"""
Default watchlist for the Momentum Compounder challenge.

Tier 1: High-liquidity, heavily traded — sector leaders + index/leveraged ETFs
Tier 2: Mid-range, high-volatility — fractional equity or cheap options at $50–$150
Tier 3: Speculative, event-driven, leveraged sector plays (1 position max)

576 symbols across 91 sectors. Scanner catches momentum ANYWHERE in the market.
"""

TIER1 = [
    # ── Mega-cap tech ──────────────────────────────────────────────────────────
    "NVDA", "TSLA", "AMD", "AAPL", "META", "GOOGL", "MSFT", "AMZN", "MSTR", "SMCI",

    # ── Semiconductor (core) ───────────────────────────────────────────────────
    "ARM", "AVGO", "MU", "AMAT", "ASML", "TSM", "QCOM",

    # ── Semiconductor (expanded) ───────────────────────────────────────────────
    "LRCX", "KLAC", "MRVL", "INTC", "TXN", "ON", "NXPI",

    # ── Enterprise software / cloud (large-cap) ────────────────────────────────
    "CRM", "ORCL", "SNOW", "NET", "DDOG",
    "ADBE", "NOW", "WDAY", "INTU", "HUBS", "TEAM",

    # ── Cybersecurity ──────────────────────────────────────────────────────────
    "CRWD", "PANW", "FTNT", "ZS",

    # ── Consumer tech / media platforms ───────────────────────────────────────
    "APP", "ROKU", "SPOT", "TTD",

    # ── Streaming / entertainment ─────────────────────────────────────────────
    "NFLX", "DIS",

    # ── Mobility / consumer platform ──────────────────────────────────────────
    "UBER", "SHOP",

    # ── Mega-cap travel / e-commerce ──────────────────────────────────────────
    "BKNG", "EBAY",

    # ── Consumer / retail ─────────────────────────────────────────────────────
    "COST", "WMT", "HD", "NKE", "MCD", "SBUX", "LULU", "TGT", "LOW",

    # ── Telecom ────────────────────────────────────────────────────────────────
    "T", "VZ", "TMUS",

    # ── Auto ───────────────────────────────────────────────────────────────────
    "F", "GM",

    # ── Logistics ─────────────────────────────────────────────────────────────
    "UPS", "FDX",

    # ── Index ETFs ────────────────────────────────────────────────────────────
    "SPY", "QQQ", "IWM",

    # ── Sector ETFs (broad rotation detection) ────────────────────────────────
    "XLK", "XLF", "XLV", "XLE", "XLI",

    # ── Leveraged bull ETFs (3x) ──────────────────────────────────────────────
    "SPXL", "TQQQ", "SOXL", "FNGU", "TECL", "UPRO", "UDOW",

    # ── Leveraged bear ETFs (3x) ──────────────────────────────────────────────
    "SPXS", "SQQQ", "SOXS",

    # ── ARK / thematic ETFs ───────────────────────────────────────────────────
    "ARKK", "ARKG",

    # ── Semiconductor ETFs ────────────────────────────────────────────────────
    "SOXX", "SOXQ", "IBB",

    # ── Specialty ETFs ────────────────────────────────────────────────────────
    "GDXJ", "JETS", "HACK",

    # ── Financials (core) ─────────────────────────────────────────────────────
    "JPM", "GS", "BAC", "WFC", "V", "MA",

    # ── Financials (expanded — investment banks / private equity) ─────────────
    "C", "MS", "AXP", "BX",

    # ── Financial services ────────────────────────────────────────────────────
    "SCHW", "CME", "CBOE", "ICE",

    # ── Leveraged financials ──────────────────────────────────────────────────
    "FAS", "FAZ",

    # ── Defense ───────────────────────────────────────────────────────────────
    "LMT", "RTX", "NOC",

    # ── Industrials ───────────────────────────────────────────────────────────
    "CAT", "DE", "BA", "GE", "HON", "GD", "LHX", "MMM",

    # ── Energy majors ─────────────────────────────────────────────────────────
    "XOM", "CVX", "OXY",

    # ── Healthcare / GLP-1 ────────────────────────────────────────────────────
    "LLY", "UNH", "NVO",

    # ── Healthcare pharma (large-cap) ─────────────────────────────────────────
    "ABBV", "PFE", "REGN", "AMGN", "ISRG", "VRTX", "GILD", "JNJ",

    # ── Healthcare devices (large-cap) ────────────────────────────────────────
    "DXCM", "MDT", "SYK",

    # ── Utilities ─────────────────────────────────────────────────────────────
    "NEE",

    # ── Crypto ETF (spot Bitcoin) ─────────────────────────────────────────────
    "IBIT",

    # ── Precious metals leveraged ─────────────────────────────────────────────
    "NUGT",

    # ── Federal Reserve — Treasury yield curve ────────────────────────────────
    # Short end (rate hike/cut sensitivity): SHY tracks 1-3yr, IEF tracks 7-10yr
    "SHY", "IEF",

    # ── Federal Reserve — Aggregate bond market ───────────────────────────────
    "BND", "AGG", "LQD", "TIP",

    # ── Federal Reserve — US Dollar (hawkish Fed = strong USD) ────────────────
    "UUP",

    # ── Federal Reserve — Homebuilders (biggest rate-cut beneficiaries) ────────
    # DHI and LEN move 5–15% on a single FOMC surprise — highest beta to rate cuts
    "DHI", "LEN",

    # ── Federal Reserve — Mega-cap regional/money-center banks ────────────────
    "USB", "PNC", "TFC",

    # ── Federal Reserve — Mortgage REITs (ultra-sensitive to rate spreads) ─────
    "AGNC", "NLY",

    # ── Federal Reserve — Homebuilder ETFs (single best FOMC reaction proxy) ──
    # ITB and XHB move 5–10% on CPI surprise — faster signal than individual names
    "ITB", "XHB",

    # ── Federal Reserve — REIT ETF (rate-cut beneficiary basket) ─────────────
    "VNQ",

    # ── Federal Reserve — Asset managers (AUM fees rise with market, NIMs rise) ─
    "BLK", "TROW", "IVZ",

    # ── Federal Reserve — Insurance (float invested at higher yields) ─────────
    "PGR", "AFL", "ALL",

    # ── Federal Reserve — KBW Bank ETF (pure bank earnings play) ─────────────
    "KBWB",

    # ── Federal Reserve — Building materials (housing supply chain) ───────────
    # MLM and VMC (aggregates) surge when rate-cut cycle ignites construction
    "MLM", "VMC",
]

