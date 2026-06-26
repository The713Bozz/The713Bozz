from dataclasses import dataclass
from datetime import date
from typing import Optional

try:
    from src.data import finnhub as _finnhub
    from src.data import coingecko as _coingecko
    from src.data import fmp as _fmp
    _DATA_AVAILABLE = True
except ImportError:
    _DATA_AVAILABLE = False


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
    Evaluate headlines text for red flags.
    news_text can come from Finnhub (preferred) or raw WebFetch fallback.
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
            symbol, True, "news_caution",
            f"Soft flags in headlines: {', '.join(soft_hits)}. Review before entry.",
        )

    return CatalystResult(symbol, True, "clear", "No negative catalyst in headlines.")


def check_earnings_risk(symbol: str, days_ahead: int = 2) -> tuple[bool, str]:
    """
    Order-time earnings gate. Returns (safe_to_trade, block_reason).
    safe_to_trade=False when earnings fall within days_ahead calendar days.
    Uses both Finnhub and FMP for cross-verification — either source can block.
    Passes through (True, "") when data modules are unavailable.
    """
    if not _DATA_AVAILABLE:
        return True, ""
    finn_dates = _finnhub.earnings_dates(symbol, days_forward=days_ahead)
    try:
        fmp_dates = _fmp.earnings_dates(symbol, days_forward=days_ahead)
    except Exception:
        fmp_dates = []
    all_dates = list(set(finn_dates + fmp_dates))
    result = check_earnings_window(symbol, all_dates)
    if not result.clear:
        return False, result.detail
    return True, ""


def full_catalyst_check(symbol: str, today: Optional[date] = None) -> CatalystResult:
    """
    Full automated catalyst check using live APIs (no WebFetch needed).
    Order: BTC gate → earnings window → news scan.
    Falls back gracefully if any API is unavailable.
    """
    if not _DATA_AVAILABLE:
        return CatalystResult(symbol, True, "clear", "Data modules unavailable — manual catalyst check required.")

    # 1. BTC gate for crypto miners
    btc = _coingecko.btc_gate(symbol)
    if not btc["allowed"]:
        return CatalystResult(symbol, False, "btc_gate", btc["reason"])

    # 2. Earnings window — cross-check Finnhub + FMP for reliability
    finn_dates = _finnhub.earnings_dates(symbol, days_forward=7)
    fmp_dates = _fmp.earnings_dates(symbol, days_forward=7)
    all_dates = list(set(finn_dates + fmp_dates))
    earnings_result = check_earnings_window(symbol, all_dates, today=today)
    if not earnings_result.clear:
        return earnings_result

    # 3. Analyst grade signal — major firm downgrade = soft block
    grade = _fmp.grade_signal(symbol, days_back=14)
    if grade["sentiment"] == "bearish" and grade["major_downgrades"] > 0:
        return CatalystResult(symbol, False, "news_caution", grade["detail"])

    # 4. News scan via Finnhub
    headlines = _finnhub.news_headlines_text(symbol, days_back=3)
    if headlines:
        news_result = check_news_text(symbol, headlines)
        if not news_result.clear:
            return news_result

    btc_note = f" BTC {btc['btc_change']:+.1%}." if btc.get("btc_change") is not None else ""
    grade_note = f" Analyst: {grade['sentiment']} ({grade['upgrades']}U/{grade['downgrades']}D)." if (grade['upgrades'] + grade['downgrades']) > 0 else ""
    return CatalystResult(symbol, True, "clear", f"All catalyst checks passed.{btc_note}{grade_note}")
