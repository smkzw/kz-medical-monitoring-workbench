"""R4-D04 protocol compliance slice -- domain model, applicability gates,
rule-expression evaluation, evidence gates, Chinese Query drafts and
coverage-gap notices.

Frozen source of truth: ``FROZEN_R4_D04_CONTRACT_V1_1`` (§§1-13).  This
module implements the D04 protocol domain on top of the shared
``RiskDomainUnitResult`` protocol, reusing the accepted R1 coverage, R2
identity/lifecycle and R3 normalization public contracts.  It does not
copy lifecycle, identity, Query or coverage implementations.

Design constraints enforced here (frozen D04 contract):

1. Immutable value objects with fail-closed invariant validation; closed
   owner-domain and signal-type enums; no ``|``-joined free signal types.
2. Deterministic canonical identities: the eight frozen EvaluationUnit hash
   dimensions, sorted applicability-gate fingerprints, canonical
   ``protocol_applicability_id`` and N->N+1-compatible R2 risk identities.
3. One EvaluationUnit per atomic/package evaluation root; component
   assessments are separate stable ids and never enter expected-set/L1/L2/
   lifecycle.
4. AND/OR/NOT/AT_LEAST_N parent issue-expression evaluation over feasible
   truth assignments of boundary/not_evaluable components; L0/L1
   orthogonality with coverage-gap notices blocking domain completeness.
5. Exact cross-domain evidence gates (subject/site/producer unit/stable
   source event/content hash/rule+component/comparable window/relation
   type); producer-owned control points are routed out and only surface as
   typed producer references.
6. not_evaluable units carry zero candidate/risk/Query; three-part Chinese
   Query wording is conditional on the enrollment context.
7. Deterministic counts (expected = five L1 buckets; coverage-gap notices
   are separate from Query counts) and delegated routing lists.

All data is synthetic/offline.  No real project, provider, threshold,
listing layout, visit window, medication rule or service.
"""

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

__all__ = [
    # Domain identity
    "D04_DOMAIN",
    "D04_UNIT_ALGO_VERSION",
    "D04_RULE_LINEAGE_DEFAULT",
    # Closed enums
    "OWNER_DOMAINS",
    "OWNER_D02",
    "OWNER_D03",
    "OWNER_D04",
    "OWNER_D05",
    "OWNER_D08",
    "OWNER_UNRESOLVED",
    "CONTROL_TYPES",
    "SIGNAL_TYPES",
    "NODE_IDS",
    "ANCHOR_KINDS",
    "PRECISIONS",
    "INCLUSIVITIES",
    "APPLICABILITY_STATUSES",
    "ISSUE_RESULTS",
    "EXPR_OPERATORS",
    "OPERATORS",
    "EXCEPTION_EFFECTS",
    "RELATION_TYPES",
    "JOIN_REASONS",
    "GAP_REASON_CODES",
    "POSITIVE_SUBTYPES",
    "SUBTYPE_LABELS",
    "QUERY_CONTEXTS",
    "TRANSITION_SCOPES",
    "ROUNDING_POLICIES",
    "CLAIM_KINDS",
    # Errors
    "ProtocolSliceError",
    # Value objects
    "ProtocolControlPoint",
    "ProtocolComponent",
    "RuleComparison",
    "ProtocolStructuredRule",
    "IssueExpression",
    "ProtocolRuleEvaluationPlan",
    "ProtocolVersionRecord",
    "ProtocolApplicabilityDecision",
    "ProtocolControlRoutingRecord",
    "ProtocolDelegatedControlPoint",
    "RuleEvidenceRequirement",
    "RuleEvidenceBinding",
    "ProtocolExceptionBinding",
    "UnitConversionRule",
    "RetestOutcome",
    "ProtocolComponentAssessment",
    "ProtocolCoverageGapNotice",
    "D04PriorityPolicy",
    "EnrollmentContext",
    "EvaluationWindowSpec",
    "CrossDomainGateOutcome",
    "RegulatoryGuidanceVersion",
    "ProtocolJourneyEvent",
    "ProtocolRiskMarker",
    "ProtocolEventMarkerJoin",
    "ProtocolProducerReference",
    "ProtocolUnitExpanded",
    "ProtocolExpectedSetExpansion",
    "ProtocolUnitResult",
    "ProtocolSliceResult",
    # Functions
    "positive_subtype_audience_label",
    "policy_content_hash_value",
    "protocol_applicability_id",
    "feasible_version_fingerprint",
    "build_protocol_unit",
    "expected_set_hash",
    "expand_protocol_expected_set",
    "build_rule_evidence_requirement",
    "expand_rule_evidence_requirements",
    "route_control_point",
    "resolve_protocol_applicability",
    "resolve_regulatory_guidance",
    "resolve_enrollment_context",
    "verify_cross_domain_ref",
    "component_issue_predicate",
    "evaluate_issue_expression",
    "evaluate_component_condition",
    "evaluate_protocol_unit",
    "evaluate_protocol_slice",
]


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


def _version_covers_event(
    version: ProtocolVersionRecord, event_date: datetime.date,
    version_lo: datetime.date, version_hi: Optional[datetime.date],
) -> bool:
    if version_lo > event_date:
        return False
    if version_hi is not None and event_date > version_hi:
        return False
    return True


def _version_supported_at_enrollment(
    version: ProtocolVersionRecord, enroll_day: datetime.date,
    adoption_lo: Optional[datetime.date],
) -> bool:
    """True when a predecessor version was in force at the subject's
    enrollment time: approved, its effective interval covers the day and
    the site adoption (when given) had started (§2.3
    existing_continue_old).  The version's own ``effective_end`` may lie
    before the evaluated event -- the explicit transition keeps existing
    subjects on the old version, so project-wide end dates never by
    themselves force the subject onto the amendment."""
    if not version.approval_date.strip():
        return False
    lo = _day_date(version.effective_start)
    if lo is None or enroll_day < lo:
        return False
    hi = (_day_date(version.effective_end)
          if version.effective_end.strip() else None)
    if hi is not None and enroll_day > hi:
        return False
    if adoption_lo is not None and enroll_day < adoption_lo:
        return False
    return True


def resolve_protocol_applicability(
    *,
    subject_ref: str, site_ref: str, event_anchor_kind: str,
    event_anchor_date: str,
    versions: Sequence[ProtocolVersionRecord],
    site_adoption_start: str = "", site_adoption_end: str = "",
    adoption_start_inclusive: Optional[bool] = None,
    adoption_end_inclusive: Optional[bool] = None,
    subject_enrollment_date: str = "",
    subject_consent_date: str = "",
    subject_randomization_date: str = "",
    subject_first_dose_date: str = "",
    cohort: str = "", phase: str = "", arm: str = "",
    treatment_role: str = "", control_point_applicability: str = "",
    event_time_rule_scope: str = "",
    stable_source_content_key: str = "",
    source_locators: Sequence[SourceLocator] = (),
) -> ProtocolApplicabilityDecision:
    """Resolve the unique active protocol version (§2.3 fixed order).

    1. Explicit protocol/amendment link (the caller may pass exactly one
       version; then its effective interval still must cover the event).
    2. Ethics/authority approval and site adoption dates.
    3. Amendment transition scope -- assessed BEFORE the feasible-count
       shortcut (corrective 03): ``all_switch`` keeps the interval/
       adoption behaviour only without a re-consent dependency;
       ``new_enrollment_only`` requires a day-comparable enrollment date
       (missing -> not_evaluable) and grandfathers pre-amendment
       enrollees; ``existing_continue_old`` keeps the unique predecessor
       supported at the subject's enrollment time (zero -> not_evaluable,
       two -> boundary, never the amendment); ``next_visit_or_reconsent``
       or any ``re_consent_required=True`` and ``undetermined`` return one
       not_evaluable gate -- the subject is never pushed onto a newer
       version merely because its effective/site interval covers the event.
    4. Subject event times (consent/randomization/first dose/enrollment).
    5. Cohort/phase/arm/treatment role and control-point applicability.
    6. Only when all conditions yield exactly one active version.

    Never defaults to the latest version or the event-nearest version.
    Missing/conflicting key dates -> ``not_evaluable``; two or more
    feasible versions with support -> ``multi_feasible_boundary``.
    """
    if event_anchor_kind not in ANCHOR_KINDS:
        raise ProtocolSliceError(
            f"event_anchor_kind={event_anchor_kind!r} invalid")
    if not versions:
        raise ProtocolSliceError("at least one ProtocolVersionRecord required")
    if not stable_source_content_key.strip():
        raise ProtocolSliceError(
            "resolve_protocol_applicability requires a non-empty "
            "stable_source_content_key: the decision identity must stay "
            "attached to stable source lineage (run/snapshot/revision "
            "remain excluded)")
    event_date = _day_date(event_anchor_date)
    missing_key_dates = not event_date or not site_adoption_start.strip()

    # Site adoption interval (day precision required for a determinate
    # adoption check; partial adoption dates stay boundary).
    adoption_lo = _day_date(site_adoption_start)
    adoption_hi = _day_date(site_adoption_end)
    adoption_partial = (
        (bool(site_adoption_start.strip())
         and _date_precision(site_adoption_start) != PRECISION_DAY)
        or (bool(site_adoption_end.strip())
            and _date_precision(site_adoption_end) != PRECISION_DAY)
    )
    adoption_boundary = (
        adoption_partial
        or (event_date is not None and adoption_lo is not None
            and event_date == adoption_lo
            and adoption_start_inclusive is None)
        or (event_date is not None and adoption_hi is not None
            and event_date == adoption_hi
            and adoption_end_inclusive is None)
    )

    def site_covers(day: datetime.date) -> bool:
        if adoption_lo is not None:
            if adoption_start_inclusive is False:
                if day <= adoption_lo:
                    return False
            elif day < adoption_lo:
                return False
        if adoption_hi is not None:
            if adoption_end_inclusive is False:
                if day >= adoption_hi:
                    return False
            elif day > adoption_hi:
                return False
        return True

    def _version_fingerprint(version: ProtocolVersionRecord) -> str:
        return feasible_version_fingerprint(
            protocol_id=version.protocol_id,
            protocol_version=version.protocol_version,
            amendment_id_or_hash=version.amendment_id_or_hash,
            approval_date=version.approval_date,
            effective_start=version.effective_start,
            effective_end=version.effective_end,
            transition_scope=version.transition_scope,
            new_enrollment_only=version.new_enrollment_only,
            re_consent_required=version.re_consent_required,
            rule_content_hash=version.rule_content_hash,
            extraction_hash=version.extraction_hash,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability)

    base_feasible: List[ProtocolVersionRecord] = []
    for version in versions:
        if not version.approval_date.strip():
            continue  # unapproved version is not feasible
        v_lo = _day_date(version.effective_start)
        v_hi = (_day_date(version.effective_end)
                if version.effective_end.strip() else None)
        if v_lo is None:
            continue
        if event_date is not None and not _version_covers_event(
                version, event_date, v_lo, v_hi):
            continue
        if event_date is not None and not site_covers(event_date):
            continue
        # Version-level site adoption (challenge 11: the latest amendment
        # may not yet be enabled at the centre).  When a version declares
        # its own adoption interval it must additionally cover the event;
        # otherwise the shared site adoption interval already governs.
        if version.site_adoption_start.strip():
            v_lo = _day_date(version.site_adoption_start)
            v_hi = (_day_date(version.site_adoption_end)
                    if version.site_adoption_end.strip() else None)
            if v_lo is None or event_date is None or event_date < v_lo:
                continue
            if v_hi is not None and event_date > v_hi:
                continue
        base_feasible.append(version)

    # Base feasible-version fingerprints (event/site coverage only) are
    # preserved in every gate's lineage/context; the §2.3 transition
    # assessment below may then restrict or reject them.
    base_fps = _canonical_sorted(
        [_version_fingerprint(v) for v in base_feasible])

    # ------------------------------------------------------------------
    # §2.3 transition-scope assessment (fail closed, BEFORE the
    # feasible-count shortcut): a subject is never pushed onto a newer
    # version merely because its effective/site interval covers the
    # event.  Missing/conflicting transition inputs yield one
    # not_evaluable/boundary applicability gate and no candidate,
    # risk or Query downstream (corrective 03).
    # ------------------------------------------------------------------
    feasible: List[ProtocolVersionRecord] = base_feasible
    gate_status: Optional[str] = None
    gate_rationale = ""
    gate_scope = ""
    gate_fps: Tuple[str, ...] = base_fps
    gate_new_enrollment_only: Optional[bool] = None
    gate_re_consent: Optional[bool] = None
    chosen_old: Optional[ProtocolVersionRecord] = None

    def re_consent_dependent(version: ProtocolVersionRecord) -> bool:
        return (version.re_consent_required is True
                or version.transition_scope
                == TRANSITION_NEXT_VISIT_OR_RECONSENT)

    reconsent = [v for v in base_feasible if re_consent_dependent(v)]
    if reconsent:
        # The schema does not distinguish original consent from
        # re-consent and carries no versioned next-visit/re-consent
        # trigger policy: subject_consent_date is never reinterpreted as
        # re-consent and no earliest/AND/OR semantics are invented.
        gate_status = APPLICABILITY_NOT_EVALUABLE
        gate_rationale = (
            "修订依赖重新知情/下次访视触发切换，当前输入无法区分原始知情"
            "与重新知情且缺少版本化触发策略，适用性无法评价")
        gate_scope = reconsent[0].transition_scope
        gate_re_consent = True
    else:
        undetermined = [
            v for v in base_feasible
            if v.transition_scope == TRANSITION_UNDETERMINED]
        if undetermined:
            gate_status = APPLICABILITY_NOT_EVALUABLE
            gate_rationale = (
                "修订过渡范围未声明，无法确定新旧版本的适用规则，"
                "适用性无法评价")
            gate_scope = undetermined[0].transition_scope
        else:
            new_only = [
                v for v in base_feasible
                if v.new_enrollment_only is True
                or v.transition_scope == TRANSITION_NEW_ENROLLMENT_ONLY]
            if new_only:
                enroll_day = _day_date(subject_enrollment_date)
                if enroll_day is None:
                    # A day-comparable enrollment date is mandatory for a
                    # new-enrollment-only amendment; missing input is
                    # never silently admitted as a unique version.
                    gate_status = APPLICABILITY_NOT_EVALUABLE
                    gate_rationale = (
                        "仅新入组适用的修订缺少可比较的入组日期，"
                        "适用性无法评价")
                    gate_scope = new_only[0].transition_scope
                    gate_new_enrollment_only = True
                else:
                    # Grandfathering: a subject enrolled before the
                    # amendment start excludes it; post-start enrollment
                    # may admit it.
                    feasible = [
                        v for v in base_feasible
                        if not (
                            (v.new_enrollment_only is True
                             or v.transition_scope
                             == TRANSITION_NEW_ENROLLMENT_ONLY)
                            and _day_date(v.effective_start) is not None
                            and enroll_day < _day_date(v.effective_start))]
            if gate_status is None:
                existing_old = [
                    v for v in feasible
                    if v.transition_scope
                    == TRANSITION_EXISTING_CONTINUE_OLD]
                if existing_old:
                    gate_scope = existing_old[0].transition_scope
                    enroll_day = _day_date(subject_enrollment_date)
                    if enroll_day is None:
                        gate_status = APPLICABILITY_NOT_EVALUABLE
                        gate_rationale = (
                            "既有受试者延续旧版需要可比较的入组日期，"
                            "入组日期缺失，适用性无法评价")
                    else:
                        predecessors = [
                            v for v in versions
                            if v.transition_scope
                            != TRANSITION_EXISTING_CONTINUE_OLD]
                        supported = [
                            v for v in predecessors
                            if _version_supported_at_enrollment(
                                v, enroll_day, adoption_lo)]
                        if len(supported) == 1:
                            chosen_old = supported[0]
                        elif not supported:
                            gate_status = APPLICABILITY_NOT_EVALUABLE
                            gate_rationale = (
                                "既有受试者延续旧版，但入组时点有来源支持"
                                "的旧版本不足一个，适用性无法评价")
                        else:
                            gate_status = (
                                APPLICABILITY_MULTI_FEASIBLE_BOUNDARY)
                            gate_rationale = (
                                "多个既有版本在受试者入组时点均有来源"
                                "支持，适用性存在边界")
                            gate_fps = _canonical_sorted(
                                [_version_fingerprint(v)
                                 for v in supported])

    fps = _canonical_sorted(
        [_version_fingerprint(v) for v in feasible])

    if chosen_old is not None:
        # existing_continue_old: exactly one predecessor is supported at
        # the subject's enrollment time -- the old version continues even
        # after the amendment's project effective start.
        v = chosen_old
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=APPLICABILITY_UNIQUE_ACTIVE,
            protocol_id=v.protocol_id, protocol_version=v.protocol_version,
            amendment_id_or_hash=v.amendment_id_or_hash,
            ethics_or_authority_approval_date=v.approval_date,
            effective_start=v.effective_start,
            effective_end=v.effective_end,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=gate_scope,
            new_enrollment_only=v.new_enrollment_only,
            re_consent_requirement=v.re_consent_required,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=_canonical_sorted(
                [_version_fingerprint(v)]),
            stable_source_content_key=stable_source_content_key,
            rationale=(
                f"既有受试者按过渡条款延续旧版，唯一适用版本 "
                f"{v.protocol_version}"))

    if gate_status is not None:
        # One subject-level applicability gate: not_evaluable (missing /
        # insufficient transition evidence) or multi_feasible_boundary
        # (two supported predecessors).  Never a unique version, and no
        # candidate/risk/Query is generated downstream.
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=gate_status,
            protocol_id=versions[0].protocol_id,
            amendment_id_or_hash=versions[0].amendment_id_or_hash,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=gate_scope,
            new_enrollment_only=gate_new_enrollment_only,
            re_consent_requirement=gate_re_consent,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=gate_fps,
            stable_source_content_key=stable_source_content_key,
            rationale=gate_rationale)

    if missing_key_dates or adoption_boundary:
        status = (
            APPLICABILITY_NOT_EVALUABLE if missing_key_dates
            else APPLICABILITY_MULTI_FEASIBLE_BOUNDARY)
        rationale = (
            "批准/启用/事件关键日期缺失或冲突，无法确定适用版本"
            if missing_key_dates
            else "中心启用日期与事件时点端点未定义，适用性存在边界")
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=status,
            protocol_id=versions[0].protocol_id,
            amendment_id_or_hash=versions[0].amendment_id_or_hash,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=versions[0].transition_scope,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=fps,
            stable_source_content_key=stable_source_content_key,
            rationale=rationale)

    if len(feasible) == 1:
        v = feasible[0]
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=APPLICABILITY_UNIQUE_ACTIVE,
            protocol_id=v.protocol_id, protocol_version=v.protocol_version,
            amendment_id_or_hash=v.amendment_id_or_hash,
            ethics_or_authority_approval_date=v.approval_date,
            effective_start=v.effective_start,
            effective_end=v.effective_end,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=v.transition_scope,
            new_enrollment_only=v.new_enrollment_only,
            re_consent_requirement=v.re_consent_required,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=fps,
            stable_source_content_key=stable_source_content_key,
            rationale=f"唯一适用版本 {v.protocol_version}")

    if len(feasible) > 1:
        return ProtocolApplicabilityDecision(
            subject_ref=subject_ref, site_ref=site_ref,
            decision_time_anchor=event_anchor_kind,
            decision_time_anchor_date=event_anchor_date,
            decision_status=APPLICABILITY_MULTI_FEASIBLE_BOUNDARY,
            protocol_id=versions[0].protocol_id,
            amendment_id_or_hash=versions[0].amendment_id_or_hash,
            site_activation_or_adoption_start=site_adoption_start,
            site_activation_or_adoption_end=site_adoption_end,
            amendment_transition_scope=versions[0].transition_scope,
            cohort=cohort, phase=phase, arm=arm,
            treatment_role=treatment_role,
            control_point_applicability=control_point_applicability,
            event_time_rule_scope=event_time_rule_scope,
            source_locators=tuple(source_locators),
            feasible_version_fingerprints=fps,
            stable_source_content_key=stable_source_content_key,
            rationale=(
                f"{len(feasible)} 个可行方案版本均有来源支持，"
                f"无法唯一确定适用版本"))

    # Zero feasible versions with complete inputs is an inability to
    # identify an applicable version -- not a supported competing
    # interpretation: not_evaluable, one subject-level gate, zero
    # candidate/risk/Query (§2.3, §5).
    return ProtocolApplicabilityDecision(
        subject_ref=subject_ref, site_ref=site_ref,
        decision_time_anchor=event_anchor_kind,
        decision_time_anchor_date=event_anchor_date,
        decision_status=APPLICABILITY_NOT_EVALUABLE,
        protocol_id=versions[0].protocol_id,
        amendment_id_or_hash=versions[0].amendment_id_or_hash,
        site_activation_or_adoption_start=site_adoption_start,
        site_activation_or_adoption_end=site_adoption_end,
        amendment_transition_scope=versions[0].transition_scope,
        cohort=cohort, phase=phase, arm=arm,
        treatment_role=treatment_role,
        control_point_applicability=control_point_applicability,
        event_time_rule_scope=event_time_rule_scope,
        source_locators=tuple(source_locators),
        feasible_version_fingerprints=fps,
        stable_source_content_key=stable_source_content_key,
        rationale="无任何方案版本覆盖该事件时点，适用性无法确定")


# ---------------------------------------------------------------------------
# Routing (§3.2) -- closed owner decision table
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolControlRoutingRecord:
    """Versioned routing record for one control point/component.

    Routing precedes expected-set generation.  Producer-owned control
    points never enter the D04 medical expected-set; they only surface as
    typed producer references in the compliance overview.  When the owner
    cannot be uniquely determined, exactly one ``protocol_routing``
    not_evaluable gate is generated -- never one risk per competing
    domain (challenge 67).
    """

    control_point_id: str
    owner_domain: str
    owner_signal_type: str
    routing_rule_version: str
    routing_rule_hash: str
    producer_unit_id: str = ""
    routing_gap: str = ""
    component_id: str = ""
    source_locators: Tuple[SourceLocator, ...] = ()
    candidate_owners: Tuple[str, ...] = ()
    decision_rationale: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.control_point_id,
                           "ProtocolControlRoutingRecord.control_point_id")
        if self.owner_domain not in OWNER_DOMAINS:
            raise ProtocolSliceError(
                f"owner_domain={self.owner_domain!r} invalid")
        _validate_nonempty(self.owner_signal_type,
                           "ProtocolControlRoutingRecord.owner_signal_type")
        if self.owner_domain == OWNER_D04:
            raise ProtocolSliceError(
                "a routing record must not point a control point back to "
                "D04 itself; D04-native points are evaluated, not routed")
        has_producer = bool(self.producer_unit_id.strip())
        has_gap = bool(self.routing_gap.strip())
        if self.owner_domain == OWNER_UNRESOLVED:
            if not self.candidate_owners:
                raise ProtocolSliceError(
                    "owner_unresolved routing requires candidate_owners")
            if not has_gap or has_producer:
                raise ProtocolSliceError(
                    "owner_unresolved routing requires a routing_gap and "
                    "no producer_unit_id")
        else:
            if has_producer == has_gap:
                raise ProtocolSliceError(
                    "routed control point requires exactly one of "
                    "producer_unit_id or routing_gap (§11: every delegated "
                    "item must tie to an owner expected unit or a routing "
                    "gap, never both)")
        object.__setattr__(self, "source_locators",
                           tuple(self.source_locators))
        object.__setattr__(self, "candidate_owners",
                           _canonical_sorted(self.candidate_owners))


