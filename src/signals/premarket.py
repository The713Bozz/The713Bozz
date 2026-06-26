"""
Pre-market intelligence pass — 9:00 to 9:30 AM ET.

Scans Tier 1 watchlist for:
  1. Pre-market gap ≥ threshold (default 2%) vs prior close
  2. News catalyst from last 48 hours
  3. Catalyst type + sentiment classification

Output: priority candidates flagged before the 9:30 AM technical scan.

Entry points:
  run_premarket_scan(quotes_map)
      Agent path: pass pre-fetched MCP quotes for Tier 1 symbols.
  run_premarket_scan_standalone()
      CLI path: fetches Finnhub quotes for Tier 1, calls run_premarket_scan.
"""
from __future__ import annotations

import json as _json
from concurrent.futures import ThreadPoolExecutor, as_completed as _as_completed
from dataclasses import dataclass
from pathlib import Path as _Path

from src.data import finnhub as _finnhub


def _load_cfg() -> dict:
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as f:
            return _json.load(f).get("premarket", {})
    except Exception:
        return {}


# Catalyst keyword map: (type, sentiment, keywords)
# Sentiment scale: +2 strongly positive, +1 positive, 0 neutral, -1 negative, -2 strongly negative
_CATALYST_MAP: list[tuple[str, int, list[str]]] = [
    ("merger",         +2, [
        "to be acquired", "buyout agreement", "merger agreement",
        "acquisition deal", "definitive agreement to acquire",
        "going private", "tender offer",
    ]),
    ("fda_approval",   +2, [
        "fda approved", "fda approval", "cleared by fda",
        "nda approved", "bla approved", "510k clearance",
        "granted approval", "approved the new drug",
    ]),
    ("fda_rejection",  -2, [
        "fda rejected", "complete response letter", "crl issued",
        "refuse to file", "clinical hold", "fda declined",
    ]),
    ("legal",          -2, [
        "class action lawsuit", "sec charges", "sec investigation",
        "securities fraud", "subpoena received", "doj investigation",
    ]),
    ("earnings_beat",  +1, [
        "beats estimates", "beat estimates", "exceeds estimates",
        "tops estimates", "eps beat", "above expectations",
        "record earnings", "blowout quarter", "earnings beat",
    ]),
    ("earnings_miss",  -1, [
        "misses estimates", "missed estimates", "below estimates",
        "disappoints", "eps miss", "falls short", "weaker than expected",
        "earnings miss", "misses expectations",
    ]),
    ("guidance_raise", +1, [
        "raises guidance", "raised outlook", "increases guidance",
        "raised guidance", "raised its outlook", "boosted guidance",
        "increased its forecast",
    ]),
    ("guidance_cut",   -1, [
        "cuts guidance", "lowers outlook", "reduces guidance",
        "lowered guidance", "cut its forecast", "lowered its outlook",
        "trimmed guidance",
    ]),
    ("upgrade",        +1, [
        "upgraded to buy", "upgraded to outperform", "raises price target",
        "initiates with buy", "strong buy rating", "upgraded to overweight",
    ]),
    ("downgrade",      -1, [
        "downgraded to sell", "downgraded to underperform", "lowered price target",
        "cut to sell", "downgraded to underweight", "reduces to sell",
    ]),
    ("contract",       +1, [
        "awarded contract", "major contract", "supply agreement",
        "multi-year deal", "strategic partnership", "licensing deal",
    ]),
]


@dataclass
class PremarketCandidate:
    symbol: str
    gap_pct: float           # pre-market move vs prior close (positive = up)
    catalyst_type: str       # e.g. "earnings_beat", "upgrade", "none"
    catalyst_sentiment: int  # -2 to +2
    headline: str            # best matching headline (≤120 chars)
    priority: int            # composite sort key — higher is more actionable
    watch_note: str          # human-readable one-liner for the report


def _classify_catalyst(symbol: str) -> tuple[str, int, str]:
    """
    Fetch last 48h Finnhub headlines and match against _CATALYST_MAP.
    Returns (catalyst_type, sentiment, best_headline).
    Returns ("none", 0, first_headline) when no keyword matches.
    Returns ("none", 0, "") on API failure.
    """
    text = _finnhub.news_headlines_text(symbol, days_back=2)
    if not text:
        return "none", 0, ""
    text_lower = text.lower()
    for cat_type, sentiment, keywords in _CATALYST_MAP:
        for kw in keywords:
            if kw in text_lower:
                for hl in text.split(" | "):
                    if kw in hl.lower():
                        return cat_type, sentiment, hl.strip()[:120]
                return cat_type, sentiment, text.split(" | ")[0].strip()[:120]
    return "none", 0, text.split(" | ")[0].strip()[:120]


