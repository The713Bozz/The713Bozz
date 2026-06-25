# Final report — Codebase Audit

## Outcome
The signal, risk, data, and execution layers are largely functional Python code. The autonomous trading loop does not exist. Two safety-critical gaps are live right now.

## What exists vs. what's missing

### FUNCTIONAL (built, no action needed)
| File | What it does |
|------|-------------|
| src/signals/technical.py | 4-signal scoring stack (RS, volume, EMA, 52w high) |
| src/signals/scanner.py | MCP scan + standalone Finnhub scan |
| src/signals/catalyst.py | Earnings window + news hard-block gate |
| src/signals/regime.py | SPY regime classifier (bull/bear/volatile/ranging) |
| src/risk/risk_manager.py | Full risk suite: sizing, PDT, drawdown, circuit breaker |
| src/execution/order.py | Order builder with all gate chains |
| src/data/finnhub.py | Finnhub API client |
| src/data/alphavantage.py | AlphaVantage EMA + intraday client |
| src/data/coingecko.py | BTC gate for crypto-correlated symbols |
| src/data/fmp.py | FMP earnings + analyst grades client |
| src/strategy/watchlist.py | Tier 1/2/3 symbol lists + get_scan_list() |
| skills/momentum-compounder | Concrete entry/exit rules, position sizing formulas |
| agents/market-analyst.md | Detailed subagent spec, runnable |
| skills/ito-trade-planner | Pre-trade worksheet generator |
| skills/prediction-market-risk-review | Safety checklist with correct numeric thresholds |
| config/challenge.json | Valid state file with correct risk parameters |

### BUGS (will crash at runtime)
| Location | Bug |
|----------|-----|
| src/signals/learning.py:139,146 | d['wins'] KeyError — key is 'weighted_wins'. Crashes once >=5 trades logged. |

### MISSING (described in CLAUDE.md, does not exist)
| What | Why it matters |
|------|---------------|
| config/watchlist.json | Every skill and the scanner references this. Scan pipeline breaks without it. |
| Autonomous event loop | main.py is a CLI toolkit. No scheduler, no 9:30 AM trigger, no daemon mode. |
| --mode / --account args | CLAUDE.md documents these CLI flags but argparse doesn't define them. |
| src/strategy/trade_decision.py | No programmatic signal-to-order pipeline. Agent is the decision layer. |

### DEAD CODE (exists but never fires)
| What | Why |
|------|-----|
| hooks/pre-order-guard.json | Not referenced in .claude/settings.json → Claude Code never runs it |
| pre-order-guard --account-value 50 | Hardcoded starting balance → risk gate wrong the moment account grows |

### CONFLICT
| | CLAUDE.md | momentum-compounder SKILL.md |
|--|-----------|------------------------------|
| Phase 2 max risk | 20% all phases | 10% in Phase 2 |

## Prioritized build plan

### P1 — CRITICAL (fix before next trade)
1. **Wire the pre-order-guard hook** into `.claude/settings.json`
2. **Fix hook account-value** — replace hardcoded `50` with dynamic `get_portfolio` call
3. **Create config/watchlist.json** — 20 symbols matching watchlist.py tiers

### P2 — HIGH (will crash at runtime)
4. **Fix learning.py KeyError** — lines 139/146: `d['wins']` → `round(d['win_rate'] * d['total'])`
5. **Resolve Phase 2 risk conflict** — pick one: 20% (CLAUDE.md) or 10% (skill)
6. **Add current_account_value to challenge.json** — live balance field separate from day_open_value

### P3 — MEDIUM (autonomous operation)
7. **Session-start scan** — wire `--scan` into session-start hook so every session auto-scans
8. **Add --mode / --account args** to src/main.py argparse
9. **Build src/strategy/trade_decision.py** — signal score → order spec pipeline

### P4 — LOW (quality)
10. Add EMA params to market-analyst.md (interval='5minute', span='day')
11. Add tools frontmatter to ito-basket-compare and ito-trade-planner
12. Populate __init__.py files with public exports

## Skipped checks
- Did not run the code (read-only audit)
- Did not verify API keys are set

## Remaining risk
- Pre-order-guard not firing is an active safety gap right now
- config/watchlist.json missing means scanner has no symbol list to iterate
