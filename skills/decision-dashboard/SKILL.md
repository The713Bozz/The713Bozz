---
name: decision-dashboard
description: >
  Canonical pre-trade pipeline for The713Bozz. Turns live market data + verified
  research into a gated 4-part Decision Dashboard, then routes to the broker
  review step. Invoke for EVERY trade candidate, before any order.
---

# Decision Dashboard — Standard Operating Procedure

This is the pipeline the system runs off. It combines a DeerFlow-style verified
research layer with the daily_stock_analysis four-part decision report, gated by
the existing risk rules. It **builds a plan; it never places an order.**

## The pipeline (5 steps)

1. **Regime** — Pull SPY (live MCP `get_equity_quotes` + recent `get_equity_historicals`).
   Classify via `src/signals/regime.py`. The resulting `position_scale` sets size:
   `1.0` bull · `0.5` ranging · `0.0` volatile/bear (stand aside).

2. **Scan + measure** — For each candidate, pull live quote + daily/intraday bars.
   Score the four signals with `src/signals/technical.py`:
   relative strength · **measured** volume (RVOL) · EMA alignment · breakout/near-high.
   *Volume must be MEASURED, not linearly projected* — early-session linear
   projection under-counts (volume is U-shaped). A new high on light volume fades.

3. **Verify research (DeerFlow layer)** — Build a `ResearchNote`
   (`src/signals/research.py`) from WebSearch + reasoning. A catalyst is only
   `verified=True` with ≥1 named source. Contradictions are recorded, never hidden.
   Confirm sector breadth (is the whole group moving, or one lone name?).

4. **Dashboard** — Run the CLI; it builds the report and the gated battle plan:

   ```bash
   python src/main.py --dashboard \
     --symbol <SYM> --price <px> --day-change <decimal> --score <0-4> \
     --signals "relative_strength,ema_aligned,near_61d_high" \
     --regime <bull|ranging|bear|volatile> --position-scale <1.0|0.5|0.0> \
     --stop-pct <decimal> --target-pct <decimal> \
     --catalyst "<one-liner>" --thesis "<why>" --sources "<a, b>" \
     --research-verified --conviction <high|medium|low> \
     --sector-context "<breadth read>" --account-value <value>
   ```

   Guardrails fire automatically:
   - Unverified catalyst → BUY downgraded to **WATCH**, "do not size up" caveat.
   - Volume signal absent → "new high on light volume fades" caveat.
   - Day change ≥ +6% → extension/chase warning (prefer pullback entry).
   - `position_scale == 0` (volatile/bear) → **stand aside**, no entry.
   - Playbook match from `config/strategies/*.yaml` (regime + signals + breadth).

5. **Review** — Take the battle plan to `review_equity_order` / `review_option_order`,
   present the preview + compliance disclosure, get **explicit user confirmation**,
   then `place_*_order`. **Never bypass review** (CLAUDE.md Always-Follow Rule #1).

## Output contract (`Dashboard`)

- **① core_conclusion** — action (BUY/WATCH/PASS), conviction, regime scale, matched playbook.
- **② data_perspective** — the measured 4-signal scorecard + day change.
- **③ intelligence** — verified research, sources, breadth, contradictions.
- **④ battle_plan** — entry / stop / target / R:R / position size + caveats.

## Non-negotiables

- The dashboard is a **plan**, not an order. Placement always needs user confirmation.
- No unverified catalyst raises conviction. No unmeasured volume passes the volume signal.
- Respect the regime scale and all standing risk gates (20% cap, 3-loss circuit
  breaker, daily drawdown, PDT). The dashboard does not override them.
