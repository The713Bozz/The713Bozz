# LESSONS — Hard-won, never to be repeated

This is the permanent memory of the system. Every mistake that cost real money or
real trust is recorded here with its root cause and the **mechanism** that now
prevents recurrence — because a lesson is not learned until it is enforced by code
or a rule, not merely remembered. Read this at the start of every session. Newest first.

Meta-fact worth holding: the account opened at **$50.00 on 2026-06-17** and, after two
weeks of activity (AMD, MARA, TTWO, QUBT, AMAT), sat at **$49.97**. Net progress: zero.
Almost every entry below is a variation on one theme — *activity is not edge.*

---

## 2026-07-01 — A confirmed exit that never executed (execution integrity)

**What happened.** AMAT's stop ($694) was breached. The user confirmed the exit
("sell"). I said "executing" — but the `place_equity_order` call never actually
fired: the session was interrupted between the confirmation and the order, and I
did not verify. Hours later the position was still open. AMAT had fallen from ~$689
(where the exit was reviewed) to **$650.91**.

**Cost.** The stop-sell would have realized ≈ **−$0.59**. Because it never placed,
the loss widened to ≈ **−$1.12 (−11%)** — the position fell another ~5% unmanaged.
Small dollars on a $10 position; a large breach of trust and discipline.

**Root cause.** I treated "the user confirmed" as "the order is done." I operated on
an *assumed* fill instead of verifying broker state, and I relied on my own session
staying alive to carry out a time-sensitive action.

**Mechanism (never again).**
- **Place AND verify in the same turn** — after `place_*_order`, immediately confirm
  the fill via `get_equity_orders` / `get_equity_positions`. Never report an order
  done without seeing it filled. (Codified: Always-Follow Rule #8.)
- **Queue time-sensitive exits at the broker**, not in my intentions. The broker
  queue is durable; the agent session is not.
- **Verify state, don't assume** — lead with `get_equity_positions`/`get_equity_orders`
  before claiming any prior action succeeded.

---

## 2026-07-01 — Asking permission for work I'm supposed to do myself (trust)

**What happened.** I repeatedly ended turns with "want me to run the scan?" — for the
market-open scan, which is a *built-in autonomous behavior*. I also let a fragile
wake-up chain silently fail to fire the 9:30 scan, and only discovered it when the
user asked why it hadn't run.

**Cost.** No dollars — trust. The user had to chase me for things the system exists to
do on its own. "I shouldn't have to ask every time."

**Root cause.** Offloading action back to the user, and relying on a scheduler I had to
babysit instead of a durable trigger.

**Mechanism (never again).** Operating Principle #0 — *do it yourself; only the
order-confirmation gate is deferred to the user.* Pre-market and open scans run and
report automatically (cron), and money-critical actions are broker-queued, not
wake-up-dependent.

---

## 2026-06-30 — New highs on light volume fade (volume must confirm)

**What happened.** The warning was on the record days earlier: on **2026-06-26** the scan
surfaced **10 names at 3/4, every one missing the volume signal** (SNOW, DDOG, LLY, JNJ,
SYK, TROW, PGR, ALL, UNH, ABBV) — and **9 of 10 faded** by the next session. Yet the
dashboard still treated volume as a *caveat*, not a gate. So on 6/30 we bought AMAT at
+5.5% on ~0.5× volume; it faded below entry that same close, and the entire light-volume
semicap complex **collapsed the next day** (AMAT −10%, KLAC/LRCX −6%, MU −5.7%).

**Root cause.** Volume — the signal that separates a real breakout from a fade — was
optional. A recorded warning (6/26) was not turned into an enforced rule until after it
cost a position.

**Mechanism (never again).** Volume is now a **gating signal**: absent/unconfirmed volume
downgrades BUY → WATCH, exactly like an unverified catalyst. A new high without volume
≥ 1.5× avg cannot carry a BUY. (Codified in `src/strategy/dashboard.py`.)

---

## 2026-06-29 — Volume projected on bad math (measurement discipline)

**What happened.** Mid-session I projected KLAC's full-day volume by *linear* extrapolation
(~5.9M) and called the move "light" (~0.38×), nearly disqualifying it. KLAC actually closed
near **14.6M (≈ average)**. My projection was off by ~2.5×.

**Root cause.** Intraday volume is **U-shaped** (heavy at the open and the close). A linear
projection from a mid-session partial systematically *under-counts*, producing false "light
volume" reads.

**Mechanism (never again).** Use a U-shape-aware estimate (e.g. ~42% of daily volume done by
~30% of session elapsed), and never disqualify a name on an early linear projection alone —
the decisive volume read comes in the afternoon. "Volume must be measured, not estimated."

---

## 2026-06-24 — Abandoning a plan to chase a hotter narrative (no-chase / lottery concentration)

**What happened.** The AMD position (bought 6/18 at ~$533 on a clean 4/4) was sold at a loss
in a bear regime, and TTWO (a GTA VI catalyst hold) was liquidated (~flat), to consolidate
~$50 and rotate into far-OTM **QUBT Jul17 $12 calls** chasing a "quantum catalyst." (Logged
as a user decision.) The lottery rotation did not compound — the account was back to ~$50.

**Root cause.** Liquidating existing, thesis-based setups to chase a newer, hotter story, and
concentrating a tiny account into a single far-out-of-the-money lottery option. (Cutting AMD
in a bear regime was defensible; cutting it *to chase quantum* was not.)

**Mechanism (never again).** No-chase discipline — *"the setup must come to you; do not chase
a stock that has already moved"* (`rules/trading-rules.md` #16). The regime gate blocks new
longs in bear. Conviction-only entries. Don't sell a thesis to fund a hotter one; don't bet
the whole account on one lottery ticket.

---

## The through-line

Every failure here shares one root: **trusting intent, assumption, or a hot narrative over
verified reality and durable mechanisms.** The fix is always the same shape — turn the lesson
into something the system *enforces* (a gate, a rule, a broker-side queue, an automatic
behavior), so a tired, interrupted, or excited future session cannot repeat it. Activity is
not edge; enforced discipline is.
