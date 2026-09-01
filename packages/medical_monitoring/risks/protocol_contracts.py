"""Protocol compliance contracts and immutable value objects."""

from __future__ import annotations

import datetime
import itertools
from dataclasses import dataclass
from types import MappingProxyType
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Set,
                    Tuple)

from ..domain.identity import make_risk_identity
from ..domain.risk import RiskCandidate, RiskIdentity
from ..intelligence.normalization import normalize_partial_date

from .contracts import (
    CrossDomainEvidenceRef,
    EvaluationUnit,
    EvidenceItem,
    L0CoverageStatus,
    L1Disposition,
    L1bEvidencePolarity,
    MONITORING_PRIORITY_HIGH,
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
# Domain identity
# ---------------------------------------------------------------------------

D04_DOMAIN = "D04_protocol_compliance"
D04_UNIT_ALGO_VERSION = "d04_unit_v1"
D04_RULE_LINEAGE_DEFAULT = "d04-protocol-rule-v1"


# ---------------------------------------------------------------------------
# Closed enums (frozen D04 contract)
# ---------------------------------------------------------------------------

#: Closed owner-domain set (routing decision table §3.2).
OWNER_D02 = "D02_cm"
OWNER_D03 = "D03_ip_exposure"
OWNER_D04 = "D04_protocol_compliance"
OWNER_D05 = "D05_visit_window"          # synthetic stub owner, not accepted
OWNER_D08 = "D08_multi_table_relation"
OWNER_UNRESOLVED = "owner_unresolved"
OWNER_DOMAINS: Tuple[str, ...] = (
    OWNER_D02, OWNER_D03, OWNER_D04, OWNER_D05, OWNER_D08, OWNER_UNRESOLVED,
)

#: Closed control-point types (§3.2).
CONTROL_INCLUSION = "inclusion"
CONTROL_EXCLUSION = "exclusion"
CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT = "prohibited_or_restricted_treatment"
CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT = "required_procedure_or_assessment"
CONTROL_DOSE_OR_TREATMENT_MANAGEMENT = "dose_or_treatment_management"
CONTROL_DISCONTINUATION_OR_WITHDRAWAL = "discontinuation_or_withdrawal"
CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT = "consent_randomization_enrollment"
CONTROL_OTHER_PROTOCOL_REQUIREMENT = "other_protocol_requirement"
CONTROL_TYPES: Tuple[str, ...] = (
    CONTROL_INCLUSION,
    CONTROL_EXCLUSION,
    CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT,
    CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT,
    CONTROL_DOSE_OR_TREATMENT_MANAGEMENT,
    CONTROL_DISCONTINUATION_OR_WITHDRAWAL,
    CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
    CONTROL_OTHER_PROTOCOL_REQUIREMENT,
)

#: Closed signal types (§5): never ``|``-joined free strings.
SIGNAL_INCLUSION = "inclusion"
SIGNAL_EXCLUSION = "exclusion"
SIGNAL_REQUIRED_PROTOCOL_ACTION = "required_protocol_action"
SIGNAL_DISCONTINUATION_OR_WITHDRAWAL = "discontinuation_or_withdrawal"
SIGNAL_CONSENT_RANDOMIZATION_ENROLLMENT = "consent_randomization_enrollment"
SIGNAL_OTHER_PROTOCOL_REQUIREMENT = "other_protocol_requirement"
SIGNAL_PROTOCOL_APPLICABILITY = "protocol_applicability"
SIGNAL_PROTOCOL_ROUTING = "protocol_routing"
SIGNAL_TYPES: Tuple[str, ...] = (
    SIGNAL_INCLUSION,
    SIGNAL_EXCLUSION,
    SIGNAL_REQUIRED_PROTOCOL_ACTION,
    SIGNAL_DISCONTINUATION_OR_WITHDRAWAL,
    SIGNAL_CONSENT_RANDOMIZATION_ENROLLMENT,
    SIGNAL_OTHER_PROTOCOL_REQUIREMENT,
    SIGNAL_PROTOCOL_APPLICABILITY,
    SIGNAL_PROTOCOL_ROUTING,
)

#: Closed evaluation-node ids (§5).
NODE_ATOMIC = "atomic"
NODE_PACKAGE = "package"
NODE_APPLICABILITY_GATE = "applicability_gate"
NODE_ROUTING_GATE = "routing_gate"
NODE_IDS: Tuple[str, ...] = (
    NODE_ATOMIC, NODE_PACKAGE, NODE_APPLICABILITY_GATE, NODE_ROUTING_GATE,
)

#: Closed evaluation-anchor kinds (§5, §7.2) -- never interchangeable.
ANCHOR_SCREENING = "screening"
ANCHOR_CONSENT = "consent"
ANCHOR_RANDOMIZATION = "randomization"
ANCHOR_FIRST_DOSE = "first_dose"
ANCHOR_ON_TREATMENT = "on_treatment"
ANCHOR_DISCONTINUATION = "discontinuation"
ANCHOR_OTHER = "other"
ANCHOR_KINDS: Tuple[str, ...] = (
    ANCHOR_SCREENING, ANCHOR_CONSENT, ANCHOR_RANDOMIZATION, ANCHOR_FIRST_DOSE,
    ANCHOR_ON_TREATMENT, ANCHOR_DISCONTINUATION, ANCHOR_OTHER,
)

PRECISION_DAY = "day"
PRECISION_MONTH = "month"
PRECISION_YEAR = "year"
PRECISION_UNKNOWN = "unknown"
PRECISIONS: Tuple[str, ...] = (
    PRECISION_DAY, PRECISION_MONTH, PRECISION_YEAR, PRECISION_UNKNOWN,
)

INCLUSIVITY_INCLUSIVE = "inclusive"
INCLUSIVITY_EXCLUSIVE = "exclusive"
INCLUSIVITY_MIXED = "mixed"
INCLUSIVITY_UNSTATED = "unstated"
INCLUSIVITY_GATE = "gate"
INCLUSIVITIES: Tuple[str, ...] = (
    INCLUSIVITY_INCLUSIVE, INCLUSIVITY_EXCLUSIVE, INCLUSIVITY_MIXED,
    INCLUSIVITY_UNSTATED, INCLUSIVITY_GATE,
)

APPLICABILITY_UNIQUE_ACTIVE = "unique_active"
APPLICABILITY_MULTI_FEASIBLE_BOUNDARY = "multi_feasible_boundary"
APPLICABILITY_NOT_EVALUABLE = "not_evaluable"
APPLICABILITY_STATUSES: Tuple[str, ...] = (
    APPLICABILITY_UNIQUE_ACTIVE,
    APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
    APPLICABILITY_NOT_EVALUABLE,
)

#: Closed component issue-predicate results (§5).
ISSUE_TRUE = "issue_true"
ISSUE_FALSE = "issue_false"
ISSUE_BOUNDARY = "boundary"
ISSUE_NOT_EVALUABLE = "not_evaluable"
ISSUE_NOT_APPLICABLE = "not_applicable"
ISSUE_RESULTS: Tuple[str, ...] = (
    ISSUE_TRUE, ISSUE_FALSE, ISSUE_BOUNDARY, ISSUE_NOT_EVALUABLE,
    ISSUE_NOT_APPLICABLE,
)

#: Closed parent-issue-expression operators (§5).
EXPR_AND = "AND"
EXPR_OR = "OR"
EXPR_NOT = "NOT"
EXPR_AT_LEAST_N = "AT_LEAST_N"
EXPR_OPERATORS: Tuple[str, ...] = (
    EXPR_AND, EXPR_OR, EXPR_NOT, EXPR_AT_LEAST_N,
)

#: Closed structured-rule operators (§3.3).  ``combination`` must be
#: decomposed into a package expression; an atomic rule carrying it fails
#: closed at evaluation time.
OP_EXISTS = "exists"
OP_NOT_EXISTS = "not_exists"
OP_EQUALS = "equals"
OP_NOT_EQUALS = "not_equals"
OP_SET_MEMBERSHIP = "set_membership"
OP_NUMERIC_AT_LEAST = "numeric_at_least"
OP_NUMERIC_AT_MOST = "numeric_at_most"
OP_NUMERIC_ABOVE = "numeric_above"
OP_NUMERIC_BELOW = "numeric_below"
OP_WITHIN_RANGE = "within_range"
OP_TEMPORAL_ORDER = "temporal_order"
OP_TEMPORAL_INCLUSION = "temporal_inclusion"
OP_DURATION = "duration"
OP_COUNT = "count"
OP_AGE = "age"
OP_DISCONTINUATION_TRIGGER = "discontinuation_trigger"
OP_SEQUENCE = "sequence"
OP_APPROVED_EXCEPTION = "approved_exception"
OP_INVESTIGATOR_JUDGMENT = "investigator_judgment"
OPERATORS: Tuple[str, ...] = (
    OP_EXISTS, OP_NOT_EXISTS, OP_EQUALS, OP_NOT_EQUALS, OP_SET_MEMBERSHIP,
    OP_NUMERIC_AT_LEAST, OP_NUMERIC_AT_MOST, OP_NUMERIC_ABOVE,
    OP_NUMERIC_BELOW, OP_WITHIN_RANGE, OP_TEMPORAL_ORDER,
    OP_TEMPORAL_INCLUSION, OP_DURATION, OP_COUNT, OP_AGE,
    OP_DISCONTINUATION_TRIGGER, OP_SEQUENCE, OP_APPROVED_EXCEPTION,
    OP_INVESTIGATOR_JUDGMENT,
)

#: Closed exception-effect classes (§7.3).
EXCEPTION_PROTOCOL_DEFINED = "protocol_defined_exception"
EXCEPTION_EFFECTIVE_RULE_CHANGE = "effective_rule_change"
EXCEPTION_URGENT_HAZARD = "urgent_hazard_justification"
EXCEPTION_RETROSPECTIVE = "retrospective_explanation"
EXCEPTION_UNRESOLVED = "unresolved"
EXCEPTION_EFFECTS: Tuple[str, ...] = (
    EXCEPTION_PROTOCOL_DEFINED,
    EXCEPTION_EFFECTIVE_RULE_CHANGE,
    EXCEPTION_URGENT_HAZARD,
    EXCEPTION_RETROSPECTIVE,
    EXCEPTION_UNRESOLVED,
)

#: Closed cross-domain relation types (§7.4).
RELATION_ELIGIBILITY_FACT = "eligibility_fact"
RELATION_EXPOSURE_FACT = "exposure_fact"
RELATION_VISIT_FACT = "visit_fact"
RELATION_DISPOSITION_FACT = "disposition_fact"
RELATION_UNCONFIRMED = "unconfirmed"
RELATION_TYPES: Tuple[str, ...] = (
    RELATION_ELIGIBILITY_FACT, RELATION_EXPOSURE_FACT, RELATION_VISIT_FACT,
    RELATION_DISPOSITION_FACT, RELATION_UNCONFIRMED,
)

#: Closed journey-join reasons (§7.4).
JOIN_UNIT_IDENTITY = "unit_identity"
JOIN_ANCHOR_EVENT = "anchor_event"
JOIN_SOURCE_LOCATOR = "source_locator"
JOIN_PRODUCER_REFERENCE = "producer_reference"
JOIN_REASONS: Tuple[str, ...] = (
    JOIN_UNIT_IDENTITY, JOIN_ANCHOR_EVENT, JOIN_SOURCE_LOCATOR,
    JOIN_PRODUCER_REFERENCE,
)

#: Closed coverage-gap reason codes (§6.4).
GAP_APPLICABILITY_UNDETERMINED = "applicability_undetermined"
GAP_RULE_NOT_VERIFIED = "rule_not_verified"
GAP_EXPRESSION_INCOMPLETE = "expression_incomplete"
GAP_SOURCE_ROLE_NOT_COVERED = "source_role_not_covered"
GAP_EVIDENCE_IDENTITY_UNCONFIRMED = "evidence_identity_unconfirmed"
GAP_VALUE_MISSING = "value_missing"
GAP_UNIT_UNCONVERTIBLE = "unit_unconvertible"
GAP_TEMPORAL_UNCOMPARABLE = "temporal_uncomparable"
GAP_IE_SUMMARY_ONLY = "ie_summary_only"
GAP_FREE_TEXT_ONLY = "free_text_only"
GAP_RETEST_UNCONFIRMED = "retest_unconfirmed"
GAP_EXCEPTION_UNRESOLVED = "exception_unresolved"
GAP_ROUTING_UNRESOLVED = "routing_unresolved"
GAP_INVESTIGATOR_JUDGMENT_MISSING = "investigator_judgment_missing"
GAP_RECORD_MISSING_UNPROVEN = "record_missing_unproven"
GAP_RELATION_UNCONFIRMED = "relation_unconfirmed"
GAP_PRODUCER_DEPENDENCY = "producer_dependency_not_evaluable"
GAP_AGE_ALGORITHM_UNFROZEN = "age_algorithm_unfrozen"
GAP_COMPONENT_GAP_DETERMINATE = "component_gap_with_determinate_l1"
GAP_UNKNOWN_OPERATOR = "unknown_operator"
GAP_REASON_CODES: Tuple[str, ...] = (
    GAP_APPLICABILITY_UNDETERMINED,
    GAP_RULE_NOT_VERIFIED,
    GAP_EXPRESSION_INCOMPLETE,
    GAP_SOURCE_ROLE_NOT_COVERED,
    GAP_EVIDENCE_IDENTITY_UNCONFIRMED,
    GAP_VALUE_MISSING,
    GAP_UNIT_UNCONVERTIBLE,
    GAP_TEMPORAL_UNCOMPARABLE,
    GAP_IE_SUMMARY_ONLY,
    GAP_FREE_TEXT_ONLY,
    GAP_RETEST_UNCONFIRMED,
    GAP_EXCEPTION_UNRESOLVED,
    GAP_ROUTING_UNRESOLVED,
    GAP_INVESTIGATOR_JUDGMENT_MISSING,
    GAP_RECORD_MISSING_UNPROVEN,
    GAP_RELATION_UNCONFIRMED,
    GAP_PRODUCER_DEPENDENCY,
    GAP_AGE_ALGORITHM_UNFROZEN,
    GAP_COMPONENT_GAP_DETERMINATE,
    GAP_UNKNOWN_OPERATOR,
)

#: Closed positive primary subtypes (§6.1) -- one per unit.
SUBTYPE_INCLUSION_NOT_MET = "inclusion_requirement_not_met"
SUBTYPE_EXCLUSION_PRESENT = "exclusion_condition_present"
SUBTYPE_REQUIRED_ACTION_NOT_MET = "required_protocol_action_not_met"
SUBTYPE_DISCONTINUATION_INCONSISTENT = (
    "discontinuation_or_withdrawal_requirement_inconsistent")
SUBTYPE_CONSENT_SEQUENCE_INCONSISTENT = "consent_randomization_sequence_inconsistent"
SUBTYPE_OTHER_REQUIREMENT_INCONSISTENT = "other_protocol_requirement_inconsistent"
POSITIVE_SUBTYPES: Tuple[str, ...] = (
    SUBTYPE_INCLUSION_NOT_MET,
    SUBTYPE_EXCLUSION_PRESENT,
    SUBTYPE_REQUIRED_ACTION_NOT_MET,
    SUBTYPE_DISCONTINUATION_INCONSISTENT,
    SUBTYPE_CONSENT_SEQUENCE_INCONSISTENT,
    SUBTYPE_OTHER_REQUIREMENT_INCONSISTENT,
)

#: Chinese audience labels (§8.2) -- the only user-visible positive labels.
SUBTYPE_LABELS: Dict[str, str] = {
    SUBTYPE_INCLUSION_NOT_MET: "入选条件待核实",
    SUBTYPE_EXCLUSION_PRESENT: "排除条件待核实",
    SUBTYPE_REQUIRED_ACTION_NOT_MET: "方案要求执行情况待核实",
    SUBTYPE_DISCONTINUATION_INCONSISTENT: "退出或终止参与标准待核实",
    SUBTYPE_CONSENT_SEQUENCE_INCONSISTENT: "知情与入组时序待核实",
    SUBTYPE_OTHER_REQUIREMENT_INCONSISTENT: "方案执行情况待核实",
}

#: Closed enrollment query contexts (§8.3).
QUERY_CONTEXT_NOT_OCCURRED = "enrollment_not_occurred"
QUERY_CONTEXT_ENROLLED = "enrolled_or_post_enrollment"
QUERY_CONTEXT_UNRESOLVED = "enrollment_state_unresolved"
QUERY_CONTEXTS: Tuple[str, ...] = (
    QUERY_CONTEXT_NOT_OCCURRED, QUERY_CONTEXT_ENROLLED,
    QUERY_CONTEXT_UNRESOLVED,
)

#: Closed amendment transition scopes (§2.3).
TRANSITION_NEW_ENROLLMENT_ONLY = "new_enrollment_only"
TRANSITION_EXISTING_CONTINUE_OLD = "existing_continue_old"
TRANSITION_ALL_SWITCH = "all_switch"
TRANSITION_NEXT_VISIT_OR_RECONSENT = "next_visit_or_reconsent"
TRANSITION_UNDETERMINED = "undetermined"
TRANSITION_SCOPES: Tuple[str, ...] = (
    TRANSITION_NEW_ENROLLMENT_ONLY,
    TRANSITION_EXISTING_CONTINUE_OLD,
    TRANSITION_ALL_SWITCH,
    TRANSITION_NEXT_VISIT_OR_RECONSENT,
    TRANSITION_UNDETERMINED,
)

ROUNDING_BEFORE = "compare_before_rounding"
ROUNDING_AFTER = "compare_after_rounding"
ROUNDING_POLICIES: Tuple[str, ...] = (ROUNDING_BEFORE, ROUNDING_AFTER)

#: Closed routing claim kinds (frozen routing decision table §3.2).
CLAIM_CONCOMITANT_MEDICATION = "concomitant_medication"
CLAIM_IP_DOSING_ACTION = "ip_dosing_action"
CLAIM_VISIT_WINDOW = "visit_window"
CLAIM_MULTI_TABLE_RELATION = "multi_table_relation"
CLAIM_ELIGIBILITY = "eligibility"
CLAIM_SEQUENCE = "sequence"
CLAIM_DISPOSITION = "disposition"
CLAIM_OTHER = "other"
CLAIM_KINDS: Tuple[str, ...] = (
    CLAIM_CONCOMITANT_MEDICATION, CLAIM_IP_DOSING_ACTION, CLAIM_VISIT_WINDOW,
    CLAIM_MULTI_TABLE_RELATION, CLAIM_ELIGIBILITY, CLAIM_SEQUENCE,
    CLAIM_DISPOSITION, CLAIM_OTHER,
)

#: Condition verdicts used internally by component evaluation.
VERDICT_MET = "met"
VERDICT_UNMET = "unmet"
VERDICT_BOUNDARY = "boundary"
VERDICT_NOT_EVALUABLE = "not_evaluable"
VERDICT_NOT_APPLICABLE = "not_applicable"
VERDICTS: Tuple[str, ...] = (
    VERDICT_MET, VERDICT_UNMET, VERDICT_BOUNDARY, VERDICT_NOT_EVALUABLE,
    VERDICT_NOT_APPLICABLE,
)

#: Semantic roles that are auxiliary-only (§4.1): they may hint at a
#: candidate but can never alone prove a criterion met or unmet.
AUXILIARY_ONLY_ROLES: Tuple[str, ...] = (
    "aggregate_ie_status", "deviation_listing", "monitoring_note",
    "email_or_edc_note",
)

#: Chinese labels for evaluation anchors (user-visible Query text).
_ANCHOR_LABELS: Dict[str, str] = {
    ANCHOR_SCREENING: "筛选期",
    ANCHOR_CONSENT: "知情同意时点",
    ANCHOR_RANDOMIZATION: "随机化时点",
    ANCHOR_FIRST_DOSE: "首次给药时点",
    ANCHOR_ON_TREATMENT: "治疗期",
    ANCHOR_DISCONTINUATION: "退出/终止参与时点",
    ANCHOR_OTHER: "评价时点",
}

#: Chinese labels for gap reason codes (coverage-gap audience text).
_GAP_LABELS: Dict[str, str] = {
    GAP_APPLICABILITY_UNDETERMINED: "适用方案版本无法唯一确定",
    GAP_RULE_NOT_VERIFIED: "规则抽取未经来源验证",
    GAP_EXPRESSION_INCOMPLETE: "组合逻辑或表达式不完整",
    GAP_SOURCE_ROLE_NOT_COVERED: "必需来源角色覆盖不完整",
    GAP_EVIDENCE_IDENTITY_UNCONFIRMED: "证据身份或时间关系未确认",
    GAP_VALUE_MISSING: "关键数值缺失",
    GAP_UNIT_UNCONVERTIBLE: "单位未知或无可信换算",
    GAP_TEMPORAL_UNCOMPARABLE: "日期缺失或精度不足，无法比较",
    GAP_IE_SUMMARY_ONLY: "仅有 IE/汇总结论，无逐条标准证据",
    GAP_FREE_TEXT_ONLY: "仅有自由文本或未定位摘要，无逐条标准证据",
    GAP_RETEST_UNCONFIRMED: "复测政策或复测证据未确认",
    GAP_EXCEPTION_UNRESOLVED: "例外/豁免效力或适用性未确认",
    GAP_ROUTING_UNRESOLVED: "控制点归属路由无法唯一确定",
    GAP_INVESTIGATOR_JUDGMENT_MISSING: "研究者判断缺失",
    GAP_RECORD_MISSING_UNPROVEN: "未见记录但无法证明来源完整覆盖",
    GAP_RELATION_UNCONFIRMED: "跨域关系未确认或身份不匹配",
    GAP_PRODUCER_DEPENDENCY: "所依赖的上游评价暂无法评价",
    GAP_AGE_ALGORITHM_UNFROZEN: "年龄算法未冻结，无法计算年龄",
    GAP_COMPONENT_GAP_DETERMINATE: "存在未决子条件缺口，医学完整性受阻",
    GAP_UNKNOWN_OPERATOR: "规则运算子不受支持，无法评价",
}


def positive_subtype_audience_label(subtype: str) -> str:
    """Return the frozen Chinese audience label for a positive subtype
    (§8.2).  Engineering tokens are never user-visible."""
    if subtype not in SUBTYPE_LABELS:
        raise ProtocolSliceError(f"unknown positive subtype {subtype!r}")
    return SUBTYPE_LABELS[subtype]


def _signal_type_for_control(control_point_type: str) -> str:
    """Map a D04-native control point type to its closed signal type."""
    if control_point_type == CONTROL_INCLUSION:
        return SIGNAL_INCLUSION
    if control_point_type == CONTROL_EXCLUSION:
        return SIGNAL_EXCLUSION
    if control_point_type == CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT:
        return SIGNAL_REQUIRED_PROTOCOL_ACTION
    if control_point_type == CONTROL_DISCONTINUATION_OR_WITHDRAWAL:
        return SIGNAL_DISCONTINUATION_OR_WITHDRAWAL
    if control_point_type == CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT:
        return SIGNAL_CONSENT_RANDOMIZATION_ENROLLMENT
    if control_point_type == CONTROL_OTHER_PROTOCOL_REQUIREMENT:
        return SIGNAL_OTHER_PROTOCOL_REQUIREMENT
    raise ProtocolSliceError(
        f"control point type {control_point_type!r} is not D04-native")


def _subtype_for_control(control_point_type: str) -> str:
    if control_point_type == CONTROL_INCLUSION:
        return SUBTYPE_INCLUSION_NOT_MET
    if control_point_type == CONTROL_EXCLUSION:
        return SUBTYPE_EXCLUSION_PRESENT
    if control_point_type == CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT:
        return SUBTYPE_REQUIRED_ACTION_NOT_MET
    if control_point_type == CONTROL_DISCONTINUATION_OR_WITHDRAWAL:
        return SUBTYPE_DISCONTINUATION_INCONSISTENT
    if control_point_type == CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT:
        return SUBTYPE_CONSENT_SEQUENCE_INCONSISTENT
    if control_point_type == CONTROL_OTHER_PROTOCOL_REQUIREMENT:
        return SUBTYPE_OTHER_REQUIREMENT_INCONSISTENT
    raise ProtocolSliceError(
        f"control point type {control_point_type!r} has no D04 subtype")


class ProtocolSliceError(Exception):
    """A D04 protocol slice evaluation invariant was violated."""


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def _validate_nonempty(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProtocolSliceError(
            f"{field_name} is required and must be a non-empty string")
    return value


def _validate_optional_str(value: Any, field_name: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ProtocolSliceError(f"{field_name} must be a string or None")
    return value


def _freeze_tuple(value: Any, field_name: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise ProtocolSliceError(
            f"{field_name} must be a sequence, not a string")
    try:
        result: Tuple[str, ...] = tuple(value)
    except TypeError:
        raise ProtocolSliceError(f"{field_name} must be iterable")
    for item in result:
        if not isinstance(item, str):
            raise ProtocolSliceError(
                f"{field_name} members must be strings, got "
                f"{type(item).__name__}")
    return result


def _canonical_sorted(value: Sequence[str]) -> Tuple[str, ...]:
    """Deduplicated, deterministically sorted tuple of non-empty strings."""
    seen: List[str] = []
    for item in value:
        s = str(item).strip()
        if s and s not in seen:
            seen.append(s)
    return tuple(sorted(seen))


def _date_precision(raw: str) -> str:
    """Precision of a raw date string (day/month/year/unknown) using the
    frozen R3 partial-date normalization; never silently padded."""
    if not raw.strip():
        return PRECISION_UNKNOWN
    nv = normalize_partial_date(raw)
    if not nv.normalized:
        return PRECISION_UNKNOWN
    parts = str(nv.normalized).split("-")
    if len(parts) == 3:
        return PRECISION_DAY
    if len(parts) == 2:
        return PRECISION_MONTH
    if len(parts) == 1:
        return PRECISION_YEAR
    return PRECISION_UNKNOWN


def _day_date(raw: str) -> Optional[datetime.date]:
    """Parse a day-precision date, or None when missing/partial/invalid."""
    if not raw.strip():
        return None
    nv = normalize_partial_date(raw)
    if not nv.normalized or _date_precision(raw) != PRECISION_DAY:
        return None
    try:
        return datetime.date.fromisoformat(str(nv.normalized))
    except (ValueError, TypeError):
        return None


def _date_interval(
    raw: str,
) -> Optional[Tuple[Optional[datetime.date], Optional[datetime.date]]]:
    """Earliest/latest day-dates implied by a partial date.

    ``"2026-01-15"`` -> (d, d); ``"2026-01"`` -> (Jan 1, Jan 31);
    ``"2026"`` -> (Jan 1, Dec 31); missing/invalid -> None.  Comparison
    happens on the shared precision only: a strict inequality on the
    intervals is determinate, an overlap is boundary (challenge 37).
    """
    if not raw.strip():
        return None
    nv = normalize_partial_date(raw)
    if not nv.normalized:
        return None
    parts = str(nv.normalized).split("-")
    try:
        if len(parts) == 3:
            d = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
            return (d, d)
        if len(parts) == 2:
            y, m = int(parts[0]), int(parts[1])
            start = datetime.date(y, m, 1)
            if m == 12:
                end = datetime.date(y, 12, 31)
            else:
                end = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
            return (start, end)
        if len(parts) == 1:
            y = int(parts[0])
            return (datetime.date(y, 1, 1), datetime.date(y, 12, 31))
    except (ValueError, TypeError):
        return None
    return None


def _parse_decimal(value: str) -> Optional[Decimal]:
    if not value.strip():
        return None
    try:
        return Decimal(value.strip())
    except Exception:
        return None


def _round_decimal(value: Decimal, precision: int, mode: str) -> Decimal:
    quantum = Decimal(1).scaleb(-precision)
    rounding = {
        "round_half_up": ROUND_HALF_UP,
        "floor": ROUND_FLOOR,
        "ceiling": ROUND_CEILING,
    }.get(mode, ROUND_HALF_UP)
    return value.quantize(quantum, rounding=rounding)


def _interval_relation(
    a: Tuple[Optional[datetime.date], Optional[datetime.date]],
    b: Tuple[Optional[datetime.date], Optional[datetime.date]],
) -> str:
    """Determinate ordering between two partial-date intervals.

    Returns ``"before"`` / ``"after"`` / ``"equal_day"`` /
    ``"possibly_overlap"``.  Only strict interval separation is
    determinate; coarse-precision equality stays boundary.
    """
    a_lo, a_hi = a
    b_lo, b_hi = b
    if a_hi < b_lo:
        return "before"
    if a_lo > b_hi:
        return "after"
    if a_lo == a_hi and b_lo == b_hi and a_lo == b_lo:
        return "equal_day"
    return "possibly_overlap"


# ---------------------------------------------------------------------------
# Structured rule and comparison spec (§3.3)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RuleComparison:
    """Versioned numeric/count/duration comparison semantics.

    ``comparison`` is one of ``at_least|at_most|above|below|equals|
    not_equals|within_range``.  Inclusivity is explicit; ``None`` means
    unstated (a value exactly on the endpoint is boundary, §7.1).
    Rounding policy is versioned: ``compare_before_rounding`` compares the
    raw value, ``compare_after_rounding`` rounds first (challenge 21).
    """

    comparison: str
    threshold: str = ""
    threshold_upper: str = ""
    lower_inclusive: Optional[bool] = None
    upper_inclusive: Optional[bool] = None
    canonical_unit: str = ""
    rounding_policy: str = ROUNDING_BEFORE
    rounding_precision: int = 0
    rounding_mode: str = "round_half_up"

    def __post_init__(self) -> None:
        valid = ("at_least", "at_most", "above", "below", "equals",
                 "not_equals", "within_range")
        if self.comparison not in valid:
            raise ProtocolSliceError(
                f"RuleComparison.comparison={self.comparison!r} invalid")
        if self.comparison in ("equals", "not_equals"):
            if not self.threshold.strip():
                raise ProtocolSliceError(
                    f"RuleComparison {self.comparison} requires threshold")
        elif self.comparison == "within_range":
            if (not self.threshold.strip()
                    or not self.threshold_upper.strip()):
                raise ProtocolSliceError(
                    "within_range requires threshold and threshold_upper")
        else:
            if not self.threshold.strip():
                raise ProtocolSliceError(
                    f"RuleComparison {self.comparison} requires threshold")
        if self.rounding_policy not in ROUNDING_POLICIES:
            raise ProtocolSliceError(
                f"rounding_policy={self.rounding_policy!r} invalid")
        if self.rounding_precision < 0:
            raise ProtocolSliceError("rounding_precision must be >= 0")


@dataclass(frozen=True)
class ProtocolStructuredRule:
    """Versioned controlled structured rule (§3.3).

    Only controlled operators/values/units/anchors may be executed by the
    generic kernel; no free expression is ever evaluated.  Missing
    equality semantics, unit conversion, rounding order, window endpoints,
    retest priority or exception conditions fail closed -- the kernel never
    infers them.
    """

    operator: str
    value_set: Tuple[str, ...] = ()
    comparison: Optional[RuleComparison] = None
    canonical_unit: str = ""
    temporal_anchor: str = ANCHOR_OTHER
    evaluation_window_start: str = ""
    evaluation_window_end: str = ""
    window_start_inclusive: Optional[bool] = None
    window_end_inclusive: Optional[bool] = None
    required_evidence_roles: Tuple[str, ...] = ()
    alternate_evidence_roles: Tuple[str, ...] = ()
    retest_or_confirmation_policy: str = ""
    exception_or_waiver_policy: str = ""
    missing_or_conflict_policy: str = ""
    rule_priority_policy: str = ""
    # exists / not_exists target role
    exists_target_role: str = ""
    # temporal order (OP_TEMPORAL_ORDER / OP_SEQUENCE)
    order_direction: str = ""
    anchor_role_a: str = ""
    anchor_role_b: str = ""
    # duration (OP_DURATION)
    duration_min: str = ""
    duration_min_inclusive: Optional[bool] = None
    # count (OP_COUNT)
    count_comparison: str = ""
    count_threshold: int = 0
    # age (OP_AGE)
    age_algorithm_id: str = ""
    # discontinuation trigger (OP_DISCONTINUATION_TRIGGER)
    trigger_comparison: Optional[RuleComparison] = None
    expected_disposition_values: Tuple[str, ...] = ()
    disposition_window_days: str = ""
    # investigator judgment
    investigator_judgment_required: bool = False

    def __post_init__(self) -> None:
        if self.operator not in OPERATORS:
            raise ProtocolSliceError(
                f"operator={self.operator!r} is not a controlled operator")
        if self.temporal_anchor not in ANCHOR_KINDS:
            raise ProtocolSliceError(
                f"temporal_anchor={self.temporal_anchor!r} invalid")
        object.__setattr__(self, "value_set",
                           tuple(self.value_set))
        object.__setattr__(self, "required_evidence_roles",
                           tuple(self.required_evidence_roles))
        object.__setattr__(self, "alternate_evidence_roles",
                           tuple(self.alternate_evidence_roles))
        object.__setattr__(self, "expected_disposition_values",
                           tuple(self.expected_disposition_values))
        if self.operator in (OP_NUMERIC_AT_LEAST, OP_NUMERIC_AT_MOST,
                             OP_NUMERIC_ABOVE, OP_NUMERIC_BELOW,
                             OP_WITHIN_RANGE, OP_COUNT, OP_AGE):
            if self.comparison is None:
                raise ProtocolSliceError(
                    f"operator {self.operator} requires a RuleComparison")
        if self.operator in (OP_EQUALS, OP_NOT_EQUALS, OP_SET_MEMBERSHIP):
            if not self.value_set:
                raise ProtocolSliceError(
                    f"operator {self.operator} requires a non-empty value_set")
        if self.operator == OP_WITHIN_RANGE:
            if self.comparison.comparison != "within_range":
                raise ProtocolSliceError(
                    "within_range operator requires within_range comparison")
        if self.operator == OP_TEMPORAL_ORDER:
            if (self.order_direction not in ("before", "after",
                                             "not_after", "not_before")
                    or not self.anchor_role_a.strip()
                    or not self.anchor_role_b.strip()):
                raise ProtocolSliceError(
                    "temporal_order requires order_direction + roles a/b")
        if self.operator == OP_SEQUENCE:
            if (self.order_direction not in ("before", "after", "not_after",
                                             "not_before")
                    or not self.anchor_role_a.strip()
                    or not self.anchor_role_b.strip()):
                raise ProtocolSliceError(
                    "sequence requires order_direction + roles a/b")
        if self.operator == OP_DURATION:
            if not self.duration_min.strip():
                raise ProtocolSliceError(
                    "duration requires duration_min")
        if self.operator == OP_COUNT:
            if self.count_comparison not in ("at_least", "at_most", "equals"):
                raise ProtocolSliceError(
                    f"count_comparison={self.count_comparison!r} invalid")
            if self.count_threshold < 0:
                raise ProtocolSliceError("count_threshold must be >= 0")
        if self.operator == OP_EXISTS or self.operator == OP_NOT_EXISTS:
            if not self.exists_target_role.strip():
                raise ProtocolSliceError(
                    f"{self.operator} requires exists_target_role")
        if self.operator == OP_DISCONTINUATION_TRIGGER:
            if self.trigger_comparison is None:
                raise ProtocolSliceError(
                    "discontinuation_trigger requires trigger_comparison")
            if not self.expected_disposition_values:
                raise ProtocolSliceError(
                    "discontinuation_trigger requires "
                    "expected_disposition_values")
            if "disposition" not in self.required_evidence_roles:
                object.__setattr__(
                    self, "required_evidence_roles",
                    tuple(self.required_evidence_roles) + ("disposition",))
        if self.operator == OP_APPROVED_EXCEPTION:
            raise ProtocolSliceError(
                "approved_exception is not an executable atomic operator; "
                "exceptions bind through ProtocolExceptionBinding")
        if self.operator == OP_INVESTIGATOR_JUDGMENT:
            if not self.investigator_judgment_required:
                raise ProtocolSliceError(
                    "investigator_judgment operator requires "
                    "investigator_judgment_required=True")
        if self.operator in (OP_NUMERIC_AT_LEAST, OP_NUMERIC_AT_MOST,
                             OP_NUMERIC_ABOVE, OP_NUMERIC_BELOW,
                             OP_WITHIN_RANGE, OP_COUNT):
            if self.comparison.comparison == "within_range" and \
                    self.operator != OP_WITHIN_RANGE:
                raise ProtocolSliceError(
                    "within_range comparison is only valid for the "
                    "within_range operator")
        if not self.required_evidence_roles:
            raise ProtocolSliceError(
                "structured rule requires required_evidence_roles")


@dataclass(frozen=True)
class IssueExpression:
    """Controlled parent issue expression (§5).

    The expression always means "whether this evaluation root has a
    protocol issue" and references only component ids.  The protocol
    decomposer converts original wording ("至少满足任一入选子条件" etc.)
    into this expression; the raw connective is never copied mechanically.
    """

    operator: str
    component_ids: Tuple[str, ...]
    at_least_n: int = 0

    def __post_init__(self) -> None:
        if self.operator not in EXPR_OPERATORS:
            raise ProtocolSliceError(
                f"issue expression operator={self.operator!r} invalid")
        ids = _freeze_tuple(self.component_ids, "IssueExpression.component_ids")
        if self.operator == EXPR_NOT:
            if len(ids) != 1:
                raise ProtocolSliceError(
                    "NOT expression requires exactly one component id")
        else:
            if not ids:
                raise ProtocolSliceError(
                    f"{self.operator} expression requires >=1 component id")
        if len(set(ids)) != len(ids):
            raise ProtocolSliceError(
                "issue expression contains duplicate component ids")
        object.__setattr__(self, "component_ids", ids)
        if self.operator == EXPR_AT_LEAST_N:
            if not (1 <= self.at_least_n <= len(ids)):
                raise ProtocolSliceError(
                    "AT_LEAST_N requires 1 <= at_least_n <= len(component_ids)")

    def truth_value(
        self, assignment: Mapping[str, bool],
    ) -> bool:
        if self.operator == EXPR_AND:
            return all(assignment[cid] for cid in self.component_ids)
        if self.operator == EXPR_OR:
            return any(assignment[cid] for cid in self.component_ids)
        if self.operator == EXPR_NOT:
            return not assignment[self.component_ids[0]]
        if self.operator == EXPR_AT_LEAST_N:
            return sum(1 for cid in self.component_ids
                       if assignment[cid]) >= self.at_least_n
        raise ProtocolSliceError(
            f"unknown issue expression operator {self.operator!r}")


# ---------------------------------------------------------------------------
# Protocol control points and components (§3.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolControlPoint:
    """One official protocol control point (evaluation root).

    The original numbering, heading, order, nesting, footnotes and
    "以下任一/全部/除外" logic are preserved verbatim.  An atomic root
    carries a structured rule; a package root carries a parent issue
    expression over its atomic component ids.  Neither the official
    numbering nor a derived id is fabricated: when no official criterion
    id exists a stable derived id is generated and marked as derived
    (challenge 10).
    """

    control_point_id: str
    control_point_type: str
    official_section_id: str
    official_criterion_id: str
    official_heading: str
    evaluation_root_kind: str
    display_order: str
    nesting_path: str
    verbatim_text: str
    source_locator: SourceLocator
    source_revision_hash: str
    extraction_status: str
    verification_status: str
    structured_rule: Optional[ProtocolStructuredRule] = None
    issue_expression: Optional[IssueExpression] = None
    component_ids: Tuple[str, ...] = ()
    parent_rule_id: str = ""
    derived_id_note: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.control_point_id,
                           "ProtocolControlPoint.control_point_id")
        if self.control_point_type not in CONTROL_TYPES:
            raise ProtocolSliceError(
                f"control_point_type={self.control_point_type!r} invalid")
        _validate_nonempty(self.official_section_id,
                           "ProtocolControlPoint.official_section_id")
        if self.evaluation_root_kind not in (NODE_ATOMIC, NODE_PACKAGE):
            raise ProtocolSliceError(
                f"evaluation_root_kind={self.evaluation_root_kind!r} invalid")
        if self.extraction_status not in ("verified", "unverified"):
            raise ProtocolSliceError(
                f"extraction_status={self.extraction_status!r} invalid")
        if self.verification_status not in ("verified", "unverified"):
            raise ProtocolSliceError(
                f"verification_status={self.verification_status!r} invalid")
        if not isinstance(self.source_locator, SourceLocator):
            raise ProtocolSliceError(
                "ProtocolControlPoint.source_locator must be a SourceLocator")
        if self.evaluation_root_kind == NODE_ATOMIC:
            if self.structured_rule is None:
                raise ProtocolSliceError(
                    "atomic control point requires structured_rule")
            if self.issue_expression is not None or self.component_ids:
                raise ProtocolSliceError(
                    "atomic control point must not carry issue_expression/"
                    "component_ids")
        else:
            if self.issue_expression is None:
                raise ProtocolSliceError(
                    "package control point requires issue_expression")
            ids = _freeze_tuple(self.component_ids,
                                "ProtocolControlPoint.component_ids")
            if not ids:
                raise ProtocolSliceError(
                    "package control point requires component_ids")
            for cid in ids:
                if cid not in self.issue_expression.component_ids:
                    raise ProtocolSliceError(
                        f"package component {cid!r} is not referenced by "
                        f"the issue expression")
            object.__setattr__(self, "component_ids", ids)
        object.__setattr__(self, "parent_rule_id",
                           _validate_optional_str(
                               self.parent_rule_id,
                               "ProtocolControlPoint.parent_rule_id"))
        if not self.official_criterion_id.strip():
            derived = f"d04-{self.control_point_id}"
            object.__setattr__(self, "official_criterion_id", derived)
            note = self.derived_id_note or (
                "无官方编号，使用稳定派生编号；显示时始终回连方案原文定位")
            object.__setattr__(self, "derived_id_note", note)

    def signal_type(self) -> str:
        return _signal_type_for_control(self.control_point_type)

    def positive_subtype(self) -> str:
        return _subtype_for_control(self.control_point_type)


@dataclass(frozen=True)
class ProtocolComponent:
    """One atomic condition under a package standard.

    Components keep the official ids, parent rule id, display order,
    nesting path and verbatim text.  They are NOT EvaluationUnits: only
    the evaluation root (atomic or package) enters the expected-set, L1,
    L2 and lifecycle (§5).
    """

    component_id: str
    control_point_id: str
    official_criterion_id: str
    parent_rule_id: str
    display_order: str
    nesting_path: str
    verbatim_text: str
    source_locator: SourceLocator
    source_revision_hash: str
    structured_rule: ProtocolStructuredRule
    verification_status: str = "verified"

    def __post_init__(self) -> None:
        _validate_nonempty(self.component_id, "ProtocolComponent.component_id")
        _validate_nonempty(self.control_point_id,
                           "ProtocolComponent.control_point_id")
        if self.verification_status not in ("verified", "unverified"):
            raise ProtocolSliceError(
                f"verification_status={self.verification_status!r} invalid")
        if not isinstance(self.source_locator, SourceLocator):
            raise ProtocolSliceError(
                "ProtocolComponent.source_locator must be a SourceLocator")
        if not isinstance(self.structured_rule, ProtocolStructuredRule):
            raise ProtocolSliceError(
                "ProtocolComponent.structured_rule must be a "
                "ProtocolStructuredRule")
        if not self.official_criterion_id.strip():
            object.__setattr__(
                self, "official_criterion_id",
                f"d04-{self.component_id}")


@dataclass(frozen=True)
class ProtocolRuleEvaluationPlan:
    """Frozen plan of which official nodes are evaluation roots (§5).

    ``verification_status`` must be ``verified`` for a root to be
    evaluated; when the original wording is ambiguous ("需满足下列标准"
    with no determinable 任一/全部/至少 N), the plan stays unverified and
    the whole root is ``not_evaluable`` -- AND/OR is never defaulted
    (challenge 82).  The lineage fields feed the unit rule lineage.
    """

    plan_id: str
    protocol_id: str
    protocol_version: str
    amendment_id_or_hash: str
    rule_content_hash: str
    extraction_hash: str
    mapping_version: str
    unit_term_policy_version: str
    verification_status: str
    root_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.plan_id, "ProtocolRuleEvaluationPlan.plan_id")
        _validate_nonempty(self.protocol_id,
                           "ProtocolRuleEvaluationPlan.protocol_id")
        _validate_nonempty(self.protocol_version,
                           "ProtocolRuleEvaluationPlan.protocol_version")
        if self.verification_status not in ("verified", "unverified"):
            raise ProtocolSliceError(
                f"plan verification_status={self.verification_status!r} "
                f"invalid")
        ids = _freeze_tuple(self.root_ids, "ProtocolRuleEvaluationPlan.root_ids")
        object.__setattr__(self, "root_ids", ids)


# ---------------------------------------------------------------------------
# Protocol applicability (§2.3, §5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolVersionRecord:
    """One versioned protocol/amendment input record (synthetic/versioned).

    The kernel never defaults to the latest version, a project-wide
    activation date, or the event-nearest version: version selection uses
    approval/effective dates, site adoption, transition scope and the
    subject event time (§2.3 resolution order).
    """

    protocol_id: str
    protocol_version: str
    amendment_id_or_hash: str
    approval_date: str
    effective_start: str
    effective_end: str
    rule_content_hash: str
    extraction_hash: str
    transition_scope: str = TRANSITION_UNDETERMINED
    new_enrollment_only: Optional[bool] = None
    re_consent_required: Optional[bool] = None
    site_adoption_start: str = ""
    site_adoption_end: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.protocol_id,
                           "ProtocolVersionRecord.protocol_id")
        _validate_nonempty(self.protocol_version,
                           "ProtocolVersionRecord.protocol_version")
        if self.transition_scope not in TRANSITION_SCOPES:
            raise ProtocolSliceError(
                f"transition_scope={self.transition_scope!r} invalid")
        if not self.effective_start.strip():
            raise ProtocolSliceError(
                "ProtocolVersionRecord.effective_start is required")


def feasible_version_fingerprint(
    *, protocol_id: str, protocol_version: str, amendment_id_or_hash: str,
    approval_date: str, effective_start: str, effective_end: str,
    transition_scope: str, new_enrollment_only: Optional[bool],
    re_consent_required: Optional[bool],
    rule_content_hash: str = "", extraction_hash: str = "",
    cohort: str = "", phase: str = "", arm: str = "",
    treatment_role: str = "", control_point_applicability: str = "",
) -> str:
    """Deterministic content fingerprint of one feasible version.

    Feasible-version fingerprints are sorted before they enter the
    applicability-gate lineage, so input order never changes the gate unit
    id or expected-set hash (challenge 83).
    """
    return "d04-vfp-" + content_hash({
        "protocol_id": protocol_id,
        "protocol_version": protocol_version,
        "amendment_id_or_hash": amendment_id_or_hash,
        "approval_date": approval_date,
        "effective_start": effective_start,
        "effective_end": effective_end,
        "transition_scope": transition_scope,
        "new_enrollment_only": new_enrollment_only,
        "re_consent_required": re_consent_required,
        "rule_content_hash": rule_content_hash,
        "extraction_hash": extraction_hash,
        "cohort": cohort,
        "phase": phase,
        "arm": arm,
        "treatment_role": treatment_role,
        "control_point_applicability": control_point_applicability,
    })


def protocol_applicability_id(
    *, subject_ref: str, site_ref: str, decision_anchor_kind: str,
    decision_anchor_precision: str, feasible_version_fingerprints:
        Sequence[str], stable_source_content_key: str,
) -> str:
    """Canonical content id of one applicability decision.

    Hashes subject/site, decision anchor, date precision, sorted feasible
    version fingerprints and the stable source content key.  It never
    contains run/snapshot/revision ids (§5).
    """
    fingerprints = _canonical_sorted(feasible_version_fingerprints)
    return "d04-appl-" + content_hash({
        "subject_ref": subject_ref,
        "site_ref": site_ref,
        "decision_anchor_kind": decision_anchor_kind,
        "decision_anchor_precision": decision_anchor_precision,
        "feasible_version_fingerprints": list(fingerprints),
        "stable_source_content_key": stable_source_content_key,
    })


@dataclass(frozen=True)
class ProtocolApplicabilityDecision:
    """The mandatory per-subject applicability decision (§2.3).

    ``decision_status`` is closed: ``unique_active`` produces the normal
    evaluation-root units; ``multi_feasible_boundary`` / ``not_evaluable``
    produce exactly one subject-level applicability gate unit per stable
    decision (affected control point ids and feasible version ids live only
    in the decision/context -- never as N per-control-point gates, §5).
    """

    subject_ref: str
    site_ref: str
    decision_time_anchor: str
    decision_time_anchor_date: str
    decision_status: str
    protocol_id: str = ""
    protocol_version: str = ""
    amendment_id_or_hash: str = ""
    ethics_or_authority_approval_date: str = ""
    effective_start: str = ""
    effective_end: str = ""
    site_activation_or_adoption_start: str = ""
    site_activation_or_adoption_end: str = ""
    amendment_transition_scope: str = TRANSITION_UNDETERMINED
    grandfathering_policy: str = ""
    new_enrollment_only: Optional[bool] = None
    re_consent_requirement: Optional[bool] = None
    re_consent_actual_status: str = ""
    cohort: str = ""
    phase: str = ""
    arm: str = ""
    treatment_role: str = ""
    control_point_applicability: str = ""
    subject_applicability: Optional[bool] = None
    event_time_rule_scope: str = ""
    source_locators: Tuple[SourceLocator, ...] = ()
    feasible_version_fingerprints: Tuple[str, ...] = ()
    stable_source_content_key: str = ""
    not_applicable_control_point_ids: Tuple[str, ...] = ()
    affected_control_point_ids: Tuple[str, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref,
                           "ProtocolApplicabilityDecision.subject_ref")
        _validate_nonempty(self.site_ref,
                           "ProtocolApplicabilityDecision.site_ref")
        _validate_nonempty(
            self.stable_source_content_key,
            "ProtocolApplicabilityDecision.stable_source_content_key")
        if self.decision_time_anchor not in ANCHOR_KINDS:
            raise ProtocolSliceError(
                f"decision_time_anchor={self.decision_time_anchor!r} invalid")
        if self.decision_status not in APPLICABILITY_STATUSES:
            raise ProtocolSliceError(
                f"decision_status={self.decision_status!r} invalid")
        if self.amendment_transition_scope not in TRANSITION_SCOPES:
            raise ProtocolSliceError(
                f"amendment_transition_scope="
                f"{self.amendment_transition_scope!r} invalid")
        fps = _canonical_sorted(self.feasible_version_fingerprints)
        object.__setattr__(self, "feasible_version_fingerprints", fps)
        object.__setattr__(self, "source_locators",
                           tuple(self.source_locators))
        object.__setattr__(
            self, "not_applicable_control_point_ids",
            _canonical_sorted(self.not_applicable_control_point_ids))
        object.__setattr__(
            self, "affected_control_point_ids",
            _canonical_sorted(self.affected_control_point_ids))
        anchor_precision = _date_precision(self.decision_time_anchor_date)
        computed = protocol_applicability_id(
            subject_ref=self.subject_ref, site_ref=self.site_ref,
            decision_anchor_kind=self.decision_time_anchor,
            decision_anchor_precision=anchor_precision,
            feasible_version_fingerprints=fps,
            stable_source_content_key=self.stable_source_content_key)
        object.__setattr__(self, "_applicability_id", computed)
        if self.decision_status == APPLICABILITY_UNIQUE_ACTIVE:
            if not self.protocol_id.strip() or not self.protocol_version.strip():
                raise ProtocolSliceError(
                    "unique_active applicability requires protocol_id and "
                    "protocol_version")
            if not fps:
                raise ProtocolSliceError(
                    "unique_active applicability requires one feasible "
                    "version fingerprint")

    @property
    def applicability_precision(self) -> str:
        return _date_precision(self.decision_time_anchor_date)

    @property
    def protocol_applicability_id(self) -> str:
        return self._applicability_id
