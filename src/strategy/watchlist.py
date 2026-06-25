"""
Default watchlist for the Momentum Compounder challenge.

Tier 1: High-liquidity, heavily traded — sector leaders + index/leveraged ETFs
Tier 2: Mid-range, high-volatility — fractional equity or cheap options at $50–$150
Tier 3: Speculative, event-driven, leveraged sector plays (1 position max)

~240 symbols across 35 sectors. Scanner catches momentum ANYWHERE in the market.
"""

TIER1 = [
    # ── Mega-cap tech ──────────────────────────────────────────────────────────
    "NVDA", "TSLA", "AMD", "AAPL", "META", "GOOGL", "MSFT", "AMZN", "MSTR", "SMCI",

    # ── Semiconductor (core) ───────────────────────────────────────────────────
    "ARM", "AVGO", "MU", "AMAT", "ASML", "TSM", "QCOM",

    # ── Semiconductor (expanded) ───────────────────────────────────────────────
    "LRCX", "KLAC", "MRVL", "INTC", "TXN",

    # ── Enterprise software / cloud ────────────────────────────────────────────
    "CRM", "ORCL", "SNOW", "NET", "DDOG",

    # ── Cybersecurity ──────────────────────────────────────────────────────────
    "CRWD", "PANW", "FTNT", "ZS",

    # ── Consumer tech / media platforms ───────────────────────────────────────
    "APP", "ROKU", "SPOT", "TTD",

    # ── Streaming / entertainment ─────────────────────────────────────────────
    "NFLX", "DIS",

    # ── Mobility / consumer platform ──────────────────────────────────────────
    "UBER", "SHOP",

    # ── Mega-cap travel ────────────────────────────────────────────────────────
    "BKNG",

    # ── Consumer / retail ─────────────────────────────────────────────────────
    "COST", "WMT", "HD", "NKE", "MCD", "SBUX", "LULU",

    # ── Index ETFs ────────────────────────────────────────────────────────────
    "SPY", "QQQ", "IWM",

    # ── Leveraged bull ETFs (3x — amplify sector moves for fractional plays) ──
    "SPXL", "TQQQ", "SOXL", "FNGU", "TECL",

    # ── Leveraged bear ETFs (3x — downside / hedge regime) ────────────────────
    "SPXS", "SQQQ", "SOXS",

    # ── ARK / thematic ETFs ───────────────────────────────────────────────────
    "ARKK",

    # ── Financials (core) ─────────────────────────────────────────────────────
    "JPM", "GS", "BAC", "WFC", "V", "MA",

    # ── Financials (expanded — investment banks / private equity) ─────────────
    "C", "MS", "AXP", "BX",

    # ── Leveraged financials ETF ──────────────────────────────────────────────
    "FAS", "FAZ",

    # ── Defense ───────────────────────────────────────────────────────────────
    "LMT", "RTX", "NOC",

    # ── Industrials ───────────────────────────────────────────────────────────
    "CAT", "DE", "BA", "GE", "HON",

    # ── Energy majors ─────────────────────────────────────────────────────────
    "XOM", "CVX", "OXY",

    # ── Healthcare / GLP-1 ────────────────────────────────────────────────────
    "LLY", "UNH", "NVO",

    # ── Healthcare pharma (large-cap) ─────────────────────────────────────────
    "ABBV", "PFE", "REGN", "AMGN", "ISRG", "VRTX", "GILD",

    # ── Crypto ETF (spot Bitcoin) ─────────────────────────────────────────────
    "IBIT",

    # ── Precious metals leveraged ─────────────────────────────────────────────
    "NUGT",
]

