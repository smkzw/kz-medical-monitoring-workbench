#!/usr/bin/env python3
"""Generate the R5-S5 typed-authority model delta.

The accepted temporal v0.2 AuthorityBundle is the sole serialized input
authority.  Frozen typed records are a lossless decoder, not a second truth
plane.  Public leaves remain deterministic recipe outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1"
CONTRACT_PATH = ARTIFACT_DIR / "authority_contract.json"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"
CONTEXT_PATH = ROOT / "context/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1_20260825_context.md"
REVIEW_PATH = ROOT / "reviews/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1_20260825.md"
GENERATOR_PATH = Path(__file__).resolve()
VERIFIER_PATH = ROOT / "tools/verify_medical_monitoring_r5_s5_typed_authority_model_delta_v0_1.py"

UPSTREAM = {
    "temporal_v02_schema": (
        ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/schema.json",
        "74617b858f961f3af615b3d96a51625427faeecfac8c5a4011ecac4fd79dabbc",
    ),
    "temporal_v02_fixtures": (
        ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/full_graph_fixture_registry.json",
        "f9bf0c8031d3acba615b5ac147c27866c8a7430154a0bb98fc24314619009ae7",
    ),
    "temporal_v02_recipes": (
        ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/emitter_recipe_registry.json",
        "e7a8d5246d71e7b2baece0d21909518426da6d3799bfd6913d4fefa81729bf39",
    ),
    "temporal_v02_manifest": (
        ROOT / "artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2/manifest.json",
        "466b0ae605b83a57f0e184446db311beb05ff5e4e1998a7dc5be9bb44d2b7de8",
    ),
    "temporal_v02_generator": (
        ROOT / "tools/generate_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "40be3c5bf8c3a2f09e6380d7309bb3388aead1895b59f7a0ed4a276e3bc0249e",
    ),
    "temporal_v02_verifier": (
        ROOT / "tools/verify_medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2.py",
        "7b78dd1b649cd937c6f182719896ab27cb82a4bf84b5be27902e111a7e109d19",
    ),
    "temporal_v02_acceptance": (
        ROOT / "context/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_2_acceptance_record_20260821.md",
        "d08b4ed27f9829db4cdcab0837f3623c244ee8c888cce699c55580621bd68ef4",
    ),
    "parent_subject_schema": (
        ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json",
        "d2f56f21dc7b228736b2efbdc4c1db3a28185e25895563c0b59a812cd126a0f4",
    ),
    "parent_aemh_schema": (
        ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json",
        "479dc2759833d698fd761247f4ec504069880717ec9c64631242ad2554b19840",
    ),
    # Enumeration only. This rejected candidate supplies no values or authority.
    "rejected_v041_leaf_enumeration": (
        ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/source_join_matrix.json",
        "32df331bb5f48b174194384f9297ece2df9d26c80367507ac66657d0a2f7ee36",
    ),
    "rejected_v041_manifest": (
        ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/manifest.json",
        "1033daaa81eb4c0eede2445b5a8228e37d54d6621feb8b35ebb179a20d55c5bd",
    ),
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

CONTRACT_KEYS = {
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


def raw_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load(name: str) -> Any:
    path, expected = UPSTREAM[name]
    actual = raw_sha(path)
    if actual != expected:
        raise SystemExit(f"upstream pin drift: {name}: {actual}")
    if path.suffix == ".json":
        return json.loads(path.read_text())
    return path.read_text()


def recipe_ref(value: str) -> str | None:
    if not value.startswith("recipe."):
        return None
    for suffix in (".sealed", ".value"):
        if value.endswith(suffix):
            return value[: -len(suffix)]
    return None


def build_recipe_closure(recipes_doc: dict[str, Any]) -> list[dict[str, Any]]:
    recipes = {row["recipe_id"]: row for row in recipes_doc["executable_v02_recipes"]}
    memo: dict[str, tuple[str, ...]] = {}

    def roots(recipe_id: str, stack: tuple[str, ...] = ()) -> tuple[str, ...]:
        if recipe_id in memo:
            return memo[recipe_id]
        if recipe_id in stack:
            raise SystemExit(f"recipe cycle: {' -> '.join((*stack, recipe_id))}")
        recipe = recipes[recipe_id]
        direct: set[str] = set()
        prior: set[str] = set()
        for node in recipe["nodes"]:
            direct.update(node["params"]["authority_input_pointers"])
            for ref in node["params"]["prior_recipe_output_refs"]:
                parent = recipe_ref(ref)
                if parent:
                    prior.add(parent)
        result = set(direct)
        for parent in prior:
            result.update(roots(parent, (*stack, recipe_id)))
        memo[recipe_id] = tuple(sorted(result))
        return memo[recipe_id]

    output = []
    for recipe_id in sorted(recipes):
        recipe = recipes[recipe_id]
        direct = sorted({p for n in recipe["nodes"] for p in n["params"]["authority_input_pointers"]})
        prior = sorted(
            {
                parent
                for n in recipe["nodes"]
                for ref in n["params"]["prior_recipe_output_refs"]
                if (parent := recipe_ref(ref))
            }
        )
        output.append(
            {
                "direct_authority_pointers": direct,
                "prior_recipe_ids": prior,
                "recipe_content_hash": recipe["recipe_content_hash"],
                "recipe_id": recipe_id,
                "target_contract": recipe["target_contract"],
                "transitive_authority_pointers": list(roots(recipe_id)),
            }
        )
    return output


def pointer_get(value: Any, pointer: str) -> Any:
    node = value
    for part in pointer.strip("/").split("/") if pointer != "/" else []:
        part = part.replace("~1", "/").replace("~0", "~")
        node = node[int(part)] if isinstance(node, list) else node[part]
    return node


def validate_parent_leaf(row: dict[str, Any], parent_docs: dict[str, Any]) -> None:
    doc = parent_docs[row["contract"]]
    obj = doc["objects"].get(row["object_type"])
    if not isinstance(obj, dict) or row["leaf"] not in obj:
        raise SystemExit(f"parent leaf missing: {row['qualified_leaf']}")


def subject_public_cutoff(authority_input: dict[str, Any], parent_doc: dict[str, Any]) -> dict[str, Any]:
    if parent_doc["hash_recipes"]["object_content_hash"] != (
        "sha256(canonical_json(all exact object fields except that object's *_content_hash field))"
    ):
        raise SystemExit("parent object hash recipe drift")
    binding = authority_input["source"]["cutoff_binding"]
    core = {
        "state": binding["state"],
        "exact_date": binding["exact_date"],
        "source_locator_refs": sorted(binding["source_locator_refs"]),
    }
    constructed = {**core, "cutoff_content_hash": digest(core)}
    if set(constructed) != set(parent_doc["objects"]["PublicCutoffEndpoint"]):
        raise SystemExit("parent cutoff exact keys")
    return constructed


def build_contract() -> dict[str, Any]:
    schema = load("temporal_v02_schema")
    fixtures = load("temporal_v02_fixtures")
    recipes_doc = load("temporal_v02_recipes")
    enumeration = load("rejected_v041_leaf_enumeration")
    parent_docs = {
        "subject-temporal-public-v1": load("parent_subject_schema"),
        "aemh-match-history-public-v1": load("parent_aemh_schema"),
    }
    load("temporal_v02_manifest")
    load("temporal_v02_generator")
    load("temporal_v02_verifier")
    load("temporal_v02_acceptance")
    load("rejected_v041_manifest")

    if len(enumeration["rows"]) != 272:
        raise SystemExit("leaf enumeration count")
    closures = build_recipe_closure(recipes_doc)
    closure_by_id = {row["recipe_id"]: row for row in closures}
    baselines = {row["authority_input"]["target_contract"]: row["authority_input"] for row in fixtures["baselines"]}

    leaf_derivations = []
    seen: set[str] = set()
    for row in enumeration["rows"]:
        validate_parent_leaf(row, parent_docs)
        qleaf = row["qualified_leaf"]
        if qleaf in seen:
            raise SystemExit(f"duplicate leaf: {qleaf}")
        seen.add(qleaf)
        closure = closure_by_id.get(row["recipe_id"])
        if closure is None:
            raise SystemExit(f"recipe missing: {row['recipe_id']}")
        authority_input = baselines[row["contract"]]
        for pointer in closure["transitive_authority_pointers"]:
            pointer_get(authority_input, pointer)
        shared_cutoff = row["construction_target"]["target_kind"] == "contract_shared_intermediate"
        constructed_cutoff = (
            subject_public_cutoff(authority_input, parent_docs[row["contract"]]) if shared_cutoff else None
        )
        construction_digest = digest(constructed_cutoff[row["leaf"]]) if constructed_cutoff else None
        if shared_cutoff and construction_digest != row["construction_target"]["resolved_value_content_hash"]:
            raise SystemExit(f"enumeration comparison drift: {qleaf}")
        leaf_derivations.append(
            {
                "authority_relation": "serialized_authority_plus_lossless_typed_decode",
                "contract": row["contract"],
                "construction_target_value_digest": construction_digest,
                "constructor_id": "subject_public_cutoff_from_binding" if shared_cutoff else None,
                "derivation_kind": "deterministic_typed_constructor" if shared_cutoff else "deterministic_recipe_output",
                "output_json_pointer": row["output_json_pointer"],
                "qualified_leaf": qleaf,
                "recipe_id": row["recipe_id"],
                "recipe_output_json_pointer": (
                    None if shared_cutoff else row["recipe_output_json_pointer"]
                ),
                "target_verification_json_pointer": (
                    None if shared_cutoff else row["output_json_pointer"]
                ),
                "target_kind": row["construction_target"]["target_kind"],
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

    typed_records = []
    for name in sorted(SOURCE_TYPES):
        obj = schema["objects"][name]
        typed_records.append(
            {
                "additional_properties": False,
                "fields": obj["fields"],
                "frozen": True,
                "name": name,
                "optional": obj["optional"],
                "required": obj["required"],
                "runtime_role": "lossless_decoder_not_independent_authority",
            }
        )

    challenges = [
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
    contract = {
        "authority_model": {
            "construction_graph_role": "independent_deterministic_implementation_check",
            "serialized_input_authority": "accepted_temporal_v02_authority_bundle",
            "typed_decode_role": "lossless_representation_not_second_authority",
            "output_leaf_role": "deterministic_recipe_or_typed_constructor_derivation",
            "shared_intermediate_leaf_role": "deterministic_typed_constructor_from_accepted_binding",
            "parent_validator_role": "independent_contract_validation",
            "three_plane_value_equality_for_all_output_leaves": False,
        },
        "challenge_cases": [
            {"challenge_id": cid, "mutation": mutation, "expected": "reject"} for cid, mutation in challenges
        ],
        "contract_id": "medical-monitoring-r5-s5-typed-authority-model-delta-v0.1",
        "counts": {
            "accepted_baselines": len(fixtures["baselines"]),
            "challenge_cases": len(challenges),
            "leaf_derivations": len(leaf_derivations),
            "recipe_closures": len(closures),
            "typed_records": len(typed_records),
        },
        "forbidden": [
            "R1 mutable fixture classes as a public-leaf value authority",
            "one arbitrary typed field reused for unrelated output leaves",
            "typed decoder described as an independent medical truth plane",
            "candidate output, expected packet, or ConstructionGraph target copied into authority input",
            "direct typed-to-output equality for deterministic derived leaves",
            "unresolved leaves silently mirrored instead of declared deferred",
        ],
        "leaf_derivations": leaf_derivations,
        "recipe_dependency_closure": closures,
        "schema": "typed-authority-model-delta-v0.1",
        "schema_version": "2026-08-25.1",
        "typed_records": typed_records,
        "upstream_pins": {
            name: {"path": str(path.relative_to(ROOT)), "raw_sha256": sha} for name, (path, sha) in UPSTREAM.items()
        },
    }
    if set(contract) != CONTRACT_KEYS:
        raise SystemExit("contract exact keys")
    contract["counts"]["contract_content_hash"] = digest({k: v for k, v in contract.items() if k != "counts"})
    return contract


def context_markdown(contract: dict[str, Any]) -> bytes:
    return f"""# R5-S5 Typed Authority Model Delta v0.1 Context

