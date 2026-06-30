"""
Strategy library — loads the ported playbooks from config/strategies/*.yaml and
tags which playbook(s) a scored candidate fits, given the regime and (optional)
verified research breadth.

This is the daily_stock_analysis contribution: instead of a bare 0–4 score, a
candidate is matched to a named strategy with an explicit regime fit — a
guardrail that says "this setup only works in these conditions."

Degrades gracefully: if PyYAML is missing or the dir is absent, returns [] with
a visible reason rather than crashing (matches the codebase's "skip enrichment
when data absent" convention).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml  # PyYAML — declared in requirements.txt
    _YAML_OK = True
except ImportError:  # pragma: no cover
    _YAML_OK = False

_STRATEGY_DIR = Path(__file__).parent.parent.parent / "config" / "strategies"


@dataclass
class Strategy:
    name: str
    label: str
    description: str
    fits_regime: list[str]
    required_signals: list[str]
    min_score: int = 3
    instrument_bias: str = "calls"
    requires_sector_breadth: bool = False
    notes: str = ""


@dataclass
class StrategyMatch:
    matched: list[Strategy] = field(default_factory=list)
    reason: str = ""

    @property
    def names(self) -> list[str]:
        return [s.label for s in self.matched]


def load_strategies(strategy_dir: Optional[Path] = None) -> list[Strategy]:
    if not _YAML_OK:
        return []
    d = strategy_dir or _STRATEGY_DIR
    if not d.is_dir():
        return []
    out: list[Strategy] = []
    for path in sorted(d.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError:
            continue  # one malformed file must not nuke the whole library
        out.append(
            Strategy(
                name=raw.get("name", path.stem),
                label=raw.get("label", path.stem),
                description=(raw.get("description") or "").strip(),
                fits_regime=raw.get("fits_regime", []),
                required_signals=raw.get("required_signals", []),
                min_score=int(raw.get("min_score", 3)),
                instrument_bias=raw.get("instrument_bias", "calls"),
                requires_sector_breadth=bool(raw.get("requires_sector_breadth", False)),
                notes=(raw.get("notes") or "").strip(),
            )
        )
    return out


def _has_signal(signal_names: list[str], token: str) -> bool:
    """Match a required token against a SignalResult's signal list.
    'near_high' is logical: technical.py emits near_52w_high / near_{N}d_high /
    near_3m_high / strong_breakout depending on bar span, so treat any of those
    as satisfying a 'near_high' requirement."""
    if token == "near_high":
        return any(
            s.startswith("near_") or s == "strong_breakout" for s in signal_names
        )
    return token in signal_names


def match_strategies(
    signal_names: list[str],
    score: int,
    regime: str,
    has_sector_breadth: bool = False,
    strategies: Optional[list[Strategy]] = None,
) -> StrategyMatch:
    """Return the playbooks this candidate qualifies for.

    A strategy matches when: regime fits, score >= its min_score, every required
    signal is present, and (if it requires breadth) breadth is confirmed.
    """
    lib = strategies if strategies is not None else load_strategies()
    if not lib:
        reason = (
            "PyYAML unavailable — strategy tagging skipped."
            if not _YAML_OK
            else "No strategy definitions found."
        )
        return StrategyMatch(matched=[], reason=reason)

    matched: list[Strategy] = []
    for st in lib:
        if st.fits_regime and regime not in st.fits_regime:
            continue
        if score < st.min_score:
            continue
        if not all(_has_signal(signal_names, t) for t in st.required_signals):
            continue
        if st.requires_sector_breadth and not has_sector_breadth:
            continue
        matched.append(st)

    if not matched:
        return StrategyMatch(matched=[], reason="No playbook fits this setup/regime.")
    return StrategyMatch(matched=matched, reason=f"{len(matched)} playbook(s) matched.")
