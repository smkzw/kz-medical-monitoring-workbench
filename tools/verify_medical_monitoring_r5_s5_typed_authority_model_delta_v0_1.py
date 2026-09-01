#!/usr/bin/env python3
"""Independently verify the R5-S5 typed-authority model delta."""

from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import importlib.util
import json
import re
import socket
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1"
CONTRACT_PATH = ARTIFACT_DIR / "authority_contract.json"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"
GENERATOR_PATH = ROOT / "tools/generate_medical_monitoring_r5_s5_typed_authority_model_delta_v0_1.py"
CONTEXT_PATH = ROOT / "context/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1_20260825_context.md"
REVIEW_PATH = ROOT / "reviews/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1_20260825.md"
V02_GENERATOR = ROOT / "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py"
V02_SCHEMA = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/schema.json"
V02_FIXTURES = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json"
V02_RECIPES = ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/emitter_recipe_registry.json"
ENUMERATION = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/source_join_matrix.json"

EXACT_CONTRACT_KEYS = {
    "authority_model",
    "challenge_cases",
    "contract_id",
    "counts",
    "forbidden",
    "leaf_derivations",
    "recipe_dependency_closure",
    "schema",
    "schema_version",
    "typed_records",
    "upstream_pins",
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
EXPECTED_CHALLENGES = [
    ("TAM-001", "authority_model_masquerades_as_two_truth_planes"),
    ("TAM-002", "typed_record_not_frozen"),
    ("TAM-003", "typed_record_allows_unknown_key"),
    ("TAM-004", "leaf_row_removed"),
    ("TAM-005", "leaf_row_duplicated"),
    ("TAM-006", "recipe_dependency_removed"),
    ("TAM-007", "recipe_dependency_added"),
    ("TAM-008", "recipe_id_drift"),
    ("TAM-009", "typed_constructor_digest_drift"),
    ("TAM-010", "rejected_r1_field_selector_reintroduced"),
    ("TAM-011", "upstream_pin_drift"),
    ("TAM-012", "unknown_contract_key"),
]
EXPECTED_UPSTREAM_PINS = {
    "parent_aemh_schema": {
        "path": "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json",
        "raw_sha256": "479dc2759833d698fd761247f4ec504069880717ec9c64631242ad2554b19840",
    },
    "parent_subject_schema": {
        "path": "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json",
        "raw_sha256": "d2f56f21dc7b228736b2efbdc4c1db3a28185e25895563c0b59a812cd126a0f4",
    },
    "rejected_v041_leaf_enumeration": {
        "path": "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/source_join_matrix.json",
        "raw_sha256": "32df331bb5f48b174194384f9297ece2df9d26c80367507ac66657d0a2f7ee36",
    },
    "rejected_v041_manifest": {
        "path": "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/manifest.json",
        "raw_sha256": "1033daaa81eb4c0eede2445b5a8228e37d54d6621feb8b35ebb179a20d55c5bd",
    },
    "temporal_v02_acceptance": {
        "path": "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_acceptance_record_20260821.md",
        "raw_sha256": "d08b4ed27f9829db4cdcab0837f3623c244ee8c888cce699c55580621bd68ef4",
    },
    "temporal_v02_fixtures": {
        "path": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json",
        "raw_sha256": "f9bf0c8031d3acba615b5ac147c27866c8a7430154a0bb98fc24314619009ae7",
    },
    "temporal_v02_generator": {
        "path": "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "raw_sha256": "40be3c5bf8c3a2f09e6380d7309bb3388aead1895b59f7a0ed4a276e3bc0249e",
    },
    "temporal_v02_manifest": {
        "path": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json",
        "raw_sha256": "466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8",
    },
    "temporal_v02_recipes": {
        "path": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/emitter_recipe_registry.json",
        "raw_sha256": "e7a8d5246d71e7b2baece0d21909518426da6d3799bfd6913d4fefa81729bf39",
    },
    "temporal_v02_schema": {
        "path": "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/schema.json",
        "raw_sha256": "74617b858f961f3af615b3d96a51625427faeecfac8c5a4011ecac4fd79dabbc",
    },
    "temporal_v02_verifier": {
        "path": "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "raw_sha256": "7b78dd1b649cd937c6f182719896ab27cb82a4bf84b5be27902e111a7e109d19",
    },
}
EXPECTED_FORBIDDEN = [
    "R1 mutable fixture classes as a public-leaf value authority",
    "one arbitrary typed field reused for unrelated output leaves",
    "typed decoder described as an independent medical truth plane",
    "candidate output, expected packet, or ConstructionGraph target copied into authority input",
    "direct typed-to-output equality for deterministic derived leaves",
    "unresolved leaves silently mirrored instead of declared deferred",
]


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def pointer_get(value: Any, pointer: str) -> Any:
    node = value
    for part in pointer.strip("/").split("/") if pointer != "/" else []:
        part = part.replace("~1", "/").replace("~0", "~")
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def recipe_ref(value: str) -> str | None:
    if not value.startswith("recipe."):
        return None
    for suffix in (".sealed", ".value"):
        if value.endswith(suffix):
            return value[: -len(suffix)]
    return None


def independent_recipe_closure(recipes_doc: dict[str, Any]) -> list[dict[str, Any]]:
    recipes = {row["recipe_id"]: row for row in recipes_doc["executable_v02_recipes"]}
    memo: dict[str, tuple[str, ...]] = {}

    def visit(recipe_id: str, active: frozenset[str] = frozenset()) -> tuple[str, ...]:
        if recipe_id in memo:
            return memo[recipe_id]
        if recipe_id in active:
            raise ValueError("recipe cycle")
        recipe = recipes[recipe_id]
        direct = {pointer for node in recipe["nodes"] for pointer in node["params"]["authority_input_pointers"]}
        prior = {
            parent
            for node in recipe["nodes"]
            for ref in node["params"]["prior_recipe_output_refs"]
            if (parent := recipe_ref(ref))
        }
        resolved = set(direct)
        for parent in prior:
            resolved.update(visit(parent, active | {recipe_id}))
        memo[recipe_id] = tuple(sorted(resolved))
        return memo[recipe_id]

    rows = []
    for recipe_id in sorted(recipes):
        recipe = recipes[recipe_id]
        direct = sorted({pointer for node in recipe["nodes"] for pointer in node["params"]["authority_input_pointers"]})
        prior = sorted(
            {
                parent
                for node in recipe["nodes"]
                for ref in node["params"]["prior_recipe_output_refs"]
                if (parent := recipe_ref(ref))
            }
        )
        rows.append(
            {
                "direct_authority_pointers": direct,
                "prior_recipe_ids": prior,
                "recipe_content_hash": recipe["recipe_content_hash"],
                "recipe_id": recipe_id,
                "target_contract": recipe["target_contract"],
                "transitive_authority_pointers": list(visit(recipe_id)),
            }
        )
    return rows


def expected_typed_records(schema: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "additional_properties": False,
            "fields": schema["objects"][name]["fields"],
            "frozen": True,
            "name": name,
            "optional": schema["objects"][name]["optional"],
            "required": schema["objects"][name]["required"],
            "runtime_role": "lossless_decoder_not_independent_authority",
        }
        for name in sorted(SOURCE_TYPES)
    ]


