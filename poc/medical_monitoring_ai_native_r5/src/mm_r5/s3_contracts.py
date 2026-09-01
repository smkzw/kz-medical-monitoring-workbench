"""R5 S3 typed contract surface for the offline project cockpit and center
graph runtime (``medical-monitoring-r5-s3-packet-schema-v0.2``).

Implements, as immutable frozen dataclasses with fail-closed validation, the
authority objects declared by the accepted, independently reviewed machine
authority ``artifacts/medical_monitoring_r5_s3_contract_v0_2``:

* ``packet_schema.json``            (SHA-256 ``839ba88b…``)
* ``exact_overlay.json``            (SHA-256 ``02f5b371…``)
* ``source_pins.json``              (SHA-256 ``f1c369e5…``)
* ``manifest.json`` canonical       (SHA-256 ``be1ec58f…``)
* human contract ``reviews/…v0_2_20260818.md`` (SHA-256 ``9e991731…``)

Scope
-----
* Typed packet objects only: exact keys / cardinality / nullability from the
  frozen schema; closed enums are exact tuples; every enum-typed field is
  validated fail-closed at construction.
* The packet embeds the R4/S1/S2 public authority objects read-only
  (``D09/D10*`` public projections, ``R5AuthorityReceipt``,
  ``SourceRevisionContentPair``, ``R5CurrentRiskSet``, ``R5ChangeBand``,
  ``R5QuantitativeMeasure``, ``R5CenterMapProjection``,
  ``R5ProjectCockpitProjection``, ``R5ProjectionInstance``).  No D09/D10
  typed-input leaf (``Member``, ``SubjectRiskMember``, …) is ever promoted
  to a public authority field.
* Exact named supplemental authorities (closed, no generic ``value``) and
  the root ``R5S3AuthorityPacket`` with the frozen acyclic hash DAG:
  ``packet_id == 'r5-s3-contract:' + audience_replay_content_hash``
  (single-colon grammar), ``audience_replay_content_hash`` covers the
  complete audience payload including low clusters, and
  ``packet_integrity_hash`` covers every other leaf including private
  hidden/evaluation refs and excludes its own dependencies.
* ``validate_s3_authority_packet`` is the fail-closed validator: it re-runs
  the frozen authority-side cross-object invariants against the packet and
  returns ``{"valid": bool, "reasons": tuple of frozen error codes}``.
  Construction itself is fail-closed too: authority-side invariants run at
  construction and a violation raises.
* Nothing here branches on project/case/fixture/test ids, filenames,
  synthetic sentinels, oracles, indexes, mutation classes or hash naming
  conventions (forbidden semantic branches of the frozen schema).  The only
  authority mode is the frozen literal ``synthetic_offline_test_only``.
* This module does not implement the projection layer (current-risk plane
  closure, center-cell closure, change-band emission, closure bidirectionality,
  cockpit aggregation): those renderer-neutral renderers are the worker_02
  projector's domain and consume these exposed authorities.

Canonicalization follows the frozen hash recipe
``utf8_nfc_sorted_keys_compact_json_newline`` (NFC, sorted keys, compact
separators, ``allow_nan=False``, trailing newline) exactly as the accepted
verifier and S2 packet recipe use it.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, fields as dataclass_fields, is_dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from mm_r4.d09_projection import (
    D09AudienceProjection,
    D09HotspotProjection,
    D09ProjectionCountSurface,
    D09R2RiskHandoff,
    D09RiskMarker,
)
from mm_r4.d10_projection import (
    D10AudienceProjection,
    D10CenterPatternRow,
    D10ChangeSection,
    D10HotspotProjection,
    D10ProjectionCountSurface,
    D10ProjectionVersion,
    D10ProjectProjection,
    D10R2RiskHandoff,
    D10RiskMarker,
)
from mm_r5.contracts import (
    R5AuthorityReceipt,
    R5CenterMapProjection,
    R5ChangeBand,
    R5CurrentRiskSet,
    R5ProjectCockpitProjection,
    R5QuantitativeMeasure,
    SourceRevisionContentPair,
)

# ---------------------------------------------------------------------------
# Frozen contract identity
# ---------------------------------------------------------------------------

S3_PACKET_SCHEMA_ID = "medical-monitoring-r5-s3-packet-schema-v0.2"
S3_PACKET_SCHEMA_SHA256 = (
    "839ba88b3fb2620ad7fc9a96722c0bff5bea7202d12cede561a7698b3c938daf")
S3_EXACT_OVERLAY_SHA256 = (
    "02f5b371f236073bd964f3837c916651bf225135036641e9370e1ff363bf69a3")
S3_SOURCE_PINS_SHA256 = (
    "f1c369e5f636e280c72ad470a0b88870789792a9c1a90c5015febe8ea1bcf1eb")
S3_MANIFEST_CONTENT_SHA256 = (
    "be1ec58f6534e4c6843a62238e3b8b96aaa2eb0ceba3fb2c67a9f0261fed3b94")
S3_HUMAN_CONTRACT_SHA256 = (
    "9e99173182c9477bda6b7913d651d77aa5f6f485b6ffe9e8c16856f141ea7fe2")

#: Planner-frozen authority mode (``authority_scope.mode``).
AUTHORITY_MODE_S3 = "synthetic_offline_test_only"
#: Frozen stage status the packet may claim.
STAGE_STATUS_S3 = "R5_S3_CONTRACT_READY_FOR_REVIEW"
#: Literal single-colon packet identity grammar and ref prefixes.
PACKET_ID_PREFIX = "r5-s3-contract"
PACKET_ID_GRAMMAR = "r5-s3-contract:<audience_replay_content_hash>"
RECEIPT_REF_PREFIX = "receipt:"
CLUSTER_REF_PREFIX = "cluster:"
AGGREGATE_REF_PREFIX = "aggregate:"
#: Closed marker-identity prefixes of the public D09/D10 risk markers.
D09_MARKER_PREFIX = "d09_marker:"
D10_MARKER_PREFIX = "d10_marker:"

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class S3ContractError(Exception):
    """Closed-enum, exact-key, cardinality, shape or invariant violation of an
    S3 typed authority object."""


class S3HashMismatchError(S3ContractError):
    """A supplied content hash does not match the deterministic canonical hash
    of the object's non-hash fields (tamper rejection)."""


class S3CanonicalError(Exception):
    """A value cannot be canonicalized (unknown type, non-finite decimal) or
    is not a valid sha256 hex string."""


class S3InvariantError(S3ContractError):
    """One frozen cross-object invariant failed.  ``args[0]`` carries the
    invariant context; ``error_code`` is the frozen schema error code."""

    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code


# ---------------------------------------------------------------------------
# Closed enumerations (exact vocabulary/order from packet_schema.json /
# exact_overlay.json / verifier hard pins)
# ---------------------------------------------------------------------------

S3_DOMAINS: Tuple[str, ...] = (
    "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
    "symptom_efficacy", "protocol_compliance")
S3_SEVERITIES: Tuple[str, ...] = ("critical", "high", "medium", "low")
S3_COVERAGE_STATES: Tuple[str, ...] = (
    "complete", "partial", "truncated", "unknown", "not_applicable")
S3_RATE_STATES: Tuple[str, ...] = ("permitted", "qualified", "not_evaluable")
S3_DENOMINATOR_KINDS: Tuple[str, ...] = (
    "enrolled_subjects", "treated_subjects", "safety_evaluable_subjects",
    "efficacy_evaluable_subjects", "subject_time", "exposure_time")
S3_DENOMINATOR_STATES: Tuple[str, ...] = (
    "closed_positive", "closed_zero", "unknown", "unclosed")
S3_NUMERATOR_KINDS: Tuple[str, ...] = (
    "individual_risk", "center_pattern", "affected_subject", "event",
    "affected_site", "project_signal", "clue", "query")
S3_MEASURE_UNITS: Tuple[str, ...] = (
    "subject", "event", "site", "day", "subject_day", "percent")
S3_CHANGE_KINDS: Tuple[str, ...] = (
    "initial_current", "new", "upgraded", "continued", "downgraded",
    "resolved", "reopened", "superseded", "not_evaluable",
    "not_comparable")
S3_CHANGE_CAUSES: Tuple[str, ...] = (
    "data", "knowledge", "rule", "mapping", "model", "method", "coverage",
    "denominator", "population", "visibility", "mode", "user_decision")
S3_VISIBILITY_STATES: Tuple[str, ...] = ("projectable", "hidden",
                                         "not_evaluable")
S3_PROJECTION_KINDS: Tuple[str, ...] = (
    "d09_audience", "d10_project", "ensemble", "subject_temporal",
    "aemh_history")
S3_TAGGED_VARIANT_KINDS: Tuple[str, ...] = (
    "d09_center_pattern_unit", "d10_project_unit")
S3_MEMBERSHIP_STATES: Tuple[str, ...] = ("projectable", "not_projectable")
S3_MEMBERSHIP_OPERATORS: Tuple[str, ...] = (
    "filter_marker_member_refs", "unique_subject_stable_ids",
    "exact_supplemental_refs")
S3_DENOMINATOR_POLICIES: Tuple[str, ...] = ("applicable", "not_applicable")
S3_RATE_POLICIES: Tuple[str, ...] = (
    "permitted_qualified_not_evaluable", "qualified_not_evaluable",
    "not_evaluable_only")
S3_CONSERVATION_OPERATORS: Tuple[str, ...] = (
    "count_equals_sorted_unique_length", "count_equals_unique_subject_length",
    "non_expandable_requires_not_projectable")
S3_DISABLED_PATH_POLICIES: Tuple[str, ...] = (
    "event_count_disabled", "site_count_disabled", "no_disabled_path")
S3_LIFECYCLE_STATES: Tuple[str, ...] = (
    "current", "proposed_close", "superseded", "resolved")
S3_LIFECYCLE_ACTIONS: Tuple[str, ...] = (
    "create", "continue", "update", "reopen", "propose_close", "supersede")
S3_MARKER_KINDS: Tuple[str, ...] = ("d09", "d10")
S3_CLOSURE_DECISION_KINDS: Tuple[str, ...] = ("resolved",)
S3_SUPPLEMENTAL_KINDS: Tuple[str, ...] = (
    "denominator_authority", "layer_membership_authority",
    "cutoff_authority", "evaluation_limit_authority",
    "coverage_authority", "change_cause_mixture_authority",
    "risk_lifecycle_authority", "closure_authority",
    "clinical_domain_authority")
S3_SOURCE_KINDS: Tuple[str, ...] = (
    "r4_public", "r5_receipt", "named_supplemental", "packet_fixture")
S3_HASH_DOMAINS: Tuple[str, ...] = (
    "private_packet_integrity", "public_audience_authority",
    "public_replay_content")
S3_DISABLED_STATES: Tuple[str, ...] = (
    "no_disabled_path", "enabled", "event_count_disabled",
    "site_count_disabled")
S3_HASH_ALGORITHM: Tuple[str, ...] = ("sha256",)
S3_ERROR_CODES: Tuple[str, ...] = (
    "authority_scope_violation", "typed_input_leaf_promoted",
    "aggregate_identity_mismatch", "tagged_variant_payload_mismatch",
    "hidden_leaf_in_audience_hash", "invalid_coverage_enum",
    "mixed_d10_cause", "resolved_without_lifecycle_authority",
    "marker_required_for_change_kind", "prior_identity_required",
    "prior_ref_required", "not_projectable_supplemental_missing",
    "raw_member_as_current_risk_ref", "aggregate_receipt_missing",
    "layer_recipe_missing", "change_emission_missing",
    "challenge_duplicate_id", "challenge_missing_locator",
    "source_pin_drift", "dangling_ref", "duplicate_ref",
    "schema_key_mismatch", "schema_enum_mismatch",
    "unknown_typed_input_path", "hash_recipe_cycle",
    "coverage_not_evaluable_in_coverage_states", "schema_version_mismatch",
    "artifact_set_mismatch", "source_path_parse_error",
    "not_projectable_ok", "hash_algorithm_mismatch",
    "hash_canonicalization_mismatch", "hash_dag_edge_mismatch",
    "receipt_recipe_mismatch", "receipt_content_hash_mismatch",
    "receipt_ref_prefix_mismatch", "packet_id_grammar_mismatch",
    "packet_id_self_edge", "sourced_from_unknown_path",
    "sourced_from_typed_input", "lifecycle_domain_drift",
    "lifecycle_severity_drift", "lifecycle_action_drift",
    "lifecycle_state_mapping_mismatch", "lifecycle_marker_identity_mismatch",
    "lifecycle_member_expansion_mismatch", "lifecycle_r2_binding_mismatch",
    "current_risk_not_marker_prefix", "current_risk_lifecycle_unresolved",
    "current_risk_marker_unresolved", "cluster_canonical_ref_mismatch",
    "cluster_lifecycle_unresolved", "resolved_closure_unresolved",
    "current_reserved_overlap_check", "propose_close_resolved",
    "measure_unit_mismatch", "denominator_recipe_mismatch",
    "rate_policy_mismatch", "membership_operator_mismatch",
    "conservation_operator_mismatch", "disabled_path_mismatch",
    "clinical_domain_not_in_enum", "severity_not_in_enum",
    "unknown_lifecycle_authority", "unknown_closure_authority",
    "unknown_domain_authority", "domain_authority_binding_mismatch",
    "center_cell_lifecycle_unresolved", "center_cell_domain_drift",
    "center_cell_severity_drift", "center_cell_pattern_upgrade",
    "center_cell_ref_mismatch", "closure_authority_missing",
    "closure_identity_mismatch", "lifecycle_unresolved",
    "proposed_close_no_resolve", "sourced_from_missing",
    "packet_oracle_failed", "challenge_pre_post_identical",
    "challenge_expected_mismatch", "challenge_locator_missing",
    "packet_assert_failed", "source_path_not_in_allowlist",
    "runtime_validator_prefix_check", "low_cluster_not_in_replay",
    "stale_replay_rejected", "manifest_hash_rewrite",
    "layer_recipe_key_mismatch", "change_emission_key_mismatch",
    "hash_dag_key_mismatch", "lifecycle_state_table_mismatch",
    "cross_object_keys_mismatch", "tagged_variant_key_mismatch",
    "source_binding_key_mismatch", "challenge_row_key_mismatch",
    "mutation_op_mismatch", "current_plane_high_mismatch",
    "current_plane_medium_mismatch", "current_plane_low_cluster_mismatch",
    "current_plane_resolved_mismatch", "center_cell_set_mismatch",
    "center_cell_site_mismatch", "center_cell_order_mismatch",
    "center_cell_classification_mismatch", "closure_prior_instance_mismatch",
    "closure_decision_hash_mismatch", "closure_receipt_binding_mismatch",
    "closure_visibility_binding_mismatch", "closure_content_hash_mismatch",
    "closure_orphan", "closure_missing_for_resolved", "closure_ambiguous",
    "current_plane_duplicate_projection", "center_cell_duplicate_member",
)

