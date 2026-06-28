"""Hub-and-spoke coordinator.

The coordinator owns all inter-subagent communication. Subagents never call each
other; every handoff is mediated here.

At this stage the coordinator skeleton is in place: it accepts a runner, accepts a
DefectReport, and returns a CorrectiveActionReport. The helper methods that will
actually drive the four subagents (`_invoke_root_cause`, `_invoke_report`,
`build_root_cause_payload`) are given to you below as infrastructure; the parallel
spawn helper is introduced in a later step. Coordinator.run currently returns empty fields,
which is expected at this stage.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import TypeVar

from pydantic import BaseModel

from manufacturing_qc.models import (
    CorrectiveActionReport,
    DefectClassification,
    DefectReport,
    RootCauseHypothesis,
    SubagentReport,
    SupplierFindings,
)
from manufacturing_qc.subagents import (
    DEFECT_CLASSIFIER,
    REPORT,
    ROOT_CAUSE,
    SUPPLIER_DATA,
    SubagentRunner,
)

_M = TypeVar("_M", bound=BaseModel)

SCOPE_COVERAGE: dict[str, str] = {
    DEFECT_CLASSIFIER.name: "defect-type",
    SUPPLIER_DATA.name: "sourcing",
    ROOT_CAUSE.name: "root-cause",
    REPORT.name: "corrective-action",
}
"""Maps each subagent to the dimension of defect analysis it owns. The four
dimensions are exhaustive for this scope; see PRD section 4 AC-01-06."""


class Coordinator:
    """Hub of the hub-and-spoke multi-agent system."""

    def __init__(self, runner: SubagentRunner) -> None:
        self._runner = runner

    async def run(self, report: DefectReport) -> CorrectiveActionReport:
        return CorrectiveActionReport(
            defect_id=report.defect_id,
            corrective_actions=[],
            coverage_gap=None,
            refinement_rounds=0,
            partial_failures=[],
        )

    async def _invoke_root_cause(
        self,
        classification: DefectClassification,
        supplier_findings: SupplierFindings | None,
    ) -> RootCauseHypothesis:
        payload = build_root_cause_payload(
            classification.model_dump(),
            supplier_findings.model_dump() if supplier_findings is not None else None,
        )
        result = await self._runner.run(ROOT_CAUSE, payload)
        return _expect(result, RootCauseHypothesis)

    async def _invoke_report(
        self,
        defect_id: str,
        hypothesis: RootCauseHypothesis,
        partial_failures: list[str],
    ) -> SubagentReport:
        payload = {
            "defect_id": defect_id,
            "root_cause_hypothesis": hypothesis.model_dump(),
            "partial_failures": list(partial_failures),
        }
        result = await self._runner.run(REPORT, payload)
        return _expect(result, SubagentReport)


def build_root_cause_payload(
    defect_classification: Mapping[str, object],
    supplier_findings: Mapping[str, object] | None,
) -> dict[str, object]:
    """Compose the structured payload handed to the root-cause subagent.

    At this stage the inputs are forwarded as-is; a later step tightens the contract by
    validating each input against its Pydantic schema before the call.
    """
    return {
        "defect_classification": dict(defect_classification),
        "supplier_findings": (
            dict(supplier_findings) if supplier_findings is not None else None
        ),
    }


def _expect(value: BaseModel | BaseException, schema: type[_M]) -> _M:
    if not isinstance(value, schema):
        got = type(value).__name__
        raise TypeError(f"runner returned {got}, expected {schema.__name__}")
    return value
