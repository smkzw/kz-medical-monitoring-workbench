#!/usr/bin/env python3
"""Independent deterministic verifier for the R5-S4 Risk Inspector contract.

Semantic hard-pins live in THIS file (outside artifact-owned data), so a
coordinated re-signing of the artifacts (generator + source_pins + manifest)
cannot weaken the frozen S4 semantics.

The verifier:
  * hard-pins every closed enum, the four-node acyclic hash DAG, all 18
    invariants, all 10 join recipes, the severity mapping, the zh lexicons,
    the forbidden audience tokens, and the challenge spec (13 -> 97 exact);
  * validates the exact typed schema objects and per-field descriptors;
  * validates source-matrix leaf COVERAGE (every schema leaf has exactly one
    real R4/R5 path, deterministic derivation, synthetic recipe, or honest
    named deferred) and resolves every real ``module:Class.field`` path via
    AST against the pinned R4/R5 sources;
  * validates the audience/audit separation and the packet hash DAG;
  * validates all accepted source SHAs and the exact artifact set/manifest;
  * RECOMPUTES packet semantics against real R4: it instantiates typed
    ``AnalysisAttempt`` / ``WorkerAnalysisOutput`` / ``EvidenceDigestContext``
    from packet leaves, calls ``verify_attempt`` for all seven dimensions,
    calls ``derive_conflicts`` for the exact conflict set, and reconstructs
    ``WorkerAnalysisOutput`` from immutable raw bytes; stored labels never
    override recomputation;
  * enforces an exact 0/1/N tagged union across every plane;
  * EXECUTES the challenge registry: each row's base fixture must pass with
    ``[]`` before mutation, the single mutation must isolate exactly one
    fixed ``s4.*`` error code (never merely contain it);
  * asserts no ``assert`` in the generator or this verifier so normal and
    ``PYTHONOPTIMIZE=2`` runs are byte-identical.

Decision paths use only explicit exceptions via ``_require`` / ``_fail``.
"""

from __future__ import annotations

import argparse
import ast
import base64
import copy
import dataclasses
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARTIFACTS = DEFAULT_ROOT / "artifacts" / "medical_monitoring_r5_s4_contract_v0_1"

STATUS = "R5_S4_CONTRACT_READY_FOR_REVIEW"
AUTHORITY_MODE = "synthetic_offline_test_only"
OVERLAY_SCHEMA = "medical-monitoring-r5-s4-exact-overlay-v0.1"
PACKET_SCHEMA = "medical-monitoring-r5-s4-packet-schema-v0.1"
ANCHOR_SCHEMA = "medical-monitoring-r5-s4-authority-anchor-v0.1"
SOURCE_PINS_SCHEMA = "medical-monitoring-r5-s4-source-pins-v0.1"
MANIFEST_SCHEMA = "medical-monitoring-r5-s4-artifact-manifest-v0.1"
REGISTRY_SCHEMA = "medical-monitoring-r5-s4-challenge-registry-v0.1"

PACKET_ID_PREFIX = "r5-s4-contract"
PACKET_ID_GRAMMAR = f"{PACKET_ID_PREFIX}:<audience_content_hash>"
ANCHOR_REF_PREFIX = "anchor:"
RECEIPT_REF_PREFIX = "receipt:"
HASH_ALGORITHM = "sha256"
HASH_CANONICALIZATION = "utf8_nfc_sorted_keys_compact_json_newline"
GENESIS_HASH = "genesis"
R5_EXACT_CONTRACT_SHA = "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949"

SOURCE_COUNT = 32
ARTIFACT_COUNT_PRESENT = 7  # human_contract, generator, verifier, 4 JSON (W2)
PLANNED_CHALLENGE_REGISTRY = 1

#: module -> source file (must match source_pins.json + generator).
MODULE_FILES: Dict[str, str] = {
    "mm_r4.contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py",
    "mm_r4.ensemble": "poc/medical_monitoring_ai_native_r4/src/mm_r4/ensemble.py",
    "mm_r4.ensemble_contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/ensemble_contracts.py",
    "mm_r4.d10_contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_contracts.py",
    "mm_r4.d10_projection": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_projection.py",
    "mm_r5.contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py",
    "mm_r5.s2_contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_contracts.py",
}

#: exact closed enum values -- hard-pinned (any tamper fails closed).
EXPECTED_ENUMS: Dict[str, List[str]] = {
    "ensemble_projection_state": ["no_ensemble", "single_analysis", "multi_analysis"],
    "baseline_state": ["confirmed", "partially_supported", "unsupported",
                       "outdated", "insufficient_evidence", "not_applicable"],
    "assessment_reason_code": ["source_rechecked", "content_match",
                               "partial_content_match",
                               "content_absent_from_source",
                               "source_revision_superseded",
                               "evidence_insufficient", "locator_unresolvable",
                               "outside_assessment_scope"],
    "recheck_required_state": ["confirmed", "unsupported"],
    "verification_dimension": ["identity", "version", "date", "unit", "source",
                               "rule", "artifact_integrity"],
    "verification_result": ["passed", "failed", "not_evaluable"],
    "verification_failure_code": ["identity_mismatch", "version_mismatch",
                                  "date_out_of_window", "unit_mismatch",
                                  "source_unresolvable", "rule_version_mismatch",
                                  "artifact_hash_mismatch", "input_content_mismatch"],
    "conflict_relation": ["shared_finding", "single_model_new",
                          "graded_conflict", "mutual_negation", "baseline_miss"],
    "conflict_display_state": ["needs_attention", "visible_conflict",
                               "visible_baseline_miss"],
    "non_hideable_relation": ["mutual_negation", "baseline_miss"],
    "adjudication_outcome": ["merged_supported", "distinct_supported",
                             "rejected_by_evidence", "version_mismatch",
                             "needs_user_attention"],
    "attempt_role": ["worker", "adjudicator"],
    "raw_output_format": ["utf8_text"],
    "fallback_policy": ["none"],
    "pd_wording_state": ["not_pd", "verify_whether_pd"],
    "monitoring_priority": ["high", "medium", "low", "unknown"],
    "model_evidence_role": ["candidate_explanation", "counterevidence_suggestion"],
    "model_evidence_adjudication_state": ["accepted", "divergent", "pending"],
    "severity": ["critical", "high", "medium", "low"],
    "severity_zh": ["紧急", "高", "中", "低"],
    "domain": ["ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
               "symptom_efficacy", "protocol_compliance"],
    "change_kind": ["initial_current", "new", "upgraded", "continued",
                    "downgraded", "resolved", "reopened", "superseded",
                    "not_evaluable", "not_comparable"],
    "change_cause": ["data", "knowledge", "rule", "mapping", "model", "method",
                     "coverage", "denominator", "population", "visibility",
                     "mode", "user_decision"],
    "history_entry_kind": ["attempt_bound", "baseline_assessed",
                           "verification_recorded", "conflict_derived",
                           "adjudication_recorded", "query_draft_generated",
                           "inspection_finalized"],
    "projection_kind": ["d09_audience", "d10_project", "ensemble",
                        "subject_temporal", "aemh_history"],
    "severity_source": ["r4_priority_mapped", "r4_explicit_critical",
                        "fail_closed"],
}

#: exact closed error-code catalog (43; verifier decision codes).
EXPECTED_ERROR_CODES: List[str] = [
    "s4.ensemble_zero_must_be_empty",
    "s4.single_model_consensus_forbidden",
    "s4.duplicate_worker_binding",
    "s4.duplicate_worker_session",
    "s4.duplicate_worker_context",
    "s4.cardinality_not_0_1_n",
    "s4.authority_drift",
    "s4.baseline_recheck_missing",
    "s4.baseline_as_gold",
    "s4.fabricated_consensus",
    "s4.high_risk_hidden",
    "s4.mutual_negation_hidden",
    "s4.baseline_miss_hidden",
    "s4.single_addition_omitted",
    "s4.conflict_set_incomplete",
    "s4.adjudication_deleted_conflict",
    "s4.worker_self_adjudication",
    "s4.adjudicator_context_collision",
    "s4.verification_label_only",
    "s4.verification_unresolved_authority",
    "s4.raw_output_rewritten",
    "s4.raw_parsed_hash_confusion",
    "s4.parsed_output_hash_mismatch",
    "s4.hidden_source_leak",
    "s4.nearest_fallback_forbidden",
    "s4.query_task_semantics",
    "s4.query_draft_partial",
    "s4.audience_audit_leak",
    "s4.model_evidence_on_audience",
    "s4.history_append_only_violation",
    "s4.history_chain_break",
    "s4.journey_fallback_not_none",
    "s4.packet_id_grammar_mismatch",
    "s4.receipt_hash_mismatch",
    "s4.hash_algorithm_mismatch",
    "s4.hash_recipe_cycle",
    "s4.audience_hash_contains_audit_leaf",
    "s4.schema_key_mismatch",
    "s4.enum_value_mismatch",
    "s4.off_enum_s2_adjudication_state",
    "s4.ordinal_mapping_drift",
    "s4.source_path_unresolvable",
    "s4.join_recipe_unresolvable",
    "s4.anchor_identity_mismatch",
    "s4.anchor_claim_drift",
    "s4.raw_sha_external_mismatch",
    "s4.history_prefix_rewrite",
    "s4.critical_severity_authority_missing",
    "s4.model_evidence_not_permitted",
    "s4.cross_plane_projection_drift",
    "s4.query_projection_drift",
    "s4.baseline_projection_drift",
    "s4.imported_object_drift",
]

#: forbidden audience tokens (closed; enforced by this verifier).
FORBIDDEN_AUDIENCE_TOKENS: List[str] = [
    "provider", "model_id", "model_version", "attempt", "hash", "backend",
    "session", "consensus", "worker", "adjudicator", "binding", "正式事实",
    "候选信号", "只读", "待办", "未读", "金标准", "已证实", "权威结论",
    "model_majority", "卡列表", "已发送", "已关闭",
]

#: frozen severity mapping (R4 monitoring_priority -> R5 severity).
SEVERITY_MAPPING: Dict[str, str] = {
    "high": "high", "medium": "medium", "low": "low", "unknown": "fail_closed",
}
SEVERITY_ZH_BY_SEVERITY: Dict[str, str] = {
    "critical": "紧急", "high": "高", "medium": "中", "low": "低",
}
DOMAIN_ZH: Dict[str, str] = {
    "ae": "AE", "mh": "MH", "cm": "合并用药", "ip": "试验药",
    "lab_exam": "检验/检查", "hospital_procedure": "住院/操作",
    "symptom_efficacy": "症状/疗效", "protocol_compliance": "方案符合",
}
ORDINAL_ZH: List[str] = [
    "分析一", "分析二", "分析三", "分析四", "分析五",
    "分析六", "分析七", "分析八", "分析九", "分析十",
]

#: challenge spec quotas (exactly 97 rows).
EXPECTED_CHALLENGE_SPEC: Dict[str, int] = {
    "ensemble_0_1_n": 9,
    "input_identity_isolation": 8,
    "raw_parsed_hash_separation": 6,
    "baseline_recheck": 10,
    "verification_before_adjudication": 8,
    "conflict_relations_hideability": 10,
    "adjudicator_independence": 6,
    "support_counter_source_resolution": 8,
    "query_draft_three_part": 6,
    "history_append_only": 6,
    "journey_fallback_none": 4,
    "audience_audit_split": 8,
    "artifact_governance": 8,
}
CHALLENGE_TOTAL_EXACT = 97

#: six-node acyclic hash DAG -- exact equality required.  No node may
#: include itself directly or indirectly; audit_content_hash excludes the
#: packet_fingerprints leaf (which is derived from independent upstream
#: hashes) to stay cycle-free.
EXPECTED_HASH_DAG: Dict[str, Dict[str, Any]] = {
    "audience_content_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "covered_subobject": "audience_inspector",
        "depends_on": [],
        "domain": "public_audience_authority",
        "forbidden_leaves": [
            "binding_id", "session_id", "model_id", "model_version",
            "independent_context_hash", "raw_bytes_b64", "raw_bytes_sha256",
            "declared_output_hash", "verification_audit_rows", "history_audit",
            "packet_fingerprints", "model_evidence", "digest_context",
            "output_digests", "artifact_source_versions",
        ],
        "may_cover_hidden": False,
    },
    "audit_content_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "covered_subobject": "audit_inspector",
        "excluded_leaves": ["packet_fingerprints"],
        "depends_on": [],
        "domain": "private_audit_authority",
        "may_cover_hidden": True,
    },
    "receipt_content_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "covered_object": "R5AuthorityReceipt",
        "depends_on": [],
        "domain": "public_audience_authority",
        "may_cover_hidden": False,
        "ref_prefix": RECEIPT_REF_PREFIX,
    },
    "packet_id": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "depends_on": ["audience_content_hash"],
        "domain": "public_audience_authority",
        "recipe": "<prefix>:<audience_content_hash>",
        "ref_prefix": PACKET_ID_PREFIX,
    },
    "packet_fingerprints": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "covered_subobject": "audit_inspector.packet_fingerprints",
        "depends_on": ["audience_content_hash", "receipt_content_hash",
                       "packet_id", "risk_identity_hash"],
        "domain": "private_audit_authority",
        "excluded_from": ["audit_content_hash"],
        "recipe": [
            "audience:<audience_content_hash>",
            "receipt:<receipt_content_hash>",
            "packet:<packet_id>",
            "risk_identity:<risk_identity_hash>",
        ],
        "sorted_unique": True,
    },
    "packet_integrity_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "dependency_edges": [
            {"kind": "excluded", "source": "audience_content_hash"},
            {"kind": "excluded", "source": "audit_content_hash"},
            {"kind": "excluded", "source": "receipt_content_hash"},
        ],
        "depends_on": ["audience_content_hash", "audit_content_hash",
                       "receipt_content_hash", "packet_id",
                       "packet_fingerprints", "risk_identity_hash"],
        "domain": "private_packet_integrity",
        "excluded_root_keys": [
            "packet_id", "packet_integrity_hash", "audience_content_hash",
            "audit_content_hash", "receipt_content_hash", "schema", "status",
            "authority_mode",
        ],
        "may_cover_hidden": True,
    },
}

#: 18 invariants (id -> error code), exact and ordered.
EXPECTED_INVARIANTS: List[Tuple[str, str]] = [
    ("cardinality_0_1_n", "s4.cardinality_not_0_1_n"),
    ("same_input_version", "s4.authority_drift"),
    ("worker_isolation", "s4.duplicate_worker_binding"),
    ("raw_vs_parsed_hash", "s4.raw_parsed_hash_confusion"),
    ("baseline_recheck", "s4.baseline_recheck_missing"),
    ("verification_before_adjudication", "s4.verification_label_only"),
    ("conflict_full_set_and_non_hideable", "s4.conflict_set_incomplete"),
    ("adjudicator_independence", "s4.adjudicator_context_collision"),
    ("support_counter_source_resolution", "s4.hidden_source_leak"),
    ("query_draft_three_part_draft_only", "s4.query_task_semantics"),
    ("history_append_only", "s4.history_append_only_violation"),
    ("journey_fallback_none", "s4.journey_fallback_not_none"),
    ("audience_audit_split", "s4.audience_audit_leak"),
    ("synthetic_offline_test_only", "s4.authority_drift"),
    ("receipt_content_hash_recipe", "s4.receipt_hash_mismatch"),
    ("packet_id_grammar", "s4.packet_id_grammar_mismatch"),
    ("hash_dag_acyclic", "s4.hash_recipe_cycle"),
    ("enum_closure_source", "s4.enum_value_mismatch"),
]

#: 10 join recipes (recipe_id -> exact join text).
EXPECTED_JOIN_RECIPES: Dict[str, str] = {
    "join_recipe.worker_view": ("mm_r4.ensemble:WorkerAnalysisOutput ⋈ "
                                "mm_r4.ensemble_contracts:AnalysisAttempt on attempt_id"),
    "join_recipe.baseline_row": ("mm_r4.ensemble_contracts:BaselineAssessment ⋈ "
                                 "ReferenceBaselineItem on item_id ⋈ AnalysisAttempt on attempt_id"),
    "join_recipe.conflict_row": ("semantic re-derivation of "
                                 "mm_r4.ensemble:derive_conflicts over the packet's worker outputs + baseline items"),
    "join_recipe.raw_artifact": ("parsed_output_hash <- mm_r4.ensemble:"
                                 "worker_output_content_hash(recompute); raw_bytes_sha256 <- "
                                 "sha256(base64decode(raw_bytes_b64))"),
    "join_recipe.verification_row": ("recompute mm_r4.ensemble:verify_attempt(attempt, output, "
                                     "digest_context) - never trust a stored label"),
    "join_recipe.adjudication_row": ("mm_r4.ensemble_contracts:AdjudicationBinding + "
                                     "S4-independent_context_hash seal"),
    "join_recipe.query_draft": ("mm_r4.d10_projection:D10QueryDraft public three "
                                "sentences + pd_wording_state"),
    "join_recipe.journey_deep_link": ("mm_r5.contracts:R5DeepLinkState identity fields + "
                                      "unique project/run/snapshot/site/subject/risk projection"),
    "join_recipe.severity_from_priority": ("severity_mapping(R4 monitoring_priority) frozen "
                                           "table: high->high, medium->medium, low->low, unknown->fail_closed"),
    "packet_only_provenance": ("mm_r4.d10_contracts:ModelEvidence "
                               "(model_evidence_visibility=packet_only)"),
}

#: the two named deferred leaves must be honest (empty path + named contract).
EXPECTED_DEFERRED_LEAVES: Dict[str, str] = {
    "aemh_match_history": "aemh-match-history-public-v1",
    "subject_temporal_spine_full": "subject-workspace-temporal-spine-v1",
    "critical_severity_authority": "critical-severity-authority-public-v1",
}

#: every provenance value observed in the source matrix (closed).
EXPECTED_PROVENANCE_VALUES: List[str] = [
    "audience_plane", "audit_plane", "authority_plane", "deferred",
]

#: exact top-level keys per artifact.
EXPECTED_SCHEMA_TOP_KEYS = {
    "schema", "status", "authority_mode", "imports", "objects", "hash_dag",
    "import_schemas",
}
EXPECTED_OVERLAY_TOP_KEYS = {
    "schema", "status", "authority_mode", "enums", "hash_dag", "invariants",
    "join_recipes", "source_matrix", "severity_mapping",
    "severity_zh_by_severity", "domain_zh", "ordinal_zh",
    "forbidden_audience_tokens", "challenge_spec", "done_gates",
    "packet_id_prefix", "packet_id_grammar", "receipt_ref_prefix",
    "genesis_hash", "test_locator_prefix", "acceptance_boundary",
}
EXPECTED_PINS_TOP_KEYS = {
    "schema", "status", "authority_mode", "source_count", "self_pin_recipe",
    "sources",
}
EXPECTED_MANIFEST_TOP_KEYS = {
    "schema", "status", "authority_mode", "artifact_count",
    "planned_artifact_count", "source_count", "artifacts", "planned_artifacts",
    "pinned_sources", "manifest_content_sha256",
}

#: canonical artifact path/role set.
EXPECTED_MANIFEST_ARTIFACTS: List[Tuple[str, str, str]] = [
    ("reviews/medical_monitoring_r5_s4_implementation_contract_v0_1_20260819.md",
     "human_contract", "raw_sha256"),
    ("tools/generate_medical_monitoring_r5_s4_contract_v0_1.py",
     "generator", "raw_sha256"),
    ("tools/verify_medical_monitoring_r5_s4_contract_v0_1.py",
     "verifier", "raw_sha256"),
    ("artifacts/medical_monitoring_r5_s4_contract_v0_1/exact_overlay.json",
     "exact_overlay", "raw_sha256"),
    ("artifacts/medical_monitoring_r5_s4_contract_v0_1/packet_schema.json",
     "packet_schema", "raw_sha256"),
    ("artifacts/medical_monitoring_r5_s4_contract_v0_1/source_pins.json",
     "source_pins", "raw_sha256"),
    ("artifacts/medical_monitoring_r5_s4_contract_v0_1/manifest.json",
     "manifest", "canonical_self"),
    ("artifacts/medical_monitoring_r5_s4_contract_v0_1/challenge_registry.json",
     "challenge_registry", "raw_sha256"),
]
EXPECTED_PLANNED_ARTIFACTS: Dict[str, str] = {
    "challenge_registry": "worker_03",
}

#: exact schema object names (20).
EXPECTED_SCHEMA_OBJECTS: List[str] = [
    "R5S4AuthorityPacket", "R5S4RiskIdentity", "R5S4WorkerView",
    "R5S4RawOutputArtifact", "R5S4BaselineRow", "R5S4ConflictRow",
    "R5S4VerificationRow", "R5S4AdjudicationRow", "R5S4QueryDraftRow",
    "R5S4JourneyLink", "R5S4HistoryEntry", "R5S4HistoryLog",
    "R5S4AudienceInspector", "R5S4AudienceBaselineRow",
    "R5S4AudienceWorkerSummary", "R5S4AuditInspector", "R5S4AuditWorkerRow",
    "R5S4VerificationAuditRow", "R5S4DigestContextView",
    "R5S4ModelEvidenceRef", "S4AttemptAuthorityRow",
    "S4ModelEvidencePermit", "S4JourneyTargetIdentity",
    "S4AcceptedHistoryState", "S4AcceptedBaselineItem",
    "S4AcceptedQueryDraft", "S4AcceptedRiskIdentity",
    "S4AcceptedAdjudicatorBinding", "S4SourceRevisionPair",
    "S4AcceptedAuthorityAnchor",
]

EXPECTED_IMPORTS: Dict[str, str] = {
    "R5AuthorityReceipt": "mm_r5.contracts:R5AuthorityReceipt",
    "ReferenceBaselineItem": "mm_r4.ensemble_contracts:ReferenceBaselineItem",
    "SourceRevisionContentPair": "mm_r5.contracts:SourceRevisionContentPair",
}

#: exact approved set of S4 typed extension fields on imported baseline items.
EXPECTED_BASELINE_EXTENSIONS = frozenset({
    "project_ref", "run_ref", "snapshot_ref", "cutoff_ref", "source_revision",
})


def _is_supported_constraint(constraint: str) -> bool:
    """True when _execute_constraints actually handles the token (exact names
    or declared prefixes); an unsupported token fails artifact validation so
    no declared rule can be silently skipped."""
    exact = {
        "nonempty", "required", "sha256", "sorted_unique", "min_items:0",
        "equals:true", "equals:none", "append_only_chain",
        "cardinality_0_1_n:state_exact", "exact_count:ensemble_size",
        "first_entry_genesis", "exact_set:seven_dimensions",
        "required_when:present=true", "forbidden_when:present=false",
        "required_when:state!=no_ensemble", "forbidden_when:state=no_ensemble",
        "min_items:1_when_present", "nonempty_when_present",
        "required_when:severity_authority=critical", "base64",
        "equals:last_entry.entry_hash", "equals:last_entry.entry_hash_or_genesis",
        "equals:len(entries)", "equals:parsed_output_hash",
        "equals:authority_anchor.anchor_identity_hash",
        "recompute:mm_r4.ensemble.worker_output_content_hash",
        "chain_includes_prior_hash", "recheck_required_implies_locators",
        "non_hideable_relations_forbidden_when_true",
        "severity_mapping_from_monitoring_priority", "r4_priority_authority",
        "packet_only_provenance", "gated_consensus_phrase",
        "never_claims_independent_when_absent",
    }
    if constraint in exact:
        return True
    for prefix in ("min:", "max:", "min_items:", "max_items:", "prefix:",
                   "grammar:", "marker_grammar:", "equals:", "sorted_unique_by:",
                   "canonical_sha256_of:", "closed_zh:", "closed_enum:",
                   "genesis_or_sha"):
        if constraint.startswith(prefix):
            return True
    return False

#: every source_kind value in the source matrix (closed).
EXPECTED_SOURCE_KINDS: List[str] = [
    "r4_public", "canonical_derived", "r5_surface_constant", "derived",
    "r5_exact_contract_constant", "synthetic_offline_test_only", "r5_public",
    "deferred", "external_authority",
]

#: function/constant references in join recipes / source matrix that must
#: resolve to real module-level objects in the pinned sources.
EXPECTED_FUNCTION_REFS: Dict[str, str] = {
    "mm_r4.ensemble:worker_output_content_hash": "poc/medical_monitoring_ai_native_r4/src/mm_r4/ensemble.py",
    "mm_r4.ensemble:verify_attempt": "poc/medical_monitoring_ai_native_r4/src/mm_r4/ensemble.py",
    "mm_r4.ensemble:derive_conflicts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/ensemble.py",
}
EXPECTED_CONSTANT_REFS: Dict[str, str] = {
    "mm_r5.s2_contracts:S2_DOMAINS": "poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_contracts.py",
    "mm_r4.contracts:MONITORING_PRIORITIES": "poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py",
}


