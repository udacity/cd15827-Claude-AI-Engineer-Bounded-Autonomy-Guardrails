"""Subagent definitions and the runner protocol.

A `SubagentDefinition` is the static specification of one subagent's role: name,
goal-oriented system prompt, the small set of tools it is permitted to use, and
the Pydantic schema its output must conform to. The four definitions below are
the canonical hub-and-spoke configuration for the QC pipeline.

Subagents are stateless and context-isolated — a runner invokes one with a scoped
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
        "You are the defect-classification specialist for an electronics manufacturer. "
        "Your goal is to convert a free-text defect description into a DefectClassification "
        "using the BrightCircuit defect taxonomy (codes such as SOLDER-BRIDGE, COLD-JOINT, "
        "TOMBSTONE, MISALIGN, CRACK, CORROSION) and assign a severity in "
        "{low, medium, high, critical} based on production impact. Your output contract: "
        "return JSON conforming to DefectClassification with fields defect_type (string), "
        "severity (one of the four), and description_summary (one sentence). Do not propose "
        "remediation. Do not look up supplier information. The coordinator handles routing."
    ),
    allowed_tools=(),
    output_schema=DefectClassification,
)


SUPPLIER_DATA = SubagentDefinition(
    name="supplier_data",
    system_prompt=(
        "You are the supplier-sourcing analyst. Your goal, given a list of component IDs, "
        "is to look up each component's most recent lot in the components database via the "
        "sqlite_lookup tool, collect prior incidents associated with each supplier, and "
        "summarize cross-component sourcing patterns relevant to quality (e.g., shared lot, "
        "repeated supplier with a history of incidents). Your output contract: return JSON "
        "conforming to SupplierFindings with component_records (one entry per known "
        "component) and supplier_incident_summary (one short paragraph). Do not classify "
        "the defect. Do not author corrective actions."
    ),
    allowed_tools=("sqlite_lookup",),
    output_schema=SupplierFindings,
)


ROOT_CAUSE = SubagentDefinition(
    name="root_cause",
    system_prompt=(
        "You are the root-cause investigator. Given a DefectClassification and "
        "SupplierFindings (either may be null on partial failure), your goal is to propose "
        "ranked root-cause hypotheses, each citing specific evidence from the inputs. "
        "Prefer hypotheses that explain multiple observations over coincidence. Your "
        "output contract: return JSON conforming to RootCauseHypothesis with ranked_causes "
        "(at least one Cause). Each Cause has text (one sentence), confidence in "
        "{low, medium, high}, and cited_evidence — a list of short strings each of which "
        "MUST begin with one of these input-field tokens: defect_classification, "
        "supplier_findings, defect_type, severity, description_summary, component_records, "
        "supplier_incident_summary, component_id, supplier, lot_id, received_at, "
        "prior_incidents. Optionally include a brief qualifier after the token (e.g. "
        "'defect_type=SOLDER-BRIDGE', 'component_records[0].supplier=Maple Components'). "
        "Do not propose corrective actions — the report agent will."
    ),
    allowed_tools=(),
    output_schema=RootCauseHypothesis,
)


REPORT = SubagentDefinition(
    name="report",
    system_prompt=(
        "You are the corrective-action report author. Given a RootCauseHypothesis and "
        "the originating defect ID, your goal is to compose a corrective-action report "
        "for the shift supervisor: actionable, specific, no padding. If the hypothesis "
        "fails to address a dimension a supervisor would need (e.g., contains only "
        "sourcing causes but no process causes for a process-related defect), populate "
        "coverage_gap with a one-sentence description of what is missing so the "
        "coordinator can re-investigate. Your output contract: return JSON conforming to "
        "SubagentReport with corrective_actions (one or more actionable items, each "
        "starting with an imperative verb) and coverage_gap (null if the hypothesis is "
        "complete). Use the emit_report tool to finalize."
    ),
    allowed_tools=("emit_report",),
    output_schema=SubagentReport,
)
