"""R4-D08 cross-domain logic slice -- typed contract and validation.

Implements the frozen D08 typed contract (v0.6,
``medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_
20260814.md``) as closed typed definitions for the synthetic/offline
runtime.  The module owns:

* deterministic canonical JSON and content addressing
  (``sha256(canonical_json(value))``);
* the closed typed enumerations (dispositions, resolve statuses, cutoff
  decisions, L0 coverage states, closure states, unmatched/overmatch
  policies, unit grains, signal types, change causes, propagation results,
  temporal relations, integrity stages and error classes);
* frozen dataclasses for every typed object of the ``d08-typed-input-v1``
  container (record nodes, relation rules, cardinality, raw/materialized
  resolve, observed edges, bidirectional joins, n-ary RELID memberships,
  fanout candidate sets, waiver handoffs, propagation objects, identity
  comparisons, visibility decisions, source jumps, authority/coverage/
  scope bindings and the owner-routing decision);
* ``validate_typed_input`` -- exact closed-enum and required-field
  validation of a parsed typed bundle.

The runtime never reads the challenge catalog, oracle, manifest, registry
or the generator, and never branches on case/test/fixture identifiers or
expected text.  All data is synthetic and offline.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field as _dataclass_field
from typing import Any, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Frozen contract identity
# ---------------------------------------------------------------------------

D08_SCHEMA_VERSION = "1.0.0"
D08_TYPED_INPUT_SCHEMA = "d08-typed-input-v1"
D08_UNIT_ALGORITHM_VERSION = "d08_unit_v1"
D08_PUBLIC_IDENTITY_VERSION = "d08_public_v1"
D08_DOMAIN_ID = "D08_cross_domain_logic"

# ---------------------------------------------------------------------------
# Canonical serialization and content addressing
# ---------------------------------------------------------------------------

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _normalize_nfc(value: Any) -> Any:
    """Recursively Unicode-NFC-normalize strings and dict keys."""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_normalize_nfc(item) for item in value]
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(key)): _normalize_nfc(item)
            for key, item in value.items()
        }
    return value


def d08_canonical_json(value: Any) -> str:
    """Deterministic D08 canonical JSON (NFC, sorted keys, compact)."""
    return json.dumps(
        _normalize_nfc(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def d08_sha256_text(text: str) -> str:
    """SHA-256 of a UTF-8 encoded string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def d08_content_hash(value: Any) -> str:
    """Content address of any JSON-able value (hex sha256 of canonical JSON)."""
    return d08_sha256_text(d08_canonical_json(value))


def d08_content_hash_prefixed(value: Any) -> str:
    """Content address with the ``sha256:`` prefix (identity refs)."""
    return "sha256:" + d08_content_hash(value)


def is_sha256_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.match(value))


# ---------------------------------------------------------------------------
# Closed typed enumerations (v0.6 contract)
# ---------------------------------------------------------------------------

