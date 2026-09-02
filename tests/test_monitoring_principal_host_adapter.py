from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from starlette.requests import Request

from services.api.app.monitoring_principal_host_adapter import (
    MONITORING_PRINCIPAL_STATE_KEY,
    build_local_single_user_principal,
    local_single_user_enabled,
    resolve_monitoring_principal_from_request,
)
from services.api.app.monitoring_runtime_principal import (
    MonitoringAuthenticatedPrincipal,
)
from services.api.app.monitoring_identity_authorization import MonitoringRole


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = ROOT / "services" / "api" / "app" / "main.py"


def _request() -> Request:
    return Request({"type": "http", "method": "POST", "path": "/"})


def _principal() -> MonitoringAuthenticatedPrincipal:
    return MonitoringAuthenticatedPrincipal(
        principal_id="host-principal",
        tenant_id="tenant-kangzhe",
        roles=(MonitoringRole.MEDICAL_MANAGER,),
        project_scope=("proj-host",),
        issued_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
        authenticated=True,
        authn_method="host-session",
        session_id="host-session-secret",
        directory_revision="directory-host-v1",
        verification_ref_sha256="a" * 64,
    )


def test_missing_request_state_is_fail_closed():
    request = _request()

    assert resolve_monitoring_principal_from_request(request) is None


def test_wrong_request_state_type_is_not_treated_as_authenticated():
    request = _request()
    setattr(request.state, MONITORING_PRINCIPAL_STATE_KEY, {"principal_id": "forged"})

    assert resolve_monitoring_principal_from_request(request) is None


def test_verified_request_state_principal_is_returned_unchanged():
    request = _request()
    principal = _principal()
    setattr(request.state, MONITORING_PRINCIPAL_STATE_KEY, principal)

    assert resolve_monitoring_principal_from_request(request) is principal


def test_local_single_user_identity_is_server_owned_and_project_scoped():
    now = datetime(2026, 9, 2, tzinfo=timezone.utc)
    principal = build_local_single_user_principal(
        ("proj-a", "proj-b", "proj-a"),
        now=now,
        local_user="medical-monitor",
        device_name="workstation-1",
    )

    assert principal.project_scope == ("proj-a", "proj-b")
    assert principal.roles == (MonitoringRole.MEDICAL_MANAGER, MonitoringRole.SYSTEM_ADMIN)
    assert principal.authn_method == "local-os-user-device"
    assert principal.verification_ref_sha256 == (
        "40eaf590cb2ec4a5e73251f3c91be4307a2a56b95234518f53183cbd7c2981ef"
    )
    assert principal.expires_at > now


def test_local_single_user_profile_requires_explicit_host_switch():
    assert local_single_user_enabled("true") is True
    assert local_single_user_enabled("1") is True
    assert local_single_user_enabled("") is False
    assert local_single_user_enabled(None) is False


def test_main_wires_the_adapter_without_installing_a_fallback_identity():
    source = MAIN_SOURCE.read_text(encoding="utf-8")

    assert "from .monitoring_principal_host_adapter import" in source
    assert "resolve_monitoring_principal_from_request" in source
    assert "principal_resolver=resolve_monitoring_principal_from_request" in source
    assert "require_server_principal=True" in source
