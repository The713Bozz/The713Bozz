import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "challenge.json"
LOG_PATH = Path(__file__).parent.parent.parent / "logs" / "trades.jsonl"

# Kill switch: set TRADING_HALTED=1 in environment to abort all order paths instantly.
_KILL_SWITCH = os.environ.get("TRADING_HALTED", "").strip().lower() in ("1", "true", "yes")


@dataclass
class RiskCheck:
    allowed: bool
    reason: str
    max_dollars: float = 0.0


# Hard block — never call any external transfer tool without user permission.
BLOCKED_ACTIONS = frozenset([
    "transfer_funds",
    "initiate_ach",
    "ach_transfer",
    "deposit",
    "withdraw",
    "link_bank",
    "move_money",
])


def assert_no_external_transfer(action: str) -> None:
    if action.lower().replace(" ", "_") in BLOCKED_ACTIONS:
        raise PermissionError(
            f"BLOCKED: '{action}' is not permitted. "
            "Never transfer funds from an external account without explicit user permission."
        )


def load_state() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_agentic_account() -> str:
    """
    Return the agentic challenge account number from config/challenge.json.
    ALWAYS use this for portfolio fetches and order calls — never hardcode,
    never guess, never use the margin account.
    """
    cfg = load_state()
    acct = cfg.get("account", {}).get("agentic_account_number")
    if not acct:
        raise ValueError(
            "agentic_account_number not set in config/challenge.json. "
            "Cannot proceed without a verified account number."
        )
    return acct


def assert_agentic_account(account_number: str) -> None:
    """
    Raise PermissionError if account_number does not match the agentic challenge account.
    Call before any order placement to prevent touching the wrong account.
    """
    expected = get_agentic_account()
    if str(account_number).strip() != str(expected).strip():
        raise PermissionError(
            f"WRONG ACCOUNT: '{account_number}' is not the agentic challenge account. "
            f"Expected '{expected}'. Never touch any other account."
        )


def save_state(state: dict) -> None:
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, CONFIG_PATH)  # atomic on Linux — no corrupt-on-crash window


def get_phase(account_value: float) -> int:
    cfg = load_state()
    return 1 if account_value < cfg["challenge"]["phase1_target"] else 2


def max_risk_pct(
    account_value: float,
    score: Optional[int] = None,
    catalyst_clear: Optional[bool] = None,
) -> float:
    """
    Risk fraction of account for a single trade.

    Convex barbell (config["convex"]): base size on ordinary 3/4 setups, and an
    upsized "high-conviction" fraction ONLY on a score >= high_conviction_min_score
    (a 4/4, which already requires the volume signal) AND, when required, a confirmed
    catalyst (catalyst_clear is True). Callers that pass no score get the base size,
    so every existing call is unchanged.
    """
    cfg = load_state()
    risk = cfg.get("risk", {})
    conv = cfg.get("convex", {})
    base = conv.get("base_risk_pct", risk.get("max_risk_per_trade_pct", 0.20))

    if conv.get("enabled") and score is not None:
        min_score = conv.get("high_conviction_min_score", 4)
        needs_cat = conv.get("high_conviction_requires_catalyst", True)
        if score >= min_score and (catalyst_clear is True or not needs_cat):
            return conv.get("high_conviction_risk_pct", base)
    return base


def position_size(
    account_value: float,
    score: Optional[int] = None,
    catalyst_clear: Optional[bool] = None,
) -> float:
    return account_value * max_risk_pct(account_value, score, catalyst_clear)


def option_contracts(account_value: float, option_price: float) -> int:
    cfg = load_state()
    max_contracts = cfg["instruments"].get("option_max_contracts", 5)
    dollars = position_size(account_value)
    contracts = int(dollars / (option_price * 100))
    return max(1, min(contracts, max_contracts))


