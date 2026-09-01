#!/usr/bin/env python3
"""Verify the frozen R5-S5 public-authority contract artifact set.

The checks are deterministic and contract-only.  They do not import, execute,
or create a public-authority producer or any S5 runtime/test module.
"""

from __future__ import annotations

import ast
import calendar
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import re
import socket
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py"
VERIFIER_PATH = Path(__file__).resolve()
ARTIFACT_DIR = ROOT / "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1"
ALLOWLIST = {
    "reviews/medical_monitoring_r5_s5_public_authority_contract_v0_1_20260819.md",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/exact_overlay.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/source_matrix.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/challenge_registry.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/base_inputs.json",
    "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json",
    "tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py",
    "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py",
}
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PARTIAL_DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
EXPECTED_SOURCE_MATRIX_CANONICAL_SHA256 = (
    "e190e015dcf510d08a0af4fad2057d8f69e5a4972707245987a3ba716f546091"
)
PARENT_R5_AUDIENCE_CONTRACT_ID = "contract.s4.1"
EXPECTED_NO_RUNTIME_TEST_SURFACE = {
    "scan_roots": [
        "poc/medical_monitoring_ai_native_r5/src/mm_r5",
        "poc/medical_monitoring_ai_native_r5/tests",
    ],
    "forbidden_exact_paths": [
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/aemh_match_history_public.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_authority_builder.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_contracts.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s5_projection.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/subject_temporal_public.py",
        "poc/medical_monitoring_ai_native_r5/tests/s5_runtime_fixtures.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_aemh_match_history_public.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_s5_contracts.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_s5_projection.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_subject_temporal_public.py",
    ],
    "forbidden_relative_path_regexes": [
        "^poc/medical_monitoring_ai_native_r5/src/mm_r5/(?:subject_temporal_public|aemh_match_history_public|s5_[^/]+)(?:\\.py|\\.pyc|\\.pyo|/.*|$)$",
        "^poc/medical_monitoring_ai_native_r5/tests/(?:.*/)?(?:test_)?(?:subject_temporal_public|aemh_match_history_public|s5_[^/]+)(?:\\.py|\\.pyc|\\.pyo|/.*|$)$",
    ],
    "file_surface_rule": "fail closed if any regular file or symlink matches an exact path or regex; scan names only and do not read file content",
}