State: `CANDIDATE_UNACCEPTED`

This delta corrects one false premise in rejected v0.4.1: the accepted temporal v0.2
`AuthorityBundleV02` is the sole serialized input authority. Frozen typed records are
a lossless decoder of that authority, not a second medical truth plane. Of the 272
enumerated parent leaves, 268 are accepted recipe outputs checked against the parent
packet; four shared cutoff leaves are constructed from accepted `cutoff_binding` and
validated with the parent schema object-hash recipe.

Counts: {contract['counts']['typed_records']} typed input records,
{contract['counts']['recipe_closures']} recipe dependency closures,
{contract['counts']['leaf_derivations']} public leaf derivations, and
{contract['counts']['challenge_cases']} fail-closed challenges.

This candidate does not modify or accept v0.4.1, create producer files, start 8911,
touch medical-writing, or accept UI/browser/real-project/model/product behavior.
""".encode()


def review_markdown(contract: dict[str, Any]) -> bytes:
    return f"""# R5-S5 Typed Authority Model Delta v0.1 Author Review

Disposition: `CANDIDATE_FOR_FRESH_ISOLATED_REVIEW`

The minimal correction is semantic, not another value plane. The contract removes
all R1 mutable-class leaf selectors, freezes {contract['counts']['typed_records']}
exact frozen decoder records from the already accepted v0.2 input schema. Of the
{contract['counts']['leaf_derivations']} parent leaves, 268 bind through accepted
recipe outputs to the parent packet; four shared cutoff leaves are constructed from
accepted `cutoff_binding` under the parent object-content-hash recipe.

