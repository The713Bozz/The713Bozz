"""
Trade decision logic: pick the best candidate from a scan result set.

No MCP calls. No file I/O. Pure in-process scoring and selection.
"""

from dataclasses import dataclass, field
from typing import Optional

from src.signals.technical import SignalResult


@dataclass
class TradeDecision:
    symbol: str
    score: int
    signals: list
    instrument: str
    rationale: str
    max_spend: float


def pick_best_candidate(
    candidates: list,
    account_value: float,
    min_score: int = 3,
) -> Optional[TradeDecision]:
    """
    Select the top trade candidate from a list of SignalResult objects.

    Filtering and ranking:
      - Only candidates with score >= min_score pass the gate.
      - Ties broken by analyst_signal (getattr with default 0) descending.

    Instrument selection:
      - max_spend = 20% of account_value, rounded to 2 decimal places.
      - instrument = "option" if max_spend >= 10.0, else "equity_fractional".

    Returns a TradeDecision for the top candidate, or None if no eligible
    candidates remain after filtering.
    """
    eligible = [c for c in candidates if c.score >= min_score]
    if not eligible:
        return None

    eligible.sort(
        key=lambda c: (c.score, getattr(c, "analyst_signal", 0)),
        reverse=True,
    )

    top = eligible[0]
    max_spend = round(account_value * 0.20, 2)
    instrument = "option" if max_spend >= 10.0 else "equity_fractional"

    signal_list = ", ".join(top.signals) if top.signals else "none"
    rationale = (
        f"{top.symbol} selected with score {top.score}/4 "
        f"(signals: {signal_list}). "
        f"Max spend ${max_spend:.2f} ({instrument}). "
        f"Conviction: {getattr(top, 'conviction', 'unknown')}."
    )

    return TradeDecision(
        symbol=top.symbol,
        score=top.score,
        signals=list(top.signals),
        instrument=instrument,
        rationale=rationale,
        max_spend=max_spend,
    )