_ALL_ENUMS: Dict[str, Tuple[str, ...]] = {
    "domain": S3_DOMAINS,
    "severity": S3_SEVERITIES,
    "coverage_state": S3_COVERAGE_STATES,
    "rate_state": S3_RATE_STATES,
    "denominator_kind": S3_DENOMINATOR_KINDS,
    "denominator_state": S3_DENOMINATOR_STATES,
    "numerator_kind": S3_NUMERATOR_KINDS,
    "measure_unit": S3_MEASURE_UNITS,
    "change_kind": S3_CHANGE_KINDS,
    "change_cause": S3_CHANGE_CAUSES,
    "visibility_state": S3_VISIBILITY_STATES,
    "projection_kind": S3_PROJECTION_KINDS,
    "tagged_variant_kind": S3_TAGGED_VARIANT_KINDS,
    "membership_state": S3_MEMBERSHIP_STATES,
    "membership_operator": S3_MEMBERSHIP_OPERATORS,
    "denominator_policy": S3_DENOMINATOR_POLICIES,
    "rate_policy": S3_RATE_POLICIES,
    "conservation_operator": S3_CONSERVATION_OPERATORS,
    "disabled_path_policy": S3_DISABLED_PATH_POLICIES,
    "disabled_state": S3_DISABLED_STATES,
    "lifecycle_state": S3_LIFECYCLE_STATES,
    "lifecycle_action": S3_LIFECYCLE_ACTIONS,
    "marker_kind": S3_MARKER_KINDS,
    "closure_decision_kind": S3_CLOSURE_DECISION_KINDS,
    "supplemental_kind": S3_SUPPLEMENTAL_KINDS,
    "source_kind": S3_SOURCE_KINDS,
    "hash_domain": S3_HASH_DOMAINS,
    "hash_algorithm": S3_HASH_ALGORITHM,
    "receipt_ref_prefix": (RECEIPT_REF_PREFIX,),
    "cluster_ref_prefix": (CLUSTER_REF_PREFIX,),
    "packet_id_grammar": (PACKET_ID_GRAMMAR,),
    "acceptance_boundary": (STAGE_STATUS_S3,),
    "error_code": S3_ERROR_CODES,
}


def s3_enum_values(name: str) -> Tuple[str, ...]:
    """Exact closed-enum vocabulary by frozen schema enum name (fail closed)."""
    try:
        return _ALL_ENUMS[name]
    except KeyError:
        raise S3ContractError(
            f"unknown S3 enum {name!r}; known: "
            f"{sorted(_ALL_ENUMS)!r}") from None


# ---------------------------------------------------------------------------
# Frozen lifecycle state table (overlay ``lifecycle_state_table``)
# ---------------------------------------------------------------------------

#: lifecycle action -> (state, closure_allowed) frozen mapping.
LIFECYCLE_STATE_TABLE: Dict[str, Dict[str, Any]] = {
    "create": {"state": "current", "closure_allowed": False},
    "continue": {"state": "current", "closure_allowed": False},
    "update": {"state": "current", "closure_allowed": False},
    "reopen": {"state": "current", "closure_allowed": False},
    "supersede": {"state": "superseded", "closure_allowed": False},
    "propose_close": {"state": "proposed_close", "closure_allowed": False},
}

#: ``propose_close`` never resolves; the only resolved state requires a
#: closure authority.  These hard semantic pins mirror the overlay table.
PROPOSE_CLOSE_STATE = "proposed_close"
RESOLVED_STATE = "resolved"


# ---------------------------------------------------------------------------
# Frozen structured layer recipes (overlay ``layer_recipes`` / verifier pins)
# ---------------------------------------------------------------------------

#: The eight closed numerator kinds in the fixed recipe order.
S3_LAYERS: Tuple[str, ...] = (
    "individual_risk", "center_pattern", "affected_subject", "event",
    "affected_site", "project_signal", "clue", "query")

PER_LAYER_MEASURE_UNIT: Dict[str, str] = {
    "individual_risk": "subject",
    "center_pattern": "subject",
    "affected_subject": "subject",
    "event": "event",
    "affected_site": "site",
    "project_signal": "subject",
    "clue": "event",
    "query": "event",
}
PER_LAYER_MEMBERSHIP_OPERATOR: Dict[str, str] = {
    "individual_risk": "filter_marker_member_refs",
    "center_pattern": "filter_marker_member_refs",
    "affected_subject": "unique_subject_stable_ids",
    "event": "exact_supplemental_refs",
    "affected_site": "exact_supplemental_refs",
    "project_signal": "filter_marker_member_refs",
    "clue": "exact_supplemental_refs",
    "query": "exact_supplemental_refs",
}
PER_LAYER_DENOMINATOR_POLICY: Dict[str, str] = {
    "individual_risk": "applicable", "center_pattern": "applicable",
    "affected_subject": "applicable", "event": "applicable",
    "affected_site": "applicable", "project_signal": "not_applicable",
    "clue": "not_applicable", "query": "not_applicable",
}
PER_LAYER_RATE_POLICY: Dict[str, str] = {
    "individual_risk": "permitted_qualified_not_evaluable",
    "center_pattern": "permitted_qualified_not_evaluable",
    "affected_subject": "permitted_qualified_not_evaluable",
    "event": "qualified_not_evaluable",
    "affected_site": "permitted_qualified_not_evaluable",
    "project_signal": "not_evaluable_only",
    "clue": "not_evaluable_only",
    "query": "not_evaluable_only",
}
PER_LAYER_CONSERVATION_OPERATOR: Dict[str, str] = {
    "individual_risk": "count_equals_sorted_unique_length",
    "center_pattern": "count_equals_sorted_unique_length",
    "affected_subject": "count_equals_unique_subject_length",
    "event": "count_equals_sorted_unique_length",
    "affected_site": "count_equals_sorted_unique_length",
    "project_signal": "count_equals_sorted_unique_length",
    "clue": "non_expandable_requires_not_projectable",
    "query": "non_expandable_requires_not_projectable",
}
PER_LAYER_DISABLED_PATH_POLICY: Dict[str, str] = {
    "individual_risk": "no_disabled_path",
    "center_pattern": "no_disabled_path",
    "affected_subject": "no_disabled_path",
    "event": "event_count_disabled",
    "affected_site": "site_count_disabled",
    "project_signal": "no_disabled_path",
    "clue": "no_disabled_path",
    "query": "no_disabled_path",
}
PER_LAYER_SOURCE_COUNT_PATHS: Dict[str, Tuple[str, ...]] = {
    "individual_risk": (
        "mm_r4.d10_projection:D10ProjectionCountSurface.individual_risk_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.individual_risk_count"),
    "center_pattern": (
        "mm_r4.d10_projection:D10ProjectionCountSurface.center_pattern_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.center_pattern_count"),
    "affected_subject": (
        "mm_r4.d10_projection:D10ProjectionCountSurface.affected_subject_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.affected_subject_count"),
    "event": (
        "mm_r4.d10_projection:D10ProjectionCountSurface.event_or_outcome_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.event_count"),
    "affected_site": (
        "mm_r4.d10_projection:D10ProjectionCountSurface.affected_site_count",),
    "project_signal": (
        "mm_r4.d10_projection:D10ProjectionCountSurface.project_signal_count",),
    "clue": (
        "mm_r4.d10_projection:D10ProjectionCountSurface.clue_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.clue_count"),
    "query": (
        "mm_r4.d10_projection:D10ProjectionCountSurface.query_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.query_count"),
}
PER_LAYER_MEMBERSHIP_SOURCES: Dict[str, Tuple[str, ...]] = {
    "individual_risk": (
        "mm_r4.d10_projection:D10RiskMarker.member_refs",
        "mm_r4.d09_projection:D09RiskMarker.member_refs"),
    "center_pattern": (
        "mm_r4.d10_projection:D10RiskMarker.member_refs",
        "mm_r4.d09_projection:D09RiskMarker.member_refs"),
    "affected_subject": ("named_supplemental:layer_membership_authority",),
    "event": ("named_supplemental:layer_membership_authority",),
    "affected_site": ("named_supplemental:layer_membership_authority",),
    "project_signal": (
        "named_supplemental:layer_membership_authority",
        "mm_r4.d10_projection:D10RiskMarker.member_refs"),
    "clue": ("named_supplemental:layer_membership_authority",),
    "query": ("named_supplemental:layer_membership_authority",),
}
PER_LAYER_NUMERATOR_UNIT: Dict[str, str] = {
    "individual_risk": "risk_member",
    "center_pattern": "center_pattern_member",
    "affected_subject": "unique_subject",
    "event": "event",
    "affected_site": "site",
    "project_signal": "project_signal",
    "clue": "clue",
    "query": "query_draft",
}
PER_LAYER_CONSERVATION_EXPR: Dict[str, str] = {
    "individual_risk":
        "count == len(projectable individual_risk members) "
        "when membership_state=projectable",
    "center_pattern":
        "count == len(projectable center_pattern members) "
        "when membership_state=projectable",
    "affected_subject":
        "count == len(unique projectable subject ids) "
        "when membership_state=projectable",
    "event":
        "count == len(projectable event refs) when projectable; "
        "suppressed to 0 via not_projectable supplemental "
        "when event_count_disabled",
    "affected_site":
        "count == len(projectable site refs) when projectable; "
        "suppressed to 0 via not_projectable supplemental "
        "when site_count_disabled",
    "project_signal":
        "count == len(projectable project_signal refs) when projectable; "
        "rate_state=not_evaluable (no project-level denominator)",
    "clue":
        "count == len(projectable clue refs) when projectable; "
        "else require not_projectable supplemental record",
    "query":
        "count == len(projectable query refs) when projectable; "
        "else require not_projectable supplemental record",
}


def _require_layer_recipes_present() -> None:
    """Invariant ``layer_recipes_complete``: exactly the eight closed
    numerator kinds each have one frozen structured layer recipe."""
    for layer in S3_LAYERS:
        if layer not in PER_LAYER_MEASURE_UNIT:
            raise S3InvariantError("layer_recipe_missing",
                                   f"missing measure unit for layer {layer!r}")
        if layer not in PER_LAYER_MEMBERSHIP_OPERATOR:
            raise S3InvariantError("layer_recipe_missing",
                                   f"missing membership operator for {layer!r}")
        if layer not in PER_LAYER_DENOMINATOR_POLICY:
            raise S3InvariantError("layer_recipe_missing",
                                   f"missing denominator policy for {layer!r}")
        if layer not in PER_LAYER_RATE_POLICY:
            raise S3InvariantError("layer_recipe_missing",
                                   f"missing rate policy for {layer!r}")
        if layer not in PER_LAYER_CONSERVATION_OPERATOR:
            raise S3InvariantError("layer_recipe_missing",
                                   f"missing conservation op for {layer!r}")
        if layer not in PER_LAYER_DISABLED_PATH_POLICY:
            raise S3InvariantError("layer_recipe_missing",
                                   f"missing disabled path for {layer!r}")
        if layer not in PER_LAYER_SOURCE_COUNT_PATHS:
            raise S3InvariantError("layer_recipe_missing",
                                   f"missing source count paths for {layer!r}")


# ---------------------------------------------------------------------------
# Frozen change-emission table (overlay ``change_emission_table``)
# ---------------------------------------------------------------------------

#: change kind -> frozen emission row (marker present / prior identity / prior
#: ref / R2 action / emit_when_identity_available / lifecycle state effect).
CHANGE_EMISSION_TABLE: Dict[str, Dict[str, Any]] = {
    "initial_current": {"marker_present": "optional", "prior_identity": "none",
                        "prior_ref": "none", "r2_action": "create",
                        "emit_when_identity_available": False,
                        "lifecycle_state_effect": "current"},
    "new": {"marker_present": "required", "prior_identity": "none",
            "prior_ref": "optional", "r2_action": "create",
            "emit_when_identity_available": False,
            "lifecycle_state_effect": "current"},
    "upgraded": {"marker_present": "required", "prior_identity": "required",
                 "prior_ref": "required", "r2_action": "continue",
                 "emit_when_identity_available": True,
                 "lifecycle_state_effect": "current"},
    "continued": {"marker_present": "required", "prior_identity": "required",
                  "prior_ref": "required", "r2_action": "continue",
                  "emit_when_identity_available": True,
                  "lifecycle_state_effect": "current"},
    "downgraded": {"marker_present": "required",
                   "prior_identity": "required", "prior_ref": "required",
                   "r2_action": "continue",
                   "emit_when_identity_available": True,
                   "lifecycle_state_effect": "current"},
    "resolved": {"marker_present": "optional", "prior_identity": "required",
                 "prior_ref": "required", "r2_action": "closure_authority",
                 "emit_when_identity_available": True,
                 "lifecycle_state_effect": "resolved"},
    "reopened": {"marker_present": "required", "prior_identity": "required",
                 "prior_ref": "required", "r2_action": "continue",
                 "emit_when_identity_available": True,
                 "lifecycle_state_effect": "current"},
    "superseded": {"marker_present": "optional", "prior_identity": "required",
                   "prior_ref": "required", "r2_action": "supersede",
                   "emit_when_identity_available": True,
                   "lifecycle_state_effect": "superseded"},
    "not_evaluable": {"marker_present": "forbidden", "prior_identity": "n/a",
                      "prior_ref": "optional", "r2_action": "none",
                      "emit_when_identity_available": False,
                      "lifecycle_state_effect": "no_band"},
    "not_comparable": {"marker_present": "forbidden",
                       "prior_identity": "n/a", "prior_ref": "optional",
                       "r2_action": "none",
                       "emit_when_identity_available": False,
                       "lifecycle_state_effect": "no_band"},
}


