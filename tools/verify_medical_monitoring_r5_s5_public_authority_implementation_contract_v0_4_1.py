"""Independently verify public-authority implementation contract v0.4.1."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import unicodedata
from typing import Any, NoReturn

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1"
PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
TEMPORAL = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
GENERATOR = ROOT / "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1.py"
VERIFIER = pathlib.Path(__file__).resolve()
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.4.1"

EXPECTED_MANIFEST_COUNTS = {
    "spec_count": 236,
    "unique_trace_count": 236,
    "alias_count": 0,
    "positive_count": 10,
    "reject_count": 226,
    "leaf_count": 272,
    "resolved_join_count": 272,
    "recipe_count": 16,
    "recipe_node_count": 32,
    "artifact_governance_probe_count": 22,
    "pre_delta_error_replay_count": 170,
    "accepted_delta_error_replay_count": 22,
    "error_union_count": 192,
    "active_gate_check_count": 58,
}

TYPED_RECIPE_BINDINGS = {
    "recipe.v02.subject_identity_cutoff": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "MonitoringRun", "project_id", "/source/scope/project_ref"),
    "recipe.v02.subject_locators_revisions": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "SourceRevision", "revision_id", "/source/revision_specs/0/revision_ref"),
    "recipe.v02.subject_temporal_members": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "TemporalEvent", "event_id", "/source/events/0/event_ref"),
    "recipe.v02.subject_domains_pending_membership": ("poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py", "SemanticRecord", "role", "/source/domain_applicability/0/domain"),
    "recipe.v02.subject_axis": ("poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py", "VisitJourneyProjection", "subject_ref", "/source/scope/subject_ref"),
    "recipe.v02.subject_projection": ("poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py", "S4AcceptedAuthorityAnchor", "spine_ref", "/source/scope/spine_ref"),
    "recipe.v02.subject_receipt": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "MonitoringRun", "run_id", "/source/scope/run_ref"),
    "recipe.v02.subject_packet": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "ListingSnapshot", "snapshot_version", "/source/scope/snapshot_ref"),
    "recipe.v02.aemh_identity_locators_revisions": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "MonitoringRun", "project_id", "/source/current_scope/project_ref"),
    "recipe.v02.aemh_previous_threads": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py", "AEMHResult", "project_id", "/source/previous_scope/project_ref"),
    "recipe.v02.aemh_previous_packet": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py", "AEMHResult", "snapshot_version", "/source/previous_scope/snapshot_ref"),
    "recipe.v02.aemh_current_threads": ("poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py", "AEMHSliceResult", "subject_ref", "/source/current_scope/subject_ref"),
    "recipe.v02.aemh_current_membership_prefix_cutoff": ("poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py", "RiskCandidate", "domain", "/source/thread_specs/0/domain"),
    "recipe.v02.aemh_projection": ("poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py", "S4AcceptedAuthorityAnchor", "spine_ref", "/source/current_scope/spine_ref"),
    "recipe.v02.aemh_receipt": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "MonitoringRun", "run_id", "/source/current_scope/run_ref"),
    "recipe.v02.aemh_packet": ("poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py", "AEMHResult", "snapshot_version", "/source/current_scope/snapshot_ref"),
}

EXPECTED_ERROR_COUNTS = {
    "authority_inventory": {"parent": 81, "semantic_delta": 49, "temporal_delta": 62, "union": 192},
    "executable_coverage": {"pre_delta_unique": 170, "error_replay_delta": 22, "post_union_unique": 192},
    "executed_cases": {"parent": 194, "semantic": 66, "temporal_v01": 418, "temporal_v02": 236, "error_replay_delta": 22},
}

EXACT_PATHS = {
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1_20260821_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1_20260821.md",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/public_api.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/source_join_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/invariant_error_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/test_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1.py",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1.py",
}

S5_LOCKS = {
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_contracts.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_authority_builder.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_projection.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/s5_runtime_fixtures.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_contracts.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_authority_builder.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_projection.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s5_readonly_gate.py",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_s5_runtime_challenges.py",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_readonly_sha256.json",
}

FUTURE_PATHS = [
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py",
    "poc/medical_monitoring_ai_native_r5/tests/public_authority_runtime_fixtures.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_common.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s5_public_authority_readonly_sha256.json",
]


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"object required: {path}")
    return value


def load_module(path: pathlib.Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonicalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(key)): canonicalize(item) for key, item in value.items()}
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_count_issues(counts: Any) -> list[str]:
    if not isinstance(counts, dict):
        return ["COUNTS_NOT_OBJECT"]
    issues: list[str] = []
    if set(counts) != set(EXPECTED_MANIFEST_COUNTS):
        issues.append("COUNTS_EXACT_KEYS")
    for key, expected in EXPECTED_MANIFEST_COUNTS.items():
        if key not in counts:
            continue
        if type(counts[key]) is not int:
            issues.append(f"COUNT_TYPE:{key}")
        elif counts[key] != expected:
            issues.append(f"COUNT_VALUE:{key}")
    return issues


def error_count_issues(counts: Any) -> list[str]:
    if not isinstance(counts, dict) or set(counts) != set(EXPECTED_ERROR_COUNTS):
        return ["ERROR_COUNT_TOP_KEYS"]
    issues: list[str] = []
    for plane, expected_values in EXPECTED_ERROR_COUNTS.items():
        values = counts[plane]
        if not isinstance(values, dict) or set(values) != set(expected_values):
            issues.append(f"ERROR_COUNT_KEYS:{plane}")
            continue
        for key, expected in expected_values.items():
            if type(values[key]) is not int:
                issues.append(f"ERROR_COUNT_TYPE:{plane}:{key}")
            elif values[key] != expected:
                issues.append(f"ERROR_COUNT_VALUE:{plane}:{key}")
    return issues


def engine() -> Any:
    return load_module(
        ROOT / "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "accepted_temporal_v02_independent_engine_for_v041",
    )


def json_get(value: Any, pointer: str) -> Any:
    current = value
    for token in pointer.strip("/").split("/") if pointer != "/" else []:
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def verify_static_tools() -> None:
    generator_tree = ast.parse(GENERATOR.read_text(encoding="utf-8"), filename=str(GENERATOR))
    verifier_tree = ast.parse(VERIFIER.read_text(encoding="utf-8"), filename=str(VERIFIER))
    if any(isinstance(node, ast.Assert) for tree in (generator_tree, verifier_tree) for node in ast.walk(tree)):
        fail("assert-only gate forbidden")
    generator_text = GENERATOR.read_text(encoding="utf-8")
    verifier_text = VERIFIER.read_text(encoding="utf-8")
    imports = [
        alias.name
        for tree in (generator_tree, verifier_tree)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    ]
    if any("public_authority_implementation_contract_v0_4_1" in name for name in imports):
        fail("mutual v0.4.1 import/reference forbidden")
    if "temporal_projection_authority_delta_v0_2.py" not in generator_text or "temporal_projection_authority_delta_v0_2.py" not in verifier_text:
        fail("separate accepted engines missing")
    for tree in (generator_tree, verifier_tree):
        for node in ast.walk(tree):
            match_type = getattr(ast, "Match", None)
            if isinstance(node, ast.If) or (match_type is not None and isinstance(node, match_type)):
                source = ast.unparse(node.test if isinstance(node, ast.If) else node.subject)
                forbidden_branch_tokens = ("case" + "_id", "senti" + "nel", "source" + "_case_ref")
                if any(token in source for token in forbidden_branch_tokens):
                    fail("case/label/sentinel branch forbidden")


def verify_manifest() -> dict[str, Any]:
    manifest = load(OUT / "manifest.json")
    if manifest.get("contract_id") != CONTRACT_ID or manifest.get("status") != "candidate_unaccepted":
        fail("manifest identity/status")
    if set(manifest.get("exact_nine_paths", [])) != EXACT_PATHS or len(manifest.get("exact_nine_paths", [])) != 9:
        fail("nine path boundary")
    if "acceptance_token" in manifest or manifest.get("acceptance_token_forbidden") is not True:
        fail("acceptance token leakage")
    if manifest.get("manifest_content_hash") != digest({key: value for key, value in manifest.items() if key != "manifest_content_hash"}):
        fail("manifest content hash")
    pins = manifest.get("file_raw_sha256", {})
    if set(pins) != EXACT_PATHS - {str(OUT.relative_to(ROOT) / "manifest.json")}:
        fail("eight external file pins")
    for relative, expected in pins.items():
        if raw_sha(ROOT / relative) != expected:
            fail(f"v0.4.1 raw pin drift: {relative}")
    for surface in ("authority_chain_pins", "typed_source_pins", "temporal_v02_nine_file_pins"):
        for relative, expected in manifest[surface].items():
            if raw_sha(ROOT / relative) != expected:
                fail(f"{surface} drift: {relative}")
    temporal_manifest = load(TEMPORAL / "manifest.json")
    if manifest["typed_source_pins"] != temporal_manifest["typed_source_pins"]:
        fail("duplicate typed pin disagreement")
    if manifest_count_issues(manifest.get("counts")):
        fail("manifest counts")
    added_counts = (
        "resolved_join_count",
        "pre_delta_error_replay_count",
        "accepted_delta_error_replay_count",
        "error_union_count",
        "active_gate_check_count",
    )
    for key in added_counts:
        candidate = copy.deepcopy(manifest["counts"])
        candidate[key] += 1
        if not manifest_count_issues(candidate):
            fail(f"manifest count +1 negative control: {key}")
    candidate = copy.deepcopy(manifest["counts"])
    candidate.pop("resolved_join_count")
    if not manifest_count_issues(candidate):
        fail("manifest missing count negative control")
    candidate = copy.deepcopy(manifest["counts"])
    candidate["extra_count"] = 1
    if not manifest_count_issues(candidate):
        fail("manifest extra count negative control")
    candidate = copy.deepcopy(manifest["counts"])
    candidate["resolved_join_count"] = True
    if not manifest_count_issues(candidate):
        fail("manifest bool-as-int negative control")
    required_false = ("producer_executed", "runtime_tests_executed", "evidence_created", "self_acceptance")
    if any(manifest.get(key) is not False for key in required_false):
        fail("false execution/acceptance claim")
    if manifest.get("authority_scope") != "synthetic_test_only" or manifest.get("execution_profile") != "full_parent_graph":
        fail("manifest scope/profile")
    return manifest


def verify_api() -> dict[str, Any]:
    api = load(OUT / "public_api.json")
    expected_functions = {
        "canonical_json_bytes(value: object) -> bytes",
        "canonical_sha256(value: object) -> str",
        "validation_result(issues: Iterable[PublicAuthorityValidationIssue]) -> PublicAuthorityValidationResult",
        "build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket",
        "validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult",
        "build_aemh_match_history_authority(source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> AEMHMatchHistoryAuthorityPacket",
        "validate_aemh_match_history_authority(candidate: AEMHMatchHistoryAuthorityPacket, source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> PublicAuthorityValidationResult",
    }
    actual = {item for module in api["modules"].values() for item in module.get("functions", [])}
    if actual != expected_functions:
        fail("exact public signatures")
    all_classes = [item for module in api["modules"].values() for section in ("input_classes", "output_classes", "result_classes") for item in module.get(section, [])]
    if not all(item.get("decorator") == "dataclasses.dataclass(frozen=True)" for item in all_classes):
        fail("all classes frozen dataclass")
    for item in all_classes:
        for _, type_name in item.get("fields", []):
            if type_name == "Any" or type_name.startswith(("list[", "dict[", "Mapping[")):
                fail(f"untyped/mutable/free mapping field: {item['name']}")
    if api["exact_output_schema"] != {
        "subject_object_count": 17, "aemh_object_count": 13,
        "subject_schema_raw_sha256": raw_sha(PARENT_DIR / "subject_temporal_schema.json"),
        "aemh_schema_raw_sha256": raw_sha(PARENT_DIR / "aemh_match_history_schema.json"),
        "extra_serialization_leaves_forbidden": True,
    }:
        fail("output schema pins")
    if api["authority_bundle_contract"] != {
        "authority_scope": "synthetic_test_only", "execution_profile": "full_parent_graph",
        "temporal_v01_manifest_sha256": "e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97",
        "temporal_v02_manifest_sha256": "466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8",
        "exact_target_contracts": [SUBJECT, AEMH], "candidate_backfill_forbidden": True, "dual_plane_exact_cross_check": True,
    }:
        fail("authority bundle contract")
    return api


def ast_field_exists(selector: dict[str, Any]) -> bool:
    expected_keys = {"module_path", "class_name", "field_path", "instance_key", "json_pointer", "cardinality"}
    if set(selector) != expected_keys or any(type(selector[key]) is not str for key in expected_keys):
        return False
    if any(key in selector for key in ("path", "class", "field")):
        return False
    tree = ast.parse((ROOT / selector["module_path"]).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == selector["class_name"]:
            fields = {
                item.target.id
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            }
            segments = selector["field_path"].split(".")
            if not segments or segments[0] not in fields:
                return False
            return len(segments) == 1
    return False


def baseline_runtime(independent: Any) -> dict[str, dict[str, Any]]:
    fixtures = load(TEMPORAL / "full_graph_fixture_registry.json")
    recipes = load(TEMPORAL / "emitter_recipe_registry.json")
    result = {}
    for row in fixtures["baselines"]:
        bundle = copy.deepcopy(row["authority_input"])
        target = bundle["target_contract"]
        if independent.authority_issues(bundle, load(TEMPORAL / "schema.json")):
            fail(f"baseline authority invalid: {target}")
        built, outputs = independent.execute_independent_recipe_dag(bundle, recipes)
        if target == SUBJECT:
            packet = built
            issues = independent.validate_parent(target, packet)
        else:
            previous, packet = built
            issues = [*independent.validate_parent(target, previous, None), *independent.validate_parent(target, packet, previous)]
        if issues:
            fail(f"baseline parent invalid: {target}:{issues}")
        result[target] = {"bundle": bundle, "built": built, "packet": packet, "outputs": outputs}
    if set(result) != {SUBJECT, AEMH}:
        fail("2/2 baseline closure")
    return result


def construction_graphs(runtime: dict[str, dict[str, Any]]) -> dict[str, Any]:
    graphs: dict[str, Any] = {}
    for target, baseline in runtime.items():
        bundle = baseline["bundle"]
        typed_instances = {}
        for recipe_id, (module_path, class_name, field_path, authority_pointer) in TYPED_RECIPE_BINDINGS.items():
            if (target == SUBJECT) != recipe_id.startswith("recipe.v02.subject_"):
                continue
            value = copy.deepcopy(json_get(bundle, authority_pointer))
            typed_instances[recipe_id] = {
                "module_path": module_path,
                "class_name": class_name,
                "instance_key": recipe_id,
                "fields": {field_path: value},
            }
        common_objects = {}
        if target == SUBJECT:
            binding = bundle["source"]["cutoff_binding"]
            core = {
                "state": binding["state"],
                "exact_date": binding["exact_date"],
                "source_locator_refs": sorted(set(binding["source_locator_refs"])),
            }
            common_objects = {"PublicCutoffEndpoint": {"subject-cutoff-binding": {**core, "cutoff_content_hash": digest(core)}}}
        graphs[target] = {
            "target_contract": target,
            "authority_bundle": bundle,
            "typed_source_instances": typed_instances,
            "recipe_outputs": baseline["outputs"],
            "common_objects": common_objects,
            "final_packet": baseline["packet"],
        }
    return {"contracts": graphs}


def expected_selectors(row: dict[str, Any], runtime: dict[str, dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
    module_path, class_name, field_path, authority_pointer = TYPED_RECIPE_BINDINGS[row["recipe_id"]]
    target = row["contract"]
    typed = {
        "module_path": module_path,
        "class_name": class_name,
        "field_path": field_path,
        "instance_key": row["recipe_id"],
        "json_pointer": f"/contracts/{target}/typed_source_instances/{row['recipe_id']}/fields/{field_path}",
        "cardinality": "exact-one",
    }
    v02 = {
        "root_type": "AuthorityBundleV02",
        "source_variant": "SubjectFullGraphInputV02" if target == SUBJECT else "AEMHFullGraphInputV02",
        "instance_key": runtime[target]["bundle"]["bundle_content_identity"],
        "json_pointer": f"/contracts/{target}/authority_bundle{authority_pointer}",
        "cardinality": "exact-one",
    }
    return typed, v02


def join_issues(joins: dict[str, Any], runtime: dict[str, dict[str, Any]]) -> list[str]:
    issues = []
    wrapped_graphs = construction_graphs(runtime)
    rows = joins.get("rows", [])
    if len(rows) != 272 or joins.get("subject_count") != 156 or joins.get("aemh_count") != 116:
        issues.append("count")
    if len({row.get("qualified_leaf") for row in rows}) != len(rows):
        issues.append("qualified_duplicate")
    if len({row.get("output_json_pointer") for row in rows}) != len(rows):
        issues.append("pointer_duplicate")
    positions = {row.get("qualified_leaf"): index for index, row in enumerate(rows)}
    recipes = load(TEMPORAL / "emitter_recipe_registry.json")
    recipe_by_id = {row["recipe_id"]: row for row in recipes["executable_v02_recipes"]}
    recipe_ids = set(recipe_by_id)
    node_ids = {node["node_id"] for recipe in recipes["executable_v02_recipes"] for node in recipe["nodes"]}
    for index, row in enumerate(rows):
        required = {"ordinal", "contract", "object_type", "leaf", "qualified_leaf", "output_json_pointer", "output_type", "nullable", "cardinality", "ordering_rule", "key_selector", "authority_source_kind", "typed_source_selector", "v02_authority_selector", "selector_cardinality", "selector_zero_policy", "selector_many_policy", "reducer_id", "recipe_id", "recipe_content_hash", "recipe_node_id", "recipe_node_output_ref", "recipe_output_json_pointer", "recipe_registry_content_hash", "dependency_output_leaves", "dependency_recipe_nodes", "construction_phase", "parent_schema_ref", "semantic_ref", "expected_plane_ref", "fail_closed_codes", "candidate_backfill_forbidden", "mirror_forbidden"}
        if not required.issubset(row):
            issues.append(f"keys:{index}")
            continue
        if row["recipe_id"] not in recipe_ids or row["recipe_node_id"] not in node_ids:
            issues.append(f"recipe:{index}")
            continue
        expected_typed, expected_v02 = expected_selectors(row, runtime)
        if not ast_field_exists(row["typed_source_selector"]):
            issues.append(f"typed:{index}")
        if row["typed_source_selector"] != expected_typed:
            issues.append(f"typed_semantic:{index}")
        if set(row["v02_authority_selector"]) != {"root_type", "source_variant", "instance_key", "json_pointer", "cardinality"} or row["v02_authority_selector"] != expected_v02:
            issues.append(f"v02_selector:{index}")
        construction_keys = {"graph_type", "json_pointer", "instance_key", "common_object", "resolved_value_content_hash", "target_kind"}
        if set(row["construction_target"]) != construction_keys or row["construction_target"]["graph_type"] != "ConstructionGraph":
            issues.append(f"construction_target_schema:{index}")
        packet_target = row["packet_target"]
        if packet_target is not None and (set(packet_target) != {"json_pointer", "target_kind"} or packet_target["target_kind"] not in {"root_packet", "packet_reachable"}):
            issues.append(f"packet_target_schema:{index}")
        if row["construction_target"]["target_kind"] == "contract_shared_intermediate" and packet_target is not None:
            issues.append(f"shared_packet_target:{index}")
        if set(row["key_selector"]) != {"strategy", "object_type", "instance_key", "selected_instance_count", "available_instance_count"} or row["key_selector"]["strategy"] != "exact_construction_path" or row["key_selector"]["object_type"] != row["object_type"]:
            issues.append(f"key_selector:{index}")
        if set(row["instance_selector"]) != {"graph_root", "instance_key", "cardinality", "zero_policy", "many_policy"}:
            issues.append(f"instance_selector:{index}")
        if row["selector_cardinality"] != "exact-one" or row["authority_source_kind"] != "dual_typed_and_accepted_v02":
            issues.append(f"selector_contract:{index}")
        try:
            target = row["contract"]
            exact_prefix = f"/contracts/{target}/"
            if not row["output_json_pointer"].startswith(exact_prefix):
                raise KeyError("legacy or cross-contract output prefix")
            prefix = f"/contracts/{target}/authority_bundle"
            json_get(runtime[target]["bundle"], row["v02_authority_selector"]["json_pointer"].removeprefix(prefix))
            target_kind = row["construction_target"]["target_kind"]
            classification = joins["target_kind_contract"][target_kind]
            if f"{target}::{row['object_type']}" not in classification:
                raise KeyError("target-kind classification")
            construction_value = json_get(wrapped_graphs, row["construction_target"]["json_pointer"])
            output_value = json_get(wrapped_graphs, row["output_json_pointer"])
            if digest(construction_value) != row["construction_target"]["resolved_value_content_hash"]:
                raise KeyError("construction target hash")
            if target_kind == "contract_shared_intermediate":
                if row["packet_target"] is not None or "/common_objects/" not in row["construction_target"]["json_pointer"]:
                    raise KeyError("shared target")
                binding = runtime[target]["bundle"]["source"]["cutoff_binding"]
                core = {"state": binding["state"], "exact_date": binding["exact_date"], "source_locator_refs": sorted(set(binding["source_locator_refs"]))}
                expected_common = {**core, "cutoff_content_hash": digest(core)}[row["leaf"]]
                if construction_value != expected_common or output_value != expected_common:
                    raise KeyError("shared source authority")
            else:
                if row["packet_target"] is None or row["packet_target"]["target_kind"] != target_kind:
                    raise KeyError("packet target kind")
                if row["packet_target"]["json_pointer"] != row["output_json_pointer"]:
                    raise KeyError("packet/output target disagreement")
                packet_value = json_get(wrapped_graphs, row["packet_target"]["json_pointer"])
                stage = runtime[row["contract"]]["outputs"][row["recipe_node_output_ref"]]["value"]
                stage_value = json_get(stage, row["recipe_output_json_pointer"])
                if construction_value != packet_value or output_value != stage_value or packet_value != stage_value:
                    raise KeyError("resolved leaf disagreement")
            parent_pointer = row["output_json_pointer"].rsplit("/", 1)[0]
            resolved_parent = json_get(wrapped_graphs, parent_pointer)
            schema = load(PARENT_DIR / ("subject_temporal_schema.json" if target == SUBJECT else "aemh_match_history_schema.json"))
            if set(resolved_parent) != set(schema["objects"][row["object_type"]]) or row["leaf"] not in resolved_parent:
                raise KeyError("resolved object type/field")
        except (KeyError, IndexError, TypeError):
            issues.append(f"pointer:{index}")
        for dependency in row["dependency_output_leaves"]:
            if positions.get(dependency, len(rows)) >= index:
                issues.append(f"future:{index}")
        if row["candidate_backfill_forbidden"] is not True or row["mirror_forbidden"] is not True:
            issues.append(f"authority:{index}")
        if "candidate" in str(row["v02_authority_selector"]).lower():
            issues.append(f"candidate_source:{index}")
    return issues


def verify_joins(independent: Any, runtime: dict[str, dict[str, Any]]) -> dict[str, Any]:
    joins = load(OUT / "source_join_matrix.json")
    issues = join_issues(joins, runtime)
    if issues:
        fail("join matrix: " + "|".join(issues[:20]))
    return joins


def error_issues(matrix: dict[str, Any]) -> list[str]:
    issues = []
    if error_count_issues(matrix.get("counts")):
        issues.append("counts")
    rows = matrix.get("errors", [])
    if len(rows) != 192 or [row.get("priority") for row in rows] != list(range(1, 193)):
        issues.append("priority")
    if len({(row.get("code"), row.get("path"), row.get("origin"), row.get("message_semantics")) for row in rows}) != 192:
        issues.append("dedup")
    if matrix.get("any_issue_forbids_packet") is not True or matrix.get("primary_code") != "first ordered issue code":
        issues.append("result_semantics")
    for row in rows:
        if row.get("coverage_replay_ref") != row.get("source_challenge_ref") or not row.get("coverage_replay_ref"):
            issues.append("coverage_replay_ref")
            break
    return issues


def verify_errors() -> dict[str, Any]:
    matrix = load(OUT / "invariant_error_matrix.json")
    issues = error_issues(matrix)
    if issues:
        fail("error matrix: " + "|".join(issues))
    flat = {"parent": 81, "semantic_delta": 49, "temporal_delta": 62, "union": 192}
    if not error_count_issues(flat):
        fail("flat legacy error counts negative control")
    for plane, values in EXPECTED_ERROR_COUNTS.items():
        for key in values:
            candidate = copy.deepcopy(EXPECTED_ERROR_COUNTS)
            candidate[plane][key] += 1
            if not error_count_issues(candidate):
                fail(f"error count +1 negative control: {plane}:{key}")
    candidate = copy.deepcopy(EXPECTED_ERROR_COUNTS)
    candidate["authority_inventory"].pop("parent")
    if not error_count_issues(candidate):
        fail("error count missing negative control")
    candidate = copy.deepcopy(EXPECTED_ERROR_COUNTS)
    candidate["extra"] = {}
    if not error_count_issues(candidate):
        fail("error count extra negative control")
    candidate = copy.deepcopy(EXPECTED_ERROR_COUNTS)
    candidate["executable_coverage"]["pre_delta_unique"] = True
    if not error_count_issues(candidate):
        fail("error count bool negative control")
    return matrix


def replay_specs(independent: Any) -> tuple[int, int, int]:
    tests = load(OUT / "test_matrix.json")
    specs = tests["current_contract_verification"]["runtime_specifications"]
    if len(specs) != 236 or len({row["trace_identity"] for row in specs}) != 236:
        fail("test spec identity inventory")
    accepted = load(TEMPORAL / "trace_realization_registry.json")
    bases = accepted["base_authority_inputs"]
    recipes = load(TEMPORAL / "emitter_recipe_registry.json")
    parent = independent.parent_module()
    subject_schema = load(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = load(PARENT_DIR / "aemh_match_history_schema.json")
    error_by_code = {row["code"]: row for row in load(OUT / "invariant_error_matrix.json")["errors"]}
    positives = rejects = 0
    identities = set()
    required_keys = {
        "trace_identity", "contract", "lane", "base_input_ref", "base_input_content_identity",
        "pre_authority_identities", "instance_selector", "primary_operation", "linked_operations",
        "reseal_mode", "reseal_order", "reseal_plan", "actual_ordered_issues", "actual_ordered_issue_objects",
        "future_validator_expected", "post_packet_content_hash", "post_projection_content_hash",
        "identity_contract", "generator_executed", "producer_executed",
    }
    for index, spec in enumerate(specs):
        if set(spec) != required_keys:
            fail(f"spec exact keys: {index}")
        if spec["base_input_ref"] not in bases or spec["instance_selector"] != {
            "base_variant": spec["base_input_ref"],
            "semantic_rule_path": spec["instance_selector"].get("semantic_rule_path"),
        } or not isinstance(spec["instance_selector"]["semantic_rule_path"], str) or not spec["instance_selector"]["semantic_rule_path"].startswith("/"):
            fail(f"spec instance selector: {index}")
        base = copy.deepcopy(bases[spec["base_input_ref"]])
        target = spec["contract"]
        if target != base["target_contract"] or spec["base_input_content_identity"] != base["bundle_content_identity"]:
            fail(f"spec base authority: {index}")
        pre_built, _ = independent.execute_independent_recipe_dag(copy.deepcopy(base), recipes)
        if target == SUBJECT:
            pre_previous = None
            pre_packet = pre_built
        else:
            pre_previous, pre_packet = pre_built
        pre_identities = {
            "authority_bundle": base["bundle_content_identity"],
            "previous_packet": None if pre_previous is None else pre_previous["packet_content_hash"],
            "pre_packet": pre_packet["packet_content_hash"],
        }
        if spec["pre_authority_identities"] != pre_identities:
            fail(f"spec pre authority identities: {index}")
        identity_payload = {
            "pre_authority_identities": spec["pre_authority_identities"],
            "instance_selector": spec["instance_selector"],
            "primary_operation": spec["primary_operation"],
            "linked_operations": spec["linked_operations"],
            "lane": spec["lane"],
            "reseal_mode": spec["reseal_mode"],
            "reseal_order": spec["reseal_order"],
            "reseal_plan": spec["reseal_plan"],
        }
        identity = digest(identity_payload)
        if identity != spec["trace_identity"] or identity in identities:
            fail(f"trace identity: spec-{index + 1}")
        identities.add(identity)
        primary = copy.deepcopy(spec["primary_operation"])
        linked = copy.deepcopy(spec["linked_operations"])
        operations = [primary, *linked]
        order_tokens = [
            f"{operation.get('sequence', position)}:{operation['op']}:{operation.get('path', operation.get('target'))}"
            for position, operation in enumerate(operations, 1)
        ]
        if order_tokens != spec["reseal_order"]:
            fail(f"spec reseal order: {index}")
        source_transform = isinstance(primary.get("sequence"), int) and all(isinstance(item.get("sequence"), int) for item in linked)
        plan = spec["reseal_plan"]
        if set(plan) != {"mode", "ordered_targets", "preserve_fields"} or plan["mode"] != spec["reseal_mode"]:
            fail(f"spec reseal plan schema: {index}")
        if plan["mode"] not in {"none", "full_subject_dag", "full_aemh_dag"}:
            fail(f"spec reseal plan mode: {index}")
        if not isinstance(plan["ordered_targets"], list) or len(plan["ordered_targets"]) != len(set(plan["ordered_targets"])):
            fail(f"spec reseal targets duplicate/type: {index}")
        if not isinstance(plan["preserve_fields"], list) or len(plan["preserve_fields"]) != len(set(plan["preserve_fields"])) or any(item != "/receipt/evaluation_content_identities" for item in plan["preserve_fields"]):
            fail(f"spec preserve fields: {index}")
        previous = None
        if source_transform:
            if plan["ordered_targets"] != ["authority_bundle", "accepted_v02_recipe_dag", "parent_validator"] or plan["preserve_fields"]:
                fail(f"spec source reseal plan: {index}")
            for operation in sorted(operations, key=lambda item: item["sequence"]):
                if independent.pointer_get(base, operation["path"]) != operation["pre_value"]:
                    fail(f"spec source pre: {index}")
                independent.apply_source_operation(base, operation)
                if independent.pointer_get(base, operation["path"]) != operation["post_value"]:
                    fail(f"spec source post: {index}")
            if spec["reseal_mode"] not in {"full_subject_dag", "full_aemh_dag"}:
                fail(f"spec source reseal mode: {index}")
            independent.reseal_bundle(base)
            built, _ = independent.execute_independent_recipe_dag(base, recipes)
            if target == SUBJECT:
                graph = built
                issue_codes = independent.validate_parent(target, graph)
            else:
                previous, graph = built
                issue_codes = [*independent.validate_parent(target, previous, None), *independent.validate_parent(target, graph, previous)]
        else:
            if linked != ([{"op": "apply_parent_mutation", "target": primary["path"]}] + ([] if spec["reseal_mode"] == "none" else [{"op": "reseal_parent_graph", "target": target}]) + [{"op": "validate_parent", "target": target}]):
                fail(f"spec linked parent program: {index}")
            previous = pre_previous
            graph = copy.deepcopy(pre_packet)
            parent.apply_mutation(graph, primary)
            expected_targets = ["candidate_packet", "parent_validator"] if spec["reseal_mode"] == "none" else ["candidate_packet", "parent_hash_dag", "parent_validator"]
            if plan["ordered_targets"] != expected_targets:
                fail(f"spec parent reseal targets: {index}")
            if spec["reseal_mode"] != "none":
                expected_mode = "full_subject_dag" if target == SUBJECT else "full_aemh_dag"
                if spec["reseal_mode"] != expected_mode:
                    fail(f"spec parent reseal mode: {index}")
                preserved_before = copy.deepcopy(json_get(graph, "/receipt/evaluation_content_identities"))
                preserve = plan["preserve_fields"] == ["/receipt/evaluation_content_identities"]
                if target == SUBJECT:
                    parent.reseal_subject_packet(graph, subject_schema, preserve_evaluation=preserve)
                else:
                    parent.reseal_aemh_packet(graph, aemh_schema, preserve_evaluation=preserve)
                if preserve and json_get(graph, "/receipt/evaluation_content_identities") != preserved_before:
                    fail(f"spec preserve not effective: {index}")
            elif plan["preserve_fields"]:
                fail(f"spec preserve without reseal: {index}")
            issue_codes = independent.validate_parent(target, graph, previous)
        positives += int(not issue_codes)
        rejects += int(bool(issue_codes))
        issue_objects = [{"code": code, "path": error_by_code[code]["path"], "message": error_by_code[code]["message"], "origin": error_by_code[code]["origin"], "priority": error_by_code[code]["priority"]} for code in issue_codes]
        expected_result = {"ok": not issue_codes, "primary_code": issue_codes[0] if issue_codes else None, "ordered_issue_codes": issue_codes, "ordered_issues": issue_objects, "packet_emitted": not issue_codes}
        if spec["actual_ordered_issues"] != issue_codes or spec["actual_ordered_issue_objects"] != issue_objects or spec["future_validator_expected"] != expected_result:
            fail(f"full ordered issue sequence: spec-{index + 1}:{issue_codes}")
        if graph["packet_content_hash"] != spec["post_packet_content_hash"] or graph["projection"]["projection_content_hash"] != spec["post_projection_content_hash"]:
            fail(f"post graph hash: spec-{index + 1}")
    if (len(identities), positives, rejects) != (236, 10, 226):
        fail("236/10/226 closure")
    identity_fields = ("pre_authority_identities", "instance_selector", "primary_operation", "linked_operations", "lane", "reseal_mode", "reseal_order", "reseal_plan")
    baseline_spec = specs[0]
    mutations = {
        "primary": lambda value: value["primary_operation"].__setitem__("value", "poison"),
        "linked": lambda value: value["linked_operations"].clear(),
        "instance": lambda value: value["instance_selector"].__setitem__("base_variant", "wrong"),
        "reseal": lambda value: value.__setitem__("reseal_mode", "none"),
        "order": lambda value: value["reseal_order"].reverse(),
        "pre_identity": lambda value: value["pre_authority_identities"].__setitem__("pre_packet", "0" * 64),
        "preserve_singular": lambda value: value["reseal_plan"].__setitem__("preserve_fields", ["/receipt/evaluation_content_identity"]),
        "preserve_deleted": lambda value: value["reseal_plan"].__setitem__("preserve_fields", []),
        "preserve_extra": lambda value: value["reseal_plan"].__setitem__("preserve_fields", ["/receipt/evaluation_content_identities", "/receipt/extra"]),
        "targets_reordered": lambda value: value["reseal_plan"]["ordered_targets"].reverse(),
    }
    preserve_spec = next(item for item in specs if item["reseal_plan"]["preserve_fields"])
    for label, mutate in mutations.items():
        source_spec = preserve_spec if label.startswith("preserve_") else baseline_spec
        candidate = {key: copy.deepcopy(source_spec[key]) for key in identity_fields}
        mutate(candidate)
        if digest(candidate) == source_spec["trace_identity"]:
            fail(f"spec identity mutation survived: {label}")
    return len(identities), positives, rejects


def apply_governance_mutation(document: dict[str, Any], mutation: dict[str, Any]) -> None:
    parts = mutation["path"].strip("/").split("/")
    current: Any = document
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    key = parts[-1]
    if mutation["op"] == "replace":
        if isinstance(current, list):
            current[int(key)] = copy.deepcopy(mutation["value"])
        else:
            current[key] = copy.deepcopy(mutation["value"])
    elif mutation["op"] == "reverse":
        target = current[int(key)] if isinstance(current, list) else current[key]
        target.reverse()
    else:
        fail("unsupported governance mutation")


def verify_governance() -> int:
    tests = load(OUT / "test_matrix.json")
    probes = tests["current_contract_verification"]["artifact_governance_probes"]
    parent = load_module(ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py", "accepted_parent_governance_for_v041_verifier")
    parent_exact = load(ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    for probe in probes:
        base = probe["base_artifact"]
        if base == "exact_overlay_artifact":
            candidate = load(PARENT_DIR / "exact_overlay.json"); apply_governance_mutation(candidate, probe["mutation"]); issue_codes = parent.overlay_validation_issues(candidate, parent_exact)
        elif base == "source_matrix_artifact":
            candidate = load(PARENT_DIR / "source_matrix.json"); apply_governance_mutation(candidate, probe["mutation"]); issue_codes = parent.source_matrix_validation_issues(candidate)
        else:
            candidate = load(PARENT_DIR / "manifest.json"); apply_governance_mutation(candidate, probe["mutation"]); candidate["manifest_content_hash"] = parent.canonical_hash({key: value for key, value in candidate.items() if key != "manifest_content_hash"}); issue_codes = parent.manifest_contract_validation_issues(candidate)
        if issue_codes != probe["actual_ordered_issues"] or probe["required_issue"] not in issue_codes:
            fail(f"governance ordered issues: {probe['probe_identity']}")
    if len(probes) != 22:
        fail("22 governance probes")
    return len(probes)


def expect_problem(label: str, issues: list[str]) -> None:
    if not issues:
        fail(f"active attack survived: {label}")


def verify_active_attacks(independent: Any, manifest: dict[str, Any], api: dict[str, Any], joins: dict[str, Any], errors: dict[str, Any]) -> int:
    count = 0
    manifest_attacks = [
        ("accepted_pin", ("authority_chain_pins", next(iter(manifest["authority_chain_pins"])))),
        ("rejected_pin", ("rejected_implementation_snapshots_negative_evidence_only", "v0_1")),
        ("typed_pin", ("typed_source_pins", next(iter(manifest["typed_source_pins"])))),
        ("root_pin", ("protected_pins", "r5_root_init_sha256")),
        ("s4_pin", ("protected_pins", "s4_acceptance_record_sha256")),
        ("mw_542", ("protected_pins", "medical_writing_protected_file_count")),
    ]
    for label, path in manifest_attacks:
        candidate = copy.deepcopy(manifest)
        parent = candidate
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = "drift" if not isinstance(parent[path[-1]], int) else 541
        candidate["manifest_content_hash"] = digest({key: value for key, value in candidate.items() if key != "manifest_content_hash"})
        problems = []
        if candidate != manifest:
            problems.append("pinned exact disagreement")
        expect_problem(label, problems); count += 1
    for key in ("producer_executed", "runtime_tests_executed", "evidence_created"):
        candidate = copy.deepcopy(manifest); candidate[key] = True
        expect_problem(key, [] if candidate[key] is False else ["false claim"]); count += 1
    candidate = copy.deepcopy(manifest); candidate["acceptance_token"] = "forbidden"
    expect_problem("acceptance_token", ["forbidden key"] if "acceptance_token" in candidate else []); count += 1
    for key in ("authority_scope", "execution_profile", "temporal_v01_manifest_sha256", "temporal_v02_manifest_sha256"):
        candidate = copy.deepcopy(api); candidate["authority_bundle_contract"][key] = "wrong"
        problems = [] if candidate["authority_bundle_contract"] == api["authority_bundle_contract"] else ["authority contract drift"]
        expect_problem(f"api_{key}", problems); count += 1
    temporal_schema = load(TEMPORAL / "schema.json")
    attack_runtime = baseline_runtime(independent)
    subject_bundle = attack_runtime[SUBJECT]["bundle"]
    aemh_bundle = attack_runtime[AEMH]["bundle"]
    bundle_attacks = [
        ("authority_extra_key", lambda value: value.__setitem__("extra", True)),
        ("authority_missing_key", lambda value: value.pop("schema_version")),
        ("authority_wrong_type", lambda value: value.__setitem__("bundle_content_identity", 1)),
        ("authority_contract", lambda value: value.__setitem__("contract_id", "wrong")),
        ("authority_schema", lambda value: value.__setitem__("schema_version", "wrong")),
        ("authority_scope", lambda value: value.__setitem__("authority_scope", "wrong")),
        ("authority_profile", lambda value: value.__setitem__("execution_profile", "wrong")),
        ("authority_target", lambda value: value.__setitem__("target_contract", "wrong")),
        ("authority_v01_pin", lambda value: value.__setitem__("temporal_v01_manifest_sha256", "0" * 64)),
        ("authority_source_variant", lambda value: value.__setitem__("source", copy.deepcopy(aemh_bundle["source"]))),
    ]
    for label, mutate in bundle_attacks:
        candidate = copy.deepcopy(subject_bundle); mutate(candidate)
        expect_problem(label, independent.authority_issues(candidate, temporal_schema)); count += 1
    for forbidden_key in ("candidate_packet", "parent_packet", "expected_packet", "target_output", "case_id", "sentinel"):
        candidate = copy.deepcopy(subject_bundle); candidate[forbidden_key] = {}
        expect_problem(f"self_authority_{forbidden_key}", independent.authority_issues(candidate, temporal_schema)); count += 1
    for label, mutate in (
        ("join_duplicate", lambda value: value["rows"].__setitem__(1, copy.deepcopy(value["rows"][0]))),
        ("join_missing", lambda value: value["rows"].pop()),
        ("join_future", lambda value: value["rows"][0]["dependency_output_leaves"].append(value["rows"][1]["qualified_leaf"])),
        ("join_candidate", lambda value: value["rows"][0]["v02_authority_selector"].__setitem__("json_pointer", "/candidate")),
        ("join_mirror", lambda value: value["rows"][0].__setitem__("mirror_forbidden", False)),
        ("selector_zero", lambda value: value["rows"][0]["v02_authority_selector"].__setitem__("json_pointer", "/source/missing")),
        ("selector_many", lambda value: value["rows"][0].__setitem__("selector_cardinality", "ordered-many")),
        ("selector_cross_scope", lambda value: value["rows"][0].__setitem__("contract", AEMH)),
        ("selector_wrong_key", lambda value: value["rows"][0].__setitem__("key_selector", "wrong.key")),
        ("selector_same_type_swap", lambda value: value["rows"][0]["typed_source_selector"].update({"field": "run_id", "selector": "MonitoringRun.run_id"})),
        ("selector_reflection", lambda value: value["rows"][0].__setitem__("authority_source_kind", "candidate_reflection")),
    ):
        candidate = copy.deepcopy(joins); mutate(candidate)
        expect_problem(label, join_issues(candidate, baseline_runtime(independent))); count += 1
    for label, mutate in (
        ("error_priority", lambda value: value["errors"][0].__setitem__("priority", 2)),
        ("error_missing", lambda value: value["errors"].pop()),
        ("error_primary", lambda value: value.__setitem__("primary_code", "last issue")),
        ("error_packet", lambda value: value.__setitem__("any_issue_forbids_packet", False)),
    ):
        candidate = copy.deepcopy(errors); mutate(candidate)
        expect_problem(label, error_issues(candidate)); count += 1
    recipe_registry = load(TEMPORAL / "emitter_recipe_registry.json")
    schema = load(TEMPORAL / "schema.json")
    for label, mutate in (
        ("recipe_unknown_op", lambda value: value["executable_v02_recipes"][0]["nodes"][0].__setitem__("op", "unknown")),
        ("recipe_swapped_op", lambda value: value["executable_v02_recipes"][0]["nodes"][0].__setitem__("op", value["executable_v02_recipes"][1]["nodes"][0]["op"])),
        ("recipe_phase", lambda value: value["executable_v02_recipes"][0]["nodes"][0]["params"].__setitem__("phase", "packet")),
        ("recipe_output", lambda value: value["executable_v02_recipes"][0]["nodes"][0]["outputs"].append("extra")),
        ("recipe_missing_node", lambda value: value["executable_v02_recipes"][0]["nodes"].pop()),
        ("recipe_extra_node", lambda value: value["executable_v02_recipes"][0]["nodes"].append(copy.deepcopy(value["executable_v02_recipes"][0]["nodes"][0]))),
        ("recipe_input_drift", lambda value: value["executable_v02_recipes"][0]["nodes"][0]["inputs"].append("/source/extra")),
        ("recipe_reorder", lambda value: value["executable_v02_recipes"].reverse()),
        ("recipe_cycle", lambda value: value["executable_v02_recipes"][0]["nodes"][0]["params"]["prior_recipe_output_refs"].append(value["executable_v02_recipes"][0]["nodes"][1]["outputs"][0])),
        ("recipe_cross_target", lambda value: value["executable_v02_recipes"][0]["nodes"][0]["params"]["prior_recipe_output_refs"].append("recipe.v02.aemh_packet.sealed")),
    ):
        candidate = copy.deepcopy(recipe_registry); mutate(candidate)
        problems = independent.recipe_ir_issues(candidate, schema)
        if not problems:
            try:
                independent.execute_independent_recipe_dag(baseline_runtime(independent)[SUBJECT]["bundle"], candidate)
            except (SystemExit, KeyError, ValueError, TypeError, IndexError) as exc:
                problems = [type(exc).__name__]
        expect_problem(label, problems); count += 1
    tests = load(OUT / "test_matrix.json")
    for label, mutate in (
        ("linked_missing", lambda value: value["current_contract_verification"]["runtime_specifications"][0]["linked_operations"].clear()),
        ("linked_fake", lambda value: value["current_contract_verification"]["runtime_specifications"][0]["linked_operations"].append({"op": "fake", "target": "/"})),
        ("reseal_order", lambda value: value["current_contract_verification"]["runtime_specifications"][0]["reseal_order"].reverse()),
    ):
        candidate = copy.deepcopy(tests); mutate(candidate)
        original_hash = digest(tests["current_contract_verification"]["runtime_specifications"])
        problems = [] if digest(candidate["current_contract_verification"]["runtime_specifications"]) == original_hash else ["trace registry drift"]
        expect_problem(label, problems); count += 1
    if count < 30:
        fail("active attack minimum")
    return count


def medical_writing_inventory(contract: dict[str, Any]) -> tuple[int, str]:
    paths = []
    regex = __import__("re").compile(contract["relative_path_regex"])
    for root_rel in contract["roots"]:
        root = ROOT / root_rel
        for path in root.rglob("*"):
            if path.is_file():
                relative = path.relative_to(ROOT).as_posix()
                if regex.search(relative):
                    paths.append(relative)
    payload = b"".join(relative.encode() + b"\0" + raw_sha(ROOT / relative).encode() + b"\n" for relative in sorted(paths))
    return len(paths), hashlib.sha256(payload).hexdigest()


def verify_future_machine_spec() -> None:
    tests = load(OUT / "test_matrix.json")
    outer = tests.get("future_producer_acceptance")
    if not isinstance(outer, dict) or set(outer) != {"create_only_allowlist", "files_present", "producer_executed", "runtime_tests_executed", "ast_executed", "sensitivity_executed", "isolation_executed", "machine_executable_spec"}:
        fail("future acceptance exact schema")
    if any(outer[key] is not False for key in ("files_present", "producer_executed", "runtime_tests_executed", "ast_executed", "sensitivity_executed", "isolation_executed")):
        fail("future acceptance false flags")
    spec = outer["machine_executable_spec"]
    expected_keys = {"schema", "path_specs", "module_count", "public_signatures", "dataclass_constructors", "ast", "pytest_node_ids", "commands", "sensitivity_vectors", "isolation", "executed"}
    if set(spec) != expected_keys or spec["schema"] != "future-public-authority-producer-gates-v0.4.1" or spec["executed"] is not False or spec["module_count"] != 10:
        fail("future machine exact schema")
    if [row["path"] for row in spec["path_specs"]] != FUTURE_PATHS or outer["create_only_allowlist"] != FUTURE_PATHS:
        fail("future exact 11 paths")
    for relative, row in zip(FUTURE_PATHS, spec["path_specs"]):
        if set(row) != {"path", "absolute_path", "module", "kind", "create_only"} or row["absolute_path"] != str((ROOT / relative).resolve()) or row["create_only"] is not True:
            fail(f"future path spec: {relative}")
    expected_signatures = {
        ("mm_r5.public_authority_common", "canonical_json_bytes(value: object) -> bytes"),
        ("mm_r5.public_authority_common", "canonical_sha256(value: object) -> str"),
        ("mm_r5.public_authority_common", "validation_result(issues: Iterable[PublicAuthorityValidationIssue]) -> PublicAuthorityValidationResult"),
        ("mm_r5.subject_temporal_public", "build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket"),
        ("mm_r5.subject_temporal_public", "validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult"),
        ("mm_r5.aemh_match_history_public", "build_aemh_match_history_authority(source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> AEMHMatchHistoryAuthorityPacket"),
        ("mm_r5.aemh_match_history_public", "validate_aemh_match_history_authority(candidate: AEMHMatchHistoryAuthorityPacket, source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> PublicAuthorityValidationResult"),
    }
    if {(row.get("module"), row.get("signature")) for row in spec["public_signatures"]} != expected_signatures or any(set(row) != {"module", "signature"} for row in spec["public_signatures"]):
        fail("future exact public signatures")
    ast_contract = spec["ast"]
    expected_ast_keys = {"allowed_node_types", "denied_node_types", "unknown_node_policy", "mutation_controls", "allowed_import_roots", "denied_import_roots", "allowed_call_symbols", "denied_call_symbols", "reachable_call_rules"}
    allowed_nodes = ["Module", "Import", "ImportFrom", "ClassDef", "FunctionDef", "arguments", "arg", "Return", "Assign", "AnnAssign", "Expr", "If", "For", "comprehension", "Call", "Name", "Attribute", "Constant", "List", "Tuple", "Dict", "Set", "Subscript", "Slice", "BinOp", "BoolOp", "Compare", "UnaryOp", "keyword", "Raise", "Try", "ExceptHandler", "With", "withitem"]
    denied_nodes = ["AsyncFunctionDef", "Await", "Yield", "YieldFrom", "Global", "Nonlocal", "Assert", "Lambda", "NamedExpr"]
    if set(ast_contract) != expected_ast_keys or ast_contract["allowed_node_types"] != allowed_nodes or ast_contract["denied_node_types"] != denied_nodes or ast_contract["unknown_node_policy"] != "fail_closed":
        fail("future AST exact policy")
    controls = [
        {"node_type": "Assert", "mutation": "inject assert True", "expected_issue": "FUTURE_AST_NODE_DENIED"},
        {"node_type": "Lambda", "mutation": "inject lambda: None", "expected_issue": "FUTURE_AST_NODE_DENIED"},
        {"node_type": "NamedExpr", "mutation": "inject walrus expression", "expected_issue": "FUTURE_AST_NODE_DENIED"},
    ]
    if ast_contract["mutation_controls"] != controls:
        fail("future AST mutation controls")
    for control in controls:
        node = control["node_type"]
        if node in ast_contract["allowed_node_types"] or node not in ast_contract["denied_node_types"]:
            fail(f"future AST mutation survived: {node}")
    nodes = [
        f"{FUTURE_PATHS[4]}::test_canonical_json_bytes_exact", f"{FUTURE_PATHS[4]}::test_validation_result_total_order",
        f"{FUTURE_PATHS[5]}::test_subject_builder_returns_packet_only", f"{FUTURE_PATHS[5]}::test_subject_validator_rebuilds_construction_graph",
        f"{FUTURE_PATHS[6]}::test_aemh_builder_returns_packet_only", f"{FUTURE_PATHS[6]}::test_aemh_validator_preserves_history",
        f"{FUTURE_PATHS[7]}::test_all_272_exact_joins", f"{FUTURE_PATHS[7]}::test_subject_common_cutoff_instance",
        f"{FUTURE_PATHS[8]}::test_all_authority_pins", f"{FUTURE_PATHS[8]}::test_no_side_effects",
        f"{FUTURE_PATHS[9]}::test_all_236_runtime_specs", f"{FUTURE_PATHS[9]}::test_all_192_error_replays",
    ]
    commands = [
        {"mode": "normal", "argv": ["python3", "-B", "-m", "pytest", *nodes]},
        {"mode": "O", "argv": ["python3", "-O", "-B", "-m", "pytest", *nodes]},
        {"mode": "OO", "argv": ["python3", "-OO", "-B", "-m", "pytest", *nodes]},
    ]
    if spec["pytest_node_ids"] != nodes or spec["commands"] != commands:
        fail("future exact pytest commands")
    if len(spec["sensitivity_vectors"]) != 10 or digest(spec["sensitivity_vectors"]) != "613dc35dde1c7896a9518f0bd52ad2a3b7b62828e06cbacd08f349ea2fcf6d4b":
        fail("future exact sensitivity vectors")
    isolation = spec["isolation"]
    entry = str((ROOT / FUTURE_PATHS[8]).resolve())
    isolation_keys = {"test_entry_relative", "test_entry_absolute", "argv", "entry_cli_contract", "bootstrap_paths", "bootstrap_sequence", "import_before_hook_forbidden", "hook_install_precedes_candidate_import", "hook_scope", "deny_families", "api_call_windows"}
    if set(isolation) != isolation_keys or isolation["test_entry_relative"] != FUTURE_PATHS[8] or isolation["test_entry_absolute"] != entry or isolation["argv"] != ["python3", "-I", "-B", entry, "--isolation-probe"]:
        fail("future isolation entry/argv")
    if isolation["entry_cli_contract"] != {"main_signature": "main(argv: list[str]) -> int", "probe_flag": "--isolation-probe", "unknown_arg_policy": "exit_nonzero", "normal_pytest_import_safe": True}:
        fail("future isolation CLI contract")
    if isolation["bootstrap_paths"] != {"src": str((ROOT / "poc/medical_monitoring_ai_native_r5/src").resolve()), "tests": str((ROOT / "poc/medical_monitoring_ai_native_r5/tests").resolve())}:
        fail("future isolation bootstrap paths")
    sequence = ["bootstrap_exact_local_src_tests_paths", "import_exact_candidate_modules_and_support", "construct_synthetic_inputs", "install_denial_hooks", "execute_four_public_api_call_windows", "remove_denial_hooks", "emit_probe_result"]
    if isolation["bootstrap_sequence"] != sequence or isolation["import_before_hook_forbidden"] is not False or isolation["hook_install_precedes_candidate_import"] is not False or isolation["hook_scope"] != "only_four_public_api_call_windows":
        fail("future isolation bootstrap/hook scope")
    if set(isolation["deny_families"]) != {"filesystem", "network", "subprocess", "dynamic_code"} or len(isolation["api_call_windows"]) != 4 or any(not row.get("positive_control") or not row.get("negative_control") for row in isolation["api_call_windows"]):
        fail("future isolation controls")


def verify_protection_and_absence(manifest: dict[str, Any]) -> None:
    protected = manifest["protected_pins"]
    if raw_sha(ROOT / "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py") != protected["r5_root_init_sha256"]:
        fail("root init drift")
    if raw_sha(ROOT / "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json") != protected["accepted_r4_r5_s4_readonly_manifest_sha256"]:
        fail("S4 readonly drift")
    count, aggregate = medical_writing_inventory(protected["medical_writing_inventory_contract"])
    if (count, aggregate) != (542, "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"):
        fail(f"medical-writing protected inventory: {count}:{aggregate}")
    producer = set(manifest["future_producer_allowlist"])
    if any((ROOT / relative).exists() for relative in producer | S5_LOCKS):
        fail("future producer/S5 absence")
    forbidden_cache = [path for path in (ROOT / "poc/medical_monitoring_ai_native_r5").rglob("*.pyc") if "public_authority" in path.name or "s5_" in path.name or "test_s5" in path.name]
    if forbidden_cache:
        fail(f"future bytecode/cache absence: {forbidden_cache[:3]}")
    if {path.name for path in OUT.iterdir()} != {"public_api.json", "source_join_matrix.json", "invariant_error_matrix.json", "test_matrix.json", "manifest.json"}:
        fail("five artifact exact set")
    with socket.socket() as sock:
        sock.settimeout(0.2)
        if sock.connect_ex(("127.0.0.1", 8911)) == 0:
            fail("port 8911 listening")


def verify_generation_and_ruff() -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.run([sys.executable, "-B", str(GENERATOR), "--check"], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    with tempfile.TemporaryDirectory(prefix="v041-a-") as first, tempfile.TemporaryDirectory(prefix="v041-b-") as second:
        for target in (first, second):
            subprocess.run([sys.executable, "-B", str(GENERATOR), "--output-root", target], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
        for relative in EXACT_PATHS:
            if (pathlib.Path(first) / relative).read_bytes() != (pathlib.Path(second) / relative).read_bytes():
                fail(f"double generation drift: {relative}")
    subprocess.run([
        "/Users/smkzw/.local/bin/uvx", "--offline", "ruff", "check", "--no-cache", str(GENERATOR.relative_to(ROOT)), str(VERIFIER.relative_to(ROOT)),
    ], cwd=ROOT, env=env, check=True, capture_output=True, text=True)


def main() -> int:
    verify_static_tools()
    manifest = verify_manifest()
    api = verify_api()
    independent = engine()
    runtime = baseline_runtime(independent)
    joins = verify_joins(independent, runtime)
    errors = verify_errors()
    specs, positives, rejects = replay_specs(independent)
    governance = verify_governance()
    attacks = verify_active_attacks(independent, manifest, api, joins, errors)
    verify_future_machine_spec()
    verify_protection_and_absence(manifest)
    verify_generation_and_ruff()
    print(json.dumps({"status": "PASS", "optimize": sys.flags.optimize, "baselines": "2/2", "specs": f"{specs}/{specs}/0", "positives": f"{positives}/10", "rejects": f"{rejects}/226", "joins": "272/272", "recipes": "16/32", "governance": f"{governance}/22", "active_attacks": attacks, "producer_executed": False, "port_8911": "stopped"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
