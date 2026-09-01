"""The closed, GET-only R5-S7 product API surface."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
from typing import Any, Callable, Mapping, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import ORJSONResponse

from .medical_monitoring_r5_product_adapter import (
    R5ProductAdapter,
    R5ProductAdapterError,
    build_response_envelope,
)
from .monitoring_audit_contract import MonitoringAuditTargetType
from .monitoring_authorized_route_context import (
    MonitoringAuthorizedRouteContext,
    MonitoringAuthorizedRouteContextError,
    build_monitoring_authorized_route_context,
)
from .monitoring_identity_authorization import (
    MonitoringAction,
    authorize_monitoring_action,
)
from .monitoring_runtime_principal import (
    MonitoringAuthenticatedPrincipal,
    MonitoringRuntimePrincipalDenied,
)
from .monitoring_runtime_route_context import (
    MonitoringRuntimeRouteContextError,
    build_monitoring_runtime_route_context,
)


R5_PRODUCT_PREFIX = "/api/projects/{project_id}/modules/medical-monitoring/r5"
R5_SURFACE_OVERVIEW = "r5_overview"
R5_SURFACE_SUBJECT_WORKSPACE = "r5_subject_workspace"
R5_SURFACE_SOURCE_EVIDENCE = "r5_source_evidence"
R5_SURFACE_ACTION = {
    R5_SURFACE_OVERVIEW: MonitoringAction.READ_MONITORING,
    R5_SURFACE_SUBJECT_WORKSPACE: MonitoringAction.READ_MONITORING,
    R5_SURFACE_SOURCE_EVIDENCE: MonitoringAction.READ_SOURCE_EVIDENCE,
}
R5_QUERY_ALLOWLIST = {
    "overview": frozenset({"run_ref", "snapshot_ref", "cutoff_ref", "site_ref"}),
    "subject_workspace": frozenset(
        {
            "run_ref",
            "snapshot_ref",
            "cutoff_ref",
            "site_ref",
            "spine_ref",
            "window_start",
            "window_end",
            "risk_instance_ref",
            "risk_anchor_ref",
            "visit_ref",
            "event_ref",
        }
    ),
    "source_evidence": frozenset(
        {"run_ref", "snapshot_ref", "cutoff_ref", "risk_instance_ref", "source_locator_ref"}
    ),
}


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _canonical_path_value(value: str, field_name: str) -> str:
    text = str(value or "").strip()
    if not text or text != value:
        raise _http_error(422, "r5_path_invalid", f"{field_name} path is invalid")
    return text


async def _reject_get_body(request: Request) -> None:
    body = await request.body()
    if body:
        raise _http_error(422, "r5_request_body_forbidden", "R5 read routes do not accept a request body")


def _parse_query(
    request: Request,
    surface: str,
    *,
    required: frozenset[str] = frozenset(),
    grouped: bool = False,
) -> dict[str, str]:
    allowed = R5_QUERY_ALLOWLIST[surface]
    result: dict[str, str] = {}
    for key, value in request.query_params.multi_items():
        if key not in allowed:
            raise _http_error(422, "r5_query_key_forbidden", f"unknown R5 query key: {key}")
        if key in result:
            raise _http_error(422, "r5_query_duplicate", f"duplicate R5 query key: {key}")
        cleaned = str(value or "").strip()
        if not cleaned:
            raise _http_error(422, "r5_query_value_invalid", f"empty R5 query value: {key}")
        result[key] = cleaned
    if grouped:
        supplied_identity = set(result).intersection(required)
        if supplied_identity and supplied_identity != set(required):
            raise _http_error(422, "r5_query_group_incomplete", "run_ref, snapshot_ref and cutoff_ref must be supplied together")
        return result
    missing = required - set(result)
    if missing:
        raise _http_error(422, "r5_query_required", f"missing R5 query keys: {', '.join(sorted(missing))}")
    return result


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise _http_error(422, "r5_date_invalid", f"{field_name} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise _http_error(422, "r5_date_invalid", f"{field_name} must be canonical ISO date")
    return parsed


def _request_id(request: Request, *, surface: str, target_id: str) -> str:
    supplied = str(request.headers.get("X-Request-ID", "") or "").strip()
    if supplied and len(supplied) <= 200 and all(char.isalnum() or char in "._:/-" for char in supplied):
        return supplied
    material = f"{surface}|{request.url.path}|{request.url.query}|{target_id}"
    return f"r5-request:{sha256(material.encode('utf-8')).hexdigest()[:32]}"


def _audit_id(*, request_id: str, surface: str, target_id: str, source_revision: str) -> str:
    return f"r5-audit:{sha256(f'{request_id}|{surface}|{target_id}|{source_revision}'.encode('utf-8')).hexdigest()}"


def _resolve_route_context(
    request: Request,
    *,
    project_id: str,
    surface: str,
    target_id: str,
    principal_resolver: Optional[Callable[[Request], MonitoringAuthenticatedPrincipal | None]],
    require_server_principal: bool,
) -> MonitoringRuntimeRouteContext:
    if not require_server_principal:
        raise _http_error(503, "r5_principal_required", "R5 requires a server-verified principal")
    if principal_resolver is None:
        raise _http_error(503, "r5_principal_unavailable", "R5 server-verified principal is unavailable")
    try:
        principal = principal_resolver(request)
    except Exception as exc:
        raise _http_error(503, "r5_principal_unavailable", "R5 server-verified principal lookup failed") from exc
    if not isinstance(principal, MonitoringAuthenticatedPrincipal):
        raise _http_error(503, "r5_principal_unavailable", "R5 requires a server-verified principal")
    action = R5_SURFACE_ACTION[surface]
    request_id = _request_id(request, surface=surface, target_id=target_id)
    try:
        route_context = build_monitoring_runtime_route_context(
            principal,
            request_id=request_id,
            route_project_id=project_id,
            tenant_id=principal.tenant_id,
            target_scope="subject" if surface == R5_SURFACE_SUBJECT_WORKSPACE else "trial",
            action=action,
        )
        authorization_principal = route_context.principal.to_monitoring_principal(
            now=route_context.validated_at
        )
        decision = authorize_monitoring_action(
            authorization_principal,
            route_context.request,
        )
    except MonitoringRuntimePrincipalDenied as exc:
        status = 401 if exc.reason_code in {"principal_not_authenticated", "principal_not_yet_valid", "principal_expired"} else 403
        raise _http_error(status, f"r5_{exc.reason_code}", "R5 principal is not authorized") from exc
    except (MonitoringRuntimeRouteContextError, MonitoringAuthorizedRouteContextError, ValueError) as exc:
        raise _http_error(403, "r5_authorization_invalid", "R5 read authorization handoff is invalid") from exc
    if not decision.allowed:
        raise _http_error(403, "r5_read_not_permitted", "R5 principal is not permitted to read this surface")
    return route_context


def _authorize(
    request: Request,
    *,
    project_id: str,
    surface: str,
    target_type: MonitoringAuditTargetType,
    target_id: str,
    source_revision: str,
    principal_resolver: Optional[Callable[[Request], MonitoringAuthenticatedPrincipal | None]],
    require_server_principal: bool,
    route_context: Optional[MonitoringRuntimeRouteContext] = None,
) -> MonitoringAuthorizedRouteContext:
    if route_context is None:
        route_context = _resolve_route_context(
            request,
            project_id=project_id,
            surface=surface,
            target_id=target_id,
            principal_resolver=principal_resolver,
            require_server_principal=require_server_principal,
        )
    try:
        authorized = build_monitoring_authorized_route_context(
            route_context,
            audit_id=_audit_id(
                request_id=route_context.request.request_id,
                surface=surface,
                target_id=target_id,
                source_revision=source_revision,
            ),
            target_type=target_type,
            target_id=target_id,
            source_revision=source_revision,
            occurred_at=route_context.validated_at,
            payload={"surface": surface, "read_only": True, "synthetic_fixture_boundary": "explicit"},
            aggregate_version_before=0,
        )
    except (MonitoringRuntimeRouteContextError, MonitoringAuthorizedRouteContextError, ValueError) as exc:
        raise _http_error(403, "r5_authorization_invalid", "R5 read authorization handoff is invalid") from exc
    if not authorized.decision.allowed:
        raise _http_error(403, "r5_read_not_permitted", "R5 principal is not permitted to read this surface")
    return authorized


def _translate_adapter_error(exc: R5ProductAdapterError) -> HTTPException:
    if exc.code in {"AUTHORITY_PACKET_UNAVAILABLE", "AUTHORITY_PROVIDER_INVALID"}:
        return _http_error(503, f"r5_{exc.code.lower()}", "R5 authority packet is unavailable; synthetic fallback is disabled")
    if exc.code in {"PROJECT_IDENTITY_MISMATCH", "AUTHORITY_IDENTITY_MISMATCH", "CUTOFF_IDENTITY_MISMATCH", "SOURCE_SNAPSHOT_MISMATCH", "TARGET_NOT_PROJECTABLE", "SOURCE_LOCATOR_NOT_BOUND", "SNAPSHOT_NOT_IN_SYNTHETIC_PACKET", "RUN_NOT_IN_SYNTHETIC_PACKET", "PROJECT_NOT_IN_SYNTHETIC_PACKET"}:
        return _http_error(409, f"r5_{exc.code.lower()}", "R5 target is not an exact member of the authority packet")
    return _http_error(422, f"r5_{exc.code.lower()}", "R5 request or authority packet failed closed validation")


def create_medical_monitoring_r5_product_router(
    *,
    authority_provider: Optional[Any] = None,
    principal_resolver: Optional[Callable[[Request], MonitoringAuthenticatedPrincipal | None]] = None,
    require_server_principal: bool = True,
    synthetic_fixture_mode: bool = False,
) -> APIRouter:
    """Create only the three R5 product GET routes."""

    adapter = R5ProductAdapter(authority_provider, synthetic_fixture_mode=synthetic_fixture_mode)
    router = APIRouter(prefix=R5_PRODUCT_PREFIX, tags=["medical-monitoring-r5-product"])

    @router.get("/overview")
    async def r5_overview(project_id: str, request: Request) -> dict[str, Any]:
        await _reject_get_body(request)
        project_id = _canonical_path_value(project_id, "project_id")
        query = _parse_query(request, "overview", required=frozenset({"run_ref", "snapshot_ref", "cutoff_ref"}), grouped=True)
        target_id = query.get("site_ref") or project_id
        route_context = _resolve_route_context(
            request,
            project_id=project_id,
            surface=R5_SURFACE_OVERVIEW,
            target_id=target_id,
            principal_resolver=principal_resolver,
            require_server_principal=require_server_principal,
        )
        try:
            result = adapter.overview(
                project_ref=project_id,
                run_ref=query.get("run_ref"),
                snapshot_ref=query.get("snapshot_ref"),
                cutoff_ref=query.get("cutoff_ref"),
                site_ref=query.get("site_ref"),
            )
            packet = result["packet"]
            authorized = _authorize(
                request,
                project_id=project_id,
                surface=R5_SURFACE_OVERVIEW,
                target_type="site" if query.get("site_ref") else "project",
                target_id=target_id,
                source_revision=packet.source_snapshot_sha256,
                principal_resolver=principal_resolver,
                require_server_principal=require_server_principal,
                route_context=route_context,
            )
            envelope = build_response_envelope(
                result,
                read_handoff=_read_handoff(authorized),
                read_handoff_builder=lambda digest: _read_handoff(authorized, digest),
                tenant_id=authorized.route_context.tenant_id,
                principal_identity_hash=authorized.principal.principal_sha256,
                authorization_decision_sha256=authorized.decision.decision_sha256,
                audit_id=authorized.audit_event.audit_id,
            )
            return ORJSONResponse(content=envelope)
        except R5ProductAdapterError as exc:
            raise _translate_adapter_error(exc) from exc

    @router.get("/subject-workspaces/{subject_id}")
    async def r5_subject_workspace(project_id: str, subject_id: str, request: Request) -> dict[str, Any]:
        await _reject_get_body(request)
        project_id = _canonical_path_value(project_id, "project_id")
        subject_id = _canonical_path_value(subject_id, "subject_id")
        required = frozenset({"run_ref", "snapshot_ref", "cutoff_ref", "site_ref", "spine_ref", "window_start", "window_end"})
        query = _parse_query(request, "subject_workspace", required=required)
        route_context = _resolve_route_context(
            request,
            project_id=project_id,
            surface=R5_SURFACE_SUBJECT_WORKSPACE,
            target_id=subject_id,
            principal_resolver=principal_resolver,
            require_server_principal=require_server_principal,
        )
        try:
            result = adapter.subject_workspace(
                project_ref=project_id,
                subject_ref=subject_id,
                run_ref=query["run_ref"],
                snapshot_ref=query["snapshot_ref"],
                cutoff_ref=query["cutoff_ref"],
                site_ref=query["site_ref"],
                spine_ref=query["spine_ref"],
                window_start=_parse_iso_date(query["window_start"], "window_start"),
                window_end=_parse_iso_date(query["window_end"], "window_end"),
                risk_instance_ref=query.get("risk_instance_ref"),
                risk_anchor_ref=query.get("risk_anchor_ref"),
                visit_ref=query.get("visit_ref"),
                event_ref=query.get("event_ref"),
            )
            packet = result["packet"]
            authorized = _authorize(
                request,
                project_id=project_id,
                surface=R5_SURFACE_SUBJECT_WORKSPACE,
                target_type="subject",
                target_id=subject_id,
                source_revision=packet.source_snapshot_sha256,
                principal_resolver=principal_resolver,
                require_server_principal=require_server_principal,
                route_context=route_context,
            )
            envelope = build_response_envelope(
                result,
                read_handoff=_read_handoff(authorized),
                read_handoff_builder=lambda digest: _read_handoff(authorized, digest),
                tenant_id=authorized.route_context.tenant_id,
                principal_identity_hash=authorized.principal.principal_sha256,
                authorization_decision_sha256=authorized.decision.decision_sha256,
                audit_id=authorized.audit_event.audit_id,
            )
            return ORJSONResponse(content=envelope)
        except R5ProductAdapterError as exc:
            raise _translate_adapter_error(exc) from exc

    @router.get("/source-evidence")
    async def r5_source_evidence(project_id: str, request: Request) -> dict[str, Any]:
        await _reject_get_body(request)
        project_id = _canonical_path_value(project_id, "project_id")
        required = frozenset({"run_ref", "snapshot_ref", "cutoff_ref", "risk_instance_ref", "source_locator_ref"})
        query = _parse_query(request, "source_evidence", required=required)
        route_context = _resolve_route_context(
            request,
            project_id=project_id,
            surface=R5_SURFACE_SOURCE_EVIDENCE,
            target_id=query["source_locator_ref"],
            principal_resolver=principal_resolver,
            require_server_principal=require_server_principal,
        )
        try:
            result = adapter.source_evidence(
                project_ref=project_id,
                run_ref=query["run_ref"],
                snapshot_ref=query["snapshot_ref"],
                cutoff_ref=query["cutoff_ref"],
                risk_instance_ref=query["risk_instance_ref"],
                source_locator_ref=query["source_locator_ref"],
            )
            packet = result["packet"]
            authorized = _authorize(
                request,
                project_id=project_id,
                surface=R5_SURFACE_SOURCE_EVIDENCE,
                target_type="source",
                target_id=query["source_locator_ref"],
                source_revision=packet.source_snapshot_sha256,
                principal_resolver=principal_resolver,
                require_server_principal=require_server_principal,
                route_context=route_context,
            )
            envelope = build_response_envelope(
                result,
                read_handoff=_read_handoff(authorized),
                read_handoff_builder=lambda digest: _read_handoff(authorized, digest),
                tenant_id=authorized.route_context.tenant_id,
                principal_identity_hash=authorized.principal.principal_sha256,
                authorization_decision_sha256=authorized.decision.decision_sha256,
                audit_id=authorized.audit_event.audit_id,
            )
            return ORJSONResponse(content=envelope)
        except R5ProductAdapterError as exc:
            raise _translate_adapter_error(exc) from exc

    return router


def _read_handoff(
    context: MonitoringAuthorizedRouteContext,
    response_digest: str = "0" * 64,
) -> Mapping[str, Any]:
    """Create the non-persisted read handoff after route authorization."""

    from .monitoring_read_action_contract import (
        MonitoringReadSurface,
        build_monitoring_read_action_contract,
    )

    surface_name = context.audit_event.payload.get("surface")
    surface = {
        R5_SURFACE_OVERVIEW: getattr(MonitoringReadSurface, "R5_OVERVIEW", R5_SURFACE_OVERVIEW),
        R5_SURFACE_SUBJECT_WORKSPACE: getattr(MonitoringReadSurface, "R5_SUBJECT_WORKSPACE", R5_SURFACE_SUBJECT_WORKSPACE),
        R5_SURFACE_SOURCE_EVIDENCE: getattr(MonitoringReadSurface, "R5_SOURCE_EVIDENCE", R5_SURFACE_SOURCE_EVIDENCE),
    }.get(str(surface_name), surface_name)
    contract = build_monitoring_read_action_contract(
        context,
        surface=surface,
        source_snapshot_sha256=context.audit_event.source_revision,
        response_snapshot_sha256=response_digest,
        idempotency_key=f"{surface_name}:{context.audit_event.audit_id}",
        cas_version=context.audit_event.aggregate_version_before,
    )
    return contract.public_dict()


__all__ = [
    "R5_PRODUCT_PREFIX",
    "R5_QUERY_ALLOWLIST",
    "R5_SURFACE_ACTION",
    "R5_SURFACE_OVERVIEW",
    "R5_SURFACE_SOURCE_EVIDENCE",
    "R5_SURFACE_SUBJECT_WORKSPACE",
    "create_medical_monitoring_r5_product_router",
]
