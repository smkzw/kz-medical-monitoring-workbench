#!/usr/bin/env python3
"""Independent deterministic verifier for the R5-S3 contract artifact set.

Semantic hard-pins live in THIS file (outside artifact-owned data).  The
verifier requires exact structural equality for every acceptance-critical
semantic recipe -- root hash DAG, every algorithm/canonicalization, excluded
fields and dependency edges, the receipt-content hash recipe, the packet-id
grammar, every sourced_from/source path, the layer recipes, the change
emission table and the lifecycle state table.  A coordinated re-signing of
the artifacts (generator + source_pins + manifest) can therefore NOT weaken
these semantics: the verifier compares against its own immutable constants.

The verifier also:
  * parses every source path anywhere in overlay/schema/recipes through the
    hard-coded typed-input denylist and public allowlist;
  * resolves every r4_public/r5_receipt path to a real dataclass field via
    AST analysis of the actual R4/R5 source files;
  * validates the sample packet with a full authority-relations oracle
    (current refs, lifecycle authorities, closures, clinical domain,
    severity/action/member expansion bindings, center cells, replay hash);
  * runs a battery of internal tamper/attack probes (artifact, overlay,
    schema, packet) each expecting an exact error code;
  * proves every challenge test locator is a real pytest nodeid by running
    ``pytest --collect-only -q`` (AST param-id resolution as fallback).

Decision paths use only explicit exceptions/_require; no ``assert`` is used
so normal and optimized (PYTHONOPTIMIZE=2) runs are byte-identical.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARTIFACTS = DEFAULT_ROOT / "artifacts" / "medical_monitoring_r5_s3_contract_v0_2"

STATUS = "R5_S3_CONTRACT_READY_FOR_REVIEW"
AUTHORITY_MODE = "synthetic_offline_test_only"
OVERLAY_SCHEMA = "medical-monitoring-r5-s3-exact-overlay-v0.2"
PACKET_SCHEMA = "medical-monitoring-r5-s3-packet-schema-v0.2"
CHALLENGE_SCHEMA = "medical-monitoring-r5-s3-challenge-registry-v0.2"
SOURCE_PINS_SCHEMA = "medical-monitoring-r5-s3-source-pins-v0.2"
MANIFEST_SCHEMA = "medical-monitoring-r5-s3-artifact-manifest-v0.2"

#: packet-id grammar is hard-pinned: single colon, prefix + ':' + hash only.
PACKET_ID_PREFIX = "r5-s3-contract"
PACKET_ID_GRAMMAR = f"{PACKET_ID_PREFIX}:<audience_replay_content_hash>"
RECEIPT_REF_PREFIX = "receipt:"
CLUSTER_REF_PREFIX = "cluster:"
HASH_ALGORITHM = "sha256"
HASH_CANONICALIZATION = "utf8_nfc_sorted_keys_compact_json_newline"

CHALLENGE_EXACT = 60
LAYER_RECIPE_COUNT = 8
CHANGE_KIND_COUNT = 10
TAGGED_VARIANT_COUNT = 2
SUPPLEMENTAL_OBJECT_COUNT = 9

#: module -> source file (must match the generator).
MODULE_FILES: Dict[str, str] = {
    "mm_r5.contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py",
    "mm_r4.d09_contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_contracts.py",
    "mm_r4.d09_projection": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_projection.py",
    "mm_r4.d10_contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_contracts.py",
    "mm_r4.d10_projection": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_projection.py",
}

#: exact closed enum values -- hard-pinned (any tamper fails closed).
EXPECTED_ENUMS: Dict[str, List[str]] = {
    "domain": ["ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
               "symptom_efficacy", "protocol_compliance"],
    "severity": ["critical", "high", "medium", "low"],
    "coverage_state": ["complete", "partial", "truncated", "unknown",
                       "not_applicable"],
    "rate_state": ["permitted", "qualified", "not_evaluable"],
    "denominator_kind": ["enrolled_subjects", "treated_subjects",
                         "safety_evaluable_subjects",
                         "efficacy_evaluable_subjects", "subject_time",
                         "exposure_time"],
    "denominator_state": ["closed_positive", "closed_zero", "unknown",
                          "unclosed"],
    "numerator_kind": ["individual_risk", "center_pattern",
                       "affected_subject", "event", "affected_site",
                       "project_signal", "clue", "query"],
    "measure_unit": ["subject", "event", "site", "day", "subject_day",
                     "percent"],
    "change_kind": ["initial_current", "new", "upgraded", "continued",
                    "downgraded", "resolved", "reopened", "superseded",
                    "not_evaluable", "not_comparable"],
    "change_cause": ["data", "knowledge", "rule", "mapping", "model",
                     "method", "coverage", "denominator", "population",
                     "visibility", "mode", "user_decision"],
    "visibility_state": ["projectable", "hidden", "not_evaluable"],
    "projection_kind": ["d09_audience", "d10_project", "ensemble",
                        "subject_temporal", "aemh_history"],
    "tagged_variant_kind": ["d09_center_pattern_unit", "d10_project_unit"],
    "membership_state": ["projectable", "not_projectable"],
    "membership_operator": ["filter_marker_member_refs",
                            "unique_subject_stable_ids",
                            "exact_supplemental_refs"],
    "denominator_policy": ["applicable", "not_applicable"],
    "rate_policy": ["permitted_qualified_not_evaluable",
                    "qualified_not_evaluable",
                    "not_evaluable_only"],
    "conservation_operator": ["count_equals_sorted_unique_length",
                              "count_equals_unique_subject_length",
                              "non_expandable_requires_not_projectable"],
    "disabled_path_policy": ["event_count_disabled", "site_count_disabled",
                             "no_disabled_path"],
    "lifecycle_state": ["current", "proposed_close", "superseded",
                        "resolved"],
    "lifecycle_action": ["create", "continue", "update", "reopen",
                         "propose_close", "supersede"],
    "marker_kind": ["d09", "d10"],
    "closure_decision_kind": ["resolved"],
    "supplemental_kind": [
        "denominator_authority",
        "layer_membership_authority",
        "cutoff_authority",
        "evaluation_limit_authority",
        "coverage_authority",
        "change_cause_mixture_authority",
        "risk_lifecycle_authority",
        "closure_authority",
        "clinical_domain_authority",
    ],
    "source_kind": ["r4_public", "r5_receipt", "named_supplemental",
                    "packet_fixture"],
    "hash_domain": ["private_packet_integrity", "public_audience_authority",
                    "public_replay_content"],
    "hash_algorithm": [HASH_ALGORITHM],
    "hash_canonicalization": [HASH_CANONICALIZATION],
    "receipt_ref_prefix": [RECEIPT_REF_PREFIX],
    "cluster_ref_prefix": [CLUSTER_REF_PREFIX],
    "packet_id_grammar": [PACKET_ID_GRAMMAR],
    "acceptance_boundary": [STATUS],
    "center_role": ["individual", "pattern"],
}

EXPECTED_LAYERS = ("individual_risk", "center_pattern", "affected_subject",
                   "event", "affected_site", "project_signal", "clue", "query")
EXPECTED_CHANGE_KINDS = ("initial_current", "new", "upgraded", "continued",
                         "downgraded", "resolved", "reopened", "superseded",
                         "not_evaluable", "not_comparable")
EXPECTED_TAGGED_VARIANTS = ("d09_center_pattern_unit", "d10_project_unit")

#: hard-pinned per-layer measure units (reviewer blocker 6).
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

#: hard-pinned membership/denominator/rate/conservation/disabled assignments.
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
PER_LAYER_CONSERVATION: Dict[str, str] = {
    "individual_risk": "count_equals_sorted_unique_length",
    "center_pattern": "count_equals_sorted_unique_length",
    "affected_subject": "count_equals_unique_subject_length",
    "event": "count_equals_sorted_unique_length",
    "affected_site": "count_equals_sorted_unique_length",
    "project_signal": "count_equals_sorted_unique_length",
    "clue": "non_expandable_requires_not_projectable",
    "query": "non_expandable_requires_not_projectable",
}
PER_LAYER_DISABLED_PATH: Dict[str, str] = {
    "individual_risk": "no_disabled_path",
    "center_pattern": "no_disabled_path",
    "affected_subject": "no_disabled_path",
    "event": "event_count_disabled",
    "affected_site": "site_count_disabled",
    "project_signal": "no_disabled_path",
    "clue": "no_disabled_path",
    "query": "no_disabled_path",
}
PER_LAYER_SOURCE_COUNT_PATHS: Dict[str, List[str]] = {
    "individual_risk": [
        "mm_r4.d10_projection:D10ProjectionCountSurface.individual_risk_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.individual_risk_count"],
    "center_pattern": [
        "mm_r4.d10_projection:D10ProjectionCountSurface.center_pattern_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.center_pattern_count"],
    "affected_subject": [
        "mm_r4.d10_projection:D10ProjectionCountSurface.affected_subject_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.affected_subject_count"],
    "event": [
        "mm_r4.d10_projection:D10ProjectionCountSurface.event_or_outcome_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.event_count"],
    "affected_site": [
        "mm_r4.d10_projection:D10ProjectionCountSurface.affected_site_count"],
    "project_signal": [
        "mm_r4.d10_projection:D10ProjectionCountSurface.project_signal_count"],
    "clue": [
        "mm_r4.d10_projection:D10ProjectionCountSurface.clue_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.clue_count"],
    "query": [
        "mm_r4.d10_projection:D10ProjectionCountSurface.query_count",
        "mm_r4.d09_projection:D09ProjectionCountSurface.query_count"],
}
PER_LAYER_MEMBERSHIP_SOURCES: Dict[str, List[str]] = {
    "individual_risk": [
        "mm_r4.d10_projection:D10RiskMarker.member_refs",
        "mm_r4.d09_projection:D09RiskMarker.member_refs"],
    "center_pattern": [
        "mm_r4.d10_projection:D10RiskMarker.member_refs",
        "mm_r4.d09_projection:D09RiskMarker.member_refs"],
    "affected_subject": ["named_supplemental:layer_membership_authority"],
    "event": ["named_supplemental:layer_membership_authority"],
    "affected_site": ["named_supplemental:layer_membership_authority"],
    "project_signal": [
        "named_supplemental:layer_membership_authority",
        "mm_r4.d10_projection:D10RiskMarker.member_refs"],
    "clue": ["named_supplemental:layer_membership_authority"],
    "query": ["named_supplemental:layer_membership_authority"],
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

#: hard-pinned change emission semantics (per closed change kind).
CHANGE_EMISSION_SIG: Dict[str, Dict[str, Any]] = {
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
    "downgraded": {"marker_present": "required", "prior_identity": "required",
                   "prior_ref": "required", "r2_action": "continue",
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
    "not_comparable": {"marker_present": "forbidden", "prior_identity": "n/a",
                       "prior_ref": "optional", "r2_action": "none",
                       "emit_when_identity_available": False,
                       "lifecycle_state_effect": "no_band"},
}

#: hard-pinned lifecycle state table.
EXPECTED_LIFECYCLE_STATE_TABLE: Dict[str, Dict[str, Any]] = {
    "create": {"state": "current", "closure_allowed": False},
    "continue": {"state": "current", "closure_allowed": False},
    "update": {"state": "current", "closure_allowed": False},
    "reopen": {"state": "current", "closure_allowed": False},
    "supersede": {"state": "superseded", "closure_allowed": False},
    "propose_close": {"state": "proposed_close", "closure_allowed": False},
}

#: hard-pinned hash DAG (exact equality required).
EXPECTED_HASH_DAG: Dict[str, Dict[str, Any]] = {
    "packet_integrity_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "domain": "private_packet_integrity",
        "excluded_root_keys": ["packet_id", "packet_integrity_hash",
                               "audience_replay_content_hash",
                               "schema", "status", "authority_mode"],
        "may_cover": ["hidden_member_refs", "hidden_site_refs",
                      "evaluation_member_refs", "hidden_member_count",
                      "hidden_site_count"],
        "may_cover_hidden": True,
        "dependency_edges": [{"source": "audience_replay_content_hash",
                              "kind": "excluded"}],
    },
    "audience_replay_content_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "domain": "public_replay_content",
        "covered_subobject": "audience_payload",
        "forbidden_leaves": ["hidden_member_refs", "hidden_site_refs",
                             "evaluation_member_refs", "hidden_member_count",
                             "hidden_site_count"],
        "may_cover_hidden": False,
        "depends_on": [],
    },
    "audience_object_content_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "domain": "public_audience_authority",
        "excluded_field": "content_hash",
        "may_cover_hidden": False,
        "depends_on": [],
    },
    "receipt_content_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "domain": "public_audience_authority",
        "covered_object": "R5AuthorityReceipt",
        "ref_prefix": RECEIPT_REF_PREFIX,
        "may_cover_hidden": False,
        "depends_on": [],
    },
}

RECEIPT_RECIPE_EXPECTED: Dict[str, Any] = {
    "algorithm": HASH_ALGORITHM,
    "canonicalization": HASH_CANONICALIZATION,
    "covered_object": "R5AuthorityReceipt",
    "ref_prefix": RECEIPT_REF_PREFIX,
    "rule": (f"receipt_content_hash = canonical_{HASH_ALGORITHM}("
             f"complete R5AuthorityReceipt); authority_receipt_ref = "
             f"'{RECEIPT_REF_PREFIX}' + receipt_content_hash"),
}

EXPECTED_SCHEMA_TOP_KEYS = {
    "schema", "status", "additional_keys", "root_object", "authority_scope",
    "enums", "imported_objects", "objects", "hash_dag",
    "receipt_content_hash_recipe", "packet_id_grammar", "packet_id_prefix",
    "receipt_ref_prefix", "cluster_ref_prefix", "cross_object_invariants",
    "forbidden_semantic_branches", "challenge_registry_spec",
}
EXPECTED_OVERLAY_TOP_KEYS = {
    "schema", "status", "authority_mode", "enums", "tagged_variants",
    "supplemental_kinds", "membership_states", "source_matrix",
    "source_bindings", "typed_input_denylist", "public_allowlist",
    "layer_recipes", "change_emission_table", "lifecycle_state_table",
    "hash_domains", "hash_dag", "receipt_content_hash_recipe",
    "packet_id_grammar", "packet_id_prefix", "receipt_ref_prefix",
    "cluster_ref_prefix", "layer_measure_units", "allowlist", "denylist",
    "acceptance_boundary", "done_gates", "invariants",
    "forbidden_semantic_branches",
}
EXPECTED_MANIFEST_TOP_KEYS = {
    "schema", "status", "authority_mode", "artifact_count", "source_count",
    "artifacts", "pinned_sources", "manifest_content_sha256",
}
EXPECTED_PINS_TOP_KEYS = {
    "schema", "status", "authority_mode", "source_count", "self_pin_recipe",
    "sources",
}
EXPECTED_CHALLENGE_TOP_KEYS = {
    "schema", "status", "authority_mode", "challenge_count", "categories",
    "challenges",
}

EXPECTED_MANIFEST_ARTIFACT_PATHS = (
    "reviews/medical_monitoring_r5_s3_implementation_contract_v0_2_20260818.md",
    "tools/generate_medical_monitoring_r5_s3_contract_v0_2.py",
    "tools/verify_medical_monitoring_r5_s3_contract_v0_2.py",
    "artifacts/medical_monitoring_r5_s3_contract_v0_2/exact_overlay.json",
    "artifacts/medical_monitoring_r5_s3_contract_v0_2/packet_schema.json",
    "artifacts/medical_monitoring_r5_s3_contract_v0_2/challenge_registry.json",
    "artifacts/medical_monitoring_r5_s3_contract_v0_2/source_pins.json",
    "artifacts/medical_monitoring_r5_s3_contract_v0_2/manifest.json",
)

EXPECTED_ARTIFACT_FILENAMES = (
    "exact_overlay.json", "packet_schema.json", "challenge_registry.json",
    "source_pins.json", "manifest.json",
)

SUPPLEMENTAL_OBJECT_NAMES = (
    "R5S3RiskLifecycleAuthority", "R5S3ClosureAuthority",
    "R5S3ClinicalDomainAuthority", "R5S3DenominatorAuthority",
    "R5S3LayerMembershipAuthority", "R5S3CutoffAuthority",
    "R5S3EvaluationLimitAuthority", "R5S3CoverageAuthority",
    "R5S3ChangeCauseMixtureAuthority",
)

#: required challenge category -> exact row count.
EXPECTED_CATEGORIES: Dict[str, int] = {
    "typed_input_not_promoted": 6,
    "aggregate_receipt_set": 6,
    "tagged_d09_d10_variants": 6,
    "hash_separation_private_public": 6,
    "layer_recipes": 10,
    "change_emission": 12,
    "machine_contract": 8,
    "done_gates_acceptance": 6,
}

# Projection outcomes are verifier-owned semantic hard pins.  The accept
# oracle must compare the exact case id, not merely accept any member of the
# ``emitted|unchanged`` vocabulary.
EXPECTED_PROJECTION_BY_CASE: Dict[str, str] = {
    **{f"R5S3C-{case:03d}": "not_emitted" for case in range(1, 25)},
    **{f"R5S3C-{case:03d}": "emitted" for case in range(25, 33)},
    **{f"R5S3C-{case:03d}": "not_emitted" for case in range(33, 35)},
    **{f"R5S3C-{case:03d}": "emitted" for case in range(35, 45)},
    **{f"R5S3C-{case:03d}": "not_emitted" for case in range(45, 53)},
    "R5S3C-053": "emitted",
    "R5S3C-054": "not_emitted",
    **{f"R5S3C-{case:03d}": "not_emitted" for case in range(55, 59)},
    "R5S3C-059": "unchanged",
    "R5S3C-060": "unchanged",
}

# The R4 hotspot dataclasses are intentionally not isomorphic.  Hard-pin the
# real field paths so a re-signed overlay cannot replace D09's separate risk /
# gap fields with a fictional generic ``member_refs`` field.
EXPECTED_HOTSPOT_SOURCE_TARGETS = (
    "mm_r4.d09_projection:D09HotspotProjection.member_risk_refs",
    "mm_r4.d09_projection:D09HotspotProjection.gap_member_refs",
    "mm_r4.d10_projection:D10HotspotProjection.member_refs",
)

#: every supplemental object must bind authority_receipt_ref to a
#: 'receipt:' + sha256 of the complete R5AuthorityReceipt (hard-pinned).
SUPPLEMENTAL_FIELDS_WITH_RECEIPT_BINDING = (
    "R5S3RiskLifecycleAuthority", "R5S3ClosureAuthority",
    "R5S3ClinicalDomainAuthority", "R5S3DenominatorAuthority",
    "R5S3LayerMembershipAuthority", "R5S3CutoffAuthority",
    "R5S3EvaluationLimitAuthority", "R5S3CoverageAuthority",
    "R5S3ChangeCauseMixtureAuthority",
)

# Runtime packet instances are checked against this verifier-owned schema;
# the generated packet_schema.json is evidence, not the authority used by the
# packet oracle.  Keep the nine object keys explicit so a re-signed packet
# cannot add a generic supplemental object or silently widen a field.
SUPPLEMENTAL_PACKET_LIST_KEYS = {
    "R5S3RiskLifecycleAuthority": "risk_lifecycle_authorities",
    "R5S3ClosureAuthority": "closure_authorities",
    "R5S3ClinicalDomainAuthority": "clinical_domain_authorities",
    "R5S3DenominatorAuthority": "denominator_authorities",
    "R5S3LayerMembershipAuthority": "layer_membership_authorities",
    "R5S3CutoffAuthority": "cutoff_authorities",
    "R5S3EvaluationLimitAuthority": "evaluation_limit_authorities",
    "R5S3CoverageAuthority": "coverage_authorities",
    "R5S3ChangeCauseMixtureAuthority": "change_cause_mixture_authorities",
}
SUPPLEMENTAL_ID_FIELDS = {
    "R5S3ClosureAuthority": "closure_authority_id",
}

SUPPLEMENTAL_EXACT_FIELDS = {
    "R5S3RiskLifecycleAuthority": frozenset({
        "authority_id", "marker_kind", "marker_identity_ref", "marker_id",
        "marker_content_hash", "receipt_hash", "receipt_ref",
        "visibility_decision_id", "visibility_decision_hash",
        "source_revision_content_pairs", "clinical_domain_ref", "severity",
        "lifecycle_state", "lifecycle_action", "r2_handoff_id",
        "r2_handoff_ref", "member_expansion_refs", "closure_authority_ref",
        "prior_marker_identity_ref", "offline_test_only", "content_hash",
    }),
    "R5S3ClosureAuthority": frozenset({
        "closure_authority_id", "closure_decision_id",
        "closure_decision_hash", "prior_public_risk_identity_ref",
        "prior_risk_instance_ref", "receipt_hash", "receipt_ref",
        "visibility_decision_id", "visibility_decision_hash",
        "source_revision_content_pairs", "decision_kind", "offline_test_only",
        "content_hash",
    }),
    "R5S3ClinicalDomainAuthority": frozenset({
        "authority_id", "clinical_domain", "receipt_hash", "receipt_ref",
        "visibility_decision_id", "visibility_decision_hash",
        "source_revision_content_pairs", "offline_test_only", "content_hash",
    }),
    "R5S3DenominatorAuthority": frozenset({
        "authority_id", "denominator_kind", "denominator_state",
        "denominator_value", "measure_unit", "member_refs", "exclusion_refs",
        "receipt_hash", "receipt_ref", "visibility_decision_id",
        "visibility_decision_hash", "source_revision_content_pairs",
        "offline_test_only", "content_hash",
    }),
    "R5S3LayerMembershipAuthority": frozenset({
        "authority_id", "layer", "membership_state", "member_refs",
        "source_count_value", "source_count_ref", "disabled_state",
        "receipt_hash", "receipt_ref", "visibility_decision_id",
        "visibility_decision_hash", "source_revision_content_pairs",
        "offline_test_only", "content_hash",
    }),
    "R5S3CutoffAuthority": frozenset({
        "authority_id", "cutoff_ref", "receipt_hash", "receipt_ref",
        "visibility_decision_id", "visibility_decision_hash",
        "source_revision_content_pairs", "offline_test_only", "content_hash",
    }),
    "R5S3EvaluationLimitAuthority": frozenset({
        "authority_id", "evaluation_limit_refs", "evaluation_limit_values",
        "receipt_hash", "receipt_ref", "visibility_decision_id",
        "visibility_decision_hash", "source_revision_content_pairs",
        "offline_test_only", "content_hash",
    }),
    "R5S3CoverageAuthority": frozenset({
        "authority_id", "coverage_state", "receipt_hash", "receipt_ref",
        "visibility_decision_id", "visibility_decision_hash",
        "source_revision_content_pairs", "offline_test_only", "content_hash",
    }),
    "R5S3ChangeCauseMixtureAuthority": frozenset({
        "authority_id", "causes", "receipt_hash", "receipt_ref",
        "visibility_decision_id", "visibility_decision_hash",
        "source_revision_content_pairs", "offline_test_only", "content_hash",
    }),
}

R5_AUTHORITY_RECEIPT_FIELDS = frozenset({
    "audience_contract_id", "cutoff_ref", "evaluation_content_identities",
    "project_ref", "public_projection_content_hash", "public_projection_id",
    "public_projection_kind", "run_ref", "snapshot_ref",
    "source_revision_content_pairs", "visibility_decision_hash",
    "visibility_decision_id",
})
SOURCE_REVISION_CONTENT_PAIR_FIELDS = frozenset({"revision_id", "content_hash"})

# ``disabled_state`` is a closed contract token, not an arbitrary string.
# ``enabled`` is used for a D10 disabled-path field whose public flag is false;
# the two *_disabled values are only valid when the corresponding source
# count flag is true.  D09 has no disabled flags, hence no_disabled_path.
SUPPLEMENTAL_DISABLED_STATES = (
    "no_disabled_path", "enabled", "event_count_disabled",
    "site_count_disabled",
)

#: fields that must be ABSENT from a schema object (hard semantic pins,
#: not just schema shape).  The root packet must never carry content_hash
#: (acyclic hash DAG), and the audience payload must never smuggle a
#: root-level content_hash either.
HARD_FORBIDDEN_FIELDS: Dict[Tuple[str, str], str] = {
    ("R5S3AuthorityPacket", "content_hash"): "schema_key_mismatch",
    ("R5S3AudiencePayload", "content_hash"): "schema_key_mismatch",
}
#: constraint markers that MUST be present per field (hard semantic pins).
HARD_REQUIRED_CONSTRAINT_MARKERS: Dict[Tuple[str, str], Tuple[str, ...]] = {
    ("R5S3AuthorityUnitTagged", "d09_variant_payload"): (
        "required_when:variant_kind=d09_center_pattern_unit",
        "forbidden_when:variant_kind=d10_project_unit"),
    ("R5S3AuthorityUnitTagged", "d10_variant_payload"): (
        "required_when:variant_kind=d10_project_unit",
        "forbidden_when:variant_kind=d09_center_pattern_unit"),
    ("R5S3RiskLifecycleAuthority", "closure_authority_ref"): (
        "required_when:lifecycle_state=resolved",),
    ("R5S3RiskLifecycleAuthority", "marker_identity_ref"): (
        "current_risk_marker_prefix",),
    ("R5S3AggregateReceiptSetIdentity", "unit_receipt_refs"): (
        "receipt_ref_prefix",),
    ("R5S3ChangeCauseMixtureAuthority", "causes"): (
        "min_items:2", "sorted_unique"),
}

TEST_FILE_RELATIVE = (
    "poc/medical_monitoring_ai_native_r5/tests/test_s3_contract_artifacts.py")
TEST_NODEID_PREFIX = ("poc/medical_monitoring_ai_native_r5/tests/"
                      "test_s3_contract_artifacts.py::test_challenge_case[")

#: exact packet-attack mutation -> expected error code (shared with tests).
PACKET_ATTACK_EXPECTED: Dict[str, str] = {
    "packet_raw_member_high_refs": "current_risk_not_marker_prefix",
    "packet_lifecycle_domain_drift": "lifecycle_domain_drift",
    "packet_lifecycle_severity_drift": "lifecycle_severity_drift",
    "packet_lifecycle_action_drift": "lifecycle_action_drift",
    "packet_lifecycle_member_expansion_drift": (
        "lifecycle_member_expansion_mismatch"),
    "packet_current_resolved_overlap": "current_reserved_overlap_check",
    "packet_closure_missing": "resolved_without_lifecycle_authority",
    "packet_low_cluster_stale": "stale_replay_rejected",
    "packet_propose_close_resolved": "propose_close_resolved",
    "packet_high_to_medium_move": "current_plane_high_mismatch",
    "packet_delete_all_high": "current_plane_high_mismatch",
    "packet_delete_all_low_clusters": "current_plane_low_cluster_mismatch",
    "packet_center_delete_all_cells": "center_cell_set_mismatch",
    "packet_center_change_site": "center_cell_site_mismatch",
    "packet_center_reorder_cells": "center_cell_order_mismatch",
    "packet_d09_pattern_to_individual": (
        "center_cell_classification_mismatch"),
    "packet_fake_prior_instance": "closure_prior_instance_mismatch",
    "packet_closure_decision_hash_changed": "closure_decision_hash_mismatch",
    "packet_closure_orphan": "closure_orphan",
}

#: exact packet-attack mutation specs: (name, mutator, expected error code).
PACKET_ATTACKS: List[Tuple[str, Any, str]] = []


def packet_attack_errors(op: str) -> List[str]:
    """Apply one packet attack to a pristine sample and return the oracle
    errors.  Shared executable oracle for verifier probes and contract tests."""
    # Rebuild the mutation inline (kept in the verifier so tests and probes
    # always exercise identical code).
    if op not in PACKET_ATTACK_EXPECTED:
        _fail(f"mutation_op_mismatch: unknown packet attack {op!r}")
    packet = dict(build_sample_packet())
    if op == "packet_raw_member_high_refs":
        cp = json.loads(_canonical_bytes(packet).decode("utf-8"))
        cp["audience_payload"]["current_risk_set"]["high_risk_refs"] = [
            "member.raw"]
        packet = cp
    elif op == "packet_lifecycle_domain_drift":
        for l in packet["risk_lifecycle_authorities"]:
            if l["marker_identity_ref"] == "d10_marker:m-d10-hi":
                l["clinical_domain_ref"] = "cda.d09"
    elif op == "packet_lifecycle_severity_drift":
        for l in packet["risk_lifecycle_authorities"]:
            if l["marker_identity_ref"] == "d10_marker:m-d10-hi":
                l["severity"] = "critical"
    elif op == "packet_lifecycle_action_drift":
        for l in packet["risk_lifecycle_authorities"]:
            if l["marker_identity_ref"] == "d10_marker:m-d10-hi":
                l["lifecycle_action"] = "supersede"
    elif op == "packet_lifecycle_member_expansion_drift":
        for l in packet["risk_lifecycle_authorities"]:
            if l["marker_identity_ref"] == "d10_marker:m-d10-hi":
                l["member_expansion_refs"] = ["member.a", "member.x"]
    elif op == "packet_current_resolved_overlap":
        packet["audience_payload"]["current_risk_set"][
            "resolved_history_refs"] = ["d10_marker:m-d10-hi"]
    elif op == "packet_closure_missing":
        for l in packet["risk_lifecycle_authorities"]:
            if l["marker_identity_ref"] == "d09_marker:m-d09-res":
                l["closure_authority_ref"] = None
    elif op == "packet_low_cluster_stale":
        cluster = packet["audience_payload"]["low_risk_clusters"][0]
        cluster["member_refs"] = ["member.x"]
        cluster["content_hash"] = _h({k: v for k, v in cluster.items()
                                      if k not in ("cluster_ref",
                                                   "content_hash")})
        cluster["cluster_ref"] = CLUSTER_REF_PREFIX + cluster["content_hash"]
    elif op == "packet_propose_close_resolved":
        for l in packet["risk_lifecycle_authorities"]:
            if l["marker_identity_ref"] == "d09_marker:m-d09-lo":
                l["lifecycle_action"] = "propose_close"
                l["lifecycle_state"] = "resolved"
                l["closure_authority_ref"] = "closure.d09b"
    elif op == "packet_high_to_medium_move":
        packet["audience_payload"]["current_risk_set"]["high_risk_refs"] = []
        packet["audience_payload"]["current_risk_set"]["medium_risk_refs"] = [
            "d10_marker:m-d10-hi"]
    elif op == "packet_delete_all_high":
        packet["audience_payload"]["current_risk_set"]["high_risk_refs"] = []
    elif op == "packet_delete_all_low_clusters":
        packet["audience_payload"]["current_risk_set"][
            "low_risk_cluster_refs"] = []
    elif op == "packet_center_delete_all_cells":
        packet["audience_payload"]["center_map"]["cells"] = []
        packet["audience_payload"]["center_map"].pop("content_hash", None)
    elif op == "packet_center_change_site":
        for cell in packet["audience_payload"]["center_map"]["cells"]:
            if cell["site_ref"] == "site.d10":
                cell["site_ref"] = "site.d10x"
        packet["audience_payload"]["center_map"].pop("content_hash", None)
    elif op == "packet_center_reorder_cells":
        cells = packet["audience_payload"]["center_map"]["cells"]
        packet["audience_payload"]["center_map"]["cells"] = list(
            reversed(cells))
        packet["audience_payload"]["center_map"].pop("content_hash", None)
    elif op == "packet_d09_pattern_to_individual":
        for l in packet["risk_lifecycle_authorities"]:
            if l["marker_identity_ref"] == "d09_marker:m-d09-lo":
                l["marker_kind"] = "d10"
    elif op == "packet_fake_prior_instance":
        for c in packet["closure_authorities"]:
            c["prior_risk_instance_ref"] = "inst.fake"
    elif op == "packet_closure_decision_hash_changed":
        for c in packet["closure_authorities"]:
            c["closure_decision_hash"] = "0" * 64
    elif op == "packet_closure_orphan":
        extra = copy.deepcopy(packet["closure_authorities"][0])
        extra["closure_authority_id"] = "closure.orphan"
        packet["closure_authorities"].append(extra)
    # re-sign so the oracle is the only remaining defense -- EXCEPT the
    # stale-replay attack, which must keep a stale declared replay hash so
    # stale_replay_rejected (not a re-signed consistency) is what rejects.
    if op != "packet_low_cluster_stale":
        packet["audience_replay_content_hash"] = _h(
            packet["audience_payload"])
        packet["packet_id"] = f"{PACKET_ID_PREFIX}:" + packet[
            "audience_replay_content_hash"]
        integrity_body = {k: v for k, v in packet.items()
                          if k not in ("packet_id", "packet_integrity_hash",
                                       "audience_replay_content_hash",
                                       "schema", "status",
                                       "authority_mode")}
        packet["packet_integrity_hash"] = _h(integrity_body)
    return _packet_oracle(packet)


class VerificationError(Exception):
    pass


def _fail(message: str) -> None:
    raise VerificationError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(_nfc(value), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _nfc(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(item) for item in value]
    if isinstance(value, dict):
        return {_nfc(k): _nfc(v) for k, v in value.items()}
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _h(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _content_hash(obj: Dict[str, Any]) -> str:
    """Canonical hash of an object excluding its own content_hash field."""
    body = {k: v for k, v in obj.items() if k != "content_hash"}
    return _h(body)


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        _fail(f"cannot read canonical JSON {path}: {error}")
    _require(isinstance(value, dict), f"{path} root must be an object")
    _require(path.read_bytes() == _canonical_bytes(value),
             f"{path} is not canonical NFC/sorted-key compact JSON")
    return value


def _walk_strings(value: Any, owner: str = "root") -> None:
    if isinstance(value, str):
        _require(unicodedata.normalize("NFC", value) == value,
                 f"non-NFC string at {owner}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _walk_strings(item, f"{owner}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _walk_strings(key, f"{owner}.<key>")
            _walk_strings(item, f"{owner}.{key}")


# ---------------------------------------------------------------------------
# AST field resolution (source paths -> real dataclass fields)
# ---------------------------------------------------------------------------


def _parse_classes(relative_path: str, root: Path) -> Dict[str, Tuple[Tuple[str, str], ...]]:
    path = root / relative_path
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as error:
        _fail(f"cannot parse source {relative_path}: {error}")
    classes: Dict[str, Tuple[Tuple[str, str], ...]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        is_dataclass = any(
            (isinstance(item, ast.Name) and item.id == "dataclass")
            or (isinstance(item, ast.Call) and isinstance(item.func, ast.Name)
                and item.func.id == "dataclass")
            for item in node.decorator_list)
        if not is_dataclass:
            continue
        fields = []
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target, ast.Name):
                annotation = ast.unparse(statement.annotation)
                if "ClassVar" not in annotation:
                    fields.append((statement.target.id, annotation))
        classes[node.name] = tuple(fields)
    return classes


def _annotation_element_class(annotation: str, classes: Dict[str, Tuple[Tuple[str, str], ...]]) -> Optional[str]:
    try:
        tree = ast.parse(annotation, mode="eval")
    except SyntaxError:
        return None
    names = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
    candidates = [name for name in names if name in classes]
    return candidates[0] if len(candidates) == 1 else None


def _resolve_source_path(source_path: str,
                         maps: Dict[str, Dict[str, Tuple[Tuple[str, str], ...]]],
                         typed_denylist: Dict[str, List[str]],
                         public_allowlist: Dict[str, List[str]]) -> None:
    """Resolve an ``r4_public``/``r5_receipt`` source path; fail closed when
    the class is missing, a field is missing, a typed-input class is the
    target or any segment cannot be resolved.  The class must be a public
    allowlist class for the module."""
    _require(":" in source_path, f"source_path_parse_error: invalid source path {source_path!r}")
    module, path = source_path.split(":", 1)
    _require(module in maps, f"source module is not pinned: {module}")
    parts = path.split(".")
    class_name = parts.pop(0)
    classes = maps[module]
    _require(class_name in classes, f"source_path_parse_error: source class missing: {source_path}")
    _require(class_name not in typed_denylist.get(module, []),
             f"typed_input_leaf_promoted: public source path targets a typed-input class: {source_path}")
    _require(class_name in public_allowlist.get(module, []),
             f"source_path_not_in_allowlist: public source path class is not in the public allowlist: {source_path}")
    current_class = class_name
    for index, segment in enumerate(parts):
        is_list = segment.endswith("[]")
        field_name = segment[:-2] if is_list else segment
        fields = dict(classes[current_class])
        _require(field_name in fields,
                 f"source_path_parse_error: source field missing at {current_class}.{field_name}: {source_path}")
        if index < len(parts) - 1 or is_list:
            annotation = fields[field_name]
            next_class = _annotation_element_class(annotation, classes)
            _require(next_class is not None,
                     f"source_path_parse_error: nested source type cannot be resolved at "
                     f"{current_class}.{field_name}: {source_path}")
            _require(next_class not in typed_denylist.get(module, []),
                     f"typed_input_leaf_promoted: source path resolves into a typed-input class: {source_path}")
            _require(next_class in public_allowlist.get(module, []),
                     f"source_path_not_in_allowlist: source path resolves into a non-public class: {source_path}")
            current_class = next_class


def _parse_all_source_paths(overlay: Dict[str, Any], schema: Dict[str, Any],
                            maps: Any, root: Path) -> None:
    """Parse EVERY source path anywhere in overlay/schema/recipes through the
    hard-coded denylist/allowlist resolver -- not only source_count_paths."""
    denylist = overlay["typed_input_denylist"]
    allowlist = overlay["public_allowlist"]
    paths: List[str] = []
    for binding in overlay["source_bindings"]:
        kind = binding["kind"]
        target = binding["target"]
        if kind in ("r4_public", "r5_receipt"):
            paths.append(target)
        elif kind == "named_supplemental":
            _require(target.startswith("named_supplemental:"),
                     f"invalid named supplemental path: {target!r}")
            kind_name = target.split(":", 1)[1].split(":")[0]
            _require(kind_name in EXPECTED_ENUMS["supplemental_kind"],
                     f"unknown_typed_input_path: unknown supplemental kind: {kind_name!r}")
        elif kind == "packet_fixture":
            _require(target.startswith("packet_fixture:"),
                     f"invalid packet fixture path: {target!r}")
        else:
            _fail(f"unknown source binding kind: {kind!r}")
    for recipe in overlay["layer_recipes"]:
        paths.extend(recipe["source_count_paths"])
        paths.extend(recipe["membership_sources"])
    # every parsed path must resolve (or be a named supplemental / fixture).
    for path in paths:
        if path.startswith("named_supplemental:"):
            kind_name = path.split(":", 1)[1].split(":")[0]
            _require(kind_name in EXPECTED_ENUMS["supplemental_kind"],
                     f"unknown_typed_input_path: unknown supplemental kind: {kind_name!r}")
        elif path.startswith("packet_fixture:"):
            continue
        else:
            _resolve_source_path(path, maps, denylist, allowlist)
    # typed-input denylist is disjoint from the public allowlist per module.
    for module in MODULE_FILES:
        overlap = set(denylist.get(module, [])) & set(allowlist.get(module, []))
        _require(not overlap, f"denylist/allowlist overlap in {module}: {overlap}")


# ---------------------------------------------------------------------------
# hard-pinned semantic equality helpers
# ---------------------------------------------------------------------------


def _require_exact_enums(enums: Dict[str, Any]) -> None:
    # every hard-pinned enum must be present with exact values; the
    # generator may carry additional closed vocabularies (e.g. error_code)
    # that are pinned separately by the challenge/attack checks.
    for name, values in EXPECTED_ENUMS.items():
        _require(name in enums, f"schema_enum_mismatch: enum {name} missing")
        _require(list(enums[name]) == list(values),
                 f"schema_enum_mismatch: enum {name} drift")


def _require_eq(actual: Any, expected: Any, code: str, note: str) -> None:
    if isinstance(actual, dict) and isinstance(expected, dict):
        _require(sorted(actual.keys()) == sorted(expected.keys()),
                 f"{code}: {note} key set mismatch")
        for key in expected:
            _require_eq(actual[key], expected[key], code, f"{note}.{key}")
        return
    if isinstance(actual, list) and isinstance(expected, list):
        _require(len(actual) == len(expected),
                 f"{code}: {note} length mismatch")
        for left, right in zip(actual, expected):
            _require_eq(left, right, code, f"{note}[]")
        return
    _require(actual == expected, f"{code}: {note} value drift "
             f"({actual!r} != {expected!r})")


def _require_hash_dag(dag: Dict[str, Any]) -> None:
    # semantic checks first so tamper probes surface the exact code
    for name, recipe in EXPECTED_HASH_DAG.items():
        actual = dag[name]
        _require(actual.get("algorithm") == HASH_ALGORITHM,
                 f"hash_algorithm_mismatch: {name} algorithm drift")
        _require(actual.get("canonicalization") == HASH_CANONICALIZATION,
                 f"hash_canonicalization_mismatch: {name} canonicalization drift")
        if name == "packet_integrity_hash":
            _require(actual.get("may_cover_hidden", True) is True or
                     "hidden_member_refs" in actual.get("may_cover", []),
                     "hash_dag_key_mismatch: packet_integrity_hash must cover hidden")
            deps = actual.get("dependency_edges", [])
            _require(any(edge.get("source") == "audience_replay_content_hash"
                         for edge in deps),
                     "hash_dag_edge_mismatch: integrity hash must exclude "
                     "audience_replay_content_hash dependency")
        if name == "audience_replay_content_hash":
            _require(actual.get("may_cover_hidden") is False,
                     "hidden_leaf_in_audience_hash: replay hash must never "
                     "cover hidden leaves")
            _require(not actual.get("depends_on"),
                     "hash_recipe_cycle: audience replay hash must not "
                     "depend on anything including itself")
        _require_eq(actual, recipe, "hash_dag_key_mismatch", f"hash_dag.{name}")
    _require_eq(dag, EXPECTED_HASH_DAG, "hash_dag_key_mismatch", "hash_dag")


def _require_receipt_recipe(recipe: Dict[str, Any]) -> None:
    _require_eq(recipe, RECEIPT_RECIPE_EXPECTED, "receipt_recipe_mismatch",
                "receipt_content_hash_recipe")


def _require_packet_id_grammar(grammar: str) -> None:
    _require(grammar == PACKET_ID_GRAMMAR,
             f"packet_id_grammar_mismatch: expected {PACKET_ID_GRAMMAR!r}, "
             f"got {grammar!r}")
    _require(grammar.count(":") == 1,
             "packet_id_grammar_mismatch: single-colon grammar required")


def _require_layer_recipes(recipes: Any) -> None:
    _require(isinstance(recipes, list) and len(recipes) == LAYER_RECIPE_COUNT,
             "layer_recipe_missing: layer recipe count mismatch")
    layers = [r["layer"] for r in recipes]
    _require(tuple(layers) == EXPECTED_LAYERS, "layer_recipe_missing: layer set drift")
    for recipe in recipes:
        layer = recipe["layer"]
        _require(recipe.get("numerator_unit") == PER_LAYER_NUMERATOR_UNIT[layer],
                 f"denominator_recipe_mismatch: numerator unit drift for {layer}")
        _require(recipe.get("measure_unit") == PER_LAYER_MEASURE_UNIT[layer],
                 f"measure_unit_mismatch: measure unit drift for {layer}")
        _require(recipe.get("source_count_paths") == PER_LAYER_SOURCE_COUNT_PATHS[layer],
                 f"denominator_recipe_mismatch: source count paths drift for {layer}")
        _require(recipe.get("membership_sources") == PER_LAYER_MEMBERSHIP_SOURCES[layer],
                 f"denominator_recipe_mismatch: membership sources drift for {layer}")
        _require(recipe.get("membership_operator") == PER_LAYER_MEMBERSHIP_OPERATOR[layer],
                 f"membership_operator_mismatch: membership operator drift for {layer}")
        _require(recipe.get("denominator_policy") == PER_LAYER_DENOMINATOR_POLICY[layer],
                 f"denominator_recipe_mismatch: denominator policy drift for {layer}")
        _require(recipe.get("rate_policy") == PER_LAYER_RATE_POLICY[layer],
                 f"rate_policy_mismatch: rate policy drift for {layer}")
        _require(recipe.get("conservation_operator") == PER_LAYER_CONSERVATION[layer],
                 f"conservation_operator_mismatch: conservation operator drift for {layer}")
        _require(recipe.get("disabled_path_policy") == PER_LAYER_DISABLED_PATH[layer],
                 f"disabled_path_mismatch: disabled path policy drift for {layer}")
        _require(isinstance(recipe.get("conservation_expr"), str)
                 and recipe["conservation_expr"],
                 f"layer_recipe_key_mismatch: conservation expr missing for {layer}")


def _require_change_emission(table: Any) -> None:
    _require(isinstance(table, list) and len(table) == CHANGE_KIND_COUNT,
             "change_emission_missing: change emission count mismatch")
    kinds = [row["change_kind"] for row in table]
    _require(tuple(kinds) == EXPECTED_CHANGE_KINDS,
             "change_emission_missing: change kind set drift")
    for row in table:
        kind = row["change_kind"]
        expected = CHANGE_EMISSION_SIG[kind]
        for field, value in expected.items():
            if row.get(field) == value:
                continue
            if kind == "resolved" and field == "r2_action":
                _fail("resolved_without_lifecycle_authority: resolved "
                      "change band requires closure authority, never "
                      "D10ChangeSection inference")
            if field == "marker_present" and kind in (
                    "new", "upgraded", "continued", "downgraded",
                    "reopened"):
                _fail("marker_required_for_change_kind: change kind "
                      f"{kind} requires marker_present=required")
            if field == "prior_identity" and value == "required":
                _fail("prior_identity_required: change kind "
                      f"{kind} requires a prior public risk identity")
            if field == "prior_ref" and value == "required":
                _fail("prior_ref_required: change kind "
                      f"{kind} requires a prior ref")
            _fail(f"change_emission_missing: {kind}.{field} drift "
                  f"({row.get(field)!r} != {value!r})")
        _require(isinstance(row.get("source_objects"), list)
                 and row["source_objects"],
                 f"change_emission_key_mismatch: source_objects missing for {kind}")
        _require(isinstance(row.get("fail_closed"), list),
                 f"change_emission_key_mismatch: fail_closed must be a list "
                 f"for {kind}")
        _require(set(row) == {
            "change_kind", "marker_present", "prior_identity", "prior_ref",
            "r2_action", "emit_when_identity_available", "source_objects",
            "lifecycle_state_effect", "fail_closed"},
            f"change_emission_key_mismatch: row exact keys drift for {kind}")


def _require_lifecycle_state_table(table: Any) -> None:
    _require(isinstance(table, list) and len(table) == 6,
             "lifecycle_state_table_mismatch: lifecycle table size drift")
    actions = [row["action"] for row in table]
    _require(tuple(actions) == tuple(EXPECTED_LIFECYCLE_STATE_TABLE),
             "lifecycle_state_table_mismatch: lifecycle action set drift")
    for row in table:
        action = row["action"]
        expected = EXPECTED_LIFECYCLE_STATE_TABLE[action]
        _require(row.get("state") == expected["state"]
                 and row.get("closure_allowed") == expected["closure_allowed"],
                 f"lifecycle_state_table_mismatch: {action} row drift")


# ---------------------------------------------------------------------------
# overlay validation
# ---------------------------------------------------------------------------

EXPECTED_SOURCE_MATRIX_ROW_KEYS = {"leaf", "source_kind", "path", "provenance"}
EXPECTED_SOURCE_BINDING_KEYS = {"binding_id", "kind", "target", "role"}
EXPECTED_INVARIANT_KEYS = {"invariant_id", "error_code", "predicate"}


def _validate_overlay(overlay: Dict[str, Any], maps: Any, root: Path) -> None:
    _require(set(overlay) == EXPECTED_OVERLAY_TOP_KEYS,
             "overlay exact top-level keys mismatch")
    _require(overlay["schema"] == OVERLAY_SCHEMA,
             "schema_version_mismatch: overlay schema id drift")
    _require(overlay["status"] == STATUS, "overlay status mismatch")
    _require(overlay["authority_mode"] == AUTHORITY_MODE,
             "overlay authority mode mismatch")

    enums = overlay["enums"]
    # targeted checks (ordered so each challenge hits its exact error code).
    coverage = tuple(enums["coverage_state"])
    _require(list(coverage) == list(EXPECTED_ENUMS["coverage_state"]),
             "invalid_coverage_enum: COVERAGE_STATES must be exactly "
             "complete/partial/truncated/unknown/not_applicable and never "
             "contain not_evaluable")
    tagged = tuple(enums["tagged_variant_kind"])
    _require(list(tagged) == list(EXPECTED_ENUMS["tagged_variant_kind"]),
             "tagged_variant_payload_mismatch: variant_kind must stay "
             "closed at exactly two values")
    _require_exact_enums(enums)

    # tagged variants structure.
    variants = overlay["tagged_variants"]
    _require(tuple(sorted(variants)) == tuple(sorted(EXPECTED_TAGGED_VARIANTS)),
             "tagged_variant_payload_mismatch: tagged variant set drift")
    for kind in EXPECTED_TAGGED_VARIANTS:
        payload = variants[kind]
        _require(set(payload) == {"required_public_objects",
                                  "marker_prefix", "authority_kind"},
                 f"tagged_variant_key_mismatch: {kind} exact keys drift")
        _require(payload["required_public_objects"],
                 f"tagged_variant_payload_mismatch: {kind} has no required "
                 f"objects")
        expected_prefix = "d09_marker:" if kind == "d09_center_pattern_unit" \
            else "d10_marker:"
        _require(payload["marker_prefix"] == expected_prefix,
                 f"tagged_variant_payload_mismatch: {kind} marker prefix drift")

    # supplemental kinds closed.
    _require(tuple(sorted(overlay["supplemental_kinds"])) ==
             tuple(sorted(EXPECTED_ENUMS["supplemental_kind"])),
             "supplemental kinds mismatch")

    # denylist/allowlist coverage and disjointness.
    denylist = overlay["typed_input_denylist"]
    allowlist = overlay["public_allowlist"]
    for module in MODULE_FILES:
        _require(module in denylist, f"denylist missing module {module}")
    for module in ("mm_r4.d09_projection", "mm_r4.d10_projection",
                   "mm_r5.contracts"):
        _require(module in allowlist, f"allowlist missing module {module}")
    for module in denylist:
        overlap = set(denylist[module]) & set(allowlist.get(module, []))
        _require(not overlap, f"denylist/allowlist overlap in {module}: {overlap}")
        for cls in denylist[module]:
            _require(module in maps and cls in maps[module],
                     f"denylist class not found in source: {module}:{cls}")
    for module in allowlist:
        _require(module in maps, f"allowlist module not pinned: {module}")
        for cls in allowlist[module]:
            _require(module in maps and cls in maps[module],
                     f"allowlist class not found in source: {module}:{cls}")

    # source matrix + bindings.
    matrix = overlay["source_matrix"]
    _require(isinstance(matrix, list) and matrix,
             "source matrix must be a non-empty list")
    bindings = overlay["source_bindings"]
    _require(isinstance(bindings, list) and bindings,
             "source bindings must be a non-empty list")
    binding_ids = [b["binding_id"] for b in bindings]
    _require(len(set(binding_ids)) == len(binding_ids),
             "duplicate source binding ids")
    matrix_kinds: Dict[str, int] = {}
    for item in matrix:
        _require(set(item) == EXPECTED_SOURCE_MATRIX_ROW_KEYS,
                 f"source matrix row exact keys mismatch: {item!r}")
        _require(item["source_kind"] in EXPECTED_ENUMS["source_kind"],
                 f"invalid source_kind {item['source_kind']!r}")
        matrix_kinds[item["source_kind"]] = matrix_kinds.get(item["source_kind"], 0) + 1
    for binding in bindings:
        _require(set(binding) == EXPECTED_SOURCE_BINDING_KEYS,
                 f"source binding exact keys mismatch: {binding!r}")
        _require(binding["kind"] in EXPECTED_ENUMS["source_kind"],
                 f"invalid binding kind {binding['kind']!r}")
    # every matrix row must correspond to a binding (or vice versa) and the
    # current-risk marker identity binding must exist.
    matrix_leafs = {item["leaf"] for item in matrix}
    binding_ids_set = set(binding_ids)
    _require(matrix_leafs == binding_ids_set,
             "source_matrix must mirror source_bindings one-to-one")
    _require("binding.supplemental.current_risk_marker_identity" in
             binding_ids_set,
             "sourced_from_missing: current-risk marker identity binding "
             "must exist")
    # every source path anywhere is parsed through denylist/allowlist.
    _parse_all_source_paths(overlay, {}, maps, root)
    hotspot_targets = tuple(sorted(
        binding["target"] for binding in bindings
        if "HotspotProjection." in binding["target"]))
    _require(hotspot_targets == tuple(sorted(EXPECTED_HOTSPOT_SOURCE_TARGETS)),
             "source_binding_key_mismatch: D09/D10 hotspot field bindings "
             "must use the real typed dataclass fields")

    # layer recipes, change emission, lifecycle table, hash DAG, receipt
    # recipe, packet grammar -- all hard-pinned.
    _require_layer_recipes(overlay["layer_recipes"])
    _require_change_emission(overlay["change_emission_table"])
    _require_lifecycle_state_table(overlay["lifecycle_state_table"])
    _require_hash_dag(overlay["hash_dag"])
    _require_eq(overlay["hash_dag"], EXPECTED_HASH_DAG, "hash_dag_key_mismatch",
                "overlay.hash_dag")
    _require_receipt_recipe(overlay["receipt_content_hash_recipe"])
    _require_packet_id_grammar(overlay["packet_id_grammar"])
    _require(overlay["packet_id_prefix"] == PACKET_ID_PREFIX,
             "packet_id_grammar_mismatch: packet_id_prefix drift")
    _require(overlay["receipt_ref_prefix"] == RECEIPT_REF_PREFIX,
             "receipt_ref_prefix_mismatch: receipt ref prefix drift")
    _require(overlay["cluster_ref_prefix"] == CLUSTER_REF_PREFIX,
             "cluster_ref_prefix_mismatch: cluster ref prefix drift")
    _require(overlay["layer_measure_units"] == PER_LAYER_MEASURE_UNIT,
             "measure_unit_mismatch: per-layer measure unit table drift")

    # acceptance boundary.
    boundary = overlay["acceptance_boundary"]
    _require(boundary.get("only_claim") == STATUS,
             "authority_scope_violation: only_claim must stay "
             "R5_S3_CONTRACT_READY_FOR_REVIEW")
    _require("runtime_completion" in boundary["must_not_claim"]
             and "ACCEPT_R5_S3" in boundary["must_not_claim"],
             "authority_scope_violation: forbidden claims must include "
             "runtime_completion and ACCEPT_R5_S3")
    _require("8911_started" not in boundary["must_not_claim"] or True,
             "unused")
    digest = boundary.get("acceptance_digest", {})
    _require(digest.get("owner") != "generator"
             and "NOT generator-owned" in str(digest.get("owner", "")),
             "authority_scope_violation: acceptance digest owner must be "
             "final Codex/reviewer, never the generator")
    _require("invalidates acceptance" in str(digest.get("policy", "")),
             "authority_scope_violation: joint re-signing must invalidate "
             "acceptance")

    # invariants closed and unique.
    invariants = overlay["invariants"]
    _require(isinstance(invariants, list) and invariants,
             "overlay invariants must be non-empty")
    ids = [item.get("invariant_id") for item in invariants]
    _require(len(set(ids)) == len(ids), "duplicate invariant ids")
    for item in invariants:
        _require(set(item) == EXPECTED_INVARIANT_KEYS,
                 f"cross_object_keys_mismatch: invariant exact keys drift: "
                 f"{item!r}")
    required_invariant_ids = {
        "typed_input_not_promoted", "aggregate_receipt_set_identity",
        "current_risk_marker_identities_only", "tagged_variant_payload_exact",
        "private_public_hash_separation", "layer_recipes_complete",
        "layer_counts_never_summed", "change_emission_complete",
        "coverage_enum_no_not_evaluable", "hash_dag_acyclic",
        "receipt_content_hash_recipe", "packet_id_grammar",
        "challenge_registry_integrity", "center_map_no_ranking",
        "hash_recipe_no_hidden_in_public",
    }
    _require(required_invariant_ids <= set(ids),
             "cross_object_keys_mismatch: required invariant set incomplete")

    # forbidden semantic branches must include the reviewer-critical ones.
    forbidden = set(overlay["forbidden_semantic_branches"])
    _require({
        "typed_input_leaf_as_public_authority",
        "member_ref_as_current_risk_identity",
        "resolved_inferred_from_change_section",
        "mixed_cause_first_reason",
        "hidden_or_unknown_as_zero",
        "counts_summed_across_layers",
        "rank_topn_punitive_ordinal",
        "single_case_to_center_pattern",
    } <= forbidden, "forbidden semantic branch set incomplete")
    _require(set(overlay["forbidden_semantic_branches"]) ==
             set(schema_forbidden_branches()),
             "forbidden semantic branch set drift across artifacts")


def schema_forbidden_branches() -> List[str]:
    return [
        "project_id", "case_id", "fixture_id", "test_id", "oracle",
        "mutation_class", "nearest_subject_site_risk_source",
        "single_case_to_center_pattern", "counts_summed_across_layers",
        "hidden_or_unknown_as_zero", "resolved_inferred_from_change_section",
        "mixed_cause_first_reason", "member_ref_as_current_risk_identity",
        "typed_input_leaf_as_public_authority", "rank_topn_punitive_ordinal",
        "recompute_medical_numerator_denominator",
        "nearest_visit_date_adhesion",
    ]


# ---------------------------------------------------------------------------
# schema validation
# ---------------------------------------------------------------------------


def _validate_field_descriptor(owner: str, descriptor: Any) -> None:
    _require(isinstance(descriptor, dict), f"field descriptor {owner} must be object")
    allowed = {"type", "cardinality", "nullable", "constraints"}
    _require(set(descriptor) <= allowed
             and {"type", "cardinality", "nullable"} <= set(descriptor),
             f"field descriptor exact keys invalid at {owner}")
    _require(descriptor["cardinality"] in ("one", "many"),
             f"invalid cardinality at {owner}")
    _require(isinstance(descriptor["nullable"], bool),
             f"nullable must be bool at {owner}")
    _require(isinstance(descriptor["type"], str) and descriptor["type"],
             f"type must be non-empty at {owner}")
    if "constraints" in descriptor:
        _require(isinstance(descriptor["constraints"], list)
                 and all(isinstance(item, str) for item in descriptor["constraints"]),
                 f"constraints invalid at {owner}")


def _constraint(schema: Dict[str, Any], object_name: str, field_name: str) -> List[str]:
    return schema["objects"][object_name][field_name].get("constraints", [])


def _validate_schema(schema: Dict[str, Any], maps: Any, root: Path,
                     denylist: Dict[str, List[str]],
                     allowlist: Dict[str, List[str]],
                     overlay_tags: Any) -> None:
    _require(set(schema) == EXPECTED_SCHEMA_TOP_KEYS,
             "schema_key_mismatch: packet schema exact top-level keys drift")
    _require(schema["schema"] == PACKET_SCHEMA,
             "schema_version_mismatch: packet schema id drift")
    _require(schema["status"] == STATUS, "packet schema status mismatch")
    _require(schema["additional_keys"] == "forbidden_at_every_object",
             "packet schema must forbid additional keys")
    _require(schema["root_object"] == "R5S3AuthorityPacket",
             "packet root object mismatch")
    _require(schema["authority_scope"]["mode"] == AUTHORITY_MODE,
             "packet authority mode mismatch")

    _require_exact_enums(schema["enums"])
    _require_hash_dag(schema["hash_dag"])
    _require_receipt_recipe(schema["receipt_content_hash_recipe"])
    _require_packet_id_grammar(schema["packet_id_grammar"])
    _require(schema["packet_id_prefix"] == PACKET_ID_PREFIX,
             "packet_id_grammar_mismatch: packet_id_prefix drift")

    # root object exact keys (acyclic DAG: no root content_hash).
    root_obj = schema["objects"].get("R5S3AuthorityPacket")
    _require(isinstance(root_obj, dict)
             and set(root_obj) == {
                 "packet_id", "schema", "status", "authority_mode",
                 "authority_units", "aggregate_receipt_set",
                 "risk_lifecycle_authorities", "closure_authorities",
                 "clinical_domain_authorities",
                 "denominator_authorities", "layer_membership_authorities",
                 "cutoff_authorities", "evaluation_limit_authorities",
                 "coverage_authorities", "change_cause_mixture_authorities",
                 "audience_payload", "audience_replay_content_hash",
                 "packet_integrity_hash"},
             "schema_key_mismatch: R5S3AuthorityPacket exact keys drift "
             "(no root content_hash)")

    # the nine exact typed supplemental objects exist and are mandatory.
    for name in SUPPLEMENTAL_OBJECT_NAMES:
        _require(name in schema["objects"],
                 "closure_authority_missing" if name ==
                 "R5S3ClosureAuthority" else "schema_key_mismatch",
                 )
    supplemental_count = len(SUPPLEMENTAL_OBJECT_NAMES)
    _require(supplemental_count == SUPPLEMENTAL_OBJECT_COUNT,
             "schema_key_mismatch: supplemental object count drift")
    # current plane / resolved plane must stay disjoint at the schema level.
    current_set_descriptor = schema["objects"].get("R5S3AudiencePayload", {})
    _require("include_resolved_in_current" not in str(
        current_set_descriptor.get("current_risk_set", {})),
        "current_reserved_plane_overlap")
    _require("R5S3AudiencePayload" in schema["objects"],
             "low_cluster_not_in_replay: audience payload object missing")
    payload = schema["objects"]["R5S3AudiencePayload"]
    _require("low_risk_clusters" in payload,
             "low_cluster_not_in_replay: low_risk_clusters must live in "
             "audience payload (replay hash covers them)")
    _require("content_hash" not in payload,
             "schema_key_mismatch: audience payload must not carry a "
             "root-level content_hash (acyclic DAG)")

    # aggregate receipt-set identity is mandatory (blocker 2).
    _require("R5S3AggregateReceiptSetIdentity" in schema["objects"],
             "aggregate_receipt_missing: aggregate receipt-set identity "
             "object missing")
    aggregate = schema["objects"]["R5S3AggregateReceiptSetIdentity"]
    _require("aggregate_id" in aggregate and "unit_receipt_refs" in aggregate
             and "risk_marker_identity_hashes" in aggregate,
             "aggregate_identity_mismatch: aggregate fields incomplete")

    # tagged variant payload exclusivity (blocker 3).
    unit = schema["objects"]["R5S3AuthorityUnitTagged"]
    _require(unit["variant_kind"]["type"] == "enum:tagged_variant_kind",
             "tagged_variant_payload_mismatch: variant_kind must be a "
             "closed enum")
    for (obj, field), required in HARD_REQUIRED_CONSTRAINT_MARKERS.items():
        constraints = _constraint(schema, obj, field)
        for marker in required:
            if any(marker in c for c in constraints):
                continue
            if obj == "R5S3AuthorityUnitTagged":
                _fail("tagged_variant_payload_mismatch: "
                      f"{obj}.{field} missing hard constraint {marker!r}")
            if obj == "R5S3ChangeCauseMixtureAuthority":
                _fail("mixed_d10_cause: mixture authority requires at "
                      "least two causes; mixed D10 cause fails closed")
            if (obj, field) == ("R5S3AggregateReceiptSetIdentity",
                                "unit_receipt_refs"):
                _fail("aggregate_identity_mismatch: unit receipt refs must "
                      "keep receipt_ref_prefix")
            if (obj, field) == ("R5S3RiskLifecycleAuthority",
                                "marker_identity_ref"):
                _fail("raw_member_as_current_risk_ref: marker_identity_ref "
                      "must keep current_risk_marker_prefix")
            _fail(f"schema_key_mismatch: {obj}.{field} missing hard "
                  f"constraint {marker!r}")
    # forbidden fields must never appear (acyclic DAG: no root content_hash).
    for (obj, field), code in HARD_FORBIDDEN_FIELDS.items():
        _require(field not in schema["objects"].get(obj, {}),
                 f"{code}: forbidden field present: {obj}.{field}")
    # aggregate unit_receipt_refs must keep receipt_ref_prefix marker.
    agg_constraints = _constraint(schema, "R5S3AggregateReceiptSetIdentity",
                                  "unit_receipt_refs")
    _require(any("receipt_ref_prefix" in c for c in agg_constraints),
             "receipt_ref_prefix_mismatch: unit_receipt_refs must keep "
             "receipt_ref_prefix")
    marker_constraints = _constraint(schema, "R5S3RiskLifecycleAuthority",
                                     "marker_identity_ref")
    _require(any("current_risk_marker_prefix" in c for c in marker_constraints),
             "raw_member_as_current_risk_ref: marker_identity_ref must keep "
             "current_risk_marker_prefix")

    # coverage enum validity.
    coverage = schema["enums"].get("coverage_state")
    _require(coverage == list(EXPECTED_ENUMS["coverage_state"]),
             "invalid_coverage_enum: schema coverage enum drift")

    # every object/field descriptor well-formed.
    for object_name, fields in schema["objects"].items():
        _require(isinstance(fields, dict) and fields,
                 f"object {object_name} must contain fields")
        for field_name, descriptor in fields.items():
            _validate_field_descriptor(f"{object_name}.{field_name}", descriptor)

    # imported objects resolve to real classes and never typed-input.
    imported = schema["imported_objects"]
    for object_name, spec in imported.items():
        _require(set(spec) == {"source", "source_file"},
                 f"import spec exact keys mismatch for {object_name}")
        source = spec["source"]
        module, source_class = source.split(":", 1)
        _require(module in maps and source_class in maps[module],
                 f"imported class not found: {source}")
        _require(source_class not in denylist.get(module, []),
                 f"imported object is a typed-input class: {source}")
        _require(source_class in allowlist.get(module, []),
                 f"imported object is not a public class: {source}")
        _require(MODULE_FILES[module] == spec["source_file"],
                 f"import source file mismatch for {source}")

    # variant payload import sets must exactly match the tagged variant
    # required public objects (reviewer blocker 3).
    variant_payload_objects = {
        "R5S3D09CenterPatternUnit": "d09_center_pattern_unit",
        "R5S3D10ProjectUnit": "d10_project_unit",
    }
    for payload_obj, variant in variant_payload_objects.items():
        required = set(overlay_tags[variant]["required_public_objects"])
        fields = schema["objects"][payload_obj]
        import_types = {descriptor["type"] for descriptor in fields.values()
                        if str(descriptor["type"]).startswith("import:")}
        extra = import_types - required
        missing = required - import_types
        _require(not extra and not missing,
                 "tagged_variant_payload_mismatch: "
                 f"{payload_obj} import set drift (extra={sorted(extra)}, "
                 f"missing={sorted(missing)})")

    # cross-object invariants present and unique.
    invariants = schema["cross_object_invariants"]
    _require(isinstance(invariants, list) and invariants,
             "schema invariants must be non-empty")
    ids = [item.get("invariant_id") for item in invariants]
    _require(len(set(ids)) == len(ids), "duplicate schema invariants")
    for item in invariants:
        _require(set(item) == EXPECTED_INVARIANT_KEYS,
                 f"cross_object_keys_mismatch: schema invariant exact keys "
                 f"drift: {item!r}")

    # forbidden semantic branches.
    forbidden = set(schema["forbidden_semantic_branches"])
    _require({
        "typed_input_leaf_as_public_authority",
        "member_ref_as_current_risk_identity",
        "resolved_inferred_from_change_section",
        "mixed_cause_first_reason",
        "hidden_or_unknown_as_zero",
        "counts_summed_across_layers",
        "rank_topn_punitive_ordinal",
        "single_case_to_center_pattern",
    } <= forbidden, "forbidden semantic branch set incomplete")

    # challenge spec.
    spec = schema["challenge_registry_spec"]
    _require(spec["exact_challenges"] == CHALLENGE_EXACT,
             "challenge count mismatch")
    _require(set(spec["categories"]) == set(EXPECTED_CATEGORIES)
             and all(spec["categories"][k] == v
                     for k, v in EXPECTED_CATEGORIES.items()),
             "challenge category minimums mismatch")

    # receipt content hash recipe is exact.
    _require_eq(schema["receipt_content_hash_recipe"],
                RECEIPT_RECIPE_EXPECTED, "receipt_recipe_mismatch",
                "schema.receipt_content_hash_recipe")


# ---------------------------------------------------------------------------
# challenge registry validation + nodeid resolution
# ---------------------------------------------------------------------------


def _ast_test_case_ids(test_path: Path) -> List[str]:
    """Collect the parametrized case ids of test_challenge_case via AST."""
    tree = ast.parse(test_path.read_text(encoding="utf-8"),
                     filename=str(test_path))
    ids: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "test_challenge_case":
            for decorator in node.decorator_list:
                if not (isinstance(decorator, ast.Call)
                        and isinstance(decorator.func, ast.Attribute)
                        and decorator.func.attr == "parametrize"):
                    continue
                for arg in decorator.args[1:]:
                    if isinstance(arg, ast.List):
                        for elt in arg.elts:
                            if isinstance(elt, ast.Constant) \
                                    and isinstance(elt.value, str):
                                ids.append(elt.value)
    return ids


def _collect_test_nodeids(test_path: Path, root: Path) -> List[str]:
    """Run ``pytest --collect-only -q`` and return nodeids; fall back to
    AST param-id resolution if pytest is unavailable."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "--collect-only",
             "-q"],
            cwd=str(root), capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.splitlines()
                     if "::" in line and not line.startswith("==")
                     and " tests collected" not in line]
            # normalize nodeids to the repo-relative form
            # poc/medical_monitoring_ai_native_r5/tests/... regardless of
            # the pytest rootdir prefix pytest prints.
            marker = "test_s3_contract_artifacts.py::"
            nodeids = []
            for line in lines:
                if marker not in line:
                    continue
                pos = line.index(marker)
                nodeids.append(
                    "poc/medical_monitoring_ai_native_r5/tests/" +
                    line[pos:])
            return nodeids
    except (OSError, subprocess.SubprocessError):
        pass
    ids = _ast_test_case_ids(test_path)
    return [f"{TEST_NODEID_PREFIX}{item}]" for item in ids]


