"""Public facade for the AE/MH structural risk slice."""
from __future__ import annotations

from .aemh_evaluation import evaluate_aemh_slice, evaluate_aemh_unit
from .aemh_results import AEMHSliceError, AEMHSliceResult, AEMHUnitResult
from .aemh_temporal import (
    BoundaryClassification,
    ProtocolAnchorDates,
    TemporalComparison,
    classify_event_against_boundary,
    compare_partial_dates,
)
from .aemh_types import (
    AEMH_ROLES,
    CLINICAL_FLAG_TOKENS,
    OPTIONAL_EVIDENCE_ROLES,
    REQUIRED_AEMH_ROLES,
    ConceptEquivalence,
    EventMatchStrategy,
    MedicalGrading,
    ProtocolAEMHBoundary,
    RoleAvailability,
    SemanticRecord,
    SemanticRecordSet,
    TemporalTolerance,
    _VALID_MONITORING_PRIORITIES,
    consume_cross_domain_evidence_refs,
    derive_monitoring_priority,
)
from .contracts import (
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_UNKNOWN,
    candidate_identity_classifier,
    candidate_identity_scope,
    candidate_lineage_fingerprint,
    candidate_stable_core,
)

__all__ = [
    "AEMH_ROLES",
    "REQUIRED_AEMH_ROLES",
    "OPTIONAL_EVIDENCE_ROLES",
    "ProtocolAEMHBoundary",
    "ProtocolAnchorDates",
    "BoundaryClassification",
    "EventMatchStrategy",
    "ConceptEquivalence",
    "TemporalTolerance",
    "classify_event_against_boundary",
    "SemanticRecord",
    "SemanticRecordSet",
    "RoleAvailability",
    "consume_cross_domain_evidence_refs",
    "MedicalGrading",
    "derive_monitoring_priority",
    "TemporalComparison",
    "compare_partial_dates",
    "AEMHUnitResult",
    "AEMHSliceResult",
    "AEMHSliceError",
    "evaluate_aemh_unit",
    "evaluate_aemh_slice",
    "candidate_identity_scope",
    "candidate_identity_classifier",
    "candidate_stable_core",
    "candidate_lineage_fingerprint",
    "MONITORING_PRIORITY_HIGH",
    "MONITORING_PRIORITY_MEDIUM",
    "MONITORING_PRIORITY_LOW",
    "MONITORING_PRIORITY_UNKNOWN",
    "CLINICAL_FLAG_TOKENS",
]
