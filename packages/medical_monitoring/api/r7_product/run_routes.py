"""Run launch, execution, progress and detail routes for R7."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..run_entry import chinese_message_for
from ...runtime import launch_registry as lr
from ...runtime import project_backup as pb
from ...runtime import run_setup as rs
from ...runtime.run_entry import MonitoringRunEntry, RunEntryError
from ...runtime.runtime_progress import RuntimeProgressError
from .contracts import (
    ProductCreateRunRequest,
    ProductExecutionActionRequest,
    ProductPrepareAndStartRequest,
    ProductPrepareExecutionRequest,
)
from .errors import (
    _AUTH_MESSAGES,
    _error_response,
    _launch_error_response,
    _run_entry_error_response,
    _validation_error_response,
)
from .legacy_projections import (
    _execution_action_projection,
    _legacy_binding_projection,
    _legacy_launch_record,
    _legacy_progress_projection,
    _runtime_work_units,
)
from .public_result_requests import _comparison_range_text
from .public_text import _projection
from .result_projections import _launch_projection


@dataclass(frozen=True)
class RunRouteContext:
    root: Path
    resolve_project: Any
    authorize: Any
    mutable_project_error: Any
    read_json_object: Any
    acquire_product_write_gate: Any
    open_entry: Any
    auto_scopes: Any
    open_launch_registry: Any
    progress_adapter: Any
    resolve_launch_inputs: Any
    open_legacy_view: Any
    publication_overlay: Any
    workspace_dir: Any
    workspace_is_ready: Any
    monitoring_action: Any


def register_run_launch_routes(router: APIRouter, context: RunRouteContext) -> None:
    root = context.root
    resolve_project = context.resolve_project
    authorize = context.authorize
    mutable_project_error = context.mutable_project_error
    _read_json_object = context.read_json_object
    acquire_product_write_gate = context.acquire_product_write_gate
    _open_entry = context.open_entry
    _auto_scopes = context.auto_scopes
    open_launch_registry = context.open_launch_registry
    progress_adapter = context.progress_adapter
    resolve_launch_inputs = context.resolve_launch_inputs
    open_legacy_view = context.open_legacy_view
    _publication_overlay = context.publication_overlay
    _workspace_dir = context.workspace_dir
    _workspace_is_ready = context.workspace_is_ready
    MonitoringAction = context.monitoring_action

    @router.post("/runs/prepare-and-start")
    async def prepare_and_start(project_id: str, request: Request) -> Any:
        canonical = resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = authorize(
            request,
            project_id=canonical,
            # Starting a medical-monitoring run is a user-facing AI-run
            # action.  The lower-level execution controls remain admin-only.
            action=MonitoringAction.READ_AI_RUN,
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
            parsed = ProductPrepareAndStartRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)

        workspace = _workspace_dir(root, canonical)
        if not _workspace_is_ready(workspace):
            return _error_response(
                422,
                "global_default_missing",
                _AUTH_MESSAGES["workspace_not_ready"],
            )
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            resolved = resolve_launch_inputs(canonical, parsed)
        except Exception as exc:
            if isinstance(exc, (rs.RunSetupError, RunEntryError, RuntimeProgressError)):
                response = _run_entry_error_response(exc)
            else:
                response = _error_response(500, "internal_error")
            write_permit.release()
            return response
        if isinstance(resolved, JSONResponse):
            write_permit.release()
            return resolved
        current, baseline, revisions, manifest = resolved

        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            write_permit.release()
            return registry
        entry: Optional[MonitoringRunEntry] = None
        try:
            reservation = registry.reserve(
                canonical,
                idempotency_key=parsed.idempotency_key,
                mode=parsed.mode,
                execution_basis=parsed.execution_basis,
                current_snapshot_token=parsed.current_snapshot_token,
                baseline_token=parsed.baseline_token,
                rule_tokens=(
                    rs.public_revision_token(revision.revision_token)
                    for revision in revisions
                ),
                data_cutoff=current.data_cutoff,
                comparison_range_text=_comparison_range_text(
                    parsed.mode,
                    parsed.execution_basis,
                    baseline,
                ),
                enforce_in_flight=True,
            )
            # A retry after the durable reservation but before manifest
            # preparation must finish the same run instead of leaving an
            # unstartable history row.  Once the manifest is recorded, the
            # request is a normal replay and must never start a second worker.
            if reservation.replayed and reservation.record.manifest_digest is not None:
                return _launch_projection(reservation.record, replayed=True)

            entry = _open_entry(workspace, allow_create=False)
            if isinstance(entry, JSONResponse):
                return entry
            run_id = reservation.run_id
            scopes = _auto_scopes(
                entry,
                canonical_project_id=canonical,
                run_id=run_id,
                capability_scope_key="",
            )
            entry.bind_run(
                run_id=run_id,
                project_id=canonical,
                mode=parsed.mode,
                execution_basis=parsed.execution_basis,
                data_cutoff=current.data_cutoff,
                source_revision_id=current.source_revision_id or current.snapshot_ref,
                prior_accepted_snapshot_ref=(
                    baseline.snapshot_ref
                    if parsed.mode == rs.MODE_DAILY
                    and parsed.execution_basis == rs.BASIS_INCREMENTAL
                    and baseline is not None
                    else None
                ),
                **scopes,
            )
            adapter = progress_adapter(workspace, entry, canonical)
            adapter.prepare_execution(run_id, _runtime_work_units(manifest))
            registry.record_manifest(
                run_id,
                manifest.manifest_digest,
                project_id=canonical,
            )
            try:
                adapter.start_execution(run_id)
            except (RuntimeProgressError, RunEntryError) as exc:
                if exc.code != "worker_start_failed":
                    raise
                record = registry.record_start_failure(
                    run_id,
                    project_id=canonical,
                )
                return _launch_projection(record, replayed=False)
            record = registry.mark_running(run_id, project_id=canonical)
            return _launch_projection(record, replayed=reservation.replayed)
        except lr.LaunchRegistryError as exc:
            return _launch_error_response(exc)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            try:
                if entry is not None and not isinstance(entry, JSONResponse):
                    entry.close()
            finally:
                try:
                    registry.close()
                finally:
                    write_permit.release()

    @router.get("/runs")
    async def get_runs(
        project_id: str,
        request: Request,
        limit: Optional[str] = None,
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
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                history_limit: Optional[int] = None
                if limit is not None:
                    try:
                        history_limit = int(limit)
                    except (TypeError, ValueError) as exc:
                        raise lr.LaunchRegistryError(
                            "invalid_history_limit"
                        ) from exc
                    if history_limit < 0:
                        raise lr.LaunchRegistryError("invalid_history_limit")
                    history_limit = min(history_limit, 100)
                rows = sorted(
                    view.list_launches(),
                    key=lambda row: (
                        str(row.get("created_at", "")),
                        int(row.get("sequence", 0)),
                    ),
                    reverse=True,
                )
                if history_limit is not None:
                    rows = rows[:history_limit]
                records = [_legacy_launch_record(row) for row in rows]
                return {
                    "runs": [record.public_projection() for record in records]
                }
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        registry = open_launch_registry(canonical)
        if isinstance(registry, JSONResponse):
            write_permit.release()
            return registry
        entry: Optional[MonitoringRunEntry] = None
        try:
            history_limit: Optional[int] = None
            if limit is not None:
                try:
                    history_limit = int(limit)
                except (TypeError, ValueError) as exc:
                    raise lr.LaunchRegistryError("invalid_history_limit") from exc
            records = list(registry.list_records(canonical, limit=history_limit))
            active = registry.get_in_flight(canonical)
            if active is not None and active.manifest_digest is not None:
                workspace = _workspace_dir(root, canonical)
                entry = _open_entry(workspace, allow_create=False)
                if not isinstance(entry, JSONResponse):
                    adapter = progress_adapter(workspace, entry, canonical)
                    try:
                        state = adapter.read_progress(active.run_id).get(
                            "run_state"
                        )
                        if (
                            state in lr.RUN_STATE_VALUES
                            and state != active.run_state
                        ):
                            updated = registry.update_state(
                                active.run_id,
                                state,
                                project_id=canonical,
                            )
                            records = [
                                updated
                                if record.sequence == active.sequence
                                else record
                                for record in records
                            ]
                    except (
                        RuntimeProgressError,
                        RunEntryError,
                        lr.LaunchRegistryError,
                    ):
                        # A launch reserved before preparation remains a
                        # visible waiting item and is recoverable by the
                        # same idempotent request.
                        pass
            return {"runs": [record.public_projection() for record in records]}
        finally:
            try:
                if entry is not None and not isinstance(entry, JSONResponse):
                    entry.close()
            finally:
                try:
                    registry.close()
                finally:
                    write_permit.release()

def register_execution_routes(router: APIRouter, context: RunRouteContext) -> None:
    root = context.root
    resolve_project = context.resolve_project
    authorize = context.authorize
    mutable_project_error = context.mutable_project_error
    _read_json_object = context.read_json_object
    acquire_product_write_gate = context.acquire_product_write_gate
    _open_entry = context.open_entry
    _auto_scopes = context.auto_scopes
    open_launch_registry = context.open_launch_registry
    progress_adapter = context.progress_adapter
    resolve_launch_inputs = context.resolve_launch_inputs
    open_legacy_view = context.open_legacy_view
    _publication_overlay = context.publication_overlay
    _workspace_dir = context.workspace_dir
    _workspace_is_ready = context.workspace_is_ready
    MonitoringAction = context.monitoring_action

    @router.post("/runs")
    async def bind_run(project_id: str, request: Request) -> Any:
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

        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductCreateRunRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
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
            scopes = _auto_scopes(
                entry,
                canonical_project_id=canonical,
                run_id=parsed.run_id,
                capability_scope_key=parsed.capability_scope_key,
            )
            result = entry.bind_run(
                run_id=parsed.run_id,
                project_id=canonical,
                mode=parsed.mode,
                execution_basis=parsed.execution_basis,
                data_cutoff=parsed.data_cutoff,
                source_revision_id=parsed.source_revision_id,
                prior_accepted_snapshot_ref=parsed.prior_accepted_snapshot_ref,
                **scopes,
            )
            return _projection(result, replayed=True)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.post("/runs/{run_id}/execution/prepare")
    async def prepare_execution(project_id: str, run_id: str, request: Request) -> Any:
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

        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductPrepareExecutionRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
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
            adapter = progress_adapter(workspace, entry, canonical)
            return adapter.prepare_execution(
                run_id,
                parsed.work_units,
                execution_kind=parsed.execution_mode or parsed.execution_kind,
            )
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.post("/runs/{run_id}/execution/start")
    async def start_execution(project_id: str, run_id: str, request: Request) -> Any:
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

        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            ProductExecutionActionRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
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
            adapter = progress_adapter(workspace, entry, canonical)
            return _execution_action_projection(adapter.start_execution(run_id))
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.post("/runs/{run_id}/execution/resume")
    async def resume_execution(project_id: str, run_id: str, request: Request) -> Any:
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

        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            ProductExecutionActionRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
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
            adapter = progress_adapter(workspace, entry, canonical)
            return _execution_action_projection(adapter.resume_execution(run_id))
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.post("/runs/{run_id}/execution/cancel")
    async def cancel_execution(project_id: str, run_id: str, request: Request) -> Any:
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

        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            ProductExecutionActionRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
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
            adapter = progress_adapter(workspace, entry, canonical)
            return _execution_action_projection(adapter.cancel_execution(run_id))
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()

    @router.get("/runs/{public_run_token}/progress")
    async def get_progress(
        project_id: str, public_run_token: str, request: Request
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
        run_id = public_run_token
        resolved_run_id = run_id
        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                launch: Optional[lr.LaunchRecord] = None
                if run_id.startswith("run:"):
                    launch_rows = [
                        row
                        for row in view.list_launches()
                        if row.get("public_run_token") == run_id
                    ]
                    if not launch_rows:
                        return _error_response(
                            404,
                            "public_run_not_found",
                            "未找到指定的监查运行。",
                        )
                    launch = _legacy_launch_record(launch_rows[0])
                    resolved_run_id = launch.run_id
                else:
                    launch_rows = [
                        row
                        for row in view.list_launches()
                        if row.get("run_id") == run_id
                    ]
                    if launch_rows:
                        launch = _legacy_launch_record(launch_rows[0])
                result = _legacy_progress_projection(
                    view,
                    resolved_run_id,
                    launch,
                )
                if auth is not None:
                    action_auth = authorize(
                        request,
                        project_id=canonical,
                        action=MonitoringAction.ADMINISTER_RUNTIME,
                    )
                    if isinstance(action_auth, JSONResponse):
                        result = {**result, "available_actions": []}
                return result
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        resolved_run_id = run_id
        if run_id.startswith("run:"):
            launch_path = (
                _workspace_dir(root, canonical) / lr.LAUNCH_REGISTRY_DB_NAME
            )
            if not launch_path.is_file():
                return _error_response(
                    404,
                    "public_run_not_found",
                    "未找到指定的监查运行。",
                )
            launch_registry = open_launch_registry(canonical)
            if isinstance(launch_registry, JSONResponse):
                return launch_registry
            try:
                resolved_run_id = launch_registry.get_by_public_token(
                    run_id, project_id=canonical
                ).run_id
            except lr.LaunchRegistryError as exc:
                return _launch_error_response(exc)
            finally:
                launch_registry.close()
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
            adapter = progress_adapter(workspace, entry, canonical)
            result = adapter.read_progress(resolved_run_id)
            overlay = _publication_overlay(canonical, resolved_run_id, result)
            has_launch = bool(overlay.pop("_publication_has_launch", False))
            overlay.pop("_publication_public_token", None)
            result = overlay
            # Progress is readable by medical monitors, but run controls and
            # publication actions are only useful to runtime administrators.
            admin_allowed = True
            if auth is not None:
                action_auth = authorize(
                    request,
                    project_id=canonical,
                    action=MonitoringAction.ADMINISTER_RUNTIME,
                )
                admin_allowed = not isinstance(action_auth, JSONResponse)
            if not admin_allowed:
                result = {**result, "available_actions": []}
            elif has_launch and result.get("run_state") == lr.STATE_COMPLETED:
                actions = list(result.get("available_actions", []))
                publication_state = result.get("publication_state")
                action = (
                    "整理结果"
                    if publication_state == "not_started"
                    else (
                        "重新整理"
                        if publication_state
                        in {
                            lr.PUBLICATION_STATE_RECOVERABLE_FAILED,
                            lr.PUBLICATION_STATE_BLOCKED,
                        }
                        else None
                    )
                )
                if action is not None and action not in actions:
                    actions.append(action)
            return result
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            try:
                entry.close()
            finally:
                write_permit.release()

def register_run_detail_route(router: APIRouter, context: RunRouteContext) -> None:
    root = context.root
    resolve_project = context.resolve_project
    authorize = context.authorize
    mutable_project_error = context.mutable_project_error
    _read_json_object = context.read_json_object
    acquire_product_write_gate = context.acquire_product_write_gate
    _open_entry = context.open_entry
    _auto_scopes = context.auto_scopes
    open_launch_registry = context.open_launch_registry
    progress_adapter = context.progress_adapter
    resolve_launch_inputs = context.resolve_launch_inputs
    open_legacy_view = context.open_legacy_view
    _publication_overlay = context.publication_overlay
    _workspace_dir = context.workspace_dir
    _workspace_is_ready = context.workspace_is_ready
    MonitoringAction = context.monitoring_action

    @router.get("/runs/{run_id}")
    async def get_run(project_id: str, run_id: str, request: Request) -> Any:
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
        if (
            not isinstance(run_id, str)
            or not run_id.strip()
            or run_id != run_id.strip()
        ):
            return _error_response(
                422, "invalid_run_id", chinese_message_for("invalid_run_id")
            )
        view = open_legacy_view(canonical)
        if view is not None:
            try:
                rows = [
                    row
                    for row in view.list_run_bindings()
                    if row.get("run_id") == run_id
                ]
                if not rows:
                    return _error_response(
                        404,
                        "run_binding_not_found",
                        chinese_message_for("run_binding_not_found"),
                    )
                return _legacy_binding_projection(rows[0])
            except Exception as exc:
                return _run_entry_error_response(exc)
            finally:
                view.close()
        compatibility_error = mutable_project_error(canonical)
        if compatibility_error is not None:
            return compatibility_error
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=False)
        if isinstance(entry, JSONResponse):
            return entry
        try:
            binding = entry.get_run(run_id)
            if str(binding.get("project_id", "")) != canonical:
                return _error_response(
                    404,
                    "run_binding_not_found",
                    chinese_message_for("run_binding_not_found"),
                )
            return _projection(binding)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()


__all__ = [
    "RunRouteContext",
    "register_run_launch_routes",
    "register_execution_routes",
    "register_run_detail_route",
]
