"""Pydantic models that cross subagent boundaries.

Every payload entering or leaving a subagent is one of these types. No untyped dicts
travel between agents; the schema is the contract.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


# TODO: Build the _ALLOWED_EVIDENCE_FIELDS frozenset below.
# Each entry is a token a cited_evidence string may begin with. Include:
#   - top-level container names: "defect_classification", "supplier_findings"
#   - DefectClassification leaf fields: "defect_type", "severity", "description_summary"
#   - SupplierFindings leaf fields: "component_records", "supplier_incident_summary"
#   - ComponentRecord leaf fields: "component_id", "supplier", "lot_id", "received_at",
#     "prior_incidents"
#   - The refinement token "refinement" (used by the refinement loop later)
# The allowlist is intentionally permissive (substring match, not exact equality), because
# the model returns evidence strings like "defect_type=SOLDER-BRIDGE" rather than bare names.
_ALLOWED_EVIDENCE_FIELDS: frozenset[str] = frozenset()


class RootCauseHypothesis(BaseModel):
    """Output of the root_cause subagent."""

    model_config = ConfigDict(frozen=True)

    ranked_causes: list[Cause] = Field(min_length=1)

    # TODO: Implement a Pydantic model_validator(mode="after") named
    # `_evidence_must_reference_known_fields` that iterates over every Cause in
    # ranked_causes and every entry in cause.cited_evidence. If an entry contains
    # NONE of the tokens in _ALLOWED_EVIDENCE_FIELDS as a substring, raise a
    # ValueError naming which cause's evidence is rejected.
    #
    # (Friction note: a model_validator(mode="after") method MUST return `self` at the
    # end. If you forget, the validator silently runs but its checks won't surface as
    # expected, and frozen=True hides the misbehavior even more.)


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
