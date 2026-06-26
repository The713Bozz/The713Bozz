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
      EMA called via Alpha Vantage on top-N candidates only (25 req/day limit).
"""

from __future__ import annotations

import json as _json
from concurrent.futures import ThreadPoolExecutor, as_completed as _as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path as _Path
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
from src.strategy.watchlist import get_tiered_scan_symbols


def _load_signals_cfg() -> dict:
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as _f:
            return _json.load(_f).get("signals", {})
    except Exception:
        return {}


def _load_regime_cfg() -> dict:
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as _f:
            return _json.load(_f).get("regime", {})
    except Exception:
        return {}


_SIG: dict = {}  # reloaded at start of run_scan / run_scan_standalone
_REG: dict = {}  # reloaded at start of run_scan / run_scan_standalone


# ── MCP bar normalizer ────────────────────────────────────────────────────────

def _normalize_mcp_bars(bars: list[dict]) -> list[dict]:
    """
    Convert Robinhood MCP get_equity_historicals bars to internal OHLCV format.
    Internal: {t, o, h, l, c, v}  (float prices, int volume)
    MCP:      {begins_at, open_price, high_price, low_price, close_price, volume}
    No-op when bars are already in internal format (detected by "c" key presence).
    """
    if not bars or "c" in bars[0]:
        return bars
    return [
        {
            "t": b.get("begins_at", ""),
            "o": float(b.get("open_price") or 0),
            "h": float(b.get("high_price") or 0),
            "l": float(b.get("low_price") or 0),
            "c": float(b.get("close_price") or 0),
            "v": int(b.get("volume") or 0),
        }
        for b in bars
    ]


# ── Volume projection helper ──────────────────────────────────────────────────

def _project_todays_volume(bars: list[dict]) -> Optional[float]:
    """
    Project today's session volume to a full-day equivalent using
    (390 / minutes_elapsed_since_930_ET).

    Handles both:
      - A single daily partial bar (if the endpoint returns one for today)
      - Multiple intraday bars (e.g. 5-min bars) — sums all today's volumes

    Assumes bars are already in internal format {t, v} — call _normalize_mcp_bars
    first. Returns None when no today's bar is found so score_from_bars() falls
    back to bars[-1]["v"] (yesterday's completed session volume).
    """
    if not bars:
        return None

    today_utc_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_bars = [b for b in bars if str(b.get("t", "")).startswith(today_utc_prefix)]
    if not today_bars:
        return None

    # Sum all today's bar volumes — correct for both a single daily partial bar
    # and a list of intraday bars (where each bar has only its interval's volume).
    raw = sum(float(b["v"]) for b in today_bars)

    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo  # type: ignore[no-redef]

    et = ZoneInfo("America/New_York")
    now_et = datetime.now(timezone.utc).astimezone(et)
    market_open_et = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    minutes_elapsed = (now_et - market_open_et).total_seconds() / 60

    if minutes_elapsed < 1:
        return raw
    if minutes_elapsed >= 390:
        return raw

    return raw * (390.0 / minutes_elapsed)


# ── Quote helpers ─────────────────────────────────────────────────────────────

def _day_change(quote: dict) -> float:
    """Return intraday day-change fraction from a Robinhood MCP quote dict."""
    try:
        price = float(
            quote.get("last_trade_price") or quote.get("ask_price") or quote.get("c") or 0
        )
        prev = float(
            quote.get("adjusted_previous_close")
            or quote.get("previous_close")
            or quote.get("pc")
            or price
        )
        if price > 0 and prev > 0:
            return (price - prev) / prev
    except (TypeError, ValueError):
        pass
    return 0.0


# ── Regime helpers ────────────────────────────────────────────────────────────

def _spy_changes_from_bars(bars: list[dict], days: int = 5) -> list[float]:
    if len(bars) < 2:
        return []
    closes = [b["c"] for b in bars[-(days + 1):]]
    return [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]


def _write_spy_cache(changes: list[float]) -> None:
    """Persist SPY daily changes to challenge.json so standalone scans can use them."""
    if not changes:
        return
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as f:
            cfg = _json.load(f)
        cfg.setdefault("spy_cache", {})["changes"] = changes
        cfg["spy_cache"]["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(p, "w") as f:
            _json.dump(cfg, f, indent=2)
    except Exception:
        pass


def _read_spy_cache(max_age_hours: float = 26.0) -> list[float]:
    """Read cached SPY changes. Returns [] if missing or stale."""
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as f:
            cfg = _json.load(f)
        cache = cfg.get("spy_cache", {})
        changes = cache.get("changes", [])
        updated_at = cache.get("updated_at")
        if not changes or not updated_at:
            return []
        age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(
            updated_at.replace("Z", "+00:00")
        )).total_seconds() / 3600
        if age_hours > max_age_hours:
            return []
        return changes
    except Exception:
        return []


# ── Analyst forecast layer ────────────────────────────────────────────────────

def _fetch_analyst_targets(symbols: list[str]) -> dict[str, dict]:
    """
    Fetch Finnhub analyst consensus price targets — only called for scored candidates,
    never for the full watchlist. Parallel fetch with up to 5 workers.
    """
    if not symbols:
        return {}
    targets: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=min(len(symbols), 5)) as pool:
        futures = {pool.submit(_finnhub.price_target, sym): sym for sym in symbols}
        for fut in _as_completed(futures):
            sym = futures[fut]
            try:
                t = fut.result()
                if t:
                    targets[sym] = t
            except Exception:
                pass
    return targets


def _apply_analyst_signal(result: SignalResult, target_dict: dict) -> None:
    """
    Apply analyst consensus target to an already-scored SignalResult.
    Modifies result in place — call BEFORE catalyst gate and filter.

    +1 signal ("analyst_+X%_target") if consensus mean ≥ threshold above current price.
    Sets forecast_warning if consensus mean ≥ threshold BELOW current price.
    Re-evaluates breakout_alert and conviction after any score change.
    """
    upside_threshold = _SIG.get("analyst_upside_threshold", 0.10)
    filter_min = _SIG.get("filter_min_score", 3)

    mean = target_dict.get("target_mean")
    if not mean or result.current_price <= 0:
        return

    upside = (mean - result.current_price) / result.current_price
    result.forecast_upside_pct = upside
    result.forecast_target = float(mean)

    if upside >= upside_threshold:
        result.score += 1
        result.signals.append(f"analyst_{upside:+.0%}_target")
        # Recompute conviction
        if result.score >= 4:
            result.conviction = "high"
        elif result.score >= filter_min:
            result.conviction = "medium"
        # Re-evaluate breakout alert with boosted score
        if result.day_change_pct >= 0.08 and result.score >= 2:
            result.breakout_alert = True
    elif upside <= -upside_threshold:
        result.forecast_warning = (
            f"Analyst target ${mean:.2f} ({upside:.0%} below current) — consensus sees downside"
        )


# ── Primary path (agent session with MCP) ─────────────────────────────────────

def run_scan(
    quotes: dict[str, dict],
    spy_bars: list[dict],
    account_value: float,
    historicals: dict[str, list[dict]] | None = None,
    today_volumes: dict[str, float] | None = None,
) -> tuple[list[SignalResult], RegimeResult]:
    """
    Primary scan using Robinhood MCP data.
    quotes:        {symbol: quote_dict} from get_equity_quotes.
    spy_bars:      daily OHLCV bars for SPY. MCP format auto-normalized.
    historicals:   optional {symbol: bars} from get_equity_historicals.
                   MCP format auto-normalized. Use start_time ≥90 calendar days
                   back so high_3m (63 bars) is computed and 21-EMA has warmup.
    today_volumes: optional {symbol: projected_full_day_volume}. When provided
                   for a symbol, overrides _project_todays_volume(). Compute by
                   summing today's 5-min bar volumes × (390 / minutes_elapsed).
    """
    global _SIG, _REG
    _SIG = _load_signals_cfg()
    _REG = _load_regime_cfg()
    spy_window = _REG.get("spy_window_days", 5)
    filter_min = _SIG.get("filter_min_score", 3)

    spy_bars = _normalize_mcp_bars(spy_bars)
    spy_changes = _spy_changes_from_bars(spy_bars, days=spy_window)
    if spy_changes:
        _write_spy_cache(spy_changes)
    regime = classify_regime(spy_changes)
    spy_today = spy_changes[-1] if spy_changes else 0.0

    rs_min = _SIG.get("rs_min_day_change", 0.03)
    stale_vol_syms: list[str] = []
    results: list[SignalResult] = []
    for symbol, quote in quotes.items():
        bars = _normalize_mcp_bars((historicals or {}).get(symbol, []))
        today_vol = (today_volumes or {}).get(symbol)
        if today_vol is None:
            today_vol = _project_todays_volume(bars) if bars else None
        if today_vol is None and bars:
            # No intraday data — volume will use yesterday's completed session.
            # This compares yesterday vs 14d-avg, not today vs 14d-avg.
            if _day_change(quote) >= rs_min:
                stale_vol_syms.append(symbol)
        result = score_from_bars(symbol, quote, bars, spy_change=spy_today, today_volume=today_vol)
        results.append(result)

    if stale_vol_syms:
        print(
            f"[SCAN] ⚠ Volume signal using yesterday's data for {len(stale_vol_syms)} RS "
            f"candidate(s) — pass today_volumes or include intraday bars for live surge "
            f"detection: {', '.join(stale_vol_syms)}"
        )

    # Warn when RS-qualifying symbols have no historicals — they score 0/1 on signals
    # 2–4 (volume, EMA, high) and are silently under-scored.
    if historicals:
        missing_hist = [
            sym for sym, q in quotes.items()
            if _day_change(q) >= rs_min and not (historicals or {}).get(sym)
        ]
        if missing_hist:
            print(
                f"[SCAN] ⚠ {len(missing_hist)} RS candidate(s) scored without historicals "
                f"(vol/EMA/high signals unavailable): {', '.join(missing_hist)}"
            )

    # Catalyst gate runs first (internally gated on score ≥ catalyst_gate_min_score)
    _run_catalyst_gate(results)

    # Analyst targets: only fetch for score ≥ 2 candidates — never for the full watchlist.
    # Cuts Finnhub calls from 168 → 0–5 on a typical scan day.
    gate_min = _SIG.get("catalyst_gate_min_score", 2)
    promising = [r for r in results if r.score >= gate_min or r.breakout_alert]
    if promising:
        analyst_targets = _fetch_analyst_targets([r.symbol for r in promising])
        for r in promising:
            _apply_analyst_signal(r, analyst_targets.get(r.symbol, {}))

    return filter_candidates(results, min_score=filter_min), regime


# ── Standalone CLI path (Finnhub only) ────────────────────────────────────────

def run_scan_standalone(account_value: float) -> tuple[list[SignalResult], RegimeResult]:
    """
    Standalone scan using Finnhub quotes + metrics.
    SPY regime from Finnhub ETF candles falls back to unknown if restricted.
    EMA called via Alpha Vantage on top-N pre-filter candidates only.
    """
    global _SIG, _REG
    _SIG = _load_signals_cfg()
    _REG = _load_regime_cfg()
    spy_window   = _REG.get("spy_window_days", 5)
    spy_lookback = _REG.get("spy_lookback_days", 20)
    av_top_n     = _SIG.get("av_ema_top_n", 3)
    filter_min   = _SIG.get("filter_min_score", 3)

    # Regime: try SPY candles; fall back to current quote if paywalled (Finnhub free tier)
    spy_bars = _finnhub.stock_candles("SPY", days_back=spy_lookback)
    spy_changes = _spy_changes_from_bars(spy_bars, days=spy_window)
    if not spy_changes:
        spy_q = _finnhub.current_quote("SPY")
        if spy_q and spy_q.get("c") and spy_q.get("pc"):
            spy_changes = [(spy_q["c"] - spy_q["pc"]) / spy_q["pc"]]
    if not spy_changes:
        spy_changes = _read_spy_cache()
        if spy_changes:
            print("[REGIME] Using cached SPY data (Finnhub restricted) — regime may be up to 26h old.")
    regime = classify_regime(spy_changes)
    spy_today = spy_changes[-1] if spy_changes else 0.0

    symbols, scan_tier = get_tiered_scan_symbols(spy_today)
    print(f"[SCAN] SPY {spy_today:+.2%} → {scan_tier} ({len(symbols)} symbols)")

    # Pass 1: Parallel quote fetch — 10 workers, ~8–15s for 168 symbols vs ~90s serial
    rs_min = _SIG.get("rs_min_day_change", 0.03)
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

    # Loose 50% RS pre-filter: only fetch metrics for symbols showing day move ≥ 1.5%
    # (half the RS threshold — keeps the gate wide enough to never miss a real candidate)
    rs_prefilter: set[str] = {
        sym for sym, fq in quotes_map.items()
        if fq.get("pc", 0) > 0 and abs((fq["c"] - fq["pc"]) / fq["pc"]) >= rs_min * 0.5
    }
    print(f"[SCAN] {len(rs_prefilter)}/{len(quotes_map)} symbols need metrics (move ≥{rs_min*0.5:.1%})")

    # Pass 2: Parallel metrics fetch — only for RS candidates (typically 0–15 symbols)
    metrics_map: dict[str, dict] = {}
    if rs_prefilter:
        with ThreadPoolExecutor(max_workers=min(len(rs_prefilter), 5)) as pool:
            futures = {pool.submit(_finnhub.stock_metrics, sym): sym for sym in rs_prefilter}
            for fut in _as_completed(futures):
                sym = futures[fut]
                try:
                    m = fut.result()
                    if m:
                        metrics_map[sym] = m
                except Exception:
                    pass

    results: list[SignalResult] = []
    for symbol in symbols:
        fq = quotes_map.get(symbol)
        if not fq:
            continue
        quote = {
            "last_trade_price": str(fq.get("c", 0)),
            "adjusted_previous_close": str(fq.get("pc", 0)),
        }
        result = score_from_metrics(symbol, quote, metrics_map.get(symbol, {}), spy_change=spy_today)
        results.append(result)

    # EMA via Alpha Vantage — only on top-N pre-filter candidates (conserves 25/day budget)
    pre_filter = sorted(results, key=lambda r: r.score, reverse=True)[:av_top_n]
    for r in pre_filter:
        aligned = _av.ema_aligned(r.symbol)
        if aligned is not None:
            if aligned and "ema_aligned" not in r.signals:
                r.score += 1
                r.signals.append("ema_aligned")
            if r.score >= 4:
                r.conviction = "high"
            elif r.score == 3:
                r.conviction = "medium"

    # Catalyst gate (gated internally on score ≥ catalyst_gate_min_score)
    _run_catalyst_gate(results)

    # Analyst targets: only for score ≥ 2 candidates — never for the full watchlist
    gate_min = _SIG.get("catalyst_gate_min_score", 2)
    promising = [r for r in results if r.score >= gate_min or r.breakout_alert]
    if promising:
        analyst_targets = _fetch_analyst_targets([r.symbol for r in promising])
        for r in promising:
            _apply_analyst_signal(r, analyst_targets.get(r.symbol, {}))

    return filter_candidates(results, min_score=filter_min), regime


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _run_catalyst_gate(results: list[SignalResult]) -> None:
    """Run full catalyst check on score ≥ threshold candidates. Modifies results in place."""
    gate_min = _SIG.get("catalyst_gate_min_score", 2)
    for r in results:
        if r.score >= gate_min:
            cat = full_catalyst_check(r.symbol)
            r.catalyst_clear = cat.clear
            r.catalyst_detail = cat.detail


# ── Scan decision logging & near-miss carry-forward ────────────────────────────
#
# Scan decisions go to logs/scans.jsonl — a SEPARATE log from logs/trades.jsonl.
# Rationale: trades.jsonl holds order/fill records that contain the account number
# and is gitignored (never committed). Scan records carry NO account number — only
# symbols, signals, and the account *balance* (already public in config/challenge.json)
# — so scans.jsonl is committable. That lets the near-miss carry-forward survive a
# fresh/ephemeral container across a weekend via git, without ever putting the account
# number into version control. The .gitignore un-ignores this one file: !logs/scans.jsonl
#
# The 4 signal "slots" of the Momentum Compounder stack. A SignalResult lists the
# specific signals that fired (e.g. "near_61d_high", "strong_breakout"); we collapse
# those to the 4 canonical slots so a scan record can say *which* slot a name is
# missing. "missing only volume" is the premium carry-forward case: a 3/4 name that
# fires the 4th signal next session is a high-conviction confirmation.

SCAN_LOG_PATH = _Path(__file__).parent.parent.parent / "logs" / "scans.jsonl"


def _append_scan_record(record: dict, log_path: "_Path") -> None:
    """Append a timestamped scan record to the committable scan log (NOT trades.jsonl)."""
    log_path.parent.mkdir(exist_ok=True)
    record["logged_at"] = datetime.now(timezone.utc).isoformat()
    with open(log_path, "a") as f:
        f.write(_json.dumps(record) + "\n")


def _slot_status(signals: list[str]) -> dict[str, bool]:
    """Map a SignalResult.signals list to the 4 canonical signal slots (filled/missing)."""
    return {
        "relative_strength": "relative_strength" in signals,
        "volume": any(s in ("volume_surge", "volume_accumulation") for s in signals),
        "ema_aligned": "ema_aligned" in signals,
        "high": any(s.startswith("near_") or s == "strong_breakout" for s in signals),
    }


def log_scan_result(
    candidates: list[SignalResult],
    regime: RegimeResult,
    account_value: float,
    log_path: "_Path | None" = None,
) -> dict:
    """
    Append a scan-decision record to logs/scans.jsonl (CLAUDE.md rule 6: log every
    signal and rejection). Records each surfaced candidate with its filled/missing
    signal slots so the decision — and the near-misses — are auditable and replayable.

    Writes NO account number — only symbols, signals, and the account balance (already
    public in config) — so the file is safe to commit and the carry-forward persists
    across containers. Returns the written record.
    """
    surfaced = []
    for r in candidates:
        slots = _slot_status(r.signals)
        surfaced.append({
            "symbol": r.symbol,
            "score": r.score,
            "conviction": r.conviction,
            "signals": list(r.signals),
            "missing": [slot for slot, present in slots.items() if not present],
            "day_change_pct": round(r.day_change_pct, 4),
            "price": round(r.current_price, 2),
            "breakout_alert": r.breakout_alert,
            "catalyst_clear": r.catalyst_clear,
        })
    record = {
        "event": "scan",
        "regime": regime.regime,
        "trade_allowed": regime.trade_allowed,
        "position_scale": regime.position_scale,
        "account_value": round(account_value, 2),
        "surfaced_count": len(surfaced),
        "surfaced": surfaced,
    }
    _append_scan_record(record, log_path or SCAN_LOG_PATH)
    return record


def recent_near_misses(
    max_age_hours: float = 80.0,
    missing_slot: str = "volume",
    min_score: int = 3,
    log_path: "_Path | None" = None,
) -> list[dict]:
    """
    Read back the most recent scan record from logs/trades.jsonl and return the names
    that scored ≥ min_score while missing ONLY the given slot. These are the premium
    carry-forward candidates: a 3/4 name missing only volume today becomes a confirmed
    4/4 setup if volume shows up next session.

    Default window is 80h so a Friday scan still carries into Monday's open across a
    normal weekend (a 3-day holiday weekend can still age out — that is acceptable, the
    next scan re-evaluates every name from scratch anyway). Returns [] when no scan
    within the window, or none qualify.
    """
    path = log_path or SCAN_LOG_PATH
    if not path.exists():
        return []

    last_scan = None
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = _json.loads(line)
                except _json.JSONDecodeError:
                    continue
                if entry.get("event") == "scan":
                    last_scan = entry  # keep the latest — file is append-ordered
    except OSError:
        return []

    if not last_scan:
        return []

    logged_at = last_scan.get("logged_at")
    if logged_at:
        try:
            ts = datetime.fromisoformat(logged_at.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
            if age_h > max_age_hours:
                return []
        except (ValueError, AttributeError):
            pass

    return [
        s for s in last_scan.get("surfaced", [])
        if s.get("score", 0) >= min_score and s.get("missing") == [missing_slot]
    ]


# ── Agent-session orchestrator (single entry point for MCP-fed scans) ──────────

def run_agent_scan(
    quotes: dict[str, dict],
    spy_bars: list[dict],
    account_value: float,
    historicals: dict[str, list[dict]] | None = None,
    today_volumes: dict[str, float] | None = None,
) -> tuple[list[SignalResult], RegimeResult]:
    """
    One call that drives the *committed, tested* scan pipeline end-to-end from
    already-fetched Robinhood MCP data: score → catalyst gate → analyst layer →
    filter (run_scan), print the report, and log the decision to trades.jsonl.
    Also surfaces near-misses carried forward from the previous scan.

    Use this from the agent session instead of re-deriving signals inline — the
    decision then comes from the same code path that is unit-tested, not throwaway
    scratch scripts. Returns (candidates, regime).
    """
    # Carry-forward must be read BEFORE we log this scan, so it reflects the prior one.
    carry = recent_near_misses()

    candidates, regime = run_scan(
        quotes, spy_bars, account_value,
        historicals=historicals, today_volumes=today_volumes,
    )

    print_scan_report(candidates, regime, account_value)

    if carry:
        names = ", ".join(
            f"{c['symbol']} ({c['day_change_pct']:+.1%}, was {c['score']}/4)" for c in carry
        )
        print(
            f"--- CARRY-FORWARD: {len(carry)} name(s) were 3/4 missing only volume last scan ---\n"
            f"    Watch for volume confirmation today → high-conviction: {names}\n"
        )

    log_scan_result(candidates, regime, account_value)
    return candidates, regime


def print_scan_report(
    candidates: list[SignalResult],
    regime: RegimeResult,
    account_value: float,
) -> None:
    from src.risk.risk_manager import position_size

    upside_threshold = _SIG.get("analyst_upside_threshold", 0.10)
    filter_min       = _SIG.get("filter_min_score", 3)
    brk_alert        = _SIG.get("breakout_alert_pct", 0.08)

    tag = "OK" if regime.trade_allowed else "HALT"
    print(f"\n[REGIME:{tag}] {regime.regime.upper()} — {regime.detail}")

    if not regime.trade_allowed:
        print("No new entries. Monitoring existing positions only.\n")
        return

    # Separate clean 3/4+ candidates from breakout alerts (2/4 but ≥8% on the day)
    clean = [r for r in candidates if r.score >= filter_min]
    alerts = [r for r in candidates if r.breakout_alert and r.score < filter_min]

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
            if r.forecast_upside_pct is not None and r.forecast_upside_pct >= upside_threshold:
                print(f"    Forecast: ${r.forecast_target:.2f} ({r.forecast_upside_pct:+.0%} analyst consensus upside)")
            if r.forecast_warning:
                print(f"    ⚠  {r.forecast_warning}")
        print()
    else:
        print("No 3/4+ candidates at this time.\n")

    if alerts:
        print(f"--- BREAKOUT ALERTS (≥{brk_alert:.0%} move, 2+ signals — review for entry) ---")
        for r in alerts:
            print(f"  !! {r.symbol:<6} {r.score}/4  {r.entry_note}  [{', '.join(r.signals)}]")
            if r.catalyst_detail:
                print(f"     Catalyst: {r.catalyst_detail}")
            if r.forecast_upside_pct is not None and r.forecast_upside_pct >= upside_threshold:
                print(f"     Forecast: ${r.forecast_target:.2f} ({r.forecast_upside_pct:+.0%} upside)")
            if r.forecast_warning:
                print(f"     ⚠  {r.forecast_warning}")
        print()
