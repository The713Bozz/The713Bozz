"""
CoinGecko API client — BTC/ETH price and 24h change.
Used as entry gate for crypto-correlated names (MARA, RIOT).
Docs: https://docs.coingecko.com/reference/introduction
"""

import os

import requests

BASE = "https://api.coingecko.com/api/v3"
_KEY = os.environ.get("COINGECKO_API_KEY", "")

# Symbols on our watchlist that move with BTC
BTC_CORRELATED = {"MARA", "RIOT", "CLSK", "BTBT", "HUT"}


def _get(path: str, params: dict | None = None) -> dict | None:
    headers = {"x-cg-demo-api-key": _KEY} if _KEY else {}
    try:
        r = requests.get(f"{BASE}{path}", params=params or {}, headers=headers, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def btc_day_change() -> float | None:
    """
    Return BTC 24h price change as a decimal (e.g. -0.032 = -3.2%).
    Returns None on failure — caller should treat as non-blocking.
    """
    data = _get("/simple/price", {"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true"})
    if not isinstance(data, dict):
        return None
    btc = data.get("bitcoin", {})
    change_pct = btc.get("usd_24h_change")
    if change_pct is None:
        return None
    return change_pct / 100.0


def btc_gate(symbol: str, block_threshold: float = -0.03) -> dict:
    """
    Gate for BTC-correlated names. Blocks entry if BTC is down > threshold.
    Returns: {"allowed": bool, "btc_change": float | None, "reason": str}
    """
    if symbol.upper() not in BTC_CORRELATED:
        return {"allowed": True, "btc_change": None, "reason": "Not BTC-correlated — gate skipped."}

    change = btc_day_change()
    if change is None:
        return {"allowed": True, "btc_change": None, "reason": "CoinGecko unavailable — gate skipped."}

    if change <= block_threshold:
        return {
            "allowed": False,
            "btc_change": change,
            "reason": f"BTC down {change:.1%} today — {symbol} entry blocked. Miners follow BTC down.",
        }

    return {
        "allowed": True,
        "btc_change": change,
        "reason": f"BTC {change:+.1%} today — {symbol} gate clear.",
    }
