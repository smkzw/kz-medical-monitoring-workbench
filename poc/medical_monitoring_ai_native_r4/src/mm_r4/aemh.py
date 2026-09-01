"""R4-D01 AE/MH structural vertical slice.

This module implements the frozen D01 contract (matrix §4 R4-D01, §§3.2-3.8)
on top of the worker_01 common coverage contract.  It consumes
**semantic-role** records (never fixed table names), requires a versioned
:class:`ProtocolAEMHBoundary` and :class:`EventMatchStrategy`, reuses frozen
R3 partial-date normalization read-only, and produces L1 dispositions with
source-linked evidence, candidates, Query drafts and journey projections.

Key separations enforced here (matrix §3.5, §3.6):

* **reported AE/MH source records** are kept separate from **evidence
  assertions** and from **R2 :class:`RiskCandidate` objects**.  An AI/model
  assertion, if represented, remains an evidence assertion or candidate --
  never a reported source fact.
* **event intensity** (severity/grade), **seriousness criteria** (SAE/AESI
  flags), and **monitoring priority** are distinct fields.  Only monitoring
  priority projects to ``RiskCandidate.severity_hint``.
* Concept equivalence and temporal tolerance are **caller-supplied**; common
  code provides no project concept aliases and no default day-gap window.

The module does NOT own risk lifecycle (worker_03 / R2 ``RiskLifecycle``)
and does NOT mutate ``sys.path``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from mm_r2.identity import make_risk_identity
from mm_r2.risk import RiskCandidate, RiskIdentity
from mm_r3.normalization import NormalizedValue, normalize_partial_date

from .contracts import (
    CrossDomainEvidenceRef,
    CoverageValidationError,
    EvaluationUnit,
    EvidenceItem,
    L0CoverageStatus,
    L1Disposition,
    L1bEvidencePolarity,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_UNKNOWN,
    QueryDraftRef,
    RiskCandidateRef,
    RiskInstanceRef,
    SourceLocator,
    SourceRecordRef,
    UnitEvaluation,
    VALID_MONITORING_PRIORITIES,
    candidate_identity_classifier,
    candidate_identity_scope,
    candidate_stable_core,
    candidate_lineage_fingerprint,
)

__all__ = [
    # Semantic role constants
    "AEMH_ROLES",
    "REQUIRED_AEMH_ROLES",
    "OPTIONAL_EVIDENCE_ROLES",
    # Protocol inputs
    "ProtocolAEMHBoundary",
    "ProtocolAnchorDates",
    "BoundaryClassification",
    "EventMatchStrategy",
    "ConceptEquivalence",
    "TemporalTolerance",
    "classify_event_against_boundary",
    # Input records
    "SemanticRecord",
    "SemanticRecordSet",
    "RoleAvailability",
    "consume_cross_domain_evidence_refs",
    # Medical grading
    "MedicalGrading",
    "derive_monitoring_priority",
    # Temporal comparison
    "TemporalComparison",
    "compare_partial_dates",
    # Evaluation result
    "AEMHUnitResult",
    "AEMHSliceResult",
    # Engine
    "AEMHSliceError",
    "evaluate_aemh_unit",
    "evaluate_aemh_slice",
    # Identity accessors (public, for lifecycle integration)
    "candidate_identity_scope",
    "candidate_identity_classifier",
    "candidate_stable_core",
    "candidate_lineage_fingerprint",
    # Severity constants
    "MONITORING_PRIORITY_HIGH",
    "MONITORING_PRIORITY_MEDIUM",
    "MONITORING_PRIORITY_LOW",
    "MONITORING_PRIORITY_UNKNOWN",
    "CLINICAL_FLAG_TOKENS",
]


# ---------------------------------------------------------------------------
# Semantic role constants (matrix §4 D01, frozen contract §7)
# ---------------------------------------------------------------------------

#: Minimum required semantic roles for D01 AE/MH evaluation.
REQUIRED_AEMH_ROLES: Tuple[str, ...] = (
    "reported_ae",
    "reported_mh",
    "subject_identity",
    "site_identity",
    "temporal_anchor",
)

#: Optional evidence-bearing roles that may surface under-reporting clues
#: or counterevidence (matrix §4 D01 "必需输入").
OPTIONAL_EVIDENCE_ROLES: Tuple[str, ...] = (
    "symptom_event",
    "cm_indication",
    "lab_finding",
    "exam_finding",
    "healthcare_encounter",
    "procedure",
    "ip_action",
    "seriousness_clue",
    "death_event",
    "visit",
)

#: All recognized D01 semantic roles.
AEMH_ROLES: Tuple[str, ...] = REQUIRED_AEMH_ROLES + OPTIONAL_EVIDENCE_ROLES


# ---------------------------------------------------------------------------
# Monitoring-priority constants (matrix §3.5) -- re-exported from contracts
# ---------------------------------------------------------------------------
#
# The ``MONITORING_PRIORITY_*`` constants and ``VALID_MONITORING_PRIORITIES``
# now live on the neutral common surface ``mm_r4.contracts`` (frozen D02
# contract §2) so the lifecycle adapter and every concrete domain result
# share one set of tokens.  This module re-exports them for backward
# compatibility with existing public imports (``from mm_r4.aemh import
# MONITORING_PRIORITY_HIGH``).

#: Private alias retained for the in-package ``MedicalGrading`` validation;
#: identical to the neutral ``VALID_MONITORING_PRIORITIES``.
_VALID_MONITORING_PRIORITIES: Tuple[str, ...] = VALID_MONITORING_PRIORITIES

#: Clinical-flag tokens that map to SAE/AESI seriousness criteria, NOT to
#: event intensity or monitoring priority (matrix §3.5).  These are kept in
#: candidate detail / projection, separate from severity_hint.
CLINICAL_FLAG_TOKENS: Tuple[str, ...] = (
    "sae",
    "aesi",
    "death",
    "life_threatening",
    "hospitalization",
    "disability",
    "congenital_anomaly",
    "other_important_medical_event",
)
# Backward-compatible private alias for in-package call sites.
_CLINICAL_FLAG_TOKENS = CLINICAL_FLAG_TOKENS

# Seriousness criteria that make an event SAE-like for R2's independent
# ``clinical_risk_flags`` projection.  AESI remains a separate flag and may
# coexist with SAE.
_SAE_CRITERIA_TOKENS: Tuple[str, ...] = tuple(
    token for token in CLINICAL_FLAG_TOKENS if token != "aesi"
)


#: NCS (not clinically significant) signal tokens -- recognized in record
#: ``clinical_significance`` or note text.  NCS is *combination* counter-
#: evidence only: it never absolutely excludes a clue by itself.
_NCS_TOKENS: Tuple[str, ...] = (
    "ncs",
    "not_clinically_significant",
    "not clinically significant",
)

#: Alternative-diagnosis signal tokens.  A confirmed alternative diagnosis
#: may act as source-linked counterevidence but never absolutely excludes.
_ALT_DIAG_TOKENS: Tuple[str, ...] = (
    "alternative_diagnosis",
    "alternative diagnosis",
    "alt_diagnosis",
    "confirmed_alternative_diagnosis",
)


def _has_token(text: str, tokens: Sequence[str]) -> bool:
    """Case-insensitive substring check for any token in text."""
    lower = text.strip().lower()
    if not lower:
        return False
    for token in tokens:
        if token.lower() in lower:
            return True
    return False

# ---------------------------------------------------------------------------
# Versioned protocol boundary and event-match strategy (matrix §4 D01)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConceptEquivalence:
    """Caller-supplied concept equivalence groups.

    Each group is a frozenset of concept strings treated as equivalent for
    matching purposes.  Common code provides NO project concept aliases
    (matrix §4 D01 "误报控制").

    Two concepts match when they are string-identical OR belong to the same
    caller-supplied equivalence group.
    """
    groups: Tuple[frozenset, ...] = ()
    version: str = ""

    def __post_init__(self) -> None:
        validated: List[frozenset] = []
        for grp in self.groups:
            if not isinstance(grp, (frozenset, set, tuple, list)):
                raise CoverageValidationError(
                    "ConceptEquivalence.groups entries must be iterables of "
                    "strings")
            frozen = frozenset(grp)
            if not frozen:
                continue
            for item in frozen:
                if not isinstance(item, str) or not item.strip():
                    raise CoverageValidationError(
                        "ConceptEquivalence group members must be non-empty "
                        "strings")
            validated.append(frozen)
        object.__setattr__(self, "groups", tuple(validated))
        if not isinstance(self.version, str) or not self.version.strip():
            raise CoverageValidationError(
                "ConceptEquivalence.version is required and must be a "
                "non-empty string")

    def are_equivalent(self, concept_a: str, concept_b: str) -> bool:
        """True when both concepts are identical or in the same group."""
        if concept_a == concept_b:
            return True
        for grp in self.groups:
            if concept_a in grp and concept_b in grp:
                return True
        return False

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "groups": [sorted(g) for g in self.groups],
            "version": self.version,
        }


@dataclass(frozen=True)
class TemporalTolerance:
    """Caller-supplied temporal tolerance for event matching.

    ``same_day`` means two events on the same calendar day match temporally.
    ``tolerance_days`` defines a symmetric window; ``None`` means no
    day-based tolerance is applied -- the caller must rely on shared-date
    precision only.  Common code provides NO default day-gap window
    (matrix §4 D01 "误报控制").

    If ``tolerance_days`` is ``None``, two dates with no shared precision
    (e.g., one year-only, one full date from a different year) will fail
    closed into ``boundary`` or ``not_evaluable``.
    """

    tolerance_days: Optional[int] = None
    same_day: bool = True
    version: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.same_day, bool):
            raise CoverageValidationError(
                "TemporalTolerance.same_day must be a bool")
        if self.tolerance_days is not None:
            if not isinstance(self.tolerance_days, int) or isinstance(
                    self.tolerance_days, bool):
                raise CoverageValidationError(
                    "TemporalTolerance.tolerance_days must be a non-negative "
                    "int or None")
            if self.tolerance_days < 0:
                raise CoverageValidationError(
                    "TemporalTolerance.tolerance_days must be a non-negative "
                    "int or None")
        if not isinstance(self.version, str) or not self.version.strip():
            raise CoverageValidationError(
                "TemporalTolerance.version is required and must be a "
                "non-empty string")

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "tolerance_days": self.tolerance_days,
            "same_day": self.same_day,
            "version": self.version,
        }


@dataclass(frozen=True)
class EventMatchStrategy:
    """Versioned strategy for matching cross-source medical events to
    reported AE/MH records.

    Combines caller-supplied :class:`ConceptEquivalence` and
    :class:`TemporalTolerance`.  No project-specific thresholds, no default
    30-day rule, no hardcoded concept aliases (matrix §4 D01).
    """

    strategy_id: str
    version: str
    # Required and versioned: no silent empty ConceptEquivalence /
    # TemporalTolerance defaults (those raise without a version anyway).
    concept_equivalence: ConceptEquivalence
    temporal_tolerance: TemporalTolerance
    description: str = ""

    def __post_init__(self) -> None:
        if not self.strategy_id.strip():
            raise CoverageValidationError(
                "EventMatchStrategy.strategy_id is required")
        if not self.version.strip():
            raise CoverageValidationError(
                "EventMatchStrategy.version is required")
        if not isinstance(self.concept_equivalence, ConceptEquivalence):
            raise CoverageValidationError(
                "EventMatchStrategy.concept_equivalence must be a "
                "ConceptEquivalence")
        if not isinstance(self.temporal_tolerance, TemporalTolerance):
            raise CoverageValidationError(
                "EventMatchStrategy.temporal_tolerance must be a "
                "TemporalTolerance")
        if not self.concept_equivalence.version.strip():
            raise CoverageValidationError(
                "EventMatchStrategy.concept_equivalence.version is required "
                "and must be non-empty")
        if not self.temporal_tolerance.version.strip():
            raise CoverageValidationError(
                "EventMatchStrategy.temporal_tolerance.version is required "
                "and must be non-empty")

    def concepts_match(self, concept_a: str, concept_b: str) -> bool:
        return self.concept_equivalence.are_equivalent(concept_a, concept_b)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "version": self.version,
            "concept_equivalence": self.concept_equivalence.canonical_payload(),
            "temporal_tolerance": self.temporal_tolerance.canonical_payload(),
            "description": self.description,
        }


@dataclass(frozen=True)
class ProtocolAEMHBoundary:
    """Versioned protocol reporting boundary for AE/MH (matrix §4 D01).

    Defines the study reference period (informed consent, first dose /
    randomization, treatment phase, reporting cutoff) and any protocol-
    specified exclusions.  The boundary is determined by the *protocol*,
    not globally hardcoded to the first dose date.

    ``reporting_start_anchor`` and ``reporting_end_anchor`` are versioned
    anchor descriptors (e.g., "icf_date", "first_dose_date", "cutoff_date",
    "end_of_treatment_plus_30d").  They are *descriptors*, not dates; the
    actual anchor dates are resolved from the subject's temporal anchor
    records via :class:`ProtocolAnchorDates` during evaluation.

    ``applicable`` (default ``True``) plus ``non_applicable_reason`` allows
    a versioned protocol to mark a unit as genuinely out of scope, yielding
    L1 ``not_applicable`` (finding 3).
    """

    boundary_id: str
    version: str
    reporting_start_anchor: str
    reporting_end_anchor: str
    protocol_exclusions: Tuple[str, ...] = ()
    description: str = ""
    applicable: bool = True
    non_applicable_reason: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.boundary_id, str) or not self.boundary_id.strip():
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.boundary_id is required")
        if not isinstance(self.version, str) or not self.version.strip():
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.version is required")
        if not isinstance(self.reporting_start_anchor, str) or not \
                self.reporting_start_anchor.strip():
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.reporting_start_anchor is required")
        if not isinstance(self.reporting_end_anchor, str) or not \
                self.reporting_end_anchor.strip():
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.reporting_end_anchor is required")
        if not isinstance(self.applicable, bool):
            raise CoverageValidationError(
                "ProtocolAEMHBoundary.applicable must be a bool")
        frozen_excl = tuple(self.protocol_exclusions)
        for item in frozen_excl:
            if not isinstance(item, str) or not item.strip():
                raise CoverageValidationError(
                    "ProtocolAEMHBoundary.protocol_exclusions members must be "
                    "non-empty strings")
        object.__setattr__(self, "protocol_exclusions", frozen_excl)
        if not self.applicable:
            if not isinstance(self.non_applicable_reason, str) or not \
                    self.non_applicable_reason.strip():
                raise CoverageValidationError(
                    "ProtocolAEMHBoundary.non_applicable_reason is required "
                    "when applicable=False")

    def is_excluded_concept(self, concept: str) -> bool:
        """True when the protocol explicitly excludes this concept from
        AE collection."""
        return concept in self.protocol_exclusions

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "version": self.version,
            "reporting_start_anchor": self.reporting_start_anchor,
            "reporting_end_anchor": self.reporting_end_anchor,
            "protocol_exclusions": list(self.protocol_exclusions),
            "description": self.description,
            "applicable": self.applicable,
            "non_applicable_reason": self.non_applicable_reason,
        }


# ---------------------------------------------------------------------------
# Resolved protocol anchors + boundary classification (finding 2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolAnchorDates:
    """Resolved actual anchor dates for one subject under a
    :class:`ProtocolAEMHBoundary`.

    ``start_norm`` and ``end_norm`` are R3-normalized partial dates
    resolved by matching the boundary's anchor descriptors to the
    subject's ``temporal_anchor`` records.  ``resolved`` is ``True`` only
    when both anchors are available and normalizable.
    """

    start_descriptor: str
    end_descriptor: str
    start_norm: Optional[NormalizedValue]
    end_norm: Optional[NormalizedValue]
    start_raw: str = ""
    end_raw: str = ""

    @property
    def resolved(self) -> bool:
        return (
            self.start_norm is not None
            and self.end_norm is not None
            and self.start_norm.quality not in ("unsupported", "missing")
            and self.end_norm.quality not in ("unsupported", "missing")
            and bool(self.start_norm.normalized)
            and bool(self.end_norm.normalized)
        )

    def unresolved_reason(self) -> str:
        if self.start_norm is None or not self.start_norm.normalized or \
                self.start_norm.quality in ("unsupported", "missing"):
            return (
                f"报告起始锚点 {self.start_descriptor!r} 未解析到有效日期")
        if self.end_norm is None or not self.end_norm.normalized or \
                self.end_norm.quality in ("unsupported", "missing"):
            return (
                f"报告截止锚点 {self.end_descriptor!r} 未解析到有效日期")
        return ""


@dataclass(frozen=True)
class BoundaryClassification:
    """Outcome of classifying an event date against the resolved protocol
    boundary (finding 2).

    * ``inside``: event is strictly inside the reporting window.
    * ``outside``: event is strictly outside at shared precision.
    * ``boundary``: event date precision is insufficient or crosses a
      boundary edge (e.g., month-only date that could be inside or outside).
    * ``not_evaluable``: anchors missing/invalid or comparison impossible.
    """

    classification: str  # "inside" | "outside" | "boundary" | "not_evaluable"
    reason: str = ""
    shared_precision: str = "none"

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "classification": self.classification,
            "reason": self.reason,
            "shared_precision": self.shared_precision,
        }


_PREC_ORDER = {"day": 3, "month": 2, "year": 1, "none": 0}
_ORDER_PREC = {0: "none", 1: "year", 2: "month", 3: "day"}


def _resolve_protocol_anchors(
    record_set: "SemanticRecordSet",
    boundary: ProtocolAEMHBoundary,
) -> ProtocolAnchorDates:
    """Resolve the boundary's anchor descriptors to actual subject dates
    by matching ``anchor_descriptor`` on ``temporal_anchor`` records
    (finding 2)."""
    start_norm: Optional[NormalizedValue] = None
    end_norm: Optional[NormalizedValue] = None
    start_raw = ""
    end_raw = ""
    for rec in record_set.temporal_anchor_records:
        desc = rec.anchor_descriptor.strip()
        if not desc:
            continue
        if desc == boundary.reporting_start_anchor and not start_norm:
            start_raw = rec.event_date_raw
            start_norm = rec.normalized_date()
        elif desc == boundary.reporting_end_anchor and not end_norm:
            end_raw = rec.event_date_raw
            end_norm = rec.normalized_date()
    return ProtocolAnchorDates(
        start_descriptor=boundary.reporting_start_anchor,
        end_descriptor=boundary.reporting_end_anchor,
        start_norm=start_norm,
        end_norm=end_norm,
        start_raw=start_raw,
        end_raw=end_raw,
    )


def classify_event_against_boundary(
    event_date: Optional[NormalizedValue],
    anchors: ProtocolAnchorDates,
) -> BoundaryClassification:
    """Classify an event date against the resolved protocol boundary.

    Exact inside/outside comparisons affect applicability; partial dates
    crossing a boundary yield ``boundary``; missing/invalid/incomparable
    anchors yield ``not_evaluable``; no silent first/last-day imputation
    (finding 2).
    """
    if not anchors.resolved:
        return BoundaryClassification(
            classification="not_evaluable",
            reason=anchors.unresolved_reason(),
            shared_precision="none")

    if event_date is None or not event_date.normalized:
        return BoundaryClassification(
            classification="not_evaluable",
            reason="事件日期缺失，无法与方案报告窗口比较",
            shared_precision="none")
    if event_date.quality in ("unsupported", "missing"):
        return BoundaryClassification(
            classification="not_evaluable",
            reason=f"事件日期质量不足 (quality={event_date.quality})",
            shared_precision="none")

    start = anchors.start_norm  # type: ignore[union-attr]
    end = anchors.end_norm      # type: ignore[union-attr]
    ev_norm = str(event_date.normalized)
    start_norm = str(start.normalized)
    end_norm = str(end.normalized)

    ev_prec = _precision_level(event_date)
    start_prec = _precision_level(start)
    end_prec = _precision_level(end)

    min_prec_order = min(
        _PREC_ORDER[ev_prec],
        _PREC_ORDER[start_prec],
        _PREC_ORDER[end_prec],
    )
    if min_prec_order == 0:
        return BoundaryClassification(
            classification="not_evaluable",
            reason="无共享精度，无法比较事件与方案报告窗口",
            shared_precision="none")
    min_prec = _ORDER_PREC[min_prec_order]

    def _cmp(a: str, b: str, prec: str) -> int:
        n = {"year": 4, "month": 7, "day": 10}.get(prec, 0)
        sa, sb = a[:n], b[:n]
        if sa < sb:
            return -1
        if sa > sb:
            return 1
        return 0

    cmp_start = _cmp(ev_norm, start_norm, min_prec)
    cmp_end = _cmp(ev_norm, end_norm, min_prec)

    # Strictly inside at shared precision.  A first occurrence exactly on
    # the study/reporting start cannot be ordered relative to the anchor
    # without time-of-day or explicit pre-existing/worsening context, so it
    # is a boundary even when both values are day precision (matrix §4 D01).
    if cmp_start >= 0 and cmp_end <= 0:
        if cmp_start == 0:
            return BoundaryClassification(
                classification="boundary",
                reason=(
                    "事件恰位于方案研究起点，缺少日内先后或既往存在/"
                    "新发恶化信息，暂无法确定是否属于研究期事件"),
                shared_precision=min_prec)
        # End-edge ambiguity remains precision-dependent: a day-precision
        # reporting cutoff is inclusive unless the protocol says otherwise,
        # while a month/year value cannot prove window membership.
        if min_prec in ("year", "month") and cmp_end == 0:
            return BoundaryClassification(
                classification="boundary",
                reason=(
                    f"事件在 {min_prec} 精度上恰位于方案报告窗口边界，"
                    f"无法确定是否在窗口内"),
                shared_precision=min_prec)
        return BoundaryClassification(
            classification="inside",
            reason="事件在方案报告窗口内",
            shared_precision=min_prec)

    # Strictly outside at shared precision.
    if cmp_start < 0 or cmp_end > 0:
        # If the event is coarser than the boundary and same year as the
        # edge, it could cross -> boundary.
        if ev_prec in ("year", "month") and (
                start_prec == "day" or end_prec == "day"):
            edge_same = False
            if cmp_start < 0 and ev_norm[:4] == start_norm[:4]:
                edge_same = True
            if cmp_end > 0 and ev_norm[:4] == end_norm[:4]:
                edge_same = True
            if edge_same:
                return BoundaryClassification(
                    classification="boundary",
                    reason=(
                        f"事件精度 ({ev_prec}) 不足以确定是否跨过"
                        f"方案报告窗口边界"),
                    shared_precision=min_prec)
        return BoundaryClassification(
            classification="outside",
            reason="事件在方案报告窗口外",
            shared_precision=min_prec)

    # Should not reach here, but fail safe.
    return BoundaryClassification(
        classification="boundary",
        reason="无法确定事件是否在方案报告窗口内",
        shared_precision=min_prec)


# ---------------------------------------------------------------------------
# Semantic-role records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SemanticRecord:
    """One semantic-role record carrying row-level content and a source
    locator.

    ``role`` is a semantic role from the active mapping (e.g.
    ``reported_ae``, ``symptom_event``, ``lab_finding``), never a fixed
    SDTM table name.  ``concept`` is the normalized medical concept
    (e.g., a MedDRA PT code).  ``event_date_raw`` is the raw date string
    that will be normalized via frozen R3 ``normalize_partial_date``.

    ``intensity`` carries event severity/grade (mild/moderate/severe, or
    a CTCAE grade) -- it is NEVER confused with seriousness or monitoring
    priority (matrix §3.5).

    ``seriousness_criteria`` is a tuple of seriousness-criterion tokens
    (e.g., ``("sae", "hospitalization")``).  These are clinical flags,
    kept separate from ``intensity`` and from monitoring priority.

    ``ai_assertion`` marks whether this record originated from a model/AI
    source.  When ``True``, the record can only become evidence or a
    candidate -- never a reported source fact (matrix §3.6, contract §9).
    """

    role: str
    concept: str
    locator: SourceLocator
    event_date_raw: str = ""
    subject_ref: str = ""
    site_ref: str = ""
    intensity: str = ""
    seriousness_criteria: Tuple[str, ...] = ()
    intensity_scale: str = ""  # e.g., "ctcae_v5", "protocol_scale_v1"
    outcome: str = ""
    action_taken: str = ""
    visit_label: str = ""
    phase: str = ""
    ai_assertion: bool = False
    note: str = ""
    clinical_significance: str = ""
    alternative_diagnosis: str = ""
    alternative_diagnosis_confirmed: bool = False
    anchor_descriptor: str = ""
    cross_domain_content_hash: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.role, str) or not self.role.strip():
            raise CoverageValidationError("SemanticRecord.role is required")
        if not isinstance(self.concept, str) or not self.concept.strip():
            raise CoverageValidationError(
                "SemanticRecord.concept is required")
        if not isinstance(self.locator, SourceLocator):
            raise CoverageValidationError(
                "SemanticRecord.locator must be a SourceLocator")
        if self.role not in AEMH_ROLES:
            raise CoverageValidationError(
                f"SemanticRecord.role={self.role!r} is not a recognized D01 "
                f"semantic role; recognized={AEMH_ROLES}")
        object.__setattr__(
            self, "seriousness_criteria", tuple(self.seriousness_criteria))
        if not isinstance(self.ai_assertion, bool):
            raise CoverageValidationError(
                "SemanticRecord.ai_assertion must be an actual bool, "
                "not a string or other type (finding 3)")
        if not isinstance(self.alternative_diagnosis_confirmed, bool):
            raise CoverageValidationError(
                "SemanticRecord.alternative_diagnosis_confirmed must be "
                "an actual bool (finding 2)")
        if self.cross_domain_content_hash:
            try:
                valid_hash = (
                    len(self.cross_domain_content_hash) == 64
                    and int(self.cross_domain_content_hash, 16) >= 0
                )
            except ValueError:
                valid_hash = False
            if not valid_hash:
                raise CoverageValidationError(
                    "SemanticRecord.cross_domain_content_hash must be SHA-256")

    @property
    def is_reported_ae(self) -> bool:
        return self.role == "reported_ae"

    @property
    def is_reported_mh(self) -> bool:
        return self.role == "reported_mh"

    @property
    def is_reported_source(self) -> bool:
        """True when this record is an accepted reported AE/MH source.

        An AI assertion is NEVER a reported source fact, even if its role
        is ``reported_ae`` / ``reported_mh`` (finding 7)."""
        if self.ai_assertion:
            return False
        return self.role in ("reported_ae", "reported_mh")

    @property
    def is_evidence_role(self) -> bool:
        """True when this record is an optional evidence-bearing role."""
        return self.role in OPTIONAL_EVIDENCE_ROLES

    @property
    def has_seriousness_clue(self) -> bool:
        return bool(self.seriousness_criteria)

    @property
    def is_ncs(self) -> bool:
        """True when this record carries an explicit NCS determination
        (finding 6)."""
        return (
            bool(self.clinical_significance.strip())
            and _has_token(self.clinical_significance, _NCS_TOKENS)
        ) or _has_token(self.note, _NCS_TOKENS)

    @property
    def has_alternative_diagnosis(self) -> bool:
        """True when this record carries a *confirmed* alternative
        diagnosis (finding 2/6).  A non-empty tentative diagnosis alone
        must NOT suppress a clue."""
        return (
            bool(self.alternative_diagnosis.strip())
            and self.alternative_diagnosis_confirmed
        )

    @property
    def has_medical_action(self) -> bool:
        """True when this record indicates a medical action or treatment
        (finding 6: NCS alone is not exclusion if there is a symptom,
        action, seriousness clue, or repeat worsening)."""
        return bool(self.action_taken.strip())

    def normalized_date(self) -> Optional[NormalizedValue]:
        """R3 partial-date normalization of ``event_date_raw``."""
        if not self.event_date_raw:
            return None
        return normalize_partial_date(self.event_date_raw)


def _cross_domain_dedup_key(
    *, locator: SourceLocator, evidence_role: str, content_hash_value: str,
) -> Tuple[str, str, str, str]:
    return (
        locator.table_semantic,
        locator.record_id,
        evidence_role,
        content_hash_value,
    )


def consume_cross_domain_evidence_refs(
    active_mapping_records: Sequence[SemanticRecord],
    refs: Sequence[CrossDomainEvidenceRef],
) -> Tuple[SemanticRecord, ...]:
    """Consume D02 ``cm_indication`` refs with frozen dual-path dedup.

    The only dedup key is ``(table_semantic, record_id, evidence_role,
    content_hash)``.  Active ``cm_indication`` records without a canonical
    hash fail closed; changed clinical claims remain distinct.  This adapter
    carries source evidence only and never imports D02 lifecycle objects.
    """
    merged = list(active_mapping_records)
    seen: Set[Tuple[str, str, str, str]] = set()
    for record in active_mapping_records:
        if record.role != "cm_indication":
            continue
        if not record.cross_domain_content_hash:
            raise CoverageValidationError(
                "active cm_indication requires cross_domain_content_hash")
        seen.add(_cross_domain_dedup_key(
            locator=record.locator, evidence_role=record.role,
            content_hash_value=record.cross_domain_content_hash))

    for ref in refs:
        if (ref.consumer_domain != "D01_aemh"
                or ref.evidence_role != "cm_indication"):
            raise CoverageValidationError(
                "unsupported cross-domain evidence consumer or role")
        if not ref.verify_content_hash():
            raise CoverageValidationError(
                "cross-domain evidence content hash verification failed")
        key = _cross_domain_dedup_key(
            locator=ref.source_locator, evidence_role=ref.evidence_role,
            content_hash_value=ref.content_hash)
        if key in seen:
            continue
        payload = dict(ref.context_payload)
        concept = str(payload.get("indication_concept", "")).strip()
        subject_ref = str(payload.get("subject_ref", "")).strip()
        if not concept or not subject_ref:
            raise CoverageValidationError(
                "cm_indication handoff requires concept and subject_ref")
        merged.append(SemanticRecord(
            role="cm_indication", concept=concept,
            locator=ref.source_locator, subject_ref=subject_ref,
            site_ref=str(payload.get("site_ref", "")).strip(),
            note=str(payload.get("indication_text", "")).strip(),
            cross_domain_content_hash=ref.content_hash,
        ))
        seen.add(key)
    return tuple(merged)


@dataclass(frozen=True)
class RoleAvailability:
    """Immutable role-availability/coverage surface (finding 1).

    Distinguishes an *available but empty* semantic role (the mapped source
    was covered and had zero rows) from a *missing* role (the mapping or
    source was absent).  An empty-but-covered role satisfies the required-
    role contract; a missing role does not.
    """

    available_roles: Tuple[str, ...]
    empty_covered_roles: Tuple[str, ...]

    def is_available(self, role: str) -> bool:
        return role in self.available_roles

    def is_empty_covered(self, role: str) -> bool:
        return role in self.empty_covered_roles

    def is_satisfied(self, role: str) -> bool:
        """A role is satisfied when it is available (has records) or
        explicitly empty-but-covered."""
        return self.is_available(role) or self.is_empty_covered(role)

    def missing_required(self, required: Sequence[str]) -> Tuple[str, ...]:
        return tuple(r for r in required if not self.is_satisfied(r))


@dataclass(frozen=True)
class SemanticRecordSet:
    """A collection of :class:`SemanticRecord` values for one subject/scope.

    Carries an explicit :class:`RoleAvailability` surface so an empty-but-
    covered semantic role differs from a missing role (finding 1).  The
    record collection may be empty -- in that case a missing-subject slice
    evaluation returns a fail-closed result instead of crashing.

    Validates recognized semantic roles and rejects mixed subject/site
    records (finding 1).
    """

    records: Tuple[SemanticRecord, ...] = ()
    subject_ref: str = ""
    site_ref: str = ""
    scope_key: str = ""
    available_roles: Tuple[str, ...] = ()
    empty_covered_roles: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple):
            object.__setattr__(self, "records", tuple(self.records))
        if not isinstance(self.subject_ref, str) or not \
                self.subject_ref.strip():
            raise CoverageValidationError(
                "SemanticRecordSet.subject_ref is required")
        if not self.scope_key.strip():
            object.__setattr__(self, "scope_key", self.subject_ref)
        # Validate recognized roles and subject/site consistency.
        for rec in self.records:
            if not isinstance(rec, SemanticRecord):
                raise CoverageValidationError(
                    "SemanticRecordSet.records entries must be "
                    "SemanticRecord")
            if rec.role not in AEMH_ROLES:
                raise CoverageValidationError(
                    f"SemanticRecordSet contains unrecognized role "
                    f"{rec.role!r}")
            rec_subject = rec.subject_ref.strip()
            rec_site = rec.site_ref.strip()
            if rec_subject and rec_subject != self.subject_ref:
                raise CoverageValidationError(
                    f"SemanticRecordSet subject_ref={self.subject_ref!r} "
                    f"but record {rec.locator.record_id!r} has "
                    f"subject_ref={rec_subject!r}")
            if rec_site and self.site_ref and rec_site != self.site_ref:
                raise CoverageValidationError(
                    f"SemanticRecordSet site_ref={self.site_ref!r} but "
                    f"record {rec.locator.record_id!r} has "
                    f"site_ref={rec_site!r}")
        # F4: Validate role availability coherence.
        # 1. available_roles and empty_covered_roles must be recognized roles.
        for role in self.available_roles:
            if role not in AEMH_ROLES:
                raise CoverageValidationError(
                    f"SemanticRecordSet.available_roles contains "
                    f"unrecognized role {role!r}")
        for role in self.empty_covered_roles:
            if role not in AEMH_ROLES:
                raise CoverageValidationError(
                    f"SemanticRecordSet.empty_covered_roles contains "
                    f"unrecognized role {role!r}")
        # 2. No overlap between available and empty-covered.
        overlap = set(self.available_roles) & set(self.empty_covered_roles)
        if overlap:
            raise CoverageValidationError(
                f"SemanticRecordSet roles cannot be both available and "
                f"empty-covered: {sorted(overlap)}")
        # 3. Every role present in records must appear in available_roles.
        roles_in_records = set(r.role for r in self.records)
        missing_from_available = roles_in_records - set(self.available_roles)
        if missing_from_available:
            raise CoverageValidationError(
                f"SemanticRecordSet: roles present in records but not in "
                f"available_roles: {sorted(missing_from_available)}")
        # Freeze availability tuples.
        object.__setattr__(
            self, "available_roles",
            tuple(sorted(set(self.available_roles))))
        object.__setattr__(
            self, "empty_covered_roles",
            tuple(sorted(set(self.empty_covered_roles))))

    @property
    def role_availability(self) -> RoleAvailability:
        return RoleAvailability(
            available_roles=self.available_roles,
            empty_covered_roles=self.empty_covered_roles,
        )

    def by_role(self, role: str) -> Tuple[SemanticRecord, ...]:
        return tuple(r for r in self.records if r.role == role)

    @property
    def reported_ae_records(self) -> Tuple[SemanticRecord, ...]:
        return tuple(
            r for r in self.records
            if r.is_reported_source and r.role == "reported_ae")

    @property
    def reported_mh_records(self) -> Tuple[SemanticRecord, ...]:
        return tuple(
            r for r in self.records
            if r.is_reported_source and r.role == "reported_mh")

    @property
    def reported_source_records(self) -> Tuple[SemanticRecord, ...]:
        """Reported AE/MH source records, excluding any AI assertion
        (finding 7)."""
        return self.reported_ae_records + self.reported_mh_records

    @property
    def evidence_records(self) -> Tuple[SemanticRecord, ...]:
        """All non-source records that may surface clues.  An AI-asserted
        ``reported_ae``/``reported_mh`` is treated as evidence here, never
        as a reported source fact (finding 7)."""
        result: List[SemanticRecord] = []
        for r in self.records:
            if r.role in OPTIONAL_EVIDENCE_ROLES:
                result.append(r)
            elif r.ai_assertion and r.role in ("reported_ae", "reported_mh"):
                result.append(r)
        return tuple(result)

    @property
    def temporal_anchor_records(self) -> Tuple[SemanticRecord, ...]:
        return self.by_role("temporal_anchor")

    def roles_present(self) -> Tuple[str, ...]:
        return tuple(sorted(set(r.role for r in self.records)))

    def missing_required_roles(
        self, required: Sequence[str] = REQUIRED_AEMH_ROLES,
    ) -> Tuple[str, ...]:
        return self.role_availability.missing_required(required)


# ---------------------------------------------------------------------------
# Medical grading: intensity, seriousness, monitoring priority (matrix §3.5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MedicalGrading:
    """The three independent medical dimensions, kept separate.

    * ``intensity``: event severity/grade (e.g., "moderate", "Grade 2").
    * ``seriousness_criteria``: SAE/AESI/IME criterion tokens.
    * ``monitoring_priority``: high/medium/low/unknown -- this is the ONLY
      dimension that projects to ``RiskCandidate.severity_hint``.

    A high CTCAE grade does NOT auto-promote to SAE, and SAE does NOT
    require ``intensity=severe`` (matrix §3.5).
    """

    intensity: str = ""
    intensity_scale: str = ""
    seriousness_criteria: Tuple[str, ...] = ()
    monitoring_priority: str = MONITORING_PRIORITY_UNKNOWN

    def __post_init__(self) -> None:
        if self.monitoring_priority not in _VALID_MONITORING_PRIORITIES:
            raise CoverageValidationError(
                f"MedicalGrading.monitoring_priority="
                f"{self.monitoring_priority!r} is not one of "
                f"{_VALID_MONITORING_PRIORITIES}")
        object.__setattr__(
            self, "seriousness_criteria", tuple(self.seriousness_criteria))

    @property
    def has_seriousness_clue(self) -> bool:
        return any(
            token in _CLINICAL_FLAG_TOKENS
            for token in self.seriousness_criteria)

    @property
    def is_high_priority(self) -> bool:
        return self.monitoring_priority == MONITORING_PRIORITY_HIGH

    @property
    def severity_hint(self) -> str:
        """The R2 ``RiskCandidate.severity_hint`` value.

        Only monitoring priority maps here (matrix §3.5).  Unknown stays
        unknown; it is never defaulted to zero or low.
        """
        return self.monitoring_priority

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "intensity": self.intensity,
            "intensity_scale": self.intensity_scale,
            "seriousness_criteria": list(self.seriousness_criteria),
            "monitoring_priority": self.monitoring_priority,
        }


def derive_monitoring_priority(
    intensity: str = "",
    seriousness_criteria: Tuple[str, ...] = (),
    ai_confidence: float = 0.0,
) -> str:
    """Derive a conservative monitoring priority from available signals.

    This is a *conservative* derivation, not a clinical conclusion.  SAE /
    AESI / death / important-medical-event seriousness clues raise priority
    to ``high``.  A known ``severe`` intensity raises to at least ``medium``.
    Everything else stays ``unknown`` rather than defaulting to ``low`` --
    unknown means unknown (matrix §3.5 "未知强度/优先级保持 unknown").

    The function never conflates intensity with seriousness: a ``severe``
    intensity with no seriousness criteria is ``medium``, not ``high``.
    """
    serious = set(seriousness_criteria) & set(_CLINICAL_FLAG_TOKENS)
    if serious:
        return MONITORING_PRIORITY_HIGH
    norm_intensity = intensity.strip().lower() if intensity else ""
    if norm_intensity in ("severe", "grade 3", "grade 4", "grade 5", "grade4", "grade5"):
        return MONITORING_PRIORITY_MEDIUM
    if norm_intensity in ("moderate", "grade 2", "grade2"):
        return MONITORING_PRIORITY_MEDIUM
    if norm_intensity in ("mild", "grade 1", "grade1"):
        return MONITORING_PRIORITY_LOW
    return MONITORING_PRIORITY_UNKNOWN


# ---------------------------------------------------------------------------
# Temporal comparison using R3 partial dates (matrix §3.8)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TemporalComparison:
    """Outcome of comparing two R3-normalized partial dates.

    Comparison is only valid on the **shared precision** of both dates.
    If shared precision is insufficient to determine ordering or window
    membership, ``comparable`` is ``False`` and the caller must fall back
    to ``boundary`` or ``not_evaluable`` (matrix §3.8).
    """

    comparable: bool
    same_period: bool
    within_tolerance: bool
    shared_precision: str  # "day" | "month" | "year" | "none"
    uncertainty: str

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "comparable": self.comparable,
            "same_period": self.same_period,
            "within_tolerance": self.within_tolerance,
            "shared_precision": self.shared_precision,
            "uncertainty": self.uncertainty,
        }


def _precision_level(norm: Optional[NormalizedValue]) -> str:
    """Return the precision level of a normalized date: day/month/year/none."""
    if norm is None or not norm.normalized:
        return "none"
    normalized = str(norm.normalized)
    parts = normalized.split("-")
    if len(parts) >= 3 and len(parts[2]) == 2:
        return "day"
    if len(parts) >= 2:
        return "month"
    if len(parts) >= 1 and len(parts[0]) == 4:
        return "year"
    return "none"


def _shared_precision(a: str, b: str) -> str:
    """Return the finest precision shared by two precision levels."""
    order = {"day": 3, "month": 2, "year": 1, "none": 0}
    return a if order[a] <= order[b] else b


def compare_partial_dates(
    date_a: Optional[NormalizedValue],
    date_b: Optional[NormalizedValue],
    tolerance: TemporalTolerance,
) -> TemporalComparison:
    """Compare two R3-normalized partial dates on their shared precision.

    Fails closed: if either date is missing/unsupported, or if the shared
    precision is insufficient to determine whether the dates are within
    tolerance, ``comparable`` is ``False``.
    """
    if date_a is None or date_b is None:
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty="one or both dates missing")
    if date_a.quality in ("unsupported", "missing"):
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty=f"date_a quality={date_a.quality}")
    if date_b.quality in ("unsupported", "missing"):
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty=f"date_b quality={date_b.quality}")

    norm_a = str(date_a.normalized) if date_a.normalized else ""
    norm_b = str(date_b.normalized) if date_b.normalized else ""
    if not norm_a or not norm_b:
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty="one or both normalized values empty")

    prec_a = _precision_level(date_a)
    prec_b = _precision_level(date_b)
    shared = _shared_precision(prec_a, prec_b)

    if shared == "none":
        return TemporalComparison(
            comparable=False, same_period=False, within_tolerance=False,
            shared_precision="none",
            uncertainty="no shared date precision")

    # Compare at the shared precision level.
    if shared == "year":
        same = norm_a[:4] == norm_b[:4]
        return TemporalComparison(
            comparable=True, same_period=same, within_tolerance=same,
            shared_precision="year",
            uncertainty="compared at year precision only")

    if shared == "month":
        same = norm_a[:7] == norm_b[:7]
        return TemporalComparison(
            comparable=True, same_period=same, within_tolerance=same,
            shared_precision="month",
            uncertainty="compared at month precision only")

    # shared == "day": full comparison possible.
    if norm_a[:10] == norm_b[:10]:
        if not tolerance.same_day:
            return TemporalComparison(
                comparable=True, same_period=True, within_tolerance=False,
                shared_precision="day",
                uncertainty="same-day matching disabled by strategy")
        return TemporalComparison(
            comparable=True, same_period=True, within_tolerance=True,
            shared_precision="day", uncertainty="")

    # Different days: apply tolerance if provided.
    if tolerance.tolerance_days is not None:
        import datetime
        try:
            da = datetime.date.fromisoformat(norm_a[:10])
            db = datetime.date.fromisoformat(norm_b[:10])
            delta = abs((da - db).days)
            within = delta <= tolerance.tolerance_days
            return TemporalComparison(
                comparable=True, same_period=False,
                within_tolerance=within,
                shared_precision="day",
                uncertainty=f"day delta={delta}, "
                            f"tolerance={tolerance.tolerance_days}")
        except (ValueError, TypeError):
            return TemporalComparison(
                comparable=False, same_period=False, within_tolerance=False,
                shared_precision="day",
                uncertainty="could not parse day-precision dates for delta")
    # No tolerance: different days are not within tolerance.
    return TemporalComparison(
        comparable=True, same_period=False, within_tolerance=False,
        shared_precision="day",
        uncertainty="different days, no tolerance applied")


# ---------------------------------------------------------------------------
# Evaluation result types
# ---------------------------------------------------------------------------

class AEMHSliceError(Exception):
    """An AE/MH slice evaluation invariant was violated."""


@dataclass(frozen=True)
class AEMHUnitResult:
    """The evaluation outcome for one D01 EvaluationUnit.

    Bundles the L1 disposition, L1b evidence items, source-record refs,
    candidate refs, risk-instance refs, query refs, journey markers and
    the medical grading -- all bound to the same ``unit_id`` and source
    locators.
    """
    unit_id: str
    subject_ref: str
    l1_disposition: str
    medical_grading: MedicalGrading
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    journey_markers: Tuple[Dict[str, Any], ...] = ()
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    not_evaluable_reason: str = ""
    boundary_reason: str = ""

    @property
    def monitoring_priority(self) -> str:
        """Neutral monitoring-priority accessor (frozen D02 contract §2):
        projects ``medical_grading.monitoring_priority`` so the lifecycle
        adapter and ``RiskDomainUnitResult`` consumers read priority off
        any domain result without importing a domain-specific grading
        type.  D01 behavior is unchanged -- this is a read-only view of
        the existing field."""
        return self.medical_grading.monitoring_priority

    def all_source_locator_ids(self) -> Tuple[str, ...]:
        ids: List[str] = []
        for ref in self.source_record_refs:
            ids.append(ref.locator.locator_id())
        for item in self.evidence:
            ids.append(item.locator.locator_id())
        for ref in self.risk_candidate_refs:
            if ref.locator is not None:
                ids.append(ref.locator.locator_id())
        return tuple(sorted(set(ids)))

    def to_unit_evaluation(
        self,
        *,
        l0_status: str = L0CoverageStatus.COVERED,
        provenance_snapshot_id: str = "",
        provenance_rule_lineage: str = "",
    ) -> UnitEvaluation:
        """Build a worker_01 :class:`UnitEvaluation` from this result using
        caller-supplied L0/provenance (finding 5).

        This is a bounded conversion/validation surface that exercises the
        real common-contract join invariants.  The caller must supply
        ``provenance_snapshot_id`` for non-not_evaluable dispositions and
        ``provenance_rule_lineage`` for positive/boundary dispositions.
        """
        polarities: List[str] = []
        for ev in self.evidence:
            if ev.polarity in (
                    L1bEvidencePolarity.SUPPORTING,
                    L1bEvidencePolarity.COUNTEREVIDENCE,
                    L1bEvidencePolarity.CONTEXT):
                if ev.polarity not in polarities:
                    polarities.append(ev.polarity)
        return UnitEvaluation(
            unit_id=self.unit_id,
            l0_status=l0_status,
            l1_disposition=self.l1_disposition,
            l1b_polarities=tuple(polarities),
            evidence=self.evidence,
            source_record_refs=self.source_record_refs,
            risk_candidate_refs=self.risk_candidate_refs,
            risk_instance_refs=self.risk_instance_refs,
            query_refs=self.query_refs,
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=self.not_evaluable_reason,
        )


@dataclass(frozen=True)
class AEMHSliceResult:
    """Aggregate result of evaluating one or more D01 units for a subject."""

    subject_ref: str
    unit_results: Tuple[AEMHUnitResult, ...]
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    protocol_boundary: ProtocolAEMHBoundary = None  # type: ignore[assignment]
    match_strategy: EventMatchStrategy = None  # type: ignore[assignment]
    rule_lineage: str = ""

    @property
    def candidate_count(self) -> int:
        return len(self.r2_candidates)

    @property
    def positive_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.POSITIVE)

    @property
    def negative_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.NEGATIVE)

    @property
    def boundary_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.BOUNDARY)

    @property
    def not_evaluable_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.NOT_EVALUABLE)

    @property
    def not_applicable_count(self) -> int:
        return sum(
            1 for r in self.unit_results
            if r.l1_disposition == L1Disposition.NOT_APPLICABLE)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_evidence_item(
    evidence_id: str,
    polarity: str,
    record: SemanticRecord,
    rule_lineage: str,
    uncertainty_note: str = "",
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        polarity=polarity,
        locator=record.locator,
        evidence_role=record.role,
        rule_lineage=rule_lineage,
        uncertainty_note=uncertainty_note,
    )


def _make_source_record_ref(record: SemanticRecord) -> SourceRecordRef:
    return SourceRecordRef(
        record_id=record.locator.record_id,
        locator=record.locator,
    )


def _signal_type_for(record: SemanticRecord, grading: MedicalGrading) -> str:
    """R2 RiskCandidate.signal_type for a D01 clue.

    R2 derives the independent SAE/AESI ``clinical_risk_flags`` from this
    public signal surface.  Encode only the flags actually supported by the
    record's seriousness criteria; do not infer AESI merely because the
    semantic role is ``seriousness_clue``.
    """
    if record.role == "symptom_event":
        base = "potential_unreported_ae_symptom"
    elif record.role == "healthcare_encounter":
        base = "potential_unreported_ae_hospitalization"
    elif record.role == "death_event":
        base = "potential_unreported_death_event"
    elif record.role == "seriousness_clue":
        base = "potential_seriousness_clue"
    else:
        base = f"potential_unreported_aemh_{record.role}"

    criteria = set(grading.seriousness_criteria)
    flags: List[str] = []
    if criteria.intersection(_SAE_CRITERIA_TOKENS):
        flags.append("sae")
    if "aesi" in criteria:
        flags.append("aesi")
    if flags:
        return base + "_" + "_".join(flags)
    return base


def _candidate_detail_payload(
    record: SemanticRecord,
    grading: MedicalGrading,
    match_reason: str,
) -> Dict[str, Any]:
    """Detail payload for R2 RiskCandidate, keeping clinical flags separate
    from monitoring priority."""
    return {
        "role": record.role,
        "concept": record.concept,
        "intensity": grading.intensity,
        "intensity_scale": grading.intensity_scale,
        "seriousness_criteria": list(grading.seriousness_criteria),
        "monitoring_priority": grading.monitoring_priority,
        "clinical_risk_flags": sorted(
            set(grading.seriousness_criteria) & set(_CLINICAL_FLAG_TOKENS)),
        "ai_assertion": record.ai_assertion,
        "match_reason": match_reason,
        "locator_id": record.locator.locator_id(),
    }


def _r4_risk_scope(
    *,
    record: SemanticRecord,
    unit: EvaluationUnit,
    rule_lineage: str,
) -> List[str]:
    """Deterministic R4 scope list for a D01 risk identity (matrix §3.6).

    Scope carries the dimensions that, together with the classifier, make
    the public R2 identity exact and stable.  Lineage/version inputs live
    in the scope so a rule/mapping/knowledge/algorithm change produces a
    *different* identity for the same stable clinical event (detectable
    as a supersede), while a different concept or source event changes
    the classifier (genuinely different identity).
    """
    norm = record.normalized_date()
    date_detail = norm.detail if norm else "none"
    return sorted({
        f"site:{record.site_ref}" if record.site_ref else "site:",
        f"tw:{unit.temporal_window}",
        f"dp:{date_detail}",
        f"ul:{unit.rule_or_knowledge_lineage}",
        f"ua:{unit.unit_algorithm_version}",
        f"rl:{rule_lineage}",
    })


def _stable_source_event_key(record: SemanticRecord) -> str:
    """Stable source/event identity key that survives snapshot/revision
    changes (Codex round-3 finding 1).

    Binds the semantic source role (``table_semantic``) and the stable
    record/event id (``record_id``) -- never ``snapshot_id`` or
    ``source_revision_id``, which change on every export.  This keeps
    the same stable clinical/source event at the same identity across
    N→N+1 exports.  The full locator is kept separately in candidate
    detail for provenance.
    """
    return f"{record.locator.table_semantic}:{record.locator.record_id}"


def _r4_risk_classifier(
    *,
    record: SemanticRecord,
    signal_type: str,
) -> str:
    """Deterministic R4 classifier for a D01 risk identity (matrix §3.6).

    Binds the normalized medical concept, the candidate signal type and
    a *stable* source/event key (semantic role + record/event id) that
    excludes ``snapshot_id`` and ``source_revision_id``.  Two clues with
    the same classifier are the same stable clinical/source event across
    exports; a different concept or different record/event id is a
    genuinely different identity and must NOT keep an old risk alive.
    """
    return "|".join((
        "d01",
        _concept(record),
        signal_type,
        _stable_source_event_key(record),
    ))


def _build_r4_risk_identity(
    *,
    project_id: str,
    subject_ref: str,
    record: SemanticRecord,
    signal_type: str,
    unit: EvaluationUnit,
    rule_lineage: str,
) -> RiskIdentity:
    """Build the *public* R2 :class:`RiskIdentity` for a D01 candidate.

    Uses only :func:`mm_r2.identity.make_risk_identity`.  The same
    dimensions always yield the same deterministic
    ``risk_identity_id``; R4 holds no parallel identity hash.
    """
    return make_risk_identity(
        project_id=project_id,
        subject_ref=subject_ref,
        domain="D01_aemh",
        scope=_r4_risk_scope(record=record, unit=unit, rule_lineage=rule_lineage),
        classifier=_r4_risk_classifier(record=record, signal_type=signal_type),
    )


def _r4_identity_detail(
    *,
    record: SemanticRecord,
    identity: RiskIdentity,
    signal_type: str,
) -> Dict[str, Any]:
    """Identity components stored on the R2 candidate ``detail`` so the
    lifecycle adapter can compare stable cores and lineage fingerprints
    and re-establish with the *exact* public scope/classifier, without
    re-deriving a parallel identity (matrix §3.6).  The full locator is
    kept separately for provenance; it does not enter the identity."""
    return {
        "risk_identity_id": identity.risk_identity_id,
        "stable_core": _r4_risk_classifier(
            record=record, signal_type=signal_type),
        "lineage_fingerprint": "|".join(identity.scope),
        "scope": list(identity.scope),
        "classifier": identity.classifier,
        "domain": identity.domain,
        "stable_source_event_key": _stable_source_event_key(record),
        "full_locator_id": record.locator.locator_id(),
    }

def _build_r2_candidate(
    *,
    project_id: str,
    subject_ref: str,
    record: SemanticRecord,
    grading: MedicalGrading,
    match_reason: str,
    snapshot_id: str,
    rule_lineage: str,
    unit: EvaluationUnit,
) -> Tuple[RiskCandidate, RiskIdentity]:
    """Construct the real R2 :class:`RiskCandidate` and its public
    :class:`RiskIdentity` (finding 4 + identity integration).

    The candidate ``detail`` carries the identity components so the
    lifecycle adapter can compare stable cores and lineage fingerprints
    without a parallel identity hash.  No candidate is established here.
    """
    signal_type = _signal_type_for(record, grading)
    identity = _build_r4_risk_identity(
        project_id=project_id,
        subject_ref=subject_ref,
        record=record,
        signal_type=signal_type,
        unit=unit,
        rule_lineage=rule_lineage,
    )
    detail = _candidate_detail_payload(record, grading, match_reason)
    detail.update(_r4_identity_detail(
        record=record, identity=identity, signal_type=signal_type))
    candidate = RiskCandidate.from_signal(
        project_id=project_id,
        subject_ref=subject_ref,
        domain="D01_aemh",
        signal_type=signal_type,
        source_snapshot_id=snapshot_id,
        rule_activation_id=rule_lineage,
        severity_hint=grading.severity_hint,
        confidence_hint=0.0,
        detail=detail,
    )
    return candidate, identity



def _concept(record: SemanticRecord) -> str:
    return record.concept.strip()



# ---------------------------------------------------------------------------
# Reported-match logic (matrix §4 D01 "误报控制")
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _ReportedMatchOutcome:
    """Result of matching an evidence record against reported AE/MH."""

    matched: bool
    boundary: bool
    not_evaluable: bool
    reason: str
    matched_record: Optional[SemanticRecord] = None


def _match_evidence_to_reported(
    evidence: SemanticRecord,
    reported: Sequence[SemanticRecord],
    strategy: EventMatchStrategy,
    boundary: ProtocolAEMHBoundary,
) -> _ReportedMatchOutcome:
    """Match one evidence record against reported AE/MH source records.

    Returns a match outcome with boundary/not_evaluable flags for partial-
    date or precision-insufficient cases.
    """
    any_boundary = False
    any_not_evaluable = False
    boundary_reason = ""
    ne_reason = ""

    ev_date = evidence.normalized_date()
    ev_concept = _concept(evidence)

    for rep in reported:
        # Concept match (caller-supplied equivalence, no project aliases).
        if not strategy.concepts_match(ev_concept, _concept(rep)):
            continue

        rep_date = rep.normalized_date()
        temporal = compare_partial_dates(ev_date, rep_date,
                                         strategy.temporal_tolerance)

        if not temporal.comparable:
            any_not_evaluable = True
            ne_reason = (
                f"concept matched but dates incomparable: "
                f"{evidence.event_date_raw!r} vs {rep.event_date_raw!r} "
                f"at {temporal.shared_precision} precision "
                f"({temporal.uncertainty})")
            continue

        if temporal.within_tolerance and temporal.shared_precision == "day":
            return _ReportedMatchOutcome(
                matched=True, boundary=False, not_evaluable=False,
                reason=f"evidence matches reported {rep.role} "
                       f"at day precision",
                matched_record=rep)

        # Month/year precision within_tolerance means same period but
        # insufficient day-level detail to confirm the same event ->
        # boundary, not a clean match (matrix §3.8, §4 D01 "误报控制").
        if temporal.within_tolerance and temporal.shared_precision in (
                "month", "year"):
            any_boundary = True
            boundary_reason = (
                f"concept matched and same {temporal.shared_precision} "
                f"but insufficient day precision to confirm same event: "
                f"{evidence.event_date_raw!r} vs {rep.event_date_raw!r}")
            continue

        # Comparable but not within tolerance -> could be a different event
        # or a boundary if precision is coarse.
        if temporal.shared_precision in ("year", "month"):
            any_boundary = True
            boundary_reason = (
                f"concept matched but dates only comparable at "
                f"{temporal.shared_precision} precision: "
                f"{evidence.event_date_raw!r} vs {rep.event_date_raw!r}")
        # If day-precision and outside tolerance, it's a distinct event
        # (not a match, not a boundary) -- continue searching.

    if any_not_evaluable:
        return _ReportedMatchOutcome(
            matched=False, boundary=False, not_evaluable=True,
            reason=ne_reason)
    if any_boundary:
        return _ReportedMatchOutcome(
            matched=False, boundary=True, not_evaluable=False,
            reason=boundary_reason)
    return _ReportedMatchOutcome(
        matched=False, boundary=False, not_evaluable=False,
        reason="no concept-and-temporal match found among reported records")


# ---------------------------------------------------------------------------
# Journey marker construction
# ---------------------------------------------------------------------------

#: Mapping from semantic role to journey event category.
#: Categories are kept distinct (matrix §3.9, §4 D01 "输出"):
#: AE/MH/CM/IP/检查/住院/操作/症状 etc. are never conflated.
_ROLE_TO_JOURNEY_CATEGORY: Dict[str, str] = {
    "reported_ae": "ae",
    "reported_mh": "mh",
    "symptom_event": "symptom",
    "cm_indication": "cm",
    "lab_finding": "lab",
    "exam_finding": "exam",
    "healthcare_encounter": "hospitalization",
    "procedure": "procedure",
    "ip_action": "ip",
    "seriousness_clue": "seriousness",
    "death_event": "death",
    "visit": "visit",
}


def _journey_category(role: str) -> str:
    return _ROLE_TO_JOURNEY_CATEGORY.get(role, "other")


def _build_journey_marker(
    record: SemanticRecord,
    grading: MedicalGrading,
    unit_id: str,
    uncertainty: str = "",
    *,
    is_candidate: bool = False,
    is_boundary_support: bool = False,
) -> Dict[str, Any]:
    """Build one journey projection marker from a semantic record.

    This is projection *data*, not a UI.  The category is a stable
    engineering code; audience labels are produced in ``projection.py``.
    Risk-marker scoping flags (finding 8) are carried so the projection
    layer can mark only candidate, boundary-supporting or serious locators.
    Every marker carries the source ``unit_id`` (finding 6).
    """
    norm = record.normalized_date()
    is_serious = bool(
        grading.has_seriousness_clue
        or grading.monitoring_priority == MONITORING_PRIORITY_HIGH)
    return {
        "unit_id": unit_id,
        "category": _journey_category(record.role),
        "concept": record.concept,
        "role": record.role,
        "source_locator_id": record.locator.locator_id(),
        "record_id": record.locator.record_id,
        "temporal_anchor_raw": record.event_date_raw,
        "temporal_anchor_normalized": str(norm.normalized) if norm and norm.normalized else "",
        "temporal_precision": _precision_level(norm) if norm else "none",
        "visit_label": record.visit_label,
        "phase": record.phase,
        "intensity": grading.intensity,
        "intensity_scale": grading.intensity_scale,
        "seriousness_criteria": list(grading.seriousness_criteria),
        "monitoring_priority": grading.monitoring_priority,
        "ai_assertion": record.ai_assertion,
        "uncertainty": uncertainty or (norm.uncertainty if norm else ""),
        "is_candidate_locator": is_candidate,
        "is_boundary_support_locator": is_boundary_support,
        "is_serious_locator": is_serious,
    }

# ---------------------------------------------------------------------------
# NCS / alternative-diagnosis counterevidence (finding 6)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _CounterevidenceAssessment:
    """Assessment of whether an evidence record is explained away by NCS
    or a confirmed alternative diagnosis (finding 6)."""

    is_combination_counterevidence: bool
    reason: str


def _assess_counterevidence(
    evidence: SemanticRecord,
    grading: MedicalGrading,
) -> _CounterevidenceAssessment:
    """Determine whether NCS or a confirmed alternative diagnosis explains
    away an evidence clue (finding 6).

    NCS is only combination counterevidence when there is no associated
    symptom, medical action/treatment, seriousness clue, or repeat
    worsening.  NCS alone must not become an absolute exclusion.  A
    confirmed alternative diagnosis may be counterevidence but must remain
    source-linked.
    """
    if evidence.has_alternative_diagnosis:
        return _CounterevidenceAssessment(
            is_combination_counterevidence=True,
            reason=(
                f"确认的替代诊断 {evidence.alternative_diagnosis!r} 可作为"
                f"排除依据，但须保留来源链接，不绝对排除"),
        )

    if evidence.is_ncs:
        has_confounder = (
            evidence.role == "symptom_event"
            or evidence.has_medical_action
            or grading.has_seriousness_clue
            or grading.monitoring_priority == MONITORING_PRIORITY_HIGH
            or evidence.intensity.strip().lower() in (
                "severe", "grade 3", "grade4", "grade5",
                "grade 3", "grade 4", "grade 5")
        )
        if has_confounder:
            return _CounterevidenceAssessment(
                is_combination_counterevidence=False,
                reason=(
                    "NCS 不能单独作为排除依据：存在相关症状、医学处置、"
                    "严重性线索或恶化"),
            )
        return _CounterevidenceAssessment(
            is_combination_counterevidence=True,
            reason="明确 NCS 且无相关症状/处置/严重性/恶化，可作为组合反证",
        )

    return _CounterevidenceAssessment(
        is_combination_counterevidence=False, reason="")


# ---------------------------------------------------------------------------
# Query construction helpers (finding 9)
# ---------------------------------------------------------------------------
def _query_basis_text(
    boundary: ProtocolAEMHBoundary,
    strategy: EventMatchStrategy,
) -> str:
    """Audience-readable Query basis identifying the versioned protocol
    boundary and match strategy (finding 9).

    Returns the basis text WITHOUT the ``依据：`` prefix; the projection
    layer adds exactly one ``依据：`` prefix (finding 5)."""
    return (
        f"方案 AE/MH 报告边界 {boundary.boundary_id} "
        f"(v{boundary.version})，事件匹配策略 {strategy.strategy_id} "
        f"(v{strategy.version})")


def _query_finding_text(
    subject_ref: str,
    concept: str,
) -> str:
    """Query finding uses concrete medical wording (finding 9)."""
    return (
        f"受试者 {subject_ref} 的 {concept} 在当前 AE/MH 中未发现对应记录，"
        f"可能为 AE/MH 漏报")


def _query_action_text() -> str:
    return "请核实是否为 AE/MH 漏报，并补充或说明原始记录"


# ---------------------------------------------------------------------------
# Core evaluation: evaluate_aemh_unit
# ---------------------------------------------------------------------------

def evaluate_aemh_unit(
    unit: EvaluationUnit,
    record_set: SemanticRecordSet,
    protocol_boundary: ProtocolAEMHBoundary,
    match_strategy: EventMatchStrategy,
    *,
    project_id: str,
    rule_lineage: str,
    run_id: str = "",
    snapshot_id: str = "",
    unit_algorithm_version: str = "",
    existing_risk_instances: Sequence[RiskInstanceRef] = (),
) -> AEMHUnitResult:
    """Evaluate one D01 AE/MH :class:`EvaluationUnit`.

    Produces one L1 disposition with source-linked evidence, candidates,
    Query refs and journey markers.  The function never establishes or
    closes R2 lifecycle; it produces R2 :class:`RiskCandidate` values for
    worker_03 / ``RiskLifecycle`` to register.
    """
    # -- Validate required inputs -------------------------------------------
    if not isinstance(unit, EvaluationUnit):
        raise AEMHSliceError("unit must be an EvaluationUnit")
    if not isinstance(record_set, SemanticRecordSet):
        raise AEMHSliceError("record_set must be a SemanticRecordSet")
    if not isinstance(protocol_boundary, ProtocolAEMHBoundary):
        raise AEMHSliceError(
            "protocol_boundary must be a ProtocolAEMHBoundary")
    if not isinstance(match_strategy, EventMatchStrategy):
        raise AEMHSliceError("match_strategy must be an EventMatchStrategy")

    unit_id = unit.unit_id
    subject_ref = record_set.subject_ref

    # -- Finding 1: Check all five required roles are satisfied -------------
    missing_roles = record_set.missing_required_roles()
    if missing_roles:
        missing_str = "、".join(missing_roles)
        return AEMHUnitResult(
            unit_id=unit_id,
            subject_ref=subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            medical_grading=MedicalGrading(),
            not_evaluable_reason=(
                f"必需语义角色缺失或未覆盖：{missing_str}，"
                f"无法完成 AE/MH 评价"),
        )

    # -- Finding 3: versioned explicit non-applicability --------------------
    if not protocol_boundary.applicable:
        return AEMHUnitResult(
            unit_id=unit_id,
            subject_ref=subject_ref,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            medical_grading=MedicalGrading(),
        )

    # -- Finding 2: Resolve protocol anchors --------------------------------
    anchors = _resolve_protocol_anchors(record_set, protocol_boundary)

    evidence_records = record_set.evidence_records
    reported = record_set.reported_source_records

    # -- Collect evidence items and source-record refs ----------------------
    evidence_items: List[EvidenceItem] = []
    source_refs: List[SourceRecordRef] = []
    candidate_refs: List[RiskCandidateRef] = []
    query_refs: List[QueryDraftRef] = []
    journey_markers: List[Dict[str, Any]] = []
    r2_candidates: List[RiskCandidate] = []
    candidate_locator_ids: Set[str] = set()
    boundary_support_locator_ids: Set[str] = set()
    boundary_event_reasons: List[str] = []

    # Reported AE/MH become source-record refs + context evidence.
    for idx, rep in enumerate(reported):
        source_refs.append(_make_source_record_ref(rep))
        norm = rep.normalized_date()
        uncertainty = norm.uncertainty if norm else ""
        grading = MedicalGrading(
            intensity=rep.intensity,
            intensity_scale=rep.intensity_scale,
            seriousness_criteria=rep.seriousness_criteria,
            monitoring_priority=derive_monitoring_priority(
                rep.intensity, rep.seriousness_criteria))
        journey_markers.append(
            _build_journey_marker(rep, grading, unit_id, uncertainty))
        evidence_items.append(_make_evidence_item(
            evidence_id=f"ev-rep-{unit_id[:16]}-{idx}",
            polarity=L1bEvidencePolarity.CONTEXT,
            record=rep,
            rule_lineage=rule_lineage,
            uncertainty_note=uncertainty,
        ))

    # -- Scan evidence records for under-reporting clues --------------------
    unmatched_evidence: List[Tuple[SemanticRecord, _ReportedMatchOutcome]] = []
    matched_evidence: List[Tuple[SemanticRecord, SemanticRecord]] = []

    for ev in evidence_records:
        # Protocol exclusion check (concept explicitly excluded from AE).
        if protocol_boundary.is_excluded_concept(_concept(ev)):
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-exc-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.CONTEXT,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note="protocol-excluded concept",
            ))
            grading = MedicalGrading(
                intensity=ev.intensity,
                intensity_scale=ev.intensity_scale,
                seriousness_criteria=ev.seriousness_criteria,
                monitoring_priority=derive_monitoring_priority(
                    ev.intensity, ev.seriousness_criteria))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, "protocol-excluded"))
            continue

        # Finding 2: classify event against the protocol boundary.
        ev_norm = ev.normalized_date()
        boundary_cls = classify_event_against_boundary(ev_norm, anchors)
        if boundary_cls.classification == "not_evaluable":
            return AEMHUnitResult(
                unit_id=unit_id,
                subject_ref=subject_ref,
                l1_disposition=L1Disposition.NOT_EVALUABLE,
                medical_grading=MedicalGrading(),
                evidence=tuple(evidence_items),
                source_record_refs=tuple(source_refs),
                journey_markers=tuple(journey_markers),
                not_evaluable_reason=boundary_cls.reason,
            )

        # Events outside the reporting window at sufficient precision are
        # not AE/MH under-reporting clues; they become context evidence.
        if boundary_cls.classification == "outside":
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-out-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.CONTEXT,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note="事件在方案报告窗口外",
            ))
            grading = MedicalGrading(
                intensity=ev.intensity,
                intensity_scale=ev.intensity_scale,
                seriousness_criteria=ev.seriousness_criteria,
                monitoring_priority=derive_monitoring_priority(
                    ev.intensity, ev.seriousness_criteria))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, "事件在方案报告窗口外"))
            continue

        is_boundary_event = boundary_cls.classification == "boundary"
        if is_boundary_event:
            boundary_support_locator_ids.add(ev.locator.locator_id())
            if boundary_cls.reason:
                boundary_event_reasons.append(boundary_cls.reason)

        match_outcome = _match_evidence_to_reported(
            ev, reported, match_strategy, protocol_boundary)

        grading = MedicalGrading(
            intensity=ev.intensity,
            intensity_scale=ev.intensity_scale,
            seriousness_criteria=ev.seriousness_criteria,
            monitoring_priority=derive_monitoring_priority(
                ev.intensity, ev.seriousness_criteria))

        if match_outcome.matched and match_outcome.matched_record is not None:
            matched_evidence.append((ev, match_outcome.matched_record))
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-mat-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note=match_outcome.reason,
            ))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, match_outcome.reason,
                    is_boundary_support=is_boundary_event))
            continue

        # Finding 6: NCS / alternative-diagnosis counterevidence.
        ce_assessment = _assess_counterevidence(ev, grading)
        if ce_assessment.is_combination_counterevidence:
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-ce-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note=ce_assessment.reason,
            ))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, ce_assessment.reason,
                    is_boundary_support=is_boundary_event))
            continue

        if match_outcome.not_evaluable:
            unmatched_evidence.append((ev, match_outcome))
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-ne-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.SUPPORTING,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note=match_outcome.reason,
            ))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, match_outcome.reason,
                    is_boundary_support=is_boundary_event))
            continue

        if match_outcome.boundary:
            unmatched_evidence.append((ev, match_outcome))
            evidence_items.append(_make_evidence_item(
                evidence_id=f"ev-bnd-{unit_id[:16]}-{ev.locator.record_id}",
                polarity=L1bEvidencePolarity.SUPPORTING,
                record=ev,
                rule_lineage=rule_lineage,
                uncertainty_note=match_outcome.reason,
            ))
            journey_markers.append(
                _build_journey_marker(
                    ev, grading, unit_id, match_outcome.reason,
                    is_boundary_support=True))
            continue

        # No match found: this is a potential under-reporting clue.
        # Finding 4 + identity integration: build the real R2
        # RiskCandidate once with its public R2 RiskIdentity.
        r2_cand, r2_identity = _build_r2_candidate(
            project_id=project_id,
            subject_ref=subject_ref,
            record=ev,
            grading=grading,
            match_reason=match_outcome.reason,
            snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            unit=unit,
        )
        r2_candidates.append(r2_cand)
        cand_ref = RiskCandidateRef(
            candidate_id=r2_cand.candidate_id,
            risk_identity_id=r2_identity.risk_identity_id,
            locator=ev.locator,
        )
        candidate_refs.append(cand_ref)
        candidate_locator_ids.add(ev.locator.locator_id())
        evidence_items.append(_make_evidence_item(
            evidence_id=f"ev-clue-{unit_id[:16]}-{ev.locator.record_id}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            record=ev,
            rule_lineage=rule_lineage,
            uncertainty_note="no matching reported AE/MH found",
        ))
        journey_markers.append(
            _build_journey_marker(
                ev, grading, unit_id, "potential under-reporting clue",
                is_candidate=True,
                is_boundary_support=is_boundary_event))
        unmatched_evidence.append((ev, match_outcome))

    # -- Determine L1 disposition -------------------------------------------
    l1_disposition, boundary_reason, ne_reason = _determine_l1_disposition(
        unmatched_evidence=unmatched_evidence,
        matched_evidence=matched_evidence,
        candidate_refs=candidate_refs,
        reported=reported,
        evidence_records=evidence_records,
        protocol_boundary=protocol_boundary,
        anchors=anchors,
        record_set=record_set,
        boundary_support_locator_ids=boundary_support_locator_ids,
        boundary_event_reasons=boundary_event_reasons,
    )

    # Finding 9: Build Query drafts with audience-readable basis and
    # minimal locator sets.
    if l1_disposition in (L1Disposition.POSITIVE, L1Disposition.BOUNDARY):
        basis_text = _query_basis_text(protocol_boundary, match_strategy)
        for cand_ref in candidate_refs:
            # Minimal locator set: candidate locator + its supporting
            # evidence locator only.
            ev_for_cand = [
                item for item in evidence_items
                if item.locator.locator_id() == cand_ref.locator.locator_id()]
            minimal_locators: Set[str] = {cand_ref.locator.locator_id()}
            for item in ev_for_cand:
                minimal_locators.add(item.locator.locator_id())
            # Find concept by matching locator in record_set.
            ev_concept = "医学事件"
            for rec in record_set.records:
                if rec.locator.locator_id() == cand_ref.locator.locator_id():
                    ev_concept = _concept(rec)
                    break
            query_refs.append(QueryDraftRef(
                query_id=f"qry-{cand_ref.candidate_id[:28]}",
                unit_id=unit_id,
                basis=basis_text,
                finding=_query_finding_text(subject_ref, ev_concept),
                action=_query_action_text(),
                source_locator_ids=tuple(sorted(minimal_locators)),
                linked_candidate_id=cand_ref.candidate_id,
            ))

    # -- Compute aggregate grading ------------------------------------------
    all_grading_signals = (
        [(r.intensity, r.seriousness_criteria) for r in reported]
        + [(r.intensity, r.seriousness_criteria) for r in evidence_records])
    best_intensity = ""
    all_seriousness: Tuple[str, ...] = ()
    best_priority = MONITORING_PRIORITY_UNKNOWN
    for intensity, seriousness in all_grading_signals:
        if seriousness:
            all_seriousness = all_seriousness + tuple(seriousness)
        pri = derive_monitoring_priority(intensity, seriousness)
        if pri == MONITORING_PRIORITY_HIGH:
            best_priority = MONITORING_PRIORITY_HIGH
        elif (pri == MONITORING_PRIORITY_MEDIUM
              and best_priority != MONITORING_PRIORITY_HIGH):
            best_priority = MONITORING_PRIORITY_MEDIUM
        elif (pri == MONITORING_PRIORITY_LOW
              and best_priority not in (
                  MONITORING_PRIORITY_HIGH, MONITORING_PRIORITY_MEDIUM)):
            best_priority = MONITORING_PRIORITY_LOW
        if intensity and not best_intensity:
            best_intensity = intensity

    aggregate_grading = MedicalGrading(
        intensity=best_intensity,
        seriousness_criteria=all_seriousness,
        monitoring_priority=best_priority,
    )

    return AEMHUnitResult(
        unit_id=unit_id,
        subject_ref=subject_ref,
        l1_disposition=l1_disposition,
        medical_grading=aggregate_grading,
        evidence=tuple(evidence_items),
        source_record_refs=tuple(source_refs),
        risk_candidate_refs=tuple(candidate_refs),
        risk_instance_refs=tuple(existing_risk_instances),
        query_refs=tuple(query_refs),
        journey_markers=tuple(journey_markers),
        r2_candidates=tuple(r2_candidates),
        not_evaluable_reason=ne_reason,
        boundary_reason=boundary_reason,
    )

def _determine_l1_disposition(
    *,
    unmatched_evidence: Sequence[Tuple[SemanticRecord, _ReportedMatchOutcome]],
    matched_evidence: Sequence[Tuple[SemanticRecord, SemanticRecord]],
    candidate_refs: Sequence[RiskCandidateRef],
    reported: Sequence[SemanticRecord],
    evidence_records: Sequence[SemanticRecord],
    protocol_boundary: ProtocolAEMHBoundary,
    anchors: ProtocolAnchorDates,
    record_set: SemanticRecordSet,
    boundary_support_locator_ids: Set[str],
    boundary_event_reasons: Sequence[str],
) -> Tuple[str, str, str]:
    """Determine the L1 disposition and return (disposition, boundary_reason,
    not_evaluable_reason)."""
    # (has_subject / has_temporal / required-role checks are handled earlier
    # in evaluate_aemh_unit, before this function is called.)

    # Check for not_evaluable date conflicts.
    has_ne = any(
        outcome.not_evaluable for _, outcome in unmatched_evidence)
    if has_ne:
        reasons = [
            outcome.reason for _, outcome in unmatched_evidence
            if outcome.not_evaluable]
        return (
            L1Disposition.NOT_EVALUABLE, "",
            "；".join(reasons))

    # Check for boundary date conflicts from match outcomes.
    has_match_boundary = any(
        outcome.boundary for _, outcome in unmatched_evidence)

    # F1: Check if any candidate was created from a boundary-classified
    # event.  If so, the unit disposition must be BOUNDARY, not POSITIVE.
    has_boundary_event_candidate = any(
        cand.locator is not None
        and cand.locator.locator_id() in boundary_support_locator_ids
        for cand in candidate_refs)

    # If there are unmatched clues (candidates), the unit is positive or
    # boundary.
    if candidate_refs:
        if has_match_boundary or has_boundary_event_candidate:
            specific_reasons = list(dict.fromkeys(
                list(boundary_event_reasons) + [
                    outcome.reason for _, outcome in unmatched_evidence
                    if outcome.boundary and outcome.reason
                ]
            ))
            return (
                L1Disposition.BOUNDARY,
                "；".join(specific_reasons) if specific_reasons else (
                    "存在疑似 AE/MH 漏报线索，同时部分日期精度不足以确定"
                    "是否在方案报告窗口内或与已记录事件匹配"
                ),
                "")
        return (L1Disposition.POSITIVE, "", "")

    # No unmatched clues. Check if all evidence was matched or excluded.
    if has_match_boundary or has_boundary_event_candidate:
        boundary_reasons = [
            outcome.reason for _, outcome in unmatched_evidence
            if outcome.boundary]
        return (
            L1Disposition.BOUNDARY,
            "；".join(boundary_reasons) if boundary_reasons
            else "部分日期跨界，尚不能确定匹配关系",
            "")

    # All evidence matched or no evidence records.
    if evidence_records and not unmatched_evidence:
        # All evidence matched to reported records.
        return (L1Disposition.NEGATIVE, "", "")

    if not evidence_records and reported:
        # No evidence roles, only reported records -- the unit evaluated
        # the reported records and found nothing to flag.
        return (L1Disposition.NEGATIVE, "", "")

    if not evidence_records and not reported:
        # No records at all for this unit.  This is not_evaluable unless
        # the protocol proves the unit is out of scope.
        return (
            L1Disposition.NOT_EVALUABLE, "",
            "该评价单元无 AE/MH 记录且无证据记录，无法完成评价")

    # Default: negative (all evidence matched or explained).
    return (L1Disposition.NEGATIVE, "", "")


# ---------------------------------------------------------------------------
# Slice-level evaluation
# ---------------------------------------------------------------------------

def evaluate_aemh_slice(
    units: Sequence[EvaluationUnit],
    record_sets: Mapping[str, SemanticRecordSet],
    protocol_boundary: ProtocolAEMHBoundary,
    match_strategy: EventMatchStrategy,
    *,
    project_id: str,
    rule_lineage: str,
    run_id: str = "",
    snapshot_id: str = "",
    unit_algorithm_version: str = "",
) -> Dict[str, AEMHSliceResult]:
    """Evaluate multiple D01 units, one per subject.

    Returns a mapping of ``subject_ref -> AEMHSliceResult``.  Each unit is
    evaluated independently; the function does not merge or split risk
    identities (that is worker_03 / R2 lifecycle territory).
    """
    if not isinstance(protocol_boundary, ProtocolAEMHBoundary):
        raise AEMHSliceError(
            "protocol_boundary must be a ProtocolAEMHBoundary")
    if not isinstance(match_strategy, EventMatchStrategy):
        raise AEMHSliceError("match_strategy must be an EventMatchStrategy")

    results: Dict[str, AEMHSliceResult] = {}
    for unit in units:
        scope_key = unit.scope_key
        record_set = record_sets.get(scope_key)
        if record_set is None:
            # No records for this subject -- still produce a result.
            record_set = SemanticRecordSet(
                records=(),
                subject_ref=scope_key,
                scope_key=scope_key,
            )
        unit_result = evaluate_aemh_unit(
            unit=unit,
            record_set=record_set,
            protocol_boundary=protocol_boundary,
            match_strategy=match_strategy,
            project_id=project_id,
            rule_lineage=rule_lineage,
            run_id=run_id,
            snapshot_id=snapshot_id,
            unit_algorithm_version=unit_algorithm_version,
        )
        existing_results = results.get(unit_result.subject_ref)
        unit_results: Tuple[AEMHUnitResult, ...]
        r2_candidates: Tuple[RiskCandidate, ...]
        if existing_results is not None:
            unit_results = existing_results.unit_results + (unit_result,)
            # Finding 4: aggregate all R2 candidates from each unit result.
            r2_candidates = (
                existing_results.r2_candidates + unit_result.r2_candidates)
        else:
            unit_results = (unit_result,)
            r2_candidates = unit_result.r2_candidates
        results[unit_result.subject_ref] = AEMHSliceResult(
            subject_ref=unit_result.subject_ref,
            unit_results=unit_results,
            r2_candidates=r2_candidates,
            protocol_boundary=protocol_boundary,
            match_strategy=match_strategy,
            rule_lineage=rule_lineage,
        )
    return results
