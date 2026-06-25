# Result 03: config + hooks

## Summary
challenge.json is valid and well-structured. Two critical gaps: watchlist.json missing, pre-order-guard not wired.

## Verdict by file
- config/challenge.json — PARTIAL (no live account_value field, day_open_value only)
- config/watchlist.json — MISSING
- hooks/pre-order-guard.json — PARTIAL (exists but NOT in .claude/settings.json, --account-value hardcoded to 50)

## Key gaps
1. config/watchlist.json does not exist anywhere in repo
2. hooks/pre-order-guard.json not referenced in .claude/settings.json → never fires
3. pre-order-guard hardcodes --account-value 50 → risk gate wrong for any balance > $50
4. No live current_account_value in challenge.json