def route_control_point(
    control_point_type: str, claim_kind: str = CLAIM_OTHER,
) -> str:
    """Closed routing decision table (§3.2).

    CM/合并用药禁限用 claim -> D02; 研究药计划/实际暴露、剂量或给药
    动作 claim -> D03; 名义/实际访视、检查/评估/样本计划和时窗 claim ->
    D05; 知情/筛选/随机/入组时序、入排资格、非计划型前置动作及退出
    触发条件 claim -> D04; 多表关系本身 -> D08.
    """
    if control_point_type == CONTROL_PROHIBITED_OR_RESTRICTED_TREATMENT:
        return OWNER_D02
    if control_point_type == CONTROL_DOSE_OR_TREATMENT_MANAGEMENT:
        return OWNER_D03
    if control_point_type == CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT:
        if claim_kind == CLAIM_VISIT_WINDOW:
            return OWNER_D05
        return OWNER_D04
    if control_point_type in (
            CONTROL_INCLUSION, CONTROL_EXCLUSION,
            CONTROL_DISCONTINUATION_OR_WITHDRAWAL,
            CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT):
        return OWNER_D04
    if control_point_type == CONTROL_OTHER_PROTOCOL_REQUIREMENT:
        if claim_kind == CLAIM_CONCOMITANT_MEDICATION:
            return OWNER_D02
        if claim_kind == CLAIM_IP_DOSING_ACTION:
            return OWNER_D03
        if claim_kind == CLAIM_VISIT_WINDOW:
            return OWNER_D05
        if claim_kind == CLAIM_MULTI_TABLE_RELATION:
            return OWNER_D08
        return OWNER_D04
    raise ProtocolSliceError(
        f"cannot route unknown control point type {control_point_type!r}")


@dataclass(frozen=True)
class ProtocolDelegatedControlPoint:
    """One producer-owned control point excluded from the D04 expected-set
    (§11).  Each item must tie to an exact owner expected unit
    (``producer_unit_id``) or a ``routing_gap``."""

    control_point_id: str
    owner_domain: str
    owner_signal_type: str
    producer_unit_id: str = ""
    routing_gap: str = ""
    component_id: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.control_point_id,
                           "ProtocolDelegatedControlPoint.control_point_id")
        if self.owner_domain not in (
                OWNER_D02, OWNER_D03, OWNER_D05, OWNER_D08):
            raise ProtocolSliceError(
                f"delegated control point owner_domain="
                f"{self.owner_domain!r} must be a producer domain "
                f"(D02/D03/D05/D08), never D04/self or owner_unresolved")
        has_producer = bool(self.producer_unit_id.strip())
        has_gap = bool(self.routing_gap.strip())
        if has_producer == has_gap:
            raise ProtocolSliceError(
                "delegated control point requires exactly one of "
                "producer_unit_id or routing_gap")


# ---------------------------------------------------------------------------
# Evaluation window spec (temporal hash dimension)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvaluationWindowSpec:
    """Versioned evaluation window for one control point (§5)."""

    eval_anchor_kind: str = ANCHOR_OTHER
    window_start: str = ""
    window_end: str = ""
    precision: str = ""
    endpoint_inclusivity: str = ""

    def __post_init__(self) -> None:
        if self.eval_anchor_kind not in ANCHOR_KINDS:
            raise ProtocolSliceError(
                f"eval_anchor_kind={self.eval_anchor_kind!r} invalid")
        if self.precision not in ("", *PRECISIONS):
            raise ProtocolSliceError(
                f"precision={self.precision!r} invalid")
        if self.endpoint_inclusivity not in ("", *INCLUSIVITIES):
            raise ProtocolSliceError(
                f"endpoint_inclusivity={self.endpoint_inclusivity!r} invalid")


# ---------------------------------------------------------------------------
# Evidence requirements and bindings (§4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RuleEvidenceRequirement:
    """One per-control-point evidence requirement (§4.2)."""

    requirement_id: str
    control_point_id: str
    component_id: str
    required_evidence_roles: Tuple[str, ...]
    alternate_evidence_roles: Tuple[str, ...] = ()
    coverage_complete_required: bool = True
    retest_or_confirmation_policy: str = ""
    rule_lineage: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.requirement_id,
                           "RuleEvidenceRequirement.requirement_id")
        _validate_nonempty(self.control_point_id,
                           "RuleEvidenceRequirement.control_point_id")
        req = _freeze_tuple(self.required_evidence_roles,
                            "RuleEvidenceRequirement.required_evidence_roles")
        if not req:
            raise ProtocolSliceError(
                "RuleEvidenceRequirement requires required_evidence_roles")
        object.__setattr__(self, "required_evidence_roles", req)
        object.__setattr__(
            self, "alternate_evidence_roles",
            _freeze_tuple(self.alternate_evidence_roles,
                          "RuleEvidenceRequirement.alternate_evidence_roles"))
        if not isinstance(self.coverage_complete_required, bool):
            raise ProtocolSliceError(
                "RuleEvidenceRequirement.coverage_complete_required must be "
                "a literal bool")
        _validate_optional_str(
            self.rule_lineage, "RuleEvidenceRequirement.rule_lineage")


def build_rule_evidence_requirement(
    *,
    control_point_id: str,
    component_id: str,
    required_evidence_roles: Sequence[str],
    alternate_evidence_roles: Sequence[str] = (),
    coverage_complete_required: bool = True,
    retest_or_confirmation_policy: str = "",
    rule_lineage: str = D04_RULE_LINEAGE_DEFAULT,
) -> RuleEvidenceRequirement:
    """Deterministic public builder for one D04 evidence requirement (§4.2).

    The requirement id is content-addressed over the full semantic payload
    (control point/component identity, required/alternate roles,
    completeness requirement, retest/confirmation policy and rule
    lineage): identical accepted inputs replay to the identical id, and
    any semantic evidence-requirement change produces a new id.  Required
    identity fields and the literal-boolean completeness requirement fail
    closed -- no silent defaults, no inferred role list.
    """
    if not control_point_id.strip():
        raise ProtocolSliceError(
            "build_rule_evidence_requirement requires control_point_id")
    if not component_id.strip():
        raise ProtocolSliceError(
            "build_rule_evidence_requirement requires component_id")
    req_roles = _canonical_sorted(required_evidence_roles)
    if not req_roles:
        raise ProtocolSliceError(
            "RuleEvidenceRequirement requires required_evidence_roles")
    alt_roles = _canonical_sorted(alternate_evidence_roles)
    if not isinstance(coverage_complete_required, bool):
        raise ProtocolSliceError(
            "RuleEvidenceRequirement.coverage_complete_required must be a "
            "literal bool")
    lineage = rule_lineage if rule_lineage.strip() else D04_RULE_LINEAGE_DEFAULT
    requirement_id = "d04-req-" + content_hash({
        "control_point_id": control_point_id,
        "component_id": component_id,
        "required_evidence_roles": list(req_roles),
        "alternate_evidence_roles": list(alt_roles),
        "coverage_complete_required": coverage_complete_required,
        "retest_or_confirmation_policy": retest_or_confirmation_policy,
        "rule_lineage": lineage,
    })
    return RuleEvidenceRequirement(
        requirement_id=requirement_id,
        control_point_id=control_point_id,
        component_id=component_id,
        required_evidence_roles=req_roles,
        alternate_evidence_roles=alt_roles,
        coverage_complete_required=coverage_complete_required,
        retest_or_confirmation_policy=retest_or_confirmation_policy,
        rule_lineage=lineage)


def expand_rule_evidence_requirements(
    control_point: ProtocolControlPoint,
    components: Optional[Mapping[str, ProtocolComponent]] = None,
    rule_lineage: str = D04_RULE_LINEAGE_DEFAULT,
) -> Tuple[RuleEvidenceRequirement, ...]:
    """Generate exactly one RuleEvidenceRequirement per atomic root and per
    package component (§4.2/§5).

    The atomic root's synthesized component carries the control point id,
    so its single requirement uses ``component_id == control_point_id``.
    Package roots generate one requirement per official component in
    ``component_ids`` order.  The completeness requirement is always
    ``True``: §4.3/§6.1/§6.2 require the required roles' accepted-source
    coverage to be complete for any determinate verdict, and the frozen
    rule schema carries no per-rule completeness override.  Producer-owned
    /delegated control points and applicability/routing gates never
    fabricate D04 requirements here.
    """
    if not isinstance(control_point, ProtocolControlPoint):
        raise ProtocolSliceError(
            "expand_rule_evidence_requirements requires a "
            "ProtocolControlPoint")
    lineage = rule_lineage if rule_lineage.strip() else D04_RULE_LINEAGE_DEFAULT
    if control_point.evaluation_root_kind == NODE_ATOMIC:
        rule = control_point.structured_rule
        if rule is None:
            raise ProtocolSliceError(
                "atomic control point requires structured_rule for its "
                "evidence requirement")
        return (build_rule_evidence_requirement(
            control_point_id=control_point.control_point_id,
            component_id=control_point.control_point_id,
            required_evidence_roles=rule.required_evidence_roles,
            alternate_evidence_roles=rule.alternate_evidence_roles,
            coverage_complete_required=True,
            retest_or_confirmation_policy=rule.retest_or_confirmation_policy,
            rule_lineage=lineage),)
    component_map = components or {}
    reqs: List[RuleEvidenceRequirement] = []
    for cid in control_point.component_ids:
        comp = component_map.get(cid)
        if comp is None:
            raise ProtocolSliceError(
                f"package {control_point.control_point_id} references "
                f"unknown component {cid!r} for evidence requirement")
        if not isinstance(comp, ProtocolComponent):
            raise ProtocolSliceError(
                f"package component {cid!r} must be a ProtocolComponent, "
                f"got {type(comp).__name__}")
        rule = comp.structured_rule
        reqs.append(build_rule_evidence_requirement(
            control_point_id=control_point.control_point_id,
            component_id=cid,
            required_evidence_roles=rule.required_evidence_roles,
            alternate_evidence_roles=rule.alternate_evidence_roles,
            coverage_complete_required=True,
            retest_or_confirmation_policy=rule.retest_or_confirmation_policy,
            rule_lineage=lineage))
    return tuple(reqs)


CONFIRMATION_CONFIRMED = "confirmed"
CONFIRMATION_UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class RuleEvidenceBinding:
    """One identity/time-matched evidence binding (§4.2).

    The binding must carry subject/site, official rule id/component,
    source role, stable source event key, value/unit/date/precision,
    source locator, accepted revision, relationship confirmation status
    and applicability lineage.  A binding whose identity is unconfirmed or
    whose cross-domain relation is not exactly verified fails closed at
    evaluation time (challenges 35/36/63).
    """

    binding_id: str
    control_point_id: str
    component_id: str
    subject_ref: str
    site_ref: str
    source_role: str
    stable_source_event_key: str
    source_locator: SourceLocator
    value: str = ""
    unit: str = ""
    date_raw: str = ""
    relationship_confirmation: str = CONFIRMATION_CONFIRMED
    accepted_revision_id: str = ""
    applicability_lineage: str = ""
    rule_lineage: str = ""
    cross_domain_ref: Optional[CrossDomainEvidenceRef] = None
    expected_producer_unit_id: str = ""
    producer_dependency_blocked: bool = False
    producer_dependency_reason: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.binding_id, "RuleEvidenceBinding.binding_id")
        _validate_nonempty(self.control_point_id,
                           "RuleEvidenceBinding.control_point_id")
        _validate_nonempty(self.component_id,
                           "RuleEvidenceBinding.component_id")
        _validate_nonempty(self.subject_ref,
                           "RuleEvidenceBinding.subject_ref")
        _validate_nonempty(self.site_ref, "RuleEvidenceBinding.site_ref")
        _validate_nonempty(self.source_role,
                           "RuleEvidenceBinding.source_role")
        _validate_nonempty(self.stable_source_event_key,
                           "RuleEvidenceBinding.stable_source_event_key")
        if not isinstance(self.source_locator, SourceLocator):
            raise ProtocolSliceError(
                "RuleEvidenceBinding.source_locator must be a SourceLocator")
        if self.relationship_confirmation not in (
                CONFIRMATION_CONFIRMED, CONFIRMATION_UNRESOLVED):
            raise ProtocolSliceError(
                f"relationship_confirmation="
                f"{self.relationship_confirmation!r} invalid")
        if (self.cross_domain_ref is not None
                and not isinstance(self.cross_domain_ref,
                                   CrossDomainEvidenceRef)):
            raise ProtocolSliceError(
                "RuleEvidenceBinding.cross_domain_ref must be a "
                "CrossDomainEvidenceRef or None")

    @property
    def is_confirmed(self) -> bool:
        return self.relationship_confirmation == CONFIRMATION_CONFIRMED


@dataclass(frozen=True)
class UnitConversionRule:
    """Versioned unit conversion (factor-based, exact Decimal math)."""

    conversion_id: str
    from_unit: str
    to_unit: str
    factor: str
    content_hash_value: str

    def __post_init__(self) -> None:
        _validate_nonempty(self.conversion_id, "UnitConversionRule.conversion_id")
        if not self.from_unit.strip() or not self.to_unit.strip():
            raise ProtocolSliceError(
                "UnitConversionRule requires from_unit and to_unit")
        if self.from_unit == self.to_unit:
            raise ProtocolSliceError(
                "UnitConversionRule from_unit must differ from to_unit")
        if _parse_decimal(self.factor) is None:
            raise ProtocolSliceError(
                f"UnitConversionRule.factor={self.factor!r} is not numeric")
        if not self.content_hash_value.strip():
            raise ProtocolSliceError(
                "UnitConversionRule.content_hash_value is required")


@dataclass(frozen=True)
class RetestOutcome:
    """Versioned retest/confirmation outcome (§7.1).

    A retest may cover the initial result only when the rule's
    retest_or_confirmation_policy allows it and the retest falls inside
    the allowed retest window with the required count/authority.
    """

    has_retest: bool
    retest_value: str = ""
    retest_unit: str = ""
    retest_date_raw: str = ""
    retest_in_allowed_window: Optional[bool] = None
    retest_authority_ok: Optional[bool] = None
    retest_count_ok: Optional[bool] = None
    meets_criterion: Optional[bool] = None
    conflict_with_initial: bool = False
    rationale: str = ""


@dataclass(frozen=True)
class ProtocolExceptionBinding:
    """One exception/waiver/investigator-judgment record (§7.3).

    Only an active-protocol pre-allowed exception path, or a formal rule
    change already effective at the evaluated event time and bound to this
    subject/site/rule/component/window, may enter rule arithmetic as
    counterevidence.  "已批准豁免" wording, retrospective acknowledgements,
    unapproved records and wrong rule/subject/site/window bindings are
    context only and can never rewrite a non-conformance (challenge 26).
    """

    exception_id: str
    subject_ref: str
    site_ref: str
    control_point_id: str
    component_id: str
    window_start: str
    window_end: str
    exception_effect: str
    approved_or_confirmed: Optional[bool] = None
    effective_at_event_time: Optional[bool] = None
    decision_date_raw: str = ""
    source_locator: Optional[SourceLocator] = None
    rationale: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.exception_id,
                           "ProtocolExceptionBinding.exception_id")
        if self.exception_effect not in EXCEPTION_EFFECTS:
            raise ProtocolSliceError(
                f"exception_effect={self.exception_effect!r} invalid")
        if (self.source_locator is not None
                and not isinstance(self.source_locator, SourceLocator)):
            raise ProtocolSliceError(
                "ProtocolExceptionBinding.source_locator must be a "
                "SourceLocator or None")


# ---------------------------------------------------------------------------
# Priority policy (§8.1) -- versioned, content-addressed
# ---------------------------------------------------------------------------

def policy_content_hash_value(
    *,
    policy_id: str,
    version: str,
    rationale: str,
    subtype_priorities: Sequence[Tuple[str, str]] = (),
    subtype_critical: Sequence[Tuple[str, bool]] = (),
    subtype_machine_close_forbidden: Sequence[Tuple[str, bool]] = (),
) -> str:
    """Canonical content address of the policy semantic payload.

    Covers policy id, version, rationale and the three sorted subtype
    pair lists; the supplied ``policy_content_hash`` itself is excluded
    (it IS this value).  Duplicate subtypes are rejected upstream, so the
    sorted pair lists are unambiguous and order-independent.
    """
    return "d04-policy-" + content_hash({
        "policy_id": policy_id,
        "version": version,
        "rationale": rationale,
        "subtype_priorities": sorted(
            (s, pri) for s, pri in subtype_priorities),
        "subtype_critical": sorted(
            (s, bool(f)) for s, f in subtype_critical),
        "subtype_machine_close_forbidden": sorted(
            (s, bool(f)) for s, f in subtype_machine_close_forbidden),
    })


@dataclass(frozen=True)
class D04PriorityPolicy:
    """Versioned, content-addressed monitoring-priority policy (§8.1).

    Priorities come from this policy only -- never model-scored, never a
    fixed universal threshold.  ``unknown`` is never defaulted to low.
    The frozen boolean candidate keys ``rights_or_safety_critical`` and
    ``machine_close_forbidden`` are read through the public strict readers
    in ``contracts.py`` by the shared lifecycle adapter (§8.1, §10.4).

    Invariants enforced at construction:

    * nested pairs are deep-frozen tuples, flags are literal ``bool`` and
      duplicate subtype entries are rejected (mutable aliases fail
      closed);
    * ``policy_content_hash`` must equal the canonical content address
      :func:`policy_content_hash_value` of the semantic payload (tampered
      hashes fail closed);
    * frozen producer invariant: any subtype with
      ``rights_or_safety_critical=true`` must also carry
      ``machine_close_forbidden=true`` and an effective monitoring
      priority of ``high`` -- enforced here, not only by the shared
      lifecycle adapter's either-flag normalization (§10.4).
    """

    policy_id: str
    version: str
    policy_content_hash: str
    rationale: str
    subtype_priorities: Tuple[Tuple[str, str], ...] = ()
    subtype_critical: Tuple[Tuple[str, bool], ...] = ()
    subtype_machine_close_forbidden: Tuple[Tuple[str, bool], ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.policy_id, "D04PriorityPolicy.policy_id")
        _validate_nonempty(self.version, "D04PriorityPolicy.version")
        _validate_nonempty(self.policy_content_hash,
                           "D04PriorityPolicy.policy_content_hash")
        if not self.rationale.strip():
            raise ProtocolSliceError(
                "D04PriorityPolicy.rationale is required")
        priorities = self._freeze_pairs(
            self.subtype_priorities, "subtype_priorities",
            flag_kind=False)
        critical = self._freeze_pairs(
            self.subtype_critical, "subtype_critical", flag_kind=True)
        forbidden = self._freeze_pairs(
            self.subtype_machine_close_forbidden,
            "subtype_machine_close_forbidden", flag_kind=True)
        object.__setattr__(self, "subtype_priorities", priorities)
        object.__setattr__(self, "subtype_critical", critical)
        object.__setattr__(self, "subtype_machine_close_forbidden", forbidden)
        # Frozen producer invariant (§10.4) -- fail closed at construction.
        for subtype, flag in critical:
            if not flag:
                continue
            if not self.machine_close_forbidden_for_subtype(subtype):
                raise ProtocolSliceError(
                    f"subtype {subtype!r} rights_or_safety_critical=true "
                    f"requires machine_close_forbidden=true")
            if self.priority_for_subtype(subtype) != MONITORING_PRIORITY_HIGH:
                raise ProtocolSliceError(
                    f"subtype {subtype!r} rights_or_safety_critical=true "
                    f"requires effective monitoring priority high")
        computed = policy_content_hash_value(
            policy_id=self.policy_id, version=self.version,
            rationale=self.rationale,
            subtype_priorities=priorities,
            subtype_critical=critical,
            subtype_machine_close_forbidden=forbidden)
        if self.policy_content_hash != computed:
            raise ProtocolSliceError(
                f"D04PriorityPolicy.policy_content_hash "
                f"{self.policy_content_hash!r} is not the canonical content "
                f"address {computed!r} of the policy semantic payload")

    def _freeze_pairs(
        self, value: Sequence[Any], field_name: str, *, flag_kind: bool,
    ) -> Tuple[Tuple[str, Any], ...]:
        """Deep-freeze one nested pair list; flags must be literal bools;
        duplicate subtypes are rejected."""
        result: List[Tuple[str, Any]] = []
        seen: Set[str] = set()
        for entry in value:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise ProtocolSliceError(
                    f"D04PriorityPolicy.{field_name} entries must be "
                    f"2-tuples, got {type(entry).__name__}")
            subtype, second = entry
            if not isinstance(subtype, str) or not subtype.strip():
                raise ProtocolSliceError(
                    f"D04PriorityPolicy.{field_name} subtype must be a "
                    f"non-empty string")
            if subtype not in POSITIVE_SUBTYPES:
                raise ProtocolSliceError(
                    f"unknown subtype {subtype!r} in {field_name}")
            if subtype in seen:
                raise ProtocolSliceError(
                    f"duplicate subtype {subtype!r} in "
                    f"D04PriorityPolicy.{field_name}")
            seen.add(subtype)
            if flag_kind:
                if type(second) is not bool:
                    raise ProtocolSliceError(
                        f"D04PriorityPolicy.{field_name} flag for "
                        f"{subtype!r} must be a literal bool, got "
                        f"{type(second).__name__}")
            else:
                if second not in VALID_MONITORING_PRIORITIES:
                    raise ProtocolSliceError(
                        f"priority {second!r} invalid in "
                        f"D04PriorityPolicy.{field_name}")
            result.append((subtype, second))
        return tuple(result)

    def priority_for_subtype(self, subtype: str) -> str:
        for s, priority in self.subtype_priorities:
            if s == subtype:
                return priority
        return MONITORING_PRIORITY_UNKNOWN

    def critical_for_subtype(self, subtype: str) -> bool:
        for s, flag in self.subtype_critical:
            if s == subtype:
                return bool(flag)
        return False

    def machine_close_forbidden_for_subtype(self, subtype: str) -> bool:
        for s, flag in self.subtype_machine_close_forbidden:
            if s == subtype:
                return bool(flag)
        return False


