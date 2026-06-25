"""
Default watchlist for the Momentum Compounder challenge.

Tier 1: High-liquidity, heavily traded — sector leaders + index/leveraged ETFs
Tier 2: Mid-range, high-volatility — fractional equity or cheap options at $50–$150
Tier 3: Speculative, event-driven, leveraged sector plays (1 position max)

~120 symbols across 25 sectors. Scanner catches momentum ANYWHERE in the market.
"""

TIER1 = [
    # ── Mega-cap tech ──────────────────────────────────────────────────────────
    "NVDA", "TSLA", "AMD", "AAPL", "META", "GOOGL", "MSFT", "AMZN", "MSTR", "SMCI",

    # ── Semiconductor ──────────────────────────────────────────────────────────
    "ARM", "AVGO", "MU", "AMAT", "ASML", "TSM", "QCOM",

    # ── Enterprise software / cloud ────────────────────────────────────────────
    "CRM", "ORCL", "SNOW", "NET", "DDOG",

    # ── Cybersecurity ──────────────────────────────────────────────────────────
    "CRWD", "PANW", "FTNT", "ZS",

    # ── Streaming / media / entertainment ─────────────────────────────────────
    "NFLX", "DIS",

    # ── Mobility / consumer platform ──────────────────────────────────────────
    "UBER", "SHOP",

    # ── Index ETFs ────────────────────────────────────────────────────────────
    "SPY", "QQQ", "IWM",

    # ── Leveraged bull ETFs (3x — amplify sector moves for fractional plays) ──
    "SPXL", "TQQQ", "SOXL", "FNGU",

    # ── Leveraged bear ETFs (3x — downside / hedge regime) ────────────────────
    "SPXS", "SQQQ", "SOXS",

    # ── Financials ────────────────────────────────────────────────────────────
    "JPM", "GS", "BAC", "WFC", "V", "MA",

    # ── Defense ───────────────────────────────────────────────────────────────
    "LMT", "RTX", "NOC",

    # ── Energy majors ─────────────────────────────────────────────────────────
    "XOM", "CVX", "OXY",

    # ── Healthcare / GLP-1 ────────────────────────────────────────────────────
    "LLY", "UNH", "NVO",
]

TIER2 = [
    # ── Fintech / payments ────────────────────────────────────────────────────
    "SOFI", "PLTR", "HOOD", "COIN", "AFRM", "PYPL", "SQ", "NU",

    # ── GLP-1 / consumer health (high volatility, hot narrative) ──────────────
    "HIMS", "CELH",

    # ── EV / mobility ─────────────────────────────────────────────────────────
    "RIVN", "NIO", "ACHR", "XPEV", "LCID",

    # ── Quantum computing ─────────────────────────────────────────────────────
    "IONQ", "ARQQ", "QUBT",

    # ── Space / next-gen aerospace ────────────────────────────────────────────
    "RKLB", "JOBY",

    # ── AI / voice / small-cap tech ───────────────────────────────────────────
    "SOUN", "BBAI", "AI", "RXRX", "PATH", "UPST",

    # ── Crypto mining ─────────────────────────────────────────────────────────
    "MARA", "RIOT", "CLSK",

    # ── Biotech / gene editing (catalyst-driven 10–30% moves) ────────────────
    "MRNA", "NVAX", "CRSP", "EDIT", "BEAM", "SAVA",

    # ── Nuclear / clean energy ────────────────────────────────────────────────
    "OKLO", "SMR",

    # ── Solar / hydrogen / EV charging ───────────────────────────────────────
    "ENPH", "FSLR", "PLUG", "CHPT",

    # ── Materials / lithium / copper ──────────────────────────────────────────
    "FCX", "ALB",

    # ── China ADRs ────────────────────────────────────────────────────────────
    "BABA", "PDD", "BIDU", "JD", "BILI",

    # ── SE Asia / LatAm emerging tech ─────────────────────────────────────────
    "SE",

    # ── Social / entertainment / gaming ───────────────────────────────────────
    "SNAP", "RDDT", "RBLX", "DKNG",

    # ── Travel / leisure (cyclical high-beta) ─────────────────────────────────
    "ABNB", "AAL", "RCL",
]

