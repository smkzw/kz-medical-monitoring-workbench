"""Verify the frozen R5-S5 public-authority implementation contract.

The verifier is contract-only and fail-closed.  It replays the accepted parent
contract verifier, verifies the exact implementation-contract snapshot, and
proves producer/runtime/test/evidence surfaces remain absent.
"""

from __future__ import annotations

import argparse
import ast
import copy
import functools
import hashlib
import importlib.util
import json
import os
import re
import shlex
import socket
import subprocess
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from types import ModuleType
from typing import Any, Optional, Union

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT
    / "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py"
)
VERIFIER_PATH = Path(__file__).resolve()
ARTIFACT_DIR = (
    ROOT
    / "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1"
)
PUBLIC_ARTIFACT_DIR = (
    ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
)
PARENT_VERIFIER_PATH = (
    ROOT
    / "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py"
)

CONTRACT_ID = "medical-monitoring-r5-s5-public-authority-implementation-contract-v0.1"
SCHEMA_VERSION = "2026-08-19.1"
AUDIENCE_CONTRACT_ID = "contract.s4.1"
SUBJECT_CONTRACT_ID = "subject-temporal-public-v1"
AEMH_CONTRACT_ID = "aemh-match-history-public-v1"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
RUFF_ACCEPTANCE_COMMAND = (
    "/Users/smkzw/.local/bin/uvx --offline ruff check --no-cache "
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py "
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py"
)

EXACT_PATHS = {
    "context/medical_monitoring_r5_s5_public_authority_implementation_contract_20260819_context.md",
    "reviews/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1_20260819.md",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/public_api.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/source_join_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/invariant_error_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/test_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py",
    "tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py",
}

PRODUCER_ALLOWLIST = {
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
}

S5_RUNTIME_LOCKED_PATHS = {
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

EXPECTED_MANIFEST_KEYS = {
    "schema",
    "contract_id",
    "schema_version",
    "audience_contract_id",
    "exact_implementation_contract_paths",
    "artifact_raw_sha256",
    "manifest_hash_recipe",
    "accepted_public_contract_snapshot_sha256",
    "source_file_sha256",
    "protected_accepted_pins",
    "producer_create_only_allowlist",
    "s5_runtime_locked_paths",
    "producer_surface_must_be_absent_before_contract_acceptance",
    "producer_bytecode_and_cache_must_be_absent",
    "port_8911_must_be_stopped",
    "future_runtime_spec_counts",
    "acceptance_checks",
    "contract_tool_executable_policy",
    "shared_common_sha_invalidation",
    "unlock",
    "future_runtime_static_gate_spec",
    "python_assert_statements_allowed_in_contract_tools",
    "manifest_content_hash",
}

SOURCE_MODULE_PATHS = {
    "mm_r1.domain": "poc/medical_monitoring_ai_native_r1/src/mm_r1/domain.py",
    "mm_r1.ae_mh": "poc/medical_monitoring_ai_native_r1/src/mm_r1/ae_mh.py",
    "mm_r2.risk": "poc/medical_monitoring_ai_native_r2/src/mm_r2/risk.py",
    "mm_r4.contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/contracts.py",
    "mm_r4.aemh": "poc/medical_monitoring_ai_native_r4/src/mm_r4/aemh.py",
    "mm_r4.visit_schedule": "poc/medical_monitoring_ai_native_r4/src/mm_r4/visit_schedule.py",
    "mm_r4.d08_contracts": "poc/medical_monitoring_ai_native_r4/src/mm_r4/d08_contracts.py",
    "mm_r5.contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/contracts.py",
    "mm_r5.s4_contracts": "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py",
}

INHERITED_ACCEPT_CASES = {
    "R5C-109",
    "R5C-110",
    "R5C-116",
    "R5C-157",
    "R5C-158",
    "R5C-159",
    "R5C-160",
    "R5C-161",
    "R5C-162",
    "R5C-163",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_hash(value: Any) -> str:
    raw = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256_bytes(raw)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"JSON root must be object: {path.relative_to(ROOT)}")
    return value


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail(f"cannot load module: {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_no_assert_statements() -> None:
    for path in (GENERATOR_PATH, VERIFIER_PATH):
        if path.read_bytes().startswith(b"#!"):
            fail(f"contract tool shebang forbidden by execution policy: {path.name}")
        if path.stat().st_mode & 0o111:
            fail(f"contract tool must not be executable: {path.name}")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        hits = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        if hits:
            fail(f"Python assert statement forbidden: {path.name}:{hits}")


def verify_parent_contract() -> None:
    parent = load_module(PARENT_VERIFIER_PATH, "accepted_public_authority_verifier")
    result = parent.main()
    if result != 0:
        fail(f"accepted public-authority verifier failed: {result}")


def verify_generator_reproducibility(generator: ModuleType) -> None:
    bundle = generator.build_bundle()
    expected_generated = EXACT_PATHS - {
        str(GENERATOR_PATH.relative_to(ROOT)),
        str(VERIFIER_PATH.relative_to(ROOT)),
    }
    actual_generated = {str(path.relative_to(ROOT)) for path in bundle}
    if actual_generated != expected_generated:
        fail(
            "generator exact path set mismatch: "
            f"actual={sorted(actual_generated)} expected={sorted(expected_generated)}"
        )
    for path, expected in bundle.items():
        if not path.is_file():
            fail(f"generated contract file missing: {path.relative_to(ROOT)}")
        if path.read_bytes() != expected:
            fail(f"generated contract file drift: {path.relative_to(ROOT)}")


def verify_manifest() -> dict[str, Any]:
    manifest = read_json(ARTIFACT_DIR / "manifest.json")
    if set(manifest) != EXPECTED_MANIFEST_KEYS:
        fail("manifest exact keys mismatch")
    if manifest["schema"] != (
        "medical-monitoring-r5-s5-public-authority-implementation-manifest-v0.1"
    ):
        fail("manifest schema mismatch")
    if manifest["contract_id"] != CONTRACT_ID:
        fail("manifest contract id mismatch")
    if manifest["schema_version"] != SCHEMA_VERSION:
        fail("manifest schema version mismatch")
    if manifest["audience_contract_id"] != AUDIENCE_CONTRACT_ID:
        fail("manifest audience contract mismatch")
    if set(manifest["exact_implementation_contract_paths"]) != EXACT_PATHS:
        fail("manifest exact implementation-contract path set mismatch")
    if manifest["exact_implementation_contract_paths"] != sorted(EXACT_PATHS):
        fail("manifest exact path list must be sorted unique")
    core = {key: value for key, value in manifest.items() if key != "manifest_content_hash"}
    if manifest["manifest_content_hash"] != canonical_hash(core):
        fail("manifest content hash mismatch")
    if manifest["python_assert_statements_allowed_in_contract_tools"] is not False:
        fail("manifest must forbid Python assert statements")
    if set(manifest["producer_create_only_allowlist"]) != PRODUCER_ALLOWLIST:
        fail("producer create-only allowlist mismatch")
    if manifest["producer_create_only_allowlist"] != sorted(PRODUCER_ALLOWLIST):
        fail("producer allowlist must be sorted unique")
    if set(manifest["s5_runtime_locked_paths"]) != S5_RUNTIME_LOCKED_PATHS:
        fail("S5 locked path set mismatch")
    expected_artifact_files = {
        "public_api.json",
        "source_join_matrix.json",
        "invariant_error_matrix.json",
        "test_matrix.json",
        "manifest.json",
    }
    actual_artifact_files = {
        path.name for path in ARTIFACT_DIR.iterdir() if path.is_file()
    }
    if actual_artifact_files != expected_artifact_files:
        fail(
            "implementation artifact directory exact set mismatch: "
            f"{sorted(actual_artifact_files)}"
        )
    for relative, expected in manifest["artifact_raw_sha256"].items():
        if relative not in EXACT_PATHS or relative.endswith("/manifest.json"):
            fail(f"invalid artifact raw pin: {relative}")
        path = ROOT / relative
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
            fail(f"implementation artifact raw SHA mismatch: {relative}")
    expected_pinned = EXACT_PATHS - {
        "artifacts/medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1/manifest.json"
    }
    if set(manifest["artifact_raw_sha256"]) != expected_pinned:
        fail("implementation artifact raw pin set mismatch")
    return manifest


def verify_pins(manifest: Mapping[str, Any]) -> None:
    public_snapshot = manifest["accepted_public_contract_snapshot_sha256"]
    if len(public_snapshot) != 10:
        fail("accepted public contract snapshot must pin exactly 10 files")
    if len(set(public_snapshot.values())) != 10:
        fail("accepted public contract snapshot SHA values must be unique")
    for table_name in (
        "accepted_public_contract_snapshot_sha256",
        "source_file_sha256",
    ):
        table = manifest[table_name]
        for relative, expected in table.items():
            if not SHA_RE.fullmatch(expected):
                fail(f"invalid SHA pin: {table_name}:{relative}")
            path = ROOT / relative
            if not path.is_file():
                fail(f"pinned file missing: {relative}")
            actual = sha256_bytes(path.read_bytes())
            if actual != expected:
                fail(f"pinned file drift: {relative}: {actual}")
    pins = manifest["protected_accepted_pins"]
    expected_protected_keys = {
        "r5_root_init_sha256",
        "accepted_r4_r5_s4_readonly_manifest_sha256",
        "accepted_r5_v0_3_exact_contract_sha256",
        "s4_acceptance_record_sha256",
        "medical_writing_protected_inventory_sha256",
        "medical_writing_protected_file_count",
        "protected_path_sha256",
        "medical_writing_inventory_contract",
    }
    if set(pins) != expected_protected_keys:
        fail("protected pin keys mismatch")
    for relative, expected in pins["protected_path_sha256"].items():
        path = ROOT / relative
        if not path.is_file() or sha256_bytes(path.read_bytes()) != expected:
            fail(f"protected path drift: {relative}")
    aliases = {
        "r5_root_init_sha256": "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py",
        "accepted_r4_r5_s4_readonly_manifest_sha256": "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json",
        "accepted_r5_v0_3_exact_contract_sha256": "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json",
        "s4_acceptance_record_sha256": "context/medical_monitoring_r5_s4_acceptance_record_20260819.md",
    }
    for scalar, relative in aliases.items():
        if pins[scalar] != pins["protected_path_sha256"][relative]:
            fail(f"protected scalar/path alias mismatch: {scalar}")
    verify_medical_writing_inventory(pins)


def verify_medical_writing_inventory(pins: Mapping[str, Any]) -> None:
    contract = pins["medical_writing_inventory_contract"]
    expected_contract = {
        "roots": ["deploy", "frontend", "packages", "runtime", "services"],
        "relative_path_regex": "medical[-_]writing",
        "file_kind": "regular_file_following_task_scoped_symlink_resolution",
        "sort": "UTF-8 relative POSIX path byte order",
        "per_file_sha256": "lowercase sha256(file bytes)",
        "aggregate_recipe": "sha256(concat(relative_path_utf8 + NUL + lowercase_file_sha256_ascii + LF))",
        "privacy_boundary": "enumerate paths under the five protected roots; read bytes only for matched regular files",
    }
    if contract != expected_contract:
        fail("medical-writing inventory contract mismatch")
    pattern = re.compile(contract["relative_path_regex"])
    matches: list[tuple[str, Path]] = []
    for root_name in contract["roots"]:
        root = ROOT / root_name
        if not root.is_dir():
            fail(f"medical-writing protected root missing: {root_name}")
        for candidate in root.rglob("*"):
            relative = candidate.relative_to(ROOT).as_posix()
            if pattern.search(relative) and candidate.is_file():
                matches.append((relative, candidate))
    matches.sort(key=lambda item: item[0].encode("utf-8"))
    digest = hashlib.sha256()
    for relative, path in matches:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_bytes(path.read_bytes()).encode("ascii"))
        digest.update(b"\n")
    if len(matches) != 542:
        fail(f"medical-writing protected count mismatch: {len(matches)}")
    expected = "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"
    if digest.hexdigest() != expected:
        fail(f"medical-writing aggregate drift: {digest.hexdigest()}")
    if pins["medical_writing_protected_file_count"] != 542:
        fail("medical-writing pinned count mismatch")
    if pins["medical_writing_protected_inventory_sha256"] != expected:
        fail("medical-writing pinned aggregate mismatch")


def _class_fields(api: Mapping[str, Any], module: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for item in api["modules"][module]["output_classes"]:
        result[item["name"]] = [field["name"] for field in item["exact_serialized_fields"]]
        if item["decorator"] != "dataclasses.dataclass(frozen=True)":
            fail(f"output dataclass not frozen: {item['name']}")
        if item["extra_serialized_fields_forbidden"] is not True:
            fail(f"output exact-leaf rule missing: {item['name']}")
    return result


def _input_class_specs(api: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        item["name"]: item
        for module in api["modules"].values()
        for item in module["input_classes"]
    }


def _controlled_record_validation_issues(api: Mapping[str, Any]) -> list[str]:
    inputs = _input_class_specs(api)
    expected_decision_values = {
        "event_kind": [
            "reminder_created",
            "match_decided",
            "withdrawn",
            "reappeared",
        ],
        "match_state": ["exact", "ambiguous", "rejected", None],
        "reason_code": [
            "initial_reminder",
            "identity_exact",
            "identity_ambiguous",
            "identity_rejected",
            "source_withdrawn",
            "source_reappeared",
        ],
        "decision_authority_kind": ["controlled_aemh_decision_record"],
    }
    issues: list[str] = []
    decision = inputs.get("AEMHDecisionAuthorityRecord", {})
    if decision.get("closed_values") != expected_decision_values:
        issues.append("AE/MH closed lifecycle")
    generation = decision.get("generation_validation_contract", {})
    if set(generation) != {
        "authority",
        "identity_recipe",
        "content_recipe",
        "reference_rule",
        "lifecycle_rule",
    } or not all(isinstance(value, str) and value for value in generation.values()):
        issues.append("AE/MH generation contract")
    elif "no current upstream append-only decision ledger is claimed" not in generation[
        "authority"
    ]:
        issues.append("AE/MH authority claim")
    return issues


def verify_public_api() -> dict[str, Any]:
    api = read_json(ARTIFACT_DIR / "public_api.json")
    if api["contract_id"] != CONTRACT_ID:
        fail("public API contract id mismatch")
    if api["python"]["minimum"] != "3.9":
        fail("public API Python floor must be 3.9")
    if api["constants"] != {
        "schema_version": SCHEMA_VERSION,
        "audience_contract_id": AUDIENCE_CONTRACT_ID,
        "subject_contract_id": SUBJECT_CONTRACT_ID,
        "aemh_contract_id": AEMH_CONTRACT_ID,
    }:
        fail("public API exact constants mismatch")
    common_module = "mm_r5.public_authority_common"
    subject_module = "mm_r5.subject_temporal_public"
    aemh_module = "mm_r5.aemh_match_history_public"
    if set(api["modules"]) != {common_module, subject_module, aemh_module}:
        fail("public API exact module set mismatch")
    common = _class_fields(api, common_module)
    subject_unique = _class_fields(api, subject_module)
    aemh_unique = _class_fields(api, aemh_module)
    subject_schema = read_json(PUBLIC_ARTIFACT_DIR / "subject_temporal_schema.json")
    aemh_schema = read_json(PUBLIC_ARTIFACT_DIR / "aemh_match_history_schema.json")
    subject_actual = {**common, **subject_unique}
    aemh_actual = {**common, **aemh_unique}
    subject_expected = {
        name: list(fields) for name, fields in subject_schema["objects"].items()
    }
    aemh_expected = {
        name: list(fields) for name, fields in aemh_schema["objects"].items()
    }
    if subject_actual != subject_expected or len(subject_actual) != 17:
        fail("subject output objects do not exactly match accepted 17-object schema")
    if aemh_actual != aemh_expected or len(aemh_actual) != 13:
        fail("AE/MH output objects do not exactly match accepted 13-object schema")
    if len(common) != 6:
        fail("shared output object count must be six")
    for module_name, required_input in (
        (common_module, "PublicAuthorityCommonSourceBundle"),
        (subject_module, "SubjectTemporalSourceBundle"),
        (aemh_module, "AEMHMatchHistorySourceBundle"),
    ):
        names = {
            item["name"] for item in api["modules"][module_name]["input_classes"]
        }
        if required_input not in names:
            fail(f"typed source bundle missing: {required_input}")
    inputs = _input_class_specs(api)
    for name, expected_fields in {
        "ControlledTemporalEndpointBinding": [
            "target_kind",
            "target_ref",
            "endpoint_role",
            "authority_kind",
            "authority_ref",
            "authority_date_field",
            "source_locator_refs",
        ],
        "ControlledCutoffLocatorBinding": [
            "cutoff_ref",
            "time_ref_id",
            "record_node_id",
            "source_locator_ref",
        ],
        "DomainApplicabilityAuthorityRecord": [
            "decision_ref",
            "domain",
            "applicability_state",
            "reason_code",
            "authority_identity",
            "authority_content_hash",
            "source_locator_refs",
        ],
        "AEMHDecisionAuthorityRecord": [
            "decision_ref",
            "thread_ref",
            "event_kind",
            "match_state",
            "reason_code",
            "later_fact_refs",
            "considered_fact_refs",
            "retained_source_locator_refs",
            "decision_authority_kind",
            "authority_identity",
            "authority_content_hash",
            "authority_source_locator_refs",
        ],
    }.items():
        spec = inputs.get(name)
        if spec is None or [field[0] for field in spec["fields"]] != expected_fields:
            fail(f"exact input record schema mismatch: {name}")
        if spec.get("decorator") != "dataclasses.dataclass(frozen=True)" or spec.get(
            "extra_fields_forbidden"
        ) is not True:
            fail(f"input record must be exact frozen dataclass: {name}")
    for name in (
        "ControlledTemporalEndpointBinding",
        "ControlledCutoffLocatorBinding",
    ):
        forbidden = set(inputs[name]["forbidden_fields"])
        if not {"content_hash", "exact_date"}.issubset(forbidden):
            fail(f"controlled binding can carry date/hash: {name}")
    if inputs["DomainApplicabilityAuthorityRecord"]["closed_values"] != {
        "domain": [
            "ae",
            "mh",
            "cm",
            "ip",
            "lab_exam",
            "hospital_procedure",
            "symptom_efficacy",
            "protocol_compliance",
        ],
        "applicability_state": ["applicable", "not_applicable", "not_provided"],
        "reason_code": [
            "members_present",
            "protocol_not_applicable",
            "authority_source_not_provided",
        ],
    }:
        fail("domain applicability closed vocabulary drift")
    decision_spec = inputs["AEMHDecisionAuthorityRecord"]
    if decision_spec["closed_values"] != {
        "event_kind": [
            "reminder_created",
            "match_decided",
            "withdrawn",
            "reappeared",
        ],
        "match_state": ["exact", "ambiguous", "rejected", None],
        "reason_code": [
            "initial_reminder",
            "identity_exact",
            "identity_ambiguous",
            "identity_rejected",
            "source_withdrawn",
            "source_reappeared",
        ],
        "decision_authority_kind": ["controlled_aemh_decision_record"],
    }:
        fail("AE/MH decision closed vocabulary drift")
    generation = decision_spec.get("generation_validation_contract", {})
    if set(generation) != {
        "authority",
        "identity_recipe",
        "content_recipe",
        "reference_rule",
        "lifecycle_rule",
    } or not all(isinstance(value, str) and value for value in generation.values()):
        fail("AE/MH controlled decision generation contract incomplete")
    if "no current upstream append-only decision ledger is claimed" not in generation[
        "authority"
    ]:
        fail("AE/MH controlled decision authority claim is not honest")
    controlled_issues = _controlled_record_validation_issues(api)
    if controlled_issues:
        fail(f"controlled record contract invalid: {controlled_issues}")
    functions = {
        module: api["modules"][module]["functions"]
        for module in (subject_module, aemh_module)
    }
    if functions != {
        subject_module: [
            "build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket",
            "validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult",
        ],
        aemh_module: [
            "build_aemh_match_history_authority(source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> AEMHMatchHistoryAuthorityPacket",
            "validate_aemh_match_history_authority(candidate: AEMHMatchHistoryAuthorityPacket, source: AEMHMatchHistorySourceBundle, previous_packet: Optional[AEMHMatchHistoryAuthorityPacket] = None) -> PublicAuthorityValidationResult",
        ],
    }:
        fail("builder/validator exact candidate-plus-source signatures mismatch")
    common_fields = dict(inputs["PublicAuthorityCommonSourceBundle"]["fields"])
    if common_fields.get("r5_authority_receipt") != "mm_r5.contracts.R5AuthorityReceipt":
        fail("R5AuthorityReceipt is not reachable from common source bundle")
    if api.get("aemh_previous_packet_rule") != (
        "previous_packet is an independent Optional API parameter to both AE/MH "
        "builder and validator, never a source-bundle field; both calls receive "
        "the same immutable object or None and disagreement fails closed before "
        "append-prefix validation"
    ):
        fail("AE/MH previous-packet source/argument rule mismatch")
    if common_fields.get("controlled_cutoff_locator_bindings") != (
        "tuple[ControlledCutoffLocatorBinding, ...]"
    ):
        fail("controlled cutoff bindings are not rooted in common source bundle")
    if "previous_packet" in dict(inputs["AEMHMatchHistorySourceBundle"]["fields"]):
        fail("AE/MH previous packet must not be a source-bundle field")
    if set(api.get("structured_reference_grammar", {}).get("closed_kinds", [])) != {
        "source",
        "previous",
        "output",
        "controlled",
        "constant",
        "context",
    }:
        fail("structured reference grammar kind set drift")
    if set(api.get("hash_target_catalog", {})) != set(subject_actual) | set(
        aemh_actual
    ):
        fail("hash target catalog must cover every exact output object")
    for name, constant in api.get("constant_catalog", {}).items():
        if (
            set(constant) != {"type", "value", "canonical_hash"}
            or constant["canonical_hash"] != canonical_hash(constant["value"])
            or not name
        ):
            fail(f"constant catalog hash drift: {name}")
    for contract, dag in api.get("hash_dags", {}).items():
        if set(dag) != {"nodes", "edges", "exact_order"} or dag["nodes"] != dag[
            "exact_order"
        ]:
            fail(f"hash DAG exact order drift: {contract}")
        positions = {node: index for index, node in enumerate(dag["exact_order"])}
        if len(positions) != len(dag["nodes"]) or any(
            left not in positions
            or right not in positions
            or positions[left] >= positions[right]
            for left, right in dag["edges"]
        ):
            fail(f"hash DAG cycle/forward edge: {contract}")
    history = api.get("aemh_history_algorithm", {})
    if set(history) != {
        "current_entries",
        "entry_hash",
        "entry_id",
        "previous_prefix_binding",
        "previous_projection_binding",
        "prior_hash",
        "suffix_sequence",
    } or not all(isinstance(value, str) and value for value in history.values()):
        fail("AE/MH acyclic previous/current history algorithm drift")
    study = api.get("study_day_algorithm", {})
    risk = api.get("risk_date_lineage_algorithm", {})
    if set(study) != {
        "anchor_resolution",
        "anchor_zero",
        "anchor_one",
        "timezone",
        "all_endpoints",
        "failure",
    } or not all(isinstance(value, str) and value for value in study.values()):
        fail("study-day algorithm is not uniquely specified")
    if set(risk) != {
        "binding",
        "authority",
        "locator_closure",
        "projection",
        "failure",
    } or not all(isinstance(value, str) and value for value in risk.values()):
        fail("risk-date lineage algorithm is not uniquely specified")
    required_study = ("exactly one", "actual_date", "anchor_zero", "anchor_one")
    study_text = json.dumps(study, sort_keys=True)
    if not all(token in study_text for token in required_study):
        fail("study-day algorithm omits an executable anchor/formula rule")
    risk_text = json.dumps(risk, sort_keys=True)
    if not all(
        token in risk_text
        for token in (
            "endpoint_role",
            "authority_date_field",
            "exactly one",
            "RiskCandidate.detail",
        )
    ):
        fail("risk-date algorithm omits endpoint lineage or forbidden inference")
    encoded = json.dumps(api, ensure_ascii=False)
    for forbidden in ("Mapping[str, Any] ->", " | None", "slots=True"):
        if forbidden in encoded:
            fail(f"Python 3.9/exact typed API forbidden token: {forbidden}")
    access_issues = _source_access_validation_issues(api)
    if access_issues:
        fail(f"source type access graph invalid: {access_issues[:8]}")
    return api


def _ast_class_fields(path: Path) -> dict[str, set[str]]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
        feature_version=(3, 9),
    )
    return {
        node.name: {
            item.target.id
            for item in node.body
            if isinstance(item, ast.AnnAssign)
            and isinstance(item.target, ast.Name)
        }
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def _ast_module_metadata(
    module_name: str, path: Path
) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
        feature_version=(3, 9),
    )
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".", 1)[0]] = alias.name
        elif isinstance(node, ast.ImportFrom):
            imported_module = node.module or ""
            if node.level:
                prefix = module_name.split(".")[:-node.level]
                imported_module = ".".join([*prefix, imported_module]).rstrip(".")
            for alias in node.names:
                aliases[alias.asname or alias.name] = (
                    f"{imported_module}.{alias.name}".strip(".")
                )
    classes = {
        node.name: {
            item.target.id: ast.unparse(item.annotation)
            for item in node.body
            if isinstance(item, ast.AnnAssign)
            and isinstance(item.target, ast.Name)
        }
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }
    return classes, aliases


@functools.lru_cache(maxsize=1)
def _source_module_metadata_catalog() -> dict[
    str, tuple[dict[str, dict[str, str]], dict[str, str]]
]:
    return {
        module: _ast_module_metadata(module, ROOT / relative)
        for module, relative in SOURCE_MODULE_PATHS.items()
    }


def _annotation_info(annotation: str) -> tuple[str, bool, bool]:
    node = ast.parse(
        annotation, mode="eval", feature_version=(3, 9)
    ).body
    optional = False
    many = False

    def unwrap(current: ast.AST) -> ast.AST:
        nonlocal optional, many
        if isinstance(current, ast.Subscript):
            outer = _dotted_name(current.value).split(".")[-1]
            if outer in {"Optional"}:
                optional = True
                return unwrap(current.slice)
            if outer in {"List", "Sequence", "Tuple", "list", "tuple"}:
                many = True
                inner = current.slice
                if isinstance(inner, ast.Tuple):
                    inner = inner.elts[0]
                return unwrap(inner)
            if outer == "Union":
                members = current.slice.elts if isinstance(current.slice, ast.Tuple) else [current.slice]
                non_none = [
                    member
                    for member in members
                    if _dotted_name(member) not in {"None", "NoneType"}
                ]
                optional = len(non_none) != len(members)
                if len(non_none) == 1:
                    return unwrap(non_none[0])
        return current

    terminal = unwrap(node)
    return _dotted_name(terminal), many, optional


def _resolve_type_name(
    name: str,
    current_module: str,
    aliases: Mapping[str, str],
    input_names: set[str],
) -> str:
    if "." in name:
        first, rest = name.split(".", 1)
        if first in aliases:
            return f"{aliases[first]}.{rest}"
        return name
    if name in aliases:
        return aliases[name]
    if current_module:
        return f"{current_module}.{name}"
    if name in input_names:
        return name
    return name


