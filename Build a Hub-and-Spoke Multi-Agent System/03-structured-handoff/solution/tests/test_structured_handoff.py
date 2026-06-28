"""Sequential delegation with structured context handoff.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from manufacturing_qc import (
    DEFECT_CLASSIFIER,
    REPORT,
    ROOT_CAUSE,
    SUPPLIER_DATA,
    Coordinator,
    DefectReport,
    SubagentDefinition,
)
from manufacturing_qc.coordinator import build_root_cause_payload
from manufacturing_qc.models import (
    Cause,
    DefectClassification,
    RootCauseHypothesis,
    SubagentReport,
    SupplierFindings,
)


# structured input validation for root cause
def test_build_root_cause_payload_accepts_valid_inputs() -> None:
    defect = DefectClassification(
        defect_type="SOLDER-BRIDGE", severity="high", description_summary="bridge"
    )
    supplier = SupplierFindings(component_records=[], supplier_incident_summary="none")
    payload = build_root_cause_payload(defect.model_dump(), supplier.model_dump())
    assert set(payload.keys()) == {"defect_classification", "supplier_findings"}


def test_build_root_cause_payload_accepts_none_supplier() -> None:
    defect = DefectClassification(
        defect_type="SOLDER-BRIDGE", severity="high", description_summary="bridge"
    )
    payload = build_root_cause_payload(defect.model_dump(), None)
    assert payload["supplier_findings"] is None


def test_build_root_cause_payload_rejects_malformed_classification() -> None:
    bad_classification = {"defect_type": "SOLDER-BRIDGE", "severity": "EXTREME"}
    supplier = SupplierFindings(component_records=[], supplier_incident_summary="none")
    with pytest.raises(ValidationError):
        build_root_cause_payload(bad_classification, supplier.model_dump())


def test_build_root_cause_payload_rejects_malformed_supplier() -> None:
    defect = DefectClassification(
        defect_type="SOLDER-BRIDGE", severity="high", description_summary="bridge"
    )
    bad_supplier = {"component_records": [{"component_id": 42}], "supplier_incident_summary": ""}
    with pytest.raises(ValidationError):
        build_root_cause_payload(defect.model_dump(), bad_supplier)


# RootCauseHypothesis constraints
def test_root_cause_requires_at_least_one_cause() -> None:
    with pytest.raises(ValidationError):
        RootCauseHypothesis(ranked_causes=[])


def test_cause_rejects_invalid_confidence_value() -> None:
    with pytest.raises(ValidationError):
        Cause(text="x", confidence="certain", cited_evidence=["defect_type"])  # type: ignore[arg-type]


def test_root_cause_rejects_evidence_that_does_not_reference_input_fields() -> None:
    with pytest.raises(ValidationError, match="does not reference"):
        RootCauseHypothesis(
            ranked_causes=[
                Cause(text="x", confidence="medium", cited_evidence=["weather_report"])
            ]
        )


def test_root_cause_accepts_evidence_that_references_classification_fields() -> None:
    hypothesis = RootCauseHypothesis(
        ranked_causes=[
            Cause(
                text="reflow drift causing solder bridges",
                confidence="high",
                cited_evidence=["defect_type=SOLDER-BRIDGE", "severity=high"],
            )
        ]
    )
    assert len(hypothesis.ranked_causes) == 1


def test_root_cause_accepts_evidence_that_references_supplier_fields() -> None:
    hypothesis = RootCauseHypothesis(
        ranked_causes=[
            Cause(
                text="lot defect from supplier X",
                confidence="medium",
                cited_evidence=["component_records[0].supplier", "supplier_incident_summary"],
            )
        ]
    )
    assert len(hypothesis.ranked_causes) == 1


# report agent receives only RootCauseHypothesis + defect_id (+ partial_failures meta)
@pytest.mark.asyncio
async def test_report_agent_payload_does_not_include_classifier_or_supplier_outputs() -> None:
    calls: list[tuple[str, Mapping[str, object]]] = []

    class _RecordingRunner:
        async def run(
            self, subagent: SubagentDefinition, payload: Mapping[str, object]
        ) -> BaseModel:
            calls.append((subagent.name, dict(payload)))
            return _stub_output(subagent)

    coordinator = Coordinator(runner=_RecordingRunner())
    await coordinator.run(_make_report())

    report_payload = next(p for name, p in calls if name == REPORT.name)
    # Allowed keys: defect_id, root_cause_hypothesis, partial_failures
    assert set(report_payload.keys()) <= {"defect_id", "root_cause_hypothesis", "partial_failures"}
    # Forbidden keys: any raw classifier/supplier output
    forbidden = {"defect_classification", "supplier_findings", "description", "component_ids"}
    assert not (set(report_payload.keys()) & forbidden), (
        f"report agent received raw classifier/supplier output: {report_payload.keys()}"
    )


# CorrectiveActionReport has both fields and is non-empty against a fixture
@pytest.mark.asyncio
async def test_pipeline_produces_non_empty_corrective_actions_from_fixture() -> None:
    fixture_dir = Path(__file__).parent.parent / "data" / "defect_reports"
    fixture_files = sorted(fixture_dir.glob("*.json"))
    assert fixture_files, "no fixture defect reports found in data/defect_reports/"
    report = DefectReport.model_validate(json.loads(fixture_files[0].read_text()))

    class _RealisticRunner:
        async def run(
            self, subagent: SubagentDefinition, payload: Mapping[str, object]
        ) -> BaseModel:
            return _stub_output(subagent)

    coordinator = Coordinator(runner=_RealisticRunner())
    result = await coordinator.run(report)

    assert result.defect_id == report.defect_id
    assert hasattr(result, "corrective_actions")
    assert hasattr(result, "coverage_gap")
    assert len(result.corrective_actions) >= 1


# helpers
def _make_report() -> DefectReport:
    return DefectReport(
        defect_id="D-HANDOFF-0001",
        description="cold solder joint on capacitor leg",
        component_ids=["CAP-10UF-A"],
        line="L1",
        shift="swing",
    )


def _stub_output(subagent: SubagentDefinition) -> BaseModel:
    if subagent is DEFECT_CLASSIFIER:
        return DefectClassification(
            defect_type="COLD-JOINT", severity="medium", description_summary="cold joint"
        )
    if subagent is SUPPLIER_DATA:
        return SupplierFindings(component_records=[], supplier_incident_summary="none")
    if subagent is ROOT_CAUSE:
        return RootCauseHypothesis(
            ranked_causes=[
                Cause(
                    text="reflow underheat at zone 3",
                    confidence="medium",
                    cited_evidence=["defect_type=COLD-JOINT"],
                )
            ]
        )
    if subagent is REPORT:
        return SubagentReport(
            corrective_actions=["raise zone 3 reflow temp by 5°C", "recheck after 2 cycles"],
            coverage_gap=None,
        )
    raise ValueError(f"unknown subagent {subagent.name}")
