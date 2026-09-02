"""C1 data-admission product-route contract tests (Phase C, worker slice 5).

Covers the three thin admission endpoints (create / status / profile preview)
over an injected fake pipeline: authorization per monitoring action, Chinese
error envelopes, public-projection boundary (paths, hashes and internal ids
only inside ``technical_details``), fail-closed behavior with no pipeline
bound, attempt-id validation, and proof that registration is purely additive
under the R7 project prefix (no route outside the R7 namespace is created or
changed — medical-writing and other surfaces stay untouched).

All admitted files are generated non-real fixtures; the source tree snapshot
proves the integration never writes into the source directory.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from services.api.app.medical_monitoring_r7_product_router import (
    R7_PRODUCT_PREFIX,
    create_medical_monitoring_r7_product_router,
)
from services.api.app.monitoring_runtime_principal import (
    MonitoringAuthenticatedPrincipal,
)
from packages.medical_monitoring.api.r7_product.admission_routes import (
    ADMISSION_SCHEMA_VERSION,
    AdmissionPipelineError,
)
from packages.medical_monitoring.admission import (
    LOCATOR_INDEX_KIND,
    DataAdmissionPipeline,
)
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.runtime.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
)
from services.api.app.listing_file_parser import parse_listing_file

PROJECT_A = "c1-admission-project-a"


def _has_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _assert_error_body(payload: Mapping[str, Any], *, status_code: int) -> None:
    assert status_code >= 400
    assert "detail" not in payload
    assert isinstance(payload.get("code"), str) and payload["code"].strip()
    assert isinstance(payload.get("message"), str) and payload["message"].strip()
    assert _has_chinese(payload["message"])
    blob = json.dumps(payload, ensure_ascii=False).lower()
    assert "traceback" not in blob
    assert "sqlite" not in blob


def _principal(
    *project_ids: str,
    roles: tuple[str, ...] = ("medical_manager", "system_admin"),
) -> MonitoringAuthenticatedPrincipal:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return MonitoringAuthenticatedPrincipal.from_server_verified_claims(
        {
            "server_verified": True,
            "principal_id": "c1-admission-test-user",
            "tenant_id": "c1-tenant-001",
            "roles": list(roles),
            "project_scope": list(project_ids or (PROJECT_A,)),
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=2)).isoformat(),
            "authenticated": True,
            "authn_method": "offline-test-session",
            "session_id": "c1-admission-test-session",
            "directory_revision": "c1-admission-directory-v1",
            "verification_ref_sha256": "c" * 64,
        },
        now=now,
    )


def _base(project_id: str = PROJECT_A) -> str:
    return R7_PRODUCT_PREFIX.format(project_id=project_id)


class FakeAdmissionPipeline:
    """Minimal AdmissionPipeline double recording every call."""

    def __init__(
        self,
        *,
        create_result: Mapping[str, Any] | None = None,
        status_result: Mapping[str, Any] | None = None,
        profile_result: Mapping[str, Any] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.create_result = create_result if create_result is not None else {
            "attempt_id": "attempt-0001",
            "state": "ready",
            "summary": {"files": 2, "tables": 1, "rows": 3},
            "technical_details": {
                "source_dir": "/generated/non-real/source",
                "copy_sha256": "a" * 64,
            },
        }
        self.status_result = status_result if status_result is not None else {
            "attempt_id": "attempt-0001",
            "state": "ready",
            "summary": {"files": 2, "tables": 1, "rows": 3},
        }
        self.profile_result = profile_result if profile_result is not None else {
            "attempt_id": "attempt-0001",
            "tables": [
                {
                    "name": "generated_sheet",
                    "row_count": 3,
                    "headers": ["subject", "visit", "date"],
                }
            ],
            "technical_details": {
                "snapshot_id": "snap-0001",
                "revision_id": "rev-0001",
            },
        }
        self.error = error

    def _record(self, name: str, kwargs: dict[str, Any]) -> None:
        self.calls.append((name, kwargs))
        if self.error is not None:
            raise self.error

    def create_attempt(self, **kwargs: Any) -> Mapping[str, Any]:
        self._record("create_attempt", kwargs)
        return self.create_result

    def create_uploaded_attempt(self, **kwargs: Any) -> Mapping[str, Any]:
        captured = []
        for relative_path, stream in kwargs.pop("uploads"):
            stream.seek(0)
            captured.append((relative_path, stream.read()))
        self._record("create_uploaded_attempt", {**kwargs, "uploads": captured})
        return self.create_result

    def attempt_status(self, **kwargs: Any) -> Mapping[str, Any]:
        self._record("attempt_status", kwargs)
        return self.status_result

    def profile_preview(self, **kwargs: Any) -> Mapping[str, Any]:
        self._record("profile_preview", kwargs)
        return self.profile_result


def _make_app(
    runtime_dir: Path,
    *,
    principal: MonitoringAuthenticatedPrincipal,
    admission_pipeline: Any = None,
) -> FastAPI:
    app = FastAPI()

    @app.get("/__sentinel_non_r7")
    def _sentinel() -> dict[str, str]:
        return {"surface": "non-r7"}

    def _resolve_principal(_request: Request) -> MonitoringAuthenticatedPrincipal:
        return principal

    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=runtime_dir,
            project_resolver=lambda project_id: project_id,
            principal_resolver=_resolve_principal,
            require_server_principal=True,
            admission_pipeline=admission_pipeline,
        )
    )
    return app


_SENTINEL = object()


def _client(
    runtime_dir: Path,
    *,
    principal: Any = _SENTINEL,
    admission_pipeline: Any = None,
) -> TestClient:
    if principal is _SENTINEL:
        principal = _principal(PROJECT_A)
    return TestClient(
        _make_app(
            runtime_dir,
            principal=principal,
            admission_pipeline=admission_pipeline,
        )
    )


def _flatten_paths(routes: Any) -> set[str]:
    paths: set[str] = set()
    for route in routes:
        path = getattr(route, "path", "")
        if path:
            paths.add(path)
        nested = getattr(route, "routes", None)
        if nested:
            paths.update(_flatten_paths(nested))
        original = getattr(route, "original_router", None)
        original_routes = getattr(original, "routes", None) if original is not None else None
        if original_routes:
            paths.update(_flatten_paths(original_routes))
    return paths


def _snapshot_tree(root: Path) -> list[tuple[str, int, float]]:
    entries: list[tuple[str, int, float]] = []
    for path in sorted(root.rglob("*")):
        stat = path.stat()
        entries.append(
            (str(path.relative_to(root)), stat.st_size if path.is_file() else -1, stat.st_mtime)
        )
    return entries


def _make_generated_source_tree(root: Path) -> Path:
    """Generate a small non-real listing directory (test-only data)."""
    source = root / "generated_source"
    (source / "listing_a").mkdir(parents=True)
    (source / "listing_a" / "table.csv").write_text(
        "subject,visit,date\nS001,V1,2026-01-01\nS002,V1,2026-01-02\nS003,V2,2026-01-03\n",
        encoding="utf-8",
    )
    (source / "listing_a" / "notes.json").write_text(
        json.dumps({"batch": "generated-non-real", "rows": 3}), encoding="utf-8"
    )
    return source


def test_admission_registration_is_additive_and_r7_scoped(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    pipeline = FakeAdmissionPipeline()
    app = _make_app(runtime_dir, principal=_principal(PROJECT_A), admission_pipeline=pipeline)

    paths = _flatten_paths(app.routes)
    r7_paths = {path for path in paths if "medical-monitoring/r7" in path}
    admission_paths = {path for path in r7_paths if "data-admissions" in path}
    assert admission_paths == {
        "/api/projects/{project_id}/modules/medical-monitoring/r7/data-admissions",
        "/api/projects/{project_id}/modules/medical-monitoring/r7/data-admissions/upload",
        "/api/projects/{project_id}/modules/medical-monitoring/r7/data-admissions/{attempt_id}",
        "/api/projects/{project_id}/modules/medical-monitoring/r7/data-admissions/{attempt_id}/mapping-candidates",
        "/api/projects/{project_id}/modules/medical-monitoring/r7/data-admissions/{attempt_id}/profile",
    }
    assert all(
        path.startswith("/api/projects/{project_id}/modules/medical-monitoring/r7")
        for path in r7_paths
    )
    non_r7 = paths - r7_paths
    assert non_r7 == {"/__sentinel_non_r7", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


def test_create_status_and_profile_happy_path_boundary(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    source = _make_generated_source_tree(tmp_path)
    before = _snapshot_tree(source)
    pipeline = FakeAdmissionPipeline()
    client = _client(runtime_dir, admission_pipeline=pipeline)

    response = client.post(
        f"{_base()}/data-admissions",
        json={"source_dir": str(source)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == ADMISSION_SCHEMA_VERSION
    assert body["project_id"] == PROJECT_A
    assert body["attempt_id"] == "attempt-0001"
    assert body["state"] == "ready"
    # Path/hash values stay inside the collapsed technical-details view.
    public_view = {k: v for k, v in body.items() if k != "technical_details"}
    public_blob = json.dumps(public_view, ensure_ascii=False).lower()
    assert "/generated/non-real/source" not in public_blob
    assert "a" * 64 not in public_blob
    assert body["technical_details"]["copy_sha256"] == "a" * 64

    (name, kwargs), = pipeline.calls
    assert name == "create_attempt"
    assert kwargs["project_id"] == PROJECT_A
    assert Path(kwargs["source_dir"]) == source
    assert kwargs["workspace_dir"] == runtime_dir / "medical_monitoring_r7" / PROJECT_A

    pipeline.calls.clear()
    status = client.get(f"{_base()}/data-admissions/attempt-0001")
    assert status.status_code == 200
    assert status.json()["state"] == "ready"
    assert status.json()["attempt_id"] == "attempt-0001"
    profile = client.get(f"{_base()}/data-admissions/attempt-0001/profile")
    assert profile.status_code == 200
    assert profile.json()["tables"][0]["name"] == "generated_sheet"
    assert profile.json()["technical_details"]["snapshot_id"] == "snap-0001"
    assert [(n, sorted(k for k in kws if k != "workspace_dir")) for n, kws in pipeline.calls] == [
        ("attempt_status", ["attempt_id", "project_id"]),
        ("profile_preview", ["attempt_id", "project_id"]),
    ]

    assert _snapshot_tree(source) == before


def test_browser_upload_create_uses_relative_names_and_bytes(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    pipeline = FakeAdmissionPipeline()
    client = _client(runtime_dir, admission_pipeline=pipeline)
    content = b"subject,visit,date\nS001,V1,2026-01-01\n"

    response = client.post(
        f"{_base()}/data-admissions/upload",
        files=[("files", ("table.csv", content, "text/csv"))],
        data={"relative_paths": "listing_a/table.csv"},
    )

    assert response.status_code == 200, response.text
    (name, kwargs), = pipeline.calls
    assert name == "create_uploaded_attempt"
    assert kwargs["project_id"] == PROJECT_A
    assert kwargs["uploads"] == [("listing_a/table.csv", content)]
    assert kwargs["workspace_dir"] == runtime_dir / "medical_monitoring_r7" / PROJECT_A


def test_real_pipeline_closes_generated_browser_upload_loop(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    client = _client(
        runtime_dir,
        admission_pipeline=DataAdmissionPipeline(parse_listing_file),
    )
    content = b"subject,visit,date\nS001,V1,2026-01-01\nS002,V2,2026-01-02\n"

    created = client.post(
        f"{_base()}/data-admissions/upload",
        files=[("files", ("table.csv", content, "text/csv"))],
        data={"relative_paths": "selected_folder/table.csv"},
    )

    assert created.status_code == 200, created.text
    body = created.json()
    assert body["state"] == "profile_ready"
    assert body["summary"] == {"files": 1, "tables": 1, "rows": 2}
    attempt_id = body["attempt_id"]
    profile = client.get(f"{_base()}/data-admissions/{attempt_id}/profile")
    assert profile.status_code == 200
    assert profile.json()["tables"][0]["row_count"] == 2
    intake_parent = (
        runtime_dir
        / "medical_monitoring_r7"
        / PROJECT_A
        / "admissions"
        / "upload-intake"
    )
    assert not intake_parent.exists()


def test_real_pipeline_closes_generated_file_product_loop(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    source = _make_generated_source_tree(tmp_path)
    before = _snapshot_tree(source)
    client = _client(
        runtime_dir,
        admission_pipeline=DataAdmissionPipeline(parse_listing_file),
    )

    created = client.post(
        f"{_base()}/data-admissions", json={"source_dir": str(source)}
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["state"] == "profile_ready"
    assert body["summary"] == {"files": 1, "tables": 1, "rows": 3}
    attempt_id = body["attempt_id"]
    snapshot_id = body["technical_details"]["snapshot_ids"][0]

    status = client.get(f"{_base()}/data-admissions/{attempt_id}")
    assert status.status_code == 200
    assert status.json()["summary"] == body["summary"]
    profile = client.get(f"{_base()}/data-admissions/{attempt_id}/profile")
    assert profile.status_code == 200
    table = profile.json()["tables"][0]
    assert table["name"] == "table"
    assert table["row_count"] == 3
    assert table["column_count"] == 3
    assert any(column["suggested_roles"] for column in table["columns"])
    assert _snapshot_tree(source) == before

    project_workspace = runtime_dir / "medical_monitoring_r7" / PROJECT_A
    store = Store(
        project_workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
        project_workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME,
    )
    try:
        assert store.get_project(PROJECT_A).is_synthetic is False
        assert store.get_listing_snapshot(snapshot_id).is_synthetic is False
        locator_index = store.get_domain_object(LOCATOR_INDEX_KIND, snapshot_id)
        assert locator_index is not None
        assert locator_index[1]["row_numbers"] == [2, 3, 4]
        assert len(locator_index[1]["locator_ids"]) == 9
    finally:
        store.close()

    replay = client.post(
        f"{_base()}/data-admissions", json={"source_dir": str(source)}
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["attempt_id"] != attempt_id
    assert replay.json()["technical_details"]["snapshot_ids"] == [snapshot_id]


def test_real_pipeline_refuses_existing_synthetic_project_identity(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    source = _make_generated_source_tree(tmp_path)
    project_workspace = runtime_dir / "medical_monitoring_r7" / PROJECT_A
    store = Store(
        project_workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
        project_workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME,
    )
    try:
        store.create_project(PROJECT_A, PROJECT_A, is_synthetic=True)
    finally:
        store.close()

    client = _client(
        runtime_dir,
        admission_pipeline=DataAdmissionPipeline(parse_listing_file),
    )
    response = client.post(
        f"{_base()}/data-admissions", json={"source_dir": str(source)}
    )

    _assert_error_body(response.json(), status_code=409)
    assert response.json()["code"] == "admission_project_identity_conflict"


def test_create_leaves_generated_source_tree_unmodified(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    source = _make_generated_source_tree(tmp_path)
    before = _snapshot_tree(source)
    pipeline = FakeAdmissionPipeline(error=AdmissionPipelineError("admission_copy_rejected"))
    client = _client(runtime_dir, admission_pipeline=pipeline)

    response = client.post(f"{_base()}/data-admissions", json={"source_dir": str(source)})
    _assert_error_body(response.json(), status_code=409)
    assert response.json()["code"] == "admission_copy_rejected"
    assert _snapshot_tree(source) == before
    # A rejected attempt leaves no runtime workspace behind from this route.
    assert not (runtime_dir / "medical_monitoring_r7" / PROJECT_A).exists()


def test_unconfigured_pipeline_fails_closed_without_writes(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    client = _client(runtime_dir, admission_pipeline=None)

    response = client.post(f"{_base()}/data-admissions", json={"source_dir": "/tmp/x"})
    _assert_error_body(response.json(), status_code=503)
    assert response.json()["code"] == "admission_pipeline_unconfigured"
    status = client.get(f"{_base()}/data-admissions/attempt-0001")
    _assert_error_body(status.json(), status_code=503)
    profile = client.get(f"{_base()}/data-admissions/attempt-0001/profile")
    _assert_error_body(profile.json(), status_code=503)
    assert not (runtime_dir / "medical_monitoring_r7").exists()


def test_admission_actions_follow_monitoring_roles(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    source = _make_generated_source_tree(tmp_path)
    monitor_client = _client(
        runtime_dir,
        principal=_principal(PROJECT_A, roles=("medical_monitor",)),
        admission_pipeline=FakeAdmissionPipeline(),
    )

    denied = monitor_client.post(
        f"{_base()}/data-admissions", json={"source_dir": str(source)}
    )
    _assert_error_body(denied.json(), status_code=403)
    assert denied.json()["code"] == "not_permitted"

    allowed_status = monitor_client.get(f"{_base()}/data-admissions/attempt-0001")
    assert allowed_status.status_code == 200
    allowed_profile = monitor_client.get(f"{_base()}/data-admissions/attempt-0001/profile")
    assert allowed_profile.status_code == 200

    writer_client = _client(
        runtime_dir,
        principal=_principal(PROJECT_A, roles=("medical_writer",)),
        admission_pipeline=FakeAdmissionPipeline(),
    )
    writer_status = writer_client.get(f"{_base()}/data-admissions/attempt-0001")
    assert writer_status.status_code == 200


def test_unknown_attempt_and_invalid_ids_fail_with_chinese_errors(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()

    class NotFoundPipeline(FakeAdmissionPipeline):
        def attempt_status(self, **kwargs: Any) -> Mapping[str, Any]:
            self._record("attempt_status", kwargs)
            raise AdmissionPipelineError("admission_attempt_not_found")

    client = _client(
        runtime_dir,
        admission_pipeline=NotFoundPipeline(),
    )
    missing = client.get(f"{_base()}/data-admissions/attempt-9999")
    _assert_error_body(missing.json(), status_code=404)
    assert missing.json()["code"] == "admission_attempt_not_found"

    bad_id = client.get(f"{_base()}/data-admissions/../escaped")
    assert bad_id.status_code in (404, 422)
    traversal = client.get(f"{_base()}/data-admissions/{'x' * 300}")
    _assert_error_body(traversal.json(), status_code=422)
    assert traversal.json()["code"] == "admission_attempt_id_invalid"


def test_pipeline_failures_map_to_sanitized_chinese_envelopes(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    source = _make_generated_source_tree(tmp_path)

    class BrokenPipeline(FakeAdmissionPipeline):
        def create_attempt(self, **kwargs: Any) -> Mapping[str, Any]:
            self._record("create_attempt", kwargs)
            raise RuntimeError("internal sqlite disk I/O error detail")

    client = _client(runtime_dir, admission_pipeline=BrokenPipeline())
    response = client.post(f"{_base()}/data-admissions", json={"source_dir": str(source)})
    _assert_error_body(response.json(), status_code=500)
    assert response.json()["code"] == "admission_pipeline_failed"
    assert "sqlite" not in json.dumps(response.json(), ensure_ascii=False).lower()

    profile_client = _client(
        runtime_dir,
        admission_pipeline=FakeAdmissionPipeline(
            error=AdmissionPipelineError("admission_profile_unavailable")
        ),
    )
    profile = profile_client.get(f"{_base()}/data-admissions/attempt-0001/profile")
    _assert_error_body(profile.json(), status_code=409)
    assert profile.json()["code"] == "admission_profile_unavailable"


def test_projection_boundary_rejects_public_hash_or_path_keys(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    source = _make_generated_source_tree(tmp_path)
    leaky = FakeAdmissionPipeline(
        create_result={
            "attempt_id": "attempt-0001",
            "state": "ready",
            "source_sha256": "b" * 64,
        }
    )
    client = _client(runtime_dir, admission_pipeline=leaky)
    response = client.post(f"{_base()}/data-admissions", json={"source_dir": str(source)})
    _assert_error_body(response.json(), status_code=500)
    assert response.json()["code"] == "admission_projection_violation"
    assert "b" * 64 not in json.dumps(response.json(), ensure_ascii=False)

    malformed = FakeAdmissionPipeline(create_result={"state": "ready"})
    client = _client(runtime_dir, admission_pipeline=malformed)
    response = client.post(f"{_base()}/data-admissions", json={"source_dir": str(source)})
    _assert_error_body(response.json(), status_code=500)
    assert response.json()["code"] == "admission_projection_violation"


def test_create_request_validation_is_strict_and_chinese(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    client = _client(runtime_dir, admission_pipeline=FakeAdmissionPipeline())

    empty_dir = client.post(f"{_base()}/data-admissions", json={"source_dir": "   "})
    _assert_error_body(empty_dir.json(), status_code=422)

    extra_field = client.post(
        f"{_base()}/data-admissions",
        json={"source_dir": "/tmp/x", "project_id": "smuggled"},
    )
    _assert_error_body(extra_field.json(), status_code=422)

    missing_field = client.post(f"{_base()}/data-admissions", json={})
    _assert_error_body(missing_field.json(), status_code=422)

    not_object = client.post(f"{_base()}/data-admissions", json=["source_dir"])
    _assert_error_body(not_object.json(), status_code=422)


def test_unauthorized_principal_cannot_reach_admission_routes(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    client = _client(
        runtime_dir,
        principal=None,
        admission_pipeline=FakeAdmissionPipeline(),
    )
    response = client.post(
        f"{_base()}/data-admissions", json={"source_dir": "/tmp/x"}
    )
    _assert_error_body(response.json(), status_code=503)
    assert response.json()["code"] == "principal_required"
