"""Hub-and-spoke coordinator.

The coordinator owns all inter-subagent communication. Subagents never call each
other — every handoff is mediated here. The flow:

    1. Spawn defect_classifier and supplier_data in parallel (independent scopes).
    2. Hand the typed outputs to root_cause sequentially.
    3. Hand the hypothesis to report; if it flags a coverage_gap, re-invoke
       root_cause with a refinement query (bounded by `max_refinements`).

Later steps tighten the handoff contracts and implement the refinement loop.
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
dimensions are exhaustive for this scope — see PRD §4 AC-01-06."""


class Coordinator:
    """Hub of the hub-and-spoke multi-agent system."""

    def __init__(self, runner: SubagentRunner, max_refinements: int = 1) -> None:
        if max_refinements < 0:
            raise ValueError("max_refinements must be >= 0")
        self._runner = runner
        self._max_refinements = max_refinements

    async def run(self, report: DefectReport) -> CorrectiveActionReport:
        partial_failures: list[str] = []

        classification, supplier_findings = await self._spawn_independent(report, partial_failures)

        hypothesis = await self._invoke_root_cause(classification, supplier_findings)
        subagent_report = await self._invoke_report(
            report.defect_id, hypothesis, partial_failures
        )

        refinement_rounds = 0
        while (
            subagent_report.coverage_gap is not None
            and refinement_rounds < self._max_refinements
        ):
            refinement_rounds += 1
            hypothesis = await self._invoke_root_cause(
                classification,
                supplier_findings,
                refinement=_build_refinement_query(subagent_report.coverage_gap, hypothesis),
            )
            subagent_report = await self._invoke_report(
                report.defect_id, hypothesis, partial_failures
            )

        return CorrectiveActionReport(
            defect_id=report.defect_id,
            corrective_actions=list(subagent_report.corrective_actions),
            coverage_gap=subagent_report.coverage_gap,
            refinement_rounds=refinement_rounds,
            partial_failures=partial_failures,
        )

    async def _spawn_independent(
        self, report: DefectReport, partial_failures: list[str]
    ) -> tuple[DefectClassification, SupplierFindings | None]:
        """Spawn classifier and supplier_data concurrently with scoped payloads.

        Each subagent receives only the fields its scope requires. Supplier failure is
        tolerated and downgrades the supplier output to None; classifier failure is
        fatal (the rest of the pipeline cannot proceed without a defect type).
        """
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
        refinement: str | None = None,
    ) -> RootCauseHypothesis:
        payload = build_root_cause_payload(
            classification.model_dump(),
            supplier_findings.model_dump() if supplier_findings is not None else None,
        )
        if refinement is not None:
            payload["refinement"] = refinement
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


def _build_refinement_query(gap: str, prior: RootCauseHypothesis) -> str:
    summary = "; ".join(
        f"{i + 1}) {c.text} ({c.confidence})" for i, c in enumerate(prior.ranked_causes)
    )
    return f"Re-investigate: {gap}. Prior hypothesis: {summary}"


def build_root_cause_payload(
    defect_classification: Mapping[str, object],
    supplier_findings: Mapping[str, object] | None,
) -> dict[str, object]:
    """Validate the root-cause subagent's input against the two source schemas
    and return the structured payload. Raises pydantic.ValidationError if either
    input is malformed.

    Defined at module scope so the contract is independently testable and so
    later callers (e.g., a re-entry from the refinement loop) can reuse it.
    """
    DefectClassification.model_validate(defect_classification)
    if supplier_findings is not None:
        SupplierFindings.model_validate(supplier_findings)
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