L1_DISPOSITIONS: Tuple[str, ...] = (
    "positive", "negative", "boundary", "not_applicable", "not_evaluable",
)
D08_ACTIONS: Tuple[str, ...] = (
    "evaluate_and_own", "consume_only", "handoff_only", "context_only",
    "routing_gate",
)
RESOLVE_STATUSES: Tuple[str, ...] = (
    "unique", "ambiguous", "not_found", "wrong_subject_or_site", "not_evaluable",
)
CUTOFF_DECISIONS: Tuple[str, ...] = (
    "in_cutoff", "out_of_cutoff", "spans_cutoff", "time_missing_not_evaluable",
)
L0_STATUSES: Tuple[str, ...] = (
    "covered", "missing", "partial", "truncated", "not_evaluable", "failed",
)
CLOSURE_STATES: Tuple[str, ...] = ("full_set", "explicit_empty", "missing")
UNMATCHED_POLICIES: Tuple[str, ...] = (
    "positive_missing_required", "not_evaluable_coverage", "not_applicable",
)
OVERMATCH_POLICIES: Tuple[str, ...] = (
    "positive_forbidden_edge", "boundary_multi_model", "allowed",
)
UNIT_GRAINS: Tuple[str, ...] = (
    "per_left_anchor_slot", "per_right_anchor_slot", "per_explicit_rel_instance",
    "per_propagation_derived_object", "routing_or_coverage_gate",
)
SIGNAL_TYPES: Tuple[str, ...] = (
    "explicit_link_resolve", "reverse_cardinality", "identity_collision",
    "temporal_impossibility", "propagation_lineage", "identity_fanout_exceeded",
    "routing_or_coverage_gate",
)
GATE_SIGNAL_TYPES: Tuple[str, ...] = (
    "cutoff_boundary_gate", "identity_fanout_exceeded", "routing_ambiguity_gate",
)
EDGE_DIRECTIONS: Tuple[str, ...] = ("forward", "reverse")
DIRECTIONALITIES: Tuple[str, ...] = ("directed", "bidirectional", "undirected")
CHANGE_CAUSES: Tuple[str, ...] = ("data", "rule_or_mapping", "algorithm")
DERIVED_OBJECT_TYPES: Tuple[str, ...] = (
    "producer_declared_derived_value", "producer_declared_grade_ref",
    "producer_declared_trend_ref", "producer_declared_relationship_ref",
)
PROPAGATION_RESULTS: Tuple[str, ...] = (
    "in_sync", "stale", "derived_missing", "producer_not_evaluable",
    "ambiguous_chain", "not_applicable", "lineage_supersede_handoff",
)
TEMPORAL_RELATIONS: Tuple[str, ...] = (
    "before", "equal", "after", "overlap", "contains", "contained_by",
)
INTEGRITY_STAGES: Tuple[str, ...] = (
    "run_snapshot_identity",
    "subject_spine_identity",
    "producer_coverage",
    "rule_authority",
    "record_node_identity",
    "correction_chain_lineage",
    "owner_routing",
    "expected_set_admission",
    "producer_consumption_binding",
)
INTEGRITY_ERROR_CLASSES: Tuple[str, ...] = (
    "snapshot_identity_mismatch",
    "subject_spine_identity_mismatch",
    "producer_l0_missing",
    "producer_l0_partial",
    "producer_l0_truncated",
    "producer_l0_not_evaluable",
    "producer_l0_failed",
    "authority_locator_missing",
    "authority_hash_mismatch",
    "authority_window_excludes",
    "node_content_hash_mismatch",
    "node_locator_missing",
    "correction_chain_incomplete",
    "expected_set_admission_failed",
    "routing_ambiguity_gate",
    "producer_binding_scope_mismatch",
    "obligation_identity_missing",
    "evaluator_admission_empty",
)
TIME_PRECISIONS: Tuple[str, ...] = ("day", "month", "year", "datetime")
TIME_KINDS: Tuple[str, ...] = ("point", "interval", "partial_point")
TIMEZONE_STATES: Tuple[str, ...] = ("present", "missing", "incomparable")
IDENTITY_RESULTS: Tuple[str, ...] = ("matched", "distinct", "ambiguous")
LINEAGE_FINGERPRINT_STATES: Tuple[str, ...] = ("intact", "broken_chain", "mismatch")
RELATION_PAYLOAD_STATUSES: Tuple[str, ...] = ("valid", "wrong_subject_or_site")
NODE_CONTENT_HASH_STATES: Tuple[str, ...] = ("valid", "invalid")
# Closed identity decision codes.  These are the structured semantics behind
# the identity comparison: each code maps to exactly one disposition and
# counterevidence count in the evaluator.  ``unclassified`` means no closed
# code applies (the comparison then falls back to the duplicate-policy and
# default paths, mirroring the frozen verifier's fallthrough).
IDENTITY_DECISION_CODES: Tuple[str, ...] = (
    "unclassified",
    # positive
    "alias_same_identity", "duplicate_content_same_identity",
    "collision_across_files", "collision_across_sheets",
    "same_identity_different_subject", "same_identity_different_site",
    "same_identity_different_role", "wrong_subject_assignment",
    "wrong_site_assignment", "same_stable_identity_subjects",
    # negative (no counterevidence)
    "fp_same_text_distinct_identity", "alias_distinct_identities",
    "duplicate_content_distinct_identity", "same_event_different_text",
    "revision_history_not_duplicate", "raw_mirror_exemption_documented",
    "text_equality_not_identity", "date_revision_same_classifier",
    # negative with documented modelling-rule counterevidence
    "split_with_rule", "merge_with_rule", "stable_event_merge_with_rule",
    # boundary
    "split_without_rule", "merge_without_rule",
    # not_evaluable
    "operand_unknown", "dedup_keys_uncovered",
)


