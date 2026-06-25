# Result 01: signals + risk

## Summary
signals/ is mostly functional. risk_manager.py is fully functional. One real bug in learning.py.

## Verdict by file
- technical.py — FUNCTIONAL
- scanner.py — FUNCTIONAL (fragility: timestamp format assumption)
- catalyst.py — FUNCTIONAL
- regime.py — FUNCTIONAL
- learning.py — PARTIAL (KeyError bug lines 139/146)
- risk_manager.py — FUNCTIONAL
- __init__.py (both) — stubs, not functional blockers

## Key gaps
1. learning.py d['wins'] KeyError — crashes once >=5 closed trades logged
2. scanner.py day_open_value uninitialized on first run — drawdown check always passes
3. spy_bars=[] failure-open — empty bars skip regime gate silently