# ---------------------------------------------------------------------------
# Enrollment context (§8.3) -- Query wording gate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EnrollmentContext:
    """Frozen query context decided by locatable screening/randomization/
    enrollment/first-dose/disposition records (§8.3)."""

    subject_ref: str
    query_context: str
    rationale: str
    source_locator_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "EnrollmentContext.subject_ref")
        if self.query_context not in QUERY_CONTEXTS:
            raise ProtocolSliceError(
                f"query_context={self.query_context!r} invalid")
        if not self.rationale.strip():
            raise ProtocolSliceError("EnrollmentContext.rationale is required")
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))


def resolve_enrollment_context(
    *,
    subject_ref: str,
    randomized_or_enrolled: Optional[bool],
    received_study_intervention: Optional[bool],
    disposition_recorded: Optional[bool] = None,
    coverage_complete: bool = False,
    source_locator_ids: Sequence[str] = (),
) -> EnrollmentContext:
    """Decide the enrollment query context (§8.3).

    ``enrolled_or_post_enrollment`` when randomization/enrollment/study
    intervention/disposition is determinately recorded; ``enrollment_
    not_occurred`` when determinately not randomized/enrolled and no study
    intervention (with complete coverage); otherwise ``enrollment_state_
    unresolved`` -- never guessed from the current page or model.
    """
    enrolled = (
        coverage_complete
        and (randomized_or_enrolled is True
             or received_study_intervention is True
             or disposition_recorded is True))
    if enrolled:
        return EnrollmentContext(
            subject_ref=subject_ref,
            query_context=QUERY_CONTEXT_ENROLLED,
            rationale="已记录随机/入组、接受研究干预或处置记录",
            source_locator_ids=tuple(source_locator_ids))
    not_occurred = (
        coverage_complete
        and randomized_or_enrolled is False
        and received_study_intervention is False
        and disposition_recorded is not True)
    if not_occurred:
        return EnrollmentContext(
            subject_ref=subject_ref,
            query_context=QUERY_CONTEXT_NOT_OCCURRED,
            rationale="确定尚未随机/入组且未接受研究干预",
            source_locator_ids=tuple(source_locator_ids))
    return EnrollmentContext(
        subject_ref=subject_ref,
        query_context=QUERY_CONTEXT_UNRESOLVED,
        rationale="随机/入组/首次给药状态或时序无法确定，资料不足",
        source_locator_ids=tuple(source_locator_ids))


# ---------------------------------------------------------------------------
# Regulatory guidance metadata (challenge 15) -- data-driven, no hardcode
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegulatoryGuidanceVersion:
    """One externally effective regulatory guidance version (§2.1)."""

    version_id: str
    effective_start: str
    effective_end: str = ""
    content_reference: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.version_id,
                           "RegulatoryGuidanceVersion.version_id")
        _validate_nonempty(self.effective_start,
                           "RegulatoryGuidanceVersion.effective_start")


def resolve_regulatory_guidance(
    *,
    evaluation_time: str,
    guidance_records: Sequence[RegulatoryGuidanceVersion],
) -> Tuple[Optional[RegulatoryGuidanceVersion], str]:
    """Select the regulatory guidance effective at the Run evaluation time
    (§2.1).  The kernel holds no hardcoded regulatory calendar; the
    2026-09-01 China GCP boundary is supplied by the caller as data, so a
    re-interpretation of past results requires a new Run, never a rewrite.
    """
    day = _day_date(evaluation_time)
    if day is None:
        return None, "评价时点日期缺失或精度不足，无法选择适用规范版本"
    candidates: List[RegulatoryGuidanceVersion] = []
    for rec in guidance_records:
        lo = _day_date(rec.effective_start)
        hi = _day_date(rec.effective_end) if rec.effective_end.strip() else None
        if lo is None:
            continue
        if lo > day:
            continue
        if hi is not None and day > hi:
            continue
        candidates.append(rec)
    if len(candidates) == 1:
        return candidates[0], ""
    if not candidates:
        return None, "评价时点不在任何已登记规范版本有效期内"
    return None, "多个规范版本同时有效或边界重叠，无法唯一确定"


# ---------------------------------------------------------------------------
# Coverage-gap notice (§6.4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolCoverageGapNotice:
    """资料不足提示: bound to unit, reason, protocol locators and
    reachable source locators.  ``notice_id`` is a canonical content hash
    over unit + reason + sorted missing roles + sorted locators -- it never
    contains runtime free text, so reruns are deterministic (challenge 48).
    """

    notice_id: str
    unit_id: str
    reason_code: str
    missing_evidence_roles: Tuple[str, ...] = ()
    protocol_locator_ids: Tuple[str, ...] = ()
    reachable_source_locator_ids: Tuple[str, ...] = ()
    audience_text: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.unit_id, "ProtocolCoverageGapNotice.unit_id")
        if self.reason_code not in GAP_REASON_CODES:
            raise ProtocolSliceError(
                f"reason_code={self.reason_code!r} invalid")
        missing = _canonical_sorted(self.missing_evidence_roles)
        protocol_loc = _canonical_sorted(self.protocol_locator_ids)
        reachable = _canonical_sorted(self.reachable_source_locator_ids)
        object.__setattr__(self, "missing_evidence_roles", missing)
        object.__setattr__(self, "protocol_locator_ids", protocol_loc)
        object.__setattr__(self, "reachable_source_locator_ids", reachable)
        computed = "d04-gap-" + content_hash({
            "unit_id": self.unit_id,
            "reason_code": self.reason_code,
            "missing_evidence_roles": list(missing),
            "protocol_locator_ids": list(protocol_loc),
            "reachable_source_locator_ids": list(reachable),
        })
        if self.notice_id and self.notice_id != computed:
            raise ProtocolSliceError(
                f"ProtocolCoverageGapNotice.notice_id {self.notice_id!r} "
                f"does not match the canonical hash {computed!r}")
        object.__setattr__(self, "notice_id", computed)


def _gap_notice(
    *, unit_id: str, reason_code: str,
    missing_evidence_roles: Sequence[str] = (),
    protocol_locator_ids: Sequence[str] = (),
    reachable_source_locator_ids: Sequence[str] = (),
    audience_text: str = "",
) -> ProtocolCoverageGapNotice:
    return ProtocolCoverageGapNotice(
        notice_id="", unit_id=unit_id, reason_code=reason_code,
        missing_evidence_roles=tuple(missing_evidence_roles),
        protocol_locator_ids=tuple(protocol_locator_ids),
        reachable_source_locator_ids=tuple(reachable_source_locator_ids),
        audience_text=audience_text or _GAP_LABELS.get(
            reason_code, "资料不足，暂无法核实"))


# ---------------------------------------------------------------------------
# Journey / marker / typed producer value objects (§7.4, §9)
# ---------------------------------------------------------------------------
#
# These fixed schemas are renderer-neutral payloads.  The journey
# *projection* functions live in ``protocol_projection.py`` (worker_03);
# this module owns the value objects only.

@dataclass(frozen=True)
class ProtocolJourneyEvent:
    """One protocol-compliance journey event (§9 minimal fields)."""

    event_id: str
    domain_track: str
    subject_ref: str
    site_ref: str
    anchor_kind: str
    start: str = ""
    end: str = ""
    date_precision: str = ""
    nominal_visit: str = ""
    actual_visit: str = ""
    phase: str = ""
    protocol_version: str = ""
    control_point_id: str = ""
    evaluation_node_id: str = ""
    decisive_component_ids: Tuple[str, ...] = ()
    display_label: str = ""
    source_locator_ids: Tuple[str, ...] = ()
    unit_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.event_id, "ProtocolJourneyEvent.event_id")
        _validate_nonempty(self.domain_track,
                           "ProtocolJourneyEvent.domain_track")
        _validate_nonempty(self.subject_ref,
                           "ProtocolJourneyEvent.subject_ref")
        if self.anchor_kind not in ANCHOR_KINDS:
            raise ProtocolSliceError(
                f"ProtocolJourneyEvent.anchor_kind={self.anchor_kind!r} "
                f"invalid")
        object.__setattr__(self, "decisive_component_ids",
                           _canonical_sorted(self.decisive_component_ids))
        object.__setattr__(self, "source_locator_ids",
                           _canonical_sorted(self.source_locator_ids))
        object.__setattr__(self, "unit_ids",
                           _canonical_sorted(self.unit_ids))


@dataclass(frozen=True)
class ProtocolRiskMarker:
    """One protocol-compliance risk marker (§9 minimal fields)."""

    marker_id: str
    risk_family: str
    audience_label: str
    monitoring_priority: str
    anchor_kind: str
    anchor_start: str = ""
    anchor_end: str = ""
    date_precision: str = ""
    unit_id: str = ""
    candidate_or_risk_id: str = ""
    protocol_locator_ids: Tuple[str, ...] = ()
    supporting_locator_ids: Tuple[str, ...] = ()
    counterevidence_locator_ids: Tuple[str, ...] = ()
    query_ids: Tuple[str, ...] = ()
    coverage_gap: bool = False

    def __post_init__(self) -> None:
        _validate_nonempty(self.marker_id, "ProtocolRiskMarker.marker_id")
        if self.anchor_kind not in ANCHOR_KINDS:
            raise ProtocolSliceError(
                f"ProtocolRiskMarker.anchor_kind={self.anchor_kind!r} invalid")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise ProtocolSliceError(
                f"monitoring_priority={self.monitoring_priority!r} invalid")
        object.__setattr__(self, "protocol_locator_ids",
                           _canonical_sorted(self.protocol_locator_ids))
        object.__setattr__(self, "supporting_locator_ids",
                           _canonical_sorted(self.supporting_locator_ids))
        object.__setattr__(self, "counterevidence_locator_ids",
                           _canonical_sorted(self.counterevidence_locator_ids))
        object.__setattr__(self, "query_ids",
                           _canonical_sorted(self.query_ids))


@dataclass(frozen=True)
class ProtocolEventMarkerJoin:
    """Fixed event-marker join (§7.4).  Every id must be reachable and
    share subject/site/window; tamper fails before projection."""

    event_id: str
    marker_id: str
    unit_id: str
    risk_identity_id: str
    join_reason: str
    typed_ref_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonempty(self.event_id, "ProtocolEventMarkerJoin.event_id")
        _validate_nonempty(self.marker_id, "ProtocolEventMarkerJoin.marker_id")
        _validate_nonempty(self.unit_id, "ProtocolEventMarkerJoin.unit_id")
        if self.join_reason not in JOIN_REASONS:
            raise ProtocolSliceError(
                f"join_reason={self.join_reason!r} invalid")
        object.__setattr__(self, "typed_ref_ids",
                           _canonical_sorted(self.typed_ref_ids))


@dataclass(frozen=True)
class ProtocolProducerReference:
    """Typed producer join for the compliance overview (§7.4, §9).

    Carries the producer's own marker/Query/risk identity; D04 never
    copies a producer candidate/risk/Query or creates a second identity.
    """

    ref_id: str
    owner_domain: str
    producer_unit_id: str
    producer_marker_or_query_id: str = ""
    producer_risk_identity_id: str = ""
    audience_label: str = ""
    monitoring_priority: str = MONITORING_PRIORITY_UNKNOWN
    control_point_id: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.ref_id, "ProtocolProducerReference.ref_id")
        if self.owner_domain not in (
                OWNER_D02, OWNER_D03, OWNER_D05, OWNER_D08):
            raise ProtocolSliceError(
                f"ProtocolProducerReference.owner_domain="
                f"{self.owner_domain!r} must be a producer domain "
                f"(D02/D03/D05/D08), never D04/self or owner_unresolved")
        _validate_nonempty(self.producer_unit_id,
                           "ProtocolProducerReference.producer_unit_id")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise ProtocolSliceError(
                f"monitoring_priority={self.monitoring_priority!r} invalid")


# ---------------------------------------------------------------------------
# Expected-set expansion (§5): eight frozen hash dimensions
# ---------------------------------------------------------------------------

def build_protocol_unit(
    *,
    project_id: str,
    subject_ref: str,
    control_point_id: str,
    evaluation_node_id: str,
    signal_type: str,
    protocol_applicability_id: str,
    eval_anchor_kind: str,
    window_start: str,
    window_end: str,
    precision: str,
    endpoint_inclusivity: str,
    protocol_id: str,
    protocol_version: str,
    amendment_id_or_hash: str,
    rule_content_hash: str,
    extraction_hash: str,
    mapping_version: str,
    unit_term_policy_version: str,
    feasible_version_fingerprints: Sequence[str] = (),
) -> EvaluationUnit:
    """Build the D04 EvaluationUnit from the frozen eight dimensions (§5).

    All nested objects are canonical-JSON serialized into single strings
    before hashing; control-point ids containing ``|`` still produce
    distinct canonical unit ids (challenge 59).
    """
    if evaluation_node_id not in NODE_IDS:
        raise ProtocolSliceError(
            f"evaluation_node_id={evaluation_node_id!r} invalid")
    if signal_type not in SIGNAL_TYPES:
        raise ProtocolSliceError(f"signal_type={signal_type!r} invalid")
    if eval_anchor_kind not in ANCHOR_KINDS:
        raise ProtocolSliceError(
            f"eval_anchor_kind={eval_anchor_kind!r} invalid")
    norm = content_hash({
        "control_point_id": control_point_id,
        "evaluation_node_id": evaluation_node_id,
        "signal_type": signal_type,
    })
    window = content_hash({
        "protocol_applicability_id": protocol_applicability_id,
        "eval_anchor_kind": eval_anchor_kind,
        "window_start": window_start,
        "window_end": window_end,
        "precision": precision,
        "endpoint_inclusivity": endpoint_inclusivity,
    })
    lineage_payload: Dict[str, Any] = {
        "protocol_id": protocol_id,
        "protocol_version": protocol_version,
        "amendment_id_or_hash": amendment_id_or_hash,
        "rule_content_hash": rule_content_hash,
        "extraction_hash": extraction_hash,
        "mapping_version": mapping_version,
        "unit_term_policy_version": unit_term_policy_version,
    }
    fps = _canonical_sorted(feasible_version_fingerprints)
    if fps:
        lineage_payload["feasible_version_fingerprints"] = list(fps)
    lineage = content_hash(lineage_payload)
    return EvaluationUnit(
        project_id=project_id, domain_id=D04_DOMAIN,
        scope_type="subject", scope_key=subject_ref,
        normalized_concept_or_rule_item=norm,
        temporal_window=window,
        rule_or_knowledge_lineage=lineage,
        unit_algorithm_version=D04_UNIT_ALGO_VERSION)


def expected_set_hash(unit_ids: Sequence[str]) -> str:
    """D04 expected-set hash -- input-order independent (challenge 48/83).

    Duplicate unit ids are rejected, never silently deduplicated: each
    expected unit appears exactly once (§11)."""
    if isinstance(unit_ids, str):
        raise ProtocolSliceError(
            "expected_set_hash requires a sequence, not a string")
    seen: Set[str] = set()
    for uid in unit_ids:
        if not isinstance(uid, str) or not uid.strip():
            raise ProtocolSliceError(
                "expected-set unit ids must be non-empty strings")
        if uid in seen:
            raise ProtocolSliceError(
                f"duplicate unit_id {uid!r} in expected set "
                f"(§11: each unit id appears exactly once)")
        seen.add(uid)
    return "d04-eset-" + content_hash(sorted(seen))


@dataclass(frozen=True)
class ProtocolUnitExpanded:
    """One expanded expected EvaluationUnit seed for D04."""

    subject_ref: str
    site_ref: str
    applicability: ProtocolApplicabilityDecision
    evaluation_node_id: str
    signal_type: str
    plan: ProtocolRuleEvaluationPlan
    control_point: Optional[ProtocolControlPoint] = None
    issue_expression: Optional[IssueExpression] = None
    component_ids: Tuple[str, ...] = ()
    components: Optional[Mapping[str, ProtocolComponent]] = None
    evidence_requirements: Tuple[RuleEvidenceRequirement, ...] = ()
    route: Optional[ProtocolControlRoutingRecord] = None
    window: EvaluationWindowSpec = EvaluationWindowSpec()
    control_point_not_applicable: bool = False
    affected_control_point_ids: Tuple[str, ...] = ()
    candidate_owners: Tuple[str, ...] = ()
    not_evaluable_reason_hint: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.subject_ref, "ProtocolUnitExpanded.subject_ref")
        _validate_nonempty(self.site_ref, "ProtocolUnitExpanded.site_ref")
        if not isinstance(self.applicability, ProtocolApplicabilityDecision):
            raise ProtocolSliceError(
                "ProtocolUnitExpanded.applicability must be a "
                "ProtocolApplicabilityDecision")
        if self.evaluation_node_id not in NODE_IDS:
            raise ProtocolSliceError(
                f"evaluation_node_id={self.evaluation_node_id!r} invalid")
        if self.signal_type not in SIGNAL_TYPES:
            raise ProtocolSliceError(
                f"signal_type={self.signal_type!r} invalid")
        if not isinstance(self.plan, ProtocolRuleEvaluationPlan):
            raise ProtocolSliceError(
                "ProtocolUnitExpanded.plan must be a "
                "ProtocolRuleEvaluationPlan")
        object.__setattr__(self, "component_ids",
                           _freeze_tuple(self.component_ids,
                                         "ProtocolUnitExpanded.component_ids"))
        object.__setattr__(self, "affected_control_point_ids",
                           _canonical_sorted(self.affected_control_point_ids))
        object.__setattr__(self, "candidate_owners",
                           _canonical_sorted(self.candidate_owners))
        # Deep-freeze the component mapping: a read-only view over a
        # defensive copy.  Direct mutation and caller-alias mutation are
        # both impossible, so package evaluation stays deterministic.
        # Key/value identity is validated (key == component.component_id).
        if self.components is not None:
            frozen: Dict[str, ProtocolComponent] = dict(self.components)
            for key, comp in frozen.items():
                if not isinstance(key, str) or not key.strip():
                    raise ProtocolSliceError(
                        "component map keys must be non-empty strings")
                if not isinstance(comp, ProtocolComponent):
                    raise ProtocolSliceError(
                        "component map values must be ProtocolComponent "
                        "instances")
                if comp.component_id != key:
                    raise ProtocolSliceError(
                        f"component map key {key!r} must equal its "
                        f"component_id {comp.component_id!r}")
            object.__setattr__(self, "components",
                               MappingProxyType(frozen))
        reqs = tuple(self.evidence_requirements)
        for req in reqs:
            if not isinstance(req, RuleEvidenceRequirement):
                raise ProtocolSliceError(
                    "evidence_requirements must be RuleEvidenceRequirement "
                    "instances")
            cp_id = (self.control_point.control_point_id
                     if self.control_point is not None else "")
            if req.control_point_id != cp_id:
                raise ProtocolSliceError(
                    f"evidence requirement {req.requirement_id!r} is bound "
                    f"to control point {req.control_point_id!r}, expected "
                    f"{cp_id!r}")
        if self.evaluation_node_id in (NODE_ATOMIC, NODE_PACKAGE):
            if not reqs:
                raise ProtocolSliceError(
                    "atomic/package unit requires generated "
                    "evidence_requirements (never inferred at evaluation)")
            if self.evaluation_node_id == NODE_ATOMIC:
                if (len(reqs) != 1
                        or reqs[0].component_id
                        != self.control_point.control_point_id):
                    raise ProtocolSliceError(
                        "atomic unit requires exactly one evidence "
                        "requirement for the control point component")
            else:
                req_components = [r.component_id for r in reqs]
                if len(set(req_components)) != len(req_components):
                    raise ProtocolSliceError(
                        "package unit evidence requirements must be unique "
                        "per component")
                if set(req_components) != set(self.component_ids):
                    raise ProtocolSliceError(
                        "package unit evidence requirements must cover "
                        "exactly its component ids")
        else:
            if reqs:
                raise ProtocolSliceError(
                    "applicability/routing gate units must not fabricate "
                    "evidence requirements")
        object.__setattr__(self, "evidence_requirements", reqs)
        if self.evaluation_node_id in (NODE_ATOMIC, NODE_PACKAGE):
            if self.control_point is None:
                raise ProtocolSliceError(
                    "atomic/package unit requires control_point")
            if (self.evaluation_node_id == NODE_PACKAGE
                    and self.issue_expression is None):
                raise ProtocolSliceError(
                    "package unit requires issue_expression")
            if self.signal_type != self.control_point.signal_type():
                raise ProtocolSliceError(
                    "unit signal_type must match control point signal type")
        if self.evaluation_node_id == NODE_APPLICABILITY_GATE:
            if self.signal_type != SIGNAL_PROTOCOL_APPLICABILITY:
                raise ProtocolSliceError(
                    "applicability gate requires signal_type "
                    "protocol_applicability")
        if self.evaluation_node_id == NODE_ROUTING_GATE:
            if self.signal_type != SIGNAL_PROTOCOL_ROUTING:
                raise ProtocolSliceError(
                    "routing gate requires signal_type protocol_routing")

    def build_unit(self, project_id: str) -> EvaluationUnit:
        appl = self.applicability
        if self.evaluation_node_id == NODE_APPLICABILITY_GATE:
            cp_id = "protocol_applicability"
            protocol_version = "multi_feasible"
            amendment = "multi_feasible"
            if appl.decision_status == APPLICABILITY_NOT_EVALUABLE:
                protocol_version = "undetermined"
                amendment = "undetermined"
            return build_protocol_unit(
                project_id=project_id, subject_ref=self.subject_ref,
                control_point_id=cp_id,
                evaluation_node_id=NODE_APPLICABILITY_GATE,
                signal_type=SIGNAL_PROTOCOL_APPLICABILITY,
                protocol_applicability_id=appl.protocol_applicability_id,
                eval_anchor_kind=ANCHOR_OTHER,
                window_start="", window_end="",
                precision=PRECISION_UNKNOWN,
                endpoint_inclusivity=INCLUSIVITY_GATE,
                protocol_id=appl.protocol_id,
                protocol_version=protocol_version,
                amendment_id_or_hash=amendment,
                rule_content_hash="applicability_gate",
                extraction_hash="applicability_gate",
                mapping_version=self.plan.mapping_version,
                unit_term_policy_version=self.plan.unit_term_policy_version,
                feasible_version_fingerprints=appl.feasible_version_fingerprints)
        if self.evaluation_node_id == NODE_ROUTING_GATE:
            cp_id = (self.control_point.control_point_id
                     if self.control_point is not None
                     else "protocol_routing")
            return build_protocol_unit(
                project_id=project_id, subject_ref=self.subject_ref,
                control_point_id=cp_id,
                evaluation_node_id=NODE_ROUTING_GATE,
                signal_type=SIGNAL_PROTOCOL_ROUTING,
                protocol_applicability_id=appl.protocol_applicability_id,
                eval_anchor_kind=appl.decision_time_anchor,
                window_start="", window_end="",
                precision=appl.applicability_precision,
                endpoint_inclusivity=INCLUSIVITY_GATE,
                protocol_id=appl.protocol_id,
                protocol_version=(
                    appl.protocol_version or "routing_undetermined"),
                amendment_id_or_hash=(
                    appl.amendment_id_or_hash or "routing_undetermined"),
                rule_content_hash="routing_gate",
                extraction_hash="routing_gate",
                mapping_version=self.plan.mapping_version,
                unit_term_policy_version=self.plan.unit_term_policy_version)
        assert self.control_point is not None
        return build_protocol_unit(
            project_id=project_id, subject_ref=self.subject_ref,
            control_point_id=self.control_point.control_point_id,
            evaluation_node_id=self.evaluation_node_id,
            signal_type=self.signal_type,
            protocol_applicability_id=appl.protocol_applicability_id,
            eval_anchor_kind=self.window.eval_anchor_kind,
            window_start=self.window.window_start,
            window_end=self.window.window_end,
            precision=self.window.precision,
            endpoint_inclusivity=self.window.endpoint_inclusivity,
            protocol_id=appl.protocol_id,
            protocol_version=appl.protocol_version,
            amendment_id_or_hash=appl.amendment_id_or_hash,
            rule_content_hash=self.plan.rule_content_hash,
            extraction_hash=self.plan.extraction_hash,
            mapping_version=self.plan.mapping_version,
            unit_term_policy_version=self.plan.unit_term_policy_version)


