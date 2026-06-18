# Trading Rules — Always Follow

These rules are non-negotiable. They apply to every trade, every session.

## Capital Protection — Absolute Rules

0. **Treat every dollar as if your life depends on it.** This $50 is the seed of $5,000,000. Every trade decision must reflect that weight. No lazy entries, no impulsive exits, no FOMO. Act like losing it is not an option.
0. **Never transfer funds from the user's checking, debit, savings, or any external account.** Not for margin, not for a "sure thing," not for any reason. Only trade what is already inside the Robinhood brokerage account. If more capital is needed, stop and ask the user first.

## Risk Rules

1. **20% max per trade** (Phase 1). 10% max (Phase 2). Never exceed.
2. **2:1 minimum R:R**. If stop and target don't yield at least 2:1, skip the trade.
3. **Cut at -50% from entry mid on options, -8% on equities.** Stop is anchored to the (bid + ask) / 2 at the time of fill — not the ask fill price. Buying at the ask when the bid is lower means you are already below ask at fill; the stop must reflect real value. No exceptions. No "let it come back."
4. **No averaging down.** Ever. If a position is losing, wait for the stop or exit.
5. **Max 2 open positions** at any time.

## Autonomous Scan Rules

6a. **Scan at 9:30 AM ET every market day — no permission needed.** Pull quotes on all 20 watchlist symbols, score signals, report top candidates and the market context (SPY/QQQ direction).
6b. **Pre-market scan at 9:00 AM ET — no permission needed.** Flag any symbol up >3% pre-market as a priority setup for open.
6c. **Scanning is never a trade.** Autonomous scans report findings only. No order is placed without explicit user confirmation.

## Process Rules

6. **Always review before placing.** Call `review_equity_order` or `review_option_order`. Read every alert. Confirm with user.
7. **Log every trade.** Win, loss, or cancelled. Include signal reasons.
8. **Check circuit breaker first.** 3 consecutive losses = stop for the day, alert user, require manual reset.
9. **Check PDT count** before any intraday buy+sell. If near limit, swing trade only.
9b. **PDT + late-week DTE escalation**: If day trades used ≥ 2 AND it is Thursday or Friday, require DTE ≥ 14. Never enter a 7-DTE contract on a Thursday or Friday when the PDT guard is active — you cannot exit same-day, and a Monday gap will blow straight through the stop without triggering it.
10. **No trading the last 5 minutes** of market session unless closing an existing position.

## Market Context Rules

11. **If SPY is down >1.5%**, only take short setups (puts) or stay in cash. No long calls.
12. **Avoid FOMC days** unless already positioned before the announcement.
13. **No earnings plays on same day** unless unusual options activity is confirmed and DTE > 1 day.
14. **Liquidity check**: options bid/ask ratio must be ≥ 0.60 (bid ≥ 60% of ask). Minimum ask price is $0.10 — never buy sub-dime contracts. An absolute $0.10 spread cap is not sufficient: a $0.05 bid / $0.10 ask passes the old rule but puts you -50% at fill. The ratio check is the enforceable gate.

## Mindset Rules (for the agent)

15. **Missing a trade is not a loss.** Patience beats FOMO every time.
16. **The setup must come to you.** Do not chase a stock that has already moved 10%+ without you.
17. **One good trade beats five bad ones.** Quality > quantity.
18. **After a loss, wait 30 minutes before the next scan.** Don't revenge trade.
