"""Run setup, risk-rule and execution-profile routes for R7."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ...admission.fact_materialization import latest_fact_materialization_ready
from pydantic import ValidationError

from ..run_entry import ProfileFieldsRequest, chinese_message_for
from ...runtime import project_backup as pb
from ...runtime import run_setup as rs
from .contracts import (
    ProductRiskRulePreviewRequest,
    ProductRiskRuleRequest,
)
from .errors import (
    _error_response,
    _run_entry_error_response,
    _validation_error_response,
)
from .legacy_projections import (
    _legacy_profile_projection,
    _legacy_risk_projection,
    _setup_projection,
)
from .public_text import _projection


@dataclass(frozen=True)
class SetupRouteContext:
    root: Path
    resolve_project: Any
    authorize: Any
    mutable_project_error: Any
    read_json_object: Any
    acquire_product_write_gate: Any
    open_entry: Any
    legacy_setup_projection: Any
    setup_catalog: Any
    setup_registry: Any
    open_legacy_view: Any
    validated_layer_scope: Any
    workspace_dir: Any
    risk_registry_lock: Any
    monitoring_action: Any


def register_setup_routes(router: APIRouter, context: SetupRouteContext) -> None:
    root = context.root
    resolve_project = context.resolve_project
    authorize = context.authorize
    mutable_project_error = context.mutable_project_error
    _read_json_object = context.read_json_object
    acquire_product_write_gate = context.acquire_product_write_gate
    _open_entry = context.open_entry
    legacy_setup_projection = context.legacy_setup_projection
    setup_catalog = context.setup_catalog
    setup_registry = context.setup_registry
    open_legacy_view = context.open_legacy_view
    _validated_layer_scope = context.validated_layer_scope
    _workspace_dir = context.workspace_dir
    risk_registry_lock = context.risk_registry_lock
    MonitoringAction = context.monitoring_action

    @router.get("/run-setup/options")
    async def get_run_setup_options(
        project_id: str,
        request: Request,
        current_snapshot_token: Optional[str] = None,
        snapshot_token: Optional[str] = None,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        for selector in (current_snapshot_token, snapshot_token):
            if selector is not None and not selector.strip():
                return _run_entry_error_response(
                    rs.RunSetupError("invalid_snapshot")
                )
        workspace = _workspace_dir(root, canonical)
        if (
            (workspace / "admissions").is_dir()
            and not latest_fact_materialization_ready(canonical, workspace)
        ):
            return _run_entry_error_response(rs.RunSetupError("run_data_not_ready"))
        try:
            legacy_options = legacy_setup_projection(canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)
        if legacy_options is not None:
            return legacy_options
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        catalog = setup_catalog(canonical)
        if isinstance(catalog, JSONResponse):
            return catalog
        try:
            options = catalog.get_options(
                canonical,
                current_snapshot_token=current_snapshot_token or snapshot_token,
            )
            return _setup_projection(options.public_projection())
        except Exception as exc:
            return _run_entry_error_response(exc)
    
    @router.post("/risk-rules/preview")
    async def preview_risk_rule(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.DRAFT_QUERY,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error
    
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductRiskRulePreviewRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            registry = setup_registry(canonical)
            if isinstance(registry, JSONResponse):
                return registry
            preview = registry.preview(
                canonical,
                parsed.source_text,
                applicable_scope=parsed.applicable_scope,
                starting_run=parsed.starting_run,
            )
            return _setup_projection(preview.as_dict())
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            write_permit.release()
    
    @router.post("/risk-rules")
    async def append_risk_rule(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.DRAFT_QUERY,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error
    
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductRiskRuleRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            with risk_registry_lock:
                registry = setup_registry(canonical)
                if isinstance(registry, JSONResponse):
                    return registry
                if parsed.preview is not None:
                    draft: Any = parsed.preview
                elif parsed.draft is not None:
                    draft = parsed.draft
                elif parsed.preview_token:
                    draft = parsed.preview_token
                else:
                    draft = {}
                kwargs: dict[str, Any] = {}
                if parsed.candidate_id is not None:
                    kwargs["candidate_id"] = parsed.candidate_id
                if parsed.starting_run is not None:
                    kwargs["starting_run"] = parsed.starting_run
                if parsed.created_at:
                    kwargs["created_at"] = parsed.created_at
                if parsed.idempotency_key is not None:
                    kwargs["idempotency_key"] = parsed.idempotency_key
                revision = registry.append_revision(canonical, draft, **kwargs)
                return _setup_projection(revision.as_dict())
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            write_permit.release()
    
    @router.get("/risk-rules")
    async def get_risk_rules(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_RISK_AUDIT,
        )
        if isinstance(auth, JSONResponse):
            return auth
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                return _setup_projection(
                    {
                        "schema_version": rs.SCHEMA_VERSION,
                        "project_id": canonical,
                        "rule_revisions": [
                            _legacy_risk_projection(row)
                            for row in view.list_risk_rules()
                        ],
                    }
                )
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        registry = setup_registry(canonical)
        if isinstance(registry, JSONResponse):
            return registry
        try:
            return _setup_projection(
                {
                    "schema_version": rs.SCHEMA_VERSION,
                    "project_id": canonical,
                    "rule_revisions": registry.public_revisions(canonical),
                }
            )
        except Exception as exc:
            return _run_entry_error_response(exc)
    
    @router.post("/execution-profiles/{layer_kind}/{scope_key}")
    async def append_profile(
        project_id: str,
        layer_kind: str,
        scope_key: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        if isinstance(auth, JSONResponse):
            return auth
        compatibility_error = mutable_project_error(
            canonical,
            allow_uninitialized=True,
        )
        if compatibility_error is not None:
            return compatibility_error
    
        validated_scope = _validated_layer_scope(
            layer_kind=layer_kind,
            scope_key=scope_key,
            canonical_project_id=canonical,
        )
        if isinstance(validated_scope, JSONResponse):
            return validated_scope
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProfileFieldsRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        fields = parsed.fields()
        if not fields:
            return _error_response(
                422,
                "empty_override_payload",
                chinese_message_for("empty_override_payload"),
            )
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            result = entry.append_execution_profile(
                layer_kind, validated_scope, fields
            )
            return _projection(result)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()
    
    @router.get("/execution-profiles/{layer_kind}/{scope_key}")
    async def get_profile(
        project_id: str,
        layer_kind: str,
        scope_key: str,
        request: Request,
    ) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            action=MonitoringAction.READ_AI_RUN,
        )
        if isinstance(auth, JSONResponse):
            return auth
        validated_scope = _validated_layer_scope(
            layer_kind=layer_kind,
            scope_key=scope_key,
            canonical_project_id=canonical,
        )
        if isinstance(validated_scope, JSONResponse):
            return validated_scope
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                rows = view.list_execution_profiles(
                    layer_kind=layer_kind,
                    scope_key=validated_scope,
                )
                if not rows:
                    return _error_response(
                        404,
                        "profile_layer_not_found",
                        chinese_message_for("profile_layer_not_found"),
                    )
                return _legacy_profile_projection(rows[-1])
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            return entry
        try:
            return _projection(
                entry.get_execution_profile(layer_kind, validated_scope)
            )
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()


__all__ = ["SetupRouteContext", "register_setup_routes"]
