import json as _json
from dataclasses import dataclass
from pathlib import Path as _Path
from typing import Optional


def _load_regime_cfg() -> dict:
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as _f:
            return _json.load(_f).get("regime", {})
    except Exception:
        return {}


_REG = _load_regime_cfg()


@dataclass
class RegimeResult:
    regime: str           # "bull" | "bear" | "ranging" | "volatile" | "unknown"
    trade_allowed: bool
    instrument_bias: str  # "calls" | "puts" | "flat" | "any"
    confidence: str       # "high" | "medium" | "low"
    detail: str
    position_scale: float = 1.0  # 1.0 = full size, 0.5 = half (ranging), 0.0 = no entry
    vix: Optional[float] = None


def classify_regime(
    spy_changes: list[float],
    vix: Optional[float] = None,
) -> RegimeResult:
    """
    Classify market regime from SPY daily % changes (decimals: 0.012 = +1.2%).
    spy_changes: ordered oldest → newest, minimum 1 value.
    vix: current VIX level — overrides to volatile if ≥ vix_volatile_threshold (30).

    Thresholds read from config/challenge.json ["regime"] with hardcoded fallbacks:
    - volatile : avg |move| > volatile_avg_abs_threshold (1.5%)  OR  vix ≥ 30
    - bear     : avg < bear_avg_threshold (-0.3%) + majority negative days
    - bull     : avg > bull_avg_threshold (+0.3%) + majority positive days
    - ranging  : everything else — half-size entries only
    """
    vol_thresh    = _REG.get("volatile_avg_abs_threshold", 0.015)
    bear_thresh   = _REG.get("bear_avg_threshold", -0.003)
    bull_thresh   = _REG.get("bull_avg_threshold", 0.003)
    ranging_scale = _REG.get("ranging_position_scale", 0.5)
    vix_vol_thr   = _REG.get("vix_volatile_threshold", 30.0)
    vix_elev_thr  = _REG.get("vix_elevated_threshold", 20.0)

    vix_note = f"  VIX {vix:.1f}" if vix is not None else ""

    # VIX override: extreme fear → volatile regardless of SPY direction
    if vix is not None and vix >= vix_vol_thr:
        return RegimeResult(
            "volatile", False, "flat", "high",
            f"Volatile: VIX {vix:.1f} ≥ {vix_vol_thr:.0f} — fear spike. "
            "Momentum signals unreliable — stand aside.",
            position_scale=0.0,
            vix=vix,
        )

    if not spy_changes:
        return RegimeResult(
            "unknown", True, "any", "low",
            f"No SPY data — proceeding without regime filter.{vix_note}",
            vix=vix,
        )

    n = len(spy_changes)
    avg = sum(spy_changes) / n
    avg_abs = sum(abs(c) for c in spy_changes) / n
    pos_days = sum(1 for c in spy_changes if c > 0)

    # VIX elevated: reduce confidence and tighten scale even if not fully volatile
    vix_elevated = vix is not None and vix >= vix_elev_thr

    # Volatile overrides direction — chop kills momentum entries
    if avg_abs > vol_thresh:
        return RegimeResult(
            "volatile", False, "flat", "high",
            f"Volatile: avg daily move {avg_abs:.1%} over {n}d.{vix_note} "
            "Momentum signals unreliable — stand aside.",
            position_scale=0.0,
            vix=vix,
        )

    if avg < bear_thresh and pos_days < n / 2:
        conf = "high" if n >= 3 else "medium"
        scale = ranging_scale if vix_elevated else 0.0
        return RegimeResult(
            "bear", not vix_elevated, "puts", conf,
            f"Bear: SPY avg {avg:+.2%}/day over {n}d ({pos_days}/{n} up).{vix_note} "
            "Momentum longs blocked. Watch for put setups on bounces.",
            position_scale=scale,
            vix=vix,
        )

    if avg > bull_thresh and pos_days >= n / 2:
        conf = "high" if n >= 3 else "medium"
        scale = ranging_scale if vix_elevated else 1.0
        return RegimeResult(
            "bull", True, "calls", conf,
            f"Bull: SPY avg {avg:+.2%}/day over {n}d ({pos_days}/{n} up).{vix_note} "
            "Momentum longs enabled — full scan.",
            position_scale=scale,
            vix=vix,
        )

    # Ranging: allow 3/4+ entries at half position — individual stocks can outrun SPY.
    return RegimeResult(
        "ranging", True, "flat", "medium",
        f"Ranging: SPY avg {avg:+.2%}/day, no clear trend over {n}d.{vix_note} "
        "Half-size entries for 3/4+ signals only — macro edge is low.",
        position_scale=ranging_scale,
        vix=vix,
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