class D08ContractError(Exception):
    """Closed-enum or required-field violation of a D08 typed object."""


def _check_closed(name: str, value: Any, allowed: Sequence[str]) -> None:
    if value not in allowed:
        raise D08ContractError(f"{name} must be one of {allowed!r}, got {value!r}")


def _check_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise D08ContractError(f"{name} must be a non-empty string, got {value!r}")
    return value


def _check_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise D08ContractError(f"{name} must be a bool, got {value!r}")
    return value


def _check_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise D08ContractError(f"{name} must be an int, got {value!r}")
    return value


def _check_list(value: Any, name: str) -> list:
    if not isinstance(value, list):
        raise D08ContractError(f"{name} must be a list, got {value!r}")
    return value


# ---------------------------------------------------------------------------
# Typed objects (every section of ``d08-typed-input-v1``)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StableRecordIdentity:
    stable_record_id: str
    project_ref: str
    subject_ref: str
    site_ref: str
    domain_id: str
    semantic_role: str
    correction_chain_head: Optional[str] = None


@dataclass(frozen=True)
class CutoffDecision:
    decision: str
    reason_codes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class RecordNode:
    record_node_id: str
    stable_record_identity: StableRecordIdentity
    accepted_snapshot_ref: str
    source_revision: str
    record_status: str
    cutoff_decision: CutoffDecision
    time_ref_ids: Tuple[str, ...] = ()
    visit_ref_ids: Tuple[str, ...] = ()
    accepted_source_field_values: Mapping[str, Any] = _dataclass_field(default_factory=dict)
    unit_value_role: str = "record"
    locator_ids: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()
    content_hash: str = ""
    content_hash_state: str = "valid"


@dataclass(frozen=True)
class TimeRef:
    time_ref_id: str
    value: str = ""
    precision: str = "day"
    kind: str = "point"
    end_value: str = ""
    end_precision: str = ""
    timezone: str = ""
    timezone_state: str = "present"
    source_locator_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class TemporalComparison:
    comparison_id: str
    left_time_ref_id: str
    right_time_ref_id: str
    expected_relation: Optional[str] = None
    allowed_relation_set: Tuple[str, ...] = ()
    left_endpoint_openness: str = "closed"
    right_endpoint_openness: str = "closed"
    timezone_state: str = "present"
    precision_level: str = ""
    relation_rule_id: str = ""


@dataclass(frozen=True)
class IdentityOperandResult:
    operand_id: str
    equality_result: str = "unknown"


@dataclass(frozen=True)
class IdentityComparison:
    comparison_id: str
    relation_rule_id: str = ""
    final_result: str = "matched"
    decision_code: str = "unclassified"
    operand_equality_results: Tuple[IdentityOperandResult, ...] = ()
    reason_codes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class IdentityOperand:
    operand_id: str
    value: str = ""
    normalized_value: str = ""
    alias_group_id: str = ""


@dataclass(frozen=True)
class RuleWindow:
    window_kind: str = "rule_window"
    start: str = ""
    end: str = ""


@dataclass(frozen=True)
class RelationRule:
    rule_id: str
    version: str = "1"
    rule_hash: str = ""
    owner_routing_ref: str = ""
    clinical_relationship_type: str = ""
    left_role_constraint: str = ""
    unit_anchor_role: str = ""
    evidence_set_role: str = ""
    unit_grain: str = "per_left_anchor_slot"
    directionality: str = "directed"
    identity_operand_ids: Tuple[str, ...] = ()
    time_operand_ids: Tuple[str, ...] = ()
    shared_precision: str = ""
    normalization_preconditions: Tuple[str, ...] = ()
    expected_relation: Optional[str] = None
    forbidden_relation: Optional[str] = None
    allowed_relation_set: Tuple[str, ...] = ()
    required_relation: Optional[str] = None
    required_producer_domains: Tuple[str, ...] = ()
    applicability_window: Optional[RuleWindow] = None
    authority_locator_id: str = ""
    max_unidentified_fanout: int = 5
    duplicate_policy_ref: str = ""
    cardinality_ref: str = ""
    owner_domain: str = "D08"
    algorithm_version: str = D08_UNIT_ALGORITHM_VERSION


