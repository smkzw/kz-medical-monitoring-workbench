"""Host seam for a server-verified monitoring principal.

The workbench host may eventually install an authentication/session middleware
that places a verified :class:`MonitoringAuthenticatedPrincipal` on
``request.state``.  This adapter only reads that already-verified object.  It
does not parse headers, cookies, bearer tokens, client actors, or session
material, and it returns ``None`` for missing or malformed state so the route
boundary can fail closed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import getpass
from hashlib import sha256
import platform
from typing import Iterable

from fastapi import Request

from .monitoring_runtime_principal import MonitoringAuthenticatedPrincipal


MONITORING_PRINCIPAL_STATE_KEY = "monitoring_principal"
LOCAL_SINGLE_USER_ENV = "WORKBENCH_LOCAL_SINGLE_USER"


def resolve_monitoring_principal_from_request(
    request: Request,
) -> MonitoringAuthenticatedPrincipal | None:
    """Read the host-provided verified principal without authenticating it."""

    candidate = getattr(request.state, MONITORING_PRINCIPAL_STATE_KEY, None)
    if isinstance(candidate, MonitoringAuthenticatedPrincipal):
        return candidate
    return None


def local_single_user_enabled(value: str | None) -> bool:
    """Return whether the explicit local single-user host profile is enabled."""

    return str(value or "").strip().casefold() in {"1", "true", "yes", "on"}


def build_local_single_user_principal(
    project_scope: Iterable[str],
    *,
    now: datetime | None = None,
    local_user: str | None = None,
    device_name: str | None = None,
) -> MonitoringAuthenticatedPrincipal:
    """Build the server-owned identity required by the local desktop product.

    The v1.2 product is a local single-user workbench. Identity comes from the
    operating-system user and device, never from request headers or browser
    input. This records ordinary local confirmation identity; it is not an
    electronic signature.
    """

    current = now or datetime.now(timezone.utc)
    user = str(local_user or getpass.getuser()).strip()
    device = str(device_name or platform.node()).strip()
    projects = tuple(dict.fromkeys(str(item).strip() for item in project_scope if str(item).strip()))
    if not user or not device or not projects:
        raise ValueError("local single-user identity requires user, device and project scope")
    identity_hash = sha256(f"{user}\0{device}\0cms-medical-workbench".encode("utf-8")).hexdigest()
    # R24V2-W04（20260926授权决策）：本地单用户产品的唯一OS用户即本机
    # 医学经理责任人，规则确认/发布（APPROVE_RULE_CHANGE，总监专属+
    # 电子签名级）由其承担。注意：这是本地确认身份，不是托管电子签名
    # 系统——托管多用户部署时必须重新评审该角色映射（附于台账）。
    return MonitoringAuthenticatedPrincipal.from_server_verified_claims(
        {
            "server_verified": True,
            "principal_id": f"local-user-{identity_hash[:16]}",
            "tenant_id": f"local-workbench-{identity_hash[16:32]}",
            "roles": ["medical_manager", "system_admin", "medical_director"],
            "project_scope": list(projects),
            "issued_at": current.isoformat(),
            "expires_at": (current + timedelta(hours=12)).isoformat(),
            "authenticated": True,
            "authn_method": "local-os-user-device",
            "session_id": f"local-session-{identity_hash[32:48]}",
            "directory_revision": "local-single-user-v1",
            "verification_ref_sha256": identity_hash,
        },
        now=current,
    )
