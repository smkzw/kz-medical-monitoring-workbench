"""R4-D03 synthetic study-drug exposure, adherence, accountability and
medical-disposition slice engine.

Frozen source of truth: ``FROZEN_R4_D03_CONTRACT_V1_1`` (§§1-12).  This
module implements the D03 IP domain engine on top of the shared
``RiskDomainUnitResult`` protocol, reusing the accepted R1 coverage, R2
identity/lifecycle, and R3 mapping/rule/knowledge public contracts.  It
provides the versioned non-listing inputs, expected-set expansion, the six
L1 evaluation classes, the three-part Chinese Query drafts, and the
coverage/lifecycle adaptation (protocol-satisfying unit result + full
``UnitEvaluation`` materialization for the ``CoverageLedger``).

Design constraints enforced here (frozen D03 contract):

1. Actual exposure days, treatment span, dose count and amount are distinct;
   the kernel derives exposure days only from ``ExposureOccurrence`` rows,
   never from episode span.
2. The assignment/episode binding is deterministic and lineage-bearing:
   direct link first, derived unique candidate second, zero candidates or
   multiple feasible candidates fail closed (not_evaluable/boundary).
3. Six control items expand per episode; sibling units stay independent and
   an episode rollup preserves ``has_positive/has_boundary/
   has_not_evaluable`` (any not_evaluable blocks domain completeness).
4. Adherence is executable: canonical numerator/denominator, versioned
   window/endpoints, threshold inclusivity, precision, rounding mode,
   compare-before/after-rounding, and fail-closed zero/missing/duplicate
   policies.  The kernel never invents a default formula.
5. Return/dispense coverage follows the frozen §5.4 decision table; zero
   rows and uncovered roles are never conflated.
6. Blinded roles/phases are verifiable without product identity; masked
   dose/identity makes the corresponding control not_evaluable and never
   leaks unapproved actual identity into Query/Journey text.
7. Query text stays Chinese-native and asks to verify whether the issue
   constitutes PD; it never states confirmed PD.

All data is synthetic/offline.  No real project, provider, or product
service.  This module does not implement the final journey projection
(worker_02) or the challenge matrix/root exports (worker_03).
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP
from fractions import Fraction
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from mm_r2.identity import make_risk_identity
from mm_r2.risk import RiskCandidate, RiskIdentity
from mm_r3.normalization import NormalizedValue, normalize_partial_date

from .contracts import (
    L0CoverageStatus,
    EvaluationUnit,
    EvidenceItem,
    L1Disposition,
    L1bEvidencePolarity,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_UNKNOWN,
    QueryDraftRef,
    RiskCandidateRef,
    RiskInstanceRef,
    SourceLocator,
    SourceRecordRef,
    UnitEvaluation,
    VALID_MONITORING_PRIORITIES,
    content_hash,
)

__all__ = [
    "REQUIRED_IP_ROLES",
    "OPTIONAL_IP_ROLES",
    "IP_ROLES",
    "IPSliceError",
    "PlannedTreatmentAssignment",
    "IPExposureEpisode",
    "ExposureOccurrence",
    "ExposureAggregationPolicy",
    "ProtocolExposureRule",
    "AdherenceAlgorithm",
    "AdherenceObservation",
    "PlannedExposureAction",
    "ActualIPAction",
    "IPActionEvidence",
    "AssignmentBindingMapping",
    "D03PriorityPolicy",
    "IPSemanticRecord",
    "IPWindowDescriptor",
    "AssignmentResolution",
    "ExposureDayComputation",
    "compute_actual_exposure_days",
    "resolve_episode_assignment",
    "IPUnitExpanded",
    "IPExpectedSetExpansion",
    "expand_ip_expected_set",
    "IPUnitResult",
    "IPSliceResult",
    "IPEpisodeRollup",
    "evaluate_ip_unit",
    "evaluate_ip_slice",
    "POSITIVE_SUBTYPE_LABELS",
    "positive_subtype_audience_label",
    "D03_DOMAIN",
    "D03_UNIT_ALGO_VERSION",
    "IP_RULE_TYPES",
    "CONTROL_ITEMS",
    "IP_ACTION_TYPES",
    "METRIC_KINDS",
    "CONFIRMATION_CONFIRMED",
    "CONFIRMATION_UNRESOLVED",
]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

D03_DOMAIN = "D03_ip_exposure"
D03_UNIT_ALGO_VERSION = "d03_unit_v1"
D03_RULE_LINEAGE_DEFAULT = "d03-ip-rule-v1"

REQUIRED_IP_ROLES: Tuple[str, ...] = (
    "ip_exposure", "subject_identity", "site_identity", "temporal_anchor",
)

OPTIONAL_IP_ROLES: Tuple[str, ...] = (
    "randomization", "planned_treatment", "study_phase",
    "ip_dispense", "ip_return", "ip_accountability",
    "reported_ae", "lab_finding", "exam_finding", "efficacy_assessment",
    "ip_action_reason", "recorded_cm",
)

IP_ROLES: Tuple[str, ...] = REQUIRED_IP_ROLES + OPTIONAL_IP_ROLES

CONFIRMATION_CONFIRMED = "confirmed"
CONFIRMATION_UNRESOLVED = "unresolved"

ACTION_PAUSE = "pause"
ACTION_DOSE_REDUCE = "dose_reduce"
ACTION_DOSE_INCREASE = "dose_increase"
ACTION_RESUME = "resume"
ACTION_STOP = "stop"

IP_ACTION_TYPES: Tuple[str, ...] = (
    ACTION_PAUSE, ACTION_DOSE_REDUCE, ACTION_DOSE_INCREASE,
    ACTION_RESUME, ACTION_STOP,
)

CONTROL_PLAN_ACTUAL = "plan_actual"
CONTROL_ROLE_PHASE = "role_phase"
CONTROL_ADHERENCE = "adherence"
CONTROL_ALLOWED_ACTION = "allowed_action"
CONTROL_MEDICAL_ACTION = "medical_action"
CONTROL_ACCOUNTABILITY = "accountability"

CONTROL_ITEMS: Tuple[str, ...] = (
    CONTROL_PLAN_ACTUAL, CONTROL_ROLE_PHASE, CONTROL_ADHERENCE,
    CONTROL_ALLOWED_ACTION, CONTROL_MEDICAL_ACTION, CONTROL_ACCOUNTABILITY,
)

RULE_TYPE_PLAN_ACTUAL = "plan_actual"
RULE_TYPE_ALLOWED_ACTION = "allowed_action"
RULE_TYPE_MEDICAL_ACTION = "medical_action"

IP_RULE_TYPES: Tuple[str, ...] = (
    RULE_TYPE_PLAN_ACTUAL, RULE_TYPE_ALLOWED_ACTION,
    RULE_TYPE_MEDICAL_ACTION,
)

EXPOSURE_SEMANTICS_SINGLE = "single_dose"
EXPOSURE_SEMANTICS_CONTINUOUS = "continuous_interval"
EXPOSURE_SEMANTICS_SPAN = "treatment_span"

EXPOSURE_SEMANTICS: Tuple[str, ...] = (
    EXPOSURE_SEMANTICS_SINGLE, EXPOSURE_SEMANTICS_CONTINUOUS,
    EXPOSURE_SEMANTICS_SPAN,
)

METRIC_DAY_RATIO = "day_ratio"
METRIC_DOSE_COUNT_RATIO = "dose_count_ratio"
METRIC_AMOUNT_RATIO = "amount_ratio"
METRIC_ACCOUNTABILITY_PROXY = "accountability_proxy"

METRIC_KINDS: Tuple[str, ...] = (
    METRIC_DAY_RATIO, METRIC_DOSE_COUNT_RATIO, METRIC_AMOUNT_RATIO,
    METRIC_ACCOUNTABILITY_PROXY,
)

ROUNDING_ROUND_HALF_UP = "round_half_up"
ROUNDING_FLOOR = "floor"
ROUNDING_CEILING = "ceiling"

ROUNDING_MODES: Tuple[str, ...] = (
    ROUNDING_ROUND_HALF_UP, ROUNDING_FLOOR, ROUNDING_CEILING,
)

COMPARE_BEFORE_ROUNDING = "before"
COMPARE_AFTER_ROUNDING = "after"

COMPARE_POLICIES: Tuple[str, ...] = (
    COMPARE_BEFORE_ROUNDING, COMPARE_AFTER_ROUNDING,
)

PLANNED_PAUSE_INCLUDED = "included"
PLANNED_PAUSE_EXCLUDED = "excluded_from_denominator"

PLANNED_PAUSE_HANDLINGS: Tuple[str, ...] = (
    PLANNED_PAUSE_INCLUDED, PLANNED_PAUSE_EXCLUDED,
)

OVERLAP_POLICY_UNION_FAIL = "union_fail"
OVERLAP_POLICY_BOUNDARY = "boundary"
OVERLAP_POLICY_SPLIT = "split_at_change"

OVERLAP_POLICIES: Tuple[str, ...] = (
    OVERLAP_POLICY_UNION_FAIL, OVERLAP_POLICY_BOUNDARY,
    OVERLAP_POLICY_SPLIT,
)

DISCLOSURE_OPEN = "open"
DISCLOSURE_MASKED_IDENTITY = "masked_identity"
DISCLOSURE_MASKED_IDENTITY_DOSE = "masked_identity_and_dose"

DISCLOSURE_STATES: Tuple[str, ...] = (
    DISCLOSURE_OPEN, DISCLOSURE_MASKED_IDENTITY,
    DISCLOSURE_MASKED_IDENTITY_DOSE,
)

ASSIGNMENT_LINK_DIRECT = "direct"
ASSIGNMENT_LINK_DERIVED = "derived"
ASSIGNMENT_LINK_NONE = "none"

ASSIGNMENT_LINK_STATUSES: Tuple[str, ...] = (
    ASSIGNMENT_LINK_DIRECT, ASSIGNMENT_LINK_DERIVED, ASSIGNMENT_LINK_NONE,
)

RESOLUTION_BOUND = "bound"
RESOLUTION_MISSING = "missing"
RESOLUTION_AMBIGUOUS = "ambiguous"

DAY_STATUS_COMPLETE = "complete"
DAY_STATUS_NO_OCCURRENCE = "no_occurrence"
DAY_STATUS_AMBIGUOUS = "ambiguous"
DAY_STATUS_BOUNDARY = "boundary"

RETURN_EXPECTED = "expected"
RETURN_NOT_REQUIRED = "not_required"
RETURN_UNKNOWN = "unknown"

RETURN_EXPECTATIONS: Tuple[str, ...] = (
    RETURN_EXPECTED, RETURN_NOT_REQUIRED, RETURN_UNKNOWN,
)

AMOUNT_KIND_EXACT = "exact"
AMOUNT_KIND_ZERO = "zero"
AMOUNT_KIND_RANGE = "range"
AMOUNT_KIND_PARTIAL = "partial"
AMOUNT_KIND_MISSING = "missing"

AMOUNT_KINDS: Tuple[str, ...] = (
    AMOUNT_KIND_EXACT, AMOUNT_KIND_ZERO, AMOUNT_KIND_RANGE,
    AMOUNT_KIND_PARTIAL, AMOUNT_KIND_MISSING,
)

POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH = (
    "planned_actual_exposure_mismatch")
POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH = (
    "treatment_role_or_phase_mismatch")
POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE = "adherence_out_of_range"
POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION = "unsupported_ip_action"
POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT = (
    "medical_trigger_action_inconsistent")
POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY = (
    "ip_accountability_inconsistency")

POSITIVE_SUBTYPES: Tuple[str, ...] = (
    POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH,
    POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH,
    POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE,
    POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION,
    POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT,
    POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY,
)

POSITIVE_SUBTYPE_LABELS: Dict[str, str] = {
    POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH:
        "研究药给药与方案不一致",
    POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH:
        "治疗分组或阶段待核实",
    POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE: "研究药依从性待核实",
    POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION: "给药调整依据待核实",
    POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT:
        "给药处置与医学事件不一致",
    POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY:
        "研究药物核算待核实",
}

#: Frozen §6.2: an ``accountability_proxy`` adherence metric must be
#: annotated in user-visible Query/evidence text as computed from
#: dispense/return accounting and must never be presented as proven actual
#: dosing days.  The exact phrase ``按发放/回收核算`` is the frozen
#: annotation; the disclaimer is deliberately worded without the token
#: ``实际服药天数`` so the proxy can never read as a proven day count.
ACCOUNTABILITY_PROXY_ANNOTATION = (
    "按发放/回收核算（代理口径），不能证明每日实际服药情况")

#: Chinese labels for semantic roles used in coverage-gap reasons.
IP_ROLE_LABELS: Dict[str, str] = {
    "ip_exposure": "研究药暴露",
    "subject_identity": "受试者身份",
    "site_identity": "中心身份",
    "temporal_anchor": "时间锚点",
    "randomization": "随机信息",
    "planned_treatment": "计划治疗",
    "study_phase": "研究阶段",
    "ip_dispense": "发放记录",
    "ip_return": "回收记录",
    "ip_accountability": "药物核算",
    "reported_ae": "不良事件",
    "lab_finding": "实验室检查",
    "exam_finding": "其他检查",
    "efficacy_assessment": "疗效评估",
    "ip_action_reason": "给药调整原因",
    "recorded_cm": "合并用药记录",
}

#: Risk family per control item (stable engineering code, never audience text).
RISK_FAMILY_BY_CONTROL: Dict[str, str] = {
    CONTROL_PLAN_ACTUAL: "plan_actual_exposure",
    CONTROL_ROLE_PHASE: "treatment_role_phase",
    CONTROL_ADHERENCE: "adherence",
    CONTROL_ALLOWED_ACTION: "ip_action",
    CONTROL_MEDICAL_ACTION: "medical_action",
    CONTROL_ACCOUNTABILITY: "ip_accountability",
}

PLAN_ACTUAL_COMPARE_FIELDS: Tuple[str, ...] = (
    "dose", "dose_unit", "dosage_form", "route", "frequency",
)

TRIGGER_ROLES: Tuple[str, ...] = (
    "reported_ae", "lab_finding", "exam_finding", "efficacy_assessment",
)


def positive_subtype_audience_label(subtype: str) -> str:
    if subtype not in POSITIVE_SUBTYPE_LABELS:
        raise IPSliceError(f"unknown positive subtype {subtype!r}")
    return POSITIVE_SUBTYPE_LABELS[subtype]


class IPSliceError(Exception):
    """A D03 IP slice evaluation invariant was violated."""


# ---------------------------------------------------------------------------
# Versioned non-listing inputs (frozen D03 §3.2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlannedTreatmentAssignment:
    """Versioned planned treatment assignment (randomization/treatment arm).

    Carries the plan only: randomization/cohort/phase, planned drug
    identity, dose/form/route/frequency, planned window, content hash,
    assignment lineage, the blinded-safe display label and the disclosure
    state of the *display* surface.  Different phases or roles MUST use
    different assignments; the kernel never guesses between overlapping
    assignments by drug name or nearest date.
    """

    assignment_id: str
    subject_ref: str
    site_ref: str
    treatment_role_token: str
    study_phase: str
    planned_drug_identity: str
    dose: str
    dose_unit: str
    dosage_form: str
    route: str
    frequency: str
    planned_start: str
    planned_end: str
    content_hash: str
    assignment_lineage: str
    display_role_label: str
    period: str = ""
    randomization_token: str = ""
    cohort_token: str = ""
    disclosure_state: str = DISCLOSURE_OPEN
    source_locator: Optional[SourceLocator] = None

    def __post_init__(self) -> None:
        for name, value in (
            ("assignment_id", self.assignment_id),
            ("subject_ref", self.subject_ref),
            ("site_ref", self.site_ref),
            ("treatment_role_token", self.treatment_role_token),
            ("study_phase", self.study_phase),
            ("planned_drug_identity", self.planned_drug_identity),
            ("dose", self.dose),
            ("dose_unit", self.dose_unit),
            ("dosage_form", self.dosage_form),
            ("route", self.route),
            ("frequency", self.frequency),
            ("planned_start", self.planned_start),
            ("planned_end", self.planned_end),
            ("content_hash", self.content_hash),
            ("assignment_lineage", self.assignment_lineage),
            ("display_role_label", self.display_role_label),
        ):
            if not value.strip():
                raise IPSliceError(
                    f"PlannedTreatmentAssignment.{name} is required")
        if self.disclosure_state not in DISCLOSURE_STATES:
            raise IPSliceError(
                f"PlannedTreatmentAssignment.disclosure_state="
                f"{self.disclosure_state!r} invalid")
        if self.source_locator is not None and not isinstance(
                self.source_locator, SourceLocator):
            raise IPSliceError(
                "PlannedTreatmentAssignment.source_locator must be a "
                "SourceLocator or None")


@dataclass(frozen=True)
class IPExposureEpisode:
    """One stable study-drug exposure episode.

    ``span_start``/``span_end`` are the treatment SPAN (first to last
    recorded date); they never prove daily dosing inside the span.  Actual
    exposure days come only from ``ExposureOccurrence`` rows (§6.1).

    ``assignment_link_status``: ``direct`` (authoritative accepted link),
    ``derived`` (unique deterministic mapping), or ``none``.  A
    direct/derived link MUST carry ``assignment_id``.
    """

    episode_key: str
    subject_ref: str
    site_ref: str
    actual_treatment_role: str
    source_locator: SourceLocator
    role_confirmed: bool = False
    study_phase: str = ""
    phase_confirmed: bool = False
    actual_drug_identity: str = ""
    dose: str = ""
    dose_unit: str = ""
    dosage_form: str = ""
    route: str = ""
    frequency: str = ""
    span_start: str = ""
    span_end: str = ""
    span_ongoing: bool = False
    source_semantics: str = EXPOSURE_SEMANTICS_SPAN
    reason: str = ""
    assignment_link_status: str = ASSIGNMENT_LINK_NONE
    assignment_id: str = ""
    assignment_link_lineage: str = ""
    disclosure_state: str = DISCLOSURE_OPEN

    def __post_init__(self) -> None:
        for name, value in (
            ("episode_key", self.episode_key),
            ("subject_ref", self.subject_ref),
            ("site_ref", self.site_ref),
            ("actual_treatment_role", self.actual_treatment_role),
        ):
            if not value.strip():
                raise IPSliceError(f"IPExposureEpisode.{name} is required")
        if not isinstance(self.source_locator, SourceLocator):
            raise IPSliceError(
                "IPExposureEpisode.source_locator must be a SourceLocator")
        if self.source_semantics not in EXPOSURE_SEMANTICS:
            raise IPSliceError(
                f"IPExposureEpisode.source_semantics="
                f"{self.source_semantics!r} invalid")
        if self.assignment_link_status not in ASSIGNMENT_LINK_STATUSES:
            raise IPSliceError(
                f"IPExposureEpisode.assignment_link_status="
                f"{self.assignment_link_status!r} invalid")
        if (self.assignment_link_status in (ASSIGNMENT_LINK_DIRECT,
                                            ASSIGNMENT_LINK_DERIVED)
                and not self.assignment_id.strip()):
            raise IPSliceError(
                "direct/derived assignment link requires assignment_id")
        if (self.assignment_link_status == ASSIGNMENT_LINK_DERIVED
                and not self.assignment_link_lineage.strip()):
            raise IPSliceError(
                "derived assignment link requires assignment_link_lineage "
                "(versioned mapping lineage)")
        if self.disclosure_state not in DISCLOSURE_STATES:
            raise IPSliceError(
                f"IPExposureEpisode.disclosure_state="
                f"{self.disclosure_state!r} invalid")

    @property
    def identity_disclosed(self) -> bool:
        return self.disclosure_state == DISCLOSURE_OPEN

    @property
    def dose_disclosed(self) -> bool:
        return self.disclosure_state in (
            DISCLOSURE_OPEN, DISCLOSURE_MASKED_IDENTITY)

    @property
    def stable_ip_event_key(self) -> str:
        return f"{self.source_locator.table_semantic}:{self.source_locator.record_id}"


@dataclass(frozen=True)
class ExposureOccurrence:
    """One accepted actual-dosing occurrence row.

    ``date_start``/``date_end``: a single date when ``date_end`` is empty
    or equals ``date_start``; otherwise an explicitly declared interval.
    ``continuous_daily`` declares that the source explicitly states daily
    dosing inside the interval; the kernel expands the interval to a day
    set only when the aggregation policy allows it (§6.1).  Occurrences
    are the authoritative source of actual dosing days/counts/dose.
    """

    occurrence_id: str
    episode_key: str
    date_start: str
    source_locator: SourceLocator
    assignment_id: str = ""
    date_end: str = ""
    continuous_daily: bool = False
    dose: str = ""
    dose_unit: str = ""
    route: str = ""
    frequency: str = ""
    accepted_revision: str = ""
    accepted_revision_hash: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("occurrence_id", self.occurrence_id),
            ("episode_key", self.episode_key),
            ("date_start", self.date_start),
        ):
            if not value.strip():
                raise IPSliceError(f"ExposureOccurrence.{name} is required")
        if not isinstance(self.source_locator, SourceLocator):
            raise IPSliceError(
                "ExposureOccurrence.source_locator must be a SourceLocator")


@dataclass(frozen=True)
class ExposureAggregationPolicy:
    """Versioned exposure aggregation policy (§6.1).

    Controls dedup by locator/revision, same-role same-dose interval
    union, multi-dose-per-day counting semantics, overlapping different-
    dose/role conflict handling, continuous-interval expansion eligibility
    and unit conversion.  The kernel never assumes daily dosing inside an
    interval on its own.
    """

    version: str
    content_hash: str
    rationale: str = ""
    input_granularity: str = "occurrence"
    date_start_inclusive: bool = True
    date_end_inclusive: bool = True
    dedup_by_locator_and_revision: bool = True
    union_same_role_same_dose: bool = True
    multi_dose_per_day_counts: str = "day"
    overlap_conflict_policy: str = OVERLAP_POLICY_BOUNDARY
    split_priority_lineage: str = ""
    continuous_interval_expansion_allowed: bool = False
    unit_conversion_rules: Tuple[Tuple[str, str, str], ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("version", self.version),
            ("content_hash", self.content_hash),
        ):
            if not value.strip():
                raise IPSliceError(
                    f"ExposureAggregationPolicy.{name} is required")
        if self.overlap_conflict_policy not in OVERLAP_POLICIES:
            raise IPSliceError(
                f"ExposureAggregationPolicy.overlap_conflict_policy="
                f"{self.overlap_conflict_policy!r} invalid")
        if (self.overlap_conflict_policy == OVERLAP_POLICY_SPLIT
                and not self.split_priority_lineage.strip()):
            raise IPSliceError(
                "split_at_change requires split_priority_lineage "
                "(versioned priority rule lineage)")
        rules = tuple(
            (str(a), str(b), str(c))
            for a, b, c in self.unit_conversion_rules)
        object.__setattr__(self, "unit_conversion_rules", rules)


@dataclass(frozen=True)
class ProtocolExposureRule:
    """Versioned protocol exposure rule (frozen D03 §3.2, §4).

    ``rule_type`` selects the control it feeds: ``plan_actual``,
    ``allowed_action`` or ``medical_action``.  Thresholds/endpoints and
    allowed adjustments are versioned input; the kernel hardcodes no dose
    or adherence formula.
    """

    rule_id: str
    rule_version: str
    clause_locator: str
    rule_content_hash: str
    rule_lineage: str
    rule_type: str
    applicable_treatment_role: str = ""
    applicable_phases: Tuple[str, ...] = ()
    window_start: str = ""
    window_end: str = ""
    window_start_inclusive: Optional[bool] = None
    window_end_inclusive: Optional[bool] = None
    planned_dose: str = ""
    planned_dose_unit: str = ""
    planned_dosage_form: str = ""
    planned_route: str = ""
    planned_frequency: str = ""
    compare_fields: Tuple[str, ...] = ()
    allowed_action_types: Tuple[str, ...] = ()
    allowed_reasons: Tuple[str, ...] = ()
    allowed_dose_after_values: Tuple[str, ...] = ()
    planned_action_required: bool = True
    trigger_role: str = ""
    trigger_concept: str = ""
    expected_actions: Tuple[str, ...] = ()
    priority_on_hit: str = MONITORING_PRIORITY_UNKNOWN
    priority_rationale: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("rule_id", self.rule_id),
            ("rule_version", self.rule_version),
            ("clause_locator", self.clause_locator),
            ("rule_content_hash", self.rule_content_hash),
            ("rule_lineage", self.rule_lineage),
        ):
            if not value.strip():
                raise IPSliceError(f"ProtocolExposureRule.{name} is required")
        if self.rule_type not in IP_RULE_TYPES:
            raise IPSliceError(
                f"ProtocolExposureRule.rule_type={self.rule_type!r} invalid")
        if self.priority_on_hit not in VALID_MONITORING_PRIORITIES:
            raise IPSliceError("ProtocolExposureRule.priority_on_hit invalid")
        if not self.priority_rationale.strip():
            raise IPSliceError("ProtocolExposureRule.priority_rationale required")
        object.__setattr__(self, "applicable_phases",
                           tuple(self.applicable_phases))
        object.__setattr__(self, "compare_fields",
                           tuple(self.compare_fields))
        object.__setattr__(self, "allowed_action_types",
                           tuple(self.allowed_action_types))
        object.__setattr__(self, "allowed_reasons",
                           tuple(self.allowed_reasons))
        object.__setattr__(self, "allowed_dose_after_values",
                           tuple(self.allowed_dose_after_values))
        object.__setattr__(self, "expected_actions",
                           tuple(self.expected_actions))
        if self.rule_type == RULE_TYPE_PLAN_ACTUAL:
            fields = self.compare_fields or PLAN_ACTUAL_COMPARE_FIELDS
            object.__setattr__(self, "compare_fields", fields)
            for fname, value in (
                ("dose", self.planned_dose),
                ("dose_unit", self.planned_dose_unit),
                ("dosage_form", self.planned_dosage_form),
                ("route", self.planned_route),
                ("frequency", self.planned_frequency),
            ):
                if fname in fields and not value.strip():
                    raise IPSliceError(
                        f"plan_actual rule {self.rule_id!r} requires "
                        f"planned_{fname}")
        elif self.compare_fields:
            raise IPSliceError(
                "compare_fields are only valid for plan_actual rules")
        if self.rule_type == RULE_TYPE_ALLOWED_ACTION:
            if not self.allowed_action_types or any(
                    t not in IP_ACTION_TYPES
                    for t in self.allowed_action_types):
                raise IPSliceError(
                    "allowed_action rule requires valid allowed_action_types")
        elif self.allowed_action_types or self.allowed_dose_after_values:
            raise IPSliceError(
                "action fields are only valid for allowed_action rules")
        if self.rule_type == RULE_TYPE_MEDICAL_ACTION:
            if self.trigger_role not in TRIGGER_ROLES:
                raise IPSliceError(
                    "medical_action rule requires trigger_role in "
                    f"{TRIGGER_ROLES}")
            if not self.expected_actions or any(
                    a not in IP_ACTION_TYPES for a in self.expected_actions):
                raise IPSliceError(
                    "medical_action rule requires valid expected_actions")
        elif self.trigger_role or self.trigger_concept or self.expected_actions:
            raise IPSliceError(
                "trigger fields are only valid for medical_action rules")


@dataclass(frozen=True)
class AdherenceAlgorithm:
    """Versioned adherence/accountability algorithm (§6.2).

    Frozen fields: metric kind, numerator/denominator source, canonical
    unit + conversion lineage, window id/start/end + endpoint inclusivity,
    lower/upper threshold + per-side inclusivity, planned
    pause/rescue/makeup/return handling, calculation precision + rounding
    mode + compare-before-or-after-rounding, and zero/missing/duplicate
    observation policies.  Only structured enumeration; no free
    expressions.  ``accountability_proxy`` metrics drive the independent
    accountability control item.
    """

    algorithm_id: str
    version: str
    content_hash: str
    metric_kind: str
    numerator_source: str
    denominator_source: str
    window_id: str = ""
    window_start: str = ""
    window_end: str = ""
    window_start_inclusive: Optional[bool] = True
    window_end_inclusive: Optional[bool] = True
    canonical_unit: str = ""
    conversion_lineage: str = ""
    unit_conversion_rules: Tuple[Tuple[str, str, str], ...] = ()
    lower_threshold: Optional[str] = None
    upper_threshold: Optional[str] = None
    lower_inclusive: Optional[bool] = None
    upper_inclusive: Optional[bool] = None
    planned_pause_handling: str = PLANNED_PAUSE_INCLUDED
    rescue_makeup_handling: str = "included_as_actual"
    return_handling: str = "not_applied"
    calculation_precision: int = 1
    rounding_mode: str = ROUNDING_ROUND_HALF_UP
    compare_before_or_after_rounding: str = COMPARE_BEFORE_ROUNDING
    zero_denominator_policy: str = "not_evaluable"
    missing_item_policy: str = "not_evaluable"
    duplicate_item_policy: str = "not_evaluable"
    rationale: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("algorithm_id", self.algorithm_id),
            ("version", self.version),
            ("content_hash", self.content_hash),
            ("numerator_source", self.numerator_source),
            ("denominator_source", self.denominator_source),
        ):
            if not value.strip():
                raise IPSliceError(f"AdherenceAlgorithm.{name} is required")
        if self.metric_kind not in METRIC_KINDS:
            raise IPSliceError(
                f"AdherenceAlgorithm.metric_kind={self.metric_kind!r} invalid")
        if self.window_id and not (
                self.window_start.strip() and self.window_end.strip()):
            raise IPSliceError(
                "AdherenceAlgorithm window requires window_start and "
                "window_end when window_id is set")
        if self.lower_threshold is None and self.upper_threshold is None:
            raise IPSliceError(
                "AdherenceAlgorithm requires at least one threshold; an "
                "algorithm without an allowed range cannot define "
                "out-of-range")
        for name, value in (
            ("lower_threshold", self.lower_threshold),
            ("upper_threshold", self.upper_threshold),
        ):
            if value is not None:
                try:
                    Decimal(str(value))
                except Exception:
                    raise IPSliceError(
                        f"AdherenceAlgorithm.{name}={value!r} is not a "
                        f"parseable decimal threshold")
        if self.planned_pause_handling not in PLANNED_PAUSE_HANDLINGS:
            raise IPSliceError("AdherenceAlgorithm.planned_pause_handling invalid")
        if self.rounding_mode not in ROUNDING_MODES:
            raise IPSliceError(
                f"AdherenceAlgorithm.rounding_mode={self.rounding_mode!r} invalid")
        if self.compare_before_or_after_rounding not in COMPARE_POLICIES:
            raise IPSliceError(
                "AdherenceAlgorithm.compare_before_or_after_rounding invalid")
        if self.calculation_precision < 0:
            raise IPSliceError("AdherenceAlgorithm.calculation_precision >= 0")
        rules = tuple(
            (str(a), str(b), str(c))
            for a, b, c in self.unit_conversion_rules)
        object.__setattr__(self, "unit_conversion_rules", rules)

    @property
    def is_accountability_proxy(self) -> bool:
        return self.metric_kind == METRIC_ACCOUNTABILITY_PROXY

    @property
    def is_day_ratio(self) -> bool:
        return self.metric_kind == METRIC_DAY_RATIO


@dataclass(frozen=True)
class AdherenceObservation:
    """Window-level raw numerator/denominator observation (§3.2).

    Carries the raw items (values, unit, per-item source locators,
    coverage status and accepted revision), never only a final percentage.
    For ``day_ratio`` the kernel derives numerator days from
    ``ExposureOccurrence``; for dose-count/amount/proxy metrics the raw
    numerator/denominator values are authoritative here.
    """

    observation_id: str
    algorithm_id: str
    window_id: str
    coverage_complete: bool = False
    numerator_value: str = ""
    denominator_value: str = ""
    unit: str = ""
    numerator_source: str = ""
    denominator_source: str = ""
    item_source_locators: Tuple[SourceLocator, ...] = ()
    accepted_revision: str = ""
    source_locator: Optional[SourceLocator] = None

    def __post_init__(self) -> None:
        for name, value in (
            ("observation_id", self.observation_id),
            ("algorithm_id", self.algorithm_id),
            ("window_id", self.window_id),
        ):
            if not value.strip():
                raise IPSliceError(f"AdherenceObservation.{name} is required")
        locs = tuple(
            loc for loc in self.item_source_locators
            if isinstance(loc, SourceLocator))
        object.__setattr__(self, "item_source_locators", locs)
        if self.source_locator is not None and not isinstance(
                self.source_locator, SourceLocator):
            raise IPSliceError(
                "AdherenceObservation.source_locator must be a SourceLocator "
                "or None")


@dataclass(frozen=True)
class PlannedExposureAction:
    """A planned exposure action (pause/reduce/increase/resume/stop)."""

    action_id: str
    action_type: str
    assignment_id: str
    episode_key: str
    action_start: str
    source_locator: Optional[SourceLocator] = None
    action_end: str = ""
    dose_before: str = ""
    dose_after: str = ""
    dose_unit: str = ""
    reason: str = ""
    allowed_condition: str = ""
    confirmation_status: str = CONFIRMATION_CONFIRMED

    def __post_init__(self) -> None:
        self._validate_common()

    def _validate_common(self) -> None:
        for name, value in (
            ("action_id", self.action_id),
            ("action_type", self.action_type),
            ("assignment_id", self.assignment_id),
            ("episode_key", self.episode_key),
            ("action_start", self.action_start),
        ):
            if not value.strip():
                raise IPSliceError(f"{type(self).__name__}.{name} is required")
        if self.action_type not in IP_ACTION_TYPES:
            raise IPSliceError(
                f"{type(self).__name__}.action_type={self.action_type!r} invalid")
        if self.confirmation_status not in (CONFIRMATION_CONFIRMED,
                                            CONFIRMATION_UNRESOLVED):
            raise IPSliceError(
                f"{type(self).__name__}.confirmation_status invalid")
        if self.source_locator is not None and not isinstance(
                self.source_locator, SourceLocator):
            raise IPSliceError(
                f"{type(self).__name__}.source_locator must be a "
                "SourceLocator or None")


@dataclass(frozen=True)
class ActualIPAction:
    """An actual exposure action (pause/reduce/increase/resume/stop)."""

    action_id: str
    action_type: str
    assignment_id: str
    episode_key: str
    action_start: str
    source_locator: Optional[SourceLocator] = None
    action_end: str = ""
    dose_before: str = ""
    dose_after: str = ""
    dose_unit: str = ""
    reason: str = ""
    related_planned_action_id: str = ""
    confirmation_status: str = CONFIRMATION_CONFIRMED

    def __post_init__(self) -> None:
        self._validate_common()

    def _validate_common(self) -> None:
        for name, value in (
            ("action_id", self.action_id),
            ("action_type", self.action_type),
            ("assignment_id", self.assignment_id),
            ("episode_key", self.episode_key),
            ("action_start", self.action_start),
        ):
            if not value.strip():
                raise IPSliceError(f"{type(self).__name__}.{name} is required")
        if self.action_type not in IP_ACTION_TYPES:
            raise IPSliceError(
                f"{type(self).__name__}.action_type={self.action_type!r} invalid")
        if self.confirmation_status not in (CONFIRMATION_CONFIRMED,
                                            CONFIRMATION_UNRESOLVED):
            raise IPSliceError(
                f"{type(self).__name__}.confirmation_status invalid")
        if self.source_locator is not None and not isinstance(
                self.source_locator, SourceLocator):
            raise IPSliceError(
                f"{type(self).__name__}.source_locator must be a "
                "SourceLocator or None")


@dataclass(frozen=True)
class IPActionEvidence:
    """Typed medical-trigger -> IP-action evidence link (frozen D03 §3.2).

    The verified link key is
    ``source_role|stable_source_event_key|subject|site|
    linked_ip_episode_id|relation_type|relation_confirmation``; a public
    ``SourceLocator`` alone never proves the identity relation (§7).
    """

    source_role: str
    stable_source_event_key: str
    subject_ref: str
    site_ref: str
    linked_ip_episode_id: str
    relation_type: str
    source_locator: SourceLocator
    concept: str = ""
    expected_action: str = ""
    actual_action: str = ""
    event_start: str = ""
    event_end: str = ""
    relation_confirmation: str = CONFIRMATION_UNRESOLVED

    def __post_init__(self) -> None:
        for name, value in (
            ("source_role", self.source_role),
            ("stable_source_event_key", self.stable_source_event_key),
            ("subject_ref", self.subject_ref),
            ("site_ref", self.site_ref),
            ("linked_ip_episode_id", self.linked_ip_episode_id),
            ("relation_type", self.relation_type),
        ):
            if not value.strip():
                raise IPSliceError(f"IPActionEvidence.{name} is required")
        if self.source_role not in TRIGGER_ROLES:
            raise IPSliceError(
                f"IPActionEvidence.source_role={self.source_role!r} invalid")
        if not isinstance(self.source_locator, SourceLocator):
            raise IPSliceError(
                "IPActionEvidence.source_locator must be a SourceLocator")
        if self.relation_confirmation not in (CONFIRMATION_CONFIRMED,
                                              CONFIRMATION_UNRESOLVED):
            raise IPSliceError(
                "IPActionEvidence.relation_confirmation invalid")

    @property
    def verified_link_key(self) -> str:
        return "|".join((
            self.source_role, self.stable_source_event_key,
            self.subject_ref, self.site_ref, self.linked_ip_episode_id,
            self.relation_type, self.relation_confirmation,
        ))


@dataclass(frozen=True)
class AssignmentBindingMapping:
    """Versioned assignment-binding mapping (§4 steps 1-3).

    Gates deterministic derivation: only when the mapping explicitly
    allows derived binding and exactly one candidate satisfies
    subject + site + role + phase + unambiguous window is a derived link
    bound.  Version + content hash enter the lineage fingerprint.
    """

    version: str
    content_hash: str
    rationale: str = ""
    allow_derived_binding: bool = True

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise IPSliceError("AssignmentBindingMapping.version is required")
        if not self.content_hash.strip():
            raise IPSliceError(
                "AssignmentBindingMapping.content_hash is required")


@dataclass(frozen=True)
class D03PriorityPolicy:
    """Versioned priority policy for non-rule D03 risks (§8)."""

    version: str
    policy_content_hash: str
    rationale: str = ""
    planned_actual_priority: str = MONITORING_PRIORITY_MEDIUM
    role_phase_priority: str = MONITORING_PRIORITY_HIGH
    adherence_priority: str = MONITORING_PRIORITY_MEDIUM
    unsupported_action_priority: str = MONITORING_PRIORITY_MEDIUM
    medical_action_priority: str = MONITORING_PRIORITY_HIGH
    accountability_priority: str = MONITORING_PRIORITY_MEDIUM

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise IPSliceError("D03PriorityPolicy.version is required")
        if not self.policy_content_hash.strip():
            raise IPSliceError(
                "D03PriorityPolicy.policy_content_hash is required")
        for name, value in (
            ("planned_actual_priority", self.planned_actual_priority),
            ("role_phase_priority", self.role_phase_priority),
            ("adherence_priority", self.adherence_priority),
            ("unsupported_action_priority", self.unsupported_action_priority),
            ("medical_action_priority", self.medical_action_priority),
            ("accountability_priority", self.accountability_priority),
        ):
            if value not in VALID_MONITORING_PRIORITIES:
                raise IPSliceError(f"D03PriorityPolicy.{name}={value!r} invalid")

    def priority_for_subtype(self, subtype: str) -> str:
        if subtype == POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH:
            return self.planned_actual_priority
        if subtype == POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH:
            return self.role_phase_priority
        if subtype == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE:
            return self.adherence_priority
        if subtype == POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION:
            return self.unsupported_action_priority
        if subtype == POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT:
            return self.medical_action_priority
        if subtype == POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY:
            return self.accountability_priority
        return MONITORING_PRIORITY_UNKNOWN


# ---------------------------------------------------------------------------
# Semantic-role record (frozen D03 §3.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPSemanticRecord:
    """One semantic-role listing row (returns, dispenses, CM conflicts).

    Roles come from active mapping, never fixed table names.  ``amount_kind``
    records the return/dispense amount state for the §5.4 decision table:
    ``exact``/``zero`` enter the algorithm, ``range``/``partial`` are
    boundary, ``missing`` is not_evaluable.
    """

    role: str
    concept: str
    locator: SourceLocator
    subject_ref: str = ""
    site_ref: str = ""
    event_start_raw: str = ""
    event_end_raw: str = ""
    amount_value: str = ""
    amount_unit: str = ""
    amount_kind: str = AMOUNT_KIND_MISSING
    treatment_role: str = ""
    action_value: str = ""
    linked_ip_episode_key: str = ""
    relation_type: str = ""
    relationship_confirmation: str = CONFIRMATION_UNRESOLVED
    raw_payload: Mapping[str, Any] = field(default_factory=dict, repr=False)
    ai_assertion: bool = False

    def __post_init__(self) -> None:
        if not self.role.strip():
            raise IPSliceError("IPSemanticRecord.role is required")
        if self.role not in IP_ROLES:
            raise IPSliceError(
                f"IPSemanticRecord.role={self.role!r} not a D03 semantic role")
        if not isinstance(self.locator, SourceLocator):
            raise IPSliceError("locator must be a SourceLocator")
        if self.amount_kind not in AMOUNT_KINDS:
            raise IPSliceError(
                f"IPSemanticRecord.amount_kind={self.amount_kind!r} invalid")
        if self.relationship_confirmation not in (CONFIRMATION_CONFIRMED,
                                                  CONFIRMATION_UNRESOLVED):
            raise IPSliceError("invalid relationship_confirmation")
        object.__setattr__(self, "raw_payload", dict(self.raw_payload))

    @property
    def stable_source_event_key(self) -> str:
        return f"{self.locator.table_semantic}:{self.locator.record_id}"


# ---------------------------------------------------------------------------
# Window descriptor + date helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPWindowDescriptor:
    """Versioned episode-span + control-window descriptor (§4, §7).

    The episode span is the treatment span (never proof of daily dosing);
    the control window belongs to a rule or algorithm and carries its own
    endpoint inclusivity.
    """

    span_start: str = ""
    span_end: str = ""
    span_ongoing: bool = False
    cutoff: str = ""
    window_start: str = ""
    window_end: str = ""
    window_start_inclusive: Optional[bool] = None
    window_end_inclusive: Optional[bool] = None
    applicable_phase: str = ""

    def normalized_span_start(self) -> Optional[NormalizedValue]:
        if not self.span_start.strip():
            return None
        return normalize_partial_date(self.span_start)

    def normalized_span_end(self) -> Optional[NormalizedValue]:
        if self.span_ongoing:
            if not self.cutoff.strip():
                return None
            return normalize_partial_date(self.cutoff)
        if not self.span_end.strip():
            return None
        return normalize_partial_date(self.span_end)

    def temporal_window_descriptor(self) -> str:
        span_end_token = ("ongoing" if self.span_ongoing
                          else (self.span_end or "none"))
        inc: List[str] = []
        if self.window_start_inclusive is True:
            inc.append("si")
        elif self.window_start_inclusive is False:
            inc.append("sx")
        if self.window_end_inclusive is True:
            inc.append("ei")
        elif self.window_end_inclusive is False:
            inc.append("ex")
        inc_token = "-".join(inc) if inc else "inc_unset"
        return (
            f"ep[{self.span_start or 'none'},{span_end_token}]"
            f"|ph[{self.applicable_phase or 'none'}]"
            f"|cw[{self.window_start or 'none'},{self.window_end or 'none'},"
            f"{inc_token}]"
        )


def _prec_rank(p: str) -> int:
    return {"day": 3, "month": 2, "year": 1, "none": 0}.get(p, 0)


def _nv_precision(nv: Optional[NormalizedValue]) -> str:
    if nv is None or not nv.normalized:
        return "none"
    s = str(nv.normalized)
    parts = s.split("-")
    if len(parts) >= 3 and len(parts[2]) == 2:
        return "day"
    if len(parts) >= 2:
        return "month"
    if len(parts) >= 1 and len(parts[0]) == 4:
        return "year"
    return "none"


def _to_day(value: NormalizedValue) -> Optional[Any]:
    """Convert a day-precision NormalizedValue to a datetime.date."""
    if _nv_precision(value) != "day" or not value.normalized:
        return None
    try:
        return datetime.date.fromisoformat(str(value.normalized)[:10])
    except (ValueError, TypeError):
        return None


def _day_range(start: Any, end: Any) -> List[Any]:
    """Inclusive list of dates from start to end."""
    days: List[Any] = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += datetime.timedelta(days=1)
    return days


# ---------------------------------------------------------------------------
# Window-overlap comparison (frozen D03 §7)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _WindowOverlap:
    inside: bool
    outside: bool
    possibly_overlap: bool
    comparable: bool
    boundary_reason: str


def _compare_windows(
    interval: IPWindowDescriptor,
    win_start: str, win_end: str,
    start_inclusive: Optional[bool],
    end_inclusive: Optional[bool],
    *,
    containment: bool = True,
) -> _WindowOverlap:
    """Compare an episode/action window against a control window.

    ``containment=True`` (rule applicability): the episode/action must be
    fully inside the control window; a partial overlap is boundary.
    ``containment=False`` (algorithm computation window): any definite
    overlap evaluates; only a fully disjoint window is not_applicable.

    Full-day precision with explicit inclusivity determines overlap.
    Endpoint equality with unstated inclusivity is boundary.  Partial
    month/year dates that possibly overlap are boundary.  Incomparable
    anchors are not_evaluable.
    """
    span_start = interval.normalized_span_start()
    if span_start is None:
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=False,
            comparable=False, boundary_reason="开始日期缺失或无法解析")
    rw_start = (normalize_partial_date(win_start)
                if win_start.strip() else None)
    rw_end = (normalize_partial_date(win_end)
              if win_end.strip() else None)
    if rw_start is None and rw_end is None:
        return _WindowOverlap(
            inside=True, outside=False, possibly_overlap=False,
            comparable=True, boundary_reason="")
    span_end = interval.normalized_span_end()
    if span_end is None and not interval.span_ongoing:
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason="结束日期缺失；可能落入控制窗口")
    p_start = _nv_precision(span_start)
    p_end = _nv_precision(span_end)
    p_rw_start = _nv_precision(rw_start)
    p_rw_end = _nv_precision(rw_end)
    min_prec = min(_prec_rank(p_start), _prec_rank(p_end),
                   _prec_rank(p_rw_start), _prec_rank(p_rw_end))
    if min_prec < 3:
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason=(
                f"部分日期精度（{p_start}/{p_end}/{p_rw_start}/{p_rw_end}）；"
                f"可能落入控制窗口"))
    cs = _to_day(span_start)
    ce = _to_day(span_end) if span_end else None
    rws = _to_day(rw_start) if rw_start else None
    rwe = _to_day(rw_end) if rw_end else None
    if cs is None or (span_end is not None and ce is None) or (
            rw_start is not None and rws is None) or (
            rw_end is not None and rwe is None):
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=False,
            comparable=False, boundary_reason="全日日期无法解析")
    # Endpoint equality with unstated inclusivity is ambiguous.
    if (start_inclusive is None and rws is not None and cs == rws
            and (containment or rwe is None or ce is None or ce <= rws)):
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason="开始日期恰在控制窗口起点；端点包含关系未声明")
    if (end_inclusive is None and rwe is not None and ce is not None
            and ce == rwe
            and (containment or rws is None or cs >= rwe)):
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True,
            boundary_reason="结束日期恰在控制窗口终点；端点包含关系未声明")
    # Exclusive endpoints: contact at the excluded endpoint is disjoint.
    if (rws is not None and start_inclusive is False and cs == rws
            and ce == rws):
        return _WindowOverlap(
            inside=False, outside=True, possibly_overlap=False,
            comparable=True, boundary_reason="")
    if (rwe is not None and end_inclusive is False and cs == rwe
            and ce == rwe):
        return _WindowOverlap(
            inside=False, outside=True, possibly_overlap=False,
            comparable=True, boundary_reason="")
    # Definite disjointness.
    definitely_outside = False
    if rws is not None and ce is not None:
        definitely_outside = (ce < rws
                              or (ce == rws and start_inclusive is False))
    if rwe is not None:
        definitely_outside = definitely_outside or (
            cs > rwe or (cs == rwe and end_inclusive is False))
    if definitely_outside:
        return _WindowOverlap(
            inside=False, outside=True, possibly_overlap=False,
            comparable=True, boundary_reason="")
    if containment:
        after_start = True
        if rws is not None:
            after_start = (cs >= rws if start_inclusive is not False
                           else cs > rws)
        before_end = True
        if rwe is not None and ce is not None:
            before_end = (ce <= rwe if end_inclusive is not False
                          else ce < rwe)
        if after_start and before_end:
            return _WindowOverlap(
                inside=True, outside=False, possibly_overlap=False,
                comparable=True, boundary_reason="")
        return _WindowOverlap(
            inside=False, outside=False, possibly_overlap=True,
            comparable=True, boundary_reason="区间部分落入控制窗口")
    # Overlap mode: any definite intersection evaluates.
    return _WindowOverlap(
        inside=True, outside=False, possibly_overlap=False,
        comparable=True, boundary_reason="")


def _episode_window(episode: IPExposureEpisode) -> IPWindowDescriptor:
    return IPWindowDescriptor(
        span_start=episode.span_start, span_end=episode.span_end,
        span_ongoing=episode.span_ongoing,
        applicable_phase=episode.study_phase)


def _rule_window(episode: IPExposureEpisode,
                 rule: ProtocolExposureRule) -> IPWindowDescriptor:
    return IPWindowDescriptor(
        span_start=episode.span_start, span_end=episode.span_end,
        span_ongoing=episode.span_ongoing,
        window_start=rule.window_start, window_end=rule.window_end,
        window_start_inclusive=rule.window_start_inclusive,
        window_end_inclusive=rule.window_end_inclusive,
        applicable_phase=episode.study_phase)


def _algorithm_window(episode: IPExposureEpisode,
                      algorithm: AdherenceAlgorithm) -> IPWindowDescriptor:
    return IPWindowDescriptor(
        span_start=episode.span_start, span_end=episode.span_end,
        span_ongoing=episode.span_ongoing,
        window_start=algorithm.window_start,
        window_end=algorithm.window_end,
        window_start_inclusive=algorithm.window_start_inclusive,
        window_end_inclusive=algorithm.window_end_inclusive,
        applicable_phase=episode.study_phase)


# ---------------------------------------------------------------------------
# Assignment binding (frozen D03 §4 steps 1-3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AssignmentResolution:
    """Outcome of binding one episode to a planned treatment assignment."""

    status: str                       # bound | missing | ambiguous
    assignment: Optional[PlannedTreatmentAssignment] = None
    reason: str = ""

    @property
    def is_bound(self) -> bool:
        return self.status == RESOLUTION_BOUND


def resolve_episode_assignment(
    *,
    episode: IPExposureEpisode,
    assignments: Sequence[PlannedTreatmentAssignment],
    binding_mapping: Optional[AssignmentBindingMapping] = None,
) -> AssignmentResolution:
    """Bind an episode to a unique assignment (frozen D03 §4 steps 1-3).

    1. A stable accepted direct/derived link is preferred; the linked
       assignment must exist and share subject + site.
    2. Without a link, only an active mapping that deterministically
       yields exactly one subject+site+role+phase+window candidate may
       derive a binding.
    3. Zero candidates -> missing (not_evaluable); two or more feasible
       candidates -> ambiguous (boundary/not_evaluable).  The kernel never
       picks by drug name, nearest date or input order.
    """
    if not isinstance(episode, IPExposureEpisode):
        raise IPSliceError("episode must be an IPExposureEpisode")
    if episode.assignment_link_status in (ASSIGNMENT_LINK_DIRECT,
                                          ASSIGNMENT_LINK_DERIVED):
        if not episode.assignment_id.strip():
            return AssignmentResolution(
                status=RESOLUTION_MISSING,
                reason="episode 声称存在 assignment 链接但缺少 assignment_id")
        linked = [a for a in assignments
                  if a.assignment_id == episode.assignment_id]
        if not linked:
            return AssignmentResolution(
                status=RESOLUTION_MISSING,
                reason=(f"assignment 链接 {episode.assignment_id!r} 未找到，"
                        f"无法唯一绑定"))
        if len(linked) > 1:
            return AssignmentResolution(
                status=RESOLUTION_AMBIGUOUS,
                reason=(f"assignment 链接 {episode.assignment_id!r} 存在多条"
                        f"记录，无法唯一绑定"))
        candidate = linked[0]
        if (candidate.subject_ref != episode.subject_ref
                or candidate.site_ref != episode.site_ref):
            return AssignmentResolution(
                status=RESOLUTION_MISSING,
                reason=("assignment 链接与 episode 的受试者/中心不一致，"
                        "无法绑定"))
        return AssignmentResolution(
            status=RESOLUTION_BOUND, assignment=candidate)
    # No direct link: derived binding only under an active mapping.
    if binding_mapping is None or not binding_mapping.allow_derived_binding:
        return AssignmentResolution(
            status=RESOLUTION_MISSING,
            reason="episode 无直接 assignment 链接且无允许派生的版本化映射")
    keyed_candidates = [
        a for a in assignments
        if (a.subject_ref == episode.subject_ref
            and a.site_ref == episode.site_ref
            and a.treatment_role_token == episode.actual_treatment_role
            and a.study_phase == episode.study_phase)]
    if not keyed_candidates:
        return AssignmentResolution(
            status=RESOLUTION_MISSING,
            reason=("没有满足 subject+site+role+phase 的 assignment 候选，"
                    "无法确定性绑定"))

    candidates: List[PlannedTreatmentAssignment] = []
    unresolved_ids: List[str] = []
    episode_window = _episode_window(episode)
    for candidate in keyed_candidates:
        overlap = _compare_windows(
            episode_window,
            candidate.planned_start,
            candidate.planned_end,
            True,
            True,
            containment=True,
        )
        if overlap.inside:
            candidates.append(candidate)
        elif not overlap.outside:
            unresolved_ids.append(candidate.assignment_id)

    if unresolved_ids:
        ids = sorted(a.assignment_id for a in candidates) + sorted(
            unresolved_ids)
        return AssignmentResolution(
            status=RESOLUTION_AMBIGUOUS,
            reason=(f"assignment 候选 {ids} 的时间窗存在部分日期、缺失或"
                    "边界重叠，无法证明唯一适用窗口"))
    if not candidates:
        return AssignmentResolution(
            status=RESOLUTION_MISSING,
            reason=("满足 subject+site+role+phase 的 assignment 均与"
                    "episode 时间窗明确不相交，无法确定性绑定"))
    if len(candidates) > 1:
        ids = sorted(a.assignment_id for a in candidates)
        return AssignmentResolution(
            status=RESOLUTION_AMBIGUOUS,
            reason=(f"存在多个可适用 assignment 候选 {ids}，不得按药名、"
                    f"最近日期或输入顺序选择"))
    return AssignmentResolution(status=RESOLUTION_BOUND, assignment=candidates[0])


# ---------------------------------------------------------------------------
# Actual exposure days (frozen D03 §6.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExposureDayComputation:
    """Actual exposure day set derived ONLY from accepted occurrences.

    ``day_set`` holds the unique full-day dates with proven dosing;
    ``status`` is ``complete``/``no_occurrence``/``ambiguous``/``boundary``.
    The episode span is carried for display but never used as dosing proof.
    """

    day_set: Tuple[str, ...]
    status: str
    span_start: str = ""
    span_end: str = ""
    reason: str = ""

    @property
    def actual_exposure_days(self) -> int:
        return len(self.day_set)


def compute_actual_exposure_days(
    *,
    episode: IPExposureEpisode,
    occurrences: Sequence[ExposureOccurrence],
    policy: ExposureAggregationPolicy,
) -> ExposureDayComputation:
    """Compute the actual exposure day set for one episode (§6.1).

    * Dedup by full locator; identical rows collapse, conflicting content
      under one locator or one stable event key with different accepted
      revisions is ambiguous (fail-closed).
    * Single occurrences contribute their explicit date; intervals expand
      to a day set only with explicit continuous-daily semantics AND
      policy permission; otherwise they contribute only their explicit
      endpoints.
    * Same-role same-dose same-semantics overlapping intervals union their
      day sets (never sum interval lengths); different dose/role overlaps
      follow the policy (union_fail -> ambiguous, boundary -> boundary,
      split_at_change -> counted once with the versioned priority rule).
    * Zero occurrences is ``no_occurrence``; the span never implies days.
    """
    episode_occs = [o for o in occurrences
                    if o.episode_key == episode.episode_key]
    # -- dedup / revision selection --------------------------------------
    by_locator: Dict[str, List[ExposureOccurrence]] = {}
    for occ in episode_occs:
        by_locator.setdefault(occ.source_locator.locator_id(), []).append(occ)
    chosen: List[ExposureOccurrence] = []
    for loc_id, rows in by_locator.items():
        payloads = {content_hash((
            occ.date_start, occ.date_end, occ.continuous_daily, occ.dose,
            occ.dose_unit, occ.route, occ.frequency, occ.accepted_revision,
            occ.accepted_revision_hash)) for occ in rows}
        if len(payloads) > 1:
            return ExposureDayComputation(
                day_set=(), status=DAY_STATUS_AMBIGUOUS,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=("同一来源定位出现内容不同的记录，无法确定当前 "
                        "accepted 行"))
        chosen.append(rows[0])
    # Stable event key (table_semantic:record_id) revision conflicts.
    by_event: Dict[str, List[ExposureOccurrence]] = {}
    for occ in chosen:
        by_event.setdefault(
            f"{occ.source_locator.table_semantic}:{occ.source_locator.record_id}",
            []).append(occ)
    accepted: List[ExposureOccurrence] = []
    for key, rows in by_event.items():
        revisions = {r.accepted_revision for r in rows}
        if len(revisions) > 1:
            return ExposureDayComputation(
                day_set=(), status=DAY_STATUS_AMBIGUOUS,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=("同一稳定来源事件存在多个不同 accepted revision，"
                        "无法确定当前 accepted 行"))
        accepted.append(rows[0])
    if not accepted:
        return ExposureDayComputation(
            day_set=(), status=DAY_STATUS_NO_OCCURRENCE,
            span_start=episode.span_start, span_end=episode.span_end,
            reason=("未找到该 episode 的给药记录；不得从治疗跨度推导实际"
                    "给药日，也不得推断漏服"))

    days: Set[Any] = set()
    day_fingerprint: Dict[Any, Set[str]] = {}
    day_interval_covered: Set[Any] = set()
    conflict_reason = ""
    for occ in accepted:
        start = normalize_partial_date(occ.date_start)
        if start is None or _nv_precision(start) != "day":
            return ExposureDayComputation(
                day_set=(), status=DAY_STATUS_AMBIGUOUS,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=(f"给药记录 {occ.occurrence_id!r} 日期缺失或精度不足，"
                        f"无法确定实际给药日"))
        d_start = _to_day(start)
        d_end = d_start
        if occ.date_end.strip() and occ.date_end != occ.date_start:
            end = normalize_partial_date(occ.date_end)
            if end is None or _nv_precision(end) != "day":
                return ExposureDayComputation(
                    day_set=(), status=DAY_STATUS_AMBIGUOUS,
                    span_start=episode.span_start, span_end=episode.span_end,
                    reason=(f"给药记录 {occ.occurrence_id!r} 区间终点缺失或"
                            f"精度不足"))
            d_end = _to_day(end)
        # A true continuous-dosing interval expands to its full day set;
        # every other occurrence contributes only its explicit dates.
        is_expanded_interval = (
            d_end != d_start and occ.continuous_daily
            and policy.continuous_interval_expansion_allowed)
        if d_end == d_start:
            explicit_days = [d_start]
        elif is_expanded_interval:
            explicit_days = _day_range(d_start, d_end)
        else:
            # Interval without continuous-daily declaration contributes
            # only its explicit endpoints (§6.1).
            explicit_days = [d_start, d_end]
        fingerprint = "|".join((
            occ.dose or "-", occ.dose_unit or "-", occ.route or "-",
            occ.frequency or "-", episode.source_semantics,
        ))
        for day in explicit_days:
            days.add(day)
            day_fingerprint.setdefault(day, set()).add(fingerprint)
            if is_expanded_interval:
                day_interval_covered.add(day)
    # -- overlap conflict handling ----------------------------------------
    # Different-dose/role overlaps matter only when a continuous interval
    # covers the day; several single-dose occurrences on the same day are a
    # legitimate multi-dose day (counted once for day purposes, §6.1).
    policy_conflict = False
    for day, fps in day_fingerprint.items():
        if len(fps) > 1 and day in day_interval_covered:
            policy_conflict = True
            break
    if policy_conflict:
        if policy.overlap_conflict_policy == OVERLAP_POLICY_UNION_FAIL:
            return ExposureDayComputation(
                day_set=(), status=DAY_STATUS_AMBIGUOUS,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=("同一日存在不同剂量/单位/途径/频次或来源语义的重叠"
                        "连续给药区间，聚合策略不允许合并"))
        if policy.overlap_conflict_policy == OVERLAP_POLICY_BOUNDARY:
            return ExposureDayComputation(
                day_set=tuple(sorted(day.isoformat() for day in days)),
                status=DAY_STATUS_BOUNDARY,
                span_start=episode.span_start, span_end=episode.span_end,
                reason=("同一日存在不同剂量/角色重叠的连续给药区间，两个可行"
                        "解释均有来源支持"))
        # split_at_change: day counted once; the versioned priority rule
        # (policy.split_priority_lineage) resolves dose identity at change
        # points.  The day set itself is the union.
        conflict_reason = (
            "重叠给药日按版本化优先级规则在变化点拆分，实际给药日按日去重")
    return ExposureDayComputation(
        day_set=tuple(sorted(day.isoformat() for day in days)),
        status=DAY_STATUS_COMPLETE,
        span_start=episode.span_start, span_end=episode.span_end,
        reason=conflict_reason)


# ---------------------------------------------------------------------------
# Identity helpers (frozen D03 §4)
# ---------------------------------------------------------------------------

def _d03_risk_classifier(
    *, episode: IPExposureEpisode, control_token: str,
    risk_family: str, signal_type: str,
) -> str:
    """Deterministic D03 classifier (stable; no versions/hashes/snapshots)."""
    return "|".join((
        "d03", risk_family, episode.episode_key,
        episode.actual_treatment_role or "none",
        control_token, signal_type,
    ))


def _d03_risk_scope(
    *, episode: IPExposureEpisode, window: IPWindowDescriptor,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    binding_mapping: Optional[AssignmentBindingMapping],
) -> List[str]:
    """Deterministic D03 scope/lineage dimensions (site, time precision,
    treatment role, phase, assignment/rule/mapping/algorithm version+hash)."""
    span_start = window.normalized_span_start()
    dp = span_start.detail if span_start else "none"
    parts: Set[str] = {
        f"site:{episode.site_ref}" if episode.site_ref else "site:",
        f"tw:{window.temporal_window_descriptor()}",
        f"dp:{dp}",
        f"role:{episode.actual_treatment_role or 'none'}",
        f"ph:{episode.study_phase or 'none'}",
        f"ua:{D03_UNIT_ALGO_VERSION}",
    }
    if assignment is not None:
        parts.add(f"asg:{assignment.assignment_id}/"
                  f"{assignment.content_hash}/"
                  f"{assignment.assignment_lineage}")
    else:
        parts.add("asg:none")
    if binding_mapping is not None:
        parts.add(f"map:{binding_mapping.version}/"
                  f"{binding_mapping.content_hash}")
    else:
        parts.add("map:none")
    if rule is not None:
        parts.add(f"rule:{rule.rule_id}/{rule.rule_version}/"
                  f"{rule.rule_content_hash}/{rule.rule_lineage}")
    else:
        parts.add("rule:none")
    if algorithm is not None:
        parts.add(f"alg:{algorithm.algorithm_id}/{algorithm.version}/"
                  f"{algorithm.content_hash}")
    else:
        parts.add("alg:none")
    return sorted(parts)


def _build_d03_risk_identity(
    *, project_id: str, episode: IPExposureEpisode,
    window: IPWindowDescriptor, control_token: str,
    risk_family: str, signal_type: str,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    binding_mapping: Optional[AssignmentBindingMapping],
) -> RiskIdentity:
    classifier = _d03_risk_classifier(
        episode=episode, control_token=control_token,
        risk_family=risk_family, signal_type=signal_type)
    scope = _d03_risk_scope(
        episode=episode, window=window, assignment=assignment,
        rule=rule, algorithm=algorithm, binding_mapping=binding_mapping)
    return make_risk_identity(
        project_id=project_id, subject_ref=episode.subject_ref,
        domain=D03_DOMAIN, scope=scope, classifier=classifier)


def _d03_identity_detail(
    *, episode: IPExposureEpisode, identity: RiskIdentity,
    control_token: str, risk_family: str, signal_type: str,
) -> Dict[str, Any]:
    return {
        "risk_identity_id": identity.risk_identity_id,
        "stable_core": _d03_risk_classifier(
            episode=episode, control_token=control_token,
            risk_family=risk_family, signal_type=signal_type),
        "lineage_fingerprint": "|".join(identity.scope),
        "scope": list(identity.scope),
        "classifier": identity.classifier,
        "domain": identity.domain,
        "stable_ip_episode_key": episode.episode_key,
        "full_locator_id": episode.source_locator.locator_id(),
    }


def _build_d03_candidate(
    *, project_id: str, episode: IPExposureEpisode,
    window: IPWindowDescriptor, control_token: str,
    risk_family: str, signal_type: str,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    binding_mapping: Optional[AssignmentBindingMapping],
    snapshot_id: str, monitoring_priority: str,
    match_reason: str, positive_subtype: str = "",
    audience_label: str = "",
) -> Tuple[RiskCandidate, RiskIdentity]:
    identity = _build_d03_risk_identity(
        project_id=project_id, episode=episode, window=window,
        control_token=control_token, risk_family=risk_family,
        signal_type=signal_type, assignment=assignment, rule=rule,
        algorithm=algorithm, binding_mapping=binding_mapping)
    detail: Dict[str, Any] = {
        "risk_family": risk_family,
        "control_item": control_token.split(":", 1)[0],
        "control_token": control_token,
        "signal_type": signal_type,
        "monitoring_priority": monitoring_priority,
        "match_reason": match_reason,
        "positive_subtype": positive_subtype,
        "audience_label": audience_label,
        "treatment_role": episode.actual_treatment_role,
        "phase": episode.study_phase,
        "dose": episode.dose,
        "dose_unit": episode.dose_unit,
        "route": episode.route,
        "frequency": episode.frequency,
        "locator_id": episode.source_locator.locator_id(),
    }
    if assignment is not None:
        detail.update({
            "assignment_id": assignment.assignment_id,
            "assignment_lineage": assignment.assignment_lineage,
            "display_role_label": assignment.display_role_label,
        })
    if rule is not None:
        detail.update({
            "rule_id": rule.rule_id,
            "rule_version": rule.rule_version,
            "rule_clause_locator": rule.clause_locator,
            "rule_type": rule.rule_type,
        })
    if algorithm is not None:
        detail.update({
            "algorithm_id": algorithm.algorithm_id,
            "algorithm_version": algorithm.version,
            "metric_kind": algorithm.metric_kind,
            "window_id": algorithm.window_id,
        })
    detail.update(_d03_identity_detail(
        episode=episode, identity=identity, control_token=control_token,
        risk_family=risk_family, signal_type=signal_type))
    rule_lineage = (rule.rule_lineage if rule is not None
                    else D03_RULE_LINEAGE_DEFAULT)
    candidate = RiskCandidate.from_signal(
        project_id=project_id, subject_ref=episode.subject_ref,
        domain=D03_DOMAIN, signal_type=signal_type,
        source_snapshot_id=snapshot_id, rule_activation_id=rule_lineage,
        severity_hint=monitoring_priority, confidence_hint=0.0,
        detail=detail)
    return candidate, identity


# ---------------------------------------------------------------------------
# Expected-set expansion (frozen D03 §4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPUnitExpanded:
    """One expanded expected EvaluationUnit seed for D03."""

    episode: IPExposureEpisode
    control_item: str
    control_token: str
    risk_family: str
    resolution: AssignmentResolution
    assignment: Optional[PlannedTreatmentAssignment] = None
    rule: Optional[ProtocolExposureRule] = None
    algorithm: Optional[AdherenceAlgorithm] = None
    action_type: str = ""
    trigger_key: str = ""
    window_override: Optional[IPWindowDescriptor] = None
    binding_mapping: Optional[AssignmentBindingMapping] = None

    @property
    def window(self) -> IPWindowDescriptor:
        if self.window_override is not None:
            return self.window_override
        return _episode_window(self.episode)

    def signal_type(self) -> str:
        return self.risk_family

    def build_unit(
        self, project_id: str,
        binding_mapping: Optional[AssignmentBindingMapping] = None,
    ) -> EvaluationUnit:
        if binding_mapping is None:
            binding_mapping = self.binding_mapping
        norm_concept = "|".join((
            self.episode.episode_key,
            self.episode.actual_treatment_role or "none",
            self.control_token,
            self.risk_family,
        ))
        scope_lineage = "|".join(_d03_risk_scope(
            episode=self.episode, window=self.window,
            assignment=self.assignment, rule=self.rule,
            algorithm=self.algorithm, binding_mapping=binding_mapping))
        return EvaluationUnit(
            project_id=project_id, domain_id=D03_DOMAIN,
            scope_type="subject", scope_key=self.episode.subject_ref,
            normalized_concept_or_rule_item=norm_concept,
            temporal_window=self.window.temporal_window_descriptor(),
            rule_or_knowledge_lineage=scope_lineage,
            unit_algorithm_version=D03_UNIT_ALGO_VERSION)


@dataclass(frozen=True)
class IPExpectedSetExpansion:
    """Result of expanding episodes + control items into the expected set."""

    units: Tuple[IPUnitExpanded, ...]
    project_id: str
    binding_mapping: Optional[AssignmentBindingMapping]
    unit_ids: Tuple[str, ...] = ()
    expected_set_hash: str = ""

    def __post_init__(self) -> None:
        ids = tuple(
            u.build_unit(self.project_id).unit_id
            for u in self.units)
        object.__setattr__(self, "unit_ids", ids)
        object.__setattr__(self, "expected_set_hash", _expected_set_hash(ids))

    @property
    def count(self) -> int:
        return len(self.units)


def _expected_set_hash(unit_ids: Sequence[str]) -> str:
    return "d03-eset-" + content_hash(sorted(set(unit_ids)))


def _control_token_for(
    control_item: str, *, episode: IPExposureEpisode,
    rule: Optional[ProtocolExposureRule] = None,
    algorithm: Optional[AdherenceAlgorithm] = None,
    assignment: Optional[PlannedTreatmentAssignment] = None,
    action_type: str = "",
    trigger_key: str = "",
) -> str:
    if control_item == CONTROL_ROLE_PHASE:
        assignment_id = (assignment.assignment_id
                         if assignment is not None else "none")
        return f"role_phase:{assignment_id}"
    if control_item == CONTROL_PLAN_ACTUAL:
        return f"plan_actual:{rule.rule_id}"
    if control_item == CONTROL_ADHERENCE:
        return f"adherence:{algorithm.algorithm_id}:{algorithm.window_id}"
    if control_item == CONTROL_ALLOWED_ACTION:
        return f"allowed_action:{rule.rule_id}:{action_type}"
    if control_item == CONTROL_MEDICAL_ACTION:
        return f"medical_action:{rule.rule_id}:{trigger_key}"
    if control_item == CONTROL_ACCOUNTABILITY:
        return (f"accountability:{algorithm.algorithm_id}:"
                f"{algorithm.window_id}")
    raise IPSliceError(f"unknown control item {control_item!r}")


def expand_ip_expected_set(
    *, project_id: str,
    episodes: Sequence[IPExposureEpisode],
    assignments: Sequence[PlannedTreatmentAssignment] = (),
    active_rules: Sequence[ProtocolExposureRule] = (),
    adherence_algorithms: Sequence[AdherenceAlgorithm] = (),
    action_evidence: Sequence[IPActionEvidence] = (),
    binding_mapping: Optional[AssignmentBindingMapping] = None,
) -> IPExpectedSetExpansion:
    """Expand D03 episodes + activated control items into the expected unit
    set (frozen D03 §4).  Every episode expands independently: role_phase
    (assignment), then each activated plan_actual rule, adherence/account-
    ability algorithm, allowed_action rule x action type, and medical_action
    rule x trigger event key.  No merging of roles/phases into one unit.
    """
    if not project_id.strip():
        raise IPSliceError("project_id is required")
    expanded: List[IPUnitExpanded] = []
    for episode in episodes:
        resolution = resolve_episode_assignment(
            episode=episode, assignments=assignments,
            binding_mapping=binding_mapping)
        assignment = resolution.assignment
        # 1. role_phase:<assignment_id>
        expanded.append(IPUnitExpanded(
            episode=episode, control_item=CONTROL_ROLE_PHASE,
            control_token=_control_token_for(
                CONTROL_ROLE_PHASE, episode=episode, assignment=assignment),
            risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_ROLE_PHASE],
            resolution=resolution, assignment=assignment,
            binding_mapping=binding_mapping))
        # 2. plan_actual:<rule_id>
        for rule in active_rules:
            if rule.rule_type != RULE_TYPE_PLAN_ACTUAL:
                continue
            expanded.append(IPUnitExpanded(
                episode=episode, control_item=CONTROL_PLAN_ACTUAL,
                control_token=_control_token_for(
                    CONTROL_PLAN_ACTUAL, episode=episode, rule=rule),
                risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_PLAN_ACTUAL],
                resolution=resolution, assignment=assignment, rule=rule,
                window_override=_rule_window(episode, rule),
                binding_mapping=binding_mapping))
        # 3./6. adherence / accountability per algorithm.
        for algorithm in adherence_algorithms:
            if algorithm.is_accountability_proxy:
                expanded.append(IPUnitExpanded(
                    episode=episode, control_item=CONTROL_ACCOUNTABILITY,
                    control_token=_control_token_for(
                        CONTROL_ACCOUNTABILITY, episode=episode,
                        algorithm=algorithm),
                    risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_ACCOUNTABILITY],
                    resolution=resolution, assignment=assignment,
                    algorithm=algorithm,
                    window_override=_algorithm_window(episode, algorithm),
                    binding_mapping=binding_mapping))
            else:
                expanded.append(IPUnitExpanded(
                    episode=episode, control_item=CONTROL_ADHERENCE,
                    control_token=_control_token_for(
                        CONTROL_ADHERENCE, episode=episode,
                        algorithm=algorithm),
                    risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_ADHERENCE],
                    resolution=resolution, assignment=assignment,
                    algorithm=algorithm,
                    window_override=_algorithm_window(episode, algorithm),
                    binding_mapping=binding_mapping))
        # 4. allowed_action:<rule_id>:<action>
        for rule in active_rules:
            if rule.rule_type != RULE_TYPE_ALLOWED_ACTION:
                continue
            for action_type in rule.allowed_action_types:
                expanded.append(IPUnitExpanded(
                    episode=episode, control_item=CONTROL_ALLOWED_ACTION,
                    control_token=_control_token_for(
                        CONTROL_ALLOWED_ACTION, episode=episode, rule=rule,
                        action_type=action_type),
                    risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_ALLOWED_ACTION],
                    resolution=resolution, assignment=assignment, rule=rule,
                    action_type=action_type,
                    window_override=_rule_window(episode, rule),
                    binding_mapping=binding_mapping))
        # 5. medical_action:<rule_id>:<source_event_key>
        for rule in active_rules:
            if rule.rule_type != RULE_TYPE_MEDICAL_ACTION:
                continue
            keys = sorted({
                ev.stable_source_event_key for ev in action_evidence
                if ev.source_role == rule.trigger_role})
            if not keys:
                keys = ["none"]
            for key in keys:
                expanded.append(IPUnitExpanded(
                    episode=episode, control_item=CONTROL_MEDICAL_ACTION,
                    control_token=_control_token_for(
                        CONTROL_MEDICAL_ACTION, episode=episode, rule=rule,
                        trigger_key=key),
                    risk_family=RISK_FAMILY_BY_CONTROL[CONTROL_MEDICAL_ACTION],
                    resolution=resolution, assignment=assignment, rule=rule,
                    trigger_key=key,
                    window_override=_rule_window(episode, rule),
                    binding_mapping=binding_mapping))
    return IPExpectedSetExpansion(
        units=tuple(expanded), project_id=project_id,
        binding_mapping=binding_mapping)


# ---------------------------------------------------------------------------
# Evidence / source-record / Query helpers
# ---------------------------------------------------------------------------

def _make_evidence_item(
    *, evidence_id: str, polarity: str, locator: SourceLocator,
    evidence_role: str, rule_lineage: str,
    uncertainty_note: str = "",
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id, polarity=polarity, locator=locator,
        evidence_role=evidence_role, rule_lineage=rule_lineage,
        uncertainty_note=uncertainty_note)


def _dedup_locator_ids(*locators: Optional[SourceLocator]) -> Tuple[str, ...]:
    """Return deduplicated sorted locator ids, skipping None."""
    ids: List[str] = []
    for loc in locators:
        if loc is not None:
            ids.append(loc.locator_id())
    return tuple(sorted(set(ids)))


def _make_source_record_ref(locator: SourceLocator) -> SourceRecordRef:
    return SourceRecordRef(record_id=locator.record_id, locator=locator)


def _canonical_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _canonical_dose(value: str) -> Optional[Decimal]:
    """Parse a dose value as Decimal (exact), or None when unparseable."""
    if not value.strip():
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _canonical_record_value(field_name: str, value: str) -> Optional[str]:
    """Return a comparable canonical value or None when insufficient."""
    if not value.strip():
        return None
    if field_name in ("dose", "dose_after", "dose_before"):
        dec = _canonical_dose(value)
        if dec is None:
            return None
        return str(dec)
    return _canonical_text(value)


def _journey_marker(
    *, episode: IPExposureEpisode, unit_id: str,
    assignment: Optional[PlannedTreatmentAssignment],
    risk_family: str, audience_label: str, monitoring_priority: str,
    positive_subtype: str = "",
) -> Dict[str, Any]:
    return {
        "domain_track": "ip", "event_id": episode.episode_key,
        "subject_ref": episode.subject_ref,
        "start": episode.span_start, "end": episode.span_end,
        "ongoing": episode.span_ongoing,
        "episode_id": episode.episode_key, "unit_id": unit_id,
        "assignment_id": (assignment.assignment_id
                          if assignment is not None else ""),
        "treatment_role_token": episode.actual_treatment_role,
        "display_role_label": (assignment.display_role_label
                               if assignment is not None else ""),
        "disclosure_state": episode.disclosure_state,
        "dose": episode.dose, "dose_unit": episode.dose_unit,
        "route": episode.route, "frequency": episode.frequency,
        "risk_family": risk_family, "audience_label": audience_label,
        "monitoring_priority": monitoring_priority,
        "positive_subtype": positive_subtype,
        "source_locator_id": episode.source_locator.locator_id(),
    }


# ---------------------------------------------------------------------------
# IPUnitResult (frozen D03 §2 RiskDomainUnitResult + ledger materialization)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPUnitResult:
    """The evaluation outcome for one D03 EvaluationUnit.

    Satisfies the neutral ``RiskDomainUnitResult`` protocol AND can
    materialize a full ``UnitEvaluation`` for the ``CoverageLedger``.
    """

    unit_id: str
    subject_ref: str
    l1_disposition: str
    monitoring_priority: str
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    not_evaluable_reason: str = ""
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    journey_markers: Tuple[Dict[str, Any], ...] = ()
    boundary_reason: str = ""
    positive_subtype: str = ""
    audience_label: str = ""

    def __post_init__(self) -> None:
        if self.l1_disposition not in L1Disposition.ALL:
            raise IPSliceError(
                f"l1_disposition={self.l1_disposition!r} not a valid L1")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise IPSliceError(
                f"monitoring_priority={self.monitoring_priority!r} invalid")
        object.__setattr__(self, "r2_candidates", tuple(self.r2_candidates))
        object.__setattr__(self, "risk_candidate_refs",
                           tuple(self.risk_candidate_refs))
        object.__setattr__(self, "risk_instance_refs",
                           tuple(self.risk_instance_refs))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "source_record_refs",
                           tuple(self.source_record_refs))
        object.__setattr__(self, "query_refs", tuple(self.query_refs))
        object.__setattr__(self, "journey_markers",
                           tuple(self.journey_markers))

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
        self, *, l0_status: str = L0CoverageStatus.COVERED,
        provenance_snapshot_id: str = "",
        provenance_rule_lineage: str = "",
    ) -> UnitEvaluation:
        polarities: List[str] = []
        for ev in self.evidence:
            if ev.polarity in (L1bEvidencePolarity.SUPPORTING,
                               L1bEvidencePolarity.COUNTEREVIDENCE,
                               L1bEvidencePolarity.CONTEXT):
                if ev.polarity not in polarities:
                    polarities.append(ev.polarity)
        return UnitEvaluation(
            unit_id=self.unit_id, l0_status=l0_status,
            l1_disposition=self.l1_disposition,
            l1b_polarities=tuple(polarities),
            evidence=self.evidence,
            source_record_refs=self.source_record_refs,
            risk_candidate_refs=self.risk_candidate_refs,
            risk_instance_refs=self.risk_instance_refs,
            query_refs=self.query_refs,
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=self.not_evaluable_reason)


# ---------------------------------------------------------------------------
# Query construction (frozen D03 §8)
# ---------------------------------------------------------------------------

def _display_label(
    assignment: Optional[PlannedTreatmentAssignment],
) -> str:
    if assignment is not None and assignment.display_role_label.strip():
        return assignment.display_role_label.strip()
    return "研究药物"


def _query_text(
    *, subtype: str, subject_ref: str, episode: IPExposureEpisode,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    match_reason: str,
) -> Tuple[str, str, str]:
    """Build the three-part Chinese Query text (frozen D03 §8)."""
    label = _display_label(assignment)
    loc_id = episode.source_locator.locator_id()
    if subtype == POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH:
        basis = (f"方案规则 {rule.rule_id}（版本 {rule.rule_version}，条款 "
                 f"{rule.clause_locator}）规定计划剂量/剂型/途径/频次及给药"
                 f"窗口。")
        finding = (f"参与者 {subject_ref} 的 {label} 实际暴露记录与方案计划"
                   f"不一致：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实实际给药记录与方案计划；如属实，请确认是否构成"
                  "方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH:
        basis = (f"随机/治疗分组由 assignment {assignment.assignment_id}"
                 f"（版本 {assignment.assignment_lineage}）定义：治疗角色"
                 f"{assignment.treatment_role_token}，研究阶段"
                 f"{assignment.study_phase}。")
        finding = (f"参与者 {subject_ref} 的 {label} 实际暴露角色或阶段与"
                   f"分组计划不一致：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实受试者实际分组、随机信息与暴露记录；如属实，请确认"
                  "是否构成方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE:
        basis = (f"依从性算法 {algorithm.algorithm_id}（版本 "
                 f"{algorithm.version}，窗口 {algorithm.window_id}）规定"
                 f"允许范围与计算口径。")
        finding = (f"参与者 {subject_ref} 在窗口 {algorithm.window_id} 的依从性"
                   f"计算结果超出允许范围：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实实际给药记录、算法分子分母及原始记录；如属实，请"
                  "确认是否构成方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION:
        basis = (f"方案规则 {rule.rule_id}（版本 {rule.rule_version}，条款 "
                 f"{rule.clause_locator}）规定允许的给药调整及条件。")
        finding = (f"参与者 {subject_ref} 的 {label} 实际给药调整与方案允许"
                   f"条件不一致：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实给药调整的原因、前后剂量及方案允许条件；如属实，请"
                  "确认是否构成方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT:
        basis = (f"方案规则 {rule.rule_id}（版本 {rule.rule_version}，条款 "
                 f"{rule.clause_locator}）规定医学触发事件 {rule.trigger_concept}"
                 f" 对应的预期处置。")
        finding = (f"参与者 {subject_ref} 的 {label} 实际处置与医学触发事件"
                   f"不一致：{match_reason}。记录定位 {loc_id}。")
        action = ("请核实医学事件与给药处置记录的关系；如属实，请确认是否"
                  "构成方案偏离并按项目流程处理。")
        return basis, finding, action
    if subtype == POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY:
        if algorithm is not None and algorithm.is_accountability_proxy:
            basis = (f"依从性算法 {algorithm.algorithm_id}（版本 "
                     f"{algorithm.version}，窗口 {algorithm.window_id}）将"
                     f"发放回收核算作为独立控制项，结果{ACCOUNTABILITY_PROXY_ANNOTATION}。")
            finding = (f"参与者 {subject_ref} 在窗口 {algorithm.window_id} "
                       f"按发放/回收核算，发放、回收与记录给药核算不一致："
                       f"{match_reason}。记录定位 {loc_id}。")
        else:
            basis = (f"依从性算法 {algorithm.algorithm_id}（版本 "
                     f"{algorithm.version}，窗口 {algorithm.window_id}）将发放"
                     f"回收核算作为独立控制项。")
            finding = (f"参与者 {subject_ref} 在窗口 {algorithm.window_id} 的发放、"
                       f"回收与记录给药核算不一致：{match_reason}。记录定位 "
                       f"{loc_id}。")
        action = ("请核实发放、回收与实际给药记录；如属实，请确认是否构成"
                  "方案偏离并按项目流程处理。")
        return basis, finding, action
    raise IPSliceError(f"no Query template for subtype {subtype!r}")


def _build_query_ref(
    *, query_id: str, unit_id: str, subtype: str, subject_ref: str,
    episode: IPExposureEpisode,
    assignment: Optional[PlannedTreatmentAssignment],
    rule: Optional[ProtocolExposureRule],
    algorithm: Optional[AdherenceAlgorithm],
    candidate_id: str,
    source_locator_ids: Sequence[str],
    match_reason: str,
) -> QueryDraftRef:
    basis_body, finding_body, action_body = _query_text(
        subtype=subtype, subject_ref=subject_ref, episode=episode,
        assignment=assignment, rule=rule, algorithm=algorithm,
        match_reason=match_reason)
    return QueryDraftRef(
        query_id=query_id, unit_id=unit_id,
        basis=f"依据：{basis_body}",
        finding=f"发现：{finding_body}",
        action=f"行动项：{action_body}",
        source_locator_ids=tuple(source_locator_ids),
        linked_candidate_id=candidate_id)


# ---------------------------------------------------------------------------
# Positive/boundary materialization helpers
# ---------------------------------------------------------------------------

def _build_positive_result(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    subtype: str, match_reason: str, snapshot_id: str,
    monitoring_priority: str, rule_lineage: str,
    source_locators: Sequence[SourceLocator],
    extra_evidence: Sequence[EvidenceItem] = (),
) -> IPUnitResult:
    """Materialize a D03 positive with complete provenance."""
    audience = positive_subtype_audience_label(subtype)
    episode = expanded.episode
    candidate, identity = _build_d03_candidate(
        project_id=project_id, episode=episode, window=expanded.window,
        control_token=expanded.control_token,
        risk_family=expanded.risk_family, signal_type=subtype,
        assignment=expanded.assignment, rule=expanded.rule,
        algorithm=expanded.algorithm,
        binding_mapping=expanded.binding_mapping, snapshot_id=snapshot_id,
        monitoring_priority=monitoring_priority,
        match_reason=match_reason, positive_subtype=subtype,
        audience_label=audience)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=episode.source_locator)
    evidence: List[EvidenceItem] = [
        _make_evidence_item(
            evidence_id=f"ev-{unit_id}-match",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=episode.source_locator,
            evidence_role="ip_exposure", rule_lineage=rule_lineage,
            uncertainty_note=match_reason),
    ]
    evidence.extend(extra_evidence)
    extra_locs: List[SourceLocator] = []
    seen_locs: Set[str] = {episode.source_locator.locator_id()}
    if expanded.assignment is not None \
            and expanded.assignment.source_locator is not None:
        extra_locs.append(expanded.assignment.source_locator)
        seen_locs.add(expanded.assignment.source_locator.locator_id())
    for loc in source_locators:
        if loc.locator_id() not in seen_locs:
            extra_locs.append(loc)
            seen_locs.add(loc.locator_id())
    for index, loc in enumerate(extra_locs):
        evidence.append(_make_evidence_item(
            evidence_id=f"ev-{unit_id}-src-{index}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=loc, evidence_role="ip_exposure",
            rule_lineage=rule_lineage,
            uncertainty_note="来源记录定位"))
    query_loc_ids = _dedup_locator_ids(
        episode.source_locator, *extra_locs)
    query = _build_query_ref(
        query_id=f"q-{unit_id}", unit_id=unit_id, subtype=subtype,
        subject_ref=episode.subject_ref, episode=episode,
        assignment=expanded.assignment, rule=expanded.rule,
        algorithm=expanded.algorithm,
        candidate_id=candidate.candidate_id,
        source_locator_ids=query_loc_ids, match_reason=match_reason)
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, assignment=expanded.assignment,
        risk_family=expanded.risk_family, audience_label=audience,
        monitoring_priority=monitoring_priority, positive_subtype=subtype)
    src_ref = _make_source_record_ref(episode.source_locator)
    return IPUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.POSITIVE,
        monitoring_priority=monitoring_priority,
        r2_candidates=(candidate,), risk_candidate_refs=(cand_ref,),
        evidence=tuple(evidence), source_record_refs=(src_ref,),
        query_refs=(query,), journey_markers=(jm,),
        positive_subtype=subtype, audience_label=audience)


def _build_boundary_result(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    boundary_reason: str, snapshot_id: str,
    rule_lineage: str, audience_suffix: str,
    source_locators: Sequence[SourceLocator] = (),
    extra_evidence: Sequence[EvidenceItem] = (),
) -> IPUnitResult:
    """Materialize a D03 boundary with a candidate and no Query."""
    episode = expanded.episode
    risk_family = expanded.risk_family
    signal_type = f"{risk_family}_boundary"
    audience = f"{audience_suffix}（边界）"
    candidate, identity = _build_d03_candidate(
        project_id=project_id, episode=episode, window=expanded.window,
        control_token=expanded.control_token,
        risk_family=risk_family, signal_type=signal_type,
        assignment=expanded.assignment, rule=expanded.rule,
        algorithm=expanded.algorithm,
        binding_mapping=expanded.binding_mapping, snapshot_id=snapshot_id,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        match_reason=boundary_reason, audience_label=audience)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=episode.source_locator)
    evidence: List[EvidenceItem] = [_make_evidence_item(
        evidence_id=f"ev-{unit_id}-boundary",
        polarity=L1bEvidencePolarity.SUPPORTING,
        locator=episode.source_locator,
        evidence_role="ip_exposure", rule_lineage=rule_lineage,
        uncertainty_note=boundary_reason)]
    evidence.extend(extra_evidence)
    extra_locs: List[SourceLocator] = []
    seen_locs: Set[str] = {episode.source_locator.locator_id()}
    if expanded.assignment is not None \
            and expanded.assignment.source_locator is not None:
        extra_locs.append(expanded.assignment.source_locator)
        seen_locs.add(expanded.assignment.source_locator.locator_id())
    for loc in source_locators:
        if loc.locator_id() not in seen_locs:
            extra_locs.append(loc)
            seen_locs.add(loc.locator_id())
    for index, loc in enumerate(extra_locs):
        evidence.append(_make_evidence_item(
            evidence_id=f"ev-{unit_id}-bnd-src-{index}",
            polarity=L1bEvidencePolarity.SUPPORTING,
            locator=loc, evidence_role="ip_exposure",
            rule_lineage=rule_lineage, uncertainty_note=boundary_reason))
    jm = _journey_marker(
        episode=episode, unit_id=unit_id, assignment=expanded.assignment,
        risk_family=risk_family, audience_label=audience,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN)
    src_ref = _make_source_record_ref(episode.source_locator)
    return IPUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.BOUNDARY,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        r2_candidates=(candidate,), risk_candidate_refs=(cand_ref,),
        evidence=tuple(evidence), source_record_refs=(src_ref,),
        journey_markers=(jm,), boundary_reason=boundary_reason,
        audience_label=audience)


def _not_evaluable_result(
    *, unit_id: str, episode: IPExposureEpisode,
    reason: str, rule_lineage: str,
    extra_locators: Sequence[SourceLocator] = (),
) -> IPUnitResult:
    """Materialize a D03 not_evaluable (no candidate/Query)."""
    src_ref = _make_source_record_ref(episode.source_locator)
    evidence: List[EvidenceItem] = [_make_evidence_item(
        evidence_id=f"ev-{unit_id}-ne",
        polarity=L1bEvidencePolarity.CONTEXT,
        locator=episode.source_locator,
        evidence_role="ip_exposure", rule_lineage=rule_lineage,
        uncertainty_note=reason)]
    for index, loc in enumerate(extra_locators):
        if loc.locator_id() == episode.source_locator.locator_id():
            continue
        evidence.append(_make_evidence_item(
            evidence_id=f"ev-{unit_id}-ne-src-{index}",
            polarity=L1bEvidencePolarity.CONTEXT,
            locator=loc, evidence_role="ip_exposure",
            rule_lineage=rule_lineage, uncertainty_note=reason))
    return IPUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NOT_EVALUABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        not_evaluable_reason=reason, evidence=tuple(evidence),
        source_record_refs=(src_ref,))


def _negative_result(
    *, unit_id: str, episode: IPExposureEpisode,
    rule_lineage: str, reason: str,
    extra_locators: Sequence[SourceLocator] = (),
) -> IPUnitResult:
    """Materialize a D03 negative with counterevidence."""
    src_ref = _make_source_record_ref(episode.source_locator)
    evidence: List[EvidenceItem] = [_make_evidence_item(
        evidence_id=f"ev-{unit_id}-negative",
        polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
        locator=episode.source_locator,
        evidence_role="ip_exposure", rule_lineage=rule_lineage,
        uncertainty_note=reason)]
    for index, loc in enumerate(extra_locators):
        if loc.locator_id() == episode.source_locator.locator_id():
            continue
        evidence.append(_make_evidence_item(
            evidence_id=f"ev-{unit_id}-neg-src-{index}",
            polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
            locator=loc, evidence_role="ip_exposure",
            rule_lineage=rule_lineage, uncertainty_note=reason))
    return IPUnitResult(
        unit_id=unit_id, subject_ref=episode.subject_ref,
        l1_disposition=L1Disposition.NEGATIVE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        evidence=tuple(evidence), source_record_refs=(src_ref,))


# ---------------------------------------------------------------------------
# Role coverage gate (frozen D03 §3.1)
# ---------------------------------------------------------------------------

def _required_roles_for(
    expanded: IPUnitExpanded,
    role_coverage: Mapping[str, bool],
) -> Optional[str]:
    """Return a Chinese gap reason when a required semantic role is not
    covered, else None.  Fail-closed: roles absent from ``role_coverage``
    are not covered."""
    required: Set[str] = set(REQUIRED_IP_ROLES)
    control = expanded.control_item
    if control == CONTROL_PLAN_ACTUAL:
        required.add("planned_treatment")
    elif control == CONTROL_ROLE_PHASE:
        required.add("planned_treatment")
        required.add("study_phase")
        if (expanded.assignment is not None
                and expanded.assignment.randomization_token.strip()):
            required.add("randomization")
    elif control == CONTROL_ADHERENCE:
        required.add("planned_treatment")
        required.add("study_phase")
    elif control == CONTROL_ALLOWED_ACTION:
        required.add("planned_treatment")
        required.add("ip_action_reason")
    elif control == CONTROL_MEDICAL_ACTION:
        required.add("planned_treatment")
        required.add("ip_action_reason")
    elif control == CONTROL_ACCOUNTABILITY:
        required.add("ip_dispense")
        required.add("ip_return")
    missing = sorted(role for role in required
                     if not role_coverage.get(role, False))
    if not missing:
        return None
    labels = "、".join(IP_ROLE_LABELS.get(role, role) for role in missing)
    return f"必需来源角色覆盖不完整（{labels}），无法评价"


def _audience_suffix_for(expanded: "IPUnitExpanded") -> str:
    control = expanded.control_item
    return {
        CONTROL_PLAN_ACTUAL: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH],
        CONTROL_ROLE_PHASE: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH],
        CONTROL_ADHERENCE: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE],
        CONTROL_ALLOWED_ACTION: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION],
        CONTROL_MEDICAL_ACTION: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT],
        CONTROL_ACCOUNTABILITY: POSITIVE_SUBTYPE_LABELS[
            POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY],
    }[control]


def _binding_gate_result(
    *, project_id: str, expanded: "IPUnitExpanded", unit_id: str,
    snapshot_id: str, rule_lineage: str,
) -> Optional[IPUnitResult]:
    """Terminal result when the assignment binding failed.

    Zero candidates -> not_evaluable; two or more feasible candidates ->
    boundary (both have source support; the kernel must not choose).
    """
    episode = expanded.episode
    if expanded.resolution.status == RESOLUTION_MISSING:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=expanded.resolution.reason, rule_lineage=rule_lineage)
    if expanded.resolution.status == RESOLUTION_AMBIGUOUS:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=expanded.resolution.reason,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=_audience_suffix_for(expanded))
    return None


# ---------------------------------------------------------------------------
# Unit-level evaluation: role_phase
# ---------------------------------------------------------------------------

def _evaluate_role_phase_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    assignment = expanded.assignment
    if not episode.role_confirmed:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="实际治疗角色未确认，无法核对治疗分组或阶段",
            rule_lineage=rule_lineage)
    if not episode.phase_confirmed or not episode.study_phase.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="研究阶段缺失或未确认，无法核对治疗分组或阶段",
            rule_lineage=rule_lineage)
    mismatches: List[str] = []
    if (episode.actual_treatment_role.strip()
            != assignment.treatment_role_token.strip()):
        mismatches.append(
            f"实际治疗角色 {episode.actual_treatment_role} 与分组角色 "
            f"{assignment.treatment_role_token} 不一致")
    if episode.study_phase.strip() != assignment.study_phase.strip():
        mismatches.append(
            f"实际研究阶段 {episode.study_phase} 与分组阶段 "
            f"{assignment.study_phase} 不一致")
    if not mismatches:
        return _negative_result(
            unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
            reason="实际治疗角色与研究阶段与已确认分组一致")
    match_reason = "；".join(mismatches)
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(
            POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    return _build_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        subtype=POSITIVE_SUBTYPE_TREATMENT_ROLE_OR_PHASE_MISMATCH,
        match_reason=match_reason, snapshot_id=snapshot_id,
        monitoring_priority=priority, rule_lineage=rule_lineage,
        source_locators=(
            (assignment.source_locator,) if assignment.source_locator else ()))


# ---------------------------------------------------------------------------
# Unit-level evaluation: plan_actual
# ---------------------------------------------------------------------------

def _rule_phase_applicability(
    *, episode: IPExposureEpisode, rule: ProtocolExposureRule,
    unit_id: str, rule_lineage: str,
) -> Optional[IPUnitResult]:
    """Return a terminal NA/NE result when the rule does not apply, else
    None.  Confirmed phase outside applicability is not_applicable; every
    unconfirmed/missing phase state is not_evaluable."""
    if rule.applicable_phases:
        if not episode.phase_confirmed or not episode.study_phase.strip():
            note = ("研究阶段缺失或为空，无法判定方案规则适用性"
                    if not episode.study_phase.strip()
                    else f"研究阶段 {episode.study_phase!r} 未获确认，"
                         f"无法判定方案规则适用性")
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode, reason=note,
                rule_lineage=rule_lineage)
        if episode.study_phase.strip() not in rule.applicable_phases:
            return IPUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_APPLICABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                source_record_refs=(
                    _make_source_record_ref(episode.source_locator),))
    if rule.applicable_treatment_role:
        if not episode.role_confirmed:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="实际治疗角色未确认，无法判定方案规则适用性",
                rule_lineage=rule_lineage)
        if (episode.actual_treatment_role.strip()
                != rule.applicable_treatment_role.strip()):
            return IPUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_APPLICABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                source_record_refs=(
                    _make_source_record_ref(episode.source_locator),))
    return None


def _evaluate_plan_actual_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    occurrences: Sequence[ExposureOccurrence],
    aggregation_policy: Optional[ExposureAggregationPolicy],
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    rule = expanded.rule
    gate = _rule_phase_applicability(
        episode=episode, rule=rule, unit_id=unit_id,
        rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    # Window applicability: a determinate overlap evaluates; a fully
    # disjoint episode is not_applicable; possible overlap is boundary
    # (frozen D03 §7).  Out-of-window dosing surfaces via occurrence days.
    overlap = _compare_windows(
        expanded.window, rule.window_start, rule.window_end,
        rule.window_start_inclusive, rule.window_end_inclusive,
        containment=False)
    if not overlap.comparable:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=overlap.boundary_reason, rule_lineage=rule_lineage)
    if overlap.outside:
        return IPUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            source_record_refs=(
                _make_source_record_ref(episode.source_locator),))
    if overlap.possibly_overlap:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=overlap.boundary_reason, snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH])
    # Disclosure gate: dose/form comparison needs dose disclosure (F-07).
    compares_dose = any(f in ("dose", "dosage_form")
                        for f in rule.compare_fields)
    if compares_dose and not episode.dose_disclosed:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="需要核对剂量/剂型身份但该身份在当前披露范围不可用",
            rule_lineage=rule_lineage)
    # Field comparison.
    mismatches: List[str] = []
    for fname in rule.compare_fields:
        actual = _canonical_record_value(fname, getattr(episode, fname))
        planned = _canonical_record_value(
            fname, getattr(rule, f"planned_{fname}"))
        if actual is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason=f"实际{_field_label(fname)}缺失或精度不足，无法与方案"
                       f"计划可靠比较",
                rule_lineage=rule_lineage)
        if planned is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason=f"方案计划{_field_label(fname)}缺失，无法可靠比较",
                rule_lineage=rule_lineage)
        if actual != planned:
            mismatches.append(
                f"实际{_field_label(fname)} {getattr(episode, fname)} 与计划"
                f" {getattr(rule, f'planned_{fname}')} 不一致")
    # Window mismatch via occurrence days outside the planned dosing window.
    window_violations: List[str] = []
    if aggregation_policy is not None and rule.window_start.strip():
        occ_days = _occurrence_days_in_rule_window(
            episode=episode, occurrences=occurrences,
            rule=rule, policy=aggregation_policy)
        if occ_days is not None:
            window_violations = occ_days
    if window_violations:
        mismatches.append(
            "存在给药日落在方案计划给药窗口之外："
            + "、".join(sorted(window_violations)[:3]))
    if not mismatches:
        return _negative_result(
            unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
            reason="实际给药与方案计划在剂量、剂型、途径、频次和窗口上一致")
    match_reason = "；".join(mismatches)
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(
            POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    return _build_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        subtype=POSITIVE_SUBTYPE_PLANNED_ACTUAL_EXPOSURE_MISMATCH,
        match_reason=match_reason, snapshot_id=snapshot_id,
        monitoring_priority=priority, rule_lineage=rule_lineage,
        source_locators=())


_FIELD_LABELS: Dict[str, str] = {
    "dose": "剂量", "dose_unit": "剂量单位", "dosage_form": "剂型",
    "route": "给药途径", "frequency": "给药频次",
}


def _field_label(field_name: str) -> str:
    return _FIELD_LABELS.get(field_name, field_name)


def _occurrence_days_in_rule_window(
    *, episode: IPExposureEpisode,
    occurrences: Sequence[ExposureOccurrence],
    rule: ProtocolExposureRule,
    policy: ExposureAggregationPolicy,
) -> Optional[List[str]]:
    """Return occurrence day tokens determinately OUTSIDE the rule window,
    or None when the check cannot be proven (no occurrences / ambiguous /
    insufficient precision)."""
    daycomp = compute_actual_exposure_days(
        episode=episode, occurrences=occurrences, policy=policy)
    if daycomp.status != DAY_STATUS_COMPLETE or not daycomp.day_set:
        return None
    rw_start = (normalize_partial_date(rule.window_start)
                if rule.window_start.strip() else None)
    rw_end = (normalize_partial_date(rule.window_end)
              if rule.window_end.strip() else None)
    if rw_start is None and rw_end is None:
        return None
    days_parsed: List[Any] = []
    for day_txt in daycomp.day_set:
        day_nv = normalize_partial_date(day_txt)
        day = _to_day(day_nv)
        if day is None:
            return None
        days_parsed.append(day)
    d_rws = _to_day(rw_start) if rw_start is not None else None
    d_rwe = _to_day(rw_end) if rw_end is not None else None
    # Unstated endpoint inclusivity on an occurrence day is not provable.
    if (rule.window_start_inclusive is None and d_rws is not None
            and any(day == d_rws for day in days_parsed)):
        return None
    if (rule.window_end_inclusive is None and d_rwe is not None
            and any(day == d_rwe for day in days_parsed)):
        return None
    outside: List[str] = []
    for day_txt, day in zip(daycomp.day_set, days_parsed):
        if d_rws is not None:
            if (day < d_rws
                    if rule.window_start_inclusive is not False
                    else day <= d_rws):
                outside.append(day_txt)
                continue
        if d_rwe is not None:
            if (day > d_rwe
                    if rule.window_end_inclusive is not False
                    else day >= d_rwe):
                outside.append(day_txt)
    return sorted(set(outside))


# ---------------------------------------------------------------------------
# Unit-level evaluation: adherence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _RatioOutcome:
    out_of_range: bool
    equality: bool
    value_desc: str
    reason: str


def _round_ratio(frac: Fraction, precision: int, mode: str) -> Decimal:
    dec = Decimal(frac.numerator) / Decimal(frac.denominator)
    quantum = Decimal(1).scaleb(-precision)
    rounding = {
        ROUNDING_ROUND_HALF_UP: ROUND_HALF_UP,
        ROUNDING_FLOOR: ROUND_FLOOR,
        ROUNDING_CEILING: ROUND_CEILING,
    }[mode]
    return dec.quantize(quantum, rounding=rounding)


def _threshold_fraction(value: str) -> Optional[Fraction]:
    try:
        return Fraction(Decimal(str(value)))
    except Exception:
        return None


def _check_ratio_against_thresholds(
    frac: Fraction, algorithm: AdherenceAlgorithm,
) -> _RatioOutcome:
    """Compare a ratio against the algorithm thresholds (§6.2).

    Threshold equality is decisive only when the side's inclusivity is
    explicit; otherwise boundary.
    """
    compare_after = (
        algorithm.compare_before_or_after_rounding == COMPARE_AFTER_ROUNDING)
    if compare_after:
        rounded = _round_ratio(frac, algorithm.calculation_precision,
                               algorithm.rounding_mode)
        value_desc = str(rounded)
        val: Optional[Fraction] = None
    else:
        value_desc = (f"{frac.numerator}/{frac.denominator}="
                      f"{float(frac):.6g}")
        val = frac
    out_of_range = False
    equality_thresholds: List[str] = []
    if algorithm.upper_threshold is not None:
        thr = _threshold_fraction(algorithm.upper_threshold)
        if thr is None:
            return _RatioOutcome(False, False, value_desc,
                                 "上限阈值无法解析")
        if compare_after:
            if rounded > Decimal(algorithm.upper_threshold):
                out_of_range = True
            elif rounded == Decimal(algorithm.upper_threshold):
                equality_thresholds.append("upper")
        else:
            if val > thr:
                out_of_range = True
            elif val == thr:
                equality_thresholds.append("upper")
    if algorithm.lower_threshold is not None:
        thr = _threshold_fraction(algorithm.lower_threshold)
        if thr is None:
            return _RatioOutcome(False, False, value_desc,
                                 "下限阈值无法解析")
        if compare_after:
            if rounded < Decimal(algorithm.lower_threshold):
                out_of_range = True
            elif rounded == Decimal(algorithm.lower_threshold):
                equality_thresholds.append("lower")
        else:
            if val < thr:
                out_of_range = True
            elif val == thr:
                equality_thresholds.append("lower")
    if out_of_range:
        return _RatioOutcome(True, False, value_desc, "超出允许范围")
    if equality_thresholds:
        inclusive_flags = {
            "upper": algorithm.upper_inclusive,
            "lower": algorithm.lower_inclusive,
        }
        if any(inclusive_flags[t] is None for t in equality_thresholds):
            return _RatioOutcome(
                False, True, value_desc,
                "计算值恰在阈值等号边界，算法未声明该侧包含关系")
        if all(inclusive_flags[t] for t in equality_thresholds):
            return _RatioOutcome(
                False, False, value_desc, "恰在阈值等号且该侧包含，处于允许范围")
        return _RatioOutcome(
            True, False, value_desc, "恰在阈值等号且该侧不包含，超出允许范围")
    return _RatioOutcome(False, False, value_desc, "")


def _window_day_count(
    algorithm: AdherenceAlgorithm,
) -> Tuple[Optional[int], str]:
    """Expected day count of the algorithm window per endpoint rules."""
    start = (normalize_partial_date(algorithm.window_start)
             if algorithm.window_start.strip() else None)
    end = (normalize_partial_date(algorithm.window_end)
           if algorithm.window_end.strip() else None)
    if start is None or end is None:
        return None, "算法窗口起止日期缺失"
    if _nv_precision(start) != "day" or _nv_precision(end) != "day":
        return None, "算法窗口日期精度不足（需全日精度）"
    if (algorithm.window_start_inclusive is None
            or algorithm.window_end_inclusive is None):
        return None, "算法窗口端点包含关系未声明，无法确定分母"
    d_start = _to_day(start)
    d_end = _to_day(end)
    if d_start is None or d_end is None or d_end < d_start:
        return None, "算法窗口日期无法解析或起止颠倒"
    if algorithm.window_start_inclusive is False:
        d_start += datetime.timedelta(days=1)
    if algorithm.window_end_inclusive is False:
        d_end -= datetime.timedelta(days=1)
    if d_end < d_start:
        return None, "算法窗口端点包含关系导致窗口为空"
    return (d_end - d_start).days + 1, ""


def _days_in_window(
    day_set: Sequence[str], algorithm: AdherenceAlgorithm,
) -> Tuple[Optional[int], str]:
    """Count exposure days inside the algorithm window per endpoints."""
    start = (normalize_partial_date(algorithm.window_start)
             if algorithm.window_start.strip() else None)
    end = (normalize_partial_date(algorithm.window_end)
           if algorithm.window_end.strip() else None)
    if start is None or end is None:
        return None, "算法窗口起止日期缺失"
    if (algorithm.window_start_inclusive is None
            or algorithm.window_end_inclusive is None):
        return None, "算法窗口端点包含关系未声明，无法确定窗口内给药日"
    d_start = _to_day(start)
    d_end = _to_day(end)
    if d_start is None or d_end is None:
        return None, "算法窗口日期无法解析"
    count = 0
    for day_txt in day_set:
        day = _to_day(normalize_partial_date(day_txt))
        if day is None:
            return None, "实际给药日精度不足，无法与算法窗口比较"
        if algorithm.window_start_inclusive is False and day == d_start:
            continue
        if algorithm.window_end_inclusive is False and day == d_end:
            continue
        if d_start <= day <= d_end:
            count += 1
    return count, ""


def _planned_pause_day_count(
    *, algorithm: AdherenceAlgorithm,
    episode: IPExposureEpisode,
    assignment: Optional[PlannedTreatmentAssignment],
    planned_actions: Sequence[PlannedExposureAction],
    action_coverage_complete: bool,
) -> Tuple[Optional[int], str]:
    """Planned-pause day count subtracted from the denominator when the
    algorithm excludes planned pauses (§6.2/§6.3)."""
    if algorithm.planned_pause_handling == PLANNED_PAUSE_INCLUDED:
        return 0, ""
    if not action_coverage_complete:
        return None, "计划动作来源覆盖不完整，无法按排除计划暂停计算分母"
    total = 0
    assignment_id = assignment.assignment_id if assignment is not None else ""
    for action in planned_actions:
        if (action.action_type != ACTION_PAUSE
                or action.episode_key != episode.episode_key
                or action.assignment_id != assignment_id
                or action.confirmation_status != CONFIRMATION_CONFIRMED):
            continue
        start = (normalize_partial_date(action.action_start)
                 if action.action_start.strip() else None)
        end = (normalize_partial_date(action.action_end)
               if action.action_end.strip() else None)
        if start is None or end is None or _nv_precision(start) != "day" \
                or _nv_precision(end) != "day":
            return None, "计划暂停起止日期缺失或精度不足，无法计算分母"
        d_start = _to_day(start)
        d_end = _to_day(end)
        if d_start is None or d_end is None:
            return None, "计划暂停日期无法解析"
        total += (d_end - d_start).days + 1
    return total, ""


def _observation_for(
    algorithm: AdherenceAlgorithm,
    observations: Sequence[AdherenceObservation],
) -> Tuple[Optional[AdherenceObservation], Optional[str]]:
    """Select the unique observation for this algorithm+window, deduping
    identical rows; conflicting duplicates fail closed."""
    matching = [o for o in observations
                if (o.algorithm_id == algorithm.algorithm_id
                    and o.window_id == algorithm.window_id)]
    if not matching:
        return None, "缺少该窗口的依从性 observation"
    unique: List[AdherenceObservation] = []
    seen_hashes: Set[str] = set()
    for obs in matching:
        h = content_hash((
            obs.numerator_value, obs.denominator_value, obs.unit,
            obs.numerator_source, obs.denominator_source,
            obs.coverage_complete,
            tuple(loc.locator_id() for loc in obs.item_source_locators),
            obs.accepted_revision))
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        unique.append(obs)
    if len(unique) > 1:
        return None, "存在多个内容不同的重复 observation，无法唯一确定"
    return unique[0], ""


def _convert_unit(value: Decimal, unit: str, algorithm: AdherenceAlgorithm,
                  ) -> Tuple[Optional[Decimal], str]:
    """Convert a value to the algorithm's canonical unit when a versioned
    conversion rule exists; identical units pass through."""
    if _canonical_text(unit) == _canonical_text(algorithm.canonical_unit):
        return value, ""
    for from_unit, to_unit, factor in algorithm.unit_conversion_rules:
        if (_canonical_text(unit) == _canonical_text(from_unit)
                and _canonical_text(to_unit)
                == _canonical_text(algorithm.canonical_unit)):
            try:
                factor_dec = Decimal(str(factor))
            except Exception:
                return None, f"换算系数 {factor!r} 无法解析"
            return value * factor_dec, ""
    return None, (
        f"观察单位 {unit!r} 与算法规范单位 {algorithm.canonical_unit!r} "
        f"不一致且无版本化换算依据")


def _evaluate_adherence_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    occurrences: Sequence[ExposureOccurrence],
    aggregation_policy: Optional[ExposureAggregationPolicy],
    observations: Sequence[AdherenceObservation],
    planned_actions: Sequence[PlannedExposureAction],
    action_coverage_complete: bool,
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    algorithm = expanded.algorithm
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    # Window applicability (algorithm window defines the computation scope).
    overlap = _compare_windows(
        expanded.window, algorithm.window_start, algorithm.window_end,
        algorithm.window_start_inclusive, algorithm.window_end_inclusive,
        containment=False)
    if not overlap.comparable:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=overlap.boundary_reason, rule_lineage=rule_lineage)
    if overlap.outside:
        return IPUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            source_record_refs=(
                _make_source_record_ref(episode.source_locator),))
    if overlap.possibly_overlap:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=overlap.boundary_reason, snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE])

    if aggregation_policy is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="缺少版本化暴露聚合策略，无法计算实际给药日",
            rule_lineage=rule_lineage)
    observation, obs_gap = _observation_for(algorithm, observations)
    if observation is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=obs_gap,
            rule_lineage=rule_lineage)
    if not observation.coverage_complete:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="依从性 observation 覆盖不完整，无法确认分子分母完整",
            rule_lineage=rule_lineage)

    numerator: Optional[int] = None
    denominator: Optional[int] = None
    num_desc = ""
    if algorithm.is_day_ratio:
        daycomp = compute_actual_exposure_days(
            episode=episode, occurrences=occurrences,
            policy=aggregation_policy)
        if daycomp.status == DAY_STATUS_NO_OCCURRENCE:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason=("未找到该 episode 的给药记录；单条缺失不得推断漏服，"
                        "实际给药日不能从治疗跨度推导"),
                rule_lineage=rule_lineage,
                extra_locators=tuple(o.source_locator for o in occurrences))
        if daycomp.status == DAY_STATUS_AMBIGUOUS:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason=daycomp.reason, rule_lineage=rule_lineage)
        if daycomp.status == DAY_STATUS_BOUNDARY:
            return _build_boundary_result(
                project_id=project_id, expanded=expanded, unit_id=unit_id,
                boundary_reason=daycomp.reason, snapshot_id=snapshot_id,
                rule_lineage=rule_lineage,
                audience_suffix=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE],
                source_locators=tuple(o.source_locator for o in occurrences))
        in_window, gap = _days_in_window(daycomp.day_set, algorithm)
        if in_window is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode, reason=gap,
                rule_lineage=rule_lineage)
        numerator = in_window
        num_desc = f"实际给药日 {in_window} 天"
        expected, wgap = _window_day_count(algorithm)
        if expected is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode, reason=wgap,
                rule_lineage=rule_lineage)
        denominator = expected
        pause_days, pgap = _planned_pause_day_count(
            algorithm=algorithm, episode=episode,
            assignment=expanded.assignment,
            planned_actions=planned_actions,
            action_coverage_complete=action_coverage_complete)
        if pause_days is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode, reason=pgap,
                rule_lineage=rule_lineage)
        denominator -= pause_days
        if denominator < 0:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="计划暂停日数超过算法窗口日数，分母计算冲突",
                rule_lineage=rule_lineage)
        if denominator == 0:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="依从性分母为零（零分母按算法策略不可评价）",
                rule_lineage=rule_lineage)
        frac = Fraction(numerator, denominator)
        denominator_desc = str(denominator)
    else:
        if not observation.numerator_value.strip() \
                or not observation.denominator_value.strip():
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="依从性 observation 缺少原始分子或分母值",
                rule_lineage=rule_lineage)
        try:
            num_frac = Fraction(Decimal(observation.numerator_value))
            den_frac = Fraction(Decimal(observation.denominator_value))
        except Exception:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="依从性分子或分母无法解析", rule_lineage=rule_lineage)
        if den_frac == 0:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="依从性分母为零（零分母按算法策略不可评价）",
                rule_lineage=rule_lineage)
        if algorithm.canonical_unit:
            num_converted, cgap = _convert_unit(
                Decimal(observation.numerator_value), observation.unit,
                algorithm)
            if num_converted is None:
                return _not_evaluable_result(
                    unit_id=unit_id, episode=episode, reason=cgap,
                    rule_lineage=rule_lineage)
            num_frac = Fraction(num_converted)
            den_converted, dgap = _convert_unit(
                Decimal(observation.denominator_value), observation.unit,
                algorithm)
            if den_converted is None:
                return _not_evaluable_result(
                    unit_id=unit_id, episode=episode, reason=dgap,
                    rule_lineage=rule_lineage)
            den_frac = Fraction(den_converted)
        num_desc = (f"分子 {observation.numerator_value}{observation.unit}，"
                    f"分母 {observation.denominator_value}{observation.unit}")
        frac = num_frac / den_frac
        denominator_desc = str(den_frac)
    # -- ratio + threshold check -------------------------------------------
    outcome = _check_ratio_against_thresholds(frac, algorithm)
    reason = (
        f"{num_desc}，分母 {denominator_desc}，比值 {outcome.value_desc}"
        f"（算法 {algorithm.algorithm_id} v{algorithm.version}）"
        + (f"；{outcome.reason}" if outcome.reason else ""))
    if outcome.out_of_range:
        if priority_policy is not None:
            priority = priority_policy.priority_for_subtype(
                POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE)
        else:
            priority = MONITORING_PRIORITY_UNKNOWN
        obs_locators = tuple(
            loc for loc in observation.item_source_locators)
        return _build_positive_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            subtype=POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE,
            match_reason=reason, snapshot_id=snapshot_id,
            monitoring_priority=priority, rule_lineage=rule_lineage,
            source_locators=obs_locators)
    if outcome.equality:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=reason, snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_ADHERENCE_OUT_OF_RANGE],
            source_locators=tuple(
                loc for loc in observation.item_source_locators))
    return _negative_result(
        unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
        reason=reason,
        extra_locators=tuple(loc for loc in observation.item_source_locators))


# ---------------------------------------------------------------------------
# Unit-level evaluation: allowed_action
# ---------------------------------------------------------------------------

def _evaluate_allowed_action_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    planned_actions: Sequence[PlannedExposureAction],
    actual_actions: Sequence[ActualIPAction],
    action_coverage_complete: bool,
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    rule = expanded.rule
    gate = _rule_phase_applicability(
        episode=episode, rule=rule, unit_id=unit_id,
        rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    if not action_coverage_complete:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="实际给药动作来源覆盖不完整，无法核对允许条件",
            rule_lineage=rule_lineage)
    assignment_id = expanded.assignment.assignment_id
    actuals = [
        a for a in actual_actions
        if (a.episode_key == episode.episode_key
            and a.assignment_id == assignment_id
            and a.action_type == expanded.action_type)]
    if not actuals:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=(f"未找到该类型（{expanded.action_type}）的实际给药动作；"
                    f"动作记录缺失且无法证明其本应存在，不自动判为允许"),
            rule_lineage=rule_lineage)
    if len(actuals) > 1:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason="同一类型存在多个实际动作记录，且无唯一版本化优先级可解析重叠",
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION],
            source_locators=tuple(a.source_locator for a in actuals
                                  if a.source_locator))
    action = actuals[0]
    if action.confirmation_status != CONFIRMATION_CONFIRMED:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="实际给药动作未获确认，无法核对允许条件",
            rule_lineage=rule_lineage,
            extra_locators=(action.source_locator,) if action.source_locator
            else ())
    # Rule window applicability for the action.
    overlap = _compare_windows(
        expanded.window, rule.window_start, rule.window_end,
        rule.window_start_inclusive, rule.window_end_inclusive)
    if not overlap.comparable:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=overlap.boundary_reason, rule_lineage=rule_lineage)
    if overlap.outside:
        return IPUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            source_record_refs=(
                _make_source_record_ref(episode.source_locator),))
    if overlap.possibly_overlap:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=overlap.boundary_reason, snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION],
            source_locators=(action.source_locator,) if action.source_locator
            else ())
    problems: List[str] = []
    # Dose constraint (50 mg vs 25 mg case).
    if rule.allowed_dose_after_values:
        if not episode.dose_disclosed:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="需要核对调整后剂量但该身份在当前披露范围不可用",
                rule_lineage=rule_lineage)
        actual_after = _canonical_record_value("dose_after", action.dose_after)
        if actual_after is None:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="实际动作调整后剂量缺失或精度不足，无法核对允许值",
                rule_lineage=rule_lineage,
                extra_locators=(action.source_locator,) if action.source_locator
                else ())
        allowed = {
            _canonical_record_value("dose_after", v)
            for v in rule.allowed_dose_after_values}
        if actual_after not in allowed:
            problems.append(
                f"调整后剂量 {action.dose_after} 不在方案允许值 "
                f"{sorted(rule.allowed_dose_after_values)} 内")
    # Reason requirement.
    if rule.allowed_reasons:
        if not action.reason.strip():
            problems.append("给药调整缺少已记录原因")
        elif _canonical_text(action.reason) not in {
                _canonical_text(r) for r in rule.allowed_reasons}:
            problems.append(
                f"给药调整原因 {action.reason!r} 不在方案允许原因"
                f" {list(rule.allowed_reasons)} 内")
    # Planned-action closure (§6.3).
    if rule.planned_action_required:
        planned_matches = [
            p for p in planned_actions
            if (p.episode_key == episode.episode_key
                and p.assignment_id == expanded.assignment.assignment_id
                and p.action_type == expanded.action_type
                and p.confirmation_status == CONFIRMATION_CONFIRMED)]
        if not planned_matches:
            problems.append(
                "实际给药调整缺少对应的已确认计划动作，闭环不完整")
        elif len(planned_matches) > 1:
            return _build_boundary_result(
                project_id=project_id, expanded=expanded, unit_id=unit_id,
                boundary_reason="实际动作对应多个计划动作，动作重叠无唯一版本化优先级可解析",
                snapshot_id=snapshot_id, rule_lineage=rule_lineage,
                audience_suffix=POSITIVE_SUBTYPE_LABELS[
                    POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION],
                source_locators=tuple(p.source_locator for p in planned_matches
                                      if p.source_locator))
    if not problems:
        locs = [locator for locator in (action.source_locator,) if locator]
        return _negative_result(
            unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
            reason=("实际给药调整的类型、原因、前后剂量与方案允许条件及计划"
                    "动作闭环一致"),
            extra_locators=locs)
    match_reason = "；".join(problems)
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(
            POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    locs = [locator for locator in (action.source_locator,) if locator]
    return _build_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        subtype=POSITIVE_SUBTYPE_UNSUPPORTED_IP_ACTION,
        match_reason=match_reason, snapshot_id=snapshot_id,
        monitoring_priority=priority, rule_lineage=rule_lineage,
        source_locators=locs)


# ---------------------------------------------------------------------------
# Unit-level evaluation: medical_action
# ---------------------------------------------------------------------------

def _evaluate_medical_action_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    action_evidence: Sequence[IPActionEvidence],
    trigger_coverage_complete: bool,
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    rule = expanded.rule
    gate = _rule_phase_applicability(
        episode=episode, rule=rule, unit_id=unit_id,
        rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    if not trigger_coverage_complete:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="医学触发来源覆盖不完整，无法核对处置关系",
            rule_lineage=rule_lineage)
    if expanded.trigger_key == "none":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=("未找到该规则对应的医学触发记录；来源行缺失且无法证明"
                    "其本应存在，不自动判为处置关系成立"),
            rule_lineage=rule_lineage)
    matching = [ev for ev in action_evidence
                if ev.stable_source_event_key == expanded.trigger_key]
    if not matching:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="触发事件定位不到对应来源证据",
            rule_lineage=rule_lineage)
    # Dedup by verified link key.
    by_key: Dict[str, IPActionEvidence] = {}
    for ev in matching:
        by_key.setdefault(ev.verified_link_key, ev)
    evidence_rows = [by_key[k] for k in sorted(by_key)]
    if len(evidence_rows) > 1:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason="同一触发事件存在多条不同关联键的证据，关系无法唯一确定",
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT],
            source_locators=tuple(ev.source_locator for ev in evidence_rows))
    ev = evidence_rows[0]
    # Subject/site/episode identity (wrong subject/site/episode never forms
    # a positive/negative; it is not_evaluable context, §7).
    if (ev.subject_ref != episode.subject_ref
            or ev.site_ref != episode.site_ref
            or ev.linked_ip_episode_id != episode.episode_key):
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=("处置关系需要精确的 episode/来源链接；链接缺失或跨受试者"
                    "/中心，无法评价"),
            rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
    if ev.relation_confirmation != CONFIRMATION_CONFIRMED:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="医学触发事件与给药处置的关系尚未确认，无法评价",
            rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
    if rule.trigger_concept and (
            _canonical_text(ev.concept) != _canonical_text(rule.trigger_concept)):
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=("触发事件概念与规则要求不一致，且该记录不能作为处置关系"
                    "裁决依据"),
            rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
    # Time-window comparability.
    ev_window = IPWindowDescriptor(
        span_start=ev.event_start, span_end=ev.event_end,
        applicable_phase=episode.study_phase)
    overlap = _compare_windows(
        ev_window, rule.window_start, rule.window_end,
        rule.window_start_inclusive, rule.window_end_inclusive)
    if not overlap.comparable:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason=overlap.boundary_reason, rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
    if overlap.outside:
        return IPUnitResult(
            unit_id=unit_id, subject_ref=episode.subject_ref,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            source_record_refs=(
                _make_source_record_ref(episode.source_locator),))
    if overlap.possibly_overlap:
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=overlap.boundary_reason, snapshot_id=snapshot_id,
            rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT],
            source_locators=(ev.source_locator,))
    expected = {_canonical_text(a) for a in rule.expected_actions}
    actual_action = _canonical_text(ev.actual_action)
    if actual_action in expected:
        return _negative_result(
            unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
            reason=(f"医学触发事件 {ev.stable_source_event_key} 对应的实际处置"
                    f" {ev.actual_action} 与规则预期一致"),
            extra_locators=(ev.source_locator,))
    if not ev.actual_action.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="触发事件的处置动作记录缺失，无法核对预期处置",
            rule_lineage=rule_lineage,
            extra_locators=(ev.source_locator,))
    match_reason = (
        f"触发事件 {ev.stable_source_event_key} 的实际处置 {ev.actual_action}"
        f" 与规则 {rule.rule_id} 预期 {sorted(rule.expected_actions)} 冲突")
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(
            POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    return _build_positive_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        subtype=POSITIVE_SUBTYPE_MEDICAL_TRIGGER_ACTION_INCONSISTENT,
        match_reason=match_reason, snapshot_id=snapshot_id,
        monitoring_priority=priority, rule_lineage=rule_lineage,
        source_locators=(ev.source_locator,))


# ---------------------------------------------------------------------------
# Unit-level evaluation: accountability (frozen D03 §5.4 decision table)
# ---------------------------------------------------------------------------

def _amount_decimal(value: str) -> Optional[Decimal]:
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _record_totals(
    records: Sequence[IPSemanticRecord],
) -> Tuple[Optional[Decimal], str, Optional[str], List[SourceLocator]]:
    """Sum exact/zero amounts of records sharing one unit.

    Returns (total, unit, gap_reason, locators).  ``unit`` is the single
    canonical source unit of the side ("" when the side does not sum
    cleanly); it is preserved so the accountability balance can convert
    every side to the algorithm's canonical unit before comparison
    (frozen §6.2 rules 1/3).  Range/partial -> boundary via gap_reason
    marker; conflicting or missing units/fields -> not_evaluable reason
    markers.
    """
    total = Decimal(0)
    units: Set[str] = set()
    locators: List[SourceLocator] = []
    for rec in records:
        locators.append(rec.locator)
        if rec.amount_kind in (AMOUNT_KIND_RANGE, AMOUNT_KIND_PARTIAL):
            return None, "", "range", locators
        if rec.amount_kind == AMOUNT_KIND_MISSING \
                or not rec.amount_value.strip() or not rec.amount_unit.strip():
            return None, "", "missing", locators
        if rec.amount_kind not in (AMOUNT_KIND_EXACT, AMOUNT_KIND_ZERO):
            return None, "", "missing", locators
        value = _amount_decimal(rec.amount_value)
        if value is None:
            return None, "", "missing", locators
        units.add(_canonical_text(rec.amount_unit))
        total += value
    if len(units) > 1:
        return None, "", "units", locators
    unit = next(iter(units)) if units else ""
    return total, unit, "", locators


def _evaluate_accountability_unit(
    *, project_id: str, expanded: IPUnitExpanded, unit_id: str,
    snapshot_id: str, rule_lineage: str,
    return_records: Sequence[IPSemanticRecord],
    dispense_records: Sequence[IPSemanticRecord],
    observations: Sequence[AdherenceObservation],
    protocol_return_expectation: str,
    priority_policy: Optional[D03PriorityPolicy],
) -> IPUnitResult:
    episode = expanded.episode
    algorithm = expanded.algorithm
    gate = _binding_gate_result(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        snapshot_id=snapshot_id, rule_lineage=rule_lineage)
    if gate is not None:
        return gate
    if protocol_return_expectation not in RETURN_EXPECTATIONS:
        raise IPSliceError(
            f"protocol_return_expectation={protocol_return_expectation!r} "
            f"invalid")
    # §5.4 decision table.
    episode_returns = [
        r for r in return_records
        if (r.subject_ref == episode.subject_ref
            and r.site_ref == episode.site_ref
            and (not r.linked_ip_episode_key
                 or r.linked_ip_episode_key == episode.episode_key))]
    episode_dispenses = [
        r for r in dispense_records
        if (r.subject_ref == episode.subject_ref
            and r.site_ref == episode.site_ref
            and (not r.linked_ip_episode_key
                 or r.linked_ip_episode_key == episode.episode_key))]
    if not episode_returns:
        if protocol_return_expectation == RETURN_NOT_REQUIRED:
            return IPUnitResult(
                unit_id=unit_id, subject_ref=episode.subject_ref,
                l1_disposition=L1Disposition.NOT_APPLICABLE,
                monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
                source_record_refs=(
                    _make_source_record_ref(episode.source_locator),))
        if protocol_return_expectation == RETURN_EXPECTED:
            reason = ("方案明确期望回收，但完整覆盖中没有可定位的回收记录；"
                      "研究药物核算信息待核实，不得推断未归还或未服药")
        else:
            reason = ("回收记录缺失且无法证明其本应存在；研究药物核算信息"
                      "待核实")
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=reason,
            rule_lineage=rule_lineage)
    return_total, return_unit, return_gap, return_locs = _record_totals(
        episode_returns)
    if return_gap == "range":
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason=("已确认发生回收，但回收量为部分值/范围值，或存在"
                             "多个有版本化依据的换算结果"),
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY],
            source_locators=return_locs)
    if return_gap == "missing":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="回收记录必需字段（数量或单位）为空，无法核算",
            rule_lineage=rule_lineage, extra_locators=return_locs)
    if return_gap == "units":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="回收记录单位不一致且无版本化换算依据，无法核算",
            rule_lineage=rule_lineage, extra_locators=return_locs)
    if not episode_dispenses:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="发放记录缺失，无法完成发放回收核算",
            rule_lineage=rule_lineage)
    dispense_total, dispense_unit, dispense_gap, dispense_locs = _record_totals(
        episode_dispenses)
    if dispense_gap == "range":
        return _build_boundary_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            boundary_reason="发放量为部分值/范围值，核算存在两个可行解释",
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            audience_suffix=POSITIVE_SUBTYPE_LABELS[
                POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY],
            source_locators=dispense_locs)
    if dispense_gap == "missing":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="发放记录必需字段（数量或单位）为空，无法核算",
            rule_lineage=rule_lineage, extra_locators=dispense_locs)
    if dispense_gap == "units":
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="发放记录单位不一致且无版本化换算依据，无法核算",
            rule_lineage=rule_lineage, extra_locators=dispense_locs)
    # Recorded-administered total from the window observation.
    observation, obs_gap = _observation_for(algorithm, observations)
    if observation is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=obs_gap,
            rule_lineage=rule_lineage)
    if not observation.coverage_complete:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="记录给药核算覆盖不完整，无法完成发放回收核算",
            rule_lineage=rule_lineage)
    recorded = _amount_decimal(observation.numerator_value)
    if recorded is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="记录给药总量缺失或无法解析，无法核算",
            rule_lineage=rule_lineage)
    # Frozen §6.2 rules 1/3: convert every side to the algorithm's
    # canonical unit before balance comparison.  Raw values are never
    # compared across units; a missing/conflicting unit or a missing
    # versioned conversion basis fails closed to not_evaluable.
    if not algorithm.canonical_unit.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="算法未声明规范单位，无法完成发放回收核算",
            rule_lineage=rule_lineage,
            extra_locators=return_locs + dispense_locs)
    converted_return, return_gap = _convert_unit(
        return_total, return_unit, algorithm)
    if converted_return is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=return_gap,
            rule_lineage=rule_lineage, extra_locators=return_locs)
    converted_dispense, dispense_gap = _convert_unit(
        dispense_total, dispense_unit, algorithm)
    if converted_dispense is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=dispense_gap,
            rule_lineage=rule_lineage, extra_locators=dispense_locs)
    if not observation.unit.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="记录给药核算缺少单位，无法完成发放回收核算",
            rule_lineage=rule_lineage,
            extra_locators=tuple(loc for loc in observation.item_source_locators))
    converted_recorded, recorded_gap = _convert_unit(
        recorded, observation.unit, algorithm)
    if converted_recorded is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=recorded_gap,
            rule_lineage=rule_lineage,
            extra_locators=tuple(loc for loc in observation.item_source_locators))
    balance = converted_dispense - converted_return
    if balance != converted_recorded:
        match_reason = (
            f"发放 {converted_dispense} 减回收 {converted_return} 为 "
            f"{balance}，与记录给药总量 {converted_recorded} 不一致（规范"
            f"单位 {algorithm.canonical_unit}）")
        # Frozen §6.2: an accountability_proxy positive must carry the exact
        # 按发放/回收核算 annotation on its user-visible evidence and must
        # never be presented as proven actual dosing days.
        extra_evidence: Tuple[EvidenceItem, ...] = ()
        if algorithm.is_accountability_proxy:
            extra_evidence = (_make_evidence_item(
                evidence_id=f"ev-{unit_id}-proxy",
                polarity=L1bEvidencePolarity.SUPPORTING,
                locator=episode.source_locator,
                evidence_role="ip_accountability",
                rule_lineage=rule_lineage,
                uncertainty_note=ACCOUNTABILITY_PROXY_ANNOTATION),)
        if priority_policy is not None:
            priority = priority_policy.priority_for_subtype(
                POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY)
        else:
            priority = MONITORING_PRIORITY_UNKNOWN
        return _build_positive_result(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            subtype=POSITIVE_SUBTYPE_IP_ACCOUNTABILITY_INCONSISTENCY,
            match_reason=match_reason, snapshot_id=snapshot_id,
            monitoring_priority=priority, rule_lineage=rule_lineage,
            source_locators=return_locs + dispense_locs
            + list(observation.item_source_locators),
            extra_evidence=extra_evidence)
    return _negative_result(
        unit_id=unit_id, episode=episode, rule_lineage=rule_lineage,
        reason=("发放减回收与记录给药总量一致，核算闭环成立（按发放/回收"
                "核算口径）"),
        extra_locators=return_locs + dispense_locs)


# ---------------------------------------------------------------------------
# Core evaluation: evaluate_ip_unit
# ---------------------------------------------------------------------------

def evaluate_ip_unit(
    *, project_id: str, expanded: IPUnitExpanded,
    occurrences: Sequence[ExposureOccurrence] = (),
    action_evidence: Sequence[IPActionEvidence] = (),
    planned_actions: Sequence[PlannedExposureAction] = (),
    actual_actions: Sequence[ActualIPAction] = (),
    observations: Sequence[AdherenceObservation] = (),
    return_records: Sequence[IPSemanticRecord] = (),
    dispense_records: Sequence[IPSemanticRecord] = (),
    cm_conflict_rows: Sequence[IPSemanticRecord] = (),
    role_coverage: Optional[Mapping[str, bool]] = None,
    aggregation_policy: Optional[ExposureAggregationPolicy] = None,
    action_coverage_complete: bool = False,
    trigger_coverage_complete: bool = False,
    protocol_return_expectation: str = RETURN_UNKNOWN,
    priority_policy: Optional[D03PriorityPolicy] = None,
    binding_mapping: Optional[AssignmentBindingMapping] = None,
    snapshot_id: str = "",
) -> IPUnitResult:
    """Evaluate one D03 expanded unit (frozen D03 §5).

    Coverage gates are explicit and fail closed: ``role_coverage`` proves
    the semantic roles this unit kind requires; ``action_coverage_complete``
    proves all actual-action rows were read; ``trigger_coverage_complete``
    proves the medical-trigger sources were read; ``protocol_return_
    expectation`` drives the §5.4 return decision table.  An empty record
    sequence alone never proves a complete search.
    """
    if not isinstance(expanded, IPUnitExpanded):
        raise IPSliceError("expanded must be an IPUnitExpanded")
    episode = expanded.episode
    coverage: Mapping[str, bool] = (
        role_coverage if role_coverage is not None else {})
    if binding_mapping is None:
        binding_mapping = expanded.binding_mapping
    unit = expanded.build_unit(project_id, binding_mapping)
    unit_id = unit.unit_id

    # -- CM/IP mutual exclusion (frozen D03 §3.1) --------------------------
    for cm_row in cm_conflict_rows:
        if cm_row.locator.record_id == episode.source_locator.record_id:
            return _not_evaluable_result(
                unit_id=unit_id, episode=episode,
                reason="同一来源行同时映射为 CM 与 IP，角色互斥冲突",
                rule_lineage=D03_RULE_LINEAGE_DEFAULT)

    # -- Required semantic-role coverage gate (§3.1) -----------------------
    gap = _required_roles_for(expanded, coverage)
    if gap is not None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode, reason=gap,
            rule_lineage=D03_RULE_LINEAGE_DEFAULT)

    # -- Role/phase confirmation gate (§4) ---------------------------------
    if not episode.role_confirmed or not episode.actual_treatment_role.strip():
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="缺少已确认的治疗角色，不得合并角色/阶段建立单元结论",
            rule_lineage=D03_RULE_LINEAGE_DEFAULT)
    if expanded.resolution.is_bound and expanded.assignment is None:
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="episode 已绑定但缺少 assignment 对象，无法评价",
            rule_lineage=D03_RULE_LINEAGE_DEFAULT)

    rule_lineage = (expanded.rule.rule_lineage if expanded.rule is not None
                    else D03_RULE_LINEAGE_DEFAULT)

    if (expanded.control_item in (CONTROL_PLAN_ACTUAL,
                                  CONTROL_ALLOWED_ACTION,
                                  CONTROL_MEDICAL_ACTION)
            and expanded.rule is None):
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="缺少适用的方案规则，当前无法评价",
            rule_lineage=rule_lineage)
    if (expanded.control_item in (CONTROL_ADHERENCE, CONTROL_ACCOUNTABILITY)
            and expanded.algorithm is None):
        return _not_evaluable_result(
            unit_id=unit_id, episode=episode,
            reason="缺少适用的依从性算法，当前无法评价",
            rule_lineage=rule_lineage)

    if expanded.control_item == CONTROL_ROLE_PHASE:
        return _evaluate_role_phase_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_PLAN_ACTUAL:
        return _evaluate_plan_actual_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            occurrences=occurrences,
            aggregation_policy=aggregation_policy,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_ADHERENCE:
        return _evaluate_adherence_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            occurrences=occurrences,
            aggregation_policy=aggregation_policy,
            observations=observations,
            planned_actions=planned_actions,
            action_coverage_complete=action_coverage_complete,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_ALLOWED_ACTION:
        return _evaluate_allowed_action_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            planned_actions=planned_actions,
            actual_actions=actual_actions,
            action_coverage_complete=action_coverage_complete,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_MEDICAL_ACTION:
        return _evaluate_medical_action_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            action_evidence=action_evidence,
            trigger_coverage_complete=trigger_coverage_complete,
            priority_policy=priority_policy)
    if expanded.control_item == CONTROL_ACCOUNTABILITY:
        return _evaluate_accountability_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            snapshot_id=snapshot_id, rule_lineage=rule_lineage,
            return_records=return_records,
            dispense_records=dispense_records,
            observations=observations,
            protocol_return_expectation=protocol_return_expectation,
            priority_policy=priority_policy)

    return _not_evaluable_result(
        unit_id=unit_id, episode=episode,
        reason=f"未识别的控制项 {expanded.control_item!r}，当前无法评价",
        rule_lineage=rule_lineage)


# ---------------------------------------------------------------------------
# Slice-level evaluation (frozen D03 §4, §10)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IPEpisodeRollup:
    """Read-only episode rollup preserving all child unit ids and flags."""

    episode_key: str
    subject_ref: str
    child_unit_ids: Tuple[str, ...]
    has_positive: bool
    has_boundary: bool
    has_not_evaluable: bool
    has_negative: bool
    source_record_count: int


@dataclass(frozen=True)
class IPSliceResult:
    """Aggregate result of evaluating one or more D03 units for a subject."""

    subject_ref: str
    unit_results: Tuple[IPUnitResult, ...]
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    expected_set_hash: str = ""
    rule_lineage: str = ""

    @property
    def candidate_count(self) -> int:
        return len(self.r2_candidates)

    @property
    def positive_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.POSITIVE)

    @property
    def negative_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NEGATIVE)

    @property
    def boundary_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.BOUNDARY)

    @property
    def not_evaluable_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NOT_EVALUABLE)

    @property
    def not_applicable_count(self) -> int:
        return sum(1 for r in self.unit_results
                   if r.l1_disposition == L1Disposition.NOT_APPLICABLE)

    def episode_rollups(
        self, expansions: IPExpectedSetExpansion,
    ) -> Tuple[IPEpisodeRollup, ...]:
        """Build read-only episode rollups preserving all child unit ids."""
        unit_by_expanded: Dict[str, IPUnitResult] = {
            r.unit_id: r for r in self.unit_results}
        rollups: List[IPEpisodeRollup] = []
        by_episode: Dict[str, List[IPUnitExpanded]] = {}
        for eu in expansions.units:
            by_episode.setdefault(eu.episode.episode_key, []).append(eu)
        for ep_key, eus in by_episode.items():
            child_ids: List[str] = []
            has_pos = has_bnd = has_ne = has_neg = False
            src_loc_ids: Set[str] = set()
            for eu in eus:
                unit = eu.build_unit(expansions.project_id)
                uid = unit.unit_id
                child_ids.append(uid)
                r = unit_by_expanded.get(uid)
                if r is None:
                    continue
                if r.l1_disposition == L1Disposition.POSITIVE:
                    has_pos = True
                elif r.l1_disposition == L1Disposition.BOUNDARY:
                    has_bnd = True
                elif r.l1_disposition == L1Disposition.NOT_EVALUABLE:
                    has_ne = True
                elif r.l1_disposition == L1Disposition.NEGATIVE:
                    has_neg = True
                for sref in r.source_record_refs:
                    src_loc_ids.add(sref.locator.locator_id())
            rollups.append(IPEpisodeRollup(
                episode_key=ep_key,
                subject_ref=eus[0].episode.subject_ref,
                child_unit_ids=tuple(sorted(set(child_ids))),
                has_positive=has_pos, has_boundary=has_bnd,
                has_not_evaluable=has_ne, has_negative=has_neg,
                source_record_count=len(src_loc_ids)))
        return tuple(rollups)


def evaluate_ip_slice(
    *, project_id: str, episodes: Sequence[IPExposureEpisode],
    assignments: Sequence[PlannedTreatmentAssignment] = (),
    active_rules: Sequence[ProtocolExposureRule] = (),
    adherence_algorithms: Sequence[AdherenceAlgorithm] = (),
    action_evidence: Sequence[IPActionEvidence] = (),
    occurrences: Sequence[ExposureOccurrence] = (),
    planned_actions: Sequence[PlannedExposureAction] = (),
    actual_actions: Sequence[ActualIPAction] = (),
    observations: Sequence[AdherenceObservation] = (),
    return_records: Sequence[IPSemanticRecord] = (),
    dispense_records: Sequence[IPSemanticRecord] = (),
    cm_conflict_rows: Sequence[IPSemanticRecord] = (),
    role_coverage: Optional[Mapping[str, bool]] = None,
    aggregation_policy: Optional[ExposureAggregationPolicy] = None,
    action_coverage_complete: bool = False,
    trigger_coverage_complete: bool = False,
    protocol_return_expectation: str = RETURN_UNKNOWN,
    priority_policy: Optional[D03PriorityPolicy] = None,
    binding_mapping: Optional[AssignmentBindingMapping] = None,
    snapshot_id: str = "",
) -> Dict[str, IPSliceResult]:
    """Evaluate multiple D03 units, grouped by subject (frozen D03 §4, §11).

    Returns a mapping of subject_ref -> IPSliceResult.  Each unit gets
    exactly one L1 disposition; episode rollups are read-only views that
    preserve sibling flags (positive/boundary/not_evaluable independent).
    """
    expansions = expand_ip_expected_set(
        project_id=project_id, episodes=episodes,
        assignments=assignments, active_rules=active_rules,
        adherence_algorithms=adherence_algorithms,
        action_evidence=action_evidence,
        binding_mapping=binding_mapping)
    results: List[IPUnitResult] = []
    for eu in expansions.units:
        r = evaluate_ip_unit(
            project_id=project_id, expanded=eu,
            occurrences=occurrences, action_evidence=action_evidence,
            planned_actions=planned_actions, actual_actions=actual_actions,
            observations=observations,
            return_records=return_records,
            dispense_records=dispense_records,
            cm_conflict_rows=cm_conflict_rows,
            role_coverage=role_coverage,
            aggregation_policy=aggregation_policy,
            action_coverage_complete=action_coverage_complete,
            trigger_coverage_complete=trigger_coverage_complete,
            protocol_return_expectation=protocol_return_expectation,
            priority_policy=priority_policy,
            binding_mapping=binding_mapping, snapshot_id=snapshot_id)
        results.append(r)
    by_subject: Dict[str, List[IPUnitResult]] = {}
    for r in results:
        by_subject.setdefault(r.subject_ref, []).append(r)
    out: Dict[str, IPSliceResult] = {}
    for subj, urs in by_subject.items():
        subj_cands = [c for r in urs for c in r.r2_candidates]
        out[subj] = IPSliceResult(
            subject_ref=subj, unit_results=tuple(urs),
            r2_candidates=tuple(subj_cands),
            expected_set_hash=expansions.expected_set_hash,
            rule_lineage=D03_RULE_LINEAGE_DEFAULT)
    return out
