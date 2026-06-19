"""
Default watchlist for the Momentum Compounder challenge.

Tier 1: High-liquidity momentum names — options accessible at $250+ account
Tier 2: $5–$50 range, high IV — 1 contract affordable at $50–$150 account (fast path)
Tier 3: Speculative / squeeze candidates (1 position max)
"""

TIER1 = [
    "NVDA", "TSLA", "AMD", "MSTR", "SMCI",
    "SPY", "QQQ", "AAPL", "META", "GOOGL",
]

TIER2 = [
    "SOFI", "PLTR", "RIVN", "NIO", "IONQ",
    "RKLB", "SOUN", "BBAI", "ARQQ", "QUBT",
    "MARA", "RIOT", "ACHR", "OKLO", "HOOD",
]

TIER3 = [
    "GME", "AMC",
]

ALL_SYMBOLS = TIER1 + TIER2 + TIER3

TIER_MAP = {s: 1 for s in TIER1}
TIER_MAP.update({s: 2 for s in TIER2})
TIER_MAP.update({s: 3 for s in TIER3})


def get_scan_list(account_value: float, include_tier3: bool = False) -> list[str]:
    """
    Return symbols to scan.
    Under $150: Tier 2 first — cheap options are the fast path.
    Over $150: Tier 1 + Tier 2.
    """
    if account_value < 150:
        symbols = TIER2 + TIER1
    else:
        symbols = TIER1 + TIER2
    if include_tier3:
        symbols += TIER3[:1]
    return symbols


def tier(symbol: str) -> int:
    return TIER_MAP.get(symbol.upper(), 2)