TIER2 = [
    # ── Fintech / payments ────────────────────────────────────────────────────
    "SOFI", "PLTR", "HOOD", "COIN", "AFRM", "PYPL", "SQ", "NU",
    "LC", "FUTU",

    # ── Financial services (mid-cap) ──────────────────────────────────────────
    "FISV", "FIS", "GPN", "IBKR", "ALLY", "APO", "PRU", "MET",

    # ── Banks ETF ─────────────────────────────────────────────────────────────
    "KBE", "KRE",

    # ── Insurance ─────────────────────────────────────────────────────────────

    # ── GLP-1 / consumer health ───────────────────────────────────────────────
    "HIMS", "CELH",

    # ── EV / mobility ─────────────────────────────────────────────────────────
    "RIVN", "NIO", "ACHR", "XPEV", "LCID",

    # ── EV components / infrastructure ────────────────────────────────────────
    "APTV", "EVGO",

    # ── Gig economy / consumer platforms ─────────────────────────────────────
    "LYFT", "DASH", "CVNA", "CHWY", "PTON",

    # ── Consumer growth (off-price / specialty retail) ────────────────────────
    "TJX", "BURL", "ROST", "ANF", "DECK", "CROX",

    # ── E-commerce / marketplace ──────────────────────────────────────────────
    "ETSY", "W", "CPNG",

    # ── Restaurants / food-tech ───────────────────────────────────────────────
    "CMG", "YUM", "CAVA", "WING", "WEN", "EAT", "TXRH", "CAKE",
    "DNUT", "BROS", "SHAK",

    # ── Hotels / leisure ──────────────────────────────────────────────────────
    "HLT", "MAR",

    # ── Social / discovery / communication ────────────────────────────────────
    "PINS", "ZM", "SNAP", "RDDT",

    # ── Quantum computing ─────────────────────────────────────────────────────
    "IONQ", "ARQQ", "QUBT",

    # ── Space / next-gen aerospace ────────────────────────────────────────────
    "RKLB", "JOBY",

    # ── AI / voice / small-cap tech ───────────────────────────────────────────
    "SOUN", "BBAI", "AI", "RXRX", "PATH", "UPST",

    # ── Mid-cap SaaS / software ────────────────────────────────────────────────
    "MDB", "CFLT", "S", "BILL", "GTLB", "VEEV", "ASAN", "TWLO", "OKTA", "ZI", "DOCU",
    "ESTC", "DOMO", "APPN",

    # ── Telecom / media ───────────────────────────────────────────────────────
    "CMCSA", "CHTR", "PARA", "WBD", "FOX", "SIRI",

    # ── Media / ad tech ───────────────────────────────────────────────────────
    "OMC",

    # ── Semiconductor mid-cap ─────────────────────────────────────────────────
    "SWKS", "MBLY", "AEHR", "SMTC",

    # ── Gaming / casinos / entertainment ──────────────────────────────────────
    "EA", "TTWO", "PENN", "MGM", "CZR", "LVS", "WYNN",
    "RBLX", "DKNG", "NTES", "TME",

    # ── Crypto mining (core) ──────────────────────────────────────────────────
    "MARA", "RIOT", "CLSK",

    # ── Crypto mining (expanded) ──────────────────────────────────────────────
    "BTBT", "HUT", "CIFR", "IREN",

    # ── Crypto / digital assets ───────────────────────────────────────────────
    "ETHA", "BITO",

    # ── Global / emerging fintech ─────────────────────────────────────────────
    "GRAB", "MELI",

    # ── Biotech / gene editing (catalyst-driven 10–30% moves) ────────────────
    "MRNA", "NVAX", "CRSP", "EDIT", "BEAM", "SAVA",

    # ── Biotech (mid-cap) ─────────────────────────────────────────────────────
    "BMRN", "ARWR", "ALNY", "BIIB",

    # ── Biotech / genomics (high-event) ───────────────────────────────────────
    "ILMN", "EXAS", "NTRA", "PACB", "BLUE", "FATE", "AGEN", "NTLA", "SGMO", "NVCR",

    # ── Biotech / oncology ────────────────────────────────────────────────────
    "EXEL", "FOLD", "AXSM",

    # ── Nuclear / clean energy ────────────────────────────────────────────────
    "OKLO", "SMR",

    # ── Solar / hydrogen / EV charging ───────────────────────────────────────
    "ENPH", "FSLR", "PLUG", "CHPT",

    # ── Clean energy (expanded) ───────────────────────────────────────────────
    "RUN", "STEM", "FLNC", "NOVA", "ARRY", "CSIQ", "DQ", "MAXN",

    # ── Utilities (clean energy mid-cap) ──────────────────────────────────────
    "AES", "CWEN",

    # ── Materials / lithium / copper ──────────────────────────────────────────
    "FCX", "ALB",

    # ── Industrial chemicals ──────────────────────────────────────────────────
    "LIN", "APD",

    # ── Precious metals / gold mining ────────────────────────────────────────
    "GOLD", "NEM", "WPM", "MP",

    # ── Real estate / REITs (core) ────────────────────────────────────────────
    "AMT", "EQIX", "PLD", "VICI", "O",

    # ── Real estate / REITs (expanded) ────────────────────────────────────────
    "SPG", "DLR", "CCI", "WPC", "NNN", "COLD", "IIPR",

    # ── Sector ETFs (additional rotation) ────────────────────────────────────
    "XLRE", "XLU", "XLP",

    # ── Thematic ETFs ─────────────────────────────────────────────────────────
    "ARKW", "ARKQ", "ARKF",
    "ICLN", "TAN", "ROBO", "PAVE", "FINX", "SKYY",

    # ── China ADRs ────────────────────────────────────────────────────────────
    "BABA", "PDD", "BIDU", "JD", "BILI",

    # ── SE Asia / LatAm / global emerging tech ────────────────────────────────
    "SE", "TCOM",

    # ── LatAm / Brazil ────────────────────────────────────────────────────────
    "VALE", "ITUB", "PAGS", "STNE", "BBD", "ARCO",

    # ── India tech ────────────────────────────────────────────────────────────
    "INFY", "WIT", "HDB",

    # ── Global markets ────────────────────────────────────────────────────────
    "GLOB",

    # ── Emerging market ETFs ──────────────────────────────────────────────────
    "KWEB", "MCHI", "INDA", "EEM", "EWZ",
    "EWJ", "EWT", "EWY", "EWG",

    # ── Travel / leisure (core) ───────────────────────────────────────────────
    "ABNB", "AAL", "RCL",

    # ── Travel / leisure (expanded) ───────────────────────────────────────────
    "UAL", "DAL", "EXPE", "CCL",

    # ── Healthcare devices (mid-cap) ──────────────────────────────────────────
    "BSX", "EW", "PODD", "ALGN", "HOLX",

    # ── Healthcare managed care / services ────────────────────────────────────
    "CI", "CVS", "HUM", "MOH", "CNC", "TDOC", "DOCS",

    # ── Energy (expanded) ─────────────────────────────────────────────────────
    "COP", "SLB", "HAL", "DVN", "PSX", "VLO", "MPC", "BP", "SU", "AR", "CTRA",

    # ── Industrials (expanded) ────────────────────────────────────────────────
    "ITW", "EMR", "PH", "UNP", "CSX", "ROK",

    # ── Commodity ETFs ────────────────────────────────────────────────────────
    "WEAT", "SOYB", "CPER", "PDBC",

    # ── Payments / global fintech ─────────────────────────────────────────────
    "WU", "EVTC",

    # ── Consumer staples (cyclical rotation) ─────────────────────────────────
    "MNST", "BYND",

    # ── Federal Reserve — Homebuilders (mid-cap, rate-sensitive) ─────────────
    # Full complex moves together on every CPI/PCE/FOMC print
    "PHM", "TOL", "KBH", "TMHC", "MHO", "NVR",

    # ── Federal Reserve — Mortgage originators ────────────────────────────────
    # Rocket and UWM volume explodes when rates drop: refi wave plays
    "RKT", "UWMC",

    # ── Federal Reserve — Mortgage REITs (expanded) ───────────────────────────
    "MFA", "TWO", "ARR", "IVR",

    # ── Federal Reserve — Regional banks (rate-spread plays) ──────────────────
    # Regional banks are the purest play on yield curve steepening
    "WAL", "ZION", "CFG", "RF", "FITB", "HBAN", "KEY", "MTB", "STT", "BK",

    # ── Federal Reserve — Currency ETFs (policy divergence plays) ─────────────
    # UDN rises when Fed is dovish (dollar weakens); FXE and FXY for cross-rate
    "UDN", "FXE", "FXY",

    # ── Federal Reserve — Treasury curve ETFs ────────────────────────────────
    # ZROZ is 25+ year zero coupon — maximum duration, maximum rate sensitivity
    "ZROZ", "EDV", "BIL",

    # ── Federal Reserve — Credit market ETFs (risk-on/risk-off proxy) ─────────
    "EMB", "VCIT", "FLOT",

    # ── Federal Reserve — Rate hedge / volatility instruments ─────────────────
    # PFIX profits directly from rising long-end rates; IVOL from rate vol spikes
    "PFIX", "IVOL",

    # ── Federal Reserve — Ultra-short Treasury (Fed funds rate proxy) ─────────
    # SHV and SGOV yield = overnight Fed funds rate — pure monetary policy plays
    "SHV", "SGOV",

    # ── Federal Reserve — TIPS (inflation expectations strip) ─────────────────
    # VTIP is short-duration; STIP is 0-5yr; SCHP is the broad market
    "VTIP", "STIP", "SCHP",

    # ── Federal Reserve — Broad Treasury ETFs (duration laddering) ───────────
    "GOVT", "VGLT",

    # ── Federal Reserve — Currency divergence (policy gap plays) ─────────────
    # FXB = pound (BoE vs Fed), FXC = loonie (BoC), FXA = Aussie (RBA), FXF = franc (SNB)
    # USDU = broader dollar basket; DXJ = hedged Japan (yen carry trade unwinding)
    "FXB", "FXC", "FXA", "FXF", "USDU", "DXJ",

    # ── Federal Reserve — Building materials / lumber (housing supply chain) ──
    "WY", "SUM", "EXP",

    # ── Federal Reserve — Apartment REITs (housing demand = rate sensitivity) ─
    "EQR", "AVB", "MAA", "CPT",

    # ── Federal Reserve — Healthcare / senior housing REITs ───────────────────
    "WELL", "VTR", "PEAK",

    # ── Federal Reserve — Mortgage servicers (refi volume plays) ─────────────
    "COOP", "PFSI", "PMT",

    # ── Federal Reserve — Insurance ETFs ─────────────────────────────────────
    "KIE", "IAK",

    # ── Federal Reserve — More insurance (float yield beneficiaries) ──────────
    "CINF", "MKL",

    # ── Federal Reserve — Asset managers (mid-cap) ────────────────────────────
    "BEN", "SEIC",

    # ── Federal Reserve — Regional banks (expanded) ───────────────────────────
    "FHN", "EWBC", "WBS",

    # ── Federal Reserve — Short-duration credit (floating-rate, SOFR-linked) ──
    "SJNK", "FALN", "USIG",
]

