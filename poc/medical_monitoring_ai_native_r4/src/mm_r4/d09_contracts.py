"""R4-D09 center pattern runtime -- typed contract and validation.

Implements the closed typed envelope of the frozen D09 v0.5 contract as
immutable dataclasses plus closed-enum validation.  This module is the
runtime kernel's data model.

Clean-semantics boundary (worker_01 follow-up, 2026-08-15):
  * The semantic modules never read audit/test metadata: ``mutation_context``
    and ``anti_overfit_variant`` are carried by this envelope as opaque
    schema only (the frozen catalog emits them); the evaluator must not read
    them and the static closure tests prove that.
  * No synthetic sentinel, substring or hash convention lives in the runtime:
    there is no missing-locator marker, no unresolvable-anchor substring
    convention and no revision-content hash recomputation convention.
    Locator resolution, anchor resolution, producer content verification,
    authority validity, method/comparability validity, Query redundancy,
    lifecycle carry-forward, rule/method supersession and site identity
    continuity must be explicit closed typed facts; where the frozen v1
    catalog does not carry them, the runtime leaves those decisions open
    (see the worker_01_followup1 gap matrix) instead of inferring them.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Frozen contract identity
# ---------------------------------------------------------------------------

D09_SCHEMA_VERSION = "1.0.0"
D09_TYPED_INPUT_SCHEMA = "d09-typed-input-v1"
D09_UNIT_ALGORITHM_VERSION = "d09_unit_v1"
D09_PUBLIC_IDENTITY_VERSION = "d09_public_v1"
D09_DOMAIN_ID = "D09_center_pattern"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------------------------
# Closed typed enumerations (contract sections 2.1/3.1/3.2/6/7)
# ---------------------------------------------------------------------------

D09_PATTERN_KINDS: Tuple[str, ...] = (
    "repeated_subject_risk",
    "systematic_data_or_process_gap",
    "within_site_time_trend",
)

# Non-medical pseudo-kinds carried by admission-rejected envelopes
# (routing-gate cases); they never enter the medical expected set.
D09_PSEUDO_KINDS: Tuple[str, ...] = ("routing_gate",)

D09_ACTIONS: Tuple[str, ...] = (
    "evaluate_and_own", "consume_only", "handoff_only", "context_only",
    "routing_gate",
)

D09_CLAIM_TOKENS: Tuple[str, ...] = (
    "d09_repeated_subject_risk",
    "d09_systematic_data_or_process_gap",
    "d09_within_site_time_trend",
    "d06_site_efficacy_rate",
    "d06_estimand",
    "d10_cross_site_outlier",
    "d10_treatment_arm_compare",
    "d10_project_trend",
    "d01_d08_individual_fact",
    "unresolved",
)

# Contract section 2.1: exactly the three ownable tokens may evaluate and own.
OWNED_CLAIM_TOKENS: frozenset = frozenset((
    "d09_repeated_subject_risk",
    "d09_systematic_data_or_process_gap",
    "d09_within_site_time_trend",
))

OWNED_KIND_CLAIM_TOKENS: Mapping[str, str] = {
    "repeated_subject_risk": "d09_repeated_subject_risk",
    "systematic_data_or_process_gap": "d09_systematic_data_or_process_gap",
    "within_site_time_trend": "d09_within_site_time_trend",
}

L1_DISPOSITIONS: Tuple[str, ...] = (
    "positive", "negative", "boundary", "not_applicable", "not_evaluable",
)

L0_STATUSES: Tuple[str, ...] = (
    "covered", "missing", "partial", "truncated", "not_evaluable", "failed",
)

L1_COMPLETENESS: Tuple[str, ...] = (
    "complete", "partial", "missing", "not_evaluable",
)

DENOMINATOR_KINDS: Tuple[str, ...] = (
    "enrolled_subjects", "treated_subjects", "evaluable_subjects",
    "subject_time", "exposure_time", "expected_assessment_opportunities",
)

DENOMINATOR_STATES: Tuple[str, ...] = (
    "closed_positive", "closed_zero", "unclosed",
)

DENOMINATOR_UNITS: Mapping[str, str] = {
    "enrolled_subjects": "subject",
    "treated_subjects": "subject",
    "evaluable_subjects": "subject",
    "subject_time": "subject_day",
    "exposure_time": "subject_day",
    "expected_assessment_opportunities": "opportunity",
}

OPPORTUNITY_STATES: Tuple[str, ...] = ("sufficient", "insufficient", "unknown")

# Contract section 6.2/15: accepted/versioned plan objects only; a raw
# listing enumeration or a conflicting D05 enumeration fails closed.
OPPORTUNITY_PROVENANCES: Tuple[str, ...] = (
    "accepted_d05_plan", "raw_listing_only", "enumeration_conflict",
)

CUTOFF_RELATIONS: Tuple[str, ...] = (
    "in_cutoff", "out_of_cutoff", "spans_cutoff", "time_missing_not_evaluable",
)

CUTOFF_IDENTITY_STATES: Tuple[str, ...] = ("consistent", "conflict")

ORIGIN_DECISIONS: Tuple[str, ...] = (
    "verified_same_origin", "distinct", "ambiguous", "wrong_scope",
    "not_evaluable",
)

STRATUM_ADMISSIONS: Tuple[str, ...] = ("admitted", "rejected_empty", "fanout_rejected")
STRATUM_STATES: Tuple[str, ...] = ("closed", "open", "empty")

WINDOW_KINDS: Tuple[str, ...] = (
    "calendar_interval", "study_day_interval", "subject_time_interval",
    "exposure_time_interval",
)

ANCHOR_KINDS: Tuple[str, ...] = (
    "calendar_date", "site_activation", "consent", "randomization",
    "first_dose", "domain_event",
)

INCLUSIVITIES: Tuple[str, ...] = (
    "both_inclusive", "left_inclusive", "right_inclusive", "exclusive",
)

WINDOW_STATES: Tuple[str, ...] = ("closed", "open")

CHANGE_KINDS: Tuple[str, ...] = ("increased", "decreased", "unchanged", "not_comparable")
CHANGE_CAUSES: Tuple[str, ...] = (
    "data", "denominator", "coverage", "rule_or_mapping", "method", "mixed",
)
COMPARABLE_STATES: Tuple[str, ...] = ("comparable", "boundary", "not_evaluable")

RATE_PROJECTION_STATES: Tuple[str, ...] = ("permitted", "suppressed", "qualified")
BLIND_STATUSES: Tuple[str, ...] = ("blinded", "unblinded_authorized")
MEMBER_KINDS: Tuple[str, ...] = ("subject_risk", "gap_opportunity", "change_ledger")

EXPECTED_SET_STATES: Tuple[str, ...] = (
    "admitted", "routed_consume_only", "routing_gate_unresolved",
    "global_admission_failed",
)

ADMISSION_GATE_KINDS: Tuple[str, ...] = (
    "legal_matrix_row_absent", "cartesian_definition_fanout", "global_integrity",
)

WINDOW_PAIR_GATE_STATES: Tuple[str, ...] = (
    "insufficient_windows", "incomparable_windows", "ready",
)

SCOPE_TYPES: Tuple[str, ...] = ("site", "subject", "shared_spine")
SCOPE_EQUALITY_DECISIONS: Tuple[str, ...] = ("exact_match", "equal", "unequal")

# Contract section 7.3 (closed clinical fact): blinded projects must not use
# treatment-group/treatment-role stratum keys; such keys are only admissible
# under an explicitly authorized unblinded analysis scope.
TREATMENT_STRATUM_KEYS: Tuple[str, ...] = ("treatment_arm", "treatment_role")

# Resolved domain facts (worker_01 corrective pass 2026-08-15): closed
# vocabulary for decisions the runtime must take from explicit typed facts
# rather than from test/audit metadata.
AUTHORITY_VALIDITY_STATES: Tuple[str, ...] = ("valid", "invalid")
METHOD_VALIDITY_STATES: Tuple[str, ...] = ("valid", "insufficient")
STATISTICAL_SIGNAL_ROLES: Tuple[str, ...] = ("none", "supporting", "sole_evidence")
MEMBER_EXPANSION_STATES: Tuple[str, ...] = ("expanded", "unexpandable", "not_applicable")
CARRY_FORWARD_STATES: Tuple[str, ...] = ("none", "active")
LINEAGE_RELATIONS: Tuple[str, ...] = (
    "none", "first_seen", "continued_from_data_revision",
    "continued_from_cutoff_advance", "superseded_by_rule_or_method_change",
)
SITE_IDENTITY_STATES: Tuple[str, ...] = ("stable", "merged", "split")
QUERY_REDUNDANCY_DECISIONS: Tuple[str, ...] = (
    "site_process_delta_present", "fully_covered_by_member_queries",
    "members_unlistable", "not_applicable",
)
SOURCE_VERIFICATION_STATES: Tuple[str, ...] = ("verified", "mismatch", "unverifiable")
LOCATOR_RESOLUTION_STATES: Tuple[str, ...] = ("locatable", "missing", "unresolvable")
ANCHOR_RESOLUTION_STATES: Tuple[str, ...] = ("resolved", "unresolved")


# ---------------------------------------------------------------------------
# Canonical serialization and content addressing (contract section 16)
# ---------------------------------------------------------------------------


def d09_normalize_nfc(value: Any) -> Any:
    """Recursively Unicode-NFC-normalize strings and dict keys."""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        return {d09_normalize_nfc(key): d09_normalize_nfc(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [d09_normalize_nfc(item) for item in value]
    if isinstance(value, tuple):
        return tuple(d09_normalize_nfc(item) for item in value)
    return value


def d09_canonical_json(value: Any) -> str:
    """Deterministic D09 canonical JSON (NFC, sorted keys, compact, no NaN)."""
    return json.dumps(
        d09_normalize_nfc(value), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    )


def d09_sha256_text(text: str) -> str:
    """SHA-256 of a UTF-8 encoded string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def d09_content_hash(value: Any) -> str:
    """Content address of any JSON-able value (hex sha256 of canonical JSON)."""
    return d09_sha256_text(d09_canonical_json(value))


