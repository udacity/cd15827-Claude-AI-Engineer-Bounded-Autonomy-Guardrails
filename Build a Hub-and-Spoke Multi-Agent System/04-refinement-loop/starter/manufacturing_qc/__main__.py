"""CLI entry point: `manufacturing-qc run <defect_report.json>` prints the
CorrectiveActionReport as JSON to stdout.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from manufacturing_qc.coordinator import Coordinator
from manufacturing_qc.models import DefectReport
from manufacturing_qc.runner import AnthropicSubagentRunner
from manufacturing_qc.tools import sqlite_lookup

_DEFAULT_DB = Path(__file__).parent.parent / "data" / "components.sqlite"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="manufacturing-qc")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Triage one defect report")
    run_parser.add_argument("defect_report", type=Path)
    run_parser.add_argument("--db", type=Path, default=_DEFAULT_DB)
    run_parser.add_argument("--model", default="claude-haiku-4-5")

    args = parser.parse_args(argv)

    report = DefectReport.model_validate(json.loads(args.defect_report.read_text()))
    runner = AnthropicSubagentRunner(
        model=args.model,
        tool_handlers={"sqlite_lookup": lambda inp: sqlite_lookup(args.db, **inp)},
    )
    coordinator = Coordinator(runner=runner)
    result = asyncio.run(coordinator.run(report))
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