The author does not accept this candidate. A fresh reviewer must independently test
round-trip decoding, recipe closure, the 272-leaf bijection, upstream pins, all
challenge mutations, the protected 542-file medical-writing aggregate, and exact
absence of the 11 future producer paths before the delta can unlock a v0.4.1 rewrite.
""".encode()


def render() -> dict[Path, bytes]:
    contract = build_contract()
    outputs = {
        CONTRACT_PATH: pretty(contract),
        CONTEXT_PATH: context_markdown(contract),
        REVIEW_PATH: review_markdown(contract),
    }
    manifest = {
        "artifact_raw_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(data).hexdigest() for path, data in outputs.items()},
        "contract_id": contract["contract_id"],
        "exact_paths": sorted(
            str(path.relative_to(ROOT))
            for path in (*outputs, MANIFEST_PATH, GENERATOR_PATH, VERIFIER_PATH)
        ),
        "generator_raw_sha256": raw_sha(GENERATOR_PATH),
        "manifest_content_hash": "",
        "schema": "typed-authority-model-delta-manifest-v0.1",
        "self_acceptance": False,
        "upstream_pins": contract["upstream_pins"],
        "verifier_raw_sha256": raw_sha(VERIFIER_PATH),
    }
    manifest["manifest_content_hash"] = digest({**manifest, "manifest_content_hash": ""})
    outputs[MANIFEST_PATH] = pretty(manifest)
    return outputs


def write_or_check(outputs: dict[Path, bytes], check: bool) -> None:
    if check:
        stale = [str(path.relative_to(ROOT)) for path, data in outputs.items() if not path.exists() or path.read_bytes() != data]
        if stale:
            raise SystemExit("stale outputs: " + ", ".join(stale))
        return
    for path, data in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = render()
    write_or_check(outputs, args.check)
    print(f"TYPED_AUTHORITY_MODEL_DELTA_GENERATOR_OK mode={'check' if args.check else 'write'} files={len(outputs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
