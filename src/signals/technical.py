from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SignalResult:
    symbol: str
    score: int
    signals: list[str] = field(default_factory=list)
    conviction: str = "low"
    instrument: str = "equity"
    option_type: Optional[str] = None
    entry_note: str = ""
    stop_pct: float = 0.08
    target_pct: float = 0.20
    rr_ratio: float = 0.0
    catalyst_clear: Optional[bool] = None
    catalyst_detail: str = ""

    def __post_init__(self):
        if self.score >= 4:
            self.conviction = "high"
        elif self.score == 3:
            self.conviction = "medium"
        else:
            self.conviction = "low"
        if self.stop_pct > 0:
            self.rr_ratio = round(self.target_pct / self.stop_pct, 1)


def compute_ema(prices: list[float], period: int) -> Optional[float]:
    """EMA from close prices list (oldest → newest). Returns None if insufficient data."""
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period  # SMA seed
    for price in prices[period:]:
        ema = price * k + ema * (1 - k)
    return ema


def score_quote(
    symbol: str,
    quote: dict,
    spy_change: float = 0.0,
    volume: Optional[float] = None,
    avg_volume: Optional[float] = None,
    high_52w: Optional[float] = None,
    ema_aligned: Optional[bool] = None,
    avg_vol_10d: Optional[float] = None,
    avg_vol_3m: Optional[float] = None,
) -> SignalResult:
    """
    Score a symbol against the Momentum Compounder signal stack.

    Two volume signal modes:
      - Primary:  volume + avg_volume (today's volume vs 14d avg from MCP historicals)
      - Fallback: avg_vol_10d + avg_vol_3m (10d avg vs 3m avg from Finnhub metrics —
                  used in standalone CLI mode where today's intraday volume is unavailable)

    Signals are SKIPPED (not penalised) when enrichment data is absent.
    """
    signals = []
    score = 0

    try:
        price = float(quote.get("last_trade_price") or quote.get("ask_price") or quote.get("c", 0))
        prev_close = float(
            quote.get("adjusted_previous_close")
            or quote.get("previous_close")
            or quote.get("pc", price)
        )
    except (TypeError, ValueError):
        return SignalResult(symbol=symbol, score=0)

    if price <= 0 or prev_close <= 0:
        return SignalResult(symbol=symbol, score=0)

    day_change_pct = (price - prev_close) / prev_close

    # 1. Relative strength vs SPY
    if day_change_pct >= 0.03 or (day_change_pct - spy_change) >= 0.02:
        score += 1
        signals.append("relative_strength")

    # 2. Volume signal — two modes depending on available data
    if volume is not None and avg_volume is not None and avg_volume > 0:
        # Primary: today's volume vs 14d avg (MCP historicals path)
        if volume >= avg_volume * 1.5:
            score += 1
            signals.append("volume_surge")
    elif avg_vol_10d is not None and avg_vol_3m is not None and avg_vol_3m > 0:
        # Fallback: 10d avg vs 3m avg — accumulation signal (standalone path)
        if avg_vol_10d >= avg_vol_3m * 1.2:
            score += 1
            signals.append("volume_accumulation")

    # 3. EMA alignment — skip if data unavailable
    if ema_aligned is True:
        score += 1
        signals.append("ema_aligned")

    # 4. 52-week high proximity — skip if data unavailable; fallback to breakout magnitude
    if high_52w is not None and high_52w > 0:
        if price >= high_52w * 0.90:
            score += 1
            signals.append("near_52w_high")
        elif day_change_pct >= 0.05:
            score += 1
            signals.append("strong_breakout")
    elif day_change_pct >= 0.07:
        # Only count magnitude breakout as a fallback when 52w high is unknown
        # Higher bar (7% vs 5%) to compensate for missing context
        score += 1
        signals.append("strong_breakout")

    instrument = "option" if price >= 5.0 else "equity"
    option_type = "call" if day_change_pct >= 0 else "put"
    stop_pct = 0.50 if instrument == "option" else 0.08
    target_pct = 1.50 if instrument == "option" else 0.25

    vol_note = f", Vol {volume/avg_volume:.1f}x" if (volume and avg_volume) else ""
    ema_note = " EMA✓" if ema_aligned else ""

    return SignalResult(
        symbol=symbol,
        score=score,
        signals=signals,
        instrument=instrument,
        option_type=option_type,
        entry_note=f"{day_change_pct:+.1%}{vol_note}{ema_note}",
        stop_pct=stop_pct,
        target_pct=target_pct,
    )


def score_from_metrics(
    symbol: str,
    quote: dict,
    metrics: dict,
    spy_change: float = 0.0,
    ema_aligned: Optional[bool] = None,
) -> SignalResult:
    """
    Score using Finnhub /quote + /stock/metric data (standalone CLI path).
    metrics: dict from finnhub.stock_metrics() — has high_52w, avg_vol_10d, avg_vol_3m.
    ema_aligned: pass result of alphavantage.ema_aligned() for top candidates only.
    """
    return score_quote(
        symbol=symbol,
        quote=quote,
        spy_change=spy_change,
        high_52w=metrics.get("high_52w"),
        ema_aligned=ema_aligned,
        avg_vol_10d=metrics.get("avg_vol_10d"),
        avg_vol_3m=metrics.get("avg_vol_3m"),
    )


def score_from_bars(
    symbol: str,
    quote: dict,
    bars: list[dict],
    spy_change: float = 0.0,
) -> SignalResult:
    """
    Score using live quote + Finnhub OHLCV bars.
    Computes volume stats, 52w high, and EMA alignment from bars locally
    so no extra API calls are needed.
    bars: list of {"t","o","h","l","c","v"} ordered oldest → newest.
    """
    volume: Optional[float] = None
    avg_volume: Optional[float] = None
    high_52w: Optional[float] = None
    ema_aligned: Optional[bool] = None

    if bars:
        volume = float(bars[-1]["v"])
        if len(bars) >= 15:
            avg_volume = sum(b["v"] for b in bars[-15:-1]) / 14
        high_52w = max(b["h"] for b in bars)

        closes = [b["c"] for b in bars]
        ema9 = compute_ema(closes, 9)
        ema21 = compute_ema(closes, 21)
        if ema9 is not None and ema21 is not None:
            ema_aligned = ema9 > ema21

    return score_quote(
        symbol=symbol,
        quote=quote,
        spy_change=spy_change,
        volume=volume,
        avg_volume=avg_volume,
        high_52w=high_52w,
        ema_aligned=ema_aligned,
    )


def filter_candidates(results: list[SignalResult], min_score: int = 3) -> list[SignalResult]:
    """catalyst_clear=False is a hard gate regardless of score."""
    qualified = [r for r in results if r.score >= min_score and r.catalyst_clear is not False]
    return sorted(qualified, key=lambda r: r.score, reverse=True)
