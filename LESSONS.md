# LESSONS — Hard-won, never to be repeated

This is the permanent memory of the system. Every mistake that cost real money or
real trust is recorded here with its root cause and the **mechanism** that now
prevents recurrence — because a lesson is not learned until it is enforced by code
or a rule, not merely remembered. Read this at the start of every session. Newest first.

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
staying alive to carry out a time-sensitive action. Both are forbidden by Rule #2
(no stale assumptions) — I violated my own rule.

**Mechanism (never again).**
- **Place AND verify in the same turn** — after `place_*_order`, immediately confirm
  the fill via `get_equity_orders` / `get_equity_positions`. Never report an order
  done without seeing it filled. (Codified: Always-Follow Rule #8.)
- **Queue time-sensitive exits at the broker**, not in my intentions. The broker
  queue is durable; the agent session is not. (The eventual fix was a broker-queued
  market-sell that fires at the open regardless of whether my session is awake.)
- **Verify state, don't assume** — lead with `get_equity_positions`/`get_equity_orders`
  before claiming any prior action succeeded.

---

## 2026-06-30 — New highs on light volume fade (volume must confirm)

**What happened.** Three straight sessions, the "leaders" (semicap/AI: AMAT, KLAC,
LRCX, MRVL…) ran to new highs on **below-average volume** (RVOL ~0.3–0.5×). The
dashboard flagged it only as a *caveat* and still rated AMAT a BUY. We bought AMAT
at +5.5% on ~0.5× volume; it faded below entry that same close, and the entire
light-volume complex **collapsed the next day** (AMAT −10%, KLAC/LRCX −6%, MU −5.7%).

**Root cause.** Volume — the signal that separates a real breakout from a fade — was
treated as optional. Price without participation is not a breakout.

**Mechanism (never again).** Volume is now a **gating signal**: absent/unconfirmed
volume downgrades BUY → WATCH, exactly like an unverified catalyst. A new high
without volume ≥ 1.5× avg cannot carry a full BUY. (Codified in `src/strategy/dashboard.py`.)

---

## The through-line

Every failure here shares one root: **trusting intent or assumption over verified
reality and durable mechanisms.** The fix is always the same shape — turn the lesson
into something the system *enforces*, so a tired or interrupted future session cannot
repeat it.