def is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.match(value))


# ---------------------------------------------------------------------------
# Contract error and closed checks
# ---------------------------------------------------------------------------


class D09ContractError(Exception):
    """Closed-enum or required-field violation of a D09 typed object."""


def _check_closed(name: str, value: Any, allowed: Sequence[str]) -> str:
    if value not in allowed:
        raise D09ContractError(
            f"{name} must be one of {allowed!r}, got {value!r}")
    return value


def _check_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise D09ContractError(
            f"{name} must be a non-empty string, got {value!r}")
    return value


def _check_optional_str(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise D09ContractError(
            f"{name} must be a non-empty string or None, got {value!r}")
    return value


def _check_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise D09ContractError(f"{name} must be a bool, got {value!r}")
    return value


def _check_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise D09ContractError(f"{name} must be an int, got {value!r}")
    return value


def _check_nonneg_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise D09ContractError(
            f"{name} must be a non-negative int, got {value!r}")
    return value


def _check_positive_int(value: Any, name: str) -> int:
    value = _check_nonneg_int(value, name)
    if value < 1:
        raise D09ContractError(f"{name} must be >= 1, got {value!r}")
    return value


def _check_list(value: Any, name: str) -> List[Any]:
    if not isinstance(value, list):
        raise D09ContractError(f"{name} must be a list, got {value!r}")
    return value


def _check_str_tuple(value: Any, name: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise D09ContractError(f"{name} must be a list, got {value!r}")
    return tuple(_check_str(item, f"{name}[{index}]")
                 for index, item in enumerate(value))


def _check_hash(value: Any, name: str) -> str:
    if not is_sha256_hex(value):
        raise D09ContractError(f"{name} must be a 64-hex sha256, got {value!r}")
    return value


def _check_optional_hash(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_hash(value, name)


# ---------------------------------------------------------------------------
# Typed objects (full ``d09-typed-input-v1`` envelope)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScopeBinding:
    scope_binding_id: str
    scope_type: str = "site"
    scope_equality_decision: str = "exact_match"


@dataclass(frozen=True)
class PatternDefinition:
    pattern_definition_id: str
    pattern_kind: Optional[str]
    clinical_label_zh: str
    risk_domain: str
    clinical_claim_token: str
    d09_action: str
    required_producer_domains: Tuple[str, ...] = ()
    accepted_member_risk_kinds: Tuple[str, ...] = ()
    numerator_contract_id: str = ""
    allowed_denominator_kinds: Tuple[str, ...] = ()
    window_contract_id: str = ""
    stratum_contract_id: str = ""
    comparability_contract_id: str = ""
    positive_rule_ref: str = ""
    counterevidence_rule_refs: Tuple[str, ...] = ()
    monitoring_priority_rule_ref: str = ""
    center_query_policy_id: str = ""
    minimum_member_subject_count_ref: Optional[str] = None
    required_window_count_ref: Optional[str] = None
    opportunity_contract_id: Optional[str] = None
    authority_version: str = ""
    pattern_definition_content_hash: str = ""
    legal_definition_matrix_content_hash: str = ""
    numeric_execution_policy_content_hash: str = ""


@dataclass(frozen=True)
class AnalysisWindow:
    window_instance_id: str
    analysis_window_stable_id: str
    window_kind: str
    window_definition_id: str
    inclusivity: str
    anchor_kind: str
    computed_window_start: str
    computed_window_end: str
    cutoff_id: str
    scope_binding_stable_id: str
    window_state: str
    window_contract_content_hash: str


@dataclass(frozen=True)
class Stratum:
    stratum_contract_id: str
    stratum_contract_content_hash: str
    stratum_key: str
    stratum_state: str
    stratum_admission: str


@dataclass(frozen=True)
class CoverageStatus:
    producer_domain: str
    l0_status: str
    l1_medical_completeness_state: str
    accepted_current: bool = True
    coverage_locator_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class SubjectRiskMember:
    member_id: str
    subject_stable_id: str
    site_stable_id: str
    producer_domain: str
    risk_kind: str
    monitoring_priority: str
    public_r4_risk_identity: str
    source_event_identity: str
    event_time_ref: str
    cutoff_relation: str
    origin_decision: str
    member_kind: str = "subject_risk"
    source_locator_refs: Tuple[str, ...] = ()
    query_draft_refs: Tuple[str, ...] = ()
    source_locator_resolution_state: str = "locatable"


@dataclass(frozen=True)
class GapMember:
    member_id: str
    subject_stable_id: str
    site_stable_id: str
    producer_domain: str
    gap_kind: str
    gap_opportunity_id: str
    gap_definition_id: str
    normalized_field_or_process_identity: str
    obligation_or_opportunity_ref: str
    visit_or_time_anchor_refs: Tuple[str, ...] = ()
    cutoff_relation: str = "in_cutoff"
    member_kind: str = "gap_opportunity"
    source_locator_refs: Tuple[str, ...] = ()
    query_draft_refs: Tuple[str, ...] = ()
    source_locator_resolution_state: str = "locatable"
    anchor_resolution_state: str = "resolved"


@dataclass(frozen=True)
class ChangeLedgerMember:
    member_id: str
    subject_stable_id: str
    site_stable_id: str
    change_ledger_member_id: str
    current_window_instance_ref: str
    prior_window_instance_ref: str
    comparable_state: str
    change_kind: str
    change_cause: str
    unit: str
    producer_domain: str = "D09"
    member_kind: str = "change_ledger"
    absolute_delta: Optional[int] = None
    rate_delta: Optional[float] = None
    supporting_member_refs: Tuple[str, ...] = ()
    source_locator_refs: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Denominator:
    denominator_kind: str
    denominator_member_refs: Tuple[str, ...] = ()
    denominator_eligibility_rule_ref: str = ""
    denominator_excluded_member_refs: Tuple[str, ...] = ()
    exclusion_reason_codes: Tuple[str, ...] = ()
    denominator_value: int = 0
    denominator_unit: str = "subject"
    denominator_state: str = "closed_positive"


@dataclass(frozen=True)
class Opportunity:
    opportunity_definition_ref: str = ""
    expected_opportunity_refs: Tuple[str, ...] = ()
    expected_opportunity_count: int = 0
    observed_opportunity_refs: Tuple[str, ...] = ()
    observed_opportunity_count: int = 0
    missing_opportunity_refs: Tuple[str, ...] = ()
    opportunity_value: str = ""
    opportunity_unit: str = "opportunity"
    opportunity_state: str = "sufficient"
    opportunity_provenance: str = "accepted_d05_plan"


@dataclass(frozen=True)
class Cutoff:
    cutoff_id: str = ""
    cutoff_contract_id: str = ""
    snapshot_as_of: str = ""
    clinical_event_cutoff: str = ""
    cutoff_identity_state: str = "consistent"
    cutoff_policy_ref: str = ""


@dataclass(frozen=True)
class NumericPolicy:
    rate_numerator_kind: str = "unique_subject_count"
    rate_denominator_kind: str = "evaluable_subjects"
    scale: int = 3
    rounding_mode: str = "half_up"
    missing_zero_policy: str = "zero_is_observation"
    display_precision: int = 1
    time_unit: str = "day"
    exposure_unit: str = "subject_day"


@dataclass(frozen=True)
class VisibilityDecision:
    audience_scope_id: str
    blind_status: str = "blinded"
    evaluation_member_refs: Tuple[str, ...] = ()
    projectable_member_refs: Tuple[str, ...] = ()
    hidden_member_refs: Tuple[str, ...] = ()
    hidden_reason_codes: Tuple[str, ...] = ()
    visible_n: Optional[int] = None
    eligible_n: Optional[int] = None
    rate_projection_state: str = "permitted"


@dataclass(frozen=True)
class AdmissionGate:
    gate_kind: str
    reason_codes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ExpectedSet:
    expected_set_state: str = "admitted"
    admission_gate: Optional[AdmissionGate] = None


@dataclass(frozen=True)
class MutationContext:
    """Opaque audit/test metadata (frozen catalog emission).

    The semantic modules never read this object; it exists only so the
    test adapter can round-trip the frozen envelope byte-for-byte.
    """

    mutation_class: str = "none"
    desc: str = ""
    variant_id: Optional[str] = None
    base_fixture_id: Optional[str] = None


@dataclass(frozen=True)
class SurfaceChange:
    changed_token: str
    from_value: str
    to_value: str


@dataclass(frozen=True)
class AntiOverfitVariant:
    """Opaque audit/test metadata (frozen catalog emission); never read by
    the semantic modules."""

    variant_id: str
    base_fixture_id: str
    semantic_equivalence_ref: str = ""
    surface_changes: Tuple[SurfaceChange, ...] = ()


@dataclass(frozen=True)
class EvidenceRef:
    locator_id: str
    locator_kind: str
    source_file: str
    row_or_cell_ref: str
    lineage_ref: str


@dataclass(frozen=True)
class AudienceLexicon:
    affected_subjects_zh: str
    center_pattern_count_zh: str
    coverage_zh: str
    event_count_zh: str
    individual_risk_count_zh: str
    pattern_label_zh: str
    disposition_zh: Mapping[str, str] = field(default_factory=dict)
    lifecycle_zh: Mapping[str, str] = field(default_factory=dict)
    forbidden_internal_terms: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolvedAuthorityDecision:
    """Resolved authority facts (contract sections 3.2/9): the resolved
    minimum-member threshold, closed authority validity state and refs."""

    minimum_member_subject_count: Optional[int]
    gap_positive_minimum_opportunity_count: Optional[int]
    trend_positive_minimum_subject_count: Optional[int]
    authority_validity_state: str
    authority_ref: str
    authority_locator_ref: str
    mode_contract_version: str
    authority_content_hash: str


@dataclass(frozen=True)
class MethodComparabilityDecision:
    """Resolved method/comparability facts (contract sections 7.3/9): method
    validity, statistical-signal role and member expansion, and the
    per-window rule/method version refs that make a trend pair comparable."""

    method_validity_state: str = "valid"
    statistical_signal_role: str = "none"
    member_expansion_state: str = "not_applicable"
    window_rule_version_refs: Tuple[str, ...] = ()
    stratum_method_version_refs: Tuple[str, ...] = ()


@dataclass(frozen=True)
class LineageContext:
    """Lineage facts (contract sections 5.1/8.2/10/13): prior D09 risk
    instance, carry-forward state, lineage relation and site identity
    continuity."""

    prior_risk_instance_ref: Optional[str] = None
    prior_public_risk_identity_ref: Optional[str] = None
    carry_forward_state: str = "none"
    lineage_relation: str = "none"
    site_identity_state: str = "stable"


@dataclass(frozen=True)
class CenterQueryPolicy:
    """Versioned ModeContract Query policy (contract section 12)."""

    policy_id: str
    mode_contract_version: str
    max_query_member_fanout: int
    member_order_policy: str
    redundancy_rule_ref: str
    allowed_action_kinds: Tuple[str, ...]
    pd_wording_rule_ref: str
    content_hash: str
    effective_interval: str


@dataclass(frozen=True)
class QueryRedundancyDecision:
    """Resolved Query redundancy decision (contract section 12): closed
    decision, resolved fanout limit and the member-set coverage proof."""

    decision: str
    max_query_member_fanout: int
    unit_member_set_hash: str = ""
    covered_member_refs: Tuple[str, ...] = ()
    uncovered_member_refs: Tuple[str, ...] = ()
    member_query_refs: Tuple[str, ...] = ()
    coverage_proof_hash: str = ""


@dataclass(frozen=True)
class SourceVerificationRecord:
    """Producer source-verification record (contract section 4): revision,
    declared vs verified content hash and the closed verification state."""

    revision: str
    declared_content_hash: str
    verified_content_hash: str
    verification_state: str = "verified"


@dataclass(frozen=True)
class D09TypedInput:
    """Complete typed bundle for one D09 evaluation (``d09-typed-input-v1``)."""

    envelope_id: str
    input_schema: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    source_revision_set: Tuple[str, ...]
    source_content_hashes: Tuple[str, ...]
    site_stable_id: str
    resolved_authority_decision: ResolvedAuthorityDecision
    method_comparability_decision: MethodComparabilityDecision
    lineage_context: LineageContext
    center_query_policy: CenterQueryPolicy
    query_redundancy_decision: QueryRedundancyDecision
    source_verification_records: Tuple[SourceVerificationRecord, ...]
    scope_binding: ScopeBinding
    pattern_definition: PatternDefinition
    mode_contract_version: str
    matched_counterevidence_rule_refs: Tuple[str, ...]
    mode_contract_design_clause_ref: Optional[str]
    analysis_windows: Tuple[AnalysisWindow, ...]
    stratum: Stratum
    coverage: Tuple[CoverageStatus, ...]
    subject_risk_members: Tuple[SubjectRiskMember, ...]
    gap_members: Tuple[GapMember, ...]
    change_ledger_members: Tuple[ChangeLedgerMember, ...]
    denominator: Denominator
    opportunity: Opportunity
    cutoff: Cutoff
    numeric_policy: NumericPolicy
    visibility_decision: VisibilityDecision
    expected_set: ExpectedSet
    mutation_context: MutationContext
    anti_overfit_variant: Optional[AntiOverfitVariant]
    evidence_refs: Tuple[EvidenceRef, ...]
    audience_lexicon: AudienceLexicon


# ---------------------------------------------------------------------------
# Result types (typed outputs; worker_02 consumes these for projection)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class D09UnitResult:
    """One medical expected-set unit (contract section 9 five dispositions)."""

    stable_core: str
    l1_disposition: str
    pattern_kind: str
    primary_reason: str
    participant_count: int
    event_count: int
    gap_opportunity_count: int
    individual_risk_count: int
    risk_count: int
    clue_count: int
    query_count: int
    evidence_count: int
    counterevidence_count: int
    lineage_handoff: bool
    unit_kind: str = "d09_pattern_unit"
    gate_signal_type: Optional[str] = None


@dataclass(frozen=True)
class D09TraceEdge:
    """One typed member->source binding edge (contract sections 10/14).

    ``edge_index`` is a deterministic 1-based ordinal over the sorted
    member/locator pairs of the run; renderers may map it onto their own
    identity vocabulary.  ``member_ref`` is the member object ref and
    ``locator_ref`` its first source locator.
    """

    edge_index: int
    member_ref: str
    locator_ref: str


@dataclass(frozen=True)
class D09RunResult:
    """Complete deterministic outcome of one typed run."""

    typed: D09TypedInput
    disposition: str
    primary_reason: str
    integrity_stage: str
    admission_gate_kind: Optional[str]
    window_pair_gate_present: bool
    window_pair_state: Optional[str]
    gate_count: int
    open_gate_count: int
    owner_domain: str
    d09_action: str
    l0_complete: bool
    domain_complete: bool
    unit_count: int
    positive_count: int
    negative_count: int
    boundary_count: int
    not_applicable_count: int
    not_evaluable_count: int
    individual_risk_count: int
    affected_subject_count: int
    event_count: int
    gap_opportunity_count: int
    center_pattern_count: int
    clue_count: int
    query_count: int
    risk_count: int
    source_record_count: int
    denominator_kind: str
    denominator_value: int
    denominator_state: str
    opportunity_expected: int
    opportunity_observed: int
    opportunity_missing: int
    opportunity_state: str
    downstream_handoff: bool
    handoff_target_domain: Optional[str]
    superseded_unit_count: int
    journey_marker_present: bool
    all_members_locatable: bool
    units: Tuple[D09UnitResult, ...] = ()
    trace_edges: Tuple[D09TraceEdge, ...] = ()
    evidence_locators: Tuple[str, ...] = ()
    member_pairs: Tuple[Tuple[str, str], ...] = ()
    hidden_member_refs: Tuple[str, ...] = ()
    producer_binding_ids: Tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Per-object validation
# ---------------------------------------------------------------------------


def _validate_scope_binding(binding: Any, name: str) -> None:
    if not isinstance(binding, ScopeBinding):
        raise D09ContractError(f"{name} must be a ScopeBinding")
    _check_str(binding.scope_binding_id, f"{name}.scope_binding_id")
    _check_closed(f"{name}.scope_type", binding.scope_type, SCOPE_TYPES)
    _check_closed(f"{name}.scope_equality_decision",
                  binding.scope_equality_decision, SCOPE_EQUALITY_DECISIONS)


def _validate_pattern_definition(definition: Any, name: str) -> None:
    if not isinstance(definition, PatternDefinition):
        raise D09ContractError(f"{name} must be a PatternDefinition")
    _check_str(definition.pattern_definition_id, f"{name}.pattern_definition_id")
    if definition.pattern_kind is not None:
        allowed = D09_PATTERN_KINDS + D09_PSEUDO_KINDS
        _check_closed(f"{name}.pattern_kind", definition.pattern_kind, allowed)
    _check_str(definition.risk_domain, f"{name}.risk_domain")
    _check_closed(f"{name}.clinical_claim_token", definition.clinical_claim_token,
                  D09_CLAIM_TOKENS)
    _check_closed(f"{name}.d09_action", definition.d09_action, D09_ACTIONS)
    for index, domain in enumerate(definition.required_producer_domains):
        _check_str(domain, f"{name}.required_producer_domains[{index}]")
    for index, kind in enumerate(definition.accepted_member_risk_kinds):
        _check_str(kind, f"{name}.accepted_member_risk_kinds[{index}]")
    for index, kind in enumerate(definition.allowed_denominator_kinds):
        _check_closed(f"{name}.allowed_denominator_kinds[{index}]", kind,
                      DENOMINATOR_KINDS)
    _check_hash(definition.pattern_definition_content_hash,
                f"{name}.pattern_definition_content_hash")
    _check_hash(definition.legal_definition_matrix_content_hash,
                f"{name}.legal_definition_matrix_content_hash")
    _check_hash(definition.numeric_execution_policy_content_hash,
                f"{name}.numeric_execution_policy_content_hash")


def _validate_window(window: Any, index: int) -> None:
    name = f"analysis_windows[{index}]"
    if not isinstance(window, AnalysisWindow):
        raise D09ContractError(f"{name} must be an AnalysisWindow")
    _check_str(window.window_instance_id, f"{name}.window_instance_id")
    _check_str(window.analysis_window_stable_id, f"{name}.analysis_window_stable_id")
    _check_closed(f"{name}.window_kind", window.window_kind, WINDOW_KINDS)
    _check_closed(f"{name}.anchor_kind", window.anchor_kind, ANCHOR_KINDS)
    _check_closed(f"{name}.inclusivity", window.inclusivity, INCLUSIVITIES)
    _check_closed(f"{name}.window_state", window.window_state, WINDOW_STATES)
    _check_hash(window.window_contract_content_hash,
                f"{name}.window_contract_content_hash")


def _validate_stratum(stratum: Any, name: str) -> None:
    if not isinstance(stratum, Stratum):
        raise D09ContractError(f"{name} must be a Stratum")
    _check_str(stratum.stratum_key, f"{name}.stratum_key")
    _check_closed(f"{name}.stratum_state", stratum.stratum_state, STRATUM_STATES)
    _check_closed(f"{name}.stratum_admission", stratum.stratum_admission,
                  STRATUM_ADMISSIONS)
    _check_hash(stratum.stratum_contract_content_hash,
                f"{name}.stratum_contract_content_hash")


def _validate_coverage(coverage: Any, index: int) -> None:
    name = f"coverage[{index}]"
    if not isinstance(coverage, CoverageStatus):
        raise D09ContractError(f"{name} must be a CoverageStatus")
    _check_str(coverage.producer_domain, f"{name}.producer_domain")
    _check_closed(f"{name}.l0_status", coverage.l0_status, L0_STATUSES)
    _check_closed(f"{name}.l1_medical_completeness_state",
                  coverage.l1_medical_completeness_state, L1_COMPLETENESS)
    _check_bool(coverage.accepted_current, f"{name}.accepted_current")
    _check_str_tuple(coverage.coverage_locator_ids, f"{name}.coverage_locator_ids")


def _validate_risk_member(member: Any, index: int) -> None:
    name = f"subject_risk_members[{index}]"
    if not isinstance(member, SubjectRiskMember):
        raise D09ContractError(f"{name} must be a SubjectRiskMember")
    _check_closed(f"{name}.member_kind", member.member_kind, MEMBER_KINDS)
    _check_str(member.member_id, f"{name}.member_id")
    _check_str(member.subject_stable_id, f"{name}.subject_stable_id")
    _check_str(member.site_stable_id, f"{name}.site_stable_id")
    _check_str(member.risk_kind, f"{name}.risk_kind")
    _check_str(member.public_r4_risk_identity, f"{name}.public_r4_risk_identity")
    _check_str(member.source_event_identity, f"{name}.source_event_identity")
    _check_closed(f"{name}.cutoff_relation", member.cutoff_relation,
                  CUTOFF_RELATIONS)
    _check_closed(f"{name}.origin_decision", member.origin_decision,
                  ORIGIN_DECISIONS)
    _check_closed(f"{name}.source_locator_resolution_state",
                  member.source_locator_resolution_state, LOCATOR_RESOLUTION_STATES)


def _validate_gap_member(member: Any, index: int) -> None:
    name = f"gap_members[{index}]"
    if not isinstance(member, GapMember):
        raise D09ContractError(f"{name} must be a GapMember")
    _check_closed(f"{name}.member_kind", member.member_kind, MEMBER_KINDS)
    _check_str(member.member_id, f"{name}.member_id")
    _check_str(member.subject_stable_id, f"{name}.subject_stable_id")
    _check_str(member.gap_opportunity_id, f"{name}.gap_opportunity_id")
    _check_str(member.gap_definition_id, f"{name}.gap_definition_id")
    _check_str(member.normalized_field_or_process_identity,
               f"{name}.normalized_field_or_process_identity")
    _check_str(member.obligation_or_opportunity_ref,
               f"{name}.obligation_or_opportunity_ref")
    _check_closed(f"{name}.cutoff_relation", member.cutoff_relation,
                  CUTOFF_RELATIONS)
    for index_anchor, anchor in enumerate(member.visit_or_time_anchor_refs):
        _check_str(anchor, f"{name}.visit_or_time_anchor_refs[{index_anchor}]")
    _check_closed(f"{name}.source_locator_resolution_state",
                  member.source_locator_resolution_state, LOCATOR_RESOLUTION_STATES)
    _check_closed(f"{name}.anchor_resolution_state",
                  member.anchor_resolution_state, ANCHOR_RESOLUTION_STATES)


def _validate_change_member(member: Any, index: int) -> None:
    name = f"change_ledger_members[{index}]"
    if not isinstance(member, ChangeLedgerMember):
        raise D09ContractError(f"{name} must be a ChangeLedgerMember")
    _check_closed(f"{name}.member_kind", member.member_kind, MEMBER_KINDS)
    _check_str(member.member_id, f"{name}.member_id")
    _check_str(member.subject_stable_id, f"{name}.subject_stable_id")
    _check_str(member.change_ledger_member_id, f"{name}.change_ledger_member_id")
    _check_closed(f"{name}.comparable_state", member.comparable_state,
                  COMPARABLE_STATES)
    _check_closed(f"{name}.change_kind", member.change_kind, CHANGE_KINDS)
    _check_closed(f"{name}.change_cause", member.change_cause, CHANGE_CAUSES)


def _validate_denominator(denominator: Any, name: str) -> None:
    if not isinstance(denominator, Denominator):
        raise D09ContractError(f"{name} must be a Denominator")
    _check_closed(f"{name}.denominator_kind", denominator.denominator_kind,
                  DENOMINATOR_KINDS)
    _check_closed(f"{name}.denominator_state", denominator.denominator_state,
                  DENOMINATOR_STATES)
    _check_nonneg_int(denominator.denominator_value, f"{name}.denominator_value")
    _check_str_tuple(denominator.denominator_member_refs,
                     f"{name}.denominator_member_refs")
    _check_str_tuple(denominator.denominator_excluded_member_refs,
                     f"{name}.denominator_excluded_member_refs")


def _validate_opportunity(opportunity: Any, name: str) -> None:
    if not isinstance(opportunity, Opportunity):
        raise D09ContractError(f"{name} must be an Opportunity")
    _check_nonneg_int(opportunity.expected_opportunity_count,
                      f"{name}.expected_opportunity_count")
    _check_nonneg_int(opportunity.observed_opportunity_count,
                      f"{name}.observed_opportunity_count")
    _check_closed(f"{name}.opportunity_state", opportunity.opportunity_state,
                  OPPORTUNITY_STATES)
    _check_closed(f"{name}.opportunity_provenance",
                  opportunity.opportunity_provenance, OPPORTUNITY_PROVENANCES)


def _validate_cutoff(cutoff: Any, name: str) -> None:
    if not isinstance(cutoff, Cutoff):
        raise D09ContractError(f"{name} must be a Cutoff")
    _check_closed(f"{name}.cutoff_identity_state", cutoff.cutoff_identity_state,
                  CUTOFF_IDENTITY_STATES)


def _validate_numeric_policy(policy: Any, name: str) -> None:
    if not isinstance(policy, NumericPolicy):
        raise D09ContractError(f"{name} must be a NumericPolicy")
    _check_nonneg_int(policy.scale, f"{name}.scale")
    _check_nonneg_int(policy.display_precision, f"{name}.display_precision")


def _validate_visibility(visibility: Any, name: str) -> None:
    if not isinstance(visibility, VisibilityDecision):
        raise D09ContractError(f"{name} must be a VisibilityDecision")
    _check_str(visibility.audience_scope_id, f"{name}.audience_scope_id")
    _check_closed(f"{name}.blind_status", visibility.blind_status, BLIND_STATUSES)
    _check_closed(f"{name}.rate_projection_state",
                  visibility.rate_projection_state, RATE_PROJECTION_STATES)
    if visibility.visible_n is not None:
        _check_nonneg_int(visibility.visible_n, f"{name}.visible_n")
    if visibility.eligible_n is not None:
        _check_nonneg_int(visibility.eligible_n, f"{name}.eligible_n")


def _validate_expected_set(expected_set: Any, name: str) -> None:
    if not isinstance(expected_set, ExpectedSet):
        raise D09ContractError(f"{name} must be an ExpectedSet")
    _check_closed(f"{name}.expected_set_state", expected_set.expected_set_state,
                  EXPECTED_SET_STATES)
    gate = expected_set.admission_gate
    if gate is not None:
        if not isinstance(gate, AdmissionGate):
            raise D09ContractError(f"{name}.admission_gate must be an AdmissionGate")
        _check_closed(f"{name}.admission_gate.gate_kind", gate.gate_kind,
                      ADMISSION_GATE_KINDS)


def _validate_mutation_context(context: Any, name: str) -> None:
    """Shape-only validation: the mutation context is opaque audit metadata
    that the semantic modules never read (closed vocabulary is test-side)."""
    if not isinstance(context, MutationContext):
        raise D09ContractError(f"{name} must be a MutationContext")
    _check_str(context.mutation_class, f"{name}.mutation_class")
    if not isinstance(context.desc, str):
        raise D09ContractError(f"{name}.desc must be a str")
    _check_optional_str(context.variant_id, f"{name}.variant_id")
    _check_optional_str(context.base_fixture_id, f"{name}.base_fixture_id")


def _validate_lexicon(lexicon: Any, name: str) -> None:
    if not isinstance(lexicon, AudienceLexicon):
        raise D09ContractError(f"{name} must be an AudienceLexicon")
    _check_str(lexicon.pattern_label_zh, f"{name}.pattern_label_zh")


def _validate_resolved_authority(decision: Any, name: str) -> None:
    if not isinstance(decision, ResolvedAuthorityDecision):
        raise D09ContractError(f"{name} must be a ResolvedAuthorityDecision")
    if decision.minimum_member_subject_count is not None:
        _check_nonneg_int(decision.minimum_member_subject_count,
                          f"{name}.minimum_member_subject_count")
    if decision.gap_positive_minimum_opportunity_count is not None:
        _check_positive_int(decision.gap_positive_minimum_opportunity_count,
                            f"{name}.gap_positive_minimum_opportunity_count")
    if decision.trend_positive_minimum_subject_count is not None:
        _check_positive_int(decision.trend_positive_minimum_subject_count,
                            f"{name}.trend_positive_minimum_subject_count")
    _check_closed(f"{name}.authority_validity_state",
                  decision.authority_validity_state, AUTHORITY_VALIDITY_STATES)
    _check_str(decision.authority_ref, f"{name}.authority_ref")
    _check_str(decision.authority_locator_ref, f"{name}.authority_locator_ref")
    _check_str(decision.mode_contract_version, f"{name}.mode_contract_version")
    _check_hash(decision.authority_content_hash,
                f"{name}.authority_content_hash")
    expected_hash = d09_content_hash({
        "authority_ref": decision.authority_ref,
        "mode_contract_version": decision.mode_contract_version,
        "minimum_member_subject_count": decision.minimum_member_subject_count,
        "gap_positive_minimum_opportunity_count": (
            decision.gap_positive_minimum_opportunity_count),
        "trend_positive_minimum_subject_count": (
            decision.trend_positive_minimum_subject_count),
    })
    if decision.authority_content_hash != expected_hash:
        raise D09ContractError(f"{name}.authority_content_hash mismatch")


def _validate_method_comparability(decision: Any, name: str) -> None:
    if not isinstance(decision, MethodComparabilityDecision):
        raise D09ContractError(f"{name} must be a MethodComparabilityDecision")
    _check_closed(f"{name}.method_validity_state", decision.method_validity_state,
                  METHOD_VALIDITY_STATES)
    _check_closed(f"{name}.statistical_signal_role",
                  decision.statistical_signal_role, STATISTICAL_SIGNAL_ROLES)
    _check_closed(f"{name}.member_expansion_state",
                  decision.member_expansion_state, MEMBER_EXPANSION_STATES)
    _check_str_tuple(decision.window_rule_version_refs,
                     f"{name}.window_rule_version_refs")
    _check_str_tuple(decision.stratum_method_version_refs,
                     f"{name}.stratum_method_version_refs")


def _validate_lineage_context(context: Any, name: str) -> None:
    if not isinstance(context, LineageContext):
        raise D09ContractError(f"{name} must be a LineageContext")
    _check_optional_str(context.prior_risk_instance_ref,
                        f"{name}.prior_risk_instance_ref")
    _check_optional_str(context.prior_public_risk_identity_ref,
                        f"{name}.prior_public_risk_identity_ref")
    _check_closed(f"{name}.carry_forward_state", context.carry_forward_state,
                  CARRY_FORWARD_STATES)
    _check_closed(f"{name}.lineage_relation", context.lineage_relation,
                  LINEAGE_RELATIONS)
    _check_closed(f"{name}.site_identity_state", context.site_identity_state,
                  SITE_IDENTITY_STATES)


def _validate_center_query_policy(policy: Any, name: str) -> None:
    if not isinstance(policy, CenterQueryPolicy):
        raise D09ContractError(f"{name} must be a CenterQueryPolicy")
    _check_str(policy.policy_id, f"{name}.policy_id")
    _check_str(policy.mode_contract_version, f"{name}.mode_contract_version")
    _check_positive_int(policy.max_query_member_fanout,
                        f"{name}.max_query_member_fanout")
    _check_str(policy.member_order_policy, f"{name}.member_order_policy")
    _check_str(policy.redundancy_rule_ref, f"{name}.redundancy_rule_ref")
    _check_str_tuple(policy.allowed_action_kinds,
                     f"{name}.allowed_action_kinds")
    if not policy.allowed_action_kinds:
        raise D09ContractError(f"{name}.allowed_action_kinds must be non-empty")
    _check_str(policy.pd_wording_rule_ref, f"{name}.pd_wording_rule_ref")
    _check_str(policy.effective_interval, f"{name}.effective_interval")
    _check_hash(policy.content_hash, f"{name}.content_hash")
    expected_hash = d09_content_hash({
        "policy_id": policy.policy_id,
        "mode_contract_version": policy.mode_contract_version,
        "max_query_member_fanout": policy.max_query_member_fanout,
        "member_order_policy": policy.member_order_policy,
        "redundancy_rule_ref": policy.redundancy_rule_ref,
        "allowed_action_kinds": list(policy.allowed_action_kinds),
        "pd_wording_rule_ref": policy.pd_wording_rule_ref,
        "effective_interval": policy.effective_interval,
    })
    if policy.content_hash != expected_hash:
        raise D09ContractError(f"{name}.content_hash mismatch")


def _validate_query_redundancy(decision: Any, name: str) -> None:
    if not isinstance(decision, QueryRedundancyDecision):
        raise D09ContractError(f"{name} must be a QueryRedundancyDecision")
    _check_closed(f"{name}.decision", decision.decision,
                  QUERY_REDUNDANCY_DECISIONS)
    _check_positive_int(decision.max_query_member_fanout,
                        f"{name}.max_query_member_fanout")
    _check_hash(decision.unit_member_set_hash, f"{name}.unit_member_set_hash")
    _check_str_tuple(decision.covered_member_refs, f"{name}.covered_member_refs")
    _check_str_tuple(decision.uncovered_member_refs, f"{name}.uncovered_member_refs")
    _check_str_tuple(decision.member_query_refs, f"{name}.member_query_refs")
    _check_hash(decision.coverage_proof_hash, f"{name}.coverage_proof_hash")


def validate_typed_input(typed: D09TypedInput) -> None:
    """Closed validation of a parsed typed bundle.

    Raises ``D09ContractError`` on the first closed-enum or required-field
    violation.  Runtime evaluation must never run on an invalid envelope.
    """
    if not isinstance(typed, D09TypedInput):
        raise D09ContractError("typed must be a D09TypedInput")
    if typed.input_schema != D09_TYPED_INPUT_SCHEMA:
        raise D09ContractError(
            f"input_schema must be {D09_TYPED_INPUT_SCHEMA!r}, got {typed.input_schema!r}")
    _check_str(typed.envelope_id, "envelope_id")
    _check_str(typed.project_ref, "project_ref")
    _check_str(typed.run_ref, "run_ref")
    _check_str(typed.snapshot_ref, "snapshot_ref")
    _check_str(typed.site_stable_id, "site_stable_id")
    _check_str(typed.mode_contract_version, "mode_contract_version")
    _check_str_tuple(typed.source_revision_set, "source_revision_set")
    _check_str_tuple(typed.source_content_hashes, "source_content_hashes")
    for index, value in enumerate(typed.source_content_hashes):
        _check_hash(value, f"source_content_hashes[{index}]")
    if len(typed.source_revision_set) != len(typed.source_content_hashes):
        raise D09ContractError(
            "source_revision_set and source_content_hashes must have equal length")
    if not typed.source_revision_set:
        raise D09ContractError("source revision/hash set must be non-empty")
    _validate_scope_binding(typed.scope_binding, "scope_binding")
    _validate_pattern_definition(typed.pattern_definition, "pattern_definition")
    _check_str_tuple(typed.matched_counterevidence_rule_refs,
                     "matched_counterevidence_rule_refs")
    _check_optional_str(typed.mode_contract_design_clause_ref,
                        "mode_contract_design_clause_ref")
    for index, window in enumerate(typed.analysis_windows):
        _validate_window(window, index)
    _validate_stratum(typed.stratum, "stratum")
    for index, coverage in enumerate(typed.coverage):
        _validate_coverage(coverage, index)
    for index, member in enumerate(typed.subject_risk_members):
        _validate_risk_member(member, index)
    for index, member in enumerate(typed.gap_members):
        _validate_gap_member(member, index)
    for index, member in enumerate(typed.change_ledger_members):
        _validate_change_member(member, index)
    _validate_denominator(typed.denominator, "denominator")
    _validate_opportunity(typed.opportunity, "opportunity")
    _validate_cutoff(typed.cutoff, "cutoff")
    _validate_visibility(typed.visibility_decision, "visibility_decision")
    _validate_expected_set(typed.expected_set, "expected_set")
    _validate_mutation_context(typed.mutation_context, "mutation_context")
    _validate_resolved_authority(typed.resolved_authority_decision,
                                 "resolved_authority_decision")
    _validate_method_comparability(typed.method_comparability_decision,
                                   "method_comparability_decision")
    _validate_lineage_context(typed.lineage_context, "lineage_context")
    _validate_center_query_policy(typed.center_query_policy,
                                  "center_query_policy")
    _validate_query_redundancy(typed.query_redundancy_decision,
                               "query_redundancy_decision")
    definition = typed.pattern_definition
    expected_state = typed.expected_set.expected_set_state
    if expected_state == "admitted":
        expected_token = OWNED_KIND_CLAIM_TOKENS.get(definition.pattern_kind)
        if expected_token is None:
            raise D09ContractError(
                "admitted D09 input requires an ownable pattern kind")
        if definition.clinical_claim_token != expected_token:
            raise D09ContractError(
                "admitted D09 claim token must match its pattern kind")
        if definition.d09_action != "evaluate_and_own":
            raise D09ContractError(
                "admitted D09 input requires evaluate_and_own")
    elif expected_state == "routed_consume_only":
        if (definition.clinical_claim_token in OWNED_CLAIM_TOKENS
                or definition.d09_action != "consume_only"):
            raise D09ContractError(
                "consume-only routing requires a foreign claim token and action")
    elif expected_state == "routing_gate_unresolved":
        if (definition.pattern_kind != "routing_gate"
                or definition.clinical_claim_token != "unresolved"
                or definition.d09_action != "routing_gate"):
            raise D09ContractError(
                "unresolved routing gate requires the exact gate token/action")

    if expected_state == "admitted":
        if definition.pattern_kind == "repeated_subject_risk":
            accepted = set(definition.accepted_member_risk_kinds)
            for member in typed.subject_risk_members:
                if member.member_kind != "subject_risk":
                    raise D09ContractError("subject-risk member kind mismatch")
                if member.site_stable_id != typed.site_stable_id:
                    raise D09ContractError("subject-risk member site mismatch")
                if member.risk_kind not in accepted:
                    raise D09ContractError("subject-risk kind is not accepted")
        elif definition.pattern_kind == "systematic_data_or_process_gap":
            for member in typed.gap_members:
                if member.member_kind != "gap_opportunity":
                    raise D09ContractError("gap member kind mismatch")
                if member.site_stable_id != typed.site_stable_id:
                    raise D09ContractError("gap member site mismatch")
        elif definition.pattern_kind == "within_site_time_trend":
            for member in typed.change_ledger_members:
                if member.member_kind != "change_ledger":
                    raise D09ContractError("change-ledger member kind mismatch")
                if member.site_stable_id != typed.site_stable_id:
                    raise D09ContractError("change-ledger member site mismatch")
    authority = typed.resolved_authority_decision
    if authority.mode_contract_version != typed.mode_contract_version:
        raise D09ContractError(
            "resolved_authority_decision.mode_contract_version mismatch")
    kind = typed.pattern_definition.pattern_kind
    if authority.authority_validity_state == "valid":
        if (kind == "repeated_subject_risk"
                and (authority.minimum_member_subject_count is None
                     or authority.minimum_member_subject_count < 2)):
            raise D09ContractError(
                "valid repeated_subject_risk authority requires "
                "minimum_member_subject_count >= 2")
        if (kind == "systematic_data_or_process_gap"
                and authority.gap_positive_minimum_opportunity_count is None):
            raise D09ContractError(
                "valid systematic gap authority requires "
                "gap_positive_minimum_opportunity_count")
        if (kind == "within_site_time_trend"
                and authority.trend_positive_minimum_subject_count is None):
            raise D09ContractError(
                "valid trend authority requires trend_positive_minimum_subject_count")
    policy = typed.center_query_policy
    if policy.mode_contract_version != typed.mode_contract_version:
        raise D09ContractError("center_query_policy.mode_contract_version mismatch")
    query = typed.query_redundancy_decision
    if query.max_query_member_fanout != policy.max_query_member_fanout:
        raise D09ContractError(
            "query_redundancy_decision fanout does not match center_query_policy")
    if kind == "repeated_subject_risk":
        query_members = typed.subject_risk_members
    elif kind == "systematic_data_or_process_gap":
        query_members = typed.gap_members
    else:
        query_members = typed.change_ledger_members
    member_ids = tuple(sorted(member.member_id for member in query_members))
    if len(member_ids) != len(set(member_ids)):
        raise D09ContractError("D09 member ids must be unique")
    if query.unit_member_set_hash != d09_content_hash(list(member_ids)):
        raise D09ContractError("query_redundancy_decision unit-member hash mismatch")
    covered = set(query.covered_member_refs)
    uncovered = set(query.uncovered_member_refs)
    if (len(covered) != len(query.covered_member_refs)
            or len(uncovered) != len(query.uncovered_member_refs)
            or covered & uncovered
            or covered | uncovered != set(member_ids)):
        raise D09ContractError(
            "query covered/uncovered refs must be a disjoint exact member partition")
    actual_member_queries = tuple(sorted(set(
        ref
        for member in query_members
        for ref in member.query_draft_refs
    ))) if kind != "within_site_time_trend" else ()
    if tuple(sorted(query.member_query_refs)) != actual_member_queries:
        raise D09ContractError("query member-query refs mismatch")
    expected_proof_hash = d09_content_hash({
        "decision": query.decision,
        "covered": sorted(covered),
        "uncovered": sorted(uncovered),
        "member_queries": list(actual_member_queries),
        "fanout": query.max_query_member_fanout,
    })
    if query.coverage_proof_hash != expected_proof_hash:
        raise D09ContractError("query coverage proof hash mismatch")
    if query.decision == "fully_covered_by_member_queries" and (
            uncovered or covered != set(member_ids)
            or (member_ids and not query.member_query_refs)):
        raise D09ContractError("fully-covered Query decision lacks exact coverage")
    if (query.decision == "site_process_delta_present" and member_ids
            and not uncovered):
        raise D09ContractError("site-process delta requires uncovered members")
    expected_source_map = dict(zip(
        typed.source_revision_set, typed.source_content_hashes))
    if len(expected_source_map) != len(typed.source_revision_set):
        raise D09ContractError("source revisions must be unique")
    if len(typed.source_verification_records) != len(expected_source_map):
        raise D09ContractError(
            "source verification records must cover every revision exactly once")
    seen_revisions = set()
    for index, record in enumerate(typed.source_verification_records):
        if not isinstance(record, SourceVerificationRecord):
            raise D09ContractError(
                f"source_verification_records[{index}] must be a SourceVerificationRecord")
        _check_closed(f"source_verification_records[{index}].verification_state",
                      record.verification_state, SOURCE_VERIFICATION_STATES)
        _check_str(record.revision, f"source_verification_records[{index}].revision")
        _check_hash(record.declared_content_hash,
                    f"source_verification_records[{index}].declared_content_hash")
        _check_hash(record.verified_content_hash,
                    f"source_verification_records[{index}].verified_content_hash")
        if record.revision in seen_revisions or record.revision not in expected_source_map:
            raise D09ContractError("source verification revision mismatch or duplicate")
        seen_revisions.add(record.revision)
        if record.declared_content_hash != expected_source_map[record.revision]:
            raise D09ContractError("source verification declared hash mismatch")
        if (record.verification_state == "verified"
                and record.declared_content_hash != record.verified_content_hash):
            raise D09ContractError(
                "verified source record must have equal declared/verified hashes")
        if (record.verification_state == "mismatch"
                and record.declared_content_hash == record.verified_content_hash):
            raise D09ContractError(
                "mismatch source record must have unequal declared/verified hashes")
    _validate_lexicon(typed.audience_lexicon, "audience_lexicon")
    for index, ref in enumerate(typed.evidence_refs):
        if not isinstance(ref, EvidenceRef):
            raise D09ContractError(f"evidence_refs[{index}] must be an EvidenceRef")
    if typed.anti_overfit_variant is not None and not isinstance(
            typed.anti_overfit_variant, AntiOverfitVariant):
        raise D09ContractError("anti_overfit_variant must be an AntiOverfitVariant")


# ---------------------------------------------------------------------------
# Stable identities (contract sections 5.1/5.2)
# ---------------------------------------------------------------------------


def d09_unit_stable_core(typed: D09TypedInput) -> str:
    """Stable core: project|site|definition|window|stratum|stratum key.

    Revision-free semantic key; trend units use the current (last) closed
    window's stable id.  Never includes run/snapshot ids, computed dates,
    process ids or display text.
    """
    window_stable = (
        typed.analysis_windows[-1].analysis_window_stable_id
        if typed.analysis_windows else ""
    )
    return "|".join((
        typed.project_ref,
        typed.site_stable_id,
        typed.pattern_definition.pattern_definition_id,
        window_stable,
        typed.stratum.stratum_contract_id,
        typed.stratum.stratum_key,
    ))
