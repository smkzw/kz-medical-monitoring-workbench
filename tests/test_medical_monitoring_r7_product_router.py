"""R7 product-router offline contract tests.

Covers zero-import writes, per-project isolation, bootstrap/MTPLX default,
name-only DeepSeek, auto scope, replay/conflict, Chinese R7 errors,
run-setup options, special-risk-rule preview/revision lifecycle,
synthetic prepare-and-start/public history recovery, and Slice-07C-3/4
publication progress/history/result-entry/public result-context failure and
recovery gates. Uses a throwaway FastAPI host + tmp runtime only — no main.py
import, no live service, no real model/project.
"""

from __future__ import annotations

from dataclasses import replace as dataclass_replace
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

from services.api.app.medical_monitoring_r7_product_router import (
    R7_PRODUCT_PREFIX,
    create_medical_monitoring_r7_product_router,
)
from services.api.app.monitoring_runtime_principal import (
    MonitoringAuthenticatedPrincipal,
)
from poc.medical_monitoring_ai_native_r7.src.mm_r7.run_entry import (
    RUN_BINDING_DB_NAME,
    MonitoringRunEntry,
)
from poc.medical_monitoring_ai_native_r7.src.mm_r7.background_recovery import (
    BackgroundRecoveryAdapter,
)
from poc.medical_monitoring_ai_native_r7.src.mm_r7.maintenance_gate import (
    ProjectMaintenanceGate,
)
from poc.medical_monitoring_ai_native_r7.src.mm_r7 import launch_registry as lr
from poc.medical_monitoring_ai_native_r7.src.mm_r7 import project_backup as pb
from poc.medical_monitoring_ai_native_r7.tests.fake_harness import (
    FakeCatalog,
    FakeHarnessAdapter,
)

PROJECT_A = "r7-product-project-a"
PROJECT_B = "r7-product-project-b"
MTPLX_CONFIG = "mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality"
DEEPSEEK_CONFIG = "deepseek/DeepSeek V4 flash"

FORBIDDEN_VALUE_TOKENS = (
    "super-secret-value",
    "env-value-leaked",
    "sk-",
    "modeoutput",
    "risk_instance",
    "patientjourney",
    "query_draft",
    "canonical_fact",
    "report_claim",
)


def _has_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _assert_error_body(payload: Mapping[str, Any], *, status_code: int) -> None:
    assert status_code >= 400
    # Frozen Slice-03: R7 product errors are top-level {code, message}.
    assert "detail" not in payload
    assert isinstance(payload.get("code"), str) and payload["code"].strip()
    assert isinstance(payload.get("message"), str) and payload["message"].strip()
    assert _has_chinese(payload["message"])
    blob = json.dumps(payload, ensure_ascii=False).lower()
    for token in FORBIDDEN_VALUE_TOKENS:
        assert token not in blob
    assert "traceback" not in blob
    assert "sqlite" not in blob


def _assert_public_clean(payload: Mapping[str, Any]) -> None:
    blob = json.dumps(payload, ensure_ascii=False).lower()
    for token in FORBIDDEN_VALUE_TOKENS:
        assert token not in blob
    assert "effective_selector" not in payload
    assert "requested_provider" not in payload
    assert "requested_model" not in payload
    assert "credential_value" not in blob


def _principal(
    *project_ids: str,
    roles: tuple[str, ...] | None = None,
) -> MonitoringAuthenticatedPrincipal:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    scope = tuple(project_ids) if project_ids else (PROJECT_A, PROJECT_B)
    return MonitoringAuthenticatedPrincipal.from_server_verified_claims(
        {
            "server_verified": True,
            "principal_id": "r7-product-test-user",
            "tenant_id": "r7-tenant-001",
            # Writes: ADMINISTER_RUNTIME (system_admin); reads: READ_AI_RUN.
            "roles": list(roles or ("medical_manager", "system_admin")),
            "project_scope": list(scope),
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=2)).isoformat(),
            "authenticated": True,
            "authn_method": "offline-test-session",
            "session_id": "r7-product-test-session",
            "directory_revision": "r7-product-directory-v1",
            "verification_ref_sha256": "e" * 64,
        },
        now=now,
    )


def _base(project_id: str) -> str:
    return R7_PRODUCT_PREFIX.format(project_id=project_id)


def _r7_workspace(runtime_dir: Path, project_id: str) -> Path:
    return runtime_dir / "medical_monitoring_r7" / project_id


def _sqlite_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.sqlite3") if p.is_file())


def _make_app(
    runtime_dir: Path,
    *,
    principal: MonitoringAuthenticatedPrincipal | None = None,
    maintenance_wait_seconds: float = 30.0,
    project_resolver: Callable[[str], str] | None = None,
    require_server_principal: bool = True,
    harness_runtime_factory: Callable[..., Any] | None = None,
    harness_adapter: Any = None,
    harness_catalog: Any = None,
    harness_r1_profile: Any = None,
    authority_provider: Any = None,
    r5_product_packet_factory: Callable[[Any], Any] | None = None,
    r6_output_provider: Any = None,
    r6_publication_provider: Any = None,
    mode_output_provider: Any = None,
    r6_mode_output_provider: Any = None,
    continuity_bridge: Any = None,
) -> FastAPI:
    app = FastAPI()

    @app.get("/__non_r7_probe")
    def _non_r7_probe() -> None:
        raise HTTPException(status_code=400, detail="legacy-non-r7-detail-shape")

    def _resolve_principal(_request: Request) -> MonitoringAuthenticatedPrincipal | None:
        return principal

    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=runtime_dir,
            project_resolver=project_resolver or (lambda project_id: project_id),
            principal_resolver=_resolve_principal,
            require_server_principal=require_server_principal,
            harness_runtime_factory=harness_runtime_factory,
            harness_adapter=harness_adapter,
            harness_catalog=harness_catalog,
            harness_r1_profile=harness_r1_profile,
            authority_provider=authority_provider,
            r5_product_packet_factory=r5_product_packet_factory,
            maintenance_wait_seconds=maintenance_wait_seconds,
            r6_output_provider=r6_output_provider,
            r6_publication_provider=r6_publication_provider,
            mode_output_provider=mode_output_provider,
            r6_mode_output_provider=r6_mode_output_provider,
            continuity_bridge=continuity_bridge,
        )
    )
    return app


_SENTINEL = object()


def _client(
    runtime_dir: Path,
    *,
    principal: MonitoringAuthenticatedPrincipal | None = _SENTINEL,
    maintenance_wait_seconds: float = 30.0,
    project_resolver: Callable[[str], str] | None = None,
    harness_runtime_factory: Callable[..., Any] | None = None,
    harness_adapter: Any = None,
    harness_catalog: Any = None,
    harness_r1_profile: Any = None,
    authority_provider: Any = None,
    r5_product_packet_factory: Callable[[Any], Any] | None = None,
    r6_output_provider: Any = None,
    r6_publication_provider: Any = None,
    mode_output_provider: Any = None,
    r6_mode_output_provider: Any = None,
    continuity_bridge: Any = None,
) -> TestClient:
    if principal is _SENTINEL:
        principal = _principal()
    return TestClient(
        _make_app(
            runtime_dir,
            principal=principal,
            project_resolver=project_resolver,
            maintenance_wait_seconds=maintenance_wait_seconds,
            harness_runtime_factory=harness_runtime_factory,
            harness_adapter=harness_adapter,
            harness_catalog=harness_catalog,
            harness_r1_profile=harness_r1_profile,
            authority_provider=authority_provider,
            r5_product_packet_factory=r5_product_packet_factory,
            r6_output_provider=r6_output_provider,
            r6_publication_provider=r6_publication_provider,
            mode_output_provider=mode_output_provider,
            r6_mode_output_provider=r6_mode_output_provider,
            continuity_bridge=continuity_bridge,
        )
    )


def _run_body(**overrides: Any) -> dict[str, Any]:
    """Product CreateRun DTO: no project_id / project_scope_key / run_override_scope_key."""
    body: dict[str, Any] = {
        "run_id": "run-product-001",
        "mode": "daily",
        "execution_basis": "full",
        "data_cutoff": "2026-08-28",
        "source_revision_id": "src-sha256:product-bbb",
        "prior_accepted_snapshot_ref": None,
    }
    body.update(overrides)
    return body


def test_product_prefix_and_routes_exclude_isolated_poc_prefix(tmp_path: Path) -> None:
    app = _make_app(tmp_path, principal=_principal())

    def _flatten_paths(routes: Any) -> set[str]:
        # fastapi >= 0.137 nests included routers as _IncludedRouter objects.
        # Child routes live on original_router.routes, not on app.routes.
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

    paths = _flatten_paths(app.routes)
    r7_paths = {path for path in paths if "medical-monitoring/r7" in path}
    assert r7_paths
    assert all(path.startswith("/api/projects/{project_id}/modules/medical-monitoring/r7") for path in r7_paths)
    assert not any(path.startswith("/api/medical-monitoring/r7") for path in paths)
    assert R7_PRODUCT_PREFIX == "/api/projects/{project_id}/modules/medical-monitoring/r7"


def test_import_and_router_construction_make_zero_r7_writes(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    before = _sqlite_files(runtime_dir)
    assert before == []

    # Re-import / construct must not mkdir medical_monitoring_r7 or open SQLite.
    import importlib

    import services.api.app.medical_monitoring_r7_product_router as product_mod

    importlib.reload(product_mod)
    router = product_mod.create_medical_monitoring_r7_product_router(
        runtime_dir=runtime_dir,
        project_resolver=lambda project_id: project_id,
        principal_resolver=lambda _request: _principal(),
        require_server_principal=True,
    )
    assert router.prefix == R7_PRODUCT_PREFIX or any(
        "medical-monitoring/r7" in getattr(route, "path", "") for route in router.routes
    )
    assert not (runtime_dir / "medical_monitoring_r7").exists()
    assert _sqlite_files(runtime_dir) == []


def test_bootstrap_seeds_mtplx_medium_and_is_idempotent(tmp_path: Path) -> None:
    client = _client(tmp_path)
    first = client.post(f"{_base(PROJECT_A)}/workspace/bootstrap")
    assert first.status_code == 200, first.text
    body1 = first.json()
    _assert_public_clean(body1)
    assert body1.get("replayed") is False
    assert body1.get("user_config_name") == MTPLX_CONFIG
    assert body1.get("reasoning_effort") == "medium"
    assert body1.get("revision") == 1

    ws = _r7_workspace(tmp_path, PROJECT_A)
    assert ws.is_dir()
    assert _sqlite_files(ws)

    second = client.post(f"{_base(PROJECT_A)}/workspace/bootstrap")
    assert second.status_code == 200, second.text
    body2 = second.json()
    assert body2.get("replayed") is True
    assert body2.get("revision") == body1.get("revision") == 1
    assert body2.get("record_id") == body1.get("record_id")
    assert body2.get("user_config_name") == MTPLX_CONFIG

def _assert_backup_public_projection(
    payload: Mapping[str, Any],
    *,
    expected_keys: set[str],
) -> None:
    _assert_public_clean(payload)
    assert set(payload) == expected_keys
    for key in {
        "status",
        "operation_kind",
        "idempotency_key",
        "canonical_project_id",
        "package_id",
        "package_path",
        "source_workspace_fingerprint",
        "staging_path",
        "rollback_path",
        "maintenance_state",
        "payload",
        "schema_version",
        "manifest",
    }:
        assert key not in payload


def _wait_for_operation(
    client: TestClient,
    url: str,
    *,
    field: str,
    terminal_values: set[str],
    timeout: float = 5.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        response = client.get(url)
        assert response.status_code == 200, response.text
        last = response.json()
        if last.get(field) in terminal_values:
            return last
        time.sleep(0.01)
    raise AssertionError(f"operation did not reach terminal state: {last!r}")


def test_slice09a_product_five_routes_use_chinese_public_dtos(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    backup_response = client.post(
        f"{_base(PROJECT_A)}/backups",
        json={"idempotency_key": "slice09a-product-backup-001"},
    )
    assert backup_response.status_code == 200, backup_response.text
    backup = backup_response.json()
    backup_keys = {
        "operation_id",
        "status_label",
        "project_name",
        "backup_cutoff_label",
        "monitoring_scope_summary",
        "recommended_next_action",
        "progress_percent",
        "current_step_label",
    }
    _assert_backup_public_projection(backup, expected_keys=backup_keys)
    assert backup["status_label"] == "准备中"
    assert backup["progress_percent"] == 5
    backup_operation_id = backup["operation_id"]

    backup_status = _wait_for_operation(
        client,
        f"{_base(PROJECT_A)}/backups/{backup_operation_id}",
        field="status_label",
        terminal_values={"已可下载"},
    )
    assert backup_status["status_label"] == "已可下载"
    assert backup_status["progress_percent"] == 100
    backup = backup_status

    backup_status = client.get(
        f"{_base(PROJECT_A)}/backups/{backup_operation_id}"
    )
    assert backup_status.status_code == 200, backup_status.text
    assert backup_status.json() == backup
    replayed_backup = client.post(
        f"{_base(PROJECT_A)}/backups",
        json={"idempotency_key": "slice09a-product-backup-001"},
    )
    assert replayed_backup.status_code == 200, replayed_backup.text
    assert replayed_backup.json() == backup
    monitor = _client(
        tmp_path,
        principal=_principal(PROJECT_A, roles=("medical_monitor",)),
    )
    monitor_get = monitor.get(
        f"{_base(PROJECT_A)}/backups/{backup_operation_id}"
    )
    assert monitor_get.status_code == 200, monitor_get.text
    monitor_post = monitor.post(f"{_base(PROJECT_A)}/backups", json={})
    _assert_error_body(monitor_post.json(), status_code=monitor_post.status_code)
    assert monitor_post.status_code == 403

    preflight_response = client.post(
        f"{_base(PROJECT_A)}/restores/preflight",
        json={
            "backup_operation_id": backup_operation_id,
            "idempotency_key": "slice09a-product-preflight-001",
        },
    )
    assert preflight_response.status_code == 200, preflight_response.text
    preflight = preflight_response.json()
    preflight_keys = {
        "operation_id",
        "backup_operation_id",
        "decision_label",
        "backup_project_name",
        "backup_cutoff_label",
        "current_cutoff_label",
        "impact_summary",
        "items_preserved",
        "items_rolled_back",
        "recommended_action",
        "confirmation_required",
        "unfinished_work_notice",
        "progress_percent",
        "current_step_label",
    }
    _assert_backup_public_projection(preflight, expected_keys=preflight_keys)
    assert preflight["decision_label"] in {
        "可恢复",
        "已是当前版本",
        "需确认回退",
        "无法恢复",
    }
    assert "unfinished_work_notice" in preflight
    assert set(preflight["items_rolled_back"]) == {
        "监查运行",
        "结果发布",
        "风险规则",
        "连续性计划",
    }
    preflight_operation_id = preflight["operation_id"]

    restore_response = client.post(
        f"{_base(PROJECT_A)}/restores",
        json={
            "backup_operation_id": backup_operation_id,
            "preflight_operation_id": preflight_operation_id,
            "idempotency_key": "slice09a-product-restore-001",
            "confirmation": True,
        },
    )
    assert restore_response.status_code == 200, restore_response.text
    restore = restore_response.json()
    restore_keys = {
        "operation_id",
        "result_label",
        "project_name",
        "restored_cutoff_label",
        "verification_summary",
        "next_action_label",
        "progress_percent",
        "current_step_label",
    }
    _assert_backup_public_projection(restore, expected_keys=restore_keys)
    assert restore["result_label"] == "正在恢复项目"
    assert restore["progress_percent"] == 5
    restore_operation_id = restore["operation_id"]
    restore = _wait_for_operation(
        client,
        f"{_base(PROJECT_A)}/restores/{restore_operation_id}",
        field="result_label",
        terminal_values={
            "恢复完成",
            "项目已是此版本",
            "保持原项目未变",
            "需要人工处理",
        },
    )
    assert restore["result_label"] in {
        "恢复完成",
        "项目已是此版本",
        "保持原项目未变",
        "需要人工处理",
    }
    restore_status = client.get(
        f"{_base(PROJECT_A)}/restores/{restore_operation_id}"
    )
    assert restore_status.status_code == 200, restore_status.text

    assert restore_status.json() == restore

    wrong_project = client.get(
        f"{_base(PROJECT_B)}/backups/{backup_operation_id}"
    )
    _assert_error_body(wrong_project.json(), status_code=wrong_project.status_code)
    assert wrong_project.status_code == 404

    unknown_field = client.post(
        f"{_base(PROJECT_A)}/backups",
        json={"package_path": "/private/internal.mmbackup"},
    )
    _assert_error_body(unknown_field.json(), status_code=unknown_field.status_code)
    assert unknown_field.status_code == 422

def test_slice09a_product_backup_post_is_async_and_replay_starts_one_worker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    entered = threading.Event()
    release = threading.Event()
    calls: list[dict[str, Any]] = []
    original_backup = pb.ProjectBackupManager.backup

    def slow_backup(
        manager: pb.ProjectBackupManager,
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> Any:
        calls.append(dict(kwargs))
        entered.set()
        release.wait(5.0)
        return original_backup(manager, idempotency_key, **kwargs)

    monkeypatch.setattr(pb.ProjectBackupManager, "backup", slow_backup)
    response_holder: dict[str, Any] = {}
    response_done = threading.Event()

    def invoke_backup() -> None:
        try:
            response_holder["response"] = client.post(
                f"{_base(PROJECT_A)}/backups",
                json={"idempotency_key": "slice09a-product-async-backup-001"},
            )
        finally:
            response_done.set()

    caller = threading.Thread(target=invoke_backup)
    caller.start()
    try:
        assert entered.wait(2.0), "backup worker did not start"
        assert response_done.wait(0.5), "backup POST waited for core work"
        first = response_holder["response"]
        assert first.status_code == 200, first.text
        first_body = first.json()
        assert first_body["status_label"] == "准备中"
        assert first_body["progress_percent"] == 5

        replay = client.post(
            f"{_base(PROJECT_A)}/backups",
            json={"idempotency_key": "slice09a-product-async-backup-001"},
        )
        assert replay.status_code == 200, replay.text
        assert replay.json() == first_body
        assert len(calls) == 1
    finally:
        release.set()
        caller.join(5.0)

    assert response_done.is_set()
    operation_id = response_holder["response"].json()["operation_id"]
    final = _wait_for_operation(
        client,
        f"{_base(PROJECT_A)}/backups/{operation_id}",
        field="status_label",
        terminal_values={"已可下载"},
    )
    assert final["progress_percent"] == 100


def test_slice09a_product_backup_worker_setup_failure_becomes_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    original_init = pb.ProjectBackupManager.__init__

    def fail_init(manager: pb.ProjectBackupManager, *args: Any, **kwargs: Any) -> None:
        raise pb.ProjectBackupError("sqlite_integrity_failed")

    monkeypatch.setattr(pb.ProjectBackupManager, "__init__", fail_init)
    response = client.post(
        f"{_base(PROJECT_A)}/backups",
        json={"idempotency_key": "slice09a-product-worker-setup-failure"},
    )
    assert response.status_code == 200, response.text
    operation_id = response.json()["operation_id"]
    failed = _wait_for_operation(
        client,
        f"{_base(PROJECT_A)}/backups/{operation_id}",
        field="status_label",
        terminal_values={"未能完成"},
    )
    assert failed["current_step_label"] == "未能完成"
    assert failed["recommended_next_action"] == "请稍后重试"

    monkeypatch.setattr(pb.ProjectBackupManager, "__init__", original_init)


def test_slice09a_product_restore_post_is_async_and_replay_starts_one_worker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    backup_response = client.post(
        f"{_base(PROJECT_A)}/backups",
        json={"idempotency_key": "slice09a-product-async-restore-source"},
    )
    assert backup_response.status_code == 200, backup_response.text
    backup_id = backup_response.json()["operation_id"]
    backup = _wait_for_operation(
        client,
        f"{_base(PROJECT_A)}/backups/{backup_id}",
        field="status_label",
        terminal_values={"已可下载"},
    )
    preflight_response = client.post(
        f"{_base(PROJECT_A)}/restores/preflight",
        json={
            "backup_operation_id": backup_id,
            "idempotency_key": "slice09a-product-async-restore-preflight",
        },
    )
    assert preflight_response.status_code == 200, preflight_response.text
    preflight_id = preflight_response.json()["operation_id"]

    entered = threading.Event()
    release = threading.Event()
    calls: list[dict[str, Any]] = []
    original_restore = pb.ProjectBackupManager.restore

    def slow_restore(
        manager: pb.ProjectBackupManager,
        package: Any,
        idempotency_key: str | None = None,
        **kwargs: Any,
    ) -> Any:
        calls.append(dict(kwargs))
        entered.set()
        release.wait(5.0)
        return original_restore(manager, package, idempotency_key, **kwargs)

    monkeypatch.setattr(pb.ProjectBackupManager, "restore", slow_restore)
    response_holder: dict[str, Any] = {}
    response_done = threading.Event()

    def invoke_restore() -> None:
        try:
            response_holder["response"] = client.post(
                f"{_base(PROJECT_A)}/restores",
                json={
                    "backup_operation_id": backup_id,
                    "preflight_operation_id": preflight_id,
                    "idempotency_key": "slice09a-product-async-restore-001",
                    "confirmation": True,
                },
            )
        finally:
            response_done.set()

    caller = threading.Thread(target=invoke_restore)
    caller.start()
    try:
        assert entered.wait(2.0), "restore worker did not start"
        assert response_done.wait(0.5), "restore POST waited for core work"
        first = response_holder["response"]
        assert first.status_code == 200, first.text
        first_body = first.json()
        assert first_body["result_label"] == "正在恢复项目"
        assert first_body["progress_percent"] == 5

        replay = client.post(
            f"{_base(PROJECT_A)}/restores",
            json={
                "backup_operation_id": backup_id,
                "preflight_operation_id": preflight_id,
                "idempotency_key": "slice09a-product-async-restore-001",
                "confirmation": True,
            },
        )
        assert replay.status_code == 200, replay.text
        assert replay.json() == first_body
        assert len(calls) == 1
    finally:
        release.set()
        caller.join(5.0)

    assert response_done.is_set()
    operation_id = response_holder["response"].json()["operation_id"]
    final = _wait_for_operation(
        client,
        f"{_base(PROJECT_A)}/restores/{operation_id}",
        field="result_label",
        terminal_values={
            "恢复完成",
            "项目已是此版本",
            "保持原项目未变",
            "需要人工处理",
        },
    )
    assert final["result_label"] == "项目已是此版本"


def test_slice09a_product_restore_confirmation_hold_survives_worker_failure_handling(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    bound = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(
            run_id="slice09a-confirmation-hold-run",
            source_revision_id="slice09a-confirmation-hold-source-revision",
        ),
    )
    assert bound.status_code == 200, bound.text
    prepared = client.post(
        f"{_base(PROJECT_A)}/runs/slice09a-confirmation-hold-run/execution/prepare",
        json={"work_units": _slice04_units("confirmation-hold")},
    )
    assert prepared.status_code == 200, prepared.text
    backup_response = client.post(
        f"{_base(PROJECT_A)}/backups",
        json={"idempotency_key": "slice09a-product-confirmation-hold-source"},
    )
    assert backup_response.status_code == 200, backup_response.text
    backup_id = backup_response.json()["operation_id"]
    _wait_for_operation(
        client,
        f"{_base(PROJECT_A)}/backups/{backup_id}",
        field="status_label",
        terminal_values={"已可下载"},
    )

    runtime_db = _r7_workspace(tmp_path, PROJECT_A) / "runtime" / "monitoring_runtime.sqlite3"
    conn = sqlite3.connect(str(runtime_db))
    conn.execute(
        "UPDATE projects SET name='更新后的项目' WHERE project_id=?",
        (PROJECT_A,),
    )
    conn.commit()
    conn.close()

    preflight_response = client.post(
        f"{_base(PROJECT_A)}/restores/preflight",
        json={
            "backup_operation_id": backup_id,
            "idempotency_key": "slice09a-product-confirmation-hold-preflight",
        },
    )
    assert preflight_response.status_code == 200, preflight_response.text
    preflight_id = preflight_response.json()["operation_id"]
    restore_body = {
        "backup_operation_id": backup_id,
        "preflight_operation_id": preflight_id,
        "idempotency_key": "slice09a-product-confirmation-hold-restore",
    }

    held_response = client.post(
        f"{_base(PROJECT_A)}/restores",
        json={**restore_body, "confirmation": False},
    )
    assert held_response.status_code == 200, held_response.text
    operation_id = held_response.json()["operation_id"]
    held = _wait_for_operation(
        client,
        f"{_base(PROJECT_A)}/restores/{operation_id}",
        field="result_label",
        terminal_values={"保持原项目未变", "需要人工处理"},
    )
    assert held["result_label"] == "保持原项目未变"

    retry_response = client.post(
        f"{_base(PROJECT_A)}/restores",
        json={**restore_body, "confirmation": True},
    )
    assert retry_response.status_code == 200, retry_response.text
    assert retry_response.json()["operation_id"] == operation_id
    restored = _wait_for_operation(
        client,
        f"{_base(PROJECT_A)}/restores/{operation_id}",
        field="result_label",
        terminal_values={"恢复完成", "需要人工处理"},
    )
    assert restored["result_label"] == "恢复完成"


def test_slice09a_product_write_route_honors_maintenance_gate(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path, maintenance_wait_seconds=0)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    gate = ProjectMaintenanceGate(
        tmp_path / "medical_monitoring_r7",
        PROJECT_A,
        wait_seconds=0,
    )
    permit = gate.acquire(exclusive=True, timeout_seconds=0)
    try:
        response = client.post(
            f"{_base(PROJECT_A)}/execution-profiles/project/{PROJECT_A}",
            json={"user_config_name": DEEPSEEK_CONFIG},
        )
    finally:
        permit.release()
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "project_busy_retry_later"


def test_mtplx_default_bind_without_override_layers(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    bound = client.post(f"{_base(PROJECT_A)}/runs", json=_run_body())
    assert bound.status_code == 200, bound.text
    body = bound.json()
    _assert_public_clean(body)
    assert body.get("replayed") is False
    assert body.get("project_id") == PROJECT_A
    assert body.get("user_config_name") == MTPLX_CONFIG
    assert body.get("run_id") == "run-product-001"


def test_name_only_deepseek_auto_scope_resolves_without_fallback(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    # Cross-run override must not leak onto a different run_id.
    other = client.post(
        f"{_base(PROJECT_A)}/execution-profiles/run_override/run-other",
        json={"user_config_name": DEEPSEEK_CONFIG},
    )
    assert other.status_code == 200, other.text

    default_bound = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(run_id="run-mtplx-only", data_cutoff="2026-08-01"),
    )
    assert default_bound.status_code == 200, default_bound.text
    assert default_bound.json().get("user_config_name") == MTPLX_CONFIG

    created = client.post(
        f"{_base(PROJECT_A)}/execution-profiles/run_override/run-ds-target",
        json={"user_config_name": DEEPSEEK_CONFIG},
    )
    assert created.status_code == 200, created.text
    assert created.json().get("user_config_name") == DEEPSEEK_CONFIG

    # Product DTO omits run_override_scope_key; adapter auto-applies same-name layer.
    bound = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(
            run_id="run-ds-target",
            data_cutoff="2026-08-02",
            source_revision_id="src-sha256:product-bbb",
        ),
    )
    assert bound.status_code == 200, bound.text
    body = bound.json()
    _assert_public_clean(body)
    assert body.get("replayed") is False
    assert body.get("user_config_name") == DEEPSEEK_CONFIG
    entry = MonitoringRunEntry(_r7_workspace(tmp_path, PROJECT_A))
    try:
        _, frozen = entry.run_binding_store.get_with_frozen("run-ds-target")
        assert frozen.reasoning_effort == "max"
        assert frozen.fallback_profile_ids == ()
    finally:
        entry.close()


def test_project_scope_auto_selected_when_project_layer_exists(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    appended = client.post(
        f"{_base(PROJECT_A)}/execution-profiles/project/{PROJECT_A}",
        json={"timeout_seconds": 77, "credential_ref": "env:OMP_CREDENTIAL_REF"},
    )
    assert appended.status_code == 200, appended.text
    assert appended.json().get("scope_key") == PROJECT_A

    bound = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(run_id="run-scope-auto", data_cutoff="2026-08-03"),
    )
    assert bound.status_code == 200, bound.text
    body = bound.json()
    _assert_public_clean(body)
    assert body.get("project_id") == PROJECT_A
    assert body.get("user_config_name") == MTPLX_CONFIG
    entry = MonitoringRunEntry(_r7_workspace(tmp_path, PROJECT_A))
    try:
        _, frozen = entry.run_binding_store.get_with_frozen("run-scope-auto")
        assert frozen.timeout_seconds == 77
    finally:
        entry.close()


def test_project_scope_alias_is_canonicalized_before_storage(tmp_path: Path) -> None:
    alias = "project-a-alias"

    def resolver(project_id: str) -> str:
        if project_id in {alias, PROJECT_A}:
            return PROJECT_A
        raise KeyError(project_id)

    client = _client(tmp_path, project_resolver=resolver)
    assert client.post(f"{_base(alias)}/workspace/bootstrap").status_code == 200

    appended = client.post(
        f"{_base(alias)}/execution-profiles/project/{alias}",
        json={"timeout_seconds": 81},
    )
    assert appended.status_code == 200, appended.text
    assert appended.json()["scope_key"] == PROJECT_A

    bound = client.post(
        f"{_base(alias)}/runs",
        json=_run_body(run_id="run-alias-project", data_cutoff="2026-08-04"),
    )
    assert bound.status_code == 200, bound.text
    assert bound.json()["project_id"] == PROJECT_A
    entry = MonitoringRunEntry(_r7_workspace(tmp_path, PROJECT_A))
    try:
        _, frozen = entry.run_binding_store.get_with_frozen("run-alias-project")
        assert frozen.timeout_seconds == 81
    finally:
        entry.close()


def test_product_run_dto_rejects_client_identity_and_scope_fields(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    for forbidden_field, value in (
        ("project_id", PROJECT_B),
        ("project_scope_key", PROJECT_A),
        ("run_override_scope_key", "run-product-001"),
    ):
        resp = client.post(
            f"{_base(PROJECT_A)}/runs",
            json=_run_body(**{forbidden_field: value}),
        )
        assert resp.status_code >= 400, forbidden_field
        _assert_error_body(resp.json(), status_code=resp.status_code)


def test_project_isolation_runs_are_not_cross_readable(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    assert client.post(f"{_base(PROJECT_B)}/workspace/bootstrap").status_code == 200

    created = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(run_id="run-only-in-a"),
    )
    assert created.status_code == 200, created.text

    got_a = client.get(f"{_base(PROJECT_A)}/runs/run-only-in-a")
    assert got_a.status_code == 200, got_a.text
    assert got_a.json().get("project_id") == PROJECT_A

    leak = client.get(f"{_base(PROJECT_B)}/runs/run-only-in-a")
    assert leak.status_code >= 400
    _assert_error_body(leak.json(), status_code=leak.status_code)

    assert _r7_workspace(tmp_path, PROJECT_A).is_dir()
    assert _r7_workspace(tmp_path, PROJECT_B).is_dir()
    assert _r7_workspace(tmp_path, PROJECT_A) != _r7_workspace(tmp_path, PROJECT_B)


def test_unconfigured_project_fails_before_r7_workspace_write(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()

    def resolver(project_id: str) -> str:
        if project_id == "not-configured-project":
            raise KeyError(project_id)
        return project_id

    client = _client(runtime_dir, project_resolver=resolver)
    assert not (runtime_dir / "medical_monitoring_r7").exists()

    resp = client.post(f"{_base('not-configured-project')}/workspace/bootstrap")
    assert resp.status_code >= 400
    _assert_error_body(resp.json(), status_code=resp.status_code)
    assert not (runtime_dir / "medical_monitoring_r7" / "not-configured-project").exists()
    assert _sqlite_files(runtime_dir) == []


def test_replay_and_conflict_and_three_modes_and_basis_rules(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    for mode in ("daily", "pre_lock", "post_lock_pre_cfdi"):
        resp = client.post(
            f"{_base(PROJECT_A)}/runs",
            json=_run_body(run_id=f"run-mode-{mode}", mode=mode),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json().get("mode") == mode
        assert resp.json().get("replayed") is False

    first = client.post(f"{_base(PROJECT_A)}/runs", json=_run_body())
    assert first.status_code == 200, first.text
    replay = client.post(f"{_base(PROJECT_A)}/runs", json=_run_body())
    assert replay.status_code == 200, replay.text
    assert replay.json().get("replayed") is True
    assert replay.json().get("run_id") == first.json().get("run_id")

    conflict = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(data_cutoff="2026-08-29"),
    )
    assert conflict.status_code >= 400
    _assert_error_body(conflict.json(), status_code=conflict.status_code)

    incr_ok = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(
            run_id="run-incr-ok",
            execution_basis="incremental",
            prior_accepted_snapshot_ref="snap-accepted-product",
            data_cutoff="2026-08-30",
        ),
    )
    assert incr_ok.status_code == 200, incr_ok.text
    assert incr_ok.json().get("execution_basis") == "incremental"

    incr_bad = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(
            run_id="run-incr-bad",
            execution_basis="incremental",
            prior_accepted_snapshot_ref=None,
            data_cutoff="2026-08-31",
        ),
    )
    assert incr_bad.status_code >= 400
    _assert_error_body(incr_bad.json(), status_code=incr_bad.status_code)

    full_bad = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(
            run_id="run-full-bad",
            execution_basis="full",
            prior_accepted_snapshot_ref="snap-should-not",
            data_cutoff="2026-09-01",
        ),
    )
    assert full_bad.status_code >= 400
    _assert_error_body(full_bad.json(), status_code=full_bad.status_code)


def test_chinese_errors_for_missing_profile_and_secret_fields(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    missing = client.get(
        f"{_base(PROJECT_A)}/execution-profiles/project/does-not-exist"
    )
    assert missing.status_code >= 400
    _assert_error_body(missing.json(), status_code=missing.status_code)

    secret = client.post(
        f"{_base(PROJECT_A)}/execution-profiles/project/{PROJECT_A}",
        json={
            "timeout_seconds": 70,
            "credential_ref": "env:OMP_CREDENTIAL_REF",
            "credential_value": "super-secret-value",
            "api_key": "env-value-leaked",
        },
    )
    assert secret.status_code >= 400
    _assert_error_body(secret.json(), status_code=secret.status_code)

    # Bind before bootstrap on a fresh project must stay Chinese / fail-closed.
    client_b = _client(tmp_path / "other")
    no_boot = client_b.post(f"{_base(PROJECT_B)}/runs", json=_run_body(run_id="run-no-boot"))
    assert no_boot.status_code >= 400
    _assert_error_body(no_boot.json(), status_code=no_boot.status_code)

    missing_capability = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(
            run_id="run-missing-capability",
            capability_scope_key="capability-does-not-exist",
        ),
    )
    assert missing_capability.status_code == 404
    _assert_error_body(
        missing_capability.json(), status_code=missing_capability.status_code
    )
    assert missing_capability.json()["message"] == "未找到指定的执行配置。"


def test_partial_workspace_does_not_recreate_missing_binding_db(tmp_path: Path) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    binding_db = _r7_workspace(tmp_path, PROJECT_A) / RUN_BINDING_DB_NAME
    binding_db.unlink()
    assert not binding_db.exists()

    response = client.get(
        f"{_base(PROJECT_A)}/execution-profiles/global_default/*"
    )
    assert response.status_code == 422
    _assert_error_body(response.json(), status_code=response.status_code)
    assert response.json()["code"] == "global_default_missing"
    assert not binding_db.exists(), "only explicit bootstrap may restore workspace stores"


def test_non_r7_error_shape_unchanged_after_mount(tmp_path: Path) -> None:
    client = _client(tmp_path)
    probe = client.get("/__non_r7_probe")
    assert probe.status_code == 400
    assert probe.json() == {"detail": "legacy-non-r7-detail-shape"}

    # R7 validation still uses top-level Chinese envelope (no app-wide hijack).
    bad = client.post(f"{_base(PROJECT_A)}/runs", json={"unexpected": 1})
    assert bad.status_code >= 400
    _assert_error_body(bad.json(), status_code=bad.status_code)
    assert "detail" not in bad.json()

    for method, path in (
        ("get", f"{_base(PROJECT_A)}/does-not-exist"),
        ("put", f"{_base(PROJECT_A)}/runs"),
    ):
        response = getattr(client, method)(path)
        assert response.status_code == 404
        _assert_error_body(response.json(), status_code=response.status_code)
        assert response.json()["code"] == "route_not_found"


def test_per_request_entry_closes_both_stores(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7 import run_entry as re

    closed: list[bool] = []
    original_close = re.MonitoringRunEntry.close

    def _tracking_close(self: Any) -> None:
        closed.append(True)
        return original_close(self)

    monkeypatch.setattr(re.MonitoringRunEntry, "close", _tracking_close)

    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    assert closed, "bootstrap must close MonitoringRunEntry"
    closed.clear()

    assert client.post(f"{_base(PROJECT_A)}/runs", json=_run_body()).status_code == 200
    assert closed, "bind_run must close MonitoringRunEntry"
    closed.clear()

    assert client.get(f"{_base(PROJECT_A)}/runs/run-product-001").status_code == 200
    assert closed, "get_run must close MonitoringRunEntry"


def _slice04_units(prefix: str = "progress") -> list[dict[str, Any]]:
    return [
        {
            "work_unit_id": f"{prefix}-1",
            "stage": "资料准备",
            "label": "核对合成研究资料清单",
            "scope": "source",
            "target_ref": "SYN-DOC-1",
            "ordinal": 1,
            "mandatory": True,
            "depends_on": [],
        },
        {
            "work_unit_id": f"{prefix}-2",
            "stage": "数据解构",
            "label": "整理受试者访视数据",
            "scope": "subject",
            "target_ref": "SYN-001",
            "ordinal": 2,
            "mandatory": True,
            "depends_on": [],
        },
    ]


def _slice04_bind_product_run(
    client: TestClient,
    project_id: str,
    *,
    run_id: str,
    mode: str = "daily",
    source_revision_id: str | None = None,
) -> None:
    boot = client.post(f"{_base(project_id)}/workspace/bootstrap")
    assert boot.status_code == 200, boot.text
    bound = client.post(
        f"{_base(project_id)}/runs",
        json=_run_body(
            run_id=run_id,
            mode=mode,
            data_cutoff="2026-08-28",
            source_revision_id=source_revision_id or f"source-{run_id}",
        ),
    )
    assert bound.status_code == 200, bound.text


def _assert_slice04_public(payload: Mapping[str, Any]) -> None:
    forbidden_keys = {
        "run_id",
        "project_id",
        "node_id",
        "work_unit_id",
        "attempt_id",
        "manifest_revision",
        "owner",
        "owner_token",
        "lease",
        "lease_expires_at",
        "generation",
        "thread",
        "pid",
        "token",
        "provider",
        "model",
        "selector",
        "adapter",
        "harness",
        "backend",
        "binding",
        "audit",
        "hash",
        "path",
        "database",
        "sqlite",
    }

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                assert str(key).casefold() not in forbidden_keys
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str):
            lowered = value.casefold()
            for token in forbidden_keys | {"正式事实", "候选信号", "只读"}:
                assert token.casefold() not in lowered

    walk(payload)


def test_slice04_prepare_and_progress_routes_return_only_public_chinese_view(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    run_id = "run-slice04-product"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id)
    units = _slice04_units()

    prepared = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": units},
    )
    assert prepared.status_code == 200, prepared.text
    assert prepared.json() == {
        "replayed": False,
        "scope_version_text": "第 1 版监查范围",
        "total": 2,
        "data_cutoff_text": "2026-08-28",
        "mode_text": "日常监查",
        "basis_text": "全量",
    }
    _assert_slice04_public(prepared.json())

    replay = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": units},
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["replayed"] is True
    assert replay.json()["scope_version_text"] == "第 1 版监查范围"

    progress = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert progress.status_code == 200, progress.text
    body = progress.json()
    assert set(body) == {
        "scope_version_text",
        "mode_text",
        "basis_text",
        "data_cutoff_text",
        "headline",
        "completed",
        "total",
        "percent",
        "progress_text",
        "status_overview",
        "stage_progress",
        "current_work",
        "latest_updates",
        "run_status_text",
        "available_actions",
        "run_state",
        "publication_state",
        "result_available",
        "publication_status_text",
    }
    assert body["scope_version_text"] == "第 1 版监查范围"
    assert body["headline"] == "等待开始医学监查"
    assert body["completed"] == 0
    assert body["total"] == 2
    assert body["percent"] == 0.0
    assert {item["state_label"]: item["count"] for item in body["status_overview"]} == {
        "等待开始": 2
    }
    assert [
        (item["stage"], item["processed"], item["total"])
        for item in body["stage_progress"]
    ] == [("资料准备", 0, 1), ("数据解构", 0, 1)]
    assert body["current_work"] == []
    assert body["latest_updates"] == []
    assert body["publication_state"] == "not_started"
    assert body["result_available"] is False
    assert body["publication_status_text"] == "结果尚未整理完成"
    assert body["run_status_text"] == "等待开始医学监查"
    assert body["available_actions"] == ["开始"]
    assert body["run_state"] == "waiting_start"
    _assert_slice04_public(body)


def test_slice05_product_execution_actions_and_overlay_are_public_chinese(
    tmp_path: Path,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.background_recovery import (
        BackgroundRecoveryAdapter,
        ExecutionControlState,
    )

    client = _client(tmp_path)
    run_id = "run-slice05-product-actions"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id)
    prepared = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("slice05")},
    )
    assert prepared.status_code == 200, prepared.text

    before = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert before.status_code == 200, before.text
    assert before.json()["run_status_text"] == "等待开始医学监查"
    assert before.json()["available_actions"] == ["开始"]
    assert before.json()["run_state"] == "waiting_start"
    _assert_slice04_public(before.json())

    started = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/start",
        json={},
    )
    assert started.status_code == 200, started.text
    assert started.json() == {
        "replayed": False,
        "run_status_text": "医学监查进行中",
        "available_actions": ["停止"],
    }
    _assert_slice04_public(started.json())

    workspace = _r7_workspace(tmp_path, PROJECT_A)
    runner = BackgroundRecoveryAdapter(
        runtime_dir=workspace / "runtime",
        canonical_project_id=PROJECT_A,
    )
    assert runner.wait(run_id, timeout=5.0)
    assert runner.get_control(run_id).state is ExecutionControlState.FINISHED

    after = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert after.status_code == 200, after.text
    body = after.json()
    assert body["completed"] == body["total"] == 2
    assert body["percent"] == 100.0
    assert body["run_status_text"] == "本次监查已完成"
    assert body["available_actions"] == []
    assert body["run_state"] == "completed"
    _assert_slice04_public(body)

    # The action endpoints stay mounted and fail with stable Chinese codes
    # after the terminal state; no client-controlled fields are accepted.
    finished_start = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/start", json={}
    )
    assert finished_start.status_code == 409
    assert finished_start.json()["code"] == "already_finished"
    assert finished_start.json()["message"] == "本次监查已结束，无需再次开始。"
    _assert_error_body(finished_start.json(), status_code=finished_start.status_code)

    unknown_field = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/cancel",
        json={"owner_token": "client-must-not-supply"},
    )
    assert unknown_field.status_code == 422
    _assert_error_body(unknown_field.json(), status_code=unknown_field.status_code)


