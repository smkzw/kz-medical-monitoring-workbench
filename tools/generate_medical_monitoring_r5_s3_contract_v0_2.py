#!/usr/bin/env python3
"""Deterministic generator for the R5-S3 implementation-contract artifact set.

Generates the four non-manifest data artifacts plus the manifest under
``artifacts/medical_monitoring_r5_s3_contract_v0_2/``.  Deterministic:
same inputs -> identical bytes.  ``--check`` compares without writing.

Artifacts are the machine authority for R5-S3 (reviewer blocker 7):
  * packet_schema.json          -- exact keys/types/cardinality/nullability
  * exact_overlay.json          -- closed enums, source bindings + denylist,
                                   structured layer recipes, change emission
                                   table, hash DAG, receipt recipe, packet-id
                                   grammar, acceptance boundary with
                                   external acceptance-digest policy
  * challenge_registry.json     -- exactly CHALLENGE_EXACT independent rows
                                   with executable mutations and exact
                                   expected typed outcomes
  * source_pins.json            -- source-of-truth + generator/verifier pins
  * manifest.json               -- artifact set, shas, pins, canonical hash

The generator never writes to any other path.  No ``assert`` is used in any
decision path so normal and PYTHONOPTIMIZE=2 runs are identical.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_DIR = ROOT / "artifacts" / "medical_monitoring_r5_s3_contract_v0_2"

OVERLAY_PATH = ARTIFACT_DIR / "exact_overlay.json"
SCHEMA_PATH = ARTIFACT_DIR / "packet_schema.json"
CHALLENGE_PATH = ARTIFACT_DIR / "challenge_registry.json"
SOURCE_PINS_PATH = ARTIFACT_DIR / "source_pins.json"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"

HUMAN_CONTRACT_PATH = ROOT / "reviews" / "medical_monitoring_r5_s3_implementation_contract_v0_2_20260818.md"
GENERATOR_PATH = ROOT / "tools" / "generate_medical_monitoring_r5_s3_contract_v0_2.py"
VERIFIER_PATH = ROOT / "tools" / "verify_medical_monitoring_r5_s3_contract_v0_2.py"
TEST_PATH = ROOT / "poc" / "medical_monitoring_ai_native_r5" / "tests" / "test_s3_contract_artifacts.py"

STATUS = "R5_S3_CONTRACT_READY_FOR_REVIEW"
AUTHORITY_MODE = "synthetic_offline_test_only"
OVERLAY_SCHEMA = "medical-monitoring-r5-s3-exact-overlay-v0.2"
PACKET_SCHEMA = "medical-monitoring-r5-s3-packet-schema-v0.2"
CHALLENGE_SCHEMA = "medical-monitoring-r5-s3-challenge-registry-v0.2"
SOURCE_PINS_SCHEMA = "medical-monitoring-r5-s3-source-pins-v0.2"
MANIFEST_SCHEMA = "medical-monitoring-r5-s3-artifact-manifest-v0.2"

#: Exactly one challenge per row; every row is an independent executable
#: oracle with a real pytest nodeid under the parametrized challenge test.
CHALLENGE_EXACT = 60
LAYER_RECIPE_COUNT = 8
CHANGE_KIND_COUNT = 10
TAGGED_VARIANT_COUNT = 2

#: packet-id grammar is exactly single-colon: prefix + ':' + replay hash.
PACKET_ID_PREFIX = "r5-s3-contract"
RECEIPT_REF_PREFIX = "receipt:"
CLUSTER_REF_PREFIX = "cluster:"
HASH_ALGORITHM = "sha256"
HASH_CANONICALIZATION = "utf8_nfc_sorted_keys_compact_json_newline"

#: R5 exact closed enums (from mm_r5.contracts).  COVERAGE_STATES has NO
#: ``not_evaluable``; coverage uses ``unknown`` + ``rate_state=not_evaluable``.
ENUMS: Dict[str, List[str]] = {
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
    "packet_id_grammar": [f"{PACKET_ID_PREFIX}:<audience_replay_content_hash>"],
    "error_code": [
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
        "coverage_not_evaluable_in_coverage_states",
        "schema_version_mismatch", "artifact_set_mismatch",
        "source_path_parse_error", "not_projectable_ok",
        "hash_algorithm_mismatch", "hash_canonicalization_mismatch",
        "hash_dag_edge_mismatch", "receipt_recipe_mismatch",
        "receipt_content_hash_mismatch", "receipt_ref_prefix_mismatch",
        "packet_id_grammar_mismatch", "packet_id_self_edge",
        "sourced_from_unknown_path", "sourced_from_typed_input",
        "lifecycle_domain_drift", "lifecycle_severity_drift",
        "lifecycle_action_drift", "lifecycle_state_mapping_mismatch",
        "lifecycle_marker_identity_mismatch",
        "lifecycle_member_expansion_mismatch",
        "lifecycle_r2_binding_mismatch",
        "current_risk_not_marker_prefix",
        "current_risk_lifecycle_unresolved",
        "current_risk_marker_unresolved",
        "cluster_canonical_ref_mismatch", "cluster_lifecycle_unresolved",
        "resolved_closure_unresolved",
        "current_resolved_plane_overlap",
        "propose_close_resolved", "measure_unit_mismatch",
        "denominator_recipe_mismatch", "rate_policy_mismatch",
        "membership_operator_mismatch", "conservation_operator_mismatch",
        "disabled_path_mismatch", "clinical_domain_not_in_enum",
        "severity_not_in_enum", "unknown_lifecycle_authority",
        "unknown_closure_authority", "unknown_domain_authority",
        "domain_authority_binding_mismatch",
        "center_cell_lifecycle_unresolved",
        "center_cell_domain_drift", "center_cell_severity_drift",
        "center_cell_pattern_upgrade", "center_cell_ref_mismatch",
        "closure_authority_missing", "closure_identity_mismatch",
        "lifecycle_unresolved", "proposed_close_no_resolve",
        "sourced_from_missing", "packet_oracle_failed",
        "challenge_pre_post_identical", "challenge_expected_mismatch",
        "challenge_locator_missing", "packet_assert_failed",
        "source_path_not_in_allowlist", "runtime_validator_prefix_check",
        "low_cluster_not_in_replay", "stale_replay_rejected",
        "manifest_hash_rewrite", "layer_recipe_key_mismatch",
        "change_emission_key_mismatch", "hash_dag_key_mismatch",
        "lifecycle_state_table_mismatch", "cross_object_keys_mismatch",
        "tagged_variant_key_mismatch", "source_binding_key_mismatch",
        "challenge_row_key_mismatch", "mutation_op_mismatch",
        "current_plane_high_mismatch", "current_plane_medium_mismatch",
        "current_plane_low_cluster_mismatch", "current_plane_resolved_mismatch",
        "center_cell_set_mismatch", "center_cell_site_mismatch",
        "center_cell_order_mismatch", "center_cell_classification_mismatch",
        "closure_prior_instance_mismatch", "closure_decision_hash_mismatch",
        "closure_receipt_binding_mismatch", "closure_visibility_binding_mismatch",
        "closure_content_hash_mismatch", "closure_orphan",
        "closure_missing_for_resolved", "closure_ambiguous",
        "current_plane_duplicate_projection", "center_cell_duplicate_member",
    ],
    "acceptance_boundary": [STATUS],
    "center_role": ["individual", "pattern"],
}

#: frozen per-layer measure units (reviewer blocker 6: freeze each layer's
#: measure unit; no union-like prose type).
LAYER_MEASURE_UNITS: Dict[str, str] = {
    "individual_risk": "subject",
    "center_pattern": "subject",
    "affected_subject": "subject",
    "event": "event",
    "affected_site": "site",
    "project_signal": "subject",
    "clue": "event",
    "query": "event",
}

#: module -> source file (relative to ROOT) used for AST field resolution.
MODULE_FILES: Dict[str, str] = {
    "mm_r5.contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py",
    "mm_r4.d09_contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_contracts.py",
    "mm_r4.d09_projection": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_projection.py",
    "mm_r4.d10_contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_contracts.py",
    "mm_r4.d10_projection": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_projection.py",
}

#: D09/D10 typed-input classes that must NEVER be a public source path.
TYPED_INPUT_DENYLIST: Dict[str, List[str]] = {
    "mm_r4.d09_contracts": [
        "D09TypedInput", "D09RunResult", "D09UnitResult", "D09TraceEdge",
        "SubjectRiskMember", "GapMember", "ChangeLedgerMember",
        "Denominator", "Opportunity", "Cutoff", "NumericPolicy",
        "VisibilityDecision", "ExpectedSet", "MutationContext",
        "AntiOverfitVariant", "EvidenceRef", "ScopeBinding",
        "PatternDefinition", "AnalysisWindow", "Stratum", "CoverageStatus",
        "AdmissionGate", "ResolvedAuthorityDecision",
        "MethodComparabilityDecision", "LineageContext", "CenterQueryPolicy",
        "QueryRedundancyDecision", "SourceVerificationRecord",
        "AudienceLexicon", "SurfaceChange",
    ],
    "mm_r4.d10_contracts": [
        "D10TypedInput", "D10EvaluationAuthority",
        "Member", "NumeratorLedger", "MeasureOriginBinding", "Denominator",
        "TimeSegment", "Opportunity", "AnalysisPopulation", "CoverageStatus",
        "CutoffAdvance", "ChangeDecision", "VisibilityDecision",
        "QueryDecision", "AudienceText", "DeepLink", "ModelEvidence",
        "SafetyContext", "EfficacyContext", "RuleHit", "Hotspot",
        "CountLayers", "EvaluationLimits", "NumericPolicy", "MutationContext",
        "AntiOverfitVariant", "EvidenceRef", "SourceRevisionPair",
        "ScopeBinding", "ModeContract", "SignalDefinition", "LegalMatrixRow",
        "AdmissionGate", "ExpectedSet", "AnalysisWindow", "Stratum",
        "ComparisonGate", "WindowPairGate", "SiteLedger", "SurfaceChange",
    ],
    "mm_r4.d09_projection": [],
    "mm_r4.d10_projection": [],
    "mm_r5.contracts": [],
}

#: public projection / receipt / R5 typed classes that MAY be a source.
PUBLIC_ALLOWLIST: Dict[str, List[str]] = {
    "mm_r4.d09_projection": [
        "D09AudienceProjection", "D09ProjectionCountSurface", "D09RiskMarker",
        "D09HotspotProjection", "D09DeepLinkTarget", "D09QueryDraft",
        "D09R2RiskHandoff", "D09ProjectionBundle",
    ],
    "mm_r4.d10_projection": [
        "D10AudienceProjection", "D10ProjectionCountSurface",
        "D10ProjectionVersion", "D10RiskMarker", "D10HotspotProjection",
        "D10DeepLinkTarget", "D10AudiencePart", "D10QueryDraft",
        "D10ChangeSection", "D10CenterPatternRow", "D10TrendSurface",
        "D10WarningMarker", "D10R2RiskHandoff", "D10ProjectProjection",
        "D10ProjectionBundle",
    ],
    "mm_r5.contracts": [
        "R5AuthorityReceipt", "SourceRevisionContentPair",
        "R5CurrentRiskSet", "R5ChangeBand", "R5QuantitativeMeasure",
        "R5CenterMapCell", "R5CenterMapProjection", "R5ProjectionInstance",
        "R5ProjectCockpitProjection",
    ],
}

#: every source path referenced by any recipe/relation, regardless of leaf;
#: ``kind`` is the source_kind and every r4_public/r5_receipt path must
#: resolve to a real dataclass field that is NOT a typed-input class.  These
#: are the hard semantic source paths used by sourced_from relations too.
SOURCE_BINDINGS: List[Dict[str, Any]] = [
    # d09 center-pattern unit leaves
    {"binding_id": "binding.r4.d09.audience.projectable_member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09AudienceProjection.projectable_member_refs",
     "role": "audience_plane"},
    {"binding_id": "binding.r4.d09.audience.evaluation_member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09AudienceProjection.evaluation_member_refs",
     "role": "audience_plane"},
    {"binding_id": "binding.r4.d09.audience.hidden_member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09AudienceProjection.hidden_member_refs",
     "role": "private_integrity_only"},
    {"binding_id": "binding.r4.d09.counts.individual_risk_count",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09ProjectionCountSurface.individual_risk_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d09.counts.center_pattern_count",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09ProjectionCountSurface.center_pattern_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d09.counts.affected_subject_count",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09ProjectionCountSurface.affected_subject_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d09.counts.event_count",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09ProjectionCountSurface.event_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d09.counts.clue_count",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09ProjectionCountSurface.clue_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d09.counts.query_count",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09ProjectionCountSurface.query_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d09.counts.rate_projection_state",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09ProjectionCountSurface.rate_projection_state",
     "role": "rate_leaf"},
    {"binding_id": "binding.r4.d09.marker.marker_id",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09RiskMarker.marker_id",
     "role": "marker_identity"},
    {"binding_id": "binding.r4.d09.marker.public_risk_identity",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09RiskMarker.public_risk_identity",
     "role": "marker_public_identity"},
    {"binding_id": "binding.r4.d09.marker.member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09RiskMarker.member_refs",
     "role": "member_expansion"},
    {"binding_id": "binding.r4.d09.r2.action",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09R2RiskHandoff.action",
     "role": "lifecycle_action"},
    {"binding_id": "binding.r4.d09.r2.handoff_id",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09R2RiskHandoff.handoff_id",
     "role": "lifecycle_handoff_id"},
    {"binding_id": "binding.r4.d09.r2.monitoring_priority",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09R2RiskHandoff.monitoring_priority",
     "role": "lifecycle_severity"},
    {"binding_id": "binding.r4.d09.r2.member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09R2RiskHandoff.member_refs",
     "role": "member_expansion"},
    {"binding_id": "binding.r4.d09.r2.prior_risk_instance_ref",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09R2RiskHandoff.prior_risk_instance_ref",
     "role": "prior_instance_ref"},
    {"binding_id": "binding.r4.d09.r2.prior_public_risk_identity_ref",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09R2RiskHandoff.prior_public_risk_identity_ref",
     "role": "prior_identity_ref"},
    # d10 project unit leaves
    {"binding_id": "binding.r4.d10.audience.projectable_member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10AudienceProjection.projectable_member_refs",
     "role": "audience_plane"},
    {"binding_id": "binding.r4.d10.audience.evaluation_member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10AudienceProjection.evaluation_member_refs",
     "role": "audience_plane"},
    {"binding_id": "binding.r4.d10.audience.hidden_member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10AudienceProjection.hidden_member_refs",
     "role": "private_integrity_only"},
    {"binding_id": "binding.r4.d10.audience.hidden_site_refs",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10AudienceProjection.hidden_site_refs",
     "role": "private_integrity_only"},
    {"binding_id": "binding.r4.d10.audience.projectable_site_refs",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10AudienceProjection.projectable_site_refs",
     "role": "audience_plane"},
    {"binding_id": "binding.r4.d10.counts.individual_risk_count",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.individual_risk_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d10.counts.center_pattern_count",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.center_pattern_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d10.counts.affected_subject_count",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.affected_subject_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d10.counts.event_or_outcome_count",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.event_or_outcome_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d10.counts.affected_site_count",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.affected_site_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d10.counts.project_signal_count",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.project_signal_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d10.counts.clue_count",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.clue_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d10.counts.query_count",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.query_count",
     "role": "count_leaf"},
    {"binding_id": "binding.r4.d10.counts.rate_projection_state",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.rate_projection_state",
     "role": "rate_leaf"},
    {"binding_id": "binding.r4.d10.counts.event_count_disabled",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.event_count_disabled",
     "role": "disabled_path"},
    {"binding_id": "binding.r4.d10.counts.site_count_disabled",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionCountSurface.site_count_disabled",
     "role": "disabled_path"},
    {"binding_id": "binding.r4.d10.version.cutoff_ref",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionVersion.cutoff_ref",
     "role": "cutoff_bound"},
    {"binding_id": "binding.r4.d10.version.source_evaluation_content_identities",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionVersion.source_evaluation_content_identities",
     "role": "evaluation_identity"},
    {"binding_id": "binding.r4.d10.version.project_ref",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionVersion.project_ref",
     "role": "project_identity"},
    {"binding_id": "binding.r4.d10.version.run_ref",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionVersion.run_ref",
     "role": "run_identity"},
    {"binding_id": "binding.r4.d10.version.snapshot_ref",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ProjectionVersion.snapshot_ref",
     "role": "snapshot_identity"},
    {"binding_id": "binding.r4.d10.change_section.change_kind",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ChangeSection.change_kind",
     "role": "change_kind_leaf"},
    {"binding_id": "binding.r4.d10.change_section.change_cause",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ChangeSection.change_cause",
     "role": "change_cause_leaf"},
    {"binding_id": "binding.r4.d10.change_section.fresh_full",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ChangeSection.fresh_full",
     "role": "fresh_full_leaf"},
    {"binding_id": "binding.r4.d10.change_section.replay",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ChangeSection.replay",
     "role": "replay_leaf"},
    {"binding_id": "binding.r4.d10.change_section.analysis_only",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10ChangeSection.analysis_only",
     "role": "analysis_only_leaf"},
    {"binding_id": "binding.r4.d10.marker.marker_id",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10RiskMarker.marker_id",
     "role": "marker_identity"},
    {"binding_id": "binding.r4.d10.marker.public_risk_identity",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10RiskMarker.public_risk_identity",
     "role": "marker_public_identity"},
    {"binding_id": "binding.r4.d10.marker.member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10RiskMarker.member_refs",
     "role": "member_expansion"},
    {"binding_id": "binding.r4.d10.r2.action",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10R2RiskHandoff.action",
     "role": "lifecycle_action"},
    {"binding_id": "binding.r4.d10.r2.handoff_id",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10R2RiskHandoff.handoff_id",
     "role": "lifecycle_handoff_id"},
    {"binding_id": "binding.r4.d10.r2.monitoring_priority",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10R2RiskHandoff.monitoring_priority",
     "role": "lifecycle_severity"},
    {"binding_id": "binding.r4.d10.r2.member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10R2RiskHandoff.member_refs",
     "role": "member_expansion"},
    {"binding_id": "binding.r4.d10.r2.prior_risk_instance_ref",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10R2RiskHandoff.prior_risk_instance_ref",
     "role": "prior_instance_ref"},
    {"binding_id": "binding.r4.d10.center.row.site_ref",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10CenterPatternRow.site_ref",
     "role": "center_site"},
    {"binding_id": "binding.r4.d10.center.row.coverage_state",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10CenterPatternRow.coverage_state",
     "role": "center_coverage"},
    {"binding_id": "binding.r4.d10.center.row.denominator_value",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10CenterPatternRow.denominator_value",
     "role": "center_denominator"},
    {"binding_id": "binding.r4.d10.center.row.affected_subject_count",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10CenterPatternRow.affected_subject_count",
     "role": "center_count"},
    # D09/D10 hotspot member bindings are intentionally type-specific.  D09
    # exposes separate risk/gap member fields; D10 exposes one member_refs
    # field.  The verifier resolves these against the real dataclass fields
    # and never aliases the two shapes.
    {"binding_id": "binding.r4.d09.hotspot.member_risk_refs",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09HotspotProjection.member_risk_refs",
     "role": "center_member_binding"},
    {"binding_id": "binding.r4.d09.hotspot.gap_member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d09_projection:D09HotspotProjection.gap_member_refs",
     "role": "center_member_binding"},
    {"binding_id": "binding.r4.d10.hotspot.member_refs",
     "kind": "r4_public",
     "target": "mm_r4.d10_projection:D10HotspotProjection.member_refs",
     "role": "center_member_binding"},
    # receipts / aggregate
    {"binding_id": "binding.receipt.audience_contract_id",
     "kind": "r5_receipt",
     "target": "mm_r5.contracts:R5AuthorityReceipt.audience_contract_id",
     "role": "receipt_leaf"},
    {"binding_id": "binding.receipt.public_projection_content_hash",
     "kind": "r5_receipt",
     "target": "mm_r5.contracts:R5AuthorityReceipt.public_projection_content_hash",
     "role": "receipt_content"},
    {"binding_id": "binding.receipt.visibility_decision_hash",
     "kind": "r5_receipt",
     "target": "mm_r5.contracts:R5AuthorityReceipt.visibility_decision_hash",
     "role": "receipt_visibility"},
    {"binding_id": "binding.receipt.source_revision_content_pairs",
     "kind": "r5_receipt",
     "target": "mm_r5.contracts:R5AuthorityReceipt.source_revision_content_pairs",
     "role": "receipt_sources"},
    {"binding_id": "binding.receipt.project_ref",
     "kind": "r5_receipt",
     "target": "mm_r5.contracts:R5AuthorityReceipt.project_ref",
     "role": "project_identity"},
    {"binding_id": "binding.receipt.run_ref",
     "kind": "r5_receipt",
     "target": "mm_r5.contracts:R5AuthorityReceipt.run_ref",
     "role": "run_identity"},
    {"binding_id": "binding.receipt.snapshot_ref",
     "kind": "r5_receipt",
     "target": "mm_r5.contracts:R5AuthorityReceipt.snapshot_ref",
     "role": "snapshot_identity"},
    {"binding_id": "binding.receipt.cutoff_ref",
     "kind": "r5_receipt",
     "target": "mm_r5.contracts:R5AuthorityReceipt.cutoff_ref",
     "role": "cutoff_bound"},
    # named supplemental authorities (offline-test only)
    {"binding_id": "binding.supplemental.denominator_authority",
     "kind": "named_supplemental",
     "target": "named_supplemental:denominator_authority",
     "role": "supplemental_authority"},
    {"binding_id": "binding.supplemental.layer_membership_authority",
     "kind": "named_supplemental",
     "target": "named_supplemental:layer_membership_authority",
     "role": "supplemental_authority"},
    {"binding_id": "binding.supplemental.cutoff_authority",
     "kind": "named_supplemental",
     "target": "named_supplemental:cutoff_authority",
     "role": "supplemental_authority"},
    {"binding_id": "binding.supplemental.evaluation_limit_authority",
     "kind": "named_supplemental",
     "target": "named_supplemental:evaluation_limit_authority",
     "role": "supplemental_authority"},
    {"binding_id": "binding.supplemental.coverage_authority",
     "kind": "named_supplemental",
     "target": "named_supplemental:coverage_authority",
     "role": "supplemental_authority"},
    {"binding_id": "binding.supplemental.change_cause_mixture_authority",
     "kind": "named_supplemental",
     "target": "named_supplemental:change_cause_mixture_authority",
     "role": "supplemental_authority"},
    {"binding_id": "binding.supplemental.clinical_domain_authority",
     "kind": "named_supplemental",
     "target": "named_supplemental:clinical_domain_authority",
     "role": "supplemental_authority"},
    {"binding_id": "binding.supplemental.current_risk_marker_identity",
     "kind": "named_supplemental",
     "target": "named_supplemental:risk_lifecycle_authority",
     "role": "current_risk_marker_identity"},
    # packet fixture bindings used by the packet oracle (synthetic offline
    # fixture ONLY; never a real public-source claim).
    {"binding_id": "binding.fixture.unit.d09.marker.marker_id",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d09.risk_marker.marker_id",
     "role": "marker_identity"},
    {"binding_id": "binding.fixture.unit.d09.marker.member_refs",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d09.risk_marker.member_refs",
     "role": "member_expansion"},
    {"binding_id": "binding.fixture.unit.d09.r2.action",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d09.r2_handoff.action",
     "role": "lifecycle_action"},
    {"binding_id": "binding.fixture.unit.d09.r2.handoff_id",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d09.r2_handoff.handoff_id",
     "role": "lifecycle_handoff_id"},
    {"binding_id": "binding.fixture.unit.d09.r2.monitoring_priority",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d09.r2_handoff.monitoring_priority",
     "role": "lifecycle_severity"},
    {"binding_id": "binding.fixture.unit.d09.clinical_domain",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d09.clinical_domain",
     "role": "clinical_domain"},
    {"binding_id": "binding.fixture.unit.d10.marker.marker_id",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d10.risk_marker.marker_id",
     "role": "marker_identity"},
    {"binding_id": "binding.fixture.unit.d10.marker.member_refs",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d10.risk_marker.member_refs",
     "role": "member_expansion"},
    {"binding_id": "binding.fixture.unit.d10.r2.action",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d10.r2_handoff.action",
     "role": "lifecycle_action"},
    {"binding_id": "binding.fixture.unit.d10.r2.handoff_id",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d10.r2_handoff.handoff_id",
     "role": "lifecycle_handoff_id"},
    {"binding_id": "binding.fixture.unit.d10.r2.monitoring_priority",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d10.r2_handoff.monitoring_priority",
     "role": "lifecycle_severity"},
    {"binding_id": "binding.fixture.unit.d10.clinical_domain",
     "kind": "packet_fixture",
     "target": "packet_fixture:unit.d10.clinical_domain",
     "role": "clinical_domain"},
]

#: source matrix: per-audience-leaf provenance.  Kept as the audit trail of
#: which audience leaf is sourced from which public/receipt/supplemental
#: authority; every r4_public/r5_receipt path is resolved by the verifier.
SOURCE_MATRIX: List[Dict[str, str]] = [
    {"leaf": binding["binding_id"],
     "source_kind": binding["kind"],
     "path": binding["target"],
     "provenance": binding["role"]}
    for binding in SOURCE_BINDINGS
]

#: frozen numerator-layer recipes (reviewer blocker 2/5) -- fully structured,
#: no prose union types.  Every leaf is machine-checked.
LAYER_RECIPES: List[Dict[str, Any]] = [
    {"layer": "individual_risk",
     "numerator_unit": "risk_member",
     "measure_unit": LAYER_MEASURE_UNITS["individual_risk"],
     "source_count_paths": [
         "mm_r4.d10_projection:D10ProjectionCountSurface.individual_risk_count",
         "mm_r4.d09_projection:D09ProjectionCountSurface.individual_risk_count"],
     "membership_sources": [
         "mm_r4.d10_projection:D10RiskMarker.member_refs",
         "mm_r4.d09_projection:D09RiskMarker.member_refs"],
     "membership_operator": "filter_marker_member_refs",
     "denominator_policy": "applicable",
     "rate_policy": "permitted_qualified_not_evaluable",
     "conservation_operator": "count_equals_sorted_unique_length",
     "conservation_expr": "count == len(projectable individual_risk members) when membership_state=projectable",
     "disabled_path_policy": "no_disabled_path"},
    {"layer": "center_pattern",
     "numerator_unit": "center_pattern_member",
     "measure_unit": LAYER_MEASURE_UNITS["center_pattern"],
     "source_count_paths": [
         "mm_r4.d10_projection:D10ProjectionCountSurface.center_pattern_count",
         "mm_r4.d09_projection:D09ProjectionCountSurface.center_pattern_count"],
     "membership_sources": [
         "mm_r4.d10_projection:D10RiskMarker.member_refs",
         "mm_r4.d09_projection:D09RiskMarker.member_refs"],
     "membership_operator": "filter_marker_member_refs",
     "denominator_policy": "applicable",
     "rate_policy": "permitted_qualified_not_evaluable",
     "conservation_operator": "count_equals_sorted_unique_length",
     "conservation_expr": "count == len(projectable center_pattern members) when membership_state=projectable",
     "disabled_path_policy": "no_disabled_path"},
    {"layer": "affected_subject",
     "numerator_unit": "unique_subject",
     "measure_unit": LAYER_MEASURE_UNITS["affected_subject"],
     "source_count_paths": [
         "mm_r4.d10_projection:D10ProjectionCountSurface.affected_subject_count",
         "mm_r4.d09_projection:D09ProjectionCountSurface.affected_subject_count"],
     "membership_sources": ["named_supplemental:layer_membership_authority"],
     "membership_operator": "unique_subject_stable_ids",
     "denominator_policy": "applicable",
     "rate_policy": "permitted_qualified_not_evaluable",
     "conservation_operator": "count_equals_unique_subject_length",
     "conservation_expr": "count == len(unique projectable subject ids) when membership_state=projectable",
     "disabled_path_policy": "no_disabled_path"},
    {"layer": "event",
     "numerator_unit": "event",
     "measure_unit": LAYER_MEASURE_UNITS["event"],
     "source_count_paths": [
         "mm_r4.d10_projection:D10ProjectionCountSurface.event_or_outcome_count",
         "mm_r4.d09_projection:D09ProjectionCountSurface.event_count"],
     "membership_sources": ["named_supplemental:layer_membership_authority"],
     "membership_operator": "exact_supplemental_refs",
     "denominator_policy": "applicable",
     "rate_policy": "qualified_not_evaluable",
     "conservation_operator": "count_equals_sorted_unique_length",
     "conservation_expr": "count == len(projectable event refs) when projectable; suppressed to 0 via not_projectable supplemental when event_count_disabled",
     "disabled_path_policy": "event_count_disabled"},
    {"layer": "affected_site",
     "numerator_unit": "site",
     "measure_unit": LAYER_MEASURE_UNITS["affected_site"],
     "source_count_paths": [
         "mm_r4.d10_projection:D10ProjectionCountSurface.affected_site_count"],
     "membership_sources": ["named_supplemental:layer_membership_authority"],
     "membership_operator": "exact_supplemental_refs",
     "denominator_policy": "applicable",
     "rate_policy": "permitted_qualified_not_evaluable",
     "conservation_operator": "count_equals_sorted_unique_length",
     "conservation_expr": "count == len(projectable site refs) when projectable; suppressed to 0 via not_projectable supplemental when site_count_disabled",
     "disabled_path_policy": "site_count_disabled"},
    {"layer": "project_signal",
     "numerator_unit": "project_signal",
     "measure_unit": LAYER_MEASURE_UNITS["project_signal"],
     "source_count_paths": [
         "mm_r4.d10_projection:D10ProjectionCountSurface.project_signal_count"],
     "membership_sources": [
         "named_supplemental:layer_membership_authority",
         "mm_r4.d10_projection:D10RiskMarker.member_refs"],
     "membership_operator": "filter_marker_member_refs",
     "denominator_policy": "not_applicable",
     "rate_policy": "not_evaluable_only",
     "conservation_operator": "count_equals_sorted_unique_length",
     "conservation_expr": "count == len(projectable project_signal refs) when projectable; rate_state=not_evaluable (no project-level denominator)",
     "disabled_path_policy": "no_disabled_path"},
    {"layer": "clue",
     "numerator_unit": "clue",
     "measure_unit": LAYER_MEASURE_UNITS["clue"],
     "source_count_paths": [
         "mm_r4.d10_projection:D10ProjectionCountSurface.clue_count",
         "mm_r4.d09_projection:D09ProjectionCountSurface.clue_count"],
     "membership_sources": ["named_supplemental:layer_membership_authority"],
     "membership_operator": "exact_supplemental_refs",
     "denominator_policy": "not_applicable",
     "rate_policy": "not_evaluable_only",
     "conservation_operator": "non_expandable_requires_not_projectable",
     "conservation_expr": "count == len(projectable clue refs) when projectable; else require not_projectable supplemental record",
     "disabled_path_policy": "no_disabled_path"},
    {"layer": "query",
     "numerator_unit": "query_draft",
     "measure_unit": LAYER_MEASURE_UNITS["query"],
     "source_count_paths": [
         "mm_r4.d10_projection:D10ProjectionCountSurface.query_count",
         "mm_r4.d09_projection:D09ProjectionCountSurface.query_count"],
     "membership_sources": ["named_supplemental:layer_membership_authority"],
     "membership_operator": "exact_supplemental_refs",
     "denominator_policy": "not_applicable",
     "rate_policy": "not_evaluable_only",
     "conservation_operator": "non_expandable_requires_not_projectable",
     "conservation_expr": "count == len(projectable query refs) when projectable; else require not_projectable supplemental record",
     "disabled_path_policy": "no_disabled_path"},
]

#: frozen change-band emission table (reviewer blocker 4/6) -- structured,
#: with emit_when_identity_available and exact source object fields.
CHANGE_EMISSION_TABLE: List[Dict[str, Any]] = [
    {"change_kind": "initial_current",
     "marker_present": "optional",
     "prior_identity": "none",
     "prior_ref": "none",
     "r2_action": "create",
     "emit_when_identity_available": False,
     "source_objects": ["D10ChangeSection.fresh_full|replay",
                        "D09ProjectionBundle"],
     "lifecycle_state_effect": "current",
     "fail_closed": ["marker_required_for_change_kind"]},
    {"change_kind": "new",
     "marker_present": "required",
     "prior_identity": "none",
     "prior_ref": "optional",
     "r2_action": "create",
     "emit_when_identity_available": False,
     "source_objects": ["D10ChangeSection.new", "D10R2RiskHandoff.create"],
     "lifecycle_state_effect": "current",
     "fail_closed": ["marker_required_for_change_kind"]},
    {"change_kind": "upgraded",
     "marker_present": "required",
     "prior_identity": "required",
     "prior_ref": "required",
     "r2_action": "continue",
     "emit_when_identity_available": True,
     "source_objects": ["D10ChangeSection.upgraded",
                        "D10R2RiskHandoff.continue"],
     "lifecycle_state_effect": "current",
     "fail_closed": ["marker_required_for_change_kind",
                     "prior_identity_required", "prior_ref_required"]},
    {"change_kind": "continued",
     "marker_present": "required",
     "prior_identity": "required",
     "prior_ref": "required",
     "r2_action": "continue",
     "emit_when_identity_available": True,
     "source_objects": ["D10ChangeSection.continued",
                        "D10R2RiskHandoff.continue"],
     "lifecycle_state_effect": "current",
     "fail_closed": ["marker_required_for_change_kind",
                     "prior_identity_required", "prior_ref_required"]},
    {"change_kind": "downgraded",
     "marker_present": "required",
     "prior_identity": "required",
     "prior_ref": "required",
     "r2_action": "continue",
     "emit_when_identity_available": True,
     "source_objects": ["D10ChangeSection.downgraded",
                        "D10R2RiskHandoff.continue"],
     "lifecycle_state_effect": "current",
     "fail_closed": ["marker_required_for_change_kind",
                     "prior_identity_required", "prior_ref_required"]},
    {"change_kind": "resolved",
     "marker_present": "optional",
     "prior_identity": "required",
     "prior_ref": "required",
     "r2_action": "closure_authority",
     "emit_when_identity_available": True,
     "source_objects": ["R5S3ClosureAuthority",
                        "D10R2RiskHandoff", "D09R2RiskHandoff"],
     "lifecycle_state_effect": "resolved",
     "fail_closed": ["resolved_without_lifecycle_authority",
                     "prior_identity_required", "prior_ref_required"]},
    {"change_kind": "reopened",
     "marker_present": "required",
     "prior_identity": "required",
     "prior_ref": "required",
     "r2_action": "continue",
     "emit_when_identity_available": True,
     "source_objects": ["D10ChangeSection.reopened",
                        "D10R2RiskHandoff.continue"],
     "lifecycle_state_effect": "current",
     "fail_closed": ["marker_required_for_change_kind",
                     "prior_identity_required", "prior_ref_required"]},
    {"change_kind": "superseded",
     "marker_present": "optional",
     "prior_identity": "required",
     "prior_ref": "required",
     "r2_action": "supersede",
     "emit_when_identity_available": True,
     "source_objects": ["D09/D10 lineage supersede",
                        "D09R2RiskHandoff.supersede"],
     "lifecycle_state_effect": "superseded",
     "fail_closed": ["prior_identity_required", "prior_ref_required"]},
    {"change_kind": "not_evaluable",
     "marker_present": "forbidden",
     "prior_identity": "n/a",
     "prior_ref": "optional",
     "r2_action": "none",
     "emit_when_identity_available": False,
     "source_objects": ["D10ChangeSection.not_evaluable"],
     "lifecycle_state_effect": "no_band",
     "fail_closed": []},
    {"change_kind": "not_comparable",
     "marker_present": "forbidden",
     "prior_identity": "n/a",
     "prior_ref": "optional",
     "r2_action": "none",
     "emit_when_identity_available": False,
     "source_objects": ["D10ChangeSection.not_comparable",
                        "analysis_only"],
     "lifecycle_state_effect": "no_band",
     "fail_closed": []},
]

#: lifecycle state mapping (reviewer blocker 3): create/continue/update/
#: reopen => current; supersede => superseded; propose_close stays
#: current/proposed-close and MUST NOT resolve; resolved requires closure.
LIFECYCLE_STATE_TABLE: List[Dict[str, Any]] = [
    {"action": "create", "state": "current", "closure_allowed": False},
    {"action": "continue", "state": "current", "closure_allowed": False},
    {"action": "update", "state": "current", "closure_allowed": False},
    {"action": "reopen", "state": "current", "closure_allowed": False},
    {"action": "supersede", "state": "superseded", "closure_allowed": False},
    {"action": "propose_close", "state": "proposed_close",
     "closure_allowed": False},
]

#: cross-object invariants (machine-checkable predicates).
INVARIANTS: List[Dict[str, Any]] = [
    {"invariant_id": "synthetic_offline_test_only",
     "error_code": "authority_scope_violation",
     "predicate": "authority_mode equals the frozen literal synthetic_offline_test_only and the packet cannot grant clinical truth, real-project, model, product, production or security eligibility"},
    {"invariant_id": "typed_input_not_promoted",
     "error_code": "typed_input_leaf_promoted",
     "predicate": "every audience leaf source resolves into a public projection class, an R5 receipt, a named supplemental authority or a packet fixture path; no source path resolves into any D09/D10 typed-input class"},
    {"invariant_id": "aggregate_receipt_set_identity",
     "error_code": "aggregate_identity_mismatch",
     "predicate": "all authority units share the same project/run/snapshot/cutoff/audience_contract; current_risk_set.authority_receipt_ref equals the aggregate receipt-set identity hash over sorted unique unit receipt content hashes and risk marker identity hashes"},
    {"invariant_id": "current_risk_marker_identities_only",
     "error_code": "raw_member_as_current_risk_ref",
     "predicate": "current-risk high/medium/low/resolved refs reference only d09_marker:/d10_marker: public risk marker identities; raw member refs are expansion-only and never a current-risk identity"},
    {"invariant_id": "tagged_variant_payload_exact",
     "error_code": "tagged_variant_payload_mismatch",
     "predicate": "R5S3AuthorityUnitTagged.variant_kind is a closed enum; d09_center_pattern_unit carries exactly the D09 public objects and d10_project_unit exactly the D10 public objects; cross-variant payload is rejected"},
    {"invariant_id": "private_public_hash_separation",
     "error_code": "hidden_leaf_in_audience_hash",
     "predicate": "packet_integrity_hash covers all leaves including hidden refs; audience_replay_content_hash and every audience content_hash cover only projectable public leaves; a hidden-only mutation changes packet_integrity_hash and leaves every audience payload/hash identical"},
    {"invariant_id": "layer_recipes_complete",
     "error_code": "layer_recipe_missing",
     "predicate": "exactly the eight closed numerator kinds each have one frozen structured layer recipe with numerator unit, measure unit, source count paths, membership sources/operator, denominator policy, rate policy, conservation operator/expr and disabled-path policy"},
    {"invariant_id": "layer_counts_never_summed",
     "error_code": "not_projectable_supplemental_missing",
     "predicate": "the eight count layers are conserved separately and never summed; a nonzero count with non-expandable refs requires a named supplemental record with membership_state=not_projectable; empty refs alone are insufficient"},
    {"invariant_id": "change_emission_complete",
     "error_code": "change_emission_missing",
     "predicate": "every closed change kind has a frozen emission row with marker present/absent, prior identity/ref requirement, R2 action, emit_when_identity_available and exact source objects; resolved never inferred from D10ChangeSection alone; mixed D10 cause fails closed"},
    {"invariant_id": "coverage_enum_no_not_evaluable",
     "error_code": "invalid_coverage_enum",
     "predicate": "COVERAGE_STATES is exactly complete/partial/truncated/unknown/not_applicable and never contains not_evaluable; non-evaluable coverage uses unknown plus rate_state=not_evaluable"},
    {"invariant_id": "hash_dag_acyclic",
     "error_code": "hash_recipe_cycle",
     "predicate": "the hash graph is acyclic: packet_integrity_hash excludes packet_id and every hash field it depends on; audience_replay_content_hash covers the complete audience payload including low clusters; packet_id depends on audience_replay_content_hash only and never the reverse; no root content_hash"},
    {"invariant_id": "receipt_content_hash_recipe",
     "error_code": "receipt_content_hash_mismatch",
     "predicate": "receipt_content_hash is the canonical SHA-256 of the complete R5AuthorityReceipt and authority_receipt_ref equals 'receipt:' + receipt_content_hash"},
    {"invariant_id": "packet_id_grammar",
     "error_code": "packet_id_grammar_mismatch",
     "predicate": "packet_id is exactly 'r5-s3-contract:' + audience_replay_content_hash (single colon grammar, no other characters)"},
    {"invariant_id": "challenge_registry_integrity",
     "error_code": "challenge_duplicate_id",
     "predicate": "every challenge row has a unique case_id, an executable mutation whose pre/post canonical bytes differ, an exact expected typed outcome/error code, an exact expected projection, exact hash relation, and a real pytest test locator"},
    {"invariant_id": "center_map_no_ranking",
     "error_code": "schema_key_mismatch",
     "predicate": "the center-map schema and audience outputs contain no score/rank/top-N or punitive ordinal field; stable_site_order is NFC-stable site identity ascending only"},
    {"invariant_id": "hash_recipe_no_hidden_in_public",
     "error_code": "hidden_leaf_in_audience_hash",
     "predicate": "no public audience hash recipe includes hidden_member_refs/hidden_site_refs or any private integrity leaf"},
]

#: forbidden semantic branches.
FORBIDDEN_SEMANTIC_BRANCHES: List[str] = [
    "project_id", "case_id", "fixture_id", "test_id", "oracle",
    "mutation_class", "nearest_subject_site_risk_source",
    "single_case_to_center_pattern", "counts_summed_across_layers",
    "hidden_or_unknown_as_zero", "resolved_inferred_from_change_section",
    "mixed_cause_first_reason", "member_ref_as_current_risk_identity",
    "typed_input_leaf_as_public_authority", "rank_topn_punitive_ordinal",
    "recompute_medical_numerator_denominator",
    "nearest_visit_date_adhesion",
]

#: challenge registry categories -> exact row counts (must sum to 60).
CHALLENGE_CATEGORIES: Dict[str, int] = {
    "typed_input_not_promoted": 6,
    "aggregate_receipt_set": 6,
    "tagged_d09_d10_variants": 6,
    "hash_separation_private_public": 6,
    "layer_recipes": 10,
    "change_emission": 12,
    "machine_contract": 8,
    "done_gates_acceptance": 6,
}

# Each challenge row has a frozen projection outcome.  This is deliberately
# keyed by case id rather than inferred from the broad accept/reject label so
# a coordination re-sign cannot turn, for example, R5S3C-025 from ``emitted``
# into ``unchanged`` and still pass an accept oracle.
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


def _nfc(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(item) for item in value]
    if isinstance(value, dict):
        return {_nfc(k): _nfc(v) for k, v in value.items()}
    return value


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(_nfc(value), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _field(type_name: str, *, cardinality: str = "one",
           nullable: bool = False, constraints: Tuple[str, ...] = ()) -> Dict[str, Any]:
    descriptor: Dict[str, Any] = {
        "type": type_name, "cardinality": cardinality, "nullable": nullable,
    }
    if constraints:
        descriptor["constraints"] = list(constraints)
    return descriptor


def _binding_descriptor(binding: Dict[str, Any]) -> Dict[str, Any]:
    return {"binding_id": binding["binding_id"], "kind": binding["kind"],
            "target": binding["target"], "role": binding["role"]}


# ---------------------------------------------------------------------------
# packet_schema.json
# ---------------------------------------------------------------------------


HASH_DAG: Dict[str, Dict[str, Any]] = {
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


def _hash_dag() -> Dict[str, Dict[str, Any]]:
    return {k: dict(v) for k, v in HASH_DAG.items()}


def build_schema() -> Dict[str, Any]:
    hash_dag = _hash_dag()
    objects: Dict[str, Dict[str, Any]] = {
        "R5S3AuthorityPacket": {
            "packet_id": _field("str", constraints=["packet_id_grammar:r5-s3-contract:<audience_replay_content_hash>"]),
            "schema": _field("str", constraints=["equals:medical-monitoring-r5-s3-packet-schema-v0.2"]),
            "status": _field("str", constraints=["equals:R5_S3_CONTRACT_READY_FOR_REVIEW"]),
            "authority_mode": _field("str", constraints=["equals:synthetic_offline_test_only"]),
            "authority_units": _field("R5S3AuthorityUnitTagged", cardinality="many", constraints=["min_items:1", "sorted_unique_by:unit_ref"]),
            "aggregate_receipt_set": _field("R5S3AggregateReceiptSetIdentity", constraints=["required"]),
            "risk_lifecycle_authorities": _field("R5S3RiskLifecycleAuthority", cardinality="many", constraints=["sorted_unique_by:marker_identity_ref", "min_items:0"]),
            "closure_authorities": _field("R5S3ClosureAuthority", cardinality="many", constraints=["sorted_unique_by:closure_authority_id", "min_items:0"]),
            "clinical_domain_authorities": _field("R5S3ClinicalDomainAuthority", cardinality="many", constraints=["sorted_unique_by:authority_id", "min_items:0"]),
            "denominator_authorities": _field("R5S3DenominatorAuthority", cardinality="many", constraints=["sorted_unique_by:authority_id", "min_items:0"]),
            "layer_membership_authorities": _field("R5S3LayerMembershipAuthority", cardinality="many", constraints=["sorted_unique_by:authority_id", "min_items:0"]),
            "cutoff_authorities": _field("R5S3CutoffAuthority", cardinality="many", constraints=["sorted_unique_by:authority_id", "min_items:0"]),
            "evaluation_limit_authorities": _field("R5S3EvaluationLimitAuthority", cardinality="many", constraints=["sorted_unique_by:authority_id", "min_items:0"]),
            "coverage_authorities": _field("R5S3CoverageAuthority", cardinality="many", constraints=["sorted_unique_by:authority_id", "min_items:0"]),
            "change_cause_mixture_authorities": _field("R5S3ChangeCauseMixtureAuthority", cardinality="many", constraints=["sorted_unique_by:authority_id", "min_items:0"]),
            "audience_payload": _field("R5S3AudiencePayload", constraints=["required"]),
            "audience_replay_content_hash": _field("sha256", constraints=["canonical_sha256_of:audience_payload"]),
            "packet_integrity_hash": _field("sha256", constraints=["canonical_sha256_of_all_leaves_excluding_self_and_dependencies"]),
        },
        "R5S3AuthorityUnitTagged": {
            "unit_ref": _field("str"),
            "variant_kind": _field("enum:tagged_variant_kind"),
            "authority_receipt": _field("import:R5AuthorityReceipt", constraints=["required"]),
            "receipt_content_hash": _field("sha256", constraints=["canonical_sha256_of:authority_receipt"]),
            "projectable_member_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
            "hidden_member_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0", "private_integrity_only"]),
            "hidden_site_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0", "private_integrity_only"]),
            "source_unit_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
            "d09_variant_payload": _field("R5S3D09CenterPatternUnit", nullable=True, constraints=["required_when:variant_kind=d09_center_pattern_unit", "forbidden_when:variant_kind=d10_project_unit"]),
            "d10_variant_payload": _field("R5S3D10ProjectUnit", nullable=True, constraints=["required_when:variant_kind=d10_project_unit", "forbidden_when:variant_kind=d09_center_pattern_unit"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3D09CenterPatternUnit": {
            "audience": _field("import:D09AudienceProjection", constraints=["required"]),
            "counts": _field("import:D09ProjectionCountSurface", constraints=["required"]),
            "risk_marker": _field("import:D09RiskMarker", nullable=True, constraints=["optional"]),
            "r2_handoff": _field("import:D09R2RiskHandoff", nullable=True, constraints=["optional"]),
            "hotspots": _field("import:D09HotspotProjection", cardinality="many", constraints=["min_items:0", "sorted_unique_by:projection_id"]),
            "clinical_domain_authority_ref": _field("str", constraints=["domain_authority_ref_required"]),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
        },
        "R5S3D10ProjectUnit": {
            "audience": _field("import:D10AudienceProjection", constraints=["required"]),
            "counts": _field("import:D10ProjectionCountSurface", constraints=["required"]),
            "version": _field("import:D10ProjectionVersion", constraints=["required"]),
            "change_section": _field("import:D10ChangeSection", constraints=["required"]),
            "center_distribution": _field("import:D10CenterPatternRow", cardinality="many", constraints=["min_items:0", "sorted_unique_by:site_ref"]),
            "risk_marker": _field("import:D10RiskMarker", nullable=True, constraints=["optional"]),
            "r2_handoff": _field("import:D10R2RiskHandoff", nullable=True, constraints=["optional"]),
            "hotspots": _field("import:D10HotspotProjection", cardinality="many", constraints=["min_items:0", "sorted_unique_by:projection_id"]),
            "clinical_domain_authority_ref": _field("str", constraints=["domain_authority_ref_required"]),
            "project_projection": _field("import:D10ProjectProjection", constraints=["required"]),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
        },
        "R5S3AggregateReceiptSetIdentity": {
            "aggregate_id": _field("str", constraints=["equals_prefix_plus_hash:aggregate:"]),
            "unit_receipt_refs": _field("str", cardinality="many", constraints=["min_items:1", "sorted_unique", "receipt_ref_prefix"]),
            "risk_marker_identity_hashes": _field("sha256", cardinality="many", constraints=["min_items:0", "sorted_unique"]),
            "project_ref": _field("str"),
            "run_ref": _field("str"),
            "snapshot_ref": _field("str"),
            "cutoff_ref": _field("str", nullable=True),
            "audience_contract_id": _field("str"),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3RiskLifecycleAuthority": {
            "authority_id": _field("str"),
            "marker_kind": _field("enum:marker_kind"),
            "marker_identity_ref": _field("str", constraints=["current_risk_marker_prefix"]),
            "marker_id": _field("str"),
            "marker_content_hash": _field("sha256"),
            "receipt_hash": _field("sha256"),
            "receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "visibility_decision_id": _field("str"),
            "visibility_decision_hash": _field("sha256"),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
            "clinical_domain_ref": _field("str", constraints=["domain_authority_ref_required"]),
            "severity": _field("enum:severity"),
            "lifecycle_state": _field("enum:lifecycle_state"),
            "lifecycle_action": _field("enum:lifecycle_action"),
            "r2_handoff_id": _field("str"),
            "r2_handoff_ref": _field("str"),
            "member_expansion_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
            "closure_authority_ref": _field("str", nullable=True, constraints=["required_when:lifecycle_state=resolved"]),
            "prior_marker_identity_ref": _field("str", nullable=True, constraints=["optional"]),
            "offline_test_only": _field("bool", constraints=["equals:true"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3ClosureAuthority": {
            "closure_authority_id": _field("str"),
            "closure_decision_id": _field("str"),
            "closure_decision_hash": _field("sha256"),
            "prior_public_risk_identity_ref": _field("str", constraints=["current_risk_marker_prefix"]),
            "prior_risk_instance_ref": _field("str"),
            "receipt_hash": _field("sha256"),
            "receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "visibility_decision_id": _field("str"),
            "visibility_decision_hash": _field("sha256"),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
            "decision_kind": _field("enum:closure_decision_kind"),
            "offline_test_only": _field("bool", constraints=["equals:true"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3ClinicalDomainAuthority": {
            "authority_id": _field("str"),
            "clinical_domain": _field("enum:domain"),
            "receipt_hash": _field("sha256"),
            "receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "visibility_decision_id": _field("str"),
            "visibility_decision_hash": _field("sha256"),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
            "offline_test_only": _field("bool", constraints=["equals:true"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3DenominatorAuthority": {
            "authority_id": _field("str"),
            "denominator_kind": _field("enum:denominator_kind"),
            "denominator_state": _field("enum:denominator_state"),
            "denominator_value": _field("num", nullable=True),
            "measure_unit": _field("enum:measure_unit"),
            "member_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
            "exclusion_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
            "receipt_hash": _field("sha256"),
            "receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "visibility_decision_id": _field("str"),
            "visibility_decision_hash": _field("sha256"),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
            "offline_test_only": _field("bool", constraints=["equals:true"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3LayerMembershipAuthority": {
            "authority_id": _field("str"),
            "layer": _field("enum:numerator_kind"),
            "membership_state": _field("enum:membership_state"),
            "member_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
            "source_count_value": _field("num"),
            "source_count_ref": _field("str", constraints=["count_ref_required"]),
            "disabled_state": _field("str", constraints=["disabled_state_closed"]),
            "receipt_hash": _field("sha256"),
            "receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "visibility_decision_id": _field("str"),
            "visibility_decision_hash": _field("sha256"),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
            "offline_test_only": _field("bool", constraints=["equals:true"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3CutoffAuthority": {
            "authority_id": _field("str"),
            "cutoff_ref": _field("str", nullable=True),
            "receipt_hash": _field("sha256"),
            "receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "visibility_decision_id": _field("str"),
            "visibility_decision_hash": _field("sha256"),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
            "offline_test_only": _field("bool", constraints=["equals:true"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3EvaluationLimitAuthority": {
            "authority_id": _field("str"),
            "evaluation_limit_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
            "evaluation_limit_values": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
            "receipt_hash": _field("sha256"),
            "receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "visibility_decision_id": _field("str"),
            "visibility_decision_hash": _field("sha256"),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
            "offline_test_only": _field("bool", constraints=["equals:true"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3CoverageAuthority": {
            "authority_id": _field("str"),
            "coverage_state": _field("enum:coverage_state"),
            "receipt_hash": _field("sha256"),
            "receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "visibility_decision_id": _field("str"),
            "visibility_decision_hash": _field("sha256"),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
            "offline_test_only": _field("bool", constraints=["equals:true"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3ChangeCauseMixtureAuthority": {
            "authority_id": _field("str"),
            "causes": _field("enum:change_cause", cardinality="many", constraints=["min_items:2", "sorted_unique"]),
            "receipt_hash": _field("sha256"),
            "receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "visibility_decision_id": _field("str"),
            "visibility_decision_hash": _field("sha256"),
            "source_revision_content_pairs": _field("import:SourceRevisionContentPair", cardinality="many", constraints=["min_items:1", "sorted_unique_by:revision_id"]),
            "offline_test_only": _field("bool", constraints=["equals:true"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3LowRiskCluster": {
            "cluster_ref": _field("str", constraints=["equals_prefix_plus_hash:cluster:"]),
            "authority_receipt_ref": _field("str", constraints=["receipt_ref_prefix"]),
            "domain": _field("enum:domain"),
            "site_ref": _field("str"),
            "member_refs": _field("str", cardinality="many", constraints=["min_items:1", "sorted_unique", "current_projectable_low_only"]),
            "content_hash": _field("sha256", constraints=["canonical_sha256_of_non_hash_fields"]),
        },
        "R5S3AudiencePayload": {
            "current_risk_set": _field("import:R5CurrentRiskSet", constraints=["required"]),
            "change_bands": _field("import:R5ChangeBand", cardinality="many", constraints=["sorted_unique_by:risk_ref", "min_items:0"]),
            "measures": _field("import:R5QuantitativeMeasure", cardinality="many", constraints=["sorted_unique_by:authoritative_value_ref", "min_items:0"]),
            "center_map": _field("import:R5CenterMapProjection", constraints=["required"]),
            "cockpit": _field("import:R5ProjectCockpitProjection", constraints=["required"]),
            "low_risk_clusters": _field("R5S3LowRiskCluster", cardinality="many", constraints=["sorted_unique_by:cluster_ref", "min_items:0"]),
        },
    }
    imported = {
        "R5AuthorityReceipt": {"source": "mm_r5.contracts:R5AuthorityReceipt", "source_file": MODULE_FILES["mm_r5.contracts"]},
        "SourceRevisionContentPair": {"source": "mm_r5.contracts:SourceRevisionContentPair", "source_file": MODULE_FILES["mm_r5.contracts"]},
        "R5CurrentRiskSet": {"source": "mm_r5.contracts:R5CurrentRiskSet", "source_file": MODULE_FILES["mm_r5.contracts"]},
        "R5ChangeBand": {"source": "mm_r5.contracts:R5ChangeBand", "source_file": MODULE_FILES["mm_r5.contracts"]},
        "R5QuantitativeMeasure": {"source": "mm_r5.contracts:R5QuantitativeMeasure", "source_file": MODULE_FILES["mm_r5.contracts"]},
        "R5CenterMapProjection": {"source": "mm_r5.contracts:R5CenterMapProjection", "source_file": MODULE_FILES["mm_r5.contracts"]},
        "R5ProjectionInstance": {"source": "mm_r5.contracts:R5ProjectionInstance", "source_file": MODULE_FILES["mm_r5.contracts"]},
        "R5ProjectCockpitProjection": {"source": "mm_r5.contracts:R5ProjectCockpitProjection", "source_file": MODULE_FILES["mm_r5.contracts"]},
        "D09AudienceProjection": {"source": "mm_r4.d09_projection:D09AudienceProjection", "source_file": MODULE_FILES["mm_r4.d09_projection"]},
        "D09ProjectionCountSurface": {"source": "mm_r4.d09_projection:D09ProjectionCountSurface", "source_file": MODULE_FILES["mm_r4.d09_projection"]},
        "D09RiskMarker": {"source": "mm_r4.d09_projection:D09RiskMarker", "source_file": MODULE_FILES["mm_r4.d09_projection"]},
        "D09R2RiskHandoff": {"source": "mm_r4.d09_projection:D09R2RiskHandoff", "source_file": MODULE_FILES["mm_r4.d09_projection"]},
        "D09HotspotProjection": {"source": "mm_r4.d09_projection:D09HotspotProjection", "source_file": MODULE_FILES["mm_r4.d09_projection"]},
        "D10AudienceProjection": {"source": "mm_r4.d10_projection:D10AudienceProjection", "source_file": MODULE_FILES["mm_r4.d10_projection"]},
        "D10ProjectionCountSurface": {"source": "mm_r4.d10_projection:D10ProjectionCountSurface", "source_file": MODULE_FILES["mm_r4.d10_projection"]},
        "D10ProjectionVersion": {"source": "mm_r4.d10_projection:D10ProjectionVersion", "source_file": MODULE_FILES["mm_r4.d10_projection"]},
        "D10RiskMarker": {"source": "mm_r4.d10_projection:D10RiskMarker", "source_file": MODULE_FILES["mm_r4.d10_projection"]},
        "D10R2RiskHandoff": {"source": "mm_r4.d10_projection:D10R2RiskHandoff", "source_file": MODULE_FILES["mm_r4.d10_projection"]},
        "D10HotspotProjection": {"source": "mm_r4.d10_projection:D10HotspotProjection", "source_file": MODULE_FILES["mm_r4.d10_projection"]},
        "D10ChangeSection": {"source": "mm_r4.d10_projection:D10ChangeSection", "source_file": MODULE_FILES["mm_r4.d10_projection"]},
        "D10CenterPatternRow": {"source": "mm_r4.d10_projection:D10CenterPatternRow", "source_file": MODULE_FILES["mm_r4.d10_projection"]},
        "D10ProjectProjection": {"source": "mm_r4.d10_projection:D10ProjectProjection", "source_file": MODULE_FILES["mm_r4.d10_projection"]},
    }
    schema = {
        "schema": PACKET_SCHEMA,
        "status": STATUS,
        "additional_keys": "forbidden_at_every_object",
        "root_object": "R5S3AuthorityPacket",
        "authority_scope": {
            "mode": AUTHORITY_MODE,
            "may_claim": ["S3 synthetic/offline supplemental test authority"],
            "must_not_claim": ["clinical_truth", "formal_medical_conclusion",
                               "real_project", "real_model", "product",
                               "production", "security_eligibility",
                               "S4+_acceptance", "runtime_completion"],
        },
        "enums": ENUMS,
        "imported_objects": imported,
        "objects": objects,
        "hash_dag": hash_dag,
        "receipt_content_hash_recipe": {
            "algorithm": HASH_ALGORITHM,
            "canonicalization": HASH_CANONICALIZATION,
            "covered_object": "R5AuthorityReceipt",
            "ref_prefix": RECEIPT_REF_PREFIX,
            "rule": (f"receipt_content_hash = canonical_{HASH_ALGORITHM}("
                     f"complete R5AuthorityReceipt); authority_receipt_ref = "
                     f"'{RECEIPT_REF_PREFIX}' + receipt_content_hash"),
        },
        "packet_id_grammar": f"{PACKET_ID_PREFIX}:<audience_replay_content_hash>",
        "packet_id_prefix": PACKET_ID_PREFIX,
        "receipt_ref_prefix": RECEIPT_REF_PREFIX,
        "cluster_ref_prefix": CLUSTER_REF_PREFIX,
        "cross_object_invariants": INVARIANTS,
        "forbidden_semantic_branches": FORBIDDEN_SEMANTIC_BRANCHES,
        "challenge_registry_spec": {
            "exact_challenges": CHALLENGE_EXACT,
            "categories": CHALLENGE_CATEGORIES,
            "test_nodeid_pattern": ("poc/medical_monitoring_ai_native_r5/tests/"
                                    "test_s3_contract_artifacts.py::"
                                    "test_challenge_case[{}]"),
        },
    }
    return schema


# ---------------------------------------------------------------------------
# exact_overlay.json
# ---------------------------------------------------------------------------


def build_overlay() -> Dict[str, Any]:
    return {
        "schema": OVERLAY_SCHEMA,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "enums": ENUMS,
        "tagged_variants": {
            "d09_center_pattern_unit": {
                "required_public_objects": [
                    "import:D09AudienceProjection",
                    "import:D09ProjectionCountSurface",
                    "import:D09RiskMarker",
                    "import:D09R2RiskHandoff",
                    "import:D09HotspotProjection",
                    "import:SourceRevisionContentPair",
                ],
                "marker_prefix": "d09_marker:",
                "authority_kind": "d09_audience",
            },
            "d10_project_unit": {
                "required_public_objects": [
                    "import:D10AudienceProjection",
                    "import:D10ProjectionCountSurface",
                    "import:D10ProjectionVersion",
                    "import:D10ChangeSection",
                    "import:D10CenterPatternRow",
                    "import:D10RiskMarker",
                    "import:D10R2RiskHandoff",
                    "import:D10HotspotProjection",
                    "import:D10ProjectProjection",
                    "import:SourceRevisionContentPair",
                ],
                "marker_prefix": "d10_marker:",
                "authority_kind": "d10_project",
            },
        },
        "supplemental_kinds": ENUMS["supplemental_kind"],
        "membership_states": ENUMS["membership_state"],
        "source_matrix": SOURCE_MATRIX,
        "source_bindings": [_binding_descriptor(b) for b in SOURCE_BINDINGS],
        "typed_input_denylist": TYPED_INPUT_DENYLIST,
        "public_allowlist": PUBLIC_ALLOWLIST,
        "layer_recipes": LAYER_RECIPES,
        "change_emission_table": CHANGE_EMISSION_TABLE,
        "lifecycle_state_table": LIFECYCLE_STATE_TABLE,
        "hash_domains": {
            "private_packet_integrity": {
                "may_cover": ["hidden_member_refs", "hidden_site_refs",
                              "evaluation_member_refs", "hidden_member_count",
                              "hidden_site_count"],
                "hash_leaf": "packet_integrity_hash",
            },
            "public_audience_authority": {
                "may_cover": ["projectable public projection leaves only"],
                "hash_leaf": "content_hash",
            },
            "public_replay_content": {
                "may_cover": ["audience_payload only (including low clusters)"],
                "hash_leaf": "audience_replay_content_hash",
            },
        },
        "hash_dag": _hash_dag(),
        "receipt_content_hash_recipe": {
            "algorithm": HASH_ALGORITHM,
            "canonicalization": HASH_CANONICALIZATION,
            "covered_object": "R5AuthorityReceipt",
            "ref_prefix": RECEIPT_REF_PREFIX,
            "rule": (f"receipt_content_hash = canonical_{HASH_ALGORITHM}("
                     f"complete R5AuthorityReceipt); authority_receipt_ref = "
                     f"'{RECEIPT_REF_PREFIX}' + receipt_content_hash"),
        },
        "packet_id_grammar": f"{PACKET_ID_PREFIX}:<audience_replay_content_hash>",
        "packet_id_prefix": PACKET_ID_PREFIX,
        "receipt_ref_prefix": RECEIPT_REF_PREFIX,
        "cluster_ref_prefix": CLUSTER_REF_PREFIX,
        "layer_measure_units": LAYER_MEASURE_UNITS,
        "allowlist": ["projectable public projection leaves",
                      "existing R5 receipt leaves",
                      "named synthetic supplemental authority",
                      "packet fixture (synthetic offline, never public)"],
        "denylist": ["D09/D10 typed-input leaves",
                     "raw member refs as current-risk identities",
                     "hidden leaves in any audience hash",
                     "not_evaluable in COVERAGE_STATES",
                     "score/rank/top-N/punitive ordinal fields",
                     "recomputed medical numerator/denominator/rate",
                     "clinical domain or severity sourced from typed Member"],
        "acceptance_boundary": {
            "only_claim": STATUS,
            "must_not_claim": ["ACCEPT_R5_S3_CONTRACT", "ACCEPT_R5_S3",
                               "runtime_completion", "S4+_acceptance",
                               "product", "production"],
            "codex_and_reviewer_own": ["ACCEPT_R5_S3_CONTRACT", "ACCEPT_R5_S3"],
            "acceptance_digest": {
                "owner": "final Codex/reviewer acceptance (NOT generator-owned)",
                "policy": ("acceptance creates an external immutable digest "
                           "pinning the exact human/generator/verifier/"
                           "artifact/test SHA-256 values; that digest is "
                           "never authored or re-signable by the generator; "
                           "later joint re-signing invalidates acceptance"),
            },
        },
        "done_gates": {
            "D1": {"gate": "authority read-only and leaf-traceable",
                   "categories": ["typed_input_not_promoted"]},
            "D2": {"gate": "current risk full set, low cluster lossless and in replay, resolved excluded",
                   "categories": ["aggregate_receipt_set"]},
            "D3": {"gate": "change band closed emission, no fabricated/resolved inference, mixed fail-closed",
                   "categories": ["change_emission"]},
            "D4": {"gate": "eight count layers conserved separately, membership rebuild or not_projectable",
                   "categories": ["layer_recipes"]},
            "D5": {"gate": "center map pattern/individual layering, hidden zero-leak, stable order, no ranking",
                   "categories": ["tagged_d09_d10_variants"]},
            "D6": {"gate": "machine contract before runtime: schema/overlay/registry/pins/manifest, generator+verifier normal and optimized, tamper gates",
                   "categories": ["machine_contract"]},
        },
        "invariants": INVARIANTS,
        "forbidden_semantic_branches": FORBIDDEN_SEMANTIC_BRANCHES,
    }


# ---------------------------------------------------------------------------
# challenge_registry.json
# ---------------------------------------------------------------------------


def _challenge(case_id: str, category: str, rule_id: str,
               mutation: Dict[str, Any], expected: str, severity: str,
               oracle: str) -> Dict[str, Any]:
    mutation_path = mutation.get("path", "")
    location = mutation.get("location", "artifacts")
    frozen_projection = EXPECTED_PROJECTION_BY_CASE.get(case_id)
    if frozen_projection is None:
        raise RuntimeError(f"missing frozen projection for {case_id}")
    if mutation.get("expected_projection", "not_emitted") != frozen_projection:
        raise RuntimeError(
            f"challenge {case_id} projection drift: "
            f"{mutation.get('expected_projection')!r} != {frozen_projection!r}")
    return {
        "case_id": case_id,
        "category": category,
        "rule_id": rule_id,
        "precondition": f"valid R5-S3 contract artifact set with a single-mutation leaf {mutation_path or '(packet oracle)'}",
        "single_mutation": mutation,
        "expected_typed_outcome_or_error": expected,
        "expected_projection": frozen_projection,
        "forbidden_audience_output": "no stale, cross-identity, fabricated, hidden or task-state audience output",
        "stage_oracle_contract": {
            "kind": "executable_pytest",
            "planned_stage": "S3",
            "rule_id": rule_id,
            "test_locator": f"poc/medical_monitoring_ai_native_r5/tests/test_s3_contract_artifacts.py::test_challenge_case[{case_id}]",
            "required_non_llm_anchor": "executed mutation on an isolated re-signed copy with exact typed error/hash/projection assertion",
        },
        "non_llm_oracle": oracle,
        "severity": severity,
        "mutation_location": location,
    }


def build_challenge_registry() -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []

    def _add(category: str, rule_id: str, mutation: Dict[str, Any],
             expected: str, severity: str = "P1", oracle: str = "") -> None:
        case_id = f"R5S3C-{len(rows) + 1:03d}"
        rows.append(_challenge(case_id, category, rule_id, mutation,
                               expected, severity, oracle or expected))

    def _artifact(path: str, value: Any, projection: str = "not_emitted",
                  resign: str = "before") -> Dict[str, Any]:
        return {"op": "replace_leaf", "path": path, "value": value,
                "expected_projection": projection, "location": "artifacts",
                "resign": resign}

    # ---- typed_input_not_promoted (6) ------------------------------------
    for rule, path_value in [
        ("d09_typed_input_leaf",
         ("mm_r4.d09_contracts:D09TypedInput.denominator", "unit.d09.injected")),
        ("d10_typed_input_leaf",
         ("mm_r4.d10_contracts:D10TypedInput.visibility_decision", "unit.d10.injected")),
        ("member_leaf_as_public",
         ("mm_r4.d10_contracts:Member.member_ref", "unit.d10.injected_member")),
        ("member_domain_leaf",
         ("mm_r4.d10_contracts:Member.domain", "unit.d10.injected_member_domain")),
        ("member_priority_leaf",
         ("mm_r4.d10_contracts:Member.monitoring_priority", "unit.d10.injected_member_priority")),
        ("denominator_typed_leaf",
         ("mm_r4.d10_contracts:Denominator.denominator_kind", "measure.denominator_typed")),
    ]:
        target, leaf = path_value
        _add("typed_input_not_promoted", f"typed_input_not_promoted.{rule}",
             {"op": "append_source_row", "path": "overlay.source_matrix",
              "value": {"leaf": leaf, "source_kind": "r4_public",
                        "path": target, "provenance": "tamper"},
              "expected_projection": "not_emitted", "location": "artifacts"},
             "reject:typed_input_leaf_promoted",
             oracle=f"source path {target} targets a typed-input class and must fail closed through the hard-coded denylist resolver")

    # ---- aggregate_receipt_set (6) ---------------------------------------
    _add("aggregate_receipt_set", "aggregate_receipt_set.missing_aggregate_receipt",
         {"op": "delete_object", "path": "packet_schema.objects.R5S3AggregateReceiptSetIdentity",
          "value": "", "expected_projection": "not_emitted", "location": "artifacts"},
         "reject:aggregate_receipt_missing", oracle="aggregate receipt-set identity object must exist in schema")
    _add("aggregate_receipt_set", "aggregate_receipt_set.unit_identity_mismatch",
         _artifact("packet_schema.objects.R5S3AggregateReceiptSetIdentity.unit_receipt_refs.constraints",
                   [], ),
         "reject:aggregate_identity_mismatch", oracle="unit receipt refs must keep receipt_ref_prefix (aggregate identity binding)")
    _add("aggregate_receipt_set", "aggregate_receipt_set.raw_member_current_risk_ref",
         _artifact("packet_schema.objects.R5S3RiskLifecycleAuthority.marker_identity_ref.constraints",
                   []),
         "reject:raw_member_as_current_risk_ref", oracle="lifecycle marker identity ref must keep current_risk_marker_prefix")
    _add("aggregate_receipt_set", "aggregate_receipt_set.marker_identity_required",
         {"op": "drop_binding", "path": "overlay.source_matrix",
          "value": "binding.supplemental.current_risk_marker_identity",
          "expected_projection": "not_emitted", "location": "artifacts"},
         "reject:sourced_from_missing", oracle="current-risk marker-identity supplemental binding must exist")
    _add("aggregate_receipt_set", "aggregate_receipt_set.resolved_not_in_current",
         _artifact("packet_schema.objects.R5S3AudiencePayload.current_risk_set.constraints",
                   ["include_resolved_in_current"]),
         "reject:current_reserved_plane_overlap", oracle="resolved refs must never join the current plane")
    _add("aggregate_receipt_set", "aggregate_receipt_set.low_cluster_lossless_expansion",
         {"op": "delete_object", "path": "packet_schema.objects.R5S3AudiencePayload.low_risk_clusters",
          "value": "", "expected_projection": "not_emitted", "location": "artifacts"},
         "reject:low_cluster_not_in_replay", oracle="low clusters must live in audience payload and replay hash")

    # ---- tagged_d09_d10_variants (6) -------------------------------------
    _add("tagged_d09_d10_variants", "tagged_d09_d10_variants.closed_variant_enum",
         _artifact("overlay.enums.tagged_variant_kind",
                   ["d09_center_pattern_unit", "d10_project_unit", "d11_hybrid"]),
         "reject:tagged_variant_payload_mismatch", oracle="variant_kind enum must stay closed at exactly two values")
    _add("tagged_d09_d10_variants", "tagged_d09_d10_variants.d09_payload_exact",
         _artifact("packet_schema.objects.R5S3D09CenterPatternUnit.audience.type",
                   "import:D10AudienceProjection"),
         "reject:tagged_variant_payload_mismatch", oracle="d09 variant payload must carry D09 audience projection only")
    _add("tagged_d09_d10_variants", "tagged_d09_d10_variants.d10_payload_exact",
         _artifact("packet_schema.objects.R5S3D10ProjectUnit.audience.type",
                   "import:D09AudienceProjection"),
         "reject:tagged_variant_payload_mismatch", oracle="d10 variant payload must carry D10 audience projection only")
    _add("tagged_d09_d10_variants", "tagged_d09_d10_variants.cross_variant_payload",
         _artifact("packet_schema.objects.R5S3AuthorityUnitTagged.d09_variant_payload.constraints",
                   ["required_when:variant_kind=d10_project_unit"]),
         "reject:tagged_variant_payload_mismatch", oracle="d09 payload must be forbidden for d10 variant")
    _add("tagged_d09_d10_variants", "tagged_d09_d10_variants.both_authorities_present",
         _artifact("packet_schema.objects.R5S3AuthorityUnitTagged.d10_variant_payload.constraints",
                   ["required_when:variant_kind=d09_center_pattern_unit"]),
         "reject:tagged_variant_payload_mismatch", oracle="d10 payload must be forbidden for d09 variant")
    _add("tagged_d09_d10_variants", "tagged_d09_d10_variants.d09_d10_not_confused",
         _artifact("overlay.tagged_variants.d09_center_pattern_unit.marker_prefix",
                   "d10_marker:"),
         "reject:tagged_variant_payload_mismatch", oracle="d09 variant must keep d09_marker: prefix")

    # ---- hash_separation_private_public (6) ------------------------------
    _add("hash_separation_private_public", "hash_separation_private_public.receipt_recipe_sha1",
         _artifact("overlay.hash_dag.receipt_content_hash.algorithm", "sha1"),
         "reject:hash_algorithm_mismatch", oracle="receipt content hash must be sha256 only")
    _add("hash_separation_private_public", "hash_separation_private_public.receipt_recipe_canonicalization",
         _artifact("overlay.hash_dag.receipt_content_hash.canonicalization", "plain"),
         "reject:hash_canonicalization_mismatch", oracle="receipt recipe canonicalization must stay frozen")
    _add("hash_separation_private_public", "hash_separation_private_public.audience_replay_self_edge",
         _artifact("overlay.hash_dag.audience_replay_content_hash.depends_on",
                   ["audience_replay_content_hash"]),
         "reject:hash_recipe_cycle", oracle="audience replay hash must never depend on itself")
    _add("hash_separation_private_public", "hash_separation_private_public.hidden_leaf_in_audience_hash",
         _artifact("overlay.hash_dag.audience_replay_content_hash.may_cover_hidden", True),
         "reject:hidden_leaf_in_audience_hash", oracle="audience replay hash must never cover hidden leaves")
    _add("hash_separation_private_public", "hash_separation_private_public.packet_id_double_colon",
         _artifact("overlay.packet_id_grammar",
                   "r5-s3-contract::<audience_replay_content_hash>"),
         "reject:packet_id_grammar_mismatch", oracle="packet-id grammar must be exactly single-colon")
    _add("hash_separation_private_public", "hash_separation_private_public.audience_replay_covers_clusters",
         {"op": "delete_object", "path": "packet_schema.objects.R5S3AudiencePayload.low_risk_clusters",
          "value": "", "expected_projection": "not_emitted", "location": "artifacts"},
         "reject:low_cluster_not_in_replay", oracle="low clusters must stay in audience payload under replay hash")

    # ---- layer_recipes (10) ----------------------------------------------
    for layer in ["individual_risk", "center_pattern", "affected_subject",
                  "event", "affected_site", "project_signal", "clue", "query"]:
        _add("layer_recipes", f"layer_recipes.{layer}",
             _artifact(f"overlay.layer_recipes.{layer}.conservation_expr",
                       f"count == len(projectable {layer} members) when membership_state=projectable (variant)",
                       projection="emitted"),
             f"accept:layer_recipes.{layer}",
             oracle=f"{layer} recipe conserved variant; pre/post canonical bytes differ and the re-signed copy still verifies")
    _add("layer_recipes", "layer_recipes.invalid_coverage_enum",
         _artifact("overlay.enums.coverage_state",
                   list(ENUMS["coverage_state"]) + ["not_evaluable"]),
         "reject:invalid_coverage_enum", oracle="COVERAGE_STATES must never contain not_evaluable")
    _add("layer_recipes", "layer_recipes.not_projectable_supplemental",
         _artifact("overlay.layer_recipes.clue.conservation_operator",
                   "count_equals_sorted_unique_length"),
         "reject:conservation_operator_mismatch", oracle="clue/query layers require the non-expandable conservation operator")

    # ---- change_emission (12) --------------------------------------------
    for kind in ["initial_current", "new", "upgraded", "continued", "downgraded",
                 "resolved", "reopened", "superseded", "not_evaluable", "not_comparable"]:
        _add("change_emission", f"change_emission.{kind}",
             _artifact(f"overlay.change_emission_table.{kind}.source_objects",
                       [f"exact source objects frozen for {kind} (variant)"],
                       projection="emitted"),
             f"accept:change_emission.{kind}",
             oracle=f"{kind} emission row frozen; source_objects exact; re-signed copy verifies")
    _add("change_emission", "change_emission.resolved_inferred_from_change_section",
         _artifact("overlay.change_emission_table.resolved.r2_action", "continue"),
         "reject:resolved_without_lifecycle_authority", oracle="resolved change band requires closure authority, never D10ChangeSection inference")
    _add("change_emission", "change_emission.mixed_d10_cause",
         _artifact("packet_schema.objects.R5S3ChangeCauseMixtureAuthority.causes.constraints",
                   ["min_items:1"]),
         "reject:mixed_d10_cause", oracle="mixture authority requires at least two causes; mixed D10 cause fails closed")

    # ---- machine_contract (8) --------------------------------------------
    _add("machine_contract", "machine_contract.schema_exact_keys",
         {"op": "add_object_key", "path": "packet_schema.objects.R5S3AuthorityPacket",
          "value": {"content_hash": {"type": "sha256", "cardinality": "one", "nullable": False}},
          "expected_projection": "not_emitted", "location": "artifacts"},
         "reject:schema_key_mismatch", oracle="root packet must contain no content_hash (acyclic DAG)")
    _add("machine_contract", "machine_contract.source_pin_drift",
         _artifact("source_pins.sources.0.sha256", "0" * 64),
         "reject:source_pin_drift", oracle="source pin sha256 must match the real file bytes")
    _add("machine_contract", "machine_contract.manifest_hash_rewrite",
         _artifact("manifest.artifacts.0.sha256", "0" * 64, resign="after"),
         "reject:manifest_hash_rewrite", oracle="manifest artifact sha256 must match the real bytes")
    _add("machine_contract", "machine_contract.challenge_unique_id",
         _artifact("challenge_registry.challenges.0.case_id", "R5S3C-002"),
         "reject:challenge_duplicate_id", oracle="challenge case ids must be unique")
    _add("machine_contract", "machine_contract.challenge_missing_locator",
         _artifact("challenge_registry.challenges.0.stage_oracle_contract.test_locator", ""),
         "reject:challenge_missing_locator", oracle="every challenge row needs a real pytest nodeid")
    _add("machine_contract", "machine_contract.generator_check_deterministic",
         _artifact("overlay.schema", "medical-monitoring-r5-s3-exact-overlay-v9.9"),
         "reject:schema_version_mismatch", oracle="generator/verifier must pin the exact schema versions")
    _add("machine_contract", "machine_contract.verifier_normal_optimized",
         _artifact("source_pins.self_pin_recipe",
                   "self-pin recipe (variant wording, still self-pin)",
                   projection="emitted"),
         "accept:machine_contract.verifier_normal_optimized", oracle="normal and optimized verifier outputs compare byte-identical")
    _add("machine_contract", "machine_contract.tamper_artifact_add_remove",
         {"op": "delete_object", "path": "packet_schema.objects.R5S3ClosureAuthority",
          "value": "", "expected_projection": "not_emitted", "location": "artifacts"},
         "reject:closure_authority_missing", oracle="closure authority object must exist")

    # ---- done_gates_acceptance (6) ---------------------------------------
    _add("done_gates_acceptance", "done_gates_acceptance.contract_ready_only",
         _artifact("overlay.acceptance_boundary.only_claim", "ACCEPT_R5_S3_CONTRACT"),
         "reject:authority_scope_violation", oracle="artifact work yields only R5_S3_CONTRACT_READY_FOR_REVIEW")
    _add("done_gates_acceptance", "done_gates_acceptance.no_runtime_claim",
         _artifact("overlay.acceptance_boundary.must_not_claim",
                   ["clinical_truth", "ACCEPT_R5_S3", "product",
                    "production"]),
         "reject:authority_scope_violation", oracle="runtime_completion must stay in must_not_claim")
    _add("done_gates_acceptance", "done_gates_acceptance.no_8911_start",
         _artifact("overlay.acceptance_boundary.must_not_claim",
                   ["clinical_truth", "product", "production", "8911_started"]),
         "reject:authority_scope_violation", oracle="8911 startup must never be claimed")
    _add("done_gates_acceptance", "done_gates_acceptance.acceptance_digest_not_generator_owned",
         _artifact("overlay.acceptance_boundary.acceptance_digest.owner", "generator"),
         "reject:authority_scope_violation", oracle="acceptance digest owner must be final Codex/reviewer, never generator")
    _add("done_gates_acceptance", "done_gates_acceptance.hidden_only_mutation_keeps_audience",
         {"op": "packet_hidden_only_mutation", "path": "packet.oracle.hidden_member_refs",
          "value": ["member.hidden.extra"], "expected_projection": "unchanged",
          "location": "packet"},
         "accept:done_gates_acceptance.hidden_only_mutation_keeps_audience",
         oracle="hidden-only mutation changes packet_integrity_hash and leaves audience replay/content hashes identical")
    _add("done_gates_acceptance", "done_gates_acceptance.unit_order_permutation_canonicalized",
         {"op": "packet_unit_order_permutation", "path": "packet.oracle.authority_units",
          "value": "reversed", "expected_projection": "unchanged",
          "location": "packet"},
         "accept:done_gates_acceptance.unit_order_permutation_canonicalized",
         oracle="unit-order permutation canonicalizes to the same audience replay content hash")

    return {
        "schema": CHALLENGE_SCHEMA,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "challenge_count": len(rows),
        "categories": CHALLENGE_CATEGORIES,
        "challenges": rows,
    }


# ---------------------------------------------------------------------------
# source_pins.json
# ---------------------------------------------------------------------------


def _source_group(path: str) -> str:
    if "implementation_contract_v0_2" in path:
        return "r5_s3_human_contract"
    if "stage_contract_v0_3" in path or "exact_contract.json" in path:
        return "accepted_s0"
    if "acceptance_record" in path or "s2_acceptance_record" in path:
        return "accepted_r5"
    if "r5_s3_20260818_context" in path or "implementation_contract_v0_1" in path:
        return "task_context"
    if path.startswith("poc/medical_monitoring_ai_native_r4/"):
        return "accepted_r4_public_authority"
    if path.startswith("poc/medical_monitoring_ai_native_r5/"):
        return "accepted_r5_surface"
    if "tools/" in path:
        return "generator_verifier"
    return "misc"


SOURCE_PATHS: List[str] = [
    "reviews/medical_monitoring_r5_s3_implementation_contract_v0_2_20260818.md",
    "reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md",
    "reviews/medical_monitoring_r5_s3_implementation_contract_v0_1_20260818.md",
    "context/medical_monitoring_r5_s3_20260818_context.md",
    "context/medical_monitoring_r5_contract_acceptance_record_20260818.md",
    "context/medical_monitoring_r5_s2_acceptance_record_20260818.md",
    "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/authority_adapter.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/canonical.py",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_contracts.py",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/d09_projection.py",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_contracts.py",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_projection.py",
    "tools/generate_medical_monitoring_r5_s3_contract_v0_2.py",
    "tools/verify_medical_monitoring_r5_s3_contract_v0_2.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s3_contract_artifacts.py",
]


def build_source_pins() -> Dict[str, Any]:
    pins = []
    for path in SOURCE_PATHS:
        target = ROOT / path
        if not target.exists() or not target.is_file():
            raise RuntimeError(f"pinned source missing: {path}")
        pins.append({
            "path": path,
            "group": _source_group(path),
            "sha256": sha256_file(target),
        })
    return {
        "schema": SOURCE_PINS_SCHEMA,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "source_count": len(pins),
        "self_pin_recipe": "each pinned source is SHA-256 of its raw file bytes recorded at generation time; the verifier validates its own raw bytes against its recorded pin (normalized, auditable, non-deadlock self-pin)",
        "sources": pins,
    }


# ---------------------------------------------------------------------------
# manifest.json
# ---------------------------------------------------------------------------


def build_manifest(overlay_bytes: bytes, schema_bytes: bytes,
                   challenge_bytes: bytes, source_pins_bytes: bytes) -> Dict[str, Any]:
    artifact_paths = [
        ("reviews/medical_monitoring_r5_s3_implementation_contract_v0_2_20260818.md", "human_contract"),
        ("tools/generate_medical_monitoring_r5_s3_contract_v0_2.py", "generator"),
        ("tools/verify_medical_monitoring_r5_s3_contract_v0_2.py", "verifier"),
        ("artifacts/medical_monitoring_r5_s3_contract_v0_2/exact_overlay.json", "exact_overlay"),
        ("artifacts/medical_monitoring_r5_s3_contract_v0_2/packet_schema.json", "packet_schema"),
        ("artifacts/medical_monitoring_r5_s3_contract_v0_2/challenge_registry.json", "challenge_registry"),
        ("artifacts/medical_monitoring_r5_s3_contract_v0_2/source_pins.json", "source_pins"),
        ("artifacts/medical_monitoring_r5_s3_contract_v0_2/manifest.json", "manifest"),
    ]
    artifacts = []
    for path, role in artifact_paths:
        if role == "manifest":
            artifacts.append({"path": path, "role": role, "hash_kind": "canonical_self", "sha256": None})
        else:
            target = ROOT / path
            if role in ("human_contract", "generator", "verifier"):
                sha = sha256_file(target)
            elif path.endswith("exact_overlay.json"):
                sha = sha256_bytes(overlay_bytes)
            elif path.endswith("packet_schema.json"):
                sha = sha256_bytes(schema_bytes)
            elif path.endswith("challenge_registry.json"):
                sha = sha256_bytes(challenge_bytes)
            elif path.endswith("source_pins.json"):
                sha = sha256_bytes(source_pins_bytes)
            else:  # pragma: no cover
                raise RuntimeError(f"unhandled artifact: {path}")
            artifacts.append({"path": path, "role": role, "hash_kind": "raw_sha256", "sha256": sha})
    sources = [
        {"path": item["path"], "group": item["group"], "sha256": item["sha256"]}
        for item in json.loads(source_pins_bytes)["sources"]
    ]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "artifact_count": len(artifacts),
        "source_count": len(sources),
        "artifacts": artifacts,
        "pinned_sources": sources,
        "manifest_content_sha256": "",
    }
    manifest["manifest_content_sha256"] = _manifest_content_hash(manifest)
    return manifest


def _manifest_content_hash(manifest: Dict[str, Any]) -> str:
    core = dict(manifest)
    core.pop("manifest_content_sha256", None)
    return sha256_bytes(canonical_bytes(core))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def expected_artifacts(artifact_dir: Path) -> Dict[Path, bytes]:
    overlay_bytes = canonical_bytes(build_overlay())
    schema_bytes = canonical_bytes(build_schema())
    challenge_bytes = canonical_bytes(build_challenge_registry())
    source_pins_bytes = canonical_bytes(build_source_pins())
    manifest_bytes = canonical_bytes(build_manifest(
        overlay_bytes, schema_bytes, challenge_bytes, source_pins_bytes))
    return {
        artifact_dir / "exact_overlay.json": overlay_bytes,
        artifact_dir / "packet_schema.json": schema_bytes,
        artifact_dir / "challenge_registry.json": challenge_bytes,
        artifact_dir / "source_pins.json": source_pins_bytes,
        artifact_dir / "manifest.json": manifest_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="compare expected artifacts without writing")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--artifacts", type=Path, default=ARTIFACT_DIR)
    args = parser.parse_args()
    root: Path = args.root
    artifact_dir: Path = args.artifacts
    if not root.is_dir():
        root = ROOT
    if str(artifact_dir).endswith("medical_monitoring_r5_s3_contract_v0_2"):
        artifact_dir = root / "artifacts" / "medical_monitoring_r5_s3_contract_v0_2"
    expected = expected_artifacts(artifact_dir)
    if args.check:
        mismatches = []
        for path, payload in expected.items():
            if not path.exists() or path.read_bytes() != payload:
                mismatches.append(str(path.relative_to(root)))
        print(json.dumps({"ok": not mismatches, "mode": "check",
                          "mismatches": mismatches}, sort_keys=True))
        return 0 if not mismatches else 1
    for path, payload in expected.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(json.dumps({"ok": True, "mode": "write",
                      "written": [str(p.relative_to(root)) for p in expected]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
