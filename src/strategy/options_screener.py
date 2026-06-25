"""
Options screener — given pre-fetched option chain + quote data (from MCP),
filter and rank contracts that fit the account's risk parameters.

Usage (agent session):
    chain_data  = await mcp.get_option_chains(symbol="KLAC", expiration_dates=...)
    quote_data  = await mcp.get_option_quotes(instruments=[...])
    contracts   = screen_options("KLAC", chain_data, quote_data, "call", 49.97)

The MCP fetch stays in the agent layer. This module only processes the data.
"""

from __future__ import annotations

import json as _json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path as _Path
from typing import Optional


def _load_cfg() -> tuple[dict, dict, dict]:
    try:
        p = _Path(__file__).parent.parent.parent / "config" / "challenge.json"
        with open(p) as f:
            cfg = _json.load(f)
        return cfg.get("instruments", {}), cfg.get("risk", {}), cfg.get("signals", {})
    except Exception:
        return {}, {}, {}


@dataclass
class OptionContract:
    symbol: str
    option_type: str        # "call" | "put"
    strike: float
    expiry: str             # YYYY-MM-DD
    dte: int
    bid: float
    ask: float
    mid: float
    delta: Optional[float]
    open_interest: int
    volume: int
    cost_per_contract: float  # ask × 100
    bid_ask_ratio: float
    delta_per_dollar: Optional[float]  # delta / cost — higher = more leverage
    liquidity_ok: bool
    affordable: bool
    rejection_reason: str   # empty string if no rejection
    rank_score: float       # higher = better — used for sorting


def _days_to_expiry(expiry_str: str) -> int:
    try:
        exp = date.fromisoformat(expiry_str)
        today = datetime.now(timezone.utc).date()
        return max(0, (exp - today).days)
    except Exception:
        return 0


def screen_options(
    symbol: str,
    chains_data: dict,
    quotes_data: dict,
    direction: str,
    account_value: float,
    pdt_trades_used: int = 0,
    top_n: int = 3,
) -> list[OptionContract]:
    """
    Filter and rank option contracts from pre-fetched MCP data.

    chains_data : response from mcp__robinhood-trading__get_option_chains
    quotes_data : response from mcp__robinhood-trading__get_option_quotes
                  keyed by instrument URL or symbol — both formats accepted
    direction   : "call" or "put"
    top_n       : number of contracts to return (best first)

    Returns an empty list if no contracts pass the filters.
    The rejection_reason field on each contract explains any filter failure.
    """
    inst_cfg, risk_cfg, sig_cfg = _load_cfg()

    direction = direction.lower()
    if direction not in ("call", "put"):
        raise ValueError(f"direction must be 'call' or 'put', got '{direction}'")

    # Load thresholds from config
    dte_min      = inst_cfg.get("option_dte_min", 7)
    dte_min_pdt  = inst_cfg.get("option_dte_min_pdt_pressure", 14)
    dte_max      = inst_cfg.get("option_dte_max", 45)
    delta_min    = inst_cfg.get("option_delta_min", 0.20)
    delta_max    = inst_cfg.get("option_delta_max", 0.45)
    max_cost_pct = risk_cfg.get("max_option_contract_cost_pct", 0.30)
    min_ask      = risk_cfg.get("min_option_ask", 0.10)
    min_ba_ratio = risk_cfg.get("min_bid_ask_ratio", 0.60)
    min_oi       = 50   # minimum open interest for liquidity
    min_vol      = 10   # minimum daily volume

    max_cost = account_value * max_cost_pct  # max dollars per contract

    # Apply PDT pressure DTE floor
    today_weekday = datetime.now(timezone.utc).weekday()
    is_late_week = today_weekday >= 3
    effective_dte_min = dte_min_pdt if (is_late_week and pdt_trades_used >= 2) else dte_min

    # Parse chain data — handle Robinhood MCP response shape
    expirations: list[str] = []
    strikes_by_expiry: dict[str, list[float]] = {}
    instruments_by_key: dict[str, dict] = {}

    raw_chains = chains_data.get("data", chains_data) if isinstance(chains_data, dict) else {}
    results_list = raw_chains.get("results", [raw_chains]) if isinstance(raw_chains, dict) else []

    for chain in results_list:
        exp_dates = chain.get("expiration_dates", [])
        expirations.extend(exp_dates)

    # Parse quotes — build lookup by instrument URL or symbol+strike+expiry key
    raw_quotes = quotes_data.get("data", quotes_data) if isinstance(quotes_data, dict) else {}
    quote_results = raw_quotes.get("results", []) if isinstance(raw_quotes, dict) else []

    quote_lookup: dict[str, dict] = {}
    for q in quote_results:
        url = q.get("instrument") or q.get("url") or ""
        key = _option_key(q.get("symbol", symbol), q.get("type", ""), q.get("strike_price", ""), q.get("expiration_date", ""))
        if url:
            quote_lookup[url] = q
        if key:
            quote_lookup[key] = q
        # Also index by instrument_id if present
        inst_id = q.get("instrument_id") or q.get("id") or ""
        if inst_id:
            quote_lookup[inst_id] = q

    contracts: list[OptionContract] = []

    for q in quote_results:
        opt_type = (q.get("type") or q.get("option_type") or "").lower()
        if opt_type not in ("call", "put") or opt_type != direction:
            continue

        strike_raw = q.get("strike_price") or q.get("strike") or 0
        expiry = q.get("expiration_date") or q.get("expiry") or ""
        try:
            strike = float(strike_raw)
        except (TypeError, ValueError):
            continue

        dte = _days_to_expiry(expiry)
        bid = _safe_float(q.get("bid_price") or q.get("bid"))
        ask = _safe_float(q.get("ask_price") or q.get("ask"))
        mid = (bid + ask) / 2 if ask > 0 else 0.0
        delta_raw = q.get("delta")
        delta = _safe_float(delta_raw) if delta_raw is not None else None
        oi = int(q.get("open_interest") or 0)
        vol = int(q.get("volume") or 0)

        cost = ask * 100  # cost per contract
        ba_ratio = (bid / ask) if ask > 0 else 0.0

        rejection = ""

        # DTE filter
        if dte < effective_dte_min:
            rejection = f"DTE {dte} < min {effective_dte_min}"
        elif dte > dte_max:
            rejection = f"DTE {dte} > max {dte_max}"

        # Ask floor
        if not rejection and ask < min_ask:
            rejection = f"Ask ${ask:.2f} < floor ${min_ask:.2f} (lethal spread)"

        # Affordability
        if not rejection and cost > max_cost:
            rejection = f"Cost ${cost:.2f} > max ${max_cost:.2f} ({max_cost_pct:.0%} of account)"

        # Bid/ask spread
        if not rejection and ba_ratio < min_ba_ratio:
            rejection = f"Spread {ba_ratio:.0%} < min {min_ba_ratio:.0%} (fills at immediate loss)"

        # Delta filter (skip if delta not available — don't reject)
        if not rejection and delta is not None:
            abs_delta = abs(delta)
            if abs_delta < delta_min:
                rejection = f"Delta {abs_delta:.2f} < min {delta_min:.2f} (lottery ticket)"
            elif abs_delta > delta_max:
                rejection = f"Delta {abs_delta:.2f} > max {delta_max:.2f} (too expensive)"

        # Liquidity
        if not rejection and oi < min_oi:
            rejection = f"Open interest {oi} < min {min_oi}"
        if not rejection and vol < min_vol:
            rejection = f"Volume {vol} < min {min_vol}"

        liquidity_ok = not rejection or "Delta" in rejection  # delta rejection ≠ illiquid
        affordable = cost <= max_cost

        abs_delta = abs(delta) if delta is not None else None
        dpd = (abs_delta / cost) if (abs_delta and cost > 0) else None

        # Rank: prioritize delta-per-dollar, penalize wide spreads
        rank = 0.0
        if not rejection:
            dpd_score = (dpd * 100) if dpd else 0.0
            spread_penalty = (1 - ba_ratio) * 20
            dte_score = min(dte / 14, 1.0) * 10  # prefer 14+ DTE up to a cap
            rank = dpd_score - spread_penalty + dte_score

        contracts.append(OptionContract(
            symbol=symbol,
            option_type=direction,
            strike=strike,
            expiry=expiry,
            dte=dte,
            bid=bid,
            ask=ask,
            mid=mid,
            delta=delta,
            open_interest=oi,
            volume=vol,
            cost_per_contract=cost,
            bid_ask_ratio=ba_ratio,
            delta_per_dollar=dpd,
            liquidity_ok=liquidity_ok,
            affordable=affordable,
            rejection_reason=rejection,
            rank_score=rank,
        ))

    # Return top_n qualifying contracts, best first
    qualified = [c for c in contracts if not c.rejection_reason]
    qualified.sort(key=lambda c: c.rank_score, reverse=True)
    return qualified[:top_n]


