"""
Signal backtester — measures real historical accuracy of the 4-signal scoring system.

Usage (agent session — feed pre-fetched MCP historicals):
    from src.backtest.backtest_signals import run_backtest, print_backtest_report
    results = run_backtest(historicals_dict, spy_bars)
    print_backtest_report(results)

historicals_dict : {symbol: [bars]} — each bar {"t","o","h","l","c","v"}
                   from mcp__robinhood-trading__get_equity_historicals
spy_bars         : SPY daily bars for regime classification

Results are automatically saved to config/challenge.json ["backtest"] so
they persist across sessions and inform confidence-level reporting.
"""

from __future__ import annotations

import json as _json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path as _Path
from typing import Optional

from src.signals.technical import compute_ema, score_quote
from src.signals.regime import classify_regime


def _load_cfg() -> dict:
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as f:
            return _json.load(f)
    except Exception:
        return {}


def _save_backtest_stats(stats: dict) -> None:
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as f:
            cfg = _json.load(f)
        cfg["backtest"].update(stats)
        cfg["backtest"]["last_run_at"] = datetime.now(timezone.utc).isoformat()
        with open(p, "w") as f:
            _json.dump(cfg, f, indent=2)
    except Exception:
        pass


@dataclass
class SignalHit:
    symbol: str
    date: str
    score: int
    signals: list[str]
    price_at_signal: float
    forward_3d: Optional[float] = None   # % return 3 days later
    forward_5d: Optional[float] = None   # % return 5 days later
    forward_10d: Optional[float] = None  # % return 10 days later
    hit_2x_target: bool = False          # reached +150% (option target)
    hit_stop: bool = False               # hit -50% (option stop) before target
    regime: str = "unknown"


@dataclass
class BacktestResults:
    total_signals: int = 0
    win_3d: int = 0
    win_5d: int = 0
    win_10d: int = 0
    avg_return_5d: float = 0.0
    median_return_5d: float = 0.0
    avg_return_3d: float = 0.0
    option_target_hit_rate: float = 0.0  # how often +150% was achievable within 5d
    option_stop_hit_rate: float = 0.0    # how often -50% was hit first
    score_3_win_rate_5d: float = 0.0
    score_4_win_rate_5d: float = 0.0
    by_signal: dict = field(default_factory=dict)
    hits: list[SignalHit] = field(default_factory=list)
    symbols_scanned: int = 0
    bars_processed: int = 0
    date_range: str = ""


