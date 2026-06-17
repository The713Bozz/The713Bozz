import json
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "challenge.json"
LOG_PATH = Path(__file__).parent.parent.parent / "logs" / "trades.jsonl"


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


def save_state(state: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(state, f, indent=2)


def get_phase(account_value: float) -> int:
    cfg = load_state()
    return 1 if account_value < cfg["challenge"]["phase1_target"] else 2


def max_risk_pct(account_value: float) -> float:
    # Same aggressive strategy in both phases — compound indefinitely until user stops.
    return 0.20


def position_size(account_value: float) -> float:
    return account_value * max_risk_pct(account_value)


def option_contracts(account_value: float, option_price: float) -> int:
    dollars = position_size(account_value)
    contracts = int(dollars / (option_price * 100))
    return max(1, min(contracts, 5))


def check_trade_allowed(account_value: float) -> RiskCheck:
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

    pdt = cfg["pdt"]
    if pdt["halt_if_pdt_risk"] and account_value < 25000 and pdt["day_trades_used"] >= 3:
        return RiskCheck(False, "PDT limit: 3 day trades used this week. Cannot day trade again without risking PDT flag.")

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

    now = datetime.utcnow().isoformat()
    if get_phase(account_value) == 2 and cfg["challenge"]["phase"] == 1:
        cfg["challenge"]["phase"] = 2
        cfg["challenge"]["completed_at"] = now

    ultimate = cfg["challenge"].get("ultimate_target", 5_000_000)
    if account_value >= ultimate and not cfg["challenge"].get("ultimate_completed_at"):
        cfg["challenge"]["ultimate_completed_at"] = now

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
    entry["logged_at"] = datetime.utcnow().isoformat()
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
        "strategy": "Momentum Compounder — same style all the way to $5M",
    }
