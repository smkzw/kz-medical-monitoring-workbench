"""B5 ``--synthetic`` startup seed tests: idempotent deterministic run seed."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.app.medical_monitoring_r7_product_router import (
    R7_PRODUCT_PREFIX,
    create_medical_monitoring_r7_product_router,
)
from services.api.app.monitoring_runtime_principal import (
    MonitoringAuthenticatedPrincipal,
)
from services.api.app.__main__ import _seed_synthetic_run
from packages.medical_monitoring.api.r7_product.route_utils import (
    R7_WORKSPACE_ROOT_NAME,
)
from packages.medical_monitoring.projections.product_types import (
    SYNTHETIC_PROJECT_REF,
)
from packages.medical_monitoring.runtime.run_entry import MonitoringRunEntry

RUN_ID = "s7-run-current-001"


def _synthetic_route_principal() -> MonitoringAuthenticatedPrincipal:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return MonitoringAuthenticatedPrincipal.from_server_verified_claims(
        {
            "server_verified": True,
            "principal_id": "s7-browser-medical-monitor",
            "tenant_id": "s7-tenant-001",
            "roles": ["medical_manager", "system_admin"],
            "project_scope": [SYNTHETIC_PROJECT_REF],
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=2)).isoformat(),
            "authenticated": True,
            "authn_method": "local-synthetic-fixture",
            "session_id": "s7-browser-session",
            "directory_revision": "s7-browser-directory-v1",
            "verification_ref_sha256": "d" * 64,
        },
        now=now,
    )


def _synthetic_app(runtime_dir: Path) -> FastAPI:
    app = FastAPI()
    app.include_router(
        create_medical_monitoring_r7_product_router(
            runtime_dir=runtime_dir,
            # main.py resolves projects through the manifest; synthetic mode
            # additionally lets the synthetic project canonicalize to itself.
            project_resolver=(
                lambda project_id: (
                    SYNTHETIC_PROJECT_REF
                    if project_id == SYNTHETIC_PROJECT_REF
                    else project_id
                )
            ),
            principal_resolver=lambda _request: _synthetic_route_principal(),
            require_server_principal=True,
            synthetic_fixture_mode=True,
        )
    )
    return app


def _run_is_bound(workspace: Path) -> bool:
    entry = MonitoringRunEntry(workspace)
    try:
        entry.run_binding_store.get(RUN_ID)
        return True
    finally:
        entry.close()


def test_seed_synthetic_run_is_idempotent(tmp_path: Path) -> None:
    app = _synthetic_app(tmp_path)
    workspace = tmp_path / R7_WORKSPACE_ROOT_NAME / SYNTHETIC_PROJECT_REF

    first = _seed_synthetic_run(app, runtime_dir=tmp_path)
    assert first["seeded"] is True
    assert first["run_id"] == RUN_ID
    assert _run_is_bound(workspace)

    second = _seed_synthetic_run(app, runtime_dir=tmp_path)
    assert second["seeded"] is False
    assert _run_is_bound(workspace)

    progress = TestClient(app).get(
        f"{R7_PRODUCT_PREFIX.format(project_id=SYNTHETIC_PROJECT_REF)}"
        f"/runs/{RUN_ID}/progress"
    )
    assert progress.status_code == 200, progress.text
    body = progress.json()
    assert body["run_state"] == "waiting_start"
    assert body["total"] == 2
