"""Hub-and-spoke coordinator.

The coordinator owns all inter-subagent communication. Subagents never call each
other; every handoff is mediated here. In this step you wire up the parallel
classifier+supplier branch and pipe its outputs through the existing helper methods.

The helper methods `_invoke_root_cause`, `_invoke_report`, and `build_root_cause_payload`
are already provided. Your work is `_spawn_independent` and the body of `Coordinator.run`.
"""
from __future__ import annotations

import asyncio
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
        # TODO: Replace this stub with the orchestration pipeline.
        # 1. Track partial failures in a list (start empty).
        # 2. Call self._spawn_independent(report, partial_failures) to get
        #    (classification, supplier_findings); supplier_findings may be None
        #    on partial failure.
        # 3. Call self._invoke_root_cause(classification, supplier_findings) to get
        #    a RootCauseHypothesis.
        # 4. Call self._invoke_report(report.defect_id, hypothesis, partial_failures)
        #    to get a SubagentReport.
        # 5. Return a CorrectiveActionReport built from the SubagentReport fields,
        #    refinement_rounds=0, and the partial_failures list.
        return CorrectiveActionReport(
            defect_id=report.defect_id,
            corrective_actions=[],
            coverage_gap=None,
            refinement_rounds=0,
            partial_failures=[],
        )

    async def _spawn_independent(
        self, report: DefectReport, partial_failures: list[str]
    ) -> tuple[DefectClassification, SupplierFindings | None]:
        """Spawn classifier and supplier_data concurrently with scoped payloads.

        Each subagent receives ONLY the fields its scope requires:
        - classifier gets {"description": report.description}
        - supplier_data gets {"component_ids": list(report.component_ids)}

        Supplier failure is tolerated (downgrade supplier_findings to None and append a
        marker to partial_failures); classifier failure is fatal (re-raise).
        """
        # TODO: Use asyncio.gather to run both runner calls concurrently in a single
        # awaited expression. Pass return_exceptions=True so a single subagent failure
        # does not cancel the sibling task.
        #
        # (Friction note: omitting return_exceptions=True is a common mistake. Without
        # it, an exception from one task cancels the other and the partial-failure
        # branch below never runs.)
        #
        # After gather returns, handle results in order:
        # - classifier_result: if isinstance(..., BaseException), raise it; else
        #   validate via _expect(..., DefectClassification).
        # - supplier_result: if isinstance(..., BaseException), append a marker like
        #   "supplier_data: <ExceptionType>: <message>" to partial_failures and set
        #   supplier_findings = None; else validate via _expect(..., SupplierFindings).
        # Return (classification, supplier_findings).
        raise NotImplementedError("TODO US-02: implement parallel spawn with scoped payloads")

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
