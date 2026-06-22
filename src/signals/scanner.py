"""
Full scan pipeline: fetch → enrich → score → catalyst gate → filter → rank.

Two entry points:

  run_scan(quotes, account_value)
      Primary path. Call from Claude Code agent session where Robinhood MCP
      quotes are already fetched. Uses MCP get_equity_historicals for volume.
      Full 4-signal scoring (RS + volume_surge + ema_aligned + 52w_high).

  run_scan_standalone(account_value)
      Standalone CLI path (--scan flag). Fetches from Finnhub — no MCP needed.
      3-signal scoring (RS + volume_accumulation + ema_aligned + 52w_high).
      EMA called via Alpha Vantage on top-3 candidates only (25 req/day limit).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from src.data import finnhub as _finnhub
from src.data import alphavantage as _av
from src.signals.catalyst import full_catalyst_check
from src.signals.regime import RegimeResult, classify_regime
from src.signals.technical import (
    SignalResult,
    filter_candidates,
    score_from_bars,
    score_from_metrics,
)
from src.strategy.watchlist import get_scan_list


# ── Volume projection helper ──────────────────────────────────────────────────

def _project_todays_volume(bars: list[dict]) -> Optional[float]:
    """
    If bars[-1] is today's partial bar, scale its raw volume to a projected
    full-session equivalent using (390 / minutes_elapsed_since_930_ET).

    Returns None when the last bar is from a prior day (stale cache), so
    score_from_bars() falls back to bars[-1]["v"] as-is (completed prior day).
    Never call this after market close — returns raw volume unchanged if >= 390
    minutes have elapsed.
    """
    if not bars:
        return None

    last_t = bars[-1].get("t", "")
    if not last_t:
        return None

    # Robinhood daily bars use UTC midnight begins_at (e.g. "2026-06-23T00:00:00Z")
    today_utc_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not str(last_t).startswith(today_utc_prefix):
        return None  # Stale bar — caller will use bars[-1]["v"] as prior-day volume

    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo  # type: ignore[no-redef]

    et = ZoneInfo("America/New_York")
    now_et = datetime.now(timezone.utc).astimezone(et)
    market_open_et = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    minutes_elapsed = (now_et - market_open_et).total_seconds() / 60

    raw = float(bars[-1]["v"])
    if minutes_elapsed < 1:
        return raw  # Pre-market or opening tick — no meaningful projection yet
    if minutes_elapsed >= 390:
        return raw  # Full session complete — no scaling needed

    return raw * (390.0 / minutes_elapsed)


# ── Regime helpers ────────────────────────────────────────────────────────────

def _spy_changes_from_bars(bars: list[dict], days: int = 5) -> list[float]:
    if len(bars) < 2:
        return []
    closes = [b["c"] for b in bars[-(days + 1):]]
    return [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]


# ── Primary path (agent session with MCP) ─────────────────────────────────────

def run_scan(
    quotes: dict[str, dict],
    spy_bars: list[dict],
    account_value: float,
    historicals: dict[str, list[dict]] | None = None,
) -> tuple[list[SignalResult], RegimeResult]:
    """
    Primary scan using Robinhood MCP data.
    quotes:      {symbol: quote_dict} from get_equity_quotes
    spy_bars:    daily OHLCV bars for SPY from get_equity_historicals
    historicals: optional {symbol: bars} from get_equity_historicals per symbol
                 (provides volume + 52w high + EMA — best signal quality)
    """
    spy_changes = _spy_changes_from_bars(spy_bars)
    regime = classify_regime(spy_changes)
    spy_today = spy_changes[-1] if spy_changes else 0.0

    results: list[SignalResult] = []
    for symbol, quote in quotes.items():
        bars = (historicals or {}).get(symbol, [])
        today_vol = _project_todays_volume(bars) if bars else None
        result = score_from_bars(symbol, quote, bars, spy_change=spy_today, today_volume=today_vol)
        results.append(result)

    _run_catalyst_gate(results)
    return filter_candidates(results, min_score=3), regime


# ── Standalone CLI path (Finnhub only) ────────────────────────────────────────

def run_scan_standalone(account_value: float) -> tuple[list[SignalResult], RegimeResult]:
    """
    Standalone scan using Finnhub quotes + metrics.
    SPY regime from Finnhub ETF candles falls back to unknown if restricted.
    EMA called via Alpha Vantage on top-3 pre-filter candidates only.
    """
    # Regime: try SPY candles; fall back gracefully if paywalled
    spy_bars = _finnhub.stock_candles("SPY", days_back=20)
    spy_changes = _spy_changes_from_bars(spy_bars, days=5)
    regime = classify_regime(spy_changes)
    spy_today = spy_changes[-1] if spy_changes else 0.0

    symbols = get_scan_list(account_value)
    results: list[SignalResult] = []

    for symbol in symbols:
        fq = _finnhub.current_quote(symbol)
        if not fq:
            continue
        # Normalise Finnhub quote to shape score_quote() expects
        quote = {
            "last_trade_price": str(fq.get("c", 0)),
            "adjusted_previous_close": str(fq.get("pc", 0)),
        }
        metrics = _finnhub.stock_metrics(symbol)
        result = score_from_metrics(symbol, quote, metrics, spy_change=spy_today)
        results.append(result)

    # EMA via Alpha Vantage — only on top-3 pre-filter candidates (conserves 25/day budget)
    pre_filter = sorted(results, key=lambda r: r.score, reverse=True)[:3]
    for r in pre_filter:
        aligned = _av.ema_aligned(r.symbol)
        if aligned is not None:
            was_score = r.score
            if aligned and "ema_aligned" not in r.signals:
                r.score += 1
                r.signals.append("ema_aligned")
            # Recompute conviction after score change
            if r.score >= 4:
                r.conviction = "high"
            elif r.score == 3:
                r.conviction = "medium"

    _run_catalyst_gate(results)
    return filter_candidates(results, min_score=3), regime


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _run_catalyst_gate(results: list[SignalResult]) -> None:
    """Run full catalyst check on score ≥ 2 candidates. Modifies results in place."""
    for r in results:
        if r.score >= 2:
            cat = full_catalyst_check(r.symbol)
            r.catalyst_clear = cat.clear
            r.catalyst_detail = cat.detail


def print_scan_report(
    candidates: list[SignalResult],
    regime: RegimeResult,
    account_value: float,
) -> None:
    from src.risk.risk_manager import position_size

    tag = "OK" if regime.trade_allowed else "HALT"
    print(f"\n[REGIME:{tag}] {regime.regime.upper()} — {regime.detail}")

    if not regime.trade_allowed:
        print("No new entries. Monitoring existing positions only.\n")
        return

    # Separate clean 3/4+ candidates from breakout alerts (2/4 but ≥8% on the day)
    clean = [r for r in candidates if r.score >= 3]
    alerts = [r for r in candidates if r.breakout_alert and r.score < 3]

    max_pos = position_size(account_value) * regime.position_scale
    scale_note = "  ⚠ RANGING: half-size entries" if regime.position_scale < 1.0 else ""
    print(f"Max position: ${max_pos:.2f}{scale_note}\n")

    if clean:
        print(f"{'#':<3} {'Symbol':<7} {'Score':<7} {'Conv':<9} {'Signals'}")
        print("-" * 75)
        for i, r in enumerate(clean, 1):
            print(f"{i:<3} {r.symbol:<7} {r.score}/4{'':<3} {r.conviction:<9} {', '.join(r.signals)}")
            print(f"    {r.entry_note}  |  Stop -{r.stop_pct:.0%}  Target +{r.target_pct:.0%}  R:R {r.rr_ratio:.1f}x  [{r.instrument} {r.option_type or ''}]")
            if r.catalyst_detail:
                print(f"    Catalyst: {r.catalyst_detail}")
        print()
    else:
        print("No 3/4+ candidates at this time.\n")

    if alerts:
        print("--- BREAKOUT ALERTS (≥8% move, 2+ signals — review for entry) ---")
        for r in alerts:
            print(f"  !! {r.symbol:<6} {r.score}/4  {r.entry_note}  [{', '.join(r.signals)}]")
            if r.catalyst_detail:
                print(f"     Catalyst: {r.catalyst_detail}")
        print()
