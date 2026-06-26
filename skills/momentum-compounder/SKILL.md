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
2. **Volume Surge**: Current volume > 1.5x 14-day average volume (intraday pace).
   The 14-day baseline uses `bars[-(vol_window+1):-1]` — it **excludes the reference/today bar**
   so the average is not inflated by the session being measured. Do not use `bars[-14:]` in
   ad-hoc checks; that includes yesterday and produces a slightly different baseline.
3. **EMA alignment**: 9-day EMA above 21-day EMA (daily bars)
4. **Trend**: Price within 10% of 52-week high OR breaking out of consolidation.
   When fewer than 252 bars are available (e.g. ~61 bars with a 90-calendar-day lookback),
   the signal is labeled `near_{N}d_high` (not `near_52w_high`) to reflect the actual bar
   span. A 90-calendar-day lookback yields ~61 trading days — the true 52-week high is
   unavailable. The high_3m gate (price ≥90% of 63-bar max) and strong_breakout fallback
   (≥5% day change) still apply as alternates.

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

## MCP Scan Protocol (agent session)

Execute in this order to keep scan time under 3 minutes and usage under 15%:

1. **Fetch SPY quote** — check `spy_cache` in `challenge.json` first (valid 26h). Only call MCP if stale.
2. **Gate on SPY change** (use `get_tiered_scan_symbols(spy_change)` from `src/strategy/watchlist.py`):
   - SPY <1%  → Tier 1 only (164 symbols, ~4 batches) — *most common case*
   - SPY 1–2% → Tier 1 + Tier 2 (494 symbols, ~13 batches)
   - SPY ≥2%  → All 576 (15 batches) — only on genuine surge days
3. **Batch size: 40 symbols per `get_equity_quotes` call** — MCP closes are omitted above 20, but RS uses `adjusted_previous_close` from the quote itself, so closes are not needed.
4. **Parallelism: max 4 calls per wave** — ≥10 simultaneous crashes the stream.
5. **RS pre-filter first**: only fetch historicals for symbols with day_change >3%. On flat days this is zero — skip historicals entirely.
   - **Lookback**: use `start_time` ≥90 calendar days back (~63 trading days). Less than 63 bars skips `high_3m` entirely and leaves the 21-EMA underwarmed.
   - **Today's volume**: daily bars end at yesterday's close. For live volume, fetch 5-min intraday bars from today's open separately, sum their volumes, and pass `today_volumes={symbol: sum * (390 / minutes_elapsed)}` to `run_scan()`.
   - **Format**: `run_scan()` auto-normalizes raw MCP bar dicts — pass them directly, no manual conversion needed.
   - **Missing historicals warning**: `run_scan()` prints a warning when RS candidates (day_change ≥3%) have no historicals. These symbols score only the RS signal — volume/EMA/high signals are all unavailable.
6. **Breakout alerts**: `filter_candidates()` passes through any symbol with `day_change ≥8% AND score ≥2`, even below the 3/4 minimum. These appear as `!! BREAKOUT ALERTS` in `print_scan_report()`. They are not trade signals — they flag news-driven explosions that may need catalyst verification before entry.
7. **Inverse and leveraged bear ETFs** (SOXS, SQQQ, SPXS, SDOW, etc.): These appear in Tier 1 and will generate RS signals on down-market days. They are **not standard long momentum setups** — a high RS day for SOXS means the underlying sector (semiconductors) is crashing. Do not apply the standard breakout/EMA/high framework to them. If they appear in candidates, note the inverse nature and skip unless explicitly trading the downside.

Expected times at batch=40, max 4 parallel:
| Regime | Symbols | Batches | Waves | Time |
|--------|---------|---------|-------|------|
| Flat (SPY <1%) | 164 | 5 | 2 | ~45 s |
| Active (SPY 1–2%) | 494 | 13 | 4 | ~2 min |
| Surge (SPY ≥2%) | 576 | 15 | 4 | ~2.5 min |

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