def format_screener_report(
    contracts: list[OptionContract],
    account_value: float,
    symbol: str,
    direction: str,
) -> str:
    """Human-readable report of screened option contracts."""
    lines = [f"\n--- Options Screener: {symbol} {direction.upper()} ---"]
    inst_cfg, risk_cfg, _ = _load_cfg()
    max_cost = account_value * risk_cfg.get("max_option_contract_cost_pct", 0.30)

    if not contracts:
        lines.append(f"  No contracts pass filters (max cost ${max_cost:.2f}/contract).")
        lines.append(f"  Account ${account_value:.2f} is too small for {symbol} options at this level.")
        lines.append(f"  Consider: fractional equity, or wait until account grows to afford contracts.")
        return "\n".join(lines)

    lines.append(f"  Max affordable: ${max_cost:.2f}/contract | Showing top {len(contracts)}")
    lines.append(f"  {'Strike':>8}  {'Exp':>12}  {'DTE':>4}  {'Ask':>6}  {'Cost':>7}  {'Delta':>6}  {'D/$':>6}  {'B/A':>5}")
    lines.append("  " + "-" * 70)
    for c in contracts:
        delta_str = f"{c.delta:.2f}" if c.delta is not None else "  N/A"
        dpd_str = f"{c.delta_per_dollar:.4f}" if c.delta_per_dollar else "  N/A"
        lines.append(
            f"  ${c.strike:>7.2f}  {c.expiry:>12}  {c.dte:>4}  "
            f"${c.ask:>5.2f}  ${c.cost_per_contract:>6.2f}  "
            f"{delta_str:>6}  {dpd_str:>6}  {c.bid_ask_ratio:>4.0%}"
        )
        lines.append(f"           Entry mid: ${c.mid:.2f} | Stop: ${c.mid * 0.50:.2f} | Target: ${c.mid * 2.5:.2f}")
    return "\n".join(lines)


def _safe_float(val) -> float:
    try:
        return float(val) if val is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _option_key(symbol: str, opt_type: str, strike: str, expiry: str) -> str:
    return f"{symbol}_{opt_type}_{strike}_{expiry}".upper()