TIER3 = [
    # ── Meme / squeeze (1 position max, only on confirmed signal) ─────────────
    "GME", "AMC",

    # ── VIX / volatility instruments ──────────────────────────────────────────
    "UVXY", "VIXY",

    # ── Leveraged sector ETFs — event plays ───────────────────────────────────
    "LABU", "TNA", "DPST", "NAIL",

    # ── Commodities ETFs ──────────────────────────────────────────────────────
    "GLD", "GDX", "SLV", "USO",

    # ── Micro-cap speculative ─────────────────────────────────────────────────
    "FCEL", "BLNK", "NKLA",
]

ALL_SYMBOLS = TIER1 + TIER2 + TIER3

TIER_MAP = {s: 1 for s in TIER1}
TIER_MAP.update({s: 2 for s in TIER2})
TIER_MAP.update({s: 3 for s in TIER3})

# Sector lookup — used for rotation detection and targeted re-scans
SECTORS = {
    "mega_cap_tech":       ["NVDA", "TSLA", "AMD", "AAPL", "META", "GOOGL", "MSFT", "AMZN", "MSTR", "SMCI"],
    "semiconductor":       ["NVDA", "AMD", "SMCI", "ARM", "AVGO", "MU", "AMAT", "ASML", "TSM", "QCOM"],
    "enterprise_software": ["CRM", "ORCL", "SNOW", "NET", "DDOG"],
    "cybersecurity":       ["CRWD", "PANW", "FTNT", "ZS"],
    "streaming_media":     ["NFLX", "DIS", "RBLX", "RDDT"],
    "mobility_consumer":   ["UBER", "SHOP", "ABNB"],
    "index_etf":           ["SPY", "QQQ", "IWM"],
    "leveraged_bull":      ["SPXL", "TQQQ", "SOXL", "FNGU", "LABU", "TNA", "DPST", "NAIL"],
    "leveraged_bear":      ["SPXS", "SQQQ", "SOXS"],
    "financials":          ["JPM", "GS", "BAC", "WFC", "V", "MA", "SOFI", "PLTR", "HOOD", "COIN", "AFRM", "PYPL", "SQ", "NU"],
    "defense":             ["LMT", "RTX", "NOC"],
    "energy":              ["XOM", "CVX", "OXY", "USO"],
    "healthcare_glp1":     ["LLY", "UNH", "NVO", "HIMS", "CELH"],
    "ev_mobility":         ["TSLA", "RIVN", "NIO", "ACHR", "XPEV", "LCID"],
    "quantum":             ["IONQ", "ARQQ", "QUBT"],
    "space":               ["RKLB", "JOBY"],
    "ai_small_cap":        ["SOUN", "BBAI", "AI", "RXRX", "PATH", "UPST"],
    "crypto":              ["MSTR", "MARA", "RIOT", "CLSK", "COIN"],
    "biotech":             ["MRNA", "NVAX", "CRSP", "EDIT", "BEAM", "SAVA"],
    "nuclear":             ["OKLO", "SMR"],
    "clean_energy":        ["ENPH", "FSLR", "PLUG", "CHPT", "FCEL", "BLNK"],
    "materials":           ["FCX", "ALB"],
    "china_adr":           ["BABA", "PDD", "BIDU", "JD", "BILI"],
    "emerging_market":     ["SE", "NU"],
    "travel_leisure":      ["ABNB", "AAL", "RCL", "DKNG"],
    "commodities":         ["GLD", "GDX", "SLV", "USO"],
    "speculative":         ["GME", "AMC", "UVXY", "VIXY", "NKLA"],
}


def get_scan_list(account_value: float, include_tier3: bool = False) -> list[str]:
    """
    Return symbols to scan.
    Under $150: Tier 2 first — cheap fractional or options fast path.
    Over $150: Tier 1 first — options become accessible.
    Always includes commodity + leveraged sector picks from Tier 3
    so rotation into gold, oil, or sector ETFs is never missed.
    """
    if account_value < 150:
        symbols = TIER2 + TIER1
    else:
        symbols = TIER1 + TIER2
    if include_tier3:
        symbols += TIER3
    else:
        # Commodity and leveraged sector plays — always scan, never miss rotation
        symbols += ["GLD", "GDX", "SLV", "USO", "LABU", "TNA", "DPST"]
    return symbols


def get_sector_symbols(sector: str) -> list[str]:
    """Return all symbols for a given sector name."""
    return SECTORS.get(sector, [])


def tier(symbol: str) -> int:
    return TIER_MAP.get(symbol.upper(), 2)
