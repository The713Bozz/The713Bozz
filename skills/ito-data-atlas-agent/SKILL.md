---
name: ito-data-atlas-agent
description: |
  Design and run a background research agent for The713Bozz that watches
  prediction market data sources, builds candidate trade setups, drafts
  signal parameters, and routes them through human-in-the-loop approval
  before any Robinhood order tool is called.
metadata:
  origin: ECC — adapted for The713Bozz
version: "1.0.0"
---

# Itô Data Atlas Agent

Use this skill to design or invoke a background research agent that continuously
watches prediction market signals, pairs them with momentum technical signals, and
surfaces trade candidates for human review — without placing orders autonomously.

## Guardrails

- All execution is behind explicit human approval.
- `ITO_API_KEY` is used only for read-only Itô data access.
- Robinhood order tools (`place_equity_order`, `place_option_order`) are never
  called by this agent — only by the user after reviewing the worksheet.
- Do not persist portfolio data or account numbers outside `config/challenge.json`
  and `logs/trades.jsonl`.
- Run `prediction-market-risk-review` before surfacing any candidate to the user.

## Four-Lane Architecture

```
Lane 1: RESEARCH COLLECTOR
  Sources: Kalshi, Polymarket, public news, X (if configured), Itô read endpoints
  Skills : ito-market-intelligence, prediction-market-oracle-research
  Output : raw event data, odds, liquidity, freshness

Lane 2: SIGNAL DRAFTER
  Sources: Lane 1 output + Robinhood quotes/historicals + momentum signal stack
  Skills : market-analyst agent, ito-basket-compare
  Output : candidate setups with signal score + oracle confirmation

Lane 3: RISK REVIEWER
  Sources: Lane 2 candidates + current portfolio + challenge state
  Skills : prediction-market-risk-review
  Output : pass/warn/fail for each candidate, with required mitigations

Lane 4: HUMAN EDITOR
  Sources: Lane 3 output
  Skills : ito-trade-planner (produces the worksheet)
  Action : presents worksheet to user → waits for explicit approval
           → only then calls review_equity_order / review_option_order
```

## Workflow

1. **Define the scan objective**:
   - "Find momentum setups where prediction market odds also support the direction."

2. **Run Lane 1** — collect prediction market events relevant to watchlist symbols.

3. **Run Lane 2** — score each symbol: momentum signal (0–4) + oracle signal (support/neutral/contradict).
   Filter: momentum score ≥ 3 AND oracle ≠ contradict.

4. **Run Lane 3** — risk review each passing candidate.
   Drop any candidate with a FAIL finding.

5. **Run Lane 4** — produce `ito-trade-planner` worksheet for each surviving candidate.
   Present to user ranked by conviction (highest first).

6. **Wait for user approval** on each candidate before proceeding to order review.

7. **Log the audit trail** to `logs/trades.jsonl`:
   - Inputs (sources, timestamps, signal scores)
   - Agent output (candidates surfaced)
   - Human decision (approved / rejected / modified)
   - Final order outcome

## Useful Skill Chains

```
ito-market-intelligence
  → prediction-market-oracle-research
    → ito-basket-compare (optional, for watchlist gap analysis)
      → prediction-market-risk-review
        → ito-trade-planner
          → [user approval]
            → review_equity_order / review_option_order
              → place_equity_order / place_option_order
```

## Output Contract

Return an implementation-ready scan summary:

```
DATA ATLAS SCAN SUMMARY
━━━━━━━━━━━━━━━━━━━━━━
Run at        : [timestamp]
Symbols scanned: [N]
Candidates    : [M passed all lanes]

RANKED CANDIDATES
  1. [symbol] — Score: [X/4 momentum + oracle: support] — [brief rationale]
  2. ...

DROPPED
  [symbol] — [reason: FAIL on risk review / oracle contradicts / score < 3]

AUDIT TRAIL
  Logged to logs/trades.jsonl ✓

NEXT STEP
  Review worksheet(s) above and confirm to proceed to order review.
```