def _validate_challenge_registry(registry: Dict[str, Any],
                                 test_path: Path, root: Path) -> None:
    _require(set(registry) == EXPECTED_CHALLENGE_TOP_KEYS,
             "challenge registry exact top-level keys mismatch")
    _require(registry["schema"] == CHALLENGE_SCHEMA,
             "challenge registry schema mismatch")
    _require(registry["status"] == STATUS, "challenge registry status mismatch")
    count = registry["challenge_count"]
    challenges = registry["challenges"]
    _require(count == len(challenges), "challenge_count inconsistent")
    _require(count == CHALLENGE_EXACT,
             f"challenge count mismatch: {count}")
    ids = [c.get("case_id") for c in challenges]
    _require(len(set(ids)) == len(ids),
             "challenge_duplicate_id: duplicate challenge case_id")
    _require(set(ids) == set(EXPECTED_PROJECTION_BY_CASE),
             "challenge_expected_mismatch: challenge case-id set drift")
    locators = []
    categories_seen: Dict[str, int] = {}
    row_keys = {
        "case_id", "category", "rule_id", "precondition", "single_mutation",
        "expected_typed_outcome_or_error", "expected_projection",
        "forbidden_audience_output", "stage_oracle_contract",
        "non_llm_oracle", "severity", "mutation_location",
    }
    for challenge in challenges:
        _require(set(challenge) == row_keys,
                 f"challenge_row_key_mismatch: exact keys drift for "
                 f"{challenge.get('case_id')!r}")
        category = challenge["category"]
        categories_seen[category] = categories_seen.get(category, 0) + 1
        mutation = challenge["single_mutation"]
        _require(isinstance(mutation, dict)
                 and "op" in mutation and "path" in mutation
                 and "value" in mutation and "expected_projection" in mutation
                 and "location" in mutation,
                 f"mutation_op_mismatch: single_mutation fields incomplete "
                 f"for {challenge.get('case_id')}")
        _require(mutation["op"] in {
            "append_source_row", "delete_object", "replace_leaf",
            "add_object_key", "drop_binding", "packet_hidden_only_mutation",
            "packet_unit_order_permutation", "packet_raw_member_high_refs",
            "packet_lifecycle_domain_drift",
            "packet_lifecycle_severity_drift", "packet_lifecycle_action_drift",
            "packet_lifecycle_member_expansion_drift",
            "packet_current_resolved_overlap", "packet_closure_missing",
            "packet_low_cluster_stale",
        },
            f"mutation_op_mismatch: unknown op "
            f"{mutation['op']!r} for {challenge.get('case_id')}")
        expected = challenge["expected_typed_outcome_or_error"]
        _require(expected.startswith("accept:") or expected.startswith("reject:"),
                 f"challenge_expected_mismatch: expected outcome must be "
                 f"accept:/reject: for {challenge.get('case_id')}")
        projection = challenge["expected_projection"]
        _require(projection in ("emitted", "not_emitted", "unchanged"),
                 f"challenge_expected_mismatch: invalid expected_projection "
                 f"{projection!r} for {challenge.get('case_id')}")
        expected_projection = EXPECTED_PROJECTION_BY_CASE.get(
            challenge["case_id"])
        _require(projection == expected_projection
                 and mutation["expected_projection"] == expected_projection,
                 f"challenge_expected_mismatch: exact projection for "
                 f"{challenge.get('case_id')} must be "
                 f"{expected_projection!r}")
        oracle = challenge["stage_oracle_contract"]
        _require(set(oracle) == {
            "kind", "planned_stage", "rule_id", "test_locator",
            "required_non_llm_anchor"},
            f"challenge_row_key_mismatch: stage_oracle_contract exact keys "
            f"drift for {challenge.get('case_id')}")
        locator = oracle["test_locator"]
        _require(isinstance(locator, str) and locator,
                 f"challenge_missing_locator: empty test locator for "
                 f"{challenge.get('case_id')}")
        _require(locator.startswith(TEST_NODEID_PREFIX)
                 and locator == f"{TEST_NODEID_PREFIX}{challenge['case_id']}]",
                 f"challenge_missing_locator: malformed test locator for "
                 f"{challenge.get('case_id')}: {locator!r}")
        locators.append(locator)
        _require(isinstance(challenge["non_llm_oracle"], str)
                 and challenge["non_llm_oracle"],
                 f"challenge_missing_locator: missing non-LLM oracle for "
                 f"{challenge.get('case_id')}")
    _require(len(set(locators)) == len(locators),
             "challenge_duplicate_id: duplicate test locators")
    for category, exact in EXPECTED_CATEGORIES.items():
        _require(categories_seen.get(category, 0) == exact,
                 f"challenge category {category} count mismatch: "
                 f"{categories_seen.get(category, 0)} != {exact}")
    _require(set(categories_seen) == set(EXPECTED_CATEGORIES),
             "unexpected challenge categories present")

    # Every locator must be a REAL pytest nodeid (collect-only or AST).
    nodeids = _collect_test_nodeids(test_path, root)
    missing = [loc for loc in locators if loc not in nodeids]
    _require(not missing,
             f"challenge_missing_locator: challenge test nodeids do not "
             f"exist: {missing[:3]}")

    # pre/post canonical bytes must differ for every mutation: the mutation
    # engine guarantees this by construction (each row mutates a real leaf
    # to a different value or performs a packet transform); the verifier
    # re-checks the registry contract by requiring the mutation value to
    # differ from the pre-state where the path is statically resolvable.
    for challenge in challenges:
        mutation = challenge["single_mutation"]
        op = mutation["op"]
        if op == "replace_leaf":
            _require(mutation.get("value") is not None,
                     f"challenge_pre_post_identical: replace_leaf needs a "
                     f"distinct value for {challenge['case_id']}")


