from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from services.api.app.medical_monitoring_r5_product_router import (
    create_medical_monitoring_r5_product_router,
)


ROOT = Path(__file__).resolve().parents[1]
ASSIGNED = {
    "services/api/app/medical_monitoring_r5_product_router.py",
    "services/api/app/medical_monitoring_r5_product_adapter.py",
    "services/api/app/main.py",
    "services/api/app/monitoring_read_action_contract.py",
    "tests/test_medical_monitoring_r5_product_adapter.py",
    "tests/test_medical_monitoring_r5_product_router.py",
    "tests/test_medical_monitoring_r5_product_allowlist.py",
}


def test_assigned_backend_paths_exist_and_no_medical_writing_file_is_added() -> None:
    assert all((ROOT / path).is_file() for path in ASSIGNED)
    assert not any("medical-writing" in path or "medical_writing" in path for path in ASSIGNED)


def test_product_router_is_get_only_and_has_no_legacy_api_fallback() -> None:
    app = FastAPI()
    app.include_router(create_medical_monitoring_r5_product_router(synthetic_fixture_mode=True))
    r5_routes = [
        route
        for route in app.routes
        if "/modules/medical-monitoring/r5" in route.path
    ]
    assert len(r5_routes) == 3
    assert all(route.methods == {"GET"} for route in r5_routes)

    source = (ROOT / "services/api/app/medical_monitoring_r5_product_router.py").read_text()
    assert "medical_monitoring_router" not in source
    assert "medicalMonitoringApi" not in source


def test_read_action_contract_exposes_three_r5_surface_names_without_legacy_iteration_drift() -> None:
    from services.api.app.monitoring_read_action_contract import (
        MonitoringReadSurface,
        R5_OVERVIEW,
        R5_SOURCE_EVIDENCE,
        R5_SUBJECT_WORKSPACE,
    )

    assert tuple(MonitoringReadSurface)
    assert MonitoringReadSurface.R5_OVERVIEW.value == R5_OVERVIEW.value
    assert MonitoringReadSurface.R5_SUBJECT_WORKSPACE.value == R5_SUBJECT_WORKSPACE.value
    assert MonitoringReadSurface.R5_SOURCE_EVIDENCE.value == R5_SOURCE_EVIDENCE.value


def test_main_has_only_one_r5_router_import_and_include_seam() -> None:
    source = (ROOT / "services/api/app/main.py").read_text()
    assert source.count("create_medical_monitoring_r5_product_router") == 2
    assert "WORKBENCH_R5_S7_FIXTURE_MODE" in source
    assert "principal_resolver=_resolve_r5_product_principal" in source
    assert '"project_scope": ["s7-synthetic-project-001"]' in source
    assert "request.headers" not in source[source.index("_r5_s7_fixture_mode") : source.index("create_monitoring_daily_run_router")]