@dataclass(frozen=True)
class CardinalitySpec:
    cardinality_id: str
    unit_grain: str = "per_left_anchor_slot"
    left_min: int = 0
    left_max: int = 1
    right_min: int = 0
    right_max: int = 1
    unbounded: bool = False
    bidirectional: bool = False
    reverse_required: bool = False
    unmatched_required_policy: str = "positive_missing_required"
    overmatch_policy: str = "allowed"


@dataclass(frozen=True)
class DuplicatePolicy:
    policy_id: str
    version: str = "1"
    dedup_keys: Tuple[str, ...] = ()
    raw_materialized_mirror_exemption: bool = False
    stable_event_collision_semantics: str = "independent_events"
    modeling_rule_ref: str = ""


@dataclass(frozen=True)
class RawLinkRecord:
    raw_link_id: str
    subject_ref: str = ""
    domain_id: str = ""
    idvar: str = ""
    idvarval: str = ""
    relid: str = ""
    reltype: str = ""
    source_locator_ids: Tuple[str, ...] = ()
    raw_content_hash: str = ""


@dataclass(frozen=True)
class ResolveDecision:
    resolve_decision_id: str
    raw_link_id: str
    status: str
    materialized_record_node_ids: Tuple[str, ...] = ()
    rejected_candidate_ids: Tuple[str, ...] = ()
    reason_codes: Tuple[str, ...] = ()
    l0_coverage_status: str = "covered"


@dataclass(frozen=True)
class ObservedEdge:
    edge_id: str
    relation_rule_id: str = ""
    direction: str = "forward"
    edge_directionality: str = "directed"
    left_stable_identity: str = ""
    right_stable_identity: str = ""
    explicit_rel_instance_id: str = ""
    recorded_operands: Tuple[str, ...] = ()


@dataclass(frozen=True)
class BidirectionalJoin:
    join_id: str
    relation_rule_id: str = ""
    forward_edge_refs: Tuple[str, ...] = ()
    reverse_edge_refs: Tuple[str, ...] = ()
    forward_identity_set: Tuple[str, ...] = ()
    reverse_identity_set: Tuple[str, ...] = ()


@dataclass(frozen=True)
class RelInstanceMembership:
    rel_instance_id: str
    relation_rule_id: str = ""
    unit_grain: str = "per_explicit_rel_instance"
    member_ids: Tuple[str, ...] = ()
    raw_link_ids: Tuple[str, ...] = ()
    raw_link_bijection: Mapping[str, str] = _dataclass_field(default_factory=dict)


@dataclass(frozen=True)
class FanoutCandidateSet:
    fanout_set_id: str
    relation_rule_id: str = ""
    obligation_side_identity: str = ""
    candidate_identities: Tuple[str, ...] = ()
    max_unidentified_fanout: int = 0
    has_unique_identity_or_relid: bool = False


@dataclass(frozen=True)
class WaiverHandoff:
    handoff_id: str
    project_ref: str = ""
    run_ref: str = ""
    subject_ref: str = ""
    site_ref: str = ""
    scope_binding_id: str = ""
    cutoff: str = ""
    owner_domain: str = ""
    relation_rule_id: str = ""
    anchor_stable_identity: str = ""
    closure_state: str = "missing"
    authorized_object_refs: Tuple[str, ...] = ()
    authority_locator_ids: Tuple[str, ...] = ()
    producer_version: str = ""
    lineage_hash: str = ""