def _require_change_emission_present() -> None:
    """Invariant ``change_emission_complete``: every closed change kind has a
    frozen emission row."""
    for kind in S3_CHANGE_KINDS:
        if kind not in CHANGE_EMISSION_TABLE:
            raise S3InvariantError(
                "change_emission_missing", f"missing emission row {kind!r}")
        if CHANGE_EMISSION_TABLE[kind]["lifecycle_state_effect"] not in (
                "current", "resolved", "superseded", "no_band"):
            raise S3InvariantError(
                "change_emission_missing",
                f"invalid lifecycle_state_effect for {kind!r}")


# ---------------------------------------------------------------------------
# Validation helpers (fail closed, never ``assert``)
# ---------------------------------------------------------------------------

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _check_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise S3ContractError(f"{name} must be a non-empty str, got {value!r}")
    return unicodedata.normalize("NFC", value)


def _check_optional_str(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_str(value, name)


def _check_bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise S3ContractError(f"{name} must be a bool, got {value!r}")
    return value


def _check_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise S3ContractError(f"{name} must be an int, got {value!r}")
    return value


def _check_optional_int(value: Any, name: str) -> Optional[int]:
    if value is None:
        return None
    return _check_int(value, name)


def _check_decimal(value: Any, name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise S3ContractError(
            f"{name} must be a Decimal, got {type(value).__name__}: {value!r}")
    return value


def _check_optional_decimal(value: Any, name: str) -> Optional[Decimal]:
    if value is None:
        return None
    return _check_decimal(value, name)


def _check_hash(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.match(value):
        raise S3ContractError(f"{name} must be a 64-hex sha256, got {value!r}")
    return value


def _check_optional_hash(value: Any, name: str) -> Optional[str]:
    if value is None:
        return None
    return _check_hash(value, name)


def _check_closed(value: Any, name: str, allowed: Tuple[str, ...]) -> str:
    if value not in allowed:
        raise S3ContractError(
            f"{name} must be one of {allowed!r}, got {value!r}")
    return value


def _check_optional_closed(
    value: Any, name: str, allowed: Tuple[str, ...],
) -> Optional[str]:
    if value is None:
        return None
    return _check_closed(value, name, allowed)


def _freeze_str_tuple(value: Any, name: str) -> Tuple[str, ...]:
    """Many-str reference collection: list/tuple input, every member a
    non-empty NFC str, sorted (unordered set) and duplicate-free."""
    if not isinstance(value, (list, tuple)):
        raise S3ContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(_check_str(item, f"{name}[]") for item in value)
    if len(set(result)) != len(result):
        raise S3ContractError(
            f"{name} must be duplicate-free, got {sorted(result)!r}")
    return tuple(sorted(result))


def _freeze_hash_tuple(value: Any, name: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise S3ContractError(f"{name} must be a list/tuple, got {value!r}")
    result = tuple(_check_hash(item, f"{name}[]") for item in value)
    if len(set(result)) != len(result):
        raise S3ContractError(
            f"{name} must be duplicate-free, got {sorted(result)!r}")
    return tuple(sorted(result))


def _freeze_sorted_objects(
    value: Any, name: str, cls: type, key_name: str,
) -> Tuple[Any, ...]:
    """Many-cardinality object collection: every item is a ``cls`` instance,
    sorted by the schema-declared ``sorted_unique_by`` key and
    duplicate-free."""
    if not isinstance(value, (list, tuple)):
        raise S3ContractError(f"{name} must be a list/tuple, got {value!r}")
    items = []
    for item in value:
        if not isinstance(item, cls):
            raise S3ContractError(
                f"{name}[] must be a {cls.__name__}, got "
                f"{type(item).__name__}")
        key = _check_str(getattr(item, key_name), f"{name}[].{key_name}")
        items.append((key, item))
    keys = [key for key, _ in items]
    if len(set(keys)) != len(keys):
        raise S3ContractError(
            f"{name} must be sorted-unique by {key_name}, got "
            f"{sorted(keys)!r}")
    return tuple(item for _, item in sorted(items, key=lambda pair: pair[0]))


def _freeze_source_pairs(
    value: Any, name: str,
) -> Tuple[SourceRevisionContentPair, ...]:
    """Many ``SourceRevisionContentPair`` collection: every pair typed,
    sorted-unique by ``revision_id`` (schema ``sorted_unique_by:revision_id``),
    at least one pair (schema ``min_items:1``)."""
    if not isinstance(value, (list, tuple)) or not value:
        raise S3ContractError(
            f"{name} must be a non-empty list/tuple, got {value!r}")
    items = []
    for item in value:
        if not isinstance(item, SourceRevisionContentPair):
            raise S3ContractError(
                f"{name}[] must be a SourceRevisionContentPair, got "
                f"{type(item).__name__}")
        items.append(item)
    seen: set = set()
    for item in items:
        rev = unicodedata.normalize("NFC", item.revision_id)
        if rev in seen:
            raise S3ContractError(
                f"{name} must be unique by revision_id, "
                f"duplicate revision {rev!r}")
        seen.add(rev)
    # Schema declares ``sorted_unique_by:revision_id``; order is normalized
    # (values preserved, order canonicalized).
    return tuple(sorted(items, key=lambda pair: pair.revision_id))


def _require_exact_count(
    items: Tuple[Any, ...], expected: int, name: str,
) -> None:
    if len(items) != expected:
        raise S3ContractError(
            f"{name} must have exactly {expected} items, got {len(items)}")


def _require_min_count(items: Tuple[Any, ...], minimum: int, name: str) -> None:
    if len(items) < minimum:
        raise S3ContractError(
            f"{name} must have at least {minimum} items, got {len(items)}")


def _require_empty(items: Tuple[Any, ...], name: str) -> None:
    if items:
        raise S3ContractError(f"{name} must be exactly empty, got {items!r}")


def _require_nfc(value: str, name: str) -> None:
    if not unicodedata.is_normalized("NFC", value):
        raise S3ContractError(
            f"{name} must be Unicode NFC, got {value!r}")


def _check_obj_type(value: Any, cls: type, name: str) -> None:
    if not isinstance(value, cls):
        raise S3ContractError(
            f"{name} must be a {cls.__name__}, got {type(value).__name__}")


def _check_receipt_ref(value: Any, name: str) -> str:
    result = _check_str(value, name)
    if not result.startswith(RECEIPT_REF_PREFIX):
        raise S3ContractError(
            f"{name} must start with {RECEIPT_REF_PREFIX!r}, got {result!r}")
    return result


def _check_marker_identity_ref(value: Any, name: str) -> str:
    result = _check_str(value, name)
    if not (result.startswith(D09_MARKER_PREFIX)
            or result.startswith(D10_MARKER_PREFIX)):
        raise S3ContractError(
            f"{name} must start with {D09_MARKER_PREFIX!r} or "
            f"{D10_MARKER_PREFIX!r}, got {result!r}")
    return result


# ---------------------------------------------------------------------------
# Canonical serialization (frozen hash_recipes / utf8_nfc_sorted_keys_compact_json_newline)
# ---------------------------------------------------------------------------


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite():
        raise S3CanonicalError(
            f"non-finite decimal cannot be canonicalized: {value!r}")
    normalized = value.normalize()
    if normalized == 0:
        return "0"
    return format(normalized, "f")


def _to_plain(value: Any) -> Any:
    """Recursively convert a packet value to a plain JSON-able structure
    (frozen dataclass -> field dict, Decimal -> deterministic number text).
    Tuple/list items keep their stored order (a many field's canonical order
    is decided at construction by the schema-declared sorted_unique rule)."""
    if isinstance(value, Decimal):
        return _canonical_decimal(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, (list, tuple)):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(key)): _to_plain(item)
                for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {unicodedata.normalize("NFC", field.name):
                _to_plain(getattr(value, field.name))
                for field in dataclass_fields(value)}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and not _is_finite_float(value):
            raise S3CanonicalError(
                f"non-finite float cannot be canonicalized: {value!r}")
        return value
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    raise S3CanonicalError(
        f"unsupported packet leaf type {type(value).__name__}: {value!r}")


def _is_finite_float(value: float) -> bool:
    import math
    return math.isfinite(value)


def s3_canonical_bytes(value: Any) -> bytes:
    """Deterministic canonical bytes of any packet value (NFC, sorted keys,
    compact separators, ``allow_nan=False``, trailing newline)."""
    plain = _to_plain(value)
    text = json.dumps(plain, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False) + "\n"
    return text.encode("utf-8")


def s3_canonical_json(value: Any) -> str:
    """Deterministic canonical JSON text of any packet value (recipe above)."""
    return s3_canonical_bytes(value).decode("utf-8")


def s3_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def s3_object_content_hash(obj: Any) -> str:
    """Content address of one packet object over ALL of its fields (used for
    the ``audience_object_content_hash`` domain and object identities)."""
    return s3_sha256(s3_canonical_bytes(obj))


def s3_content_hash_excluding(obj: Any, excluded: Tuple[str, ...]) -> str:
    """Content address of one packet object excluding the named root fields
    (e.g. ``content_hash`` itself)."""
    if not is_dataclass(obj) or isinstance(obj, type):
        raise S3CanonicalError(
            "s3_content_hash_excluding requires a dataclass instance")
    core = {field.name: getattr(obj, field.name)
            for field in dataclass_fields(obj)
            if field.name not in excluded}
    return s3_sha256(s3_canonical_bytes(core))


# ---------------------------------------------------------------------------
# Recipe helpers (exact identity / receipt / cluster / aggregate bindings)
# ---------------------------------------------------------------------------


def receipt_content_hash(receipt: R5AuthorityReceipt) -> str:
    """``receipt_content_hash = canonical_sha256(complete R5AuthorityReceipt)``
    (schema ``receipt_content_hash_recipe``; the receipt is hashed as a whole,
    no field excluded)."""
    return s3_sha256(s3_canonical_bytes(receipt))


def authority_receipt_ref(receipt: R5AuthorityReceipt) -> str:
    """``authority_receipt_ref = 'receipt:' + receipt_content_hash``."""
    return RECEIPT_REF_PREFIX + receipt_content_hash(receipt)


def unit_content_hash(unit: "R5S3AuthorityUnitTagged") -> str:
    """Canonical content hash of one tagged authority unit excluding its own
    ``content_hash`` field."""
    return s3_content_hash_excluding(unit, ("content_hash",))


def lifecycle_content_hash(obj: Any) -> str:
    return s3_content_hash_excluding(obj, ("content_hash",))


def cluster_content_body(
    authority_receipt_ref: str, domain: str, site_ref: str,
    member_refs: Tuple[str, ...],
) -> Dict[str, Any]:
    """The canonical cluster body whose hash becomes both ``content_hash``
    and ``cluster_ref == 'cluster:' + content_hash`` (schema
    ``equals_prefix_plus_hash:cluster:``)."""
    return {
        "authority_receipt_ref": authority_receipt_ref,
        "domain": domain,
        "site_ref": site_ref,
        "member_refs": list(member_refs),
    }


def cluster_content_hash(authority_receipt_ref: str, domain: str,
                         site_ref: str,
                         member_refs: Tuple[str, ...]) -> str:
    return s3_sha256(s3_canonical_bytes(cluster_content_body(
        authority_receipt_ref, domain, site_ref, member_refs)))


def aggregate_identity_body(
    unit_receipt_refs: Tuple[str, ...],
    risk_marker_identity_hashes: Tuple[str, ...],
    project_ref: str, run_ref: str, snapshot_ref: str,
    cutoff_ref: Optional[str], audience_contract_id: str,
) -> Dict[str, Any]:
    """The canonical aggregate receipt-set identity body whose hash becomes
    ``aggregate_id == 'aggregate:' + hash`` (schema
    ``equals_prefix_plus_hash:aggregate:``)."""
    return {
        "unit_receipt_refs": list(unit_receipt_refs),
        "risk_marker_identity_hashes": list(risk_marker_identity_hashes),
        "project_ref": project_ref,
        "run_ref": run_ref,
        "snapshot_ref": snapshot_ref,
        "cutoff_ref": cutoff_ref,
        "audience_contract_id": audience_contract_id,
    }


def aggregate_identity_id(
    unit_receipt_refs: Tuple[str, ...],
    risk_marker_identity_hashes: Tuple[str, ...],
    project_ref: str, run_ref: str, snapshot_ref: str,
    cutoff_ref: Optional[str], audience_contract_id: str,
) -> str:
    return AGGREGATE_REF_PREFIX + s3_sha256(s3_canonical_bytes(
        aggregate_identity_body(unit_receipt_refs, risk_marker_identity_hashes,
                                project_ref, run_ref, snapshot_ref, cutoff_ref,
                                audience_contract_id)))


def _verify_content_hash(obj: Any, hash_field: str) -> None:
    """Canonical content-hash verification (tamper rejection): a supplied
    hash must equal the deterministic canonical hash of the non-hash fields;
    a missing/``None`` supplied hash is filled in."""
    expected = s3_content_hash_excluding(obj, (hash_field,))
    supplied = getattr(obj, hash_field)
    if supplied is not None and supplied != expected:
        raise S3HashMismatchError(
            f"{type(obj).__name__}.{hash_field} {supplied!r} does not match "
            f"the canonical hash {expected!r}")
    object.__setattr__(obj, hash_field, expected)


def _verify_supplied_content_hash(obj: Any, hash_field: str) -> None:
    """Strict content-hash verification: the supplied hash must already be
    present and correct (the builder never trusts a caller-supplied hash)."""
    expected = s3_content_hash_excluding(obj, (hash_field,))
    supplied = getattr(obj, hash_field)
    if supplied != expected:
        raise S3HashMismatchError(
            f"{type(obj).__name__}.{hash_field} {supplied!r} does not match "
            f"the canonical hash {expected!r}")


# ---------------------------------------------------------------------------
# Named supplemental authorities (exact keys from packet_schema.json)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S3ClinicalDomainAuthority:
    """Synthetic/offline clinical-domain authority: the closed eight-domain
    enum, bound to one complete R5 receipt (visibility + source pairs exact).
    It exists because the D09/D10 public projections carry no clinical domain;
    it never claims to be public R4 authority."""

    authority_id: str
    clinical_domain: str
    receipt_hash: str
    receipt_ref: str
    visibility_decision_id: str
    visibility_decision_hash: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    offline_test_only: bool
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_id", _check_str(
            self.authority_id, "R5S3ClinicalDomainAuthority.authority_id"))
        object.__setattr__(self, "clinical_domain", _check_closed(
            self.clinical_domain,
            "R5S3ClinicalDomainAuthority.clinical_domain", S3_DOMAINS))
        object.__setattr__(self, "receipt_hash", _check_hash(
            self.receipt_hash, "R5S3ClinicalDomainAuthority.receipt_hash"))
        object.__setattr__(self, "receipt_ref", _check_receipt_ref(
            self.receipt_ref, "R5S3ClinicalDomainAuthority.receipt_ref"))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5S3ClinicalDomainAuthority.visibility_decision_id"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5S3ClinicalDomainAuthority.visibility_decision_hash"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3ClinicalDomainAuthority."
                               "source_revision_content_pairs"))
        if self.offline_test_only is not True:
            raise S3ContractError(
                "R5S3ClinicalDomainAuthority.offline_test_only must be True")
        if self.receipt_ref != RECEIPT_REF_PREFIX + self.receipt_hash:
            raise S3ContractError(
                "R5S3ClinicalDomainAuthority.receipt_ref must equal "
                f"{RECEIPT_REF_PREFIX!r} + receipt_hash")
        _verify_supplied_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S3DenominatorAuthority:
    """Quantified supplemental: exact denominator kind/state/value/unit and
    exact member/exclusion refs (no generic ``value``)."""

    authority_id: str
    denominator_kind: str
    denominator_state: str
    denominator_value: Optional[Decimal]
    measure_unit: str
    member_refs: Tuple[str, ...]
    exclusion_refs: Tuple[str, ...]
    receipt_hash: str
    receipt_ref: str
    visibility_decision_id: str
    visibility_decision_hash: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    offline_test_only: bool
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_id", _check_str(
            self.authority_id, "R5S3DenominatorAuthority.authority_id"))
        object.__setattr__(self, "denominator_kind", _check_closed(
            self.denominator_kind,
            "R5S3DenominatorAuthority.denominator_kind",
            S3_DENOMINATOR_KINDS))
        object.__setattr__(self, "denominator_state", _check_closed(
            self.denominator_state,
            "R5S3DenominatorAuthority.denominator_state",
            S3_DENOMINATOR_STATES))
        object.__setattr__(self, "denominator_value", _check_optional_decimal(
            self.denominator_value,
            "R5S3DenominatorAuthority.denominator_value"))
        object.__setattr__(self, "measure_unit", _check_closed(
            self.measure_unit, "R5S3DenominatorAuthority.measure_unit",
            S3_MEASURE_UNITS))
        object.__setattr__(self, "member_refs", _freeze_str_tuple(
            self.member_refs, "R5S3DenominatorAuthority.member_refs"))
        object.__setattr__(self, "exclusion_refs", _freeze_str_tuple(
            self.exclusion_refs, "R5S3DenominatorAuthority.exclusion_refs"))
        object.__setattr__(self, "receipt_hash", _check_hash(
            self.receipt_hash, "R5S3DenominatorAuthority.receipt_hash"))
        object.__setattr__(self, "receipt_ref", _check_receipt_ref(
            self.receipt_ref, "R5S3DenominatorAuthority.receipt_ref"))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5S3DenominatorAuthority.visibility_decision_id"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5S3DenominatorAuthority.visibility_decision_hash"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3DenominatorAuthority."
                               "source_revision_content_pairs"))
        if self.offline_test_only is not True:
            raise S3ContractError(
                "R5S3DenominatorAuthority.offline_test_only must be True")
        if self.receipt_ref != RECEIPT_REF_PREFIX + self.receipt_hash:
            raise S3ContractError(
                "R5S3DenominatorAuthority.receipt_ref must equal "
                f"{RECEIPT_REF_PREFIX!r} + receipt_hash")
        _verify_supplied_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S3LayerMembershipAuthority:
    """Quantified supplemental: exact closed layer / membership_state /
    projectable member refs / non-null source count value+ref / disabled
    state (the D09/D10 public count-surface binding is validated by the
    builder; this object freezes the exact shape)."""

    authority_id: str
    layer: str
    membership_state: str
    member_refs: Tuple[str, ...]
    source_count_value: Decimal
    source_count_ref: str
    disabled_state: str
    receipt_hash: str
    receipt_ref: str
    visibility_decision_id: str
    visibility_decision_hash: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    offline_test_only: bool
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_id", _check_str(
            self.authority_id, "R5S3LayerMembershipAuthority.authority_id"))
        object.__setattr__(self, "layer", _check_closed(
            self.layer, "R5S3LayerMembershipAuthority.layer",
            S3_NUMERATOR_KINDS))
        object.__setattr__(self, "membership_state", _check_closed(
            self.membership_state,
            "R5S3LayerMembershipAuthority.membership_state",
            S3_MEMBERSHIP_STATES))
        object.__setattr__(self, "member_refs", _freeze_str_tuple(
            self.member_refs, "R5S3LayerMembershipAuthority.member_refs"))
        object.__setattr__(self, "source_count_value", _check_decimal(
            self.source_count_value,
            "R5S3LayerMembershipAuthority.source_count_value"))
        object.__setattr__(self, "source_count_ref", _check_str(
            self.source_count_ref,
            "R5S3LayerMembershipAuthority.source_count_ref"))
        object.__setattr__(self, "disabled_state", _check_closed(
            self.disabled_state,
            "R5S3LayerMembershipAuthority.disabled_state",
            S3_DISABLED_STATES))
        object.__setattr__(self, "receipt_hash", _check_hash(
            self.receipt_hash, "R5S3LayerMembershipAuthority.receipt_hash"))
        object.__setattr__(self, "receipt_ref", _check_receipt_ref(
            self.receipt_ref, "R5S3LayerMembershipAuthority.receipt_ref"))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5S3LayerMembershipAuthority.visibility_decision_id"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5S3LayerMembershipAuthority.visibility_decision_hash"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3LayerMembershipAuthority."
                               "source_revision_content_pairs"))
        if self.offline_test_only is not True:
            raise S3ContractError(
                "R5S3LayerMembershipAuthority.offline_test_only must be True")
        if self.receipt_ref != RECEIPT_REF_PREFIX + self.receipt_hash:
            raise S3ContractError(
                "R5S3LayerMembershipAuthority.receipt_ref must equal "
                f"{RECEIPT_REF_PREFIX!r} + receipt_hash")
        _verify_supplied_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S3CutoffAuthority:
    """Supplemental carrying the exact cutoff bound of one unit (cutoff ref
    verbatim from the public projection version / receipt)."""

    authority_id: str
    cutoff_ref: Optional[str]
    receipt_hash: str
    receipt_ref: str
    visibility_decision_id: str
    visibility_decision_hash: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    offline_test_only: bool
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_id", _check_str(
            self.authority_id, "R5S3CutoffAuthority.authority_id"))
        object.__setattr__(self, "cutoff_ref", _check_optional_str(
            self.cutoff_ref, "R5S3CutoffAuthority.cutoff_ref"))
        object.__setattr__(self, "receipt_hash", _check_hash(
            self.receipt_hash, "R5S3CutoffAuthority.receipt_hash"))
        object.__setattr__(self, "receipt_ref", _check_receipt_ref(
            self.receipt_ref, "R5S3CutoffAuthority.receipt_ref"))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5S3CutoffAuthority.visibility_decision_id"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5S3CutoffAuthority.visibility_decision_hash"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3CutoffAuthority."
                               "source_revision_content_pairs"))
        if self.offline_test_only is not True:
            raise S3ContractError(
                "R5S3CutoffAuthority.offline_test_only must be True")
        if self.receipt_ref != RECEIPT_REF_PREFIX + self.receipt_hash:
            raise S3ContractError(
                "R5S3CutoffAuthority.receipt_ref must equal "
                f"{RECEIPT_REF_PREFIX!r} + receipt_hash")
        _verify_supplied_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S3EvaluationLimitAuthority:
    """Supplemental carrying closed evaluation-limit refs and values (copied
    verbatim from public evaluation-identity leaves; never fabricated)."""

    authority_id: str
    evaluation_limit_refs: Tuple[str, ...]
    evaluation_limit_values: Tuple[str, ...]
    receipt_hash: str
    receipt_ref: str
    visibility_decision_id: str
    visibility_decision_hash: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    offline_test_only: bool
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_id", _check_str(
            self.authority_id,
            "R5S3EvaluationLimitAuthority.authority_id"))
        object.__setattr__(self, "evaluation_limit_refs", _freeze_str_tuple(
            self.evaluation_limit_refs,
            "R5S3EvaluationLimitAuthority.evaluation_limit_refs"))
        object.__setattr__(self, "evaluation_limit_values", _freeze_str_tuple(
            self.evaluation_limit_values,
            "R5S3EvaluationLimitAuthority.evaluation_limit_values"))
        object.__setattr__(self, "receipt_hash", _check_hash(
            self.receipt_hash,
            "R5S3EvaluationLimitAuthority.receipt_hash"))
        object.__setattr__(self, "receipt_ref", _check_receipt_ref(
            self.receipt_ref, "R5S3EvaluationLimitAuthority.receipt_ref"))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5S3EvaluationLimitAuthority.visibility_decision_id"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5S3EvaluationLimitAuthority.visibility_decision_hash"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3EvaluationLimitAuthority."
                               "source_revision_content_pairs"))
        if self.offline_test_only is not True:
            raise S3ContractError(
                "R5S3EvaluationLimitAuthority.offline_test_only must be True")
        if self.receipt_ref != RECEIPT_REF_PREFIX + self.receipt_hash:
            raise S3ContractError(
                "R5S3EvaluationLimitAuthority.receipt_ref must equal "
                f"{RECEIPT_REF_PREFIX!r} + receipt_hash")
        _verify_supplied_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S3CoverageAuthority:
    """Supplemental carrying the closed coverage state (never
    ``not_evaluable``: the frozen COVERAGE_STATES enum excludes it)."""

    authority_id: str
    coverage_state: str
    receipt_hash: str
    receipt_ref: str
    visibility_decision_id: str
    visibility_decision_hash: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    offline_test_only: bool
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_id", _check_str(
            self.authority_id, "R5S3CoverageAuthority.authority_id"))
        object.__setattr__(self, "coverage_state", _check_closed(
            self.coverage_state, "R5S3CoverageAuthority.coverage_state",
            S3_COVERAGE_STATES))
        object.__setattr__(self, "receipt_hash", _check_hash(
            self.receipt_hash, "R5S3CoverageAuthority.receipt_hash"))
        object.__setattr__(self, "receipt_ref", _check_receipt_ref(
            self.receipt_ref, "R5S3CoverageAuthority.receipt_ref"))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5S3CoverageAuthority.visibility_decision_id"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5S3CoverageAuthority.visibility_decision_hash"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3CoverageAuthority."
                               "source_revision_content_pairs"))
        if self.offline_test_only is not True:
            raise S3ContractError(
                "R5S3CoverageAuthority.offline_test_only must be True")
        if self.receipt_ref != RECEIPT_REF_PREFIX + self.receipt_hash:
            raise S3ContractError(
                "R5S3CoverageAuthority.receipt_ref must equal "
                f"{RECEIPT_REF_PREFIX!r} + receipt_hash")
        _verify_supplied_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S3ChangeCauseMixtureAuthority:
    """Supplemental carrying a closed change-cause mixture: at least two
    sorted-unique closed causes (a single D10 cause can never be promoted to
    a mixture -- invariant ``mixed_d10_cause``)."""

    authority_id: str
    causes: Tuple[str, ...]
    receipt_hash: str
    receipt_ref: str
    visibility_decision_id: str
    visibility_decision_hash: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    offline_test_only: bool
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_id", _check_str(
            self.authority_id,
            "R5S3ChangeCauseMixtureAuthority.authority_id"))
        causes = tuple(
            _check_closed(cause, "R5S3ChangeCauseMixtureAuthority.causes[]",
                          S3_CHANGE_CAUSES)
            for cause in self.causes)
        if len(set(causes)) != len(causes):
            raise S3ContractError(
                "R5S3ChangeCauseMixtureAuthority.causes must be "
                f"duplicate-free, got {sorted(causes)!r}")
        if len(causes) < 2:
            raise S3ContractError(
                "R5S3ChangeCauseMixtureAuthority.causes must have at least "
                f"2 causes (mixed_d10_cause), got {causes!r}")
        object.__setattr__(self, "causes", tuple(sorted(causes)))
        object.__setattr__(self, "receipt_hash", _check_hash(
            self.receipt_hash,
            "R5S3ChangeCauseMixtureAuthority.receipt_hash"))
        object.__setattr__(self, "receipt_ref", _check_receipt_ref(
            self.receipt_ref,
            "R5S3ChangeCauseMixtureAuthority.receipt_ref"))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5S3ChangeCauseMixtureAuthority.visibility_decision_id"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5S3ChangeCauseMixtureAuthority.visibility_decision_hash"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3ChangeCauseMixtureAuthority."
                               "source_revision_content_pairs"))
        if self.offline_test_only is not True:
            raise S3ContractError(
                "R5S3ChangeCauseMixtureAuthority.offline_test_only must be True")
        if self.receipt_ref != RECEIPT_REF_PREFIX + self.receipt_hash:
            raise S3ContractError(
                "R5S3ChangeCauseMixtureAuthority.receipt_ref must equal "
                f"{RECEIPT_REF_PREFIX!r} + receipt_hash")
        _verify_supplied_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S3ClosureAuthority:
    """Closure authority for a resolved lifecycle: prior public risk identity
    + prior risk instance refs bound to the closure decision id/hash and the
    receipt (bidirectional integrity is the builder/oracle's domain)."""

    closure_authority_id: str
    closure_decision_id: str
    closure_decision_hash: str
    prior_public_risk_identity_ref: str
    prior_risk_instance_ref: str
    receipt_hash: str
    receipt_ref: str
    visibility_decision_id: str
    visibility_decision_hash: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    decision_kind: str
    offline_test_only: bool
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "closure_authority_id", _check_str(
            self.closure_authority_id,
            "R5S3ClosureAuthority.closure_authority_id"))
        object.__setattr__(self, "closure_decision_id", _check_str(
            self.closure_decision_id,
            "R5S3ClosureAuthority.closure_decision_id"))
        object.__setattr__(self, "closure_decision_hash", _check_hash(
            self.closure_decision_hash,
            "R5S3ClosureAuthority.closure_decision_hash"))
        object.__setattr__(self, "prior_public_risk_identity_ref",
                           _check_marker_identity_ref(
                               self.prior_public_risk_identity_ref,
                               "R5S3ClosureAuthority."
                               "prior_public_risk_identity_ref"))
        object.__setattr__(self, "prior_risk_instance_ref", _check_str(
            self.prior_risk_instance_ref,
            "R5S3ClosureAuthority.prior_risk_instance_ref"))
        object.__setattr__(self, "receipt_hash", _check_hash(
            self.receipt_hash, "R5S3ClosureAuthority.receipt_hash"))
        object.__setattr__(self, "receipt_ref", _check_receipt_ref(
            self.receipt_ref, "R5S3ClosureAuthority.receipt_ref"))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5S3ClosureAuthority.visibility_decision_id"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5S3ClosureAuthority.visibility_decision_hash"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3ClosureAuthority."
                               "source_revision_content_pairs"))
        object.__setattr__(self, "decision_kind", _check_closed(
            self.decision_kind, "R5S3ClosureAuthority.decision_kind",
            S3_CLOSURE_DECISION_KINDS))
        if self.offline_test_only is not True:
            raise S3ContractError(
                "R5S3ClosureAuthority.offline_test_only must be True")
        if self.receipt_ref != RECEIPT_REF_PREFIX + self.receipt_hash:
            raise S3ContractError(
                "R5S3ClosureAuthority.receipt_ref must equal "
                f"{RECEIPT_REF_PREFIX!r} + receipt_hash")
        _verify_supplied_content_hash(self, "content_hash")