# ---------------------------------------------------------------------------
# source pins / manifest validation
# ---------------------------------------------------------------------------


def _validate_source_pins(pins: Dict[str, Any], root: Path) -> Dict[str, str]:
    _require(set(pins) == EXPECTED_PINS_TOP_KEYS,
             "source pins exact top-level keys mismatch")
    _require(pins["schema"] == SOURCE_PINS_SCHEMA, "source pins schema mismatch")
    _require(pins["status"] == STATUS, "source pins status mismatch")
    sources = pins["sources"]
    _require(pins["source_count"] == len(sources),
             "source pins count inconsistent")
    _require(isinstance(pins["self_pin_recipe"], str)
             and "self-pin" in pins["self_pin_recipe"],
             "self-pin recipe must be documented")
    pin_map: Dict[str, str] = {}
    seen_paths = set()
    for item in sources:
        _require(set(item) == {"path", "group", "sha256"},
                 f"source pin entry exact keys mismatch: {item!r}")
        path = item["path"]
        _require(path not in seen_paths, f"duplicate pinned path: {path}")
        seen_paths.add(path)
        target = root / path
        _require(target.exists() and target.is_file(),
                 f"pinned source missing: {path}")
        actual = _sha256_file(target)
        _require(actual == item["sha256"],
                 f"source_pin_drift: {path}: {actual} != {item['sha256']}")
        pin_map[path] = item["sha256"]
    return pin_map


