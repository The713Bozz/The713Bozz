"""
Fibonacci retracement / "golden zone" toolkit.

Honest framing: fib ratios carry no proven statistical magic — this module is
used as a *disciplined pullback-entry framework*, not prophecy. Its value here:
  - forbids chasing extension (our one recorded loss, AMAT 2026-06-30, was a
    chase at the top of a leg — see LESSONS.md);
  - defines the entry zone (default 50%-61.8% retrace of the last impulse leg),
    a hard invalidation (78.6%), and therefore a tight stop with mechanically
    strong R:R back to the swing high.

Entry in the zone is NEVER sufficient alone — the standing gates still apply:
volume must confirm the reversal at the zone, regime must allow entry, catalyst
verified, review + user confirmation before any order (CLAUDE.md rules).

Pure math. No MCP calls, no file I/O (same contract as trade_decision.py).
"""

from dataclasses import dataclass, field
from typing import Optional

RETRACE_LEVELS = (0.236, 0.382, 0.500, 0.618, 0.650, 0.786)
EXTENSION_LEVELS = (1.272, 1.618)

# Default zone: 50%–61.8% retracement ("golden zone"). The tighter 61.8%–65%
# band some traders use is the "golden pocket" — reachable via zone=(0.618, 0.65).
DEFAULT_ZONE = (0.500, 0.618)
DEFAULT_INVALIDATION = 0.786


@dataclass
class FibAnalysis:
    symbol: str
    swing_low: float
    swing_high: float
    price: float
    retrace_frac: Optional[float]      # None when inputs invalid
    levels: dict = field(default_factory=dict)   # frac -> price
    status: str = ""                   # above_highs | approaching | in_zone | past_zone | invalidated | invalid_inputs
    in_golden_zone: bool = False
    zone: tuple = DEFAULT_ZONE
    zone_prices: tuple = (0.0, 0.0)    # (upper price = shallow bound, lower price = deep bound)
    stop: float = 0.0                  # just below invalidation level
    target: float = 0.0                # conservative: back to swing high
    rr_ratio: float = 0.0              # (target - price) / (price - stop), when in zone
    note: str = ""


def fib_levels(swing_low: float, swing_high: float) -> dict:
    """Retracement prices for an up-leg swing_low -> swing_high.
    Key = retrace fraction, value = price after retracing that fraction."""
    leg = swing_high - swing_low
    return {f: round(swing_high - leg * f, 4) for f in RETRACE_LEVELS}


def detect_swing(bars: list[dict], lookback: int = 63) -> Optional[tuple[float, float]]:
    """Most recent up-leg from OHLC bars (keys 'h'/'l', oldest -> newest):
    swing_high = highest high in the lookback window; swing_low = lowest low
    *before or at* that high. Returns (swing_low, swing_high) or None."""
    if not bars:
        return None
    window = bars[-lookback:]
    hi_idx = max(range(len(window)), key=lambda i: window[i]["h"])
    swing_high = window[hi_idx]["h"]
    swing_low = min(b["l"] for b in window[: hi_idx + 1])
    if swing_high <= swing_low:
        return None
    return (swing_low, swing_high)


def analyze(
    symbol: str,
    swing_low: float,
    swing_high: float,
    price: float,
    zone: tuple = DEFAULT_ZONE,
    invalidation: float = DEFAULT_INVALIDATION,
    stop_buffer: float = 0.005,
) -> FibAnalysis:
    """Classify where price sits in the retracement of the up-leg and derive
    the battle-plan numbers (stop under the invalidation level, target at the
    swing high, R:R from the current price)."""
    if swing_high <= swing_low or price <= 0:
        return FibAnalysis(
            symbol=symbol, swing_low=swing_low, swing_high=swing_high, price=price,
            retrace_frac=None, status="invalid_inputs",
            note="swing_high must exceed swing_low and price must be positive.",
        )

    leg = swing_high - swing_low
    frac = (swing_high - price) / leg
    levels = fib_levels(swing_low, swing_high)
    zone_shallow, zone_deep = min(zone), max(zone)
    zone_prices = (
        round(swing_high - leg * zone_shallow, 4),  # shallow bound (higher price)
        round(swing_high - leg * zone_deep, 4),     # deep bound (lower price)
    )
    invalidation_price = swing_high - leg * invalidation
    stop = round(invalidation_price * (1 - stop_buffer), 4)
    target = round(swing_high, 4)

    if frac <= 0:
        status, note = "above_highs", "At/above swing high — no retrace. Chasing here is the AMAT mistake; wait for the pullback."
    elif frac < zone_shallow:
        status, note = "approaching", f"Retraced {frac:.1%} — shallow of the zone. Patience; zone is {zone_shallow:.1%}-{zone_deep:.1%}."
    elif frac <= zone_deep:
        status, note = "in_zone", "In the golden zone. Entry still requires: volume confirming the reversal, regime scale > 0, verified catalyst, review + confirmation."
    elif frac <= invalidation:
        status, note = "past_zone", f"Retraced {frac:.1%} — deeper than the zone but above invalidation ({invalidation:.1%}). Weakening; only the golden-pocket school buys here."
    else:
        status, note = "invalidated", f"Retraced {frac:.1%} > {invalidation:.1%} — the up-leg is invalidated. No long setup; the 'discount' is a broken trend."

    in_zone = status == "in_zone"
    rr = round((target - price) / (price - stop), 2) if in_zone and price > stop else 0.0

    return FibAnalysis(
        symbol=symbol, swing_low=swing_low, swing_high=swing_high, price=price,
        retrace_frac=round(frac, 4), levels=levels, status=status,
        in_golden_zone=in_zone, zone=(zone_shallow, zone_deep), zone_prices=zone_prices,
        stop=stop, target=target, rr_ratio=rr,
        note=note,
    )


def format_fib(a: FibAnalysis) -> str:
    if a.retrace_frac is None:
        return f"[FIB:{a.symbol}] INVALID — {a.note}"
    lines = [
        f"# Fibonacci Golden Zone — {a.symbol}",
        f"Leg: {a.swing_low:,.2f} -> {a.swing_high:,.2f}  |  price {a.price:,.2f}  |  retraced {a.retrace_frac:.1%}",
        f"Status: {a.status.upper()}{'  ✅ IN GOLDEN ZONE' if a.in_golden_zone else ''}",
        "",
        "Levels:",
    ]
    for f, px in a.levels.items():
        marker = "  <-- zone" if a.zone[0] <= f <= a.zone[1] else ("  <-- invalidation" if f == DEFAULT_INVALIDATION else "")
        lines.append(f"  {f:.3f}  ${px:,.2f}{marker}")
    lines += [
        "",
        f"Zone prices : ${a.zone_prices[0]:,.2f} (shallow) -> ${a.zone_prices[1]:,.2f} (deep)",
        f"Stop        : ${a.stop:,.2f}  (below {DEFAULT_INVALIDATION:.1%} invalidation)",
        f"Target      : ${a.target:,.2f}  (swing high, conservative)",
    ]
    if a.in_golden_zone:
        lines.append(f"R:R at price: {a.rr_ratio}:1")
    lines += ["", f"Note: {a.note}"]
    return "\n".join(lines)
