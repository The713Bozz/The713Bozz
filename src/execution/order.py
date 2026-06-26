"""
Order execution module for The713Bozz trading system.

Flow per trade:
  1. build_equity_order() or build_option_order() — runs all gates, returns OrderSpec
  2. Agent calls review_equity_order or review_option_order (MCP) with spec fields
  3. Agent presents review alerts to user
  4. User explicitly confirms "yes"
  5. Agent calls place_equity_order or place_option_order (MCP)
  6. Agent calls log_fill() with confirmed order ID and fill price

build_*_order() NEVER places orders. Placing always requires user confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from src.risk.risk_manager import (
    check_quote_freshness,
    check_trade_allowed,
    entry_mid_stop,
    get_agentic_account,
    load_state,
    log_trade,
    position_size,
    required_dte,
    validate_option_entry,
)
from src.signals.catalyst import check_earnings_risk


class OrderRejected(Exception):
    """Raised when any pre-order gate fails. Message is human-readable."""


@dataclass
class OrderSpec:
    """
    Fully gate-validated order ready for review_*_order MCP call.
    All prices in dollars. quantity = fractional shares (equity) or contracts (option).
    """
    account_number: str
    symbol: str
    instrument: str           # "equity" or "option"
    side: str = "buy"
    order_type: str = "limit"
    quantity: float = 0.0
    limit_price: float = 0.0
    total_cost: float = 0.0
    max_position_dollars: float = 0.0

    # Option-only
    option_type: Optional[str] = None   # "call" or "put"
    strike: Optional[float] = None
    expiry_date: Optional[str] = None   # "YYYY-MM-DD"
    entry_mid: Optional[float] = None
    stop_note: str = ""

    # Risk levels
    stop_price: float = 0.0
    target_price: float = 0.0
    stop_pct: float = 0.0
    target_pct: float = 0.0

    # Context
    signals: list[str] = field(default_factory=list)
    signal_score: int = 0
    regime: str = ""
    entry_note: str = ""


def build_equity_order(
    symbol: str,
    price: float,
    quote_timestamp_utc: str,
    account_value: float,
    signals: list[str],
    score: int,
    regime: str,
    entry_note: str = "",
    position_scale: float = 1.0,
) -> OrderSpec:
    """
    Build a validated equity buy order spec.
    Raises OrderRejected if any gate fails.
    Gates: kill switch, circuit breaker, daily drawdown, PDT limit, quote freshness, signal score.
    position_scale: 1.0 = full, 0.5 = half (ranging regime).
    """
    account_number = get_agentic_account()

    check = check_trade_allowed(account_value)
    if not check.allowed:
        raise OrderRejected(f"Trade blocked: {check.reason}")

    earnings_safe, earnings_reason = check_earnings_risk(symbol)
    if not earnings_safe:
        raise OrderRejected(f"[EARNINGS GATE] {earnings_reason}")

    fresh = check_quote_freshness(quote_timestamp_utc)
    if not fresh.allowed:
        raise OrderRejected(f"Stale quote: {fresh.reason}")

    if score < 3:
        raise OrderRejected(f"Signal score {score}/4 below minimum 3 — setup not ready.")

    max_dollars = position_size(account_value) * max(0.0, min(1.0, position_scale))
    quantity = round(max_dollars / price, 4)
    quantity = max(0.001, quantity)
    total_cost = round(quantity * price, 2)

    # Equity stops: -8% hard stop / +25% target → 3.1x R:R
    stop_price = round(price * 0.92, 4)
    target_price = round(price * 1.25, 4)

    return OrderSpec(
        account_number=account_number,
        symbol=symbol,
        instrument="equity",
        side="buy",
        order_type="limit",
        quantity=quantity,
        limit_price=round(price, 4),
        total_cost=total_cost,
        max_position_dollars=round(max_dollars, 2),
        stop_price=stop_price,
        target_price=target_price,
        stop_pct=0.08,
        target_pct=0.25,
        signals=signals,
        signal_score=score,
        regime=regime,
        entry_note=entry_note,
    )


def build_option_order(
    symbol: str,
    bid: float,
    ask: float,
    quote_timestamp_utc: str,
    account_value: float,
    strike: float,
    expiry_date: str,
    option_type: str,
    signals: list[str],
    score: int,
    regime: str,
    pdt_trades_used: int = 0,
    entry_note: str = "",
    position_scale: float = 1.0,
) -> OrderSpec:
    """
    Build a validated option buy order spec.
    Raises OrderRejected if any gate fails.
    Gates: kill switch, circuit breaker, daily drawdown, PDT limit,
           option liquidity, quote freshness, signal score, DTE minimum.
    Stop anchored to mid price (not ask) to survive the spread at fill.
    position_scale: 1.0 = full, 0.5 = half (ranging regime).
    """
    account_number = get_agentic_account()

    check = check_trade_allowed(account_value)
    if not check.allowed:
        raise OrderRejected(f"Trade blocked: {check.reason}")

    earnings_safe, earnings_reason = check_earnings_risk(symbol)
    if not earnings_safe:
        raise OrderRejected(f"[EARNINGS GATE] {earnings_reason}")

    # Liquidity + freshness (combined gate)
    val = validate_option_entry(bid, ask, quote_timestamp_utc)
    if not val.allowed:
        raise OrderRejected(f"Option entry rejected: {val.reason}")

    if score < 3:
        raise OrderRejected(f"Signal score {score}/4 below minimum 3 — setup not ready.")

    try:
        exp = date.fromisoformat(expiry_date)
        dte = (exp - date.today()).days
    except (ValueError, TypeError):
        raise OrderRejected(f"Cannot parse expiry_date '{expiry_date}' — use YYYY-MM-DD.")

    min_dte = required_dte(pdt_trades_used)
    if dte < min_dte:
        raise OrderRejected(
            f"DTE {dte} < required {min_dte}. "
            f"Select a contract expiring at least {min_dte} days from today."
        )

    max_dollars = position_size(account_value) * max(0.0, min(1.0, position_scale))
    cfg_state = load_state()
    max_contracts_cap = cfg_state["instruments"].get("option_max_contracts", 5)
    single_cost = ask * 100
    max_per_contract = account_value * cfg_state["risk"].get("max_option_contract_cost_pct", 0.30)
    if single_cost > max_per_contract:
        raise OrderRejected(
            f"Contract cost ${single_cost:.2f} exceeds per-contract limit "
            f"${max_per_contract:.2f} ({cfg_state['risk'].get('max_option_contract_cost_pct', 0.30):.0%} of ${account_value:.2f})."
        )
    contracts = max(1, min(int(max_dollars / single_cost), max_contracts_cap))
    total_cost = round(contracts * single_cost, 2)

    # Stop anchored to mid — buying at ask with bid below means you are immediately
    # down (ask - bid)/ask on paper. Anchor stop to mid so it reflects real value.
    stop_data = entry_mid_stop(ask, bid, stop_pct=0.50)
    mid = stop_data["entry_mid"]
    stop_price = stop_data["stop_price"]
    target_price = round(mid * 2.0, 4)  # 100% gain from mid = 2x target

    return OrderSpec(
        account_number=account_number,
        symbol=symbol,
        instrument="option",
        side="buy",
        order_type="limit",
        quantity=float(contracts),
        limit_price=round(ask, 4),
        total_cost=total_cost,
        max_position_dollars=round(max_dollars, 2),
        option_type=option_type,
        strike=strike,
        expiry_date=expiry_date,
        entry_mid=mid,
        stop_note=stop_data["note"],
        stop_price=stop_price,
        target_price=target_price,
        stop_pct=0.50,
        target_pct=1.00,
        signals=signals,
        signal_score=score,
        regime=regime,
        entry_note=entry_note,
    )


def display_order(spec: OrderSpec) -> str:
    """Return a formatted order summary for user confirmation before MCP review call."""
    qty_unit = "contracts" if spec.instrument == "option" else "shares"
    lines = [
        "",
        "=" * 62,
        f"  ORDER SPEC — {spec.symbol} {spec.instrument.upper()}",
        "=" * 62,
        f"  Account      : {spec.account_number}",
        f"  Side         : {spec.side.upper()}  ({spec.order_type})",
        f"  Quantity     : {spec.quantity} {qty_unit}",
        f"  Limit Price  : ${spec.limit_price:.4f}",
        f"  Total Cost   : ${spec.total_cost:.2f}  (max ${spec.max_position_dollars:.2f})",
    ]

    if spec.instrument == "option":
        lines.append(
            f"  Contract     : {(spec.option_type or '').upper()} "
            f"${spec.strike:.2f} exp {spec.expiry_date}"
        )
        if spec.entry_mid is not None:
            lines.append(f"  Entry Mid    : ${spec.entry_mid:.4f}")

    stop_suffix = "  [anchored to mid]" if spec.instrument == "option" else ""
    lines.append(f"  Stop         : ${spec.stop_price:.4f}  (-{spec.stop_pct:.0%}){stop_suffix}")
    lines.append(f"  Target       : ${spec.target_price:.4f}  (+{spec.target_pct:.0%})")
    lines.append(f"  Score        : {spec.signal_score}/4  [{', '.join(spec.signals)}]")
    lines.append(f"  Regime       : {spec.regime}")

    if spec.entry_note:
        lines.append(f"  Note         : {spec.entry_note}")
    if spec.instrument == "option" and spec.stop_note:
        lines.append(f"  Stop detail  : {spec.stop_note}")

    lines += [
        "",
        "  CONFIRMATION REQUIRED — reply 'yes' to proceed to MCP review.",
        "=" * 62,
        "",
    ]
    return "\n".join(lines)


def log_order_attempt(
    spec: OrderSpec,
    status: str,
    order_id: Optional[str] = None,
) -> None:
    """Write a pre-fill order attempt record to logs/trades.jsonl."""
    log_trade({
        "event": "order_attempt",
        "status": status,
        "order_id": order_id,
        "account_number": spec.account_number,
        "symbol": spec.symbol,
        "instrument": spec.instrument,
        "side": spec.side,
        "quantity": spec.quantity,
        "limit_price": spec.limit_price,
        "total_cost": spec.total_cost,
        "option_type": spec.option_type,
        "strike": spec.strike,
        "expiry_date": spec.expiry_date,
        "stop_price": spec.stop_price,
        "target_price": spec.target_price,
        "signals": spec.signals,
        "signal_score": spec.signal_score,
        "regime": spec.regime,
        "entry_note": spec.entry_note,
    })


def log_fill(
    order_id: str,
    symbol: str,
    filled_price: float,
    quantity: float,
    instrument: str,
    option_type: Optional[str] = None,
    strike: Optional[float] = None,
    expiry_date: Optional[str] = None,
    stop_price: Optional[float] = None,
    target_price: Optional[float] = None,
    won: Optional[bool] = None,
    signals: Optional[list] = None,
) -> None:
    """Write a confirmed fill record to logs/trades.jsonl."""
    multiplier = 100 if instrument == "option" else 1
    log_trade({
        "event": "fill",
        "order_id": order_id,
        "symbol": symbol,
        "instrument": instrument,
        "option_type": option_type,
        "strike": strike,
        "expiry_date": expiry_date,
        "filled_price": filled_price,
        "quantity": quantity,
        "total_cost": round(filled_price * quantity * multiplier, 2),
        "stop_price": stop_price,
        "target_price": target_price,
        "won": won,
        "signals": signals or [],
    })
