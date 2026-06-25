# Result 04: skills + agents

## Summary
momentum-compounder and market-analyst are actionable. ITO/prediction-market skills partially operational. One real conflict found.

## Verdict by skill
- momentum-compounder — FUNCTIONAL (concrete entry/exit rules)
- market-analyst.md — FUNCTIONAL (missing EMA computation detail)
- prediction-market-risk-review — FUNCTIONAL
- ito-trade-planner — FUNCTIONAL (no tools frontmatter)
- prediction-market-oracle-research — PARTIAL (no MCP for Kalshi/Polymarket)
- ito-market-intelligence — PARTIAL (no MCP or SDK specified)
- ito-basket-compare — PARTIAL (no tools frontmatter, no formal input contract)
- ito-data-atlas-agent — PARTIAL (design doc, not spawnable spec)
- ponytail — FUNCTIONAL (unrelated to trading)

## Key gaps
1. CONFLICT: momentum-compounder Phase 2 max_risk_pct=0.10 vs CLAUDE.md says 20% all phases
2. market-analyst.md missing get_equity_historicals interval/span parameters for EMA computation
3. Prediction market skills have no tool/API for Kalshi/Polymarket data
4. config/watchlist.json missing — skills that reference it will break
