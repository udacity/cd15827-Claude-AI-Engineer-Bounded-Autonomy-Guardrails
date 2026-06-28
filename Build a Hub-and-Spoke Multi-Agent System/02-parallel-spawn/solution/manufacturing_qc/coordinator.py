"""Hub-and-spoke coordinator.

The coordinator owns all inter-subagent communication. Subagents never call each
other; every handoff is mediated here. The flow at this stage:

    1. Spawn defect_classifier and supplier_data in parallel (independent scopes).
    2. Hand the typed outputs to root_cause sequentially with Pydantic-validated payloads.
    3. Hand the hypothesis to report.

Later steps tighten the handoff contracts. The iterative refinement loop is added afterward.
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
        partial_failures: list[str] = []

        classification, supplier_findings = await self._spawn_independent(report, partial_failures)
        hypothesis = await self._invoke_root_cause(classification, supplier_findings)
        subagent_report = await self._invoke_report(
            report.defect_id, hypothesis, partial_failures
        )

        return CorrectiveActionReport(
            defect_id=report.defect_id,
            corrective_actions=list(subagent_report.corrective_actions),
            coverage_gap=subagent_report.coverage_gap,
            refinement_rounds=0,
            partial_failures=partial_failures,
        )

    async def _spawn_independent(
        self, report: DefectReport, partial_failures: list[str]
    ) -> tuple[DefectClassification, SupplierFindings | None]:
        """Spawn classifier and supplier_data concurrently with scoped payloads."""
        results = await asyncio.gather(
            self._runner.run(DEFECT_CLASSIFIER, {"description": report.description}),
            self._runner.run(SUPPLIER_DATA, {"component_ids": list(report.component_ids)}),
            return_exceptions=True,
        )
        classifier_result, supplier_result = results

        if isinstance(classifier_result, BaseException):
            raise classifier_result
        classification = _expect(classifier_result, DefectClassification)

        supplier_findings: SupplierFindings | None
        if isinstance(supplier_result, BaseException):
            partial_failures.append(
                f"supplier_data: {type(supplier_result).__name__}: {supplier_result}"
            )
            supplier_findings = None
        else:
            supplier_findings = _expect(supplier_result, SupplierFindings)

        return classification, supplier_findings

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