TIER2 = [
    # ── Fintech / payments ────────────────────────────────────────────────────
    "SOFI", "PLTR", "HOOD", "COIN", "AFRM", "PYPL", "SQ", "NU",
    "LC", "FUTU",

    # ── GLP-1 / consumer health (high volatility, hot narrative) ──────────────
    "HIMS", "CELH",

    # ── EV / mobility ─────────────────────────────────────────────────────────
    "RIVN", "NIO", "ACHR", "XPEV", "LCID",

    # ── Gig economy / consumer growth ─────────────────────────────────────────
    "LYFT", "DASH", "CVNA", "CHWY",

    # ── Consumer growth (restaurants / lifestyle) ─────────────────────────────
    "CMG", "YUM", "CAVA", "WING",

    # ── Social / discovery ────────────────────────────────────────────────────
    "PINS", "ZM",

    # ── Quantum computing ─────────────────────────────────────────────────────
    "IONQ", "ARQQ", "QUBT",

    # ── Space / next-gen aerospace ────────────────────────────────────────────
    "RKLB", "JOBY",

    # ── AI / voice / small-cap tech ───────────────────────────────────────────
    "SOUN", "BBAI", "AI", "RXRX", "PATH", "UPST",

    # ── Mid-cap SaaS / software ────────────────────────────────────────────────
    "MDB", "CFLT", "S", "BILL", "GTLB", "VEEV", "ASAN", "TWLO", "OKTA", "ZI", "DOCU",

    # ── Crypto mining (core) ──────────────────────────────────────────────────
    "MARA", "RIOT", "CLSK",

    # ── Crypto mining (expanded) ──────────────────────────────────────────────
    "BTBT", "HUT", "CIFR", "IREN",

    # ── Global / emerging fintech ─────────────────────────────────────────────
    "GRAB", "MELI",

    # ── Biotech / gene editing (catalyst-driven 10–30% moves) ────────────────
    "MRNA", "NVAX", "CRSP", "EDIT", "BEAM", "SAVA",

    # ── Biotech (mid-cap, high-conviction) ────────────────────────────────────
    "BMRN", "ARWR", "ALNY", "BIIB",

    # ── Nuclear / clean energy ────────────────────────────────────────────────
    "OKLO", "SMR",

    # ── Solar / hydrogen / EV charging ───────────────────────────────────────
    "ENPH", "FSLR", "PLUG", "CHPT",

    # ── Clean energy (expanded) ───────────────────────────────────────────────
    "RUN", "STEM", "FLNC", "NOVA",

    # ── Materials / lithium / copper ──────────────────────────────────────────
    "FCX", "ALB",

    # ── Precious metals / gold mining ────────────────────────────────────────
    "GOLD", "NEM", "WPM", "MP",

    # ── Real estate / REITs ───────────────────────────────────────────────────
    "AMT", "EQIX", "PLD", "VICI", "O",

    # ── China ADRs ────────────────────────────────────────────────────────────
    "BABA", "PDD", "BIDU", "JD", "BILI",

    # ── SE Asia / LatAm / global emerging tech ────────────────────────────────
    "SE", "TCOM",

    # ── Emerging market ETFs ──────────────────────────────────────────────────
    "KWEB", "MCHI", "INDA", "EEM", "EWZ",

    # ── Social / entertainment / gaming ───────────────────────────────────────
    "SNAP", "RDDT", "RBLX", "DKNG",

    # ── Travel / leisure (core) ───────────────────────────────────────────────
    "ABNB", "AAL", "RCL",

    # ── Travel / leisure (expanded airlines + cruise + booking) ───────────────
    "UAL", "DAL", "EXPE", "CCL",
]

TIER3 = [
    # ── Meme / squeeze (1 position max, only on confirmed signal) ─────────────
    "GME", "AMC",

    # ── VIX / volatility instruments ──────────────────────────────────────────
    "UVXY", "VIXY",

    # ── Leveraged sector ETFs — event plays ───────────────────────────────────
    "LABU", "TNA", "DPST", "NAIL",

    # ── Leveraged energy ETFs ─────────────────────────────────────────────────
    "GUSH", "ERX", "ERY",

    # ── Leveraged internet / tech / market ────────────────────────────────────
    "WEBL", "BULZ", "SDOW",

    # ── Leveraged healthcare ──────────────────────────────────────────────────
    "CURE",

    # ── Natural gas ETFs (weather / LNG catalyst plays) ──────────────────────
    "BOIL", "KOLD", "UNG",

    # ── Agriculture / broad commodities ───────────────────────────────────────
    "DBA",

    # ── Macro / fixed income rate plays ───────────────────────────────────────
    "TLT", "TBT",

    # ── Commodities ETFs ──────────────────────────────────────────────────────
    "GLD", "GDX", "SLV", "USO",

    # ── Micro-cap speculative ─────────────────────────────────────────────────
    "FCEL", "BLNK", "NKLA",

    # ── Micro-cap speculative (expanded) ──────────────────────────────────────
    "BNGO", "OCGN", "WKHS", "MULN", "FFIE",
]

ALL_SYMBOLS = TIER1 + TIER2 + TIER3

TIER_MAP = {s: 1 for s in TIER1}
TIER_MAP.update({s: 2 for s in TIER2})
TIER_MAP.update({s: 3 for s in TIER3})

