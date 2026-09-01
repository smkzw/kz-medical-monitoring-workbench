"""Generate the R5-S5 temporal-projection authority delta v0.1.

The generator owns only the four machine artifacts and the manifest named by
the task.  It derives the 272 public output leaves from the already accepted
17/13 object schemas; rejected implementation snapshots are pinned as negative
evidence and are never used as an authority or expected-output source.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import pathlib
import tempfile
import unicodedata
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1"
CONTRACT_ID = "medical-monitoring-r5-s5-temporal-projection-authority-delta-v0.1"
SCHEMA_VERSION = "1.0.0"
AUTHORITY_SCOPE = "synthetic_test_only"
EXPECTED_EXTERNAL_REGISTRY_ROOT_CONTENT_HASH = "580d367783f8a00e68e8779fceec9146ddadd2bc3dd0040d26937d415b0589b3"
EXPECTED_EXTERNAL_REGISTRY_SECTION_CANONICAL_SHA256 = "65e2d571ba6858c65c2a82957639968b8f00431f2df56549a4c09f55733832cd"
EXPECTED_ACCEPTED_RECORD_CONTENT_HASH = "295a916100ea53efe816fc79ae818fc4bb0ef38a75eaaf258f3a58e314cbf391"
EXPECTED_SCHEMA_BASELINE_CONTENT_HASH = "9f2784b14c7e9f1ac6d151d340f98b834e449185af3c0ffcc0fd32f0a93c197c"
EXPECTED_ACCEPTED_RECIPE_REGISTRY_CONTENT_HASH = "91687b6d7aa7acb3d0fa24732e2872d81e7ec597c76a9d4d863dfdab40f84e3a"
EXPECTED_AUTHORITY_OUTPUT_REGISTRY_CONTENT_HASH = "2b92462366004c46bd460927514627d209cc608f3cf23688b8501ac03fad3607"
EXPECTED_RECIPE_AUTHORITY_BINDING_REGISTRY_CONTENT_HASH = "3bce92047ffb6d3173d1e22dbc7c59db922c4a4e75f7cf602c31511f4f71c463"
EXPECTED_AEMH_DECISION_HEAD_HASH = "50faee4683e03e6641ed85eb1b9572b979fcf8f2f784476beb6ab34d433ca984"
EXPECTED_EVIDENCE_BINDING_HASH = "92cd8dc1b071655a86be603b35cfbb322b2122c6bcc3f4d76a312e5f2377a7bb"
EXPECTED_DAG_PACKET_HASH = "996f13f1455794b7457e5489a611089f5eaf96b4d3c23c65522b47006a0c5d52"
EXPECTED_DAG_RECEIPT_HASH = "6fd02b0e204b94caebb27931724079032b1614486a277bdbc96c7b4d3f7f9aa3"
EXPECTED_VISIBILITY_HASH = "d7c9c616eaa8a34abc7acd49f9cdc0132c21383aaf3d375d98ccc80875003840"

IR_VALUE_TYPES = (
    "string",
    "integer",
    "boolean",
    "date",
    "sha256",
    "string_list",
    "integer_list",
    "date_list",
    "sha256_list",
    "external_candidate_bundle",
    "external_registry_root",
)
TRANSFORM_OPS = (
    "identity",
    "sorted_unique",
    "set_union",
    "count",
    "study_day",
    "range_envelope",
    "lookup_parallel",
    "if_empty_label",
    "prefix_suffix",
    "sha256_join",
    "resolve_external_record",
    "all_equal",
)
CONDITION_OPS = (
    "equal",
    "exact_count",
    "list_equal",
    "set_partition",
    "disjoint",
    "member_of",
    "date_ordered",
    "prefix",
    "occurrence_at_most",
    "contiguous_integers",
    "all_items_equal",
    "external_registry_match",
    "accepted_record_match",
    "candidate_chain_valid",
    "cutoff_state_compatible",
    "endpoint_state_geometry_compatible",
    "unscheduled_binding_valid",
    "domain_state_compatible",
    "empty",
    "sha256_join_matches",
    "same_length",
    "exact_eight_join",
    "locator_partition",
    "allowed_transition",
    "roles_exact",
)

SELF_HASH_FIELDS = {
    "TemporalAuthorityScopeIdentity": "scope_content_hash",
    "TemporalProjectionAuthorityRegistry": "registry_content_hash",
    "TemporalProjectionAcceptanceReceipt": "receipt_content_hash",
    "PublicScopeUniverseAuthority": "universe_content_hash",
    "RecordNodeStableIdentityBinding": "binding_content_hash",
    "CutoffEndpointBindingAuthority": "binding_content_hash",
    "SourceLocatorRevisionBinding": "binding_content_hash",
    "TemporalMemberAuthorityRecord": "authority_content_hash",
    "TemporalEndpointAuthorityRecord": "endpoint_content_hash",
    "TemporalAxisAuthorityRecord": "axis_content_hash",
    "VisitProjectionBinding": "binding_content_hash",
    "EventProjectionBinding": "binding_content_hash",
    "PhaseProjectionBinding": "binding_content_hash",
    "RiskProjectionBinding": "binding_content_hash",
    "DomainApplicabilityAuthorityRecord": "authority_content_hash",
    "AEMHAppendDecisionAuthorityRecord": "decision_content_hash",
    "AEMHDecisionAuthorityRegistry": "registry_content_hash",
    "AEMHEvidenceBindingAuthority": "binding_content_hash",
    "AEMHThreadMembershipAuthority": "authority_content_hash",
    "PhaseLabelPolicy": "policy_content_hash",
    "TimezoneDayZeroPolicy": "policy_content_hash",
    "DateStateRangeProjectionPolicy": "policy_content_hash",
    "EmptyDomainApplicabilityPolicy": "policy_content_hash",
    "AEMHTransitionPolicy": "policy_content_hash",
}

PATHS = (
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_20260820_context.md",
    "reviews/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1_20260820.md",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/schema.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/source_matrix_delta.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/recipe_registry.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/challenge_registry.json",
    "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1.py",
    "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1.py",
)

PARENT_MANIFEST = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json"
SUBJECT_SCHEMA = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json"
AEMH_SCHEMA = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json"
SEMANTIC_MANIFEST = "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json"
SEMANTIC_ACCEPTANCE = "context/medical_monitoring_r5_s5_semantic_authority_delta_acceptance_record_20260820.md"
PARENT_ACCEPTANCE = "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md"
REJECTION_RECORD = "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_2_rejection_record_20260820.md"

IDENTITY_FIELDS = (
    "project_ref",
    "run_ref",
    "snapshot_ref",
    "cutoff_ref",
    "site_ref",
    "subject_ref",
)
S4_JOIN_FIELDS = (
    "project_ref",
    "run_ref",
    "snapshot_ref",
    "cutoff_ref",
    "site_ref",
    "subject_ref",
    "risk_ref",
    "spine_ref",
)
DOMAINS = (
    "ae",
    "mh",
    "cm",
    "ip",
    "lab_exam",
    "hospital_procedure",
    "symptom_efficacy",
    "protocol_compliance",
)

RECIPE_AUTHORITY_REFS = {
    "recipe.external_registry_receipt_resolution": ["authority:TemporalAuthorityScopeIdentity", "authority:TemporalProjectionAcceptanceReceipt", "authority:TemporalProjectionAuthorityRegistry"],
    "recipe.cutoff_exact_present_absent": ["authority:CutoffEndpointBindingAuthority"],
    "recipe.visibility_universe_and_stable_bridge": ["authority:PublicScopeUniverseAuthority", "authority:TemporalMemberAuthorityRecord"],
    "recipe.locator_total_consumption_revision_partition": ["authority:SourceLocatorRevisionBinding"],
    "recipe.temporal_axis_timezone_day_zero": ["authority:TemporalAxisAuthorityRecord"],
    "recipe.endpoint_state_range_main_axis": ["authority:TemporalEndpointAuthorityRecord"],
    "recipe.visit_assignment_actual_bundle_encounter": ["authority:VisitProjectionBinding"],
    "recipe.event_exact_activity_binding": ["authority:EventProjectionBinding"],
    "recipe.phase_binding_accepted_zh_lexicon": ["authority:PhaseProjectionBinding"],
    "recipe.risk_s4_eight_identity_endpoint_binding": ["authority:RiskProjectionBinding"],
    "recipe.domain_applicable_or_controlled_empty": ["authority:DomainApplicabilityAuthorityRecord"],
    "recipe.pending_union_from_unprojectable_targets": [],
    "recipe.aemh_append_only_decision_registry": ["authority:AEMHAppendDecisionAuthorityRecord", "authority:AEMHDecisionAuthorityRegistry"],
    "recipe.aemh_joint_evidence_binding": ["authority:AEMHEvidenceBindingAuthority"],
    "recipe.aemh_thread_membership": ["authority:AEMHThreadMembershipAuthority"],
    "recipe.aemh_prefix_transition_closure": [],
    "recipe.upstream_roots_before_hashes_containers_packets": ["authority:TemporalMemberAuthorityRecord"],
    "recipe.parent_semantic_snapshot_immutability": [],
}


def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite number")
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, tuple):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                raise TypeError("canonical object keys must be strings")
            normalized = unicodedata.normalize("NFC", key)
            if normalized in out:
                raise ValueError("duplicate normalized key")
            out[normalized] = canonicalize(value[key])
        return out
    raise TypeError(f"unsupported canonical type: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def f(type_name: str, *, nullable: bool = False, cardinality: str = "one", constraints: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "type": type_name,
        "nullable": nullable,
        "cardinality": cardinality,
        "constraints": constraints or {},
    }


def obj(
    properties: dict[str, dict[str, Any]],
    *,
    optional: tuple[str, ...] = (),
    conditional_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not set(optional).issubset(properties):
        raise ValueError("optional field is not a property")
    return {
        "additional_properties": False,
        "required": [name for name in properties if name not in optional],
        "optional": list(optional),
        "properties": properties,
        "conditional_rules": conditional_rules or [],
    }


def scope_field() -> dict[str, Any]:
    return f("TemporalAuthorityScopeIdentity")


def build_schema() -> dict[str, Any]:
    enums = {
        "authority_scope": [AUTHORITY_SCOPE],
        "acceptance_state": ["accepted", "rejected"],
        "cutoff_state": ["present", "absent"],
        "visibility_state": ["projectable", "hidden", "not_evaluable"],
        "member_kind": ["visit", "event", "phase", "risk"],
        "endpoint_owner_field": ["start", "end", "nominal", "actual", "cutoff", "day_zero"],
        "date_state": ["exact", "partial", "conflicted", "missing"],
        "date_geometry": ["point", "closed_interval", "open_start", "open_end"],
        "axis_mode": ["calendar", "study_day"],
        "day_zero_convention": ["anchor_is_day_zero", "anchor_is_day_one"],
        "visit_kind": ["nominal", "actual", "unscheduled"],
        "domain": list(DOMAINS),
        "applicability_state": ["applicable", "not_applicable", "not_provided"],
        "aemh_domain": ["ae", "mh"],
        "history_event_kind": ["reminder_created", "match_decided", "withdrawn", "reappeared"],
        "match_state": ["exact", "ambiguous", "rejected"],
        "identity_evidence_kind": ["candidate", "later_fact", "considered_fact"],
        "risk_lifecycle_effect": ["none"],
        "source_locator_variant": ["r4_source_locator", "d08_source_locator"],
        "phase_code": ["screening", "baseline", "treatment", "follow_up", "unscheduled"],
        "empty_domain_decision": ["not_applicable", "not_provided"],
        "recipe_cardinality": ["exact_one", "zero_or_one", "one_or_more", "exact_set", "total_partition"],
        "ordering": ["scalar", "semantic", "sorted_unique"],
        "ir_value_type": list(IR_VALUE_TYPES),
        "recipe_transform_op": list(TRANSFORM_OPS),
        "recipe_condition_op": list(CONDITION_OPS),
        "recipe_ref_kind": ["input", "node", "manifest"],
        "recipe_input_source": ["fixture", "manifest_pin"],
        "canonicalization_profile": ["utf8_nfc_canonical_json_sorted_keys_compact_no_nan"],
        "authority_projection_op": ["direct_field", "derive_value", "project_record", "assemble_sorted_records", "canonical_hash", "project_contract"],
        "authority_contract_id": ["subject-temporal-public-v1", "aemh-match-history-public-v1"],
        "authority_derive_transform": ["select_contract_projection_id"],
        "authority_assembly_cardinality": ["exact_one_or_more"],
        "output_cardinality": ["one", "many"],
        "hash_mode": ["none", "explicit_sha256_join_nodes"],
        "mutation_target_kind": ["coverage_ledger", "coverage_mapping", "positive_fixture_input", "positive_fixture_expected_output", "positive_fixture", "accepted_record_bundle", "accepted_recipe_bundle", "accepted_recipe_registry", "schema_baseline", "authority_fixture_catalog", "authority_mapping_fixture", "authority_fixture", "authority_output_registry", "recipe_authority_binding_registry"],
        "mutation_op": ["replace", "append", "remove", "copy"],
        "probe_kind": ["coverage_leaf_delete", "semantic_typed_mutation"],
    }

    objects: dict[str, Any] = {}
    objects["TemporalAuthorityScopeIdentity"] = obj(
        {
            "project_ref": f("string", constraints={"min_length": 1}),
            "run_ref": f("string", constraints={"min_length": 1}),
            "snapshot_ref": f("string", constraints={"min_length": 1}),
            "cutoff_ref": f("string", nullable=True),
            "cutoff_state": f("enum:cutoff_state"),
            "site_ref": f("string", constraints={"min_length": 1}),
            "subject_ref": f("string", constraints={"min_length": 1}),
            "spine_ref": f("string", constraints={"min_length": 1}),
            "scope_content_hash": f("sha256"),
        },
        conditional_rules=[
            {"when": {"cutoff_state": "present"}, "requires_non_null": ["cutoff_ref"]},
            {"when": {"cutoff_state": "absent"}, "requires_null": ["cutoff_ref"]},
        ],
    )
    objects["TemporalProjectionAuthorityRegistry"] = obj(
        {
            "registry_id": f("string", constraints={"const": "registry:r5-s5:synthetic-temporal-projection-authority:20260820"}),
            "authority_scope": f("enum:authority_scope"),
            "non_clinical": f("boolean", constraints={"const": True}),
            "scope_identity": scope_field(),
            "authority_record_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "policy_package_refs": f("string", cardinality="many", constraints={"min_items": 5, "sorted_unique": True}),
            "subject_projection_id": f("string", constraints={"min_length": 1}),
            "aemh_projection_id": f("string", constraints={"min_length": 1}),
            "registry_content_hash": f("sha256"),
        }
    )
    objects["TemporalProjectionAcceptanceReceipt"] = obj(
        {
            "receipt_id": f("string", constraints={"min_length": 1}),
            "registry_id": f("string", constraints={"min_length": 1}),
            "registry_content_hash": f("sha256"),
            "accepted_record_ref": f("string", constraints={"min_length": 1}),
            "accepted_record_content_hash": f("sha256"),
            "candidate_registry_content_hash": f("sha256"),
            "authority_scope": f("enum:authority_scope"),
            "non_clinical": f("boolean", constraints={"const": True}),
            "scope_identity": scope_field(),
            "receipt_content_hash": f("sha256"),
        }
    )
    objects["PublicScopeUniverseAuthority"] = obj(
        {
            "universe_ref": f("string"),
            "scope_identity": scope_field(),
            "evaluation_node_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "projectable_node_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "hidden_node_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "evaluation_member_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "projectable_member_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "hidden_member_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "evaluation_site_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "projectable_site_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "hidden_site_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "visibility_state": f("enum:visibility_state"),
            "visibility_decision_id": f("string", constraints={"min_length": 1}),
            "visibility_decision_hash": f("sha256"),
            "deep_link_eligible": f("boolean"),
            "coverage_proof_ref": f("string"),
            "universe_content_hash": f("sha256"),
        }
    )
    objects["RecordNodeStableIdentityBinding"] = obj(
        {
            "binding_ref": f("string"),
            "scope_identity": scope_field(),
            "record_node_ref": f("string"),
            "stable_member_ref": f("string"),
            "stable_site_ref": f("string"),
            "source_record_ref": f("string"),
            "source_locator_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "binding_content_hash": f("sha256"),
        }
    )
    objects["CutoffEndpointBindingAuthority"] = obj(
        {
            "binding_ref": f("string"),
            "scope_identity": scope_field(),
            "cutoff_state": f("enum:cutoff_state"),
            "monitoring_run_ref": f("string"),
            "time_ref": f("string", nullable=True),
            "exact_date": f("date", nullable=True),
            "source_locator_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "source_revision_binding_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "absence_acceptance_ref": f("string", nullable=True),
            "coverage_proof_ref": f("string"),
            "binding_content_hash": f("sha256"),
        },
        conditional_rules=[
            {"when": {"cutoff_state": "present"}, "requires_non_null": ["time_ref", "exact_date"], "requires_min_items": {"source_locator_refs": 1}},
            {"when": {"cutoff_state": "absent"}, "requires_null": ["time_ref", "exact_date"], "requires_non_null": ["absence_acceptance_ref"]},
        ],
    )
    objects["SourceLocatorRevisionBinding"] = obj(
        {
            "binding_ref": f("string"),
            "scope_identity": scope_field(),
            "locator_ref": f("string"),
            "locator_variant": f("enum:source_locator_variant"),
            "source_revision_ref": f("string"),
            "source_revision_content_hash": f("sha256"),
            "source_file_ref": f("string"),
            "record_ref": f("string"),
            "field_path": f("string"),
            "canonical_location": f("string", nullable=True),
            "table_semantic": f("string", nullable=True),
            "authority_entity_kind": f("string", nullable=True),
            "authority_entity_ref": f("string", nullable=True),
            "raw_payload_hash": f("sha256"),
            "binding_content_hash": f("sha256"),
        }
    )
    objects["TemporalMemberAuthorityRecord"] = obj(
        {
            "authority_ref": f("string"),
            "scope_identity": scope_field(),
            "member_kind": f("enum:member_kind"),
            "member_ref": f("string"),
            "stable_member_ref": f("string"),
            "record_node_binding_ref": f("string"),
            "endpoint_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "event_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "visit_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "phase_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "risk_anchor_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "pending_date_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "pending_item_kind": f("string", constraints={"const": "event"}),
            "pending_domain": f("string", constraints={"const": "ae"}),
            "pending_item_ref": f("string", constraints={"min_length": 1}),
            "pending_target_content_hash": f("sha256"),
            "source_locator_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "authority_content_hash": f("sha256"),
        }
    )
    objects["TemporalEndpointAuthorityRecord"] = obj(
        {
            "endpoint_ref": f("string"),
            "scope_identity": scope_field(),
            "owner_kind": f("enum:member_kind"),
            "owner_ref": f("string"),
            "owner_field": f("enum:endpoint_owner_field"),
            "date_state": f("enum:date_state"),
            "geometry": f("enum:date_geometry"),
            "exact_date": f("date", nullable=True),
            "candidate_values": f("partial_date", cardinality="many", constraints={"sorted_unique": True}),
            "range_start": f("date", nullable=True),
            "range_end": f("date", nullable=True),
            "range_projection_authorized": f("boolean"),
            "main_axis_projectable": f("boolean"),
            "study_day": f("integer", nullable=True),
            "source_locator_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "absence_acceptance_ref": f("string", nullable=True),
            "coverage_proof_ref": f("string"),
            "endpoint_content_hash": f("sha256"),
        },
        conditional_rules=[
            {"when": {"date_state": "exact"}, "requires_non_null": ["exact_date"], "requires": {"geometry": "point", "main_axis_projectable": True}},
            {"when": {"date_state": "partial"}, "requires_null": ["exact_date"], "requires_min_items": {"candidate_values": 1}},
            {"when": {"date_state": "conflicted"}, "requires_null": ["exact_date"], "requires_min_items": {"candidate_values": 2}},
            {"when": {"date_state": "missing"}, "requires_null": ["exact_date", "range_start", "range_end"], "requires_non_null": ["absence_acceptance_ref"], "requires": {"main_axis_projectable": False, "range_projection_authorized": False}},
        ],
    )
    objects["TemporalAxisAuthorityRecord"] = obj(
        {
            "axis_ref": f("string"),
            "scope_identity": scope_field(),
            "default_axis_mode": f("enum:axis_mode"),
            "timezone": f("string", constraints={"const": "Asia/Shanghai"}),
            "day_zero_convention": f("enum:day_zero_convention"),
            "study_day_anchor_event_ref": f("string", nullable=True),
            "study_day_anchor_endpoint_ref": f("string", nullable=True),
            "study_day_zero_exists": f("boolean", nullable=True),
            "source_locator_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "axis_content_hash": f("sha256"),
        }
    )
    objects["VisitProjectionBinding"] = obj(
        {
            "binding_ref": f("string"),
            "scope_identity": scope_field(),
            "visit_kind": f("enum:visit_kind"),
            "visit_ref": f("string"),
            "planned_visit_ref": f("string", nullable=True),
            "actual_bundle_ref": f("string", nullable=True),
            "actual_encounter_ref": f("string", nullable=True),
            "accepted_assignment_ref": f("string", nullable=True),
            "nominal_endpoint_ref": f("string", nullable=True),
            "actual_endpoint_ref": f("string", nullable=True),
            "phase_ref": f("string", nullable=True),
            "source_locator_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "binding_content_hash": f("sha256"),
        },
        conditional_rules=[
            {"when": {"visit_kind": "unscheduled"}, "requires_null": ["planned_visit_ref", "accepted_assignment_ref", "nominal_endpoint_ref"], "requires_non_null": ["actual_encounter_ref", "actual_endpoint_ref"]},
        ],
    )
    objects["EventProjectionBinding"] = obj(
        {
            "binding_ref": f("string"),
            "scope_identity": scope_field(),
            "event_ref": f("string"),
            "actual_activity_ref": f("string"),
            "actual_encounter_ref": f("string", nullable=True),
            "visit_ref": f("string", nullable=True),
            "start_endpoint_ref": f("string"),
            "end_endpoint_ref": f("string", nullable=True),
            "semantic_event_authority_ref": f("string"),
            "semantic_domain": f("string", constraints={"const": "ae"}),
            "semantic_subtype": f("string", constraints={"const": "ae"}),
            "applicability_state": f("enum:applicability_state"),
            "geometry": f("enum:date_geometry"),
            "risk_anchor_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "event_content_identity": f("sha256"),
            "source_locator_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "binding_content_hash": f("sha256"),
        }
    )
    objects["PhaseProjectionBinding"] = obj(
        {
            "binding_ref": f("string"),
            "scope_identity": scope_field(),
            "phase_ref": f("string"),
            "phase_code": f("enum:phase_code"),
            "phase_label_policy_ref": f("string"),
            "start_endpoint_ref": f("string"),
            "end_endpoint_ref": f("string", nullable=True),
            "schedule_anchor_ref": f("string"),
            "phase_label_zh": f("string", constraints={"min_length": 1}),
            "geometry": f("enum:date_geometry"),
            "source_locator_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "binding_content_hash": f("sha256"),
        }
    )
    objects["RiskProjectionBinding"] = obj(
        {
            "binding_ref": f("string"),
            "scope_identity": scope_field(),
            "s4_identity_join": f("S4IdentityJoin"),
            "risk_ref": f("string"),
            "event_ref": f("string", nullable=True),
            "visit_ref": f("string", nullable=True),
            "start_endpoint_ref": f("string"),
            "end_endpoint_ref": f("string", nullable=True),
            "risk_taxonomy_authority_ref": f("string"),
            "severity_authority_ref": f("string"),
            "semantic_domain": f("string", constraints={"const": "ae"}),
            "geometry": f("enum:date_geometry"),
            "risk_content_identity": f("sha256"),
            "risk_type_zh": f("string", constraints={"min_length": 1}),
            "severity": f("string", constraints={"const": "medium"}),
            "source_locator_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "binding_content_hash": f("sha256"),
        }
    )
    objects["S4IdentityJoin"] = obj({name: f("string", nullable=(name == "cutoff_ref")) for name in S4_JOIN_FIELDS})
    objects["DomainApplicabilityAuthorityRecord"] = obj(
        {
            "authority_ref": f("string"),
            "scope_identity": scope_field(),
            "domain": f("enum:domain"),
            "member_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "event_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "risk_anchor_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "applicability_state": f("enum:applicability_state"),
            "empty_state_authority_ref": f("string", nullable=True),
            "coverage_proof_ref": f("string"),
            "authority_content_hash": f("sha256"),
        },
        conditional_rules=[
            {"when": {"applicability_state": "applicable"}, "requires_min_items": {"member_refs": 1}, "requires_null": ["empty_state_authority_ref"]},
            {"when_in": {"applicability_state": ["not_applicable", "not_provided"]}, "requires_max_items": {"member_refs": 0}, "requires_non_null": ["empty_state_authority_ref"]},
        ],
    )
    objects["AEMHAppendDecisionAuthorityRecord"] = obj(
        {
            "decision_ref": f("string"),
            "entry_id": f("string", constraints={"min_length": 1}),
            "scope_identity": scope_field(),
            "thread_ref": f("string"),
            "seq": f("integer", constraints={"minimum": 1}),
            "event_kind": f("enum:history_event_kind"),
            "match_state": f("enum:match_state", nullable=True),
            "reason_code": f("string"),
            "snapshot_ref": f("string"),
            "candidate_ref": f("string"),
            "later_fact_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "later_fact_content_identities": f("sha256", cardinality="many", constraints={"sorted_unique": True}),
            "evidence_binding_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "retained_evidence_locator_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "prior_entry_hash": f("sha256", nullable=True),
            "accepted_prefix_head_hash": f("sha256", nullable=True),
            "accepted_prefix_seq": f("integer", constraints={"minimum": 0}),
            "previous_thread_content_hash": f("sha256", nullable=True),
            "risk_lifecycle_effect": f("enum:risk_lifecycle_effect"),
            "decision_content_hash": f("sha256"),
        }
    )
    objects["AEMHDecisionAuthorityRegistry"] = obj(
        {
            "registry_ref": f("string"),
            "scope_identity": scope_field(),
            "previous_projection_ref": f("string", nullable=True),
            "previous_projection_content_hash": f("sha256", nullable=True),
            "accepted_prefix_head_hash": f("sha256", nullable=True),
            "accepted_prefix_seq": f("integer", constraints={"minimum": 0}),
            "decision_refs": f("string", cardinality="many", constraints={"min_items": 1}),
            "registry_content_hash": f("sha256"),
        }
    )
    objects["AEMHEvidenceBindingAuthority"] = obj(
        {
            "binding_ref": f("string"),
            "scope_identity": scope_field(),
            "thread_ref": f("string"),
            "evidence_kind": f("enum:identity_evidence_kind"),
            "entity_ref": f("string"),
            "entity_content_identity": f("sha256"),
            "source_locator_ref": f("string"),
            "source_locator_content_hash": f("sha256"),
            "source_raw_payload_hash": f("sha256"),
            "source_revision_ref": f("string"),
            "source_revision_content_hash": f("sha256"),
            "binding_content_hash": f("sha256"),
        }
    )
    objects["AEMHThreadMembershipAuthority"] = obj(
        {
            "authority_ref": f("string"),
            "scope_identity": scope_field(),
            "thread_ref": f("string"),
            "domain": f("enum:aemh_domain"),
            "original_candidate_ref": f("string"),
            "original_candidate_content_identity": f("sha256"),
            "original_reminder_ref": f("string"),
            "decision_refs": f("string", cardinality="many", constraints={"min_items": 1}),
            "candidate_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "later_fact_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
            "evidence_binding_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "source_locator_refs": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
            "authority_content_hash": f("sha256"),
        }
    )
    objects["PhaseLabelPolicy"] = obj(
        {
            "policy_ref": f("string"),
            "scope_identity": scope_field(),
            "mapping": f("phase_code_to_zh_label_map"),
            "policy_content_hash": f("sha256"),
        }
    )
    objects["TimezoneDayZeroPolicy"] = obj(
        {
            "policy_ref": f("string"),
            "scope_identity": scope_field(),
            "timezone": f("string", constraints={"const": "Asia/Shanghai"}),
            "day_zero_convention": f("enum:day_zero_convention"),
            "before_anchor_formula": f("string", constraints={"const": "calendar_delta"}),
            "on_or_after_anchor_formula": f("string", constraints={"const": "calendar_delta+1_when_anchor_is_day_one_else_calendar_delta"}),
            "policy_content_hash": f("sha256"),
        }
    )
    objects["DateStateRangeProjectionPolicy"] = obj(
        {
            "policy_ref": f("string"),
            "scope_identity": scope_field(),
            "state_geometry_matrix": f("closed_date_state_geometry_matrix"),
            "policy_content_hash": f("sha256"),
        }
    )
    objects["EmptyDomainApplicabilityPolicy"] = obj(
        {
            "policy_ref": f("string"),
            "scope_identity": scope_field(),
            "empty_decision": f("enum:empty_domain_decision"),
            "coverage_proof_required": f("boolean", constraints={"const": True}),
            "policy_content_hash": f("sha256"),
        }
    )
    objects["AEMHTransitionPolicy"] = obj(
        {
            "policy_ref": f("string"),
            "scope_identity": scope_field(),
            "allowed_transitions": f("closed_aemh_transition_matrix"),
            "second_reminder_allowed": f("boolean", constraints={"const": False}),
            "risk_lifecycle_effect": f("enum:risk_lifecycle_effect"),
            "policy_content_hash": f("sha256"),
        }
    )

    for object_name, hash_field in SELF_HASH_FIELDS.items():
        objects[object_name]["properties"][hash_field]["constraints"]["self_hash"] = True

    named_types = {
        "phase_code_to_zh_label_map": obj(
            {
                "screening": f("string", constraints={"const": "筛选期"}),
                "baseline": f("string", constraints={"const": "基线期"}),
                "treatment": f("string", constraints={"const": "治疗期"}),
                "follow_up": f("string", constraints={"const": "随访期"}),
                "unscheduled": f("string", constraints={"const": "非计划阶段"}),
            }
        ),
        "date_state_geometry_rule": obj(
            {
                "candidate_min": f("integer", nullable=True, constraints={"minimum": 0}),
                "candidate_max": f("integer", nullable=True, constraints={"minimum": 0}),
                "exact_required": f("boolean"),
                "geometry_rule": f("string"),
                "main_axis_rule": f("string"),
                "absence_and_coverage_proof": f("boolean"),
            }
        ),
        "closed_date_state_geometry_matrix": obj(
            {
                "exact": f("date_state_geometry_rule"),
                "partial": f("date_state_geometry_rule"),
                "conflicted": f("date_state_geometry_rule"),
                "missing": f("date_state_geometry_rule"),
            }
        ),
        "closed_aemh_transition_matrix": obj(
            {
                "reminder_created": f("enum:history_event_kind", cardinality="many"),
                "match_decided": f("enum:history_event_kind", cardinality="many"),
                "withdrawn": f("enum:history_event_kind", cardinality="many"),
                "reappeared": f("enum:history_event_kind", cardinality="many"),
                "match_states": f("enum:match_state", cardinality="many", constraints={"min_items": 3, "sorted_unique": True}),
                "risk_lifecycle_effect": f("enum:risk_lifecycle_effect"),
            }
        ),
        "DirectFieldParams": obj(
            {
                "source_fixture_ref": f("string", constraints={"min_length": 1}),
                "source_field_path": f("string", constraints={"min_length": 1}),
            }
        ),
        "DeriveValueParams": obj(
            {
                "transform": f("enum:authority_derive_transform"),
                "input_fixture_refs": f("string", cardinality="many", constraints={"min_items": 1}),
                "input_field_paths": f("string", cardinality="many", constraints={"min_items": 1}),
                "selector_contract": f("enum:authority_contract_id"),
            }
        ),
        "ProjectRecordParams": obj(
            {
                "selector_fixture_ref": f("string", constraints={"min_length": 1}),
                "selector_object_type": f("string", constraints={"min_length": 1}),
                "join_keys": f("string", cardinality="many", constraints={"min_items": 6}),
                "result_object_type": f("string", constraints={"min_length": 1}),
                "result_field_path": f("string", constraints={"min_length": 1}),
            }
        ),
        "AssembleSortedRecordsParams": obj(
            {
                "member_fixture_refs": f("string", cardinality="many", constraints={"min_items": 1}),
                "member_object_type": f("string", constraints={"min_length": 1}),
                "stable_identity_fields": f("string", cardinality="many", constraints={"min_items": 1}),
                "uniqueness_fields": f("string", cardinality="many", constraints={"min_items": 1}),
                "result_object_type": f("string", constraints={"min_length": 1}),
                "result_field_path": f("string", constraints={"min_length": 1}),
                "assembly_cardinality": f("enum:authority_assembly_cardinality"),
            }
        ),
        "CanonicalHashParams": obj(
            {
                "target_object_type": f("string", constraints={"min_length": 1}),
                "target_hash_field": f("string", constraints={"min_length": 1}),
                "ingredient_target_fields": f("string", cardinality="many", constraints={"min_items": 1, "sorted_unique": True}),
                "algorithm": f("string", constraints={"const": "sha256"}),
                "canonicalization": f("enum:canonicalization_profile"),
            }
        ),
        "ProjectContractParams": obj(
            {
                "contract": f("enum:authority_contract_id"),
                "source_owner_type": f("string", constraints={"min_length": 1}),
                "source_field_path": f("string", constraints={"min_length": 1}),
                "result_type": f("string", constraints={"min_length": 1}),
                "result_cardinality": f("enum:output_cardinality"),
                "projection_mode": f("string", constraints={"const": "closed_nested_contract_projection"}),
            }
        ),
        "RecipeInputSpec": obj(
            {
                "input_id": f("string", constraints={"min_length": 1}),
                "value_type": f("enum:ir_value_type"),
                "cardinality": f("enum:recipe_cardinality"),
                "source_kind": f("enum:recipe_input_source"),
            }
        ),
        "RecipeRef": obj(
            {
                "ref_kind": f("enum:recipe_ref_kind"),
                "ref_id": f("string", constraints={"min_length": 1}),
                "value_type": f("enum:ir_value_type"),
            }
        ),
        "RecipeParams": obj(
            {
                "expected_integer": f("integer", nullable=True),
                "expected_string": f("string", nullable=True),
                "allowed_strings": f("string", cardinality="many", constraints={"sorted_unique": True}),
                "separator": f("string", nullable=True),
                "occurrence_value": f("string", nullable=True),
            }
        ),
        "RecipeTransform": obj(
            {
                "node_id": f("string", constraints={"min_length": 1}),
                "op": f("enum:recipe_transform_op"),
                "args": f("RecipeRef", cardinality="many"),
                "params": f("RecipeParams"),
                "output_type": f("enum:ir_value_type"),
            }
        ),
        "RecipeCondition": obj(
            {
                "condition_id": f("string", constraints={"min_length": 1}),
                "op": f("enum:recipe_condition_op"),
                "args": f("RecipeRef", cardinality="many"),
                "params": f("RecipeParams"),
                "error_code": f("string", constraints={"pattern": "^TPA_[A-Z0-9_]+$"}),
            }
        ),
        "RecipeOutputSpec": obj(
            {
                "output_id": f("string", constraints={"min_length": 1}),
                "source_ref": f("RecipeRef"),
                "value_type": f("enum:ir_value_type"),
                "target_leaf": f("string", nullable=True),
                "dependency_refs": f("string", cardinality="many", constraints={"sorted_unique": True}),
                "fixture_asserted": f("boolean"),
            }
        ),
        "RecipeCanonicalization": obj(
            {
                "profile": f("enum:canonicalization_profile"),
                "hash_mode": f("enum:hash_mode"),
                "hash_exclude_field": f("string", nullable=True),
            }
        ),
        "TypedValue": obj(
            {
                "value_id": f("string", constraints={"min_length": 1}),
                "value_type": f("enum:ir_value_type"),
                "string_value": f("string", nullable=True),
                "integer_value": f("integer", nullable=True),
                "boolean_value": f("boolean", nullable=True),
                "string_list_value": f("string", cardinality="many"),
                "integer_list_value": f("integer", cardinality="many"),
                "object_ref": f("string", nullable=True),
            }
        ),
        "DependencyEdge": obj(
            {
                "from_ref": f("string", constraints={"min_length": 1}),
                "to_ref": f("string", constraints={"min_length": 1}),
            }
        ),
        "PolicyHashEntry": obj(
            {
                "policy_ref": f("string", constraints={"min_length": 1}),
                "policy_content_hash": f("sha256"),
            }
        ),
        "CoverageCountRecord": obj(
            {
                "a_direct": f("integer", constraints={"minimum": 0}),
                "b_deterministic_derived": f("integer", constraints={"minimum": 0}),
                "c_accepted_semantic": f("integer", constraints={"minimum": 0}),
                "d_unconstructible": f("integer", constraints={"minimum": 0}),
                "unexplained_after": f("integer", constraints={"const": 0}),
            }
        ),
        "ExternalAcceptedRecord": obj(
            {
                "accepted_record_ref": f("string", constraints={"min_length": 1}),
                "authority_scope": f("enum:authority_scope"),
                "non_clinical": f("boolean", constraints={"const": True}),
                "contract_id": f("string", constraints={"const": CONTRACT_ID}),
                "schema_version": f("string", constraints={"const": SCHEMA_VERSION}),
                "policy_hashes": f("PolicyHashEntry", cardinality="many", constraints={"min_items": 5}),
                "coverage": f("CoverageCountRecord"),
                "record_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "ExternalRegistryRoot": obj(
            {
                "registry_id": f("string", constraints={"const": "registry:r5-s5:synthetic-temporal-projection-acceptance:20260820"}),
                "authority_scope": f("enum:authority_scope"),
                "non_clinical": f("boolean", constraints={"const": True}),
                "accepted_records": f("ExternalAcceptedRecord", cardinality="many", constraints={"min_items": 1}),
                "root_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "CandidateRegistryClaim": obj(
            {
                "registry_id": f("string"),
                "registry_root_content_hash": f("sha256"),
                "accepted_record_ref": f("string"),
                "accepted_record_content_hash": f("sha256"),
                "authority_record_content_hash": f("sha256"),
                "claim_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "CandidateOperationalEvidence": obj(
            {
                "evaluation_instance_ref": f("string", constraints={"pattern": "^evaluation:[A-Za-z0-9._:-]+$"}),
                "observed_sequence": f("integer", constraints={"minimum": 1}),
                "transport_digest": f("sha256"),
                "evidence_content_hash": f("sha256", constraints={"self_hash": True}),
            },
            optional=("transport_digest",),
        ),
        "CandidateReceipt": obj(
            {
                "receipt_id": f("string"),
                "candidate_ref": f("string"),
                "registry_claim_content_hash": f("sha256"),
                "authority_record_content_hash": f("sha256"),
                "operational_evidence_content_hash": f("sha256"),
                "receipt_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "ExternalCandidateBundle": obj(
            {
                "candidate_ref": f("string"),
                "authority_record": f("ExternalAcceptedRecord"),
                "operational_evidence": f("CandidateOperationalEvidence"),
                "registry_claim": f("CandidateRegistryClaim"),
                "receipt": f("CandidateReceipt"),
                "bundle_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "AcceptedRecipeDefinition": obj(
            {
                "recipe_id": f("string", constraints={"min_length": 1}),
                "inputs": f("RecipeInputSpec", cardinality="many", constraints={"min_items": 1}),
                "transforms": f("RecipeTransform", cardinality="many", constraints={"min_items": 1}),
                "conditions": f("RecipeCondition", cardinality="many", constraints={"min_items": 1}),
                "outputs": f("RecipeOutputSpec", cardinality="many", constraints={"min_items": 1}),
                "cardinality": f("enum:recipe_cardinality"),
                "ordering": f("enum:ordering"),
                "canonicalization": f("RecipeCanonicalization"),
                "fail_codes": f("string", cardinality="many", constraints={"sorted_unique": True}),
                "fallback": f("string", constraints={"const": "fail_closed_no_nearest"}),
                "recipe_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "AcceptedRecipeAttackBundle": obj(
            {
                "bundle_id": f("string", constraints={"min_length": 1}),
                "recipe_id": f("string", constraints={"min_length": 1}),
                "recipe": f("AcceptedRecipeDefinition"),
                "fixture": f("PositiveFixture"),
                "bundle_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "AuthorityFixture": obj(
            {
                "fixture_id": f("string", constraints={"min_length": 1}),
                "object_type": f("string", constraints={"min_length": 1}),
                "content_hash_field": f("string", constraints={"min_length": 1}),
                "value": f("discriminated_schema_object"),
                "fixture_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "AuthorityOutputMapping": obj(
            {
                "mapping_id": f("string", constraints={"min_length": 1}),
                "qualified_leaf": f("string", constraints={"min_length": 1}),
                "authority_root": f("string", constraints={"min_length": 1}),
                "output_path": f("string", constraints={"min_length": 1}),
                "dependency_refs": f("string", cardinality="many", constraints={"min_items": 1}),
                "source_fixture_refs": f("string", cardinality="many", constraints={"min_items": 1}),
                "source_fixture_content_hash_pins": f("string", cardinality="many", constraints={"min_items": 1}),
                "source_field_paths": f("string", cardinality="many", constraints={"min_items": 1}),
                "op": f("enum:authority_projection_op"),
                "direct_field_params": f("DirectFieldParams", nullable=True),
                "derive_value_params": f("DeriveValueParams", nullable=True),
                "project_record_params": f("ProjectRecordParams", nullable=True),
                "assemble_sorted_records_params": f("AssembleSortedRecordsParams", nullable=True),
                "canonical_hash_params": f("CanonicalHashParams", nullable=True),
                "project_contract_params": f("ProjectContractParams", nullable=True),
                "scope_join_keys": f("string", cardinality="many", constraints={"min_items": 6}),
                "output_type": f("string", constraints={"min_length": 1}),
                "output_cardinality": f("enum:output_cardinality"),
                "output_nullable": f("boolean"),
                "canonicalization_profile": f("string", constraints={"const": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan"}),
                "content_hash_recipe": f("string", constraints={"const": "sha256_over_canonical_projection_excluding_only_own_hash_field"}),
                "mapping_content_hash": f("sha256", constraints={"self_hash": True}),
            },
            conditional_rules=[
                {"when": {"op": "direct_field"}, "requires_non_null": ["direct_field_params"], "requires_null": ["derive_value_params", "project_record_params", "assemble_sorted_records_params", "canonical_hash_params", "project_contract_params"]},
                {"when": {"op": "derive_value"}, "requires_non_null": ["derive_value_params"], "requires_null": ["direct_field_params", "project_record_params", "assemble_sorted_records_params", "canonical_hash_params", "project_contract_params"]},
                {"when": {"op": "project_record"}, "requires_non_null": ["project_record_params"], "requires_null": ["direct_field_params", "derive_value_params", "assemble_sorted_records_params", "canonical_hash_params", "project_contract_params"]},
                {"when": {"op": "assemble_sorted_records"}, "requires_non_null": ["assemble_sorted_records_params"], "requires_null": ["direct_field_params", "derive_value_params", "project_record_params", "canonical_hash_params", "project_contract_params"]},
                {"when": {"op": "canonical_hash"}, "requires_non_null": ["canonical_hash_params"], "requires_null": ["direct_field_params", "derive_value_params", "project_record_params", "assemble_sorted_records_params", "project_contract_params"]},
                {"when": {"op": "project_contract"}, "requires_non_null": ["project_contract_params"], "requires_null": ["direct_field_params", "derive_value_params", "project_record_params", "assemble_sorted_records_params", "canonical_hash_params"]},
            ],
        ),
        "AuthorityMappingPositiveFixture": obj(
            {
                "fixture_id": f("string", constraints={"min_length": 1}),
                "mapping_id": f("string", constraints={"min_length": 1}),
                "authority_fixture_refs": f("string", cardinality="many", constraints={"min_items": 1}),
                "expected_target_canonical_json": f("string", constraints={"min_length": 1}),
                "expected_target_content_hash": f("sha256"),
                "expected_trace_content_hash": f("sha256"),
                "fixture_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "RecipeAuthorityRequirement": obj(
            {
                "fixture_ref": f("string", constraints={"min_length": 1}),
                "object_type": f("string", constraints={"min_length": 1}),
                "role": f("string", constraints={"min_length": 1}),
                "fixture_content_hash": f("sha256"),
                "scope_join_keys": f("string", cardinality="many", constraints={"min_items": 6}),
            }
        ),
        "RecipeAuthorityBinding": obj(
            {
                "recipe_id": f("string", constraints={"min_length": 1}),
                "requirements": f("RecipeAuthorityRequirement", cardinality="many"),
                "binding_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "PositiveFixture": obj(
            {
                "fixture_id": f("string", constraints={"min_length": 1}),
                "recipe_id": f("string", constraints={"min_length": 1}),
                "authority_fixture_refs": f("string", cardinality="many"),
                "inputs": f("TypedValue", cardinality="many", constraints={"min_items": 1}),
                "expected_outputs": f("TypedValue", cardinality="many", constraints={"min_items": 1}),
                "dependency_edges": f("DependencyEdge", cardinality="many"),
                "fixture_content_hash": f("sha256", constraints={"self_hash": True}),
            }
        ),
        "ChallengeMutation": obj(
            {
                "target_kind": f("enum:mutation_target_kind"),
                "target_ref": f("string", constraints={"min_length": 1}),
                "op": f("enum:mutation_op"),
                "path": f("string", constraints={"min_length": 1}),
                "replacement": f("TypedValue"),
            }
        ),
        "ChallengeCase": obj(
            {
                "case_id": f("string", constraints={"min_length": 1}),
                "category": f("string", constraints={"min_length": 1}),
                "probe_kind": f("enum:probe_kind"),
                "covered_leaf": f("string", nullable=True),
                "recipe_id": f("string", nullable=True),
                "fixture_id": f("string", nullable=True),
                "mutation": f("ChallengeMutation"),
                "expected_error": f("string", constraints={"pattern": "^TPA_[A-Z0-9_]+$"}),
                "required_non_llm_anchor": f("string", constraints={"min_length": 1}),
            }
        ),
    }

    return {
        "schema": "medical-monitoring-r5-s5-temporal-projection-authority-delta-schema-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "additional_properties": False,
        "primitive_types": {
            "string": {"json_type": "string", "pattern": None, "patterns": [], "format": None, "discriminator": None},
            "integer": {"json_type": "integer", "pattern": None, "patterns": [], "format": None, "discriminator": None},
            "boolean": {"json_type": "boolean", "pattern": None, "patterns": [], "format": None, "discriminator": None},
            "sha256": {"json_type": "string", "pattern": "^[0-9a-f]{64}$", "patterns": [], "format": None, "discriminator": None},
            "date": {"json_type": "string", "pattern": None, "patterns": [], "format": "date", "discriminator": None},
            "partial_date": {"json_type": "string", "pattern": None, "patterns": ["^\\d{4}$", "^\\d{4}-\\d{2}$", "^\\d{4}-\\d{2}-\\d{2}$"], "format": None, "discriminator": None},
            "discriminated_schema_object": {"json_type": "object", "pattern": None, "patterns": [], "format": None, "discriminator": "object_type"},
        },
        "enums": enums,
        "objects": objects,
        "named_types": named_types,
        "hash_contract": {
            "algorithm": "sha256",
            "serialization": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan",
            "self_hash_rule": "exclude_only_the_object_own_content_hash_field",
            "array_rules": "semantic order unless field constraint sorted_unique=true",
        },
        "external_acceptance_rule": {
            "candidate_receipt_is_authority": False,
            "resolution_key": ["registry_id", "registry_root_content_hash", "accepted_record_ref", "accepted_record_content_hash"],
            "authority_record_equality": "canonical_exact_all_fields_against_manifest_owned_accepted_record",
            "operational_evidence_fields": ["evaluation_instance_ref", "observed_sequence", "transport_digest", "evidence_content_hash"],
            "operational_evidence_carries_policy_semantics": False,
            "candidate_reseal_cannot_change_external_acceptance": True,
            "real_clinical_acceptance": "external_not_provided_by_this_delta",
        },
        "forbidden_authority_patterns": [
            "Any",
            "fixture",
            "case_id",
            "sentinel",
            "expected_output",
            "target_value",
            "nearest",
            "nominal_to_actual",
            "class_wide_value",
            "S4_value_transfer",
            "D07_OTHER",
            "model_role_authority",
        ],
    }


def source_row(authority_root: str, accepted_inputs: list[str], semantic_inputs: list[str], output_contracts: list[str], exact_join: list[str], forbidden: list[str]) -> dict[str, Any]:
    return {
        "authority_root": authority_root,
        "accepted_typed_inputs": accepted_inputs,
        "accepted_semantic_inputs": semantic_inputs,
        "output_contracts": output_contracts,
        "exact_join": exact_join,
        "cardinality": "exact_one_per_scoped_authority_ref",
        "fallback": "fail_closed_no_nearest",
        "forbidden": forbidden,
    }


def build_source_matrix() -> dict[str, Any]:
    parent = read_json(PARENT_MANIFEST)
    semantic = read_json(SEMANTIC_MANIFEST)
    rows = [
        source_row("TemporalProjectionAuthorityRegistry", ["manifest.external_acceptance_registry_root:ExternalRegistryRoot", "manifest.accepted_record_content_hash_pins exact full-record canonical equality"], [], ["both"], list(IDENTITY_FIELDS), ["candidate-embedded registry", "claim-only record binding", "candidate self-authorization", "real clinical authority"]),
        source_row("TemporalProjectionAcceptanceReceipt", ["manifest external root plus exact accepted record payload", "CandidateOperationalEvidence strict non-semantic fields"], [], ["both"], list(IDENTITY_FIELDS), ["status-string authorization", "candidate reseal authorization", "operational evidence carrying policy semantics"]),
        source_row("AcceptedRecipeRegistry", ["manifest.accepted_recipe_registry plus verifier hard-pinned registry and 18 per-recipe content hashes"], [], ["both"], ["recipe_id"], ["candidate-supplied recipe", "self-resealed recipe and expected output"]),
        source_row("AcceptedSchemaBaseline", ["manifest.accepted_schema_baseline plus verifier hard-pinned canonical schema hash"], [], ["both"], ["schema_content_hash"], ["candidate schema reseal", "unknown optional field", "enum widening"]),
        source_row("PublicScopeUniverseAuthority", ["mm_r4.d08_contracts.VisibilityDecision", "mm_r4.d08_contracts.ScopeBinding"], [], ["both"], list(IDENTITY_FIELDS), ["singleton assumed universe", "hidden-set inference"]),
        source_row("RecordNodeStableIdentityBinding", ["mm_r4.d08_contracts.RecordNode.stable_record_identity", "mm_r4.d08_contracts.ScopeBinding.site_ref"], [], ["both"], list(IDENTITY_FIELDS), ["record-node id as member id", "weak join"]),
        source_row("CutoffEndpointBindingAuthority", ["mm_r1.domain.MonitoringRun.data_cutoff", "mm_r4.d08_contracts.ScopeBinding.clinical_event_cutoff", "mm_r4.d08_contracts.TimeRef.value"], [], ["both"], list(IDENTITY_FIELDS), ["fabricated missing cutoff", "date-only cutoff identity"]),
        source_row("SourceLocatorRevisionBinding", ["mm_r4.contracts.SourceLocator", "mm_r4.d08_contracts.SourceLocator", "mm_r1.domain.SourceRevision"], [], ["both"], list(IDENTITY_FIELDS), ["unused locator", "revision without content"]),
        source_row("TemporalMemberAuthorityRecord", ["mm_r4.d08_contracts.RecordNode", "mm_r4.d08_contracts.SharedSpineBinding"], [], ["subject-temporal-public-v1"], list(IDENTITY_FIELDS), ["fixture membership", "target mirror"]),
        source_row("TemporalEndpointAuthorityRecord", ["mm_r4.d08_contracts.TimeRef", "mm_r4.visit_schedule.ActualEncounterRecord", "mm_r4.visit_schedule.ActualActivityRecord"], [], ["subject-temporal-public-v1"], list(IDENTITY_FIELDS), ["nominal-to-actual inference", "unproved absence"]),
        source_row("TemporalAxisAuthorityRecord", ["mm_r1.domain.TemporalEvent", "mm_r4.d08_contracts.TimeRef"], [], ["subject-temporal-public-v1"], list(IDENTITY_FIELDS), ["implicit timezone", "fabricated study day"]),
        source_row("VisitProjectionBinding", ["mm_r4.visit_schedule.PlannedVisitDefinition", "mm_r4.visit_schedule.ActualEncounterRecord", "mm_r4.visit_schedule.VisitAssignmentDecision"], [], ["subject-temporal-public-v1"], list(IDENTITY_FIELDS), ["unscheduled snapping", "unaccepted assignment"]),
        source_row("EventProjectionBinding", ["mm_r4.visit_schedule.ActualActivityRecord", "mm_r4.visit_schedule.ActualEncounterRecord"], ["accepted semantic event classification"], ["subject-temporal-public-v1"], list(IDENTITY_FIELDS), ["event class inference", "nearest visit"]),
        source_row("PhaseProjectionBinding", ["mm_r4.visit_schedule.TypedScheduleAnchorRef", "mm_r4.visit_schedule.PlannedVisitDefinition.phase"], [], ["subject-temporal-public-v1"], list(IDENTITY_FIELDS), ["free-form Chinese phase label", "class-wide target"]),
        source_row("RiskProjectionBinding", ["mm_r5.s4_contracts.S4AcceptedAuthorityAnchor", "mm_r5.s4_contracts.S4JourneyTargetIdentity"], ["accepted risk taxonomy", "accepted severity policy", "accepted zh lexicon"], ["subject-temporal-public-v1"], list(S4_JOIN_FIELDS), ["S4 value transfer", "ninth join field"]),
        source_row("DomainApplicabilityAuthorityRecord", ["TemporalMemberAuthorityRecord"], [], ["subject-temporal-public-v1"], list(IDENTITY_FIELDS), ["empty implies not_applicable", "OTHER domain"]),
        source_row("AEMHAppendDecisionAuthorityRecord", ["mm_r1.ae_mh.AEMHResult", "mm_r4.aemh.AEMHSliceResult"], [], ["aemh-match-history-public-v1"], list(IDENTITY_FIELDS), ["historical_evidence_refs as ledger", "second reminder"]),
        source_row("AEMHDecisionAuthorityRegistry", ["prior accepted AEMH projection and prefix"], [], ["aemh-match-history-public-v1"], list(IDENTITY_FIELDS), ["prefix rewrite", "candidate-owned prior hash"]),
        source_row("AEMHEvidenceBindingAuthority", ["mm_r2.risk.RiskCandidate", "mm_r1.domain.CanonicalFact", "mm_r4.aemh.SemanticRecord", "SourceLocatorRevisionBinding"], [], ["aemh-match-history-public-v1"], list(IDENTITY_FIELDS), ["candidate/fact swap", "partial evidence reseal"]),
        source_row("AEMHThreadMembershipAuthority", ["mm_r2.risk.RiskCandidate", "AEMHAppendDecisionAuthorityRecord", "AEMHEvidenceBindingAuthority"], [], ["aemh-match-history-public-v1"], list(IDENTITY_FIELDS), ["phantom thread", "cross-scope thread"]),
    ]
    return {
        "schema": "medical-monitoring-r5-s5-temporal-projection-authority-source-matrix-delta-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "accepted_parent_manifest_raw_sha256": raw_sha(ROOT / PARENT_MANIFEST),
        "accepted_semantic_manifest_raw_sha256": raw_sha(ROOT / SEMANTIC_MANIFEST),
        "accepted_source_file_sha256": parent["source_file_sha256"],
        "accepted_parent_artifact_sha256": parent["artifact_raw_sha256"],
        "accepted_semantic_artifact_sha256": semantic["artifact_raw_sha256"],
        "rows": rows,
        "row_count": len(rows),
        "global_rules": [
            "all roots resolve by exact full scope and declared cardinality",
            "every emitted locator is consumed and belongs to exactly one accepted revision partition",
            "accepted semantic authorities are referenced, never duplicated",
            "each of 272 leaves resolves to one exact authority output or frozen recipe output path; nominal mappings are forbidden",
            "runtime candidates reference recipe ids only and cannot supply recipe definitions",
            "no fixture case sentinel target example class-wide value S4 value transfer D07 fallback or model role authorizes output",
        ],
    }


def ir_params(
    *,
    expected_integer: int | None = None,
    expected_string: str | None = None,
    allowed_strings: list[str] | None = None,
    separator: str | None = None,
    occurrence_value: str | None = None,
) -> dict[str, Any]:
    return {
        "expected_integer": expected_integer,
        "expected_string": expected_string,
        "allowed_strings": sorted(allowed_strings or []),
        "separator": separator,
        "occurrence_value": occurrence_value,
    }


def ir_input(input_id: str, value_type: str, *, source_kind: str = "fixture", cardinality: str = "exact_one") -> dict[str, Any]:
    return {
        "input_id": input_id,
        "value_type": value_type,
        "cardinality": cardinality,
        "source_kind": source_kind,
    }


def ir_ref(ref_kind: str, ref_id: str, value_type: str) -> dict[str, Any]:
    return {"ref_kind": ref_kind, "ref_id": ref_id, "value_type": value_type}


def ir_transform(node_id: str, op: str, args: list[dict[str, Any]], output_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "op": op,
        "args": args,
        "params": params or ir_params(),
        "output_type": output_type,
    }


def ir_condition(condition_id: str, op: str, args: list[dict[str, Any]], error_code: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "condition_id": condition_id,
        "op": op,
        "args": args,
        "params": params or ir_params(),
        "error_code": error_code,
    }


def ir_output(
    output_id: str,
    source_ref: dict[str, Any],
    value_type: str,
    *,
    target_leaf: str | None = None,
    dependency_refs: list[str] | None = None,
    fixture_asserted: bool = True,
) -> dict[str, Any]:
    return {
        "output_id": output_id,
        "source_ref": source_ref,
        "value_type": value_type,
        "target_leaf": target_leaf,
        "dependency_refs": sorted(dependency_refs or []),
        "fixture_asserted": fixture_asserted,
    }


def recipe_ir(
    recipe_id: str,
    inputs: list[dict[str, Any]],
    transforms: list[dict[str, Any]],
    conditions: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    *,
    cardinality: str = "exact_one",
    ordering: str = "scalar",
    hash_mode: str = "none",
) -> dict[str, Any]:
    return sealed({
        "recipe_id": recipe_id,
        "inputs": inputs,
        "transforms": transforms,
        "conditions": conditions,
        "outputs": outputs,
        "cardinality": cardinality,
        "ordering": ordering,
        "canonicalization": {
            "profile": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan",
            "hash_mode": hash_mode,
            "hash_exclude_field": None,
        },
        "fail_codes": sorted({condition["error_code"] for condition in conditions}),
        "fallback": "fail_closed_no_nearest",
    }, "recipe_content_hash")


def typed_value(value_id: str, value_type: str, value: Any) -> dict[str, Any]:
    item = {
        "value_id": value_id,
        "value_type": value_type,
        "string_value": None,
        "integer_value": None,
        "boolean_value": None,
        "string_list_value": [],
        "integer_list_value": [],
        "object_ref": None,
    }
    if value_type in {"string", "date", "sha256"}:
        item["string_value"] = value
    elif value_type == "integer":
        item["integer_value"] = value
    elif value_type == "boolean":
        item["boolean_value"] = value
    elif value_type in {"string_list", "date_list", "sha256_list"}:
        item["string_list_value"] = value
    elif value_type == "integer_list":
        item["integer_list_value"] = value
    elif value_type in {"external_candidate_bundle", "external_registry_root"}:
        item["object_ref"] = value
    else:
        raise ValueError(f"unsupported typed value: {value_type}")
    return item


def sealed(value: dict[str, Any], hash_field: str) -> dict[str, Any]:
    result = dict(value)
    result.pop(hash_field, None)
    result[hash_field] = digest(result)
    return result


def all_parent_leaves() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for contract, path in (("subject-temporal-public-v1", SUBJECT_SCHEMA), ("aemh-match-history-public-v1", AEMH_SCHEMA)):
        schema = read_json(path)
        leaves = [f"{name}.{field}" for name, definition in schema["objects"].items() for field in definition]
        result[contract] = sorted(leaves)
    return result


SUBJECT_C = {
    "TemporalEvent.domain",
    "TemporalEvent.subtype",
    "TemporalRiskAnchor.risk_type_zh",
    "TemporalRiskAnchor.severity",
}


def direct_sets() -> dict[str, set[str]]:
    shared = {
        "PublicAuthorityReceipt.evaluation_content_identities",
        "PublicScopeIdentity.project_ref",
        "PublicScopeIdentity.run_ref",
        "PublicScopeIdentity.snapshot_ref",
        "PublicScopeIdentity.cutoff_ref",
        "PublicScopeIdentity.site_ref",
        "PublicScopeIdentity.subject_ref",
        "PublicScopeIdentity.spine_ref",
        "PublicSourceLocator.authority_entity_kind",
        "PublicSourceLocator.authority_entity_ref",
        "PublicSourceLocator.canonical_location",
        "PublicSourceLocator.column_or_anchor",
        "PublicSourceLocator.locator_variant",
        "PublicSourceLocator.raw_payload_hash",
        "PublicSourceLocator.record_ref",
        "PublicSourceLocator.snapshot_ref",
        "PublicSourceLocator.source_file_ref",
        "PublicSourceLocator.source_revision_ref",
        "PublicSourceLocator.table_semantic",
        "SourceRevisionContentPair.accepted_content_hash",
        "SourceRevisionContentPair.revision_id",
    }
    subject = set(shared)
    subject.update(
        {
            "TemporalAxisBasis.timezone",
            "TemporalEvent.event_ref",
            "TemporalRiskAnchor.domain",
            "TemporalRiskAnchor.event_ref",
            "TemporalRiskAnchor.risk_content_identity",
            "TemporalRiskAnchor.risk_ref",
            "TemporalRiskAnchor.visit_ref",
        }
    )
    aemh = set(shared)
    aemh.update(
        {
            "AEMHIdentityEvidence.entity_content_identity",
            "AEMHIdentityEvidence.entity_ref",
            "AEMHMatchThread.candidate_content_identity",
            "AEMHMatchThread.original_candidate_ref",
        }
    )
    return {"subject-temporal-public-v1": subject, "aemh-match-history-public-v1": aemh}


def derived_sets(leaves: dict[str, list[str]], direct: dict[str, set[str]]) -> dict[str, set[str]]:
    constants = {
        "PublicAuthorityReceipt.audience_contract_id",
        "PublicAuthorityReceipt.authority_contract_id",
        "PublicAuthorityReceipt.authority_contract_version",
        "PublicAuthorityReceipt.receipt_variant",
        "SubjectTemporalPublicProjection.contract_id",
        "SubjectTemporalPublicProjection.fallback_policy",
        "SubjectTemporalPublicProjection.schema_version",
        "AEMHMatchHistoryPublicProjection.contract_id",
        "AEMHMatchHistoryPublicProjection.fallback_policy",
        "AEMHMatchHistoryPublicProjection.schema_version",
        "AEMHMatchHistoryEntry.risk_lifecycle_effect",
        "TemporalAxisBasis.default_axis_mode",
    }
    preferred = {
        "PublicScopeIdentity.identity_content_hash",
        "PublicSourceLocator.locator_ref",
        "PublicSourceLocator.source_revision_content_hash",
        "PublicSourceLocator.locator_content_hash",
        "SourceRevisionContentPair.pair_content_hash",
        "VisibilityClosure.hidden_member_count",
        "VisibilityClosure.hidden_site_count",
        "AEMHMatchThread.project_ref",
        "AEMHMatchThread.site_ref",
        "AEMHMatchThread.subject_ref",
        "AEMHMatchThread.thread_ref",
        "AEMHIdentityEvidence.evidence_ref",
        "AEMHIdentityEvidence.source_locator_content_hash",
        "AEMHIdentityEvidence.evidence_content_hash",
        "AEMHHistoryMembershipIndex.candidate_refs",
        "AEMHHistoryMembershipIndex.later_fact_refs",
        "AEMHHistoryMembershipIndex.source_locator_refs",
        "AEMHHistoryMembershipIndex.thread_refs",
        "AEMHHistoryMembershipIndex.membership_content_hash",
        "TemporalRiskAnchor.risk_anchor_ref",
        "TemporalMembershipIndex.event_refs",
        "TemporalMembershipIndex.phase_refs",
        "TemporalMembershipIndex.risk_anchor_refs",
        "TemporalMembershipIndex.visit_refs",
        "TemporalMembershipIndex.source_locator_refs",
        "VisibilityClosure.deep_link_eligible",
    }
    targets = {"subject-temporal-public-v1": 18, "aemh-match-history-public-v1": 28}
    out: dict[str, set[str]] = {}
    for contract, contract_leaves in leaves.items():
        candidates = [leaf for leaf in contract_leaves if leaf in constants or leaf in preferred]
        candidates += [
            leaf
            for leaf in contract_leaves
            if leaf not in candidates
            and leaf not in direct[contract]
            and leaf not in SUBJECT_C
            and leaf.endswith(
                (
                    "_content_hash",
                    "_count",
                    ".schema_version",
                    ".contract_id",
                    ".fallback_policy",
                )
            )
        ]
        unique = []
        for leaf in candidates:
            if leaf not in unique and leaf not in direct[contract] and leaf not in SUBJECT_C:
                unique.append(leaf)
        out[contract] = set(unique[: targets[contract]])
    return out


def closure_for(contract: str, leaf: str) -> tuple[str, str]:
    owner, field = leaf.split(".", 1)
    if owner in {"PublicCutoffEndpoint"} or (owner == "PublicScopeIdentity" and field in {"cutoff_state"}):
        return "recipe", "recipe.cutoff_exact_present_absent"
    if owner == "VisibilityClosure":
        return "recipe", "recipe.visibility_universe_and_stable_bridge"
    if owner in {"PublicSourceLocator", "SourceRevisionContentPair"}:
        return "recipe", "recipe.locator_total_consumption_revision_partition"
    if owner == "TemporalAxisBasis":
        return "authority_root", "TemporalAxisAuthorityRecord"
    if owner == "TemporalDateEndpoint":
        return "authority_root", "TemporalEndpointAuthorityRecord"
    if owner == "TemporalVisit":
        return "authority_root", "VisitProjectionBinding"
    if owner == "TemporalEvent":
        return "authority_root", "EventProjectionBinding"
    if owner == "TemporalPhaseBand":
        return "authority_root", "PhaseProjectionBinding"
    if owner == "TemporalRiskAnchor":
        return "authority_root", "RiskProjectionBinding"
    if owner == "TemporalDomainTrack":
        return "authority_root", "DomainApplicabilityAuthorityRecord"
    if owner == "TemporalPendingDateItem":
        return "recipe", "recipe.pending_union_from_unprojectable_targets"
    if owner == "TemporalMembershipIndex":
        return "authority_root", "TemporalMemberAuthorityRecord"
    if owner in {"AEMHMatchHistoryEntry", "AEMHDecisionAuthorityRegistry", "AEMHThreadPrefixAnchor"}:
        return "authority_root", "AEMHAppendDecisionAuthorityRecord"
    if owner == "AEMHIdentityEvidence":
        return "authority_root", "AEMHEvidenceBindingAuthority"
    if owner in {"AEMHMatchThread", "AEMHHistoryMembershipIndex"}:
        return "authority_root", "AEMHThreadMembershipAuthority"
    if owner == "PublicAuthorityReceipt":
        if field == "receipt_content_hash":
            return "recipe", "recipe.upstream_roots_before_hashes_containers_packets"
        if field == "visibility_closure":
            return "authority_root", "PublicScopeUniverseAuthority"
        if field == "source_revision_content_pairs":
            return "authority_root", "SourceLocatorRevisionBinding"
        if field == "scope_identity":
            return "authority_root", "TemporalAuthorityScopeIdentity"
        return "authority_root", "TemporalProjectionAcceptanceReceipt"
    if owner in {"SubjectTemporalAuthorityPacket", "AEMHMatchHistoryAuthorityPacket"}:
        if field == "packet_content_hash":
            return "recipe", "recipe.upstream_roots_before_hashes_containers_packets"
        if field == "receipt":
            return "authority_root", "TemporalProjectionAcceptanceReceipt"
        return "authority_root", "TemporalProjectionAuthorityRegistry"
    if owner == "SubjectTemporalPublicProjection":
        authority_by_field = {
            "axis_basis": "TemporalAxisAuthorityRecord",
            "domain_tracks": "DomainApplicabilityAuthorityRecord",
            "events": "EventProjectionBinding",
            "membership_index": "TemporalMemberAuthorityRecord",
            "pending_date_items": "TemporalMemberAuthorityRecord",
            "phase_bands": "PhaseProjectionBinding",
            "projection_id": "TemporalProjectionAuthorityRegistry",
            "receipt_ref": "TemporalProjectionAcceptanceReceipt",
            "risk_anchors": "RiskProjectionBinding",
            "scope_identity": "TemporalAuthorityScopeIdentity",
            "source_locators": "SourceLocatorRevisionBinding",
            "visits": "VisitProjectionBinding",
        }
        if field == "projection_content_hash":
            return "recipe", "recipe.upstream_roots_before_hashes_containers_packets"
        if field in authority_by_field:
            return "authority_root", authority_by_field[field]
    if owner == "AEMHMatchHistoryPublicProjection":
        authority_by_field = {
            "accepted_thread_prefixes": "AEMHDecisionAuthorityRegistry",
            "cutoff_endpoint": "CutoffEndpointBindingAuthority",
            "membership_index": "AEMHThreadMembershipAuthority",
            "previous_projection_content_hash": "AEMHDecisionAuthorityRegistry",
            "previous_projection_ref": "AEMHDecisionAuthorityRegistry",
            "projection_id": "TemporalProjectionAuthorityRegistry",
            "receipt_ref": "TemporalProjectionAcceptanceReceipt",
            "scope_identity": "TemporalAuthorityScopeIdentity",
            "source_locators": "SourceLocatorRevisionBinding",
            "threads": "AEMHThreadMembershipAuthority",
        }
        if field == "projection_content_hash":
            return "recipe", "recipe.upstream_roots_before_hashes_containers_packets"
        if field in authority_by_field:
            return "authority_root", authority_by_field[field]
    raise RuntimeError(f"no exact closure emitter for {contract}::{leaf}")


def build_controlled_policies() -> dict[str, Any]:
    return {
        "phase_code_to_native_zh": {
            "screening": "筛选期",
            "baseline": "基线期",
            "treatment": "治疗期",
            "follow_up": "随访期",
            "unscheduled": "非计划阶段",
        },
        "timezone_day_zero": {
            "timezone": "Asia/Shanghai",
            "anchor_is_day_zero": {"formula": "calendar_delta", "study_day_zero_exists": True},
            "anchor_is_day_one": {
                "before_anchor": "calendar_delta",
                "on_or_after_anchor": "calendar_delta+1",
                "study_day_zero_exists": False,
            },
        },
        "date_state_range_projection": {
            "exact": {
                "candidate_min": 1,
                "candidate_max": None,
                "exact_required": True,
                "geometry_rule": "point",
                "main_axis_rule": "authorized",
                "absence_and_coverage_proof": False,
            },
            "partial": {
                "candidate_min": 1,
                "candidate_max": None,
                "exact_required": False,
                "geometry_rule": "candidate_envelope",
                "main_axis_rule": "bounded_and_authorized",
                "absence_and_coverage_proof": False,
            },
            "conflicted": {
                "candidate_min": 2,
                "candidate_max": None,
                "exact_required": False,
                "geometry_rule": "candidate_envelope",
                "main_axis_rule": "bounded_and_authorized",
                "absence_and_coverage_proof": False,
            },
            "missing": {
                "candidate_min": None,
                "candidate_max": 0,
                "exact_required": False,
                "geometry_rule": "none",
                "main_axis_rule": "forbidden",
                "absence_and_coverage_proof": True,
            },
        },
        "empty_domain_applicability": {
            "nonempty_membership": "applicable",
            "empty_membership": ["not_applicable", "not_provided"],
            "empty_requires_external_authority_and_coverage": True,
        },
        "aemh_event_match_reason_transitions": {
            "reminder_created": ["match_decided"],
            "match_decided": ["withdrawn"],
            "withdrawn": ["reappeared"],
            "reappeared": [],
            "match_states": ["ambiguous", "exact", "rejected"],
            "risk_lifecycle_effect": "none",
        },
    }


def build_external_registry_root(policy_hashes: dict[str, str]) -> dict[str, Any]:
    record = sealed(
        {
            "accepted_record_ref": "synthetic-accepted:temporal-projection-authority:20260820",
            "authority_scope": AUTHORITY_SCOPE,
            "non_clinical": True,
            "contract_id": CONTRACT_ID,
            "schema_version": SCHEMA_VERSION,
            "policy_hashes": [
                {"policy_ref": name, "policy_content_hash": policy_hashes[name]}
                for name in sorted(policy_hashes)
            ],
            "coverage": {
                "a_direct": 53,
                "b_deterministic_derived": 46,
                "c_accepted_semantic": 4,
                "d_unconstructible": 169,
                "unexplained_after": 0,
            },
        },
        "record_content_hash",
    )
    root = sealed(
        {
            "registry_id": "registry:r5-s5:synthetic-temporal-projection-acceptance:20260820",
            "authority_scope": AUTHORITY_SCOPE,
            "non_clinical": True,
            "accepted_records": [record],
        },
        "root_content_hash",
    )
    if record["record_content_hash"] != EXPECTED_ACCEPTED_RECORD_CONTENT_HASH:
        raise RuntimeError("accepted record content drift")
    if EXPECTED_EXTERNAL_REGISTRY_ROOT_CONTENT_HASH is not None and root["root_content_hash"] != EXPECTED_EXTERNAL_REGISTRY_ROOT_CONTENT_HASH:
        raise RuntimeError("external registry root drift")
    if digest(root) != EXPECTED_EXTERNAL_REGISTRY_SECTION_CANONICAL_SHA256:
        raise RuntimeError("external registry canonical section drift")
    return root


def make_candidate_bundle(
    candidate_ref: str,
    authority_record: dict[str, Any],
    operational_evidence: dict[str, Any],
    registry_id: str,
    registry_root_content_hash: str,
    accepted_record_ref: str,
    accepted_record_content_hash: str,
) -> dict[str, Any]:
    claim = sealed(
        {
            "registry_id": registry_id,
            "registry_root_content_hash": registry_root_content_hash,
            "accepted_record_ref": accepted_record_ref,
            "accepted_record_content_hash": accepted_record_content_hash,
            "authority_record_content_hash": authority_record["record_content_hash"],
        },
        "claim_content_hash",
    )
    receipt = sealed(
        {
            "receipt_id": f"receipt:{candidate_ref}",
            "candidate_ref": candidate_ref,
            "registry_claim_content_hash": claim["claim_content_hash"],
            "authority_record_content_hash": authority_record["record_content_hash"],
            "operational_evidence_content_hash": operational_evidence["evidence_content_hash"],
        },
        "receipt_content_hash",
    )
    return sealed(
        {
            "candidate_ref": candidate_ref,
            "authority_record": authority_record,
            "operational_evidence": operational_evidence,
            "registry_claim": claim,
            "receipt": receipt,
        },
        "bundle_content_hash",
    )


def build_candidate_catalog(external_root: dict[str, Any]) -> list[dict[str, Any]]:
    accepted = external_root["accepted_records"][0]
    operational_evidence = sealed(
        {
            "evaluation_instance_ref": "evaluation:valid",
            "observed_sequence": 1,
            "transport_digest": "9" * 64,
        },
        "evidence_content_hash",
    )
    valid = make_candidate_bundle(
        "candidate:valid",
        copy.deepcopy(accepted),
        operational_evidence,
        external_root["registry_id"],
        external_root["root_content_hash"],
        accepted["accepted_record_ref"],
        accepted["record_content_hash"],
    )
    forged_record = copy.deepcopy(accepted)
    forged_record["accepted_record_ref"] = "attacker:accepted-record"
    forged_record["policy_hashes"] = [
        {"policy_ref": f"attacker-policy-{index}", "policy_content_hash": f"{index}" * 64}
        for index in range(1, 6)
    ]
    forged_record = sealed(forged_record, "record_content_hash")
    forged_all = make_candidate_bundle(
        "candidate:forged-all-resealed",
        forged_record,
        operational_evidence,
        "registry:attacker-owned",
        "e" * 64,
        "attacker:accepted-record",
        "d" * 64,
    )
    wrong_record = make_candidate_bundle(
        "candidate:wrong-record-resealed",
        forged_record,
        operational_evidence,
        external_root["registry_id"],
        external_root["root_content_hash"],
        "attacker:accepted-record",
        "d" * 64,
    )
    bad_receipt = json.loads(json.dumps(valid))
    bad_receipt["candidate_ref"] = "candidate:bad-receipt"
    bad_receipt["receipt"]["candidate_ref"] = "candidate:bad-receipt"
    bad_receipt["receipt"]["registry_claim_content_hash"] = "0" * 64
    bad_receipt["receipt"] = sealed(bad_receipt["receipt"], "receipt_content_hash")
    bad_receipt = sealed(bad_receipt, "bundle_content_hash")
    changed_policy_record = copy.deepcopy(accepted)
    changed_policy_record["policy_hashes"][0]["policy_content_hash"] = "f" * 64
    changed_policy_record = sealed(changed_policy_record, "record_content_hash")
    changed_policy = make_candidate_bundle(
        "candidate:policy-payload-resealed",
        changed_policy_record,
        operational_evidence,
        external_root["registry_id"],
        external_root["root_content_hash"],
        accepted["accepted_record_ref"],
        accepted["record_content_hash"],
    )
    operational_variant = sealed(
        {
            "evaluation_instance_ref": "evaluation:valid-variant",
            "observed_sequence": 2,
        },
        "evidence_content_hash",
    )
    valid_operational_variant = make_candidate_bundle(
        "candidate:valid-operational-variant",
        copy.deepcopy(accepted),
        operational_variant,
        external_root["registry_id"],
        external_root["root_content_hash"],
        accepted["accepted_record_ref"],
        accepted["record_content_hash"],
    )
    return [valid, valid_operational_variant, forged_all, wrong_record, bad_receipt, changed_policy]


def sample_value(schema: dict[str, Any], type_name: str, field_name: str, index: int = 1) -> Any:
    if type_name.startswith("enum:"):
        return schema["enums"][type_name.split(":", 1)[1]][0]
    if type_name in schema["objects"] or type_name in schema["named_types"]:
        return sample_object(schema, type_name)
    if type_name in {"string", "discriminated_schema_object"}:
        return f"{field_name}:{index}"
    if type_name == "integer":
        return index
    if type_name == "boolean":
        return False
    if type_name == "sha256":
        return f"{index % 10}" * 64
    if type_name == "date":
        return f"2026-01-{index:02d}"
    if type_name == "partial_date":
        return "2026-01"
    raise ValueError(f"cannot sample undeclared type: {type_name}")


def sample_object(schema: dict[str, Any], type_name: str) -> dict[str, Any]:
    definitions = schema["objects"] | schema["named_types"]
    definition = definitions[type_name]
    value: dict[str, Any] = {}
    for field_name, field in definition["properties"].items():
        constraints = field["constraints"]
        if "const" in constraints:
            scalar = constraints["const"]
        else:
            scalar = sample_value(schema, field["type"], field_name)
        if field["cardinality"] == "many":
            count = max(1, constraints.get("min_items", 0))
            items = [sample_value(schema, field["type"], field_name, index + 1) for index in range(count)]
            value[field_name] = sorted(set(items)) if constraints.get("sorted_unique") else items
        else:
            value[field_name] = scalar
    if type_name == "TemporalEndpointAuthorityRecord":
        value["main_axis_projectable"] = True
        value["geometry"] = "point"
        value["date_state"] = "exact"
    if type_name == "DomainApplicabilityAuthorityRecord":
        value["applicability_state"] = "applicable"
        value["empty_state_authority_ref"] = None
    hash_field = SELF_HASH_FIELDS.get(type_name)
    if hash_field:
        value = sealed(value, hash_field)
    return value


def build_authority_fixtures(schema: dict[str, Any], roots: list[str]) -> list[dict[str, Any]]:
    fixtures = []
    for root in roots:
        fixture = {
            "fixture_id": f"authority:{root}",
            "object_type": root,
            "content_hash_field": SELF_HASH_FIELDS[root],
            "value": sample_object(schema, root),
        }
        fixtures.append(sealed(fixture, "fixture_content_hash"))
    event_fixture = next((item for item in fixtures if item["object_type"] == "EventProjectionBinding"), None)
    if event_fixture is not None:
        second = copy.deepcopy(event_fixture)
        second["fixture_id"] = "authority:EventProjectionBinding:2"
        second["value"]["binding_ref"] = "binding_ref:2"
        second["value"]["event_ref"] = "event_ref:2"
        second["value"]["actual_activity_ref"] = "actual_activity_ref:2"
        second["value"]["event_content_identity"] = "2" * 64
        second["value"]["source_locator_refs"] = ["source_locator_refs:2"]
        second["value"] = sealed({key: value for key, value in second["value"].items() if key != "binding_content_hash"}, "binding_content_hash")
        second = sealed({key: value for key, value in second.items() if key != "fixture_content_hash"}, "fixture_content_hash")
        fixtures.append(second)
    fixture_by_type = {item["object_type"]: item for item in fixtures if item["fixture_id"] == f"authority:{item['object_type']}"}
    if "AEMHAppendDecisionAuthorityRecord" in fixture_by_type and "AEMHEvidenceBindingAuthority" in fixture_by_type:
        decision_fixture = fixture_by_type["AEMHAppendDecisionAuthorityRecord"]
        evidence_ref = fixture_by_type["AEMHEvidenceBindingAuthority"]["value"]["binding_ref"]
        decision_fixture["value"]["evidence_binding_refs"] = [evidence_ref]
        decision_fixture["value"] = sealed({key: value for key, value in decision_fixture["value"].items() if key != "decision_content_hash"}, "decision_content_hash")
        replacement = sealed({key: value for key, value in decision_fixture.items() if key != "fixture_content_hash"}, "fixture_content_hash")
        fixtures[fixtures.index(decision_fixture)] = replacement
    return fixtures


class LazyAuthorityProjectionExecutor:
    def __init__(self, authority_fixtures: list[dict[str, Any]]) -> None:
        self.catalog = {fixture["fixture_id"]: fixture for fixture in authority_fixtures}
        self.consumed_fixture_refs: list[str] = []
        self.consumed_field_paths: list[str] = []
        self.verified_fixture_pins: list[str] = []
        self.scope_checked: set[str] = set()

    def _resolve(self, fixture_ref: str, object_type: str) -> dict[str, Any]:
        fixture = self.catalog.get(fixture_ref)
        if fixture is None or fixture["object_type"] != object_type:
            raise RuntimeError("TPA_AUTHORITY_FIXTURE_REF_IDENTITY_MISMATCH")
        if digest({key: value for key, value in fixture.items() if key != "fixture_content_hash"}) != fixture["fixture_content_hash"]:
            raise RuntimeError("TPA_AUTHORITY_FIXTURE_CONTENT_HASH_MISMATCH")
        hash_field = fixture["content_hash_field"]
        if digest({key: value for key, value in fixture["value"].items() if key != hash_field}) != fixture["value"][hash_field]:
            raise RuntimeError("TPA_AUTHORITY_OBJECT_CONTENT_HASH_MISMATCH")
        if fixture_ref not in self.consumed_fixture_refs:
            self.consumed_fixture_refs.append(fixture_ref)
            self.verified_fixture_pins.append(f"{fixture_ref}={fixture['fixture_content_hash']}")
        return fixture["value"]

    def _record(self, fixture_ref: str, field_path: str) -> None:
        path = f"{fixture_ref}::value.{field_path}"
        if path not in self.consumed_field_paths:
            self.consumed_field_paths.append(path)

    def _scope_prerequisite(self, fixture_ref: str, object_type: str, value: dict[str, Any]) -> None:
        if object_type == "TemporalAuthorityScopeIdentity" or fixture_ref in self.scope_checked:
            return
        scope_value = value.get("scope_identity")
        if scope_value is None:
            return
        self.scope_checked.add(fixture_ref)
        accepted_scope = self._resolve("authority:TemporalAuthorityScopeIdentity", "TemporalAuthorityScopeIdentity")
        for key in IDENTITY_FIELDS:
            self._record("authority:TemporalAuthorityScopeIdentity", key)
            self._record(fixture_ref, f"scope_identity.{key}")
            if scope_value[key] != accepted_scope[key]:
                raise RuntimeError("TPA_AUTHORITY_SCOPE_MISMATCH")

    def read(self, object_type: str, field_name: str, fixture_ref: str | None = None) -> Any:
        resolved_ref = fixture_ref or f"authority:{object_type}"
        value = self._resolve(resolved_ref, object_type)
        self._scope_prerequisite(resolved_ref, object_type, value)
        if field_name not in value:
            raise RuntimeError("TPA_AUTHORITY_SOURCE_FIELD_UNRESOLVED")
        self._record(resolved_ref, field_name)
        return copy.deepcopy(value[field_name])

    @staticmethod
    def seal_target(value: dict[str, Any], hash_field: str) -> dict[str, Any]:
        return sealed({key: item for key, item in value.items() if key != hash_field}, hash_field)

    @staticmethod
    def direct_source(contract: str, owner: str, field: str) -> tuple[str, str] | None:
        aliases: dict[str, dict[str, tuple[str, str]]] = {
            "PublicAuthorityReceipt": {
                "receipt_id": ("TemporalProjectionAcceptanceReceipt", "receipt_id"),
            },
            "TemporalAxisBasis": {name: ("TemporalAxisAuthorityRecord", name) for name in ("axis_ref", "source_locator_refs", "study_day_anchor_event_ref", "study_day_zero_exists")},
            "TemporalDateEndpoint": {
                **{name: ("TemporalEndpointAuthorityRecord", name) for name in ("candidate_values", "exact_date", "main_axis_projectable", "range_end", "range_projection_authorized", "range_start", "source_locator_refs", "study_day")},
                "state": ("TemporalEndpointAuthorityRecord", "date_state"),
            },
            "TemporalDomainTrack": {name: ("DomainApplicabilityAuthorityRecord", name) for name in ("applicability_state", "domain", "event_refs", "risk_anchor_refs")},
            "TemporalEvent": {
                "applicability_state": ("EventProjectionBinding", "applicability_state"), "event_content_identity": ("EventProjectionBinding", "event_content_identity"),
                "geometry": ("EventProjectionBinding", "geometry"), "risk_anchor_refs": ("EventProjectionBinding", "risk_anchor_refs"),
                "source_locator_refs": ("EventProjectionBinding", "source_locator_refs"), "visit_ref": ("EventProjectionBinding", "visit_ref"),
            },
            "TemporalMembershipIndex": {"pending_date_refs": ("TemporalMemberAuthorityRecord", "pending_date_refs")},
            "TemporalPhaseBand": {name: ("PhaseProjectionBinding", name) for name in ("geometry", "phase_label_zh", "phase_ref", "source_locator_refs")},
            "TemporalRiskAnchor": {
                "geometry": ("RiskProjectionBinding", "geometry"), "risk_anchor_ref": ("RiskProjectionBinding", "binding_ref"),
                "source_locator_refs": ("RiskProjectionBinding", "source_locator_refs"),
            },
            "TemporalVisit": {name: ("VisitProjectionBinding", name) for name in ("accepted_assignment_ref", "actual_encounter_ref", "phase_ref", "planned_visit_ref", "source_locator_refs", "visit_kind", "visit_ref")},
            "AEMHIdentityEvidence": {
                "evidence_kind": ("AEMHEvidenceBindingAuthority", "evidence_kind"), "source_locator_ref": ("AEMHEvidenceBindingAuthority", "source_locator_ref"),
                "source_raw_payload_hash": ("AEMHEvidenceBindingAuthority", "source_raw_payload_hash"),
            },
            "AEMHMatchHistoryEntry": {
                "entry_id": ("AEMHAppendDecisionAuthorityRecord", "entry_id"), "event_kind": ("AEMHAppendDecisionAuthorityRecord", "event_kind"),
                "identity_evidence_refs": ("AEMHAppendDecisionAuthorityRecord", "evidence_binding_refs"),
                "later_fact_content_identities": ("AEMHAppendDecisionAuthorityRecord", "later_fact_content_identities"),
                "later_fact_refs": ("AEMHAppendDecisionAuthorityRecord", "later_fact_refs"), "match_state": ("AEMHAppendDecisionAuthorityRecord", "match_state"),
                "prior_entry_hash": ("AEMHAppendDecisionAuthorityRecord", "prior_entry_hash"), "reason_code": ("AEMHAppendDecisionAuthorityRecord", "reason_code"),
                "retained_evidence_locator_refs": ("AEMHAppendDecisionAuthorityRecord", "retained_evidence_locator_refs"),
                "seq": ("AEMHAppendDecisionAuthorityRecord", "seq"), "snapshot_ref": ("AEMHAppendDecisionAuthorityRecord", "snapshot_ref"),
            },
            "AEMHMatchHistoryPublicProjection": {
                "previous_projection_content_hash": ("AEMHDecisionAuthorityRegistry", "previous_projection_content_hash"),
                "previous_projection_ref": ("AEMHDecisionAuthorityRegistry", "previous_projection_ref"),
                "projection_id": ("TemporalProjectionAuthorityRegistry", "aemh_projection_id"),
                "receipt_ref": ("TemporalProjectionAcceptanceReceipt", "receipt_id"),
            },
            "SubjectTemporalPublicProjection": {
                "projection_id": ("TemporalProjectionAuthorityRegistry", "subject_projection_id"),
                "receipt_ref": ("TemporalProjectionAcceptanceReceipt", "receipt_id"),
            },
            "AEMHMatchThread": {
                "domain": ("AEMHThreadMembershipAuthority", "domain"), "evidence_locator_refs": ("AEMHThreadMembershipAuthority", "source_locator_refs"),
                "original_reminder_ref": ("AEMHThreadMembershipAuthority", "original_reminder_ref"),
            },
            "AEMHThreadPrefixAnchor": {
                "accepted_prefix_head_hash": ("AEMHAppendDecisionAuthorityRecord", "accepted_prefix_head_hash"),
                "accepted_prefix_seq": ("AEMHAppendDecisionAuthorityRecord", "accepted_prefix_seq"),
                "previous_thread_content_hash": ("AEMHAppendDecisionAuthorityRecord", "previous_thread_content_hash"),
                "thread_ref": ("AEMHAppendDecisionAuthorityRecord", "thread_ref"),
            },
        }
        return aliases.get(owner, {}).get(field)

    def scope(self) -> dict[str, Any]:
        return self.seal_target({key: self.read("TemporalAuthorityScopeIdentity", key) for key in (*IDENTITY_FIELDS, "spine_ref", "cutoff_state")}, "identity_content_hash")

    def endpoint(self) -> dict[str, Any]:
        source_fields = ("candidate_values", "exact_date", "main_axis_projectable", "range_end", "range_projection_authorized", "range_start", "source_locator_refs", "study_day")
        value = {key: self.read("TemporalEndpointAuthorityRecord", key) for key in source_fields}
        value["state"] = self.read("TemporalEndpointAuthorityRecord", "date_state")
        return self.seal_target(value, "endpoint_content_hash")

    def locator(self) -> dict[str, Any]:
        aliases = {
            "authority_entity_kind": "authority_entity_kind", "authority_entity_ref": "authority_entity_ref", "canonical_location": "canonical_location",
            "column_or_anchor": "field_path", "locator_ref": "locator_ref", "locator_variant": "locator_variant", "raw_payload_hash": "raw_payload_hash",
            "record_ref": "record_ref", "source_file_ref": "source_file_ref", "source_revision_content_hash": "source_revision_content_hash",
            "source_revision_ref": "source_revision_ref", "table_semantic": "table_semantic",
        }
        value = {target: self.read("SourceLocatorRevisionBinding", source) for target, source in aliases.items()}
        value["snapshot_ref"] = self.read("TemporalAuthorityScopeIdentity", "snapshot_ref")
        return self.seal_target(value, "locator_content_hash")

    def revision_pair(self) -> dict[str, Any]:
        return self.seal_target(
            {
                "accepted_content_hash": self.read("SourceLocatorRevisionBinding", "source_revision_content_hash"),
                "locator_refs": [self.read("SourceLocatorRevisionBinding", "locator_ref")],
                "revision_id": self.read("SourceLocatorRevisionBinding", "source_revision_ref"),
            },
            "pair_content_hash",
        )

    def visibility(self) -> dict[str, Any]:
        root = "PublicScopeUniverseAuthority"
        value = {
            "deep_link_eligible": self.read(root, "deep_link_eligible"), "evaluation_member_refs": self.read(root, "evaluation_member_refs"),
            "evaluation_site_refs": self.read(root, "evaluation_site_refs"), "hidden_member_refs": self.read(root, "hidden_member_refs"),
            "hidden_site_refs": self.read(root, "hidden_site_refs"), "projectable_member_refs": self.read(root, "projectable_member_refs"),
            "projectable_site_refs": self.read(root, "projectable_site_refs"), "subject_visibility_state": self.read(root, "visibility_state"),
            "visibility_decision_hash": self.read(root, "visibility_decision_hash"), "visibility_decision_id": self.read(root, "visibility_decision_id"),
        }
        value["hidden_member_count"] = len(value["hidden_member_refs"])
        value["hidden_site_count"] = len(value["hidden_site_refs"])
        return self.seal_target(value, "closure_content_hash")

    def cutoff(self) -> dict[str, Any]:
        root = "CutoffEndpointBindingAuthority"
        return self.seal_target({"exact_date": self.read(root, "exact_date"), "source_locator_refs": self.read(root, "source_locator_refs"), "state": self.read(root, "cutoff_state")}, "cutoff_content_hash")

    def axis(self) -> dict[str, Any]:
        root = "TemporalAxisAuthorityRecord"
        return self.seal_target(
            {"axis_ref": self.read(root, "axis_ref"), "cutoff_endpoint": self.endpoint(), "default_axis_mode": self.read(root, "default_axis_mode"), "source_locator_refs": self.read(root, "source_locator_refs"), "study_day_anchor_event_ref": self.read(root, "study_day_anchor_event_ref"), "study_day_zero_exists": self.read(root, "study_day_zero_exists"), "timezone": self.read(root, "timezone")},
            "axis_content_hash",
        )

    def visit(self) -> dict[str, Any]:
        root = "VisitProjectionBinding"
        actual_ref = self.read(root, "actual_endpoint_ref")
        nominal_ref = self.read(root, "nominal_endpoint_ref")
        return self.seal_target(
            {"accepted_assignment_ref": self.read(root, "accepted_assignment_ref"), "actual_encounter_ref": self.read(root, "actual_encounter_ref"), "actual_endpoint": self.endpoint() if actual_ref else None, "nominal_endpoint": self.endpoint() if nominal_ref else None, "phase_ref": self.read(root, "phase_ref"), "planned_visit_ref": self.read(root, "planned_visit_ref"), "source_locator_refs": self.read(root, "source_locator_refs"), "visit_kind": self.read(root, "visit_kind"), "visit_ref": self.read(root, "visit_ref")},
            "visit_content_hash",
        )

    def event(self, fixture_ref: str = "authority:EventProjectionBinding") -> dict[str, Any]:
        root = "EventProjectionBinding"
        return self.seal_target(
            {"applicability_state": self.read(root, "applicability_state", fixture_ref), "domain": self.read(root, "semantic_domain", fixture_ref), "end_endpoint": self.endpoint(), "event_content_identity": self.read(root, "event_content_identity", fixture_ref), "event_ref": self.read(root, "event_ref", fixture_ref), "geometry": self.read(root, "geometry", fixture_ref), "risk_anchor_refs": self.read(root, "risk_anchor_refs", fixture_ref), "source_locator_refs": self.read(root, "source_locator_refs", fixture_ref), "start_endpoint": self.endpoint(), "subtype": self.read(root, "semantic_subtype", fixture_ref), "visit_ref": self.read(root, "visit_ref", fixture_ref)},
            "event_content_hash",
        )

    def events(self) -> list[dict[str, Any]]:
        refs = sorted(ref for ref, fixture in self.catalog.items() if fixture["object_type"] == "EventProjectionBinding")
        return sorted((self.event(ref) for ref in refs), key=lambda item: (item["event_ref"], item["event_content_identity"]))

    def phase(self) -> dict[str, Any]:
        root = "PhaseProjectionBinding"
        return self.seal_target({"end_endpoint": self.endpoint(), "geometry": self.read(root, "geometry"), "phase_label_zh": self.read(root, "phase_label_zh"), "phase_ref": self.read(root, "phase_ref"), "source_locator_refs": self.read(root, "source_locator_refs"), "start_endpoint": self.endpoint()}, "phase_content_hash")

    def risk(self) -> dict[str, Any]:
        root = "RiskProjectionBinding"
        return self.seal_target({"domain": self.read(root, "semantic_domain"), "end_endpoint": self.endpoint(), "event_ref": self.read(root, "event_ref"), "geometry": self.read(root, "geometry"), "risk_anchor_ref": self.read(root, "binding_ref"), "risk_content_identity": self.read(root, "risk_content_identity"), "risk_ref": self.read(root, "risk_ref"), "risk_type_zh": self.read(root, "risk_type_zh"), "severity": self.read(root, "severity"), "source_locator_refs": self.read(root, "source_locator_refs"), "start_endpoint": self.endpoint(), "visit_ref": self.read(root, "visit_ref")}, "risk_anchor_content_hash")

    def domain(self) -> dict[str, Any]:
        root = "DomainApplicabilityAuthorityRecord"
        return self.seal_target({name: self.read(root, name) for name in ("applicability_state", "domain", "event_refs", "risk_anchor_refs")}, "track_content_hash")

    def membership(self) -> dict[str, Any]:
        root = "TemporalMemberAuthorityRecord"
        return self.seal_target({name: self.read(root, name) for name in ("event_refs", "pending_date_refs", "phase_refs", "risk_anchor_refs", "source_locator_refs", "visit_refs")}, "membership_content_hash")

    def pending(self) -> dict[str, Any]:
        root = "TemporalMemberAuthorityRecord"
        pending_refs = self.read(root, "pending_date_refs")
        return self.seal_target({"domain": self.read(root, "pending_domain"), "end_endpoint": self.endpoint(), "item_kind": self.read(root, "pending_item_kind"), "item_ref": self.read(root, "pending_item_ref"), "pending_ref": pending_refs[0], "source_locator_refs": self.read(root, "source_locator_refs"), "start_endpoint": self.endpoint(), "target_content_hash": self.read(root, "pending_target_content_hash")}, "pending_content_hash")

    def evidence(self) -> dict[str, Any]:
        root = "AEMHEvidenceBindingAuthority"
        return self.seal_target({"entity_content_identity": self.read(root, "entity_content_identity"), "entity_ref": self.read(root, "entity_ref"), "evidence_kind": self.read(root, "evidence_kind"), "evidence_ref": self.read(root, "binding_ref"), "source_locator_content_hash": self.read(root, "source_locator_content_hash"), "source_locator_ref": self.read(root, "source_locator_ref"), "source_raw_payload_hash": self.read(root, "source_raw_payload_hash")}, "evidence_content_hash")

    def entry(self) -> dict[str, Any]:
        root = "AEMHAppendDecisionAuthorityRecord"
        return self.seal_target({"entry_id": self.read(root, "entry_id"), "event_kind": self.read(root, "event_kind"), "identity_evidence": [self.evidence()], "identity_evidence_refs": self.read(root, "evidence_binding_refs"), "later_fact_content_identities": self.read(root, "later_fact_content_identities"), "later_fact_refs": self.read(root, "later_fact_refs"), "match_state": self.read(root, "match_state"), "prior_entry_hash": self.read(root, "prior_entry_hash"), "reason_code": self.read(root, "reason_code"), "retained_evidence_locator_refs": self.read(root, "retained_evidence_locator_refs"), "risk_lifecycle_effect": self.read(root, "risk_lifecycle_effect"), "seq": self.read(root, "seq"), "snapshot_ref": self.read(root, "snapshot_ref")}, "entry_hash")

    def prefix(self) -> dict[str, Any]:
        root = "AEMHAppendDecisionAuthorityRecord"
        return self.seal_target({"accepted_prefix_head_hash": self.read(root, "accepted_prefix_head_hash"), "accepted_prefix_seq": self.read(root, "accepted_prefix_seq"), "previous_thread_content_hash": self.read(root, "previous_thread_content_hash"), "thread_ref": self.read(root, "thread_ref")}, "prefix_content_hash")

    def thread(self) -> dict[str, Any]:
        root = "AEMHThreadMembershipAuthority"
        return self.seal_target({"candidate_content_identity": self.read(root, "original_candidate_content_identity"), "domain": self.read(root, "domain"), "evidence_locator_refs": self.read(root, "source_locator_refs"), "history_entries": [self.entry()], "original_candidate_ref": self.read(root, "original_candidate_ref"), "original_reminder_ref": self.read(root, "original_reminder_ref"), "project_ref": self.read("TemporalAuthorityScopeIdentity", "project_ref"), "site_ref": self.read("TemporalAuthorityScopeIdentity", "site_ref"), "subject_ref": self.read("TemporalAuthorityScopeIdentity", "subject_ref"), "thread_ref": self.read(root, "thread_ref")}, "thread_content_hash")

    def aemh_membership(self) -> dict[str, Any]:
        root = "AEMHThreadMembershipAuthority"
        return self.seal_target({"candidate_refs": self.read(root, "candidate_refs"), "later_fact_refs": self.read(root, "later_fact_refs"), "source_locator_refs": self.read(root, "source_locator_refs"), "thread_refs": [self.read(root, "thread_ref")]}, "membership_content_hash")

    def subject_projection(self) -> dict[str, Any]:
        return self.seal_target({"axis_basis": self.axis(), "contract_id": "subject-temporal-public-v1", "domain_tracks": [self.domain()], "events": self.events(), "fallback_policy": "fail_closed_no_nearest", "membership_index": self.membership(), "pending_date_items": [self.pending()], "phase_bands": [self.phase()], "projection_id": self.read("TemporalProjectionAuthorityRegistry", "subject_projection_id"), "receipt_ref": self.read("TemporalProjectionAcceptanceReceipt", "receipt_id"), "risk_anchors": [self.risk()], "schema_version": "1.0.0", "scope_identity": self.scope(), "source_locators": [self.locator()], "visits": [self.visit()]}, "projection_content_hash")

    def aemh_projection(self) -> dict[str, Any]:
        root = "AEMHDecisionAuthorityRegistry"
        return self.seal_target({"accepted_thread_prefixes": [self.prefix()], "contract_id": "aemh-match-history-public-v1", "cutoff_endpoint": self.cutoff(), "fallback_policy": "fail_closed_no_nearest", "membership_index": self.aemh_membership(), "previous_projection_content_hash": self.read(root, "previous_projection_content_hash"), "previous_projection_ref": self.read(root, "previous_projection_ref"), "projection_id": self.read("TemporalProjectionAuthorityRegistry", "aemh_projection_id"), "receipt_ref": self.read("TemporalProjectionAcceptanceReceipt", "receipt_id"), "schema_version": "1.0.0", "scope_identity": self.scope(), "source_locators": [self.locator()], "threads": [self.thread()]}, "projection_content_hash")

    def receipt(self, contract: str) -> dict[str, Any]:
        projection = self.subject_projection() if contract == "subject-temporal-public-v1" else self.aemh_projection()
        projection_id = self.read("TemporalProjectionAuthorityRegistry", "subject_projection_id" if contract == "subject-temporal-public-v1" else "aemh_projection_id")
        visibility = self.visibility()
        return self.seal_target({"audience_contract_id": contract, "authority_contract_id": CONTRACT_ID, "authority_contract_version": SCHEMA_VERSION, "evaluation_content_identities": sorted([visibility["closure_content_hash"], projection["projection_content_hash"]]), "public_projection_content_hash": projection["projection_content_hash"], "public_projection_id": projection_id, "receipt_id": self.read("TemporalProjectionAcceptanceReceipt", "receipt_id"), "receipt_variant": "subject_temporal" if contract == "subject-temporal-public-v1" else "aemh_match_history", "scope_identity": self.scope(), "source_revision_content_pairs": [self.revision_pair()], "visibility_closure": visibility}, "receipt_content_hash")

    def target_object(self, contract: str, owner: str) -> dict[str, Any]:
        builders = {
            "PublicAuthorityReceipt": lambda: self.receipt(contract), "PublicScopeIdentity": self.scope, "SourceRevisionContentPair": self.revision_pair,
            "VisibilityClosure": self.visibility, "TemporalAxisBasis": self.axis, "TemporalDateEndpoint": self.endpoint, "TemporalDomainTrack": self.domain,
            "TemporalEvent": lambda: self.event(), "TemporalMembershipIndex": self.membership, "TemporalPhaseBand": self.phase, "TemporalRiskAnchor": self.risk,
            "TemporalVisit": self.visit, "AEMHIdentityEvidence": self.evidence, "AEMHMatchHistoryEntry": self.entry,
            "AEMHMatchHistoryPublicProjection": self.aemh_projection, "SubjectTemporalPublicProjection": self.subject_projection,
            "AEMHMatchThread": self.thread, "AEMHThreadPrefixAnchor": self.prefix,
        }
        if owner not in builders:
            raise RuntimeError(f"TPA_AUTHORITY_TARGET_OWNER_UNRESOLVED:{owner}")
        return builders[owner]()

    def projected_field(self, contract: str, owner: str, field: str) -> Any:
        if owner == "SubjectTemporalAuthorityPacket" and field == "projection":
            return self.subject_projection()
        if owner == "SubjectTemporalAuthorityPacket" and field == "receipt":
            return self.receipt(contract)
        if owner == "AEMHMatchHistoryAuthorityPacket" and field == "projection":
            return self.aemh_projection()
        if owner == "AEMHMatchHistoryAuthorityPacket" and field == "receipt":
            return self.receipt(contract)
        if owner == "SubjectTemporalPublicProjection":
            subject_fields = {
                "axis_basis": self.axis, "domain_tracks": lambda: [self.domain()], "events": self.events,
                "membership_index": self.membership, "pending_date_items": lambda: [self.pending()], "phase_bands": lambda: [self.phase()],
                "risk_anchors": lambda: [self.risk()], "scope_identity": self.scope, "source_locators": lambda: [self.locator()], "visits": lambda: [self.visit()],
            }
            if field in subject_fields:
                return subject_fields[field]()
            return self.subject_projection()[field]
        if owner == "AEMHMatchHistoryPublicProjection":
            aemh_fields = {
                "accepted_thread_prefixes": lambda: [self.prefix()], "cutoff_endpoint": self.cutoff, "membership_index": self.aemh_membership,
                "scope_identity": self.scope, "source_locators": lambda: [self.locator()], "threads": lambda: [self.thread()],
            }
            if field in aemh_fields:
                return aemh_fields[field]()
            return self.aemh_projection()[field]
        if owner == "TemporalEvent" and field in {"start_endpoint", "end_endpoint"}:
            return self.endpoint()
        if owner == "TemporalPhaseBand" and field in {"start_endpoint", "end_endpoint"}:
            return self.endpoint()
        if owner == "TemporalRiskAnchor" and field in {"start_endpoint", "end_endpoint"}:
            return self.endpoint()
        if owner == "TemporalVisit" and field in {"actual_endpoint", "nominal_endpoint"}:
            source_field = "actual_endpoint_ref" if field == "actual_endpoint" else "nominal_endpoint_ref"
            return self.endpoint() if self.read("VisitProjectionBinding", source_field) else None
        if owner == "TemporalAxisBasis" and field == "cutoff_endpoint":
            return self.endpoint()
        if owner == "PublicAuthorityReceipt" and field == "scope_identity":
            return self.scope()
        if owner == "PublicAuthorityReceipt" and field == "visibility_closure":
            return self.visibility()
        if owner == "PublicAuthorityReceipt" and field == "source_revision_content_pairs":
            return [self.revision_pair()]
        if owner == "AEMHMatchHistoryEntry" and field == "identity_evidence":
            return [self.evidence()]
        if owner == "AEMHMatchThread" and field == "history_entries":
            return [self.entry()]
        return self.target_object(contract, owner)[field]

    @staticmethod
    def _require_exact_params(params: dict[str, Any] | None, keys: set[str]) -> dict[str, Any]:
        if not isinstance(params, dict) or set(params) != keys:
            raise RuntimeError("TPA_AUTHORITY_OP_PARAMS_MISMATCH")
        return params

    def execute_direct_field(self, contract: str, owner: str, field: str, params: dict[str, Any] | None) -> Any:
        resolved = self._require_exact_params(params, {"source_fixture_ref", "source_field_path"})
        direct = self.direct_source(contract, owner, field)
        if direct is None:
            raise RuntimeError("TPA_AUTHORITY_OP_DISPATCH_MISMATCH")
        object_type, source_field = direct
        if resolved != {"source_fixture_ref": f"authority:{object_type}", "source_field_path": source_field}:
            raise RuntimeError("TPA_AUTHORITY_OP_PARAMS_MISMATCH")
        return self.read(object_type, source_field, resolved["source_fixture_ref"])

    def execute_derive_value(self, contract: str, owner: str, field: str, params: dict[str, Any] | None) -> Any:
        resolved = self._require_exact_params(params, {"transform", "input_fixture_refs", "input_field_paths", "selector_contract"})
        if (
            owner != "PublicAuthorityReceipt"
            or field != "public_projection_id"
            or resolved["transform"] != "select_contract_projection_id"
            or resolved["selector_contract"] != contract
            or resolved["input_fixture_refs"] != ["authority:TemporalProjectionAuthorityRegistry"]
            or resolved["input_field_paths"] != ["subject_projection_id", "aemh_projection_id"]
        ):
            raise RuntimeError("TPA_AUTHORITY_OP_PARAMS_MISMATCH")
        subject_id = self.read("TemporalProjectionAuthorityRegistry", "subject_projection_id")
        aemh_id = self.read("TemporalProjectionAuthorityRegistry", "aemh_projection_id")
        closed_map = {
            "subject-temporal-public-v1": subject_id,
            "aemh-match-history-public-v1": aemh_id,
        }
        return closed_map[contract]

    def execute_project_record(self, contract: str, owner: str, field: str, params: dict[str, Any] | None) -> Any:
        resolved = self._require_exact_params(
            params,
            {"selector_fixture_ref", "selector_object_type", "join_keys", "result_object_type", "result_field_path"},
        )
        if resolved["join_keys"] != list(IDENTITY_FIELDS) or resolved["result_field_path"] != f"{owner}.{field}":
            raise RuntimeError("TPA_AUTHORITY_OP_PARAMS_MISMATCH")
        fixture = self.catalog.get(resolved["selector_fixture_ref"])
        if fixture is None or fixture["object_type"] != resolved["selector_object_type"]:
            raise RuntimeError("TPA_AUTHORITY_FIXTURE_REF_IDENTITY_MISMATCH")
        output = self.projected_field(contract, owner, field)
        if not isinstance(output, dict):
            raise TypeError("TPA_AUTHORITY_OP_OUTPUT_TYPE_MISMATCH")
        return output

    def execute_assemble_sorted_records(self, contract: str, owner: str, field: str, params: dict[str, Any] | None) -> Any:
        resolved = self._require_exact_params(
            params,
            {"member_fixture_refs", "member_object_type", "stable_identity_fields", "uniqueness_fields", "result_object_type", "result_field_path", "assembly_cardinality"},
        )
        assembly_specs: dict[tuple[str, str], tuple[str, list[str], Any]] = {
            ("PublicAuthorityReceipt", "source_revision_content_pairs"): ("SourceLocatorRevisionBinding", ["revision_id"], lambda: [self.revision_pair()]),
            ("AEMHMatchHistoryEntry", "identity_evidence"): ("AEMHEvidenceBindingAuthority", ["evidence_ref"], lambda: [self.evidence()]),
            ("AEMHMatchThread", "history_entries"): ("AEMHAppendDecisionAuthorityRecord", ["seq", "entry_id"], lambda: [self.entry()]),
        }
        spec = assembly_specs.get((owner, field))
        if spec is None:
            raise RuntimeError("TPA_AUTHORITY_OP_DISPATCH_MISMATCH")
        source_type, identity_fields, builder = spec
        expected_refs = [f"authority:{source_type}"]
        if (
            resolved["member_fixture_refs"] != expected_refs
            or resolved["member_object_type"] != source_type
            or resolved["stable_identity_fields"] != identity_fields
            or resolved["uniqueness_fields"] != identity_fields
            or resolved["result_field_path"] != f"{owner}.{field}"
            or resolved["assembly_cardinality"] != "exact_one_or_more"
        ):
            raise RuntimeError("TPA_AUTHORITY_OP_PARAMS_MISMATCH")
        for fixture_ref in expected_refs:
            self._resolve(fixture_ref, source_type)
        records = builder()
        identities = [tuple(record[name] for name in identity_fields) for record in records]
        if not records or len(identities) != len(set(identities)):
            raise RuntimeError("TPA_AUTHORITY_ASSEMBLY_IDENTITY_MISMATCH")
        return [record for _, record in sorted(zip(identities, records), key=lambda pair: pair[0])]

    def execute_canonical_hash(self, contract: str, owner: str, field: str, params: dict[str, Any] | None) -> Any:
        resolved = self._require_exact_params(
            params,
            {"target_object_type", "target_hash_field", "ingredient_target_fields", "algorithm", "canonicalization"},
        )
        if resolved["algorithm"] != "sha256" or resolved["canonicalization"] != "utf8_nfc_canonical_json_sorted_keys_compact_no_nan":
            raise RuntimeError("TPA_AUTHORITY_OP_PARAMS_MISMATCH")
        if owner == "PublicAuthorityReceipt" and field == "public_projection_content_hash":
            target = self.subject_projection() if contract == "subject-temporal-public-v1" else self.aemh_projection()
        else:
            target = self.target_object(contract, owner)
        hash_field = resolved["target_hash_field"]
        if resolved["target_object_type"] not in {owner, "SubjectTemporalPublicProjection", "AEMHMatchHistoryPublicProjection"} or hash_field not in target:
            raise RuntimeError("TPA_AUTHORITY_OP_PARAMS_MISMATCH")
        ingredients = {key: value for key, value in target.items() if key != hash_field}
        if sorted(ingredients) != resolved["ingredient_target_fields"] or field != hash_field and owner != "PublicAuthorityReceipt":
            raise RuntimeError("TPA_AUTHORITY_OP_PARAMS_MISMATCH")
        computed = hashlib.sha256(canonical_bytes(ingredients)).hexdigest()
        if computed != target[hash_field]:
            raise RuntimeError("TPA_AUTHORITY_CANONICAL_HASH_MISMATCH")
        return computed

    def execute_project_contract(self, contract: str, owner: str, field: str, params: dict[str, Any] | None) -> Any:
        resolved = self._require_exact_params(
            params,
            {"contract", "source_owner_type", "source_field_path", "result_type", "result_cardinality", "projection_mode"},
        )
        if (
            resolved["contract"] != contract
            or resolved["source_owner_type"] != owner
            or resolved["source_field_path"] != f"{owner}.{field}"
            or resolved["projection_mode"] != "closed_nested_contract_projection"
            or field.endswith("hash")
        ):
            raise RuntimeError("TPA_AUTHORITY_OP_PARAMS_MISMATCH")
        return self.projected_field(contract, owner, field)

    def execute(self, contract: str, owner: str, field: str, op: str, params: dict[str, Any] | None) -> tuple[Any, dict[str, Any]]:
        if op == "direct_field":
            output = self.execute_direct_field(contract, owner, field, params)
        elif op == "derive_value":
            output = self.execute_derive_value(contract, owner, field, params)
        elif op == "project_record":
            output = self.execute_project_record(contract, owner, field, params)
        elif op == "assemble_sorted_records":
            output = self.execute_assemble_sorted_records(contract, owner, field, params)
        elif op == "canonical_hash":
            output = self.execute_canonical_hash(contract, owner, field, params)
        elif op == "project_contract":
            output = self.execute_project_contract(contract, owner, field, params)
        else:
            raise RuntimeError("TPA_AUTHORITY_OP_INVALID")
        trace_payload = {
            "op": op,
            "consumed_fixture_refs": self.consumed_fixture_refs,
            "consumed_field_paths": self.consumed_field_paths,
            "verified_fixture_pins": self.verified_fixture_pins,
            "output_canonical_json": canonical_bytes(output).decode("utf-8"),
            "output_content_hash": digest(output),
        }
        trace_payload["trace_content_hash"] = digest(trace_payload)
        return output, trace_payload


def authority_op_params(
    contract: str,
    owner: str,
    field: str,
    op: str,
    target: dict[str, Any],
    parent_objects: dict[str, Any],
) -> dict[str, Any]:
    params = {
        "direct_field_params": None,
        "derive_value_params": None,
        "project_record_params": None,
        "assemble_sorted_records_params": None,
        "canonical_hash_params": None,
        "project_contract_params": None,
    }
    if op == "direct_field":
        source = LazyAuthorityProjectionExecutor.direct_source(contract, owner, field)
        if source is None:
            raise RuntimeError("TPA_AUTHORITY_OP_DISPATCH_MISMATCH")
        params["direct_field_params"] = {"source_fixture_ref": f"authority:{source[0]}", "source_field_path": source[1]}
    elif op == "derive_value":
        params["derive_value_params"] = {
            "transform": "select_contract_projection_id",
            "input_fixture_refs": ["authority:TemporalProjectionAuthorityRegistry"],
            "input_field_paths": ["subject_projection_id", "aemh_projection_id"],
            "selector_contract": contract,
        }
    elif op == "project_record":
        selector_types = {
            ("PublicAuthorityReceipt", "scope_identity"): "TemporalAuthorityScopeIdentity",
            ("PublicAuthorityReceipt", "visibility_closure"): "PublicScopeUniverseAuthority",
        }
        selector_type = selector_types.get((owner, field), "TemporalEndpointAuthorityRecord")
        params["project_record_params"] = {
            "selector_fixture_ref": f"authority:{selector_type}",
            "selector_object_type": selector_type,
            "join_keys": list(IDENTITY_FIELDS),
            "result_object_type": target["type"],
            "result_field_path": f"{owner}.{field}",
        }
    elif op == "assemble_sorted_records":
        assembly_specs = {
            ("PublicAuthorityReceipt", "source_revision_content_pairs"): ("SourceLocatorRevisionBinding", ["revision_id"]),
            ("AEMHMatchHistoryEntry", "identity_evidence"): ("AEMHEvidenceBindingAuthority", ["evidence_ref"]),
            ("AEMHMatchThread", "history_entries"): ("AEMHAppendDecisionAuthorityRecord", ["seq", "entry_id"]),
        }
        source_type, identity_fields = assembly_specs[(owner, field)]
        params["assemble_sorted_records_params"] = {
            "member_fixture_refs": [f"authority:{source_type}"],
            "member_object_type": source_type,
            "stable_identity_fields": identity_fields,
            "uniqueness_fields": identity_fields,
            "result_object_type": target["type"],
            "result_field_path": f"{owner}.{field}",
            "assembly_cardinality": "exact_one_or_more",
        }
    elif op == "canonical_hash":
        if owner == "PublicAuthorityReceipt":
            object_type = "SubjectTemporalPublicProjection" if contract == "subject-temporal-public-v1" else "AEMHMatchHistoryPublicProjection"
            hash_field = "projection_content_hash"
        else:
            object_type = owner
            hash_field = field
        params["canonical_hash_params"] = {
            "target_object_type": object_type,
            "target_hash_field": hash_field,
            "ingredient_target_fields": sorted(name for name in parent_objects[object_type] if name != hash_field),
            "algorithm": "sha256",
            "canonicalization": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan",
        }
    elif op == "project_contract":
        params["project_contract_params"] = {
            "contract": contract,
            "source_owner_type": owner,
            "source_field_path": f"{owner}.{field}",
            "result_type": target["type"],
            "result_cardinality": target["cardinality"],
            "projection_mode": "closed_nested_contract_projection",
        }
    else:
        raise RuntimeError("TPA_AUTHORITY_OP_INVALID")
    return params


def build_recipes(external_root: dict[str, Any]) -> dict[str, Any]:
    leaves = all_parent_leaves()
    direct = direct_sets()
    derived = derived_sets(leaves, direct)
    if len(direct["subject-temporal-public-v1"]) != 28 or len(direct["aemh-match-history-public-v1"]) != 25:
        raise RuntimeError("direct classification count drift")
    if len(derived["subject-temporal-public-v1"]) != 18 or len(derived["aemh-match-history-public-v1"]) != 28:
        raise RuntimeError("derived classification count drift")

    def inp(name: str, value_type: str) -> dict[str, Any]:
        return ir_ref("input", name, value_type)

    def node(name: str, value_type: str) -> dict[str, Any]:
        return ir_ref("node", name, value_type)

    manifest_root_ref = ir_ref("manifest", "external_acceptance_registry_root", "external_registry_root")
    recipes = [
        recipe_ir(
            "recipe.external_registry_receipt_resolution",
            [
                ir_input("candidate_bundle", "external_candidate_bundle"),
                ir_input("external_registry_root", "external_registry_root", source_kind="manifest_pin"),
            ],
            [ir_transform("accepted_record_ref", "resolve_external_record", [inp("candidate_bundle", "external_candidate_bundle"), manifest_root_ref], "string")],
            [
                ir_condition("candidate_chain", "candidate_chain_valid", [inp("candidate_bundle", "external_candidate_bundle")], "TPA_CANDIDATE_CHAIN_HASH_MISMATCH"),
                ir_condition("external_registry_pin", "external_registry_match", [inp("candidate_bundle", "external_candidate_bundle"), manifest_root_ref], "TPA_EXTERNAL_REGISTRY_PIN_MISMATCH"),
                ir_condition("accepted_record", "accepted_record_match", [inp("candidate_bundle", "external_candidate_bundle"), manifest_root_ref], "TPA_ACCEPTED_RECORD_MISMATCH"),
            ],
            [ir_output("accepted_record_ref", node("accepted_record_ref", "string"), "string")],
        ),
        recipe_ir(
            "recipe.cutoff_exact_present_absent",
            [ir_input("cutoff_state", "string"), ir_input("cutoff_date", "date"), ir_input("binding_refs", "string_list"), ir_input("scope_refs", "string_list"), ir_input("accepted_scope_refs", "string_list")],
            [ir_transform("cutoff_output", "identity", [inp("cutoff_date", "date")], "date")],
            [
                ir_condition("cutoff_cardinality", "exact_count", [inp("binding_refs", "string_list")], "TPA_CUTOFF_ZERO_OR_MULTIPLE", ir_params(expected_integer=1)),
                ir_condition("cutoff_scope", "list_equal", [inp("scope_refs", "string_list"), inp("accepted_scope_refs", "string_list")], "TPA_SCOPE_DRIFT"),
                ir_condition("cutoff_state", "cutoff_state_compatible", [inp("cutoff_state", "string"), inp("cutoff_date", "date")], "TPA_CUTOFF_STATE_MISMATCH"),
            ],
            [ir_output("cutoff_date", node("cutoff_output", "date"), "date")],
        ),
        recipe_ir(
            "recipe.visibility_universe_and_stable_bridge",
            [ir_input("evaluation_members", "string_list"), ir_input("projectable_members", "string_list"), ir_input("hidden_members", "string_list"), ir_input("bridge_members", "string_list"), ir_input("declared_count", "integer"), ir_input("declared_hash", "sha256")],
            [ir_transform("evaluation_count", "count", [inp("evaluation_members", "string_list")], "integer")],
            [
                ir_condition("partition", "set_partition", [inp("evaluation_members", "string_list"), inp("projectable_members", "string_list"), inp("hidden_members", "string_list")], "TPA_VISIBILITY_PARTITION_MISMATCH"),
                ir_condition("overlap", "disjoint", [inp("projectable_members", "string_list"), inp("hidden_members", "string_list")], "TPA_VISIBILITY_SET_OVERLAP"),
                ir_condition("bridge", "list_equal", [inp("evaluation_members", "string_list"), inp("bridge_members", "string_list")], "TPA_VISIBILITY_BRIDGE_INCOMPLETE"),
                ir_condition("count", "equal", [node("evaluation_count", "integer"), inp("declared_count", "integer")], "TPA_VISIBILITY_COUNT_MISMATCH"),
                ir_condition("hash", "sha256_join_matches", [inp("evaluation_members", "string_list"), inp("declared_hash", "sha256")], "TPA_VISIBILITY_HASH_MISMATCH", ir_params(separator="\u0000")),
            ],
            [ir_output("evaluation_count", node("evaluation_count", "integer"), "integer")],
            cardinality="total_partition",
            ordering="sorted_unique",
            hash_mode="explicit_sha256_join_nodes",
        ),
        recipe_ir(
            "recipe.locator_total_consumption_revision_partition",
            [ir_input("locator_refs", "string_list"), ir_input("consumed_refs", "string_list"), ir_input("record_bindings", "string_list"), ir_input("accepted_record_bindings", "string_list"), ir_input("revision_assignments", "string_list")],
            [ir_transform("locator_count", "count", [inp("locator_refs", "string_list")], "integer")],
            [
                ir_condition("consumption", "list_equal", [inp("locator_refs", "string_list"), inp("consumed_refs", "string_list")], "TPA_LOCATOR_UNUSED"),
                ir_condition("binding", "list_equal", [inp("record_bindings", "string_list"), inp("accepted_record_bindings", "string_list")], "TPA_LOCATOR_BINDING_MISMATCH"),
                ir_condition("revision_partition", "locator_partition", [inp("locator_refs", "string_list"), inp("revision_assignments", "string_list")], "TPA_REVISION_PARTITION_INCOMPLETE"),
            ],
            [ir_output("locator_count", node("locator_count", "integer"), "integer")],
            cardinality="total_partition",
            ordering="sorted_unique",
        ),
        recipe_ir(
            "recipe.temporal_axis_timezone_day_zero",
            [ir_input("timezone", "string"), ir_input("anchor_date", "date"), ir_input("event_date", "date"), ir_input("day_zero_convention", "string"), ir_input("anchor_refs", "string_list")],
            [ir_transform("study_day", "study_day", [inp("anchor_date", "date"), inp("event_date", "date"), inp("day_zero_convention", "string")], "integer")],
            [
                ir_condition("timezone", "equal", [inp("timezone", "string")], "TPA_TIMEZONE_MISMATCH", ir_params(expected_string="Asia/Shanghai")),
                ir_condition("anchor", "exact_count", [inp("anchor_refs", "string_list")], "TPA_STUDY_DAY_WITHOUT_EXACT_ANCHOR", ir_params(expected_integer=1)),
                ir_condition("day_zero", "member_of", [inp("day_zero_convention", "string")], "TPA_DAY_ZERO_MISMATCH", ir_params(allowed_strings=["anchor_is_day_one", "anchor_is_day_zero"])),
            ],
            [ir_output("study_day", node("study_day", "integer"), "integer")],
        ),
        recipe_ir(
            "recipe.endpoint_state_range_main_axis",
            [ir_input("date_state", "string"), ir_input("geometry", "string"), ir_input("exact_date", "date"), ir_input("candidate_dates", "date_list"), ir_input("declared_candidate_count", "integer"), ir_input("main_axis_mode", "string")],
            [ir_transform("date_range", "range_envelope", [inp("candidate_dates", "date_list")], "date_list")],
            [
                ir_condition("state_geometry", "endpoint_state_geometry_compatible", [inp("date_state", "string"), inp("geometry", "string"), inp("exact_date", "date"), inp("candidate_dates", "date_list"), inp("main_axis_mode", "string")], "TPA_ENDPOINT_STATE_INVALID"),
                ir_condition("range", "date_ordered", [inp("candidate_dates", "date_list")], "TPA_RANGE_INVALID"),
                ir_condition("count", "equal", [inp("declared_candidate_count", "integer")], "TPA_ENDPOINT_COUNT_MISMATCH", ir_params(expected_integer=2)),
            ],
            [ir_output("date_range", node("date_range", "date_list"), "date_list")],
        ),
        recipe_ir(
            "recipe.visit_assignment_actual_bundle_encounter",
            [ir_input("assignment_refs", "string_list"), ir_input("visit_kind", "string"), ir_input("planned_visit_ref", "string"), ir_input("actual_encounter_ref", "string"), ir_input("nominal_ref", "string"), ir_input("actual_ref", "string")],
            [ir_transform("encounter", "identity", [inp("actual_encounter_ref", "string")], "string")],
            [
                ir_condition("assignment", "exact_count", [inp("assignment_refs", "string_list")], "TPA_VISIT_JOIN_ZERO_OR_MULTIPLE", ir_params(expected_integer=1)),
                ir_condition("unscheduled", "unscheduled_binding_valid", [inp("visit_kind", "string"), inp("planned_visit_ref", "string"), inp("actual_encounter_ref", "string")], "TPA_UNSCHEDULED_SNAPPED"),
                ir_condition("nominal_actual", "disjoint", [inp("nominal_ref", "string"), inp("actual_ref", "string")], "TPA_NOMINAL_ACTUAL_SUBSTITUTION"),
            ],
            [ir_output("actual_encounter_ref", node("encounter", "string"), "string")],
        ),
        recipe_ir(
            "recipe.event_exact_activity_binding",
            [ir_input("activity_match_refs", "string_list"), ir_input("semantic_authority_refs", "string_list"), ir_input("activity_ref", "string")],
            [ir_transform("activity", "identity", [inp("activity_ref", "string")], "string")],
            [
                ir_condition("activity_join", "exact_count", [inp("activity_match_refs", "string_list")], "TPA_EVENT_BINDING_MISMATCH", ir_params(expected_integer=1)),
                ir_condition("semantic_join", "exact_count", [inp("semantic_authority_refs", "string_list")], "TPA_EVENT_SEMANTIC_UNRESOLVED", ir_params(expected_integer=1)),
            ],
            [ir_output("activity_ref", node("activity", "string"), "string")],
        ),
        recipe_ir(
            "recipe.phase_binding_accepted_zh_lexicon",
            [ir_input("phase_code", "string"), ir_input("phase_codes", "string_list"), ir_input("phase_labels", "string_list"), ir_input("anchor_refs", "string_list")],
            [ir_transform("phase_label", "lookup_parallel", [inp("phase_codes", "string_list"), inp("phase_labels", "string_list"), inp("phase_code", "string")], "string")],
            [
                ir_condition("phase_code", "member_of", [inp("phase_code", "string"), inp("phase_codes", "string_list")], "TPA_PHASE_LABEL_UNACCEPTED"),
                ir_condition("lexicon_shape", "same_length", [inp("phase_codes", "string_list"), inp("phase_labels", "string_list")], "TPA_PHASE_LABEL_UNACCEPTED"),
                ir_condition("anchor", "exact_count", [inp("anchor_refs", "string_list")], "TPA_PHASE_BINDING_MISMATCH", ir_params(expected_integer=1)),
            ],
            [ir_output("phase_label", node("phase_label", "string"), "string")],
        ),
        recipe_ir(
            "recipe.risk_s4_eight_identity_endpoint_binding",
            [ir_input("join_left", "string_list"), ir_input("join_right", "string_list"), ir_input("risk_match_refs", "string_list"), ir_input("risk_ref", "string")],
            [ir_transform("risk", "identity", [inp("risk_ref", "string")], "string")],
            [
                ir_condition("eight_fields", "exact_eight_join", [inp("join_left", "string_list")], "TPA_S4_JOIN_NOT_EXACT_EIGHT"),
                ir_condition("scope_join", "list_equal", [inp("join_left", "string_list"), inp("join_right", "string_list")], "TPA_JOIN_CROSS_SCOPE"),
                ir_condition("risk_join", "exact_count", [inp("risk_match_refs", "string_list")], "TPA_RISK_JOIN_ZERO_OR_MULTIPLE", ir_params(expected_integer=1)),
            ],
            [ir_output("risk_ref", node("risk", "string"), "string")],
        ),
        recipe_ir(
            "recipe.domain_applicable_or_controlled_empty",
            [ir_input("member_refs", "string_list"), ir_input("declared_state", "string"), ir_input("domain_codes", "string_list"), ir_input("empty_authority_refs", "string_list")],
            [ir_transform("applicability", "if_empty_label", [inp("member_refs", "string_list")], "string", ir_params(expected_string="not_applicable", occurrence_value="applicable"))],
            [
                ir_condition("domain_set", "list_equal", [inp("domain_codes", "string_list")], "TPA_DOMAIN_SET_NOT_EIGHT", ir_params(allowed_strings=sorted(DOMAINS))),
                ir_condition("state", "domain_state_compatible", [inp("member_refs", "string_list"), inp("declared_state", "string"), inp("empty_authority_refs", "string_list")], "TPA_DOMAIN_APPLICABILITY_MISMATCH"),
            ],
            [ir_output("applicability_state", node("applicability", "string"), "string")],
            cardinality="exact_set",
            ordering="sorted_unique",
        ),
        recipe_ir(
            "recipe.pending_union_from_unprojectable_targets",
            [ir_input("missing_target_refs", "string_list"), ir_input("unprojectable_target_refs", "string_list"), ir_input("declared_pending_refs", "string_list"), ir_input("member_kind_pairs", "string_list")],
            [ir_transform("pending_refs", "set_union", [inp("missing_target_refs", "string_list"), inp("unprojectable_target_refs", "string_list")], "string_list")],
            [
                ir_condition("pending_exact", "list_equal", [node("pending_refs", "string_list"), inp("declared_pending_refs", "string_list")], "TPA_PENDING_ADD_DROP"),
                ir_condition("pending_kind", "all_items_equal", [inp("member_kind_pairs", "string_list")], "TPA_PENDING_KIND_MISMATCH", ir_params(expected_string="event|event")),
            ],
            [ir_output("pending_refs", node("pending_refs", "string_list"), "string_list")],
            ordering="sorted_unique",
        ),
        recipe_ir(
            "recipe.aemh_append_only_decision_registry",
            [ir_input("event_kinds", "string_list"), ir_input("sequence_numbers", "integer_list"), ir_input("prior_head_hash", "sha256"), ir_input("candidate_fact_roles", "string_list")],
            [ir_transform("decision_head_hash", "sha256_join", [inp("prior_head_hash", "sha256"), inp("event_kinds", "string_list"), inp("sequence_numbers", "integer_list")], "sha256", ir_params(separator="\u0000"))],
            [
                ir_condition("one_reminder", "occurrence_at_most", [inp("event_kinds", "string_list")], "TPA_AEMH_SECOND_REMINDER", ir_params(expected_integer=1, occurrence_value="reminder_created")),
                ir_condition("transition", "allowed_transition", [inp("event_kinds", "string_list")], "TPA_AEMH_INVALID_TRANSITION"),
                ir_condition("sequence", "contiguous_integers", [inp("sequence_numbers", "integer_list")], "TPA_AEMH_SEQUENCE_GAP"),
                ir_condition("roles", "roles_exact", [inp("candidate_fact_roles", "string_list")], "TPA_AEMH_CANDIDATE_FACT_SWAP"),
            ],
            [ir_output("decision_head_hash", node("decision_head_hash", "sha256"), "sha256")],
            hash_mode="explicit_sha256_join_nodes",
        ),
        recipe_ir(
            "recipe.aemh_joint_evidence_binding",
            [ir_input("entity_role", "string"), ir_input("entity_ref", "string"), ir_input("entity_content_hash", "sha256"), ir_input("locator_ref", "string"), ir_input("locator_content_hash", "sha256"), ir_input("raw_payload_hash", "sha256"), ir_input("revision_ref", "string"), ir_input("revision_content_hash", "sha256"), ir_input("declared_binding_hash", "sha256")],
            [ir_transform("binding_hash", "sha256_join", [inp("entity_role", "string"), inp("entity_ref", "string"), inp("entity_content_hash", "sha256"), inp("locator_ref", "string"), inp("locator_content_hash", "sha256"), inp("raw_payload_hash", "sha256"), inp("revision_ref", "string"), inp("revision_content_hash", "sha256")], "sha256", ir_params(separator="\u0000"))],
            [
                ir_condition("role", "member_of", [inp("entity_role", "string")], "TPA_AEMH_EVIDENCE_ROLE_MISMATCH", ir_params(allowed_strings=["candidate", "considered_fact", "later_fact"])),
                ir_condition("joint_hash", "equal", [node("binding_hash", "sha256"), inp("declared_binding_hash", "sha256")], "TPA_AEMH_EVIDENCE_JOINT_MISMATCH"),
            ],
            [ir_output("binding_hash", node("binding_hash", "sha256"), "sha256")],
            hash_mode="explicit_sha256_join_nodes",
        ),
        recipe_ir(
            "recipe.aemh_thread_membership",
            [ir_input("candidate_refs", "string_list"), ir_input("later_fact_refs", "string_list"), ir_input("declared_member_refs", "string_list"), ir_input("scope_refs", "string_list"), ir_input("member_scope_refs", "string_list")],
            [ir_transform("member_refs", "set_union", [inp("candidate_refs", "string_list"), inp("later_fact_refs", "string_list")], "string_list")],
            [
                ir_condition("membership", "list_equal", [node("member_refs", "string_list"), inp("declared_member_refs", "string_list")], "TPA_AEMH_THREAD_MEMBERSHIP_MISMATCH"),
                ir_condition("scope", "list_equal", [inp("scope_refs", "string_list"), inp("member_scope_refs", "string_list")], "TPA_AEMH_THREAD_CROSS_SCOPE"),
            ],
            [ir_output("member_refs", node("member_refs", "string_list"), "string_list")],
            ordering="sorted_unique",
        ),
        recipe_ir(
            "recipe.aemh_prefix_transition_closure",
            [ir_input("prior_entries", "string_list"), ir_input("current_entries", "string_list"), ir_input("accepted_snapshot_ref", "string"), ir_input("current_snapshot_ref", "string"), ir_input("lifecycle_effects", "string_list")],
            [ir_transform("suffix", "prefix_suffix", [inp("prior_entries", "string_list"), inp("current_entries", "string_list")], "string_list")],
            [
                ir_condition("prefix", "prefix", [inp("prior_entries", "string_list"), inp("current_entries", "string_list")], "TPA_AEMH_PREFIX_REWRITE"),
                ir_condition("snapshot", "equal", [inp("accepted_snapshot_ref", "string"), inp("current_snapshot_ref", "string")], "TPA_AEMH_FOREIGN_SNAPSHOT"),
                ir_condition("lifecycle", "all_items_equal", [inp("lifecycle_effects", "string_list")], "TPA_AEMH_LIFECYCLE_EFFECT", ir_params(expected_string="none")),
            ],
            [ir_output("suffix", node("suffix", "string_list"), "string_list")],
        ),
        recipe_ir(
            "recipe.upstream_roots_before_hashes_containers_packets",
            [ir_input("root_hashes", "sha256_list"), ir_input("declared_packet_hash", "sha256"), ir_input("external_registry_hash", "sha256"), ir_input("declared_receipt_hash", "sha256")],
            [
                ir_transform("packet_hash", "sha256_join", [inp("root_hashes", "sha256_list")], "sha256", ir_params(separator="\u0000")),
                ir_transform("receipt_hash", "sha256_join", [node("packet_hash", "sha256"), inp("external_registry_hash", "sha256")], "sha256", ir_params(separator="\u0000")),
            ],
            [
                ir_condition("packet", "equal", [node("packet_hash", "sha256"), inp("declared_packet_hash", "sha256")], "TPA_PACKET_HASH_MISMATCH"),
                ir_condition("receipt", "equal", [node("receipt_hash", "sha256"), inp("declared_receipt_hash", "sha256")], "TPA_RECEIPT_HASH_MISMATCH"),
            ],
            [ir_output("packet_hash", node("packet_hash", "sha256"), "sha256"), ir_output("receipt_hash", node("receipt_hash", "sha256"), "sha256")],
            hash_mode="explicit_sha256_join_nodes",
        ),
        recipe_ir(
            "recipe.parent_semantic_snapshot_immutability",
            [
                ir_input("expected_pins", "sha256_list"),
                ir_input("actual_pins", "sha256_list"),
                ir_input("forbidden_sources", "string_list"),
            ],
            [ir_transform("pins_match", "all_equal", [inp("expected_pins", "sha256_list"), inp("actual_pins", "sha256_list")], "boolean")],
            [
                ir_condition("pins", "list_equal", [inp("expected_pins", "sha256_list"), inp("actual_pins", "sha256_list")], "TPA_PROTECTED_PIN_DRIFT"),
                ir_condition("forbidden", "empty", [inp("forbidden_sources", "string_list")], "TPA_FORBIDDEN_AUTHORITY_SOURCE"),
            ],
            [ir_output("pins_match", node("pins_match", "boolean"), "boolean")],
        ),
    ]

    ledger: list[dict[str, Any]] = []
    authority_leaf_outputs: list[dict[str, Any]] = []
    for contract in ("subject-temporal-public-v1", "aemh-match-history-public-v1"):
        for leaf in leaves[contract]:
            qualified_leaf = f"{contract}::{leaf}"
            if leaf in direct[contract]:
                before = "A_direct"
                closure_kind, closure_ref = "accepted_authority_leaf", "accepted_parent_manifest"
                post = "constructible_preserved_direct"
            elif leaf in derived[contract]:
                before = "B_deterministic_derived"
                closure_kind, closure_ref = "accepted_authority_leaf", "accepted_parent_manifest"
                post = "constructible_preserved_derived"
            elif contract == "subject-temporal-public-v1" and leaf in SUBJECT_C:
                before = "C_accepted_semantic"
                closure_kind, closure_ref = "accepted_authority_leaf", "accepted_semantic_delta_manifest"
                post = "constructible_preserved_semantic"
            else:
                before = "D_unconstructible"
                closure_kind, closure_ref = closure_for(contract, leaf)
                post = "constructible_from_new_authority" if closure_kind == "authority_root" else "constructible_by_exact_recipe"
            if closure_kind == "recipe":
                target_output_path = f"{closure_ref}::outputs::{qualified_leaf}"
                dependency_chain = [f"recipe:{closure_ref}", f"output:{qualified_leaf}"]
            else:
                target_output_path = f"{closure_ref}::outputs::{qualified_leaf}"
                dependency_chain = [f"authority:{closure_ref}", f"output:{qualified_leaf}"]
                if closure_kind == "authority_root":
                    authority_leaf_outputs.append(
                        {
                            "qualified_leaf": qualified_leaf,
                            "authority_root": closure_ref,
                            "output_path": target_output_path,
                            "dependency_refs": dependency_chain,
                        }
                    )
            ledger.append(
                {
                    "contract": contract,
                    "leaf": leaf,
                    "before_status": before,
                    "before_basis": {
                        "A_direct": "exact accepted typed leaf with no value inference",
                        "B_deterministic_derived": "closed constant or canonical derivation over accepted leaves",
                        "C_accepted_semantic": "accepted semantic delta exact authority",
                        "D_unconstructible": "fresh audit found no honest authority root or closed recipe",
                    }[before],
                    "post_delta_status": post,
                    "closure_kind": closure_kind,
                    "closure_ref": closure_ref,
                    "target_output_path": target_output_path,
                    "dependency_chain": dependency_chain,
                    "nominal_mapping": False,
                    "unexplained": False,
                }
            )

    recipe_map = {recipe["recipe_id"]: recipe for recipe in recipes}
    for row in ledger:
        if row["closure_kind"] != "recipe":
            continue
        recipe = recipe_map[row["closure_ref"]]
        primary = recipe["outputs"][0]
        source_ref = copy.deepcopy(primary["source_ref"])
        if row["closure_ref"] == "recipe.upstream_roots_before_hashes_containers_packets":
            node_id = "receipt_hash" if row["leaf"].endswith("receipt_content_hash") else "packet_hash"
            source_ref = ir_ref("node", node_id, "sha256")
        recipe["outputs"].append(
            ir_output(
                f"leaf::{row['contract']}::{row['leaf']}",
                source_ref,
                source_ref["value_type"],
                target_leaf=f"{row['contract']}::{row['leaf']}",
                dependency_refs=row["dependency_chain"],
                fixture_asserted=False,
            )
        )
    recipes = [sealed({key: value for key, value in recipe.items() if key != "recipe_content_hash"}, "recipe_content_hash") for recipe in recipes]

    parent_objects: dict[str, Any] = {}
    for parent_path in (SUBJECT_SCHEMA, AEMH_SCHEMA):
        parent_objects.update(read_json(parent_path)["objects"])
    authority_schema = build_schema()
    authority_fixture_roots = sorted({declaration["authority_root"] for declaration in authority_leaf_outputs})
    authority_fixture_catalog = build_authority_fixtures(authority_schema, authority_fixture_roots)
    authority_fixture_map = {fixture["fixture_id"]: fixture for fixture in authority_fixture_catalog}
    recipe_authority_bindings = []
    for recipe_id in sorted(RECIPE_AUTHORITY_REFS):
        requirements = []
        for position, fixture_ref in enumerate(RECIPE_AUTHORITY_REFS[recipe_id], 1):
            fixture = authority_fixture_map[fixture_ref]
            requirements.append(
                {
                    "fixture_ref": fixture_ref,
                    "object_type": fixture["object_type"],
                    "role": f"{recipe_id.rsplit('.', 1)[1]}:{position}",
                    "fixture_content_hash": fixture["fixture_content_hash"],
                    "scope_join_keys": list(IDENTITY_FIELDS),
                }
            )
        recipe_authority_bindings.append(sealed({"recipe_id": recipe_id, "requirements": requirements}, "binding_content_hash"))
    recipe_authority_binding_registry = sealed(
        {"binding_count": len(recipe_authority_bindings), "bindings": recipe_authority_bindings},
        "registry_content_hash",
    )
    if recipe_authority_binding_registry["registry_content_hash"] != EXPECTED_RECIPE_AUTHORITY_BINDING_REGISTRY_CONTENT_HASH:
        raise RuntimeError("accepted recipe authority binding registry drift")
    canonical_target_hash_fields = {
        "TemporalAxisBasis.axis_content_hash", "TemporalDateEndpoint.endpoint_content_hash", "TemporalDomainTrack.track_content_hash",
        "TemporalEvent.event_content_hash", "TemporalMembershipIndex.membership_content_hash", "TemporalPhaseBand.phase_content_hash",
        "TemporalRiskAnchor.risk_anchor_content_hash", "TemporalVisit.visit_content_hash", "AEMHMatchHistoryEntry.entry_hash",
        "AEMHMatchThread.thread_content_hash", "AEMHThreadPrefixAnchor.prefix_content_hash",
    }
    executable_authority_outputs: list[dict[str, Any]] = []
    for declaration in authority_leaf_outputs:
        contract, leaf = declaration["qualified_leaf"].split("::", 1)
        owner, field = leaf.split(".", 1)
        target = parent_objects[owner][field]
        direct_source = LazyAuthorityProjectionExecutor.direct_source(contract, owner, field)
        if owner == "PublicAuthorityReceipt" and field == "public_projection_id":
            op = "derive_value"
        elif direct_source is not None:
            op = "direct_field"
        elif leaf in canonical_target_hash_fields or (owner == "PublicAuthorityReceipt" and field == "public_projection_content_hash"):
            op = "canonical_hash"
        elif owner.endswith(("AuthorityPacket", "PublicProjection")):
            op = "project_contract"
        elif target["cardinality"] == "many" and target["type"] in parent_objects:
            op = "assemble_sorted_records"
        elif target["type"] in parent_objects:
            op = "project_record"
        else:
            op = "derive_value"
        op_params = authority_op_params(contract, owner, field, op, target, parent_objects)
        selected_params = op_params[f"{op}_params"]
        projector = LazyAuthorityProjectionExecutor(authority_fixture_catalog)
        _output, execution_trace = projector.execute(contract, owner, field, op, selected_params)
        executable_authority_outputs.append(
            sealed(
                declaration
                | {
                    "mapping_id": f"authority.mapping.{len(executable_authority_outputs) + 1:03d}",
                    "source_fixture_refs": execution_trace["consumed_fixture_refs"],
                    "source_fixture_content_hash_pins": execution_trace["verified_fixture_pins"],
                    "source_field_paths": execution_trace["consumed_field_paths"],
                    "op": op,
                    **op_params,
                    "scope_join_keys": list(IDENTITY_FIELDS),
                    "output_type": target["type"],
                    "output_cardinality": target["cardinality"],
                    "output_nullable": target["nullable"],
                    "canonicalization_profile": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan",
                    "content_hash_recipe": "sha256_over_canonical_projection_excluding_only_own_hash_field",
                },
                "mapping_content_hash",
            )
        )
    authority_output_registry_payload = {
        "mapping_count": len(executable_authority_outputs),
        "mappings": executable_authority_outputs,
    }
    authority_output_registry = sealed(authority_output_registry_payload, "registry_content_hash")
    if EXPECTED_AUTHORITY_OUTPUT_REGISTRY_CONTENT_HASH is not None and authority_output_registry["registry_content_hash"] != EXPECTED_AUTHORITY_OUTPUT_REGISTRY_CONTENT_HASH:
        raise RuntimeError("accepted authority output registry drift")
    dependency_counts = sorted(len(mapping["source_fixture_refs"]) + len(mapping["source_field_paths"]) for mapping in executable_authority_outputs)
    middle = len(dependency_counts) // 2
    median_dependency_count = dependency_counts[middle]
    unique_dependency_slice_count = len({(tuple(mapping["source_fixture_refs"]), tuple(mapping["source_field_paths"])) for mapping in executable_authority_outputs})
    authority_op_counts = {
        op: sum(1 for mapping in executable_authority_outputs if mapping["op"] == op)
        for op in ("direct_field", "derive_value", "project_record", "assemble_sorted_records", "canonical_hash", "project_contract")
    }

    before_counts: dict[str, int] = {}
    post_counts: dict[str, int] = {}
    per_contract: dict[str, dict[str, int]] = {}
    for row in ledger:
        before_counts[row["before_status"]] = before_counts.get(row["before_status"], 0) + 1
        post_counts[row["post_delta_status"]] = post_counts.get(row["post_delta_status"], 0) + 1
        contract_counts = per_contract.setdefault(row["contract"], {})
        contract_counts[row["before_status"]] = contract_counts.get(row["before_status"], 0) + 1
    expected = {
        "A_direct": 53,
        "B_deterministic_derived": 46,
        "C_accepted_semantic": 4,
        "D_unconstructible": 169,
    }
    if before_counts != expected:
        raise RuntimeError(f"coverage classification mismatch: {before_counts}")
    expected_contract = {
        "subject-temporal-public-v1": {"A_direct": 28, "B_deterministic_derived": 18, "C_accepted_semantic": 4, "D_unconstructible": 106},
        "aemh-match-history-public-v1": {"A_direct": 25, "B_deterministic_derived": 28, "D_unconstructible": 63},
    }
    if per_contract != expected_contract:
        raise RuntimeError(f"per-contract classification mismatch: {per_contract}")

    controlled_policies = build_controlled_policies()
    policy_hashes = {name: digest(value) for name, value in controlled_policies.items()}
    accepted_record = external_root["accepted_records"][0]
    external_reference = {
        "manifest_path": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json",
        "section_pointer": "/external_acceptance_registry_root",
        "registry_id": external_root["registry_id"],
        "registry_root_content_hash": external_root["root_content_hash"],
        "accepted_record_ref": accepted_record["accepted_record_ref"],
        "accepted_record_content_hash": accepted_record["record_content_hash"],
        "section_canonical_sha256": EXPECTED_EXTERNAL_REGISTRY_SECTION_CANONICAL_SHA256,
    }

    return {
        "schema": "medical-monitoring-r5-s5-temporal-projection-authority-recipe-registry-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "authority_scope": AUTHORITY_SCOPE,
        "non_clinical": True,
        "external_registry_reference": external_reference,
        "controlled_policies": controlled_policies,
        "controlled_policy_content_hashes": policy_hashes,
        "recipes": recipes,
        "recipe_count": len(recipes),
        "recipe_content_hashes": {recipe["recipe_id"]: recipe["recipe_content_hash"] for recipe in recipes},
        "coverage_ledger": ledger,
        "authority_leaf_outputs": executable_authority_outputs,
        "authority_output_registry": authority_output_registry,
        "authority_output_registry_content_hash": authority_output_registry["registry_content_hash"],
        "authority_mapping_count": len(executable_authority_outputs),
        "executable_authority_mapping_count": len(executable_authority_outputs),
        "authority_leaf_without_emitter_count": 0,
        "recipe_authority_binding_registry": recipe_authority_binding_registry,
        "recipe_authority_binding_registry_content_hash": recipe_authority_binding_registry["registry_content_hash"],
        "unique_dependency_slice_count": unique_dependency_slice_count,
        "min_dependency_count": dependency_counts[0],
        "max_dependency_count": dependency_counts[-1],
        "median_dependency_count": median_dependency_count,
        "mappings_with_all_19_count": sum(1 for mapping in executable_authority_outputs if len(mapping["source_fixture_refs"]) == 19),
        "unused_declared_dependency_count": 0,
        "authority_op_counts": authority_op_counts,
        "op_branch_positive_coverage": {op: count > 0 for op, count in authority_op_counts.items()},
        "exact_leaf_output_bijection_count": len(ledger),
        "nominal_mapping_count": sum(1 for row in ledger if row["nominal_mapping"]),
        "coverage_counts_before": before_counts,
        "coverage_counts_before_by_contract": per_contract,
        "coverage_counts_after": post_counts,
        "total_leaf_count": len(ledger),
        "former_d_leaf_count": sum(1 for row in ledger if row["before_status"] == "D_unconstructible"),
        "unexplained_leaf_count": sum(1 for row in ledger if row["unexplained"]),
        "construction_order": [
            "manifest-pinned external acceptance registry resolution",
            "scope cutoff visibility locator and stable identity roots",
            "member endpoint axis visit event phase risk and domain roots",
            "AE/MH decision evidence and thread roots",
            "membership and pending unions",
            "inner content hashes",
            "projection ids and hashes",
            "external receipts",
            "packets",
        ],
    }


def positive_fixture(
    fixture_id: str,
    recipe_id: str,
    inputs: list[dict[str, Any]],
    expected_outputs: list[dict[str, Any]],
    authority_fixture_refs: list[str] | None = None,
    dependency_edges: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return sealed(
        {
            "fixture_id": fixture_id,
            "recipe_id": recipe_id,
            "authority_fixture_refs": list(authority_fixture_refs or []),
            "inputs": inputs,
            "expected_outputs": expected_outputs,
            "dependency_edges": dependency_edges or [],
        },
        "fixture_content_hash",
    )


def build_positive_fixtures(external_root: dict[str, Any]) -> list[dict[str, Any]]:
    dag_receipt_hash = EXPECTED_DAG_RECEIPT_HASH or "0" * 64
    roots = ["1" * 64, "2" * 64, "3" * 64]
    domain_codes = sorted(DOMAINS)
    fixtures = [
        positive_fixture(
            "fixture.recipe.01.external",
            "recipe.external_registry_receipt_resolution",
            [typed_value("candidate_bundle", "external_candidate_bundle", "candidate:valid")],
            [typed_value("accepted_record_ref", "string", "synthetic-accepted:temporal-projection-authority:20260820")],
            ["authority:TemporalAuthorityScopeIdentity", "authority:TemporalProjectionAcceptanceReceipt", "authority:TemporalProjectionAuthorityRegistry"],
        ),
        positive_fixture(
            "fixture.recipe.02.cutoff",
            "recipe.cutoff_exact_present_absent",
            [typed_value("cutoff_state", "string", "present"), typed_value("cutoff_date", "date", "2026-01-12"), typed_value("binding_refs", "string_list", ["cutoff-binding:1"]), typed_value("scope_refs", "string_list", ["project:p1", "run:r1", "site:s1", "subject:u1"]), typed_value("accepted_scope_refs", "string_list", ["project:p1", "run:r1", "site:s1", "subject:u1"])],
            [typed_value("cutoff_date", "date", "2026-01-12")],
            ["authority:CutoffEndpointBindingAuthority"],
        ),
        positive_fixture(
            "fixture.recipe.03.visibility",
            "recipe.visibility_universe_and_stable_bridge",
            [typed_value("evaluation_members", "string_list", ["member:m1", "member:m2"]), typed_value("projectable_members", "string_list", ["member:m1"]), typed_value("hidden_members", "string_list", ["member:m2"]), typed_value("bridge_members", "string_list", ["member:m1", "member:m2"]), typed_value("declared_count", "integer", 2), typed_value("declared_hash", "sha256", EXPECTED_VISIBILITY_HASH)],
            [typed_value("evaluation_count", "integer", 2)],
            ["authority:PublicScopeUniverseAuthority", "authority:TemporalMemberAuthorityRecord"],
        ),
        positive_fixture(
            "fixture.recipe.04.locator",
            "recipe.locator_total_consumption_revision_partition",
            [typed_value("locator_refs", "string_list", ["locator:l1", "locator:l2"]), typed_value("consumed_refs", "string_list", ["locator:l1", "locator:l2"]), typed_value("record_bindings", "string_list", ["locator:l1|record:r1|field:start|raw:" + "a" * 64, "locator:l2|record:r2|field:end|raw:" + "b" * 64]), typed_value("accepted_record_bindings", "string_list", ["locator:l1|record:r1|field:start|raw:" + "a" * 64, "locator:l2|record:r2|field:end|raw:" + "b" * 64]), typed_value("revision_assignments", "string_list", ["locator:l1=revision:v1", "locator:l2=revision:v2"])],
            [typed_value("locator_count", "integer", 2)],
            ["authority:SourceLocatorRevisionBinding"],
        ),
        positive_fixture(
            "fixture.recipe.05.axis",
            "recipe.temporal_axis_timezone_day_zero",
            [typed_value("timezone", "string", "Asia/Shanghai"), typed_value("anchor_date", "date", "2026-01-10"), typed_value("event_date", "date", "2026-01-12"), typed_value("day_zero_convention", "string", "anchor_is_day_one"), typed_value("anchor_refs", "string_list", ["endpoint:anchor"])],
            [typed_value("study_day", "integer", 3)],
            ["authority:TemporalAxisAuthorityRecord"],
        ),
        positive_fixture(
            "fixture.recipe.06.endpoint",
            "recipe.endpoint_state_range_main_axis",
            [typed_value("date_state", "string", "partial"), typed_value("geometry", "string", "closed_interval"), typed_value("exact_date", "date", "2026-01-10"), typed_value("candidate_dates", "date_list", ["2026-01-10", "2026-01-12"]), typed_value("declared_candidate_count", "integer", 2), typed_value("main_axis_mode", "string", "authorized")],
            [typed_value("date_range", "date_list", ["2026-01-10", "2026-01-12"])],
            ["authority:TemporalEndpointAuthorityRecord"],
        ),
        positive_fixture(
            "fixture.recipe.07.visit",
            "recipe.visit_assignment_actual_bundle_encounter",
            [typed_value("assignment_refs", "string_list", ["assignment:a1"]), typed_value("visit_kind", "string", "nominal"), typed_value("planned_visit_ref", "string", "visit:planned"), typed_value("actual_encounter_ref", "string", "encounter:e1"), typed_value("nominal_ref", "string", "endpoint:nominal"), typed_value("actual_ref", "string", "endpoint:actual")],
            [typed_value("actual_encounter_ref", "string", "encounter:e1")],
            ["authority:VisitProjectionBinding"],
        ),
        positive_fixture(
            "fixture.recipe.08.event",
            "recipe.event_exact_activity_binding",
            [typed_value("activity_match_refs", "string_list", ["activity-match:1"]), typed_value("semantic_authority_refs", "string_list", ["semantic:event:1"]), typed_value("activity_ref", "string", "activity:a1")],
            [typed_value("activity_ref", "string", "activity:a1")],
            ["authority:EventProjectionBinding"],
        ),
        positive_fixture(
            "fixture.recipe.09.phase",
            "recipe.phase_binding_accepted_zh_lexicon",
            [typed_value("phase_code", "string", "treatment"), typed_value("phase_codes", "string_list", ["baseline", "follow_up", "screening", "treatment", "unscheduled"]), typed_value("phase_labels", "string_list", ["基线期", "随访期", "筛选期", "治疗期", "非计划阶段"]), typed_value("anchor_refs", "string_list", ["anchor:phase:1"])],
            [typed_value("phase_label", "string", "治疗期")],
            ["authority:PhaseProjectionBinding"],
        ),
        positive_fixture(
            "fixture.recipe.10.risk",
            "recipe.risk_s4_eight_identity_endpoint_binding",
            [typed_value("join_left", "string_list", [f"identity:{index}" for index in range(1, 9)]), typed_value("join_right", "string_list", [f"identity:{index}" for index in range(1, 9)]), typed_value("risk_match_refs", "string_list", ["risk-match:1"]), typed_value("risk_ref", "string", "risk:r1")],
            [typed_value("risk_ref", "string", "risk:r1")],
            ["authority:RiskProjectionBinding"],
        ),
        positive_fixture(
            "fixture.recipe.11.domain",
            "recipe.domain_applicable_or_controlled_empty",
            [typed_value("member_refs", "string_list", ["event:e1"]), typed_value("declared_state", "string", "applicable"), typed_value("domain_codes", "string_list", domain_codes), typed_value("empty_authority_refs", "string_list", [])],
            [typed_value("applicability_state", "string", "applicable")],
            ["authority:DomainApplicabilityAuthorityRecord"],
        ),
        positive_fixture(
            "fixture.recipe.12.pending",
            "recipe.pending_union_from_unprojectable_targets",
            [typed_value("missing_target_refs", "string_list", ["event:e1"]), typed_value("unprojectable_target_refs", "string_list", ["visit:v1"]), typed_value("declared_pending_refs", "string_list", ["event:e1", "visit:v1"]), typed_value("member_kind_pairs", "string_list", ["event|event"])],
            [typed_value("pending_refs", "string_list", ["event:e1", "visit:v1"])],
        ),
        positive_fixture(
            "fixture.recipe.13.aemh-append",
            "recipe.aemh_append_only_decision_registry",
            [typed_value("event_kinds", "string_list", ["reminder_created", "match_decided"]), typed_value("sequence_numbers", "integer_list", [1, 2]), typed_value("prior_head_hash", "sha256", "a" * 64), typed_value("candidate_fact_roles", "string_list", ["candidate", "later_fact"])],
            [typed_value("decision_head_hash", "sha256", EXPECTED_AEMH_DECISION_HEAD_HASH)],
            ["authority:AEMHAppendDecisionAuthorityRecord", "authority:AEMHDecisionAuthorityRegistry"],
            [{"from_ref": "prior_head_hash", "to_ref": "decision_head_hash"}],
        ),
        positive_fixture(
            "fixture.recipe.14.evidence",
            "recipe.aemh_joint_evidence_binding",
            [typed_value("entity_role", "string", "candidate"), typed_value("entity_ref", "string", "candidate:c1"), typed_value("entity_content_hash", "sha256", "b" * 64), typed_value("locator_ref", "string", "locator:l1"), typed_value("locator_content_hash", "sha256", "c" * 64), typed_value("raw_payload_hash", "sha256", "d" * 64), typed_value("revision_ref", "string", "revision:r1"), typed_value("revision_content_hash", "sha256", "e" * 64), typed_value("declared_binding_hash", "sha256", EXPECTED_EVIDENCE_BINDING_HASH)],
            [typed_value("binding_hash", "sha256", EXPECTED_EVIDENCE_BINDING_HASH)],
            ["authority:AEMHEvidenceBindingAuthority"],
        ),
        positive_fixture(
            "fixture.recipe.15.thread",
            "recipe.aemh_thread_membership",
            [typed_value("candidate_refs", "string_list", ["candidate:c1"]), typed_value("later_fact_refs", "string_list", ["fact:f1"]), typed_value("declared_member_refs", "string_list", ["candidate:c1", "fact:f1"]), typed_value("scope_refs", "string_list", ["project:p1", "site:s1", "subject:u1"]), typed_value("member_scope_refs", "string_list", ["project:p1", "site:s1", "subject:u1"])],
            [typed_value("member_refs", "string_list", ["candidate:c1", "fact:f1"])],
            ["authority:AEMHThreadMembershipAuthority"],
        ),
        positive_fixture(
            "fixture.recipe.16.prefix",
            "recipe.aemh_prefix_transition_closure",
            [typed_value("prior_entries", "string_list", ["h1"]), typed_value("current_entries", "string_list", ["h1", "h2"]), typed_value("accepted_snapshot_ref", "string", "snapshot:s1"), typed_value("current_snapshot_ref", "string", "snapshot:s1"), typed_value("lifecycle_effects", "string_list", ["none", "none"])],
            [typed_value("suffix", "string_list", ["h2"])],
        ),
        positive_fixture(
            "fixture.recipe.17.dag",
            "recipe.upstream_roots_before_hashes_containers_packets",
            [typed_value("root_hashes", "sha256_list", roots), typed_value("declared_packet_hash", "sha256", EXPECTED_DAG_PACKET_HASH), typed_value("external_registry_hash", "sha256", external_root["root_content_hash"]), typed_value("declared_receipt_hash", "sha256", dag_receipt_hash)],
            [typed_value("packet_hash", "sha256", EXPECTED_DAG_PACKET_HASH), typed_value("receipt_hash", "sha256", dag_receipt_hash)],
            ["authority:TemporalMemberAuthorityRecord"],
            [{"from_ref": "root_hashes", "to_ref": "packet_hash"}, {"from_ref": "packet_hash", "to_ref": "receipt_hash"}, {"from_ref": "external_registry_hash", "to_ref": "receipt_hash"}],
        ),
        positive_fixture(
            "fixture.recipe.18.pins",
            "recipe.parent_semantic_snapshot_immutability",
            [typed_value("expected_pins", "sha256_list", ["1" * 64, "2" * 64]), typed_value("actual_pins", "sha256_list", ["1" * 64, "2" * 64]), typed_value("forbidden_sources", "string_list", [])],
            [typed_value("pins_match", "boolean", True)],
        ),
    ]
    if len(fixtures) != 18:
        raise RuntimeError("positive recipe fixture count drift")
    return fixtures


def replacement_fixture(base: dict[str, Any], fixture_id: str, candidate_ref: str, expected_record_ref: str) -> dict[str, Any]:
    replacement = json.loads(json.dumps(base))
    replacement["fixture_id"] = fixture_id
    for value in replacement["inputs"]:
        if value["value_id"] == "candidate_bundle":
            value["object_ref"] = candidate_ref
    replacement["expected_outputs"] = [typed_value("accepted_record_ref", "string", expected_record_ref)]
    return sealed(replacement, "fixture_content_hash")


def challenge_mutation(target_kind: str, target_ref: str, path: str, replacement: dict[str, Any], *, op: str = "replace") -> dict[str, Any]:
    return {"target_kind": target_kind, "target_ref": target_ref, "op": op, "path": path, "replacement": replacement}


def build_active_attack_specs(
    positive_fixtures: list[dict[str, Any]],
    recipes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    external = next(item for item in positive_fixtures if item["fixture_id"] == "fixture.recipe.01.external")
    replacement_fixtures = [
        replacement_fixture(external, "fixture.replacement.external-self-reseal", "candidate:forged-all-resealed", "synthetic-accepted:temporal-projection-authority:20260820"),
        replacement_fixture(external, "fixture.replacement.external-output-reseal", "candidate:forged-all-resealed", "attacker:accepted-record"),
    ]
    axis_recipe_attack = copy.deepcopy(next(item for item in recipes if item["recipe_id"] == "recipe.temporal_axis_timezone_day_zero"))
    axis_recipe_attack["transforms"][0]["op"] = "count"
    axis_recipe_attack = sealed({key: value for key, value in axis_recipe_attack.items() if key != "recipe_content_hash"}, "recipe_content_hash")
    axis_fixture_attack = copy.deepcopy(next(item for item in positive_fixtures if item["fixture_id"] == "fixture.recipe.05.axis"))
    axis_fixture_attack["expected_outputs"] = [typed_value("study_day", "integer", 10)]
    axis_fixture_attack = sealed({key: value for key, value in axis_fixture_attack.items() if key != "fixture_content_hash"}, "fixture_content_hash")
    recipe_attack_bundles = [
        sealed(
            {
                "bundle_id": "recipe-attack:study-day-to-count-and-output-10",
                "recipe_id": axis_recipe_attack["recipe_id"],
                "recipe": axis_recipe_attack,
                "fixture": axis_fixture_attack,
            },
            "bundle_content_hash",
        )
    ]
    specs: list[dict[str, Any]] = []

    def add(
        name: str,
        category: str,
        recipe_id: str,
        fixture_id: str,
        target_kind: str,
        target_ref: str,
        path: str,
        replacement: dict[str, Any],
        error: str,
        *,
        op: str = "replace",
    ) -> None:
        specs.append(
            {
                "name": name,
                "category": category,
                "recipe_id": recipe_id,
                "fixture_id": fixture_id,
                "mutation": challenge_mutation(target_kind, target_ref, path, replacement, op=op),
                "expected_error": error,
            }
        )

    def input_attack(name: str, category: str, fixture: str, recipe_id: str, input_id: str, value_type: str, value: Any, error: str) -> None:
        add(name, category, recipe_id, fixture, "positive_fixture_input", fixture, input_id, typed_value(input_id, value_type, value), error)

    def output_attack(name: str, category: str, fixture: str, recipe_id: str, output_id: str, value_type: str, value: Any, error: str) -> None:
        add(name, category, recipe_id, fixture, "positive_fixture_expected_output", fixture, output_id, typed_value(output_id, value_type, value), error)

    external_recipe = "recipe.external_registry_receipt_resolution"
    external_fixture = "fixture.recipe.01.external"
    add("registry_chain_self_reseal", "external_acceptance", external_recipe, external_fixture, "positive_fixture", external_fixture, "/", typed_value("fixture_ref", "string", "fixture.replacement.external-self-reseal"), "TPA_EXTERNAL_REGISTRY_PIN_MISMATCH")
    add("output_target_plus_candidate_reseal", "external_acceptance", external_recipe, external_fixture, "positive_fixture", external_fixture, "/", typed_value("fixture_ref", "string", "fixture.replacement.external-output-reseal"), "TPA_EXTERNAL_REGISTRY_PIN_MISMATCH")
    input_attack("accepted_record_reseal", "external_acceptance", external_fixture, external_recipe, "candidate_bundle", "external_candidate_bundle", "candidate:wrong-record-resealed", "TPA_ACCEPTED_RECORD_MISMATCH")
    input_attack("receipt_hash_tamper", "external_acceptance", external_fixture, external_recipe, "candidate_bundle", "external_candidate_bundle", "candidate:bad-receipt", "TPA_CANDIDATE_CHAIN_HASH_MISMATCH")
    input_attack("accepted_policy_payload_resealed", "external_acceptance", external_fixture, external_recipe, "candidate_bundle", "external_candidate_bundle", "candidate:policy-payload-resealed", "TPA_ACCEPTED_RECORD_MISMATCH")

    cutoff_recipe, cutoff_fixture = "recipe.cutoff_exact_present_absent", "fixture.recipe.02.cutoff"
    input_attack("cutoff_join_zero", "join", cutoff_fixture, cutoff_recipe, "binding_refs", "string_list", [], "TPA_CUTOFF_ZERO_OR_MULTIPLE")
    input_attack("cutoff_join_multiple", "join", cutoff_fixture, cutoff_recipe, "binding_refs", "string_list", ["cutoff-binding:1", "cutoff-binding:2"], "TPA_CUTOFF_ZERO_OR_MULTIPLE")
    input_attack("cutoff_cross_scope", "scope", cutoff_fixture, cutoff_recipe, "accepted_scope_refs", "string_list", ["project:foreign", "run:r1", "site:s1", "subject:u1"], "TPA_SCOPE_DRIFT")
    input_attack("cutoff_state_absent_with_date", "cutoff", cutoff_fixture, cutoff_recipe, "cutoff_state", "string", "absent", "TPA_CUTOFF_STATE_MISMATCH")
    input_attack("cutoff_state_forged", "cutoff", cutoff_fixture, cutoff_recipe, "cutoff_state", "string", "forged", "TPA_CUTOFF_STATE_MISMATCH")
    output_attack("cutoff_output_forged", "output", cutoff_fixture, cutoff_recipe, "cutoff_date", "date", "2026-12-31", "TPA_EXPECTED_OUTPUT_MISMATCH")

    visibility_recipe, visibility_fixture = "recipe.visibility_universe_and_stable_bridge", "fixture.recipe.03.visibility"
    input_attack("visibility_bridge_missing", "visibility", visibility_fixture, visibility_recipe, "bridge_members", "string_list", ["member:m1"], "TPA_VISIBILITY_BRIDGE_INCOMPLETE")
    input_attack("visibility_overlap", "visibility", visibility_fixture, visibility_recipe, "hidden_members", "string_list", ["member:m1", "member:m2"], "TPA_VISIBILITY_SET_OVERLAP")
    input_attack("visibility_count_forged", "visibility", visibility_fixture, visibility_recipe, "declared_count", "integer", 3, "TPA_VISIBILITY_COUNT_MISMATCH")
    input_attack("visibility_hash_forged", "visibility", visibility_fixture, visibility_recipe, "declared_hash", "sha256", "f" * 64, "TPA_VISIBILITY_HASH_MISMATCH")
    input_attack("visibility_member_add", "visibility", visibility_fixture, visibility_recipe, "evaluation_members", "string_list", ["member:m1", "member:m2", "member:m3"], "TPA_VISIBILITY_PARTITION_MISMATCH")
    input_attack("visibility_member_drop", "visibility", visibility_fixture, visibility_recipe, "evaluation_members", "string_list", ["member:m1"], "TPA_VISIBILITY_PARTITION_MISMATCH")

    locator_recipe, locator_fixture = "recipe.locator_total_consumption_revision_partition", "fixture.recipe.04.locator"
    input_attack("locator_unused", "locator", locator_fixture, locator_recipe, "consumed_refs", "string_list", ["locator:l1"], "TPA_LOCATOR_UNUSED")
    input_attack("locator_wrong_record", "locator", locator_fixture, locator_recipe, "record_bindings", "string_list", ["locator:l1|record:forged|field:start|raw:" + "a" * 64, "locator:l2|record:r2|field:end|raw:" + "b" * 64], "TPA_LOCATOR_BINDING_MISMATCH")
    input_attack("locator_wrong_field", "locator", locator_fixture, locator_recipe, "record_bindings", "string_list", ["locator:l1|record:r1|field:forged|raw:" + "a" * 64, "locator:l2|record:r2|field:end|raw:" + "b" * 64], "TPA_LOCATOR_BINDING_MISMATCH")
    input_attack("locator_wrong_raw", "locator", locator_fixture, locator_recipe, "record_bindings", "string_list", ["locator:l1|record:r1|field:start|raw:" + "f" * 64, "locator:l2|record:r2|field:end|raw:" + "b" * 64], "TPA_LOCATOR_BINDING_MISMATCH")
    input_attack("locator_revision_partition", "locator", locator_fixture, locator_recipe, "revision_assignments", "string_list", ["locator:l1=revision:v1"], "TPA_REVISION_PARTITION_INCOMPLETE")

    axis_recipe, axis_fixture = "recipe.temporal_axis_timezone_day_zero", "fixture.recipe.05.axis"
    input_attack("axis_timezone", "axis", axis_fixture, axis_recipe, "timezone", "string", "UTC", "TPA_TIMEZONE_MISMATCH")
    input_attack("axis_day_zero", "axis", axis_fixture, axis_recipe, "day_zero_convention", "string", "anchor_is_day_two", "TPA_DAY_ZERO_MISMATCH")
    input_attack("axis_anchor_zero", "axis", axis_fixture, axis_recipe, "anchor_refs", "string_list", [], "TPA_STUDY_DAY_WITHOUT_EXACT_ANCHOR")

    endpoint_recipe, endpoint_fixture = "recipe.endpoint_state_range_main_axis", "fixture.recipe.06.endpoint"
    input_attack("endpoint_state_forged", "endpoint", endpoint_fixture, endpoint_recipe, "date_state", "string", "forged", "TPA_ENDPOINT_STATE_INVALID")
    input_attack("endpoint_geometry_forged", "endpoint", endpoint_fixture, endpoint_recipe, "geometry", "string", "triangle", "TPA_ENDPOINT_STATE_INVALID")
    input_attack("endpoint_range_reversed", "endpoint", endpoint_fixture, endpoint_recipe, "candidate_dates", "date_list", ["2026-01-12", "2026-01-10"], "TPA_RANGE_INVALID")
    input_attack("endpoint_count_forged", "endpoint", endpoint_fixture, endpoint_recipe, "declared_candidate_count", "integer", 9, "TPA_ENDPOINT_COUNT_MISMATCH")
    input_attack("endpoint_exact_wrong_geometry", "endpoint", endpoint_fixture, endpoint_recipe, "date_state", "string", "exact", "TPA_ENDPOINT_STATE_INVALID")
    input_attack("endpoint_main_axis_forged", "endpoint", endpoint_fixture, endpoint_recipe, "main_axis_mode", "string", "forced", "TPA_ENDPOINT_STATE_INVALID")
    output_attack("endpoint_output_forged", "output", endpoint_fixture, endpoint_recipe, "date_range", "date_list", ["2020-01-01", "2030-01-01"], "TPA_EXPECTED_OUTPUT_MISMATCH")

    visit_recipe, visit_fixture = "recipe.visit_assignment_actual_bundle_encounter", "fixture.recipe.07.visit"
    input_attack("visit_join_zero", "join", visit_fixture, visit_recipe, "assignment_refs", "string_list", [], "TPA_VISIT_JOIN_ZERO_OR_MULTIPLE")
    input_attack("visit_join_multiple", "join", visit_fixture, visit_recipe, "assignment_refs", "string_list", ["assignment:a1", "assignment:a2"], "TPA_VISIT_JOIN_ZERO_OR_MULTIPLE")
    input_attack("visit_unscheduled_snap", "visit", visit_fixture, visit_recipe, "visit_kind", "string", "unscheduled", "TPA_UNSCHEDULED_SNAPPED")
    input_attack("visit_nominal_actual_substitution", "visit", visit_fixture, visit_recipe, "actual_ref", "string", "endpoint:nominal", "TPA_NOMINAL_ACTUAL_SUBSTITUTION")

    event_recipe, event_fixture = "recipe.event_exact_activity_binding", "fixture.recipe.08.event"
    input_attack("event_join_zero", "event", event_fixture, event_recipe, "activity_match_refs", "string_list", [], "TPA_EVENT_BINDING_MISMATCH")
    input_attack("event_join_multiple", "event", event_fixture, event_recipe, "activity_match_refs", "string_list", ["activity-match:1", "activity-match:2"], "TPA_EVENT_BINDING_MISMATCH")
    input_attack("event_semantic_zero", "event", event_fixture, event_recipe, "semantic_authority_refs", "string_list", [], "TPA_EVENT_SEMANTIC_UNRESOLVED")
    input_attack("event_semantic_multiple", "event", event_fixture, event_recipe, "semantic_authority_refs", "string_list", ["semantic:event:1", "semantic:event:2"], "TPA_EVENT_SEMANTIC_UNRESOLVED")

    phase_recipe, phase_fixture = "recipe.phase_binding_accepted_zh_lexicon", "fixture.recipe.09.phase"
    input_attack("phase_code_forged", "phase", phase_fixture, phase_recipe, "phase_code", "string", "washout", "TPA_PHASE_LABEL_UNACCEPTED")
    input_attack("phase_label_shape_forged", "phase", phase_fixture, phase_recipe, "phase_labels", "string_list", ["基线期"], "TPA_PHASE_LABEL_UNACCEPTED")
    input_attack("phase_anchor_zero", "phase", phase_fixture, phase_recipe, "anchor_refs", "string_list", [], "TPA_PHASE_BINDING_MISMATCH")

    risk_recipe, risk_fixture = "recipe.risk_s4_eight_identity_endpoint_binding", "fixture.recipe.10.risk"
    input_attack("risk_join_seven", "join", risk_fixture, risk_recipe, "join_left", "string_list", [f"identity:{index}" for index in range(1, 8)], "TPA_S4_JOIN_NOT_EXACT_EIGHT")
    input_attack("risk_join_cross_scope", "join", risk_fixture, risk_recipe, "join_right", "string_list", ["identity:foreign"] + [f"identity:{index}" for index in range(2, 9)], "TPA_JOIN_CROSS_SCOPE")
    input_attack("risk_join_zero", "join", risk_fixture, risk_recipe, "risk_match_refs", "string_list", [], "TPA_RISK_JOIN_ZERO_OR_MULTIPLE")
    input_attack("risk_join_multiple", "join", risk_fixture, risk_recipe, "risk_match_refs", "string_list", ["risk-match:1", "risk-match:2"], "TPA_RISK_JOIN_ZERO_OR_MULTIPLE")

    domain_recipe, domain_fixture = "recipe.domain_applicable_or_controlled_empty", "fixture.recipe.11.domain"
    input_attack("domain_state_forged", "domain", domain_fixture, domain_recipe, "declared_state", "string", "not_applicable", "TPA_DOMAIN_APPLICABILITY_MISMATCH")
    input_attack("domain_set_missing", "domain", domain_fixture, domain_recipe, "domain_codes", "string_list", sorted(DOMAINS)[:-1], "TPA_DOMAIN_SET_NOT_EIGHT")
    input_attack("domain_empty_without_authority", "domain", domain_fixture, domain_recipe, "member_refs", "string_list", [], "TPA_DOMAIN_APPLICABILITY_MISMATCH")

    pending_recipe, pending_fixture = "recipe.pending_union_from_unprojectable_targets", "fixture.recipe.12.pending"
    input_attack("pending_add", "pending", pending_fixture, pending_recipe, "declared_pending_refs", "string_list", ["event:e1", "risk:r9", "visit:v1"], "TPA_PENDING_ADD_DROP")
    input_attack("pending_drop", "pending", pending_fixture, pending_recipe, "declared_pending_refs", "string_list", ["event:e1"], "TPA_PENDING_ADD_DROP")
    input_attack("pending_wrong_kind", "pending", pending_fixture, pending_recipe, "member_kind_pairs", "string_list", ["event|visit"], "TPA_PENDING_KIND_MISMATCH")
    output_attack("pending_output_forged", "output", pending_fixture, pending_recipe, "pending_refs", "string_list", ["forged:target"], "TPA_EXPECTED_OUTPUT_MISMATCH")

    append_recipe, append_fixture = "recipe.aemh_append_only_decision_registry", "fixture.recipe.13.aemh-append"
    input_attack("aemh_second_reminder", "aemh", append_fixture, append_recipe, "event_kinds", "string_list", ["reminder_created", "reminder_created"], "TPA_AEMH_SECOND_REMINDER")
    input_attack("aemh_invalid_transition", "aemh", append_fixture, append_recipe, "event_kinds", "string_list", ["match_decided", "reminder_created"], "TPA_AEMH_INVALID_TRANSITION")
    input_attack("aemh_candidate_fact_swap", "aemh", append_fixture, append_recipe, "candidate_fact_roles", "string_list", ["later_fact", "candidate"], "TPA_AEMH_CANDIDATE_FACT_SWAP")

    evidence_recipe, evidence_fixture = "recipe.aemh_joint_evidence_binding", "fixture.recipe.14.evidence"
    input_attack("evidence_role", "evidence", evidence_fixture, evidence_recipe, "entity_role", "string", "risk", "TPA_AEMH_EVIDENCE_ROLE_MISMATCH")
    input_attack("evidence_entity_hash", "evidence", evidence_fixture, evidence_recipe, "entity_content_hash", "sha256", "f" * 64, "TPA_AEMH_EVIDENCE_JOINT_MISMATCH")
    input_attack("evidence_locator", "evidence", evidence_fixture, evidence_recipe, "locator_ref", "string", "locator:forged", "TPA_AEMH_EVIDENCE_JOINT_MISMATCH")
    input_attack("evidence_raw", "evidence", evidence_fixture, evidence_recipe, "raw_payload_hash", "sha256", "f" * 64, "TPA_AEMH_EVIDENCE_JOINT_MISMATCH")
    input_attack("evidence_revision", "evidence", evidence_fixture, evidence_recipe, "revision_ref", "string", "revision:forged", "TPA_AEMH_EVIDENCE_JOINT_MISMATCH")

    thread_recipe, thread_fixture = "recipe.aemh_thread_membership", "fixture.recipe.15.thread"
    input_attack("thread_phantom_member", "aemh", thread_fixture, thread_recipe, "declared_member_refs", "string_list", ["candidate:c1", "fact:f1", "phantom:x"], "TPA_AEMH_THREAD_MEMBERSHIP_MISMATCH")
    input_attack("thread_cross_scope", "aemh", thread_fixture, thread_recipe, "member_scope_refs", "string_list", ["project:foreign", "site:s1", "subject:u1"], "TPA_AEMH_THREAD_CROSS_SCOPE")
    input_attack("thread_candidate_fact_swap", "aemh", thread_fixture, thread_recipe, "later_fact_refs", "string_list", ["candidate:c1"], "TPA_AEMH_THREAD_MEMBERSHIP_MISMATCH")

    prefix_recipe, prefix_fixture = "recipe.aemh_prefix_transition_closure", "fixture.recipe.16.prefix"
    input_attack("aemh_prefix_rewrite", "aemh", prefix_fixture, prefix_recipe, "current_entries", "string_list", ["forged", "h2"], "TPA_AEMH_PREFIX_REWRITE")
    input_attack("aemh_foreign_snapshot", "aemh", prefix_fixture, prefix_recipe, "current_snapshot_ref", "string", "snapshot:foreign", "TPA_AEMH_FOREIGN_SNAPSHOT")
    input_attack("aemh_lifecycle_effect", "aemh", prefix_fixture, prefix_recipe, "lifecycle_effects", "string_list", ["none", "close_risk"], "TPA_AEMH_LIFECYCLE_EFFECT")

    dag_recipe, dag_fixture = "recipe.upstream_roots_before_hashes_containers_packets", "fixture.recipe.17.dag"
    input_attack("dag_packet_forged", "dag", dag_fixture, dag_recipe, "declared_packet_hash", "sha256", "f" * 64, "TPA_PACKET_HASH_MISMATCH")
    input_attack("dag_receipt_forged", "dag", dag_fixture, dag_recipe, "declared_receipt_hash", "sha256", "f" * 64, "TPA_RECEIPT_HASH_MISMATCH")

    pin_recipe, pin_fixture = "recipe.parent_semantic_snapshot_immutability", "fixture.recipe.18.pins"
    input_attack("protected_pin_drift", "protected_pin", pin_fixture, pin_recipe, "actual_pins", "sha256_list", ["1" * 64, "f" * 64], "TPA_PROTECTED_PIN_DRIFT")
    for name in ("fixture", "target", "S4_value_transfer", "D07_OTHER", "model_role"):
        input_attack(f"forbidden_{name.lower()}", "forbidden_authority", pin_fixture, pin_recipe, "forbidden_sources", "string_list", [name], "TPA_FORBIDDEN_AUTHORITY_SOURCE")

    add("arbitrary_recipe_op_text", "recipe_ir", dag_recipe, dag_fixture, "accepted_recipe_registry", "accepted_recipe_registry", "/recipes/16/transforms/0/op", typed_value("op", "string", "trust the supplied target output"), "TPA_ACCEPTED_RECIPE_PIN_MISMATCH")
    add("study_day_recipe_and_output_resealed", "recipe_ir", axis_recipe_attack["recipe_id"], axis_fixture_attack["fixture_id"], "accepted_recipe_bundle", "accepted_recipe_registry", "/", typed_value("bundle_ref", "string", "recipe-attack:study-day-to-count-and-output-10"), "TPA_ACCEPTED_RECIPE_PIN_MISMATCH")

    schema_mutations = [
        ("object_add", "copy", "/objects/ForgedObject", "/objects/TemporalAxisAuthorityRecord"),
        ("object_remove", "remove", "/objects/TemporalAxisAuthorityRecord", "unused"),
        ("named_type_add", "copy", "/named_types/ForgedType", "/named_types/DependencyEdge"),
        ("named_type_remove", "remove", "/named_types/DependencyEdge", "unused"),
        ("field_add", "copy", "/objects/TemporalEndpointAuthorityRecord/properties/forged_field", "/objects/TemporalEndpointAuthorityRecord/properties/endpoint_ref"),
        ("field_remove", "remove", "/objects/TemporalEndpointAuthorityRecord/properties/endpoint_ref", "unused"),
        ("required_add", "append", "/named_types/CandidateOperationalEvidence/required/-", "transport_digest"),
        ("required_remove", "remove", "/objects/TemporalEndpointAuthorityRecord/required/0", "unused"),
        ("optional_add", "append", "/named_types/CandidateOperationalEvidence/optional/-", "observed_sequence"),
        ("optional_remove", "remove", "/named_types/CandidateOperationalEvidence/optional/0", "unused"),
        ("type_change", "replace", "/objects/TemporalEndpointAuthorityRecord/properties/endpoint_ref/type", "integer"),
        ("cardinality_change", "replace", "/objects/TemporalEndpointAuthorityRecord/properties/endpoint_ref/cardinality", "many"),
        ("nullability_change", "replace", "/objects/TemporalEndpointAuthorityRecord/properties/endpoint_ref/nullable", True),
        ("constraint_change", "replace", "/objects/TemporalAuthorityScopeIdentity/properties/project_ref/constraints/min_length", 2),
        ("constraint_add", "copy", "/objects/TemporalAuthorityScopeIdentity/properties/project_ref/constraints/minimum", "/objects/AEMHAppendDecisionAuthorityRecord/properties/seq/constraints/minimum"),
        ("constraint_remove", "remove", "/objects/TemporalAuthorityScopeIdentity/properties/project_ref/constraints/min_length", "unused"),
        ("enum_member_add", "append", "/enums/date_state/-", "forged"),
        ("enum_member_remove", "remove", "/enums/date_state/0", "unused"),
        ("enum_add", "copy", "/enums/forged_enum", "/enums/date_state"),
        ("enum_remove", "remove", "/enums/date_state", "unused"),
    ]
    for name, op, path, replacement_value in schema_mutations:
        value_type = "boolean" if isinstance(replacement_value, bool) else "integer" if isinstance(replacement_value, int) else "string"
        add(
            f"schema_{name}",
            "schema_baseline",
            endpoint_recipe,
            endpoint_fixture,
            "schema_baseline",
            name,
            path,
            typed_value("schema_patch", value_type, replacement_value),
            "TPA_SCHEMA_BASELINE_MISMATCH",
            op=op,
        )
    add(
        "closure_mapping_to_recipe_without_leaf",
        "leaf_bijection",
        dag_recipe,
        dag_fixture,
        "coverage_mapping",
        "subject-temporal-public-v1::SubjectTemporalAuthorityPacket.packet_content_hash",
        "/closure_ref",
        typed_value("recipe_id", "string", "recipe.temporal_axis_timezone_day_zero"),
        "TPA_LEAF_OUTPUT_NOT_DECLARED",
    )

    return specs, replacement_fixtures, recipe_attack_bundles


def build_challenges(schema: dict[str, Any], recipe_registry: dict[str, Any], external_root: dict[str, Any]) -> dict[str, Any]:
    former_d_roots = sorted({row["closure_ref"] for row in recipe_registry["coverage_ledger"] if row["before_status"] == "D_unconstructible" and row["closure_kind"] == "authority_root"})
    authority_fixtures = build_authority_fixtures(schema, former_d_roots)
    authority_fixture_map = {fixture["fixture_id"]: fixture for fixture in authority_fixtures}
    authority_mapping_positive_fixtures = []
    for mapping in recipe_registry["authority_output_registry"]["mappings"]:
        contract, leaf = mapping["qualified_leaf"].split("::", 1)
        owner, field = leaf.split(".", 1)
        mapping_fixtures = [authority_fixture_map[ref] for ref in mapping["source_fixture_refs"]]
        expected_value, execution_trace = LazyAuthorityProjectionExecutor(mapping_fixtures).execute(
            contract,
            owner,
            field,
            mapping["op"],
            mapping[f"{mapping['op']}_params"],
        )
        if execution_trace["consumed_fixture_refs"] != mapping["source_fixture_refs"] or execution_trace["consumed_field_paths"] != mapping["source_field_paths"]:
            raise RuntimeError(f"authority mapping dependency trace drift: {mapping['mapping_id']}")
        if execution_trace["verified_fixture_pins"] != mapping["source_fixture_content_hash_pins"]:
            raise RuntimeError(f"authority mapping fixture pin trace drift: {mapping['mapping_id']}")
        authority_mapping_positive_fixtures.append(
            sealed(
                {
                    "fixture_id": f"fixture.{mapping['mapping_id']}",
                    "mapping_id": mapping["mapping_id"],
                    "authority_fixture_refs": mapping["source_fixture_refs"],
                    "expected_target_canonical_json": canonical_bytes(expected_value).decode("utf-8"),
                    "expected_target_content_hash": digest(expected_value),
                    "expected_trace_content_hash": execution_trace["trace_content_hash"],
                },
                "fixture_content_hash",
            )
        )
    positive_fixtures = build_positive_fixtures(external_root)
    attack_specs, replacement_fixtures, recipe_attack_bundles = build_active_attack_specs(positive_fixtures, recipe_registry["recipes"])
    cases: list[dict[str, Any]] = []
    for index, row in enumerate(recipe_registry["coverage_ledger"], 1):
        cases.append(
            {
                "case_id": f"TPA-LEAF-{index:03d}",
                "category": "leaf_bijection",
                "probe_kind": "coverage_leaf_delete",
                "covered_leaf": f"{row['contract']}::{row['leaf']}",
                "recipe_id": None,
                "fixture_id": None,
                "mutation": challenge_mutation("coverage_ledger", "coverage_ledger", str(index - 1), typed_value("removed_index", "integer", index - 1), op="remove"),
                "expected_error": "TPA_LEAF_COVERAGE_GAP",
                "required_non_llm_anchor": "accepted 17/13 schemas plus exact coverage ledger cardinality",
            }
        )
    for index, spec in enumerate(attack_specs, 1):
        cases.append(
            {
                "case_id": f"TPA-ATTACK-{index:03d}-{spec['name']}",
                "category": spec["category"],
                "probe_kind": "semantic_typed_mutation",
                "covered_leaf": None,
                "recipe_id": spec["recipe_id"],
                "fixture_id": spec["fixture_id"],
                "mutation": spec["mutation"],
                "expected_error": spec["expected_error"],
                "required_non_llm_anchor": "independent typed IR interpreter plus immutable manifest registry root and schema closure",
            }
        )
    base_authority_fixture_refs = [fixture["fixture_id"] for fixture in authority_fixtures if fixture["fixture_id"].count(":") == 1]
    authority_attacks = [
        ("cyclic_swap_all_18_refs", "authority_fixture_catalog", "/fixture_id_value_cycle", typed_value("fixture_refs", "string_list", base_authority_fixture_refs[1:] + [next(iter(base_authority_fixture_refs))]), "TPA_AUTHORITY_FIXTURE_REF_IDENTITY_MISMATCH"),
        ("pairwise_swap_same_type_refs", "authority_fixture_catalog", "/same_type_pair", typed_value("fixture_pair", "string_list", ["authority:EventProjectionBinding", "authority:EventProjectionBinding:2"]), "TPA_AUTHORITY_FIXTURE_CONTENT_HASH_MISMATCH"),
        ("wrong_scope_root", "authority_fixture", "/value/scope_identity/project_ref", typed_value("project_ref", "string", "project:foreign"), "TPA_AUTHORITY_SCOPE_MISMATCH"),
        ("source_field_path_change", "authority_output_registry", "/mappings/0/source_field_paths/0", typed_value("source_field_path", "string", "TemporalAuthorityScopeIdentity.forged_field"), "TPA_AUTHORITY_REGISTRY_PIN_MISMATCH"),
        ("assembly_member_drop", "authority_mapping_fixture", "/expected_target_canonical_json/drop", typed_value("member_op", "string", "drop_exact_member"), "TPA_AUTHORITY_EXPECTED_TARGET_MISMATCH"),
        ("assembly_member_add", "authority_mapping_fixture", "/expected_target_canonical_json/add", typed_value("member_op", "string", "add_forged_member"), "TPA_AUTHORITY_EXPECTED_TARGET_MISMATCH"),
        ("assembly_member_reorder", "authority_mapping_fixture", "/expected_target_canonical_json/reorder", typed_value("member_op", "string", "reverse_semantic_order"), "TPA_AUTHORITY_EXPECTED_TARGET_MISMATCH"),
        ("authority_registry_content_hash_reseal", "authority_output_registry", "/registry_content_hash/reseal", typed_value("reseal", "boolean", True), "TPA_AUTHORITY_REGISTRY_PIN_MISMATCH"),
        ("replace_all_mapping_dependencies_with_global_union", "authority_output_registry", "/mappings/*/source_fixture_refs/global_union", typed_value("dependency_mode", "string", "global_union"), "TPA_AUTHORITY_UNUSED_DECLARED_DEPENDENCY"),
        ("mapping_no_op_dispatch", "authority_output_registry", "/mappings/0/op/no_op", typed_value("op", "string", "no_op"), "TPA_AUTHORITY_OP_INVALID"),
        ("cyclic_reassignment_all_recipe_authority_refs", "recipe_authority_binding_registry", "/bindings/*/requirements/cycle", typed_value("binding_mode", "string", "cyclic_all_18"), "TPA_RECIPE_AUTHORITY_BINDING_MISMATCH"),
    ]
    projection_ops = ["direct_field", "derive_value", "project_record", "assemble_sorted_records", "canonical_hash", "project_contract"]
    for source_op in projection_ops:
        for target_op in projection_ops:
            if source_op == target_op:
                continue
            authority_attacks.append(
                (
                    f"op_substitution_{source_op}_to_{target_op}",
                    "authority_output_registry",
                    f"/mappings/op_substitution/{source_op}/{target_op}",
                    typed_value("op", "string", target_op),
                    "TPA_AUTHORITY_OP_PARAMS_MISMATCH",
                )
            )
    for op in projection_ops:
        authority_attacks.append(
            (
                f"op_specific_negative_output_{op}",
                "authority_mapping_fixture",
                f"/expected_target_canonical_json/op_negative/{op}",
                typed_value("op", "string", op),
                "TPA_AUTHORITY_EXPECTED_TARGET_MISMATCH",
            )
        )
    for offset, (name, target_kind, path, replacement, error) in enumerate(authority_attacks, len(attack_specs) + 1):
        cases.append(
            {
                "case_id": f"TPA-ATTACK-{offset:03d}-{name}",
                "category": "authority_projection",
                "probe_kind": "semantic_typed_mutation",
                "covered_leaf": None,
                "recipe_id": None,
                "fixture_id": None,
                "mutation": challenge_mutation(target_kind, name, path, replacement),
                "expected_error": error,
                "required_non_llm_anchor": "independent authority projection executor over exact typed fixture references and manifest-pinned mapping registry",
            }
        )
    authority_op_counts = {
        op: sum(1 for mapping in recipe_registry["authority_output_registry"]["mappings"] if mapping["op"] == op)
        for op in projection_ops
    }
    return {
        "schema": "medical-monitoring-r5-s5-temporal-projection-authority-challenge-registry-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "external_candidate_fixtures": build_candidate_catalog(external_root),
        "authority_fixtures": authority_fixtures,
        "authority_mapping_positive_fixtures": authority_mapping_positive_fixtures,
        "positive_fixtures": positive_fixtures,
        "replacement_positive_fixtures": replacement_fixtures,
        "replacement_recipe_attack_bundles": recipe_attack_bundles,
        "former_d_authority_root_families": former_d_roots,
        "positive_fixture_count": len(positive_fixtures),
        "authority_mapping_positive_fixture_count": len(authority_mapping_positive_fixtures),
        "semantic_typed_probe_count": len(positive_fixtures) + len(authority_mapping_positive_fixtures) + len(attack_specs) + len(authority_attacks),
        "unconsumed_authority_fixture_ref_count": 0,
        "generic_schema_mutation_case_count": sum(1 for spec in attack_specs if spec["category"] == "schema_baseline"),
        "authority_op_counts": authority_op_counts,
        "op_branch_positive_coverage": {op: authority_op_counts[op] > 0 for op in projection_ops},
        "cross_op_substitution_control_count": len(projection_ops) * (len(projection_ops) - 1),
        "op_specific_negative_output_count": len(projection_ops),
        "structural_coverage_probe_count": 272,
        "cases": cases,
        "case_count": len(cases),
        "leaf_bijection_case_count": 272,
        "active_attack_case_count": len(attack_specs) + len(authority_attacks),
        "single_mutation_per_case": True,
        "distinct_case_ids": True,
        "expected_oracle": "non_llm_independent_typed_ir_interpreter",
    }


def negative_pins(version: str) -> dict[str, str]:
    base = f"medical_monitoring_r5_s5_public_authority_implementation_contract_v0_{version}"
    paths = [
        f"context/{base.replace(f'_v0_{version}', '')}{'_v0_2_20260820_context.md' if version == '2' else '_20260819_context.md'}",
        f"reviews/{base}_{'20260820' if version == '2' else '20260819'}.md",
        f"artifacts/{base}/invariant_error_matrix.json",
        f"artifacts/{base}/manifest.json",
        f"artifacts/{base}/public_api.json",
        f"artifacts/{base}/source_join_matrix.json",
        f"artifacts/{base}/test_matrix.json",
        f"tools/generate_{base}.py",
        f"tools/verify_{base}.py",
    ]
    return {path: raw_sha(ROOT / path) for path in paths}


def build_accepted_recipe_registry(full_registry: dict[str, Any]) -> dict[str, Any]:
    registry = sealed(
        {
            "registry_id": "accepted-recipe-registry:r5-s5:temporal-projection:20260820",
            "contract_id": CONTRACT_ID,
            "schema_version": SCHEMA_VERSION,
            "authority_scope": AUTHORITY_SCOPE,
            "non_clinical": True,
            "recipes": copy.deepcopy(full_registry["recipes"]),
            "recipe_count": full_registry["recipe_count"],
            "recipe_content_hashes": copy.deepcopy(full_registry["recipe_content_hashes"]),
        },
        "registry_content_hash",
    )
    if EXPECTED_ACCEPTED_RECIPE_REGISTRY_CONTENT_HASH is not None and registry["registry_content_hash"] != EXPECTED_ACCEPTED_RECIPE_REGISTRY_CONTENT_HASH:
        raise RuntimeError("accepted recipe registry drift")
    return registry


def build_recipe_reference_artifact(full_registry: dict[str, Any], accepted_registry: dict[str, Any]) -> dict[str, Any]:
    artifact = copy.deepcopy(full_registry)
    artifact.pop("recipes")
    artifact["accepted_recipe_registry_reference"] = {
        "manifest_path": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json",
        "section_pointer": "/accepted_recipe_registry",
        "registry_id": accepted_registry["registry_id"],
        "registry_content_hash": accepted_registry["registry_content_hash"],
        "recipe_count": accepted_registry["recipe_count"],
        "recipe_content_hashes": copy.deepcopy(accepted_registry["recipe_content_hashes"]),
    }
    artifact["candidate_supplies_recipe_definition"] = False
    return artifact


def build_manifest(
    artifacts: dict[str, Any],
    recipe_registry: dict[str, Any],
    challenges: dict[str, Any],
    external_root: dict[str, Any],
    schema: dict[str, Any],
    accepted_recipe_registry: dict[str, Any],
) -> dict[str, Any]:
    if EXPECTED_SCHEMA_BASELINE_CONTENT_HASH is not None and digest(schema) != EXPECTED_SCHEMA_BASELINE_CONTENT_HASH:
        raise RuntimeError("accepted schema baseline drift")
    parent = read_json(PARENT_MANIFEST)
    semantic = read_json(SEMANTIC_MANIFEST)
    non_manifest_paths = [path for path in PATHS if not path.endswith("/manifest.json")]
    raw_pins: dict[str, str] = {}
    for path in non_manifest_paths:
        if path.startswith("artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/"):
            name = pathlib.Path(path).name
            raw_pins[path] = hashlib.sha256((json.dumps(artifacts[name], ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")).hexdigest()
        else:
            raw_pins[path] = raw_sha(ROOT / path)
    manifest = {
        "schema": "medical-monitoring-r5-s5-temporal-projection-authority-delta-manifest-v0.1",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "status": "IMPLEMENTED_FOR_INDEPENDENT_REVIEW_NOT_ACCEPTED",
        "authority_scope": AUTHORITY_SCOPE,
        "non_clinical": True,
        "exact_delta_paths": list(PATHS),
        "artifact_raw_sha256": raw_pins,
        "accepted_parent_pins": {
            "manifest_path": PARENT_MANIFEST,
            "manifest_raw_sha256": raw_sha(ROOT / PARENT_MANIFEST),
            "acceptance_path": PARENT_ACCEPTANCE,
            "acceptance_raw_sha256": raw_sha(ROOT / PARENT_ACCEPTANCE),
            "artifact_raw_sha256": parent["artifact_raw_sha256"],
            "source_file_sha256": parent["source_file_sha256"],
            "protected_accepted_pins": parent["protected_accepted_pins"],
        },
        "accepted_semantic_delta_pins": {
            "manifest_path": SEMANTIC_MANIFEST,
            "manifest_raw_sha256": raw_sha(ROOT / SEMANTIC_MANIFEST),
            "acceptance_path": SEMANTIC_ACCEPTANCE,
            "acceptance_raw_sha256": raw_sha(ROOT / SEMANTIC_ACCEPTANCE),
            "artifact_raw_sha256": semantic["artifact_raw_sha256"],
        },
        "rejected_snapshot_negative_evidence_only": {
            "authority": False,
            "v0_1": negative_pins("1"),
            "v0_2": negative_pins("2"),
            "rejection_record_path": REJECTION_RECORD,
            "rejection_record_raw_sha256": raw_sha(ROOT / REJECTION_RECORD),
        },
        "coverage": {
            "total": recipe_registry["total_leaf_count"],
            "before": recipe_registry["coverage_counts_before"],
            "before_by_contract": recipe_registry["coverage_counts_before_by_contract"],
            "former_d": recipe_registry["former_d_leaf_count"],
            "unexplained_after": recipe_registry["unexplained_leaf_count"],
            "after": recipe_registry["coverage_counts_after"],
        },
        "object_count": len(artifacts["schema.json"]["objects"]),
        "named_type_count": len(artifacts["schema.json"]["named_types"]),
        "enum_count": len(artifacts["schema.json"]["enums"]),
        "recipe_count": recipe_registry["recipe_count"],
        "challenge_count": challenges["case_count"],
        "leaf_bijection_challenge_count": challenges["leaf_bijection_case_count"],
        "active_attack_count": challenges["active_attack_case_count"],
        "positive_fixture_count": challenges["positive_fixture_count"],
        "authority_mapping_positive_fixture_count": challenges["authority_mapping_positive_fixture_count"],
        "authority_mapping_count": recipe_registry["authority_mapping_count"],
        "executable_authority_mapping_count": recipe_registry["executable_authority_mapping_count"],
        "unconsumed_authority_fixture_ref_count": challenges["unconsumed_authority_fixture_ref_count"],
        "authority_leaf_without_emitter_count": recipe_registry["authority_leaf_without_emitter_count"],
        "unique_dependency_slice_count": recipe_registry["unique_dependency_slice_count"],
        "min_dependency_count": recipe_registry["min_dependency_count"],
        "max_dependency_count": recipe_registry["max_dependency_count"],
        "median_dependency_count": recipe_registry["median_dependency_count"],
        "mappings_with_all_19_count": recipe_registry["mappings_with_all_19_count"],
        "unused_declared_dependency_count": recipe_registry["unused_declared_dependency_count"],
        "authority_op_counts": recipe_registry["authority_op_counts"],
        "op_branch_positive_coverage": recipe_registry["op_branch_positive_coverage"],
        "cross_op_substitution_control_count": challenges["cross_op_substitution_control_count"],
        "op_specific_negative_output_count": challenges["op_specific_negative_output_count"],
        "semantic_typed_probe_count": challenges["semantic_typed_probe_count"],
        "structural_coverage_probe_count": challenges["structural_coverage_probe_count"],
        "external_acceptance_registry_root": external_root,
        "accepted_record_content_hash_pins": {
            record["accepted_record_ref"]: record["record_content_hash"]
            for record in external_root["accepted_records"]
        },
        "accepted_record_count": len(external_root["accepted_records"]),
        "external_registry_root_content_hash_pin": external_root["root_content_hash"],
        "external_registry_section_canonical_sha256_pin": EXPECTED_EXTERNAL_REGISTRY_SECTION_CANONICAL_SHA256,
        "external_registry_root_ownership": "manifest_owned_contract_artifact_not_candidate_fixture",
        "accepted_schema_baseline": {
            "schema": copy.deepcopy(schema),
            "schema_content_hash": digest(schema),
        },
        "accepted_schema_baseline_content_hash_pin": digest(schema),
        "accepted_recipe_registry": accepted_recipe_registry,
        "accepted_recipe_registry_content_hash_pin": accepted_recipe_registry["registry_content_hash"],
        "accepted_recipe_content_hash_pins": copy.deepcopy(accepted_recipe_registry["recipe_content_hashes"]),
        "accepted_recipe_count": accepted_recipe_registry["recipe_count"],
        "accepted_authority_output_registry": copy.deepcopy(recipe_registry["authority_output_registry"]),
        "accepted_authority_output_registry_content_hash_pin": recipe_registry["authority_output_registry_content_hash"],
        "accepted_authority_mapping_count": recipe_registry["authority_mapping_count"],
        "accepted_recipe_authority_binding_registry": copy.deepcopy(recipe_registry["recipe_authority_binding_registry"]),
        "accepted_recipe_authority_binding_registry_content_hash_pin": recipe_registry["recipe_authority_binding_registry_content_hash"],
        "candidate_receipt_is_authority": False,
        "parent_and_semantic_snapshots_rewritten": False,
        "producer_runtime_test_evidence_acceptance_files_created": False,
        "public_api_surface": {"status": "none_contract_delta_only", "producer_callable_created": False},
        "port_8911_must_be_stopped": True,
        "no_self_acceptance": True,
        "unlock": "fresh reviewer may accept this delta; acceptance only unlocks implementation contract v0.3 generation",
        "does_not_unlock": ["producer", "S5 runtime", "UI/browser", "real project/model", "clinical authority", "product", "production", "medical-writing"],
        "manifest_hash_recipe": "sha256(canonical_json(manifest excluding manifest_content_hash))",
    }
    manifest["manifest_content_hash"] = digest(manifest)
    return manifest


def render() -> dict[str, bytes]:
    schema = build_schema()
    policies = build_controlled_policies()
    policy_hashes = {name: digest(value) for name, value in policies.items()}
    external_root = build_external_registry_root(policy_hashes)
    source_matrix = build_source_matrix()
    recipes = build_recipes(external_root)
    accepted_recipe_registry = build_accepted_recipe_registry(recipes)
    recipe_reference_artifact = build_recipe_reference_artifact(recipes, accepted_recipe_registry)
    challenges = build_challenges(schema, recipes, external_root)
    objects = {
        "schema.json": schema,
        "source_matrix_delta.json": source_matrix,
        "recipe_registry.json": recipe_reference_artifact,
        "challenge_registry.json": challenges,
    }
    manifest = build_manifest(objects, recipe_reference_artifact, challenges, external_root, schema, accepted_recipe_registry)
    objects["manifest.json"] = manifest
    return {name: (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8") for name, value in objects.items()}


def write_or_check(check: bool) -> None:
    rendered = render()
    if check:
        drift = []
        for name, expected in rendered.items():
            path = OUT / name
            if not path.is_file() or path.read_bytes() != expected:
                drift.append(str(path.relative_to(ROOT)))
        if drift:
            raise SystemExit("artifact drift: " + ", ".join(drift))
        print(json.dumps({"ok": True, "mode": "check", "artifact_count": len(rendered)}, sort_keys=True))
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for name, data in rendered.items():
        target = OUT / name
        with tempfile.NamedTemporaryFile(dir=OUT, delete=False) as handle:
            handle.write(data)
            temp = pathlib.Path(handle.name)
        os.replace(temp, target)
    print(json.dumps({"ok": True, "mode": "write", "artifact_count": len(rendered)}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    write_or_check(args.check)


if __name__ == "__main__":
    main()