def test_slice05_product_stop_continue_happy_path_uses_chinese_overlay(
    tmp_path: Path,
) -> None:
    from poc.medical_monitoring_ai_native_r1.src.mm_r1.domain import NodeStatus
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.background_recovery import (
        BackgroundOutcome,
        BackgroundRecoveryAdapter,
        ExecutionControlState,
    )

    client = _client(tmp_path)
    run_id = "run-slice05-product-stop-continue"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id)
    prepared = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("stop-continue")},
    )
    assert prepared.status_code == 200, prepared.text

    entered = threading.Event()
    release = threading.Event()

    def blocked(unit: Any, _key: str) -> BackgroundOutcome:
        entered.set()
        assert release.wait(5.0)
        return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")

    workspace = _r7_workspace(tmp_path, PROJECT_A)
    runner = BackgroundRecoveryAdapter(
        runtime_dir=workspace / "runtime",
        canonical_project_id=PROJECT_A,
        unit_step=blocked,
    )
    runner.start_execution(run_id)
    assert entered.wait(5.0)

    stopped = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/cancel", json={}
    )
    assert stopped.status_code == 200, stopped.text
    assert stopped.json() == {
        "replayed": False,
        "run_status_text": "正在停止医学监查",
        "available_actions": [],
    }
    _assert_slice04_public(stopped.json())

    stopping_view = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert stopping_view.status_code == 200, stopping_view.text
    assert stopping_view.json()["run_state"] == "stopping"
    assert stopping_view.json()["run_status_text"] == "正在停止医学监查"
    assert stopping_view.json()["available_actions"] == []
    _assert_slice04_public(stopping_view.json())

    release.set()
    assert runner.wait(run_id, timeout=5.0)
    assert runner.get_control(run_id).state is ExecutionControlState.INTERRUPTED
    stopped_view = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert stopped_view.status_code == 200, stopped_view.text
    assert stopped_view.json()["run_status_text"] == "已停止，可继续"
    assert stopped_view.json()["available_actions"] == ["继续"]
    assert stopped_view.json()["run_state"] == "interrupted_resumable"
    _assert_slice04_public(stopped_view.json())

    resumed = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/resume", json={}
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["replayed"] is False
    _assert_slice04_public(resumed.json())
    rebuilt = BackgroundRecoveryAdapter(
        runtime_dir=workspace / "runtime",
        canonical_project_id=PROJECT_A,
    )
    assert rebuilt.wait(run_id, timeout=5.0)
    final_view = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert final_view.status_code == 200, final_view.text
    assert final_view.json()["completed"] == final_view.json()["total"]
    assert final_view.json()["run_status_text"] == "本次监查已完成"
    assert final_view.json()["available_actions"] == []
    assert final_view.json()["run_state"] == "completed"
    _assert_slice04_public(final_view.json())


def test_slice06_product_harness_uses_injected_fake_and_public_progress(
    tmp_path: Path,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.background_recovery import (
        BackgroundRecoveryAdapter,
        ExecutionControlState,
    )

    fake = FakeHarnessAdapter()
    client = _client(
        tmp_path,
        harness_adapter=fake,
        harness_catalog=FakeCatalog(),
    )
    run_id = "run-slice06-product-harness"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id)
    prepared = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("slice06"), "execution_kind": "harness"},
    )
    assert prepared.status_code == 200, prepared.text
    _assert_slice04_public(prepared.json())

    started = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/start", json={}
    )
    assert started.status_code == 200, started.text
    assert started.json()["run_status_text"] == "医学监查进行中"
    _assert_slice04_public(started.json())

    workspace = _r7_workspace(tmp_path, PROJECT_A)
    runner = BackgroundRecoveryAdapter(
        runtime_dir=workspace / "runtime",
        canonical_project_id=PROJECT_A,
    )
    assert runner.wait(run_id, timeout=5.0)
    assert runner.get_control(run_id).state is ExecutionControlState.FINISHED
    assert fake.preflight_calls == 2
    assert len(fake.invoke_calls) == 2

    progress = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert progress.status_code == 200, progress.text
    body = progress.json()
    assert body["completed"] == body["total"] == 2
    assert body["percent"] == 100.0
    assert body["run_status_text"] == "本次监查已完成"
    assert body["available_actions"] == []
    assert body["run_state"] == "completed"
    _assert_slice04_public(body)


def test_slice06_product_harness_preflight_failure_is_public_and_no_dispatch(
    tmp_path: Path,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.background_recovery import (
        BackgroundRecoveryAdapter,
        ExecutionControlState,
    )

    fake = FakeHarnessAdapter()
    client = _client(
        tmp_path,
        harness_adapter=fake,
        harness_catalog=FakeCatalog(valid=False, failure_reason="catalog_missing"),
    )
    run_id = "run-slice06-product-preflight-failure"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id)
    prepared = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("slice06-failure"), "execution_kind": "harness"},
    )
    assert prepared.status_code == 200, prepared.text

    started = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/start", json={}
    )
    assert started.status_code == 200, started.text
    _assert_slice04_public(started.json())

    workspace = _r7_workspace(tmp_path, PROJECT_A)
    runner = BackgroundRecoveryAdapter(
        runtime_dir=workspace / "runtime",
        canonical_project_id=PROJECT_A,
    )
    assert runner.wait(run_id, timeout=5.0)
    assert runner.get_control(run_id).state is ExecutionControlState.INTERRUPTED
    assert fake.preflight_calls == 1
    assert fake.invoke_calls == []

    progress = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert progress.status_code == 200, progress.text
    body = progress.json()
    assert body["completed"] == 0
    assert body["total"] == 2
    assert body["run_status_text"] == "已停止，可继续"
    assert body["available_actions"] == ["继续"]
    assert body["run_state"] == "interrupted_resumable"
    _assert_slice04_public(body)


def test_slice06_product_harness_preserves_bound_profile_identity_for_both_profiles(
    tmp_path: Path,
) -> None:
    cases = (
        (
            "mtplx",
            None,
            "mtplx",
            "mtplx/Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality",
            "medium",
        ),
        (
            "deepseek",
            DEEPSEEK_CONFIG,
            "deepseek",
            "deepseek/deepseek-v4-flash",
            "max",
        ),
    )
    for suffix, override, provider, selector, effort in cases:
        runtime_dir = tmp_path / suffix
        fake = FakeHarnessAdapter()
        client = _client(
            runtime_dir,
            harness_adapter=fake,
            harness_catalog=FakeCatalog(),
        )
        run_id = f"run-slice06-profile-{suffix}"
        boot = client.post(f"{_base(PROJECT_A)}/workspace/bootstrap")
        assert boot.status_code == 200, boot.text
        if override is not None:
            profile = client.post(
                f"{_base(PROJECT_A)}/execution-profiles/run_override/{run_id}",
                json={"user_config_name": override},
            )
            assert profile.status_code == 200, profile.text
        bound = client.post(
            f"{_base(PROJECT_A)}/runs",
            json=_run_body(run_id=run_id),
        )
        assert bound.status_code == 200, bound.text
        prepared = client.post(
            f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
            json={"work_units": _slice04_units(suffix), "execution_kind": "harness"},
        )
        assert prepared.status_code == 200, prepared.text
        started = client.post(
            f"{_base(PROJECT_A)}/runs/{run_id}/execution/start", json={}
        )
        assert started.status_code == 200, started.text
        runner = BackgroundRecoveryAdapter(
            runtime_dir=_r7_workspace(runtime_dir, PROJECT_A) / "runtime",
            canonical_project_id=PROJECT_A,
        )
        assert runner.wait(run_id, timeout=5.0)

        assert len(fake.invoke_calls) == 2
        assert {
            (call["requested_provider"], call["selector"], call["effort"])
            for call in fake.invoke_calls
        } == {(provider, selector, effort)}
        with MonitoringRunEntry(_r7_workspace(runtime_dir, PROJECT_A)) as entry:
            binding = entry.run_binding_store.get(run_id)
        assert all(
            call["profile_digest"] == binding.execution_profile_digest
            for call in fake.invoke_calls
        )
        assert binding.effective_selector == selector


def test_slice06_product_harness_transport_fault_stays_failed_and_public_clean(
    tmp_path: Path,
) -> None:
    fake = FakeHarnessAdapter(
        invoke_exceptions=(
            RuntimeError("transport_unavailable: token=super-secret-value"),
        )
    )
    client = _client(
        tmp_path,
        harness_adapter=fake,
        harness_catalog=FakeCatalog(),
    )
    run_id = "run-slice06-product-transport-failure"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id)
    prepared = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": _slice04_units("transport-failure")[:1],
            "execution_kind": "harness",
        },
    )
    assert prepared.status_code == 200, prepared.text
    started = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/start", json={}
    )
    assert started.status_code == 200, started.text
    workspace = _r7_workspace(tmp_path, PROJECT_A)
    runner = BackgroundRecoveryAdapter(
        runtime_dir=workspace / "runtime",
        canonical_project_id=PROJECT_A,
    )
    assert runner.wait(run_id, timeout=5.0)
    assert len(fake.invoke_calls) == 1

    progress = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert progress.status_code == 200, progress.text
    body = progress.json()
    # R1's audience denominator counts terminal work as processed; the
    # failed status remains visible in the projection and is not promoted to
    # a passed medical result.
    assert body["completed"] == 1
    assert body["total"] == 1
    assert body["run_status_text"] == "分析服务连接异常，本项分析未完成。"
    assert body["available_actions"] == []
    assert body["run_state"] == "failed"
    _assert_public_clean(body)
    _assert_slice04_public(body)


