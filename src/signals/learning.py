"""
Win-rate learning from closed trades in logs/trades.jsonl.
Closed trades are entries with a "won" field (logged at exit, not entry).
Requires 5+ closed trades for signal analysis, 10+ for combo analysis.
"""

import json
from collections import defaultdict
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent.parent / "logs" / "trades.jsonl"


def _closed_trades(log_path: Path = LOG_PATH) -> list[dict]:
    if not log_path.exists():
        return []
    trades = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if "won" in entry and "signals" in entry:
                    trades.append(entry)
            except json.JSONDecodeError:
                continue
    return trades


def win_rate_by_signal(log_path: Path = LOG_PATH) -> dict:
    """Win rate per individual signal. Needs 5+ closed trades."""
    trades = _closed_trades(log_path)
    if len(trades) < 5:
        return {"_status": f"Need 5+ closed trades (have {len(trades)})."}

    counts: dict = defaultdict(lambda: {"wins": 0, "total": 0})
    for t in trades:
        for sig in t.get("signals", []):
            counts[sig]["total"] += 1
            if t["won"]:
                counts[sig]["wins"] += 1

    return {
        sig: {
            "win_rate": round(d["wins"] / d["total"], 3),
            "wins": d["wins"],
            "total": d["total"],
        }
        for sig, d in sorted(counts.items(), key=lambda x: -(x[1]["wins"] / max(x[1]["total"], 1)))
    }


def win_rate_by_combination(log_path: Path = LOG_PATH) -> dict:
    """Win rate per signal combination. Needs 10+ closed trades."""
    trades = _closed_trades(log_path)
    if len(trades) < 10:
        return {"_status": f"Need 10+ closed trades (have {len(trades)})."}

    counts: dict = defaultdict(lambda: {"wins": 0, "total": 0, "symbols": []})
    for t in trades:
        key = "+".join(sorted(t.get("signals", []))) or "none"
        counts[key]["total"] += 1
        counts[key]["symbols"].append(t.get("symbol", "?"))
        if t["won"]:
            counts[key]["wins"] += 1

    return {
        combo: {
            "win_rate": round(d["wins"] / d["total"], 3),
            "wins": d["wins"],
            "total": d["total"],
            "symbols": sorted(set(d["symbols"])),
        }
        for combo, d in sorted(counts.items(), key=lambda x: -(x[1]["wins"] / max(x[1]["total"], 1)))
    }


def best_signal_weight(signal: str, log_path: Path = LOG_PATH) -> float:
    """
    Return a weight multiplier for a signal based on historical win rate.
    Above 60% win rate → 1.2x weight. Below 40% → 0.8x. Otherwise 1.0x.
    Falls back to 1.0 if not enough data yet.
    """
    rates = win_rate_by_signal(log_path)
    if "_status" in rates or signal not in rates:
        return 1.0
    wr = rates[signal]["win_rate"]
    if wr >= 0.60:
        return 1.2
    if wr <= 0.40:
        return 0.8
    return 1.0


def learning_report(log_path: Path = LOG_PATH) -> str:
    trades = _closed_trades(log_path)
    if not trades:
        return "No closed trades yet. Learning begins after first exit is logged."

    total = len(trades)
    wins = sum(1 for t in trades if t["won"])
    wr = wins / total

    lines = [
        f"Closed trades: {total}  |  Win rate: {wr:.0%}  ({wins}W / {total - wins}L)",
        "",
    ]

    by_signal = win_rate_by_signal(log_path)
    if "_status" not in by_signal:
        lines.append("Signal win rates:")
        for sig, d in by_signal.items():
            bar = "█" * round(d["win_rate"] * 10)
            lines.append(f"  {sig:<25}  {d['win_rate']:.0%}  {bar}  ({d['wins']}/{d['total']})")
        lines.append("")

    by_combo = win_rate_by_combination(log_path)
    if "_status" not in by_combo:
        lines.append("Top signal combinations:")
        for combo, d in list(by_combo.items())[:5]:
            lines.append(f"  {d['win_rate']:.0%}  {combo}  ({d['wins']}/{d['total']})")
    else:
        lines.append(by_combo["_status"])

    return "\n".join(lines)
