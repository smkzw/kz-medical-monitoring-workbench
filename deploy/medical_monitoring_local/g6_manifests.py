#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R8 G6 frozen manifest loaders and fail-closed validators.

The three JSON manifests in this directory are technical evidence.  They are
not user-facing configuration and must never be replaced with values observed
from a running page.  This module keeps validation deterministic and usable by
both the actual-app entry point and offline focused tests.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

try:  # direct execution from the deployment directory
    from canonical_evidence import canonical_json_bytes, digest_ref
except ImportError:  # pragma: no cover - package-style import support
    from .canonical_evidence import canonical_json_bytes, digest_ref


MANIFEST_VERSION = "1"
CONTRACT_VERSION = "medical_monitoring_r8_gate6_synthetic_ego_v0.2"
ENTRY_SCHEMA = "mm-monitoring-r8-g6-entry-manifest-v1"
BOUNDARY_SCHEMA = "mm-monitoring-r8-g6-execution-boundary-manifest-v1"
VIEWPORT_SCHEMA = "mm-monitoring-r8-g6-viewport-layout-manifest-v1"
APP_SCHEMA = "mm-monitoring-r8-g6-actual-app-v1"
SYNTHETIC_PROFILE_ID = "synthetic-profile-cross-domain-g6-v1"
SYNTHETIC_PROFILE_BINDING_DIGEST = (
    "sha256:80baa7f09edc2af53f1afe731721dd094e4b2277a0090ee61d6063a366623578"
)
SYNTHETIC_FIXTURE_DIGEST = (
    "sha256:1aae22caf46c4609453f53529a34e3d0e6ff4660c774cacfcee37308bf33b2e7"
)
SYNTHETIC_DEFAULT_RUN_BINDING_DIGEST = (
    "sha256:3af2b05db7def6ca461a6579bd86a11687dcf33611f7749617b7b6e45cf211f4"
)
SYNTHETIC_BUNDLE_DIGEST = (
    "sha256:2ec92ea99d0a146200cc8cddf999b6ed8083b2eec6edba186b529c4ee2edc8a2"
)
SYNTHETIC_TASK_SPEC_DIGEST = (
    "sha256:db3a742f4e1fcc8398a698d4177f63f0b49e17341c21ad68aa089aec6a94f488a"
)
SYNTHETIC_RUN_BINDING_COUNT = 6
SYNTHETIC_ENTRY_ROUTE = "/?g6=synthetic"
SYNTHETIC_ADAPTER_ID = "g6-mock-recorded-adapter"


ENTRY_MANIFEST_NAME = "entry_manifest.json"
EXECUTION_BOUNDARY_MANIFEST_NAME = "execution_boundary_manifest.json"
VIEWPORT_LAYOUT_MANIFEST_NAME = "viewport_layout_manifest.json"

_MANIFEST_NAMES = (
    ENTRY_MANIFEST_NAME,
    EXECUTION_BOUNDARY_MANIFEST_NAME,
    VIEWPORT_LAYOUT_MANIFEST_NAME,
)


class ManifestError(ValueError):
    """Raised whenever a frozen G6 manifest cannot be trusted."""


def _as_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"{field}_must_be_object")
    return value


def _as_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field}_must_be_non_empty_string")
    return value


def _as_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ManifestError(f"{field}_must_be_positive_integer")
    return value


def _as_non_negative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ManifestError(f"{field}_must_be_non_negative_integer")
    return value


def _digest_file(path: Path) -> str:
    hasher = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
    except OSError as exc:
        raise ManifestError(f"file_unreadable:{path.name}") from exc
    return "sha256:" + hasher.hexdigest()


