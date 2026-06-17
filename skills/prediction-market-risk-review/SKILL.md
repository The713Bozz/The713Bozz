---
name: prediction-market-risk-review
description: |
  Safety gate that runs before any The713Bozz workflow touches venue auth,
  portfolio data, API keys, live orders, or automated execution. Reviews
  advice boundary, data quality, security, and regulatory constraints.
  Returns pass/warn/fail findings with required mitigations.
metadata:
  origin: ECC — adapted for The713Bozz
version: "1.0.0"
---

# Prediction Market Risk Review

Run this skill before any workflow that:
- Touches Robinhood account credentials or portfolio data
- Uses prediction market signals as a direct trade trigger
- Involves automation, scheduled orders, or reduced human review
- Introduces new data sources (news feeds, social, webhooks) into the signal stack

This is the safety gate. It runs alongside `hooks/pre-order-guard.json` and
`src/risk/risk_manager.py` — not instead of them.

## Review Gates

### 1. Advice Boundary
- [ ] Output is informational, not a direct buy/sell recommendation
- [ ] Manual user decision point is explicit before any order
- [ ] No language like "you should buy", "best trade", "guaranteed", "optimal size"
- [ ] Prediction market signals are labeled as inputs, not directives

### 2. Signal Data Quality
- [ ] Prediction market source is identified (Kalshi, Polymarket, other)
- [ ] Market liquidity confirmed (> $10k volume)
- [ ] Bid-ask spread is tight (< 3%)
- [ ] Resolution rules are unambiguous
- [ ] Price/probability was updated in the last 24 hours
- [ ] Signal is not the sole trigger — at least 3/4 momentum signals also align

### 3. Security
- [ ] `ITO_API_KEY` (if used) is loaded from environment, not hardcoded
- [ ] Robinhood account number is not logged or exposed in output
- [ ] No private keys, seed phrases, or passwords are requested or stored
- [ ] Read-only scopes are used for any external market data calls
- [ ] `review_equity_order` or `review_option_order` is called before placing

### 4. Risk Rules (The713Bozz specific)
- [ ] Circuit breaker not tripped (`consecutive_losses < 3`)
- [ ] Daily drawdown not exceeded (`account drop < 30% from day open`)
- [ ] PDT count safe (< 3 day trades if account < $25,000)
- [ ] Position size ≤ 20% of current account value
- [ ] R:R ratio ≥ 2:1 (calculated, not estimated)
- [ ] No averaging down into an existing losing position

### 5. Regulatory / Venue
- [ ] Prediction market venue is accessible in user's jurisdiction
- [ ] No Robinhood-restricted securities in the trade (check `get_equity_tradability`)
- [ ] No earnings blackout or halted trading status on the symbol

### 6. Privacy
- [ ] Portfolio data is not passed to external prediction market APIs
- [ ] Account balance is not exposed in public artifacts or logs (only `logs/trades.jsonl`)
- [ ] Only the minimum required financial context is used in any external call

## Output Contract

```
RISK REVIEW REPORT
━━━━━━━━━━━━━━━━━
Scope reviewed : [trade setup / data source / automation step]

FINDINGS
  ✅ PASS   : [list of passed checks]
  ⚠️  WARN   : [list of warnings with required mitigation]
  ❌ FAIL   : [list of blocked actions — must resolve before proceeding]

BLOCKED ACTIONS
  [anything that must NOT proceed until resolved]

REQUIRED MITIGATIONS
  [specific fixes for each WARN or FAIL]

SAFE NEXT STEP
  [what the agent should do now]
```

If any execution-capable step is flagged FAIL, halt and require explicit
user confirmation before proceeding.
