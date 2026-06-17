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

    def __post_init__(self):
        if self.score >= 4:
            self.conviction = "high"
        elif self.score == 3:
            self.conviction = "medium"
        else:
            self.conviction = "low"

        if self.stop_pct > 0:
            self.rr_ratio = round(self.target_pct / self.stop_pct, 1)


def score_quote(symbol: str, quote: dict, spy_change: float = 0.0) -> SignalResult:
    """
    Score a quote against the Momentum Compounder signal stack.
    quote fields expected from get_equity_quotes:
      last_trade_price, previous_close, ask_price, bid_price,
      high_52_weeks, low_52_weeks, volume (today), average_volume_2_weeks
    """
    signals = []
    score = 0

    try:
        price = float(quote.get("last_trade_price") or quote.get("ask_price", 0))
        prev_close = float(quote.get("adjusted_previous_close") or quote.get("previous_close", price))
        high_52w = float(quote.get("high_52_weeks", price))
        volume = float(quote.get("volume", 0))
        avg_volume = float(quote.get("average_volume_2_weeks") or quote.get("average_volume", 1))
    except (TypeError, ValueError):
        return SignalResult(symbol=symbol, score=0)

    if price <= 0 or prev_close <= 0:
        return SignalResult(symbol=symbol, score=0)

    day_change_pct = (price - prev_close) / prev_close

    # 1. Relative strength
    if day_change_pct >= 0.03 or (day_change_pct - spy_change) >= 0.02:
        score += 1
        signals.append("relative_strength")

    # 2. Volume surge
    if avg_volume > 0 and volume >= avg_volume * 1.5:
        score += 1
        signals.append("volume_surge")

    # 3. EMA alignment — approximated from daily data (real check needs intraday)
    # Mark as pending; the market-analyst agent checks intraday via historicals
    signals.append("ema_check_pending")

    # 4. Trend: within 10% of 52-week high or meaningful uptrend
    if high_52w > 0 and price >= high_52w * 0.90:
        score += 1
        signals.append("near_52w_high")
    elif day_change_pct >= 0.05:
        score += 1
        signals.append("strong_breakout")

    # Instrument selection
    instrument = "option" if price >= 5.0 else "equity"
    option_type = "call" if day_change_pct >= 0 else "put"

    # Stop / target levels
    stop_pct = 0.50 if instrument == "option" else 0.08
    target_pct = 1.50 if instrument == "option" else 0.25

    result = SignalResult(
        symbol=symbol,
        score=score,
        signals=[s for s in signals if s != "ema_check_pending"],
        instrument=instrument,
        option_type=option_type,
        entry_note=f"Day change: {day_change_pct:+.1%}, Volume: {volume/avg_volume:.1f}x avg",
        stop_pct=stop_pct,
        target_pct=target_pct,
    )
    return result


def filter_candidates(results: list[SignalResult], min_score: int = 3) -> list[SignalResult]:
    qualified = [r for r in results if r.score >= min_score]
    return sorted(qualified, key=lambda r: r.score, reverse=True)