@dataclass(frozen=True)
class PropagationObject:
    propagation_id: str
    source_record_node_id: str = ""
    change_cause: str = "data"
    source_revision: str = ""
    declared_consumed_revision: str = ""
    actual_consumed_revision: str = ""
    changed_fields: Tuple[str, ...] = ()
    consumed_field_intersection: Tuple[str, ...] = ()
    derived_object_id: str = ""
    derived_object_type: str = ""
    lineage_fingerprint: str = ""
    lineage_fingerprint_state: str = "intact"
    old_derived_object_ref: str = ""
    new_derived_object_ref: str = ""


@dataclass(frozen=True)
class DerivedObject:
    derived_object_id: str
    derived_object_type: str = ""
    producer_object_id: str = ""
    producer_version: str = ""
    producer_hash: str = ""
    declared_consumed_revision: str = ""
    declared_consumed_fields: Tuple[str, ...] = ()
    source_locator_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ProducerConsumptionBinding:
    binding_id: str
    producer_object_id: str = ""
    producer_object_hash: str = ""
    producer_version: str = ""
    purpose: str = ""
    permitted_outputs: Tuple[str, ...] = ()
    scope_equality: bool = True


@dataclass(frozen=True)
class AuthorityBinding:
    authority_binding_id: str
    authority_kind: str = ""
    authority_version: str = ""
    authority_hash: str = ""
    applicability_window: Optional[RuleWindow] = None


@dataclass(frozen=True)
class CoverageStatus:
    producer_domain: str
    l0_status: str = "covered"
    accepted_current: bool = True
    coverage_locator_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class VisibilityDecision:
    visibility_decision_id: str
    audience_anchor_rule: str = "obligation_side"
    audience_lexicon_ref: str = ""
    evaluation_node_set: Tuple[str, ...] = ()
    projectable_node_set: Tuple[str, ...] = ()
    blinded_node_ids: Tuple[str, ...] = ()
    forbidden_node_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceJump:
    jump_target_id: str
    target_kind: str = "record_node"
    target_object_id: str = ""
    source_locator_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceLocator:
    source_locator_id: str
    source_file_ref: str = ""
    canonical_location: str = ""
    locator_kind: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class AudienceLexicon:
    lexicon_id: str
    version: str = "1"
    required_sentence_patterns: Tuple[str, ...] = ("依据", "发现", "行动项")
    allowed_domain_labels: Tuple[str, ...] = ()
    forbidden_internal_tokens: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ScopeBinding:
    scope_binding_id: str
    project_ref: str = ""
    run_ref: str = ""
    subject_ref: str = ""
    site_ref: str = ""
    episode_key: str = ""
    monitoring_mode: str = ""
    accepted_snapshot_ref: str = ""
    snapshot_as_of: str = ""
    clinical_event_cutoff: str = ""
    producer_version: str = ""
    lineage_hash: str = ""


@dataclass(frozen=True)
class SharedSpineBinding:
    shared_spine_ref: str = ""
    scope_equality_decision: str = "equal"


@dataclass(frozen=True)
class MutationContext:
    mutation_class: str = "none"
    mutation_description: str = ""
    substantive_input_hash: str = ""
    base_fixture_id: Optional[str] = None
    variant_of: Optional[str] = None


@dataclass(frozen=True)
class AntiOverfitVariant:
    variant_id: str
    base_fixture_id: str
    surface_changes: Tuple[str, ...] = ()
    semantic_equivalence_ref: str = ""


@dataclass(frozen=True)
class OwnerRouting:
    candidate_problem_kind: str = ""
    clinical_claim_token: str = ""
    owner_domain: str = ""
    d08_action: str = ""
    left_role: str = ""
    right_role: str = ""
    source: str = ""
    rule_refs: Tuple[str, ...] = ()
    locator_ids: Tuple[str, ...] = ()
    required_producer_domains: Tuple[str, ...] = ()