def _relative_path(value: Any, field: str) -> str:
    raw = _as_non_empty_string(value, field).replace("\\", "/")
    if raw.startswith("/") or raw.startswith("~"):
        raise ManifestError(f"{field}_must_be_relative")
    parts = [part for part in raw.split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raise ManifestError(f"{field}_unsafe")
    return "/".join(parts)


def _manifest_digest(payload: Mapping[str, Any]) -> str:
    expected = payload.get("manifest_digest")
    if not isinstance(expected, str) or not expected.startswith("sha256:"):
        raise ManifestError("manifest_digest_missing")
    body = {key: value for key, value in payload.items() if key != "manifest_digest"}
    actual = digest_ref(body)
    if expected != actual:
        raise ManifestError("manifest_digest_mismatch")
    return expected


def _common(payload: Mapping[str, Any], schema: str) -> None:
    if payload.get("schema") != schema:
        raise ManifestError("schema_mismatch")
    if payload.get("manifest_version") != MANIFEST_VERSION:
        raise ManifestError("manifest_version_mismatch")
    if payload.get("contract_version") != CONTRACT_VERSION:
        raise ManifestError("contract_version_mismatch")
    _manifest_digest(payload)


def _resolve_under(root: Path, relative: str, field: str) -> Path:
    base = root.expanduser().resolve()
    target = (base / relative).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ManifestError(f"{field}_escapes_release_root") from exc
    return target


def validate_entry_manifest(
    payload: Mapping[str, Any], *, release_root: Optional[Path] = None
) -> Dict[str, Any]:
    """Validate entry identity and, when supplied, its on-disk bundle."""

    value = dict(_as_mapping(payload, "entry_manifest"))
    _common(value, ENTRY_SCHEMA)
    if value.get("product_name") != "医学监查工作台":
        raise ManifestError("product_name_mismatch")

    release = _as_mapping(value.get("release_root"), "release_root")
    if release.get("relative_path") != ".":
        raise ManifestError("release_root_must_be_bundle_root")
    entry = _as_mapping(value.get("entry"), "entry")
    if entry.get("type") != "macos_application_bundle":
        raise ManifestError("entry_type_mismatch")
    bundle_relative = _relative_path(entry.get("relative_path"), "entry.relative_path")
    executable_relative = _relative_path(
        entry.get("executable_relative_path"), "entry.executable_relative_path"
    )
    if not bundle_relative.endswith(".app"):
        raise ManifestError("entry_bundle_suffix_mismatch")
    if not executable_relative.startswith(bundle_relative + "/Contents/MacOS/"):
        raise ManifestError("entry_executable_must_be_macos_bundle_path")
    static_relative = _relative_path(
        entry.get("static_root_relative_path"), "entry.static_root_relative_path"
    )
    if entry.get("entry_url") != SYNTHETIC_ENTRY_ROUTE:
        raise ManifestError("entry_url_mismatch")
    if entry.get("static_root_required") is not True:
        raise ManifestError("static_root_required")
    if not isinstance(entry.get("bundle_identifier"), str) or not entry["bundle_identifier"].startswith(
        "com."
    ):
        raise ManifestError("bundle_identifier_invalid")
    if not isinstance(entry.get("file_digest"), str) or not entry["file_digest"].startswith("sha256:"):
        raise ManifestError("entry_file_digest_missing")
    if not isinstance(entry.get("directory_digest"), str) or not entry["directory_digest"].startswith("sha256:"):
        raise ManifestError("entry_directory_digest_missing")
    if not isinstance(value.get("app_digest"), str) or not value["app_digest"].startswith("sha256:"):
        raise ManifestError("app_digest_missing")
    if value["app_digest"] != entry.get("directory_digest"):
        raise ManifestError("app_digest_mismatch")
    if not isinstance(value.get("release_digest"), str) or not value["release_digest"].startswith("sha256:"):
        raise ManifestError("release_digest_missing")
    release_files = value.get("release_files")
    if not isinstance(release_files, list) or not release_files:
        raise ManifestError("release_files_missing")
    release_rows = []
    seen_release_paths = set()
    for index, item in enumerate(release_files):
        row = _as_mapping(item, f"release_files[{index}]")
        relative = _relative_path(row.get("path"), f"release_files[{index}].path")
        if relative in _MANIFEST_NAMES:
            raise ManifestError("release_files_must_exclude_manifest")
        if relative in seen_release_paths:
            raise ManifestError("release_files_duplicate")
        seen_release_paths.add(relative)
        file_digest = _as_non_empty_string(row.get("sha256"), f"release_files[{index}].sha256")
        if not file_digest.startswith("sha256:"):
            raise ManifestError("release_file_digest_invalid")
        release_rows.append({"path": relative, "sha256": file_digest})
    if digest_ref(release_rows) != value["release_digest"]:
        raise ManifestError("release_digest_mismatch")
    if release_root is not None:
        root = release_root.expanduser().resolve()
        for row in release_rows:
            target = _resolve_under(root, row["path"], "release_files.path")
            if not target.is_file() or _digest_file(target) != row["sha256"]:
                raise ManifestError("release_file_digest_mismatch")

    protocol = _as_mapping(value.get("protocol"), "protocol")
    _as_non_empty_string(protocol.get("version"), "protocol.version")
    _as_non_empty_string(protocol.get("ready_signal"), "protocol.ready_signal")
    _as_non_empty_string(protocol.get("failure_signal"), "protocol.failure_signal")
    window = _as_mapping(value.get("window_identity"), "window_identity")
    if window.get("kind") not in {"browser_window", "desktop_window"}:
        raise ManifestError("window_identity_kind_invalid")
    _as_non_empty_string(window.get("title"), "window_identity.title")
    _as_non_empty_string(window.get("identity"), "window_identity.identity")

    process = _as_mapping(value.get("owned_process_tree"), "owned_process_tree")
    processes = process.get("processes")
    if not isinstance(processes, list) or not processes:
        raise ManifestError("owned_process_tree_empty")
    names = []
    for index, item in enumerate(processes):
        row = _as_mapping(item, f"owned_process_tree.processes[{index}]")
        names.append(_as_non_empty_string(row.get("name"), f"process[{index}].name"))
        if row.get("role") not in {"app", "http_server", "browser_window"}:
            raise ManifestError(f"process[{index}].role_invalid")
        if row.get("role") == "app":
            if row.get("executable_relative_path") != executable_relative:
                raise ManifestError("process_identity_path_mismatch")
            if row.get("argv_contains") != "actual_app.py --launch":
                raise ManifestError("process_identity_argv_mismatch")
    if len(names) != len(set(names)):
        raise ManifestError("owned_process_tree_duplicate")
    if process.get("unknown_process_policy") != "fail_closed":
        raise ManifestError("unknown_process_policy_mismatch")

    if release_root is not None:
        root = release_root.expanduser().resolve()
        bundle = _resolve_under(root, bundle_relative, "entry.relative_path")
        executable = _resolve_under(root, executable_relative, "entry.executable_relative_path")
        if not bundle.is_dir() or not executable.is_file():
            raise ManifestError("entry_artifact_missing")
        if not os.access(executable, os.X_OK):
            raise ManifestError("entry_artifact_not_executable")
        if _digest_file(executable) != entry["file_digest"]:
            raise ManifestError("entry_file_digest_mismatch")
        expected_directory = value.get("entry", {}).get("directory_digest")
        if expected_directory != digest_directory(bundle):
            raise ManifestError("entry_directory_digest_mismatch")
    return value


def validate_execution_boundary_manifest(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate the closed roots/process/network/adapter execution set."""

    value = dict(_as_mapping(payload, "execution_boundary_manifest"))
    _common(value, BOUNDARY_SCHEMA)
    if value.get("synthetic_only") is not True:
        raise ManifestError("synthetic_only_required")
    roots = _as_mapping(value.get("allowed_roots"), "allowed_roots")
    required_roots = {"release_root", "fixture_root", "system_temp_runtime_root", "application_data_root"}
    if set(roots) != required_roots:
        raise ManifestError("allowed_roots_shape_mismatch")
    for name in sorted(required_roots):
        row = _as_mapping(roots[name], f"allowed_roots.{name}")
        if row.get("kind") not in {"release", "workspace_relative", "system_temp", "os_application_data"}:
            raise ManifestError(f"allowed_roots.{name}.kind_invalid")
        if row.get("access") not in {"read_only", "read_write"}:
            raise ManifestError(f"allowed_roots.{name}.access_invalid")
        if name in {"fixture_root", "release_root"}:
            relative = roots[name].get("relative_path")
            if name == "release_root" and relative == ".":
                continue
            _relative_path(relative, f"allowed_roots.{name}.relative_path")
    network = _as_mapping(value.get("network"), "network")
    if network.get("mode") != "loopback_only" or network.get("allow_dns") is not False:
        raise ManifestError("network_not_closed")
    if network.get("allow_external") is not False:
        raise ManifestError("external_network_must_be_disabled")
    endpoints = network.get("allowed_endpoints")
    if not isinstance(endpoints, list) or not endpoints:
        raise ManifestError("allowed_endpoints_empty")
    for index, endpoint in enumerate(endpoints):
        row = _as_mapping(endpoint, f"network.allowed_endpoints[{index}]")
        if row.get("host") != "127.0.0.1":
            raise ManifestError("non_loopback_endpoint")
        _as_positive_int(row.get("port"), f"network.allowed_endpoints[{index}].port")
        _as_non_empty_string(row.get("purpose"), f"network.allowed_endpoints[{index}].purpose")
    process = _as_mapping(value.get("owned_process_tree"), "owned_process_tree")
    if process.get("max_processes") != len(process.get("allowed_process_names") or []):
        raise ManifestError("process_count_bound_mismatch")
    if process.get("unknown_process_policy") != "fail_closed":
        raise ManifestError("unknown_process_policy_mismatch")
    if process.get("allow_orphan_adoption") is not False:
        raise ManifestError("orphan_adoption_must_be_disabled")
    adapters = value.get("adapters")
    if not isinstance(adapters, list) or not adapters:
        raise ManifestError("adapters_empty")
    for index, adapter in enumerate(adapters):
        row = _as_mapping(adapter, f"adapters[{index}]")
        if row.get("id") != SYNTHETIC_ADAPTER_ID:
            raise ManifestError("adapter_id_mismatch")
        if row.get("kind") not in {"mock", "recorded"}:
            raise ManifestError("adapter_kind_not_synthetic")
        if row.get("network") != "none":
            raise ManifestError("adapter_network_not_closed")
        if row.get("fallback") is not False or row.get("real_model") is not False:
            raise ManifestError("adapter_real_or_fallback_forbidden")
    binding = _as_mapping(value.get("synthetic_binding"), "synthetic_binding")
    if binding.get("synthetic_profile_id") != SYNTHETIC_PROFILE_ID:
        raise ManifestError("synthetic_profile_id_mismatch")
    if binding.get("profile_binding_digest") != SYNTHETIC_PROFILE_BINDING_DIGEST:
        raise ManifestError("profile_binding_digest_mismatch")
    if binding.get("binding_digest") != SYNTHETIC_PROFILE_BINDING_DIGEST:
        raise ManifestError("binding_digest_mismatch")
    if binding.get("fixture_digest") != SYNTHETIC_FIXTURE_DIGEST:
        raise ManifestError("fixture_digest_mismatch")
    if binding.get("default_run_binding_digest") != SYNTHETIC_DEFAULT_RUN_BINDING_DIGEST:
        raise ManifestError("default_run_binding_digest_mismatch")
    if binding.get("bundle_digest") != SYNTHETIC_BUNDLE_DIGEST:
        raise ManifestError("bundle_digest_mismatch")
    if binding.get("task_spec_digest") != SYNTHETIC_TASK_SPEC_DIGEST:
        raise ManifestError("task_spec_digest_mismatch")
    if binding.get("run_binding_count") != SYNTHETIC_RUN_BINDING_COUNT:
        raise ManifestError("run_binding_count_mismatch")
    observation = _as_mapping(value.get("independent_observation"), "independent_observation")
    required = observation.get("required_observers")
    if not isinstance(required, list) or set(required) != {"filesystem", "process_tree", "network", "adapter_calls"}:
        raise ManifestError("observation_set_incomplete")
    if observation.get("unavailable_policy") != "blocked":
        raise ManifestError("observation_failure_policy_mismatch")
    return value


def validate_viewport_layout_manifest(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate the pre-baseline, three-wide-viewport numeric layout freeze."""

    value = dict(_as_mapping(payload, "viewport_layout_manifest"))
    _common(value, VIEWPORT_SCHEMA)
    if value.get("baseline_state") != "frozen_before_visual_baseline":
        raise ManifestError("viewport_baseline_not_frozen")
    if value.get("browser_zoom_percent") != 100:
        raise ManifestError("browser_zoom_must_be_100")
    viewports = value.get("viewports")
    if not isinstance(viewports, list) or len(viewports) != 3:
        raise ManifestError("viewport_count_must_be_three")
    expected_dimensions = {(1920, 1080), (2560, 1440), (3840, 2160)}
    observed_dimensions = set()
    for index, viewport in enumerate(viewports):
        row = _as_mapping(viewport, f"viewports[{index}]")
        css = _as_mapping(row.get("css_viewport"), f"viewports[{index}].css_viewport")
        width = _as_positive_int(css.get("width"), f"viewports[{index}].width")
        height = _as_positive_int(css.get("height"), f"viewports[{index}].height")
        observed_dimensions.add((width, height))
        dpr = row.get("device_pixel_ratio")
        if not isinstance(dpr, (int, float)) or dpr <= 0:
            raise ManifestError(f"viewports[{index}].dpr_invalid")
        raw = _as_mapping(row.get("raw_pixels"), f"viewports[{index}].raw_pixels")
        if raw.get("width") != int(width * dpr) or raw.get("height") != int(height * dpr):
            raise ManifestError(f"viewports[{index}].raw_pixels_mismatch")
        layout = _as_mapping(row.get("layout"), f"viewports[{index}].layout")
        max_width = _as_positive_int(layout.get("content_max_width"), f"viewports[{index}].content_max_width")
        left = _as_non_negative_int(layout.get("left_gutter"), f"viewports[{index}].left_gutter")
        right = _as_non_negative_int(layout.get("right_gutter"), f"viewports[{index}].right_gutter")
        if max_width + left + right > width:
            raise ManifestError(f"viewports[{index}].layout_exceeds_viewport")
        columns = _as_positive_int(layout.get("column_count"), f"viewports[{index}].column_count")
        widths = layout.get("column_widths")
        if not isinstance(widths, list) or len(widths) != columns or any(
            not isinstance(item, int) or item <= 0 for item in widths
        ):
            raise ManifestError(f"viewports[{index}].column_widths_invalid")
        if sum(widths) + max(0, columns - 1) * int(layout.get("column_gap", 0)) > max_width:
            raise ManifestError(f"viewports[{index}].columns_exceed_content")
        chart_width = _as_positive_int(layout.get("primary_chart_effective_width"), f"viewports[{index}].chart_width")
        if chart_width > max_width:
            raise ManifestError(f"viewports[{index}].chart_exceeds_content")
        reading = _as_mapping(layout.get("reading_column"), f"viewports[{index}].reading_column")
        minimum = _as_positive_int(reading.get("min_chinese_chars"), f"viewports[{index}].reading_min")
        maximum = _as_positive_int(reading.get("max_chinese_chars"), f"viewports[{index}].reading_max")
        if minimum < 45 or maximum > 90 or minimum > maximum:
            raise ManifestError(f"viewports[{index}].reading_column_out_of_contract")
        targets = _as_mapping(row.get("target_minimums"), f"viewports[{index}].target_minimums")
        for name in ("core_button", "risk_summary", "flow_graph", "journey_axis", "table_first_row"):
            box = _as_mapping(targets.get(name), f"target_minimums.{name}")
            if box.get("min_css_width", 0) < 32 or box.get("min_css_height", 0) < 32:
                raise ManifestError(f"target_minimums.{name}_below_32")
    if observed_dimensions != expected_dimensions:
        raise ManifestError("viewport_dimensions_mismatch")
    thresholds = _as_mapping(value.get("thresholds"), "thresholds")
    if thresholds.get("minimum_click_target_css_px") != 32:
        raise ManifestError("click_target_threshold_mismatch")
    if thresholds.get("reading_column_min_chinese_chars") != 45 or thresholds.get("reading_column_max_chinese_chars") != 90:
        raise ManifestError("reading_threshold_mismatch")
    return value


def digest_directory(path: Path) -> str:
    """Return a deterministic digest of relative file names and file bytes."""

    root = path.expanduser().resolve()
    if not root.is_dir():
        raise ManifestError("directory_unreadable")
    rows = []
    try:
        paths = sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: item.relative_to(root).as_posix())
        for item in paths:
            relative = item.relative_to(root).as_posix()
            rows.append({"path": relative, "sha256": _digest_file(item)})
    except OSError as exc:
        raise ManifestError("directory_unreadable") from exc
    return digest_ref(rows)


def load_manifest(name: str, *, base_dir: Optional[Path] = None) -> Dict[str, Any]:
    if name not in _MANIFEST_NAMES:
        raise ManifestError("unknown_manifest")
    directory = (base_dir or Path(__file__).resolve().parent).expanduser().resolve()
    path = directory / name
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"manifest_unreadable:{name}") from exc
    if not isinstance(payload, dict):
        raise ManifestError(f"manifest_not_object:{name}")
    return payload


