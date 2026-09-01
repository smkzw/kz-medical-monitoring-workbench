#!/usr/bin/env python3
"""Apply the independently accepted case-030 D07 oracle erratum."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_d07_challenge_registry as g  # noqa: E402

CONTRACT = ROOT / "reviews/medical_monitoring_r4_d07_safety_laboratory_slice_contract_v1_20260813.md"
CATALOG = ROOT / "reviews/medical_monitoring_r4_d07_typed_fixture_catalog_v1_20260813.json"
ORACLE = ROOT / "reviews/medical_monitoring_r4_d07_expected_outcome_oracle_v1_20260813.json"
REGISTRY = ROOT / "reviews/medical_monitoring_r4_d07_challenge_manifest_registry_v1_20260813.json"
GENERATOR = ROOT / "tools/generate_d07_challenge_registry.py"

EXPECTED_HASHES = {
    CONTRACT: "0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84",
    CATALOG: "419f2a060e0d46550c0e1faaeabddd5094a12556ba7f9ba9f66d99be5b5ee4cd",
    ORACLE: "28b792a39676aaf9be442e2d2bc349f8f33b214c485bed1d487e752876c3626b",
    REGISTRY: "470bfc41b390358697d1066e9611ee18ac2944bebabfe0352244cd1b09e1b4a0",
    GENERATOR: "1b230c374830d69c7bc37323960696f9a50ed3bba16bfa9f8996e6a64ce44a9b",
}

OLD_PAIRS = [
    {"cardinality": "one", "source_object_id": "SYN-RES-030-3", "target_kind": "listing_row", "target_object_id": "SYN-REC-030-3"},
    {"cardinality": "one", "source_object_id": "SYN-RES-030-3", "target_kind": "lab_manual_rule", "target_object_id": "SYN-TREND-1"},
]
NEW_PAIRS = [
    {"cardinality": "one", "source_object_id": "SYN-RES-030-3", "target_kind": "listing_row", "target_object_id": "SYN-REC-030-3"},
    {"cardinality": "one", "source_object_id": "SYN-RES-030-3", "target_kind": "lab_manual_rule", "target_object_id": "SYN-GRADESET-ALT-5"},
    {"cardinality": "one", "source_object_id": "SYN-RES-030-3", "target_kind": "protocol_clause", "target_object_id": "SYN-MR-ALT-ACTION-1"},
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".case030.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def build_manifest(oracle: dict) -> dict:
    catalog = g.load_json(CATALOG, "typed_fixture_catalog")
    _, catalog_by_id = g.validate_catalog(catalog)
    _, oracle_by_id, path_types = g.validate_oracle(oracle, catalog_by_id)
    bindings = []
    for case_id in [f"{number:03d}" for number in range(1, g.EXPECTED_CASE_COUNT + 1)]:
        case = catalog_by_id[case_id]
        expectation = oracle_by_id[case_id]
        program = g.compile_assertion_program(
            case_id,
            expectation["expected_leaf_set"],
            expectation["expected_trace_leaf_set"],
            expectation["expected_source_leaf_set"],
            expectation.get("expected_integrity_error"),
            path_types,
        )
        bindings.append({
            "case_id": case_id,
            "fixture_id": case["fixture_id"],
            "oracle_case_id": case_id,
            "entrypoint": case["entrypoint"],
            "required_assertion_clause_ids": [item["clause_id"] for item in program],
            "required_trace_paths": sorted(expectation["expected_trace_leaf_set"]),
            "required_source_paths": sorted(expectation["expected_source_leaf_set"]),
            "required_test_id": f"d07-test-{case_id}",
        })
    core = {
        "schema_version": g.SCHEMA_VERSION,
        "artifact_kind": "challenge_manifest",
        "contract_semantic_hash": g.CANONICAL_CONTRACT_SEMANTIC_HASH,
        "manifest_id": "medical-monitoring-r4-d07-challenge-manifest",
        "ordered_bindings": bindings,
        "case_count": len(bindings),
    }
    manifest = {**core, "content_hash": g.content_hash(core)}
    g.validate_manifest(manifest, catalog_by_id)
    return manifest


def main() -> int:
    for path, expected in EXPECTED_HASHES.items():
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"precondition failed: {path} {actual} != {expected}")

    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    if oracle.get("content_hash") != "cc85edefeefda2cafa7ade573b8abfa531b48cf081e275de6c65fda4d4e733f8":
        raise SystemExit("precondition failed: oracle content hash drift")
    expectation = next(item for item in oracle["ordered_expectations"] if item["case_id"] == "030")
    source = expectation["expected_source_leaf_set"]
    if source.get("source.reverse_binding_count") != 2 or source.get("source.source_jump_target_pairs") != OLD_PAIRS:
        raise SystemExit("precondition failed: case 030 old source leaves drift")
    source["source.reverse_binding_count"] = 3
    source["source.source_jump_target_pairs"] = NEW_PAIRS
    oracle["content_hash"] = g.content_hash(oracle)
    write_json(ORACLE, oracle)

    write_json(REGISTRY, build_manifest(oracle))
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    print(json.dumps({
        "changed_leaf_count": 2,
        "oracle_file_sha256": sha256(ORACLE),
        "oracle_content_hash": oracle["content_hash"],
        "registry_file_sha256": sha256(REGISTRY),
        "registry_content_hash": registry["content_hash"],
        "unchanged": {str(path.relative_to(ROOT)): sha256(path) for path in (CONTRACT, CATALOG, GENERATOR)},
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
