# Integration

## Accepted
All 4 explorer results accepted. Cross-agent findings are consistent — no contradictions.

## Key cross-cutting observations
- The signal/risk/execution Python code is surprisingly complete and functional
- The integration layer (main.py as autonomous loop) is the biggest gap
- The safety hook exists but is dead code (not wired into settings.json)
- config/watchlist.json is the single most-referenced missing file across all 4 agents

## Conflicts
- Phase 2 risk %: momentum-compounder says 10%, CLAUDE.md says 20%. Resolve in CLAUDE.md or skill.

## Final changes
None — audit only.

## Verification still needed
- Confirm backports.zoneinfo is in requirements.txt for Python <3.9
- Confirm .claude/settings.json path is correct for hook wiring

## Remaining risks
- pre-order-guard not firing is a live safety gap right now
- learning.py KeyError will surface once 5 trades are logged