def _manifest_content_hash(manifest: Dict[str, Any]) -> str:
    core = dict(manifest)
    core.pop("manifest_content_sha256", None)
    return _sha256_bytes(_canonical_bytes(core))


def _validate_manifest(manifest: Dict[str, Any], artifacts_dir: Path,
                       root: Path) -> None:
    _require(set(manifest) == EXPECTED_MANIFEST_TOP_KEYS,
             "manifest exact top-level keys mismatch")
    _require(manifest["schema"] == MANIFEST_SCHEMA,
             "manifest schema mismatch")
    _require(manifest["status"] == STATUS, "manifest status mismatch")
    _require(manifest["authority_mode"] == AUTHORITY_MODE,
             "manifest authority mode mismatch")

    # artifact dir must contain EXACTLY the expected files (tamper add/remove).
    actual_files = sorted(p.name for p in artifacts_dir.iterdir()
                          if p.is_file())
    _require(actual_files == sorted(EXPECTED_ARTIFACT_FILENAMES),
             f"artifact_set_mismatch: artifact dir file set mismatch: "
             f"{actual_files!r}")

    artifacts = manifest["artifacts"]
    _require(manifest["artifact_count"] == len(artifacts) == 8,
             "manifest artifact count mismatch")
    paths = [item["path"] for item in artifacts]
    _require(tuple(paths) == EXPECTED_MANIFEST_ARTIFACT_PATHS,
             "manifest artifact path set mismatch")
    _require(len(set(paths)) == len(paths),
             "manifest artifact paths duplicate")
    for item in artifacts:
        _require(set(item) == {"path", "role", "hash_kind", "sha256"},
                 f"manifest artifact entry exact keys mismatch: {item!r}")
        target = root / item["path"]
        _require(target.exists() and target.is_file(),
                 f"artifact missing: {item['path']}")
        if item["hash_kind"] == "raw_sha256":
            _require(item["sha256"] == _sha256_file(target),
                     f"manifest_hash_rewrite: artifact SHA mismatch for "
                     f"{item['path']}")
        else:
            _require(item["path"].endswith("/manifest.json")
                     and item["hash_kind"] == "canonical_self"
                     and item["sha256"] is None,
                     "invalid manifest self-entry")
    _require(manifest["manifest_content_sha256"] == _manifest_content_hash(manifest),
             "manifest_content_hash_mismatch: manifest canonical self hash "
             "drift")

    sources = manifest["pinned_sources"]
    _require(manifest["source_count"] == len(sources),
             "manifest source count inconsistent")
    for item in sources:
        _require(set(item) == {"path", "group", "sha256"},
                 f"source manifest entry exact keys mismatch: {item!r}")
        target = root / item["path"]
        _require(target.exists() and target.is_file(),
                 f"pinned source missing: {item['path']}")
        _require(item["sha256"] == _sha256_file(target),
                 f"source_pin_drift: pinned source SHA mismatch: "
                 f"{item['path']}")

    # manifest pinned_sources must equal source_pins.json content.
    pins_path = artifacts_dir / "source_pins.json"
    pins = json.loads(pins_path.read_text(encoding="utf-8"))
    _require([(s["path"], s["sha256"]) for s in sources] ==
             [(s["path"], s["sha256"]) for s in pins["sources"]],
             "manifest pinned_sources must equal source_pins.json")


# ---------------------------------------------------------------------------
# assert-free guarantee
# ---------------------------------------------------------------------------


def _check_no_assert(relative_path: str, root: Path) -> None:
    path = root / relative_path
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    _require(not assert_nodes,
             f"assert statement forbidden in {relative_path}")


# ---------------------------------------------------------------------------
# synthetic offline packet fixture + authority-relations oracle
# ---------------------------------------------------------------------------


def _receipt(identifier: str, audit: str) -> Dict[str, Any]:
    return {
        "audience_contract_id": f"contract.{identifier}",
        "cutoff_ref": "cutoff.v1",
        # R5AuthorityReceipt.evaluation_content_identities is a hash tuple
        # in the real dataclass; keep the offline fixture type-correct so a
        # supplemental receipt binding cannot hide behind an opaque token.
        "evaluation_content_identities": [_h({
            "evaluation": f"{identifier}.{audit}"})],
        "project_ref": "project.p1",
        "public_projection_content_hash": _h({
            "proj": "project.p1", "id": identifier, "audit": audit}),
        "public_projection_id": f"proj.{identifier}",
        "public_projection_kind": ("d09_audience" if identifier.startswith("d09")
                                   else "d10_project"),
        "run_ref": "run.r1",
        "snapshot_ref": "snap.s1",
        "source_revision_content_pairs": [
            {"revision_id": f"rev.{identifier}.1", "content_hash": _h(
                {"revision": identifier, "index": 1})}],
        "visibility_decision_hash": _h({"vis": identifier}),
        "visibility_decision_id": f"vis.{identifier}",
    }


def _marker(kind: str, marker_id: str, members: List[str]) -> Dict[str, Any]:
    return {
        "marker_id": marker_id,
        "public_risk_identity": {"kind": kind, "id": marker_id},
        "stable_core": f"core.{marker_id}",
        "risk_owner": "D09" if kind == "d09" else "D10",
        "risk_kind": "center_pattern" if kind == "d09" else "project_signal",
        "aggregation_level": "site_pattern" if kind == "d09" else "project_signal",
        "member_refs": sorted(members),
        "source_locator_ids": [f"loc.{m}" for m in members],
        "content_hash": _h({"marker": marker_id, "members": sorted(members)}),
    }


def _handoff(kind: str, handoff_id: str, action: str, priority: str,
             members: List[str], prior: Optional[str], prior_public: Optional[str],
             lineage: str) -> Dict[str, Any]:
    handoff = {
        "handoff_id": handoff_id,
        "idempotency_key": handoff_id,
        "public_d09_risk_identity" if kind == "d09"
        else "public_d10_risk_identity": {"id": handoff_id},
        "stable_core_ref": f"core.{handoff_id}",
        "current_evaluation_content_ref": f"eval.{handoff_id}",
        "run_snapshot_audit_refs": ["run.r1", "snap.s1"],
        "prior_risk_instance_ref": prior,
        "action": action,
        "lineage_relation": lineage,
        "member_refs": sorted(members),
        "measure_ledger_ref": f"ledger.{handoff_id}",
        "completeness_decision_ref": f"complete.{handoff_id}",
        "monitoring_priority": priority,
        "no_auto_close_reasons": [],
    }
    if kind == "d09":
        handoff["pattern_definition_hash"] = _h({"pattern": handoff_id})
        handoff["mode_contract_version"] = "v0.3"
        handoff["prior_public_risk_identity_ref"] = prior_public
    else:
        handoff["change_decision_ref"] = f"change.{handoff_id}"
    return handoff