@dataclass(frozen=True)
class R5S3RiskLifecycleAuthority:
    """Per-marker lifecycle authority: exact marker identity/content bindings,
    R2 handoff id/action, closed severity equal to the public
    ``monitoring_priority`` (critical/unknown/unmapped fail closed), closed
    clinical domain ref, member expansion equal to the public marker member
    set, and a closure authority ref for resolved lifecycles."""

    authority_id: str
    marker_kind: str
    marker_identity_ref: str
    marker_id: str
    marker_content_hash: str
    receipt_hash: str
    receipt_ref: str
    visibility_decision_id: str
    visibility_decision_hash: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]
    clinical_domain_ref: str
    severity: str
    lifecycle_state: str
    lifecycle_action: str
    r2_handoff_id: str
    r2_handoff_ref: str
    member_expansion_refs: Tuple[str, ...]
    closure_authority_ref: Optional[str]
    prior_marker_identity_ref: Optional[str]
    offline_test_only: bool
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_id", _check_str(
            self.authority_id, "R5S3RiskLifecycleAuthority.authority_id"))
        object.__setattr__(self, "marker_kind", _check_closed(
            self.marker_kind, "R5S3RiskLifecycleAuthority.marker_kind",
            S3_MARKER_KINDS))
        object.__setattr__(self, "marker_identity_ref",
                           _check_marker_identity_ref(
                               self.marker_identity_ref,
                               "R5S3RiskLifecycleAuthority."
                               "marker_identity_ref"))
        object.__setattr__(self, "marker_id", _check_str(
            self.marker_id, "R5S3RiskLifecycleAuthority.marker_id"))
        object.__setattr__(self, "marker_content_hash", _check_hash(
            self.marker_content_hash,
            "R5S3RiskLifecycleAuthority.marker_content_hash"))
        object.__setattr__(self, "receipt_hash", _check_hash(
            self.receipt_hash, "R5S3RiskLifecycleAuthority.receipt_hash"))
        object.__setattr__(self, "receipt_ref", _check_receipt_ref(
            self.receipt_ref, "R5S3RiskLifecycleAuthority.receipt_ref"))
        object.__setattr__(self, "visibility_decision_id", _check_str(
            self.visibility_decision_id,
            "R5S3RiskLifecycleAuthority.visibility_decision_id"))
        object.__setattr__(self, "visibility_decision_hash", _check_hash(
            self.visibility_decision_hash,
            "R5S3RiskLifecycleAuthority.visibility_decision_hash"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3RiskLifecycleAuthority."
                               "source_revision_content_pairs"))
        object.__setattr__(self, "clinical_domain_ref", _check_str(
            self.clinical_domain_ref,
            "R5S3RiskLifecycleAuthority.clinical_domain_ref"))
        object.__setattr__(self, "severity", _check_closed(
            self.severity, "R5S3RiskLifecycleAuthority.severity",
            S3_SEVERITIES))
        object.__setattr__(self, "lifecycle_state", _check_closed(
            self.lifecycle_state, "R5S3RiskLifecycleAuthority.lifecycle_state",
            S3_LIFECYCLE_STATES))
        object.__setattr__(self, "lifecycle_action", _check_closed(
            self.lifecycle_action,
            "R5S3RiskLifecycleAuthority.lifecycle_action",
            S3_LIFECYCLE_ACTIONS))
        object.__setattr__(self, "r2_handoff_id", _check_str(
            self.r2_handoff_id,
            "R5S3RiskLifecycleAuthority.r2_handoff_id"))
        object.__setattr__(self, "r2_handoff_ref", _check_str(
            self.r2_handoff_ref, "R5S3RiskLifecycleAuthority.r2_handoff_ref"))
        object.__setattr__(self, "member_expansion_refs", _freeze_str_tuple(
            self.member_expansion_refs,
            "R5S3RiskLifecycleAuthority.member_expansion_refs"))
        object.__setattr__(self, "closure_authority_ref", _check_optional_str(
            self.closure_authority_ref,
            "R5S3RiskLifecycleAuthority.closure_authority_ref"))
        object.__setattr__(self, "prior_marker_identity_ref",
                           _check_optional_str(
                               self.prior_marker_identity_ref,
                               "R5S3RiskLifecycleAuthority."
                               "prior_marker_identity_ref"))
        if self.offline_test_only is not True:
            raise S3ContractError(
                "R5S3RiskLifecycleAuthority.offline_test_only must be True")
        if self.receipt_ref != RECEIPT_REF_PREFIX + self.receipt_hash:
            raise S3ContractError(
                "R5S3RiskLifecycleAuthority.receipt_ref must equal "
                f"{RECEIPT_REF_PREFIX!r} + receipt_hash")
        expected_prefix = (D09_MARKER_PREFIX if self.marker_kind == "d09"
                           else D10_MARKER_PREFIX)
        if not self.marker_identity_ref.startswith(expected_prefix):
            raise S3ContractError(
                "R5S3RiskLifecycleAuthority.marker_identity_ref prefix "
                f"must match marker_kind {self.marker_kind!r}")
        if self.lifecycle_state == "resolved":
            if self.closure_authority_ref is None:
                raise S3ContractError(
                    "R5S3RiskLifecycleAuthority resolved requires "
                    "closure_authority_ref (resolved_without_lifecycle_"
                    "authority)")
        elif self.closure_authority_ref is not None:
            raise S3ContractError(
                "R5S3RiskLifecycleAuthority.closure_authority_ref is only "
                "allowed on resolved lifecycles "
                "(lifecycle_state_mapping_mismatch)")
        mapping = LIFECYCLE_STATE_TABLE.get(self.lifecycle_action)
        if mapping is None:
            raise S3ContractError(
                "R5S3RiskLifecycleAuthority unknown lifecycle_action "
                f"{self.lifecycle_action!r}")
        if self.lifecycle_state not in (mapping["state"], "resolved"):
            raise S3ContractError(
                "R5S3RiskLifecycleAuthority lifecycle_state "
                f"{self.lifecycle_state!r} does not match action "
                f"{self.lifecycle_action!r} table state {mapping['state']!r}")
        if self.lifecycle_action == "propose_close" \
                and self.lifecycle_state == "resolved":
            raise S3ContractError(
                "R5S3RiskLifecycleAuthority propose_close must never "
                "resolve (propose_close_resolved)")
        _verify_supplied_content_hash(self, "content_hash")


