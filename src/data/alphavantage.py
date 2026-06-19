"""
Alpha Vantage API client — intraday bars and EMA as backup to Robinhood historicals.
Use when Robinhood get_equity_historicals returns stale/incomplete data.
Docs: https://www.alphavantage.co/documentation/
Free tier: 25 requests/day.
"""

import os
from typing import Optional

import requests

BASE = "https://www.alphavantage.co/query"
_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")

# ponytail: 25 req/day on free tier — use sparingly, only as fallback
_DAILY_BUDGET = 25


def _get(params: dict) -> dict | None:
    if not _KEY:
        return None
    params["apikey"] = _KEY
    try:
        r = requests.get(BASE, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        # Alpha Vantage returns error in a note key
        if "Note" in data or "Information" in data:
            return None
        return data
    except Exception:
        return None


def intraday_5min(symbol: str, outputsize: str = "compact") -> list[dict]:
    """
    Return 5-min OHLCV bars, most recent first.
    outputsize: "compact" = last 100 bars, "full" = 30 days.
    Each bar: {"time": str, "open": float, "high": float, "low": float, "close": float, "volume": int}
    """
    data = _get({
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol.upper(),
        "interval": "5min",
        "outputsize": outputsize,
        "extended_hours": "true",
    })
    if not data:
        return []
    series = data.get("Time Series (5min)", {})
    bars = []
    for ts, ohlcv in sorted(series.items(), reverse=True):
        try:
            bars.append({
                "time": ts,
                "open": float(ohlcv["1. open"]),
                "high": float(ohlcv["2. high"]),
                "low": float(ohlcv["3. low"]),
                "close": float(ohlcv["4. close"]),
                "volume": int(ohlcv["5. volume"]),
            })
        except (KeyError, ValueError):
            continue
    return bars


def ema_latest(symbol: str, period: int = 9, interval: str = "5min") -> Optional[float]:
    """
    Return the most recent EMA value from Alpha Vantage's built-in indicator.
    Use period=9 and period=21 to check EMA alignment.
    """
    data = _get({
        "function": "EMA",
        "symbol": symbol.upper(),
        "interval": interval,
        "time_period": period,
        "series_type": "close",
    })
    if not data:
        return None
    indicator = data.get("Technical Analysis: EMA", {})
    if not indicator:
        return None
    latest_ts = max(indicator.keys())
    try:
        return float(indicator[latest_ts]["EMA"])
    except (KeyError, ValueError):
        return None


def ema_aligned(symbol: str) -> Optional[bool]:
    """
    Return True if 9 EMA > 21 EMA on 5-min (bullish alignment).
    Returns None if data unavailable (don't block on API failure).
    """
    ema9 = ema_latest(symbol, period=9)
    ema21 = ema_latest(symbol, period=21)
    if ema9 is None or ema21 is None:
        return None
    return ema9 > ema21


def news_sentiment(symbol: str) -> dict:
    """
    Return news sentiment score from Alpha Vantage's NEWS_SENTIMENT endpoint.
    Returns: {"sentiment": "Bullish"|"Bearish"|"Neutral"|"Somewhat-Bullish"|...,
              "score": float, "articles": int}
    """
    data = _get({
        "function": "NEWS_SENTIMENT",
        "tickers": symbol.upper(),
        "limit": "10",
    })
    if not data:
        return {}
    feed = data.get("feed", [])
    if not feed:
        return {"sentiment": "Neutral", "score": 0.0, "articles": 0}

    scores = []
    for article in feed:
        for ticker_data in article.get("ticker_sentiment", []):
            if ticker_data.get("ticker") == symbol.upper():
                try:
                    scores.append(float(ticker_data["ticker_sentiment_score"]))
                except (KeyError, ValueError):
                    continue

    if not scores:
        return {"sentiment": "Neutral", "score": 0.0, "articles": len(feed)}

    avg = sum(scores) / len(scores)
    if avg >= 0.35:
        label = "Bullish"
    elif avg >= 0.15:
        label = "Somewhat-Bullish"
    elif avg <= -0.35:
        label = "Bearish"
    elif avg <= -0.15:
        label = "Somewhat-Bearish"
    else:
        label = "Neutral"

    return {"sentiment": label, "score": round(avg, 4), "articles": len(feed)}
