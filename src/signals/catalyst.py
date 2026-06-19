from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class CatalystResult:
    symbol: str
    clear: bool
    flag: str   # "clear" | "earnings_near" | "earnings_imminent" | "news_risk" | "news_caution"
    detail: str
    days_to_earnings: Optional[int] = None


def check_earnings_window(
    symbol: str,
    earnings_dates: list[str],
    today: Optional[date] = None,
) -> CatalystResult:
    """
    Block if earnings ≤2 days out (binary surprise risk).
    Caution if ≤5 days out (hold-through risk on multi-day options).
    earnings_dates: list of "YYYY-MM-DD" strings from get_earnings_calendar.
    """
    if today is None:
        today = date.today()

    nearest: Optional[int] = None
    for ds in earnings_dates:
        try:
            delta = (date.fromisoformat(ds) - today).days
            if delta >= 0 and (nearest is None or delta < nearest):
                nearest = delta
        except ValueError:
            continue

    if nearest is None:
        return CatalystResult(symbol, True, "clear", "No upcoming earnings in calendar.")

    if nearest <= 2:
        return CatalystResult(
            symbol, False, "earnings_imminent",
            f"Earnings in {nearest} day(s) — binary event risk. SKIP.",
            days_to_earnings=nearest,
        )
    if nearest <= 5:
        return CatalystResult(
            symbol, False, "earnings_near",
            f"Earnings in {nearest} days — hold-through risk. Only enter if option DTE > earnings date.",
            days_to_earnings=nearest,
        )

    return CatalystResult(
        symbol, True, "clear",
        f"Next earnings {nearest} days out — clear window.",
        days_to_earnings=nearest,
    )


# Hard blocks: enter with any of these in headlines = instant skip, no override.
_HARD_BLOCKS = [
    "fda rejection", "clinical hold", "complete response letter",
    "sec investigation", "doj investigation", "securities fraud",
    "going concern", "bankruptcy", "chapter 11", "delisting notice",
    "restatement", "accounting irregularities",
    "safety recall", "plant shutdown",
]

# Soft flags: surface to user, don't auto-block.
_SOFT_FLAGS = [
    "downgrade", "misses estimates", "disappoints", "warns",
    "cuts guidance", "guidance cut", "layoffs", "class action",
    "subpoena", "short seller report", "short report",
]


def check_news_text(symbol: str, news_text: str) -> CatalystResult:
    """
    Evaluate pre-fetched news headlines/summary for red flags.
    The agent fetches the text via WebFetch; this function scores it.
    Returns clear=False on hard blocks (auto-skip) or soft flags (user review).
    """
    text = news_text.lower()

    for kw in _HARD_BLOCKS:
        if kw in text:
            return CatalystResult(
                symbol, False, "news_risk",
                f"Hard block — '{kw}' in headlines. Do not enter.",
            )

    soft_hits = [kw for kw in _SOFT_FLAGS if kw in text]
    if soft_hits:
        return CatalystResult(
            symbol, False, "news_caution",
            f"Soft flags in headlines: {', '.join(soft_hits)}. Review before entry.",
        )

    return CatalystResult(symbol, True, "clear", "No negative catalyst in headlines.")