@dataclass(frozen=True)
class D08TypedInput:
    """Complete typed bundle for one D08 evaluation run (``d08-typed-input-v1``)."""

    input_schema: str = D08_TYPED_INPUT_SCHEMA
    relation_payload_status: str = "valid"
    scope_binding: Optional[ScopeBinding] = None
    shared_spine_binding: Optional[SharedSpineBinding] = None
    owner_route: Optional[OwnerRouting] = None
    record_nodes: Tuple[RecordNode, ...] = ()
    time_refs: Tuple[TimeRef, ...] = ()
    temporal_comparisons: Tuple[TemporalComparison, ...] = ()
    identity_comparisons: Tuple[IdentityComparison, ...] = ()
    identity_operands: Tuple[IdentityOperand, ...] = ()
    relation_rules: Tuple[RelationRule, ...] = ()
    cardinality_specs: Tuple[CardinalitySpec, ...] = ()
    duplicate_policies: Tuple[DuplicatePolicy, ...] = ()
    raw_links: Tuple[RawLinkRecord, ...] = ()
    resolve_decisions: Tuple[ResolveDecision, ...] = ()
    observed_edges: Tuple[ObservedEdge, ...] = ()
    bidirectional_joins: Tuple[BidirectionalJoin, ...] = ()
    rel_instance_memberships: Tuple[RelInstanceMembership, ...] = ()
    fanout_candidate_sets: Tuple[FanoutCandidateSet, ...] = ()
    waiver_handoffs: Tuple[WaiverHandoff, ...] = ()
    propagation_objects: Tuple[PropagationObject, ...] = ()
    derived_objects: Tuple[DerivedObject, ...] = ()
    producer_consumption_bindings: Tuple[ProducerConsumptionBinding, ...] = ()
    authority_bindings: Tuple[AuthorityBinding, ...] = ()
    coverage_status: Tuple[CoverageStatus, ...] = ()
    visibility_decision: Optional[VisibilityDecision] = None
    source_jump_registry: Tuple[SourceJump, ...] = ()
    source_locators: Tuple[SourceLocator, ...] = ()
    audience_lexicon: Optional[AudienceLexicon] = None
    visit_refs: Tuple[Any, ...] = ()
    mutation_context: Optional[MutationContext] = None
    anti_overfit_variant: Optional[AntiOverfitVariant] = None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate_rule_window(window: Any, name: str) -> None:
    if not isinstance(window, RuleWindow):
        raise D08ContractError(f"{name} must be a RuleWindow")
    if window.window_kind not in ("rule_window",):
        raise D08ContractError(f"{name}.window_kind closed: {window.window_kind!r}")


def _validate_identity(identity: Any, name: str) -> None:
    if not isinstance(identity, StableRecordIdentity):
        raise D08ContractError(f"{name} must be a StableRecordIdentity")
    for f in ("stable_record_id", "project_ref", "subject_ref", "site_ref",
              "domain_id", "semantic_role"):
        _check_str(getattr(identity, f), f"{name}.{f}")
    # correction_chain_head is optional: None means the correction-chain
    # lineage is absent (a structured fact, never a synthetic sentinel id).
    if identity.correction_chain_head is not None:
        _check_str(identity.correction_chain_head, f"{name}.correction_chain_head")


def _validate_record_node(node: Any, index: int) -> None:
    name = f"record_nodes[{index}]"
    if not isinstance(node, RecordNode):
        raise D08ContractError(f"{name} must be a RecordNode")
    _check_str(node.record_node_id, f"{name}.record_node_id")
    _check_str(node.accepted_snapshot_ref, f"{name}.accepted_snapshot_ref")
    _check_str(node.source_revision, f"{name}.source_revision")
    _check_str(node.record_status, f"{name}.record_status")
    _validate_identity(node.stable_record_identity, f"{name}.stable_record_identity")
    if not isinstance(node.cutoff_decision, CutoffDecision):
        raise D08ContractError(f"{name}.cutoff_decision must be a CutoffDecision")
    _check_closed(f"{name}.cutoff_decision.decision", node.cutoff_decision.decision,
                  CUTOFF_DECISIONS)
    _check_str(node.content_hash, f"{name}.content_hash")
    if not is_sha256_hex(node.content_hash):
        raise D08ContractError(f"{name}.content_hash must be sha256 hex")
    _check_closed(f"{name}.content_hash_state", node.content_hash_state,
                  NODE_CONTENT_HASH_STATES)
    _check_list(list(node.locator_ids), f"{name}.locator_ids")


