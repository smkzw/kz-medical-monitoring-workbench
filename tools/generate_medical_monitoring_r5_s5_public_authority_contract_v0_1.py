#!/usr/bin/env python3
"""Generate the R5-S5 public-authority contract artifact set.

This generator is intentionally contract-only.  It does not import or create a
public-authority producer, adapter, validator runtime, or any R5-S5 runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
REVIEW_PATH = ROOT / "reviews/medical_monitoring_r5_s5_public_authority_contract_v0_1_20260819.md"
GENERATOR_PATH = ROOT / "tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py"
VERIFIER_PATH = ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py"
PARENT_CONTRACT_PATH = ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json"

CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-contract-v0.1"
SCHEMA_VERSION = "2026-08-19.1"
SUBJECT_CONTRACT_ID = "subject-temporal-public-v1"
AEMH_CONTRACT_ID = "aemh-match-history-public-v1"
PARENT_R5_AUDIENCE_CONTRACT_ID = "contract.s4.1"

SOURCE_PINS = {
    "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json": "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949",
    "context/medical_monitoring_r5_s4_acceptance_record_20260819.md": "1d17297c44b371aefecf28cfc2388181b7be35d9e5cc830b148a0b3a9da1971e",
    "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py": "039f197ff01f4d689db01327bf08ef917551c06105d1907eaa920c9bdb5b01dc",
    "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py": "0fc533f88a2fcf65f0574af13c0c44b76103c2cf399be953c66e4060c3f519a8",
    "poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py": "25c6b7cc8932cdf3c28a245679449c8c35b2653492f8fa2a7b75516f8fbc0f8b",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py": "993d6bea9b10842aa13f8226847961ff3881689a34797c8fdb9d68ac1aa6e5c4",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py": "7cfe74ba4ee2334709945309f568d39314f6a5b95935f3edfbd335f1e690aaed",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py": "83651868390e65eb4d3e6af14225f0384dad09804f1f7208230c1c5e330cd53d",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/d07_journey.py": "7c4f576b62fea6eb8b538680b3a3aba24d919dfc5b359c84db65a3bb4e842fce",
    "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py": "8d8fb6727a878642b361b444edb110b7283ef11b41adc1cb3c561152699225ad",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py": "e9b78e90af77ce3a34616865e692f8aeec82b624f044443cc826b623e611b2b0",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/authority_adapter.py": "fe24e69cbbce0d46d20615ac5d4819ad38f9383b76d277bf139a1d71e88035e7",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s2_authority_builder.py": "6c8a18bdbc31af57a9086e0366f0e387d06ef2732ffe62a90432698d809793c7",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py": "0ea6de7495c9226007308752df69ec3c21ac3f1b23891ef44ca1e1b0e37d58d3",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_authority_builder.py": "af98919b5806ebe0123290091a8b73026d7cca30730c1117d5f3d5bb6c5d2396",
}

PROTECTED_ACCEPTED_PINS = {
    "r5_root_init_sha256": "0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd",
    "accepted_r4_r5_s4_readonly_manifest_sha256": "53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822",
    "accepted_r5_v0_3_exact_contract_sha256": SOURCE_PINS[
        "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json"
    ],
    "s4_acceptance_record_sha256": SOURCE_PINS[
        "context/medical_monitoring_r5_s4_acceptance_record_20260819.md"
    ],
    "medical_writing_protected_inventory_sha256": "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca",
    "medical_writing_protected_file_count": 542,
    "protected_path_sha256": {
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py": "0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd",
        "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json": "53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822",
        "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json": SOURCE_PINS[
            "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json"
        ],
        "context/medical_monitoring_r5_s4_acceptance_record_20260819.md": SOURCE_PINS[
            "context/medical_monitoring_r5_s4_acceptance_record_20260819.md"
        ],
    },
    "medical_writing_inventory_contract": {
        "roots": ["deploy", "frontend", "packages", "runtime", "services"],
        "relative_path_regex": "medical[-_]writing",
        "file_kind": "regular_file_following_task_scoped_symlink_resolution",
        "sort": "UTF-8 relative POSIX path byte order",
        "per_file_sha256": "lowercase sha256(file bytes)",
        "aggregate_recipe": "sha256(concat(relative_path_utf8 + NUL + lowercase_file_sha256_ascii + LF))",
        "privacy_boundary": "enumerate paths under the five protected roots; read bytes only for matched regular files",
    },
}

NO_RUNTIME_TEST_SURFACE = {
    "scan_roots": [
        "poc/medical_monitoring_ai_native_r5/src/mm_r5",
        "poc/medical_monitoring_ai_native_r5/tests",
    ],
    "forbidden_exact_paths": [
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_authority_builder.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_contracts.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_projection.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py",
        "poc/medical_monitoring_ai_native_r5/tests/s5_runtime_fixtures.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_s5_contracts.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_s5_projection.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py",
    ],
    "forbidden_relative_path_regexes": [
        "^poc/medical_monitoring_ai_native_r5/src/mm_r5/(?:subject_temporal_public|aemh_match_history_public|s5_[^/]+)(?:\\.py|\\.pyc|\\.pyo|/.*|$)$",
        "^poc/medical_monitoring_ai_native_r5/tests/(?:.*/)?(?:test_)?(?:subject_temporal_public|aemh_match_history_public|s5_[^/]+)(?:\\.py|\\.pyc|\\.pyo|/.*|$)$",
    ],
    "file_surface_rule": "fail closed if any regular file or symlink matches an exact path or regex; scan names only and do not read file content",
}

DOMAINS = [
    "ae",
    "mh",
    "cm",
    "ip",
    "lab_exam",
    "hospital_procedure",
    "symptom_efficacy",
    "protocol_compliance",
]

COMMON_ENUMS = {
    "receipt_variant": ["subject_temporal", "aemh_match_history"],
    "source_locator_variant": ["r4_source_locator", "d08_source_locator"],
    "visibility_state": ["projectable", "hidden", "not_evaluable"],
    "cutoff_state": ["present", "absent"],
    "fallback_policy": ["fail_closed_no_nearest"],
    "cutoff_endpoint_state": ["present", "absent"],
}

TEMPORAL_ENUMS = {
    **COMMON_ENUMS,
    "axis_mode": ["calendar", "study_day"],
    "date_state": ["exact", "partial", "conflicted", "missing"],
    "date_geometry": ["point", "closed_interval", "open_start", "open_end"],
    "visit_kind": ["nominal", "actual", "unscheduled"],
    "domain": DOMAINS,
    "applicability_state": ["applicable", "not_applicable", "not_provided"],
    "severity": ["critical", "high", "medium", "low"],
    "pending_item_kind": ["visit", "event", "risk", "phase"],
    "journey_subtype": [
        "ae",
        "mh",
        "concomitant_medication",
        "ip_dose",
        "ip_pause",
        "ip_resume",
        "lab",
        "exam",
        "hospitalization",
        "procedure",
        "symptom",
        "efficacy",
        "scale",
        "outcome",
        "trend",
        "protocol_deviation",
    ],
}

AEMH_ENUMS = {
    **COMMON_ENUMS,
    "aemh_domain": ["ae", "mh"],
    "history_event_kind": [
        "reminder_created",
        "match_decided",
        "withdrawn",
        "reappeared",
    ],
    "match_state": ["exact", "ambiguous", "rejected"],
    "risk_lifecycle_effect": ["none"],
    "identity_evidence_kind": ["candidate", "later_fact", "considered_fact"],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def pretty_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
        "utf-8"
    )


def field(type_name: str, *, nullable: bool = False, many: bool = False) -> dict[str, Any]:
    return {
        "type": type_name,
        "cardinality": "many" if many else "one",
        "nullable": nullable,
    }


def seal(value: dict[str, Any], hash_field: str = "content_hash") -> dict[str, Any]:
    sealed = dict(value)
    sealed[hash_field] = canonical_hash(value)
    return sealed


COMMON_OBJECTS = {
    "PublicScopeIdentity": {
        "project_ref": field("string"),
        "run_ref": field("string"),
        "snapshot_ref": field("string"),
        "cutoff_state": field("enum:cutoff_state"),
        "cutoff_ref": field("string", nullable=True),
        "site_ref": field("string"),
        "subject_ref": field("string"),
        "spine_ref": field("string"),
        "identity_content_hash": field("sha256"),
    },
    "PublicSourceLocator": {
        "locator_ref": field("string"),
        "locator_variant": field("enum:source_locator_variant"),
        "snapshot_ref": field("string"),
        "source_revision_ref": field("string"),
        "source_revision_content_hash": field("sha256"),
        "source_file_ref": field("string", nullable=True),
        "table_semantic": field("string", nullable=True),
        "record_ref": field("string"),
        "authority_entity_kind": field("string", nullable=True),
        "authority_entity_ref": field("string", nullable=True),
        "column_or_anchor": field("string"),
        "canonical_location": field("string", nullable=True),
        "raw_payload_hash": field("sha256"),
        "locator_content_hash": field("sha256"),
    },
    "SourceRevisionContentPair": {
        "revision_id": field("string"),
        "accepted_content_hash": field("sha256"),
        "locator_refs": field("string", many=True),
        "pair_content_hash": field("sha256"),
    },
    "VisibilityClosure": {
        "visibility_decision_id": field("string"),
        "visibility_decision_hash": field("sha256"),
        "evaluation_member_refs": field("string", many=True),
        "evaluation_site_refs": field("string", many=True),
        "projectable_member_refs": field("string", many=True),
        "projectable_site_refs": field("string", many=True),
        "hidden_member_refs": field("string", many=True),
        "hidden_site_refs": field("string", many=True),
        "hidden_member_count": field("integer"),
        "hidden_site_count": field("integer"),
        "subject_visibility_state": field("enum:visibility_state"),
        "deep_link_eligible": field("boolean"),
        "closure_content_hash": field("sha256"),
    },
    "PublicCutoffEndpoint": {
        "state": field("enum:cutoff_endpoint_state"),
        "exact_date": field("date", nullable=True),
        "source_locator_refs": field("string", many=True),
        "cutoff_content_hash": field("sha256"),
    },
    "PublicAuthorityReceipt": {
        "receipt_id": field("string"),
        "receipt_variant": field("enum:receipt_variant"),
        "authority_contract_id": field("string"),
        "authority_contract_version": field("string"),
        "scope_identity": field("PublicScopeIdentity"),
        "public_projection_id": field("string"),
        "public_projection_content_hash": field("sha256"),
        "evaluation_content_identities": field("sha256", many=True),
        "visibility_closure": field("VisibilityClosure"),
        "source_revision_content_pairs": field("SourceRevisionContentPair", many=True),
        "audience_contract_id": field("string"),
        "receipt_content_hash": field("sha256"),
    },
}


def subject_schema() -> dict[str, Any]:
    objects = {
        **COMMON_OBJECTS,
        "TemporalDateEndpoint": {
            "state": field("enum:date_state"),
            "exact_date": field("date", nullable=True),
            "range_start": field("date", nullable=True),
            "range_end": field("date", nullable=True),
            "candidate_values": field("partial_date", many=True),
            "source_locator_refs": field("string", many=True),
            "main_axis_projectable": field("boolean"),
            "range_projection_authorized": field("boolean"),
            "study_day": field("integer", nullable=True),
            "endpoint_content_hash": field("sha256"),
        },
        "TemporalAxisBasis": {
            "axis_ref": field("string"),
            "default_axis_mode": field("enum:axis_mode"),
            "timezone": field("string"),
            "study_day_anchor_event_ref": field("string", nullable=True),
            "study_day_zero_exists": field("boolean", nullable=True),
            "cutoff_endpoint": field("TemporalDateEndpoint"),
            "source_locator_refs": field("string", many=True),
            "axis_content_hash": field("sha256"),
        },
        "TemporalVisit": {
            "visit_ref": field("string"),
            "visit_kind": field("enum:visit_kind"),
            "planned_visit_ref": field("string", nullable=True),
            "actual_encounter_ref": field("string", nullable=True),
            "accepted_assignment_ref": field("string", nullable=True),
            "phase_ref": field("string", nullable=True),
            "nominal_endpoint": field("TemporalDateEndpoint", nullable=True),
            "actual_endpoint": field("TemporalDateEndpoint", nullable=True),
            "source_locator_refs": field("string", many=True),
            "visit_content_hash": field("sha256"),
        },
        "TemporalEvent": {
            "event_ref": field("string"),
            "event_content_identity": field("sha256"),
            "domain": field("enum:domain"),
            "subtype": field("enum:journey_subtype"),
            "applicability_state": field("enum:applicability_state"),
            "visit_ref": field("string", nullable=True),
            "geometry": field("enum:date_geometry"),
            "start_endpoint": field("TemporalDateEndpoint"),
            "end_endpoint": field("TemporalDateEndpoint"),
            "risk_anchor_refs": field("string", many=True),
            "source_locator_refs": field("string", many=True),
            "event_content_hash": field("sha256"),
        },
        "TemporalRiskAnchor": {
            "risk_anchor_ref": field("string"),
            "risk_ref": field("string"),
            "risk_content_identity": field("sha256"),
            "domain": field("enum:domain"),
            "severity": field("enum:severity"),
            "risk_type_zh": field("string"),
            "event_ref": field("string", nullable=True),
            "visit_ref": field("string", nullable=True),
            "geometry": field("enum:date_geometry"),
            "start_endpoint": field("TemporalDateEndpoint"),
            "end_endpoint": field("TemporalDateEndpoint"),
            "source_locator_refs": field("string", many=True),
            "risk_anchor_content_hash": field("sha256"),
        },
        "TemporalPendingDateItem": {
            "pending_ref": field("string"),
            "item_kind": field("enum:pending_item_kind"),
            "item_ref": field("string"),
            "target_content_hash": field("sha256"),
            "domain": field("enum:domain", nullable=True),
            "start_endpoint": field("TemporalDateEndpoint"),
            "end_endpoint": field("TemporalDateEndpoint"),
            "source_locator_refs": field("string", many=True),
            "pending_content_hash": field("sha256"),
        },
        "TemporalPhaseBand": {
            "phase_ref": field("string"),
            "phase_label_zh": field("string"),
            "geometry": field("enum:date_geometry"),
            "start_endpoint": field("TemporalDateEndpoint"),
            "end_endpoint": field("TemporalDateEndpoint"),
            "source_locator_refs": field("string", many=True),
            "phase_content_hash": field("sha256"),
        },
        "TemporalDomainTrack": {
            "domain": field("enum:domain"),
            "applicability_state": field("enum:applicability_state"),
            "event_refs": field("string", many=True),
            "risk_anchor_refs": field("string", many=True),
            "track_content_hash": field("sha256"),
        },
        "TemporalMembershipIndex": {
            "visit_refs": field("string", many=True),
            "event_refs": field("string", many=True),
            "risk_anchor_refs": field("string", many=True),
            "pending_date_refs": field("string", many=True),
            "phase_refs": field("string", many=True),
            "source_locator_refs": field("string", many=True),
            "membership_content_hash": field("sha256"),
        },
        "SubjectTemporalPublicProjection": {
            "contract_id": field("string"),
            "schema_version": field("string"),
            "projection_id": field("string"),
            "receipt_ref": field("string"),
            "scope_identity": field("PublicScopeIdentity"),
            "fallback_policy": field("enum:fallback_policy"),
            "axis_basis": field("TemporalAxisBasis"),
            "visits": field("TemporalVisit", many=True),
            "events": field("TemporalEvent", many=True),
            "risk_anchors": field("TemporalRiskAnchor", many=True),
            "pending_date_items": field("TemporalPendingDateItem", many=True),
            "phase_bands": field("TemporalPhaseBand", many=True),
            "domain_tracks": field("TemporalDomainTrack", many=True),
            "source_locators": field("PublicSourceLocator", many=True),
            "membership_index": field("TemporalMembershipIndex"),
            "projection_content_hash": field("sha256"),
        },
        "SubjectTemporalAuthorityPacket": {
            "receipt": field("PublicAuthorityReceipt"),
            "projection": field("SubjectTemporalPublicProjection"),
            "packet_content_hash": field("sha256"),
        },
    }
    return {
        "schema": "subject-temporal-public-v1-exact-schema",
        "schema_version": SCHEMA_VERSION,
        "exact_object_keys": True,
        "enums": TEMPORAL_ENUMS,
        "objects": objects,
        "hash_recipes": {
            "canonical_json": "UTF-8 JSON; object keys sorted; no insignificant whitespace; arrays preserve declared semantic order; strings are not Unicode-normalized by the contract layer",
            "object_content_hash": "sha256(canonical_json(all exact object fields except that object's *_content_hash field))",
            "set_like_arrays": "every visibility/source/evaluation/candidate/locator/member/reference collection is sorted unique; object arrays sort by stable ref, domain_tracks use closed domain enum order, and duplicates fail closed before hashing",
            "projection_id": "sha256(canonical_json({contract_id,schema_version,scope_identity.identity_content_hash,membership_index.membership_content_hash,axis_basis.axis_content_hash}))",
            "receipt_id": "sha256(canonical_json({receipt_variant,authority_contract_id,scope_identity.identity_content_hash,public_projection_id}))",
            "packet_content_hash": "sha256(canonical_json({receipt_content_hash,projection_content_hash}))",
        },
        "invariants": [
            "receipt_variant=subject_temporal and authority_contract_id=subject-temporal-public-v1",
            "receipt, projection, visibility and every member join the same project/run/snapshot/cutoff/site/subject/spine identity",
            "projection.schema_version and receipt.authority_contract_version equal this schema.schema_version exactly; receipt.audience_contract_id equals the pinned parent R5 audience contract constant contract.s4.1",
            "subject and site must each be evaluation/projectable members, must not be hidden, and subject must be deep-link eligible",
            "visibility evaluation/projectable/hidden member and site sets equal the exact in-scope singleton subject/site universes, are sorted unique, and contain no foreign refs",
            "each source locator snapshot equals scope snapshot and resolves through a sorted-unique exact total partition to one nonempty source-revision pair whose accepted content hash equals locator.source_revision_content_hash; unused pairs are forbidden",
            "evaluation_content_identities equal the complete deterministic set of projection, scope, membership, axis, member, locator and accepted source content identities",
            "cutoff_state=absent iff cutoff_ref is null and axis cutoff endpoint is missing, nonprojectable and date/study-day empty; present requires exact projectable equality",
            "calendar is the default axis; every cutoff/visit/event/risk/phase/pending endpoint is scanned and any study_day value or study_day axis requires one exact projectable accepted anchor event in the same membership spine",
            "study day is derived only from the accepted anchor calendar date: anchor study_day=0 selects day-zero mode with day=calendar_delta; anchor study_day=1 selects no-day-zero mode with day=calendar_delta+1 for delta>=0 and day=calendar_delta for delta<0; anchor values other than 0/1 and every inconsistent endpoint value fail closed",
            "study_day_zero_exists is not self-reported: it is null without a study-day anchor and otherwise equals whether the accepted anchor endpoint carries study_day=0",
            "start and end date states are independent; partial/conflicted candidates are real dates or partial dates, sorted unique, each expands inside the range, and the range equals their exact envelope; main_axis_projectable equals valid bounded range and range_projection_authorized",
            "identical nonmissing endpoints require point geometry; closed_interval requires distinct chronologically ordered endpoints",
            "missing endpoints are not main-axis projectable; affected objects are present in pending_date_items",
            "pending items mirror target endpoints/domain/source content exactly and form a one-to-one exact set for every missing or nonprojectable visit/event/risk/phase with no extras",
            "point, closed_interval, open_start and open_end geometry agree exactly with endpoint states",
            "unscheduled visits require an actual encounter, forbid a planned visit and accepted assignment, and are never snapped to a nominal visit",
            "between-visit events retain actual chronology and nullable visit_ref; nearest fallback is forbidden",
            "domain tracks cover exactly eight domains once each; unknown and OTHER are forbidden",
            "domain applicability is exact: applicable iff that domain emits at least one event or risk member; not_applicable and not_provided remain distinct, require empty refs, and cannot coexist with emitted members",
            "every emitted event has applicability_state=applicable and its domain track is applicable; event-level not_applicable/not_provided is representable only by absence from emitted event/risk membership and empty refs on the corresponding domain track",
            "critical/high/medium/low is copied from accepted authority; high is never promoted to critical",
            "membership_index equals the exact set of emitted visits/events/risks/pending/phases/locators",
            "every source locator is consumed by an actual axis/member/endpoint; receipt, source-pair, membership or evaluation identity references alone do not justify an otherwise unused locator",
        ],
        "error_codes": [
            "PUB_SCHEMA_EXACT_KEYS",
            "PUB_TYPE_BOOL_REQUIRED",
            "PUB_TYPE_MISMATCH",
            "PUB_ENUM_UNKNOWN",
            "PUB_DUPLICATE_REF",
            "PUB_HASH_MISMATCH",
            "PUB_IDENTITY_PROJECT_MISMATCH",
            "PUB_IDENTITY_RUN_MISMATCH",
            "PUB_IDENTITY_SNAPSHOT_MISMATCH",
            "PUB_IDENTITY_CUTOFF_MISMATCH",
            "PUB_IDENTITY_SITE_MISMATCH",
            "PUB_IDENTITY_SUBJECT_MISMATCH",
            "PUB_IDENTITY_SPINE_MISMATCH",
            "PUB_CONTRACT_VERSION_MISMATCH",
            "PUB_AUDIENCE_CONTRACT_MISMATCH",
            "PUB_VISIBILITY_NOT_PROJECTABLE",
            "PUB_VISIBILITY_DEEP_LINK_INELIGIBLE",
            "PUB_VISIBILITY_SCOPE_MISMATCH",
            "PUB_SET_ORDER_OR_DUPLICATE",
            "PUB_SOURCE_REVISION_UNRESOLVED",
            "PUB_SOURCE_PARTITION_MISMATCH",
            "PUB_SOURCE_CONTENT_MISMATCH",
            "PUB_LOCATOR_SNAPSHOT_MISMATCH",
            "PUB_SOURCE_LOCATOR_UNRESOLVED",
            "PUB_SOURCE_LOCATOR_UNUSED",
            "PUB_EVALUATION_IDENTITY_MISMATCH",
            "PUB_CUTOFF_STATE_MISMATCH",
            "PUB_DATE_INVALID",
            "PUB_DATE_RANGE_ORDER",
            "PUB_DATE_CANDIDATE_RANGE_MISMATCH",
            "PUB_INTERVAL_ORDER",
            "PUB_DATE_GEOMETRY_DEGENERATE",
            "PUB_DATE_PROJECTABILITY_MISMATCH",
            "PUB_DATE_STATE_INVALID",
            "PUB_DATE_GEOMETRY_INVALID",
            "PUB_DATE_FABRICATION_FORBIDDEN",
            "PUB_STUDY_DAY_ANCHOR_MISSING",
            "PUB_STUDY_DAY_VALUE_MISMATCH",
            "PUB_UNSCHEDULED_PLANNED_BINDING_FORBIDDEN",
            "PUB_NEAREST_FALLBACK_FORBIDDEN",
            "PUB_DOMAIN_UNKNOWN",
            "PUB_DOMAIN_APPLICABILITY_MISMATCH",
            "PUB_MEMBERSHIP_MISMATCH",
            "PUB_REFERENCE_UNRESOLVED",
            "PUB_REFERENCE_DOMAIN_MISMATCH",
            "PUB_REFERENCE_PHASE_MISMATCH",
            "PUB_PENDING_MIRROR_MISMATCH",
            "PUB_PENDING_COVERAGE_MISMATCH",
            "PUB_OVERLAY_ARTIFACT_MISMATCH",
            "PUB_SOURCE_MATRIX_ARTIFACT_MISMATCH",
            "PUB_MANIFEST_CONTRACT_MISMATCH",
            "PUB_MANIFEST_PROTECTED_PIN_MISMATCH",
            "PUB_RUNTIME_TEST_SURFACE_FORBIDDEN",
        ],
    }


def aemh_schema() -> dict[str, Any]:
    objects = {
        **COMMON_OBJECTS,
        "AEMHIdentityEvidence": {
            "evidence_ref": field("string"),
            "evidence_kind": field("enum:identity_evidence_kind"),
            "entity_ref": field("string"),
            "entity_content_identity": field("sha256"),
            "source_locator_ref": field("string"),
            "source_locator_content_hash": field("sha256"),
            "source_raw_payload_hash": field("sha256"),
            "evidence_content_hash": field("sha256"),
        },
        "AEMHMatchHistoryEntry": {
            "entry_id": field("string"),
            "seq": field("integer"),
            "event_kind": field("enum:history_event_kind"),
            "snapshot_ref": field("string"),
            "match_state": field("enum:match_state", nullable=True),
            "later_fact_refs": field("string", many=True),
            "later_fact_content_identities": field("sha256", many=True),
            "identity_evidence_refs": field("string", many=True),
            "identity_evidence": field("AEMHIdentityEvidence", many=True),
            "retained_evidence_locator_refs": field("string", many=True),
            "reason_code": field("string"),
            "risk_lifecycle_effect": field("enum:risk_lifecycle_effect"),
            "prior_entry_hash": field("sha256", nullable=True),
            "entry_hash": field("sha256"),
        },
        "AEMHThreadPrefixAnchor": {
            "thread_ref": field("string"),
            "accepted_prefix_seq": field("integer"),
            "accepted_prefix_head_hash": field("sha256", nullable=True),
            "previous_thread_content_hash": field("sha256", nullable=True),
            "prefix_content_hash": field("sha256"),
        },
        "AEMHMatchThread": {
            "thread_ref": field("string"),
            "project_ref": field("string"),
            "site_ref": field("string"),
            "domain": field("enum:aemh_domain"),
            "subject_ref": field("string"),
            "original_candidate_ref": field("string"),
            "candidate_content_identity": field("sha256"),
            "original_reminder_ref": field("string"),
            "history_entries": field("AEMHMatchHistoryEntry", many=True),
            "evidence_locator_refs": field("string", many=True),
            "thread_content_hash": field("sha256"),
        },
        "AEMHHistoryMembershipIndex": {
            "thread_refs": field("string", many=True),
            "candidate_refs": field("string", many=True),
            "later_fact_refs": field("string", many=True),
            "source_locator_refs": field("string", many=True),
            "membership_content_hash": field("sha256"),
        },
        "AEMHMatchHistoryPublicProjection": {
            "contract_id": field("string"),
            "schema_version": field("string"),
            "projection_id": field("string"),
            "receipt_ref": field("string"),
            "scope_identity": field("PublicScopeIdentity"),
            "cutoff_endpoint": field("PublicCutoffEndpoint"),
            "fallback_policy": field("enum:fallback_policy"),
            "previous_projection_ref": field("string", nullable=True),
            "previous_projection_content_hash": field("sha256", nullable=True),
            "accepted_thread_prefixes": field("AEMHThreadPrefixAnchor", many=True),
            "threads": field("AEMHMatchThread", many=True),
            "source_locators": field("PublicSourceLocator", many=True),
            "membership_index": field("AEMHHistoryMembershipIndex"),
            "projection_content_hash": field("sha256"),
        },
        "AEMHMatchHistoryAuthorityPacket": {
            "receipt": field("PublicAuthorityReceipt"),
            "projection": field("AEMHMatchHistoryPublicProjection"),
            "packet_content_hash": field("sha256"),
        },
    }
    return {
        "schema": "aemh-match-history-public-v1-exact-schema",
        "schema_version": SCHEMA_VERSION,
        "exact_object_keys": True,
        "enums": AEMH_ENUMS,
        "objects": objects,
        "hash_recipes": {
            "canonical_json": "UTF-8 JSON; object keys sorted; no insignificant whitespace; history entries alone preserve append order; every other set-like identity/reference/object array is sorted unique and rejects duplicates",
            "entry_hash": "sha256(canonical_json(all AEMHMatchHistoryEntry fields except entry_hash))",
            "thread_content_hash": "sha256(canonical_json(all AEMHMatchThread fields except thread_content_hash))",
            "prefix_content_hash": "sha256(canonical_json(all AEMHThreadPrefixAnchor fields except prefix_content_hash))",
            "projection_content_hash": "sha256(canonical_json(all projection fields except projection_content_hash))",
            "receipt_content_hash": "sha256(canonical_json(all receipt fields except receipt_content_hash))",
            "projection_id": "sha256(canonical_json({contract_id,schema_version,scope_identity.identity_content_hash,membership_index.membership_content_hash}))",
            "receipt_id": "sha256(canonical_json({receipt_variant,authority_contract_id,scope_identity.identity_content_hash,public_projection_id}))",
            "packet_content_hash": "sha256(canonical_json({receipt_content_hash,projection_content_hash}))",
        },
        "invariants": [
            "receipt_variant=aemh_match_history and authority_contract_id=aemh-match-history-public-v1",
            "receipt, projection and every thread join the same project/run/snapshot/cutoff/site/subject/spine identity",
            "projection.schema_version and receipt.authority_contract_version equal this schema.schema_version exactly; receipt.audience_contract_id equals the pinned parent R5 audience contract constant contract.s4.1",
            "projection contract_id, scope cutoff state/ref and PublicCutoffEndpoint close exactly; subject/site visibility closes exactly as in subject-temporal-public-v1",
            "each thread contains exactly one reminder_created entry at seq=1 and original_reminder_ref equals that entry_id",
            "entry_id is globally unique across the projection and every original_reminder_ref resolves to exactly one entry globally and to that thread's sole seq=1 reminder",
            "entries are append-only, strictly contiguous by seq, and each prior_entry_hash equals the preceding entry_hash",
            "match_decided requires exact, ambiguous or rejected; exact has one later fact, ambiguous has at least two, rejected retains considered identity evidence and has no accepted later fact",
            "exact and ambiguous match decisions retain candidate-plus-fact identity evidence; rejected decisions retain nonempty considered identity evidence; every decision retains source evidence locators",
            "identity evidence is typed and exact: candidate evidence binds original_candidate_ref/candidate_content_identity; later-fact evidence binds each later_fact_ref/content identity; considered evidence is allowed only for rejected decisions; every evidence object binds an actually retained source locator, its locator content hash and raw payload hash",
            "candidate and fact content identities equal sha256(canonical_json({entity_kind,entity_ref,source_locator_ref,source_raw_payload_hash})); synchronously rewriting fact ref/content/membership without matching accepted source content fails closed",
            "later_fact_ref and later_fact_content_identity cardinalities are equal and preserve content identity across snapshots",
            "withdrawn and reappeared append new entries; neither deletes or rewrites reminder/match evidence",
            "each thread permits at most one match_decided entry; withdrawn references the same fact/content identity from that prior match, and reappeared is permitted only after that exact fact has been withdrawn and preserves its content identity",
            "retained evidence is a monotonic superset and the thread evidence set equals the union of all retained evidence",
            "risk_lifecycle_effect is mechanically closed to none for every entry; history cannot close, resolve, downgrade or otherwise mutate risk lifecycle",
            "reported AE/MH facts remain distinct from reminder candidates; no candidate is promoted by this projection",
            "a non-initial projection binds previous_projection_ref/hash and one accepted prefix anchor per continuing thread; the current history must preserve the prior history as a byte-identical prefix",
            "previous and current thread sets are identical; prefix-anchor refs equal both sets bidirectionally with no phantom/deleted thread; project/site/subject/domain/candidate/reminder identity is stable across versions",
            "entry snapshot refs are closed to the previous/current lineage: preserved prefix entries retain their prior snapshot byte-for-byte and every appended entry uses the current scope snapshot",
            "every source locator belongs to exactly one nonempty source-revision pair in a sorted-unique total partition; unused pairs and nearest source fallback are forbidden",
            "every source locator is consumed by a cutoff endpoint, thread evidence or retained history evidence; receipt, membership or evaluation-only references cannot justify an unused locator",
            "threads, candidates, prefix anchors, locators and membership refs are sorted unique; membership_index equals their exact emitted sets",
            "evaluation_content_identities equal the complete deterministic sorted-unique projection/member/locator/source/prefix identity set",
        ],
        "error_codes": [
            "PUB_SCHEMA_EXACT_KEYS",
            "PUB_TYPE_BOOL_REQUIRED",
            "PUB_TYPE_MISMATCH",
            "PUB_ENUM_UNKNOWN",
            "PUB_DUPLICATE_REF",
            "PUB_HASH_MISMATCH",
            "PUB_IDENTITY_MISMATCH",
            "PUB_CONTRACT_VERSION_MISMATCH",
            "PUB_AUDIENCE_CONTRACT_MISMATCH",
            "PUB_VISIBILITY_NOT_PROJECTABLE",
            "PUB_VISIBILITY_DEEP_LINK_INELIGIBLE",
            "PUB_VISIBILITY_SCOPE_MISMATCH",
            "PUB_SET_ORDER_OR_DUPLICATE",
            "PUB_SOURCE_REVISION_UNRESOLVED",
            "PUB_SOURCE_PARTITION_MISMATCH",
            "PUB_SOURCE_LOCATOR_UNRESOLVED",
            "PUB_SOURCE_LOCATOR_UNUSED",
            "PUB_SOURCE_CONTENT_MISMATCH",
            "PUB_LOCATOR_SNAPSHOT_MISMATCH",
            "PUB_EVALUATION_IDENTITY_MISMATCH",
            "PUB_IDENTITY_CUTOFF_MISMATCH",
            "PUB_CUTOFF_STATE_MISMATCH",
            "AEMH_CONTRACT_ID_MISMATCH",
            "AEMH_THREAD_REMINDER_MISSING",
            "AEMH_THREAD_REMINDER_REWRITTEN",
            "AEMH_THREAD_REMINDER_DUPLICATE",
            "AEMH_ORIGINAL_REMINDER_REF_MISMATCH",
            "AEMH_ENTRY_ID_DUPLICATE",
            "AEMH_HISTORY_SEQ_GAP",
            "AEMH_HISTORY_PRIOR_HASH_MISMATCH",
            "AEMH_MATCH_STATE_INVALID",
            "AEMH_MATCH_DECISION_DUPLICATE",
            "AEMH_LIFECYCLE_TRANSITION_INVALID",
            "AEMH_MATCH_EVIDENCE_MISSING",
            "AEMH_IDENTITY_EVIDENCE_MISMATCH",
            "AEMH_LATER_FACT_IDENTITY_MISMATCH",
            "AEMH_LATER_FACT_IDENTITY_DRIFT",
            "AEMH_EVIDENCE_RETENTION_VIOLATION",
            "AEMH_WITHDRAW_REAPPEAR_HISTORY_LOSS",
            "AEMH_RISK_LIFECYCLE_EFFECT_FORBIDDEN",
            "AEMH_PREVIOUS_PROJECTION_MISMATCH",
            "AEMH_PREFIX_SEQ_MISMATCH",
            "AEMH_PREFIX_HASH_MISMATCH",
            "AEMH_PREFIX_CONTENT_MISMATCH",
            "AEMH_THREAD_SET_MISMATCH",
            "AEMH_PREFIX_SET_MISMATCH",
            "AEMH_THREAD_STABLE_IDENTITY_MISMATCH",
            "AEMH_SNAPSHOT_LINEAGE_MISMATCH",
            "PUB_OVERLAY_DEFERRED_SET_MISMATCH",
            "PUB_OVERLAY_ARTIFACT_MISMATCH",
            "PUB_SOURCE_MATRIX_ARTIFACT_MISMATCH",
            "PUB_MANIFEST_CONTRACT_MISMATCH",
            "PUB_MANIFEST_PROTECTED_PIN_MISMATCH",
            "PUB_RUNTIME_TEST_SURFACE_FORBIDDEN",
            "PUB_NEAREST_FALLBACK_FORBIDDEN",
            "PUB_MEMBERSHIP_MISMATCH",
        ],
    }


def scope_identity(
    *, snapshot_ref: str = "snapshot::N+1", cutoff_ref: str | None = "2026-08-19"
) -> dict[str, Any]:
    return seal(
        {
            "project_ref": "project::synthetic-contract-example",
            "run_ref": "run::synthetic-contract-example",
            "snapshot_ref": snapshot_ref,
            "cutoff_state": "present" if cutoff_ref is not None else "absent",
            "cutoff_ref": cutoff_ref,
            "site_ref": "site::001",
            "subject_ref": "subject::001-0001",
            "spine_ref": f"spine::001-0001::{snapshot_ref.split('::')[-1]}",
        },
        "identity_content_hash",
    )


def locator(
    locator_ref: str,
    record_ref: str,
    anchor: str,
    *,
    snapshot_ref: str = "snapshot::N+1",
    source_revision_ref: str = "source-revision::listing::N+1",
    source_revision_content_hash: str | None = None,
    authority_entity_kind: str | None = None,
    authority_entity_ref: str | None = None,
) -> dict[str, Any]:
    revision_hash = source_revision_content_hash or canonical_hash(
        {"revision": source_revision_ref, "accepted": True}
    )
    return seal(
        {
            "locator_ref": locator_ref,
            "locator_variant": "r4_source_locator",
            "snapshot_ref": snapshot_ref,
            "source_revision_ref": source_revision_ref,
            "source_revision_content_hash": revision_hash,
            "source_file_ref": None,
            "table_semantic": "synthetic_listing",
            "record_ref": record_ref,
            "authority_entity_kind": authority_entity_kind,
            "authority_entity_ref": authority_entity_ref,
            "column_or_anchor": anchor,
            "canonical_location": None,
            "raw_payload_hash": canonical_hash({"record": record_ref, "anchor": anchor}),
        },
        "locator_content_hash",
    )


def endpoint(
    state: str,
    *,
    exact_date: str | None,
    range_start: str | None,
    range_end: str | None,
    candidates: list[str],
    locator_refs: list[str],
    projectable: bool,
    range_projection_authorized: bool,
    study_day: int | None,
) -> dict[str, Any]:
    return seal(
        {
            "state": state,
            "exact_date": exact_date,
            "range_start": range_start,
            "range_end": range_end,
            "candidate_values": candidates,
            "source_locator_refs": locator_refs,
            "main_axis_projectable": projectable,
            "range_projection_authorized": range_projection_authorized,
            "study_day": study_day,
        },
        "endpoint_content_hash",
    )


def visibility(identity: dict[str, Any]) -> dict[str, Any]:
    subject_ref = identity["subject_ref"]
    site_ref = identity["site_ref"]
    core = {
        "visibility_decision_id": (
            f"visibility::{subject_ref}::{identity['snapshot_ref']}"
        ),
        "visibility_decision_hash": canonical_hash({
            "project_ref": identity["project_ref"],
            "run_ref": identity["run_ref"],
            "snapshot_ref": identity["snapshot_ref"],
            "cutoff_state": identity["cutoff_state"],
            "cutoff_ref": identity["cutoff_ref"],
            "site_ref": site_ref,
            "subject_ref": subject_ref,
            "spine_ref": identity["spine_ref"],
            "state": "projectable",
        }),
        "evaluation_member_refs": [subject_ref],
        "evaluation_site_refs": [site_ref],
        "projectable_member_refs": [subject_ref],
        "projectable_site_refs": [site_ref],
        "hidden_member_refs": [],
        "hidden_site_refs": [],
        "hidden_member_count": 0,
        "hidden_site_count": 0,
        "subject_visibility_state": "projectable",
        "deep_link_eligible": True,
    }
    return seal(core, "closure_content_hash")


def source_pair(
    locator_refs: list[str],
    *,
    revision_id: str = "source-revision::listing::N+1",
    accepted_content_hash: str | None = None,
) -> dict[str, Any]:
    return seal(
        {
            "revision_id": revision_id,
            "accepted_content_hash": accepted_content_hash
            or canonical_hash({"revision": revision_id, "accepted": True}),
            "locator_refs": sorted(locator_refs),
        },
        "pair_content_hash",
    )


def receipt(
    *,
    variant: str,
    authority_contract_id: str,
    identity: dict[str, Any],
    projection_id: str,
    projection_hash: str,
    locator_refs: list[str],
    evaluation_content_identities: list[str],
    source_revision_id: str = "source-revision::listing::N+1",
    source_revision_content_hash: str | None = None,
    source_revision_pairs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    core = {
        "receipt_id": canonical_hash(
            {
                "receipt_variant": variant,
                "authority_contract_id": authority_contract_id,
                "scope_identity_hash": identity["identity_content_hash"],
                "public_projection_id": projection_id,
            }
        ),
        "receipt_variant": variant,
        "authority_contract_id": authority_contract_id,
        "authority_contract_version": SCHEMA_VERSION,
        "scope_identity": identity,
        "public_projection_id": projection_id,
        "public_projection_content_hash": projection_hash,
        "evaluation_content_identities": sorted(set(evaluation_content_identities)),
        "visibility_closure": visibility(identity),
        "source_revision_content_pairs": source_revision_pairs
        if source_revision_pairs is not None
        else [
            source_pair(
                locator_refs,
                revision_id=source_revision_id,
                accepted_content_hash=source_revision_content_hash,
            )
        ],
        "audience_contract_id": PARENT_R5_AUDIENCE_CONTRACT_ID,
    }
    return seal(core, "receipt_content_hash")


def subject_evaluation_identities(
    projection: dict[str, Any], source_revision_content_hashes: list[str]
) -> list[str]:
    values = [
        projection["projection_content_hash"],
        projection["scope_identity"]["identity_content_hash"],
        projection["membership_index"]["membership_content_hash"],
        projection["axis_basis"]["axis_content_hash"],
        *source_revision_content_hashes,
    ]
    values.extend(row["visit_content_hash"] for row in projection["visits"])
    values.extend(row["event_content_identity"] for row in projection["events"])
    values.extend(row["event_content_hash"] for row in projection["events"])
    values.extend(row["risk_content_identity"] for row in projection["risk_anchors"])
    values.extend(row["risk_anchor_content_hash"] for row in projection["risk_anchors"])
    values.extend(row["pending_content_hash"] for row in projection["pending_date_items"])
    values.extend(row["phase_content_hash"] for row in projection["phase_bands"])
    values.extend(row["track_content_hash"] for row in projection["domain_tracks"])
    values.extend(row["locator_content_hash"] for row in projection["source_locators"])
    return sorted(set(values))


def aemh_evaluation_identities(
    projection: dict[str, Any], source_revision_content_hashes: list[str]
) -> list[str]:
    values = [
        projection["projection_content_hash"],
        projection["scope_identity"]["identity_content_hash"],
        projection["membership_index"]["membership_content_hash"],
        projection["cutoff_endpoint"]["cutoff_content_hash"],
        *source_revision_content_hashes,
    ]
    if projection["previous_projection_content_hash"] is not None:
        values.append(projection["previous_projection_content_hash"])
    values.extend(row["prefix_content_hash"] for row in projection["accepted_thread_prefixes"])
    for thread in projection["threads"]:
        values.extend(
            [thread["candidate_content_identity"], thread["thread_content_hash"]]
        )
        for entry in thread["history_entries"]:
            values.append(entry["entry_hash"])
            values.extend(entry["later_fact_content_identities"])
            values.extend(
                evidence["evidence_content_hash"]
                for evidence in entry["identity_evidence"]
            )
    values.extend(row["locator_content_hash"] for row in projection["source_locators"])
    return sorted(set(values))


def subject_example(
    *,
    cutoff_ref: str | None = "2026-08-19",
    uncertain_state: str = "partial",
    include_study_day: bool = True,
) -> dict[str, Any]:
    identity = scope_identity(cutoff_ref=cutoff_ref)
    loc_visit = locator("locator::visit::v1", "visit-row::v1", "visit_date")
    loc_event = locator("locator::event::ae1", "ae-row::1", "start_date")
    loc_partial = locator("locator::event::mh1", "mh-row::1", "start_date")
    locator_refs = [loc_event["locator_ref"], loc_partial["locator_ref"], loc_visit["locator_ref"]]
    exact = endpoint(
        "exact",
        exact_date="2026-08-01",
        range_start=None,
        range_end=None,
        candidates=[],
        locator_refs=[loc_visit["locator_ref"]],
        projectable=True,
        range_projection_authorized=True,
        study_day=1 if include_study_day else None,
    )
    uncertain_candidates = (
        ["2026-08"]
        if uncertain_state == "partial"
        else ["2026-08-03", "2026-08-17"]
    )
    uncertain_range = (
        ("2026-08-01", "2026-08-31")
        if uncertain_state == "partial"
        else ("2026-08-03", "2026-08-17")
    )
    partial = endpoint(
        uncertain_state,
        exact_date=None,
        range_start=uncertain_range[0],
        range_end=uncertain_range[1],
        candidates=uncertain_candidates,
        locator_refs=[loc_partial["locator_ref"]],
        projectable=True,
        range_projection_authorized=True,
        study_day=None,
    )
    exact_end = endpoint(
        "exact",
        exact_date="2026-08-02",
        range_start=None,
        range_end=None,
        candidates=[],
        locator_refs=[loc_event["locator_ref"]],
        projectable=True,
        range_projection_authorized=True,
        study_day=2 if include_study_day else None,
    )
    missing = endpoint(
        "missing",
        exact_date=None,
        range_start=None,
        range_end=None,
        candidates=[],
        locator_refs=[loc_partial["locator_ref"]],
        projectable=False,
        range_projection_authorized=False,
        study_day=None,
    )
    cutoff_endpoint = endpoint(
        "exact" if cutoff_ref is not None else "missing",
        exact_date=cutoff_ref,
        range_start=None,
        range_end=None,
        candidates=[],
        locator_refs=[loc_visit["locator_ref"]],
        projectable=cutoff_ref is not None,
        range_projection_authorized=cutoff_ref is not None,
        study_day=None,
    )
    visit = seal(
        {
            "visit_ref": "visit::actual::v1",
            "visit_kind": "actual",
            "planned_visit_ref": "visit::planned::v1",
            "actual_encounter_ref": "encounter::v1",
            "accepted_assignment_ref": "assignment::v1",
            "phase_ref": "phase::treatment",
            "nominal_endpoint": exact,
            "actual_endpoint": exact,
            "source_locator_refs": [loc_visit["locator_ref"]],
        },
        "visit_content_hash",
    )
    event_ae = seal(
        {
            "event_ref": "event::ae::1",
            "event_content_identity": canonical_hash({"event": "ae::1", "content": "accepted"}),
            "domain": "ae",
            "subtype": "ae",
            "applicability_state": "applicable",
            "visit_ref": visit["visit_ref"],
            "geometry": "closed_interval",
            "start_endpoint": exact,
            "end_endpoint": exact_end,
            "risk_anchor_refs": ["risk-anchor::ae::1"],
            "source_locator_refs": [loc_event["locator_ref"]],
        },
        "event_content_hash",
    )
    event_mh = seal(
        {
            "event_ref": "event::mh::1",
            "event_content_identity": canonical_hash({"event": "mh::1", "content": "accepted"}),
            "domain": "mh",
            "subtype": "mh",
            "applicability_state": "applicable",
            "visit_ref": None,
            "geometry": "open_end",
            "start_endpoint": partial,
            "end_endpoint": missing,
            "risk_anchor_refs": [],
            "source_locator_refs": [loc_partial["locator_ref"]],
        },
        "event_content_hash",
    )
    risk = seal(
        {
            "risk_anchor_ref": "risk-anchor::ae::1",
            "risk_ref": "risk::ae::1",
            "risk_content_identity": canonical_hash({"risk": "ae::1", "severity": "high"}),
            "domain": "ae",
            "severity": "high",
            "risk_type_zh": "严重性核查",
            "event_ref": event_ae["event_ref"],
            "visit_ref": visit["visit_ref"],
            "geometry": "point",
            "start_endpoint": exact,
            "end_endpoint": exact,
            "source_locator_refs": [loc_event["locator_ref"]],
        },
        "risk_anchor_content_hash",
    )
    pending_event = seal(
        {
            "pending_ref": "pending::event::mh::1",
            "item_kind": "event",
            "item_ref": event_mh["event_ref"],
            "target_content_hash": event_mh["event_content_hash"],
            "domain": "mh",
            "start_endpoint": partial,
            "end_endpoint": missing,
            "source_locator_refs": [loc_partial["locator_ref"]],
        },
        "pending_content_hash",
    )
    phase = seal(
        {
            "phase_ref": "phase::treatment",
            "phase_label_zh": "治疗期",
            "geometry": "open_end",
            "start_endpoint": exact,
            "end_endpoint": missing,
            "source_locator_refs": [loc_visit["locator_ref"]],
        },
        "phase_content_hash",
    )
    pending_phase = seal(
        {
            "pending_ref": "pending::phase::treatment",
            "item_kind": "phase",
            "item_ref": phase["phase_ref"],
            "target_content_hash": phase["phase_content_hash"],
            "domain": None,
            "start_endpoint": exact,
            "end_endpoint": missing,
            "source_locator_refs": [loc_visit["locator_ref"]],
        },
        "pending_content_hash",
    )
    tracks = []
    for domain in DOMAINS:
        event_refs = [e["event_ref"] for e in (event_ae, event_mh) if e["domain"] == domain]
        risk_refs = [risk["risk_anchor_ref"]] if domain == "ae" else []
        tracks.append(
            seal(
                {
                    "domain": domain,
                    "applicability_state": "applicable" if event_refs or risk_refs else "not_provided",
                    "event_refs": event_refs,
                    "risk_anchor_refs": risk_refs,
                },
                "track_content_hash",
            )
        )
    membership = seal(
        {
            "visit_refs": [visit["visit_ref"]],
            "event_refs": [event_ae["event_ref"], event_mh["event_ref"]],
            "risk_anchor_refs": [risk["risk_anchor_ref"]],
            "pending_date_refs": [pending_event["pending_ref"], pending_phase["pending_ref"]],
            "phase_refs": [phase["phase_ref"]],
            "source_locator_refs": sorted(locator_refs),
        },
        "membership_content_hash",
    )
    axis = seal(
        {
            "axis_ref": "axis::subject::001-0001::N+1",
            "default_axis_mode": "calendar",
            "timezone": "Asia/Shanghai",
            "study_day_anchor_event_ref": (
                event_ae["event_ref"] if include_study_day else None
            ),
            "study_day_zero_exists": False if include_study_day else None,
            "cutoff_endpoint": cutoff_endpoint,
            "source_locator_refs": [loc_visit["locator_ref"]],
        },
        "axis_content_hash",
    )
    projection_core = {
        "contract_id": SUBJECT_CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "projection_id": canonical_hash(
            {
                "contract_id": SUBJECT_CONTRACT_ID,
                "schema_version": SCHEMA_VERSION,
                "scope_identity_hash": identity["identity_content_hash"],
                "membership_index_hash": membership["membership_content_hash"],
                "axis_basis_hash": axis["axis_content_hash"],
            }
        ),
        "receipt_ref": canonical_hash(
            {
                "receipt_variant": "subject_temporal",
                "authority_contract_id": SUBJECT_CONTRACT_ID,
                "scope_identity_hash": identity["identity_content_hash"],
                "public_projection_id": canonical_hash(
                    {
                        "contract_id": SUBJECT_CONTRACT_ID,
                        "schema_version": SCHEMA_VERSION,
                        "scope_identity_hash": identity["identity_content_hash"],
                        "membership_index_hash": membership["membership_content_hash"],
                        "axis_basis_hash": axis["axis_content_hash"],
                    }
                ),
            }
        ),
        "scope_identity": identity,
        "fallback_policy": "fail_closed_no_nearest",
        "axis_basis": axis,
        "visits": [visit],
        "events": [event_ae, event_mh],
        "risk_anchors": [risk],
        "pending_date_items": [pending_event, pending_phase],
        "phase_bands": [phase],
        "domain_tracks": tracks,
        "source_locators": [loc_event, loc_partial, loc_visit],
        "membership_index": membership,
    }
    projection = seal(projection_core, "projection_content_hash")
    evaluation_identities = subject_evaluation_identities(
        projection, [loc_visit["source_revision_content_hash"]]
    )
    public_receipt = receipt(
        variant="subject_temporal",
        authority_contract_id=SUBJECT_CONTRACT_ID,
        identity=identity,
        projection_id=projection["projection_id"],
        projection_hash=projection["projection_content_hash"],
        locator_refs=locator_refs,
        evaluation_content_identities=evaluation_identities,
        source_revision_content_hash=loc_visit["source_revision_content_hash"],
    )
    projection["receipt_ref"] = public_receipt["receipt_id"]
    projection = seal(
        {k: v for k, v in projection.items() if k != "projection_content_hash"},
        "projection_content_hash",
    )
    evaluation_identities = subject_evaluation_identities(
        projection, [loc_visit["source_revision_content_hash"]]
    )
    public_receipt = receipt(
        variant="subject_temporal",
        authority_contract_id=SUBJECT_CONTRACT_ID,
        identity=identity,
        projection_id=projection["projection_id"],
        projection_hash=projection["projection_content_hash"],
        locator_refs=locator_refs,
        evaluation_content_identities=evaluation_identities,
        source_revision_content_hash=loc_visit["source_revision_content_hash"],
    )
    packet = {
        "receipt": public_receipt,
        "projection": projection,
    }
    packet["packet_content_hash"] = canonical_hash(
        {
            "receipt_content_hash": public_receipt["receipt_content_hash"],
            "projection_content_hash": projection["projection_content_hash"],
        }
    )
    return packet


def aemh_entity_content_identity(
    entity_kind: str, entity_ref: str, source_locator: dict[str, Any]
) -> str:
    return canonical_hash(
        {
            "entity_kind": entity_kind,
            "entity_ref": entity_ref,
            "source_locator_ref": source_locator["locator_ref"],
            "source_raw_payload_hash": source_locator["raw_payload_hash"],
        }
    )


def identity_evidence(
    evidence_ref: str,
    evidence_kind: str,
    entity_ref: str,
    source_locator: dict[str, Any],
) -> dict[str, Any]:
    return seal(
        {
            "evidence_ref": evidence_ref,
            "evidence_kind": evidence_kind,
            "entity_ref": entity_ref,
            "entity_content_identity": aemh_entity_content_identity(
                evidence_kind, entity_ref, source_locator
            ),
            "source_locator_ref": source_locator["locator_ref"],
            "source_locator_content_hash": source_locator[
                "locator_content_hash"
            ],
            "source_raw_payload_hash": source_locator["raw_payload_hash"],
        },
        "evidence_content_hash",
    )


def history_entry(
    *,
    thread_key: str,
    seq: int,
    event_kind: str,
    snapshot_ref: str,
    match_state: str | None,
    later_fact_refs: list[str],
    later_fact_hashes: list[str],
    identity_evidence_refs: list[str],
    identity_evidence_items: list[dict[str, Any]],
    retained: list[str],
    reason_code: str,
    prior_entry_hash: str | None,
) -> dict[str, Any]:
    core = {
        "entry_id": f"history-entry::{thread_key}::{seq}",
        "seq": seq,
        "event_kind": event_kind,
        "snapshot_ref": snapshot_ref,
        "match_state": match_state,
        "later_fact_refs": later_fact_refs,
        "later_fact_content_identities": later_fact_hashes,
        "identity_evidence_refs": identity_evidence_refs,
        "identity_evidence": identity_evidence_items,
        "retained_evidence_locator_refs": retained,
        "reason_code": reason_code,
        "risk_lifecycle_effect": "none",
        "prior_entry_hash": prior_entry_hash,
    }
    return seal(core, "entry_hash")


def cutoff_endpoint(
    exact_date: str | None, locator_refs: list[str]
) -> dict[str, Any]:
    return seal(
        {
            "state": "present" if exact_date is not None else "absent",
            "exact_date": exact_date,
            "source_locator_refs": sorted(set(locator_refs)) if exact_date is not None else [],
        },
        "cutoff_content_hash",
    )


def build_aemh_packet(
    *,
    identity: dict[str, Any],
    threads: list[dict[str, Any]],
    locators: list[dict[str, Any]],
    source_pairs: list[dict[str, Any]],
    cutoff: dict[str, Any],
    previous_packet: dict[str, Any] | None,
) -> dict[str, Any]:
    locators = sorted(locators, key=lambda row: row["locator_ref"])
    threads = sorted(threads, key=lambda row: row["thread_ref"])
    source_pairs = sorted(source_pairs, key=lambda row: row["revision_id"])
    locator_refs = [row["locator_ref"] for row in locators]
    later_fact_refs = sorted(
        {
            ref
            for thread in threads
            for entry in thread["history_entries"]
            for ref in entry["later_fact_refs"]
        }
    )
    membership = seal(
        {
            "thread_refs": [thread["thread_ref"] for thread in threads],
            "candidate_refs": sorted(
                thread["original_candidate_ref"] for thread in threads
            ),
            "later_fact_refs": later_fact_refs,
            "source_locator_refs": locator_refs,
        },
        "membership_content_hash",
    )
    prefixes: list[dict[str, Any]] = []
    previous_projection_ref = None
    previous_projection_content_hash = None
    if previous_packet is not None:
        previous_projection = previous_packet["projection"]
        previous_threads = {
            row["thread_ref"]: row for row in previous_projection["threads"]
        }
        for thread in threads:
            previous_thread = previous_threads.get(thread["thread_ref"])
            if previous_thread is None:
                continue
            previous_entries = previous_thread["history_entries"]
            prefixes.append(
                seal(
                    {
                        "thread_ref": thread["thread_ref"],
                        "accepted_prefix_seq": len(previous_entries),
                        "accepted_prefix_head_hash": (
                            previous_entries[-1]["entry_hash"]
                            if previous_entries
                            else None
                        ),
                        "previous_thread_content_hash": previous_thread[
                            "thread_content_hash"
                        ],
                    },
                    "prefix_content_hash",
                )
            )
        prefixes.sort(key=lambda row: row["thread_ref"])
        previous_projection_ref = previous_projection["projection_id"]
        previous_projection_content_hash = previous_projection["projection_content_hash"]
    projection_id = canonical_hash(
        {
            "contract_id": AEMH_CONTRACT_ID,
            "schema_version": SCHEMA_VERSION,
            "scope_identity_hash": identity["identity_content_hash"],
            "membership_index_hash": membership["membership_content_hash"],
        }
    )
    receipt_id = canonical_hash(
        {
            "receipt_variant": "aemh_match_history",
            "authority_contract_id": AEMH_CONTRACT_ID,
            "scope_identity_hash": identity["identity_content_hash"],
            "public_projection_id": projection_id,
        }
    )
    projection = seal(
        {
            "contract_id": AEMH_CONTRACT_ID,
            "schema_version": SCHEMA_VERSION,
            "projection_id": projection_id,
            "receipt_ref": receipt_id,
            "scope_identity": identity,
            "cutoff_endpoint": cutoff,
            "fallback_policy": "fail_closed_no_nearest",
            "previous_projection_ref": previous_projection_ref,
            "previous_projection_content_hash": previous_projection_content_hash,
            "accepted_thread_prefixes": prefixes,
            "threads": threads,
            "source_locators": locators,
            "membership_index": membership,
        },
        "projection_content_hash",
    )
    revision_hashes = [pair["accepted_content_hash"] for pair in source_pairs]
    public_receipt = receipt(
        variant="aemh_match_history",
        authority_contract_id=AEMH_CONTRACT_ID,
        identity=identity,
        projection_id=projection["projection_id"],
        projection_hash=projection["projection_content_hash"],
        locator_refs=locator_refs,
        evaluation_content_identities=aemh_evaluation_identities(
            projection, revision_hashes
        ),
        source_revision_pairs=source_pairs,
    )
    packet = {"receipt": public_receipt, "projection": projection}
    packet["packet_content_hash"] = canonical_hash(
        {
            "receipt_content_hash": public_receipt["receipt_content_hash"],
            "projection_content_hash": projection["projection_content_hash"],
        }
    )
    return packet


def aemh_examples() -> tuple[dict[str, Any], dict[str, Any]]:
    revision_n = "source-revision::listing::N"
    revision_n1 = "source-revision::listing::N+1"
    revision_n_hash = canonical_hash({"revision": revision_n, "accepted": True})
    revision_n1_hash = canonical_hash({"revision": revision_n1, "accepted": True})
    previous_identity = scope_identity(snapshot_ref="snapshot::N", cutoff_ref="2026-08-10")
    current_identity = scope_identity(snapshot_ref="snapshot::N+1", cutoff_ref="2026-08-19")
    previous_ae_reminder_locator = locator(
        "locator::reminder::ae1",
        "clue-row::1",
        "concept",
        snapshot_ref="snapshot::N",
        source_revision_ref=revision_n,
        source_revision_content_hash=revision_n_hash,
        authority_entity_kind="candidate",
        authority_entity_ref="candidate::suspected-ae::1",
    )
    previous_mh_reminder_locator = locator(
        "locator::reminder::mh1",
        "clue-row::2",
        "concept",
        snapshot_ref="snapshot::N",
        source_revision_ref=revision_n,
        source_revision_content_hash=revision_n_hash,
        authority_entity_kind="candidate",
        authority_entity_ref="candidate::suspected-mh::1",
    )
    current_ae_reminder_locator = locator(
        "locator::reminder::ae1",
        "clue-row::1",
        "concept",
        snapshot_ref="snapshot::N+1",
        source_revision_ref=revision_n,
        source_revision_content_hash=revision_n_hash,
        authority_entity_kind="candidate",
        authority_entity_ref="candidate::suspected-ae::1",
    )
    current_mh_reminder_locator = locator(
        "locator::reminder::mh1",
        "clue-row::2",
        "concept",
        snapshot_ref="snapshot::N+1",
        source_revision_ref=revision_n,
        source_revision_content_hash=revision_n_hash,
        authority_entity_kind="candidate",
        authority_entity_ref="candidate::suspected-mh::1",
    )
    current_fact_locator = locator(
        "locator::fact::ae1",
        "ae-row::later-1",
        "term",
        snapshot_ref="snapshot::N+1",
        source_revision_ref=revision_n1,
        source_revision_content_hash=revision_n1_hash,
        authority_entity_kind="later_fact",
        authority_entity_ref="fact::reported-ae::later-1",
    )
    current_considered_mh_locator = locator(
        "locator::considered-fact::mh1",
        "mh-row::considered-1",
        "term",
        snapshot_ref="snapshot::N+1",
        source_revision_ref=revision_n1,
        source_revision_content_hash=revision_n1_hash,
        authority_entity_kind="considered_fact",
        authority_entity_ref="considered-fact::reported-mh::1",
    )
    ae_candidate_ref = "candidate::suspected-ae::1"
    mh_candidate_ref = "candidate::suspected-mh::1"
    fact_ref = "fact::reported-ae::later-1"
    considered_mh_ref = "considered-fact::reported-mh::1"
    ae_candidate_identity = aemh_entity_content_identity(
        "candidate", ae_candidate_ref, previous_ae_reminder_locator
    )
    mh_candidate_identity = aemh_entity_content_identity(
        "candidate", mh_candidate_ref, previous_mh_reminder_locator
    )
    fact_hash = aemh_entity_content_identity(
        "later_fact", fact_ref, current_fact_locator
    )
    previous_ae_candidate_evidence = identity_evidence(
        "identity-evidence::candidate::ae1",
        "candidate",
        ae_candidate_ref,
        previous_ae_reminder_locator,
    )
    previous_mh_candidate_evidence = identity_evidence(
        "identity-evidence::candidate::mh1",
        "candidate",
        mh_candidate_ref,
        previous_mh_reminder_locator,
    )
    ae_e1 = history_entry(
        thread_key="ae::1",
        seq=1,
        event_kind="reminder_created",
        snapshot_ref="snapshot::N",
        match_state=None,
        later_fact_refs=[],
        later_fact_hashes=[],
        identity_evidence_refs=["identity-evidence::candidate::ae1"],
        identity_evidence_items=[previous_ae_candidate_evidence],
        retained=[previous_ae_reminder_locator["locator_ref"]],
        reason_code="suspected_unreported_ae_reminder",
        prior_entry_hash=None,
    )
    mh_e1 = history_entry(
        thread_key="mh::1",
        seq=1,
        event_kind="reminder_created",
        snapshot_ref="snapshot::N",
        match_state=None,
        later_fact_refs=[],
        later_fact_hashes=[],
        identity_evidence_refs=["identity-evidence::candidate::mh1"],
        identity_evidence_items=[previous_mh_candidate_evidence],
        retained=[previous_mh_reminder_locator["locator_ref"]],
        reason_code="suspected_unreported_mh_reminder",
        prior_entry_hash=None,
    )
    previous_ae_thread = seal(
        {
            "thread_ref": "aemh-thread::ae::1",
            "project_ref": previous_identity["project_ref"],
            "site_ref": previous_identity["site_ref"],
            "domain": "ae",
            "subject_ref": previous_identity["subject_ref"],
            "original_candidate_ref": ae_candidate_ref,
            "candidate_content_identity": ae_candidate_identity,
            "original_reminder_ref": ae_e1["entry_id"],
            "history_entries": [ae_e1],
            "evidence_locator_refs": [previous_ae_reminder_locator["locator_ref"]],
        },
        "thread_content_hash",
    )
    previous_mh_thread = seal(
        {
            "thread_ref": "aemh-thread::mh::1",
            "project_ref": previous_identity["project_ref"],
            "site_ref": previous_identity["site_ref"],
            "domain": "mh",
            "subject_ref": previous_identity["subject_ref"],
            "original_candidate_ref": mh_candidate_ref,
            "candidate_content_identity": mh_candidate_identity,
            "original_reminder_ref": mh_e1["entry_id"],
            "history_entries": [mh_e1],
            "evidence_locator_refs": [previous_mh_reminder_locator["locator_ref"]],
        },
        "thread_content_hash",
    )
    previous_pair = source_pair(
        [
            previous_ae_reminder_locator["locator_ref"],
            previous_mh_reminder_locator["locator_ref"],
        ],
        revision_id=revision_n,
        accepted_content_hash=revision_n_hash,
    )
    previous_packet = build_aemh_packet(
        identity=previous_identity,
        threads=[previous_ae_thread, previous_mh_thread],
        locators=[previous_ae_reminder_locator, previous_mh_reminder_locator],
        source_pairs=[previous_pair],
        cutoff=cutoff_endpoint(
            "2026-08-10", [previous_ae_reminder_locator["locator_ref"]]
        ),
        previous_packet=None,
    )
    current_ae_candidate_evidence = identity_evidence(
        "identity-evidence::candidate::ae1",
        "candidate",
        ae_candidate_ref,
        current_ae_reminder_locator,
    )
    current_ae_fact_evidence = identity_evidence(
        "identity-evidence::fact::ae1",
        "later_fact",
        fact_ref,
        current_fact_locator,
    )
    current_mh_candidate_evidence = identity_evidence(
        "identity-evidence::candidate::mh1",
        "candidate",
        mh_candidate_ref,
        current_mh_reminder_locator,
    )
    current_mh_considered_evidence = identity_evidence(
        "identity-evidence::considered-fact::mh1",
        "considered_fact",
        considered_mh_ref,
        current_considered_mh_locator,
    )
    retained = sorted(
        [
            current_fact_locator["locator_ref"],
            current_ae_reminder_locator["locator_ref"],
        ]
    )
    ae_e2 = history_entry(
        thread_key="ae::1",
        seq=2,
        event_kind="match_decided",
        snapshot_ref="snapshot::N+1",
        match_state="exact",
        later_fact_refs=[fact_ref],
        later_fact_hashes=[fact_hash],
        identity_evidence_refs=["identity-evidence::candidate::ae1", "identity-evidence::fact::ae1"],
        identity_evidence_items=[current_ae_candidate_evidence, current_ae_fact_evidence],
        retained=retained,
        reason_code="exact_identity_and_temporal_match",
        prior_entry_hash=ae_e1["entry_hash"],
    )
    ae_e3 = history_entry(
        thread_key="ae::1",
        seq=3,
        event_kind="withdrawn",
        snapshot_ref="snapshot::N+1",
        match_state=None,
        later_fact_refs=[fact_ref],
        later_fact_hashes=[fact_hash],
        identity_evidence_refs=["identity-evidence::fact::ae1"],
        identity_evidence_items=[current_ae_fact_evidence],
        retained=retained,
        reason_code="later_fact_withdrawn",
        prior_entry_hash=ae_e2["entry_hash"],
    )
    ae_e4 = history_entry(
        thread_key="ae::1",
        seq=4,
        event_kind="reappeared",
        snapshot_ref="snapshot::N+1",
        match_state=None,
        later_fact_refs=[fact_ref],
        later_fact_hashes=[fact_hash],
        identity_evidence_refs=["identity-evidence::fact::ae1"],
        identity_evidence_items=[current_ae_fact_evidence],
        retained=retained,
        reason_code="same_later_fact_reappeared",
        prior_entry_hash=ae_e3["entry_hash"],
    )
    current_ae_thread = seal(
        {
            "thread_ref": previous_ae_thread["thread_ref"],
            "project_ref": current_identity["project_ref"],
            "site_ref": current_identity["site_ref"],
            "domain": "ae",
            "subject_ref": current_identity["subject_ref"],
            "original_candidate_ref": previous_ae_thread["original_candidate_ref"],
            "candidate_content_identity": ae_candidate_identity,
            "original_reminder_ref": ae_e1["entry_id"],
            "history_entries": [ae_e1, ae_e2, ae_e3, ae_e4],
            "evidence_locator_refs": retained,
        },
        "thread_content_hash",
    )
    mh_e2 = history_entry(
        thread_key="mh::1",
        seq=2,
        event_kind="match_decided",
        snapshot_ref="snapshot::N+1",
        match_state="rejected",
        later_fact_refs=[],
        later_fact_hashes=[],
        identity_evidence_refs=[
            "identity-evidence::candidate::mh1",
            "identity-evidence::considered-fact::mh1",
        ],
        identity_evidence_items=[
            current_mh_candidate_evidence,
            current_mh_considered_evidence,
        ],
        retained=sorted(
            [
                current_considered_mh_locator["locator_ref"],
                current_mh_reminder_locator["locator_ref"],
            ]
        ),
        reason_code="rejected_after_identity_evidence_review",
        prior_entry_hash=mh_e1["entry_hash"],
    )
    current_mh_thread = seal(
        {
            "thread_ref": previous_mh_thread["thread_ref"],
            "project_ref": current_identity["project_ref"],
            "site_ref": current_identity["site_ref"],
            "domain": previous_mh_thread["domain"],
            "subject_ref": current_identity["subject_ref"],
            "original_candidate_ref": previous_mh_thread["original_candidate_ref"],
            "candidate_content_identity": mh_candidate_identity,
            "original_reminder_ref": mh_e1["entry_id"],
            "history_entries": [mh_e1, mh_e2],
            "evidence_locator_refs": sorted(
                [
                    current_considered_mh_locator["locator_ref"],
                    current_mh_reminder_locator["locator_ref"],
                ]
            ),
        },
        "thread_content_hash",
    )
    current_pairs = [
        source_pair(
            [
                current_ae_reminder_locator["locator_ref"],
                current_mh_reminder_locator["locator_ref"],
            ],
            revision_id=revision_n,
            accepted_content_hash=revision_n_hash,
        ),
        source_pair(
            [
                current_considered_mh_locator["locator_ref"],
                current_fact_locator["locator_ref"],
            ],
            revision_id=revision_n1,
            accepted_content_hash=revision_n1_hash,
        ),
    ]
    current_packet = build_aemh_packet(
        identity=current_identity,
        threads=[current_ae_thread, current_mh_thread],
        locators=[
            current_considered_mh_locator,
            current_fact_locator,
            current_ae_reminder_locator,
            current_mh_reminder_locator,
        ],
        source_pairs=current_pairs,
        cutoff=cutoff_endpoint(
            "2026-08-19", [current_ae_reminder_locator["locator_ref"]]
        ),
        previous_packet=previous_packet,
    )
    return previous_packet, current_packet


def source_matrix() -> dict[str, Any]:
    entries = [
        {
            "source": "mm_r1.domain:SourceRevision.{revision_id,project_id,content_hash}",
            "classification": "reusable_upstream_leaf",
            "permits": ["source revision identity and accepted content hash input"],
            "forbids": ["using SourceRevision alone as a public receipt or visibility decision"],
        },
        {
            "source": "mm_r1.domain:ListingSnapshot.{snapshot_id,project_id,revision_id,content_hash}",
            "classification": "reusable_upstream_leaf",
            "permits": ["snapshot/revision identity join"],
            "forbids": ["treating is_synthetic or a fixture name as public authority"],
        },
        {
            "source": "mm_r1.domain:MonitoringRun.{run_id,project_id,data_cutoff,source_revision_id}",
            "classification": "reusable_upstream_leaf",
            "permits": ["run/project/cutoff join"],
            "forbids": ["fabricating a missing cutoff"],
        },
        {
            "source": "mm_r1.domain:TemporalEvent and SubjectTemporalSpine",
            "classification": "reference_only_incomplete_public_authority",
            "permits": ["event/subject/run identity and exact actual_date when accepted upstream"],
            "forbids": ["direct public authority: no receipt, visibility closure, independent start/end state, geometry, conflict ranges or source revision closure"],
        },
        {
            "source": "mm_r1.ae_mh:AEMHResult.{reported_facts,candidates,identity_metadata,historical_evidence_refs,temporal_spines}",
            "classification": "reference_only_incomplete_public_authority",
            "permits": ["candidate/fact/evidence leaves when joined to accepted snapshots"],
            "forbids": ["direct match-history authority; historical_evidence_refs is not an append-only decision ledger"],
        },
        {
            "source": "mm_r2.risk:RiskCandidate.{candidate_id,subject_ref,domain,source_snapshot_id,content_hash}",
            "classification": "reusable_upstream_leaf",
            "permits": ["candidate content identity and subject/domain/snapshot join"],
            "forbids": ["promotion to reported AE/MH fact or risk lifecycle mutation by S5"],
        },
        {
            "source": "mm_r2.risk:RiskInstance and RiskTransition",
            "classification": "reusable_upstream_leaf_read_only",
            "permits": ["existing risk identity/state display input"],
            "forbids": ["using match history to close, resolve, reopen, downgrade or otherwise mutate lifecycle"],
        },
        {
            "source": "mm_r4.contracts:SourceLocator",
            "classification": "reusable_upstream_leaf",
            "permits": ["snapshot/revision/table/record/column/raw-payload source locator variant"],
            "forbids": ["nearest record/cell/clause fallback"],
        },
        {
            "source": "mm_r4.visit_schedule:{PlannedVisitDefinition,ActualEncounterRecord,ActualActivityRecord,VisitAssignmentDecision,TypedScheduleAnchorRef}",
            "classification": "reusable_upstream_leaf_set",
            "permits": ["planned/actual/assignment/phase/time/source leaves"],
            "forbids": ["inferring actual from nominal; snapping unscheduled encounters; accepting unverified assignment"],
        },
        {
            "source": "mm_r4.visit_schedule:VisitJourneyProjection",
            "classification": "reference_only_incomplete_public_authority",
            "permits": ["projection and marker identity/hash reference"],
            "forbids": ["direct public authority because activity_markers and pending_time_markers are Any and receipt/visibility/source-revision closure is absent"],
        },
        {
            "source": "mm_r4.d08_contracts:{ScopeBinding,SharedSpineBinding,RecordNode,TimeRef,VisibilityDecision,SourceLocator}",
            "classification": "reusable_upstream_leaf_set",
            "permits": ["scope/spine/record/time/visibility/source joins"],
            "forbids": ["using D08TypedInput.visit_refs:Tuple[Any,...] as an exact public visit contract"],
        },
        {
            "source": "mm_r4.d07_journey:build_d07_subject_journey output",
            "classification": "reference_renderer_projection_only",
            "permits": ["shared-spine/hash/source-jump validation design reference"],
            "forbids": ["direct authority; dictionary output and fallback OTHER behavior do not satisfy the closed eight-domain public contract"],
        },
        {
            "source": "mm_r4.aemh:{SemanticRecord,EventMatchStrategy,AEMHUnitResult,AEMHSliceResult}",
            "classification": "reusable_upstream_leaf_set",
            "permits": ["reported-vs-evidence distinction, match evidence, candidate and journey marker leaves"],
            "forbids": ["direct cross-snapshot append-only history; _ReportedMatchOutcome is private and single-run"],
        },
        {
            "source": "mm_r5.contracts:{R5AuthorityReceipt,SourceRevisionContentPair}",
            "classification": "reusable_upstream_contract_shape",
            "permits": ["receipt identity, visibility hash and source revision-content pair conventions"],
            "forbids": ["claiming subject_temporal or aemh_history producer variants exist today"],
        },
        {
            "source": "mm_r5.s4_contracts:S4AcceptedAuthorityAnchor and S4JourneyTargetIdentity",
            "classification": "reusable_accepted_identity_leaf_set",
            "permits": ["accepted project/run/snapshot/cutoff/site/subject/risk/spine/source identity join"],
            "forbids": ["S4 acceptance being transferred to S5 public authority"],
        },
        {
            "source": "subject_temporal_public:SubjectTemporalAuthorityPacket",
            "classification": "new_external_public_authority_producer_requirement",
            "implementation_status": "contract_only_not_implemented",
            "permits": ["future exact subject-temporal receipt and projection only after separate implementation contract and acceptance"],
            "forbids": ["labeling this nonexistent producer as current direct authority"],
        },
        {
            "source": "aemh_match_history_public:AEMHMatchHistoryAuthorityPacket",
            "classification": "new_external_public_authority_producer_requirement",
            "implementation_status": "contract_only_not_implemented",
            "permits": ["future append-only AE/MH history receipt and projection only after separate implementation contract and acceptance"],
            "forbids": ["labeling this nonexistent producer as current direct authority"],
        },
    ]
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-source-matrix-v0.1",
        "contract_id": CONTRACT_ID,
        "exact_entry_order_and_content": True,
        "entries": entries,
        "classification_vocabulary": [
            "reusable_upstream_leaf",
            "reusable_upstream_leaf_read_only",
            "reusable_upstream_leaf_set",
            "reusable_upstream_contract_shape",
            "reusable_accepted_identity_leaf_set",
            "reference_only_incomplete_public_authority",
            "reference_renderer_projection_only",
            "new_external_public_authority_producer_requirement",
        ],
        "producer_requirement_contract": [
            {
                "contract_id": AEMH_CONTRACT_ID,
                "packet_source": "aemh_match_history_public:AEMHMatchHistoryAuthorityPacket",
                "projection_source": "aemh_match_history_public:AEMHMatchHistoryPublicProjection",
                "receipt_variant": "aemh_match_history",
                "implementation_status": "contract_only_not_implemented",
            },
            {
                "contract_id": SUBJECT_CONTRACT_ID,
                "packet_source": "subject_temporal_public:SubjectTemporalAuthorityPacket",
                "projection_source": "subject_temporal_public:SubjectTemporalPublicProjection",
                "receipt_variant": "subject_temporal",
                "implementation_status": "contract_only_not_implemented",
            },
        ],
        "global_rule": "Only an existing exact typed leaf may be called reusable/direct input. Both public packet module paths are future producer requirements and are not current direct authority.",
    }


def overlay(parent: dict[str, Any]) -> dict[str, Any]:
    replacements = []
    for mapping in parent["field_mappings"]:
        deferred = mapping.get("deferred_contract")
        if deferred not in (SUBJECT_CONTRACT_ID, AEMH_CONTRACT_ID):
            continue
        target = mapping["target"]
        if deferred == SUBJECT_CONTRACT_ID:
            source_path = "subject_temporal_public:SubjectTemporalPublicProjection"
            receipt_variant = "subject_temporal"
        else:
            source_path = "aemh_match_history_public:AEMHMatchHistoryPublicProjection"
            receipt_variant = "aemh_match_history"
        replacements.append(
            {
                "target": target,
                "parent_deferred_contract": deferred,
                "replacement_source_kind": "external_public_authority_requirement",
                "replacement_source_path": source_path,
                "required_receipt_variant": receipt_variant,
                "implementation_status": "contract_only_not_implemented",
                "adaptation_recipe": mapping["recipe_id"],
            }
        )
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-exact-overlay-v0.1",
        "contract_id": CONTRACT_ID,
        "parent_exact_contract_sha256": SOURCE_PINS[
            "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json"
        ],
        "parent_schema": parent["schema"],
        "deferred_contracts_closed_by_schema": [SUBJECT_CONTRACT_ID, AEMH_CONTRACT_ID],
        "mapping_replacements": replacements,
        "replacement_count": len(replacements),
        "authority_rule": "The overlay freezes future producer requirements. It does not change existing R5 files and does not claim either module/path currently exists.",
        "unlock_rule": {
            "contract_acceptance_only_unlocks": "later_public_authority_implementation_contract",
            "does_not_satisfy": [
                "ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1",
                "ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1",
                "ACCEPT_R5_S5_CONTRACT",
            ],
            "s5_runtime_remains_locked": True,
        },
    }


def inherited_challenges(parent: dict[str, Any]) -> list[dict[str, Any]]:
    selected = parent["challenge_rules"][100:164]
    expected_categories = (
        ["visit_semantics"] * 8
        + ["axis_conversion"] * 8
        + ["uncertain_dates"] * 8
        + ["eight_domain_adaptation"] * 16
        + ["encoding_registry"] * 8
        + ["aemh_projection"] * 8
        + ["aemh_match_history"] * 8
    )
    if [row["category"] for row in selected] != expected_categories:
        raise RuntimeError("parent R5C-101..164 challenge slice drifted")
    result = []
    for offset, row in enumerate(selected, start=101):
        contract = AEMH_CONTRACT_ID if row["category"] in (
            "aemh_projection",
            "aemh_match_history",
        ) else SUBJECT_CONTRACT_ID
        result.append(
            {
                "case_id": f"R5C-{offset}",
                "origin": "accepted_r5_v0_3_challenge_rule_projection",
                "parent_case_id": f"R5C-{offset}",
                "contract": contract,
                "category": row["category"],
                "precondition": f"valid::{row['rule_id']}",
                "single_mutation": {
                    "op": "replace",
                    "path": f"/{row['category']}/{row['slot']}",
                    "value": row["mutated_value"],
                },
                "expected_typed_outcome_or_error": row["expected_outcome"],
                "forbidden_audience_output": ["fabricated_authority", "nearest_fallback"],
                "stage_oracle_contract": {
                    "kind": "inherited_specification_projection",
                    "planned_stage": "later_public_authority_implementation",
                    "rule_id": row["rule_id"],
                    "test_locator": f"public_authority_implementation::{row['rule_id']}",
                    "expected_outcome": row["expected_outcome"],
                    "expected_projection": row["expected_projection"],
                    "required_non_llm_anchor": "typed producer fixture + public authority validator + canonical projection hash",
                },
            }
        )
    return result


def public_specific_challenges() -> list[dict[str, Any]]:
    specs = [
        ("PA-001", SUBJECT_CONTRACT_ID, "receipt_variant", "/receipt/receipt_variant", "aemh_match_history", "PUB_ENUM_UNKNOWN"),
        ("PA-002", SUBJECT_CONTRACT_ID, "projection_hash", "/receipt/public_projection_content_hash", "0" * 64, "PUB_HASH_MISMATCH"),
        ("PA-003", SUBJECT_CONTRACT_ID, "subject_join", "/projection/scope_identity/subject_ref", "subject::wrong", "PUB_IDENTITY_SUBJECT_MISMATCH"),
        ("PA-004", SUBJECT_CONTRACT_ID, "visibility", "/receipt/visibility_closure/subject_visibility_state", "hidden", "PUB_VISIBILITY_NOT_PROJECTABLE"),
        ("PA-005", SUBJECT_CONTRACT_ID, "source_revision", "/receipt/source_revision_content_pairs/0/accepted_content_hash", "0" * 64, "PUB_SOURCE_REVISION_UNRESOLVED"),
        ("PA-006", SUBJECT_CONTRACT_ID, "source_locator", "/projection/events/0/source_locator_refs/0", "locator::missing", "PUB_SOURCE_LOCATOR_UNRESOLVED"),
        ("PA-007", SUBJECT_CONTRACT_ID, "unscheduled_semantics", "/projection/visits/0/visit_kind", "unscheduled", "PUB_UNSCHEDULED_PLANNED_BINDING_FORBIDDEN"),
        ("PA-008", SUBJECT_CONTRACT_ID, "fallback", "/projection/fallback_policy", "nearest", "PUB_NEAREST_FALLBACK_FORBIDDEN"),
        ("PA-009", AEMH_CONTRACT_ID, "receipt_variant", "/receipt/receipt_variant", "subject_temporal", "AEMH_CONTRACT_ID_MISMATCH"),
        ("PA-010", AEMH_CONTRACT_ID, "candidate_identity", "/projection/threads/0/candidate_content_identity", "0" * 64, "PUB_HASH_MISMATCH"),
        ("PA-011", AEMH_CONTRACT_ID, "history_order", "/projection/threads/0/history_entries/1/seq", 4, "AEMH_HISTORY_SEQ_GAP"),
        ("PA-012", AEMH_CONTRACT_ID, "prior_hash", "/projection/threads/0/history_entries/1/prior_entry_hash", "0" * 64, "AEMH_HISTORY_PRIOR_HASH_MISMATCH"),
        ("PA-013", AEMH_CONTRACT_ID, "evidence_retention", "/projection/threads/0/history_entries/1/retained_evidence_locator_refs", [], "AEMH_EVIDENCE_RETENTION_VIOLATION"),
        ("PA-014", AEMH_CONTRACT_ID, "later_fact_identity", "/projection/threads/0/history_entries/1/later_fact_content_identities", [], "AEMH_LATER_FACT_IDENTITY_MISMATCH"),
        ("PA-015", AEMH_CONTRACT_ID, "risk_lifecycle_veto", "/projection/threads/0/history_entries/1/risk_lifecycle_effect", "closed", "AEMH_RISK_LIFECYCLE_EFFECT_FORBIDDEN"),
        ("PA-016", AEMH_CONTRACT_ID, "reminder_immutability", "/projection/threads/0/history_entries/0/event_kind", "withdrawn", "AEMH_THREAD_REMINDER_REWRITTEN"),
        ("PA-017", SUBJECT_CONTRACT_ID, "locator_snapshot_scope", "/projection/source_locators/0/snapshot_ref", "snapshot::wrong", "PUB_LOCATOR_SNAPSHOT_MISMATCH"),
        ("PA-018", SUBJECT_CONTRACT_ID, "locator_revision_pair", "/projection/source_locators/0/source_revision_ref", "source-revision::missing", "PUB_SOURCE_REVISION_UNRESOLVED"),
        ("PA-019", SUBJECT_CONTRACT_ID, "locator_revision_content", "/projection/source_locators/0/source_revision_content_hash", "0" * 64, "PUB_SOURCE_CONTENT_MISMATCH"),
        ("PA-020", SUBJECT_CONTRACT_ID, "subject_projectable_membership", "/receipt/visibility_closure/projectable_member_refs", [], "PUB_VISIBILITY_NOT_PROJECTABLE"),
        ("PA-021", SUBJECT_CONTRACT_ID, "subject_hidden_exclusion", "/receipt/visibility_closure/hidden_member_refs", ["subject::001-0001"], "PUB_VISIBILITY_NOT_PROJECTABLE"),
        ("PA-022", SUBJECT_CONTRACT_ID, "site_projectable_membership", "/receipt/visibility_closure/projectable_site_refs", [], "PUB_VISIBILITY_NOT_PROJECTABLE"),
        ("PA-023", SUBJECT_CONTRACT_ID, "site_hidden_exclusion", "/receipt/visibility_closure/hidden_site_refs", ["site::001"], "PUB_VISIBILITY_NOT_PROJECTABLE"),
        ("PA-024", SUBJECT_CONTRACT_ID, "real_calendar_date", "/projection/axis_basis/cutoff_endpoint/exact_date", "2026-02-30", "PUB_DATE_INVALID"),
        ("PA-025", SUBJECT_CONTRACT_ID, "range_order", "/projection/events/1/start_endpoint/range_start", "2026-09-01", "PUB_DATE_RANGE_ORDER"),
        ("PA-026", SUBJECT_CONTRACT_ID, "interval_order", "/projection/events/0/start_endpoint/exact_date", "2026-08-03", "PUB_INTERVAL_ORDER"),
        ("PA-027", AEMH_CONTRACT_ID, "projection_contract_id", "/projection/contract_id", "wrong-contract", "AEMH_CONTRACT_ID_MISMATCH"),
        ("PA-028", AEMH_CONTRACT_ID, "cutoff_scope_join", "/projection/scope_identity/cutoff_ref", "2026-08-18", "PUB_IDENTITY_CUTOFF_MISMATCH"),
        ("PA-029", AEMH_CONTRACT_ID, "cutoff_endpoint_join", "/projection/cutoff_endpoint/exact_date", "2026-08-18", "PUB_IDENTITY_CUTOFF_MISMATCH"),
        ("PA-030", AEMH_CONTRACT_ID, "aemh_site_visibility", "/receipt/visibility_closure/projectable_site_refs", [], "PUB_VISIBILITY_NOT_PROJECTABLE"),
        ("PA-031", AEMH_CONTRACT_ID, "single_reminder", "/projection/threads/0/history_entries/1/event_kind", "reminder_created", "AEMH_THREAD_REMINDER_DUPLICATE"),
        ("PA-032", AEMH_CONTRACT_ID, "original_reminder_binding", "/projection/threads/0/original_reminder_ref", "history-entry::wrong", "AEMH_ORIGINAL_REMINDER_REF_MISMATCH"),
        ("PA-033", AEMH_CONTRACT_ID, "later_fact_identity_drift", "/projection/threads/0/history_entries/2/later_fact_content_identities/0", "0" * 64, "AEMH_LATER_FACT_IDENTITY_DRIFT"),
        ("PA-034", AEMH_CONTRACT_ID, "prefix_seq", "/projection/accepted_thread_prefixes/0/accepted_prefix_seq", 2, "AEMH_PREFIX_SEQ_MISMATCH"),
        ("PA-035", AEMH_CONTRACT_ID, "prefix_head", "/projection/accepted_thread_prefixes/0/accepted_prefix_head_hash", "0" * 64, "AEMH_PREFIX_HASH_MISMATCH"),
        ("PA-036", AEMH_CONTRACT_ID, "previous_projection_hash", "/projection/previous_projection_content_hash", "0" * 64, "AEMH_PREVIOUS_PROJECTION_MISMATCH"),
        ("PA-037", AEMH_CONTRACT_ID, "prefix_content", "/projection/threads/0/history_entries/0/reason_code", "rewritten", "AEMH_PREFIX_CONTENT_MISMATCH"),
        ("PA-038", SUBJECT_CONTRACT_ID, "subject_evaluation_identities", "/receipt/evaluation_content_identities", [], "PUB_EVALUATION_IDENTITY_MISMATCH"),
        ("PA-039", AEMH_CONTRACT_ID, "aemh_evaluation_identities", "/receipt/evaluation_content_identities", [], "PUB_EVALUATION_IDENTITY_MISMATCH"),
        ("PA-040", SUBJECT_CONTRACT_ID, "track_dangling_event", "/projection/domain_tracks/0/event_refs/0", "event::missing", "PUB_REFERENCE_UNRESOLVED"),
        ("PA-041", SUBJECT_CONTRACT_ID, "track_cross_domain", "/projection/domain_tracks/0/event_refs/0", "event::mh::1", "PUB_REFERENCE_DOMAIN_MISMATCH"),
        ("PA-042", SUBJECT_CONTRACT_ID, "event_dangling_visit", "/projection/events/0/visit_ref", "visit::missing", "PUB_REFERENCE_UNRESOLVED"),
        ("PA-043", SUBJECT_CONTRACT_ID, "event_dangling_risk", "/projection/events/0/risk_anchor_refs/0", "risk-anchor::missing", "PUB_REFERENCE_UNRESOLVED"),
        ("PA-044", SUBJECT_CONTRACT_ID, "risk_dangling_event", "/projection/risk_anchors/0/event_ref", "event::missing", "PUB_REFERENCE_UNRESOLVED"),
        ("PA-045", SUBJECT_CONTRACT_ID, "visit_dangling_phase", "/projection/visits/0/phase_ref", "phase::missing", "PUB_REFERENCE_PHASE_MISMATCH"),
        ("PA-046", SUBJECT_CONTRACT_ID, "pending_dangling_item", "/projection/pending_date_items/0/item_ref", "event::missing", "PUB_REFERENCE_UNRESOLVED"),
        ("PA-047", SUBJECT_CONTRACT_ID, "pending_cross_domain", "/projection/pending_date_items/0/domain", "ae", "PUB_REFERENCE_DOMAIN_MISMATCH"),
        ("PA-048", SUBJECT_CONTRACT_ID, "partial_projection_authority", "/projection/events/1/start_endpoint/range_projection_authorized", False, "PUB_DATE_PROJECTABILITY_MISMATCH"),
        ("PA-049", SUBJECT_CONTRACT_ID, "partial_projection_state", "/projection/events/1/start_endpoint/main_axis_projectable", False, "PUB_DATE_PROJECTABILITY_MISMATCH"),
        ("PA-050", AEMH_CONTRACT_ID, "aemh_locator_snapshot_scope", "/projection/source_locators/0/snapshot_ref", "snapshot::wrong", "PUB_LOCATOR_SNAPSHOT_MISMATCH"),
        ("PA-051", AEMH_CONTRACT_ID, "aemh_subject_projectable_membership", "/receipt/visibility_closure/projectable_member_refs", [], "PUB_VISIBILITY_NOT_PROJECTABLE"),
        ("PA-052", AEMH_CONTRACT_ID, "aemh_subject_hidden_exclusion", "/receipt/visibility_closure/hidden_member_refs", ["subject::001-0001"], "PUB_VISIBILITY_NOT_PROJECTABLE"),
        ("PA-053", AEMH_CONTRACT_ID, "aemh_site_hidden_exclusion", "/receipt/visibility_closure/hidden_site_refs", ["site::001"], "PUB_VISIBILITY_NOT_PROJECTABLE"),
        ("PA-054", AEMH_CONTRACT_ID, "aemh_source_pair_unique_revision", "/receipt/source_revision_content_pairs/1/revision_id", "source-revision::listing::N", "PUB_SOURCE_REVISION_UNRESOLVED"),
        ("PA-055", AEMH_CONTRACT_ID, "aemh_locator_revision_content", "/projection/source_locators/0/source_revision_content_hash", "0" * 64, "PUB_SOURCE_CONTENT_MISMATCH"),
        ("PA-056", SUBJECT_CONTRACT_ID, "partial_calendar_date", "/projection/events/1/start_endpoint/candidate_values/0", "2026-13", "PUB_DATE_INVALID"),
    ]
    rows = []
    for case_id, contract, category, path, value, error in specs:
        rows.append(
            {
                "case_id": case_id,
                "origin": "public_authority_specific_contract_case",
                "parent_case_id": None,
                "contract": contract,
                "category": category,
                "precondition": "valid frozen base input",
                "base_input_key": (
                    "subject_temporal_valid_base"
                    if contract == SUBJECT_CONTRACT_ID
                    else "aemh_match_history_valid_base"
                ),
                "fully_reseal_after_mutation": False,
                "single_mutation": {"op": "replace", "path": path, "value": value},
                "expected_typed_outcome_or_error": f"reject:{error}",
                "forbidden_audience_output": ["mutated_projection", "risk_lifecycle_write"],
                "stage_oracle_contract": {
                    "kind": "contract_tamper_probe",
                    "planned_stage": "contract_verification",
                    "rule_id": f"public_authority.{category}",
                    "test_locator": f"verify_medical_monitoring_r5_s5_public_authority_contract_v0_1::{case_id}",
                    "expected_outcome": f"reject:{error}",
                    "expected_projection": "not_emitted",
                    "required_non_llm_anchor": "deterministic in-memory mutation rejected by verifier",
                },
            }
        )
    exact_start = endpoint(
        "exact",
        exact_date="2026-08-01",
        range_start=None,
        range_end=None,
        candidates=[],
        locator_refs=["locator::visit::v1"],
        projectable=True,
        range_projection_authorized=True,
        study_day=1,
    )
    exact_end = endpoint(
        "exact",
        exact_date="2026-08-02",
        range_start=None,
        range_end=None,
        candidates=[],
        locator_refs=["locator::event::ae1"],
        projectable=True,
        range_projection_authorized=True,
        study_day=2,
    )
    phantom_prefix = seal(
        {
            "thread_ref": "aemh-thread::phantom::1",
            "accepted_prefix_seq": 1,
            "accepted_prefix_head_hash": "0" * 64,
            "previous_thread_content_hash": "1" * 64,
        },
        "prefix_content_hash",
    )
    invalid_not_applicable_track = seal(
        {
            "domain": "cm",
            "applicability_state": "not_applicable",
            "event_refs": ["event::ae::1"],
            "risk_anchor_refs": [],
        },
        "track_content_hash",
    )
    unused_subject_revision = "source-revision::unused-subject"
    unused_subject_hash = canonical_hash(
        {"revision": unused_subject_revision, "accepted": True}
    )
    unused_subject_locator = locator(
        "locator::unused::subject",
        "unused-row::subject",
        "unused_anchor",
        source_revision_ref=unused_subject_revision,
        source_revision_content_hash=unused_subject_hash,
    )
    unused_subject_pair = source_pair(
        [unused_subject_locator["locator_ref"]],
        revision_id=unused_subject_revision,
        accepted_content_hash=unused_subject_hash,
    )
    unused_aemh_revision = "source-revision::unused-aemh"
    unused_aemh_hash = canonical_hash(
        {"revision": unused_aemh_revision, "accepted": True}
    )
    unused_aemh_locator = locator(
        "locator::unused::aemh",
        "unused-row::aemh",
        "unused_anchor",
        source_revision_ref=unused_aemh_revision,
        source_revision_content_hash=unused_aemh_hash,
    )
    unused_aemh_pair = source_pair(
        [unused_aemh_locator["locator_ref"]],
        revision_id=unused_aemh_revision,
        accepted_content_hash=unused_aemh_hash,
    )
    advanced_specs = [
        ("PA-057", SUBJECT_CONTRACT_ID, "visibility_foreign_evaluation_member", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/visibility_closure/evaluation_member_refs", "value": ["subject::001-0001", "subject::foreign"]}, "PUB_VISIBILITY_SCOPE_MISMATCH"),
        ("PA-058", SUBJECT_CONTRACT_ID, "visibility_foreign_projectable_member", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/visibility_closure/projectable_member_refs", "value": ["subject::001-0001", "subject::foreign"]}, "PUB_VISIBILITY_SCOPE_MISMATCH"),
        ("PA-059", SUBJECT_CONTRACT_ID, "visibility_foreign_evaluation_site", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/visibility_closure/evaluation_site_refs", "value": ["site::001", "site::foreign"]}, "PUB_VISIBILITY_SCOPE_MISMATCH"),
        ("PA-060", SUBJECT_CONTRACT_ID, "visibility_foreign_hidden_member", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/visibility_closure/hidden_member_refs", "value": ["subject::foreign"]}, "PUB_VISIBILITY_SCOPE_MISMATCH"),
        ("PA-061", SUBJECT_CONTRACT_ID, "visibility_duplicate_member", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/visibility_closure/evaluation_member_refs", "value": ["subject::001-0001", "subject::001-0001"]}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-062", AEMH_CONTRACT_ID, "aemh_visibility_foreign_member", "aemh_match_history_valid_base", {"op": "replace", "path": "/receipt/visibility_closure/projectable_member_refs", "value": ["subject::001-0001", "subject::foreign"]}, "PUB_VISIBILITY_SCOPE_MISMATCH"),
        ("PA-063", SUBJECT_CONTRACT_ID, "source_locator_order", "subject_temporal_valid_base", {"op": "reverse", "path": "/projection/source_locators"}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-064", AEMH_CONTRACT_ID, "source_pair_order", "aemh_match_history_valid_base", {"op": "reverse", "path": "/receipt/source_revision_content_pairs"}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-065", SUBJECT_CONTRACT_ID, "source_pair_locator_duplicate", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/source_revision_content_pairs/0/locator_refs", "value": ["locator::event::ae1", "locator::event::ae1", "locator::event::mh1", "locator::visit::v1"]}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-066", SUBJECT_CONTRACT_ID, "source_pair_empty_unused", "subject_temporal_valid_base", {"op": "append", "path": "/receipt/source_revision_content_pairs", "value": source_pair([], revision_id="source-revision::unused")}, "PUB_SOURCE_PARTITION_MISMATCH"),
        ("PA-067", SUBJECT_CONTRACT_ID, "endpoint_locator_duplicate", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/0/start_endpoint/source_locator_refs", "value": ["locator::visit::v1", "locator::visit::v1"]}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-068", SUBJECT_CONTRACT_ID, "subject_evaluation_identity_order", "subject_temporal_valid_base", {"op": "reverse", "path": "/receipt/evaluation_content_identities"}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-069", AEMH_CONTRACT_ID, "aemh_evaluation_identity_order", "aemh_match_history_valid_base", {"op": "reverse", "path": "/receipt/evaluation_content_identities"}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-070", SUBJECT_CONTRACT_ID, "absent_cutoff_scope_ref", "subject_temporal_absent_cutoff_valid_base", {"op": "replace", "path": "/projection/scope_identity/cutoff_ref", "value": "2026-08-19"}, "PUB_CUTOFF_STATE_MISMATCH"),
        ("PA-071", SUBJECT_CONTRACT_ID, "absent_cutoff_endpoint_state", "subject_temporal_absent_cutoff_valid_base", {"op": "replace", "path": "/projection/axis_basis/cutoff_endpoint/state", "value": "exact"}, "PUB_CUTOFF_STATE_MISMATCH"),
        ("PA-072", SUBJECT_CONTRACT_ID, "absent_cutoff_projectable", "subject_temporal_absent_cutoff_valid_base", {"op": "replace", "path": "/projection/axis_basis/cutoff_endpoint/main_axis_projectable", "value": True}, "PUB_CUTOFF_STATE_MISMATCH"),
        ("PA-073", SUBJECT_CONTRACT_ID, "present_cutoff_missing", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/axis_basis/cutoff_endpoint/state", "value": "missing"}, "PUB_CUTOFF_STATE_MISMATCH"),
        ("PA-074", SUBJECT_CONTRACT_ID, "partial_candidate_outside_range", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/1/start_endpoint/candidate_values/0", "value": "2026-09"}, "PUB_DATE_CANDIDATE_RANGE_MISMATCH"),
        ("PA-075", SUBJECT_CONTRACT_ID, "partial_range_not_candidate_envelope", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/1/start_endpoint/range_start", "value": "2026-08-02"}, "PUB_DATE_CANDIDATE_RANGE_MISMATCH"),
        ("PA-076", SUBJECT_CONTRACT_ID, "partial_candidate_duplicate", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/1/start_endpoint/candidate_values", "value": ["2026-08", "2026-08"]}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-077", SUBJECT_CONTRACT_ID, "conflicted_candidate_outside_range", "subject_temporal_conflicted_valid_base", {"op": "replace", "path": "/projection/events/1/start_endpoint/candidate_values/1", "value": "2026-08-18"}, "PUB_DATE_CANDIDATE_RANGE_MISMATCH"),
        ("PA-078", SUBJECT_CONTRACT_ID, "conflicted_range_not_candidate_envelope", "subject_temporal_conflicted_valid_base", {"op": "replace", "path": "/projection/events/1/start_endpoint/range_end", "value": "2026-08-18"}, "PUB_DATE_CANDIDATE_RANGE_MISMATCH"),
        ("PA-079", SUBJECT_CONTRACT_ID, "closed_interval_identical_endpoints", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/0/end_endpoint", "value": exact_start}, "PUB_DATE_GEOMETRY_DEGENERATE"),
        ("PA-080", SUBJECT_CONTRACT_ID, "point_distinct_endpoints", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/risk_anchors/0/end_endpoint", "value": exact_end}, "PUB_DATE_GEOMETRY_INVALID"),
        ("PA-081", SUBJECT_CONTRACT_ID, "pending_endpoint_mirror", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/pending_date_items/0/start_endpoint", "value": exact_start}, "PUB_PENDING_MIRROR_MISMATCH"),
        ("PA-082", SUBJECT_CONTRACT_ID, "pending_source_mirror", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/pending_date_items/0/source_locator_refs", "value": ["locator::visit::v1"]}, "PUB_PENDING_MIRROR_MISMATCH"),
        ("PA-083", SUBJECT_CONTRACT_ID, "pending_event_missing", "subject_temporal_valid_base", {"op": "delete", "path": "/projection/pending_date_items/0"}, "PUB_PENDING_COVERAGE_MISMATCH"),
        ("PA-084", SUBJECT_CONTRACT_ID, "pending_phase_missing", "subject_temporal_valid_base", {"op": "delete", "path": "/projection/pending_date_items/1"}, "PUB_PENDING_COVERAGE_MISMATCH"),
        ("PA-085", SUBJECT_CONTRACT_ID, "pending_visit_nonprojectable", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/visits/0/actual_endpoint/main_axis_projectable", "value": False}, "PUB_PENDING_COVERAGE_MISMATCH"),
        ("PA-086", SUBJECT_CONTRACT_ID, "pending_risk_nonprojectable", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/risk_anchors/0/start_endpoint/main_axis_projectable", "value": False}, "PUB_PENDING_COVERAGE_MISMATCH"),
        ("PA-087", SUBJECT_CONTRACT_ID, "pending_duplicate_target", "subject_temporal_valid_base", {"op": "append_copy", "path": "/projection/pending_date_items", "from_index": 0}, "PUB_PENDING_COVERAGE_MISMATCH"),
        ("PA-088", SUBJECT_CONTRACT_ID, "duplicate_visit", "subject_temporal_valid_base", {"op": "append_copy", "path": "/projection/visits", "from_index": 0}, "PUB_DUPLICATE_REF"),
        ("PA-089", SUBJECT_CONTRACT_ID, "duplicate_event", "subject_temporal_valid_base", {"op": "append_copy", "path": "/projection/events", "from_index": 0}, "PUB_DUPLICATE_REF"),
        ("PA-090", SUBJECT_CONTRACT_ID, "duplicate_risk", "subject_temporal_valid_base", {"op": "append_copy", "path": "/projection/risk_anchors", "from_index": 0}, "PUB_DUPLICATE_REF"),
        ("PA-091", SUBJECT_CONTRACT_ID, "duplicate_phase", "subject_temporal_valid_base", {"op": "append_copy", "path": "/projection/phase_bands", "from_index": 0}, "PUB_DUPLICATE_REF"),
        ("PA-092", SUBJECT_CONTRACT_ID, "duplicate_track", "subject_temporal_valid_base", {"op": "append_copy", "path": "/projection/domain_tracks", "from_index": 0}, "PUB_DUPLICATE_REF"),
        ("PA-093", SUBJECT_CONTRACT_ID, "duplicate_membership_ref", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/membership_index/event_refs", "value": ["event::ae::1", "event::ae::1", "event::mh::1"]}, "PUB_DUPLICATE_REF"),
        ("PA-094", AEMH_CONTRACT_ID, "duplicate_thread", "aemh_match_history_valid_base", {"op": "append_copy", "path": "/projection/threads", "from_index": 0}, "PUB_DUPLICATE_REF"),
        ("PA-095", AEMH_CONTRACT_ID, "duplicate_candidate", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/original_candidate_ref", "value": "candidate::suspected-ae::1"}, "PUB_DUPLICATE_REF"),
        ("PA-096", AEMH_CONTRACT_ID, "duplicate_aemh_membership_ref", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/membership_index/thread_refs", "value": ["aemh-thread::ae::1", "aemh-thread::ae::1"]}, "PUB_DUPLICATE_REF"),
        ("PA-097", AEMH_CONTRACT_ID, "cross_version_thread_deletion", "aemh_match_history_valid_base", {"op": "delete", "path": "/projection/threads/1"}, "AEMH_THREAD_SET_MISMATCH"),
        ("PA-098", AEMH_CONTRACT_ID, "cross_version_prefix_missing", "aemh_match_history_valid_base", {"op": "delete", "path": "/projection/accepted_thread_prefixes/1"}, "AEMH_PREFIX_SET_MISMATCH"),
        ("PA-099", AEMH_CONTRACT_ID, "cross_version_prefix_phantom", "aemh_match_history_valid_base", {"op": "append", "path": "/projection/accepted_thread_prefixes", "value": phantom_prefix}, "AEMH_PREFIX_SET_MISMATCH"),
        ("PA-100", AEMH_CONTRACT_ID, "thread_stable_project", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/project_ref", "value": "project::foreign"}, "AEMH_THREAD_STABLE_IDENTITY_MISMATCH"),
        ("PA-101", AEMH_CONTRACT_ID, "thread_stable_site", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/site_ref", "value": "site::foreign"}, "AEMH_THREAD_STABLE_IDENTITY_MISMATCH"),
        ("PA-102", AEMH_CONTRACT_ID, "thread_stable_subject", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/subject_ref", "value": "subject::foreign"}, "AEMH_THREAD_STABLE_IDENTITY_MISMATCH"),
        ("PA-103", AEMH_CONTRACT_ID, "thread_stable_domain", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/domain", "value": "ae"}, "AEMH_THREAD_STABLE_IDENTITY_MISMATCH"),
        ("PA-104", AEMH_CONTRACT_ID, "thread_stable_candidate_ref", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/original_candidate_ref", "value": "candidate::foreign"}, "AEMH_THREAD_STABLE_IDENTITY_MISMATCH"),
        ("PA-105", AEMH_CONTRACT_ID, "thread_stable_candidate_content", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/candidate_content_identity", "value": "0" * 64}, "AEMH_THREAD_STABLE_IDENTITY_MISMATCH"),
        ("PA-106", AEMH_CONTRACT_ID, "thread_stable_reminder", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/original_reminder_ref", "value": "history-entry::foreign"}, "AEMH_THREAD_STABLE_IDENTITY_MISMATCH"),
        ("PA-107", AEMH_CONTRACT_ID, "prefix_anchor_order", "aemh_match_history_valid_base", {"op": "reverse", "path": "/projection/accepted_thread_prefixes"}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-108", AEMH_CONTRACT_ID, "thread_order", "aemh_match_history_valid_base", {"op": "reverse", "path": "/projection/threads"}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-109", AEMH_CONTRACT_ID, "entry_evidence_duplicate", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/identity_evidence_refs", "value": ["identity-evidence::candidate::ae1", "identity-evidence::candidate::ae1"]}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-110", AEMH_CONTRACT_ID, "aemh_pair_locator_duplicate", "aemh_match_history_valid_base", {"op": "replace", "path": "/receipt/source_revision_content_pairs/0/locator_refs", "value": ["locator::reminder::ae1", "locator::reminder::ae1", "locator::reminder::mh1"]}, "PUB_SET_ORDER_OR_DUPLICATE"),
        ("PA-111", AEMH_CONTRACT_ID, "aemh_unused_nonempty_pair", "aemh_match_history_valid_base", {"op": "append", "path": "/receipt/source_revision_content_pairs", "value": source_pair(["locator::foreign"], revision_id="source-revision::unused")}, "PUB_SOURCE_PARTITION_MISMATCH"),
        ("PA-112", SUBJECT_CONTRACT_ID, "visibility_foreign_projectable_site", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/visibility_closure/projectable_site_refs", "value": ["site::001", "site::foreign"]}, "PUB_VISIBILITY_SCOPE_MISMATCH"),
        ("PA-113", AEMH_CONTRACT_ID, "cross_version_thread_phantom", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/thread_ref", "value": "aemh-thread::phantom::1"}, "AEMH_THREAD_SET_MISMATCH"),
        ("PA-114", AEMH_CONTRACT_ID, "duplicate_candidate_membership", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/membership_index/candidate_refs", "value": ["candidate::suspected-ae::1", "candidate::suspected-ae::1"]}, "PUB_DUPLICATE_REF"),
        ("PA-115", SUBJECT_CONTRACT_ID, "pending_target_content_mirror", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/pending_date_items/0/target_content_hash", "value": "0" * 64}, "PUB_PENDING_MIRROR_MISMATCH"),
        ("PA-116", SUBJECT_CONTRACT_ID, "absent_cutoff_exact_date", "subject_temporal_absent_cutoff_valid_base", {"op": "replace", "path": "/projection/axis_basis/cutoff_endpoint/exact_date", "value": "2026-08-19"}, "PUB_CUTOFF_STATE_MISMATCH"),
        ("PA-117", SUBJECT_CONTRACT_ID, "absent_cutoff_study_day", "subject_temporal_absent_cutoff_valid_base", {"op": "replace", "path": "/projection/axis_basis/cutoff_endpoint/study_day", "value": 1}, "PUB_CUTOFF_STATE_MISMATCH"),
        ("PA-118", SUBJECT_CONTRACT_ID, "present_cutoff_exact_mismatch", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/axis_basis/cutoff_endpoint/exact_date", "value": "2026-08-18"}, "PUB_CUTOFF_STATE_MISMATCH"),
        ("PA-119", SUBJECT_CONTRACT_ID, "visibility_foreign_hidden_site", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/visibility_closure/hidden_site_refs", "value": ["site::foreign"]}, "PUB_VISIBILITY_SCOPE_MISMATCH"),
        ("PA-120", AEMH_CONTRACT_ID, "fully_resealed_prefix_seq", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/accepted_thread_prefixes/0/accepted_prefix_seq", "value": 2}, "AEMH_PREFIX_SEQ_MISMATCH"),
        ("PA-121", AEMH_CONTRACT_ID, "fully_resealed_prefix_head", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/accepted_thread_prefixes/0/accepted_prefix_head_hash", "value": "0" * 64}, "AEMH_PREFIX_HASH_MISMATCH"),
        ("PA-122", SUBJECT_CONTRACT_ID, "subject_evaluation_identity_missing", "subject_temporal_valid_base", {"op": "delete", "path": "/receipt/evaluation_content_identities/0"}, "PUB_EVALUATION_IDENTITY_MISMATCH"),
        ("PA-123", AEMH_CONTRACT_ID, "aemh_evaluation_identity_missing", "aemh_match_history_valid_base", {"op": "delete", "path": "/receipt/evaluation_content_identities/0"}, "PUB_EVALUATION_IDENTITY_MISMATCH"),
        ("PA-124", AEMH_CONTRACT_ID, "fully_resealed_source_content", "aemh_match_history_valid_base", {"op": "replace", "path": "/receipt/source_revision_content_pairs/0/accepted_content_hash", "value": "0" * 64}, "PUB_SOURCE_CONTENT_MISMATCH"),
        ("PA-125", AEMH_CONTRACT_ID, "fully_resealed_locator_revision", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/source_locators/0/source_revision_ref", "value": "source-revision::missing"}, "PUB_SOURCE_REVISION_UNRESOLVED"),
        ("PA-126", SUBJECT_CONTRACT_ID, "domain_member_not_provided", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/domain_tracks/0/applicability_state", "value": "not_provided"}, "PUB_DOMAIN_APPLICABILITY_MISMATCH"),
        ("PA-127", SUBJECT_CONTRACT_ID, "empty_domain_applicable", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/domain_tracks/2/applicability_state", "value": "applicable"}, "PUB_DOMAIN_APPLICABILITY_MISMATCH"),
        ("PA-128", SUBJECT_CONTRACT_ID, "not_applicable_with_member_ref", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/domain_tracks/2", "value": invalid_not_applicable_track}, "PUB_DOMAIN_APPLICABILITY_MISMATCH"),
        ("PA-129", SUBJECT_CONTRACT_ID, "study_day_anchor_removed", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/axis_basis/study_day_anchor_event_ref", "value": None}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-130", SUBJECT_CONTRACT_ID, "visit_nominal_study_day_without_anchor", "subject_temporal_no_study_day_valid_base", {"op": "replace", "path": "/projection/visits/0/nominal_endpoint/study_day", "value": 1}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-131", SUBJECT_CONTRACT_ID, "visit_actual_study_day_without_anchor", "subject_temporal_no_study_day_valid_base", {"op": "replace", "path": "/projection/visits/0/actual_endpoint/study_day", "value": 1}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-132", SUBJECT_CONTRACT_ID, "event_study_day_without_anchor", "subject_temporal_no_study_day_valid_base", {"op": "replace", "path": "/projection/events/0/start_endpoint/study_day", "value": 1}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-133", SUBJECT_CONTRACT_ID, "risk_study_day_without_anchor", "subject_temporal_no_study_day_valid_base", {"op": "replace", "path": "/projection/risk_anchors/0/start_endpoint/study_day", "value": 1}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-134", SUBJECT_CONTRACT_ID, "phase_study_day_without_anchor", "subject_temporal_no_study_day_valid_base", {"op": "replace", "path": "/projection/phase_bands/0/start_endpoint/study_day", "value": 1}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-135", SUBJECT_CONTRACT_ID, "pending_study_day_without_anchor", "subject_temporal_no_study_day_valid_base", {"op": "replace", "path": "/projection/pending_date_items/0/start_endpoint/study_day", "value": 1}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-136", SUBJECT_CONTRACT_ID, "study_day_axis_without_anchor", "subject_temporal_no_study_day_valid_base", {"op": "replace", "path": "/projection/axis_basis/default_axis_mode", "value": "study_day"}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-137", SUBJECT_CONTRACT_ID, "event_end_study_day_without_anchor", "subject_temporal_no_study_day_valid_base", {"op": "replace", "path": "/projection/events/0/end_endpoint/study_day", "value": 2}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-138", AEMH_CONTRACT_ID, "appended_entry_foreign_snapshot", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/snapshot_ref", "value": "snapshot::foreign"}, "AEMH_SNAPSHOT_LINEAGE_MISMATCH"),
        ("PA-139", AEMH_CONTRACT_ID, "prefix_entry_foreign_snapshot", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/0/snapshot_ref", "value": "snapshot::foreign"}, "AEMH_SNAPSHOT_LINEAGE_MISMATCH"),
        ("PA-140", AEMH_CONTRACT_ID, "appended_entry_previous_snapshot", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/snapshot_ref", "value": "snapshot::N"}, "AEMH_SNAPSHOT_LINEAGE_MISMATCH"),
        ("PA-141", AEMH_CONTRACT_ID, "exact_match_identity_evidence_missing", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/identity_evidence_refs", "value": []}, "AEMH_MATCH_EVIDENCE_MISSING"),
        ("PA-142", AEMH_CONTRACT_ID, "exact_match_retained_evidence_missing", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/retained_evidence_locator_refs", "value": []}, "AEMH_MATCH_EVIDENCE_MISSING"),
        ("PA-143", AEMH_CONTRACT_ID, "rejected_match_identity_evidence_missing", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/history_entries/1/identity_evidence_refs", "value": []}, "AEMH_MATCH_EVIDENCE_MISSING"),
        ("PA-144", AEMH_CONTRACT_ID, "rejected_match_retained_evidence_missing", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/history_entries/1/retained_evidence_locator_refs", "value": []}, "AEMH_MATCH_EVIDENCE_MISSING"),
        ("PA-145", SUBJECT_CONTRACT_ID, "subject_unused_locator", "subject_temporal_valid_base", {"op": "inject_unused_locator", "path": "/", "locator": unused_subject_locator, "source_pair": unused_subject_pair}, "PUB_SOURCE_LOCATOR_UNUSED"),
        ("PA-146", AEMH_CONTRACT_ID, "aemh_unused_locator", "aemh_match_history_valid_base", {"op": "inject_unused_locator", "path": "/", "locator": unused_aemh_locator, "source_pair": unused_aemh_pair}, "PUB_SOURCE_LOCATOR_UNUSED"),
        ("PA-147", "exact-overlay-v0.1", "overlay_duplicate_target", "exact_overlay_artifact", {"op": "replace", "path": "/mapping_replacements/0/target", "value": "R5AEMHMatchHistory.from_snapshot_ref"}, "PUB_OVERLAY_DEFERRED_SET_MISMATCH"),
        ("PA-148", "exact-overlay-v0.1", "overlay_wrong_deferred_contract", "exact_overlay_artifact", {"op": "replace", "path": "/mapping_replacements/0/parent_deferred_contract", "value": "subject-temporal-public-v1"}, "PUB_OVERLAY_DEFERRED_SET_MISMATCH"),
        ("PA-149", "exact-overlay-v0.1", "overlay_unsorted_pairs", "exact_overlay_artifact", {"op": "reverse", "path": "/mapping_replacements"}, "PUB_OVERLAY_DEFERRED_SET_MISMATCH"),
        ("PA-150", SUBJECT_CONTRACT_ID, "study_day_anchor_outside_membership", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/membership_index/event_refs", "value": []}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-151", SUBJECT_CONTRACT_ID, "study_day_anchor_without_accepted_source", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/0/start_endpoint/source_locator_refs", "value": []}, "PUB_STUDY_DAY_ANCHOR_MISSING"),
        ("PA-152", AEMH_CONTRACT_ID, "exact_match_foreign_identity_evidence", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/identity_evidence_refs", "value": ["identity-evidence::foreign::1", "identity-evidence::foreign::2"]}, "AEMH_MATCH_EVIDENCE_MISSING"),
        ("PA-153", AEMH_CONTRACT_ID, "rejected_match_without_considered_identity", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/history_entries/1/identity_evidence_refs", "value": ["identity-evidence::candidate::mh1"]}, "AEMH_MATCH_EVIDENCE_MISSING"),
        ("PA-154", SUBJECT_CONTRACT_ID, "event_not_applicable_while_emitted", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/0/applicability_state", "value": "not_applicable"}, "PUB_DOMAIN_APPLICABILITY_MISMATCH"),
        ("PA-155", SUBJECT_CONTRACT_ID, "event_not_provided_while_emitted", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/1/applicability_state", "value": "not_provided"}, "PUB_DOMAIN_APPLICABILITY_MISMATCH"),
        ("PA-156", SUBJECT_CONTRACT_ID, "study_day_arbitrary_999", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/visits/0/nominal_endpoint/study_day", "value": 999}, "PUB_STUDY_DAY_VALUE_MISMATCH"),
        ("PA-157", SUBJECT_CONTRACT_ID, "study_day_anchor_invalid_value", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/0/start_endpoint/study_day", "value": 2}, "PUB_STUDY_DAY_VALUE_MISMATCH"),
        ("PA-158", SUBJECT_CONTRACT_ID, "study_day_zero_flag_drift", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/axis_basis/study_day_zero_exists", "value": True}, "PUB_STUDY_DAY_VALUE_MISMATCH"),
        ("PA-159", SUBJECT_CONTRACT_ID, "study_day_calendar_offset_drift", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/events/0/end_endpoint/study_day", "value": 3}, "PUB_STUDY_DAY_VALUE_MISMATCH"),
        ("PA-160", AEMH_CONTRACT_ID, "typed_identity_foreign_entity", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/identity_evidence/1/entity_ref", "value": "fact::foreign"}, "AEMH_IDENTITY_EVIDENCE_MISMATCH"),
        ("PA-161", AEMH_CONTRACT_ID, "typed_identity_locator_content_drift", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/identity_evidence/1/source_locator_content_hash", "value": "0" * 64}, "AEMH_IDENTITY_EVIDENCE_MISMATCH"),
        ("PA-162", AEMH_CONTRACT_ID, "synchronized_later_fact_forgery", "aemh_match_history_valid_base", {"op": "forge_later_fact_lineage", "path": "/", "forged_ref": "fact::reported-ae::forged", "source_locator_ref": "locator::fact::ae1"}, "AEMH_IDENTITY_EVIDENCE_MISMATCH"),
        ("PA-163", "exact-overlay-v0.1", "overlay_root_schema_drift", "exact_overlay_artifact", {"op": "replace", "path": "/schema", "value": "wrong-overlay"}, "PUB_OVERLAY_ARTIFACT_MISMATCH"),
        ("PA-164", "exact-overlay-v0.1", "overlay_runtime_unlock", "exact_overlay_artifact", {"op": "replace", "path": "/unlock_rule/s5_runtime_remains_locked", "value": False}, "PUB_OVERLAY_ARTIFACT_MISMATCH"),
        ("PA-165", "exact-overlay-v0.1", "overlay_unlock_rule_drift", "exact_overlay_artifact", {"op": "replace", "path": "/unlock_rule/contract_acceptance_only_unlocks", "value": "runtime"}, "PUB_OVERLAY_ARTIFACT_MISMATCH"),
        ("PA-166", "exact-overlay-v0.1", "overlay_replacement_source_path", "exact_overlay_artifact", {"op": "replace", "path": "/mapping_replacements/0/replacement_source_path", "value": "foreign:Projection"}, "PUB_OVERLAY_ARTIFACT_MISMATCH"),
        ("PA-167", "exact-overlay-v0.1", "overlay_receipt_variant", "exact_overlay_artifact", {"op": "replace", "path": "/mapping_replacements/0/required_receipt_variant", "value": "subject_temporal"}, "PUB_OVERLAY_ARTIFACT_MISMATCH"),
        ("PA-168", "exact-overlay-v0.1", "overlay_adapter_recipe", "exact_overlay_artifact", {"op": "replace", "path": "/mapping_replacements/0/adaptation_recipe", "value": "foreign.recipe"}, "PUB_OVERLAY_ARTIFACT_MISMATCH"),
        ("PA-169", "source-matrix-v0.1", "source_matrix_producer_path", "source_matrix_artifact", {"op": "replace", "path": "/producer_requirement_contract/0/projection_source", "value": "foreign:Projection"}, "PUB_SOURCE_MATRIX_ARTIFACT_MISMATCH"),
        ("PA-170", "source-matrix-v0.1", "source_matrix_producer_status", "source_matrix_artifact", {"op": "replace", "path": "/entries/16/implementation_status", "value": "implemented"}, "PUB_SOURCE_MATRIX_ARTIFACT_MISMATCH"),
        ("PA-171", "source-matrix-v0.1", "source_matrix_entry_content", "source_matrix_artifact", {"op": "replace", "path": "/entries/0/classification", "value": "reference_only_incomplete_public_authority"}, "PUB_SOURCE_MATRIX_ARTIFACT_MISMATCH"),
        ("PA-172", "manifest-v0.1", "manifest_protected_anchor", "manifest_artifact", {"op": "replace", "path": "/protected_accepted_pins/r5_root_init_sha256", "value": "0" * 64}, "PUB_MANIFEST_PROTECTED_PIN_MISMATCH"),
        ("PA-173", "manifest-v0.1", "manifest_medical_writing_count", "manifest_artifact", {"op": "replace", "path": "/protected_accepted_pins/medical_writing_protected_file_count", "value": 541}, "PUB_MANIFEST_PROTECTED_PIN_MISMATCH"),
        ("PA-174", "manifest-v0.1", "manifest_medical_writing_recipe", "manifest_artifact", {"op": "replace", "path": "/protected_accepted_pins/medical_writing_inventory_contract/relative_path_regex", "value": ".*"}, "PUB_MANIFEST_PROTECTED_PIN_MISMATCH"),
        ("PA-175", "exact-overlay-v0.1", "overlay_row_status", "exact_overlay_artifact", {"op": "replace", "path": "/mapping_replacements/0/implementation_status", "value": "implemented"}, "PUB_OVERLAY_ARTIFACT_MISMATCH"),
        ("PA-176", "source-matrix-v0.1", "source_matrix_entry_producer_path", "source_matrix_artifact", {"op": "replace", "path": "/entries/16/source", "value": "foreign:AuthorityPacket"}, "PUB_SOURCE_MATRIX_ARTIFACT_MISMATCH"),
        ("PA-177", "manifest-v0.1", "manifest_nested_protected_path_pin", "manifest_artifact", {"op": "replace", "path": "/protected_accepted_pins/protected_path_sha256/poc~1medical_monitoring_ai_native_r5~1src~1mm_r5~1__init__.py", "value": "0" * 64}, "PUB_MANIFEST_PROTECTED_PIN_MISMATCH"),
        ("PA-178", "manifest-v0.1", "manifest_medical_writing_aggregate", "manifest_artifact", {"op": "replace", "path": "/protected_accepted_pins/medical_writing_protected_inventory_sha256", "value": "0" * 64}, "PUB_MANIFEST_PROTECTED_PIN_MISMATCH"),
        ("PA-179", "manifest-v0.1", "manifest_runtime_unlock", "manifest_artifact", {"op": "replace", "path": "/runtime_unlock/s5_runtime_locked", "value": False}, "PUB_MANIFEST_CONTRACT_MISMATCH"),
        ("PA-180", "manifest-v0.1", "manifest_unlock_rule", "manifest_artifact", {"op": "replace", "path": "/runtime_unlock/unlocks_only", "value": "runtime"}, "PUB_MANIFEST_CONTRACT_MISMATCH"),
        ("PA-181", SUBJECT_CONTRACT_ID, "subject_projection_schema_version", "subject_temporal_valid_base", {"op": "replace", "path": "/projection/schema_version", "value": "wrong-version"}, "PUB_CONTRACT_VERSION_MISMATCH"),
        ("PA-182", SUBJECT_CONTRACT_ID, "subject_receipt_authority_version", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/authority_contract_version", "value": "wrong-version"}, "PUB_CONTRACT_VERSION_MISMATCH"),
        ("PA-183", SUBJECT_CONTRACT_ID, "subject_parent_audience_contract", "subject_temporal_valid_base", {"op": "replace", "path": "/receipt/audience_contract_id", "value": "r5-v0.3-audience-contract"}, "PUB_AUDIENCE_CONTRACT_MISMATCH"),
        ("PA-184", AEMH_CONTRACT_ID, "aemh_projection_schema_version", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/schema_version", "value": "wrong-version"}, "PUB_CONTRACT_VERSION_MISMATCH"),
        ("PA-185", AEMH_CONTRACT_ID, "aemh_receipt_authority_version", "aemh_match_history_valid_base", {"op": "replace", "path": "/receipt/authority_contract_version", "value": "wrong-version"}, "PUB_CONTRACT_VERSION_MISMATCH"),
        ("PA-186", AEMH_CONTRACT_ID, "aemh_parent_audience_contract", "aemh_match_history_valid_base", {"op": "replace", "path": "/receipt/audience_contract_id", "value": "r5-v0.3-audience-contract"}, "PUB_AUDIENCE_CONTRACT_MISMATCH"),
        ("PA-187", AEMH_CONTRACT_ID, "entry_id_duplicate_within_thread", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/entry_id", "value": "history-entry::ae::1::1"}, "AEMH_ENTRY_ID_DUPLICATE"),
        ("PA-188", AEMH_CONTRACT_ID, "entry_id_duplicate_across_threads", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/1/history_entries/0/entry_id", "value": "history-entry::ae::1::1"}, "AEMH_ENTRY_ID_DUPLICATE"),
        ("PA-189", AEMH_CONTRACT_ID, "withdrawn_without_prior_match", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/event_kind", "value": "withdrawn"}, "AEMH_LIFECYCLE_TRANSITION_INVALID"),
        ("PA-190", AEMH_CONTRACT_ID, "reappeared_without_prior_match", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/1/event_kind", "value": "reappeared"}, "AEMH_LIFECYCLE_TRANSITION_INVALID"),
        ("PA-191", AEMH_CONTRACT_ID, "reappeared_without_withdrawal", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/2/event_kind", "value": "reappeared"}, "AEMH_LIFECYCLE_TRANSITION_INVALID"),
        ("PA-192", AEMH_CONTRACT_ID, "withdrawn_fact_identity_drift", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/2/later_fact_content_identities/0", "value": "0" * 64}, "AEMH_LIFECYCLE_TRANSITION_INVALID"),
        ("PA-193", AEMH_CONTRACT_ID, "duplicate_match_decided", "aemh_match_history_valid_base", {"op": "replace", "path": "/projection/threads/0/history_entries/2/event_kind", "value": "match_decided"}, "AEMH_MATCH_DECISION_DUPLICATE"),
        ("PA-194", "manifest-v0.1", "manifest_no_runtime_test_surface_drift", "manifest_artifact", {"op": "replace", "path": "/no_runtime_test_surface/forbidden_relative_path_regexes/0", "value": "^$"}, "PUB_MANIFEST_CONTRACT_MISMATCH"),
    ]
    for case_id, contract, category, base_key, mutation, error in advanced_specs:
        rows.append(
            {
                "case_id": case_id,
                "origin": "public_authority_specific_contract_case",
                "parent_case_id": None,
                "contract": contract,
                "category": category,
                "precondition": f"valid frozen base input::{base_key}",
                "base_input_key": base_key,
                "fully_reseal_after_mutation": True,
                "single_mutation": mutation,
                "expected_typed_outcome_or_error": f"reject:{error}",
                "forbidden_audience_output": [
                    "mutated_projection",
                    "risk_lifecycle_write",
                ],
                "stage_oracle_contract": {
                    "kind": "contract_tamper_probe",
                    "planned_stage": "contract_verification",
                    "rule_id": f"public_authority.{category}",
                    "test_locator": f"verify_medical_monitoring_r5_s5_public_authority_contract_v0_1::{case_id}",
                    "expected_outcome": f"reject:{error}",
                    "expected_projection": "not_emitted",
                    "required_non_llm_anchor": "deterministic in-memory mutation rejected by verifier",
                },
            }
        )
    return rows


def challenge_registry(parent: dict[str, Any]) -> dict[str, Any]:
    inherited = inherited_challenges(parent)
    public = public_specific_challenges()
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-challenge-registry-v0.1",
        "contract_id": CONTRACT_ID,
        "parent_exact_contract_sha256": SOURCE_PINS[
            "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json"
        ],
        "inherited_case_range": "R5C-101..R5C-164",
        "inherited_cases": inherited,
        "public_authority_specific_cases": public,
        "counts": {"inherited": len(inherited), "public_authority_specific": len(public)},
        "quota_ledger": None,
        "quota_rule": "No second quota ledger. The 64 inherited rows remain owned by the accepted parent 204-row ledger; the additional rows test only receipt/source/history invariants not expressible there.",
    }


def base_inputs() -> dict[str, Any]:
    aemh_previous, aemh_current = aemh_examples()
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-base-inputs-v0.1",
        "contract_id": CONTRACT_ID,
        "accepted_parent_inputs": {
            "protected_accepted_pins": PROTECTED_ACCEPTED_PINS,
            "source_file_sha256": SOURCE_PINS,
        },
        "examples_are_contract_only_not_authority": True,
        "subject_temporal_valid_base": subject_example(),
        "subject_temporal_absent_cutoff_valid_base": subject_example(cutoff_ref=None),
        "subject_temporal_conflicted_valid_base": subject_example(
            uncertain_state="conflicted"
        ),
        "subject_temporal_no_study_day_valid_base": subject_example(
            include_study_day=False
        ),
        "aemh_match_history_previous_base": aemh_previous,
        "aemh_match_history_valid_base": aemh_current,
    }


def review_markdown(
    subject: dict[str, Any],
    aemh: dict[str, Any],
    matrix: dict[str, Any],
    registry: dict[str, Any],
) -> bytes:
    text = f"""# 医学监查 R5-S5 公共权威合同 v0.1

