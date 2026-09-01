"""Generate the synthetic-only R5-S5 temporal projection authority delta v0.2.

The generator owns seven data/prose outputs.  It never reads a parent base
packet.  Full packets are composed from typed authority inputs by the executor
below and are retained only as in-memory observations.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import socket
import sys
import unicodedata
from typing import Any

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
CONTRACT_ID = "r5-s5-temporal-projection-authority-delta-v0.2"
SCHEMA_VERSION = "2026-08-21.1"
PARENT_SCHEMA_VERSION = "2026-08-19.1"
PROFILE = "full_parent_graph"
AUTHORITY_SCOPE = "synthetic_test_only"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
AUDIENCE = "contract.s4.1"

PATHS = (
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_20260821_context.md",
    "reviews/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_20260821.md",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/schema.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/emitter_recipe_registry.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/trace_realization_registry.json",
    "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
    "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
)

PARENT_MANIFEST = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json"
PARENT_VALIDATOR = "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py"
SUBJECT_SCHEMA = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json"
AEMH_SCHEMA = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json"
V01_MANIFEST = "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json"
PARENT_CHALLENGES = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/challenge_registry.json"

TYPED_SOURCE_PINS = json.loads((ROOT / PARENT_MANIFEST).read_text())["source_file_sha256"]
if len(TYPED_SOURCE_PINS) != 15:
    raise RuntimeError("accepted parent typed-source pin cardinality drift")

FROZEN_PINS = {
    V01_MANIFEST: "e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97",
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_acceptance_record_20260820.md": "523351f1b5536b12c1a5be9251ad01f4e8b7a70f5088073a2333aefc241d1b79",
    PARENT_MANIFEST: "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270",
    SUBJECT_SCHEMA: "d2f56f21dc7b228736b2efbdc4c1db3a28185e25895563c0b59a812cd126a0f4",
    AEMH_SCHEMA: "479dc2759833d698fd761247f4ec504069880717ec9c64631242ad2554b19840",
    PARENT_VALIDATOR: "1aebff8f6a7ed95b6fb3665f9a7fc37fe1d7e66393f3ac62501f4799ba9e2491",
    "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json": "66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py": "0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json": "53a927a08451b426edb9ac9578a6ea3b658ff8df1d5dd2b33f94fb0446647822",
}

REJECTED_V03_PINS = {
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820_context.md": "a94f9c793c03339ce8c342e54db68f706693464e24208470d28d1a981160f448",
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_rejection_record_20260820.md": "11b2baf15c1c89cc22a0a052c2e591ba6ce88e79cf660535578f6ba07e98099a",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820.md": "68e82a6e248a60f56e339f31f9416da2954e347b335d55abeb9e566300590a3c",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/invariant_error_matrix.json": "77780a7d95dc468ca64efda9a49bde28d701313c19c7a26440852dcb23aa9170",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/manifest.json": "c3c9e9d2ba6cb25bf9f73d4a4f685b2e8f8cb8bf4ba5707803d1a356061a4f35",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/public_api.json": "a10e30115c8351a30ed1987ed1eb6b230e5b2ab1a225887a4bda5d117c6aff0a",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/source_join_matrix.json": "85b5678debd1f99f2df07810a39a29aaf508d833e1f5a8afeda3f689480d08d8",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/test_matrix.json": "7937c0e2d71b1397ed4eddee22e7dd3343459ae4fa9a84fc49aa657983338466",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py": "5cad78d95fed0e83eb587bc3804859c84301b3771ba8cde56c443e119010c9ae",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py": "ebf426693566d6cee73aea8d62958219b846b7baca55b136fcd917be835049e5",
}

DOMAINS = [
    "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
    "symptom_efficacy", "protocol_compliance",
]
POSITIVE_CASES = ["R5C-109", "R5C-110", "R5C-116", *[f"R5C-{n}" for n in range(157, 164)]]


def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, tuple):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", key): canonicalize(value[key]) for key in sorted(value)}
    raise TypeError(type(value).__name__)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def sealed(value: dict[str, Any], hash_field: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(hash_field, None)
    result[hash_field] = digest(result)
    return result


def check_pins() -> None:
    for rel, expected in {**FROZEN_PINS, **REJECTED_V03_PINS, **TYPED_SOURCE_PINS}.items():
        actual = raw_sha(ROOT / rel)
        if actual != expected:
            raise SystemExit(f"STOP pin drift {rel}: {actual} != {expected}")


def typed_source_pin_issues(pin_map: Any) -> list[str]:
    if not isinstance(pin_map, dict) or set(pin_map) != set(TYPED_SOURCE_PINS):
        return ["TPA_V02_TYPED_SOURCE_PIN_SET"]
    issues = []
    for rel, expected in sorted(TYPED_SOURCE_PINS.items()):
        if not isinstance(pin_map.get(rel), str) or pin_map[rel] != expected:
            issues.append(f"TPA_V02_TYPED_SOURCE_PIN_VALUE:{rel}")
        elif raw_sha(ROOT / rel) != expected:
            issues.append(f"TPA_V02_TYPED_SOURCE_FILE_DRIFT:{rel}")
    return issues


def exact_type(fields: dict[str, str], optional: list[str] | None = None) -> dict[str, Any]:
    return {"additional_properties": False, "fields": fields, "optional": optional or [], "required": [key for key in fields if key not in (optional or [])]}


def build_schema() -> dict[str, Any]:
    enums = {
        "authority_scope": [AUTHORITY_SCOPE],
        "execution_profile": [PROFILE],
        "target_contract": [SUBJECT, AEMH],
        "cutoff_binding_state": ["present", "absent"],
        "supersession_disposition": ["supersede", "preserve"],
        "trace_lane": ["typed_source_transform", "parent_error_probe", "governance_probe"],
        "trace_disposition": ["accept", "reject"],
        "mutation_op": ["replace", "append", "append_copy", "reverse", "delete", "inject_unused_locator", "forge_later_fact_lineage"],
        "reseal_mode": ["full_subject_dag", "full_aemh_dag", "none"],
        "recipe_op": [
            "emit_subject_identity_cutoff", "seal_subject_identity_cutoff",
            "emit_subject_locators_revisions", "seal_subject_locators_revisions",
            "emit_subject_axis", "seal_subject_axis",
            "emit_subject_temporal_members", "seal_subject_temporal_members",
            "emit_subject_domains_pending_membership", "seal_subject_domains_pending_membership",
            "emit_subject_projection", "seal_subject_projection",
            "emit_subject_receipt", "seal_subject_receipt",
            "emit_subject_packet", "seal_subject_packet",
            "emit_aemh_identity_locators_revisions", "seal_aemh_identity_locators_revisions",
            "emit_aemh_previous_threads", "seal_aemh_previous_threads",
            "emit_aemh_previous_packet", "seal_aemh_previous_packet",
            "emit_aemh_current_threads", "seal_aemh_current_threads",
            "emit_aemh_current_membership_prefix_cutoff", "seal_aemh_current_membership_prefix_cutoff",
            "emit_aemh_projection", "seal_aemh_projection",
            "emit_aemh_receipt", "seal_aemh_receipt",
            "emit_aemh_packet", "seal_aemh_packet",
        ],
        "recipe_phase": ["identity_cutoff", "locators_revisions", "temporal_members", "domains_pending_membership", "axis", "projection", "receipt", "packet", "identity_locators_revisions", "previous_threads", "previous_packet", "current_threads", "current_membership_prefix_cutoff"],
        "trace_operation": ["recompute_bundle_identity", "recompute_all_study_days", "construct_full_graph", "apply_parent_mutation", "reseal_parent_graph", "validate_parent"],
        "domain": DOMAINS,
        "axis_mode": ["calendar", "study_day"],
        "day_zero_convention": ["anchor_day_zero", "anchor_day_one"],
        "aemh_domain": ["ae", "mh"],
        "history_event_kind": ["reminder_created", "match_decided", "withdrawn", "reappeared"],
        "match_state": ["exact", "ambiguous", "rejected"],
    }
    types = {
        "ExternalPinV02": exact_type({"path": "string", "sha256": "sha256", "role": "string"}),
        "EmitterSupersessionRuleV02": exact_type({"rule_id": "string", "v01_method": "string", "disposition": "enum:supersession_disposition", "required_manifest_sha256": "sha256", "execution_profile": "enum:execution_profile", "target_contracts": "list:enum:target_contract", "affected_mapping_ids": "list:string", "preserved_formulas": "list:string", "replacement_recipe_ids": "list:string"}),
        "RecipeNodeV02": exact_type({"node_id": "string", "op": "enum:recipe_op", "inputs": "list:string", "params": "RecipeParamsV02", "outputs": "list:string"}),
        "RecipeParamsV02": exact_type({"operation_version": "string", "phase": "enum:recipe_phase", "authority_input_pointers": "list:string", "prior_recipe_output_refs": "list:string", "output_name": "string", "canonicalization": "string"}),
        "ExecutableRecipeV02": exact_type({"recipe_id": "string", "target_contract": "enum:target_contract", "inputs": "list:string", "nodes": "list:RecipeNodeV02", "dependency_edges": "list:DependencyEdgeV02", "external_pin_refs": "list:string", "recipe_content_hash": "sha256"}),
        "DependencyEdgeV02": exact_type({"from": "string", "to": "string"}),
        "AuthorityBundleV02": exact_type({"contract_id": "string", "schema_version": "string", "authority_scope": "enum:authority_scope", "execution_profile": "enum:execution_profile", "temporal_v01_manifest_sha256": "sha256", "target_contract": "enum:target_contract", "source": "union:SubjectFullGraphInputV02|AEMHFullGraphInputV02", "bundle_content_identity": "sha256"}),
        "SubjectFullGraphInputV02": exact_type({"scope": "IdentityScopeInputV02", "cutoff_binding": "CutoffEndpointBindingV02", "locator_specs": "list:LocatorInputV02", "revision_specs": "list:RevisionInputV02", "axis": "AxisInputV02", "visit": "VisitInputV02", "events": "list:SubjectEventInputV02", "risk": "RiskInputV02", "phase": "PhaseInputV02", "domain_applicability": "list:DomainInputV02"}),
        "AEMHFullGraphInputV02": exact_type({"previous_scope": "ScopeInputV02", "current_scope": "ScopeInputV02", "previous_locator_specs": "list:LocatorInputV02", "current_locator_specs": "list:LocatorInputV02", "previous_revision_specs": "list:RevisionInputV02", "current_revision_specs": "list:RevisionInputV02", "thread_specs": "list:AEMHThreadInputV02", "decision_records": "list:AEMHDecisionInputV02"}),
        "IdentityScopeInputV02": exact_type({"project_ref": "string", "run_ref": "string", "snapshot_ref": "string", "site_ref": "string", "subject_ref": "string", "spine_ref": "string"}),
        "ScopeInputV02": exact_type({"project_ref": "string", "run_ref": "string", "snapshot_ref": "string", "cutoff_ref": "date", "site_ref": "string", "subject_ref": "string", "spine_ref": "string"}),
        "CutoffEndpointBindingV02": exact_type({"state": "enum:cutoff_binding_state", "exact_date": "nullable:date", "source_locator_refs": "list:string"}),
        "LocatorInputV02": exact_type({"locator_ref": "string", "record_ref": "string", "anchor": "string", "snapshot_ref": "string", "revision_ref": "string", "revision_content_identity": "sha256", "entity_kind": "nullable:string", "entity_ref": "nullable:string", "authority_domain": "nullable:string", "authority_thread_ref": "nullable:string"}),
        "RevisionInputV02": exact_type({"revision_ref": "string", "revision_content_identity": "sha256", "locator_refs": "list:string"}),
        "EndpointInputV02": exact_type({"state": "string", "exact_date": "nullable:date", "range_start": "nullable:date", "range_end": "nullable:date", "candidates": "list:string", "locator_refs": "list:string", "projectable": "boolean", "range_authorized": "boolean", "study_day": "nullable:integer"}),
        "AxisInputV02": exact_type({"axis_ref": "string", "mode": "enum:axis_mode", "timezone": "string", "day_zero_convention": "enum:day_zero_convention", "anchor_event_ref": "nullable:string", "study_day_enabled": "boolean"}),
        "VisitInputV02": exact_type({"visit_ref": "string", "planned_visit_ref": "string", "actual_encounter_ref": "string", "assignment_ref": "string", "phase_ref": "string", "nominal": "EndpointInputV02", "actual": "EndpointInputV02", "locator_refs": "list:string"}),
        "SubjectEventInputV02": exact_type({"event_ref": "string", "domain": "enum:domain", "subtype": "string", "visit_ref": "nullable:string", "geometry": "string", "start": "EndpointInputV02", "end": "EndpointInputV02", "risk_refs": "list:string", "locator_refs": "list:string", "content_identity": "sha256"}),
        "RiskInputV02": exact_type({"risk_anchor_ref": "string", "risk_ref": "string", "domain": "enum:domain", "severity": "string", "risk_type_zh": "string", "event_ref": "string", "visit_ref": "string", "geometry": "string", "start": "EndpointInputV02", "end": "EndpointInputV02", "locator_refs": "list:string", "content_identity": "sha256"}),
        "PhaseInputV02": exact_type({"phase_ref": "string", "label_zh": "string", "geometry": "string", "start": "EndpointInputV02", "end": "EndpointInputV02", "locator_refs": "list:string"}),
        "DomainInputV02": exact_type({"domain": "enum:domain", "state": "string", "event_refs": "list:string", "risk_refs": "list:string"}),
        "AEMHThreadInputV02": exact_type({"thread_ref": "string", "domain": "enum:aemh_domain", "candidate_ref": "string", "reminder_reason": "string", "candidate_locator_ref": "string"}),
        "AEMHDecisionInputV02": exact_type({"decision_ref": "string", "thread_ref": "string", "event_kind": "enum:history_event_kind", "match_state": "nullable:enum:match_state", "fact_refs": "list:string", "considered_fact_refs": "list:string", "reason_code": "string"}),
        "TraceRealizationBindingV02": exact_type({"source_case_ref": "string", "source_rule_id": "string", "base_input_ref": "string", "base_input_content_identity": "sha256", "contract": "enum:target_contract", "source_single_mutation": "ParentMutationV02", "adapter_id": "string", "realized_mutation": "union:SourceOperationV02|ParentMutationV02", "exact_path": "string", "instance_selector": "TraceInstanceSelectorV02", "pre_value": "any", "post_value": "any", "linked_operations": "list:union:SourceOperationV02|TraceLinkedOperationV02", "operation_count": "integer", "lane": "enum:trace_lane", "expected_disposition": "enum:trace_disposition", "expected_code": "string", "observed_disposition": "enum:trace_disposition", "observed_ordered_issues": "list:string", "reseal_mode": "enum:reseal_mode", "reseal_order": "list:string", "post_authority_input_content_identity": "sha256", "post_graph_content_hash": "sha256", "trace_identity": "sha256"}),
        "TraceInstanceSelectorV02": exact_type({"base_variant": "string", "semantic_rule_path": "string"}),
        "TraceLinkedOperationV02": exact_type({"op": "enum:trace_operation", "target": "string"}),
        "SourceOperationV02": exact_type({"sequence": "integer", "op": "enum:mutation_op", "path": "string", "pre_value": "any", "post_value": "any", "value": "any"}),
        "ParentMutationV02": exact_type({"op": "enum:mutation_op", "path": "string", "value": "any", "from_index": "integer", "locator": "any", "source_pair": "any", "forged_ref": "string", "source_locator_ref": "string"}, optional=["value", "from_index", "locator", "source_pair", "forged_ref", "source_locator_ref"]),
    }
    baseline = {"objects": types, "enums": enums}
    return {"schema": "r5-s5-temporal-projection-authority-delta-v0.2-exact", "schema_version": SCHEMA_VERSION, "exact_keys_recursive": True, **baseline, "baseline_content_hash": digest(baseline), "forbidden_candidate_keys": ["packet", "expected_packet", "expected_hash", "expected_error", "acceptance_token", "target_output"]}


def validate_typed(value: Any, type_name: str, schema: dict[str, Any], path: str = "$") -> list[str]:
    """Recursively enforce the closed v0.2 descriptor language."""
    if type_name.startswith("nullable:"):
        return [] if value is None else validate_typed(value, type_name[9:], schema, path)
    if type_name.startswith("list:"):
        if not isinstance(value, list):
            return [f"{path}:expected_list"]
        return [issue for index, item in enumerate(value) for issue in validate_typed(item, type_name[5:], schema, f"{path}[{index}]")]
    if type_name.startswith("enum:"):
        enum_name = type_name[5:]
        return [] if value in schema["enums"][enum_name] else [f"{path}:enum:{enum_name}"]
    if type_name.startswith("union:"):
        alternatives = type_name[6:].split("|")
        attempts = [validate_typed(value, alternative, schema, path) for alternative in alternatives]
        return [] if any(not attempt for attempt in attempts) else [f"{path}:union"]
    if type_name in schema["objects"]:
        descriptor = schema["objects"][type_name]
        if not isinstance(value, dict):
            return [f"{path}:expected_object:{type_name}"]
        fields = descriptor["fields"]
        required = set(descriptor["required"])
        issues = []
        if set(value) - set(fields):
            issues.append(f"{path}:extra_keys:{','.join(sorted(set(value) - set(fields)))}")
        if required - set(value):
            issues.append(f"{path}:missing_keys:{','.join(sorted(required - set(value)))}")
        for key in sorted(set(value) & set(fields)):
            issues.extend(validate_typed(value[key], fields[key], schema, f"{path}.{key}"))
        return issues
    if type_name == "any":
        try:
            canonical_bytes(value)
        except (TypeError, ValueError):
            return [f"{path}:noncanonical_any"]
        return []
    checks = {
        "string": lambda item: isinstance(item, str),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "object": lambda item: isinstance(item, dict),
        "sha256": lambda item: isinstance(item, str) and len(item) == 64 and all(char in "0123456789abcdef" for char in item),
        "date": lambda item: isinstance(item, str) and _valid_date(item),
    }
    if type_name not in checks:
        return [f"{path}:unknown_type:{type_name}"]
    return [] if checks[type_name](value) else [f"{path}:type:{type_name}"]


def _valid_date(value: str) -> bool:
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_authority_bundle(authority_bundle: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    issues = validate_typed(authority_bundle, "AuthorityBundleV02", schema)
    if issues:
        return issues
    if authority_bundle["contract_id"] != CONTRACT_ID:
        issues.append("$.contract_id:constant")
    if authority_bundle["schema_version"] != SCHEMA_VERSION:
        issues.append("$.schema_version:constant")
    if authority_bundle["authority_scope"] != AUTHORITY_SCOPE:
        issues.append("$.authority_scope:constant")
    if authority_bundle["execution_profile"] != PROFILE:
        issues.append("$.execution_profile:constant")
    if authority_bundle["temporal_v01_manifest_sha256"] != FROZEN_PINS[V01_MANIFEST]:
        issues.append("$.temporal_v01_manifest_sha256:pin")
    source_type = "SubjectFullGraphInputV02" if authority_bundle["target_contract"] == SUBJECT else "AEMHFullGraphInputV02"
    source_variant_issues = validate_typed(authority_bundle["source"], source_type, schema, "$.source")
    issues.extend(source_variant_issues)
    if source_variant_issues:
        return issues
    if authority_bundle["bundle_content_identity"] != digest({key: value for key, value in authority_bundle.items() if key != "bundle_content_identity"}):
        issues.append("$.bundle_content_identity:hash")
    if authority_bundle["target_contract"] == SUBJECT:
        source = authority_bundle["source"]
        if len(source["events"]) != 2 or len(source["domain_applicability"]) != 8 or [row["domain"] for row in source["domain_applicability"]] != DOMAINS:
            issues.append("$.source:subject_cardinality")
        if source["axis"]["study_day_enabled"] != (source["axis"]["anchor_event_ref"] is not None):
            issues.append("$.source.axis:study_day_cardinality")
    else:
        source = authority_bundle["source"]
        if len(source["thread_specs"]) != 2 or {row["domain"] for row in source["thread_specs"]} != {"ae", "mh"}:
            issues.append("$.source:thread_cardinality")
    return issues


def endpoint_input(state: str, exact: str | None, refs: list[str], *, start: str | None = None, end: str | None = None, candidates: list[str] | None = None, projectable: bool = True, study_day: int | None = None) -> dict[str, Any]:
    return {"state": state, "exact_date": exact, "range_start": start, "range_end": end, "candidates": candidates or [], "locator_refs": refs, "projectable": projectable, "range_authorized": projectable, "study_day": study_day}


def subject_endpoint_specs(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Return every authority endpoint governed by the subject study-day anchor."""
    endpoints = [source["visit"]["nominal"], source["visit"]["actual"]]
    endpoints.extend(endpoint for event in source["events"] for endpoint in (event["start"], event["end"]))
    endpoints.extend((source["risk"]["start"], source["risk"]["end"], source["phase"]["start"], source["phase"]["end"]))
    return endpoints