def load_all_manifests(*, base_dir: Optional[Path] = None, release_root: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    manifests = {
        "entry": load_manifest(ENTRY_MANIFEST_NAME, base_dir=base_dir),
        "execution_boundary": load_manifest(EXECUTION_BOUNDARY_MANIFEST_NAME, base_dir=base_dir),
        "viewport_layout": load_manifest(VIEWPORT_LAYOUT_MANIFEST_NAME, base_dir=base_dir),
    }
    validate_entry_manifest(manifests["entry"], release_root=release_root)
    validate_execution_boundary_manifest(manifests["execution_boundary"])
    validate_viewport_layout_manifest(manifests["viewport_layout"])
    return manifests


def manifest_bundle_digest(payload: Mapping[str, Any]) -> str:
    """Digest the identity-bearing entry subset without circular manifest fields."""

    entry = _as_mapping(payload.get("entry"), "entry")
    return digest_ref(
        {
            "schema": payload.get("schema"),
            "protocol": payload.get("protocol"),
            "window_identity": payload.get("window_identity"),
            "entry": {
                key: value
                for key, value in entry.items()
                if key not in {"directory_digest"}
            },
        }
    )


__all__ = [
    "APP_SCHEMA",
    "BOUNDARY_SCHEMA",
    "CONTRACT_VERSION",
    "ENTRY_MANIFEST_NAME",
    "ENTRY_SCHEMA",
    "EXECUTION_BOUNDARY_MANIFEST_NAME",
    "MANIFEST_VERSION",
    "ManifestError",
    "VIEWPORT_LAYOUT_MANIFEST_NAME",
    "VIEWPORT_SCHEMA",
    "digest_directory",
    "load_all_manifests",
    "load_manifest",
    "manifest_bundle_digest",
    "validate_entry_manifest",
    "validate_execution_boundary_manifest",
    "validate_viewport_layout_manifest",
]
