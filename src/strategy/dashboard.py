"""
Decision Dashboard — the daily_stock_analysis four-part report, built from this
system's own primitives (SignalResult + RegimeResult + ResearchNote + matched
strategies) and gated by the same risk rules the rest of the system obeys.

Sections (daily_stock_analysis contract):
  ① core_conclusion   signal, conviction, one-line call + caveat
  ② data_perspective  the measured 4-signal scorecard
  ③ intelligence      verified research (DeerFlow layer)
  ④ battle_plan       entry / stop / target / size + matched playbooks

Pure: no MCP, no file I/O (same contract as trade_decision.py). The agent feeds
it live-measured inputs; this module decides and renders. It NEVER places an
order — terminal output is a plan that still requires review + user confirmation
(CLAUDE.md rule #1).
"""

from dataclasses import dataclass, field
from typing import Optional

from src.signals.technical import SignalResult
from src.signals.regime import RegimeResult
from src.signals.research import ResearchNote, format_research
from src.strategy.strategy_library import StrategyMatch, match_strategies


@dataclass
class Dashboard:
    symbol: str
    action: str            # "BUY" | "WATCH" | "PASS"
    conviction: str
    core_conclusion: str
    entry: float
    stop: float
    target: float
    rr_ratio: float
    position_dollars: float
    matched_strategies: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
    research: Optional[ResearchNote] = None
    signal: Optional[SignalResult] = None
    regime: Optional[RegimeResult] = None


# canonical 4-signal scorecard rows -> the token(s) that satisfy each
_SCORECARD = [
    ("Relative strength", ("relative_strength",)),
    ("Volume (measured)", ("volume_surge", "volume_accumulation")),
    ("Trend / EMA",       ("ema_aligned",)),
    ("Breakout / high",   ("near_", "strong_breakout")),
]


def _has(sig_names: list[str], tokens) -> bool:
    for t in tokens:
        if t.endswith("_"):  # prefix match (near_52w_high / near_{N}d_high / near_3m_high)
            if any(s.startswith(t) for s in sig_names):
                return True
        elif t in sig_names:
            return True
    return False