SELF_HASH_FIELD = {
    "PublicScopeIdentity": "identity_content_hash",
    "PublicSourceLocator": "locator_content_hash",
    "SourceRevisionContentPair": "pair_content_hash",
    "VisibilityClosure": "closure_content_hash",
    "PublicCutoffEndpoint": "cutoff_content_hash",
    "PublicAuthorityReceipt": "receipt_content_hash",
    "AEMHIdentityEvidence": "evidence_content_hash",
    "TemporalDateEndpoint": "endpoint_content_hash",
    "TemporalAxisBasis": "axis_content_hash",
    "TemporalVisit": "visit_content_hash",
    "TemporalEvent": "event_content_hash",
    "TemporalRiskAnchor": "risk_anchor_content_hash",
    "TemporalPendingDateItem": "pending_content_hash",
    "TemporalPhaseBand": "phase_content_hash",
    "TemporalDomainTrack": "track_content_hash",
    "TemporalMembershipIndex": "membership_content_hash",
    "SubjectTemporalPublicProjection": "projection_content_hash",
    "AEMHMatchHistoryEntry": "entry_hash",
    "AEMHThreadPrefixAnchor": "prefix_content_hash",
    "AEMHMatchThread": "thread_content_hash",
    "AEMHHistoryMembershipIndex": "membership_content_hash",
    "AEMHMatchHistoryPublicProjection": "projection_content_hash",
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


def read_json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("r5_s5_public_contract_generator", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        fail("cannot load generator module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_generator_reproducibility(generator: ModuleType) -> None:
    bundle = generator.build_bundle()
    expected_paths = {str(path.relative_to(ROOT)) for path in bundle}
    generated_paths = ALLOWLIST - {
        "tools/generate_medical_monitoring_r5_s5_public_authority_contract_v0_1.py",
        "tools/verify_medical_monitoring_r5_s5_public_authority_contract_v0_1.py",
    }
    if expected_paths != generated_paths:
        fail(f"generator artifact set mismatch: expected={sorted(expected_paths)}")
    for path, expected in bundle.items():
        if not path.is_file():
            fail(f"generated artifact missing: {path.relative_to(ROOT)}")
        if path.read_bytes() != expected:
            fail(f"generated artifact drift: {path.relative_to(ROOT)}")


def verify_no_python_assert_statements() -> None:
    for path in (GENERATOR_PATH, VERIFIER_PATH):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        hits = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        if hits:
            fail(f"Python assertion statement forbidden: {path.name}:{hits}")


def verify_manifest() -> dict[str, Any]:
    manifest = read_json(
        "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json"
    )
    manifest_keys = {
        "schema",
        "contract_id",
        "schema_version",
        "exact_artifact_paths",
        "artifact_raw_sha256",
        "manifest_hash_recipe",
        "source_file_sha256",
        "protected_accepted_pins",
        "no_runtime_test_surface",
        "parent_challenge_projection",
        "public_authority_specific_case_count",
        "runtime_unlock",
        "python_assert_statements_allowed",
        "manifest_content_hash",
    }
    if set(manifest) != manifest_keys:
        fail("manifest exact keys mismatch")
    if set(manifest["exact_artifact_paths"]) != ALLOWLIST:
        fail("manifest exact artifact allowlist mismatch")
    if manifest["python_assert_statements_allowed"] is not False:
        fail("manifest must forbid Python assertion statements")
    manifest_core = {k: v for k, v in manifest.items() if k != "manifest_content_hash"}
    if canonical_hash(manifest_core) != manifest["manifest_content_hash"]:
        fail("manifest content hash mismatch")
    for relative, expected in manifest["artifact_raw_sha256"].items():
        path = ROOT / relative
        if not path.is_file():
            fail(f"manifest-pinned artifact missing: {relative}")
        if sha256_bytes(path.read_bytes()) != expected:
            fail(f"manifest-pinned artifact drift: {relative}")
    manifest_path = "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json"
    if manifest_path in manifest["artifact_raw_sha256"]:
        fail("manifest must use manifest_content_hash rather than circular raw self-pin")
    actual_artifacts = {
        str(path.relative_to(ROOT))
        for path in ARTIFACT_DIR.iterdir()
        if path.is_file()
    }
    expected_artifacts = {p for p in ALLOWLIST if p.startswith("artifacts/")}
    if actual_artifacts != expected_artifacts:
        fail(
            f"artifact directory contains unexpected/missing files: "
            f"actual={sorted(actual_artifacts)} expected={sorted(expected_artifacts)}"
        )
    expected_unlock = {
        "unlocks_only": "later_public_authority_implementation_contract",
        "does_not_satisfy": [
            "ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1",
            "ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1",
            "ACCEPT_R5_S5_CONTRACT",
        ],
        "s5_runtime_locked": True,
    }
    if manifest["runtime_unlock"] != expected_unlock:
        fail("manifest acceptance non-transfer boundary mismatch")
    if manifest["no_runtime_test_surface"] != EXPECTED_NO_RUNTIME_TEST_SURFACE:
        fail("manifest no-runtime/no-test surface contract mismatch")
    return manifest


def manifest_contract_validation_issues(manifest: dict[str, Any]) -> list[str]:
    expected_unlock = {
        "unlocks_only": "later_public_authority_implementation_contract",
        "does_not_satisfy": [
            "ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1",
            "ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1",
            "ACCEPT_R5_S5_CONTRACT",
        ],
        "s5_runtime_locked": True,
    }
    issues: list[str] = []
    if (
        manifest.get("schema")
        != "medical-monitoring-r5-s5-public-authority-manifest-v0.1"
        or manifest.get("contract_id")
        != "medical-monitoring-r5-s5-public-authority-contract-v0.1"
        or manifest.get("runtime_unlock") != expected_unlock
        or manifest.get("no_runtime_test_surface")
        != EXPECTED_NO_RUNTIME_TEST_SURFACE
    ):
        issues.append("PUB_MANIFEST_CONTRACT_MISMATCH")
    issues.extend(protected_pin_validation_issues(manifest))
    return sorted(set(issues))


def verify_source_pins(manifest: dict[str, Any]) -> None:
    for relative, expected in manifest["source_file_sha256"].items():
        path = ROOT / relative
        if not path.is_file():
            fail(f"pinned source missing: {relative}")
        actual = sha256_bytes(path.read_bytes())
        if actual != expected:
            fail(f"pinned source drift: {relative}: {actual}")
    protected_issues = protected_pin_validation_issues(manifest)
    if protected_issues:
        fail(f"protected accepted pin mismatch: {protected_issues}")
    audience_source = (
        ROOT
        / "poc/medical_monitoring_ai_native_r5/src/mm_r5/s4_contracts.py"
    )
    audience_tree = ast.parse(
        audience_source.read_text(encoding="utf-8"),
        filename=str(audience_source),
    )
    audience_values = [
        node.value.value
        for node in ast.walk(audience_tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "AUDIENCE_CONTRACT_ID"
            for target in node.targets
        )
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if audience_values != [PARENT_R5_AUDIENCE_CONTRACT_ID]:
        fail(
            "PUB_AUDIENCE_CONTRACT_MISMATCH: pinned parent R5 audience "
            f"constant drifted: {audience_values}"
        )


def protected_pin_validation_issues(manifest: dict[str, Any]) -> list[str]:
    pins = manifest.get("protected_accepted_pins", {})
    expected_keys = {
        "r5_root_init_sha256",
        "accepted_r4_r5_s4_readonly_manifest_sha256",
        "accepted_r5_v0_3_exact_contract_sha256",
        "s4_acceptance_record_sha256",
        "medical_writing_protected_inventory_sha256",
        "medical_writing_protected_file_count",
        "protected_path_sha256",
        "medical_writing_inventory_contract",
    }
    if set(pins) != expected_keys:
        return ["PUB_MANIFEST_PROTECTED_PIN_MISMATCH"]
    path_pins = pins["protected_path_sha256"]
    expected_path_keys = {
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py",
        "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s4_readonly_sha256.json",
        "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json",
        "context/medical_monitoring_r5_s4_acceptance_record_20260819.md",
    }
    if set(path_pins) != expected_path_keys:
        return ["PUB_MANIFEST_PROTECTED_PIN_MISMATCH"]
    if any(
        not (ROOT / relative).is_file()
        or sha256_bytes((ROOT / relative).read_bytes()) != expected
        for relative, expected in path_pins.items()
    ):
        return ["PUB_MANIFEST_PROTECTED_PIN_MISMATCH"]
    scalar_path_aliases = {
        "r5_root_init_sha256": (
            "poc/medical_monitoring_ai_native_r5/src/mm_r5/__init__.py"
        ),
        "accepted_r4_r5_s4_readonly_manifest_sha256": (
            "poc/medical_monitoring_ai_native_r5/evidence/"
            "r4_r5_s4_readonly_sha256.json"
        ),
        "accepted_r5_v0_3_exact_contract_sha256": (
            "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json"
        ),
        "s4_acceptance_record_sha256": (
            "context/medical_monitoring_r5_s4_acceptance_record_20260819.md"
        ),
    }
    if any(
        pins[scalar_name] != path_pins[relative]
        for scalar_name, relative in scalar_path_aliases.items()
    ):
        return ["PUB_MANIFEST_PROTECTED_PIN_MISMATCH"]
    inventory_contract = pins["medical_writing_inventory_contract"]
    expected_inventory_contract = {
        "roots": ["deploy", "frontend", "packages", "runtime", "services"],
        "relative_path_regex": "medical[-_]writing",
        "file_kind": "regular_file_following_task_scoped_symlink_resolution",
        "sort": "UTF-8 relative POSIX path byte order",
        "per_file_sha256": "lowercase sha256(file bytes)",
        "aggregate_recipe": (
            "sha256(concat(relative_path_utf8 + NUL + "
            "lowercase_file_sha256_ascii + LF))"
        ),
        "privacy_boundary": (
            "enumerate paths under the five protected roots; read bytes only "
            "for matched regular files"
        ),
    }
    if inventory_contract != expected_inventory_contract:
        return ["PUB_MANIFEST_PROTECTED_PIN_MISMATCH"]
    pattern = re.compile(inventory_contract["relative_path_regex"])
    matched_paths: list[tuple[str, Path]] = []
    for root_name in inventory_contract["roots"]:
        root_path = ROOT / root_name
        if not root_path.is_dir():
            return ["PUB_MANIFEST_PROTECTED_PIN_MISMATCH"]
        for candidate in root_path.rglob("*"):
            relative = candidate.relative_to(ROOT).as_posix()
            if pattern.search(relative) and candidate.is_file():
                matched_paths.append((relative, candidate))
    matched_paths.sort(key=lambda item: item[0].encode("utf-8"))
    aggregate = hashlib.sha256()
    for relative, path in matched_paths:
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(sha256_bytes(path.read_bytes()).encode("ascii"))
        aggregate.update(b"\n")
    if (
        len(matched_paths) != pins["medical_writing_protected_file_count"]
        or aggregate.hexdigest()
        != pins["medical_writing_protected_inventory_sha256"]
    ):
        return ["PUB_MANIFEST_PROTECTED_PIN_MISMATCH"]
    return []


def verify_schema_descriptor(schema: dict[str, Any], expected_name: str) -> None:
    exact_root = {
        "schema",
        "schema_version",
        "exact_object_keys",
        "enums",
        "objects",
        "hash_recipes",
        "invariants",
        "error_codes",
    }
    if set(schema) != exact_root:
        fail(f"{expected_name}: schema root exact keys mismatch")
    if schema["schema"] != expected_name:
        fail(f"{expected_name}: schema id mismatch")
    if schema["exact_object_keys"] is not True:
        fail(f"{expected_name}: exact_object_keys must be true")
    if len(schema["error_codes"]) != len(set(schema["error_codes"])):
        fail(f"{expected_name}: duplicate error code")
    enum_names = set(schema["enums"])
    object_names = set(schema["objects"])
    for enum_name, values in schema["enums"].items():
        if not isinstance(values, list) or not values or len(values) != len(set(values)):
            fail(f"{expected_name}: invalid enum {enum_name}")
    for object_name, fields in schema["objects"].items():
        if not fields:
            fail(f"{expected_name}: empty object {object_name}")
        for field_name, descriptor in fields.items():
            if set(descriptor) != {"type", "cardinality", "nullable"}:
                fail(f"{expected_name}:{object_name}.{field_name}: descriptor keys")
            if descriptor["cardinality"] not in ("one", "many"):
                fail(f"{expected_name}:{object_name}.{field_name}: cardinality")
            if type(descriptor["nullable"]) is not bool:
                fail(f"{expected_name}:{object_name}.{field_name}: nullable must be bool")
            type_name = descriptor["type"]
            if type_name.startswith("enum:"):
                if type_name.split(":", 1)[1] not in enum_names:
                    fail(f"{expected_name}:{object_name}.{field_name}: unknown enum")
            elif type_name not in {
                "string",
                "sha256",
                "date",
                "partial_date",
                "integer",
                "boolean",
            } and type_name not in object_names:
                fail(f"{expected_name}:{object_name}.{field_name}: unknown type {type_name}")
            if type_name in ("json", "Any", "mapping"):
                fail(f"{expected_name}:{object_name}.{field_name}: untyped field forbidden")


def scalar_type_ok(value: Any, type_name: str, enums: dict[str, list[Any]]) -> bool:
    if type_name == "string":
        return isinstance(value, str) and bool(value)
    if type_name == "sha256":
        return isinstance(value, str) and bool(SHA_RE.fullmatch(value))
    if type_name == "date":
        if not isinstance(value, str) or not DATE_RE.fullmatch(value):
            return False
        try:
            dt.date.fromisoformat(value)
        except ValueError:
            return False
        return True
    if type_name == "partial_date":
        if not isinstance(value, str) or not PARTIAL_DATE_RE.fullmatch(value):
            return False
        parts = value.split("-")
        if len(parts) == 1:
            return int(parts[0]) >= 1
        if len(parts) == 2:
            return 1 <= int(parts[1]) <= 12
        try:
            dt.date.fromisoformat(value)
        except ValueError:
            return False
        return True
    if type_name == "integer":
        return type(value) is int
    if type_name == "boolean":
        return type(value) is bool
    if type_name.startswith("enum:"):
        return value in enums[type_name.split(":", 1)[1]]
    return False


def validate_exact_object(
    object_name: str,
    value: Any,
    schema: dict[str, Any],
    path: str,
    issues: list[str],
) -> None:
    if not isinstance(value, dict):
        issues.append("PUB_TYPE_MISMATCH")
        return
    descriptors = schema["objects"][object_name]
    if set(value) != set(descriptors):
        issues.append("PUB_SCHEMA_EXACT_KEYS")
        return
    for field_name, descriptor in descriptors.items():
        current = value[field_name]
        item_path = f"{path}/{field_name}"
        if current is None:
            if not descriptor["nullable"]:
                issues.append("PUB_TYPE_MISMATCH")
            continue
        items = current
        if descriptor["cardinality"] == "many":
            if not isinstance(current, list):
                issues.append("PUB_TYPE_MISMATCH")
                continue
            items = current
        else:
            items = [current]
        for index, item in enumerate(items):
            type_name = descriptor["type"]
            nested_path = f"{item_path}/{index}" if descriptor["cardinality"] == "many" else item_path
            if type_name in schema["objects"]:
                validate_exact_object(type_name, item, schema, nested_path, issues)
            elif not scalar_type_ok(item, type_name, schema["enums"]):
                if type_name == "boolean":
                    issues.append("PUB_TYPE_BOOL_REQUIRED")
                elif type_name.startswith("enum:"):
                    issues.append("PUB_ENUM_UNKNOWN")
                elif type_name in ("date", "partial_date"):
                    issues.append("PUB_DATE_INVALID")
                else:
                    issues.append("PUB_TYPE_MISMATCH")
    hash_field = SELF_HASH_FIELD.get(object_name)
    if hash_field and hash_field in value:
        core = {k: v for k, v in value.items() if k != hash_field}
        if canonical_hash(core) != value[hash_field]:
            issues.append("PUB_HASH_MISMATCH")


def check_sorted_unique(values: list[str], issues: list[str]) -> None:
    if len(values) != len(set(values)):
        issues.append("PUB_DUPLICATE_REF")
    if values != sorted(set(values)):
        issues.append("PUB_SET_ORDER_OR_DUPLICATE")


def partial_date_bounds(value: str) -> tuple[dt.date, dt.date] | None:
    if not isinstance(value, str) or not PARTIAL_DATE_RE.fullmatch(value):
        return None
    parts = value.split("-")
    try:
        if len(parts) == 1:
            year = int(parts[0])
            return dt.date(year, 1, 1), dt.date(year, 12, 31)
        if len(parts) == 2:
            year, month = map(int, parts)
            last_day = calendar.monthrange(year, month)[1]
            return dt.date(year, month, 1), dt.date(year, month, last_day)
        exact = dt.date.fromisoformat(value)
        return exact, exact
    except (ValueError, OverflowError):
        return None


def endpoint_requires_pending(endpoint: dict[str, Any] | None) -> bool:
    return endpoint is None or (
        endpoint["state"] == "missing" or endpoint["main_axis_projectable"] is False
    )


def check_endpoint(endpoint: dict[str, Any], issues: list[str]) -> None:
    state = endpoint["state"]
    exact = endpoint["exact_date"]
    start = endpoint["range_start"]
    end = endpoint["range_end"]
    candidates = endpoint["candidate_values"]
    projectable = endpoint["main_axis_projectable"]
    projection_authorized = endpoint["range_projection_authorized"]
    check_sorted_unique(candidates, issues)
    check_sorted_unique(endpoint["source_locator_refs"], issues)
    if state == "exact":
        if exact is None or start is not None or end is not None or candidates:
            issues.append("PUB_DATE_STATE_INVALID")
        if not projectable or not projection_authorized:
            issues.append("PUB_DATE_PROJECTABILITY_MISMATCH")
    elif state in ("partial", "conflicted"):
        if exact is not None or not candidates or ((start is None) != (end is None)):
            issues.append("PUB_DATE_STATE_INVALID")
        bounded_range = start is not None and end is not None
        if projectable != (bounded_range and projection_authorized):
            issues.append("PUB_DATE_PROJECTABILITY_MISMATCH")
        if bounded_range:
            try:
                range_start = dt.date.fromisoformat(start)
                range_end = dt.date.fromisoformat(end)
                if range_start > range_end:
                    issues.append("PUB_DATE_RANGE_ORDER")
                candidate_bounds = [partial_date_bounds(value) for value in candidates]
                if any(bounds is None for bounds in candidate_bounds):
                    issues.append("PUB_DATE_INVALID")
                else:
                    typed_bounds = [bounds for bounds in candidate_bounds if bounds]
                    candidate_start = min(bounds[0] for bounds in typed_bounds)
                    candidate_end = max(bounds[1] for bounds in typed_bounds)
                    if (
                        candidate_start != range_start
                        or candidate_end != range_end
                    ):
                        issues.append("PUB_DATE_CANDIDATE_RANGE_MISMATCH")
            except ValueError:
                issues.append("PUB_DATE_INVALID")
    elif state == "missing":
        if exact is not None or start is not None or end is not None or candidates or projectable or projection_authorized:
            issues.append("PUB_DATE_FABRICATION_FORBIDDEN")
        if endpoint["study_day"] is not None:
            issues.append("PUB_DATE_FABRICATION_FORBIDDEN")


def check_geometry(item: dict[str, Any], issues: list[str]) -> None:
    start_state = item["start_endpoint"]["state"]
    end_state = item["end_endpoint"]["state"]
    geometry = item["geometry"]
    valid = {
        "point": start_state != "missing" and item["start_endpoint"] == item["end_endpoint"],
        "closed_interval": start_state != "missing" and end_state != "missing",
        "open_start": start_state == "missing" and end_state != "missing",
        "open_end": start_state != "missing" and end_state == "missing",
    }
    if not valid.get(geometry, False):
        issues.append("PUB_DATE_GEOMETRY_INVALID")
        return
    endpoints_equal = item["start_endpoint"] == item["end_endpoint"]
    if endpoints_equal and geometry != "point":
        issues.append("PUB_DATE_GEOMETRY_DEGENERATE")
    if geometry == "closed_interval" and endpoints_equal:
        issues.append("PUB_DATE_GEOMETRY_DEGENERATE")
    if geometry in ("closed_interval", "point"):
        start_lower = item["start_endpoint"]["exact_date"] or item["start_endpoint"]["range_start"]
        end_upper = item["end_endpoint"]["exact_date"] or item["end_endpoint"]["range_end"]
        if start_lower is not None and end_upper is not None:
            try:
                start_date = dt.date.fromisoformat(start_lower)
                end_date = dt.date.fromisoformat(end_upper)
                if start_date > end_date:
                    issues.append("PUB_INTERVAL_ORDER")
                elif geometry == "closed_interval" and start_date == end_date:
                    issues.append("PUB_DATE_GEOMETRY_DEGENERATE")
            except ValueError:
                issues.append("PUB_DATE_INVALID")


def reference_universe_subject(projection: dict[str, Any]) -> set[str]:
    return {loc["locator_ref"] for loc in projection["source_locators"]}


def validate_visibility_and_sources(
    receipt: dict[str, Any], projection: dict[str, Any], issues: list[str]
) -> set[str]:
    scope = projection["scope_identity"]
    visibility = receipt["visibility_closure"]
    subject_ref = scope["subject_ref"]
    site_ref = scope["site_ref"]
    visibility_ref_arrays = (
        visibility["evaluation_member_refs"],
        visibility["evaluation_site_refs"],
        visibility["projectable_member_refs"],
        visibility["projectable_site_refs"],
        visibility["hidden_member_refs"],
        visibility["hidden_site_refs"],
    )
    for values in visibility_ref_arrays:
        check_sorted_unique(values, issues)
    expected_decision_hash = canonical_hash(
        {
            "project_ref": scope["project_ref"],
            "run_ref": scope["run_ref"],
            "snapshot_ref": scope["snapshot_ref"],
            "cutoff_state": scope["cutoff_state"],
            "cutoff_ref": scope["cutoff_ref"],
            "site_ref": site_ref,
            "subject_ref": subject_ref,
            "spine_ref": scope["spine_ref"],
            "state": "projectable",
        }
    )
    if (
        visibility["evaluation_member_refs"] != [subject_ref]
        or visibility["projectable_member_refs"] != [subject_ref]
        or visibility["hidden_member_refs"] != []
        or visibility["evaluation_site_refs"] != [site_ref]
        or visibility["projectable_site_refs"] != [site_ref]
        or visibility["hidden_site_refs"] != []
        or visibility["hidden_member_count"] != 0
        or visibility["hidden_site_count"] != 0
        or visibility["subject_visibility_state"] != "projectable"
        or visibility["visibility_decision_id"]
        != f"visibility::{subject_ref}::{scope['snapshot_ref']}"
        or visibility["visibility_decision_hash"] != expected_decision_hash
    ):
        issues.append("PUB_VISIBILITY_SCOPE_MISMATCH")
        issues.append("PUB_VISIBILITY_NOT_PROJECTABLE")
    if visibility["deep_link_eligible"] is not True:
        issues.append("PUB_VISIBILITY_DEEP_LINK_INELIGIBLE")
    locators = projection["source_locators"]
    if [row["locator_ref"] for row in locators] != sorted(
        row["locator_ref"] for row in locators
    ):
        issues.append("PUB_SET_ORDER_OR_DUPLICATE")
    locator_universe = {loc["locator_ref"] for loc in locators}
    if len(locator_universe) != len(locators):
        issues.append("PUB_DUPLICATE_REF")
    pairs = receipt["source_revision_content_pairs"]
    if [pair["revision_id"] for pair in pairs] != sorted(
        pair["revision_id"] for pair in pairs
    ):
        issues.append("PUB_SET_ORDER_OR_DUPLICATE")
    pair_by_revision: dict[str, dict[str, Any]] = {}
    for pair in pairs:
        check_sorted_unique(pair["locator_refs"], issues)
        if not pair["locator_refs"]:
            issues.append("PUB_SOURCE_PARTITION_MISMATCH")
        if pair["revision_id"] in pair_by_revision:
            issues.append("PUB_SOURCE_REVISION_UNRESOLVED")
            issues.append("PUB_SOURCE_PARTITION_MISMATCH")
        pair_by_revision[pair["revision_id"]] = pair
        core = {k: v for k, v in pair.items() if k != "pair_content_hash"}
        if canonical_hash(core) != pair["pair_content_hash"]:
            issues.append("PUB_SOURCE_REVISION_UNRESOLVED")
    refs_by_revision: dict[str, set[str]] = {}
    for loc in locators:
        if loc["snapshot_ref"] != scope["snapshot_ref"]:
            issues.append("PUB_LOCATOR_SNAPSHOT_MISMATCH")
        pair = pair_by_revision.get(loc["source_revision_ref"])
        if pair is None:
            issues.append("PUB_SOURCE_REVISION_UNRESOLVED")
            continue
        if loc["source_revision_content_hash"] != pair["accepted_content_hash"]:
            issues.append("PUB_SOURCE_CONTENT_MISMATCH")
        refs_by_revision.setdefault(loc["source_revision_ref"], set()).add(
            loc["locator_ref"]
        )
    for revision, pair in pair_by_revision.items():
        if set(pair["locator_refs"]) != refs_by_revision.get(revision, set()):
            issues.append("PUB_SOURCE_REVISION_UNRESOLVED")
            issues.append("PUB_SOURCE_PARTITION_MISMATCH")
    all_pair_refs = [ref for pair in pairs for ref in pair["locator_refs"]]
    if len(all_pair_refs) != len(set(all_pair_refs)) or set(all_pair_refs) != locator_universe:
        issues.append("PUB_SOURCE_REVISION_UNRESOLVED")
        issues.append("PUB_SOURCE_PARTITION_MISMATCH")
    return locator_universe


def expected_subject_evaluation_identities(
    receipt: dict[str, Any], projection: dict[str, Any]
) -> list[str]:
    values = [
        projection["projection_content_hash"],
        projection["scope_identity"]["identity_content_hash"],
        projection["membership_index"]["membership_content_hash"],
        projection["axis_basis"]["axis_content_hash"],
    ]
    values.extend(
        pair["accepted_content_hash"] for pair in receipt["source_revision_content_pairs"]
    )
    values.extend(row["visit_content_hash"] for row in projection["visits"])
    values.extend(row["event_content_identity"] for row in projection["events"])
    values.extend(row["event_content_hash"] for row in projection["events"])
    values.extend(row["risk_content_identity"] for row in projection["risk_anchors"])
    values.extend(row["risk_anchor_content_hash"] for row in projection["risk_anchors"])
    values.extend(row["pending_content_hash"] for row in projection["pending_date_items"])
    values.extend(row["phase_content_hash"] for row in projection["phase_bands"])
    values.extend(row["track_content_hash"] for row in projection["domain_tracks"])
    values.extend(row["locator_content_hash"] for row in projection["source_locators"])
    return sorted(set(values))


def expected_aemh_evaluation_identities(
    receipt: dict[str, Any], projection: dict[str, Any]
) -> list[str]:
    values = [
        projection["projection_content_hash"],
        projection["scope_identity"]["identity_content_hash"],
        projection["membership_index"]["membership_content_hash"],
        projection["cutoff_endpoint"]["cutoff_content_hash"],
    ]
    values.extend(
        pair["accepted_content_hash"] for pair in receipt["source_revision_content_pairs"]
    )
    if projection["previous_projection_content_hash"] is not None:
        values.append(projection["previous_projection_content_hash"])
    values.extend(row["prefix_content_hash"] for row in projection["accepted_thread_prefixes"])
    for thread in projection["threads"]:
        values.extend(
            [thread["candidate_content_identity"], thread["thread_content_hash"]]
        )
        for entry in thread["history_entries"]:
            values.append(entry["entry_hash"])
            values.extend(entry["later_fact_content_identities"])
            values.extend(
                evidence["evidence_content_hash"]
                for evidence in entry["identity_evidence"]
            )
    values.extend(row["locator_content_hash"] for row in projection["source_locators"])
    return sorted(set(values))


def validate_subject(packet: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    validate_exact_object("SubjectTemporalAuthorityPacket", packet, schema, "", issues)
    if issues and "PUB_SCHEMA_EXACT_KEYS" in issues:
        return sorted(set(issues))
    receipt = packet["receipt"]
    projection = packet["projection"]
    if receipt["receipt_variant"] != "subject_temporal" or receipt["authority_contract_id"] != "subject-temporal-public-v1":
        issues.append("PUB_ENUM_UNKNOWN")
    if projection["contract_id"] != "subject-temporal-public-v1":
        issues.append("PUB_ENUM_UNKNOWN")
    if (
        projection["schema_version"] != schema["schema_version"]
        or receipt["authority_contract_version"] != schema["schema_version"]
    ):
        issues.append("PUB_CONTRACT_VERSION_MISMATCH")
    if receipt["audience_contract_id"] != PARENT_R5_AUDIENCE_CONTRACT_ID:
        issues.append("PUB_AUDIENCE_CONTRACT_MISMATCH")
    if projection["receipt_ref"] != receipt["receipt_id"]:
        issues.append("PUB_HASH_MISMATCH")
    expected_projection_id = canonical_hash(
        {
            "contract_id": projection["contract_id"],
            "schema_version": projection["schema_version"],
            "scope_identity_hash": projection["scope_identity"]["identity_content_hash"],
            "membership_index_hash": projection["membership_index"]["membership_content_hash"],
            "axis_basis_hash": projection["axis_basis"]["axis_content_hash"],
        }
    )
    if projection["projection_id"] != expected_projection_id:
        issues.append("PUB_HASH_MISMATCH")
    expected_receipt_id = canonical_hash(
        {
            "receipt_variant": receipt["receipt_variant"],
            "authority_contract_id": receipt["authority_contract_id"],
            "scope_identity_hash": receipt["scope_identity"]["identity_content_hash"],
            "public_projection_id": receipt["public_projection_id"],
        }
    )
    if receipt["receipt_id"] != expected_receipt_id:
        issues.append("PUB_HASH_MISMATCH")
    if receipt["public_projection_id"] != projection["projection_id"] or receipt["public_projection_content_hash"] != projection["projection_content_hash"]:
        issues.append("PUB_HASH_MISMATCH")
    if receipt["scope_identity"] != projection["scope_identity"]:
        issues.append("PUB_IDENTITY_SUBJECT_MISMATCH")
    locator_universe = validate_visibility_and_sources(receipt, projection, issues)
    check_sorted_unique(receipt["evaluation_content_identities"], issues)
    if receipt["evaluation_content_identities"] != expected_subject_evaluation_identities(
        receipt, projection
    ):
        issues.append("PUB_EVALUATION_IDENTITY_MISMATCH")
    if projection["fallback_policy"] != "fail_closed_no_nearest":
        issues.append("PUB_NEAREST_FALLBACK_FORBIDDEN")
    collection_id_fields = {
        "visits": "visit_ref",
        "events": "event_ref",
        "risk_anchors": "risk_anchor_ref",
        "pending_date_items": "pending_ref",
        "phase_bands": "phase_ref",
    }
    for collection, id_field in collection_id_fields.items():
        check_sorted_unique(
            [row[id_field] for row in projection[collection]], issues
        )
    if [row["domain"] for row in projection["domain_tracks"]] != schema["enums"][
        "domain"
    ]:
        issues.append("PUB_DOMAIN_UNKNOWN")
        if len({row["domain"] for row in projection["domain_tracks"]}) != len(
            projection["domain_tracks"]
        ):
            issues.append("PUB_DUPLICATE_REF")
    check_sorted_unique(projection["axis_basis"]["source_locator_refs"], issues)
    for visit in projection["visits"]:
        check_sorted_unique(visit["source_locator_refs"], issues)
    for event in projection["events"]:
        check_sorted_unique(event["risk_anchor_refs"], issues)
        check_sorted_unique(event["source_locator_refs"], issues)
    for risk in projection["risk_anchors"]:
        check_sorted_unique(risk["source_locator_refs"], issues)
    for pending in projection["pending_date_items"]:
        check_sorted_unique(pending["source_locator_refs"], issues)
    for phase in projection["phase_bands"]:
        check_sorted_unique(phase["source_locator_refs"], issues)
    for track in projection["domain_tracks"]:
        check_sorted_unique(track["event_refs"], issues)
        check_sorted_unique(track["risk_anchor_refs"], issues)
    for values in projection["membership_index"].values():
        if isinstance(values, list):
            check_sorted_unique(values, issues)
    cutoff_identity = projection["scope_identity"]
    cutoff_endpoint = projection["axis_basis"]["cutoff_endpoint"]
    if cutoff_identity["cutoff_state"] == "present":
        if (
            cutoff_identity["cutoff_ref"] is None
            or cutoff_endpoint["state"] != "exact"
            or cutoff_endpoint["exact_date"] != cutoff_identity["cutoff_ref"]
            or cutoff_endpoint["range_start"] is not None
            or cutoff_endpoint["range_end"] is not None
            or cutoff_endpoint["candidate_values"]
            or cutoff_endpoint["main_axis_projectable"] is not True
            or cutoff_endpoint["range_projection_authorized"] is not True
            or cutoff_endpoint["study_day"] is not None
        ):
            issues.append("PUB_IDENTITY_CUTOFF_MISMATCH")
            issues.append("PUB_CUTOFF_STATE_MISMATCH")
    elif (
        cutoff_identity["cutoff_ref"] is not None
        or cutoff_endpoint["state"] != "missing"
        or cutoff_endpoint["exact_date"] is not None
        or cutoff_endpoint["range_start"] is not None
        or cutoff_endpoint["range_end"] is not None
        or cutoff_endpoint["candidate_values"]
        or cutoff_endpoint["main_axis_projectable"] is not False
        or cutoff_endpoint["range_projection_authorized"] is not False
        or cutoff_endpoint["study_day"] is not None
    ):
        issues.append("PUB_IDENTITY_CUTOFF_MISMATCH")
        issues.append("PUB_CUTOFF_STATE_MISMATCH")
    all_referenced: list[str] = []
    all_referenced.extend(projection["axis_basis"]["source_locator_refs"])
    for collection in ("visits", "events", "risk_anchors", "pending_date_items", "phase_bands"):
        for item in projection[collection]:
            all_referenced.extend(item["source_locator_refs"])
    for endpoint_owner in [projection["axis_basis"]] + projection["events"] + projection["risk_anchors"] + projection["pending_date_items"] + projection["phase_bands"]:
        endpoint_names = [name for name in ("cutoff_endpoint", "start_endpoint", "end_endpoint") if name in endpoint_owner]
        for name in endpoint_names:
            check_endpoint(endpoint_owner[name], issues)
            all_referenced.extend(endpoint_owner[name]["source_locator_refs"])
    for visit in projection["visits"]:
        for name in ("nominal_endpoint", "actual_endpoint"):
            if visit[name] is not None:
                check_endpoint(visit[name], issues)
                all_referenced.extend(visit[name]["source_locator_refs"])
        if visit["visit_kind"] == "unscheduled" and (
            visit["planned_visit_ref"] is not None
            or visit["accepted_assignment_ref"] is not None
            or visit["actual_encounter_ref"] is None
        ):
            issues.append("PUB_UNSCHEDULED_PLANNED_BINDING_FORBIDDEN")
    if any(ref not in locator_universe for ref in all_referenced):
        issues.append("PUB_SOURCE_LOCATOR_UNRESOLVED")
    if set(all_referenced) != locator_universe:
        issues.append("PUB_SOURCE_LOCATOR_UNUSED")
    for collection in ("events", "risk_anchors", "phase_bands"):
        for item in projection[collection]:
            check_geometry(item, issues)
    event_by_ref = {event["event_ref"]: event for event in projection["events"]}
    study_day_anchor = projection["axis_basis"]["study_day_anchor_event_ref"]
    temporal_endpoints = [projection["axis_basis"]["cutoff_endpoint"]]
    temporal_endpoints.extend(
        endpoint
        for visit in projection["visits"]
        for endpoint in (visit["nominal_endpoint"], visit["actual_endpoint"])
        if endpoint is not None
    )
    temporal_endpoints.extend(
        endpoint
        for collection in (
            projection["events"],
            projection["risk_anchors"],
            projection["phase_bands"],
            projection["pending_date_items"],
        )
        for item in collection
        for endpoint in (item["start_endpoint"], item["end_endpoint"])
    )
    has_study_day = any(
        endpoint["study_day"] is not None for endpoint in temporal_endpoints
    )
    anchor_event = event_by_ref.get(study_day_anchor)
    anchor_valid = (
        anchor_event is not None
        and study_day_anchor in projection["membership_index"]["event_refs"]
        and anchor_event["start_endpoint"]["state"] == "exact"
        and anchor_event["start_endpoint"]["exact_date"] is not None
        and anchor_event["start_endpoint"]["main_axis_projectable"] is True
        and bool(anchor_event["start_endpoint"]["source_locator_refs"])
        and set(anchor_event["start_endpoint"]["source_locator_refs"])
        <= locator_universe
    )
    if (
        study_day_anchor is not None
        or projection["axis_basis"]["default_axis_mode"] == "study_day"
        or has_study_day
    ) and not anchor_valid:
        issues.append("PUB_STUDY_DAY_ANCHOR_MISSING")
    zero_flag = projection["axis_basis"]["study_day_zero_exists"]
    if study_day_anchor is None:
        if zero_flag is not None:
            issues.append("PUB_STUDY_DAY_VALUE_MISMATCH")
    elif anchor_valid:
        anchor_endpoint = anchor_event["start_endpoint"]
        anchor_study_day = anchor_endpoint["study_day"]
        if anchor_study_day not in (0, 1):
            issues.append("PUB_STUDY_DAY_VALUE_MISMATCH")
        else:
            expected_zero_flag = anchor_study_day == 0
            if zero_flag is not expected_zero_flag:
                issues.append("PUB_STUDY_DAY_VALUE_MISMATCH")
            try:
                anchor_date = dt.date.fromisoformat(
                    anchor_endpoint["exact_date"]
                )
            except ValueError:
                issues.append("PUB_STUDY_DAY_VALUE_MISMATCH")
                anchor_date = None
            for temporal_endpoint in temporal_endpoints:
                study_day = temporal_endpoint["study_day"]
                if study_day is None:
                    continue
                if (
                    temporal_endpoint["state"] != "exact"
                    or temporal_endpoint["exact_date"] is None
                ):
                    issues.append("PUB_STUDY_DAY_VALUE_MISMATCH")
                    continue
                try:
                    endpoint_date = dt.date.fromisoformat(
                        temporal_endpoint["exact_date"]
                    )
                except ValueError:
                    issues.append("PUB_STUDY_DAY_VALUE_MISMATCH")
                    continue
                if anchor_date is None:
                    continue
                delta = (endpoint_date - anchor_date).days
                expected_study_day = (
                    delta
                    if expected_zero_flag or delta < 0
                    else delta + 1
                )
                if study_day != expected_study_day:
                    issues.append("PUB_STUDY_DAY_VALUE_MISMATCH")
    visits_by_ref = {row["visit_ref"]: row for row in projection["visits"]}
    events_by_ref = {row["event_ref"]: row for row in projection["events"]}
    risks_by_ref = {row["risk_anchor_ref"]: row for row in projection["risk_anchors"]}
    phases_by_ref = {row["phase_ref"]: row for row in projection["phase_bands"]}
    for visit in projection["visits"]:
        if visit["phase_ref"] is not None and visit["phase_ref"] not in phases_by_ref:
            issues.append("PUB_REFERENCE_PHASE_MISMATCH")
    for event in projection["events"]:
        if event["applicability_state"] != "applicable":
            issues.append("PUB_DOMAIN_APPLICABILITY_MISMATCH")
        if event["visit_ref"] is not None and event["visit_ref"] not in visits_by_ref:
            issues.append("PUB_REFERENCE_UNRESOLVED")
        for risk_ref in event["risk_anchor_refs"]:
            risk = risks_by_ref.get(risk_ref)
            if risk is None:
                issues.append("PUB_REFERENCE_UNRESOLVED")
            elif risk["domain"] != event["domain"] or risk["event_ref"] != event["event_ref"]:
                issues.append("PUB_REFERENCE_DOMAIN_MISMATCH")
    for risk in projection["risk_anchors"]:
        if risk["event_ref"] is not None:
            event = events_by_ref.get(risk["event_ref"])
            if event is None:
                issues.append("PUB_REFERENCE_UNRESOLVED")
            elif event["domain"] != risk["domain"] or risk["risk_anchor_ref"] not in event["risk_anchor_refs"]:
                issues.append("PUB_REFERENCE_DOMAIN_MISMATCH")
        if risk["visit_ref"] is not None and risk["visit_ref"] not in visits_by_ref:
            issues.append("PUB_REFERENCE_UNRESOLVED")
    for track in projection["domain_tracks"]:
        domain_has_members = any(
            event["domain"] == track["domain"] for event in projection["events"]
        ) or any(
            risk["domain"] == track["domain"]
            for risk in projection["risk_anchors"]
        )
        if track["applicability_state"] == "applicable":
            if not domain_has_members:
                issues.append("PUB_DOMAIN_APPLICABILITY_MISMATCH")
        elif track["applicability_state"] in (
            "not_applicable",
            "not_provided",
        ) and (domain_has_members or track["event_refs"] or track["risk_anchor_refs"]):
            issues.append("PUB_DOMAIN_APPLICABILITY_MISMATCH")
        for event_ref in track["event_refs"]:
            event = events_by_ref.get(event_ref)
            if event is None:
                issues.append("PUB_REFERENCE_UNRESOLVED")
            elif event["domain"] != track["domain"]:
                issues.append("PUB_REFERENCE_DOMAIN_MISMATCH")
        for risk_ref in track["risk_anchor_refs"]:
            risk = risks_by_ref.get(risk_ref)
            if risk is None:
                issues.append("PUB_REFERENCE_UNRESOLVED")
            elif risk["domain"] != track["domain"]:
                issues.append("PUB_REFERENCE_DOMAIN_MISMATCH")
    tracked_events = [ref for track in projection["domain_tracks"] for ref in track["event_refs"]]
    tracked_risks = [ref for track in projection["domain_tracks"] for ref in track["risk_anchor_refs"]]
    if sorted(tracked_events) != sorted(events_by_ref) or len(tracked_events) != len(set(tracked_events)):
        issues.append("PUB_MEMBERSHIP_MISMATCH")
    if sorted(tracked_risks) != sorted(risks_by_ref) or len(tracked_risks) != len(set(tracked_risks)):
        issues.append("PUB_MEMBERSHIP_MISMATCH")
    target_specs: dict[
        tuple[str, str],
        tuple[
            str | None,
            dict[str, Any] | None,
            dict[str, Any] | None,
            list[str],
            str,
            bool,
        ],
    ] = {}
    for visit in projection["visits"]:
        visit_endpoints = [
            endpoint
            for endpoint in (visit["actual_endpoint"], visit["nominal_endpoint"])
            if endpoint is not None
        ]
        problematic_endpoints = [
            endpoint for endpoint in visit_endpoints if endpoint_requires_pending(endpoint)
        ]
        effective_endpoint = (
            problematic_endpoints[0]
            if problematic_endpoints
            else (visit_endpoints[0] if visit_endpoints else None)
        )
        target_specs[("visit", visit["visit_ref"])] = (
            None,
            effective_endpoint,
            effective_endpoint,
            visit["source_locator_refs"],
            visit["visit_content_hash"],
            not visit_endpoints or bool(problematic_endpoints),
        )
    for kind, collection, ref_field in (
        ("event", projection["events"], "event_ref"),
        ("risk", projection["risk_anchors"], "risk_anchor_ref"),
        ("phase", projection["phase_bands"], "phase_ref"),
    ):
        for target in collection:
            target_specs[(kind, target[ref_field])] = (
                target["domain"] if kind in ("event", "risk") else None,
                target["start_endpoint"],
                target["end_endpoint"],
                target["source_locator_refs"],
                target[
                    {
                        "event": "event_content_hash",
                        "risk": "risk_anchor_content_hash",
                        "phase": "phase_content_hash",
                    }[kind]
                ],
                endpoint_requires_pending(target["start_endpoint"])
                or endpoint_requires_pending(target["end_endpoint"]),
            )
    pending_counts: dict[tuple[str, str], int] = {}
    for pending in projection["pending_date_items"]:
        key = (pending["item_kind"], pending["item_ref"])
        pending_counts[key] = pending_counts.get(key, 0) + 1
        spec = target_specs.get(key)
        if spec is None:
            issues.append("PUB_REFERENCE_UNRESOLVED")
            issues.append("PUB_PENDING_COVERAGE_MISMATCH")
            continue
        (
            domain,
            start_endpoint,
            end_endpoint,
            source_refs,
            target_content_hash,
            _requires_pending,
        ) = spec
        if pending["domain"] != domain:
            issues.append("PUB_REFERENCE_DOMAIN_MISMATCH")
        if (
            start_endpoint is None
            or end_endpoint is None
            or pending["start_endpoint"] != start_endpoint
            or pending["end_endpoint"] != end_endpoint
            or pending["source_locator_refs"] != source_refs
            or pending["target_content_hash"] != target_content_hash
        ):
            issues.append("PUB_PENDING_MIRROR_MISMATCH")
    expected_pending_keys = {
        key for key, spec in target_specs.items() if spec[5]
    }
    if (
        set(pending_counts) != expected_pending_keys
        or any(count != 1 for count in pending_counts.values())
    ):
        issues.append("PUB_PENDING_COVERAGE_MISMATCH")
    membership = projection["membership_index"]
    expected_membership = {
        "visit_refs": [row["visit_ref"] for row in projection["visits"]],
        "event_refs": [row["event_ref"] for row in projection["events"]],
        "risk_anchor_refs": [row["risk_anchor_ref"] for row in projection["risk_anchors"]],
        "pending_date_refs": [row["pending_ref"] for row in projection["pending_date_items"]],
        "phase_refs": [row["phase_ref"] for row in projection["phase_bands"]],
        "source_locator_refs": sorted(locator_universe),
    }
    for key, expected in expected_membership.items():
        if membership[key] != expected:
            issues.append("PUB_MEMBERSHIP_MISMATCH")
    packet_expected = canonical_hash(
        {
            "receipt_content_hash": receipt["receipt_content_hash"],
            "projection_content_hash": projection["projection_content_hash"],
        }
    )
    if packet["packet_content_hash"] != packet_expected:
        issues.append("PUB_HASH_MISMATCH")
    return sorted(set(issues))


def validate_aemh(
    packet: dict[str, Any],
    schema: dict[str, Any],
    previous_packet: dict[str, Any] | None = None,
) -> list[str]:
    issues: list[str] = []
    validate_exact_object("AEMHMatchHistoryAuthorityPacket", packet, schema, "", issues)
    if issues and "PUB_SCHEMA_EXACT_KEYS" in issues:
        return sorted(set(issues))
    receipt = packet["receipt"]
    projection = packet["projection"]
    if (
        receipt["receipt_variant"] != "aemh_match_history"
        or receipt["authority_contract_id"] != "aemh-match-history-public-v1"
        or projection["contract_id"] != "aemh-match-history-public-v1"
    ):
        issues.append("AEMH_CONTRACT_ID_MISMATCH")
    if (
        projection["schema_version"] != schema["schema_version"]
        or receipt["authority_contract_version"] != schema["schema_version"]
    ):
        issues.append("PUB_CONTRACT_VERSION_MISMATCH")
    if receipt["audience_contract_id"] != PARENT_R5_AUDIENCE_CONTRACT_ID:
        issues.append("PUB_AUDIENCE_CONTRACT_MISMATCH")
    if projection["receipt_ref"] != receipt["receipt_id"]:
        issues.append("PUB_HASH_MISMATCH")
    expected_projection_id = canonical_hash(
        {
            "contract_id": projection["contract_id"],
            "schema_version": projection["schema_version"],
            "scope_identity_hash": projection["scope_identity"]["identity_content_hash"],
            "membership_index_hash": projection["membership_index"]["membership_content_hash"],
        }
    )
    if projection["projection_id"] != expected_projection_id:
        issues.append("PUB_HASH_MISMATCH")
    expected_receipt_id = canonical_hash(
        {
            "receipt_variant": receipt["receipt_variant"],
            "authority_contract_id": receipt["authority_contract_id"],
            "scope_identity_hash": receipt["scope_identity"]["identity_content_hash"],
            "public_projection_id": receipt["public_projection_id"],
        }
    )
    if receipt["receipt_id"] != expected_receipt_id:
        issues.append("PUB_HASH_MISMATCH")
    if receipt["public_projection_id"] != projection["projection_id"] or receipt["public_projection_content_hash"] != projection["projection_content_hash"]:
        issues.append("PUB_HASH_MISMATCH")
    if receipt["scope_identity"] != projection["scope_identity"]:
        issues.append("PUB_IDENTITY_MISMATCH")
    locator_universe = validate_visibility_and_sources(receipt, projection, issues)
    lineage_locator_by_key = {
        (locator["snapshot_ref"], locator["locator_ref"]): locator
        for locator in projection["source_locators"]
    }
    if previous_packet is not None:
        lineage_locator_by_key.update(
            {
                (locator["snapshot_ref"], locator["locator_ref"]): locator
                for locator in previous_packet["projection"]["source_locators"]
            }
        )
    check_sorted_unique(receipt["evaluation_content_identities"], issues)
    if receipt["evaluation_content_identities"] != expected_aemh_evaluation_identities(
        receipt, projection
    ):
        issues.append("PUB_EVALUATION_IDENTITY_MISMATCH")
    if projection["fallback_policy"] != "fail_closed_no_nearest":
        issues.append("PUB_NEAREST_FALLBACK_FORBIDDEN")
    cutoff_identity = projection["scope_identity"]
    cutoff = projection["cutoff_endpoint"]
    if cutoff_identity["cutoff_state"] == "present":
        if (
            cutoff_identity["cutoff_ref"] is None
            or cutoff["state"] != "present"
            or cutoff["exact_date"] != cutoff_identity["cutoff_ref"]
            or not cutoff["source_locator_refs"]
        ):
            issues.append("PUB_IDENTITY_CUTOFF_MISMATCH")
            issues.append("PUB_CUTOFF_STATE_MISMATCH")
    elif (
        cutoff_identity["cutoff_ref"] is not None
        or cutoff["state"] != "absent"
        or cutoff["exact_date"] is not None
        or cutoff["source_locator_refs"]
    ):
        issues.append("PUB_IDENTITY_CUTOFF_MISMATCH")
        issues.append("PUB_CUTOFF_STATE_MISMATCH")
    check_sorted_unique(cutoff["source_locator_refs"], issues)
    if any(ref not in locator_universe for ref in cutoff["source_locator_refs"]):
        issues.append("PUB_SOURCE_LOCATOR_UNRESOLVED")
    all_thread_evidence: set[str] = set()
    consumed_locator_refs: set[str] = set(cutoff["source_locator_refs"])
    later_fact_refs: list[str] = []
    thread_refs = [row["thread_ref"] for row in projection["threads"]]
    candidate_refs = [row["original_candidate_ref"] for row in projection["threads"]]
    prefix_refs = [
        row["thread_ref"] for row in projection["accepted_thread_prefixes"]
    ]
    all_entries = [
        entry
        for thread in projection["threads"]
        for entry in thread["history_entries"]
    ]
    entry_id_counts: dict[str, int] = {}
    for entry in all_entries:
        entry_id_counts[entry["entry_id"]] = (
            entry_id_counts.get(entry["entry_id"], 0) + 1
        )
    if any(count != 1 for count in entry_id_counts.values()):
        issues.append("AEMH_ENTRY_ID_DUPLICATE")
    check_sorted_unique(thread_refs, issues)
    check_sorted_unique(candidate_refs, issues)
    check_sorted_unique(prefix_refs, issues)
    for values in projection["membership_index"].values():
        if isinstance(values, list):
            check_sorted_unique(values, issues)
    for thread in projection["threads"]:
        if (
            thread["project_ref"] != projection["scope_identity"]["project_ref"]
            or thread["site_ref"] != projection["scope_identity"]["site_ref"]
            or thread["subject_ref"] != projection["scope_identity"]["subject_ref"]
        ):
            issues.append("PUB_IDENTITY_MISMATCH")
        check_sorted_unique(thread["evidence_locator_refs"], issues)
        if entry_id_counts.get(thread["original_reminder_ref"], 0) != 1:
            issues.append("AEMH_ORIGINAL_REMINDER_REF_MISMATCH")
        entries = thread["history_entries"]
        reminders = [entry for entry in entries if entry["event_kind"] == "reminder_created"]
        if not entries or entries[0]["event_kind"] != "reminder_created" or entries[0]["seq"] != 1:
            issues.append("AEMH_THREAD_REMINDER_MISSING")
            issues.append("AEMH_THREAD_REMINDER_REWRITTEN")
        if len(reminders) != 1:
            issues.append("AEMH_THREAD_REMINDER_DUPLICATE")
        elif thread["original_reminder_ref"] != reminders[0]["entry_id"]:
            issues.append("AEMH_ORIGINAL_REMINDER_REF_MISMATCH")
        reminder_identity_evidence = (
            set(reminders[0]["identity_evidence_refs"])
            if len(reminders) == 1
            else set()
        )
        prior_hash = None
        retained: set[str] = set()
        later_fact_identity_by_ref: dict[str, str] = {}
        fact_lifecycle: dict[str, dict[str, Any]] = {}
        match_decision_count = 0
        for expected_seq, entry in enumerate(entries, start=1):
            check_sorted_unique(entry["later_fact_refs"], issues)
            check_sorted_unique(entry["identity_evidence_refs"], issues)
            evidence_refs = [
                evidence["evidence_ref"]
                for evidence in entry["identity_evidence"]
            ]
            check_sorted_unique(evidence_refs, issues)
            evidence_entity_keys = [
                (evidence["evidence_kind"], evidence["entity_ref"])
                for evidence in entry["identity_evidence"]
            ]
            if len(evidence_entity_keys) != len(set(evidence_entity_keys)):
                issues.append("AEMH_IDENTITY_EVIDENCE_MISMATCH")
            check_sorted_unique(entry["retained_evidence_locator_refs"], issues)
            entry_retained = set(entry["retained_evidence_locator_refs"])
            if entry["identity_evidence_refs"] != evidence_refs:
                issues.append("AEMH_IDENTITY_EVIDENCE_MISMATCH")
            fact_identity_by_ref = dict(
                zip(
                    entry["later_fact_refs"],
                    entry["later_fact_content_identities"],
                )
            )
            evidence_by_kind: dict[str, list[dict[str, Any]]] = {
                "candidate": [],
                "later_fact": [],
                "considered_fact": [],
            }
            for evidence in entry["identity_evidence"]:
                evidence_by_kind[evidence["evidence_kind"]].append(evidence)
                source_locator = lineage_locator_by_key.get(
                    (entry["snapshot_ref"], evidence["source_locator_ref"])
                )
                if (
                    source_locator is None
                    or evidence["source_locator_ref"] not in entry_retained
                    or evidence["source_locator_content_hash"]
                    != source_locator["locator_content_hash"]
                    or evidence["source_raw_payload_hash"]
                    != source_locator["raw_payload_hash"]
                    or evidence["entity_ref"]
                    != source_locator["authority_entity_ref"]
                    or evidence["evidence_kind"]
                    != source_locator["authority_entity_kind"]
                ):
                    issues.append("AEMH_IDENTITY_EVIDENCE_MISMATCH")
                    continue
                expected_entity_identity = canonical_hash(
                    {
                        "entity_kind": evidence["evidence_kind"],
                        "entity_ref": evidence["entity_ref"],
                        "source_locator_ref": evidence["source_locator_ref"],
                        "source_raw_payload_hash": evidence[
                            "source_raw_payload_hash"
                        ],
                    }
                )
                if evidence["entity_content_identity"] != expected_entity_identity:
                    issues.append("AEMH_IDENTITY_EVIDENCE_MISMATCH")
            candidate_evidence = evidence_by_kind["candidate"]
            later_fact_evidence = evidence_by_kind["later_fact"]
            considered_evidence = evidence_by_kind["considered_fact"]
            candidate_exact = (
                len(candidate_evidence) == 1
                and candidate_evidence[0]["entity_ref"]
                == thread["original_candidate_ref"]
                and candidate_evidence[0]["entity_content_identity"]
                == thread["candidate_content_identity"]
            )
            fact_evidence_exact = {
                evidence["entity_ref"]: evidence["entity_content_identity"]
                for evidence in later_fact_evidence
            } == fact_identity_by_ref and len(later_fact_evidence) == len(
                fact_identity_by_ref
            )
            if entry["event_kind"] == "reminder_created" and (
                not candidate_exact
                or later_fact_evidence
                or considered_evidence
            ):
                issues.append("AEMH_IDENTITY_EVIDENCE_MISMATCH")
            elif entry["event_kind"] == "match_decided":
                if (
                    entry["match_state"] in ("exact", "ambiguous")
                    and (
                        not candidate_exact
                        or not fact_evidence_exact
                        or considered_evidence
                    )
                ) or (
                    entry["match_state"] == "rejected"
                    and (
                        not candidate_exact
                        or later_fact_evidence
                        or not considered_evidence
                    )
                ):
                    issues.append("AEMH_IDENTITY_EVIDENCE_MISMATCH")
            elif entry["event_kind"] in ("withdrawn", "reappeared") and (
                candidate_evidence
                or considered_evidence
                or not fact_evidence_exact
            ):
                issues.append("AEMH_IDENTITY_EVIDENCE_MISMATCH")
            if entry["seq"] != expected_seq:
                issues.append("AEMH_HISTORY_SEQ_GAP")
            if entry["prior_entry_hash"] != prior_hash:
                issues.append("AEMH_HISTORY_PRIOR_HASH_MISMATCH")
            if entry["risk_lifecycle_effect"] != "none":
                issues.append("AEMH_RISK_LIFECYCLE_EFFECT_FORBIDDEN")
            current_retained = entry_retained
            consumed_locator_refs.update(current_retained)
            if not retained <= current_retained:
                issues.append("AEMH_EVIDENCE_RETENTION_VIOLATION")
            retained = current_retained
            if not current_retained <= locator_universe:
                issues.append("PUB_SOURCE_LOCATOR_UNRESOLVED")
            if len(entry["later_fact_refs"]) != len(entry["later_fact_content_identities"]):
                issues.append("AEMH_LATER_FACT_IDENTITY_MISMATCH")
            for fact_ref, content_identity in zip(
                entry["later_fact_refs"], entry["later_fact_content_identities"]
            ):
                prior_identity = later_fact_identity_by_ref.get(fact_ref)
                if prior_identity is not None and prior_identity != content_identity:
                    issues.append("AEMH_LATER_FACT_IDENTITY_DRIFT")
                later_fact_identity_by_ref[fact_ref] = content_identity
            if entry["event_kind"] == "reminder_created":
                if entry["match_state"] is not None or entry["later_fact_refs"]:
                    issues.append("AEMH_THREAD_REMINDER_REWRITTEN")
            elif entry["event_kind"] == "match_decided":
                match_decision_count += 1
                if match_decision_count > 1:
                    issues.append("AEMH_MATCH_DECISION_DUPLICATE")
                state = entry["match_state"]
                count = len(entry["later_fact_refs"])
                if (
                    (state == "exact" and count != 1)
                    or (state == "ambiguous" and count < 2)
                    or (state == "rejected" and count != 0)
                    or state not in ("exact", "ambiguous", "rejected")
                ):
                    issues.append("AEMH_MATCH_STATE_INVALID")
                minimum_identity_evidence = {
                    "exact": len(reminder_identity_evidence) + count,
                    "ambiguous": len(reminder_identity_evidence) + count,
                    "rejected": len(reminder_identity_evidence) + 1,
                }.get(state, 1)
                if (
                    len(entry["identity_evidence_refs"])
                    < minimum_identity_evidence
                    or not reminder_identity_evidence
                    <= set(entry["identity_evidence_refs"])
                    or not entry["retained_evidence_locator_refs"]
                ):
                    issues.append("AEMH_MATCH_EVIDENCE_MISSING")
                if state in ("exact", "ambiguous"):
                    for fact_ref, content_identity in zip(
                        entry["later_fact_refs"],
                        entry["later_fact_content_identities"],
                    ):
                        if fact_ref in fact_lifecycle:
                            issues.append("AEMH_MATCH_DECISION_DUPLICATE")
                        else:
                            fact_lifecycle[fact_ref] = {
                                "content_identity": content_identity,
                                "withdrawn": False,
                            }
            elif entry["event_kind"] in ("withdrawn", "reappeared"):
                if entry["match_state"] is not None:
                    issues.append("AEMH_MATCH_STATE_INVALID")
                fact_pairs = list(
                    zip(
                        entry["later_fact_refs"],
                        entry["later_fact_content_identities"],
                    )
                )
                if not fact_pairs:
                    issues.append("AEMH_LIFECYCLE_TRANSITION_INVALID")
                for fact_ref, content_identity in fact_pairs:
                    lifecycle = fact_lifecycle.get(fact_ref)
                    if (
                        lifecycle is None
                        or lifecycle["content_identity"] != content_identity
                    ):
                        issues.append("AEMH_LIFECYCLE_TRANSITION_INVALID")
                        continue
                    if entry["event_kind"] == "withdrawn":
                        if lifecycle["withdrawn"] is True:
                            issues.append("AEMH_LIFECYCLE_TRANSITION_INVALID")
                        else:
                            lifecycle["withdrawn"] = True
                    elif lifecycle["withdrawn"] is not True:
                        issues.append("AEMH_LIFECYCLE_TRANSITION_INVALID")
                    else:
                        lifecycle["withdrawn"] = False
            later_fact_refs.extend(entry["later_fact_refs"])
            prior_hash = entry["entry_hash"]
        if set(thread["evidence_locator_refs"]) != retained:
            issues.append("AEMH_EVIDENCE_RETENTION_VIOLATION")
        all_thread_evidence.update(thread["evidence_locator_refs"])
        consumed_locator_refs.update(thread["evidence_locator_refs"])
    if previous_packet is None:
        if any(
            entry["snapshot_ref"] != projection["scope_identity"]["snapshot_ref"]
            for thread in projection["threads"]
            for entry in thread["history_entries"]
        ):
            issues.append("AEMH_SNAPSHOT_LINEAGE_MISMATCH")
        if (
            projection["previous_projection_ref"] is not None
            or projection["previous_projection_content_hash"] is not None
            or projection["accepted_thread_prefixes"]
        ):
            issues.append("AEMH_PREVIOUS_PROJECTION_MISMATCH")
    else:
        previous_projection = previous_packet["projection"]
        if (
            projection["previous_projection_ref"] != previous_projection["projection_id"]
            or projection["previous_projection_content_hash"]
            != previous_projection["projection_content_hash"]
        ):
            issues.append("AEMH_PREVIOUS_PROJECTION_MISMATCH")
        previous_threads = {
            thread["thread_ref"]: thread for thread in previous_projection["threads"]
        }
        current_threads = {
            thread["thread_ref"]: thread for thread in projection["threads"]
        }
        prefix_by_thread = {
            anchor["thread_ref"]: anchor
            for anchor in projection["accepted_thread_prefixes"]
        }
        previous_ref_set = set(previous_threads)
        current_ref_set = set(current_threads)
        prefix_ref_set = set(prefix_by_thread)
        if previous_ref_set != current_ref_set:
            issues.append("AEMH_THREAD_SET_MISMATCH")
        if prefix_ref_set != previous_ref_set or prefix_ref_set != current_ref_set:
            issues.append("AEMH_PREFIX_SET_MISMATCH")
        if len(prefix_by_thread) != len(projection["accepted_thread_prefixes"]):
            issues.append("AEMH_PREFIX_HASH_MISMATCH")
        for thread in projection["threads"]:
            previous_thread = previous_threads.get(thread["thread_ref"])
            if previous_thread is None:
                continue
            stable_fields = (
                "thread_ref",
                "project_ref",
                "site_ref",
                "subject_ref",
                "domain",
                "original_candidate_ref",
                "candidate_content_identity",
                "original_reminder_ref",
            )
            if any(
                thread[field] != previous_thread[field] for field in stable_fields
            ):
                issues.append("AEMH_THREAD_STABLE_IDENTITY_MISMATCH")
            anchor = prefix_by_thread.get(thread["thread_ref"])
            if anchor is None:
                issues.append("AEMH_PREFIX_HASH_MISMATCH")
                continue
            previous_entries = previous_thread["history_entries"]
            previous_snapshot_lineage = {
                entry["snapshot_ref"] for entry in previous_entries
            }
            current_snapshot = projection["scope_identity"]["snapshot_ref"]
            current_entries = thread["history_entries"]
            if any(
                entry["snapshot_ref"] not in previous_snapshot_lineage
                | {current_snapshot}
                for entry in current_entries
            ) or any(
                entry["snapshot_ref"] != current_snapshot
                for entry in current_entries[len(previous_entries) :]
            ):
                issues.append("AEMH_SNAPSHOT_LINEAGE_MISMATCH")
            if anchor["accepted_prefix_seq"] != len(previous_entries):
                issues.append("AEMH_PREFIX_SEQ_MISMATCH")
            expected_head = previous_entries[-1]["entry_hash"] if previous_entries else None
            if anchor["accepted_prefix_head_hash"] != expected_head:
                issues.append("AEMH_PREFIX_HASH_MISMATCH")
            if anchor["previous_thread_content_hash"] != previous_thread["thread_content_hash"]:
                issues.append("AEMH_PREFIX_HASH_MISMATCH")
            if thread["history_entries"][: len(previous_entries)] != previous_entries:
                issues.append("AEMH_PREFIX_CONTENT_MISMATCH")
    membership = projection["membership_index"]
    if membership["thread_refs"] != sorted(thread_refs):
        issues.append("PUB_MEMBERSHIP_MISMATCH")
    if membership["candidate_refs"] != sorted(candidate_refs):
        issues.append("PUB_MEMBERSHIP_MISMATCH")
    if membership["later_fact_refs"] != sorted(set(later_fact_refs)):
        issues.append("PUB_MEMBERSHIP_MISMATCH")
    if membership["source_locator_refs"] != sorted(locator_universe):
        issues.append("PUB_MEMBERSHIP_MISMATCH")
    if all_thread_evidence != locator_universe:
        issues.append("AEMH_EVIDENCE_RETENTION_VIOLATION")
    if consumed_locator_refs != locator_universe:
        issues.append("PUB_SOURCE_LOCATOR_UNUSED")
    packet_expected = canonical_hash(
        {
            "receipt_content_hash": receipt["receipt_content_hash"],
            "projection_content_hash": projection["projection_content_hash"],
        }
    )
    if packet["packet_content_hash"] != packet_expected:
        issues.append("PUB_HASH_MISMATCH")
    return sorted(set(issues))


def set_pointer(document: dict[str, Any], pointer: str, value: Any) -> None:
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer.split("/")[1:]]
    current: Any = document
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    final = parts[-1]
    if isinstance(current, list):
        current[int(final)] = value
    else:
        current[final] = value


def get_pointer(document: dict[str, Any], pointer: str) -> Any:
    current: Any = document
    for part in pointer.split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def apply_mutation(document: dict[str, Any], mutation: dict[str, Any]) -> None:
    operation = mutation["op"]
    path = mutation["path"]
    if operation == "replace":
        set_pointer(document, path, copy.deepcopy(mutation["value"]))
    elif operation == "reverse":
        target = get_pointer(document, path)
        if not isinstance(target, list):
            fail(f"reverse mutation target is not a list: {path}")
        target.reverse()
    elif operation == "append":
        target = get_pointer(document, path)
        if not isinstance(target, list):
            fail(f"append mutation target is not a list: {path}")
        target.append(copy.deepcopy(mutation["value"]))
    elif operation == "append_copy":
        target = get_pointer(document, path)
        if not isinstance(target, list):
            fail(f"append_copy mutation target is not a list: {path}")
        target.append(copy.deepcopy(target[mutation["from_index"]]))
    elif operation == "delete":
        parts = path.split("/")
        parent_path = "/".join(parts[:-1])
        parent = get_pointer(document, parent_path)
        final = parts[-1].replace("~1", "/").replace("~0", "~")
        if isinstance(parent, list):
            del parent[int(final)]
        else:
            del parent[final]
    elif operation == "inject_unused_locator":
        locator_value = copy.deepcopy(mutation["locator"])
        pair_value = copy.deepcopy(mutation["source_pair"])
        locator_ref = locator_value["locator_ref"]
        document["projection"]["source_locators"].append(locator_value)
        document["projection"]["source_locators"].sort(
            key=lambda row: row["locator_ref"]
        )
        document["receipt"]["source_revision_content_pairs"].append(pair_value)
        document["receipt"]["source_revision_content_pairs"].sort(
            key=lambda row: row["revision_id"]
        )
        document["projection"]["membership_index"][
            "source_locator_refs"
        ].append(locator_ref)
        document["projection"]["membership_index"][
            "source_locator_refs"
        ].sort()
    elif operation == "forge_later_fact_lineage":
        forged_ref = mutation["forged_ref"]
        source_locator = next(
            locator
            for locator in document["projection"]["source_locators"]
            if locator["locator_ref"] == mutation["source_locator_ref"]
        )
        forged_identity = canonical_hash(
            {
                "entity_kind": "later_fact",
                "entity_ref": forged_ref,
                "source_locator_ref": source_locator["locator_ref"],
                "source_raw_payload_hash": source_locator["raw_payload_hash"],
            }
        )
        for entry in document["projection"]["threads"][0]["history_entries"]:
            if entry["later_fact_refs"]:
                entry["later_fact_refs"] = [forged_ref]
                entry["later_fact_content_identities"] = [forged_identity]
                for evidence in entry["identity_evidence"]:
                    if evidence["evidence_kind"] == "later_fact":
                        evidence["entity_ref"] = forged_ref
                        evidence["entity_content_identity"] = forged_identity
        document["projection"]["membership_index"]["later_fact_refs"] = [
            forged_ref
        ]
    else:
        fail(f"unsupported challenge mutation op: {operation}")


def reseal_exact_object(
    object_name: str, value: dict[str, Any], schema: dict[str, Any]
) -> None:
    descriptors = schema["objects"][object_name]
    for field_name, descriptor in descriptors.items():
        nested_name = descriptor["type"]
        current = value.get(field_name)
        if current is None or nested_name not in schema["objects"]:
            continue
        nested_values = current if descriptor["cardinality"] == "many" else [current]
        for nested_value in nested_values:
            reseal_exact_object(nested_name, nested_value, schema)
    hash_field = SELF_HASH_FIELD.get(object_name)
    if hash_field and hash_field in value:
        value[hash_field] = canonical_hash(
            {key: item for key, item in value.items() if key != hash_field}
        )


def reseal_subject_packet(
    packet: dict[str, Any], schema: dict[str, Any], *, preserve_evaluation: bool
) -> None:
    projection = packet["projection"]
    receipt = packet["receipt"]
    reseal_exact_object("SubjectTemporalPublicProjection", projection, schema)
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
    reseal_exact_object("PublicAuthorityReceipt", receipt, schema)
    receipt["receipt_id"] = canonical_hash(
        {
            "receipt_variant": receipt["receipt_variant"],
            "authority_contract_id": receipt["authority_contract_id"],
            "scope_identity_hash": receipt["scope_identity"]["identity_content_hash"],
            "public_projection_id": projection["projection_id"],
        }
    )
    projection["receipt_ref"] = receipt["receipt_id"]
    reseal_exact_object("SubjectTemporalPublicProjection", projection, schema)
    receipt["public_projection_id"] = projection["projection_id"]
    receipt["public_projection_content_hash"] = projection["projection_content_hash"]
    if not preserve_evaluation:
        receipt["evaluation_content_identities"] = expected_subject_evaluation_identities(
            receipt, projection
        )
    reseal_exact_object("PublicAuthorityReceipt", receipt, schema)
    packet["packet_content_hash"] = canonical_hash(
        {
            "receipt_content_hash": receipt["receipt_content_hash"],
            "projection_content_hash": projection["projection_content_hash"],
        }
    )


def reseal_aemh_packet(
    packet: dict[str, Any], schema: dict[str, Any], *, preserve_evaluation: bool
) -> None:
    projection = packet["projection"]
    receipt = packet["receipt"]
    for thread in projection["threads"]:
        prior_hash = None
        for entry in thread["history_entries"]:
            entry["prior_entry_hash"] = prior_hash
            reseal_exact_object("AEMHMatchHistoryEntry", entry, schema)
            prior_hash = entry["entry_hash"]
        reseal_exact_object("AEMHMatchThread", thread, schema)
    reseal_exact_object("AEMHMatchHistoryPublicProjection", projection, schema)
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
        }
    )
    reseal_exact_object("PublicAuthorityReceipt", receipt, schema)
    receipt["receipt_id"] = canonical_hash(
        {
            "receipt_variant": receipt["receipt_variant"],
            "authority_contract_id": receipt["authority_contract_id"],
            "scope_identity_hash": receipt["scope_identity"]["identity_content_hash"],
            "public_projection_id": projection["projection_id"],
        }
    )
    projection["receipt_ref"] = receipt["receipt_id"]
    reseal_exact_object("AEMHMatchHistoryPublicProjection", projection, schema)
    receipt["public_projection_id"] = projection["projection_id"]
    receipt["public_projection_content_hash"] = projection["projection_content_hash"]
    if not preserve_evaluation:
        receipt["evaluation_content_identities"] = expected_aemh_evaluation_identities(
            receipt, projection
        )
    reseal_exact_object("PublicAuthorityReceipt", receipt, schema)
    packet["packet_content_hash"] = canonical_hash(
        {
            "receipt_content_hash": receipt["receipt_content_hash"],
            "projection_content_hash": projection["projection_content_hash"],
        }
    )


def verify_challenges(
    registry: dict[str, Any],
    parent: dict[str, Any],
    subject_schema_doc: dict[str, Any],
    aemh_schema_doc: dict[str, Any],
    inputs: dict[str, Any],
) -> int:
    expected_root_keys = {
        "schema",
        "contract_id",
        "parent_exact_contract_sha256",
        "inherited_case_range",
        "inherited_cases",
        "public_authority_specific_cases",
        "counts",
        "quota_ledger",
        "quota_rule",
    }
    if set(registry) != expected_root_keys:
        fail("challenge registry exact root keys mismatch")
    if registry["quota_ledger"] is not None:
        fail("second quota ledger is forbidden")
    inherited = registry["inherited_cases"]
    if len(inherited) != 64 or [r["case_id"] for r in inherited] != [f"R5C-{i}" for i in range(101, 165)]:
        fail("inherited R5C-101..164 projection mismatch")
    parent_rows = parent["challenge_rules"][100:164]
    for projected, source in zip(inherited, parent_rows):
        oracle = projected["stage_oracle_contract"]
        if projected["category"] != source["category"] or oracle["rule_id"] != source["rule_id"]:
            fail(f"inherited challenge drift: {projected['case_id']}")
        if oracle["expected_outcome"] != source["expected_outcome"] or oracle["expected_projection"] != source["expected_projection"]:
            fail(f"inherited challenge outcome drift: {projected['case_id']}")
    public = registry["public_authority_specific_cases"]
    expected_public_ids = [f"PA-{index:03d}" for index in range(1, len(public) + 1)]
    if not public or [row["case_id"] for row in public] != expected_public_ids:
        fail("public-authority challenge count/id mismatch")
    if registry["counts"] != {
        "inherited": len(inherited),
        "public_authority_specific": len(public),
    }:
        fail("challenge registry count metadata mismatch")
    executed = 0
    for row in public:
        base_key = row["base_input_key"]
        if row["contract"] == "subject-temporal-public-v1":
            mutated = copy.deepcopy(inputs[base_key])
            apply_mutation(mutated, row["single_mutation"])
            if row["fully_reseal_after_mutation"]:
                reseal_subject_packet(
                    mutated,
                    subject_schema_doc,
                    preserve_evaluation=row["category"].startswith(
                        "subject_evaluation_identity_"
                    ),
                )
            issues = validate_subject(mutated, subject_schema_doc)
        elif row["contract"] == "aemh-match-history-public-v1":
            mutated = copy.deepcopy(inputs[base_key])
            apply_mutation(mutated, row["single_mutation"])
            if row["fully_reseal_after_mutation"]:
                reseal_aemh_packet(
                    mutated,
                    aemh_schema_doc,
                    preserve_evaluation=row["category"].startswith(
                        "aemh_evaluation_identity_"
                    ),
                )
            issues = validate_aemh(
                mutated,
                aemh_schema_doc,
                inputs["aemh_match_history_previous_base"],
            )
        elif row["contract"] == "exact-overlay-v0.1":
            mutated = read_json(
                "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/exact_overlay.json"
            )
            apply_mutation(mutated, row["single_mutation"])
            issues = overlay_validation_issues(mutated, parent)
        elif row["contract"] == "source-matrix-v0.1":
            mutated = read_json(
                "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/source_matrix.json"
            )
            apply_mutation(mutated, row["single_mutation"])
            issues = source_matrix_validation_issues(mutated)
        elif row["contract"] == "manifest-v0.1":
            mutated = read_json(
                "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/manifest.json"
            )
            apply_mutation(mutated, row["single_mutation"])
            if row["fully_reseal_after_mutation"]:
                mutated["manifest_content_hash"] = canonical_hash(
                    {
                        key: value
                        for key, value in mutated.items()
                        if key != "manifest_content_hash"
                    }
                )
            issues = manifest_contract_validation_issues(mutated)
        else:
            fail(f"unknown challenge contract: {row['case_id']}")
        expected = row["expected_typed_outcome_or_error"].split("reject:", 1)[-1]
        if row["fully_reseal_after_mutation"] and "PUB_HASH_MISMATCH" in issues:
            fail(
                f"fully resealed tamper leaked generic hash mismatch: "
                f"{row['case_id']} issues={issues}"
            )
        if expected not in issues:
            fail(
                f"tamper gate failed: {row['case_id']} expected={expected} issues={issues}"
            )
        print(
            f"TAMPER_GATE_REJECT case={row['case_id']} expected={expected} "
            f"fully_resealed={str(row['fully_reseal_after_mutation']).lower()}"
        )
        executed += 1
    return executed


def overlay_validation_issues(
    overlay: dict[str, Any], parent: dict[str, Any]
) -> list[str]:
    parent_deferred = [
        row
        for row in parent["field_mappings"]
        if row.get("deferred_contract") in (
            "subject-temporal-public-v1",
            "aemh-match-history-public-v1",
        )
    ]
    expected_root_keys = {
        "schema",
        "contract_id",
        "parent_exact_contract_sha256",
        "parent_schema",
        "deferred_contracts_closed_by_schema",
        "mapping_replacements",
        "replacement_count",
        "authority_rule",
        "unlock_rule",
    }
    issues: list[str] = []
    if set(overlay) != expected_root_keys:
        return ["PUB_OVERLAY_ARTIFACT_MISMATCH"]
    replacements = overlay["mapping_replacements"]
    parent_pairs = sorted(
        (row["target"], row["deferred_contract"]) for row in parent_deferred
    )
    replacement_pairs = [
        (row["target"], row["parent_deferred_contract"])
        for row in replacements
    ]
    if (
        overlay["replacement_count"] != len(replacements)
        or parent_pairs != sorted(set(parent_pairs))
        or replacement_pairs != sorted(set(replacement_pairs))
        or sorted(set(replacement_pairs)) != parent_pairs
    ):
        issues.append("PUB_OVERLAY_DEFERRED_SET_MISMATCH")
    expected_replacements = []
    for mapping in parent_deferred:
        deferred = mapping["deferred_contract"]
        if deferred == "subject-temporal-public-v1":
            source_path = (
                "subject_temporal_public:SubjectTemporalPublicProjection"
            )
            receipt_variant = "subject_temporal"
        else:
            source_path = (
                "aemh_match_history_public:AEMHMatchHistoryPublicProjection"
            )
            receipt_variant = "aemh_match_history"
        expected_replacements.append(
            {
                "target": mapping["target"],
                "parent_deferred_contract": deferred,
                "replacement_source_kind": (
                    "external_public_authority_requirement"
                ),
                "replacement_source_path": source_path,
                "required_receipt_variant": receipt_variant,
                "implementation_status": "contract_only_not_implemented",
                "adaptation_recipe": mapping["recipe_id"],
            }
        )
    expected_unlock = {
        "contract_acceptance_only_unlocks": (
            "later_public_authority_implementation_contract"
        ),
        "does_not_satisfy": [
            "ACCEPT_SUBJECT_TEMPORAL_PUBLIC_V1",
            "ACCEPT_AEMH_MATCH_HISTORY_PUBLIC_V1",
            "ACCEPT_R5_S5_CONTRACT",
        ],
        "s5_runtime_remains_locked": True,
    }
    if (
        overlay["schema"]
        != "medical-monitoring-r5-s5-public-authority-exact-overlay-v0.1"
        or overlay["contract_id"]
        != "medical-monitoring-r5-s5-public-authority-contract-v0.1"
        or overlay["parent_exact_contract_sha256"]
        != "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949"
        or overlay["parent_schema"] != parent["schema"]
        or overlay["deferred_contracts_closed_by_schema"]
        != ["subject-temporal-public-v1", "aemh-match-history-public-v1"]
        or overlay["authority_rule"]
        != "The overlay freezes future producer requirements. It does not change existing R5 files and does not claim either module/path currently exists."
        or overlay["unlock_rule"] != expected_unlock
        or replacements != expected_replacements
    ):
        issues.append("PUB_OVERLAY_ARTIFACT_MISMATCH")
    return sorted(set(issues))


def source_matrix_validation_issues(matrix: dict[str, Any]) -> list[str]:
    expected_root_keys = {
        "schema",
        "contract_id",
        "exact_entry_order_and_content",
        "entries",
        "classification_vocabulary",
        "producer_requirement_contract",
        "global_rule",
    }
    expected_producers = [
        {
            "contract_id": "aemh-match-history-public-v1",
            "packet_source": (
                "aemh_match_history_public:AEMHMatchHistoryAuthorityPacket"
            ),
            "projection_source": (
                "aemh_match_history_public:AEMHMatchHistoryPublicProjection"
            ),
            "receipt_variant": "aemh_match_history",
            "implementation_status": "contract_only_not_implemented",
        },
        {
            "contract_id": "subject-temporal-public-v1",
            "packet_source": (
                "subject_temporal_public:SubjectTemporalAuthorityPacket"
            ),
            "projection_source": (
                "subject_temporal_public:SubjectTemporalPublicProjection"
            ),
            "receipt_variant": "subject_temporal",
            "implementation_status": "contract_only_not_implemented",
        },
    ]
    if (
        set(matrix) != expected_root_keys
        or matrix["schema"]
        != "medical-monitoring-r5-s5-public-authority-source-matrix-v0.1"
        or matrix["contract_id"]
        != "medical-monitoring-r5-s5-public-authority-contract-v0.1"
        or matrix["exact_entry_order_and_content"] is not True
        or matrix["producer_requirement_contract"] != expected_producers
        or canonical_hash(matrix)
        != EXPECTED_SOURCE_MATRIX_CANONICAL_SHA256
    ):
        return ["PUB_SOURCE_MATRIX_ARTIFACT_MISMATCH"]
    return []


def verify_overlay_and_matrix(
    overlay: dict[str, Any], matrix: dict[str, Any], parent: dict[str, Any]
) -> None:
    overlay_issues = overlay_validation_issues(overlay, parent)
    if overlay_issues:
        fail(f"exact overlay deferred mapping coverage mismatch: {overlay_issues}")
    matrix_issues = source_matrix_validation_issues(matrix)
    if matrix_issues:
        fail(f"exact source matrix mismatch: {matrix_issues}")


def verify_no_runtime_test_surface(manifest: dict[str, Any]) -> None:
    surface = manifest["no_runtime_test_surface"]
    if surface != EXPECTED_NO_RUNTIME_TEST_SURFACE:
        fail("no-runtime/no-test surface contract drift")
    patterns = [
        re.compile(pattern)
        for pattern in surface["forbidden_relative_path_regexes"]
    ]
    hits: set[str] = set()
    for relative in surface["forbidden_exact_paths"]:
        candidate = ROOT / relative
        if candidate.exists() or candidate.is_symlink():
            hits.add(relative)
    for root_relative in surface["scan_roots"]:
        root = ROOT / root_relative
        if not root.is_dir():
            fail(f"no-runtime/no-test scan root missing: {root_relative}")
        for candidate in root.rglob("*"):
            if not (candidate.is_file() or candidate.is_symlink()):
                continue
            relative = candidate.relative_to(ROOT).as_posix()
            if any(pattern.fullmatch(relative) for pattern in patterns):
                hits.add(relative)
    if hits:
        fail(
            "PUB_RUNTIME_TEST_SURFACE_FORBIDDEN: forbidden public-authority "
            f"runtime/test surface exists: {sorted(hits)}"
        )


def verify_port_8911_stopped() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        result = sock.connect_ex(("127.0.0.1", 8911))
    if result == 0:
        fail("port 8911 has a listener")


def main() -> int:
    generator = load_generator()
    verify_no_python_assert_statements()
    verify_generator_reproducibility(generator)
    manifest = verify_manifest()
    verify_source_pins(manifest)
    subject_schema_doc = read_json(
        "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/subject_temporal_schema.json"
    )
    aemh_schema_doc = read_json(
        "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/aemh_match_history_schema.json"
    )
    verify_schema_descriptor(subject_schema_doc, "subject-temporal-public-v1-exact-schema")
    verify_schema_descriptor(aemh_schema_doc, "aemh-match-history-public-v1-exact-schema")
    inputs = read_json(
        "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/base_inputs.json"
    )
    for base_key in (
        "subject_temporal_valid_base",
        "subject_temporal_absent_cutoff_valid_base",
        "subject_temporal_conflicted_valid_base",
        "subject_temporal_no_study_day_valid_base",
    ):
        subject_issues = validate_subject(inputs[base_key], subject_schema_doc)
        if subject_issues:
            fail(f"valid subject-temporal base rejected: {base_key}: {subject_issues}")
    previous_aemh_issues = validate_aemh(
        inputs["aemh_match_history_previous_base"], aemh_schema_doc
    )
    if previous_aemh_issues:
        fail(f"valid previous AE/MH base rejected: {previous_aemh_issues}")
    aemh_issues = validate_aemh(
        inputs["aemh_match_history_valid_base"],
        aemh_schema_doc,
        inputs["aemh_match_history_previous_base"],
    )
    if aemh_issues:
        fail(f"valid AE/MH base rejected: {aemh_issues}")
    parent = read_json("artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json")
    registry = read_json(
        "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/challenge_registry.json"
    )
    executed_tamper_gates = verify_challenges(
        registry, parent, subject_schema_doc, aemh_schema_doc, inputs
    )
    overlay = read_json(
        "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/exact_overlay.json"
    )
    matrix = read_json(
        "artifacts/medical_monitoring_r5_s5_public_authority_contract_v0_1/source_matrix.json"
    )
    verify_overlay_and_matrix(overlay, matrix, parent)
    verify_no_runtime_test_surface(manifest)
    verify_port_8911_stopped()
    print(
        "PUBLIC_AUTHORITY_CONTRACT_VERIFY_OK "
        f"artifacts={len(ALLOWLIST)} inherited_cases=64 "
        f"tamper_gates={executed_tamper_gates} optimized={not __debug__} "
        "runtime_test_surface=absent port_8911=stopped"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
