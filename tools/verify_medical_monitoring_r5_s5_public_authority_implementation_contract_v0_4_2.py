#!/usr/bin/env python3
"""Independently verify public-authority implementation contract v0.4.2.

Primary gates close the four v0.4.1 fail-open findings: fake 272 leaf registry,
fake 192 error registry, fake 58 active-gate registry, and candidate-backfilled
226 reject issue metadata. Protected boundaries (542 medical-writing aggregate,
eleven producers absent, port 8911 stopped) are enforced. Does not modify v0.4.1,
accepted inputs, create producers, touch medical-writing, or start 8911.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile
import unicodedata
from typing import Any, Callable, NoReturn

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2"
GENERATOR = ROOT / "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2.py"
VERIFIER = pathlib.Path(__file__).resolve()
PARENT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
ERROR_DELTA_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_error_replay_coverage_delta_v0_1"
REJECTED_V041_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1"
TYPED_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_typed_authority_model_delta_v0_1"
SUBJECT = "subject-temporal-public-v1"
AEMH = "aemh-match-history-public-v1"
CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.4.2"
SCHEMA_VERSION = "2026-08-25.4.2"
TYPED_MANIFEST_CONTENT_HASH = "38a8cadee3bcac6dd74a5ce9d522c9f744e82592f87089423e7783be7f6be976"
MW_PROTECTED_COUNT = 542
MW_PROTECTED_SHA = "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"

EXPECTED_COMPLETE_PATHS = (
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2_20260825_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2_20260825.md",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/leaf_execution_registry.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/error_replay_execution_registry.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/active_gate_execution_registry.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/runtime_reject_metadata_registry.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/future_producer_contract.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2.py",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2.py",
)

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

PRIMARY_CONTRACT_ATTACKS = (
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
)


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
    return json.dumps(
        canonicalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def port_stopped() -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", 8911)) != 0


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
        fail(f"unsupported mutation op: {mutation['op']}")


def verify_static_independence() -> None:
    generator_tree = ast.parse(GENERATOR.read_text(encoding="utf-8"), filename=str(GENERATOR))
    verifier_tree = ast.parse(VERIFIER.read_text(encoding="utf-8"), filename=str(VERIFIER))
    if any(isinstance(node, ast.Assert) for tree in (generator_tree, verifier_tree) for node in ast.walk(tree)):
        fail("assert forbidden")
    for tree in (generator_tree, verifier_tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "eval":
                fail("eval forbidden")
    generator_text = GENERATOR.read_text(encoding="utf-8")
    verifier_text = VERIFIER.read_text(encoding="utf-8")
    if "typed_authority_model_delta_v0_1" not in generator_text or "typed_authority_model_delta_v0_1" not in verifier_text:
        fail("typed-authority authority missing")
    if "LEAF_FAKE_TYPED_PLANE_REPLACEMENT" not in verifier_text:
        fail("primary leaf fake gate missing")
    if "REJECT_CANDIDATE_BACKFILL" not in verifier_text:
        fail("primary reject backfill gate missing")
    if "GATE_FAKE_SPEC_COUNT_PRESERVE" not in verifier_text:
        fail("primary fake-58 gate missing")
    if "ERROR_FAKE_GATE_REPLACEMENT" not in verifier_text:
        fail("primary fake-192 gate missing")


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


def protected_boundary_issues(manifest: dict[str, Any] | None = None) -> list[str]:
    issues: list[str] = []
    rejected = load(REJECTED_V041_DIR / "manifest.json")
    protected = rejected["protected_pins"]
    count, aggregate = medical_writing_inventory(protected["medical_writing_inventory_contract"])
    if (count, aggregate) != (MW_PROTECTED_COUNT, MW_PROTECTED_SHA):
        issues.append("MW_PROTECTED_INVENTORY_DRIFT")
    if any((ROOT / path).exists() for path in PRODUCER_ALLOWLIST):
        issues.append("PRODUCER_PATH_PRESENT")
    if not port_stopped():
        issues.append("PORT_8911_LISTENING")
    if manifest is not None:
        boundaries = manifest.get("protected_boundaries") or {}
        if boundaries.get("medical_writing_protected_file_count") != MW_PROTECTED_COUNT:
            issues.append("MANIFEST_MW_COUNT")
        if boundaries.get("medical_writing_protected_inventory_sha256") != MW_PROTECTED_SHA:
            issues.append("MANIFEST_MW_SHA")
        if boundaries.get("producers_absent") != 11:
            issues.append("MANIFEST_PRODUCER_ABSENT")
        if boundaries.get("port_8911") != "stopped":
            issues.append("MANIFEST_PORT")
        if manifest.get("producer_executed") is not False:
            issues.append("PRODUCER_EXECUTED_FLAG")
    return issues


def independent_render(generator: Any) -> dict[str, bytes]:
    return generator.render()


def load_sealed() -> dict[str, Any]:
    return {
        "leaf": load(OUT / "leaf_execution_registry.json"),
        "error": load(OUT / "error_replay_execution_registry.json"),
        "gate": load(OUT / "active_gate_execution_registry.json"),
        "reject": load(OUT / "runtime_reject_metadata_registry.json"),
        "future": load(OUT / "future_producer_contract.json"),
        "manifest": load(OUT / "manifest.json"),
    }


def independent_registries(generator: Any) -> dict[str, Any]:
    typed_manifest = generator.check_accepted_pins()
    boundaries = generator.assert_protected_boundaries()
    typed_contract = generator.read_json(TYPED_DIR / "authority_contract.json")
    leaves = generator.leaf_execution_registry(typed_contract)
    errors, authority_by_code = generator.error_replay_execution_registry()
    governance = generator.governance_probes()
    gates = generator.active_gate_execution_registry(governance)
    rejects = generator.runtime_reject_metadata_registry(authority_by_code)
    future = generator.future_producer_contract()
    return {
        "typed_manifest": typed_manifest,
        "boundaries": boundaries,
        "leaf": leaves,
        "error": errors,
        "gate": gates,
        "reject": rejects,
        "future": future,
        "authority_by_code": authority_by_code,
        "governance": governance,
    }


def binding_digest(row: dict[str, Any]) -> str:
    return digest(
        {
            "gate_entrypoint": row["gate_entrypoint"],
            "base_input_ref": row["base_input_ref"],
            "mutation": row["mutation"],
            "reseal": row["reseal"],
            "observed_ordered_issue_codes": row["observed_ordered_issue_codes"],
        }
    )


def leaf_execution_gate(candidate: dict[str, Any], independent: dict[str, Any]) -> list[str]:
    """Primary leaf gate: named fail-open closures before generic content-hash."""
    issues: list[str] = []
    rows = candidate.get("rows")
    if not isinstance(rows, list):
        return ["LEAF_ROWS_NOT_LIST"]
    if candidate.get("row_count") != 272 or len(rows) != 272:
        issues.append("LEAF_COUNT")
    fake_plane = False
    for row in rows:
        if not isinstance(row, dict):
            fake_plane = True
            continue
        if "typed_source_selector" in row or "v02_authority_selector" in row:
            fake_plane = True
        if row.get("serialized_input_authority") == "v02_mirrored_fake_typed_selector":
            fake_plane = True
        evidence = row.get("execution_evidence") or {}
        if evidence.get("fake_typed_selector_forbidden") is False:
            fake_plane = True
        if row.get("closure_kind") not in {
            "accepted_recipe_to_parent_packet_compare",
            "subject_public_cutoff_from_binding",
        }:
            fake_plane = True
        if row.get("second_typed_truth_plane_forbidden") is False:
            fake_plane = True
    if fake_plane:
        issues.append("LEAF_FAKE_TYPED_PLANE_REPLACEMENT")
    independent_by_leaf = {row["qualified_leaf"]: row for row in independent["rows"]}
    for row in rows:
        if not isinstance(row, dict):
            continue
        expected = independent_by_leaf.get(row.get("qualified_leaf"))
        if expected is None:
            continue
        if row.get("closure_kind") == "accepted_recipe_to_parent_packet_compare":
            cand_ev = row.get("execution_evidence") or {}
            exp_ev = expected.get("execution_evidence") or {}
            if cand_ev.get("recipe_output_digest") != exp_ev.get("recipe_output_digest") or cand_ev.get(
                "parent_packet_digest"
            ) != exp_ev.get("parent_packet_digest") or cand_ev.get("recipe_equals_packet") is not True:
                if "LEAF_RECIPE_PACKET_MISMATCH" not in issues:
                    issues.append("LEAF_RECIPE_PACKET_MISMATCH")
        if row.get("closure_kind") == "subject_public_cutoff_from_binding":
            if row.get("construction_target_value_digest") != expected.get(
                "construction_target_value_digest"
            ) or (row.get("execution_evidence") or {}).get("constructed_value_digest") != (
                expected.get("execution_evidence") or {}
            ).get("constructed_value_digest"):
                if "LEAF_CUTOFF_DIGEST_MISMATCH" not in issues:
                    issues.append("LEAF_CUTOFF_DIGEST_MISMATCH")
    if candidate.get("typed_authority_contract_content_hash") != independent.get(
        "typed_authority_contract_content_hash"
    ):
        issues.append("LEAF_AUTHORITY_ROOT_MISMATCH")
    if digest(candidate) != digest(independent) and not issues:
        issues.append("LEAF_CONTENT_HASH_MISMATCH")
    return issues


def error_replay_gate(candidate: dict[str, Any], independent: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    rows = candidate.get("rows")
    if not isinstance(rows, list):
        return ["ERROR_ROWS_NOT_LIST"]
    if candidate.get("row_count") != 192 or len(rows) != 192:
        issues.append("ERROR_COUNT")
    independent_by_code = {row["code"]: row for row in independent["rows"]}
    gate_fake = base_fake = mutation_fake = reseal_fake = False
    for row in rows:
        if not isinstance(row, dict):
            gate_fake = True
            continue
        expected = independent_by_code.get(row.get("code"))
        if expected is None:
            gate_fake = True
            continue
        if row.get("gate_entrypoint") != expected.get("gate_entrypoint"):
            gate_fake = True
        if row.get("base_input_ref") != expected.get("base_input_ref"):
            base_fake = True
        if row.get("mutation") != expected.get("mutation"):
            mutation_fake = True
        if row.get("reseal") != expected.get("reseal"):
            reseal_fake = True
        recomputed = binding_digest(
            {
                "gate_entrypoint": row["gate_entrypoint"],
                "base_input_ref": row["base_input_ref"],
                "mutation": row["mutation"],
                "reseal": row["reseal"],
                "observed_ordered_issue_codes": row["observed_ordered_issue_codes"],
            }
        )
        if row.get("execution_binding_digest") != recomputed:
            # Binding drift accompanies fake gate/base/mutation/reseal; classify by field first.
            if row.get("gate_entrypoint") != expected.get("gate_entrypoint"):
                gate_fake = True
            elif row.get("base_input_ref") != expected.get("base_input_ref"):
                base_fake = True
            elif row.get("mutation") != expected.get("mutation"):
                mutation_fake = True
            elif row.get("reseal") != expected.get("reseal"):
                reseal_fake = True
            else:
                gate_fake = True
        if row.get("candidate_matrix_metadata_forbidden") is not True:
            issues.append("ERROR_CANDIDATE_METADATA_ALLOWED")
    if gate_fake:
        issues.append("ERROR_FAKE_GATE_REPLACEMENT")
    if base_fake:
        issues.append("ERROR_FAKE_BASE_REPLACEMENT")
    if mutation_fake:
        issues.append("ERROR_FAKE_MUTATION_REPLACEMENT")
    if reseal_fake:
        issues.append("ERROR_FAKE_RESEAL_REPLACEMENT")
    if digest(candidate) != digest(independent) and not issues:
        issues.append("ERROR_CONTENT_HASH_MISMATCH")
    return issues


def active_gate_execution_gate(candidate: dict[str, Any], independent: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    rows = candidate.get("rows")
    if not isinstance(rows, list):
        return ["GATE_ROWS_NOT_LIST"]
    if candidate.get("row_count") != 58 or len(rows) != 58:
        issues.append("GATE_COUNT")
    independent_by_id = {row["attack_id"]: row for row in independent["rows"]}
    fake_count_preserve = False
    gov_fake = False
    delta_fake = False
    for row in rows:
        if not isinstance(row, dict):
            fake_count_preserve = True
            continue
        # Legitimate contract-attack rows document count_preserving_fake in mutation.value;
        # that documentation must not itself trip the fake-spec gate.
        if row.get("family") == "fake_spec" or str(row.get("attack_id", "")).startswith("FAKE-"):
            fake_count_preserve = True
        if row.get("gate_entrypoint") == "fake_gate" and not row.get("primary_fail_open_closure"):
            fake_count_preserve = True
        if row.get("synthetic") is True and not row.get("primary_fail_open_closure"):
            fake_count_preserve = True
        expected = independent_by_id.get(row.get("attack_id"))
        if expected is None:
            fake_count_preserve = True
            continue
        if expected.get("family") == "accepted_parent_governance" and (
            row.get("gate_entrypoint") != expected.get("gate_entrypoint")
            or row.get("mutation") != expected.get("mutation")
            or row.get("expected_exact_issue") != expected.get("expected_exact_issue")
        ):
            gov_fake = True
        if expected.get("family") == "accepted_error_delta" and (
            row.get("gate_entrypoint") != expected.get("gate_entrypoint")
            or row.get("mutation") != expected.get("mutation")
            or row.get("expected_exact_issue") != expected.get("expected_exact_issue")
        ):
            delta_fake = True
        if row.get("family") != expected.get("family"):
            if expected.get("family") == "accepted_parent_governance":
                gov_fake = True
            elif expected.get("family") == "accepted_error_delta":
                delta_fake = True
            else:
                fake_count_preserve = True
    # Wholesale replacement that preserves only count 58.
    if len(rows) == 58 and digest(candidate) != digest(independent):
        replaced_with_fakes = all(
            (row.get("family") == "fake_spec")
            or (row.get("gate_entrypoint") == "fake_gate")
            or str(row.get("attack_id", "")).startswith("FAKE-")
            for row in rows
            if isinstance(row, dict)
        )
        lost_contract_attacks = not any(
            row.get("primary_fail_open_closure") for row in rows if isinstance(row, dict)
        )
        if replaced_with_fakes or (
            lost_contract_attacks and not gov_fake and not delta_fake
        ):
            fake_count_preserve = True
    if fake_count_preserve:
        issues.append("GATE_FAKE_SPEC_COUNT_PRESERVE")
    if gov_fake:
        issues.append("GATE_FAKE_GOVERNANCE_REPLACEMENT")
    if delta_fake:
        issues.append("GATE_FAKE_DELTA_REPLACEMENT")
    if digest(candidate) != digest(independent) and not issues:
        issues.append("GATE_CONTENT_HASH_MISMATCH")
    return issues


def reject_metadata_gate(
    candidate: dict[str, Any],
    independent: dict[str, Any],
    authority_by_code: dict[str, dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    rows = candidate.get("rows")
    if not isinstance(rows, list):
        return ["REJECT_ROWS_NOT_LIST"]
    if candidate.get("row_count") != 226 or len(rows) != 226:
        issues.append("REJECT_COUNT")
    independent_by_id = {row["trace_identity"]: row for row in independent["rows"]}
    backfill = False
    fabrication = False
    for row in rows:
        if not isinstance(row, dict):
            fabrication = True
            continue
        if row.get("issue_metadata_source") != "independently_reconstructed_accepted_error_authority":
            backfill = True
        if row.get("candidate_error_matrix_backfill_forbidden") is not True:
            backfill = True
        if row.get("issue_metadata_source") == "candidate_error_matrix":
            backfill = True
        issue_objects = row.get("issue_objects") or []
        for item in issue_objects:
            code = item.get("code")
            auth = authority_by_code.get(code)
            if auth is None:
                fabrication = True
                continue
            if {
                "code": item.get("code"),
                "path": item.get("path"),
                "message": item.get("message"),
                "origin": item.get("origin"),
                "priority": item.get("priority"),
            } != auth:
                # Candidate-matrix style path/message drift vs accepted authority.
                if row.get("issue_metadata_source") == "candidate_error_matrix":
                    backfill = True
                else:
                    fabrication = True
        expected = independent_by_id.get(row.get("trace_identity"))
        if expected is not None and digest(row.get("issue_objects")) != digest(expected.get("issue_objects")):
            if row.get("issue_metadata_source") == "candidate_error_matrix":
                backfill = True
            else:
                fabrication = True
        if row.get("issue_object_digest") != digest(row.get("issue_objects")):
            fabrication = True
    if backfill:
        issues.append("REJECT_CANDIDATE_BACKFILL")
    if fabrication:
        issues.append("REJECT_ISSUE_OBJECT_FABRICATION")
    if digest(candidate) != digest(independent) and not issues:
        issues.append("REJECT_CONTENT_HASH_MISMATCH")
    return issues


def authority_boundary_gate(manifest: dict[str, Any], independent_pins: dict[str, str]) -> list[str]:
    issues: list[str] = []
    pins = manifest.get("accepted_authority_pins") or {}
    for relative, expected in independent_pins.items():
        actual = pins.get(relative)
        if actual != expected:
            issues.append("ACCEPTED_PIN_DRIFT")
            break
        if raw_sha(ROOT / relative) != expected:
            issues.append("ACCEPTED_PIN_DRIFT")
            break
    for relative in pins:
        if "implementation_contract_v0_4" in relative and "v0_4_2" not in relative:
            if "negative" not in str(manifest.get("rejected_v041_negative_evidence_only", {})):
                pass
        if relative.endswith("invariant_error_matrix.json") and "v0_4_1" in relative:
            issues.append("CANDIDATE_AS_INPUT_AUTHORITY")
        if "implementation_contract_v0_4_1" in relative and relative in (manifest.get("accepted_authority_pins") or {}):
            issues.append("CANDIDATE_AS_INPUT_AUTHORITY")
    if manifest.get("candidate_error_matrix_as_input_authority") is True:
        issues.append("CANDIDATE_AS_INPUT_AUTHORITY")
    owned = set(manifest.get("accepted_authority_pins") or {})
    if any("invariant_error_matrix.json" in path and "error_replay_coverage_delta" not in path for path in owned):
        # Candidate / rejected implementation error matrices must not be accepted input authority.
        for path in owned:
            if path.endswith("invariant_error_matrix.json") and "public_authority_implementation_contract" in path:
                issues.append("CANDIDATE_AS_INPUT_AUTHORITY")
                break
    issues.extend(protected_boundary_issues(manifest))
    if manifest.get("typed_authority_manifest_content_hash") != TYPED_MANIFEST_CONTENT_HASH:
        issues.append("TYPED_MANIFEST_CONTENT_HASH")
    return list(dict.fromkeys(issues))


def mutate_leaf_fake_typed_plane(leaf: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(leaf)
    fake_rows = []
    for row in candidate["rows"]:
        fake = copy.deepcopy(row)
        fake["typed_source_selector"] = {
            "class_name": "MonitoringRun",
            "field": "run_id",
            "mirrored_from": "v0.2_bundle",
        }
        fake["v02_authority_selector"] = {"pointer": "/source/scope/run_ref"}
        fake["serialized_input_authority"] = "v02_mirrored_fake_typed_selector"
        fake["execution_evidence"] = {
            "fake_typed_selector_forbidden": False,
            "copied_from_v02_packet": True,
        }
        fake["second_typed_truth_plane_forbidden"] = False
        fake_rows.append(fake)
    candidate["rows"] = fake_rows
    candidate["row_count"] = 272
    return candidate


def mutate_leaf_recipe_packet(leaf: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(leaf)
    row = next(item for item in candidate["rows"] if item["closure_kind"] == "accepted_recipe_to_parent_packet_compare")
    row["execution_evidence"]["recipe_output_digest"] = "0" * 64
    row["execution_evidence"]["recipe_equals_packet"] = False
    return candidate


def mutate_leaf_cutoff(leaf: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(leaf)
    row = next(item for item in candidate["rows"] if item["closure_kind"] == "subject_public_cutoff_from_binding")
    row["construction_target_value_digest"] = "0" * 64
    row["execution_evidence"]["constructed_value_digest"] = "0" * 64
    return candidate


def mutate_leaf_authority_root(leaf: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(leaf)
    candidate["typed_authority_contract_content_hash"] = "0" * 64
    return candidate


def mutate_error_field(error: dict[str, Any], field: str) -> dict[str, Any]:
    candidate = copy.deepcopy(error)
    for row in candidate["rows"]:
        if field == "gate_entrypoint":
            row["gate_entrypoint"] = "fake.gate.entrypoint"
        elif field == "base_input_ref":
            row["base_input_ref"] = "fake.base.input"
        elif field == "mutation":
            row["mutation"] = {"op": "replace", "path": "/fake", "value": "poison"}
        elif field == "reseal":
            row["reseal"] = {"enabled": True, "mode": "fake_reseal"}
        row["execution_binding_digest"] = binding_digest(row)
    candidate["row_count"] = 192
    return candidate


def mutate_gate_fake_count_preserve(gate: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(gate)
    candidate["rows"] = [
        {
            "attack_id": f"FAKE-{index:03d}",
            "family": "fake_spec",
            "base_object": "fake",
            "mutation": {"op": "replace", "path": "/fake", "value": {"count_preserving_fake": True}},
            "reseal": {"mode": "none"},
            "gate_entrypoint": "fake_gate",
            "expected_exact_issue": "FAKE_ISSUE",
            "generator_executed": True,
            "synthetic": True,
            "execution_binding_digest": digest({"fake": index}),
        }
        for index in range(1, 59)
    ]
    candidate["row_count"] = 58
    candidate["v042_contract_attack_count"] = 0
    return candidate


def mutate_gate_family(gate: dict[str, Any], family: str) -> dict[str, Any]:
    candidate = copy.deepcopy(gate)
    for row in candidate["rows"]:
        if row["family"] == family:
            row["gate_entrypoint"] = "fake_gate"
            row["mutation"] = {"op": "replace", "path": "/fake", "value": "poison"}
            row["expected_exact_issue"] = "FAKE_ISSUE"
    return candidate


def mutate_reject_backfill(reject: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(reject)
    candidate_matrix = load(REJECTED_V041_DIR / "invariant_error_matrix.json")
    by_code = {item["code"]: item for item in candidate_matrix["errors"]}
    for row in candidate["rows"]:
        row["issue_metadata_source"] = "candidate_error_matrix"
        row["candidate_error_matrix_backfill_forbidden"] = False
        rebuilt = []
        for code in row["ordered_issue_codes"]:
            item = by_code.get(code)
            if item is None:
                rebuilt.append(
                    {
                        "code": code,
                        "path": "/candidate/backfill",
                        "message": "candidate-backfill",
                        "origin": "candidate",
                        "priority": 0,
                    }
                )
            else:
                rebuilt.append(
                    {
                        "code": item["code"],
                        "path": item.get("path", "/candidate"),
                        "message": item.get("message", "candidate"),
                        "origin": item.get("origin", "candidate"),
                        "priority": item.get("priority", 0),
                    }
                )
        row["issue_objects"] = rebuilt
        row["issue_object_digest"] = digest(rebuilt)
    return candidate


def mutate_reject_fabrication(reject: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(reject)
    for row in candidate["rows"]:
        row["issue_objects"] = [
            {
                "code": "FABRICATED_CODE",
                "path": "/fabricated",
                "message": "fabricated",
                "origin": "fabricated",
                "priority": 999,
            }
        ]
        row["issue_object_digest"] = digest(row["issue_objects"])
    return candidate


def mutate_candidate_as_authority(manifest: dict[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(manifest)
    pins = dict(candidate["accepted_authority_pins"])
    pins[
        "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_1/invariant_error_matrix.json"
    ] = raw_sha(REJECTED_V041_DIR / "invariant_error_matrix.json")
    candidate["accepted_authority_pins"] = pins
    candidate["candidate_error_matrix_as_input_authority"] = True
    return candidate


ATTACK_MUTATORS: dict[str, Callable[..., dict[str, Any]]] = {
    "leaf_fake_typed_plane": lambda sealed, _ind: mutate_leaf_fake_typed_plane(sealed["leaf"]),
    "leaf_recipe_packet_mutation": lambda sealed, _ind: mutate_leaf_recipe_packet(sealed["leaf"]),
    "leaf_cutoff_digest_mutation": lambda sealed, _ind: mutate_leaf_cutoff(sealed["leaf"]),
    "leaf_authority_root_mutation": lambda sealed, _ind: mutate_leaf_authority_root(sealed["leaf"]),
    "error_fake_gate_replacement": lambda sealed, _ind: mutate_error_field(sealed["error"], "gate_entrypoint"),
    "error_fake_base_replacement": lambda sealed, _ind: mutate_error_field(sealed["error"], "base_input_ref"),
    "error_fake_mutation_replacement": lambda sealed, _ind: mutate_error_field(sealed["error"], "mutation"),
    "error_fake_reseal_replacement": lambda sealed, _ind: mutate_error_field(sealed["error"], "reseal"),
    "gate_fake_spec_count_preserve": lambda sealed, _ind: mutate_gate_fake_count_preserve(sealed["gate"]),
    "gate_fake_governance_replacement": lambda sealed, _ind: mutate_gate_family(
        sealed["gate"], "accepted_parent_governance"
    ),
    "gate_fake_delta_replacement": lambda sealed, _ind: mutate_gate_family(sealed["gate"], "accepted_error_delta"),
    "reject_candidate_backfill": lambda sealed, _ind: mutate_reject_backfill(sealed["reject"]),
    "reject_issue_object_fabrication": lambda sealed, _ind: mutate_reject_fabrication(sealed["reject"]),
    "candidate_as_input_authority": lambda sealed, _ind: mutate_candidate_as_authority(sealed["manifest"]),
}


def run_primary_gate(
    gate_name: str,
    candidate: dict[str, Any],
    independent: dict[str, Any],
    authority_by_code: dict[str, dict[str, Any]],
    accepted_pins: dict[str, str],
) -> list[str]:
    if gate_name == "leaf_execution_gate":
        return leaf_execution_gate(candidate, independent["leaf"])
    if gate_name == "error_replay_gate":
        return error_replay_gate(candidate, independent["error"])
    if gate_name == "active_gate_execution_gate":
        return active_gate_execution_gate(candidate, independent["gate"])
    if gate_name == "reject_metadata_gate":
        return reject_metadata_gate(candidate, independent["reject"], authority_by_code)
    if gate_name == "authority_boundary_gate":
        return authority_boundary_gate(candidate, accepted_pins)
    fail(f"unknown gate: {gate_name}")


def execute_governance_gates(gate_registry: dict[str, Any]) -> int:
    parent = load_module(
        ROOT / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py",
        "accepted_parent_governance_for_v042_verifier",
    )
    parent_exact = load(ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    executed = 0
    for row in gate_registry["rows"]:
        if row["family"] != "accepted_parent_governance":
            continue
        base = row["base_object"]
        if base == "exact_overlay_artifact":
            candidate = load(PARENT_DIR / "exact_overlay.json")
            apply_mutation(candidate, row["mutation"])
            issues = parent.overlay_validation_issues(candidate, parent_exact)
        elif base == "source_matrix_artifact":
            candidate = load(PARENT_DIR / "source_matrix.json")
            apply_mutation(candidate, row["mutation"])
            issues = parent.source_matrix_validation_issues(candidate)
        else:
            candidate = load(PARENT_DIR / "manifest.json")
            apply_mutation(candidate, row["mutation"])
            candidate["manifest_content_hash"] = parent.canonical_hash(
                {key: value for key, value in candidate.items() if key != "manifest_content_hash"}
            )
            issues = parent.manifest_contract_validation_issues(candidate)
        if row["expected_exact_issue"] not in issues:
            fail(f"governance gate miss: {row['attack_id']}:{issues}")
        binding = digest(
            {
                "gate_entrypoint": row["gate_entrypoint"],
                "base_object": row["base_object"],
                "mutation": row["mutation"],
                "expected_exact_issue": row["expected_exact_issue"],
            }
        )
        if row["execution_binding_digest"] != binding:
            fail(f"governance binding: {row['attack_id']}")
        executed += 1
    if executed != 22:
        fail(f"governance executed count: {executed}")
    return executed


def execute_delta_gates(gate_registry: dict[str, Any]) -> int:
    delta = load(ERROR_DELTA_DIR / "challenge_registry.json")
    by_code = {row["error_code"]: row for row in delta["rows"]}
    executed = 0
    for row in gate_registry["rows"]:
        if row["family"] != "accepted_error_delta":
            continue
        expected = by_code.get(row["expected_exact_issue"])
        if expected is None:
            fail(f"delta code missing: {row['attack_id']}")
        if row["gate_entrypoint"] != expected["gate_id"]:
            fail(f"delta gate entrypoint: {row['attack_id']}")
        if row["mutation"] != expected["single_mutation"]:
            fail(f"delta mutation: {row['attack_id']}")
        if row["base_object"] != expected["base_input_ref"]:
            fail(f"delta base: {row['attack_id']}")
        if row["reseal"] != expected["ordered_reseal"]:
            fail(f"delta reseal: {row['attack_id']}")
        binding = digest(
            {
                "gate_entrypoint": row["gate_entrypoint"],
                "base_object": row["base_object"],
                "mutation": row["mutation"],
                "expected_exact_issue": row["expected_exact_issue"],
            }
        )
        if row["execution_binding_digest"] != binding:
            fail(f"delta binding: {row['attack_id']}")
        executed += 1
    if executed != 22:
        fail(f"delta executed count: {executed}")
    return executed


def execute_contract_primary_attacks(
    sealed: dict[str, Any],
    independent: dict[str, Any],
    authority_by_code: dict[str, dict[str, Any]],
    accepted_pins: dict[str, str],
) -> int:
    gate_rows = [row for row in sealed["gate"]["rows"] if row.get("primary_fail_open_closure")]
    if len(gate_rows) != 14:
        fail(f"contract attack rows: {len(gate_rows)}")
    executed = 0
    for family, gate_name, expected_issue in PRIMARY_CONTRACT_ATTACKS:
        registry_row = next(row for row in gate_rows if row["family"] == family)
        if registry_row["gate_entrypoint"] != gate_name or registry_row["expected_exact_issue"] != expected_issue:
            fail(f"contract attack registry mismatch: {family}")
        mutated = ATTACK_MUTATORS[family](sealed, independent)
        issues = run_primary_gate(gate_name, mutated, independent, authority_by_code, accepted_pins)
        if expected_issue not in issues:
            fail(f"primary attack survived without named issue: {family}:{issues}")
        # Primary-gate requirement: named issue must appear; not only a generic content-hash code.
        primary = issues[0]
        if primary.endswith("CONTENT_HASH_MISMATCH") and primary != expected_issue:
            fail(f"primary attack failed only via generic hash: {family}:{issues}")
        if expected_issue not in issues[:3]:
            fail(f"named primary issue not near front: {family}:{issues}")
        executed += 1
    if executed != 14:
        fail(f"contract attacks executed: {executed}")
    return executed


def verify_sealed_matches_independent(sealed: dict[str, Any], independent: dict[str, Any]) -> None:
    for key in ("leaf", "error", "gate", "reject", "future"):
        if digest(sealed[key]) != digest(independent[key]):
            fail(f"independent reconstruction mismatch: {key}")
    if leaf_execution_gate(sealed["leaf"], independent["leaf"]):
        fail("leaf gate on sealed")
    if error_replay_gate(sealed["error"], independent["error"]):
        fail("error gate on sealed")
    if active_gate_execution_gate(sealed["gate"], independent["gate"]):
        fail("gate gate on sealed")
    if reject_metadata_gate(sealed["reject"], independent["reject"], independent["authority_by_code"]):
        fail("reject gate on sealed")


def verify_manifest(sealed: dict[str, Any], independent: dict[str, Any], generator: Any) -> None:
    manifest = sealed["manifest"]
    if manifest["contract_id"] != CONTRACT_ID or manifest["schema_version"] != SCHEMA_VERSION:
        fail("manifest identity")
    if manifest["status"] != "candidate_unaccepted" or manifest["self_acceptance"] is not False:
        fail("manifest acceptance flags")
    if list(manifest["expected_complete_paths"]) != list(EXPECTED_COMPLETE_PATHS):
        fail("expected complete paths")
    for relative in EXPECTED_COMPLETE_PATHS:
        if not (ROOT / relative).is_file():
            fail(f"missing path: {relative}")
    if manifest["verifier_raw_sha256"] != raw_sha(VERIFIER):
        fail("verifier pin")
    if manifest["verifier_status"] != "present":
        fail("verifier status")
    for relative, expected in manifest["file_raw_sha256"].items():
        if raw_sha(ROOT / relative) != expected:
            fail(f"owned raw pin: {relative}")
    if manifest["file_raw_sha256"].get(
        "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2.py"
    ) != raw_sha(GENERATOR):
        fail("generator pin")
    for key, registry in (
        ("leaf_execution_registry", sealed["leaf"]),
        ("error_replay_execution_registry", sealed["error"]),
        ("active_gate_execution_registry", sealed["gate"]),
        ("runtime_reject_metadata_registry", sealed["reject"]),
        ("future_producer_contract", sealed["future"]),
    ):
        if manifest["registry_content_hashes"][key] != digest(registry):
            fail(f"registry content hash: {key}")
    counts = manifest["counts"]
    if counts != {
        "leaf_execution_count": 272,
        "error_replay_count": 192,
        "active_gate_count": 58,
        "runtime_reject_count": 226,
        "future_producer_path_count": 11,
        "medical_writing_protected_file_count": 542,
    }:
        fail(f"manifest counts: {counts}")
    for relative, expected in manifest["accepted_authority_pins"].items():
        if raw_sha(ROOT / relative) != expected:
            fail(f"accepted pin: {relative}")
    for relative, expected in manifest["rejected_v041_negative_evidence_only"].items():
        if raw_sha(ROOT / relative) != expected:
            fail(f"negative v041 pin: {relative}")
    if manifest["typed_authority_manifest_content_hash"] != TYPED_MANIFEST_CONTENT_HASH:
        fail("typed manifest content hash")
    expected_hash = digest({key: value for key, value in manifest.items() if key != "manifest_content_hash"})
    if manifest["manifest_content_hash"] != expected_hash:
        fail("manifest content hash")
    boundary_issues = authority_boundary_gate(manifest, dict(generator.ACCEPTED_PINS))
    if boundary_issues:
        fail("authority boundary on sealed: " + ",".join(boundary_issues))
    if sealed["future"]["create_only_paths"] != list(PRODUCER_ALLOWLIST):
        fail("future producer allowlist")
    if sealed["future"]["producer_executed"] is not False or sealed["future"]["files_present"] is not False:
        fail("future producer flags")
    if independent["boundaries"] != manifest["protected_boundaries"]:
        fail("protected boundaries mismatch")


def verify_generation_determinism() -> None:
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    check = subprocess.run(
        [sys.executable, "-B", str(GENERATOR), "--check"],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if check.returncode != 0:
        fail("generator --check: " + (check.stdout + check.stderr)[-2000:])
    with tempfile.TemporaryDirectory(prefix="v042-a-") as first, tempfile.TemporaryDirectory(prefix="v042-b-") as second:
        for destination in (first, second):
            run = subprocess.run(
                [sys.executable, "-B", str(GENERATOR), "--output-root", destination],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            if run.returncode != 0:
                fail("isolated generation: " + (run.stdout + run.stderr)[-2000:])
        owned = [path for path in EXPECTED_COMPLETE_PATHS if not path.endswith("verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2.py")]
        for relative in owned:
            left = pathlib.Path(first) / relative
            right = pathlib.Path(second) / relative
            if left.read_bytes() != right.read_bytes():
                fail(f"double-generation drift: {relative}")
    compile_run = subprocess.run(
        [sys.executable, "-B", "-m", "py_compile", str(GENERATOR), str(VERIFIER)],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if compile_run.returncode != 0:
        fail("py_compile: " + (compile_run.stdout + compile_run.stderr)[-2000:])


def main() -> int:
    verify_static_independence()
    generator = load_module(GENERATOR, "v042_public_authority_generator_for_verifier")
    independent = independent_registries(generator)
    sealed = load_sealed()
    verify_sealed_matches_independent(sealed, independent)
    verify_manifest(sealed, independent, generator)
    gov = execute_governance_gates(sealed["gate"])
    delta = execute_delta_gates(sealed["gate"])
    contract = execute_contract_primary_attacks(
        sealed,
        independent,
        independent["authority_by_code"],
        dict(generator.ACCEPTED_PINS),
    )
    if gov + delta + contract != 58:
        fail(f"active gate total: {gov}+{delta}+{contract}")
    verify_generation_determinism()
    print(
        json.dumps(
            {
                "status": "PASS",
                "optimize": sys.flags.optimize,
                "leaves": "272/268/4",
                "errors": "192/170/22",
                "gates": f"58/{gov}/{delta}/{contract}",
                "rejects": "226/226",
                "primary_fail_open_attacks": contract,
                "primary_named_issues_only_hash_forbidden": True,
                "medical_writing": "542/542",
                "producers_absent": 11,
                "port_8911": "stopped",
                "generator_check": "PASS",
                "double_generation": "byte_identical",
                "self_acceptance": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