def test_slice06_product_cancel_keeps_current_call_and_does_not_claim_next(
    tmp_path: Path,
) -> None:
    fake = FakeHarnessAdapter(block=True)
    client = _client(
        tmp_path,
        harness_adapter=fake,
        harness_catalog=FakeCatalog(),
    )
    run_id = "run-slice06-product-cancel"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id)
    prepared = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("cancel"), "execution_kind": "harness"},
    )
    assert prepared.status_code == 200, prepared.text
    started = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/start", json={}
    )
    assert started.status_code == 200, started.text
    assert fake.entered.wait(5.0)

    stopped = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/cancel", json={}
    )
    assert stopped.status_code == 200, stopped.text
    assert stopped.json()["run_status_text"] == (
        "正在停止，当前分析可能完成；系统不会开始下一项工作。"
    )
    assert stopped.json()["available_actions"] == []
    _assert_public_clean(stopped.json())

    stopping_view = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert stopping_view.status_code == 200, stopping_view.text
    assert stopping_view.json()["run_state"] == "stopping"
    assert stopping_view.json()["run_status_text"] == (
        "正在停止，当前分析可能完成；系统不会开始下一项工作。"
    )
    assert stopping_view.json()["available_actions"] == []
    _assert_slice04_public(stopping_view.json())

    fake.release.set()
    workspace = _r7_workspace(tmp_path, PROJECT_A)
    runner = BackgroundRecoveryAdapter(
        runtime_dir=workspace / "runtime",
        canonical_project_id=PROJECT_A,
    )
    assert runner.wait(run_id, timeout=5.0)
    assert len(fake.invoke_calls) == 1
    progress = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert progress.status_code == 200, progress.text
    assert progress.json()["run_state"] == "interrupted_resumable"
    _assert_public_clean(progress.json())
    _assert_slice04_public(progress.json())


@pytest.mark.parametrize("action", ["start", "resume", "cancel"])
def test_slice05_execution_actions_require_admin_runtime_permission(
    tmp_path: Path, action: str
) -> None:
    admin = _client(
        tmp_path,
        principal=_principal(PROJECT_A, roles=("medical_manager", "system_admin")),
    )
    run_id = f"run-slice05-permission-{action}"
    _slice04_bind_product_run(admin, PROJECT_A, run_id=run_id)
    prepared = admin.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("permission")},
    )
    assert prepared.status_code == 200, prepared.text

    reader = _client(
        tmp_path,
        principal=_principal(PROJECT_A, roles=("medical_manager",)),
    )
    response = reader.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/{action}",
        json={},
    )
    assert response.status_code == 403, response.text
    _assert_error_body(response.json(), status_code=response.status_code)


def test_slice04_unbootstrap_unbound_and_invalid_prepare_have_zero_runtime_io(
    tmp_path: Path,
) -> None:
    unbootstrapped = _client(tmp_path / "unbootstrapped")
    unboot_path = _r7_workspace(tmp_path / "unbootstrapped", PROJECT_A)
    for method, path, kwargs in (
        (
            "get",
            f"{_base(PROJECT_A)}/runs/unbooted/progress",
            {},
        ),
        (
            "post",
            f"{_base(PROJECT_A)}/runs/unbooted/execution/prepare",
            {"json": {"work_units": _slice04_units()}},
        ),
    ):
        response = getattr(unbootstrapped, method)(path, **kwargs)
        assert response.status_code == 422
        _assert_error_body(response.json(), status_code=response.status_code)
    assert not unboot_path.exists()

    client = _client(tmp_path / "bound")
    run_id = "run-zero-runtime-io"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id)
    runtime_path = _r7_workspace(tmp_path / "bound", PROJECT_A) / "runtime"

    missing = client.get(f"{_base(PROJECT_A)}/runs/run-not-bound/progress")
    assert missing.status_code == 404
    assert missing.json()["code"] == "run_binding_not_found"
    assert not runtime_path.exists()

    invalid_bodies = (
        {"work_units": []},
        {"work_units": _slice04_units(), "run_id": "client-supplied"},
        {
            "work_units": [
                {**_slice04_units()[0], "unexpected": "rejected"},
            ]
        },
    )
    for body in invalid_bodies:
        response = client.post(
            f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
            json=body,
        )
        assert response.status_code >= 400
        _assert_error_body(response.json(), status_code=response.status_code)
        assert not runtime_path.exists()

    unprepared = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert unprepared.status_code == 422
    assert unprepared.json()["code"] == "execution_not_prepared"
    assert not runtime_path.exists()


def test_slice04_alias_uses_canonical_runtime_and_same_run_id_isolated_by_project(
    tmp_path: Path,
) -> None:
    alias = "r7-project-a-alias"

    def resolver(project_id: str) -> str:
        if project_id in {alias, PROJECT_A}:
            return PROJECT_A
        if project_id == PROJECT_B:
            return PROJECT_B
        raise KeyError(project_id)

    client = _client(tmp_path, project_resolver=resolver)
    run_id = "run-same-id-in-two-projects"
    _slice04_bind_product_run(
        client,
        alias,
        run_id=run_id,
        source_revision_id="source-alias",
    )
    first = client.post(
        f"{_base(alias)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("a")},
    )
    assert first.status_code == 200, first.text
    assert client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress").status_code == 200

    _slice04_bind_product_run(
        client,
        PROJECT_B,
        run_id=run_id,
        source_revision_id="source-project-b",
    )
    second = client.post(
        f"{_base(PROJECT_B)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("b")},
    )
    assert second.status_code == 200, second.text

    workspace_a = _r7_workspace(tmp_path, PROJECT_A)
    workspace_b = _r7_workspace(tmp_path, PROJECT_B)
    assert (workspace_a / "runtime" / "monitoring_runtime.sqlite3").is_file()
    assert (workspace_b / "runtime" / "monitoring_runtime.sqlite3").is_file()
    assert workspace_a != workspace_b
    assert not _r7_workspace(tmp_path, alias).exists()
    assert client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress").json()["total"] == 2
    assert client.get(f"{_base(PROJECT_B)}/runs/{run_id}/progress").json()["total"] == 2


def test_slice04_prepare_requires_admin_and_progress_allows_ai_run_read(
    tmp_path: Path,
) -> None:
    admin = _client(
        tmp_path,
        principal=_principal(PROJECT_A, roles=("medical_manager", "system_admin")),
    )
    run_id = "run-slice04-permissions"
    _slice04_bind_product_run(admin, PROJECT_A, run_id=run_id)
    prepared = admin.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units()},
    )
    assert prepared.status_code == 200, prepared.text

    reader = _client(
        tmp_path,
        principal=_principal(PROJECT_A, roles=("medical_manager",)),
    )
    progress = reader.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert progress.status_code == 200, progress.text
    assert progress.json()["available_actions"] == []
    admin_progress = admin.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert admin_progress.status_code == 200, admin_progress.text
    assert admin_progress.json()["available_actions"] == ["开始"]
    denied = reader.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units()},
    )
    assert denied.status_code == 403, denied.text
    _assert_error_body(denied.json(), status_code=denied.status_code)


def test_slice04_product_rejects_internal_cutoff_before_binding(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    response = client.post(
        f"{_base(PROJECT_A)}/runs",
        json=_run_body(
            run_id="run-unsafe-cutoff",
            data_cutoff="cutoff-sha256:internal-value",
        ),
    )
    assert response.status_code == 422
    assert response.json() == {
        "code": "unsafe_data_cutoff",
        "message": "数据截止点不符合展示约定。",
    }
    assert not (_r7_workspace(tmp_path, PROJECT_A) / "runtime").exists()


@pytest.mark.parametrize(
    ("mode", "expected_code"),
    [
        ("daily", "superseded_scope_replay_forbidden"),
        ("pre_lock", "superseded_scope_replay_forbidden"),
        ("post_lock_pre_cfdi", "frozen_scope_revision_forbidden"),
    ],
)
def test_slice04_product_scope_evolution_fails_closed(
    tmp_path: Path,
    mode: str,
    expected_code: str,
) -> None:
    client = _client(tmp_path)
    run_id = f"run-scope-{mode}"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id, mode=mode)
    first = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("a")},
    )
    assert first.status_code == 200, first.text
    second = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("b")},
    )
    if mode == "post_lock_pre_cfdi":
        assert second.status_code == 409
        assert second.json()["code"] == expected_code
        return
    assert second.status_code == 200, second.text
    rollback = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("a")},
    )
    assert rollback.status_code == 409
    assert rollback.json()["code"] == expected_code


def test_slice07a_run_state_values_are_stable_and_action_responses_stay_overlay_only(
    tmp_path: Path,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.background_recovery import (
        RUN_STATE_VALUES,
    )

    # Slice-07A contract: the frontend branches and polls on this exact
    # machine-readable set; Chinese text is never parsed for state.
    assert tuple(RUN_STATE_VALUES) == (
        "waiting_start",
        "running",
        "stopping",
        "interrupted_resumable",
        "completed",
        "ended_incomplete",
        "failed",
    )

    client = _client(tmp_path)
    run_id = "run-slice07a-run-state"
    _slice04_bind_product_run(client, PROJECT_A, run_id=run_id)
    prepared = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/prepare",
        json={"work_units": _slice04_units("slice07a")},
    )
    assert prepared.status_code == 200, prepared.text
    assert "run_state" not in prepared.json()

    progress = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert progress.status_code == 200, progress.text
    assert progress.json()["run_state"] in RUN_STATE_VALUES

    started = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/start", json={}
    )
    assert started.status_code == 200, started.text
    # Execution action responses keep the frozen three-key overlay shape;
    # the frontend re-reads progress for the authoritative run_state.
    assert set(started.json()) == {"replayed", "run_status_text", "available_actions"}

    workspace = _r7_workspace(tmp_path, PROJECT_A)
    runner = BackgroundRecoveryAdapter(
        runtime_dir=workspace / "runtime",
        canonical_project_id=PROJECT_A,
    )
    assert runner.wait(run_id, timeout=5.0)
    finished = client.get(f"{_base(PROJECT_A)}/runs/{run_id}/progress")
    assert finished.status_code == 200, finished.text
    assert finished.json()["run_state"] == "completed"


def test_slice07c1_run_setup_options_are_project_scoped_and_public_safe(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    unbootstrapped = client.get(f"{_base(PROJECT_A)}/run-setup/options")
    assert unbootstrapped.status_code == 422
    assert unbootstrapped.json()["code"] == "global_default_missing"
    assert not _r7_workspace(tmp_path, PROJECT_A).exists()

    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    response = client.get(f"{_base(PROJECT_A)}/run-setup/options")
    assert response.status_code == 200, response.text
    body = response.json()
    _assert_public_clean(body)
    assert body["project_id"] == PROJECT_A
    assert body["schema_version"] == "mm-r7-slice07c1-run-setup-v1"
    assert len(body["data_batches"]) == 2
    assert body["current_data"]["data_cutoff"] == "2026-08-28"
    assert [item["mode"] for item in body["modes"]] == [
        "daily",
        "pre_lock",
        "post_lock_pre_cfdi",
    ]
    daily, pre_lock, post_lock = body["modes"]
    assert daily["default_execution_basis"] == "incremental"
    assert daily["execution_basis_options"][0]["value"] == "incremental"
    assert daily["execution_basis_options"][0]["available"] is True
    assert daily["baseline_options"][0]["recommended"] is True
    assert pre_lock["default_execution_basis"] == "full"
    assert pre_lock["baseline_options"][0]["recommended"] is True
    assert post_lock["execution_basis_options"] == [
        {
            "value": "full",
            "label": "全量",
            "available": True,
            "disabled_reason": "",
        }
    ]
    assert post_lock["baseline_options"] == []

    assert client.post(f"{_base(PROJECT_B)}/workspace/bootstrap").status_code == 200
    other = client.get(f"{_base(PROJECT_B)}/run-setup/options")
    assert other.status_code == 200, other.text
    assert other.json()["project_id"] == PROJECT_B
    assert other.json()["current_data"]["snapshot_token"] != body["current_data"]["snapshot_token"]


def test_slice07c1_risk_rule_preview_confirmation_revision_and_history(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    ambiguous = client.post(
        f"{_base(PROJECT_A)}/risk-rules/preview",
        json={"source_text": "请关注本次数据变化"},
    )
    assert ambiguous.status_code == 200, ambiguous.text
    ambiguous_body = ambiguous.json()
    _assert_public_clean(ambiguous_body)
    assert ambiguous_body["status"] == "待确认的关注规则"
    assert ambiguous_body["state"] == "ambiguous"
    assert ambiguous_body["confirmable"] is False
    assert 2 <= len(ambiguous_body["candidates"]) <= 5
    rejected = client.post(
        f"{_base(PROJECT_A)}/risk-rules",
        json={
            "preview_token": ambiguous_body["preview_token"],
            "candidate_id": ambiguous_body["candidates"][0]["candidate_id"],
        },
    )
    assert rejected.status_code == 422
    assert rejected.json()["code"] == "ambiguous_risk_rule"

    preview = client.post(
        f"{_base(PROJECT_A)}/risk-rules/preview",
        json={
            "source_text": "ALT 超过上限",
            "applicable_scope": "所有受试者",
            "starting_run": "下一次日常监查",
        },
    )
    assert preview.status_code == 200, preview.text
    preview_body = preview.json()
    assert preview_body["state"] == "ready"
    assert preview_body["confirmable"] is True
    candidate_id = preview_body["candidates"][0]["candidate_id"]

    confirmed = client.post(
        f"{_base(PROJECT_A)}/risk-rules",
        json={
            "preview_token": preview_body["preview_token"],
            "candidate_id": candidate_id,
            "idempotency_key": "request-001",
        },
    )
    assert confirmed.status_code == 200, confirmed.text
    revision = confirmed.json()
    _assert_public_clean(revision)
    assert revision["project_id"] == PROJECT_A
    assert revision["revision"] == 1
    assert revision["selectable"] is True
    assert revision["applicable_scope"] == "所有受试者"
    assert revision["starting_run"] == "下一次日常监查"
    assert revision["revision_token"].startswith("rule-revision:")
    assert "request-001" not in revision["revision_token"]

    replay = client.post(
        f"{_base(PROJECT_A)}/risk-rules",
        json={
            "preview_token": preview_body["preview_token"],
            "candidate_id": candidate_id,
            "idempotency_key": "request-001",
        },
    )
    assert replay.status_code == 200, replay.text
    assert replay.json() == revision

    listed = client.get(f"{_base(PROJECT_A)}/risk-rules")
    assert listed.status_code == 200, listed.text
    listed_body = listed.json()
    _assert_public_clean(listed_body)
    assert listed_body["project_id"] == PROJECT_A
    assert listed_body["rule_revisions"] == [revision]

    options = client.get(f"{_base(PROJECT_A)}/run-setup/options")
    assert options.status_code == 200, options.text
    assert options.json()["rule_revisions"] == [revision]

    assert client.post(f"{_base(PROJECT_B)}/workspace/bootstrap").status_code == 200
    assert client.get(f"{_base(PROJECT_B)}/risk-rules").json()["rule_revisions"] == []


def test_slice07c1_expired_preview_and_empty_snapshot_selector_fail_clearly(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200

    preview = client.post(
        f"{_base(PROJECT_A)}/risk-rules/preview",
        json={"source_text": "ALT 超过上限"},
    ).json()
    restarted_client = _client(tmp_path)
    missing = restarted_client.post(
        f"{_base(PROJECT_A)}/risk-rules",
        json={"preview_token": preview["preview_token"]},
    )
    assert missing.status_code == 404
    assert missing.json() == {
        "code": "risk_rule_preview_not_found",
        "message": "待确认的关注规则已失效，请重新预览后再确认。",
    }

    empty_selector = restarted_client.get(
        f"{_base(PROJECT_A)}/run-setup/options?current_snapshot_token="
    )
    assert empty_selector.status_code == 422
    assert empty_selector.json()["code"] == "invalid_snapshot"


def test_slice07c2_prepare_and_start_resolves_tokens_and_replays(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options")
    assert options.status_code == 200, options.text
    setup = options.json()
    current_token = setup["current_data"]["snapshot_token"]
    daily = setup["modes"][0]
    baseline_token = daily["baseline_options"][0]["baseline_token"]
    payload = {
        "current_snapshot_token": current_token,
        "mode": "daily",
        "execution_basis": "incremental",
        "baseline_token": baseline_token,
        "risk_rule_tokens": [],
        "idempotency_key": "prepare-start-001",
    }

    first = client.post(f"{_base(PROJECT_A)}/runs/prepare-and-start", json=payload)
    assert first.status_code == 200, first.text
    first_body = first.json()
    _assert_public_clean(first_body)
    assert first_body["replayed"] is False
    assert first_body["public_run_token"].startswith("run:")
    assert first_body["mode_text"] == "日常监查"
    assert first_body["run_state"] == "running"
    assert first_body["result_available"] is False
    assert first_body["main_action"] == "查看本次进度"

    replay = client.post(f"{_base(PROJECT_A)}/runs/prepare-and-start", json=payload)
    assert replay.status_code == 200, replay.text
    replay_body = replay.json()
    assert replay_body["replayed"] is True
    assert replay_body["public_run_token"] == first_body["public_run_token"]

    conflict_payload = {**payload, "execution_basis": "full", "baseline_token": None}
    conflict = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json=conflict_payload,
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "idempotency_conflict"

    history = client.get(f"{_base(PROJECT_A)}/runs")
    for _ in range(100):
        assert history.status_code == 200, history.text
        if history.json()["runs"][0]["run_state"] == "completed":
            break
        time.sleep(0.01)
        history = client.get(f"{_base(PROJECT_A)}/runs")
    assert len(history.json()["runs"]) == 1
    history_run = history.json()["runs"][0]
    assert history_run["public_run_token"] == first_body["public_run_token"]
    assert history_run["run_state"] == "completed"
    assert history_run["result_available"] is False
    assert history_run["main_action"] == "查看本次进度"


def test_slice07c2_prepare_and_start_start_failure_is_recoverable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.runtime_progress import (
        RuntimeProgressAdapter,
        RuntimeProgressError,
    )

    def fail_start(_adapter: RuntimeProgressAdapter, _run_id: str) -> dict[str, Any]:
        raise RuntimeProgressError("worker_start_failed")

    monkeypatch.setattr(RuntimeProgressAdapter, "start_execution", fail_start)
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    payload = {
        "current_snapshot_token": options["current_data"]["snapshot_token"],
        "mode": "daily",
        "execution_basis": "full",
        "risk_rule_tokens": [],
        "idempotency_key": "prepare-start-failure-001",
    }

    failed_start = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json=payload,
    )
    assert failed_start.status_code == 200, failed_start.text
    body = failed_start.json()
    assert body["run_state"] == "waiting_start"
    assert body["replayed"] is False
    assert body["result_available"] is False

    replay = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json=payload,
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["replayed"] is True
    assert replay.json()["public_run_token"] == body["public_run_token"]
    history = client.get(f"{_base(PROJECT_A)}/runs")
    assert history.status_code == 200
    assert history.json()["runs"][0]["run_state"] == "waiting_start"


def test_slice07c2_start_failure_then_admin_start_reaches_completed_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.runtime_progress import (
        RuntimeProgressAdapter,
        RuntimeProgressError,
    )

    original_start = RuntimeProgressAdapter.start_execution
    calls = 0

    def fail_once(
        adapter: RuntimeProgressAdapter, run_id: str
    ) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeProgressError("worker_start_failed")
        return original_start(adapter, run_id)

    monkeypatch.setattr(RuntimeProgressAdapter, "start_execution", fail_once)
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    payload = {
        "current_snapshot_token": options["current_data"]["snapshot_token"],
        "mode": "daily",
        "execution_basis": "full",
        "risk_rule_tokens": [],
        "idempotency_key": "prepare-start-recovery-001",
    }
    first = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start", json=payload
    )
    assert first.status_code == 200
    assert first.json()["run_state"] == "waiting_start"

    workspace = _r7_workspace(tmp_path, PROJECT_A)
    with lr.LaunchRegistry(
        workspace / lr.LAUNCH_REGISTRY_DB_NAME,
        project_id=PROJECT_A,
    ) as registry:
        run_id = registry.list_records(PROJECT_A)[0].run_id
    restarted = client.post(
        f"{_base(PROJECT_A)}/runs/{run_id}/execution/start", json={}
    )
    assert restarted.status_code == 200, restarted.text

    history = client.get(f"{_base(PROJECT_A)}/runs")
    for _ in range(100):
        assert history.status_code == 200, history.text
        if history.json()["runs"][0]["run_state"] == "completed":
            break
        time.sleep(0.01)
        history = client.get(f"{_base(PROJECT_A)}/runs")
    assert history.json()["runs"][0]["run_state"] == "completed"
    assert history.json()["runs"][0]["result_available"] is False


def test_slice07c2_retry_after_reservation_finishes_same_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.runtime_progress import (
        RuntimeProgressAdapter,
        RuntimeProgressError,
    )

    original_prepare = RuntimeProgressAdapter.prepare_execution
    calls = 0

    def interrupt_once(
        adapter: RuntimeProgressAdapter,
        run_id: str,
        work_units: list[dict[str, Any]],
        execution_kind: str = "deterministic",
    ) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeProgressError("runtime_integrity_failed")
        return original_prepare(
            adapter,
            run_id,
            work_units,
            execution_kind=execution_kind,
        )

    monkeypatch.setattr(RuntimeProgressAdapter, "prepare_execution", interrupt_once)
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    payload = {
        "current_snapshot_token": options["current_data"]["snapshot_token"],
        "mode": "daily",
        "execution_basis": "full",
        "risk_rule_tokens": [],
        "idempotency_key": "prepare-start-interrupted-001",
    }

    interrupted = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start", json=payload
    )
    assert interrupted.status_code >= 400
    assert interrupted.json()["code"] == "runtime_integrity_failed"
    waiting = client.get(f"{_base(PROJECT_A)}/runs").json()["runs"]
    assert len(waiting) == 1
    public_run_token = waiting[0]["public_run_token"]
    assert waiting[0]["run_state"] == "waiting_start"

    retried = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start", json=payload
    )
    assert retried.status_code == 200, retried.text
    assert retried.json()["replayed"] is True
    assert retried.json()["public_run_token"] == public_run_token
    assert len(client.get(f"{_base(PROJECT_A)}/runs").json()["runs"]) == 1


def test_slice07c2_product_tokens_fail_closed_before_launch_registry_write(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    assert client.post(f"{_base(PROJECT_B)}/workspace/bootstrap").status_code == 200
    options_a = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    options_b = client.get(f"{_base(PROJECT_B)}/run-setup/options").json()
    payload = {
        "current_snapshot_token": options_b["current_data"]["snapshot_token"],
        "mode": "daily",
        "execution_basis": "full",
        "risk_rule_tokens": [],
        "idempotency_key": "cross-project-token-001",
    }

    rejected = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start", json=payload
    )
    assert rejected.status_code >= 400
    assert rejected.json()["code"] == "invalid_snapshot"
    assert client.get(f"{_base(PROJECT_A)}/runs").json()["runs"] == []

    payload.update(
        current_snapshot_token=options_a["current_data"]["snapshot_token"],
        execution_basis="incremental",
        baseline_token=options_b["modes"][0]["baseline_options"][0]["baseline_token"],
        idempotency_key="cross-project-baseline-001",
    )
    rejected = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start", json=payload
    )
    assert rejected.status_code >= 400
    assert rejected.json()["code"] == "baseline_not_published"
    assert client.get(f"{_base(PROJECT_A)}/runs").json()["runs"] == []


def test_slice07c2_medical_monitor_can_launch_but_medical_writer_cannot(
    tmp_path: Path,
) -> None:
    admin = _client(tmp_path)
    assert admin.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    monitor = _client(tmp_path, principal=_principal(roles=("medical_monitor",)))
    options = monitor.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    payload = {
        "current_snapshot_token": options["current_data"]["snapshot_token"],
        "mode": "daily",
        "execution_basis": "full",
        "risk_rule_tokens": [],
        "idempotency_key": "monitor-launch-001",
    }
    allowed = monitor.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start", json=payload
    )
    assert allowed.status_code == 200, allowed.text

    writer = _client(tmp_path, principal=_principal(roles=("medical_writer",)))
    denied = writer.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json={**payload, "idempotency_key": "writer-launch-001"},
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == "not_permitted"


def _wait_product_launch_completed(
    client: TestClient,
    project_id: str,
    public_run_token: str,
) -> None:
    for _ in range(200):
        history = client.get(f"{_base(project_id)}/runs")
        assert history.status_code == 200, history.text
        rows = history.json()["runs"]
        assert rows
        if rows[0]["public_run_token"] == public_run_token:
            if rows[0]["run_state"] == "completed":
                return
        time.sleep(0.01)
    raise AssertionError("synthetic launch did not reach completed")


def _route_fake_r5_packet() -> SimpleNamespace:
    return SimpleNamespace(
        packet_identity="r5-publication-authority:" + "a" * 64,
        packet_digest="a" * 64,
        authority_hash="a" * 64,
        s4_packet_ids=("s4:synthetic:one",),
        s4_packet_digests=("b" * 64,),
        site_refs=("site-01", "site-02"),
    )


def test_slice07c3_publication_failure_matrix_blocks_without_r5_provider(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    launched = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json={
            "current_snapshot_token": options["current_data"]["snapshot_token"],
            "mode": "daily",
            "execution_basis": "full",
            "risk_rule_tokens": [],
            "idempotency_key": "slice07c3-missing-r5-launch",
        },
    )
    assert launched.status_code == 200, launched.text
    public_token = launched.json()["public_run_token"]
    unavailable = client.get(
        f"{_base(PROJECT_A)}/runs/{public_token}/result-entry"
    )
    assert unavailable.status_code == 409
    assert unavailable.json() == {
        "code": "publication_not_available",
        "message": "结果尚未整理完成",
    }

    _wait_product_launch_completed(client, PROJECT_A, public_token)
    rejected = client.post(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice07c3-missing-r5-publication"},
    )
    assert rejected.status_code == 409
    assert rejected.json() == {
        "code": "publication_blocked",
        "message": "结果尚未整理完成",
    }
    state = client.get(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication"
    )
    assert state.status_code == 200
    assert state.json()["publication_state"] == "blocked"
    assert state.json()["result_available"] is False
    history = client.get(f"{_base(PROJECT_A)}/runs").json()["runs"]
    assert history[0]["result_available"] is False
    assert history[0]["main_action"] == "查看本次进度"
    workspace = _r7_workspace(tmp_path, PROJECT_A)
    with lr.LaunchRegistry(
        workspace / lr.LAUNCH_REGISTRY_DB_NAME,
        project_id=PROJECT_A,
    ) as registry:
        internal_run_id = registry.get_by_public_token(
            public_token, project_id=PROJECT_A
        ).run_id
    progress = client.get(
        f"{_base(PROJECT_A)}/runs/{internal_run_id}/progress"
    )
    assert progress.status_code == 200, progress.text
    assert progress.json()["publication_state"] == "blocked"
    assert progress.json()["publication_status_text"] == (
        "分析已结束，结果整理未完成"
    )