日期：2026-08-19  
状态：`PUBLIC_AUTHORITY_CONTRACT_FROZEN_FOR_INDEPENDENT_REVIEW`  
机器合同：`{SUBJECT_CONTRACT_ID}` 与 `{AEMH_CONTRACT_ID}`

## 1. 边界

本文件只冻结两个未来公共 producer 的 exact contract。它不创建 producer、adapter、validator runtime 或测试，不改写既有 R1–R5，也不启动 8911。当前 R1/R4 访视、Journey、AE/MH 和 R5 S4 对象只按 `source_matrix.json` 复用已有 exact leaves；字典投影、`Any` 字段、synthetic fixture、私有 `_ReportedMatchOutcome` 与 R1 `historical_evidence_refs` 均不得冒充直接公共权威。

本合同本身不签发 `ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1`、`ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1` 或 `ACCEPT_R5_S5_CONTRACT`。即使本合同随后被独立接受，也只解锁另行冻结的 public-authority implementation contract，S5 runtime 仍保持锁定。

## 2. subject-temporal-public-v1

- exact 对象数：{len(subject['objects'])}；closed enums：{len(subject['enums'])}；closed errors：{len(subject['error_codes'])}。
- 唯一 packet 为 `SubjectTemporalAuthorityPacket`，receipt variant 固定 `subject_temporal`。
- project/run/snapshot/cutoff/site/subject/spine、visibility、source-revision/content、locator 和 membership 必须全闭合。
- projection `schema_version` 与 receipt `authority_contract_version` 必须逐字等于 subject schema 的 `schema_version`；receipt `audience_contract_id` 固定为已 pin 的父 R5 常量 `contract.s4.1`，不得使用推造的版本名称。
- visibility 的 evaluation/projectable/hidden member/site 集合必须等于当前 scope 的精确 subject/site universe；source pair 与 locator 必须构成 sorted-unique、无空项、无闲置项的全分区。
- calendar 为默认轴；study day 仅在 exact accepted anchor 存在时生成。名义、实际和非计划访视分开；非计划访视禁止 planned binding/assignment，访视间事件不吸附、不 nearest fallback。
- 验证器扫描 cutoff、visit nominal/actual、event、risk、phase 与 pending mirror 的全部 temporal endpoint；任一 `study_day` 或 study-day 轴均要求同一 membership spine 内的 exact、可投影且有接受来源的 anchor event。
- study-day 数值只由 accepted anchor 的 exact calendar date 推导：anchor=0 时 `study_day=calendar_delta`；anchor=1 时不存在 day 0，delta>=0 使用 `delta+1`、delta<0 使用 `delta`。anchor 只能为 0/1；`study_day_zero_exists` 无 anchor 时必须为 null，有 anchor 时精确等于 anchor 是否为 0，不能自报。
- start/end 各自携带 exact/partial/conflicted/missing、候选值/范围、来源、主轴可投影性；几何固定 point/closed_interval/open_start/open_end。缺失端点不进入主轴，相关对象进入 `pending_date_items`。
- exact/partial/conflicted 候选与范围均执行真实日历解析；range 与 interval 必须有序。partial/conflicted 仅在存在合法有界范围且 `range_projection_authorized=true` 时才允许 `main_axis_projectable=true`。
- partial/conflicted 的 range 必须等于候选值展开后的精确 envelope；相同非缺失端点只能是 point，closed interval 必须存在可区分的有序端点。pending item 必须与目标 endpoint/domain/source 完全镜像，并精确覆盖所有缺失或不可投影的 visit/event/risk/phase，禁止遗漏、重复或额外项。
- 八域固定且恰好各一 track：{', '.join(DOMAINS)}。`applicable` 当且仅当该域实际发出 event/risk member；`not_applicable`/`not_provided` 必须 refs 为空且不得与该域成员共存。unknown 与 OTHER fail-closed。
- 每个已发出的 event 自身也必须是 `applicable`，并与对应 applicable domain track 精确一致；event-level `not_applicable`/`not_provided` 只能通过该域无 event/risk member 且 track refs 为空表达。
- 每个 source locator 必须由实际 axis/member/endpoint 消费；仅出现在 receipt pair、membership 或 evaluation identity 中不能掩盖闲置 locator。

