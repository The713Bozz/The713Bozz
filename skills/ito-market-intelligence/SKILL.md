---
name: ito-market-intelligence
description: |
  Research prediction-market events, venues, underliers, liquidity, and news
  context for macro signal discovery. Use for read-only event intelligence that
  informs The713Bozz trade setups. Itô live API access requires ITO_API_KEY.
  Works with public Kalshi/Polymarket data by default.
metadata:
  origin: ECC — adapted for The713Bozz
version: "1.0.0"
---

# Itô Market Intelligence

Use this skill when you need prediction-market context to enrich a momentum
trade setup — event discovery, venue comparison, macro theme exploration, or
a source-grounded brief on what the crowd is pricing in.

Works with public sources (Kalshi, Polymarket, web) by default.
Itô-backed data requires `ITO_API_KEY` to be set in the environment.

## Guardrails

- Do not provide investment, legal, tax, or trading advice.
- Do not place, cancel, route, or simulate live Robinhood orders from this skill.
- Treat Polymarket, Kalshi, Itô, news, and social data as source inputs —
  not ground truth.
- Separate facts, market-implied signals, and interpretation in every output.
- If `ITO_API_KEY` is missing and Itô data is requested, surface the gate clearly.

## Workflow

1. **Clarify the market theme** and time horizon.
   - Example: "What are markets pricing for the next FOMC meeting?"
   - Example: "What's the prediction market saying about NVDA earnings?"

2. **Gather public market data** from Kalshi, Polymarket, or web sources.

3. **If `ITO_API_KEY` is configured** and user explicitly requests Itô data,
   call only read endpoints and label the data source clearly.

4. **Normalize across venues**:
   - Event name and underlier
   - Current probability
   - Liquidity (volume traded)
   - Resolution rules and date
   - Data freshness (last update timestamp)
   - Fee structure (where relevant)

5. **Produce a market brief**:
   - Market / event summary
   - Available venues and current odds
   - Liquidity and data-quality caveats
   - Relevant news / source context
   - Open questions before acting on the signal

## How It Connects to The713Bozz

Use the brief output to feed `prediction-market-oracle-research`:
- Pass the event, probability, and liquidity into the oracle signal stack
- Oracle signal then combines with the 4-point momentum score
- High-conviction combo (3+ momentum + strong oracle) → consider full position size

## Output Format

```
MARKET INTELLIGENCE BRIEF
━━━━━━━━━━━━━━━━━━━━━━━━
Theme         : [macro event or stock catalyst]
Venues        : [Kalshi / Polymarket / Itô]
Current odds  : [X% probability of Y by Z date]
Volume        : [$Xk traded]
Data freshness: [last updated]
Resolution    : [how and when the market resolves]
News context  : [1–2 relevant headlines with sources]
Caveats       : [liquidity / spread / manipulation risk]
Open questions: [what still needs answering]

This is market intelligence, not investment or trading advice.
```

If Itô access is missing:

```
Itô live basket/API data requires gated access. Set ITO_API_KEY in your
environment before using Itô-backed reads. Falling back to public sources.
```