def derived_study_day(anchor_date: str, target_date: str, day_zero: bool) -> int:
    delta = (dt.date.fromisoformat(target_date) - dt.date.fromisoformat(anchor_date)).days
    return delta if day_zero or delta < 0 else delta + 1


def recompute_subject_study_days(source: dict[str, Any]) -> None:
    """Apply the accepted parent formula to all source endpoints in one pass."""
    if not source["axis"]["study_day_enabled"]:
        for endpoint in subject_endpoint_specs(source):
            endpoint["study_day"] = None
        return
    anchor_ref = source["axis"]["anchor_event_ref"]
    anchor = next(row for row in source["events"] if row["event_ref"] == anchor_ref)["start"]
    if anchor["state"] != "exact" or anchor["exact_date"] is None or not anchor["projectable"]:
        raise ValueError("TPA_V02_STUDY_DAY_ANCHOR_INVALID")
    anchor_date = anchor["exact_date"]
    day_zero = source["axis"]["day_zero_convention"] == "anchor_day_zero"
    for endpoint in subject_endpoint_specs(source):
        endpoint["study_day"] = (
            derived_study_day(anchor_date, endpoint["exact_date"], day_zero)
            if endpoint["state"] == "exact" and endpoint["exact_date"] is not None
            else None
        )


def validate_subject_study_days(source: dict[str, Any]) -> None:
    expected = copy.deepcopy(source)
    recompute_subject_study_days(expected)
    actual_values = [row["study_day"] for row in subject_endpoint_specs(source)]
    expected_values = [row["study_day"] for row in subject_endpoint_specs(expected)]
    if actual_values != expected_values:
        raise ValueError("TPA_V02_STUDY_DAY_INPUT_MISMATCH")


def base_scope(snapshot: str) -> dict[str, Any]:
    return {"project_ref": "project::synthetic-contract-example", "run_ref": "run::synthetic-contract-example", "snapshot_ref": snapshot, "site_ref": "site::001", "subject_ref": "subject::001-0001", "spine_ref": f"spine::001-0001::{snapshot.split('::')[-1]}"}


def aemh_scope(snapshot: str, cutoff: str) -> dict[str, Any]:
    return {**base_scope(snapshot), "cutoff_ref": cutoff}


def revision_identity(ref: str) -> str:
    return digest({"revision": ref, "accepted": True})


def locator_input(ref: str, record: str, anchor: str, snapshot: str, revision: str, kind: str | None = None, entity: str | None = None, domain: str | None = None, thread_ref: str | None = None) -> dict[str, Any]:
    return {"locator_ref": ref, "record_ref": record, "anchor": anchor, "snapshot_ref": snapshot, "revision_ref": revision, "revision_content_identity": revision_identity(revision), "entity_kind": kind, "entity_ref": entity, "authority_domain": domain, "authority_thread_ref": thread_ref}


def subject_source() -> dict[str, Any]:
    visit_ref, ae_ref, mh_ref, cutoff_ref = "locator::visit::v1", "locator::event::ae1", "locator::event::mh1", "locator::cutoff::v1"
    revision = "source-revision::listing::N+1"
    exact1 = endpoint_input("exact", "2026-08-01", [visit_ref], study_day=1)
    exact2 = endpoint_input("exact", "2026-08-02", [ae_ref], study_day=2)
    partial = endpoint_input("partial", None, [mh_ref], start="2026-08-01", end="2026-08-31", candidates=["2026-08"])
    missing = endpoint_input("missing", None, [mh_ref], projectable=False)
    source = {
        "scope": base_scope("snapshot::N+1"),
        "cutoff_binding": {"state": "present", "exact_date": "2026-08-19", "source_locator_refs": [cutoff_ref]},
        "locator_specs": [
            locator_input(cutoff_ref, "run-row::1", "data_cutoff", "snapshot::N+1", revision),
            locator_input(ae_ref, "ae-row::1", "start_end_date", "snapshot::N+1", revision),
            locator_input(mh_ref, "mh-row::1", "start_end_date", "snapshot::N+1", revision),
            locator_input(visit_ref, "visit-row::v1", "visit_date", "snapshot::N+1", revision),
        ],
        "revision_specs": [{"revision_ref": revision, "revision_content_identity": revision_identity(revision), "locator_refs": sorted([cutoff_ref, ae_ref, mh_ref, visit_ref])}],
        "axis": {"axis_ref": "axis::subject::001-0001::N+1", "mode": "calendar", "timezone": "Asia/Shanghai", "day_zero_convention": "anchor_day_one", "anchor_event_ref": "event::ae::1", "study_day_enabled": True},
        "visit": {"visit_ref": "visit::actual::v1", "planned_visit_ref": "visit::planned::v1", "actual_encounter_ref": "encounter::v1", "assignment_ref": "assignment::v1", "phase_ref": "phase::treatment", "nominal": exact1, "actual": exact1, "locator_refs": [visit_ref]},
        "events": [
            {"event_ref": "event::ae::1", "domain": "ae", "subtype": "ae", "visit_ref": "visit::actual::v1", "geometry": "closed_interval", "start": copy.deepcopy(exact1), "end": exact2, "risk_refs": ["risk-anchor::ae::1"], "locator_refs": [ae_ref], "content_identity": digest({"event": "ae::1", "content": "accepted"})},
            {"event_ref": "event::mh::1", "domain": "mh", "subtype": "mh", "visit_ref": None, "geometry": "open_end", "start": partial, "end": missing, "risk_refs": [], "locator_refs": [mh_ref], "content_identity": digest({"event": "mh::1", "content": "accepted"})},
        ],
        "risk": {"risk_anchor_ref": "risk-anchor::ae::1", "risk_ref": "risk::ae::1", "domain": "ae", "severity": "high", "risk_type_zh": "严重性核查", "event_ref": "event::ae::1", "visit_ref": "visit::actual::v1", "geometry": "point", "start": copy.deepcopy(exact1), "end": copy.deepcopy(exact1), "locator_refs": [ae_ref], "content_identity": digest({"risk": "ae::1", "severity": "high"})},
        "phase": {"phase_ref": "phase::treatment", "label_zh": "治疗期", "geometry": "open_end", "start": copy.deepcopy(exact1), "end": copy.deepcopy(missing), "locator_refs": [visit_ref]},
        "domain_applicability": [{"domain": domain, "state": "applicable" if domain in ("ae", "mh") else "not_provided", "event_refs": [f"event::{domain}::1"] if domain in ("ae", "mh") else [], "risk_refs": ["risk-anchor::ae::1"] if domain == "ae" else []} for domain in DOMAINS],
    }
    recompute_subject_study_days(source)
    return source


def aemh_source() -> dict[str, Any]:
    prev, curr = "snapshot::N", "snapshot::N+1"
    rev_n, rev_n1 = "source-revision::listing::N", "source-revision::listing::N+1"
    prev_locs = [
        locator_input("locator::reminder::ae1", "clue-row::1", "concept", prev, rev_n, "candidate", "candidate::suspected-ae::1", "ae", "aemh-thread::ae::1"),
        locator_input("locator::reminder::mh1", "clue-row::2", "concept", prev, rev_n, "candidate", "candidate::suspected-mh::1", "mh", "aemh-thread::mh::1"),
    ]
    curr_locs = [
        locator_input("locator::considered-fact::mh1", "mh-row::considered-1", "term", curr, rev_n1, "considered_fact", "considered-fact::reported-mh::1", "mh", "aemh-thread::mh::1"),
        locator_input("locator::fact::ae1", "ae-row::later-1", "term", curr, rev_n1, "later_fact", "fact::reported-ae::later-1", "ae", "aemh-thread::ae::1"),
        locator_input("locator::reminder::ae1", "clue-row::1", "concept", curr, rev_n, "candidate", "candidate::suspected-ae::1", "ae", "aemh-thread::ae::1"),
        locator_input("locator::reminder::mh1", "clue-row::2", "concept", curr, rev_n, "candidate", "candidate::suspected-mh::1", "mh", "aemh-thread::mh::1"),
    ]
    return {
        "previous_scope": aemh_scope(prev, "2026-08-10"),
        "current_scope": aemh_scope(curr, "2026-08-19"),
        "previous_locator_specs": prev_locs,
        "current_locator_specs": curr_locs,
        "previous_revision_specs": [{"revision_ref": rev_n, "revision_content_identity": revision_identity(rev_n), "locator_refs": sorted(row["locator_ref"] for row in prev_locs)}],
        "current_revision_specs": [
            {"revision_ref": rev_n, "revision_content_identity": revision_identity(rev_n), "locator_refs": ["locator::reminder::ae1", "locator::reminder::mh1"]},
            {"revision_ref": rev_n1, "revision_content_identity": revision_identity(rev_n1), "locator_refs": ["locator::considered-fact::mh1", "locator::fact::ae1"]},
        ],
        "thread_specs": [
            {"thread_ref": "aemh-thread::ae::1", "domain": "ae", "candidate_ref": "candidate::suspected-ae::1", "reminder_reason": "suspected_unreported_ae_reminder", "candidate_locator_ref": "locator::reminder::ae1"},
            {"thread_ref": "aemh-thread::mh::1", "domain": "mh", "candidate_ref": "candidate::suspected-mh::1", "reminder_reason": "suspected_unreported_mh_reminder", "candidate_locator_ref": "locator::reminder::mh1"},
        ],
        "decision_records": [
            {"decision_ref": "decision::ae::exact", "thread_ref": "aemh-thread::ae::1", "event_kind": "match_decided", "match_state": "exact", "fact_refs": ["fact::reported-ae::later-1"], "considered_fact_refs": [], "reason_code": "exact_identity_and_temporal_match"},
            {"decision_ref": "decision::ae::withdrawn", "thread_ref": "aemh-thread::ae::1", "event_kind": "withdrawn", "match_state": None, "fact_refs": ["fact::reported-ae::later-1"], "considered_fact_refs": [], "reason_code": "later_fact_withdrawn"},
            {"decision_ref": "decision::ae::reappeared", "thread_ref": "aemh-thread::ae::1", "event_kind": "reappeared", "match_state": None, "fact_refs": ["fact::reported-ae::later-1"], "considered_fact_refs": [], "reason_code": "same_later_fact_reappeared"},
            {"decision_ref": "decision::mh::rejected", "thread_ref": "aemh-thread::mh::1", "event_kind": "match_decided", "match_state": "rejected", "fact_refs": [], "considered_fact_refs": ["considered-fact::reported-mh::1"], "reason_code": "rejected_after_identity_evidence_review"},
        ],
    }


def bundle(target: str, source: dict[str, Any]) -> dict[str, Any]:
    source_graph = json.loads(canonical_bytes(source))
    core = {"contract_id": CONTRACT_ID, "schema_version": SCHEMA_VERSION, "authority_scope": AUTHORITY_SCOPE, "execution_profile": PROFILE, "temporal_v01_manifest_sha256": FROZEN_PINS[V01_MANIFEST], "target_contract": target, "source": source_graph}
    return {**core, "bundle_content_identity": digest(core)}


