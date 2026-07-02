"""Iterative refinement loop on coverage gaps.

The live test is gated by ANTHROPIC_API_KEY and
runs only under `pytest -m live`.
"""
from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from pydantic import BaseModel

from manufacturing_qc import (
    DEFECT_CLASSIFIER,
    REPORT,
    ROOT_CAUSE,
    SUPPLIER_DATA,
    Coordinator,
    DefectReport,
    SubagentDefinition,
)
from manufacturing_qc.models import (
    Cause,
    DefectClassification,
    RootCauseHypothesis,
    SubagentReport,
    SupplierFindings,
)


def _make_report() -> DefectReport:
    return DefectReport(
        defect_id="D-REFINE-0001",
        description="lifted pad on the input capacitor — solder didn't take",
        component_ids=["CAP-10UF-A"],
        line="L1",
        shift="morning",
    )


@dataclass
class _GapStreakRunner:
    """Reports a coverage gap the first `gap_rounds` times the report agent is called,
    then reports a clean result. Used to exercise the refinement loop end-to-end.
    """

    gap_rounds: int
    root_cause_calls: list[Mapping[str, object]] = field(default_factory=list)
    report_calls: list[Mapping[str, object]] = field(default_factory=list)

    async def run(
        self, subagent: SubagentDefinition, payload: Mapping[str, object]
    ) -> BaseModel:
        if subagent is DEFECT_CLASSIFIER:
            return DefectClassification(
                defect_type="LIFTED-PAD",
                severity="high",
                description_summary="pad lift on input cap",
            )
        if subagent is SUPPLIER_DATA:
            return SupplierFindings(
                component_records=[], supplier_incident_summary="no prior incidents"
            )
        if subagent is ROOT_CAUSE:
            self.root_cause_calls.append(dict(payload))
            return RootCauseHypothesis(
                ranked_causes=[
                    Cause(
                        text="reflow underheat — cold paste",
                        confidence="medium",
                        cited_evidence=["defect_type=LIFTED-PAD"],
                    )
                ]
            )
        if subagent is REPORT:
            self.report_calls.append(dict(payload))
            call_idx = len(self.report_calls) - 1
            if call_idx < self.gap_rounds:
                return SubagentReport(
                    corrective_actions=["interim: hold board for QA"],
                    coverage_gap="hypothesis ignores possible PCB warpage",
                )
            return SubagentReport(
                corrective_actions=[
                    "raise reflow zone 3 by 5°C",
                    "inspect PCB warpage on inbound batch",
                ],
                coverage_gap=None,
            )


# refinement query shape
@pytest.mark.asyncio
async def test_refinement_query_passed_to_root_cause_on_gap() -> None:
    runner = _GapStreakRunner(gap_rounds=1)
    coordinator = Coordinator(runner=runner, max_refinements=1)
    await coordinator.run(_make_report())

    # Second root-cause call should include a refinement field
    assert len(runner.root_cause_calls) == 2
    second = runner.root_cause_calls[1]
    assert "refinement" in second
    refinement = second["refinement"]
    assert isinstance(refinement, str)
    assert refinement.startswith("Re-investigate:")
    assert "hypothesis ignores possible PCB warpage" in refinement
    assert "Prior hypothesis:" in refinement


@pytest.mark.asyncio
async def test_initial_root_cause_call_has_no_refinement_field() -> None:
    runner = _GapStreakRunner(gap_rounds=0)
    coordinator = Coordinator(runner=runner, max_refinements=1)
    await coordinator.run(_make_report())

    assert "refinement" not in runner.root_cause_calls[0]


# hard cap behavior, configurable
@pytest.mark.asyncio
async def test_max_refinements_one_caps_root_cause_at_two_calls() -> None:
    runner = _GapStreakRunner(gap_rounds=5)  # always reports a gap within the cap
    coordinator = Coordinator(runner=runner, max_refinements=1)
    await coordinator.run(_make_report())
    assert len(runner.root_cause_calls) == 2


@pytest.mark.asyncio
async def test_max_refinements_two_caps_root_cause_at_three_calls() -> None:
    runner = _GapStreakRunner(gap_rounds=5)
    coordinator = Coordinator(runner=runner, max_refinements=2)
    await coordinator.run(_make_report())
    assert len(runner.root_cause_calls) == 3


@pytest.mark.asyncio
async def test_max_refinements_zero_skips_refinement_entirely() -> None:
    runner = _GapStreakRunner(gap_rounds=5)
    coordinator = Coordinator(runner=runner, max_refinements=0)
    await coordinator.run(_make_report())
    assert len(runner.root_cause_calls) == 1


def test_max_refinements_negative_rejected() -> None:
    class _NoopRunner:
        async def run(
            self, subagent: SubagentDefinition, payload: Mapping[str, object]
        ) -> BaseModel:
            raise NotImplementedError

    with pytest.raises(ValueError):
        Coordinator(runner=_NoopRunner(), max_refinements=-1)


# refinement_rounds bookkeeping
@pytest.mark.asyncio
async def test_refinement_rounds_zero_when_no_gap() -> None:
    runner = _GapStreakRunner(gap_rounds=0)
    coordinator = Coordinator(runner=runner)
    result = await coordinator.run(_make_report())
    assert result.refinement_rounds == 0
    assert result.coverage_gap is None


@pytest.mark.asyncio
async def test_refinement_rounds_one_after_gap_resolved() -> None:
    runner = _GapStreakRunner(gap_rounds=1)
    coordinator = Coordinator(runner=runner, max_refinements=1)
    result = await coordinator.run(_make_report())
    assert result.refinement_rounds == 1
    assert result.coverage_gap is None
    assert result.corrective_actions  # non-empty after resolution


@pytest.mark.asyncio
async def test_refinement_rounds_caps_when_gap_persists() -> None:
    runner = _GapStreakRunner(gap_rounds=99)
    coordinator = Coordinator(runner=runner, max_refinements=1)
    result = await coordinator.run(_make_report())
    assert result.refinement_rounds == 1
    # gap persists in the final report — coordinator did its bounded best
    assert result.coverage_gap is not None


# live end-to-end
@pytest.mark.live
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
@pytest.mark.asyncio
async def test_end_to_end_live_against_anthropic_api() -> None:
    from manufacturing_qc.runner import AnthropicSubagentRunner
    from manufacturing_qc.tools import sqlite_lookup

    fixture = Path(__file__).parent.parent / "data" / "defect_reports" / "D-0001.json"
    report = DefectReport.model_validate(json.loads(fixture.read_text()))

    db_path = Path(__file__).parent.parent / "data" / "components.sqlite"
    runner = AnthropicSubagentRunner(
        model="claude-haiku-4-5-20251001",
        tool_handlers={"sqlite_lookup": lambda args: sqlite_lookup(db_path, **args)},
    )
    coordinator = Coordinator(runner=runner, max_refinements=1)
    result = await coordinator.run(report)

    assert result.defect_id == "D-0001"
    assert len(result.corrective_actions) >= 1, (
        f"expected non-empty corrective_actions, got {result.corrective_actions!r}"
    )
    assert result.coverage_gap is None, (
        f"expected coverage_gap=None after refinement, got {result.coverage_gap!r}"
    )
    assert result.refinement_rounds <= 1
