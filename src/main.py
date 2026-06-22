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
from datetime import datetime, timezone
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
from src.signals.scanner import print_scan_report, run_scan_standalone
from src.strategy.watchlist import get_scan_list
from src.agents.hermes import HermesTask, describe_tasks, is_available, run_task

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
        "- [ ] Wire in FMP congressional trades API (waiting on Hermes)",
        "- [ ] Wire in Quiver Quant WSB sentiment API (waiting on Hermes)",
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


def cmd_scan(account_value: float, regime: RegimeResult | None = None) -> None:
    check = check_trade_allowed(account_value)
    if not check.allowed:
        print(f"\n[BLOCKED] {check.reason}\n")
        return

    cfg = load_state()
    max_contract = account_value * cfg["risk"]["max_option_contract_cost_pct"]
    symbols = get_scan_list(account_value)

    print(f"\nScanning {len(symbols)} symbols | Max position: ${check.max_dollars:.2f} | Max contract: ${max_contract:.2f}")
    print("Fetching Finnhub data...\n")

    candidates, detected_regime = run_scan_standalone(account_value)
    print_scan_report(candidates, detected_regime, account_value)


def cmd_risk_check(account_value: float) -> None:
    check = check_trade_allowed(account_value)
    status = "ALLOWED" if check.allowed else "BLOCKED"
    print(f"\n[{status}] {check.reason}")
    if check.allowed:
        print(f"Max position: ${check.max_dollars:.2f}\n")


def cmd_hermes(task_type: str, prompt: str, context_pairs: list[str]) -> None:
    """Dispatch a pre-approved task to the Hermes agent."""
    print(f"\n[HERMES] Checking availability...")
    if not is_available():
        print("[HERMES] Unavailable — API unreachable or key not set.")
        print("  Set NOUS_BASE_URL in .env if the inference endpoint differs from default.")
        print("  Default: https://inference.nousresearch.com/v1")
        return

    ctx: dict = {}
    for pair in context_pairs:
        if "=" in pair:
            k, _, v = pair.partition("=")
            ctx[k.strip()] = v.strip()

    task = HermesTask(task_type=task_type, prompt=prompt, context=ctx)
    print(f"[HERMES] Running task: {task_type}")
    result = run_task(task)

    if result.ok:
        print(f"\n[HERMES OK] model={result.model} tokens={result.tokens_used}")
        print("-" * 54)
        print(result.content)
        print("-" * 54 + "\n")
    else:
        print(f"\n[HERMES ERROR] {result.content}\n")


def main():
    parser = argparse.ArgumentParser(description="The713Bozz Trading System")
    parser.add_argument("--status", action="store_true", help="Show challenge status")
    parser.add_argument("--scan", action="store_true", help="Scan watchlist for setups")
    parser.add_argument("--risk-check", action="store_true", help="Check if trading is allowed")
    parser.add_argument("--reset-circuit-breaker", action="store_true")
    parser.add_argument("--reset-daily", metavar="ACCOUNT_VALUE", type=float)
    parser.add_argument("--learn", action="store_true", help="Show win-rate learning report from trade log")
    parser.add_argument("--write-session", action="store_true", help="Write SESSION.md state snapshot")
    parser.add_argument("--session-notes", type=str, default="", help="Notes to append to SESSION.md")
    parser.add_argument("--account-value", type=float, default=50.0, help="Current account value in USD")
    parser.add_argument("--hermes", metavar="TASK_TYPE", help="Dispatch a task to Hermes agent (requires user approval)")
    parser.add_argument("--hermes-prompt", type=str, default="", help="Prompt for the Hermes task")
    parser.add_argument("--hermes-context", nargs="*", default=[], metavar="KEY=VALUE", help="Context key=value pairs for Hermes")
    parser.add_argument("--hermes-tasks", action="store_true", help="List available Hermes task types")

    args = parser.parse_args()
    account_value = args.account_value

    if args.status:
        cmd_status(account_value)
        print(learning_report())
    elif args.scan:
        cmd_scan(account_value)
    elif args.learn:
        print(learning_report())
    elif args.write_session:
        cmd_write_session(account_value, notes=args.session_notes)
    elif args.risk_check:
        cmd_risk_check(account_value)
    elif args.reset_circuit_breaker:
        reset_circuit_breaker()
        print("Circuit breaker reset. Consecutive losses set to 0.")
    elif args.reset_daily is not None:
        reset_daily(args.reset_daily)
        print(f"Daily limits reset. Day open value set to ${args.reset_daily:.2f}")
    elif args.hermes_tasks:
        print(describe_tasks())
    elif args.hermes:
        if not args.hermes_prompt:
            print("Error: --hermes-prompt is required with --hermes")
            parser.print_usage()
        else:
            cmd_hermes(args.hermes, args.hermes_prompt, args.hermes_context)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
