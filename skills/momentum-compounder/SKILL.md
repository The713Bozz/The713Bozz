---
name: momentum-compounder
description: |
  $50→$500 challenge trading skill. Identifies high-probability momentum setups
  using volume surges, EMA crossovers, and relative strength. Sizes positions
  using Kelly-lite risk rules. Targets cheap options (< $0.30/contract) or
  fractional shares on breakouts. Cut losers at 50% of position, let winners
  reach 2x–5x. After phase 1 ($500), switches to compound growth mode.
version: "1.0.0"
---

# Momentum Compounder

## When to Use

- Claude is acting as the trading agent for The713Bozz challenge
- Evaluating whether a stock/option setup qualifies as a trade
- Sizing a position given current account value
- Deciding when to exit a position (profit or loss)
- Scanning the watchlist for setups during market hours

## Phase Logic

### Phase 1: $50 → $500 (Challenge)
- Max risk per trade: **20% of account**
- Min R:R: **2:1** (prefer 3:1 or better)
- Instruments: cheap OTM calls/puts ($0.05–$0.30/contract), fractional shares
- Setups: momentum breakouts, gap-and-go, earnings catalysts
- Stop: exit option at **-50%** of entry price
- Target: exit at **+100% to +400%** of entry price

### Phase 2: $500 → $5,000,000 (Compounding — same strategy, no change)
- **Identical rules to Phase 1.** Same risk %, same instruments, same signal stack.
- The only change: mode label updates to "Phase 2: Compounding ($500 → $5,000,000)."
- System runs until account reaches $5,000,000 or user explicitly stops it.
- Position sizes scale automatically — 20% of a growing account means bigger dollars with the same discipline.
- $5M milestone is logged in `config/challenge.json` as `ultimate_completed_at`.

## Signal Stack (all must align)

### Required (minimum 3 of 4 must be true):
1. **Relative Strength**: Stock up >3% on the day OR outperforming SPY by >2%
2. **Volume Surge**: Current volume > 1.5x 20-day average volume (intraday pace)
3. **EMA alignment**: Price above both 9 EMA and 21 EMA on 5-minute chart
4. **Trend**: Price within 10% of 52-week high OR breaking out of consolidation

### Bonus (increases conviction, allows larger size):
- Earnings catalyst within 5 days
- Sector rotation into this stock's sector
- High short interest (>10%) = squeeze potential
- Unusual options activity (high call volume vs open interest)

## Instrument Selection

### Options (preferred in Phase 1):
```
Target: 7–45 DTE, delta 0.20–0.45 (OTM but not too far)
Max cost: $0.30/contract ($30 per contract notional)
Contracts: floor($position_size / (option_price * 100))
Where: $position_size = account_value * max_risk_pct
```

### Equities (when options too expensive or illiquid):
```
Position size: account_value * max_risk_pct
Stop loss: entry_price * 0.92 (8% stop on shares)
Target: entry_price * 1.20+ (20%+ gain)
Use fractional shares if needed
```

## Position Sizing Formula

```python
account_value = get_portfolio()
phase = 1 if account_value < 500 else 2
max_risk_pct = 0.20 if phase == 1 else 0.20
risk_dollars = account_value * max_risk_pct

# For options:
max_contracts = int(risk_dollars / (option_price * 100))
max_contracts = max(1, min(max_contracts, 5))  # cap at 5 contracts

# For equities:
shares = risk_dollars / entry_price  # fractional ok
```

## Exit Rules

| Scenario | Action |
|----------|--------|
| Option down 50% | Sell immediately, no questions |
| Option up 100% | Sell half, move stop to breakeven on rest |
| Option up 200%+ | Sell 75%, let 25% run with no stop |
| Equity down 8% | Sell immediately |
| Equity up 20% | Sell half, trail stop on rest |
| End of day (options) | Close any position down >30% if DTE < 14 |

## Watchlist Categories

**Tier 1 (highest conviction — gap-up >5% + volume):**
- Any stock gapping >5% pre-market on earnings/news with unusual volume
- Check: TSLA, NVDA, AMD, MSTR, SMCI for momentum

**Tier 2 (trend plays — breakout setups):**
- Stocks making 52-week highs with increasing volume
- Focus on $5–$50 range stocks (options are cheaper)

**Tier 3 (speculative/squeeze):**
- High short interest + recent volume surge
- Risky — max 1 position at a time from this tier

## Pre-Trade Checklist

Before every order:
- [ ] Signal stack: ≥3/4 conditions met
- [ ] Account value confirmed via `get_portfolio`
- [ ] Risk calculation done: position ≤ max_risk_pct of account
- [ ] R:R ratio calculated and ≥ 2:1
- [ ] Consecutive losses < 3 (circuit breaker not tripped)
- [ ] Daily drawdown < 30% from day open
- [ ] PDT day trade count < 3 if account < $25k
- [ ] `review_equity_order` or `review_option_order` called and alerts reviewed
- [ ] User confirmed the order

## Post-Trade Actions

1. Log trade to `logs/trades.jsonl` with: symbol, instrument, entry price, size, signal reasons, timestamp
2. Update `config/challenge.json`: consecutive_losses, total_trades, state
3. Set price alerts for stop loss and target levels
4. Monitor position — check every 15 minutes during market hours