def cutoff_from_binding(authority: dict[str, Any], parent_doc: dict[str, Any]) -> dict[str, Any]:
    if parent_doc["hash_recipes"]["object_content_hash"] != (
        "sha256(canonical_json(all exact object fields except that object's *_content_hash field))"
    ):
        raise ValueError("parent object hash recipe")
    binding = authority["source"]["cutoff_binding"]
    body = {
        "state": binding["state"],
        "exact_date": binding["exact_date"],
        "source_locator_refs": sorted(binding["source_locator_refs"]),
    }
    constructed = {**body, "cutoff_content_hash": digest(body)}
    if set(constructed) != set(parent_doc["objects"]["PublicCutoffEndpoint"]):
        raise ValueError("parent cutoff exact keys")
    return constructed


def expected_leaf_derivations(
    enumeration: dict[str, Any],
    closures: list[dict[str, Any]],
    fixtures: dict[str, Any],
    parent_subject: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {row["recipe_id"]: row for row in closures}
    authority_by_contract = {
        row["authority_input"]["target_contract"]: row["authority_input"] for row in fixtures["baselines"]
    }
    rows = []
    for source in enumeration["rows"]:
        closure = by_id[source["recipe_id"]]
        shared_cutoff = source["construction_target"]["target_kind"] == "contract_shared_intermediate"
        constructed = (
            cutoff_from_binding(authority_by_contract[source["contract"]], parent_subject)
            if shared_cutoff
            else None
        )
        rows.append(
            {
                "authority_relation": "serialized_authority_plus_lossless_typed_decode",
                "contract": source["contract"],
                "construction_target_value_digest": digest(constructed[source["leaf"]]) if constructed else None,
                "constructor_id": "subject_public_cutoff_from_binding" if shared_cutoff else None,
                "derivation_kind": "deterministic_typed_constructor" if shared_cutoff else "deterministic_recipe_output",
                "output_json_pointer": source["output_json_pointer"],
                "qualified_leaf": source["qualified_leaf"],
                "recipe_id": source["recipe_id"],
                "recipe_output_json_pointer": None if shared_cutoff else source["recipe_output_json_pointer"],
                "target_verification_json_pointer": None if shared_cutoff else source["output_json_pointer"],
                "target_kind": source["construction_target"]["target_kind"],
                "transitive_authority_pointers": (
                    ["/source/cutoff_binding"] if shared_cutoff else closure["transitive_authority_pointers"]
                ),
                "verification_chain": (
                    [
                        "accepted_v02_exact_schema_validate",
                        "frozen_typed_decode_roundtrip",
                        "typed_constructor_execute",
                        "parent_schema_object_hash_recipe_validate",
                    ]
                    if shared_cutoff
                    else [
                        "accepted_v02_exact_schema_validate",
                        "frozen_typed_decode_roundtrip",
                        "accepted_v02_recipe_execute",
                        "accepted_recipe_to_parent_packet_compare",
                        "accepted_parent_validator",
                    ]
                ),
            }
        )
    return rows


def contract_issues(candidate: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if set(candidate) != EXACT_CONTRACT_KEYS:
        issues.append("TAM_EXACT_KEYS")
        return issues
    expected_model = {
        "construction_graph_role": "independent_deterministic_implementation_check",
        "serialized_input_authority": "accepted_temporal_v02_authority_bundle",
        "typed_decode_role": "lossless_representation_not_second_authority",
        "output_leaf_role": "deterministic_recipe_or_typed_constructor_derivation",
        "shared_intermediate_leaf_role": "deterministic_typed_constructor_from_accepted_binding",
        "parent_validator_role": "independent_contract_validation",
        "three_plane_value_equality_for_all_output_leaves": False,
    }
    if candidate["authority_model"] != expected_model:
        issues.append("TAM_AUTHORITY_MODEL")
    schema = load_json(V02_SCHEMA)
    fixtures = load_json(V02_FIXTURES)
    recipes = load_json(V02_RECIPES)
    enumeration = load_json(ENUMERATION)
    parent_subject = load_json(ROOT / EXPECTED_UPSTREAM_PINS["parent_subject_schema"]["path"])
    closures = independent_recipe_closure(recipes)
    if candidate["typed_records"] != expected_typed_records(schema):
        issues.append("TAM_TYPED_RECORDS")
    if candidate["recipe_dependency_closure"] != closures:
        issues.append("TAM_RECIPE_CLOSURE")
    if candidate["leaf_derivations"] != expected_leaf_derivations(
        enumeration, closures, fixtures, parent_subject
    ):
        issues.append("TAM_LEAF_DERIVATIONS")
    if candidate["forbidden"] != EXPECTED_FORBIDDEN:
        issues.append("TAM_FORBIDDEN")
    if any("typed_source_selector" in json.dumps(row, sort_keys=True) for row in candidate["leaf_derivations"]):
        issues.append("TAM_REJECTED_SELECTOR")
    if candidate["upstream_pins"] != EXPECTED_UPSTREAM_PINS:
        issues.append("TAM_UPSTREAM_PINS")
    elif any(raw_sha(ROOT / row["path"]) != row["raw_sha256"] for row in EXPECTED_UPSTREAM_PINS.values()):
        issues.append("TAM_UPSTREAM_PIN_DRIFT")
    counts = candidate["counts"]
    expected_counts = {
        "accepted_baselines": 2,
        "challenge_cases": 12,
        "leaf_derivations": 272,
        "recipe_closures": 16,
        "typed_records": 17,
        "contract_content_hash": digest({k: v for k, v in candidate.items() if k != "counts"}),
    }
    if counts != expected_counts:
        issues.append("TAM_COUNTS")
    expected_challenges = [
        {"challenge_id": challenge_id, "mutation": mutation, "expected": "reject"}
        for challenge_id, mutation in EXPECTED_CHALLENGES
    ]
    if candidate["challenge_cases"] != expected_challenges:
        issues.append("TAM_CHALLENGES")
    return issues


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
            raise ValueError("union resolution")
        return decode(value, matches[0], schema, classes)
    if type_spec in classes:
        obj = schema["objects"][type_spec]
        if set(value) != set(obj["required"]):
            raise ValueError(f"exact keys: {type_spec}")
        return classes[type_spec](**{field: decode(value[field], obj["fields"][field], schema, classes) for field in obj["required"]})
    return value


def encoded(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: encoded(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, tuple):
        return [encoded(item) for item in value]
    return value


def load_v02_module() -> Any:
    spec = importlib.util.spec_from_file_location("accepted_temporal_v02_generator", V02_GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("v0.2 loader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def output_value(result: Any, contract: str, pointer: str) -> Any:
    packet = result if contract == "subject-temporal-public-v1" else result[1]
    prefix = f"/contracts/{contract}/final_packet"
    if not pointer.startswith(prefix):
        raise ValueError("target pointer")
    return pointer_get(packet, pointer[len(prefix) :] or "/")


def execute_evidence(contract: dict[str, Any]) -> tuple[int, int, int]:
    module = load_v02_module()
    schema = load_json(V02_SCHEMA)
    fixtures = load_json(V02_FIXTURES)
    recipes = load_json(V02_RECIPES)
    enumeration = load_json(ENUMERATION)
    classes = build_classes(schema)
    enum_by_leaf = {row["qualified_leaf"]: row for row in enumeration["rows"]}
    leaf_by_contract: dict[str, list[dict[str, Any]]] = {}
    for row in contract["leaf_derivations"]:
        leaf_by_contract.setdefault(row["contract"], []).append(row)
    decoded_count = compared = parent_valid = 0
    for baseline in fixtures["baselines"]:
        authority = copy.deepcopy(baseline["authority_input"])
        schema_issues = module.validate_authority_bundle(authority, schema)
        if schema_issues:
            raise SystemExit("accepted v0.2 schema: " + ",".join(schema_issues))
        typed = decode(authority, "AuthorityBundleV02", schema, classes)
        if encoded(typed) != authority:
            raise SystemExit("typed roundtrip")
        try:
            setattr(typed, "contract_id", "mutated")
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise SystemExit("typed root mutable")
        try:
            setattr(typed.source, "scope", None)
        except dataclasses.FrozenInstanceError:
            pass
        else:
            raise SystemExit("typed nested record mutable")
        decoded_count += 1
        result, outputs = module.execute_recipe_dag(authority, recipes, capture_outputs=True)
        target = authority["target_contract"]
        previous = result[0] if target == "aemh-match-history-public-v1" else None
        current = result[1] if previous is not None else result
        if module.parent_errors(target, current, previous):
            raise SystemExit("parent validator")
        parent_valid += 1
        for mapping in leaf_by_contract[target]:
            enum = enum_by_leaf[mapping["qualified_leaf"]]
            if mapping["constructor_id"] == "subject_public_cutoff_from_binding":
                parent_subject = load_json(
                    ROOT / EXPECTED_UPSTREAM_PINS["parent_subject_schema"]["path"]
                )
                constructed = cutoff_from_binding(authority, parent_subject)
                leaf = enum["leaf"]
                if digest(constructed[leaf]) != mapping["construction_target_value_digest"]:
                    raise SystemExit("cutoff constructor target mismatch: " + mapping["qualified_leaf"])
                if mapping["transitive_authority_pointers"] != ["/source/cutoff_binding"]:
                    raise SystemExit("cutoff constructor authority")
                compared += 1
                continue
            recipe_value = pointer_get(outputs[f"{mapping['recipe_id']}.sealed"]["value"], mapping["recipe_output_json_pointer"])
            target_value = output_value(result, target, mapping["target_verification_json_pointer"])
            if recipe_value != target_value:
                raise SystemExit("recipe target mismatch: " + mapping["qualified_leaf"])
            for pointer in mapping["transitive_authority_pointers"]:
                pointer_get(authority, pointer)
            if enum["recipe_id"] != mapping["recipe_id"]:
                raise SystemExit("enumeration recipe")
            compared += 1
    return decoded_count, compared, parent_valid


def challenge_evidence(contract: dict[str, Any]) -> int:
    attacks: list[dict[str, Any]] = []
    c = copy.deepcopy(contract)
    c["authority_model"]["typed_decode_role"] = "independent_truth"
    attacks.append(c)
    c = copy.deepcopy(contract)
    c["typed_records"][0]["frozen"] = False
    attacks.append(c)
    c = copy.deepcopy(contract)
    c["typed_records"][0]["additional_properties"] = True
    attacks.append(c)
    c = copy.deepcopy(contract)
    c["leaf_derivations"].pop()
    attacks.append(c)
    c = copy.deepcopy(contract)
    c["leaf_derivations"].append(copy.deepcopy(c["leaf_derivations"][0]))
    attacks.append(c)
    c = copy.deepcopy(contract)
    c["recipe_dependency_closure"][0]["transitive_authority_pointers"].pop()
    attacks.append(c)
    c = copy.deepcopy(contract)
    c["recipe_dependency_closure"][0]["transitive_authority_pointers"].append("/source/bogus")
    attacks.append(c)
    c = copy.deepcopy(contract)
    c["leaf_derivations"][0]["recipe_id"] = "recipe.fake"
    attacks.append(c)
    c = copy.deepcopy(contract)
    cutoff_row = next(row for row in c["leaf_derivations"] if row["constructor_id"] is not None)
    cutoff_row["construction_target_value_digest"] = "0" * 64
    attacks.append(c)
    c = copy.deepcopy(contract)
    c["leaf_derivations"][0]["typed_source_selector"] = {"class_name": "MonitoringRun"}
    attacks.append(c)
    c = copy.deepcopy(contract)
    next(iter(c["upstream_pins"].values()))["raw_sha256"] = "0" * 64
    attacks.append(c)
    c = copy.deepcopy(contract)
    c["unexpected"] = True
    attacks.append(c)
    rejected = sum(bool(contract_issues(candidate)) for candidate in attacks)
    if rejected != 12:
        raise SystemExit(f"challenge rejection: {rejected}/12")
    return rejected


def verify_manifest(contract: dict[str, Any]) -> None:
    manifest = load_json(MANIFEST_PATH)
    expected_paths = sorted(
        str(path.relative_to(ROOT))
        for path in (CONTRACT_PATH, CONTEXT_PATH, REVIEW_PATH, MANIFEST_PATH, GENERATOR_PATH, Path(__file__).resolve())
    )
    if manifest["exact_paths"] != expected_paths or manifest["self_acceptance"] is not False:
        raise SystemExit("manifest boundary")
    for relative, expected in manifest["artifact_raw_sha256"].items():
        if raw_sha(ROOT / relative) != expected:
            raise SystemExit("artifact pin: " + relative)
    if manifest["generator_raw_sha256"] != raw_sha(GENERATOR_PATH):
        raise SystemExit("generator pin")
    if manifest["verifier_raw_sha256"] != raw_sha(Path(__file__).resolve()):
        raise SystemExit("verifier pin")
    expected_content = digest({**manifest, "manifest_content_hash": ""})
    if manifest["manifest_content_hash"] != expected_content:
        raise SystemExit("manifest content hash")
    if manifest["upstream_pins"] != contract["upstream_pins"]:
        raise SystemExit("manifest upstream pins")


def verify_protected_boundaries() -> tuple[int, int]:
    rejected_manifest = load_json(
        ROOT / EXPECTED_UPSTREAM_PINS["rejected_v041_manifest"]["path"]
    )
    protected = rejected_manifest["protected_pins"]
    inventory = protected["medical_writing_inventory_contract"]
    pattern = re.compile(inventory["relative_path_regex"])
    paths = sorted(
        path.relative_to(ROOT).as_posix()
        for root_name in inventory["roots"]
        for path in (ROOT / root_name).rglob("*")
        if path.is_file() and pattern.search(path.relative_to(ROOT).as_posix())
    )
    payload = b"".join(
        relative.encode() + b"\0" + raw_sha(ROOT / relative).encode() + b"\n"
        for relative in paths
    )
    aggregate = hashlib.sha256(payload).hexdigest()
    expected = (
        protected["medical_writing_protected_file_count"],
        protected["medical_writing_protected_inventory_sha256"],
    )
    if (len(paths), aggregate) != expected or expected != (
        542,
        "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca",
    ):
        raise SystemExit("medical-writing protected inventory")
    producer_paths = rejected_manifest["future_producer_allowlist"]
    if len(producer_paths) != 11 or any((ROOT / relative).exists() for relative in producer_paths):
        raise SystemExit("future producer absence")
    return len(paths), len(producer_paths)


def port_stopped() -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", 8911)) != 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    contract = load_json(CONTRACT_PATH)
    issues = contract_issues(contract)
    if issues:
        raise SystemExit("contract: " + ",".join(issues))
    verify_manifest(contract)
    medical_writing_count, absent_producer_count = verify_protected_boundaries()
    decoded, compared, parent_valid = execute_evidence(contract)
    rejected = challenge_evidence(contract)
    if not port_stopped():
        raise SystemExit("8911 listening")
    print(
        "TYPED_AUTHORITY_MODEL_DELTA_VERIFIER_OK "
        f"decoded={decoded} compared={compared} parent_valid={parent_valid} challenges={rejected} "
        f"medical_writing={medical_writing_count} producers_absent={absent_producer_count} port_8911=stopped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