## 3. aemh-match-history-public-v1

- exact 对象数：{len(aemh['objects'])}；closed enums：{len(aemh['enums'])}；closed errors：{len(aemh['error_codes'])}。
- 唯一 packet 为 `AEMHMatchHistoryAuthorityPacket`，receipt variant 固定 `aemh_match_history`。
- projection `schema_version` 与 receipt `authority_contract_version` 必须逐字等于 AE/MH schema 的 `schema_version`；receipt audience 同样固定为父 R5 `contract.s4.1`。
- 每个 thread 从 immutable `reminder_created` 开始；`match_decided` 只允许 exact/ambiguous/rejected；withdrawn 与 reappeared 只能 append。
- later fact 同时保留 ref 与 content identity；证据集合只能单调扩张；原 reminder 和全部历史不可删除或重写。
- 每个 thread 恰好一个 seq=1 的 `reminder_created`，`original_reminder_ref` 必须精确指向它；后续 reminder fail-closed。
- `entry_id` 在整个 projection 全局唯一；每个 `original_reminder_ref` 必须在全局唯一解析，并解析到本 thread 唯一的 seq=1 reminder。
- exact/ambiguous 决策必须保留 candidate 与 later-fact identity evidence，rejected 必须保留非空 considered identity evidence；三种决策均必须保留 source evidence locator。
- identity evidence 为 exact typed object，分别标注 candidate/later_fact/considered_fact；entity ref/content identity 必须绑定 thread candidate 或 entry later fact，并同时绑定 entry snapshot 对应的实际 source locator ref、locator content hash 与 raw payload hash。整条 later-fact ref/content/membership 同步改写但没有相同 accepted locator authority entity 的输入仍 fail-closed。
- 非初始 projection 必须绑定 previous projection ref/hash 与逐 thread accepted prefix seq/head/content；验证器将前一包与当前包机械比较，拒绝跨版本前缀重写，而不只验证单包 hash chain。
- previous/current thread ref 集合与 prefix-anchor ref 集合必须双向相等；跨版本 project/site/subject/domain/candidate/reminder identity 必须稳定，禁止 thread 删除、phantom prefix 或候选冲突。
- history snapshot lineage 同样闭合：保留前缀逐字保留既有 snapshot，新增 suffix entry 必须使用当前 scope snapshot，任何 foreign snapshot 均拒绝。
- 每个 thread 最多一次 `match_decided`。withdrawn 必须引用本 thread 此前 match_decided 的同一 later-fact ref/content identity；reappeared 仅可发生在该 exact fact 已 withdrawn 后，并保持 identity 不变。无 match 的 withdrawn/reappeared、无 withdrawal 的 reappeared、重复 match 均 fail-closed。
- AE/MH locator 必须由 cutoff、thread evidence 或 history retained evidence 实际消费；receipt/source-pair/membership/evaluation-only 引用不构成消费。
- 每条 history entry 的 `risk_lifecycle_effect` closed enum 只有 `none`。补录/撤回/再出现均不得自动关闭、解决、降级或改写风险。

