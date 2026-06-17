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

    if get_phase(account_value) == 2 and cfg["challenge"]["phase"] == 1:
        cfg["challenge"]["phase"] = 2
        cfg["challenge"]["completed_at"] = datetime.utcnow().isoformat()
        # Strategy continues unchanged — same risk, same style, indefinitely.

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
    target = cfg["challenge"]["phase1_target"]
    phase = get_phase(account_value)
    pct = ((account_value - start) / (target - start)) * 100 if phase == 1 else 100.0
    mode = "Challenge ($50→$500)" if phase == 1 else "Compounding — running until stopped"
    return {
        "phase": phase,
        "mode": mode,
        "account_value": account_value,
        "start": start,
        "target": target,
        "progress_pct": round(min(pct, 100.0), 1),
        "multiplier": round(account_value / start, 2),
        "total_trades": cfg["state"]["total_trades"],
        "win_rate": f"{win_rate():.0%}",
        "consecutive_losses": cfg["state"]["consecutive_losses"],
        "circuit_breaker_halted": cfg["state"]["circuit_breaker_halted"],
        "strategy": "Momentum Compounder (same style, no change after $500)",
    }
