"""
The713Bozz — Momentum Compounder Trading System
$50 → $500 Challenge, then compound indefinitely.

Usage:
  python src/main.py --status                          # Show challenge progress
  python src/main.py --scan                            # Scan watchlist for setups
  python src/main.py --reset-circuit-breaker           # Reset after 3 losses
  python src/main.py --reset-daily <account_value>     # Reset daily limits
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.risk.risk_manager import (
    challenge_progress,
    check_trade_allowed,
    load_state,
    record_trade_result,
    refresh_day_open,
    reset_circuit_breaker,
    reset_daily,
)
from src.signals.learning import learning_report
from src.signals.regime import RegimeResult
from src.signals.premarket import (
    format_premarket_report,
    run_premarket_scan_standalone,
)
from src.signals.scanner import print_scan_report, run_scan_standalone
from src.strategy.watchlist import get_tiered_scan_symbols

SESSION_PATH = Path(__file__).parent.parent / "SESSION.md"


def cmd_status(account_value: float) -> None:
    progress = challenge_progress(account_value)
    print(f"\n{'='*54}")
    print(f"  The713Bozz Trading System")
    print(f"  {progress['mode']}")
    print(f"{'='*54}")
    print(f"  Account Value    : ${progress['account_value']:>14,.2f}")
    print(f"  Ultimate Goal    : ${progress['ultimate_target']:>14,.2f}")
    print(f"  Remaining        : ${progress['remaining_to_goal']:>14,.2f}")
    print(f"  Progress         : {progress['progress_pct']}%  ({progress['multiplier']}x from start)")
    if progress.get("next_milestone_label"):
        print(f"  Next Milestone   : {progress['next_milestone_label']}  (${progress['next_milestone']:,.0f})")
    if progress.get("milestones_hit"):
        print(f"  Milestones Hit   : {', '.join(progress['milestones_hit'])}")
    print(f"  Strategy         : {progress['strategy']}")
    print(f"  Total Trades     : {progress['total_trades']}")
    print(f"  Win Rate         : {progress['win_rate']}")
    print(f"  Consecutive Loss : {progress['consecutive_losses']}")
    print(f"  Circuit Breaker  : {'HALTED' if progress['circuit_breaker_halted'] else 'OK'}")
    print(f"{'='*54}\n")


def cmd_write_session(account_value: float, notes: str = "") -> None:
    """Write SESSION.md — snapshot of current state for session continuity."""
    cfg = load_state()
    progress = challenge_progress(account_value)
    state = cfg["state"]
    pdt = cfg["pdt"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    learn = learning_report()

    lines = [
        "# The713Bozz — Session State",
        f"_Last updated: {now}_",
        "",
        "## Challenge Progress",
        f"- **Account:** ${account_value:,.2f}",
        f"- **Phase:** {progress['phase']} ({progress['mode']})",
        f"- **Progress:** {progress['progress_pct']}% — {progress['multiplier']}x from $50 start",
        f"- **Next milestone:** {progress.get('next_milestone_label', 'n/a')}",
    ]
    if progress.get("milestones_hit"):
        lines.append(f"- **Milestones hit:** {', '.join(progress['milestones_hit'])}")

    lines += [
        "",
        "## Trade State",
        f"- Total trades: {state['total_trades']}",
        f"- Win rate: {progress['win_rate']}",
        f"- Consecutive losses: {state['consecutive_losses']} / 3 (circuit breaker at 3)",
        f"- Circuit breaker: {'HALTED ⛔' if state['circuit_breaker_halted'] else 'OK'}",
        f"- Daily halted: {'YES ⛔' if state['daily_halted'] else 'NO'}",
        f"- Day open value: ${state['day_open_value']:,.2f}",
        "",
        "## PDT Status",
        f"- Day trades used (rolling 5d): {pdt['day_trades_used']} / 3",
        f"- Rolling window start: {pdt['rolling_window_start'] or 'not set'}",
        "",
        "## Active Positions",
        "_(Update manually after each session — check Robinhood MCP at session start)_",
        "",
        "## Pending Tasks",
        "- [ ] Run morning scan at 9:30 AM ET",
        "- [ ] Check open positions vs stop levels",
    ]

    if notes:
        lines += ["", "## Session Notes", notes]

    lines += [
        "",
        "## Learning Report",
        "```",
        learn,
        "```",
        "",
        "## Read This At Session Start",
        "1. Check `config/challenge.json` for current state",
        "2. Pull live portfolio via `get_portfolio` MCP",
        "3. Check open positions vs stop levels",
        "4. If market open: run regime check → scan",
        "5. Never place an order without user confirmation",
    ]

    SESSION_PATH.write_text("\n".join(lines))
    print(f"SESSION.md written → {SESSION_PATH}")


def cmd_premarket_scan() -> None:
    """Run pre-market intelligence pass (Finnhub standalone path)."""
    from src.risk.risk_manager import load_state as _load_state
    cfg = _load_state()
    if not cfg.get("premarket", {}).get("enabled", True):
        print("[PREMARKET] Disabled in config.")
        return
    gap_pct = cfg.get("premarket", {}).get("gap_threshold_pct", 0.02)
    print(f"\nPre-market scan — gap threshold ≥{gap_pct:.0%}. Fetching quotes...\n")
    candidates = run_premarket_scan_standalone(gap_threshold=gap_pct)
    print(format_premarket_report(candidates, gap_threshold=gap_pct))


def cmd_scan(account_value: float, regime: RegimeResult | None = None) -> None:
    check = check_trade_allowed(account_value)
    if not check.allowed:
        print(f"\n[BLOCKED] {check.reason}\n")
        return

    cfg = load_state()
    max_contract = account_value * cfg["risk"]["max_option_contract_cost_pct"]

    print(f"\nMax position: ${check.max_dollars:.2f} | Max contract: ${max_contract:.2f}")
    print("Fetching Finnhub data...\n")

    candidates, detected_regime = run_scan_standalone(account_value)
    print_scan_report(candidates, detected_regime, account_value)


def cmd_build_order(args) -> None:
    from src.execution.order import (
        OrderRejected,
        build_equity_order,
        build_option_order,
        display_order,
        log_order_attempt,
    )

    account_value = args.account_value
    signals = [s.strip() for s in args.signals.split(",") if s.strip()] if args.signals else []

    if not args.symbol:
        print("[ERROR] --symbol required")
        return
    if not args.instrument:
        print("[ERROR] --instrument required")
        return

    try:
        if args.instrument == "equity":
            if args.price is None:
                print("[ERROR] --price required for equity orders")
                return
            if not args.quote_time:
                print("[ERROR] --quote-time required")
                return
            spec = build_equity_order(
                symbol=args.symbol,
                price=args.price,
                quote_timestamp_utc=args.quote_time,
                account_value=account_value,
                signals=signals,
                score=args.score,
                regime=args.regime,
                entry_note=args.entry_note,
                position_scale=args.position_scale,
            )
        elif args.instrument == "option":
            missing = []
            if args.bid is None:
                missing.append("--bid")
            if args.ask is None:
                missing.append("--ask")
            if not args.quote_time:
                missing.append("--quote-time")
            if not args.option_type:
                missing.append("--option-type")
            if args.strike is None:
                missing.append("--strike")
            if not args.expiry:
                missing.append("--expiry")
            if missing:
                print(f"[ERROR] Missing required args for option: {', '.join(missing)}")
                return
            spec = build_option_order(
                symbol=args.symbol,
                bid=args.bid,
                ask=args.ask,
                quote_timestamp_utc=args.quote_time,
                account_value=account_value,
                strike=args.strike,
                expiry_date=args.expiry,
                option_type=args.option_type,
                signals=signals,
                score=args.score,
                regime=args.regime,
                pdt_trades_used=args.pdt_trades_used,
                entry_note=args.entry_note,
                position_scale=args.position_scale,
            )
        else:
            print("[ERROR] --instrument must be 'equity' or 'option'")
            return

        print(display_order(spec))
        log_order_attempt(spec, status="pending")

    except OrderRejected as e:
        print(f"\n[REJECTED] {e}\n")
    except Exception as e:
        print(f"\n[ERROR] {e}\n")


def cmd_log_fill(args) -> None:
    from src.execution.order import log_fill

    missing = []
    if not args.order_id:
        missing.append("--order-id")
    if not args.symbol:
        missing.append("--symbol")
    if args.filled_price is None:
        missing.append("--filled-price")
    if args.quantity is None:
        missing.append("--quantity")
    if not args.instrument:
        missing.append("--instrument")
    if missing:
        print(f"[ERROR] Missing required args: {', '.join(missing)}")
        return

    log_fill(
        order_id=args.order_id,
        symbol=args.symbol,
        filled_price=args.filled_price,
        quantity=args.quantity,
        instrument=args.instrument,
        option_type=getattr(args, "option_type", None),
        strike=getattr(args, "strike", None),
        expiry_date=getattr(args, "expiry", None),
    )
    qty_unit = "contracts" if args.instrument == "option" else "shares"
    print(f"Fill logged: {args.quantity} {qty_unit} {args.symbol} @ ${args.filled_price}")


def cmd_record_result(args) -> None:
    if not args.won and not args.lost:
        print("[ERROR] Specify --won or --lost")
        return
    if args.won and args.lost:
        print("[ERROR] Cannot specify both --won and --lost")
        return

    record_trade_result(won=args.won, account_value=args.account_value)
    status = "WIN" if args.won else "LOSS"
    print(f"[{status}] Trade result recorded. Account value: ${args.account_value:.2f}")
    print(learning_report())


def cmd_risk_check(account_value: float) -> None:
    check = check_trade_allowed(account_value)
    status = "ALLOWED" if check.allowed else "BLOCKED"
    print(f"\n[{status}] {check.reason}")
    if check.allowed:
        print(f"Max position: ${check.max_dollars:.2f}\n")
    else:
        sys.exit(1)  # triggers block_on_failure in pre-order-guard hook


def cmd_pdt_status(account_value: float) -> None:
    cfg = load_state()
    pdt = cfg["pdt"]
    from src.risk.risk_manager import required_dte, _pdt_business_days_since
    import datetime as _dt

    trades_used = pdt["day_trades_used"]
    window_start = pdt.get("rolling_window_start")
    remaining = 3 - trades_used

    # Expire stale window
    if window_start and _pdt_business_days_since(window_start) >= 5:
        trades_used = 0
        remaining = 3
        window_start = None

    today_wd = _dt.datetime.now(_dt.timezone.utc).weekday()
    dte_floor = required_dte(trades_used, today_wd)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    print(f"\n--- PDT Status ---")
    print(f"  Day trades used : {trades_used}/3  (rolling 5-business-day window)")
    print(f"  Remaining today : {remaining} day trade(s)")
    print(f"  Window started  : {window_start or 'not started'}")
    print(f"  Min DTE now     : {dte_floor} days  (PDT pressure: {'YES' if dte_floor > 7 else 'no'})")

    if account_value >= 25000:
        print(f"  PDT rule        : EXEMPT (account ≥ $25,000)")
    elif remaining == 0:
        print(f"  ⛔ PDT LIMIT REACHED — swing trades only (hold overnight, no same-day close)")
    elif remaining == 1:
        print(f"  ⚠ 1 day trade remaining — use only for highest-conviction entry")
    else:
        print(f"  Swing strategy  : buy today, sell in {dte_floor}+ days → no PDT consumed")
    print()


def cmd_session_start(account_value):
    import datetime
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo
    now = datetime.datetime.now(ZoneInfo("America/New_York"))
    is_premarket = (now.weekday() < 5
                    and datetime.time(9, 0) <= now.time() < datetime.time(9, 30))
    is_open = (now.weekday() < 5
               and datetime.time(9, 30) <= now.time() <= datetime.time(16, 0))

    market_state = "pre-market" if is_premarket else ("market open" if is_open else "market closed")
    print(f"Session start: {now.strftime('%Y-%m-%d %H:%M')} ET ({market_state})")

    refresh_day_open(account_value)
    cmd_status(account_value)
    cmd_pdt_status(account_value)

    if is_premarket:
        print("\nPre-market window (9:00–9:30 AM) — running intelligence pass...\n")
        cmd_premarket_scan()
    elif is_open:
        print("\nMarket is open — running watchlist scan...\n")
        cmd_scan(account_value)
    else:
        print("Market is closed. Next scan at 9:30 AM ET.")


def main():
    parser = argparse.ArgumentParser(description="The713Bozz Trading System")
    parser.add_argument("--status", action="store_true", help="Show challenge status")
    parser.add_argument("--premarket-scan", action="store_true", help="Run pre-market intelligence pass (9:00–9:30 AM)")
    parser.add_argument("--scan", action="store_true", help="Scan watchlist for setups")
    parser.add_argument("--pdt-status", action="store_true", help="Show PDT day-trade window status")
    parser.add_argument("--risk-check", action="store_true", help="Check if trading is allowed")
    parser.add_argument("--reset-circuit-breaker", action="store_true")
    parser.add_argument("--reset-daily", metavar="ACCOUNT_VALUE", type=float)
    parser.add_argument("--learn", action="store_true", help="Show win-rate learning report from trade log")
    parser.add_argument("--write-session", action="store_true", help="Write SESSION.md state snapshot")
    parser.add_argument("--session-notes", type=str, default="", help="Notes to append to SESSION.md")
    parser.add_argument("--account-value", type=float, default=None, help="Current account value in USD")
    parser.add_argument("--mode", choices=["paper", "live"], default="paper",
                        help="Trading mode: paper (simulated) or live (real orders)")
    parser.add_argument("--account", type=str, default=None,
                        help="Robinhood account number (required for --mode live)")
    parser.add_argument("--session-start", action="store_true",
                        help="Session startup: print status and scan if market is open")

    # --build-order arguments
    parser.add_argument("--build-order", action="store_true", help="Build and gate-validate an order spec")
    parser.add_argument("--symbol", type=str, help="Ticker symbol")
    parser.add_argument("--price", type=float, help="Current price (equity)")
    parser.add_argument("--bid", type=float, help="Option bid price")
    parser.add_argument("--ask", type=float, help="Option ask price")
    parser.add_argument("--quote-time", type=str, help="Quote timestamp ISO 8601 UTC")
    parser.add_argument("--instrument", type=str, choices=["equity", "option"], help="equity or option")
    parser.add_argument("--option-type", type=str, choices=["call", "put"], help="call or put")
    parser.add_argument("--strike", type=float, help="Option strike price")
    parser.add_argument("--expiry", type=str, help="Option expiry date YYYY-MM-DD")
    parser.add_argument("--signals", type=str, default="", help="Comma-separated signal names")
    parser.add_argument("--score", type=int, default=0, help="Signal score 0-4")
    parser.add_argument("--regime", type=str, default="unknown", help="Market regime label")
    parser.add_argument("--pdt-trades-used", type=int, default=0, help="PDT day trades used this rolling 5-day window")
    parser.add_argument("--entry-note", type=str, default="", help="Entry context note")
    parser.add_argument("--position-scale", type=float, default=1.0, help="Position size scale: 1.0=full, 0.5=half (ranging regime)")

    # --log-fill arguments
    parser.add_argument("--log-fill", action="store_true", help="Log a confirmed fill to trades.jsonl")
    parser.add_argument("--order-id", type=str, help="Robinhood order ID")
    parser.add_argument("--filled-price", type=float, help="Actual fill price")
    parser.add_argument("--quantity", type=float, help="Shares or contracts filled")

    # --record-result arguments
    parser.add_argument("--record-result", action="store_true", help="Record win/loss and update challenge state")
    parser.add_argument("--won", action="store_true", help="Trade was a winner")
    parser.add_argument("--lost", action="store_true", help="Trade was a loser")

    args = parser.parse_args()
    if args.mode == "live" and not args.account:
        parser.error("--mode live requires --account <ACCOUNT_NUMBER>")
    if args.account_value is not None:
        account_value = args.account_value
    else:
        from src.risk.risk_manager import load_state as _load_state
        _st = _load_state()
        account_value = (_st.get("account", {}).get("current_account_value")
                         or _st.get("state", {}).get("day_open_value", 50.0))

    if args.status:
        cmd_status(account_value)
        print(learning_report())
    elif args.pdt_status:
        cmd_pdt_status(account_value)
    elif args.premarket_scan:
        cmd_premarket_scan()
    elif args.scan:
        cmd_scan(account_value)
    elif args.learn:
        print(learning_report())
    elif args.write_session:
        cmd_write_session(account_value, notes=args.session_notes)
    elif args.risk_check:
        cmd_risk_check(account_value)
    elif args.build_order:
        cmd_build_order(args)
    elif args.log_fill:
        cmd_log_fill(args)
    elif args.record_result:
        cmd_record_result(args)
    elif args.reset_circuit_breaker:
        reset_circuit_breaker()
        print("Circuit breaker reset. Consecutive losses set to 0.")
    elif args.reset_daily is not None:
        reset_daily(args.reset_daily)
        print(f"Daily limits reset. Day open value set to ${args.reset_daily:.2f}")
    elif args.session_start:
        cmd_session_start(account_value)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
