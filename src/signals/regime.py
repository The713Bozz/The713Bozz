from dataclasses import dataclass
from typing import Optional


@dataclass
class RegimeResult:
    regime: str           # "bull" | "bear" | "ranging" | "volatile" | "unknown"
    trade_allowed: bool
    instrument_bias: str  # "calls" | "puts" | "flat" | "any"
    confidence: str       # "high" | "medium" | "low"
    detail: str
    position_scale: float = 1.0  # 1.0 = full size, 0.5 = half (ranging), 0.0 = no entry


def classify_regime(spy_changes: list[float]) -> RegimeResult:
    """
    Classify market regime from SPY daily % changes (decimals: 0.012 = +1.2%).
    spy_changes: ordered oldest → newest, minimum 1 value.

    Thresholds (tested against SPY's typical daily volatility range):
    - volatile : avg |move| > 1.5% — momentum signals break down in whipsaw
    - bear     : avg < -0.3% + majority negative days — block longs
    - bull     : avg > +0.3% + majority positive days — full green
    - ranging  : everything else — edge too low, stand aside
    """
    if not spy_changes:
        return RegimeResult(
            "unknown", True, "any", "low",
            "No SPY data — proceeding without regime filter.",
        )

    n = len(spy_changes)
    avg = sum(spy_changes) / n
    avg_abs = sum(abs(c) for c in spy_changes) / n
    pos_days = sum(1 for c in spy_changes if c > 0)

    # Volatile overrides direction — chop kills momentum entries
    if avg_abs > 0.015:
        return RegimeResult(
            "volatile", False, "flat", "high",
            f"Volatile: avg daily move {avg_abs:.1%} over {n}d. "
            "Momentum signals unreliable — stand aside.",
            position_scale=0.0,
        )

    if avg < -0.003 and pos_days < n / 2:
        conf = "high" if n >= 3 else "medium"
        return RegimeResult(
            "bear", False, "puts", conf,
            f"Bear: SPY avg {avg:+.2%}/day over {n}d ({pos_days}/{n} up). "
            "Momentum longs blocked. Watch for put setups on bounces.",
            position_scale=0.0,
        )

    if avg > 0.003 and pos_days >= n / 2:
        conf = "high" if n >= 3 else "medium"
        return RegimeResult(
            "bull", True, "calls", conf,
            f"Bull: SPY avg {avg:+.2%}/day over {n}d ({pos_days}/{n} up). "
            "Momentum longs enabled — full scan.",
            position_scale=1.0,
        )

    # Ranging: allow 3/4+ entries at half position — individual stocks can outrun SPY.
    # Bear and volatile remain hard halts.
    return RegimeResult(
        "ranging", True, "flat", "medium",
        f"Ranging: SPY avg {avg:+.2%}/day, no clear trend over {n}d. "
        "Half-size entries for 3/4+ signals only — macro edge is low.",
        position_scale=0.5,
    )


def regime_from_quote(today_change: float, prev_changes: Optional[list[float]] = None) -> RegimeResult:
    """
    Wrapper for single-quote path (agent has today's SPY change only).
    Confidence is lower with 1 data point — treated as medium max.
    """
    changes = (prev_changes or []) + [today_change]
    result = classify_regime(changes)
    if len(changes) == 1 and result.confidence == "high":
        result.confidence = "medium"
    return result
