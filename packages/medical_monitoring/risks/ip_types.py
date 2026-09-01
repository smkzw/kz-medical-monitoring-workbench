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

from ..domain.identity import make_risk_identity
from ..domain.risk import RiskCandidate, RiskIdentity
from ..intelligence.normalization import NormalizedValue, normalize_partial_date

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
