"""Project lifecycle, backup, restore and bootstrap routes for R7."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..run_entry import chinese_message_for
from ...runtime import project_backup as pb
from ...runtime.migration import MigrationError, MigrationRunner, TERMINAL_STATES
from ...runtime.project_lifecycle import (
    ProjectCompatibilityError,
    open_project_result,
    upgrade_progress_from_operation,
    upgrade_result_from_state,
)
from ...runtime.project_verifier import (
    ProjectVerificationDTO,
    ProjectVerificationError,
    RecoveryCoordinationError,
    RESULT_RECOVERY_REQUIRED,
)
from .backup_projections import (
    _public_backup_projection,
    _public_preflight_projection,
    _public_restore_projection,
)
from .contracts import (
    ProductBackupRequest,
    ProductBootstrapRequest,
    ProductProjectUpgradeRequest,
    ProductRestorePreflightRequest,
    ProductRestoreRequest,
)
from .errors import (
    _error_response,
    _run_entry_error_response,
    _validation_error_response,
)
from .public_text import _projection


@dataclass(frozen=True)
class ProjectRouteContext:
    root: Path
    backup_runtime_root: Path
    maintenance_wait_seconds: float
    resolve_project: Any
    authorize: Any
    blocked_project_open_projection: Any
    open_project_inspection: Any
    verification_projection: Any
    read_json_object: Any
    begin_product_boundary: Any
    boundary_verification_result: Any
    classify_product_recovery: Any
    finish_product_boundary: Any
    operation_key: Any
    operation_projection_for: Any
    migration_projection: Any
    migration_records: Any
    migration_record: Any
    reserve_operation: Any
    start_backup_worker: Any
    operation_record: Any
    backup_source: Any
    requested_operation_id: Any
    restore_should_start: Any
    start_restore_worker: Any
    acquire_product_write_gate: Any
    mutable_project_error: Any
    open_entry: Any
    workspace_dir: Any
    backup_terminal: Any
    monitoring_action: Any


def register_project_routes(router: APIRouter, context: ProjectRouteContext) -> None:
    root = context.root
    backup_runtime_root = context.backup_runtime_root
    maintenance_wait_seconds = context.maintenance_wait_seconds
    resolve_project = context.resolve_project
    authorize = context.authorize
    blocked_project_open_projection = context.blocked_project_open_projection
    open_project_inspection = context.open_project_inspection
    verification_projection = context.verification_projection
    _read_json_object = context.read_json_object
    begin_product_boundary = context.begin_product_boundary
    boundary_verification_result = context.boundary_verification_result
    classify_product_recovery = context.classify_product_recovery
    finish_product_boundary = context.finish_product_boundary
    operation_key = context.operation_key
    operation_projection_for = context.operation_projection_for
    migration_projection = context.migration_projection
    migration_records = context.migration_records
    migration_record = context.migration_record
    reserve_operation = context.reserve_operation
    start_backup_worker = context.start_backup_worker
    operation_record = context.operation_record
    backup_source = context.backup_source
    requested_operation_id = context.requested_operation_id
    restore_should_start = context.restore_should_start
    start_restore_worker = context.start_restore_worker
    acquire_product_write_gate = context.acquire_product_write_gate
    mutable_project_error = context.mutable_project_error
    _open_entry = context.open_entry
    _workspace_dir = context.workspace_dir
    _PRODUCT_BACKUP_TERMINAL = context.backup_terminal
    MonitoringAction = context.monitoring_action

    @router.get("/project/open")
    async def open_project(project_id: str, request: Request) -> Any:
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
        try:
            inspection = open_project_inspection(canonical)
            return open_project_result(inspection).as_dict()
        except (MigrationError, ProjectCompatibilityError):
            return blocked_project_open_projection()
        except Exception:
            return blocked_project_open_projection()

    @router.api_route("/project/audit/verify", methods=["GET", "POST"])
    async def verify_project_audit(project_id: str, request: Request) -> Any:
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
        try:
            return verification_projection(canonical, request, auth)
        except (
            ProjectVerificationError,
            RecoveryCoordinationError,
        ):
            return ProjectVerificationDTO(
                RESULT_RECOVERY_REQUIRED,
                "暂时无法完成项目核验，请保留当前项目并联系支持。",
                "保留当前项目并联系支持",
            ).as_dict()
        except Exception:
            return ProjectVerificationDTO(
                RESULT_RECOVERY_REQUIRED,
                "暂时无法完成项目核验，请保留当前项目并联系支持。",
                "保留当前项目并联系支持",
            ).as_dict()

    @router.post("/project/upgrade")
    async def start_project_upgrade(
        project_id: str,
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
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductProjectUpgradeRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        runner = MigrationRunner(
            backup_runtime_root,
            canonical,
            project_dir=_workspace_dir(root, canonical),
            wait_seconds=maintenance_wait_seconds,
        )
        receipt: Any = None
        try:
            key = operation_key(request, parsed.idempotency_key, "migration")
            receipt = begin_product_boundary(
                canonical,
                key,
                operation_kind="migration",
                expected_state="requested",
                request=request,
                principal=auth,
            )
            result = runner.start_upgrade(
                key,
                confirmation=parsed.confirmation,
            )
            finish_product_boundary(
                canonical,
                receipt,
                observed_durable_phase=result.state,
                request=request,
                principal=auth,
                operation_update=(
                    operation_projection_for(result.operation)
                    if (
                        result.operation is not None
                        and result.operation.operation_id == receipt.operation_id
                    )
                    else None
                ),
            )
            verification_result = boundary_verification_result(
                canonical,
                receipt,
            )
            finish_product_boundary(
                canonical,
                receipt,
                observed_durable_phase=result.state,
                request=request,
                principal=auth,
                verification_result=verification_result,
                commit=False,
            )
            return upgrade_result_from_state(result.state).as_dict()
        except (MigrationError, ProjectCompatibilityError) as exc:
            if receipt is not None:
                try:
                    classify_product_recovery(
                        canonical,
                        receipt.operation_id,
                        operation_kind="migration",
                        observed_durable_phase="requested",
                        classification="需重新恢复",
                        request=request,
                        principal=auth,
                    )
                except Exception:
                    pass
            return _run_entry_error_response(exc)
        except Exception as exc:
            if receipt is not None:
                try:
                    classify_product_recovery(
                        canonical,
                        receipt.operation_id,
                        operation_kind="migration",
                        observed_durable_phase="requested",
                        classification="需重新恢复",
                        request=request,
                        principal=auth,
                    )
                except Exception:
                    pass
            return _run_entry_error_response(exc)
        finally:
            runner.close()

    @router.get("/project/upgrade")
    async def get_latest_project_upgrade(
        project_id: str,
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
        try:
            records = migration_records(canonical)
            if not records:
                raise MigrationError("migration_operation_not_found")
            return migration_projection(records[-1])
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.get("/project/upgrade/{operation_id}/progress")
    async def get_project_upgrade_progress(
        project_id: str,
        operation_id: str,
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
        try:
            record = migration_record(canonical, operation_id)
            if record.status in TERMINAL_STATES:
                return upgrade_result_from_state(record.status).as_dict()
            return upgrade_progress_from_operation(record).as_dict()
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.get("/project/upgrade/{operation_id}")
    async def get_project_upgrade(
        project_id: str,
        operation_id: str,
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
        try:
            return migration_projection(migration_record(canonical, operation_id))
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.post("/backups")
    async def create_backup(project_id: str, request: Request) -> Any:
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
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductBackupRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            key = operation_key(request, parsed.idempotency_key, "backup")
            record = reserve_operation(
                pb.OP_BACKUP,
                canonical,
                key,
            )
            if record.status not in _PRODUCT_BACKUP_TERMINAL:
                receipt = begin_product_boundary(
                    canonical,
                    record.operation_id,
                    operation_kind=pb.OP_BACKUP,
                    expected_state=record.status,
                    request=request,
                    principal=auth,
                )
                start_backup_worker(
                    canonical,
                    record.operation_id,
                    key,
                    boundary_receipt=receipt,
                    request=request,
                    principal=auth,
                )
            return _public_backup_projection(record, canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.get("/backups/{operation_id}")
    async def get_backup(
        project_id: str,
        operation_id: str,
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
        try:
            record = operation_record(canonical, operation_id, pb.OP_BACKUP)
            return _public_backup_projection(record, canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.post("/restores/preflight")
    async def restore_preflight(project_id: str, request: Request) -> Any:
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
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductRestorePreflightRequest.model_validate(body)
            source_id = requested_operation_id(
                parsed.backup_operation_id, parsed.operation_id
            )
        except ValidationError as exc:
            return _validation_error_response(exc)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        if source_id is None:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        manager: Optional[pb.ProjectBackupManager] = None
        try:
            _, package_path = backup_source(canonical, source_id)
            manager = pb.ProjectBackupManager(backup_runtime_root, canonical)
            result = manager.preflight(
                package_path,
                operation_key(request, parsed.idempotency_key, "preflight"),
            )
            return _public_preflight_projection(result, source_id)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            if manager is not None:
                manager.ledger.close()

    @router.post("/restores")
    async def restore_project(project_id: str, request: Request) -> Any:
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
        body = await _read_json_object(request)
        if isinstance(body, JSONResponse):
            return body
        try:
            parsed = ProductRestoreRequest.model_validate(body)
            source_id = requested_operation_id(
                parsed.backup_operation_id, parsed.operation_id
            )
            preflight_id = parsed.preflight_operation_id
        except ValidationError as exc:
            return _validation_error_response(exc)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        if source_id is None:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        try:
            source_record, package_path = backup_source(canonical, source_id)
            if preflight_id is not None:
                preflight_record = operation_record(
                    canonical, preflight_id, pb.OP_PREFLIGHT
                )
                if (
                    preflight_record.status
                    != pb.STATUS_READY_FOR_CONFIRMATION
                    or preflight_record.package_id != source_record.package_id
                ):
                    raise pb.ProjectBackupError("backup_operation_conflict")
            key = operation_key(request, parsed.idempotency_key, "restore")
            record = reserve_operation(
                pb.OP_RESTORE,
                canonical,
                key,
                package_id=source_record.package_id,
                initial_status=pb.STATUS_CONFIRMED,
            )
            if restore_should_start(record, parsed.confirmation):
                receipt = begin_product_boundary(
                    canonical,
                    record.operation_id,
                    operation_kind=pb.OP_RESTORE,
                    expected_state=record.status,
                    request=request,
                    principal=auth,
                )
                start_restore_worker(
                    canonical,
                    record.operation_id,
                    key,
                    package_path,
                    preflight_id,
                    parsed.confirmation,
                    boundary_receipt=receipt,
                    request=request,
                    principal=auth,
                )
            return _public_restore_projection(record, canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.get("/restores/{operation_id}")
    async def get_restore(
        project_id: str,
        operation_id: str,
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
        try:
            record = operation_record(canonical, operation_id, pb.OP_RESTORE)
            return _public_restore_projection(record, canonical)
        except Exception as exc:
            return _run_entry_error_response(exc)

    @router.post("/workspace/bootstrap")
    async def bootstrap(project_id: str, request: Request) -> Any:
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
            ProductBootstrapRequest.model_validate(body)
        except ValidationError as exc:
            return _validation_error_response(exc)
        try:
            write_permit = acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        workspace = _workspace_dir(root, canonical)
        entry = _open_entry(workspace, allow_create=True)
        if isinstance(entry, JSONResponse):
            write_permit.release()
            return entry
        try:
            result = entry.bootstrap_workspace()
            return _projection(result, replayed=True)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            entry.close()
            write_permit.release()


__all__ = ["ProjectRouteContext", "register_project_routes"]