@dataclass(frozen=True)
class ProtocolExpectedSetExpansion:
    """Expansion result: evaluation-root units + delegated routing list."""

    units: Tuple[ProtocolUnitExpanded, ...]
    project_id: str
    applicability: ProtocolApplicabilityDecision
    plan: ProtocolRuleEvaluationPlan
    delegated_control_points: Tuple[ProtocolDelegatedControlPoint, ...] = ()
    unit_ids: Tuple[str, ...] = ()
    expected_set_hash: str = ""

    def __post_init__(self) -> None:
        ids = tuple(u.build_unit(self.project_id).unit_id for u in self.units)
        object.__setattr__(self, "unit_ids", ids)
        object.__setattr__(self, "expected_set_hash", expected_set_hash(ids))

    @property
    def count(self) -> int:
        return len(self.units)


def _window_for_control_point(
    control_point: ProtocolControlPoint,
    applicability: ProtocolApplicabilityDecision,
    window_by_control_point: Optional[Mapping[str, EvaluationWindowSpec]],
) -> EvaluationWindowSpec:
    if window_by_control_point is not None:
        spec = window_by_control_point.get(control_point.control_point_id)
        if spec is not None:
            return spec
    rule = control_point.structured_rule
    if rule is not None and rule.evaluation_window_start.strip():
        return EvaluationWindowSpec(
            eval_anchor_kind=rule.temporal_anchor,
            window_start=rule.evaluation_window_start,
            window_end=rule.evaluation_window_end,
            precision=_date_precision(rule.evaluation_window_start),
            endpoint_inclusivity=_inclusivity_token(
                rule.window_start_inclusive, rule.window_end_inclusive))
    return EvaluationWindowSpec(
        eval_anchor_kind=applicability.decision_time_anchor,
        precision=applicability.applicability_precision)


def _inclusivity_token(
    start_inclusive: Optional[bool], end_inclusive: Optional[bool],
) -> str:
    if start_inclusive is None or end_inclusive is None:
        return INCLUSIVITY_UNSTATED
    if start_inclusive and end_inclusive:
        return INCLUSIVITY_INCLUSIVE
    if not start_inclusive and not end_inclusive:
        return INCLUSIVITY_EXCLUSIVE
    return INCLUSIVITY_MIXED


def expand_protocol_expected_set(
    *,
    project_id: str,
    applicability: ProtocolApplicabilityDecision,
    control_points: Sequence[ProtocolControlPoint],
    plan: ProtocolRuleEvaluationPlan,
    components: Optional[Mapping[str, ProtocolComponent]] = None,
    routing_records: Optional[Sequence[ProtocolControlRoutingRecord]] = None,
    window_by_control_point: Optional[Mapping[str, EvaluationWindowSpec]] = None,
) -> ProtocolExpectedSetExpansion:
    """Expand control points into the D04 expected unit set (§5).

    One EvaluationUnit per atomic/package root; producer-owned control
    points never enter the expected-set (they become delegated items);
    owner competition produces exactly one ``protocol_routing`` gate;
    a non-unique applicability decision produces exactly one subject-level
    ``protocol_applicability`` gate and no per-control-point medical units
    (challenges 60/67/71).
    """
    if not project_id.strip():
        raise ProtocolSliceError("project_id is required")
    if not isinstance(plan, ProtocolRuleEvaluationPlan):
        raise ProtocolSliceError("plan must be a ProtocolRuleEvaluationPlan")
    component_map: Dict[str, ProtocolComponent] = dict(components or {})
    routing_by_cp: Dict[str, ProtocolControlRoutingRecord] = {}
    for rec in routing_records or ():
        if rec.control_point_id in routing_by_cp:
            raise ProtocolSliceError(
                f"duplicate routing record for control point "
                f"{rec.control_point_id!r}: one owner decision per control "
                f"point (§3.2)")
        routing_by_cp[rec.control_point_id] = rec

    units: List[ProtocolUnitExpanded] = []
    delegated: List[ProtocolDelegatedControlPoint] = []

    for cp in control_points:
        if not isinstance(cp, ProtocolControlPoint):
            raise ProtocolSliceError(
                "control_points must be ProtocolControlPoint instances")
        if cp.control_point_id not in plan.root_ids:
            # A control point that is not an evaluation root is not an
            # expected unit (e.g. a display grouping node) -- §5: chapter
            # headings and display groups never masquerade as units.
            continue
        route = routing_by_cp.get(cp.control_point_id)
        if route is None:
            owner = route_control_point(cp.control_point_type)
            if owner == OWNER_D04:
                route = None
            else:
                route = ProtocolControlRoutingRecord(
                    control_point_id=cp.control_point_id,
                    owner_domain=owner,
                    owner_signal_type=owner,
                    routing_rule_version="routing-table-v1",
                    routing_rule_hash="routing-table-v1",
                    routing_gap="routing_by_control_point_type",
                    decision_rationale="closed routing decision table §3.2")
        if route is not None and route.owner_domain == OWNER_UNRESOLVED:
            units.append(ProtocolUnitExpanded(
                subject_ref=applicability.subject_ref,
                site_ref=applicability.site_ref,
                applicability=applicability,
                evaluation_node_id=NODE_ROUTING_GATE,
                signal_type=SIGNAL_PROTOCOL_ROUTING,
                plan=plan,
                control_point=cp,
                route=route,
                candidate_owners=route.candidate_owners,
                not_evaluable_reason_hint=route.routing_gap))
            continue
        if route is not None:
            delegated.append(ProtocolDelegatedControlPoint(
                control_point_id=cp.control_point_id,
                owner_domain=route.owner_domain,
                owner_signal_type=route.owner_signal_type,
                producer_unit_id=route.producer_unit_id,
                routing_gap=route.routing_gap,
                component_id=route.component_id))
            continue
        # D04-native root.
        if applicability.decision_status != APPLICABILITY_UNIQUE_ACTIVE:
            # Applicability gate covers all D04-native control points;
            # affected ids stay in the decision context only (§5, 71).
            continue
        if (cp.control_point_id
                in applicability.not_applicable_control_point_ids):
            not_applicable = True
        else:
            not_applicable = False
        window = _window_for_control_point(
            cp, applicability, window_by_control_point)
        if cp.evaluation_root_kind == NODE_ATOMIC:
            units.append(ProtocolUnitExpanded(
                subject_ref=applicability.subject_ref,
                site_ref=applicability.site_ref,
                applicability=applicability,
                evaluation_node_id=NODE_ATOMIC,
                signal_type=cp.signal_type(),
                plan=plan,
                control_point=cp,
                window=window,
                control_point_not_applicable=not_applicable,
                evidence_requirements=expand_rule_evidence_requirements(
                    cp, rule_lineage=plan.rule_content_hash)))
        else:
            ids: List[str] = []
            for cid in cp.component_ids:
                if cid not in component_map:
                    raise ProtocolSliceError(
                        f"package {cp.control_point_id} references unknown "
                        f"component {cid!r}")
                ids.append(cid)
            units.append(ProtocolUnitExpanded(
                subject_ref=applicability.subject_ref,
                site_ref=applicability.site_ref,
                applicability=applicability,
                evaluation_node_id=NODE_PACKAGE,
                signal_type=cp.signal_type(),
                plan=plan,
                control_point=cp,
                issue_expression=cp.issue_expression,
                component_ids=tuple(ids),
                components=component_map,
                window=window,
                control_point_not_applicable=not_applicable,
                evidence_requirements=expand_rule_evidence_requirements(
                    cp, components=component_map,
                    rule_lineage=plan.rule_content_hash)))

    if applicability.decision_status != APPLICABILITY_UNIQUE_ACTIVE:
        blocked_roots = sorted(
            cp.control_point_id for cp in control_points
            if cp.control_point_id in plan.root_ids)
        units.insert(0, ProtocolUnitExpanded(
            subject_ref=applicability.subject_ref,
            site_ref=applicability.site_ref,
            applicability=applicability,
            evaluation_node_id=NODE_APPLICABILITY_GATE,
            signal_type=SIGNAL_PROTOCOL_APPLICABILITY,
            plan=plan,
            affected_control_point_ids=tuple(blocked_roots),
            not_evaluable_reason_hint=applicability.rationale))

    return ProtocolExpectedSetExpansion(
        units=tuple(units), project_id=project_id,
        applicability=applicability, plan=plan,
        delegated_control_points=tuple(delegated))


# ---------------------------------------------------------------------------
# Cross-domain evidence gate (§7.4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrossDomainGateOutcome:
    """Outcome of the exact cross-domain verification gate (§7.4)."""

    verified: bool
    reason: str = ""
    relation_type: str = ""


def verify_cross_domain_ref(
    *,
    ref: CrossDomainEvidenceRef,
    subject_ref: str,
    site_ref: str,
    producer_unit_id: str,
    control_point_id: str,
    component_id: str,
    relation_type: str,
    rule_lineage: str,
) -> CrossDomainGateOutcome:
    """Exact cross-domain evidence gate (§7.4).

    Only subject + site + producer unit + stable source event
    key/content hash + rule/component + comparable window + closed
    relation type all exactly verified may support a positive/negative.
    Same record id on another subject, date-closeness alone, same row
    number alone and unconfirmed relations all fail closed
    (challenges 35/36/63).
    """
    if relation_type not in RELATION_TYPES:
        return CrossDomainGateOutcome(
            False, f"relation_type={relation_type!r} is not closed", "")
    if relation_type == RELATION_UNCONFIRMED:
        return CrossDomainGateOutcome(
            False, "跨域关系未确认，不能作为裁决依据",
            relation_type)
    if ref.consumer_domain != D04_DOMAIN:
        return CrossDomainGateOutcome(
            False,
            f"CrossDomainEvidenceRef consumer_domain must be {D04_DOMAIN}, "
            f"got {ref.consumer_domain!r}", relation_type)
    if not ref.verify_content_hash():
        return CrossDomainGateOutcome(
            False, "跨域引用内容哈希与稳定来源事件不一致",
            relation_type)
    if producer_unit_id and ref.producer_unit_id != producer_unit_id:
        return CrossDomainGateOutcome(
            False,
            f"producer_unit_id mismatch: ref {ref.producer_unit_id!r} != "
            f"expected {producer_unit_id!r}", relation_type)
    if not control_point_id.strip() or not component_id.strip():
        return CrossDomainGateOutcome(
            False, "rule/component 引用缺失，跨域关系无法确认",
            relation_type)
    ctx = dict(ref.context_payload)
    if ctx.get("subject_ref") != subject_ref:
        return CrossDomainGateOutcome(
            False,
            "跨域记录 subject 与受试者不匹配（仅 record id 相同不足）",
            relation_type)
    if ctx.get("site_ref") != site_ref:
        return CrossDomainGateOutcome(
            False,
            "跨域记录 site 与研究中心不匹配",
            relation_type)
    return CrossDomainGateOutcome(True, "", relation_type)


# ---------------------------------------------------------------------------
# Component condition evaluation (generic operator semantics)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ComponentConditionOutcome:
    """Verdict + evidence of one atomic condition evaluation."""

    verdict: str
    reason: str = ""
    gap_codes: Tuple[str, ...] = ()
    gaps: Tuple[str, ...] = ()
    supporting: Tuple[EvidenceItem, ...] = ()
    counterevidence: Tuple[EvidenceItem, ...] = ()
    context: Tuple[EvidenceItem, ...] = ()
    binding_ids: Tuple[str, ...] = ()


def _binding_evidence(
    *, unit_id: str, component_id: str, binding: RuleEvidenceBinding,
    polarity: str, rule_lineage: str, note: str,
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=f"ev-{unit_id}-{component_id}-{binding.binding_id}",
        polarity=polarity, locator=binding.source_locator,
        evidence_role=binding.source_role, rule_lineage=rule_lineage,
        uncertainty_note=note)


def _convert_value(
    value: Decimal, unit: str, target_unit: str,
    conversion_rules: Sequence[UnitConversionRule],
) -> Tuple[Optional[Decimal], bool, str]:
    """Versioned unit conversion; returns (value, ambiguous, reason)."""
    if unit == target_unit:
        return value, False, ""
    matches = [
        c for c in conversion_rules
        if c.from_unit == unit and c.to_unit == target_unit
    ]
    if not matches:
        return None, False, (
            f"单位 {unit!r} 与 {target_unit!r} 无版本化换算关系，无法比较")
    if len(matches) > 1:
        return None, True, (
            f"单位 {unit!r} 存在多个可行换算关系，无法唯一确定")
    factor = _parse_decimal(matches[0].factor)
    if factor is None:
        return None, False, "换算系数不可解析"
    return value * factor, False, ""


def _numeric_verdict(
    *, unit_id: str, component_id: str, comparison: RuleComparison,
    bindings: Sequence[RuleEvidenceBinding],
    conversion_rules: Sequence[UnitConversionRule],
    rule_lineage: str,
) -> ComponentConditionOutcome:
    """Generic numeric comparison with versioned conversion and rounding
    policy (§7.1, challenges 16-21)."""
    if not bindings:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="缺少数值证据",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("必需来源角色覆盖不完整",))
    # Identity/time gate: only confirmed bindings with comparable value.
    usable: List[RuleEvidenceBinding] = []
    for b in bindings:
        if not b.is_confirmed:
            return ComponentConditionOutcome(
                verdict=VERDICT_NOT_EVALUABLE,
                reason="证据身份或时间关系未确认，无法比较",
                gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
                gaps=("证据身份或时间关系未确认，无法比较",))
        usable.append(b)
    if len(usable) > 1:
        # 同日多个值只有版本化选择策略才可确定裁决 (§7.1); no policy here.
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="存在多个数值记录且无版本化选择策略，无法唯一确定",
            gap_codes=(GAP_RETEST_UNCONFIRMED,),
            gaps=("多值选择策略缺失，无法唯一确定",))
    b = usable[0]
    value = _parse_decimal(b.value)
    if value is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="关键数值缺失或不可解析",
            gap_codes=(GAP_VALUE_MISSING,),
            gaps=("关键数值缺失",))
    converted, ambiguous, reason = _convert_value(
        value, b.unit, comparison.canonical_unit, conversion_rules)
    if converted is None:
        return ComponentConditionOutcome(
            verdict=(VERDICT_BOUNDARY if ambiguous else VERDICT_NOT_EVALUABLE),
            reason=reason,
            gap_codes=(GAP_UNIT_UNCONVERTIBLE,),
            gaps=(reason,))
    value = converted
    if comparison.rounding_policy == ROUNDING_AFTER:
        value = _round_decimal(
            value, comparison.rounding_precision, comparison.rounding_mode)

    threshold = _parse_decimal(comparison.threshold)
    upper = (_parse_decimal(comparison.threshold_upper)
             if comparison.threshold_upper.strip() else None)
    if threshold is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="规则阈值不可解析", gap_codes=(GAP_VALUE_MISSING,),
            gaps=("规则阈值不可解析",))
    outcome = _compare_value(
        value=value, comparison=comparison.comparison,
        threshold=threshold, upper=upper,
        lower_inclusive=comparison.lower_inclusive,
        upper_inclusive=comparison.upper_inclusive)
    if outcome == "boundary":
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="数值恰在阈值且等号/端点包含关系未定义",
            gap_codes=(), gaps=())
    ev = _binding_evidence(
        unit_id=unit_id, component_id=component_id, binding=b,
        polarity=(L1bEvidencePolarity.SUPPORTING
                  if outcome == "met" else L1bEvidencePolarity.COUNTEREVIDENCE),
        rule_lineage=rule_lineage,
        note=f"记录值 {b.value} {b.unit}，比较结果 {'满足' if outcome == 'met' else '不满足'}规则")
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if outcome == "met" else VERDICT_UNMET),
        reason=f"数值比较{'满足' if outcome == 'met' else '不满足'}",
        supporting=(ev,) if outcome == "met" else (),
        counterevidence=() if outcome == "met" else (ev,),
        binding_ids=(b.binding_id,))


def _compare_value(
    *, value: Decimal, comparison: str, threshold: Decimal,
    upper: Optional[Decimal], lower_inclusive: Optional[bool],
    upper_inclusive: Optional[bool],
) -> str:
    """Returns met/unmet/boundary with explicit inclusivity semantics."""
    def endpoint_eq(v: Decimal, t: Decimal, inclusive: Optional[bool]) -> Optional[bool]:
        if v == t:
            if inclusive is None:
                return None
            return bool(inclusive)
        return None

    if comparison == "equals":
        return "met" if value == threshold else "unmet"
    if comparison == "not_equals":
        return "unmet" if value == threshold else "met"
    if comparison == "at_least":
        if value == threshold:
            if lower_inclusive is None:
                return "boundary"
            return "met" if lower_inclusive else "unmet"
        return "met" if value > threshold else "unmet"
    if comparison == "at_most":
        if value == threshold:
            if lower_inclusive is None:
                return "boundary"
            return "met" if lower_inclusive else "unmet"
        return "met" if value < threshold else "unmet"
    if comparison == "above":
        return "met" if value > threshold else "unmet"
    if comparison == "below":
        return "met" if value < threshold else "unmet"
    if comparison == "within_range":
        if upper is None:
            return "unmet"
        if value == threshold:
            if lower_inclusive is None:
                return "boundary"
            if not lower_inclusive:
                return "unmet"
        elif value < threshold:
            return "unmet"
        if value == upper:
            if upper_inclusive is None:
                return "boundary"
            if not upper_inclusive:
                return "unmet"
        elif value > upper:
            return "unmet"
        return "met"
    return "unmet"


def _window_contains_date(
    date_raw: str, window_start: str, window_end: str,
    start_inclusive: Optional[bool], end_inclusive: Optional[bool],
) -> Tuple[str, str]:
    """Determinate inside/outside/boundary for one date in a window."""
    day = _day_date(date_raw)
    if day is None:
        return "not_evaluable", "日期缺失或精度不足，无法确认窗口内"
    lo = _day_date(window_start) if window_start.strip() else None
    hi = _day_date(window_end) if window_end.strip() else None
    if lo is None and hi is None:
        return "inside", ""
    if lo is not None and day == lo and start_inclusive is None:
        return "boundary", "日期恰在窗口起点且端点包含关系未定义"
    if hi is not None and day == hi and end_inclusive is None:
        return "boundary", "日期恰在窗口终点且端点包含关系未定义"
    inside = True
    if lo is not None:
        inside = inside and (day >= lo if start_inclusive is True
                             else day > lo)
    if hi is not None:
        inside = inside and (day <= hi if end_inclusive is True
                             else day < hi)
    return ("inside" if inside else "outside"), ""


def _evaluate_existence(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding],
    coverage_complete_roles: Mapping[str, bool],
    rule_lineage: str,
) -> ComponentConditionOutcome:
    """exists/not_exists with the §4.3 zero-record proof requirements."""
    role = rule.exists_target_role
    target = [b for b in bindings if b.source_role == role]
    role_covered = coverage_complete_roles.get(role, False)
    if any(not b.is_confirmed for b in target):
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="记录关系未确认，不能作为存在性依据",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("记录关系未确认，不能作为存在性依据",))
    # Window filtering: a record outside the declared window is not the
    # target record; date missing cannot confirm inside-window status.
    in_window: List[RuleEvidenceBinding] = []
    if rule.evaluation_window_start.strip() or rule.evaluation_window_end.strip():
        for b in target:
            status, _reason = _window_contains_date(
                b.date_raw, rule.evaluation_window_start,
                rule.evaluation_window_end, rule.window_start_inclusive,
                rule.window_end_inclusive)
            if status == "inside":
                in_window.append(b)
            elif status == "boundary":
                return ComponentConditionOutcome(
                    verdict=VERDICT_BOUNDARY,
                    reason="记录日期与规则窗口端点关系未定义",
                    gap_codes=(), gaps=())
            elif status == "not_evaluable":
                return ComponentConditionOutcome(
                    verdict=VERDICT_NOT_EVALUABLE,
                    reason="记录日期缺失或精度不足，无法确认是否在窗口内",
                    gap_codes=(GAP_TEMPORAL_UNCOMPARABLE,),
                    gaps=("记录日期缺失或精度不足，无法确认是否在窗口内",))
    else:
        in_window = list(target)

    def build_ev(b: RuleEvidenceBinding, found: bool) -> Tuple[EvidenceItem, ...]:
        if not found:
            return ()
        note = ("命中目标记录" if rule.operator == OP_EXISTS
                else "不应存在的记录被发现")
        return (_binding_evidence(
            unit_id=unit_id, component_id=component_id, binding=b,
            polarity=L1bEvidencePolarity.SUPPORTING,
            rule_lineage=rule_lineage, note=note),)

    if rule.operator == OP_EXISTS:
        if in_window:
            evs = tuple(ev for b in in_window for ev in build_ev(b, True))
            return ComponentConditionOutcome(
                verdict=VERDICT_MET, reason="目标记录存在",
                supporting=evs,
                binding_ids=tuple(b.binding_id for b in in_window))
        if role_covered:
            return ComponentConditionOutcome(
                verdict=VERDICT_UNMET,
                reason="来源完整覆盖下未发现目标记录",
                gap_codes=(), gaps=())
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="未见记录但无法证明来源完整覆盖，不能推断未发生",
            gap_codes=(GAP_RECORD_MISSING_UNPROVEN,),
            gaps=("未见记录但无法证明来源完整覆盖，不能推断未发生",))
    # not_exists
    if in_window:
        evs = tuple(ev for b in in_window for ev in build_ev(b, True))
        return ComponentConditionOutcome(
            verdict=VERDICT_UNMET, reason="不应存在的记录被发现",
            counterevidence=evs,
            binding_ids=tuple(b.binding_id for b in in_window))
    if role_covered:
        return ComponentConditionOutcome(
            verdict=VERDICT_MET,
            reason="来源完整覆盖下未见任何目标记录",
            gap_codes=(), gaps=())
    return ComponentConditionOutcome(
        verdict=VERDICT_NOT_EVALUABLE,
        reason="未见记录但无法证明来源完整覆盖，不能推断未发生",
        gap_codes=(GAP_RECORD_MISSING_UNPROVEN,),
        gaps=("未见记录但无法证明来源完整覆盖，不能推断未发生",))


