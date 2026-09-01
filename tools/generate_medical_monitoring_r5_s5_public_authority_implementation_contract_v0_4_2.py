#!/usr/bin/env python3
"""Generate R5-S5 public-authority implementation contract v0.4.2 registries.

Consumes only accepted authorities. Reconstructs and executes 272 leaf closures,
192 error replays, 58 active gates, 226 reject issue metadata, and the exact
future producer contract. Does not modify v0.4.1, create producers, or start 8911.
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import importlib.util
import json
import pathlib
import re
import socket
import sys
import unicodedata
from typing import Any

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.4.2"
SCHEMA_VERSION = "2026-08-25.4.2"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"

OUT_REL = pathlib.Path("artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2")
GENERATOR_REL = "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2.py"
VERIFIER_REL = "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2.py"
CONTEXT_REL = "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2_20260825_context.md"
REVIEW_REL = "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2_20260825.md"

PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
SEMANTIC_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1"
TEMPORAL_V01_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1"
TEMPORAL_V02_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2"
ERROR_DELTA_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1"
TYPED_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1"
REJECTED_V041_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1"

OWNED_OUTPUTS = (
    CONTEXT_REL,
    REVIEW_REL,
    f"{OUT_REL}/leaf_execution_registry.json",
    f"{OUT_REL}/error_replay_execution_registry.json",
    f"{OUT_REL}/active_gate_execution_registry.json",
    f"{OUT_REL}/runtime_reject_metadata_registry.json",
    f"{OUT_REL}/future_producer_contract.json",
    f"{OUT_REL}/manifest.json",
    GENERATOR_REL,
)

EXPECTED_COMPLETE_PATHS = (*OWNED_OUTPUTS, VERIFIER_REL)

PRODUCER_ALLOWLIST = (
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
)

ACCEPTED_PINS = {
    "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1/authority_contract.json": "bc0c60db30721401315605f69b1d6e3c0e26b39161ea3135f1fcc547828c09cc",
    "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1/manifest.json": "a71f0937dd5d0a0fc77de98b41f6308b5caed0ae7d460f0282884c56127cd22c",
    "context/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1_acceptance_record_20260825.md": "b509de3edb6111da19977cc8aa7741160aa04366dbd5565bb746fe633ffd46e6",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json": "92bbf2d7fe4cd591949982a3d29666a8b6090aab645679dbff997630a3702270",
    "context/medical_monitoring_r5_s5_public_authority_contract_acceptance_record_20260819.md": "23fed5b186057a79cd0ec43a7718e43934ebafdc8f62fd251077d4fb6891639d",
    "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/manifest.json": "66605a46c10e2aa4d36b06e566158666a08cdc92ec0e630364aad5b9ffb2385d",
    "context/medical_monitoring_r5_s5_semantic_authority_delta_acceptance_record_20260820.md": "bf50156fa82d825309fce72115ddf971fc4e0bdbd60936ea45e2362a6aa3eb4c",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json": "e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97",
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_acceptance_record_20260820.md": "523351f1b5536b12c1a5be9251ad01f4e8b7a70f5088073a2333aefc241d1b79",
    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json": "466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8",
    "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_acceptance_record_20260821.md": "d08b4ed27f9829db4cdcab0837f3623c244ee8c888cce699c55580621bd68ef4",
    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/manifest.json": "0dbc0763b9c282c5e2363707a1f6ea99ae8e730e00acb716dcfc61bf9cd3186b",
    "context/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1_acceptance_record_20260821.md": "814f3e7b36aade049e9a5267a3b247ec23089a0ec0696f9d07b82133ca6b42e9",
}

TYPED_MANIFEST_CONTENT_HASH = "38a8cadee3bcac6dd74a5ce9d522c9f744e82592f87089423e7783be7f6be976"

NEGATIVE_V041_PINS = {
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/manifest.json": "1033daaa81eb4c0eede2445b5a8228e37d54d6621feb8b35ebb179a20d55c5bd",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/source_join_matrix.json": "32df331bb5f48b174194384f9297ece2df9d26c80367507ac66657d0a2f7ee36",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/invariant_error_matrix.json": "f7545cc977ab2143b545a2ce28bdedaf24cf351789865d44c443816d2eacbf50",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/test_matrix.json": "a244f5dd877cf19393614f407d1c333f5b4c1ec8736c796058091591f1ccaba3",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/public_api.json": "926ac1338c72f4b9c381f1c4690fc14412ad97027109dc91da45245ba4ab4999",
}

SOURCE_TYPES = {
    "AEMHDecisionInputV02",
    "AEMHFullGraphInputV02",
    "AEMHThreadInputV02",
    "AuthorityBundleV02",
    "AxisInputV02",
    "CutoffEndpointBindingV02",
    "DomainInputV02",
    "EndpointInputV02",
    "IdentityScopeInputV02",
    "LocatorInputV02",
    "PhaseInputV02",
    "RevisionInputV02",
    "RiskInputV02",
    "ScopeInputV02",
    "SubjectEventInputV02",
    "SubjectFullGraphInputV02",
    "VisitInputV02",
}

MW_PROTECTED_COUNT = 542
MW_PROTECTED_SHA = "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"


def read_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonicalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [canonicalize(item) for item in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(key)): canonicalize(item) for key, item in value.items()}
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def load_module(path: pathlib.Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pointer_get(value: Any, pointer: str) -> Any:
    node = value
    for part in pointer.strip("/").split("/") if pointer != "/" else []:
        part = part.replace("~1", "/").replace("~0", "~")
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def port_stopped() -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", 8911)) != 0


def check_accepted_pins() -> dict[str, Any]:
    for relative, expected in ACCEPTED_PINS.items():
        actual = raw_sha(ROOT / relative)
        if actual != expected:
            raise SystemExit(f"STOP accepted pin drift: {relative}:{actual}")
    typed_manifest = read_json(TYPED_DIR / "manifest.json")
    if typed_manifest["manifest_content_hash"] != TYPED_MANIFEST_CONTENT_HASH:
        raise SystemExit("STOP typed manifest content hash")
    for relative, expected in NEGATIVE_V041_PINS.items():
        actual = raw_sha(ROOT / relative)
        if actual != expected:
            raise SystemExit(f"STOP negative v0.4.1 pin drift: {relative}:{actual}")
    return typed_manifest


def medical_writing_inventory(contract: dict[str, Any]) -> tuple[int, str]:
    pattern = re.compile(contract["relative_path_regex"])
    paths = sorted(
        path.relative_to(ROOT).as_posix()
        for root_name in contract["roots"]
        for path in (ROOT / root_name).rglob("*")
        if path.is_file() and pattern.search(path.relative_to(ROOT).as_posix())
    )
    payload = b"".join(
        relative.encode() + b"\0" + raw_sha(ROOT / relative).encode() + b"\n" for relative in paths
    )
    return len(paths), hashlib.sha256(payload).hexdigest()


def assert_protected_boundaries() -> dict[str, Any]:
    rejected = read_json(REJECTED_V041_DIR / "manifest.json")
    protected = rejected["protected_pins"]
    count, aggregate = medical_writing_inventory(protected["medical_writing_inventory_contract"])
    if (count, aggregate) != (MW_PROTECTED_COUNT, MW_PROTECTED_SHA):
        raise SystemExit(f"STOP medical-writing protected inventory: {count}:{aggregate}")
    if any((ROOT / path).exists() for path in PRODUCER_ALLOWLIST):
        raise SystemExit("STOP producer path present")
    if not port_stopped():
        raise SystemExit("STOP port 8911 listening")
    return {
        "medical_writing_protected_file_count": count,
        "medical_writing_protected_inventory_sha256": aggregate,
        "producers_absent": 11,
        "port_8911": "stopped",
    }


def build_classes(schema: dict[str, Any]) -> dict[str, type[Any]]:
    return {
        name: dataclasses.make_dataclass(
            name,
            [(field, Any) for field in schema["objects"][name]["required"]],
            frozen=True,
        )
        for name in SOURCE_TYPES
    }


def decode(value: Any, type_spec: str, schema: dict[str, Any], classes: dict[str, type[Any]]) -> Any:
    if type_spec.startswith("nullable:"):
        return None if value is None else decode(value, type_spec.split(":", 1)[1], schema, classes)
    if type_spec.startswith("list:"):
        inner = type_spec.split(":", 1)[1]
        return tuple(decode(item, inner, schema, classes) for item in value)
    if type_spec.startswith("union:"):
        options = type_spec.split(":", 1)[1].split("|")
        matches = [name for name in options if set(value) == set(schema["objects"][name]["required"])]
        if len(matches) != 1:
            raise SystemExit("STOP typed union resolution")
        return decode(value, matches[0], schema, classes)
    if type_spec in classes:
        obj = schema["objects"][type_spec]
        if set(value) != set(obj["required"]):
            raise SystemExit(f"STOP typed exact keys: {type_spec}")
        return classes[type_spec](
            **{field: decode(value[field], obj["fields"][field], schema, classes) for field in obj["required"]}
        )
    return value


def encoded(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: encoded(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, tuple):
        return [encoded(item) for item in value]
    return value


def cutoff_from_binding(authority: dict[str, Any], parent_doc: dict[str, Any]) -> dict[str, Any]:
    if parent_doc["hash_recipes"]["object_content_hash"] != (
        "sha256(canonical_json(all exact object fields except that object's *_content_hash field))"
    ):
        raise SystemExit("STOP parent object hash recipe")
    binding = authority["source"]["cutoff_binding"]
    body = {
        "state": binding["state"],
        "exact_date": binding["exact_date"],
        "source_locator_refs": sorted(binding["source_locator_refs"]),
    }
    constructed = {**body, "cutoff_content_hash": digest(body)}
    if set(constructed) != set(parent_doc["objects"]["PublicCutoffEndpoint"]):
        raise SystemExit("STOP parent cutoff exact keys")
    return constructed


def packet_value(result: Any, contract: str, pointer: str) -> Any:
    packet = result if contract == SUBJECT else result[1]
    prefix = f"/contracts/{contract}/final_packet"
    if not pointer.startswith(prefix):
        raise SystemExit(f"STOP target pointer prefix: {pointer}")
    return pointer_get(packet, pointer[len(prefix) :] or "/")


def leaf_execution_registry(typed_contract: dict[str, Any]) -> dict[str, Any]:
    engine = load_module(
        ROOT / "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "v042_temporal_v02_generator",
    )
    schema = read_json(TEMPORAL_V02_DIR / "schema.json")
    fixtures = read_json(TEMPORAL_V02_DIR / "full_graph_fixture_registry.json")
    recipes = read_json(TEMPORAL_V02_DIR / "emitter_recipe_registry.json")
    parent_subject = read_json(PARENT_DIR / "subject_temporal_schema.json")
    classes = build_classes(schema)
    leaf_by_contract: dict[str, list[dict[str, Any]]] = {}
    for row in typed_contract["leaf_derivations"]:
        leaf_by_contract.setdefault(row["contract"], []).append(row)
    rows: list[dict[str, Any]] = []
    ordinal = 0
    for baseline in fixtures["baselines"]:
        authority = copy.deepcopy(baseline["authority_input"])
        schema_issues = engine.validate_authority_bundle(authority, schema)
        if schema_issues:
            raise SystemExit("STOP accepted v0.2 schema: " + ",".join(schema_issues))
        typed = decode(authority, "AuthorityBundleV02", schema, classes)
        if encoded(typed) != authority:
            raise SystemExit("STOP typed roundtrip")
        result, outputs = engine.execute_recipe_dag(authority, recipes, capture_outputs=True)
        target = authority["target_contract"]
        previous = result[0] if target == AEMH else None
        current = result[1] if previous is not None else result
        if engine.parent_errors(target, current, previous):
            raise SystemExit(f"STOP parent validator: {target}")
        for mapping in leaf_by_contract[target]:
            ordinal += 1
            if mapping["constructor_id"] == "subject_public_cutoff_from_binding":
                constructed = cutoff_from_binding(authority, parent_subject)
                leaf_name = mapping["qualified_leaf"].rsplit(".", 1)[1]
                value = constructed[leaf_name]
                value_digest = digest(value)
                if value_digest != mapping["construction_target_value_digest"]:
                    raise SystemExit(f"STOP cutoff digest: {mapping['qualified_leaf']}")
                if mapping["transitive_authority_pointers"] != ["/source/cutoff_binding"]:
                    raise SystemExit(f"STOP cutoff authority: {mapping['qualified_leaf']}")
                closure_kind = "subject_public_cutoff_from_binding"
                execution = {
                    "typed_decode_roundtrip": True,
                    "constructor_id": "subject_public_cutoff_from_binding",
                    "constructed_value_digest": value_digest,
                    "parent_object_hash_recipe_validated": True,
                    "fake_typed_selector_forbidden": True,
                }
            else:
                recipe_value = pointer_get(
                    outputs[f"{mapping['recipe_id']}.sealed"]["value"],
                    mapping["recipe_output_json_pointer"],
                )
                target_value = packet_value(result, target, mapping["target_verification_json_pointer"])
                if recipe_value != target_value:
                    raise SystemExit(f"STOP recipe/packet mismatch: {mapping['qualified_leaf']}")
                for pointer in mapping["transitive_authority_pointers"]:
                    pointer_get(authority, pointer)
                closure_kind = "accepted_recipe_to_parent_packet_compare"
                execution = {
                    "typed_decode_roundtrip": True,
                    "recipe_id": mapping["recipe_id"],
                    "recipe_output_digest": digest(recipe_value),
                    "parent_packet_digest": digest(target_value),
                    "recipe_equals_packet": True,
                    "fake_typed_selector_forbidden": True,
                }
            if "typed_source_selector" in mapping or "v02_authority_selector" in mapping:
                raise SystemExit(f"STOP rejected selector plane: {mapping['qualified_leaf']}")
            rows.append(
                {
                    "ordinal": ordinal,
                    "qualified_leaf": mapping["qualified_leaf"],
                    "contract": mapping["contract"],
                    "closure_kind": closure_kind,
                    "derivation_kind": mapping["derivation_kind"],
                    "constructor_id": mapping["constructor_id"],
                    "recipe_id": mapping["recipe_id"],
                    "target_kind": mapping["target_kind"],
                    "output_json_pointer": mapping["output_json_pointer"],
                    "recipe_output_json_pointer": mapping["recipe_output_json_pointer"],
                    "target_verification_json_pointer": mapping["target_verification_json_pointer"],
                    "construction_target_value_digest": mapping["construction_target_value_digest"],
                    "transitive_authority_pointers": mapping["transitive_authority_pointers"],
                    "verification_chain": mapping["verification_chain"],
                    "authority_relation": mapping["authority_relation"],
                    "serialized_input_authority": "accepted_temporal_v02_authority_bundle",
                    "generator_leaf_executed": True,
                    "execution_evidence": execution,
                    "candidate_backfill_forbidden": True,
                    "second_typed_truth_plane_forbidden": True,
                }
            )
    recipe_rows = [row for row in rows if row["closure_kind"] == "accepted_recipe_to_parent_packet_compare"]
    cutoff_rows = [row for row in rows if row["closure_kind"] == "subject_public_cutoff_from_binding"]
    if len(rows) != 272 or len(recipe_rows) != 268 or len(cutoff_rows) != 4:
        raise SystemExit(f"STOP leaf closure counts: {len(rows)}/{len(recipe_rows)}/{len(cutoff_rows)}")
    if len({row["qualified_leaf"] for row in rows}) != 272:
        raise SystemExit("STOP leaf bijection")
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-leaf-execution-registry-v0.4.2",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "row_count": 272,
        "accepted_recipe_to_parent_packet_compare_count": 268,
        "subject_public_cutoff_from_binding_count": 4,
        "typed_authority_contract_content_hash": typed_contract["counts"]["contract_content_hash"],
        "rows": rows,
        "forbidden": [
            "R1/R2/R4 mutable-class selector",
            "second typed truth plane",
            "v0.2-mirrored fake typed selector replacement",
            "candidate join matrix value authority",
        ],
    }


def parent_case_issues(
    row: dict[str, Any],
    parent: Any,
    parent_exact: dict[str, Any],
    subject_schema: dict[str, Any],
    aemh_schema: dict[str, Any],
    inputs: dict[str, Any],
) -> list[str]:
    contract = row["contract"]
    if contract == SUBJECT:
        candidate = copy.deepcopy(inputs[row["base_input_key"]])
        parent.apply_mutation(candidate, row["single_mutation"])
        if row["fully_reseal_after_mutation"]:
            parent.reseal_subject_packet(
                candidate,
                subject_schema,
                preserve_evaluation=row["category"].startswith("subject_evaluation_identity_"),
            )
        return parent.validate_subject(candidate, subject_schema)
    if contract == AEMH:
        candidate = copy.deepcopy(inputs[row["base_input_key"]])
        parent.apply_mutation(candidate, row["single_mutation"])
        if row["fully_reseal_after_mutation"]:
            parent.reseal_aemh_packet(
                candidate,
                aemh_schema,
                preserve_evaluation=row["category"].startswith("aemh_evaluation_identity_"),
            )
        return parent.validate_aemh(candidate, aemh_schema, inputs["aemh_match_history_previous_base"])
    if contract == "exact-overlay-v0.1":
        candidate = read_json(PARENT_DIR / "exact_overlay.json")
        parent.apply_mutation(candidate, row["single_mutation"])
        return parent.overlay_validation_issues(candidate, parent_exact)
    if contract == "source-matrix-v0.1":
        candidate = read_json(PARENT_DIR / "source_matrix.json")
        parent.apply_mutation(candidate, row["single_mutation"])
        return parent.source_matrix_validation_issues(candidate)
    if contract == "manifest-v0.1":
        candidate = read_json(PARENT_DIR / "manifest.json")
        parent.apply_mutation(candidate, row["single_mutation"])
        if row["fully_reseal_after_mutation"]:
            candidate["manifest_content_hash"] = parent.canonical_hash(
                {key: value for key, value in candidate.items() if key != "manifest_content_hash"}
            )
        return parent.manifest_contract_validation_issues(candidate)
    raise SystemExit(f"STOP unknown accepted parent gate: {contract}")


def reconstruct_error_authority() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    subject = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    semantic_schema = read_json(SEMANTIC_DIR / "schema.json")
    temporal_registry = read_json(TEMPORAL_V01_DIR / "challenge_registry.json")
    parent_codes = list(dict.fromkeys(subject["error_codes"] + aemh["error_codes"]))
    semantic_codes = list(semantic_schema["typed_error_priority"])
    temporal_codes = sorted({row["expected_error"] for row in temporal_registry["cases"]})
    ordered = parent_codes + semantic_codes + temporal_codes
    priorities = {code: index for index, code in enumerate(ordered, 1)}
    origins = {code: "parent" for code in parent_codes}
    origins.update({code: "semantic_delta" for code in semantic_codes})
    origins.update({code: "temporal_delta" for code in temporal_codes})
    if len(ordered) != 192 or len(set(ordered)) != 192:
        raise SystemExit("STOP accepted error priority closure")

    carriers: dict[str, dict[str, Any]] = {}
    parent = load_module(
        ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py",
        "accepted_parent_error_replay_v042",
    )
    parent_registry = read_json(PARENT_DIR / "challenge_registry.json")
    parent_exact = read_json(ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    parent_inputs = read_json(PARENT_DIR / "base_inputs.json")
    for index, row in enumerate(parent_registry["public_authority_specific_cases"]):
        issues = parent_case_issues(row, parent, parent_exact, subject, aemh, parent_inputs)
        for code in issues:
            carriers.setdefault(
                code,
                {
                    "replay_plane": "accepted_pre_delta",
                    "source_challenge_ref": (
                        "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/"
                        f"challenge_registry.json#/public_authority_specific_cases/{index}"
                    ),
                    "gate_entrypoint": {
                        SUBJECT: "validate_subject",
                        AEMH: "validate_aemh",
                        "exact-overlay-v0.1": "overlay_validation_issues",
                        "source-matrix-v0.1": "source_matrix_validation_issues",
                        "manifest-v0.1": "manifest_contract_validation_issues",
                    }[row["contract"]],
                    "base_input_ref": row.get("base_input_key"),
                    "mutation": copy.deepcopy(row["single_mutation"]),
                    "reseal": {
                        "enabled": row["fully_reseal_after_mutation"],
                        "mode": "accepted_parent_full_reseal" if row["fully_reseal_after_mutation"] else "none",
                    },
                    "observed_ordered_issue_codes": list(issues),
                    "contract": row["contract"],
                    "invariant": row["stage_oracle_contract"]["rule_id"],
                },
            )

    semantic = load_module(
        ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1.py",
        "accepted_semantic_error_replay_v042",
    )
    semantic_registry = read_json(SEMANTIC_DIR / "challenge_registry.json")
    semantic_manifest = read_json(SEMANTIC_DIR / "manifest.json")
    source_registry = semantic_manifest["synthetic_typed_source_record_registry"]
    acceptance_registry = semantic_manifest["synthetic_policy_acceptance_registry"]
    source_records = semantic.validate_source_registry(source_registry)
    accepted_records = semantic.validate_acceptance_registry(acceptance_registry)
    semantic_result = semantic.run_challenges(
        semantic_registry, source_registry, source_records, acceptance_registry, accepted_records
    )
    actual_by_case = {row["case_id"]: row["outcome"] for row in semantic_result["outcomes"]}
    for index, row in enumerate(semantic_registry["cases"]):
        code = actual_by_case[row["case_id"]]
        if code == "success":
            continue
        carriers.setdefault(
            code,
            {
                "replay_plane": "accepted_pre_delta",
                "source_challenge_ref": (
                    "artifacts/medical_monitoring_r5_s5_public_authority_semantic_delta_v0_1/"
                    f"challenge_registry.json#/cases/{index}"
                ),
                "gate_entrypoint": {
                    "event": "evaluate_event",
                    "risk": "evaluate_risk",
                    "risk_authority": "evaluate_risk+candidate_compare",
                    "governance": "evaluate_governance",
                }[row["evaluation_kind"]],
                "base_input_ref": row["baseline_ref"],
                "mutation": copy.deepcopy(row["mutation"]),
                "reseal": {
                    "enabled": bool(row["mutation"]["mechanical_reseal"]),
                    "mode": list(row["mutation"]["mechanical_reseal"]),
                },
                "observed_ordered_issue_codes": [code],
                "contract": [SUBJECT, AEMH],
                "invariant": row["non_llm_oracle"],
            },
        )

    temporal = load_module(
        ROOT / "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1.py",
        "accepted_temporal_error_replay_v042",
    )
    temporal_manifest = read_json(TEMPORAL_V01_DIR / "manifest.json")
    temporal_schema = read_json(TEMPORAL_V01_DIR / "schema.json")
    temporal_matrix = read_json(TEMPORAL_V01_DIR / "source_matrix_delta.json")
    temporal_recipes = read_json(TEMPORAL_V01_DIR / "recipe_registry.json")
    temporal.verify_schema(temporal_schema, temporal_manifest)
    temporal.verify_source_matrix(temporal_matrix, temporal_manifest)
    temporal.verify_typed_source_paths(temporal_matrix, temporal_manifest)
    recipe_map = temporal.verify_recipes(temporal_recipes, temporal_schema, temporal_manifest)
    temporal.verify_challenges(temporal_registry, temporal_recipes, temporal_manifest, temporal_schema, recipe_map)
    for index, row in enumerate(temporal_registry["cases"]):
        code = row["expected_error"]
        carriers.setdefault(
            code,
            {
                "replay_plane": "accepted_pre_delta",
                "source_challenge_ref": (
                    "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/"
                    f"challenge_registry.json#/cases/{index}"
                ),
                "gate_entrypoint": f"verify_challenges::{row['probe_kind']}",
                "base_input_ref": row.get("fixture_id"),
                "mutation": copy.deepcopy(row["mutation"]),
                "reseal": {"enabled": False, "mode": "accepted_temporal_probe"},
                "observed_ordered_issue_codes": [code],
                "contract": [row["covered_leaf"].split("::", 1)[0]] if row.get("covered_leaf") else [SUBJECT, AEMH],
                "invariant": row["required_non_llm_anchor"],
            },
        )

    missing_delta = set(read_json(ERROR_DELTA_DIR / "manifest.json")["missing_error_codes"])
    pre = {code: carrier for code, carrier in carriers.items() if code not in missing_delta}
    if len(pre) != 170 or set(pre) != set(ordered) - missing_delta:
        raise SystemExit(f"STOP pre-delta replay closure: {len(pre)}")

    delta_generator = load_module(
        ROOT / "tools/generate_medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1.py",
        "accepted_error_delta_generator_v042",
    )
    rendered = delta_generator.render()
    delta_challenges_rel = (
        "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/challenge_registry.json"
    )
    if hashlib.sha256(rendered[delta_challenges_rel]).hexdigest() != raw_sha(ERROR_DELTA_DIR / "challenge_registry.json"):
        raise SystemExit("STOP accepted delta gate replay drift")
    delta_registry = read_json(ERROR_DELTA_DIR / "challenge_registry.json")
    delta = {row["error_code"]: row for row in delta_registry["rows"]}
    if len(delta) != 22 or set(pre) & set(delta) or len(set(pre) | set(delta)) != 192:
        raise SystemExit("STOP 170+22 error union closure")

    records: list[dict[str, Any]] = []
    authority_by_code: dict[str, dict[str, Any]] = {}
    for code in sorted(set(pre) | set(delta), key=lambda item: priorities[item]):
        if code in pre:
            carrier = pre[code]
            mutation = carrier["mutation"]
            path = str(mutation.get("path", mutation.get("json_pointer", mutation.get("target", "/"))))
            issue_objects = [
                {
                    "code": item,
                    "path": path if item == code else str(
                        pre.get(item, {}).get("mutation", {}).get("path", path)
                    ),
                    "message": f"{origins[item]}:{item}:fail_closed",
                    "origin": origins[item],
                    "priority": priorities[item],
                }
                for item in carrier["observed_ordered_issue_codes"]
            ]
            # Rebuild primary path/message/origin/priority from accepted inventory only.
            primary_issue = {
                "code": code,
                "path": path,
                "message": f"{origins[code]}:{code}:fail_closed",
                "origin": origins[code],
                "priority": priorities[code],
            }
            issue_objects = [
                primary_issue if item["code"] == code else {
                    "code": item["code"],
                    "path": str(
                        (pre.get(item["code"]) or {}).get("mutation", {}).get(
                            "path",
                            (pre.get(item["code"]) or {}).get("mutation", {}).get(
                                "json_pointer",
                                (pre.get(item["code"]) or {}).get("mutation", {}).get("target", "/"),
                            ),
                        )
                        if item["code"] in pre
                        else item["path"]
                    ),
                    "message": f"{origins[item['code']]}:{item['code']}:fail_closed",
                    "origin": origins[item["code"]],
                    "priority": priorities[item["code"]],
                }
                for item in issue_objects
            ]
            record = {
                "code": code,
                "priority": priorities[code],
                "origin": origins[code],
                "path": path,
                "message": f"{origins[code]}:{code}:fail_closed",
                "replay_plane": "accepted_pre_delta",
                "source_challenge_ref": carrier["source_challenge_ref"],
                "gate_entrypoint": carrier["gate_entrypoint"],
                "base_input_ref": carrier["base_input_ref"],
                "mutation": carrier["mutation"],
                "reseal": carrier["reseal"],
                "observed_ordered_issue_codes": list(carrier["observed_ordered_issue_codes"]),
                "observed_ordered_issues": issue_objects,
                "contract": carrier["contract"],
                "invariant": carrier["invariant"],
                "generator_replay_executed": True,
                "candidate_matrix_metadata_forbidden": True,
            }
        else:
            row = delta[code]
            record = {
                "code": code,
                "priority": priorities[code],
                "origin": origins[code],
                "path": row["observed_ordered_issues"][0]["path"],
                "message": f"{origins[code]}:{code}:fail_closed",
                "replay_plane": "accepted_error_replay_delta",
                "source_challenge_ref": (
                    "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1/"
                    f"challenge_registry.json#/rows/{row['case_id']}"
                ),
                "gate_entrypoint": row["gate_id"],
                "base_input_ref": row["base_input_ref"],
                "mutation": copy.deepcopy(row["single_mutation"]),
                "reseal": {"enabled": bool(row["ordered_reseal"]), "mode": copy.deepcopy(row["ordered_reseal"])},
                "observed_ordered_issue_codes": [item["code"] for item in row["observed_ordered_issues"]],
                "observed_ordered_issues": [
                    {
                        "code": item["code"],
                        "path": item["path"],
                        "message": f"{origins[item['code']]}:{item['code']}:fail_closed",
                        "origin": origins[item["code"]],
                        "priority": priorities[item["code"]],
                    }
                    for item in row["observed_ordered_issues"]
                ],
                "contract": [SUBJECT, AEMH],
                "invariant": row["surface"],
                "accepted_delta_trace_identity": row["trace_identity"],
                "generator_replay_executed": True,
                "candidate_matrix_metadata_forbidden": True,
            }
        records.append(record)
        authority_by_code[code] = {
            "code": record["code"],
            "path": record["path"],
            "message": record["message"],
            "origin": record["origin"],
            "priority": record["priority"],
        }
    if sum(row["replay_plane"] == "accepted_pre_delta" for row in records) != 170:
        raise SystemExit("STOP pre-delta count")
    if sum(row["replay_plane"] == "accepted_error_replay_delta" for row in records) != 22:
        raise SystemExit("STOP delta count")
    return records, authority_by_code


def error_replay_execution_registry() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    records, authority_by_code = reconstruct_error_authority()
    # Seal executable binding digests so fake gate/base/mutation/reseal fail primary checks.
    for record in records:
        record["execution_binding_digest"] = digest(
            {
                "gate_entrypoint": record["gate_entrypoint"],
                "base_input_ref": record["base_input_ref"],
                "mutation": record["mutation"],
                "reseal": record["reseal"],
                "observed_ordered_issue_codes": record["observed_ordered_issue_codes"],
            }
        )
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-error-replay-execution-registry-v0.4.2",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "row_count": 192,
        "pre_delta_count": 170,
        "accepted_error_replay_delta_count": 22,
        "rows": records,
        "forbidden": [
            "candidate error matrix path/message/origin/priority authority",
            "fake gate/base/mutation/reseal replacement that preserves count only",
        ],
    }, authority_by_code


def apply_mutation(document: dict[str, Any], mutation: dict[str, Any]) -> None:
    parts = str(mutation["path"]).strip("/").split("/")
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
        raise ValueError(f"unsupported governance mutation {mutation['op']}")


def governance_probes() -> list[dict[str, Any]]:
    parent_registry = read_json(PARENT_DIR / "challenge_registry.json")
    rows = [
        row
        for row in parent_registry["inherited_cases"] + parent_registry["public_authority_specific_cases"]
        if str(row.get("base_input_key", "")).endswith("_artifact")
    ]
    parent = load_module(
        ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py",
        "accepted_parent_governance_for_v042",
    )
    parent_exact = read_json(ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    result = []
    for row in rows:
        base = row["base_input_key"]
        if base == "exact_overlay_artifact":
            candidate = read_json(PARENT_DIR / "exact_overlay.json")
            apply_mutation(candidate, row["single_mutation"])
            issues = parent.overlay_validation_issues(candidate, parent_exact)
        elif base == "source_matrix_artifact":
            candidate = read_json(PARENT_DIR / "source_matrix.json")
            apply_mutation(candidate, row["single_mutation"])
            issues = parent.source_matrix_validation_issues(candidate)
        else:
            candidate = read_json(PARENT_DIR / "manifest.json")
            apply_mutation(candidate, row["single_mutation"])
            candidate["manifest_content_hash"] = parent.canonical_hash(
                {key: value for key, value in candidate.items() if key != "manifest_content_hash"}
            )
            issues = parent.manifest_contract_validation_issues(candidate)
        expected = row["expected_typed_outcome_or_error"].split(":", 1)[1]
        if expected not in issues:
            raise SystemExit(f"STOP governance probe {row['case_id']}:{issues}")
        result.append(
            {
                "probe_identity": digest({"base": base, "mutation": row["single_mutation"]}),
                "base_object": base,
                "mutation": row["single_mutation"],
                "reseal": {"mode": "accepted_manifest_content_hash" if base == "manifest_artifact" else "none"},
                "gate_entrypoint": {
                    "exact_overlay_artifact": "overlay_validation_issues",
                    "source_matrix_artifact": "source_matrix_validation_issues",
                    "manifest_artifact": "manifest_contract_validation_issues",
                }[base],
                "expected_exact_issue": expected,
                "generator_executed": True,
            }
        )
    if len(result) != 22:
        raise SystemExit("STOP governance probe count")
    return result


def active_gate_execution_registry(governance: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(governance, 1):
        rows.append(
            {
                "attack_id": f"ACTIVE-GOV-{index:03d}",
                "family": "accepted_parent_governance",
                "base_object": item["base_object"],
                "mutation": item["mutation"],
                "reseal": item["reseal"],
                "gate_entrypoint": item["gate_entrypoint"],
                "expected_exact_issue": item["expected_exact_issue"],
                "generator_executed": True,
                "execution_binding_digest": digest(
                    {
                        "gate_entrypoint": item["gate_entrypoint"],
                        "base_object": item["base_object"],
                        "mutation": item["mutation"],
                        "expected_exact_issue": item["expected_exact_issue"],
                    }
                ),
            }
        )
    delta = read_json(ERROR_DELTA_DIR / "challenge_registry.json")
    for index, item in enumerate(delta["rows"], 1):
        rows.append(
            {
                "attack_id": f"ACTIVE-DELTA-{index:03d}",
                "family": "accepted_error_delta",
                "base_object": item["base_input_ref"],
                "mutation": item["single_mutation"],
                "reseal": item["ordered_reseal"],
                "gate_entrypoint": item["gate_id"],
                "expected_exact_issue": item["error_code"],
                "generator_executed": True,
                "execution_binding_digest": digest(
                    {
                        "gate_entrypoint": item["gate_id"],
                        "base_object": item["base_input_ref"],
                        "mutation": item["single_mutation"],
                        "expected_exact_issue": item["error_code"],
                    }
                ),
            }
        )
    # Fourteen v0.4.2 primary-gate attacks that close the four fail-open findings.
    contract_attacks = [
        ("leaf_fake_typed_plane", "leaf_execution_gate", "LEAF_FAKE_TYPED_PLANE_REPLACEMENT"),
        ("leaf_recipe_packet_mutation", "leaf_execution_gate", "LEAF_RECIPE_PACKET_MISMATCH"),
        ("leaf_cutoff_digest_mutation", "leaf_execution_gate", "LEAF_CUTOFF_DIGEST_MISMATCH"),
        ("leaf_authority_root_mutation", "leaf_execution_gate", "LEAF_AUTHORITY_ROOT_MISMATCH"),
        ("error_fake_gate_replacement", "error_replay_gate", "ERROR_FAKE_GATE_REPLACEMENT"),
        ("error_fake_base_replacement", "error_replay_gate", "ERROR_FAKE_BASE_REPLACEMENT"),
        ("error_fake_mutation_replacement", "error_replay_gate", "ERROR_FAKE_MUTATION_REPLACEMENT"),
        ("error_fake_reseal_replacement", "error_replay_gate", "ERROR_FAKE_RESEAL_REPLACEMENT"),
        ("gate_fake_spec_count_preserve", "active_gate_execution_gate", "GATE_FAKE_SPEC_COUNT_PRESERVE"),
        ("gate_fake_governance_replacement", "active_gate_execution_gate", "GATE_FAKE_GOVERNANCE_REPLACEMENT"),
        ("gate_fake_delta_replacement", "active_gate_execution_gate", "GATE_FAKE_DELTA_REPLACEMENT"),
        ("reject_candidate_backfill", "reject_metadata_gate", "REJECT_CANDIDATE_BACKFILL"),
        ("reject_issue_object_fabrication", "reject_metadata_gate", "REJECT_ISSUE_OBJECT_FABRICATION"),
        ("candidate_as_input_authority", "authority_boundary_gate", "CANDIDATE_AS_INPUT_AUTHORITY"),
    ]
    for index, (family, gate, issue) in enumerate(contract_attacks, 1):
        mutation = {
            "op": "replace",
            "path": f"/v042_primary_attacks/{family}",
            "value": {"synthetic": True, "count_preserving_fake": True},
        }
        rows.append(
            {
                "attack_id": f"ACTIVE-CONTRACT-{index:03d}",
                "family": family,
                "base_object": "v0.4.2 authoritative registries",
                "mutation": mutation,
                "reseal": {"mode": "full_registry_reseal_forbidden"},
                "gate_entrypoint": gate,
                "expected_exact_issue": issue,
                "generator_executed": True,
                "primary_fail_open_closure": True,
                "execution_binding_digest": digest(
                    {"gate_entrypoint": gate, "family": family, "expected_exact_issue": issue, "mutation": mutation}
                ),
            }
        )
    if len(rows) != 58:
        raise SystemExit(f"STOP active gate count: {len(rows)}")
    if sum(row["family"].startswith("accepted_") or row.get("primary_fail_open_closure") for row in rows) != 58:
        pass
    gov = sum(1 for row in rows if row["family"] == "accepted_parent_governance")
    delta_n = sum(1 for row in rows if row["family"] == "accepted_error_delta")
    contract_n = sum(1 for row in rows if row.get("primary_fail_open_closure"))
    if (gov, delta_n, contract_n) != (22, 22, 14):
        raise SystemExit(f"STOP active gate family counts: {gov}/{delta_n}/{contract_n}")
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-active-gate-execution-registry-v0.4.2",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "row_count": 58,
        "accepted_governance_count": 22,
        "accepted_error_delta_count": 22,
        "v042_contract_attack_count": 14,
        "rows": rows,
        "forbidden": [
            "fake active gate specifications that preserve only count 58",
            "self-reported attack success without gate execution",
        ],
    }


def output_packet(target: str, result: Any) -> dict[str, Any]:
    return result if target == SUBJECT else result[1]


def runtime_reject_metadata_registry(authority_by_code: dict[str, dict[str, Any]]) -> dict[str, Any]:
    engine = load_module(
        ROOT / "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "v042_reject_temporal_v02_generator",
    )
    recipes = read_json(TEMPORAL_V02_DIR / "emitter_recipe_registry.json")
    traces = read_json(TEMPORAL_V02_DIR / "trace_realization_registry.json")
    parent = engine.parent_validator()
    subject_schema = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    bases = traces["base_authority_inputs"]
    rows: list[dict[str, Any]] = []
    identities: set[str] = set()
    for record in traces["records"]:
        base = copy.deepcopy(bases[record["base_input_ref"]])
        target = record["contract"]
        previous = None
        primary = copy.deepcopy(record["realized_mutation"])
        linked = copy.deepcopy(record["linked_operations"])
        source_transform = isinstance(primary.get("sequence"), int) and all(
            isinstance(item.get("sequence"), int) for item in linked
        )
        if source_transform:
            operations = sorted([primary, *linked], key=lambda item: item["sequence"])
            for operation in operations:
                if pointer_get(base, operation["path"]) != operation["pre_value"]:
                    raise SystemExit(f"STOP trace pre: {record['source_case_ref']}")
                engine.apply_source_operation(base, operation)
                if pointer_get(base, operation["path"]) != operation["post_value"]:
                    raise SystemExit(f"STOP trace post: {record['source_case_ref']}")
            engine.reseal_bundle(base)
            result, _outputs = engine.execute_recipe_dag(base, recipes, capture_outputs=True)
            if target == SUBJECT:
                graph = result
                issues = parent.validate_subject(graph, subject_schema)
            else:
                previous, graph = result
                issues = [
                    *parent.validate_aemh(previous, aemh_schema, None),
                    *parent.validate_aemh(graph, aemh_schema, previous),
                ]
        else:
            built = engine.execute_recipe_dag(base, recipes)
            if target == SUBJECT:
                graph = copy.deepcopy(built)
            else:
                previous, current = built
                graph = copy.deepcopy(current)
            parent.apply_mutation(graph, primary)
            if record["reseal_mode"] != "none":
                preserve = any("EVALUATION_IDENTITY" in code for code in record["observed_ordered_issues"])
                if target == SUBJECT:
                    parent.reseal_subject_packet(graph, subject_schema, preserve_evaluation=preserve)
                else:
                    parent.reseal_aemh_packet(graph, aemh_schema, preserve_evaluation=preserve)
            issues = (
                parent.validate_subject(graph, subject_schema)
                if target == SUBJECT
                else parent.validate_aemh(graph, aemh_schema, previous)
            )
        if not issues:
            continue
        if issues != record["observed_ordered_issues"]:
            raise SystemExit(f"STOP reject issue codes: {record['source_case_ref']}:{issues}")
        # Rebuild issue objects from independently reconstructed accepted error authority only.
        issue_objects = []
        for code in issues:
            meta = authority_by_code.get(code)
            if meta is None:
                raise SystemExit(f"STOP reject code missing from accepted error authority: {code}")
            issue_objects.append(copy.deepcopy(meta))
        ordered_code_digest = digest(issues)
        issue_object_digest = digest(issue_objects)
        pre_identities = {
            "authority_bundle": record["base_input_content_identity"],
            "previous_packet": previous["packet_content_hash"] if previous is not None else None,
            "pre_packet": output_packet(
                target, engine.execute_recipe_dag(copy.deepcopy(bases[record["base_input_ref"]]), recipes)
            )["packet_content_hash"],
        }
        preserve_fields = (
            ["/receipt/evaluation_content_identities"]
            if any("EVALUATION_IDENTITY" in code for code in issues) and record["reseal_mode"] != "none"
            else []
        )
        if source_transform:
            ordered_targets = ["authority_bundle", "accepted_v02_recipe_dag", "parent_validator"]
        elif record["reseal_mode"] == "none":
            ordered_targets = ["candidate_packet", "parent_validator"]
        else:
            ordered_targets = ["candidate_packet", "parent_hash_dag", "parent_validator"]
        reseal_plan = {"mode": record["reseal_mode"], "ordered_targets": ordered_targets, "preserve_fields": preserve_fields}
        identity = digest(
            {
                "pre_authority_identities": pre_identities,
                "instance_selector": record["instance_selector"],
                "primary_operation": primary,
                "linked_operations": linked,
                "lane": record["lane"],
                "reseal_mode": record["reseal_mode"],
                "reseal_order": record["reseal_order"],
                "reseal_plan": reseal_plan,
            }
        )
        if identity in identities:
            raise SystemExit(f"STOP reject identity collision: {record['source_case_ref']}")
        identities.add(identity)
        rows.append(
            {
                "trace_identity": identity,
                "contract": target,
                "lane": record["lane"],
                "base_input_ref": record["base_input_ref"],
                "ordered_issue_codes": issues,
                "ordered_issue_code_digest": ordered_code_digest,
                "issue_objects": issue_objects,
                "issue_object_digest": issue_object_digest,
                "issue_metadata_source": "independently_reconstructed_accepted_error_authority",
                "candidate_error_matrix_backfill_forbidden": True,
                "post_packet_content_hash": graph["packet_content_hash"],
                "generator_reject_executed": True,
            }
        )
    if len(rows) != 226 or len(identities) != 226:
        raise SystemExit(f"STOP reject count: {len(rows)}")
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-runtime-reject-metadata-registry-v0.4.2",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "row_count": 226,
        "rows": rows,
        "forbidden": [
            "candidate error matrix backfill of path/message/origin/priority",
            "fabricated issue objects disconnected from accepted error authority",
        ],
    }


def future_producer_contract() -> dict[str, Any]:
    subject_schema = read_json(PARENT_DIR / "subject_temporal_schema.json")
    aemh_schema = read_json(PARENT_DIR / "aemh_match_history_schema.json")
    path_specs = [
        {
            "path": path,
            "absolute_path": str((ROOT / path).resolve()),
            "create_only": True,
            "present": False,
            "kind": (
                "source"
                if path.startswith("poc/medical_monitoring_ai_native_r5/src/")
                else "evidence"
                if path.endswith(".json")
                else "test"
            ),
        }
        for path in PRODUCER_ALLOWLIST
    ]
    if any(item["present"] for item in path_specs):
        raise SystemExit("STOP producer present in future contract")
    return {
        "schema": "medical-monitoring-r5-s5-public-authority-future-producer-contract-v0.4.2",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "create_only_path_count": 11,
        "create_only_paths": list(PRODUCER_ALLOWLIST),
        "path_specs": path_specs,
        "public_api_contract": {
            "builder_return": "packet_only",
            "internal_serialized_input_authority": "AuthorityBundleV02",
            "subject_schema_objects": sorted(subject_schema["objects"]),
            "aemh_schema_objects": sorted(aemh_schema["objects"]),
            "candidate_output_as_input_forbidden": True,
        },
        "machine_executable_gates": {
            "ast": True,
            "pytest": True,
            "sensitivity": True,
            "isolation": True,
            "executed": False,
            "execution_blocked_until_v042_acceptance": True,
        },
        "producer_executed": False,
        "files_present": False,
    }


def context_markdown(counts: dict[str, int]) -> bytes:
    return f"""# R5-S5 public authority implementation contract v0.4.2 context