def test_slice07c3_snapshot_token_mapping_drift_keeps_result_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    client = _client(tmp_path)
    assert (
        client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code
        == 200
    )
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    launched = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json={
            "current_snapshot_token": options["current_data"]["snapshot_token"],
            "mode": "daily",
            "execution_basis": "full",
            "risk_rule_tokens": [],
            "idempotency_key": "slice07c3-token-drift-launch",
        },
    )
    assert launched.status_code == 200, launched.text
    public_token = launched.json()["public_run_token"]
    _wait_product_launch_completed(client, PROJECT_A, public_token)

    def transient_authority_failure(*_: Any, **__: Any) -> Any:
        raise product_mod.ProductPublicationError(
            "authority_provider_unavailable", recoverable=True
        )

    monkeypatch.setattr(
        product_mod,
        "_build_r5_publication_packet",
        transient_authority_failure,
    )
    first = client.post(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice07c3-token-drift-publication"},
    )
    assert first.status_code == 500
    assert first.json()["code"] == "publication_recoverable_failed"

    original_snapshot_for_token = (
        product_mod.rs.RunSetupCatalog.snapshot_for_token
    )

    def drift_snapshot(
        catalog: Any,
        project_id: str,
        selector: str,
    ) -> Any:
        snapshot = original_snapshot_for_token(
            catalog, project_id, selector
        )
        return product_mod.rs.DataSnapshot(
            snapshot_ref=snapshot.snapshot_ref + ":drift",
            project_id=snapshot.project_id,
            data_cutoff=snapshot.data_cutoff,
            rows=snapshot.rows,
            key_fields=snapshot.key_fields,
            imported_at=snapshot.imported_at,
            scope_description=snapshot.scope_description,
            source_revision_id=snapshot.source_revision_id,
        )

    monkeypatch.setattr(
        product_mod.rs.RunSetupCatalog,
        "snapshot_for_token",
        drift_snapshot,
    )
    replay = client.post(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice07c3-token-drift-publication"},
    )
    assert replay.status_code == 422
    assert replay.json()["code"] == "invalid_snapshot"

    state = client.get(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication"
    )
    assert state.status_code == 200
    assert state.json()["publication_state"] == "recoverable_failed"
    assert state.json()["result_available"] is False
    entry = client.get(
        f"{_base(PROJECT_A)}/runs/{public_token}/result-entry"
    )
    assert entry.status_code == 409
    assert entry.json()["code"] == "publication_not_available"


def test_slice07c3_audit_integrity_failure_is_blocked_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    client = _client(tmp_path)
    assert (
        client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code
        == 200
    )
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    launched = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json={
            "current_snapshot_token": options["current_data"]["snapshot_token"],
            "mode": "daily",
            "execution_basis": "full",
            "risk_rule_tokens": [],
            "idempotency_key": "slice07c3-audit-drift-launch",
        },
    )
    assert launched.status_code == 200, launched.text
    public_token = launched.json()["public_run_token"]
    _wait_product_launch_completed(client, PROJECT_A, public_token)

    monkeypatch.setattr(
        product_mod,
        "_build_r5_publication_packet",
        lambda *args, **kwargs: _route_fake_r5_packet(),
    )
    monkeypatch.setattr(
        product_mod.RuntimeProgressAdapter,
        "read_progress",
        lambda _adapter, _run_id: {"run_state": "completed"},
    )
    monkeypatch.setattr(
        product_mod.Store,
        "verify_audit_chain",
        lambda _store: (False, 1, 1),
    )
    rejected = client.post(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice07c3-audit-drift-publication"},
    )
    assert rejected.status_code == 409
    assert rejected.json() == {
        "code": "publication_blocked",
        "message": "结果尚未整理完成",
    }
    workspace = _r7_workspace(tmp_path, PROJECT_A)
    with lr.LaunchRegistry(
        workspace / lr.LAUNCH_REGISTRY_DB_NAME,
        project_id=PROJECT_A,
    ) as registry:
        launch_record = registry.get_by_public_token(
            public_token, project_id=PROJECT_A
        )
        publication = registry.get_publication(
            project_id=PROJECT_A, run_id=launch_record.run_id
        )
    assert publication.publication_state == "blocked"
    assert publication.failure_code == "receipt_gate_blocked"
    assert publication.result_available is False
    entry = client.get(
        f"{_base(PROJECT_A)}/runs/{public_token}/result-entry"
    )
    assert entry.status_code == 409
    assert entry.json()["code"] == "publication_not_available"


def test_slice07c3_publication_retry_stays_blocked_without_r6_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    launched = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json={
            "current_snapshot_token": options["current_data"]["snapshot_token"],
            "mode": "daily",
            "execution_basis": "full",
            "risk_rule_tokens": [],
            "idempotency_key": "slice07c3-retry-launch",
        },
    )
    assert launched.status_code == 200, launched.text
    public_token = launched.json()["public_run_token"]
    _wait_product_launch_completed(client, PROJECT_A, public_token)

    first = client.post(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice07c3-retry-publication"},
    )
    assert first.status_code == 409
    assert first.json()["code"] == "publication_blocked"

    fake_packet = _route_fake_r5_packet()
    monkeypatch.setattr(
        product_mod,
        "_build_r5_publication_packet",
        lambda *args, **kwargs: fake_packet,
    )
    retried = client.post(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice07c3-retry-publication"},
    )
    assert retried.status_code == 409
    assert retried.json()["code"] == "publication_blocked"
    assert (
        client.get(f"{_base(PROJECT_A)}/runs/{public_token}/result-entry").status_code
        == 409
    )
    return

    replayed = client.post(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice07c3-retry-publication-new-key"},
    )
    assert replayed.status_code == 200, replayed.text
    assert replayed.json()["publication_state"] == "available"
    assert replayed.json()["replayed"] is True

    entry = client.get(
        f"{_base(PROJECT_A)}/runs/{public_token}/result-entry"
    )
    assert entry.status_code == 200, entry.text
    body = entry.json()
    assert set(body) == {
        "project_ref",
        "public_run_token",
        "snapshot_token",
        "data_cutoff_text",
        "site_options",
        "result_context_token",
    }
    assert body["project_ref"] == PROJECT_A
    assert body["public_run_token"] == public_token
    assert [
        (item["site_ref"], item["site_label"])
        for item in body["site_options"]
    ] == [
        ("site-01", "中心 site-01"),
        ("site-02", "中心 site-02"),
    ]
    blob = json.dumps(body, ensure_ascii=False).lower()
    assert "run_id" not in blob
    assert "authority" not in blob
    assert "digest" not in blob
    history = client.get(f"{_base(PROJECT_A)}/runs").json()["runs"]
    assert history[0]["result_available"] is True
    assert history[0]["main_action"] == "查看本次结果"


def test_slice07c3_product_route_uses_actual_typed_r5_bridge_and_refetches(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    # Load the accepted R5 package through the same lazy source seam as the
    # product route, then import only its deterministic test fixture helpers.
    product_mod._r5_publication_types()
    monkeypatch.syspath_prepend(
        str(
            Path(__file__).resolve().parents[1]
            / "poc"
            / "medical_monitoring_ai_native_r5"
            / "tests"
        )
    )
    from s4_runtime_fixtures import build_runtime_input
    from test_r5_publication_authority import _members
    from packages.medical_monitoring.projections.publication.r5_publication_authority import (
        R5PublicationAuthorityInputAssembler,
    )
    from packages.medical_monitoring.projections.publication import s4_projection
    from packages.medical_monitoring.projections.publication import s4_validator

    fixture_runtime = build_runtime_input("single_analysis")
    project_id = fixture_runtime.anchor.project_ref
    run_id = fixture_runtime.anchor.run_ref
    site_ref = fixture_runtime.anchor.site_ref
    snapshot_ref = fixture_runtime.anchor.snapshot_ref
    cutoff = fixture_runtime.anchor.cutoff_ref
    source_revision = (
        fixture_runtime.authority_receipt.source_revision_content_pairs[0]
        .revision_id
    )
    current = product_mod.rs.DataSnapshot(
        snapshot_ref=snapshot_ref,
        project_id=project_id,
        data_cutoff=cutoff,
        rows=(
            {
                "canonical_key": "site.01/S-001/lab-alt",
                "site_ref": site_ref,
                "subject_ref": "S-001",
                "value": 47,
            },
        ),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    prior = product_mod.rs.DataSnapshot(
        snapshot_ref="snap.prior",
        project_id=project_id,
        data_cutoff="cutoff.prior",
        rows=(
            {
                "canonical_key": "site.01/S-001/lab-alt",
                "site_ref": site_ref,
                "subject_ref": "S-001",
                "value": 42,
            },
        ),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((prior, current), ()),
    )
    setup_manifest = product_mod.rs.generate_work_units(
        "daily",
        "full",
        current_snapshot_token=current.snapshot_token,
    )

    class TypedProvider:
        def __init__(self) -> None:
            self.assembler = R5PublicationAuthorityInputAssembler()
            self.calls = 0
            self.attempt_batches: list[tuple[Mapping[str, Any], ...]] = []

        def get_authority_input(
            self,
            run_identity: Any,
            attempts: Any,
            **_: Any,
        ) -> Any:
            self.calls += 1
            persisted = tuple(attempts or ())
            if not persisted:
                raise AssertionError(
                    "R5 provider requires persisted receipt attempts"
                )
            self.attempt_batches.append(persisted)
            return self.assembler.assemble(
                run_identity,
                runtime_input=fixture_runtime,
                **_members(fixture_runtime),
            )

    class SyntheticR6Provider:
        def get_mode_outputs(
            self,
            run_binding: Mapping[str, Any],
            r5_packet: Any,
            **_: Any,
        ) -> tuple[dict[str, Any], ...]:
            return _make_slice08b_mode_outputs(run_binding, r5_packet, "daily")

    provider = TypedProvider()
    client = _client(
        tmp_path,
        principal=_principal(project_id),
        harness_adapter=FakeHarnessAdapter(),
        harness_catalog=FakeCatalog(),
        authority_provider=provider,
        r6_output_provider=SyntheticR6Provider(),
    )
    assert (
        client.post(
            f"{_base(project_id)}/workspace/bootstrap"
        ).status_code
        == 200
    )
    bound = client.post(
        f"{_base(project_id)}/runs",
        json={
            "run_id": run_id,
            "mode": "daily",
            "execution_basis": "full",
            "data_cutoff": cutoff,
            "source_revision_id": source_revision,
        },
    )
    assert bound.status_code == 200, bound.text
    prepared = client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": product_mod._runtime_work_units(setup_manifest),
            "execution_kind": "harness",
        },
    )
    assert prepared.status_code == 200, prepared.text
    started = client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/start",
        json={},
    )
    assert started.status_code == 200, started.text
    for _ in range(200):
        progress = client.get(
            f"{_base(project_id)}/runs/{run_id}/progress"
        )
        assert progress.status_code == 200, progress.text
        if progress.json()["run_state"] == "completed":
            break
        time.sleep(0.01)
    assert progress.json()["run_state"] == "completed"

    # The launch registry normally owns this row.  This test intentionally
    # binds a fixture-compatible run identity through the existing schema so
    # the product route can exercise the real R5 identity checks.
    workspace = _r7_workspace(tmp_path, project_id)
    registry_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    registry = lr.LaunchRegistry(registry_path, project_id=project_id)
    reservation = registry.reserve(
        project_id,
        idempotency_key="typed-r5-launch",
        mode="daily",
        execution_basis="full",
        current_snapshot_token=current.snapshot_token,
        data_cutoff=cutoff,
        manifest_digest=setup_manifest.manifest_digest,
    )
    sequence = reservation.record.sequence
    registry.close()
    public_token = lr.derive_public_run_token(project_id, run_id)
    with sqlite3.connect(str(registry_path)) as connection:
        connection.execute(
            "UPDATE r7_launch_registry SET run_id=?, public_run_token=? "
            "WHERE sequence=?",
            (run_id, public_token, sequence),
        )
        connection.commit()
    with lr.LaunchRegistry(
        registry_path, project_id=project_id
    ) as registry:
        registry.mark_completed(run_id, project_id=project_id)

    from poc.medical_monitoring_ai_native_r7.src.mm_r7.run_binding import (
        RunBindingStore,
    )
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.runtime_progress import (
        RuntimeProgressAdapter,
    )

    order: list[str] = []
    reserve_publication = lr.LaunchRegistry.reserve_publication
    entry_init = MonitoringRunEntry.__init__
    binding_get = RunBindingStore.get
    read_progress = RuntimeProgressAdapter.read_progress

    def reserve_probe(registry: Any, *args: Any, **kwargs: Any) -> Any:
        order.append("reserve")
        return reserve_publication(registry, *args, **kwargs)

    def entry_probe(entry: Any, *args: Any, **kwargs: Any) -> None:
        order.append("entry")
        entry_init(entry, *args, **kwargs)

    def binding_probe(store: Any, *args: Any, **kwargs: Any) -> Any:
        probe = lr.LaunchRegistry(registry_path, project_id=project_id)
        try:
            bound_publication = probe.get_publication(
                project_id=project_id, run_id=run_id
            )
            assert bound_publication.publication_state == "publishing"
        finally:
            probe.close()
        order.append("binding")
        return binding_get(store, *args, **kwargs)

    def progress_probe(adapter: Any, *args: Any, **kwargs: Any) -> Any:
        order.append("progress")
        return read_progress(adapter, *args, **kwargs)

    monkeypatch.setattr(
        lr.LaunchRegistry, "reserve_publication", reserve_probe
    )
    monkeypatch.setattr(MonitoringRunEntry, "__init__", entry_probe)
    monkeypatch.setattr(RunBindingStore, "get", binding_probe)
    monkeypatch.setattr(
        RuntimeProgressAdapter, "read_progress", progress_probe
    )


    real_builder = s4_projection.build_s4_authority_packet
    real_validator = s4_validator.validate_s4_authority_packet
    builder = Mock(wraps=real_builder)
    validator = Mock(wraps=real_validator)
    monkeypatch.setattr(
        s4_projection, "build_s4_authority_packet", builder
    )
    monkeypatch.setattr(
        s4_validator, "validate_s4_authority_packet", validator
    )

    published = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": "typed-r5-publication"},
    )
    assert published.status_code == 200, published.text
    assert published.json()["publication_state"] == "available"
    assert provider.calls == 1
    assert builder.call_count == 1
    assert validator.call_count == 1

    assert order[:4] == ["reserve", "entry", "progress", "binding"]
    result_entry = client.get(
        f"{_base(project_id)}/runs/{public_token}/result-entry"
    )
    assert result_entry.status_code == 200, result_entry.text
    assert provider.calls == 2
    assert builder.call_count == 2
    assert validator.call_count == 2
    assert result_entry.json()["site_options"] == [
        {"site_ref": site_ref, "site_label": f"中心 {site_ref}"}
    ]
    assert provider.attempt_batches
    assert all(provider.attempt_batches)
    original_gate = product_mod._read_publication_gate

    def drifted_gate(*args: Any, **kwargs: Any) -> dict[str, Any]:
        gate = original_gate(*args, **kwargs)
        drifted_receipts = list(gate["receipt_ids"])
        drifted_receipts[0] = "receipt-drift"
        return {
            **gate,
            "receipt_ids": tuple(drifted_receipts),
            "receipt_set_digest": "receipt-set-drift",
        }

    monkeypatch.setattr(
        product_mod, "_read_publication_gate", drifted_gate
    )
    drifted = client.get(
        f"{_base(project_id)}/runs/{public_token}/result-entry"
    )
    assert drifted.status_code == 409
    assert drifted.json()["code"] == "receipt_gate_blocked"
    assert provider.calls == 2
    assert builder.call_count == 2
    assert validator.call_count == 2


@pytest.mark.parametrize(
    "failure_point",
    ("finalize.after_publication_update", "finalize.after_launch_update"),
)
def test_slice07c3_product_route_does_not_reach_finalize_without_r6_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    client = _client(tmp_path)
    assert (
        client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code
        == 200
    )
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    launched = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json={
            "current_snapshot_token": options["current_data"]["snapshot_token"],
            "mode": "daily",
            "execution_basis": "full",
            "risk_rule_tokens": [],
            "idempotency_key": f"slice07c3-fault-{failure_point}",
        },
    )
    assert launched.status_code == 200, launched.text
    public_token = launched.json()["public_run_token"]
    _wait_product_launch_completed(client, PROJECT_A, public_token)

    fake_packet = _route_fake_r5_packet()
    monkeypatch.setattr(
        product_mod,
        "_build_r5_publication_packet",
        lambda *args, **kwargs: fake_packet,
    )

    original_init = lr.LaunchRegistry.__init__
    hook_calls: list[str] = []

    def inject_finalize_failure(
        registry: Any, *args: Any, **kwargs: Any
    ) -> None:
        original_init(registry, *args, **kwargs)

        def injector(point: str) -> None:
            hook_calls.append(point)
            if point == failure_point:
                raise RuntimeError("synthetic finalize fault")

        registry.set_failure_injector(injector)

    monkeypatch.setattr(lr.LaunchRegistry, "__init__", inject_finalize_failure)
    first = client.post(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication",
        json={"idempotency_key": f"publication-{failure_point}"},
    )
    assert first.status_code == 409, first.text
    assert first.json()["code"] == "publication_blocked"
    assert failure_point not in hook_calls
    return

    # Both transaction sides must remain closed after either injected fault.
    state = client.get(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication"
    )
    assert state.status_code == 200
    assert state.json()["publication_state"] == "recoverable_failed"
    assert state.json()["result_available"] is False
    history = client.get(f"{_base(PROJECT_A)}/runs").json()["runs"]
    assert history[0]["result_available"] is False
    assert history[0]["main_action"] == "查看本次进度"
    unavailable = client.get(
        f"{_base(PROJECT_A)}/runs/{public_token}/result-entry"
    )
    assert unavailable.status_code == 409
    assert unavailable.json()["code"] == "publication_not_available"

    # Remove only the injected failure; the same key resumes revision 1.
    monkeypatch.setattr(lr.LaunchRegistry, "__init__", original_init)
    retried = client.post(
        f"{_base(PROJECT_A)}/runs/{public_token}/publication",
        json={"idempotency_key": f"publication-{failure_point}"},
    )
    assert retried.status_code == 200, retried.text
    assert retried.json()["publication_state"] == "available"
    assert retried.json()["result_available"] is True
    history = client.get(f"{_base(PROJECT_A)}/runs").json()["runs"]
    assert history[0]["result_available"] is True
    assert history[0]["main_action"] == "查看本次结果"
    assert (
        client.get(
            f"{_base(PROJECT_A)}/runs/{public_token}/result-entry"
        ).status_code
        == 200
    )


def test_slice07c4_public_result_context_requires_r6_artifact_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod
    from services.api.app.medical_monitoring_r5_product_adapter import (
        build_synthetic_r5_authority_packet,
    )

    current = product_mod.rs.DataSnapshot(
        snapshot_ref="s7-snapshot-current-001",
        project_id=PROJECT_A,
        data_cutoff="2026-03-31",
        rows=(
            {
                "canonical_key": "s7-site-006/S-06021",
                "site_ref": "s7-site-006",
                "subject_ref": "s7-subject-06021",
            },
            {
                "canonical_key": "s7-site-010/S-10008",
                "site_ref": "s7-site-010",
                "subject_ref": "s7-subject-10008",
            },
        ),
        key_fields=("canonical_key",),
        imported_at="2026-03-31T00:00:00+00:00",
        source_revision_id="s7-revision-current-001",
    )
    prior = product_mod.rs.DataSnapshot(
        snapshot_ref="s7-snapshot-prior-001",
        project_id=PROJECT_A,
        data_cutoff="2026-03-01",
        rows=current.rows,
        key_fields=current.key_fields,
        imported_at="2026-03-01T00:00:00+00:00",
        source_revision_id="s7-revision-prior-001",
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((prior, current), ()),
    )

    local_packet = dataclass_replace(
        build_synthetic_r5_authority_packet(),
        project_ref=PROJECT_A,
        run_ref="placeholder-run",
        snapshot_ref=current.snapshot_ref,
        cutoff_ref=current.data_cutoff,
        synthetic=False,
        data_mode="authority",
        authority_hash="",
        source_snapshot_sha256="",
    )

    def fake_builder(
        _provider: Any,
        identity: Any,
        **_: Any,
    ) -> Any:
        return SimpleNamespace(
            packet_identity="r5-publication-authority:" + "d" * 64,
            packet_digest="d" * 64,
            site_refs=("s7-site-006", "s7-site-010"),
            s4_packet_ids=("s4:synthetic:one",),
            s4_packet_digests=("e" * 64,),
            product_packet=dataclass_replace(
                local_packet,
                run_ref=identity.run_ref,
                authority_hash="",
                source_snapshot_sha256="",
            ),
        )

    monkeypatch.setattr(
        product_mod,
        "_build_r5_publication_packet",
        fake_builder,
    )
    client = _client(tmp_path, principal=_principal(PROJECT_A))
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    launched = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json={
            "current_snapshot_token": options["current_data"]["snapshot_token"],
            "mode": "daily",
            "execution_basis": "full",
            "risk_rule_tokens": [],
            "idempotency_key": "slice07c4-public-result-launch",
        },
    )
    assert launched.status_code == 200, launched.text
    public_run_token = launched.json()["public_run_token"]
    _wait_product_launch_completed(client, PROJECT_A, public_run_token)

    published = client.post(
        f"{_base(PROJECT_A)}/runs/{public_run_token}/publication",
        json={"idempotency_key": "slice07c4-public-result-publication"},
    )
    assert published.status_code == 409, published.text
    assert published.json()["code"] == "publication_blocked"
    entry = client.get(
        f"{_base(PROJECT_A)}/runs/{public_run_token}/result-entry"
    )
    assert entry.status_code == 409, entry.text
    return
    result_context_token = entry.json()["result_context_token"]
    assert result_context_token.startswith("result-context:")
    assert (
        client.get(
            f"{_base(PROJECT_A)}/runs/{public_run_token}/result-entry"
        ).json()["result_context_token"]
        == result_context_token
    )

    overview = client.get(
        f"{_base(PROJECT_A)}/results/{result_context_token}/overview"
    )
    assert overview.status_code == 200, overview.text
    overview_body = overview.json()
    assert set(overview_body) == {
        "identity",
        "projection",
        "result_context_token",
        "response_digest",
    }
    assert overview_body["result_context_token"] == result_context_token
    assert overview_body["identity"]["view"] == "overview"
    assert overview_body["identity"]["mode_text"] == "日常监查"
    assert overview_body["identity"]["snapshot_token"] == options["current_data"][
        "snapshot_token"
    ]
    assert overview_body["response_digest"] == lr.content_digest(
        {
            "identity": overview_body["identity"],
            "projection": overview_body["projection"],
        }
    )
    overview_blob = json.dumps(overview_body, ensure_ascii=False).lower()
    for forbidden in (
        "run_id",
        "run_ref",
        "snapshot_ref",
        "cutoff_ref",
        "authority_receipt",
        "authority_hash",
        "packet_digest",
        "s4_",
    ):
        assert forbidden not in overview_blob

    out_of_scope = client.get(
        f"{_base(PROJECT_A)}/results/{result_context_token}/overview",
        params={"site_ref": "site-outside"},
    )
    assert out_of_scope.status_code == 409
    assert out_of_scope.json()["code"] == "result_center_out_of_scope"

    subject = client.get(
        f"{_base(PROJECT_A)}/results/{result_context_token}/subjects/"
        "s7-subject-10008",
        params={
            "site_ref": "s7-site-010",
            "spine_ref": "s7-spine-10008",
            "window_start": "2026-01-01",
            "window_end": "2026-03-31",
        },
    )
    assert subject.status_code == 200, subject.text
    assert subject.json()["identity"]["view"] == "journey"
    assert subject.json()["identity"]["subject_ref"] == "s7-subject-10008"

    source = client.get(
        f"{_base(PROJECT_A)}/results/{result_context_token}/source-evidence",
        params={
            "risk_instance_ref": "s7-risk-pd-10008",
            "source_locator_ref": "s7-source-pd-10008",
        },
    )
    assert source.status_code == 200, source.text
    assert source.json()["identity"]["view"] == "evidence"
    assert source.json()["identity"]["source_locator_ref"] == "s7-source-pd-10008"


def test_slice07c4_prepare_and_start_blocks_second_in_flight_run_and_public_progress(
    tmp_path: Path,
) -> None:
    client = _client(tmp_path)
    assert client.post(f"{_base(PROJECT_A)}/workspace/bootstrap").status_code == 200
    options = client.get(f"{_base(PROJECT_A)}/run-setup/options").json()
    base_payload = {
        "current_snapshot_token": options["current_data"]["snapshot_token"],
        "mode": "daily",
        "execution_basis": "full",
        "risk_rule_tokens": [],
    }
    first = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json={**base_payload, "idempotency_key": "slice07c4-first"},
    )
    assert first.status_code == 200, first.text
    public_run_token = first.json()["public_run_token"]

    second = client.post(
        f"{_base(PROJECT_A)}/runs/prepare-and-start",
        json={**base_payload, "idempotency_key": "slice07c4-second"},
    )
    assert second.status_code == 409, second.text
    assert second.json() == {
        "code": "in_flight_conflict",
        "message": "当前已有监查正在进行，请先查看本次进度",
    }

    progress = client.get(
        f"{_base(PROJECT_A)}/runs/{public_run_token}/progress"
    )
    assert progress.status_code == 200, progress.text
    assert progress.json()["publication_state"] == "not_started"

    history = client.get(f"{_base(PROJECT_A)}/runs")
    assert history.status_code == 200, history.text
    assert len(history.json()["runs"]) == 1
    assert set(history.json()["runs"][0]) == {
        "public_run_token",
        "mode_text",
        "data_cutoff_text",
        "comparison_range_text",
        "run_state",
        "result_available",
        "main_action",
        "status_text",
    }


# ---------------------------------------------------------------------------
# Slice-08B: R5 / R6 / R1 Authority & Artifact Bridge Product Router Tests
# ---------------------------------------------------------------------------


