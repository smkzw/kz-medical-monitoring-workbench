"""Independently verify public-authority implementation contract v0.4."""

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
OUT = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4"
PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
TEMPORAL = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
GENERATOR = ROOT / "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py"
VERIFIER = pathlib.Path(__file__).resolve()
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.4"

EXACT_PATHS = {
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_20260821.md",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/public_api.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/source_join_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/invariant_error_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/test_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4.py",
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


def engine() -> Any:
    return load_module(
        ROOT / "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "accepted_temporal_v02_independent_engine_for_v04",
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
    if any("public_authority_implementation_contract_v0_4" in name for name in imports):
        fail("mutual v0.4 import/reference forbidden")
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
            fail(f"v0.4 raw pin drift: {relative}")
    for surface in ("authority_chain_pins", "typed_source_pins", "temporal_v02_nine_file_pins"):
        for relative, expected in manifest[surface].items():
            if raw_sha(ROOT / relative) != expected:
                fail(f"{surface} drift: {relative}")
    temporal_manifest = load(TEMPORAL / "manifest.json")
    if manifest["typed_source_pins"] != temporal_manifest["typed_source_pins"]:
        fail("duplicate typed pin disagreement")
    expected_counts = {"spec_count": 236, "unique_trace_count": 236, "alias_count": 0, "positive_count": 10, "reject_count": 226, "leaf_count": 272, "recipe_count": 16, "recipe_node_count": 32, "artifact_governance_probe_count": 22}
    if manifest.get("counts") != expected_counts:
        fail("manifest counts")
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


def ast_field_exists(selector: dict[str, str]) -> bool:
    tree = ast.parse((ROOT / selector["path"]).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == selector["class"]:
            return any(isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id == selector["field"] for item in node.body)
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


def expected_typed_selector(leaf: str) -> dict[str, str]:
    lowered = leaf.lower()
    candidates = [
        (("project",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "MonitoringRun", "project_id"),
        (("run",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "MonitoringRun", "run_id"),
        (("snapshot",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "ListingSnapshot", "snapshot_version"),
        (("revision",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "SourceRevision", "revision_id"),
        (("cutoff", "date", "endpoint", "timezone", "study_day"), "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py", "TimeRef", "value"),
        (("locator", "source"), "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py", "SourceLocator", "source_locator_id"),
        (("visit",), "poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py", "PlannedVisitMarker", "planned_visit_id"),
        (("event",), "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py", "TemporalEvent", "event_id"),
        (("risk", "severity"), "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py", "S4AcceptedRiskIdentity", "risk_ref"),
        (("thread", "match", "candidate", "fact", "history", "evidence"), "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py", "AEMHResult", "reported_facts"),
        (("domain", "subtype"), "poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py", "SemanticRecord", "role"),
        (("subject", "site", "spine"), "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py", "S4AcceptedRiskIdentity", "subject_ref"),
    ]
    for tokens, path, class_name, field in candidates:
        if any(token in lowered for token in tokens):
            return {"path": path, "class": class_name, "field": field, "selector": f"{class_name}.{field}"}
    return {"path": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py", "class": "D08TypedInput", "field": "scope_binding", "selector": "D08TypedInput.scope_binding"}


def join_issues(joins: dict[str, Any], runtime: dict[str, dict[str, Any]]) -> list[str]:
    issues = []
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
        if not ast_field_exists(row["typed_source_selector"]):
            issues.append(f"typed:{index}")
        if row["typed_source_selector"] != expected_typed_selector(row["leaf"]):
            issues.append(f"typed_semantic:{index}")
        parent_schema = load(PARENT_DIR / ("subject_temporal_schema.json" if row["contract"] == SUBJECT else "aemh_match_history_schema.json"))
        if row["key_selector"] != f"{row['object_type']}.{next(iter(parent_schema['objects'][row['object_type']]))}":
            issues.append(f"key_selector:{index}")
        expected_cardinality = "ordered-many" if row["cardinality"] == "many" else "zero-or-one" if row["nullable"] else "exact-one"
        if row["selector_cardinality"] != expected_cardinality or row["authority_source_kind"] != "dual_typed_and_accepted_v02":
            issues.append(f"selector_contract:{index}")
        recipe = recipe_by_id.get(row["recipe_id"], {})
        pointers = recipe.get("nodes", [{}])[0].get("params", {}).get("authority_input_pointers", [])
        expected_v02_pointer = pointers[0] if pointers else "/source"
        if row["v02_authority_selector"].get("json_pointer") != expected_v02_pointer:
            issues.append(f"v02_selector:{index}")
        try:
            json_get(runtime[row["contract"]]["bundle"], row["v02_authority_selector"]["json_pointer"])
            selector = row.get("recipe_leaf_selector")
            if selector:
                binding = runtime[row["contract"]]["bundle"]["source"]["cutoff_binding"]
                virtual = {"state": binding["state"], "exact_date": binding["exact_date"], "source_locator_refs": sorted(binding["source_locator_refs"])}
                virtual["cutoff_content_hash"] = digest(virtual)
                final_value = virtual[selector["field"]]
                stage_value = virtual[selector["field"]]
            else:
                prefix = f"/{row['contract']}"
                if not row["output_json_pointer"].startswith(prefix):
                    raise KeyError("contract-qualified output pointer")
                packet_pointer = row["output_json_pointer"][len(prefix):]
                final_value = json_get(runtime[row["contract"]]["packet"], packet_pointer)
                stage = runtime[row["contract"]]["outputs"][row["recipe_node_output_ref"]]["value"]
                stage_value = json_get(stage, row["recipe_output_json_pointer"])
            if final_value != stage_value:
                issues.append(f"join:{index}")
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
    if matrix.get("counts") != {"parent": 81, "semantic_delta": 49, "temporal_delta": 62, "union": 192}:
        issues.append("counts")
    rows = matrix.get("errors", [])
    if len(rows) != 192 or [row.get("priority") for row in rows] != list(range(1, 193)):
        issues.append("priority")
    if len({(row.get("code"), row.get("path"), row.get("origin"), row.get("message_semantics")) for row in rows}) != 192:
        issues.append("dedup")
    if matrix.get("any_issue_forbids_packet") is not True or matrix.get("primary_code") != "first ordered issue code":
        issues.append("result_semantics")
    return issues


def verify_errors() -> dict[str, Any]:
    matrix = load(OUT / "invariant_error_matrix.json")
    issues = error_issues(matrix)
    if issues:
        fail("error matrix: " + "|".join(issues))
    return matrix


def replay_specs(independent: Any) -> tuple[int, int, int]:
    tests = load(OUT / "test_matrix.json")
    specs = tests["current_contract_verification"]["runtime_specifications"]
    if len(specs) != 236 or len({row["trace_identity"] for row in specs}) != 236:
        fail("test spec identity inventory")
    frozen = {row["trace_identity"]: row for row in specs}
    accepted = load(TEMPORAL / "trace_realization_registry.json")
    recipes = load(TEMPORAL / "emitter_recipe_registry.json")
    parent = independent.parent_module()
    subject_schema = load(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = load(PARENT_DIR / "aemh_match_history_schema.json")
    error_by_code = {row["code"]: row for row in load(OUT / "invariant_error_matrix.json")["errors"]}
    positives = rejects = 0
    identities = set()
    for record in accepted["records"]:
        base = copy.deepcopy(accepted["base_authority_inputs"][record["base_input_ref"]])
        target = record["contract"]
        previous = None
        if record["expected_disposition"] == "accept":
            operations = sorted([record["realized_mutation"], *record["linked_operations"]], key=lambda item: item["sequence"])
            for operation in operations:
                if independent.pointer_get(base, operation["path"]) != operation["pre_value"]:
                    fail(f"trace pre: {record['source_case_ref']}")
                independent.apply_source_operation(base, operation)
                if independent.pointer_get(base, operation["path"]) != operation["post_value"]:
                    fail(f"trace post: {record['source_case_ref']}")
            independent.reseal_bundle(base)
            built, _ = independent.execute_independent_recipe_dag(base, recipes)
            if target == SUBJECT:
                graph = built; issue_codes = independent.validate_parent(target, graph)
            else:
                previous, graph = built
                issue_codes = [*independent.validate_parent(target, previous, None), *independent.validate_parent(target, graph, previous)]
            positives += 1
        else:
            built, _ = independent.execute_independent_recipe_dag(base, recipes)
            if target == SUBJECT:
                graph = copy.deepcopy(built)
            else:
                previous, current = built; graph = copy.deepcopy(current)
            parent.apply_mutation(graph, record["realized_mutation"])
            if record["reseal_mode"] != "none":
                preserve = any("EVALUATION_IDENTITY" in code for code in record["observed_ordered_issues"])
                if target == SUBJECT:
                    parent.reseal_subject_packet(graph, subject_schema, preserve_evaluation=preserve)
                else:
                    parent.reseal_aemh_packet(graph, aemh_schema, preserve_evaluation=preserve)
            issue_codes = independent.validate_parent(target, graph, previous)
            rejects += 1
        identity = digest({"base_input_content_identity": record["base_input_content_identity"], "realized_mutation": record["realized_mutation"], "linked_operations": record["linked_operations"], "lane": record["lane"]})
        spec = frozen.get(identity)
        if spec is None or identity in identities:
            fail(f"trace identity: {record['source_case_ref']}")
        identities.add(identity)
        issue_objects = [{"code": code, "path": error_by_code[code]["path"], "message": error_by_code[code]["message_semantics"], "origin": error_by_code[code]["origin"], "priority": error_by_code[code]["priority"]} for code in issue_codes]
        expected_result = {"ok": not issue_codes, "primary_code": issue_codes[0] if issue_codes else None, "ordered_issue_codes": issue_codes, "ordered_issues": issue_objects, "packet_emitted": not issue_codes}
        if spec["actual_ordered_issues"] != issue_codes or spec["actual_ordered_issue_objects"] != issue_objects or spec["future_validator_expected"] != expected_result:
            fail(f"full ordered issue sequence: {record['source_case_ref']}:{issue_codes}")
        if graph["packet_content_hash"] != spec["post_packet_content_hash"] or graph["projection"]["projection_content_hash"] != spec["post_projection_content_hash"]:
            fail(f"post graph hash: {record['source_case_ref']}")
    if (len(identities), positives, rejects) != (236, 10, 226):
        fail("236/10/226 closure")
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
    parent = load_module(ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py", "accepted_parent_governance_for_v04_verifier")
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
    with tempfile.TemporaryDirectory(prefix="v04-a-") as first, tempfile.TemporaryDirectory(prefix="v04-b-") as second:
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
    verify_protection_and_absence(manifest)
    verify_generation_and_ruff()
    print(json.dumps({"status": "PASS", "optimize": sys.flags.optimize, "baselines": "2/2", "specs": f"{specs}/{specs}/0", "positives": f"{positives}/10", "rejects": f"{rejects}/226", "joins": "272/272", "recipes": "16/32", "governance": f"{governance}/22", "active_attacks": attacks, "producer_executed": False, "port_8911": "stopped"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