# ---------------------------------------------------------------------------
# D09 / D10 payload units (exact keys from packet_schema.json)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S3D09CenterPatternUnit:
    """The D09 public authority payload of one center-pattern unit: the public
    D09 projection objects read-only, the clinical-domain authority ref and
    receipt source pairs."""

    audience: D09AudienceProjection
    counts: D09ProjectionCountSurface
    risk_marker: Optional[D09RiskMarker]
    r2_handoff: Optional[D09R2RiskHandoff]
    hotspots: Tuple[D09HotspotProjection, ...]
    clinical_domain_authority_ref: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]

    def __post_init__(self) -> None:
        _check_obj_type(self.audience, D09AudienceProjection,
                        "R5S3D09CenterPatternUnit.audience")
        _check_obj_type(self.counts, D09ProjectionCountSurface,
                        "R5S3D09CenterPatternUnit.counts")
        if self.risk_marker is not None and not isinstance(
                self.risk_marker, D09RiskMarker):
            raise S3ContractError(
                "R5S3D09CenterPatternUnit.risk_marker must be a "
                f"D09RiskMarker, got {type(self.risk_marker).__name__}")
        if self.r2_handoff is not None and not isinstance(
                self.r2_handoff, D09R2RiskHandoff):
            raise S3ContractError(
                "R5S3D09CenterPatternUnit.r2_handoff must be a "
                f"D09R2RiskHandoff, got {type(self.r2_handoff).__name__}")
        object.__setattr__(self, "hotspots", _freeze_sorted_objects(
            self.hotspots, "R5S3D09CenterPatternUnit.hotspots",
            D09HotspotProjection, "projection_id"))
        object.__setattr__(self, "clinical_domain_authority_ref", _check_str(
            self.clinical_domain_authority_ref,
            "R5S3D09CenterPatternUnit.clinical_domain_authority_ref"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3D09CenterPatternUnit."
                               "source_revision_content_pairs"))


@dataclass(frozen=True)
class R5S3D10ProjectUnit:
    """The D10 public authority payload of one project unit: the public D10
    projection objects read-only, the clinical-domain authority ref and
    receipt source pairs."""

    audience: D10AudienceProjection
    counts: D10ProjectionCountSurface
    version: D10ProjectionVersion
    change_section: D10ChangeSection
    center_distribution: Tuple[D10CenterPatternRow, ...]
    risk_marker: Optional[D10RiskMarker]
    r2_handoff: Optional[D10R2RiskHandoff]
    hotspots: Tuple[D10HotspotProjection, ...]
    project_projection: D10ProjectProjection
    clinical_domain_authority_ref: str
    source_revision_content_pairs: Tuple[SourceRevisionContentPair, ...]

    def __post_init__(self) -> None:
        _check_obj_type(self.audience, D10AudienceProjection,
                        "R5S3D10ProjectUnit.audience")
        _check_obj_type(self.counts, D10ProjectionCountSurface,
                        "R5S3D10ProjectUnit.counts")
        _check_obj_type(self.version, D10ProjectionVersion,
                        "R5S3D10ProjectUnit.version")
        _check_obj_type(self.change_section, D10ChangeSection,
                        "R5S3D10ProjectUnit.change_section")
        _check_obj_type(self.project_projection, D10ProjectProjection,
                        "R5S3D10ProjectUnit.project_projection")
        if self.risk_marker is not None and not isinstance(
                self.risk_marker, D10RiskMarker):
            raise S3ContractError(
                "R5S3D10ProjectUnit.risk_marker must be a D10RiskMarker, got "
                f"{type(self.risk_marker).__name__}")
        if self.r2_handoff is not None and not isinstance(
                self.r2_handoff, D10R2RiskHandoff):
            raise S3ContractError(
                "R5S3D10ProjectUnit.r2_handoff must be a D10R2RiskHandoff, "
                f"got {type(self.r2_handoff).__name__}")
        object.__setattr__(self, "center_distribution",
                           _freeze_sorted_objects(
                               self.center_distribution,
                               "R5S3D10ProjectUnit.center_distribution",
                               D10CenterPatternRow, "site_ref"))
        object.__setattr__(self, "hotspots", _freeze_sorted_objects(
            self.hotspots, "R5S3D10ProjectUnit.hotspots",
            D10HotspotProjection, "projection_id"))
        object.__setattr__(self, "clinical_domain_authority_ref", _check_str(
            self.clinical_domain_authority_ref,
            "R5S3D10ProjectUnit.clinical_domain_authority_ref"))
        object.__setattr__(self, "source_revision_content_pairs",
                           _freeze_source_pairs(
                               self.source_revision_content_pairs,
                               "R5S3D10ProjectUnit."
                               "source_revision_content_pairs"))