## 4. Hash、receipt 与来源

所有 hash 使用 UTF-8 canonical JSON、sorted object keys、无多余空白与 SHA-256；数组按 schema 声明区分 semantic order 与 set-like order。projection 先独立封口，receipt 再绑定 projection id/hash、visibility closure、evaluation content identities 和 source revision-content pairs，packet 最后绑定 receipt/projection hashes。任一身份、来源、顺序、成员或 hash 漂移均 fail-closed。

`source_matrix.json` 共 {len(matrix['entries'])} 行，明确区分 reusable upstream leaves、reference-only projections 与两项 `contract_only_not_implemented` external producer requirements。

`exact_overlay.json` 的 `(target,parent_deferred_contract)` 必须与 accepted parent 的 deferred `(target,deferred_contract)` 构成精确 sorted-unique 集合，数量相等不足以通过，重复、遗漏、替换或乱序均 fail-closed。

Verifier 独立重建 overlay 的 exact root、unlock rule 和每一 mapping row，逐项核对 replacement source path、receipt variant、implementation status 与父 mapping recipe。`source_matrix.json` 的 root、17 个有序 entry、classification vocabulary、两个 future producer packet/projection path 和 `contract_only_not_implemented` status 由独立 canonical hash 与 exact producer contract 双重冻结，不依赖 generator 自证。