TIER3 = [
    # ── Meme / squeeze (1 position max, only on confirmed signal) ─────────────
    "GME", "AMC",

    # ── VIX / volatility instruments ──────────────────────────────────────────
    "UVXY", "VIXY",

    # ── Leveraged sector ETFs — event plays ───────────────────────────────────
    "LABU", "TNA", "DPST", "NAIL",

    # ── Leveraged energy ──────────────────────────────────────────────────────
    "GUSH", "ERX", "ERY",

    # ── Leveraged internet / tech / market ────────────────────────────────────
    "WEBL", "BULZ", "SDOW", "TECS",

    # ── Leveraged healthcare / biotech ────────────────────────────────────────
    "CURE", "LABD",

    # ── Leveraged aerospace / defense ─────────────────────────────────────────
    "DFEN",

    # ── Leveraged consumer discretionary ─────────────────────────────────────
    "WANT", "RETL",

    # ── Leveraged high-beta ────────────────────────────────────────────────────
    "HIBL", "HIBS",

    # ── Leveraged transportation ──────────────────────────────────────────────
    "TPOR",

    # ── Leveraged real estate ─────────────────────────────────────────────────
    "DRN",

    # ── Leveraged Europe / international ──────────────────────────────────────
    "EURL",

    # ── Leveraged mid-cap / Dow ───────────────────────────────────────────────
    "MIDU", "SPXU",

    # ── Leveraged bonds ───────────────────────────────────────────────────────
    "TMF",

    # ── Leveraged gold miners ─────────────────────────────────────────────────
    "JNUG",

    # ── Junior miners ETF ─────────────────────────────────────────────────────
    "SILJ",

    # ── China leveraged ───────────────────────────────────────────────────────
    "YINN", "YANG",

    # ── China ETF ─────────────────────────────────────────────────────────────
    "FXI", "ASHR",

    # ── Natural gas ETFs (weather / LNG catalyst plays) ──────────────────────
    "BOIL", "KOLD", "UNG",

    # ── Agriculture / broad commodities ───────────────────────────────────────
    "DBA",

    # ── Commodity ETFs (base metals / oil) ────────────────────────────────────
    "DBO", "DBB",

    # ── Macro / fixed income rate plays ───────────────────────────────────────
    "TLT", "TBT",

    # ── High yield / credit spread ────────────────────────────────────────────
    "HYG", "JNK",

    # ── Commodities ETFs ──────────────────────────────────────────────────────
    "GLD", "GDX", "SLV", "USO",

    # ── Single-stock leveraged ETFs (2x — extreme volatility) ─────────────────
    "NVDL", "TSLL", "BITX", "MSTU",

    # ── Cannabis (event-driven legalization plays) ────────────────────────────
    "SNDL", "TLRY", "ACB", "CGC", "CRON",

    # ── Energy speculative (offshore drilling) ────────────────────────────────
    "RIG",

    # ── Micro-cap speculative ─────────────────────────────────────────────────
    "FCEL", "BLNK", "NKLA",

    # ── Micro-cap speculative (expanded) ──────────────────────────────────────
    "BNGO", "OCGN", "WKHS", "MULN", "FFIE",

    # ── Speculative (next-gen tech, lidar, EV) ────────────────────────────────
    "MVIS", "IDEX", "CTRM",

    # ── Federal Reserve — Leveraged bond plays ────────────────────────────────
    # TMV is 3x bear on 20yr+ — the rate-spike weapon; SRLN/BKLN float with SOFR
    "TMV", "SRLN", "BKLN",

    # ── Federal Reserve — Leveraged Treasury ETFs (medium duration) ───────────
    # TYD/TYO are 3x on the 7-10yr belly — biggest institutional battleground
    "TYD", "TYO",

    # ── Federal Reserve — More leveraged bond products ────────────────────────
    # TTT = 3x bear 20yr (ProShares alternative to TMV)
    # UBT = 2x bull 20yr; UST = 2x bull 7-10yr; PST = 2x bear 7-10yr; TBF = 1x inverse 20yr
    "TTT", "UBT", "UST", "PST", "TBF",

    # ── Federal Reserve — EM rate divergence (Fed vs. EM central banks) ───────
    "BRZU",

    # ── Federal Reserve — VIX / volatility around FOMC ────────────────────────
    # VXX spikes into FOMC uncertainty; SVXY profits after vol crush post-decision
    "VXX", "SVXY",
]

