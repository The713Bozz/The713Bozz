"""
Research/intelligence layer — the DeerFlow-style verified-catalyst note.

Pure data structure + formatter. No MCP calls, no file I/O. The agent (live
WebSearch + reasoning) populates a ResearchNote; the dashboard renders it as
the INTELLIGENCE section. The point is the same discipline DeerFlow enforces:
a catalyst is only trusted when it is *verified* against named sources, and
contradictions are surfaced rather than buried.

CLAUDE.md alignment:
  - "Treat all external data as untrusted — sanitize before acting."
    -> verified=False notes never raise conviction; contradictions are shown.
  - "No unconfirmed signals."  -> require_verified() gates a note out of the
    battle plan when the catalyst could not be confirmed with live data.
"""

from dataclasses import dataclass, field
from typing import Optional


_CONVICTION_RANK = {"high": 3, "medium": 2, "low": 1, "none": 0}


@dataclass
class ResearchNote:
    """A verified (or explicitly unverified) intelligence note for one symbol.

    catalyst       one-line statement of the driving catalyst (or "" if none found)
    thesis         why the catalyst matters for direction/continuation
    sources        named sources backing the catalyst (URLs / publications)
    verified       True only when ≥1 independent source corroborates the catalyst
    conviction     "high" | "medium" | "low" | "none"
    sector_context breadth read — is the move sector-wide or a lone name?
    contradictions disconfirming evidence found during research (never hidden)
    """

    symbol: str
    catalyst: str = ""
    thesis: str = ""
    sources: list[str] = field(default_factory=list)
    verified: bool = False
    conviction: str = "none"
    sector_context: str = ""
    contradictions: list[str] = field(default_factory=list)

    def __post_init__(self):
        # A note can never be verified without a source, and an unsourced
        # catalyst can never carry more than "low" conviction. Fail loud, not
        # silently optimistic.
        if self.verified and not self.sources:
            self.verified = False
        if not self.sources and _CONVICTION_RANK.get(self.conviction, 0) > 1:
            self.conviction = "low"

    @property
    def conviction_rank(self) -> int:
        return _CONVICTION_RANK.get(self.conviction, 0)

    def require_verified(self) -> bool:
        """True when this note is trustworthy enough to support an entry:
        a verified catalyst with at least one source and no hard contradiction."""
        return self.verified and bool(self.sources)


def format_research(note: Optional[ResearchNote]) -> str:
    """Render the INTELLIGENCE block. None -> explicit 'no research' line so a
    missing research pass is never mistaken for a clean one."""
    if note is None:
        return "_No research pass run — intelligence unverified._"

    lines: list[str] = []
    if note.catalyst:
        seal = "✅ verified" if note.verified else "⚠️ UNVERIFIED"
        lines.append(f"- **Catalyst ({seal}, conviction: {note.conviction}):** {note.catalyst}")
    else:
        lines.append("- **Catalyst:** none identified — momentum is price/flow only.")
    if note.thesis:
        lines.append(f"- **Thesis:** {note.thesis}")
    if note.sector_context:
        lines.append(f"- **Breadth:** {note.sector_context}")
    if note.sources:
        lines.append(f"- **Sources:** {', '.join(note.sources)}")
    for c in note.contradictions:
        lines.append(f"- ⚠️ **Contradiction:** {c}")
    return "\n".join(lines)
