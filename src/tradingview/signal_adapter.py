"""
Convert a TradingView TVAlert into the existing SignalResult format
so that TV alerts feed directly into the Momentum Compounder stack.
"""

from src.signals.technical import SignalResult
from src.tradingview.webhook import TVAlert


def tv_alert_to_signal(alert: TVAlert) -> SignalResult:
    """
    Map a TVAlert to a SignalResult.

    Scoring heuristic (mirrors score_quote logic):
      +1  action is "buy"
      +1  day change >= 3 % (TV {{change}} field)
      +1  strategy tag confirms momentum ("momentum" | "breakout" | "compounder")
      +1  price-based 52w-high approximation — not available from alert alone,
          so this point is left at 0 until enriched by a live quote lookup.

    The caller should enrich the result with a live quote if needed.
    """
    signals: list[str] = []
    score = 0

    if alert.action == "buy":
        score += 1
        signals.append("tv_buy_signal")
    elif alert.action in ("sell", "close"):
        signals.append("tv_exit_signal")

    if alert.change >= 0.03:
        score += 1
        signals.append("relative_strength")

    strategy_lower = alert.strategy.lower()
    if any(kw in strategy_lower for kw in ("momentum", "breakout", "compounder")):
        score += 1
        signals.append("strategy_confirmed")

    instrument = "option" if alert.price >= 5.0 else "equity"
    option_type = "call" if alert.action == "buy" else "put"
    stop_pct = 0.50 if instrument == "option" else 0.08
    target_pct = 1.50 if instrument == "option" else 0.25

    change_display = f"{alert.change:+.1%}" if alert.change else "n/a"
    entry_note = (
        f"TV alert: {alert.action.upper()} @ ${alert.price:.2f} | "
        f"change={change_display} | strategy={alert.strategy or 'unset'} | "
        f"interval={alert.interval or 'unset'}"
    )

    return SignalResult(
        symbol=alert.symbol,
        score=score,
        signals=signals,
        instrument=instrument,
        option_type=option_type,
        entry_note=entry_note,
        stop_pct=stop_pct,
        target_pct=target_pct,
    )