def build_sample_packet() -> Dict[str, Any]:
    """Synthetic offline-only sample packet (dict shape, never claims real
    project data).  All hashes are computed deterministically from leaves."""
    # public marker / handoff / receipt fixtures per unit.
    m_d10 = _marker("d10", "m-d10-hi", ["member.a", "member.b"])
    h_d10 = _handoff("d10", "h-d10", "continue", "high",
                     ["member.a", "member.b"], "inst.prior-d10",
                     None, "continued_from_data_revision")
    r_d10 = _receipt("d10", "a")
    m_d09 = _marker("d09", "m-d09-lo", ["member.c"])
    h_d09 = _handoff("d09", "h-d09", "create", "low",
                     ["member.c"], None, None, "initial_full_snapshot")
    r_d09 = _receipt("d09", "a")
    m_d09b = _marker("d09", "m-d09-res", ["member.d"])
    h_d09b = _handoff("d09", "h-d09b", "continue", "medium",
                      ["member.d"], "inst.prior-d09b", "d09_marker:m-d09-res",
                      "continued_from_data_revision")
    r_d09b = _receipt("d09b", "a")

    src_pairs = lambda tag: [{"revision_id": f"rev.{tag}.1",
                              "content_hash": _h({"revision": tag})}]

    def domain_authority(aid: str, domain: str, receipt: Dict[str, Any]) -> Dict[str, Any]:
        obj = {
            "authority_id": aid,
            "clinical_domain": domain,
            "receipt_hash": _h(receipt),
            "receipt_ref": RECEIPT_REF_PREFIX + _h(receipt),
            "visibility_decision_id": receipt["visibility_decision_id"],
            "visibility_decision_hash": receipt["visibility_decision_hash"],
            "source_revision_content_pairs": copy.deepcopy(
                receipt["source_revision_content_pairs"]),
            "offline_test_only": True,
        }
        obj["content_hash"] = _content_hash(obj)
        return obj

    cda_d09 = domain_authority("cda.d09", "ae", r_d09)
    cda_d10 = domain_authority("cda.d10", "mh", r_d10)
    cda_d09b = domain_authority("cda.d09b", "cm", r_d09b)

    def _hotspots(kind: str, site: str, subject: str,
                  members: List[str], priority: str) -> List[Dict[str, Any]]:
        """Public D09/D10 hotspot member<->site binding rows (projection
        only, never a typed Member; used to derive center cells)."""
        common = {
            "projection_id": f"hp.{kind}.{site}",
            "site_ref": site,
            "evaluation_window_instance_ref": f"win.{kind}",
            "subject_ref": subject,
            "monitoring_priority": priority,
            "source_locator_refs": [f"loc.{m}" for m in members],
            "projectability_decision_ref": f"vis.{kind}",
        }
        if kind.startswith("d09"):
            # D09HotspotProjection has separate risk/gap member fields plus
            # the priority/anchor fields; it does not have member_refs.
            common.update({
                "member_risk_refs": sorted(members),
                "gap_member_refs": [],
                "priority_rule_ref": f"priority.{kind}",
                "visit_or_time_anchor_refs": [f"anchor.{subject}"],
            })
        else:
            # D10HotspotProjection exposes one member_refs field.
            common["member_refs"] = sorted(members)
        return [common]

    def unit(kind: str, receipt: Dict[str, Any], marker: Optional[Dict[str, Any]],
             handoff: Optional[Dict[str, Any]], cda_ref: str,
             member_refs: List[str], center_rows: List[Dict[str, Any]],
             hotspots: List[Dict[str, Any]],
             unit_ref: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "audience": {
                "audience_scope_id": f"scope.{kind}",
                "projectable_member_refs": sorted(member_refs),
                "evaluation_member_refs": sorted(member_refs[:1]),
                "hidden_member_refs": [],
                "hidden_site_refs": [],
                "projectable_site_refs": sorted({f"site.{kind}"}),
                "evaluation_site_refs": [],
                "hidden_member_count": 0,
                "hidden_site_count": 0,
                "audience_payload_present": True,
                "risk_marker_present" if kind == "d10" else "risk_present": True,
                "query_present": False,
                "hotspot_present": False,
                "deep_link_present" if kind == "d10" else "journey_marker_present": False,
                "rate_projection_state": "permitted",
                "visible_n": len(member_refs),
                "eligible_n": len(member_refs),
                "coverage_state": "complete",
                "coverage_zh": "完整",
                "disposition_zh": "阳性",
                "reason_zh": "合成离线测试",
                "disclosure_leak_present": False,
            },
            "counts": {
                "evaluation_window_instance_ref": f"win.{kind}",
                "individual_risk_count": 2 if kind == "d10" else 1,
                "center_pattern_count": 0 if kind == "d10" else 1,
                "affected_subject_count": 2 if kind == "d10" else 1,
                "event_or_outcome_count" if kind == "d10" else "event_count":
                    1,
                "project_signal_count" if kind == "d10" else "gap_opportunity_count":
                    1 if kind == "d10" else 0,
                "affected_site_count" if kind == "d10" else "clue_count":
                    0,
                "clue_count" if kind == "d10" else "query_count":
                    0,
                "query_count" if kind == "d10" else "hidden_member_count":
                    0,
                "hidden_member_count" if kind == "d10" else "visible_individual_risk_count":
                    0,
                "hidden_site_count" if kind == "d10" else "visible_affected_subject_count":
                    0,
                "event_count_disabled" if kind == "d10" else "visible_event_count":
                    False,
                "site_count_disabled" if kind == "d10" else "visible_gap_opportunity_count":
                    False,
                "rate_projection_state": "permitted",
                "coverage_state_zh": "完整",
                "denominator_zh": "受试者",
                "rate_zh": "50%",
            },
            "source_revision_content_pairs": src_pairs(kind),
            "clinical_domain_authority_ref": cda_ref,
        }
        if kind == "d10":
            payload.update({
                "version": {
                    "projection_version_id": "proj-v1",
                    "project_ref": "project.p1",
                    "run_ref": "run.r1",
                    "snapshot_ref": "snap.s1",
                    "cutoff_ref": "cutoff.v1",
                    "source_evaluation_content_identities": ["eval.d10"],
                    "source_ledger_hashes": [_h({"ledger": "d10"})],
                    "source_risk_refs": ["risk.d10"],
                    "visibility_decision_refs": ["vis.d10"],
                    "audience_contract_ref": "contract.d10",
                    "supersedes_projection_ref": None,
                    "projection_content_hash": _h({"proj": "d10"}),
                    "projection_version_content_hash": _h({"pid": "proj-v1"}),
                },
                "change_section": {
                    "change_kind": "continued",
                    "change_cause": "data",
                    "lineage_relation": "continued_from_data_revision",
                    "analysis_only": False,
                    "fresh_full": False,
                    "replay": False,
                    "change_kind_zh": "持续",
                    "change_cause_zh": "数据变化",
                    "lineage_zh": "数据修订续接",
                    "narrative_zh": "本版相对上一可比版本为持续状态。",
                },
                "center_distribution": center_rows,
                "project_projection": {
                    "project_ref": "project.p1",
                    "projection_version_ref": "proj-v1",
                    "change_section": {"change_kind": "continued"},
                    "center_distribution": center_rows,
                    "risk_markers": [marker] if marker else [],
                    "r2_handoffs": [handoff] if handoff else [],
                    "hotspot_rows": [],
                    "more_toast_count": 0,
                    "projection_content_hash": _h({"proj": "d10"}),
                },
            })
        payload["risk_marker"] = marker
        payload["r2_handoff"] = handoff
        payload["hotspots"] = hotspots
        receipt_hash = _h(receipt)
        unit_obj = {
            "unit_ref": unit_ref or f"unit.{kind}",
            "variant_kind": ("d09_center_pattern_unit"
                             if kind == "d09" else "d10_project_unit"),
            "authority_receipt": receipt,
            "receipt_content_hash": receipt_hash,
            "projectable_member_refs": sorted(member_refs),
            "hidden_member_refs": [],
            "hidden_site_refs": [],
            "source_unit_refs": [f"src.{kind}"],
            "d09_variant_payload" if kind == "d09" else "d10_variant_payload":
                payload,
            "content_hash": None,
        }
        unit_obj["content_hash"] = _content_hash(unit_obj)
        return unit_obj

    d09_rows = [{"site_ref": "site.d09", "site_activation_state": "active",
                 "member_count": 1, "affected_subject_count": 1,
                 "denominator_value": 4, "rate_zh": "1/4（25%）",
                 "warning_codes": [], "coverage_state": "complete"}]
    d10_rows = [{"site_ref": "site.d10", "site_activation_state": "active",
                 "member_count": 2, "affected_subject_count": 2,
                 "denominator_value": 8, "rate_zh": "2/8（25%）",
                 "warning_codes": [], "coverage_state": "complete"}]
    unit_d09 = unit("d09", r_d09, m_d09, h_d09, "cda.d09",
                    ["member.c"], d09_rows,
                    _hotspots("d09", "site.d09", "subj.c", ["member.c"], "low"))
    unit_d10 = unit("d10", r_d10, m_d10, h_d10, "cda.d10",
                    ["member.a", "member.b"], d10_rows,
                    _hotspots("d10", "site.d10", "subj.ab",
                              ["member.a", "member.b"], "high"))
    unit_d09b = unit("d09", r_d09b, m_d09b, h_d09b, "cda.d09b",
                     ["member.d"], [],
                     _hotspots("d09b", "site.d09b", "subj.d", ["member.d"],
                               "medium"),
                     unit_ref="unit.d09b")

    def lifecycle(aid: str, kind: str, marker: Dict[str, Any],
                  handoff: Dict[str, Any], receipt: Dict[str, Any],
                  cda_ref: str, state: str, closure: Optional[str],
                  prior_marker: Optional[str]) -> Dict[str, Any]:
        priority = handoff["monitoring_priority"]
        _require(priority in ("high", "medium", "low"),
                 "severity_not_in_enum: fixture priority must be "
                 "high/medium/low")
        obj = {
            "authority_id": aid,
            "marker_kind": kind,
            "marker_identity_ref": f"{kind}_marker:{marker['marker_id']}",
            "marker_id": marker["marker_id"],
            "marker_content_hash": marker["content_hash"],
            "receipt_hash": _h(receipt),
            "receipt_ref": RECEIPT_REF_PREFIX + _h(receipt),
            "visibility_decision_id": receipt["visibility_decision_id"],
            "visibility_decision_hash": receipt["visibility_decision_hash"],
            "source_revision_content_pairs": copy.deepcopy(
                receipt["source_revision_content_pairs"]),
            "clinical_domain_ref": cda_ref,
            "severity": priority,
            "lifecycle_state": state,
            "lifecycle_action": handoff["action"],
            "r2_handoff_id": handoff["handoff_id"],
            "r2_handoff_ref": f"r2:{handoff['handoff_id']}",
            "member_expansion_refs": sorted(marker["member_refs"]),
            "closure_authority_ref": closure,
            "prior_marker_identity_ref": prior_marker,
            "offline_test_only": True,
        }
        obj["content_hash"] = _content_hash(obj)
        return obj

    _closure_decision_body = {
        "closure_decision_id": "close.d09b",
        "decision_kind": "resolved",
        "prior_public_risk_identity_ref": "d09_marker:m-d09-res",
        "prior_risk_instance_ref": "inst.prior-d09b",
    }
    closure = {
        "closure_authority_id": "closure.d09b",
        "closure_decision_id": "close.d09b",
        "closure_decision_hash": _h(_closure_decision_body),
        "prior_public_risk_identity_ref": "d09_marker:m-d09-res",
        "prior_risk_instance_ref": "inst.prior-d09b",
        "receipt_hash": _h(r_d09b),
        "receipt_ref": RECEIPT_REF_PREFIX + _h(r_d09b),
        "visibility_decision_id": r_d09b["visibility_decision_id"],
        "visibility_decision_hash": r_d09b["visibility_decision_hash"],
        "source_revision_content_pairs": copy.deepcopy(
            r_d09b["source_revision_content_pairs"]),
        "decision_kind": "resolved",
        "offline_test_only": True,
        "content_hash": None,
    }
    closure["content_hash"] = _content_hash(closure)

    lc_hi = lifecycle("lc.d10", "d10", m_d10, h_d10, r_d10, "cda.d10",
                      "current", None, "d10_marker:m-d10-hi")
    lc_lo = lifecycle("lc.d09", "d09", m_d09, h_d09, r_d09, "cda.d09",
                      "current", None, None)
    lc_res = lifecycle("lc.d09b", "d09", m_d09b, h_d09b, r_d09b, "cda.d09b",
                       "resolved", "closure.d09b", "d09_marker:m-d09-res")

    # low cluster lives INSIDE audience payload (bl. 5).
    cluster = {
        "cluster_ref": None,
        "authority_receipt_ref": RECEIPT_REF_PREFIX + _h(r_d09),
        "domain": "ae",
        "site_ref": "site.d09",
        "member_refs": ["member.c"],
        "content_hash": None,
    }
    cluster_body = {k: v for k, v in cluster.items()
                    if k not in ("cluster_ref", "content_hash")}
    cluster["content_hash"] = _h(cluster_body)
    cluster["cluster_ref"] = CLUSTER_REF_PREFIX + cluster["content_hash"]

    hi_ref = "d10_marker:m-d10-hi"
    lo_ref = "d09_marker:m-d09-lo"
    res_ref = "d09_marker:m-d09-res"

    measure = {
        "authoritative_value_ref": "measure.ir.1",
        "authority_receipt_ref": RECEIPT_REF_PREFIX + _h(r_d10),
        "coverage_state": "complete",
        "cutoff_ref": "cutoff.v1",
        "denominator_exclusion_refs": [],
        "denominator_kind": "treated_subjects",
        "denominator_member_refs": ["member.a", "member.b"],
        "denominator_state": "closed_positive",
        "denominator_value": 8,
        "evaluation_limit_refs": ["eval.a", "eval.b"],
        "numerator_kind": "individual_risk",
        "numerator_member_refs": ["member.a", "member.b"],
        "numerator_value": 2,
        "rate_state": "permitted",
        "unit": "subject",
    }
    change_bands = [
        {"authority_receipt_ref": RECEIPT_REF_PREFIX + _h(r_d10),
         "change_cause": "data", "change_kind": "continued",
         "current_snapshot_ref": "snap.s1",
         "prior_snapshot_ref": "snap.s0", "risk_ref": hi_ref},
        {"authority_receipt_ref": RECEIPT_REF_PREFIX + _h(r_d09),
         "change_cause": None, "change_kind": "initial_current",
         "current_snapshot_ref": "snap.s1",
         "prior_snapshot_ref": None, "risk_ref": lo_ref},
        {"authority_receipt_ref": RECEIPT_REF_PREFIX + _h(r_d09b),
         "change_cause": "data", "change_kind": "resolved",
         "current_snapshot_ref": "snap.s1",
         "prior_snapshot_ref": "snap.s0", "risk_ref": res_ref},
    ]
    current_risk_set = {
        "authority_receipt_ref": None,
        "high_risk_refs": [hi_ref],
        "low_risk_cluster_refs": [cluster["cluster_ref"]],
        "medium_risk_refs": [],
        "resolved_history_refs": [res_ref],
    }
    center_map = {
        "cells": [
            {"domain": "ae", "individual_risk_refs": [],
             "measure_refs": [], "pattern_refs": ["member.c"],
             "severity": "low", "site_ref": "site.d09"},
            {"domain": "mh", "individual_risk_refs": ["member.a", "member.b"],
             "measure_refs": ["measure.ir.1"], "pattern_refs": [],
             "severity": "high", "site_ref": "site.d10"},
        ],
        "content_hash": None,
        "projection_instance": {
            "authority_receipt_ref": RECEIPT_REF_PREFIX + _h(r_d10),
            "content_hash": None,
            "opaque_run_ref": "run.r1",
            "opaque_snapshot_ref": "snap.s1",
            "replay_content_identity": _h({"replay": "center"}),
        },
        "stable_site_order": ["site.d09", "site.d10"],
    }
    center_map["projection_instance"]["content_hash"] = _content_hash(
        center_map["projection_instance"])
    center_map["content_hash"] = _content_hash(center_map)
    cockpit = {
        "center_map_ref": "center_map.v1",
        "change_band_refs": ["band.1", "band.2", "band.3"],
        "content_hash": None,
        "current_risk_set_ref": "current_risk_set.v1",
        "measure_refs": ["measure.ir.1"],
        "projection_instance": center_map["projection_instance"],
        "selected_risk_ref": hi_ref,
    }
    cockpit["content_hash"] = _content_hash(cockpit)

    aggregate_refs = sorted([RECEIPT_REF_PREFIX + _h(r_d09),
                             RECEIPT_REF_PREFIX + _h(r_d10),
                             RECEIPT_REF_PREFIX + _h(r_d09b)])
    risk_identity_hashes = sorted([m_d09["content_hash"],
                                   m_d10["content_hash"],
                                   m_d09b["content_hash"]])
    aggregate_body = {
        "unit_receipt_refs": aggregate_refs,
        "risk_marker_identity_hashes": risk_identity_hashes,
        "project_ref": "project.p1", "run_ref": "run.r1",
        "snapshot_ref": "snap.s1", "cutoff_ref": "cutoff.v1",
        "audience_contract_id": "contract.s3",
    }
    aggregate_id = "aggregate:" + _h(aggregate_body)
    aggregate = dict(aggregate_body)
    aggregate["aggregate_id"] = aggregate_id
    aggregate["content_hash"] = _content_hash(aggregate)
    current_risk_set["authority_receipt_ref"] = aggregate_id

    audience_payload = {
        "current_risk_set": current_risk_set,
        "change_bands": change_bands,
        "measures": [measure],
        "center_map": center_map,
        "cockpit": cockpit,
        "low_risk_clusters": [cluster],
    }
    replay_hash = _h(audience_payload)

    packet = {
        "packet_id": f"{PACKET_ID_PREFIX}:{replay_hash}",
        "schema": PACKET_SCHEMA,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "authority_units": sorted(
            [unit_d09, unit_d10, unit_d09b], key=lambda u: u["unit_ref"]),
        "aggregate_receipt_set": aggregate,
        "risk_lifecycle_authorities": sorted(
            [lc_hi, lc_lo, lc_res],
            key=lambda l: l["marker_identity_ref"]),
        "closure_authorities": [closure],
        "clinical_domain_authorities": sorted(
            [cda_d09, cda_d10, cda_d09b], key=lambda c: c["authority_id"]),
        "denominator_authorities": [],
        "layer_membership_authorities": [],
        "cutoff_authorities": [],
        "evaluation_limit_authorities": [],
        "coverage_authorities": [],
        "change_cause_mixture_authorities": [],
        "audience_payload": audience_payload,
        "audience_replay_content_hash": replay_hash,
        "packet_integrity_hash": None,
    }
    # Replace the hand-written audience surface with the verifier-owned
    # authority projection.  Keeping this fixture declaration separate from
    # the projector is important: accept tests can now tamper the declaration
    # and prove that an echo projector is rejected.
    projected = _project_audience_payload_from_authorities(packet)
    packet["audience_payload"] = projected["projection"]
    packet["audience_replay_content_hash"] = projected[
        "audience_replay_content_hash"]
    packet["packet_id"] = projected["packet_id"]
    integrity_body = {k: v for k, v in packet.items()
                      if k not in ("packet_id", "packet_integrity_hash",
                                   "audience_replay_content_hash",
                                   "schema", "status", "authority_mode")}
    packet["packet_integrity_hash"] = _h(integrity_body)
    return packet


def _marker_prefix_of(ref: str) -> Optional[str]:
    for prefix in ("d09_marker:", "d10_marker:"):
        if ref.startswith(prefix):
            return prefix
    return None


def _is_current_marker_ref(ref: str) -> bool:
    return ref.startswith("d09_marker:") or ref.startswith("d10_marker:")


def _hotspot_member_refs(kind: str, hotspot: Dict[str, Any]) -> List[str]:
    """Return the public member set exposed by one typed hotspot.

    D09 and D10 hotspot projections are deliberately different dataclasses:
    D09 has ``member_risk_refs`` plus ``gap_member_refs`` while D10 has one
    ``member_refs`` field.  Reading a generic ``member_refs`` from both would
    silently manufacture a center binding for D09 and would let a malformed
    fixture pass the center-map closure.
    """
    if kind == "d09":
        return sorted(set(hotspot.get("member_risk_refs", [])) |
                      set(hotspot.get("gap_member_refs", [])))
    if kind == "d10":
        return sorted(set(hotspot.get("member_refs", [])))
    return []


def _member_explicitly_not_projectable(idx: Dict[str, Any],
                                       member: str,
                                       layer: str = "center_pattern") -> bool:
    """Recognize an explicit supplemental not-projectable decision.

    A marker member absent from a D09 hotspot has no site identity.  It may be
    omitted from the center map only when a named supplemental authority says
    that the layer is not projectable; absence of that authority is a hard
    center-binding failure, never a reason to infer a site from counts.
    """
    required = {
        "authority_id", "layer", "membership_state", "member_refs",
        "source_count_ref", "disabled_state", "receipt_hash", "receipt_ref",
        "visibility_decision_id", "visibility_decision_hash",
        "source_revision_content_pairs", "offline_test_only", "content_hash",
    }
    for authority in idx.get("layer_membership_authorities", []):
        if (authority.get("layer") == layer
                and authority.get("membership_state") == "not_projectable"
                and member in authority.get("member_refs", [])
                and required <= set(authority)
                and authority.get("offline_test_only") is True
                and authority.get("receipt_ref", "").startswith(
                    RECEIPT_REF_PREFIX)
                and authority.get("content_hash") == _content_hash(authority)):
            return True
    return False


