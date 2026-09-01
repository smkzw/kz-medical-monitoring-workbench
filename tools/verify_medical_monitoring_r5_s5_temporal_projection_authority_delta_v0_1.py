"""Independent verifier for the R5-S5 temporal authority delta.

This module intentionally imports no generator code.  It reconstructs the
accepted parent leaf universe, canonical hashes, challenge mutations, external
registry resolution and protected pins from files and independent code.
"""

from __future__ import annotations

import ast
import copy
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import re
import socket
import subprocess
import sys
import unicodedata
from typing import Any, NoReturn

ROOT = pathlib.Path(__file__).resolve().parents[1]
DELTA = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1"
CONTRACT_ID = "medical-monitoring-r5-s5-temporal-projection-authority-delta-v0.1"
SCHEMA_VERSION = "1.0.0"
IDENTITY_FIELDS = ("project_ref", "run_ref", "snapshot_ref", "cutoff_ref", "site_ref", "subject_ref")
EXPECTED_EXTERNAL_REGISTRY_ROOT_CONTENT_HASH = "580d367783f8a00e68e8779fceec9146ddadd2bc3dd0040d26937d415b0589b3"
EXPECTED_EXTERNAL_REGISTRY_SECTION_CANONICAL_SHA256 = "65e2d571ba6858c65c2a82957639968b8f00431f2df56549a4c09f55733832cd"
EXPECTED_ACCEPTED_RECORD_CONTENT_HASH = "295a916100ea53efe816fc79ae818fc4bb0ef38a75eaaf258f3a58e314cbf391"
EXPECTED_SCHEMA_BASELINE_CONTENT_HASH = "9f2784b14c7e9f1ac6d151d340f98b834e449185af3c0ffcc0fd32f0a93c197c"
EXPECTED_ACCEPTED_RECIPE_REGISTRY_CONTENT_HASH = "91687b6d7aa7acb3d0fa24732e2872d81e7ec597c76a9d4d863dfdab40f84e3a"
EXPECTED_AUTHORITY_OUTPUT_REGISTRY_CONTENT_HASH = "2b92462366004c46bd460927514627d209cc608f3cf23688b8501ac03fad3607"
EXPECTED_RECIPE_AUTHORITY_BINDING_REGISTRY_CONTENT_HASH = "3bce92047ffb6d3173d1e22dbc7c59db922c4a4e75f7cf602c31511f4f71c463"
EXPECTED_RECIPE_CONTENT_HASHES = {
    "recipe.aemh_append_only_decision_registry": "fd32897b1fbb0696bc053928badb3f20a6fad16cc1285dab3e040d6c69fee597",
    "recipe.aemh_joint_evidence_binding": "32076528d65aee891d873ae00f9cfe13afbb9ec7a83da71cfb7a8d7ec3979531",
    "recipe.aemh_prefix_transition_closure": "96351ca4f33e8e10b01420fca65dac1935c5a7ca5eefe849425188b5d44caa2e",
    "recipe.aemh_thread_membership": "e2d007cd9285419d4ff71f3ee4217526de3f7fce2e57ef3fa7e54019a49ba293",
    "recipe.cutoff_exact_present_absent": "70126f43f32a008e6d689491e79a4cbe648bd41fd865ddbb3380a141662b6649",
    "recipe.domain_applicable_or_controlled_empty": "4fb5c08b3dcbb04f6e72ddd0abf2023c84eab145ed0f55e917b10d44cbd15f67",
    "recipe.endpoint_state_range_main_axis": "c2cd05e95d70afb25f16ee9c0a811af229ffbbf0915fbc1ea5eb3209de0da7e7",
    "recipe.event_exact_activity_binding": "99688188431a6590ab66dcc591c14c60013b0016acc7d44e346cdd168ce5798a",
    "recipe.external_registry_receipt_resolution": "530e74b410956cee22a57f66e5d17ae27bd63da05cedf49a56e920dafb793b46",
    "recipe.locator_total_consumption_revision_partition": "9ac48b610e50cdac1e4615b230c7f72f303975050f5c55972b70687ab7d8cb83",
    "recipe.parent_semantic_snapshot_immutability": "158eea76ab61b3cba5fd747949e17340fe77bb441002acedcfd1246c27c4f30c",
    "recipe.pending_union_from_unprojectable_targets": "65a9af86ad3dd3cc731b005236de438249e60e914124bb667370d57e72e40113",
    "recipe.phase_binding_accepted_zh_lexicon": "ad749ad2a6a779946ffe09c7a8e2abfb42fcea8e80bf716b810f458393ae6dc4",
    "recipe.risk_s4_eight_identity_endpoint_binding": "f95496ad3421620bde61b29add12c04b7a7e131a30408ccf8df1cb2d889aae43",
    "recipe.temporal_axis_timezone_day_zero": "7698902f6760cfeaa91c86d942645a19a18c14357a2b9caf472c804245818559",
    "recipe.upstream_roots_before_hashes_containers_packets": "df7853c3a417bb464bf5ec784b0e580201c35d1f5b6e69b74f806b311705f1d6",
    "recipe.visibility_universe_and_stable_bridge": "4bf680cbc8e3fb70c8dc0e0d5f31cad18d9b1b98a357870ce9170eb5e4288061",
    "recipe.visit_assignment_actual_bundle_encounter": "d4db58792b4a0d63f28675809ff12b56b4da92ff5ff5c38725223595df28d67f",
}
PARENT_MANIFEST = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json"
SUBJECT_SCHEMA = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json"
AEMH_SCHEMA = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json"
SEMANTIC_MANIFEST = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json"
GENERATOR = ROOT / "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1.py"
VERIFIER = pathlib.Path(__file__).resolve()