Manifest 的全部 protected pins 均解析到实际路径并重新计算。医学写作边界固定为 `deploy/frontend/packages/runtime/services` 五个 roots 下 relative path 匹配 `medical[-_]writing` 的 regular files；仅对匹配文件读取 bytes，按 UTF-8 relative POSIX path byte order 排序，逐项拼接 `path + NUL + lowercase sha256(file bytes) + LF` 后再 SHA-256；期望 count=542 与 aggregate 均必须匹配。

Contract stage 的 no-runtime/no-test 文件面同样冻结在 manifest：只扫描 `poc/medical_monitoring_ai_native_r5/src/mm_r5` 与 `poc/medical_monitoring_ai_native_r5/tests` 的路径名；任何 subject-temporal public、AE/MH match-history public 或 `s5_*` module/test 的 regular file 或 symlink 均 fail-closed。该扫描在 verifier main 的 normal/O2 路径中执行，不读取匹配文件内容。

## 5. Challenge registry

`challenge_registry.json` 原样投影已接受父合同 `R5C-101..164` 共 {registry['counts']['inherited']} 行，不创建第二 quota ledger；另有 {registry['counts']['public_authority_specific']} 个针对 locator/source/visibility/cutoff/date/geometry/pending/duplicate/reference/evaluation/history/prefix/cross-version identity 的 bounded contract tamper cases。合同阶段只冻结规范并执行 deterministic in-memory tamper rejection，不宣称未来 producer/runtime 行为已实现。

