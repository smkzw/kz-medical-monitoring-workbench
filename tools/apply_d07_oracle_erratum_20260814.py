#!/usr/bin/env python3
"""Apply the approved D07 oracle erratum and deterministically rebuild artifacts.

The script is intentionally one-shot and fail-closed: it accepts only the
previously frozen file hashes and exact old leaf values recorded in the 2026-08-14
decision. It does not modify contract, catalog, generator, runtime, or tests.
"""

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

EXPECTED_FILE_HASHES = {
    CONTRACT: "0b1f42c108ab6d4f5caa11a879cd2233328518e061772f74668cf1afd520fe84",
    CATALOG: "419f2a060e0d46550c0e1faaeabddd5094a12556ba7f9ba9f66d99be5b5ee4cd",
    ORACLE: "6ef89feb9d5527b54a81870af444e82fa24082571a7927467170f686e66360a8",
    REGISTRY: "01f036f2b086cb92c5c63ed755a38c1fe17ff43ff8868a6d6519aa55af29e9ca",
    GENERATOR: "1b230c374830d69c7bc37323960696f9a50ed3bba16bfa9f8996e6a64ce44a9b",
}

GRADE_CHANGES = {
    "010": ("G3", "G2"),
    "085": ("G2", "G1"),
    "093": ("G3", "G2"),
    "094": ("G3", "G2"),
    "100": ("G3", "G2"),
    "101": ("G3", "G2"),
    "102": ("G3", "G2"),
    "106": ("G3", "G2"),
}
ANCHORED_COUNTS = {"129": 2, "130": 2, "131": 3, "132": 1, "133": 2, "136": 1}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json_atomic(path: Path, value: dict) -> None:
    temp = path.with_suffix(path.suffix + ".erratum.tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


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
            "required_assertion_clause_ids": [clause["clause_id"] for clause in program],
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
    for path, expected in EXPECTED_FILE_HASHES.items():
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"precondition failed: {path} SHA-256 {actual} != {expected}")

    oracle = json.loads(ORACLE.read_text(encoding="utf-8"))
    if oracle.get("content_hash") != "e0bf81c81d96a0c476ebe34ed95fc51cf8a985bca3c931ff5807a9e06cb52ada":
        raise SystemExit("precondition failed: oracle embedded content_hash drift")
    by_id = {item["case_id"]: item for item in oracle["ordered_expectations"]}

    changed_leaves = 0
    for case_id, (old, new) in GRADE_CHANGES.items():
        leaves = by_id[case_id]["expected_leaf_set"]
        path = "units.1.grade"
        if leaves.get(path) != old:
            raise SystemExit(f"precondition failed: case {case_id} {path} != {old}")
        leaves[path] = new
        changed_leaves += 1

    priority_path = "units.1.monitoring_priority"
    leaves_085 = by_id["085"]["expected_leaf_set"]
    if leaves_085.get(priority_path) != "medium":
        raise SystemExit("precondition failed: case 085 priority != medium")
    leaves_085[priority_path] = "low"
    changed_leaves += 1

    anchored_path = "journey.risk_marker_anchored_result_count"
    for case_id, count in ANCHORED_COUNTS.items():
        leaves = by_id[case_id]["expected_leaf_set"]
        if anchored_path in leaves:
            raise SystemExit(f"precondition failed: case {case_id} already has {anchored_path}")
        leaves[anchored_path] = count
        changed_leaves += 1

    if changed_leaves != 15:
        raise SystemExit(f"internal error: changed {changed_leaves} leaves, expected 15")

    oracle["content_hash"] = g.content_hash(oracle)
    write_json_atomic(ORACLE, oracle)

    manifest = build_manifest(oracle)
    write_json_atomic(REGISTRY, manifest)
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True)

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    print(json.dumps({
        "changed_leaf_count": changed_leaves,
        "oracle_content_hash": oracle["content_hash"],
        "oracle_file_sha256": sha256(ORACLE),
        "registry_content_hash": registry["content_hash"],
        "registry_file_sha256": sha256(REGISTRY),
        "unchanged_file_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (CONTRACT, CATALOG, GENERATOR)
        },
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
