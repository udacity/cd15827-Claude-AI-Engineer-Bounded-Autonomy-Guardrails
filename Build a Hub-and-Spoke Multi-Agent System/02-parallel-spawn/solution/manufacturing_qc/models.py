"""Pydantic models that cross subagent boundaries.

Every payload entering or leaving a subagent is one of these types. No untyped dicts
travel between agents; the schema is the contract.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["low", "medium", "high", "critical"]
Confidence = Literal["low", "medium", "high"]


class DefectReport(BaseModel):
    """Input to the coordinator; a single defect observation from the line."""

    model_config = ConfigDict(frozen=True)

    defect_id: str
    description: str
    component_ids: list[str] = Field(min_length=1)
    line: str
    shift: str
    reported_at: datetime | None = None


class DefectClassification(BaseModel):
    """Output of the defect_classifier subagent."""

    model_config = ConfigDict(frozen=True)

    defect_type: str
    severity: Severity
    description_summary: str


class ComponentRecord(BaseModel):
    """A row from the components SQLite table."""

    model_config = ConfigDict(frozen=True)

    component_id: str
    supplier: str
    lot_id: str
    received_at: datetime
    prior_incidents: list[str] = Field(default_factory=list)


class SupplierFindings(BaseModel):
    """Output of the supplier_data subagent."""

    model_config = ConfigDict(frozen=True)

    component_records: list[ComponentRecord] = Field(default_factory=list)
    supplier_incident_summary: str


class Cause(BaseModel):
    """A single ranked root-cause hypothesis."""

    model_config = ConfigDict(frozen=True)

    text: str
    confidence: Confidence
    cited_evidence: list[str] = Field(min_length=1)


class RootCauseHypothesis(BaseModel):
    """Output of the root_cause subagent."""

    model_config = ConfigDict(frozen=True)

    ranked_causes: list[Cause] = Field(min_length=1)


class SubagentReport(BaseModel):
    """Output of the report subagent; the raw payload before refinement bookkeeping
    is added by the coordinator to produce a CorrectiveActionReport.
    """

    model_config = ConfigDict(frozen=True)

    corrective_actions: list[str] = Field(default_factory=list)
    coverage_gap: str | None = None


class CorrectiveActionReport(BaseModel):
    """The coordinator's final output for one defect report."""

    model_config = ConfigDict(frozen=True)

    defect_id: str
    corrective_actions: list[str] = Field(default_factory=list)
    coverage_gap: str | None = None
    refinement_rounds: int = 0
    partial_failures: list[str] = Field(default_factory=list)