ALL_SYMBOLS = TIER1 + TIER2 + TIER3

TIER_MAP = {s: 1 for s in TIER1}
TIER_MAP.update({s: 2 for s in TIER2})
TIER_MAP.update({s: 3 for s in TIER3})

# Sector lookup — used for rotation detection and targeted re-scans
SECTORS = {
    # ── Technology ────────────────────────────────────────────────────────────
    "mega_cap_tech":        ["NVDA", "TSLA", "AMD", "AAPL", "META", "GOOGL", "MSFT", "AMZN", "MSTR", "SMCI"],
    "semiconductor":        ["NVDA", "AMD", "SMCI", "ARM", "AVGO", "MU", "AMAT", "ASML", "TSM", "QCOM",
                             "LRCX", "KLAC", "MRVL", "INTC", "TXN", "ON", "NXPI", "SWKS", "MBLY", "AEHR"],
    "semiconductor_etf":    ["SOXX", "SOXQ", "SOXL", "SOXS"],
    "enterprise_software":  ["CRM", "ORCL", "SNOW", "NET", "DDOG", "ADBE", "NOW", "WDAY", "INTU", "HUBS", "TEAM"],
    "saas_mid_cap":         ["MDB", "CFLT", "S", "BILL", "GTLB", "VEEV", "ASAN", "TWLO", "OKTA", "ZI", "DOCU",
                             "ESTC", "DOMO", "APPN"],
    "cybersecurity":        ["CRWD", "PANW", "FTNT", "ZS", "HACK"],
    "consumer_tech":        ["APP", "ROKU", "SPOT", "TTD", "LYFT", "DASH", "CVNA", "CHWY", "PINS", "ZM"],
    "streaming_media":      ["NFLX", "DIS", "RBLX", "RDDT"],
    "telecom_media":        ["T", "VZ", "TMUS", "CMCSA", "CHTR", "PARA", "WBD", "FOX", "SIRI"],
    "ad_tech":              ["TTD", "OMC", "RDDT", "PINS"],

    # ── Consumer ──────────────────────────────────────────────────────────────
    "mobility_consumer":    ["UBER", "SHOP", "ABNB", "BKNG"],
    "consumer_retail":      ["COST", "WMT", "HD", "NKE", "MCD", "SBUX", "LULU", "TGT", "LOW",
                             "TJX", "BURL", "ROST", "ANF", "DECK", "CROX"],
    "ecommerce":            ["AMZN", "EBAY", "ETSY", "W", "CPNG", "MELI", "SE"],
    "restaurants":          ["CMG", "YUM", "CAVA", "WING", "WEN", "EAT", "TXRH", "CAKE", "DNUT", "BROS", "SHAK"],
    "hotels_leisure":       ["HLT", "MAR", "ABNB", "BKNG"],
    "gig_economy":          ["UBER", "LYFT", "DASH", "ABNB"],
    "consumer_staples":     ["MNST", "COST", "WMT", "MCD", "SBUX"],

    # ── Finance ───────────────────────────────────────────────────────────────
    "financials":           ["JPM", "GS", "BAC", "WFC", "V", "MA", "C", "MS", "AXP", "BX",
                             "SOFI", "PLTR", "HOOD", "COIN", "AFRM", "PYPL", "SQ", "NU", "LC", "FUTU"],
    "investment_banks":     ["GS", "MS", "BX", "JPM", "C"],
    "financial_services":   ["SCHW", "CME", "CBOE", "ICE", "FISV", "FIS", "GPN", "IBKR", "ALLY", "APO"],
    "insurance":            ["PRU", "MET", "PGR", "AFL", "ALL", "CINF", "MKL", "KIE", "IAK"],
    "banks_etf":            ["KBE", "KRE", "FAS", "FAZ"],

    # ── Industrials / Transport ────────────────────────────────────────────────
    "defense":              ["LMT", "RTX", "NOC", "GD", "LHX", "DFEN"],
    "industrials":          ["CAT", "DE", "BA", "GE", "HON", "GD", "LHX", "MMM",
                             "ITW", "EMR", "PH", "UNP", "CSX", "ROK"],
    "logistics":            ["UPS", "FDX"],
    "auto":                 ["F", "GM", "TSLA", "RIVN", "NIO", "ACHR", "XPEV", "LCID", "APTV"],

    # ── Energy ────────────────────────────────────────────────────────────────
    "energy":               ["XOM", "CVX", "OXY", "COP", "SLB", "HAL", "DVN", "PSX", "VLO", "MPC",
                             "BP", "SU", "AR", "CTRA", "XLE", "USO", "GUSH", "ERX", "ERY"],
    "natural_gas":          ["BOIL", "KOLD", "UNG", "AR", "CTRA"],

    # ── Healthcare ────────────────────────────────────────────────────────────
    "healthcare_glp1":      ["LLY", "UNH", "NVO", "HIMS", "CELH"],
    "healthcare_pharma":    ["ABBV", "PFE", "REGN", "AMGN", "ISRG", "VRTX", "GILD", "JNJ",
                             "BIIB", "BMRN", "ARWR", "ALNY"],
    "healthcare_devices":   ["MDT", "SYK", "DXCM", "BSX", "EW", "PODD", "ALGN", "HOLX"],
    "healthcare_services":  ["CI", "CVS", "HUM", "MOH", "CNC", "TDOC", "DOCS"],
    "biotech":              ["MRNA", "NVAX", "CRSP", "EDIT", "BEAM", "SAVA",
                             "ILMN", "EXAS", "NTRA", "PACB", "BLUE", "FATE", "AGEN", "NTLA", "SGMO", "NVCR",
                             "EXEL", "FOLD", "AXSM", "IBB", "LABU", "LABD"],

    # ── Emerging tech ─────────────────────────────────────────────────────────
    "ev_mobility":          ["TSLA", "RIVN", "NIO", "ACHR", "XPEV", "LCID", "APTV", "EVGO"],
    "quantum":              ["IONQ", "ARQQ", "QUBT"],
    "space":                ["RKLB", "JOBY"],
    "ai_small_cap":         ["SOUN", "BBAI", "AI", "RXRX", "PATH", "UPST"],
    "nuclear":              ["OKLO", "SMR"],

    # ── Crypto ────────────────────────────────────────────────────────────────
    "crypto":               ["MSTR", "MARA", "RIOT", "CLSK", "COIN", "BTBT", "HUT", "CIFR", "IREN"],
    "crypto_etf":           ["IBIT", "BITO", "ETHA", "BITX", "MSTU"],

    # ── Clean energy ──────────────────────────────────────────────────────────
    "clean_energy":         ["ENPH", "FSLR", "PLUG", "CHPT", "RUN", "STEM", "FLNC", "NOVA",
                             "ARRY", "CSIQ", "DQ", "MAXN", "AES", "CWEN", "FCEL", "BLNK",
                             "ICLN", "TAN"],

    # ── Materials ─────────────────────────────────────────────────────────────
    "materials":            ["FCX", "ALB", "GOLD", "NEM", "WPM", "MP", "LIN", "APD"],
    "precious_metals":      ["GLD", "GDX", "SLV", "GOLD", "NEM", "WPM", "NUGT", "GDXJ", "JNUG", "SILJ"],

    # ── Real estate ───────────────────────────────────────────────────────────
    "real_estate":          ["AMT", "EQIX", "PLD", "VICI", "O", "SPG", "DLR", "CCI", "WPC", "NNN",
                             "COLD", "IIPR", "XLRE", "DRN"],

    # ── Utilities ─────────────────────────────────────────────────────────────
    "utilities":            ["NEE", "AES", "CWEN", "XLU"],

    # ── International / EM ────────────────────────────────────────────────────
    "china_adr":            ["BABA", "PDD", "BIDU", "JD", "BILI", "TCOM", "NTES", "TME"],
    "china_etf":            ["KWEB", "MCHI", "FXI", "ASHR", "YINN", "YANG"],
    "emerging_market":      ["SE", "NU", "GRAB", "MELI", "VALE", "ITUB", "PAGS", "STNE", "BBD", "ARCO"],
    "emerging_market_etf":  ["EEM", "EWZ", "EWJ", "EWT", "EWY", "EWG", "INDA"],
    "india":                ["INFY", "WIT", "HDB", "INDA"],
    "latam":                ["VALE", "ITUB", "PAGS", "STNE", "BBD", "ARCO", "MELI", "EWZ"],

    # ── Travel ────────────────────────────────────────────────────────────────
    "travel_leisure":       ["ABNB", "AAL", "RCL", "DKNG", "UAL", "DAL", "EXPE", "CCL", "BKNG",
                             "HLT", "MAR", "JETS", "LVS", "WYNN", "PENN", "MGM", "CZR"],

    # ── Gaming / entertainment ────────────────────────────────────────────────
    "gaming_casinos":       ["EA", "TTWO", "RBLX", "DKNG", "PENN", "MGM", "CZR", "LVS", "WYNN",
                             "NTES", "TME"],

    # ── Commodities ───────────────────────────────────────────────────────────
    "commodities":          ["GLD", "GDX", "SLV", "USO", "GOLD", "NEM", "WPM", "DBO", "DBB"],
    "agriculture":          ["DBA", "WEAT", "SOYB"],
    "commodities_broad":    ["PDBC", "CPER", "DBO", "DBB"],

    # ── Macro / bonds ─────────────────────────────────────────────────────────
    "macro_rates":          ["TLT", "TBT", "TMF", "HYG", "JNK"],
    "volatility":           ["UVXY", "VIXY"],

    # ── ETF blocks ────────────────────────────────────────────────────────────
    "index_etf":            ["SPY", "QQQ", "IWM"],
    "sector_etf":           ["XLK", "XLF", "XLV", "XLE", "XLI", "XLRE", "XLU", "XLP"],
    "thematic_etf":         ["ARKK", "ARKG", "ARKW", "ARKQ", "ARKF", "ICLN", "TAN", "ROBO",
                             "PAVE", "FINX", "SKYY", "HACK", "JETS", "IBB"],
    "leveraged_bull":       ["SPXL", "TQQQ", "SOXL", "FNGU", "TECL", "UPRO", "UDOW", "FAS",
                             "LABU", "TNA", "DPST", "NAIL", "GUSH", "ERX", "WEBL", "BULZ", "CURE",
                             "DFEN", "WANT", "RETL", "HIBL", "TPOR", "DRN", "EURL", "MIDU", "JNUG"],
    "leveraged_bear":       ["SPXS", "SQQQ", "SOXS", "FAZ", "ERY", "SDOW", "TECS", "LABD",
                             "HIBS", "YANG", "SPXU"],
    "leveraged_bonds":      ["TMF", "TBT", "TMV"],
    "leveraged_single":     ["NVDL", "TSLL", "BITX", "MSTU"],

    # ── Federal Reserve themes (rate policy → sector rotation) ─────────────────
    "fed_treasury_curve":   ["SHY", "IEF", "TLT", "BND", "AGG", "LQD", "TIP",
                             "ZROZ", "EDV", "BIL", "VCIT", "FLOT", "EMB",
                             "TMF", "TBT", "TMV"],
    "fed_homebuilders":     ["DHI", "LEN", "PHM", "TOL", "KBH", "TMHC", "MHO", "NVR"],
    "fed_mortgage_reits":   ["AGNC", "NLY", "MFA", "TWO", "ARR", "IVR"],
    "fed_regional_banks":   ["USB", "PNC", "TFC", "WAL", "ZION", "CFG", "RF",
                             "FITB", "HBAN", "KEY", "MTB", "STT", "BK", "FHN", "EWBC", "WBS"],
    "fed_mortgage_origin":  ["RKT", "UWMC"],
    "fed_dollar_currency":  ["UUP", "UDN", "FXE", "FXY"],
    "fed_rate_hedge":       ["PFIX", "IVOL", "SRLN", "BKLN"],
    "fed_credit_market":    ["HYG", "JNK", "EMB", "VCIT", "FLOT", "SRLN", "BKLN",
                             "SJNK", "FALN", "USIG"],
    "fed_homebuilder_etf":  ["ITB", "XHB", "NAIL"],
    "fed_reit_etf":         ["VNQ", "XLRE", "DRN"],
    "fed_apartment_reit":   ["EQR", "AVB", "MAA", "CPT"],
    "fed_healthcare_reit":  ["WELL", "VTR", "PEAK"],
    "fed_building_mats":    ["MLM", "VMC", "WY", "SUM", "EXP"],
    "fed_mortgage_svc":     ["COOP", "PFSI", "PMT"],
    "fed_insurance":        ["PGR", "AFL", "ALL", "PRU", "MET", "CINF", "MKL", "KIE", "IAK"],
    "fed_asset_managers":   ["BLK", "TROW", "IVZ", "BEN", "SEIC", "SCHW", "IBKR"],
    # fed_regional_banks+ merged into fed_regional_banks above
    "fed_treasury_short":   ["SHV", "SGOV", "BIL", "SHY"],
    "fed_treasury_long":    ["TLT", "ZROZ", "EDV", "VGLT", "GOVT"],
    "fed_tips":             ["TIP", "VTIP", "STIP", "SCHP"],
    "fed_treasury_lev":     ["TMF", "TBT", "TMV", "TTT", "UBT", "UST", "TYD", "TYO", "PST", "TBF"],
    "fed_currency":         ["UUP", "UDN", "FXE", "FXY", "FXB", "FXC", "FXA", "FXF", "USDU", "DXJ"],
    "fed_fomc_vol":         ["VXX", "SVXY", "UVXY", "VIXY", "PFIX", "IVOL"],
    "fed_em_divergence":    ["BRZU", "EMB", "EWZ", "EEM"],

    # ── Speculative ───────────────────────────────────────────────────────────
    "cannabis":             ["SNDL", "TLRY", "ACB", "CGC", "CRON", "IIPR"],
    "speculative":          ["GME", "AMC", "UVXY", "VIXY", "NKLA", "BNGO", "OCGN", "WKHS",
                             "MULN", "FFIE", "MVIS", "IDEX", "CTRM", "RIG",
                             "SNDL", "TLRY", "ACB", "CGC", "CRON"],
}


