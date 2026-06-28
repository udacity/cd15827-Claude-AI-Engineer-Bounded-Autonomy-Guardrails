"""Spawn defect classifier and supplier data agents in parallel.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

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
        defect_id="D-PARALLEL-0001",
        description="solder bridge between pin 3 and 4 on the regulator IC",
        component_ids=["IC-REG-7805", "RES-100-OHM"],
        line="L2",
        shift="morning",
    )


@dataclass
class _RecordingRunner:
    """Records every (subagent, payload, start_ts, end_ts) call.

    Optionally delays each subagent by `delay_seconds[name]`.
    Optionally raises for subagents listed in `raise_for`.
    """

    delay_seconds: dict[str, float] = field(default_factory=dict)
    raise_for: set[str] = field(default_factory=set)
    calls: list[tuple[str, dict[str, object], float, float]] = field(default_factory=list)

    async def run(
        self, subagent: SubagentDefinition, payload: dict[str, object]
    ) -> BaseModel:
        start = time.perf_counter()
        delay = self.delay_seconds.get(subagent.name, 0.0)
        if delay:
            await asyncio.sleep(delay)
        if subagent.name in self.raise_for:
            end = time.perf_counter()
            self.calls.append((subagent.name, dict(payload), start, end))
            raise RuntimeError(f"simulated failure in {subagent.name}")
        end = time.perf_counter()
        self.calls.append((subagent.name, dict(payload), start, end))
        return _stub_output(subagent)


def _stub_output(subagent: SubagentDefinition) -> BaseModel:
    if subagent is DEFECT_CLASSIFIER:
        return DefectClassification(
            defect_type="SOLDER-BRIDGE", severity="medium", description_summary="bridge on IC"
        )
    if subagent is SUPPLIER_DATA:
        return SupplierFindings(component_records=[], supplier_incident_summary="no priors")
    if subagent is ROOT_CAUSE:
        return RootCauseHypothesis(
            ranked_causes=[
                Cause(
                    text="reflow profile drift",
                    confidence="medium",
                    cited_evidence=["defect_type"],
                )
            ]
        )
    if subagent is REPORT:
        return SubagentReport(
            corrective_actions=["recalibrate reflow oven zone 3"], coverage_gap=None
        )
    raise ValueError(f"unknown subagent {subagent.name}")


# parallel, not sequential
@pytest.mark.asyncio
async def test_classifier_and_supplier_overlap_in_time() -> None:
    runner = _RecordingRunner(delay_seconds={"defect_classifier": 0.2, "supplier_data": 0.2})
    coordinator = Coordinator(runner=runner)
    await coordinator.run(_make_report())

    by_name = {c[0]: c for c in runner.calls}
    cls_start, cls_end = by_name["defect_classifier"][2], by_name["defect_classifier"][3]
    sup_start, sup_end = by_name["supplier_data"][2], by_name["supplier_data"][3]
    overlap = min(cls_end, sup_end) - max(cls_start, sup_start)
    assert overlap > 0, "classifier and supplier did not overlap — sequential, not parallel"


# 300ms each, both run in < 450ms (sequential would be ~600ms)
@pytest.mark.asyncio
async def test_parallel_elapsed_less_than_sequential_sum() -> None:
    runner = _RecordingRunner(delay_seconds={"defect_classifier": 0.3, "supplier_data": 0.3})
    coordinator = Coordinator(runner=runner)
    start = time.perf_counter()
    await coordinator.run(_make_report())
    elapsed = time.perf_counter() - start
    assert elapsed < 0.45, f"elapsed {elapsed:.3f}s implies sequential execution"


# runtime scoping: payloads only contain the scoped fields
@pytest.mark.asyncio
async def test_classifier_receives_only_description() -> None:
    runner = _RecordingRunner()
    coordinator = Coordinator(runner=runner)
    await coordinator.run(_make_report())

    classifier_payload = next(c[1] for c in runner.calls if c[0] == "defect_classifier")
    assert set(classifier_payload.keys()) == {"description"}
    assert classifier_payload["description"] == _make_report().description


@pytest.mark.asyncio
async def test_supplier_receives_only_component_ids() -> None:
    runner = _RecordingRunner()
    coordinator = Coordinator(runner=runner)
    await coordinator.run(_make_report())

    supplier_payload = next(c[1] for c in runner.calls if c[0] == "supplier_data")
    assert set(supplier_payload.keys()) == {"component_ids"}
    assert supplier_payload["component_ids"] == list(_make_report().component_ids)


@pytest.mark.asyncio
async def test_neither_classifier_nor_supplier_receives_defect_id_or_shift() -> None:
    runner = _RecordingRunner()
    coordinator = Coordinator(runner=runner)
    await coordinator.run(_make_report())

    for name, payload, *_ in runner.calls:
        if name in ("defect_classifier", "supplier_data"):
            assert "defect_id" not in payload
            assert "shift" not in payload
            assert "line" not in payload


# static prompt non-overlap
def test_classifier_prompt_does_not_mention_components() -> None:
    prompt = DEFECT_CLASSIFIER.system_prompt.lower()
    assert "component" not in prompt, (
        "defect_classifier prompt should not reference components — sourcing is the supplier "
        "subagent's scope"
    )


def test_supplier_prompt_does_not_mention_defect_description() -> None:
    prompt = SUPPLIER_DATA.system_prompt.lower()
    assert "defect description" not in prompt
    assert "description" not in prompt, (
        "supplier_data prompt should not reference the defect description — classification "
        "is the classifier's scope"
    )


# partial failure of supplier
@pytest.mark.asyncio
async def test_supplier_failure_records_marker_and_pipeline_continues() -> None:
    runner = _RecordingRunner(raise_for={"supplier_data"})
    coordinator = Coordinator(runner=runner)
    result = await coordinator.run(_make_report())

    assert any("supplier_data" in marker for marker in result.partial_failures), (
        f"expected partial-failure marker for supplier_data, got {result.partial_failures!r}"
    )
    # pipeline continued: root_cause and report still ran
    called_names = [c[0] for c in runner.calls]
    assert ROOT_CAUSE.name in called_names
    assert REPORT.name in called_names


@pytest.mark.asyncio
async def test_root_cause_receives_supplier_findings_none_on_failure() -> None:
    runner = _RecordingRunner(raise_for={"supplier_data"})
    coordinator = Coordinator(runner=runner)
    await coordinator.run(_make_report())

    rc_payload = next(c[1] for c in runner.calls if c[0] == ROOT_CAUSE.name)
    assert "supplier_findings" in rc_payload
    assert rc_payload["supplier_findings"] is None


@pytest.mark.asyncio
async def test_report_agent_sees_partial_failure_marker() -> None:
    runner = _RecordingRunner(raise_for={"supplier_data"})
    coordinator = Coordinator(runner=runner)
    await coordinator.run(_make_report())

    report_payload = next(c[1] for c in runner.calls if c[0] == REPORT.name)
    assert "partial_failures" in report_payload
    failures = report_payload["partial_failures"]
    assert isinstance(failures, list)
    assert any("supplier_data" in m for m in failures)
