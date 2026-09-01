"""Offline G6 canonical bundle and actual-app endpoint seam tests.

These tests exercise the endpoint projection without opening a listener.  They do
not start an app, browser, model, subprocess, or network connection.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable

import pytest

WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_DIR = WORKBENCH_ROOT / "deploy" / "medical_monitoring_local"
SOURCE_STATIC_ROOT = WORKBENCH_ROOT / "frontend" / "dist"
PACKAGED_STATIC_ROOT = DEPLOY_DIR / "frontend" / "dist"
if str(DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOY_DIR))

import actual_app as app  # noqa: E402
import g6_manifests as manifests  # noqa: E402
import synthetic_ego as g  # noqa: E402


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def test_endpoint_payload_is_the_validated_canonical_bundle() -> None:
    expected = g.build_synthetic_audience_bundle()
    status, payload = app.synthetic_bundle_endpoint_response()

    assert status == 200
    assert payload == expected
    assert g.validate_synthetic_audience_bundle(payload) == expected
    assert payload["fixture"]["counts"]["events"] == 96
    assert payload["fixture"]["fixture_digest"].startswith("sha256:")
    assert payload["fixture"]["binding_digest"] == payload["fixture"]["profile_binding_digest"]
    assert payload["binding"]["fixture_digest"] == payload["fixture"]["fixture_digest"]
    assert payload["binding"]["fixture_binding_digest"] == payload["fixture"]["binding_digest"]
    assert payload["binding_role"] == "backward_compatible_default_alpha_full"
    assert payload["run_binding_count"] == 6
    assert {
        (row["project_ref"], row["analysis_mode"])
        for row in payload["run_bindings"]
    } == {
        (project_ref, analysis_mode)
        for project_ref in ("synthetic-project-alpha", "synthetic-project-beta")
        for analysis_mode in g.ANALYSIS_MODES
    }
    assert len({row["binding_digest"] for row in payload["run_bindings"]}) == 6
    assert payload["user_task_evidence"]["evidence_kind"] == "required_task_specification"
    assert payload["user_task_evidence"]["status"] == "awaiting_user_actions"
    assert payload["user_task_evidence"]["task_spec_digest"] == g.TASK_SPEC_DIGEST


def test_actual_app_route_projects_the_same_payload_without_a_listener() -> None:
    response = app.synthetic_api_get("/api/g6/synthetic-bundle?view=audience")
    assert response is not None
    status, payload = response
    assert status == 200
    assert payload == g.build_synthetic_audience_bundle()
    assert app.synthetic_api_get("/api/unknown") is None


def test_endpoint_identity_and_digests_are_deterministic() -> None:
    first_status, first = app.synthetic_bundle_endpoint_response()
    second_status, second = app.synthetic_bundle_endpoint_response()

    assert first_status == second_status == 200
    assert first == second
    assert first["bundle_digest"] == second["bundle_digest"]
    assert first["fixture"]["fixture_digest"] == second["fixture"]["fixture_digest"]
    assert first["fixture"]["binding_digest"] == second["fixture"]["binding_digest"]
    assert first["binding"]["binding_digest"] == second["binding"]["binding_digest"]


def test_endpoint_exposes_only_synthetic_adapter_and_project_identity() -> None:
    _status, payload = app.synthetic_bundle_endpoint_response()
    fixture = payload["fixture"]
    binding = payload["binding"]

    assert binding["provider"] == g.SYNTHETIC_PROVIDER
    assert binding["model"] == g.SYNTHETIC_MODEL
    assert binding["adapter_id"] == g.RECORDED_ADAPTER_ID
    assert binding["adapter_kind"] == g.RECORDED_ADAPTER_KIND
    assert binding["synthetic_only"] is True
    assert binding["offline"] is True
    assert all(row["project_ref"].startswith("synthetic-") for row in fixture["projects"])
    assert all(row["project_ref"].startswith("synthetic-") for row in fixture["subjects"])
    assert all(row["project_ref"].startswith("synthetic-") for row in fixture["events"])
    serialized = "\n".join(_strings(payload))
    for token in ("/Users/", "/tmp/", "/var/", "\\", ".env", "8911", "5174", "8984"):
        assert token not in serialized


def test_endpoint_fails_closed_when_bundle_validation_rejects(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject(_payload: object) -> dict[str, object]:
        raise g.SyntheticEgoError("tampered_bundle")

    monkeypatch.setattr(app._synthetic_ego, "validate_synthetic_audience_bundle", reject)
    status, payload = app.synthetic_bundle_endpoint_response()

    assert status == 503
    assert payload == {
        "schema": app.APP_SCHEMA,
        "protocol_version": app.APP_PROTOCOL_VERSION,
        "ready": False,
        "synthetic_only": True,
    }


def test_endpoint_fails_closed_on_forged_builder_output(monkeypatch: pytest.MonkeyPatch) -> None:
    canonical = g.build_synthetic_audience_bundle()
    forged = dict(canonical)
    forged["bundle_digest"] = "sha256:" + "f" * 64
    monkeypatch.setattr(app._synthetic_ego, "build_synthetic_audience_bundle", lambda: forged)

    status, payload = app.synthetic_bundle_endpoint_response()

    assert status == 503
    assert payload["ready"] is False
    assert "bundle_digest" not in payload


def test_release_inventory_contains_canonical_g6_generator() -> None:
    inventory = json.loads(
        (DEPLOY_DIR / "release_sources.json").read_text(encoding="utf-8")
    )
    assert "deploy/medical_monitoring_local/synthetic_ego.py" in inventory["entries"]
    assert "deploy/medical_monitoring_local/frontend/dist" in inventory["entries"]
    for runtime_file in (
        "deploy/medical_monitoring_local/actual_app.py",
        "deploy/medical_monitoring_local/g6_manifests.py",
        "deploy/medical_monitoring_local/canonical_evidence.py",
        "deploy/medical_monitoring_local/synthetic_ego.py",
        "deploy/medical_monitoring_local/synthetic_notification.py",
    ):
        assert runtime_file in inventory["entries"]


def _packaged_frontend_text() -> str:
    text_files = sorted(
        path
        for path in PACKAGED_STATIC_ROOT.rglob("*")
        if path.is_file() and path.suffix in {".css", ".html", ".js", ".json"}
    )
    return "\n".join(path.read_text(encoding="utf-8") for path in text_files)


def test_release_root_freezes_packaged_static_and_runtime_imports() -> None:
    frozen = manifests.load_all_manifests(base_dir=DEPLOY_DIR, release_root=DEPLOY_DIR)
    entry = frozen["entry"]
    assert entry["entry"]["static_root_relative_path"] == "frontend/dist"
    assert entry["entry"]["static_root_required"] is True
    assert PACKAGED_STATIC_ROOT.is_dir()

    packaged_static_files = sorted(
        path.relative_to(PACKAGED_STATIC_ROOT).as_posix()
        for path in PACKAGED_STATIC_ROOT.rglob("*")
        if path.is_file()
    )
    source_static_files = sorted(
        path.relative_to(SOURCE_STATIC_ROOT).as_posix()
        for path in SOURCE_STATIC_ROOT.rglob("*")
        if path.is_file()
    )
    assert packaged_static_files == source_static_files
    for relative in packaged_static_files:
        assert (PACKAGED_STATIC_ROOT / relative).read_bytes() == (SOURCE_STATIC_ROOT / relative).read_bytes()

    release_paths = {row["path"] for row in entry["release_files"]}
    assert {f"frontend/dist/{path}" for path in packaged_static_files} <= release_paths
    assert {
        "MedicalMonitoring.app/Contents/Info.plist",
        "MedicalMonitoring.app/Contents/MacOS/MedicalMonitoring",
        "actual_app.py",
        "g6_manifests.py",
        "canonical_evidence.py",
        "synthetic_ego.py",
        "synthetic_notification.py",
    } <= release_paths


def test_boundary_endpoint_frontend_and_release_share_canonical_identity() -> None:
    frozen = manifests.load_all_manifests(base_dir=DEPLOY_DIR, release_root=DEPLOY_DIR)
    boundary_binding = frozen["execution_boundary"]["synthetic_binding"]
    status, payload = app.synthetic_bundle_endpoint_response()
    assert status == 200

    fixture = payload["fixture"]
    assert boundary_binding["synthetic_profile_id"] == g.SYNTHETIC_PROFILE_ID
    assert boundary_binding["binding_digest"] == fixture["binding_digest"]
    assert boundary_binding["profile_binding_digest"] == fixture["profile_binding_digest"]
    assert boundary_binding["fixture_digest"] == fixture["fixture_digest"]
    assert boundary_binding["binding_digest"] != payload["binding"]["binding_digest"]
    assert frozen["execution_boundary"]["adapters"][0]["id"] == g.RECORDED_ADAPTER_ID

    frontend = _packaged_frontend_text()
    assert g.SYNTHETIC_PROFILE_ID in frontend
    assert fixture["fixture_digest"] in frontend
    assert fixture["binding_digest"] in frontend
    assert "/api/g6/synthetic-bundle" in frontend


def test_release_has_no_stale_g6_identity_or_58_event_fixture() -> None:
    _status, payload = app.synthetic_bundle_endpoint_response()
    assert len(payload["fixture"]["events"]) == 96
    assert payload["fixture"]["counts"]["events"] == 96
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    assert '"events": 58' not in serialized

    release_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in DEPLOY_DIR.rglob("*")
        if path.is_file() and path.suffix in {".json", ".py", ".js", ".css", ".html"}
    )
    assert "g6-cross-domain-v1" not in release_text
    assert "sha256:fb2399bdc54784699da68e03a2940abd96929211f33f01fa4a7b92e3f08c1c94" not in release_text
