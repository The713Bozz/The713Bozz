"""
Default watchlist for the Momentum Compounder challenge.

Tier 1: High-liquidity, heavily traded — broadest sector coverage, regime anchors
Tier 2: Mid-range, high-volatility — fractional equity or cheap options at $50–$150
Tier 3: Speculative, event-driven, leveraged sector plays (1 position max)

Total: ~75 symbols across 18 sectors so the scanner catches momentum in ANY part
of the market, not just tech.
"""

TIER1 = [
    # Mega-cap tech
    "NVDA", "TSLA", "AMD", "AAPL", "META", "GOOGL", "MSFT", "AMZN", "MSTR", "SMCI",
    # Semiconductor leaders
    "ARM", "AVGO", "MU", "AMAT",
    # Broad market / index ETFs
    "SPY", "QQQ", "IWM",
    # Leveraged bull ETFs (3x — amplify sector moves for fractional plays)
    "SPXL", "TQQQ", "SOXL", "FNGU",
    # Leveraged bear ETFs (3x — hedge or play downside regime)
    "SPXS", "SQQQ", "SOXS",
    # Financials
    "JPM", "GS", "BAC",
    # Defense
    "LMT", "RTX",
    # Energy majors
    "XOM", "CVX",
]

TIER2 = [
    # Fintech / crypto brokerage
    "SOFI", "PLTR", "HOOD", "COIN", "AFRM",
    # EV / mobility (high-beta sector rotation)
    "RIVN", "NIO", "ACHR", "XPEV", "LCID",
    # Quantum computing
    "IONQ", "ARQQ", "QUBT",
    # Space / next-gen aerospace
    "RKLB", "JOBY",
    # AI / voice / small-cap tech
    "SOUN", "BBAI", "AI", "RXRX",
    # Crypto mining
    "MARA", "RIOT", "CLSK",
    # Biotech (catalyst-driven 10–30% single-day moves)
    "MRNA", "NVAX", "CRSP",
    # Nuclear / energy
    "OKLO", "OXY", "SMR",
    # China ADRs (high volatility, macro-driven)
    "BABA", "PDD", "BIDU",
    # Social media / entertainment (high-beta consumer)
    "SNAP", "RDDT", "RBLX",
]

TIER3 = [
    # Meme / squeeze (1 position max, only on confirmed signal)
    "GME", "AMC",
    # VIX leveraged — fear spike plays
    "UVXY",
    # Leveraged sector ETFs — event plays
    "LABU", "TNA",
    # Commodities (gold, miners, silver)
    "GLD", "GDX", "SLV",
    # High-beta consumer / gaming
    "DKNG",
]

ALL_SYMBOLS = TIER1 + TIER2 + TIER3

TIER_MAP = {s: 1 for s in TIER1}
TIER_MAP.update({s: 2 for s in TIER2})
TIER_MAP.update({s: 3 for s in TIER3})


def get_scan_list(account_value: float, include_tier3: bool = False) -> list[str]:
    """
    Return symbols to scan.
    Under $150: Tier 2 first — cheap fractional or options fast path.
    Over $150: Tier 1 first — options become accessible.
    Tier 3 scanned for top-3 names (GLD, LABU, TNA) to catch commodity/sector pivots.
    """
    if account_value < 150:
        symbols = TIER2 + TIER1
    else:
        symbols = TIER1 + TIER2
    if include_tier3:
        symbols += TIER3
    else:
        # Always scan top tier3 entries (commodities + leveraged sector) — exclude meme/VIX
        symbols += ["GLD", "GDX", "SLV", "LABU", "TNA", "DKNG"]
    return symbols


def tier(symbol: str) -> int:
    return TIER_MAP.get(symbol.upper(), 2)
