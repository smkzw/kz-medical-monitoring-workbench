"""Independently verify public-authority implementation contract v0.3."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.3"
SCHEMA_VERSION = "2026-08-20.4"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
ARTIFACT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3"
PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
SEMANTIC_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1"
TEMPORAL_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1"
GENERATOR_PATH = ROOT / "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py"
VERIFIER_PATH = Path(__file__).resolve()

PARENT_MANIFEST_SHA = "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270"
PARENT_ACCEPTANCE_SHA = "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d"
SEMANTIC_MANIFEST_SHA = "66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d"
SEMANTIC_ACCEPTANCE_SHA = "bf50156fa82d825309fce72115ddf971fc4e0bdbd60936ea45e2362a6aa3eb4c"
TEMPORAL_MANIFEST_SHA = "e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97"
TEMPORAL_ACCEPTANCE_SHA = "523351f1b5536b12c1a5be9251ad01f4e8b7a70f5088073a2333aefc241d1b79"

EXACT_PATHS = {
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3_20260820.md",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/public_api.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/source_join_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/invariant_error_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/test_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3.py",
}

ALIASES = {
    "PA-007": ["R5C-103"],
    "PA-034": ["PA-120"],
    "PA-035": ["PA-121"],
    "PA-118": ["R5C-108"],
    "PA-129": ["R5C-111"],
}


def fail(message: str) -> None:
    raise SystemExit(f"PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_3_VERIFY_FAIL: {message}")


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read JSON {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"JSON root is not object: {path}")
    return value


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f"cannot load pinned verifier: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def optimization_args() -> list[str]:
    if sys.flags.optimize == 1:
        return ["-O"]
    if sys.flags.optimize >= 2:
        return ["-OO"]
    return []


def run_pinned_verifier(relative: str) -> None:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, *optimization_args(), "-B", relative]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=240,
    )
    if completed.returncode != 0:
        tail = (completed.stdout + "\n" + completed.stderr)[-4000:]
        fail(f"accepted surface verifier failed: {relative}: {tail}")


def verify_no_assert_statements() -> None:
    for path in (GENERATOR_PATH, VERIFIER_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        lines = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        if lines:
            fail(f"assert statement forbidden: {path.name}:{lines}")
    generator_tree = ast.parse(GENERATOR_PATH.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(generator_tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    if any("verify_medical_monitoring" in name for name in imports):
        fail("generator imports a verifier")


def verify_exact_paths(manifest: dict[str, Any]) -> None:
    if set(manifest.get("exact_implementation_contract_paths", [])) != EXACT_PATHS:
        fail("exact nine-file allowlist mismatch")
    missing = [relative for relative in EXACT_PATHS if not (ROOT / relative).is_file()]
    if missing:
        fail(f"missing v0.3 paths: {missing}")
    actual_artifacts = {
        str(path.relative_to(ROOT)) for path in ARTIFACT_DIR.iterdir() if path.is_file()
    }
    expected_artifacts = {relative for relative in EXACT_PATHS if relative.startswith("artifacts/")}
    if actual_artifacts != expected_artifacts:
        fail(f"artifact path set mismatch: {sorted(actual_artifacts)}")


def verify_manifest() -> dict[str, Any]:
    manifest = read_json(ARTIFACT_DIR / "manifest.json")
    if manifest.get("contract_id") != CONTRACT_ID or manifest.get("schema_version") != SCHEMA_VERSION:
        fail("manifest identity/version mismatch")
    claimed = manifest.get("manifest_content_hash")
    core = {key: value for key, value in manifest.items() if key != "manifest_content_hash"}
    if claimed != digest(core):
        fail("manifest content hash mismatch")
    verify_exact_paths(manifest)
    for relative, expected in manifest.get("artifact_raw_sha256", {}).items():
        if raw_sha(ROOT / relative) != expected:
            fail(f"generated artifact drift: {relative}")
    expected_artifacts = {
        "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/public_api.json",
        "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/source_join_matrix.json",
        "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/invariant_error_matrix.json",
        "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_3/test_matrix.json",
    }
    if set(manifest.get("artifact_raw_sha256", {})) != expected_artifacts:
        fail("manifest generated-artifact pin set mismatch")
    authority = manifest.get("authority_consumption", {})
    if authority != {
        "leaf_bijection": 272,
        "authority_emitters": 119,
        "accepted_recipe_definitions": 18,
        "semantic_leaves": 4,
        "fourth_local_authority_layer_created": False,
    }:
        fail("authority consumption declaration mismatch")
    counts = manifest.get("future_runtime_spec_counts")
    if counts != {"distinct_specs": 231, "accepted_traces": 236, "aliases": 5, "governance_probes": 22}:
        fail("future spec count declaration mismatch")
    unlock = manifest.get("unlock", {})
    if unlock.get("only_later_exact_token") != "ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_3":
        fail("unlock token mismatch")
    if unlock.get("self_acceptance_forbidden") is not True:
        fail("self-acceptance boundary missing")
    return manifest


def verify_pin_map(pins: dict[str, str], label: str) -> None:
    for relative, expected in pins.items():
        path = ROOT / relative
        if not path.is_file() or raw_sha(path) != expected:
            fail(f"{label} pin drift: {relative}")


def verify_surface_pins(manifest: dict[str, Any]) -> None:
    expected_roots = {
        "accepted_parent": (PARENT_MANIFEST_SHA, PARENT_ACCEPTANCE_SHA),
        "accepted_semantic_delta": (SEMANTIC_MANIFEST_SHA, SEMANTIC_ACCEPTANCE_SHA),
        "accepted_temporal_delta": (TEMPORAL_MANIFEST_SHA, TEMPORAL_ACCEPTANCE_SHA),
    }
    surfaces = manifest.get("accepted_authority_surfaces", {})
    if set(surfaces) != set(expected_roots):
        fail("accepted authority surface set mismatch")
    for name, (manifest_sha, acceptance_sha) in expected_roots.items():
        surface = surfaces[name]
        if surface.get("manifest_raw_sha256") != manifest_sha or surface.get("acceptance_raw_sha256") != acceptance_sha:
            fail(f"accepted surface hard pin mismatch: {name}")
        if raw_sha(ROOT / surface["manifest_path"]) != manifest_sha:
            fail(f"accepted manifest bytes changed: {name}")
        if raw_sha(ROOT / surface["acceptance_path"]) != acceptance_sha:
            fail(f"accepted record bytes changed: {name}")
        verify_pin_map(surface["artifact_raw_sha256"], f"{name} artifact")
    rejected = manifest.get("rejected_snapshots_negative_evidence_only", {})
    if rejected.get("authority") is not False:
        fail("rejected snapshot promoted to authority")
    verify_pin_map(rejected.get("v0_1", {}), "rejected v0.1")
    verify_pin_map(rejected.get("v0_2", {}), "rejected v0.2")
    verify_pin_map(manifest.get("source_file_sha256", {}), "typed source")
    protected = manifest.get("protected_accepted_pins", {})
    verify_pin_map(protected.get("protected_path_sha256", {}), "protected accepted")


def verify_medical_writing_inventory(manifest: dict[str, Any]) -> None:
    contract = manifest["protected_accepted_pins"]["medical_writing_inventory_contract"]
    records: list[tuple[str, str]] = []
    for root_name in contract["roots"]:
        root = ROOT / root_name
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix()
            lowered = relative.lower()
            if "medical-writing" in lowered or "medical_writing" in lowered:
                records.append((relative, raw_sha(path)))
    records.sort(key=lambda pair: pair[0].encode("utf-8"))
    payload = b"".join(
        relative.encode("utf-8") + b"\0" + value.encode("ascii") + b"\n"
        for relative, value in records
    )
    if len(records) != 542:
        fail(f"medical-writing file count drift: {len(records)}")
    if hashlib.sha256(payload).hexdigest() != "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca":
        fail("medical-writing aggregate drift")


def _class_catalog(api: dict[str, Any], key: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for module in api["modules"].values():
        for item in module.get(key, []):
            if item["name"] in result and result[item["name"]] != item:
                fail(f"conflicting API class: {item['name']}")
            result[item["name"]] = item
    return result


def verify_public_api() -> dict[str, Any]:
    api = read_json(ARTIFACT_DIR / "public_api.json")
    if api.get("contract_id") != CONTRACT_ID or api.get("schema_version") != SCHEMA_VERSION:
        fail("public API identity mismatch")
    if api.get("python") != {
        "minimum": "3.9",
        "frozen_dataclasses": True,
        "pep604_union_forbidden": True,
        "root_init_frozen": True,
        "imports": "full module path only",
    }:
        fail("Python API contract mismatch")
    subject_schema = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    semantic_schema = read_json(SEMANTIC_DIR / "schema.json")
    temporal_schema = read_json(TEMPORAL_DIR / "schema.json")
    accepted_bundle_expectations = {
        "AcceptedSemanticAuthorityBundle": semantic_schema,
        "AcceptedTemporalProjectionAuthorityBundle": temporal_schema,
    }
    for bundle_name, accepted_schema in accepted_bundle_expectations.items():
        bundle = api.get("accepted_bundle_types", {}).get(bundle_name, {})
        observed = bundle.get("exact_dataclass_signatures", [])
        expected: list[dict[str, Any]] = []
        for name, definition in sorted(accepted_schema["objects"].items()):
            properties = definition.get("properties", definition.get("fields", {}))
            order = definition.get("required", definition.get("exact_keys", list(properties)))
            expected.append(
                {
                    "name": name,
                    "decorator": "dataclasses.dataclass(frozen=True)",
                    "fields_in_exact_order": [
                        {"name": field, **properties[field]} for field in order
                    ],
                    "additional_properties": definition.get("additional_properties", False),
                    "accepted_definition_content_hash": canonical_sha(definition),
                }
            )
        if observed != expected:
            fail(f"accepted bundle signature drift: {bundle_name}")
    outputs = _class_catalog(api, "output_classes")
    results = _class_catalog(api, "result_classes")
    if set(results) != {"PublicAuthorityValidationIssue", "PublicAuthorityValidationResult"}:
        fail("exact validation result objects are not frozen")
    for schema in (subject_schema, aemh_schema):
        for name, fields in schema["objects"].items():
            item = outputs.get(name)
            if item is None:
                fail(f"missing output dataclass: {name}")
            observed = {field["name"]: {key: value for key, value in field.items() if key != "name"} for field in item["exact_serialized_fields"]}
            if observed != fields:
                fail(f"output schema drift: {name}")
            if item.get("extra_serialized_fields_forbidden") is not True:
                fail(f"extra serialized fields not forbidden: {name}")
    output_contract = api.get("output_object_contract", {})
    if output_contract.get("subject_exact_object_count") != 17 or output_contract.get("aemh_exact_object_count") != 13:
        fail("accepted 17/13 object counts changed")
    canonical_semantics = api.get("accepted_canonical_semantics", {})
    expected_semantic_hashes = {
        "subject_hash_recipes": canonical_sha(subject_schema["hash_recipes"]),
        "subject_invariants": canonical_sha(subject_schema["invariants"]),
        "aemh_hash_recipes": canonical_sha(aemh_schema["hash_recipes"]),
        "aemh_invariants": canonical_sha(aemh_schema["invariants"]),
        "semantic_hash_and_id_recipes": canonical_sha({
            "canonical_hash_recipes": semantic_schema["canonical_hash_recipes"],
            "canonical_id_recipes": semantic_schema["canonical_id_recipes"],
        }),
        "temporal_hash_contract": canonical_sha(temporal_schema["hash_contract"]),
    }
    for key, expected_hash in expected_semantic_hashes.items():
        if canonical_semantics.get(key, {}).get("definition_content_hash") != expected_hash:
            fail(f"accepted canonical semantics drift: {key}")
    serialized = canonical_bytes(api).decode("utf-8")
    forbidden_local_authority = [
        "IndependentExpectedJoinAuthorityRecord",
        "IndependentExpectedJoinAuthorityRegistry",
        "ControlledTemporalEndpointBinding",
        "AEMHDecisionAuthorityRecord",
    ]
    if any(token in serialized for token in forbidden_local_authority):
        fail("rejected local authority layer reintroduced")
    if api["construction_contract"] != {
        "execute_all_exact_authority_emitters": 119,
        "execute_all_exact_accepted_recipes": 18,
        "output_leaf_bijection": 272,
        "semantic_leaf_count": 4,
        "s4_identity_join_count": 8,
        "candidate_output_backfill_forbidden": True,
        "baseline_output_patch_forbidden": True,
        "hash_order": "authorities -> members/endpoints -> memberships -> inner hashes -> projections -> receipts -> packets",
    }:
        fail("construction contract mismatch")
    return api


def source_matrix_issues(candidate: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    temporal_registry = read_json(TEMPORAL_DIR / "recipe_registry.json")
    semantic_schema = read_json(SEMANTIC_DIR / "schema.json")
    coverage = temporal_registry["coverage_ledger"]
    rows = candidate.get("rows", [])
    if candidate.get("row_count") != 272 or len(rows) != 272:
        return ["V03_SCHEMA_CARDINALITY"]
    if [row.get("ordinal") for row in rows] != list(range(1, 273)):
        issues.append("V03_SCHEMA_ORDER")
    qualified = [row.get("qualified_leaf") for row in rows]
    expected_qualified = [f"{row['contract']}::{row['leaf']}" for row in coverage]
    if qualified != expected_qualified or len(set(qualified)) != 272:
        issues.append("V03_LEAF_BIJECTION")
    mapping_map = {
        row["qualified_leaf"]: row
        for row in temporal_registry["authority_output_registry"]["mappings"]
    }
    semantic_projection = semantic_schema["future_bundle_integration"]["leaf_projection"]
    for row, accepted in zip(rows, coverage):
        if row.get("contract") != accepted["contract"] or row.get("leaf") != accepted["leaf"]:
            issues.append("V03_LEAF_ROW_MISMATCH")
            continue
        resolver = row.get("resolver", {})
        if accepted["before_status"] == "C_accepted_semantic":
            if resolver.get("surface") != "accepted_semantic_delta" or resolver.get("source_path") != semantic_projection[accepted["leaf"]]:
                issues.append("V03_SEMANTIC_RESOLVER_MISMATCH")
        elif accepted["closure_kind"] == "authority_root":
            mapping = mapping_map[f"{accepted['contract']}::{accepted['leaf']}"]
            exact = {
                "surface": "accepted_parent_plus_temporal_delta",
                "operation": "execute accepted authority emitter",
                "mapping_id": mapping["mapping_id"],
                "mapping_content_hash": mapping["mapping_content_hash"],
                "authority_root": mapping["authority_root"],
                "emitter_op": mapping["op"],
                "minimal_dependency_fixture_refs": mapping["source_fixture_refs"],
                "minimal_dependency_field_paths": mapping["source_field_paths"],
                "dependency_refs": mapping["dependency_refs"],
            }
            if resolver != exact:
                issues.append("V03_AUTHORITY_MAPPING_MISMATCH")
        elif accepted["closure_kind"] == "recipe":
            if resolver.get("recipe_id") != accepted["closure_ref"] or resolver.get("operation") != "execute accepted recipe IR":
                issues.append("V03_RECIPE_RESOLVER_MISMATCH")
        elif resolver.get("operation") != "consume accepted parent leaf or parent deterministic recipe through temporal coverage ledger":
            issues.append("V03_PARENT_RESOLVER_MISMATCH")
        if row.get("unexplained") is not False or row.get("output_backfill_forbidden") is not True:
            issues.append("V03_FAIL_CLOSED_RULE_MISMATCH")
    pins = candidate.get("accepted_registry_pins", {})
    expected_pins = {
        "authority_output_registry_content_hash": temporal_registry["authority_output_registry_content_hash"],
        "recipe_registry_content_hash": temporal_registry["accepted_recipe_registry_reference"]["registry_content_hash"],
        "recipe_authority_binding_registry_content_hash": temporal_registry["recipe_authority_binding_registry_content_hash"],
    }
    if pins != expected_pins:
        issues.append("V03_REGISTRY_PIN_MISMATCH")
    return sorted(set(issues))


def verify_source_matrix() -> dict[str, Any]:
    joins = read_json(ARTIFACT_DIR / "source_join_matrix.json")
    issues = source_matrix_issues(joins)
    if issues:
        fail(f"source join matrix invalid: {issues}")
    coverage = joins.get("coverage", {})
    if coverage != {"subject": 156, "aemh": 116, "semantic": 4, "authority_emitters": 119, "accepted_recipes": 18, "unexplained": 0}:
        fail(f"source join counts mismatch: {coverage}")
    probes: list[dict[str, Any]] = []
    removed = copy.deepcopy(joins)
    removed["rows"].pop()
    probes.append(removed)
    added = copy.deepcopy(joins)
    added["rows"].append(copy.deepcopy(added["rows"][-1]))
    probes.append(added)
    changed_mapping = copy.deepcopy(joins)
    authority_row = next(row for row in changed_mapping["rows"] if "mapping_id" in row["resolver"])
    authority_row["resolver"]["mapping_id"] = "authority.mapping.forged"
    probes.append(changed_mapping)
    changed_op = copy.deepcopy(joins)
    authority_row = next(row for row in changed_op["rows"] if "emitter_op" in row["resolver"])
    authority_row["resolver"]["emitter_op"] = "project_contract"
    probes.append(changed_op)
    changed_dependency = copy.deepcopy(joins)
    authority_row = next(row for row in changed_dependency["rows"] if "minimal_dependency_field_paths" in row["resolver"])
    authority_row["resolver"]["minimal_dependency_field_paths"] = authority_row["resolver"]["minimal_dependency_field_paths"][1:]
    probes.append(changed_dependency)
    changed_registry = copy.deepcopy(joins)
    changed_registry["accepted_registry_pins"]["authority_output_registry_content_hash"] = "0" * 64
    probes.append(changed_registry)
    changed_semantic = copy.deepcopy(joins)
    semantic_row = next(row for row in changed_semantic["rows"] if row["before_status"] == "C_accepted_semantic")
    semantic_row["resolver"]["surface"] = "accepted_parent_plus_temporal_delta"
    probes.append(changed_semantic)
    for index, probe in enumerate(probes, 1):
        if not source_matrix_issues(probe):
            fail(f"active source-matrix mutation was accepted: {index}")
    return joins


def verify_error_matrix() -> None:
    errors = read_json(ARTIFACT_DIR / "invariant_error_matrix.json")
    subject = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    semantic = read_json(SEMANTIC_DIR / "schema.json")
    temporal = read_json(TEMPORAL_DIR / "challenge_registry.json")
    parent_codes = list(dict.fromkeys(subject["error_codes"] + aemh["error_codes"]))
    semantic_codes = semantic["typed_error_priority"]
    temporal_codes = sorted({row["expected_error"] for row in temporal["cases"]})
    total = parent_codes + semantic_codes + temporal_codes
    if errors.get("accepted_parent_error_codes") != parent_codes:
        fail("parent error union drift")
    if errors.get("accepted_semantic_delta_error_codes") != semantic_codes:
        fail("semantic error union drift")
    if errors.get("accepted_temporal_delta_error_codes") != temporal_codes:
        fail("temporal error union drift")
    observed = errors.get("deterministic_priority", [])
    if [row.get("code") for row in observed] != total or [row.get("priority") for row in observed] != list(range(1, len(total) + 1)):
        fail("error priority is not total/deterministic")
    if errors.get("error_union_count") != len(total):
        fail("error union count mismatch")


def execute_temporal_semantics() -> tuple[int, int]:
    module = load_module(
        ROOT / "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1.py",
        "accepted_temporal_delta_verifier_for_v03",
    )
    manifest = read_json(TEMPORAL_DIR / "manifest.json")
    challenges = read_json(TEMPORAL_DIR / "challenge_registry.json")
    schema = read_json(TEMPORAL_DIR / "schema.json")
    authority_fixture_map = {item["fixture_id"]: item for item in challenges["authority_fixtures"]}
    mapping_fixture_map = {item["mapping_id"]: item for item in challenges["authority_mapping_positive_fixtures"]}
    executed_mappings = 0
    for mapping in manifest["accepted_authority_output_registry"]["mappings"]:
        fixture = mapping_fixture_map.get(mapping["mapping_id"])
        if fixture is None:
            fail(f"missing accepted authority fixture: {mapping['mapping_id']}")
        selected = [authority_fixture_map[ref] for ref in mapping["source_fixture_refs"]]
        executor = module.LazyAuthorityProjectionExecutor(selected)
        contract, leaf = mapping["qualified_leaf"].split("::", 1)
        owner, field = leaf.split(".", 1)
        params = mapping[f"{mapping['op']}_params"]
        try:
            output, trace = executor.execute(contract, owner, field, mapping["op"], params)
        except RuntimeError as exc:
            fail(f"accepted emitter failed: {mapping['mapping_id']}: {exc}")
        expected = json.loads(fixture["expected_target_canonical_json"])
        if canonical_bytes(output) != canonical_bytes(expected):
            fail(f"accepted emitter target mismatch: {mapping['mapping_id']}")
        if trace["consumed_fixture_refs"] != mapping["source_fixture_refs"]:
            fail(f"accepted emitter fixture slice mismatch: {mapping['mapping_id']}")
        if trace["consumed_field_paths"] != mapping["source_field_paths"]:
            fail(f"accepted emitter field slice mismatch: {mapping['mapping_id']}")
        executed_mappings += 1
    recipes = {row["recipe_id"]: row for row in manifest["accepted_recipe_registry"]["recipes"]}
    fixtures = {row["recipe_id"]: row for row in challenges["positive_fixtures"]}
    candidates = {row["candidate_ref"]: row for row in challenges["external_candidate_fixtures"]}
    bindings = {
        row["recipe_id"]: row
        for row in manifest["accepted_recipe_authority_binding_registry"]["bindings"]
    }
    executed_recipes = 0
    for recipe_id, recipe in recipes.items():
        fixture = fixtures.get(recipe_id)
        if fixture is None:
            fail(f"missing accepted recipe fixture: {recipe_id}")
        error, outputs = module.execute_recipe(
            recipe,
            fixture,
            candidates,
            manifest["external_acceptance_registry_root"],
            schema,
            authority_fixture_map,
            bindings[recipe_id],
        )
        if error is not None or not outputs:
            fail(f"accepted recipe execution failed: {recipe_id}: {error}")
        executed_recipes += 1
    if executed_mappings != 119 or executed_recipes != 18:
        fail(f"accepted execution counts mismatch: {executed_mappings}/{executed_recipes}")
    required_attacks = {
        "TPA_ACCEPTED_RECORD_MISMATCH",
        "TPA_AUTHORITY_FIXTURE_REF_IDENTITY_MISMATCH",
        "TPA_AUTHORITY_OP_PARAMS_MISMATCH",
        "TPA_AUTHORITY_UNUSED_DECLARED_DEPENDENCY",
        "TPA_JOIN_CROSS_SCOPE",
        "TPA_VISIBILITY_COUNT_MISMATCH",
        "TPA_PENDING_ADD_DROP",
        "TPA_AEMH_PREFIX_REWRITE",
        "TPA_AEMH_CANDIDATE_FACT_SWAP",
        "TPA_AEMH_EVIDENCE_JOINT_MISMATCH",
        "TPA_RECIPE_AUTHORITY_BINDING_MISMATCH",
        "TPA_PROTECTED_PIN_DRIFT",
    }
    observed_attacks = {row["expected_error"] for row in challenges["cases"]}
    if not required_attacks.issubset(observed_attacks):
        fail("accepted temporal active attack coverage incomplete")
    return executed_mappings, executed_recipes


def json_pointer_parts(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        fail(f"invalid JSON pointer: {pointer}")
    return [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]


def apply_mutation(document: dict[str, Any], mutation: dict[str, Any]) -> None:
    parts = json_pointer_parts(mutation["path"])
    current: Any = document
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    key = parts[-1]
    if mutation["op"] == "replace":
        if isinstance(current, list):
            current[int(key)] = copy.deepcopy(mutation["value"])
        else:
            current[key] = copy.deepcopy(mutation["value"])
    elif mutation["op"] == "remove":
        if isinstance(current, list):
            current.pop(int(key))
        else:
            current.pop(key)
    elif mutation["op"] == "append":
        current.append(copy.deepcopy(mutation["value"]))
    elif mutation["op"] == "reverse":
        target = current[int(key)] if isinstance(current, list) else current[key]
        if not isinstance(target, list):
            fail(f"reverse target is not a list: {mutation['path']}")
        target.reverse()
    else:
        fail(f"unsupported governance mutation: {mutation['op']}")


def verify_governance_probes(tests: dict[str, Any]) -> int:
    parent = load_module(
        ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py",
        "accepted_parent_verifier_for_v03",
    )
    parent_exact = read_json(ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    probes = tests.get("artifact_governance_probes", [])
    if len(probes) != 22:
        fail("governance probe count mismatch")
    executed = 0
    for probe in probes:
        base = probe["base_input_key"]
        if base == "exact_overlay_artifact":
            candidate = read_json(PARENT_DIR / "exact_overlay.json")
            apply_mutation(candidate, probe["mutation"])
            issues = parent.overlay_validation_issues(candidate, parent_exact)
        elif base == "source_matrix_artifact":
            candidate = read_json(PARENT_DIR / "source_matrix.json")
            apply_mutation(candidate, probe["mutation"])
            issues = parent.source_matrix_validation_issues(candidate)
        elif base == "manifest_artifact":
            candidate = read_json(PARENT_DIR / "manifest.json")
            apply_mutation(candidate, probe["mutation"])
            candidate["manifest_content_hash"] = parent.canonical_hash(
                {key: value for key, value in candidate.items() if key != "manifest_content_hash"}
            )
            issues = parent.manifest_contract_validation_issues(candidate)
        else:
            fail(f"unknown governance base: {base}")
        if probe["expected_exact_error"] not in issues:
            fail(f"governance probe did not reject: {probe['case_id']}: {issues}")
        executed += 1
    return executed


def verify_test_matrix(joins: dict[str, Any]) -> tuple[int, int, int]:
    tests = read_json(ARTIFACT_DIR / "test_matrix.json")
    counts = tests.get("counts", {})
    expected_counts = {
        "accepted_case_trace_total": 236,
        "future_executable_spec_total": 231,
        "alias_group_count": 5,
        "alias_trace_delta": 5,
        "artifact_governance_probe_total": 22,
        "positive_spec_total": 10,
    }
    if counts != expected_counts:
        fail(f"test count mismatch: {counts}")
    aliases = {
        row["canonical_case_id"]: row["alias_case_ids"]
        for row in tests.get("aliases", [])
    }
    if aliases != ALIASES:
        fail("five alias groups mismatch")
    parent_registry = read_json(PARENT_DIR / "challenge_registry.json")
    accepted_rows = parent_registry["inherited_cases"] + parent_registry["public_authority_specific_cases"]
    governance_ids = {
        row["case_id"] for row in accepted_rows if str(row.get("base_input_key", "")).endswith("_artifact")
    }
    expected_trace_ids = {row["case_id"] for row in accepted_rows} - governance_ids
    specs = tests.get("future_runtime_specs", [])
    observed_trace_ids = {
        case_id for spec in specs for case_id in spec.get("covered_trace_case_ids", [])
    }
    if observed_trace_ids != expected_trace_ids or len(observed_trace_ids) != 236:
        fail("accepted trace coverage mismatch")
    plans = tests.get("contract_construction_plans", {})
    if plans.get(SUBJECT, {}).get("exact_leaf_count") != 156 or plans.get(AEMH, {}).get("exact_leaf_count") != 116:
        fail("contract construction plan leaf counts mismatch")
    identities: list[str] = []
    for spec in specs:
        packet = spec["typed_fixture_reference_packet"]
        plan = plans[spec["contract"]]
        identity_payload = {
            "contract": spec["contract"],
            "lane": spec["harness_lane"],
            "typed_candidate_fixture_content_hash": packet["candidate_fixture_content_hash"],
            "exact_mutation": spec["one_exact_mutation"],
            "selected_authority_resolver": packet["selected_authority_resolver"],
            "linked_operations": spec["linked_source_operations"],
            "canonical_reseal_targets": spec["canonical_reseal_targets"],
            "construction_plan_hash": digest(plan),
        }
        identity = digest(identity_payload)
        if identity != spec.get("future_spec_input_identity") or identity != spec.get("input_identity_payload_sha256"):
            fail(f"future input identity mismatch: {spec.get('spec_id')}")
        if spec.get("spec_id") != f"future-spec::{identity[:20]}":
            fail("spec id not content addressed")
        if spec.get("producer_executed") is not False or spec.get("contract_spec_only") is not True:
            fail("contract claims producer execution")
        if not spec.get("future_pytest_node") or not spec.get("forbidden_audience_output"):
            fail("future spec lacks exact node or forbidden output")
        oracle = spec.get("non_llm_oracle", {})
        if oracle.get("execute_temporal_emitters_and_recipes") is not True or oracle.get("recompute_all_dependent_ids_hashes_containers_receipts_packets") is not True:
            fail("future spec lacks executable non-LLM oracle")
        identities.append(identity)
    if len(specs) != 231 or len(set(identities)) != 231:
        fail("future spec identity distinctness mismatch")
    positives = [spec for spec in specs if spec["expected_typed_result_or_error"]["disposition"] == "accept"]
    if len(positives) != 10:
        fail("positive future spec count mismatch")
    for spec in positives:
        plan = plans[spec["contract"]]
        if plan.get("complete_packet_required") is not True or plan.get("baseline_output_patch_forbidden") is not True:
            fail("positive spec does not require complete source-built packet")
        if spec["covered_trace_case_ids"] == ["R5C-109"] and len(spec["linked_source_operations"]) != 5:
            fail("R5C-109 exact five linked operations missing")
    governance = verify_governance_probes(tests)
    return len(specs), len(observed_trace_ids), governance


def verify_locked_surfaces(manifest: dict[str, Any]) -> None:
    allowlist = manifest.get("producer_create_only_allowlist", [])
    if len(allowlist) != 11 or len(set(allowlist)) != 11:
        fail("producer allowlist is not exact 11")
    for relative in allowlist + manifest.get("s5_runtime_locked_paths", []):
        path = ROOT / relative
        if path.exists() or path.is_symlink():
            fail(f"locked future surface exists: {relative}")
    scan_roots = [
        ROOT / "poc/medical_monitoring_ai_native_r5/src/mm_r5",
        ROOT / "poc/medical_monitoring_ai_native_r5/tests",
    ]
    forbidden_stems = {
        "public_authority_common",
        "subject_temporal_public",
        "aemh_match_history_public",
        "public_authority_runtime_fixtures",
    }
    for root in scan_roots:
        for path in root.rglob("*"):
            name = path.name
            if any(stem in name for stem in forbidden_stems) and (name.endswith(".pyc") or name == "__pycache__"):
                fail(f"producer bytecode/cache exists: {path.relative_to(ROOT)}")
    root_init = ROOT / "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py"
    if raw_sha(root_init) != "0a24c6993cb4997b1e77cefcfeeff490aaf882b269ab0fece8635ce81b6b4ebd":
        fail("root init drift")


def verify_port_8911_stopped() -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        probe.bind(("127.0.0.1", 8911))
    except OSError as exc:
        fail(f"port 8911 is not available/stopped: {exc}")
    finally:
        probe.close()


def verify_generator_check() -> None:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, *optimization_args(), "-B", str(GENERATOR_PATH), "--check"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if completed.returncode != 0:
        fail(f"generator --check failed: {(completed.stdout + completed.stderr)[-3000:]}")


def main() -> int:
    verify_no_assert_statements()
    manifest = verify_manifest()
    verify_surface_pins(manifest)
    verify_medical_writing_inventory(manifest)
    run_pinned_verifier("tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py")
    run_pinned_verifier("tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py")
    run_pinned_verifier("tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1.py")
    verify_public_api()
    joins = verify_source_matrix()
    verify_error_matrix()
    mappings, recipes = execute_temporal_semantics()
    specs, traces, governance = verify_test_matrix(joins)
    verify_locked_surfaces(manifest)
    verify_port_8911_stopped()
    verify_generator_check()
    print(
        "PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_V0_3_VERIFY_OK "
        f"optimize={sys.flags.optimize} leaves=272 emitters={mappings} recipes={recipes} "
        f"specs={specs} traces={traces} aliases=5 governance={governance} port_8911=stopped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
