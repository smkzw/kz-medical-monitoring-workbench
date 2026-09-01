#!/usr/bin/env python3
"""Verify the renderer-neutral R5-S6 contract and its offline challenges.

This verifier is deliberately self-contained and read-only.  It checks the
worker-01 contract bytes, the S6-owned challenge/quota artifacts, exact
navigation/accessibility/performance vocabulary, and the protected boundary.
It does not import a product runtime, browser, service, model, or project.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import socket
import stat
import sys
from collections import Counter
from typing import Any, Callable


sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1"
EXACT = ARTIFACT_DIR / "exact_contract.json"
SCHEMA = ARTIFACT_DIR / "navigation_schema.json"
ENCODING = ARTIFACT_DIR / "audience_encoding_registry.json"
PERFORMANCE = ARTIFACT_DIR / "performance_corpus_registry.json"
MANIFEST = ARTIFACT_DIR / "manifest.json"
CHALLENGE = ARTIFACT_DIR / "challenge_registry.json"
QUOTA = ARTIFACT_DIR / "quota_ledger.json"

CONTRACT_ID = "medical-monitoring-r5-s6-navigation-density-accessibility-contract-v0.1"
SCHEMA_VERSION = "2026-08-26.1"
EXPECTED_CHALLENGE_ROWS = 104
ACCEPTANCE_TOKEN = "ACCEPT_R5_S6_NAVIGATION_DENSITY_ACCESSIBILITY_CONTRACT"

IDENTITY_FIELDS = [
    "target_kind", "project_ref", "run_ref", "snapshot_ref", "cutoff_state", "cutoff_ref",
    "site_ref", "subject_ref", "risk_ref", "spine_ref", "view", "axis_mode", "window_start",
    "window_end", "visit_ref", "event_ref", "risk_anchor_ref", "source_locator_ref",
    "target_projection_content_hash", "return_context_key", "fallback_policy",
]
CANONICAL_FIELDS = [
    "deep_link_identity", "filter_state", "sort_state", "page_state", "selection_anchor",
    "semantic_zoom_state", "axis_mode", "window_start", "window_end",
]
EPHEMERAL_FIELDS = [
    "scroll_refs", "inspector_width", "inspector_expanded", "temporary_expansion_refs", "focus_ref",
]
REGION_ORDER = ["risk_list", "center_map", "inspector", "workspace", "temporal_spine", "source_drawer"]

DOMAIN_ITEMS = [
    {"domain": "ae", "short_label_zh": "AE", "event_shape": "rounded_rect", "line_style": "solid", "subtypes": ["ae"]},
    {"domain": "mh", "short_label_zh": "MH", "event_shape": "bookmark", "line_style": "dot_dash", "subtypes": ["mh"]},
    {"domain": "cm", "short_label_zh": "合并用药", "event_shape": "capsule", "line_style": "solid", "subtypes": ["concomitant_medication"]},
    {"domain": "ip", "short_label_zh": "试验药", "event_shape": "hexagon", "line_style": "step", "subtypes": ["ip_dose", "ip_pause", "ip_resume"]},
    {"domain": "lab_exam", "short_label_zh": "检验/检查", "event_shape": "square", "line_style": "trend", "subtypes": ["lab", "exam"]},
    {"domain": "hospital_procedure", "short_label_zh": "住院/操作", "event_shape": "doorframe", "line_style": "solid", "subtypes": ["hospitalization", "procedure"]},
    {"domain": "symptom_efficacy", "short_label_zh": "症状/疗效", "event_shape": "circle", "line_style": "trend", "subtypes": ["symptom", "efficacy", "scale", "outcome", "trend"]},
    {"domain": "protocol_compliance", "short_label_zh": "方案符合", "event_shape": "single_flag", "line_style": "bracket", "subtypes": ["protocol_deviation"]},
]
SEVERITY_ITEMS = [
    {"severity": "critical", "label_zh": "紧急"},
    {"severity": "high", "label_zh": "高"},
    {"severity": "medium", "label_zh": "中"},
    {"severity": "low", "label_zh": "低"},
]
FORBIDDEN_TERMS = ["已记录事项", "正式事实", "候选信号", "通用风险点", "只读xx", "Checklist", "待行动", "未读"]

CATEGORY_COUNTS = {
    "deep_link_identity": 21,
    "deep_link_no_nearest_fallback": 5,
    "canonical_return_context": 18,
    "density_semantic_zoom": 14,
    "keyboard_non_mutating": 16,
    "non_colour_encoding": 11,
    "performance_corpus_identity": 13,
    "protected_boundary": 6,
}

EXPECTED_PROJECTION_BY_CATEGORY = {
    "deep_link_identity": "not_emitted",
    "deep_link_no_nearest_fallback": "not_emitted",
    "canonical_return_context": "not_restored",
    "density_semantic_zoom": "not_emitted",
    "keyboard_non_mutating": "not_emitted",
    "non_colour_encoding": "not_emitted",
    "performance_corpus_identity": "not_emitted",
    "protected_boundary": "not_emitted",
}

EXPECTED_INPUT_RAW_SHA = {
    "artifacts/medical_monitoring_r5_contract_v0_3/exact_contract.json": "3cdd1641f0660cf49593c56a1dad8b66370603321e28b5ecf6de4a91fb057949",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/challenge_registry.json": "e5143edda759685fccedd9c696429454f2e1924175171d89f7c3948e5d61f00c",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json": "5b674b16159295052afb56a0736dc8fc87a6070a0ea5524a2b8bfc7850d29cac",
    "artifacts/medical_monitoring_r5_s5_subject_workspace_contract_v0_1/manifest.json": "868815c74b4fb4ee33eb738d9de0f20c3148e9339f56a18745b0afccb32a34d8",
    "context/medical_monitoring_r5_contract_acceptance_record_20260818.md": "c086a19772be498b560a7fea6b5eab5b6e897283b1cd87ff3f139b823e79e6f2",
    "context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_20260826_context.md": "3d5410c85d3ab2426bd599c228f5d58b910ec719ea9970f4bb51bed0a6ae6327",
    "context/medical_monitoring_r5_s5_subject_workspace_contract_v0_1_acceptance_record_20260826.md": "fed3ae96d95aa43bb6eda3fe2df175371c5fe3d7a4654818316294eec4b82f52",
    "context/medical_monitoring_r5_s5_subject_workspace_runtime_v0_1_acceptance_record_20260826.md": "6f623c4b285cbf003f06e3378deb69583b14ceb1ef0a30b404518c7588e995d1",
    "context/medical_monitoring_r5_s5_subject_workspace_runtime_v0_1_pause_20260826.md": "729457382123e368b9f38c955f5668d3b43925f184f0a400e4839a879e39c899",
    "reviews/medical_monitoring_r5_stage_contract_v0_3_20260818.md": "1d2f2531584ad55b5e788636839add8248026e28a24460f0a85387e2bb72a0c6",
}

EXPECTED_OWNED_RAW_SHA = {
    "artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/audience_encoding_registry.json": "817f58fbcdd5e764a22f64513d45343b1d284f2dc6799fb3d82128865c2d20ac",
    "artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/exact_contract.json": "220fedabe7b3c6b191a49ccee04718918740a384daff2a5ee2bcaf5c1c9150aa",
    "artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/navigation_schema.json": "fac69d3e9485d501ed9331b38b6ecea266c00c89c52977a8b2d1b3d5efddf466",
    "artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/performance_corpus_registry.json": "72e78c388510b30853603ca35c2e29d10cd8c5de63a0e80f43fa54b0eccd81fe",
    "context/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1_20260826_context.md": "a9f25f6764863166f7db8229867a2dbbe193e586391b1c586071219908272cc7",
    "reviews/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1_20260826.md": "a72bfd80019e8c441f4401bfe5523fa09418607bc04bcf4967867b89651b4373",
    "scripts/generate_medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1.py": "9cc9cc2508096b2e4dea39176fadb06bd1a09d2d2f12edbf448282c8734915d3",
}
EXPECTED_S6_CONTENT_SHA = {
    "contract": "ba083b9a60b09560a045ef03ce7df73196467e2473ba19a9e8c7ff747ec6f4ec",
    "schema": "5a2e58fd7a2f4f37ce66fe58ce43522d7ef833802e140b10477b62d2081b3cf6",
    "audience_encoding": "16e22812c22380eba16dfb3cfa3a0d610a52db0d7e84cf2843bee70a1e68f247",
    "performance_corpus": "d36719fe3766125e1550faba54cc6cae7a88ebd81ac6baa76c48fd75b58be9e7",
}

MEDICAL_WRITING_ROOTS = ("deploy", "frontend", "packages", "runtime", "services")
MEDICAL_WRITING_PATTERN = re.compile(r"medical[-_]writing")
MEDICAL_WRITING_COUNT = 542
MEDICAL_WRITING_AGGREGATE_SHA256 = "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca"
MEDICAL_WRITING_ALGORITHM_SOURCE = "reviews/medical_monitoring_r5_s5_public_authority_contract_v0_1_20260819.md"
EXPECTED_VALIDATION_PATH_ORDER = (
    "artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/challenge_registry.json",
    "artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1/quota_ledger.json",
    "scripts/test_medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1.py",
    "scripts/verify_medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1.py",
)
VALIDATION_PATHS = frozenset(EXPECTED_VALIDATION_PATH_ORDER)
EXPECTED_FUTURE_RUNTIME_PATH_ORDER = (
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_contracts.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_navigation.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_accessibility.py",
    "poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/s6_runtime_fixtures.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s6_contracts.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s6_navigation.py",
    "poc/medical_monitoring_ai_native_r5/tests/test_s6_validator.py",
    "poc/medical_monitoring_ai_native_r5/tests/challenges/test_s6_runtime_challenges.py",
    "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s6_navigation_readonly_sha256.json",
)
FUTURE_RUNTIME_PATHS = frozenset(EXPECTED_FUTURE_RUNTIME_PATH_ORDER)


class VerificationFailure(RuntimeError):
    """Raised after all deterministic checks have been collected."""

    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("\n".join(issues))


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def content_digest(value: Any, excluded_key: str) -> str:
    if not isinstance(value, dict):
        raise TypeError("content digest requires an object")
    payload = {key: item for key, item in value.items() if key != excluded_key}
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def raw_digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path, issues: list[str], label: str) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(f"MISSING_FILE:{label}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issues.append(f"INVALID_JSON:{label}:{type(exc).__name__}")
        return None
    if not isinstance(value, dict):
        issues.append(f"ROOT_NOT_OBJECT:{label}")
        return None
    return value


def check(issues: list[str], condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        issues.append(code if not detail else f"{code}:{detail}")


def check_equal(issues: list[str], actual: Any, expected: Any, code: str, detail: str = "") -> None:
    check(issues, actual == expected, code, detail or f"actual={actual!r};expected={expected!r}")


def check_raw_map(issues: list[str], expected: dict[str, str]) -> None:
    for relative, expected_sha in sorted(expected.items()):
        path = ROOT / relative
        if not path.exists():
            issues.append(f"MISSING_PINNED_FILE:{relative}")
            continue
        observed = raw_digest(path)
        check_equal(issues, observed, expected_sha, "RAW_SHA_MISMATCH", relative)


def recompute_medical_writing_boundary() -> dict[str, Any]:
    """Rebuild the frozen medical-writing inventory from workspace bytes.

    The relative path is workspace-relative (including its protected root),
    matching the frozen aggregate identity.  ``Path.stat`` and ``read_bytes``
    intentionally follow a task-scoped symlink to a regular file.
    """
    matched_hashes: dict[str, str] = {}
    errors: list[str] = []
    for root_relative in MEDICAL_WRITING_ROOTS:
        root = ROOT / root_relative
        if not root.is_dir():
            errors.append(f"MISSING_MEDICAL_WRITING_ROOT:{root_relative}")
            continue
        for directory, directory_names, file_names in os.walk(root, topdown=True, followlinks=False):
            directory_names.sort()
            file_names.sort()
            for filename in file_names:
                path = pathlib.Path(directory) / filename
                relative = path.relative_to(ROOT).as_posix()
                if MEDICAL_WRITING_PATTERN.search(relative) is None:
                    continue
                try:
                    mode = path.stat().st_mode
                except OSError as exc:
                    errors.append(f"MEDICAL_WRITING_STAT_ERROR:{relative}:{type(exc).__name__}")
                    continue
                if not stat.S_ISREG(mode):
                    continue
                try:
                    matched_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest().lower()
                except (OSError, UnicodeError) as exc:
                    errors.append(f"MEDICAL_WRITING_READ_ERROR:{relative}:{type(exc).__name__}")
    aggregate = hashlib.sha256()
    for relative in sorted(matched_hashes, key=lambda value: value.encode("utf-8")):
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(matched_hashes[relative].encode("ascii"))
        aggregate.update(b"\n")
    return {
        "roots": list(MEDICAL_WRITING_ROOTS),
        "relative_path_regex": MEDICAL_WRITING_PATTERN.pattern,
        "file_count": len(matched_hashes),
        "aggregate_sha256": aggregate.hexdigest(),
        "errors": errors,
    }


def recompute_manifest_input_pins(manifest: dict[str, Any]) -> dict[str, Any]:
    """Rehash every accepted input path named by the S6 manifest."""
    declared = manifest.get("input_raw_sha256")
    if not isinstance(declared, dict):
        return {"declared": declared, "observed": {}, "errors": ["MANIFEST_INPUT_PINS_NOT_OBJECT"]}
    observed: dict[str, str] = {}
    errors: list[str] = []
    for relative, declared_sha in sorted(declared.items()):
        if not isinstance(relative, str) or pathlib.PurePosixPath(relative).is_absolute() or ".." in pathlib.PurePosixPath(relative).parts:
            errors.append(f"MANIFEST_INPUT_PATH_INVALID:{relative!r}")
            continue
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"MISSING_MANIFEST_INPUT:{relative}")
            continue
        try:
            observed_sha = raw_digest(path)
        except (OSError, UnicodeError) as exc:
            errors.append(f"MANIFEST_INPUT_READ_ERROR:{relative}:{type(exc).__name__}")
            continue
        observed[relative] = observed_sha
        if observed_sha != declared_sha:
            errors.append(f"MANIFEST_INPUT_PIN_DRIFT:{relative}")
    return {
        "declared": dict(sorted(declared.items())),
        "observed": dict(sorted(observed.items())),
        "errors": errors,
    }


def verify_medical_writing_and_inputs(manifest: dict[str, Any], issues: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    boundary = recompute_medical_writing_boundary()
    for error in boundary["errors"]:
        issues.append(error)
    check_equal(issues, boundary["file_count"], MEDICAL_WRITING_COUNT, "MEDICAL_WRITING_FILE_COUNT_MISMATCH")
    check_equal(issues, boundary["aggregate_sha256"], MEDICAL_WRITING_AGGREGATE_SHA256, "MEDICAL_WRITING_INVENTORY_MISMATCH")
    protected = manifest.get("protected_boundaries", {})
    check_equal(issues, protected.get("medical_writing_file_count"), boundary["file_count"], "MANIFEST_MEDICAL_WRITING_COUNT_MISMATCH")
    check_equal(issues, protected.get("medical_writing_inventory_sha256"), boundary["aggregate_sha256"], "MANIFEST_MEDICAL_WRITING_INVENTORY_MISMATCH")

    pins = recompute_manifest_input_pins(manifest)
    for error in pins["errors"]:
        issues.append(error)
    check_equal(issues, pins["declared"], dict(sorted(EXPECTED_INPUT_RAW_SHA.items())), "MANIFEST_INPUT_SHA_MAP_MISMATCH")
    check_equal(issues, pins["observed"], pins["declared"], "MANIFEST_INPUT_PIN_RECOMPUTE_MISMATCH")
    return boundary, pins


def verify_manifest_file_hashes(manifest: dict[str, Any], issues: list[str]) -> None:
    declared = manifest.get("file_raw_sha256")
    check(issues, isinstance(declared, dict), "MANIFEST_FILE_SHA_MAP_NOT_OBJECT")
    if not isinstance(declared, dict):
        return
    allowed = set(EXPECTED_OWNED_RAW_SHA) | set(VALIDATION_PATHS)
    check(issues, set(declared).issubset(allowed), "MANIFEST_FILE_SHA_SCOPE_MISMATCH")
    for relative, expected_sha in EXPECTED_OWNED_RAW_SHA.items():
        check_equal(issues, declared.get(relative), expected_sha, "MANIFEST_IMMUTABLE_FILE_SHA_MISMATCH", relative)
    for relative, declared_sha in sorted(declared.items()):
        if relative not in allowed:
            continue
        path = ROOT / relative
        if not path.is_file():
            issues.append(f"MISSING_MANIFEST_FILE_SHA_TARGET:{relative}")
            continue
        check_equal(issues, raw_digest(path), declared_sha, "MANIFEST_FILE_SHA_RECOMPUTE_MISMATCH", relative)


def verify_future_runtime_allowlist(manifest: dict[str, Any], issues: list[str]) -> None:
    check(issues, "future_validation_allowlist" not in manifest, "LEGACY_VALIDATION_ALLOWLIST_PRESENT")
    allowlist = manifest.get("future_runtime_allowlist")
    check(issues, isinstance(allowlist, list), "FUTURE_RUNTIME_ALLOWLIST_NOT_LIST")
    if not isinstance(allowlist, list):
        return
    actual_paths = [item.get("path") for item in allowlist if isinstance(item, dict)]
    check_equal(issues, actual_paths, list(EXPECTED_FUTURE_RUNTIME_PATH_ORDER), "FUTURE_RUNTIME_PATH_ORDER_OR_SCOPE_MISMATCH")
    for relative in EXPECTED_FUTURE_RUNTIME_PATH_ORDER:
        check(issues, not os.path.lexists(ROOT / relative), "FUTURE_RUNTIME_PATH_PRESENT", relative)
    for item in allowlist:
        check(issues, isinstance(item, dict), "FUTURE_RUNTIME_ROW_INVALID")
        if not isinstance(item, dict):
            continue
        path = str(item.get("path"))
        check_equal(issues, item.get("present"), False, "FUTURE_RUNTIME_PRESENT_FLAG", path)
        check_equal(issues, item.get("create_only"), True, "FUTURE_RUNTIME_CREATE_ONLY", path)
        check_equal(issues, item.get("kind"), "synthetic_offline_renderer_neutral_runtime_or_test", "FUTURE_RUNTIME_KIND", path)
        check_equal(issues, item.get("medical_writing"), False, "FUTURE_RUNTIME_MEDICAL_WRITING_SCOPE", path)
        check_equal(issues, item.get("runtime"), True, "FUTURE_RUNTIME_RUNTIME_SCOPE", path)
        check_equal(issues, item.get("browser"), False, "FUTURE_RUNTIME_BROWSER_SCOPE", path)
        check_equal(issues, item.get("real_project_or_model"), False, "FUTURE_RUNTIME_REAL_SCOPE", path)
        check_equal(issues, item.get("starts_8911"), False, "FUTURE_RUNTIME_8911_SCOPE", path)
        check_equal(issues, item.get("allowed_only_after"), ACCEPTANCE_TOKEN, "FUTURE_RUNTIME_STAGE", path)


def port_is_listening(port: int = 8911) -> bool:
    for family, address in ((socket.AF_INET, ("127.0.0.1", port)), (socket.AF_INET6, ("::1", port))):
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(0.15)
        try:
            if sock.connect_ex(address) == 0:
                return True
        finally:
            sock.close()
    return False


def expected_keyboard_bindings() -> list[dict[str, Any]]:
    rows = [
        ("Tab", "focus_next_region", "global", False),
        ("Shift+Tab", "focus_previous_region", "global", False),
        ("Enter", "activate_focused_target", "global", True),
        ("Space", "toggle_focused_control", "global", True),
        ("Escape", "close_ephemeral_surface", "global", True),
        ("ArrowUp", "move_previous", "risk_list", True),
        ("ArrowDown", "move_next", "risk_list", True),
        ("ArrowUp", "move_previous", "center_map", True),
        ("ArrowDown", "move_next", "center_map", True),
        ("ArrowLeft", "move_previous", "temporal_spine", True),
        ("ArrowRight", "move_next", "temporal_spine", True),
        ("Home", "focus_first", "workspace", True),
        ("End", "focus_last", "workspace", True),
        ("+", "semantic_zoom_in", "temporal_spine", True),
        ("-", "semantic_zoom_out", "temporal_spine", True),
        ("0", "semantic_zoom_reset", "temporal_spine", True),
    ]
    return [
        {
            "key": key,
            "action": action,
            "scope": scope,
            "prevent_default": prevent_default,
            "medical_state_mutation": False,
        }
        for key, action, scope, prevent_default in rows
    ]


def verify_contract(exact: dict[str, Any], schema: dict[str, Any], encoding: dict[str, Any], performance: dict[str, Any], manifest: dict[str, Any], issues: list[str]) -> None:
    check_equal(issues, exact.get("contract_id"), CONTRACT_ID, "CONTRACT_ID_MISMATCH", "exact")
    check_equal(issues, exact.get("schema_version"), SCHEMA_VERSION, "SCHEMA_VERSION_MISMATCH", "exact")
    check_equal(issues, exact.get("renderer_neutral"), True, "RENDERER_NEUTRAL_REQUIRED")
    check_equal(issues, exact.get("contract_only"), True, "CONTRACT_ONLY_REQUIRED")
    check_equal(issues, schema.get("contract_id"), CONTRACT_ID, "CONTRACT_ID_MISMATCH", "schema")
    check_equal(issues, schema.get("schema_version"), SCHEMA_VERSION, "SCHEMA_VERSION_MISMATCH", "schema")
    check_equal(issues, encoding.get("contract_id"), CONTRACT_ID, "CONTRACT_ID_MISMATCH", "encoding")
    check_equal(issues, performance.get("contract_id"), CONTRACT_ID, "CONTRACT_ID_MISMATCH", "performance")

    check_equal(issues, schema.get("content_hash"), content_digest(schema, "content_hash"), "SCHEMA_CONTENT_HASH_MISMATCH")
    check_equal(issues, encoding.get("content_hash"), content_digest(encoding, "content_hash"), "ENCODING_CONTENT_HASH_MISMATCH")
    check_equal(issues, performance.get("content_hash"), content_digest(performance, "content_hash"), "PERFORMANCE_CONTENT_HASH_MISMATCH")
    check_equal(issues, exact.get("contract_content_hash"), content_digest(exact, "contract_content_hash"), "CONTRACT_CONTENT_HASH_MISMATCH")
    check_equal(issues, schema.get("content_hash"), EXPECTED_S6_CONTENT_SHA["schema"], "SCHEMA_CONTENT_PIN_MISMATCH")
    check_equal(issues, encoding.get("content_hash"), EXPECTED_S6_CONTENT_SHA["audience_encoding"], "ENCODING_CONTENT_PIN_MISMATCH")
    check_equal(issues, performance.get("content_hash"), EXPECTED_S6_CONTENT_SHA["performance_corpus"], "PERFORMANCE_CONTENT_PIN_MISMATCH")
    check_equal(issues, exact.get("contract_content_hash"), EXPECTED_S6_CONTENT_SHA["contract"], "CONTRACT_CONTENT_PIN_MISMATCH")

    deep_link = exact.get("deep_link_contract", {})
    check_equal(issues, deep_link.get("identity_fields"), IDENTITY_FIELDS, "DEEP_LINK_IDENTITY_FIELD_SET_MISMATCH")
    check_equal(issues, deep_link.get("fallback_policy"), "none", "DEEP_LINK_FALLBACK_NOT_NONE")
    check_equal(issues, deep_link.get("failure_outcome"), "not_emitted", "DEEP_LINK_FAILURE_OUTCOME_MISMATCH")
    check(issues, "NEAREST_FALLBACK_FORBIDDEN" in deep_link.get("failure_codes", []), "DEEP_LINK_NEAREST_CODE_MISSING")
    check(issues, "target content hash" in deep_link.get("exact_target_rule", ""), "DEEP_LINK_HASH_CHECK_MISSING")
    check(issues, "no empty string" in deep_link.get("cutoff_absent_rule", ""), "DEEP_LINK_CUTOFF_ABSENCE_RULE_MISSING")

    return_contract = exact.get("return_context_contract", {})
    check_equal(issues, return_contract.get("canonical_fields"), CANONICAL_FIELDS, "CANONICAL_FIELD_SET_MISMATCH")
    check_equal(issues, return_contract.get("ephemeral_fields"), EPHEMERAL_FIELDS, "EPHEMERAL_FIELD_SET_MISMATCH")
    check_equal(issues, return_contract.get("url_byte_identity_required"), False, "URL_BYTE_IDENTITY_MUST_BE_FALSE")
    check_equal(issues, return_contract.get("canonical_equivalence_required"), True, "CANONICAL_EQUIVALENCE_REQUIRED")
    check_equal(issues, return_contract.get("medical_state_mutation"), False, "RETURN_CONTEXT_MEDICAL_MUTATION")
    check_equal(issues, return_contract.get("failure_outcome"), "not_restored", "RETURN_FAILURE_OUTCOME_MISMATCH")
    check(issues, "NEAREST_FALLBACK_FORBIDDEN" in return_contract.get("failure_codes", []), "RETURN_NEAREST_CODE_MISSING")
    check_equal(issues, schema.get("canonical_state_fields"), CANONICAL_FIELDS, "SCHEMA_CANONICAL_FIELDS_MISMATCH")
    check_equal(issues, schema.get("ephemeral_state_fields"), EPHEMERAL_FIELDS, "SCHEMA_EPHEMERAL_FIELDS_MISMATCH")

    density = exact.get("density_and_zoom_contract", {})
    check_equal(issues, density.get("desktop_min_viewport"), [1440, 900], "DESKTOP_MIN_VIEWPORT_MISMATCH")
    check_equal(issues, sorted(density.get("density_modes", {})), ["high", "standard"], "DENSITY_MODE_SET_MISMATCH")
    check(issues, "never hide" in density.get("density_modes", {}).get("high", ""), "HIGH_DENSITY_HIDING_RULE_MISSING")
    expected_zoom = {
        "overview": {
            "aggregation_policy": "low_risk_by_domain_window",
            "risk_visibility_policy": "all_critical_high_medium",
            "source_locator_policy": "risk_only",
            "content_omission_policy": "low_risk_only",
        },
        "detail": {
            "aggregation_policy": "none",
            "risk_visibility_policy": "all_critical_high_medium",
            "source_locator_policy": "event_and_risk",
            "content_omission_policy": "none",
        },
        "evidence": {
            "aggregation_policy": "none_source_expanded",
            "risk_visibility_policy": "all_projectable",
            "source_locator_policy": "all_projectable",
            "content_omission_policy": "none",
        },
    }
    actual_zoom = density.get("semantic_zoom_levels", {})
    check_equal(issues, sorted(actual_zoom), ["detail", "evidence", "overview"], "SEMANTIC_ZOOM_LEVEL_SET_MISMATCH")
    for level, expected in expected_zoom.items():
        check_equal(issues, actual_zoom.get(level), expected, "SEMANTIC_ZOOM_POLICY_MISMATCH", level)
    check_equal(issues, density.get("invariants"), [
        "all critical/high/medium risk anchors remain individually represented at every semantic zoom level",
        "overview aggregation is limited to low-risk ordinary events within one domain and time window",
        "detail and evidence do not aggregate events or risk anchors",
        "semantic zoom changes representation, not identity, membership, authority or canonical return state",
        "density changes spacing only and cannot be used as an omission or fallback mechanism",
    ], "DENSITY_INVARIANTS_MISMATCH")

    keyboard = exact.get("keyboard_contract", {})
    check_equal(issues, keyboard.get("region_order"), REGION_ORDER, "KEYBOARD_REGION_ORDER_MISMATCH")
    check_equal(issues, keyboard.get("bindings"), expected_keyboard_bindings(), "KEYBOARD_BINDINGS_MISMATCH")
    check(issues, "hidden or non-projectable targets are not focusable" in keyboard.get("focus_policy", ""), "KEYBOARD_FOCUS_CLOSURE_MISSING")
    check(issues, "no key creates, edits, closes or regrades medical state" in keyboard.get("selection_policy", ""), "KEYBOARD_NON_MUTATION_POLICY_MISSING")
    check(issues, all(item.get("medical_state_mutation") is False for item in keyboard.get("bindings", [])), "KEYBOARD_MEDICAL_STATE_MUTATION")

    check_equal(issues, encoding.get("domain_items"), DOMAIN_ITEMS, "DOMAIN_ENCODING_MISMATCH")
    check_equal(issues, encoding.get("severity_items"), SEVERITY_ITEMS, "SEVERITY_ENCODING_MISMATCH")
    check_equal(issues, encoding.get("event_forbidden_shapes"), ["double_chevron_badge"], "EVENT_RISK_SHAPE_COLLISION")
    check_equal(issues, encoding.get("forbidden_terms"), FORBIDDEN_TERMS, "FORBIDDEN_TERM_REGISTRY_MISMATCH")
    check_equal(issues, encoding.get("risk_overlay"), {
        "shape": "double_chevron_badge",
        "outer_ring": True,
        "text_pattern": "{domain_short_label}·{severity_zh}",
        "colour_only": False,
    }, "RISK_OVERLAY_ENCODING_MISMATCH")
    severity_rules = encoding.get("severity_rules", {})
    check_equal(issues, severity_rules.get("critical_authority_required"), True, "CRITICAL_AUTHORITY_RULE_MISSING")
    check_equal(issues, severity_rules.get("high_must_not_promote_to_critical"), True, "HIGH_PROMOTION_RULE_MISSING")
    check_equal(issues, severity_rules.get("unmapped_legacy_value"), "fail_closed", "LEGACY_SEVERITY_FAIL_CLOSED_MISSING")
    domain_rules = encoding.get("domain_rules", {})
    check_equal(issues, domain_rules.get("exact_domain_count"), 8, "DOMAIN_COUNT_MISMATCH")
    check_equal(issues, domain_rules.get("other_domain"), "forbidden", "OTHER_DOMAIN_NOT_FORBIDDEN")
    check_equal(issues, domain_rules.get("unknown_domain"), "fail_closed_to_domain_confirmation_surface", "UNKNOWN_DOMAIN_NOT_FAIL_CLOSED")

    corpus = performance.get("corpus", {})
    check_equal(issues, corpus.get("corpus_id"), "r5-s6-offline-density-performance-corpus-v0.1", "PERFORMANCE_CORPUS_ID_MISMATCH")
    check_equal(issues, corpus.get("schema_version"), SCHEMA_VERSION, "PERFORMANCE_CORPUS_SCHEMA_MISMATCH")
    check_equal(issues, corpus.get("event_count"), 1000, "PERFORMANCE_EVENT_COUNT_MISMATCH")
    check_equal(issues, corpus.get("indicator_count"), 40, "PERFORMANCE_INDICATOR_COUNT_MISMATCH")
    check_equal(issues, corpus.get("risk_anchor_count"), 300, "PERFORMANCE_RISK_ANCHOR_COUNT_MISMATCH")
    check_equal(issues, corpus.get("record_order"), ["event", "indicator", "risk_anchor"], "PERFORMANCE_RECORD_ORDER_MISMATCH")
    check_equal(issues, corpus.get("content_hash"), content_digest(corpus, "content_hash"), "PERFORMANCE_CORPUS_HASH_MISMATCH")
    check_equal(issues, performance.get("modes"), ["cold", "warm"], "PERFORMANCE_MODE_SET_MISMATCH")
    check_equal(issues, performance.get("samples_per_mode"), 7, "PERFORMANCE_SAMPLE_COUNT_MISMATCH")
    check_equal(issues, performance.get("latency_statistic"), "p95_nearest_rank", "PERFORMANCE_LATENCY_STATISTIC_MISMATCH")
    check_equal(issues, performance.get("fps_statistic"), "p05_nearest_rank", "PERFORMANCE_FPS_STATISTIC_MISMATCH")
    check_equal(issues, performance.get("result_state"), "unmeasured_contract_only", "PERFORMANCE_RESULT_PREMATURE")
    offline = performance.get("offline_boundary", {})
    check_equal(issues, offline.get("synthetic_only"), True, "PERFORMANCE_SYNTHETIC_BOUNDARY_MISSING")
    check_equal(issues, offline.get("real_project"), False, "PERFORMANCE_REAL_PROJECT_BOUNDARY")
    check_equal(issues, offline.get("real_model"), False, "PERFORMANCE_REAL_MODEL_BOUNDARY")
    check_equal(issues, offline.get("starts_8911"), False, "PERFORMANCE_8911_BOUNDARY")
    check_equal(issues, offline.get("browser_acceptance"), "S7_only", "PERFORMANCE_BROWSER_STAGE_MISMATCH")
    check_equal(issues, performance.get("thresholds"), {
        "brush_zoom_select_ms_p95": 100,
        "cold_interactive_ms_p95": 2500,
        "pan_fps_p05": 30,
        "warm_interactive_ms_p95": 1500,
    }, "PERFORMANCE_THRESHOLD_MISMATCH")

    check_equal(issues, manifest.get("contract_id"), CONTRACT_ID, "MANIFEST_CONTRACT_ID_MISMATCH")
    check_equal(issues, manifest.get("schema_version"), SCHEMA_VERSION, "MANIFEST_SCHEMA_VERSION_MISMATCH")
    check_equal(issues, manifest.get("status"), "candidate_unaccepted", "MANIFEST_STATUS_NOT_CANDIDATE")
    check_equal(issues, manifest.get("self_acceptance"), False, "SELF_ACCEPTANCE_FORBIDDEN")
    check_equal(issues, manifest.get("acceptance_token_emitted"), False, "ACCEPTANCE_TOKEN_EMITTED")
    check_equal(issues, manifest.get("acceptance_token"), ACCEPTANCE_TOKEN, "ACCEPTANCE_TOKEN_ID_MISMATCH")
    check_equal(issues, manifest.get("contract_content_hash"), EXPECTED_S6_CONTENT_SHA["contract"], "MANIFEST_CONTRACT_HASH_MISMATCH")
    check_equal(issues, manifest.get("schema_content_hash"), EXPECTED_S6_CONTENT_SHA["schema"], "MANIFEST_SCHEMA_HASH_MISMATCH")
    check_equal(issues, manifest.get("audience_encoding_content_hash"), EXPECTED_S6_CONTENT_SHA["audience_encoding"], "MANIFEST_ENCODING_HASH_MISMATCH")
    check_equal(issues, manifest.get("performance_corpus_content_hash"), EXPECTED_S6_CONTENT_SHA["performance_corpus"], "MANIFEST_PERFORMANCE_HASH_MISMATCH")
    check_equal(issues, manifest.get("manifest_content_hash"), content_digest(manifest, "manifest_content_hash"), "MANIFEST_CONTENT_HASH_MISMATCH")
    protected = manifest.get("protected_boundaries", {})
    check_equal(issues, protected, {
        "port_8911": "stopped_required",
        "medical_writing_file_count": 542,
        "medical_writing_inventory_sha256": "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca",
        "accepted_r1_r5_inputs_immutable": True,
        "production_paths_written": False,
    }, "PROTECTED_BOUNDARY_MANIFEST_MISMATCH")
    freeze = exact.get("contract_freeze_validation", {})
    expected_validation_paths = freeze.get("artifact_paths", [])
    check(issues, isinstance(expected_validation_paths, list), "VALIDATION_PATH_DECLARATION_INVALID")
    check_equal(issues, expected_validation_paths, list(EXPECTED_VALIDATION_PATH_ORDER), "VALIDATION_CONTRACT_PATHS_MISMATCH")
    validation_rows = manifest.get("contract_freeze_validation_artifacts")
    file_sha_map = manifest.get("file_raw_sha256", {})
    check(issues, isinstance(validation_rows, list), "VALIDATION_ARTIFACT_ROWS_INVALID")
    if isinstance(expected_validation_paths, list) and isinstance(validation_rows, list):
        actual_validation_paths = [item.get("path") for item in validation_rows if isinstance(item, dict)]
        check_equal(issues, actual_validation_paths, expected_validation_paths, "VALIDATION_PATH_ORDER_OR_SCOPE_MISMATCH")
        raw_sha_map = manifest.get("contract_freeze_validation_raw_sha256")
        expected_raw_sha_map = {
            path: file_sha_map.get(path) for path in expected_validation_paths
        } if isinstance(file_sha_map, dict) else {}
        check_equal(issues, raw_sha_map, expected_raw_sha_map, "VALIDATION_RAW_SHA_MAP_MISMATCH")
    for item in validation_rows if isinstance(validation_rows, list) else []:
        check(issues, isinstance(item, dict), "VALIDATION_ARTIFACT_ROW_INVALID")
        if not isinstance(item, dict):
            continue
        path = str(item.get("path"))
        check_equal(
            issues,
            item.get("raw_sha256"),
            file_sha_map.get(path) if isinstance(file_sha_map, dict) else None,
            "VALIDATION_ROW_RAW_SHA_MISMATCH",
            path,
        )
        check_equal(issues, item.get("binding"), "raw_bytes_sha256", "VALIDATION_BINDING_MISMATCH", path)
        check_equal(issues, item.get("present"), True, "VALIDATION_PRESENT_MISMATCH", path)
        check_equal(issues, item.get("medical_writing"), False, "VALIDATION_MEDICAL_WRITING_SCOPE", path)
        check_equal(issues, item.get("runtime"), False, "VALIDATION_RUNTIME_SCOPE", path)
        check_equal(issues, item.get("browser"), False, "VALIDATION_BROWSER_SCOPE", path)
        check_equal(issues, item.get("real_project_or_model"), False, "VALIDATION_REAL_SCOPE", path)
        check_equal(issues, item.get("starts_8911"), False, "VALIDATION_8911_SCOPE", path)
        check_equal(issues, item.get("role"), "worker_02_final_contract_freeze_evidence", "VALIDATION_ROLE_MISMATCH", path)

    counts = manifest.get("counts", {})
    check_equal(issues, counts.get("contract_freeze_validation_paths"), 4, "MANIFEST_VALIDATION_PATH_COUNT")
    check_equal(issues, counts.get("future_runtime_allowlist_paths"), 10, "MANIFEST_FUTURE_RUNTIME_PATH_COUNT")
    check_equal(issues, counts.get("upstream_input_pins"), 10, "MANIFEST_INPUT_PIN_COUNT")
    check_equal(issues, manifest.get("binding_graph"), {
        "exact_contract": "semantic_requirements_and_validation_paths_only",
        "manifest": "raw_bytes_for_exact_quota_challenge_verifier_tests_and_all_other_present_owned_artifacts",
        "manifest_self_raw_hash": "excluded",
        "quota": "references_exact_contract.contract_content_hash",
    }, "MANIFEST_BINDING_GRAPH_MISMATCH")
    verify_future_runtime_allowlist(manifest, issues)
    check_raw_map(issues, EXPECTED_OWNED_RAW_SHA)
    verify_manifest_file_hashes(manifest, issues)


def expected_challenge_paths() -> dict[str, set[str]]:
    return {
        "deep_link_identity": {f"/candidate/deep_link_identity/{field}" for field in IDENTITY_FIELDS},
        "deep_link_no_nearest_fallback": {
            "/candidate/deep_link_identity/project_ref",
            "/candidate/deep_link_identity/target_projection_content_hash",
            "/candidate/deep_link_identity/risk_anchor_ref",
            "/candidate/deep_link_identity/subject_ref",
            "/candidate/deep_link_identity/event_ref",
        },
        "canonical_return_context": {
            "/candidate/return_context/canonical/deep_link_identity",
            "/candidate/return_context/canonical/filter_state",
            "/candidate/return_context/canonical/sort_state",
            "/candidate/return_context/canonical/page_state",
            "/candidate/return_context/canonical/selection_anchor",
            "/candidate/return_context/canonical/semantic_zoom_state",
            "/candidate/return_context/canonical/axis_mode",
            "/candidate/return_context/canonical/window_start",
            "/candidate/return_context/canonical/window_end",
            "/candidate/return_context/canonical/canonical_state_hash",
            "/candidate/return_context/return_context_key",
            "/candidate/return_context/canonical/selection_anchor/selected_event_ref",
            "/candidate/return_context/canonical/deep_link_identity/subject_ref",
            "/candidate/return_context/ephemeral/scroll_refs",
            "/candidate/return_context/ephemeral/inspector_width",
            "/candidate/return_context/ephemeral/inspector_expanded",
            "/candidate/return_context/ephemeral/temporary_expansion_refs",
            "/candidate/return_context/ephemeral/focus_ref",
        },
        "density_semantic_zoom": {
            "/candidate/density_semantic_zoom/density_modes/standard",
            "/candidate/density_semantic_zoom/density_modes/high",
            *{
                f"/candidate/density_semantic_zoom/semantic_zoom_levels/{level}/{policy}"
                for level in ("overview", "detail", "evidence")
                for policy in ("aggregation_policy", "risk_visibility_policy", "source_locator_policy", "content_omission_policy")
            },
        },
        "keyboard_non_mutating": {f"/candidate/keyboard_contract/bindings/{index}/medical_state_mutation" for index in range(16)},
        "non_colour_encoding": {
            *{f"/candidate/audience_encoding/domain_items/{index}/event_shape" for index in range(8)},
            "/candidate/audience_encoding/risk_overlay/shape",
            "/candidate/audience_encoding/risk_overlay/colour_only",
            "/candidate/audience_encoding/risk_overlay/text_pattern",
        },
        "performance_corpus_identity": {
            "/candidate/performance/corpus/event_count",
            "/candidate/performance/corpus/indicator_count",
            "/candidate/performance/corpus/risk_anchor_count",
            "/candidate/performance/corpus/corpus_id",
            "/candidate/performance/corpus/schema_version",
            "/candidate/performance/corpus/record_order",
            "/candidate/performance/corpus/content_hash",
            "/candidate/performance/modes",
            "/candidate/performance/samples_per_mode",
            "/candidate/performance/latency_statistic",
            "/candidate/performance/fps_statistic",
            "/candidate/performance/result_state",
            "/candidate/performance/offline_boundary/starts_8911",
        },
        "protected_boundary": {
            "/candidate/protected_boundaries/port_8911",
            "/candidate/protected_boundaries/medical_writing_file_count",
            "/candidate/protected_boundaries/medical_writing_inventory_sha256",
            "/candidate/protected_boundaries/accepted_r1_r5_inputs_immutable",
            "/candidate/protected_boundaries/production_paths_written",
            "/candidate/manifest/acceptance_token_emitted",
        },
    }


def expected_challenge_oracles() -> dict[tuple[str, str], tuple[str, str]]:
    """Return the independent error/rule oracle for every mutation path."""
    paths = expected_challenge_paths()
    oracles: dict[tuple[str, str], tuple[str, str]] = {}
    for path in paths["deep_link_identity"]:
        error = "NEAREST_FALLBACK_FORBIDDEN" if path.endswith("/fallback_policy") else "DEEP_LINK_IDENTITY_MISMATCH"
        rule = "deep_link_no_nearest_fallback" if error == "NEAREST_FALLBACK_FORBIDDEN" else "deep_link_identity_exact"
        oracles[("deep_link_identity", path)] = (error, rule)
    oracles.update({
        ("deep_link_no_nearest_fallback", "/candidate/deep_link_identity/project_ref"): ("DEEP_LINK_TARGET_NOT_PROJECTABLE", "deep_link_no_nearest_fallback"),
        ("deep_link_no_nearest_fallback", "/candidate/deep_link_identity/target_projection_content_hash"): ("DEEP_LINK_ARTIFACT_MISSING", "deep_link_no_nearest_fallback"),
        ("deep_link_no_nearest_fallback", "/candidate/deep_link_identity/risk_anchor_ref"): ("DEEP_LINK_ANCHOR_NOT_MEMBER", "deep_link_no_nearest_fallback"),
        ("deep_link_no_nearest_fallback", "/candidate/deep_link_identity/subject_ref"): ("NEAREST_FALLBACK_FORBIDDEN", "deep_link_no_nearest_fallback"),
        ("deep_link_no_nearest_fallback", "/candidate/deep_link_identity/event_ref"): ("DEEP_LINK_TARGET_NOT_PROJECTABLE", "deep_link_no_nearest_fallback"),
    })
    canonical_oracles = {
        "/candidate/return_context/canonical/deep_link_identity": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/filter_state": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/sort_state": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/page_state": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/selection_anchor": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/semantic_zoom_state": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/axis_mode": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/window_start": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/window_end": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/canonical_state_hash": ("CANONICAL_STATE_HASH_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/return_context_key": ("RETURN_CONTEXT_KEY_MISMATCH", "canonical_return_exact"),
        "/candidate/return_context/canonical/selection_anchor/selected_event_ref": ("RETURN_ANCHOR_NOT_MEMBER", "canonical_return_exact"),
        "/candidate/return_context/canonical/deep_link_identity/subject_ref": ("NEAREST_FALLBACK_FORBIDDEN", "canonical_return_no_nearest_fallback"),
        "/candidate/return_context/ephemeral/scroll_refs": ("EPHEMERAL_STATE_IN_CANONICAL_HASH", "ephemeral_return_separate"),
        "/candidate/return_context/ephemeral/inspector_width": ("EPHEMERAL_STATE_IN_CANONICAL_HASH", "ephemeral_return_separate"),
        "/candidate/return_context/ephemeral/inspector_expanded": ("EPHEMERAL_STATE_IN_CANONICAL_HASH", "ephemeral_return_separate"),
        "/candidate/return_context/ephemeral/temporary_expansion_refs": ("EPHEMERAL_STATE_IN_CANONICAL_HASH", "ephemeral_return_separate"),
        "/candidate/return_context/ephemeral/focus_ref": ("EPHEMERAL_STATE_IN_CANONICAL_HASH", "ephemeral_return_separate"),
    }
    oracles.update({("canonical_return_context", path): oracle for path, oracle in canonical_oracles.items()})
    for path in paths["density_semantic_zoom"]:
        error = "DENSITY_REQUIRED_RISK_HIDDEN" if path.endswith("/density_modes/standard") or path.endswith("/density_modes/high") else "SEMANTIC_ZOOM_POLICY_MISMATCH"
        rule = "density_no_omission" if error == "DENSITY_REQUIRED_RISK_HIDDEN" else "semantic_zoom_closed"
        oracles[("density_semantic_zoom", path)] = (error, rule)
    for path in paths["keyboard_non_mutating"]:
        oracles[("keyboard_non_mutating", path)] = ("KEYBOARD_MEDICAL_STATE_MUTATION", "keyboard_non_mutating")
    for path in paths["non_colour_encoding"]:
        oracles[("non_colour_encoding", path)] = ("NON_COLOUR_ENCODING_INCOMPLETE", "non_colour_encoding_complete")
    for path in paths["performance_corpus_identity"]:
        error = "PROTECTED_BOUNDARY_DRIFT" if path.endswith("/offline_boundary/starts_8911") else "PERFORMANCE_RESULT_PREMATURE" if path.endswith("/result_state") else "PERFORMANCE_CORPUS_IDENTITY_MISMATCH"
        rule = "protected_boundary" if error == "PROTECTED_BOUNDARY_DRIFT" else "performance_unmeasured_until_runtime" if error == "PERFORMANCE_RESULT_PREMATURE" else "performance_corpus_exact" if path.endswith("/corpus/" + path.rsplit("/", 1)[-1]) else "performance_profile_exact"
        oracles[("performance_corpus_identity", path)] = (error, rule)
    for path in paths["protected_boundary"]:
        oracles[("protected_boundary", path)] = ("PROTECTED_BOUNDARY_DRIFT", "protected_boundary")
    return oracles


def verify_challenges(registry: dict[str, Any], quota: dict[str, Any], exact: dict[str, Any], issues: list[str]) -> Counter[str]:
    check_equal(issues, registry.get("contract_id"), CONTRACT_ID, "CHALLENGE_CONTRACT_ID_MISMATCH")
    check_equal(issues, registry.get("schema_version"), SCHEMA_VERSION, "CHALLENGE_SCHEMA_VERSION_MISMATCH")
    check_equal(issues, registry.get("status"), "metadata_only", "CHALLENGE_RUNTIME_SCOPE")
    check_equal(issues, registry.get("registry_content_hash"), content_digest(registry, "registry_content_hash"), "CHALLENGE_REGISTRY_HASH_MISMATCH")
    check_equal(issues, registry.get("row_count"), EXPECTED_CHALLENGE_ROWS, "CHALLENGE_ROW_COUNT_DECLARATION")
    check_equal(issues, registry.get("category_counts"), CATEGORY_COUNTS, "CHALLENGE_CATEGORY_QUOTA_DECLARATION")
    check_equal(issues, registry.get("authority_source_forbidden"), [
        "fixture_text", "fixture_count", "case_id", "filename", "unbound_hash", "nearest_record", "ui_state", "candidate_output",
    ], "CHALLENGE_FORBIDDEN_AUTHORITY_SET_MISMATCH")
    row_contract = registry.get("row_contract", {})
    check_equal(issues, row_contract.get("single_mutation_required"), ["op", "path", "value"], "CHALLENGE_MUTATION_SHAPE_MISMATCH")
    check_equal(issues, row_contract.get("expected_projection_by_category"), EXPECTED_PROJECTION_BY_CATEGORY, "CHALLENGE_PROJECTION_CONTRACT_MISMATCH")
    check_equal(issues, row_contract.get("placeholder_mutations_forbidden"), True, "CHALLENGE_PLACEHOLDER_MUTATIONS_ALLOWED")
    check_equal(issues, row_contract.get("required_non_llm_anchor"), "python-stdlib-deterministic-verifier", "CHALLENGE_ANCHOR_MISMATCH")
    check_equal(issues, row_contract.get("test_locator"), "scripts/test_medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1.py::TestS6Contract::test_challenge_registry", "CHALLENGE_TEST_LOCATOR_MISMATCH")

    rows = registry.get("rows", [])
    check(issues, isinstance(rows, list), "CHALLENGE_ROWS_NOT_LIST")
    if not isinstance(rows, list):
        return Counter()
    check_equal(issues, len(rows), EXPECTED_CHALLENGE_ROWS, "CHALLENGE_ROW_COUNT")
    ids = [row.get("challenge_id") for row in rows if isinstance(row, dict)]
    check_equal(issues, ids, [f"S6C-{index:03d}" for index in range(1, EXPECTED_CHALLENGE_ROWS + 1)], "CHALLENGE_ID_SEQUENCE")
    check_equal(issues, len(set(ids)), EXPECTED_CHALLENGE_ROWS, "CHALLENGE_ID_DUPLICATE")

    expected_paths = expected_challenge_paths()
    expected_oracles = expected_challenge_oracles()
    category_paths: dict[str, set[str]] = {category: set() for category in CATEGORY_COUNTS}
    allowed_errors = {
        "deep_link_identity": {"DEEP_LINK_IDENTITY_MISMATCH", "NEAREST_FALLBACK_FORBIDDEN"},
        "deep_link_no_nearest_fallback": {"DEEP_LINK_TARGET_NOT_PROJECTABLE", "DEEP_LINK_ARTIFACT_MISSING", "DEEP_LINK_ANCHOR_NOT_MEMBER", "NEAREST_FALLBACK_FORBIDDEN"},
        "canonical_return_context": {"CANONICAL_STATE_HASH_MISMATCH", "RETURN_CONTEXT_KEY_MISMATCH", "RETURN_ANCHOR_NOT_MEMBER", "NEAREST_FALLBACK_FORBIDDEN", "EPHEMERAL_STATE_IN_CANONICAL_HASH"},
        "density_semantic_zoom": {"DENSITY_REQUIRED_RISK_HIDDEN", "SEMANTIC_ZOOM_POLICY_MISMATCH"},
        "keyboard_non_mutating": {"KEYBOARD_MEDICAL_STATE_MUTATION"},
        "non_colour_encoding": {"NON_COLOUR_ENCODING_INCOMPLETE"},
        "performance_corpus_identity": {"PERFORMANCE_CORPUS_IDENTITY_MISMATCH", "PERFORMANCE_RESULT_PREMATURE", "PROTECTED_BOUNDARY_DRIFT"},
        "protected_boundary": {"PROTECTED_BOUNDARY_DRIFT"},
    }
    for row in rows:
        if not isinstance(row, dict):
            issues.append("CHALLENGE_ROW_NOT_OBJECT")
            continue
        for key in row_contract.get("required_fields", []):
            check(issues, key in row, "CHALLENGE_REQUIRED_FIELD_MISSING", f"{row.get('challenge_id')}:{key}")
        category = row.get("category")
        path = row.get("single_mutation", {}).get("path") if isinstance(row.get("single_mutation"), dict) else None
        if category in category_paths and isinstance(path, str):
            category_paths[category].add(path)
        check(issues, category in CATEGORY_COUNTS, "CHALLENGE_UNKNOWN_CATEGORY", str(category))
        mutation = row.get("single_mutation")
        if not isinstance(mutation, dict):
            issues.append(f"CHALLENGE_MUTATION_NOT_OBJECT:{row.get('challenge_id')}")
            continue
        check_equal(issues, set(mutation), {"op", "path", "value"}, "CHALLENGE_MUTATION_KEYS", str(row.get("challenge_id")))
        check_equal(issues, mutation.get("op"), "replace", "CHALLENGE_MUTATION_OP", str(row.get("challenge_id")))
        check(issues, isinstance(path, str) and re.fullmatch(r"/[A-Za-z0-9_./\[\]-]+", path) is not None, "CHALLENGE_MUTATION_PATH", str(row.get("challenge_id")))
        check(issues, row.get("baseline_value") != mutation.get("value"), "CHALLENGE_MUTATION_IS_NOOP", str(row.get("challenge_id")))
        check(issues, row.get("test_metadata_only") is True, "CHALLENGE_RUNTIME_TEST_SCOPE", str(row.get("challenge_id")))
        check(issues, isinstance(row.get("target"), str) and bool(row.get("target")), "CHALLENGE_TARGET_MISSING", str(row.get("challenge_id")))
        check_equal(issues, row.get("expected_projection"), EXPECTED_PROJECTION_BY_CATEGORY.get(category), "CHALLENGE_EXPECTED_PROJECTION", str(row.get("challenge_id")))
        expected_error = row.get("expected_error")
        check(issues, expected_error in allowed_errors.get(category, set()), "CHALLENGE_EXPECTED_ERROR", f"{row.get('challenge_id')}:{expected_error}")
        expected_oracle = expected_oracles.get((category, path))
        check(issues, expected_oracle is not None, "CHALLENGE_ORACLE_PATH_MISSING", f"{category}:{path}")
        if expected_oracle is not None:
            check_equal(issues, (expected_error, row.get("rule_id")), expected_oracle, "CHALLENGE_ORACLE_MISMATCH", str(row.get("challenge_id")))
        check_equal(issues, row.get("expected_outcome"), f"reject:{expected_error}", "CHALLENGE_OUTCOME_ERROR_MISMATCH", str(row.get("challenge_id")))
        check(issues, isinstance(row.get("rule_id"), str) and bool(row.get("rule_id")), "CHALLENGE_RULE_ID_MISSING", str(row.get("challenge_id")))
        serialized = json.dumps(row, ensure_ascii=False, sort_keys=True)
        for forbidden in ("mutated::", "placeholder", "nearest_record", "fixture_text", "fixture_count", "candidate_output"):
            check(issues, forbidden not in serialized, "CHALLENGE_FORBIDDEN_PLACEHOLDER", f"{row.get('challenge_id')}:{forbidden}")

    for category, expected in expected_paths.items():
        check_equal(issues, category_paths.get(category), expected, "CHALLENGE_PATH_COVERAGE_MISMATCH", category)
    counts = Counter(row.get("category") for row in rows if isinstance(row, dict))
    check_equal(issues, dict(counts), CATEGORY_COUNTS, "CHALLENGE_CATEGORY_COUNTS")

    check_equal(issues, quota.get("contract_id"), CONTRACT_ID, "QUOTA_CONTRACT_ID_MISMATCH")
    check_equal(issues, quota.get("schema_version"), SCHEMA_VERSION, "QUOTA_SCHEMA_VERSION_MISMATCH")
    check_equal(issues, quota.get("contract_content_hash"), exact.get("contract_content_hash"), "QUOTA_CONTRACT_HASH_MISMATCH")
    check_equal(issues, quota.get("registry_content_hash"), registry.get("registry_content_hash"), "QUOTA_REGISTRY_HASH_MISMATCH")
    check_equal(issues, quota.get("category_quotas"), {
        "deep_link_identity": {"required": 21, "coverage_rule": "all 21 exact deep-link identity fields, one replacement each"},
        "deep_link_no_nearest_fallback": {"required": 5, "coverage_rule": "target-not-projectable, artifact-missing, anchor-not-member and adjacent-target rejection paths"},
        "canonical_return_context": {"required": 18, "coverage_rule": "all 9 canonical fields, canonical hash, return key, membership, nearest fallback and all 5 ephemeral fields"},
        "density_semantic_zoom": {"required": 14, "coverage_rule": "standard/high density plus all four policies at overview/detail/evidence"},
        "keyboard_non_mutating": {"required": 16, "coverage_rule": "every frozen keyboard binding has one medical_state_mutation=true challenge"},
        "non_colour_encoding": {"required": 11, "coverage_rule": "all 8 domain event-shape distinctions plus risk overlay shape/colour/text safeguards"},
        "performance_corpus_identity": {"required": 13, "coverage_rule": "1000/40/300 counts, corpus identity, sampling/statistics, unmeasured state and offline boundary"},
        "protected_boundary": {"required": 6, "coverage_rule": "8911, medical-writing inventory, accepted inputs, production writes and token emission"},
    }, "QUOTA_DEFINITION_MISMATCH")
    check_equal(issues, quota.get("expected_total"), EXPECTED_CHALLENGE_ROWS, "QUOTA_TOTAL_MISMATCH")
    check_equal(issues, quota.get("instance_count"), EXPECTED_CHALLENGE_ROWS, "QUOTA_INSTANCE_COUNT_MISMATCH")
    check_equal(issues, quota.get("ledger_content_hash"), content_digest(quota, "ledger_content_hash"), "QUOTA_LEDGER_HASH_MISMATCH")
    return counts


def verify(*, port_probe: Callable[[], bool] | None = None) -> dict[str, Any]:
    issues: list[str] = []
    check_raw_map(issues, EXPECTED_OWNED_RAW_SHA)
    exact = read_json(EXACT, issues, "exact_contract")
    schema = read_json(SCHEMA, issues, "navigation_schema")
    encoding = read_json(ENCODING, issues, "audience_encoding_registry")
    performance = read_json(PERFORMANCE, issues, "performance_corpus_registry")
    manifest = read_json(MANIFEST, issues, "manifest")
    registry = read_json(CHALLENGE, issues, "challenge_registry")
    quota = read_json(QUOTA, issues, "quota_ledger")
    if all(isinstance(item, dict) for item in (exact, schema, encoding, performance, manifest)):
        verify_contract(exact, schema, encoding, performance, manifest, issues)
        boundary, input_pins = verify_medical_writing_and_inputs(manifest, issues)
    else:
        boundary = {"file_count": 0, "aggregate_sha256": "", "errors": []}
        input_pins = {"declared": {}, "observed": {}, "errors": []}
    counts = Counter()
    if all(isinstance(item, dict) for item in (registry, quota, exact)):
        counts = verify_challenges(registry, quota, exact, issues)
    # The real TCP probe is mandatory. The optional seam is additive only: it
    # can model an observed listener for deterministic regression coverage, but
    # it cannot replace or suppress enforcement of the real 8911 check.
    try:
        actual_port_observation = port_is_listening()
    except Exception as exc:
        issues.append(f"PORT_8911_OBSERVATION_ERROR:{type(exc).__name__}")
        actual_port_observation = None

    injected_port_observation = None
    if port_probe is not None:
        try:
            injected_port_observation = port_probe()
        except Exception as exc:
            issues.append(f"PORT_8911_OBSERVATION_ERROR:{type(exc).__name__}")

    if actual_port_observation is True or injected_port_observation is True:
        issues.append("PORT_8911_LISTENING")
    elif actual_port_observation is not False:
        issues.append("PORT_8911_OBSERVATION_INVALID")
    elif port_probe is not None and injected_port_observation is not False:
        issues.append("PORT_8911_OBSERVATION_INVALID")
    if issues:
        raise VerificationFailure(issues)
    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "challenge_rows": EXPECTED_CHALLENGE_ROWS,
        "category_counts": dict(sorted(counts.items())),
        "deep_link_identity_fields": len(IDENTITY_FIELDS),
        "canonical_return_fields": len(CANONICAL_FIELDS),
        "ephemeral_return_fields": len(EPHEMERAL_FIELDS),
        "keyboard_bindings": 16,
        "domain_encoding_items": 8,
        "performance_dataset": {"events": 1000, "indicators": 40, "risk_anchors": 300},
        "performance_result_state": "unmeasured_contract_only",
        "port_8911": "stopped",
        "medical_writing_file_count": boundary["file_count"],
        "medical_writing_inventory_sha256": boundary["aggregate_sha256"],
        "accepted_input_pin_count": len(input_pins["observed"]),
        "runtime_started": False,
        "browser_exercised": False,
        "real_project_or_model": False,
    }


def main() -> int:
    try:
        summary = verify()
    except VerificationFailure as exc:
        print("S6_VERIFY_FAILED")
        for issue in exc.issues:
            print(issue)
        return 1
    print("S6_VERIFY_OK " + json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