SCAN_BATCH_SIZE = 40  # ponytail: MCP returns quotes fine at 40; closes omitted >20 but RS uses adjusted_previous_close from quote, not closes


def get_tiered_scan_symbols(spy_change_pct: float) -> tuple[list[str], str]:
    """
    Return (symbols, tier_label) gated on SPY's day change.
    RS threshold is >3% — on flat days (<1% SPY) nothing in Tier 2/3 passes.
    Cuts scan from 576 → 164 symbols on consolidation days (the common case).
    """
    abs_chg = abs(spy_change_pct)
    if abs_chg < 0.01:  # SPY <1%: Tier 1 only
        return TIER1[:], "tier1"
    if abs_chg < 0.02:  # SPY 1-2%: Tier 1 + Tier 2
        return list(dict.fromkeys(TIER1 + TIER2)), "tier1+tier2"
    return list(dict.fromkeys(TIER1 + TIER2 + TIER3)), "all"  # SPY ≥2%


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
        # Key T3 rotation markers — commodity, rate, vol, and leveraged sector plays.
        # XLV/XLE/XLF/XLI are already in TIER1; omit them here to avoid duplicate scoring.
        symbols += ["GLD", "GDX", "SLV", "USO", "LABU", "TNA", "DPST", "TLT", "BOIL", "GUSH", "HYG"]
    return list(dict.fromkeys(symbols))  # preserve order, deduplicate any remaining overlap


def get_sector_symbols(sector: str) -> list[str]:
    """Return all symbols for a given sector name."""
    return SECTORS.get(sector, [])


def tier(symbol: str) -> int:
    return TIER_MAP.get(symbol.upper(), 2)