def _ordered_bindings_for_roles(
    *, component_id: str, bindings: Sequence[RuleEvidenceBinding],
    role_a: str, role_b: str,
) -> Tuple[Optional[RuleEvidenceBinding], Optional[RuleEvidenceBinding], str]:
    """Select the role-a/role-b bindings; wrong identity fails closed."""
    a = [b for b in bindings if b.source_role == role_a]
    b_list = [b for b in bindings if b.source_role == role_b]
    for b in a + b_list:
        if not b.is_confirmed:
            return None, None, "证据身份或时间关系未确认"
    if len(a) > 1 or len(b_list) > 1:
        return None, None, "同一锚点存在多个记录且无版本化选择策略"
    return (a[0] if a else None), (b_list[0] if b_list else None), ""


def _evaluate_temporal_order(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
) -> ComponentConditionOutcome:
    """OP_TEMPORAL_ORDER / OP_SEQUENCE -- anchors are never interchangeable
    (§7.2, challenge 39); partial dates compare on shared precision only."""
    a, b, reason = _ordered_bindings_for_roles(
        component_id=component_id, bindings=bindings,
        role_a=rule.anchor_role_a, role_b=rule.anchor_role_b)
    if reason:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE, reason=reason,
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=(reason,))
    if a is None or b is None:
        missing = [r for r in (rule.anchor_role_a, rule.anchor_role_b)
                   if (a is None and r == rule.anchor_role_a)
                   or (b is None and r == rule.anchor_role_b)]
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason=f"时序锚点 {missing} 记录缺失，无法比较",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("时序锚点记录缺失，无法比较",))
    ia = _date_interval(a.date_raw)
    ib = _date_interval(b.date_raw)
    if ia is None or ib is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="时序锚点日期缺失或无法解析",
            gap_codes=(GAP_TEMPORAL_UNCOMPARABLE,),
            gaps=("时序锚点日期缺失或无法解析，无法比较",))
    relation = _interval_relation(ia, ib)
    direction = rule.order_direction
    if direction == "before":
        met = relation == "before"
    elif direction == "after":
        met = relation == "after"
    elif direction == "not_after":
        met = relation in ("before", "equal_day")
    else:  # not_before
        met = relation in ("after", "equal_day")
    if relation == "possibly_overlap":
        # Partial dates that may or may not satisfy the order stay
        # boundary -- never silently padded (challenge 37).
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="部分日期在共享精度上可能命中也可能不命中时序关系",
            gap_codes=(), gaps=())
    evs = (
        _binding_evidence(
            unit_id=unit_id, component_id=component_id, binding=b,
            polarity=(L1bEvidencePolarity.SUPPORTING if met
                      else L1bEvidencePolarity.COUNTEREVIDENCE),
            rule_lineage=rule_lineage,
            note=f"{rule.anchor_role_a}={a.date_raw}, "
                 f"{rule.anchor_role_b}={b.date_raw}"),
    )
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"时序关系{'满足' if met else '不满足'}规则要求",
        supporting=evs if met else (),
        counterevidence=() if met else evs,
        binding_ids=(a.binding_id, b.binding_id))


def _evaluate_duration(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
) -> ComponentConditionOutcome:
    a, b, reason = _ordered_bindings_for_roles(
        component_id=component_id, bindings=bindings,
        role_a=rule.anchor_role_a, role_b=rule.anchor_role_b)
    if reason:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE, reason=reason,
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=(reason,))
    if a is None or b is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="持续时长所需日期记录缺失",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("持续时长所需日期记录缺失",))
    da = _day_date(a.date_raw)
    db = _day_date(b.date_raw)
    if da is None or db is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="部分日期无法计算精确持续时长，可能命中也可能不命中",
            gap_codes=(), gaps=())
    days = abs((db - da).days)
    threshold = _parse_decimal(rule.duration_min)
    if threshold is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="持续时长阈值不可解析",
            gap_codes=(GAP_VALUE_MISSING,), gaps=("持续时长阈值不可解析",))
    day_dec = Decimal(days)
    if day_dec == threshold and rule.duration_min_inclusive is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="持续时长恰在阈值且端点包含关系未定义",
            gap_codes=(), gaps=())
    met = (day_dec >= threshold
           if rule.duration_min_inclusive is not False
           else day_dec > threshold)
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"持续时长 {days} 天{'满足' if met else '不满足'}要求",
        gap_codes=(), gaps=())


def _evaluate_count(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding],
    coverage_complete_roles: Mapping[str, bool], rule_lineage: str,
    evidence_requirement: Optional[RuleEvidenceRequirement] = None,
) -> ComponentConditionOutcome:
    req = evidence_requirement
    required_roles = (req.required_evidence_roles if req is not None
                      else rule.required_evidence_roles)
    alternate_roles = (req.alternate_evidence_roles if req is not None
                       else rule.alternate_evidence_roles)
    targets = [b for b in bindings
               if b.source_role in required_roles
               or b.source_role in alternate_roles]
    if any(not b.is_confirmed for b in targets):
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="计数记录关系未确认",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("计数记录关系未确认",))
    if rule.evaluation_window_start.strip() or rule.evaluation_window_end.strip():
        filtered: List[RuleEvidenceBinding] = []
        for b in targets:
            status, _r = _window_contains_date(
                b.date_raw, rule.evaluation_window_start,
                rule.evaluation_window_end, rule.window_start_inclusive,
                rule.window_end_inclusive)
            if status == "inside":
                filtered.append(b)
            elif status == "boundary":
                return ComponentConditionOutcome(
                    verdict=VERDICT_BOUNDARY,
                    reason="计数记录日期与窗口端点关系未定义",
                    gap_codes=(), gaps=())
            elif status == "not_evaluable":
                return ComponentConditionOutcome(
                    verdict=VERDICT_NOT_EVALUABLE,
                    reason="计数记录日期缺失或精度不足",
                    gap_codes=(GAP_TEMPORAL_UNCOMPARABLE,),
                    gaps=("计数记录日期缺失或精度不足",))
        targets = filtered
    count = len(targets)
    threshold = rule.count_threshold
    cmp_ = rule.count_comparison
    met = (count >= threshold if cmp_ == "at_least"
           else count <= threshold if cmp_ == "at_most"
           else count == threshold)
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"计数 {count} {'满足' if met else '不满足'}阈值 {threshold}",
        gap_codes=(), gaps=())


def _evaluate_age(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
) -> ComponentConditionOutcome:
    """OP_AGE -- never defaults to 周岁/实足年龄 (challenge 80)."""
    if not rule.age_algorithm_id.strip():
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="年龄算法未冻结，绝不默认周岁/实足年龄算法",
            gap_codes=(GAP_AGE_ALGORITHM_UNFROZEN,),
            gaps=("年龄算法未冻结，无法计算年龄",))
    birth = [b for b in bindings if b.source_role == "demographics"]
    consent = [b for b in bindings if b.source_role == "consent"]
    if not birth or not consent:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="出生日期或知情日期缺失，无法计算年龄",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("出生日期或知情日期缺失，无法计算年龄",))
    birth_nv = normalize_partial_date(birth[0].value or birth[0].date_raw)
    consent_day = _day_date(consent[0].date_raw)
    if not birth_nv.normalized or consent_day is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="部分日期无法确定精确年龄，可能命中也可能不命中",
            gap_codes=(), gaps=())
    birth_parts = str(birth_nv.normalized).split("-")
    if len(birth_parts) < 1:
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="出生日期精度不足，无法确定年龄",
            gap_codes=(), gaps=())
    birth_year = int(birth_parts[0])
    age_years = consent_day.year - birth_year
    comparison = rule.comparison
    if comparison is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="年龄规则缺少比较语义",
            gap_codes=(GAP_EXPRESSION_INCOMPLETE,),
            gaps=("年龄规则缺少比较语义",))
    dec = Decimal(age_years)
    threshold = _parse_decimal(comparison.threshold)
    if threshold is None:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="年龄阈值不可解析",
            gap_codes=(GAP_VALUE_MISSING,), gaps=("年龄阈值不可解析",))
    if len(birth_parts) < 3 and dec == threshold:
        # Only birth year known and age sits on the threshold year: the
        # subject may or may not have crossed the birthday -> boundary.
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="仅知出生年份且年龄恰在阈值年度，可能命中也可能不命中",
            gap_codes=(), gaps=())
    met = _compare_value(
        value=dec, comparison=comparison.comparison, threshold=threshold,
        upper=(_parse_decimal(comparison.threshold_upper)
               if comparison.threshold_upper.strip() else None),
        lower_inclusive=comparison.lower_inclusive,
        upper_inclusive=comparison.upper_inclusive) == "met"
    if not met and _compare_value(
            value=dec, comparison=comparison.comparison, threshold=threshold,
            upper=(_parse_decimal(comparison.threshold_upper)
                   if comparison.threshold_upper.strip() else None),
            lower_inclusive=comparison.lower_inclusive,
            upper_inclusive=comparison.upper_inclusive) == "boundary":
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="年龄恰在阈值且端点包含关系未定义",
            gap_codes=(), gaps=())
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"年龄 {age_years} 岁{'满足' if met else '不满足'}规则",
        gap_codes=(), gaps=())


def _evaluate_discontinuation_trigger(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding],
    conversion_rules: Sequence[UnitConversionRule], rule_lineage: str,
    evidence_requirement: Optional[RuleEvidenceRequirement] = None,
) -> ComponentConditionOutcome:
    """OP_DISCONTINUATION_TRIGGER (§3.2/6.1 subtype 4).

    Trigger reached + disposition determinately inconsistent -> issue
    (verdict unmet); trigger not reached -> requirement satisfied
    (verdict met); disposition missing/unconfirmed -> not_evaluable.
    IP stop/pause dosing actions are D03-owned and never re-evaluated
    here (challenge 41/42).
    """
    req = evidence_requirement
    required_roles = (req.required_evidence_roles if req is not None
                      else rule.required_evidence_roles)
    trigger = rule.trigger_comparison
    trigger_bindings = [
        b for b in bindings
        if b.source_role in required_roles
        and b.source_role != "disposition"]
    trigger_outcome = _numeric_verdict(
        unit_id=unit_id, component_id=component_id,
        comparison=trigger, bindings=trigger_bindings,
        conversion_rules=conversion_rules, rule_lineage=rule_lineage)
    if trigger_outcome.verdict == VERDICT_UNMET:
        # Trigger not reached: no withdrawal issue.
        return ComponentConditionOutcome(
            verdict=VERDICT_MET,
            reason="退出/终止参与触发条件未达到",
            supporting=trigger_outcome.supporting,
            counterevidence=trigger_outcome.counterevidence,
            binding_ids=trigger_outcome.binding_ids)
    if trigger_outcome.verdict in (VERDICT_BOUNDARY,
                                   VERDICT_NOT_EVALUABLE):
        return trigger_outcome
    # Trigger reached: check disposition consistency.
    disposition = [b for b in bindings if b.source_role == "disposition"]
    if not disposition:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="已满足退出/终止参与触发条件，但受试者处置记录缺失",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("受试者处置记录缺失，无法判定是否一致",))
    disp = disposition[0]
    if not disp.is_confirmed:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="处置记录关系未确认，无法判定一致性",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("处置记录关系未确认",))
    expected = {v.strip() for v in rule.expected_disposition_values}
    actual = disp.value.strip()
    consistent = actual in expected
    if consistent and rule.disposition_window_days.strip():
        window_days = _parse_decimal(rule.disposition_window_days)
        trigger_date = next(
            (b.date_raw for b in trigger_bindings if b.date_raw.strip()), "")
        disp_day = _day_date(disp.date_raw)
        trig_day = _day_date(trigger_date)
        if disp_day is None or trig_day is None:
            return ComponentConditionOutcome(
                verdict=VERDICT_BOUNDARY,
                reason="处置或触发日期精度不足，无法确认处置时窗",
                gap_codes=(), gaps=())
        if (disp_day - trig_day).days > int(window_days):
            consistent = False
    ev = _binding_evidence(
        unit_id=unit_id, component_id=component_id, binding=disp,
        polarity=(L1bEvidencePolarity.SUPPORTING if consistent
                  else L1bEvidencePolarity.COUNTEREVIDENCE),
        rule_lineage=rule_lineage,
        note=f"处置记录 {actual}，{'一致' if consistent else '不一致'}")
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if consistent else VERDICT_UNMET),
        reason=("处置记录与触发标准一致" if consistent
                else "处置记录与触发标准确定不一致"),
        supporting=(ev,) if consistent else (),
        counterevidence=() if consistent else (ev,),
        binding_ids=(disp.binding_id,))


def _evaluate_investigator_judgment(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
) -> ComponentConditionOutcome:
    judgments = [b for b in bindings
                 if b.source_role == "investigator_judgment"]
    if not judgments:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="规则必需研究者判断，但判断记录缺失，不得由临床常识补写",
            gap_codes=(GAP_INVESTIGATOR_JUDGMENT_MISSING,),
            gaps=("研究者判断缺失",))
    j = judgments[0]
    if not j.is_confirmed:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="研究者判断记录未确认",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("研究者判断记录未确认",))
    note = j.value.strip()
    met = (note.lower() not in ("no", "否", "不适用", ""))
    ev = _binding_evidence(
        unit_id=unit_id, component_id=component_id, binding=j,
        polarity=(L1bEvidencePolarity.SUPPORTING if met
                  else L1bEvidencePolarity.COUNTEREVIDENCE),
        rule_lineage=rule_lineage, note="研究者判断记录")
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason="研究者判断已记录",
        supporting=(ev,) if met else (),
        counterevidence=() if met else (ev,),
        binding_ids=(j.binding_id,))


def _evaluate_equality_or_membership(
    *, unit_id: str, component_id: str, rule: ProtocolStructuredRule,
    bindings: Sequence[RuleEvidenceBinding], rule_lineage: str,
    evidence_requirement: Optional[RuleEvidenceRequirement] = None,
) -> ComponentConditionOutcome:
    req = evidence_requirement
    required_roles = (req.required_evidence_roles if req is not None
                      else rule.required_evidence_roles)
    alternate_roles = (req.alternate_evidence_roles if req is not None
                       else rule.alternate_evidence_roles)
    usable = [b for b in bindings
              if b.source_role in required_roles
              or b.source_role in alternate_roles]
    if not usable:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="缺少等值/集合证据",
            gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
            gaps=("必需来源角色覆盖不完整",))
    b = usable[0]
    if not b.is_confirmed:
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="证据关系未确认",
            gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
            gaps=("证据关系未确认",))
    actual = " ".join(b.value.strip().casefold().split())
    if rule.operator == OP_SET_MEMBERSHIP:
        allowed = {" ".join(v.strip().casefold().split())
                   for v in rule.value_set}
        met = actual in allowed
    else:  # equals / not_equals
        target = " ".join(rule.value_set[0].strip().casefold().split())
        met = actual == target
        if rule.operator == OP_NOT_EQUALS:
            met = not met
    ev = _binding_evidence(
        unit_id=unit_id, component_id=component_id, binding=b,
        polarity=(L1bEvidencePolarity.SUPPORTING if met
                  else L1bEvidencePolarity.COUNTEREVIDENCE),
        rule_lineage=rule_lineage,
        note=f"记录值 {b.value}，{'满足' if met else '不满足'}规则")
    return ComponentConditionOutcome(
        verdict=(VERDICT_MET if met else VERDICT_UNMET),
        reason=f"值比较{'满足' if met else '不满足'}",
        supporting=(ev,) if met else (),
        counterevidence=() if met else (ev,),
        binding_ids=(b.binding_id,))


def _qualifying_exception(
    *, component: ProtocolComponent, subject_ref: str, site_ref: str,
    exceptions: Sequence[ProtocolExceptionBinding],
) -> Tuple[bool, Optional[ProtocolExceptionBinding], Optional[str]]:
    """Classify exceptions per §7.3.

    Returns (qualifies, exception, gap_or_boundary).  A qualifying
    exception flips the component verdict to met with counterevidence.
    ``retrospective_explanation`` / ``urgent_hazard_justification`` are
    context only and never rewrite a non-conformance (challenges 25/26/28).
    """
    for exc in exceptions:
        if exc.control_point_id != component.control_point_id:
            continue
        if exc.component_id and exc.component_id != component.component_id:
            continue
        if exc.subject_ref != subject_ref or exc.site_ref != site_ref:
            continue
        if exc.exception_effect == EXCEPTION_RETROSPECTIVE:
            continue
        if exc.exception_effect == EXCEPTION_URGENT_HAZARD:
            continue
        if exc.exception_effect == EXCEPTION_UNRESOLVED:
            return False, exc, "boundary"
        if exc.exception_effect == EXCEPTION_PROTOCOL_DEFINED:
            if exc.approved_or_confirmed is None:
                return False, exc, "gap"
            if not exc.approved_or_confirmed:
                continue  # unapproved wording cannot rewrite
            return True, exc, None
        if exc.exception_effect == EXCEPTION_EFFECTIVE_RULE_CHANGE:
            if exc.approved_or_confirmed is None:
                return False, exc, "gap"
            if exc.effective_at_event_time is None:
                return False, exc, "gap"
            if not exc.approved_or_confirmed or not exc.effective_at_event_time:
                continue
            return True, exc, None
    return False, None, None