def run_premarket_scan(
    quotes_map: dict[str, dict],
    gap_threshold: float | None = None,
) -> list[PremarketCandidate]:
    """
    Identify pre-market gap candidates from a pre-fetched quotes dict.

    quotes_map: {symbol: quote_dict} — supports both MCP field names
                (last_trade_price / adjusted_previous_close) and
                Finnhub field names (c / pc).
    gap_threshold: minimum absolute gap to qualify (default: config premarket.gap_threshold_pct = 2%).

    Filtering rules:
      - Gap down + strongly negative catalyst (-2) → falling knife, excluded.
      - All other combinations surface regardless of direction — user decides.
    Returns candidates sorted by priority (highest first).
    """
    cfg = _load_cfg()
    if gap_threshold is None:
        gap_threshold = cfg.get("gap_threshold_pct", 0.02)

    gapped: list[tuple[str, float]] = []
    for sym, q in quotes_map.items():
        try:
            price = float(
                q.get("last_trade_price") or q.get("ask_price") or q.get("c") or 0
            )
            prev = float(
                q.get("adjusted_previous_close") or q.get("previous_close") or q.get("pc") or 0
            )
            if price > 0 and prev > 0:
                gap = (price - prev) / prev
                if abs(gap) >= gap_threshold:
                    gapped.append((sym, gap))
        except (TypeError, ValueError):
            continue

    if not gapped:
        return []

    # News only for gapped symbols — typically 0–10 in pre-market
    news_results: dict[str, tuple[str, int, str]] = {}
    with ThreadPoolExecutor(max_workers=min(len(gapped), 8)) as pool:
        futures = {pool.submit(_classify_catalyst, sym): sym for sym, _ in gapped}
        for fut in _as_completed(futures):
            sym = futures[fut]
            try:
                news_results[sym] = fut.result()
            except Exception:
                news_results[sym] = ("none", 0, "")

    candidates: list[PremarketCandidate] = []
    for sym, gap in gapped:
        cat_type, sentiment, headline = news_results.get(sym, ("none", 0, ""))

        # Exclude falling knives: gap down + hard negative catalyst (FDA rejection, legal, etc.)
        if gap < 0 and sentiment <= -2:
            continue

        # Priority: gap magnitude (1 pt per 1%) + catalyst sentiment weight
        gap_score = int(abs(gap) * 100)
        priority = gap_score + (sentiment * 2)

        direction = "GAP UP" if gap > 0 else "GAP DOWN"
        cat_label = cat_type.replace("_", " ").title() if cat_type != "none" else ""
        watch_note = f"{direction} {gap:+.1%}"
        if cat_label:
            watch_note += f" — {cat_label}"
        # Flag IV crush risk on post-earnings gaps — option buyers get hit even on beats
        if cat_type in ("earnings_beat", "earnings_miss") and abs(gap) >= 0.03:
            watch_note += " [⚠ post-earnings: IV crush risk on options]"

        candidates.append(PremarketCandidate(
            symbol=sym,
            gap_pct=gap,
            catalyst_type=cat_type,
            catalyst_sentiment=sentiment,
            headline=headline,
            priority=priority,
            watch_note=watch_note,
        ))

    return sorted(candidates, key=lambda c: c.priority, reverse=True)


def run_premarket_scan_standalone(gap_threshold: float | None = None) -> list[PremarketCandidate]:
    """
    CLI standalone path: fetch Tier 1 + _ALWAYS_SCAN quotes from Finnhub in parallel,
    then run the pre-market intelligence pass.
    """
    from src.strategy.watchlist import get_tiered_scan_symbols
    cfg = _load_cfg()
    if gap_threshold is None:
        gap_threshold = cfg.get("gap_threshold_pct", 0.02)

    # Tier 1 only pre-market — SPY hasn't confirmed direction yet
    symbols, _ = get_tiered_scan_symbols(spy_change_pct=0.0)

    quotes_map: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_finnhub.current_quote, sym): sym for sym in symbols}
        for fut in _as_completed(futures):
            sym = futures[fut]
            try:
                q = fut.result()
                if q:
                    quotes_map[sym] = q
            except Exception:
                pass

    print(f"[PREMARKET] {len(quotes_map)}/{len(symbols)} quotes fetched")
    return run_premarket_scan(quotes_map, gap_threshold=gap_threshold)


def format_premarket_report(
    candidates: list[PremarketCandidate],
    gap_threshold: float = 0.02,
) -> str:
    """Human-readable pre-market intelligence report."""
    _SENT_LABELS = {
        2: "STRONGLY +", 1: "POSITIVE", 0: "NEUTRAL", -1: "NEGATIVE", -2: "STRONGLY -",
    }
    lines = [f"\n{'='*62}", f"  PRE-MARKET INTELLIGENCE PASS (≥{gap_threshold:.0%} gap)", f"{'='*62}"]

    if not candidates:
        lines.append("  No qualifying pre-market gaps detected.")
        lines.append("  → Standard technical scan at 9:30 AM open.")
        return "\n".join(lines)

    lines.append(f"  {len(candidates)} candidate(s) flagged — verify volume at 9:30 AM open:\n")
    for c in candidates:
        sent_str = _SENT_LABELS.get(c.catalyst_sentiment, "NEUTRAL")
        gap_str = f"{c.gap_pct:+.1%}"
        cat_str = c.catalyst_type.replace("_", " ").upper() if c.catalyst_type != "none" else "NO CATALYST"
        lines.append(f"  !! {c.symbol:<7} {gap_str:<8}  {cat_str:<22}  [{sent_str}]")
        if c.headline:
            lines.append(f'     "{c.headline}"')
        lines.append(f"     {c.watch_note}")
        lines.append("")

    lines += [
        "  ENTRY RULES AT OPEN:",
        "  1. Gap + catalyst + volume surge ≥1.5× avg → highest conviction",
        "  2. Gap alone (no catalyst) → wait for volume confirmation first 5 min",
        "  3. Post-earnings gap → equity entry only (IV crush kills option value)",
        f"{'='*62}",
    ]
    return "\n".join(lines)
