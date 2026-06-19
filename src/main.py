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
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.risk.risk_manager import (
    challenge_progress,
    check_trade_allowed,
    load_state,
    reset_circuit_breaker,
    reset_daily,
)
from src.signals.learning import learning_report
from src.signals.regime import RegimeResult
from src.strategy.watchlist import get_scan_list


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
    print(f"  Strategy         : {progress['strategy']}")
    print(f"  Total Trades     : {progress['total_trades']}")
    print(f"  Win Rate         : {progress['win_rate']}")
    print(f"  Consecutive Loss : {progress['consecutive_losses']}")
    print(f"  Circuit Breaker  : {'HALTED' if progress['circuit_breaker_halted'] else 'OK'}")
    print(f"{'='*54}\n")


def cmd_scan(account_value: float, regime: RegimeResult | None = None) -> None:
    check = check_trade_allowed(account_value)
    if not check.allowed:
        print(f"\n[BLOCKED] {check.reason}\n")
        return

    if regime is not None:
        tag = "OK" if regime.trade_allowed else "HALT"
        print(f"\n[REGIME:{tag}] {regime.regime.upper()} — {regime.detail}")
        if not regime.trade_allowed:
            print("No new entries until regime shifts. Monitoring existing positions only.\n")
            return

    symbols = get_scan_list(account_value)
    print(f"\nScanning {len(symbols)} symbols for momentum setups...")
    print(f"Max position size: ${check.max_dollars:.2f}")
    if account_value < 150:
        cfg = load_state()
        max_contract = account_value * cfg["risk"]["max_option_contract_cost_pct"]
        print(f"Max contract cost: ${max_contract:.2f}  (${max_contract/100:.2f}/share options)")
    print("\nSymbols (Tier 2 first — cheap options priority):", ", ".join(symbols))
    print("\nLive scan runs via agent MCP calls — invoke from Claude Code session.\n")


def cmd_risk_check(account_value: float) -> None:
    check = check_trade_allowed(account_value)
    status = "ALLOWED" if check.allowed else "BLOCKED"
    print(f"\n[{status}] {check.reason}")
    if check.allowed:
        print(f"Max position: ${check.max_dollars:.2f}\n")


def main():
    parser = argparse.ArgumentParser(description="The713Bozz Trading System")
    parser.add_argument("--status", action="store_true", help="Show challenge status")
    parser.add_argument("--scan", action="store_true", help="Scan watchlist for setups")
    parser.add_argument("--risk-check", action="store_true", help="Check if trading is allowed")
    parser.add_argument("--reset-circuit-breaker", action="store_true")
    parser.add_argument("--reset-daily", metavar="ACCOUNT_VALUE", type=float)
    parser.add_argument("--learn", action="store_true", help="Show win-rate learning report from trade log")
    parser.add_argument("--account-value", type=float, default=50.0, help="Current account value in USD")

    args = parser.parse_args()
    account_value = args.account_value

    if args.status:
        cmd_status(account_value)
        print(learning_report())
    elif args.scan:
        cmd_scan(account_value)
    elif args.learn:
        print(learning_report())
    elif args.risk_check:
        cmd_risk_check(account_value)
    elif args.reset_circuit_breaker:
        reset_circuit_breaker()
        print("Circuit breaker reset. Consecutive losses set to 0.")
    elif args.reset_daily is not None:
        reset_daily(args.reset_daily)
        print(f"Daily limits reset. Day open value set to ${args.reset_daily:.2f}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