EXACT_PATHS = (
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

REQUIRED_OBJECTS = {
    "TemporalAuthorityScopeIdentity",
    "TemporalProjectionAuthorityRegistry",
    "TemporalProjectionAcceptanceReceipt",
    "PublicScopeUniverseAuthority",
    "RecordNodeStableIdentityBinding",
    "CutoffEndpointBindingAuthority",
    "SourceLocatorRevisionBinding",
    "TemporalMemberAuthorityRecord",
    "TemporalEndpointAuthorityRecord",
    "TemporalAxisAuthorityRecord",
    "VisitProjectionBinding",
    "EventProjectionBinding",
    "PhaseProjectionBinding",
    "RiskProjectionBinding",
    "S4IdentityJoin",
    "DomainApplicabilityAuthorityRecord",
    "AEMHAppendDecisionAuthorityRecord",
    "AEMHDecisionAuthorityRegistry",
    "AEMHEvidenceBindingAuthority",
    "AEMHThreadMembershipAuthority",
    "PhaseLabelPolicy",
    "TimezoneDayZeroPolicy",
    "DateStateRangeProjectionPolicy",
    "EmptyDomainApplicabilityPolicy",
    "AEMHTransitionPolicy",
}
REQUIRED_ENUMS = {
    "authority_scope",
    "acceptance_state",
    "cutoff_state",
    "visibility_state",
    "member_kind",
    "endpoint_owner_field",
    "date_state",
    "date_geometry",
    "axis_mode",
    "day_zero_convention",
    "visit_kind",
    "domain",
    "applicability_state",
    "aemh_domain",
    "history_event_kind",
    "match_state",
    "identity_evidence_kind",
    "risk_lifecycle_effect",
    "source_locator_variant",
    "phase_code",
    "empty_domain_decision",
    "recipe_cardinality",
    "ordering",
    "ir_value_type",
    "recipe_transform_op",
    "recipe_condition_op",
    "recipe_ref_kind",
    "recipe_input_source",
    "canonicalization_profile",
    "authority_projection_op",
    "authority_contract_id",
    "authority_derive_transform",
    "authority_assembly_cardinality",
    "output_cardinality",
    "hash_mode",
    "mutation_target_kind",
    "mutation_op",
    "probe_kind",
}
REQUIRED_NAMED_TYPES = {
    "DirectFieldParams",
    "DeriveValueParams",
    "ProjectRecordParams",
    "AssembleSortedRecordsParams",
    "CanonicalHashParams",
    "ProjectContractParams",
    "AuthorityFixture",
    "AuthorityOutputMapping",
    "AuthorityMappingPositiveFixture",
    "RecipeAuthorityRequirement",
    "RecipeAuthorityBinding",
    "CandidateReceipt",
    "CandidateOperationalEvidence",
    "CandidateRegistryClaim",
    "ChallengeCase",
    "ChallengeMutation",
    "CoverageCountRecord",
    "DependencyEdge",
    "ExternalAcceptedRecord",
    "ExternalCandidateBundle",
    "ExternalRegistryRoot",
    "PolicyHashEntry",
    "PositiveFixture",
    "RecipeCanonicalization",
    "RecipeCondition",
    "RecipeInputSpec",
    "RecipeOutputSpec",
    "RecipeParams",
    "RecipeRef",
    "RecipeTransform",
    "TypedValue",
    "closed_aemh_transition_matrix",
    "closed_date_state_geometry_matrix",
    "date_state_geometry_rule",
    "phase_code_to_zh_label_map",
    "AcceptedRecipeDefinition",
    "AcceptedRecipeAttackBundle",
}
IR_VALUE_TYPES = {
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
}
TRANSFORM_OPS = {
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
}
CONDITION_OPS = {
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
}
REQUIRED_RECIPE_IDS = {
    "recipe.external_registry_receipt_resolution",
    "recipe.cutoff_exact_present_absent",
    "recipe.visibility_universe_and_stable_bridge",
    "recipe.locator_total_consumption_revision_partition",
    "recipe.temporal_axis_timezone_day_zero",
    "recipe.endpoint_state_range_main_axis",
    "recipe.visit_assignment_actual_bundle_encounter",
    "recipe.event_exact_activity_binding",
    "recipe.phase_binding_accepted_zh_lexicon",
    "recipe.risk_s4_eight_identity_endpoint_binding",
    "recipe.domain_applicable_or_controlled_empty",
    "recipe.pending_union_from_unprojectable_targets",
    "recipe.aemh_append_only_decision_registry",
    "recipe.aemh_joint_evidence_binding",
    "recipe.aemh_thread_membership",
    "recipe.aemh_prefix_transition_closure",
    "recipe.upstream_roots_before_hashes_containers_packets",
    "recipe.parent_semantic_snapshot_immutability",
}


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def load(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path.relative_to(ROOT)}: {exc}")


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonicalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            fail("non-finite canonical number")
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                fail("canonical key is not a string")
            normalized = unicodedata.normalize("NFC", key)
            if normalized in output:
                fail("duplicate normalized canonical key")
            output[normalized] = canonicalize(value[key])
        return output
    fail(f"unsupported canonical type: {type(value).__name__}")


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(canonicalize(value), ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


digest = canonical_digest


def sealed(value: dict[str, Any], hash_field: str) -> dict[str, Any]:
    output = copy.deepcopy(value)
    output[hash_field] = canonical_digest(output)
    return output


def exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        fail(f"{where} keys mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}")


class ContractViolation(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


def reject(code: str, detail: str) -> NoReturn:
    raise ContractViolation(code, detail)


def verify_no_asserts(path: pathlib.Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assertions = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    if assertions:
        fail(f"assert statements forbidden in {path.name}: {assertions}")


def verify_generator_has_no_semantic_interpreter() -> None:
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"), filename=str(GENERATOR))
    forbidden_names = {"execute_recipe", "execute_transform", "condition_passes", "typed_value_python", "interpret_recipe"}
    declared = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    if forbidden_names & (declared | called):
        fail("generator contains semantic interpreter or output backfill helper")
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    if any("verify_medical_monitoring_r5_s5_temporal_projection" in name for name in imports):
        fail("generator imports independent verifier")


def verify_exact_paths(manifest: dict[str, Any]) -> None:
    if tuple(manifest.get("exact_delta_paths", ())) != EXACT_PATHS:
        fail("exact nine-path allowlist mismatch")
    for relative in EXACT_PATHS:
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            fail(f"delta path missing or symlinked: {relative}")
    artifact_names = sorted(path.name for path in DELTA.iterdir() if path.is_file() or path.is_symlink())
    expected_names = sorted(["manifest.json", "schema.json", "source_matrix_delta.json", "recipe_registry.json", "challenge_registry.json"])
    if artifact_names != expected_names:
        fail(f"delta artifact set mismatch: {artifact_names}")


def verify_raw_pins(manifest: dict[str, Any]) -> None:
    raw = manifest.get("artifact_raw_sha256")
    if not isinstance(raw, dict) or len(raw) != 8:
        fail("manifest must pin exactly eight non-manifest delta files")
    for relative, expected in raw.items():
        actual = raw_sha(ROOT / relative)
        if actual != expected:
            fail(f"delta raw pin mismatch: {relative}")
    content = dict(manifest)
    claimed = content.pop("manifest_content_hash", None)
    if claimed != canonical_digest(content):
        fail("manifest content hash mismatch")


def verify_parent_and_negative_pins(manifest: dict[str, Any]) -> None:
    parent = manifest.get("accepted_parent_pins", {})
    semantic = manifest.get("accepted_semantic_delta_pins", {})
    for group_name, group in (("parent", parent), ("semantic", semantic)):
        for key in ("manifest_path", "manifest_raw_sha256", "acceptance_path", "acceptance_raw_sha256", "artifact_raw_sha256"):
            if key not in group:
                fail(f"{group_name} pin group missing {key}")
        if raw_sha(ROOT / group["manifest_path"]) != group["manifest_raw_sha256"]:
            fail(f"{group_name} manifest drift")
        if raw_sha(ROOT / group["acceptance_path"]) != group["acceptance_raw_sha256"]:
            fail(f"{group_name} acceptance drift")
        for relative, expected in group["artifact_raw_sha256"].items():
            if raw_sha(ROOT / relative) != expected:
                fail(f"{group_name} artifact drift: {relative}")
    current_parent = load(PARENT_MANIFEST)
    if parent.get("source_file_sha256") != current_parent.get("source_file_sha256"):
        fail("accepted typed source pin map mismatch")
    for relative, expected in parent["source_file_sha256"].items():
        if raw_sha(ROOT / relative) != expected:
            fail(f"accepted typed source drift: {relative}")

    negative = manifest.get("rejected_snapshot_negative_evidence_only", {})
    if negative.get("authority") is not False:
        fail("rejected snapshot marked authoritative")
    for version in ("v0_1", "v0_2"):
        pins = negative.get(version)
        if not isinstance(pins, dict) or len(pins) != 9:
            fail(f"{version} negative pin count mismatch")
        for relative, expected in pins.items():
            if raw_sha(ROOT / relative) != expected:
                fail(f"{version} rejected snapshot drift: {relative}")
    rejection_path = negative.get("rejection_record_path")
    if raw_sha(ROOT / rejection_path) != negative.get("rejection_record_raw_sha256"):
        fail("v0.2 rejection record drift")


def schema_validation_error(schema: dict[str, Any]) -> str | None:
    root_keys = {
        "schema",
        "schema_version",
        "contract_id",
        "additional_properties",
        "primitive_types",
        "enums",
        "objects",
        "named_types",
        "hash_contract",
        "external_acceptance_rule",
        "forbidden_authority_patterns",
    }
    if set(schema) != root_keys:
        return "TPA_SCHEMA_UNKNOWN_KEY"
    if schema["contract_id"] != CONTRACT_ID or schema["additional_properties"] is not False:
        return "TPA_SCHEMA_NOT_CLOSED"
    if set(schema["objects"]) != REQUIRED_OBJECTS:
        return "TPA_SCHEMA_OBJECT_SET_MISMATCH"
    if set(schema["named_types"]) != REQUIRED_NAMED_TYPES:
        return "TPA_SCHEMA_NAMED_TYPE_SET_MISMATCH"
    if set(schema["enums"]) != REQUIRED_ENUMS:
        return "TPA_SCHEMA_ENUM_SET_MISMATCH"
    primitive_keys = {"json_type", "pattern", "patterns", "format", "discriminator"}
    for definition in schema["primitive_types"].values():
        if set(definition) != primitive_keys:
            return "TPA_SCHEMA_UNKNOWN_KEY"
        if definition["json_type"] not in {"string", "integer", "boolean", "object"}:
            return "TPA_SCHEMA_PRIMITIVE_INVALID"
    for values in schema["enums"].values():
        if not isinstance(values, list) or not values or len(values) != len(set(values)) or any(not isinstance(item, str) for item in values):
            return "TPA_SCHEMA_ENUM_INVALID"
    if set(schema["enums"]["ir_value_type"]) != IR_VALUE_TYPES:
        return "TPA_SCHEMA_IR_VALUE_ENUM_MISMATCH"
    if set(schema["enums"]["recipe_transform_op"]) != TRANSFORM_OPS:
        return "TPA_RECIPE_OP_INVALID"
    if set(schema["enums"]["recipe_condition_op"]) != CONDITION_OPS:
        return "TPA_RECIPE_CONDITION_OP_INVALID"

    field_keys = {"type", "nullable", "cardinality", "constraints"}
    definition_keys = {"additional_properties", "required", "optional", "properties", "conditional_rules"}
    constraint_keys = {"min_length", "const", "min_items", "sorted_unique", "minimum", "self_hash", "pattern"}
    declared = set(schema["primitive_types"]) | set(schema["objects"]) | set(schema["named_types"])
    for enum_name in schema["enums"]:
        declared.add(f"enum:{enum_name}")
    definitions = schema["objects"] | schema["named_types"]
    for definition in definitions.values():
        if set(definition) != definition_keys:
            return "TPA_SCHEMA_UNKNOWN_KEY"
        if definition["additional_properties"] is not False:
            return "TPA_SCHEMA_NOT_CLOSED"
        required = definition["required"]
        optional = definition["optional"]
        properties = definition["properties"]
        if (
            not isinstance(required, list)
            or not isinstance(optional, list)
            or set(required) & set(optional)
            or set(required) | set(optional) != set(properties)
            or len(required) != len(set(required))
            or len(optional) != len(set(optional))
        ):
            return "TPA_SCHEMA_REQUIRED_EXTRA"
        for field in properties.values():
            if set(field) != field_keys:
                return "TPA_SCHEMA_UNKNOWN_KEY"
            if field["type"] not in declared:
                return "TPA_SCHEMA_UNDEFINED_TYPE"
            if field["type"] in {"Any", "object", "free_form"}:
                return "TPA_SCHEMA_FREE_FORM_TYPE"
            if field["cardinality"] not in {"one", "many"} or not isinstance(field["nullable"], bool):
                return "TPA_SCHEMA_CARDINALITY_INVALID"
            if set(field["constraints"]) - constraint_keys:
                return "TPA_SCHEMA_UNKNOWN_KEY"
            if field["constraints"].get("self_hash") is True and field["type"] != "sha256":
                return "TPA_SCHEMA_SELF_HASH_TYPE_INVALID"
        for rule in definition["conditional_rules"]:
            allowed_rule_keys = {"when", "when_in", "requires_non_null", "requires_null", "requires", "requires_min_items", "requires_max_items"}
            if not isinstance(rule, dict) or set(rule) - allowed_rule_keys:
                return "TPA_SCHEMA_UNKNOWN_KEY"
            referenced: set[str] = set()
            for key in ("when", "when_in", "requires", "requires_min_items", "requires_max_items"):
                if key in rule:
                    if not isinstance(rule[key], dict):
                        return "TPA_SCHEMA_CONDITION_INVALID"
                    referenced.update(rule[key])
            for key in ("requires_non_null", "requires_null"):
                if key in rule:
                    if not isinstance(rule[key], list):
                        return "TPA_SCHEMA_CONDITION_INVALID"
                    referenced.update(rule[key])
            if not referenced.issubset(properties):
                return "TPA_SCHEMA_CONDITION_UNKNOWN_FIELD"

    for root in REQUIRED_OBJECTS - {"TemporalAuthorityScopeIdentity", "S4IdentityJoin"}:
        fields = schema["objects"][root]["properties"]
        if "scope_identity" not in fields and root != "TemporalProjectionAuthorityRegistry":
            return "TPA_SCHEMA_SCOPE_IDENTITY_MISSING"
        if not any(field["constraints"].get("self_hash") is True for field in fields.values()):
            return "TPA_SCHEMA_SELF_HASH_MISSING"
    if schema["objects"]["S4IdentityJoin"]["required"] != ["project_ref", "run_ref", "snapshot_ref", "cutoff_ref", "site_ref", "subject_ref", "risk_ref", "spine_ref"]:
        return "TPA_SCHEMA_S4_JOIN_INVALID"
    if schema["external_acceptance_rule"].get("candidate_receipt_is_authority") is not False:
        return "TPA_SCHEMA_CANDIDATE_AUTHORITY_ENABLED"
    if schema["external_acceptance_rule"].get("resolution_key") != ["registry_id", "registry_root_content_hash", "accepted_record_ref", "accepted_record_content_hash"]:
        return "TPA_SCHEMA_EXTERNAL_KEY_INVALID"
    serialized = json.dumps(schema, ensure_ascii=False).lower()
    for forbidden in ("nearest fallback", "expected_output_authority", "model_role_authority=true"):
        if forbidden in serialized:
            return "TPA_SCHEMA_FORBIDDEN_AUTHORITY"
    return None


def recursive_schema_diff(candidate: Any, baseline: Any, path: str = "$") -> str | None:
    if type(candidate) is not type(baseline):
        return path
    if isinstance(baseline, dict):
        if set(candidate) != set(baseline):
            return path
        for key in sorted(baseline):
            difference = recursive_schema_diff(candidate[key], baseline[key], f"{path}/{key}")
            if difference is not None:
                return difference
        return None
    if isinstance(baseline, list):
        if len(candidate) != len(baseline):
            return path
        for index, expected in enumerate(baseline):
            difference = recursive_schema_diff(candidate[index], expected, f"{path}/{index}")
            if difference is not None:
                return difference
        return None
    return None if candidate == baseline else path


def schema_baseline_error(candidate: dict[str, Any], baseline: dict[str, Any]) -> str | None:
    return None if recursive_schema_diff(candidate, baseline) is None else "TPA_SCHEMA_BASELINE_MISMATCH"


def verify_schema(schema: dict[str, Any], manifest: dict[str, Any]) -> None:
    baseline_section = manifest.get("accepted_schema_baseline")
    if not isinstance(baseline_section, dict) or set(baseline_section) != {"schema", "schema_content_hash"}:
        fail("accepted schema baseline section invalid")
    baseline = baseline_section["schema"]
    if canonical_digest(baseline) != EXPECTED_SCHEMA_BASELINE_CONTENT_HASH:
        fail("accepted schema baseline hard pin mismatch")
    if baseline_section["schema_content_hash"] != EXPECTED_SCHEMA_BASELINE_CONTENT_HASH:
        fail("accepted schema baseline content hash mismatch")
    if manifest.get("accepted_schema_baseline_content_hash_pin") != EXPECTED_SCHEMA_BASELINE_CONTENT_HASH:
        fail("accepted schema manifest pin mismatch")
    if schema_baseline_error(schema, baseline) is not None:
        fail("TPA_SCHEMA_BASELINE_MISMATCH: schema artifact differs from immutable baseline")
    error = schema_validation_error(schema)
    if error is not None:
        fail(f"{error}: recursive schema closure failed")


def validate_scalar(value: Any, type_name: str, schema: dict[str, Any], where: str) -> None:
    if type_name.startswith("enum:"):
        enum_name = type_name.split(":", 1)[1]
        if value not in schema["enums"][enum_name]:
            reject("TPA_TYPED_VALUE_ENUM", where)
        return
    if type_name in schema["objects"] or type_name in schema["named_types"]:
        validate_object_instance(value, type_name, schema, where)
        return
    primitive = schema["primitive_types"].get(type_name)
    if primitive is None:
        reject("TPA_SCHEMA_UNDEFINED_TYPE", where)
    json_type = primitive["json_type"]
    valid = (
        (json_type == "string" and isinstance(value, str))
        or (json_type == "integer" and isinstance(value, int) and not isinstance(value, bool))
        or (json_type == "boolean" and isinstance(value, bool))
        or (json_type == "object" and isinstance(value, dict))
    )
    if not valid:
        reject("TPA_TYPED_VALUE_TYPE", where)
    if primitive["pattern"] is not None and re.fullmatch(primitive["pattern"], value) is None:
        reject("TPA_TYPED_VALUE_PATTERN", where)
    if primitive["patterns"] and not any(re.fullmatch(pattern, value) for pattern in primitive["patterns"]):
        reject("TPA_TYPED_VALUE_PATTERN", where)
    if primitive["format"] == "date":
        try:
            dt.date.fromisoformat(value)
        except ValueError:
            reject("TPA_TYPED_VALUE_DATE", where)


def validate_field_value(value: Any, field: dict[str, Any], schema: dict[str, Any], where: str) -> None:
    if value is None:
        if not field["nullable"]:
            reject("TPA_TYPED_VALUE_NULL", where)
        return
    values = value if field["cardinality"] == "many" else [value]
    if field["cardinality"] == "many" and not isinstance(value, list):
        reject("TPA_TYPED_VALUE_CARDINALITY", where)
    constraints = field["constraints"]
    if len(values) < constraints.get("min_items", 0):
        reject("TPA_TYPED_VALUE_MIN_ITEMS", where)
    if constraints.get("sorted_unique") is True and values != sorted(set(values)):
        reject("TPA_TYPED_VALUE_ORDERING", where)
    for item in values:
        validate_scalar(item, field["type"], schema, where)
        if "const" in constraints and item != constraints["const"]:
            reject("TPA_TYPED_VALUE_CONST", where)
        if isinstance(item, str) and len(item) < constraints.get("min_length", 0):
            reject("TPA_TYPED_VALUE_MIN_LENGTH", where)
        if isinstance(item, int) and not isinstance(item, bool) and item < constraints.get("minimum", item):
            reject("TPA_TYPED_VALUE_MINIMUM", where)
        if "pattern" in constraints and re.fullmatch(constraints["pattern"], item) is None:
            reject("TPA_TYPED_VALUE_PATTERN", where)


def conditional_rule_applies(value: dict[str, Any], rule: dict[str, Any]) -> bool:
    if "when" in rule:
        return all(value.get(key) == expected for key, expected in rule["when"].items())
    if "when_in" in rule:
        return all(value.get(key) in expected for key, expected in rule["when_in"].items())
    return True


def validate_object_instance(value: Any, type_name: str, schema: dict[str, Any], where: str) -> None:
    if not isinstance(value, dict):
        reject("TPA_TYPED_OBJECT_TYPE", where)
    definitions = schema["objects"] | schema["named_types"]
    definition = definitions[type_name]
    required = set(definition["required"])
    allowed = required | set(definition["optional"])
    if not required.issubset(value) or not set(value).issubset(allowed):
        reject("TPA_TYPED_OBJECT_EXTRA_KEY", where)
    for field_name, field in definition["properties"].items():
        if field_name in value:
            validate_field_value(value[field_name], field, schema, f"{where}.{field_name}")
    for rule in definition["conditional_rules"]:
        if not conditional_rule_applies(value, rule):
            continue
        for field_name in rule.get("requires_non_null", []):
            if value[field_name] is None:
                reject("TPA_TYPED_CONDITION", f"{where}.{field_name}")
        for field_name in rule.get("requires_null", []):
            if value[field_name] is not None:
                reject("TPA_TYPED_CONDITION", f"{where}.{field_name}")
        for field_name, expected_value in rule.get("requires", {}).items():
            if value[field_name] != expected_value:
                reject("TPA_TYPED_CONDITION", f"{where}.{field_name}")
        for field_name, minimum in rule.get("requires_min_items", {}).items():
            if len(value[field_name]) < minimum:
                reject("TPA_TYPED_CONDITION", f"{where}.{field_name}")
        for field_name, maximum in rule.get("requires_max_items", {}).items():
            if len(value[field_name]) > maximum:
                reject("TPA_TYPED_CONDITION", f"{where}.{field_name}")
    for field_name, field in definition["properties"].items():
        if field_name in value and field["constraints"].get("self_hash") is True:
            unhashed = dict(value)
            claimed = unhashed.pop(field_name)
            if claimed != canonical_digest(unhashed):
                reject("TPA_TYPED_SELF_HASH_MISMATCH", where)
    if type_name == "AuthorityFixture":
        object_type = value["object_type"]
        if object_type not in schema["objects"]:
            reject("TPA_AUTHORITY_FIXTURE_TYPE", where)
        validate_object_instance(value["value"], object_type, schema, f"{where}.value")
        if value["content_hash_field"] not in schema["objects"][object_type]["properties"]:
            reject("TPA_AUTHORITY_FIXTURE_HASH_FIELD", where)
    if type_name == "TypedValue":
        validate_typed_value_payload(value, where)


def validate_typed_value_payload(value: dict[str, Any], where: str) -> None:
    value_type = value["value_type"]
    populated = {
        "string_value": value["string_value"] is not None,
        "integer_value": value["integer_value"] is not None,
        "boolean_value": value["boolean_value"] is not None,
        "string_list_value": bool(value["string_list_value"]),
        "integer_list_value": bool(value["integer_list_value"]),
        "object_ref": value["object_ref"] is not None,
    }
    expected_field = {
        "string": "string_value",
        "date": "string_value",
        "sha256": "string_value",
        "integer": "integer_value",
        "boolean": "boolean_value",
        "string_list": "string_list_value",
        "date_list": "string_list_value",
        "sha256_list": "string_list_value",
        "integer_list": "integer_list_value",
        "external_candidate_bundle": "object_ref",
        "external_registry_root": "object_ref",
    }[value_type]
    for field_name, is_populated in populated.items():
        if field_name != expected_field and is_populated:
            reject("TPA_TYPED_VALUE_UNION", where)
    if value_type not in {"string_list", "date_list", "sha256_list", "integer_list"} and not populated[expected_field]:
        reject("TPA_TYPED_VALUE_UNION", where)
    if value_type == "sha256" and re.fullmatch(r"[0-9a-f]{64}", value["string_value"]) is None:
        reject("TPA_TYPED_VALUE_PATTERN", where)
    if value_type == "date":
        try:
            dt.date.fromisoformat(value["string_value"])
        except ValueError:
            reject("TPA_TYPED_VALUE_DATE", where)
    if value_type == "date_list":
        for item in value["string_list_value"]:
            try:
                dt.date.fromisoformat(item)
            except ValueError:
                reject("TPA_TYPED_VALUE_DATE", where)
    if value_type == "sha256_list" and any(re.fullmatch(r"[0-9a-f]{64}", item) is None for item in value["string_list_value"]):
        reject("TPA_TYPED_VALUE_PATTERN", where)


def parent_leaf_universe() -> set[str]:
    universe: set[str] = set()
    for contract, path in (("subject-temporal-public-v1", SUBJECT_SCHEMA), ("aemh-match-history-public-v1", AEMH_SCHEMA)):
        schema = load(path)
        for object_name, fields in schema["objects"].items():
            for field in fields:
                universe.add(f"{contract}::{object_name}.{field}")
    return universe


def verify_source_matrix(matrix: dict[str, Any], manifest: dict[str, Any]) -> None:
    exact_keys(matrix, {"schema", "schema_version", "contract_id", "accepted_parent_manifest_raw_sha256", "accepted_semantic_manifest_raw_sha256", "accepted_source_file_sha256", "accepted_parent_artifact_sha256", "accepted_semantic_artifact_sha256", "rows", "row_count", "global_rules"}, "source matrix root")
    if matrix["row_count"] != len(matrix["rows"]) or matrix["row_count"] < 18:
        fail("source matrix row count")
    if matrix["accepted_parent_manifest_raw_sha256"] != raw_sha(PARENT_MANIFEST):
        fail("source matrix parent manifest pin")
    if matrix["accepted_semantic_manifest_raw_sha256"] != raw_sha(SEMANTIC_MANIFEST):
        fail("source matrix semantic manifest pin")
    if matrix["accepted_source_file_sha256"] != manifest["accepted_parent_pins"]["source_file_sha256"]:
        fail("source matrix accepted typed pin map")
    row_keys = {"authority_root", "accepted_typed_inputs", "accepted_semantic_inputs", "output_contracts", "exact_join", "cardinality", "fallback", "forbidden"}
    roots = []
    for row in matrix["rows"]:
        exact_keys(row, row_keys, "source matrix row")
        if row["fallback"] != "fail_closed_no_nearest":
            fail("source matrix fallback drift")
        if row["authority_root"] in roots:
            fail("duplicate source matrix authority root")
        roots.append(row["authority_root"])
    if not {"CutoffEndpointBindingAuthority", "PublicScopeUniverseAuthority", "SourceLocatorRevisionBinding", "AEMHAppendDecisionAuthorityRecord", "AEMHEvidenceBindingAuthority", "AEMHThreadMembershipAuthority"}.issubset(roots):
        fail("source matrix missing required systemic authority roots")


def verify_typed_source_paths(matrix: dict[str, Any], manifest: dict[str, Any]) -> None:
    module_inventory: dict[str, dict[str, set[str]]] = {}
    for relative in manifest["accepted_parent_pins"]["source_file_sha256"]:
        if not relative.endswith(".py"):
            continue
        marker = "/src/"
        if marker not in relative:
            continue
        module = relative.split(marker, 1)[1][:-3].replace("/", ".")
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"), filename=relative)
        classes: dict[str, set[str]] = {}
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            fields = {
                item.target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            }
            classes[node.name] = fields
        module_inventory[module] = classes
    unresolved: list[str] = []
    for row in matrix["rows"]:
        for source in row["accepted_typed_inputs"]:
            if not source.startswith("mm_"):
                continue
            resolved = False
            for module, classes in module_inventory.items():
                prefix = module + "."
                if not source.startswith(prefix):
                    continue
                tail = source[len(prefix):]
                class_name, separator, field_path = tail.partition(".")
                if class_name not in classes:
                    continue
                if separator and field_path.split(".", 1)[0] not in classes[class_name]:
                    continue
                resolved = True
                break
            if not resolved:
                unresolved.append(source)
    if unresolved:
        fail("unresolved actual typed source paths: " + ", ".join(sorted(set(unresolved))))


def independently_expected_d_emitter(contract: str, leaf: str) -> tuple[str, str]:
    owner, field = leaf.split(".", 1)
    if owner == "PublicCutoffEndpoint" or (owner == "PublicScopeIdentity" and field == "cutoff_state"):
        return "recipe", "recipe.cutoff_exact_present_absent"
    if owner == "VisibilityClosure":
        return "recipe", "recipe.visibility_universe_and_stable_bridge"
    if owner in {"PublicSourceLocator", "SourceRevisionContentPair"}:
        return "recipe", "recipe.locator_total_consumption_revision_partition"
    direct_roots = {
        "TemporalAxisBasis": "TemporalAxisAuthorityRecord",
        "TemporalDateEndpoint": "TemporalEndpointAuthorityRecord",
        "TemporalVisit": "VisitProjectionBinding",
        "TemporalEvent": "EventProjectionBinding",
        "TemporalPhaseBand": "PhaseProjectionBinding",
        "TemporalRiskAnchor": "RiskProjectionBinding",
        "TemporalDomainTrack": "DomainApplicabilityAuthorityRecord",
        "TemporalMembershipIndex": "TemporalMemberAuthorityRecord",
        "AEMHMatchHistoryEntry": "AEMHAppendDecisionAuthorityRecord",
        "AEMHDecisionAuthorityRegistry": "AEMHAppendDecisionAuthorityRecord",
        "AEMHThreadPrefixAnchor": "AEMHAppendDecisionAuthorityRecord",
        "AEMHIdentityEvidence": "AEMHEvidenceBindingAuthority",
        "AEMHMatchThread": "AEMHThreadMembershipAuthority",
        "AEMHHistoryMembershipIndex": "AEMHThreadMembershipAuthority",
    }
    if owner in direct_roots:
        return "authority_root", direct_roots[owner]
    if owner == "TemporalPendingDateItem":
        return "recipe", "recipe.pending_union_from_unprojectable_targets"
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
        return (
            ("authority_root", "TemporalProjectionAcceptanceReceipt")
            if field == "receipt"
            else ("authority_root", "TemporalProjectionAuthorityRegistry")
        )
    if owner == "SubjectTemporalPublicProjection":
        roots = {
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
        if field in roots:
            return "authority_root", roots[field]
    if owner == "AEMHMatchHistoryPublicProjection":
        roots = {
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
        if field in roots:
            return "authority_root", roots[field]
    fail(f"independent verifier has no exact emitter for {contract}::{leaf}")


def verify_recipes(registry: dict[str, Any], schema: dict[str, Any], manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    expected_root_keys = {
        "schema",
        "schema_version",
        "contract_id",
        "authority_scope",
        "non_clinical",
        "external_registry_reference",
        "controlled_policies",
        "controlled_policy_content_hashes",
        "recipe_count",
        "recipe_content_hashes",
        "accepted_recipe_registry_reference",
        "candidate_supplies_recipe_definition",
        "coverage_ledger",
        "authority_leaf_outputs",
        "authority_output_registry",
        "authority_output_registry_content_hash",
        "authority_mapping_count",
        "executable_authority_mapping_count",
        "authority_leaf_without_emitter_count",
        "recipe_authority_binding_registry",
        "recipe_authority_binding_registry_content_hash",
        "unique_dependency_slice_count",
        "min_dependency_count",
        "max_dependency_count",
        "median_dependency_count",
        "mappings_with_all_19_count",
        "unused_declared_dependency_count",
        "authority_op_counts",
        "op_branch_positive_coverage",
        "exact_leaf_output_bijection_count",
        "nominal_mapping_count",
        "coverage_counts_before",
        "coverage_counts_before_by_contract",
        "coverage_counts_after",
        "total_leaf_count",
        "former_d_leaf_count",
        "unexplained_leaf_count",
        "construction_order",
    }
    exact_keys(registry, expected_root_keys, "recipe registry root")
    if registry["authority_scope"] != "synthetic_test_only" or registry["non_clinical"] is not True:
        fail("registry synthetic/non-clinical boundary")
    if registry["candidate_supplies_recipe_definition"] is not False:
        fail("candidate recipe definition boundary")
    authority_registry = manifest.get("accepted_authority_output_registry")
    if authority_registry != registry["authority_output_registry"]:
        fail("TPA_AUTHORITY_REGISTRY_PIN_MISMATCH: runtime registry differs from manifest-owned registry")
    if canonical_digest({key: value for key, value in authority_registry.items() if key != "registry_content_hash"}) != authority_registry.get("registry_content_hash"):
        fail("TPA_AUTHORITY_REGISTRY_PIN_MISMATCH: authority registry self hash")
    if authority_registry.get("registry_content_hash") != EXPECTED_AUTHORITY_OUTPUT_REGISTRY_CONTENT_HASH:
        fail("TPA_AUTHORITY_REGISTRY_PIN_MISMATCH: authority registry hard pin")
    if manifest.get("accepted_authority_output_registry_content_hash_pin") != EXPECTED_AUTHORITY_OUTPUT_REGISTRY_CONTENT_HASH:
        fail("TPA_AUTHORITY_REGISTRY_PIN_MISMATCH: manifest authority registry pin")
    if manifest.get("accepted_authority_mapping_count") != 119 or authority_registry.get("mapping_count") != 119:
        fail("authority mapping count mismatch")
    if registry["authority_mapping_count"] != 119 or registry["executable_authority_mapping_count"] != 119 or registry["authority_leaf_without_emitter_count"] != 0:
        fail("authority executable emitter count mismatch")
    binding_registry = manifest.get("accepted_recipe_authority_binding_registry")
    if binding_registry != registry["recipe_authority_binding_registry"]:
        fail("TPA_RECIPE_AUTHORITY_BINDING_MISMATCH: runtime binding registry differs from manifest")
    if canonical_digest({key: value for key, value in binding_registry.items() if key != "registry_content_hash"}) != binding_registry.get("registry_content_hash"):
        fail("TPA_RECIPE_AUTHORITY_BINDING_MISMATCH: registry self hash")
    if binding_registry.get("registry_content_hash") != EXPECTED_RECIPE_AUTHORITY_BINDING_REGISTRY_CONTENT_HASH:
        fail("TPA_RECIPE_AUTHORITY_BINDING_MISMATCH: hard pin")
    if manifest.get("accepted_recipe_authority_binding_registry_content_hash_pin") != EXPECTED_RECIPE_AUTHORITY_BINDING_REGISTRY_CONTENT_HASH:
        fail("TPA_RECIPE_AUTHORITY_BINDING_MISMATCH: manifest pin")
    if binding_registry.get("binding_count") != 18:
        fail("recipe authority binding count mismatch")
    for binding in binding_registry["bindings"]:
        validate_object_instance(binding, "RecipeAuthorityBinding", schema, "recipe authority binding")
        if canonical_digest({key: value for key, value in binding.items() if key != "binding_content_hash"}) != binding["binding_content_hash"]:
            fail("recipe authority binding content hash mismatch")
    reference = registry["external_registry_reference"]
    exact_keys(reference, {"manifest_path", "section_pointer", "registry_id", "registry_root_content_hash", "accepted_record_ref", "accepted_record_content_hash", "section_canonical_sha256"}, "external registry reference")
    if "accepted_records" in registry or "synthetic_external_acceptance_registry" in registry:
        fail("candidate artifact embeds external registry authority")
    accepted_registry = manifest.get("accepted_recipe_registry")
    accepted_keys = {"registry_id", "contract_id", "schema_version", "authority_scope", "non_clinical", "recipes", "recipe_count", "recipe_content_hashes", "registry_content_hash"}
    exact_keys(accepted_registry, accepted_keys, "manifest accepted recipe registry")
    if accepted_registry["registry_content_hash"] != EXPECTED_ACCEPTED_RECIPE_REGISTRY_CONTENT_HASH:
        fail("TPA_ACCEPTED_RECIPE_PIN_MISMATCH: registry hard pin")
    if manifest.get("accepted_recipe_registry_content_hash_pin") != EXPECTED_ACCEPTED_RECIPE_REGISTRY_CONTENT_HASH:
        fail("TPA_ACCEPTED_RECIPE_PIN_MISMATCH: manifest registry pin")
    if manifest.get("accepted_recipe_count") != 18 or accepted_registry["recipe_count"] != 18:
        fail("accepted recipe count mismatch")
    if manifest.get("accepted_recipe_content_hash_pins") != EXPECTED_RECIPE_CONTENT_HASHES:
        fail("TPA_ACCEPTED_RECIPE_PIN_MISMATCH: manifest per-recipe pins")
    if accepted_registry["recipe_content_hashes"] != EXPECTED_RECIPE_CONTENT_HASHES:
        fail("TPA_ACCEPTED_RECIPE_PIN_MISMATCH: registry per-recipe pins")
    unhashed_registry = dict(accepted_registry)
    claimed_registry_hash = unhashed_registry.pop("registry_content_hash")
    if canonical_digest(unhashed_registry) != claimed_registry_hash:
        fail("TPA_ACCEPTED_RECIPE_PIN_MISMATCH: registry self hash")
    reference = registry["accepted_recipe_registry_reference"]
    expected_reference = {
        "manifest_path": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json",
        "section_pointer": "/accepted_recipe_registry",
        "registry_id": accepted_registry["registry_id"],
        "registry_content_hash": EXPECTED_ACCEPTED_RECIPE_REGISTRY_CONTENT_HASH,
        "recipe_count": 18,
        "recipe_content_hashes": EXPECTED_RECIPE_CONTENT_HASHES,
    }
    if reference != expected_reference or registry["recipe_content_hashes"] != EXPECTED_RECIPE_CONTENT_HASHES:
        fail("TPA_ACCEPTED_RECIPE_PIN_MISMATCH: candidate recipe reference")

    ids: list[str] = []
    for recipe in accepted_registry["recipes"]:
        validate_object_instance(recipe, "AcceptedRecipeDefinition", schema, "accepted recipe")
        unhashed_recipe = dict(recipe)
        claimed_recipe_hash = unhashed_recipe.pop("recipe_content_hash")
        if canonical_digest(unhashed_recipe) != claimed_recipe_hash or EXPECTED_RECIPE_CONTENT_HASHES.get(recipe["recipe_id"]) != claimed_recipe_hash:
            fail(f"TPA_ACCEPTED_RECIPE_PIN_MISMATCH: {recipe['recipe_id']}")
        ids.append(recipe["recipe_id"])
        if recipe["fallback"] != "fail_closed_no_nearest" or not recipe["transforms"] or not recipe["conditions"] or not recipe["outputs"]:
            fail(f"recipe incomplete: {recipe['recipe_id']}")
        input_types: dict[str, str] = {}
        for item in recipe["inputs"]:
            validate_object_instance(item, "RecipeInputSpec", schema, f"{recipe['recipe_id']}.input")
            if item["input_id"] in input_types:
                fail(f"duplicate recipe input: {recipe['recipe_id']}")
            input_types[item["input_id"]] = item["value_type"]
            if item["source_kind"] == "manifest_pin" and item["input_id"] != "external_registry_root":
                fail(f"undeclared manifest input: {recipe['recipe_id']}")
        node_types: dict[str, str] = {}
        used_inputs: set[str] = set()
        for transform in recipe["transforms"]:
            validate_object_instance(transform, "RecipeTransform", schema, f"{recipe['recipe_id']}.transform")
            if transform["op"] not in TRANSFORM_OPS:
                fail("TPA_RECIPE_OP_INVALID")
            if transform["node_id"] in node_types:
                fail(f"duplicate recipe node: {recipe['recipe_id']}")
            verify_recipe_refs(transform["args"], input_types, node_types, used_inputs, recipe["recipe_id"])
            node_types[transform["node_id"]] = transform["output_type"]
        condition_codes = []
        for condition in recipe["conditions"]:
            validate_object_instance(condition, "RecipeCondition", schema, f"{recipe['recipe_id']}.condition")
            if condition["op"] not in CONDITION_OPS:
                fail("TPA_RECIPE_CONDITION_OP_INVALID")
            verify_recipe_refs(condition["args"], input_types, node_types, used_inputs, recipe["recipe_id"])
            condition_codes.append(condition["error_code"])
        for output in recipe["outputs"]:
            validate_object_instance(output, "RecipeOutputSpec", schema, f"{recipe['recipe_id']}.output")
            verify_recipe_refs([output["source_ref"]], input_types, node_types, used_inputs, recipe["recipe_id"])
            if output["source_ref"]["value_type"] != output["value_type"]:
                fail(f"recipe output type drift: {recipe['recipe_id']}")
            if output["target_leaf"] is None and output["dependency_refs"]:
                fail(f"non-leaf recipe output has leaf dependencies: {recipe['recipe_id']}")
            if output["target_leaf"] is not None and (output["fixture_asserted"] is not False or not output["dependency_refs"]):
                fail(f"leaf output assertion/dependency contract drift: {recipe['recipe_id']}")
        if not any(output["fixture_asserted"] for output in recipe["outputs"]):
            fail(f"recipe lacks fixture-asserted output: {recipe['recipe_id']}")
        validate_object_instance(recipe["canonicalization"], "RecipeCanonicalization", schema, f"{recipe['recipe_id']}.canonicalization")
        if recipe["fail_codes"] != sorted(set(condition_codes)):
            fail(f"recipe fail-code closure mismatch: {recipe['recipe_id']}")
        fixture_inputs = {item["input_id"] for item in recipe["inputs"] if item["source_kind"] == "fixture"}
        if used_inputs != fixture_inputs:
            fail(f"recipe input not consumed exactly: {recipe['recipe_id']} missing={sorted(fixture_inputs-used_inputs)}")
        serialized_recipe = json.dumps(recipe, ensure_ascii=False).lower()
        for prose in ("trust the supplied", "target output", "expected output", "copy target", "mirror output"):
            if prose in serialized_recipe:
                fail(f"arbitrary prose recipe operation: {recipe['recipe_id']}")
    if set(ids) != REQUIRED_RECIPE_IDS or len(ids) != len(set(ids)) or registry["recipe_count"] != len(ids):
        fail("recipe exact set/count mismatch")
    policies = registry["controlled_policies"]
    expected_policy_names = {"phase_code_to_native_zh", "timezone_day_zero", "date_state_range_projection", "empty_domain_applicability", "aemh_event_match_reason_transitions"}
    if set(policies) != expected_policy_names:
        fail("controlled policy exact set mismatch")
    for name, policy in policies.items():
        if canonical_digest(policy) != registry["controlled_policy_content_hashes"].get(name):
            fail(f"controlled policy hash mismatch: {name}")
    accepted_policy_hashes = {
        item["policy_ref"]: item["policy_content_hash"]
        for item in manifest["external_acceptance_registry_root"]["accepted_records"][0]["policy_hashes"]
    }
    if registry["controlled_policy_content_hashes"] != accepted_policy_hashes:
        fail("controlled policy payloads do not match immutable accepted record")
    if policies["phase_code_to_native_zh"] != {"baseline": "基线期", "follow_up": "随访期", "screening": "筛选期", "treatment": "治疗期", "unscheduled": "非计划阶段"}:
        fail("phase native Chinese lexicon mismatch")
    if policies["timezone_day_zero"].get("timezone") != "Asia/Shanghai":
        fail("timezone policy drift")
    if policies["aemh_event_match_reason_transitions"].get("risk_lifecycle_effect") != "none":
        fail("AE/MH transition policy mutates lifecycle")

    universe = parent_leaf_universe()
    ledger = registry["coverage_ledger"]
    ledger_keys = {"contract", "leaf", "before_status", "before_basis", "post_delta_status", "closure_kind", "closure_ref", "target_output_path", "dependency_chain", "nominal_mapping", "unexplained"}
    keyed: set[str] = set()
    before: dict[str, int] = {}
    per_contract: dict[str, dict[str, int]] = {}
    authority_roots = set(schema["objects"])
    recipe_map = {recipe["recipe_id"]: recipe for recipe in accepted_registry["recipes"]}
    authority_declarations = {
        item["qualified_leaf"]: item
        for item in registry["authority_leaf_outputs"]
    }
    if registry["authority_leaf_outputs"] != authority_registry["mappings"]:
        fail("TPA_AUTHORITY_REGISTRY_PIN_MISMATCH: mapping list differs from manifest registry")
    for mapping in authority_registry["mappings"]:
        validate_object_instance(mapping, "AuthorityOutputMapping", schema, "authority output mapping")
        unhashed_mapping = {key: value for key, value in mapping.items() if key != "mapping_content_hash"}
        if canonical_digest(unhashed_mapping) != mapping["mapping_content_hash"]:
            fail("authority mapping content hash mismatch")
    dependency_counts = sorted(len(mapping["source_fixture_refs"]) + len(mapping["source_field_paths"]) for mapping in authority_registry["mappings"])
    unique_slices = len({(tuple(mapping["source_fixture_refs"]), tuple(mapping["source_field_paths"])) for mapping in authority_registry["mappings"]})
    expected_dependency_stats = {
        "unique_dependency_slice_count": unique_slices,
        "min_dependency_count": dependency_counts[0],
        "max_dependency_count": dependency_counts[-1],
        "median_dependency_count": dependency_counts[len(dependency_counts) // 2],
        "mappings_with_all_19_count": sum(1 for mapping in authority_registry["mappings"] if len(mapping["source_fixture_refs"]) == 19),
        "unused_declared_dependency_count": 0,
    }
    if unique_slices <= 1 or expected_dependency_stats["mappings_with_all_19_count"] != 0:
        fail("authority dependency slices remain class-wide")
    if any(registry[key] != value for key, value in expected_dependency_stats.items()):
        fail("authority dependency slice statistics mismatch")
    projection_ops = ("direct_field", "derive_value", "project_record", "assemble_sorted_records", "canonical_hash", "project_contract")
    expected_op_counts = {op: sum(1 for mapping in authority_registry["mappings"] if mapping["op"] == op) for op in projection_ops}
    if registry["authority_op_counts"] != expected_op_counts or registry["op_branch_positive_coverage"] != {op: count > 0 for op, count in expected_op_counts.items()}:
        fail("authority op branch coverage mismatch")
    if any(count <= 0 for count in expected_op_counts.values()):
        fail("authority op branch lacks positive fixture")
    if len(authority_declarations) != len(registry["authority_leaf_outputs"]):
        fail("duplicate authority leaf output declaration")
    recipe_leaf_mappings = 0
    for row in ledger:
        exact_keys(row, ledger_keys, "coverage row")
        key = f"{row['contract']}::{row['leaf']}"
        if key in keyed:
            fail(f"duplicate coverage leaf: {key}")
        keyed.add(key)
        before[row["before_status"]] = before.get(row["before_status"], 0) + 1
        bucket = per_contract.setdefault(row["contract"], {})
        bucket[row["before_status"]] = bucket.get(row["before_status"], 0) + 1
        if row["unexplained"] is not False:
            fail(f"unexplained coverage leaf: {key}")
        if row["nominal_mapping"] is not False or not row["dependency_chain"]:
            fail(f"nominal or dependency-free leaf mapping: {key}")
        if row["closure_kind"] == "recipe":
            recipe = recipe_map.get(row["closure_ref"])
            if recipe is None:
                fail(f"leaf recipe missing: {key}")
            matches = [output for output in recipe["outputs"] if output["target_leaf"] == key]
            if len(matches) != 1:
                fail(f"TPA_LEAF_OUTPUT_NOT_DECLARED: {key}")
            expected_path = f"{row['closure_ref']}::outputs::{key}"
            if row["target_output_path"] != expected_path or matches[0]["output_id"] != f"leaf::{key}":
                fail(f"leaf recipe output path mismatch: {key}")
            if matches[0]["dependency_refs"] != sorted(row["dependency_chain"]):
                fail(f"leaf recipe dependency mismatch: {key}")
            recipe_leaf_mappings += 1
        elif row["closure_kind"] == "authority_root":
            declaration = authority_declarations.get(key)
            if declaration is None:
                fail(f"authority leaf output not declared: {key}")
            if declaration["authority_root"] != row["closure_ref"] or declaration["output_path"] != row["target_output_path"]:
                fail(f"authority leaf output mismatch: {key}")
            if declaration["dependency_refs"] != row["dependency_chain"]:
                fail(f"authority leaf dependency mismatch: {key}")
        if row["before_status"] == "D_unconstructible":
            expected_kind, expected_ref = independently_expected_d_emitter(row["contract"], row["leaf"])
            if (row["closure_kind"], row["closure_ref"]) != (expected_kind, expected_ref):
                fail(f"independent leaf emitter mismatch: {key}")
            if row["closure_kind"] == "authority_root" and row["closure_ref"] not in authority_roots:
                fail(f"D leaf authority root missing: {key}")
            if row["closure_kind"] == "recipe" and row["closure_ref"] not in REQUIRED_RECIPE_IDS:
                fail(f"D leaf recipe missing: {key}")
            if row["closure_kind"] not in {"authority_root", "recipe"}:
                fail(f"D leaf dishonest closure kind: {key}")
        else:
            expected_ref = "accepted_semantic_delta_manifest" if row["before_status"] == "C_accepted_semantic" else "accepted_parent_manifest"
            if row["closure_kind"] != "accepted_authority_leaf" or row["closure_ref"] != expected_ref:
                fail(f"preserved leaf emitter mismatch: {key}")
    if keyed != universe or len(ledger) != 272 or registry["total_leaf_count"] != 272:
        fail(f"272-leaf bijection mismatch missing={len(universe-keyed)} extra={len(keyed-universe)}")
    expected_before = {"A_direct": 53, "B_deterministic_derived": 46, "C_accepted_semantic": 4, "D_unconstructible": 169}
    if before != expected_before or registry["coverage_counts_before"] != expected_before:
        fail(f"before coverage counts mismatch: {before}")
    expected_contract = {
        "subject-temporal-public-v1": {"A_direct": 28, "B_deterministic_derived": 18, "C_accepted_semantic": 4, "D_unconstructible": 106},
        "aemh-match-history-public-v1": {"A_direct": 25, "B_deterministic_derived": 28, "D_unconstructible": 63},
    }
    if per_contract != expected_contract or registry["coverage_counts_before_by_contract"] != expected_contract:
        fail("per-contract coverage count mismatch")
    if registry["former_d_leaf_count"] != 169 or registry["unexplained_leaf_count"] != 0:
        fail("former D/unexplained count mismatch")
    expected_after: dict[str, int] = {}
    for row in ledger:
        expected_after[row["post_delta_status"]] = expected_after.get(row["post_delta_status"], 0) + 1
    if registry["coverage_counts_after"] != expected_after:
        fail("post-delta coverage counts mismatch")
    if registry["exact_leaf_output_bijection_count"] != 272 or registry["nominal_mapping_count"] != 0:
        fail("exact leaf-output bijection/nominal mapping mismatch")
    accepted_leaf_mappings = sum(1 for row in ledger if row["closure_kind"] == "accepted_authority_leaf")
    if len(authority_declarations) + recipe_leaf_mappings + accepted_leaf_mappings != 272:
        fail("leaf-output emitter bijection mismatch")
    return {recipe["recipe_id"]: recipe for recipe in accepted_registry["recipes"]}


def verify_recipe_refs(
    refs: list[dict[str, Any]],
    input_types: dict[str, str],
    node_types: dict[str, str],
    used_inputs: set[str],
    recipe_id: str,
) -> None:
    for ref in refs:
        if ref["ref_kind"] == "input":
            if input_types.get(ref["ref_id"]) != ref["value_type"]:
                fail(f"recipe input reference unresolved: {recipe_id}.{ref['ref_id']}")
            used_inputs.add(ref["ref_id"])
        elif ref["ref_kind"] == "node":
            if node_types.get(ref["ref_id"]) != ref["value_type"]:
                fail(f"recipe node reference unresolved or forward: {recipe_id}.{ref['ref_id']}")
        elif ref["ref_kind"] == "manifest":
            if ref != {"ref_kind": "manifest", "ref_id": "external_acceptance_registry_root", "value_type": "external_registry_root"}:
                fail(f"recipe manifest reference unresolved: {recipe_id}")
        else:
            fail(f"recipe ref kind invalid: {recipe_id}")


def typed_value_python(value: dict[str, Any], candidate_catalog: dict[str, dict[str, Any]]) -> Any:
    value_type = value["value_type"]
    if value_type in {"string", "date", "sha256"}:
        return value["string_value"]
    if value_type == "integer":
        return value["integer_value"]
    if value_type == "boolean":
        return value["boolean_value"]
    if value_type in {"string_list", "date_list", "sha256_list"}:
        return list(value["string_list_value"])
    if value_type == "integer_list":
        return list(value["integer_list_value"])
    if value_type == "external_candidate_bundle":
        if value["object_ref"] not in candidate_catalog:
            reject("TPA_CANDIDATE_FIXTURE_UNRESOLVED", value["object_ref"])
        return candidate_catalog[value["object_ref"]]
    reject("TPA_TYPED_VALUE_TYPE", value_type)


def flatten_hash_values(values: list[Any]) -> list[str]:
    flattened: list[str] = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(str(item) for item in value)
        elif isinstance(value, bool):
            flattened.append("true" if value else "false")
        else:
            flattened.append(str(value))
    return flattened


def sha256_join(values: list[Any], separator: str | None) -> str:
    joiner = "\u0000" if separator is None else separator
    return hashlib.sha256(joiner.join(flatten_hash_values(values)).encode("utf-8")).hexdigest()


def candidate_chain_valid(candidate: dict[str, Any], schema: dict[str, Any]) -> bool:
    try:
        validate_object_instance(candidate, "ExternalCandidateBundle", schema, "candidate")
    except ContractViolation:
        return False
    record = candidate["authority_record"]
    evidence = candidate["operational_evidence"]
    claim = candidate["registry_claim"]
    receipt = candidate["receipt"]
    return (
        claim["authority_record_content_hash"] == record["record_content_hash"]
        and receipt["candidate_ref"] == candidate["candidate_ref"]
        and receipt["registry_claim_content_hash"] == claim["claim_content_hash"]
        and receipt["authority_record_content_hash"] == record["record_content_hash"]
        and receipt["operational_evidence_content_hash"] == evidence["evidence_content_hash"]
    )


def resolve_ir_ref(
    ref: dict[str, Any],
    inputs: dict[str, Any],
    nodes: dict[str, Any],
    external_root: dict[str, Any],
) -> Any:
    if ref["ref_kind"] == "input":
        return inputs[ref["ref_id"]]
    if ref["ref_kind"] == "node":
        return nodes[ref["ref_id"]]
    if ref["ref_kind"] == "manifest" and ref["ref_id"] == "external_acceptance_registry_root":
        return external_root
    reject("TPA_RECIPE_REF_UNRESOLVED", ref["ref_id"])



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
        return {"subject-temporal-public-v1": subject_id, "aemh-match-history-public-v1": aemh_id}[contract]

    def execute_project_record(self, contract: str, owner: str, field: str, params: dict[str, Any] | None) -> Any:
        resolved = self._require_exact_params(params, {"selector_fixture_ref", "selector_object_type", "join_keys", "result_object_type", "result_field_path"})
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
        resolved = self._require_exact_params(params, {"member_fixture_refs", "member_object_type", "stable_identity_fields", "uniqueness_fields", "result_object_type", "result_field_path", "assembly_cardinality"})
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
        resolved = self._require_exact_params(params, {"target_object_type", "target_hash_field", "ingredient_target_fields", "algorithm", "canonicalization"})
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
        resolved = self._require_exact_params(params, {"contract", "source_owner_type", "source_field_path", "result_type", "result_cardinality", "projection_mode"})
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


def execute_transform(op: str, args: list[Any], params: dict[str, Any], external_root: dict[str, Any]) -> Any:
    if op == "identity":
        return copy.deepcopy(args[0])
    if op == "sorted_unique":
        return sorted(set(args[0]))
    if op == "set_union":
        return sorted(set().union(*[set(value) for value in args]))
    if op == "count":
        return len(args[0])
    if op == "study_day":
        anchor = dt.date.fromisoformat(args[0])
        event = dt.date.fromisoformat(args[1])
        difference = (event - anchor).days
        if args[2] == "anchor_is_day_one" and difference >= 0:
            return difference + 1
        return difference
    if op == "range_envelope":
        return [min(args[0]), max(args[0])]
    if op == "lookup_parallel":
        if len(args[0]) != len(args[1]) or args[2] not in args[0]:
            return ""
        return dict(zip(args[0], args[1]))[args[2]]
    if op == "if_empty_label":
        return params["expected_string"] if not args[0] else params["occurrence_value"]
    if op == "prefix_suffix":
        return args[1][len(args[0]) :]
    if op == "sha256_join":
        return sha256_join(args, params["separator"])
    if op == "resolve_external_record":
        return external_root["accepted_records"][0]["accepted_record_ref"]
    if op == "all_equal":
        return all(value == args[0] for value in args[1:])
    reject("TPA_RECIPE_OP_INVALID", op)


def condition_passes(op: str, args: list[Any], params: dict[str, Any], schema: dict[str, Any]) -> bool:
    if op == "equal":
        if len(args) == 2:
            return args[0] == args[1]
        expected = params["expected_string"] if params["expected_string"] is not None else params["expected_integer"]
        return args[0] == expected
    if op == "exact_count":
        return len(args[0]) == params["expected_integer"]
    if op == "list_equal":
        expected = args[1] if len(args) == 2 else params["allowed_strings"]
        return args[0] == expected
    if op == "set_partition":
        return set(args[0]) == set(args[1]) | set(args[2])
    if op == "disjoint":
        if isinstance(args[0], list) and isinstance(args[1], list):
            return set(args[0]).isdisjoint(args[1])
        return args[0] != args[1]
    if op == "member_of":
        allowed = args[1] if len(args) == 2 else params["allowed_strings"]
        return args[0] in allowed
    if op == "date_ordered":
        return args[0] == sorted(args[0])
    if op == "prefix":
        return args[1][: len(args[0])] == args[0]
    if op == "occurrence_at_most":
        return args[0].count(params["occurrence_value"]) <= params["expected_integer"]
    if op == "contiguous_integers":
        return args[0] == list(range(args[0][0], args[0][0] + len(args[0]))) if args[0] else True
    if op == "all_items_equal":
        return all(item == params["expected_string"] for item in args[0])
    if op == "candidate_chain_valid":
        return candidate_chain_valid(args[0], schema)
    if op == "external_registry_match":
        claim = args[0]["registry_claim"]
        return claim["registry_id"] == args[1]["registry_id"] and claim["registry_root_content_hash"] == args[1]["root_content_hash"]
    if op == "accepted_record_match":
        claim = args[0]["registry_claim"]
        accepted = args[1]["accepted_records"][0]
        return (
            claim["accepted_record_ref"] == accepted["accepted_record_ref"]
            and claim["accepted_record_content_hash"] == accepted["record_content_hash"]
            and args[0]["authority_record"] == accepted
        )
    if op == "cutoff_state_compatible":
        return args[0] == "present" and isinstance(args[1], str) and bool(args[1])
    if op == "endpoint_state_geometry_compatible":
        state, geometry, _exact_date, candidates, main_axis = args
        if state == "exact":
            return geometry == "point" and main_axis == "authorized"
        if state in {"partial", "conflicted"}:
            minimum = 1 if state == "partial" else 2
            return geometry in {"closed_interval", "open_start", "open_end"} and len(candidates) >= minimum and main_axis == "authorized"
        if state == "missing":
            return not candidates and main_axis == "forbidden"
        return False
    if op == "unscheduled_binding_valid":
        return args[0] != "unscheduled" or (args[1] == "" and args[2] != "")
    if op == "domain_state_compatible":
        if args[0]:
            return args[1] == "applicable" and not args[2]
        return args[1] in {"not_applicable", "not_provided"} and len(args[2]) == 1
    if op == "empty":
        return not args[0]
    if op == "sha256_join_matches":
        return sha256_join([args[0]], params["separator"]) == args[1]
    if op == "same_length":
        return len(args[0]) == len(args[1])
    if op == "exact_eight_join":
        return len(args[0]) == 8 and len(set(args[0])) == 8
    if op == "locator_partition":
        locators = []
        for assignment in args[1]:
            if assignment.count("=") != 1:
                return False
            locator, revision = assignment.split("=", 1)
            if not revision:
                return False
            locators.append(locator)
        return sorted(locators) == sorted(args[0]) and len(locators) == len(set(locators))
    if op == "allowed_transition":
        allowed = {"reminder_created": "match_decided", "match_decided": "withdrawn", "withdrawn": "reappeared"}
        return all(allowed.get(left) == right for left, right in zip(args[0], args[0][1:]))
    if op == "roles_exact":
        return args[0] == ["candidate", "later_fact"]
    reject("TPA_RECIPE_CONDITION_OP_INVALID", op)


def recipe_authority_binding_error(
    fixture: dict[str, Any],
    binding: dict[str, Any],
    authority_fixture_map: dict[str, dict[str, Any]],
) -> str | None:
    requirements = binding["requirements"]
    expected_refs = [requirement["fixture_ref"] for requirement in requirements]
    if fixture["recipe_id"] != binding["recipe_id"] or fixture["authority_fixture_refs"] != expected_refs:
        return "TPA_RECIPE_AUTHORITY_BINDING_MISMATCH"
    accepted_scope = authority_fixture_map["authority:TemporalAuthorityScopeIdentity"]["value"]
    for position, requirement in enumerate(requirements, 1):
        authority_fixture = authority_fixture_map.get(requirement["fixture_ref"])
        expected_role = f"{binding['recipe_id'].rsplit('.', 1)[1]}:{position}"
        if authority_fixture is None or authority_fixture["object_type"] != requirement["object_type"] or requirement["role"] != expected_role:
            return "TPA_RECIPE_AUTHORITY_BINDING_MISMATCH"
        if authority_fixture["fixture_content_hash"] != requirement["fixture_content_hash"]:
            return "TPA_RECIPE_AUTHORITY_BINDING_MISMATCH"
        scope = authority_fixture["value"].get("scope_identity")
        if scope is not None and any(scope[key] != accepted_scope[key] for key in requirement["scope_join_keys"]):
            return "TPA_RECIPE_AUTHORITY_SCOPE_MISMATCH"
    return None


def execute_recipe(
    recipe: dict[str, Any],
    fixture: dict[str, Any],
    candidate_catalog: dict[str, dict[str, Any]],
    external_root: dict[str, Any],
    schema: dict[str, Any],
    authority_fixture_map: dict[str, dict[str, Any]] | None = None,
    authority_binding: dict[str, Any] | None = None,
) -> tuple[str | None, dict[str, Any]]:
    if authority_fixture_map is not None and authority_binding is not None:
        binding_error = recipe_authority_binding_error(fixture, authority_binding, authority_fixture_map)
        if binding_error is not None:
            return binding_error, {}
    input_specs = {item["input_id"]: item for item in recipe["inputs"] if item["source_kind"] == "fixture"}
    fixture_values = {item["value_id"]: item for item in fixture["inputs"]}
    if set(input_specs) != set(fixture_values):
        return "TPA_FIXTURE_INPUT_SET_MISMATCH", {}
    inputs: dict[str, Any] = {}
    for input_id, spec in input_specs.items():
        value = fixture_values[input_id]
        if value["value_type"] != spec["value_type"]:
            return "TPA_FIXTURE_INPUT_TYPE_MISMATCH", {}
        inputs[input_id] = typed_value_python(value, candidate_catalog)
    nodes: dict[str, Any] = {}
    for transform in recipe["transforms"]:
        args = [resolve_ir_ref(ref, inputs, nodes, external_root) for ref in transform["args"]]
        nodes[transform["node_id"]] = execute_transform(transform["op"], args, transform["params"], external_root)
    for condition in recipe["conditions"]:
        args = [resolve_ir_ref(ref, inputs, nodes, external_root) for ref in condition["args"]]
        if not condition_passes(condition["op"], args, condition["params"], schema):
            return condition["error_code"], {}
    outputs = {
        output["output_id"]: resolve_ir_ref(output["source_ref"], inputs, nodes, external_root)
        for output in recipe["outputs"]
    }
    expected = {item["value_id"]: typed_value_python(item, candidate_catalog) for item in fixture["expected_outputs"]}
    asserted_outputs = {
        output["output_id"]: outputs[output["output_id"]]
        for output in recipe["outputs"]
        if output["fixture_asserted"]
    }
    if asserted_outputs != expected:
        return "TPA_EXPECTED_OUTPUT_MISMATCH", outputs
    return None, outputs


def verify_external_registry_root(
    manifest: dict[str, Any],
    registry: dict[str, Any],
    challenges: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    root = manifest.get("external_acceptance_registry_root")
    if manifest.get("external_registry_root_ownership") != "manifest_owned_contract_artifact_not_candidate_fixture":
        fail("external registry ownership boundary")
    if manifest.get("external_registry_root_content_hash_pin") != EXPECTED_EXTERNAL_REGISTRY_ROOT_CONTENT_HASH:
        fail("external registry manifest pin mismatch")
    if manifest.get("external_registry_section_canonical_sha256_pin") != EXPECTED_EXTERNAL_REGISTRY_SECTION_CANONICAL_SHA256:
        fail("external registry section canonical pin mismatch")
    validate_object_instance(root, "ExternalRegistryRoot", schema, "manifest.external_registry_root")
    if root["root_content_hash"] != EXPECTED_EXTERNAL_REGISTRY_ROOT_CONTENT_HASH:
        fail("external registry hard pin mismatch")
    if canonical_digest(root) != EXPECTED_EXTERNAL_REGISTRY_SECTION_CANONICAL_SHA256:
        fail("external registry canonical section bytes drift")
    reference = registry["external_registry_reference"]
    accepted = root["accepted_records"][0]
    expected_record_pins = {accepted["accepted_record_ref"]: EXPECTED_ACCEPTED_RECORD_CONTENT_HASH}
    if manifest.get("accepted_record_count") != 1 or manifest.get("accepted_record_content_hash_pins") != expected_record_pins:
        fail("accepted record count/content pins mismatch")
    if accepted["record_content_hash"] != EXPECTED_ACCEPTED_RECORD_CONTENT_HASH:
        fail("accepted record hard pin mismatch")
    expected_reference = {
        "manifest_path": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json",
        "section_pointer": "/external_acceptance_registry_root",
        "registry_id": root["registry_id"],
        "registry_root_content_hash": root["root_content_hash"],
        "accepted_record_ref": accepted["accepted_record_ref"],
        "accepted_record_content_hash": accepted["record_content_hash"],
        "section_canonical_sha256": EXPECTED_EXTERNAL_REGISTRY_SECTION_CANONICAL_SHA256,
    }
    if reference != expected_reference:
        fail("candidate registry reference does not resolve immutable manifest root")
    context_text = (ROOT / EXACT_PATHS[0]).read_text(encoding="utf-8")
    if EXPECTED_EXTERNAL_REGISTRY_ROOT_CONTENT_HASH not in context_text or EXPECTED_EXTERNAL_REGISTRY_SECTION_CANONICAL_SHA256 not in context_text:
        fail("context lacks external registry hard pin")
    candidate_catalog: dict[str, Any] = {}
    for candidate in challenges["external_candidate_fixtures"]:
        validate_object_instance(candidate, "ExternalCandidateBundle", schema, "external candidate")
        if candidate["candidate_ref"] in candidate_catalog:
            fail("duplicate external candidate fixture")
        candidate_catalog[candidate["candidate_ref"]] = candidate
    for candidate_ref in ("candidate:valid", "candidate:valid-operational-variant"):
        candidate = candidate_catalog.get(candidate_ref)
        if candidate is None or candidate["authority_record"] != accepted:
            fail("valid candidate authority record does not exactly equal accepted record")
    if candidate_catalog["candidate:valid"]["operational_evidence"] == candidate_catalog["candidate:valid-operational-variant"]["operational_evidence"]:
        fail("operational evidence variation fixture missing")
    if schema["external_acceptance_rule"].get("operational_evidence_carries_policy_semantics") is not False:
        fail("operational evidence may carry policy semantics")
    return candidate_catalog


def reseal_fixture(fixture: dict[str, Any]) -> None:
    content = dict(fixture)
    content.pop("fixture_content_hash", None)
    fixture["fixture_content_hash"] = canonical_digest(content)


def json_pointer_parts(pointer: str) -> list[str]:
    if pointer == "/":
        return []
    if not pointer.startswith("/"):
        reject("TPA_MUTATION_TARGET_UNRESOLVED", pointer)
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def json_pointer_get(document: Any, pointer: str) -> Any:
    current = document
    for part in json_pointer_parts(pointer):
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            reject("TPA_MUTATION_TARGET_UNRESOLVED", pointer)
    return current


def apply_json_pointer_mutation(document: Any, pointer: str, op: str, replacement: Any) -> Any:
    mutated = copy.deepcopy(document)
    parts = json_pointer_parts(pointer)
    if not parts:
        return copy.deepcopy(replacement) if op in {"replace", "copy"} else mutated
    parent_pointer = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
    parent = mutated if len(parts) == 1 else json_pointer_get(mutated, parent_pointer)
    key = parts[-1]
    value = json_pointer_get(mutated, replacement) if op == "copy" else replacement
    if isinstance(parent, list):
        if op == "append" and key == "-":
            parent.append(copy.deepcopy(value))
        elif op == "remove":
            parent.pop(int(key))
        elif op in {"replace", "copy"}:
            if key == "-":
                parent.append(copy.deepcopy(value))
            else:
                parent[int(key)] = copy.deepcopy(value)
        else:
            reject("TPA_MUTATION_TARGET_UNRESOLVED", pointer)
    elif isinstance(parent, dict):
        if op == "remove":
            if key not in parent:
                reject("TPA_MUTATION_TARGET_UNRESOLVED", pointer)
            parent.pop(key)
        elif op in {"replace", "append", "copy"}:
            parent[key] = copy.deepcopy(value)
        else:
            reject("TPA_MUTATION_TARGET_UNRESOLVED", pointer)
    else:
        reject("TPA_MUTATION_TARGET_UNRESOLVED", pointer)
    return mutated


def mutation_scalar(replacement: dict[str, Any]) -> Any:
    value_type = replacement["value_type"]
    if value_type == "string":
        return replacement["string_value"]
    if value_type == "integer":
        return replacement["integer_value"]
    if value_type == "boolean":
        return replacement["boolean_value"]
    reject("TPA_MUTATION_TARGET_UNRESOLVED", value_type)


def accepted_recipe_pin_error(accepted_registry: dict[str, Any]) -> str | None:
    content = dict(accepted_registry)
    claimed = content.pop("registry_content_hash", None)
    if claimed != canonical_digest(content) or claimed != EXPECTED_ACCEPTED_RECIPE_REGISTRY_CONTENT_HASH:
        return "TPA_ACCEPTED_RECIPE_PIN_MISMATCH"
    recipes = accepted_registry.get("recipes")
    if not isinstance(recipes, list):
        return "TPA_ACCEPTED_RECIPE_PIN_MISMATCH"
    actual: dict[str, str] = {}
    for recipe in recipes:
        if not isinstance(recipe, dict) or "recipe_id" not in recipe or "recipe_content_hash" not in recipe:
            return "TPA_ACCEPTED_RECIPE_PIN_MISMATCH"
        unhashed = dict(recipe)
        recipe_hash = unhashed.pop("recipe_content_hash")
        if canonical_digest(unhashed) != recipe_hash:
            return "TPA_ACCEPTED_RECIPE_PIN_MISMATCH"
        actual[recipe["recipe_id"]] = recipe_hash
    return None if actual == EXPECTED_RECIPE_CONTENT_HASHES else "TPA_ACCEPTED_RECIPE_PIN_MISMATCH"


def apply_typed_case_mutation(
    case: dict[str, Any],
    fixture_map: dict[str, dict[str, Any]],
    replacement_map: dict[str, dict[str, Any]],
    recipe_map: dict[str, dict[str, Any]],
    recipe_attack_map: dict[str, dict[str, Any]],
    schema: dict[str, Any],
    registry: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    mutation = case["mutation"]
    target_kind = mutation["target_kind"]
    replacement = mutation["replacement"]
    if target_kind == "positive_fixture":
        replacement_ref = replacement["string_value"]
        return None, copy.deepcopy(replacement_map[replacement_ref]), recipe_map[case["recipe_id"]]
    if target_kind in {"positive_fixture_input", "positive_fixture_expected_output"}:
        fixture = copy.deepcopy(fixture_map[case["fixture_id"]])
        bucket = "inputs" if target_kind == "positive_fixture_input" else "expected_outputs"
        matches = [index for index, value in enumerate(fixture[bucket]) if value["value_id"] == mutation["path"]]
        if len(matches) != 1:
            return "TPA_MUTATION_TARGET_UNRESOLVED", None, None
        fixture[bucket][matches[0]] = copy.deepcopy(replacement)
        reseal_fixture(fixture)
        return None, fixture, recipe_map[case["recipe_id"]]
    if target_kind == "accepted_recipe_registry":
        mutated_registry = apply_json_pointer_mutation(
            manifest["accepted_recipe_registry"],
            mutation["path"],
            mutation["op"],
            mutation_scalar(replacement),
        )
        return accepted_recipe_pin_error(mutated_registry), None, None
    if target_kind == "accepted_recipe_bundle":
        bundle_ref = replacement["string_value"]
        bundle = recipe_attack_map.get(bundle_ref)
        if bundle is None:
            return "TPA_MUTATION_TARGET_UNRESOLVED", None, None
        mutated_registry = copy.deepcopy(manifest["accepted_recipe_registry"])
        matches = [index for index, recipe in enumerate(mutated_registry["recipes"]) if recipe["recipe_id"] == bundle["recipe_id"]]
        if len(matches) != 1:
            return "TPA_MUTATION_TARGET_UNRESOLVED", None, None
        mutated_registry["recipes"][matches[0]] = copy.deepcopy(bundle["recipe"])
        return accepted_recipe_pin_error(mutated_registry), None, None
    if target_kind == "schema_baseline":
        replacement_value = mutation_scalar(replacement)
        mutated_schema = apply_json_pointer_mutation(schema, mutation["path"], mutation["op"], replacement_value)
        return schema_baseline_error(mutated_schema, manifest["accepted_schema_baseline"]["schema"]), None, None
    if target_kind == "coverage_mapping":
        mutated = copy.deepcopy(registry["coverage_ledger"])
        matches = [row for row in mutated if f"{row['contract']}::{row['leaf']}" == mutation["target_ref"]]
        if len(matches) != 1:
            return "TPA_MUTATION_TARGET_UNRESOLVED", None, None
        matches[0]["closure_kind"] = "recipe"
        matches[0]["closure_ref"] = replacement["string_value"]
        recipe = recipe_map.get(matches[0]["closure_ref"])
        declared = [] if recipe is None else [output for output in recipe["outputs"] if output["target_leaf"] == mutation["target_ref"]]
        return (None if len(declared) == 1 else "TPA_LEAF_OUTPUT_NOT_DECLARED"), None, None
    if target_kind == "coverage_ledger":
        mutated = copy.deepcopy(registry["coverage_ledger"])
        mutated.pop(int(mutation["path"]))
        keys = {f"{row['contract']}::{row['leaf']}" for row in mutated}
        return (None if keys == parent_leaf_universe() and len(mutated) == 272 else "TPA_LEAF_COVERAGE_GAP"), None, None
    return "TPA_MUTATION_TARGET_UNRESOLVED", None, None


def verify_recursive_instance_unknown_key_rejection(
    schema: dict[str, Any],
    fixture: dict[str, Any],
    recipe: dict[str, Any],
    authority_fixture: dict[str, Any],
    candidate: dict[str, Any],
    external_root: dict[str, Any],
) -> None:
    fixture_extra = copy.deepcopy(fixture)
    fixture_extra["inputs"][0]["unexpected_contract_key"] = "invalid"
    try:
        validate_object_instance(fixture_extra, "PositiveFixture", schema, "extra-key-probe")
    except ContractViolation as exc:
        if exc.code != "TPA_TYPED_OBJECT_EXTRA_KEY":
            fail(f"wrong nested extra-key error: {exc.code}")
    else:
        fail("nested fixture extra key was accepted")
    typed_probes = [
        (recipe["transforms"][0], "RecipeTransform", "recipe-transform"),
        (authority_fixture["value"], authority_fixture["object_type"], "authority-value"),
        (candidate["receipt"], "CandidateReceipt", "candidate-receipt"),
        (external_root["accepted_records"][0], "ExternalAcceptedRecord", "external-record"),
    ]
    for original, type_name, label in typed_probes:
        extra = copy.deepcopy(original)
        extra["unexpected_contract_key"] = "invalid"
        try:
            validate_object_instance(extra, type_name, schema, label)
        except ContractViolation as exc:
            if exc.code != "TPA_TYPED_OBJECT_EXTRA_KEY":
                fail(f"wrong extra-key error for {label}: {exc.code}")
        else:
            fail(f"extra key accepted for {label}")


def execute_authority_attack(
    case: dict[str, Any],
    authority_fixture_map: dict[str, dict[str, Any]],
    mapping_fixture_map: dict[str, dict[str, Any]],
    recipe_fixture_map: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
) -> str | None:
    mutation = case["mutation"]
    target_kind = mutation["target_kind"]
    path = mutation["path"]
    if target_kind == "authority_fixture_catalog":
        refs = mutation["replacement"]["string_list_value"]
        if path == "/fixture_id_value_cycle":
            base_refs = sorted(ref for ref in authority_fixture_map if ref.count(":") == 1)
            if len(refs) == 18 and set(refs) == set(base_refs) and refs != base_refs:
                return "TPA_AUTHORITY_FIXTURE_REF_IDENTITY_MISMATCH"
        if path == "/same_type_pair" and len(refs) == 2 and all(authority_fixture_map[ref]["object_type"] == "EventProjectionBinding" for ref in refs):
            swapped = [copy.deepcopy(authority_fixture_map[ref]) for ref in refs]
            swapped[0]["value"], swapped[1]["value"] = swapped[1]["value"], swapped[0]["value"]
            for fixture in swapped:
                fixture["fixture_content_hash"] = canonical_digest({key: value for key, value in fixture.items() if key != "fixture_content_hash"})
            accepted_pins = {
                pin
                for mapping in manifest["accepted_authority_output_registry"]["mappings"]
                for pin in mapping["source_fixture_content_hash_pins"]
            }
            if any(f"{fixture['fixture_id']}={fixture['fixture_content_hash']}" not in accepted_pins for fixture in swapped):
                return "TPA_AUTHORITY_FIXTURE_CONTENT_HASH_MISMATCH"
        return None
    if target_kind == "authority_fixture":
        mutated = copy.deepcopy(authority_fixture_map)
        event = mutated["authority:EventProjectionBinding"]
        event["value"]["scope_identity"]["project_ref"] = mutation["replacement"]["string_value"]
        base_scope = mutated["authority:TemporalAuthorityScopeIdentity"]["value"]
        if event["value"]["scope_identity"]["project_ref"] != base_scope["project_ref"]:
            return "TPA_AUTHORITY_SCOPE_MISMATCH"
        return None
    if target_kind == "authority_output_registry":
        mutated = copy.deepcopy(manifest["accepted_authority_output_registry"])
        if path.startswith("/mappings/op_substitution/"):
            _, _, _, source_op, target_op = path.split("/")
            mapping = next(item for item in mutated["mappings"] if item["op"] == source_op)
            mapping["op"] = target_op
            selected_param_fields = [
                name
                for name in ("direct_field_params", "derive_value_params", "project_record_params", "assemble_sorted_records_params", "canonical_hash_params", "project_contract_params")
                if mapping[name] is not None
            ]
            if selected_param_fields != [f"{source_op}_params"] or mapping[f"{target_op}_params"] is None:
                return "TPA_AUTHORITY_OP_PARAMS_MISMATCH"
            return None
        if path == "/mappings/0/source_field_paths/0":
            mutated["mappings"][0]["source_field_paths"][0] = mutation["replacement"]["string_value"]
        elif path == "/mappings/*/source_fixture_refs/global_union":
            global_refs = list(dict.fromkeys(ref for mapping in mutated["mappings"] for ref in mapping["source_fixture_refs"]))
            mapping = mutated["mappings"][0]
            if any(ref not in mapping["source_fixture_refs"] for ref in global_refs):
                return "TPA_AUTHORITY_UNUSED_DECLARED_DEPENDENCY"
            return None
        elif path == "/mappings/0/op/no_op":
            mapping = mutated["mappings"][0]
            contract, leaf = mapping["qualified_leaf"].split("::", 1)
            owner, field = leaf.split(".", 1)
            try:
                LazyAuthorityProjectionExecutor([authority_fixture_map[ref] for ref in mapping["source_fixture_refs"]]).execute(contract, owner, field, "no_op", None)
            except RuntimeError as exc:
                return str(exc)
            return None
        else:
            mutated["mappings"][0]["op"] = "project_contract"
            mapping_payload = {key: value for key, value in mutated["mappings"][0].items() if key != "mapping_content_hash"}
            mutated["mappings"][0]["mapping_content_hash"] = canonical_digest(mapping_payload)
            mutated["registry_content_hash"] = canonical_digest({key: value for key, value in mutated.items() if key != "registry_content_hash"})
        if mutated != manifest["accepted_authority_output_registry"] or mutated["registry_content_hash"] != EXPECTED_AUTHORITY_OUTPUT_REGISTRY_CONTENT_HASH:
            return "TPA_AUTHORITY_REGISTRY_PIN_MISMATCH"
        return None
    if target_kind == "recipe_authority_binding_registry":
        bindings = manifest["accepted_recipe_authority_binding_registry"]["bindings"]
        binding_map = {binding["recipe_id"]: binding for binding in bindings}
        fixtures = sorted(recipe_fixture_map.values(), key=lambda item: item["recipe_id"])
        authority_ref_lists = [fixture["authority_fixture_refs"] for fixture in fixtures]
        rotated = authority_ref_lists[1:] + authority_ref_lists[:1]
        if len(fixtures) == 18:
            for fixture, reassigned_refs in zip(fixtures, rotated):
                mutated_fixture = copy.deepcopy(fixture)
                mutated_fixture["authority_fixture_refs"] = reassigned_refs
                error = recipe_authority_binding_error(mutated_fixture, binding_map[fixture["recipe_id"]], authority_fixture_map)
                if error is not None:
                    return error
        return None
    if target_kind == "authority_mapping_fixture":
        if "/op_negative/" in path:
            op = path.rsplit("/", 1)[1]
            mapping = next(item for item in manifest["accepted_authority_output_registry"]["mappings"] if item["op"] == op)
            target = mapping_fixture_map[mapping["mapping_id"]]
            expected = json.loads(target["expected_target_canonical_json"])
            forged = {"forged_op": op, "original": expected}
            mutated_json = json.dumps(canonicalize(forged), ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True)
            if mutated_json != target["expected_target_canonical_json"]:
                return "TPA_AUTHORITY_EXPECTED_TARGET_MISMATCH"
            return None
        target = next(
            fixture
            for mapping_id, fixture in mapping_fixture_map.items()
            if next(mapping for mapping in manifest["accepted_authority_output_registry"]["mappings"] if mapping["mapping_id"] == mapping_id)["qualified_leaf"]
            == "subject-temporal-public-v1::SubjectTemporalPublicProjection.events"
        )
        expected = json.loads(target["expected_target_canonical_json"])
        if path.endswith("/drop"):
            expected.pop()
        elif path.endswith("/add"):
            forged = copy.deepcopy(expected[-1])
            forged["event_ref"] = "event_ref:forged"
            expected.append(forged)
        elif path.endswith("/reorder"):
            expected.reverse()
        mutated_json = json.dumps(canonicalize(expected), ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True)
        if mutated_json != target["expected_target_canonical_json"]:
            return "TPA_AUTHORITY_EXPECTED_TARGET_MISMATCH"
        return None
    return None


def validate_parent_projection_value(
    value: Any,
    type_name: str,
    cardinality: str,
    nullable: bool,
    parent_objects: dict[str, Any],
    parent_enums: dict[str, list[str]],
    where: str,
) -> None:
    if value is None:
        if not nullable:
            fail(f"TPA_AUTHORITY_OUTPUT_NULL: {where}")
        return
    values = value if cardinality == "many" else [value]
    if cardinality == "many" and not isinstance(value, list):
        fail(f"TPA_AUTHORITY_OUTPUT_CARDINALITY: {where}")
    for item in values:
        if type_name in parent_objects:
            if not isinstance(item, dict) or set(item) != set(parent_objects[type_name]):
                fail(f"TPA_AUTHORITY_OUTPUT_OBJECT_SHAPE: {where}")
            for field_name, field in parent_objects[type_name].items():
                validate_parent_projection_value(
                    item[field_name],
                    field["type"],
                    field["cardinality"],
                    field["nullable"],
                    parent_objects,
                    parent_enums,
                    f"{where}.{field_name}",
                )
        elif type_name.startswith("enum:"):
            if item not in parent_enums[type_name.split(":", 1)[1]]:
                fail(f"TPA_AUTHORITY_OUTPUT_ENUM: {where}")
        elif type_name in {"string", "date", "partial_date", "sha256"}:
            if not isinstance(item, str):
                fail(f"TPA_AUTHORITY_OUTPUT_SCALAR: {where}")
            if type_name == "sha256" and re.fullmatch(r"[0-9a-f]{64}", item) is None:
                fail(f"TPA_AUTHORITY_OUTPUT_HASH: {where}")
        elif type_name == "integer":
            if not isinstance(item, int) or isinstance(item, bool):
                fail(f"TPA_AUTHORITY_OUTPUT_INTEGER: {where}")
        elif type_name == "boolean":
            if not isinstance(item, bool):
                fail(f"TPA_AUTHORITY_OUTPUT_BOOLEAN: {where}")
        else:
            fail(f"TPA_AUTHORITY_OUTPUT_TYPE_UNRESOLVED: {where} -> {type_name}")


def verify_challenges(
    challenges: dict[str, Any],
    registry: dict[str, Any],
    manifest: dict[str, Any],
    schema: dict[str, Any],
    recipe_map: dict[str, dict[str, Any]],
) -> None:
    root_keys = {
        "schema",
        "schema_version",
        "contract_id",
        "external_candidate_fixtures",
        "authority_fixtures",
        "authority_mapping_positive_fixtures",
        "positive_fixtures",
        "replacement_positive_fixtures",
        "replacement_recipe_attack_bundles",
        "former_d_authority_root_families",
        "positive_fixture_count",
        "authority_mapping_positive_fixture_count",
        "semantic_typed_probe_count",
        "unconsumed_authority_fixture_ref_count",
        "generic_schema_mutation_case_count",
        "authority_op_counts",
        "op_branch_positive_coverage",
        "cross_op_substitution_control_count",
        "op_specific_negative_output_count",
        "structural_coverage_probe_count",
        "cases",
        "case_count",
        "leaf_bijection_case_count",
        "active_attack_case_count",
        "single_mutation_per_case",
        "distinct_case_ids",
        "expected_oracle",
    }
    exact_keys(challenges, root_keys, "challenge root")
    if challenges["positive_fixture_count"] != 18 or challenges["authority_mapping_positive_fixture_count"] != 119 or challenges["semantic_typed_probe_count"] != 283 or challenges["structural_coverage_probe_count"] != 272:
        fail("semantic/structural probe counts mismatch")
    if challenges["unconsumed_authority_fixture_ref_count"] != 0:
        fail("unconsumed authority fixture refs reported")
    if challenges["case_count"] != 418 or challenges["leaf_bijection_case_count"] != 272 or challenges["active_attack_case_count"] != 146:
        fail("challenge counts mismatch")
    if challenges["generic_schema_mutation_case_count"] != 20:
        fail("generic schema mutation coverage count mismatch")
    expected_ops = {"direct_field": 67, "derive_value": 2, "project_record": 13, "assemble_sorted_records": 4, "canonical_hash": 13, "project_contract": 20}
    if challenges["authority_op_counts"] != expected_ops or challenges["op_branch_positive_coverage"] != {op: True for op in expected_ops}:
        fail("challenge op branch positive coverage mismatch")
    if challenges["cross_op_substitution_control_count"] != 30 or challenges["op_specific_negative_output_count"] != 6:
        fail("cross-op or negative-output control count mismatch")
    candidate_catalog = verify_external_registry_root(manifest, registry, challenges, schema)
    authority_fixture_map: dict[str, dict[str, Any]] = {}
    for fixture in challenges["authority_fixtures"]:
        validate_object_instance(fixture, "AuthorityFixture", schema, "authority fixture")
        authority_fixture_map[fixture["fixture_id"]] = fixture
    if len(authority_fixture_map) != len(challenges["authority_fixtures"]):
        fail("duplicate authority fixture")
    expected_root_families = {
        row["closure_ref"]
        for row in registry["coverage_ledger"]
        if row["before_status"] == "D_unconstructible" and row["closure_kind"] == "authority_root"
    }
    if set(challenges["former_d_authority_root_families"]) != expected_root_families:
        fail("former-D authority root family set mismatch")
    if {fixture["object_type"] for fixture in authority_fixture_map.values()} != expected_root_families:
        fail("former-D root fixture coverage mismatch")
    base_scope = authority_fixture_map["authority:TemporalAuthorityScopeIdentity"]["value"]
    for authority_fixture in authority_fixture_map.values():
        candidate_scope = authority_fixture["value"].get("scope_identity")
        if candidate_scope is not None and any(candidate_scope[key] != base_scope[key] for key in IDENTITY_FIELDS):
            fail("TPA_AUTHORITY_SCOPE_MISMATCH")

    mapping_registry = manifest["accepted_authority_output_registry"]
    mapping_map = {mapping["mapping_id"]: mapping for mapping in mapping_registry["mappings"]}
    if len(mapping_map) != 119:
        fail("authority mapping identity/count mismatch")
    mapping_fixture_map: dict[str, dict[str, Any]] = {}
    consumed_authority_refs: set[str] = set()
    parent_objects: dict[str, Any] = {}
    parent_enums: dict[str, list[str]] = {}
    for parent_schema in (load(SUBJECT_SCHEMA), load(AEMH_SCHEMA)):
        parent_objects.update(parent_schema["objects"])
        parent_enums.update(parent_schema["enums"])
    for fixture in challenges["authority_mapping_positive_fixtures"]:
        validate_object_instance(fixture, "AuthorityMappingPositiveFixture", schema, "authority mapping fixture")
        mapping = mapping_map.get(fixture["mapping_id"])
        if mapping is None or fixture["fixture_id"] != f"fixture.{fixture['mapping_id']}":
            fail("authority mapping fixture identity mismatch")
        if fixture["authority_fixture_refs"] != mapping["source_fixture_refs"]:
            fail("TPA_AUTHORITY_FIXTURE_REF_IDENTITY_MISMATCH")
        for ref in fixture["authority_fixture_refs"]:
            authority_fixture = authority_fixture_map.get(ref)
            if authority_fixture is None or not ref.startswith(f"authority:{authority_fixture['object_type']}"):
                fail("TPA_AUTHORITY_FIXTURE_REF_UNRESOLVED")
            consumed_authority_refs.add(ref)
        contract, leaf = mapping["qualified_leaf"].split("::", 1)
        owner, field = leaf.split(".", 1)
        target_meta = parent_objects[owner][field]
        if (mapping["output_type"], mapping["output_cardinality"], mapping["output_nullable"]) != (target_meta["type"], target_meta["cardinality"], target_meta["nullable"]):
            fail("TPA_AUTHORITY_OUTPUT_TYPE_MISMATCH")
        canonical_fields = {
            "TemporalAxisBasis.axis_content_hash", "TemporalDateEndpoint.endpoint_content_hash", "TemporalDomainTrack.track_content_hash",
            "TemporalEvent.event_content_hash", "TemporalMembershipIndex.membership_content_hash", "TemporalPhaseBand.phase_content_hash",
            "TemporalRiskAnchor.risk_anchor_content_hash", "TemporalVisit.visit_content_hash", "AEMHMatchHistoryEntry.entry_hash",
            "AEMHMatchThread.thread_content_hash", "AEMHThreadPrefixAnchor.prefix_content_hash",
        }
        if owner == "PublicAuthorityReceipt" and field == "public_projection_id":
            expected_op = "derive_value"
        elif LazyAuthorityProjectionExecutor.direct_source(contract, owner, field) is not None:
            expected_op = "direct_field"
        elif leaf in canonical_fields or (owner == "PublicAuthorityReceipt" and field == "public_projection_content_hash"):
            expected_op = "canonical_hash"
        elif owner.endswith(("AuthorityPacket", "PublicProjection")):
            expected_op = "project_contract"
        elif target_meta["cardinality"] == "many" and target_meta["type"] in parent_objects:
            expected_op = "assemble_sorted_records"
        elif target_meta["type"] in parent_objects:
            expected_op = "project_record"
        else:
            expected_op = "derive_value"
        if mapping["op"] != expected_op:
            fail("TPA_AUTHORITY_OP_DISPATCH_MISMATCH")
        op_params = mapping[f"{mapping['op']}_params"]
        if mapping["op"] == "derive_value" and (target_meta["type"] in parent_objects or target_meta["type"] == "sha256" or target_meta["cardinality"] != "one"):
            fail("TPA_AUTHORITY_OP_OUTPUT_TYPE_MISMATCH")
        if mapping["op"] == "project_record" and (
            target_meta["type"] not in parent_objects
            or target_meta["cardinality"] != "one"
            or op_params["result_object_type"] != target_meta["type"]
        ):
            fail("TPA_AUTHORITY_OP_OUTPUT_TYPE_MISMATCH")
        if mapping["op"] == "assemble_sorted_records" and (
            target_meta["type"] not in parent_objects
            or target_meta["cardinality"] != "many"
            or op_params["result_object_type"] != target_meta["type"]
        ):
            fail("TPA_AUTHORITY_OP_OUTPUT_TYPE_MISMATCH")
        if mapping["op"] == "canonical_hash" and (target_meta["type"], target_meta["cardinality"], target_meta["nullable"]) != ("sha256", "one", False):
            fail("TPA_AUTHORITY_OP_OUTPUT_TYPE_MISMATCH")
        if mapping["op"] == "project_contract" and (
            owner.endswith(("AuthorityPacket", "PublicProjection")) is False
            or target_meta["type"] == "sha256"
            or op_params["result_type"] != target_meta["type"]
            or op_params["result_cardinality"] != target_meta["cardinality"]
        ):
            fail("TPA_AUTHORITY_OP_OUTPUT_TYPE_MISMATCH")
        try:
            computed, trace = LazyAuthorityProjectionExecutor([authority_fixture_map[ref] for ref in fixture["authority_fixture_refs"]]).execute(
                contract,
                owner,
                field,
                mapping["op"],
                mapping[f"{mapping['op']}_params"],
            )
        except RuntimeError as exc:
            fail(f"authority mapping execution failed: {mapping['mapping_id']} -> {exc}")
        if trace["consumed_fixture_refs"] != mapping["source_fixture_refs"] or trace["consumed_field_paths"] != mapping["source_field_paths"]:
            fail("TPA_AUTHORITY_UNUSED_DECLARED_DEPENDENCY")
        if trace["verified_fixture_pins"] != mapping["source_fixture_content_hash_pins"]:
            fail("TPA_AUTHORITY_FIXTURE_CONTENT_HASH_MISMATCH")
        if trace["trace_content_hash"] != fixture["expected_trace_content_hash"]:
            fail("TPA_AUTHORITY_TRACE_MISMATCH")
        validate_parent_projection_value(
            computed,
            target_meta["type"],
            target_meta["cardinality"],
            target_meta["nullable"],
            parent_objects,
            parent_enums,
            mapping["qualified_leaf"],
        )
        computed_json = json.dumps(canonicalize(computed), ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True)
        if fixture["expected_target_canonical_json"] != computed_json or fixture["expected_target_content_hash"] != canonical_digest(computed):
            fail("TPA_AUTHORITY_EXPECTED_TARGET_MISMATCH")
        mapping_fixture_map[fixture["mapping_id"]] = fixture
    if set(mapping_fixture_map) != set(mapping_map) or len(mapping_fixture_map) != 119:
        fail("authority mapping positive fixture bijection mismatch")
    if consumed_authority_refs != set(authority_fixture_map):
        fail("unconsumed authority fixture reference")

    fixture_map: dict[str, dict[str, Any]] = {}
    used_authority_refs: set[str] = set()
    for fixture in challenges["positive_fixtures"]:
        validate_object_instance(fixture, "PositiveFixture", schema, "positive fixture")
        fixture_map[fixture["fixture_id"]] = fixture
        used_authority_refs.update(fixture["authority_fixture_refs"])
    if len(fixture_map) != 18 or {item["recipe_id"] for item in fixture_map.values()} != REQUIRED_RECIPE_IDS:
        fail("positive fixture/recipe bijection mismatch")
    base_authority_refs = {ref for ref in authority_fixture_map if ref.count(":") == 1}
    if used_authority_refs != base_authority_refs:
        fail("positive fixtures do not exercise every former-D root family")
    recipe_authority_binding_map = {
        binding["recipe_id"]: binding
        for binding in manifest["accepted_recipe_authority_binding_registry"]["bindings"]
    }
    if set(recipe_authority_binding_map) != REQUIRED_RECIPE_IDS:
        fail("recipe authority binding recipe set mismatch")
    replacement_map: dict[str, dict[str, Any]] = {}
    for fixture in challenges["replacement_positive_fixtures"]:
        validate_object_instance(fixture, "PositiveFixture", schema, "replacement fixture")
        replacement_map[fixture["fixture_id"]] = fixture
    recipe_attack_map: dict[str, dict[str, Any]] = {}
    for bundle in challenges["replacement_recipe_attack_bundles"]:
        validate_object_instance(bundle, "AcceptedRecipeAttackBundle", schema, "recipe attack bundle")
        recipe_attack_map[bundle["bundle_id"]] = bundle
    if len(recipe_attack_map) != 1:
        fail("replacement recipe attack bundle count mismatch")
    for fixture in fixture_map.values():
        error, _outputs = execute_recipe(
            recipe_map[fixture["recipe_id"]], fixture, candidate_catalog, manifest["external_acceptance_registry_root"], schema,
            authority_fixture_map, recipe_authority_binding_map[fixture["recipe_id"]],
        )
        if error is not None:
            fail(f"positive typed fixture failed: {fixture['fixture_id']} -> {error}")

    dag_fixture = fixture_map["fixture.recipe.17.dag"]
    expected_edges = {
        ("root_hashes", "packet_hash"),
        ("packet_hash", "receipt_hash"),
        ("external_registry_hash", "receipt_hash"),
    }
    if {(edge["from_ref"], edge["to_ref"]) for edge in dag_fixture["dependency_edges"]} != expected_edges:
        fail("packet/receipt dependency DAG mismatch")

    ids: set[str] = set()
    leaf_cases: set[str] = set()
    mutation_identities: set[tuple[str, str, str, str]] = set()
    for case in challenges["cases"]:
        validate_object_instance(case, "ChallengeCase", schema, "challenge case")
        if case["case_id"] in ids:
            fail("duplicate challenge id")
        ids.add(case["case_id"])
        mutation = case["mutation"]
        identity = (mutation["target_kind"], mutation["target_ref"], mutation["path"], canonical_digest(mutation["replacement"]))
        if identity in mutation_identities:
            fail("challenge mutations are not distinct")
        mutation_identities.add(identity)
        if mutation["target_kind"] in {"authority_fixture_catalog", "authority_mapping_fixture", "authority_fixture", "authority_output_registry", "recipe_authority_binding_registry"}:
            actual_error = execute_authority_attack(case, authority_fixture_map, mapping_fixture_map, fixture_map, manifest)
            fixture = None
            recipe = None
        else:
            actual_error, fixture, recipe = apply_typed_case_mutation(
                case,
                fixture_map,
                replacement_map,
                recipe_map,
                recipe_attack_map,
                schema,
                registry,
                manifest,
            )
        if case["probe_kind"] == "coverage_leaf_delete":
            leaf_cases.add(case["covered_leaf"])
        elif case["probe_kind"] == "semantic_typed_mutation" and actual_error is None:
            if fixture is None or recipe is None:
                fail(f"typed mutation missing fixture/recipe: {case['case_id']}")
            try:
                actual_error, _outputs = execute_recipe(
                    recipe, fixture, candidate_catalog, manifest["external_acceptance_registry_root"], schema,
                    authority_fixture_map, recipe_authority_binding_map[fixture["recipe_id"]],
                )
            except ContractViolation as exc:
                actual_error = exc.code
        if actual_error != case["expected_error"]:
            fail(f"challenge oracle mismatch for {case['case_id']}: got={actual_error} expected={case['expected_error']}")
    if leaf_cases != parent_leaf_universe():
        fail("leaf challenge bijection mismatch")
    verify_recursive_instance_unknown_key_rejection(
        schema,
        next(iter(fixture_map.values())),
        next(iter(recipe_map.values())),
        next(iter(authority_fixture_map.values())),
        next(iter(candidate_catalog.values())),
        manifest["external_acceptance_registry_root"],
    )


def medical_writing_inventory(contract: dict[str, Any]) -> tuple[int, str]:
    rows: list[tuple[str, str]] = []
    for root_name in contract["roots"]:
        base = ROOT / root_name
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(ROOT).as_posix()
            normalized = relative.lower().replace("-", "_")
            if "medical_writing" not in normalized:
                continue
            rows.append((relative, raw_sha(path)))
    rows.sort(key=lambda item: item[0].encode("utf-8"))
    material = b"".join(path.encode("utf-8") + b"\0" + sha.encode("ascii") + b"\n" for path, sha in rows)
    return len(rows), hashlib.sha256(material).hexdigest()


def verify_protected_surface(manifest: dict[str, Any]) -> None:
    protected = manifest["accepted_parent_pins"]["protected_accepted_pins"]
    for relative, expected in protected["protected_path_sha256"].items():
        if raw_sha(ROOT / relative) != expected:
            fail(f"protected path drift: {relative}")
    inventory_contract = protected["medical_writing_inventory_contract"]
    count, aggregate = medical_writing_inventory(inventory_contract)
    if count != protected["medical_writing_protected_file_count"] or aggregate != protected["medical_writing_protected_inventory_sha256"]:
        fail(f"medical-writing aggregate drift count={count} aggregate={aggregate}")

    r5_root = ROOT / "poc/medical_monitoring_ai_native_r5"
    forbidden_paths = []
    for path in r5_root.rglob("*"):
        if not (path.is_file() or path.is_symlink()):
            continue
        name = path.name.lower()
        relative = path.relative_to(ROOT).as_posix().lower()
        producer = "subject_temporal_public" in name or "aemh_match_history_public" in name or "public_authority_common" in name
        s5_runtime = ("/src/mm_r5/s5_" in relative or "/tests/test_s5_" in relative or "/tests/s5_" in relative or "/evidence/r4_r5_s5" in relative)
        bytecode = name.endswith((".pyc", ".pyo")) and (producer or "s5" in name)
        if producer or s5_runtime or bytecode:
            forbidden_paths.append(path.relative_to(ROOT).as_posix())
    if forbidden_paths:
        fail("producer/S5 runtime/test/evidence/bytecode surface exists: " + ", ".join(sorted(forbidden_paths)))
    delta_cache = list((ROOT / "tools").glob("__pycache__/*temporal_projection_authority_delta*.pyc"))
    if delta_cache:
        fail("delta bytecode cache exists")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.15)
        if sock.connect_ex(("127.0.0.1", 8911)) == 0:
            fail("port 8911 is listening")


def verify_generator_determinism() -> None:
    names = ["manifest.json", "schema.json", "source_matrix_delta.json", "recipe_registry.json", "challenge_registry.json"]
    before = {name: (DELTA / name).read_bytes() for name in names}
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    outputs = []
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-B", str(GENERATOR)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            fail(f"generator execution failed: {result.stderr[-1000:]}")
        outputs.append({name: (DELTA / name).read_bytes() for name in names})
    if before != outputs[0] or outputs[0] != outputs[1]:
        fail("two generations are not byte-identical")


def main() -> None:
    verify_no_asserts(GENERATOR)
    verify_no_asserts(VERIFIER)
    verify_generator_has_no_semantic_interpreter()
    manifest = load(DELTA / "manifest.json")
    schema = load(DELTA / "schema.json")
    matrix = load(DELTA / "source_matrix_delta.json")
    registry = load(DELTA / "recipe_registry.json")
    challenges = load(DELTA / "challenge_registry.json")
    if manifest.get("contract_id") != CONTRACT_ID or manifest.get("no_self_acceptance") is not True:
        fail("manifest identity/self-acceptance boundary")
    if manifest.get("public_api_surface") != {"status": "none_contract_delta_only", "producer_callable_created": False}:
        fail("delta public API surface must be exactly absent")
    verify_exact_paths(manifest)
    verify_raw_pins(manifest)
    verify_parent_and_negative_pins(manifest)
    verify_schema(schema, manifest)
    verify_source_matrix(matrix, manifest)
    verify_typed_source_paths(matrix, manifest)
    recipe_map = verify_recipes(registry, schema, manifest)
    verify_challenges(challenges, registry, manifest, schema, recipe_map)
    verify_protected_surface(manifest)
    verify_generator_determinism()
    final_manifest = load(DELTA / "manifest.json")
    if final_manifest != manifest:
        fail("manifest changed during deterministic generation")
    result = {
        "ok": True,
        "contract_id": CONTRACT_ID,
        "object_count": len(schema["objects"]),
        "named_type_count": len(schema["named_types"]),
        "enum_count": len(schema["enums"]),
        "recipe_count": len(recipe_map),
        "coverage_leaf_count": len(registry["coverage_ledger"]),
        "former_d_leaf_count": registry["former_d_leaf_count"],
        "unexplained_leaf_count": registry["unexplained_leaf_count"],
        "challenge_count": len(challenges["cases"]),
        "active_attack_count": challenges["active_attack_case_count"],
        "positive_fixture_count": challenges["positive_fixture_count"],
        "authority_mapping_positive_fixture_count": challenges["authority_mapping_positive_fixture_count"],
        "authority_mapping_count": registry["authority_mapping_count"],
        "executable_authority_mapping_count": registry["executable_authority_mapping_count"],
        "unconsumed_authority_fixture_ref_count": challenges["unconsumed_authority_fixture_ref_count"],
        "authority_leaf_without_emitter_count": registry["authority_leaf_without_emitter_count"],
        "accepted_authority_output_registry_content_hash": EXPECTED_AUTHORITY_OUTPUT_REGISTRY_CONTENT_HASH,
        "accepted_recipe_authority_binding_registry_content_hash": EXPECTED_RECIPE_AUTHORITY_BINDING_REGISTRY_CONTENT_HASH,
        "unique_dependency_slice_count": registry["unique_dependency_slice_count"],
        "min_dependency_count": registry["min_dependency_count"],
        "max_dependency_count": registry["max_dependency_count"],
        "median_dependency_count": registry["median_dependency_count"],
        "mappings_with_all_19_count": registry["mappings_with_all_19_count"],
        "unused_declared_dependency_count": registry["unused_declared_dependency_count"],
        "authority_op_counts": registry["authority_op_counts"],
        "op_branch_positive_coverage": registry["op_branch_positive_coverage"],
        "cross_op_substitution_control_count": challenges["cross_op_substitution_control_count"],
        "op_specific_negative_output_count": challenges["op_specific_negative_output_count"],
        "semantic_typed_probe_count": challenges["semantic_typed_probe_count"],
        "structural_coverage_probe_count": challenges["structural_coverage_probe_count"],
        "external_registry_root_content_hash": EXPECTED_EXTERNAL_REGISTRY_ROOT_CONTENT_HASH,
        "accepted_record_count": manifest["accepted_record_count"],
        "accepted_recipe_count": manifest["accepted_recipe_count"],
        "generic_schema_mutation_case_count": challenges["generic_schema_mutation_case_count"],
        "exact_leaf_output_bijection_count": registry["exact_leaf_output_bijection_count"],
        "nominal_mapping_count": registry["nominal_mapping_count"],
        "python_optimize": sys.flags.optimize,
        "python_hash_seed": os.environ.get("PYTHONHASHSEED", "random"),
        "two_byte_identical_generations": True,
        "port_8911_stopped": True,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
