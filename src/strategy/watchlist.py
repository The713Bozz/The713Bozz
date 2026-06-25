"""
Default watchlist for the Momentum Compounder challenge.

Tier 1: High-liquidity momentum names — options accessible at $250+ account
Tier 2: Mid-range, high-volatility — fractional equity or cheap options at $50–$150 account
Tier 3: Speculative / squeeze / leveraged candidates (1 position max)
"""

TIER1 = [
    # Mega-cap tech + ETFs
    "NVDA", "TSLA", "AMD", "MSTR", "SMCI",
    "SPY", "QQQ", "AAPL", "META", "GOOGL",
    # Financials + defense + energy (sector rotation targets)
    "JPM", "LMT", "XOM",
    # Semiconductor IP + China tech
    "ARM", "BABA",
]

TIER2 = [
    # Fintech / broker
    "SOFI", "PLTR", "HOOD", "COIN",
    # EV / mobility
    "RIVN", "NIO", "ACHR",
    # Quantum computing
    "IONQ", "ARQQ", "QUBT",
    # Space / defense
    "RKLB",
    # AI / voice / small-cap tech
    "SOUN", "BBAI",
    # Crypto mining
    "MARA", "RIOT",
    # Nuclear / energy
    "OKLO", "OXY",
    # Biotech (catalyst-driven 10–30% moves)
    "MRNA", "NVAX",
    # China ADRs (high volatility)
    "PDD", "BIDU",
    # Leveraged ETFs (3x amplification — daily momentum plays)
    "SOXL", "TQQQ",
]

TIER3 = [
    # Meme / squeeze
    "GME", "AMC",
    # VIX leveraged — fear spikes only
    "UVXY",
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
