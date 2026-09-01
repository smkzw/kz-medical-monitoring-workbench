"""R4-D10 project/cross-site signal aggregation runtime -- typed contracts.

Implements the closed typed envelope of the frozen D10 v0.6 contract
(``reviews/medical_monitoring_r4_d10_project_signal_slice_contract_v0_6_20260816.md``)
as immutable, exact-key dataclasses.  The runtime consumes only these typed
objects; it never reads artifact files, generators, the oracle, the registry,
the quota manifest, the verifier or tests, and never branches on case/fixture/
test identifiers, mutation metadata, descriptions, ``SYN-*`` strings or
synthetic revision-hash conventions.

The envelope mirrors the frozen catalog's ``d10-typed-input-v1`` shape:
every nested object carries the exact key set fixed by the frozen catalog
generator, and every value validates against a closed enumeration.

Anti-overfit boundary (worker_01): decisive runtime facts are the explicit
closed typed fields below (rule hit state, counterevidence refs, coverage,
denominator, visibility decision, query decision, change decision, safety/
efficacy contexts, measure-origin binding, model evidence, source revision
pairs).  The mutation context and anti-overfit variant blocks are carried as
opaque audit metadata and are never read by the evaluator.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, List, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Frozen contract identity
# ---------------------------------------------------------------------------

D10_SCHEMA_VERSION = "1.0.0"
D10_TYPED_INPUT_SCHEMA = "d10-typed-input-v1"
D10_UNIT_ALGORITHM_VERSION = "d10_v1"
D10_DOMAIN_ID = "D10_project_signal_aggregation"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


# ---------------------------------------------------------------------------
# Closed typed enumerations (frozen v0.6 contract; exact vocabulary from the
# frozen generators/verifier)
# ---------------------------------------------------------------------------

SIGNAL_KINDS: Tuple[str, ...] = (
    "project_risk_distribution",
    "cross_site_pattern",
    "project_time_trend",
    "project_safety_trend",
    "project_efficacy_trend",
)

OWNED_TOKENS: Tuple[str, ...] = (
    "d10_project_risk_distribution",
    "d10_cross_site_pattern",
    "d10_project_time_trend",
    "d10_project_safety_trend",
    "d10_project_efficacy_trend",
)

CONSUME_ONLY_TOKENS: Tuple[str, ...] = (
    "d09_within_site_pattern",
    "d01_d08_individual_claim",
)

HANDOFF_ONLY_TOKENS: Tuple[str, ...] = (
    "formal_benefit_risk_conclusion",
    "confirmatory_treatment_effect",
    "site_quality_judgment",
)

UNRESOLVED_TOKEN = "unresolved"

OWNER_ROUTES: Tuple[str, ...] = (
    "evaluate_and_own",
    "consume_only",
    "handoff_only",
    "context_only",
    "routing_gate",
)

DISPOSITIONS: Tuple[str, ...] = (
    "positive",
    "negative",
    "boundary",
    "not_applicable",
    "not_evaluable",
)

GATE_DISPOSITIONS: Tuple[str, ...] = (
    "global_gate",
    "comparison_set_gate",
    "window_pair_gate",
    "routing_gate",
    "integrity_gate",
    "handoff_gate",
)

DENOMINATOR_KINDS: Tuple[str, ...] = (
    "enrolled_subjects",
    "treated_subjects",
    "safety_evaluable_subjects",
    "efficacy_evaluable_subjects",
    "subject_time",
    "exposure_time",
    "expected_assessment_opportunities",
    "analysis_population_members",
)

DENOMINATOR_STATES: Tuple[str, ...] = (
    "closed_positive",
    "closed_zero",
    "unclosed",
)

ESTIMATE_KINDS: Tuple[str, ...] = (
    "count",
    "proportion",
    "incidence_rate",
    "exposure_adjusted_rate",
    "summary_statistic",
    "responder_rate",
    "model_estimate",
)

COMPARISON_STATES: Tuple[str, ...] = ("insufficient_sites", "incomparable_sites", "ready")
PAIR_STATES: Tuple[str, ...] = ("insufficient_windows", "incomparable_windows", "ready")

CHANGE_KINDS: Tuple[str, ...] = (
    "initial_current", "new", "continued", "upgraded", "downgraded",
    "resolved", "reopened", "not_comparable",
)

CHANGE_CAUSES: Tuple[str, ...] = (
    "data", "denominator", "coverage", "knowledge", "rule", "mapping",
    "model", "method", "population", "visibility", "mode", "mixed",
)

LINEAGE_RELATIONS: Tuple[str, ...] = (
    "initial_full_snapshot",
    "continued_from_data_revision",
    "continued_from_cutoff_advance",
    "superseded_by_knowledge_change",
    "superseded_by_rule_or_mapping_change",
    "superseded_by_method_or_population_change",
    "superseded_by_mode_change",
    "superseded_by_visibility_change",
    "coverage_regressed",
    "not_comparable",
    "none",
)

HANDOFF_ACTIONS: Tuple[str, ...] = (
    "create", "continue", "update", "propose_close", "reopen", "supersede",
)

CUTOFF_DECISION_STATES: Tuple[str, ...] = (
    "strict_advance", "same_window", "policy_changed", "not_evaluable",
)

ORIGIN_DECISIONS: Tuple[str, ...] = (
    "all_verified_same_origin", "all_distinct", "mixed_verified_and_distinct",
    "ambiguous", "wrong_scope", "not_evaluable",
)

RATE_PROJECTION_STATES: Tuple[str, ...] = ("permitted", "suppressed", "qualified")
QUERY_REDUNDANCY_DECISIONS: Tuple[str, ...] = (
    "project_delta_present", "fully_covered_by_member_queries",
    "members_unlistable", "not_applicable",
)
PD_WORDING_STATES: Tuple[str, ...] = ("not_pd", "verify_whether_pd")
MEMBER_EXPANSION_STATES: Tuple[str, ...] = ("expanded", "unexpandable", "not_applicable")
MEMBER_SCOPE_STATES: Tuple[str, ...] = (
    "in_scope", "wrong_project", "wrong_site", "wrong_subject", "unresolvable",
)
RULE_HIT_STATES: Tuple[str, ...] = ("hit", "no_hit", "not_applicable")
EVIDENCE_SOURCES: Tuple[str, ...] = (
    "typed_member", "verified_measure", "pvalue", "model_majority",
)
EXPECTED_SET_STATES: Tuple[str, ...] = (
    "admitted", "global_admission_failed", "routed_consume_only",
    "routing_gate_unresolved", "control_plane_gate",
)
DESIGN_APPLICABLE_STATES: Tuple[str, ...] = ("applicable", "not_applicable", "unresolved")
LEAF_KINDS: Tuple[str, ...] = (
    "medical_unit", "hotspot_member_leaf", "control_plane_comparison_gate",
    "control_plane_window_pair_gate", "global_integrity_gate", "routing_gate",
    "handoff_gate", "analysis_only_change_leaf",
)
TRACE_KINDS: Tuple[str, ...] = ("evaluation_identity", "admission_replay")
TERMINAL_STATES: Tuple[str, ...] = ("stable", "blocked")
BLIND_STATUSES: Tuple[str, ...] = ("blinded", "unblinded_authorized")
MEMBER_KINDS: Tuple[str, ...] = (
    "individual_risk", "center_pattern", "accepted_gap", "safety_measure",
    "efficacy_measure", "denominator_member",
)
AGGREGATION_PLANES: Tuple[str, ...] = ("individual", "site_pattern", "project_measure")
SITE_ACTIVATION_STATES: Tuple[str, ...] = ("active", "late")
SCOPE_EQUALITY_DECISIONS: Tuple[str, ...] = ("exact_match", "mismatch")
OPPORTUNITY_PROVENANCES: Tuple[str, ...] = ("accepted_d05_plan", "raw_only")
OPPORTUNITY_STATES: Tuple[str, ...] = ("sufficient", "insufficient", "unknown")
WINDOW_KINDS: Tuple[str, ...] = (
    "calendar_interval", "study_day_interval", "exposure_interval",
)
WINDOW_STATES: Tuple[str, ...] = ("closed", "open")
STRATUM_ADMISSIONS: Tuple[str, ...] = (
    "admitted", "rejected_empty", "fanout_rejected", "not_required",
)
STRATUM_STATES: Tuple[str, ...] = ("closed", "open", "empty")
DEEP_LINK_TARGET_KINDS: Tuple[str, ...] = ("member", "site", "subject_site_pair")
MODEL_EVIDENCE_ROLES: Tuple[str, ...] = (
    "candidate_explanation", "counterevidence_suggestion",
)
ADJUDICATION_STATES: Tuple[str, ...] = ("accepted", "divergent", "pending")
CUTOFF_ADVANCE_DECISION_STATES: Tuple[str, ...] = (
    "strict_advance", "same_window", "policy_changed", "not_evaluable",
)

# Resolved-domain facts the runtime must derive from explicit typed fields
# (never from test/audit metadata):
NOT_EVALUABLE_COMP_CODES: Tuple[str, ...] = (
    "case_mix_missing", "method_validity_insufficient",
    "site_evidence_incomplete", "site_quality_judgment",
)
BOUNDARY_COMP_CODES: Tuple[str, ...] = (
    "case_mix_mismatch", "exposure_shortfall", "followup_shortfall",
    "heterogeneous_sites", "site_late_start", "site_late_start_outlier",
    "site_small", "site_small_outlier",
)
STIGMA_CODES: Tuple[str, ...] = (
    "site_late_start_outlier", "site_small", "site_small_outlier",
)
NON_DATA_CAUSE_KEYS: Tuple[str, ...] = (
    "denom_n", "coverage_n", "knowledge_n", "rule_n", "mapping_n",
    "model_n", "method_n", "population_n", "visibility_n", "mode_n",
)
CHANGE_KIND_FORBIDDEN_FOR_NON_DATA: Tuple[str, ...] = (
    "new", "continued", "upgraded", "downgraded", "resolved", "reopened",
)
ALLOWED_CREATE_LINEAGES: frozenset = frozenset((
    "initial_full_snapshot",
    "continued_from_data_revision",
    "continued_from_cutoff_advance",
))
DEFAULT_REQUIRED_DOMAINS: Mapping[str, Tuple[str, ...]] = {
    "project_risk_distribution": ("D01", "D02", "D03", "D04"),
    "cross_site_pattern": ("D09", "D01"),
    "project_time_trend": ("D09", "D10"),
    "project_safety_trend": ("D07", "D01"),
    "project_efficacy_trend": ("D06", "D01"),
}
DEN_KIND_ESTIMATE: Mapping[str, str] = {
    "subject_time": "incidence_rate",
    "exposure_time": "exposure_adjusted_rate",
}


# ---------------------------------------------------------------------------
# Canonical serialization and content addressing (contract section 16)
# ---------------------------------------------------------------------------


def d10_normalize_nfc(value: Any) -> Any:
    """Recursively Unicode-NFC-normalize strings and dict keys."""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        return {d10_normalize_nfc(k): d10_normalize_nfc(v)
                for k, v in value.items()}
    if isinstance(value, list):
        return [d10_normalize_nfc(item) for item in value]
    return value


def d10_canonical_json(value: Any) -> str:
    """Deterministic canonical JSON (NFC, sorted keys, compact, no NaN)."""
    return json.dumps(d10_normalize_nfc(value), ensure_ascii=False,
                      sort_keys=True, separators=(",", ":"), allow_nan=False)


def d10_sha256_text(text: str) -> str:
    """SHA-256 of a UTF-8 encoded string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def d10_content_hash(value: Any, own_hash_key: str = "content_hash") -> str:
    """Content address of any JSON-able object (hex sha256 of canonical JSON
    minus the object's own hash key)."""
    if isinstance(value, dict):
        core = {k: item for k, item in value.items() if k != own_hash_key}
    else:
        core = value
    return d10_sha256_text(d10_canonical_json(core))