@dataclass(frozen=True)
class R5S3AuthorityUnitTagged:
    """One tagged authority unit: the variant-kind discriminator, the
    complete R5 receipt, the receipt content hash, the public projectable /
    private hidden member/site planes and exactly one tagged variant
    payload."""

    unit_ref: str
    variant_kind: str
    authority_receipt: R5AuthorityReceipt
    receipt_content_hash: str
    projectable_member_refs: Tuple[str, ...]
    hidden_member_refs: Tuple[str, ...]
    hidden_site_refs: Tuple[str, ...]
    source_unit_refs: Tuple[str, ...]
    d09_variant_payload: Optional[R5S3D09CenterPatternUnit]
    d10_variant_payload: Optional[R5S3D10ProjectUnit]
    content_hash: Optional[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "unit_ref", _check_str(
            self.unit_ref, "R5S3AuthorityUnitTagged.unit_ref"))
        object.__setattr__(self, "variant_kind", _check_closed(
            self.variant_kind, "R5S3AuthorityUnitTagged.variant_kind",
            S3_TAGGED_VARIANT_KINDS))
        _check_obj_type(self.authority_receipt, R5AuthorityReceipt,
                        "R5S3AuthorityUnitTagged.authority_receipt")
        object.__setattr__(self, "receipt_content_hash", _check_hash(
            self.receipt_content_hash,
            "R5S3AuthorityUnitTagged.receipt_content_hash"))
        object.__setattr__(self, "projectable_member_refs", _freeze_str_tuple(
            self.projectable_member_refs,
            "R5S3AuthorityUnitTagged.projectable_member_refs"))
        object.__setattr__(self, "hidden_member_refs", _freeze_str_tuple(
            self.hidden_member_refs,
            "R5S3AuthorityUnitTagged.hidden_member_refs"))
        object.__setattr__(self, "hidden_site_refs", _freeze_str_tuple(
            self.hidden_site_refs,
            "R5S3AuthorityUnitTagged.hidden_site_refs"))
        object.__setattr__(self, "source_unit_refs", _freeze_str_tuple(
            self.source_unit_refs, "R5S3AuthorityUnitTagged.source_unit_refs"))
        if self.variant_kind == "d09_center_pattern_unit":
            if self.d09_variant_payload is None:
                raise S3ContractError(
                    "R5S3AuthorityUnitTagged d09_center_pattern_unit requires "
                    "d09_variant_payload (tagged_variant_payload_mismatch)")
            if self.d10_variant_payload is not None:
                raise S3ContractError(
                    "R5S3AuthorityUnitTagged d09_center_pattern_unit forbids "
                    "d10_variant_payload (tagged_variant_payload_mismatch)")
        else:
            if self.d10_variant_payload is None:
                raise S3ContractError(
                    "R5S3AuthorityUnitTagged d10_project_unit requires "
                    "d10_variant_payload (tagged_variant_payload_mismatch)")
            if self.d09_variant_payload is not None:
                raise S3ContractError(
                    "R5S3AuthorityUnitTagged d10_project_unit forbids "
                    "d09_variant_payload (tagged_variant_payload_mismatch)")
        object.__setattr__(self, "content_hash",
                           _optional_content_hash(self.content_hash,
                                                  unit_content_hash(self)))
        # private <-> public plane separation: hidden refs never projectable.
        if set(self.hidden_member_refs) & set(self.projectable_member_refs):
            raise S3ContractError(
                "R5S3AuthorityUnitTagged hidden_member_refs must be disjoint "
                "from projectable_member_refs (hidden_leaf_in_audience_hash)")


def _optional_content_hash(supplied: Optional[str], expected: str) -> str:
    if supplied is not None and supplied != expected:
        raise S3HashMismatchError(
            f"supplied content_hash {supplied!r} does not match {expected!r}")
    return expected


@dataclass(frozen=True)
class R5S3LowRiskCluster:
    """One low-risk cluster inside the audience payload: canonical
    ``cluster_ref == 'cluster:' + content_hash``, receipt ref, closed domain,
    site ref and exact projectable low member refs."""

    cluster_ref: str
    authority_receipt_ref: str
    domain: str
    site_ref: str
    member_refs: Tuple[str, ...]
    content_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "authority_receipt_ref", _check_receipt_ref(
            self.authority_receipt_ref,
            "R5S3LowRiskCluster.authority_receipt_ref"))
        object.__setattr__(self, "domain", _check_closed(
            self.domain, "R5S3LowRiskCluster.domain", S3_DOMAINS))
        object.__setattr__(self, "site_ref", _check_str(
            self.site_ref, "R5S3LowRiskCluster.site_ref"))
        object.__setattr__(self, "member_refs", _freeze_str_tuple(
            self.member_refs, "R5S3LowRiskCluster.member_refs"))
        _require_min_count(self.member_refs, 1,
                           "R5S3LowRiskCluster.member_refs")
        expected_hash = cluster_content_hash(
            self.authority_receipt_ref, self.domain, self.site_ref,
            self.member_refs)
        if self.content_hash != expected_hash:
            raise S3HashMismatchError(
                "R5S3LowRiskCluster.content_hash does not match the "
                f"canonical cluster hash {expected_hash!r}")
        if self.cluster_ref != CLUSTER_REF_PREFIX + expected_hash:
            raise S3ContractError(
                "R5S3LowRiskCluster.cluster_ref must equal "
                f"{CLUSTER_REF_PREFIX!r} + canonical content hash "
                "(cluster_canonical_ref_mismatch)")


@dataclass(frozen=True)
class R5S3AggregateReceiptSetIdentity:
    """The aggregate receipt-set identity: sorted-unique unit receipt refs and
    risk marker identity hashes plus the shared project/run/snapshot/cutoff/
    audience contract.  ``aggregate_id == 'aggregate:' + canonical hash``."""

    aggregate_id: str
    unit_receipt_refs: Tuple[str, ...]
    risk_marker_identity_hashes: Tuple[str, ...]
    project_ref: str
    run_ref: str
    snapshot_ref: str
    cutoff_ref: Optional[str]
    audience_contract_id: str
    content_hash: str

    def __post_init__(self) -> None:
        unit_receipt_refs = tuple(
            _check_receipt_ref(item,
                               "R5S3AggregateReceiptSetIdentity."
                               "unit_receipt_refs[]")
            for item in self.unit_receipt_refs)
        if len(set(unit_receipt_refs)) != len(unit_receipt_refs):
            raise S3ContractError(
                "R5S3AggregateReceiptSetIdentity.unit_receipt_refs must be "
                f"duplicate-free, got {sorted(unit_receipt_refs)!r}")
        _require_min_count(unit_receipt_refs, 1,
                           "R5S3AggregateReceiptSetIdentity.unit_receipt_refs")
        object.__setattr__(self, "unit_receipt_refs",
                           tuple(sorted(unit_receipt_refs)))
        object.__setattr__(self, "risk_marker_identity_hashes",
                           _freeze_hash_tuple(
                               self.risk_marker_identity_hashes,
                               "R5S3AggregateReceiptSetIdentity."
                               "risk_marker_identity_hashes"))
        object.__setattr__(self, "project_ref", _check_str(
            self.project_ref, "R5S3AggregateReceiptSetIdentity.project_ref"))
        object.__setattr__(self, "run_ref", _check_str(
            self.run_ref, "R5S3AggregateReceiptSetIdentity.run_ref"))
        object.__setattr__(self, "snapshot_ref", _check_str(
            self.snapshot_ref, "R5S3AggregateReceiptSetIdentity.snapshot_ref"))
        object.__setattr__(self, "cutoff_ref", _check_optional_str(
            self.cutoff_ref, "R5S3AggregateReceiptSetIdentity.cutoff_ref"))
        object.__setattr__(self, "audience_contract_id", _check_str(
            self.audience_contract_id,
            "R5S3AggregateReceiptSetIdentity.audience_contract_id"))
        expected_id = aggregate_identity_id(
            self.unit_receipt_refs, self.risk_marker_identity_hashes,
            self.project_ref, self.run_ref, self.snapshot_ref, self.cutoff_ref,
            self.audience_contract_id)
        if self.aggregate_id != expected_id:
            raise S3ContractError(
                "R5S3AggregateReceiptSetIdentity.aggregate_id must equal "
                f"{AGGREGATE_REF_PREFIX!r} + canonical identity hash "
                f"({expected_id!r}), got {self.aggregate_id!r}")
        _verify_supplied_content_hash(self, "content_hash")


# ---------------------------------------------------------------------------
# Audience payload and root packet
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S3AudiencePayload:
    """The complete public audience payload: current risk set, change bands,
    measures, center map, cockpit and low-risk clusters (all imported typed R5
    objects read-only; the projections are the worker_02 projector's domain)."""

    current_risk_set: R5CurrentRiskSet
    change_bands: Tuple[R5ChangeBand, ...]
    measures: Tuple[R5QuantitativeMeasure, ...]
    center_map: R5CenterMapProjection
    cockpit: R5ProjectCockpitProjection
    low_risk_clusters: Tuple[R5S3LowRiskCluster, ...]

    def __post_init__(self) -> None:
        _check_obj_type(self.current_risk_set, R5CurrentRiskSet,
                        "R5S3AudiencePayload.current_risk_set")
        _check_obj_type(self.center_map, R5CenterMapProjection,
                        "R5S3AudiencePayload.center_map")
        _check_obj_type(self.cockpit, R5ProjectCockpitProjection,
                        "R5S3AudiencePayload.cockpit")
        object.__setattr__(self, "change_bands", _freeze_sorted_objects(
            self.change_bands, "R5S3AudiencePayload.change_bands",
            R5ChangeBand, "risk_ref"))
        object.__setattr__(self, "measures", _freeze_sorted_objects(
            self.measures, "R5S3AudiencePayload.measures",
            R5QuantitativeMeasure, "authoritative_value_ref"))
        object.__setattr__(self, "low_risk_clusters", _freeze_sorted_objects(
            self.low_risk_clusters, "R5S3AudiencePayload.low_risk_clusters",
            R5S3LowRiskCluster, "cluster_ref"))
        # low clusters live INSIDE the replay hash (contract P1-4); the schema
        # minimum for the payload collection is zero (min_items:0), so an
        # empty cluster list is structurally valid here -- the projector's
        # current-plane closure decides exactness.
        # every change band / current-risk ref must be a marker or cluster ref.
        _require_marker_prefixes(self.current_risk_set, self.change_bands)


def _require_marker_prefixes(
    current_risk_set: R5CurrentRiskSet, change_bands: Tuple[R5ChangeBand, ...],
) -> None:
    """Invariant ``current_risk_marker_identities_only`` at the payload level:
    current-risk high/medium/low/resolved refs reference only
    ``d09_marker:``/``d10_marker:``/``cluster:`` public identities; raw member
    refs are expansion-only and never a current-risk identity."""
    for name, plane in (
            ("high_risk", current_risk_set.high_risk_refs),
            ("medium_risk", current_risk_set.medium_risk_refs),
            ("low_risk_cluster", current_risk_set.low_risk_cluster_refs),
            ("resolved_history", current_risk_set.resolved_history_refs)):
        for ref in plane:
            if not (ref.startswith(D09_MARKER_PREFIX)
                    or ref.startswith(D10_MARKER_PREFIX)
                    or ref.startswith(CLUSTER_REF_PREFIX)):
                raise S3ContractError(
                    "R5S3AudiencePayload current-risk "
                    f"{name} ref {ref!r} is not a marker/cluster identity "
                    "(raw_member_as_current_risk_ref)")


def audience_replay_content_hash(payload: R5S3AudiencePayload) -> str:
    """``audience_replay_content_hash``: canonical SHA-256 of the complete
    audience payload (including low clusters, excluding hidden leaves)."""
    return s3_sha256(s3_canonical_bytes(payload))


def packet_core_dict(packet: "R5S3AuthorityPacket") -> Dict[str, Any]:
    """Plain projection of the packet excluding exactly ``packet_id``,
    ``packet_integrity_hash``, ``audience_replay_content_hash``, ``schema``,
    ``status`` and ``authority_mode`` (the frozen packet-integrity body)."""
    return {field.name: getattr(packet, field.name)
            for field in dataclass_fields(packet)
            if field.name not in (
                "packet_id", "packet_integrity_hash",
                "audience_replay_content_hash", "schema", "status",
                "authority_mode")}


def compute_packet_integrity_hash(packet: "R5S3AuthorityPacket") -> str:
    """``packet_integrity_hash``: canonical SHA-256 of ``packet_core_dict``."""
    return s3_sha256(s3_canonical_bytes(packet_core_dict(packet)))


def compute_packet_id(packet: "R5S3AuthorityPacket") -> str:
    """Nonrecursive packet identity: literal single-colon prefix plus the
    audience replay content hash."""
    return PACKET_ID_PREFIX + ":" + packet.audience_replay_content_hash


# ---------------------------------------------------------------------------
# Imported exact-key sets (re-verified against the frozen schema at import)
# ---------------------------------------------------------------------------

#: public allowlist module -> allowed projection/receipt classes (read-only).
S3_PUBLIC_ALLOWLIST: Dict[str, Tuple[str, ...]] = {
    "mm_r4.d09_projection": (
        "D09AudienceProjection", "D09ProjectionCountSurface", "D09RiskMarker",
        "D09HotspotProjection", "D09DeepLinkTarget", "D09QueryDraft",
        "D09R2RiskHandoff", "D09ProjectionBundle"),
    "mm_r4.d10_projection": (
        "D10AudienceProjection", "D10ProjectionCountSurface",
        "D10ProjectionVersion", "D10RiskMarker", "D10HotspotProjection",
        "D10DeepLinkTarget", "D10AudiencePart", "D10QueryDraft",
        "D10ChangeSection", "D10CenterPatternRow", "D10TrendSurface",
        "D10WarningMarker", "D10R2RiskHandoff", "D10ProjectProjection",
        "D10ProjectionBundle"),
    "mm_r5.contracts": (
        "R5AuthorityReceipt", "SourceRevisionContentPair",
        "R5CurrentRiskSet", "R5ChangeBand", "R5QuantitativeMeasure",
        "R5CenterMapCell", "R5CenterMapProjection", "R5ProjectionInstance",
        "R5ProjectCockpitProjection"),
}

#: typed-input denylist modules (never promoted to public authority).
S3_TYPED_INPUT_DENYLIST_MODULES: Tuple[str, ...] = (
    "mm_r4.d09_contracts", "mm_r4.d10_contracts")


def check_imported_objects_allowed(payload: Any) -> None:
    """Invariant ``typed_input_not_promoted`` (structural gate): every
    imported object embedded in an S3 unit is a public projection/receipt
    class.  A D09/D10 typed-input object (``Member``, ``SubjectRiskMember``,
    ``GapMember``, …) is never a public authority leaf."""
    for field in dataclass_fields(payload):
        value = getattr(payload, field.name)
        if value is None:
            continue
        values = value if isinstance(value, (list, tuple)) else (value,)
        for item in values:
            if is_dataclass(item) and not isinstance(item, type):
                mod = type(item).__module__
                if mod in S3_TYPED_INPUT_DENYLIST_MODULES:
                    raise S3InvariantError(
                        "typed_input_leaf_promoted",
                        f"{type(payload).__name__}.{field.name} embeds "
                        f"typed-input {type(item).__name__} from {mod!r}")


