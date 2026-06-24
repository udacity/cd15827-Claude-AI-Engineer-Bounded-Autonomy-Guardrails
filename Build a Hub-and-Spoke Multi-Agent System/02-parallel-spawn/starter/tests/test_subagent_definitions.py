"""US-01 — Define coordinator and four scoped subagents.

Covers AC-01-01 through AC-01-06.
"""
from __future__ import annotations

import dataclasses
import inspect

import pytest
from pydantic import BaseModel

from manufacturing_qc import (
    DEFECT_CLASSIFIER,
    REPORT,
    ROOT_CAUSE,
    SUPPLIER_DATA,
    Coordinator,
    CorrectiveActionReport,
    DefectReport,
    SubagentDefinition,
)
from manufacturing_qc.coordinator import SCOPE_COVERAGE

ALL_SUBAGENTS = [DEFECT_CLASSIFIER, SUPPLIER_DATA, ROOT_CAUSE, REPORT]


# AC-01-01: SubagentDefinition shape and four instances exist
def test_subagent_definition_is_a_dataclass_with_required_fields() -> None:
    assert dataclasses.is_dataclass(SubagentDefinition)
    field_names = {f.name for f in dataclasses.fields(SubagentDefinition)}
    assert {"name", "system_prompt", "allowed_tools", "output_schema"} <= field_names


def test_all_four_subagent_instances_exist_and_are_distinct() -> None:
    names = {s.name for s in ALL_SUBAGENTS}
    assert names == {"defect_classifier", "supplier_data", "root_cause", "report"}


def test_each_subagent_output_schema_is_a_pydantic_model() -> None:
    for s in ALL_SUBAGENTS:
        assert inspect.isclass(s.output_schema)
        assert issubclass(s.output_schema, BaseModel)


# AC-01-03: scoped allowed_tools
def test_allowed_tools_subset_of_known_tools() -> None:
    known = {"sqlite_lookup", "emit_report"}
    for s in ALL_SUBAGENTS:
        assert set(s.allowed_tools) <= known, f"{s.name} has unknown tool"


def test_report_agent_has_no_db_tools() -> None:
    assert "sqlite_lookup" not in REPORT.allowed_tools


def test_supplier_agent_has_no_report_tool() -> None:
    assert "emit_report" not in SUPPLIER_DATA.allowed_tools


def test_supplier_agent_has_sqlite_lookup() -> None:
    assert "sqlite_lookup" in SUPPLIER_DATA.allowed_tools


# AC-01-02: goal-oriented, not procedural prompts
PROCEDURAL_TELLS = ("step 1", "first,", "then,", "next,", "after that")


def test_prompts_are_not_procedural() -> None:
    for s in ALL_SUBAGENTS:
        lowered = s.system_prompt.lower()
        for tell in PROCEDURAL_TELLS:
            assert tell not in lowered, f"{s.name} prompt contains procedural language: '{tell}'"


# AC-01-05: structured-output contract present in the prompt
def test_each_prompt_states_output_contract() -> None:
    for s in ALL_SUBAGENTS:
        schema_name = s.output_schema.__name__
        marker = "return JSON conforming to"
        assert marker in s.system_prompt, f"{s.name} missing '{marker}' marker"
        assert schema_name in s.system_prompt, (
            f"{s.name} prompt does not reference schema {schema_name}"
        )


# AC-01-06: SCOPE_COVERAGE doc + no orphan dimension
EXPECTED_DIMENSIONS = {"defect-type", "sourcing", "root-cause", "corrective-action"}


def test_scope_coverage_constant_enumerates_dimensions() -> None:
    assert isinstance(SCOPE_COVERAGE, dict)
    for s in ALL_SUBAGENTS:
        assert s.name in SCOPE_COVERAGE, f"{s.name} not in SCOPE_COVERAGE"
    owned = set(SCOPE_COVERAGE.values())
    assert EXPECTED_DIMENSIONS <= owned, f"missing dimensions: {EXPECTED_DIMENSIONS - owned}"


def test_subagent_prompts_jointly_cover_all_dimensions() -> None:
    """Each dimension must be mentioned in at least one subagent prompt."""
    joined = " ".join(s.system_prompt.lower() for s in ALL_SUBAGENTS)
    dimension_keywords = {
        "defect-type": ("defect type", "defect taxonomy", "classification"),
        "sourcing": ("supplier", "sourcing", "component lot"),
        "root-cause": ("root cause", "root-cause", "failure pattern"),
        "corrective-action": ("corrective action", "corrective-action", "remediation"),
    }
    for dim, keywords in dimension_keywords.items():
        assert any(k in joined for k in keywords), f"dimension '{dim}' orphaned"


# AC-01-04: Coordinator.run is callable and returns a CorrectiveActionReport
@pytest.mark.asyncio
async def test_coordinator_run_returns_corrective_action_report() -> None:
    coordinator = Coordinator(runner=_NullRunner())
    report = DefectReport(
        defect_id="D-TEST-0001",
        description="solder bridge between pin 3 and 4 on the regulator IC",
        component_ids=["IC-REG-7805"],
        line="L2",
        shift="morning",
    )
    result = await coordinator.run(report)
    assert isinstance(result, CorrectiveActionReport)
    assert result.defect_id == "D-TEST-0001"


class _NullRunner:
    """A subagent runner that returns empty/default outputs — used to exercise the
    coordinator's wiring before US-02/US-03 fill in the real flow.
    """

    async def run(
        self, subagent: SubagentDefinition, payload: dict[str, object]
    ) -> BaseModel:
        from manufacturing_qc.models import (
            Cause,
            DefectClassification,
            RootCauseHypothesis,
            SubagentReport,
            SupplierFindings,
        )

        if subagent is DEFECT_CLASSIFIER:
            return DefectClassification(
                defect_type="unknown", severity="low", description_summary="(stub)"
            )
        if subagent is SUPPLIER_DATA:
            return SupplierFindings(component_records=[], supplier_incident_summary="")
        if subagent is ROOT_CAUSE:
            return RootCauseHypothesis(
                ranked_causes=[
                    Cause(text="stub", confidence="low", cited_evidence=["defect_type"])
                ]
            )
        if subagent is REPORT:
            return SubagentReport(corrective_actions=["stub action"], coverage_gap=None)
        raise ValueError(f"unknown subagent {subagent.name}")