def check_option_liquidity(bid: float, ask: float) -> RiskCheck:
    """
    Reject options where the bid/ask spread would put you near or past the
    -50% hard stop the instant the buy order fills.

    Minimum ask $0.10: sub-dime contracts have nearly 100% proportional spreads.
    Minimum bid/ask ratio 0.60: buying at ask with bid at 60% of ask means
    you are immediately 40% down on paper — survivable. Below 0.60 you are
    already inside the stop zone at fill.
    """
    cfg = load_state()
    min_ask = cfg["risk"].get("min_option_ask", 0.10)
    min_ratio = cfg["risk"].get("min_bid_ask_ratio", 0.60)

    if ask <= 0:
        return RiskCheck(False, "Invalid option ask price (zero or negative).")

    if ask < min_ask:
        return RiskCheck(
            False,
            f"Option ask ${ask:.2f} is below the ${min_ask:.2f} floor. "
            "Sub-dime contracts have lethal spreads — skip this contract.",
        )

    ratio = bid / ask
    if ratio < min_ratio:
        immediate_loss = (ask - bid) / ask
        return RiskCheck(
            False,
            f"Spread too wide: bid/ask ratio {ratio:.0%} < {min_ratio:.0%} minimum. "
            f"Filling at ${ask:.2f} with bid ${bid:.2f} puts you {immediate_loss:.0%} down instantly — "
            "this fires the -50% stop before the trade has a chance to work.",
        )

    return RiskCheck(True, f"Liquidity OK — bid/ask ratio {ratio:.0%} ≥ {min_ratio:.0%}.")


def check_quote_freshness(quote_timestamp_utc: str, max_age_seconds: int = 60) -> RiskCheck:
    """
    Reject stale quotes before order placement.
    Guards the review→place race condition: if the quote used in review_option_order
    is older than max_age_seconds, require a fresh review before placing.
    quote_timestamp_utc: ISO 8601 string from MCP venue_last_trade_time or similar.
    """
    try:
        ts_str = quote_timestamp_utc.replace("Z", "+00:00")
        ts_str = re.sub(r'(\.\d{6})\d+', r'\1', ts_str)  # truncate nanoseconds to microseconds
        ts = datetime.fromisoformat(ts_str)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
    except (ValueError, AttributeError):
        return RiskCheck(False, f"Cannot parse quote timestamp '{quote_timestamp_utc}' — re-fetch before placing.")

    if age > max_age_seconds:
        return RiskCheck(
            False,
            f"Quote is {age:.0f}s old (limit {max_age_seconds}s) — market may have moved. "
            "Re-run review_option_order before placing.",
        )
    return RiskCheck(True, f"Quote fresh — {age:.0f}s old.")


def validate_option_entry(bid: float, ask: float, quote_timestamp_utc: str) -> RiskCheck:
    """
    Mandatory pre-order gate for all option entries. Combines:
      1. Liquidity check (bid/ask ratio, minimum ask floor)
      2. Quote freshness check (stale quote = race condition risk)
    Both must pass. Call this immediately before review_option_order.
    """
    liq = check_option_liquidity(bid, ask)
    if not liq.allowed:
        return liq
    return check_quote_freshness(quote_timestamp_utc)


def entry_mid_stop(ask: float, bid: float, stop_pct: float = 0.50) -> dict:
    """
    Anchor the hard stop to the mid price at entry, not the ask fill.

    Buying at the ask when the bid is lower means the position's liquidation
    value at fill is already below ask. The -50% stop must be measured from
    the mid so it reflects real value, not the inflated fill price.

    Returns a dict with stop_price, the effective loss-from-ask, and a note
    suitable for logging and the pre-trade worksheet.
    """
    mid = (ask + bid) / 2.0
    stop_price = mid * (1.0 - stop_pct)
    loss_from_ask = (stop_price - ask) / ask
    return {
        "entry_ask": round(ask, 4),
        "entry_bid": round(bid, 4),
        "entry_mid": round(mid, 4),
        "stop_price": round(stop_price, 4),
        "stop_pct_from_ask": round(loss_from_ask, 4),
        "note": (
            f"Stop ${stop_price:.4f} = mid ${mid:.4f} × (1 − {stop_pct:.0%}). "
            f"From ask fill that is {loss_from_ask:.1%} — not {-stop_pct:.0%}."
        ),
    }


def required_dte(pdt_trades_used: int, weekday: int = -1) -> int:
    """
    Return the minimum DTE required given current PDT usage and day of week.

    Normal minimum: 7 DTE (from config).
    PDT-pressure minimum: 14 DTE — applied when PDT day trades used ≥ 2 AND
    it is Thursday or Friday (weekday 3 or 4). This prevents being forced to
    hold a 7-DTE option over the weekend with no legal same-day exit, where a
    Monday gap can blow straight through the -50% stop without triggering it.

    weekday: 0=Monday … 4=Friday. Pass -1 (default) to use today's UTC weekday.
    """
    cfg = load_state()
    base_dte = cfg["instruments"].get("option_dte_min", 7)
    pressure_dte = cfg["instruments"].get("option_dte_min_pdt_pressure", 14)

    if weekday == -1:
        weekday = datetime.now(timezone.utc).weekday()

    is_late_week = weekday >= 3  # Thursday or Friday
    pdt_near_limit = pdt_trades_used >= 2

    if is_late_week and pdt_near_limit:
        return pressure_dte

    return base_dte


