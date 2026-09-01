#!/usr/bin/env python3
"""Deterministic source-of-truth generator for the R5-S4 Risk Inspector /
multi-model ensemble-evidence exact contract (synthetic/offline,
renderer-neutral).  Same inputs -> identical bytes; ``--check`` compares
without writing.

Owned artifacts (under artifacts/medical_monitoring_r5_s4_contract_v0_1/):
  * packet_schema.json   -- exact typed objects + per-field descriptors + hash DAG
  * exact_overlay.json   -- closed enums, source matrix (field mappings),
                            join recipes, invariants, error-code catalog,
                            severity mapping, forbidden tokens, challenge spec,
                            hash DAG grammar, audience/audit done gates
  * source_pins.json     -- SHA-256 pins of every authority file consumed
  * manifest.json        -- artifact manifest + pinned sources + self hash

The generator NEVER writes the acceptance digest; it only writes these four
JSON artifacts.  It does not implement S4 runtime: it does not call
run_ensemble / verify_attempt / derive_conflicts / _adjudicate / D10 Query
builder.  Those R4 deterministic functions are the verifier's (worker_02)
non-LLM oracle per the join recipes below.

Scope boundary:
  * No production writes, no 8911, no browser, no real project/model.
  * R4, accepted R5 S1-S3, frontend, services, medical-writing and the root
    __init__.py are READ-ONLY and are only pinned (never modified).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent

ARTIFACT_DIR = ROOT / "artifacts" / "medical_monitoring_r5_s4_contract_v0_1"
SCHEMA_PATH = ARTIFACT_DIR / "packet_schema.json"
OVERLAY_PATH = ARTIFACT_DIR / "exact_overlay.json"
SOURCE_PINS_PATH = ARTIFACT_DIR / "source_pins.json"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"

SCHEMA_BASE = "medical-monitoring-r5-s4-packet-schema-v0.1"
OVERLAY_SCHEMA = "medical-monitoring-r5-s4-exact-overlay-v0.1"
SOURCE_PINS_SCHEMA = "medical-monitoring-r5-s4-source-pins-v0.1"
MANIFEST_SCHEMA = "medical-monitoring-r5-s4-artifact-manifest-v0.1"

STATUS = "R5_S4_CONTRACT_READY_FOR_REVIEW"
AUTHORITY_MODE = "synthetic_offline_test_only"

HASH_ALGORITHM = "sha256"
HASH_CANONICALIZATION = "utf8_nfc_sorted_keys_compact_json_newline"
PACKET_ID_PREFIX = "r5-s4-contract"
RECEIPT_REF_PREFIX = "receipt:"
GENESIS_HASH = "genesis"
TEST_PREFIX = "poc/medical_monitoring_ai_native_r5/tests/test_s4_contract_artifacts.py::test_challenge_case["

# ---------------------------------------------------------------------------
# Closed vocabularies (mirroring the human contract; pinned by source_pins)
# ---------------------------------------------------------------------------

ENSEMBLE_PROJECTION_STATES: Tuple[str, ...] = (
    "no_ensemble", "single_analysis", "multi_analysis")

# import R4
BASELINE_STATES: Tuple[str, ...] = (
    "confirmed", "partially_supported", "unsupported", "outdated",
    "insufficient_evidence", "not_applicable")
# Real R4 assessment-reason enum (closed; free prose is never a reason).
ASSESSMENT_REASON_CODES: Tuple[str, ...] = (
    "source_rechecked", "content_match", "partial_content_match",
    "content_absent_from_source", "source_revision_superseded",
    "evidence_insufficient", "locator_unresolvable",
    "outside_assessment_scope")
RECHECK_REQUIRED_STATES: Tuple[str, ...] = ("confirmed", "unsupported")
VERIFICATION_DIMENSIONS: Tuple[str, ...] = (
    "identity", "version", "date", "unit", "source", "rule",
    "artifact_integrity")
VERIFICATION_RESULTS: Tuple[str, ...] = ("passed", "failed", "not_evaluable")
VERIFICATION_FAILURE_CODES: Tuple[str, ...] = (
    "identity_mismatch", "version_mismatch", "date_out_of_window",
    "unit_mismatch", "source_unresolvable", "rule_version_mismatch",
    "artifact_hash_mismatch", "input_content_mismatch")
CONFLICT_RELATIONS: Tuple[str, ...] = (
    "shared_finding", "single_model_new", "graded_conflict",
    "mutual_negation", "baseline_miss")
CONFLICT_DISPLAY_STATES: Tuple[str, ...] = (
    "needs_attention", "visible_conflict", "visible_baseline_miss")
NON_HIDEABLE_RELATIONS: Tuple[str, ...] = ("mutual_negation", "baseline_miss")
ATTEMPT_ROLES: Tuple[str, ...] = ("worker", "adjudicator")
MONITORING_PRIORITIES: Tuple[str, ...] = ("high", "medium", "low", "unknown")
HISTORY_ENTRY_KINDS: Tuple[str, ...] = (
    "attempt_bound", "baseline_assessed", "verification_recorded",
    "conflict_derived", "adjudication_recorded", "query_draft_generated",
    "inspection_finalized")

# import R2
ADJUDICATION_OUTCOMES: Tuple[str, ...] = (
    "merged_supported", "distinct_supported", "rejected_by_evidence",
    "version_mismatch", "needs_user_attention")

# import R5 exact contract
SEVERITIES: Tuple[str, ...] = ("critical", "high", "medium", "low")
SEVERITIES_ZH: Tuple[str, ...] = ("紧急", "高", "中", "低")
DOMAINS: Tuple[str, ...] = (
    "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
    "symptom_efficacy", "protocol_compliance")
CHANGE_KINDS: Tuple[str, ...] = (
    "initial_current", "new", "upgraded", "continued", "downgraded",
    "resolved", "reopened", "superseded", "not_evaluable", "not_comparable")
CHANGE_CAUSES: Tuple[str, ...] = (
    "data", "knowledge", "rule", "mapping", "model", "method", "coverage",
    "denominator", "population", "visibility", "mode", "user_decision")
PROJECTION_KINDS: Tuple[str, ...] = (
    "d09_audience", "d10_project", "ensemble", "subject_temporal",
    "aemh_history")

# import D10
PD_WORDING_STATES: Tuple[str, ...] = ("not_pd", "verify_whether_pd")
MODEL_EVIDENCE_ROLES: Tuple[str, ...] = (
    "candidate_explanation", "counterevidence_suggestion",
)

# import S2
FALLBACK_POLICIES: Tuple[str, ...] = ("none",)
S2_ADJUDICATION_STATES: Tuple[str, ...] = ("accepted", "divergent", "pending")

# S4 frozen single-value vocabularies
RAW_OUTPUT_FORMATS: Tuple[str, ...] = ("utf8_text",)
SEVERITY_SOURCES: Tuple[str, ...] = (
    "r4_priority_mapped", "r4_explicit_critical", "fail_closed")

# Severity mapping: R4 monitoring_priority -> R5 severity (frozen table).
# critical is NEVER synthesized from priority; only an explicit R4 critical
# projection may set it.  unknown -> fail_closed.
SEVERITY_MAPPING: Dict[str, str] = {
    "high": "high",
    "medium": "medium",
    "low": "low",
    "unknown": "fail_closed",
}

# Closed error-code catalog (verifier decision codes; not free prose).
ERROR_CODES: Tuple[str, ...] = (
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
)

# Forbidden audience tokens (closed list; enforced by the verifier, not by
# presence in the schema).
FORBIDDEN_AUDIENCE_TOKENS: Tuple[str, ...] = (
    "provider", "model_id", "model_version", "attempt", "hash", "backend",
    "session", "consensus", "worker", "adjudicator", "binding",
    "正式事实", "候选信号", "只读", "待办", "未读", "金标准",
    "已证实", "权威结论", "model_majority", "卡列表", "已发送", "已关闭",
)

# Chinese severity / domain / ordinal lexicons (audience plane only).
SEVERITY_ZH_BY_SEVERITY: Dict[str, str] = {
    "critical": "紧急", "high": "高", "medium": "中", "low": "低",
}
DOMAIN_ZH: Dict[str, str] = {
    "ae": "AE", "mh": "MH", "cm": "合并用药", "ip": "试验药",
    "lab_exam": "检验/检查", "hospital_procedure": "住院/操作",
    "symptom_efficacy": "症状/疗效", "protocol_compliance": "方案符合",
}
ORDINAL_ZH = ("分析一", "分析二", "分析三", "分析四", "分析五", "分析六",
              "分析七", "分析八", "分析九", "分析十")

# Challenge spec quotas (exactly 97 registered by worker_03).
CHALLENGE_SPEC: Dict[str, int] = {
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

# ---------------------------------------------------------------------------
# Canonical serialization & hashing (R5 family convention)
# ---------------------------------------------------------------------------


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
           nullable: bool = False, constraints: Tuple[str, ...] = (),
           import_extensions: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    descriptor: Dict[str, Any] = {
        "type": type_name, "cardinality": cardinality, "nullable": nullable,
    }
    if constraints:
        descriptor["constraints"] = list(constraints)
    if import_extensions:
        descriptor["import_extensions"] = import_extensions
    return descriptor


def _invariant(invariant_id: str, error_code: str, predicate: str) -> Dict[str, str]:
    return {"invariant_id": invariant_id, "error_code": error_code,
            "predicate": predicate}


def _mapping(leaf: str, path: str, provenance: str, source_kind: str,
             join_recipe: Optional[str] = None,
             deferred: Optional[str] = None) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "leaf": leaf, "path": path, "provenance": provenance,
        "source_kind": source_kind,
    }
    if join_recipe is not None:
        row["join_recipe"] = join_recipe
    if deferred is not None:
        row["deferred_contract"] = deferred
    return row


# ---------------------------------------------------------------------------
# packet_schema.json
# ---------------------------------------------------------------------------

HASH_DAG: Dict[str, Dict[str, Any]] = {
    "audience_content_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "domain": "public_audience_authority",
        "covered_subobject": "audience_inspector",
        "forbidden_leaves": [
            "binding_id", "session_id", "model_id", "model_version",
            "independent_context_hash", "raw_bytes_b64", "raw_bytes_sha256",
            "declared_output_hash", "verification_audit_rows",
            "history_audit", "packet_fingerprints", "model_evidence",
            "digest_context", "output_digests", "artifact_source_versions",
        ],
        "may_cover_hidden": False,
        "depends_on": [],
    },
    "audit_content_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "domain": "private_audit_authority",
        "covered_subobject": "audit_inspector",
        "excluded_leaves": ["packet_fingerprints"],
        "may_cover_hidden": True,
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
    "packet_id": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "domain": "public_audience_authority",
        "recipe": "<prefix>:<audience_content_hash>",
        "ref_prefix": PACKET_ID_PREFIX,
        "depends_on": ["audience_content_hash"],
    },
    "packet_fingerprints": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "domain": "private_audit_authority",
        "covered_subobject": "audit_inspector.packet_fingerprints",
        "recipe": [
            "audience:<audience_content_hash>",
            "receipt:<receipt_content_hash>",
            "packet:<packet_id>",
            "risk_identity:<risk_identity_hash>",
        ],
        "sorted_unique": True,
        "depends_on": ["audience_content_hash", "receipt_content_hash",
                       "packet_id", "risk_identity_hash"],
        "excluded_from": ["audit_content_hash"],
    },
    "packet_integrity_hash": {
        "algorithm": HASH_ALGORITHM,
        "canonicalization": HASH_CANONICALIZATION,
        "domain": "private_packet_integrity",
        "excluded_root_keys": ["packet_id", "packet_integrity_hash",
                               "audience_content_hash", "audit_content_hash",
                               "receipt_content_hash",
                               "schema", "status", "authority_mode"],
        "may_cover_hidden": True,
        "dependency_edges": [
            {"source": "audience_content_hash", "kind": "excluded"},
            {"source": "audit_content_hash", "kind": "excluded"},
            {"source": "receipt_content_hash", "kind": "excluded"},
        ],
        "depends_on": ["audience_content_hash", "audit_content_hash",
                       "receipt_content_hash", "packet_id",
                       "packet_fingerprints", "risk_identity_hash"],
    },
}


def _hash_dag() -> Dict[str, Dict[str, Any]]:
    return {k: dict(v) for k, v in HASH_DAG.items()}


def _schema_object_risk_identity() -> Dict[str, Any]:
    return {
        "risk_ref": _field("str", constraints=["marker_grammar:d09_marker:|d10_marker:"]),
        "risk_identity_hash": _field("sha256", constraints=["canonical_sha256_of:r4_public_risk_identity"]),
        "domain": _field("enum:domain"),
        "domain_zh": _field("str", constraints=["closed_zh:domain"]),
        "monitoring_priority": _field("enum:monitoring_priority", constraints=["r4_priority_authority"]),
        "severity": _field("enum:severity", constraints=["severity_mapping_from_monitoring_priority"]),
        "severity_zh": _field("str", constraints=["closed_zh:severity"]),
        "change_kind": _field("enum:change_kind"),
        "change_cause": _field("enum:change_cause"),
        "project_ref": _field("str"),
        "run_ref": _field("str"),
        "snapshot_ref": _field("str"),
        "cutoff_ref": _field("str", nullable=True),
        "site_ref": _field("str", nullable=True),
        "subject_ref": _field("str", nullable=True),
        "spine_ref": _field("str"),
    }


def _schema_object_worker_view() -> Dict[str, Any]:
    return {
        "attempt_id": _field("str"),
        "ordinal": _field("int", constraints=["min:1", "max:10"]),
        "ordinal_zh": _field("str", constraints=["closed_zh:ordinal"]),
        "binding_id": _field("str"),
        "session_id": _field("str"),
        "model_id": _field("str"),
        "model_version": _field("str"),
        "role": _field("enum:attempt_role", constraints=["equals:worker"]),
        "independent_context_hash": _field("sha256"),
        "input_content_hash": _field("sha256"),
        "output_artifact_ref": _field("str"),
        "declared_output_hash": _field("sha256"),
        "claimed_date_window": _field("str"),
        "claimed_unit_contract": _field("str"),
        "claimed_source_revision": _field("str"),
        "claimed_rule_id": _field("str"),
        "claimed_rule_version": _field("str"),
        "assessment_row_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "finding_ids": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "gap_ids": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "raw_artifact_ref": _field("str", constraints=["prefix:raw:"]),
        "verification_ref": _field("str", constraints=["prefix:verification:"]),
    }


def _schema_object_raw_artifact() -> Dict[str, Any]:
    return {
        "artifact_id": _field("str"),
        "attempt_id": _field("str"),
        "raw_format": _field("enum:raw_output_format"),
        "raw_bytes_b64": _field("str", constraints=["base64"]),
        "raw_bytes_sha256": _field("sha256", constraints=["canonical_sha256_of:raw_bytes"]),
        "parsed_output_hash": _field("sha256", constraints=["recompute:mm_r4.ensemble.worker_output_content_hash"]),
        "declared_output_hash": _field("sha256", constraints=["equals:parsed_output_hash"]),
    }


def _schema_object_baseline_row() -> Dict[str, Any]:
    return {
        "row_ref": _field("str", constraints=["grammar:baseline-row:<item_id>:<attempt_id>"]),
        "item_id": _field("str"),
        "attempt_id": _field("str"),
        "state": _field("enum:baseline_state"),
        "reason_codes": _field("str", cardinality="many", constraints=["sorted_unique", "closed_enum:assessment_reason_code", "min_items:1"]),
        "source_recheck_locator_ids": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "source_revision_id": _field("str"),
        "snapshot_id": _field("str"),
        "recheck_complete": _field("bool", constraints=["recheck_required_implies_locators"]),
    }


def _schema_object_conflict_row() -> Dict[str, Any]:
    return {
        "conflict_id": _field("str"),
        "relation": _field("enum:conflict_relation"),
        "display_state": _field("enum:conflict_display_state"),
        "hidden": _field("bool", constraints=["non_hideable_relations_forbidden_when_true"]),
        "monitoring_priority": _field("enum:monitoring_priority"),
        "member_attempt_ids": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:1"]),
        "ordinal_labels_zh": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:1"]),
    }


def _schema_object_verification_row() -> Dict[str, Any]:
    return {
        "verification_id": _field("str"),
        "attempt_id": _field("str"),
        "checked_dimensions": _field("str", cardinality="many", constraints=["exact_set:seven_dimensions", "min_items:7", "max_items:7"]),
        "result": _field("enum:verification_result"),
        "failure_reason_codes": _field("str", cardinality="many", constraints=["sorted_unique", "closed_enum:verification_failure_code", "min_items:0"]),
        "recomputed": _field("bool", constraints=["equals:true"]),
    }


def _schema_object_adjudication_row() -> Dict[str, Any]:
    return {
        "present": _field("bool"),
        "binding_id": _field("str", nullable=True, constraints=["required_when:present=true", "forbidden_when:present=false"]),
        "session_id": _field("str", nullable=True, constraints=["required_when:present=true", "forbidden_when:present=false"]),
        "model_id": _field("str", nullable=True, constraints=["required_when:present=true", "forbidden_when:present=false"]),
        "model_version": _field("str", nullable=True, constraints=["required_when:present=true", "forbidden_when:present=false"]),
        "independent_context_hash": _field("sha256", nullable=True, constraints=["required_when:present=true", "forbidden_when:present=false"]),
        "outcome": _field("enum:adjudication_outcome", nullable=True, constraints=["required_when:present=true", "forbidden_when:present=false"]),
        "reviewed_artifact_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0", "nonempty_when_present"]),
        "adds_explanation_only": _field("bool", constraints=["equals:true"]),
    }


def _schema_object_query_draft_row() -> Dict[str, Any]:
    return {
        "query_draft_id": _field("str"),
        "risk_ref": _field("str", constraints=["marker_grammar:d09_marker:|d10_marker:"]),
        "basis_zh": _field("str"),
        "finding_zh": _field("str"),
        "action_zh": _field("str"),
        "source_locator_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:1"]),
        "pd_wording_state": _field("enum:pd_wording_state"),
        "draft_only": _field("bool", constraints=["equals:true"]),
    }


def _schema_object_journey_link() -> Dict[str, Any]:
    return {
        "deep_link_project_ref": _field("str"),
        "deep_link_run_ref": _field("str"),
        "deep_link_snapshot_ref": _field("str"),
        "deep_link_cutoff_ref": _field("str", nullable=True),
        "deep_link_site_ref": _field("str", nullable=True),
        "deep_link_subject_ref": _field("str", nullable=True),
        "deep_link_risk_ref": _field("str"),
        "deep_link_event_ref": _field("str", nullable=True),
        "deep_link_visit_ref": _field("str", nullable=True),
        "deep_link_spine_ref": _field("str"),
        "deep_link_anchor_ref": _field("str"),
        "deep_link_source_locator_ref": _field("str", nullable=True),
        "fallback_policy": _field("enum:fallback_policy", constraints=["equals:none"]),
        "journey_available": _field("bool"),
        "unavailable_reason_zh": _field("str", nullable=True),
    }


def _schema_object_history_entry() -> Dict[str, Any]:
    return {
        "entry_id": _field("str"),
        "seq": _field("int", constraints=["min:1"]),
        "kind": _field("enum:history_entry_kind"),
        "payload_ref": _field("str"),
        "prior_entry_hash": _field("str", constraints=["first_entry_genesis"]),
        "entry_hash": _field("sha256", constraints=["chain_includes_prior_hash"]),
    }


def _schema_object_history_log() -> Dict[str, Any]:
    return {
        "history_ref": _field("str", constraints=["prefix:history:"]),
        "head_seq": _field("int", constraints=["equals:len(entries)"]),
        "head_hash": _field("str", nullable=True, constraints=["equals:last_entry.entry_hash_or_genesis"]),
        "entries": _field("R5S4HistoryEntry", cardinality="many", constraints=["sorted_unique_by:seq", "append_only_chain", "min_items:1"]),
    }


def _schema_object_audience_baseline_row() -> Dict[str, Any]:
    """One audience baseline row: user-facing Chinese display text PLUS a
    machine-only stable identity (row_ref = baseline-row:<item_id>:<attempt_id>)
    distinct from display text, so two assessments of the same baseline item
    stay distinct, deterministic and correctly ordered."""
    return {
        "row_ref": _field("str", constraints=["nonempty"]),
        "item_anchor_zh": _field("str", constraints=["nonempty"]),
        "ordinal_zh": _field("str", constraints=["closed_zh:ordinal"]),
        "state_zh": _field("str", constraints=["nonempty"]),
        "recheck_zh": _field("str", constraints=["nonempty"]),
    }


def _schema_object_audience_inspector() -> Dict[str, Any]:
    return {
        "audience_contract_id": _field("str"),
        "risk_title_zh": _field("str", constraints=["nonempty"]),
        "domain_zh": _field("str", constraints=["closed_zh:domain"]),
        "severity_zh": _field("str", constraints=["closed_zh:severity"]),
        "change_state_zh": _field("str"),
        "subject_display_zh": _field("str"),
        "center_display_zh": _field("str"),
        "project_display_zh": _field("str"),
        "cutoff_display_zh": _field("str"),
        "basis_zh": _field("str", constraints=["nonempty"]),
        "support_evidence_zh": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "counterevidence_zh": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "source_one_hop_zh": _field("str"),
        "baseline_rows_zh": _field("R5S4AudienceBaselineRow", cardinality="many", constraints=["sorted_unique_by:row_ref", "min_items:0"]),
        "worker_ordinal_summaries": _field("R5S4AudienceWorkerSummary", cardinality="many", constraints=["sorted_unique_by:ordinal_zh", "min_items:0"]),
        "consensus_zh": _field("str", constraints=["gated_consensus_phrase"]),
        "adjudication_status_zh": _field("str", constraints=["never_claims_independent_when_absent"]),
        "adjudication_explanation_zh": _field("str", nullable=True),
        "query_basis_zh": _field("str", nullable=True),
        "query_finding_zh": _field("str", nullable=True),
        "query_action_zh": _field("str", nullable=True),
        "query_pd_wording_zh": _field("str", nullable=True),
        "history_summary_zh": _field("str"),
        "journey_available": _field("bool"),
        "journey_link_zh": _field("str", nullable=True),
        "journey_unavailable_reason_zh": _field("str", nullable=True),
    }


def _schema_object_audience_worker_summary() -> Dict[str, Any]:
    return {
        "ordinal_zh": _field("str", constraints=["closed_zh:ordinal"]),
        "finding_summary_zh": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "verification_zh": _field("str"),
        "gap_zh": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
    }


def _schema_object_audit_inspector() -> Dict[str, Any]:
    return {
        "authority_receipt_ref": _field("str", constraints=["prefix:receipt:"]),
        "receipt_content_hash": _field("sha256", constraints=["canonical_sha256_of:authority_receipt"]),
        "digest_context": _field("R5S4DigestContextView", nullable=True, constraints=["required_when:state!=no_ensemble", "forbidden_when:state=no_ensemble"]),
        "worker_audit_rows": _field("R5S4AuditWorkerRow", cardinality="many", constraints=["sorted_unique_by:attempt_id", "min_items:0"]),
        "verification_audit_rows": _field("R5S4VerificationAuditRow", cardinality="many", constraints=["sorted_unique_by:verification_id", "min_items:0"]),
        "adjudication_audit": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "conflict_audit": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "history_audit": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "packet_fingerprints": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:4"]),
        "model_evidence": _field("R5S4ModelEvidenceRef", nullable=True, constraints=["packet_only_provenance", "forbidden_when:state=no_ensemble"]),
    }


def _schema_object_model_evidence_ref() -> Dict[str, Any]:
    """Provenance-only ModelEvidence projection (audit plane only; never
    promoted to audience truth).  Every real R4 ModelEvidence field is
    projected (mirrors S4ModelEvidencePermit); nothing is invented."""
    return {
        "model_evidence_id": _field("str", constraints=["nonempty"]),
        "role": _field("enum:model_evidence_role"),
        "permitted_leaf": _field("str", constraints=["nonempty"]),
        "model_id": _field("str", constraints=["nonempty"]),
        "model_version": _field("str", constraints=["nonempty"]),
        "evaluation_content_identity": _field("str"),
        "input_content_hash": _field("sha256"),
        "source_revision_content_pairs": _field("S4SourceRevisionPair", cardinality="many", constraints=["min_items:0"]),
        "source_refs": _field("str", cardinality="many", constraints=["min_items:0"]),
        "independent_context_hash": _field("sha256"),
        "ensemble_id": _field("str", constraints=["nonempty"]),
        "ensemble_size": _field("int", constraints=["min:1"]),
        "member_analysis_refs": _field("str", cardinality="many", constraints=["min_items:0"]),
        "member_analysis_ref_set_hash": _field("sha256"),
        "output_identity": _field("str"),
        "output_hash": _field("sha256"),
        "adjudication_state": _field("enum:model_evidence_adjudication_state"),
        "model_binding_hash": _field("sha256"),
    }


def _schema_object_audit_worker_row() -> Dict[str, Any]:
    return {
        "attempt_id": _field("str"),
        "binding_id": _field("str"),
        "session_id": _field("str"),
        "model_id": _field("str"),
        "model_version": _field("str"),
        "role": _field("enum:attempt_role"),
        "independent_context_hash": _field("sha256"),
        "input_content_hash": _field("sha256"),
        "output_artifact_ref": _field("str"),
        "declared_output_hash": _field("sha256"),
        "raw_bytes_sha256": _field("sha256"),
        "parsed_output_hash": _field("sha256"),
    }


def _schema_object_verification_audit_row() -> Dict[str, Any]:
    return {
        "verification_id": _field("str"),
        "attempt_id": _field("str"),
        "checked_dimensions": _field("str", cardinality="many", constraints=["exact_set:seven_dimensions", "min_items:7", "max_items:7"]),
        "result": _field("enum:verification_result"),
        "failure_reason_codes": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
        "recomputed": _field("bool", constraints=["equals:true"]),
    }


def _schema_object_digest_context_view() -> Dict[str, Any]:
    return {
        "input_content_hash": _field("sha256"),
        "output_digests": _field("str_map_sha256", constraints=["required"]),
        "evidence_digests": _field("str_set_sha256", constraints=["required"]),
        "expected_ensemble_identity": _field("str"),
        "artifact_date_windows": _field("str_map_str", constraints=["required"]),
        "artifact_unit_contracts": _field("str_map_str", constraints=["required"]),
        "artifact_source_versions": _field("str_map_str", constraints=["required"]),
        "artifact_model_versions": _field("str_map_str", constraints=["required"]),
        "artifact_rule_ids": _field("str_map_str", constraints=["required"]),
        "artifact_rule_versions": _field("str_map_str", constraints=["required"]),
        "artifact_finding_identities": _field("str_map_strset", constraints=["required"]),
        "artifact_authorized_source_locators": _field("str_map_strset", constraints=["required"]),
    }


def _schema_object_attempt_authority_row() -> Dict[str, Any]:
    return {
        "attempt_id": _field("str", constraints=["nonempty"]),
        "input_content_hash": _field("sha256"),
        "artifact_ref": _field("str", constraints=["nonempty"]),
        "raw_bytes_sha256": _field("sha256"),
        "parsed_output_hash": _field("sha256"),
        "date_window": _field("str", constraints=["nonempty"]),
        "unit_contract": _field("str", constraints=["nonempty"]),
        "source_revision": _field("str", constraints=["nonempty"]),
        "rule_id": _field("str", constraints=["nonempty"]),
        "rule_version": _field("str", constraints=["nonempty"]),
        "model_id": _field("str", constraints=["nonempty"]),
        "model_version": _field("str", constraints=["nonempty"]),
    }


def _schema_object_model_evidence_permit() -> Dict[str, Any]:
    """Accepted permit binds EVERY real R4 ModelEvidence dataclass field
    (d10_contracts.ModelEvidence), so no leaf can drift unobserved; the
    dataclass-field coverage assertion in the verifier/tests enforces that a
    new upstream field fails closed until this permit binds it."""
    return {
        "model_evidence_id": _field("str", constraints=["nonempty"]),
        "role": _field("enum:model_evidence_role"),
        "permitted_leaf": _field("str", constraints=["nonempty"]),
        "model_id": _field("str", constraints=["nonempty"]),
        "model_version": _field("str", constraints=["nonempty"]),
        "evaluation_content_identity": _field("str"),
        "input_content_hash": _field("sha256"),
        "source_revision_content_pairs": _field("S4SourceRevisionPair", cardinality="many", constraints=["min_items:0"]),
        "source_refs": _field("str", cardinality="many", constraints=["min_items:0"]),
        "independent_context_hash": _field("sha256"),
        "ensemble_id": _field("str", constraints=["nonempty"]),
        "ensemble_size": _field("int", constraints=["min:1"]),
        "member_analysis_refs": _field("str", cardinality="many", constraints=["min_items:0"]),
        "member_analysis_ref_set_hash": _field("sha256"),
        "output_identity": _field("str"),
        "output_hash": _field("sha256"),
        "adjudication_state": _field("enum:model_evidence_adjudication_state"),
        "model_binding_hash": _field("sha256"),
    }


def _schema_object_source_revision_pair() -> Dict[str, Any]:
    """Accepted ModelEvidence source-revision content pair (mirrors the R4
    d10_contracts.SourceRevisionPair dataclass)."""
    return {
        "revision_id": _field("str", constraints=["nonempty"]),
        "content_hash": _field("sha256"),
    }


def _schema_object_journey_target_identity() -> Dict[str, Any]:
    return {
        "project_ref": _field("str", constraints=["nonempty"]),
        "run_ref": _field("str", constraints=["nonempty"]),
        "snapshot_ref": _field("str", constraints=["nonempty"]),
        "cutoff_ref": _field("str", nullable=True),
        "site_ref": _field("str", nullable=True),
        "subject_ref": _field("str", nullable=True),
        "risk_ref": _field("str", constraints=["nonempty"]),
        "spine_ref": _field("str", constraints=["nonempty"]),
        "anchor_ref": _field("str", constraints=["nonempty"]),
        "event_ref": _field("str", nullable=True),
        "visit_ref": _field("str", nullable=True),
        "source_locator_ref": _field("str", nullable=True),
    }


def _schema_object_authority_anchor() -> Dict[str, Any]:
    return {
        "anchor_identity_hash": _field("sha256", constraints=["canonical_sha256_of:self_excluding_anchor_identity_hash"]),
        "schema": _field("str", constraints=["equals:medical-monitoring-r5-s4-authority-anchor-v0.1"]),
        "status": _field("str", constraints=["equals:R5_S4_CONTRACT_READY_FOR_REVIEW"]),
        "authority_mode": _field("str", constraints=["equals:synthetic_offline_test_only"]),
        "accepted_receipt_identity": _field("str", constraints=["nonempty"]),
        "accepted_receipt_content_hash": _field("sha256"),
        "accepted_risk_identity_hash": _field("sha256"),
        "accepted_risk_identity": _field("S4AcceptedRiskIdentity", constraints=["required"]),
        "accepted_adjudicator_binding": _field("S4AcceptedAdjudicatorBinding", constraints=["required"]),
        "project_ref": _field("str", constraints=["nonempty"]),
        "run_ref": _field("str", constraints=["nonempty"]),
        "snapshot_ref": _field("str", constraints=["nonempty"]),
        "cutoff_ref": _field("str", nullable=True),
        "site_ref": _field("str", nullable=True),
        "subject_ref": _field("str", nullable=True),
        "risk_ref": _field("str", constraints=["nonempty"]),
        "spine_ref": _field("str", constraints=["nonempty"]),
        "accepted_journey_target": _field("S4JourneyTargetIdentity", constraints=["required"]),
        "accepted_baseline_items": _field("S4AcceptedBaselineItem", cardinality="many", constraints=["sorted_unique_by:item_id", "min_items:0"]),
        "accepted_query_draft": _field("S4AcceptedQueryDraft", nullable=True),
        "accepted_history_no_ensemble": _field("S4AcceptedHistoryState", constraints=["required"]),
        "accepted_history_single_analysis": _field("S4AcceptedHistoryState", constraints=["required"]),
        "accepted_history_multi_analysis": _field("S4AcceptedHistoryState", constraints=["required"]),
        "attempt_authority_rows": _field("S4AttemptAuthorityRow", cardinality="many", constraints=["sorted_unique_by:attempt_id", "min_items:0"]),
        "model_evidence_permits": _field("S4ModelEvidencePermit", cardinality="many", constraints=["sorted_unique_by:model_evidence_id", "min_items:0"]),
        "risk_priority_authority": _field("enum:monitoring_priority"),
        "severity_authority": _field("enum:severity", constraints=["severity_mapping_from_monitoring_priority"]),
        "critical_severity_authority": _field("str", nullable=True, constraints=["required_when:severity_authority=critical"]),
    }


def _schema_object_accepted_history_state() -> Dict[str, Any]:
    return {
        "seq": _field("int", constraints=["min:0"]),
        "head": _field("str", constraints=["genesis_or_sha"]),
        "hash": _field("str", constraints=["sha256"]),
    }


def _schema_object_accepted_baseline_item() -> Dict[str, Any]:
    """Complete canonical identity + every contracted leaf of an accepted
    ReferenceBaselineItem (externally authoritative, never packet-redefined)."""
    return {
        "item_id": _field("str", constraints=["nonempty"]),
        "source_kind": _field("str", constraints=["nonempty"]),
        "source_locator_ids": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:1"]),
        "source_revision_id": _field("str", constraints=["nonempty"]),
        "snapshot_id": _field("str", constraints=["nonempty"]),
        "claimed_identity": _field("str", constraints=["nonempty"]),
        "temporal_window": _field("str", constraints=["nonempty"]),
        "claimed_content_hash": _field("sha256"),
        "origin_artifact_hash": _field("sha256"),
        "project_ref": _field("str", constraints=["nonempty"]),
        "run_ref": _field("str", constraints=["nonempty"]),
        "snapshot_ref": _field("str", constraints=["nonempty"]),
        "cutoff_ref": _field("str", nullable=True),
        "source_revision": _field("str", constraints=["nonempty"]),
    }


def _schema_object_accepted_query_draft() -> Dict[str, Any]:
    """Accepted D10 QueryDraft canonical identity/content (externally
    authoritative; packet/audience copies are projections only)."""
    return {
        "query_draft_id": _field("str", constraints=["nonempty"]),
        "risk_ref": _field("str", constraints=["nonempty"]),
        "basis_zh": _field("str", constraints=["nonempty"]),
        "finding_zh": _field("str", constraints=["nonempty"]),
        "action_zh": _field("str", constraints=["nonempty"]),
        "source_locator_refs": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:1"]),
        "pd_wording_state": _field("enum:pd_wording_state"),
        "content_hash": _field("sha256"),
        "draft_only": _field("bool", constraints=["equals:true"]),
    }


def _schema_object_accepted_risk_identity() -> Dict[str, Any]:
    """Externally accepted R5 risk-identity instance (packet/root/audience
    copies are projections only; the accepted instance is never packet-defined).
    Includes the accepted change leaves (change_kind/change_cause)."""
    return {
        "risk_ref": _field("str", constraints=["nonempty"]),
        "risk_identity_hash": _field("sha256"),
        "domain": _field("enum:domain"),
        "domain_zh": _field("str", constraints=["closed_zh:domain"]),
        "monitoring_priority": _field("enum:monitoring_priority"),
        "severity": _field("enum:severity"),
        "severity_zh": _field("str", constraints=["closed_zh:severity"]),
        "change_kind": _field("enum:change_kind"),
        "change_cause": _field("enum:change_cause"),
        "project_ref": _field("str", constraints=["nonempty"]),
        "run_ref": _field("str", constraints=["nonempty"]),
        "snapshot_ref": _field("str", constraints=["nonempty"]),
        "cutoff_ref": _field("str", nullable=True),
        "site_ref": _field("str", nullable=True),
        "subject_ref": _field("str", nullable=True),
        "spine_ref": _field("str", constraints=["nonempty"]),
    }


def _schema_object_accepted_adjudicator_binding() -> Dict[str, Any]:
    """Externally accepted adjudication binding identity (complete R4
    AdjudicationBinding + S4 independence-context seal).  The packet's
    adjudication_row is a projection of this accepted instance; the
    reviewed-artifact set is derived from the active worker raw artifacts."""
    return {
        "binding_id": _field("str", constraints=["nonempty"]),
        "session_id": _field("str", constraints=["nonempty"]),
        "model_id": _field("str", constraints=["nonempty"]),
        "model_version": _field("str", constraints=["nonempty"]),
        "independent_context_hash": _field("sha256"),
        "outcome": _field("enum:adjudication_outcome"),
    }


def build_schema() -> Dict[str, Any]:
    """Exact typed objects plus per-field descriptors and the hash DAG."""
    objects: Dict[str, Dict[str, Any]] = {
            "R5S4AuthorityPacket": {
            "packet_id": _field("str", constraints=["grammar:r5-s4-contract:<audience_content_hash>"]),
            "schema": _field("str", constraints=["equals:medical-monitoring-r5-s4-packet-schema-v0.1"]),
            "status": _field("str", constraints=["equals:R5_S4_CONTRACT_READY_FOR_REVIEW"]),
            "authority_mode": _field("str", constraints=["equals:synthetic_offline_test_only"]),
            "authority_anchor_ref": _field("str", constraints=["grammar:anchor:<sha256>"]),
            "anchor_identity_hash": _field("sha256", constraints=["equals:authority_anchor.anchor_identity_hash"]),
            "ensemble_projection_state": _field("enum:ensemble_projection_state"),
            "ensemble_id": _field("str"),
            "ensemble_size": _field("int", constraints=["cardinality_0_1_n:state_exact"]),
            "input_content_hash": _field("sha256", nullable=True, constraints=["required_when:state!=no_ensemble", "forbidden_when:state=no_ensemble"]),
            "risk_identity": _field("R5S4RiskIdentity", constraints=["required"]),
            "authority_receipt": _field("import:R5AuthorityReceipt", constraints=["required"]),
            "receipt_content_hash": _field("sha256", constraints=["canonical_sha256_of:authority_receipt"]),
            "baseline_items": _field("import:ReferenceBaselineItem", cardinality="many", constraints=["sorted_unique_by:item_id", "min_items:0"], import_extensions={
                "project_ref": _field("str", constraints=["nonempty", "grammar:project_ref:"]),
                "run_ref": _field("str", constraints=["nonempty", "grammar:run_ref:"]),
                "snapshot_ref": _field("str", constraints=["nonempty", "grammar:snapshot_ref:"]),
                "cutoff_ref": _field("str", nullable=True, constraints=["grammar:cutoff_ref:"]),
                "source_revision": _field("str", constraints=["nonempty", "grammar:source_revision:"]),
            }),
            "baseline_rows": _field("R5S4BaselineRow", cardinality="many", constraints=["sorted_unique_by:row_ref", "min_items:0"]),
            "worker_views": _field("R5S4WorkerView", cardinality="many", constraints=["sorted_unique_by:attempt_id", "exact_count:ensemble_size"]),
            "raw_artifacts": _field("R5S4RawOutputArtifact", cardinality="many", constraints=["sorted_unique_by:artifact_id", "exact_count:ensemble_size"]),
            "verification_rows": _field("R5S4VerificationRow", cardinality="many", constraints=["sorted_unique_by:verification_id", "exact_count:ensemble_size"]),
            "conflict_rows": _field("R5S4ConflictRow", cardinality="many", constraints=["sorted_unique_by:conflict_id", "min_items:0"]),
            "adjudication_row": _field("R5S4AdjudicationRow", constraints=["required"]),
            "query_draft_row": _field("R5S4QueryDraftRow", nullable=True),
            "journey_link": _field("R5S4JourneyLink", constraints=["required"]),
            "history_log": _field("R5S4HistoryLog", constraints=["required"]),
            "audience_inspector": _field("R5S4AudienceInspector", constraints=["required"]),
            "audit_inspector": _field("R5S4AuditInspector", constraints=["required"]),
            "audience_content_hash": _field("sha256", constraints=["canonical_sha256_of:audience_inspector"]),
            "audit_content_hash": _field("sha256", constraints=["canonical_sha256_of:audit_inspector_excluding:packet_fingerprints"]),
            "packet_integrity_hash": _field("sha256", constraints=["canonical_sha256_of_all_leaves_excluding_self_and_hash_fields_and_dependencies"]),
        },
        "R5S4RiskIdentity": _schema_object_risk_identity(),
        "R5S4WorkerView": _schema_object_worker_view(),
        "R5S4RawOutputArtifact": _schema_object_raw_artifact(),
        "R5S4BaselineRow": _schema_object_baseline_row(),
        "R5S4ConflictRow": _schema_object_conflict_row(),
        "R5S4VerificationRow": _schema_object_verification_row(),
        "R5S4AdjudicationRow": _schema_object_adjudication_row(),
        "R5S4QueryDraftRow": _schema_object_query_draft_row(),
        "R5S4JourneyLink": _schema_object_journey_link(),
        "R5S4HistoryEntry": _schema_object_history_entry(),
        "R5S4HistoryLog": _schema_object_history_log(),
        "R5S4AudienceInspector": _schema_object_audience_inspector(),
        "R5S4AudienceBaselineRow": _schema_object_audience_baseline_row(),
        "R5S4AudienceWorkerSummary": _schema_object_audience_worker_summary(),
        "R5S4AuditInspector": _schema_object_audit_inspector(),
        "R5S4ModelEvidenceRef": _schema_object_model_evidence_ref(),
        "R5S4AuditWorkerRow": _schema_object_audit_worker_row(),
        "R5S4VerificationAuditRow": _schema_object_verification_audit_row(),
        "R5S4DigestContextView": _schema_object_digest_context_view(),
        "S4AttemptAuthorityRow": _schema_object_attempt_authority_row(),
        "S4ModelEvidencePermit": _schema_object_model_evidence_permit(),
        "S4JourneyTargetIdentity": _schema_object_journey_target_identity(),
        "S4AcceptedHistoryState": _schema_object_accepted_history_state(),
        "S4AcceptedBaselineItem": _schema_object_accepted_baseline_item(),
        "S4AcceptedQueryDraft": _schema_object_accepted_query_draft(),
        "S4AcceptedRiskIdentity": _schema_object_accepted_risk_identity(),
        "S4AcceptedAdjudicatorBinding": _schema_object_accepted_adjudicator_binding(),
        "S4SourceRevisionPair": _schema_object_source_revision_pair(),
        "S4AcceptedAuthorityAnchor": _schema_object_authority_anchor(),
    }
    schema = {
        "schema": SCHEMA_BASE,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "hash_dag": _hash_dag(),
        "objects": objects,
        "imports": {
            "R5AuthorityReceipt": "mm_r5.contracts:R5AuthorityReceipt",
            "ReferenceBaselineItem": "mm_r4.ensemble_contracts:ReferenceBaselineItem",
            "SourceRevisionContentPair": "mm_r5.contracts:SourceRevisionContentPair",
        },
        "import_schemas": {
            "SourceRevisionContentPair": {
                "revision_id": _field("str", constraints=["nonempty"]),
                "content_hash": _field("sha256"),
            },
            "R5AuthorityReceipt": {
                "audience_contract_id": _field("str", constraints=["nonempty"]),
                "cutoff_ref": _field("str", nullable=True),
                "evaluation_content_identities": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:0"]),
                "project_ref": _field("str", constraints=["nonempty"]),
                "public_projection_content_hash": _field("sha256"),
                "public_projection_id": _field("str", constraints=["nonempty"]),
                "public_projection_kind": _field("enum:projection_kind"),
                "run_ref": _field("str", constraints=["nonempty"]),
                "snapshot_ref": _field("str", constraints=["nonempty"]),
                "source_revision_content_pairs": _field("SourceRevisionContentPair", cardinality="many", constraints=["min_items:0"]),
                "visibility_decision_hash": _field("sha256"),
                "visibility_decision_id": _field("str", constraints=["nonempty"]),
            },
            "ReferenceBaselineItem": {
                "item_id": _field("str", constraints=["nonempty"]),
                "source_kind": _field("str", constraints=["nonempty"]),
                "source_locator_ids": _field("str", cardinality="many", constraints=["sorted_unique", "min_items:1"]),
                "source_revision_id": _field("str", constraints=["nonempty"]),
                "snapshot_id": _field("str", constraints=["nonempty"]),
                "claimed_identity": _field("str", constraints=["nonempty"]),
                "temporal_window": _field("str", constraints=["nonempty"]),
                "claimed_content_hash": _field("sha256"),
                "origin_artifact_hash": _field("sha256"),
            },
        },
    }
    _validate_built_schema(schema)
    return schema


def _validate_built_schema(schema: Dict[str, Any]) -> None:
    objects = schema["objects"]
    required_objects = {
        "R5S4AuthorityPacket", "R5S4RiskIdentity", "R5S4WorkerView",
        "R5S4RawOutputArtifact", "R5S4BaselineRow", "R5S4ConflictRow",
        "R5S4VerificationRow", "R5S4AdjudicationRow", "R5S4QueryDraftRow",
        "R5S4JourneyLink", "R5S4HistoryEntry", "R5S4HistoryLog",
        "R5S4AudienceInspector", "R5S4AuditInspector",
        "S4AcceptedAuthorityAnchor",
    }
    missing = required_objects - set(objects)
    if missing:
        raise RuntimeError(f"schema missing objects: {sorted(missing)}")
    # hash DAG acyclicity: packet_integrity_hash must exclude the other hashes.
    dag = schema["hash_dag"]
    if "packet_integrity_hash" not in dag:
        raise RuntimeError("hash DAG missing packet_integrity_hash")
    excluded = set(dag["packet_integrity_hash"].get("excluded_root_keys", []))
    for dep in ("audience_content_hash", "audit_content_hash",
                "receipt_content_hash"):
        if dep not in excluded:
            raise RuntimeError(
                f"packet_integrity_hash must exclude dependency {dep!r} "
                "(acyclic hash DAG)")


# ---------------------------------------------------------------------------
# exact_overlay.json
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Source matrix: one row per schema leaf (real path | deterministic derived |
# contract constant | synthetic offline recipe | honest named deferred).
# ---------------------------------------------------------------------------

#: object.field -> real ``module:Class.field`` path (resolved by the verifier
#: via AST against the pinned R4/R5 sources).
REAL_LEAF_PATHS: Dict[str, str] = {
    "R5S4RiskIdentity.risk_ref": "mm_r4.d10_projection:D10RiskMarker.marker_id",
    "R5S4RiskIdentity.monitoring_priority": "mm_r4.contracts:MONITORING_PRIORITIES",
    "R5S4RiskIdentity.domain": "mm_r5.s2_contracts:S2_DOMAINS",
    "R5S4WorkerView.attempt_id": "mm_r4.ensemble_contracts:AnalysisAttempt.attempt_id",
    "R5S4WorkerView.binding_id": "mm_r4.ensemble_contracts:AnalysisAttempt.binding_id",
    "R5S4WorkerView.session_id": "mm_r4.ensemble_contracts:AnalysisAttempt.session_id",
    "R5S4WorkerView.model_id": "mm_r4.ensemble_contracts:AnalysisAttempt.model_id",
    "R5S4WorkerView.model_version": "mm_r4.ensemble_contracts:AnalysisAttempt.model_version",
    "R5S4WorkerView.role": "mm_r4.ensemble_contracts:AnalysisAttempt.role",
    "R5S4WorkerView.independent_context_hash": "mm_r4.ensemble_contracts:AnalysisAttempt.independent_context_hash",
    "R5S4WorkerView.input_content_hash": "mm_r4.ensemble_contracts:AnalysisAttempt.input_content_hash",
    "R5S4WorkerView.output_artifact_ref": "mm_r4.ensemble_contracts:AnalysisAttempt.output_artifact_ref",
    "R5S4WorkerView.declared_output_hash": "mm_r4.ensemble_contracts:AnalysisAttempt.output_hash",
    "R5S4WorkerView.claimed_date_window": "mm_r4.ensemble_contracts:AnalysisAttempt.claimed_date_window",
    "R5S4WorkerView.claimed_unit_contract": "mm_r4.ensemble_contracts:AnalysisAttempt.claimed_unit_contract",
    "R5S4WorkerView.claimed_source_revision": "mm_r4.ensemble_contracts:AnalysisAttempt.claimed_source_revision",
    "R5S4WorkerView.claimed_rule_id": "mm_r4.ensemble_contracts:AnalysisAttempt.claimed_rule_id",
    "R5S4WorkerView.claimed_rule_version": "mm_r4.ensemble_contracts:AnalysisAttempt.claimed_rule_version",
    "R5S4RawOutputArtifact.attempt_id": "mm_r4.ensemble_contracts:AnalysisAttempt.attempt_id",
    "R5S4RawOutputArtifact.declared_output_hash": "mm_r4.ensemble_contracts:AnalysisAttempt.output_hash",
    "R5S4BaselineRow.item_id": "mm_r4.ensemble_contracts:BaselineAssessment.item_id",
    "R5S4BaselineRow.attempt_id": "mm_r4.ensemble_contracts:BaselineAssessment.attempt_id",
    "R5S4BaselineRow.state": "mm_r4.ensemble_contracts:BaselineAssessment.state",
    "R5S4BaselineRow.reason_codes": "mm_r4.ensemble_contracts:BaselineAssessment.reason_codes",
    "R5S4BaselineRow.source_recheck_locator_ids": "mm_r4.ensemble_contracts:BaselineAssessment.source_recheck_locator_ids",
    "R5S4ConflictRow.relation": "mm_r4.ensemble_contracts:ConflictVisibility.relation",
    "R5S4ConflictRow.display_state": "mm_r4.ensemble_contracts:ConflictVisibility.display_state",
    "R5S4ConflictRow.hidden": "mm_r4.ensemble_contracts:ConflictVisibility.hidden",
    "R5S4ConflictRow.monitoring_priority": "mm_r4.ensemble_contracts:ConflictVisibility.monitoring_priority",
    "R5S4ConflictRow.member_attempt_ids": "mm_r4.ensemble_contracts:ConflictVisibility.member_attempt_ids",
    "R5S4AdjudicationRow.binding_id": "mm_r4.ensemble_contracts:AdjudicationBinding.binding_id",
    "R5S4AdjudicationRow.session_id": "mm_r4.ensemble_contracts:AdjudicationBinding.session_id",
    "R5S4AdjudicationRow.model_id": "mm_r4.ensemble_contracts:AdjudicationBinding.model_id",
    "R5S4AdjudicationRow.model_version": "mm_r4.ensemble_contracts:AdjudicationBinding.model_version",
    "R5S4AdjudicationRow.outcome": "mm_r4.ensemble_contracts:AdjudicationBinding.outcome",
    "R5S4AdjudicationRow.reviewed_artifact_refs": "mm_r4.ensemble_contracts:AdjudicationBinding.reviewed_artifact_refs",
    "R5S4QueryDraftRow.basis_zh": "mm_r4.d10_projection:D10QueryDraft.basis_sentence",
    "R5S4QueryDraftRow.finding_zh": "mm_r4.d10_projection:D10QueryDraft.finding_sentence",
    "R5S4QueryDraftRow.action_zh": "mm_r4.d10_projection:D10QueryDraft.action_sentence",
    "R5S4QueryDraftRow.pd_wording_state": "mm_r4.d10_projection:D10QueryDraft.pd_wording_state",
    "R5S4QueryDraftRow.source_locator_refs": "mm_r4.d10_projection:D10QueryDraft.source_locator_ids",
    "R5S4AuditInspector.digest_context.input_content_hash": "mm_r4.ensemble:EvidenceDigestContext.input_content_hash",
    "R5S4AuditInspector.digest_context.output_digests": "mm_r4.ensemble:EvidenceDigestContext.output_digests",
    "R5S4AuditInspector.digest_context.evidence_digests": "mm_r4.ensemble:EvidenceDigestContext.evidence_digests",
    "R5S4AuditInspector.digest_context.expected_ensemble_identity": "mm_r4.ensemble:EvidenceDigestContext.expected_ensemble_identity",
    "R5S4AuditInspector.digest_context.artifact_date_windows": "mm_r4.ensemble:EvidenceDigestContext.artifact_date_windows",
    "R5S4AuditInspector.digest_context.artifact_unit_contracts": "mm_r4.ensemble:EvidenceDigestContext.artifact_unit_contracts",
    "R5S4AuditInspector.digest_context.artifact_source_versions": "mm_r4.ensemble:EvidenceDigestContext.artifact_source_versions",
    "R5S4AuditInspector.digest_context.artifact_model_versions": "mm_r4.ensemble:EvidenceDigestContext.artifact_model_versions",
    "R5S4AuditInspector.digest_context.artifact_rule_ids": "mm_r4.ensemble:EvidenceDigestContext.artifact_rule_ids",
    "R5S4AuditInspector.digest_context.artifact_rule_versions": "mm_r4.ensemble:EvidenceDigestContext.artifact_rule_versions",
    "R5S4AuditInspector.digest_context.artifact_finding_identities": "mm_r4.ensemble:EvidenceDigestContext.artifact_finding_identities",
    "R5S4AuditInspector.digest_context.artifact_authorized_source_locators": "mm_r4.ensemble:EvidenceDigestContext.artifact_authorized_source_locators",
    "R5S4ModelEvidenceRef.model_evidence_id": "mm_r4.d10_contracts:ModelEvidence.model_evidence_id",
    "R5S4ModelEvidenceRef.role": "mm_r4.d10_contracts:ModelEvidence.role",
    "R5S4ModelEvidenceRef.permitted_leaf": "mm_r4.d10_contracts:ModelEvidence.permitted_leaf",
    "R5S4ModelEvidenceRef.model_id": "mm_r4.d10_contracts:ModelEvidence.model_id",
    "R5S4ModelEvidenceRef.model_version": "mm_r4.d10_contracts:ModelEvidence.model_version",
    "R5S4ModelEvidenceRef.adjudication_state": "mm_r4.d10_contracts:ModelEvidence.adjudication_state",
    "R5S4ModelEvidenceRef.output_hash": "mm_r4.d10_contracts:ModelEvidence.output_hash",
    "R5S4ModelEvidenceRef.ensemble_id": "mm_r4.d10_contracts:ModelEvidence.ensemble_id",
    "R5S4ModelEvidenceRef.independent_context_hash": "mm_r4.d10_contracts:ModelEvidence.independent_context_hash",
    "R5S4ModelEvidenceRef.evaluation_content_identity": "mm_r4.d10_contracts:ModelEvidence.evaluation_content_identity",
    "R5S4ModelEvidenceRef.input_content_hash": "mm_r4.d10_contracts:ModelEvidence.input_content_hash",
    "R5S4ModelEvidenceRef.source_revision_content_pairs": "mm_r4.d10_contracts:ModelEvidence.source_revision_content_pairs",
    "R5S4ModelEvidenceRef.source_refs": "mm_r4.d10_contracts:ModelEvidence.source_refs",
    "R5S4ModelEvidenceRef.ensemble_size": "mm_r4.d10_contracts:ModelEvidence.ensemble_size",
    "R5S4ModelEvidenceRef.member_analysis_refs": "mm_r4.d10_contracts:ModelEvidence.member_analysis_refs",
    "R5S4ModelEvidenceRef.member_analysis_ref_set_hash": "mm_r4.d10_contracts:ModelEvidence.member_analysis_ref_set_hash",
    "R5S4ModelEvidenceRef.output_identity": "mm_r4.d10_contracts:ModelEvidence.output_identity",
    "R5S4ModelEvidenceRef.model_binding_hash": "mm_r4.d10_contracts:ModelEvidence.model_binding_hash",
    "R5S4AuditWorkerRow.attempt_id": "mm_r4.ensemble_contracts:AnalysisAttempt.attempt_id",
    "R5S4AuditWorkerRow.binding_id": "mm_r4.ensemble_contracts:AnalysisAttempt.binding_id",
    "R5S4AuditWorkerRow.session_id": "mm_r4.ensemble_contracts:AnalysisAttempt.session_id",
    "R5S4AuditWorkerRow.model_id": "mm_r4.ensemble_contracts:AnalysisAttempt.model_id",
    "R5S4AuditWorkerRow.model_version": "mm_r4.ensemble_contracts:AnalysisAttempt.model_version",
    "R5S4AuditWorkerRow.role": "mm_r4.ensemble_contracts:AnalysisAttempt.role",
    "R5S4AuditWorkerRow.independent_context_hash": "mm_r4.ensemble_contracts:AnalysisAttempt.independent_context_hash",
    "R5S4AuditWorkerRow.input_content_hash": "mm_r4.ensemble_contracts:AnalysisAttempt.input_content_hash",
    "R5S4AuditWorkerRow.output_artifact_ref": "mm_r4.ensemble_contracts:AnalysisAttempt.output_artifact_ref",
    "R5S4AuditWorkerRow.declared_output_hash": "mm_r4.ensemble_contracts:AnalysisAttempt.output_hash",
    "R5S4AuditWorkerRow.raw_bytes_sha256": "canonical(sha256(base64decode(raw_bytes_b64)))",
    "R5S4AuditWorkerRow.parsed_output_hash": "canonical(mm_r4.ensemble:worker_output_content_hash)",
    "R5S4JourneyLink.deep_link_project_ref": "mm_r5.contracts:R5DeepLinkState.project_ref",
    "R5S4JourneyLink.deep_link_run_ref": "mm_r5.contracts:R5DeepLinkState.run_ref",
    "R5S4JourneyLink.deep_link_snapshot_ref": "mm_r5.contracts:R5DeepLinkState.snapshot_ref",
    "R5S4JourneyLink.deep_link_cutoff_ref": "mm_r5.contracts:R5DeepLinkState.cutoff_ref",
    "R5S4JourneyLink.deep_link_site_ref": "mm_r5.contracts:R5DeepLinkState.site_ref",
    "R5S4JourneyLink.deep_link_subject_ref": "mm_r5.contracts:R5DeepLinkState.subject_ref",
    "R5S4JourneyLink.deep_link_risk_ref": "mm_r5.contracts:R5DeepLinkState.risk_ref",
    "R5S4JourneyLink.deep_link_event_ref": "mm_r5.contracts:R5DeepLinkState.event_ref",
    "R5S4JourneyLink.deep_link_visit_ref": "mm_r5.contracts:R5DeepLinkState.visit_ref",
    "R5S4JourneyLink.deep_link_spine_ref": "mm_r5.contracts:R5DeepLinkState.spine_ref",
    "R5S4JourneyLink.deep_link_anchor_ref": "mm_r5.contracts:R5DeepLinkState.risk_anchor_ref",
    "R5S4JourneyLink.deep_link_source_locator_ref": "mm_r5.contracts:R5DeepLinkState.source_locator_ref",
    "R5S4RiskIdentity.risk_identity_hash": "canonical(mm_r4.d10_projection:D10RiskMarker.public_risk_identity)",
}

#: object.field -> deterministic canonical/derived recipe id (never a fake
#: module path; recomputed from leaves).
DERIVED_LEAF_RECIPES: Dict[str, str] = {
    "R5S4RiskIdentity.severity": "severity_mapping(monitoring_priority)",
    "R5S4RiskIdentity.severity_zh": "severity_zh lexicon(canonical)",
    "R5S4RiskIdentity.domain_zh": "domain_zh lexicon(canonical)",
    "R5S4RiskIdentity.change_kind": "R5 exact change_kind enum",
    "R5S4RiskIdentity.change_cause": "R5 exact change_cause enum",
    "R5S4WorkerView.ordinal": "ordinal = sorted index over attempt_id (canonical)",
    "R5S4WorkerView.ordinal_zh": "ordinal_zh lexicon(ordinal)",
    "R5S4WorkerView.assessment_row_refs": "derived: baseline-row:<item_id>:<attempt_id>",
    "R5S4WorkerView.finding_ids": "derived: finding ids from parsed worker output",
    "R5S4WorkerView.gap_ids": "derived: gap ids from parsed worker output",
    "R5S4WorkerView.raw_artifact_ref": "derived: raw:<attempt_id>",
    "R5S4WorkerView.verification_ref": "derived: verification:v-<attempt_id>",
    "R5S4RawOutputArtifact.artifact_id": "derived: raw:<attempt_id>",
    "R5S4RawOutputArtifact.raw_bytes_sha256": "canonical: sha256(base64decode(raw_bytes_b64))",
    "R5S4RawOutputArtifact.parsed_output_hash": "canonical: worker_output_content_hash(reconstructed output)",
    "R5S4RawOutputArtifact.raw_format": "S4 frozen single value: utf8_text",
    "R5S4BaselineRow.row_ref": "derived: baseline-row:<item_id>:<attempt_id>",
    "R5S4BaselineRow.source_revision_id": "derived: reference item source_revision_id",
    "R5S4BaselineRow.snapshot_id": "derived: reference item snapshot_id",
    "R5S4BaselineRow.recheck_complete": "canonical: state in recheck-required => locators nonempty",
    "R5S4ConflictRow.conflict_id": "canonical: R4 derive_conflicts recompute",
    "R5S4ConflictRow.ordinal_labels_zh": "canonical: ordinal_zh of member attempts",
    "R5S4VerificationRow.verification_id": "canonical: R4 verify_attempt recompute",
    "R5S4VerificationRow.attempt_id": "derived: attempt identity",
    "R5S4VerificationRow.checked_dimensions": "canonical: R4 verify_attempt recompute (seven dims)",
    "R5S4VerificationRow.result": "canonical: R4 verify_attempt recompute",
    "R5S4VerificationRow.failure_reason_codes": "canonical: R4 verify_attempt recompute",
    "R5S4VerificationRow.recomputed": "S4 frozen constant: true",
    "R5S4AdjudicationRow.present": "S4 frozen derived: state != no_ensemble and adjudicator bound",
    "R5S4AdjudicationRow.independent_context_hash": "synthetic s4 wrapper: R4 Adjudicator has no context hash (S4 seals it)",
    "R5S4AdjudicationRow.adds_explanation_only": "S4 frozen constant: true",
    "R5S4QueryDraftRow.query_draft_id": "derived: D10QueryDraft.query_draft_id",
    "R5S4QueryDraftRow.risk_ref": "derived: D10RiskMarker.marker_id",
    "R5S4QueryDraftRow.draft_only": "S4 frozen constant: true",
    "R5S4JourneyLink.fallback_policy": "S2 FALLBACK_POLICIES frozen single value: none",
    "R5S4JourneyLink.journey_available": "canonical: all required deep-link identities present",
    "R5S4HistoryLog.history_ref": "derived: history:s4.<seq>",
    "R5S4HistoryLog.head_seq": "canonical: len(entries)",
    "R5S4HistoryLog.head_hash": "canonical: last entry.entry_hash",
    "R5S4HistoryLog.entries": "canonical: append-only chained entry hashes",
    "R5S4HistoryEntry.entry_id": "derived: h<seq>",
    "R5S4HistoryEntry.seq": "canonical: strictly increasing 1..N",
    "R5S4HistoryEntry.kind": "S4 frozen history kind enum",
    "R5S4HistoryEntry.payload_ref": "derived: payload.h<seq>",
    "R5S4HistoryEntry.prior_entry_hash": "canonical: genesis for first, else prior entry hash",
    "R5S4HistoryEntry.entry_hash": "canonical: chained sha of entry incl prior hash",
    "R5S4AuditInspector.authority_receipt_ref": "derived: receipt:<receipt_content_hash>",
    "R5S4AuditInspector.receipt_content_hash": "canonical: sha256(authority_receipt)",
    "R5S4AuditInspector.verification_audit_rows": "canonical: R4 verify_attempt recompute",
    "R5S4AuditInspector.adjudication_audit": "derived: adjudication record refs",
    "R5S4AuditInspector.conflict_audit": "derived: conflict ids",
    "R5S4AuditInspector.history_audit": "derived: entry hashes",
    "R5S4AuditInspector.packet_fingerprints": "canonical: sorted([audience:<audience_content_hash>, receipt:<receipt_content_hash>, packet:<packet_id>, risk_identity:<risk_identity_hash>]) acyclic prefix labels",
    "R5S4VerificationAuditRow.verification_id": "canonical: R4 verify_attempt recompute",
    "R5S4VerificationAuditRow.attempt_id": "derived: attempt identity",
    "R5S4VerificationAuditRow.checked_dimensions": "canonical: R4 verify_attempt recompute",
    "R5S4VerificationAuditRow.result": "canonical: R4 verify_attempt recompute",
    "R5S4VerificationAuditRow.failure_reason_codes": "canonical: R4 verify_attempt recompute",
    "R5S4VerificationAuditRow.recomputed": "S4 frozen constant: true",
    "R5S4DigestContextView.input_content_hash": "r4_public: EvidenceDigestContext.input_content_hash",
    "R5S4DigestContextView.output_digests": "r4_public: EvidenceDigestContext.output_digests",
    "R5S4DigestContextView.evidence_digests": "r4_public: EvidenceDigestContext.evidence_digests",
    "R5S4DigestContextView.expected_ensemble_identity": "r4_public: EvidenceDigestContext.expected_ensemble_identity",
    "R5S4DigestContextView.artifact_date_windows": "r4_public: EvidenceDigestContext.artifact_date_windows",
    "R5S4DigestContextView.artifact_unit_contracts": "r4_public: EvidenceDigestContext.artifact_unit_contracts",
    "R5S4DigestContextView.artifact_source_versions": "r4_public: EvidenceDigestContext.artifact_source_versions",
    "R5S4DigestContextView.artifact_model_versions": "r4_public: EvidenceDigestContext.artifact_model_versions",
    "R5S4DigestContextView.artifact_rule_ids": "r4_public: EvidenceDigestContext.artifact_rule_ids",
    "R5S4DigestContextView.artifact_rule_versions": "r4_public: EvidenceDigestContext.artifact_rule_versions",
    "R5S4DigestContextView.artifact_finding_identities": "r4_public: EvidenceDigestContext.artifact_finding_identities",
    "R5S4DigestContextView.artifact_authorized_source_locators": "r4_public: EvidenceDigestContext.artifact_authorized_source_locators",
}

#: object.field -> named synthetic recipe (audience zh / display; deterministic
#: offline test derivation, never an invented module path).
SYNTHETIC_LEAF_RECIPES: Dict[str, str] = {
    "R5S4AuthorityPacket.packet_id": "grammar: r5-s4-contract:<audience_content_hash>",
    "R5S4AuthorityPacket.authority_anchor_ref": "grammar: anchor:<sha256> (external anchor identity)",
    "R5S4AuthorityPacket.anchor_identity_hash": "canonical: equals external S4AcceptedAuthorityAnchor.anchor_identity_hash",
    "R5S4AuthorityPacket.schema": "S4 frozen schema id",
    "R5S4AuthorityPacket.status": "S4 frozen status",
    "R5S4AuthorityPacket.authority_mode": "S4 frozen authority mode",
    "R5S4AuthorityPacket.ensemble_projection_state": "S4 frozen 0/1/N state",
    "R5S4AuthorityPacket.ensemble_id": "derived: ensemble identity from digest context",
    "R5S4AuthorityPacket.ensemble_size": "canonical: cardinality of worker_views",
    "R5S4AuthorityPacket.input_content_hash": "r4_public: shared attempt input hash",
    "R5S4AuthorityPacket.risk_identity": "synthetic: R5 audience risk identity object",
    "R5S4AuthorityPacket.authority_receipt": "r5_public: R5AuthorityReceipt import",
    "R5S4AuthorityPacket.receipt_content_hash": "canonical: sha256(authority_receipt)",
    "R5S4AuthorityPacket.baseline_items": "r4_public: ReferenceBaselineItem import",
    "R5S4AuthorityPacket.baseline_rows": "r4_public: BaselineAssessment rows",
    "R5S4AuthorityPacket.worker_views": "r4_public: AnalysisAttempt views",
    "R5S4AuthorityPacket.raw_artifacts": "derived: raw byte artifacts",
    "R5S4AuthorityPacket.verification_rows": "canonical: R4 verify_attempt recompute",
    "R5S4AuthorityPacket.conflict_rows": "canonical: R4 derive_conflicts recompute",
    "R5S4AuthorityPacket.adjudication_row": "r4_public: AdjudicationBinding + S4 seal",
    "R5S4AuthorityPacket.query_draft_row": "r4_public: D10QueryDraft three-part draft",
    "R5S4AuthorityPacket.journey_link": "r5_public: R5DeepLinkState identities",
    "R5S4AuthorityPacket.history_log": "S4 frozen append-only history",
    "R5S4AuthorityPacket.audience_inspector": "synthetic: audience zh projection",
    "R5S4AuthorityPacket.audit_inspector": "audit: private projection",
    "R5S4AuthorityPacket.audience_content_hash": "canonical: sha256(audience_inspector)",
    "R5S4AuthorityPacket.audit_content_hash": "canonical: sha256(audit_inspector minus packet_fingerprints) acyclic exclusion",
    "R5S4AuthorityPacket.packet_integrity_hash": "canonical: sha256(all leaves except id/hashes/deps)",
    "R5S4RiskIdentity.project_ref": "synthetic: project unique projection",
    "R5S4RiskIdentity.run_ref": "synthetic: run unique projection",
    "R5S4RiskIdentity.snapshot_ref": "synthetic: snapshot unique projection",
    "R5S4RiskIdentity.cutoff_ref": "synthetic: cutoff unique projection (nullable)",
    "R5S4RiskIdentity.site_ref": "synthetic: site unique projection (nullable)",
    "R5S4RiskIdentity.subject_ref": "synthetic: subject unique projection (nullable)",
    "R5S4RiskIdentity.spine_ref": "external accepted authority: subject temporal spine identity (critical packets require external acceptance)",
    "R5S4RawOutputArtifact.raw_bytes_b64": "synthetic offline test fixture: raw worker output bytes",
    "R5S4AudienceInspector.audience_contract_id": "synthetic: audience contract identity",
    "R5S4AudienceInspector.risk_title_zh": "synthetic: risk display title",
    "R5S4AudienceInspector.domain_zh": "synthetic: domain zh lexicon",
    "R5S4AudienceInspector.severity_zh": "synthetic: severity zh lexicon",
    "R5S4AudienceInspector.change_state_zh": "synthetic: change state zh",
    "R5S4AudienceInspector.subject_display_zh": "synthetic: subject display",
    "R5S4AudienceInspector.center_display_zh": "synthetic: center display",
    "R5S4AudienceInspector.project_display_zh": "synthetic: project display",
    "R5S4AudienceInspector.cutoff_display_zh": "synthetic: cutoff display",
    "R5S4AudienceInspector.basis_zh": "synthetic: why-reminder basis zh",
    "R5S4AudienceInspector.support_evidence_zh": "synthetic: support evidence zh (projectable locators only)",
    "R5S4AudienceInspector.counterevidence_zh": "synthetic: counterevidence zh (projectable locators only)",
    "R5S4AudienceInspector.source_one_hop_zh": "synthetic: one-hop source zh",
    "R5S4AudienceInspector.worker_ordinal_summaries": "synthetic: per-worker zh summaries",
    "R5S4AudienceInspector.consensus_zh": "synthetic: gated consensus phrase",
    "R5S4AudienceInspector.adjudication_status_zh": "synthetic: adjudication status zh (never independent when absent)",
    "R5S4AudienceInspector.adjudication_explanation_zh": "synthetic: adjudication explanation zh (nullable)",
    "R5S4AudienceInspector.query_basis_zh": "synthetic: query basis zh",
    "R5S4AudienceInspector.query_finding_zh": "synthetic: query finding zh",
    "R5S4AudienceInspector.query_action_zh": "synthetic: query action zh",
    "R5S4AudienceInspector.query_pd_wording_zh": "synthetic: query pd wording zh",
    "R5S4AudienceInspector.history_summary_zh": "synthetic: history summary zh",
    "R5S4AudienceInspector.journey_available": "derived: journey identity completeness",
    "R5S4AudienceInspector.journey_link_zh": "synthetic: journey link zh",
    "R5S4AudienceInspector.journey_unavailable_reason_zh": "synthetic: journey unavailable reason zh (nullable)",
    "R5S4AudienceBaselineRow.row_ref": "derived: baseline-row composite identity (baseline-row:<item_id>:<attempt_id>)",
    "R5S4AudienceBaselineRow.item_anchor_zh": "synthetic: baseline item anchor zh",
    "R5S4AudienceBaselineRow.ordinal_zh": "synthetic: ordinal zh",
    "R5S4AudienceBaselineRow.state_zh": "synthetic: baseline state zh",
    "R5S4AudienceBaselineRow.recheck_zh": "synthetic: recheck status zh",
    "R5S4AudienceWorkerSummary.ordinal_zh": "synthetic: ordinal zh",
    "R5S4AudienceWorkerSummary.finding_summary_zh": "synthetic: finding summary zh",
    "R5S4AudienceWorkerSummary.verification_zh": "synthetic: verification zh",
    "R5S4AudienceWorkerSummary.gap_zh": "synthetic: gap zh",
    "R5S4JourneyLink.unavailable_reason_zh": "synthetic: journey unavailable reason zh (nullable)",
}

#: object.field -> external accepted-authority recipe (anchor is a separate
#: external input; its leaves are accepted truth, never packet-owned).
AUTHORITY_LEAF_RECIPES: Dict[str, str] = {
    "S4AcceptedAuthorityAnchor.anchor_identity_hash": "canonical: sha256(anchor body excluding anchor_identity_hash)",
    "S4AcceptedAuthorityAnchor.schema": "S4 frozen anchor schema id",
    "S4AcceptedAuthorityAnchor.status": "S4 frozen status",
    "S4AcceptedAuthorityAnchor.authority_mode": "S4 frozen authority mode",
    "S4AcceptedAuthorityAnchor.accepted_receipt_identity": "external: accepted R5 receipt identity",
    "S4AcceptedAuthorityAnchor.accepted_receipt_content_hash": "external: canonical sha256 of accepted R5AuthorityReceipt",
    "S4AcceptedAuthorityAnchor.project_ref": "external: accepted project identity",
    "S4AcceptedAuthorityAnchor.run_ref": "external: accepted run identity",
    "S4AcceptedAuthorityAnchor.snapshot_ref": "external: accepted snapshot identity",
    "S4AcceptedAuthorityAnchor.cutoff_ref": "external: accepted cutoff identity (nullable)",
    "S4AcceptedAuthorityAnchor.site_ref": "external: accepted site identity (nullable)",
    "S4AcceptedAuthorityAnchor.subject_ref": "external: accepted subject identity (nullable)",
    "S4AcceptedAuthorityAnchor.risk_ref": "external: accepted risk identity",
    "S4AcceptedAuthorityAnchor.spine_ref": "external: accepted subject temporal spine identity",
    "S4AcceptedAuthorityAnchor.accepted_journey_target": "external: accepted Journey target identity",
    "S4AcceptedAuthorityAnchor.accepted_risk_identity_hash": "external: accepted R4 public risk identity hash",
    "S4AcceptedAuthorityAnchor.accepted_history_no_ensemble": "external: accepted no_ensemble history state",
    "S4AcceptedAuthorityAnchor.accepted_history_single_analysis": "external: accepted single_analysis history state",
    "S4AcceptedAuthorityAnchor.accepted_history_multi_analysis": "external: accepted multi_analysis history state",
    "S4AcceptedHistoryState.seq": "external: accepted history sequence",
    "S4AcceptedHistoryState.head": "external: accepted history head (genesis or sha)",
    "S4AcceptedHistoryState.hash": "external: accepted history head entry hash",
    "S4JourneyTargetIdentity.event_ref": "external: accepted journey event identity",
    "S4JourneyTargetIdentity.visit_ref": "external: accepted journey visit identity",
    "S4AcceptedBaselineItem.item_id": "external: accepted baseline item id",
    "S4AcceptedBaselineItem.source_kind": "external: accepted baseline source kind",
    "S4AcceptedBaselineItem.source_locator_ids": "external: accepted baseline source locators",
    "S4AcceptedBaselineItem.source_revision_id": "external: accepted baseline source revision id",
    "S4AcceptedBaselineItem.snapshot_id": "external: accepted baseline snapshot id",
    "S4AcceptedBaselineItem.claimed_identity": "external: accepted baseline claimed identity",
    "S4AcceptedBaselineItem.temporal_window": "external: accepted baseline temporal window",
    "S4AcceptedBaselineItem.claimed_content_hash": "external: accepted baseline content hash (R4 recipe)",
    "S4AcceptedBaselineItem.origin_artifact_hash": "external: accepted baseline origin artifact hash",
    "S4AcceptedBaselineItem.project_ref": "external: accepted baseline project identity",
    "S4AcceptedBaselineItem.run_ref": "external: accepted baseline run identity",
    "S4AcceptedBaselineItem.snapshot_ref": "external: accepted baseline snapshot identity",
    "S4AcceptedBaselineItem.cutoff_ref": "external: accepted baseline cutoff identity (nullable)",
    "S4AcceptedBaselineItem.source_revision": "external: accepted baseline source revision",
    "S4AcceptedQueryDraft.query_draft_id": "external: accepted query draft id",
    "S4AcceptedQueryDraft.risk_ref": "external: accepted query risk ref",
    "S4AcceptedQueryDraft.basis_zh": "external: accepted query basis sentence",
    "S4AcceptedQueryDraft.finding_zh": "external: accepted query finding sentence",
    "S4AcceptedQueryDraft.action_zh": "external: accepted query action sentence",
    "S4AcceptedQueryDraft.source_locator_refs": "external: accepted query source refs",
    "S4AcceptedQueryDraft.pd_wording_state": "external: accepted query PD wording state",
    "S4AcceptedQueryDraft.content_hash": "external: accepted query canonical content hash",
    "S4AcceptedQueryDraft.draft_only": "external: accepted query draft-only flag",
    "S4AcceptedAuthorityAnchor.attempt_authority_rows": "external: accepted per-attempt authority rows",
    "S4AcceptedAuthorityAnchor.model_evidence_permits": "external: accepted ModelEvidence permits",
    "S4AcceptedAuthorityAnchor.risk_priority_authority": "external: accepted per-risk monitoring priority",
    "S4AcceptedAuthorityAnchor.severity_authority": "external: accepted per-risk severity",
    "S4AcceptedAuthorityAnchor.critical_severity_authority": "external: accepted critical severity authority (named deferred contract)",
    "S4AttemptAuthorityRow.attempt_id": "external: accepted attempt identity",
    "S4AttemptAuthorityRow.input_content_hash": "external: accepted attempt input hash",
    "S4AttemptAuthorityRow.artifact_ref": "external: accepted output artifact ref",
    "S4AttemptAuthorityRow.raw_bytes_sha256": "external: accepted raw-byte sha256",
    "S4AttemptAuthorityRow.parsed_output_hash": "external: accepted parsed-output hash",
    "S4AttemptAuthorityRow.date_window": "external: accepted date window",
    "S4AttemptAuthorityRow.unit_contract": "external: accepted unit contract",
    "S4AttemptAuthorityRow.source_revision": "external: accepted source revision",
    "S4AttemptAuthorityRow.rule_id": "external: accepted rule id",
    "S4AttemptAuthorityRow.rule_version": "external: accepted rule version",
    "S4AttemptAuthorityRow.model_id": "external: accepted model id",
    "S4AttemptAuthorityRow.model_version": "external: accepted model version",
    "S4ModelEvidencePermit.model_evidence_id": "external: accepted ModelEvidence id",
    "S4ModelEvidencePermit.role": "external: accepted ModelEvidence role (D10 closed)",
    "S4ModelEvidencePermit.permitted_leaf": "external: accepted permitted leaf",
    "S4ModelEvidencePermit.model_id": "external: accepted model id",
    "S4ModelEvidencePermit.model_version": "external: accepted model version",
    "S4ModelEvidencePermit.output_hash": "external: accepted worker parsed-output hash",
    "S4ModelEvidencePermit.ensemble_id": "external: accepted ensemble identity",
    "S4ModelEvidencePermit.independent_context_hash": "external: accepted independent context hash",
    "S4ModelEvidencePermit.evaluation_content_identity": "external: accepted ModelEvidence evaluation content identity",
    "S4ModelEvidencePermit.input_content_hash": "external: accepted ModelEvidence input content hash",
    "S4ModelEvidencePermit.source_revision_content_pairs": "external: accepted ModelEvidence source revision pairs",
    "S4ModelEvidencePermit.source_refs": "external: accepted ModelEvidence source refs",
    "S4ModelEvidencePermit.ensemble_size": "external: accepted ModelEvidence ensemble size",
    "S4ModelEvidencePermit.member_analysis_refs": "external: accepted ModelEvidence member analysis refs",
    "S4ModelEvidencePermit.member_analysis_ref_set_hash": "external: accepted ModelEvidence member set hash",
    "S4ModelEvidencePermit.output_identity": "external: accepted ModelEvidence output identity",
    "S4ModelEvidencePermit.adjudication_state": "external: accepted ModelEvidence adjudication state (D10 closed)",
    "S4ModelEvidencePermit.model_binding_hash": "external: accepted ModelEvidence binding hash",
    "S4AcceptedRiskIdentity.risk_ref": "external: accepted risk identity ref",
    "S4AcceptedRiskIdentity.risk_identity_hash": "external: accepted risk identity hash",
    "S4AcceptedRiskIdentity.domain": "external: accepted risk domain",
    "S4AcceptedRiskIdentity.domain_zh": "external: accepted risk domain zh (closed projection of domain)",
    "S4AcceptedRiskIdentity.monitoring_priority": "external: accepted per-risk monitoring priority",
    "S4AcceptedRiskIdentity.severity": "external: accepted per-risk severity",
    "S4AcceptedRiskIdentity.severity_zh": "external: accepted per-risk severity zh (closed projection of severity)",
    "S4AcceptedRiskIdentity.change_kind": "external: accepted public change kind instance",
    "S4AcceptedRiskIdentity.change_cause": "external: accepted public change cause instance",
    "S4AcceptedRiskIdentity.project_ref": "external: accepted project identity",
    "S4AcceptedRiskIdentity.run_ref": "external: accepted run identity",
    "S4AcceptedRiskIdentity.snapshot_ref": "external: accepted snapshot identity",
    "S4AcceptedRiskIdentity.cutoff_ref": "external: accepted cutoff identity (nullable)",
    "S4AcceptedRiskIdentity.site_ref": "external: accepted site identity (nullable)",
    "S4AcceptedRiskIdentity.subject_ref": "external: accepted subject identity (nullable)",
    "S4AcceptedRiskIdentity.spine_ref": "external: accepted subject temporal spine identity",
    "S4AcceptedAdjudicatorBinding.binding_id": "external: accepted adjudicator binding identity",
    "S4AcceptedAdjudicatorBinding.session_id": "external: accepted adjudicator session identity",
    "S4AcceptedAdjudicatorBinding.model_id": "external: accepted adjudicator model id",
    "S4AcceptedAdjudicatorBinding.model_version": "external: accepted adjudicator model version",
    "S4AcceptedAdjudicatorBinding.independent_context_hash": "external: accepted adjudicator independence context",
    "S4AcceptedAdjudicatorBinding.outcome": "external: accepted adjudicator outcome (R2 five-state)",
    "S4SourceRevisionPair.revision_id": "external: accepted ModelEvidence source revision id",
    "S4SourceRevisionPair.content_hash": "external: accepted ModelEvidence source revision content hash",
    "S4JourneyTargetIdentity.project_ref": "external: accepted Journey project identity",
    "S4JourneyTargetIdentity.run_ref": "external: accepted Journey run identity",
    "S4JourneyTargetIdentity.snapshot_ref": "external: accepted Journey snapshot identity",
    "S4JourneyTargetIdentity.cutoff_ref": "external: accepted Journey cutoff identity (nullable)",
    "S4JourneyTargetIdentity.site_ref": "external: accepted Journey site identity (nullable)",
    "S4JourneyTargetIdentity.subject_ref": "external: accepted Journey subject identity (nullable)",
    "S4JourneyTargetIdentity.risk_ref": "external: accepted Journey risk identity",
    "S4JourneyTargetIdentity.spine_ref": "external: accepted Journey spine identity",
    "S4JourneyTargetIdentity.anchor_ref": "external: accepted Journey anchor identity",
    "S4JourneyTargetIdentity.source_locator_ref": "external: accepted Journey source locator (nullable)",
}

#: named upstream leaves honestly deferred to later stages (empty path).
DEFERRED_LEAVES: Dict[str, str] = {
    "aemh_match_history": "aemh-match-history-public-v1",
    "subject_temporal_spine_full": "subject-workspace-temporal-spine-v1",
    "critical_severity_authority": "critical-severity-authority-public-v1",
}

#: explicit plane classification by frozen object set (no prefix heuristics).
AUDIENCE_OBJECTS: Tuple[str, ...] = (
    "R5S4AuthorityPacket", "R5S4RiskIdentity", "R5S4BaselineRow",
    "R5S4ConflictRow", "R5S4QueryDraftRow", "R5S4JourneyLink",
    "R5S4AudienceInspector", "R5S4AudienceBaselineRow",
    "R5S4AudienceWorkerSummary",
)
AUDIT_OBJECTS: Tuple[str, ...] = (
    "R5S4WorkerView", "R5S4RawOutputArtifact", "R5S4VerificationRow",
    "R5S4AdjudicationRow", "R5S4HistoryEntry", "R5S4HistoryLog",
    "R5S4AuditInspector", "R5S4AuditWorkerRow",
    "R5S4VerificationAuditRow", "R5S4DigestContextView",
    "R5S4ModelEvidenceRef",
)
AUTHORITY_OBJECTS: Tuple[str, ...] = (
    "S4AcceptedAuthorityAnchor", "S4AttemptAuthorityRow",
    "S4ModelEvidencePermit", "S4JourneyTargetIdentity",
    "S4AcceptedHistoryState", "S4AcceptedBaselineItem",
    "S4AcceptedQueryDraft", "S4AcceptedRiskIdentity",
    "S4AcceptedAdjudicatorBinding", "S4SourceRevisionPair",
)


def _leaf_provenance(obj_name: str) -> str:
    if obj_name in AUDIENCE_OBJECTS:
        return "audience_plane"
    if obj_name in AUDIT_OBJECTS:
        return "audit_plane"
    if obj_name in AUTHORITY_OBJECTS:
        return "authority_plane"
    if obj_name.startswith("import."):
        return "audience_plane"
    raise RuntimeError(f"leaf owner {obj_name!r} not classified to a plane")


def _source_matrix() -> List[Dict[str, Any]]:
    """One row per schema leaf.  Every leaf must be real, derived, synthetic
    or deferred -- an unmapped leaf fails closed (full coverage by design)."""
    schema = build_schema()
    rows: List[Dict[str, Any]] = []
    for leaf in sorted(DEFERRED_LEAVES):
        rows.append(_mapping(leaf, "", "deferred", "deferred",
                             deferred=DEFERRED_LEAVES[leaf]))
    object_names = set(schema["objects"])
    for obj_name, fields in schema["objects"].items():
        for field_name, descriptor in fields.items():
            leaf = f"{obj_name}.{field_name}"
            ftype = descriptor.get("type", "")
            if ftype in object_names or ftype.startswith("import:"):
                continue  # container object / imported object: covered by fields
            if leaf in REAL_LEAF_PATHS:
                path = REAL_LEAF_PATHS[leaf]
                provenance = _leaf_provenance(obj_name)
                if path.startswith("canonical("):
                    rows.append(_mapping(leaf, path, provenance,
                                         "canonical_derived"))
                elif obj_name in ("risk_identity",):
                    rows.append(_mapping(leaf, path, provenance,
                                         _source_kind_for(path)))
                else:
                    rows.append(_mapping(leaf, path, provenance,
                                         "r4_public"))
            elif leaf in AUTHORITY_LEAF_RECIPES:
                rows.append(_mapping(leaf, AUTHORITY_LEAF_RECIPES[leaf],
                                     _leaf_provenance(obj_name),
                                     "external_authority"))
            elif leaf in DERIVED_LEAF_RECIPES:
                rows.append(_mapping(leaf, DERIVED_LEAF_RECIPES[leaf],
                                     _leaf_provenance(obj_name),
                                     "canonical_derived"))
            elif leaf in SYNTHETIC_LEAF_RECIPES:
                rows.append(_mapping(leaf, SYNTHETIC_LEAF_RECIPES[leaf],
                                     _leaf_provenance(obj_name),
                                     "synthetic_offline_test_only"))
            else:
                raise RuntimeError(
                    f"source matrix incomplete: no source for leaf {leaf!r}")
    # Imported real objects: R5AuthorityReceipt + ReferenceBaselineItem leaves.
    receipt_paths = {
        "import.R5AuthorityReceipt.audience_contract_id": "mm_r5.contracts:R5AuthorityReceipt.audience_contract_id",
        "import.R5AuthorityReceipt.cutoff_ref": "mm_r5.contracts:R5AuthorityReceipt.cutoff_ref",
        "import.R5AuthorityReceipt.evaluation_content_identities": "mm_r5.contracts:R5AuthorityReceipt.evaluation_content_identities",
        "import.R5AuthorityReceipt.project_ref": "mm_r5.contracts:R5AuthorityReceipt.project_ref",
        "import.R5AuthorityReceipt.public_projection_content_hash": "mm_r5.contracts:R5AuthorityReceipt.public_projection_content_hash",
        "import.R5AuthorityReceipt.public_projection_id": "mm_r5.contracts:R5AuthorityReceipt.public_projection_id",
        "import.R5AuthorityReceipt.public_projection_kind": "mm_r5.contracts:R5AuthorityReceipt.public_projection_kind",
        "import.R5AuthorityReceipt.run_ref": "mm_r5.contracts:R5AuthorityReceipt.run_ref",
        "import.R5AuthorityReceipt.snapshot_ref": "mm_r5.contracts:R5AuthorityReceipt.snapshot_ref",
        "import.R5AuthorityReceipt.source_revision_content_pairs": "mm_r5.contracts:R5AuthorityReceipt.source_revision_content_pairs",
        "import.R5AuthorityReceipt.visibility_decision_hash": "mm_r5.contracts:R5AuthorityReceipt.visibility_decision_hash",
        "import.R5AuthorityReceipt.visibility_decision_id": "mm_r5.contracts:R5AuthorityReceipt.visibility_decision_id",
    }
    baseline_paths = {
        "import.ReferenceBaselineItem.item_id": "mm_r4.ensemble_contracts:ReferenceBaselineItem.item_id",
        "import.ReferenceBaselineItem.source_kind": "mm_r4.ensemble_contracts:ReferenceBaselineItem.source_kind",
        "import.ReferenceBaselineItem.source_locator_ids": "mm_r4.ensemble_contracts:ReferenceBaselineItem.source_locator_ids",
        "import.ReferenceBaselineItem.source_revision_id": "mm_r4.ensemble_contracts:ReferenceBaselineItem.source_revision_id",
        "import.ReferenceBaselineItem.snapshot_id": "mm_r4.ensemble_contracts:ReferenceBaselineItem.snapshot_id",
        "import.ReferenceBaselineItem.claimed_identity": "mm_r4.ensemble_contracts:ReferenceBaselineItem.claimed_identity",
        "import.ReferenceBaselineItem.temporal_window": "mm_r4.ensemble_contracts:ReferenceBaselineItem.temporal_window",
        "import.ReferenceBaselineItem.claimed_content_hash": "mm_r4.ensemble_contracts:ReferenceBaselineItem.claimed_content_hash",
        "import.ReferenceBaselineItem.origin_artifact_hash": "mm_r4.ensemble_contracts:ReferenceBaselineItem.origin_artifact_hash",
    }
    pair_paths = {
        "import.SourceRevisionContentPair.revision_id": "mm_r5.contracts:SourceRevisionContentPair.revision_id",
        "import.SourceRevisionContentPair.content_hash": "mm_r5.contracts:SourceRevisionContentPair.content_hash",
    }
    for leaf, path in {**receipt_paths, **baseline_paths,
                       **pair_paths}.items():
        rows.append(_mapping(leaf, path, "audience_plane", "r4_public"
                             if path.startswith("mm_r4") else "r5_public"))
    return rows


def _source_kind_for(path: str) -> str:
    if path.startswith("mm_r5.s2_contracts") or path.startswith("mm_r5.contracts"):
        return "r5_public"
    if path.startswith("mm_r4.contracts") or path.startswith("mm_r4.ensemble_contracts"):
        return "r4_public"
    if path.startswith("mm_r4.d10"):
        return "r4_public"
    return "r4_public"


def _join_recipes() -> List[Dict[str, str]]:
    """Unique, resolvable join recipes (no generic 'ensemble provenance')."""
    return [
        {"recipe_id": "join_recipe.worker_view",
         "join": "mm_r4.ensemble:WorkerAnalysisOutput ⋈ mm_r4.ensemble_contracts:AnalysisAttempt on attempt_id",
         "notes": "audit-plane; one worker view per attempt; ordinal 1..N assigned by sorted attempt_id; same model_id on different binding/session is legal"},
        {"recipe_id": "join_recipe.baseline_row",
         "join": "mm_r4.ensemble_contracts:BaselineAssessment ⋈ ReferenceBaselineItem on item_id ⋈ AnalysisAttempt on attempt_id",
         "notes": "item×attempt unique row; confirmed/unsupported require source recheck locators; unassessed item => baseline_miss conflict"},
        {"recipe_id": "join_recipe.conflict_row",
         "join": "semantic re-derivation of mm_r4.ensemble:derive_conflicts over the packet's worker outputs + baseline items",
         "notes": "full set equality (no add/remove); hidden=True rejected for high priority / mutual_negation / baseline_miss"},
        {"recipe_id": "join_recipe.raw_artifact",
         "join": "parsed_output_hash <- mm_r4.ensemble:worker_output_content_hash(recompute); raw_bytes_sha256 <- sha256(base64decode(raw_bytes_b64))",
         "notes": "raw-byte hash and parsed hash are distinct domains; declared_output_hash must equal parsed_output_hash; immutable raw bytes"},
        {"recipe_id": "join_recipe.verification_row",
         "join": "recompute mm_r4.ensemble:verify_attempt(attempt, output, digest_context) - never trust a stored label",
         "notes": "all seven dimensions; passed => no failure codes; failed blocks any supporting adjudication outcome"},
        {"recipe_id": "join_recipe.adjudication_row",
         "join": "mm_r4.ensemble_contracts:AdjudicationBinding + S4-independent_context_hash seal",
         "notes": "binding_id/session_id/independent_context_hash disjoint from every worker; absent adjudicator => present=false"},
        {"recipe_id": "join_recipe.query_draft",
         "join": "mm_r4.d10_projection:D10QueryDraft public three sentences + pd_wording_state",
         "notes": "draft-only; no send/reply/close/todo keys; query_draft_row may be null when no draft"},
        {"recipe_id": "join_recipe.journey_deep_link",
         "join": "mm_r5.contracts:R5DeepLinkState identity fields + unique project/run/snapshot/site/subject/risk projection",
         "notes": "fallback_policy=none; any identity miss => journey_available=false + Chinese repair path; never nearest fallback"},
        {"recipe_id": "join_recipe.severity_from_priority",
         "join": "severity_mapping(R4 monitoring_priority) frozen table: high->high, medium->medium, low->low, unknown->fail_closed",
         "notes": "critical only from explicit R4 critical; S4 never upgrades high to critical"},
        {"recipe_id": "packet_only_provenance",
         "join": "mm_r4.d10_contracts:ModelEvidence (model_evidence_visibility=packet_only)",
         "notes": "ModelEvidence stays audit/packet-only; adjudication_state uses D10 closed enum accepted|divergent|pending; never on audience"},
    ]


def _invariants() -> List[Dict[str, str]]:
    return [
        _invariant("cardinality_0_1_n", "s4.cardinality_not_0_1_n",
                   "ensemble_projection_state and ensemble_size agree: no_ensemble->0 (no attempts/raw/verification, no adjudicator, consensus_zh='尚无独立分析'); single_analysis->1 (consensus forbidden); multi_analysis->>=2"),
        _invariant("same_input_version", "s4.authority_drift",
                   "state != no_ensemble => every attempt shares the same input_content_hash"),
        _invariant("worker_isolation", "s4.duplicate_worker_binding",
                   "for N>=2: len(set(binding_id))==N and len(set(session_id))==N and len(set(independent_context_hash))==N"),
        _invariant("raw_vs_parsed_hash", "s4.raw_parsed_hash_confusion",
                   "raw_bytes_sha256 != parsed_output_hash; sha256(base64decode(raw_bytes_b64))==raw_bytes_sha256; parsed_output_hash==declared_output_hash==recompute(worker_output_content_hash)"),
        _invariant("baseline_recheck", "s4.baseline_recheck_missing",
                   "state in {confirmed, unsupported} => source_recheck_locator_ids non-empty and subset of authorized set; baseline row is item x attempt; unassessed item only appears as baseline_miss, never as 'baseline established'"),
        _invariant("verification_before_adjudication", "s4.verification_label_only",
                   "verification is recomputed before adjudication; result equals R4 verify_attempt recompute; checked_dimensions exactly the seven dimensions; passed carries no failure codes; any failure blocks supporting outcomes"),
        _invariant("conflict_full_set_and_non_hideable", "s4.conflict_set_incomplete",
                   "conflict_rows equal the full semantic re-derivation of derive_conflicts (no add/remove); hidden=True rejected for high priority / mutual_negation / baseline_miss; HIGH single_model_new and mutual negation cannot be hidden by consensus/adjudication; adjudication never deletes a conflict ref"),
        _invariant("adjudicator_independence", "s4.adjudicator_context_collision",
                   "present => binding_id/session_id/independent_context_hash disjoint from every worker; absent => audience shows '尚未独立核对'; outcome uses R2 five-state closed enum; S2 off-enum 'adjudicated' is rejected"),
        _invariant("support_counter_source_resolution", "s4.hidden_source_leak",
                   "support_evidence_refs ∪ counterevidence_refs ∪ source_locator_refs ⊆ projectable locator set; intersection with hidden member/site refs fails closed; unresolved locator shows Chinese repair path with no nearest fallback"),
        _invariant("query_draft_three_part_draft_only", "s4.query_task_semantics",
                   "Query has exactly basis_zh/finding_zh/action_zh; structurural task keys (send_status/reply/closed_at/assignee/todo/unread) forbidden; draft_only always true"),
        _invariant("history_append_only", "s4.history_append_only_violation",
                   "history seq strictly increasing 1..N; entry_hash chains prior_entry_hash; no delete/rewrite/reorder/chain-break"),
        _invariant("journey_fallback_none", "s4.journey_fallback_not_none",
                   "fallback_policy==none; any deep-link identity miss => journey_available=false + Chinese repair path; never nearest subject/site/risk/source"),
        _invariant("audience_audit_split", "s4.audience_audit_leak",
                   "audience_inspector has no audit-only leaf; changing an audit leaf never changes audience_content_hash; forbidden audience tokens absent; ModelEvidence never on audience plane"),
        _invariant("synthetic_offline_test_only", "s4.authority_drift",
                   "authority_mode equals synthetic_offline_test_only; packet cannot grant runtime/real-project/model authority"),
        _invariant("receipt_content_hash_recipe", "s4.receipt_hash_mismatch",
                   "receipt_content_hash is canonical sha256 of the complete R5AuthorityReceipt; authority_receipt_ref == 'receipt:' + receipt_content_hash"),
        _invariant("packet_id_grammar", "s4.packet_id_grammar_mismatch",
                   "packet_id == 'r5-s4-contract:' + audience_content_hash (single colon grammar)"),
        _invariant("hash_dag_acyclic", "s4.hash_recipe_cycle",
                   "packet_integrity_hash excludes packet_id and every hash field it depends on; no self-cycle; audience hash covers audience leaves only"),
        _invariant("enum_closure_source", "s4.enum_value_mismatch",
                   "every imported R4/R2/D10/R5 closed enum is used verbatim; no extension beyond the frozen sets"),
    ]


def build_overlay() -> Dict[str, Any]:
    """Closed enums, source matrix, join recipes, invariants, error codes,
    severity mapping, forbidden tokens and the challenge spec."""
    enums = {
        "ensemble_projection_state": list(ENSEMBLE_PROJECTION_STATES),
        "baseline_state": list(BASELINE_STATES),
        "assessment_reason_code": list(ASSESSMENT_REASON_CODES),
        "recheck_required_state": list(RECHECK_REQUIRED_STATES),
        "verification_dimension": list(VERIFICATION_DIMENSIONS),
        "verification_result": list(VERIFICATION_RESULTS),
        "verification_failure_code": list(VERIFICATION_FAILURE_CODES),
        "conflict_relation": list(CONFLICT_RELATIONS),
        "conflict_display_state": list(CONFLICT_DISPLAY_STATES),
        "non_hideable_relation": list(NON_HIDEABLE_RELATIONS),
        "adjudication_outcome": list(ADJUDICATION_OUTCOMES),
        "attempt_role": list(ATTEMPT_ROLES),
        "raw_output_format": list(RAW_OUTPUT_FORMATS),
        "fallback_policy": list(FALLBACK_POLICIES),
        "pd_wording_state": list(PD_WORDING_STATES),
    "model_evidence_role": list(MODEL_EVIDENCE_ROLES),
    "model_evidence_adjudication_state": list(S2_ADJUDICATION_STATES),
        "monitoring_priority": list(MONITORING_PRIORITIES),
        "severity": list(SEVERITIES),
        "severity_zh": list(SEVERITIES_ZH),
        "domain": list(DOMAINS),
        "change_kind": list(CHANGE_KINDS),
        "change_cause": list(CHANGE_CAUSES),
        "history_entry_kind": list(HISTORY_ENTRY_KINDS),
        "projection_kind": list(PROJECTION_KINDS),
        "severity_source": list(SEVERITY_SOURCES),
        "error_code": list(ERROR_CODES),
    }
    overlay = {
        "schema": OVERLAY_SCHEMA,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "enums": enums,
        "severity_mapping": dict(SEVERITY_MAPPING),
        "severity_zh_by_severity": dict(SEVERITY_ZH_BY_SEVERITY),
        "domain_zh": dict(DOMAIN_ZH),
        "ordinal_zh": list(ORDINAL_ZH),
        "forbidden_audience_tokens": list(FORBIDDEN_AUDIENCE_TOKENS),
        "source_matrix": _source_matrix(),
        "join_recipes": _join_recipes(),
        "invariants": _invariants(),
        "hash_dag": _hash_dag(),
        "packet_id_grammar": "r5-s4-contract:<audience_content_hash>",
        "packet_id_prefix": PACKET_ID_PREFIX,
        "receipt_ref_prefix": RECEIPT_REF_PREFIX,
        "genesis_hash": GENESIS_HASH,
        "test_locator_prefix": TEST_PREFIX,
        "challenge_spec": {
            "total_exact": sum(CHALLENGE_SPEC.values()),
            "categories": dict(CHALLENGE_SPEC),
            "notes": "worker_03 materializes challenge_registry.json with exactly this total (97) one-mutation rows bound to fixed error codes and the test_locator prefix",
        },
        "acceptance_boundary": {
            "acceptance_digest": {
                "owner": "final Codex/reviewer acceptance (NOT generator-owned)",
                "policy": "acceptance creates an external immutable digest pinning the exact human/generator/verifier/artifact/test SHA-256 values; that digest is never authored or re-signable by the generator; later joint re-signing invalidates acceptance",
            },
            "codex_and_reviewer_own": ["ACCEPT_R5_S4_CONTRACT", "ACCEPT_R5_S4"],
            "must_not_claim": [
                "ACCEPT_R5_S4_CONTRACT", "ACCEPT_R5_S4", "runtime_completion",
                "S5+_acceptance",
            ],
        },
        "done_gates": {
            "0_1_n": "state/size agree; no_ensemble empty; single consensus forbidden",
            "worker_isolation": "N>=2 distinct binding/session/context",
            "baseline_recheck": "confirmed/unsupported require source recheck locators",
            "raw_immutable": "raw_bytes_sha256 != parsed_output_hash; raw bytes immutable",
            "seven_dimension": "verification recomputes all seven dimensions before adjudication",
            "conflict_non_hideable": "full conflict set visible; high/mutual/baseline/single never hidden",
            "adjudicator_independent": "disjoint binding/session/context; adds explanation only",
            "query_draft_only": "exact three-part draft-only Query; no send/reply/close/todo",
            "history_append_only": "append-only chained history",
            "journey_fallback_none": "fallback_policy=none; fail-closed on identity miss",
            "audience_audit_split": "audience/audit hash split; no audit leaf on audience",
            "support_counter_source": "support/counter/source resolve within projectable set",
        },
    }
    _validate_built_overlay(overlay)
    return overlay


def _validate_built_overlay(overlay: Dict[str, Any]) -> None:
    # Enums closed and unique within each vocabulary.
    for name, values in overlay["enums"].items():
        if isinstance(values, list) and values:
            if len(set(values)) != len(values):
                raise RuntimeError(f"overlay enum {name!r} has duplicates")
    # Error codes unique and prefixed s4.
    codes = overlay["enums"]["error_code"]
    if len(set(codes)) != len(codes):
        raise RuntimeError("error_code catalog has duplicates")
    for code in codes:
        if not code.startswith("s4."):
            raise RuntimeError(f"error code not s4.* prefixed: {code}")
    # Challenge spec total is exactly 97.
    spec = overlay["challenge_spec"]
    if spec["total_exact"] != sum(spec["categories"].values()):
        raise RuntimeError("challenge_spec total_exact inconsistent")
    if spec["total_exact"] != 97:
        raise RuntimeError(f"challenge_spec must total exactly 97, got {spec['total_exact']}")
    # Source matrix: deferred rows must have non-empty deferred_contract names.
    for row in overlay["source_matrix"]:
        if row["source_kind"] == "deferred" and not row.get("deferred_contract"):
            raise RuntimeError("deferred source leaf requires a named deferred contract")
    # Invariant error codes must exist in the catalog.
    catalog = set(codes)
    for inv in overlay["invariants"]:
        if inv["error_code"] not in catalog:
            raise RuntimeError(
                f"invariant {inv['invariant_id']} references unknown error "
                f"code {inv['error_code']}")
    # Domain/severity zh maps fully cover the closed enums.
    if set(overlay["severity_zh_by_severity"]) != set(SEVERITIES):
        raise RuntimeError("severity_zh_by_severity must cover severity enum")
    if set(overlay["domain_zh"]) != set(DOMAINS):
        raise RuntimeError("domain_zh must cover domain enum")
    if set(overlay["severity_mapping"]) != set(MONITORING_PRIORITIES):
        raise RuntimeError("severity_mapping must cover monitoring_priority enum")


# ---------------------------------------------------------------------------
# source_pins.json
# ---------------------------------------------------------------------------


def _source_group(path: str) -> str:
    if "implementation_contract_v0_1_20260819" in path:
        return "r5_s4_human_contract"
    if "exact_contract.json" in path or "stage_contract_v0_3" in path:
        return "accepted_s0"
    if "acceptance_record" in path:
        return "accepted_r5"
    if path.startswith("runs/conference/medical_monitoring_r5_s4_20260819/"):
        return "conference_evidence"
    if "medical_monitoring_r5_s4_20260819" in path and ("context" in path or "plan" in path):
        return "task_context"
    if path.startswith("poc/medical_monitoring_ai_native_r4/"):
        return "accepted_r4_public_authority"
    if path.startswith("poc/medical_monitoring_ai_native_r5/"):
        return "accepted_r5_surface"
    if path.startswith("poc/medical_monitoring_ai_native_r2/"):
        return "accepted_r2_public_authority"
    if "tools/" in path:
        return "generator_verifier"
    if "system_design_v1" in path or "implementation_plan_v1" in path:
        return "design_authority"
    return "misc"


#: (path, optional) -- optional entries are pinned only when present so the
#: generator stays byte-deterministic across W1 (verifier/test absent) and
#: W2/W3 (verifier/test present).  Re-run after adding them.
SOURCE_PATHS: List[Tuple[str, bool]] = [
    ("reviews/medical_monitoring_r5_s4_implementation_contract_v0_1_20260819.md", False),
    ("reviews/medical_monitoring_ai_native_system_design_v1_20260809.md", False),
    ("reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md", False),
    ("reviews/medical_monitoring_r5_s3_implementation_contract_v0_2_20260818.md", False),
    ("artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json", False),
    ("context/medical_monitoring_ai_native_implementation_plan_v1_20260809.md", False),
    ("context/medical_monitoring_r5_s4_20260819_conference_context.md", False),
    ("context/medical_monitoring_r5_s4_contract_20260819_execution_context.md", False),
    ("context/medical_monitoring_r5_contract_acceptance_record_20260818.md", False),
    ("context/medical_monitoring_r5_s2_acceptance_record_20260818.md", False),
    ("context/medical_monitoring_r5_s3_contract_acceptance_record_20260819.md", False),
    ("context/medical_monitoring_r5_s3_acceptance_record_20260819.md", False),
    ("runs/conference/medical_monitoring_r5_s4_20260819/general_grok46.md", False),
    ("runs/conference/medical_monitoring_r5_s4_20260819/general_pi_qwen38_fallback_codex_luna.md", False),
    ("plans/codex_execution_medical_monitoring_r5_s4_contract_20260819.md", False),
    ("poc/medical_monitoring_ai_native_r4/src/mm_r4/ensemble_contracts.py", False),
    ("poc/medical_monitoring_ai_native_r4/src/mm_r4/ensemble.py", False),
    ("poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_contracts.py", False),
    ("poc/medical_monitoring_ai_native_r4/src/mm_r4/d10_projection.py", False),
    ("poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py", False),
    ("poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py", False),
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py", False),
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/canonical.py", False),
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/authority_adapter.py", False),
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_contracts.py", False),
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_authority_builder.py", False),
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_thin_slice.py", False),
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/s3_contracts.py", False),
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/s3_authority_builder.py", False),
    ("poc/medical_monitoring_ai_native_r5/src/mm_r5/s3_projection.py", False),
    ("artifacts/medical_monitoring_r5_s3_contract_v0_2/manifest.json", False),
    ("tools/generate_medical_monitoring_r5_s4_contract_v0_1.py", False),
    ("tools/verify_medical_monitoring_r5_s4_contract_v0_1.py", True),
    ("poc/medical_monitoring_ai_native_r5/tests/test_s4_contract_artifacts.py", True),
]


def build_source_pins() -> Dict[str, Any]:
    pins: List[Dict[str, Any]] = []
    missing_required: List[str] = []
    for path, optional in SOURCE_PATHS:
        target = ROOT / path
        if not target.exists() or not target.is_file():
            if optional:
                continue
            missing_required.append(path)
            continue
        pins.append({
            "path": path,
            "group": _source_group(path),
            "sha256": sha256_file(target),
        })
    if missing_required:
        raise RuntimeError(
            "pinned source missing: " + ", ".join(sorted(missing_required)))
    pins.sort(key=lambda p: p["path"])
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
                   source_pins_bytes: bytes) -> Dict[str, Any]:
    artifact_paths = [
        ("reviews/medical_monitoring_r5_s4_implementation_contract_v0_1_20260819.md", "human_contract", "raw_sha256", None),
        ("tools/generate_medical_monitoring_r5_s4_contract_v0_1.py", "generator", "raw_sha256", None),
        ("tools/verify_medical_monitoring_r5_s4_contract_v0_1.py", "verifier", "raw_sha256", None),
        ("artifacts/medical_monitoring_r5_s4_contract_v0_1/exact_overlay.json", "exact_overlay", "raw_sha256", overlay_bytes),
        ("artifacts/medical_monitoring_r5_s4_contract_v0_1/packet_schema.json", "packet_schema", "raw_sha256", schema_bytes),
        ("artifacts/medical_monitoring_r5_s4_contract_v0_1/source_pins.json", "source_pins", "raw_sha256", source_pins_bytes),
        ("artifacts/medical_monitoring_r5_s4_contract_v0_1/manifest.json", "manifest", "canonical_self", None),
        ("artifacts/medical_monitoring_r5_s4_contract_v0_1/challenge_registry.json", "challenge_registry", "raw_sha256", None),
    ]
    artifacts: List[Dict[str, Any]] = []
    planned: List[Dict[str, Any]] = []
    for path, role, kind, payload in artifact_paths:
        target = ROOT / path
        if target.exists() and target.is_file():
            if kind == "canonical_self":
                artifacts.append({"path": path, "role": role,
                                  "hash_kind": "canonical_self", "sha256": None})
            elif payload is not None:
                artifacts.append({"path": path, "role": role,
                                  "hash_kind": kind,
                                  "sha256": sha256_bytes(payload)})
            else:
                artifacts.append({"path": path, "role": role,
                                  "hash_kind": kind,
                                  "sha256": sha256_file(target)})
        else:
            planned.append({"path": path, "role": role,
                            "planned_by": _planned_by(role)})
    sources = [
        {"path": item["path"], "group": item["group"], "sha256": item["sha256"]}
        for item in json.loads(source_pins_bytes)["sources"]
    ]
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "status": STATUS,
        "authority_mode": AUTHORITY_MODE,
        "artifact_count": len(artifacts),
        "planned_artifact_count": len(planned),
        "source_count": len(sources),
        "artifacts": artifacts,
        "planned_artifacts": planned,
        "pinned_sources": sources,
        "manifest_content_sha256": "",
    }
    manifest["manifest_content_sha256"] = _manifest_content_hash(manifest)
    return manifest


def _planned_by(role: str) -> str:
    if role == "verifier":
        return "worker_02"
    if role == "challenge_registry":
        return "worker_03"
    if role == "test":
        return "worker_03"
    return "pending"


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
    source_pins_bytes = canonical_bytes(build_source_pins())
    manifest_bytes = canonical_bytes(build_manifest(
        overlay_bytes, schema_bytes, source_pins_bytes))
    return {
        artifact_dir / "exact_overlay.json": overlay_bytes,
        artifact_dir / "packet_schema.json": schema_bytes,
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
    if str(artifact_dir).endswith("medical_monitoring_r5_s4_contract_v0_1"):
        artifact_dir = root / "artifacts" / "medical_monitoring_r5_s4_contract_v0_1"
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