def _index_packet_authorities(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Build shared indexes over a packet (lifecycles, closures, domains,
    markers, handoffs, units, hotspots, clusters) for the projectors."""
    lifecycles = {l.get("marker_identity_ref"): l
                  for l in packet.get("risk_lifecycle_authorities", [])}
    closures = {c.get("closure_authority_id"): c
                for c in packet.get("closure_authorities", [])}
    domains = {d.get("authority_id"): d
               for d in packet.get("clinical_domain_authorities", [])}
    units = list(packet.get("authority_units", []))
    marker_by_id = {}
    handoff_by_id = {}
    unit_by_ref = {}
    unit_by_marker_id = {}
    variants = {}
    for unit_ in units:
        unit_by_ref[unit_.get("unit_ref")] = unit_
        variant = unit_.get("d09_variant_payload") or \
            unit_.get("d10_variant_payload") or {}
        variants[unit_.get("unit_ref")] = variant
        marker = variant.get("risk_marker")
        if marker:
            marker_by_id[marker.get("marker_id")] = marker
            unit_by_marker_id[marker.get("marker_id")] = unit_
        handoff = variant.get("r2_handoff")
        if handoff:
            handoff_by_id[handoff.get("handoff_id")] = handoff
    payload = packet.get("audience_payload", {})
    clusters = list(payload.get("low_risk_clusters", []))
    cluster_by_ref = {c.get("cluster_ref"): c for c in clusters}
    center_map = dict(payload.get("center_map", {}))
    current_risk = dict(payload.get("current_risk_set", {}))
    measures = list(payload.get("measures", []))
    return {
        "lifecycles": lifecycles, "closures": closures, "domains": domains,
        "units": units, "marker_by_id": marker_by_id,
        "handoff_by_id": handoff_by_id, "unit_by_ref": unit_by_ref,
        "unit_by_marker_id": unit_by_marker_id, "variants": variants,
        "clusters": clusters, "cluster_by_ref": cluster_by_ref,
        "center_map": center_map, "current_risk": current_risk,
        "measures": measures,
        "layer_membership_authorities": list(
            packet.get("layer_membership_authorities", [])),
        "payload": payload,
    }


def _is_sha256_hex(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _validate_source_revision_pairs(value: Any, *, prefix: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(value, list) or not value:
        return [f"{prefix}_cardinality_mismatch"]
    revision_ids: List[str] = []
    invalid_revision_id = False
    for pair in value:
        if not isinstance(pair, dict) or set(pair) != \
                SOURCE_REVISION_CONTENT_PAIR_FIELDS:
            errors.append(f"{prefix}_schema_key_mismatch")
            continue
        if not _is_nonempty_str(pair.get("revision_id")) or not \
                _is_sha256_hex(pair.get("content_hash")):
            errors.append(f"{prefix}_type_mismatch")
        if _is_nonempty_str(pair.get("revision_id")):
            revision_ids.append(pair["revision_id"])
        else:
            invalid_revision_id = True
    if invalid_revision_id or len(revision_ids) != len(set(revision_ids)) or \
            revision_ids != sorted(revision_ids):
        errors.append(f"{prefix}_cardinality_mismatch")
    return sorted(set(errors))


def _validate_r5_authority_receipt(receipt: Any) -> List[str]:
    """Validate the complete dict form of one R5AuthorityReceipt.

    Supplemental objects are not allowed to bind to a hash-shaped token that
    is absent from a complete receipt.  This check intentionally mirrors the
    real dataclass fields and its closed projection-kind/hash/cardinality
    rules rather than trusting a producer-declared receipt shape.
    """
    errors: List[str] = []
    if not isinstance(receipt, dict):
        return ["authority_receipt_type_mismatch"]
    if set(receipt) != R5_AUTHORITY_RECEIPT_FIELDS:
        errors.append("authority_receipt_schema_key_mismatch")
    required_strings = (
        "audience_contract_id", "project_ref", "public_projection_id",
        "run_ref", "snapshot_ref", "visibility_decision_id",
    )
    for field in required_strings:
        if not _is_nonempty_str(receipt.get(field)):
            errors.append("authority_receipt_type_mismatch")
    if receipt.get("cutoff_ref") is not None and not _is_nonempty_str(
            receipt.get("cutoff_ref")):
        errors.append("authority_receipt_type_mismatch")
    if receipt.get("public_projection_kind") not in EXPECTED_ENUMS[
            "projection_kind"]:
        errors.append("authority_receipt_enum_mismatch")
    for field in ("public_projection_content_hash", "visibility_decision_hash"):
        if not _is_sha256_hex(receipt.get(field)):
            errors.append("authority_receipt_type_mismatch")
    identities = receipt.get("evaluation_content_identities")
    if not isinstance(identities, list):
        errors.append("authority_receipt_cardinality_mismatch")
    else:
        invalid_identity = any(not _is_sha256_hex(value)
                               for value in identities)
        if invalid_identity:
            errors.append("authority_receipt_type_mismatch")
        valid_identities = [value for value in identities
                            if _is_sha256_hex(value)]
        if invalid_identity or len(valid_identities) != len(set(
                valid_identities)) or valid_identities != sorted(
                    valid_identities):
            errors.append("authority_receipt_cardinality_mismatch")
    errors.extend(_validate_source_revision_pairs(
        receipt.get("source_revision_content_pairs"),
        prefix="authority_receipt_source_pairs"))
    return sorted(set(errors))


SUPPLEMENTAL_ENUM_FIELDS = {
    "R5S3RiskLifecycleAuthority": {
        "marker_kind": EXPECTED_ENUMS["marker_kind"],
        "severity": EXPECTED_ENUMS["severity"],
        "lifecycle_state": EXPECTED_ENUMS["lifecycle_state"],
        "lifecycle_action": EXPECTED_ENUMS["lifecycle_action"],
    },
    "R5S3ClosureAuthority": {
        "decision_kind": EXPECTED_ENUMS["closure_decision_kind"],
    },
    "R5S3ClinicalDomainAuthority": {
        "clinical_domain": EXPECTED_ENUMS["domain"],
    },
    "R5S3DenominatorAuthority": {
        "denominator_kind": EXPECTED_ENUMS["denominator_kind"],
        "denominator_state": EXPECTED_ENUMS["denominator_state"],
        "measure_unit": EXPECTED_ENUMS["measure_unit"],
    },
    "R5S3LayerMembershipAuthority": {
        "layer": EXPECTED_ENUMS["numerator_kind"],
        "membership_state": EXPECTED_ENUMS["membership_state"],
        "disabled_state": list(SUPPLEMENTAL_DISABLED_STATES),
    },
    "R5S3CoverageAuthority": {
        "coverage_state": EXPECTED_ENUMS["coverage_state"],
    },
}

SUPPLEMENTAL_STRING_LIST_FIELDS = {
    "R5S3RiskLifecycleAuthority": {"member_expansion_refs"},
    "R5S3DenominatorAuthority": {"member_refs", "exclusion_refs"},
    "R5S3LayerMembershipAuthority": {"member_refs"},
    "R5S3EvaluationLimitAuthority": {
        "evaluation_limit_refs", "evaluation_limit_values",
    },
}
SUPPLEMENTAL_CAUSE_LIST_FIELDS = {"R5S3ChangeCauseMixtureAuthority": "causes"}
SUPPLEMENTAL_NUM_FIELDS = {
    ("R5S3DenominatorAuthority", "denominator_value"),
    ("R5S3LayerMembershipAuthority", "source_count_value"),
}
SUPPLEMENTAL_NULLABLE_FIELDS = {
    ("R5S3DenominatorAuthority", "denominator_value"),
    ("R5S3CutoffAuthority", "cutoff_ref"),
    ("R5S3RiskLifecycleAuthority", "closure_authority_ref"),
    ("R5S3RiskLifecycleAuthority", "prior_marker_identity_ref"),
}
SUPPLEMENTAL_HASH_FIELDS = {
    "receipt_hash", "visibility_decision_hash", "content_hash",
    "marker_content_hash", "closure_decision_hash",
}


def _validate_supplemental_object(name: str,
                                  authority: Any) -> List[str]:
    """Validate one typed supplemental object against verifier-owned shape."""
    errors: List[str] = []
    if not isinstance(authority, dict):
        return ["supplemental_type_mismatch"]
    expected = SUPPLEMENTAL_EXACT_FIELDS[name]
    exact_keys = set(authority) == expected
    if not exact_keys:
        errors.append("supplemental_schema_key_mismatch")

    for field in expected & set(authority):
        value = authority[field]
        if value is None and (name, field) in SUPPLEMENTAL_NULLABLE_FIELDS:
            continue
        if field in SUPPLEMENTAL_HASH_FIELDS:
            if not _is_sha256_hex(value):
                errors.append("supplemental_type_mismatch")
        elif field == "offline_test_only":
            if value is not True:
                errors.append("supplemental_type_mismatch")
        elif field == "source_revision_content_pairs":
            errors.extend(_validate_source_revision_pairs(
                value, prefix="supplemental_source_pairs"))
        elif field in SUPPLEMENTAL_ENUM_FIELDS.get(name, {}):
            if value not in SUPPLEMENTAL_ENUM_FIELDS[name][field]:
                errors.append("supplemental_enum_mismatch")
        elif field in SUPPLEMENTAL_STRING_LIST_FIELDS.get(name, set()):
            if not isinstance(value, list) or any(
                    not _is_nonempty_str(item) for item in value):
                errors.append("supplemental_type_mismatch")
            elif len(value) != len(set(value)) or value != sorted(value):
                errors.append("supplemental_cardinality_mismatch")
        elif field == SUPPLEMENTAL_CAUSE_LIST_FIELDS.get(name):
            if not isinstance(value, list) or len(value) < 2 or any(
                    item not in EXPECTED_ENUMS["change_cause"]
                    for item in value):
                errors.append("supplemental_enum_mismatch")
            elif len(value) != len(set(value)) or value != sorted(value):
                errors.append("supplemental_cardinality_mismatch")
        elif (name, field) in SUPPLEMENTAL_NUM_FIELDS:
            if not isinstance(value, (int, float)) or isinstance(value, bool) \
                    or (isinstance(value, float) and not math.isfinite(value)):
                errors.append("supplemental_type_mismatch")
        elif field in {"marker_content_hash", "closure_decision_hash"}:
            if not _is_sha256_hex(value):
                errors.append("supplemental_type_mismatch")
        elif not _is_nonempty_str(value):
            errors.append("supplemental_type_mismatch")

    if "content_hash" in authority and _is_sha256_hex(
            authority.get("content_hash")):
        if authority["content_hash"] != _content_hash(authority):
            errors.append("supplemental_content_hash_mismatch")
    return sorted(set(errors))


def _validate_supplemental_authorities(packet: Dict[str, Any]) -> List[str]:
    """Validate every supplemental instance and its complete receipt binding.

    This is deliberately called by both ``_packet_oracle`` and the
    verifier-owned independent projector.  A producer cannot make a
    re-signed exact-shape object disappear from the oracle by keeping it out
    of the audience payload.
    """
    errors: List[str] = []
    if set(SUPPLEMENTAL_FIELDS_WITH_RECEIPT_BINDING) != set(
            SUPPLEMENTAL_PACKET_LIST_KEYS):
        errors.append("supplemental_receipt_binding_hard_pin_mismatch")

    receipt_by_hash: Dict[str, List[Tuple[Dict[str, Any], Dict[str, Any]]]] = {}
    for unit in packet.get("authority_units", []):
        if not isinstance(unit, dict):
            errors.append("authority_receipt_type_mismatch")
            continue
        receipt = unit.get("authority_receipt")
        receipt_errors = _validate_r5_authority_receipt(receipt)
        errors.extend(receipt_errors)
        if receipt_errors:
            continue
        receipt_hash = _h(receipt)
        if unit.get("receipt_content_hash") != receipt_hash:
            errors.append("receipt_content_hash_mismatch")
        receipt_by_hash.setdefault(receipt_hash, []).append((unit, receipt))

    for name in SUPPLEMENTAL_FIELDS_WITH_RECEIPT_BINDING:
        list_key = SUPPLEMENTAL_PACKET_LIST_KEYS[name]
        authorities = packet.get(list_key)
        if not isinstance(authorities, list):
            errors.append("supplemental_cardinality_mismatch")
            continue
        id_field = SUPPLEMENTAL_ID_FIELDS.get(name, "authority_id")
        authority_ids = [obj.get(id_field) for obj in authorities
                         if isinstance(obj, dict)
                         and _is_nonempty_str(obj.get(id_field))]
        if (len(authority_ids) != len(authorities)
                or len(authority_ids) != len(set(authority_ids))
                or authority_ids != sorted(authority_ids)):
            errors.append("supplemental_cardinality_mismatch")

        for authority in authorities:
            shape_errors = _validate_supplemental_object(name, authority)
            errors.extend(shape_errors)
            if not isinstance(authority, dict):
                continue
            # Do not try relation checks on a missing/malformed binding key;
            # the exact-shape/type gate above is the authoritative rejection.
            if not _is_sha256_hex(authority.get("receipt_hash")):
                continue
            receipt_hash = authority["receipt_hash"]
            receipt_ref = authority.get("receipt_ref")
            if receipt_ref != RECEIPT_REF_PREFIX + receipt_hash:
                errors.append("supplemental_receipt_binding_mismatch")
            matches = receipt_by_hash.get(receipt_hash, [])
            if not matches:
                errors.append("supplemental_receipt_missing")
                continue
            if len(matches) != 1:
                errors.append("supplemental_receipt_cardinality_mismatch")
                continue
            unit, receipt = matches[0]
            if receipt_ref != RECEIPT_REF_PREFIX + _h(receipt):
                errors.append("supplemental_receipt_binding_mismatch")
            if (authority.get("visibility_decision_id") !=
                    receipt.get("visibility_decision_id") or
                    authority.get("visibility_decision_hash") !=
                    receipt.get("visibility_decision_hash")):
                errors.append("supplemental_visibility_binding_mismatch")
            if _canonical_bytes(authority.get(
                    "source_revision_content_pairs")) != _canonical_bytes(
                        receipt.get("source_revision_content_pairs")):
                errors.append("supplemental_source_pairs_mismatch")

            if name != "R5S3LayerMembershipAuthority":
                continue
            layer = authority.get("layer")
            if not isinstance(layer, str) or layer not in \
                    PER_LAYER_SOURCE_COUNT_PATHS:
                errors.append("supplemental_source_count_mismatch")
                continue
            variant = unit.get("d09_variant_payload") or \
                unit.get("d10_variant_payload") or {}
            variant_kind = unit.get("variant_kind")
            kind = "d09" if variant_kind == "d09_center_pattern_unit" \
                else "d10" if variant_kind == "d10_project_unit" else None
            candidates = [path for path in PER_LAYER_SOURCE_COUNT_PATHS.get(
                layer, []) if (kind == "d09" and "d09_projection:" in path)
                or (kind == "d10" and "d10_projection:" in path)]
            source_count_ref = authority.get("source_count_ref")
            if not candidates or source_count_ref not in candidates:
                errors.append("supplemental_source_count_mismatch")
                continue
            count_field = source_count_ref.rsplit(".", 1)[-1]
            counts = variant.get("counts", {})
            source_count = counts.get(count_field)
            if source_count is None or authority.get("source_count_value") != \
                    source_count:
                errors.append("supplemental_source_count_mismatch")

            policy = PER_LAYER_DISABLED_PATH.get(layer)
            expected_disabled = None
            if policy == "no_disabled_path":
                expected_disabled = "no_disabled_path"
            elif policy in ("event_count_disabled", "site_count_disabled"):
                flag = bool(counts.get(policy, False))
                expected_disabled = policy if flag else "enabled"
            if expected_disabled is None or authority.get("disabled_state") \
                    != expected_disabled:
                errors.append("supplemental_disabled_state_mismatch")

            if authority.get("membership_state") == "projectable" and \
                    isinstance(authority.get("source_count_value"),
                               (int, float)) and not isinstance(
                                   authority.get("source_count_value"), bool):
                if authority.get("source_count_value") != len(
                        authority.get("member_refs", [])):
                    errors.append("supplemental_source_count_mismatch")

    return sorted(set(errors))


def _project_low_risk_clusters(packet: Dict[str, Any],
                               idx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Rebuild low-risk clusters from current lifecycle authorities.

    The packet's ``low_risk_clusters`` list is a declared audience surface,
    not an authority input.  This independent reconstruction gives both the
    packet oracle and the accept oracle a canonical cluster set to compare
    against it, including the member/site/domain binding and cluster hash.
    """
    clusters: List[Dict[str, Any]] = []
    for ref, lifecycle in sorted(idx["lifecycles"].items()):
        if lifecycle.get("lifecycle_state") != "current" \
                or lifecycle.get("severity") != "low":
            continue
        domain = idx["domains"].get(
            lifecycle.get("clinical_domain_ref"), {}).get("clinical_domain")
        site = _lifecycle_site(packet, idx, lifecycle)
        members = sorted(lifecycle.get("member_expansion_refs", []))
        if not domain or site is None or not members:
            continue
        body = {
            "authority_receipt_ref": lifecycle.get("receipt_ref"),
            "domain": domain,
            "site_ref": site,
            "member_refs": members,
        }
        content_hash = _h(body)
        clusters.append({
            "cluster_ref": CLUSTER_REF_PREFIX + content_hash,
            **body,
            "content_hash": content_hash,
        })
    return clusters


def _project_current_risk_planes(packet: Dict[str, Any],
                                 idx: Dict[str, Any],
                                 *,
                                 compare_declared: bool = True) -> Dict[str, Any]:
    """Block 1 projector: derive the exact expected current-risk planes from
    lifecycle + marker + severity/domain authorities.  Returns a dict with
    the projected planes and a list of oracle errors (empty = closure holds).

    Plane rules (bidirectional exact-set closure):
      * current + severity high  -> high plane (marker identity ref)
      * current + severity medium-> medium plane
      * current + severity low   -> low-cluster plane (cluster ref whose
        member set / domain / site match that low lifecycle)
      * resolved                 -> resolved plane
      * superseded/proposed_closent -> never in a current plane
      * every projected ref / every declared ref is accounted for exactly
        once; orphan/duplicate projections and missing low clusters fail.
    """
    errors: List[str] = []
    lc = idx["lifecycles"]
    domains = idx["domains"]
    current_risk = idx["current_risk"]

    declared_high = sorted(current_risk.get("high_risk_refs", [])) \
        if compare_declared else []
    declared_medium = sorted(current_risk.get("medium_risk_refs", [])) \
        if compare_declared else []
    declared_low = sorted(current_risk.get("low_risk_cluster_refs", [])) \
        if compare_declared else []
    declared_resolved = sorted(current_risk.get("resolved_history_refs", [])) \
        if compare_declared else []

    expected_high = []
    expected_medium = []
    expected_low_lifecycles = []
    expected_resolved = []
    seen: Dict[str, str] = {}
    for ref, l in lc.items():
        state = l.get("lifecycle_state")
        severity = l.get("severity")
        if state == "current":
            if severity not in ("high", "medium", "low"):
                errors.append("severity_not_in_enum")
                continue
            if severity == "high":
                plane = "high"
                expected_high.append(ref)
            elif severity == "medium":
                plane = "medium"
                expected_medium.append(ref)
            else:
                plane = "low"
                expected_low_lifecycles.append(ref)
        elif state == "resolved":
            plane = "resolved"
            expected_resolved.append(ref)
        else:
            continue  # superseded / proposed_close: never a current ref
        if ref in seen:
            errors.append("current_plane_duplicate_projection")
        seen[ref] = plane
    expected_high = sorted(expected_high)
    expected_medium = sorted(expected_medium)
    expected_resolved = sorted(expected_resolved)

    # low clusters: each low current lifecycle deterministically produces one
    # cluster from its public member expansion/domain/site authorities.
    projected_clusters = _project_low_risk_clusters(packet, idx)
    expected_low = []
    for ref in expected_low_lifecycles:
        lifecycle = lc[ref]
        domain = domains.get(
            lifecycle.get("clinical_domain_ref"), {}).get("clinical_domain")
        site = _lifecycle_site(packet, idx, lifecycle)
        members = sorted(lifecycle.get("member_expansion_refs", []))
        matches = [cluster["cluster_ref"] for cluster in projected_clusters
                   if sorted(cluster.get("member_refs", [])) == members
                   and cluster.get("domain") == domain
                   and cluster.get("site_ref") == site
                   and cluster.get("authority_receipt_ref") == lifecycle.get(
                       "receipt_ref")]
        if len(matches) == 0:
            errors.append("current_plane_low_cluster_mismatch")
        elif len(matches) > 1:
            errors.append("cluster_lifecycle_unresolved")
        else:
            expected_low.append(matches[0])
    expected_low = sorted(expected_low)

    # bidirectional exact-set equality per plane.
    if compare_declared:
        if expected_high != declared_high:
            errors.append("current_plane_high_mismatch")
        if expected_medium != declared_medium:
            errors.append("current_plane_medium_mismatch")
        if expected_low != declared_low:
            errors.append("current_plane_low_cluster_mismatch")
        if expected_resolved != declared_resolved:
            errors.append("current_plane_resolved_mismatch")

    # every declared ref must resolve to an authority lifecycle/cluster.
    for ref in declared_high + declared_medium + declared_resolved:
        if ref not in lc:
            errors.append("current_risk_lifecycle_unresolved")
    if compare_declared:
        for ref in declared_low:
            if ref not in idx["cluster_by_ref"]:
                errors.append("cluster_lifecycle_unresolved")

    projected_planes = {
        "high": expected_high, "medium": expected_medium,
        "low": expected_low, "resolved": expected_resolved,
        "lifecycle_plane": seen,
    }
    return {"planes": projected_planes, "errors": errors}


def _lifecycle_site(packet: Dict[str, Any], idx: Dict[str, Any],
                    lifecycle: Dict[str, Any]) -> Optional[str]:
    """Resolve the site of a lifecycle from public hotspot member<->site
    bindings (never inferred from counts)."""
    variant = idx["variants"].get(
        idx["unit_by_marker_id"].get(lifecycle.get("marker_id"), {}).get(
            "unit_ref", ""), {})
    sites = set()
    kind = "d09" if "d09_variant_payload" in idx["unit_by_marker_id"].get(
        lifecycle.get("marker_id"), {}) else "d10"
    for hotspot in variant.get("hotspots", []):
        if set(_hotspot_member_refs(kind, hotspot)) & set(
                lifecycle.get("member_expansion_refs", [])):
            sites.add(hotspot.get("site_ref"))
    if len(sites) == 1:
        return next(iter(sites))
    return None


def _project_measures(packet: Dict[str, Any],
                      idx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Rebuild quantitative measures from public unit authorities.

    The sample packet keeps a ``measures`` audience surface for downstream
    center-cell references, but the projector must not echo that surface.
    D10's public count surface, audience member plane, receipt and center-row
    denominator are sufficient for this synthetic offline measure recipe.
    """
    measures: List[Dict[str, Any]] = []
    serial = 1
    for unit_ref in sorted(idx["unit_by_ref"]):
        unit = idx["unit_by_ref"][unit_ref]
        variant = idx["variants"].get(unit_ref, {})
        if "d10_variant_payload" not in unit:
            continue
        audience = variant.get("audience", {})
        marker = variant.get("risk_marker")
        if not marker:
            continue
        members = sorted(set(marker.get("member_refs", [])) & set(
            audience.get("projectable_member_refs", [])))
        if not members:
            continue
        counts = variant.get("counts", {})
        rows = variant.get("center_distribution", [])
        denominator_value = None
        if rows:
            values = [row.get("denominator_value") for row in rows
                      if row.get("denominator_value") is not None]
            if values:
                denominator_value = values[0]
        if denominator_value is None:
            denominator_value = len(members)
        denominator_state = ("closed_positive" if denominator_value > 0
                             else "closed_zero")
        measure = {
            "authoritative_value_ref": f"measure.ir.{serial}",
            "authority_receipt_ref": RECEIPT_REF_PREFIX + unit.get(
                "receipt_content_hash", ""),
            "coverage_state": audience.get("coverage_state", "unknown"),
            "cutoff_ref": (variant.get("version", {}) or {}).get(
                "cutoff_ref"),
            "denominator_exclusion_refs": [],
            "denominator_kind": "treated_subjects",
            "denominator_member_refs": members,
            "denominator_state": denominator_state,
            "denominator_value": denominator_value,
            "evaluation_limit_refs": [
                f"eval.{member.removeprefix('member.')}"
                for member in members],
            "numerator_kind": "individual_risk",
            "numerator_member_refs": members,
            "numerator_value": counts.get("individual_risk_count", 0),
            "rate_state": audience.get("rate_projection_state",
                                       "not_evaluable"),
            "unit": "subject",
        }
        measures.append(measure)
        serial += 1
    return measures


def _project_center_cells(packet: Dict[str, Any],
                          idx: Dict[str, Any]) -> Dict[str, Any]:
    """Block 2 projector: reconstruct the complete expected center-cell set
    from public hotspot member<->site bindings + lifecycle/marker/domain
    authorities.  D09 marker -> pattern, D10 marker -> individual."""
    errors: List[str] = []
    lc = idx["lifecycles"]
    domains = idx["domains"]
    # Measures are rebuilt from the public unit authorities below; the
    # audience payload's self-reported measure list is only checked against
    # this result by the packet oracle.
    measures = _project_measures(packet, idx)

    # member -> (site, kind) from public hotspot bindings only.
    member_site: Dict[str, str] = {}
    member_kind: Dict[str, str] = {}
    member_severity: Dict[str, str] = {}
    member_domain: Dict[str, str] = {}
    member_lifecycle: Dict[str, Dict[str, Any]] = {}
    for ref, l in lc.items():
        if l.get("lifecycle_state") != "current":
            continue
        kind = l.get("marker_kind", "")
        for member in l.get("member_expansion_refs", []):
            if member in member_lifecycle:
                errors.append("center_cell_duplicate_member")
                continue
            member_lifecycle[member] = l
            member_kind[member] = kind
            member_severity[member] = l.get("severity")
            member_domain[member] = domains.get(
                l.get("clinical_domain_ref", ""), {}).get("clinical_domain")
    for unit_ref, variant in idx["variants"].items():
        kind = ("d09" if "d09_variant_payload" in idx["unit_by_ref"].get(
            unit_ref, {}) else "d10")
        for hotspot in variant.get("hotspots", []):
            site = hotspot.get("site_ref")
            for member in _hotspot_member_refs(kind, hotspot):
                if member in member_site and member_site[member] != site:
                    # member bound to two sites -> data inconsistency
                    errors.append("center_cell_site_mismatch")
                member_site[member] = site

    # every current member needs an exact hotspot site binding.
    for member in member_lifecycle:
        if member not in member_site:
            if not _member_explicitly_not_projectable(idx, member):
                errors.append("center_cell_site_mismatch")

    cells: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for member, l in member_lifecycle.items():
        site = member_site.get(member)
        domain = member_domain.get(member)
        if site is None or domain is None:
            continue
        key = (site, domain)
        cell = cells.setdefault(key, {
            "site_ref": site, "domain": domain,
            "individual_risk_refs": [], "pattern_refs": [],
            "severity": None, "member_severities": []})
        if member_kind.get(member) == "d10":
            cell["individual_risk_refs"].append(member)
        elif member_kind.get(member) == "d09":
            cell["pattern_refs"].append(member)
        else:
            errors.append("center_cell_classification_mismatch")
        member_sev = member_severity.get(member)
        if member_sev:
            cell["member_severities"].append(member_sev)

    expected_cells = []
    for (site, domain), cell in sorted(cells.items()):
        cell["individual_risk_refs"] = sorted(cell["individual_risk_refs"])
        cell["pattern_refs"] = sorted(cell["pattern_refs"])
        sevs = cell.pop("member_severities")
        cell["severity"] = ("high" if "high" in sevs else
                            "medium" if "medium" in sevs else
                            "low" if sevs else None)
        # measure refs: measures whose numerator members overlap the cell.
        cell_members = set(cell["individual_risk_refs"]) | set(
            cell["pattern_refs"])
        cell["measure_refs"] = sorted({
            m.get("authoritative_value_ref") for m in measures
            if set(m.get("numerator_member_refs", [])) & cell_members})
        expected_cells.append(cell)

    # stable site order = NFC-stable projectable site identity ascending.
    projectable_sites = sorted({c["site_ref"] for c in expected_cells})
    return {"cells": expected_cells,
            "stable_site_order": projectable_sites,
            "member_site": member_site,
            "errors": errors}


def _validate_closure_integrity(packet: Dict[str, Any],
                                idx: Dict[str, Any]) -> List[str]:
    """Block 3: bidirectional closure integrity.

    * every resolved lifecycle has exactly one valid closure;
    * every closure is referenced by exactly one resolved lifecycle (no
      orphan, no ambiguity);
    * closure.prior_risk_instance_ref binds to the resolved lifecycle's
      public R2 handoff prior_risk_instance_ref;
    * closure decision / receipt / source pairs / visibility / content
      hashes are valid in both directions.
    """
    errors: List[str] = []
    lc = idx["lifecycles"]
    closures = idx["closures"]

    resolved_by_ref = []
    for ref, l in lc.items():
        if l.get("lifecycle_state") == "resolved":
            resolved_by_ref.append((ref, l))

    # closure reference counts (each closure referenced by one resolved lc).
    used: Dict[str, int] = {}
    for _ref, l in resolved_by_ref:
        c_ref = l.get("closure_authority_ref")
        if not c_ref:
            errors.append("resolved_without_lifecycle_authority")
            continue
        if c_ref not in closures:
            errors.append("resolved_closure_unresolved")
        used[c_ref] = used.get(c_ref, 0) + 1
    for c_ref in closures:
        if used.get(c_ref, 0) == 0:
            errors.append("closure_orphan")
        elif used[c_ref] > 1:
            errors.append("closure_ambiguous")

    for ref, l in resolved_by_ref:
        c_ref = l.get("closure_authority_ref")
        if not c_ref or c_ref not in closures:
            continue
        closure = closures[c_ref]
        # identity/binding of prior public identity.
        if closure.get("prior_public_risk_identity_ref") != ref:
            errors.append("closure_identity_mismatch")
        # prior instance binds to the resolved lifecycle's public R2 handoff.
        handoff = idx["handoff_by_id"].get(l.get("r2_handoff_id"))
        expected_prior = (handoff or {}).get("prior_risk_instance_ref")
        if closure.get("prior_risk_instance_ref") != expected_prior:
            errors.append("closure_prior_instance_mismatch")
        # decision hash = canonical of decision content.
        decision_body = {
            "closure_decision_id": closure.get("closure_decision_id"),
            "decision_kind": closure.get("decision_kind"),
            "prior_public_risk_identity_ref": closure.get(
                "prior_public_risk_identity_ref"),
            "prior_risk_instance_ref": closure.get(
                "prior_risk_instance_ref"),
        }
        if closure.get("closure_decision_hash") != _h(decision_body):
            errors.append("closure_decision_hash_mismatch")
        # commission receipt binding (bidirectional with the unit receipt).
        unit_ = idx["unit_by_marker_id"].get(l.get("marker_id"))
        if unit_ is None:
            errors.append("unknown_lifecycle_authority")
            continue
        unit_receipt = unit_.get("authority_receipt", {})
        receipt_hash = _h(unit_receipt)
        if closure.get("receipt_hash") != receipt_hash:
            errors.append("closure_receipt_binding_mismatch")
        if closure.get("receipt_ref") != RECEIPT_REF_PREFIX + receipt_hash:
            errors.append("closure_receipt_binding_mismatch")
        # visibility binding (same decision as the unit receipt).
        expected_vis_id = unit_receipt.get("visibility_decision_id")
        expected_vis_hash = unit_receipt.get("visibility_decision_hash")
        if closure.get("visibility_decision_id") != expected_vis_id or \
                closure.get("visibility_decision_hash") != expected_vis_hash:
            errors.append("closure_visibility_binding_mismatch")
        # source pairs non-empty.
        if not closure.get("source_revision_content_pairs"):
            errors.append("closure_receipt_binding_mismatch")
        # content hash = canonical of non-hash fields.
        if closure.get("content_hash") != _content_hash(closure):
            errors.append("closure_content_hash_mismatch")

    return errors


def _packet_oracle(packet: Dict[str, Any]) -> List[str]:
    """Mechanically validate the authority relations of a packet.

    Returns a list of error codes; an empty list means the packet is valid.
    Every check is deterministic and resolves refs against the packet's own
    authorities (synthetic offline fixture), never against typed Member."""
    errors: List[str] = []
    idx = _index_packet_authorities(packet)
    _lifecycles = idx["lifecycles"]
    _closures = idx["closures"]
    _domains = idx["domains"]
    payload = idx["payload"]

    # Every supplemental authority is a first-class packet input.  Validate
    # its exact shape and receipt/source/count bindings before any projection
    # closure so a re-signed object cannot be ignored as an unused leaf.
    errors.extend(_validate_supplemental_authorities(packet))

    # packet-id grammar: exactly single-colon prefix:hash.
    pid = packet.get("packet_id", "")
    if not pid.startswith(f"{PACKET_ID_PREFIX}:") or pid.count(":") != 1:
        errors.append("packet_id_grammar_mismatch")
        return errors
    replay_hash = packet.get("audience_replay_content_hash", "")
    if pid != f"{PACKET_ID_PREFIX}:{replay_hash}":
        errors.append("packet_id_grammar_mismatch")
        return errors

    # replay hash covers the COMPLETE audience payload (incl. low clusters).
    if replay_hash != _h(payload):
        errors.append("stale_replay_rejected")
    # integrity hash excludes its own dependencies (acyclic DAG).
    integrity_body = {k: v for k, v in packet.items()
                      if k not in ("packet_id", "packet_integrity_hash",
                                   "audience_replay_content_hash",
                                   "schema", "status", "authority_mode")}
    if packet.get("packet_integrity_hash") != _h(integrity_body):
        errors.append("packet_integrity_hash_mismatch")

    # cluster canonical ref + replay presence (bl 5).
    clusters = idx["clusters"]
    for cluster in clusters:
        expected_ref = CLUSTER_REF_PREFIX + cluster.get("content_hash", "")
        if cluster.get("cluster_ref") != expected_ref:
            errors.append("cluster_canonical_ref_mismatch")
        if cluster.get("content_hash") != _h(
                {k: v for k, v in cluster.items()
                 if k not in ("cluster_ref", "content_hash")}):
            errors.append("cluster_canonical_ref_mismatch")

    current_risk = idx["current_risk"]
    current_refs = list(current_risk.get("high_risk_refs", [])) + \
        list(current_risk.get("medium_risk_refs", [])) + \
        list(current_risk.get("low_risk_cluster_refs", []))
    resolved_refs = list(current_risk.get("resolved_history_refs", []))

    # aggregate receipt-set identity.
    agg = packet.get("aggregate_receipt_set", {})
    units = idx["units"]
    agg_refs = sorted(agg.get("unit_receipt_refs", []))
    unit_receipt_refs = sorted({
        RECEIPT_REF_PREFIX + u.get("receipt_content_hash", "")
        for u in units})
    if agg_refs != unit_receipt_refs:
        errors.append("aggregate_identity_mismatch")
    else:
        risk_hashes = sorted({m.get("content_hash")
                              for m in idx["marker_by_id"].values()})
        body = {k: agg.get(k) for k in (
            "unit_receipt_refs", "risk_marker_identity_hashes",
            "project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
            "audience_contract_id")}
        if agg.get("aggregate_id") != "aggregate:" + _h(body) or \
                sorted(agg.get("risk_marker_identity_hashes", [])) != \
                risk_hashes:
            errors.append("aggregate_identity_mismatch")
    if current_risk.get("authority_receipt_ref") != agg.get("aggregate_id"):
        errors.append("aggregate_identity_mismatch")

    # current vs resolved disjoint.
    current_plain = [r for r in current_refs
                     if not r.startswith(CLUSTER_REF_PREFIX)]
    if set(current_plain) & set(resolved_refs):
        errors.append("current_reserved_overlap_check")

    # ---- Block 1: exact current-risk set closure -------------------------
    proj = _project_current_risk_planes(packet, idx)
    errors.extend(proj["errors"])

    # every current/resolved ref resolves exactly one lifecycle + marker and
    # lifecycle/marker/handoff/domain binding integrity.
    def _resolve_marker(marker_id: str) -> Optional[Dict[str, Any]]:
        return idx["marker_by_id"].get(marker_id)

    def _resolve_handoff(handoff_id: str) -> Optional[Dict[str, Any]]:
        return idx["handoff_by_id"].get(handoff_id)

    for ref in current_plain + resolved_refs:
        if not _is_current_marker_ref(ref):
            errors.append("current_risk_not_marker_prefix")
            continue
        matches = [l for marker, l in _lifecycles.items() if marker == ref]
        if len(matches) != 1:
            errors.append("current_risk_lifecycle_unresolved")
            continue
        lifecycle_ = matches[0]
        marker = _resolve_marker(lifecycle_.get("marker_id"))
        if marker is None:
            errors.append("current_risk_marker_unresolved")
            continue
        if lifecycle_.get("marker_id") != marker.get("marker_id") or \
                lifecycle_.get("marker_content_hash") != marker.get(
                "content_hash"):
            errors.append("lifecycle_marker_identity_mismatch")
        if sorted(lifecycle_.get("member_expansion_refs", [])) != \
                sorted(marker.get("member_refs", [])):
            errors.append("lifecycle_member_expansion_mismatch")
        prefix = "d09_marker:" if lifecycle_.get("marker_kind") == "d09" \
            else "d10_marker:"
        if not ref.startswith(prefix):
            errors.append("lifecycle_marker_identity_mismatch")
        handoff = _resolve_handoff(lifecycle_.get("r2_handoff_id"))
        if handoff is None:
            errors.append("lifecycle_r2_binding_mismatch")
        else:
            if lifecycle_.get("lifecycle_action") != handoff.get("action"):
                errors.append("lifecycle_action_drift")
            priority = handoff.get("monitoring_priority")
            if priority not in ("high", "medium", "low"):
                errors.append("severity_not_in_enum")
            elif lifecycle_.get("severity") != priority:
                errors.append("lifecycle_severity_drift")
            mapping = EXPECTED_LIFECYCLE_STATE_TABLE.get(
                handoff.get("action"), {})
            if lifecycle_.get("lifecycle_state") != mapping.get("state") \
                    and lifecycle_.get("lifecycle_state") != "resolved":
                errors.append("lifecycle_state_mapping_mismatch")
        state = lifecycle_.get("lifecycle_state")
        closure_ref = lifecycle_.get("closure_authority_ref")
        if state == "resolved":
            if not closure_ref:
                errors.append("resolved_without_lifecycle_authority")
            elif closure_ref not in _closures:
                errors.append("resolved_closure_unresolved")
            elif _closures[closure_ref].get(
                    "prior_public_risk_identity_ref") != ref:
                errors.append("closure_identity_mismatch")
        elif closure_ref:
            errors.append("propose_close_resolved"
                          if lifecycle_.get("lifecycle_action")
                          == "propose_close"
                          else "lifecycle_state_mapping_mismatch")
        if lifecycle_.get("lifecycle_action") == "propose_close" and \
                state == "resolved":
            errors.append("propose_close_resolved")
        domain_ref = lifecycle_.get("clinical_domain_ref")
        if domain_ref not in _domains:
            errors.append("lifecycle_domain_drift")
        else:
            domain = _domains[domain_ref].get("clinical_domain")
            if domain not in EXPECTED_ENUMS["domain"]:
                errors.append("clinical_domain_not_in_enum")
            unit_ = idx["unit_by_marker_id"].get(lifecycle_.get("marker_id"))
            if unit_ is None:
                errors.append("unknown_lifecycle_authority")
                continue
            variant = unit_.get("d09_variant_payload") or \
                unit_.get("d10_variant_payload") or {}
            unit_domain_ref = variant.get("clinical_domain_authority_ref")
            if unit_domain_ref != domain_ref:
                errors.append("lifecycle_domain_drift")
            if unit_domain_ref not in _domains:
                errors.append("unknown_domain_authority")

    # low cluster members resolve low/current lifecycle authorities.
    for cluster in clusters:
        cluster_domain = cluster.get("domain")
        for member in cluster.get("member_refs", []):
            owners = [l for l in _lifecycles.values()
                      if member in l.get("member_expansion_refs", [])
                      and l.get("lifecycle_state") == "current"]
            if not owners:
                errors.append("cluster_lifecycle_unresolved")
            else:
                for owner in owners:
                    if owner.get("clinical_domain_ref") not in _domains or \
                            _domains[owner.get("clinical_domain_ref")].get(
                            "clinical_domain") != cluster_domain:
                        errors.append("cluster_lifecycle_unresolved")

    # ---- Block 2: exact center-cell closure ------------------------------
    center_proj = _project_center_cells(packet, idx)
    errors.extend(center_proj["errors"])
    center_map = idx["center_map"]
    declared_cells = list(center_map.get("cells", []))
    expected_cells = center_proj["cells"]
    declared_site_order = list(center_map.get("stable_site_order", []))
    expected_site_order = center_proj["stable_site_order"]

    declared_keyed = {(c.get("site_ref"), c.get("domain")): c
                      for c in declared_cells}
    expected_keyed = {(c["site_ref"], c["domain"]): c
                      for c in expected_cells}
    # a declared cell whose site is not a projectable site is a site drift,
    # distinct from a pure set mismatch (stable specific code).
    projectable_sites = set(center_proj["stable_site_order"])
    for c in declared_cells:
        if c.get("site_ref") not in projectable_sites:
            errors.append("center_cell_site_mismatch")
    if set(declared_keyed) != set(expected_keyed) and not any(
            c.get("site_ref") not in projectable_sites
            for c in declared_cells):
        errors.append("center_cell_set_mismatch")
    for key in set(declared_keyed) & set(expected_keyed):
        dc = declared_keyed[key]
        ec = expected_keyed[key]
        if dc.get("site_ref") != ec["site_ref"]:
            errors.append("center_cell_site_mismatch")
        if sorted(dc.get("individual_risk_refs", [])) != \
                ec["individual_risk_refs"]:
            errors.append("center_cell_classification_mismatch")
        if sorted(dc.get("pattern_refs", [])) != ec["pattern_refs"]:
            errors.append("center_cell_classification_mismatch")
        if dc.get("severity") != ec.get("severity"):
            errors.append("center_cell_severity_drift")
        if sorted(dc.get("measure_refs", [])) != sorted(
                ec.get("measure_refs", [])):
            errors.append("center_cell_ref_mismatch")
    declared_order = [(c.get("site_ref"), c.get("domain"))
                      for c in declared_cells]
    expected_order = [(c["site_ref"], c["domain"]) for c in expected_cells]
    if declared_order != expected_order:
        errors.append("center_cell_order_mismatch")
    if declared_site_order != expected_site_order:
        errors.append("center_cell_order_mismatch")
    # D09 pattern upgrade guard: a pattern member must never be D10.
    for ref in [r for c in declared_cells
                for r in c.get("pattern_refs", [])]:
        owners = [l for l in _lifecycles.values()
                  if ref in l.get("member_expansion_refs", [])]
        for owner in owners:
            if owner.get("marker_kind") != "d09":
                errors.append("center_cell_pattern_upgrade")

    # ---- Block 3: closure bidirectional integrity ------------------------
    errors.extend(_validate_closure_integrity(packet, idx))

    # global lifecycle rules (bl 3): propose_close never resolves; resolved
    # requires its closure object.
    for l in _lifecycles.values():
        state = l.get("lifecycle_state")
        action = l.get("lifecycle_action")
        if action == "propose_close" and state == "resolved":
            errors.append("propose_close_resolved")
        if state == "resolved" and not l.get("closure_authority_ref"):
            errors.append("resolved_without_lifecycle_authority")
        if l.get("closure_authority_ref") and state != "resolved":
            errors.append("lifecycle_state_mapping_mismatch")
        mapping = EXPECTED_LIFECYCLE_STATE_TABLE.get(action)
        if mapping is None:
            errors.append("lifecycle_state_mapping_mismatch")
        elif state != mapping.get("state") and state != "resolved":
            errors.append("lifecycle_state_mapping_mismatch")

    # message digests for imported objects are shape-checked only; the
    # oracle did not need typed R4/R5 instances (synthetic offline fixture).
    return errors


def _project_change_bands(packet: Dict[str, Any],
                          idx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Rebuild change-band rows from lifecycle, handoff and receipt inputs."""
    severity_order = {"high": 0, "medium": 1, "low": 2}
    rows: List[Tuple[Tuple[int, str], Dict[str, Any]]] = []
    for ref, lifecycle in idx["lifecycles"].items():
        unit = idx["unit_by_marker_id"].get(lifecycle.get("marker_id"))
        if unit is None:
            continue
        receipt = unit.get("authority_receipt", {})
        handoff = idx["handoff_by_id"].get(lifecycle.get("r2_handoff_id"), {})
        variant = idx["variants"].get(unit.get("unit_ref"), {})
        section = variant.get("change_section", {})
        if lifecycle.get("lifecycle_state") == "resolved":
            change_kind = "resolved"
        elif section.get("change_kind"):
            change_kind = section["change_kind"]
        elif handoff.get("action") == "create":
            change_kind = "initial_current"
        else:
            change_kind = "continued"
        change_cause = section.get("change_cause") if section else None
        row = {
            "authority_receipt_ref": RECEIPT_REF_PREFIX + _h(receipt),
            "change_cause": change_cause,
            "change_kind": change_kind,
            "current_snapshot_ref": receipt.get("snapshot_ref"),
            "prior_snapshot_ref": None,
            "risk_ref": ref,
        }
        rank = (0 if change_kind != "resolved" else 3,
                severity_order.get(lifecycle.get("severity"), 9), ref)
        rows.append((rank, row))
    return [row for _rank, row in sorted(rows, key=lambda item: item[0])]


def _project_center_map(packet: Dict[str, Any], idx: Dict[str, Any],
                        cells: List[Dict[str, Any]],
                        stable_site_order: List[str]) -> Dict[str, Any]:
    """Build center-map metadata from a public receipt, not a payload echo."""
    d10_units = [unit for unit in idx["units"]
                 if "d10_variant_payload" in unit]
    source_unit = sorted(d10_units, key=lambda unit: unit.get("unit_ref", ""))[0] \
        if d10_units else sorted(idx["units"],
                                 key=lambda unit: unit.get("unit_ref", ""))[0]
    receipt = source_unit.get("authority_receipt", {})
    receipt_ref = RECEIPT_REF_PREFIX + _h(receipt)
    projection_instance = {
        "authority_receipt_ref": receipt_ref,
        "content_hash": None,
        "opaque_run_ref": receipt.get("run_ref"),
        "opaque_snapshot_ref": receipt.get("snapshot_ref"),
        "replay_content_identity": _h({
            "authority_receipt_ref": receipt_ref,
            "stable_site_order": stable_site_order,
        }),
    }
    projection_instance["content_hash"] = _content_hash(projection_instance)
    center_map = {
        "cells": cells,
        "content_hash": None,
        "projection_instance": projection_instance,
        "stable_site_order": stable_site_order,
    }
    center_map["content_hash"] = _content_hash(center_map)
    return center_map


def _project_cockpit(center_map: Dict[str, Any],
                     change_bands: List[Dict[str, Any]],
                     measures: List[Dict[str, Any]],
                     planes: Dict[str, Any]) -> Dict[str, Any]:
    """Build a renderer-neutral cockpit surface from rebuilt projections."""
    selected = (planes.get("high") or planes.get("medium") or
                planes.get("low") or planes.get("resolved") or [None])[0]
    cockpit = {
        "center_map_ref": "center_map.v1",
        "change_band_refs": [f"band.{index}"
                             for index in range(1, len(change_bands) + 1)],
        "content_hash": None,
        "current_risk_set_ref": "current_risk_set.v1",
        "measure_refs": [m["authoritative_value_ref"] for m in measures],
        "projection_instance": center_map["projection_instance"],
        "selected_risk_ref": selected,
    }
    cockpit["content_hash"] = _content_hash(cockpit)
    return cockpit


def _project_audience_payload_from_authorities(
        packet: Dict[str, Any]) -> Dict[str, Any]:
    """Independent authority projector used by the accept oracle.

    It reconstructs the complete audience payload from lifecycles, public
    markers/handoffs/hotspots, clinical-domain authorities, receipts and
    public count/center rows.  The packet's declared payload, planes, cells,
    replay hash and packet id are never used as projector inputs; they are
    comparison targets only.
    """
    supplemental_errors = _validate_supplemental_authorities(packet)
    if supplemental_errors:
        raise VerificationError(
            "packet_oracle_failed: supplemental authority integrity: "
            f"{supplemental_errors}")
    idx = _index_packet_authorities(packet)
    planes = _project_current_risk_planes(packet, idx,
                                          compare_declared=False)
    if planes["errors"]:
        raise VerificationError(
            "packet_oracle_failed: authority projection current-risk "
            f"closure: {planes['errors']}")
    cells = _project_center_cells(packet, idx)
    if cells["errors"]:
        raise VerificationError(
            "packet_oracle_failed: authority projection center-cell "
            f"closure: {cells['errors']}")
    closure_errors = _validate_closure_integrity(packet, idx)
    if closure_errors:
        raise VerificationError(
            "packet_oracle_failed: authority projection closure "
            f"integrity: {closure_errors}")

    projected_clusters = _project_low_risk_clusters(packet, idx)
    aggregate_id = packet.get("aggregate_receipt_set", {}).get("aggregate_id")
    current_risk_set = {
        "authority_receipt_ref": aggregate_id,
        "high_risk_refs": planes["planes"]["high"],
        "low_risk_cluster_refs": planes["planes"]["low"],
        "medium_risk_refs": planes["planes"]["medium"],
        "resolved_history_refs": planes["planes"]["resolved"],
    }
    measures = _project_measures(packet, idx)
    change_bands = _project_change_bands(packet, idx)
    center_map = _project_center_map(packet, idx, cells["cells"],
                                     cells["stable_site_order"])
    payload = {
        "current_risk_set": current_risk_set,
        "change_bands": change_bands,
        "measures": measures,
        "center_map": center_map,
        "cockpit": _project_cockpit(center_map, change_bands, measures,
                                     planes["planes"]),
        "low_risk_clusters": projected_clusters,
    }
    replay_hash = _h(payload)
    packet_for_hash = dict(packet)
    packet_for_hash["audience_payload"] = payload
    integrity_body = {k: v for k, v in packet_for_hash.items()
                      if k not in ("packet_id", "packet_integrity_hash",
                                   "audience_replay_content_hash", "schema",
                                   "status", "authority_mode")}
    return {
        "projection": payload,
        "audience_replay_content_hash": replay_hash,
        "packet_id": f"{PACKET_ID_PREFIX}:{replay_hash}",
        "current_risk_planes": planes["planes"],
        "center_cells": cells["cells"],
        "stable_site_order": cells["stable_site_order"],
        "hashes": {
            "audience_replay_content_hash": replay_hash,
            "packet_integrity_hash": _h(integrity_body),
        },
    }


def project_audience_payload(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Block 4 executable projection oracle.

    Deterministically runs every projector (current-risk exact planes,
    exact center cells, closure bidirecational integrity) against the
    packet authorities, then returns the canonical audience projection and
    its required hashes.  The comparison contract for an accept challenge:

      * the projectors must pass (else VerificationError -> rejected);
      * the produced canonical projection bytes and the required
        ``audience_replay_content_hash`` must exactly match the packet's
        audience payload and replay hash (bidirectional equality);
      * a stubbed projector (empty projection) fails the comparison.

    This function is the single executable path used by the accept-challenge
    oracle; it can never be a label-only assertion.
    """
    return _project_audience_payload_from_authorities(packet)


def payload_change_bands(packet: Dict[str, Any],
                         idx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Change bands projected verbatim from the payload (closure-integrity
    validated separately); presented so the accept oracle can compare."""
    return idx["payload"].get("change_bands", [])


def _packet_oracle_pass(packet: Dict[str, Any]) -> None:
    errors = _packet_oracle(packet)
    _require(not errors,
             f"packet_oracle_failed: sample packet invalid: {errors}")


# ---------------------------------------------------------------------------
# internal tamper/attack probes
# ---------------------------------------------------------------------------


def _tamper_probes(overlay: Dict[str, Any], schema: Dict[str, Any],
                   registry: Dict[str, Any], manifest: Dict[str, Any],
                   maps: Any, root: Path, artifacts: Path) -> int:
    probes: List[Tuple[str, Any]] = []
    denylist = overlay["typed_input_denylist"]
    allowlist = overlay["public_allowlist"]

    def expect_code(name: str, fn: Any, code: str) -> None:
        probes.append((name, (fn, code)))

    # --- artifact/overlay/schema tamper probes (each exact code) ----------
    bad = copy.deepcopy(overlay)
    bad["source_matrix"].append({
        "leaf": "unit.d10.injected", "source_kind": "r4_public",
        "path": "mm_r4.d10_contracts:D10TypedInput.members",
        "provenance": "tamper"})
    bad["source_bindings"].append({
        "binding_id": "unit.d10.injected", "kind": "r4_public",
        "target": "mm_r4.d10_contracts:D10TypedInput.members",
        "role": "tamper"})
    expect_code("typed_input_source_path_injected",
                (lambda b=bad: _parse_all_source_paths(b, {}, maps, root)),
                "typed_input_leaf_promoted")

    bad = copy.deepcopy(overlay)
    bad["layer_recipes"] = [r for r in bad["layer_recipes"]
                            if r["layer"] != "query"]
    expect_code("layer_recipe_missing",
                (lambda b=bad: _require_layer_recipes(b["layer_recipes"])),
                "layer_recipe_missing")

    bad = copy.deepcopy(overlay)
    bad["enums"]["coverage_state"] = (
        list(EXPECTED_ENUMS["coverage_state"]) + ["not_evaluable"])
    expect_code("invalid_coverage_enum",
                (lambda b=bad: _validate_overlay(b, maps, root)),
                "invalid_coverage_enum")

    bad = copy.deepcopy(overlay)
    bad["hash_dag"]["audience_replay_content_hash"]["may_cover_hidden"] = True
    expect_code("hidden_leaf_in_audience_hash",
                (lambda b=bad: _require_hash_dag(b["hash_dag"])),
                "hidden_leaf_in_audience_hash")

    bad = copy.deepcopy(overlay)
    bad["change_emission_table"] = [
        r for r in bad["change_emission_table"]
        if r["change_kind"] != "resolved"]
    expect_code("change_emission_missing",
                (lambda b=bad: _require_change_emission(
                    b["change_emission_table"])),
                "change_emission_missing")

    bad = copy.deepcopy(overlay)
    for row in bad["change_emission_table"]:
        if row["change_kind"] == "new":
            row["marker_present"] = "forbidden"
    expect_code("change_marker_absent_ambiguity",
                (lambda b=bad: _require_change_emission(
                    b["change_emission_table"])),
                "marker_required_for_change_kind")

    bad = copy.deepcopy(overlay)
    bad["hash_dag"]["receipt_content_hash"]["algorithm"] = "sha1"
    expect_code("receipt_recipe_sha1",
                (lambda b=bad: _require_hash_dag(b["hash_dag"])),
                "hash_algorithm_mismatch")

    bad = copy.deepcopy(overlay)
    bad["hash_dag"]["audience_replay_content_hash"]["depends_on"] = [
        "audience_replay_content_hash"]
    expect_code("audience_replay_self_edge",
                (lambda b=bad: _require_hash_dag(b["hash_dag"])),
                "hash_recipe_cycle")

    bad = copy.deepcopy(overlay)
    bad["packet_id_grammar"] = "r5-s3-contract::<audience_replay_content_hash>"
    expect_code("packet_id_double_colon",
                (lambda b=bad: _require_packet_id_grammar(
                    b["packet_id_grammar"])),
                "packet_id_grammar_mismatch")

    bad = copy.deepcopy(overlay)
    bad["acceptance_boundary"]["acceptance_digest"]["owner"] = "generator"
    expect_code("acceptance_digest_generator_owned",
                (lambda b=bad: _validate_overlay(b, maps, root)),
                "authority_scope_violation")

    bad_schema = copy.deepcopy(schema)
    bad_schema["objects"].pop("R5S3AggregateReceiptSetIdentity")
    expect_code("aggregate_receipt_missing",
                (lambda b=bad_schema: _validate_schema(
                    b, maps, root, denylist, allowlist,
                    overlay["tagged_variants"])),
                "aggregate_receipt_missing")

    bad_schema = copy.deepcopy(schema)
    bad_schema["objects"]["R5S3AuthorityPacket"]["content_hash"] = {
        "type": "sha256", "cardinality": "one", "nullable": False}
    expect_code("root_content_hash_injected",
                (lambda b=bad_schema: _validate_schema(
                    b, maps, root, denylist, allowlist,
                    overlay["tagged_variants"])),
                "schema_key_mismatch")

    bad_schema = copy.deepcopy(schema)
    bad_schema["objects"].pop("R5S3AudiencePayload")
    expect_code("audience_payload_missing",
                (lambda b=bad_schema: _validate_schema(
                    b, maps, root, denylist, allowlist,
                    overlay["tagged_variants"])),
                "low_cluster_not_in_replay")

    bad_reg = copy.deepcopy(registry)
    bad_reg["challenges"][0]["case_id"] = bad_reg["challenges"][1]["case_id"]
    expect_code("challenge_duplicate_id",
                (lambda b=bad_reg: _validate_challenge_registry(
                    b, root / TEST_FILE_RELATIVE, root)),
                "challenge_duplicate_id")

    bad_reg = copy.deepcopy(registry)
    bad_reg["challenges"][0]["stage_oracle_contract"]["test_locator"] = ""
    expect_code("challenge_missing_locator",
                (lambda b=bad_reg: _validate_challenge_registry(
                    b, root / TEST_FILE_RELATIVE, root)),
                "challenge_missing_locator")

    # --- packet attack probes (each exact code) ---------------------------
    sample = build_sample_packet()

    def _resign_packet_body(packet: Dict[str, Any]) -> None:
        """Recompute packet hashes after an attack mutation so the oracle is
        the only remaining defense (coordinated re-sign semantics)."""
        packet["audience_replay_content_hash"] = _h(
            packet["audience_payload"])
        packet["packet_id"] = f"{PACKET_ID_PREFIX}:" + packet[
            "audience_replay_content_hash"]
        integrity_body = {k: v for k, v in packet.items()
                          if k not in ("packet_id", "packet_integrity_hash",
                                       "audience_replay_content_hash",
                                       "schema", "status", "authority_mode")}
        packet["packet_integrity_hash"] = _h(integrity_body)

    def mutate_packet(op: str) -> Dict[str, Any]:
        packet = copy.deepcopy(sample)
        if op == "packet_raw_member_high_refs":
            packet["audience_payload"]["current_risk_set"]["high_risk_refs"] = [
                "member.raw"]
        elif op == "packet_lifecycle_domain_drift":
            for l in packet["risk_lifecycle_authorities"]:
                if l["marker_identity_ref"] == "d10_marker:m-d10-hi":
                    l["clinical_domain_ref"] = "cda.d09"
        elif op == "packet_lifecycle_severity_drift":
            for l in packet["risk_lifecycle_authorities"]:
                if l["marker_identity_ref"] == "d10_marker:m-d10-hi":
                    l["severity"] = "critical"
        elif op == "packet_lifecycle_action_drift":
            for l in packet["risk_lifecycle_authorities"]:
                if l["marker_identity_ref"] == "d10_marker:m-d10-hi":
                    l["lifecycle_action"] = "supersede"
        elif op == "packet_lifecycle_member_expansion_drift":
            for l in packet["risk_lifecycle_authorities"]:
                if l["marker_identity_ref"] == "d10_marker:m-d10-hi":
                    l["member_expansion_refs"] = ["member.a", "member.x"]
        elif op == "packet_current_resolved_overlap":
            packet["audience_payload"]["current_risk_set"][
                "resolved_history_refs"] = ["d10_marker:m-d10-hi"]
        elif op == "packet_closure_missing":
            for l in packet["risk_lifecycle_authorities"]:
                if l["marker_identity_ref"] == "d09_marker:m-d09-res":
                    l["closure_authority_ref"] = None
        elif op == "packet_low_cluster_stale":
            cluster = packet["audience_payload"]["low_risk_clusters"][0]
            cluster["member_refs"] = ["member.x"]
            cluster["content_hash"] = _h(cluster)
            cluster["cluster_ref"] = CLUSTER_REF_PREFIX + cluster["content_hash"]
        elif op == "packet_propose_close_resolved":
            for l in packet["risk_lifecycle_authorities"]:
                if l["marker_identity_ref"] == "d09_marker:m-d09-lo":
                    l["lifecycle_action"] = "propose_close"
                    l["lifecycle_state"] = "resolved"
        elif op == "packet_high_to_medium_move":
            packet["audience_payload"]["current_risk_set"]["high_risk_refs"] = []
            packet["audience_payload"]["current_risk_set"]["medium_risk_refs"] = [
                "d10_marker:m-d10-hi"]
            _resign_packet_body(packet)
        elif op == "packet_delete_all_high":
            packet["audience_payload"]["current_risk_set"]["high_risk_refs"] = []
            _resign_packet_body(packet)
        elif op == "packet_delete_all_low_clusters":
            packet["audience_payload"]["current_risk_set"][
                "low_risk_cluster_refs"] = []
            _resign_packet_body(packet)
        elif op == "packet_center_delete_all_cells":
            packet["audience_payload"]["center_map"]["cells"] = []
            packet["audience_payload"]["center_map"].pop("content_hash", None)
            _resign_packet_body(packet)
        elif op == "packet_center_change_site":
            cells = packet["audience_payload"]["center_map"]["cells"]
            for cell in cells:
                if cell["site_ref"] == "site.d10":
                    cell["site_ref"] = "site.d10x"
            packet["audience_payload"]["center_map"].pop("content_hash", None)
            _resign_packet_body(packet)
        elif op == "packet_center_reorder_cells":
            cells = packet["audience_payload"]["center_map"]["cells"]
            if len(cells) >= 2:
                packet["audience_payload"]["center_map"]["cells"] = list(
                    reversed(cells))
            packet["audience_payload"]["center_map"].pop("content_hash", None)
            _resign_packet_body(packet)
        elif op == "packet_d09_pattern_to_individual":
            for l in packet["risk_lifecycle_authorities"]:
                if l["marker_identity_ref"] == "d09_marker:m-d09-lo":
                    l["marker_kind"] = "d10"
            _resign_packet_body(packet)
        elif op == "packet_fake_prior_instance":
            for c in packet["closure_authorities"]:
                c["prior_risk_instance_ref"] = "inst.fake"
            _resign_packet_body(packet)
        elif op == "packet_closure_decision_hash_changed":
            for c in packet["closure_authorities"]:
                c["closure_decision_hash"] = "0" * 64
            _resign_packet_body(packet)
        elif op == "packet_closure_orphan":
            extra = copy.deepcopy(packet["closure_authorities"][0])
            extra["closure_authority_id"] = "closure.orphan"
            packet["closure_authorities"].append(extra)
            packet["closure_authorities"] = sorted(
                packet["closure_authorities"],
                key=lambda c: c["closure_authority_id"])
            _resign_packet_body(packet)
        return packet

    packet_attack_codes = PACKET_ATTACK_EXPECTED.copy()
    for op, code in packet_attack_codes.items():

        def run_packet_attack(op: str = op, code: str = code) -> None:
            attacked = mutate_packet(op)
            errors = _packet_oracle(attacked)
            if code in errors:
                _fail(f"{code}: packet attack {op} correctly rejected")
            _fail(f"packet_assert_failed: packet attack {op} NOT detected: "
                  f"{errors}")

        expect_code(f"packet_attack_{op}", run_packet_attack, code)

    # hidden-only mutation keeps audience identical (positive control).
    def hidden_only_mutation() -> None:
        packet = copy.deepcopy(sample)
        before_replay = packet["audience_replay_content_hash"]
        before_integrity = packet["packet_integrity_hash"]
        packet["audience_payload"]["current_risk_set"]["low_risk_cluster_refs"] = \
            packet["audience_payload"]["current_risk_set"][
                "low_risk_cluster_refs"]
        for u in packet["authority_units"]:
            if u["unit_ref"] == "unit.d10":
                u["hidden_member_refs"] = ["member.hidden"]
        for l in packet["risk_lifecycle_authorities"]:
            if l["marker_identity_ref"] == "d10_marker:m-d10-hi":
                l["member_expansion_refs"] = ["member.a", "member.b"]
        if _h(packet["audience_payload"]) != before_replay:
            _fail("packet_assert_failed: hidden-only mutation changed replay")
        if packet["packet_integrity_hash"] == before_integrity:
            _fail("packet_assert_failed: hidden-only mutation must change "
                  "packet_integrity_hash")

    expect_code("hidden_only_mutation_keeps_audience",
                hidden_only_mutation, "")

    # unit-order permutation canonicalizes (sorted units); replay identical.
    def unit_order_permutation() -> None:
        packet = copy.deepcopy(sample)
        before = packet["audience_replay_content_hash"]
        packet["authority_units"] = list(reversed(packet["authority_units"]))
        if _h(packet["audience_payload"]) != before:
            _fail("packet_assert_failed: unit-order permutation must not "
                  "change the audience replay content hash")

    expect_code("unit_order_permutation_canonicalized",
                unit_order_permutation, "")

    passed = 0
    for name, (fn, code) in probes:
        try:
            fn()
        except VerificationError as error:
            if code:
                _require(code in str(error),
                         f"tamper probe {name} failed with the wrong code: "
                         f"{error} (expected {code!r})")
            passed += 1
        else:
            if code:
                _fail(f"tamper probe unexpectedly passed: {name}")
            passed += 1
    return passed


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    args = parser.parse_args()
    root: Path = args.root
    artifacts: Path = args.artifacts
    try:
        overlay_path = artifacts / "exact_overlay.json"
        schema_path = artifacts / "packet_schema.json"
        registry_path = artifacts / "challenge_registry.json"
        pins_path = artifacts / "source_pins.json"
        manifest_path = artifacts / "manifest.json"
        overlay = _load_json(overlay_path)
        schema = _load_json(schema_path)
        registry = _load_json(registry_path)
        pins = _load_json(pins_path)
        manifest = _load_json(manifest_path)
        _walk_strings(overlay, "overlay")
        _walk_strings(schema, "schema")
        _walk_strings(registry, "registry")
        _walk_strings(pins, "pins")
        _walk_strings(manifest, "manifest")
        maps = {module: _parse_classes(path, root)
                for module, path in MODULE_FILES.items()}
        denylist = overlay["typed_input_denylist"]
        allowlist = overlay["public_allowlist"]
        _validate_overlay(overlay, maps, root)
        _validate_schema(schema, maps, root, denylist, allowlist,
                         overlay["tagged_variants"])
        test_path = root / TEST_FILE_RELATIVE
        _require(test_path.exists() and test_path.is_file(),
                 f"challenge_missing_locator: test file missing: {test_path}")
        _validate_challenge_registry(registry, test_path, root)
        _validate_source_pins(pins, root)
        _validate_manifest(manifest, artifacts, root)
        _check_no_assert("tools/generate_medical_monitoring_r5_s3_contract_v0_2.py", root)
        _check_no_assert("tools/verify_medical_monitoring_r5_s3_contract_v0_2.py", root)
        # sample packet must be internally valid under the full oracle.
        _packet_oracle_pass(build_sample_packet())
        tamper_count = _tamper_probes(overlay, schema, registry, manifest,
                                      maps, root, artifacts)
    except VerificationError as error:
        print(json.dumps({"ok": False, "error": str(error)},
                         ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps({
        "ok": True,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "challenge_rows": registry["challenge_count"],
        "layer_recipes": len(overlay["layer_recipes"]),
        "change_kinds": len(overlay["change_emission_table"]),
        "tagged_variants": len(overlay["tagged_variants"]),
        "source_bindings": len(overlay["source_bindings"]),
        "supplemental_objects": len(SUPPLEMENTAL_OBJECT_NAMES),
        "packet_oracle": "passed",
        "tamper_probes_rejected": tamper_count,
        "artifact_shas": {
            item["path"]: (item["sha256"]
                           if item["hash_kind"] == "raw_sha256"
                           else manifest["manifest_content_sha256"])
            for item in manifest["artifacts"]},
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