def validate_typed_input(typed: D08TypedInput) -> None:
    """Closed validation of a parsed typed bundle.

    Raises :class:`D08ContractError` on the first violation.  No expected
    leaf payload, case identifier or acceptance artifact is involved.
    """
    if not isinstance(typed, D08TypedInput):
        raise D08ContractError("typed bundle must be a D08TypedInput")
    if typed.input_schema != D08_TYPED_INPUT_SCHEMA:
        raise D08ContractError(
            f"input_schema must be {D08_TYPED_INPUT_SCHEMA!r}, got {typed.input_schema!r}")
    _check_closed("relation_payload_status", typed.relation_payload_status,
                  RELATION_PAYLOAD_STATUSES)
    if typed.scope_binding is not None:
        if not isinstance(typed.scope_binding, ScopeBinding):
            raise D08ContractError("scope_binding must be a ScopeBinding")
        _check_str(typed.scope_binding.scope_binding_id, "scope_binding.scope_binding_id")
        _check_str(typed.scope_binding.accepted_snapshot_ref,
                   "scope_binding.accepted_snapshot_ref")
        _check_str(typed.scope_binding.subject_ref, "scope_binding.subject_ref")
    for index, node in enumerate(typed.record_nodes):
        _validate_record_node(node, index)
    for index, tref in enumerate(typed.time_refs):
        name = f"time_refs[{index}]"
        if not isinstance(tref, TimeRef):
            raise D08ContractError(f"{name} must be a TimeRef")
        _check_str(tref.time_ref_id, f"{name}.time_ref_id")
        _check_closed(f"{name}.precision", tref.precision, TIME_PRECISIONS)
        _check_closed(f"{name}.kind", tref.kind, TIME_KINDS)
        _check_closed(f"{name}.timezone_state", tref.timezone_state, TIMEZONE_STATES)
    for index, tc in enumerate(typed.temporal_comparisons):
        name = f"temporal_comparisons[{index}]"
        if not isinstance(tc, TemporalComparison):
            raise D08ContractError(f"{name} must be a TemporalComparison")
        _check_str(tc.comparison_id, f"{name}.comparison_id")
        _check_str(tc.left_time_ref_id, f"{name}.left_time_ref_id")
        _check_str(tc.right_time_ref_id, f"{name}.right_time_ref_id")
        _check_closed(f"{name}.timezone_state", tc.timezone_state, TIMEZONE_STATES)
        if tc.expected_relation is not None:
            _check_closed(f"{name}.expected_relation", tc.expected_relation,
                          TEMPORAL_RELATIONS)
        for rel in tc.allowed_relation_set:
            _check_closed(f"{name}.allowed_relation_set", rel, TEMPORAL_RELATIONS)
    for index, ic in enumerate(typed.identity_comparisons):
        name = f"identity_comparisons[{index}]"
        if not isinstance(ic, IdentityComparison):
            raise D08ContractError(f"{name} must be an IdentityComparison")
        _check_closed(f"{name}.final_result", ic.final_result, IDENTITY_RESULTS)
        _check_closed(f"{name}.decision_code", ic.decision_code,
                      IDENTITY_DECISION_CODES)
    for index, rule in enumerate(typed.relation_rules):
        name = f"relation_rules[{index}]"
        if not isinstance(rule, RelationRule):
            raise D08ContractError(f"{name} must be a RelationRule")
        _check_str(rule.rule_id, f"{name}.rule_id")
        _check_str(rule.clinical_relationship_type, f"{name}.clinical_relationship_type")
        _check_closed(f"{name}.directionality", rule.directionality, DIRECTIONALITIES)
        _check_closed(f"{name}.unit_grain", rule.unit_grain, UNIT_GRAINS)
        _check_str(rule.owner_domain, f"{name}.owner_domain")
        _check_list(list(rule.required_producer_domains),
                    f"{name}.required_producer_domains")
        if rule.applicability_window is not None:
            _validate_rule_window(rule.applicability_window,
                                  f"{name}.applicability_window")
    for index, card in enumerate(typed.cardinality_specs):
        name = f"cardinality_specs[{index}]"
        if not isinstance(card, CardinalitySpec):
            raise D08ContractError(f"{name} must be a CardinalitySpec")
        _check_closed(f"{name}.unmatched_required_policy",
                      card.unmatched_required_policy, UNMATCHED_POLICIES)
        _check_closed(f"{name}.overmatch_policy", card.overmatch_policy,
                      OVERMATCH_POLICIES)
        _check_closed(f"{name}.unit_grain", card.unit_grain, UNIT_GRAINS)
        _check_int(card.left_min, f"{name}.left_min")
        _check_int(card.left_max, f"{name}.left_max")
        _check_int(card.right_min, f"{name}.right_min")
        _check_int(card.right_max, f"{name}.right_max")
    for index, res in enumerate(typed.resolve_decisions):
        name = f"resolve_decisions[{index}]"
        if not isinstance(res, ResolveDecision):
            raise D08ContractError(f"{name} must be a ResolveDecision")
        _check_closed(f"{name}.status", res.status, RESOLVE_STATUSES)
    for index, edge in enumerate(typed.observed_edges):
        name = f"observed_edges[{index}]"
        if not isinstance(edge, ObservedEdge):
            raise D08ContractError(f"{name} must be an ObservedEdge")
        _check_str(edge.edge_id, f"{name}.edge_id")
        _check_closed(f"{name}.direction", edge.direction, EDGE_DIRECTIONS)
        _check_closed(f"{name}.edge_directionality", edge.edge_directionality,
                      DIRECTIONALITIES)
    for index, w in enumerate(typed.waiver_handoffs):
        name = f"waiver_handoffs[{index}]"
        if not isinstance(w, WaiverHandoff):
            raise D08ContractError(f"{name} must be a WaiverHandoff")
        _check_closed(f"{name}.closure_state", w.closure_state, CLOSURE_STATES)
        if w.closure_state == "full_set" and not w.authorized_object_refs:
            raise D08ContractError(f"{name} full_set must list authorized refs")
        if w.closure_state != "full_set" and w.authorized_object_refs:
            raise D08ContractError(f"{name} non-full_set must not carry refs")
    for index, p in enumerate(typed.propagation_objects):
        name = f"propagation_objects[{index}]"
        if not isinstance(p, PropagationObject):
            raise D08ContractError(f"{name} must be a PropagationObject")
        _check_closed(f"{name}.change_cause", p.change_cause, CHANGE_CAUSES)
        _check_closed(f"{name}.lineage_fingerprint_state",
                      p.lineage_fingerprint_state, LINEAGE_FINGERPRINT_STATES)
    for index, d in enumerate(typed.derived_objects):
        name = f"derived_objects[{index}]"
        if not isinstance(d, DerivedObject):
            raise D08ContractError(f"{name} must be a DerivedObject")
        if d.derived_object_type:
            _check_closed(f"{name}.derived_object_type", d.derived_object_type,
                          DERIVED_OBJECT_TYPES)
    for index, cov in enumerate(typed.coverage_status):
        name = f"coverage_status[{index}]"
        if not isinstance(cov, CoverageStatus):
            raise D08ContractError(f"{name} must be a CoverageStatus")
        _check_closed(f"{name}.l0_status", cov.l0_status, L0_STATUSES)
    for index, a in enumerate(typed.authority_bindings):
        name = f"authority_bindings[{index}]"
        if not isinstance(a, AuthorityBinding):
            raise D08ContractError(f"{name} must be an AuthorityBinding")
        if a.applicability_window is not None:
            _validate_rule_window(a.applicability_window, f"{name}.applicability_window")
    if typed.visibility_decision is not None:
        if not isinstance(typed.visibility_decision, VisibilityDecision):
            raise D08ContractError("visibility_decision must be a VisibilityDecision")
    if typed.audience_lexicon is not None:
        if not isinstance(typed.audience_lexicon, AudienceLexicon):
            raise D08ContractError("audience_lexicon must be an AudienceLexicon")
    if typed.mutation_context is not None:
        if not isinstance(typed.mutation_context, MutationContext):
            raise D08ContractError("mutation_context must be a MutationContext")
    if typed.owner_route is not None:
        if not isinstance(typed.owner_route, OwnerRouting):
            raise D08ContractError("owner_route must be an OwnerRouting")