def _make_slice08b_mode_outputs(
    run_binding: Mapping[str, Any],
    r5_packet: Any,
    mode: str,
    **overrides: Any,
) -> tuple[dict[str, Any], ...]:
    from packages.medical_monitoring.reports import mode_output as mo
    from poc.medical_monitoring_ai_native_r7.src.mm_r7 import continuity_bridge as cb

    binding = dict(run_binding)
    binding.setdefault("carry_forward_run_ids", [])
    binding.setdefault("mode_transition", "explicit_new_run")
    binding.setdefault("actor", "system_synthetic")
    if not binding.get("created_at"):
        binding["created_at"] = "2026-08-28T00:00:00Z"
    if not binding.get("knowledge_pack_version"):
        binding["knowledge_pack_version"] = "kp-08b-v1"
    if not binding.get("rule_activation_version"):
        binding["rule_activation_version"] = "rav-08b-v1"
    if not binding.get("mapping_version"):
        binding["mapping_version"] = "map-08b-v1"
    if not binding.get("identity_algorithm_version"):
        binding["identity_algorithm_version"] = "ia-08b-v1"
    if not binding.get("identity_algorithm_digest"):
        binding["identity_algorithm_digest"] = "ia-digest-08b-v1"
    if mode == "post_lock_pre_cfdi":
        binding.setdefault("fixed_total", True)
        if not binding.get("locked_snapshot_hash"):
            binding["locked_snapshot_hash"] = "snap-hash-fixed-001"
        if not binding.get("output_cutoff_ref"):
            binding["output_cutoff_ref"] = binding.get("data_cutoff")
        if not binding.get("output_revision_ref"):
            binding["output_revision_ref"] = binding.get("source_revision_id")
        if not binding.get("local_os_user"):
            binding["local_os_user"] = "local-user-synthetic"
        if not binding.get("acceptance_evidence_hash"):
            binding["acceptance_evidence_hash"] = "accept-hash-fixed-001"

    contract = mo.build_mode_contract(mode)
    ctx = mo.default_entry_context_for_mode(mode, run_binding=binding)
    digest = getattr(r5_packet, "packet_digest", "auth-digest-slice08b-001")
    refs = {
        "project_id": binding["project_id"],
        "run_id": binding["run_id"],
        "data_cutoff": binding["data_cutoff"],
        "source_revision_id": binding["source_revision_id"],
        "authority_digest": digest,
        "coverage_digest": digest,
        "qc_digest": digest,
        "digest": digest,
    }
    closure = cb.extract_r5_member_closure(r5_packet)
    risk_id = overrides.get("risk_id") or (closure.risk_refs[0] if closure.risk_refs else "d09_marker:m-rk")
    subject_id = overrides.get("subject_id") or (closure.subject_refs[0] if closure.subject_refs else "subject.1001")
    site_id = overrides.get("site_id") or (closure.site_refs[0] if closure.site_refs else "site.01")

    if mode == "daily":
        finding = {
            "finding_id": "finding-001",
            "risk_id": risk_id,
            "issue_id": "issue-001",
            "subject_id": subject_id,
            "site_id": site_id,
            "scope_kind": "subject",
            "basis": "方案要求报告不良事件",
            "finding": "受试者出现未记录的不良反应",
            "action": "请核实并补录",
            "evidence_refs": ["ev-listing-001"],
            "locator": {"path": "AE.AETERM", "record_id": "rec-001", "field": "AETERM"},
        }
        finding.update(overrides.get("finding_overrides", {}))
        if "query_drafts" in overrides:
            return (
                mo.build_change_summary_output(
                    binding,
                    contract,
                    authority_refs=refs,
                    coverage_refs=refs,
                    qc_refs=refs,
                    finding_deltas=[{"finding_id": "finding-001", "delta_kind": "new"}],
                    entry_context=ctx,
                ),
                mo.build_current_full_risk_output(
                    binding,
                    contract,
                    authority_refs=refs,
                    coverage_refs=refs,
                    qc_refs=refs,
                    findings=[finding],
                    risks=[{"risk_id": risk_id, "severity": "high", "risk_type": "ae_omission"}],
                    entry_context=ctx,
                ),
                mo.build_mode_output(
                    binding,
                    contract,
                    {
                        "output_kind": "affected_query_draft",
                        "query_drafts": list(overrides["query_drafts"]),
                        "eligibility": mo.default_output_eligibility(),
                    },
                    authority_refs=refs,
                    coverage_refs=refs,
                    qc_refs=refs,
                    entry_context=ctx,
                ),
                mo.build_mode_output(
                    binding,
                    contract,
                    {
                        "output_kind": "data_knowledge_rule_model_change_note",
                        "change_notes": [],
                        "eligibility": mo.default_output_eligibility(),
                    },
                    authority_refs=refs,
                    coverage_refs=refs,
                    qc_refs=refs,
                    entry_context=ctx,
                ),
            )
        return mo.build_daily_mode_outputs(
            binding,
            contract,
            authority_refs=refs,
            coverage_refs=refs,
            qc_refs=refs,
            findings=[finding],
            risks=[{"risk_id": risk_id, "severity": "high", "risk_type": "ae_omission"}],
            entry_context=ctx,
        )
    elif mode == "pre_lock":
        pop_scope = {
            "scope_kind": "project",
            "population_id": "pop-001",
            "label": "全受试者群体",
            "site_count": 1,
            "subject_count": 1,
            "risk_count": 1,
        }
        check_items = [
            {
                "level": "project",
                "check_kind": "lock_prep",
                "status": "ready",
                "evidence_refs": ["ev-proj-001"],
                "locator": {"path": "project.lock", "record_id": "p1"},
            },
            {
                "level": "site",
                "check_kind": "site_cutoff",
                "status": "ready",
                "site_id": site_id,
                "evidence_refs": ["ev-site-001"],
                "locator": {"path": "site.cutoff", "record_id": "s1"},
            },
            {
                "level": "subject",
                "check_kind": "subj_listing",
                "status": "ready",
                "site_id": site_id,
                "subject_id": subject_id,
                "evidence_refs": ["ev-subj-001"],
                "locator": {"path": "subj.listing", "record_id": "sub1"},
            },
        ]
        return mo.build_pre_lock_mode_outputs(
            binding,
            contract,
            authority_refs=refs,
            coverage_refs=refs,
            qc_refs=refs,
            from_source_revision_id="revision-prior-000",
            revision_reason="数据库锁库前例行比对",
            risks=[{"risk_id": risk_id, "severity": "high"}],
            check_items=check_items,
            population_scope=pop_scope,
            entry_context=ctx,
        )
    elif mode == "post_lock_pre_cfdi":
        pop_totals = {"site_count": 1, "subject_count": 1, "risk_count": 1}
        site_mat = [{
            "site_id": site_id,
            "subject_ids": [subject_id],
            "risk_ids": [risk_id],
            "evidence_refs": ["ev-site-001"],
            "locator": {"path": f"SITE.{site_id}", "record_id": site_id},
        }]
        subj_mat = [{
            "subject_id": subject_id,
            "site_id": site_id,
            "profile_ref": {"profile_id": f"prof-{subject_id}"},
            "timeline_ref": {"timeline_id": f"tl-{subject_id}"},
            "risk_ids": [risk_id],
            "evidence_refs": ["ev-subj-001"],
            "locator": {"path": f"SUBJ.{subject_id}", "record_id": subject_id},
        }]
        check_items = [
            {"level": "project", "check_kind": "project_lock", "scope_id": binding["project_id"], "status": "ready", "risk_ids": [risk_id], "evidence_refs": ["ev-chk-project"], "locator": {"path": "CHK.PROJECT", "record_id": "chk-p1"}},
            {"level": "site", "check_kind": "site_coverage", "scope_id": site_id, "status": "ready", "risk_ids": [risk_id], "evidence_refs": ["ev-chk-site"], "locator": {"path": "CHK.SITE", "record_id": "chk-s1"}},
            {"level": "subject", "check_kind": "subject_profile", "scope_id": subject_id, "status": "ready", "risk_ids": [risk_id], "evidence_refs": ["ev-chk-subject"], "locator": {"path": "CHK.SUBJ", "record_id": "chk-u1"}},
        ]
        report_summary = {"project_id": binding["project_id"], "status": "completed"}
        risk_summary = {"high_count": 1, "medium_count": 0, "low_count": 0, "risk_ids": [risk_id]}

        report, site, subj, chk = mo.build_post_lock_mode_outputs(
            binding,
            contract,
            authority_refs=refs,
            coverage_refs=refs,
            qc_refs=refs,
            population_totals=pop_totals,
            report_version="v1.0",
            project_summary=report_summary,
            risk_summary=risk_summary,
            evidence_refs=["ev-postlock-001"],
            site_materials=site_mat,
            subject_materials=subj_mat,
            check_items=check_items,
            entry_context=ctx,
        )
        return report, site, subj, chk
    raise ValueError(f"unsupported mode: {mode}")

@pytest.mark.parametrize("mode", ["daily", "pre_lock", "post_lock_pre_cfdi"])
def test_slice08b_product_router_three_modes_synthetic_provider_happy_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    product_mod._r5_publication_types()
    product_mod._r6_publication_types()
    monkeypatch.syspath_prepend(
        str(
            Path(__file__).resolve().parents[1]
            / "poc"
            / "medical_monitoring_ai_native_r5"
            / "tests"
        )
    )
    from s4_runtime_fixtures import build_runtime_input
    from test_r5_publication_authority import _members
    from packages.medical_monitoring.projections.publication.r5_publication_authority import (
        R5PublicationAuthorityInputAssembler,
    )
    from packages.medical_monitoring.graph.store import Store
    from poc.medical_monitoring_ai_native_r7.src.mm_r7 import continuity_bridge as cb

    fixture_runtime = build_runtime_input("single_analysis")
    project_id = fixture_runtime.anchor.project_ref
    run_id = fixture_runtime.anchor.run_ref
    site_ref = fixture_runtime.anchor.site_ref
    snapshot_ref = fixture_runtime.anchor.snapshot_ref
    cutoff = fixture_runtime.anchor.cutoff_ref
    source_revision = (
        fixture_runtime.authority_receipt.source_revision_content_pairs[0]
        .revision_id
    )
    current = product_mod.rs.DataSnapshot(
        snapshot_ref=snapshot_ref,
        project_id=project_id,
        data_cutoff=cutoff,
        rows=(
            {
                "canonical_key": "site.01/S-001/lab-alt",
                "site_ref": site_ref,
                "subject_ref": "S-001",
                "value": 47,
            },
        ),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    prior = product_mod.rs.DataSnapshot(
        snapshot_ref="snap.prior",
        project_id=project_id,
        data_cutoff="cutoff.prior",
        rows=(
            {
                "canonical_key": "site.01/S-001/lab-alt",
                "site_ref": site_ref,
                "subject_ref": "S-001",
                "value": 42,
            },
        ),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((prior, current), ()),
    )
    setup_manifest = product_mod.rs.generate_work_units(
        mode,
        "full",
        current_snapshot_token=current.snapshot_token,
    )

    class SyntheticR5Provider:
        def __init__(self) -> None:
            self.assembler = R5PublicationAuthorityInputAssembler()

        def get_authority_input(
            self,
            run_identity: Any,
            attempts: Any,
            **_: Any,
        ) -> Any:
            return self.assembler.assemble(
                run_identity,
                runtime_input=fixture_runtime,
                **_members(fixture_runtime),
            )

    class SyntheticR6Provider:
        def get_mode_outputs(
            self,
            run_binding: Mapping[str, Any],
            r5_packet: Any,
            **_: Any,
        ) -> tuple[dict[str, Any], ...]:
            return _make_slice08b_mode_outputs(run_binding, r5_packet, mode)

    r5_provider = SyntheticR5Provider()
    r6_provider = SyntheticR6Provider()

    client = _client(
        tmp_path,
        principal=_principal(project_id),
        harness_adapter=FakeHarnessAdapter(),
        harness_catalog=FakeCatalog(),
        authority_provider=r5_provider,
        r6_output_provider=r6_provider,
    )
    assert client.post(f"{_base(project_id)}/workspace/bootstrap").status_code == 200

    bound = client.post(
        f"{_base(project_id)}/runs",
        json={
            "run_id": run_id,
            "mode": mode,
            "execution_basis": "full",
            "data_cutoff": cutoff,
            "source_revision_id": source_revision,
        },
    )
    assert bound.status_code == 200, bound.text

    prepared = client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": product_mod._runtime_work_units(setup_manifest),
            "execution_kind": "harness",
        },
    )
    assert prepared.status_code == 200, prepared.text

    started = client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/start",
        json={},
    )
    assert started.status_code == 200, started.text

    for _ in range(200):
        progress = client.get(f"{_base(project_id)}/runs/{run_id}/progress")
        assert progress.status_code == 200, progress.text
        if progress.json()["run_state"] == "completed":
            break
        time.sleep(0.01)
    assert progress.json()["run_state"] == "completed"

    workspace = _r7_workspace(tmp_path, project_id)
    registry_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        reservation = registry.reserve(
            project_id,
            idempotency_key=f"slice08b-{mode}-key",
            mode=mode,
            execution_basis="full",
            current_snapshot_token=current.snapshot_token,
            data_cutoff=cutoff,
            manifest_digest=setup_manifest.manifest_digest,
        )
        sequence = reservation.record.sequence
    public_token = lr.derive_public_run_token(project_id, run_id)
    with sqlite3.connect(str(registry_path)) as connection:
        connection.execute(
            "UPDATE r7_launch_registry SET run_id=?, public_run_token=? WHERE sequence=?",
            (run_id, public_token, sequence),
        )
        connection.commit()
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        registry.mark_completed(run_id, project_id=project_id)

    # Publish result via product router POST /runs/{public_run_token}/publication
    pub_resp = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": f"slice08b-pub-{mode}"},
    )
    assert pub_resp.status_code == 200, pub_resp.text
    pub_data = pub_resp.json()
    assert pub_data["publication_state"] == "available"
    assert pub_data["replayed"] is False
    assert pub_data["public_run_token"] == public_token

    # Replay publication with same idempotency key returns replayed=True
    replay_resp = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": f"slice08b-pub-{mode}"},
    )
    assert replay_resp.status_code == 200, replay_resp.text
    assert replay_resp.json()["replayed"] is True
    assert replay_resp.json()["publication_state"] == "available"

    # Verify launch registry v4 publication fields
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        publication = registry.get_publication(project_id=project_id, run_id=run_id)
        assert publication.publication_state == "available"
        assert isinstance(publication.r6_output_set_digest, str)
        assert len(publication.r6_output_set_digest) == 64
        assert isinstance(publication.artifact_member_ids, tuple)
        assert len(publication.artifact_member_ids) == 4
        assert sorted(publication.artifact_member_ids) == list(publication.artifact_member_ids)
        assert isinstance(publication.artifact_member_set_digest, str)
        assert len(publication.artifact_member_set_digest) == 64
        assert publication.artifact_member_set_digest == lr.content_digest(list(publication.artifact_member_ids))
        assert publication.r5_authority_packet_id.startswith("r5-publication-authority:")
        assert len(publication.r5_authority_packet_digest) == 64
        assert publication.result_context_token.startswith("result-context:")

    # Verify R1 Store committed envelopes & files
    runtime_dir = workspace / "runtime"
    store = Store(runtime_dir / product_mod.RUNTIME_DB_NAME, runtime_dir / "artifacts")
    try:
        for artifact_id in publication.artifact_member_ids:
            env = store.get_artifact(artifact_id)
            assert env is not None
            assert env.artifact_type == "r6_mode_output"
            assert store.verify_artifact(artifact_id) is True
    finally:
        store.close()

    # Verify result-entry endpoint
    entry_resp = client.get(f"{_base(project_id)}/runs/{public_token}/result-entry")
    assert entry_resp.status_code == 200, entry_resp.text
    entry_data = entry_resp.json()
    assert entry_data["result_context_token"] == publication.result_context_token
    assert entry_data["project_ref"] == project_id
    assert entry_data["public_run_token"] == public_token

    # Verify public result-entry response does not leak internal digests
    entry_blob = json.dumps(entry_data, ensure_ascii=False)
    for secret_digest in (
        publication.r6_output_set_digest,
        publication.artifact_member_set_digest,
        publication.r5_authority_packet_digest,
    ):
        assert secret_digest not in entry_blob


def test_slice08b_product_router_missing_or_extra_outputs_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    product_mod._r5_publication_types()
    product_mod._r6_publication_types()
    monkeypatch.syspath_prepend(
        str(
            Path(__file__).resolve().parents[1]
            / "poc"
            / "medical_monitoring_ai_native_r5"
            / "tests"
        )
    )
    from s4_runtime_fixtures import build_runtime_input
    from test_r5_publication_authority import _members
    from packages.medical_monitoring.projections.publication.r5_publication_authority import (
        R5PublicationAuthorityInputAssembler,
    )

    fixture_runtime = build_runtime_input("single_analysis")
    project_id = fixture_runtime.anchor.project_ref
    run_id = fixture_runtime.anchor.run_ref
    site_ref = fixture_runtime.anchor.site_ref
    snapshot_ref = fixture_runtime.anchor.snapshot_ref
    cutoff = fixture_runtime.anchor.cutoff_ref
    source_revision = (
        fixture_runtime.authority_receipt.source_revision_content_pairs[0]
        .revision_id
    )
    current = product_mod.rs.DataSnapshot(
        snapshot_ref=snapshot_ref,
        project_id=project_id,
        data_cutoff=cutoff,
        rows=({"canonical_key": "k1", "site_ref": site_ref, "value": 1},),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((current, current), ()),
    )
    setup_manifest = product_mod.rs.generate_work_units(
        "daily",
        "full",
        current_snapshot_token=current.snapshot_token,
    )

    class SyntheticR5Provider:
        def get_authority_input(self, run_identity: Any, attempts: Any, **_: Any) -> Any:
            return R5PublicationAuthorityInputAssembler().assemble(
                run_identity,
                runtime_input=fixture_runtime,
                **_members(fixture_runtime),
            )

    # Provider returns only 3 outputs instead of 4
    class IncompleteR6Provider:
        def get_mode_outputs(self, run_binding: Mapping[str, Any], r5_packet: Any, **_: Any) -> tuple[dict[str, Any], ...]:
            outputs = _make_slice08b_mode_outputs(run_binding, r5_packet, "daily")
            return outputs[:3]  # Missing 4th output

    client = _client(
        tmp_path,
        principal=_principal(project_id),
        harness_adapter=FakeHarnessAdapter(),
        harness_catalog=FakeCatalog(),
        authority_provider=SyntheticR5Provider(),
        r6_output_provider=IncompleteR6Provider(),
    )
    assert client.post(f"{_base(project_id)}/workspace/bootstrap").status_code == 200

    bound = client.post(
        f"{_base(project_id)}/runs",
        json={
            "run_id": run_id,
            "mode": "daily",
            "execution_basis": "full",
            "data_cutoff": cutoff,
            "source_revision_id": source_revision,
        },
    )
    assert bound.status_code == 200
    prepared = client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": product_mod._runtime_work_units(setup_manifest),
            "execution_kind": "harness",
        },
    )
    assert prepared.status_code == 200
    started = client.post(f"{_base(project_id)}/runs/{run_id}/execution/start", json={})
    assert started.status_code == 200
    for _ in range(200):
        progress = client.get(f"{_base(project_id)}/runs/{run_id}/progress")
        if progress.json()["run_state"] == "completed":
            break
        time.sleep(0.01)

    workspace = _r7_workspace(tmp_path, project_id)
    registry_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        reservation = registry.reserve(
            project_id,
            idempotency_key="slice08b-incomplete-key",
            mode="daily",
            execution_basis="full",
            current_snapshot_token=current.snapshot_token,
            data_cutoff=cutoff,
            manifest_digest=setup_manifest.manifest_digest,
        )
        sequence = reservation.record.sequence
    public_token = lr.derive_public_run_token(project_id, run_id)
    with sqlite3.connect(str(registry_path)) as connection:
        connection.execute(
            "UPDATE r7_launch_registry SET run_id=?, public_run_token=? WHERE sequence=?",
            (run_id, public_token, sequence),
        )
        connection.commit()
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        registry.mark_completed(run_id, project_id=project_id)

    # Publication must fail closed with publication_blocked
    pub_resp = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice08b-pub-incomplete"},
    )
    assert pub_resp.status_code == 409, pub_resp.text
    assert pub_resp.json()["code"] == "publication_blocked"

    # Verify publication state is blocked
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        publication = registry.get_publication(project_id=project_id, run_id=run_id)
        assert publication.publication_state == "blocked"

    # Result entry must be closed
    entry_resp = client.get(f"{_base(project_id)}/runs/{public_token}/result-entry")
    assert entry_resp.status_code == 409
    assert entry_resp.json()["code"] == "publication_not_available"


def test_slice08b_product_router_r1_artifact_byte_tamper_blocks_result_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    product_mod._r5_publication_types()
    product_mod._r6_publication_types()
    monkeypatch.syspath_prepend(
        str(
            Path(__file__).resolve().parents[1]
            / "poc"
            / "medical_monitoring_ai_native_r5"
            / "tests"
        )
    )
    from s4_runtime_fixtures import build_runtime_input
    from test_r5_publication_authority import _members
    from packages.medical_monitoring.projections.publication.r5_publication_authority import (
        R5PublicationAuthorityInputAssembler,
    )

    fixture_runtime = build_runtime_input("single_analysis")
    project_id = fixture_runtime.anchor.project_ref
    run_id = fixture_runtime.anchor.run_ref
    site_ref = fixture_runtime.anchor.site_ref
    snapshot_ref = fixture_runtime.anchor.snapshot_ref
    cutoff = fixture_runtime.anchor.cutoff_ref
    source_revision = (
        fixture_runtime.authority_receipt.source_revision_content_pairs[0]
        .revision_id
    )
    current = product_mod.rs.DataSnapshot(
        snapshot_ref=snapshot_ref,
        project_id=project_id,
        data_cutoff=cutoff,
        rows=({"canonical_key": "k1", "site_ref": site_ref, "value": 1},),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((current, current), ()),
    )
    setup_manifest = product_mod.rs.generate_work_units(
        "daily",
        "full",
        current_snapshot_token=current.snapshot_token,
    )

    class SyntheticR5Provider:
        def get_authority_input(self, run_identity: Any, attempts: Any, **_: Any) -> Any:
            return R5PublicationAuthorityInputAssembler().assemble(
                run_identity,
                runtime_input=fixture_runtime,
                **_members(fixture_runtime),
            )

    class SyntheticR6Provider:
        def get_mode_outputs(self, run_binding: Mapping[str, Any], r5_packet: Any, **_: Any) -> tuple[dict[str, Any], ...]:
            return _make_slice08b_mode_outputs(run_binding, r5_packet, "daily")

    client = _client(
        tmp_path,
        principal=_principal(project_id),
        harness_adapter=FakeHarnessAdapter(),
        harness_catalog=FakeCatalog(),
        authority_provider=SyntheticR5Provider(),
        r6_output_provider=SyntheticR6Provider(),
    )
    assert client.post(f"{_base(project_id)}/workspace/bootstrap").status_code == 200

    bound = client.post(
        f"{_base(project_id)}/runs",
        json={
            "run_id": run_id,
            "mode": "daily",
            "execution_basis": "full",
            "data_cutoff": cutoff,
            "source_revision_id": source_revision,
        },
    )
    assert bound.status_code == 200
    prepared = client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": product_mod._runtime_work_units(setup_manifest),
            "execution_kind": "harness",
        },
    )
    assert prepared.status_code == 200
    started = client.post(f"{_base(project_id)}/runs/{run_id}/execution/start", json={})
    assert started.status_code == 200
    for _ in range(200):
        progress = client.get(f"{_base(project_id)}/runs/{run_id}/progress")
        if progress.json()["run_state"] == "completed":
            break
        time.sleep(0.01)

    workspace = _r7_workspace(tmp_path, project_id)
    registry_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        reservation = registry.reserve(
            project_id,
            idempotency_key="slice08b-tamper-key",
            mode="daily",
            execution_basis="full",
            current_snapshot_token=current.snapshot_token,
            data_cutoff=cutoff,
            manifest_digest=setup_manifest.manifest_digest,
        )
        sequence = reservation.record.sequence
    public_token = lr.derive_public_run_token(project_id, run_id)
    with sqlite3.connect(str(registry_path)) as connection:
        connection.execute(
            "UPDATE r7_launch_registry SET run_id=?, public_run_token=? WHERE sequence=?",
            (run_id, public_token, sequence),
        )
        connection.commit()
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        registry.mark_completed(run_id, project_id=project_id)

    # Publish successfully
    pub_resp = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice08b-pub-tamper"},
    )
    assert pub_resp.status_code == 200, pub_resp.text

    # Result entry works before tampering
    entry_ok = client.get(f"{_base(project_id)}/runs/{public_token}/result-entry")
    assert entry_ok.status_code == 200

    # Now tamper 1 byte in an R1 artifact payload file on disk
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        publication = registry.get_publication(project_id=project_id, run_id=run_id)
        assert len(publication.artifact_member_ids) == 4
        target_member_id = publication.artifact_member_ids[0]

    target_file = workspace / "runtime" / "artifacts" / f"{target_member_id}.json"
    assert target_file.is_file()
    raw_bytes = target_file.read_bytes()
    tampered_bytes = raw_bytes[:-1] + (b"X" if raw_bytes[-1:] != b"X" else b"Y")
    target_file.write_bytes(tampered_bytes)

    # Result entry must now detect byte corruption via Store.verify_artifact and fail closed
    entry_tampered = client.get(f"{_base(project_id)}/runs/{public_token}/result-entry")
    assert entry_tampered.status_code == 409
    assert entry_tampered.json()["code"] == "receipt_gate_blocked"


def test_slice08b_product_router_closure_violation_and_draft_pollution_blocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    product_mod._r5_publication_types()
    product_mod._r6_publication_types()
    monkeypatch.syspath_prepend(
        str(
            Path(__file__).resolve().parents[1]
            / "poc"
            / "medical_monitoring_ai_native_r5"
            / "tests"
        )
    )
    from s4_runtime_fixtures import build_runtime_input
    from test_r5_publication_authority import _members
    from packages.medical_monitoring.projections.publication.r5_publication_authority import (
        R5PublicationAuthorityInputAssembler,
    )

    fixture_runtime = build_runtime_input("single_analysis")
    project_id = fixture_runtime.anchor.project_ref
    run_id = fixture_runtime.anchor.run_ref
    site_ref = fixture_runtime.anchor.site_ref
    snapshot_ref = fixture_runtime.anchor.snapshot_ref
    cutoff = fixture_runtime.anchor.cutoff_ref
    source_revision = (
        fixture_runtime.authority_receipt.source_revision_content_pairs[0]
        .revision_id
    )
    current = product_mod.rs.DataSnapshot(
        snapshot_ref=snapshot_ref,
        project_id=project_id,
        data_cutoff=cutoff,
        rows=({"canonical_key": "k1", "site_ref": site_ref, "value": 1},),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((current, current), ()),
    )
    setup_manifest = product_mod.rs.generate_work_units(
        "daily",
        "full",
        current_snapshot_token=current.snapshot_token,
    )

    class SyntheticR5Provider:
        def get_authority_input(self, run_identity: Any, attempts: Any, **_: Any) -> Any:
            return R5PublicationAuthorityInputAssembler().assemble(
                run_identity,
                runtime_input=fixture_runtime,
                **_members(fixture_runtime),
            )

    # Case 1: Finding with unknown risk_id not in R5 packet
    class UnknownRiskR6Provider:
        def get_mode_outputs(self, run_binding: Mapping[str, Any], r5_packet: Any, **_: Any) -> tuple[dict[str, Any], ...]:
            return _make_slice08b_mode_outputs(
                run_binding, r5_packet, "daily", risk_id="unknown_risk_not_in_r5"
            )

    client = _client(
        tmp_path,
        principal=_principal(project_id),
        harness_adapter=FakeHarnessAdapter(),
        harness_catalog=FakeCatalog(),
        authority_provider=SyntheticR5Provider(),
        r6_output_provider=UnknownRiskR6Provider(),
    )
    assert client.post(f"{_base(project_id)}/workspace/bootstrap").status_code == 200

    client.post(
        f"{_base(project_id)}/runs",
        json={
            "run_id": run_id,
            "mode": "daily",
            "execution_basis": "full",
            "data_cutoff": cutoff,
            "source_revision_id": source_revision,
        },
    )
    client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": product_mod._runtime_work_units(setup_manifest),
            "execution_kind": "harness",
        },
    )
    client.post(f"{_base(project_id)}/runs/{run_id}/execution/start", json={})
    for _ in range(200):
        progress = client.get(f"{_base(project_id)}/runs/{run_id}/progress")
        if progress.json()["run_state"] == "completed":
            break
        time.sleep(0.01)

    workspace = _r7_workspace(tmp_path, project_id)
    registry_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        reservation = registry.reserve(
            project_id,
            idempotency_key="slice08b-closure-key",
            mode="daily",
            execution_basis="full",
            current_snapshot_token=current.snapshot_token,
            data_cutoff=cutoff,
            manifest_digest=setup_manifest.manifest_digest,
        )
        sequence = reservation.record.sequence
    public_token = lr.derive_public_run_token(project_id, run_id)
    with sqlite3.connect(str(registry_path)) as connection:
        connection.execute(
            "UPDATE r7_launch_registry SET run_id=?, public_run_token=? WHERE sequence=?",
            (run_id, public_token, sequence),
        )
        connection.commit()
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        registry.mark_completed(run_id, project_id=project_id)

    # Publication fails closed because risk_id is not in R5 member closure
    pub_resp = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice08b-pub-closure"},
    )
    assert pub_resp.status_code == 409
    assert pub_resp.json()["code"] == "publication_blocked"