def evaluate_component_condition(
    *,
    unit_id: str,
    component: ProtocolComponent,
    bindings: Sequence[RuleEvidenceBinding],
    coverage_complete_roles: Mapping[str, bool],
    exceptions: Sequence[ProtocolExceptionBinding] = (),
    unit_conversion_rules: Sequence[UnitConversionRule] = (),
    retest_outcome: Optional[RetestOutcome] = None,
    subject_ref: str = "",
    site_ref: str = "",
    evidence_requirement: Optional[RuleEvidenceRequirement] = None,
) -> ComponentConditionOutcome:
    """Evaluate one atomic condition -> condition verdict (§4, §7).

    Auxiliary-only roles (IE/DV summaries, monitoring notes, free text)
    can never alone prove a criterion met or unmet (challenges 5/6).
    Identity/time mismatches and unconfirmed relations fail closed.
    Exceptions are classified per §7.3 and may flip the verdict with
    counterevidence.  The verdict is neutral ("condition satisfied as
    written"); mapping to the issue predicate is done separately.

    When an ``evidence_requirement`` is supplied, its required/alternate
    role sets are the authoritative evidence-role contract (§4.2): a
    binding may satisfy only a role declared by the requirement plus its
    identity/component -- the evaluator never re-derives a second
    divergent role list from the structured rule.
    """
    rule = component.structured_rule
    req = evidence_requirement
    if req is not None:
        required_roles = req.required_evidence_roles
        alternate_roles = req.alternate_evidence_roles
    else:
        required_roles = rule.required_evidence_roles
        alternate_roles = rule.alternate_evidence_roles
    rule_lineage = rule.rule_priority_policy or D04_RULE_LINEAGE_DEFAULT
    if component.verification_status != "verified":
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="规则抽取未经验证，任一/全部/至少 N 关系未冻结，禁止默认组合语义",
            gap_codes=(GAP_RULE_NOT_VERIFIED,),
            gaps=("规则抽取未经验证",))

    # Producer-dependency gate (challenge 32): a D04 unit consuming a
    # producer fact whose own evaluation is not_evaluable is blocked.
    blocked = [b for b in bindings if b.producer_dependency_blocked]
    if blocked:
        reason = blocked[0].producer_dependency_reason or (
            "所依赖的上游评价暂无法评价")
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE, reason=reason,
            gap_codes=(GAP_PRODUCER_DEPENDENCY,), gaps=(reason,))

    # Cross-domain gate: every binding carrying a producer ref must pass
    # the exact verification (§7.4).
    for b in bindings:
        if b.cross_domain_ref is None:
            continue
        gate = verify_cross_domain_ref(
            ref=b.cross_domain_ref, subject_ref=subject_ref,
            site_ref=site_ref,
            producer_unit_id=(
                b.expected_producer_unit_id
                or b.cross_domain_ref.producer_unit_id),
            control_point_id=component.control_point_id,
            component_id=component.component_id,
            relation_type=RELATION_ELIGIBILITY_FACT,
            rule_lineage=rule_lineage)
        if not gate.verified:
            return ComponentConditionOutcome(
                verdict=VERDICT_NOT_EVALUABLE, reason=gate.reason,
                gap_codes=(GAP_RELATION_UNCONFIRMED,), gaps=(gate.reason,))

    # Auxiliary-only gate: IE/DV/monitoring summaries are hints, never
    # standalone proof (§4.1/4.2).  Applies to the whole binding set even
    # when the auxiliary role is not in the rule's required/alternate set.
    if bindings and all(b.source_role in AUXILIARY_ONLY_ROLES
                        for b in bindings):
        code = (GAP_IE_SUMMARY_ONLY if bindings[0].source_role
                == "aggregate_ie_status" else GAP_FREE_TEXT_ONLY)
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason=("IEYN/IE 汇总或 DV 行不能作为逐条标准证据；"
                    "需要逐条 rule-specific 证据"),
            gap_codes=(code,),
            gaps=("仅有汇总/自由文本证据，无逐条标准证据",))

    relevant = [b for b in bindings
                if b.source_role in required_roles
                or b.source_role in alternate_roles]
    if relevant and all(b.source_role in AUXILIARY_ONLY_ROLES
                        for b in relevant):
        code = (GAP_IE_SUMMARY_ONLY if relevant[0].source_role
                == "aggregate_ie_status" else GAP_FREE_TEXT_ONLY)
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason=("IEYN/IE 汇总或 DV 行不能作为逐条标准证据；"
                    "需要逐条 rule-specific 证据"),
            gap_codes=(code,),
            gaps=("仅有汇总/自由文本证据，无逐条标准证据",))
    for b in bindings:
        if (b.source_role not in required_roles
                and b.source_role not in alternate_roles):
            return ComponentConditionOutcome(
                verdict=VERDICT_NOT_EVALUABLE,
                reason=(
                    f"证据角色 {b.source_role!r} 不在规则允许的"
                    f"required/alternate 集合内"),
                gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
                gaps=("证据角色不在规则允许集合内",))

    op = rule.operator
    if op in (OP_NUMERIC_AT_LEAST, OP_NUMERIC_AT_MOST, OP_NUMERIC_ABOVE,
              OP_NUMERIC_BELOW, OP_WITHIN_RANGE):
        outcome = _numeric_verdict(
            unit_id=unit_id, component_id=component.component_id,
            comparison=rule.comparison, bindings=relevant,
            conversion_rules=unit_conversion_rules, rule_lineage=rule_lineage)
    elif op == OP_EXISTS or op == OP_NOT_EXISTS:
        outcome = _evaluate_existence(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings,
            coverage_complete_roles=coverage_complete_roles,
            rule_lineage=rule_lineage)
    elif op == OP_TEMPORAL_INCLUSION:
        if not relevant:
            outcome = ComponentConditionOutcome(
                verdict=VERDICT_NOT_EVALUABLE,
                reason="缺少窗口内证据",
                gap_codes=(GAP_SOURCE_ROLE_NOT_COVERED,),
                gaps=("缺少窗口内证据",))
        else:
            b = relevant[0]
            if not b.is_confirmed:
                outcome = ComponentConditionOutcome(
                    verdict=VERDICT_NOT_EVALUABLE,
                    reason="证据关系未确认",
                    gap_codes=(GAP_EVIDENCE_IDENTITY_UNCONFIRMED,),
                    gaps=("证据关系未确认",))
            else:
                status, reason = _window_contains_date(
                    b.date_raw, rule.evaluation_window_start,
                    rule.evaluation_window_end, rule.window_start_inclusive,
                    rule.window_end_inclusive)
                if status == "inside":
                    ev = _binding_evidence(
                        unit_id=unit_id,
                        component_id=component.component_id, binding=b,
                        polarity=L1bEvidencePolarity.SUPPORTING,
                        rule_lineage=rule_lineage,
                        note="记录在规则窗口内")
                    outcome = ComponentConditionOutcome(
                        verdict=VERDICT_MET, reason="记录在规则窗口内",
                        supporting=(ev,), binding_ids=(b.binding_id,))
                elif status == "outside":
                    ev = _binding_evidence(
                        unit_id=unit_id,
                        component_id=component.component_id, binding=b,
                        polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                        rule_lineage=rule_lineage,
                        note="记录在规则窗口外")
                    outcome = ComponentConditionOutcome(
                        verdict=VERDICT_UNMET, reason="记录在规则窗口外",
                        counterevidence=(ev,), binding_ids=(b.binding_id,))
                elif status == "boundary":
                    outcome = ComponentConditionOutcome(
                        verdict=VERDICT_BOUNDARY, reason=reason,
                        gap_codes=(), gaps=())
                else:
                    outcome = ComponentConditionOutcome(
                        verdict=VERDICT_NOT_EVALUABLE, reason=reason,
                        gap_codes=(GAP_TEMPORAL_UNCOMPARABLE,),
                        gaps=(reason,))
    elif op in (OP_TEMPORAL_ORDER, OP_SEQUENCE):
        outcome = _evaluate_temporal_order(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage)
    elif op == OP_DURATION:
        outcome = _evaluate_duration(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage)
    elif op == OP_COUNT:
        outcome = _evaluate_count(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings,
            coverage_complete_roles=coverage_complete_roles,
            rule_lineage=rule_lineage,
            evidence_requirement=evidence_requirement)
    elif op == OP_AGE:
        outcome = _evaluate_age(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage)
    elif op == OP_DISCONTINUATION_TRIGGER:
        outcome = _evaluate_discontinuation_trigger(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings,
            conversion_rules=unit_conversion_rules, rule_lineage=rule_lineage,
            evidence_requirement=evidence_requirement)
    elif op == OP_INVESTIGATOR_JUDGMENT:
        outcome = _evaluate_investigator_judgment(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage)
    elif op in (OP_EQUALS, OP_NOT_EQUALS, OP_SET_MEMBERSHIP):
        outcome = _evaluate_equality_or_membership(
            unit_id=unit_id, component_id=component.component_id,
            rule=rule, bindings=bindings, rule_lineage=rule_lineage,
            evidence_requirement=evidence_requirement)
    elif op == OP_APPROVED_EXCEPTION:
        outcome = ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="approved_exception 不能作为原子运算子执行",
            gap_codes=(GAP_UNKNOWN_OPERATOR,),
            gaps=("例外运算符不受支持",))
    else:
        outcome = ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason=f"规则运算子 {op!r} 不受支持，无法评价",
            gap_codes=(GAP_UNKNOWN_OPERATOR,),
            gaps=("规则运算子不受支持",))

    # Retest handling (§7.1, challenges 22-24, 81): a qualifying retest may
    # cover the initial; a retest outside the allowed window cannot.
    if retest_outcome is not None and rule.retest_or_confirmation_policy.strip():
        rt = retest_outcome
        if rt.conflict_with_initial:
            return ComponentConditionOutcome(
                verdict=VERDICT_BOUNDARY,
                reason="两个同等权威的复测/确认结果且规则未规定优先级",
                gap_codes=(), gaps=())
        if rt.has_retest:
            if rt.retest_in_allowed_window is False:
                # Retest outside the allowed window cannot serve as
                # exclusion counterevidence (challenge 81).
                pass
            elif rt.meets_criterion is True and (
                    rt.retest_in_allowed_window is True
                    and rt.retest_authority_ok is not False
                    and rt.retest_count_ok is not False):
                ev = _binding_evidence(
                    unit_id=unit_id,
                    component_id=component.component_id,
                    binding=RuleEvidenceBinding(
                        binding_id=f"{component.component_id}-retest",
                        control_point_id=component.control_point_id,
                        component_id=component.component_id,
                        subject_ref=subject_ref or component.control_point_id,
                        site_ref=site_ref,
                        source_role="retest_result",
                        stable_source_event_key="retest",
                        source_locator=SourceLocator(
                            snapshot_id="retest-synthetic",
                            source_revision_id="retest-synthetic",
                            table_semantic="retest_result",
                            record_id=f"retest-{component.component_id}")),
                    polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                    rule_lineage=rule_lineage,
                    note="规则允许的复测结果满足要求，覆盖初筛结果")
                return ComponentConditionOutcome(
                    verdict=VERDICT_MET,
                    reason="规则允许的复测结果满足要求，覆盖初筛结果",
                    counterevidence=(ev,),
                    gap_codes=(), gaps=())
            elif rt.meets_criterion is None or (
                    rt.retest_in_allowed_window is None
                    or rt.retest_authority_ok is None
                    or rt.retest_count_ok is None):
                return ComponentConditionOutcome(
                    verdict=VERDICT_NOT_EVALUABLE,
                    reason="复测时间窗/次数/权威来源未确认，无法覆盖初筛",
                    gap_codes=(GAP_RETEST_UNCONFIRMED,),
                    gaps=("复测时间窗/次数/权威来源未确认",))

    # Exception handling (§7.3) -- after the operator verdict.
    qualifies, exc, gap_or_boundary = _qualifying_exception(
        component=component, subject_ref=subject_ref, site_ref=site_ref,
        exceptions=exceptions)
    if gap_or_boundary == "gap":
        return ComponentConditionOutcome(
            verdict=VERDICT_NOT_EVALUABLE,
            reason="例外/豁免的批准/确认状态缺失，无法判断其效力",
            gap_codes=(GAP_EXCEPTION_UNRESOLVED,),
            gaps=("例外/豁免状态缺失，无法判断其效力",))
    if gap_or_boundary == "boundary":
        return ComponentConditionOutcome(
            verdict=VERDICT_BOUNDARY,
            reason="例外/豁免效力类型无法唯一确定",
            gap_codes=(), gaps=())
    if qualifies:
        ev = None
        if exc is not None and exc.source_locator is not None:
            ev = EvidenceItem(
                evidence_id=f"ev-{unit_id}-{component.component_id}-exception",
                polarity=L1bEvidencePolarity.COUNTEREVIDENCE,
                locator=exc.source_locator,
                evidence_role="protocol_exception",
                rule_lineage=rule_lineage,
                uncertainty_note="方案预先允许的例外或已生效的正式规则变化")
        return ComponentConditionOutcome(
            verdict=VERDICT_MET,
            reason="方案预先允许的例外或已生效的正式规则变化，不构成问题",
            counterevidence=((ev,) if ev is not None else ()),
            context=outcome.context)
    return outcome


# ---------------------------------------------------------------------------
# Issue predicate + expression evaluation (§5)
# ---------------------------------------------------------------------------

def component_issue_predicate(
    control_point_type: str, verdict: str,
) -> str:
    """Map a condition verdict to the component issue predicate (§5).

    inclusion: satisfied -> no issue; exclusion: condition present ->
    issue; required action/discontinuation/sequence/other: requirement
    consistent -> no issue.
    """
    if verdict == VERDICT_BOUNDARY:
        return ISSUE_BOUNDARY
    if verdict == VERDICT_NOT_EVALUABLE:
        return ISSUE_NOT_EVALUABLE
    if verdict == VERDICT_NOT_APPLICABLE:
        return ISSUE_NOT_APPLICABLE
    if control_point_type == CONTROL_INCLUSION:
        return ISSUE_FALSE if verdict == VERDICT_MET else ISSUE_TRUE
    if control_point_type == CONTROL_EXCLUSION:
        return ISSUE_TRUE if verdict == VERDICT_MET else ISSUE_FALSE
    if control_point_type == CONTROL_DISCONTINUATION_OR_WITHDRAWAL:
        return ISSUE_FALSE if verdict == VERDICT_MET else ISSUE_TRUE
    if control_point_type in (
            CONTROL_REQUIRED_PROCEDURE_OR_ASSESSMENT,
            CONTROL_CONSENT_RANDOMIZATION_ENROLLMENT,
            CONTROL_OTHER_PROTOCOL_REQUIREMENT):
        return ISSUE_FALSE if verdict == VERDICT_MET else ISSUE_TRUE
    return ISSUE_NOT_EVALUABLE


@dataclass(frozen=True)
class ExpressionEvaluation:
    """Outcome of evaluating the parent issue expression over feasible
    assignments (§5)."""

    disposition: str
    gap_component_ids: Tuple[str, ...] = ()
    decisive_component_ids: Tuple[str, ...] = ()
    reason: str = ""


def evaluate_issue_expression(
    expression: Optional[IssueExpression],
    component_results: Mapping[str, str],
    *,
    all_not_applicable: bool,
    control_point_authoritatively_not_applicable: bool,
) -> ExpressionEvaluation:
    """Evaluate AND/OR/NOT/AT_LEAST_N over feasible truth assignments.

    For boundary/not_evaluable components every feasible assignment is
    considered: constant true -> positive; constant false -> negative;
    mixed with any participating not_evaluable -> not_evaluable; mixed
    otherwise -> boundary; all components not applicable and the control
    point authoritatively not applicable -> not_applicable; an incomplete
    expression/component set -> not_evaluable (no AND/OR defaulting).
    """
    if expression is None:
        return ExpressionEvaluation(
            disposition=L1Disposition.NOT_EVALUABLE,
            reason="缺少父级问题表达式，无法评价组合标准")
    unknown = [cid for cid in expression.component_ids
               if cid not in component_results]
    if unknown:
        return ExpressionEvaluation(
            disposition=L1Disposition.NOT_EVALUABLE,
            reason=f"表达式引用未知子条件 {sorted(unknown)}",
            gap_component_ids=tuple(unknown))

    feasible_sets: List[Tuple[str, Tuple[bool, ...]]] = []
    gap_ids: List[str] = []
    decisive: List[str] = []
    participating: List[str] = []
    for cid in expression.component_ids:
        result = component_results[cid]
        if result == ISSUE_TRUE:
            feasible_sets.append((cid, (True,)))
            decisive.append(cid)
        elif result == ISSUE_FALSE:
            feasible_sets.append((cid, (False,)))
        elif result == ISSUE_BOUNDARY:
            feasible_sets.append((cid, (True, False)))
            gap_ids.append(cid)
        elif result == ISSUE_NOT_EVALUABLE:
            feasible_sets.append((cid, (True, False)))
            gap_ids.append(cid)
        elif result == ISSUE_NOT_APPLICABLE:
            continue
        else:
            return ExpressionEvaluation(
                disposition=L1Disposition.NOT_EVALUABLE,
                reason=f"子条件 {cid!r} 的问题谓词结果 {result!r} 无效")
        participating.append(cid)

    if not participating:
        if control_point_authoritatively_not_applicable:
            return ExpressionEvaluation(
                disposition=L1Disposition.NOT_APPLICABLE,
                reason="全部子条件明确不适用且控制点经权威适用性证明不适用")
        return ExpressionEvaluation(
            disposition=L1Disposition.NOT_EVALUABLE,
            reason="全部子条件不适用但控制点未经权威证明不适用",
            gap_component_ids=tuple(gap_ids))

    # Cartesian product over feasible assignments.
    outcomes: Set[bool] = set()
    ids = [cid for cid, _ in feasible_sets]
    values = [vals for _, vals in feasible_sets]
    for combo in itertools.product(*values):
        assignment = dict(zip(ids, combo))
        outcomes.add(expression.truth_value(assignment))
        if len(outcomes) == 2:
            break

    gap_ids = [cid for cid in gap_ids if cid in participating]
    if outcomes == {True}:
        return ExpressionEvaluation(
            disposition=L1Disposition.POSITIVE,
            gap_component_ids=tuple(gap_ids),
            decisive_component_ids=tuple(sorted(decisive)),
            reason="所有可行赋值下表达式恒为真")
    if outcomes == {False}:
        return ExpressionEvaluation(
            disposition=L1Disposition.NEGATIVE,
            gap_component_ids=tuple(gap_ids),
            decisive_component_ids=tuple(sorted(decisive)),
            reason="所有可行赋值下表达式恒为假")
    has_not_evaluable = any(
        component_results[cid] == ISSUE_NOT_EVALUABLE
        for cid in participating)
    if has_not_evaluable:
        return ExpressionEvaluation(
            disposition=L1Disposition.NOT_EVALUABLE,
            gap_component_ids=tuple(gap_ids),
            reason="真/假均可行且参与的不确定子条件无法评价")
    return ExpressionEvaluation(
        disposition=L1Disposition.BOUNDARY,
        gap_component_ids=tuple(gap_ids),
        reason="真/假均可行且所有参与子条件均可评价，仍无法唯一确定")


# ---------------------------------------------------------------------------
# Risk identity (§5) -- public R2 make_risk_identity only
# ---------------------------------------------------------------------------

def _evaluation_window_id(
    *, eval_anchor_kind: str, window_start: str, window_end: str,
    precision: str, endpoint_inclusivity: str,
) -> str:
    """Stable canonical window id (no Run/snapshot/revision).  Two
    disjoint windows under the same anchor kind get different ids and
    therefore different risk identities (challenge 68)."""
    return "d04-window-" + content_hash({
        "eval_anchor_kind": eval_anchor_kind,
        "window_start": window_start,
        "window_end": window_end,
        "precision": precision,
        "endpoint_inclusivity": endpoint_inclusivity,
    })


def _d04_risk_classifier(
    *, subject_ref: str, control_point_id: str, evaluation_node_id: str,
    signal_type: str, eval_anchor_kind: str, evaluation_window_id: str,
) -> str:
    """Classifier/stable-core (frozen §5): never contains protocol version,
    snapshot/revision, mutable free text or Query."""
    return content_hash({
        "subject_ref": subject_ref,
        "control_point_id": control_point_id,
        "evaluation_node_id": evaluation_node_id,
        "signal_type": signal_type,
        "eval_anchor_kind": eval_anchor_kind,
        "evaluation_window_id": evaluation_window_id,
    })


def _d04_risk_scope(
    *, site_ref: str, protocol_id: str, protocol_version: str,
    amendment_id_or_hash: str, cohort: str, phase: str,
    rule_content_hash: str, date_precision: str, mapping_version: str,
    unit_term_policy_version: str,
) -> List[str]:
    """Canonical sorted scope/lineage payload (§5)."""
    parts: Set[str] = {
        f"site:{site_ref}" if site_ref else "site:",
        f"protocol:{protocol_id}/{protocol_version}/{amendment_id_or_hash}",
        f"cohort:{cohort}" if cohort else "cohort:",
        f"phase:{phase}" if phase else "phase:",
        f"rule:{rule_content_hash}",
        f"dp:{date_precision}",
        f"mapping:{mapping_version}",
        f"utp:{unit_term_policy_version}",
        f"ua:{D04_UNIT_ALGO_VERSION}",
    }
    return sorted(parts)


def _build_d04_candidate(
    *, project_id: str, subject_ref: str, site_ref: str,
    control_point: ProtocolControlPoint, evaluation_node_id: str,
    signal_type: str, window: EvaluationWindowSpec,
    plan: ProtocolRuleEvaluationPlan, applicability: ProtocolApplicabilityDecision,
    snapshot_id: str, monitoring_priority: str, positive_subtype: str,
    audience_label: str, match_reason: str,
    decisive_component_ids: Sequence[str] = (),
    unresolved_component_ids: Sequence[str] = (),
    rights_or_safety_critical: bool = False,
    machine_close_forbidden: bool = False,
) -> Tuple[RiskCandidate, RiskIdentity]:
    """Build the D04 R2 candidate (public make_risk_identity only)."""
    window_id = _evaluation_window_id(
        eval_anchor_kind=window.eval_anchor_kind,
        window_start=window.window_start, window_end=window.window_end,
        precision=window.precision,
        endpoint_inclusivity=window.endpoint_inclusivity)
    classifier = _d04_risk_classifier(
        subject_ref=subject_ref,
        control_point_id=control_point.control_point_id,
        evaluation_node_id=evaluation_node_id,
        signal_type=signal_type,
        eval_anchor_kind=window.eval_anchor_kind,
        evaluation_window_id=window_id)
    scope = _d04_risk_scope(
        site_ref=site_ref, protocol_id=applicability.protocol_id,
        protocol_version=applicability.protocol_version,
        amendment_id_or_hash=applicability.amendment_id_or_hash,
        cohort=applicability.cohort, phase=applicability.phase,
        rule_content_hash=plan.rule_content_hash,
        date_precision=window.precision,
        mapping_version=plan.mapping_version,
        unit_term_policy_version=plan.unit_term_policy_version)
    identity = make_risk_identity(
        project_id=project_id, subject_ref=subject_ref,
        domain=D04_DOMAIN, scope=scope, classifier=classifier)
    stable_event_key = (
        f"protocol:{control_point.control_point_id}:{window_id}")
    detail: Dict[str, Any] = {
        "risk_identity_id": identity.risk_identity_id,
        "stable_core": classifier,
        "lineage_fingerprint": "|".join(identity.scope),
        "scope": list(identity.scope),
        "classifier": identity.classifier,
        "domain": identity.domain,
        "stable_source_event_key": stable_event_key,
        "full_locator_id": control_point.source_locator.locator_id(),
        "risk_family": signal_type,
        "control_point_id": control_point.control_point_id,
        "control_point_type": control_point.control_point_type,
        "evaluation_node_id": evaluation_node_id,
        "signal_type": signal_type,
        "positive_subtype": positive_subtype,
        "audience_label": audience_label,
        "eval_anchor_kind": window.eval_anchor_kind,
        "evaluation_window_id": window_id,
        "monitoring_priority": monitoring_priority,
        "decisive_component_ids": sorted(set(decisive_component_ids)),
        "unresolved_component_ids": sorted(set(unresolved_component_ids)),
        "match_reason": match_reason,
        "protocol_id": applicability.protocol_id,
        "protocol_version": applicability.protocol_version,
        "amendment_id_or_hash": applicability.amendment_id_or_hash,
        "locator_id": control_point.source_locator.locator_id(),
        "rights_or_safety_critical": rights_or_safety_critical,
        "machine_close_forbidden": machine_close_forbidden,
    }
    candidate = RiskCandidate.from_signal(
        project_id=project_id, subject_ref=subject_ref,
        domain=D04_DOMAIN, signal_type=positive_subtype,
        source_snapshot_id=snapshot_id,
        rule_activation_id=(
            plan.rule_content_hash or D04_RULE_LINEAGE_DEFAULT),
        severity_hint=monitoring_priority, confidence_hint=0.0,
        detail=detail)
    return candidate, identity


# ---------------------------------------------------------------------------
# Query drafts (§8.3) -- three-part Chinese wording, context-conditional
# ---------------------------------------------------------------------------

def _anchor_label(anchor_kind: str) -> str:
    return _ANCHOR_LABELS.get(anchor_kind, anchor_kind)


def _action_suffix(query_context: str) -> str:
    if query_context == QUERY_CONTEXT_NOT_OCCURRED:
        return "请核实入排结果、筛选结论或数据记录，并补充或更正相应记录。"
    if query_context == QUERY_CONTEXT_ENROLLED:
        return ("请核实、说明、补充或更正相应记录；如确认不符合方案，"
                "请评估是否构成方案偏离并按相应流程处理。")
    return ("请先核实是否已随机/入组/接受研究干预及事件时序；"
            "当前资料不足，暂无法确认是否符合方案。")