# ---------------------------------------------------------------------------
# Root authority packet
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class R5S3AuthorityPacket:
    """The frozen S3 authority packet: tagged authority units, the aggregate
    receipt-set identity, the nine supplemental authority collections, the
    complete audience payload and the acyclic hash DAG leaves."""

    packet_id: str
    schema: str
    status: str
    authority_mode: str
    authority_units: Tuple[R5S3AuthorityUnitTagged, ...]
    aggregate_receipt_set: R5S3AggregateReceiptSetIdentity
    risk_lifecycle_authorities: Tuple[R5S3RiskLifecycleAuthority, ...]
    closure_authorities: Tuple[R5S3ClosureAuthority, ...]
    clinical_domain_authorities: Tuple[R5S3ClinicalDomainAuthority, ...]
    denominator_authorities: Tuple[R5S3DenominatorAuthority, ...]
    layer_membership_authorities: Tuple[R5S3LayerMembershipAuthority, ...]
    cutoff_authorities: Tuple[R5S3CutoffAuthority, ...]
    evaluation_limit_authorities: Tuple[R5S3EvaluationLimitAuthority, ...]
    coverage_authorities: Tuple[R5S3CoverageAuthority, ...]
    change_cause_mixture_authorities: Tuple[
        R5S3ChangeCauseMixtureAuthority, ...]
    audience_payload: R5S3AudiencePayload
    audience_replay_content_hash: str
    packet_integrity_hash: Optional[str]

    def __post_init__(self) -> None:
        if self.schema != S3_PACKET_SCHEMA_ID:
            raise S3ContractError(
                f"R5S3AuthorityPacket.schema must be {S3_PACKET_SCHEMA_ID!r}")
        if self.status != STAGE_STATUS_S3:
            raise S3ContractError(
                f"R5S3AuthorityPacket.status must be {STAGE_STATUS_S3!r}")
        if self.authority_mode != AUTHORITY_MODE_S3:
            raise S3ContractError(
                "R5S3AuthorityPacket.authority_mode must be "
                f"{AUTHORITY_MODE_S3!r}")
        object.__setattr__(self, "packet_id", _check_str(
            self.packet_id, "R5S3AuthorityPacket.packet_id"))
        object.__setattr__(self, "authority_units", _freeze_sorted_objects(
            self.authority_units, "R5S3AuthorityPacket.authority_units",
            R5S3AuthorityUnitTagged, "unit_ref"))
        _require_min_count(self.authority_units, 1,
                           "R5S3AuthorityPacket.authority_units")
        _check_obj_type(self.aggregate_receipt_set,
                        R5S3AggregateReceiptSetIdentity,
                        "R5S3AuthorityPacket.aggregate_receipt_set")
        object.__setattr__(
            self, "risk_lifecycle_authorities", _freeze_lifecycles(
                self.risk_lifecycle_authorities))
        object.__setattr__(self, "closure_authorities",
                           _freeze_sorted_objects(
                               self.closure_authorities,
                               "R5S3AuthorityPacket.closure_authorities",
                               R5S3ClosureAuthority,
                               "closure_authority_id"))
        object.__setattr__(self, "clinical_domain_authorities",
                           _freeze_sorted_objects(
                               self.clinical_domain_authorities,
                               "R5S3AuthorityPacket."
                               "clinical_domain_authorities",
                               R5S3ClinicalDomainAuthority, "authority_id"))
        object.__setattr__(self, "denominator_authorities",
                           _freeze_sorted_objects(
                               self.denominator_authorities,
                               "R5S3AuthorityPacket.denominator_authorities",
                               R5S3DenominatorAuthority, "authority_id"))
        object.__setattr__(self, "layer_membership_authorities",
                           _freeze_sorted_objects(
                               self.layer_membership_authorities,
                               "R5S3AuthorityPacket."
                               "layer_membership_authorities",
                               R5S3LayerMembershipAuthority, "authority_id"))
        object.__setattr__(self, "cutoff_authorities",
                           _freeze_sorted_objects(
                               self.cutoff_authorities,
                               "R5S3AuthorityPacket.cutoff_authorities",
                               R5S3CutoffAuthority, "authority_id"))
        object.__setattr__(self, "evaluation_limit_authorities",
                           _freeze_sorted_objects(
                               self.evaluation_limit_authorities,
                               "R5S3AuthorityPacket."
                               "evaluation_limit_authorities",
                               R5S3EvaluationLimitAuthority, "authority_id"))
        object.__setattr__(self, "coverage_authorities",
                           _freeze_sorted_objects(
                               self.coverage_authorities,
                               "R5S3AuthorityPacket.coverage_authorities",
                               R5S3CoverageAuthority, "authority_id"))
        object.__setattr__(self, "change_cause_mixture_authorities",
                           _freeze_sorted_objects(
                               self.change_cause_mixture_authorities,
                               "R5S3AuthorityPacket."
                               "change_cause_mixture_authorities",
                               R5S3ChangeCauseMixtureAuthority,
                               "authority_id"))
        _check_obj_type(self.audience_payload, R5S3AudiencePayload,
                        "R5S3AuthorityPacket.audience_payload")
        expected_replay = audience_replay_content_hash(self.audience_payload)
        if self.audience_replay_content_hash != expected_replay:
            raise S3HashMismatchError(
                "R5S3AuthorityPacket.audience_replay_content_hash "
                f"{self.audience_replay_content_hash!r} does not match the "
                f"canonical replay hash {expected_replay!r}")
        if self.packet_id != PACKET_ID_PREFIX + ":" + expected_replay:
            raise S3ContractError(
                "R5S3AuthorityPacket.packet_id must equal "
                f"{PACKET_ID_PREFIX!r} + ':' + audience_replay_content_hash "
                "(packet_id_grammar_mismatch)")
        expected_integrity = compute_packet_integrity_hash(self)
        if (self.packet_integrity_hash is not None
                and self.packet_integrity_hash != expected_integrity):
            raise S3HashMismatchError(
                "R5S3AuthorityPacket.packet_integrity_hash does not match "
                "the canonical integrity hash")
        object.__setattr__(self, "packet_integrity_hash",
                           compute_packet_integrity_hash(self))

        _validate_packet_invariants(self)


def _freeze_lifecycles(
    value: Any,
) -> Tuple[R5S3RiskLifecycleAuthority, ...]:
    """Lifecycle authorities are sorted-unique by ``marker_identity_ref``."""
    if not isinstance(value, (list, tuple)):
        raise S3ContractError(
            "R5S3AuthorityPacket.risk_lifecycle_authorities must be a "
            "list/tuple")
    items = []
    for item in value:
        if not isinstance(item, R5S3RiskLifecycleAuthority):
            raise S3ContractError(
                "R5S3AuthorityPacket.risk_lifecycle_authorities[] must be a "
                f"R5S3RiskLifecycleAuthority, got {type(item).__name__}")
        items.append(item)
    keys = [item.marker_identity_ref for item in items]
    if len(set(keys)) != len(keys):
        raise S3ContractError(
            "R5S3AuthorityPacket.risk_lifecycle_authorities must be "
            f"sorted-unique by marker_identity_ref, got {sorted(keys)!r}")
    return tuple(sorted(items, key=lambda item: item.marker_identity_ref))


# ---------------------------------------------------------------------------
# Cross-object authority-side invariants (frozen error codes)
# ---------------------------------------------------------------------------


def _fail(error_code: str, message: str) -> None:
    raise S3InvariantError(error_code, message)


def _check_authority_scope(packet: R5S3AuthorityPacket) -> None:
    """Invariant ``synthetic_offline_test_only``."""
    if packet.authority_mode != AUTHORITY_MODE_S3:
        _fail("authority_scope_violation",
              f"authority_mode must be {AUTHORITY_MODE_S3!r}")
    if packet.status != STAGE_STATUS_S3:
        _fail("authority_scope_violation",
              f"status must be {STAGE_STATUS_S3!r}")


def _check_receipt_identity(packet: R5S3AuthorityPacket) -> None:
    """Invariant ``receipt_content_hash_recipe``: every unit's receipt content
    hash is the canonical SHA-256 of the complete R5 authority receipt and
    every supplemental receipt_ref equals ``'receipt:' + receipt_hash``."""
    for unit in packet.authority_units:
        expected = receipt_content_hash(unit.authority_receipt)
        if unit.receipt_content_hash != expected:
            _fail("receipt_content_hash_mismatch",
                  "unit %s receipt_content_hash %r != canonical %r"
                  % (unit.unit_ref, unit.receipt_content_hash, expected))
        if authority_receipt_ref(unit.authority_receipt) != \
                RECEIPT_REF_PREFIX + unit.receipt_content_hash:
            _fail("receipt_content_hash_mismatch",
                  f"unit {unit.unit_ref} receipt ref prefix mismatch")
    for name, refs in (
            ("clinical_domain", packet.clinical_domain_authorities),
            ("denominator", packet.denominator_authorities),
            ("layer_membership", packet.layer_membership_authorities),
            ("cutoff", packet.cutoff_authorities),
            ("evaluation_limit", packet.evaluation_limit_authorities),
            ("coverage", packet.coverage_authorities),
            ("change_cause_mixture",
             packet.change_cause_mixture_authorities)):
        for obj in refs:
            if obj.receipt_ref != RECEIPT_REF_PREFIX + obj.receipt_hash:
                _fail("receipt_content_hash_mismatch",
                      f"{name} authority {obj.authority_id} receipt_ref "
                      "prefix mismatch")


def _check_aggregate_identity(packet: R5S3AuthorityPacket) -> None:
    """Invariant ``aggregate_receipt_set_identity``: all units share the same
    project/run/snapshot/cutoff/audience_contract; the aggregate identity is
    the canonical hash over sorted unique unit receipt refs and risk marker
    identity hashes; the declared current-risk authority receipt ref equals
    the aggregate identity."""
    receipts = []
    markers = []
    identities = set()
    for unit in packet.authority_units:
        receipt = unit.authority_receipt
        receipts.append(RECEIPT_REF_PREFIX + unit.receipt_content_hash)
        identities.add((receipt.project_ref, receipt.run_ref,
                        receipt.snapshot_ref, receipt.cutoff_ref,
                        receipt.audience_contract_id))
        variant = unit.d09_variant_payload or unit.d10_variant_payload
        if variant is not None and variant.risk_marker is not None:
            markers.append(variant.risk_marker.content_hash)
    if len(identities) != 1:
        _fail("aggregate_identity_mismatch",
              f"units do not share one project/run/snapshot/cutoff/"
              f"audience_contract identity: {identities!r}")
    agg = packet.aggregate_receipt_set
    expected_refs = tuple(sorted(set(receipts)))
    if agg.unit_receipt_refs != expected_refs:
        _fail("aggregate_identity_mismatch",
              "aggregate unit_receipt_refs do not equal the sorted unique "
              "unit receipt refs")
    expected_hashes = tuple(sorted(set(markers)))
    if agg.risk_marker_identity_hashes != expected_hashes:
        _fail("aggregate_identity_mismatch",
              "aggregate risk_marker_identity_hashes do not equal the sorted "
              "unique marker content hashes")
    identity, = identities
    aggregate_identity = (
        agg.project_ref, agg.run_ref, agg.snapshot_ref, agg.cutoff_ref,
        agg.audience_contract_id,
    )
    if aggregate_identity != identity:
        _fail(
            "aggregate_identity_mismatch",
            "aggregate project/run/snapshot/cutoff/audience_contract fields "
            "must equal the shared authority receipt identity",
        )
    expected_id = aggregate_identity_id(
        expected_refs, expected_hashes, identity[0], identity[1],
        identity[2], identity[3], identity[4])
    if agg.aggregate_id != expected_id:
        _fail("aggregate_identity_mismatch",
              f"aggregate_id {agg.aggregate_id!r} != {expected_id!r}")
    if packet.audience_payload.current_risk_set.authority_receipt_ref \
            != agg.aggregate_id:
        _fail("aggregate_identity_mismatch",
              "current_risk_set.authority_receipt_ref must equal the "
              "aggregate identity")


def _check_hash_dag_acyclic(packet: R5S3AuthorityPacket) -> None:
    """Invariant ``hash_dag_acyclic``: the packing hashes exclude their own
    dependencies (no root content_hash, no self edge)."""
    expected = compute_packet_integrity_hash(packet)
    if packet.packet_integrity_hash != expected:
        _fail("packet_integrity_hash_mismatch",
              "packet_integrity_hash must equal the canonical hash of the "
              "packet excluding its dependencies")


def _check_current_resolved_disjoint(packet: R5S3AuthorityPacket) -> None:
    """Invariant ``unique_reference_sets``/current-resolved exclusivity: a ref
    may appear in at most one current/resolved plane."""
    payload = packet.audience_payload
    planes = (
        ("high_risk", payload.current_risk_set.high_risk_refs),
        ("medium_risk", payload.current_risk_set.medium_risk_refs),
        ("low_risk_cluster", payload.current_risk_set.low_risk_cluster_refs),
        ("resolved_history", payload.current_risk_set.resolved_history_refs),
    )
    seen: Dict[str, str] = {}
    for plane_name, members in planes:
        for item in members:
            if item in seen:
                _fail("current_reserved_overlap_check",
                      f"ref {item!r} appears in both {seen[item]!r} and "
                      f"{plane_name!r}")


def _check_typed_input_not_promoted(packet: R5S3AuthorityPacket) -> None:
    """Invariant ``typed_input_not_promoted``: no unit embeds a D09/D10
    typed-input object as a public authority leaf."""
    for unit in packet.authority_units:
        for payload in (unit.d09_variant_payload, unit.d10_variant_payload):
            if payload is not None:
                check_imported_objects_allowed(payload)


def _check_tagged_variant_exact(packet: R5S3AuthorityPacket) -> None:
    """Invariant ``tagged_variant_payload_exact``: variant kind matches the
    single tagged payload (cross-variant rejected at unit construction)."""
    for unit in packet.authority_units:
        if unit.variant_kind not in S3_TAGGED_VARIANT_KINDS:
            _fail("tagged_variant_payload_mismatch",
                  f"unknown variant_kind {unit.variant_kind!r}")
        if unit.variant_kind == "d09_center_pattern_unit":
            if unit.d10_variant_payload is not None:
                _fail("tagged_variant_payload_mismatch",
                      f"unit {unit.unit_ref} carries a D10 payload under a "
                      "D09 variant kind")


def _check_invariant_tables_present(packet: R5S3AuthorityPacket) -> None:
    """Invariance ``layer_recipes_complete`` / ``change_emission_complete`` /
    ``coverage_enum_no_not_evaluable`` / ``hash_dag`` constants (module-level
    frozen tables)."""
    _require_layer_recipes_present()
    _require_change_emission_present()
    if "not_evaluable" in S3_COVERAGE_STATES:
        _fail("invalid_coverage_enum",
              "COVERAGE_STATES must never contain 'not_evaluable'")


