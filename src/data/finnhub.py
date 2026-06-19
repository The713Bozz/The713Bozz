"""
Finnhub API client — news and earnings calendar.
Replaces raw WebFetch for catalyst checks.
Docs: https://finnhub.io/docs/api
"""

import os
import time
from datetime import date, timedelta

import requests

BASE = "https://finnhub.io/api/v1"
_KEY = os.environ.get("FINNHUB_API_KEY", "")


def _get(path: str, params: dict) -> dict | list | None:
    if not _KEY:
        return None
    params["token"] = _KEY
    try:
        r = requests.get(f"{BASE}{path}", params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def company_news(symbol: str, days_back: int = 3) -> list[dict]:
    """
    Return recent news items for a symbol.
    Each item: {"headline": str, "source": str, "datetime": int (unix), "summary": str}
    """
    today = date.today()
    from_date = (today - timedelta(days=days_back)).isoformat()
    to_date = today.isoformat()
    data = _get("/company-news", {"symbol": symbol.upper(), "from": from_date, "to": to_date})
    if not isinstance(data, list):
        return []
    # Return most recent 10 headlines only
    return sorted(data, key=lambda x: x.get("datetime", 0), reverse=True)[:10]


def earnings_dates(symbol: str, days_forward: int = 7) -> list[str]:
    """
    Return upcoming earnings dates for a symbol as "YYYY-MM-DD" strings.
    Uses the earnings calendar endpoint.
    """
    today = date.today()
    to_date = (today + timedelta(days=days_forward)).isoformat()
    data = _get("/calendar/earnings", {"from": today.isoformat(), "to": to_date, "symbol": symbol.upper()})
    if not isinstance(data, dict):
        return []
    earnings = data.get("earningsCalendar", [])
    return [e["date"] for e in earnings if "date" in e]


def insider_sentiment(symbol: str) -> dict:
    """
    Return insider buy/sell sentiment score (MSPR) for a symbol.
    Positive MSPR = net buying. Negative = net selling.
    """
    data = _get("/stock/insider-sentiment", {"symbol": symbol.upper()})
    if not isinstance(data, dict):
        return {}
    items = data.get("data", [])
    if not items:
        return {}
    latest = sorted(items, key=lambda x: (x.get("year", 0), x.get("month", 0)), reverse=True)[0]
    return {
        "mspr": latest.get("mspr", 0),       # Monthly Share Purchase Ratio (-1 to 1)
        "change": latest.get("change", 0),    # Net shares bought/sold
        "month": latest.get("month"),
        "year": latest.get("year"),
    }


def news_headlines_text(symbol: str, days_back: int = 3) -> str:
    """
    Return concatenated headlines as plain text for catalyst.check_news_text().
    """
    items = company_news(symbol, days_back)
    if not items:
        return ""
    return " | ".join(item.get("headline", "") for item in items)
