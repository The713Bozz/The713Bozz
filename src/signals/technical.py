import json as _json
from dataclasses import dataclass, field
from pathlib import Path as _Path
from typing import Optional


def _load_signals_cfg() -> dict:
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as _f:
            return _json.load(_f).get("signals", {})
    except Exception:
        return {}


_SIG: dict = {}  # reloaded inside score_from_bars / score_from_metrics on each call


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
    breakout_alert: bool = False  # up ≥8% with 2+ signals — surface even below 3/4 threshold
    # Populated after scoring by _apply_analyst_signal() in scanner
    current_price: float = 0.0
    day_change_pct: float = 0.0
    forecast_upside_pct: Optional[float] = None  # analyst consensus upside from current price
    forecast_target: Optional[float] = None       # analyst consensus mean target price
    forecast_warning: str = ""                    # non-empty when analyst sees downside

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
    high_ref: Optional[float] = None,
    ema_aligned: Optional[bool] = None,
    avg_vol_10d: Optional[float] = None,
    avg_vol_3m: Optional[float] = None,
    high_3m: Optional[float] = None,
    high_label: str = "near_52w_high",
) -> SignalResult:
    """
    Score a symbol against the Momentum Compounder signal stack.

    Two volume signal modes:
      - Primary:  volume + avg_volume (today's volume vs 14d avg from MCP historicals)
      - Fallback: avg_vol_10d + avg_vol_3m (10d avg vs 3m avg from Finnhub metrics —
                  used in standalone CLI mode where today's intraday volume is unavailable)

    Signals are SKIPPED (not penalised) when enrichment data is absent.
    high_ref: reference high for proximity check. Meaning depends on caller:
      - score_from_metrics(): true 52-week high from Finnhub
      - score_from_bars(): max high over all available bars (may be only ~61d with 90-cal-day lookback)
    high_label: label applied to the near-high signal; caller sets it to reflect actual bar span
      (e.g. "near_52w_high" only when ≥252 bars are present, otherwise "near_{N}d_high").
    """
    signals = []
    score = 0

    rs_min_day   = _SIG.get("rs_min_day_change", 0.03)
    rs_min_spy   = _SIG.get("rs_min_vs_spy", 0.02)
    vol_surge    = _SIG.get("volume_surge_multiplier", 1.5)
    vol_accum    = _SIG.get("volume_accumulation_multiplier", 1.2)
    high_prox    = _SIG.get("high_proximity_pct", 0.90)
    brk_high     = _SIG.get("strong_breakout_with_high_pct", 0.05)
    brk_no_high  = _SIG.get("strong_breakout_no_high_pct", 0.07)
    brk_alert    = _SIG.get("breakout_alert_pct", 0.08)
    opt_thresh   = _SIG.get("option_price_threshold", 5.0)
    opt_stop     = _SIG.get("option_stop_pct", 0.50)
    opt_target   = _SIG.get("option_target_pct", 1.50)
    eq_stop      = _SIG.get("equity_stop_pct", 0.08)
    eq_target    = _SIG.get("equity_target_pct", 0.25)

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
    if day_change_pct >= rs_min_day or (day_change_pct - spy_change) >= rs_min_spy:
        score += 1
        signals.append("relative_strength")

    # 2. Volume signal — two modes depending on available data
    if volume is not None and avg_volume is not None and avg_volume > 0:
        # Primary: today's volume vs N-day avg (MCP historicals path)
        if volume >= avg_volume * vol_surge:
            score += 1
            signals.append("volume_surge")
    elif avg_vol_10d is not None and avg_vol_3m is not None and avg_vol_3m > 0:
        # Fallback: 10d avg vs 3m avg — accumulation signal (standalone path)
        if avg_vol_10d >= avg_vol_3m * vol_accum:
            score += 1
            signals.append("volume_accumulation")

    # 3. EMA alignment — skip if data unavailable
    if ema_aligned is True:
        score += 1
        signals.append("ema_aligned")

    # 4. High proximity — labeled by caller (actual bar span, not assumed 52w).
    #    3m high as recovery breakout fallback; then magnitude breakout.
    if high_ref is not None and high_ref > 0:
        if price >= high_ref * high_prox:
            score += 1
            signals.append(high_label)
        elif high_3m is not None and high_3m > 0 and price >= high_3m * high_prox:
            score += 1
            signals.append("near_3m_high")
        elif day_change_pct >= brk_high:
            score += 1
            signals.append("strong_breakout")
    elif day_change_pct >= brk_no_high:
        score += 1
        signals.append("strong_breakout")

    instrument = "option" if price >= opt_thresh else "equity"
    option_type = "call" if day_change_pct >= 0 else "put"
    stop_pct = opt_stop if instrument == "option" else eq_stop
    target_pct = opt_target if instrument == "option" else eq_target

    vol_note = f", Vol {volume/avg_volume:.1f}x" if (volume and avg_volume) else ""
    ema_note = " EMA✓" if ema_aligned else ""

    breakout_alert = day_change_pct >= brk_alert and score >= 2

    return SignalResult(
        symbol=symbol,
        score=score,
        signals=signals,
        instrument=instrument,
        option_type=option_type,
        entry_note=f"{day_change_pct:+.1%}{vol_note}{ema_note}",
        stop_pct=stop_pct,
        target_pct=target_pct,
        breakout_alert=breakout_alert,
        current_price=price,
        day_change_pct=day_change_pct,
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
    global _SIG
    _SIG = _load_signals_cfg()
    return score_quote(
        symbol=symbol,
        quote=quote,
        spy_change=spy_change,
        high_ref=metrics.get("high_52w"),
        ema_aligned=ema_aligned,
        avg_vol_10d=metrics.get("avg_vol_10d"),
        avg_vol_3m=metrics.get("avg_vol_3m"),
        high_label="near_52w_high",  # Finnhub metrics always report the true 52w high
    )


def score_from_bars(
    symbol: str,
    quote: dict,
    bars: list[dict],
    spy_change: float = 0.0,
    today_volume: Optional[float] = None,
) -> SignalResult:
    """
    Score using live quote + OHLCV bars.
    bars: list of {"t","o","h","l","c","v"} ordered oldest → newest.
    today_volume: projected full-day volume for the current session (caller
                  scales the partial bar before passing). If None, bars[-1]["v"]
                  is used as-is — correct when bars are complete daily bars.

    The high label reflects actual bar span: "near_52w_high" only when ≥252 bars
    are available; otherwise "near_{n}d_high" so the signal name is truthful.
    """
    global _SIG
    _SIG = _load_signals_cfg()
    volume: Optional[float] = None
    avg_volume: Optional[float] = None
    high_allbars: Optional[float] = None
    ema_aligned: Optional[bool] = None
    high_3m: Optional[float] = None

    vol_window   = _SIG.get("volume_avg_window_days", 14)
    ema_short    = _SIG.get("ema_short_period", 9)
    ema_long     = _SIG.get("ema_long_period", 21)
    high_3m_bars = _SIG.get("high_3m_bars", 63)

    if bars:
        volume = today_volume if today_volume is not None else float(bars[-1]["v"])
        if len(bars) >= vol_window + 1:
            avg_volume = sum(b["v"] for b in bars[-(vol_window + 1):-1]) / vol_window
        high_allbars = max(b["h"] for b in bars)  # max over available bars, NOT necessarily 52w
        if len(bars) >= high_3m_bars:
            high_3m = max(b["h"] for b in bars[-high_3m_bars:])

        closes = [b["c"] for b in bars]
        ema9 = compute_ema(closes, ema_short)
        ema21 = compute_ema(closes, ema_long)
        if ema9 is not None and ema21 is not None:
            ema_aligned = ema9 > ema21

    # Label truthfully: only call it "52w" when we actually have ≥252 bars.
    high_label = "near_52w_high" if len(bars) >= 252 else f"near_{len(bars)}d_high"

    return score_quote(
        symbol=symbol,
        quote=quote,
        spy_change=spy_change,
        volume=volume,
        avg_volume=avg_volume,
        high_ref=high_allbars,
        ema_aligned=ema_aligned,
        high_3m=high_3m,
        high_label=high_label,
    )


def filter_candidates(results: list[SignalResult], min_score: int = 3) -> list[SignalResult]:
    """
    catalyst_clear=False is a hard gate regardless of score.
    breakout_alert=True entries (up ≥8%, score ≥2) pass through even below min_score
    so news-driven explosions are never silently dropped from the report.
    """
    qualified = [
        r for r in results
        if (r.score >= min_score or r.breakout_alert) and r.catalyst_clear is not False
    ]
    return sorted(qualified, key=lambda r: r.score, reverse=True)
