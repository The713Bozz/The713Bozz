---
name: ito-trade-planner
description: |
  Build a non-advisory pre-trade planning worksheet for The713Bozz setups.
  Captures venue, underlier, signal sources, constraint checks, open questions,
  and manual execution steps before touching Robinhood order tools. Does not
  place trades or recommend positions.
metadata:
  origin: ECC — adapted for The713Bozz
version: "1.0.0"
---

# Itô Trade Planner

Use this skill to produce a structured planning worksheet before entering a
trade. It captures everything needed for a clean decision — signal sources,
prediction market context, risk parameters, open questions — so the user can
review and approve before any Robinhood MCP order tool is called.

The skill is intentionally non-executing. It hands a checklist to the user.

## Guardrails

- Do not say a trade is good, bad, optimal, or recommended.
- Do not provide investment advice or position sizing advice.
- Do not call `place_equity_order` or `place_option_order` from this skill.
- Do not request private keys, exchange passwords, or account credentials.
- Always require explicit user approval before moving from planning to execution.

## Planning Workflow

1. **Restate the trade idea** as a neutral hypothesis:
   - "If [event/signal], then [instrument] on [symbol] could move [direction]."

2. **Capture signal sources**:
   - Momentum signal score (from `market-analyst` agent)
   - Oracle signal (from `prediction-market-oracle-research`)
   - Any news or catalyst context (from `ito-market-intelligence`)

3. **Pull live instrument data** (read-only):
   - Quote: `get_equity_quotes` or `get_option_quotes`
   - Tradability: `get_equity_tradability`
   - Options chain (if applicable): `get_option_chains` → `get_option_instruments`

4. **Calculate risk parameters**:
   - Account value: `get_portfolio`
   - Max position size: account_value × 0.20
   - Entry price, stop price, target price
   - R:R ratio = (target - entry) / (entry - stop)
   - Contract count (if options): floor(position_size / (option_price × 100))

5. **Run `prediction-market-risk-review`** — all gates must pass before proceeding.

6. **Build the worksheet** (see Output Contract).

7. **Present to user for approval** — do not proceed to `review_equity_order`
   or `review_option_order` until the user explicitly confirms.

## Allowed Language

Use:
- "planning worksheet"
- "questions to answer before acting"
- "observable data"
- "risk and constraint check"

Avoid:
- "you should buy/sell"
- "best trade"
- "guaranteed"
- "risk-free"
- "optimal size"

## Output Contract

```
TRADE PLANNING WORKSHEET
━━━━━━━━━━━━━━━━━━━━━━━
Hypothesis    : [neutral restatement of trade idea]
Symbol        : [ticker]
Instrument    : [equity / call / put]
Expiry / DTE  : [date / days to expiry]
Strike        : [if options]

SIGNAL SOURCES
  Momentum score  : [X/4 — signals: ...]
  Oracle signal   : [supports / contradicts / neutral — source + odds]
  Catalyst        : [event name + date if applicable]

RISK PARAMETERS
  Account value   : $[X]
  Max position    : $[X × 0.20]
  Entry price     : $[X]
  Stop price      : $[X] ([Y]% loss on position)
  Target price    : $[X] ([Y]% gain on position)
  R:R ratio       : [X:1]
  Contracts / Qty : [X]

RISK REVIEW      : [PASS / WARN / FAIL — from prediction-market-risk-review]

OPEN QUESTIONS
  [ ] [anything unresolved before acting]

NEXT STEP (requires your approval)
  → Call review_equity_order / review_option_order with the above parameters
  → Present alerts to you
  → Wait for explicit confirmation before placing

This is a planning worksheet, not investment or trading advice. Review all
parameters and make the final decision yourself.
```