def _pdt_business_days_since(start_date_str: str) -> int:
    """Count business days elapsed from start_date_str (YYYY-MM-DD) through yesterday."""
    try:
        start = date.fromisoformat(start_date_str)
    except (ValueError, TypeError):
        return 999  # Unparseable — treat as expired
    today = datetime.now(timezone.utc).date()
    count = 0
    d = start
    while d < today:
        if d.weekday() < 5:  # Mon–Fri
            count += 1
        d += timedelta(days=1)
    return count


def increment_day_trade() -> None:
    """Record one day trade against the rolling 5-business-day PDT window."""
    cfg = load_state()
    pdt = cfg["pdt"]
    today_str = datetime.now(timezone.utc).date().isoformat()

    # Expire window if ≥5 business days have elapsed since it started
    if pdt.get("rolling_window_start"):
        if _pdt_business_days_since(pdt["rolling_window_start"]) >= 5:
            pdt["day_trades_used"] = 0
            pdt["rolling_window_start"] = None

    # Start window on first trade of the period
    if not pdt.get("rolling_window_start"):
        pdt["rolling_window_start"] = today_str

    pdt["day_trades_used"] += 1
    save_state(cfg)


def refresh_day_open(account_value: float) -> None:
    """
    Update day_open_value from the live account at session start.
    Clears daily_halted only when the calendar date has rolled (new trading day).
    Does NOT reset PDT counter — that uses its own rolling window.
    """
    cfg = load_state()
    today = datetime.now(timezone.utc).date().isoformat()
    if cfg["state"].get("day_open_date", "") != today:
        cfg["state"]["daily_halted"] = False  # only clear on a new calendar day
    cfg["state"]["day_open_value"] = account_value
    cfg["state"]["day_open_date"] = today
    save_state(cfg)


def _iso_week_monday(d: date) -> str:
    """Return the ISO-8601 date string of the Monday that starts d's week."""
    return (d - timedelta(days=d.weekday())).isoformat()


def refresh_week_open(account_value: float) -> None:
    """
    Anchor the weekly-loss baseline. On the first session of a new ISO week
    (Monday-started), reset week_open_value to the live account and clear the
    weekly halt. Mid-week sessions leave the Monday baseline untouched so the
    -max_weekly_loss_pct guard measures the full week's drawdown.
    """
    cfg = load_state()
    state = cfg["state"]
    this_monday = _iso_week_monday(datetime.now(timezone.utc).date())
    if state.get("week_start_date") != this_monday:
        state["week_start_date"] = this_monday
        state["week_open_value"] = account_value
        state["weekly_halted"] = False
        save_state(cfg)


def check_trade_allowed(account_value: float) -> RiskCheck:
    if _KILL_SWITCH:
        return RiskCheck(False, "TRADING_HALTED env var is set — kill switch active. Unset to resume.")

    cfg = load_state()
    state = cfg["state"]
    risk = cfg["risk"]

    if state["circuit_breaker_halted"]:
        return RiskCheck(False, "Circuit breaker tripped — 3 consecutive losses. Reset manually.")

    if state["daily_halted"]:
        return RiskCheck(False, "Daily drawdown limit hit. No more trades today.")

    day_open = state.get("day_open_value") or account_value
    drawdown = (day_open - account_value) / day_open
    if drawdown >= risk["max_daily_drawdown_pct"]:
        state["daily_halted"] = True
        save_state(cfg)
        return RiskCheck(False, f"Daily drawdown {drawdown:.1%} exceeded {risk['max_daily_drawdown_pct']:.0%} limit.")

    # Weekly loss guardrail (convex barbell): hard halt for the rest of the week.
    if state.get("weekly_halted"):
        return RiskCheck(False, "Weekly loss limit hit — halted for the week. Resets Monday.")
    max_weekly = risk.get("max_weekly_loss_pct")
    week_open = state.get("week_open_value") or account_value
    if max_weekly and week_open > 0:
        weekly_dd = (week_open - account_value) / week_open
        if weekly_dd >= max_weekly:
            state["weekly_halted"] = True
            save_state(cfg)
            return RiskCheck(False, f"Weekly drawdown {weekly_dd:.1%} exceeded {max_weekly:.0%} limit — halt for the week.")

    pdt = cfg["pdt"]
    if pdt["halt_if_pdt_risk"] and account_value < 25000:
        # Respect the rolling 5-business-day window: if the window has expired,
        # the recorded count is stale and cannot be used to block trading.
        trades_in_window = pdt["day_trades_used"]
        if pdt.get("rolling_window_start"):
            if _pdt_business_days_since(pdt["rolling_window_start"]) >= 5:
                trades_in_window = 0  # Window expired — count resets at next increment_day_trade()
        if trades_in_window >= 3:
            return RiskCheck(False, "PDT limit: 3 day trades used in the rolling 5-business-day window. Cannot day trade again without risking PDT flag.")

    max_dollars = position_size(account_value)
    return RiskCheck(True, "All checks passed.", max_dollars=max_dollars)


