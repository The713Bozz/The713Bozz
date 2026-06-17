---
name: prediction-market-oracle-research
description: |
  Research prediction-market probabilities (Fed decisions, earnings outcomes,
  macro events, geopolitical catalysts) as signal inputs for The713Bozz
  momentum trades. Use to evaluate whether macro-implied signals support or
  contradict a trade setup before entry. Not investment advice.
metadata:
  origin: ECC — adapted for The713Bozz
version: "1.0.0"
---

# Prediction Market Oracle Research

Use this skill when a momentum trade setup needs macro or event context. Prediction
market prices (Kalshi, Polymarket) represent crowd-implied probabilities of outcomes
— use them as one signal input alongside technical momentum signals, not as a
standalone trade trigger.

## When to Use

- Before entering a trade on a rate-sensitive stock (check Fed probability)
- Before an earnings play (check implied win/loss probability)
- When a stock is moving on macro news (check event resolution odds)
- When market direction is unclear (check SPY bull/bear market odds)
- When scanning for catalyst-driven setups (find upcoming high-probability events)

## Guardrails

- Do not treat prediction market prices as objective truth — they reflect crowd
  sentiment, not guaranteed outcomes.
- Do not place a trade based solely on a prediction market signal. It must align
  with at least 3/4 signals from the Momentum Compounder signal stack.
- Separate venue mechanics, liquidity, incentives, and resolution rules from the
  implied signal.
- Call out manipulation, thin liquidity, stale markets, and ambiguous outcomes.
- Always label prediction market data with source, timestamp, and liquidity caveat.
- This is informational input only — not investment advice.

## Research Workflow

1. **Define the trade decision** the signal is meant to inform.
   - Example: "Should I buy NVDA calls before the Fed meeting?"

2. **Find relevant markets** on Kalshi, Polymarket, or public prediction venues:
   - Search by event keyword (e.g., "Fed rate cut", "NVDA earnings", "CPI")
   - Record: market name, current probability %, volume, close date

3. **Evaluate signal quality**:
   - Liquidity: is there meaningful volume? (> $10k traded)
   - Spread: is the bid-ask tight? (< 3% spread = reliable)
   - Resolution: are the rules clear and unambiguous?
   - Age: was this market updated in the last 24 hours?

4. **Map signal to trade direction**:

   | Event | High Probability (>65%) | Low Probability (<35%) |
   |-------|------------------------|----------------------|
   | Fed rate cut | Bullish: tech, growth, NVDA, TSLA | Bearish: same names |
   | Earnings beat | Bullish: calls on the stock | Bearish: puts or avoid |
   | CPI hot | Bearish: growth stocks | Bullish: growth stocks |
   | Recession | Bearish: broad market | Bullish: broad market |

5. **Combine with momentum signals**:
   - Oracle signal supports momentum setup → increases conviction, can size up
   - Oracle signal contradicts momentum setup → reduce size or skip
   - Oracle signal is neutral/unclear → rely on momentum signals only

6. **Produce a signal brief** (see Output Contract below)

## Integration with The713Bozz Signal Stack

Treat the oracle signal as a **5th bonus signal** (in addition to the 4 momentum signals):

```
Score 3/4 momentum + oracle confirms → HIGH conviction, full size
Score 3/4 momentum + oracle neutral  → MEDIUM conviction, normal size
Score 3/4 momentum + oracle contradicts → SKIP or half size
Score 4/4 momentum + oracle confirms → MAXIMUM conviction, consider 2 positions
```

## Output Contract

```
ORACLE SIGNAL BRIEF
━━━━━━━━━━━━━━━━━━
Trade setup   : [symbol + instrument + direction]
Event context : [event name + market source]
Market odds   : [X% probability of Y outcome]
Signal quality: [liquidity / spread / resolution clarity]
Trade impact  : [supports / contradicts / neutral]
Caveats       : [thin liquidity / stale / ambiguous]
Conviction    : [high / medium / low]

Prediction-market signals are informational inputs, not investment advice.
```