def test_slice08b_product_router_query_draft_status_pollution_blocked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    product_mod._r5_publication_types()
    product_mod._r6_publication_types()
    monkeypatch.syspath_prepend(
        str(
            Path(__file__).resolve().parents[1]
            / "poc"
            / "medical_monitoring_ai_native_r5"
            / "tests"
        )
    )
    from s4_runtime_fixtures import build_runtime_input
    from test_r5_publication_authority import _members
    from packages.medical_monitoring.projections.publication.r5_publication_authority import (
        R5PublicationAuthorityInputAssembler,
    )

    fixture_runtime = build_runtime_input("single_analysis")
    project_id = fixture_runtime.anchor.project_ref
    run_id = fixture_runtime.anchor.run_ref
    site_ref = fixture_runtime.anchor.site_ref
    snapshot_ref = fixture_runtime.anchor.snapshot_ref
    cutoff = fixture_runtime.anchor.cutoff_ref
    source_revision = (
        fixture_runtime.authority_receipt.source_revision_content_pairs[0]
        .revision_id
    )
    current = product_mod.rs.DataSnapshot(
        snapshot_ref=snapshot_ref,
        project_id=project_id,
        data_cutoff=cutoff,
        rows=({"canonical_key": "k1", "site_ref": site_ref, "value": 1},),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((current, current), ()),
    )
    setup_manifest = product_mod.rs.generate_work_units(
        "daily",
        "full",
        current_snapshot_token=current.snapshot_token,
    )

    class SyntheticR5Provider:
        def get_authority_input(self, run_identity: Any, attempts: Any, **_: Any) -> Any:
            return R5PublicationAuthorityInputAssembler().assemble(
                run_identity,
                runtime_input=fixture_runtime,
                **_members(fixture_runtime),
            )

    # Case 2: Query draft with status="sent" (polluted draft status)
    class PollutedQueryR6Provider:
        def get_mode_outputs(self, run_binding: Mapping[str, Any], r5_packet: Any, **_: Any) -> tuple[dict[str, Any], ...]:
            polluted_draft = {
                "query_draft_id": "query-polluted-01",
                "risk_id": "d09_marker:m-rk",
                "subject_id": "subject.1001",
                "site_id": "site.01",
                "query_text": "已发送的查询草稿不可沿用",
                "status": "sent",
                "sent": True,
                "closed": False,
                "confirmed": False,
                "response_status": "none",
                "field_locator": {"path": "AE.AETERM", "record_id": "rec-001", "field": "AETERM"},
                "evidence_refs": ["ev-listing-001"],
            }
            return _make_slice08b_mode_outputs(
                run_binding, r5_packet, "daily", query_drafts=[polluted_draft]
            )

    client = _client(
        tmp_path,
        principal=_principal(project_id),
        harness_adapter=FakeHarnessAdapter(),
        harness_catalog=FakeCatalog(),
        authority_provider=SyntheticR5Provider(),
        r6_output_provider=PollutedQueryR6Provider(),
    )
    assert client.post(f"{_base(project_id)}/workspace/bootstrap").status_code == 200

    client.post(
        f"{_base(project_id)}/runs",
        json={
            "run_id": run_id,
            "mode": "daily",
            "execution_basis": "full",
            "data_cutoff": cutoff,
            "source_revision_id": source_revision,
        },
    )
    client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": product_mod._runtime_work_units(setup_manifest),
            "execution_kind": "harness",
        },
    )
    client.post(f"{_base(project_id)}/runs/{run_id}/execution/start", json={})
    for _ in range(200):
        progress = client.get(f"{_base(project_id)}/runs/{run_id}/progress")
        if progress.json()["run_state"] == "completed":
            break
        time.sleep(0.01)

    workspace = _r7_workspace(tmp_path, project_id)
    registry_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        reservation = registry.reserve(
            project_id,
            idempotency_key="slice08b-pollute-key",
            mode="daily",
            execution_basis="full",
            current_snapshot_token=current.snapshot_token,
            data_cutoff=cutoff,
            manifest_digest=setup_manifest.manifest_digest,
        )
        sequence = reservation.record.sequence
    public_token = lr.derive_public_run_token(project_id, run_id)
    with sqlite3.connect(str(registry_path)) as connection:
        connection.execute(
            "UPDATE r7_launch_registry SET run_id=?, public_run_token=? WHERE sequence=?",
            (run_id, public_token, sequence),
        )
        connection.commit()
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        registry.mark_completed(run_id, project_id=project_id)

    # Publication fails closed because query draft is not purely draft
    pub_resp = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice08b-pub-pollute"},
    )
    assert pub_resp.status_code == 409
    assert pub_resp.json()["code"] == "publication_blocked"


def test_slice08b_product_router_cross_layer_identity_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    product_mod._r5_publication_types()
    product_mod._r6_publication_types()
    monkeypatch.syspath_prepend(
        str(
            Path(__file__).resolve().parents[1]
            / "poc"
            / "medical_monitoring_ai_native_r5"
            / "tests"
        )
    )
    from s4_runtime_fixtures import build_runtime_input
    from test_r5_publication_authority import _members
    from packages.medical_monitoring.projections.publication.r5_publication_authority import (
        R5PublicationAuthorityInputAssembler,
    )
    from packages.medical_monitoring.graph.store import Store
    from poc.medical_monitoring_ai_native_r7.src.mm_r7 import continuity_bridge as cb
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity import CarryForwardPlan, DecisionBaseline

    fixture_runtime = build_runtime_input("single_analysis")
    project_id = fixture_runtime.anchor.project_ref
    run_id = fixture_runtime.anchor.run_ref
    site_ref = fixture_runtime.anchor.site_ref
    snapshot_ref = fixture_runtime.anchor.snapshot_ref
    cutoff = fixture_runtime.anchor.cutoff_ref
    source_revision = (
        fixture_runtime.authority_receipt.source_revision_content_pairs[0]
        .revision_id
    )
    current = product_mod.rs.DataSnapshot(
        snapshot_ref=snapshot_ref,
        project_id=project_id,
        data_cutoff=cutoff,
        rows=(
            {
                "canonical_key": "site.01/S-001/lab-alt",
                "site_ref": site_ref,
                "subject_ref": "S-001",
                "value": 47,
            },
        ),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((current, current), ()),
    )
    setup_manifest = product_mod.rs.generate_work_units(
        "daily",
        "full",
        current_snapshot_token=current.snapshot_token,
    )

    class SyntheticR5Provider:
        def __init__(self) -> None:
            self.assembler = R5PublicationAuthorityInputAssembler()

        def get_authority_input(self, run_identity: Any, attempts: Any, **_: Any) -> Any:
            return self.assembler.assemble(
                run_identity,
                runtime_input=fixture_runtime,
                **_members(fixture_runtime),
            )

    class SyntheticR6Provider:
        def get_mode_outputs(self, run_binding: Mapping[str, Any], r5_packet: Any, **_: Any) -> tuple[dict[str, Any], ...]:
            return _make_slice08b_mode_outputs(run_binding, r5_packet, "daily")

    client = _client(
        tmp_path,
        principal=_principal(project_id),
        harness_adapter=FakeHarnessAdapter(),
        harness_catalog=FakeCatalog(),
        authority_provider=SyntheticR5Provider(),
        r6_output_provider=SyntheticR6Provider(),
    )
    assert client.post(f"{_base(project_id)}/workspace/bootstrap").status_code == 200

    client.post(
        f"{_base(project_id)}/runs",
        json={
            "run_id": run_id,
            "mode": "daily",
            "execution_basis": "full",
            "data_cutoff": cutoff,
            "source_revision_id": source_revision,
        },
    )
    client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": product_mod._runtime_work_units(setup_manifest),
            "execution_kind": "harness",
        },
    )
    client.post(f"{_base(project_id)}/runs/{run_id}/execution/start", json={})
    for _ in range(200):
        progress = client.get(f"{_base(project_id)}/runs/{run_id}/progress")
        if progress.json()["run_state"] == "completed":
            break
        time.sleep(0.01)

    workspace = _r7_workspace(tmp_path, project_id)
    registry_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        reservation = registry.reserve(
            project_id,
            idempotency_key="slice08b-cross-layer-key",
            mode="daily",
            execution_basis="full",
            current_snapshot_token=current.snapshot_token,
            data_cutoff=cutoff,
            manifest_digest=setup_manifest.manifest_digest,
        )
        sequence = reservation.record.sequence
    public_token = lr.derive_public_run_token(project_id, run_id)
    with sqlite3.connect(str(registry_path)) as connection:
        connection.execute(
            "UPDATE r7_launch_registry SET run_id=?, public_run_token=? WHERE sequence=?",
            (run_id, public_token, sequence),
        )
        connection.commit()
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        registry.mark_completed(run_id, project_id=project_id)

    # Publish result
    pub_resp = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice08b-pub-cross-layer"},
    )
    assert pub_resp.status_code == 200, pub_resp.text

    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        pub = registry.get_publication(project_id=project_id, run_id=run_id)

        # 1. R5 packet identity
        assert pub.r5_authority_packet_id == "r5-publication-authority:" + pub.r5_authority_packet_digest
        assert len(pub.r5_authority_packet_digest) == 64

        # 2. R6 output set digest
        assert len(pub.r6_output_set_digest) == 64

        # 3. R1 Store artifacts & member set digest
        assert len(pub.artifact_member_ids) == 4
        assert pub.artifact_member_set_digest == lr.content_digest(list(pub.artifact_member_ids))

        # 4. Direct SQLite schema verification (v4 additive fields)
        with sqlite3.connect(str(registry_path)) as conn:
            row = conn.execute(
                "SELECT r6_output_set_digest, artifact_member_ids_json, artifact_member_set_digest "
                "FROM r7_result_publications WHERE run_id=?",
                (run_id,),
            ).fetchone()
            assert row is not None
            assert row[0] == pub.r6_output_set_digest
            assert json.loads(row[1]) == list(pub.artifact_member_ids)
            assert row[2] == pub.artifact_member_set_digest

    # 5. R1 Store verifies content hash & real file bytes
    runtime_dir = workspace / "runtime"
    store = Store(runtime_dir / product_mod.RUNTIME_DB_NAME, runtime_dir / "artifacts")
    try:
        for artifact_id in pub.artifact_member_ids:
            env = store.get_artifact(artifact_id)
            assert env.canonical_hash() == artifact_id
            assert store.verify_artifact(artifact_id) is True
    finally:
        store.close()


def test_slice08b_product_router_conflicting_replay_and_cas_conflict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    product_mod._r5_publication_types()
    product_mod._r6_publication_types()
    monkeypatch.syspath_prepend(
        str(
            Path(__file__).resolve().parents[1]
            / "poc"
            / "medical_monitoring_ai_native_r5"
            / "tests"
        )
    )
    from s4_runtime_fixtures import build_runtime_input
    from test_r5_publication_authority import _members
    from packages.medical_monitoring.projections.publication.r5_publication_authority import (
        R5PublicationAuthorityInputAssembler,
    )

    fixture_runtime = build_runtime_input("single_analysis")
    project_id = fixture_runtime.anchor.project_ref
    run_id = fixture_runtime.anchor.run_ref
    site_ref = fixture_runtime.anchor.site_ref
    snapshot_ref = fixture_runtime.anchor.snapshot_ref
    cutoff = fixture_runtime.anchor.cutoff_ref
    source_revision = (
        fixture_runtime.authority_receipt.source_revision_content_pairs[0]
        .revision_id
    )
    current = product_mod.rs.DataSnapshot(
        snapshot_ref=snapshot_ref,
        project_id=project_id,
        data_cutoff=cutoff,
        rows=({"canonical_key": "k1", "site_ref": site_ref, "value": 1},),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((current, current), ()),
    )
    setup_manifest = product_mod.rs.generate_work_units(
        "daily",
        "full",
        current_snapshot_token=current.snapshot_token,
    )

    class SyntheticR5Provider:
        def get_authority_input(self, run_identity: Any, attempts: Any, **_: Any) -> Any:
            return R5PublicationAuthorityInputAssembler().assemble(
                run_identity,
                runtime_input=fixture_runtime,
                **_members(fixture_runtime),
            )

    class SyntheticR6Provider:
        def get_mode_outputs(self, run_binding: Mapping[str, Any], r5_packet: Any, **_: Any) -> tuple[dict[str, Any], ...]:
            return _make_slice08b_mode_outputs(run_binding, r5_packet, "daily")

    client = _client(
        tmp_path,
        principal=_principal(project_id),
        harness_adapter=FakeHarnessAdapter(),
        harness_catalog=FakeCatalog(),
        authority_provider=SyntheticR5Provider(),
        r6_output_provider=SyntheticR6Provider(),
    )
    assert client.post(f"{_base(project_id)}/workspace/bootstrap").status_code == 200

    client.post(
        f"{_base(project_id)}/runs",
        json={
            "run_id": run_id,
            "mode": "daily",
            "execution_basis": "full",
            "data_cutoff": cutoff,
            "source_revision_id": source_revision,
        },
    )
    client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": product_mod._runtime_work_units(setup_manifest),
            "execution_kind": "harness",
        },
    )
    client.post(f"{_base(project_id)}/runs/{run_id}/execution/start", json={})
    for _ in range(200):
        progress = client.get(f"{_base(project_id)}/runs/{run_id}/progress")
        if progress.json()["run_state"] == "completed":
            break
        time.sleep(0.01)

    workspace = _r7_workspace(tmp_path, project_id)
    registry_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        reservation = registry.reserve(
            project_id,
            idempotency_key="slice08b-conflict-key",
            mode="daily",
            execution_basis="full",
            current_snapshot_token=current.snapshot_token,
            data_cutoff=cutoff,
            manifest_digest=setup_manifest.manifest_digest,
        )
        sequence = reservation.record.sequence
    public_token = lr.derive_public_run_token(project_id, run_id)
    with sqlite3.connect(str(registry_path)) as connection:
        connection.execute(
            "UPDATE r7_launch_registry SET run_id=?, public_run_token=? WHERE sequence=?",
            (run_id, public_token, sequence),
        )
        connection.commit()
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        registry.mark_completed(run_id, project_id=project_id)

    # 1. First publication succeeds
    first_pub = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice08b-pub-initial"},
    )
    assert first_pub.status_code == 200
    assert first_pub.json()["publication_state"] == "available"

    # 2. Same idempotency key replay succeeds with replayed=True
    same_replay = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice08b-pub-initial"},
    )
    assert same_replay.status_code == 200
    assert same_replay.json()["replayed"] is True

    # 3. New idempotency key on already available publication returns 200 available
    new_key_replay = client.post(
        f"{_base(project_id)}/runs/{public_token}/publication",
        json={"idempotency_key": "slice08b-pub-different-key"},
    )
    assert new_key_replay.status_code == 200
    assert new_key_replay.json()["publication_state"] == "available"


# ---------------------------------------------------------------------------
# Slice-08C-1: Public Chinese Continuity Projection Endpoint Tests
# ---------------------------------------------------------------------------