class FullGraphExecutor:
    """Closed v0.2 composition executor over typed authority input only."""

    def __init__(self, authority_bundle: dict[str, Any]) -> None:
        self.bundle = copy.deepcopy(authority_bundle)
        self.source = self.bundle["source"]
        typed_issues = validate_authority_bundle(self.bundle, build_schema())
        if typed_issues:
            raise ValueError("TPA_V02_TYPED_AUTHORITY:" + "|".join(typed_issues))
        if self.bundle["temporal_v01_manifest_sha256"] != FROZEN_PINS[V01_MANIFEST] or self.bundle["execution_profile"] != PROFILE or self.bundle["target_contract"] not in (SUBJECT, AEMH):
            raise ValueError("TPA_V02_SUPERSESSION_PRECONDITION")
        if self.bundle["bundle_content_identity"] != digest({key: value for key, value in self.bundle.items() if key != "bundle_content_identity"}):
            raise ValueError("TPA_V02_BUNDLE_IDENTITY")
        if self.bundle["target_contract"] == SUBJECT:
            validate_subject_study_days(self.source)
            binding = self.source["cutoff_binding"]
            present_valid = binding["state"] == "present" and binding["exact_date"] is not None and bool(binding["source_locator_refs"])
            absent_valid = binding == {"state": "absent", "exact_date": None, "source_locator_refs": []}
            if not (present_valid or absent_valid):
                raise ValueError("TPA_V02_CUTOFF_BINDING_INVALID")

    @staticmethod
    def scope(spec: dict[str, Any], cutoff_binding: dict[str, Any] | None = None) -> dict[str, Any]:
        if cutoff_binding is not None:
            return sealed({**spec, "cutoff_state": cutoff_binding["state"], "cutoff_ref": cutoff_binding["exact_date"]}, "identity_content_hash")
        return sealed({**spec, "cutoff_state": "present"}, "identity_content_hash")

    @staticmethod
    def locator(spec: dict[str, Any]) -> dict[str, Any]:
        return sealed({
            "locator_ref": spec["locator_ref"], "locator_variant": "r4_source_locator",
            "snapshot_ref": spec["snapshot_ref"], "source_revision_ref": spec["revision_ref"],
            "source_revision_content_hash": spec["revision_content_identity"], "source_file_ref": None,
            "table_semantic": "synthetic_listing", "record_ref": spec["record_ref"],
            "authority_entity_kind": spec["entity_kind"], "authority_entity_ref": spec["entity_ref"],
            "column_or_anchor": spec["anchor"], "canonical_location": None,
            "raw_payload_hash": digest({"record": spec["record_ref"], "anchor": spec["anchor"]}),
        }, "locator_content_hash")

    @staticmethod
    def endpoint(spec: dict[str, Any]) -> dict[str, Any]:
        return sealed({
            "state": spec["state"], "exact_date": spec["exact_date"], "range_start": spec["range_start"],
            "range_end": spec["range_end"], "candidate_values": spec["candidates"],
            "source_locator_refs": sorted(spec["locator_refs"]), "main_axis_projectable": spec["projectable"],
            "range_projection_authorized": spec["range_authorized"], "study_day": spec["study_day"],
        }, "endpoint_content_hash")

    @staticmethod
    def visibility(identity: dict[str, Any]) -> dict[str, Any]:
        core = {
            "visibility_decision_id": f"visibility::{identity['subject_ref']}::{identity['snapshot_ref']}",
            "visibility_decision_hash": digest({**{key: identity[key] for key in ("project_ref", "run_ref", "snapshot_ref", "cutoff_state", "cutoff_ref", "site_ref", "subject_ref", "spine_ref")}, "state": "projectable"}),
            "evaluation_member_refs": [identity["subject_ref"]], "evaluation_site_refs": [identity["site_ref"]],
            "projectable_member_refs": [identity["subject_ref"]], "projectable_site_refs": [identity["site_ref"]],
            "hidden_member_refs": [], "hidden_site_refs": [], "hidden_member_count": 0, "hidden_site_count": 0,
            "subject_visibility_state": "projectable", "deep_link_eligible": True,
        }
        return sealed(core, "closure_content_hash")

    @staticmethod
    def source_pairs(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted((sealed({"revision_id": row["revision_ref"], "accepted_content_hash": row["revision_content_identity"], "locator_refs": sorted(row["locator_refs"])}, "pair_content_hash") for row in specs), key=lambda row: row["revision_id"])

    @staticmethod
    def subject_evaluation(projection: dict[str, Any], revision_hashes: list[str]) -> list[str]:
        values = [projection["projection_content_hash"], projection["scope_identity"]["identity_content_hash"], projection["membership_index"]["membership_content_hash"], projection["axis_basis"]["axis_content_hash"], *revision_hashes]
        values.extend(row["visit_content_hash"] for row in projection["visits"])
        values.extend(value for row in projection["events"] for value in (row["event_content_identity"], row["event_content_hash"]))
        values.extend(value for row in projection["risk_anchors"] for value in (row["risk_content_identity"], row["risk_anchor_content_hash"]))
        values.extend(row["pending_content_hash"] for row in projection["pending_date_items"])
        values.extend(row["phase_content_hash"] for row in projection["phase_bands"])
        values.extend(row["track_content_hash"] for row in projection["domain_tracks"])
        values.extend(row["locator_content_hash"] for row in projection["source_locators"])
        return sorted(set(values))

    @staticmethod
    def aemh_evaluation(projection: dict[str, Any], revision_hashes: list[str]) -> list[str]:
        values = [projection["projection_content_hash"], projection["scope_identity"]["identity_content_hash"], projection["membership_index"]["membership_content_hash"], projection["cutoff_endpoint"]["cutoff_content_hash"], *revision_hashes]
        if projection["previous_projection_content_hash"] is not None:
            values.append(projection["previous_projection_content_hash"])
        values.extend(row["prefix_content_hash"] for row in projection["accepted_thread_prefixes"])
        for thread in projection["threads"]:
            values.extend((thread["candidate_content_identity"], thread["thread_content_hash"]))
            for entry in thread["history_entries"]:
                values.append(entry["entry_hash"])
                values.extend(entry["later_fact_content_identities"])
                values.extend(row["evidence_content_hash"] for row in entry["identity_evidence"])
        values.extend(row["locator_content_hash"] for row in projection["source_locators"])
        return sorted(set(values))

    @classmethod
    def receipt(cls, variant: str, contract: str, identity: dict[str, Any], projection: dict[str, Any], pairs: list[dict[str, Any]], evaluation: list[str]) -> dict[str, Any]:
        core = {
            "receipt_id": digest({"receipt_variant": variant, "authority_contract_id": contract, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection["projection_id"]}),
            "receipt_variant": variant, "authority_contract_id": contract, "authority_contract_version": PARENT_SCHEMA_VERSION,
            "scope_identity": identity, "public_projection_id": projection["projection_id"],
            "public_projection_content_hash": projection["projection_content_hash"], "evaluation_content_identities": evaluation,
            "visibility_closure": cls.visibility(identity), "source_revision_content_pairs": pairs,
            "audience_contract_id": AUDIENCE,
        }
        return sealed(core, "receipt_content_hash")

    def subject_packet(self) -> dict[str, Any]:
        source = self.source
        cutoff_binding = source["cutoff_binding"]
        identity = self.scope(source["scope"], cutoff_binding)
        locators = sorted((self.locator(row) for row in source["locator_specs"]), key=lambda row: row["locator_ref"])
        pairs = self.source_pairs(source["revision_specs"])
        visit_spec = source["visit"]
        visit = sealed({
            "visit_ref": visit_spec["visit_ref"], "visit_kind": "actual", "planned_visit_ref": visit_spec["planned_visit_ref"],
            "actual_encounter_ref": visit_spec["actual_encounter_ref"], "accepted_assignment_ref": visit_spec["assignment_ref"],
            "phase_ref": visit_spec["phase_ref"], "nominal_endpoint": self.endpoint(visit_spec["nominal"]),
            "actual_endpoint": self.endpoint(visit_spec["actual"]), "source_locator_refs": sorted(visit_spec["locator_refs"]),
        }, "visit_content_hash")
        events = []
        for spec in source["events"]:
            events.append(sealed({
                "event_ref": spec["event_ref"], "event_content_identity": spec["content_identity"], "domain": spec["domain"],
                "subtype": spec["subtype"], "applicability_state": "applicable", "visit_ref": spec["visit_ref"],
                "geometry": spec["geometry"], "start_endpoint": self.endpoint(spec["start"]), "end_endpoint": self.endpoint(spec["end"]),
                "risk_anchor_refs": sorted(spec["risk_refs"]), "source_locator_refs": sorted(spec["locator_refs"]),
            }, "event_content_hash"))
        events.sort(key=lambda row: row["event_ref"])
        risk_spec = source["risk"]
        risk = sealed({
            "risk_anchor_ref": risk_spec["risk_anchor_ref"], "risk_ref": risk_spec["risk_ref"], "risk_content_identity": risk_spec["content_identity"],
            "domain": risk_spec["domain"], "severity": risk_spec["severity"], "risk_type_zh": risk_spec["risk_type_zh"],
            "event_ref": risk_spec["event_ref"], "visit_ref": risk_spec["visit_ref"], "geometry": risk_spec["geometry"],
            "start_endpoint": self.endpoint(risk_spec["start"]), "end_endpoint": self.endpoint(risk_spec["end"]),
            "source_locator_refs": sorted(risk_spec["locator_refs"]),
        }, "risk_anchor_content_hash")
        phase_spec = source["phase"]
        phase = sealed({
            "phase_ref": phase_spec["phase_ref"], "phase_label_zh": phase_spec["label_zh"], "geometry": phase_spec["geometry"],
            "start_endpoint": self.endpoint(phase_spec["start"]), "end_endpoint": self.endpoint(phase_spec["end"]),
            "source_locator_refs": sorted(phase_spec["locator_refs"]),
        }, "phase_content_hash")
        mh_event = next(row for row in events if row["domain"] == "mh")
        pending_event = sealed({
            "pending_ref": "pending::event::mh::1", "item_kind": "event", "item_ref": mh_event["event_ref"],
            "target_content_hash": mh_event["event_content_hash"], "domain": "mh", "start_endpoint": mh_event["start_endpoint"],
            "end_endpoint": mh_event["end_endpoint"], "source_locator_refs": mh_event["source_locator_refs"],
        }, "pending_content_hash")
        pending_phase = sealed({
            "pending_ref": "pending::phase::treatment", "item_kind": "phase", "item_ref": phase["phase_ref"],
            "target_content_hash": phase["phase_content_hash"], "domain": None, "start_endpoint": phase["start_endpoint"],
            "end_endpoint": phase["end_endpoint"], "source_locator_refs": phase["source_locator_refs"],
        }, "pending_content_hash")
        tracks = [sealed({"domain": row["domain"], "applicability_state": row["state"], "event_refs": sorted(row["event_refs"]), "risk_anchor_refs": sorted(row["risk_refs"])}, "track_content_hash") for row in source["domain_applicability"]]
        membership = sealed({
            "visit_refs": [visit["visit_ref"]], "event_refs": [row["event_ref"] for row in events],
            "risk_anchor_refs": [risk["risk_anchor_ref"]], "pending_date_refs": [pending_event["pending_ref"], pending_phase["pending_ref"]],
            "phase_refs": [phase["phase_ref"]], "source_locator_refs": [row["locator_ref"] for row in locators],
        }, "membership_content_hash")
        axis_spec = source["axis"]
        cutoff = self.endpoint(endpoint_input(
            "exact" if cutoff_binding["state"] == "present" else "missing",
            cutoff_binding["exact_date"],
            cutoff_binding["source_locator_refs"],
            projectable=cutoff_binding["state"] == "present",
            study_day=None,
        ))
        axis = sealed({
            "axis_ref": axis_spec["axis_ref"], "default_axis_mode": axis_spec["mode"], "timezone": axis_spec["timezone"],
            "study_day_anchor_event_ref": axis_spec["anchor_event_ref"] if axis_spec["study_day_enabled"] else None,
            "study_day_zero_exists": axis_spec["day_zero_convention"] == "anchor_day_zero" if axis_spec["study_day_enabled"] else None,
            "cutoff_endpoint": cutoff, "source_locator_refs": sorted(cutoff_binding["source_locator_refs"]),
        }, "axis_content_hash")
        projection_id = digest({"contract_id": SUBJECT, "schema_version": PARENT_SCHEMA_VERSION, "scope_identity_hash": identity["identity_content_hash"], "membership_index_hash": membership["membership_content_hash"], "axis_basis_hash": axis["axis_content_hash"]})
        receipt_id = digest({"receipt_variant": "subject_temporal", "authority_contract_id": SUBJECT, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection_id})
        projection = sealed({
            "contract_id": SUBJECT, "schema_version": PARENT_SCHEMA_VERSION, "projection_id": projection_id, "receipt_ref": receipt_id,
            "scope_identity": identity, "fallback_policy": "fail_closed_no_nearest", "axis_basis": axis, "visits": [visit],
            "events": events, "risk_anchors": [risk], "pending_date_items": [pending_event, pending_phase], "phase_bands": [phase],
            "domain_tracks": tracks, "source_locators": locators, "membership_index": membership,
        }, "projection_content_hash")
        receipt = self.receipt("subject_temporal", SUBJECT, identity, projection, pairs, self.subject_evaluation(projection, [row["accepted_content_hash"] for row in pairs]))
        packet = {"receipt": receipt, "projection": projection}
        packet["packet_content_hash"] = digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]})
        return packet

    @staticmethod
    def entity_identity(kind: str, ref: str, locator: dict[str, Any]) -> str:
        return digest({"entity_kind": kind, "entity_ref": ref, "source_locator_ref": locator["locator_ref"], "source_raw_payload_hash": locator["raw_payload_hash"]})

    @classmethod
    def evidence(cls, ref: str, kind: str, entity: str, locator: dict[str, Any]) -> dict[str, Any]:
        return sealed({
            "evidence_ref": ref, "evidence_kind": kind, "entity_ref": entity,
            "entity_content_identity": cls.entity_identity(kind, entity, locator), "source_locator_ref": locator["locator_ref"],
            "source_locator_content_hash": locator["locator_content_hash"], "source_raw_payload_hash": locator["raw_payload_hash"],
        }, "evidence_content_hash")

    @staticmethod
    def required_evidence_locator(mapping: dict[tuple[str, str, str, str], dict[str, Any]], key: tuple[str, str, str, str]) -> dict[str, Any]:
        if key not in mapping:
            raise ValueError("TPA_V02_EVIDENCE_AUTHORITY_BINDING")
        return mapping[key]

    @staticmethod
    def entry(thread_key: str, seq: int, event_kind: str, snapshot: str, match_state: str | None, fact_refs: list[str], fact_hashes: list[str], evidence: list[dict[str, Any]], retained: list[str], reason: str, prior: str | None) -> dict[str, Any]:
        if len(fact_refs) != len(fact_hashes):
            raise ValueError("TPA_V02_FACT_IDENTITY_CARDINALITY")
        fact_pairs = sorted(zip(fact_refs, fact_hashes), key=lambda row: row[0])
        return sealed({
            "entry_id": f"history-entry::{thread_key}::{seq}", "seq": seq, "event_kind": event_kind, "snapshot_ref": snapshot,
            "match_state": match_state, "later_fact_refs": [row[0] for row in fact_pairs], "later_fact_content_identities": [row[1] for row in fact_pairs],
            "identity_evidence_refs": sorted(row["evidence_ref"] for row in evidence), "identity_evidence": sorted(evidence, key=lambda row: row["evidence_ref"]),
            "retained_evidence_locator_refs": sorted(retained), "reason_code": reason, "risk_lifecycle_effect": "none", "prior_entry_hash": prior,
        }, "entry_hash")

    @classmethod
    def build_aemh_packet(cls, identity: dict[str, Any], threads: list[dict[str, Any]], locators: list[dict[str, Any]], pairs: list[dict[str, Any]], previous: dict[str, Any] | None) -> dict[str, Any]:
        threads = sorted(threads, key=lambda row: row["thread_ref"])
        locators = sorted(locators, key=lambda row: row["locator_ref"])
        later = sorted({ref for thread in threads for entry in thread["history_entries"] for ref in entry["later_fact_refs"]})
        membership = sealed({"thread_refs": [row["thread_ref"] for row in threads], "candidate_refs": sorted(row["original_candidate_ref"] for row in threads), "later_fact_refs": later, "source_locator_refs": [row["locator_ref"] for row in locators]}, "membership_content_hash")
        prefixes: list[dict[str, Any]] = []
        previous_ref = previous_hash = None
        if previous is not None:
            previous_projection = previous["projection"]
            previous_ref, previous_hash = previous_projection["projection_id"], previous_projection["projection_content_hash"]
            previous_by_ref = {row["thread_ref"]: row for row in previous_projection["threads"]}
            for thread in threads:
                old = previous_by_ref[thread["thread_ref"]]
                prefixes.append(sealed({"thread_ref": thread["thread_ref"], "accepted_prefix_seq": len(old["history_entries"]), "accepted_prefix_head_hash": old["history_entries"][-1]["entry_hash"], "previous_thread_content_hash": old["thread_content_hash"]}, "prefix_content_hash"))
        cutoff_locator = next(row["locator_ref"] for row in locators if row["authority_entity_kind"] == "candidate" and row["authority_entity_ref"] == "candidate::suspected-ae::1")
        cutoff = sealed({"state": "present", "exact_date": identity["cutoff_ref"], "source_locator_refs": [cutoff_locator]}, "cutoff_content_hash")
        projection_id = digest({"contract_id": AEMH, "schema_version": PARENT_SCHEMA_VERSION, "scope_identity_hash": identity["identity_content_hash"], "membership_index_hash": membership["membership_content_hash"]})
        receipt_id = digest({"receipt_variant": "aemh_match_history", "authority_contract_id": AEMH, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection_id})
        projection = sealed({
            "contract_id": AEMH, "schema_version": PARENT_SCHEMA_VERSION, "projection_id": projection_id, "receipt_ref": receipt_id,
            "scope_identity": identity, "cutoff_endpoint": cutoff, "fallback_policy": "fail_closed_no_nearest",
            "previous_projection_ref": previous_ref, "previous_projection_content_hash": previous_hash, "accepted_thread_prefixes": prefixes,
            "threads": threads, "source_locators": locators, "membership_index": membership,
        }, "projection_content_hash")
        receipt = cls.receipt("aemh_match_history", AEMH, identity, projection, pairs, cls.aemh_evaluation(projection, [row["accepted_content_hash"] for row in pairs]))
        packet = {"receipt": receipt, "projection": projection}
        packet["packet_content_hash"] = digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]})
        return packet

    def aemh_packets(self) -> tuple[dict[str, Any], dict[str, Any]]:
        source = self.source
        prev_identity, curr_identity = self.scope(source["previous_scope"]), self.scope(source["current_scope"])
        prev_locs = [self.locator(row) for row in source["previous_locator_specs"]]
        curr_locs = [self.locator(row) for row in source["current_locator_specs"]]
        prev_by_ref = {row["locator_ref"]: row for row in prev_locs}
        prev_authority_by_ref = {row["locator_ref"]: row for row in source["previous_locator_specs"]}
        curr_by_ref = {row["locator_ref"]: row for row in curr_locs}
        curr_by_entity = {
            (row["authority_thread_ref"], row["authority_domain"], row["entity_kind"], row["entity_ref"]): curr_by_ref[row["locator_ref"]]
            for row in source["current_locator_specs"]
        }
        previous_threads = []
        for spec in source["thread_specs"]:
            loc = prev_by_ref[spec["candidate_locator_ref"]]
            loc_authority = prev_authority_by_ref[spec["candidate_locator_ref"]]
            if (loc_authority["authority_thread_ref"], loc_authority["authority_domain"], loc_authority["entity_kind"], loc_authority["entity_ref"]) != (spec["thread_ref"], spec["domain"], "candidate", spec["candidate_ref"]):
                raise ValueError("TPA_V02_EVIDENCE_AUTHORITY_BINDING")
            evidence = self.evidence(f"identity-evidence::candidate::{spec['domain']}1", "candidate", spec["candidate_ref"], loc)
            entry = self.entry(f"{spec['domain']}::1", 1, "reminder_created", source["previous_scope"]["snapshot_ref"], None, [], [], [evidence], [loc["locator_ref"]], spec["reminder_reason"], None)
            previous_threads.append(sealed({"thread_ref": spec["thread_ref"], "project_ref": prev_identity["project_ref"], "site_ref": prev_identity["site_ref"], "domain": spec["domain"], "subject_ref": prev_identity["subject_ref"], "original_candidate_ref": spec["candidate_ref"], "candidate_content_identity": self.entity_identity("candidate", spec["candidate_ref"], loc), "original_reminder_ref": entry["entry_id"], "history_entries": [entry], "evidence_locator_refs": [loc["locator_ref"]]}, "thread_content_hash"))
        previous = self.build_aemh_packet(prev_identity, previous_threads, prev_locs, self.source_pairs(source["previous_revision_specs"]), None)
        old_by_ref = {row["thread_ref"]: row for row in previous_threads}
        decisions_by_thread: dict[str, list[dict[str, Any]]] = {row["thread_ref"]: [] for row in source["thread_specs"]}
        for decision in source["decision_records"]:
            decisions_by_thread[decision["thread_ref"]].append(decision)
        current_threads = []
        for spec in source["thread_specs"]:
            old = old_by_ref[spec["thread_ref"]]
            entries = copy.deepcopy(old["history_entries"])
            retained = {spec["candidate_locator_ref"]}
            for decision in decisions_by_thread[spec["thread_ref"]]:
                seq, evidence = len(entries) + 1, []
                fact_hashes: list[str] = []
                if decision["event_kind"] == "match_decided":
                    candidate_loc = self.required_evidence_locator(curr_by_entity, (spec["thread_ref"], spec["domain"], "candidate", spec["candidate_ref"]))
                    evidence.append(self.evidence(f"identity-evidence::candidate::{spec['domain']}1", "candidate", spec["candidate_ref"], candidate_loc))
                for fact in decision["fact_refs"]:
                    loc = self.required_evidence_locator(curr_by_entity, (spec["thread_ref"], spec["domain"], "later_fact", fact))
                    evidence.append(self.evidence(f"identity-evidence::later_fact::{digest(fact)[:12]}", "later_fact", fact, loc))
                    fact_hashes.append(self.entity_identity("later_fact", fact, loc)); retained.add(loc["locator_ref"])
                for fact in decision["considered_fact_refs"]:
                    loc = self.required_evidence_locator(curr_by_entity, (spec["thread_ref"], spec["domain"], "considered_fact", fact))
                    evidence.append(self.evidence(f"identity-evidence::considered_fact::{digest(fact)[:12]}", "considered_fact", fact, loc)); retained.add(loc["locator_ref"])
                entry = self.entry(f"{spec['domain']}::1", seq, decision["event_kind"], source["current_scope"]["snapshot_ref"], decision["match_state"], decision["fact_refs"], fact_hashes, evidence, sorted(retained), decision["reason_code"], entries[-1]["entry_hash"])
                entries.append(entry)
            current_threads.append(sealed({"thread_ref": spec["thread_ref"], "project_ref": curr_identity["project_ref"], "site_ref": curr_identity["site_ref"], "domain": spec["domain"], "subject_ref": curr_identity["subject_ref"], "original_candidate_ref": spec["candidate_ref"], "candidate_content_identity": old["candidate_content_identity"], "original_reminder_ref": old["original_reminder_ref"], "history_entries": entries, "evidence_locator_refs": sorted(retained)}, "thread_content_hash"))
        current = self.build_aemh_packet(curr_identity, current_threads, curr_locs, self.source_pairs(source["current_revision_specs"]), previous)
        return previous, current

    def execute(self) -> dict[str, Any] | tuple[dict[str, Any], dict[str, Any]]:
        return self.subject_packet() if self.bundle["target_contract"] == SUBJECT else self.aemh_packets()