def record_trade_result(won: bool, account_value: float) -> None:
    cfg = load_state()
    state = cfg["state"]

    state["total_trades"] += 1
    if won:
        state["winning_trades"] += 1
        state["consecutive_losses"] = 0
    else:
        state["losing_trades"] += 1
        state["consecutive_losses"] += 1
        if state["consecutive_losses"] >= cfg["risk"]["circuit_breaker_consecutive_losses"]:
            state["circuit_breaker_halted"] = True

    now = datetime.now(timezone.utc).isoformat()
    if get_phase(account_value) == 2 and cfg["challenge"]["phase"] == 1:
        cfg["challenge"]["phase"] = 2
        cfg["challenge"]["completed_at"] = now

    ultimate = cfg["challenge"].get("ultimate_target", 5_000_000)
    if account_value >= ultimate and not cfg["challenge"].get("ultimate_completed_at"):
        cfg["challenge"]["ultimate_completed_at"] = now

    # Stamp any newly crossed milestones
    for m in cfg.get("milestones", {}).values():
        if m["reached_at"] is None and account_value >= m["target"]:
            m["reached_at"] = now

    save_state(cfg)


def reset_circuit_breaker() -> None:
    cfg = load_state()
    cfg["state"]["circuit_breaker_halted"] = False
    cfg["state"]["consecutive_losses"] = 0
    save_state(cfg)


def reset_daily(account_value: float) -> None:
    cfg = load_state()
    cfg["state"]["daily_halted"] = False
    cfg["state"]["day_open_value"] = account_value
    cfg["pdt"]["day_trades_used"] = 0
    save_state(cfg)


def log_trade(entry: dict) -> None:
    LOG_PATH.parent.mkdir(exist_ok=True)
    entry["logged_at"] = datetime.now(timezone.utc).isoformat()
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def win_rate() -> float:
    cfg = load_state()
    total = cfg["state"]["total_trades"]
    if total == 0:
        return 0.0
    return cfg["state"]["winning_trades"] / total


def challenge_progress(account_value: float) -> dict:
    cfg = load_state()
    start = cfg["challenge"]["start_balance"]
    phase1_target = cfg["challenge"]["phase1_target"]
    ultimate = cfg["challenge"].get("ultimate_target", 5_000_000)
    phase = get_phase(account_value)

    if phase == 1:
        pct = ((account_value - start) / (phase1_target - start)) * 100
        mode = "Phase 1: Challenge ($50 → $500)"
    else:
        pct = (account_value / ultimate) * 100
        mode = "Phase 2: Compounding ($500 → $5,000,000)"

    remaining = max(0.0, ultimate - account_value)

    # Next uncleared milestone
    next_milestone = next_milestone_label = None
    for m in cfg.get("milestones", {}).values():
        if m["reached_at"] is None:
            next_milestone = m["target"]
            next_milestone_label = m["label"]
            break

    # Milestones hit so far
    hit = [m["label"] for m in cfg.get("milestones", {}).values() if m["reached_at"]]

    return {
        "phase": phase,
        "mode": mode,
        "account_value": account_value,
        "ultimate_target": ultimate,
        "remaining_to_goal": remaining,
        "progress_pct": round(min(pct, 100.0), 2),
        "multiplier": round(account_value / start, 2),
        "total_trades": cfg["state"]["total_trades"],
        "win_rate": f"{win_rate():.0%}",
        "consecutive_losses": cfg["state"]["consecutive_losses"],
        "circuit_breaker_halted": cfg["state"]["circuit_breaker_halted"],
        "next_milestone": next_milestone,
        "next_milestone_label": next_milestone_label,
        "milestones_hit": hit,
        "strategy": "Momentum Compounder — same style all the way to $5M",
    }
