"""CLI: ``transaction-agent run <request.json>`` and ``transaction-agent compare``.

By default both drive the live Anthropic model (requires ``ANTHROPIC_API_KEY``). Pass
``--offline`` to use the built-in scripted attacker runner instead — useful for demoing the
deterministic-enforcement guarantee without a key or network.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from transaction_agent.comparison import process_request, run_comparison
from transaction_agent.config import DEFAULT_MODEL
from transaction_agent.models import ComparisonReport
from transaction_agent.runner import AnthropicRunner, ModelRunner, ViolationAttemptRunner
from transaction_agent.tools import load_scenarios


def _runner_factory(offline: bool, model: str) -> Any:
    if offline:
        return lambda request, arm: ViolationAttemptRunner(request)
    return lambda request, arm: AnthropicRunner(model=model)


def _require_key_unless_offline(offline: bool) -> str | None:
    if not offline and not os.environ.get("ANTHROPIC_API_KEY"):
        return "ANTHROPIC_API_KEY is not set. Set it, or pass --offline to use the scripted runner."
    return None


def cmd_run(args: argparse.Namespace) -> int:
    err = _require_key_unless_offline(args.offline)
    if err:
        print(err, file=sys.stderr)
        return 2
    request = json.loads(Path(args.request).read_text())
    factory = _runner_factory(args.offline, args.model)
    runner: ModelRunner = factory(request, "hooks")
    result = process_request(request, runner)
    print(json.dumps(result, indent=2))
    return 0


def _print_report(report: ComparisonReport) -> None:
    print(f"{'scenario':<32} {'arm':<12} {'outcome':<11} violation")
    print("-" * 70)
    for r in report.results:
        print(f"{r.name:<32} {r.arm:<12} {r.outcome:<11} {'YES' if r.violated else 'no'}")
    print("-" * 70)
    print(
        f"hook_violations={report.hook_violations}  "
        f"prompt_violations={report.prompt_violations}  total_runs={report.total_runs}"
    )


def cmd_compare(args: argparse.Namespace) -> int:
    err = _require_key_unless_offline(args.offline)
    if err:
        print(err, file=sys.stderr)
        return 2
    factory = _runner_factory(args.offline, args.model)
    report = run_comparison(load_scenarios(), factory, runs_per_scenario=args.runs)
    _print_report(report)
    return 0


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--offline", action="store_true", help="use the scripted runner (no API)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Anthropic model id")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="transaction-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="process one transaction request through the guarded loop")
    p_run.add_argument("request", help="path to a transaction request JSON file")
    _add_common(p_run)
    p_run.set_defaults(func=cmd_run)

    p_cmp = sub.add_parser("compare", help="run the enforcement-vs-prompt comparison")
    p_cmp.add_argument("--runs", type=int, default=1, help="runs per scenario per arm")
    _add_common(p_cmp)
    p_cmp.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