def build_dashboard(
    signal: SignalResult,
    regime: RegimeResult,
    account_value: float,
    research: Optional[ResearchNote] = None,
    max_risk_pct: float = 0.20,
) -> Dashboard:
    """Assemble a Dashboard. Decision logic mirrors the live pipeline:

      action = BUY   when score>=3, regime allows entry (scale>0), and research
                     (if present) is not contradicted by a hard block.
             = WATCH when the setup is close but regime scale==0 or research is
                     unverified — a real setup we are standing aside on.
             = PASS  when score<3 and not a breakout alert.
    """
    price = signal.current_price or 0.0
    has_breadth = bool(research and research.require_verified()
                       and "sector" in (research.sector_context or "").lower())

    sm: StrategyMatch = match_strategies(
        signal_names=signal.signals,
        score=signal.score,
        regime=regime.regime,
        has_sector_breadth=has_breadth,
    )

    # Position sizing — 20% cap, scaled by regime (0.5 ranging, 0.0 stand-aside).
    max_spend = round(account_value * max_risk_pct, 2)
    position_dollars = round(max_spend * regime.position_scale, 2)

    entry = round(price, 2)
    stop = round(price * (1 - signal.stop_pct), 2)
    target = round(price * (1 + signal.target_pct), 2)

    caveats: list[str] = []

    # --- decide action ---
    if signal.score >= 3 and regime.position_scale > 0:
        action = "BUY"
    elif (signal.score >= 3 or signal.breakout_alert) and regime.position_scale == 0:
        action = "WATCH"
        caveats.append(
            f"Regime '{regime.regime}' blocks new entries (scale 0) — strong setup, stand aside."
        )
    elif signal.score >= 3:
        action = "BUY"
    else:
        action = "PASS"

    # --- research gating ---
    if research is not None:
        if research.catalyst and not research.verified:
            caveats.append("Catalyst is UNVERIFIED — do not size up on it.")
            if action == "BUY":
                action = "WATCH"
        for c in research.contradictions:
            caveats.append(f"Research contradiction: {c}")

    # --- volume GATE (lesson AMAT taught on 2026-06-30) ---
    # A new high on light/unconfirmed volume fades (AMAT: bought +5.5% on ~0.5x
    # RVOL, faded to close below entry). Volume is core to the momentum strategy
    # — "must be measured, not estimated." So treat absent/unconfirmed volume
    # like an unverified catalyst: it cannot carry a full BUY. Downgrade to WATCH
    # until volume confirms (≥ volume_surge_multiplier × avg).
    if not _has(signal.signals, ("volume_surge", "volume_accumulation")):
        caveats.append("Volume unconfirmed — a new high on light volume fades. "
                       "BUY gated to WATCH until volume confirms (≥1.5x avg).")
        if action == "BUY":
            action = "WATCH"

    # --- extension / chase guard ---
    if signal.day_change_pct >= 0.06:
        caveats.append(
            f"Extended +{signal.day_change_pct:.1%} on the day — prefer a pullback entry to "
            "the rising EMA over chasing the print (swing hold softens this)."
        )

    if regime.position_scale == 0 and action == "BUY":
        action = "WATCH"

    conv = signal.conviction
    scale_note = (
        f"half-size (×{regime.position_scale:g})" if 0 < regime.position_scale < 1
        else ("stand-aside (×0)" if regime.position_scale == 0 else "full-size")
    )
    strat_note = (", ".join(sm.names) if sm.names else sm.reason)
    core = (
        f"{action} — {conv} conviction, {signal.score}/4. "
        f"Regime {regime.regime} → {scale_note}. Playbook: {strat_note}."
    )

    return Dashboard(
        symbol=signal.symbol,
        action=action,
        conviction=conv,
        core_conclusion=core,
        entry=entry,
        stop=stop,
        target=target,
        rr_ratio=signal.rr_ratio,
        position_dollars=position_dollars,
        matched_strategies=sm.names,
        caveats=caveats,
        research=research,
        signal=signal,
        regime=regime,
    )


def format_dashboard(d: Dashboard) -> str:
    sig = d.signal
    sig_names = sig.signals if sig else []
    shares = (d.position_dollars / d.entry) if d.entry else 0.0

    rows = []
    for label, tokens in _SCORECARD:
        mark = "✅" if _has(sig_names, tokens) else "—"
        rows.append(f"| {label} | {mark} |")

    out = [
        f"# 📊 Decision Dashboard — {d.symbol}",
        "",
        "**① CORE CONCLUSION**",
        f"> **{d.core_conclusion}**",
        "",
        "**② DATA PERSPECTIVE**",
        f"- Day change: **{sig.day_change_pct:+.1%}**" if sig else "",
        "| Signal | ✓ |",
        "|---|---|",
        *rows,
        "",
        "**③ INTELLIGENCE**",
        format_research(d.research),
        "",
        "**④ BATTLE PLAN**",
        f"- **Action:** {d.action}",
        f"- **Entry:** ${d.entry:,.2f}",
        f"- **Stop:** ${d.stop:,.2f}  (−{sig.stop_pct:.0%})" if sig else f"- **Stop:** ${d.stop:,.2f}",
        f"- **Target:** ${d.target:,.2f}  (+{sig.target_pct:.0%}, R:R {d.rr_ratio})" if sig else f"- **Target:** ${d.target:,.2f}",
        f"- **Size:** ${d.position_dollars:,.2f} (≈{shares:.4f} sh) — swing, no PDT consumed",
    ]
    if d.matched_strategies:
        out.append(f"- **Playbook:** {', '.join(d.matched_strategies)}")
    if d.caveats:
        out.append("")
        out.append("**⚠️ CAVEATS**")
        out += [f"- {c}" for c in d.caveats]
    out += [
        "",
        "_Plan only — requires `review_equity_order` + explicit user confirmation before placing._",
    ]
    return "\n".join(line for line in out if line != "")