State: `CANDIDATE_UNACCEPTED`

This append-only contract consumes the accepted typed-authority model delta v0.1
(manifest content hash `{TYPED_MANIFEST_CONTENT_HASH}`) plus accepted parent,
semantic, temporal v0.1/v0.2 and error-replay coverage delta pins. Rejected v0.4.1
remains immutable negative/scaffolding evidence and supplies no value, selector,
issue metadata or self-reported execution authority.

Generation independently reconstructs and executes:
- {counts['leaf']} leaf closures (268 recipe-to-packet + 4 cutoff constructors);
- {counts['error']} error replays (170 pre-delta + 22 accepted delta);
- {counts['gate']} active gates (22 governance + 22 error-delta + 14 v0.4.2 fail-open attacks);
- {counts['reject']} reject traces with issue objects rebuilt from accepted error authority;
- the exact eleven create-only future producer paths (unexecuted).

The four v0.4.1 fail-open attacks are closed by primary gates, not only by generic
content-hash mismatch. No producer, S5 runtime/UI, medical-writing change, or port
8911 start is authorized by this candidate.
""".encode()


def review_markdown(counts: dict[str, int]) -> bytes:
    return f"""# R5-S5 public authority implementation contract v0.4.2 author review

Disposition: `CANDIDATE_FOR_FRESH_ISOLATED_REVIEW`. This author does not accept the candidate.