## 6. 生成与验证

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py --check
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py
PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py
```

Verifier 必须检查 exact artifact set、全部 protected path/SHA/count/aggregate、parent/source SHA、schema exact keys/types/enums/nullability/cardinality、sorted-unique exact-set/source-partition closure、cutoff 双态、真实日历/range/geometry/pending/reference、study-day 算法、typed AE/MH identity evidence、跨版本 thread/prefix/stable identity、overlay/source-matrix exact artifact consistency、evaluation identity 闭合、hash recipes、64+{registry['counts']['public_authority_specific']} challenge rows、脚本无 Python assertion statement，并执行 tamper-failure gates。任何失败均非零退出。
"""
    return text.encode("utf-8")


def check_source_pins() -> None:
    for relative, expected in SOURCE_PINS.items():
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing pinned source: {relative}")
        actual = sha256_bytes(path.read_bytes())
        if actual != expected:
            raise RuntimeError(
                f"pinned source drift: {relative}: expected={expected} actual={actual}"
            )


def build_bundle() -> dict[Path, bytes]:
    check_source_pins()
    parent = json.loads(PARENT_CONTRACT_PATH.read_text(encoding="utf-8"))
    subject = subject_schema()
    aemh = aemh_schema()
    matrix = source_matrix()
    registry = challenge_registry(parent)
    overlay_doc = overlay(parent)
    inputs = base_inputs()
    bundle: dict[Path, bytes] = {
        ARTIFACT_DIR / "subject_temporal_schema.json": pretty_json(subject),
        ARTIFACT_DIR / "aemh_match_history_schema.json": pretty_json(aemh),
        ARTIFACT_DIR / "exact_overlay.json": pretty_json(overlay_doc),
        ARTIFACT_DIR / "source_matrix.json": pretty_json(matrix),
        ARTIFACT_DIR / "challenge_registry.json": pretty_json(registry),
        ARTIFACT_DIR / "base_inputs.json": pretty_json(inputs),
        REVIEW_PATH: review_markdown(subject, aemh, matrix, registry),
    }
    exact_paths = [
        str(REVIEW_PATH.relative_to(ROOT)),
        *[
            str((ARTIFACT_DIR / name).relative_to(ROOT))
            for name in (
                "subject_temporal_schema.json",
                "aemh_match_history_schema.json",
                "exact_overlay.json",
                "source_matrix.json",
                "challenge_registry.json",
                "base_inputs.json",
                "manifest.json",
            )
        ],
        str(GENERATOR_PATH.relative_to(ROOT)),
        str(VERIFIER_PATH.relative_to(ROOT)),
    ]
    artifact_pins = {
        str(path.relative_to(ROOT)): sha256_bytes(data)
        for path, data in bundle.items()
    }
    artifact_pins[str(GENERATOR_PATH.relative_to(ROOT))] = sha256_bytes(
        GENERATOR_PATH.read_bytes()
    )
    if not VERIFIER_PATH.is_file():
        raise RuntimeError(f"verifier must exist before generation: {VERIFIER_PATH}")
    artifact_pins[str(VERIFIER_PATH.relative_to(ROOT))] = sha256_bytes(
        VERIFIER_PATH.read_bytes()
    )
    manifest_core = {
        "schema": "medical-monitoring-r5-s5-public-authority-manifest-v0.1",
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "exact_artifact_paths": sorted(exact_paths),
        "artifact_raw_sha256": dict(sorted(artifact_pins.items())),
        "manifest_hash_recipe": "sha256(canonical_json(all manifest fields except manifest_content_hash))",
        "source_file_sha256": SOURCE_PINS,
        "protected_accepted_pins": PROTECTED_ACCEPTED_PINS,
        "no_runtime_test_surface": NO_RUNTIME_TEST_SURFACE,
        "parent_challenge_projection": {
            "parent_range": "R5C-101..R5C-164",
            "count": 64,
            "quota_ledger": None,
        },
        "public_authority_specific_case_count": registry["counts"][
            "public_authority_specific"
        ],
        "runtime_unlock": {
            "unlocks_only": "later_public_authority_implementation_contract",
            "does_not_satisfy": [
                "ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1",
                "ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1",
                "ACCEPT_R5_S5_CONTRACT",
            ],
            "s5_runtime_locked": True,
        },
        "python_assert_statements_allowed": False,
    }
    manifest = dict(manifest_core)
    manifest["manifest_content_hash"] = canonical_hash(manifest_core)
    bundle[ARTIFACT_DIR / "manifest.json"] = pretty_json(manifest)
    return bundle


def write_or_check(bundle: dict[Path, bytes], check: bool) -> None:
    mismatches = []
    for path, expected in bundle.items():
        if check:
            if not path.is_file():
                mismatches.append(f"missing:{path.relative_to(ROOT)}")
                continue
            actual = path.read_bytes()
            if actual != expected:
                mismatches.append(f"drift:{path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if mismatches:
        raise RuntimeError("generator --check failed: " + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    bundle = build_bundle()
    write_or_check(bundle, args.check)
    mode = "check" if args.check else "write"
    print(f"PUBLIC_AUTHORITY_CONTRACT_GENERATOR_OK mode={mode} files={len(bundle)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
