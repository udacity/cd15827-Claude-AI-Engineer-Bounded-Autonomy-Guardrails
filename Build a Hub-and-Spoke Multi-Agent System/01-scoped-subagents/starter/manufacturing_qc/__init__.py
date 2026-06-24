"""Manufacturing Quality Control multi-agent system.

A coordinator agent triages electronics-defect reports by delegating to four scoped
subagents: defect classifier, supplier data, root cause, and report. Coordinator owns
all inter-subagent communication; subagents are stateless and context-isolated.
"""

from manufacturing_qc.coordinator import Coordinator
from manufacturing_qc.models import (
    ComponentRecord,
    CorrectiveActionReport,
    DefectClassification,
    DefectReport,
    RootCauseHypothesis,
    SupplierFindings,
)
from manufacturing_qc.subagents import (
    DEFECT_CLASSIFIER,
    REPORT,
    ROOT_CAUSE,
    SUPPLIER_DATA,
    SubagentDefinition,
)

__all__ = [
    "DEFECT_CLASSIFIER",
    "REPORT",
    "ROOT_CAUSE",
    "SUPPLIER_DATA",
    "ComponentRecord",
    "Coordinator",
    "CorrectiveActionReport",
    "DefectClassification",
    "DefectReport",
    "RootCauseHypothesis",
    "SubagentDefinition",
    "SupplierFindings",
]