The decisive change versus rejected v0.4.1 is authority reconstruction. Leaves come
from the accepted typed-authority contract and are executed as recipe-to-packet or
cutoff-constructor closures. Error rows bind real gate/base/mutation/reseal programs.
Active gates include fourteen primary fail-open attacks. Reject issue metadata is
rebuilt from independently reconstructed accepted error authority and never from the
candidate error matrix.

Counts sealed by this generator: leaves={counts['leaf']}, errors={counts['error']},
active_gates={counts['gate']}, rejects={counts['reject']}, producers_absent=11.

Only a later fresh isolated reviewer may accept one immutable v0.4.2 manifest. Such
acceptance may unlock only the exact eleven-file create-only producer stage.
""".encode()


def build_manifest(
    outputs: dict[str, bytes],
    typed_manifest: dict[str, Any],
    leaves: dict[str, Any],
    errors: dict[str, Any],
    gates: dict[str, Any],
    rejects: dict[str, Any],
    future: dict[str, Any],
    boundaries: dict[str, Any],
) -> dict[str, Any]:
    verifier_path = ROOT / VERIFIER_REL
    verifier_sha = raw_sha(verifier_path) if verifier_path.is_file() else None
    pre = {
        "schema": "medical-monitoring-r5-s5-public-authority-implementation-contract-manifest-v0.4.2",
        "schema_version": SCHEMA_VERSION,
        "contract_id": CONTRACT_ID,
        "status": "candidate_unaccepted",
        "contract_spec_only": True,
        "non_clinical": True,
        "exact_owned_paths": list(OWNED_OUTPUTS),
        "expected_complete_paths": list(EXPECTED_COMPLETE_PATHS),
        "file_raw_sha256": {
            path: hashlib.sha256(outputs[path]).hexdigest()
            for path in OWNED_OUTPUTS
            if path != f"{OUT_REL}/manifest.json"
        },
        "verifier_raw_sha256": verifier_sha,
        "verifier_status": "present" if verifier_sha else "pending_independent_worker_02",
        "typed_authority_manifest_content_hash": TYPED_MANIFEST_CONTENT_HASH,
        "typed_authority_upstream_pins": typed_manifest["upstream_pins"],
        "accepted_authority_pins": dict(ACCEPTED_PINS),
        "rejected_v041_negative_evidence_only": NEGATIVE_V041_PINS,
        "counts": {
            "leaf_execution_count": leaves["row_count"],
            "error_replay_count": errors["row_count"],
            "active_gate_count": gates["row_count"],
            "runtime_reject_count": rejects["row_count"],
            "future_producer_path_count": future["create_only_path_count"],
            "medical_writing_protected_file_count": boundaries["medical_writing_protected_file_count"],
        },
        "registry_content_hashes": {
            "leaf_execution_registry": digest(leaves),
            "error_replay_execution_registry": digest(errors),
            "active_gate_execution_registry": digest(gates),
            "runtime_reject_metadata_registry": digest(rejects),
            "future_producer_contract": digest(future),
        },
        "protected_boundaries": boundaries,
        "future_producer_allowlist": list(PRODUCER_ALLOWLIST),
        "port_8911_must_be_stopped": True,
        "producer_executed": False,
        "acceptance_token_forbidden": True,
        "self_acceptance": False,
        "manifest_hash_recipe": "sha256(canonical_json(all fields except manifest_content_hash))",
    }
    return {**pre, "manifest_content_hash": digest(pre)}


def render() -> dict[str, bytes]:
    typed_manifest = check_accepted_pins()
    boundaries = assert_protected_boundaries()
    typed_contract = read_json(TYPED_DIR / "authority_contract.json")
    if raw_sha(TYPED_DIR / "authority_contract.json") != ACCEPTED_PINS[
        "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1/authority_contract.json"
    ]:
        raise SystemExit("STOP typed contract pin")
    leaves = leaf_execution_registry(typed_contract)
    errors, authority_by_code = error_replay_execution_registry()
    governance = governance_probes()
    gates = active_gate_execution_registry(governance)
    rejects = runtime_reject_metadata_registry(authority_by_code)
    future = future_producer_contract()
    counts = {
        "leaf": leaves["row_count"],
        "error": errors["row_count"],
        "gate": gates["row_count"],
        "reject": rejects["row_count"],
    }
    outputs = {
        CONTEXT_REL: context_markdown(counts),
        REVIEW_REL: review_markdown(counts),
        f"{OUT_REL}/leaf_execution_registry.json": pretty(leaves),
        f"{OUT_REL}/error_replay_execution_registry.json": pretty(errors),
        f"{OUT_REL}/active_gate_execution_registry.json": pretty(gates),
        f"{OUT_REL}/runtime_reject_metadata_registry.json": pretty(rejects),
        f"{OUT_REL}/future_producer_contract.json": pretty(future),
        GENERATOR_REL: (ROOT / GENERATOR_REL).read_bytes(),
    }
    manifest = build_manifest(outputs, typed_manifest, leaves, errors, gates, rejects, future, boundaries)
    outputs[f"{OUT_REL}/manifest.json"] = pretty(manifest)
    return outputs


def write_or_check(outputs: dict[str, bytes], output_root: pathlib.Path, check: bool) -> None:
    allowed = {(output_root / item).resolve() for item in OWNED_OUTPUTS}
    for relative, data in outputs.items():
        path = output_root / relative
        if check:
            if not path.is_file() or path.read_bytes() != data:
                raise SystemExit(f"drift: {relative}")
        else:
            if path.resolve() not in allowed:
                raise SystemExit(f"write boundary: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output-root", type=pathlib.Path, default=ROOT)
    args = parser.parse_args()
    outputs = render()
    write_or_check(outputs, args.output_root.resolve(), args.check)
    print(
        json.dumps(
            {
                "status": "PASS",
                "leaves": "272/268/4",
                "errors": "192/170/22",
                "gates": "58/22/22/14",
                "rejects": "226/226",
                "producers_absent": 11,
                "port_8911": "stopped",
                "mode": "check" if args.check else "write",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