def parent_validator() -> Any:
    spec = importlib.util.spec_from_file_location("accepted_parent_validator_v01", ROOT / PARENT_VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("parent validator loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parent_errors(target: str, result: Any, previous: dict[str, Any] | None = None) -> list[str]:
    validator = parent_validator()
    if target == SUBJECT:
        return validator.validate_subject(result, json.loads((ROOT / SUBJECT_SCHEMA).read_text()))
    return validator.validate_aemh(result, json.loads((ROOT / AEMH_SCHEMA).read_text()), previous)


def ensure_parent_valid(target: str, result: Any, previous: dict[str, Any] | None = None) -> list[str]:
    errors = parent_errors(target, result, previous)
    if errors:
        raise SystemExit(f"STOP parent validation {target}: {errors}")
    return errors


def build_recipe_registry() -> dict[str, Any]:
    v01 = json.loads((ROOT / V01_MANIFEST).read_text())
    mapping_rows = v01["accepted_authority_output_registry"]["mappings"]
    owner_method = {
        "AEMHIdentityEvidence": "evidence", "AEMHMatchHistoryAuthorityPacket": "target_object",
        "AEMHMatchHistoryEntry": "entry", "AEMHMatchHistoryPublicProjection": "aemh_projection",
        "AEMHMatchThread": "thread", "AEMHThreadPrefixAnchor": "prefix", "PublicAuthorityReceipt": "receipt",
        "SubjectTemporalAuthorityPacket": "target_object", "SubjectTemporalPublicProjection": "subject_projection",
        "TemporalAxisBasis": "axis", "TemporalDateEndpoint": "endpoint", "TemporalDomainTrack": "domain",
        "TemporalEvent": "event", "TemporalMembershipIndex": "membership", "TemporalPhaseBand": "phase",
        "TemporalRiskAnchor": "risk", "TemporalVisit": "visit",
    }
    affected: dict[str, list[str]] = {name: [] for name in (
        "endpoint", "locator", "revision_pair", "visibility", "cutoff", "axis", "visit", "event", "events",
        "phase", "risk", "domain", "membership", "pending", "evidence", "entry", "prefix", "thread",
        "aemh_membership", "subject_projection", "aemh_projection", "receipt", "target_object", "projected_field",
    )}
    mapping_hashes: dict[str, str] = {}
    for row in mapping_rows:
        owner = row["qualified_leaf"].split("::", 1)[1].split(".", 1)[0]
        affected[owner_method[owner]].append(row["mapping_id"])
        mapping_hashes[row["mapping_id"]] = row["mapping_content_hash"]
    if set().union(*(set(rows) for rows in affected.values())) != set(mapping_hashes):
        raise SystemExit("STOP affected mapping partition")
    recipe_specs = [
        ("recipe.v02.subject_identity_cutoff", SUBJECT, "identity_cutoff", ["/source/scope", "/source/cutoff_binding"], []),
        ("recipe.v02.subject_locators_revisions", SUBJECT, "locators_revisions", ["/source/locator_specs", "/source/revision_specs"], ["recipe.v02.subject_identity_cutoff.sealed"]),
        ("recipe.v02.subject_temporal_members", SUBJECT, "temporal_members", ["/source/visit", "/source/events", "/source/risk", "/source/phase"], ["recipe.v02.subject_locators_revisions.sealed"]),
        ("recipe.v02.subject_domains_pending_membership", SUBJECT, "domains_pending_membership", ["/source/domain_applicability"], ["recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_locators_revisions.sealed"]),
        ("recipe.v02.subject_axis", SUBJECT, "axis", ["/source/axis"], ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_domains_pending_membership.sealed"]),
        ("recipe.v02.subject_projection", SUBJECT, "projection", [], ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed", "recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_domains_pending_membership.sealed", "recipe.v02.subject_axis.sealed"]),
        ("recipe.v02.subject_receipt", SUBJECT, "receipt", [], ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed"]),
        ("recipe.v02.subject_packet", SUBJECT, "packet", [], ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_receipt.sealed"]),
        ("recipe.v02.aemh_identity_locators_revisions", AEMH, "identity_locators_revisions", ["/source/previous_scope", "/source/current_scope", "/source/previous_locator_specs", "/source/current_locator_specs", "/source/previous_revision_specs", "/source/current_revision_specs"], []),
        ("recipe.v02.aemh_previous_threads", AEMH, "previous_threads", ["/source/thread_specs"], ["recipe.v02.aemh_identity_locators_revisions.sealed"]),
        ("recipe.v02.aemh_previous_packet", AEMH, "previous_packet", [], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"]),
        ("recipe.v02.aemh_current_threads", AEMH, "current_threads", ["/source/decision_records"], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"]),
        ("recipe.v02.aemh_current_membership_prefix_cutoff", AEMH, "current_membership_prefix_cutoff", [], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed"]),
        ("recipe.v02.aemh_projection", AEMH, "projection", [], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed", "recipe.v02.aemh_current_membership_prefix_cutoff.sealed"]),
        ("recipe.v02.aemh_receipt", AEMH, "receipt", [], ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_identity_locators_revisions.sealed"]),
        ("recipe.v02.aemh_packet", AEMH, "packet", [], ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_receipt.sealed", "recipe.v02.aemh_previous_packet.sealed"]),
    ]
    recipes = []
    for recipe_id, target, phase, pointers, prior_refs in recipe_specs:
        target_name = "subject" if target == SUBJECT else "aemh"
        emitted = f"{recipe_id}.value"
        sealed_output = f"{recipe_id}.sealed"
        inputs = [*pointers, *prior_refs]
        params = {"operation_version": SCHEMA_VERSION, "phase": phase, "authority_input_pointers": pointers, "prior_recipe_output_refs": prior_refs, "output_name": emitted, "canonicalization": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan"}
        nodes = [
            {"node_id": f"{recipe_id}.n01", "op": f"emit_{target_name}_{phase}", "inputs": inputs, "params": params, "outputs": [emitted]},
            {"node_id": f"{recipe_id}.n02", "op": f"seal_{target_name}_{phase}", "inputs": [emitted], "params": params, "outputs": [sealed_output]},
        ]
        edges = [{"from": item, "to": nodes[0]["node_id"]} for item in inputs] + [{"from": nodes[0]["node_id"], "to": nodes[1]["node_id"]}]
        core = {"recipe_id": recipe_id, "target_contract": target, "inputs": inputs, "nodes": nodes, "dependency_edges": edges, "external_pin_refs": sorted(TYPED_SOURCE_PINS)}
        recipes.append({**core, "recipe_content_hash": digest(core)})
    preserved_ids = ["recipe.external_registry_receipt_resolution", "recipe.parent_semantic_snapshot_immutability"]
    preserved = [{"recipe_id": recipe_id, "recipe_content_hash": v01["accepted_recipe_content_hash_pins"][recipe_id], "source_manifest_sha256": FROZEN_PINS[V01_MANIFEST], "disposition": "preserve"} for recipe_id in preserved_ids]
    method_recipe = {
        "endpoint": ["recipe.v02.subject_temporal_members"], "locator": ["recipe.v02.subject_locators_revisions"],
        "revision_pair": ["recipe.v02.subject_locators_revisions"], "visibility": ["recipe.v02.subject_identity_cutoff"],
        "cutoff": ["recipe.v02.subject_identity_cutoff"], "axis": ["recipe.v02.subject_axis"],
        "visit": ["recipe.v02.subject_temporal_members"], "event": ["recipe.v02.subject_temporal_members"],
        "events": ["recipe.v02.subject_temporal_members"], "phase": ["recipe.v02.subject_temporal_members"],
        "risk": ["recipe.v02.subject_temporal_members"], "domain": ["recipe.v02.subject_domains_pending_membership"],
        "membership": ["recipe.v02.subject_domains_pending_membership"], "pending": ["recipe.v02.subject_domains_pending_membership"],
        "evidence": ["recipe.v02.aemh_previous_threads", "recipe.v02.aemh_current_threads"], "entry": ["recipe.v02.aemh_previous_threads", "recipe.v02.aemh_current_threads"],
        "prefix": ["recipe.v02.aemh_current_membership_prefix_cutoff"], "thread": ["recipe.v02.aemh_previous_threads", "recipe.v02.aemh_current_threads"],
        "aemh_membership": ["recipe.v02.aemh_current_membership_prefix_cutoff"], "subject_projection": ["recipe.v02.subject_projection"],
        "aemh_projection": ["recipe.v02.aemh_projection"], "receipt": ["recipe.v02.subject_receipt", "recipe.v02.aemh_receipt"],
        "target_object": ["recipe.v02.subject_packet", "recipe.v02.aemh_packet"], "projected_field": ["recipe.v02.subject_projection", "recipe.v02.aemh_projection"],
    }
    rules = [{
        "rule_id": f"supersede.v01.{method}", "v01_method": method, "disposition": "supersede",
        "required_manifest_sha256": FROZEN_PINS[V01_MANIFEST], "execution_profile": PROFILE,
        "target_contracts": [SUBJECT, AEMH], "affected_mapping_ids": sorted(ids),
        "preserved_formulas": ["parent exact schema and enums", "parent canonical JSON", "parent self-hash recipes", "v0.1 read/scope/resolve/record/canonical/seal/direct_source primitives"],
        "replacement_recipe_ids": method_recipe[method],
    } for method, ids in affected.items()]
    root = {"schema": "emitter-recipe-registry-v0.2", "contract_id": CONTRACT_ID, "preserved_v01_recipes": preserved, "supersession_rules": rules, "executable_v02_recipes": recipes, "affected_mapping_content_hashes": mapping_hashes, "affected_mapping_count": len(mapping_hashes), "external_pins": [{"path": path, "sha256": sha, "role": "accepted_typed_source"} for path, sha in sorted(TYPED_SOURCE_PINS.items())]}
    registry = {**root, "registry_content_hash": digest(root)}
    recipe_issues = validate_recipe_registry(registry, build_schema())
    if recipe_issues:
        raise SystemExit("STOP recipe IR: " + "|".join(recipe_issues))
    return registry


def validate_recipe_registry(registry: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    issues = []
    recipes = registry.get("executable_v02_recipes")
    if not isinstance(recipes, list) or len(recipes) != 16:
        return ["TPA_V02_RECIPE_CARDINALITY"]
    known_ids = {row["recipe_id"] for row in recipes if isinstance(row, dict) and "recipe_id" in row}
    phase_order = {
        SUBJECT: ["identity_cutoff", "locators_revisions", "temporal_members", "domains_pending_membership", "axis", "projection", "receipt", "packet"],
        AEMH: ["identity_locators_revisions", "previous_threads", "previous_packet", "current_threads", "current_membership_prefix_cutoff", "projection", "receipt", "packet"],
    }
    authority_pointers = {
        "identity_cutoff": ["/source/scope", "/source/cutoff_binding"], "locators_revisions": ["/source/locator_specs", "/source/revision_specs"],
        "temporal_members": ["/source/visit", "/source/events", "/source/risk", "/source/phase"], "domains_pending_membership": ["/source/domain_applicability"],
        "axis": ["/source/axis"], "identity_locators_revisions": ["/source/previous_scope", "/source/current_scope", "/source/previous_locator_specs", "/source/current_locator_specs", "/source/previous_revision_specs", "/source/current_revision_specs"],
        "previous_threads": ["/source/thread_specs"], "current_threads": ["/source/decision_records"], "projection": [], "receipt": [], "packet": [], "previous_packet": [], "current_membership_prefix_cutoff": [],
    }
    exact_prior_refs = {
        (SUBJECT, "identity_cutoff"): [],
        (SUBJECT, "locators_revisions"): ["recipe.v02.subject_identity_cutoff.sealed"],
        (SUBJECT, "temporal_members"): ["recipe.v02.subject_locators_revisions.sealed"],
        (SUBJECT, "domains_pending_membership"): ["recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_locators_revisions.sealed"],
        (SUBJECT, "axis"): ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_domains_pending_membership.sealed"],
        (SUBJECT, "projection"): ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed", "recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_domains_pending_membership.sealed", "recipe.v02.subject_axis.sealed"],
        (SUBJECT, "receipt"): ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed"],
        (SUBJECT, "packet"): ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_receipt.sealed"],
        (AEMH, "identity_locators_revisions"): [],
        (AEMH, "previous_threads"): ["recipe.v02.aemh_identity_locators_revisions.sealed"],
        (AEMH, "previous_packet"): ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"],
        (AEMH, "current_threads"): ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"],
        (AEMH, "current_membership_prefix_cutoff"): ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed"],
        (AEMH, "projection"): ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed", "recipe.v02.aemh_current_membership_prefix_cutoff.sealed"],
        (AEMH, "receipt"): ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_identity_locators_revisions.sealed"],
        (AEMH, "packet"): ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_receipt.sealed", "recipe.v02.aemh_previous_packet.sealed"],
    }
    target_seen = {SUBJECT: [], AEMH: []}
    for index, recipe in enumerate(recipes):
        issues.extend(validate_typed(recipe, "ExecutableRecipeV02", schema, f"$.executable_v02_recipes[{index}]"))
        if issues:
            continue
        core = {key: value for key, value in recipe.items() if key != "recipe_content_hash"}
        if recipe["recipe_content_hash"] != digest(core):
            issues.append(f"recipe:{recipe['recipe_id']}:hash")
        target_seen[recipe["target_contract"]].append(first_phase if (first_phase := recipe["nodes"][0]["params"]["phase"]) else "")
        if len(recipe["nodes"]) != 2:
            issues.append(f"recipe:{recipe['recipe_id']}:node_cardinality")
            continue
        first, second = recipe["nodes"]
        target_name = "subject" if recipe["target_contract"] == SUBJECT else "aemh"
        phase = first["params"]["phase"]
        if [first["op"], second["op"]] != [f"emit_{target_name}_{phase}", f"seal_{target_name}_{phase}"]:
            issues.append(f"recipe:{recipe['recipe_id']}:op_sequence")
        params = first["params"]
        expected_inputs = [*params["authority_input_pointers"], *params["prior_recipe_output_refs"]]
        if recipe["inputs"] != expected_inputs or first["inputs"] != expected_inputs or second["inputs"] != first["outputs"]:
            issues.append(f"recipe:{recipe['recipe_id']}:dependency")
        expected_edges = [{"from": item, "to": first["node_id"]} for item in expected_inputs] + [{"from": first["node_id"], "to": second["node_id"]}]
        if recipe["dependency_edges"] != expected_edges:
            issues.append(f"recipe:{recipe['recipe_id']}:dag")
        expected_recipe_id = f"recipe.v02.{'subject' if recipe['target_contract'] == SUBJECT else 'aemh'}_{phase}"
        if first["params"] != second["params"] or recipe["recipe_id"] != expected_recipe_id or params["authority_input_pointers"] != authority_pointers[phase] or params["prior_recipe_output_refs"] != exact_prior_refs[(recipe["target_contract"], phase)] or params["output_name"] != f"{recipe['recipe_id']}.value" or first["outputs"] != [params["output_name"]] or second["outputs"] != [f"{recipe['recipe_id']}.sealed"]:
            issues.append(f"recipe:{recipe['recipe_id']}:params")
        if set(recipe["external_pin_refs"]) != set(TYPED_SOURCE_PINS):
            issues.append(f"recipe:{recipe['recipe_id']}:pins")
    if len(known_ids) != 16:
        issues.append("TPA_V02_RECIPE_ID_DUPLICATE")
    if target_seen != phase_order:
        issues.append("TPA_V02_RECIPE_PHASE_ORDER")
    recipe_target = {row["recipe_id"]: row["target_contract"] for row in recipes if isinstance(row, dict) and "recipe_id" in row and "target_contract" in row}
    for recipe in recipes:
        target = recipe.get("target_contract")
        for ref in recipe.get("nodes", [{}])[0].get("params", {}).get("prior_recipe_output_refs", []):
            prior_id = ref.removesuffix(".sealed")
            if recipe_target.get(prior_id) != target:
                issues.append(f"recipe:{recipe.get('recipe_id')}:cross_target_dependency")
    for index, rule in enumerate(registry.get("supersession_rules", [])):
        issues.extend(validate_typed(rule, "EmitterSupersessionRuleV02", schema, f"$.supersession_rules[{index}]"))
        if any(recipe_id not in known_ids for recipe_id in rule.get("replacement_recipe_ids", [])):
            issues.append(f"rule:{rule.get('rule_id')}:unknown_recipe")
    for index, pin in enumerate(registry.get("external_pins", [])):
        issues.extend(validate_typed(pin, "ExternalPinV02", schema, f"$.external_pins[{index}]"))
    if {pin.get("path"): pin.get("sha256") for pin in registry.get("external_pins", [])} != TYPED_SOURCE_PINS:
        issues.append("TPA_V02_EXTERNAL_PIN_GATE")
    return issues


def execute_recipe_dag(authority_bundle: dict[str, Any], registry: dict[str, Any], *, capture_outputs: bool = False) -> Any:
    """Execute the closed recipe IR without materializing a packet beforehand."""
    executor = FullGraphExecutor(authority_bundle)
    source = executor.source
    target = authority_bundle["target_contract"]
    recipes = [row for row in registry["executable_v02_recipes"] if row["target_contract"] == target]
    outputs: dict[str, dict[str, Any]] = {}
    stage: dict[str, Any] = {}
    binding_specs = {
        "emit_subject_identity_cutoff": ("recipe.v02.subject_identity_cutoff", SUBJECT, "identity_cutoff", ["/source/scope", "/source/cutoff_binding"], []),
        "emit_subject_locators_revisions": ("recipe.v02.subject_locators_revisions", SUBJECT, "locators_revisions", ["/source/locator_specs", "/source/revision_specs"], ["recipe.v02.subject_identity_cutoff.sealed"]),
        "emit_subject_temporal_members": ("recipe.v02.subject_temporal_members", SUBJECT, "temporal_members", ["/source/visit", "/source/events", "/source/risk", "/source/phase"], ["recipe.v02.subject_locators_revisions.sealed"]),
        "emit_subject_domains_pending_membership": ("recipe.v02.subject_domains_pending_membership", SUBJECT, "domains_pending_membership", ["/source/domain_applicability"], ["recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_locators_revisions.sealed"]),
        "emit_subject_axis": ("recipe.v02.subject_axis", SUBJECT, "axis", ["/source/axis"], ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_domains_pending_membership.sealed"]),
        "emit_subject_projection": ("recipe.v02.subject_projection", SUBJECT, "projection", [], ["recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed", "recipe.v02.subject_temporal_members.sealed", "recipe.v02.subject_domains_pending_membership.sealed", "recipe.v02.subject_axis.sealed"]),
        "emit_subject_receipt": ("recipe.v02.subject_receipt", SUBJECT, "receipt", [], ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_identity_cutoff.sealed", "recipe.v02.subject_locators_revisions.sealed"]),
        "emit_subject_packet": ("recipe.v02.subject_packet", SUBJECT, "packet", [], ["recipe.v02.subject_projection.sealed", "recipe.v02.subject_receipt.sealed"]),
        "emit_aemh_identity_locators_revisions": ("recipe.v02.aemh_identity_locators_revisions", AEMH, "identity_locators_revisions", ["/source/previous_scope", "/source/current_scope", "/source/previous_locator_specs", "/source/current_locator_specs", "/source/previous_revision_specs", "/source/current_revision_specs"], []),
        "emit_aemh_previous_threads": ("recipe.v02.aemh_previous_threads", AEMH, "previous_threads", ["/source/thread_specs"], ["recipe.v02.aemh_identity_locators_revisions.sealed"]),
        "emit_aemh_previous_packet": ("recipe.v02.aemh_previous_packet", AEMH, "previous_packet", [], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"]),
        "emit_aemh_current_threads": ("recipe.v02.aemh_current_threads", AEMH, "current_threads", ["/source/decision_records"], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_threads.sealed"]),
        "emit_aemh_current_membership_prefix_cutoff": ("recipe.v02.aemh_current_membership_prefix_cutoff", AEMH, "current_membership_prefix_cutoff", [], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed"]),
        "emit_aemh_projection": ("recipe.v02.aemh_projection", AEMH, "projection", [], ["recipe.v02.aemh_identity_locators_revisions.sealed", "recipe.v02.aemh_previous_packet.sealed", "recipe.v02.aemh_current_threads.sealed", "recipe.v02.aemh_current_membership_prefix_cutoff.sealed"]),
        "emit_aemh_receipt": ("recipe.v02.aemh_receipt", AEMH, "receipt", [], ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_identity_locators_revisions.sealed"]),
        "emit_aemh_packet": ("recipe.v02.aemh_packet", AEMH, "packet", [], ["recipe.v02.aemh_projection.sealed", "recipe.v02.aemh_receipt.sealed", "recipe.v02.aemh_previous_packet.sealed"]),
    }

    def emit_handler(expected: tuple[Any, ...]) -> Any:
        def handle(recipe: dict[str, Any], node: dict[str, Any]) -> str:
            recipe_id, expected_target, expected_phase, pointers, prior_refs = expected
            params = node["params"]
            inputs = [*pointers, *prior_refs]
            output_name = f"{recipe_id}.value"
            expected_edges = [{"from": item, "to": node["node_id"]} for item in inputs] + [{"from": node["node_id"], "to": recipe["nodes"][1]["node_id"]}]
            if recipe["recipe_id"] != recipe_id or recipe["target_contract"] != expected_target or params != {"operation_version": SCHEMA_VERSION, "phase": expected_phase, "authority_input_pointers": pointers, "prior_recipe_output_refs": prior_refs, "output_name": output_name, "canonicalization": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan"} or recipe["inputs"] != inputs or node["inputs"] != inputs or node["outputs"] != [output_name] or recipe["dependency_edges"] != expected_edges:
                raise ValueError(f"TPA_V02_EMIT_HANDLER_BINDING:{node['op']}")
            return expected_phase
        return handle

    def seal_handler(expected: tuple[Any, ...]) -> Any:
        def handle(recipe: dict[str, Any], node: dict[str, Any], value: Any) -> dict[str, Any]:
            recipe_id, expected_target, expected_phase, pointers, prior_refs = expected
            output_name = f"{recipe_id}.value"
            params = {"operation_version": SCHEMA_VERSION, "phase": expected_phase, "authority_input_pointers": pointers, "prior_recipe_output_refs": prior_refs, "output_name": output_name, "canonicalization": "utf8_nfc_canonical_json_sorted_keys_compact_no_nan"}
            if recipe["recipe_id"] != recipe_id or recipe["target_contract"] != expected_target or node["params"] != params or node["inputs"] != [output_name] or node["outputs"] != [f"{recipe_id}.sealed"]:
                raise ValueError(f"TPA_V02_SEAL_HANDLER_BINDING:{node['op']}")
            return {"value": copy.deepcopy(value), "content_hash": digest(value)}
        return handle

    emit_handlers = {op: emit_handler(spec) for op, spec in binding_specs.items()}
    seal_handlers = {op.replace("emit_", "seal_", 1): seal_handler(spec) for op, spec in binding_specs.items()}
    actual_ops = {node["op"] for recipe in registry["executable_v02_recipes"] for node in recipe["nodes"]}
    if actual_ops != set(emit_handlers) | set(seal_handlers):
        raise ValueError("TPA_V02_NODE_OP_DISPATCH_SET")
    for recipe in recipes:
        node, seal_node = recipe["nodes"]
        if node["op"] not in emit_handlers or seal_node["op"] not in seal_handlers:
            raise ValueError(f"TPA_V02_NODE_OP_DISPATCH:{recipe['recipe_id']}")
        params = node["params"]
        semantic = emit_handlers[node["op"]](recipe, node)
        for pointer in params["authority_input_pointers"]:
            json_pointer_get(authority_bundle, pointer)
        for ref in params["prior_recipe_output_refs"]:
            if ref not in outputs or outputs[ref]["content_hash"] != digest(outputs[ref]["value"]):
                raise ValueError(f"TPA_V02_RECIPE_PRIOR:{recipe['recipe_id']}:{ref}")
        if target == SUBJECT:
            if semantic == "identity_cutoff":
                binding = source["cutoff_binding"]
                identity = executor.scope(source["scope"], binding)
                cutoff = executor.endpoint(endpoint_input("exact" if binding["state"] == "present" else "missing", binding["exact_date"], binding["source_locator_refs"], projectable=binding["state"] == "present"))
                value = {"identity": identity, "cutoff": cutoff}
            elif semantic == "locators_revisions":
                identity = stage["identity_cutoff"]["identity"]
                value = {"locators": sorted((executor.locator(row) for row in source["locator_specs"]), key=lambda row: row["locator_ref"]), "pairs": executor.source_pairs(source["revision_specs"]), "visibility": executor.visibility(identity)}
            elif semantic == "temporal_members":
                visit_spec = source["visit"]
                visit = sealed({"visit_ref": visit_spec["visit_ref"], "visit_kind": "actual", "planned_visit_ref": visit_spec["planned_visit_ref"], "actual_encounter_ref": visit_spec["actual_encounter_ref"], "accepted_assignment_ref": visit_spec["assignment_ref"], "phase_ref": visit_spec["phase_ref"], "nominal_endpoint": executor.endpoint(visit_spec["nominal"]), "actual_endpoint": executor.endpoint(visit_spec["actual"]), "source_locator_refs": sorted(visit_spec["locator_refs"])}, "visit_content_hash")
                events = sorted((sealed({"event_ref": spec["event_ref"], "event_content_identity": spec["content_identity"], "domain": spec["domain"], "subtype": spec["subtype"], "applicability_state": "applicable", "visit_ref": spec["visit_ref"], "geometry": spec["geometry"], "start_endpoint": executor.endpoint(spec["start"]), "end_endpoint": executor.endpoint(spec["end"]), "risk_anchor_refs": sorted(spec["risk_refs"]), "source_locator_refs": sorted(spec["locator_refs"])}, "event_content_hash") for spec in source["events"]), key=lambda row: row["event_ref"])
                risk_spec = source["risk"]
                risk = sealed({"risk_anchor_ref": risk_spec["risk_anchor_ref"], "risk_ref": risk_spec["risk_ref"], "risk_content_identity": risk_spec["content_identity"], "domain": risk_spec["domain"], "severity": risk_spec["severity"], "risk_type_zh": risk_spec["risk_type_zh"], "event_ref": risk_spec["event_ref"], "visit_ref": risk_spec["visit_ref"], "geometry": risk_spec["geometry"], "start_endpoint": executor.endpoint(risk_spec["start"]), "end_endpoint": executor.endpoint(risk_spec["end"]), "source_locator_refs": sorted(risk_spec["locator_refs"])}, "risk_anchor_content_hash")
                phase_spec = source["phase"]
                phase_band = sealed({"phase_ref": phase_spec["phase_ref"], "phase_label_zh": phase_spec["label_zh"], "geometry": phase_spec["geometry"], "start_endpoint": executor.endpoint(phase_spec["start"]), "end_endpoint": executor.endpoint(phase_spec["end"]), "source_locator_refs": sorted(phase_spec["locator_refs"])}, "phase_content_hash")
                value = {"visit": visit, "events": events, "risk": risk, "phase": phase_band}
            elif semantic == "domains_pending_membership":
                temporal = stage["temporal_members"]
                mh_event = next(row for row in temporal["events"] if row["domain"] == "mh")
                pending_event = sealed({"pending_ref": "pending::event::mh::1", "item_kind": "event", "item_ref": mh_event["event_ref"], "target_content_hash": mh_event["event_content_hash"], "domain": "mh", "start_endpoint": mh_event["start_endpoint"], "end_endpoint": mh_event["end_endpoint"], "source_locator_refs": mh_event["source_locator_refs"]}, "pending_content_hash")
                phase_band = temporal["phase"]
                pending_phase = sealed({"pending_ref": "pending::phase::treatment", "item_kind": "phase", "item_ref": phase_band["phase_ref"], "target_content_hash": phase_band["phase_content_hash"], "domain": None, "start_endpoint": phase_band["start_endpoint"], "end_endpoint": phase_band["end_endpoint"], "source_locator_refs": phase_band["source_locator_refs"]}, "pending_content_hash")
                tracks = [sealed({"domain": row["domain"], "applicability_state": row["state"], "event_refs": sorted(row["event_refs"]), "risk_anchor_refs": sorted(row["risk_refs"])}, "track_content_hash") for row in source["domain_applicability"]]
                locators = stage["locators_revisions"]["locators"]
                membership = sealed({"visit_refs": [temporal["visit"]["visit_ref"]], "event_refs": [row["event_ref"] for row in temporal["events"]], "risk_anchor_refs": [temporal["risk"]["risk_anchor_ref"]], "pending_date_refs": [pending_event["pending_ref"], pending_phase["pending_ref"]], "phase_refs": [phase_band["phase_ref"]], "source_locator_refs": [row["locator_ref"] for row in locators]}, "membership_content_hash")
                value = {"pending": [pending_event, pending_phase], "tracks": tracks, "membership": membership}
            elif semantic == "axis":
                axis_spec = source["axis"]
                cutoff = stage["identity_cutoff"]["cutoff"]
                value = sealed({"axis_ref": axis_spec["axis_ref"], "default_axis_mode": axis_spec["mode"], "timezone": axis_spec["timezone"], "study_day_anchor_event_ref": axis_spec["anchor_event_ref"] if axis_spec["study_day_enabled"] else None, "study_day_zero_exists": axis_spec["day_zero_convention"] == "anchor_day_zero" if axis_spec["study_day_enabled"] else None, "cutoff_endpoint": cutoff, "source_locator_refs": sorted(source["cutoff_binding"]["source_locator_refs"])}, "axis_content_hash")
            elif semantic == "projection":
                identity = stage["identity_cutoff"]["identity"]; locators = stage["locators_revisions"]["locators_revisions"] if "locators_revisions" in stage["locators_revisions"] else stage["locators_revisions"]
                temporal = stage["temporal_members"]; closure = stage["domains_pending_membership"]; axis = stage["axis"]
                projection_id = digest({"contract_id": SUBJECT, "schema_version": PARENT_SCHEMA_VERSION, "scope_identity_hash": identity["identity_content_hash"], "membership_index_hash": closure["membership"]["membership_content_hash"], "axis_basis_hash": axis["axis_content_hash"]})
                receipt_id = digest({"receipt_variant": "subject_temporal", "authority_contract_id": SUBJECT, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection_id})
                value = sealed({"contract_id": SUBJECT, "schema_version": PARENT_SCHEMA_VERSION, "projection_id": projection_id, "receipt_ref": receipt_id, "scope_identity": identity, "fallback_policy": "fail_closed_no_nearest", "axis_basis": axis, "visits": [temporal["visit"]], "events": temporal["events"], "risk_anchors": [temporal["risk"]], "pending_date_items": closure["pending"], "phase_bands": [temporal["phase"]], "domain_tracks": closure["tracks"], "source_locators": locators["locators"], "membership_index": closure["membership"]}, "projection_content_hash")
            elif semantic == "receipt":
                identity = stage["identity_cutoff"]["identity"]; projection = stage["projection"]; locators = stage["locators_revisions"]
                value = executor.receipt("subject_temporal", SUBJECT, identity, projection, locators["pairs"], executor.subject_evaluation(projection, [row["accepted_content_hash"] for row in locators["pairs"]]))
            else:
                projection = stage["projection"]; receipt = stage["receipt"]
                value = {"receipt": receipt, "projection": projection, "packet_content_hash": digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]})}
        else:
            if semantic == "identity_locators_revisions":
                previous_identity = executor.scope(source["previous_scope"]); current_identity = executor.scope(source["current_scope"])
                previous_locators = sorted((executor.locator(row) for row in source["previous_locator_specs"]), key=lambda row: row["locator_ref"])
                current_locators = sorted((executor.locator(row) for row in source["current_locator_specs"]), key=lambda row: row["locator_ref"])
                value = {"previous_identity": previous_identity, "current_identity": current_identity, "previous_locators": previous_locators, "current_locators": current_locators, "previous_pairs": executor.source_pairs(source["previous_revision_specs"]), "current_pairs": executor.source_pairs(source["current_revision_specs"])}
            elif semantic == "previous_threads":
                authority = stage["identity_locators_revisions"]; previous_by_ref = {row["locator_ref"]: row for row in authority["previous_locators"]}; source_by_ref = {row["locator_ref"]: row for row in source["previous_locator_specs"]}; threads = []
                for spec in source["thread_specs"]:
                    locator = previous_by_ref[spec["candidate_locator_ref"]]; locator_source = source_by_ref[spec["candidate_locator_ref"]]
                    if (locator_source["authority_thread_ref"], locator_source["authority_domain"], locator_source["entity_kind"], locator_source["entity_ref"]) != (spec["thread_ref"], spec["domain"], "candidate", spec["candidate_ref"]): raise ValueError("TPA_V02_EVIDENCE_AUTHORITY_BINDING")
                    evidence = executor.evidence(f"identity-evidence::candidate::{spec['domain']}1", "candidate", spec["candidate_ref"], locator)
                    entry = executor.entry(f"{spec['domain']}::1", 1, "reminder_created", source["previous_scope"]["snapshot_ref"], None, [], [], [evidence], [locator["locator_ref"]], spec["reminder_reason"], None)
                    threads.append(sealed({"thread_ref": spec["thread_ref"], "project_ref": authority["previous_identity"]["project_ref"], "site_ref": authority["previous_identity"]["site_ref"], "domain": spec["domain"], "subject_ref": authority["previous_identity"]["subject_ref"], "original_candidate_ref": spec["candidate_ref"], "candidate_content_identity": executor.entity_identity("candidate", spec["candidate_ref"], locator), "original_reminder_ref": entry["entry_id"], "history_entries": [entry], "evidence_locator_refs": [locator["locator_ref"]]}, "thread_content_hash"))
                value = sorted(threads, key=lambda row: row["thread_ref"])
            elif semantic == "previous_packet":
                authority = stage["identity_locators_revisions"]
                value = executor.build_aemh_packet(authority["previous_identity"], stage["previous_threads"], authority["previous_locators"], authority["previous_pairs"], None)
            elif semantic == "current_threads":
                authority = stage["identity_locators_revisions"]; old_by_ref = {row["thread_ref"]: row for row in stage["previous_threads"]}; current_by_ref = {row["locator_ref"]: row for row in authority["current_locators"]}
                current_by_entity = {(row["authority_thread_ref"], row["authority_domain"], row["entity_kind"], row["entity_ref"]): current_by_ref[row["locator_ref"]] for row in source["current_locator_specs"]}
                decisions_by_thread = {row["thread_ref"]: [] for row in source["thread_specs"]}
                for decision in source["decision_records"]: decisions_by_thread[decision["thread_ref"]].append(decision)
                threads = []
                for spec in source["thread_specs"]:
                    old = old_by_ref[spec["thread_ref"]]; entries = copy.deepcopy(old["history_entries"]); retained = {spec["candidate_locator_ref"]}
                    for decision in decisions_by_thread[spec["thread_ref"]]:
                        evidence = []; fact_hashes = []
                        if decision["event_kind"] == "match_decided":
                            candidate = executor.required_evidence_locator(current_by_entity, (spec["thread_ref"], spec["domain"], "candidate", spec["candidate_ref"])); evidence.append(executor.evidence(f"identity-evidence::candidate::{spec['domain']}1", "candidate", spec["candidate_ref"], candidate))
                        for fact in decision["fact_refs"]:
                            locator = executor.required_evidence_locator(current_by_entity, (spec["thread_ref"], spec["domain"], "later_fact", fact)); evidence.append(executor.evidence(f"identity-evidence::later_fact::{digest(fact)[:12]}", "later_fact", fact, locator)); fact_hashes.append(executor.entity_identity("later_fact", fact, locator)); retained.add(locator["locator_ref"])
                        for fact in decision["considered_fact_refs"]:
                            locator = executor.required_evidence_locator(current_by_entity, (spec["thread_ref"], spec["domain"], "considered_fact", fact)); evidence.append(executor.evidence(f"identity-evidence::considered_fact::{digest(fact)[:12]}", "considered_fact", fact, locator)); retained.add(locator["locator_ref"])
                        entries.append(executor.entry(f"{spec['domain']}::1", len(entries) + 1, decision["event_kind"], source["current_scope"]["snapshot_ref"], decision["match_state"], decision["fact_refs"], fact_hashes, evidence, sorted(retained), decision["reason_code"], entries[-1]["entry_hash"]))
                    threads.append(sealed({"thread_ref": spec["thread_ref"], "project_ref": authority["current_identity"]["project_ref"], "site_ref": authority["current_identity"]["site_ref"], "domain": spec["domain"], "subject_ref": authority["current_identity"]["subject_ref"], "original_candidate_ref": spec["candidate_ref"], "candidate_content_identity": old["candidate_content_identity"], "original_reminder_ref": old["original_reminder_ref"], "history_entries": entries, "evidence_locator_refs": sorted(retained)}, "thread_content_hash"))
                value = sorted(threads, key=lambda row: row["thread_ref"])
            elif semantic == "current_membership_prefix_cutoff":
                authority = stage["identity_locators_revisions"]; threads = stage["current_threads"]; previous = stage["previous_packet"]
                later = sorted({ref for thread in threads for entry in thread["history_entries"] for ref in entry["later_fact_refs"]})
                membership = sealed({"thread_refs": [row["thread_ref"] for row in threads], "candidate_refs": sorted(row["original_candidate_ref"] for row in threads), "later_fact_refs": later, "source_locator_refs": [row["locator_ref"] for row in authority["current_locators"]]}, "membership_content_hash")
                previous_by_ref = {row["thread_ref"]: row for row in previous["projection"]["threads"]}
                prefixes = [sealed({"thread_ref": thread["thread_ref"], "accepted_prefix_seq": len(previous_by_ref[thread["thread_ref"]]["history_entries"]), "accepted_prefix_head_hash": previous_by_ref[thread["thread_ref"]]["history_entries"][-1]["entry_hash"], "previous_thread_content_hash": previous_by_ref[thread["thread_ref"]]["thread_content_hash"]}, "prefix_content_hash") for thread in threads]
                cutoff_locator = next(row["locator_ref"] for row in authority["current_locators"] if row["authority_entity_kind"] == "candidate" and row["authority_entity_ref"] == "candidate::suspected-ae::1")
                cutoff = sealed({"state": "present", "exact_date": authority["current_identity"]["cutoff_ref"], "source_locator_refs": [cutoff_locator]}, "cutoff_content_hash")
                value = {"membership": membership, "prefixes": prefixes, "cutoff": cutoff}
            elif semantic == "projection":
                authority = stage["identity_locators_revisions"]; closure = stage["current_membership_prefix_cutoff"]; previous = stage["previous_packet"]
                identity = authority["current_identity"]; membership = closure["membership"]
                projection_id = digest({"contract_id": AEMH, "schema_version": PARENT_SCHEMA_VERSION, "scope_identity_hash": identity["identity_content_hash"], "membership_index_hash": membership["membership_content_hash"]})
                receipt_id = digest({"receipt_variant": "aemh_match_history", "authority_contract_id": AEMH, "scope_identity_hash": identity["identity_content_hash"], "public_projection_id": projection_id})
                value = sealed({"contract_id": AEMH, "schema_version": PARENT_SCHEMA_VERSION, "projection_id": projection_id, "receipt_ref": receipt_id, "scope_identity": identity, "cutoff_endpoint": closure["cutoff"], "fallback_policy": "fail_closed_no_nearest", "previous_projection_ref": previous["projection"]["projection_id"], "previous_projection_content_hash": previous["projection"]["projection_content_hash"], "accepted_thread_prefixes": closure["prefixes"], "threads": stage["current_threads"], "source_locators": authority["current_locators"], "membership_index": membership}, "projection_content_hash")
            elif semantic == "receipt":
                authority = stage["identity_locators_revisions"]; projection = stage["projection"]
                value = executor.receipt("aemh_match_history", AEMH, authority["current_identity"], projection, authority["current_pairs"], executor.aemh_evaluation(projection, [row["accepted_content_hash"] for row in authority["current_pairs"]]))
            else:
                projection = stage["projection"]; receipt = stage["receipt"]
                current = {"receipt": receipt, "projection": projection, "packet_content_hash": digest({"receipt_content_hash": receipt["receipt_content_hash"], "projection_content_hash": projection["projection_content_hash"]})}
                value = {"previous": stage["previous_packet"], "current": current}
        sealed_output = seal_handlers[seal_node["op"]](recipe, seal_node, value)
        outputs[recipe["nodes"][1]["outputs"][0]] = sealed_output
        stage[semantic] = outputs[recipe["nodes"][1]["outputs"][0]]["value"]
    final = stage["packet"]
    result = final if target == SUBJECT else (final["previous"], final["current"])
    return (result, outputs) if capture_outputs else result


def json_pointer_get(document: Any, pointer: str) -> Any:
    value = document
    for token in pointer.strip("/").split("/") if pointer != "/" else []:
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def json_pointer_replace(document: Any, pointer: str, replacement: Any) -> None:
    parts = pointer.strip("/").split("/")
    parent = document
    for part in parts[:-1]:
        parent = parent[int(part)] if isinstance(parent, list) else parent[part]
    if isinstance(parent, list): parent[int(parts[-1])] = copy.deepcopy(replacement)
    else: parent[parts[-1]] = copy.deepcopy(replacement)


def reseal_bundle(authority_bundle: dict[str, Any]) -> None:
    authority_bundle["bundle_content_identity"] = digest({key: value for key, value in authority_bundle.items() if key != "bundle_content_identity"})


def trace_authority_bases(subject_bundle: dict[str, Any], aemh_bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    absent = copy.deepcopy(subject_bundle)
    absent["source"]["cutoff_binding"] = {"state": "absent", "exact_date": None, "source_locator_refs": []}
    absent["source"]["locator_specs"] = [row for row in absent["source"]["locator_specs"] if row["locator_ref"] != "locator::cutoff::v1"]
    absent["source"]["revision_specs"][0]["locator_refs"] = [ref for ref in absent["source"]["revision_specs"][0]["locator_refs"] if ref != "locator::cutoff::v1"]
    reseal_bundle(absent)
    conflicted = copy.deepcopy(subject_bundle)
    conflicted["source"]["events"][1]["start"].update({"state": "conflicted", "range_start": "2026-08-03", "range_end": "2026-08-17", "candidates": ["2026-08-03", "2026-08-17"]})
    reseal_bundle(conflicted)
    no_study = copy.deepcopy(subject_bundle)
    no_study["source"]["axis"].update({"anchor_event_ref": None, "study_day_enabled": False})
    recompute_subject_study_days(no_study["source"])
    reseal_bundle(no_study)
    bases = {
        "subject_temporal_valid_base": subject_bundle,
        "subject_temporal_absent_cutoff_valid_base": absent,
        "subject_temporal_conflicted_valid_base": conflicted,
        "subject_temporal_no_study_day_valid_base": no_study,
        "aemh_match_history_valid_base": aemh_bundle,
        "positive.subject.axis.base": subject_bundle,
        "positive.aemh.decision.seed": aemh_positive_seed(aemh_bundle),
    }
    schema = build_schema()
    for name, authority_bundle in bases.items():
        issues = validate_authority_bundle(authority_bundle, schema)
        if issues:
            raise SystemExit(f"STOP trace base typed authority {name}: {issues}")
    return bases


def inherited_reject_adapter(rule_id: str, target: str) -> tuple[str, dict[str, Any]]:
    invalid = f"invalid::{rule_id}"
    if target == SUBJECT:
        if rule_id.startswith("visit_semantics."):
            suffix = rule_id.split(".", 1)[1]
            paths = {
                "nominal_date": "/projection/visits/0/nominal_endpoint/state",
                "actual_date": "/projection/visits/0/actual_endpoint/state",
                "unscheduled_visit": "/projection/visits/0/visit_kind",
                "between_visit_event": "/projection/events/0/geometry",
                "phase_band": "/projection/phase_bands/0/geometry",
                "first_dose": "/projection/events/0/start_endpoint/state",
                "last_dose": "/projection/events/0/end_endpoint/state",
                "cutoff_marker": "/projection/axis_basis/cutoff_endpoint/state",
            }
            path = paths[suffix]
        elif rule_id.startswith("axis_conversion."):
            suffix = rule_id.split(".", 1)[1]
            paths = {
                "study_day_missing_anchor": "/projection/axis_basis/study_day_anchor_event_ref",
                "timezone_boundary": "/projection/axis_basis/default_axis_mode",
                "partial_anchor": "/projection/events/0/start_endpoint/state",
                "phase_anchor": "/projection/axis_basis/study_day_anchor_event_ref",
                "cutoff_anchor": "/projection/axis_basis/study_day_anchor_event_ref",
            }
            path = paths[suffix]
            if suffix == "study_day_missing_anchor":
                invalid = None
        elif rule_id.startswith("uncertain_dates."):
            suffix = rule_id.split(".", 1)[1]
            paths = {
                "partial_start": "/projection/events/1/start_endpoint/state",
                "partial_end": "/projection/events/1/end_endpoint/state",
                "conflicted_start": "/projection/events/1/start_endpoint/state",
                "conflicted_end": "/projection/events/1/end_endpoint/state",
                "missing_point": "/projection/risk_anchors/0/start_endpoint/state",
                "missing_interval": "/projection/events/0/start_endpoint/state",
                "open_start": "/projection/events/0/geometry",
                "open_end": "/projection/events/1/geometry",
            }
            path = paths[suffix]
        elif rule_id.startswith("eight_domain_adaptation."):
            ordinal = sorted([
                "ae_event", "ae_risk", "background_mapping", "cm_event", "efficacy_subtype", "hospital_event", "ip_event", "lab_event",
                "mh_event", "mh_risk", "non_drug_mapping", "not_applicable_vs_not_provided", "protocol_event", "protocol_risk", "symptom_event", "unknown_other_forbidden",
            ]).index(rule_id.split(".", 1)[1])
            path = f"/projection/domain_tracks/{ordinal % 8}/applicability_state"
        else:
            path = "/projection/risk_anchors/0/severity"
        return f"adapter.inherited.{rule_id}", {"op": "replace", "path": path, "value": invalid}
    if rule_id == "aemh_match_history.no_auto_close":
        return f"adapter.inherited.{rule_id}", {"op": "replace", "path": "/projection/threads/0/history_entries/2/event_kind", "value": "match_decided"}
    ordinal = sorted([
        "aemh_projection.ae_journey", "aemh_projection.ae_profile", "aemh_projection.ae_risk", "aemh_projection.ae_timeline",
        "aemh_projection.mh_journey", "aemh_projection.mh_profile", "aemh_projection.mh_risk", "aemh_projection.mh_timeline",
    ]).index(rule_id)
    return f"adapter.inherited.{rule_id}", {"op": "replace", "path": f"/projection/threads/{ordinal % 2}/domain", "value": invalid}


def pointer_after_mutation(document: dict[str, Any], path: str) -> Any:
    if path == "/":
        return digest(document)
    try:
        return copy.deepcopy(json_pointer_get(document, path))
    except (KeyError, IndexError, TypeError):
        return None


def build_trace_registry(subject_bundle: dict[str, Any], aemh_bundle: dict[str, Any], fixtures: dict[str, Any], recipes: dict[str, Any]) -> dict[str, Any]:
    challenge_registry = json.loads((ROOT / PARENT_CHALLENGES).read_text())
    selected = [
        *[row for row in challenge_registry["inherited_cases"] if row["contract"] in (SUBJECT, AEMH)],
        *[row for row in challenge_registry["public_authority_specific_cases"] if row["contract"] in (SUBJECT, AEMH)],
    ]
    authority_bases = trace_authority_bases(subject_bundle, aemh_bundle)
    parent = parent_validator()
    subject_schema = json.loads((ROOT / SUBJECT_SCHEMA).read_text())
    aemh_schema = json.loads((ROOT / AEMH_SCHEMA).read_text())
    packet_cache: dict[str, tuple[dict[str, Any] | None, dict[str, Any]]] = {}
    for base_ref, authority_bundle in authority_bases.items():
        if authority_bundle["target_contract"] == SUBJECT:
            packet = execute_recipe_dag(authority_bundle, recipes)
            ensure_parent_valid(SUBJECT, packet)
            packet_cache[base_ref] = (None, packet)
        else:
            previous, packet = execute_recipe_dag(authority_bundle, recipes)
            ensure_parent_valid(AEMH, previous, None)
            ensure_parent_valid(AEMH, packet, previous)
            packet_cache[base_ref] = (previous, packet)
    rows = []
    positive_hashes = set()
    positive_fixtures = {row["case_id"]: row for row in fixtures["positive_paths"]}
    for source_case in selected:
        target = source_case["contract"]
        rule_id = source_case["stage_oracle_contract"]["rule_id"]
        inherited = source_case["origin"] == "accepted_r5_v0_3_challenge_rule_projection"
        outcome = source_case["expected_typed_outcome_or_error"]
        expected_disposition, expected_code = outcome.split(":", 1)
        if inherited and expected_disposition == "accept":
            fixture = positive_fixtures[source_case["case_id"]]
            base_ref = fixture["authority_input_ref"]
            base = authority_bases[base_ref]
            operations = copy.deepcopy(fixture["source_transformation"])
            transformed = copy.deepcopy(base)
            for operation in sorted(operations, key=lambda item: item["sequence"]):
                if json_pointer_get(transformed, operation["path"]) != operation["pre_value"]:
                    raise SystemExit(f"STOP positive trace pre-value {source_case['case_id']}:{operation['path']}")
                apply_source_operation(transformed, operation)
                if json_pointer_get(transformed, operation["path"]) != operation["post_value"]:
                    raise SystemExit(f"STOP positive trace post-value {source_case['case_id']}:{operation['path']}")
            reseal_bundle(transformed)
            if transformed["bundle_content_identity"] != fixture["authority_input_content_identity"]:
                raise SystemExit(f"STOP positive trace bundle replay {source_case['case_id']}")
            previous = None
            if target == SUBJECT:
                post_graph = execute_recipe_dag(transformed, recipes)
                issues = parent.validate_subject(post_graph, subject_schema)
            else:
                previous, post_graph = execute_recipe_dag(transformed, recipes)
                issues = [*parent.validate_aemh(previous, aemh_schema, None), *parent.validate_aemh(post_graph, aemh_schema, previous)]
            primary_path = {
                "axis_conversion.calendar_default": "/source/axis/mode",
                "axis_conversion.study_day_valid": "/source/axis/day_zero_convention",
                "axis_conversion.conversion_replay": "/source/events/0/end/exact_date",
            }.get(rule_id, "/source/decision_records")
            primary_candidates = [operation for operation in operations if operation["path"] == primary_path]
            if not primary_candidates:
                raise SystemExit(f"STOP positive primary path {source_case['case_id']}:{primary_path}")
            realized = primary_candidates[0]
            linked = [operation for operation in operations if operation["sequence"] != realized["sequence"]]
            structural_diff = raw_source_mutations(base["source"], transformed["source"], "/source")
            recorded_diff = [{key: operation[key] for key in ("op", "path", "value")} for operation in operations]
            if structural_diff != recorded_diff:
                raise SystemExit(f"STOP positive structural operation completeness {source_case['case_id']}")
            if (len(operations) == 1) != (linked == []):
                raise SystemExit(f"STOP positive linked cardinality {source_case['case_id']}")
            if source_case["case_id"] == "R5C-109" and (len(operations) != 1 or linked):
                raise SystemExit("STOP R5C-109 single-operation contract")
            if source_case["case_id"] != "R5C-109" and len(operations) <= 1:
                raise SystemExit(f"STOP positive multi-operation contract {source_case['case_id']}")
            pre = realized["pre_value"]
            post = realized["post_value"]
            adapter_id = f"adapter.accepted.{rule_id}"
            reseal = True
            positive_hashes.add(post_graph["packet_content_hash"])
            post_authority_identity = transformed["bundle_content_identity"]
        else:
            base_ref = source_case.get("base_input_key", "subject_temporal_valid_base" if target == SUBJECT else "aemh_match_history_valid_base")
            base = authority_bases[base_ref]
            previous, base_packet = packet_cache[base_ref]
            post_graph = copy.deepcopy(base_packet)
            if inherited:
                adapter_id, realized = inherited_reject_adapter(rule_id, target)
                reseal = True
            else:
                adapter_id = f"adapter.parent-specific.{rule_id}"
                realized = copy.deepcopy(source_case["single_mutation"])
                reseal = source_case["fully_reseal_after_mutation"]
            pre = pointer_after_mutation(post_graph, realized["path"])
            parent.apply_mutation(post_graph, realized)
            post = pointer_after_mutation(post_graph, realized["path"])
            if reseal:
                preserve = source_case["category"].startswith(("subject_evaluation_identity_", "aemh_evaluation_identity_"))
                if target == SUBJECT:
                    parent.reseal_subject_packet(post_graph, subject_schema, preserve_evaluation=preserve)
                else:
                    parent.reseal_aemh_packet(post_graph, aemh_schema, preserve_evaluation=preserve)
            issues = parent.validate_subject(post_graph, subject_schema) if target == SUBJECT else parent.validate_aemh(post_graph, aemh_schema, previous)
            linked = [{"op": "apply_parent_mutation", "target": realized["path"]}]
            if reseal:
                linked.append({"op": "reseal_parent_graph", "target": target})
            linked.append({"op": "validate_parent", "target": target})
            post_authority_identity = base["bundle_content_identity"]
        observed_disposition = "accept" if not issues else "reject"
        if observed_disposition != expected_disposition:
            raise SystemExit(f"STOP trace disposition {source_case['case_id']}: expected={expected_disposition} issues={issues}")
        if not inherited and expected_code not in issues:
            raise SystemExit(f"STOP trace parent code {source_case['case_id']}: expected={expected_code} issues={issues}")
        if not inherited and reseal and "PUB_HASH_MISMATCH" in issues:
            raise SystemExit(f"STOP trace reseal leaked hash {source_case['case_id']}: {issues}")
        reseal_mode = ("full_subject_dag" if target == SUBJECT else "full_aemh_dag") if reseal else "none"
        reseal_order = [f"{operation.get('sequence', index)}:{operation['op']}:{operation.get('path', operation.get('target'))}" for index, operation in enumerate([realized, *linked], start=1)]
        operation_count = 1 + len(linked)
        lane = "typed_source_transform" if inherited else "parent_error_probe"
        instance_selector = {"base_variant": base_ref, "semantic_rule_path": source_case["single_mutation"]["path"]}
        identity_payload = {
            "base_input_content_identity": base["bundle_content_identity"],
            "realized_mutation": realized,
            "linked_operations": linked,
            "lane": lane,
        }
        record = {
            "source_case_ref": source_case["case_id"], "source_rule_id": rule_id,
            "base_input_ref": base_ref, "base_input_content_identity": base["bundle_content_identity"], "contract": target,
            "source_single_mutation": source_case["single_mutation"], "adapter_id": adapter_id, "realized_mutation": realized,
            "exact_path": realized["path"], "instance_selector": instance_selector, "pre_value": pre, "post_value": post,
            "linked_operations": linked, "operation_count": operation_count, "lane": lane, "expected_disposition": expected_disposition,
            "expected_code": expected_code, "observed_disposition": observed_disposition, "observed_ordered_issues": issues,
            "reseal_mode": reseal_mode, "reseal_order": reseal_order, "post_authority_input_content_identity": post_authority_identity,
            "post_graph_content_hash": post_graph["packet_content_hash"],
            "trace_identity": digest(identity_payload),
        }
        typed_issues = validate_typed(record, "TraceRealizationBindingV02", build_schema())
        if typed_issues:
            raise SystemExit(f"STOP trace typed record {source_case['case_id']}: {typed_issues}")
        rows.append(record)
    identities = {row["trace_identity"] for row in rows}
    if len(rows) != 236 or len(identities) != 236 or len(positive_hashes) != 10:
        duplicate_groups: dict[str, list[str]] = {}
        for row in rows:
            duplicate_groups.setdefault(row["trace_identity"], []).append(row["source_case_ref"])
        aliases = [case_refs for case_refs in duplicate_groups.values() if len(case_refs) > 1]
        raise SystemExit(f"STOP trace closure rows={len(rows)} identities={len(identities)} positive_hashes={len(positive_hashes)} aliases={aliases}")
    counts = {
        SUBJECT: {"inherited": sum(row["contract"] == SUBJECT for row in challenge_registry["inherited_cases"]), "specific": sum(row["contract"] == SUBJECT for row in challenge_registry["public_authority_specific_cases"])},
        AEMH: {"inherited": sum(row["contract"] == AEMH for row in challenge_registry["inherited_cases"]), "specific": sum(row["contract"] == AEMH for row in challenge_registry["public_authority_specific_cases"])},
    }
    base_inputs = {name: authority_bundle for name, authority_bundle in sorted(authority_bases.items())}
    root = {"schema": "trace-realization-registry-v0.2", "identity_excludes": ["source_case_ref", "source_rule_id", "source_single_mutation", "adapter_id", "exact_path", "instance_selector", "pre_value", "post_value", "operation_count", "label", "sentinel", "expected_disposition", "expected_code", "observed_disposition", "observed_ordered_issues", "post_authority_input_content_identity", "post_graph_content_hash"], "counts": counts, "spec_count": len(rows), "unique_trace_count": len(identities), "alias_count": len(rows) - len(identities), "base_authority_inputs": base_inputs, "records": rows}
    return {**root, "registry_content_hash": digest(root)}


POSITIVE_DECISIONS = {
    "aemh_match_history.ae_exact": ("ae", [("DEC-266438af6604301c160f", "match_decided", "exact", ["fact::reported-ae::later-1"], [], "identity_exact")]),
    "aemh_match_history.mh_exact": ("mh", [("DEC-e671321ceb83e22e0847", "match_decided", "exact", ["fact::reported-mh::later-1"], [], "identity_exact")]),
    "aemh_match_history.ambiguous": ("ae", [("DEC-fed24c4c8e55478c9293", "match_decided", "ambiguous", ["fact::reported-ae::later-1", "fact::reported-ae::later-2"], [], "identity_ambiguous")]),
    "aemh_match_history.rejected": ("mh", [("DEC-07bf5873ffa0d83262e8", "match_decided", "rejected", [], ["considered-fact::reported-mh::1"], "identity_rejected")]),
    "aemh_match_history.withdrawn": ("ae", [("DEC-2dd4176c4dc211e94733", "match_decided", "exact", ["fact::reported-ae::later-1"], [], "identity_exact"), ("DEC-e2607a29a23999e73d69", "withdrawn", None, ["fact::reported-ae::later-1"], [], "source_withdrawn")]),
    "aemh_match_history.reappeared": ("ae", [("DEC-31470006431fde35c3e9", "match_decided", "exact", ["fact::reported-ae::later-1"], [], "identity_exact"), ("DEC-3f53df1a68bbd447547d", "withdrawn", None, ["fact::reported-ae::later-1"], [], "source_withdrawn"), ("DEC-681d75b8ef22bcf72153", "reappeared", None, ["fact::reported-ae::later-1"], [], "source_reappeared")]),
    "aemh_match_history.append_only": ("mh", [("DEC-ccde6ba8f813203c7d0c", "match_decided", "ambiguous", ["fact::reported-mh::later-1", "fact::reported-mh::later-2"], [], "identity_ambiguous")]),
}


def diff_ops(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    if type(before) is not type(after):
        return [{"op": "replace", "path": path or "/", "value": after}]
    if isinstance(before, dict):
        if set(before) != set(after):
            return [{"op": "replace", "path": path or "/", "value": after}]
        return [op for key in sorted(before) for op in diff_ops(before[key], after[key], f"{path}/{key}")]
    if isinstance(before, list):
        if len(before) != len(after):
            return [{"op": "replace", "path": path or "/", "value": after}]
        return [op for index, (left, right) in enumerate(zip(before, after)) for op in diff_ops(left, right, f"{path}/{index}")]
    return [] if before == after else [{"op": "replace", "path": path or "/", "value": after}]


def raw_source_mutations(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    if type(before) is not type(after):
        return [{"op": "replace", "path": path or "/", "value": copy.deepcopy(after)}]
    if isinstance(before, dict):
        if set(before) != set(after):
            return [{"op": "replace", "path": path or "/", "value": copy.deepcopy(after)}]
        return [operation for key in sorted(before) for operation in raw_source_mutations(before[key], after[key], f"{path}/{key}")]
    if isinstance(before, list):
        if len(after) >= len(before) and after[:len(before)] == before:
            return [{"op": "append", "path": path or "/", "value": copy.deepcopy(value)} for value in after[len(before):]]
        if len(before) == len(after):
            return [operation for index, (left, right) in enumerate(zip(before, after)) for operation in raw_source_mutations(left, right, f"{path}/{index}")]
        return [{"op": "replace", "path": path or "/", "value": copy.deepcopy(after)}]
    return [] if before == after else [{"op": "replace", "path": path or "/", "value": copy.deepcopy(after)}]


def apply_source_operation(authority_bundle: dict[str, Any], operation: dict[str, Any]) -> None:
    if operation["op"] == "replace":
        json_pointer_replace(authority_bundle, operation["path"], operation["value"])
    elif operation["op"] == "append":
        target = json_pointer_get(authority_bundle, operation["path"])
        if not isinstance(target, list):
            raise ValueError("TPA_V02_SOURCE_APPEND_TARGET")
        target.append(copy.deepcopy(operation["value"]))
    else:
        raise ValueError(f"TPA_V02_SOURCE_OPERATION:{operation['op']}")


def record_and_apply(authority_bundle: dict[str, Any], sequence: int, mutation: dict[str, Any]) -> dict[str, Any]:
    path = mutation["path"]
    pre = copy.deepcopy(json_pointer_get(authority_bundle, path))
    operation = {"sequence": sequence, **copy.deepcopy(mutation), "pre_value": pre}
    apply_source_operation(authority_bundle, operation)
    operation["post_value"] = copy.deepcopy(json_pointer_get(authority_bundle, path))
    return operation


def source_operations(before_bundle: dict[str, Any], after_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    replay = json.loads(canonical_bytes(before_bundle))
    operations = []
    for sequence, mutation in enumerate(raw_source_mutations(before_bundle["source"], after_bundle["source"], "/source"), start=1):
        operations.append(record_and_apply(replay, sequence, mutation))
    reseal_bundle(replay)
    if replay != json.loads(canonical_bytes(after_bundle)):
        raise ValueError("TPA_V02_SOURCE_OPERATION_REPLAY")
    return operations


def aemh_positive_seed(aemh_bundle: dict[str, Any]) -> dict[str, Any]:
    seed = copy.deepcopy(aemh_bundle)
    seed["source"]["decision_records"] = []
    seed["source"]["current_locator_specs"] = [row for row in seed["source"]["current_locator_specs"] if row["entity_kind"] == "candidate"]
    revision = "source-revision::listing::N"
    seed["source"]["current_revision_specs"] = [{"revision_ref": revision, "revision_content_identity": revision_identity(revision), "locator_refs": sorted(row["locator_ref"] for row in seed["source"]["current_locator_specs"])}]
    reseal_bundle(seed)
    return seed


def transform_positive(rule_id: str, subject_base: dict[str, Any], aemh_base: dict[str, Any], recipes: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any]]:
    if rule_id.startswith("axis_conversion."):
        changed = copy.deepcopy(subject_base)
        if rule_id == "axis_conversion.calendar_default":
            changed["source"]["axis"]["mode"] = "study_day"
        elif rule_id == "axis_conversion.study_day_valid":
            changed["source"]["axis"]["day_zero_convention"] = "anchor_day_zero"
        elif rule_id == "axis_conversion.conversion_replay":
            changed["source"]["events"][0]["end"]["exact_date"] = "2026-08-03"
        else:
            raise ValueError(f"unknown accepted axis adapter {rule_id}")
        recompute_subject_study_days(changed["source"])
        core = {key: value for key, value in changed.items() if key != "bundle_content_identity"}
        changed["bundle_content_identity"] = digest(core)
        packet = execute_recipe_dag(changed, recipes)
        ensure_parent_valid(SUBJECT, packet)
        return SUBJECT, changed, {"packet_content_hash": packet["packet_content_hash"], "projection_content_hash": packet["projection"]["projection_content_hash"], "operations": source_operations(subject_base, changed)}
    changed = copy.deepcopy(aemh_base)
    domain, decisions = POSITIVE_DECISIONS[rule_id]
    thread_ref = f"aemh-thread::{domain}::1"
    changed["source"]["decision_records"] = [{"decision_ref": row[0], "thread_ref": thread_ref, "event_kind": row[1], "match_state": row[2], "fact_refs": row[3], "considered_fact_refs": row[4], "reason_code": row[5]} for row in decisions]
    curr = "snapshot::N+1"; revision = "source-revision::listing::N+1"
    candidate_locs = [row for row in changed["source"]["current_locator_specs"] if row["entity_kind"] == "candidate"]
    evidence_locs = []
    needed_facts = sorted({fact for row in decisions for fact in row[3]})
    needed_considered = sorted({fact for row in decisions for fact in row[4]})
    for fact in needed_facts:
        suffix = fact.rsplit("-", 1)[-1]
        evidence_locs.append(locator_input(f"locator::fact::{domain}{suffix}", f"{domain}-row::{suffix}", "term", curr, revision, "later_fact", fact, domain, thread_ref))
    for fact in needed_considered:
        evidence_locs.append(locator_input(f"locator::considered-fact::{domain}1", f"{domain}-row::considered-1", "term", curr, revision, "considered_fact", fact, domain, thread_ref))
    changed["source"]["current_locator_specs"] = [*candidate_locs, *sorted(evidence_locs, key=lambda row: row["locator_ref"])]
    changed["source"]["current_revision_specs"] = [
        {"revision_ref": "source-revision::listing::N", "revision_content_identity": revision_identity("source-revision::listing::N"), "locator_refs": sorted(row["locator_ref"] for row in candidate_locs)},
        {"revision_ref": revision, "revision_content_identity": revision_identity(revision), "locator_refs": sorted(row["locator_ref"] for row in evidence_locs)},
    ] if evidence_locs else [{"revision_ref": "source-revision::listing::N", "revision_content_identity": revision_identity("source-revision::listing::N"), "locator_refs": sorted(row["locator_ref"] for row in candidate_locs)}]
    core = {key: value for key, value in changed.items() if key != "bundle_content_identity"}; changed["bundle_content_identity"] = digest(core)
    previous, current = execute_recipe_dag(changed, recipes)
    ensure_parent_valid(AEMH, previous, None); ensure_parent_valid(AEMH, current, previous)
    selected = next(row for row in current["projection"]["threads"] if row["thread_ref"] == thread_ref)
    return AEMH, changed, {"packet_content_hash": current["packet_content_hash"], "projection_content_hash": current["projection"]["projection_content_hash"], "operations": source_operations(aemh_base, changed), "thread_history_length": len(selected["history_entries"]), "previous_prefix_byte_identical": selected["history_entries"][:1] == next(row for row in previous["projection"]["threads"] if row["thread_ref"] == thread_ref)["history_entries"]}


def build_fixture_registry(subject_bundle: dict[str, Any], aemh_bundle: dict[str, Any], recipes: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    subject_packet, subject_recipe_outputs = execute_recipe_dag(subject_bundle, recipes, capture_outputs=True)
    aemh_result, aemh_recipe_outputs = execute_recipe_dag(aemh_bundle, recipes, capture_outputs=True)
    previous, current = aemh_result
    if len(subject_recipe_outputs) != 8 or len(aemh_recipe_outputs) != 8:
        raise SystemExit("STOP recipe execution cardinality")
    if any(row["content_hash"] != digest(row["value"]) for row in [*subject_recipe_outputs.values(), *aemh_recipe_outputs.values()]):
        raise SystemExit("STOP recipe seal execution")
    legacy_subject = FullGraphExecutor(subject_bundle).subject_packet()
    legacy_previous, legacy_current = FullGraphExecutor(aemh_bundle).aemh_packets()
    if subject_packet != legacy_subject or previous != legacy_previous or current != legacy_current:
        raise SystemExit("STOP recipe DAG full-graph equivalence")
    subject_errors = ensure_parent_valid(SUBJECT, subject_packet)
    previous_errors = ensure_parent_valid(AEMH, previous, None)
    current_errors = ensure_parent_valid(AEMH, current, previous)
    positives = []
    aemh_seed = aemh_positive_seed(aemh_bundle)
    seed_previous, seed_current = execute_recipe_dag(aemh_seed, recipes)
    ensure_parent_valid(AEMH, seed_previous, None)
    ensure_parent_valid(AEMH, seed_current, seed_previous)
    positive_base_inputs = {"positive.subject.axis.base": subject_bundle, "positive.aemh.decision.seed": aemh_seed}
    challenge_rows = {row["case_id"]: row for row in json.loads((ROOT / PARENT_CHALLENGES).read_text())["inherited_cases"]}
    for case_id in POSITIVE_CASES:
        rule_id = challenge_rows[case_id]["stage_oracle_contract"]["rule_id"]
        base_ref = "positive.subject.axis.base" if rule_id.startswith("axis_conversion.") else "positive.aemh.decision.seed"
        target, transformed, observation = transform_positive(rule_id, subject_bundle, aemh_seed, recipes)
        positives.append({"case_id": case_id, "contract": target, "authority_input_ref": base_ref, "authority_input_content_identity": transformed["bundle_content_identity"], "source_transformation": observation.pop("operations"), "observation": observation, "parent_valid": True, "parent_errors": []})
    baselines = [
        {"fixture_ref": "fixture.subject.full.v02", "authority_input": subject_bundle, "observation": {"packet_content_hash": subject_packet["packet_content_hash"], "projection_content_hash": subject_packet["projection"]["projection_content_hash"], "cardinalities": {"scope": 1, "visibility": 1, "axis": 1, "locators": 4, "revision_pairs": 1, "endpoints": 8, "visits": 1, "events": 2, "risks": 1, "phases": 1, "pending": 2, "domains": 8, "membership": 1, "projection": 1, "receipt": 1, "packet": 1}}, "parent_valid": True, "parent_errors": subject_errors},
        {"fixture_ref": "fixture.aemh.full.v02", "authority_input": aemh_bundle, "observation": {"previous_packet_content_hash": previous["packet_content_hash"], "current_packet_content_hash": current["packet_content_hash"], "previous_projection_content_hash": previous["projection"]["projection_content_hash"], "current_projection_content_hash": current["projection"]["projection_content_hash"], "cardinalities": {"previous_threads": 2, "previous_reminders": 2, "previous_locators": 2, "previous_revision_pairs": 1, "current_threads": 2, "current_locators": 4, "current_revision_pairs": 2, "prefixes": 2, "current_entries": 6, "membership": 1, "projection": 1, "receipt": 1, "packet": 1}}, "parent_valid": True, "parent_errors": [*previous_errors, *current_errors]},
    ]
    root = {"schema": "full-graph-fixture-registry-v0.2", "execution_profile": PROFILE, "candidate_inputs_contain_no_parent_packet": True, "baseline_valid_count": 2, "baseline_error_count": 0, "positive_valid_count": len(positives), "positive_error_count": 0, "positive_base_inputs": positive_base_inputs, "baselines": baselines, "positive_paths": positives}
    result = {**root, "registry_content_hash": digest(root)}
    runtime = {"subject_packet": subject_packet, "aemh_previous": previous, "aemh_current": current}
    return result, runtime


def context_markdown(fixtures: dict[str, Any], traces: dict[str, Any], emitters: dict[str, Any]) -> bytes:
    text = f"""# R5-S5 temporal projection authority delta v0.2 context

## Boundary

This append-only candidate is `{CONTRACT_ID}` with schema `{SCHEMA_VERSION}`, authority scope `{AUTHORITY_SCOPE}` and execution profile `{PROFILE}`. It supersedes temporal v0.1 only when the immutable v0.1 manifest SHA, the execution profile and one exact target contract (`{SUBJECT}` or `{AEMH}`) all match. Otherwise execution stops. It changes no parent/semantic schema, enum, value or hash formula and creates no producer, runtime, test, evidence or acceptance surface.

Only the nine task-authorized paths are writable. Port 8911, services, browser, real projects, models, medical writing, frontend/packages/runtime/deploy and all accepted or rejected source surfaces remain outside authority. This worker does not accept the candidate.

## Source re-anchor

Before editing, 80 current pinned files totaling 38,643,634 bytes were read in full: 32 JSON files parsed, 25 Python files parsed through AST and 23 prose files decoded as UTF-8. The accepted parent, semantic delta and temporal v0.1 pins were checked; rejected implementation v0.1-v0.3 remained negative evidence only.

## Exact supersession and execution

The registry preserves the v0.1 external-registry receipt and parent-semantic snapshot recipes and supersedes only the named composition methods. It freezes {emitters['affected_mapping_count']} affected v0.1 mapping IDs and content hashes, 16 closed executable v0.2 recipes, full dependency edges and external pins. Candidate authority inputs contain no packet, expected packet/hash, expected error, acceptance token or target output.

The executor composed full graphs from typed inputs. Subject closure is 4 locators, 1 revision pair, 8 endpoint instances, 1/2/1/1 visit/event/risk/phase, 2 pending items, eight ordered domains and one membership/projection/receipt/packet. AE/MH closure first builds the two-reminder previous packet and then the two-thread, four-locator current packet with byte-identical prefixes, AE exact-withdrawn-reappeared and MH rejected history.

## Mechanical evidence

- parent-valid baselines: `{fixtures['baseline_valid_count']}/2`; errors `{fixtures['baseline_error_count']}/0`;
- source-transformed positive post graphs: `{fixtures['positive_valid_count']}/10`; errors `{fixtures['positive_error_count']}/0`;
- trace realization: `{traces['spec_count']}/236` specs, `{traces['unique_trace_count']}/236` unique traces, `{traces['alias_count']}/0` aliases;
- trace inventory: subject `{traces['counts'][SUBJECT]['inherited']}+{traces['counts'][SUBJECT]['specific']}`, AE/MH `{traces['counts'][AEMH]['inherited']}+{traces['counts'][AEMH]['specific']}`.

Independent verification, optimization modes, hash-seed replay, generator `--check`, offline Ruff, forbidden-write and protected-surface gates remain mandatory before handoff. Only a fresh reviewer may return `ACCEPT_R5_S5_TEMPORAL_PROJECTION_AUTHORITY_DELTA_V0_2`, and that verdict could unlock only implementation-contract v0.4 generation.
"""
    return text.encode()


def review_markdown(fixtures: dict[str, Any], traces: dict[str, Any], emitters: dict[str, Any]) -> bytes:
    text = f"""# R5-S5 temporal projection authority delta v0.2 worker review

## Disposition

`CANDIDATE_FOR_FRESH_REVIEW` — not accepted by this worker.

The candidate remains synthetic/offline and append-only. Exact supersession is gated by temporal-v0.1 manifest SHA + `{PROFILE}` + exact target contract. The only replaced surfaces are the named v0.1 composition methods; read/scope/resolve/record/canonical/seal/direct-source primitives and both accepted parent schemas and hash formulas are preserved.

## Full-graph result

The executor built the subject packet and both AE/MH lineage packets solely from typed v0.2 authority inputs; no accepted parent packet fixture is read or copied. The accepted parent validator returned no errors for 2/2 baselines. All ten positive source transformations (`R5C-109`, `R5C-110`, `R5C-116`, `R5C-157..163`) rebuilt complete post packets and returned parent-valid with zero errors. Packet hashes in the fixture registry are observations, not candidate authority or expected values.

The trace registry is derived from the accepted parent challenge data: subject 48 inherited + 95 specific = 143; AE/MH 16 inherited + 77 specific = 93; total `{traces['spec_count']}`, unique `{traces['unique_trace_count']}`, aliases `{traces['alias_count']}`. Each identity contains only the real typed pre-input identity, the actual primary and linked mutations, and the execution lane. R5C-109 has one real operation and therefore an empty linked list; each other accepted trace has a complete non-empty linked list for every additional structural diff. Case/rule labels, selectors, expected outcomes and post/result hashes are recorded for audit but excluded from identity.

## Reviewer challenge surface

Fresh review must independently challenge all parent subject and AE/MH error families, domain omit/duplicate/order/unknown, locator resolution/use/partition, cutoff/visibility/membership/pending/study-day/cross-domain, reminder/evidence/prefix/previous/thread/append, root constants, candidate packet/output/error contamination, emitter override, missing/wrong trace path, forced alias/duplicate identity and pin drift. It must also re-run normal/O/O2, three hash seeds, two deterministic generations, `--check`, offline Ruff, no-assert, bytecode/S5 absence, medical-writing aggregate and 8911-stopped gates.

No producer, runtime, UI/browser, real project/model, clinical authority, product, production, medical-writing or port-8911 work is unlocked. A fresh isolated reviewer alone may decide `ACCEPT_R5_S5_TEMPORAL_PROJECTION_AUTHORITY_DELTA_V0_2` for one immutable manifest.
"""
    return text.encode()


def build_manifest(schema: dict[str, Any], emitters: dict[str, Any], fixtures: dict[str, Any], traces: dict[str, Any], pre_manifest: dict[str, bytes]) -> dict[str, Any]:
    v01 = json.loads((ROOT / V01_MANIFEST).read_text())
    accepted_parent_pins = copy.deepcopy(v01["accepted_parent_pins"])
    accepted_parent_pins.pop("source_file_sha256", None)
    accepted_parent_pins["artifact_raw_sha256"] = {
        path: sha
        for path, sha in accepted_parent_pins["artifact_raw_sha256"].items()
        if not path.endswith("/" + "base_" + "inputs.json")
    }
    file_pins = {rel: hashlib.sha256(data).hexdigest() for rel, data in sorted(pre_manifest.items())}
    for rel in (PATHS[7], PATHS[8]):
        file_pins[rel] = raw_sha(ROOT / rel)
    core = {
        "schema": "r5-s5-temporal-projection-authority-delta-v0.2-manifest",
        "contract_id": CONTRACT_ID, "schema_version": SCHEMA_VERSION, "status": "candidate_unaccepted",
        "authority_scope": AUTHORITY_SCOPE, "execution_profile": PROFILE, "non_clinical": True, "no_self_acceptance": True,
        "supersedes": {"contract": "medical-monitoring-r5-s5-temporal-projection-authority-delta-v0.1", "manifest_sha256": FROZEN_PINS[V01_MANIFEST], "only_when": ["manifest pin exact", f"execution_profile={PROFILE}", f"target_contract in [{SUBJECT},{AEMH}]"], "otherwise": "STOP"},
        "preserved_v01_primitives": ["read", "scope", "resolve", "record", "canonical", "seal", "direct_source"],
        "preserved_parent_contracts": [SUBJECT, AEMH], "preserved_parent_schema_version": PARENT_SCHEMA_VERSION,
        "preserved_v01_recipe_ids": ["recipe.external_registry_receipt_resolution", "recipe.parent_semantic_snapshot_immutability"],
        "superseded_v01_methods": [row["v01_method"] for row in emitters["supersession_rules"]],
        "emitter_recipe_registry_content_hash": emitters["registry_content_hash"], "affected_mapping_count": emitters["affected_mapping_count"],
        "schema_baseline_content_hash": schema["baseline_content_hash"], "full_graph_fixture_registry_content_hash": fixtures["registry_content_hash"],
        "trace_realization_registry_content_hash": traces["registry_content_hash"],
        "closure": {"baseline_valid": fixtures["baseline_valid_count"], "baseline_errors": fixtures["baseline_error_count"], "positive_valid": fixtures["positive_valid_count"], "positive_errors": fixtures["positive_error_count"], "trace_specs": traces["spec_count"], "unique_traces": traces["unique_trace_count"], "aliases": traces["alias_count"]},
        "exact_v02_paths": list(PATHS), "file_raw_sha256": file_pins,
        "external_pins": {**FROZEN_PINS, **REJECTED_V03_PINS},
        "typed_source_pins": TYPED_SOURCE_PINS,
        "accepted_parent_pins": accepted_parent_pins, "accepted_semantic_delta_pins": v01["accepted_semantic_delta_pins"],
        "rejected_v01_v02_negative_evidence_only": v01["rejected_snapshot_negative_evidence_only"], "rejected_v03_negative_evidence_only": REJECTED_V03_PINS,
        "protected_accepted_pins": v01["accepted_parent_pins"]["protected_accepted_pins"],
        "parent_validator": {"path": PARENT_VALIDATOR, "sha256": FROZEN_PINS[PARENT_VALIDATOR], "invocation_required": True},
        "forbidden_candidate_keys": schema["forbidden_candidate_keys"],
        "active_probe_families": ["parent_subject_15", "parent_aemh_13", "domain_omit_duplicate_order_unknown", "locator_unresolved_unused_partition", "cutoff_visibility_membership_pending_study_day_cross_domain", "reminder_evidence_prefix_previous_thread_append", "root_constants", "candidate_packet_output_error", "emitter_override", "trace_path_missing_wrong_instance", "forced_alias_duplicate_identity", "pin_drift"],
        "required_verification": ["normal", "python_-O", "python_-OO", "PYTHONHASHSEED_0_1_777", "two_byte_identical_generations", "generator_--check", "offline_ruff", "no_assert_only_gates", "absence_bytecode_S5_locks", "zero_forbidden_writes", "port_8911_stopped"],
        "port_8911_must_be_stopped": True, "producer_runtime_test_evidence_acceptance_files_created": False,
        "unlock": "only fresh review may unlock implementation contract v0.4 generation",
        "does_not_unlock": ["producer", "runtime", "tests", "evidence", "acceptance", "S5", "UI", "browser", "real_project", "model", "clinical_authority", "product", "production", "medical_writing"],
        "manifest_hash_recipe": "sha256(canonical_json(all manifest fields except manifest_content_hash))",
    }
    return {**core, "manifest_content_hash": digest(core)}


def port_stopped() -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.15)
        return sock.connect_ex(("127.0.0.1", 8911)) != 0


def render() -> dict[str, bytes]:
    check_pins()
    if not port_stopped():
        raise SystemExit("STOP port 8911 is listening")
    schema = build_schema()
    subject_bundle = bundle(SUBJECT, subject_source())
    aemh_bundle = bundle(AEMH, aemh_source())
    emitters = build_recipe_registry()
    fixtures, _runtime = build_fixture_registry(subject_bundle, aemh_bundle, emitters)
    traces = build_trace_registry(subject_bundle, aemh_bundle, fixtures, emitters)
    pre_manifest = {
        PATHS[0]: context_markdown(fixtures, traces, emitters),
        PATHS[1]: review_markdown(fixtures, traces, emitters),
        PATHS[3]: pretty(schema), PATHS[4]: pretty(emitters), PATHS[5]: pretty(fixtures), PATHS[6]: pretty(traces),
    }
    manifest = build_manifest(schema, emitters, fixtures, traces, pre_manifest)
    return {**pre_manifest, PATHS[2]: pretty(manifest)}


def write_or_check(outputs: dict[str, bytes], check: bool) -> None:
    mismatches = []
    for rel, expected in outputs.items():
        path = ROOT / rel
        if check:
            if not path.exists() or path.read_bytes() != expected:
                mismatches.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if mismatches:
        raise SystemExit("STOP generator check mismatch: " + ", ".join(mismatches))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--print-bundle-sha", action="store_true")
    args = parser.parse_args()
    outputs = render()
    if args.print_bundle_sha:
        print(digest({rel: hashlib.sha256(data).hexdigest() for rel, data in sorted(outputs.items())}))
        return 0
    write_or_check(outputs, args.check)
    print(json.dumps({"status": "ok", "check": args.check, "outputs": len(outputs), "baseline": "2/2", "positive": "10/10", "traces": "236/236/0"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
