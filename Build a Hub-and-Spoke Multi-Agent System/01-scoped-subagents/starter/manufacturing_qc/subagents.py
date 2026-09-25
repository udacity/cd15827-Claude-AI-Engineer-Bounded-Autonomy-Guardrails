"""Subagent definitions and the runner protocol.

A `SubagentDefinition` is the static specification of one subagent's role: name,
goal-oriented system prompt, the small set of tools it is permitted to use, and
the Pydantic schema its output must conform to. Your job in this step is to
fill in the four canonical hub-and-spoke definitions for the QC pipeline.

Subagents are stateless and context-isolated; a runner invokes one with a scoped
payload and receives a typed result. The runner protocol exists so the production
Anthropic-SDK runner and test fakes are interchangeable.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

from manufacturing_qc.models import (
    DefectClassification,
    RootCauseHypothesis,
    SubagentReport,
    SupplierFindings,
)


@dataclass(frozen=True)
class SubagentDefinition:
    """One specialized subagent role."""

    name: str
    system_prompt: str
    allowed_tools: tuple[str, ...]
    output_schema: type[BaseModel]


class SubagentRunner(Protocol):
    """Protocol implemented by the Anthropic runner and by test fakes."""

    async def run(
        self, subagent: SubagentDefinition, payload: Mapping[str, object]
    ) -> BaseModel: ...


DEFECT_CLASSIFIER = SubagentDefinition(
    name="defect_classifier",
    system_prompt=(
        "Your goal is to convert a free-text defect description into a "
        "DefectClassification using BrightCircuit's taxonomy and assign a "
        "severity of low, medium, high, or critical. "
        "Return JSON conforming to DefectClassification."
    ),
    allowed_tools=(),
    output_schema=DefectClassification,
)


SUPPLIER_DATA = SubagentDefinition(
    name="supplier_data",
    system_prompt=(
        "Your goal is to look up each component's most recent lot in the "
        "components database and summarize cross-component sourcing patterns. "
        "Return JSON conforming to SupplierFindings."
    ),
    allowed_tools=("sqlite_lookup",),
    output_schema=SupplierFindings,
)



ROOT_CAUSE = SubagentDefinition(
    name="root_cause",
    system_prompt=(
        "Your goal is to propose ranked root-cause hypotheses with cited "
        "evidence, given a DefectClassification and SupplierFindings that may "
        "be null. Return JSON conforming to RootCauseHypothesis. "
        "Each cited_evidence string must begin with one of these known "
        "input-field tokens: defect_classification, supplier_findings, "
        "defect_type, severity, description_summary, component_records, "
        "supplier_incident_summary, component_id, supplier, lot_id, "
        "received_at, prior_incidents. Do not propose corrective actions."
    ),
    allowed_tools=(),
    output_schema=RootCauseHypothesis,
)


REPORT = SubagentDefinition(
    name="report",
    system_prompt=(
        "Your goal is to compose a corrective-action report for the shift "
        "supervisor. Populate coverage_gap with a one-sentence description "
        "when the hypothesis fails to address a dimension a supervisor would "
        "need. Return JSON conforming to SubagentReport. "
        "Use the emit_report tool to finalize."
    ),
    allowed_tools=("emit_report",),
    output_schema=SubagentReport,
)