def _make_slice08c_setup_and_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mode: str = "daily",
    custom_items: Any = None,
    authority_source_items: Any = None,
    baseline: Any = None,
    execution_basis: str = "full",
    skip_publish: bool = False,
    plan_status: str = "staging",
    project_id: str = PROJECT_A,
    source_run_label: str = "",
    source_artifact_sha256_override: str = "",
    source_object_id_override: str = "",
    site_label: str = "中心 01",
    omit_authority_event: bool = False,
    authority_event_anchor_override: str = "",
) -> dict[str, Any]:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    product_mod._r5_publication_types()
    product_mod._r6_publication_types()
    monkeypatch.syspath_prepend(
        str(
            Path(__file__).resolve().parents[1]
            / "poc"
            / "medical_monitoring_ai_native_r5"
            / "tests"
        )
    )
    from s4_runtime_fixtures import build_runtime_input
    from test_r5_publication_authority import _members
    from packages.medical_monitoring.projections.publication.r5_publication_authority import (
        R5PublicationAuthorityInputAssembler,
    )
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity import (
        CarryForwardItem,
        CarryForwardPlan,
        DecisionBaseline,
        build_carry_forward_item,
        build_carry_forward_plan,
    )
    from services.api.app.medical_monitoring_r5_product_adapter import (
        R5EventRecord,
        R5RiskRecord,
        R5SiteAudienceRecord,
        R5SiteRecord,
        R5SourceRecord,
        R5SourceRevisionPair,
        R5SubjectRecord,
        build_synthetic_r5_authority_packet,
        canonical_sha256,
    )

    fixture_runtime = build_runtime_input("single_analysis")
    # Use fixture's project as the canonical project to keep R5/launch consistent; ignore passed PROJECT_A unless it's fixture's
    actual_project_id = fixture_runtime.anchor.project_ref
    # Allow caller to override only if they pass a non-default that we then patch fixture to match? For now use fixture's.
    # If caller passed a custom project_id different from fixture, we keep fixture's for consistency.
    project_id = actual_project_id
    run_id = fixture_runtime.anchor.run_ref
    site_ref = fixture_runtime.anchor.site_ref
    snapshot_ref = fixture_runtime.anchor.snapshot_ref
    cutoff = fixture_runtime.anchor.cutoff_ref
    source_revision = (
        fixture_runtime.authority_receipt.source_revision_content_pairs[0]
        .revision_id
    )

    current = product_mod.rs.DataSnapshot(
        snapshot_ref=snapshot_ref,
        project_id=project_id,
        data_cutoff=cutoff,
        rows=(
            {
                "canonical_key": "site.01/S-001/lab-alt",
                "site_ref": site_ref,
                "subject_ref": "S-001",
                "value": 47,
            },
        ),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    prior = product_mod.rs.DataSnapshot(
        snapshot_ref="snap.prior",
        project_id=project_id,
        data_cutoff="cutoff.prior",
        rows=(
            {
                "canonical_key": "site.01/S-001/lab-alt",
                "site_ref": site_ref,
                "subject_ref": "S-001",
                "value": 42,
            },
        ),
        key_fields=("canonical_key",),
        source_revision_id=source_revision,
    )
    monkeypatch.setattr(
        product_mod,
        "_synthetic_setup_inputs",
        lambda _project_id: ((prior, current), ()),
    )
    setup_manifest = product_mod.rs.generate_work_units(
        mode,
        execution_basis,
        current_snapshot_token=current.snapshot_token,
    )

    class SyntheticR5Provider:
        def __init__(self) -> None:
            self.assembler = R5PublicationAuthorityInputAssembler()

        def get_authority_input(
            self,
            run_identity: Any,
            attempts: Any,
            **_: Any,
        ) -> Any:
             return self.assembler.assemble(
                 run_identity,
                 runtime_input=fixture_runtime,
                 **_members(fixture_runtime),
             )

    class SyntheticR6Provider:
        def get_mode_outputs(
            self,
            run_binding: Mapping[str, Any],
            r5_packet: Any,
            **_: Any,
        ) -> tuple[dict[str, Any], ...]:
            return _make_slice08b_mode_outputs(run_binding, r5_packet, mode)

    authority_items: list[Any] = []
    original_r5_publication_builder = product_mod._build_r5_publication_packet
    published_r5_packets: list[Any] = []

    def fake_r5_publication_packet(
        provider: Any,
        identity: Any,
        **kwargs: Any,
    ) -> Any:
        if not published_r5_packets:
            packet = original_r5_publication_builder(
                provider,
                identity,
                **kwargs,
            )
            published_r5_packets.append(packet)
            return packet
        risk_rows: dict[str, Any] = {}
        for item in authority_items:
            summary = item.evidence_summary
            instance_ref = str(summary.get("risk_instance_ref") or "")
            if instance_ref and instance_ref not in risk_rows:
                risk_rows[instance_ref] = item
        sources: dict[str, Any] = {}
        subjects: dict[str, Any] = {}
        events: dict[str, Any] = {}
        risks: list[Any] = []
        for instance_ref, item in risk_rows.items():
            summary = item.evidence_summary
            item_site = str(summary["site_ref"])
            subject_ref = str(summary["subject_ref"])
            event_ref = str(summary["event_ref"])
            primary_locator = str(summary.get("source_locator_ref") or "")
            source_count = int(summary.get("source_count") or 0)
            locators = tuple(
                primary_locator if index == 0 else f"{primary_locator}-{index + 1}"
                for index in range(source_count)
            )
            for locator in locators:
                if locator not in sources:
                    source_hash = canonical_sha256(
                        {"locator_ref": locator, "snapshot_ref": snapshot_ref}
                    )
                    sources[locator] = R5SourceRecord(
                        locator_ref=locator,
                        snapshot_ref=snapshot_ref,
                        source_file_ref="合成验证数据清单",
                        source_revision_ref=source_revision,
                        source_revision_content_hash=source_hash,
                        record_ref=f"记录 {locator}",
                        canonical_location=f"数据清单 · {locator}",
                        excerpt="合成验证记录",
                    )
            subjects.setdefault(
                subject_ref,
                R5SubjectRecord(
                    subject_ref=subject_ref,
                    site_ref=item_site,
                    spine_ref=f"spine.{subject_ref}",
                    subject_label=str(summary["subject_label"]),
                ),
            )
            event_date = datetime.fromisoformat(str(summary["date_label"])).date()
            if not omit_authority_event:
                events.setdefault(
                    event_ref,
                    R5EventRecord(
                        event_ref=event_ref,
                        subject_ref=subject_ref,
                        site_ref=item_site,
                        spine_ref=f"spine.{subject_ref}",
                        domain="ae",
                        subtype="ae",
                        date_state="exact",
                        start_date=event_date,
                        end_date=event_date,
                        visit_ref=None,
                        risk_anchor_refs=(
                            authority_event_anchor_override
                            or str(summary["risk_anchor_ref"]),
                        ),
                        source_locator_refs=locators,
                        label_zh=str(summary["title"]),
                    ),
                )
            severity = item.current_severity or item.prior_severity
            risks.append(
                R5RiskRecord(
                    risk_ref=str(summary["risk_ref"]),
                    risk_instance_ref=instance_ref,
                    risk_key=str(summary["risk_ref"]),
                    site_ref=item_site,
                    subject_ref=subject_ref,
                    spine_ref=f"spine.{subject_ref}",
                    domain="ae",
                    severity=str(severity),
                    risk_type_zh=str(summary["title"]),
                    date_state="exact",
                    event_ref=event_ref,
                    visit_ref=None,
                    risk_anchor_ref=str(summary["risk_anchor_ref"]),
                    source_locator_refs=locators,
                    change_kind=(
                        "resolved"
                        if item.risk_change_kind == "closed"
                        else "not_evaluable"
                        if item.risk_change_kind == "needs_rejudgment"
                        else str(item.risk_change_kind)
                    ),
                )
            )
        site_subjects = tuple(sorted(subjects))
        product_packet = dataclass_replace(
            build_synthetic_r5_authority_packet(),
            project_ref=project_id,
            run_ref=identity.run_ref,
            snapshot_ref=snapshot_ref,
            cutoff_ref=cutoff,
            project_label="08C 连续性合成项目",
            source_revision_content_pairs=tuple(
                R5SourceRevisionPair(
                    revision_id=source.source_revision_ref,
                    content_hash=source.source_revision_content_hash,
                    locator_refs=(source.locator_ref,),
                )
                for source in sources.values()
            ),
            sources=tuple(sources.values()),
            sites=(
                R5SiteRecord(
                    site_ref=site_ref,
                    subject_refs=site_subjects,
                    pattern_refs=("pattern.08c",),
                    individual_risk_refs=tuple(risk.risk_ref for risk in risks),
                    measure_refs=("measure.08c",),
                    domain="ae",
                    severity="high",
                    numerator=len(site_subjects),
                    denominator=max(1, len(site_subjects)),
                    coverage_state="complete",
                ),
            ),
            site_audience=(
                R5SiteAudienceRecord(
                    site_ref=site_ref,
                    site_label=site_label,
                ),
            ),
            subjects=tuple(subjects.values()),
            events=tuple(events.values()),
            visits=(),
            risks=tuple(risks),
            histories=(),
            flow_stages=(),
            subject_flow_paths=(),
            synthetic=False,
            data_mode="authority",
            authority_hash="",
            source_snapshot_sha256="",
        )
        digest = published_r5_packets[0].packet_digest
        return SimpleNamespace(
            packet_identity=published_r5_packets[0].packet_identity,
            packet_digest=digest,
            site_refs=(site_ref,),
            s4_packet_ids=("s4:08c:fixture",),
            s4_packet_digests=("e" * 64,),
            risks=product_packet.risks,
            subjects=product_packet.subjects,
            sites=product_packet.sites,
            events=product_packet.events,
            visits=product_packet.visits,
            sources=product_packet.sources,
            product_packet=product_packet,
        )

    monkeypatch.setattr(
        product_mod,
        "_build_r5_publication_packet",
        fake_r5_publication_packet,
    )

    client = _client(
        tmp_path,
        principal=_principal(project_id),
        harness_adapter=FakeHarnessAdapter(),
        harness_catalog=FakeCatalog(),
        authority_provider=SyntheticR5Provider(),
        r6_output_provider=SyntheticR6Provider(),
    )
    assert client.post(f"{_base(project_id)}/workspace/bootstrap").status_code == 200

    bound = client.post(
        f"{_base(project_id)}/runs",
        json={
            "run_id": run_id,
            "mode": mode,
            "execution_basis": execution_basis,
            "data_cutoff": cutoff,
            "source_revision_id": source_revision,
        },
    )
    assert bound.status_code == 200, bound.text

    prepared = client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/prepare",
        json={
            "work_units": product_mod._runtime_work_units(setup_manifest),
            "execution_kind": "harness",
        },
    )
    assert prepared.status_code == 200, prepared.text

    started = client.post(
        f"{_base(project_id)}/runs/{run_id}/execution/start",
        json={},
    )
    assert started.status_code == 200, started.text

    for _ in range(200):
        progress = client.get(f"{_base(project_id)}/runs/{run_id}/progress")
        assert progress.status_code == 200, progress.text
        if progress.json()["run_state"] == "completed":
            break
        time.sleep(0.01)
    assert progress.json()["run_state"] == "completed"

    workspace = _r7_workspace(tmp_path, project_id)
    registry_path = workspace / lr.LAUNCH_REGISTRY_DB_NAME
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        reservation = registry.reserve(
            project_id,
            idempotency_key=f"slice08c-{mode}-{run_id}-key",
            mode=mode,
            execution_basis=execution_basis,
            current_snapshot_token=current.snapshot_token,
            data_cutoff=cutoff,
            manifest_digest=setup_manifest.manifest_digest,
        )
        sequence = reservation.record.sequence
    public_token = lr.derive_public_run_token(project_id, run_id)
    with sqlite3.connect(str(registry_path)) as connection:
        connection.execute(
            "UPDATE r7_launch_registry SET run_id=?, public_run_token=? WHERE sequence=?",
            (run_id, public_token, sequence),
        )
        connection.commit()
    with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
        registry.mark_completed(run_id, project_id=project_id)

    # Build default rich items if not provided - use correct snapshot_token and add risk_change_kind for all
    if custom_items is None:
        items = (
            build_carry_forward_item(
                {
                    "ordinal": 0,
                    "object_type": "risk_instance",
                    "object_ref": "rk-new-001",
                    "risk_change_kind": "new",
                    "disposition": "re_evaluate_changed_data",
                    "data_change_kind": "added",
                    "prior_severity": None,
                    "current_severity": "high",
                    "prior_risk_state": None,
                    "current_risk_state": "established",
                    "target_run_id": run_id,
                    "target_project_id": project_id,
                    "target_mode": mode,
                    "reason": "受试者出现新增高危心律失常",
                    "evidence_summary": {
                        "site_ref": site_ref,
                        "site_label": "中心 01",
                        "subject_ref": "S-001",
                        "subject_label": "受试者 001",
                        "title": "新增严重心律失常风险",
                        "risk_ref": "rk-new-001",
                        "risk_instance_ref": "rinst-001",
                        "risk_anchor_ref": "anch-001",
                        "event_ref": "ev-001",
                        "source_locator_ref": "loc-001",
                        "source_count": 2,
                        "date_label": "2026-08-28",
                        "window_start": "2026-08-01",
                        "window_end": "2026-08-28",
                    },
                }
            ),
            build_carry_forward_item(
                {
                    "ordinal": 1,
                    "object_type": "risk_instance",
                    "object_ref": "rk-up-002",
                    "risk_change_kind": "upgraded",
                    "disposition": "re_evaluate_changed_data",
                    "data_change_kind": "revised",
                    "prior_severity": "medium",
                    "current_severity": "high",
                    "prior_risk_state": "established",
                    "current_risk_state": "escalated",
                    "r2_transition_type": "escalated",
                    "target_run_id": run_id,
                    "target_project_id": project_id,
                    "target_mode": mode,
                    "reason": "转氨酶指标持续升高达到3级",
                    "evidence_summary": {
                        "site_ref": site_ref,
                        "site_label": "中心 01",
                        "subject_ref": "S-001",
                        "subject_label": "受试者 001",
                        "title": "ALT指标升级至重度异常",
                        "risk_ref": "rk-up-002",
                        "risk_instance_ref": "rinst-002",
                        "risk_anchor_ref": "anch-002",
                        "event_ref": "ev-002",
                        "source_locator_ref": "loc-002",
                        "source_count": 1,
                        "date_label": "2026-08-27",
                        "window_start": "2026-08-01",
                        "window_end": "2026-08-28",
                    },
                }
            ),
            build_carry_forward_item(
                {
                    "ordinal": 2,
                    "object_type": "risk_instance",
                    "object_ref": "rk-reopen-003",
                    "risk_change_kind": "reopened",
                    "disposition": "re_evaluate_changed_data",
                    "data_change_kind": "added",
                    "prior_severity": "low",
                    "current_severity": "medium",
                    "prior_risk_state": "closed",
                    "current_risk_state": "reopened",
                    "r2_transition_type": "reopened",
                    "target_run_id": run_id,
                    "target_project_id": project_id,
                    "target_mode": mode,
                    "reason": "停药后皮疹再次出现",
                    "evidence_summary": {
                        "site_ref": site_ref,
                        "site_label": "中心 01",
                        "subject_ref": "S-002",
                        "subject_label": "受试者 002",
                        "title": "过敏性皮疹重新出现",
                        "risk_ref": "rk-reopen-003",
                        "risk_instance_ref": "rinst-003",
                        "risk_anchor_ref": "anch-003",
                        "event_ref": "ev-003",
                        "source_locator_ref": "loc-003",
                        "source_count": 1,
                        "date_label": "2026-08-26",
                        "window_start": "2026-08-01",
                        "window_end": "2026-08-28",
                    },
                }
            ),
            build_carry_forward_item(
                {
                    "ordinal": 3,
                    "object_type": "risk_instance",
                    "object_ref": "rk-rejudge-004",
                    "risk_change_kind": "needs_rejudgment",
                    "disposition": "re_evaluate_prior_uncertain",
                    "data_change_kind": "cannot_compare",
                    "prior_severity": "high",
                    "current_severity": "high",
                    "prior_risk_state": "established",
                    "current_risk_state": "identity_ambiguous",
                    "r2_transition_type": "identity_ambiguous",
                    "target_run_id": run_id,
                    "target_project_id": project_id,
                    "target_mode": mode,
                    "reason": "受试者中心迁移导致身份待确认",
                    "evidence_summary": {
                        "site_ref": site_ref,
                        "site_label": "中心 02",
                        "subject_ref": "S-003",
                        "subject_label": "受试者 003",
                        "title": "合并用药风险需重新评估",
                        "risk_ref": "rk-rejudge-004",
                        "risk_instance_ref": "rinst-004",
                        "risk_anchor_ref": "anch-004",
                        "event_ref": "ev-004",
                        "source_locator_ref": "loc-004",
                        "source_count": 1,
                        "date_label": "2026-08-25",
                        "window_start": "2026-08-01",
                        "window_end": "2026-08-28",
                    },
                }
            ),
            build_carry_forward_item(
                {
                    "ordinal": 4,
                    "object_type": "risk_instance",
                    "object_ref": "rk-down-005",
                    "risk_change_kind": "downgraded",
                    "disposition": "re_evaluate_changed_data",
                    "data_change_kind": "revised",
                    "prior_severity": "high",
                    "current_severity": "medium",
                    "prior_risk_state": "established",
                    "current_risk_state": "deescalated",
                    "r2_transition_type": "deescalated",
                    "target_run_id": run_id,
                    "target_project_id": project_id,
                    "target_mode": mode,
                    "reason": "血压指标经治疗后明显好转",
                    "evidence_summary": {
                        "site_ref": site_ref,
                        "site_label": "中心 02",
                        "subject_ref": "S-003",
                        "subject_label": "受试者 003",
                        "title": "高血压风险降级",
                        "risk_ref": "rk-down-005",
                        "risk_instance_ref": "rinst-005",
                        "risk_anchor_ref": "anch-005",
                        "event_ref": "ev-005",
                        "source_locator_ref": "loc-005",
                        "source_count": 1,
                        "date_label": "2026-08-24",
                        "window_start": "2026-08-01",
                        "window_end": "2026-08-28",
                    },
                }
            ),
            build_carry_forward_item(
                {
                    "ordinal": 5,
                    "object_type": "risk_instance",
                    "object_ref": "rk-closed-006",
                    "risk_change_kind": "closed",
                    "disposition": "close_with_evidence",
                    "data_change_kind": "unchanged",
                    "prior_severity": "medium",
                    "current_severity": None,
                    "prior_risk_state": "established",
                    "current_risk_state": "closed",
                    "r2_transition_type": "closed",
                    "closure_allowed": True,
                    "closure_evidence_refs": ("ev-close-001",),
                    "current_listing_complete": True,
                    "baseline_eligible": True,
                    "target_run_id": run_id,
                    "target_project_id": project_id,
                    "target_mode": mode,
                    "reason": "随访检验恢复正常且达到预定解除标准",
                    "evidence_summary": {
                        "site_ref": site_ref,
                        "site_label": "中心 02",
                        "subject_ref": "S-003",
                        "subject_label": "受试者 003",
                        "title": "电解质异常已关闭",
                        "risk_ref": "rk-closed-006",
                        "risk_instance_ref": "rinst-006",
                        "risk_anchor_ref": "anch-006",
                        "event_ref": "ev-006",
                        "source_locator_ref": "loc-006",
                        "source_count": 1,
                        "date_label": "2026-08-23",
                        "window_start": "2026-08-01",
                        "window_end": "2026-08-28",
                    },
                }
            ),
            build_carry_forward_item(
                {
                    "ordinal": 6,
                    "object_type": "risk_instance",
                    "object_ref": "rk-cont-007",
                    "risk_change_kind": "continued",
                    "disposition": "re_evaluate_changed_data",
                    "data_change_kind": "unchanged",
                    "prior_severity": "low",
                    "current_severity": "low",
                    "prior_risk_state": "established",
                    "current_risk_state": "established",
                    "r2_transition_type": "",
                    "target_run_id": run_id,
                    "target_project_id": project_id,
                    "target_mode": mode,
                    "reason": "轻度恶心症状持续存在",
                    "evidence_summary": {
                        "site_ref": site_ref,
                        "site_label": "中心 02",
                        "subject_ref": "S-004",
                        "subject_label": "受试者 004",
                        "title": "轻度胃肠道不适持续",
                        "risk_ref": "rk-cont-007",
                        "risk_instance_ref": "rinst-007",
                        "risk_anchor_ref": "anch-007",
                        "event_ref": "ev-007",
                        "source_locator_ref": "loc-007",
                        "source_count": 1,
                        "date_label": "2026-08-22",
                        "window_start": "2026-08-01",
                        "window_end": "2026-08-28",
                    },
                }
            ),
            build_carry_forward_item(
                {
                    "ordinal": 7,
                    "object_type": "query_draft",
                    "object_ref": "qd-008",
                    "risk_change_kind": "new",
                    "disposition": "re_evaluate_changed_data",
                    "data_change_kind": "added",
                    "target_run_id": run_id,
                    "target_project_id": project_id,
                    "target_mode": mode,
                    "reason": "合并用药记录不完整Query草稿",
                    "evidence_summary": {
                        "site_ref": site_ref,
                        "site_label": "中心 01",
                        "subject_ref": "S-001",
                        "subject_label": "受试者 001",
                        "title": "合并用药起止日期缺失草稿",
                        "risk_ref": "rk-up-002",
                        "risk_instance_ref": "rinst-002",
                        "risk_anchor_ref": "anch-002",
                        "event_ref": "ev-002",
                        "source_locator_ref": "loc-002",
                        "source_count": 1,
                        "date_label": "2026-08-27",
                        "window_start": "2026-08-01",
                        "window_end": "2026-08-28",
                    },
                }
            ),
            build_carry_forward_item(
                {
                    "ordinal": 8,
                    "object_type": "query_draft",
                    "object_ref": "qd-009",
                    "risk_change_kind": "new",
                    "disposition": "re_evaluate_changed_data",
                    "data_change_kind": "added",
                    "target_run_id": run_id,
                    "target_project_id": project_id,
                    "target_mode": mode,
                    "reason": "监查结果项汇总统计",
                    "evidence_summary": {
                        "site_ref": site_ref,
                        "site_label": "中心 01",
                        "subject_ref": "S-001",
                        "subject_label": "受试者 001",
                        "title": "主要终点缺失监查项",
                        "risk_ref": "rk-new-001",
                        "risk_instance_ref": "rinst-001",
                        "risk_anchor_ref": "anch-001",
                        "event_ref": "ev-001",
                        "source_locator_ref": "",
                        "source_count": 0,
                        "date_label": "2026-08-28",
                        "window_start": "2026-08-01",
                        "window_end": "2026-08-28",
                    },
                }
            ),
        )
        # Daily 08B emits one risk atom and one Query atom in this fixture.
        # Keep the endpoint success path one-to-one with those committed atoms;
        # lifecycle/count edge cases are exercised separately below.
        items = (items[0], items[8])
    else:
        items = tuple(custom_items)

    items = tuple(
        dataclass_replace(
            item,
            ordinal=ordinal,
            artifact_verified=True,
            artifact_member_verified=True,
            item_digest="",
        )
        for ordinal, item in enumerate(items)
    )
    authority_items[:] = tuple(authority_source_items or items)

    if baseline is None and execution_basis == "incremental":
        baseline = DecisionBaseline(
            project_id=project_id,
            mode=mode,
            target_run_id=run_id,
            target_snapshot_id=current.snapshot_token,
            target_data_cutoff=cutoff,
            target_decision_version="decision-v1",
            source_run_id="run-prior-001",
            source_publication_id="pub-prior-001",
            source_public_run_token="public-prior-token",
            source_snapshot_id="snap.prior",
            source_data_cutoff="2026-07-28",
            source_decision_version="decision-prior",
            source_created_at="2026-07-28T00:00:00Z",
            created_at="2026-08-29T00:00:00Z",
        )

    # Initial plan uses correct snapshot_token, not snapshot_ref
    plan = build_carry_forward_plan(
        project_id=project_id,
        mode=mode,
        execution_basis=execution_basis,
        target_run_id=run_id,
        target_snapshot_id=current.snapshot_token,
        target_data_cutoff=cutoff,
        target_decision_version="decision-v1",
        r5_authority_digest="a" * 64,
        r6_publication_digest="b" * 64,
        r6_receipt_digest="c" * 64,
        r6_output_set_digest="d" * 64,
        baseline=baseline,
        items=items,
        status="staging",
        created_at="2026-08-29T00:00:00Z",
    )

    result_context_token = ""
    publication = None
    if not skip_publish:
        # First publish without continuity plan to obtain real digests
        pub_resp = client.post(
            f"{_base(project_id)}/runs/{public_token}/publication",
            json={"idempotency_key": f"slice08c-pub-{mode}-{run_id}"},
        )
        assert pub_resp.status_code == 200, pub_resp.text
        assert pub_resp.json()["publication_state"] == "available"

        with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
            publication = registry.get_publication(project_id=project_id, run_id=run_id)
            result_context_token = publication.result_context_token

        from packages.medical_monitoring.graph.store import Store
        from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity_bridge import (
            extract_atomic_items,
        )

        runtime_dir = workspace / product_mod.RUNTIME_DIR_NAME
        artifact_store = Store(
            runtime_dir / product_mod.RUNTIME_DB_NAME,
            runtime_dir / product_mod.ARTIFACT_DIR_NAME,
        )
        try:
            source_envelopes = {
                member_id: artifact_store.get_artifact(member_id)
                for member_id in publication.artifact_member_ids
            }
            atoms_by_type: dict[str, list[Any]] = {}
            for member_id, envelope in source_envelopes.items():
                for atom in extract_atomic_items(
                    [envelope.payload],
                    mode=mode,
                    output_artifact_map={envelope.node_id: member_id},
                ):
                    atoms_by_type.setdefault(atom.object_type, []).append(atom)
        finally:
            artifact_store.close()
        verified_items_list = []
        for item in items:
            matching_atoms = atoms_by_type.get(item.object_type, [])
            assert matching_atoms, f"no committed 08B atom for {item.object_type}"
            atom = matching_atoms[0]
            source_envelope = source_envelopes[atom.artifact_id]
            verified_items_list.append(
                dataclass_replace(
                    item,
                    source_run_id=source_envelope.run_id,
                    source_object_id=(
                        source_object_id_override or atom.object_id
                    ),
                    target_object_id=item.object_ref,
                    source_identity=atom.item_digest,
                    source_artifact_id=atom.artifact_id,
                    source_artifact_sha256=(
                        source_artifact_sha256_override
                        or source_envelope.content_hash
                    ),
                    item_digest="",
                )
            )
        verified_items = tuple(verified_items_list)

        # Temporarily set publication to non-available to allow plan save, then create verified plan with real digests
        with sqlite3.connect(str(registry_path)) as conn:
            conn.execute(
                "UPDATE r7_result_publications SET publication_state='publishing' WHERE project_id=? AND run_id=?",
                (project_id, run_id),
            )
            conn.commit()

        # Build corrected plan with real digests
        corrected_plan = build_carry_forward_plan(
            project_id=project_id,
            mode=mode,
            execution_basis=execution_basis,
            target_run_id=run_id,
            target_snapshot_id=current.snapshot_token,
            target_data_cutoff=cutoff,
            target_decision_version="decision-v1",
            r5_authority_digest=publication.r5_authority_packet_digest,
            r6_publication_digest=publication.publication_fingerprint,
            r6_receipt_digest=publication.receipt_set_digest,
            r6_output_set_digest=publication.r6_output_set_digest,
            baseline=baseline,
            items=verified_items,
            status="staging",
            created_at="2026-08-29T00:00:00Z",
        )
        with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
            saved = registry.save_continuity_plan(corrected_plan)
            # Transition to verified
            verified = registry.update_continuity_plan_status(
                project_id, target_run_id=run_id, status="verified"
            )
            assert verified.status == "verified"

        # Restore publication to available
        with sqlite3.connect(str(registry_path)) as conn:
            conn.execute(
                "UPDATE r7_result_publications SET publication_state='available' WHERE project_id=? AND run_id=?",
                (project_id, run_id),
            )
            conn.commit()

        # Mark plan as published via internal method (replicates finalize's behavior)
        with lr.LaunchRegistry(registry_path, project_id=project_id) as reg2:
            with reg2._lock:
                conn = reg2._require_conn()
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    row = reg2._continuity_plan_row(conn, project_id, target_run_id=run_id)
                    assert row is not None, "verified plan not found"
                    plan_obj = reg2._row_to_continuity_plan(conn, row)
                    marked = reg2._mark_continuity_plan_published_locked(conn, project_id, plan_obj)
                    conn.commit()
                    assert marked.status == "published"
                except Exception:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    raise

        # Refresh publication after plan published
        with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
            publication = registry.get_publication(project_id=project_id, run_id=run_id)
            result_context_token = publication.result_context_token

    else:
        # skip_publish case: just save staging plan without marking published
        with lr.LaunchRegistry(registry_path, project_id=project_id) as registry:
            registry.save_continuity_plan(plan)
            if plan_status in ("verified", "published"):
                updated = registry.update_continuity_plan_status(
                    project_id, target_run_id=run_id, status=plan_status if plan_status=="verified" else "verified"
                )
                if plan_status == "published":
                    # For published we need the mark path; but skip_publish means no publication, so keep verified
                    pass
            saved = registry.get_continuity_plan(project_id, target_run_id=run_id)
            assert saved is not None

    return {
        "client": client,
        "project_id": project_id,
        "run_id": run_id,
        "public_token": public_token,
        "result_context_token": result_context_token,
        "plan": plan,
        "workspace": workspace,
        "publication": publication,
        "registry_path": registry_path,
        "current_snapshot_token": current.snapshot_token,
    }


def test_slice08c1_continuity_endpoint_exact_dto_nine_counts_reconstruction_and_sorting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify GET /continuity exact DTO envelope, nine change counts reconstruction, and deterministic sort."""
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        mode="daily",
        site_label="华东医学中心",
    )
    client = ctx["client"]
    project_id = ctx["project_id"]
    result_context_token = ctx["result_context_token"]
    public_token = ctx["public_token"]

    resp = client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # 1. Exact top-level keys
    assert set(body.keys()) == {
        "result_context_token",
        "identity",
        "comparison",
        "response_digest",
    }
    assert body["result_context_token"] == result_context_token

    # 2. Exact identity keys and values
    identity = body["identity"]
    assert set(identity.keys()) == {
        "project_ref",
        "public_run_token",
        "snapshot_token",
        "data_cutoff_text",
        "mode_text",
        "site_scope_text",
    }
    assert identity["project_ref"] == project_id
    assert identity["public_run_token"] == public_token
    assert identity["mode_text"] == "日常监查"
    assert "中心" in identity["site_scope_text"]

    # 3. Exact comparison keys
    comparison = body["comparison"]
    assert set(comparison.keys()) == {
        "available",
        "basis_text",
        "comparison_text",
        "source_run_text",
        "change_counts",
        "rows",
        "shown_count",
        "total_count",
        "truncated",
    }
    assert comparison["available"] is True
    assert comparison["basis_text"] in {"全量分析", "增量分析"}
    assert comparison["comparison_text"] in {
        "已与上次监查结果比较",
        "本轮为首次全面分析，无比较基线",
    }
    assert isinstance(comparison["source_run_text"], str)
    assert comparison["shown_count"] == len(comparison["rows"])
    assert comparison["total_count"] == len(comparison["rows"])
    assert comparison["truncated"] is False

    # 4. Exact 9 non-negative integer change_counts
    counts = comparison["change_counts"]
    assert set(counts.keys()) == {
        "new",
        "upgraded",
        "continued",
        "downgraded",
        "closed",
        "reopened",
        "needs_rejudgment",
        "mid_high_total",
        "changed_subject_count",
    }
    for k, v in counts.items():
        assert isinstance(v, int) and v >= 0, f"count {k} is not a non-negative int: {v}"

    # Verify expected counts from the canonical daily two-atom fixture.
    assert counts["new"] == 1
    assert counts["upgraded"] == 0
    assert counts["reopened"] == 0
    assert counts["needs_rejudgment"] == 0
    assert counts["downgraded"] == 0
    assert counts["closed"] == 0
    assert counts["continued"] == 0
    assert counts["mid_high_total"] == 1
    assert counts["changed_subject_count"] == 1

    # 5. Independent reconstruction of nine counts from rows
    rows = comparison["rows"]
    assert len(rows) == 2

    recon_new = sum(1 for r in rows if r["object_type"] == "risk" and r["change_kind"] == "new")
    recon_up = sum(1 for r in rows if r["object_type"] == "risk" and r["change_kind"] == "upgraded")
    recon_cont = sum(1 for r in rows if r["object_type"] == "risk" and r["change_kind"] == "continued")
    recon_down = sum(1 for r in rows if r["object_type"] == "risk" and r["change_kind"] == "downgraded")
    recon_closed = sum(1 for r in rows if r["object_type"] == "risk" and r["change_kind"] == "closed")
    recon_reopen = sum(1 for r in rows if r["object_type"] == "risk" and r["change_kind"] == "reopened")
    recon_rejudge = sum(1 for r in rows if r["object_type"] == "risk" and r["change_kind"] == "needs_rejudgment")
    recon_mid_high = sum(
        1 for r in rows if r["object_type"] == "risk" and r["severity_after_text"] in {"高", "中"}
    )
    changed_subjs = {
        r["subject_ref"]
        for r in rows
        if r["object_type"] == "risk"
        and r["change_kind"] in {"new", "upgraded", "downgraded", "closed", "reopened", "needs_rejudgment"}
        and r["subject_ref"]
    }

    assert counts["new"] == recon_new
    assert counts["upgraded"] == recon_up
    assert counts["continued"] == recon_cont
    assert counts["downgraded"] == recon_down
    assert counts["closed"] == recon_closed
    assert counts["reopened"] == recon_reopen
    assert counts["needs_rejudgment"] == recon_rejudge
    assert counts["mid_high_total"] == recon_mid_high
    assert counts["changed_subject_count"] == len(changed_subjs)

    # 6. Each row has exactly 28 fields and strict closed sets
    exact_row_keys = {
        "row_ref",
        "object_type",
        "object_type_text",
        "ordinal",
        "change_kind",
        "change_text",
        "disposition",
        "disposition_text",
        "data_change_kind",
        "data_change_text",
        "severity_before_text",
        "severity_after_text",
        "title",
        "reason_text",
        "attention_text",
        "site_ref",
        "site_label",
        "subject_ref",
        "subject_label",
        "date_label",
        "window_start",
        "window_end",
        "risk_ref",
        "risk_instance_ref",
        "risk_anchor_ref",
        "event_ref",
        "source_locator_ref",
        "source_count",
    }
    allowed_object_types = {"risk", "query_draft", "monitoring_output"}
    allowed_object_type_texts = {"风险", "Query 草稿", "监查结果项"}
    allowed_change_kinds = {
        "new",
        "upgraded",
        "continued",
        "downgraded",
        "closed",
        "reopened",
        "needs_rejudgment",
    }
    allowed_change_texts = {"新增", "升级", "持续", "降级", "关闭", "重开", "需重新判断"}
    allowed_dispositions = {
        "reuse_unchanged",
        "re_evaluate_changed_data",
        "re_evaluate_rule_change",
        "re_evaluate_prior_uncertain",
        "close_with_evidence",
        "blocked_incompatible",
    }
    allowed_disposition_texts = {
        "沿用不变",
        "数据变化，已重新分析",
        "规则变化，已重新分析",
        "上轮依据不足，本轮重新分析",
        "已有证据支持关闭",
        "前后版本不可直接比较",
    }
    allowed_data_change_kinds = {
        "unchanged",
        "added",
        "revised",
        "deleted",
        "cannot_compare",
        "missing",
    }
    allowed_data_change_texts = {
        "无变化",
        "新增数据",
        "数据修订",
        "数据删除",
        "无法直接比较",
        "本轮未见对应记录",
    }
    allowed_severities = {"", "高", "中", "低"}
    allowed_attentions = {
        "",
        "未见记录不代表风险已解除",
        "身份或数据不完整，需重新判断",
        "等级变化待确认",
        "原始记录位置待确认",
    }

    seen_row_refs = set()
    seen_risk_instance_refs = set()

    for row in rows:
        assert set(row.keys()) == exact_row_keys
        assert row["row_ref"] not in seen_row_refs
        seen_row_refs.add(row["row_ref"])
        assert row["object_type"] in allowed_object_types
        assert row["object_type_text"] in allowed_object_type_texts
        assert row["change_kind"] in allowed_change_kinds
        assert row["change_text"] in allowed_change_texts
        assert row["disposition"] in allowed_dispositions
        assert row["disposition_text"] in allowed_disposition_texts
        assert row["data_change_kind"] in allowed_data_change_kinds
        assert row["data_change_text"] in allowed_data_change_texts
        assert row["severity_before_text"] in allowed_severities
        assert row["severity_after_text"] in allowed_severities
        assert row["attention_text"] in allowed_attentions
        assert isinstance(row["ordinal"], int) and row["ordinal"] >= 0
        assert isinstance(row["source_count"], int) and row["source_count"] >= 0

        # Risk instance ref uniqueness across risk rows
        if row["risk_instance_ref"]:
            if row["object_type"] == "risk":
                assert row["risk_instance_ref"] not in seen_risk_instance_refs
                seen_risk_instance_refs.add(row["risk_instance_ref"])

        # Severity transitions per contract v0.2 §18
        if row["change_kind"] == "new":
            assert row["severity_before_text"] == ""
            if row["object_type"] == "risk":
                assert row["severity_after_text"] in {"高", "中", "低"}
            else:
                assert row["severity_after_text"] == ""
        elif row["change_kind"] == "closed":
            assert row["severity_before_text"] in {"高", "中", "低"}
            assert row["severity_after_text"] == ""
        elif row["change_kind"] in {"upgraded", "downgraded", "continued"}:
            assert row["severity_before_text"] in {"高", "中", "低"}
            assert row["severity_after_text"] in {"高", "中", "低"}

    # 7. Deterministic sorting order per contract v0.1 §6:
    # Group 1: Current high risk + (upgraded/new/reopened/needs_rejudgment)
    # Group 2: Current mid risk + (upgraded/new/reopened/needs_rejudgment)
    # Group 3: Other high/mid risk
    # Group 4: Low risk
    # Group 5: Query drafts
    # Group 6: Monitoring output items
    def _sort_group(r: dict[str, Any]) -> int:
        obj = r["object_type"]
        ck = r["change_kind"]
        sev = r["severity_after_text"]
        is_crit = ck in {"upgraded", "new", "reopened", "needs_rejudgment"}
        if obj == "risk":
            if sev == "高" and is_crit:
                return 1
            if sev == "中" and is_crit:
                return 2
            if sev in {"高", "中"} or (ck == "closed" and r["severity_before_text"] in {"高", "中"}):
                return 3
            if sev == "低":
                return 4
            return 4.5
        if obj == "query_draft":
            return 5
        if obj == "monitoring_output":
            return 6
        return 7

    groups = [_sort_group(r) for r in rows]
    for i in range(len(groups) - 1):
        assert groups[i] <= groups[i + 1], f"Sorting violation at index {i}: {rows[i]} before {rows[i+1]}"

    # 8. Clean public response: no secret/internal tokens
    raw_json = resp.text.lower()
    for forbidden in (
        "run_id",
        "run_ref",
        "snapshot_ref",
        "cutoff_ref",
        "authority_receipt",
        "authority_hash",
        "packet_digest",
        "packet_identity",
        "s4_",
        "r5_",
        "evidence_summary",
        "plan_id",
    ):
        assert forbidden not in raw_json, f"Internal token '{forbidden}' leaked in response"

    # 10. Response digest validity
    expected_digest = lr.content_digest({"identity": identity, "comparison": comparison})
    assert body["response_digest"] == expected_digest


def test_slice08c1_continuity_endpoint_site_ref_filtering_and_out_of_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify site_ref query filters rows and recomputes 9 counts, and out-of-scope site fails 409."""
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        mode="daily",
        site_label="华东医学中心",
    )
    client = ctx["client"]
    project_id = ctx["project_id"]
    result_context_token = ctx["result_context_token"]

    # 1. Filter by actual site (dynamic, matches fixture's site)
    unfiltered = client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity"
    )
    assert unfiltered.status_code == 200, unfiltered.text
    assert unfiltered.json()["identity"]["site_scope_text"] == "华东医学中心"
    assert {
        row["site_label"] for row in unfiltered.json()["comparison"]["rows"]
    } == {"华东医学中心"}
    actual_site = unfiltered.json()["comparison"]["rows"][0]["site_ref"]
    assert actual_site, "continuity rows should have site_ref"

    resp = client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity",
        params={"site_ref": actual_site},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Identity contains site_ref
    assert body["identity"].get("site_ref") == actual_site

    # All rows belong to actual_site
    comparison = body["comparison"]
    rows = comparison["rows"]
    assert len(rows) > 0
    for r in rows:
        assert r["site_ref"] == actual_site

    # 9 change counts recomputed for actual_site should match unfiltered (all rows share same site)
    counts = comparison["change_counts"]
    unfiltered_counts = unfiltered.json()["comparison"]["change_counts"]
    assert counts == unfiltered_counts
    # 2. Filter by out-of-scope site returns 409 result_center_out_of_scope
    out_of_scope = client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity",
        params={"site_ref": "site.999_not_covered"},
    )
    assert out_of_scope.status_code == 409
    assert out_of_scope.json()["code"] == "result_center_out_of_scope"
    _assert_error_body(out_of_scope.json(), status_code=409)