# Sector lookup — used for rotation detection and targeted re-scans
SECTORS = {
    "mega_cap_tech":       ["NVDA", "TSLA", "AMD", "AAPL", "META", "GOOGL", "MSFT", "AMZN", "MSTR", "SMCI"],
    "semiconductor":       ["NVDA", "AMD", "SMCI", "ARM", "AVGO", "MU", "AMAT", "ASML", "TSM", "QCOM",
                            "LRCX", "KLAC", "MRVL", "INTC", "TXN"],
    "enterprise_software": ["CRM", "ORCL", "SNOW", "NET", "DDOG"],
    "cybersecurity":       ["CRWD", "PANW", "FTNT", "ZS"],
    "saas_mid_cap":        ["MDB", "CFLT", "S", "BILL", "GTLB", "VEEV", "ASAN", "TWLO", "OKTA", "ZI", "DOCU"],
    "consumer_tech":       ["APP", "ROKU", "SPOT", "TTD", "LYFT", "DASH", "CVNA", "CHWY", "PINS", "ZM"],
    "streaming_media":     ["NFLX", "DIS", "RBLX", "RDDT"],
    "mobility_consumer":   ["UBER", "SHOP", "ABNB", "BKNG"],
    "consumer_retail":     ["COST", "WMT", "HD", "NKE", "MCD", "SBUX", "LULU", "CMG", "YUM", "CAVA", "WING"],
    "index_etf":           ["SPY", "QQQ", "IWM"],
    "leveraged_bull":      ["SPXL", "TQQQ", "SOXL", "FNGU", "TECL", "LABU", "TNA", "DPST", "NAIL",
                            "GUSH", "ERX", "WEBL", "BULZ", "CURE"],
    "leveraged_bear":      ["SPXS", "SQQQ", "SOXS", "FAZ", "ERY", "SDOW"],
    "thematic_etf":        ["ARKK"],
    "financials":          ["JPM", "GS", "BAC", "WFC", "V", "MA", "C", "MS", "AXP", "BX",
                            "SOFI", "PLTR", "HOOD", "COIN", "AFRM", "PYPL", "SQ", "NU", "LC", "FUTU"],
    "defense":             ["LMT", "RTX", "NOC"],
    "industrials":         ["CAT", "DE", "BA", "GE", "HON"],
    "energy":              ["XOM", "CVX", "OXY", "USO", "GUSH", "ERX", "ERY"],
    "healthcare_glp1":     ["LLY", "UNH", "NVO", "HIMS", "CELH"],
    "healthcare_pharma":   ["ABBV", "PFE", "REGN", "AMGN", "ISRG", "VRTX", "GILD", "BIIB",
                            "BMRN", "ARWR", "ALNY"],
    "ev_mobility":         ["TSLA", "RIVN", "NIO", "ACHR", "XPEV", "LCID"],
    "quantum":             ["IONQ", "ARQQ", "QUBT"],
    "space":               ["RKLB", "JOBY"],
    "ai_small_cap":        ["SOUN", "BBAI", "AI", "RXRX", "PATH", "UPST"],
    "crypto":              ["MSTR", "MARA", "RIOT", "CLSK", "COIN", "BTBT", "HUT", "CIFR", "IREN"],
    "crypto_etf":          ["IBIT"],
    "biotech":             ["MRNA", "NVAX", "CRSP", "EDIT", "BEAM", "SAVA", "BMRN", "ARWR", "ALNY", "BIIB"],
    "nuclear":             ["OKLO", "SMR"],
    "clean_energy":        ["ENPH", "FSLR", "PLUG", "CHPT", "RUN", "STEM", "FLNC", "NOVA", "FCEL", "BLNK"],
    "materials":           ["FCX", "ALB", "GOLD", "NEM", "WPM", "MP"],
    "real_estate":         ["AMT", "EQIX", "PLD", "VICI", "O"],
    "china_adr":           ["BABA", "PDD", "BIDU", "JD", "BILI", "TCOM"],
    "emerging_market":     ["SE", "NU", "GRAB", "MELI"],
    "emerging_market_etf": ["KWEB", "MCHI", "INDA", "EEM", "EWZ"],
    "travel_leisure":      ["ABNB", "AAL", "RCL", "DKNG", "UAL", "DAL", "EXPE", "CCL", "BKNG"],
    "commodities":         ["GLD", "GDX", "SLV", "USO", "GOLD", "NEM", "WPM"],
    "natural_gas":         ["BOIL", "KOLD", "UNG"],
    "agriculture":         ["DBA"],
    "macro_rates":         ["TLT", "TBT"],
    "volatility":          ["UVXY", "VIXY"],
    "speculative":         ["GME", "AMC", "UVXY", "VIXY", "NKLA", "BNGO", "OCGN", "WKHS", "MULN", "FFIE"],
    "precious_metals":     ["GLD", "GDX", "SLV", "GOLD", "NEM", "WPM", "NUGT"],
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
        # Commodity, rate, and leveraged sector plays — always scan, never miss rotation
        symbols += ["GLD", "GDX", "SLV", "USO", "LABU", "TNA", "DPST", "TLT", "BOIL", "GUSH"]
    return symbols


def get_sector_symbols(sector: str) -> list[str]:
    """Return all symbols for a given sector name."""
    return SECTORS.get(sector, [])


def tier(symbol: str) -> int:
    return TIER_MAP.get(symbol.upper(), 2)
