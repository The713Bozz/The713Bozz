---
name: ito-basket-compare
description: |
  Compare Itô prediction-market baskets or macro event themes against The713Bozz
  watchlist, current positions, and momentum signals. Use for read-only gap
  analysis — identifies alignment, conflicts, and stale assumptions between
  prediction market odds and your equity/options setups. Not investment advice.
metadata:
  origin: ECC — adapted for The713Bozz
version: "1.0.0"
---

# Itô Basket Compare

Use this skill to compare a prediction-market basket or event theme against
The713Bozz watchlist, open positions, or the momentum signal stack.

This is a gap analysis and alignment check — it does not recommend trades.
It helps surface where prediction market odds agree with, conflict with, or
add context to existing setups.

## Guardrails

- Do not provide investment advice or tell the user to buy, sell, hold, or size a trade.
- Do not execute, prepare, or submit Robinhood orders.
- Use `ITO_API_KEY` only for read-only Itô basket/market data after explicit user request.
- Do not infer or assume the user's financial situation.
- Phrase all output as inspection and questions, not directives.

## Comparison Modes

### Mode 1: Basket vs Watchlist

1. Identify the basket theme and its underlying events/securities.
2. Map each watchlist symbol to relevant prediction market events.
3. Check alignment: does the basket's implied direction match the momentum signal?
4. Flag conflicts: stock is bullish on technicals but prediction market is bearish on the catalyst.
5. Flag missing research: symbols with no relevant prediction market coverage.

### Mode 2: Basket vs Open Positions

1. Parse current open positions (from `get_equity_positions` / `get_option_positions`).
2. Compare basket themes against position exposure.
3. Flag concentration: multiple positions betting on the same macro outcome.
4. Flag correlation: positions that all lose if the same event resolves the wrong way.
5. Return questions, not recommendations.

### Mode 3: Basket vs Momentum Signal Stack

1. Accept the current signal scores for watchlist symbols.
2. Layer the basket's prediction market probabilities on top.
3. Identify where oracle signal + momentum signal align (high conviction).
4. Identify where they diverge (reduced conviction or skip).

## Output Contract

```
BASKET COMPARISON
━━━━━━━━━━━━━━━━
Basket theme     : [macro theme or event set]
Comparison target: [watchlist / positions / signal stack]

MATCHES
  [symbols / signals that align with basket direction]

CONFLICTS OR STALE ASSUMPTIONS
  [symbols / signals that diverge — flag for review]

MISSING CONTEXT
  [gaps where no prediction market data exists]

USER-ACTION CHECKLIST
  [ ] Review conflicts before next trade
  [ ] Update stale assumptions with fresh data
  [ ] Run prediction-market-risk-review if proceeding to execution

This comparison is informational and not investment or trading advice.
```
