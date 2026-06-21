"""
Financial Modeling Prep (FMP) API client.
Free tier gives us: quotes, earnings calendar, analyst grades, key metrics.
Congressional/senate trading requires premium — not available on this plan.
Docs: https://financialmodelingprep.com/developer/docs
Free tier: 250 requests/day.
"""

import os
from datetime import date, timedelta

import requests

BASE = "https://financialmodelingprep.com/stable"
_KEY = os.environ.get("FMP_API_KEY", "")

_MAJOR_FIRMS = {
    "Goldman Sachs", "Morgan Stanley", "JPMorgan", "Citigroup",
    "B of A Securities", "Barclays", "Deutsche Bank", "UBS",
    "Wells Fargo", "Jefferies", "Piper Sandler", "TD Cowen",
    "Mizuho", "Needham", "RBC Capital", "Stifel",
}


def _get(path: str, params: dict | None = None) -> list | dict | None:
    if not _KEY:
        return None
    p = dict(params or {})
    p["apikey"] = _KEY
    try:
        r = requests.get(f"{BASE}/{path}", params=p, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def earnings_dates(symbol: str, days_forward: int = 7) -> list[str]:
    """
    Upcoming earnings dates from FMP calendar. Used as backup / cross-check
    against Finnhub earnings_dates().
    Returns list of "YYYY-MM-DD" strings.
    """
    today = date.today()
    to_date = (today + timedelta(days=days_forward)).isoformat()
    data = _get("earnings-calendar", {"from": today.isoformat(), "to": to_date})
    if not isinstance(data, list):
        return []
    return [e["date"] for e in data if e.get("symbol") == symbol.upper() and e.get("date")]


def analyst_grades(symbol: str, days_back: int = 14) -> list[dict]:
    """
    Return recent analyst grade actions for a symbol.
    Each item: {"date", "gradingCompany", "previousGrade", "newGrade", "action"}
    action: "upgrade" | "downgrade" | "maintain" | "init"
    """
    cutoff = (date.today() - timedelta(days=days_back)).isoformat()
    data = _get("grades", {"symbol": symbol.upper()})
    if not isinstance(data, list):
        return []
    return [g for g in data if g.get("date", "") >= cutoff]


def grade_signal(symbol: str, days_back: int = 14) -> dict:
    """
    Summarize recent analyst action as a signal.
    Returns:
      sentiment: "bullish" | "bearish" | "mixed" | "neutral"
      detail: human-readable summary
      downgrades: count from major firms
      upgrades: count from major firms
    """
    grades = analyst_grades(symbol, days_back)
    if not grades:
        return {"sentiment": "neutral", "detail": f"No analyst activity in last {days_back} days.", "upgrades": 0, "downgrades": 0}

    major_upgrades = [g for g in grades if g["action"] == "upgrade" and g["gradingCompany"] in _MAJOR_FIRMS]
    major_downgrades = [g for g in grades if g["action"] == "downgrade" and g["gradingCompany"] in _MAJOR_FIRMS]
    any_downgrades = [g for g in grades if g["action"] == "downgrade"]
    any_upgrades = [g for g in grades if g["action"] == "upgrade"]

    u = len(any_upgrades)
    d = len(any_downgrades)

    if major_downgrades:
        firms = ", ".join(g["gradingCompany"] for g in major_downgrades)
        sentiment = "bearish"
        detail = f"Major firm downgrade(s) in last {days_back}d: {firms}. Soft block — review before entry."
    elif d > u:
        sentiment = "bearish"
        detail = f"{d} downgrade(s) vs {u} upgrade(s) in last {days_back}d. Analyst pressure."
    elif major_upgrades:
        firms = ", ".join(g["gradingCompany"] for g in major_upgrades)
        sentiment = "bullish"
        detail = f"Major firm upgrade(s) in last {days_back}d: {firms}. Analyst tailwind."
    elif u > d:
        sentiment = "bullish"
        detail = f"{u} upgrade(s) vs {d} downgrade(s) in last {days_back}d."
    else:
        sentiment = "mixed" if (u + d) > 0 else "neutral"
        detail = f"{u} upgrade(s), {d} downgrade(s) in last {days_back}d — no clear bias."

    return {
        "sentiment": sentiment,
        "detail": detail,
        "upgrades": u,
        "downgrades": d,
        "major_upgrades": len(major_upgrades),
        "major_downgrades": len(major_downgrades),
    }