def _build_query_ref(
    *, query_id: str, unit_id: str, subject_ref: str,
    subtype: str, control_point: ProtocolControlPoint,
    plan: ProtocolRuleEvaluationPlan, applicability: ProtocolApplicabilityDecision,
    window: EvaluationWindowSpec, enrollment_context: EnrollmentContext,
    decisive_ids: Sequence[str], unresolved_ids: Sequence[str],
    finding_facts: Sequence[str],
    candidate_id: str, source_locator_ids: Sequence[str],
) -> QueryDraftRef:
    basis = (
        f"依据：方案 {plan.protocol_id} {applicability.protocol_version}"
        f"（修订 {applicability.amendment_id_or_hash or '无'}）"
        f"{control_point.official_section_id} "
        f"{control_point.official_criterion_id}（{control_point.official_heading}）"
        f"；适用时点 {_anchor_label(window.eval_anchor_kind)}。")
    if finding_facts:
        facts = "；".join(finding_facts)
    else:
        facts = "当前支持依据与排除依据均需进一步核实"
    decisive_txt = "、".join(sorted(set(decisive_ids))) if decisive_ids else ""
    unresolved_txt = (
        "、".join(sorted(set(unresolved_ids))) if unresolved_ids else "")
    scope_txt = ""
    if decisive_txt:
        scope_txt += f"决定性子条件：{decisive_txt}。"
    if unresolved_txt:
        scope_txt += f"未决子条件：{unresolved_txt}（资料不足，完整性受阻）。"
    finding = (
        f"发现：参与者 {subject_ref} {facts}。{scope_txt}"
        f"支持依据定位 {', '.join(sorted(source_locator_ids))}。")
    action = f"行动项：{_action_suffix(enrollment_context.query_context)}"
    return QueryDraftRef(
        query_id=query_id, unit_id=unit_id,
        basis=basis, finding=finding, action=action,
        source_locator_ids=tuple(_canonical_sorted(source_locator_ids)),
        linked_candidate_id=candidate_id)


# ---------------------------------------------------------------------------
# ProtocolUnitResult (§2 RiskDomainUnitResult + ledger materialization)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolUnitResult:
    """The evaluation outcome for one D04 EvaluationUnit.

    Satisfies the neutral ``RiskDomainUnitResult`` protocol and can
    materialize a full ``UnitEvaluation`` for the CoverageLedger.
    """

    unit_id: str
    subject_ref: str
    l1_disposition: str
    monitoring_priority: str
    l0_status: str = L0CoverageStatus.COVERED
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    risk_candidate_refs: Tuple[RiskCandidateRef, ...] = ()
    risk_instance_refs: Tuple[RiskInstanceRef, ...] = ()
    not_evaluable_reason: str = ""
    evidence: Tuple[EvidenceItem, ...] = ()
    source_record_refs: Tuple[SourceRecordRef, ...] = ()
    query_refs: Tuple[QueryDraftRef, ...] = ()
    coverage_gap_notices: Tuple[ProtocolCoverageGapNotice, ...] = ()
    boundary_reason: str = ""
    positive_subtype: str = ""
    audience_label: str = ""
    query_context: str = ""
    decisive_component_ids: Tuple[str, ...] = ()
    unresolved_component_ids: Tuple[str, ...] = ()
    component_assessments: Tuple[ProtocolComponentAssessment, ...] = ()
    journey_markers: Tuple[ProtocolRiskMarker, ...] = ()
    protocol_locator_ids: Tuple[str, ...] = ()
    eval_anchor_kind: str = ""
    window_start: str = ""
    window_end: str = ""
    precision: str = ""
    endpoint_inclusivity: str = ""
    evaluation_window_id: str = ""
    control_point_id: str = ""
    evaluation_node_id: str = ""
    signal_type: str = ""
    protocol_version: str = ""
    amendment_id_or_hash: str = ""

    def __post_init__(self) -> None:
        if self.l1_disposition not in L1Disposition.ALL:
            raise ProtocolSliceError(
                f"l1_disposition={self.l1_disposition!r} not a valid L1")
        if self.monitoring_priority not in VALID_MONITORING_PRIORITIES:
            raise ProtocolSliceError(
                f"monitoring_priority={self.monitoring_priority!r} invalid")
        if self.l0_status not in L0CoverageStatus.ALL_STATUSES:
            raise ProtocolSliceError(
                f"l0_status={self.l0_status!r} invalid")
        if self.query_context and self.query_context not in QUERY_CONTEXTS:
            raise ProtocolSliceError(
                f"query_context={self.query_context!r} invalid")
        object.__setattr__(self, "r2_candidates",
                           tuple(self.r2_candidates))
        object.__setattr__(self, "risk_candidate_refs",
                           tuple(self.risk_candidate_refs))
        object.__setattr__(self, "risk_instance_refs",
                           tuple(self.risk_instance_refs))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "source_record_refs",
                           tuple(self.source_record_refs))
        object.__setattr__(self, "query_refs", tuple(self.query_refs))
        object.__setattr__(self, "coverage_gap_notices",
                           tuple(self.coverage_gap_notices))
        object.__setattr__(self, "component_assessments",
                           tuple(self.component_assessments))
        object.__setattr__(self, "journey_markers",
                           tuple(self.journey_markers))
        object.__setattr__(self, "protocol_locator_ids",
                           _canonical_sorted(self.protocol_locator_ids))
        object.__setattr__(self, "decisive_component_ids",
                           _canonical_sorted(self.decisive_component_ids))
        object.__setattr__(self, "unresolved_component_ids",
                           _canonical_sorted(self.unresolved_component_ids))

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
        self, *, provenance_snapshot_id: str = "",
        provenance_rule_lineage: str = "",
    ) -> UnitEvaluation:
        polarities: List[str] = []
        for ev in self.evidence:
            if ev.polarity not in polarities:
                polarities.append(ev.polarity)
        return UnitEvaluation(
            unit_id=self.unit_id, l0_status=self.l0_status,
            l1_disposition=self.l1_disposition,
            l1b_polarities=tuple(sorted(polarities)),
            evidence=self.evidence,
            source_record_refs=self.source_record_refs,
            risk_candidate_refs=self.risk_candidate_refs,
            risk_instance_refs=self.risk_instance_refs,
            query_refs=self.query_refs,
            provenance_snapshot_id=provenance_snapshot_id,
            provenance_rule_lineage=provenance_rule_lineage,
            not_evaluable_reason=self.not_evaluable_reason)


# ---------------------------------------------------------------------------
# Unit-level evaluation
# ---------------------------------------------------------------------------

def _make_source_record_ref(locator: SourceLocator) -> SourceRecordRef:
    return SourceRecordRef(record_id=locator.record_id, locator=locator)


def _component_assessment(
    *, unit_id: str, component: ProtocolComponent,
    predicate: str, outcome: ComponentConditionOutcome,
    rule_lineage: str,
) -> ProtocolComponentAssessment:
    assessment_id = "d04-ca-" + content_hash({
        "unit_id": unit_id,
        "component_id": component.component_id,
        "issue_predicate_result": predicate,
        "gaps": list(_canonical_sorted(outcome.gap_codes)),
        "evidence_ids": sorted(
            ev.evidence_id
            for ev in outcome.supporting + outcome.counterevidence
            + outcome.context),
    })
    return ProtocolComponentAssessment(
        assessment_id=assessment_id, unit_id=unit_id,
        component_id=component.component_id,
        official_criterion_id=component.official_criterion_id,
        issue_predicate_result=predicate,
        evidence=outcome.supporting + outcome.context,
        counterevidence=outcome.counterevidence,
        gaps=outcome.gaps,
        gap_reason_codes=outcome.gap_codes,
        rationale=outcome.reason)


def _evaluate_gate_unit(
    *, project_id: str, expanded: ProtocolUnitExpanded,
) -> ProtocolUnitResult:
    """Applicability/routing gate evaluation (§5).

    Gates are subject-level blocking units: they carry no R2 risk
    identity (the frozen classifier covers only atomic|package nodes),
    no candidate and no Query.  ``multi_feasible_boundary`` -> boundary;
    ``not_evaluable`` / routing gaps -> not_evaluable with a coverage-gap
    notice.  Affected control point ids stay in the decision context and
    never pollute the L1 denominator (challenges 60/67/71).
    """
    unit = expanded.build_unit(project_id)
    unit_id = unit.unit_id
    protocol_loc = tuple(
        sorted({loc.locator_id()
                for loc in expanded.applicability.source_locators}))
    if expanded.evaluation_node_id == NODE_ROUTING_GATE:
        reason = expanded.not_evaluable_reason_hint or (
            "控制点归属路由无法唯一确定，禁止在多个域各建风险")
        notice = _gap_notice(
            unit_id=unit_id, reason_code=GAP_ROUTING_UNRESOLVED,
            protocol_locator_ids=protocol_loc,
            reachable_source_locator_ids=protocol_loc)
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=L0CoverageStatus.NOT_EVALUABLE,
            not_evaluable_reason=reason,
            coverage_gap_notices=(notice,),
            protocol_locator_ids=protocol_loc,
            evaluation_node_id=NODE_ROUTING_GATE,
            signal_type=SIGNAL_PROTOCOL_ROUTING,
            control_point_id=(
                expanded.control_point.control_point_id
                if expanded.control_point is not None
                else "protocol_routing"),
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)
    # applicability gate
    if expanded.applicability.decision_status == (
            APPLICABILITY_MULTI_FEASIBLE_BOUNDARY):
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.BOUNDARY,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=L0CoverageStatus.PARTIAL,
            boundary_reason=expanded.not_evaluable_reason_hint or (
                "多个可行方案版本均有依据，适用性存在边界"),
            protocol_locator_ids=protocol_loc,
            eval_anchor_kind=ANCHOR_OTHER,
            precision=PRECISION_UNKNOWN,
            endpoint_inclusivity=INCLUSIVITY_GATE,
            evaluation_node_id=NODE_APPLICABILITY_GATE,
            signal_type=SIGNAL_PROTOCOL_APPLICABILITY,
            control_point_id="protocol_applicability",
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)
    reason = expanded.not_evaluable_reason_hint or (
        "批准/启用/过渡条款/重新知情/事件关键日期缺失或冲突，"
        "无法确定适用方案版本")
    notice = _gap_notice(
        unit_id=unit_id, reason_code=GAP_APPLICABILITY_UNDETERMINED,
        protocol_locator_ids=protocol_loc,
        reachable_source_locator_ids=protocol_loc)
    return ProtocolUnitResult(
        unit_id=unit_id, subject_ref=expanded.subject_ref,
        l1_disposition=L1Disposition.NOT_EVALUABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        l0_status=L0CoverageStatus.NOT_EVALUABLE,
        not_evaluable_reason=reason,
        coverage_gap_notices=(notice,),
        protocol_locator_ids=protocol_loc,
        eval_anchor_kind=ANCHOR_OTHER,
        precision=PRECISION_UNKNOWN,
        endpoint_inclusivity=INCLUSIVITY_GATE,
        evaluation_node_id=NODE_APPLICABILITY_GATE,
        signal_type=SIGNAL_PROTOCOL_APPLICABILITY,
        control_point_id="protocol_applicability",
        protocol_version=expanded.applicability.protocol_version,
        amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)


# ---------------------------------------------------------------------------
# Component assessment (§5) -- stable, never a unit id
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolComponentAssessment:
    """One component's issue predicate + gaps/counterevidence (§5).

    Component assessments never enter the expected-set, L1/L2 or
    lifecycle; their ids are independent stable ids and never disguise
    as EvaluationUnit ids (challenge 59).
    """

    assessment_id: str
    unit_id: str
    component_id: str
    official_criterion_id: str
    issue_predicate_result: str
    evidence: Tuple[EvidenceItem, ...] = ()
    counterevidence: Tuple[EvidenceItem, ...] = ()
    gaps: Tuple[str, ...] = ()
    gap_reason_codes: Tuple[str, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        _validate_nonempty(self.assessment_id,
                           "ProtocolComponentAssessment.assessment_id")
        _validate_nonempty(self.unit_id,
                           "ProtocolComponentAssessment.unit_id")
        _validate_nonempty(self.component_id,
                           "ProtocolComponentAssessment.component_id")
        if self.issue_predicate_result not in ISSUE_RESULTS:
            raise ProtocolSliceError(
                f"issue_predicate_result="
                f"{self.issue_predicate_result!r} invalid")
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "counterevidence",
                           tuple(self.counterevidence))
        object.__setattr__(self, "gaps", tuple(self.gaps))
        object.__setattr__(self, "gap_reason_codes",
                           tuple(self.gap_reason_codes))
        if self.assessment_id.startswith("unit-") or self.assessment_id.startswith("d04-eset-"):
            raise ProtocolSliceError(
                "component assessment id must never disguise as a unit id")


# ---------------------------------------------------------------------------
# Core evaluation: evaluate_protocol_unit
# ---------------------------------------------------------------------------

def evaluate_protocol_unit(
    *,
    project_id: str,
    expanded: ProtocolUnitExpanded,
    bindings: Sequence[RuleEvidenceBinding] = (),
    coverage_complete_roles: Optional[Mapping[str, bool]] = None,
    exceptions: Sequence[ProtocolExceptionBinding] = (),
    unit_conversion_rules: Sequence[UnitConversionRule] = (),
    retest_outcomes: Optional[Mapping[str, RetestOutcome]] = None,
    enrollment_context: Optional[EnrollmentContext] = None,
    priority_policy: Optional[D04PriorityPolicy] = None,
    snapshot_id: str = "",
) -> ProtocolUnitResult:
    """Evaluate one D04 expanded unit (§5, §6).

    * applicability/routing gates produce subject-level blocking units
      (no candidate/risk/Query);
    * atomic roots evaluate their single component;
    * package roots evaluate every component then run the parent issue
      expression over feasible uncertain assignments;
    * positive units carry at most one candidate + one Query (deciding
      components listed, unresolved gaps preserved); negative units carry
      none; boundary units carry a clue candidate only; not_evaluable
      units carry zero candidate/risk/Query plus a coverage-gap notice;
    * L0/L1 are orthogonal: a determinate L1 with an unresolved component
      gap keeps L0 partial and blocks domain completeness.
    """
    coverage = dict(coverage_complete_roles or {})
    retests = dict(retest_outcomes or {})
    unit = expanded.build_unit(project_id)
    unit_id = unit.unit_id

    if expanded.evaluation_node_id in (NODE_APPLICABILITY_GATE,
                                       NODE_ROUTING_GATE):
        return _evaluate_gate_unit(project_id=project_id, expanded=expanded)

    assert expanded.control_point is not None
    cp = expanded.control_point
    rule_lineage = (
        expanded.plan.rule_content_hash or D04_RULE_LINEAGE_DEFAULT)
    window = expanded.window
    window_id = _evaluation_window_id(
        eval_anchor_kind=window.eval_anchor_kind,
        window_start=window.window_start, window_end=window.window_end,
        precision=window.precision,
        endpoint_inclusivity=window.endpoint_inclusivity)

    if expanded.control_point_not_applicable:
        return _not_applicable_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            cp=cp, window_id=window_id, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id)

    # -- atomic root ------------------------------------------------------
    if expanded.evaluation_node_id == NODE_ATOMIC:
        assert cp.structured_rule is not None
        component = ProtocolComponent(
            component_id=cp.control_point_id,
            control_point_id=cp.control_point_id,
            official_criterion_id=cp.official_criterion_id,
            parent_rule_id=cp.parent_rule_id,
            display_order=cp.display_order,
            nesting_path=cp.nesting_path,
            verbatim_text=cp.verbatim_text,
            source_locator=cp.source_locator,
            source_revision_hash=cp.source_revision_hash,
            structured_rule=cp.structured_rule,
            verification_status=cp.verification_status)
        component_bindings = _bindings_for_component(
            component.component_id, bindings, expanded)
        requirement = _requirement_for_component(
            component.component_id, expanded)
        outcome = evaluate_component_condition(
            unit_id=unit_id, component=component,
            bindings=component_bindings,
            coverage_complete_roles=coverage,
            exceptions=exceptions,
            unit_conversion_rules=unit_conversion_rules,
            retest_outcome=retests.get(component.component_id),
            subject_ref=expanded.subject_ref, site_ref=expanded.site_ref,
            evidence_requirement=requirement)
        predicate = component_issue_predicate(
            cp.control_point_type, outcome.verdict)
        if predicate == ISSUE_NOT_APPLICABLE:
            if expanded.control_point_not_applicable:
                return _not_applicable_unit(
                    project_id=project_id, expanded=expanded,
                    unit_id=unit_id, cp=cp, window_id=window_id,
                    rule_lineage=rule_lineage, snapshot_id=snapshot_id)
            predicate = ISSUE_NOT_EVALUABLE
        if predicate == ISSUE_TRUE:
            disposition = L1Disposition.POSITIVE
        elif predicate == ISSUE_FALSE:
            disposition = L1Disposition.NEGATIVE
        else:
            disposition = predicate  # boundary/not_evaluable share L1 tokens
        affected_ids = ((component.component_id,)
                        if predicate in (ISSUE_NOT_EVALUABLE, ISSUE_BOUNDARY)
                        else ())
        missing_roles = _missing_evidence_roles(
            expanded=expanded, affected_component_ids=affected_ids,
            bindings=bindings, coverage=coverage)
        assessment = _component_assessment(
            unit_id=unit_id, component=component, predicate=predicate,
            outcome=outcome, rule_lineage=rule_lineage)
        return _materialize_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            cp=cp, window=window, window_id=window_id,
            predicate=disposition, assessments=(assessment,),
            outcomes=(outcome,), decisive_ids=(),
            unresolved_ids=(
                (component.component_id,) if predicate in (
                    ISSUE_NOT_EVALUABLE, ISSUE_BOUNDARY) else ()),
            rule_lineage=rule_lineage, snapshot_id=snapshot_id,
            enrollment_context=enrollment_context,
            priority_policy=priority_policy,
            missing_evidence_roles=missing_roles)

    # -- package root -----------------------------------------------------
    assert expanded.issue_expression is not None
    if expanded.plan.verification_status != "verified":
        # Original 任一/全部/至少 N semantics not unambiguously resolved:
        # the whole root is not_evaluable; AND/OR is never defaulted
        # (challenge 82).
        notice = _gap_notice(
            unit_id=unit_id, reason_code=GAP_RULE_NOT_VERIFIED,
            protocol_locator_ids=(cp.source_locator.locator_id(),),
            reachable_source_locator_ids=(cp.source_locator.locator_id(),))
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=L0CoverageStatus.NOT_EVALUABLE,
            not_evaluable_reason=(
                "规则抽取未经验证，任一/全部/至少 N 关系无法无歧义确定，"
                "禁止默认组合关系"),
            source_record_refs=(_make_source_record_ref(cp.source_locator),),
            coverage_gap_notices=(notice,),
            unresolved_component_ids=tuple(expanded.component_ids),
            protocol_locator_ids=(cp.source_locator.locator_id(),),
            eval_anchor_kind=window.eval_anchor_kind,
            window_start=window.window_start, window_end=window.window_end,
            precision=window.precision,
            endpoint_inclusivity=window.endpoint_inclusivity,
            evaluation_window_id=window_id,
            control_point_id=cp.control_point_id,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type,
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)

    component_results: Dict[str, str] = {}
    assessments: List[ProtocolComponentAssessment] = []
    outcomes_by_id: Dict[str, ComponentConditionOutcome] = {}
    for cid in expanded.component_ids:
        component = _require_component(cid, expanded)
        component_bindings = _bindings_for_component(
            cid, bindings, expanded)
        requirement = _requirement_for_component(cid, expanded)
        outcome = evaluate_component_condition(
            unit_id=unit_id, component=component,
            bindings=component_bindings,
            coverage_complete_roles=coverage,
            exceptions=exceptions,
            unit_conversion_rules=unit_conversion_rules,
            retest_outcome=retests.get(cid),
            subject_ref=expanded.subject_ref, site_ref=expanded.site_ref,
            evidence_requirement=requirement)
        predicate = component_issue_predicate(
            cp.control_point_type, outcome.verdict)
        if predicate == ISSUE_NOT_APPLICABLE and not expanded.control_point_not_applicable:
            predicate = ISSUE_NOT_EVALUABLE
        component_results[cid] = predicate
        outcomes_by_id[cid] = outcome
        assessments.append(_component_assessment(
            unit_id=unit_id, component=component, predicate=predicate,
            outcome=outcome, rule_lineage=rule_lineage))

    expr_eval = evaluate_issue_expression(
        expanded.issue_expression, component_results,
        all_not_applicable=all(
            r == ISSUE_NOT_APPLICABLE for r in component_results.values()),
        control_point_authoritatively_not_applicable=(
            expanded.control_point_not_applicable))
    affected_ids = tuple(
        cid for cid, r in component_results.items()
        if r in (ISSUE_NOT_EVALUABLE, ISSUE_BOUNDARY))
    missing_roles = _missing_evidence_roles(
        expanded=expanded, affected_component_ids=affected_ids,
        bindings=bindings, coverage=coverage)
    return _materialize_unit(
        project_id=project_id, expanded=expanded, unit_id=unit_id,
        cp=cp, window=window, window_id=window_id,
        predicate=expr_eval.disposition, assessments=tuple(assessments),
        outcomes=tuple(outcomes_by_id[cid]
                       for cid in expanded.component_ids),
        decisive_ids=expr_eval.decisive_component_ids,
        unresolved_ids=expr_eval.gap_component_ids,
        rule_lineage=rule_lineage, snapshot_id=snapshot_id,
        enrollment_context=enrollment_context,
        priority_policy=priority_policy,
        forced_reason=(
            expr_eval.reason
            if expr_eval.disposition == L1Disposition.NOT_EVALUABLE
            else ""),
        missing_evidence_roles=missing_roles)


def _bindings_for_component(
    component_id: str, bindings: Sequence[RuleEvidenceBinding],
    expanded: ProtocolUnitExpanded,
) -> Tuple[RuleEvidenceBinding, ...]:
    """Select bindings for one component (§4.2).

    Bindings for another subject/site/control point are ordinary
    non-matching evidence in a multi-subject accepted listing and are
    excluded, never a fatal kernel error.  When no valid required
    evidence remains the operator evaluation fails closed to
    ``not_evaluable`` with a missing-role/identity coverage notice and
    zero candidate/risk/Query.  Unconfirmed cross-domain relations are
    still handled explicitly inside the component evaluator.
    """
    matched: List[RuleEvidenceBinding] = []
    for b in bindings:
        if b.component_id != component_id:
            continue
        if (b.control_point_id
                != (expanded.control_point.control_point_id
                    if expanded.control_point is not None else "")):
            continue
        if (b.subject_ref != expanded.subject_ref
                or b.site_ref != expanded.site_ref):
            continue
        matched.append(b)
    return tuple(matched)


def _require_component(
    component_id: str, expanded: ProtocolUnitExpanded,
) -> ProtocolComponent:
    if not expanded.components:
        raise ProtocolSliceError(
            f"package {expanded.control_point.control_point_id} has no "
            f"component map; supply components to expand_protocol_expected_set")
    component = expanded.components.get(component_id)
    if component is None:
        raise ProtocolSliceError(
            f"unknown component {component_id!r} for package unit")
    return component


