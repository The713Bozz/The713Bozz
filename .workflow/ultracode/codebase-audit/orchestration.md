# Orchestration

## Parent critical path
Spawn 4 explorers in parallel → wait all → integrate → write final-report.md

## Packets
1. `01-signals-risk` — explorer, read-only: src/signals/, src/risk/
2. `02-strategy-main` — explorer, read-only: src/strategy/, src/main.py
3. `03-config-hooks` — explorer, read-only: config/, hooks/
4. `04-skills-agents` — explorer, read-only: skills/, agents/

## Delegation
- native_agent_available: true (Claude Code Workflow tool)
- wave 1: all 4 explorers in parallel
- no write agents

## Wait points
All 4 explorers must complete before integration

## Verification order
1. Read all 4 results
2. Cross-check against CLAUDE.md described behaviors
3. Write integration.md + final-report.md