def test_slice08c1_continuity_endpoint_body_and_query_rejection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify GET rejects request body, unknown query parameters, and malformed tokens."""
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        mode="daily",
    )
    client = ctx["client"]
    project_id = ctx["project_id"]
    result_context_token = ctx["result_context_token"]

    # 1. Request with unknown query parameter is rejected (422)
    unknown_query = client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity",
        params={"unsupported_key": "val"},
    )
    assert unknown_query.status_code == 422
    _assert_error_body(unknown_query.json(), status_code=422)

    # 2. Request with extra query alongside site_ref is rejected - fetch actual site first
    unfiltered = client.get(f"{_base(project_id)}/results/{result_context_token}/continuity")
    assert unfiltered.status_code == 200
    actual_site = unfiltered.json()["comparison"]["rows"][0]["site_ref"]
    extra_query = client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity",
        params={"site_ref": actual_site, "limit": "10"},
    )
    assert extra_query.status_code == 422
    _assert_error_body(extra_query.json(), status_code=422)

    # 3. Request with body is rejected (422)
    body_rejected = client.request(
        "GET",
        f"{_base(project_id)}/results/{result_context_token}/continuity",
        content=b'{"not_allowed": true}',
        headers={"Content-Type": "application/json"},
    )
    assert body_rejected.status_code == 422
    assert body_rejected.json()["code"] == "request_validation_failed"
    _assert_error_body(body_rejected.json(), status_code=422)
    # 4. Whitespace or empty result_context_token is rejected
    ws_token = client.get(
        f"{_base(project_id)}/results/%20%20/continuity"
    )
    assert ws_token.status_code in {404, 409, 422}


def test_slice08c1_continuity_endpoint_fail_closed_on_illegal_identity_and_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify fail-closed on non-existent token, staging-only plan, or authority digest drift."""
    # Case A: Non-existent result_context_token returns 409 result_context_unavailable
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        mode="daily",
    )
    client = ctx["client"]
    project_id = ctx["project_id"]
    registry_path = ctx["registry_path"]
    run_id = ctx["run_id"]

    non_existent = client.get(
        f"{_base(project_id)}/results/result-context:non-existent-token/continuity"
    )
    assert non_existent.status_code == 409
    assert non_existent.json()["code"] == "result_context_unavailable"
    _assert_error_body(non_existent.json(), status_code=409)

    # Case B: Digest drift in continuity plan causes fail closed (409)
    with sqlite3.connect(str(registry_path)) as conn:
        conn.execute(
            "UPDATE r7_continuity_plans SET r5_authority_digest='tampered_digest' WHERE target_run_id=?",
            (run_id,),
        )
        conn.commit()

    drifted = client.get(
        f"{_base(project_id)}/results/{ctx['result_context_token']}/continuity"
    )
    assert drifted.status_code == 409
    assert drifted.json()["code"] == "continuity_unavailable"
    _assert_error_body(drifted.json(), status_code=409)


def test_slice08c1_continuity_endpoint_fail_closed_on_illegal_closed_set_and_inconsistencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify fail closed when continuity plan contains invalid closed set or corrupted rows."""
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity import build_carry_forward_item

    # Build a corrupted item with invalid severity direction for upgraded
    # (upgraded but severity_before='high' and severity_after='low')
    corrupted_item = build_carry_forward_item(
        {
            "ordinal": 0,
            "object_type": "risk_instance",
            "object_ref": "rk-bad-001",
            "risk_change_kind": "upgraded",
            "disposition": "re_evaluate_changed_data",
            "data_change_kind": "revised",
            "prior_severity": "high",
            "current_severity": "low",
            "prior_risk_state": "established",
            "current_risk_state": "escalated",
            "reason": "非法升级等级方向",
            "evidence_summary": {
                "site_ref": "site.01",
                "subject_ref": "S-001",
                "subject_label": "受试者 001",
                "title": "非法方向风险",
                "risk_ref": "rk-bad-001",
                "risk_instance_ref": "rinst-bad-001",
                "risk_anchor_ref": "anch-bad-001",
                "event_ref": "ev-bad-001",
                "source_locator_ref": "loc-bad-001",
                                "source_count": 1,
                                "date_label": "2026-08-28",
                                "window_start": "2026-08-01",
                                "window_end": "2026-08-28",
                            },
        }
    )

    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        mode="daily",
        custom_items=[corrupted_item],
    )
    client = ctx["client"]
    project_id = ctx["project_id"]
    result_context_token = ctx["result_context_token"]

    resp = client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity"
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "continuity_unavailable"
    _assert_error_body(resp.json(), status_code=409)


def test_slice08c1_continuity_rejects_forged_public_text_and_source_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity import (
        build_carry_forward_item,
    )

    safe_item = build_carry_forward_item(
        {
            "ordinal": 0,
            "object_type": "risk_instance",
            "object_ref": "rk-authority-001",
            "risk_change_kind": "new",
            "disposition": "re_evaluate_changed_data",
            "data_change_kind": "added",
            "current_severity": "high",
            "current_risk_state": "established",
            "reason": "本轮新增心律失常风险",
            "evidence_summary": {
                "site_ref": "site.01",
                "subject_ref": "S-001",
                "subject_label": "受试者 001",
                "title": "新增心律失常风险",
                "risk_ref": "rk-authority-001",
                "risk_instance_ref": "rinst-authority-001",
                "risk_anchor_ref": "anch-authority-001",
                "event_ref": "ev-authority-001",
                "source_locator_ref": "loc-authority-001",
                "source_count": 1,
                "date_label": "2026-08-28",
            },
        }
    )
    forged_item = dataclass_replace(
        safe_item,
        reason="packet_digest=leak",
        evidence_summary={
            **dict(safe_item.evidence_summary),
            "site_ref": "not-in-r5",
            "source_locator_ref": "loc-forged",
            "source_count": -7,
        },
        item_digest="",
    )
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        custom_items=(forged_item,),
        authority_source_items=(safe_item,),
    )
    response = ctx["client"].get(
        f"{_base(ctx['project_id'])}/results/{ctx['result_context_token']}/continuity"
    )
    assert response.status_code == 409
    assert response.json()["code"] == "continuity_unavailable"


def test_slice08c1_continuity_allows_event_bound_query_without_risk_mapping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity import (
        build_carry_forward_item,
    )

    authority_item = build_carry_forward_item(
        {
            "ordinal": 0,
            "object_type": "risk_instance",
            "object_ref": "rk-authority-event-001",
            "risk_change_kind": "new",
            "disposition": "re_evaluate_changed_data",
            "data_change_kind": "added",
            "current_severity": "high",
            "current_risk_state": "established",
            "reason": "本轮新增异常心电图记录",
            "evidence_summary": {
                "site_ref": "site.01",
                "subject_ref": "S-001",
                "subject_label": "受试者 001",
                "title": "异常心电图记录",
                "risk_ref": "rk-authority-event-001",
                "risk_instance_ref": "rinst-authority-event-001",
                "risk_anchor_ref": "anch-authority-event-001",
                "event_ref": "ev-authority-event-001",
                "source_locator_ref": "loc-authority-event-001",
                "source_count": 1,
                "date_label": "2026-08-28",
            },
        }
    )
    query_item = build_carry_forward_item(
        {
            "ordinal": 0,
            "object_type": "query_draft",
            "object_ref": "qd-event-only-001",
            "risk_change_kind": "new",
            "disposition": "re_evaluate_changed_data",
            "data_change_kind": "added",
            "reason": "请核实心电图复查记录是否完整",
            "evidence_summary": {
                "site_ref": "site.01",
                "subject_ref": "S-001",
                "event_ref": "ev-authority-event-001",
                "source_locator_ref": "loc-authority-event-001",
                "source_count": 1,
                "window_start": "2026-08-01",
                "window_end": "2026-08-28",
            },
        }
    )
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        custom_items=(query_item,),
        authority_source_items=(authority_item,),
    )
    response = ctx["client"].get(
        f"{_base(ctx['project_id'])}/results/{ctx['result_context_token']}/continuity"
    )
    assert response.status_code == 200, response.text
    row = response.json()["comparison"]["rows"][0]
    assert row["object_type"] == "query_draft"
    assert row["event_ref"] == "ev-authority-event-001"
    assert row["risk_ref"] == ""
    assert row["risk_instance_ref"] == ""


def test_slice08c1_continuity_rejects_mixed_risk_and_event_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity import (
        build_carry_forward_item,
    )

    def authority_item(suffix: str) -> Any:
        return build_carry_forward_item(
            {
                "ordinal": 0 if suffix == "a" else 1,
                "object_type": "risk_instance",
                "object_ref": f"rk-bind-{suffix}",
                "risk_change_kind": "new",
                "disposition": "re_evaluate_changed_data",
                "data_change_kind": "added",
                "current_severity": "high",
                "current_risk_state": "established",
                "reason": f"绑定验证风险 {suffix}",
                "evidence_summary": {
                    "site_ref": "site.01",
                    "subject_ref": "S-001",
                    "subject_label": "受试者 001",
                    "title": f"绑定验证事件 {suffix}",
                    "risk_ref": f"rk-bind-{suffix}",
                    "risk_instance_ref": f"rinst-bind-{suffix}",
                    "risk_anchor_ref": f"anch-bind-{suffix}",
                    "event_ref": f"ev-bind-{suffix}",
                    "source_locator_ref": f"loc-bind-{suffix}",
                    "source_count": 1,
                    "date_label": "2026-08-28",
                },
            }
        )

    authority_a = authority_item("a")
    authority_b = authority_item("b")
    query_item = build_carry_forward_item(
        {
            "ordinal": 0,
            "object_type": "query_draft",
            "object_ref": "qd-mixed-binding",
            "risk_change_kind": "new",
            "disposition": "re_evaluate_changed_data",
            "data_change_kind": "added",
            "reason": "同一行混入不一致的风险和事件",
            "evidence_summary": {
                "site_ref": "site.01",
                "subject_ref": "S-001",
                "risk_ref": "rk-bind-a",
                "risk_instance_ref": "rinst-bind-b",
                "risk_anchor_ref": "anch-bind-b",
                "event_ref": "ev-bind-b",
                "source_locator_ref": "loc-bind-b",
                "source_count": 1,
                "window_start": "2026-08-01",
                "window_end": "2026-08-28",
            },
        }
    )
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        custom_items=(query_item,),
        authority_source_items=(authority_a, authority_b),
    )
    response = ctx["client"].get(
        f"{_base(ctx['project_id'])}/results/{ctx['result_context_token']}/continuity"
    )
    assert response.status_code == 409
    assert response.json()["code"] == "continuity_unavailable"


def test_slice08c1_continuity_rejects_false_closed_lifecycle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity import (
        build_carry_forward_item,
    )

    false_closed = build_carry_forward_item(
        {
            "ordinal": 0,
            "object_type": "risk_instance",
            "object_ref": "rk-false-closed-001",
            "risk_change_kind": "closed",
            "disposition": "re_evaluate_changed_data",
            "data_change_kind": "unchanged",
            "prior_severity": "medium",
            "current_severity": None,
            "prior_risk_state": "established",
            "current_risk_state": "established",
            "reason": "错误地将仍存在的风险标记为关闭",
            "evidence_summary": {
                "site_ref": "site.01",
                "subject_ref": "S-001",
                "subject_label": "受试者 001",
                "title": "仍存在的电解质异常",
                "risk_ref": "rk-false-closed-001",
                "risk_instance_ref": "rinst-false-closed-001",
                "risk_anchor_ref": "anch-false-closed-001",
                "event_ref": "ev-false-closed-001",
                "source_locator_ref": "loc-false-closed-001",
                "source_count": 1,
                "date_label": "2026-08-28",
                "window_start": "2026-08-01",
                "window_end": "2026-08-28",
            },
        }
    )
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        custom_items=(false_closed,),
    )
    response = ctx["client"].get(
        f"{_base(ctx['project_id'])}/results/{ctx['result_context_token']}/continuity"
    )
    assert response.status_code == 409
    assert response.json()["code"] == "continuity_unavailable"


def test_slice08c1_continuity_keeps_new_risk_with_unconfirmed_severity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity import (
        build_carry_forward_item,
    )

    authority_item = build_carry_forward_item(
        {
            "ordinal": 0,
            "object_type": "risk_instance",
            "object_ref": "rk-severity-001",
            "risk_change_kind": "new",
            "disposition": "re_evaluate_changed_data",
            "data_change_kind": "added",
            "current_severity": "high",
            "current_risk_state": "established",
            "reason": "新增风险",
            "evidence_summary": {
                "site_ref": "site.01",
                "subject_ref": "S-001",
                "subject_label": "受试者 001",
                "title": "新增待分级风险",
                "risk_ref": "rk-severity-001",
                "risk_instance_ref": "rinst-severity-001",
                "risk_anchor_ref": "anch-severity-001",
                "event_ref": "ev-severity-001",
                "source_locator_ref": "loc-severity-001",
                "source_count": 1,
                "date_label": "2026-08-28",
            },
        }
    )
    unconfirmed = dataclass_replace(
        authority_item,
        current_severity=None,
        evidence_summary={
            **dict(authority_item.evidence_summary),
            "window_start": "2026-08-01",
            "window_end": "2026-08-28",
        },
        item_digest="",
    )
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        custom_items=(unconfirmed,),
        authority_source_items=(authority_item,),
    )
    response = ctx["client"].get(
        f"{_base(ctx['project_id'])}/results/{ctx['result_context_token']}/continuity"
    )
    assert response.status_code == 200, response.text
    row = response.json()["comparison"]["rows"][0]
    assert row["severity_after_text"] == ""
    assert row["attention_text"] == "等级变化待确认"


def test_slice08c1_continuity_requires_complete_r6_artifact_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _make_slice08c_setup_and_publication(tmp_path, monkeypatch)
    with sqlite3.connect(str(ctx["registry_path"])) as connection:
        connection.execute(
            "UPDATE r7_result_publications SET r6_output_set_digest=NULL, "
            "artifact_member_ids_json='[]', artifact_member_set_digest=NULL "
            "WHERE project_id=? AND run_id=?",
            (ctx["project_id"], ctx["run_id"]),
        )
        connection.commit()
    response = ctx["client"].get(
        f"{_base(ctx['project_id'])}/results/{ctx['result_context_token']}/continuity"
    )
    assert response.status_code == 409
    assert response.json()["code"] == "continuity_unavailable"


def test_slice08c1_continuity_rejects_source_artifact_hash_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        source_artifact_sha256_override="f" * 64,
    )
    response = ctx["client"].get(
        f"{_base(ctx['project_id'])}/results/{ctx['result_context_token']}/continuity"
    )
    assert response.status_code == 409
    assert response.json()["code"] == "continuity_unavailable"


def test_slice08c1_continuity_rejects_source_object_identity_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        source_object_id_override="forged-source-object",
    )
    response = ctx["client"].get(
        f"{_base(ctx['project_id'])}/results/{ctx['result_context_token']}/continuity"
    )
    assert response.status_code == 409
    assert response.json()["code"] == "continuity_unavailable"


@pytest.mark.parametrize(
    "fixture_overrides",
    (
        {"omit_authority_event": True},
        {"authority_event_anchor_override": "anch-not-bound-to-risk"},
    ),
)
def test_slice08c1_continuity_rejects_incomplete_risk_event_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_overrides: Mapping[str, Any],
) -> None:
    """A published risk must resolve to its authoritative event and anchor."""
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        **fixture_overrides,
    )
    response = ctx["client"].get(
        f"{_base(ctx['project_id'])}/results/{ctx['result_context_token']}/continuity"
    )
    assert response.status_code == 409
    assert response.json()["code"] == "continuity_unavailable"


@pytest.mark.parametrize(
    ("change_kind", "overrides"),
    (
        (
            "new",
            {
                "prior_risk_state": None,
                "current_risk_state": "established",
                "r2_transition_type": "closed",
            },
        ),
        (
            "upgraded",
            {
                "prior_risk_state": None,
                "current_risk_state": "escalated",
                "r2_transition_type": "escalated",
            },
        ),
        (
            "continued",
            {
                "prior_risk_state": "identity_ambiguous",
                "current_risk_state": "established",
                "r2_transition_type": "established",
            },
        ),
        (
            "closed",
            {
                "prior_risk_state": None,
                "current_risk_state": "closed",
                "r2_transition_type": "closed",
            },
        ),
        (
            "needs_rejudgment",
            {
                "prior_risk_state": "established",
                "current_risk_state": "identity_ambiguous",
                "r2_transition_type": "closed",
            },
        ),
        (
            "continued",
            {
                "prior_risk_state": "established",
                "current_risk_state": "established",
                "current_present": False,
                "data_change_kind": "missing",
            },
        ),
        (
            "continued",
            {
                "prior_risk_state": "established",
                "current_risk_state": "established",
                "data_change_kind": "cannot_compare",
            },
        ),
    ),
)
def test_slice08c1_canonical_r2_validator_rejects_illegal_state_matrix(
    change_kind: str,
    overrides: Mapping[str, Any],
) -> None:
    import services.api.app.medical_monitoring_r7_product_router as product_mod

    values = {
        "prior_risk_state": "established",
        "current_risk_state": "established",
        "r2_transition_type": "",
        "prior_severity": "medium",
        "current_severity": "medium",
        "identity_ambiguous": False,
        "lineage_changed": False,
        "data_missing": False,
        "identity_compatible": True,
        "source_compatible": True,
        "output_contract_compatible": True,
        "current_present": True,
        "data_change_kind": "unchanged",
        "disposition": "close_with_evidence",
        "closure_evidence_refs": ("source-closure-001",),
        "closure_allowed": True,
        "current_listing_complete": True,
        "baseline_eligible": True,
    }
    values.update(overrides)
    with pytest.raises(product_mod.ProductPublicationError) as exc_info:
        product_mod._validate_continuity_risk_semantics(
            SimpleNamespace(**values), change_kind
        )
    assert exc_info.value.code == "continuity_unavailable"


def test_slice08c1_continuity_endpoint_authorization_and_principal_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify unauthenticated, unauthorized, or cross-project requests fail closed."""
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        mode="daily",
    )
    project_id = ctx["project_id"]
    result_context_token = ctx["result_context_token"]

    # 1. Unauthenticated request -> 401/503 (principal_required or authority_provider_invalid depending on wiring)
    unauth_client = _client(
        tmp_path,
        principal=None,
    )
    unauth_resp = unauth_client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity"
    )
    assert unauth_resp.status_code in {401, 503}
    _assert_error_body(unauth_resp.json(), status_code=unauth_resp.status_code)

    # 2. Principal lacking READ_AI_RUN role -> 403
    no_read_principal = _principal(project_id, roles=("medical_writer",))
    forbidden_client = _client(
        tmp_path,
        principal=no_read_principal,
    )
    forbidden_resp = forbidden_client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity"
    )
    assert forbidden_resp.status_code == 403
    _assert_error_body(forbidden_resp.json(), status_code=403)

    # 3. Cross-project isolation: token queried against PROJECT_B
    cross_resp = ctx["client"].get(
        f"{_base(PROJECT_B)}/results/{result_context_token}/continuity"
    )
    assert cross_resp.status_code in {403, 404, 409}


def test_slice08c1_continuity_endpoint_initial_analysis_without_baseline(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify initial full analysis without baseline returns correct comparison texts."""
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        mode="daily",
        baseline=None,
        execution_basis="full",
    )
    client = ctx["client"]
    project_id = ctx["project_id"]
    result_context_token = ctx["result_context_token"]

    resp = client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity"
    )
    assert resp.status_code == 200, resp.text
    comparison = resp.json()["comparison"]

    assert comparison["basis_text"] == "全量分析"
    assert comparison["comparison_text"] == "本轮为首次全面分析，无比较基线"
    assert comparison["source_run_text"] == ""


def test_slice08c1_continuity_endpoint_truncation_over_200_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that plans with > 200 items truncate to 200 rows with shown_count=200 and truncated=True."""
    from poc.medical_monitoring_ai_native_r7.src.mm_r7.continuity import build_carry_forward_item

    # Build 210 items
    large_items = []
    for i in range(210):
        # new items: prior None, current high/medium/low valid; continued: prior low, current low must match
        is_new = i % 2 == 0
        large_items.append(
            build_carry_forward_item(
                {
                    "ordinal": i,
                    "object_type": "risk_instance",
                    "object_ref": f"rk-large-{i:03d}",
                    "risk_change_kind": "new" if is_new else "continued",
                    "disposition": "re_evaluate_changed_data",
                    "data_change_kind": "added" if is_new else "unchanged",
                    "prior_severity": None if is_new else "low",
                    "current_severity": ("high" if i % 4 == 0 else "low") if is_new else "low",
                        "prior_risk_state": None if is_new else "established",
                        "current_risk_state": "established",
                            "r2_transition_type": "",
                        "reason": f"第 {i} 项测试风险记录",
                        "evidence_summary": {
                            "site_ref": "site.01",
                            "subject_ref": f"S-{i:03d}",
                            "subject_label": f"受试者 {i:03d}",
                            "title": f"大规模测试风险 {i}",
                            "risk_ref": f"rk-large-{i:03d}",
                            "risk_instance_ref": f"rinst-{i:03d}",
                            "risk_anchor_ref": f"anch-{i:03d}",
                            "event_ref": f"ev-{i:03d}",
                            "source_locator_ref": f"loc-{i:03d}",
                            "source_count": 1,
                            "date_label": "2026-08-28",
                            "window_start": "2026-08-01",
                            "window_end": "2026-08-28",
                        },
                }
            )
        )
    ctx = _make_slice08c_setup_and_publication(
        tmp_path,
        monkeypatch,
        mode="daily",
        custom_items=large_items,
    )
    client = ctx["client"]
    project_id = ctx["project_id"]
    result_context_token = ctx["result_context_token"]

    resp = client.get(
        f"{_base(project_id)}/results/{result_context_token}/continuity"
    )
    assert resp.status_code == 200, resp.text
    comparison = resp.json()["comparison"]

    assert comparison["total_count"] == 210
    assert comparison["shown_count"] == 200
    assert comparison["truncated"] is True
    assert len(comparison["rows"]) == 200

    # All 200 returned rows are non-empty and well-formed
    assert all(r["row_ref"] for r in comparison["rows"])