def _check_receipt_source_pair_order(packet: R5S3AuthorityPacket) -> None:
    """Receipt source revision-content pairs must be sorted-unique by
    revision id so the supplemental binding is byte-exact."""
    for unit in packet.authority_units:
        pairs = unit.authority_receipt.source_revision_content_pairs
        revs = [pair.revision_id for pair in pairs]
        if revs != sorted(set(revs)):
            _fail("receipt_content_hash_mismatch",
                  f"unit {unit.unit_ref} receipt source pairs must be "
                  "sorted-unique by revision_id")


def _supplemental_collections(
    packet: R5S3AuthorityPacket,
) -> Tuple[Tuple[str, Tuple[Any, ...]], ...]:
    """The nine frozen named supplemental collections (schema
    ``SUPPLEMENTAL_PACKET_LIST_KEYS``) and their collection names."""
    return (
        ("risk_lifecycle", packet.risk_lifecycle_authorities),
        ("closure", packet.closure_authorities),
        ("clinical_domain", packet.clinical_domain_authorities),
        ("denominator", packet.denominator_authorities),
        ("layer_membership", packet.layer_membership_authorities),
        ("cutoff", packet.cutoff_authorities),
        ("evaluation_limit", packet.evaluation_limit_authorities),
        ("coverage", packet.coverage_authorities),
        ("change_cause_mixture", packet.change_cause_mixture_authorities),
    )


def check_supplemental_receipt_bindings(
    packet: R5S3AuthorityPacket,
) -> None:
    """Verifier-owned runtime invariant over the nine supplemental
    collections (``supplemental_receipt_bindings``).

    Called at packet construction and by ``validate_s3_authority_packet``.
    It re-derives everything from the typed leaves, never from a
    caller-declared payload or outer hash, so it survives a full coordinated
    packet re-sign:

    * recomputes each object's canonical content hash with the accepted
      recipe (``supplemental_content_hash_mismatch``);
    * enforces ``receipt_ref == 'receipt:' + receipt_hash``
      (``supplemental_receipt_binding_mismatch``);
    * resolves ``receipt_hash``/``receipt_ref`` to EXACTLY ONE complete unit
      ``R5AuthorityReceipt`` (``supplemental_receipt_missing`` /
      ``supplemental_receipt_cardinality_mismatch``);
    * checks that resolved receipt's canonical content hash, the shared
      project/run/snapshot/cutoff/audience identity, the visibility decision
      id/hash, the byte-exact source revision/content pairs and the
      offline-only state all match the supplemental
      (``supplemental_receipt_binding_mismatch`` /
      ``supplemental_visibility_binding_mismatch`` /
      ``supplemental_source_pairs_mismatch`` / ``supplemental_type_mismatch``);
    * re-runs the object's own closed-enum / type / cardinality validation on
      the stored fields (``supplemental_enum_mismatch`` /
      ``supplemental_type_mismatch``).

    Stable exact error codes mirror the verifier's packet oracle so the
    runtime and the oracle agree.
    """
    # Complete unit receipts indexed by their canonical content hash.
    receipts_by_hash: Dict[str, Tuple[R5AuthorityReceipt, Any]] = {}
    identities: set = set()
    for unit in packet.authority_units:
        receipt = unit.authority_receipt
        canonical = receipt_content_hash(receipt)
        if unit.receipt_content_hash != canonical:
            _fail("supplemental_receipt_binding_mismatch",
                  f"unit {unit.unit_ref} receipt_content_hash does not match "
                  "the canonical complete-receipt hash")
        if canonical in receipts_by_hash:
            _fail("supplemental_receipt_cardinality_mismatch",
                  f"multiple units share receipt content hash {canonical!r}")
        receipts_by_hash[canonical] = (receipt, unit)
        identities.add((receipt.project_ref, receipt.run_ref,
                        receipt.snapshot_ref, receipt.cutoff_ref,
                        receipt.audience_contract_id))
    if len(identities) != 1:
        _fail("supplemental_receipt_binding_mismatch",
              "authority units do not share one project/run/snapshot/cutoff/"
              f"audience_contract identity: {identities!r}")
    shared_identity, = identities

    for collection_name, collection in _supplemental_collections(packet):
        for obj in collection:
            owner = f"{type(obj).__name__}[{collection_name}]"
            # 1) canonical object content hash (accepted recipe).
            try:
                expected_obj_hash = s3_content_hash_excluding(
                    obj, ("content_hash",))
            except S3CanonicalError as error:
                _fail("supplemental_type_mismatch",
                      f"{owner} cannot be canonicalized: {error}")
            if obj.content_hash != expected_obj_hash:
                _fail("supplemental_content_hash_mismatch",
                      f"{owner} content_hash {obj.content_hash!r} does not "
                      f"match the canonical hash {expected_obj_hash!r}")
            # 2) exact receipt_ref grammar.
            if obj.receipt_ref != RECEIPT_REF_PREFIX + obj.receipt_hash:
                _fail("supplemental_receipt_binding_mismatch",
                      f"{owner} receipt_ref must be 'receipt:' + receipt_hash, "
                      f"got {obj.receipt_ref!r} vs {obj.receipt_hash!r}")
            # 3) resolve receipt_hash to exactly one complete unit receipt.
            resolved = receipts_by_hash.get(obj.receipt_hash)
            if resolved is None:
                _fail("supplemental_receipt_missing",
                      f"{owner} receipt {obj.receipt_hash!r} does not resolve "
                      "to any complete unit R5AuthorityReceipt")
            receipt, unit = resolved
            # 4) canonical receipt content hash + shared identity.
            if receipt_content_hash(receipt) != obj.receipt_hash:
                _fail("supplemental_receipt_binding_mismatch",
                      f"{owner} receipt canonical hash mismatch")
            if (receipt.project_ref, receipt.run_ref, receipt.snapshot_ref,
                    receipt.cutoff_ref, receipt.audience_contract_id) != \
                    shared_identity:
                _fail("supplemental_receipt_binding_mismatch",
                      f"{owner} resolved receipt identity drift from the "
                      "shared project/run/snapshot/cutoff/audience identity")
            # 5) visibility decision id/hash.
            if obj.visibility_decision_id != receipt.visibility_decision_id:
                _fail("supplemental_visibility_binding_mismatch",
                      f"{owner} visibility_decision_id drift from the "
                      "resolved receipt")
            if obj.visibility_decision_hash != receipt.visibility_decision_hash:
                _fail("supplemental_visibility_binding_mismatch",
                      f"{owner} visibility_decision_hash drift from the "
                      "resolved receipt")
            # 6) byte-exact source revision/content pairs.
            if s3_canonical_bytes(obj.source_revision_content_pairs) != \
                    s3_canonical_bytes(receipt.source_revision_content_pairs):
                _fail("supplemental_source_pairs_mismatch",
                      f"{owner} source revision/content pairs drift from the "
                      "resolved receipt")
            # 7) offline-only state.
            if obj.offline_test_only is not True:
                _fail("supplemental_type_mismatch",
                      f"{owner} offline_test_only must be True")
            # 8) type/cardinality/enum relations (reconstructive re-check):
            # re-running the object's own __post_init__ validation on the
            # stored fields catches any closed-enum / shape drift that an
            # in-place mutation could have smuggled past construction.
            try:
                rebuilt = type(obj)(**{
                    field.name: getattr(obj, field.name)
                    for field in dataclass_fields(obj)})
            except S3ContractError as error:
                _fail("supplemental_enum_mismatch",
                      f"{owner} closed field drift: {error}")
            if rebuilt != obj:
                _fail("supplemental_type_mismatch",
                      f"{owner} does not survive canonical reconstruction "
                      "(field normalization drift)")


_INVARIANT_CHECKS: Tuple[Tuple[str, Any], ...] = (
    ("authority_scope", _check_authority_scope),
    ("receipt_identity", _check_receipt_identity),
    ("receipt_source_pair_order", _check_receipt_source_pair_order),
    ("aggregate_identity", _check_aggregate_identity),
    ("current_resolved_disjoint", _check_current_resolved_disjoint),
    ("typed_input_not_promoted", _check_typed_input_not_promoted),
    ("tagged_variant_exact", _check_tagged_variant_exact),
    ("invariant_tables", _check_invariant_tables_present),
    ("hash_dag_acyclic", _check_hash_dag_acyclic),
    ("supplemental_receipt_bindings", check_supplemental_receipt_bindings),
)

FROZEN_INVARIANT_ERROR_CODES: Tuple[str, ...] = tuple(
    code for code, _ in _INVARIANT_CHECKS)


def _validate_packet_invariants(packet: R5S3AuthorityPacket) -> None:
    """Fail-closed construction gate: every frozen authority-side invariant
    must hold or an ``S3InvariantError`` is raised."""
    for _name, check in _INVARIANT_CHECKS:
        check(packet)


def validate_s3_authority_packet(
    packet: R5S3AuthorityPacket,
) -> Dict[str, Any]:
    """Fail-closed validator over an S3 authority packet (authority side).

    Returns ``{"valid": bool, "reasons": tuple of frozen error codes}``
    without raising.  The projection-side invariants (current-plane closure,
    center-cell closure, change-band emission, closure bidirectionality,
    cockpit/measure projection) are the worker_02 projector's domain and are
    not evaluated here.
    """
    reasons: list = []
    for _name, check in _INVARIANT_CHECKS:
        try:
            check(packet)
        except S3InvariantError as error:
            reasons.append(error.error_code)
    return {"valid": not reasons, "reasons": tuple(reasons)}


def is_s3_authority_packet(value: Any) -> bool:
    """True iff ``value`` is an ``R5S3AuthorityPacket`` typed instance."""
    return isinstance(value, R5S3AuthorityPacket)


def unit_variant_payload(unit: R5S3AuthorityUnitTagged) -> Any:
    """The single resident variant payload (exact by construction)."""
    if unit.variant_kind == "d09_center_pattern_unit":
        return unit.d09_variant_payload
    return unit.d10_variant_payload


__all__ = [
    "S3_PACKET_SCHEMA_ID",
    "S3_PACKET_SCHEMA_SHA256",
    "S3_EXACT_OVERLAY_SHA256",
    "S3_SOURCE_PINS_SHA256",
    "S3_MANIFEST_CONTENT_SHA256",
    "S3_HUMAN_CONTRACT_SHA256",
    "AUTHORITY_MODE_S3",
    "STAGE_STATUS_S3",
    "PACKET_ID_PREFIX",
    "PACKET_ID_GRAMMAR",
    "RECEIPT_REF_PREFIX",
    "CLUSTER_REF_PREFIX",
    "AGGREGATE_REF_PREFIX",
    "D09_MARKER_PREFIX",
    "D10_MARKER_PREFIX",
    "S3ContractError",
    "S3HashMismatchError",
    "S3CanonicalError",
    "S3InvariantError",
    "S3_DOMAINS",
    "S3_SEVERITIES",
    "S3_COVERAGE_STATES",
    "S3_RATE_STATES",
    "S3_DENOMINATOR_KINDS",
    "S3_DENOMINATOR_STATES",
    "S3_NUMERATOR_KINDS",
    "S3_MEASURE_UNITS",
    "S3_CHANGE_KINDS",
    "S3_CHANGE_CAUSES",
    "S3_VISIBILITY_STATES",
    "S3_PROJECTION_KINDS",
    "S3_TAGGED_VARIANT_KINDS",
    "S3_MEMBERSHIP_STATES",
    "S3_MEMBERSHIP_OPERATORS",
    "S3_DENOMINATOR_POLICIES",
    "S3_RATE_POLICIES",
    "S3_CONSERVATION_OPERATORS",
    "S3_DISABLED_PATH_POLICIES",
    "S3_DISABLED_STATES",
    "S3_LIFECYCLE_STATES",
    "S3_LIFECYCLE_ACTIONS",
    "S3_MARKER_KINDS",
    "S3_CLOSURE_DECISION_KINDS",
    "S3_SUPPLEMENTAL_KINDS",
    "S3_SOURCE_KINDS",
    "S3_HASH_DOMAINS",
    "S3_ERROR_CODES",
    "s3_enum_values",
    "LIFECYCLE_STATE_TABLE",
    "RESOLVED_STATE",
    "S3_LAYERS",
    "PER_LAYER_MEASURE_UNIT",
    "PER_LAYER_MEMBERSHIP_OPERATOR",
    "PER_LAYER_DENOMINATOR_POLICY",
    "PER_LAYER_RATE_POLICY",
    "PER_LAYER_CONSERVATION_OPERATOR",
    "PER_LAYER_DISABLED_PATH_POLICY",
    "PER_LAYER_SOURCE_COUNT_PATHS",
    "PER_LAYER_MEMBERSHIP_SOURCES",
    "PER_LAYER_NUMERATOR_UNIT",
    "PER_LAYER_CONSERVATION_EXPR",
    "CHANGE_EMISSION_TABLE",
    "s3_canonical_bytes",
    "s3_canonical_json",
    "s3_sha256",
    "s3_object_content_hash",
    "s3_content_hash_excluding",
    "receipt_content_hash",
    "authority_receipt_ref",
    "unit_content_hash",
    "lifecycle_content_hash",
    "cluster_content_hash",
    "aggregate_identity_id",
    "R5S3ClinicalDomainAuthority",
    "R5S3DenominatorAuthority",
    "R5S3LayerMembershipAuthority",
    "R5S3CutoffAuthority",
    "R5S3EvaluationLimitAuthority",
    "R5S3CoverageAuthority",
    "R5S3ChangeCauseMixtureAuthority",
    "R5S3ClosureAuthority",
    "R5S3RiskLifecycleAuthority",
    "R5S3D09CenterPatternUnit",
    "R5S3D10ProjectUnit",
    "R5S3AuthorityUnitTagged",
    "R5S3LowRiskCluster",
    "R5S3AggregateReceiptSetIdentity",
    "R5S3AudiencePayload",
    "R5S3AuthorityPacket",
    "audience_replay_content_hash",
    "compute_packet_integrity_hash",
    "compute_packet_id",
    "S3_PUBLIC_ALLOWLIST",
    "S3_TYPED_INPUT_DENYLIST_MODULES",
    "check_imported_objects_allowed",
    "check_supplemental_receipt_bindings",
    "validate_s3_authority_packet",
    "is_s3_authority_packet",
    "unit_variant_payload",
    "FROZEN_INVARIANT_ERROR_CODES",
]
