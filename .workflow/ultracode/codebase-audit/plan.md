# Codebase Audit — Trading System

## Goal
Determine what is actually built and functional vs. what CLAUDE.md describes but is missing or incomplete. Produce a prioritized build plan.

## Success criteria
- Every directory in src/, config/, hooks/, skills/ is read and assessed
- Each module has a clear built/stub/missing verdict
- Output is a ranked list of gaps blocking the autonomous loop

## Risk level
low — read-only, no edits

## Mode
delegated — 4 parallel explorer agents, parent integrates

## Eval contract
- Outcome: gap report + prioritized build plan
- Shared surfaces: none (read-only)
- Required checks: none
- Blocking conditions: none
- Handoff evidence: each agent returns findings with file:line citations

## Work packets
1. src/signals/ + src/risk/ — signal and risk modules
2. src/strategy/ + src/main.py — strategy logic and orchestration loop
3. config/ + hooks/ — config state and safety hooks
4. skills/momentum-compounder/ + agents/ — strategy skill and subagent spec

## Completion criteria
All 4 packets complete, integration.md written, final-report.md delivered.