def _requirement_for_component(
    component_id: str, expanded: ProtocolUnitExpanded,
) -> RuleEvidenceRequirement:
    """Return the generated evidence requirement for one component.

    The generated ``evidence_requirements`` are the authoritative
    evidence-role contract (§4.2): evaluation never re-derives a second
    role list from the structured rule.  A missing requirement fails
    closed -- no silent inference.
    """
    for req in expanded.evidence_requirements:
        if req.component_id == component_id:
            return req
    cp_id = (expanded.control_point.control_point_id
             if expanded.control_point is not None else "")
    raise ProtocolSliceError(
        f"no generated RuleEvidenceRequirement for component "
        f"{component_id!r} under control point {cp_id!r}")


def _not_applicable_unit(
    *, project_id: str, expanded: ProtocolUnitExpanded, unit_id: str,
    cp: ProtocolControlPoint, window_id: str, rule_lineage: str,
    snapshot_id: str,
) -> ProtocolUnitResult:
    """Materialize an authoritatively not-applicable control point (§6.5).

    Only active protocol/design, cohort/phase and subject scope jointly
    prove non-applicability; no record, no mapping and "model cannot
    judge" are never not_applicable.
    """
    window = expanded.window
    src_ref = _make_source_record_ref(cp.source_locator)
    return ProtocolUnitResult(
        unit_id=unit_id, subject_ref=expanded.subject_ref,
        l1_disposition=L1Disposition.NOT_APPLICABLE,
        monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
        l0_status=L0CoverageStatus.NOT_APPLICABLE,
        source_record_refs=(src_ref,),
        protocol_locator_ids=(cp.source_locator.locator_id(),),
        eval_anchor_kind=window.eval_anchor_kind,
        window_start=window.window_start, window_end=window.window_end,
        precision=window.precision,
        endpoint_inclusivity=window.endpoint_inclusivity,
        evaluation_window_id=window_id,
        control_point_id=cp.control_point_id,
        evaluation_node_id=expanded.evaluation_node_id,
        signal_type=expanded.signal_type,
        protocol_version=expanded.applicability.protocol_version,
        amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)


def _missing_evidence_roles(
    *,
    expanded: ProtocolUnitExpanded,
    affected_component_ids: Sequence[str],
    bindings: Sequence[RuleEvidenceBinding],
    coverage: Mapping[str, bool],
) -> Tuple[str, ...]:
    """Semantic evidence roles required by the affected components that
    are absent or uncovered for this specific unit (§6.4).

    The role contract comes exclusively from the generated
    ``RuleEvidenceRequirement`` for each affected component -- never from
    a role list re-derived off the structured rule during evaluation.  A
    missing requirement fails closed.  Only real evidence roles are
    returned -- never reason codes, gap tokens or component ids.  A gap
    with no missing role (e.g. an ambiguous expression) returns an empty
    tuple.  ``coverage`` decides "uncovered": a role is missing when no
    identity-matched binding for the affected component carries it or the
    role's accepted-source coverage is not complete (unless the
    requirement explicitly waives completeness).
    """
    required: Set[str] = set()
    cp_id = (expanded.control_point.control_point_id
             if expanded.control_point is not None else "")
    for cid in affected_component_ids:
        requirement = _requirement_for_component(cid, expanded)
        matched_roles: Set[str] = {
            b.source_role for b in bindings
            if b.component_id == cid
            and b.control_point_id == cp_id
            and b.subject_ref == expanded.subject_ref
            and b.site_ref == expanded.site_ref
        }
        for role in requirement.required_evidence_roles:
            if role in matched_roles and (
                    coverage.get(role, False)
                    or not requirement.coverage_complete_required):
                continue
            required.add(role)
    return tuple(sorted(required))


def _materialize_unit(
    *, project_id: str, expanded: ProtocolUnitExpanded, unit_id: str,
    cp: ProtocolControlPoint, window: EvaluationWindowSpec, window_id: str,
    predicate: str, assessments: Tuple[ProtocolComponentAssessment, ...],
    outcomes: Tuple[ComponentConditionOutcome, ...],
    decisive_ids: Sequence[str], unresolved_ids: Sequence[str],
    rule_lineage: str, snapshot_id: str,
    enrollment_context: Optional[EnrollmentContext],
    priority_policy: Optional[D04PriorityPolicy],
    forced_reason: str = "",
    missing_evidence_roles: Sequence[str] = (),
) -> ProtocolUnitResult:
    """Materialize the final ProtocolUnitResult for one evaluation root
    (§6).  L0/L1 orthogonality: determinate L1 with unresolved component
    gaps keeps L0 partial + a coverage-gap notice; L1 not_evaluable
    carries zero candidate/risk/Query."""
    subtype = cp.positive_subtype()
    audience = SUBTYPE_LABELS[subtype]
    decisive = _canonical_sorted(decisive_ids)
    unresolved = _canonical_sorted(unresolved_ids)
    protocol_loc_ids = _canonical_sorted(
        (cp.source_locator.locator_id(),))

    # -- evidence aggregation ---------------------------------------------
    evidence: List[EvidenceItem] = []
    gap_codes: Set[str] = set()
    gaps: Set[str] = set()
    fact_parts: List[str] = []
    for outcome in outcomes:
        evidence.extend(outcome.supporting)
        evidence.extend(outcome.counterevidence)
        evidence.extend(outcome.context)
        gap_codes.update(outcome.gap_codes)
        gaps.update(outcome.gaps)
        if outcome.reason:
            fact_parts.append(outcome.reason)

    # -- source records ---------------------------------------------------
    # Every unique accepted evidence locator plus the protocol control-point
    # locator becomes a SourceRecordRef, deterministically deduplicated by
    # locator id.  Source/evidence/candidate/risk/Query counts stay separate
    # (§11).
    loc_by_id: Dict[str, SourceLocator] = {
        cp.source_locator.locator_id(): cp.source_locator}
    for ev in evidence:
        loc_by_id.setdefault(ev.locator.locator_id(), ev.locator)
    src_refs: List[SourceRecordRef] = [
        _make_source_record_ref(loc_by_id[lid])
        for lid in sorted(loc_by_id)]

    l0 = _l0_for(predicate=predicate, unresolved_ids=unresolved)

    if predicate == L1Disposition.NOT_APPLICABLE:
        return _not_applicable_unit(
            project_id=project_id, expanded=expanded, unit_id=unit_id,
            cp=cp, window_id=window_id, rule_lineage=rule_lineage,
            snapshot_id=snapshot_id)

    # -- coverage-gap notice ----------------------------------------------
    # ``missing_evidence_roles`` holds only real semantic evidence roles
    # (absent/uncovered for this unit); reason codes stay in
    # ``reason_code`` and unresolved component ids in
    # ``unresolved_component_ids`` -- never mixed into the role field
    # (§6.4, finding 2).
    notices: List[ProtocolCoverageGapNotice] = []
    if predicate == L1Disposition.NOT_EVALUABLE:
        reason_code = _primary_gap_code(gap_codes)
        notice = _gap_notice(
            unit_id=unit_id, reason_code=reason_code,
            missing_evidence_roles=tuple(
                _canonical_sorted(missing_evidence_roles)),
            protocol_locator_ids=protocol_loc_ids,
            reachable_source_locator_ids=tuple(sorted({
                ev.locator.locator_id() for ev in evidence})) or protocol_loc_ids,
            audience_text=(
                _GAP_LABELS.get(reason_code, "资料不足，暂无法核实")))
        notices.append(notice)
    elif predicate in (L1Disposition.POSITIVE, L1Disposition.NEGATIVE) \
            and unresolved:
        notice = _gap_notice(
            unit_id=unit_id, reason_code=GAP_COMPONENT_GAP_DETERMINATE,
            missing_evidence_roles=tuple(
                _canonical_sorted(missing_evidence_roles)),
            protocol_locator_ids=protocol_loc_ids,
            reachable_source_locator_ids=tuple(sorted({
                ev.locator.locator_id() for ev in evidence})) or protocol_loc_ids)
        notices.append(notice)

    # -- result per disposition -------------------------------------------
    if predicate == L1Disposition.NEGATIVE:
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.NEGATIVE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=l0, evidence=tuple(evidence),
            source_record_refs=tuple(src_refs),
            coverage_gap_notices=tuple(notices),
            component_assessments=assessments,
            decisive_component_ids=decisive,
            unresolved_component_ids=unresolved,
            protocol_locator_ids=protocol_loc_ids,
            eval_anchor_kind=window.eval_anchor_kind,
            window_start=window.window_start, window_end=window.window_end,
            precision=window.precision,
            endpoint_inclusivity=window.endpoint_inclusivity,
            evaluation_window_id=window_id,
            control_point_id=cp.control_point_id,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type,
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)

    if predicate == L1Disposition.BOUNDARY:
        # Boundary: a clue candidate (uncertainty preserved), no Query.
        priority = MONITORING_PRIORITY_UNKNOWN
        candidate, identity = _build_d04_candidate(
            project_id=project_id, subject_ref=expanded.subject_ref,
            site_ref=expanded.site_ref, control_point=cp,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type, window=window,
            plan=expanded.plan, applicability=expanded.applicability,
            snapshot_id=snapshot_id, monitoring_priority=priority,
            positive_subtype=subtype,
            audience_label=f"{audience}（边界）",
            match_reason="边界：真/假均可行，需进一步核实",
            decisive_component_ids=decisive,
            unresolved_component_ids=unresolved)
        cand_ref = RiskCandidateRef(
            candidate_id=candidate.candidate_id,
            risk_identity_id=identity.risk_identity_id,
            locator=cp.source_locator)
        marker = ProtocolRiskMarker(
            marker_id=f"marker-{unit_id}",
            risk_family=expanded.signal_type,
            audience_label=f"{audience}（边界）",
            monitoring_priority=priority,
            anchor_kind=window.eval_anchor_kind,
            anchor_start=window.window_start, anchor_end=window.window_end,
            date_precision=window.precision,
            unit_id=unit_id,
            candidate_or_risk_id=candidate.candidate_id,
            protocol_locator_ids=protocol_loc_ids,
            supporting_locator_ids=tuple(sorted({
                ev.locator.locator_id() for ev in evidence})),
            counterevidence_locator_ids=tuple(sorted({
                ev.locator.locator_id()
                for ev in outcomes
                for ev in ev.counterevidence})),
            coverage_gap=bool(unresolved))
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.BOUNDARY,
            monitoring_priority=priority, l0_status=l0,
            r2_candidates=(candidate,), risk_candidate_refs=(cand_ref,),
            evidence=tuple(evidence), source_record_refs=tuple(src_refs),
            coverage_gap_notices=tuple(notices),
            boundary_reason="边界：多个可行解释均有来源支持或阈值/端点未定义",
            audience_label=f"{audience}（边界）",
            component_assessments=assessments,
            decisive_component_ids=decisive,
            unresolved_component_ids=unresolved,
            journey_markers=(marker,),
            protocol_locator_ids=protocol_loc_ids,
            eval_anchor_kind=window.eval_anchor_kind,
            window_start=window.window_start, window_end=window.window_end,
            precision=window.precision,
            endpoint_inclusivity=window.endpoint_inclusivity,
            evaluation_window_id=window_id,
            control_point_id=cp.control_point_id,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type,
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)

    if predicate == L1Disposition.NOT_EVALUABLE:
        parts = [forced_reason] if forced_reason else []
        parts.extend(sorted(gaps))
        reason = "；".join(parts) if parts else "资料不足，暂无法核实"
        if forced_reason and not gaps:
            reason = forced_reason
        return ProtocolUnitResult(
            unit_id=unit_id, subject_ref=expanded.subject_ref,
            l1_disposition=L1Disposition.NOT_EVALUABLE,
            monitoring_priority=MONITORING_PRIORITY_UNKNOWN,
            l0_status=L0CoverageStatus.NOT_EVALUABLE,
            not_evaluable_reason=reason,
            evidence=tuple(evidence), source_record_refs=tuple(src_refs),
            coverage_gap_notices=tuple(notices),
            component_assessments=assessments,
            decisive_component_ids=decisive,
            unresolved_component_ids=unresolved,
            protocol_locator_ids=protocol_loc_ids,
            eval_anchor_kind=window.eval_anchor_kind,
            window_start=window.window_start, window_end=window.window_end,
            precision=window.precision,
            endpoint_inclusivity=window.endpoint_inclusivity,
            evaluation_window_id=window_id,
            control_point_id=cp.control_point_id,
            evaluation_node_id=expanded.evaluation_node_id,
            signal_type=expanded.signal_type,
            protocol_version=expanded.applicability.protocol_version,
            amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)

    # -- positive ---------------------------------------------------------
    if priority_policy is not None:
        priority = priority_policy.priority_for_subtype(subtype)
    else:
        priority = MONITORING_PRIORITY_UNKNOWN
    critical = (
        priority_policy.critical_for_subtype(subtype)
        if priority_policy is not None else False)
    close_forbidden = (
        priority_policy.machine_close_forbidden_for_subtype(subtype)
        if priority_policy is not None else False)
    candidate, identity = _build_d04_candidate(
        project_id=project_id, subject_ref=expanded.subject_ref,
        site_ref=expanded.site_ref, control_point=cp,
        evaluation_node_id=expanded.evaluation_node_id,
        signal_type=expanded.signal_type, window=window,
        plan=expanded.plan, applicability=expanded.applicability,
        snapshot_id=snapshot_id, monitoring_priority=priority,
        positive_subtype=subtype, audience_label=audience,
        match_reason="；".join(fact_parts) or "方案要求与已接受数据不一致",
        decisive_component_ids=decisive,
        unresolved_component_ids=unresolved,
        rights_or_safety_critical=critical,
        machine_close_forbidden=close_forbidden)
    cand_ref = RiskCandidateRef(
        candidate_id=candidate.candidate_id,
        risk_identity_id=identity.risk_identity_id,
        locator=cp.source_locator)

    ctx = enrollment_context
    if ctx is None:
        ctx = EnrollmentContext(
            subject_ref=expanded.subject_ref,
            query_context=QUERY_CONTEXT_UNRESOLVED,
            rationale="未提供入组情境，默认资料不足")
    query_loc_ids = _canonical_sorted({
        ref.locator.locator_id() for ref in src_refs
    } | {ev.locator.locator_id() for ev in evidence}
      | set(protocol_loc_ids))
    query = _build_query_ref(
        query_id=f"q-{unit_id}", unit_id=unit_id,
        subject_ref=expanded.subject_ref, subtype=subtype,
        control_point=cp, plan=expanded.plan,
        applicability=expanded.applicability, window=window,
        enrollment_context=ctx, decisive_ids=decisive,
        unresolved_ids=unresolved, finding_facts=fact_parts,
        candidate_id=candidate.candidate_id,
        source_locator_ids=query_loc_ids)
    marker = ProtocolRiskMarker(
        marker_id=f"marker-{unit_id}", risk_family=expanded.signal_type,
        audience_label=audience, monitoring_priority=priority,
        anchor_kind=window.eval_anchor_kind,
        anchor_start=window.window_start, anchor_end=window.window_end,
        date_precision=window.precision,
        unit_id=unit_id, candidate_or_risk_id=candidate.candidate_id,
        protocol_locator_ids=protocol_loc_ids,
        supporting_locator_ids=tuple(sorted({
            ev.locator.locator_id() for ev in evidence})),
        counterevidence_locator_ids=tuple(sorted({
            loc_id for outcome in outcomes
            for loc_id in (
                ev.locator.locator_id()
                for ev in outcome.counterevidence)})),
        query_ids=(query.query_id,),
        coverage_gap=bool(unresolved))
    return ProtocolUnitResult(
        unit_id=unit_id, subject_ref=expanded.subject_ref,
        l1_disposition=L1Disposition.POSITIVE,
        monitoring_priority=priority, l0_status=l0,
        r2_candidates=(candidate,), risk_candidate_refs=(cand_ref,),
        evidence=tuple(evidence), source_record_refs=tuple(src_refs),
        query_refs=(query,), coverage_gap_notices=tuple(notices),
        positive_subtype=subtype, audience_label=audience,
        query_context=ctx.query_context,
        decisive_component_ids=decisive,
        unresolved_component_ids=unresolved,
        component_assessments=assessments,
        journey_markers=(marker,),
        protocol_locator_ids=protocol_loc_ids,
        eval_anchor_kind=window.eval_anchor_kind,
        window_start=window.window_start, window_end=window.window_end,
        precision=window.precision,
        endpoint_inclusivity=window.endpoint_inclusivity,
        evaluation_window_id=window_id,
        control_point_id=cp.control_point_id,
        evaluation_node_id=expanded.evaluation_node_id,
        signal_type=expanded.signal_type,
        protocol_version=expanded.applicability.protocol_version,
        amendment_id_or_hash=expanded.applicability.amendment_id_or_hash)


def _l0_for(*, predicate: str, unresolved_ids: Sequence[str]) -> str:
    if predicate == L1Disposition.NOT_EVALUABLE:
        return L0CoverageStatus.NOT_EVALUABLE
    if predicate == L1Disposition.NOT_APPLICABLE:
        return L0CoverageStatus.NOT_APPLICABLE
    if predicate == L1Disposition.BOUNDARY:
        return L0CoverageStatus.PARTIAL
    if unresolved_ids:
        # Determinate L1 with an unresolved component gap: L0 partial,
        # domain completeness blocked (§6.1/§6.2).
        return L0CoverageStatus.PARTIAL
    return L0CoverageStatus.COVERED


def _primary_gap_code(gap_codes: Set[str]) -> str:
    if GAP_SOURCE_ROLE_NOT_COVERED in gap_codes:
        return GAP_SOURCE_ROLE_NOT_COVERED
    if GAP_RULE_NOT_VERIFIED in gap_codes:
        return GAP_RULE_NOT_VERIFIED
    if GAP_EXPRESSION_INCOMPLETE in gap_codes:
        return GAP_EXPRESSION_INCOMPLETE
    if gap_codes:
        return sorted(gap_codes)[0]
    return GAP_SOURCE_ROLE_NOT_COVERED


# ---------------------------------------------------------------------------
# Slice-level evaluation (§11)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolSliceResult:
    """Aggregate D04 result for one subject with separate counts."""

    subject_ref: str
    unit_results: Tuple[ProtocolUnitResult, ...]
    r2_candidates: Tuple[RiskCandidate, ...] = ()
    expected_set_hash: str = ""
    rule_lineage: str = ""
    delegated_control_points: Tuple[ProtocolDelegatedControlPoint, ...] = ()
    producer_references: Tuple[ProtocolProducerReference, ...] = ()
    expected_units: int = 0

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

    @property
    def coverage_gap_count(self) -> int:
        """Coverage-gap notices counted separately -- never in Query count
        (§11)."""
        return sum(len(r.coverage_gap_notices) for r in self.unit_results)

    @property
    def query_draft_count(self) -> int:
        return sum(len(r.query_refs) for r in self.unit_results)

    @property
    def candidate_count(self) -> int:
        return len(self.r2_candidates)

    @property
    def assigned_units(self) -> int:
        return len(self.unit_results)

    def verify_count_invariants(self) -> None:
        """expected_units = positive + negative + boundary + not_applicable
        + not_evaluable; each unit id appears exactly once (§11)."""
        total = (self.positive_count + self.negative_count
                 + self.boundary_count + self.not_applicable_count
                 + self.not_evaluable_count)
        if total != self.expected_units:
            raise ProtocolSliceError(
                f"count equation violated: sum(L1)={total} != "
                f"expected_units={self.expected_units}")
        if len(self.unit_results) != self.expected_units:
            raise ProtocolSliceError(
                "assigned unit results must equal expected_units")
        seen: Set[str] = set()
        for r in self.unit_results:
            if r.unit_id in seen:
                raise ProtocolSliceError(
                    f"duplicate unit id {r.unit_id!r} in slice result")
            seen.add(r.unit_id)


def evaluate_protocol_slice(
    *,
    project_id: str,
    applicability: ProtocolApplicabilityDecision,
    control_points: Sequence[ProtocolControlPoint],
    plan: ProtocolRuleEvaluationPlan,
    components: Optional[Mapping[str, ProtocolComponent]] = None,
    routing_records: Optional[Sequence[ProtocolControlRoutingRecord]] = None,
    window_by_control_point: Optional[Mapping[str, EvaluationWindowSpec]] = None,
    bindings: Sequence[RuleEvidenceBinding] = (),
    coverage_complete_roles: Optional[Mapping[str, bool]] = None,
    exceptions: Sequence[ProtocolExceptionBinding] = (),
    unit_conversion_rules: Sequence[UnitConversionRule] = (),
    retest_outcomes: Optional[Mapping[str, RetestOutcome]] = None,
    enrollment_context: Optional[EnrollmentContext] = None,
    priority_policy: Optional[D04PriorityPolicy] = None,
    producer_references: Sequence[ProtocolProducerReference] = (),
    snapshot_id: str = "",
) -> ProtocolSliceResult:
    """Evaluate the D04 slice for one subject (§11).

    Expands the expected set (routing first), evaluates every unit, and
    aggregates separate counts: the five L1 buckets, coverage-gap notices
    (never Query count), Query drafts (never risk count), candidates and
    delegated producer-owned control points.
    """
    expansion = expand_protocol_expected_set(
        project_id=project_id, applicability=applicability,
        control_points=control_points, plan=plan,
        components=components, routing_records=routing_records,
        window_by_control_point=window_by_control_point)
    results: List[ProtocolUnitResult] = []
    for expanded in expansion.units:
        results.append(evaluate_protocol_unit(
            project_id=project_id, expanded=expanded,
            bindings=bindings, coverage_complete_roles=coverage_complete_roles,
            exceptions=exceptions, unit_conversion_rules=unit_conversion_rules,
            retest_outcomes=retest_outcomes,
            enrollment_context=enrollment_context,
            priority_policy=priority_policy, snapshot_id=snapshot_id))
    all_cands: List[RiskCandidate] = []
    for r in results:
        all_cands.extend(r.r2_candidates)
    slice_result = ProtocolSliceResult(
        subject_ref=applicability.subject_ref,
        unit_results=tuple(results),
        r2_candidates=tuple(all_cands),
        expected_set_hash=expansion.expected_set_hash,
        rule_lineage=D04_RULE_LINEAGE_DEFAULT,
        delegated_control_points=expansion.delegated_control_points,
        producer_references=tuple(producer_references),
        expected_units=expansion.count)
    slice_result.verify_count_invariants()
    return slice_result