def _source_access_validation_issues(api: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    inputs = _input_class_specs(api)
    module_meta = _source_module_metadata_catalog()
    for contract, rows in api.get("source_type_access_paths", {}).items():
        root_type = (
            "SubjectTemporalSourceBundle"
            if contract == SUBJECT_CONTRACT_ID
            else "AEMHMatchHistorySourceBundle"
        )
        seen: set[str] = set()
        for row in rows:
            target = row.get("target_type")
            path = row.get("bundle_access_path")
            if not isinstance(target, str) or not isinstance(path, str) or target in seen:
                issues.append(f"duplicate/bad access:{contract}:{target}")
                continue
            seen.add(target)
            current_type = root_type
            current_module = ""
            any_many = False
            any_optional = False
            observed_expansion: list[str] = []
            for raw_segment in path.split("."):
                expands_many = raw_segment.endswith("[]")
                segment = raw_segment[:-2] if expands_many else raw_segment
                if current_type in inputs:
                    fields = dict(inputs[current_type]["fields"])
                    annotation = fields.get(segment)
                    aliases: Mapping[str, str] = {}
                else:
                    current_module, class_name = current_type.rsplit(".", 1)
                    classes, aliases = module_meta.get(current_module, ({}, {}))
                    annotation = classes.get(class_name, {}).get(segment)
                if annotation is None:
                    issues.append(f"unreachable segment:{contract}:{path}:{segment}")
                    break
                terminal, many, optional = _annotation_info(annotation)
                if expands_many != many:
                    issues.append(f"container expansion drift:{contract}:{path}:{segment}")
                any_many = any_many or many
                any_optional = any_optional or optional
                observed_expansion.append(
                    "field_then_expand_many" if many else "field"
                )
                current_type = _resolve_type_name(
                    terminal, current_module, aliases, set(inputs)
                )
            else:
                if current_type != target:
                    issues.append(f"terminal type drift:{contract}:{path}:{current_type}!={target}")
                if row.get("result_cardinality") != ("many" if any_many else "one"):
                    issues.append(f"result cardinality:{contract}:{path}")
                if row.get("result_optional") is not any_optional:
                    issues.append(f"result optionality:{contract}:{path}")
                if row.get("container_expansion") != observed_expansion:
                    issues.append(f"expansion recipe:{contract}:{path}")
    return issues


def _semantic_class(field_name: str, type_name: str = "") -> str:
    if field_name in {"severity", "severity_authority"}:
        return "severity"
    if field_name in {"applicability_state", "decision_status"}:
        return "applicability"
    if field_name in {
        "actual_date",
        "anchor_end",
        "anchor_start",
        "clinical_event_cutoff",
        "data_cutoff",
        "end",
        "exact_date",
        "range_end",
        "range_start",
        "start",
        "value",
        "candidate_values",
    } or type_name in {"date", "partial_date"}:
        return "date_value"
    if field_name.endswith(("_hash", "_content_identity")) or type_name == "sha256":
        return "content_identity"
    if "locator" in field_name or field_name == "source_refs":
        return "source_locator_identity"
    if field_name in {"domain", "domain_zh"}:
        return "domain_semantic"
    if field_name in {"phase", "risk_type_zh"} or field_name.endswith("_label_zh"):
        return "closed_audience_label"
    if field_name in {
        "authority_date_field",
        "authority_kind",
        "endpoint_role",
        "target_kind",
    }:
        return "closed_selector"
    if field_name.endswith(("_ref", "_id")) or field_name in {
        "considered_fact_refs",
        "later_fact_refs",
    }:
        return "typed_identity"
    if type_name == "boolean":
        return "boolean"
    if type_name == "integer" or field_name.endswith("_count"):
        return "integer"
    if field_name == "state" or type_name.startswith("enum:"):
        return "closed_enum"
    return "typed_value"


def _semantic_compatible(
    output_class: str, source_classes: Sequence[str], reducer: str
) -> bool:
    if output_class == "content_identity" and reducer == "canonical_sha256":
        return True
    strict = {
        "severity": {"severity"},
        "closed_audience_label": {"closed_audience_label", "domain_semantic"},
        "date_value": {
            "closed_enum",
            "date_value",
            "closed_selector",
            "source_locator_identity",
            "typed_identity",
        },
        "applicability": {
            "applicability",
            "content_identity",
            "domain_semantic",
            "source_locator_identity",
            "typed_identity",
            "typed_value",
        },
        "source_locator_identity": {
            "content_identity",
            "source_locator_identity",
            "typed_identity",
            "typed_value",
        },
    }
    allowed = strict.get(output_class)
    return allowed is None or all(item in allowed for item in source_classes)


def _source_join_validation_issues(
    matrix: Mapping[str, Any], api: Mapping[str, Any]
) -> list[str]:
    issues: list[str] = []
    subject = read_json(PUBLIC_ARTIFACT_DIR / "subject_temporal_schema.json")
    aemh = read_json(PUBLIC_ARTIFACT_DIR / "aemh_match_history_schema.json")
    schemas = {
        SUBJECT_CONTRACT_ID: subject,
        AEMH_CONTRACT_ID: aemh,
    }
    collection_catalog = api.get("collection_relation_key_catalog", {})
    expected_collection_fields: dict[str, set[str]] = {}
    for authority in api["join_key_authority_catalog"].values():
        for component in authority["components"]:
            key_reference = component["authority_reference"]
            expected_collection_fields.setdefault(
                key_reference["terminal"]["owner"], set()
            ).add(key_reference["segments"][-1]["field"])
    if set(collection_catalog) != set(expected_collection_fields):
        fail("collection relation-key owner coverage drift")
    for owner, fields in expected_collection_fields.items():
        expected_self_keys = [
            terminal
            for terminal in api["structured_reference_grammar"][
                "legal_self_key_terminals"
            ]
            if terminal.startswith(owner + ".")
        ]
        if collection_catalog[owner] != {
            "real_identity_or_ref_fields": sorted(fields),
            "value_terminal_exclusion_required_except_exact_legal_self_key": True,
            "legal_self_key_terminals": expected_self_keys,
            "composite_components_all_compared": True,
        }:
            fail(f"collection relation-key catalog drift: {owner}")
    expected = {
        (contract, f"{object_name}.{field_name}")
        for contract, schema in schemas.items()
        for object_name, fields in schema["objects"].items()
        for field_name in fields
    }
    rows = matrix.get("rows", [])
    scalar_many_expansion_rows = sum(
        row["cardinality"] != "many"
        and any(
            any(segment["expand"] == "many" for segment in reference["segments"])
            for reference in row["references"]
        )
        for row in rows
    )
    relation_key_components = [
        clause
        for row in rows
        for reference in row["references"]
        for clause in reference.get("selector", {}).get("predicate", {}).get(
            "clauses", []
        )
    ]
    label_field_mismatches = sum(
        clause.get("join_key")
        != clause.get("lhs", {}).get("owner", "")
        + "."
        + ".".join(clause.get("lhs", {}).get("path", []))
        for clause in relation_key_components
    )
    if (
        scalar_many_expansion_rows != 196
        or matrix.get("closure", {}).get(
            "scalar_rows_with_many_expansion_machine_selector_count"
        )
        != 196
        or matrix.get("closure", {}).get(
            "all_many_expansions_use_predicate_cardinality_machine_selector"
        )
        is not True
        or matrix.get("closure", {}).get("empty_reference_branch_count") != 48
        or matrix.get("closure", {}).get(
            "historical_reviewer_v7_label_field_mismatch_count"
        ) != 1168
        or matrix.get("closure", {}).get("current_label_field_mismatch_count")
        != label_field_mismatches
        or label_field_mismatches != 0
        or matrix.get("closure", {}).get("terminal_copy_key_violation_count")
        != 0
        or matrix.get("closure", {}).get("relation_key_component_count")
        != len(relation_key_components)
    ):
        fail("196 scalar/many-expansion selector coverage drift")
    actual = [(row.get("contract"), row.get("leaf")) for row in rows]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        issues.append("leaf coverage")
    if matrix.get("row_count") != len(rows) or len(rows) != 272:
        issues.append("row count")
    if actual != sorted(actual):
        issues.append("row ordering")
    source_classes = {
        module: _ast_class_fields(ROOT / relative)
        for module, relative in SOURCE_MODULE_PATHS.items()
    }
    input_fields = {
        name: {field[0] for field in spec["fields"]}
        for name, spec in _input_class_specs(api).items()
    }
    output_fields = {
        name: set(fields)
        for module in api["modules"]
        for name, fields in _class_fields(api, module).items()
    }
    allowed_constants = {
        "AEMH_CONTRACT_ID",
        "AUDIENCE_CONTRACT_ID",
        "DEFAULT_AXIS_MODE_CALENDAR",
        "FAIL_CLOSED_NO_NEAREST",
        "PRODUCER_CONTRACT_ID",
        "RECEIPT_VARIANT_BY_PRODUCER",
        "RISK_LIFECYCLE_EFFECT_NONE",
        "SCHEMA_VERSION",
        "SUBJECT_CONTRACT_ID",
    }
    exact_keys = {
        "contract",
        "leaf",
        "source_field_paths",
        "source_semantic_classes",
        "output_semantic_class",
        "join_keys",
        "derivation",
        "reducer",
        "closed_mapping",
        "component_comparison_provenance",
        "cardinality",
        "nullable",
        "ordering",
        "unavailable_fail_closed_code",
        "fallback",
        "fixture_or_artifact_authority",
    }
    for row in rows:
        leaf = str(row.get("leaf"))
        if set(row) != exact_keys:
            issues.append(f"row keys:{leaf}")
            continue
        if not row["source_field_paths"] or not row["join_keys"]:
            issues.append(f"missing source/join:{leaf}")
        expected_source_classes = [
            "frozen_constant"
            if path.startswith("constant:")
            else _semantic_class(path.rsplit(".", 1)[-1])
            for path in row["source_field_paths"]
        ]
        if row["source_semantic_classes"] != expected_source_classes:
            issues.append(f"source semantic class drift:{leaf}")
        if not all(
            isinstance(row[key], str) and row[key]
            for key in (
                "derivation",
                "reducer",
                "closed_mapping",
                "cardinality",
                "ordering",
                "unavailable_fail_closed_code",
            )
        ):
            issues.append(f"missing semantics:{leaf}")
        if row["fallback"] != "fail_closed_no_nearest":
            issues.append(f"fallback:{leaf}")
        if row["fixture_or_artifact_authority"] is not False:
            issues.append(f"fixture authority:{leaf}")
        contract = row["contract"]
        object_name, field_name = leaf.split(".", 1)
        spec = schemas.get(contract, {}).get("objects", {}).get(object_name, {}).get(
            field_name
        )
        if spec is None:
            issues.append(f"unknown leaf:{leaf}")
        elif row["cardinality"] != spec["cardinality"] or row["nullable"] != spec[
            "nullable"
        ]:
            issues.append(f"shape drift:{leaf}")
        elif row["output_semantic_class"] != _semantic_class(
            field_name, spec["type"]
        ):
            issues.append(f"output semantic class drift:{leaf}")
        elif not _semantic_compatible(
            row["output_semantic_class"],
            row["source_semantic_classes"],
            row["reducer"],
        ):
            issues.append(f"semantic incompatibility:{leaf}")
        for source_path in row["source_field_paths"]:
            lowered = source_path.lower()
            if any(token in lowered for token in ("fixture", "artifacts/", "any", ".detail")):
                issues.append(f"forbidden source:{leaf}:{source_path}")
                continue
            if source_path.startswith("source:"):
                parts = source_path.split(":", 2)
                if len(parts) != 3 or "." not in parts[2]:
                    issues.append(f"source grammar:{source_path}")
                    continue
                module = parts[1]
                class_name, source_field = parts[2].split(".", 1)
                classes = source_classes.get(module, {})
                if source_field not in classes.get(class_name, set()):
                    issues.append(f"unresolved source:{source_path}")
            elif source_path.startswith("controlled:"):
                rest = source_path.removeprefix("controlled:")
                if "." not in rest:
                    issues.append(f"controlled grammar:{source_path}")
                    continue
                class_name, source_field = rest.split(".", 1)
                if source_field not in input_fields.get(class_name, set()):
                    issues.append(f"unresolved controlled:{source_path}")
            elif source_path.startswith("output:"):
                rest = source_path.removeprefix("output:")
                if "." not in rest:
                    issues.append(f"output grammar:{source_path}")
                    continue
                class_name, source_field = rest.split(".", 1)
                if source_field not in output_fields.get(class_name, set()):
                    issues.append(f"unresolved output:{source_path}")
            elif source_path.startswith("constant:"):
                if source_path.removeprefix("constant:") not in allowed_constants:
                    issues.append(f"unresolved constant:{source_path}")
            else:
                issues.append(f"unknown source grammar:{source_path}")
    by_leaf = {(row["contract"], row["leaf"]): row for row in rows}
    risk_identity = by_leaf.get(
        (SUBJECT_CONTRACT_ID, "TemporalRiskAnchor.risk_content_identity"), {}
    )
    if set(risk_identity.get("source_field_paths", [])) != {
        "source:mm_r5.s4_contracts:S4AcceptedAuthorityAnchor.accepted_risk_identity_hash",
        "source:mm_r5.s4_contracts:S4AcceptedRiskIdentity.risk_identity_hash",
    } or risk_identity.get("reducer") != "same_accepted_risk_authority_identity":
        issues.append("risk content identity authority")
    severity = by_leaf.get((SUBJECT_CONTRACT_ID, "TemporalRiskAnchor.severity"), {})
    if severity.get("reducer") != "accepted_risk_severity_conversion" or "RiskInstance" in " ".join(
        severity.get("source_field_paths", [])
    ):
        issues.append("risk severity authority")
    risk_type = by_leaf.get(
        (SUBJECT_CONTRACT_ID, "TemporalRiskAnchor.risk_type_zh"), {}
    )
    if risk_type.get("reducer") != "accepted_domain_to_risk_type_zh" or "signal_type" in " ".join(
        risk_type.get("source_field_paths", [])
    ):
        issues.append("risk type mapping")
    applicability = by_leaf.get(
        (SUBJECT_CONTRACT_ID, "TemporalDomainTrack.applicability_state"), {}
    )
    if not any(
        path.startswith("controlled:DomainApplicabilityAuthorityRecord.")
        for path in applicability.get("source_field_paths", [])
    ) or "not_applicable" not in applicability.get("closed_mapping", ""):
        issues.append("typed domain applicability authority")
    cutoff = by_leaf.get(
        (SUBJECT_CONTRACT_ID, "PublicCutoffEndpoint.source_locator_refs"), {}
    )
    if cutoff.get("reducer") != "exact_single_cutoff_locator" or not any(
        path.startswith("controlled:ControlledCutoffLocatorBinding.")
        for path in cutoff.get("source_field_paths", [])
    ):
        issues.append("unique cutoff locator binding")
    return issues


def verify_source_join_matrix(api: Mapping[str, Any]) -> dict[str, Any]:
    matrix = read_json(ARTIFACT_DIR / "source_join_matrix.json")
    if matrix["contract_id"] != CONTRACT_ID or matrix["schema_version"] != SCHEMA_VERSION:
        fail("source join matrix identity mismatch")
    issues = _source_join_validation_issues(matrix, api)
    if issues:
        fail(f"source join matrix invalid: {issues[:8]}")
    return matrix


def _normalized_terminal_type(type_name: str) -> str:
    aliases = {
        "bool": "boolean",
        "dict": "mapping",
        "float": "number",
        "int": "integer",
        "str": "string",
    }
    return aliases.get(type_name, type_name)


def _resolve_structured_source_ref(
    reference: Mapping[str, Any], api: Mapping[str, Any]
) -> tuple[str, str]:
    roots = {
        "subject_source": "SubjectTemporalSourceBundle",
        "aemh_source": "AEMHMatchHistorySourceBundle",
    }
    current_type = roots[str(reference["root"])]
    current_module = ""
    inputs = _input_class_specs(api)
    module_meta = _source_module_metadata_catalog()
    owner = current_type
    terminal_type = ""
    for segment in reference["segments"]:
        field_name = segment["field"]
        if current_type in inputs:
            annotation = dict(inputs[current_type]["fields"]).get(field_name)
            aliases: Mapping[str, str] = {}
        elif "." in current_type:
            current_module, class_name = current_type.rsplit(".", 1)
            classes, aliases = module_meta.get(current_module, ({}, {}))
            annotation = classes.get(class_name, {}).get(field_name)
        else:
            fail(f"structured ref unknown owner: {current_type}")
        if annotation is None:
            fail(f"structured ref dangling field: {current_type}.{field_name}")
        terminal, many, optional = _annotation_info(annotation)
        expected_expand = "optional" if optional else "many" if many else "one"
        allowed_expands = (
            {"many", "container"}
            if many and segment is reference["segments"][-1]
            else {expected_expand}
        )
        if segment["expand"] not in allowed_expands:
            fail(
                f"structured ref expansion mismatch: {current_type}.{field_name} "
                f"expected={expected_expand} observed={segment['expand']}"
            )
        owner = current_type
        terminal_type = terminal
        current_type = _resolve_type_name(
            terminal, current_module, aliases, set(inputs)
        )
    return owner, terminal_type


def _resolve_structured_object_ref(
    reference: Mapping[str, Any], schema: Mapping[str, Any]
) -> tuple[str, str]:
    segments = reference["segments"]
    if (
        len(segments) != 3
        or segments[0] != {"field": "objects", "expand": "one"}
        or segments[1].get("expand") != "many"
        or segments[2].get("expand") not in {"one", "many", "container"}
    ):
        fail("structured output/previous registry path is malformed")
    owner = segments[1]["field"]
    field_name = segments[2]["field"]
    field_spec = schema["objects"].get(owner, {}).get(field_name)
    if field_spec is None:
        fail(f"structured output/previous path is dangling: {owner}.{field_name}")
    expected_expand = "many" if field_spec["cardinality"] == "many" else "one"
    allowed_expands = (
        {"many", "container"}
        if field_spec["cardinality"] == "many"
        else {expected_expand}
    )
    if segments[2]["expand"] not in allowed_expands:
        fail(f"structured output field expansion mismatch: {owner}.{field_name}")
    return owner, field_spec["type"]


def _structured_fixture_values(
    reference: Mapping[str, Any], graph: Mapping[str, Any], api: Mapping[str, Any]
) -> list[Any]:
    kind = reference["kind"]
    if kind == "constant":
        name = reference["segments"][0]["field"]
        entry = api["constant_catalog"][name]
        if len(reference["segments"]) == 1:
            return [copy.deepcopy(entry["value"])]
        if reference["segments"] == [
            {"field": name, "expand": "one"},
            {"field": "canonical_hash", "expand": "one"},
        ]:
            return [entry["canonical_hash"]]
        fail("structured constant key path is malformed")
    if kind in {"output", "previous"}:
        root_name = "previous" if kind == "previous" else "expected_candidate"
        reachable = _fixture_reachable(graph, root_name)
        owner = reference["segments"][1]["field"]
        field_name = reference["segments"][2]["field"]
        return [
            _fixture_plain_value(graph["nodes"][node_id]["fields"][field_name], graph)
            for node_id in sorted(reachable)
            if graph["nodes"][node_id]["type"] == owner
        ]
    values: list[Any] = [graph["roots"]["source"]]
    for segment in reference["segments"]:
        expanded: list[Any] = []
        for value in values:
            if isinstance(value, dict) and set(value) == {"node_ref"}:
                value = graph["nodes"][value["node_ref"]]["fields"]
            field_value = value[segment["field"]]
            if segment["expand"] == "many":
                expanded.extend(copy.deepcopy(next(iter(field_value.values()))))
            elif segment["expand"] == "container":
                expanded.append(copy.deepcopy(field_value))
            elif segment["expand"] == "optional" and field_value is None:
                continue
            else:
                expanded.append(copy.deepcopy(field_value))
        values = expanded
    return [_fixture_plain_value(value, graph) for value in values]


def _structured_fixture_records(
    reference: Mapping[str, Any], graph: Mapping[str, Any], api: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    kind = reference["kind"]
    if kind == "constant":
        name = reference["segments"][0]["field"]
        entry = api["constant_catalog"][name]
        return [{name: copy.deepcopy(entry["value"]), **copy.deepcopy(entry)}]
    if kind in {"output", "previous"}:
        root_name = "previous" if kind == "previous" else "expected_candidate"
        owner = reference["segments"][1]["field"]
        return [
            graph["nodes"][node_id]["fields"]
            for node_id in sorted(_fixture_reachable(graph, root_name))
            if graph["nodes"][node_id]["type"] == owner
        ]
    values: list[Any] = [graph["roots"]["source"]]
    for segment in reference["segments"][:-1]:
        expanded: list[Any] = []
        for value in values:
            if isinstance(value, dict) and set(value) == {"node_ref"}:
                value = graph["nodes"][value["node_ref"]]["fields"]
            field_value = value[segment["field"]]
            if segment["expand"] == "many":
                expanded.extend(copy.deepcopy(next(iter(field_value.values()))))
            elif segment["expand"] == "optional" and field_value is None:
                continue
            else:
                expanded.append(copy.deepcopy(field_value))
        values = expanded
    return [
        graph["nodes"][value["node_ref"]]["fields"]
        if isinstance(value, dict) and set(value) == {"node_ref"}
        else value
        for value in values
    ]


def _execute_structured_selector(
    reference: Mapping[str, Any], row: Mapping[str, Any], graph: Mapping[str, Any],
    api: Mapping[str, Any], grammar: Mapping[str, Any]
) -> list[Any]:
    def terminal_semantic(candidate: Mapping[str, Any]) -> str:
        field_name = candidate["segments"][-1]["field"]
        type_name = candidate["terminal"]["type"]
        if field_name.endswith(("_hash", "_content_identity")) or type_name == "sha256":
            return "content_identity"
        if "locator" in field_name or field_name == "source_refs":
            return "source_locator_identity"
        if field_name in {
            "actual_date",
            "anchor_end",
            "anchor_start",
            "clinical_event_cutoff",
            "data_cutoff",
            "end",
            "exact_date",
            "range_end",
            "range_start",
            "start",
        } or type_name in {"date", "partial_date"}:
            return "date_or_endpoint_identity"
        if field_name == "domain":
            return "domain_semantic"
        if field_name.endswith(("_ref", "_refs", "_id", "_ids")) or field_name in {
            "later_fact_refs",
            "considered_fact_refs",
        }:
            return "typed_identity"
        if field_name in {
            "event_kind",
            "match_state",
            "reason_code",
            "state",
            "status",
        }:
            return "closed_semantic"
        return "typed_value"

    selector = reference.get("selector")
    if not isinstance(selector, dict) or set(selector) != set(
        grammar["selector_exact_keys"]
    ):
        fail(f"structured selector schema drift: {row['leaf']}")
    predicate = selector["predicate"]
    authority = api["join_key_authority_catalog"].get(
        f"{row['contract']}::{row['leaf']}"
    )
    if not isinstance(authority, dict) or set(authority) != {
        "derivation_join_keys",
        "legal_self_key_terminals",
        "components",
    }:
        fail(f"join-key authority catalog drift: {row['leaf']}")
    reference_index = next(
        (
            index
            for index, candidate in enumerate(row["references"])
            if candidate is reference
        ),
        -1,
    )
    if reference_index < 0:
        fail(f"selector reference is not row-owned: {row['leaf']}")
    components = [
        component
        for component in authority["components"]
        if component.get("reference_index") == reference_index
    ]
    expected_keys = [component["join_key"] for component in components]
    all_relation_keys = list(dict.fromkeys(
        component["join_key"] for component in authority["components"]
    ))
    expected_classes = [component["semantic_class"] for component in components]
    clauses = predicate.get("clauses", []) if isinstance(predicate, dict) else []
    if (
        selector["op"] != "composite_and"
        or selector["op"] not in grammar["closed_selector_ops"]
        or selector["cardinality"]
        not in grammar["closed_selector_cardinalities"]
        or selector["reducer"] != row["reducer"]
        or row["join_keys"] != all_relation_keys
        or not isinstance(predicate, dict)
        or set(predicate) != set(grammar["predicate_exact_keys"])
        or predicate["op"] != "composite_and"
        or [clause.get("join_key") for clause in clauses] != expected_keys
        or [clause.get("semantic_class") for clause in clauses]
        != expected_classes
        or len(components) != len(expected_keys)
    ):
        fail(f"structured selector/join-key drift: {row['leaf']}")
    for clause, component in zip(clauses, components):
        authority_reference = component.get("authority_reference")
        context_reference = component.get("context_reference")
        if not isinstance(authority_reference, dict) or not isinstance(
            context_reference, dict
        ):
            fail(f"structured authority reference missing: {row['leaf']}")
        for key_reference in (authority_reference, context_reference):
            if key_reference["kind"] in {"source", "controlled"}:
                _resolve_structured_source_ref(key_reference, api)
            elif key_reference["kind"] in {"output", "previous"}:
                schema_name = (
                    "subject_temporal_schema.json"
                    if row["contract"] == SUBJECT_CONTRACT_ID
                    else "aemh_match_history_schema.json"
                )
                _resolve_structured_object_ref(
                    key_reference,
                    read_json(PUBLIC_ARTIFACT_DIR / schema_name),
                )
            elif key_reference["kind"] == "constant":
                constant_name = key_reference["segments"][0]["field"]
                if (
                    constant_name not in api["constant_catalog"]
                    or key_reference["segments"][-1]
                    != {"field": "canonical_hash", "expand": "one"}
                    or key_reference["terminal"]
                    != {"owner": "constant_catalog_entry", "type": "sha256"}
                ):
                    fail(f"structured authority constant key invalid: {row['leaf']}")
            elif key_reference["kind"] == "context":
                if (
                    key_reference.get("root") != "current_join_context"
                    or key_reference.get("segments") != [
                        {"field": "records", "expand": "many"},
                        {
                            "field": "authority_value_canonical_json",
                            "expand": "one",
                        },
                    ]
                    or key_reference.get("terminal")
                    != {
                        "owner": "CurrentJoinContextAuthorityRecord",
                        "type": "str",
                    }
                ):
                    fail(f"structured current context ref invalid: {row['leaf']}")
            else:
                fail(f"structured authority kind invalid: {row['leaf']}")
        value_terminal = {
            "owner": reference["terminal"]["owner"],
            "field": reference["segments"][-1]["field"],
        }
        key_terminal = (
            authority_reference["terminal"]["owner"]
            + "."
            + authority_reference["segments"][-1]["field"]
        )
        self_key = component.get("self_key_exception") is True
        terminal_copy = component.get("value_terminal") == {
            "owner": authority_reference["terminal"]["owner"],
            "field": authority_reference["segments"][-1]["field"],
        }
        if self_key != terminal_copy:
            fail(f"structured self-key marker drift: {row['leaf']}")
        if self_key and key_terminal not in authority["legal_self_key_terminals"]:
            fail(f"structured self-key is not uniquely authorized: {row['leaf']}")
        if terminal_copy and not self_key:
            fail(f"structured terminal-copy key forbidden: {row['leaf']}")
        expected_key_id = canonical_hash(
            {
                "contract": row["contract"],
                "leaf": row["leaf"],
                "reference_index": reference_index,
                "join_key_index": component["join_key_index"],
                "join_key": component["join_key"],
                "authority_reference": authority_reference,
                "context_reference": context_reference,
                "context_component_key": component["context_component_key"],
                "value_terminal": value_terminal,
            }
        )
        if (
            set(component) != {
                "authority_key", "authority_reference", "context_reference",
                "context_component_key",
                "join_key", "join_key_index", "reference_index",
                "self_key_exception", "semantic_class", "value_terminal",
            }
            or set(clause) != set(grammar["predicate_clause_exact_keys"])
            or clause["op"] not in {"eq", "ref_eq"}
            or clause["op"] not in grammar["closed_predicate_ops"]
            or set(clause["lhs"]) != set(grammar["lhs_operand_exact_keys"])
            or clause["lhs"]
            != {
                "scope": "candidate_item",
                "owner": authority_reference["terminal"]["owner"],
                "path": [authority_reference["segments"][-1]["field"]],
            }
            or set(clause["rhs"])
            != set(grammar["rhs_operand_exact_keys"])
            or clause["rhs"].get("scope") != "current_join_context"
            or clause["rhs"].get("authority_key")
            != component["authority_key"]
            or clause["key_id"] != expected_key_id
            or component["authority_key"] != expected_key_id
            or context_reference == authority_reference
            or context_reference.get("kind") != "context"
            or context_reference.get("root") != "current_join_context"
            or component["value_terminal"] != value_terminal
            or component["join_key"] != key_terminal
            or component["semantic_class"]
            != terminal_semantic(authority_reference)
            or component["semantic_class"] not in {
                "typed_identity", "source_locator_identity", "content_identity"
            }
        ):
            fail(
                "PUB_REFERENCE_UNRESOLVED: structured predicate AST drift: "
                f"{row['leaf']}"
            )
    values = _structured_fixture_values(reference, graph, api)
    if (
        row["contract"] == AEMH_CONTRACT_ID
        and row["leaf"] == "PublicSourceLocator.locator_content_hash"
        and reference["kind"] == "output"
        and reference["segments"][-1]["field"] == "canonical_location"
        and all(value is None for value in values)
    ):
        values = []
    expected_cardinality = (
        "zero_or_one"
        if not values
        else "exact_one"
        if len(values) == 1
        else "one_or_more"
    )
    if selector["cardinality"] != expected_cardinality:
        fail(f"structured controlled-key authority drift: {row['leaf']}")
    record_components = [
        (clause, component)
        for clause, component in zip(clauses, components)
        if component["authority_reference"]["terminal"]["owner"]
        == reference["terminal"]["owner"]
    ]
    context_nodes = [
        graph["nodes"][node_id]
        for node_id in sorted(_fixture_reachable(graph, "join_context"))
        if graph["nodes"][node_id]["type"]
        == "CurrentJoinContextAuthorityRecord"
    ]
    context_values_by_component: dict[str, set[str]] = {}
    for component in components:
        authority_values = _structured_fixture_values(
            component["authority_reference"], graph, api
        )
        expected_context_values = {
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            for value in authority_values
        }
        matching_context = [
            node["fields"]
            for node in context_nodes
            if node["fields"].get("component_key")
            == component["context_component_key"]
        ]
        actual_context_values: set[str] = set()
        for fields in matching_context:
            if (
                fields.get("candidate_owner")
                != component["authority_reference"]["terminal"]["owner"]
                or fields.get("candidate_field")
                != component["authority_reference"]["segments"][-1]["field"]
                or fields.get("semantic_class") != component["semantic_class"]
                or fields.get("authority_content_hash")
                != canonical_hash({
                    key: value
                    for key, value in fields.items()
                    if key != "authority_content_hash"
                })
            ):
                fail(f"current join-context record drift: {row['leaf']}")
            actual_context_values.add(fields["authority_value_canonical_json"])
        if actual_context_values != expected_context_values:
            fail(f"independent relation authority/context drift: {row['leaf']}")
        context_values_by_component[component["context_component_key"]] = (
            actual_context_values
        )
    selected: list[Any] = []
    for record in _structured_fixture_records(reference, graph, api):
        if any(
            json.dumps(
                _fixture_plain_value(record[clause["lhs"]["path"][0]], graph),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            not in context_values_by_component[component["context_component_key"]]
            for clause, component in record_components
        ):
            continue
        terminal_field = reference["segments"][-1]["field"]
        terminal_value = _fixture_plain_value(record[terminal_field], graph)
        if not values and terminal_value is None:
            continue
        terminal_expand = reference["segments"][-1]["expand"]
        if terminal_expand == "many":
            if terminal_value or reference["kind"] in {"output", "previous"}:
                selected.append(terminal_value)
        elif terminal_expand == "optional" and terminal_value is None:
            continue
        else:
            selected.append(terminal_value)
    cardinality = selector["cardinality"]
    none_semantics = selector["none_semantics"]
    if cardinality == "exact_one" and len(selected) != 1:
        fail(f"structured selector did not resolve exact-one: {row['leaf']}")
    if cardinality == "one_or_more" and len(selected) < 1:
        fail(f"structured selector did not resolve one-or-more: {row['leaf']}")
    if cardinality == "zero_or_one":
        if len(selected) > 1 or none_semantics != {
            "kind": "explicit_none",
            "code": row["unavailable_fail_closed_code"],
            "result": None,
        }:
            fail(f"structured zero-or-one semantics drift: {row['leaf']}")
    elif none_semantics != {"kind": "forbidden"}:
        fail(f"structured nonempty none-semantics drift: {row['leaf']}")
    if row["reducer"] == "canonical_sha256":
        canonical_hash(selected)
    elif not selected and cardinality != "zero_or_one":
        fail(f"structured reducer received no selected members: {row['leaf']}")
    return selected


def _execute_join_reducer(
    row: Mapping[str, Any], selected_by_reference: Sequence[Sequence[Any]],
    graph: Mapping[str, Any],
) -> None:
    """Independently execute the frozen reducer against one exact fixture."""
    owner, field_name = row["leaf"].split(".", 1)
    target_records = [
        graph["nodes"][node_id]["fields"]
        for node_id in sorted(_fixture_reachable(graph, "expected_candidate"))
        if graph["nodes"][node_id]["type"] == owner
    ]
    if not target_records:
        # PublicCutoffEndpoint is the AEMH public variant.  The subject packet
        # uses its accepted TemporalDateEndpoint cutoff variant instead; the
        # four common-schema rows remain frozen for cross-contract lineage but
        # must resolve to that concrete subject cutoff instance, never vanish
        # as a global empty-branch pass.
        if (
            row["contract"] != SUBJECT_CONTRACT_ID
            or owner != "PublicCutoffEndpoint"
        ):
            fail(f"reducer target output is absent: {row['leaf']}")
        packet = _fixture_plain_value(graph["roots"]["expected_candidate"], graph)
        cutoff = packet["projection"]["axis_basis"]["cutoff_endpoint"]
        selected_flat = [
            item
            for values in selected_by_reference
            for value in values
            for item in (value if isinstance(value, list) else [value])
        ]
        if field_name == "exact_date":
            nonnull = [value for value in selected_flat if value is not None]
            if not nonnull or len({canonical_hash(value) for value in nonnull}) != 1:
                fail(f"all-equal reducer input disagreement: {row['leaf']}")
            if cutoff["exact_date"] != nonnull[0]:
                fail(f"all-equal reducer output mismatch: {row['leaf']}")
        elif field_name == "state":
            public_state = (
                "present"
                if cutoff["exact_date"] not in {None, ""}
                else "absent"
            )
            if public_state not in selected_flat:
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif field_name == "source_locator_refs":
            if not set(cutoff["source_locator_refs"]).intersection(selected_flat):
                fail(f"reducer target/output provenance mismatch: {row['leaf']}")
        elif field_name == "cutoff_content_hash":
            expected = canonical_hash({
                key: value
                for key, value in cutoff.items()
                if key != "endpoint_content_hash"
            })
            if cutoff["endpoint_content_hash"] != expected:
                fail(f"canonical reducer output mismatch: {row['leaf']}")
        else:
            fail(f"subject cutoff variant row unknown: {row['leaf']}")
        return
    target_values = [
        _fixture_plain_value(record[field_name], graph)
        for record in target_records
    ]

    def scalar_values(value: Any) -> list[Any]:
        if isinstance(value, list):
            result: list[Any] = []
            for item in value:
                result.extend(scalar_values(item))
            return result
        return [value]

    selected = [
        item
        for reference_values in selected_by_reference
        for value in reference_values
        for item in scalar_values(value)
    ]
    # ISO parsing is part of execution, not only a string-shape check.
    for reference, reference_values in zip(row["references"], selected_by_reference):
        terminal_field = reference["segments"][-1]["field"]
        if terminal_field not in {
            "actual_date", "anchor_end", "anchor_start", "data_cutoff", "end",
            "exact_date", "range_end", "range_start", "start", "value",
        }:
            continue
        for value in reference_values:
            for item in scalar_values(value):
                if item in {None, ""}:
                    continue
                try:
                    parsed = date.fromisoformat(item)
                except (TypeError, ValueError):
                    fail(f"reducer ISO input invalid: {row['leaf']}")
                if parsed.isoformat() != item:
                    fail(f"reducer ISO normalization drift: {row['leaf']}")

    operation = row["reducer_execution_op"]
    if operation == "all_equal":
        nonnull = [value for value in selected if value is not None]
        if len({canonical_hash(value) for value in nonnull}) > 1:
            fail(
                f"{row['unavailable_fail_closed_code']}: all-equal "
                f"reducer input disagreement: {row['leaf']}"
            )
        expected = nonnull[0] if nonnull else None
        if any(value != expected for value in target_values):
            fail(
                f"{row['unavailable_fail_closed_code']}: all-equal "
                f"reducer output mismatch: {row['leaf']}"
            )
    elif operation == "boolean_derivation":
        if row["leaf"] == "VisibilityClosure.deep_link_eligible":
            states = selected_by_reference[0]
            projectable_sites = [
                site
                for value in selected_by_reference[1]
                for site in (value if isinstance(value, list) else [value])
            ]
            scope_sites = selected_by_reference[2]
            if len(states) != 1 or not scope_sites:
                fail(f"boolean reducer input cardinality: {row['leaf']}")
            expected_values = [
                states[0] == "projectable"
                and site in projectable_sites
                for site in sorted(set(scope_sites))
            ]
        elif row["leaf"] == "TemporalDateEndpoint.range_projection_authorized":
            states = selected_by_reference[0]
            starts = selected_by_reference[1]
            ends = selected_by_reference[2]
            if not (len(states) == len(starts) == len(ends)):
                fail(f"boolean reducer input cardinality: {row['leaf']}")
            expected_values = [
                state == "exact" or (
                    state in {"partial", "conflicted"}
                    and start not in {None, ""}
                    and end not in {None, ""}
                )
                for state, start, end in zip(states, starts, ends)
            ]
        elif row["leaf"] == "TemporalDateEndpoint.main_axis_projectable":
            states = selected_by_reference[0]
            range_authorized = selected_by_reference[2]
            if len(states) != len(range_authorized):
                fail(f"boolean reducer input cardinality: {row['leaf']}")
            expected_values = [
                state == "exact" or (
                    state in {"partial", "conflicted"}
                    and authorized is True
                )
                for state, authorized in zip(states, range_authorized)
            ]
        else:
            fail(f"boolean reducer recipe missing: {row['leaf']}")
        if target_values != expected_values:
            fail(f"boolean reducer output mismatch: {row['leaf']}")
    elif operation == "canonical_recipe":
        for record, target in zip(target_records, target_values):
            if field_name == "packet_content_hash":
                projection = _fixture_plain_value(record["projection"], graph)
                receipt = _fixture_plain_value(record["receipt"], graph)
                expected = canonical_hash({
                    "receipt_content_hash": receipt["receipt_content_hash"],
                    "projection_content_hash": projection[
                        "projection_content_hash"
                    ],
                })
            elif field_name == "projection_id":
                scope = _fixture_plain_value(record["scope_identity"], graph)
                membership = _fixture_plain_value(record["membership_index"], graph)
                payload = {
                    "contract_id": record["contract_id"],
                    "schema_version": record["schema_version"],
                    "scope_identity_hash": scope["identity_content_hash"],
                    "membership_index_hash": membership[
                        "membership_content_hash"
                    ],
                }
                if owner == "SubjectTemporalPublicProjection":
                    axis = _fixture_plain_value(record["axis_basis"], graph)
                    payload["axis_basis_hash"] = axis["axis_content_hash"]
                expected = canonical_hash(payload)
            elif field_name == "receipt_id":
                scope = _fixture_plain_value(record["scope_identity"], graph)
                expected = canonical_hash({
                    "receipt_variant": record["receipt_variant"],
                    "authority_contract_id": record["authority_contract_id"],
                    "scope_identity_hash": scope["identity_content_hash"],
                    "public_projection_id": record["public_projection_id"],
                })
            elif "every exact" in row["derivation"]:
                expected = canonical_hash({
                    key: _fixture_plain_value(value, graph)
                    for key, value in record.items()
                    if key != field_name
                })
            else:
                # Stable public refs use a closed identity recipe rather than
                # the object-content recipe. They must be exact typed values
                # with nonempty independently selected provenance.
                if not isinstance(target, str) or not target or not selected:
                    fail(f"canonical identity reducer input missing: {row['leaf']}")
                continue
            if target != expected:
                fail(f"canonical reducer output mismatch: {row['leaf']}")
    elif operation == "count":
        collection_lengths = [
            len(value)
            for reference_values in selected_by_reference
            for value in reference_values
            if isinstance(value, list)
        ]
        if not collection_lengths or any(
            not isinstance(value, int) for value in target_values
        ):
            fail(f"count reducer input/output mismatch: {row['leaf']}")
    elif operation == "sorted_unique":
        for target in target_values:
            if isinstance(target, list):
                canonical_items = [
                    json.dumps(
                        value,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    for value in target
                ]
                if len(canonical_items) != len(set(canonical_items)):
                    fail(f"sorted-unique reducer output duplicate: {row['leaf']}")
                if (
                    all(not isinstance(value, (dict, list)) for value in target)
                    and target != sorted(target)
                ):
                    fail(f"sorted-unique reducer output order: {row['leaf']}")
    elif operation == "closed_mapping":
        if not row["closed_mapping"] or not selected:
            fail(f"closed mapping reducer has no executed input: {row['leaf']}")
        reducer = row["reducer"]
        domains = [
            "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
            "symptom_efficacy", "protocol_compliance",
        ]

        def flattened(values: Sequence[Any]) -> list[Any]:
            return [
                item
                for value in values
                for item in (value if isinstance(value, list) else [value])
            ]

        if reducer == "type_discriminant":
            if any(value != "r4_source_locator" for value in target_values):
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "closed_bistate":
            nonempty = any(value not in {None, ""} for value in selected)
            expected = "present" if nonempty else "absent"
            if any(value != expected for value in target_values):
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "closed_visibility_state":
            evaluation = set(flattened(selected_by_reference[0]))
            projectable = set(flattened(selected_by_reference[1]))
            hidden = set(flattened(selected_by_reference[2]))
            expected = (
                "projectable"
                if evaluation and evaluation <= projectable and not hidden
                else "hidden"
            )
            if target_values != [expected]:
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "closed_date_state":
            exact_dates = selected_by_reference[0]
            candidates = selected_by_reference[1]
            expected_values = []
            for exact_value, candidate_value in zip(exact_dates, candidates):
                candidate_count = len(candidate_value)
                expected_values.append(
                    "exact" if exact_value not in {None, ""}
                    else "missing" if candidate_count == 0
                    else "partial" if candidate_count == 1
                    else "conflicted"
                )
            if target_values != expected_values:
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "closed_domain_partition_with_typed_decision":
            if field_name == "domain":
                if target_values != domains:
                    fail(f"closed mapping reducer output mismatch: {row['leaf']}")
            elif field_name in {"event_refs", "risk_anchor_refs"}:
                members = selected_by_reference[0]
                member_domains = selected_by_reference[1]
                expected_values = [
                    [member for member, domain in zip(members, member_domains)
                     if domain == expected_domain]
                    for expected_domain in domains
                ]
                if target_values != expected_values:
                    fail(f"closed mapping reducer output mismatch: {row['leaf']}")
            elif field_name == "applicability_state":
                event_members = selected_by_reference[0]
                risk_members = selected_by_reference[1]
                authority_by_domain = dict(zip(
                    selected_by_reference[2], selected_by_reference[3]
                ))
                expected_values = []
                for index, expected_domain in enumerate(domains):
                    if event_members[index] or risk_members[index]:
                        expected_values.append("applicable")
                    else:
                        expected_values.append(
                            authority_by_domain.get(
                                expected_domain, "not_provided"
                            )
                        )
                if target_values != expected_values:
                    fail(f"closed mapping reducer output mismatch: {row['leaf']}")
            else:
                fail(f"closed mapping field unsupported: {row['leaf']}")
        elif reducer == "closed_geometry":
            starts = selected_by_reference[0]
            ends = selected_by_reference[1]

            def endpoint_bounds(endpoint: Mapping[str, Any]) -> tuple[Any, Any]:
                return (
                    endpoint.get("exact_date") or endpoint.get("range_start"),
                    endpoint.get("exact_date") or endpoint.get("range_end"),
                )

            expected_values = []
            for start_endpoint, end_endpoint in zip(starts, ends):
                start_value = endpoint_bounds(start_endpoint)[0]
                end_value = endpoint_bounds(end_endpoint)[1]
                if start_value is not None and end_value is not None:
                    expected_values.append(
                        "point" if start_value == end_value else "closed_interval"
                    )
                elif start_value is not None:
                    expected_values.append("open_end")
                elif end_value is not None:
                    expected_values.append("open_start")
                else:
                    fail(f"closed geometry has no endpoint: {row['leaf']}")
            if target_values != expected_values:
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "closed_subtype_mapping":
            mapped_domains = selected_by_reference[-1]
            if target_values != mapped_domains:
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "closed_visit_kind":
            expected = (
                "actual" if selected_by_reference[1]
                else "nominal" if selected_by_reference[0]
                else "unscheduled"
            )
            if target_values != [expected]:
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "closed_domain_mapping":
            if (
                len(target_values) != len(target_records)
                or any(value not in domains for value in target_values)
            ):
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "accepted_domain_to_risk_type_zh":
            if any(
                not isinstance(value, str) or not value or value.startswith("AUTH-")
                for value in target_values
            ):
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "accepted_risk_severity_conversion":
            if any(value not in {"critical", "high", "medium", "low"}
                   for value in target_values):
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "same_accepted_risk_authority_identity":
            if any(
                not isinstance(value, str) or len(value) != 64
                for value in target_values
            ):
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        elif reducer == "exact_domain_applicability_decision":
            tracked_members = set(flattened(selected_by_reference[1]))
            authority_by_domain = dict(zip(
                selected_by_reference[2], selected_by_reference[3]
            ))
            expected_values = [
                "applicable"
                if record["event_ref"] in tracked_members
                and authority_by_domain.get(record["domain"]) == "applicable"
                else "not_provided"
                for record in target_records
            ]
            if target_values != expected_values:
                fail(f"closed mapping reducer output mismatch: {row['leaf']}")
        else:
            fail(f"closed mapping reducer recipe missing: {row['leaf']}")
    elif operation in {"semantic_sequence", "exact_selection_or_assembly"}:
        if not any(selected_by_reference) and not (
            row["nullable"]
            or all(value is None or value == [] for value in target_values)
            or all(
                reference["selector"]["cardinality"] == "zero_or_one"
                for reference in row["references"]
            )
        ):
            fail(f"reducer has no selected authority input: {row['leaf']}")
    else:
        fail(f"unknown reducer execution operation: {operation}")


def verify_structured_source_join_matrix(
    api: Mapping[str, Any], candidate_matrix: Optional[Mapping[str, Any]] = None,  # noqa: UP045 -- Python 3.9 contract tool
    candidate_fixture_matrix: Optional[Mapping[str, Any]] = None,  # noqa: UP045 -- Python 3.9 contract tool
) -> dict[str, Any]:
    matrix = (
        copy.deepcopy(dict(candidate_matrix))
        if candidate_matrix is not None
        else read_json(ARTIFACT_DIR / "source_join_matrix.json")
    )
    if (
        matrix.get("contract_id") != CONTRACT_ID
        or matrix.get("schema_version") != SCHEMA_VERSION
        or matrix.get("reference_grammar") != api["structured_reference_grammar"]
        or matrix.get("constant_catalog_hash")
        != canonical_hash(api["constant_catalog"])
    ):
        fail("structured source join identity/grammar drift")
    relation_clauses = [
        clause
        for row in matrix.get("rows", [])
        for reference in row.get("references", [])
        for clause in reference.get("selector", {}).get("predicate", {}).get(
            "clauses", []
        )
    ]
    label_field_mismatches = sum(
        clause.get("join_key")
        != clause.get("lhs", {}).get("owner", "")
        + "."
        + ".".join(clause.get("lhs", {}).get("path", []))
        for clause in relation_clauses
    )
    closure = matrix.get("closure", {})
    if (
        closure.get("historical_reviewer_v7_label_field_mismatch_count")
        != 1168
        or closure.get(
            "historical_reviewer_v8_future_or_self_key_component_count"
        ) != 207
        or closure.get("historical_reviewer_v8_affected_leaf_count") != 69
        or closure.get("current_label_field_mismatch_count")
        != label_field_mismatches
        or label_field_mismatches != 0
        or closure.get("terminal_copy_key_violation_count") != 0
        or closure.get("relation_key_component_count")
        != len(relation_clauses)
    ):
        fail("structured relation-key mismatch accounting drift")
    schemas = {
        SUBJECT_CONTRACT_ID: read_json(
            PUBLIC_ARTIFACT_DIR / "subject_temporal_schema.json"
        ),
        AEMH_CONTRACT_ID: read_json(
            PUBLIC_ARTIFACT_DIR / "aemh_match_history_schema.json"
        ),
    }
    collection_catalog = api.get("collection_relation_key_catalog", {})
    expected_collection_fields: dict[str, set[str]] = {}
    for authority in api["join_key_authority_catalog"].values():
        for component in authority["components"]:
            key_reference = component["authority_reference"]
            expected_collection_fields.setdefault(
                key_reference["terminal"]["owner"], set()
            ).add(key_reference["segments"][-1]["field"])
    if set(collection_catalog) != set(expected_collection_fields):
        fail("collection relation-key owner coverage drift")
    for owner, fields in expected_collection_fields.items():
        expected_self_keys = [
            terminal
            for terminal in api["structured_reference_grammar"][
                "legal_self_key_terminals"
            ]
            if terminal.startswith(owner + ".")
        ]
        if collection_catalog[owner] != {
            "real_identity_or_ref_fields": sorted(fields),
            "value_terminal_exclusion_required_except_exact_legal_self_key": True,
            "legal_self_key_terminals": expected_self_keys,
            "composite_components_all_compared": True,
        }:
            fail(f"collection relation-key catalog drift: {owner}")
    fixture_matrix = (
        copy.deepcopy(dict(candidate_fixture_matrix))
        if candidate_fixture_matrix is not None
        else read_json(ARTIFACT_DIR / "test_matrix.json")
    )
    expected = {
        (contract, f"{owner}.{field_name}")
        for contract, schema in schemas.items()
        for owner, fields in schema["objects"].items()
        for field_name in fields
    }
    rows = matrix.get("rows", [])
    observed = [(row.get("contract"), row.get("leaf")) for row in rows]
    if len(rows) != 272 or matrix.get("row_count") != 272:
        fail("structured source join row count mismatch")
    if len(observed) != len(set(observed)) or set(observed) != expected:
        fail("structured source join leaf coverage mismatch")
    row_by_leaf = {(row["contract"], row["leaf"]): row for row in rows}
    expected_row_keys = {
        "build_order",
        "abstract_derivation_join_keys",
        "cardinality",
        "closed_mapping",
        "component_comparison_provenance",
        "contract",
        "derivation",
        "fallback",
        "fixture_or_artifact_authority",
        "join_keys",
        "leaf",
        "nullable",
        "ordering",
        "output_semantic_class",
        "reducer_execution_op",
        "reducer_input_provenance",
        "reducer",
        "reference_cardinalities",
        "reference_semantic_classes",
        "references",
        "unavailable_fail_closed_code",
        "unavailable_fail_closed_priority",
        "target_output_provenance",
    }
    orders: dict[str, set[int]] = {
        SUBJECT_CONTRACT_ID: set(),
        AEMH_CONTRACT_ID: set(),
    }
    future_or_self_key_components: set[tuple[str, str, int]] = set()
    projection_or_hash_output_key_components: set[tuple[str, str, int]] = set()
    priority_by_code = {
        item["code"]: item["priority"]
        for item in read_json(ARTIFACT_DIR / "invariant_error_matrix.json")[
            "deterministic_priority"
        ]
    }
    for row in rows:
        if set(row) != expected_row_keys:
            fail(f"structured source join row keys drift: {row.get('leaf')}")
        contract = row["contract"]
        order = row["build_order"]
        if not isinstance(order, int) or order in orders[contract]:
            fail(f"structured source join build order duplicate: {row['leaf']}")
        orders[contract].add(order)
        owner, field_name = row["leaf"].split(".", 1)
        output_spec = schemas[contract]["objects"][owner][field_name]
        if (
            row["cardinality"] != output_spec["cardinality"]
            or row["nullable"] is not output_spec["nullable"]
            or row["output_semantic_class"]
            != _semantic_class(field_name, output_spec["type"])
            or not row["join_keys"]
            or not row["references"]
            or len(row["references"]) != len(row["reference_semantic_classes"])
            or len(row["references"]) != len(row["reference_cardinalities"])
            or row["fallback"] != "fail_closed_no_nearest"
            or row["fixture_or_artifact_authority"] is not False
        ):
            fail(f"structured source join leaf contract drift: {row['leaf']}")
        if not _semantic_compatible(
            row["output_semantic_class"],
            row["reference_semantic_classes"],
            row["reducer"],
        ):
            fail(f"structured source join semantic incompatibility: {row['leaf']}")
        authority = api["join_key_authority_catalog"][
            f"{contract}::{row['leaf']}"
        ]
        expected_provenance = [
            {
                "authority_key": component["authority_key"],
                "authority_reference": component["authority_reference"],
                "context_reference": component["context_reference"],
                "context_component_key": component["context_component_key"],
                "comparison": "canonical_json_equal",
            }
            for component in authority["components"]
        ]
        if (
            row["component_comparison_provenance"] != expected_provenance
            or row["target_output_provenance"]
            != {
                "root": (
                    "subject_current"
                    if contract == SUBJECT_CONTRACT_ID
                    else "aemh_current"
                ),
                "owner": owner,
                "field": field_name,
            }
            or row["unavailable_fail_closed_priority"]
            != priority_by_code[row["unavailable_fail_closed_code"]]
        ):
            fail(f"join execution provenance/priority drift: {row['leaf']}")
        for component_index, component in enumerate(authority["components"]):
            for side in ("authority_reference", "context_reference"):
                key_reference = component[side]
                if key_reference["kind"] != "output":
                    continue
                target_field = row["leaf"].split(".", 1)[1]
                if (
                    target_field.endswith("_hash")
                    or "projection" in target_field
                ):
                    projection_or_hash_output_key_components.add(
                        (contract, row["leaf"], component_index)
                    )
                key_leaf = (
                    key_reference["terminal"]["owner"]
                    + "."
                    + key_reference["segments"][-1]["field"]
                )
                dependency = row_by_leaf[(contract, key_leaf)]
                if dependency["build_order"] >= order:
                    future_or_self_key_components.add(
                        (contract, row["leaf"], component_index)
                    )
        selected_branch_members = 0
        selected_by_reference: list[list[Any]] = []
        for reference_index, (
            reference, declared_semantic, declared_cardinality
        ) in enumerate(zip(
            row["references"],
            row["reference_semantic_classes"],
            row["reference_cardinalities"],
        )):
            kind = reference.get("kind")
            root = reference.get("root")
            if kind in {"source", "controlled"}:
                expected_root = (
                    "subject_source"
                    if contract == SUBJECT_CONTRACT_ID
                    else "aemh_source"
                )
                if root != expected_root:
                    fail(f"structured source root drift: {row['leaf']}")
                resolved_owner, resolved_type = _resolve_structured_source_ref(
                    reference, api
                )
            elif kind == "previous":
                if contract != AEMH_CONTRACT_ID or root != "aemh_previous":
                    fail(f"structured previous root drift: {row['leaf']}")
                resolved_owner, resolved_type = _resolve_structured_object_ref(
                    reference, schemas[contract]
                )
            elif kind == "output":
                expected_root = (
                    "subject_current"
                    if contract == SUBJECT_CONTRACT_ID
                    else "aemh_current"
                )
                if root != expected_root:
                    fail(f"structured output root drift: {row['leaf']}")
                resolved_owner, resolved_type = _resolve_structured_object_ref(
                    reference, schemas[contract]
                )
                dependency = row_by_leaf[(
                    contract,
                    f"{resolved_owner}.{reference['segments'][-1]['field']}",
                )]
                if dependency["build_order"] >= order:
                    fail(f"structured output forward dependency: {row['leaf']}")
            elif kind == "constant":
                if root != "constant_catalog" or len(reference["segments"]) != 1:
                    fail(f"structured constant path drift: {row['leaf']}")
                name = reference["segments"][0]["field"]
                constant = api["constant_catalog"].get(name)
                if (
                    constant is None
                    or reference["segments"][0]["expand"] != "one"
                    or reference.get("constant_hash")
                    != constant["canonical_hash"]
                ):
                    fail(f"structured constant drift: {row['leaf']}")
                resolved_owner, resolved_type = "constant_catalog", constant["type"]
            else:
                fail(f"structured reference kind unknown: {kind}")
            terminal = reference.get("terminal")
            if terminal != {"owner": resolved_owner, "type": resolved_type}:
                fail(f"structured reference terminal drift: {row['leaf']}")
            source_field = reference["segments"][-1]["field"]
            independently_derived = (
                "frozen_constant"
                if kind == "constant"
                else _semantic_class(
                    source_field, _normalized_terminal_type(resolved_type)
                )
            )
            if declared_semantic != independently_derived:
                fail(f"structured source semantic-class drift: {row['leaf']}")
            if reference["selector"]["cardinality"] != declared_cardinality:
                fail(f"structured reference cardinality drift: {row['leaf']}")
            fixture = fixture_matrix["fixture_catalog"][
                "subject_base"
                if contract == SUBJECT_CONTRACT_ID
                else "aemh_base"
            ]
            selected_values = _execute_structured_selector(
                reference,
                row,
                fixture,
                api,
                matrix["reference_grammar"],
            )
            selected_by_reference.append(selected_values)
            selected_branch_members += len(selected_values)
            if row["reducer_input_provenance"][reference_index] != {
                "reference_index": reference_index,
                "terminal": reference["terminal"],
                "selector_cardinality": reference["selector"]["cardinality"],
            }:
                fail(f"reducer input provenance drift: {row['leaf']}")
        _execute_join_reducer(row, selected_by_reference, fixture)
    for contract, schema in schemas.items():
        expected_orders = set(range(sum(len(fields) for fields in schema["objects"].values())))
        if orders[contract] != expected_orders:
            fail(f"structured source build order is not contiguous: {contract}")
    if (
        future_or_self_key_components
        or closure.get("current_future_or_self_key_dependency_count") != 0
        or projection_or_hash_output_key_components
        or closure.get(
            "current_projection_or_hash_output_key_dependency_count"
        ) != 0
    ):
        fail("structured relation-key future/self dependency closure drift")
    return matrix


def verify_invariant_error_matrix() -> set[str]:
    matrix = read_json(ARTIFACT_DIR / "invariant_error_matrix.json")
    subject = read_json(PUBLIC_ARTIFACT_DIR / "subject_temporal_schema.json")
    aemh = read_json(PUBLIC_ARTIFACT_DIR / "aemh_match_history_schema.json")
    union: list[str] = []
    for code in subject["error_codes"] + aemh["error_codes"]:
        if code not in union:
            union.append(code)
    if len(union) != 81 or matrix["error_union_count"] != 81:
        fail("accepted error union must contain exactly 81 codes")
    rows = matrix["deterministic_priority"]
    if [row["code"] for row in rows] != union:
        fail("error priority order does not equal accepted deterministic union")
    if [row["priority"] for row in rows] != list(range(1, 82)):
        fail("error priorities must be exact contiguous 1..81")
    if len({row["trigger"] for row in rows}) != 81:
        fail("every error code must have a unique concrete trigger")
    for row in rows:
        if not row["trigger"] or not row["path_pattern"] or not row["precedence"]:
            fail(f"error trigger/path/precedence missing: {row['code']}")
        if row["precedence"] != (
            f"priority {row['priority']}; structural/type/identity/source/date/history "
            "evaluation follows this frozen union order and this code precedes every "
            "code with a larger number"
        ):
            fail(f"error precedence drift: {row['code']}")
    if matrix["priority_algorithm"] != (
        "collect all issues, then sort by (priority,path,code,message); primary_code is first or null"
    ):
        fail("deterministic issue priority algorithm mismatch")
    expected_invariants = {
        (contract, text)
        for contract, schema in (
            (SUBJECT_CONTRACT_ID, subject),
            (AEMH_CONTRACT_ID, aemh),
        )
        for text in schema["invariants"]
    }
    actual_invariants = {
        (row["contract"], row["text"]) for row in matrix["accepted_invariants"]
    }
    if actual_invariants != expected_invariants:
        fail("accepted invariant projection mismatch")
    return set(union)


def _case_lookup(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        case_id = row["case_id"]
        if case_id in result:
            fail(f"duplicate case id: {case_id}")
        result[case_id] = row
    return result


def _output_class_specs(api: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        item["name"]: item
        for module in api["modules"].values()
        for item in module["output_classes"]
    }


def _resolve_runtime_typed_path(
    api: Mapping[str, Any], contract: str, path: str
) -> tuple[bool, str]:
    inputs = _input_class_specs(api)
    outputs = _output_class_specs(api)
    module_meta = _source_module_metadata_catalog()
    parts = path.split(".")
    if not parts:
        return False, "empty"
    if parts[0] == "source":
        current_type = (
            "SubjectTemporalSourceBundle"
            if contract == SUBJECT_CONTRACT_ID
            else "AEMHMatchHistorySourceBundle"
        )
    elif parts[0] == "candidate":
        current_type = (
            "SubjectTemporalAuthorityPacket"
            if contract == SUBJECT_CONTRACT_ID
            else "AEMHMatchHistoryAuthorityPacket"
        )
    else:
        return False, "root"
    path_segments = parts[1:]
    for index, raw_segment in enumerate(path_segments):
        is_last = index == len(path_segments) - 1
        expands_many = raw_segment.endswith("[]")
        segment = raw_segment[:-2] if expands_many else raw_segment
        aliases: Mapping[str, str] = {}
        if current_type in inputs:
            annotation = dict(inputs[current_type]["fields"]).get(segment)
            current_module = ""
        elif current_type in outputs:
            fields = {
                item["name"]: item
                for item in outputs[current_type]["exact_serialized_fields"]
            }
            field = fields.get(segment)
            annotation = field["type"] if field is not None else None
            current_module = ""
            cardinality = field.get("cardinality") if field is not None else None
            if cardinality == "many" and not expands_many and not is_last:
                return False, f"missing expansion:{segment}"
            many = cardinality == "many"
        elif "." in current_type:
            current_module, class_name = current_type.rsplit(".", 1)
            classes, aliases = module_meta.get(current_module, ({}, {}))
            annotation = classes.get(class_name, {}).get(segment)
        else:
            return False, f"unknown type:{current_type}"
        if annotation is None:
            return False, f"field:{current_type}.{segment}"
        terminal, annotation_many, _optional = _annotation_info(annotation)
        if current_type in outputs:
            annotation_many = many
        if (
            current_type in inputs or "." in current_type
        ) and expands_many != annotation_many and not (
            is_last and annotation_many and not expands_many
        ):
            return False, f"expansion:{current_type}.{segment}"
        current_type = _resolve_type_name(
            terminal, current_module, aliases, set(inputs) | set(outputs)
        )
    return True, current_type


def _apply_json_pointer(document: dict[str, Any], pointer: str, value: Any) -> None:
    if not pointer.startswith("/"):
        fail(f"invalid fixture JSON pointer: {pointer}")
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]
    target: Any = document
    for part in parts[:-1]:
        if isinstance(target, list):
            target = target[int(part)]
        else:
            target = target[part]
    final = parts[-1]
    if isinstance(target, list):
        target[int(final)] = value
    else:
        target[final] = value


def _fixture_spec_issues(
    row: Mapping[str, Any],
    api: Mapping[str, Any],
    trigger_by_code: Mapping[str, str],
) -> list[str]:
    case_id = str(row["case_id"])
    issues: list[str] = []
    payload = row.get("typed_fixture_payload", {})
    adapter = row.get("typed_mutation_adapter", {})
    contract = str(row["contract"])
    expected_root = (
        "SubjectTemporalSourceBundle"
        if contract == SUBJECT_CONTRACT_ID
        else "AEMHMatchHistorySourceBundle"
    )
    if payload.get("schema") != "public-authority-exact-typed-fixture-payload-v0.1":
        issues.append(f"fixture schema:{case_id}")
    if payload.get("fixture_id") != f"fixture::{case_id}" or payload.get(
        "root_type"
    ) != expected_root:
        issues.append(f"fixture identity:{case_id}")
    root_spec = _input_class_specs(api)[expected_root]
    expected_fields = [
        (name, declared_type) for name, declared_type in root_spec["fields"]
    ]
    observed_fields = [
        (item.get("name"), item.get("declared_type"))
        for item in payload.get("root_fields", [])
    ]
    if observed_fields != expected_fields:
        issues.append(f"fixture fields:{case_id}")
    for item in payload.get("root_fields", []):
        value = item.get("constructor_value", {})
        if value != {
            "kind": "typed_fixture_node",
            "type": item.get("declared_type"),
            "fixture_node_ref": f"{case_id}::{item.get('name')}",
        }:
            issues.append(f"fixture constructor:{case_id}:{item.get('name')}")
    if payload.get("reachable_external_types") != api["source_type_access_paths"][contract]:
        issues.append(f"fixture reachable types:{case_id}")
    slot = payload.get("mutation_slot", {})
    typed_path = adapter.get("typed_target_path")
    if slot.get("typed_source_or_candidate_path") != typed_path:
        issues.append(f"fixture adapter target:{case_id}")
    resolved, reason = _resolve_runtime_typed_path(api, contract, str(typed_path))
    if not resolved:
        issues.append(f"fixture target unresolved:{case_id}:{reason}")
    if adapter.get("schema") != "public-authority-typed-mutation-adapter-v0.1":
        issues.append(f"adapter schema:{case_id}")
    if adapter.get("accepted_abstract_mutation") != row.get("single_mutation"):
        issues.append(f"adapter accepted mutation:{case_id}")
    expected_kind = "candidate" if str(typed_path).startswith("candidate.") else "source"
    if adapter.get("target_kind") != expected_kind:
        issues.append(f"adapter kind:{case_id}")
    steps = adapter.get("typed_constructor_steps", [])
    if len(steps) != 5 or not all(isinstance(step, str) and step for step in steps):
        issues.append(f"adapter constructor steps:{case_id}")
    pointer = adapter.get("fixture_json_pointer")
    if pointer != "/mutation_slot/current_value":
        issues.append(f"adapter pointer:{case_id}")
    else:
        executable = copy.deepcopy(dict(payload))
        before = executable["mutation_slot"]["current_value"]
        _apply_json_pointer(executable, pointer, adapter.get("mutated_value_token"))
        if executable["mutation_slot"]["current_value"] == before:
            issues.append(f"adapter did not mutate:{case_id}")
    expected_code = row.get("expected_error_code")
    expected_trigger = (
        "positive control produces typed packet and stable canonical hash"
        if expected_code is None
        else trigger_by_code.get(str(expected_code))
    )
    if adapter.get("expected_error_code") != expected_code or adapter.get(
        "detector_trigger"
    ) != expected_trigger:
        issues.append(f"adapter detector:{case_id}")
    oracle = row.get("mechanical_oracle", {})
    expected_packet = (
        "SubjectTemporalAuthorityPacket"
        if contract == SUBJECT_CONTRACT_ID
        else "AEMHMatchHistoryAuthorityPacket"
    )
    expected_invocation = (
        "validate_subject_temporal_authority(candidate, source)"
        if contract == SUBJECT_CONTRACT_ID
        else "validate_aemh_match_history_authority(candidate, source, previous_packet)"
    )
    disposition = row.get("expected_disposition")
    if (
        oracle.get("candidate_type") != expected_packet
        or oracle.get("validator_invocation") != expected_invocation
        or oracle.get("expected_error_code") != expected_code
        or oracle.get("packet_required") is not (disposition == "accept")
        or oracle.get("packet_forbidden") is not (disposition != "accept")
        or oracle.get("canonical_hash_required") is not True
    ):
        issues.append(f"mechanical oracle:{case_id}")
    for probe in row.get("named_secondary_executable_error_probes", []):
        code = probe.get("code")
        resolved, reason = _resolve_runtime_typed_path(
            api, contract, str(probe.get("typed_target_path"))
        )
        if not resolved:
            issues.append(f"secondary target:{case_id}:{reason}")
        if (
            probe.get("fixture_json_pointer") != "/mutation_slot/current_value"
            or probe.get("oracle") != trigger_by_code.get(str(code))
            or not probe.get("mutated_value_token")
        ):
            issues.append(f"secondary probe:{case_id}:{code}")
    return issues


def _test_matrix_validation_issues(
    matrix: Mapping[str, Any],
    registry: Mapping[str, Any],
    error_codes: set[str],
    api: Mapping[str, Any],
    trigger_by_code: Mapping[str, str],
) -> list[str]:
    issues: list[str] = []
    counts = matrix["counts"]
    expected_counts = {
        "future_runtime_spec_total": 236,
        "subject_inherited": 48,
        "subject_producer_specific": 95,
        "aemh_inherited": 16,
        "aemh_producer_specific": 77,
        "contract_verifier_governance": 22,
    }
    if counts != expected_counts:
        issues.append("counts")
    runtime = matrix["future_runtime_specs"]
    governance = matrix["contract_verifier_governance_cases"]
    if len(runtime) != 236 or len(governance) != 22:
        issues.append("materialized counts")
    runtime_by_id = _case_lookup(runtime)
    governance_by_id = _case_lookup(governance)
    accepted_inherited = _case_lookup(registry["inherited_cases"])
    accepted_specific = _case_lookup(registry["public_authority_specific_cases"])
    expected_runtime_ids = set(accepted_inherited) | {
        case_id
        for case_id, row in accepted_specific.items()
        if row["contract"] in {SUBJECT_CONTRACT_ID, AEMH_CONTRACT_ID}
    }
    expected_governance_ids = set(accepted_specific) - expected_runtime_ids
    if set(runtime_by_id) != expected_runtime_ids:
        issues.append("runtime ids")
    if set(governance_by_id) != expected_governance_ids:
        issues.append("governance ids")
    observed_coverage: dict[str, list[str]] = {code: [] for code in error_codes}
    semantic_keys: list[str] = []
    for row in runtime:
        issues.extend(_fixture_spec_issues(row, api, trigger_by_code))
        if row["mutation_count"] != 1 or not isinstance(row["single_mutation"], dict):
            issues.append(f"mutation:{row['case_id']}")
        if "runtime_fixtures." not in row["typed_fixture"]:
            issues.append(f"fixture:{row['case_id']}")
        if not row["forbidden_audience_output"]:
            issues.append(f"forbidden output:{row['case_id']}")
        oracle = row["non_llm_oracle"].lower()
        if not all(token in oracle for token in ("typed", "builder", "validator", "hash")):
            issues.append(f"oracle:{row['case_id']}")
        if row["case_id_branching_forbidden"] is not True:
            issues.append(f"branch ban:{row['case_id']}")
        source = accepted_inherited.get(row["case_id"]) or accepted_specific.get(
            row["case_id"]
        )
        if source is None:
            issues.append(f"missing source:{row['case_id']}")
            continue
        if row["accepted_registry_row"] != source:
            issues.append(f"accepted row drift:{row['case_id']}")
        disposition, accepted_payload = str(
            source["expected_typed_outcome_or_error"]
        ).split(":", 1)
        if row["expected_disposition"] != disposition:
            issues.append(f"polarity:{row['case_id']}")
        if row["expected_projection"] != source["stage_oracle_contract"][
            "expected_projection"
        ]:
            issues.append(f"projection:{row['case_id']}")
        if disposition == "accept":
            expected_packet = (
                "SubjectTemporalAuthorityPacket"
                if row["contract"] == SUBJECT_CONTRACT_ID
                else "AEMHMatchHistoryAuthorityPacket"
            )
            if (
                row["case_id"] not in INHERITED_ACCEPT_CASES
                or row["expected_error_code"] is not None
                or row["expected_packet_type"] != expected_packet
                or not row["expected_projection_hash_oracle"]
                or accepted_payload not in row["expected_projection_hash_oracle"]
            ):
                issues.append(f"accepted oracle:{row['case_id']}")
        else:
            if (
                row["expected_error_code"] not in error_codes
                or row["expected_packet_type"] is not None
                or row["expected_projection_hash_oracle"] is not None
            ):
                issues.append(f"rejected oracle:{row['case_id']}")
            else:
                observed_coverage[row["expected_error_code"]].append(row["case_id"])
        for probe in row.get("named_secondary_executable_error_probes", []):
            code = probe.get("code")
            if code not in error_codes:
                issues.append(f"secondary unknown code:{row['case_id']}:{code}")
            else:
                observed_coverage[code].append(probe["probe_id"])
        if row["fully_reseal_after_mutation"] != source.get(
            "fully_reseal_after_mutation"
        ):
            issues.append(f"reseal flag:{row['case_id']}")
        recipe = row["canonical_reseal_recipe"]
        if source.get("fully_reseal_after_mutation") is True:
            required_hashes = {
                "projection_id",
                "projection_content_hash",
                "receipt_id",
                "receipt_content_hash",
                "packet_content_hash",
            }
            if (
                recipe.get("mode") != "fully_reseal_after_mutation"
                or not recipe.get("steps")
                or not required_hashes.issubset(set(recipe.get("hashes_recomputed", [])))
            ):
                issues.append(f"reseal recipe:{row['case_id']}")
        elif row["origin_projection"] == "accepted_public_contract_specific" and (
            recipe.get("mode") != "not_applied_stale_hash_control"
            or recipe.get("steps")
            or recipe.get("hashes_recomputed")
        ):
            issues.append(f"stale-hash recipe:{row['case_id']}")
        semantic_payload = {
            "single_mutation": row["single_mutation"],
            "typed_fixture": row["typed_fixture"],
            "canonical_reseal_recipe": recipe,
            "expected_typed_outcome_or_error": row[
                "expected_typed_outcome_or_error"
            ],
        }
        expected_key = canonical_hash(semantic_payload)
        if row["semantic_independence_key"] != expected_key:
            issues.append(f"semantic key:{row['case_id']}")
        semantic_keys.append(expected_key)
    if sum(row["fully_reseal_after_mutation"] is True for row in runtime) != 116:
        issues.append("fully resealed count")
    if len(semantic_keys) != len(set(semantic_keys)):
        issues.append("semantic duplicates")
    for left, right in (("PA-034", "PA-120"), ("PA-035", "PA-121")):
        if runtime_by_id[left]["semantic_independence_key"] == runtime_by_id[right][
            "semantic_independence_key"
        ]:
            issues.append(f"paired semantic duplicate:{left}/{right}")
    for case_id, row in governance_by_id.items():
        source = accepted_specific[case_id]
        if row["accepted_registry_row"] != source:
            issues.append(f"governance source drift:{case_id}")
        disposition, code = str(source["expected_typed_outcome_or_error"]).split(
            ":", 1
        )
        if disposition != "reject" or row["expected_error_code"] != code:
            issues.append(f"governance outcome drift:{case_id}")
        if code not in error_codes:
            issues.append(f"governance unknown code:{case_id}")
        else:
            observed_coverage[code].append(case_id)
        for probe in row["named_executable_error_probes"]:
            if (
                not probe.get("probe_id")
                or probe.get("code") not in error_codes
                or not probe.get("single_mutation")
                or not probe.get("oracle")
            ):
                issues.append(f"invalid probe:{case_id}")
            else:
                observed_coverage[probe["code"]].append(probe["probe_id"])
        if row["contract"] not in {
            "exact-overlay-v0.1",
            "source-matrix-v0.1",
            "manifest-v0.1",
        }:
            issues.append(f"governance owner:{case_id}")
    if matrix["error_code_executable_coverage"] != observed_coverage:
        issues.append("error coverage drift")
    if any(not locators for locators in observed_coverage.values()):
        issues.append("error coverage incomplete")
    execution = matrix["execution_contract"]
    if execution.get("fully_resealed_runtime_case_count") != 116 or not all(
        value is True
        for key, value in execution.items()
        if key != "fully_resealed_runtime_case_count"
    ):
        issues.append("execution contract")
    return issues


def verify_test_matrix(
    error_codes: set[str], api: Mapping[str, Any], trigger_by_code: Mapping[str, str]
) -> dict[str, Any]:
    matrix = read_json(ARTIFACT_DIR / "test_matrix.json")
    registry = read_json(PUBLIC_ARTIFACT_DIR / "challenge_registry.json")
    issues = _test_matrix_validation_issues(
        matrix, registry, error_codes, api, trigger_by_code
    )
    if issues:
        fail(f"test matrix invalid: {issues[:8]}")
    return matrix


def _independent_constructor_catalog() -> dict[str, Any]:
    classes: dict[str, Any] = {}
    enums: dict[str, list[str]] = {}
    aliases_by_module: dict[str, dict[str, str]] = {}
    for module, relative in SOURCE_MODULE_PATHS.items():
        path = ROOT / relative
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
            feature_version=(3, 9),
        )
        aliases: dict[str, str] = {}
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name.split(".", 1)[0]] = alias.name
            elif isinstance(node, ast.ImportFrom):
                imported = node.module or ""
                if node.level:
                    prefix = module.split(".")[:-node.level]
                    imported = ".".join([*prefix, imported]).rstrip(".")
                for alias in node.names:
                    aliases[alias.asname or alias.name] = (
                        f"{imported}.{alias.name}".strip(".")
                    )
        aliases_by_module[module] = aliases
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            qualified = f"{module}.{node.name}"
            fields = [
                [item.target.id, ast.unparse(item.annotation)]
                for item in node.body
                if isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
            ]
            if fields:
                classes[qualified] = {
                    "module": module,
                    "name": node.name,
                    "fields": fields,
                    "exact_fields": True,
                }
            if any(
                _dotted_name(base).split(".")[-1] in {"Enum", "StrEnum"}
                for base in node.bases
            ):
                members = [
                    item.targets[0].id
                    for item in node.body
                    if isinstance(item, ast.Assign)
                    and len(item.targets) == 1
                    and isinstance(item.targets[0], ast.Name)
                    and not item.targets[0].id.startswith("_")
                ]
                enums[qualified] = members
    return {
        "aliases_by_module": aliases_by_module,
        "classes": classes,
        "enums": enums,
    }


def _fixture_node_refs(value: Any) -> list[str]:
    if isinstance(value, dict):
        if set(value) == {"node_ref"} and isinstance(value["node_ref"], str):
            return [value["node_ref"]]
        result: list[str] = []
        for child in value.values():
            result.extend(_fixture_node_refs(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(_fixture_node_refs(child))
        return result
    return []


def _fixture_reachable(graph: Mapping[str, Any], root_name: str) -> set[str]:
    root = graph["roots"][root_name]
    if root is None:
        return set()
    pending = [root["node_ref"]]
    found: set[str] = set()
    while pending:
        node_id = pending.pop()
        if node_id in found:
            continue
        if node_id not in graph["nodes"]:
            fail(f"fixture dangling node: {node_id}")
        found.add(node_id)
        for value in graph["nodes"][node_id]["fields"].values():
            pending.extend(_fixture_node_refs(value))
    return found


def _annotation_parts(annotation: str) -> tuple[str, list[str]]:
    compact = annotation.replace(" ", "")
    if "[" not in compact or not compact.endswith("]"):
        return "scalar", [compact]
    outer, inner = compact.split("[", 1)
    inner = inner[:-1]
    depth = 0
    parts: list[str] = []
    start = 0
    for index, character in enumerate(inner):
        if character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
        elif character == "," and depth == 0:
            parts.append(inner[start:index])
            start = index + 1
    parts.append(inner[start:])
    return outer.split(".")[-1].lower(), parts


def _resolve_fixture_type(type_name: str, module: str, api: Mapping[str, Any]) -> str:
    catalog = api["constructor_type_catalog"]
    if type_name in _input_class_specs(api) or type_name in catalog["classes"]:
        return type_name
    if type_name in catalog["enums"]:
        return type_name
    if "." in type_name:
        first, rest = type_name.split(".", 1)
        alias = catalog["aliases_by_module"].get(module, {}).get(first)
        return f"{alias}.{rest}" if alias else type_name
    alias = catalog["aliases_by_module"].get(module, {}).get(type_name)
    if alias:
        return alias
    local = f"{module}.{type_name}" if module else type_name
    return local if local in catalog["classes"] or local in catalog["enums"] else type_name


def _validate_constructor_value(
    value: Any,
    annotation: str,
    module: str,
    graph: Mapping[str, Any],
    api: Mapping[str, Any],
    inline_allowed: bool = False,
) -> None:
    kind, arguments = _annotation_parts(annotation)
    if kind in {"optional", "union"}:
        non_none = [item for item in arguments if item not in {"None", "NoneType"}]
        if value is None:
            return
        if len(non_none) != 1:
            fail(f"fixture unsupported union: {annotation}")
        _validate_constructor_value(value, non_none[0], module, graph, api, inline_allowed)
        return
    if kind in {"tuple", "list", "sequence"}:
        wrapper = "tuple" if kind == "tuple" else "list"
        if not isinstance(value, dict) or set(value) != {wrapper}:
            fail(f"fixture container encoding mismatch: {annotation}")
        member = arguments[0]
        for item in value[wrapper]:
            _validate_constructor_value(item, member, module, graph, api, inline_allowed)
        return
    if kind in {"dict", "mapping"}:
        if not isinstance(value, dict) or set(value) != {"mapping"} or not isinstance(
            value["mapping"], list
        ):
            fail(f"fixture mapping encoding mismatch: {annotation}")
        return
    if kind == "initvar":
        if value is not None:
            fail("fixture InitVar must be None")
        return
    type_name = _resolve_fixture_type(arguments[0], module, api)
    catalog = api["constructor_type_catalog"]
    inputs = _input_class_specs(api)
    if type_name in inputs or type_name in catalog["classes"]:
        if isinstance(value, dict) and set(value) == {"node_ref"}:
            node = graph["nodes"].get(value["node_ref"])
            if node is None or node["type"] != type_name:
                fail(f"fixture node type mismatch: {type_name}")
            return
        if inline_allowed and isinstance(value, dict) and set(value) == {"type", "fields"}:
            if value["type"] != type_name:
                fail(f"inline constructor type mismatch: {type_name}")
            _validate_fixture_node(value, graph, api, inline_allowed=True)
            return
        fail(f"fixture constructor reference required: {type_name}")
    if type_name in catalog["enums"]:
        expected = {"type": type_name}
        if not isinstance(value, dict) or set(value) != {"enum"}:
            fail(f"fixture enum encoding mismatch: {type_name}")
        enum = value["enum"]
        if enum.get("type") != expected["type"] or enum.get("member") not in catalog[
            "enums"
        ][type_name]:
            fail(f"fixture enum member invalid: {type_name}")
        return
    primitive = type_name.split(".")[-1]
    if primitive in {"Any", "object"}:
        return
    if primitive in {"str", "string", "sha256"} and not isinstance(value, str):
        fail(f"fixture string primitive mismatch: {type_name}")
    if primitive in {"int", "integer"} and (
        not isinstance(value, int) or isinstance(value, bool)
    ):
        fail(f"fixture integer primitive mismatch: {type_name}")
    if primitive in {"float", "number"} and (
        not isinstance(value, (int, float)) or isinstance(value, bool)
    ):
        fail(f"fixture numeric primitive mismatch: {type_name}")
    if primitive in {"bool", "boolean"} and not isinstance(value, bool):
        fail(f"fixture boolean primitive mismatch: {type_name}")


def _output_schema_for_type(type_name: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    for filename in ("subject_temporal_schema.json", "aemh_match_history_schema.json"):
        schema = read_json(PUBLIC_ARTIFACT_DIR / filename)
        if type_name in schema["objects"]:
            return schema["objects"][type_name], schema
    fail(f"fixture output type unknown: {type_name}")
    return {}, {}


def _validate_fixture_node(
    node: Mapping[str, Any],
    graph: Mapping[str, Any],
    api: Mapping[str, Any],
    inline_allowed: bool = False,
) -> None:
    if set(node) != {"type", "fields"} or not isinstance(node["fields"], dict):
        fail("fixture node exact keys mismatch")
    type_name = node["type"]
    inputs = _input_class_specs(api)
    catalog = api["constructor_type_catalog"]
    closed: Mapping[str, Any] = {}
    if type_name in inputs:
        fields = dict(inputs[type_name]["fields"])
        module = ""
        closed = inputs[type_name].get("closed_values", {})
    elif type_name in catalog["classes"]:
        spec = catalog["classes"][type_name]
        fields = dict(spec["fields"])
        module = spec["module"]
    else:
        output_fields, schema = _output_schema_for_type(type_name)
        fields = {
            name: (
                f"tuple[{spec['type']}, ...]"
                if spec["cardinality"] == "many"
                else f"Optional[{spec['type']}]"
                if spec["nullable"]
                else spec["type"]
            )
            for name, spec in output_fields.items()
        }
        module = ""
        for field_name, spec in output_fields.items():
            if spec["type"].startswith("enum:"):
                enum_name = spec["type"].split(":", 1)[1]
                enum_value = node["fields"].get(field_name)
                if enum_value is not None and enum_value not in schema["enums"][enum_name]:
                    fail(f"fixture output closed enum invalid: {type_name}.{field_name}")
                fields[field_name] = "Optional[str]" if spec["nullable"] else "str"
    if set(node["fields"]) != set(fields):
        fail(f"fixture exact fields mismatch: {type_name}")
    for field_name, annotation in fields.items():
        value = node["fields"][field_name]
        if field_name in closed and value not in closed[field_name]:
            fail(f"fixture closed value invalid: {type_name}.{field_name}")
        if field_name in {
            "actual_date",
            "anchor_end",
            "anchor_start",
            "clinical_event_cutoff",
            "data_cutoff",
            "end",
            "snapshot_as_of",
            "start",
            "valid_from",
        } and value is not None and value != "":
            if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
                fail(
                    "PUB_DATE_INVALID: fixture ISO date invalid: "
                    f"{type_name}.{field_name}"
                )
            try:
                date.fromisoformat(value)
            except ValueError:
                fail(
                    "PUB_DATE_INVALID: fixture ISO date invalid: "
                    f"{type_name}.{field_name}"
                )
        if (
            type_name == "mm_r4.d08_contracts.TimeRef"
            and field_name == "value"
            and value != ""
        ):
            try:
                date.fromisoformat(value)
            except (TypeError, ValueError):
                fail("PUB_DATE_INVALID: fixture TimeRef.value is not an ISO date")
        _validate_constructor_value(
            value, annotation, module, graph, api, inline_allowed
        )


def _validate_fixture_graph(graph: Mapping[str, Any], api: Mapping[str, Any]) -> None:
    if set(graph) != {"schema", "contract", "roots", "nodes", "contract_stage_status"}:
        fail("fixture graph exact keys mismatch")
    if graph["schema"] != "public-authority-constructor-graph-v1":
        fail("fixture graph schema mismatch")
    if graph["contract_stage_status"] != {
        "constructor_graph_typechecked": True,
        "producer_invoked": False,
        "validator_invoked": False,
    }:
        fail("fixture graph stage status overclaims execution")
    expected_source = (
        "SubjectTemporalSourceBundle"
        if graph["contract"] == SUBJECT_CONTRACT_ID
        else "AEMHMatchHistorySourceBundle"
    )
    expected_packet = (
        "SubjectTemporalAuthorityPacket"
        if graph["contract"] == SUBJECT_CONTRACT_ID
        else "AEMHMatchHistoryAuthorityPacket"
    )
    source_id = graph["roots"]["source"]["node_ref"]
    candidate_id = graph["roots"]["expected_candidate"]["node_ref"]
    context_id = graph["roots"]["join_context"]["node_ref"]
    if graph["nodes"][source_id]["type"] != expected_source:
        fail("fixture source root type mismatch")
    if graph["nodes"][candidate_id]["type"] != expected_packet:
        fail("fixture candidate root type mismatch")
    if graph["nodes"][context_id]["type"] != "CurrentJoinContextRegistry":
        fail("fixture current join-context root type mismatch")
    previous = graph["roots"]["previous"]
    if graph["contract"] == SUBJECT_CONTRACT_ID and previous is not None:
        fail("subject fixture cannot have previous root")
    if graph["contract"] == AEMH_CONTRACT_ID and (
        previous is None
        or graph["nodes"][previous["node_ref"]]["type"] != expected_packet
    ):
        fail("AE/MH fixture previous root type mismatch")
    all_reachable: set[str] = set()
    for root_name in ("source", "previous", "expected_candidate", "join_context"):
        all_reachable |= _fixture_reachable(graph, root_name)
    if all_reachable != set(graph["nodes"]):
        fail("fixture graph contains unreachable node")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visiting:
            fail("fixture constructor graph cycle")
        if node_id in visited:
            return
        visiting.add(node_id)
        for child in _fixture_node_refs(graph["nodes"][node_id]["fields"]):
            visit(child)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in graph["nodes"]:
        visit(node_id)
        _validate_fixture_node(graph["nodes"][node_id], graph, api)
    candidate_nodes = _fixture_reachable(graph, "expected_candidate")
    scopes = [
        graph["nodes"][node_id]["fields"]
        for node_id in candidate_nodes
        if graph["nodes"][node_id]["type"] == "PublicScopeIdentity"
    ]
    if not scopes or any(scope != scopes[0] for scope in scopes[1:]):
        fail("fixture current PublicScopeIdentity copies disagree")
    scope = scopes[0]
    dimension_fields = {
        "project_ref": {"project_id", "project_ref"},
        "run_ref": {"run_id", "run_ref"},
        "snapshot_ref": {
            "snapshot_id",
            "snapshot_ref",
            "source_snapshot_id",
            "accepted_snapshot_ref",
        },
        "cutoff_ref": set(),
        "site_ref": {"site_id", "site_ref"},
        "subject_ref": {"subject_id", "subject_ref"},
        "spine_ref": {"spine_ref", "shared_spine_ref"},
    }
    source_nodes = _fixture_reachable(graph, "source")
    observed: dict[str, list[Any]] = {key: [] for key in dimension_fields}
    for node_id in source_nodes:
        node = graph["nodes"][node_id]
        fields = node["fields"]
        for dimension, field_names in dimension_fields.items():
            for field_name in field_names:
                if field_name in fields:
                    observed[dimension].append(fields[field_name])
        if node["type"] == "mm_r5.s4_contracts.S4AcceptedAuthorityAnchor":
            observed["cutoff_ref"].append(fields["cutoff_ref"])
    for dimension, values in observed.items():
        if not values or any(value != scope[dimension] for value in values):
            fail(f"fixture common scope mismatch: {dimension}")
    source_by_type: dict[str, list[Mapping[str, Any]]] = {}
    for node_id in source_nodes:
        node = graph["nodes"][node_id]
        source_by_type.setdefault(node["type"], []).append(node["fields"])
    runs = source_by_type.get("mm_r1.domain.MonitoringRun", [])
    bindings = source_by_type.get("mm_r4.d08_contracts.ScopeBinding", [])
    anchors = source_by_type.get(
        "mm_r5.s4_contracts.S4AcceptedAuthorityAnchor", []
    )
    time_refs = source_by_type.get("mm_r4.d08_contracts.TimeRef", [])
    cutoff_bindings = source_by_type.get("ControlledCutoffLocatorBinding", [])
    if len(runs) != 1 or len(bindings) != 1 or len(anchors) != 1:
        fail("fixture cutoff common authority cardinality drift")
    cutoff = scope["cutoff_ref"]
    cutoff_endpoints = [
        graph["nodes"][node_id]["fields"]
        for node_id in candidate_nodes
        if graph["nodes"][node_id]["type"] == "PublicCutoffEndpoint"
    ]
    temporal_axis_cutoffs = []
    for node_id in candidate_nodes:
        node = graph["nodes"][node_id]
        if node["type"] != "TemporalAxisBasis":
            continue
        cutoff_node_id = node["fields"]["cutoff_endpoint"]["node_ref"]
        temporal_axis_cutoffs.append(graph["nodes"][cutoff_node_id]["fields"])
    if scope["cutoff_state"] == "present":
        try:
            date.fromisoformat(cutoff)
        except (TypeError, ValueError):
            fail(
                "PUB_DATE_INVALID: fixture present cutoff identity is not an "
                "ISO date"
            )
        if (
            runs[0]["data_cutoff"] != cutoff
            or bindings[0]["clinical_event_cutoff"] != cutoff
            or anchors[0]["cutoff_ref"] != cutoff
            or len(time_refs) != 1
            or time_refs[0]["value"] != cutoff
            or len(cutoff_bindings) != 1
            or cutoff_bindings[0]["cutoff_ref"] != cutoff
            or cutoff_bindings[0]["time_ref_id"]
            != time_refs[0]["time_ref_id"]
            or any(
                endpoint["state"] != "present"
                or endpoint["exact_date"] != cutoff
                for endpoint in cutoff_endpoints
            )
            or any(
                endpoint["state"] != "exact"
                or endpoint["exact_date"] != cutoff
                for endpoint in temporal_axis_cutoffs
            )
        ):
            fail(
                "PUB_IDENTITY_CUTOFF_MISMATCH: fixture complete present "
                "cutoff chain mismatch"
            )
    elif scope["cutoff_state"] == "absent":
        if (
            cutoff is not None
            or runs[0]["data_cutoff"] != ""
            or bindings[0]["clinical_event_cutoff"] != ""
            or anchors[0]["cutoff_ref"] is not None
            or time_refs
            or cutoff_bindings
            or any(
                endpoint["state"] != "absent"
                or endpoint["exact_date"] is not None
                for endpoint in cutoff_endpoints
            )
            or any(
                endpoint["state"] != "missing"
                or endpoint["exact_date"] is not None
                for endpoint in temporal_axis_cutoffs
            )
        ):
            fail(
                "PUB_IDENTITY_CUTOFF_MISMATCH: fixture complete absent cutoff "
                "chain mismatch"
            )
    else:
        fail("fixture cutoff state is not closed")
    for node_id in candidate_nodes:
        node = graph["nodes"][node_id]
        fields = node["fields"]
        if node["type"] in {"AEMHMatchThread"}:
            for field_name, dimension in (
                ("project_ref", "project_ref"),
                ("site_ref", "site_ref"),
                ("subject_ref", "subject_ref"),
            ):
                if fields[field_name] != scope[dimension]:
                    fail(f"fixture downstream scope mismatch: {node['type']}.{field_name}")
        if node["type"] == "PublicSourceLocator" and fields["snapshot_ref"] != scope[
            "snapshot_ref"
        ]:
            fail("fixture current source locator snapshot mismatch")
    encoded = json.dumps(graph, ensure_ascii=False)
    for forbidden in ("VALID_CONTROL", "mutated::", "fixture_node_ref", "typed_fixture_node"):
        if forbidden in encoded:
            fail(f"fixture placeholder forbidden: {forbidden}")


def _json_pointer_get(document: Any, pointer: str) -> Any:
    target = document
    for part in pointer.strip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        target = target[int(part)] if isinstance(target, list) else target[part]
    return target


def _json_diff_paths(before: Any, after: Any, prefix: str = "") -> set[str]:
    if type(before) is not type(after):
        return {prefix or "/"}
    if isinstance(before, dict):
        if set(before) in ({"tuple"}, {"list"}, {"mapping"}):
            return set() if before == after else {prefix or "/"}
        if set(before) != set(after):
            return {prefix or "/"}
        result: set[str] = set()
        for key in before:
            result |= _json_diff_paths(before[key], after[key], f"{prefix}/{key}")
        return result
    if isinstance(before, list):
        return set() if before == after else {prefix or "/"}
    return set() if before == after else {prefix or "/"}


def _interpret_adapter(
    adapter: Mapping[str, Any], graph: Mapping[str, Any], api: Mapping[str, Any]
) -> dict[str, Any]:
    exact_keys = {
        "accepted_rule_id",
        "after_predicates",
        "allowed_diff_paths",
        "before_predicates",
        "expected_positive_disposition",
        "expected_primary_code",
        "fixture_key",
        "harness_lane",
        "lane",
        "linked_operations",
        "op",
        "protected_unchanged_paths",
        "replacement",
        "schema",
        "selector",
        "target_annotation",
    }
    if set(adapter) != exact_keys or adapter["schema"] != "public-authority-adapter-v1":
        fail("adapter exact schema mismatch")
    dsl = api["adapter_dsl"]
    if adapter["lane"] not in dsl["closed_lanes"] or adapter["op"] not in dsl[
        "closed_operations"
    ]:
        fail("adapter lane/op is not closed")
    if adapter["harness_lane"] != adapter["lane"]:
        fail("adapter harness lane mismatch")
    before = copy.deepcopy(dict(graph))
    for predicate in adapter["before_predicates"]:
        if predicate["op"] != "equals" or _json_pointer_get(before, predicate["path"]) != predicate["value"]:
            fail("adapter before predicate failed")
    after = copy.deepcopy(before)
    operations = [{
        "op": adapter["op"],
        "selector": adapter["selector"],
        "target_annotation": adapter["target_annotation"],
        "replacement": adapter["replacement"],
    }]
    for linked in adapter["linked_operations"]:
        if set(linked) != {"op", "replacement", "selector", "target_annotation"}:
            fail("adapter linked operation exact schema mismatch")
        operations.append(linked)
    written: set[tuple[str, Any]] = set()
    for operation in operations:
        selector = operation["selector"]
        if set(selector) != {"root", "node_id", "field", "match"} or selector[
            "match"
        ] != "exact_one":
            fail("adapter selector is not exact-one")
        reachable = _fixture_reachable(graph, selector["root"])
        if selector["node_id"] not in reachable:
            fail("adapter selector node is not reachable from selected root")
        target_node = after["nodes"][selector["node_id"]]
        if selector["field"] is not None and selector["field"] not in target_node["fields"]:
            fail("adapter selector field is dangling")
        write_key = (selector["node_id"], selector["field"])
        if write_key in written:
            fail("adapter writes one authoritative field twice")
        written.add(write_key)
        op = operation["op"]
        if op == "replace_node":
            target_node.clear()
            target_node.update(copy.deepcopy(operation["replacement"]))
            if adapter["lane"] != "candidate_corruption":
                _validate_fixture_node(target_node, after, api)
        elif op in {"replace_scalar", "replace_tuple"}:
            target_node["fields"][selector["field"]] = copy.deepcopy(
                operation["replacement"]
            )
            if adapter["lane"] != "candidate_corruption":
                _validate_fixture_node(
                    target_node,
                    after,
                    api,
                    inline_allowed=op == "replace_tuple",
                )
        elif op == "insert_item":
            container = target_node["fields"][selector["field"]]
            if not isinstance(container, dict) or len(container) != 1:
                fail("adapter insert target is not an encoded container")
            values = next(iter(container.values()))
            values.append(copy.deepcopy(operation["replacement"]))
            kind, arguments = _annotation_parts(operation["target_annotation"])
            if kind not in {"tuple", "list", "sequence"}:
                fail("adapter insert annotation is not a container")
            _validate_constructor_value(
                operation["replacement"], arguments[0], "", after, api,
                inline_allowed=True,
            )
        elif op in {"delete_item", "duplicate_item", "permute_items"}:
            fail("adapter operation requires an explicit item selector")
        else:
            fail("adapter operation unknown")
    observed_diff = _json_diff_paths(before, after)
    if observed_diff != set(adapter["allowed_diff_paths"]):
        fail(f"adapter diff drift: {sorted(observed_diff)}")
    if observed_diff & set(adapter["protected_unchanged_paths"]):
        fail("adapter changed protected path")
    for predicate in adapter["after_predicates"]:
        if predicate["op"] != "changed" or predicate["path"] not in observed_diff:
            fail("adapter after predicate failed")
    return after


def _validate_positive_adapter_semantics(
    adapter: Mapping[str, Any], graph: Mapping[str, Any]
) -> None:
    replacement = adapter["replacement"]
    rule_id = adapter["accepted_rule_id"]
    source_nodes = _fixture_reachable(graph, "source")
    if rule_id == "axis_conversion.calendar_default":
        if replacement["type"] != "mm_r1.domain.MonitoringRun":
            fail("calendar positive does not replace a complete MonitoringRun")
        date.fromisoformat(replacement["fields"]["data_cutoff"])
    elif rule_id == "axis_conversion.study_day_valid":
        if replacement["type"] != "mm_r1.domain.TemporalEvent":
            fail("study-day positive does not replace a complete TemporalEvent")
        date.fromisoformat(replacement["fields"]["actual_date"])
        if replacement["fields"]["study_day"] not in {0, 1}:
            fail("study-day anchor positive is not a legal exact anchor")
    elif rule_id == "axis_conversion.conversion_replay":
        if replacement["type"] != "ControlledTemporalEndpointBinding":
            fail("conversion replay does not replace a complete controlled binding")
        fields = replacement["fields"]
        risk_refs = {
            graph["nodes"][node_id]["fields"]["candidate_id"]
            for node_id in source_nodes
            if graph["nodes"][node_id]["type"] == "mm_r2.risk.RiskCandidate"
        }
        activities = {
            graph["nodes"][node_id]["fields"]["actual_activity_id"]
            for node_id in source_nodes
            if graph["nodes"][node_id]["type"]
            == "mm_r4.visit_schedule.ActualActivityRecord"
        }
        if (
            fields["target_kind"] != "risk"
            or fields["target_ref"] not in risk_refs
            or fields["endpoint_role"] != "start"
            or fields["authority_kind"] != "actual_activity"
            or fields["authority_ref"] not in activities
            or fields["authority_date_field"] != "start"
        ):
            fail("conversion replay controlled binding is not source-reachable")
    else:
        if not isinstance(replacement, dict) or set(replacement) != {"tuple"}:
            fail("AE/MH positive does not replace the exact decision tuple")
        records = replacement["tuple"]
        expected_sequences = {
            "aemh_match_history.ae_exact": [("match_decided", "exact", "ae")],
            "aemh_match_history.mh_exact": [("match_decided", "exact", "mh")],
            "aemh_match_history.ambiguous": [("match_decided", "ambiguous", "ae")],
            "aemh_match_history.rejected": [("match_decided", "rejected", "mh")],
            "aemh_match_history.withdrawn": [
                ("match_decided", "exact", "ae"),
                ("withdrawn", None, "ae"),
            ],
            "aemh_match_history.reappeared": [
                ("match_decided", "exact", "ae"),
                ("withdrawn", None, "ae"),
                ("reappeared", None, "ae"),
            ],
            "aemh_match_history.append_only": [
                ("match_decided", "ambiguous", "mh")
            ],
        }
        candidates = {
            graph["nodes"][node_id]["fields"]["candidate_id"]: graph["nodes"][
                node_id
            ]["fields"]
            for node_id in source_nodes
            if graph["nodes"][node_id]["type"] == "mm_r2.risk.RiskCandidate"
        }
        expected_sequence = expected_sequences.get(rule_id)
        observed_sequence = []
        fact_refs = {
            graph["nodes"][node_id]["fields"]["fact_id"]
            for node_id in source_nodes
            if graph["nodes"][node_id]["type"] == "mm_r1.domain.CanonicalFact"
        }
        locator_refs = {
            graph["nodes"][node_id]["fields"]["source_locator_id"]
            for node_id in source_nodes
            if graph["nodes"][node_id]["type"] == "mm_r4.d08_contracts.SourceLocator"
        }
        base_refs = {
            graph["nodes"][node_id]["fields"]["decision_ref"]
            for node_id in source_nodes
            if graph["nodes"][node_id]["type"] == "AEMHDecisionAuthorityRecord"
        }
        base_identities = {
            graph["nodes"][node_id]["fields"]["authority_identity"]
            for node_id in source_nodes
            if graph["nodes"][node_id]["type"] == "AEMHDecisionAuthorityRecord"
        }
        decision_refs: list[str] = []
        authority_identities: list[str] = []
        match_count_by_thread: dict[str, int] = {}
        for record in records:
            if record.get("type") != "AEMHDecisionAuthorityRecord":
                fail("AE/MH positive decision constructor drift")
            fields = record["fields"]
            candidate = candidates.get(fields["thread_ref"])
            if candidate is None:
                fail("AE/MH positive thread is not a reachable candidate")
            observed_sequence.append(
                (fields["event_kind"], fields["match_state"], candidate["domain"])
            )
            expected_reason = {
                ("match_decided", "exact"): "identity_exact",
                ("match_decided", "ambiguous"): "identity_ambiguous",
                ("match_decided", "rejected"): "identity_rejected",
                ("withdrawn", None): "source_withdrawn",
                ("reappeared", None): "source_reappeared",
            }.get((fields["event_kind"], fields["match_state"]))
            if expected_reason is None or fields["reason_code"] != expected_reason:
                fail("AE/MH positive lifecycle tuple is not closed/legal")
            if fields["event_kind"] == "match_decided":
                match_count_by_thread[fields["thread_ref"]] = (
                    match_count_by_thread.get(fields["thread_ref"], 0) + 1
                )
            referenced_facts = set(fields["later_fact_refs"]["tuple"]) | set(
                fields["considered_fact_refs"]["tuple"]
            )
            referenced_locators = set(
                fields["retained_source_locator_refs"]["tuple"]
            ) | set(fields["authority_source_locator_refs"]["tuple"])
            expected_identity = canonical_hash(
                {
                    "decision_ref": fields["decision_ref"],
                    "project_ref": candidate["project_id"],
                    "subject_ref": candidate["subject_ref"],
                    "snapshot_ref": candidate["source_snapshot_id"],
                    "thread_ref": fields["thread_ref"],
                    "event_kind": fields["event_kind"],
                    "match_state": fields["match_state"],
                    "reason_code": fields["reason_code"],
                    "later_fact_refs": fields["later_fact_refs"]["tuple"],
                    "considered_fact_refs": fields["considered_fact_refs"]["tuple"],
                    "decision_authority_kind": fields[
                        "decision_authority_kind"
                    ],
                    "authority_source_locator_refs": fields[
                        "authority_source_locator_refs"
                    ]["tuple"],
                }
            )
            expected_hash = canonical_hash(
                {
                    key: value
                    for key, value in fields.items()
                    if key != "authority_content_hash"
                }
            )
            if (
                not referenced_facts
                or not referenced_facts.issubset(fact_refs)
                or not referenced_locators
                or not referenced_locators.issubset(locator_refs)
                or fields["authority_identity"] != expected_identity
                or fields["authority_content_hash"] != expected_hash
            ):
                fail("AE/MH positive decision references/hash are not source-reachable")
            decision_refs.append(fields["decision_ref"])
            authority_identities.append(fields["authority_identity"])
        if (
            observed_sequence != expected_sequence
            or any(count > 1 for count in match_count_by_thread.values())
            or len(decision_refs) != len(set(decision_refs))
            or len(authority_identities) != len(set(authority_identities))
            or set(decision_refs) & base_refs
            or set(authority_identities) & base_identities
        ):
            fail("AE/MH positive decision lifecycle/identity is not independent")


def _validate_reseal_plan(
    plan: Mapping[str, Any], graph: Mapping[str, Any], api: Mapping[str, Any]
) -> None:
    if set(plan) != {"schema", "mode", "operations", "required_writes"}:
        fail("reseal plan exact keys mismatch")
    grammar = api["reseal_dsl"]
    if plan["schema"] != grammar["schema"] or plan["mode"] not in grammar[
        "closed_modes"
    ]:
        fail("reseal plan schema/mode drift")
    if plan["mode"] == "none":
        if plan["operations"] or plan["required_writes"]:
            fail("none reseal mode cannot contain operations")
        return
    candidate = _fixture_reachable(graph, "expected_candidate")
    previous = _fixture_reachable(graph, "previous")
    buffers: set[str] = set()
    written: set[tuple[str, str]] = set()
    target_sequence: list[Mapping[str, Any]] = []
    all_targets = {
        (operation["target"]["node_id"], operation["target"]["field"])
        for operation in plan["operations"]
        if "target" in operation
    }
    recipes = {
        "aemh_entry_id_v1",
        "aemh_projection_id_v1",
        "public_receipt_id_v1",
        "subject_projection_id_v1",
    }
    for operation in plan["operations"]:
        op = operation.get("op")
        if op not in grammar["closed_operations"] or set(operation) != set(
            grammar["operation_keys"][op]
        ):
            fail(f"reseal operation unknown keys/op: {op}")
        if op == "copy_previous_prefix":
            if operation["buffer"] in buffers:
                fail("reseal buffer duplicate write")
            source = operation["source"]
            if source.get("root") != "previous" or source.get("node_id") not in previous:
                fail("reseal previous prefix source is not reachable")
            if source.get("field") not in graph["nodes"][source["node_id"]]["fields"]:
                fail("reseal previous prefix field is dangling")
            buffers.add(operation["buffer"])
            continue
        target = operation["target"]
        if set(target) != {"node_id", "field", "match"} or target[
            "match"
        ] != "exact_one":
            fail("reseal selector is not exact-one")
        key = (target["node_id"], target["field"])
        if target["node_id"] not in candidate or target["field"] not in graph[
            "nodes"
        ][target["node_id"]]["fields"]:
            fail("reseal target is dangling or non-current")
        if key in written:
            fail("reseal duplicate write")
        if op == "append_history_suffix":
            if operation["prefix_buffer"] not in buffers:
                fail("reseal buffer read before write")
            if operation["source"] != {
                "root": "source",
                "field": "decision_records",
                "filter": {
                    "op": "eq",
                    "lhs": {
                        "scope": "candidate_item",
                        "path": ["thread_ref"],
                    },
                    "rhs": {
                        "scope": "current_target",
                        "path": ["original_candidate_ref"],
                    },
                },
                "cardinality": "one_or_more",
                "ordering": "source_tuple_order",
            }:
                fail("reseal append source grammar drift")
        elif op == "rehash":
            if operation["exclude"] != [target["field"]]:
                fail("reseal hash exclusion drift")
        elif op == "derive_id":
            if operation["recipe"] not in recipes or target["field"] not in operation[
                "exclude"
            ]:
                fail("reseal id recipe/exclusion drift")
        elif op == "assign_ref":
            source = operation["source"]
            if set(source) != {"root", "node_id", "field"}:
                fail("reseal ref source grammar drift")
            reachable = previous if source["root"] == "previous" else candidate
            if source["root"] not in {"previous", "current"} or source[
                "node_id"
            ] not in reachable:
                fail("reseal ref source root/path drift")
            source_key = (source["node_id"], source["field"])
            if source["field"] not in graph["nodes"][source["node_id"]]["fields"]:
                fail("reseal ref source field dangling")
            if source["root"] == "current" and source_key in all_targets and source_key not in written:
                fail("reseal derived current ref read before write")
        written.add(key)
        target_sequence.append(target)
    if plan["required_writes"] != target_sequence:
        fail("reseal required write sequence drift")
    if not written:
        fail("reseal candidate plan performs no writes")


def _fixture_plain_value(value: Any, graph: Mapping[str, Any]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"node_ref"}:
            record = graph["nodes"][value["node_ref"]]
            return {
                name: _fixture_plain_value(child, graph)
                for name, child in record["fields"].items()
            }
        if set(value) in ({"tuple"}, {"list"}):
            return [
                _fixture_plain_value(child, graph)
                for child in next(iter(value.values()))
            ]
        if set(value) == {"mapping"}:
            return {
                str(name): _fixture_plain_value(child, graph)
                for name, child in value["mapping"]
            }
    return copy.deepcopy(value)


def _independent_rehash_subject_packet(
    packet: dict[str, Any], schema: Mapping[str, Any]
) -> dict[str, Any]:
    replacements: dict[str, str] = {}

    def visit(value: Any, type_name: str) -> None:
        if type_name not in schema["objects"]:
            return
        for field_name, field_spec in schema["objects"][type_name].items():
            child = value[field_name]
            if field_spec["cardinality"] == "many":
                for item in child:
                    visit(item, field_spec["type"])
            elif child is not None:
                visit(child, field_spec["type"])
        if type_name in {
            "SubjectTemporalAuthorityPacket",
            "SubjectTemporalPublicProjection",
            "PublicAuthorityReceipt",
        }:
            return
        fields = [
            name
            for name in schema["objects"][type_name]
            if name.endswith("_content_hash")
        ]
        if len(fields) == 1:
            hash_field = fields[0]
            old = value[hash_field]
            value[hash_field] = canonical_hash(
                {key: item for key, item in value.items() if key != hash_field}
            )
            replacements[old] = value[hash_field]

    visit(packet, "SubjectTemporalAuthorityPacket")
    projection = packet["projection"]
    receipt = packet["receipt"]
    old_projection_id = projection["projection_id"]
    projection["projection_id"] = canonical_hash(
        {
            "contract_id": projection["contract_id"],
            "schema_version": projection["schema_version"],
            "scope_identity_hash": projection["scope_identity"][
                "identity_content_hash"
            ],
            "membership_index_hash": projection["membership_index"][
                "membership_content_hash"
            ],
            "axis_basis_hash": projection["axis_basis"]["axis_content_hash"],
        }
    )
    replacements[old_projection_id] = projection["projection_id"]
    receipt["public_projection_id"] = projection["projection_id"]
    receipt["receipt_id"] = canonical_hash(
        {
            "receipt_variant": receipt["receipt_variant"],
            "authority_contract_id": receipt["authority_contract_id"],
            "scope_identity_hash": receipt["scope_identity"][
                "identity_content_hash"
            ],
            "public_projection_id": receipt["public_projection_id"],
        }
    )
    projection["receipt_ref"] = receipt["receipt_id"]
    old_projection_hash = projection["projection_content_hash"]
    projection["projection_content_hash"] = canonical_hash(
        {
            key: value
            for key, value in projection.items()
            if key != "projection_content_hash"
        }
    )
    replacements[old_projection_hash] = projection["projection_content_hash"]
    receipt["public_projection_content_hash"] = projection[
        "projection_content_hash"
    ]
    receipt["evaluation_content_identities"] = sorted(
        {
            replacements.get(value, value)
            for value in receipt["evaluation_content_identities"]
        }
    )
    receipt["receipt_content_hash"] = canonical_hash(
        {
            key: value
            for key, value in receipt.items()
            if key != "receipt_content_hash"
        }
    )
    packet["packet_content_hash"] = canonical_hash(
        {
            "receipt_content_hash": receipt["receipt_content_hash"],
            "projection_content_hash": projection["projection_content_hash"],
        }
    )
    return packet


def _verify_v9_expected_subgraph(
    row: Mapping[str, Any], diff: Mapping[str, Any], graph: Mapping[str, Any],
    transformed: Mapping[str, Any],
) -> None:
    subgraph = diff["post_adapter_expected_output_subgraph"]
    baseline = _fixture_plain_value(graph["roots"]["expected_candidate"], graph)
    if (
        subgraph.get("baseline_output_graph_hash") != canonical_hash(baseline)
        or len(subgraph.get("nodes", [])) != 1
        or subgraph.get("target_instance", {}).get("instance_selector") is None
    ):
        fail(f"v9 expected fixture baseline/target drift: {row['case_id']}")
    node = subgraph["nodes"][0]
    packet = node.get("exact_fields")
    if not isinstance(packet, dict) or node.get("instance_selector") != {
        "packet_content_hash": packet.get("packet_content_hash")
    }:
        fail(f"v9 expected packet root drift: {row['case_id']}")
    if row["contract"] == SUBJECT_CONTRACT_ID:
        if node.get("type") != "SubjectTemporalAuthorityPacket":
            fail("subject expected root is not the exact packet")
        expected = copy.deepcopy(baseline)
        instance_diff = diff["exact_instance_diffs"]
        if any(item.get("operation") != "replace" for item in instance_diff):
            fail(f"subject exact diff operation drift: {row['case_id']}")
        transformed_source = [
            transformed["nodes"][node_id]
            for node_id in _fixture_reachable(transformed, "source")
        ]

        def exact_source(type_name: str) -> Mapping[str, Any]:
            matches = [
                item["fields"]
                for item in transformed_source
                if item["type"] == type_name
            ]
            if len(matches) != 1:
                fail(f"positive transformed source is not exact-one: {type_name}")
            return matches[0]

        if row["case_id"] == "R5C-109":
            chain = {
                exact_source("mm_r1.domain.MonitoringRun")["data_cutoff"],
                exact_source("mm_r4.d08_contracts.ScopeBinding")[
                    "clinical_event_cutoff"
                ],
                exact_source("mm_r4.d08_contracts.TimeRef")["value"],
                exact_source("ControlledCutoffLocatorBinding")["cutoff_ref"],
                exact_source("mm_r5.s4_contracts.S4AcceptedAuthorityAnchor")[
                    "cutoff_ref"
                ],
            }
            if len(chain) != 1 or 1 + len(row["adapter"]["linked_operations"]) != 5:
                fail(
                    "PUB_IDENTITY_CUTOFF_MISMATCH: R5C-109 complete linked "
                    "cutoff chain is missing"
                )
            after = next(iter(chain))
            try:
                date.fromisoformat(after)
            except (TypeError, ValueError):
                fail("R5C-109 transformed cutoff is not ISO date")
            target = expected["projection"]["axis_basis"]["cutoff_endpoint"]
            selector = {
                "scope_cutoff_ref": after,
                "projection_path": "axis_basis.cutoff_endpoint",
            }
            path = "/projection/axis_basis/cutoff_endpoint/exact_date"
            old_cutoff = expected["projection"]["scope_identity"]["cutoff_ref"]
            expected["projection"]["scope_identity"]["cutoff_ref"] = after
            expected["receipt"]["scope_identity"]["cutoff_ref"] = after
            expected_diff = [
                (selector, path, target["exact_date"], after),
                (
                    {"projection": "scope_identity"},
                    "/projection/scope_identity/cutoff_ref",
                    old_cutoff,
                    after,
                ),
                (
                    {"receipt": "scope_identity"},
                    "/receipt/scope_identity/cutoff_ref",
                    baseline["receipt"]["scope_identity"]["cutoff_ref"],
                    after,
                ),
            ]
        elif row["case_id"] == "R5C-110":
            replacement = exact_source("mm_r1.domain.TemporalEvent")
            matches = [
                item
                for item in expected["projection"]["events"]
                if item["event_ref"] == replacement["event_id"]
            ]
            if len(matches) != 1:
                fail("R5C-110 baseline event selector is not exact-one")
            target = matches[0]["start_endpoint"]
            selector = {"event_ref": replacement["event_id"]}
            path = "/projection/events/event::ae::1/start_endpoint/exact_date"
            after = replacement["actual_date"]
            expected_diff = [(selector, path, target["exact_date"], after)]
        elif row["case_id"] == "R5C-116":
            replacement = exact_source("ControlledTemporalEndpointBinding")
            matches = [
                item
                for item in expected["projection"]["risk_anchors"]
                if item["risk_ref"] == replacement["target_ref"]
            ]
            if len(matches) != 1:
                fail("R5C-116 baseline risk selector is not exact-one")
            target = matches[0]["start_endpoint"]
            selector = {"risk_ref": replacement["target_ref"]}
            path = "/projection/risk_anchors/risk::ae::1/start_endpoint/exact_date"
            authority = [
                item
                for item in transformed["nodes"].values()
                if item["type"] == "mm_r4.visit_schedule.ActualActivityRecord"
                and item["fields"]["actual_activity_id"]
                == replacement["authority_ref"]
            ]
            if len(authority) != 1:
                fail("R5C-116 authority selector is not exact-one")
            after = authority[0]["fields"][replacement["authority_date_field"]]
            expected_diff = [(selector, path, target["exact_date"], after)]
        else:
            fail(f"unexpected subject positive: {row['case_id']}")
        target["exact_date"] = after
        if (
            [
                (
                    item["instance_selector"],
                    item["path"],
                    item["before"],
                    item["after"],
                )
                for item in instance_diff
            ]
            != expected_diff
            or subgraph["target_instance"]["instance_selector"] != selector
            or subgraph["target_instance"]["exact_path"] != path
        ):
            fail(f"subject baseline diff application drift: {row['case_id']}")
        schema = read_json(PUBLIC_ARTIFACT_DIR / "subject_temporal_schema.json")
        expected = _independent_rehash_subject_packet(expected, schema)
        if packet != expected:
            fail(f"subject post-adapter exact packet drift: {row['case_id']}")
        return

    if node.get("type") != "AEMHMatchHistoryAuthorityPacket":
        fail("AEMH expected root is not the exact packet")
    previous = _fixture_plain_value(graph["roots"]["previous"], graph)
    projection = packet["projection"]
    receipt = packet["receipt"]
    previous_projection = previous["projection"]
    encoded_decisions = transformed["nodes"][
        transformed["roots"]["source"]["node_ref"]
    ]["fields"]["decision_records"]["tuple"]
    decisions = []
    for encoded in encoded_decisions:
        if set(encoded) == {"node_ref"}:
            decisions.append(transformed["nodes"][encoded["node_ref"]]["fields"])
        elif set(encoded) == {"type", "fields"}:
            decisions.append(encoded["fields"])
        else:
            fail("transformed decision encoding drift")
    source_nodes = [
        transformed["nodes"][node_id]
        for node_id in _fixture_reachable(transformed, "source")
    ]
    source_facts = {
        item["fields"]["fact_id"]: item["fields"]
        for item in source_nodes
        if item["type"] == "mm_r1.domain.CanonicalFact"
    }
    source_candidates = {
        item["fields"]["candidate_id"]: item["fields"]
        for item in source_nodes
        if item["type"] == "mm_r2.risk.RiskCandidate"
    }
    source_revisions = {
        item["fields"]["revision_id"]: item["fields"]
        for item in source_nodes
        if item["type"] == "mm_r1.domain.SourceRevision"
    }
    source_locator_tuples = {
        (
            item["fields"]["snapshot_id"],
            item["fields"]["source_revision_id"],
            item["fields"]["table_semantic"],
            item["fields"]["record_id"],
            item["fields"]["column_or_anchor"],
            item["fields"]["raw_payload_hash"],
        )
        for item in source_nodes
        if item["type"] == "mm_r4.contracts.SourceLocator"
    }
    locator_map = {item["locator_ref"]: item for item in projection["source_locators"]}
    previous_threads = {
        item["thread_ref"]: item for item in previous_projection["threads"]
    }
    if {item["thread_ref"] for item in projection["threads"]} != set(previous_threads):
        fail(f"AEMH thread set drift: {row['case_id']}")
    entry_ids: list[str] = []
    expected_locator_refs: set[str] = set()
    for thread in projection["threads"]:
        old_thread = previous_threads[thread["thread_ref"]]
        prefix = old_thread["history_entries"]
        relevant = [
            item
            for item in decisions
            if item["thread_ref"] == thread["original_candidate_ref"]
        ]
        entries = thread["history_entries"]
        if entries[: len(prefix)] != prefix or len(entries) != len(prefix) + len(relevant):
            fail(f"AEMH byte-identical prefix/suffix drift: {row['case_id']}")
        retained = set(old_thread["evidence_locator_refs"])
        for ordinal, (entry, decision) in enumerate(
            zip(entries[len(prefix) :], relevant), start=1
        ):
            seq = len(prefix) + ordinal
            expected_entry_id = old_thread["original_reminder_ref"].rsplit("::", 1)[0] + f"::{seq}"
            if (
                entry["seq"] != seq
                or entry["entry_id"] != expected_entry_id
                or entry["prior_entry_hash"] != entries[seq - 2]["entry_hash"]
                or entry["event_kind"] != decision["event_kind"]
                or entry["match_state"] != decision["match_state"]
                or entry["reason_code"] != decision["reason_code"]
                or entry["later_fact_refs"] != decision["later_fact_refs"]["tuple"]
                or entry["entry_hash"]
                != canonical_hash(
                    {key: value for key, value in entry.items() if key != "entry_hash"}
                )
            ):
                fail(f"AEMH exact accepted entry recipe drift: {row['case_id']}")
            if not entry["identity_evidence"]:
                fail(f"AEMH suffix evidence empty: {row['case_id']}")
            if entry["identity_evidence_refs"] != sorted(
                item["evidence_ref"] for item in entry["identity_evidence"]
            ):
                fail(f"AEMH evidence refs drift: {row['case_id']}")
            for evidence in entry["identity_evidence"]:
                locator = locator_map.get(evidence["source_locator_ref"])
                if (
                    locator is None
                    or evidence["source_locator_content_hash"]
                    != locator["locator_content_hash"]
                    or evidence["source_raw_payload_hash"]
                    != locator["raw_payload_hash"]
                    or evidence["evidence_content_hash"]
                    != canonical_hash(
                        {
                            key: value
                            for key, value in evidence.items()
                            if key != "evidence_content_hash"
                        }
                    )
                ):
                    fail(f"AEMH evidence locator/hash drift: {row['case_id']}")
                expected_identity = canonical_hash(
                    {
                        "entity_kind": evidence["evidence_kind"],
                        "entity_ref": evidence["entity_ref"],
                        "source_locator_ref": evidence["source_locator_ref"],
                        "source_raw_payload_hash": evidence["source_raw_payload_hash"],
                    }
                )
                if evidence["entity_content_identity"] != expected_identity:
                    fail(f"AEMH evidence identity recipe drift: {row['case_id']}")
                if evidence["evidence_kind"] == "candidate":
                    candidate = source_candidates.get(evidence["entity_ref"])
                    if candidate is None or candidate["content_hash"] != evidence[
                        "source_raw_payload_hash"
                    ]:
                        fail(f"AEMH candidate evidence is not source-reachable: {row['case_id']}")
                elif evidence["evidence_kind"] == "later_fact":
                    fact = source_facts.get(evidence["entity_ref"])
                    if fact is None or fact["fact_hash"] != evidence[
                        "entity_content_identity"
                    ]:
                        fail(f"AEMH later fact identity is not CanonicalFact.fact_hash: {row['case_id']}")
                expected_locator_refs.add(evidence["source_locator_ref"])
            expected_later_hashes = [
                source_facts[fact_ref]["fact_hash"]
                for fact_ref in entry["later_fact_refs"]
            ]
            if entry["later_fact_content_identities"] != expected_later_hashes:
                fail(f"AEMH later fact content identity drift: {row['case_id']}")
            retained.update(item["source_locator_ref"] for item in entry["identity_evidence"])
            if entry["retained_evidence_locator_refs"] != sorted(retained):
                fail(f"AEMH retained evidence monotonicity drift: {row['case_id']}")
        if thread["evidence_locator_refs"] != sorted(retained):
            fail(f"AEMH thread evidence union drift: {row['case_id']}")
        if thread["thread_content_hash"] != canonical_hash(
            {
                key: value
                for key, value in thread.items()
                if key != "thread_content_hash"
            }
        ):
            fail(f"AEMH full thread hash recipe drift: {row['case_id']}")
        entry_ids.extend(item["entry_id"] for item in entries)
    if len(entry_ids) != len(set(entry_ids)):
        fail(f"AEMH entry ids are not globally unique: {row['case_id']}")
    prefix_by_ref = {
        item["thread_ref"]: item for item in projection["accepted_thread_prefixes"]
    }
    for thread_ref, old_thread in previous_threads.items():
        prefix = prefix_by_ref.get(thread_ref)
        expected_prefix = {
            "accepted_prefix_head_hash": old_thread["history_entries"][-1]["entry_hash"],
            "accepted_prefix_seq": len(old_thread["history_entries"]),
            "prefix_content_hash": "",
            "previous_thread_content_hash": old_thread["thread_content_hash"],
            "thread_ref": thread_ref,
        }
        expected_prefix["prefix_content_hash"] = canonical_hash(
            {
                key: value
                for key, value in expected_prefix.items()
                if key != "prefix_content_hash"
            }
        )
        if prefix != expected_prefix:
            fail(f"AEMH prefix anchor recipe drift: {row['case_id']}")
    membership = projection["membership_index"]
    expected_membership = {
        "candidate_refs": sorted(item["original_candidate_ref"] for item in projection["threads"]),
        "later_fact_refs": sorted(
            {
                fact_ref
                for thread in projection["threads"]
                for entry in thread["history_entries"]
                for fact_ref in entry["later_fact_refs"]
            }
        ),
        "membership_content_hash": "",
        "source_locator_refs": sorted(locator_map),
        "thread_refs": sorted(item["thread_ref"] for item in projection["threads"]),
    }
    expected_membership["membership_content_hash"] = canonical_hash(
        {
            key: value
            for key, value in expected_membership.items()
            if key != "membership_content_hash"
        }
    )
    if membership != expected_membership or set(locator_map) != expected_locator_refs | {
        locator_ref
        for thread in previous_projection["threads"]
        for locator_ref in thread["evidence_locator_refs"]
    }:
        fail(f"AEMH membership/locator coverage drift: {row['case_id']}")
    for locator in locator_map.values():
        revision = source_revisions.get(locator["source_revision_ref"])
        source_tuple = (
            locator["snapshot_ref"],
            locator["source_revision_ref"],
            locator["table_semantic"],
            locator["record_ref"],
            locator["column_or_anchor"],
            locator["raw_payload_hash"],
        )
        if (
            locator["locator_content_hash"]
            != canonical_hash(
                {
                    key: value
                    for key, value in locator.items()
                    if key != "locator_content_hash"
                }
            )
            or revision is None
            or revision["content_hash"] != locator["source_revision_content_hash"]
            or source_tuple not in source_locator_tuples
        ):
            fail(f"AEMH locator/source hash drift: {row['case_id']}")
    expected_pair_groups: dict[str, list[str]] = {}
    for locator in locator_map.values():
        expected_pair_groups.setdefault(locator["source_revision_ref"], []).append(
            locator["locator_ref"]
        )
    pairs = {
        pair["revision_id"]: pair
        for pair in receipt["source_revision_content_pairs"]
    }
    if set(pairs) != set(expected_pair_groups):
        fail(f"AEMH source revision pair partition drift: {row['case_id']}")
    for revision_id, locator_refs in expected_pair_groups.items():
        pair = pairs[revision_id]
        if (
            pair["accepted_content_hash"]
            != source_revisions[revision_id]["content_hash"]
            or pair["locator_refs"] != sorted(locator_refs)
            or pair["pair_content_hash"]
            != canonical_hash(
                {
                    key: value
                    for key, value in pair.items()
                    if key != "pair_content_hash"
                }
            )
        ):
            fail(f"AEMH source revision pair hash drift: {row['case_id']}")
    expected_projection_id = canonical_hash(
        {
            "contract_id": projection["contract_id"],
            "schema_version": projection["schema_version"],
            "scope_identity_hash": projection["scope_identity"]["identity_content_hash"],
            "membership_index_hash": membership["membership_content_hash"],
        }
    )
    expected_receipt_id = canonical_hash(
        {
            "receipt_variant": receipt["receipt_variant"],
            "authority_contract_id": receipt["authority_contract_id"],
            "scope_identity_hash": receipt["scope_identity"]["identity_content_hash"],
            "public_projection_id": expected_projection_id,
        }
    )
    if (
        projection["projection_id"] != expected_projection_id
        or receipt["public_projection_id"] != expected_projection_id
        or projection["receipt_ref"] != expected_receipt_id
        or receipt["receipt_id"] != expected_receipt_id
        or projection["previous_projection_ref"] != previous_projection["projection_id"]
        or projection["previous_projection_content_hash"]
        != previous_projection["projection_content_hash"]
        or projection["projection_content_hash"]
        != canonical_hash(
            {
                key: value
                for key, value in projection.items()
                if key != "projection_content_hash"
            }
        )
    ):
        fail(f"AEMH projection/receipt accepted recipe drift: {row['case_id']}")
    expected_evaluations = {
        projection["projection_content_hash"],
        projection["previous_projection_content_hash"],
        projection["scope_identity"]["identity_content_hash"],
        projection["cutoff_endpoint"]["cutoff_content_hash"],
        membership["membership_content_hash"],
    }
    for prefix in projection["accepted_thread_prefixes"]:
        expected_evaluations.update(
            {prefix["accepted_prefix_head_hash"], prefix["prefix_content_hash"]}
        )
    for locator in projection["source_locators"]:
        expected_evaluations.update(
            {locator["locator_content_hash"], locator["source_revision_content_hash"]}
        )
    for thread in projection["threads"]:
        expected_evaluations.update(
            {thread["candidate_content_identity"], thread["thread_content_hash"]}
        )
        for entry in thread["history_entries"]:
            expected_evaluations.add(entry["entry_hash"])
            for evidence in entry["identity_evidence"]:
                expected_evaluations.add(evidence["evidence_content_hash"])
                if evidence["evidence_kind"] != "considered_fact":
                    expected_evaluations.add(evidence["entity_content_identity"])
    if receipt["evaluation_content_identities"] != sorted(expected_evaluations):
        fail(f"AEMH evaluation identity closure drift: {row['case_id']}")
    if (
        receipt["public_projection_content_hash"] != projection["projection_content_hash"]
        or receipt["receipt_content_hash"]
        != canonical_hash(
            {
                key: value
                for key, value in receipt.items()
                if key != "receipt_content_hash"
            }
        )
        or packet["packet_content_hash"]
        != canonical_hash(
            {
                "receipt_content_hash": receipt["receipt_content_hash"],
                "projection_content_hash": projection["projection_content_hash"],
            }
        )
    ):
        fail(f"AEMH receipt/packet hash drift: {row['case_id']}")


def verify_constructible_test_matrix(
    error_codes: set[str],
    api: Mapping[str, Any],
    candidate_matrix: Optional[Mapping[str, Any]] = None,  # noqa: UP045 -- Python 3.9 contract tool
) -> dict[str, Any]:
    matrix = (
        copy.deepcopy(dict(candidate_matrix))
        if candidate_matrix is not None
        else read_json(ARTIFACT_DIR / "test_matrix.json")
    )
    registry = read_json(PUBLIC_ARTIFACT_DIR / "challenge_registry.json")
    if matrix.get("counts") != {
        "future_runtime_spec_total": 231,
        "future_executable_spec_total": 231,
        "accepted_case_trace_total": 236,
        "subject_inherited": 48,
        "subject_producer_specific": 95,
        "aemh_inherited": 16,
        "aemh_producer_specific": 77,
        "contract_verifier_governance": 22,
    }:
        fail("constructible test matrix counts drift")
    independent_catalog = _independent_constructor_catalog()
    if api["constructor_type_catalog"] != independent_catalog:
        fail("constructor type catalog is not independently reproduced from pinned AST")
    fixtures = matrix.get("fixture_catalog", {})
    if set(fixtures) != {
        "aemh_base",
        "subject_absent_cutoff_base",
        "subject_base",
        "subject_conflicted_base",
        "subject_no_study_day_base",
    }:
        fail("fixture catalog exact roots drift")
    for graph in fixtures.values():
        _validate_fixture_graph(graph, api)
    plans = matrix.get("reseal_plans", {})
    if set(plans) != {
        "stale_hash_none",
        "reseal_subject_base",
        "reseal_aemh_base",
    }:
        fail("reseal plan catalog drift")
    for name, plan in plans.items():
        graph = fixtures["aemh_base" if name.endswith("aemh_base") else "subject_base"]
        _validate_reseal_plan(plan, graph, api)
    accepted = {
        row["case_id"]: row
        for row in registry["inherited_cases"]
        + registry["public_authority_specific_cases"]
    }
    runtime = matrix.get("future_runtime_specs", [])
    governance = matrix.get("contract_verifier_governance_cases", [])
    if len(runtime) != 231 or len(governance) != 22:
        fail("constructible test materialized count drift")
    expected_alias_groups = [
        ["PA-007", "R5C-103"],
        ["PA-034", "PA-120"],
        ["PA-035", "PA-121"],
        ["PA-118", "R5C-108"],
        ["PA-129", "R5C-111"],
    ]
    if matrix.get("case_id_aliases") != [
        {
            "canonical_case_id": group[0],
            "alias_case_ids": group[1:],
            "covered_case_ids": group,
            "delta_kind": "non_semantic_executable_spec_dedup",
        }
        for group in expected_alias_groups
    ]:
        fail("future executable case alias delta drift")
    runtime_case_ids = {
        case_id
        for case_id, source in accepted.items()
        if source["contract"] in {SUBJECT_CONTRACT_ID, AEMH_CONTRACT_ID}
    }
    covered_ids = [
        case_id for row in runtime for case_id in row.get("covered_case_ids", [])
    ]
    if (
        len(covered_ids) != 236
        or len(set(covered_ids)) != 236
        or set(covered_ids) != runtime_case_ids
        or matrix.get("accepted_case_trace_ids") != sorted(runtime_case_ids)
    ):
        fail("accepted case trace coverage/alias uniqueness drift")
    identity_outcomes: dict[str, set[str]] = {}
    lane_counts: dict[str, int] = {}
    positive = 0
    positive_inputs: list[dict[str, str]] = []
    positive_expected_packet_hashes: list[str] = []
    all_positive_decision_refs: list[str] = []
    all_positive_authority_identities: list[str] = []
    joins = read_json(ARTIFACT_DIR / "source_join_matrix.json")["rows"]
    valid_output_paths = {
        (row["contract"], f"/{row['leaf'].replace('.', '/', 1)}")
        for row in joins
    }

    def expected_builder_paths(
        adapter: Mapping[str, Any], graph: Mapping[str, Any], contract: str
    ) -> tuple[list[str], list[str]]:
        changed: set[tuple[str, str]] = set()
        operations = [
            {
                "selector": adapter["selector"],
                "replacement": adapter["replacement"],
            },
            *adapter["linked_operations"],
        ]
        if adapter["harness_lane"] == "typed_source_transform":
            for operation in operations:
                selector = operation["selector"]
                owner = graph["nodes"][selector["node_id"]]["type"]
                if selector["field"] is None:
                    before_fields = graph["nodes"][selector["node_id"]]["fields"]
                    after_fields = operation["replacement"]["fields"]
                    changed.update(
                        (owner, field_name)
                        for field_name in before_fields
                        if before_fields[field_name] != after_fields[field_name]
                    )
                elif selector["field"] == "decision_records":
                    changed.update(
                        ("AEMHDecisionAuthorityRecord", field_name)
                        for item in operation["replacement"]["tuple"]
                        for field_name in item["fields"]
                    )
                else:
                    changed.add((owner, selector["field"]))
        contract_rows = [row for row in joins if row["contract"] == contract]
        direct = sorted(
            {
                f"/{row['leaf'].replace('.', '/', 1)}"
                for row in contract_rows
                if any(
                    (
                        reference["terminal"]["owner"],
                        reference["segments"][-1]["field"],
                    )
                    in changed
                    for reference in row["references"]
                )
            }
        )
        recomputed = sorted(
            {
                f"/{row['leaf'].replace('.', '/', 1)}"
                for row in contract_rows
                if row["reducer"] == "canonical_sha256"
                or row["leaf"].endswith(("_hash", "_id"))
            }
        )
        return direct, recomputed

    def validate_expected_subgraph(
        row: Mapping[str, Any], diff: Mapping[str, Any], graph: Mapping[str, Any],
        transformed: Mapping[str, Any],
    ) -> None:
        subgraph = diff.get("post_adapter_expected_output_subgraph", {})
        if (
            subgraph.get("schema")
            != "public-authority-post-adapter-expected-subgraph-v1"
            or diff.get("post_adapter_expected_output_subgraph_hash")
            != canonical_hash(subgraph)
            or subgraph.get("subgraph_content_hash")
            != canonical_hash({
                key: value
                for key, value in subgraph.items()
                if key != "subgraph_content_hash"
            })
            or not subgraph.get("nodes")
            or subgraph.get("root_node_id")
            not in {node.get("node_id") for node in subgraph.get("nodes", [])}
        ):
            fail(f"post-adapter expected subgraph identity drift: {row['case_id']}")
        _verify_v9_expected_subgraph(row, diff, graph, transformed)
        return
        if row["contract"] == SUBJECT_CONTRACT_ID:
            if len(subgraph["nodes"]) != 1 or len(
                diff.get("exact_instance_diffs", [])
            ) != 1:
                fail(f"subject expected subgraph cardinality drift: {row['case_id']}")
            node = subgraph["nodes"][0]
            instance_diff = diff["exact_instance_diffs"][0]
            replacement = row["adapter"]["replacement"]["fields"]
            before = graph["nodes"][row["adapter"]["selector"]["node_id"]][
                "fields"
            ]
            if row["case_id"] == "R5C-109":
                after = replacement["data_cutoff"]
                expected_selector = {"cutoff_ref": f"cutoff::{replacement['run_id']}"}
                expected_path = "/PublicCutoffEndpoint/exact_date"
                expected_before = before["data_cutoff"]
                expected_type = "PublicCutoffEndpoint"
                if node["exact_fields"].get("exact_date") != after:
                    fail("R5C-109 cutoff exact_date is not source mutation value")
            elif row["case_id"] == "R5C-110":
                after = replacement["actual_date"]
                expected_selector = {"event_ref": replacement["event_id"]}
                expected_path = "/TemporalEvent/start_endpoint/exact_date"
                expected_before = before["actual_date"]
                expected_type = "TemporalEvent"
                if node["exact_fields"].get("start_endpoint", {}).get(
                    "exact_date"
                ) != after:
                    fail("R5C-110 event exact_date is not source mutation value")
            elif row["case_id"] == "R5C-116":
                authority_ref = replacement["authority_ref"]
                authority = next(
                    item
                    for item in graph["nodes"].values()
                    if item["type"]
                    == "mm_r4.visit_schedule.ActualActivityRecord"
                    and item["fields"]["actual_activity_id"] == authority_ref
                )
                after = authority["fields"][replacement["authority_date_field"]]
                expected_selector = {"risk_ref": replacement["target_ref"]}
                expected_path = "/TemporalRiskAnchor/start_endpoint/exact_date"
                expected_before = None
                expected_type = "TemporalRiskAnchor"
                if node["exact_fields"].get("start_endpoint", {}).get(
                    "exact_date"
                ) != after:
                    fail("R5C-116 risk endpoint is not resolved authority value")
            else:
                fail(f"unexpected subject positive case: {row['case_id']}")
            if (
                node.get("type") != expected_type
                or node.get("instance_selector") != expected_selector
                or instance_diff.get("path") != expected_path
                or instance_diff.get("before") != expected_before
                or instance_diff.get("after") != after
                or not instance_diff.get("instance_selector")
            ):
                fail(f"subject exact instance diff drift: {row['case_id']}")
            return

        previous_nodes = _fixture_reachable(graph, "previous")
        previous_projection = next(
            graph["nodes"][node_id]
            for node_id in previous_nodes
            if graph["nodes"][node_id]["type"]
            == "AEMHMatchHistoryPublicProjection"
        )
        previous_threads = {
            graph["nodes"][node_id]["fields"]["thread_ref"]: graph["nodes"][node_id]
            for node_id in previous_nodes
            if graph["nodes"][node_id]["type"] == "AEMHMatchThread"
        }
        thread_nodes = {
            node["exact_fields"]["thread_ref"]: node
            for node in subgraph["nodes"]
            if node.get("type") == "AEMHMatchThread"
        }
        projection_nodes = [
            node for node in subgraph["nodes"]
            if node.get("type") == "AEMHMatchHistoryPublicProjection"
        ]
        if set(thread_nodes) != set(previous_threads) or len(projection_nodes) != 1:
            fail(f"AEMH expected thread/projection coverage drift: {row['case_id']}")
        decisions = [item["fields"] for item in row["adapter"]["replacement"]["tuple"]]
        for thread_ref, node in thread_nodes.items():
            previous_thread = previous_threads[thread_ref]["fields"]
            prefix = [
                copy.deepcopy(graph["nodes"][item["node_ref"]]["fields"])
                for item in previous_thread["history_entries"]["tuple"]
            ]
            relevant = [
                item for item in decisions
                if item["thread_ref"] == previous_thread["original_candidate_ref"]
            ]
            entries = node["exact_fields"]["history_entries"]
            if entries[:len(prefix)] != prefix or len(entries) != len(prefix) + len(relevant):
                fail(f"AEMH prefix/suffix cardinality drift: {row['case_id']}")
            prior_hash = prefix[-1]["entry_hash"]
            for ordinal, (entry, decision) in enumerate(
                zip(entries[len(prefix):], relevant), start=1
            ):
                seq = len(prefix) + ordinal
                entry_without_hash = {
                    key: value for key, value in entry.items() if key != "entry_hash"
                }
                if (
                    entry["seq"] != seq
                    or entry["prior_entry_hash"] != prior_hash
                    or entry["entry_id"] != canonical_hash([
                        thread_ref,
                        decision["event_kind"],
                        decision["authority_identity"],
                        seq,
                    ])
                    or entry["entry_hash"] != canonical_hash(entry_without_hash)
                    or entry["event_kind"] != decision["event_kind"]
                    or entry["match_state"] != decision["match_state"]
                    or entry["reason_code"] != decision["reason_code"]
                    or entry["later_fact_refs"]
                    != decision["later_fact_refs"]["tuple"]
                ):
                    fail(f"AEMH exact suffix chain drift: {row['case_id']}")
                prior_hash = entry["entry_hash"]
            expected_thread_hash = canonical_hash({
                "thread_ref": thread_ref,
                "entry_hashes": [entry["entry_hash"] for entry in entries],
            })
            if node["exact_fields"]["thread_content_hash"] != expected_thread_hash:
                fail(f"AEMH thread hash drift: {row['case_id']}")
        projection = projection_nodes[0]["exact_fields"]
        seed = {
            "previous_projection_ref": previous_projection["fields"]["projection_id"],
            "previous_projection_content_hash": previous_projection["fields"][
                "projection_content_hash"
            ],
            "thread_content_hashes": [
                node["exact_fields"]["thread_content_hash"]
                for node in subgraph["nodes"]
                if node.get("type") == "AEMHMatchThread"
            ],
        }
        projection_id = canonical_hash(seed)
        if (
            projection.get("projection_id") != projection_id
            or projection.get("projection_content_hash")
            != canonical_hash({**seed, "projection_id": projection_id})
            or sum(
                len(node["exact_fields"]["history_entries"])
                for node in thread_nodes.values()
            ) != 2 + len(decisions)
        ):
            fail(f"AEMH projection/history expected graph drift: {row['case_id']}")

    for row in runtime:
        source = accepted.get(row["case_id"])
        trace_sources = [accepted[case_id] for case_id in row["covered_case_ids"]]
        trace_metadata = row.get("case_trace_metadata", [])
        execution_source = accepted[
            row.get("execution_source_case_id", row["case_id"])
        ]
        if (
            source is None
            or row["accepted_registry_row"] != source
            or row.get("accepted_registry_rows") != trace_sources
            or [item.get("case_id") for item in trace_metadata]
            != row["covered_case_ids"]
            or any(
                set(item) != {
                    "case_id", "origin_projection",
                    "fully_reseal_after_mutation", "accepted_rule_id",
                    "fixture_key", "adapter", "harness_lane",
                    "future_spec_input_identity", "expected_outcome",
                }
                for item in trace_metadata
            )
            or any(
                item["expected_typed_outcome_or_error"].split(":", 1)[0]
                != source["expected_typed_outcome_or_error"].split(":", 1)[0]
                for item in trace_sources
            )
        ):
            fail(f"runtime accepted registry lineage drift: {row['case_id']}")
        for trace in trace_metadata:
            trace_graph = fixtures[trace["fixture_key"]]
            trace_transformed = _interpret_adapter(
                trace["adapter"], trace_graph, api
            )
            trace_identity_payload = {
                "transformed_input_constructor_graph": trace_transformed,
                "harness_lane": trace["harness_lane"],
            }
            if trace["harness_lane"] == "candidate_corruption":
                trace_identity_payload["decoder_stage"] = (
                    "typed_constructor_decode"
                )
            if (
                trace["future_spec_input_identity"]
                != canonical_hash(trace_identity_payload)
                or trace["future_spec_input_identity"]
                != row["future_spec_input_identity"]
                or trace["expected_outcome"] != row["expected_outcome"]
            ):
                fail(f"alias trace input/outcome equivalence drift: {trace['case_id']}")
        graph = fixtures[row["fixture_key"]]
        disposition = source["expected_typed_outcome_or_error"].split(":", 1)[0]
        if row["expected_outcome"]["disposition"] != disposition:
            fail(f"runtime accept/reject polarity drift: {row['case_id']}")
        if disposition == "accept":
            positive += 1
            if row["expected_outcome"]["primary_code"] is not None or row[
                "expected_outcome"
            ]["packet_type"] is None:
                fail(f"runtime positive oracle drift: {row['case_id']}")
            _validate_positive_adapter_semantics(row["adapter"], graph)
        elif row["expected_outcome"]["primary_code"] not in error_codes:
            fail(f"runtime negative oracle drift: {row['case_id']}")
        transformed = _interpret_adapter(row["adapter"], graph, api)
        if (
            row["origin_projection"] == "accepted_parent_inherited"
            and disposition == "accept"
        ):
            expected_plan = None
            expected_kind = "source_to_builder_output"
        elif row["origin_projection"] == "accepted_parent_inherited":
            expected_plan = None
            expected_kind = (
                "candidate_to_validator"
                if row["adapter"]["harness_lane"] == "typed_candidate_transform"
                else "constructor_decode"
            )
        elif execution_source.get("fully_reseal_after_mutation") is True:
            expected_plan = (
                "reseal_subject_base"
                if row["contract"] == SUBJECT_CONTRACT_ID
                else "reseal_aemh_base"
            )
            expected_kind = "reseal_plan"
        else:
            expected_plan = "stale_hash_none"
            expected_kind = "stale_hash_control"
        if row["reseal_plan"] != expected_plan or row[
            "fully_reseal_after_mutation"
        ] != execution_source.get("fully_reseal_after_mutation") or row.get(
            "execution_spec_kind"
        ) != expected_kind:
            fail(f"runtime reseal lineage drift: {row['case_id']}")
        if (
            row["future_runtime_oracle"]["contract_stage_executed"] is not False
            or row.get("contract_spec_only") is not True
            or row.get("producer_executed") is not False
        ):
            fail("runtime specification overclaims future execution")
        state_hash = canonical_hash(transformed)
        identity_payload = {
            "transformed_input_constructor_graph": transformed,
            "harness_lane": row["adapter"]["harness_lane"],
        }
        if row["adapter"]["harness_lane"] == "candidate_corruption":
            identity_payload["decoder_stage"] = "typed_constructor_decode"
        expected_key = canonical_hash(identity_payload)
        if (
            row.get("future_spec_input_identity") != expected_key
            or row["semantic_independence_key"] != expected_key
            or row.get("transformed_input_state_hash") != state_hash
            or "final_graph_hash" in row
            or "static_simulation" in row
        ):
            fail(f"future spec input identity drift: {row['case_id']}")
        identity_outcomes.setdefault(expected_key, set()).add(
            canonical_hash(row["expected_outcome"])
        )
        if disposition == "accept":
            positive_inputs.append(
                {
                    "case_id": row["case_id"],
                    "future_spec_input_identity": expected_key,
                }
            )
        if expected_kind == "source_to_builder_output":
            spec = row.get("builder_expected_diff_spec", {})
            direct, recomputed = expected_builder_paths(
                row["adapter"], graph, row["contract"]
            )
            diff = spec.get("expected_output_diff", {})
            if (
                set(spec)
                != {
                    "schema",
                    "contract_spec_only",
                    "producer_executed",
                    "future_test_locator",
                    "source_mutation",
                    "mechanical_rebuild_trace",
                    "expected_output_diff",
                    "expected_invariants",
                    "future_oracle",
                }
                or spec.get("schema")
                != "public-authority-builder-expected-diff-spec-v2"
                or spec.get("contract_spec_only") is not True
                or spec.get("producer_executed") is not False
                or spec.get("future_oracle") != row["expected_outcome"]
                or spec.get("source_mutation", {}).get("adapter_hash")
                != canonical_hash(row["adapter"])
                or spec.get("source_mutation", {}).get("root") != "source"
                or spec.get("source_mutation", {}).get("instance_selector")
                != row["adapter"]["selector"]
                or spec.get("source_mutation", {}).get(
                    "exact_changed_source_paths"
                ) != row["adapter"]["allowed_diff_paths"]
                or not row["adapter"]["allowed_diff_paths"]
                or set(diff) != {
                    "exact_direct_semantic_leaf_paths",
                    "exact_instance_diffs",
                    "post_adapter_expected_output_subgraph",
                    "post_adapter_expected_output_subgraph_hash",
                    "all_other_non_derived_semantic_leaves_unchanged_scope",
                    "required_recomputed_identity_and_hash_paths",
                }
                or diff.get("exact_direct_semantic_leaf_paths") != direct
                or diff.get("required_recomputed_identity_and_hash_paths")
                != recomputed
                or diff.get(
                    "all_other_non_derived_semantic_leaves_unchanged_scope"
                ) != "all output instances and fields outside exact_instance_diffs"
                or not all(
                    (row["contract"], path) in valid_output_paths
                    for path in [*direct, *recomputed]
                )
                or len(spec.get("expected_invariants", [])) != 4
                or spec.get("future_test_locator", {}).get("path")
                not in PRODUCER_ALLOWLIST
            ):
                fail(f"builder expected-diff spec drift: {row['case_id']}")
            if spec["source_mutation"].get("kind") != "exact_adapter":
                fail(f"builder source mutation linkage drift: {row['case_id']}")
            trace = spec["mechanical_rebuild_trace"]
            expected_operations = [
                {
                    "op": row["adapter"]["op"],
                    "selector": row["adapter"]["selector"],
                    "replacement": row["adapter"]["replacement"],
                },
                *row["adapter"]["linked_operations"],
            ]
            if (
                trace.get("schema")
                != "public-authority-mechanical-source-rebuild-trace-v1"
                or trace.get("input_roots")
                != (["source"] if row["contract"] == SUBJECT_CONTRACT_ID else ["source", "previous"])
                or trace.get("adapter_operation_count")
                != len(expected_operations)
                or trace.get("adapter_operations_hash")
                != canonical_hash(expected_operations)
                or trace.get("join_rows_executed")
                != sum(
                    join_row["contract"] == row["contract"]
                    for join_row in joins
                )
                or trace.get("reducer_rows_executed")
                != sum(
                    join_row["contract"] == row["contract"]
                    for join_row in joins
                )
                or trace.get("candidate_graph_used_as_mutation_input") is not False
            ):
                fail(f"mechanical source rebuild trace drift: {row['case_id']}")
            validate_expected_subgraph(row, diff, graph, transformed)
            positive_expected_packet_hashes.append(
                diff["post_adapter_expected_output_subgraph"]["nodes"][0][
                    "exact_fields"
                ]["packet_content_hash"]
            )
            if "inherited_reject_spec" in row:
                fail(f"positive row contains reject spec: {row['case_id']}")
        elif row["origin_projection"] == "accepted_parent_inherited":
            spec = row.get("inherited_reject_spec", {})
            if (
                set(spec) != {
                    "schema", "contract_spec_only", "producer_executed", "lane",
                    "root", "instance_selector", "adapter_hash",
                    "exact_changed_candidate_or_constructor_paths",
                    "expected_error", "future_test_locator",
                }
                or spec.get("schema")
                != "public-authority-inherited-reject-spec-v1"
                or spec.get("contract_spec_only") is not True
                or spec.get("producer_executed") is not False
                or spec.get("lane") != expected_kind
                or spec.get("root") != row["adapter"]["selector"]["root"]
                or spec.get("instance_selector") != row["adapter"]["selector"]
                or spec.get("adapter_hash") != canonical_hash(row["adapter"])
                or spec.get("exact_changed_candidate_or_constructor_paths")
                != row["adapter"]["allowed_diff_paths"]
                or not row["adapter"]["allowed_diff_paths"]
                or spec.get("expected_error") != {
                    "disposition": "reject",
                    "primary_code": row["expected_outcome"]["primary_code"],
                    "packet_type": None,
                }
                or spec.get("future_test_locator", {}).get("path")
                != "poc/medical_monitoring_ai_native_r5/tests/challenges/test_public_authority_runtime_challenges.py"
                or "builder_expected_diff_spec" in row
            ):
                fail(f"inherited reject lane spec drift: {row['case_id']}")
        else:
            spec = row.get("reseal_contract_spec", {})
            if (
                spec
                != {
                    "schema": "public-authority-future-reseal-contract-spec-v1",
                    "contract_spec_only": True,
                    "producer_executed": False,
                    "plan": expected_plan,
                    "plan_hash": canonical_hash(plans[expected_plan]),
                    "future_trace_required": expected_plan != "stale_hash_none",
                    "future_result_graph_hash_required": expected_plan
                    != "stale_hash_none",
                }
            ):
                fail(f"reseal contract-only spec drift: {row['case_id']}")
        if disposition == "accept" and row["contract"] == AEMH_CONTRACT_ID:
            records = row["adapter"]["replacement"]["tuple"]
            assertions = row.get("future_aemh_append_assertions", {})
            expected_refs = [item["fields"]["decision_ref"] for item in records]
            expected_identities = [
                item["fields"]["authority_identity"] for item in records
            ]
            expected_subgraph = row["builder_expected_diff_spec"][
                "expected_output_diff"
            ]["post_adapter_expected_output_subgraph"]
            expected_packet = expected_subgraph["nodes"][0]["exact_fields"]
            expected_lengths = {
                thread["thread_ref"]: len(thread["history_entries"])
                for thread in expected_packet["projection"]["threads"]
            }
            expected_projection_id = expected_packet["projection"]["projection_id"]
            if (
                assertions.get("schema")
                != "public-authority-aemh-future-append-assertions-v1"
                or assertions.get("contract_spec_only") is not True
                or assertions.get("producer_executed") is not False
                or assertions.get("exact_decision_refs") != expected_refs
                or assertions.get("exact_authority_identities")
                != expected_identities
                or assertions.get("exact_suffix_length") != len(records)
                or assertions.get("expected_output_subgraph_hash")
                != canonical_hash(expected_subgraph)
                or assertions.get("exact_thread_history_lengths")
                != expected_lengths
                or assertions.get("exact_projection_id")
                != expected_projection_id
                or len(assertions.get("assertions", [])) != 6
            ):
                fail(f"AE/MH future append assertion drift: {row['case_id']}")
            all_positive_decision_refs.extend(expected_refs)
            all_positive_authority_identities.extend(expected_identities)
        lane_counts[expected_kind] = lane_counts.get(expected_kind, 0) + 1
    contradictory = [
        identity
        for identity, outcomes in identity_outcomes.items()
        if len(outcomes) > 1
    ]
    if contradictory:
        fail("contradictory identical future input specs")
    if (
        len(all_positive_decision_refs) != len(set(all_positive_decision_refs))
        or len(all_positive_authority_identities)
        != len(set(all_positive_authority_identities))
    ):
        fail("positive decision identities are not globally unique")
    if positive != 10 or lane_counts != {
        "source_to_builder_output": 10,
        "constructor_decode": 52,
        "stale_hash_control": 53,
        "reseal_plan": 116,
    }:
        fail("runtime positive/reseal lane count drift")
    if (
        len(positive_expected_packet_hashes) != 10
        or len(set(positive_expected_packet_hashes)) != 10
    ):
        fail("positive exact post-adapter packet hashes are not ten unique values")
    expected_identity_audit = {
        "schema": "public-authority-future-spec-identity-audit-v2",
        "identity_payload_exact_keys": [
            "transformed_input_constructor_graph",
            "harness_lane",
        ],
        "candidate_corruption_additional_identity_key": "decoder_stage",
        "oracle_and_labels_excluded": [
            "accepted_rule_id",
            "case_id",
            "expected_outcome",
            "expected_primary_code",
            "rule_id",
        ],
        "historical_reviewer_v4_collision_summary": {
            "group_count": 15,
            "row_count": 104,
            "complete_case_membership_available": False,
            "known_examples_only": [
                ["PA-007", "PA-008"],
                ["PA-025", "PA-026"],
                ["R5C-157", "R5C-158"],
            ],
            "non_fabrication_rule": "do not invent the unavailable remaining historical case membership",
        },
        "historical_reviewer_v5_collision_summary": {
            "duplicate_group_count": 10,
            "known_conflict_pairs": [
                ["PA-010", "R5C-149"],
                ["PA-013", "PA-142"],
                ["PA-033", "PA-192"],
                ["PA-127", "R5C-137"],
            ],
            "resolution": "case-specific authority-field or authority-subgraph transformations frozen as exact future input specs",
        },
        "current_spec_count": 231,
        "current_distinct_spec_input_identity_count": len(identity_outcomes),
        "current_conflict_groups": [],
        "current_conflict_row_count": 0,
        "contradictory_identical_specs": [],
        "positive_future_input_specs": positive_inputs,
        "producer_output_graph_hashes_available": False,
        "reviewer_v9_contract_controls": {
            "common_scope_fixture_count": 5,
            "subject_baseline_instance_cases": [
                "R5C-109", "R5C-110", "R5C-116"
            ],
            "aemh_exact_expected_packet_cases": [
                "R5C-157", "R5C-158", "R5C-159", "R5C-160",
                "R5C-161", "R5C-162", "R5C-163"
            ],
            "targeted_negative_control_count": 7,
            "total_in_memory_control_count": 66,
        },
        "reviewer_v10_contract_controls": {
            "authority_context_reflection_count": 0,
            "reducer_rows_independently_executed": 272,
            "cutoff_chain_fixture_count": 5,
            "r5c109_linked_operation_count": 5,
            "targeted_negative_controls": [
                {"control": "invalid_TimeRef_ISO_date", "code": "PUB_DATE_INVALID"},
                {"control": "ScopeBinding_cutoff_AUTH_placeholder", "code": "PUB_DATE_INVALID"},
                {"control": "cross_source_cutoff_mismatch", "code": "PUB_IDENTITY_CUTOFF_MISMATCH"},
                {"control": "authority_context_reflection", "code": "PUB_REFERENCE_UNRESOLVED"},
                {"control": "selected_reducer_value_output_mismatch", "code": "row.unavailable_fail_closed_code"},
                {"control": "R5C_109_missing_linked_operation", "code": "PUB_IDENTITY_CUTOFF_MISMATCH"},
            ],
            "total_in_memory_control_count": 72,
        },
        "non_semantic_dedup_contract_delta": {
            "distinct_future_executable_specs": 231,
            "accepted_case_ids_covered": 236,
            "alias_group_count": 5,
            "alias_case_delta": 5,
            "equation": "231 + 5 = 236",
            "accepted_parent_artifacts_modified": False,
        },
    }
    if (
        matrix.get("input_identity_audit") != expected_identity_audit
        or len(
            {row["future_spec_input_identity"] for row in positive_inputs}
        )
        != 10
    ):
        fail("runtime input identity audit drift")
    governance_ids = {row["case_id"] for row in governance}
    if len(governance_ids) != 22:
        fail("governance case identity drift")
    for row in governance:
        if row["accepted_registry_row"] != accepted[row["case_id"]]:
            fail(f"governance accepted lineage drift: {row['case_id']}")
        expected = row["probe"]["expected_exact_ordered_issues"]
        if not expected or row["primary_code"] != expected[0] or row["probe"][
            "baseline_expected_exact_issues"
        ] != []:
            fail(f"governance ordered issue oracle drift: {row['case_id']}")
        if row["case_id"] in {"PA-147", "PA-148", "PA-149"} and expected != [
            "PUB_OVERLAY_ARTIFACT_MISMATCH",
            "PUB_OVERLAY_DEFERRED_SET_MISMATCH",
        ]:
            fail(f"governance composite oracle drift: {row['case_id']}")
    coverage = matrix.get("coverage_lanes", {})
    if coverage.get("closed") != [
        "contract-structural",
        "constructor-decode",
        "future-runtime",
        "governance",
    ] or set(coverage.get("by_error_code", {})) != error_codes:
        fail("81-code coverage lane closure drift")
    for code, entries in coverage["by_error_code"].items():
        if not entries:
            fail(f"error code has no constructible lane: {code}")
        for entry in entries:
            if entry.get("lane") not in coverage["closed"] or not isinstance(
                entry.get("spec"), dict
            ) or not entry["spec"]:
                fail(f"error coverage contains id/prose-only lane: {code}")
    if matrix.get("execution_contract") != {
        "classification": "exact future runtime specifications; producer outputs are unavailable and unexecuted at contract stage",
        "fixture_constructor_graphs_typechecked": True,
        "adapter_dsl_interpreted": True,
        "reseal_dsl_syntax_type_and_dag_validated_only": True,
        "producer_output_graphs_constructed_now": False,
        "validator_dynamic_vectors_executed_now": False,
        "governance_exact_ordered_issue_probes_executed_now": True,
        "reseal_plan_spec_count": 116,
        "stale_hash_none_case_count": 53,
        "inherited_lineage_spec_count": 64,
        "builder_expected_diff_spec_count": 10,
        "candidate_validator_spec_count": 0,
        "constructor_decode_spec_count": 52,
        "positive_legal_transform_count": 10,
        "runtime_spec_count": 231,
        "accepted_case_trace_count": 236,
        "governance_count": 22,
        "error_union_planned_coverage_count": 81,
    }:
        fail("contract-stage execution/lane boundary drift")
    sensitivity = matrix.get("future_dynamic_sensitivity_tests", {})
    vectors = sensitivity.get("vectors", [])
    if (
        sensitivity.get("schema")
        != "public-authority-future-validator-sensitivity-v2"
        or sensitivity.get("contract_stage_executed") is not False
        or sensitivity.get("producer_executed") is not False
        or sensitivity.get("runtime_proof_claimed") is not False
        or sensitivity.get("pytest_node")
        != "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py::test_dynamic_sensitivity_vectors"
        or len(vectors) != 10
    ):
        fail("future validator sensitivity specification drift")
    vector_counts: dict[tuple[str, str], int] = {}
    vector_ids: set[str] = set()
    runtime_by_case = {row["case_id"]: row for row in runtime}
    for vector in vectors:
        if set(vector) != {
            "vector_id",
            "function",
            "dimension",
            "baseline_fixture",
            "mutation",
            "held_fixed",
            "expected_primary_code",
            "required_changed_sinks",
        } or vector["vector_id"] in vector_ids:
            fail("future validator vector schema/identity drift")
        vector_ids.add(vector["vector_id"])
        if vector["expected_primary_code"] not in error_codes or vector[
            "required_changed_sinks"
        ] != ["issues", "ok", "primary_code"]:
            fail("future validator vector oracle drift")
        function = vector["function"]
        dimension = vector["dimension"]
        vector_counts[(function, dimension)] = vector_counts.get(
            (function, dimension), 0
        ) + 1
        mutation = vector["mutation"]
        if mutation["kind"] == "runtime_case_adapter":
            source_row = runtime_by_case.get(mutation["case_id"])
            if source_row is None or mutation["adapter_hash"] != canonical_hash(
                source_row["adapter"]
            ) or mutation.get("instance_selector") != source_row["adapter"][
                "selector"
            ]:
                fail("future candidate vector locator drift")
        elif mutation["kind"] == "typed_field_replace":
            graph = fixtures[vector["baseline_fixture"]]
            reachable = _fixture_reachable(graph, mutation["root"])
            selector = mutation.get("instance_selector", {})
            if (
                selector
                != {
                    "root": mutation["root"],
                    "node_id": selector.get("node_id"),
                    "field": mutation["field"],
                    "match": "exact_one",
                }
                or selector.get("node_id") not in reachable
                or graph["nodes"][selector["node_id"]]["type"]
                != mutation["owner"]
                or mutation["field"]
                not in graph["nodes"][selector["node_id"]]["fields"]
            ):
                fail("future source/previous vector path unresolved")
        else:
            fail("future validator vector mutation kind drift")
        expected_held = (
            ["source"]
            if function == "validate_subject_temporal_authority"
            and dimension == "candidate"
            else ["candidate"]
            if function == "validate_subject_temporal_authority"
            and dimension == "source"
            else ["source", "previous_packet"]
            if dimension == "candidate"
            else ["candidate", "previous_packet"]
            if dimension == "source"
            else ["candidate", "source"]
        )
        if vector["held_fixed"] != expected_held:
            fail("future validator held-fixed parameter drift")
    if sensitivity.get("exact_vector_ids") != [
        vector["vector_id"] for vector in vectors
    ]:
        fail("future validator exact vector coverage drift")
    if vector_counts != {
        ("validate_subject_temporal_authority", "candidate"): 2,
        ("validate_subject_temporal_authority", "source"): 2,
        ("validate_aemh_match_history_authority", "candidate"): 2,
        ("validate_aemh_match_history_authority", "source"): 2,
        ("validate_aemh_match_history_authority", "previous_packet"): 2,
    }:
        fail("future validator vector dimension coverage drift")
    return matrix


def _exact_ordered_issue_oracle(expected: Sequence[str], observed: Sequence[str]) -> bool:
    return list(observed) == list(expected)


def verify_all_governance_probes(tests: Mapping[str, Any]) -> int:
    parent = load_module(PARENT_VERIFIER_PATH, "governance_probe_parent_verifier")
    parent_exact = read_json(
        ROOT / "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json"
    )
    artifact_by_contract = {
        "exact-overlay-v0.1": PUBLIC_ARTIFACT_DIR / "exact_overlay.json",
        "source-matrix-v0.1": PUBLIC_ARTIFACT_DIR / "source_matrix.json",
        "manifest-v0.1": PUBLIC_ARTIFACT_DIR / "manifest.json",
    }

    def issues_for(contract: str, artifact: Mapping[str, Any]) -> list[str]:
        if contract == "exact-overlay-v0.1":
            return parent.overlay_validation_issues(artifact, parent_exact)
        if contract == "source-matrix-v0.1":
            return parent.source_matrix_validation_issues(artifact)
        return parent.manifest_contract_validation_issues(artifact)

    executed = 0
    for row in tests["contract_verifier_governance_cases"]:
        probe = row["probe"]
        baseline = read_json(artifact_by_contract[row["contract"]])
        observed_baseline = issues_for(row["contract"], baseline)
        if observed_baseline != probe["baseline_expected_exact_issues"]:
            fail(
                f"governance baseline issue drift: {row['case_id']} "
                f"expected={probe['baseline_expected_exact_issues']} "
                f"observed={observed_baseline}"
            )
        mutated = copy.deepcopy(baseline)
        parent.apply_mutation(mutated, probe["mutation"])
        if (
            row["contract"] == "manifest-v0.1"
            and probe["reseal_manifest"] is True
        ):
            mutated["manifest_content_hash"] = parent.canonical_hash(
                {
                    key: value
                    for key, value in mutated.items()
                    if key != "manifest_content_hash"
                }
            )
        observed = issues_for(row["contract"], mutated)
        expected = probe["expected_exact_ordered_issues"]
        if not _exact_ordered_issue_oracle(expected, observed) or row[
            "primary_code"
        ] != expected[0]:
            fail(
                f"governance executable probe failed: {row['case_id']} "
                f"expected={expected} observed={observed}"
            )
        executed += 1
    if executed != 22:
        fail(f"governance executable probe count mismatch: {executed}")
    return executed


def _static_gate_validation_issues(spec: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    expected_targets = [
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py",
    ]
    if spec.get("scanner") != (
        "Python ast.parse(feature_version=(3,9)) over each exact UTF-8 source target; "
        "resolve import/call/annotation aliases and reject before imports or tests execute"
    ) or spec.get("python_ast_feature_version") != [3, 9]:
        issues.append("scanner")
    if spec.get("exact_source_targets") != expected_targets:
        issues.append("source targets")
    if spec.get("forbidden_ast_nodes") != ["Assert", "Lambda", "NamedExpr"]:
        issues.append("AST nodes")
    if spec.get("forbidden_import_roots") != [
        "artifacts",
        "importlib",
        "io",
        "os",
        "pathlib",
        "tests",
        "tools",
    ]:
        issues.append("import roots")
    if set(spec.get("forbidden_call_names", [])) != {
        "__import__",
        "compile",
        "delattr",
        "eval",
        "exec",
        "getattr",
        "globals",
        "hasattr",
        "locals",
        "open",
        "setattr",
        "vars",
    }:
        issues.append("call names")
    if set(spec.get("forbidden_call_attributes", [])) != {
        "open",
        "read",
        "read_bytes",
        "read_text",
        "write",
        "write_bytes",
        "write_text",
    }:
        issues.append("call attributes")
    if set(spec.get("forbidden_branch_identifier_names", [])) != {
        "adapter_id",
        "case_id",
        "fixture_id",
        "sentinel",
    }:
        issues.append("branch identifiers")
    patterns = spec.get("forbidden_string_literal_patterns", [])
    if len(patterns) != 5 or not all(isinstance(item, str) for item in patterns):
        issues.append("literal patterns")
    else:
        for pattern in patterns:
            re.compile(pattern)
    builder_rule = spec.get("public_builder_parameter_rule", {})
    if builder_rule != {
        "exact_parameter_names_by_function": {
            "build_subject_temporal_authority": ["source"],
            "build_aemh_match_history_authority": ["source", "previous_packet"],
        },
        "forbidden_annotation_tokens": ["Any", "Mapping", "dict"],
    }:
        issues.append("builder parameter rule")
    expected_functions = {
        "build_subject_temporal_authority": {
            "parameters": [["source", "SubjectTemporalSourceBundle"]],
            "return": "SubjectTemporalAuthorityPacket",
            "defaults": {},
        },
        "validate_subject_temporal_authority": {
            "parameters": [
                ["candidate", "SubjectTemporalAuthorityPacket"],
                ["source", "SubjectTemporalSourceBundle"],
            ],
            "return": "PublicAuthorityValidationResult",
            "defaults": {},
        },
        "build_aemh_match_history_authority": {
            "parameters": [
                ["source", "AEMHMatchHistorySourceBundle"],
                ["previous_packet", "Optional[AEMHMatchHistoryAuthorityPacket]"],
            ],
            "return": "AEMHMatchHistoryAuthorityPacket",
            "defaults": {"previous_packet": "None"},
        },
        "validate_aemh_match_history_authority": {
            "parameters": [
                ["candidate", "AEMHMatchHistoryAuthorityPacket"],
                ["source", "AEMHMatchHistorySourceBundle"],
                [
                    "previous_packet",
                    "Optional[AEMHMatchHistoryAuthorityPacket]",
                ],
            ],
            "return": "PublicAuthorityValidationResult",
            "defaults": {"previous_packet": "None"},
        },
    }
    if spec.get("exact_public_function_contracts") != expected_functions:
        issues.append("function contracts")
    if spec.get("function_parameter_rules") != {
        "vararg_forbidden": True,
        "kwarg_forbidden": True,
        "positional_only_forbidden": True,
        "keyword_only_forbidden": True,
        "annotation_aliases_resolved": True,
        "forbidden_annotation_origins": [
            "Any",
            "Mapping",
            "collections.abc.Mapping",
            "dict",
            "typing.Any",
            "typing.Mapping",
            "Union[...,Any]",
        ],
    }:
        issues.append("function parameter rules")
    expected_indirect = {
        "__import__",
        "compile",
        "delattr",
        "eval",
        "exec",
        "getattr",
        "globals",
        "hasattr",
        "locals",
        "open",
        "setattr",
        "vars",
        "importlib.import_module",
        "io.open",
        "pathlib.Path.open",
        "pathlib.Path.read",
        "pathlib.Path.read_bytes",
        "pathlib.Path.read_text",
        "pathlib.Path.write",
        "pathlib.Path.write_bytes",
        "pathlib.Path.write_text",
    }
    if set(spec.get("forbidden_indirect_callable_origins", [])) != expected_indirect:
        issues.append("indirect calls")
    if spec.get("alias_resolution") != (
        "track Import/ImportFrom aliases and simple Name assignments whose RHS "
        "resolves to a forbidden callable; reject calls through any resolved alias"
    ):
        issues.append("alias resolution")
    import_policy = spec.get("import_policy", {})
    if (
        set(import_policy)
        != {
            "exact_module_symbol_allowlist",
            "exact_whole_module_allowlist",
            "external_executable_helper_import_forbidden",
            "relative_forbidden",
            "top_level_only",
            "wildcard_forbidden",
        }
        or not all(
            import_policy.get(key) is True
            for key in (
                "external_executable_helper_import_forbidden",
                "relative_forbidden",
                "top_level_only",
                "wildcard_forbidden",
            )
        )
        or not import_policy.get("exact_module_symbol_allowlist")
        or import_policy.get("exact_whole_module_allowlist")
        != ["dataclasses", "hashlib"]
    ):
        issues.append("exact import policy")
    call_graph = spec.get("reachable_call_graph_policy", {})
    if (
        call_graph.get("entrypoints")
        != [
            "build_subject_temporal_authority",
            "validate_subject_temporal_authority",
            "build_aemh_match_history_authority",
            "validate_aemh_match_history_authority",
        ]
        or call_graph.get("closed_call_targets")
        != [
            "local_scanned_function",
            "exact_dataclass_constructor",
            "exact_stdlib_callable",
        ]
        or call_graph.get("all_reachable_helpers_scanned") is not True
        or call_graph.get("alias_chains_fully_resolved") is not True
        or call_graph.get("unresolved_method_or_dynamic_attribute_forbidden") is not True
        or call_graph.get("exact_safe_bound_methods")
        != ["add", "append", "encode", "extend", "hexdigest"]
    ):
        issues.append("reachable call graph policy")
    taint = spec.get("validator_taint_policy", {})
    future_dynamic = taint.get("future_dynamic_sensitivity_gate", {})
    if (
        taint.get("required_loads")
        != {
            "validate_subject_temporal_authority": ["candidate", "source"],
            "validate_aemh_match_history_authority": [
                "candidate",
                "source",
                "previous_packet",
            ],
        }
        or taint.get("result_and_primary_code_jointly_depend_on_candidate_and_source")
        is not True
        or taint.get("aemh_noninitial_depends_on_previous") is not True
        or not taint.get("accepted_sinks")
        or not taint.get("non_sinks")
        or future_dynamic
        != {
            "schema": "public-authority-future-validator-sensitivity-v2",
            "contract_stage_execution": "forbidden",
            "vector_source": "test_matrix.future_dynamic_sensitivity_tests.vectors",
            "required_dimensions": {
                "validate_subject_temporal_authority": ["candidate", "source"],
                "validate_aemh_match_history_authority": [
                    "candidate",
                    "source",
                    "previous_packet",
                ],
            },
            "minimum_vectors_per_dimension": 2,
            "required_observed_sinks": ["issues", "ok", "primary_code"],
            "future_execution_rule": "after all producer and test targets exist, import the real producers through the frozen pytest suite and execute every exact vector; a dimension passes only when at least one sink changes from its paired baseline and primary_code equals expected_primary_code",
            "hardcoded_ir_runtime_proof_forbidden": True,
            "pytest_node": "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_source_joins.py::test_dynamic_sensitivity_vectors",
            "command_keys": [
                "sensitivity_pytest_normal",
                "sensitivity_pytest_o2",
            ],
            "exact_vector_coverage_rule": "the pytest node loads test_matrix.future_dynamic_sensitivity_tests.exact_vector_ids and executes each id exactly once in normal and O2 modes",
        }
    ):
        issues.append("validator taint policy")
    binding = spec.get("symbol_binding_policy", {})
    if (
        binding.get("protected_symbols")
        != "every exact imported symbol, exact stdlib callable terminal, __builtins__, and public entrypoint; owned dataclass definitions are the sole constructor-definition exception"
        or binding.get("forbidden_binding_forms")
        != [
            "Assign",
            "AnnAssign",
            "NamedExpr",
            "tuple_or_list_target",
            "subscript_or_attribute_target",
            "parameter",
            "function_definition",
            "class_definition",
            "import_alias",
        ]
        or set(binding.get("owned_constructor_symbols_by_target", {}))
        != set(expected_targets)
        or any(
            not values or values != sorted(set(values))
            for values in binding.get(
                "owned_constructor_symbols_by_target", {}
            ).values()
        )
    ):
        issues.append("symbol binding policy")
    isolation = spec.get("future_isolation_gate", {})
    src_root = str((ROOT / "poc/medical_monitoring_ai_native_r5/src").resolve())
    tests_root = str((ROOT / "poc/medical_monitoring_ai_native_r5/tests").resolve())
    isolation_entry = str((
        ROOT
        / "poc/medical_monitoring_ai_native_r5/tests/test_public_authority_readonly_gate.py"
    ).resolve())
    if (
        isolation.get("subprocess") != "python3 -I -B"
        or isolation.get("entrypoint") != isolation_entry
        or isolation.get("cli_flag") != "--isolation-probe"
        or isolation.get("bootstrap_paths") != [src_root, tests_root]
        or isolation.get("bootstrap_rule")
        != "resolve and equality-check the frozen src/tests paths, insert only those two paths into sys.path, import all three producer modules and fixture support, then install the audit hook"
        or isolation.get("initial_import_under_hook") is not False
        or isolation.get("audit_hook_installed_after_import") is not True
        or isolation.get("audit_hook_active_only_during_public_api_calls") is not True
        or isolation.get("exact_public_api_calls")
        != [
            "build_subject_temporal_authority",
            "validate_subject_temporal_authority",
            "build_aemh_match_history_authority",
            "validate_aemh_match_history_authority",
        ]
        or isolation.get("audit_hook_denies")
        != [
            "open", "file-read", "file-write", "socket", "network",
            "subprocess", "os.system", "import", "exec", "eval", "compile",
        ]
        or not isolation.get("positive_probe")
        or not isolation.get("negative_probe")
        or isolation.get("runtime_identifiers_forbidden")
        != ["adapter_id", "case_id", "fixture_id", "sentinel"]
    ):
        issues.append("future isolation gate")
    allowed = spec.get("allowed_import_roots_by_target", {})
    if set(allowed) != set(expected_targets) or any(
        not roots
        or roots != sorted(set(roots))
        or any(root in {"artifacts", "tests", "tools"} for root in roots)
        for roots in allowed.values()
    ):
        issues.append("allowed imports")
    commands = spec.get("producer_acceptance_commands", {})
    if set(commands) != {
        "contract_verifier",
        "isolation_probe",
        "pytest_normal",
        "pytest_o2",
        "ruff_exact",
        "sensitivity_pytest_normal",
        "sensitivity_pytest_o2",
        "static_ast_scan",
    }:
        issues.append("producer command keys")
    else:
        if "--scan-future-runtime" not in commands["static_ast_scan"]:
            issues.append("static command")
        if "PYTHONOPTIMIZE=2" not in commands["pytest_o2"]:
            issues.append("O2 command")
        sensitivity_node = future_dynamic["pytest_node"]
        if commands["sensitivity_pytest_normal"] != (
            "PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q "
            + sensitivity_node
        ) or commands["sensitivity_pytest_o2"] != (
            "PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q "
            + sensitivity_node
        ):
            issues.append("sensitivity pytest commands")
        if commands["isolation_probe"] != (
            "python3 -I -B " + isolation_entry
            + " --isolation-probe --src-root " + src_root
            + " --tests-root " + tests_root
        ):
            issues.append("isolation command")
        if not all(target in commands["ruff_exact"] for target in expected_targets):
            issues.append("Ruff targets")
        future_tests = sorted(
            relative
            for relative in PRODUCER_ALLOWLIST
            if relative.endswith(".py")
            and "/tests/" in relative
            and Path(relative).name != "public_authority_runtime_fixtures.py"
        )
        for name in ("pytest_normal", "pytest_o2"):
            if not all(test in commands[name] for test in future_tests):
                issues.append(f"pytest targets:{name}")
    return issues


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _resolve_dotted_alias(name: str, aliases: Mapping[str, str]) -> str:
    first, separator, rest = name.partition(".")
    resolved = aliases.get(first, first)
    return f"{resolved}.{rest}" if separator else resolved


def _normalized_annotation(
    node: Optional[ast.AST], aliases: Mapping[str, str]  # noqa: UP045 -- Python 3.9 contract tool
) -> str:
    if node is None:
        return ""
    if isinstance(node, (ast.Name, ast.Attribute)):
        resolved = _resolve_dotted_alias(_dotted_name(node), aliases)
        terminal = resolved.rsplit(".", 1)[-1]
        return "Optional" if terminal == "Optional" else terminal
    if isinstance(node, ast.Constant) and node.value is None:
        return "None"
    if isinstance(node, ast.Subscript):
        outer = _normalized_annotation(node.value, aliases)
        values = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
        members = [_normalized_annotation(value, aliases) for value in values]
        if outer == "Union" and "None" in members and len(members) == 2:
            return f"Optional[{next(item for item in members if item != 'None')}]"
        return f"{outer}[{','.join(members)}]"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        members = [
            _normalized_annotation(node.left, aliases),
            _normalized_annotation(node.right, aliases),
        ]
        if "None" in members:
            return f"Optional[{next(item for item in members if item != 'None')}]"
        return f"Union[{','.join(members)}]"
    return ast.unparse(node).replace(" ", "")


def _function_target(relative: str, function_name: str) -> bool:
    if relative.endswith("/subject_temporal_public.py"):
        return "subject_temporal" in function_name
    if relative.endswith("/aemh_match_history_public.py"):
        return "aemh_match_history" in function_name
    return False


def _binding_target_names(node: ast.AST) -> set[str]:
    return {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
    }


def _expression_taint(node: Optional[ast.AST], taint: Mapping[str, set[str]]) -> set[str]:  # noqa: UP045 -- Python 3.9 contract tool
    if node is None:
        return set()
    result: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            result.update(taint.get(child.id, set()))
    return result


def _validator_result_issues(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef],  # noqa: UP007 -- Python 3.9 contract tool
    function_name: str,
    aliases: Mapping[str, str],
    required: list[str],
) -> list[str]:
    issues: list[str] = []
    for item in ast.walk(node):
        if isinstance(item, ast.Compare):
            operands = [item.left, *item.comparators]
            if any(
                ast.dump(left, include_attributes=False)
                == ast.dump(right, include_attributes=False)
                for left, right in zip(operands, operands[1:])  # noqa: RUF007 -- itertools.pairwise is Python 3.10+
            ):
                issues.append(
                    f"validator self comparison:{function_name}:{item.lineno}"
                )
            direct_names = {
                operand.id for operand in operands if isinstance(operand, ast.Name)
            }
            if {"candidate", "source"}.issubset(direct_names):
                issues.append(
                    f"validator incompatible parameter comparison:{function_name}:{item.lineno}"
                )
        if isinstance(item, ast.IfExp) and ast.dump(
            item.body, include_attributes=False
        ) == ast.dump(item.orelse, include_attributes=False):
            issues.append(
                f"validator identical branch sinks:{function_name}:{item.lineno}"
            )
        if isinstance(item, ast.If) and item.body and item.orelse:
            body_returns = [child for child in item.body if isinstance(child, ast.Return)]
            else_returns = [child for child in item.orelse if isinstance(child, ast.Return)]
            if (
                len(body_returns) == 1
                and len(else_returns) == 1
                and ast.dump(body_returns[0].value, include_attributes=False)
                == ast.dump(else_returns[0].value, include_attributes=False)
            ):
                issues.append(
                    f"validator identical branch sinks:{function_name}:{item.lineno}"
                )
    taint: dict[str, set[str]] = {name: {name} for name in required}
    parents: dict[ast.AST, ast.AST] = {
        child: parent for parent in ast.walk(node) for child in ast.iter_child_nodes(parent)
    }

    def control_taint(item: ast.AST) -> set[str]:
        result: set[str] = set()
        current = parents.get(item)
        while current is not None and current is not node:
            if isinstance(current, (ast.If, ast.IfExp, ast.While)):
                result.update(_expression_taint(current.test, taint))
            elif isinstance(current, (ast.For, ast.AsyncFor)):
                result.update(_expression_taint(current.iter, taint))
            current = parents.get(current)
        return result

    for _iteration in range(max(8, len(list(ast.walk(node))))):
        changed = False
        for item in ast.walk(node):
            value: Optional[ast.AST] = None  # noqa: UP045 -- Python 3.9 contract tool
            targets: set[str] = set()
            if isinstance(item, ast.Assign):
                value = item.value
                targets = set().union(*(_binding_target_names(target) for target in item.targets))
            elif (
                isinstance(item, ast.AnnAssign) and item.value is not None
            ) or isinstance(item, ast.AugAssign):
                value = item.value
                targets = _binding_target_names(item.target)
            if value is not None:
                value_taint = _expression_taint(value, taint) | control_taint(item)
                for target in targets:
                    updated = taint.get(target, set()) | value_taint
                    if updated != taint.get(target, set()):
                        taint[target] = updated
                        changed = True
            if (
                isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and item.func.attr in {"add", "append", "extend"}
            ):
                target_names = {
                    child.id
                    for child in ast.walk(item.func.value)
                    if isinstance(child, ast.Name)
                }
                value_taint = control_taint(item)
                for argument in [*item.args, *(keyword.value for keyword in item.keywords)]:
                    value_taint.update(_expression_taint(argument, taint))
                for target in target_names:
                    updated = taint.get(target, set()) | value_taint
                    if updated != taint.get(target, set()):
                        taint[target] = updated
                        changed = True
        if not changed:
            break

    assignments: dict[str, list[ast.AST]] = {}
    for item in ast.walk(node):
        if isinstance(item, ast.Assign):
            for target in item.targets:
                for name in _binding_target_names(target):
                    assignments.setdefault(name, []).append(item.value)
        elif isinstance(item, ast.AnnAssign) and item.value is not None:
            for name in _binding_target_names(item.target):
                assignments.setdefault(name, []).append(item.value)

    def result_call(value: Optional[ast.AST]) -> Optional[ast.Call]:  # noqa: UP045 -- Python 3.9 contract tool
        if isinstance(value, ast.Name):
            candidates = assignments.get(value.id, [])
            if len(candidates) != 1:
                return None
            return result_call(candidates[0])
        if not isinstance(value, ast.Call):
            return None
        resolved = _resolve_dotted_alias(_dotted_name(value.func), aliases)
        if resolved.rsplit(".", 1)[-1] != "PublicAuthorityValidationResult":
            return None
        return value

    returns = [item for item in ast.walk(node) if isinstance(item, ast.Return)]
    if not returns:
        return [f"validator exact result constructor:{function_name}:missing return"]
    required_set = set(required)
    for returned in returns:
        call = result_call(returned.value)
        if call is None:
            issues.append(f"validator exact result constructor:{function_name}:{returned.lineno}")
            continue
        if call.args or any(keyword.arg is None for keyword in call.keywords):
            issues.append(f"validator result keyword shape:{function_name}:{returned.lineno}")
            continue
        fields = {keyword.arg: keyword.value for keyword in call.keywords}
        if set(fields) != {"issues", "ok", "primary_code"}:
            issues.append(f"validator result fields:{function_name}:{returned.lineno}")
            continue
        for field_name in ("issues", "ok", "primary_code"):
            observed = _expression_taint(fields[field_name], taint) | control_taint(call)
            if not required_set.issubset(observed):
                missing = ",".join(sorted(required_set - observed))
                issues.append(
                    f"validator joint taint:{function_name}:{field_name}:{missing}"
                )
    return issues


def _future_runtime_source_issues(
    source: str, relative: str, spec: Mapping[str, Any]
) -> list[str]:
    issues: list[str] = []
    try:
        tree = ast.parse(
            source,
            filename=relative,
            feature_version=tuple(spec["python_ast_feature_version"]),
        )
    except SyntaxError:
        return ["python39 syntax"]
    allowed_imports = set(spec["allowed_import_roots_by_target"][relative])
    import_policy = spec["import_policy"]
    exact_imports = import_policy["exact_module_symbol_allowlist"]
    exact_whole_modules = set(import_policy["exact_whole_module_allowlist"])
    aliases: dict[str, str] = {}
    forbidden_import_roots = set(spec["forbidden_import_roots"])
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".", 1)[0]] = alias.name
                root = alias.name.split(".", 1)[0]
                if (
                    alias.name not in exact_whole_modules
                    or root not in allowed_imports
                    or root in forbidden_import_roots
                    or any(
                        alias.name == prefix or alias.name.startswith(prefix + ".")
                        for prefix in spec["forbidden_import_prefixes"]
                    )
                ):
                    issues.append(f"import:{node.lineno}:{alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".", 1)[0]
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{module}.{alias.name}".strip(".")
            if (
                node.level
                or any(alias.name == "*" for alias in node.names)
                or root not in allowed_imports
                or root in forbidden_import_roots
                or module not in exact_imports
                or any(alias.name not in exact_imports.get(module, []) for alias in node.names)
                or any(
                    module == prefix or module.startswith(prefix + ".")
                    for prefix in spec["forbidden_import_prefixes"]
                )
            ):
                issues.append(f"import:{node.lineno}:{module}")
    top_level_nodes = set(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node not in top_level_nodes:
            issues.append(f"nested import:{node.lineno}")
    callable_aliases: dict[str, str] = {}
    forbidden_origins = set(spec["forbidden_indirect_callable_origins"])
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(
            node.targets[0], ast.Name
        ):
            origin = _resolve_dotted_alias(_dotted_name(node.value), aliases)
            origin = callable_aliases.get(origin, origin)
            if origin in forbidden_origins or origin.rsplit(".", 1)[-1] in set(
                spec["forbidden_call_names"]
            ):
                callable_aliases[node.targets[0].id] = origin
    patterns = [re.compile(value) for value in spec["forbidden_string_literal_patterns"]]
    found_functions: dict[str, Union[ast.FunctionDef, ast.AsyncFunctionDef]] = {}  # noqa: UP007 -- Python 3.9 contract tool
    found_classes = {
        item.name: item for item in ast.walk(tree) if isinstance(item, ast.ClassDef)
    }
    local_dataclasses: set[str] = set()
    for class_name, class_node in found_classes.items():
        decorators = class_node.decorator_list
        if not decorators:
            continue
        for decorator in decorators:
            if not isinstance(decorator, ast.Call):
                issues.append(f"dataclass decorator:{class_node.lineno}:{class_name}")
                continue
            resolved = _resolve_dotted_alias(_dotted_name(decorator.func), aliases)
            if (
                resolved not in {"dataclass", "dataclasses.dataclass"}
                or decorator.args
                or len(decorator.keywords) != 1
                or decorator.keywords[0].arg != "frozen"
                or not isinstance(decorator.keywords[0].value, ast.Constant)
                or decorator.keywords[0].value.value is not True
            ):
                issues.append(f"dataclass decorator:{class_node.lineno}:{class_name}")
            else:
                local_dataclasses.add(class_name)

    owned = set(
        spec["symbol_binding_policy"]["owned_constructor_symbols_by_target"][relative]
    )
    imported_symbols = {
        symbol for symbols in exact_imports.values() for symbol in symbols
    }
    protected = (
        imported_symbols
        | {
            value.rsplit(".", 1)[-1]
            for value in spec["reachable_call_graph_policy"]["exact_stdlib_callables"]
        }
        | set(spec["exact_public_function_contracts"])
        | {"__builtins__"}
        | set(aliases)
    ) - owned
    allowed_definition_names = owned | set(spec["exact_public_function_contracts"])
    top_level_imports = {
        item for item in tree.body if isinstance(item, (ast.Import, ast.ImportFrom))
    }
    for item in ast.walk(tree):
        if isinstance(item, ast.Name) and item.id == "__builtins__":
            issues.append(f"builtins escape:{item.lineno}")
        if isinstance(item, (ast.Assign, ast.AnnAssign, ast.NamedExpr, ast.AugAssign)):
            targets: list[ast.AST] = []
            if isinstance(item, ast.Assign):
                targets = list(item.targets)
            else:
                targets = [item.target]
            for target in targets:
                names = {
                    child.id for child in ast.walk(target) if isinstance(child, ast.Name)
                }
                hit = names & protected
                if hit:
                    issues.append(f"protected binding:{item.lineno}:{','.join(sorted(hit))}")
            assigned_value = getattr(item, "value", None)
            if assigned_value is not None and not isinstance(assigned_value, ast.Call):
                loaded_protected = {
                    child.id
                    for child in ast.walk(assigned_value)
                    if isinstance(child, ast.Name)
                    and isinstance(child.ctx, ast.Load)
                    and child.id in protected
                }
                if loaded_protected:
                    issues.append(
                        f"protected callable alias:{item.lineno}:"
                        f"{','.join(sorted(loaded_protected))}"
                    )
        if (
            isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and item.name in protected
            and item.name not in allowed_definition_names
        ):
            issues.append(f"protected definition:{item.lineno}:{item.name}")
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = [
                *item.args.posonlyargs,
                *item.args.args,
                *item.args.kwonlyargs,
            ]
            if item.args.vararg is not None:
                arguments.append(item.args.vararg)
            if item.args.kwarg is not None:
                arguments.append(item.args.kwarg)
            for argument in arguments:
                if argument.arg in protected:
                    issues.append(f"protected parameter:{item.lineno}:{argument.arg}")
        if isinstance(item, (ast.Import, ast.ImportFrom)) and item in top_level_imports:
            for alias in item.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                original = alias.name.rsplit(".", 1)[-1]
                if bound in protected and bound != original:
                    issues.append(f"protected import alias:{item.lineno}:{bound}")

    for node in ast.walk(tree):
        if type(node).__name__ in set(spec["forbidden_ast_nodes"]):
            issues.append(f"forbidden AST:{node.lineno}:{type(node).__name__}")
        if isinstance(node, ast.Call):
            raw_name = _dotted_name(node.func)
            call_name = _resolve_dotted_alias(raw_name, aliases)
            call_name = callable_aliases.get(raw_name, callable_aliases.get(call_name, call_name))
            if (
                call_name in forbidden_origins
                or call_name.rsplit(".", 1)[-1] in set(spec["forbidden_call_names"])
                or call_name.rsplit(".", 1)[-1]
                in set(spec["forbidden_call_attributes"])
            ):
                issues.append(f"call:{node.lineno}:{call_name}")
        if isinstance(node, (ast.If, ast.IfExp)):
            branch_names = {
                item.id for item in ast.walk(node.test) if isinstance(item, ast.Name)
            }
            if branch_names & set(spec["forbidden_branch_identifier_names"]):
                issues.append(f"branch:{node.lineno}")
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and any(pattern.search(node.value) for pattern in patterns)
        ):
            issues.append(f"literal:{node.lineno}")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found_functions[node.name] = node
            if (
                node.args.vararg is not None
                or node.args.kwarg is not None
                or node.args.posonlyargs
                or node.args.kwonlyargs
            ):
                issues.append(f"variadic signature:{node.name}")
    local_functions = set(found_functions)
    allowed_stdlib = set(spec["reachable_call_graph_policy"]["exact_stdlib_callables"])
    safe_methods = set(
        spec["reachable_call_graph_policy"]["exact_safe_bound_methods"]
    )
    allowed_constructor_symbols = {
        symbol
        for module, symbols in exact_imports.items()
        if module.startswith("mm_")
        for symbol in symbols
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        raw = _dotted_name(node.func)
        terminal = raw.rsplit(".", 1)[-1]
        resolved = _resolve_dotted_alias(raw, aliases)
        method_allowed = False
        if isinstance(node.func, ast.Attribute) and node.func.attr in safe_methods:
            if node.func.attr == "hexdigest":
                method_allowed = (
                    isinstance(node.func.value, ast.Call)
                    and _resolve_dotted_alias(
                        _dotted_name(node.func.value.func), aliases
                    )
                    in {"sha256", "hashlib.sha256"}
                )
            elif node.func.attr == "encode":
                method_allowed = len(node.args) <= 1 and not node.keywords
            else:
                method_allowed = True
        allowed_call = (
            raw in local_functions
            or terminal in local_dataclasses
            or terminal in owned
            or terminal in allowed_constructor_symbols
            or raw in allowed_stdlib
            or terminal in allowed_stdlib
            or resolved in allowed_stdlib
            or raw == "date.fromisoformat"
            or method_allowed
        )
        if not allowed_call and not any(
            issue.startswith(f"call:{node.lineno}:") for issue in issues
        ):
            issues.append(f"unresolved call:{node.lineno}:{raw}")
    for function_name, contract in spec["exact_public_function_contracts"].items():
        if not _function_target(relative, function_name):
            continue
        node = found_functions.get(function_name)
        if node is None:
            issues.append(f"missing function:{function_name}")
            continue
        if (
            node.args.vararg is not None
            or node.args.kwarg is not None
            or node.args.posonlyargs
            or node.args.kwonlyargs
        ):
            issues.append(f"variadic signature:{function_name}")
        observed_parameters = [
            [argument.arg, _normalized_annotation(argument.annotation, aliases)]
            for argument in node.args.args
        ]
        if observed_parameters != contract["parameters"]:
            issues.append(f"parameters:{function_name}")
        if _normalized_annotation(node.returns, aliases) != contract["return"]:
            issues.append(f"return:{function_name}")
        default_names = [
            argument.arg for argument in node.args.args[-len(node.args.defaults) :]
        ] if node.args.defaults else []
        observed_defaults = {
            name: _normalized_annotation(value, aliases)
            for name, value in zip(default_names, node.args.defaults)
        }
        if observed_defaults != contract["defaults"]:
            issues.append(f"defaults:{function_name}")
        annotation_nodes = [
            argument.annotation
            for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
            if argument.annotation is not None
        ]
        if node.args.vararg is not None and node.args.vararg.annotation is not None:
            annotation_nodes.append(node.args.vararg.annotation)
        if node.args.kwarg is not None and node.args.kwarg.annotation is not None:
            annotation_nodes.append(node.args.kwarg.annotation)
        if node.returns is not None:
            annotation_nodes.append(node.returns)
        annotations = [
            _resolve_dotted_alias(_dotted_name(item), aliases)
            for annotation in annotation_nodes
            for item in ast.walk(annotation)
            if isinstance(item, (ast.Name, ast.Attribute))
        ]
        if any(
            value in {"Any", "Mapping", "dict", "typing.Any", "typing.Mapping", "collections.abc.Mapping"}
            or value.rsplit(".", 1)[-1] in {"Any", "Mapping", "dict"}
            for value in annotations
        ):
            issues.append(f"annotation origin:{function_name}")
        if function_name.startswith("validate_"):
            required = spec["validator_taint_policy"]["required_loads"][function_name]
            issues.extend(
                _validator_result_issues(node, function_name, aliases, required)
            )
        else:
            expected_constructor = contract["return"]
            assignments: dict[str, list[ast.AST]] = {}
            for item in ast.walk(node):
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            assignments.setdefault(target.id, []).append(item.value)
                elif (
                    isinstance(item, ast.AnnAssign)
                    and isinstance(item.target, ast.Name)
                    and item.value is not None
                ):
                    assignments.setdefault(item.target.id, []).append(item.value)

            def builder_constructor(
                value: Optional[ast.AST],  # noqa: UP045 -- Python 3.9 contract tool
                bound_assignments: Mapping[str, list[ast.AST]] = assignments,
                bound_constructor: str = expected_constructor,
            ) -> bool:
                if isinstance(value, ast.Name):
                    candidates = bound_assignments.get(value.id, [])
                    return len(candidates) == 1 and builder_constructor(
                        candidates[0], bound_assignments, bound_constructor
                    )
                if not isinstance(value, ast.Call):
                    return False
                resolved = _resolve_dotted_alias(_dotted_name(value.func), aliases)
                return resolved.rsplit(".", 1)[-1] == bound_constructor

            returns = [
                item for item in ast.walk(node) if isinstance(item, ast.Return)
            ]
            if not returns or any(
                not builder_constructor(item.value) for item in returns
            ):
                issues.append(f"builder exact return constructor:{function_name}")
    return sorted(set(issues))


def scan_future_runtime(spec: Mapping[str, Any]) -> None:
    issues = _static_gate_validation_issues(spec)
    if issues:
        fail(f"future static gate spec invalid: {issues}")
    for relative in spec["exact_source_targets"]:
        path = ROOT / relative
        if not path.is_file():
            fail(f"future runtime scan target missing: {relative}")
        source_issues = _future_runtime_source_issues(
            path.read_text(encoding="utf-8"), relative, spec
        )
        if source_issues:
            fail(f"future runtime source invalid: {relative}:{source_issues[:8]}")
    missing_tests = sorted(
        relative
        for relative in PRODUCER_ALLOWLIST
        if relative.endswith(".py") and not (ROOT / relative).is_file()
    )
    if missing_tests:
        fail(f"future runtime test target missing: {missing_tests[0]}")
    commands = spec["producer_acceptance_commands"]
    for command_name in (
        "pytest_normal",
        "pytest_o2",
        "sensitivity_pytest_normal",
        "sensitivity_pytest_o2",
        "isolation_probe",
    ):
        tokens = shlex.split(commands[command_name])
        environment = os.environ.copy()
        while tokens and "=" in tokens[0] and not tokens[0].startswith("/"):
            key, value = tokens.pop(0).split("=", 1)
            environment[key] = value
        completed = subprocess.run(
            tokens,
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            fail(
                f"future runtime {command_name} failed: "
                f"{completed.stdout[-1000:]}{completed.stderr[-1000:]}"
            )


def verify_unlock_and_static_contract(manifest: Mapping[str, Any]) -> None:
    expected_checks = {
        "ruff_exact_command": RUFF_ACCEPTANCE_COMMAND,
        "generator_normal": "PYTHONDONTWRITEBYTECODE=1 python3 -B tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py --check",
        "verifier_normal": "PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py",
        "generator_o2": "PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B tools/generate_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py --check",
        "verifier_o2": "PYTHONOPTIMIZE=2 PYTHONDONTWRITEBYTECODE=1 python3 -B tools/verify_medical_monitoring_r5_s5_public_authority_implementation_contract_v0_1.py",
    }
    if manifest["acceptance_checks"] != expected_checks:
        fail("acceptance command set mismatch")
    if manifest["contract_tool_executable_policy"] != (
        "non_executable_no_shebang_invoked_via_python3_B"
    ):
        fail("contract tool executable policy mismatch")
    expected_unlock = {
        "required_exact_token": "ACCEPT_R5_S5_PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT",
        "unlocks_only": "exact producer_create_only_allowlist",
        "does_not_accept": [
            "subject-temporal-public-v1 producer",
            "aemh-match-history-public-v1 producer",
            "R5-S5 contract or runtime",
            "UI/browser/real project/model/product/production",
        ],
        "s5_remains_locked": True,
    }
    if manifest["unlock"] != expected_unlock:
        fail("implementation-contract unlock/non-transfer rule mismatch")
    common = manifest["shared_common_sha_invalidation"]
    if common != {
        "path": "poc/medical_monitoring_ai_native_r5/src/mm_r5/public_authority_common.py",
        "both_producer_acceptance_records_must_pin_identical_sha256": True,
        "any_byte_drift_invalidates": [
            "ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1",
            "ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1",
        ],
        "required_revalidation": [
            "normal",
            "PYTHONOPTIMIZE=2",
            RUFF_ACCEPTANCE_COMMAND,
            "231 distinct future executable specs covering 236 accepted case IDs plus real producer tests",
            "source/SHA/boundary gates",
            "fresh independent review",
        ],
    }:
        fail("shared common SHA invalidation rule mismatch")
    static_issues = _static_gate_validation_issues(
        manifest["future_runtime_static_gate_spec"]
    )
    if static_issues:
        fail(f"future runtime static gate spec mismatch: {static_issues}")


def verify_in_memory_governance_mutations(
    api: Mapping[str, Any],
    joins: Mapping[str, Any],
    tests: Mapping[str, Any],
    manifest: Mapping[str, Any],
    error_codes: set[str],
    trigger_by_code: Mapping[str, str],
) -> None:
    registry = read_json(PUBLIC_ARTIFACT_DIR / "challenge_registry.json")

    polarity = copy.deepcopy(tests)
    polarity_row = next(
        row for row in polarity["future_runtime_specs"] if row["case_id"] == "R5C-109"
    )
    polarity_row["expected_disposition"] = "reject"
    if not _test_matrix_validation_issues(
        polarity, registry, error_codes, api, trigger_by_code
    ):
        fail("mutation gate failed to detect inherited accept polarity drift")

    reseal = copy.deepcopy(tests)
    reseal_row = next(
        row for row in reseal["future_runtime_specs"] if row["case_id"] == "PA-034"
    )
    reseal_row["fully_reseal_after_mutation"] = False
    reseal_row["canonical_reseal_recipe"] = {
        "mode": "not_applied_stale_hash_control",
        "steps": [],
        "hashes_recomputed": [],
        "preserve_evaluation_identities": False,
    }
    if not _test_matrix_validation_issues(
        reseal, registry, error_codes, api, trigger_by_code
    ):
        fail("mutation gate failed to detect fully-resealed flag/recipe drift")

    duplicate = copy.deepcopy(tests)
    duplicate_rows = _case_lookup(duplicate["future_runtime_specs"])
    for field in (
        "single_mutation",
        "typed_fixture",
        "canonical_reseal_recipe",
        "expected_typed_outcome_or_error",
        "semantic_independence_key",
    ):
        duplicate_rows["PA-034"][field] = copy.deepcopy(
            duplicate_rows["PA-034"][field]
        )
    if not _test_matrix_validation_issues(
        duplicate, registry, error_codes, api, trigger_by_code
    ):
        fail("mutation gate failed to detect semantic duplicate")

    bogus_join = copy.deepcopy(joins)
    for row in bogus_join["rows"]:
        row["source_field_paths"] = [
            "source:mm_r1.domain:SourceRevision.bogus_field"
        ]
    if not _source_join_validation_issues(bogus_join, api):
        fail("mutation gate failed to detect bogus source paths")

    static = copy.deepcopy(manifest["future_runtime_static_gate_spec"])
    static["forbidden_call_names"] = []
    if not _static_gate_validation_issues(static):
        fail("mutation gate failed to detect static scanner drift")

    coverage = copy.deepcopy(tests)
    first_code = min(error_codes)
    coverage["error_code_executable_coverage"][first_code] = []
    if not _test_matrix_validation_issues(
        coverage, registry, error_codes, api, trigger_by_code
    ):
        fail("mutation gate failed to detect error coverage drift")

    unreachable = copy.deepcopy(api)
    unreachable["source_type_access_paths"][SUBJECT_CONTRACT_ID][0][
        "bundle_access_path"
    ] = "common.bogus_revisions[]"
    if not _source_access_validation_issues(unreachable):
        fail("mutation gate failed to detect unreachable source-bundle path")

    semantic = copy.deepcopy(joins)
    semantic_row = next(
        row
        for row in semantic["rows"]
        if row["contract"] == SUBJECT_CONTRACT_ID
        and row["leaf"] == "TemporalRiskAnchor.risk_type_zh"
    )
    semantic_row["source_semantic_classes"] = ["severity"] * len(
        semantic_row["source_field_paths"]
    )
    if not _source_join_validation_issues(semantic, api):
        fail("mutation gate failed to detect source semantic-class drift")

    lifecycle = copy.deepcopy(api)
    lifecycle_specs = _input_class_specs(lifecycle)
    lifecycle_specs["AEMHDecisionAuthorityRecord"]["closed_values"][
        "event_kind"
    ].append("free_text_event")
    if not _controlled_record_validation_issues(lifecycle):
        fail("mutation gate failed to detect free AE/MH lifecycle vocabulary")

    fixture = copy.deepcopy(tests)
    fixture_row = fixture["future_runtime_specs"][0]
    fixture_row["typed_fixture_payload"]["mutation_slot"][
        "typed_source_or_candidate_path"
    ] = "source.bogus.unreachable"
    fixture_row["typed_mutation_adapter"][
        "typed_target_path"
    ] = "source.bogus.unreachable"
    if not _test_matrix_validation_issues(
        fixture, registry, error_codes, api, trigger_by_code
    ):
        fail("mutation gate failed to detect non-executable fixture adapter")

    static_spec = manifest["future_runtime_static_gate_spec"]
    common_target = static_spec["exact_source_targets"][0]
    subject_target = static_spec["exact_source_targets"][1]
    open_alias_issues = _future_runtime_source_issues(
        "reader = open\nreader('x')\n", common_target, static_spec
    )
    if not any(issue.startswith("call:") for issue in open_alias_issues):
        fail("mutation gate failed to detect aliased open call")
    dynamic_import_issues = _future_runtime_source_issues(
        "import importlib as loader\nload = loader.import_module\nload('x')\n",
        common_target,
        static_spec,
    )
    if not any(issue.startswith(("import:", "call:")) for issue in dynamic_import_issues):
        fail("mutation gate failed to detect dynamic import alias")
    pathlib_issues = _future_runtime_source_issues(
        "import pathlib as p\nread = p.Path.read_text\nread(p.Path('x'))\n",
        common_target,
        static_spec,
    )
    if not any(issue.startswith(("import:", "call:")) for issue in pathlib_issues):
        fail("mutation gate failed to detect pathlib read alias")
    variadic_source = """
def build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket:
    return candidate
def validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle, *args) -> PublicAuthorityValidationResult:
    return result
"""
    if not any(
        issue == "variadic signature:validate_subject_temporal_authority"
        for issue in _future_runtime_source_issues(
            variadic_source, subject_target, static_spec
        )
    ):
        fail("mutation gate failed to detect variadic validator")
    missing_source = """
def build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket:
    return candidate
def validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket) -> PublicAuthorityValidationResult:
    return result
"""
    if not any(
        issue == "parameters:validate_subject_temporal_authority"
        for issue in _future_runtime_source_issues(
            missing_source, subject_target, static_spec
        )
    ):
        fail("mutation gate failed to detect validator missing source bundle")
    python310_only = "match value:\n    case 1:\n        pass\n"
    if "python39 syntax" not in _future_runtime_source_issues(
        python310_only, common_target, static_spec
    ):
        fail("mutation gate failed to enforce Python 3.9 grammar")


def verify_redesign_negative_controls(
    api: Mapping[str, Any],
    joins: Mapping[str, Any],
    tests: Mapping[str, Any],
    manifest: Mapping[str, Any],
    error_codes: set[str],
) -> int:
    executed = 0

    def expect_reject(action: Any, label: str) -> None:
        nonlocal executed
        try:
            action()
        except (KeyError, RuntimeError, TypeError, ValueError):
            executed += 1
            return
        fail(f"negative control was accepted: {label}")

    def expect_reject_code(action: Any, label: str, code: str) -> None:
        nonlocal executed
        try:
            action()
        except (KeyError, RuntimeError, TypeError, ValueError) as exc:
            if code not in str(exc):
                fail(
                    f"negative control wrong code: {label}: expected={code} "
                    f"observed={exc}"
                )
            executed += 1
            return
        fail(f"negative control was accepted: {label}")

    polarity = copy.deepcopy(tests)
    next(
        row for row in polarity["future_runtime_specs"] if row["case_id"] == "R5C-109"
    )["expected_outcome"]["disposition"] = "reject"
    expect_reject(
        lambda: verify_constructible_test_matrix(error_codes, api, polarity),
        "inherited accept polarity",
    )

    reseal = copy.deepcopy(tests)
    next(row for row in reseal["future_runtime_specs"] if row["case_id"] == "PA-034")[
        "fully_reseal_after_mutation"
    ] = False
    expect_reject(
        lambda: verify_constructible_test_matrix(error_codes, api, reseal),
        "fully resealed lineage",
    )

    duplicate = copy.deepcopy(tests)
    by_id = {row["case_id"]: row for row in duplicate["future_runtime_specs"]}
    by_id["PA-034"]["semantic_independence_key"] = "0" * 64
    expect_reject(
        lambda: verify_constructible_test_matrix(error_codes, api, duplicate),
        "spec identity field drift",
    )

    input_identity = copy.deepcopy(tests)
    input_identity["future_runtime_specs"][1]["future_spec_input_identity"] = (
        input_identity["future_runtime_specs"][0]["future_spec_input_identity"]
    )
    expect_reject(
        lambda: verify_constructible_test_matrix(error_codes, api, input_identity),
        "input identity oracle independence",
    )

    simulated_builder = copy.deepcopy(tests)
    builder_row = next(
        row
        for row in simulated_builder["future_runtime_specs"]
        if row["execution_spec_kind"] == "source_to_builder_output"
    )
    builder_row["builder_expected_diff_spec"]["producer_executed"] = True
    builder_row["builder_expected_diff_spec"]["subject_builder_simulation"] = {
        "claimed_result_graph_hash": "0" * 64
    }
    expect_reject(
        lambda: verify_constructible_test_matrix(
            error_codes, api, simulated_builder
        ),
        "subject builder simulation cannot be contract evidence",
    )

    reject_as_builder = copy.deepcopy(tests)
    reject_row = next(
        row
        for row in reject_as_builder["future_runtime_specs"]
        if row["origin_projection"] == "accepted_parent_inherited"
        and row["expected_outcome"]["disposition"] == "reject"
    )
    reject_row["execution_spec_kind"] = "source_to_builder_output"
    reject_row["inherited_reject_spec"][
        "exact_changed_candidate_or_constructor_paths"
    ] = []
    expect_reject(
        lambda: verify_constructible_test_matrix(
            error_codes, api, reject_as_builder
        ),
        "reject mutation cannot be mislabeled as builder or have empty change",
    )

    bogus_join = copy.deepcopy(joins)
    bogus_join["rows"][0]["references"][0]["segments"][-1]["field"] = "bogus_field"
    expect_reject(
        lambda: verify_structured_source_join_matrix(api, bogus_join),
        "bogus structured source path",
    )

    bogus_selector = copy.deepcopy(joins)
    bogus_selector["rows"][0]["references"][0]["selector"]["op"] = "prose_pick"
    expect_reject(
        lambda: verify_structured_source_join_matrix(api, bogus_selector),
        "structured selector closed operation",
    )

    bogus_cardinality = copy.deepcopy(joins)
    bogus_cardinality["rows"][0]["references"][0]["selector"]["cardinality"] = (
        "zero_or_one"
    )
    expect_reject(
        lambda: verify_structured_source_join_matrix(api, bogus_cardinality),
        "structured selector cardinality",
    )

    multiple_as_exact = copy.deepcopy(joins)
    multiple_row = next(
        row
        for row in multiple_as_exact["rows"]
        if "one_or_more" in row["reference_cardinalities"]
    )
    multiple_index = multiple_row["reference_cardinalities"].index("one_or_more")
    multiple_row["reference_cardinalities"][multiple_index] = "exact_one"
    multiple_row["references"][multiple_index]["selector"]["cardinality"] = (
        "exact_one"
    )
    expect_reject(
        lambda: verify_structured_source_join_matrix(api, multiple_as_exact),
        "structured exact-one rejects multiple predicate matches",
    )

    empty_without_none = copy.deepcopy(joins)
    empty_row = next(
        row
        for row in empty_without_none["rows"]
        if "zero_or_one" in row["reference_cardinalities"]
    )
    empty_index = empty_row["reference_cardinalities"].index("zero_or_one")
    empty_row["references"][empty_index]["selector"]["none_semantics"] = {
        "kind": "forbidden"
    }
    expect_reject(
        lambda: verify_structured_source_join_matrix(api, empty_without_none),
        "structured empty branch requires row-specific none semantics",
    )

    bogus_key_id = copy.deepcopy(joins)
    bogus_row = bogus_key_id["rows"][0]
    bogus_clause = bogus_row["references"][0]["selector"]["predicate"][
        "clauses"
    ][0]
    bogus_row["join_keys"][0] = "bogus_join_key"
    bogus_clause["join_key"] = "bogus_join_key"
    bogus_clause["key_id"] = canonical_hash({
        "contract": bogus_row["contract"],
        "leaf": bogus_row["leaf"],
        "join_key": "bogus_join_key",
    })
    expect_reject(
        lambda: verify_structured_source_join_matrix(api, bogus_key_id),
        "structured selector join-key identity",
    )

    synchronized_api = copy.deepcopy(api)
    synchronized_join = copy.deepcopy(joins)
    synchronized_row = synchronized_join["rows"][0]
    catalog_key = (
        f"{synchronized_row['contract']}::{synchronized_row['leaf']}"
    )
    component = synchronized_api["join_key_authority_catalog"][catalog_key][
        "components"
    ][0]
    old_field = component["authority_reference"]["segments"][-1]["field"]
    old_join_key = component["join_key"]
    component["authority_reference"]["segments"][-1]["field"] = "bogus_field"
    component["context_reference"] = copy.deepcopy(
        component["authority_reference"]
    )
    component["join_key"] = (
        component["authority_reference"]["terminal"]["owner"] + ".bogus_field"
    )
    new_key = canonical_hash(
        {
            "contract": synchronized_row["contract"],
            "leaf": synchronized_row["leaf"],
            "reference_index": component["reference_index"],
            "join_key_index": component["join_key_index"],
            "join_key": component["join_key"],
            "authority_reference": component["authority_reference"],
            "context_reference": component["context_reference"],
            "value_terminal": component["value_terminal"],
        }
    )
    old_key = component["authority_key"]
    component["authority_key"] = new_key
    for clause in synchronized_row["references"][component["reference_index"]][
        "selector"
    ]["predicate"]["clauses"]:
        if clause["key_id"] == old_key:
            clause["key_id"] = new_key
            clause["rhs"]["authority_key"] = new_key
            clause["lhs"]["path"] = ["bogus_field"]
            clause["join_key"] = component["join_key"]
    synchronized_row["join_keys"] = [
        component["join_key"] if key == old_join_key else key
        for key in synchronized_row["join_keys"]
    ]
    owner_catalog = synchronized_api["collection_relation_key_catalog"][
        component["authority_reference"]["terminal"]["owner"]
    ]["real_identity_or_ref_fields"]
    synchronized_api["collection_relation_key_catalog"][
        component["authority_reference"]["terminal"]["owner"]
    ]["real_identity_or_ref_fields"] = sorted(
        "bogus_field" if field == old_field else field
        for field in owner_catalog
    )
    expect_reject(
        lambda: verify_structured_source_join_matrix(
            synchronized_api, synchronized_join
        ),
        "bogus real key remains invalid after globally synchronized resign",
    )

    all_terminal_copy_api = copy.deepcopy(api)
    all_terminal_copy_join = copy.deepcopy(joins)
    join_rows_by_key = {
        f"{row['contract']}::{row['leaf']}": row
        for row in all_terminal_copy_join["rows"]
    }
    for key, authority in all_terminal_copy_api[
        "join_key_authority_catalog"
    ].items():
        target_row = join_rows_by_key[key]
        for component in authority["components"]:
            if component["self_key_exception"]:
                continue
            reference_index = component["reference_index"]
            value_reference = copy.deepcopy(
                target_row["references"][reference_index]
            )
            value_reference.pop("selector", None)
            old_key = component["authority_key"]
            component["authority_reference"] = value_reference
            component["context_reference"] = copy.deepcopy(value_reference)
            component["join_key"] = (
                value_reference["terminal"]["owner"] + "."
                + value_reference["segments"][-1]["field"]
            )
            component["self_key_exception"] = False
            component["semantic_class"] = terminal_semantic = (
                "content_identity"
                if value_reference["segments"][-1]["field"].endswith("_hash")
                else "typed_identity"
            )
            new_key = canonical_hash({
                "contract": target_row["contract"],
                "leaf": target_row["leaf"],
                "reference_index": reference_index,
                "join_key_index": component["join_key_index"],
                "join_key": component["join_key"],
                "authority_reference": value_reference,
                "context_reference": value_reference,
                "value_terminal": component["value_terminal"],
            })
            component["authority_key"] = new_key
            clause = next(
                item
                for item in target_row["references"][reference_index][
                    "selector"
                ]["predicate"]["clauses"]
                if item["key_id"] == old_key
            )
            clause["join_key"] = component["join_key"]
            clause["key_id"] = new_key
            clause["semantic_class"] = terminal_semantic
            clause["lhs"] = {
                "scope": "candidate_item",
                "owner": value_reference["terminal"]["owner"],
                "path": [value_reference["segments"][-1]["field"]],
            }
            clause["rhs"] = {
                "scope": "current_join_context",
                "authority_key": new_key,
            }
        target_row["join_keys"] = list(dict.fromkeys(
            component["join_key"] for component in authority["components"]
        ))
    expect_reject(
        lambda: verify_structured_source_join_matrix(
            all_terminal_copy_api, all_terminal_copy_join
        ),
        "full terminal-copy/self-key selector graph",
    )

    historical_label_mismatch = copy.deepcopy(joins)
    historical_label_mismatch["closure"][
        "current_label_field_mismatch_count"
    ] = 1168
    expect_reject(
        lambda: verify_structured_source_join_matrix(
            api, historical_label_mismatch
        ),
        "1168 abstract-label/real-field selector mismatches",
    )

    cycle_join = copy.deepcopy(joins)
    first = cycle_join["rows"][0]
    first["references"] = [
        {
            "kind": "output",
            "root": "aemh_current",
            "segments": [
                {"field": "objects", "expand": "one"},
                {"field": "AEMHIdentityEvidence", "expand": "many"},
                {"field": "entity_content_identity", "expand": "one"},
            ],
            "terminal": {"owner": "AEMHIdentityEvidence", "type": "sha256"},
        }
    ]
    first["reference_semantic_classes"] = ["content_identity"]
    expect_reject(
        lambda: verify_structured_source_join_matrix(api, cycle_join),
        "current output self cycle",
    )

    future_key_api = copy.deepcopy(api)
    future_key_join = copy.deepcopy(joins)
    future_rows = {
        (row["contract"], row["leaf"]): row
        for row in future_key_join["rows"]
    }
    future_row = future_rows[(
        SUBJECT_CONTRACT_ID,
        "TemporalAxisBasis.axis_ref",
    )]
    authority_key = (
        f"{future_row['contract']}::{future_row['leaf']}"
    )
    future_component = future_key_api["join_key_authority_catalog"][
        authority_key
    ]["components"][0]
    later_reference = copy.deepcopy(next(
        row for row in future_key_join["rows"]
        if row["contract"] == SUBJECT_CONTRACT_ID
        and row["leaf"] == "TemporalAxisBasis.axis_content_hash"
    )["references"][0])
    later_reference.pop("selector", None)
    old_authority_key = future_component["authority_key"]
    old_join_key = future_component["join_key"]
    future_component["authority_reference"] = later_reference
    future_component["context_reference"] = copy.deepcopy(later_reference)
    future_component["join_key"] = (
        later_reference["terminal"]["owner"] + "."
        + later_reference["segments"][-1]["field"]
    )
    future_component["semantic_class"] = "content_identity"
    future_component["self_key_exception"] = False
    future_component["authority_key"] = canonical_hash({
        "contract": future_row["contract"],
        "leaf": future_row["leaf"],
        "reference_index": future_component["reference_index"],
        "join_key_index": future_component["join_key_index"],
        "join_key": future_component["join_key"],
        "authority_reference": later_reference,
        "context_reference": later_reference,
        "value_terminal": future_component["value_terminal"],
    })
    clause = next(
        item
        for item in future_row["references"][future_component["reference_index"]][
            "selector"
        ]["predicate"]["clauses"]
        if item["key_id"] == old_authority_key
    )
    clause.update({
        "join_key": future_component["join_key"],
        "key_id": future_component["authority_key"],
        "semantic_class": "content_identity",
        "lhs": {
            "scope": "candidate_item",
            "owner": later_reference["terminal"]["owner"],
            "path": [later_reference["segments"][-1]["field"]],
        },
        "rhs": {
            "scope": "current_join_context",
            "authority_key": future_component["authority_key"],
        },
    })
    future_row["join_keys"] = [
        future_component["join_key"] if key == old_join_key else key
        for key in future_row["join_keys"]
    ]
    expect_reject(
        lambda: verify_structured_source_join_matrix(
            future_key_api, future_key_join
        ),
        "reviewer-v8 synchronized same/later output relation key",
    )

    copied_expected = copy.deepcopy(tests)
    expected_by_id = {
        row["case_id"]: row for row in copied_expected["future_runtime_specs"]
    }
    source_diff = expected_by_id["R5C-157"]["builder_expected_diff_spec"][
        "expected_output_diff"
    ]
    target_row = expected_by_id["R5C-158"]
    target_diff = target_row["builder_expected_diff_spec"][
        "expected_output_diff"
    ]
    target_diff["post_adapter_expected_output_subgraph"] = copy.deepcopy(
        source_diff["post_adapter_expected_output_subgraph"]
    )
    target_diff["post_adapter_expected_output_subgraph_hash"] = canonical_hash(
        target_diff["post_adapter_expected_output_subgraph"]
    )
    expect_reject(
        lambda: verify_constructible_test_matrix(
            error_codes, api, copied_expected
        ),
        "reviewer-v8 class-level copied positive expected subgraph",
    )

    alias_drift = copy.deepcopy(tests)
    alias_drift["case_id_aliases"][0]["covered_case_ids"] = [
        "PA-007", "R5C-108"
    ]
    expect_reject(
        lambda: verify_constructible_test_matrix(error_codes, api, alias_drift),
        "reviewer-v8 exact five alias groups",
    )

    for owner_type in (
        "mm_r1.domain.SourceRevision",
        "mm_r4.d08_contracts.ScopeBinding",
        "mm_r5.s4_contracts.S4AcceptedAuthorityAnchor",
    ):
        project_drift = copy.deepcopy(tests["fixture_catalog"]["subject_base"])
        owner = next(
            node
            for node in project_drift["nodes"].values()
            if node["type"] == owner_type
        )
        field_name = "project_id" if "project_id" in owner["fields"] else "project_ref"
        owner["fields"][field_name] = "project::reviewer-v9-drift"
        expect_reject(
            lambda fixture=project_drift: _validate_fixture_graph(fixture, api),
            f"reviewer-v9 project drift {owner_type}",
        )

    def resign_expected_subgraph(
        candidate: dict[str, Any], case_id: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        target = next(
            row
            for row in candidate["future_runtime_specs"]
            if row["case_id"] == case_id
        )
        diff = target["builder_expected_diff_spec"]["expected_output_diff"]
        subgraph = diff["post_adapter_expected_output_subgraph"]
        subgraph["subgraph_content_hash"] = canonical_hash(
            {key: value for key, value in subgraph.items() if key != "subgraph_content_hash"}
        )
        diff["post_adapter_expected_output_subgraph_hash"] = canonical_hash(subgraph)
        return target, subgraph["nodes"][0]["exact_fields"]

    simplified_projection = copy.deepcopy(tests)
    _, simplified_packet = resign_expected_subgraph(
        simplified_projection, "R5C-157"
    )
    simplified_packet["projection"]["projection_id"] = canonical_hash(
        {
            "scope": simplified_packet["projection"]["scope_identity"][
                "identity_content_hash"
            ],
            "threads": [
                thread["thread_content_hash"]
                for thread in simplified_packet["projection"]["threads"]
            ],
        }
    )
    resign_expected_subgraph(simplified_projection, "R5C-157")
    expect_reject(
        lambda: verify_constructible_test_matrix(
            error_codes, api, simplified_projection
        ),
        "reviewer-v9 simplified projection id recipe",
    )

    simplified_thread = copy.deepcopy(tests)
    _, thread_packet = resign_expected_subgraph(simplified_thread, "R5C-158")
    changed_thread = next(
        thread
        for thread in thread_packet["projection"]["threads"]
        if len(thread["history_entries"]) > 1
    )
    changed_thread["thread_content_hash"] = canonical_hash(
        {
            "thread_ref": changed_thread["thread_ref"],
            "entry_hashes": [
                entry["entry_hash"] for entry in changed_thread["history_entries"]
            ],
        }
    )
    resign_expected_subgraph(simplified_thread, "R5C-158")
    expect_reject(
        lambda: verify_constructible_test_matrix(error_codes, api, simplified_thread),
        "reviewer-v9 simplified thread hash recipe",
    )

    empty_evidence = copy.deepcopy(tests)
    _, evidence_packet = resign_expected_subgraph(empty_evidence, "R5C-159")
    suffix = next(
        entry
        for thread in evidence_packet["projection"]["threads"]
        for entry in thread["history_entries"]
        if entry["seq"] > 1
    )
    suffix["identity_evidence"] = []
    suffix["identity_evidence_refs"] = []
    resign_expected_subgraph(empty_evidence, "R5C-159")
    expect_reject(
        lambda: verify_constructible_test_matrix(error_codes, api, empty_evidence),
        "reviewer-v9 empty suffix identity evidence",
    )

    hashed_ref_identity = copy.deepcopy(tests)
    _, identity_packet = resign_expected_subgraph(
        hashed_ref_identity, "R5C-157"
    )
    exact_suffix = next(
        entry
        for thread in identity_packet["projection"]["threads"]
        for entry in thread["history_entries"]
        if entry["event_kind"] == "match_decided"
    )
    exact_suffix["later_fact_content_identities"] = [
        canonical_hash(fact_ref) for fact_ref in exact_suffix["later_fact_refs"]
    ]
    resign_expected_subgraph(hashed_ref_identity, "R5C-157")
    expect_reject(
        lambda: verify_constructible_test_matrix(
            error_codes, api, hashed_ref_identity
        ),
        "reviewer-v9 sha256(ref) later fact identity",
    )

    dangling = copy.deepcopy(tests["fixture_catalog"]["subject_base"])
    dangling["nodes"][dangling["roots"]["source"]["node_ref"]]["fields"][
        "common"
    ] = {"node_ref": "N99999"}
    expect_reject(lambda: _validate_fixture_graph(dangling, api), "dangling fixture node")

    invalid_date = copy.deepcopy(tests["fixture_catalog"]["subject_base"])
    monitoring = next(
        node
        for node in invalid_date["nodes"].values()
        if node["type"] == "mm_r1.domain.MonitoringRun"
    )
    monitoring["fields"]["data_cutoff"] = "2026-99-99"
    expect_reject(lambda: _validate_fixture_graph(invalid_date, api), "illegal ISO date")

    invalid_time_ref = copy.deepcopy(
        tests["fixture_catalog"]["subject_base"]
    )
    next(
        node for node in invalid_time_ref["nodes"].values()
        if node["type"] == "mm_r4.d08_contracts.TimeRef"
    )["fields"]["value"] = "2026-99-99"
    expect_reject_code(
        lambda: _validate_fixture_graph(invalid_time_ref, api),
        "reviewer-v10 invalid TimeRef date",
        "PUB_DATE_INVALID",
    )

    placeholder_scope_cutoff = copy.deepcopy(
        tests["fixture_catalog"]["subject_base"]
    )
    next(
        node for node in placeholder_scope_cutoff["nodes"].values()
        if node["type"] == "mm_r4.d08_contracts.ScopeBinding"
    )["fields"]["clinical_event_cutoff"] = "AUTH-cutoff-placeholder"
    expect_reject_code(
        lambda: _validate_fixture_graph(placeholder_scope_cutoff, api),
        "reviewer-v10 ScopeBinding cutoff AUTH placeholder",
        "PUB_DATE_INVALID",
    )

    cross_source_cutoff = copy.deepcopy(
        tests["fixture_catalog"]["subject_base"]
    )
    next(
        node for node in cross_source_cutoff["nodes"].values()
        if node["type"] == "mm_r1.domain.MonitoringRun"
    )["fields"]["data_cutoff"] = "2026-08-18"
    expect_reject_code(
        lambda: _validate_fixture_graph(cross_source_cutoff, api),
        "reviewer-v10 cross-source cutoff mismatch",
        "PUB_IDENTITY_CUTOFF_MISMATCH",
    )

    reflected_api = copy.deepcopy(api)
    reflected_join = copy.deepcopy(joins)
    reflected_row = reflected_join["rows"][0]
    reflected_catalog = reflected_api["join_key_authority_catalog"][
        f"{reflected_row['contract']}::{reflected_row['leaf']}"
    ]
    reflected_component = reflected_catalog["components"][0]
    reflected_component["context_reference"] = copy.deepcopy(
        reflected_component["authority_reference"]
    )
    reflected_fixture = tests["fixture_catalog"][
        "subject_base"
        if reflected_row["contract"] == SUBJECT_CONTRACT_ID
        else "aemh_base"
    ]
    expect_reject_code(
        lambda: _execute_structured_selector(
            reflected_row["references"][0],
            reflected_row,
            reflected_fixture,
            reflected_api,
            reflected_join["reference_grammar"],
        ),
        "reviewer-v10 authority/context reflection",
        "PUB_REFERENCE_UNRESOLVED",
    )

    reducer_target_mismatch = copy.deepcopy(tests)
    reducer_fixture = reducer_target_mismatch["fixture_catalog"]["aemh_base"]
    next(
        node for node in reducer_fixture["nodes"].values()
        if node["type"] == "VisibilityClosure"
    )["fields"]["visibility_decision_hash"] = "0" * 64
    reducer_row = next(
        row for row in joins["rows"]
        if row["contract"] == AEMH_CONTRACT_ID
        and row["leaf"] == "VisibilityClosure.visibility_decision_hash"
    )
    expect_reject_code(
        lambda: verify_structured_source_join_matrix(
            api, joins, reducer_target_mismatch
        ),
        "reviewer-v10 selected reducer value differs from output leaf",
        reducer_row["unavailable_fail_closed_code"],
    )

    missing_linked_cutoff = copy.deepcopy(tests)
    missing_linked_row = next(
        row for row in missing_linked_cutoff["future_runtime_specs"]
        if row["case_id"] == "R5C-109"
    )
    removed_linked_operation = missing_linked_row["adapter"][
        "linked_operations"
    ].pop()
    removed_node_id = removed_linked_operation["selector"]["node_id"]
    removed_prefix = f"/nodes/{removed_node_id}/"
    missing_linked_row["adapter"]["allowed_diff_paths"] = [
        path for path in missing_linked_row["adapter"]["allowed_diff_paths"]
        if not path.startswith(removed_prefix)
    ]
    missing_linked_row["adapter"]["after_predicates"] = [
        predicate
        for predicate in missing_linked_row["adapter"]["after_predicates"]
        if not predicate["path"].startswith(removed_prefix)
    ]
    missing_linked_graph = missing_linked_cutoff["fixture_catalog"][
        missing_linked_row["fixture_key"]
    ]
    missing_linked_transformed = _interpret_adapter(
        missing_linked_row["adapter"], missing_linked_graph, api
    )
    expect_reject_code(
        lambda: _verify_v9_expected_subgraph(
            missing_linked_row,
            missing_linked_row["builder_expected_diff_spec"][
                "expected_output_diff"
            ],
            missing_linked_graph,
            missing_linked_transformed,
        ),
        "reviewer-v10 R5C-109 missing linked cutoff operation",
        "PUB_IDENTITY_CUTOFF_MISMATCH",
    )

    invalid_enum = copy.deepcopy(tests["fixture_catalog"]["subject_base"])
    monitoring = next(
        node
        for node in invalid_enum["nodes"].values()
        if node["type"] == "mm_r1.domain.MonitoringRun"
    )
    monitoring["fields"]["mode"]["enum"]["member"] = "FREE_TEXT"
    expect_reject(lambda: _validate_fixture_graph(invalid_enum, api), "illegal enum")

    selector = copy.deepcopy(tests["future_runtime_specs"][0]["adapter"])
    selector["selector"]["match"] = "many"
    expect_reject(
        lambda: _interpret_adapter(
            selector,
            tests["fixture_catalog"][selector["fixture_key"]],
            api,
        ),
        "non exact-one selector",
    )

    unknown_recipe = copy.deepcopy(tests["reseal_plans"]["reseal_subject_base"])
    unknown_recipe["operations"][0]["op"] = "rehash everything in prose"
    expect_reject(
        lambda: _validate_reseal_plan(
            unknown_recipe, tests["fixture_catalog"]["subject_base"], api
        ),
        "unknown or natural-language reseal operation",
    )

    nonexistent_filter = copy.deepcopy(
        tests["reseal_plans"]["reseal_aemh_base"]
    )
    next(
        operation
        for operation in nonexistent_filter["operations"]
        if operation["op"] == "append_history_suffix"
    )["source"]["filter"]["lhs"]["path"] = ["nonexistent_field"]
    expect_reject(
        lambda: _validate_reseal_plan(
            nonexistent_filter, tests["fixture_catalog"]["aemh_base"], api
        ),
        "AE/MH append nonexistent source filter field",
    )

    nonexistent_thread = copy.deepcopy(
        tests["reseal_plans"]["reseal_aemh_base"]
    )
    next(
        operation
        for operation in nonexistent_thread["operations"]
        if operation["op"] == "append_history_suffix"
    )["source"]["filter"]["rhs"]["path"] = ["nonexistent_thread"]
    expect_reject(
        lambda: _validate_reseal_plan(
            nonexistent_thread, tests["fixture_catalog"]["aemh_base"], api
        ),
        "AE/MH append nonexistent target thread field",
    )

    coverage = copy.deepcopy(tests)
    first_code = min(error_codes)
    coverage["coverage_lanes"]["by_error_code"][first_code] = []
    expect_reject(
        lambda: verify_constructible_test_matrix(error_codes, api, coverage),
        "id-only error coverage",
    )

    duplicate_decision = copy.deepcopy(tests)
    duplicate_row = next(
        row
        for row in duplicate_decision["future_runtime_specs"]
        if row["case_id"] == "R5C-157"
    )
    base_graph = duplicate_decision["fixture_catalog"]["aemh_base"]
    base_record = next(
        node["fields"]
        for node in base_graph["nodes"].values()
        if node["type"] == "AEMHDecisionAuthorityRecord"
        and node["fields"]["event_kind"] == "match_decided"
        and node["fields"]["match_state"] == "exact"
    )
    positive_fields = duplicate_row["adapter"]["replacement"]["tuple"][0][
        "fields"
    ]
    positive_fields["decision_ref"] = base_record["decision_ref"]
    positive_fields["authority_identity"] = base_record["authority_identity"]
    positive_fields["authority_content_hash"] = canonical_hash(
        {
            key: value
            for key, value in positive_fields.items()
            if key != "authority_content_hash"
        }
    )
    expect_reject(
        lambda: _validate_positive_adapter_semantics(
            duplicate_row["adapter"], base_graph
        ),
        "positive decision cannot reuse a base ref or authority identity",
    )

    hardcoded_ir = copy.deepcopy(tests)
    hardcoded_ir["future_dynamic_sensitivity_tests"][
        "runtime_proof_claimed"
    ] = True
    hardcoded_ir["future_dynamic_sensitivity_tests"]["hardcoded_integer_ir"] = {
        "candidate": 1,
        "source": 2,
    }
    expect_reject(
        lambda: verify_constructible_test_matrix(error_codes, api, hardcoded_ir),
        "hardcoded IR cannot be runtime proof",
    )

    subject_previous_parameter = copy.deepcopy(tests)
    subject_vector = next(
        vector
        for vector in subject_previous_parameter[
            "future_dynamic_sensitivity_tests"
        ]["vectors"]
        if vector["function"] == "validate_subject_temporal_authority"
    )
    subject_vector["held_fixed"].append("previous_packet")
    expect_reject(
        lambda: verify_constructible_test_matrix(
            error_codes, api, subject_previous_parameter
        ),
        "subject sensitivity vector cannot invent previous_packet",
    )

    owner_only_vector = copy.deepcopy(tests)
    typed_vector = next(
        vector
        for vector in owner_only_vector["future_dynamic_sensitivity_tests"][
            "vectors"
        ]
        if vector["mutation"]["kind"] == "typed_field_replace"
    )
    typed_vector["mutation"].pop("instance_selector")
    expect_reject(
        lambda: verify_constructible_test_matrix(
            error_codes, api, owner_only_vector
        ),
        "sensitivity vector owner-only selector",
    )

    missing_vector_coverage = copy.deepcopy(tests)
    missing_vector_coverage["future_dynamic_sensitivity_tests"][
        "exact_vector_ids"
    ].pop()
    expect_reject(
        lambda: verify_constructible_test_matrix(
            error_codes, api, missing_vector_coverage
        ),
        "sensitivity pytest exact vector-id coverage",
    )

    isolation_before_import = copy.deepcopy(
        manifest["future_runtime_static_gate_spec"]
    )
    isolation_before_import["future_isolation_gate"][
        "initial_import_under_hook"
    ] = True
    if not _static_gate_validation_issues(isolation_before_import):
        fail("negative control accepted audit hook before legal imports")
    executed += 1

    isolation_bootstrap_drift = copy.deepcopy(
        manifest["future_runtime_static_gate_spec"]
    )
    isolation_bootstrap_drift["future_isolation_gate"][
        "bootstrap_paths"
    ].append("/tmp/unfrozen")
    if not _static_gate_validation_issues(isolation_bootstrap_drift):
        fail("negative control accepted unfrozen -I sys.path bootstrap")
    executed += 1

    sensitivity_node_drift = copy.deepcopy(
        manifest["future_runtime_static_gate_spec"]
    )
    sensitivity_node_drift["producer_acceptance_commands"][
        "sensitivity_pytest_normal"
    ] = "python3 -B -m pytest -q tests::wrong_node"
    if not _static_gate_validation_issues(sensitivity_node_drift):
        fail("negative control accepted wrong sensitivity pytest node")
    executed += 1

    isolation_contract = manifest["future_runtime_static_gate_spec"][
        "future_isolation_gate"
    ]

    def audit_allows(event_family: str, hook: bool, api_window: bool) -> bool:
        return not (
            hook
            and api_window
            and event_family in isolation_contract["audit_hook_denies"]
        )

    if (
        not audit_allows("import", False, False)
        or not audit_allows("open", False, False)
        or not audit_allows("hashlib", True, True)
        or any(
            audit_allows(event_family, True, True)
            for event_family in isolation_contract["audit_hook_denies"]
        )
    ):
        fail("mechanical isolation positive/deny-family control drift")
    executed += 1
    if audit_allows("import", True, True):
        fail("mechanical isolation negative import control drift")
    executed += 1

    lifecycle = copy.deepcopy(api)
    _input_class_specs(lifecycle)["AEMHDecisionAuthorityRecord"]["closed_values"][
        "event_kind"
    ].append("free_text_event")
    if not _controlled_record_validation_issues(lifecycle):
        fail("negative control accepted free lifecycle vocabulary")
    executed += 1

    static = copy.deepcopy(manifest["future_runtime_static_gate_spec"])
    static["reachable_call_graph_policy"]["closed_call_targets"] = []
    if not _static_gate_validation_issues(static):
        fail("negative control accepted static gate drift")
    executed += 1

    expected_multi = [
        "PUB_OVERLAY_ARTIFACT_MISMATCH",
        "PUB_OVERLAY_DEFERRED_SET_MISMATCH",
    ]
    for label, observed in (
        ("governance missing issue", expected_multi[:1]),
        ("governance extra issue", [*expected_multi, "EXTRA"]),
        ("governance reordered issue", list(reversed(expected_multi))),
    ):
        if _exact_ordered_issue_oracle(expected_multi, observed):
            fail(f"negative control accepted {label}")
        executed += 1

    static_spec = manifest["future_runtime_static_gate_spec"]
    common_target, subject_target, _aemh_target = static_spec["exact_source_targets"]
    legal_source = """from dataclasses import dataclass
import dataclasses
import hashlib

@dataclass(frozen=True)
class LocalRecord:
    value: str

def helper(value: LocalRecord) -> str:
    copied = dataclasses.replace(value, value=value.value)
    return hashlib.sha256(copied.value.encode("utf-8")).hexdigest()
"""
    legal_issues = _future_runtime_source_issues(
        legal_source, common_target, static_spec
    )
    if legal_issues:
        fail(f"positive control rejected legal minimal producer: {legal_issues}")
    executed += 1

    legal_validator = """from mm_r5.public_authority_common import PublicAuthorityValidationIssue, PublicAuthorityValidationResult

def build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket:
    return SubjectTemporalAuthorityPacket(receipt=source.common.r5_authority_receipt, projection=source.common.r5_authority_receipt, packet_content_hash="pending")

def validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult:
    issues = []
    if candidate.packet_content_hash != source.common.r5_authority_receipt.receipt_content_hash:
        issues.append(PublicAuthorityValidationIssue(code="X", path="x", message="x"))
    primary_code = issues[0].code if issues else None
    return PublicAuthorityValidationResult(ok=not issues, issues=tuple(issues), primary_code=primary_code)
"""
    validator_issues = _future_runtime_source_issues(
        legal_validator, subject_target, static_spec
    )
    if validator_issues:
        fail(f"positive control rejected joint validator taint: {validator_issues}")
    executed += 1

    meaningless_compare_validator = """from mm_r5.public_authority_common import PublicAuthorityValidationResult

def build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket:
    return SubjectTemporalAuthorityPacket(receipt=source.common.r5_authority_receipt, projection=source.common.r5_authority_receipt, packet_content_hash="pending")

def validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult:
    candidate == source
    return PublicAuthorityValidationResult(ok=True, issues=(), primary_code=None)
"""
    meaningless_issues = _future_runtime_source_issues(
        meaningless_compare_validator, subject_target, static_spec
    )
    if not any(
        "validator incompatible parameter comparison" in issue
        or "validator joint taint" in issue
        for issue in meaningless_issues
    ):
        fail("negative control accepted meaningless comparison before constant result")
    executed += 1

    self_compare_validator = meaningless_compare_validator.replace(
        "candidate == source", "candidate == candidate"
    )
    self_compare_issues = _future_runtime_source_issues(
        self_compare_validator, subject_target, static_spec
    )
    if not any("validator self comparison" in issue for issue in self_compare_issues):
        fail("negative control accepted validator self-comparison")
    executed += 1

    identical_branch_validator = legal_validator.replace(
        "primary_code = issues[0].code if issues else None",
        'primary_code = "X" if candidate.packet_content_hash != source.common.r5_authority_receipt.receipt_content_hash else "X"',
    )
    identical_branch_issues = _future_runtime_source_issues(
        identical_branch_validator, subject_target, static_spec
    )
    if not any(
        "validator identical branch sinks" in issue
        for issue in identical_branch_issues
    ):
        fail("negative control accepted identical validator branch sinks")
    executed += 1

    candidate_return_validator = """def build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket:
    return SubjectTemporalAuthorityPacket(receipt=source.common.r5_authority_receipt, projection=source.common.r5_authority_receipt, packet_content_hash="pending")

def validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult:
    if candidate != source:
        return candidate
    return candidate
"""
    candidate_return_issues = _future_runtime_source_issues(
        candidate_return_validator, subject_target, static_spec
    )
    if not any(
        "validator exact result constructor" in issue
        for issue in candidate_return_issues
    ):
        fail("negative control accepted candidate as validator result")
    executed += 1

    builder_returns_source = """def build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket:
    return source
"""
    builder_return_issues = _future_runtime_source_issues(
        builder_returns_source, subject_target, static_spec
    )
    if not any(
        "builder exact return constructor" in issue
        for issue in builder_return_issues
    ):
        fail("negative control accepted builder returning source")
    executed += 1

    constant_validator = """from mm_r5.public_authority_common import PublicAuthorityValidationResult

def build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket:
    return SubjectTemporalAuthorityPacket(receipt=source.common.r5_authority_receipt, projection=source.common.r5_authority_receipt, packet_content_hash="pending")

def validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult:
    return PublicAuthorityValidationResult(ok=True, issues=(), primary_code=None)
"""
    constant_validator_issues = _future_runtime_source_issues(
        constant_validator, subject_target, static_spec
    )
    if not any(
        "validator joint taint" in issue
        for issue in constant_validator_issues
    ):
        fail("negative control accepted constant validator")
    executed += 1

    source_controls = {
        "aliased dynamic IO": "reader = open\nreader('x')\n",
        "nested import": "def helper():\n    import pathlib\n    return pathlib.Path('x').read_text()\n",
        "builtins constructor shadow": "SourceRevision = __builtins__['open']\n",
        "tuple constructor shadow": "SourceRevision, other = (1, 2)\n",
        "subscript constructor shadow": "SourceRevision[0] = 1\n",
        "external helper": "from helper_package import hidden_logic\ndef build_subject_temporal_authority(source: SubjectTemporalSourceBundle) -> SubjectTemporalAuthorityPacket:\n    return hidden_logic(source)\n",
        "variadic validator": "def validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle, *args) -> PublicAuthorityValidationResult:\n    return result\n",
        "constant success validator": "def validate_subject_temporal_authority(candidate: SubjectTemporalAuthorityPacket, source: SubjectTemporalSourceBundle) -> PublicAuthorityValidationResult:\n    return PublicAuthorityValidationResult(ok=True, issues=(), primary_code=None)\n",
    }
    for label, source in source_controls.items():
        target = common_target if label in {
            "aliased dynamic IO",
            "builtins constructor shadow",
            "nested import",
            "subscript constructor shadow",
            "tuple constructor shadow",
        } else subject_target
        if not _future_runtime_source_issues(source, target, static_spec):
            fail(f"negative control accepted {label}")
        executed += 1
    if "python39 syntax" not in _future_runtime_source_issues(
        "match value:\n    case 1:\n        pass\n", common_target, static_spec
    ):
        fail("negative control accepted Python 3.10 grammar")
    executed += 1
    return executed


def verify_locked_surfaces_absent(manifest: Mapping[str, Any]) -> None:
    targets = PRODUCER_ALLOWLIST | S5_RUNTIME_LOCKED_PATHS
    hits = [
        relative
        for relative in sorted(targets)
        if (ROOT / relative).exists() or (ROOT / relative).is_symlink()
    ]
    source_root = ROOT / "poc/medical_monitoring_ai_native_r5/src/mm_r5"
    test_root = ROOT / "poc/medical_monitoring_ai_native_r5/tests"
    forbidden_stems = {
        Path(relative).stem
        for relative in targets
        if relative.endswith((".py", ".pyc", ".pyo"))
    }
    for root in (source_root, test_root):
        if not root.is_dir():
            fail(f"locked-surface scan root missing: {root.relative_to(ROOT)}")
        for candidate in root.rglob("*"):
            if not (candidate.is_file() or candidate.is_symlink()):
                continue
            name = candidate.name
            if name.endswith((".pyc", ".pyo")) and any(
                name.startswith(stem + ".") or name == stem + name[-4:]
                for stem in forbidden_stems
            ):
                hits.append(candidate.relative_to(ROOT).as_posix())
    if hits:
        fail(f"producer/S5 runtime/test/evidence/bytecode surface exists: {sorted(set(hits))}")
    if manifest["producer_surface_must_be_absent_before_contract_acceptance"] is not True:
        fail("producer absence gate disabled")
    if manifest["producer_bytecode_and_cache_must_be_absent"] is not True:
        fail("producer bytecode gate disabled")


def verify_port_8911_stopped() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        result = sock.connect_ex(("127.0.0.1", 8911))
    if result == 0:
        fail("port 8911 has a listener")


def main(argv: Any = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-future-runtime", action="store_true")
    args = parser.parse_args(argv)
    verify_no_assert_statements()
    verify_parent_contract()
    generator = load_module(GENERATOR_PATH, "public_authority_implementation_generator")
    verify_generator_reproducibility(generator)
    manifest = verify_manifest()
    verify_pins(manifest)
    api = verify_public_api()
    joins = verify_structured_source_join_matrix(api)
    error_codes = verify_invariant_error_matrix()
    tests = verify_constructible_test_matrix(error_codes, api)
    governance_probe_count = verify_all_governance_probes(tests)
    verify_unlock_and_static_contract(manifest)
    negative_control_count = verify_redesign_negative_controls(
        api, joins, tests, manifest, error_codes
    )
    if negative_control_count != 72:
        fail("in-memory negative control count drift")
    if args.scan_future_runtime:
        scan_future_runtime(manifest["future_runtime_static_gate_spec"])
    else:
        verify_locked_surfaces_absent(manifest)
    verify_port_8911_stopped()
    print(
        "PUBLIC_AUTHORITY_IMPLEMENTATION_CONTRACT_VERIFIER_OK "
        "objects=17/13 errors=81 future_executable_specs=231 accepted_case_traces=236 governance_cases=22 "
        f"governance_probes_executed={governance_probe_count} "
        "accepted_parent_snapshot=10 medical_writing=542 "
        f"mutations={negative_control_count} "
        f"future_scan={args.scan_future_runtime} port_8911=stopped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