def run_backtest(
    historicals: dict[str, list[dict]],
    spy_bars: list[dict],
    min_score: int = 3,
    forward_days: list[int] | None = None,
) -> BacktestResults:
    """
    Simulate the 4-signal system on historical bars and measure forward returns.

    historicals : {symbol: [daily_bars]} oldest→newest, each {"t","o","h","l","c","v"}
    spy_bars    : SPY daily bars (same format) for regime and RS calculation
    min_score   : only track signal hits at or above this score (default 3)
    forward_days: list of forward return windows to compute (default [3, 5, 10])
    """
    cfg = _load_cfg()
    sig_cfg = cfg.get("signals", {})
    bt_cfg  = cfg.get("backtest", {})

    if forward_days is None:
        forward_days = bt_cfg.get("forward_return_days", [3, 5, 10])

    vol_window   = sig_cfg.get("volume_avg_window_days", 14)
    ema_short    = sig_cfg.get("ema_short_period", 9)
    ema_long     = sig_cfg.get("ema_long_period", 21)
    high_window  = sig_cfg.get("high_3m_bars", 63)

    # Build SPY close series for RS calculation
    spy_closes = [b["c"] for b in spy_bars]
    spy_changes_map: dict[str, float] = {}
    for i in range(1, len(spy_bars)):
        day_key = str(spy_bars[i].get("t", ""))[:10]
        spy_changes_map[day_key] = (spy_closes[i] - spy_closes[i - 1]) / spy_closes[i - 1]

    results = BacktestResults()
    results.symbols_scanned = len(historicals)

    all_5d_returns: list[float] = []
    all_3d_returns: list[float] = []
    score3_wins: list[bool] = []
    score4_wins: list[bool] = []
    option_targets: list[bool] = []
    option_stops: list[bool] = []

    for symbol, bars in historicals.items():
        if len(bars) < vol_window + max(forward_days) + 5:
            continue

        results.bars_processed += len(bars)

        # Determine date range
        if bars:
            start = str(bars[0].get("t", ""))[:10]
            end = str(bars[-1].get("t", ""))[:10]
            if not results.date_range:
                results.date_range = f"{start} → {end}"

        for i in range(vol_window + ema_long, len(bars) - max(forward_days)):
            bar = bars[i]
            prev_bar = bars[i - 1]

            day_key = str(bar.get("t", ""))[:10]
            spy_change = spy_changes_map.get(day_key, 0.0)

            # Build quote dict from bar
            quote = {
                "last_trade_price": str(bar["c"]),
                "adjusted_previous_close": str(prev_bar["c"]),
            }

            # Compute enrichment signals from history up to and including bar[i-1]
            history = bars[:i]
            closes = [b["c"] for b in history]
            volumes = [b["v"] for b in history]

            avg_volume = sum(volumes[-vol_window:]) / vol_window if len(volumes) >= vol_window else None
            high_window_bars = history[-high_window:] if len(history) >= high_window else history
            high_52w = max(b["h"] for b in history)
            high_3m = max(b["h"] for b in high_window_bars)

            ema9 = compute_ema(closes, ema_short)
            ema21 = compute_ema(closes, ema_long)
            ema_aligned = (ema9 > ema21) if (ema9 and ema21) else None

            high_label = f"near_{len(history)}d_high" if len(history) < 252 else "near_52w_high"

            result = score_quote(
                symbol=symbol,
                quote=quote,
                spy_change=spy_change,
                volume=float(bar["v"]),
                avg_volume=avg_volume,
                high_52w=high_52w,
                ema_aligned=ema_aligned,
                high_3m=high_3m,
                high_label=high_label,
            )

            if result.score < min_score:
                continue

            # Compute forward returns
            entry_price = bar["c"]
            fwd: dict[int, float] = {}
            for fwd_days in forward_days:
                if i + fwd_days < len(bars):
                    exit_price = bars[i + fwd_days]["c"]
                    fwd[fwd_days] = (exit_price - entry_price) / entry_price

            # Check if option target (+150%) or stop (-50%) was hit first within 5 days
            option_target_hit = False
            option_stop_hit = False
            for j in range(i + 1, min(i + 6, len(bars))):
                high = bars[j]["h"]
                low = bars[j]["l"]
                gain_pct = (high - entry_price) / entry_price
                loss_pct = (low - entry_price) / entry_price
                # +20% underlying ≈ +150% option gain at delta-0.30
                # -5% underlying ≈ -50% option loss at delta-0.30
                if gain_pct >= 0.20:
                    option_target_hit = True
                    break
                if loss_pct <= -0.05:
                    option_stop_hit = True
                    break

            hit = SignalHit(
                symbol=symbol,
                date=day_key,
                score=result.score,
                signals=result.signals,
                price_at_signal=entry_price,
                forward_3d=fwd.get(3),
                forward_5d=fwd.get(5),
                forward_10d=fwd.get(10),
                hit_2x_target=option_target_hit,
                hit_stop=option_stop_hit,
            )

            results.hits.append(hit)
            results.total_signals += 1

            if fwd.get(5) is not None:
                all_5d_returns.append(fwd[5])
                win = fwd[5] > 0
                if result.score == 3:
                    score3_wins.append(win)
                elif result.score >= 4:
                    score4_wins.append(win)

            if fwd.get(3) is not None:
                all_3d_returns.append(fwd[3])

            option_targets.append(option_target_hit)
            option_stops.append(option_stop_hit)

    # Aggregate stats
    if all_5d_returns:
        results.avg_return_5d = sum(all_5d_returns) / len(all_5d_returns)
        sorted_r = sorted(all_5d_returns)
        mid = len(sorted_r) // 2
        results.median_return_5d = sorted_r[mid]
        results.win_5d = sum(1 for r in all_5d_returns if r > 0)

    if all_3d_returns:
        results.avg_return_3d = sum(all_3d_returns) / len(all_3d_returns)
        results.win_3d = sum(1 for r in all_3d_returns if r > 0)

    if score3_wins:
        results.score_3_win_rate_5d = sum(score3_wins) / len(score3_wins)
    if score4_wins:
        results.score_4_win_rate_5d = sum(score4_wins) / len(score4_wins)
    if option_targets:
        results.option_target_hit_rate = sum(option_targets) / len(option_targets)
    if option_stops:
        results.option_stop_hit_rate = sum(option_stops) / len(option_stops)

    # Persist to challenge.json
    _save_backtest_stats({
        "last_win_rate": round(results.win_5d / len(all_5d_returns), 4) if all_5d_returns else None,
        "last_avg_return_5d": round(results.avg_return_5d, 4) if all_5d_returns else None,
        "sample_size": results.total_signals,
    })

    return results


def print_backtest_report(r: BacktestResults) -> None:
    n = len([h for h in r.hits if h.forward_5d is not None])
    print(f"\n{'='*56}")
    print(f"  Signal Backtest Report")
    print(f"{'='*56}")
    print(f"  Symbols scanned   : {r.symbols_scanned}")
    print(f"  Bars processed    : {r.bars_processed:,}")
    print(f"  Date range        : {r.date_range}")
    print(f"  Total 3/4+ signals: {r.total_signals}")
    print(f"  5-day forward n   : {n}")
    print(f"{'─'*56}")
    if n > 0:
        win_rate_5d = r.win_5d / n
        print(f"  Win rate (5d)     : {win_rate_5d:.1%}  ({r.win_5d}/{n})")
        print(f"  Avg return (5d)   : {r.avg_return_5d:+.2%}")
        print(f"  Median return (5d): {r.median_return_5d:+.2%}")
        print(f"  Avg return (3d)   : {r.avg_return_3d:+.2%}")
        print(f"{'─'*56}")
        print(f"  Score 3/4 win rate: {r.score_3_win_rate_5d:.1%}")
        print(f"  Score 4/4 win rate: {r.score_4_win_rate_5d:.1%}")
        print(f"{'─'*56}")
        print(f"  Options (+150% in 5d hit): {r.option_target_hit_rate:.1%}")
        print(f"  Options (-50% stop hit)  : {r.option_stop_hit_rate:.1%}")
        ev = (r.option_target_hit_rate * 1.50) - (r.option_stop_hit_rate * 0.50)
        print(f"  Option EV per signal     : {ev:+.2f}x position")
    else:
        print("  Insufficient data for 5-day forward returns.")
    print(f"{'='*56}\n")
