"""Subagent definitions and the runner protocol.

A `SubagentDefinition` is the static specification of one subagent's role: name,
goal-oriented system prompt, the small set of tools it is permitted to use, and
the Pydantic schema its output must conform to. Your job in this exercise is to
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
    # TODO: Write a goal-oriented system prompt for the defect classifier.
    # The prompt must state the goal (convert a free-text defect description into a
    # DefectClassification using BrightCircuit's taxonomy and a severity in
    # {low, medium, high, critical}) and the structured-output contract using the
    # exact phrase "return JSON conforming to DefectClassification". Do not write
    # procedural steps ("First, ... Then, ..."). Do not mention components or the
    # supplier subagent's scope.
    system_prompt="",
    # TODO: This subagent needs no external tools (only its schema-bound emit tool,
    # which the runner adds automatically). Leave the tuple empty.
    allowed_tools=(),
    output_schema=DefectClassification,
)


SUPPLIER_DATA = SubagentDefinition(
    name="supplier_data",
    # TODO: Write a goal-oriented system prompt for the supplier-data subagent.
    # State the goal (look up each component's most recent lot in the components
    # database and summarize cross-component sourcing patterns) and use the phrase
    # "return JSON conforming to SupplierFindings". Do not write procedural steps.
    # Do not mention the defect description (that is the classifier's scope) and
    # do not propose corrective actions.
    system_prompt="",
    # TODO: This subagent needs the sqlite_lookup external tool. Add it.
    allowed_tools=(),
    output_schema=SupplierFindings,
)


ROOT_CAUSE = SubagentDefinition(
    name="root_cause",
    # TODO: Write a goal-oriented system prompt for the root-cause investigator.
    # State the goal (propose ranked root-cause hypotheses with cited evidence,
    # given a DefectClassification and SupplierFindings that may be null) and use
    # the phrase "return JSON conforming to RootCauseHypothesis". Tell the model
    # that each cited_evidence string must begin with one of the known input-field
    # tokens (defect_classification, supplier_findings, defect_type, severity,
    # description_summary, component_records, supplier_incident_summary,
    # component_id, supplier, lot_id, received_at, prior_incidents). Do not propose
    # corrective actions (that is the report agent's scope).
    system_prompt="",
    # TODO: This subagent needs no external tools.
    allowed_tools=(),
    output_schema=RootCauseHypothesis,
)


REPORT = SubagentDefinition(
    name="report",
    # TODO: Write a goal-oriented system prompt for the corrective-action report
    # author. State the goal (compose a corrective-action report for the shift
    # supervisor; populate coverage_gap with a one-sentence description when the
    # hypothesis fails to address a dimension a supervisor would need) and use
    # the phrase "return JSON conforming to SubagentReport". Tell the model to
    # use the emit_report tool to finalize.
    system_prompt="",
    # TODO: This subagent uses the emit_report tool to finalize its output.
    allowed_tools=(),
    output_schema=SubagentReport,
)