def is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.match(value))


# ---------------------------------------------------------------------------
# Contract error and closed checks
# ---------------------------------------------------------------------------


class D10ContractError(Exception):
    """Closed-enum or required-field violation of a D10 typed object."""


def _check_closed(name: str, value: Any, allowed: Sequence[str]) -> str:
    if value not in allowed:
        raise D10ContractError(
            f"{name} must be one of {allowed!r}, got {value!r}")
    return value


def _check_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise D10ContractError(f"{name} must be a non-empty str, got {value!r}")
    return value


def _check_optional_str(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_str(value, name)


def _check_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise D10ContractError(f"{name} must be a bool, got {value!r}")
    return value


def _check_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise D10ContractError(f"{name} must be an int, got {value!r}")
    return value


def _check_nonneg_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise D10ContractError(f"{name} must be a non-negative int, got {value!r}")
    return value


def _check_positive_int(value: Any, name: str) -> int:
    value = _check_nonneg_int(value, name)
    if value < 1:
        raise D10ContractError(f"{name} must be a positive int, got {value!r}")
    return value


def _check_list(value: Any, name: str) -> List[Any]:
    if not isinstance(value, list):
        raise D10ContractError(f"{name} must be a list, got {value!r}")
    return value


def _check_str_tuple(value: Any, name: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise D10ContractError(f"{name} must be a list/tuple, got {value!r}")
    return tuple(str(item) for item in value)


def _check_hash(value: Any, name: str) -> str:
    if not is_sha256_hex(value):
        raise D10ContractError(f"{name} must be a 64-hex sha256, got {value!r}")
    return value


def _check_optional_hash(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_hash(value, name)


# ---------------------------------------------------------------------------
# Typed objects (full ``d10-typed-input-v1`` envelope)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScopeBinding:
    scope_binding_id: str
    scope_type: str = "project"
    scope_equality_decision: str = "exact_match"
    scope_binding_hash: str = ""


@dataclass(frozen=True)
class ModeContract:
    mode_contract_version: str
    mode_contract_content_hash: str
    design_applicable_state: str = "applicable"
    design_clause_ref: Optional[str] = None


@dataclass(frozen=True)
class SignalDefinition:
    signal_definition_id: str
    signal_kind: str
    clinical_claim_token: str
    d10_action: str
    risk_or_outcome_domain: str
    required_producer_domains: Tuple[str, ...] = ()
    positive_rule_ref: str = ""
    counterevidence_rule_refs: Tuple[str, ...] = ()
    legal_matrix_row_ref: str = ""
    authority_locator: str = ""


@dataclass(frozen=True)
class LegalMatrixRow:
    row_id: str
    signal_kind: str
    clinical_claim_token: str
    d10_action: str
    row_hash: str = ""


@dataclass(frozen=True)
class AdmissionGate:
    gate_kind: str
    reason_codes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ExpectedSet:
    expected_set_state: str = "admitted"
    admission_gate: Optional[AdmissionGate] = None


@dataclass(frozen=True)
class AnalysisWindow:
    analysis_window_stable_id: str
    window_instance_id: str
    window_definition_id: str
    window_definition_hash: str
    window_kind: str = "calendar_interval"
    window_state: str = "closed"
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    cutoff_ref: Optional[str] = None


@dataclass(frozen=True)
class Stratum:
    stratum_contract_id: str
    stratum_key: str
    stratum_state: str = "closed"
    stratum_admission: str = "admitted"


@dataclass(frozen=True)
class ComparisonGate:
    comparison_state: str
    comparison_reference_stable_id: str
    required_site_count_ref: str = ""
    observed_eligible_site_count: int = 0
    eligible_site_refs: Tuple[str, ...] = ()
    excluded_site_refs: Tuple[str, ...] = ()
    reason_codes: Tuple[str, ...] = ()
    permitted_output: str = ""


@dataclass(frozen=True)
class WindowPairGate:
    pair_state: str
    required_window_count_ref: str = ""
    observed_unique_window_count: int = 0
    reason_codes: Tuple[str, ...] = ()
    permitted_output: str = ""


@dataclass(frozen=True)
class SiteLedger:
    ledger_id: str
    site_ref: str
    site_activation_state: str = "active"
    identity_state: str = "stable"
    eligible_subject_refs: Tuple[str, ...] = ()
    treated_subject_refs: Tuple[str, ...] = ()
    evaluable_subject_refs: Tuple[str, ...] = ()
    d09_pattern_refs: Tuple[str, ...] = ()
    coverage_refs: Tuple[str, ...] = ()
    site_activation_ref: str = ""


@dataclass(frozen=True)
class Member:
    member_ref: str
    member_kind: str
    aggregation_plane: str
    producer_domain: str
    member_scope_state: str = "in_scope"
    site_stable_id: str = ""
    subject_stable_id: Optional[str] = None
    monitoring_priority: str = "medium"
    accepted_current_state: str = "accepted_current"
    locator_resolution_state: str = "locatable"
    source_locator_refs: Tuple[str, ...] = ()
    descendant_member_refs: Tuple[str, ...] = ()
    descendant_set_hash: Optional[str] = None
    treatment_role_ref: Optional[str] = None


@dataclass(frozen=True)
class NumeratorLedger:
    individual_risk_count: int
    center_pattern_count: int
    affected_subject_count: int
    event_or_outcome_count: int
    affected_site_count: int
    numerator_member_count: int


@dataclass(frozen=True)
class MeasureOriginBinding:
    binding_id: str
    measure_ref: str
    origin_decision: str
    verified_risk_refs: Tuple[str, ...] = ()
    distinct_risk_refs: Tuple[str, ...] = ()
    ambiguous_risk_refs: Tuple[str, ...] = ()
    candidate_risk_refs: Tuple[str, ...] = ()
    candidate_partition_hash: str = ""
    numerator_plane_state: str = "single"
    binding_hash: str = ""
    source_provenance_hash: str = ""


@dataclass(frozen=True)
class Denominator:
    denominator_kind: str
    denominator_value: int
    recomputed_value: int
    denominator_unit: str = "subject"
    denominator_state: str = "closed_positive"
    denominator_member_refs: Tuple[str, ...] = ()
    excluded_member_refs: Tuple[str, ...] = ()
    exclusion_reason_codes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class TimeSegment:
    segment_id: str
    member_ref: str
    segment_kind: str = "subject_time"
    start_value: int = 0
    end_value: int = 0
    raw_duration: int = 0
    normalized_duration: int = 0
    unit: str = "day"
    inclusivity: str = "both_inclusive"
    overlap_resolution_ref: Optional[str] = None


@dataclass(frozen=True)
class Opportunity:
    opportunity_definition_ref: str = ""
    expected_opportunity_count: int = 0
    observed_opportunity_count: int = 0
    missing_opportunity_refs: Tuple[str, ...] = ()
    opportunity_provenance: str = "accepted_d05_plan"
    opportunity_state: str = "unknown"
    complete: bool = False


@dataclass(frozen=True)
class AnalysisPopulation:
    analysis_population_ref: str
    present: bool = True
    analysis_population_contract_id: str = ""


@dataclass(frozen=True)
class CoverageStatus:
    producer_domain: str
    l0_status: str = "covered"
    l1_medical_completeness_state: str = "complete"
    accepted_current: bool = True
    coverage_locator_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CutoffAdvance:
    decision_state: str
    strict_advance_predicate_passed: bool = False
    policy_semantic_hash_equal: bool = False
    prior_boundary_value: Optional[str] = None
    current_boundary_value: Optional[str] = None


@dataclass(frozen=True)
class ChangeDecision:
    execution_basis: str
    comparison_state: str
    prior_snapshot_ref_or_none: Optional[str] = None
    data_change_refs: Tuple[str, ...] = ()
    denominator_change_refs: Tuple[str, ...] = ()
    coverage_change_refs: Tuple[str, ...] = ()
    knowledge_change_refs: Tuple[str, ...] = ()
    rule_change_refs: Tuple[str, ...] = ()
    mapping_change_refs: Tuple[str, ...] = ()
    model_change_refs: Tuple[str, ...] = ()
    method_change_refs: Tuple[str, ...] = ()
    population_change_refs: Tuple[str, ...] = ()
    visibility_change_refs: Tuple[str, ...] = ()
    mode_change_refs: Tuple[str, ...] = ()
    cutoff_advance: Optional[CutoffAdvance] = None
    r2_prior_ref_or_none: Optional[str] = None
    r2_action: str = ""
    lineage_relation: str = ""
    carry_forward_state: str = "none"
    claimed_clinical_change_kind: Optional[str] = None
    claimed_primary_change_cause: Optional[str] = None
    claimed_cutoff_state: Optional[str] = None
    data_change_kind: Optional[str] = None


@dataclass(frozen=True)
class VisibilityDecision:
    decision_id: str
    blind_status: str = "blinded"
    audience_scope_id: str = ""
    evaluation_member_refs: Tuple[str, ...] = ()
    projectable_member_refs: Tuple[str, ...] = ()
    hidden_member_refs: Tuple[str, ...] = ()
    hidden_reason_codes: Tuple[str, ...] = ()
    evaluation_site_refs: Tuple[str, ...] = ()
    projectable_site_refs: Tuple[str, ...] = ()
    hidden_site_refs: Tuple[str, ...] = ()
    visible_n: int = 0
    eligible_n: int = 0
    hidden_member_count: int = 0
    hidden_site_count: int = 0
    rate_projection_state: str = "permitted"
    deep_link_eligible_member_refs: Tuple[str, ...] = ()
    deep_link_eligible_site_refs: Tuple[str, ...] = ()
    hidden_set_omitted: bool = False
    deep_link_eligible_violation: bool = False
    treatment_inference_attempt: bool = False
    projectable_subject_site_pairs: Tuple[Tuple[str, str], ...] = ()
    deep_link_eligible_subject_site_pairs: Tuple[Tuple[str, str], ...] = ()


@dataclass(frozen=True)
class QueryDecision:
    decision: str
    covered_member_refs: Tuple[str, ...] = ()
    uncovered_member_refs: Tuple[str, ...] = ()
    member_query_content_identities: Tuple[str, ...] = ()
    unit_member_set_hash: str = ""
    coverage_proof_hash: str = ""
    max_query_member_fanout: int = 100
    member_unlistable: bool = False
    pd_wording_state: str = "not_pd"
    duplicate_query_attempt: bool = False
    query_content_hash: str = ""


@dataclass(frozen=True)
class AudienceText:
    audience_contract_id: str
    display_language: str = "zh-CN"
    sentence_part_kind: str = "observed_finding"
    basis_zh: str = ""
    finding_zh: str = ""
    action_zh: str = ""
    engineering_reference_attempt: bool = False
    injection_blocked: bool = False


@dataclass(frozen=True)
class DeepLink:
    target_kind: str
    site_ref: Optional[str] = None
    subject_ref: Optional[str] = None
    member_object_ref: Optional[str] = None
    visibility_decision_ref: str = ""
    return_state_key: str = ""


@dataclass(frozen=True)
class ModelEvidence:
    model_evidence_id: str
    role: str
    permitted_leaf: str
    model_id: str
    model_version: str
    evaluation_content_identity: str = ""
    input_content_hash: str = ""
    source_revision_content_pairs: Tuple[SourceRevisionPair, ...] = ()
    source_refs: Tuple[str, ...] = ()
    independent_context_hash: str = ""
    ensemble_id: str = ""
    ensemble_size: int = 1
    member_analysis_refs: Tuple[str, ...] = ()
    member_analysis_ref_set_hash: str = ""
    output_identity: str = ""
    output_hash: str = ""
    adjudication_state: str = "pending"
    model_binding_hash: str = ""


@dataclass(frozen=True)
class SafetyContext:
    context_id: str
    context_complete: bool = False
    exposure_definition_ref: Optional[str] = None
    coding_dictionary_ref: Optional[str] = None
    severity_scale_ref: Optional[str] = None
    risk_window_ref: Optional[str] = None
    descriptive_monitoring_only: bool = True


@dataclass(frozen=True)
class EfficacyContext:
    context_id: str
    context_complete: bool = False
    endpoint_definition_ref: Optional[str] = None
    estimand_ref: Optional[str] = None
    missing_data_rule_ref: Optional[str] = None
    intercurrent_event_rule_ref: Optional[str] = None
    treatment_role_authority_ref: Optional[str] = None
    treatment_assignment_exposure_identity_ref: Optional[str] = None
    treatment_role_required: bool = False
    blind_visibility_contract_ref: Optional[str] = None
    descriptive_monitoring_only: bool = True
    estimate_kind: Optional[str] = None
    treatment_assignment_mapping_hash: Optional[str] = None


@dataclass(frozen=True)
class RuleHit:
    positive_rule_ref: str = ""
    hit_state: str = "no_hit"
    evidence_sources: Tuple[str, ...] = ()
    counterevidence_matched_refs: Tuple[str, ...] = ()
    counterevidence_declared_refs: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Hotspot:
    hotspot_member_refs: Tuple[str, ...] = ()
    hidden_in_display: bool = False


@dataclass(frozen=True)
class CountLayers:
    layers_in_common_numerator: Tuple[str, ...] = ()
    mixed: bool = False


@dataclass(frozen=True)
class EvaluationLimits:
    small_sample: bool = False
    limited_evidence: bool = False
    limited_reason: Optional[str] = None


@dataclass(frozen=True)
class NumericPolicy:
    policy_id: str = ""
    allowed_estimate_kinds: Tuple[str, ...] = ()
    decimal_context: str = "decimal(10,4)"
    rounding_mode: str = "half_up"
    display_precision: int = 1
    subject_time_unit: str = "day"
    exposure_time_unit: str = "subject_day"
    overlap_policy: str = "resolve_by_authority"


@dataclass(frozen=True)
class MutationContext:
    """Opaque audit/test metadata (frozen catalog emission).  Never read by
    the evaluator; shape-only validation."""
    mutation_class: Optional[str] = None
    desc: Optional[str] = None
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
    the evaluator."""
    base_fixture_id: Optional[str] = None
    semantic_equivalence_ref: Optional[str] = None
    surface_changes: Tuple[SurfaceChange, ...] = ()
    variant_id: Optional[int] = None


@dataclass(frozen=True)
class EvidenceRef:
    locator_id: str
    locator_kind: str = "synthetic_file"
    source_file: str = ""
    row_or_cell_ref: str = ""
    lineage_ref: str = ""


@dataclass(frozen=True)
class SourceRevisionPair:
    revision_id: str
    content_hash: str


@dataclass(frozen=True)
class D10TypedInput:
    """Complete typed bundle for one D10 evaluation (``d10-typed-input-v1``)."""
    input_schema: str
    envelope_id: str
    project_ref: str
    run_ref: str
    snapshot_ref: str
    source_revision_content_pairs: Tuple[SourceRevisionPair, ...]
    project_scope_binding: ScopeBinding
    mode_contract: ModeContract
    signal_definition: SignalDefinition
    legal_matrix_row: LegalMatrixRow
    expected_set: ExpectedSet
    analysis_windows: Tuple[AnalysisWindow, ...]
    stratum: Stratum
    comparison_gate: ComparisonGate
    window_pair_gate: WindowPairGate
    site_ledger: SiteLedger
    members: Tuple[Member, ...]
    numerator_ledger: NumeratorLedger
    measure_origin_binding: Optional[MeasureOriginBinding]
    denominator: Denominator
    time_segments: Tuple[TimeSegment, ...]
    opportunity: Optional[Opportunity]
    analysis_population: AnalysisPopulation
    coverage: Tuple[CoverageStatus, ...]
    change_decision: Optional[ChangeDecision]
    visibility_decision: VisibilityDecision
    query_decision: QueryDecision
    audience_text: AudienceText
    deep_links: Tuple[DeepLink, ...]
    model_evidence: Optional[ModelEvidence]
    safety_context: Optional[SafetyContext]
    efficacy_context: Optional[EfficacyContext]
    rule_hit: RuleHit
    hotspot: Optional[Hotspot]
    count_layers: CountLayers
    evaluation_limits: EvaluationLimits
    numeric_policy: NumericPolicy
    mutation_context: MutationContext
    anti_overfit_variant: Optional[AntiOverfitVariant]
    evidence_refs: Tuple[EvidenceRef, ...]


@dataclass(frozen=True)
class D10EvaluationAuthority:
    """Immutable runtime authority (accepted envelope identity and source
    membership) sourced from the independent fixture-authority registry.

    The test-only adapter reads the registry and constructs this object; the
    runtime reads no files and must be handed this object per evaluation.  It
    carries only decisive explicit authority facts -- never case/fixture/test
    ids, mutation metadata, descriptions or synthetic conventions:

    * the accepted project/run/snapshot identity;
    * the accepted source revision-content pairs (submitted source pairs must
      be a non-empty internally valid subset; submitted extras remain
      evaluation input and are rejected by authority preflight);
    * the accepted source locator set hash;
    * the decisive ModelEvidence binding/output pins (optional only when no
      model evidence is authorized; presence/absence and pins are checked
      before project medical facts are computed).
    """
    project_ref: str
    run_ref: str
    snapshot_ref: str
    accepted_source_revision_content_pairs: Tuple[SourceRevisionPair, ...] = ()
    accepted_source_locator_set_hash: str = ""
    model_binding_hash: Optional[str] = None
    model_output_hash: Optional[str] = None


# ---------------------------------------------------------------------------
# Per-object validation
# ---------------------------------------------------------------------------


def _validate_scope_binding(binding: Any, name: str) -> None:
    if not isinstance(binding, ScopeBinding):
        raise D10ContractError(f"{name} must be a ScopeBinding")
    _check_str(binding.scope_binding_id, f"{name}.scope_binding_id")
    _check_closed(f"{name}.scope_equality_decision",
                  binding.scope_equality_decision, SCOPE_EQUALITY_DECISIONS)
    _check_hash(binding.scope_binding_hash, f"{name}.scope_binding_hash")


def _validate_mode_contract(mode: Any, name: str) -> None:
    if not isinstance(mode, ModeContract):
        raise D10ContractError(f"{name} must be a ModeContract")
    _check_str(mode.mode_contract_version, f"{name}.mode_contract_version")
    _check_hash(mode.mode_contract_content_hash, f"{name}.mode_contract_content_hash")
    _check_closed(f"{name}.design_applicable_state",
                  mode.design_applicable_state, DESIGN_APPLICABLE_STATES)


def _validate_signal_definition(definition: Any, name: str) -> None:
    if not isinstance(definition, SignalDefinition):
        raise D10ContractError(f"{name} must be a SignalDefinition")
    _check_str(definition.signal_definition_id, f"{name}.signal_definition_id")
    _check_closed(f"{name}.signal_kind", definition.signal_kind, SIGNAL_KINDS)
    _check_closed(f"{name}.d10_action", definition.d10_action, OWNER_ROUTES)
    _check_str_tuple(definition.required_producer_domains,
                     f"{name}.required_producer_domains")


def _validate_legal_matrix_row(row: Any, name: str) -> None:
    if not isinstance(row, LegalMatrixRow):
        raise D10ContractError(f"{name} must be a LegalMatrixRow")
    _check_str(row.row_id, f"{name}.row_id")
    _check_closed(f"{name}.signal_kind", row.signal_kind, SIGNAL_KINDS)
    _check_closed(f"{name}.d10_action", row.d10_action, OWNER_ROUTES)
    _check_hash(row.row_hash, f"{name}.row_hash")


def _validate_expected_set(expected_set: Any, name: str) -> None:
    if not isinstance(expected_set, ExpectedSet):
        raise D10ContractError(f"{name} must be an ExpectedSet")
    _check_closed(f"{name}.expected_set_state",
                  expected_set.expected_set_state, EXPECTED_SET_STATES)
    if expected_set.admission_gate is not None:
        gate = expected_set.admission_gate
        if not isinstance(gate, AdmissionGate):
            raise D10ContractError(f"{name}.admission_gate must be an AdmissionGate")
        _check_str(gate.gate_kind, f"{name}.admission_gate.gate_kind")
        _check_str_tuple(gate.reason_codes, f"{name}.admission_gate.reason_codes")


def _validate_window(window: Any, index: int) -> None:
    name = f"analysis_windows[{index}]"
    if not isinstance(window, AnalysisWindow):
        raise D10ContractError(f"{name} must be an AnalysisWindow")
    _check_str(window.analysis_window_stable_id, f"{name}.analysis_window_stable_id")
    _check_str(window.window_instance_id, f"{name}.window_instance_id")
    _check_str(window.window_definition_id, f"{name}.window_definition_id")
    _check_hash(window.window_definition_hash, f"{name}.window_definition_hash")
    _check_closed(f"{name}.window_kind", window.window_kind, WINDOW_KINDS)
    _check_closed(f"{name}.window_state", window.window_state, WINDOW_STATES)


def _validate_stratum(stratum: Any, name: str) -> None:
    if not isinstance(stratum, Stratum):
        raise D10ContractError(f"{name} must be a Stratum")
    _check_str(stratum.stratum_contract_id, f"{name}.stratum_contract_id")
    _check_str(stratum.stratum_key, f"{name}.stratum_key")
    _check_closed(f"{name}.stratum_state", stratum.stratum_state, STRATUM_STATES)
    _check_closed(f"{name}.stratum_admission",
                  stratum.stratum_admission, STRATUM_ADMISSIONS)


def _validate_comparison_gate(gate: Any, name: str) -> None:
    if not isinstance(gate, ComparisonGate):
        raise D10ContractError(f"{name} must be a ComparisonGate")
    _check_closed(f"{name}.comparison_state", gate.comparison_state, COMPARISON_STATES)
    _check_str(gate.comparison_reference_stable_id,
               f"{name}.comparison_reference_stable_id")
    _check_nonneg_int(gate.observed_eligible_site_count,
                      f"{name}.observed_eligible_site_count")
    _check_str_tuple(gate.eligible_site_refs, f"{name}.eligible_site_refs")
    _check_str_tuple(gate.excluded_site_refs, f"{name}.excluded_site_refs")
    _check_str_tuple(gate.reason_codes, f"{name}.reason_codes")


def _validate_window_pair_gate(gate: Any, name: str) -> None:
    if not isinstance(gate, WindowPairGate):
        raise D10ContractError(f"{name} must be a WindowPairGate")
    _check_closed(f"{name}.pair_state", gate.pair_state, PAIR_STATES)
    _check_nonneg_int(gate.observed_unique_window_count,
                      f"{name}.observed_unique_window_count")
    _check_str_tuple(gate.reason_codes, f"{name}.reason_codes")


def _validate_site_ledger(ledger: Any, name: str) -> None:
    if not isinstance(ledger, SiteLedger):
        raise D10ContractError(f"{name} must be a SiteLedger")
    _check_str(ledger.ledger_id, f"{name}.ledger_id")
    _check_str(ledger.site_ref, f"{name}.site_ref")
    _check_closed(f"{name}.site_activation_state",
                  ledger.site_activation_state, SITE_ACTIVATION_STATES)
    _check_str_tuple(ledger.eligible_subject_refs, f"{name}.eligible_subject_refs")
    _check_str_tuple(ledger.treated_subject_refs, f"{name}.treated_subject_refs")
    _check_str_tuple(ledger.evaluable_subject_refs, f"{name}.evaluable_subject_refs")
    _check_str_tuple(ledger.d09_pattern_refs, f"{name}.d09_pattern_refs")
    _check_str_tuple(ledger.coverage_refs, f"{name}.coverage_refs")


def _validate_member(member: Any, index: int) -> None:
    name = f"members[{index}]"
    if not isinstance(member, Member):
        raise D10ContractError(f"{name} must be a Member")
    _check_str(member.member_ref, f"{name}.member_ref")
    _check_closed(f"{name}.member_kind", member.member_kind, MEMBER_KINDS)
    _check_closed(f"{name}.aggregation_plane",
                  member.aggregation_plane, AGGREGATION_PLANES)
    _check_closed(f"{name}.member_scope_state",
                  member.member_scope_state, MEMBER_SCOPE_STATES)
    _check_str_tuple(member.source_locator_refs, f"{name}.source_locator_refs")
    _check_str_tuple(member.descendant_member_refs, f"{name}.descendant_member_refs")
    if member.member_kind == "center_pattern":
        if not member.descendant_member_refs or not member.descendant_set_hash:
            raise D10ContractError(
                f"{name} center_pattern requires descendant refs + set hash")
    else:
        if member.descendant_member_refs or member.descendant_set_hash:
            raise D10ContractError(
                f"{name} non-pattern member must have empty descendant fields")


def _validate_numerator_ledger(ledger: Any, name: str) -> None:
    if not isinstance(ledger, NumeratorLedger):
        raise D10ContractError(f"{name} must be a NumeratorLedger")
    for key in ("individual_risk_count", "center_pattern_count",
                "affected_subject_count", "event_or_outcome_count",
                "affected_site_count", "numerator_member_count"):
        _check_nonneg_int(getattr(ledger, key), f"{name}.{key}")


def _validate_measure_origin(binding: Any, name: str) -> None:
    if not isinstance(binding, MeasureOriginBinding):
        raise D10ContractError(f"{name} must be a MeasureOriginBinding")
    _check_str(binding.binding_id, f"{name}.binding_id")
    _check_closed(f"{name}.origin_decision",
                  binding.origin_decision, ORIGIN_DECISIONS)
    for key in ("verified_risk_refs", "distinct_risk_refs",
                "ambiguous_risk_refs", "candidate_risk_refs"):
        _check_str_tuple(getattr(binding, key), f"{name}.{key}")
    _check_closed(f"{name}.numerator_plane_state",
                  binding.numerator_plane_state, ("single", "duplicate"))


def _validate_denominator(denominator: Any, name: str) -> None:
    if not isinstance(denominator, Denominator):
        raise D10ContractError(f"{name} must be a Denominator")
    _check_closed(f"{name}.denominator_kind",
                  denominator.denominator_kind, DENOMINATOR_KINDS)
    _check_closed(f"{name}.denominator_state",
                  denominator.denominator_state, DENOMINATOR_STATES)
    # A negative submitted denominator value is a valid tamper fixture; the
    # evaluator maps it to the ``invalid_numeric`` integrity gate (contract
    # section 6 executable equalities), so it must survive shape validation.
    _check_int(denominator.denominator_value, f"{name}.denominator_value")
    _check_int(denominator.recomputed_value, f"{name}.recomputed_value")
    _check_str_tuple(denominator.denominator_member_refs,
                     f"{name}.denominator_member_refs")
    _check_str_tuple(denominator.excluded_member_refs,
                     f"{name}.excluded_member_refs")
    _check_str_tuple(denominator.exclusion_reason_codes,
                     f"{name}.exclusion_reason_codes")


def _validate_time_segment(segment: Any, index: int) -> None:
    name = f"time_segments[{index}]"
    if not isinstance(segment, TimeSegment):
        raise D10ContractError(f"{name} must be a TimeSegment")
    _check_str(segment.segment_id, f"{name}.segment_id")
    _check_str(segment.member_ref, f"{name}.member_ref")
    _check_nonneg_int(segment.start_value, f"{name}.start_value")
    _check_nonneg_int(segment.end_value, f"{name}.end_value")
    _check_nonneg_int(segment.raw_duration, f"{name}.raw_duration")
    _check_nonneg_int(segment.normalized_duration, f"{name}.normalized_duration")


def _validate_opportunity(opportunity: Any, name: str) -> None:
    if not isinstance(opportunity, Opportunity):
        raise D10ContractError(f"{name} must be an Opportunity")
    _check_closed(f"{name}.opportunity_provenance",
                  opportunity.opportunity_provenance, OPPORTUNITY_PROVENANCES)
    _check_closed(f"{name}.opportunity_state",
                  opportunity.opportunity_state, OPPORTUNITY_STATES)
    _check_nonneg_int(opportunity.expected_opportunity_count,
                      f"{name}.expected_opportunity_count")
    _check_nonneg_int(opportunity.observed_opportunity_count,
                      f"{name}.observed_opportunity_count")
    _check_bool(opportunity.complete, f"{name}.complete")


def _validate_analysis_population(population: Any, name: str) -> None:
    if not isinstance(population, AnalysisPopulation):
        raise D10ContractError(f"{name} must be an AnalysisPopulation")
    _check_str(population.analysis_population_ref, f"{name}.analysis_population_ref")
    _check_bool(population.present, f"{name}.present")


def _validate_coverage(coverage: Any, index: int) -> None:
    name = f"coverage[{index}]"
    if not isinstance(coverage, CoverageStatus):
        raise D10ContractError(f"{name} must be a CoverageStatus")
    _check_str(coverage.producer_domain, f"{name}.producer_domain")
    _check_str_tuple(coverage.coverage_locator_ids, f"{name}.coverage_locator_ids")


def _validate_cutoff_advance(advance: Any, name: str) -> None:
    if not isinstance(advance, CutoffAdvance):
        raise D10ContractError(f"{name} must be a CutoffAdvance")
    _check_closed(f"{name}.decision_state",
                  advance.decision_state, CUTOFF_ADVANCE_DECISION_STATES)
    _check_bool(advance.strict_advance_predicate_passed,
                f"{name}.strict_advance_predicate_passed")
    _check_bool(advance.policy_semantic_hash_equal,
                f"{name}.policy_semantic_hash_equal")


def _validate_change_decision(change: Any, name: str) -> None:
    if not isinstance(change, ChangeDecision):
        raise D10ContractError(f"{name} must be a ChangeDecision")
    for key in ("data_change_refs", "denominator_change_refs",
                "coverage_change_refs", "knowledge_change_refs",
                "rule_change_refs", "mapping_change_refs",
                "model_change_refs", "method_change_refs",
                "population_change_refs", "visibility_change_refs",
                "mode_change_refs"):
        _check_str_tuple(getattr(change, key), f"{name}.{key}")
    if change.cutoff_advance is not None:
        _validate_cutoff_advance(change.cutoff_advance, f"{name}.cutoff_advance")
    if change.r2_action:
        _check_closed(f"{name}.r2_action", change.r2_action, HANDOFF_ACTIONS)
    if change.lineage_relation:
        _check_closed(f"{name}.lineage_relation",
                      change.lineage_relation, LINEAGE_RELATIONS)


def _validate_visibility(visibility: Any, name: str) -> None:
    if not isinstance(visibility, VisibilityDecision):
        raise D10ContractError(f"{name} must be a VisibilityDecision")
    _check_hash(visibility.decision_id, f"{name}.decision_id")
    _check_closed(f"{name}.blind_status", visibility.blind_status, BLIND_STATUSES)
    _check_closed(f"{name}.rate_projection_state",
                  visibility.rate_projection_state, RATE_PROJECTION_STATES)
    _check_nonneg_int(visibility.visible_n, f"{name}.visible_n")
    _check_nonneg_int(visibility.eligible_n, f"{name}.eligible_n")
    _check_nonneg_int(visibility.hidden_member_count, f"{name}.hidden_member_count")
    _check_nonneg_int(visibility.hidden_site_count, f"{name}.hidden_site_count")
    for key in ("evaluation_member_refs", "projectable_member_refs",
                "hidden_member_refs", "evaluation_site_refs",
                "projectable_site_refs", "hidden_site_refs",
                "deep_link_eligible_member_refs", "deep_link_eligible_site_refs"):
        _check_str_tuple(getattr(visibility, key), f"{name}.{key}")
    _check_bool(visibility.hidden_set_omitted, f"{name}.hidden_set_omitted")
    _check_bool(visibility.deep_link_eligible_violation,
                f"{name}.deep_link_eligible_violation")
    _check_bool(visibility.treatment_inference_attempt,
                f"{name}.treatment_inference_attempt")


def _validate_query_decision(decision: Any, name: str) -> None:
    if not isinstance(decision, QueryDecision):
        raise D10ContractError(f"{name} must be a QueryDecision")
    _check_closed(f"{name}.decision",
                  decision.decision, QUERY_REDUNDANCY_DECISIONS)
    _check_closed(f"{name}.pd_wording_state",
                  decision.pd_wording_state, PD_WORDING_STATES)
    _check_nonneg_int(decision.max_query_member_fanout,
                      f"{name}.max_query_member_fanout")
    _check_bool(decision.member_unlistable, f"{name}.member_unlistable")
    _check_bool(decision.duplicate_query_attempt, f"{name}.duplicate_query_attempt")
    for key in ("covered_member_refs", "uncovered_member_refs",
                "member_query_content_identities"):
        _check_str_tuple(getattr(decision, key), f"{name}.{key}")


def _validate_audience_text(text: Any, name: str) -> None:
    if not isinstance(text, AudienceText):
        raise D10ContractError(f"{name} must be an AudienceText")
    _check_str(text.audience_contract_id, f"{name}.audience_contract_id")
    _check_bool(text.engineering_reference_attempt,
                f"{name}.engineering_reference_attempt")
    _check_bool(text.injection_blocked, f"{name}.injection_blocked")


def _validate_deep_link(link: Any, index: int) -> None:
    name = f"deep_links[{index}]"
    if not isinstance(link, DeepLink):
        raise D10ContractError(f"{name} must be a DeepLink")
    _check_closed(f"{name}.target_kind", link.target_kind, DEEP_LINK_TARGET_KINDS)
    _check_str(link.visibility_decision_ref, f"{name}.visibility_decision_ref")


def _validate_model_evidence(model: Any, name: str) -> None:
    if not isinstance(model, ModelEvidence):
        raise D10ContractError(f"{name} must be a ModelEvidence")
    _check_closed(f"{name}.role", model.role, MODEL_EVIDENCE_ROLES)
    _check_str(model.permitted_leaf, f"{name}.permitted_leaf")
    _check_positive_int(model.ensemble_size, f"{name}.ensemble_size")
    _check_str_tuple(model.member_analysis_refs, f"{name}.member_analysis_refs")
    _check_closed(f"{name}.adjudication_state",
                  model.adjudication_state, ADJUDICATION_STATES)


def _validate_safety_context(context: Any, name: str) -> None:
    if not isinstance(context, SafetyContext):
        raise D10ContractError(f"{name} must be a SafetyContext")
    _check_bool(context.context_complete, f"{name}.context_complete")
    _check_bool(context.descriptive_monitoring_only,
                f"{name}.descriptive_monitoring_only")


def _validate_efficacy_context(context: Any, name: str) -> None:
    if not isinstance(context, EfficacyContext):
        raise D10ContractError(f"{name} must be an EfficacyContext")
    _check_bool(context.context_complete, f"{name}.context_complete")
    _check_bool(context.descriptive_monitoring_only,
                f"{name}.descriptive_monitoring_only")
    _check_bool(context.treatment_role_required, f"{name}.treatment_role_required")
    if context.estimate_kind is not None:
        _check_closed(f"{name}.estimate_kind",
                      context.estimate_kind, ESTIMATE_KINDS)


def _validate_rule_hit(hit: Any, name: str) -> None:
    if not isinstance(hit, RuleHit):
        raise D10ContractError(f"{name} must be a RuleHit")
    _check_closed(f"{name}.hit_state", hit.hit_state, RULE_HIT_STATES)
    _check_str_tuple(hit.evidence_sources, f"{name}.evidence_sources")
    _check_str_tuple(hit.counterevidence_matched_refs,
                     f"{name}.counterevidence_matched_refs")
    _check_str_tuple(hit.counterevidence_declared_refs,
                     f"{name}.counterevidence_declared_refs")


def _validate_hotspot(hotspot: Any, name: str) -> None:
    if not isinstance(hotspot, Hotspot):
        raise D10ContractError(f"{name} must be a Hotspot")
    _check_str_tuple(hotspot.hotspot_member_refs, f"{name}.hotspot_member_refs")
    _check_bool(hotspot.hidden_in_display, f"{name}.hidden_in_display")


def _validate_count_layers(layers: Any, name: str) -> None:
    if not isinstance(layers, CountLayers):
        raise D10ContractError(f"{name} must be a CountLayers")
    _check_str_tuple(layers.layers_in_common_numerator,
                     f"{name}.layers_in_common_numerator")
    _check_bool(layers.mixed, f"{name}.mixed")


def _validate_evaluation_limits(limits: Any, name: str) -> None:
    if not isinstance(limits, EvaluationLimits):
        raise D10ContractError(f"{name} must be an EvaluationLimits")
    _check_bool(limits.small_sample, f"{name}.small_sample")
    _check_bool(limits.limited_evidence, f"{name}.limited_evidence")


def _validate_numeric_policy(policy: Any, name: str) -> None:
    if not isinstance(policy, NumericPolicy):
        raise D10ContractError(f"{name} must be a NumericPolicy")
    _check_str_tuple(policy.allowed_estimate_kinds, f"{name}.allowed_estimate_kinds")
    _check_nonneg_int(policy.display_precision, f"{name}.display_precision")


def _validate_mutation_context(context: Any, name: str) -> None:
    """Shape-only validation: opaque audit metadata, never read semantically."""
    if not isinstance(context, MutationContext):
        raise D10ContractError(f"{name} must be a MutationContext")


def _validate_anti_overfit(variant: Any, name: str) -> None:
    """Shape-only validation: opaque audit metadata, never read semantically."""
    if not isinstance(variant, AntiOverfitVariant):
        raise D10ContractError(f"{name} must be an AntiOverfitVariant")


def _validate_evidence_ref(ref: Any, index: int) -> None:
    name = f"evidence_refs[{index}]"
    if not isinstance(ref, EvidenceRef):
        raise D10ContractError(f"{name} must be an EvidenceRef")
    _check_str(ref.locator_id, f"{name}.locator_id")


def _validate_source_pair(pair: Any, index: int) -> None:
    name = f"source_revision_content_pairs[{index}]"
    if not isinstance(pair, SourceRevisionPair):
        raise D10ContractError(f"{name} must be a SourceRevisionPair")
    _check_str(pair.revision_id, f"{name}.revision_id")
    _check_hash(pair.content_hash, f"{name}.content_hash")


def validate_typed_input(typed: D10TypedInput) -> None:
    """Closed validation of a parsed typed bundle.

    Every envelope field is checked against the frozen exact keys and closed
    vocabularies; structural consistency (member refs, visibility algebra,
    revision pairs) is re-derived by the evaluator from these typed facts.
    """
    if not isinstance(typed, D10TypedInput):
        raise D10ContractError("typed must be a D10TypedInput")
    _check_str(typed.input_schema, "input_schema")
    _check_str(typed.envelope_id, "envelope_id")
    _check_str(typed.project_ref, "project_ref")
    _check_str(typed.run_ref, "run_ref")
    _check_str(typed.snapshot_ref, "snapshot_ref")
    if not typed.source_revision_content_pairs:
        raise D10ContractError("source_revision_content_pairs must be non-empty")
    for index, pair in enumerate(typed.source_revision_content_pairs):
        _validate_source_pair(pair, index)
        # A duplicate revision id is a valid tamper fixture; the evaluator maps
        # it to the ``duplicate_content_identity`` integrity gate, so it must
        # survive shape validation.
    _validate_scope_binding(typed.project_scope_binding, "project_scope_binding")
    _validate_mode_contract(typed.mode_contract, "mode_contract")
    _validate_signal_definition(typed.signal_definition, "signal_definition")
    _validate_legal_matrix_row(typed.legal_matrix_row, "legal_matrix_row")
    _validate_expected_set(typed.expected_set, "expected_set")
    for index, window in enumerate(typed.analysis_windows):
        _validate_window(window, index)
    if not typed.analysis_windows:
        raise D10ContractError("analysis_windows must be non-empty")
    _validate_stratum(typed.stratum, "stratum")
    _validate_comparison_gate(typed.comparison_gate, "comparison_gate")
    _validate_window_pair_gate(typed.window_pair_gate, "window_pair_gate")
    _validate_site_ledger(typed.site_ledger, "site_ledger")
    # An empty member set is a legitimate zero-event/empty-table fixture
    # (contract section 9.2: zero events alone are never negative, but the
    # unit may still dispose to no_hit/negative via the rule engine).
    for index, member in enumerate(typed.members):
        _validate_member(member, index)
    _validate_numerator_ledger(typed.numerator_ledger, "numerator_ledger")
    if typed.measure_origin_binding is not None:
        _validate_measure_origin(typed.measure_origin_binding,
                                 "measure_origin_binding")
    _validate_denominator(typed.denominator, "denominator")
    for index, segment in enumerate(typed.time_segments):
        _validate_time_segment(segment, index)
    if typed.opportunity is not None:
        _validate_opportunity(typed.opportunity, "opportunity")
    _validate_analysis_population(typed.analysis_population, "analysis_population")
    for index, coverage in enumerate(typed.coverage):
        _validate_coverage(coverage, index)
    if typed.change_decision is not None:
        _validate_change_decision(typed.change_decision, "change_decision")
    _validate_visibility(typed.visibility_decision, "visibility_decision")
    _validate_query_decision(typed.query_decision, "query_decision")
    _validate_audience_text(typed.audience_text, "audience_text")
    for index, link in enumerate(typed.deep_links):
        _validate_deep_link(link, index)
    if typed.model_evidence is not None:
        _validate_model_evidence(typed.model_evidence, "model_evidence")
    if typed.safety_context is not None:
        _validate_safety_context(typed.safety_context, "safety_context")
    if typed.efficacy_context is not None:
        _validate_efficacy_context(typed.efficacy_context, "efficacy_context")
    _validate_rule_hit(typed.rule_hit, "rule_hit")
    if typed.hotspot is not None:
        _validate_hotspot(typed.hotspot, "hotspot")
    _validate_count_layers(typed.count_layers, "count_layers")
    _validate_evaluation_limits(typed.evaluation_limits, "evaluation_limits")
    _validate_numeric_policy(typed.numeric_policy, "numeric_policy")
    _validate_mutation_context(typed.mutation_context, "mutation_context")
    if typed.anti_overfit_variant is not None:
        _validate_anti_overfit(typed.anti_overfit_variant, "anti_overfit_variant")
    for index, ref in enumerate(typed.evidence_refs):
        _validate_evidence_ref(ref, index)


# ---------------------------------------------------------------------------
# Stable identity (contract section 5)
# ---------------------------------------------------------------------------


def d10_unit_stable_core(typed: D10TypedInput) -> str:
    """Stable core: project|definition|window|stratum|stratum key|comparison
    reference.  Never includes run/snapshot ids, computed values or display
    text."""
    window_stable = (
        typed.analysis_windows[0].analysis_window_stable_id
        if typed.analysis_windows else ""
    )
    return "|".join((
        typed.project_ref,
        typed.signal_definition.signal_definition_id,
        window_stable,
        typed.stratum.stratum_contract_id,
        typed.stratum.stratum_key,
        typed.comparison_gate.comparison_reference_stable_id,
    ))