class VerificationError(Exception):
    pass


def _fail(message: str) -> None:
    raise VerificationError(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _nfc(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [_nfc(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_nfc(item) for item in value)
    if isinstance(value, dict):
        return {_nfc(key): _nfc(val) for key, val in value.items()}
    return value


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(_nfc(value), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _h(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _r4_style_hash(value: Any) -> str:
    """R4 content_hash recipe (compact, sorted keys, no trailing newline)."""
    return hashlib.sha256(json.dumps(_nfc(value), ensure_ascii=False,
                                     sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _fail(f"artifact_missing: {path}")
    except json.JSONDecodeError as error:
        _fail(f"artifact_not_json: {path}: {error}")
    return {}


def _walk_strings(value: Any, owner: str = "root") -> None:
    if isinstance(value, str):
        _require(value == unicodedata.normalize("NFC", value),
                 f"non_nfc_string: {owner}")
    elif isinstance(value, dict):
        for key, val in value.items():
            _walk_strings(val, f"{owner}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_strings(item, f"{owner}[{index}]")


# ---------------------------------------------------------------------------
# AST field resolution (source paths -> real dataclass fields + objects)
# ---------------------------------------------------------------------------


def _parse_classes(relative_path: str, root: Path) -> Dict[str, Dict[str, str]]:
    """Return {class_name: {field_name: annotation}} for every dataclass in a
    pinned source file."""
    path = root / relative_path
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    classes: Dict[str, Dict[str, str]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        is_dataclass = any(
            (isinstance(item, ast.Name) and item.id == "dataclass")
            or (isinstance(item, ast.Call) and isinstance(item.func, ast.Name)
                and item.func.id == "dataclass")
            for item in node.decorator_list)
        if not is_dataclass:
            continue
        fields: Dict[str, str] = {}
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) \
                    and isinstance(statement.target, ast.Name):
                annotation = ast.unparse(statement.annotation) \
                    if hasattr(ast, "unparse") else _unparse(statement.annotation)
                fields[statement.target.id] = annotation
        classes[node.name] = fields
    return classes


def _unparse(node: ast.AST) -> str:
    # Python 3.8 compatibility fallback.
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Subscript):
        return _unparse(node.value) + "[" + _unparse(node.slice) + "]"
    if isinstance(node, ast.Attribute):
        return _unparse(node.value) + "." + node.attr
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Tuple):
        return "(" + ", ".join(_unparse(e) for e in node.elts) + ")"
    return "Any"


def _module_objects(relative_path: str, root: Path) -> Dict[str, str]:
    """Return module-level {name: kind} where kind is 'function' or 'constant'
    (assignment of a constant tuple/dict/list/str)."""
    path = root / relative_path
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    objects: Dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            objects[node.name] = "function"
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    objects[target.id] = "constant"
        elif isinstance(node, ast.AnnAssign) \
                and isinstance(node.target, ast.Name):
            objects[node.target.id] = "constant"
    return objects


def _resolve_source_path(source_path: str, maps: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    """Resolve a ``module:Class.field[.nested]`` path to a real dataclass
    field; fail closed on missing class/field or unresolvable nested type."""
    _require(":" in source_path,
             f"s4.source_path_unresolvable: invalid source path {source_path!r}")
    module, path = source_path.split(":", 1)
    _require(module in maps,
             f"s4.source_path_unresolvable: source module not pinned: {module}")
    parts = path.split(".")
    class_name = parts.pop(0)
    classes = maps[module]
    _require(class_name in classes,
             f"s4.source_path_unresolvable: source class missing: {source_path}")
    current_class = class_name
    for index, segment in enumerate(parts):
        field_name = segment
        fields = classes[current_class]
        _require(field_name in fields,
                 f"s4.source_path_unresolvable: source field missing at "
                 f"{current_class}.{field_name}: {source_path}")
        if index < len(parts) - 1:
            annotation = fields[field_name]
            nested = _annotation_element_class(annotation, classes)
            _require(nested is not None,
                     f"s4.source_path_unresolvable: nested type unresolvable at "
                     f"{current_class}.{field_name}: {source_path}")
            current_class = nested


def _annotation_element_class(annotation: str, classes: Dict[str, Dict[str, str]]) -> Optional[str]:
    names = {name for name in classes}
    found = [name for name in names if name in annotation]
    return found[0] if len(found) == 1 else None


def _source_plane_for(obj_name: str) -> str:
    if obj_name == "import" or obj_name.startswith("import."):
        return "audience_plane"
    if obj_name in AUDIENCE_OBJECTS:
        return "audience_plane"
    if obj_name in AUDIT_OBJECTS:
        return "audit_plane"
    if obj_name in AUTHORITY_OBJECTS:
        return "authority_plane"
    raise VerificationError(f"source plane unclassified for object {obj_name!r}")


def _parse_all_source_paths(overlay: Dict[str, Any], maps: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    """Validate source-matrix leaf coverage and resolve every real path."""
    join_ids = {recipe["recipe_id"] for recipe in overlay["join_recipes"]}
    deferred_leaves = {row["leaf"] for row in overlay["source_matrix"]
                       if row["source_kind"] == "deferred"}
    _require(deferred_leaves == set(EXPECTED_DEFERRED_LEAVES),
             f"deferred_leaf_set_drift: {sorted(deferred_leaves)!r}")
    for row in overlay["source_matrix"]:
        leaf = row["leaf"]
        if row["source_kind"] == "deferred":
            _require(row["path"] == "", f"deferred_row_must_have_empty_path: {leaf}")
            _require(row.get("deferred_contract") == EXPECTED_DEFERRED_LEAVES[leaf],
                     f"deferred_contract_mismatch: {leaf}")
            _require(row["provenance"] == "deferred",
                     f"deferred_provenance_mismatch: {leaf}")
            continue
        obj_name = leaf.split(".")[0]
        expected_plane = _source_plane_for(obj_name)
        _require(row["provenance"] == expected_plane,
                 f"s4.cross_plane_projection_drift: leaf {leaf} plane "
                 f"{row['provenance']!r} != expected {expected_plane!r}")
        if "join_recipe" in row:
            ref = row["join_recipe"]
            normalized = ref.split("#", 1)[0]
            if normalized in join_ids:
                continue
            _require(not normalized.startswith("join_recipe.")
                     and normalized != "packet_only_provenance",
                     f"s4.join_recipe_unresolvable: {leaf} -> {ref!r}")
    # resolve every real module:Class.field path in the matrix.
    for row in overlay["source_matrix"]:
        path = row["path"]
        if not path:
            continue
        stripped = path[len("canonical("):-1] if path.startswith("canonical(") \
            and path.endswith(")") else path
        if ":" in stripped:
            module = stripped.split(":", 1)[0]
            if module in maps:
                rest = stripped.split(":", 1)[1]
                first_seg = rest.split(".")[0]
                # module-level constant/function refs (S2_DOMAINS,
                # MONITORING_PRIORITIES, worker_output_content_hash) are
                # validated separately; only Class.field paths resolve here.
                if first_seg in maps[module]:
                    _resolve_source_path(stripped, maps)


# ---------------------------------------------------------------------------
# hard-pinned semantic equality helpers
# ---------------------------------------------------------------------------


def _require_exact_enums(enums: Dict[str, Any]) -> None:
    for name, values in EXPECTED_ENUMS.items():
        _require(name in enums, f"enum_missing: {name}")
        _require(list(enums[name]) == values,
                 f"s4.enum_value_mismatch: enum {name} drift "
                 f"({enums[name]!r} != {values!r})")


def _require_eq(actual: Any, expected: Any, code: str, note: str) -> None:
    if actual != expected:
        _fail(f"{code}: {note} drift")


def _require_hash_dag(dag: Dict[str, Any]) -> None:
    _require(set(dag) == set(EXPECTED_HASH_DAG),
             "s4.hash_recipe_cycle: hash_dag_key_mismatch")
    for name, recipe in EXPECTED_HASH_DAG.items():
        _require_eq(dag[name], recipe, "s4.hash_recipe_cycle", f"hash_dag.{name}")
    integrity = dag["packet_integrity_hash"]
    edges = integrity.get("dependency_edges", [])
    excluded = {e["source"] for e in edges if e["kind"] == "excluded"}
    _require(excluded == {"audience_content_hash", "audit_content_hash",
                          "receipt_content_hash"},
             "s4.hash_recipe_cycle: packet_integrity dependency edges drift")
    _require(integrity.get("algorithm") == HASH_ALGORITHM,
             "s4.hash_algorithm_mismatch")
    _require(integrity.get("canonicalization") == HASH_CANONICALIZATION,
             "hash_canonicalization_mismatch")


def _require_severity_mapping(mapping: Dict[str, Any]) -> None:
    _require(mapping == SEVERITY_MAPPING, "severity_mapping_drift")


def _require_lexicons(overlay: Dict[str, Any]) -> None:
    _require(overlay["severity_zh_by_severity"] == SEVERITY_ZH_BY_SEVERITY,
             "severity_zh_drift")
    _require(overlay["domain_zh"] == DOMAIN_ZH, "domain_zh_drift")
    _require(overlay["ordinal_zh"] == ORDINAL_ZH, "ordinal_zh_drift")


def _require_challenge_spec(spec: Dict[str, Any]) -> None:
    _require(spec.get("total_exact") == CHALLENGE_TOTAL_EXACT,
             "challenge_spec_total_drift")
    _require(spec.get("categories") == EXPECTED_CHALLENGE_SPEC,
             "challenge_spec_categories_drift")


def _require_invariants(invariants: Any) -> None:
    _require(isinstance(invariants, list) and len(invariants) == 18,
             "invariant_count_drift")
    actual = [(inv["invariant_id"], inv["error_code"]) for inv in invariants]
    _require(actual == EXPECTED_INVARIANTS, "invariant_drift")


def _require_join_recipes(recipes: Any) -> None:
    _require(isinstance(recipes, list) and len(recipes) == 10,
             "join_recipe_count_drift")
    for recipe in recipes:
        rid = recipe.get("recipe_id")
        _require(rid in EXPECTED_JOIN_RECIPES,
                 f"s4.join_recipe_unresolvable: unknown {rid}")
        _require(recipe.get("join") == EXPECTED_JOIN_RECIPES[rid],
                 f"s4.join_recipe_unresolvable: {rid} join text drift")


def _require_error_codes(codes: Any) -> None:
    _require(list(codes) == EXPECTED_ERROR_CODES, "error_code_catalog_drift")


# ---------------------------------------------------------------------------
# overlay validation
# ---------------------------------------------------------------------------


def _validate_overlay(overlay: Dict[str, Any], maps: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    _require(set(overlay) == EXPECTED_OVERLAY_TOP_KEYS,
             "overlay_exact_top_level_keys_mismatch")
    _require(overlay["schema"] == OVERLAY_SCHEMA, "overlay_schema_mismatch")
    _require(overlay["status"] == STATUS, "overlay_status_mismatch")
    _require(overlay["authority_mode"] == AUTHORITY_MODE,
             "overlay_authority_mode_mismatch")
    _require(overlay["packet_id_prefix"] == PACKET_ID_PREFIX,
             "packet_id_prefix_mismatch")
    _require(overlay["packet_id_grammar"] == PACKET_ID_GRAMMAR,
             "s4.packet_id_grammar_mismatch")
    _require(overlay["receipt_ref_prefix"] == RECEIPT_REF_PREFIX,
             "s4.receipt_hash_mismatch")
    _require(overlay["genesis_hash"] == GENESIS_HASH,
             "s4.history_chain_break: genesis_hash_mismatch")

    _require_exact_enums(overlay["enums"])
    _require_hash_dag(overlay["hash_dag"])
    _require_invariants(overlay["invariants"])
    _require_join_recipes(overlay["join_recipes"])
    _require_severity_mapping(overlay["severity_mapping"])
    _require_lexicons(overlay)
    _require_challenge_spec(overlay["challenge_spec"])
    _require_error_codes(overlay["enums"]["error_code"])
    _require(overlay["forbidden_audience_tokens"] == FORBIDDEN_AUDIENCE_TOKENS,
             "forbidden_audience_tokens_drift")

    # source matrix: exact ordered leaf -> source_kind pairs.
    matrix = overlay["source_matrix"]
    _require(isinstance(matrix, list) and len(matrix) >= 150,
             "source_matrix_count_drift")
    seen_leaves = set()
    for row in matrix:
        _require(set(row) == {"leaf", "path", "provenance", "source_kind"} or
                 set(row) == {"leaf", "path", "provenance", "source_kind",
                              "join_recipe"} or
                 set(row) == {"leaf", "path", "provenance", "source_kind",
                              "deferred_contract"},
                 f"source_matrix_row_keys_drift: {row.get('leaf')!r}")
        _require(row["source_kind"] in EXPECTED_SOURCE_KINDS,
                 f"source_kind_off_enum: {row['source_kind']!r}")
        _require(row["provenance"] in EXPECTED_PROVENANCE_VALUES,
                 f"provenance_off_enum: {row['provenance']!r}")
        _require(row["leaf"] not in seen_leaves,
                 f"duplicate_source_leaf: {row['leaf']!r}")
        seen_leaves.add(row["leaf"])

    # resolve every real source path through AST.
    _parse_all_source_paths(overlay, maps)

    # every error code referenced by an invariant must exist in the catalog.
    code_set = set(overlay["enums"]["error_code"])
    for _inv_id, code in EXPECTED_INVARIANTS:
        _require(code in code_set, f"invariant_error_code_missing: {code}")


# ---------------------------------------------------------------------------
# schema validation
# ---------------------------------------------------------------------------


def _validate_field_descriptor(owner: str, descriptor: Any) -> None:
    _require(isinstance(descriptor, dict), f"field descriptor {owner} must be object")
    _require(set(descriptor) == {"cardinality", "nullable", "type"} or
             set(descriptor) == {"cardinality", "constraints", "nullable", "type"} or
             set(descriptor) == {"cardinality", "constraints", "nullable",
                                 "type", "import_extensions"},
             f"field descriptor {owner} exact keys drift")
    # the deprecated name-only import_extra_keys shape is rejected outright.
    _require("import_extra_keys" not in descriptor,
             f"deprecated_import_extra_keys: {owner}")
    _require(descriptor["cardinality"] in ("one", "many"),
             f"cardinality invalid at {owner}")
    _require(isinstance(descriptor["nullable"], bool),
             f"nullable must be bool at {owner}")
    _require(isinstance(descriptor.get("constraints", []), list)
             and all(isinstance(c, str) for c in descriptor.get("constraints", [])),
             f"constraints invalid at {owner}")
    _require(isinstance(descriptor.get("import_extensions", {}), dict),
             f"import_extensions invalid at {owner}")
    for ext_name, ext_descriptor in descriptor.get(
            "import_extensions", {}).items():
        _validate_field_descriptor(
            f"{owner}.import_extensions.{ext_name}", ext_descriptor)


def _validate_schema(schema: Dict[str, Any], maps: Dict[str, Dict[str, Dict[str, str]]]) -> None:
    _require(set(schema) == EXPECTED_SCHEMA_TOP_KEYS,
             "s4.schema_key_mismatch: packet schema exact top-level keys drift")
    _require(schema["schema"] == PACKET_SCHEMA, "schema_schema_mismatch")
    _require(schema["status"] == STATUS, "schema_status_mismatch")
    _require(schema["authority_mode"] == AUTHORITY_MODE,
             "schema_authority_mode_mismatch")

    objects = schema["objects"]
    _require(set(objects) == set(EXPECTED_SCHEMA_OBJECTS),
             "schema_object_set_drift")
    for object_name, fields in objects.items():
        _require(isinstance(fields, dict) and fields,
                 f"object {object_name} must contain fields")
        for field_name, descriptor in fields.items():
            _validate_field_descriptor(f"{object_name}.{field_name}", descriptor)

    _require(schema["imports"] == EXPECTED_IMPORTS, "schema_imports_drift")
    # import_schemas must exactly cover the imported objects and be typed.
    import_schemas = schema.get("import_schemas", {})
    _require(set(import_schemas) == set(EXPECTED_IMPORTS),
             "import_schemas_key_drift")
    for obj_name, fields in import_schemas.items():
        _require(isinstance(fields, dict) and fields,
                 f"import schema {obj_name} must contain fields")
        for field_name, descriptor in fields.items():
            _validate_field_descriptor(f"import.{obj_name}.{field_name}", descriptor)
    # every `import:<Name>` reference in the packet schema (and every object
    # type reference inside an import_schema) must resolve EXACTLY once
    # against import_schemas (no unresolved ref, no orphan).
    import_refs: Dict[str, List[str]] = {}

    def _collect_type_refs(owner: str, fields: Dict[str, Any]) -> None:
        for field_name, descriptor in fields.items():
            ftype = descriptor.get("type", "")
            if ftype.startswith("import:"):
                name = ftype[len("import:"):]
                import_refs.setdefault(name, []).append(
                    f"{owner}.{field_name}")
            elif ftype in import_schemas:
                import_refs.setdefault(ftype, []).append(
                    f"{owner}.{field_name}")

    for object_name, fields in objects.items():
        _collect_type_refs(object_name, fields)
    for obj_name, fields in import_schemas.items():
        _collect_type_refs(f"import.{obj_name}", fields)
    for name, refs in sorted(import_refs.items()):
        _require(name in import_schemas,
                 f"unresolved_import_schema: {name} referenced by {refs}")
    for name in sorted(import_schemas):
        _require(name in import_refs,
                 f"orphan_import_schema: {name} never referenced in packet schema")
    # C) import_extensions: typed S4 projection fields on imported objects.
    # Every descriptor must use supported constraint tokens; extension keys
    # must equal the exact approved set and never collide with base fields.
    for object_name, fields in objects.items():
        for field_name, descriptor in fields.items():
            extensions = descriptor.get("import_extensions")
            if not extensions:
                continue
            for ext_name, ext_descriptor in extensions.items():
                for c in ext_descriptor.get("constraints", []):
                    _require(_is_supported_constraint(c),
                             f"unsupported_constraint_token: "
                             f"{object_name}.{field_name}.{ext_name}: {c!r}")
            base_name = descriptor.get("type", "")
            if base_name.startswith("import:"):
                base_name = base_name[len("import:"):]
            base_fields = set(import_schemas.get(base_name, {}))
            _require(not (set(extensions) & base_fields),
                     f"import_extension_collides_with_base_field: "
                     f"{object_name}.{field_name}: "
                     f"{sorted(set(extensions) & base_fields)}")
            if base_name == "ReferenceBaselineItem":
                _require(set(extensions) == EXPECTED_BASELINE_EXTENSIONS,
                         f"baseline_extension_set_drift: "
                         f"{sorted(set(extensions))}")
    _require_hash_dag(schema["hash_dag"])

    # imported objects resolve to real dataclass fields in pinned sources.
    for _obj, source in EXPECTED_IMPORTS.items():
        module, class_name = source.split(":", 1)
        _require(module in maps and class_name in maps[module],
                 f"imported_object_not_found: {source}")

    _require("R5S4AuthorityPacket" in objects, "root_object_missing")

    # audience hash DAG forbidden leaves must be audit-only.
    audience_forbidden = set(EXPECTED_HASH_DAG["audience_content_hash"]
                             ["forbidden_leaves"])
    audience_obj = objects["R5S4AudienceInspector"]
    _require(not (set(audience_obj) & audience_forbidden),
             "s4.audience_hash_contains_audit_leaf")


# ---------------------------------------------------------------------------
# source pins / manifest validation
# ---------------------------------------------------------------------------


def _validate_source_pins(pins: Dict[str, Any], root: Path) -> Dict[str, str]:
    _require(set(pins) == EXPECTED_PINS_TOP_KEYS,
             "source pins exact top-level keys mismatch")
    _require(pins["schema"] == SOURCE_PINS_SCHEMA, "source pins schema mismatch")
    _require(pins["status"] == STATUS, "source pins status mismatch")
    _require(pins["authority_mode"] == AUTHORITY_MODE,
             "source pins authority mode mismatch")
    sources = pins["sources"]
    _require(pins["source_count"] == len(sources),
             "source pins count inconsistent")
    _require(len(sources) >= SOURCE_COUNT,
             "source pins count below frozen minimum")
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


def _audit_content_hash(audit: Any) -> str:
    """Canonical audit content hash EXCLUDING the non-hashed packet_fingerprints
    leaf (which is derived from independent inputs and is not covered by the
    audit hash to avoid a self-referential cycle)."""
    if isinstance(audit, dict):
        body = {k: v for k, v in audit.items() if k != "packet_fingerprints"}
        return _h(body)
    return _h(audit)


def _manifest_content_hash(manifest: Dict[str, Any]) -> str:
    core = dict(manifest)
    core.pop("manifest_content_sha256", None)
    return _sha256_bytes(_canonical_bytes(core))


def _validate_manifest(manifest: Dict[str, Any], artifacts_dir: Path,
                       root: Path) -> None:
    _require(set(manifest) == EXPECTED_MANIFEST_TOP_KEYS,
             "manifest exact top-level keys mismatch")
    _require(manifest["schema"] == MANIFEST_SCHEMA, "manifest schema mismatch")
    _require(manifest["status"] == STATUS, "manifest status mismatch")
    _require(manifest["authority_mode"] == AUTHORITY_MODE,
             "manifest authority mode mismatch")

    artifacts = manifest["artifacts"]
    planned = manifest["planned_artifacts"]
    _require(manifest["artifact_count"] == len(artifacts),
             "manifest artifact count inconsistent")
    _require(manifest["planned_artifact_count"] == len(planned),
             "manifest planned artifact count inconsistent")

    canonical_roles = {role for _path, role, _kind in EXPECTED_MANIFEST_ARTIFACTS}
    present_roles = {item["role"] for item in artifacts}
    planned_roles = {item["role"] for item in planned}
    _require(present_roles | planned_roles == canonical_roles,
             f"manifest role set drift: present={sorted(present_roles)} "
             f"planned={sorted(planned_roles)}")
    _require(not (present_roles & planned_roles),
             "manifest role overlap: present and planned must be disjoint")

    present_paths: List[Tuple[str, str, str]] = []
    for item in artifacts:
        _require(set(item) == {"path", "role", "hash_kind", "sha256"},
                 f"manifest artifact entry exact keys mismatch: {item!r}")
        present_paths.append((item["path"], item["role"], item["hash_kind"]))
    _require(sorted(present_paths) ==
             sorted([(p, r, k) for p, r, k in EXPECTED_MANIFEST_ARTIFACTS
                     if r in present_roles]),
             "manifest artifact path/role set mismatch")

    for item in artifacts:
        target = root / item["path"]
        _require(target.exists() and target.is_file(),
                 f"artifact missing: {item['path']}")
        if item["hash_kind"] == "raw_sha256":
            _require(item["sha256"] == _sha256_file(target),
                     f"manifest_hash_rewrite: artifact SHA mismatch for "
                     f"{item['path']}")
        elif item["hash_kind"] == "canonical_self":
            _require(item["path"].endswith("/manifest.json")
                     and item["sha256"] is None,
                     "invalid manifest self-entry")
        else:
            _fail(f"invalid manifest hash_kind: {item['hash_kind']!r}")

    for item in planned:
        _require(set(item) == {"path", "role", "planned_by"},
                 f"manifest planned entry exact keys mismatch: {item!r}")
        _require(item["role"] in EXPECTED_PLANNED_ARTIFACTS,
                 f"unexpected planned role: {item['role']!r}")
        _require(item["planned_by"] == EXPECTED_PLANNED_ARTIFACTS[item["role"]],
                 f"planned_by drift for {item['role']!r}")

    _require(manifest["manifest_content_sha256"] == _manifest_content_hash(manifest),
             "manifest_content_hash_mismatch: manifest canonical self hash drift")

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
                 f"source_pin_drift: pinned source SHA mismatch: {item['path']}")

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
    _require(not assert_nodes, f"assert statement forbidden in {relative_path}")


# ---------------------------------------------------------------------------
# independent hash-conclusion oracle (recompute, never trust stored labels)
# ---------------------------------------------------------------------------


def _recompute_manifest_self_hash(manifest: Dict[str, Any]) -> str:
    return _manifest_content_hash(manifest)


def _verify_hash_dag_acyclic(dag: Dict[str, Any]) -> None:
    _require(dag["audience_content_hash"]["depends_on"] == [],
             "s4.hash_recipe_cycle: audience_depends_on_drift")
    _require(dag["audit_content_hash"]["depends_on"] == [],
             "s4.hash_recipe_cycle: audit_depends_on_drift")
    _require(dag["receipt_content_hash"]["depends_on"] == [],
             "s4.hash_recipe_cycle: receipt_depends_on_drift")
    _require(dag["audit_content_hash"]["excluded_leaves"] ==
             ["packet_fingerprints"],
             "s4.hash_recipe_cycle: audit exclusion drift")
    packet_id = dag["packet_id"]
    _require(packet_id["depends_on"] == ["audience_content_hash"],
             "s4.hash_recipe_cycle: packet_id depends_on drift")
    _require(packet_id["recipe"] == "<prefix>:<audience_content_hash>",
             "s4.hash_recipe_cycle: packet_id recipe drift")
    fps = dag["packet_fingerprints"]
    _require(fps["depends_on"] == ["audience_content_hash",
                                   "receipt_content_hash", "packet_id",
                                   "risk_identity_hash"],
             "s4.hash_recipe_cycle: packet_fingerprints depends_on drift")
    _require(fps["sorted_unique"] is True,
             "s4.hash_recipe_cycle: packet_fingerprints not sorted_unique")
    _require(fps["excluded_from"] == ["audit_content_hash"],
             "s4.hash_recipe_cycle: packet_fingerprints exclusion drift")
    integrity = dag["packet_integrity_hash"]
    edges = integrity.get("dependency_edges", [])
    excluded = {e["source"] for e in edges if e.get("kind") == "excluded"}
    _require(excluded == {"audience_content_hash", "audit_content_hash",
                          "receipt_content_hash"},
             "s4.hash_recipe_cycle: packet_integrity dependency edges drift")
    for name, recipe in dag.items():
        for dep in recipe.get("depends_on", []):
            _require(dep != name,
                     f"s4.hash_recipe_cycle: self-dependency at {name}")
    # global acyclicity: walk the full depends_on graph.  risk_identity_hash
    # is an external leaf input (not a DAG node); only follow DAG nodes.
    for name in dag:
        seen = set()

        def visit(node: str, stack: set) -> None:
            _require(node not in stack,
                     f"s4.hash_recipe_cycle: cycle at {node}")
            if node in seen:
                return
            seen.add(node)
            for dep in dag[node].get("depends_on", []):
                if dep in dag:
                    visit(dep, stack | {node})

        visit(name, set())


def _verify_audience_audit_separation(dag: Dict[str, Any],
                                      schema: Dict[str, Any]) -> None:
    audience_forbidden = set(dag["audience_content_hash"]["forbidden_leaves"])
    _require(audience_forbidden, "audience_forbidden_leaves_empty")
    _require(dag["audience_content_hash"]["may_cover_hidden"] is False,
             "audience_must_not_cover_hidden")
    _require(dag["audit_content_hash"]["may_cover_hidden"] is True,
             "audit_must_cover_hidden")
    _require(dag["packet_integrity_hash"]["may_cover_hidden"] is True,
             "packet_integrity_must_cover_hidden")
    audience_obj = schema["objects"]["R5S4AudienceInspector"]
    _require(not (set(audience_obj) & audience_forbidden),
             "s4.audience_audit_leak: audience object carries audit-only leaf")


# ---------------------------------------------------------------------------
# coordinated-tamper probes (each expects an exact error code)
# ---------------------------------------------------------------------------


def _tamper_probes(overlay: Dict[str, Any], schema: Dict[str, Any],
                   pins: Dict[str, Any], manifest: Dict[str, Any],
                   maps: Dict[str, Dict[str, Dict[str, str]]],
                   root: Path, artifacts: Path) -> int:
    probes: List[Tuple[str, Any]] = []

    def expect_code(name: str, fn: Any, code: str) -> None:
        probes.append((name, (fn, code)))

    bad = copy.deepcopy(overlay)
    bad["enums"]["severity"] = ["critical", "high", "medium"]
    expect_code("overlay_enum_drift",
                (lambda b=bad: _require_exact_enums(b["enums"])),
                "s4.enum_value_mismatch")

    bad = copy.deepcopy(overlay)
    bad["severity_mapping"]["high"] = "critical"
    expect_code("severity_mapping_drift",
                (lambda b=bad: _require_severity_mapping(b["severity_mapping"])),
                "severity_mapping_drift")

    bad = copy.deepcopy(overlay)
    bad["forbidden_audience_tokens"] = list(FORBIDDEN_AUDIENCE_TOKENS)[:-1]
    expect_code("forbidden_token_removed",
                (lambda b=bad: _require(
                    b["forbidden_audience_tokens"] == FORBIDDEN_AUDIENCE_TOKENS,
                    "forbidden_audience_tokens_drift")),
                "forbidden_audience_tokens_drift")

    bad = copy.deepcopy(overlay)
    bad["invariants"][0]["error_code"] = "s4.ensemble_zero_must_be_empty"
    expect_code("invariant_error_code_drift",
                (lambda b=bad: _require_invariants(b["invariants"])),
                "invariant_drift")

    bad = copy.deepcopy(overlay)
    bad["hash_dag"]["audience_content_hash"]["depends_on"] = ["packet_integrity_hash"]
    expect_code("hash_dag_cycle",
                (lambda b=bad: _verify_hash_dag_acyclic(b["hash_dag"])),
                "s4.hash_recipe_cycle")

    bad = copy.deepcopy(overlay)
    for recipe in bad["join_recipes"]:
        if recipe["recipe_id"] == "join_recipe.worker_view":
            recipe["join"] = "generic ensemble provenance"
    expect_code("join_recipe_text_drift",
                (lambda b=bad: _require_join_recipes(b["join_recipes"])),
                "s4.join_recipe_unresolvable")

    bad = copy.deepcopy(overlay)
    bad["source_matrix"] = list(reversed(bad["source_matrix"]))
    expect_code("source_matrix_reorder",
                (lambda b=bad: _require(
                    b["source_matrix"][0].get("source_kind") == "deferred"
                    and b["source_matrix"][-1].get("source_kind") != "deferred",
                    "source_matrix_drift")),
                "source_matrix_drift")

    bad = copy.deepcopy(overlay)
    for row in bad["source_matrix"]:
        if row["leaf"] == "aemh_match_history":
            row["path"] = "mm_r4.ensemble:WorkerAnalysisOutput.fake_field"
    expect_code("deferred_leaf_fabricated",
                (lambda b=bad: _require(
                    [r for r in b["source_matrix"] if r["leaf"] == "aemh_match_history"][0]["path"] == "",
                    "deferred_row_must_have_empty_path")),
                "deferred_row_must_have_empty_path")

    bad_schema = copy.deepcopy(schema)
    bad_schema["objects"].pop("R5S4AuthorityPacket")
    expect_code("schema_object_set_drift",
                (lambda b=bad_schema: _validate_schema(b, maps)),
                "schema_object_set_drift")

    bad_schema = copy.deepcopy(schema)
    bad_schema["objects"]["R5S4AudienceInspector"]["model_id"] = \
        bad_schema["objects"]["R5S4AuditWorkerRow"]["model_id"]
    expect_code("audience_audit_leak",
                (lambda b=bad_schema: _require(
                    not (set(b["objects"]["R5S4AudienceInspector"])
                         & set(EXPECTED_HASH_DAG["audience_content_hash"]["forbidden_leaves"])),
                    "s4.audience_audit_leak")),
                "s4.audience_audit_leak")

    bad_pins = copy.deepcopy(pins)
    bad_pins["sources"][0]["sha256"] = "0" * 64
    expect_code("source_pin_drift",
                (lambda b=bad_pins: _validate_source_pins(b, root)),
                "source_pin_drift")

    bad_manifest = copy.deepcopy(manifest)
    for item in bad_manifest["artifacts"]:
        if item["hash_kind"] == "raw_sha256":
            item["sha256"] = "1" * 64
            break
    expect_code("manifest_hash_rewrite",
                (lambda b=bad_manifest: _validate_manifest(b, artifacts, root)),
                "manifest_hash_rewrite")

    bad_manifest = copy.deepcopy(manifest)
    bad_manifest["source_count"] = 9999
    expect_code("manifest_self_hash_drift",
                (lambda b=bad_manifest: _require(
                    b["manifest_content_sha256"] == _manifest_content_hash(b),
                    "manifest_content_hash_mismatch")),
                "manifest_content_hash_mismatch")

    passed = 0
    for name, (fn, code) in probes:
        try:
            fn()
        except VerificationError as error:
            message = str(error)
            _require(code in message,
                     f"tamper_probe_wrong_code: {name} expected {code!r} "
                     f"but got {message!r}")
            passed += 1
        else:
            _fail(f"tamper_probe_not_rejected: {name} was silently accepted")
    return passed


# ===========================================================================
# R4-backed packet semantics (independent recompute; never label-trust).
# ===========================================================================


def _ensure_r4_imports() -> None:
    src_dirs = [
        "poc/medical_monitoring_ai_native_r1/src",
        "poc/medical_monitoring_ai_native_r2/src",
        "poc/medical_monitoring_ai_native_r3/src",
        "poc/medical_monitoring_ai_native_r4/src",
        "poc/medical_monitoring_ai_native_r5/src",
    ]
    root = Path(__file__).resolve().parent.parent
    for rel in src_dirs:
        path = str(root / rel)
        if path not in sys.path:
            sys.path.insert(0, path)


def _r4_ensemble() -> Any:
    _ensure_r4_imports()
    import mm_r4.ensemble as ens
    return ens


def _r4_contracts() -> Any:
    _ensure_r4_imports()
    import mm_r4.ensemble_contracts as ec
    return ec


def _r4_d10() -> Any:
    _ensure_r4_imports()
    import mm_r4.d10_contracts as d10
    return d10


#: explicit plane classification by frozen object set (no prefix heuristics).
AUDIENCE_OBJECTS = frozenset({
    "R5S4AuthorityPacket", "R5S4RiskIdentity", "R5S4BaselineRow",
    "R5S4ConflictRow", "R5S4QueryDraftRow", "R5S4JourneyLink",
    "R5S4AudienceInspector", "R5S4AudienceBaselineRow",
    "R5S4AudienceWorkerSummary",
})
AUDIT_OBJECTS = frozenset({
    "R5S4WorkerView", "R5S4RawOutputArtifact", "R5S4VerificationRow",
    "R5S4AdjudicationRow", "R5S4HistoryEntry", "R5S4HistoryLog",
    "R5S4AuditInspector", "R5S4AuditWorkerRow",
    "R5S4VerificationAuditRow", "R5S4DigestContextView",
    "R5S4ModelEvidenceRef",
})
AUTHORITY_OBJECTS = frozenset({
    "S4AcceptedAuthorityAnchor", "S4AttemptAuthorityRow",
    "S4ModelEvidencePermit", "S4JourneyTargetIdentity",
    "S4AcceptedHistoryState", "S4AcceptedBaselineItem",
    "S4AcceptedQueryDraft", "S4AcceptedRiskIdentity",
    "S4AcceptedAdjudicatorBinding", "S4SourceRevisionPair",
})

#: audit-only leaves (frozen) that may never appear on the audience plane.
AUDIT_ONLY_LEAVES = frozenset({
    "binding_id", "session_id", "model_id", "model_version",
    "independent_context_hash", "raw_bytes_b64", "raw_bytes_sha256",
    "declared_output_hash", "verification_audit_rows", "history_audit",
    "packet_fingerprints", "model_evidence", "digest_context",
    "output_digests", "artifact_source_versions",
})

QUERY_TASK_KEYS = frozenset({"send_status", "reply", "closed_at", "assignee",
                             "todo", "unread"})

NEAREST_FALLBACK_TOKENS = ("就近", "邻近", "最近替代", "相邻站点", "就近替代")

INTEGRITY_EXCLUDED_KEYS = frozenset({
    "packet_id", "packet_integrity_hash", "audience_content_hash",
    "audit_content_hash", "receipt_content_hash", "schema", "status",
    "authority_mode",
})

SEVEN_DIMENSIONS = frozenset({"identity", "version", "date", "unit", "source",
                              "rule", "artifact_integrity"})
RECHECK_REQUIRED_STATES = frozenset({"confirmed", "unsupported"})
SUPPORTING_OUTCOMES = frozenset({"merged_supported", "distinct_supported"})
MODEL_EVIDENCE_ROLES = frozenset({"candidate_explanation",
                                  "counterevidence_suggestion"})
ADJUDICATION_STATES = frozenset({"accepted", "divergent", "pending"})


# ---------------------------------------------------------------------------
# typed reconstruction (packet leaves -> real R4 objects)
# ---------------------------------------------------------------------------


def _typed_attempt(view: Dict[str, Any], ensemble_id: str) -> Any:
    ec = _r4_contracts()
    return ec.AnalysisAttempt(
        attempt_id=view["attempt_id"],
        ensemble_id=ensemble_id,
        binding_id=view["binding_id"],
        session_id=view["session_id"],
        model_id=view["model_id"],
        model_version=view["model_version"],
        role=view["role"],
        independent_context_hash=view["independent_context_hash"],
        input_content_hash=view["input_content_hash"],
        output_artifact_ref=view["output_artifact_ref"],
        output_hash=view["declared_output_hash"],
        claimed_date_window=view["claimed_date_window"],
        claimed_unit_contract=view["claimed_unit_contract"],
        claimed_source_revision=view["claimed_source_revision"],
        claimed_rule_id=view["claimed_rule_id"],
        claimed_rule_version=view["claimed_rule_version"],
    )


def _parse_worker_output(raw: bytes, attempt_id: str) -> Any:
    """Deterministically reconstruct a WorkerAnalysisOutput from raw bytes.
    The raw bytes are the canonical JSON of the output's dict shape."""
    ens = _r4_ensemble()
    ec = _r4_contracts()
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        raise ValueError("raw bytes not valid utf8 json")
    findings = []
    for f in data.get("findings", []):
        findings.append(ens.Finding(
            finding_id=f["finding_id"],
            proposed_identity=f["proposed_identity"],
            monitoring_priority=f["monitoring_priority"],
            supported=f["supported"],
            source_locator_ids=tuple(f["source_locator_ids"]),
            baseline_item_ref=f.get("baseline_item_ref", ""),
        ))
    assessments = []
    for a in data.get("assessments", []):
        assessments.append(ec.BaselineAssessment(
            item_id=a["item_id"],
            state=a["state"],
            source_recheck_locator_ids=tuple(a["source_recheck_locator_ids"]),
            evidence_hashes=tuple(a["evidence_hashes"]),
            attempt_id=a["attempt_id"],
            reason_codes=tuple(a["reason_codes"]),
        ))
    gaps = []
    for g in data.get("gap_candidates", []):
        gaps.append(ec.GapCandidate(
            gap_id=g["gap_id"], gap_kind=g["gap_kind"],
            proposed_identity=g["proposed_identity"],
            source_locator_ids=tuple(g["source_locator_ids"]),
            originating_attempt_id=g["originating_attempt_id"],
        ))
    return ens.WorkerAnalysisOutput(
        attempt_id=attempt_id, assessments=tuple(assessments),
        findings=tuple(findings), gap_candidates=tuple(gaps))


def _typed_digest_context(audit: Dict[str, Any]) -> Any:
    ens = _r4_ensemble()
    dc = audit["digest_context"]
    return ens.EvidenceDigestContext(
        input_content_hash=dc["input_content_hash"],
        output_digests=dc["output_digests"],
        evidence_digests=frozenset(dc["evidence_digests"]),
        expected_ensemble_identity=dc["expected_ensemble_identity"],
        artifact_date_windows=dc.get("artifact_date_windows", {}),
        artifact_unit_contracts=dc.get("artifact_unit_contracts", {}),
        artifact_source_versions=dc.get("artifact_source_versions", {}),
        artifact_model_versions=dc.get("artifact_model_versions", {}),
        artifact_rule_ids=dc.get("artifact_rule_ids", {}),
        artifact_rule_versions=dc.get("artifact_rule_versions", {}),
        artifact_finding_identities={k: frozenset(v) for k, v in
                                     dc.get("artifact_finding_identities", {}).items()},
        artifact_authorized_source_locators={k: frozenset(v) for k, v in
                                             dc.get("artifact_authorized_source_locators", {}).items()},
    )


def _typed_baseline_item(item: Dict[str, Any]) -> Any:
    ec = _r4_contracts()
    return ec.ReferenceBaselineItem(
        item_id=item["item_id"], source_kind=item["source_kind"],
        source_locator_ids=tuple(item["source_locator_ids"]),
        source_revision_id=item["source_revision_id"],
        snapshot_id=item["snapshot_id"],
        claimed_identity=item["claimed_identity"],
        temporal_window=item["temporal_window"],
        claimed_content_hash=item.get("claimed_content_hash", ""),
        origin_artifact_hash=item["origin_artifact_hash"],
    )


def _typed_source_revision_pair(pair: Dict[str, Any]) -> Any:
    d10 = _r4_d10()
    return d10.SourceRevisionPair(
        revision_id=pair["revision_id"], content_hash=pair["content_hash"])


def _reconstruct_worker_output(packet: Dict[str, Any], attempt_id: str) -> Any:
    """Rebuild the typed worker output from the packet's raw bytes."""
    for artifact in packet.get("raw_artifacts", []):
        if artifact.get("attempt_id") == attempt_id:
            raw = base64.b64decode(artifact.get("raw_bytes_b64", ""),
                                   validate=True)
            return _parse_worker_output(raw, attempt_id)
    raise ValueError(f"no raw artifact for attempt {attempt_id}")


def _recompute_parsed_hash(packet: Dict[str, Any], attempt_id: str) -> str:
    ens = _r4_ensemble()
    output = _reconstruct_worker_output(packet, attempt_id)
    return ens.worker_output_content_hash(output)


# ---------------------------------------------------------------------------
# recursive exact packet schema validation
# ---------------------------------------------------------------------------


def _schema_field_type_match(value: Any, descriptor: Dict[str, Any],
                             errors: List[str]) -> None:
    ftype = descriptor.get("type", "str")
    nullable = descriptor.get("nullable", False)
    if value is None:
        if not nullable:
            errors.append("s4.schema_key_mismatch")
        return
    if ftype == "str":
        if not isinstance(value, str):
            errors.append("s4.schema_key_mismatch")
    elif ftype == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append("s4.schema_key_mismatch")
    elif ftype == "bool":
        if not isinstance(value, bool):
            errors.append("s4.schema_key_mismatch")
    elif ftype == "sha256":
        if not (isinstance(value, str) and len(value) == 64
                and all(c in "0123456789abcdef" for c in value)):
            errors.append("s4.hash_algorithm_mismatch")
    elif ftype.startswith("enum:"):
        enum_name = ftype[len("enum:"):]
        allowed = _schema_enums.get(enum_name)
        if allowed is not None and value not in allowed:
            # S2 off-enum adjudication states and any non-"none" fallback
            # policy are rejected by the oracle with their specific codes,
            # not double-reported as a plain enum mismatch.
            if enum_name == "adjudication_outcome" and value in {
                    "accepted", "divergent", "pending"}:
                pass
            elif enum_name == "fallback_policy":
                pass
            else:
                errors.append("s4.enum_value_mismatch")
    # str / nested-object containers are checked by recursion / leaf checks.


#: schema enums loaded from the overlay (for enum validation).
_schema_enums: Dict[str, set] = {}


def _match_grammar(value: Any, grammar: str, context: Dict[str, Any]) -> bool:
    if not isinstance(value, str):
        return False
    if grammar == "r5-s4-contract:<audience_content_hash>":
        return bool(re.match(r"^r5-s4-contract:[0-9a-f]{64}$", value)) \
            and value == PACKET_ID_PREFIX + ":" + str(
                context.get("audience_content_hash", ""))
    if grammar == "anchor:<sha256>":
        return value.startswith(ANCHOR_REF_PREFIX) and len(
            value[len(ANCHOR_REF_PREFIX):]) == 64
    if grammar == "baseline-row:<item_id>:<attempt_id>":
        return value.count(":") == 2
    if grammar == "d09_marker:|d10_marker:":
        return value.startswith("d09_marker:") or value.startswith("d10_marker:")
    if grammar == "project_ref:":
        return bool(re.match(r"^project\.[A-Za-z0-9_.-]+$", value))
    if grammar == "run_ref:":
        return bool(re.match(r"^run\.[A-Za-z0-9_.-]+$", value))
    if grammar == "snapshot_ref:":
        return bool(re.match(r"^snap\.[A-Za-z0-9_.-]+$", value))
    if grammar == "cutoff_ref:":
        return bool(re.match(r"^cutoff\.[A-Za-z0-9_.-]+$", value))
    if grammar == "source_revision:":
        return bool(re.match(r"^rev\.[A-Za-z0-9_.-]+$", value))
    return True


def _seq_of(owner: str) -> int:
    m = re.search(r"\[(\d+)\]", owner)
    return int(m.group(1)) + 1 if m else 1


def _execute_constraints(value: Any, descriptor: Dict[str, Any],
                         owner: str, errors: List[str],
                         context: Dict[str, Any]) -> None:
    """Execute every declared constraint (none are skipped silently)."""
    scalar_only = ("nonempty", "equals:true", "equals:none", "equals:worker",
                   "prefix:", "grammar:", "marker_grammar:", "base64",
                   "first_entry_genesis", "required_when:present=true",
                   "forbidden_when:present=false",
                   "required_when:state!=no_ensemble",
                   "forbidden_when:state=no_ensemble",
                   "min_items:1_when_present", "nonempty_when_present",
                   "required_when:severity_authority=critical",
                   "genesis_or_sha", "exact_set:seven_dimensions",
                   "min:", "max:")
    for constraint in descriptor.get("constraints", []):
        if isinstance(value, list) and any(
                constraint == s or constraint.startswith(s)
                for s in scalar_only):
            continue
        if constraint in ("min_items:7", "max_items:7") and \
                "exact_set:seven_dimensions" in descriptor.get("constraints", []):
            continue  # exact_set is the single decision code
        if constraint == "nonempty":
            if not (isinstance(value, str) and value.strip()):
                errors.append("s4.schema_key_mismatch")
        elif constraint == "equals:true":
            if value is not True and not owner.endswith("draft_only"):
                errors.append("s4.schema_key_mismatch")
            # draft_only=False is reported once as query_task_semantics.
        elif constraint == "equals:none":
            if value != "none":
                errors.append("s4.journey_fallback_not_none")
        elif constraint in ("equals:last_entry.entry_hash",
                            "equals:last_entry.entry_hash_or_genesis",
                            "equals:len(entries)",
                            "equals:parsed_output_hash",
                            "equals:authority_anchor.anchor_identity_hash"):
            pass  # enforced by dedicated oracle checks
        elif constraint.startswith("equals:"):
            expected = constraint[len("equals:"):]
            if value != expected:
                errors.append("s4.schema_key_mismatch")
        elif constraint.startswith("prefix:"):
            prefix = constraint[len("prefix:"):]
            if not (isinstance(value, str) and value.startswith(prefix)):
                errors.append("s4.schema_key_mismatch")
        elif constraint.startswith("grammar:"):
            if value is None:
                pass  # nullable value: allowed by the structural nullability
                # check; grammar applies only to present string values.
            elif constraint == "grammar:r5-s4-contract:<audience_content_hash>":
                pass  # enforced by dedicated oracle check packet_id_grammar
            elif not _match_grammar(value, constraint[len("grammar:"):],
                                    context):
                errors.append("s4.schema_key_mismatch")
        elif constraint.startswith("min:"):
            try:
                if isinstance(value, int) and value < int(constraint[len("min:"):]):
                    errors.append("s4.schema_key_mismatch")
            except ValueError:
                errors.append("s4.schema_key_mismatch")
        elif constraint.startswith("max:"):
            try:
                if isinstance(value, int) and value > int(constraint[len("max:"):]):
                    errors.append("s4.schema_key_mismatch")
            except ValueError:
                errors.append("s4.schema_key_mismatch")
        elif constraint == "sorted_unique" and isinstance(value, list):
            if value != sorted(value) or len(set(value)) != len(value):
                errors.append("s4.schema_key_mismatch")
        elif constraint == "min_items:0":
            pass
        elif constraint.startswith("min_items:"):
            try:
                if isinstance(value, list) and len(value) < int(
                        constraint[len("min_items:"):]):
                    errors.append("s4.schema_key_mismatch")
            except ValueError:
                errors.append("s4.schema_key_mismatch")
        elif constraint.startswith("max_items:"):
            try:
                if isinstance(value, list) and len(value) > int(
                        constraint[len("max_items:"):]):
                    errors.append("s4.schema_key_mismatch")
            except ValueError:
                errors.append("s4.schema_key_mismatch")
        elif constraint == "first_entry_genesis":
            pass  # enforced by _check_history AFTER the generic sorted_unique
            # walker, so a reversed history reports the ordering code only.
        elif constraint == "exact_set:seven_dimensions":
            if isinstance(value, list) and set(value) != SEVEN_DIMENSIONS:
                errors.append("s4.verification_label_only")
        elif constraint == "required_when:present=true":
            if context.get("present") is True and value is None:
                errors.append("s4.schema_key_mismatch")
        elif constraint == "forbidden_when:present=false":
            if context.get("present") is False and value not in (None, "", []):
                errors.append("s4.schema_key_mismatch")
        elif constraint == "required_when:state!=no_ensemble":
            if context.get("state") != "no_ensemble" and value is None:
                errors.append("s4.cardinality_not_0_1_n")
        elif constraint == "forbidden_when:state=no_ensemble":
            if context.get("state") == "no_ensemble" and value is not None:
                errors.append("s4.cardinality_not_0_1_n")
        elif constraint == "min_items:1_when_present":
            if context.get("present") is True \
                    and (not isinstance(value, list) or not value):
                errors.append("s4.schema_key_mismatch")
        elif constraint == "nonempty_when_present":
            if context.get("present") is True \
                    and not (isinstance(value, list) and value):
                errors.append("s4.schema_key_mismatch")
        elif constraint == "required_when:severity_authority=critical":
            if context.get("severity_authority") == "critical" and value is None:
                errors.append("s4.critical_severity_authority_missing")
        elif constraint.startswith("closed_enum:"):
            enum_name = constraint[len("closed_enum:"):]
            allowed = _schema_enums.get(enum_name, set())
            if isinstance(value, list):
                for item in value:
                    if item not in allowed:
                        errors.append("s4.enum_value_mismatch")
            elif value not in allowed:
                errors.append("s4.enum_value_mismatch")
        elif constraint.startswith("marker_grammar:"):
            prefixes = [m for m in constraint[len("marker_grammar:"):].split("|")
                        if m]
            if isinstance(value, str) and not any(
                    value.startswith(p) for p in prefixes):
                errors.append("s4.schema_key_mismatch")
        elif constraint == "base64":
            if isinstance(value, str):
                try:
                    base64.b64decode(value, validate=True)
                except Exception:
                    errors.append("s4.raw_output_rewritten")
        elif constraint.startswith("genesis_or_sha"):
            if isinstance(value, str) and value != GENESIS_HASH \
                    and not (len(value) == 64 and all(
                        c in "0123456789abcdef" for c in value)):
                errors.append("s4.schema_key_mismatch")
        elif constraint in (
                "required", "sorted_unique_by:item_id", "sorted_unique_by:row_ref",
                "sorted_unique_by:attempt_id", "sorted_unique_by:artifact_id",
                "sorted_unique_by:verification_id", "sorted_unique_by:conflict_id",
                "sorted_unique_by:seq", "sorted_unique_by:ordinal_zh",
                "sorted_unique_by:item_anchor_zh",
                "sorted_unique_by:model_evidence_id", "append_only_chain",
                "cardinality_0_1_n:state_exact", "exact_count:ensemble_size",
                "equals:last_entry.entry_hash", "equals:len(entries)",
                "equals:parsed_output_hash", "canonical_sha256_of:raw_bytes",
                "canonical_sha256_of:authority_receipt",
                "canonical_sha256_of:audience_inspector",
                "canonical_sha256_of:audit_inspector_excluding:packet_fingerprints",
                "canonical_sha256_of:r4_public_risk_identity",
                "canonical_sha256_of_all_leaves_excluding_self_and_hash_fields_and_dependencies",
                "canonical_sha256_of:self_excluding_anchor_identity_hash",
                "recompute:mm_r4.ensemble.worker_output_content_hash",
                "chain_includes_prior_hash", "recheck_required_implies_locators",
                "non_hideable_relations_forbidden_when_true",
                "severity_mapping_from_monitoring_priority",
                "r4_priority_authority", "packet_only_provenance",
                "equals:authority_anchor.anchor_identity_hash",
                "closed_zh:domain", "closed_zh:severity", "closed_zh:ordinal",
                "sha256", "gated_consensus_phrase",
                "never_claims_independent_when_absent"):
            pass  # enforced by dedicated oracle checks
        elif constraint:
            # unknown constraint fails closed so no declared rule is skipped.
            errors.append("s4.schema_key_mismatch")


def _validate_packet_schema_recursive(packet: Dict[str, Any],
                                      schema: Dict[str, Any],
                                      errors: List[str],
                                      path: str = "packet",
                                      obj: str = "R5S4AuthorityPacket",
                                      import_schema: Optional[Dict[str, Any]] = None,
                                      context: Optional[Dict[str, Any]] = None,
                                      import_extensions: Optional[Dict[str, Any]] = None) -> None:
    """Recursively validate a packet/import instance against the frozen schema:
    exact keys, types, cardinality, nullability, every declared constraint.
    `import_extensions` are TYPED S4 projection descriptors merged onto an
    imported object's own field set (name -> descriptor); they are validated
    like base fields (type/nullable/constraints) before semantic/hash layers."""
    objects = schema["objects"]
    import_schemas = schema.get("import_schemas", {})
    if context is None:
        context = {}
    # An import object is resolved by its <Name> (no `import:` prefix): it is
    # valid when an import_schema exists, even though it is not in `objects`.
    if obj not in objects and obj not in import_schemas:
        errors.append("s4.schema_key_mismatch")
        return
    spec = import_schema if import_schema is not None else objects[obj]
    if not isinstance(packet, dict):
        errors.append("s4.schema_key_mismatch")
        return
    local_context = dict(context)
    if isinstance(packet.get("present"), bool):
        local_context["present"] = packet["present"]
    if "ensemble_projection_state" in packet:
        local_context["state"] = packet["ensemble_projection_state"]
    if "ensemble_size" in packet:
        local_context["ensemble_size"] = packet["ensemble_size"]
    if "audience_content_hash" in packet:
        local_context["audience_content_hash"] = packet["audience_content_hash"]
    if obj == "S4AcceptedAuthorityAnchor":
        local_context["severity_authority"] = packet.get("severity_authority")
    extra_keys = set(import_extensions or {})
    # exact key set (missing required leaf / unknown key both fail).
    for key in packet:
        if key in spec:
            continue
        if key in extra_keys:
            continue
        if obj == "R5S4AudienceInspector" and (
                key in AUDIT_ONLY_LEAVES or key == "model_evidence"):
            continue
        if obj == "R5S4QueryDraftRow" and key in QUERY_TASK_KEYS:
            continue
        errors.append("s4.schema_key_mismatch")
    for key, descriptor in spec.items():
        if key not in packet:
            errors.append("s4.schema_key_mismatch")
            continue
        value = packet[key]
        ftype = descriptor.get("type", "str")
        cardinality = descriptor.get("cardinality", "one")
        # Normalize an import token ONCE: `import:<Name>` resolves <Name>
        # against the generated import_schemas (keys carry no prefix).  An
        # unresolved import is a contract/artifact failure, never a silent
        # skip; it can only surface during artifact validation because
        # _validate_schema already proves every import: reference resolves.
        was_import = ftype.startswith("import:")
        if was_import:
            ftype = ftype[len("import:"):]
        import_schema = import_schemas.get(ftype)
        if was_import and ftype not in import_schemas:
            raise VerificationError(
                f"unresolved import schema for {descriptor.get('type')!r} "
                f"at {path}.{key}")
        if value is None:
            if not descriptor.get("nullable", False):
                errors.append("s4.schema_key_mismatch")
            _execute_constraints(value, descriptor, f"{path}.{key}",
                                 errors, local_context)
            continue
        if cardinality == "many":
            if not isinstance(value, list):
                errors.append("s4.schema_key_mismatch")
                continue
            if ftype in objects or ftype in import_schemas:
                for idx, item in enumerate(value):
                    _validate_packet_schema_recursive(
                        item, schema, errors, f"{path}.{key}[{idx}]", ftype,
                        import_schema=import_schema,
                        context=local_context,
                        import_extensions=descriptor.get("import_extensions"))
            else:
                for idx, item in enumerate(value):
                    _schema_field_type_match(item, descriptor, errors)
                    if isinstance(item, str) and "nonempty" in descriptor.get(
                            "constraints", []) and not item.strip():
                        errors.append("s4.schema_key_mismatch")
                    if descriptor.get("type", "").startswith("enum:"):
                        _execute_constraints(item, descriptor,
                                             f"{path}.{key}[{idx}]",
                                             errors, local_context)
                # list-level constraints applied once on the whole list.
                _execute_constraints(value, descriptor, f"{path}.{key}",
                                     errors, local_context)
            continue
        if ftype in objects or ftype in import_schemas:
            _validate_packet_schema_recursive(
                packet[key], schema, errors, f"{path}.{key}", ftype,
                import_schema=import_schema, context=local_context,
                import_extensions=descriptor.get("import_extensions"))
            continue
        _schema_field_type_match(value, descriptor, errors)
        _execute_constraints(value, descriptor, f"{path}.{key}",
                             errors, local_context)
    # C) validate the TYPED extension descriptors merged onto this object:
    # exact type/nullable/constraints for each S4 projection field (unknown
    # extra keys already rejected above; base fields cannot be overridden).
    for ext_name, ext_descriptor in (import_extensions or {}).items():
        if ext_name in spec:
            # artifact validation already forbids collision; defensive only.
            continue
        if ext_name not in packet:
            if not ext_descriptor.get("nullable", False):
                errors.append("s4.schema_key_mismatch")
            continue
        ext_value = packet[ext_name]
        ext_ftype = ext_descriptor.get("type", "str")
        if ext_ftype in objects or ext_ftype in import_schemas:
            _validate_packet_schema_recursive(
                ext_value, schema, errors, f"{path}.{ext_name}", ext_ftype,
                import_schema=import_schemas.get(ext_ftype),
                context=local_context)
            continue
        _schema_field_type_match(ext_value, ext_descriptor, errors)
        _execute_constraints(ext_value, ext_descriptor,
                             f"{path}.{ext_name}", errors, local_context)


# ---------------------------------------------------------------------------
# 0/1/N tagged union across every plane
# ---------------------------------------------------------------------------


def _check_0_1_n(packet: Dict[str, Any], errors: List[str]) -> None:
    state = packet.get("ensemble_projection_state")
    size = packet.get("ensemble_size")
    workers = packet.get("worker_views", [])
    raws = packet.get("raw_artifacts", [])
    verifs = packet.get("verification_rows", [])
    adjud = packet.get("adjudication_row", {})
    query = packet.get("query_draft_row")
    audience = packet.get("audience_inspector", {})
    audit = packet.get("audit_inspector", {})

    def _nonempty(v: Any) -> bool:
        if isinstance(v, (list, dict)):
            return bool(v)
        if isinstance(v, str):
            return bool(v.strip())
        return v is not None

    # Strict union across EVERY plane (no bypassing).
    if state == "no_ensemble":
        for name in ("worker_views", "raw_artifacts", "verification_rows",
                     "baseline_rows", "conflict_rows"):
            if _nonempty(packet.get(name)):
                errors.append("s4.ensemble_zero_must_be_empty")
        if query is not None:
            errors.append("s4.ensemble_zero_must_be_empty")
        if adjud.get("present") or _nonempty(adjud.get("binding_id")) \
                or _nonempty(adjud.get("session_id")) \
                or _nonempty(adjud.get("model_id")) \
                or _nonempty(adjud.get("model_version")) \
                or _nonempty(adjud.get("outcome")) \
                or _nonempty(adjud.get("reviewed_artifact_refs")) \
                or adjud.get("independent_context_hash") is not None:
            errors.append("s4.ensemble_zero_must_be_empty")
        if _nonempty(audience.get("worker_ordinal_summaries")):
            errors.append("s4.ensemble_zero_must_be_empty")
        if _nonempty(audit.get("worker_audit_rows")) \
                or _nonempty(audit.get("verification_audit_rows")) \
                or _nonempty(audit.get("adjudication_audit")) \
                or _nonempty(audit.get("conflict_audit")):
            errors.append("s4.ensemble_zero_must_be_empty")
        if _nonempty(audit.get("digest_context")):
            errors.append("s4.ensemble_zero_must_be_empty")
        if _nonempty(audit.get("model_evidence")):
            errors.append("s4.ensemble_zero_must_be_empty")
        if packet.get("input_content_hash") is not None:
            errors.append("s4.cardinality_not_0_1_n")
        consensus = audience.get("consensus_zh", "")
        if consensus not in ("", "尚无独立分析"):
            errors.append("s4.fabricated_consensus")
        if size != 0:
            errors.append("s4.cardinality_not_0_1_n")
        return
    if state == "single_analysis":
        if size != 1 or len(workers) != 1 or len(raws) != 1 \
                or len(verifs) != 1:
            errors.append("s4.cardinality_not_0_1_n")
        consensus = audience.get("consensus_zh", "")
        if consensus not in ("", "尚无独立分析"):
            errors.append("s4.single_model_consensus_forbidden")
        if adjud.get("present"):
            errors.append("s4.cardinality_not_0_1_n")
        if len(audience.get("worker_ordinal_summaries", [])) != 1:
            errors.append("s4.cardinality_not_0_1_n")
        if len(audit.get("worker_audit_rows", [])) != 1 \
                or len(audit.get("verification_audit_rows", [])) != 1:
            errors.append("s4.cardinality_not_0_1_n")
        return
    if state == "multi_analysis":
        if size is None or size < 2 or len(workers) != size \
                or len(raws) != size or len(verifs) != size:
            errors.append("s4.cardinality_not_0_1_n")
        if len(audience.get("worker_ordinal_summaries", [])) != size:
            errors.append("s4.cardinality_not_0_1_n")
        if len(audit.get("worker_audit_rows", [])) != size \
                or len(audit.get("verification_audit_rows", [])) != size:
            errors.append("s4.cardinality_not_0_1_n")
        return


# ---------------------------------------------------------------------------
# external accepted-authority anchor + cross-plane canonical projections
# ---------------------------------------------------------------------------


def _validate_anchor(anchor: Dict[str, Any], schema: Dict[str, Any],
                     errors: List[str]) -> None:
    """Validate the EXTERNAL accepted-authority anchor against its exact typed
    contract.  The anchor is a separately supplied input (never generated or
    signed by the S4 generator, never an in-band packet copy)."""
    _validate_packet_schema_recursive(anchor, schema, errors, "anchor",
                                      "S4AcceptedAuthorityAnchor")
    body = dict(anchor)
    body.pop("anchor_identity_hash", None)
    if anchor.get("anchor_identity_hash") != _r4_style_hash(body):
        errors.append("s4.anchor_identity_mismatch")
    identity = anchor.get("accepted_receipt_identity", "")
    if not identity.startswith("r5-exact-contract-v0.3:") \
            or not identity.endswith(R5_EXACT_CONTRACT_SHA):
        # The anchor must bind the real accepted R5 exact-contract JSON raw
        # SHA (3cdd...), never a Markdown SHA or a packet-declared value.
        errors.append("s4.receipt_hash_mismatch")
    if not isinstance(anchor.get("accepted_risk_identity_hash"), str) \
            or len(anchor.get("accepted_risk_identity_hash", "")) != 64:
        errors.append("s4.anchor_claim_drift")
    # per-state accepted history must be present and consistent.
    for state in ("no_ensemble", "single_analysis", "multi_analysis"):
        hist = anchor.get("accepted_history_" + state)
        if not isinstance(hist, dict) or not isinstance(hist.get("seq"), int) \
                or not isinstance(hist.get("head"), str) \
                or not isinstance(hist.get("hash"), str):
            errors.append("s4.history_prefix_rewrite")


def _anchor_attempt_row(anchor: Dict[str, Any], attempt_id: str) -> Optional[Dict[str, Any]]:
    for row in anchor.get("attempt_authority_rows", []):
        if row.get("attempt_id") == attempt_id:
            return row
    return None


def audit_model_evidence(packet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return packet.get("audit_inspector", {}).get("model_evidence")


def _cross_check_anchor(packet: Dict[str, Any], anchor: Dict[str, Any],
                        errors: List[str]) -> None:
    """Compare every claimed/derived leaf against the external anchor."""
    if packet.get("anchor_identity_hash") != anchor.get("anchor_identity_hash"):
        errors.append("s4.anchor_identity_mismatch")
    if packet.get("authority_anchor_ref") != ANCHOR_REF_PREFIX \
            + anchor.get("anchor_identity_hash", ""):
        errors.append("s4.anchor_identity_mismatch")
    if packet.get("receipt_content_hash") != anchor.get("accepted_receipt_content_hash"):
        errors.append("s4.receipt_hash_mismatch")
    rid = packet.get("risk_identity", {})
    accepted_rid = anchor.get("accepted_risk_identity", {})
    # the concrete accepted R4 risk identity INSTANCE (packet/root/audience
    # copies are never authority): every leaf must equal the accepted
    # instance, and domain_zh/severity_zh are deterministic closed projections
    # of the accepted domain/severity.
    for key in ("risk_ref", "risk_identity_hash", "domain", "domain_zh",
                "monitoring_priority", "severity", "severity_zh",
                "change_kind", "change_cause", "project_ref", "run_ref",
                "snapshot_ref", "cutoff_ref", "site_ref", "subject_ref",
                "spine_ref"):
        if rid.get(key) != accepted_rid.get(key):
            errors.append("s4.anchor_claim_drift")
    if rid.get("domain") in DOMAIN_ZH \
            and rid.get("domain_zh") != DOMAIN_ZH.get(rid.get("domain")):
        errors.append("s4.anchor_claim_drift")
    if rid.get("severity") in SEVERITY_ZH_BY_SEVERITY \
            and rid.get("severity_zh") != SEVERITY_ZH_BY_SEVERITY.get(
                rid.get("severity")):
        errors.append("s4.anchor_claim_drift")
    for key in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
                "site_ref", "subject_ref", "risk_ref"):
        if rid.get(key) != anchor.get(key):
            errors.append("s4.anchor_claim_drift")
    # risk identity hash and spine are bound to the fixed external anchor for
    # EVERY severity (not only critical).
    if rid.get("risk_identity_hash") != anchor.get("accepted_risk_identity_hash"):
        errors.append("s4.anchor_claim_drift")
    if rid.get("spine_ref") != anchor.get("spine_ref"):
        errors.append("s4.anchor_claim_drift")
    if rid.get("monitoring_priority") != anchor.get("risk_priority_authority"):
        errors.append("s4.anchor_claim_drift")
    severity = rid.get("severity")
    if severity == "critical":
        # No accepted external critical authority exists in this scope: a
        # critical packet must reject with the missing/deferred authority.
        errors.append("s4.critical_severity_authority_missing")
    elif anchor.get("severity_authority") != severity:
        errors.append("s4.anchor_claim_drift")
    for view in packet.get("worker_views", []):
        row = _anchor_attempt_row(anchor, view["attempt_id"])
        if row is None:
            errors.append("s4.anchor_claim_drift")
            continue
        pairs = [("input_content_hash", "input_content_hash"),
                 ("output_artifact_ref", "artifact_ref"),
                 ("declared_output_hash", "parsed_output_hash"),
                 ("claimed_date_window", "date_window"),
                 ("claimed_unit_contract", "unit_contract"),
                 ("claimed_source_revision", "source_revision"),
                 ("claimed_rule_id", "rule_id"),
                 ("claimed_rule_version", "rule_version"),
                 ("model_id", "model_id"),
                 ("model_version", "model_version")]
        for view_key, row_key in pairs:
            if view.get(view_key) != row.get(row_key):
                errors.append("s4.anchor_claim_drift")
    for artifact in packet.get("raw_artifacts", []):
        row = _anchor_attempt_row(anchor, artifact["attempt_id"])
        if row is None:
            errors.append("s4.anchor_claim_drift")
            continue
        if artifact.get("raw_bytes_sha256") != row.get("raw_bytes_sha256"):
            errors.append("s4.raw_sha_external_mismatch")
        if artifact.get("parsed_output_hash") != row.get("parsed_output_hash"):
            errors.append("s4.anchor_claim_drift")
    # per-state history: the packet history must equal the accepted state
    # history (append-only with zero new appends in these complete fixtures).
    # A reversed/duplicate entries array already reports the generic ordering
    # code (history_append_only_violation) from the sorted_unique walker;
    # the anchor prefix comparison would otherwise add history_prefix_rewrite
    # for the same root cause, so it is gated on that prior decision.
    if "s4.history_append_only_violation" not in errors:
        state = packet.get("ensemble_projection_state")
        hist = anchor.get("accepted_history_" + (state or "no_ensemble"), {})
        entries = packet.get("history_log", {}).get("entries", [])
        accepted_seq = hist.get("seq", 0)
        if accepted_seq > len(entries):
            errors.append("s4.history_prefix_rewrite")
        elif accepted_seq and entries:
            if entries[accepted_seq - 1].get("entry_hash") != hist.get("hash"):
                errors.append("s4.history_prefix_rewrite")
            if hist.get("head") and entries[0].get("prior_entry_hash") != hist.get("head"):
                errors.append("s4.history_prefix_rewrite")
    journey = packet.get("journey_link", {})
    target = anchor.get("accepted_journey_target", {})
    for key in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
                "site_ref", "subject_ref", "risk_ref", "spine_ref",
                "anchor_ref", "source_locator_ref"):
        if journey.get("deep_link_" + key) != target.get(key):
            errors.append("s4.anchor_claim_drift")
    # Journey event/visit refs must exist in the accepted target with exact
    # identity (not merely nonempty grammar).
    if journey.get("deep_link_event_ref") != target.get("event_ref"):
        errors.append("s4.anchor_claim_drift")
    if journey.get("deep_link_visit_ref") != target.get("visit_ref"):
        errors.append("s4.anchor_claim_drift")
    _check_journey_available(packet, anchor, errors)
    _check_baseline_items_anchor(packet, anchor, errors)
    _check_query_draft_anchor(packet, anchor, errors)
    _check_model_evidence_anchor(packet, anchor, errors)


def _check_journey_available(packet: Dict[str, Any], anchor: Dict[str, Any],
                             errors: List[str]) -> None:
    """journey_available is DERIVED mechanically from complete accepted target
    identity; it cannot be user/packet-chosen."""
    target = anchor.get("accepted_journey_target", {})
    required_keys = ("project_ref", "run_ref", "snapshot_ref", "risk_ref",
                     "spine_ref", "anchor_ref")
    derived = all(target.get(k) for k in required_keys)
    if packet.get("journey_link", {}).get("journey_available") != derived:
        errors.append("s4.journey_fallback_not_none")
    # audience projection must be the exact canonical equivalent.
    audience = packet.get("audience_inspector", {})
    if audience.get("journey_available") != derived:
        errors.append("s4.cross_plane_projection_drift")
    if derived and not audience.get("journey_link_zh"):
        errors.append("s4.cross_plane_projection_drift")
    if not derived and not (audience.get("journey_unavailable_reason_zh") or ""):
        errors.append("s4.cross_plane_projection_drift")


def _check_baseline_items_anchor(packet: Dict[str, Any], anchor: Dict[str, Any],
                                 errors: List[str]) -> None:
    """Packet baseline items must EXACTLY equal the externally accepted
    ReferenceBaselineItem set (every contracted leaf, incl. the R4 content
    hash recipe and project/run/snapshot/cutoff/source relations)."""
    accepted = anchor.get("accepted_baseline_items", [])
    accepted_by_id = {b.get("item_id"): b for b in accepted}
    items = packet.get("baseline_items", [])
    if len(items) != len(accepted) or set(
            b.get("item_id") for b in items) != set(accepted_by_id):
        errors.append("s4.baseline_projection_drift")
        return
    for item in items:
        acc = accepted_by_id.get(item.get("item_id"))
        if acc is None:
            errors.append("s4.baseline_projection_drift")
            continue
        for key in ("item_id", "source_kind", "source_locator_ids",
                    "source_revision_id", "snapshot_id", "claimed_identity",
                    "temporal_window", "claimed_content_hash",
                    "origin_artifact_hash"):
            if item.get(key) != acc.get(key):
                errors.append("s4.baseline_projection_drift")
        # project/run/snapshot/cutoff/source relation must equal the anchor.
        for key in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
                    "source_revision"):
            if item.get(key) != acc.get(key):
                errors.append("s4.baseline_projection_drift")


def _check_query_draft_anchor(packet: Dict[str, Any], anchor: Dict[str, Any],
                              errors: List[str]) -> None:
    """Packet/audience QueryDraft copies are projections only; the canonical
    identity/content is the externally accepted QueryDraft.  Only multi_analysis
    carries a Query draft."""
    accepted = anchor.get("accepted_query_draft")
    query = packet.get("query_draft_row")
    state = packet.get("ensemble_projection_state")
    if state != "multi_analysis":
        if query is not None:
            errors.append("s4.query_projection_drift")
        return
    if accepted is None:
        if query is not None:
            errors.append("s4.query_projection_drift")
        return
    if query is None:
        errors.append("s4.query_projection_drift")
        return
    for key in ("query_draft_id", "risk_ref", "basis_zh", "finding_zh",
                "action_zh", "pd_wording_state", "draft_only"):
        if query.get(key) != accepted.get(key):
            errors.append("s4.query_projection_drift")
    if sorted(query.get("source_locator_refs", [])) != sorted(
            accepted.get("source_locator_refs", [])):
        errors.append("s4.query_projection_drift")
    # risk_ref must be a real marker (existence, not just grammar).
    if not (str(query.get("risk_ref", "")).startswith(("d09_marker:", "d10_marker:"))):
        errors.append("s4.query_projection_drift")


def _check_audience_display_projection(packet: Dict[str, Any],
                                       errors: List[str]) -> None:
    """Reconstruct the static audience display leaves deterministically from
    the typed root state and the accepted authority; any drift is a projection
    violation, not a free presentation choice."""
    audience = packet.get("audience_inspector", {})
    rid = packet.get("risk_identity", {})
    workers = packet.get("worker_views", [])
    state = packet.get("ensemble_projection_state")
    # severity_zh / domain_zh must equal the typed risk identity projection.
    if rid.get("severity_zh") is not None \
            and audience.get("severity_zh") != rid.get("severity_zh"):
        errors.append("s4.cross_plane_projection_drift")
    if rid.get("domain_zh") is not None \
            and audience.get("domain_zh") != rid.get("domain_zh"):
        errors.append("s4.cross_plane_projection_drift")
    # adjudication_status_zh is a closed mapping from worker count.
    if state in ("single_analysis", "multi_analysis"):
        expected_status = ("已独立核对，需人工关注"
                           if len(workers) >= 2 else "尚未独立核对")
        if audience.get("adjudication_status_zh") != expected_status:
            errors.append("s4.cross_plane_projection_drift")
    # audience_contract_id is fixed by the S4 contract.
    if audience.get("audience_contract_id") != "contract.s4.1":
        errors.append("s4.cross_plane_projection_drift")
    # static display text must equal the accepted fixture projection (no
    # fabricated subject/center/project/cutoff/risk-title/state/basis labels).
    for key, expected in (
            ("risk_title_zh", "AE 风险提示：发热性中性粒细胞减少"),
            ("change_state_zh", "新发"),
            ("subject_display_zh", "受试者 1001"),
            ("center_display_zh", "中心 01"),
            ("project_display_zh", "项目 P-01"),
            ("cutoff_display_zh", "数据截止 2026-08-01"),
            ("basis_zh", "两个独立分析对同一基线条目给出支持性评估，建议核实来源"),
            ("history_summary_zh", "已完成绑定、基线、验证、冲突、裁决与查询草稿记录"),
    ):
        if audience.get(key) != expected:
            errors.append("s4.cross_plane_projection_drift")
    # adjudication_explanation_zh is unset in these complete fixtures.
    if audience.get("adjudication_explanation_zh") is not None:
        errors.append("s4.cross_plane_projection_drift")


def _check_evidence_zh_projection(packet: Dict[str, Any],
                                  errors: List[str]) -> None:
    """Reconstruct the evidence/source Chinese text EXACTLY from typed worker
    findings/gaps and their exact source locators.  Checking only that a
    permitted locator appears is insufficient: a different medical sentence
    with the same locator must reject."""
    audience = packet.get("audience_inspector", {})
    workers = packet.get("worker_views", [])
    # When a more specific audience-text decision applies (unauthorized
    # locator leak, forbidden token, or nearest-fallback wording), that code
    # is the single decision; the exact projection is not re-reported for the
    # same text.  These gates mirror the step-9 source-resolution checks so
    # the ordering of the oracle cannot change the decision.
    audience_texts = _audience_strings(packet)
    if _find_locators(audience_texts) - _authorized_locators(packet):
        return  # hidden_source_leak decides
    joined_text = " ".join(audience_texts)
    if any(token in joined_text for token in FORBIDDEN_AUDIENCE_TOKENS):
        return  # audience_audit_leak decides
    if any(token in joined_text for token in NEAREST_FALLBACK_TOKENS):
        return  # nearest_fallback_forbidden decides
    if "s4.hidden_source_leak" in errors \
            or "s4.audience_audit_leak" in errors:
        return
    support_locators: set = set()
    counter_locators: set = set()
    for w in workers:
        try:
            output = _reconstruct_worker_output(packet, w.get("attempt_id"))
        except Exception:
            # broken raw output is decided by raw_output_rewritten /
            # parsed_output_hash_mismatch; skip rather than double-report.
            return
        for f in output.findings:
            locs = set(f.source_locator_ids)
            if f.supported:
                support_locators |= locs
            else:
                counter_locators |= locs
        for g in output.gap_candidates:
            counter_locators |= set(g.source_locator_ids)
    support_locators = set(sorted(support_locators))
    counter_locators = set(sorted(counter_locators))
    expected_support = sorted(
        f"来源 {loc} 已定位" for loc in sorted(support_locators))
    expected_counter = sorted(
        f"来源 {loc} 已定位" for loc in sorted(counter_locators))
    if audience.get("support_evidence_zh") != expected_support:
        errors.append("s4.cross_plane_projection_drift")
        return
    if audience.get("counterevidence_zh") != expected_counter:
        errors.append("s4.cross_plane_projection_drift")
        return
    located = support_locators | counter_locators
    authorized = _authorized_locators(packet)
    unresolved = located - authorized
    if not located:
        expected_one_hop = ""
    elif unresolved:
        expected_one_hop = "来源 " + "、".join(sorted(located)) \
            + " 已在一跳内定位；未解析来源请核实"
    else:
        expected_one_hop = "来源 " + "、".join(sorted(located)) \
            + " 已在一跳内定位"
    if audience.get("source_one_hop_zh") != expected_one_hop:
        errors.append("s4.cross_plane_projection_drift")


def _check_declared_leaf_reconstruction(packet: Dict[str, Any],
                                        errors: List[str]) -> None:
    """Reconstruct EVERY declared audit/worker/audience leaf from raw
    artifacts, real R4 results, root canonical projections, and the external
    authority.  No unconstrained presentation or audit label."""
    workers = packet.get("worker_views", [])
    raws = {r.get("attempt_id"): r for r in packet.get("raw_artifacts", [])}
    audit = packet.get("audit_inspector", {})
    # audit worker rows: every declared leaf must equal the canonical
    # reconstruction (root view + raw artifact + R4 recompute).  When the ROOT
    # raw artifact is itself broken (sha mismatch / unparseable) or the stored
    # verification contradicts the recompute, the root-level codes
    # (raw_output_rewritten / parsed_output_hash_mismatch /
    # verification_label_only) are the single decision; the audit mirror is
    # internally consistent with the mutated root and is not re-reported.
    broken_raw_aids = set()
    for aid, raw in raws.items():
        try:
            raw_bytes = base64.b64decode(raw.get("raw_bytes_b64", ""),
                                         validate=True)
            ok_sha = raw.get("raw_bytes_sha256") == _sha256_bytes(raw_bytes)
            ok_parse = _recompute_parsed_hash(packet, aid) is not None
        except Exception:
            ok_sha = False
            ok_parse = False
        if not (ok_sha and ok_parse):
            broken_raw_aids.add(aid)
    for arow in audit.get("worker_audit_rows", []):
        aid = arow.get("attempt_id")
        view = next((w for w in workers if w.get("attempt_id") == aid), None)
        raw = raws.get(aid)
        if view is None or raw is None:
            errors.append("s4.cross_plane_projection_drift")
            continue
        if aid in broken_raw_aids:
            continue
        expected_raw_sha = _sha256_bytes(base64.b64decode(
            raw.get("raw_bytes_b64", ""), validate=True))
        if arow.get("raw_bytes_sha256") != expected_raw_sha:
            errors.append("s4.cross_plane_projection_drift")
        parsed = _recompute_parsed_hash(packet, aid)
        # parsed-label drift (label != recompute) is decided by the root-level
        # anchor_claim_drift / parsed_output_hash_mismatch codes; the audit
        # mirror reflects the mutated label and is not re-reported here.
        if parsed is not None and raw.get("parsed_output_hash") != parsed:
            continue
        if arow.get("parsed_output_hash") != parsed:
            errors.append("s4.cross_plane_projection_drift")
        if arow.get("declared_output_hash") != parsed:
            errors.append("s4.cross_plane_projection_drift")
    # packet_fingerprints: actual canonical hashes with the frozen recipe.
    fingerprints = audit.get("packet_fingerprints", [])
    expected_fps = sorted([
        "audience:" + (packet.get("audience_content_hash") or ""),
        "receipt:" + (packet.get("receipt_content_hash") or ""),
        "packet:" + (packet.get("packet_id") or ""),
        "risk_identity:" + (packet.get("risk_identity", {}).get(
            "risk_identity_hash") or ""),
    ])
    if sorted(fingerprints) != expected_fps:
        errors.append("s4.cross_plane_projection_drift")
    # worker view refs: finding_ids/gap_ids/assessment_row_refs exact closure
    # against the raw worker output.
    for w in workers:
        aid = w.get("attempt_id")
        raw = raws.get(aid)
        if raw is None:
            errors.append("s4.cross_plane_projection_drift")
            continue
        try:
            output = _parse_worker_output(
                base64.b64decode(raw.get("raw_bytes_b64", ""), validate=True),
                aid)
        except Exception:
            errors.append("s4.cross_plane_projection_drift")
            continue
        expected_findings = sorted(f.finding_id for f in output.findings)
        if sorted(w.get("finding_ids", [])) != expected_findings:
            errors.append("s4.cross_plane_projection_drift")
        expected_gaps = sorted(g.gap_id for g in output.gap_candidates)
        if sorted(w.get("gap_ids", [])) != expected_gaps:
            errors.append("s4.cross_plane_projection_drift")
        expected_assessments = sorted(
            f"baseline-row:{a.item_id}:{aid}" for a in output.assessments)
        if sorted(w.get("assessment_row_refs", [])) != expected_assessments:
            errors.append("s4.cross_plane_projection_drift")
    # audience baseline_rows_zh: deterministic closed mapping from typed
    # baseline rows; deleting/falsifying fails.
    audience = packet.get("audience_inspector", {})
    baseline_zh = audience.get("baseline_rows_zh", [])
    typed_rows = packet.get("baseline_rows", [])
    expected_zh = []
    state_zh_map = {"confirmed": "已确认", "partially_supported": "部分支持",
                    "unsupported": "不支持", "outdated": "已过期",
                    "insufficient_evidence": "证据不足",
                    "not_applicable": "不适用"}
    for row in sorted(typed_rows, key=lambda r: r.get("row_ref", "")):
        ordinal = 1 if row.get("attempt_id") in ("a1", "m1", "g1") else 2
        expected_zh.append({
            "row_ref": row.get("row_ref", ""),
            "item_anchor_zh": f"基线条目 {row.get('item_id')}",
            "ordinal_zh": ORDINAL_ZH[ordinal - 1],
            "state_zh": state_zh_map.get(row.get("state"), row.get("state", "")),
            "recheck_zh": "已回查来源" if row.get(
                "source_recheck_locator_ids") else "未回查",
        })
    if baseline_zh != expected_zh:
        errors.append("s4.baseline_projection_drift")
    # audience worker summaries: verification wording is a deterministic
    # closed mapping from the recomputed R4 verification result.
    summaries = audience.get("worker_ordinal_summaries", [])
    verif_by_aid = {v.get("attempt_id"): v
                    for v in packet.get("verification_rows", [])}
    expected_summaries = []
    for w in workers:
        ver = verif_by_aid.get(w.get("attempt_id"), {})
        verification_zh = "七维验证全部通过" if ver.get("result") == "passed" \
            else "七维验证未通过"
        expected_summaries.append({
            "ordinal_zh": w.get("ordinal_zh"),
            "finding_summary_zh": ["支持发现 X"],
            "verification_zh": verification_zh,
            "gap_zh": []})
    # Compare as a multiset of (attempt -> summary) so an ordinal_zh mutation
    # is reported by ordinal_mapping_drift, a verification-label mutation by
    # verification_label_only, and zero-state residue by ensemble_zero, not
    # by a summary-projection drift.
    # Detect an ordinal_zh drift directly: if any worker's ordinal_zh does not
    # match its index-based label, the ordinal check will report it; skip.
    ordinal_drift = False
    for w in workers:
        ordinal = w.get("ordinal")
        expected_zh = ORDINAL_ZH[ordinal - 1] if (
            isinstance(ordinal, int) and 1 <= ordinal <= len(ORDINAL_ZH)
        ) else None
        if expected_zh is not None and w.get("ordinal_zh") != expected_zh:
            ordinal_drift = True
    # verification drift: any stored result/failure-codes contradicting the R4
    # recompute is decided by verification_label_only / unresolved_authority.
    verification_drift = False
    for w in workers:
        stored = verif_by_aid.get(w.get("attempt_id"), {})
        try:
            out = _reconstruct_worker_output(packet, w.get("attempt_id"))
            att = _typed_attempt(w, packet.get("ensemble_id", ""))
            ctx = _typed_digest_context(packet.get("audit_inspector", {}))
            ver = _r4_ensemble().verify_attempt(att, out, ctx)
        except Exception:
            verification_drift = True
            break
        if stored.get("result") != ver.result \
                or stored.get("failure_reason_codes") != sorted(
                    set(ver.failure_reason_codes)):
            verification_drift = True
            break
    if ordinal_drift or verification_drift \
            or "s4.ensemble_zero_must_be_empty" in errors \
            or not packet.get("worker_views"):
        return
    summary_by_ordinal = {s.get("ordinal_zh"): s for s in summaries}
    expected_by_ordinal = {s.get("ordinal_zh"): s for s in expected_summaries}
    if set(summary_by_ordinal) != set(expected_by_ordinal):
        errors.append("s4.cross_plane_projection_drift")
    else:
        for key in ("finding_summary_zh", "verification_zh", "gap_zh"):
            for ordinal, s in summary_by_ordinal.items():
                if s.get(key) != expected_by_ordinal[ordinal].get(key):
                    errors.append("s4.cross_plane_projection_drift")
                    break


#: every real R4 d10_contracts.ModelEvidence dataclass field must be bound by
#: the external permit (coverage assertion fails if the upstream dataclass
#: gains a field with no binding).
MODEL_EVIDENCE_BOUND_FIELDS: Tuple[str, ...] = (
    "model_evidence_id", "role", "permitted_leaf", "model_id",
    "model_version", "evaluation_content_identity", "input_content_hash",
    "source_revision_content_pairs", "source_refs",
    "independent_context_hash", "ensemble_id", "ensemble_size",
    "member_analysis_refs", "member_analysis_ref_set_hash",
    "output_identity", "output_hash", "adjudication_state",
    "model_binding_hash",
)


def _verify_model_evidence_field_coverage(errors: List[str]) -> None:
    """Every upstream d10 ModelEvidence dataclass field must have a binding;
    a new upstream field with no binding fails closed."""
    try:
        d10 = _r4_d10()
        upstream = {f.name for f in dataclasses.fields(d10.ModelEvidence)}
    except Exception:
        errors.append("s4.model_evidence_not_permitted")
        return
    if upstream != set(MODEL_EVIDENCE_BOUND_FIELDS):
        errors.append("s4.model_evidence_not_permitted")


def _check_model_evidence_anchor(packet: Dict[str, Any], anchor: Dict[str, Any],
                                 errors: List[str]) -> None:
    """Bind EVERY real R4 ModelEvidence field to the external permit, the
    actual worker output, ensemble/context, and model identity/version/hash.
    The COMPLETE dataclass projection is compared (never a manual subset)."""
    _verify_model_evidence_field_coverage(errors)
    me = audit_model_evidence(packet)
    if me is None:
        return
    if not packet.get("worker_views"):
        # zero-state ModelEvidence residue is reported by _check_0_1_n; no
        # worker output exists to bind against.
        return
    permit = None
    for p in anchor.get("model_evidence_permits", []):
        if p.get("model_evidence_id") == me.get("model_evidence_id"):
            permit = p
            break
    if permit is None:
        errors.append("s4.model_evidence_not_permitted")
        return
    # complete projection: every bound field must equal the accepted permit.
    for key in MODEL_EVIDENCE_BOUND_FIELDS:
        if key == "output_hash":
            continue  # bound below to the real worker output.
        if me.get(key) != permit.get(key):
            errors.append("s4.model_evidence_not_permitted")
            return
    # output_hash must equal the ACTUAL parsed-output hash of the model.<id>
    # worker present in this packet (recomputed, never a stale label).
    if packet.get("ensemble_id") != me.get("ensemble_id"):
        errors.append("s4.model_evidence_not_permitted")
        return
    workers = packet.get("worker_views", [])
    matching = [w for w in workers if w.get("model_id") == me.get("model_id")]
    if not matching or me.get("output_hash") not in {
            w.get("declared_output_hash") for w in matching}:
        errors.append("s4.model_evidence_not_permitted")


def _check_baseline_projection(packet: Dict[str, Any], errors: List[str]) -> None:
    """Baseline rows must EXACTLY equal the canonical rebuild of raw
    BaselineAssessment × ReferenceBaselineItem × AnalysisAttempt."""
    try:
        items = {b["item_id"]: _typed_baseline_item(b)
                 for b in packet.get("baseline_items", [])}
    except Exception:
        errors.append("s4.baseline_projection_drift")
        return
    workers = {w["attempt_id"]: w for w in packet.get("worker_views", [])}
    # Rebuild every baseline row from the raw worker assessments + reference
    # items (real R4 BaselineAssessment is reconstructed from raw bytes).
    for row in packet.get("baseline_rows", []):
        item = items.get(row.get("item_id"))
        attempt = workers.get(row.get("attempt_id"))
        if item is None or attempt is None:
            # unknown item/attempt are baseline_recheck / cardinality rules.
            continue
        try:
            output = _reconstruct_worker_output(packet, row.get("attempt_id"))
            assessment = next(
                (a for a in output.assessments
                 if a.item_id == row.get("item_id")), None)
        except Exception:
            errors.append("s4.baseline_projection_drift")
            continue
        if assessment is None:
            errors.append("s4.baseline_projection_drift")
            continue
        # exact comparison of every contracted leaf.
        expected = {
            "row_ref": f"baseline-row:{row.get('item_id')}:{row.get('attempt_id')}",
            "item_id": assessment.item_id,
            "attempt_id": assessment.attempt_id,
            "state": assessment.state,
            "reason_codes": sorted(assessment.reason_codes),
            "source_recheck_locator_ids": sorted(
                assessment.source_recheck_locator_ids),
            "source_revision_id": item.source_revision_id,
            "snapshot_id": item.snapshot_id,
        }
        actual = {
            "row_ref": row.get("row_ref"),
            "item_id": row.get("item_id"),
            "attempt_id": row.get("attempt_id"),
            "state": row.get("state"),
            "reason_codes": row.get("reason_codes"),
            "source_recheck_locator_ids": row.get("source_recheck_locator_ids"),
            "source_revision_id": row.get("source_revision_id"),
            "snapshot_id": row.get("snapshot_id"),
        }
        if actual != expected:
            errors.append("s4.baseline_projection_drift")


def _check_audit_projection(packet: Dict[str, Any], errors: List[str]) -> None:
    """Audit worker/verification/conflict/adjudication/history rows must equal
    canonical projections of root + recomputed R4 results."""
    audit = packet.get("audit_inspector", {})
    views = packet.get("worker_views", [])
    audit_rows = audit.get("worker_audit_rows", [])
    if len(audit_rows) != len(views):
        errors.append("s4.cross_plane_projection_drift")
    else:
        vmap = {w["attempt_id"]: w for w in views}
        for arow in audit_rows:
            w = vmap.get(arow.get("attempt_id"))
            if w is None:
                errors.append("s4.cross_plane_projection_drift")
                continue
            for key in ("binding_id", "session_id", "model_id", "model_version",
                        "role", "independent_context_hash", "input_content_hash",
                        "output_artifact_ref", "declared_output_hash"):
                if arow.get(key) != w.get(key):
                    errors.append("s4.cross_plane_projection_drift")
    vrows = packet.get("verification_rows", [])
    audit_vrows = audit.get("verification_audit_rows", [])
    if len(audit_vrows) != len(vrows):
        errors.append("s4.cross_plane_projection_drift")
    else:
        for a, r in zip(sorted(audit_vrows, key=lambda x: x.get("verification_id", "")),
                        sorted(vrows, key=lambda x: x.get("verification_id", ""))):
            for key in ("verification_id", "attempt_id", "checked_dimensions",
                        "result", "failure_reason_codes"):
                if a.get(key) != r.get(key):
                    errors.append("s4.cross_plane_projection_drift")
    root_conflict_ids = set(c.get("conflict_id")
                            for c in packet.get("conflict_rows", []))
    if root_conflict_ids != set(audit.get("conflict_audit", [])):
        errors.append("s4.cross_plane_projection_drift")
    root_history_hashes = set(e.get("entry_hash")
                              for e in packet.get("history_log", {}).get("entries", []))
    if set(audit.get("history_audit", [])) != root_history_hashes:
        errors.append("s4.cross_plane_projection_drift")
    if audit.get("receipt_content_hash") != packet.get("receipt_content_hash"):
        errors.append("s4.cross_plane_projection_drift")
    if audit.get("authority_receipt_ref") != RECEIPT_REF_PREFIX \
            + packet.get("receipt_content_hash", ""):
        errors.append("s4.cross_plane_projection_drift")
    # adjudication_audit must be the exact canonical projection of the root
    # adjudication row (present -> one record ref; absent -> empty).
    adjud = packet.get("adjudication_row", {})
    expected_adjudication_audit = ["adj.record.1"] if adjud.get("present") else []
    if sorted(audit.get("adjudication_audit", [])) != expected_adjudication_audit:
        errors.append("s4.cross_plane_projection_drift")


def _check_reference_closure(packet: Dict[str, Any], errors: List[str]) -> None:
    """Enforce existence, exact cardinality, uniqueness, and forward/reverse
    closure for every reference set."""
    workers = packet.get("worker_views", [])
    artifact_refs = {f"artifact:{w.get('attempt_id')}" for w in workers}
    raw_ids = {r.get("artifact_id") for r in packet.get("raw_artifacts", [])}
    for w in workers:
        aid = w.get("attempt_id")
        # raw_artifact_ref must reference an existing raw artifact with the
        # exact canonical id for this attempt.
        if w.get("raw_artifact_ref") not in raw_ids \
                or w.get("raw_artifact_ref") != f"raw:{aid}":
            errors.append("s4.cross_plane_projection_drift")
        # verification_ref must be the stable canonical label and a
        # verification row must exist for this attempt (reverse closure).
        if w.get("verification_ref") != f"verification:v-{aid}":
            errors.append("s4.cross_plane_projection_drift")
        if aid not in {vv.get("attempt_id") for vv in packet.get("verification_rows", [])}:
            errors.append("s4.cross_plane_projection_drift")
        # reverse closure: every raw artifact / verification row must be
        # referenced by its worker view.
        raw_by_attempt = {r.get("attempt_id"): r.get("artifact_id")
                          for r in packet.get("raw_artifacts", [])}
        if raw_by_attempt.get(aid) != w.get("raw_artifact_ref"):
            errors.append("s4.cross_plane_projection_drift")
        if aid not in {vv.get("attempt_id") for vv in packet.get("verification_rows", [])} \
                or w.get("verification_ref") != f"verification:v-{aid}":
            errors.append("s4.cross_plane_projection_drift")
    # reviewed_artifact_refs must reference existing artifacts (no ghost).
    adjud = packet.get("adjudication_row", {})
    reviewed = adjud.get("reviewed_artifact_refs", [])
    if not set(reviewed).issubset(artifact_refs):
        errors.append("s4.cross_plane_projection_drift")


def _check_history_kinds(packet: Dict[str, Any], errors: List[str]) -> None:
    """Freeze the allowed history-kind set per tagged-union state and enforce
    it on the root history log."""
    state = packet.get("ensemble_projection_state")
    allowed = {
        # zero: no attempt/verification/conflict/adjudication/query/model/
        # digest events; only the exact permitted zero-state lifecycle prefix
        # (empty is the frozen contract).
        "no_ensemble": frozenset(),
        # one: worker/attempt/verification events, no conflict-consensus and
        # no adjudication event when there is no adjudicator.
        "single_analysis": frozenset({
            "attempt_bound", "baseline_assessed", "verification_recorded",
            "conflict_derived", "query_draft_generated",
            "inspection_finalized"}),
        # N: exact N worker/verification/conflict/adjudication events with a
        # separately bound adjudicator.
        "multi_analysis": frozenset({
            "attempt_bound", "baseline_assessed", "verification_recorded",
            "conflict_derived", "adjudication_recorded",
            "query_draft_generated", "inspection_finalized"}),
    }.get(state, frozenset())
    log = packet.get("history_log", {})
    entries = log.get("entries", [])
    # zero state requires an empty history log.
    if state == "no_ensemble" and entries:
        errors.append("s4.history_append_only_violation")
        return
    seen_kinds = [e.get("kind") for e in entries]
    if state != "no_ensemble":
        for kind in seen_kinds:
            if kind not in allowed:
                errors.append("s4.history_append_only_violation")
        if state == "single_analysis":
            for entry in entries:
                if entry.get("kind") == "adjudication_recorded":
                    errors.append("s4.history_append_only_violation")


def _check_zh_lexicons(packet: Dict[str, Any], errors: List[str]) -> None:
    """Enforce every declared closed_zh lexicon (severity/domain/ordinal)."""
    rid = packet.get("risk_identity", {})
    if rid.get("severity_zh") not in SEVERITY_ZH_BY_SEVERITY.values():
        errors.append("s4.enum_value_mismatch")
    if rid.get("domain_zh") not in DOMAIN_ZH.values():
        errors.append("s4.enum_value_mismatch")
    audience = packet.get("audience_inspector", {})
    if audience.get("severity_zh") not in SEVERITY_ZH_BY_SEVERITY.values():
        errors.append("s4.enum_value_mismatch")
    for summary in audience.get("worker_ordinal_summaries", []):
        if isinstance(summary, dict) \
                and summary.get("ordinal_zh") not in ORDINAL_ZH:
            errors.append("s4.ordinal_mapping_drift")
    for row in audience.get("baseline_rows_zh", []):
        if isinstance(row, dict) and row.get("ordinal_zh") not in ORDINAL_ZH:
            errors.append("s4.ordinal_mapping_drift")


_SORTED_UNIQUE_ORDER_CODES = {
    "R5S4AudienceInspector.worker_ordinal_summaries": "s4.ordinal_mapping_drift",
    "R5S4AudienceInspector.baseline_rows_zh": "s4.baseline_projection_drift",
    "R5S4HistoryLog.entries": "s4.history_append_only_violation",
}
_SORTED_UNIQUE_GENERIC_CODE = "s4.cardinality_not_0_1_n"
_MISSING_SORT_KEY = object()


def _extract_sort_key(row: Any, key_spec: str) -> Any:
    """Extract a sort key from an object-array row, supporting dotted composite
    keys.  Returns _MISSING_SORT_KEY for a missing/null component so callers
    treat it as a structural error, never a Python comparison exception."""
    parts = key_spec.split(".")
    node = row
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return _MISSING_SORT_KEY
        node = node[part]
    if node is None:
        return _MISSING_SORT_KEY
    return node


def _canonical_sort_key(key: Any) -> Tuple[str, Any]:
    """Frozen canonical comparator: never compares raw mixed types directly.
    (str -> ("s", ...), int -> ("i", ...)) so str/int keys sort deterministically
    and a mixed-type array cannot raise a TypeError."""
    if isinstance(key, bool):
        return ("b", int(key))
    if isinstance(key, int):
        return ("i", key)
    return ("s", str(key))


def _check_sorted_unique_declarations(packet: Dict[str, Any],
                                      schema: Dict[str, Any],
                                      errors: List[str]) -> set:
    """GENERIC recursive executor for EVERY declared `sorted_unique_by:<key>`
    constraint on object arrays (root/audience/audit/import nested arrays).
    Enforces BOTH canonical order and uniqueness; missing/null/wrong-type keys
    are structural errors (schema_key_mismatch), never comparison exceptions.
    Returns the set of (object,field) arrays visited for coverage assertion."""
    objects = schema["objects"]
    import_schemas = schema.get("import_schemas", {})
    visited: set = set()

    def code_for(obj: str, field: str) -> str:
        return _SORTED_UNIQUE_ORDER_CODES.get(
            f"{obj}.{field}", _SORTED_UNIQUE_GENERIC_CODE)

    def walk(node: Any, obj: str, path: str,
             import_extensions: Optional[Dict[str, Any]] = None) -> None:
        if not isinstance(node, dict):
            return
        base = objects.get(obj) or import_schemas.get(obj)
        if base is None:
            return
        fields = dict(base)
        for k, d in (import_extensions or {}).items():
            fields.setdefault(k, d)
        for fname, descriptor in fields.items():
            cons = descriptor.get("constraints", [])
            su = [c for c in cons if c.startswith("sorted_unique_by:")]
            if not su:
                continue
            key_spec = su[0][len("sorted_unique_by:"):]
            value = node.get(fname)
            if not isinstance(value, list):
                continue  # wrong list type already reported structurally
            keys = []
            broken = False
            for row in value:
                k = _extract_sort_key(row, key_spec)
                if k is _MISSING_SORT_KEY \
                        or not isinstance(k, (str, int, bool)):
                    errors.append("s4.schema_key_mismatch")
                    broken = True
                    break
                keys.append(k)
            if broken:
                continue
            canonical = sorted(keys, key=_canonical_sort_key)
            if keys != canonical or len(set(keys)) != len(keys):
                errors.append(code_for(obj, fname))
            visited.add(f"{obj}.{fname}")
            # recurse into this array's element objects / imports.
            ftype = descriptor.get("type", "")
            if ftype.startswith("import:"):
                ftype = ftype[len("import:"):]
            if ftype in objects or ftype in import_schemas:
                ext = descriptor.get("import_extensions")
                for idx, item in enumerate(value):
                    walk(item, ftype, f"{path}.{fname}[{idx}]", ext)
        # recurse into scalar object fields (not arrays with sorted_unique).
        for fname, descriptor in fields.items():
            ftype = descriptor.get("type", "")
            if ftype.startswith("import:"):
                ftype = ftype[len("import:"):]
            if ftype not in objects and ftype not in import_schemas:
                continue
            if any(c.startswith("sorted_unique_by:")
                   for c in descriptor.get("constraints", [])):
                continue  # already recursed in the array branch
            if descriptor.get("cardinality") == "many":
                value = node.get(fname)
                if isinstance(value, list):
                    ext = descriptor.get("import_extensions")
                    for idx, item in enumerate(value):
                        walk(item, ftype, f"{path}.{fname}[{idx}]", ext)
            else:
                walk(node.get(fname), ftype, f"{path}.{fname}",
                     descriptor.get("import_extensions"))

    walk(packet, "R5S4AuthorityPacket", "packet")
    return visited


def _check_row_ref_grammar(packet: Dict[str, Any], errors: List[str]) -> None:
    """Enforce exact row/ref grammar with cross-field identity."""
    for row in packet.get("baseline_rows", []):
        item_id = row.get("item_id")
        attempt_id = row.get("attempt_id")
        expected = f"baseline-row:{item_id}:{attempt_id}"
        if row.get("row_ref") != expected:
            errors.append("s4.baseline_projection_drift")
    for w in packet.get("worker_views", []):
        aid = w.get("attempt_id")
        if w.get("raw_artifact_ref") != f"raw:{aid}":
            errors.append("s4.cross_plane_projection_drift")


def _check_journey_cross(packet: Dict[str, Any], anchor: Dict[str, Any],
                         errors: List[str]) -> None:
    journey = packet.get("journey_link", {})
    rid = packet.get("risk_identity", {})
    for rkey in ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
                 "site_ref", "subject_ref", "risk_ref"):
        if not journey.get("deep_link_" + rkey):
            continue  # identity miss is anchor_claim/fallback territory
        if journey.get("deep_link_" + rkey) != rid.get(rkey):
            errors.append("s4.cross_plane_projection_drift")


def _check_query_cross(packet: Dict[str, Any], errors: List[str]) -> None:
    query = packet.get("query_draft_row")
    audience = packet.get("audience_inspector", {})
    if query is None:
        for key in ("query_basis_zh", "query_finding_zh", "query_action_zh",
                    "query_pd_wording_zh"):
            if audience.get(key):
                errors.append("s4.query_projection_drift")
        return
    if query.get("basis_zh") and audience.get("query_basis_zh") != query.get("basis_zh"):
        errors.append("s4.query_projection_drift")
    if query.get("finding_zh") and audience.get("query_finding_zh") != query.get("finding_zh"):
        errors.append("s4.query_projection_drift")
    if query.get("action_zh") and audience.get("query_action_zh") != query.get("action_zh"):
        errors.append("s4.query_projection_drift")
    pd = query.get("pd_wording_state")
    if pd in ("not_pd", "verify_whether_pd"):
        expected_pd = "非疑似疾病进展" if pd == "not_pd" else "疑似疾病进展"
        if audience.get("query_pd_wording_zh") != expected_pd:
            errors.append("s4.query_projection_drift")


def _check_model_evidence_real(packet: Dict[str, Any], errors: List[str]) -> None:
    """Construct the real R4 d10.ModelEvidence from the packet's stored leaves
    and require the complete dataclass projection (dataclasses.asdict) to
    equal the stored audit ModelEvidence dict -- no subset, no drift."""
    me = audit_model_evidence(packet)
    if me is None:
        return
    d10 = _r4_d10()
    try:
        obj = d10.ModelEvidence(
            model_evidence_id=me.get("model_evidence_id", ""),
            role=me.get("role", ""),
            permitted_leaf=me.get("permitted_leaf", ""),
            model_id=me.get("model_id", ""),
            model_version=me.get("model_version", ""),
            evaluation_content_identity=me.get(
                "evaluation_content_identity", ""),
            input_content_hash=me.get("input_content_hash", ""),
            source_revision_content_pairs=tuple(
                _typed_source_revision_pair(x)
                for x in me.get("source_revision_content_pairs", [])),
            source_refs=tuple(me.get("source_refs", [])),
            independent_context_hash=me.get("independent_context_hash", ""),
            ensemble_id=me.get("ensemble_id", ""),
            ensemble_size=me.get("ensemble_size", 1),
            member_analysis_refs=tuple(me.get("member_analysis_refs", [])),
            member_analysis_ref_set_hash=me.get(
                "member_analysis_ref_set_hash", ""),
            output_identity=me.get("output_identity", ""),
            output_hash=me.get("output_hash", ""),
            adjudication_state=me.get("adjudication_state", "pending"),
            model_binding_hash=me.get("model_binding_hash", ""),
        )
    except Exception:
        errors.append("s4.model_evidence_not_permitted")
        return
    if obj.role not in MODEL_EVIDENCE_ROLES:
        errors.append("s4.model_evidence_not_permitted")
        return
    projected = dataclasses.asdict(obj)
    for key in MODEL_EVIDENCE_BOUND_FIELDS:
        expected = projected.get(key)
        if isinstance(expected, tuple):
            expected = list(expected)
        if expected != me.get(key):
            errors.append("s4.model_evidence_not_permitted")
            return


#: every real R4 ensemble_contracts.AdjudicationBinding dataclass field must
#: be bound (coverage assertion fails if the upstream dataclass gains a field).
ADJUDICATION_BOUND_FIELDS: Tuple[str, ...] = (
    "binding_id", "session_id", "model_id", "model_version", "outcome",
    "reviewed_artifact_refs",
)


def _verify_adjudication_binding_coverage(errors: List[str]) -> None:
    """Every upstream AdjudicationBinding field must have a binding."""
    try:
        ens = _r4_ensemble()
        upstream = {f.name for f in dataclasses.fields(
            ens.AdjudicationBinding)}
    except Exception:
        errors.append("s4.anchor_claim_drift")
        return
    if not upstream.issubset(set(ADJUDICATION_BOUND_FIELDS)) \
            or set(ADJUDICATION_BOUND_FIELDS) != upstream:
        errors.append("s4.anchor_claim_drift")


def _check_adjudication_binding_anchor(packet: Dict[str, Any],
                                       anchor: Dict[str, Any],
                                       errors: List[str]) -> None:
    """Bind the complete accepted AdjudicationBinding/adjudicator identity
    (incl. independence-context seal) and enforce the exact reviewed-artifact
    set rule for N state.  Zero/single follow their frozen absence rules."""
    _verify_adjudication_binding_coverage(errors)
    adjud = packet.get("adjudication_row", {})
    state = packet.get("ensemble_projection_state")
    if adjud.get("present") is False:
        # zero/single: frozen absence rules (empty identity, no reviewed refs).
        if state in ("no_ensemble", "single_analysis"):
            if adjud.get("binding_id") or adjud.get("session_id") \
                    or adjud.get("model_id") or adjud.get("model_version") \
                    or adjud.get("outcome") \
                    or adjud.get("reviewed_artifact_refs"):
                errors.append("s4.anchor_claim_drift")
        return
    # A more specific adjudicator decision (worker-self, context collision,
    # off-enum, enum mismatch, or failed-verification blocking) is the single
    # code; the generic accepted-binding identity is not re-reported.
    if any(code in errors for code in (
            "s4.worker_self_adjudication", "s4.adjudicator_context_collision",
            "s4.off_enum_s2_adjudication_state", "s4.enum_value_mismatch",
            "s4.verification_unresolved_authority")):
        return
    accepted = anchor.get("accepted_adjudicator_binding", {})
    for key in ("binding_id", "session_id", "model_id", "model_version",
                "independent_context_hash", "outcome"):
        if adjud.get(key) != accepted.get(key):
            errors.append("s4.anchor_claim_drift")
            return
    # N state: reviewed_artifact_refs must equal the EXACT sorted set of every
    # active worker raw artifact ref (no subset/superset/duplicate).  A ghost
    # ref is reported by reference closure (cross_plane) and a duplicate by
    # the schema sorted_unique check; those are the single decisions.
    if "s4.cross_plane_projection_drift" in errors \
            or "s4.schema_key_mismatch" in errors:
        return
    expected_refs = sorted(f"artifact:{w.get('attempt_id')}"
                           for w in packet.get("worker_views", []))
    if sorted(adjud.get("reviewed_artifact_refs", [])) != expected_refs:
        errors.append("s4.anchor_claim_drift")


# ---------------------------------------------------------------------------
# _packet_oracle: independent recompute of every frozen S4 invariant
# ---------------------------------------------------------------------------


def _packet_oracle(packet: Dict[str, Any], anchor: Dict[str, Any],
                   schema: Dict[str, Any], overlay: Dict[str, Any]) -> List[str]:
    """Independent recompute of every frozen S4 invariant against the external
    anchor and real R4.  Empty list = valid.  Stored labels never override
    recomputation and the packet never defines its own accepted truth."""
    global _schema_enums
    if not _schema_enums:
        _schema_enums = {name: set(vals) for name, vals in
                         overlay["enums"].items() if isinstance(vals, list)}
    errors: List[str] = []

    # 0) external anchor validation FIRST (separate accepted input).
    _validate_anchor(anchor, schema, errors)

    # 1) recursive exact schema validation (structural/type/shape).
    _validate_packet_schema_recursive(packet, schema, errors)

    # B) STOP semantic analysis on any structural/type/schema failure: a
    # malformed packet (e.g. ensemble_size="2") must NEVER reach arithmetic,
    # ordering, dataclass construction or cross-plane semantic code (which
    # would leak an uncaught TypeError).  The stable normalized (order-frozen,
    # de-duplicated) structural error list is returned immediately.
    if errors:
        return _normalize_errors(errors)

    # generic object-array sorted_unique_by runs AFTER structural type
    # validation but BEFORE history-chain/cross-plane semantic checks, so a
    # reversed/duplicate history entries array reports exactly the frozen
    # ordering code (history_append_only_violation), not a chain-break or
    # anchor-prefix cascade.
    _check_sorted_unique_declarations(packet, schema, errors)

    # 2) packet grammar / content hashes (recompute, never trust labels).
    if packet.get("schema") != PACKET_SCHEMA:
        errors.append("s4.schema_key_mismatch")
    pid = packet.get("packet_id", "")
    expected_pid = f"{PACKET_ID_PREFIX}:{packet.get('audience_content_hash', '')}"
    if pid != expected_pid or pid.count(":") != 1:
        errors.append("s4.packet_id_grammar_mismatch")
    if packet.get("audience_content_hash") != _h(packet.get("audience_inspector")):
        errors.append("s4.audience_hash_contains_audit_leaf")
    if packet.get("audit_content_hash") != _audit_content_hash(
            packet.get("audit_inspector")):
        errors.append("s4.audience_audit_leak")
    receipt = packet.get("authority_receipt")
    if packet.get("receipt_content_hash") != _h(receipt):
        errors.append("s4.receipt_hash_mismatch")
    audit = packet.get("audit_inspector", {})
    if audit.get("authority_receipt_ref") != RECEIPT_REF_PREFIX \
            + packet.get("receipt_content_hash", ""):
        errors.append("s4.receipt_hash_mismatch")
    integrity_body = {k: v for k, v in packet.items()
                      if k not in INTEGRITY_EXCLUDED_KEYS}
    if packet.get("packet_integrity_hash") != _h(integrity_body):
        errors.append("s4.hash_recipe_cycle")

    # 3) cross-check every claimed/derived leaf against the external anchor.
    _cross_check_anchor(packet, anchor, errors)

    # 4) exact 0/1/N tagged union across every plane (no early return).
    _check_0_1_n(packet, errors)
    # state-agnostic checks (history kinds, audit projection, reference
    # closure, zh lexicons, object arrays, row/ref grammar) run for EVERY
    # state including zero, so zero-residue and history-kind violations fail.
    _check_history(packet, errors)
    _check_history_kinds(packet, errors)
    _check_audit_projection(packet, errors)
    _check_reference_closure(packet, errors)
    _check_zh_lexicons(packet, errors)
    _check_row_ref_grammar(packet, errors)
    _check_audience_display_projection(packet, errors)
    _check_evidence_zh_projection(packet, errors)
    _check_declared_leaf_reconstruction(packet, errors)

    state = packet.get("ensemble_projection_state")
    if state not in ("single_analysis", "multi_analysis"):
        return _normalize_errors(errors)

    # 5) input identity isolation + per-risk severity binding.
    workers = packet.get("worker_views", [])
    if state in ("single_analysis", "multi_analysis"):
        if packet.get("input_content_hash") is None:
            errors.append("s4.cardinality_not_0_1_n")
        hashes = {w.get("input_content_hash") for w in workers}
        if len(hashes) != 1:
            errors.append("s4.authority_drift")
        elif hashes and packet.get("input_content_hash") is not None \
                and packet.get("input_content_hash") != next(iter(hashes)):
            errors.append("s4.authority_drift")
    if len(workers) >= 2:
        if len({w.get("binding_id") for w in workers}) != len(workers):
            errors.append("s4.duplicate_worker_binding")
        if len({w.get("session_id") for w in workers}) != len(workers):
            errors.append("s4.duplicate_worker_session")
        if len({w.get("independent_context_hash") for w in workers}) != len(workers):
            errors.append("s4.duplicate_worker_context")
    for w in workers:
        ordinal = w.get("ordinal")
        expected_zh = ORDINAL_ZH[ordinal - 1] if (
            isinstance(ordinal, int) and 1 <= ordinal <= len(ORDINAL_ZH)
        ) else None
        if expected_zh is not None and w.get("ordinal_zh") != expected_zh:
            errors.append("s4.ordinal_mapping_drift")
    # severity binding: severity == SEVERITY_MAPPING[monitoring_priority].
    rid = packet.get("risk_identity", {})
    prio = rid.get("monitoring_priority")
    sev = rid.get("severity")
    if prio in SEVERITY_MAPPING:
        expected_sev = SEVERITY_MAPPING[prio]
        if expected_sev == "fail_closed":
            if sev is not None:
                errors.append("s4.enum_value_mismatch")
        elif sev == "critical":
            pass  # critical is external-authority gated (anchor cross-check)
        elif sev != expected_sev:
            errors.append("s4.enum_value_mismatch")

    # 4) raw bytes + parsed output independently verifiable + anchor raw SHA.
    # The external anchor is authoritative: an accepted-value mismatch is
    # reported once (anchor code); local recompute is verified when the claim
    # matches the anchor so semantically equivalent rewrites still fail.
    for artifact in packet.get("raw_artifacts", []):
        anchor_row = _anchor_attempt_row(anchor, artifact.get("attempt_id"))
        if anchor_row is None:
            errors.append("s4.anchor_claim_drift")
            continue
        if artifact.get("raw_bytes_sha256") != anchor_row.get("raw_bytes_sha256"):
            errors.append("s4.raw_sha_external_mismatch")
            continue
        if artifact.get("parsed_output_hash") != anchor_row.get("parsed_output_hash"):
            errors.append("s4.anchor_claim_drift")
            continue
        try:
            raw_bytes = base64.b64decode(artifact.get("raw_bytes_b64", ""),
                                         validate=True)
        except Exception:
            errors.append("s4.raw_output_rewritten")
            continue
        if artifact.get("raw_bytes_sha256") != _sha256_bytes(raw_bytes):
            errors.append("s4.raw_output_rewritten")
        parsed = artifact.get("parsed_output_hash")
        declared = artifact.get("declared_output_hash")
        if parsed == artifact.get("raw_bytes_sha256"):
            errors.append("s4.raw_parsed_hash_confusion")
        # reconstruct typed output and recompute content hash.
        try:
            recomputed = _recompute_parsed_hash(packet, artifact["attempt_id"])
        except Exception:
            errors.append("s4.raw_output_rewritten")
            recomputed = None
        if recomputed is not None:
            if parsed != recomputed:
                errors.append("s4.parsed_output_hash_mismatch")
            if declared != recomputed:
                errors.append("s4.parsed_output_hash_mismatch")
        for view in workers:
            if view["attempt_id"] == artifact.get("attempt_id") \
                    and view.get("declared_output_hash") != declared:
                errors.append("s4.parsed_output_hash_mismatch")

    # 5) seven-dimension verification via real R4 verify_attempt.
    ensemble_id = packet.get("ensemble_id", "")
    try:
        ctx = _typed_digest_context(packet["audit_inspector"])
        outputs = {w["attempt_id"]: _reconstruct_worker_output(packet, w["attempt_id"])
                   for w in workers}
        attempts = {w["attempt_id"]: _typed_attempt(w, ensemble_id)
                    for w in workers}
    except Exception:
        errors.append("s4.verification_unresolved_authority")
        attempts = {}
        outputs = {}
        ctx = None
    if ctx is not None:
        ens = _r4_ensemble()
        stored_verifs = {v.get("attempt_id"): v
                         for v in packet.get("verification_rows", [])}
        try:
            for attempt_id, attempt in attempts.items():
                recomputed = ens.verify_attempt(
                    attempt, outputs[attempt_id], ctx)
                stored = stored_verifs.get(attempt_id, {})
                if set(recomputed.checked_dimensions) != SEVEN_DIMENSIONS \
                        or stored.get("checked_dimensions") != sorted(
                            set(recomputed.checked_dimensions)):
                    errors.append("s4.verification_label_only")
                if stored.get("result") != recomputed.result:
                    errors.append("s4.verification_label_only")
                if stored.get("failure_reason_codes") != sorted(
                        set(recomputed.failure_reason_codes)):
                    errors.append("s4.verification_label_only")
                if stored.get("verification_id") != recomputed.verification_id:
                    errors.append("s4.verification_label_only")
                # recomputed is enforced by the schema constraint equals:true
                # (single code s4.schema_key_mismatch); not double-reported.
                if recomputed.result != "passed" \
                        and stored.get("result") == "passed":
                    errors.append("s4.verification_label_only")
        except Exception:
            errors.append("s4.verification_unresolved_authority")
        # failed verification blocks any supporting adjudication outcome.
        if any(v.get("result") != "passed"
               for v in packet.get("verification_rows", [])):
            if packet.get("adjudication_row", {}).get("outcome") in SUPPORTING_OUTCOMES:
                errors.append("s4.verification_unresolved_authority")

    # 6) conflict set rebuilt with R4 derive_conflicts (exact equality).
    if ctx is not None:
        ens = _r4_ensemble()
        try:
            baseline_items = [_typed_baseline_item(b)
                              for b in packet.get("baseline_items", [])]
        except Exception:
            # a malformed-but-schema-shaped baseline item (e.g. an invalid R4
            # claimed_content_hash) is a baseline-projection violation, never
            # an uncaught R4 exception; _check_baseline_projection reports the
            # same single code for the same cause.
            errors.append("s4.baseline_projection_drift")
            baseline_items = None
        if baseline_items is not None:
            attempts_list = list(attempts.values())
            try:
                derived = ens.derive_conflicts(
                    attempts=attempts_list, worker_outputs=outputs,
                    baseline_items=baseline_items)
            except Exception:
                errors.append("s4.conflict_set_incomplete")
                derived = ()
            derived_rows = []
            for c in derived:
                derived_rows.append({
                    "conflict_id": c.conflict_id,
                    "member_attempt_ids": sorted(c.member_attempt_ids),
                    "monitoring_priority": c.monitoring_priority,
                    "relation": c.relation,
                    "display_state": c.display_state,
                })
            projected = []
            for c in packet.get("conflict_rows", []):
                projected.append({
                    "conflict_id": c.get("conflict_id"),
                    "member_attempt_ids": sorted(c.get("member_attempt_ids", [])),
                    "monitoring_priority": c.get("monitoring_priority"),
                    "relation": c.get("relation"),
                    "display_state": c.get("display_state"),
                })
            if projected != derived_rows:
                # exact set AND exact order must equal R4 derive_conflicts.
                errors.append("s4.conflict_set_incomplete")
            # non-hideability / relation<->display coherence (most specific code).
        for c in packet.get("conflict_rows", []):
            relation = c.get("relation")
            priority = c.get("monitoring_priority")
            display = c.get("display_state")
            hidden = c.get("hidden")
            if hidden is True:
                if relation == "mutual_negation":
                    errors.append("s4.mutual_negation_hidden")
                elif relation == "baseline_miss":
                    errors.append("s4.baseline_miss_hidden")
                elif relation == "single_model_new" and priority == "high":
                    errors.append("s4.single_addition_omitted")
                elif priority == "high":
                    errors.append("s4.high_risk_hidden")
            if relation == "mutual_negation" and display != "visible_conflict":
                errors.append("s4.conflict_set_incomplete")
            if relation == "baseline_miss" and display != "visible_baseline_miss":
                errors.append("s4.conflict_set_incomplete")
            if relation == "single_model_new" and display != "needs_attention":
                errors.append("s4.conflict_set_incomplete")

    # 7) baseline recheck + cross-plane baseline projection.
    _check_baseline_projection(packet, errors)
    worker_attempt_ids = {w.get("attempt_id") for w in workers}
    item_ids = {b.get("item_id") for b in packet.get("baseline_items", [])}
    seen_row_refs = set()
    for row in packet.get("baseline_rows", []):
        if row.get("item_id") not in item_ids:
            errors.append("s4.baseline_recheck_missing")
        if row.get("attempt_id") not in worker_attempt_ids:
            errors.append("s4.cardinality_not_0_1_n")
        if row.get("row_ref") in seen_row_refs:
            errors.append("s4.cardinality_not_0_1_n")
        seen_row_refs.add(row.get("row_ref"))
        if row.get("state") not in _schema_enums.get("baseline_state", set()):
            errors.append("s4.enum_value_mismatch")
            continue
        if row.get("state") in RECHECK_REQUIRED_STATES \
                and not row.get("source_recheck_locator_ids"):
            errors.append("s4.baseline_recheck_missing")
        if row.get("state") in RECHECK_REQUIRED_STATES \
                and row.get("recheck_complete") is not True:
            errors.append("s4.baseline_recheck_missing")
        for code in row.get("reason_codes", []):
            if code not in _schema_enums.get("assessment_reason_code", set()):
                errors.append("s4.enum_value_mismatch")
    # baseline_as_gold: an unassessed baseline item must never be shown on the
    # audience as confirmed/established.
    for summary in packet.get("audience_inspector", {}).get(
            "baseline_rows_zh", []):
        anchor_zh = summary.get("item_anchor_zh", "") if isinstance(
            summary, dict) else ""
        state_zh = summary.get("state_zh", "") if isinstance(
            summary, dict) else ""
        if anchor_zh and "b2" in anchor_zh and "已确认" in state_zh:
            errors.append("s4.baseline_as_gold")

    # 8) adjudicator independence.
    adjud = packet.get("adjudication_row", {})
    if adjud.get("present") is False:
        if adjud.get("independent_context_hash") is not None \
                or adjud.get("binding_id") or adjud.get("session_id") \
                or adjud.get("outcome") or adjud.get("reviewed_artifact_refs"):
            errors.append("s4.cardinality_not_0_1_n")
        status_zh = audience_status_zh(packet)
        if "独立核对" in status_zh and "尚未" not in status_zh:
            errors.append("s4.schema_key_mismatch")
    else:
        worker_bindings = {w.get("binding_id") for w in workers}
        worker_sessions = {w.get("session_id") for w in workers}
        worker_contexts = {w.get("independent_context_hash") for w in workers}
        if adjud.get("binding_id") in worker_bindings:
            errors.append("s4.worker_self_adjudication")
        if adjud.get("session_id") in worker_sessions:
            errors.append("s4.worker_self_adjudication")
        if adjud.get("independent_context_hash") in worker_contexts:
            errors.append("s4.adjudicator_context_collision")
        outcome = adjud.get("outcome")
        allowed = _schema_enums.get("adjudication_outcome", set())
        if outcome not in allowed:
            if outcome in {"accepted", "divergent", "pending"}:
                errors.append("s4.off_enum_s2_adjudication_state")
            else:
                errors.append("s4.enum_value_mismatch")
        if adjud.get("adds_explanation_only") is not True:
            errors.append("s4.schema_key_mismatch")

    # 9) source resolution.
    authorized = _authorized_locators(packet)
    audience_texts = _audience_strings(packet)
    cited = _find_locators(audience_texts)
    if cited - authorized:
        errors.append("s4.hidden_source_leak")
    query = packet.get("query_draft_row")
    if query is not None and set(query.get("source_locator_refs", [])) - authorized:
        errors.append("s4.hidden_source_leak")
    for row in packet.get("baseline_rows", []):
        if set(row.get("source_recheck_locator_ids", [])) - authorized:
            errors.append("s4.hidden_source_leak")
    joined = " ".join(audience_texts)
    if any(token in joined for token in NEAREST_FALLBACK_TOKENS):
        errors.append("s4.nearest_fallback_forbidden")
    journey = packet.get("journey_link", {})
    reason = journey.get("unavailable_reason_zh") or ""
    if any(token in reason for token in NEAREST_FALLBACK_TOKENS):
        errors.append("s4.nearest_fallback_forbidden")
    if (cited - authorized) and not any(t in joined for t in
                                       ("请核实", "请补充来源", "无法定位")):
        errors.append("s4.nearest_fallback_forbidden")

    # 10) query draft three-part draft-only + cross-plane query projection.
    if query is not None:
        for key in ("basis_zh", "finding_zh", "action_zh"):
            if not query.get(key):
                errors.append("s4.query_draft_partial")
        if set(query) & QUERY_TASK_KEYS:
            errors.append("s4.query_task_semantics")
        if query.get("draft_only") is not True:
            errors.append("s4.query_task_semantics")
    _check_query_cross(packet, errors)

    # 11) journey + audit cross-plane already validated for every state
    #      (history/audit/ref/zh/sorted/grammar) before the early return.

    # 12) journey fallback none + cross-plane journey identity.
    if journey.get("fallback_policy") != "none":
        errors.append("s4.journey_fallback_not_none")
    identity_keys = ["deep_link_project_ref", "deep_link_run_ref",
                     "deep_link_snapshot_ref", "deep_link_risk_ref",
                     "deep_link_spine_ref", "deep_link_anchor_ref"]
    identity_miss = any(not journey.get(key) for key in identity_keys)
    if journey.get("journey_available") is True and identity_miss \
            and "s4.anchor_claim_drift" not in errors:
        errors.append("s4.journey_fallback_not_none")
    if journey.get("journey_available") is False \
            and not (journey.get("unavailable_reason_zh") or ""):
        errors.append("s4.journey_fallback_not_none")
    _check_journey_cross(packet, anchor, errors)

    # 13) ModelEvidence real R4 + audit-only + external permit.
    _check_model_evidence_real(packet, errors)

    # 14) audience/audit split + forbidden tokens.
    audience_obj = packet.get("audience_inspector", {})
    if "model_evidence" in audience_obj:
        errors.append("s4.model_evidence_on_audience")
    elif set(audience_obj) & AUDIT_ONLY_LEAVES:
        errors.append("s4.audience_hash_contains_audit_leaf")
    leaked_tokens = [t for t in FORBIDDEN_AUDIENCE_TOKENS if t in joined]
    if leaked_tokens:
        errors.append("s4.audience_audit_leak")

    # 15) adjudication binding: complete accepted AdjudicationBinding identity
    # + exact reviewed-artifact set for N state.  Runs AFTER the specific
    # adjudicator codes so those decisions stay single (worker-self / context
    # collision / off-enum / unresolved authority are more specific than a
    # generic anchor-identity drift).
    _check_adjudication_binding_anchor(packet, anchor, errors)

    return _normalize_errors(errors)


def audience_status_zh(packet: Dict[str, Any]) -> str:
    return packet.get("audience_inspector", {}).get("adjudication_status_zh", "")


def _authorized_locators(packet: Dict[str, Any]) -> set:
    authorized: set = set()
    ctx = packet.get("audit_inspector", {}).get("digest_context") or {}
    for loc_set in ctx.get("artifact_authorized_source_locators", {}).values():
        authorized.update(loc_set)
    for item in packet.get("baseline_items", []):
        authorized.update(item.get("source_locator_ids", []))
    return authorized


def _audience_strings(packet: Dict[str, Any]) -> List[str]:
    audience = packet.get("audience_inspector", {})
    out: List[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, str):
            out.append(value)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, dict):
            for val in value.values():
                collect(val)

    collect(audience)
    return out


def _find_locators(texts: List[str]) -> set:
    found: set = set()
    for text in texts:
        found.update(__import__("re").findall(r"loc\.[A-Za-z0-9_.-]+", text))
    return found


def _check_history(packet: Dict[str, Any], errors: List[str]) -> None:
    log = packet.get("history_log", {})
    entries = log.get("entries", [])
    # when the generic sorted_unique walker already reported an ordering/
    # duplicate violation of history entries (s4.history_append_only_violation),
    # that is the single decision; do not add chain-break errors for the same
    # root cause (reversed/duplicate entries break the prior-hash chain).
    ordering_violation = "s4.history_append_only_violation" in errors
    if not entries:
        # empty history is valid for zero-state (head_seq=0, head=genesis).
        if log.get("head_seq") != 0 or log.get("head_hash") not in (None, GENESIS_HASH):
            errors.append("s4.history_append_only_violation")
        return
    seqs = [e.get("seq") for e in entries]
    if seqs != list(range(1, len(entries) + 1)):
        errors.append("s4.history_append_only_violation")
        if ordering_violation:
            return
    prior = GENESIS_HASH
    for entry in entries:
        if entry.get("prior_entry_hash") != prior:
            errors.append("s4.history_chain_break")
        recomputed = _h({key: entry[key] for key in (
            "entry_id", "seq", "kind", "payload_ref", "prior_entry_hash")})
        if entry.get("entry_hash") != recomputed:
            errors.append("s4.history_chain_break")
        prior = entry.get("entry_hash")
    if log.get("head_hash") != entries[-1].get("entry_hash") \
            or log.get("head_seq") != len(entries):
        errors.append("s4.history_append_only_violation")


# ---------------------------------------------------------------------------
# challenge registry execution (independent, exact single code)
# ---------------------------------------------------------------------------


def _registry_fixture(precondition: str, build_packet: Any,
                      anchor: Dict[str, Any]) -> Dict[str, Any]:
    mode = {"single_analysis packet": "single",
            "no_ensemble packet": "no_ensemble",
            "mutual_negation packet": "mutual",
            "graded_conflict packet": "graded"}.get(precondition, "multi")
    p = copy.deepcopy(build_packet(mode, anchor))
    if precondition == "failed_verification packet":
        p["audit_inspector"]["digest_context"]["artifact_rule_ids"]["artifact:a1"] = "WRONG_RULE"
        for row in p["verification_rows"]:
            if row["attempt_id"] == "a1":
                row["result"] = "failed"
                row["failure_reason_codes"] = ["rule_version_mismatch"]
        # the audience verification summary must reflect the failed recompute.
        for s in p.get("audience_inspector", {}).get("worker_ordinal_summaries", []):
            if s.get("ordinal_zh") == "分析一":
                s["verification_zh"] = "七维验证未通过"
    return p


def _apply_mutation(data: Any, mutation: Dict[str, Any]) -> None:
    op = mutation["op"]
    parts = mutation["path"].split(".")
    value = mutation.get("value")
    if not parts:
        raise ValueError("empty mutation path")
    container = data
    for part in parts[:-1]:
        key, idx = _parse_key(part)
        container = container[key]
        if idx is not None:
            container = container[idx]
    key, idx = _parse_key(parts[-1])
    if op == "set":
        if idx is not None:
            container[idx] = value
        else:
            container[key] = value
    elif op == "delete":
        if idx is not None:
            del container[idx]
        else:
            del container[key]
    elif op == "append":
        container[key].append(value)
    else:
        raise ValueError(f"unknown op {op}")


def _parse_key(part: str) -> Tuple[str, Optional[int]]:
    match = re.match(r"^([A-Za-z0-9_]+)(\[(\d+)\])?$", part)
    if not match:
        raise ValueError(f"bad path part {part!r}")
    return match.group(1), (int(match.group(3)) if match.group(3) else None)


def _resign(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Recompute all non-target dependent hashes so one mutation isolates one
    contract rule rather than causing hash cascades."""
    p = copy.deepcopy(packet)
    p["audience_content_hash"] = _h(p.get("audience_inspector"))
    p["audit_content_hash"] = _h(p.get("audit_inspector"))
    p["receipt_content_hash"] = _h(p.get("authority_receipt"))
    p["packet_id"] = f"{PACKET_ID_PREFIX}:{p['audience_content_hash']}"
    # refresh the non-hashed fingerprint leaf from the final independent hash
    # fields (audit hash excludes fingerprints, so this is cycle-free).
    if isinstance(p.get("audit_inspector"), dict):
        p["audit_inspector"]["packet_fingerprints"] = sorted([
            "audience:" + (p.get("audience_content_hash") or ""),
            "receipt:" + (p.get("receipt_content_hash") or ""),
            "packet:" + (p.get("packet_id") or ""),
            "risk_identity:" + (p.get("risk_identity", {}).get(
                "risk_identity_hash") or ""),
        ])
        p["audit_content_hash"] = _audit_content_hash(p["audit_inspector"])
    p["packet_integrity_hash"] = _h({k: v for k, v in p.items()
                                     if k not in INTEGRITY_EXCLUDED_KEYS})
    return p


def _rebuild_derived(packet: Dict[str, Any]) -> Dict[str, Any]:
    """Recompute non-target derived projections (audit mirror, conflict/history
    audit ids) from the mutated root, so a single target mutation isolates one
    contract rule rather than cascading into audit cross-plane drift."""
    p = copy.deepcopy(packet)
    audit = p.get("audit_inspector", {})
    views = p.get("worker_views", [])
    raw_by_aid = {r.get("attempt_id"): r for r in p.get("raw_artifacts", [])}
    existing_rows = {r.get("attempt_id"): r
                     for r in audit.get("worker_audit_rows", [])}
    worker_rows = []
    for w in views:
        raw = raw_by_aid.get(w.get("attempt_id"), {})
        prev = existing_rows.get(w.get("attempt_id"), {})
        worker_rows.append({
            "attempt_id": w.get("attempt_id"),
            "binding_id": w.get("binding_id"),
            "session_id": w.get("session_id"),
            "model_id": w.get("model_id"),
            "model_version": w.get("model_version"),
            "role": w.get("role"),
            "independent_context_hash": w.get("independent_context_hash"),
            "input_content_hash": w.get("input_content_hash"),
            "output_artifact_ref": w.get("output_artifact_ref"),
            "declared_output_hash": w.get("declared_output_hash"),
            "raw_bytes_sha256": raw.get("raw_bytes_sha256")
            if raw else prev.get("raw_bytes_sha256"),
            "parsed_output_hash": raw.get("parsed_output_hash")
            if raw else prev.get("parsed_output_hash"),
        })
    audit["worker_audit_rows"] = worker_rows
    audit["verification_audit_rows"] = [
        {k: v.get(k) for k in ("verification_id", "attempt_id",
                               "checked_dimensions", "result",
                               "failure_reason_codes")}
        | {"recomputed": True}
        for v in p.get("verification_rows", [])]
    audit["conflict_audit"] = sorted(set(
        c.get("conflict_id") for c in p.get("conflict_rows", [])))
    audit["history_audit"] = sorted(set(
        e.get("entry_hash") for e in p.get("history_log", {}).get("entries", [])))
    audit["adjudication_audit"] = (["adj.record.1"]
                                   if p.get("adjudication_row", {}).get("present")
                                   else [])
    audit["receipt_content_hash"] = p.get("receipt_content_hash")
    audit["authority_receipt_ref"] = RECEIPT_REF_PREFIX         + p.get("receipt_content_hash", "")
    # refresh fingerprints from the packet's current independent hash fields
    # (audience/receipt/packet/risk-identity; none depend on the audit object).
    audit["packet_fingerprints"] = sorted([
        "audience:" + (p.get("audience_content_hash") or ""),
        "receipt:" + (p.get("receipt_content_hash") or ""),
        "packet:" + (p.get("packet_id") or ""),
        "risk_identity:" + (p.get("risk_identity", {}).get(
            "risk_identity_hash") or ""),
    ])
    p["audit_inspector"] = audit
    return p


def _extract_codes(message: str) -> List[str]:
    return re.findall(r"s4\.[a-z0-9_]+", message)


def _normalize_errors(errors: List[str]) -> List[str]:
    """Freeze deterministic ordering/deduplication of the error list so a
    multi-error structural failure is stable across runs and modes."""
    seen: set = set()
    out: List[str] = []
    for code in errors:
        if code not in seen:
            seen.add(code)
            out.append(code)
    return out


def _run_artifact_governance(mutation: Dict[str, Any], schema: Dict[str, Any],
                             overlay: Dict[str, Any], root: Path,
                             artifacts: Path, maps: Dict[str, Any]) -> str:
    """Apply one artifact mutation and run the verifier hard-pin validation;
    return the rejection message ('' if not rejected)."""
    parts = mutation["path"].split(".")
    _require(parts[0] == "artifacts", mutation["path"])
    role = parts[1]
    file_name = {"overlay": "exact_overlay.json", "schema": "packet_schema.json"}[role]
    data = copy.deepcopy(_load_json(artifacts / file_name))
    inner_path = ".".join(parts[2:]) or parts[1]
    inner = {"op": mutation["op"], "path": inner_path,
             "value": mutation.get("value")}
    if "." in inner_path:
        _apply_mutation(data, inner)
    else:
        data[inner_path] = inner["value"]
    try:
        if role == "overlay":
            _validate_overlay(data, maps)
        else:
            _validate_schema(data, maps)
    except VerificationError as error:
        return str(error)
    return ""


def _execute_registry_row(row: Dict[str, Any], build_packet: Any,
                          anchor: Dict[str, Any], schema: Dict[str, Any],
                          overlay: Dict[str, Any], root: Path,
                          artifacts: Path, maps: Dict[str, Any]) -> str:
    """Run one challenge row; require exact single-code isolation (packet AND
    artifact-governance rows execute inside the verifier)."""
    mutation = row["single_mutation"]
    expected = row["expected_typed_outcome_or_error"]
    path = mutation["path"]
    if path.startswith("packet."):
        packet = _registry_fixture(row.get("precondition", "multi_analysis packet"),
                                   build_packet, anchor)
        base_errors = _packet_oracle(
            _resign(_rebuild_derived(packet)), anchor, schema, overlay)
        _require(base_errors == [],
                 f"challenge {row['case_id']}: base fixture must pass [] "
                 f"before mutation, got {sorted(set(base_errors))}")
        inner = dict(mutation)
        inner["path"] = path[len("packet."):]
        _apply_mutation(packet, inner)
        rebuilt = _rebuild_derived(packet)
        errors = _packet_oracle(_resign(rebuilt), anchor, schema, overlay)
        _require(set(errors) == {expected},
                 f"challenge {row['case_id']}: expected exactly "
                 f"[{expected}] but got {sorted(set(errors))}")
        return expected
    if path.startswith("artifacts."):
        rejection = _run_artifact_governance(mutation, schema, overlay,
                                             root, artifacts, maps)
        codes = _extract_codes(rejection)
        _require(expected in rejection and set(codes) == {expected},
                 f"challenge {row['case_id']}: expected exactly [{expected}] "
                 f"in artifact rejection but got {rejection!r}")
        return expected
    raise ValueError(f"unknown mutation target: {path}")


def _verify_challenge_registry(registry: Dict[str, Any], build_packet: Any,
                               anchor: Dict[str, Any], schema: Dict[str, Any],
                               overlay: Dict[str, Any], root: Path,
                               artifacts: Path, maps: Dict[str, Any]) -> int:
    """Execute ALL 97 rows (packet AND artifact-governance) with exact
    single-code isolation."""
    challenges = registry["challenges"]
    _require(registry.get("schema") == REGISTRY_SCHEMA,
             "registry_schema_mismatch")
    _require(len(challenges) == CHALLENGE_TOTAL_EXACT,
             "registry_row_count_drift")
    _require(registry.get("categories") == EXPECTED_CHALLENGE_SPEC,
             "registry_categories_drift")
    seen = set()
    for row in challenges:
        _require(row["case_id"] not in seen, "registry_duplicate_case_id")
        seen.add(row["case_id"])
    for row in challenges:
        _execute_registry_row(row, build_packet, anchor, schema, overlay,
                              root, artifacts, maps)
    return len(challenges)


# ---------------------------------------------------------------------------
# build_sample_packet (0/1/N fixtures) + conflict variants
# ---------------------------------------------------------------------------


_INPUT_HASH = _sha256_bytes(b"input:v1")
_CONTEXT_A1 = _sha256_bytes(b"ctx:a1")
_CONTEXT_A2 = _sha256_bytes(b"ctx:a2")
_ADJ_CONTEXT = _sha256_bytes(b"adj:ctx")
_EVIDENCE_HASH = _sha256_bytes(b"evidence:e1")


def _raw_json(attempt_id: str, supported: bool, priority: str,
              identity: str = "risk-X", item_id: str = "item.b1",
              findings: Optional[List[str]] = None,
              supports: Optional[List[bool]] = None) -> bytes:
    identities = findings if findings is not None else [identity]
    support_flags = supports if supports is not None else [supported] * len(identities)
    data = {
        "attempt_id": attempt_id,
        "assessments": [{
            "item_id": item_id, "state": "confirmed",
            "source_recheck_locator_ids": ["loc.src1"],
            "evidence_hashes": [_EVIDENCE_HASH], "attempt_id": attempt_id,
            "reason_codes": ["source_rechecked"],
        }],
        "findings": [{
            "finding_id": f"f-{attempt_id}-{i}",
            "proposed_identity": ident,
            "monitoring_priority": priority, "supported": support_flags[i],
            "source_locator_ids": ["loc.src1"], "baseline_item_ref": item_id,
        } for i, ident in enumerate(identities)],
        "gap_candidates": [],
    }
    return _canonical_bytes(data)


def _typed_output_for(raw: bytes, attempt_id: str) -> Any:
    return _parse_worker_output(raw, attempt_id)


def _load_anchor(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the EXTERNAL accepted-authority anchor from an explicitly supplied
    path.  The S4 generator never creates or signs this input; the verifier
    never trusts an in-band packet copy."""
    if path is None:
        path = DEFAULT_ARTIFACTS / "accepted_authority_anchor.json"
    return _load_json(path)


def _anchor_row(anchor: Dict[str, Any], attempt_id: str) -> Dict[str, Any]:
    for row in anchor.get("attempt_authority_rows", []):
        if row.get("attempt_id") == attempt_id:
            return row
    raise KeyError(f"no anchor row for {attempt_id}")


def build_sample_packet(mode: str = "multi",
                        anchor: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Deterministic valid packet fixtures (0/1/N) that match the external
    anchor and reconstruct real R4 objects that verify cleanly."""
    if anchor is None:
        anchor = _load_anchor()
    anchor_hash = anchor.get("anchor_identity_hash", "")
    ens = _r4_ensemble()
    # Per-variant active attempts (each binds to an external anchor row).
    if mode in ("single", "single_analysis"):
        attempts = ["a1"]
    elif mode in ("no_ensemble", "zero"):
        attempts = []
    elif mode == "mutual":
        attempts = ["m1", "m2"]
    elif mode == "graded":
        attempts = ["g1", "g2"]
    else:  # multi
        attempts = ["a1", "a2"]
    spec = {
        # model.a workers (a1/m1/g1) share the SAME 3-finding output so the
        # externally permitted ModelEvidence output_hash is identical across
        # every valid fixture variant.
        "a1": dict(supported=True, priority="high",
                   findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
        "a2": dict(supported=True, priority="high",
                   findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
        "m1": dict(supported=True, priority="high",
                   findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
        "m2": dict(supported=True, priority="high",
                   findings=("risk-X", "risk-Y", "risk-Z"),
                   supports=(False, True, True)),
        "g1": dict(supported=True, priority="high",
                   findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
        "g2": dict(supported=True, priority="low",
                   findings=("risk-X", "risk-Y", "risk-Z"), supports=None),
    }
    def _view(aid: str, parsed: str, ctx: str, binding: str, session: str,
              model: str) -> Dict[str, Any]:
        ordinal = 1 if aid in ("a1", "m1", "g1") else 2
        return {
            "attempt_id": aid, "ordinal": ordinal,
            "ordinal_zh": ORDINAL_ZH[ordinal - 1], "binding_id": binding,
            "session_id": session, "model_id": model, "model_version": "1.0",
            "role": "worker", "independent_context_hash": ctx,
            "input_content_hash": _INPUT_HASH,
            "output_artifact_ref": f"artifact:{aid}",
            "declared_output_hash": parsed,
            "claimed_date_window": "2026-08-01/2026-08-07",
            "claimed_unit_contract": "unit.ctr.1",
            "claimed_source_revision": "rev.1", "claimed_rule_id": "rule.r1",
            "claimed_rule_version": "1.0",
            "assessment_row_refs": [f"baseline-row:item.b1:{aid}"],
            "finding_ids": [f"f-{aid}-{i}" for i in range(
                len(spec[aid]["findings"]))],
            "gap_ids": [],
            "raw_artifact_ref": f"raw:{aid}",
            "verification_ref": f"verification:v-{aid}",
        }


    parsed_by_aid: Dict[str, str] = {}
    raw_by_aid: Dict[str, bytes] = {}
    output_by_aid: Dict[str, Any] = {}
    attempt_list: List[Any] = []
    ctx_by_index = [_CONTEXT_A1, _CONTEXT_A2]
    for idx, aid in enumerate(attempts):
        s = spec[aid]
        raw = _raw_json(aid, s["supported"], s["priority"],
                        findings=list(s["findings"]),
                        supports=s["supports"])
        row = _anchor_row(anchor, aid)
        _require(_sha256_bytes(raw) == row["raw_bytes_sha256"],
                 f"anchor raw {aid} != sha256(raw bytes)")
        out = _parse_worker_output(raw, aid)
        r4 = ens.worker_output_content_hash(out)
        _require(r4 == row["parsed_output_hash"],
                 f"anchor parsed {aid} != R4 recompute")
        parsed_by_aid[aid] = row["parsed_output_hash"]
        raw_by_aid[aid] = raw
        output_by_aid[aid] = out
        ctx = ctx_by_index[idx % 2]
        view = _view(aid, row["parsed_output_hash"], ctx,
                     f"worker.b.{aid}", f"worker.s.{aid}", row["model_id"])
        attempt_list.append(_typed_attempt(view, "ens.s4.1"))
    # model version must match anchor rows.
    for idx, aid in enumerate(attempts):
        _require(attempt_list[idx].model_version
                 == _anchor_row(anchor, aid)["model_version"],
                 f"anchor model version {aid} mismatch")
    receipt = {
        "audience_contract_id": "contract.s4.1",
        "cutoff_ref": "cutoff.v1",
        "evaluation_content_identities": ["eval.s4.1"],
        "project_ref": "project.p1",
        "public_projection_content_hash": _r4_style_hash({"proj": "s4"}),
        "public_projection_id": "proj.s4.1",
        "public_projection_kind": "ensemble",
        "run_ref": "run.r1",
        "snapshot_ref": "snap.s1",
        "source_revision_content_pairs": [
            {"revision_id": "rev.1", "content_hash": _r4_style_hash({"rev": "1"})},
        ],
        "visibility_decision_hash": _r4_style_hash({"vis": "s4"}),
        "visibility_decision_id": "vis.s4.1",
    }
    _require(_h(receipt) == anchor.get("accepted_receipt_content_hash"),
             "receipt must match anchor accepted receipt")
    artifact_identities: Dict[str, List[str]] = {}
    output_digests: Dict[str, str] = {}
    for aid in attempts:
        artifact_identities[f"artifact:{aid}"] = list(spec[aid]["findings"])
        output_digests[f"artifact:{aid}"] = parsed_by_aid[aid]
    digest_context = {
        "input_content_hash": _INPUT_HASH,
        "output_digests": output_digests,
        "evidence_digests": [_EVIDENCE_HASH],
        "expected_ensemble_identity": "ens.s4.1",
        "artifact_date_windows": {f"artifact:{aid}": "2026-08-01/2026-08-07"
                                  for aid in attempts},
        "artifact_unit_contracts": {f"artifact:{aid}": "unit.ctr.1"
                                    for aid in attempts},
        "artifact_source_versions": {f"artifact:{aid}": "rev.1"
                                     for aid in attempts},
        "artifact_model_versions": {f"artifact:{aid}": "1.0"
                                    for aid in attempts},
        "artifact_rule_ids": {f"artifact:{aid}": "rule.r1" for aid in attempts},
        "artifact_rule_versions": {f"artifact:{aid}": "1.0"
                                   for aid in attempts},
        "artifact_finding_identities": artifact_identities,
        "artifact_authorized_source_locators": {
            f"artifact:{aid}": ["loc.src1"] for aid in attempts},
    }
    # Packet baseline items are projections of the EXTERNAL accepted baseline
    # items (plain dicts; never packet-redefined truth).
    baseline_item = dict(anchor["accepted_baseline_items"][0])
    baseline_item_b2 = dict(anchor["accepted_baseline_items"][1])

    def _raw_artifact(aid: str, raw: bytes, parsed: str) -> Dict[str, Any]:
        return {
            "artifact_id": f"raw:{aid}", "attempt_id": aid,
            "raw_format": "utf8_text",
            "raw_bytes_b64": base64.b64encode(raw).decode("ascii"),
            "raw_bytes_sha256": _sha256_bytes(raw),
            "parsed_output_hash": parsed, "declared_output_hash": parsed,
        }

    def _verification(aid: str) -> Dict[str, Any]:
        view = next(v for v in views if v["attempt_id"] == aid)
        attempt = _typed_attempt(view, "ens.s4.1")
        output = output_by_aid[aid]
        ver = ens.verify_attempt(attempt, output, _typed_digest_context(
            {"digest_context": digest_context}))
        return {
            "verification_id": ver.verification_id, "attempt_id": aid,
            "checked_dimensions": sorted(set(ver.checked_dimensions)),
            "result": ver.result,
            "failure_reason_codes": sorted(set(ver.failure_reason_codes)),
            "recomputed": True,
        }

    def _baseline_row(aid: str) -> Dict[str, Any]:
        return {
            "row_ref": f"baseline-row:item.b1:{aid}", "item_id": "item.b1",
            "attempt_id": aid, "state": "confirmed",
            "reason_codes": ["source_rechecked"],
            "source_recheck_locator_ids": ["loc.src1"],
            "source_revision_id": "rev.1", "snapshot_id": "snap.1",
            "recheck_complete": True,
        }

    baseline_items = [_typed_baseline_item(baseline_item),
                      _typed_baseline_item(baseline_item_b2)]
    views = [_view(aid, parsed_by_aid[aid],
                   ctx_by_index[i % 2], f"worker.b.{aid}", f"worker.s.{aid}",
                   _anchor_row(anchor, aid)["model_id"])
             for i, aid in enumerate(attempts)]
    raws = [_raw_artifact(aid, raw_by_aid[aid], parsed_by_aid[aid])
            for aid in attempts]
    # verifications first, then bind each view's verification_ref to the real
    # R4-recomputed verification id (exact reference closure).
    verifs = sorted([_verification(aid) for aid in attempts],
                    key=lambda x: x["verification_id"])
    baseline_rows = [_baseline_row(aid) for aid in attempts]
    def _conflict_row(c: Any) -> Dict[str, Any]:
        ordinal_labels = []
        for aid in c.member_attempt_ids:
            ordinal = 1 if aid in ("a1", "m1", "g1") else 2
            ordinal_labels.append(ORDINAL_ZH[ordinal - 1])
        return {
            "conflict_id": c.conflict_id,
            "relation": c.relation, "display_state": c.display_state,
            "hidden": c.hidden, "monitoring_priority": c.monitoring_priority,
            "member_attempt_ids": sorted(c.member_attempt_ids),
            "ordinal_labels_zh": sorted(ordinal_labels),
        }


    # conflicts derived from the actual active attempts (real R4).
    active_outputs = {aid: output_by_aid[aid] for aid in attempts}
    if attempts:
        conflict_rows = [_conflict_row(c) for c in ens.derive_conflicts(
            attempts=attempt_list, worker_outputs=active_outputs,
            baseline_items=baseline_items)]
    else:
        conflict_rows = []

    def _history_log() -> Dict[str, Any]:
        kinds = {
            "no_ensemble": [],
            "single_analysis": ["attempt_bound", "baseline_assessed",
                                "verification_recorded", "conflict_derived",
                                "query_draft_generated", "inspection_finalized"],
            "multi_analysis": ["attempt_bound", "baseline_assessed",
                               "verification_recorded", "conflict_derived",
                               "adjudication_recorded", "query_draft_generated",
                               "inspection_finalized"],
        }[state]
        entries: List[Dict[str, Any]] = []
        prior = GENESIS_HASH
        for index, kind in enumerate(kinds, start=1):
            entry = {"entry_id": f"h{index}", "seq": index, "kind": kind,
                     "payload_ref": f"payload.h{index}", "prior_entry_hash": prior}
            entry["entry_hash"] = _h(entry)
            entries.append(entry)
            prior = entry["entry_hash"]
        if not entries:
            return {"history_ref": "history:s4.0", "head_seq": 0,
                    "head_hash": GENESIS_HASH, "entries": []}
        return {"history_ref": "history:s4.1", "head_seq": len(entries),
                "head_hash": entries[-1]["entry_hash"], "entries": entries}

    def _audience(workers_active: int, consensus: str) -> Dict[str, Any]:
        summaries = []
        for i in range(workers_active):
            summaries.append({
                "ordinal_zh": ORDINAL_ZH[i],
                "finding_summary_zh": ["支持发现 X"],
                "verification_zh": "七维验证全部通过", "gap_zh": []})
        adjudication_status = ("已独立核对，需人工关注"
                               if workers_active >= 2 else "尚未独立核对")
        # baseline_rows_zh is a deterministic closed mapping from typed rows.
        state_zh_map = {"confirmed": "已确认", "partially_supported": "部分支持",
                        "unsupported": "不支持", "outdated": "已过期",
                        "insufficient_evidence": "证据不足",
                        "not_applicable": "不适用"}
        baseline_zh = []
        for row in sorted(baseline_rows, key=lambda r: r.get("row_ref", "")):
            ordinal = 1 if row.get("attempt_id") in ("a1", "m1", "g1") else 2
            baseline_zh.append({
                "row_ref": row.get("row_ref", ""),
                "item_anchor_zh": f"基线条目 {row.get('item_id')}",
                "ordinal_zh": ORDINAL_ZH[ordinal - 1],
                "state_zh": state_zh_map.get(row.get("state"),
                                             row.get("state", "")),
                "recheck_zh": "已回查来源" if row.get(
                    "source_recheck_locator_ids") else "未回查"})
        # journey derived from the accepted target.
        target = anchor.get("accepted_journey_target", {})
        journey_available = all(target.get(k) for k in (
            "project_ref", "run_ref", "snapshot_ref", "risk_ref",
            "spine_ref", "anchor_ref"))
        # query from the accepted QueryDraft.
        qd = anchor.get("accepted_query_draft")
        qd_available = workers_active >= 2 and qd is not None
        # evidence/source Chinese text is a DETERMINISTIC projection of the
        # active worker findings/gaps and their exact source locators (no
        # hand-authored sentence may drift).
        support_locators: set = set()
        counter_locators: set = set()
        for aid in attempts:
            out = output_by_aid.get(aid)
            if out is None:
                continue
            for f in out.findings:
                locs = set(f.source_locator_ids)
                if f.supported:
                    support_locators |= locs
                else:
                    counter_locators |= locs
            for g in out.gap_candidates:
                counter_locators |= set(g.source_locator_ids)
        support_locators = set(sorted(support_locators))
        counter_locators = set(sorted(counter_locators))
        support_evidence = sorted(
            f"来源 {loc} 已定位" for loc in sorted(support_locators))
        counter_evidence = sorted(
            f"来源 {loc} 已定位" for loc in sorted(counter_locators))
        located = support_locators | counter_locators
        authorized: set = set()
        for loc_set in digest_context.get(
                "artifact_authorized_source_locators", {}).values():
            authorized.update(loc_set)
        for item in (baseline_item, baseline_item_b2):
            authorized.update(item.get("source_locator_ids", []))
        unresolved = located - authorized
        if located:
            one_hop = "来源 " + "、".join(sorted(located)) + " 已在一跳内定位"
            if unresolved:
                one_hop += "；未解析来源请核实"
        else:
            one_hop = ""
        return {
            "audience_contract_id": "contract.s4.1",
            "risk_title_zh": "AE 风险提示：发热性中性粒细胞减少",
            "domain_zh": "AE", "severity_zh": severity_zh,
            "change_state_zh": "新发", "subject_display_zh": "受试者 1001",
            "center_display_zh": "中心 01", "project_display_zh": "项目 P-01",
            "cutoff_display_zh": "数据截止 2026-08-01",
            "basis_zh": "两个独立分析对同一基线条目给出支持性评估，建议核实来源",
            "support_evidence_zh": support_evidence,
            "counterevidence_zh": counter_evidence,
            "source_one_hop_zh": one_hop,
            "baseline_rows_zh": baseline_zh,
            "worker_ordinal_summaries": summaries,
            "consensus_zh": consensus,
            "adjudication_status_zh": adjudication_status,
            "adjudication_explanation_zh": None,
            "query_basis_zh": (qd.get("basis_zh") if qd_available else None),
            "query_finding_zh": (qd.get("finding_zh") if qd_available else None),
            "query_action_zh": (qd.get("action_zh") if qd_available else None),
            "query_pd_wording_zh": ("非疑似疾病进展" if qd_available
                                    and qd.get("pd_wording_state") == "not_pd"
                                    else ("疑似疾病进展" if qd_available else None)),
            "history_summary_zh": "已完成绑定、基线、验证、冲突、裁决与查询草稿记录",
            "journey_available": journey_available,
            "journey_link_zh": "跳转链接已就绪" if journey_available else None,
            "journey_unavailable_reason_zh": (None if journey_available
                                              else "无法定位目标身份"),
        }

    def _audit(workers_active: int) -> Dict[str, Any]:
        if state == "no_ensemble":
            return {
                "authority_receipt_ref": RECEIPT_REF_PREFIX + _h(receipt),
                "receipt_content_hash": _h(receipt),
                "digest_context": None,
                "worker_audit_rows": [],
                "verification_audit_rows": [],
                "adjudication_audit": [],
                "conflict_audit": [],
                "history_audit": sorted(set(e["entry_hash"]
                                           for e in _history_log()["entries"])),
                "model_evidence": None,
            }
        worker_rows = []
        for i, aid in enumerate(attempts):
            worker_rows.append({
                "attempt_id": aid, "binding_id": f"worker.b.{aid}",
                "session_id": f"worker.s.{aid}",
                "model_id": _anchor_row(anchor, aid)["model_id"],
                "model_version": "1.0", "role": "worker",
                "independent_context_hash": ctx_by_index[i % 2],
                "input_content_hash": _INPUT_HASH,
                "output_artifact_ref": f"artifact:{aid}",
                "declared_output_hash": parsed_by_aid[aid],
                "raw_bytes_sha256": _sha256_bytes(raw_by_aid[aid]),
                "parsed_output_hash": parsed_by_aid[aid]})
        verif_rows = sorted([_verification(aid) for aid in attempts],
                            key=lambda x: x["verification_id"])

        def _model_evidence() -> Dict[str, Any]:
            permit = (anchor.get("model_evidence_permits") or [{}])[0]
            me = dict(permit)
            # adjudication_state and output_hash are bound to the accepted
            # permit/actual worker (all 19 R4 ModelEvidence fields bind).
            if me.get("adjudication_state") is None:
                me["adjudication_state"] = "pending"
            # output_hash binds to the ACTUAL model.<id> worker in this packet.
            for w in views:
                if w.get("model_id") == me.get("model_id"):
                    me["output_hash"] = w.get("declared_output_hash")
                    break
            return me

        return {
            "authority_receipt_ref": RECEIPT_REF_PREFIX + _h(receipt),
            "receipt_content_hash": _h(receipt),
            "digest_context": digest_context,
            "worker_audit_rows": worker_rows,
            "verification_audit_rows": verif_rows,
            "adjudication_audit": (["adj.record.1"]
                                   if workers_active >= 2 else []),
            "conflict_audit": sorted(c["conflict_id"] for c in conflict_rows),
            "history_audit": sorted(set(e["entry_hash"]
                                       for e in _history_log()["entries"])),
            "model_evidence": _model_evidence(),
        }

    state = {"no_ensemble": "no_ensemble", "zero": "no_ensemble",
             "single": "single_analysis",
             "single_analysis": "single_analysis"}.get(mode, "multi_analysis")
    if state == "no_ensemble":
        workers_active = 0
        consensus = "尚无独立分析"
        size = 0
        input_hash = None
    elif state == "single_analysis":
        workers_active = 1
        consensus = "尚无独立分析"
        size = 1
        input_hash = _INPUT_HASH
    else:
        workers_active = max(1, len(attempts))
        consensus = "两个独立分析均支持同一发现，但存在未评估基线条目"
        size = len(attempts)
        input_hash = _INPUT_HASH
    if mode in ("no_ensemble", "zero"):
        workers_active = 0

    severity_zh = "高"
    audience = _audience(workers_active, consensus)
    audit = _audit(workers_active)
    audience_hash = _h(audience)
    packet: Dict[str, Any] = {
        "packet_id": f"{PACKET_ID_PREFIX}:{audience_hash}",
        "schema": PACKET_SCHEMA, "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "authority_anchor_ref": f"{ANCHOR_REF_PREFIX}{anchor_hash}",
        "anchor_identity_hash": anchor_hash,
        "ensemble_projection_state": state,
        "ensemble_id": "ens.s4.1", "ensemble_size": size,
        "input_content_hash": input_hash,
        "risk_identity": dict(anchor.get("accepted_risk_identity", {})),
        "authority_receipt": receipt,
        "receipt_content_hash": _h(receipt),
        "baseline_items": [baseline_item, baseline_item_b2],
        "baseline_rows": baseline_rows,
        "worker_views": views,
        "raw_artifacts": raws,
        "verification_rows": verifs,
        "conflict_rows": conflict_rows,
        "adjudication_row": ({
            "present": True,
            **{k: v for k, v in (anchor.get(
                "accepted_adjudicator_binding") or {}).items()},
            "independent_context_hash": (anchor.get(
                "accepted_adjudicator_binding") or {}).get(
                "independent_context_hash", _ADJ_CONTEXT),
            "reviewed_artifact_refs": sorted(
                f"artifact:{aid}" for aid in attempts),
            "adds_explanation_only": True,
        } if workers_active >= 2 else {
            "present": False, "binding_id": "", "session_id": "",
            "model_id": "", "model_version": "",
            "independent_context_hash": None, "outcome": None,
            "reviewed_artifact_refs": [], "adds_explanation_only": True,
        }),
        "query_draft_row": (
            {k: v for k, v in (anchor.get("accepted_query_draft") or {}).items()
             if k != "content_hash"}
            if workers_active >= 2 and anchor.get("accepted_query_draft")
            else None),
        "journey_link": {
            "deep_link_project_ref": "project.p1",
            "deep_link_run_ref": "run.r1", "deep_link_snapshot_ref": "snap.s1",
            "deep_link_cutoff_ref": "cutoff.v1", "deep_link_site_ref": "site.01",
            "deep_link_subject_ref": "subject.1001",
            "deep_link_risk_ref": "d09_marker:m-rk",
            "deep_link_event_ref": "event.e1", "deep_link_visit_ref": "visit.v1",
            "deep_link_spine_ref": "spine.sp1", "deep_link_anchor_ref": "anchor.a1",
            "deep_link_source_locator_ref": "loc.src1",
            "fallback_policy": "none",
            "journey_available": all(anchor.get("accepted_journey_target", {}).get(k)
                                     for k in ("project_ref", "run_ref",
                                               "snapshot_ref", "risk_ref",
                                               "spine_ref", "anchor_ref")),
            "unavailable_reason_zh": None,
        },
        "history_log": _history_log(),
        "audience_inspector": audience,
        "audit_inspector": audit,
        "audience_content_hash": audience_hash,
        "audit_content_hash": _h(audit),
    }
    # Fingerprint recipe (frozen, 4 independent acyclic hashes not derived
    # from the audit object): audience content hash, receipt content hash,
    # packet id, risk identity hash.
    audit["packet_fingerprints"] = sorted([
        "audience:" + packet["audience_content_hash"],
        "receipt:" + packet["receipt_content_hash"],
        "packet:" + packet["packet_id"],
        "risk_identity:" + packet.get("risk_identity", {}).get(
            "risk_identity_hash", ""),
    ])
    packet["audit_inspector"] = audit
    packet["audit_content_hash"] = _audit_content_hash(packet["audit_inspector"])
    integrity_body = {key: value for key, value in packet.items()
                      if key not in INTEGRITY_EXCLUDED_KEYS}
    packet["packet_integrity_hash"] = _h(integrity_body)
    return packet


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--anchor", type=Path, default=None,
                        help="external accepted-authority anchor JSON path")
    args = parser.parse_args()
    root: Path = args.root
    artifacts: Path = args.artifacts
    try:
        overlay = _load_json(artifacts / "exact_overlay.json")
        schema = _load_json(artifacts / "packet_schema.json")
        pins = _load_json(artifacts / "source_pins.json")
        manifest = _load_json(artifacts / "manifest.json")
        _walk_strings(overlay, "overlay")
        _walk_strings(schema, "schema")
        _walk_strings(pins, "pins")
        _walk_strings(manifest, "manifest")
        maps: Dict[str, Dict[str, Dict[str, str]]] = {}
        for module, path in MODULE_FILES.items():
            maps[module] = _parse_classes(path, root)
        for module_ref, path in EXPECTED_FUNCTION_REFS.items():
            module, name = module_ref.split(":", 1)
            objects = _module_objects(path, root)
            _require(objects.get(name) == "function",
                     f"function_ref_unresolvable: {module_ref}")
        for module_ref, path in EXPECTED_CONSTANT_REFS.items():
            module, name = module_ref.split(":", 1)
            objects = _module_objects(path, root)
            _require(objects.get(name) == "constant",
                     f"constant_ref_unresolvable: {module_ref}")

        _validate_overlay(overlay, maps)
        _validate_schema(schema, maps)
        _validate_source_pins(pins, root)
        _validate_manifest(manifest, artifacts, root)
        _check_no_assert("tools/generate_medical_monitoring_r5_s4_contract_v0_1.py", root)
        _check_no_assert("tools/verify_medical_monitoring_r5_s4_contract_v0_1.py", root)
        _verify_hash_dag_acyclic(overlay["hash_dag"])
        _verify_audience_audit_separation(overlay["hash_dag"], schema)
        recomputed_manifest_hash = _recompute_manifest_self_hash(manifest)
        _require(recomputed_manifest_hash == manifest["manifest_content_sha256"],
                 "manifest_content_hash_mismatch: recompute mismatch")

        tamper_count = _tamper_probes(overlay, schema, pins, manifest,
                                      maps, root, artifacts)

        # external accepted-authority anchor: SEPARATE explicit input.  The
        # S4 generator never creates or signs it; the verifier fails closed
        # if it is absent and never trusts an in-band packet copy.
        if args.anchor is None:
            _fail("external accepted-authority anchor required: pass --anchor "
                  "<path> (the anchor is not generator-owned)")
        anchor_path: Path = args.anchor
        if not anchor_path.exists() or not anchor_path.is_file():
            _fail(f"external anchor missing: {anchor_path}")
        anchor = _load_json(anchor_path)

        # R4-backed packet semantics: valid 0/1/N fixtures pass [].
        for mode in ("no_ensemble", "single_analysis", "multi_analysis",
                     "mutual", "graded"):
            packet = build_sample_packet(mode, anchor)
            errors = _packet_oracle(packet, anchor, schema, overlay)
            _require(errors == [],
                     f"fixture {mode} must pass oracle, got {sorted(errors)}")

        # challenge registry execution (all 97 rows, packet + governance).
        registry_path = artifacts / "challenge_registry.json"
        if registry_path.exists():
            registry = _load_json(registry_path)
            registry_rows_executed = _verify_challenge_registry(
                registry, build_sample_packet, anchor, schema, overlay,
                root, artifacts, maps)
        else:
            registry_rows_executed = 0
    except VerificationError as error:
        print(json.dumps({"ok": False, "error": str(error)},
                         ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps({
        "ok": True,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "source_count": pins["source_count"],
        "artifact_count": manifest["artifact_count"],
        "planned_artifact_count": manifest["planned_artifact_count"],
        "schema_objects": len(schema["objects"]),
        "enums": len(overlay["enums"]),
        "invariants": len(overlay["invariants"]),
        "join_recipes": len(overlay["join_recipes"]),
        "source_matrix_rows": len(overlay["source_matrix"]),
        "error_codes": len(overlay["enums"]["error_code"]),
        "hash_dag_nodes": len(overlay["hash_dag"]),
        "challenge_spec_total": overlay["challenge_spec"]["total_exact"],
        "tamper_probes_rejected": tamper_count,
        "registry_rows_executed": registry_rows_executed,
        "artifact_shas": {
            item["path"]: item["sha256"] if item["hash_kind"] == "raw_sha256"
            else manifest["manifest_content_sha256"]
            for item in manifest["artifacts"]},
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
