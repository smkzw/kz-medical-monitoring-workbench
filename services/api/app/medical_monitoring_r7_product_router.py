"""Project-scoped R7 product mount adapter (Slice-07C-1/2/4).

Thin FastAPI adapters over the frozen ``mm_r7`` run-entry, run-setup and
launch-registry contracts. Import and router construction perform no R7
directory / SQLite / schema / seed writes. Existing runtime routes resolve the
project and authorize first, then open a per-project ``MonitoringRunEntry``
and close it in ``finally``. Setup and product-launch routes use deterministic
synthetic inputs and lazily open project-scoped registries after the same
workspace check.

Product errors are local top-level ``{code, message}`` Chinese envelopes.
This module never registers app-wide exception handlers and never mounts the
isolated ``/api/medical-monitoring/r7`` prefix.
"""

from __future__ import annotations

from datetime import date
import hashlib
import json
import re
import shutil
import threading
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence, Union

from fastapi import APIRouter, Request
from pydantic import ValidationError
from fastapi.responses import JSONResponse

from packages.medical_monitoring.runtime import profile_store as ps
from packages.medical_monitoring.api.run_entry import (
    ProfileFieldsRequest,
    chinese_message_for,
)
from packages.medical_monitoring.runtime.run_entry import (
    PROFILE_DB_NAME,
    RUN_BINDING_DB_NAME,
    MonitoringRunEntry,
    RunEntryError,
)
from packages.medical_monitoring.runtime.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
    RuntimeProgressAdapter,
    RuntimeProgressError,
    validate_public_data_cutoff,
)

from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.runtime import run_setup as rs
from packages.medical_monitoring.runtime import project_backup as pb
from packages.medical_monitoring.runtime.maintenance_gate import (
    DEFAULT_WAIT_SECONDS,
    MaintenanceGateError,
    ProjectMaintenanceGate,
)
from packages.medical_monitoring.runtime import launch_registry as lr
from packages.medical_monitoring.runtime.migration import (
    MigrationError,
    MigrationOperationLedger,
    MigrationRunner,
    TERMINAL_STATES,
)
from packages.medical_monitoring.runtime.project_lifecycle import (
    DATA_COVERAGE_COMPLETE,
    DATA_COVERAGE_INCOMPLETE,
    OPEN_MODE_BLOCKED,
    OPEN_MODE_EDIT,
    OPEN_MODE_READONLY,
    ProjectCompatibilityError,
    ProjectOpenDTO,
    ReadOnlyProjectView,
    inspect_project_schema,
    open_project_result,
    open_read_only_project_view,
    require_current_project,
    upgrade_progress_from_operation,
    upgrade_result_from_state,
)
from packages.medical_monitoring.runtime.schema_manifest import (
    SchemaClassification,
    inspect_member,
)
from packages.medical_monitoring.runtime.project_verifier import (
    ProjectVerificationDTO,
    ProjectVerificationError,
    RecoveryCoordinationError,
    RecoveryCoordinator,
    ProjectVerifier,
    RESULT_RECORD_COMPLETE,
    RESULT_RECOVERY_REQUIRED,
)
from packages.medical_monitoring.projections.product_adapter import (
    R5ProductAdapter,
    R5ProductAdapterError,
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


R7_PRODUCT_PREFIX = "/api/projects/{project_id}/modules/medical-monitoring/r7"
R7_PRODUCT_SCHEMA = "mm-r7-product-mount-v1"
R7_RISK_RULE_DB_NAME = "risk_rules.sqlite3"
#
# These are the only product write workflows intentionally reachable while a
# supported legacy project is read-only. Every ordinary project mutation calls
# ``mutable_project_error`` and remains blocked until an upgrade/reopen.
LEGACY_WORKFLOW_WRITE_ROUTES = frozenset(
    {
        "/project/upgrade",
        "/backups",
        "/restores/preflight",
        "/restores",
    }
)
_PRODUCT_BACKUP_WORKERS: dict[tuple[str, str, str, str], threading.Thread] = {}
_PRODUCT_BACKUP_WORKERS_LOCK = threading.RLock()
_PRODUCT_BACKUP_TERMINAL = frozenset({pb.STATUS_AVAILABLE, pb.STATUS_FAILED})
_PRODUCT_RESTORE_TERMINAL = frozenset(
    {
        pb.STATUS_COMPLETED,
        pb.STATUS_ALREADY_CURRENT,
        pb.STATUS_RETAINED_FOR_TRIAGE,
    }
)

_LAYER_KINDS = frozenset(ps.LAYER_KINDS)

class _BlockedLegacyView:
    """Non-readable sentinel used when legacy semantic checks fail."""

    def close(self) -> None:
        return None

    def __getattr__(self, _name: str) -> Any:
        raise ProjectCompatibilityError("project_open_blocked")




from packages.medical_monitoring.api.r7_product.contracts import (
    ProductPublicationError,
    _StrictModel,
    ProductBackupRequest,
    ProductRestorePreflightRequest,
    ProductRestoreRequest,
    ProductProjectUpgradeRequest,
    ProjectOpenResult,
    ProjectUpgradeProgress,
    ProjectUpgradeResult,
    ProductBootstrapRequest,
    ProductCreateRunRequest,
    ProductPrepareExecutionRequest,
    ProductExecutionActionRequest,
    ProductRiskRulePreviewRequest,
    ProductRiskRuleRequest,
    ProductPrepareAndStartRequest,
    ProductPublicationRequest,
)


from packages.medical_monitoring.api.r7_product.public_text import (
    _SECRET_FIELDS,
    _FORBIDDEN_PUBLIC,
    _SECRET_VALUE,
    _RUNTIME_INTERNAL_TOKENS,
    _public_continuity_text,
    _projection,
)
from packages.medical_monitoring.api.r7_product.result_projections import (
    _PUBLICATION_MESSAGES,
    _launch_projection,
    _publication_status_text,
    _publication_projection,
    _PUBLIC_RESULT_LOCATOR_KEYS,
    _PUBLIC_RESULT_FORBIDDEN_KEYS,
    _public_result_projection,
)
from packages.medical_monitoring.api.r7_product.errors import (
    _NOT_FOUND,
    _CONFLICT,
    _BACKUP_NOT_FOUND,
    _BACKUP_CONFLICT,
    _BACKUP_INTERNAL,
    _EXECUTION_STATE_CONFLICT,
    _AUTH_MESSAGES,
    _RUNTIME_MESSAGES,
    _status_for,
    _error_response,
    _run_entry_error_response,
    _launch_error_response,
    _validation_error_response,
)
from packages.medical_monitoring.api.r7_product.continuity_contracts import (
    _normalize_severity_zh,
    _validate_continuity_risk_semantics,
    _continuity_row_sort_key,
    _CONTINUITY_RISK_CHANGE_KINDS_ZH,
    _CONTINUITY_DISPOSITIONS_ZH,
    _CONTINUITY_DATA_CHANGE_KINDS_ZH,
    _CONTINUITY_ATTENTION_TEXTS,
    _CONTINUITY_SEVERITIES,
    _CONTINUITY_OBJECT_TYPES_ZH,
    _SEVERITY_TEXT_MAP,
    _SEVERITY_RANK,
    ProductContinuityChangeCounts,
    ProductContinuityRow,
    ProductContinuityComparison,
    ProductContinuityIdentity,
    ProductContinuityResponse,
)











from packages.medical_monitoring.api.r7_product.backup_projections import (
    _BACKUP_STATUS_LABEL,
    _BACKUP_STEP_LABEL,
    _BACKUP_IMPACT_LABEL,
    _backup_payload_manifest,
    _backup_progress,
    _backup_text,
    _backup_scope_summary,
    _public_backup_projection,
    _public_impact_items,
    _public_preflight_projection,
    _public_restore_projection,
)
from packages.medical_monitoring.api.r7_product.legacy_projections import (
    _legacy_profile_projection,
    _legacy_binding_projection,
    _legacy_launch_record,
    _legacy_risk_projection,
    _legacy_progress_projection,
    _execution_action_projection,
    _safe_setup_projection,
    _setup_projection,
    _runtime_work_units,
)
from packages.medical_monitoring.api.r7_product.public_result_requests import (
    _reject_public_result_body,
    _parse_public_result_query,
    _canonical_public_result_value,
    _parse_public_result_date,
    _comparison_range_text,
)
from packages.medical_monitoring.api.r7_product.runtime_manifest import (
    _publication_manifest_identity,
    _runtime_manifest_digest,
    _runtime_manifest_metadata,
    _runtime_audit_chain_is_invalid,
)
from packages.medical_monitoring.api.r7_product.publication_providers import (
    _r5_publication_types,
    _call_publication_method,
    _publication_provider_value,
    _publication_product_factory,
    _r6_publication_types,
    _call_r6_provider_method,
    _obtain_r6_mode_outputs,
    _validate_r5_publication_packet,
)
from packages.medical_monitoring.api.r7_product.setup_routes import (
    SetupRouteContext,
    register_setup_routes,
)
from packages.medical_monitoring.api.r7_product.run_routes import (
    RunRouteContext,
    register_run_launch_routes,
    register_execution_routes,
    register_run_detail_route,
)
from packages.medical_monitoring.api.r7_product.publication_routes import (
    PublicationRouteContext,
    register_publication_routes,
    register_public_result_routes,
)
from packages.medical_monitoring.api.r7_product.project_routes import (
    ProjectRouteContext,
    register_project_routes,
)
from packages.medical_monitoring.api.r7_product.publication_services import (
    build_r5_publication_packet as _build_r5_publication_packet_impl,
    read_publication_gate as _read_publication_gate_impl,
)
from packages.medical_monitoring.api.r7_product.route_utils import (
    R7_WORKSPACE_ROOT_NAME,
    _request_id,
    _workspace_dir,
    _workspace_is_ready,
)
from packages.medical_monitoring.api.r7_product.synthetic_setup import (
    synthetic_setup_inputs as _synthetic_setup_inputs_impl,
)





def _build_r5_publication_packet(
    provider: Any,
    identity: Any,
    *,
    attempts: Sequence[Mapping[str, Any]],
    bridge: Any = None,
    product_packet_factory: Optional[Callable[[Any], Any]] = None,
) -> Any:
    return _build_r5_publication_packet_impl(
        provider,
        identity,
        attempts=attempts,
        bridge=bridge,
        product_packet_factory=product_packet_factory,
    )


def _read_publication_gate(
    workspace: Path,
    run_id: str,
    *,
    entry: MonitoringRunEntry,
    harness_r1_profile: Any,
) -> dict[str, Any]:
    return _read_publication_gate_impl(
        workspace,
        run_id,
        entry=entry,
        harness_r1_profile=harness_r1_profile,
    )

def _synthetic_setup_inputs(
    canonical_project_id: str,
) -> tuple[tuple[rs.DataSnapshot, ...], tuple[rs.PublishedBaseline, ...]]:
    return _synthetic_setup_inputs_impl(canonical_project_id)

def create_medical_monitoring_r7_product_router(
    *,
    runtime_dir: Union[str, Path],
    project_resolver: Callable[[str], str] = lambda project_id: project_id,
    principal_resolver: Optional[
        Callable[[Request], MonitoringAuthenticatedPrincipal | None]
    ] = None,
    require_server_principal: bool = True,
    maintenance_wait_seconds: float = DEFAULT_WAIT_SECONDS,
    harness_runtime_factory: Optional[Callable[..., Any]] = None,
    harness_adapter: Any = None,
    harness_catalog: Any = None,
    harness_r1_profile: Any = None,
    authority_provider: Any = None,
    r5_authority_provider: Any = None,
    publication_authority_provider: Any = None,
    r5_publication_provider: Any = None,
    r5_authority_bridge: Any = None,
    publication_authority_bridge: Any = None,
    r5_product_packet_factory: Optional[Callable[[Any], Any]] = None,
    r6_output_provider: Any = None,
    r6_publication_provider: Any = None,
    mode_output_provider: Any = None,
    r6_mode_output_provider: Any = None,
    continuity_bridge: Any = None,
    audit_ledger_factory: Optional[Callable[..., Any]] = None,
) -> APIRouter:
    """Create the project-scoped R7 product router; no workspace I/O here."""
    # Publication never synthesizes authority.  A caller must inject one
    # explicit R5 publication provider (or the already constructed bridge
    # input); the aliases preserve naming compatibility with R5 routes.
    publication_provider = next(
        (
            value
            for value in (
                publication_authority_provider,
                r5_publication_provider,
                r5_authority_provider,
                authority_provider,
            )
            if value is not None
        ),
        None,
    )
    publication_bridge = next(
        (
            value
            for value in (r5_authority_bridge, publication_authority_bridge)
            if value is not None
        ),
        None,
    )
    r6_provider = next(
        (
            value
            for value in (
                r6_output_provider,
                r6_publication_provider,
                mode_output_provider,
                r6_mode_output_provider,
            )
            if value is not None
        ),
        None,
    )

    root = Path(runtime_dir)
    router = APIRouter(prefix=R7_PRODUCT_PREFIX, tags=["medical-monitoring-r7-product"])
    risk_registries: dict[str, rs.RiskRuleRegistry] = {}
    risk_registry_lock = threading.RLock()
    backup_runtime_root = root / R7_WORKSPACE_ROOT_NAME

    @router.on_event("startup")
    def recover_r7_projects_on_startup() -> None:
        """Cold-scan canonical projects through the shared 09C coordinator."""

        try:
            project_dirs = sorted(
                path
                for path in backup_runtime_root.iterdir()
                if path.is_dir()
                and not path.is_symlink()
                and not path.name.startswith(".")
            )
        except (FileNotFoundError, OSError):
            return
        for workspace in project_dirs:
            try:
                coordinator = RecoveryCoordinator(
                    backup_runtime_root,
                    workspace.name,
                    project_dir=workspace,
                    wait_seconds=maintenance_wait_seconds,
                    audit_ledger_factory=audit_ledger_factory,
                )
                try:
                    coordinator.startup_recovery_scan()
                finally:
                    coordinator.close()
            except Exception:
                # The durable state remains available to project-open or the
                # explicit same-key path; one project cannot block startup.
                continue

    def acquire_product_write_gate(canonical_project_id: str):
        try:
            gate = ProjectMaintenanceGate(
                backup_runtime_root,
                canonical_project_id,
                wait_seconds=maintenance_wait_seconds,
            )
            return gate.acquire(exclusive=False)
        except MaintenanceGateError as exc:
            raise pb.ProjectBackupError(exc.code, exc.message) from exc

    def close_cached_risk_registry(canonical_project_id: str) -> None:
        registry: Optional[rs.RiskRuleRegistry]
        with risk_registry_lock:
            registry = risk_registries.pop(canonical_project_id, None)
            if registry is not None:
                registry.close()

    def operation_record(
        canonical_project_id: str,
        operation_id: str,
        expected_kind: str,
    ) -> pb.OperationRecord:
        if (
            not isinstance(operation_id, str)
            or re.fullmatch(r"[A-Za-z0-9_-]+", operation_id) is None
        ):
            raise pb.ProjectBackupError("operation_not_found")
        ledger_path = backup_runtime_root / pb.OPERATIONS_DB_NAME
        if not ledger_path.is_file():
            raise pb.ProjectBackupError("operation_not_found")
        ledger: Optional[pb.OperationLedger] = None
        try:
            ledger = pb.OperationLedger(ledger_path)
            record = ledger.get(operation_id)
        finally:
            if ledger is not None:
                ledger.close()
        if (
            record.canonical_project_id != canonical_project_id
            or record.operation_kind != expected_kind
        ):
            raise pb.ProjectBackupError("operation_not_found")
        return record

    def backup_source(
        canonical_project_id: str,
        operation_id: str,
    ) -> tuple[pb.OperationRecord, Path]:
        record = operation_record(
            canonical_project_id, operation_id, pb.OP_BACKUP
        )
        package_name = record.package_path
        if not package_name:
            raise pb.ProjectBackupError("operation_not_found")
        package_root = (
            backup_runtime_root / pb.BACKUP_PUBLICATION_DIR_NAME
        ).resolve()
        package_path = Path(package_name)
        if (
            not package_path.is_absolute()
            or package_path.is_symlink()
            or package_path.suffix != pb.BACKUP_SUFFIX
        ):
            raise pb.ProjectBackupError("operation_not_found")
        try:
            package_path = package_path.resolve()
            package_path.relative_to(package_root)
        except (OSError, ValueError):
            raise pb.ProjectBackupError("operation_not_found")
        if not package_path.is_file():
            raise pb.ProjectBackupError("operation_not_found")
        return record, package_path

    def requested_operation_id(
        backup_operation_id: Optional[str],
        operation_id: Optional[str],
    ) -> Optional[str]:
        if (
            backup_operation_id is not None
            and operation_id is not None
            and backup_operation_id != operation_id
        ):
            raise pb.ProjectBackupError("backup_operation_conflict")
        return backup_operation_id or operation_id

    def operation_key(
        request: Request,
        supplied: Optional[str],
        prefix: str,
    ) -> str:
        header = str(request.headers.get("X-Idempotency-Key", "") or "").strip()
        return supplied or header or f"{prefix}-{_request_id(request)}"

    def reserve_operation(
        operation_kind: str,
        canonical_project_id: str,
        idempotency_key: str,
        *,
        package_id: Optional[str] = None,
        initial_status: Optional[str] = None,
    ) -> pb.OperationRecord:
        ledger: Optional[pb.OperationLedger] = None
        try:
            ledger = pb.OperationLedger(
                backup_runtime_root / pb.OPERATIONS_DB_NAME
            )
            return ledger.create_or_replay(
                operation_kind,
                idempotency_key,
                canonical_project_id,
                package_id=package_id,
                initial_status=initial_status,
            )
        finally:
            if ledger is not None:
                ledger.close()

    def product_worker_key(
        operation_kind: str,
        canonical_project_id: str,
        operation_id: str,
    ) -> tuple[str, str, str, str]:
        return (
            str(backup_runtime_root.resolve()),
            canonical_project_id,
            operation_kind,
            operation_id,
        )

    def start_worker_once(
        operation_kind: str,
        canonical_project_id: str,
        operation_id: str,
        target: Callable[[], None],
    ) -> None:
        worker_key = product_worker_key(
            operation_kind, canonical_project_id, operation_id
        )

        def run_and_forget() -> None:
            try:
                target()
            finally:
                with _PRODUCT_BACKUP_WORKERS_LOCK:
                    if (
                        _PRODUCT_BACKUP_WORKERS.get(worker_key)
                        is threading.current_thread()
                    ):
                        _PRODUCT_BACKUP_WORKERS.pop(worker_key, None)

        with _PRODUCT_BACKUP_WORKERS_LOCK:
            existing = _PRODUCT_BACKUP_WORKERS.get(worker_key)
            if existing is not None and existing.is_alive():
                return
            worker = threading.Thread(
                target=run_and_forget,
                name=f"r7-{operation_kind}-{operation_id[:12]}",
                daemon=True,
            )
            _PRODUCT_BACKUP_WORKERS[worker_key] = worker
            try:
                worker.start()
            except BaseException:
                if _PRODUCT_BACKUP_WORKERS.get(worker_key) is worker:
                    _PRODUCT_BACKUP_WORKERS.pop(worker_key, None)
                raise

    def mark_worker_failed(
        operation_id: str,
        exc: Exception,
        *,
        canonical_project_id: Optional[str] = None,
        operation_kind: Optional[str] = None,
        boundary_receipt: Any = None,
        request: Optional[Request] = None,
        principal: Any = None,
    ) -> None:
        ledger: Optional[pb.OperationLedger] = None
        should_classify = False
        observed_phase = pb.STATUS_FAILED
        try:
            ledger = pb.OperationLedger(
                backup_runtime_root / pb.OPERATIONS_DB_NAME
            )
            record = ledger.get(operation_id)
            terminal = (
                _PRODUCT_BACKUP_TERMINAL
                | _PRODUCT_RESTORE_TERMINAL
                | {pb.STATUS_KEPT_CURRENT}
            )
            if record.status in terminal:
                # A late verifier/callback failure must still leave an
                # auditable recovery classification; terminal status alone
                # does not close the boundary.
                observed_phase = record.status
                should_classify = boundary_receipt is not None
            else:
                failure = (
                    exc
                    if isinstance(exc, pb.ProjectBackupError)
                    else pb.ProjectBackupError("sqlite_integrity_failed")
                )
                ledger.update(
                    operation_id,
                    status=pb.STATUS_FAILED,
                    current_step="操作未完成",
                    terminal_outcome=pb.STATUS_FAILED,
                    error_code=failure.code,
                    error_message=failure.message,
                )
                should_classify = boundary_receipt is not None
        except Exception:
            pass
        finally:
            if ledger is not None:
                ledger.close()
        if should_classify:
            try:
                classify_product_recovery(
                    canonical_project_id or "",
                    operation_id,
                    operation_kind=operation_kind or "",
                    observed_durable_phase=observed_phase,
                    classification="需重新恢复",
                    request=request,
                    principal=principal,
                )
            except Exception:
                pass

    def start_backup_worker(
        canonical_project_id: str,
        operation_id: str,
        idempotency_key: str,
        *,
        boundary_receipt: Any = None,
        request: Optional[Request] = None,
        principal: Any = None,
    ) -> None:
        def run() -> None:
            manager: Optional[pb.ProjectBackupManager] = None
            try:
                manager = pb.ProjectBackupManager(
                    backup_runtime_root,
                    canonical_project_id,
                    wait_seconds=maintenance_wait_seconds,
                )
                manager.backup(
                    idempotency_key,
                    reserved_operation_id=operation_id,
                )
                if boundary_receipt is not None and request is not None:
                    manager.ledger.close()
                    manager = None
                    final_record = operation_record(
                        canonical_project_id,
                        operation_id,
                        pb.OP_BACKUP,
                    )
                    finish_product_boundary(
                        canonical_project_id,
                        boundary_receipt,
                        observed_durable_phase=final_record.status,
                        request=request,
                        principal=principal,
                        operation_update=operation_projection_for(final_record),
                    )
                    verification_result = boundary_verification_result(
                        canonical_project_id,
                        boundary_receipt,
                    )
                    finish_product_boundary(
                        canonical_project_id,
                        boundary_receipt,
                        observed_durable_phase=final_record.status,
                        request=request,
                        principal=principal,
                        verification_result=verification_result,
                        commit=False,
                    )
            except Exception as exc:
                mark_worker_failed(
                    operation_id,
                    exc,
                    canonical_project_id=canonical_project_id,
                    operation_kind=pb.OP_BACKUP,
                    boundary_receipt=boundary_receipt,
                    request=request,
                    principal=principal,
                )
            finally:
                if manager is not None:
                    manager.ledger.close()

        start_worker_once(
            pb.OP_BACKUP,
            canonical_project_id,
            operation_id,
            run,
        )

    def start_restore_worker(
        canonical_project_id: str,
        operation_id: str,
        idempotency_key: str,
        package_path: Path,
        preflight_id: Optional[str],
        confirmation: bool,
        *,
        boundary_receipt: Any = None,
        request: Optional[Request] = None,
        principal: Any = None,
    ) -> None:
        def run() -> None:
            manager: Optional[pb.ProjectBackupManager] = None
            try:
                manager = pb.ProjectBackupManager(
                    backup_runtime_root,
                    canonical_project_id,
                    wait_seconds=maintenance_wait_seconds,
                )
                preflight_result: Optional[pb.PreflightResult] = None
                if preflight_id is not None:
                    preflight_record = operation_record(
                        canonical_project_id,
                        preflight_id,
                        pb.OP_PREFLIGHT,
                    )
                    if (
                        preflight_record.status
                        != pb.STATUS_READY_FOR_CONFIRMATION
                    ):
                        raise pb.ProjectBackupError(
                            "backup_operation_conflict"
                        )
                    preflight_result = manager.preflight(
                        package_path,
                        preflight_record.idempotency_key,
                    )
                close_cached_risk_registry(canonical_project_id)
                manager.restore(
                    package_path,
                    idempotency_key,
                    confirmation=confirmation,
                    preflight_result=preflight_result,
                    reserved_operation_id=operation_id,
                )
                if boundary_receipt is not None and request is not None:
                    manager.ledger.close()
                    manager = None
                    final_record = operation_record(
                        canonical_project_id,
                        operation_id,
                        pb.OP_RESTORE,
                    )
                    finish_product_boundary(
                        canonical_project_id,
                        boundary_receipt,
                        observed_durable_phase=final_record.status,
                        request=request,
                        principal=principal,
                        operation_update=operation_projection_for(final_record),
                    )
                    verification_result = boundary_verification_result(
                        canonical_project_id,
                        boundary_receipt,
                    )
                    verified_event = finish_product_boundary(
                        canonical_project_id,
                        boundary_receipt,
                        observed_durable_phase=final_record.status,
                        request=request,
                        principal=principal,
                        verification_result=verification_result,
                        commit=False,
                    )
                    release_product_rollback(
                        canonical_project_id,
                        boundary_receipt,
                        final_record,
                        verified_event=verified_event,
                        verification_result=verification_result,
                    )
            except Exception as exc:
                mark_worker_failed(
                    operation_id,
                    exc,
                    canonical_project_id=canonical_project_id,
                    operation_kind=pb.OP_RESTORE,
                    boundary_receipt=boundary_receipt,
                    request=request,
                    principal=principal,
                )
            finally:
                if manager is not None:
                    manager.ledger.close()

        start_worker_once(
            pb.OP_RESTORE,
            canonical_project_id,
            operation_id,
            run,
        )

    def restore_should_start(
        record: pb.OperationRecord,
        confirmation: bool,
    ) -> bool:
        if record.status in _PRODUCT_RESTORE_TERMINAL:
            return False
        if record.status == pb.STATUS_KEPT_CURRENT:
            return bool(confirmation)
        if record.status == pb.STATUS_FAILED:
            return record.error_code == "project_busy_retry_later"
        return True


    def setup_registry(
        canonical_project_id: str,
    ) -> Union[rs.RiskRuleRegistry, JSONResponse]:
        workspace = _workspace_dir(root, canonical_project_id)
        if not _workspace_is_ready(workspace):
            return _error_response(
                422,
                "global_default_missing",
                _AUTH_MESSAGES["workspace_not_ready"],
            )
        with risk_registry_lock:
            registry = risk_registries.get(canonical_project_id)
        if registry is not None:
            return registry
        try:
            write_permit = acquire_product_write_gate(canonical_project_id)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            with risk_registry_lock:
                registry = risk_registries.get(canonical_project_id)
                if registry is None:
                    registry = rs.RiskRuleRegistry(
                        workspace / R7_RISK_RULE_DB_NAME
                    )
                    risk_registries[canonical_project_id] = registry
                return registry
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            write_permit.release()

    def setup_catalog(
        canonical_project_id: str,
    ) -> Union[rs.RunSetupCatalog, JSONResponse]:
        registry = setup_registry(canonical_project_id)
        if isinstance(registry, JSONResponse):
            return registry
        snapshots, baselines = _synthetic_setup_inputs(canonical_project_id)
        return rs.RunSetupCatalog(
            project_id=canonical_project_id,
            snapshots=snapshots,
            published_baselines=baselines,
            risk_rule_registry=registry,
        )

    def open_launch_registry(
        canonical_project_id: str,
    ) -> Union[lr.LaunchRegistry, JSONResponse]:
        workspace = _workspace_dir(root, canonical_project_id)
        if not _workspace_is_ready(workspace):
            return _error_response(
                422,
                "global_default_missing",
                _AUTH_MESSAGES["workspace_not_ready"],
            )
        try:
            write_permit = acquire_product_write_gate(canonical_project_id)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            return lr.LaunchRegistry(
                workspace / lr.LAUNCH_REGISTRY_DB_NAME,
                project_id=canonical_project_id,
            )
        except Exception as exc:
            return _launch_error_response(exc)
        finally:
            write_permit.release()

    def resolve_launch_inputs(
        canonical_project_id: str,
        parsed: ProductPrepareAndStartRequest,
    ) -> Union[
        tuple[
            rs.DataSnapshot,
            Optional[rs.PublishedBaseline],
            tuple[rs.RiskRuleRevision, ...],
            rs.WorkUnitManifest,
        ],
        JSONResponse,
    ]:
        catalog = setup_catalog(canonical_project_id)
        if isinstance(catalog, JSONResponse):
            return catalog
        current = catalog.snapshot_for_token(
            canonical_project_id,
            parsed.current_snapshot_token,
        )
        if parsed.current_snapshot_token != current.snapshot_token:
            raise rs.RunSetupError("invalid_snapshot")

        baseline: Optional[rs.PublishedBaseline] = None
        if parsed.baseline_token is not None:
            if parsed.mode == rs.MODE_DAILY and parsed.execution_basis == rs.BASIS_FULL:
                raise rs.RunSetupError("invalid_baseline")
            if parsed.mode == rs.MODE_POST_LOCK_PRE_CFDI:
                raise rs.RunSetupError("invalid_baseline")
            baseline = catalog.baseline_for_token(
                canonical_project_id,
                parsed.mode,
                parsed.baseline_token,
            )
            if parsed.baseline_token != baseline.baseline_token:
                raise rs.RunSetupError("invalid_baseline")
        elif (
            parsed.mode == rs.MODE_DAILY
            and parsed.execution_basis == rs.BASIS_INCREMENTAL
        ):
            raise rs.RunSetupError("baseline_not_published")

        revisions: list[rs.RiskRuleRevision] = []
        for token in sorted(set(parsed.risk_rule_tokens)):
            revision = catalog.risk_rule_registry.resolve_public_token(
                canonical_project_id,
                token,
            )
            if not revision.selectable:
                raise rs.RunSetupError("invalid_rule_revision")
            revisions.append(revision)

        diff: Optional[rs.CanonicalKeyedDiff] = None
        if baseline is not None:
            key_fields = current.key_fields or baseline.key_fields or None
            diff = rs.canonical_keyed_diff(
                current.rows,
                baseline.rows,
                key_fields=key_fields,
            )
        manifest = rs.generate_work_units(
            parsed.mode,
            parsed.execution_basis,
            current_snapshot_token=parsed.current_snapshot_token,
            prior_baseline_token=parsed.baseline_token,
            diff=diff,
            rule_revisions=revisions,
        )
        return current, baseline, tuple(revisions), manifest

    def progress_adapter(
        workspace: Path, entry: MonitoringRunEntry, canonical_id: str
    ) -> RuntimeProgressAdapter:
        return RuntimeProgressAdapter(
            workspace,
            binding_store=entry.run_binding_store,
            canonical_project_id=canonical_id,
            harness_runtime_factory=harness_runtime_factory,
            harness_adapter=harness_adapter,
            harness_catalog=harness_catalog,
            harness_r1_profile=harness_r1_profile,
        )

    def resolve_project(project_id: str) -> Union[str, JSONResponse]:
        text = str(project_id or "")
        if not text.strip() or text != text.strip():
            return _error_response(
                404, "project_not_found", _AUTH_MESSAGES["project_not_found"]
            )
        try:
            canonical = project_resolver(text)
        except Exception:
            return _error_response(
                404, "project_not_found", _AUTH_MESSAGES["project_not_found"]
            )
        cleaned = str(canonical or "").strip()
        if not cleaned or cleaned != str(canonical):
            return _error_response(
                404, "project_not_found", _AUTH_MESSAGES["project_not_found"]
            )
        if "/" in cleaned or "\\" in cleaned or ".." in cleaned:
            return _error_response(
                404, "project_not_found", _AUTH_MESSAGES["project_not_found"]
            )
        return cleaned

    def mutable_project_error(
        canonical_project_id: str,
        *,
        allow_uninitialized: bool = False,
    ) -> Optional[JSONResponse]:
        """Reject legacy/unknown projects before any mutable constructor."""
        workspace = _workspace_dir(root, canonical_project_id)
        runtime_path = workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        guarded_paths = runtime_path.exists()
        member_paths = (
            (workspace / PROFILE_DB_NAME, "profile_store"),
            (workspace / RUN_BINDING_DB_NAME, "run_binding"),
            (workspace / lr.LAUNCH_REGISTRY_DB_NAME, "launch_registry"),
            (workspace / R7_RISK_RULE_DB_NAME, "risk_rules"),
        )
        if not guarded_paths:
            for path, member in member_paths:
                if not path.exists():
                    continue
                report = inspect_member(path, member)
                if report.classification is not SchemaClassification.CURRENT:
                    code = (
                        "project_read_only"
                        if report.classification is SchemaClassification.LEGACY
                        else "project_open_blocked"
                    )
                    compatibility = ProjectCompatibilityError(code)
                    return _error_response(
                        _status_for(code),
                        code,
                        compatibility.message,
                    )
        if not workspace.exists() or not guarded_paths:
            # A missing runtime is the normal pre-bootstrap state: the
            # mutable entry may establish profile/binding stores explicitly.
            return None
        try:
            require_current_project(workspace)
        except ProjectCompatibilityError as exc:
            return _error_response(_status_for(exc.code), exc.code, exc.message)
        return None

    def open_project_inspection(
        canonical_project_id: str,
    ) -> Any:
        """Inspect first, then share 09A/09B recovery coordination."""
        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
        )
        try:
            return coordinator.open_project()
        finally:
            coordinator.close()

    def verification_context_hashes(
        canonical_project_id: str,
        request: Request,
        principal: Any,
        *,
        action: MonitoringAction = MonitoringAction.READ_AI_RUN,
    ) -> tuple[str, str]:
        principal_hash = str(getattr(principal, "identity_hash", "") or "")
        # The authorization decision is a stable policy projection.  Request
        # ids identify transport attempts, not a different authorization
        # decision; excluding them preserves same-key boundary replay.
        decision = {
            "action": action.value,
            "project_id": canonical_project_id,
        }
        decision_hash = hashlib.sha256(
            json.dumps(
                decision,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        return principal_hash, decision_hash

    def verification_projection(
        canonical_project_id: str,
        request: Request,
        principal: Any,
    ) -> dict[str, str]:
        principal_hash, decision_hash = verification_context_hashes(
            canonical_project_id,
            request,
            principal,
        )
        verifier = ProjectVerifier(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=principal_hash,
            authorization_decision_hash=decision_hash,
        )
        try:
            return verifier.verify().as_public_dict()
        finally:
            verifier.close()

    def operation_projection_for(record: Any) -> dict[str, Any]:
        """Select only mutable root-operation fields for atomic audit append."""

        fields: dict[str, Any] = {}
        for name in (
            "status",
            "progress_percent",
            "current_step",
            "package_id",
            "source_workspace_fingerprint",
            "terminal_outcome",
            "error_code",
            "error_message",
            "rollback_path",
            "staging_path",
            "package_path",
            "maintenance_state",
        ):
            if hasattr(record, name):
                fields[name] = getattr(record, name)
        if hasattr(record, "payload"):
            payload = getattr(record, "payload")
            if isinstance(payload, Mapping):
                fields["payload"] = dict(payload)
        return fields


    def begin_product_boundary(
        canonical_project_id: str,
        operation_ref: str,
        *,
        operation_kind: str,
        expected_state: str,
        request: Request,
        principal: Any,
    ) -> Any:
        principal_hash, decision_hash = verification_context_hashes(
            canonical_project_id,
            request,
            principal,
            action=MonitoringAction.ADMINISTER_RUNTIME,
        )
        snapshot = ProjectVerifier(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
        )
        try:
            before_digest = snapshot.snapshot_fingerprint()
        finally:
            snapshot.close()
        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=principal_hash,
            authorization_decision_hash=decision_hash,
        )
        try:
            boundary_token = hashlib.sha256(
                f"r7-boundary:{operation_kind}:{operation_ref}:{expected_state}".encode("utf-8")
            ).hexdigest()
            return coordinator.begin_boundary(
                operation_ref,
                operation_kind=operation_kind,
                expected_state=expected_state,
                before_digest=before_digest,
                boundary_token=boundary_token,
            )
        finally:
            coordinator.close()

    def finish_product_boundary(
        canonical_project_id: str,
        receipt: Any,
        *,
        observed_durable_phase: str,
        request: Request,
        principal: Any,
        verification_result: Optional[str] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
        commit: bool = True,
    ) -> Any:
        receipt_principal_hash = str(
            getattr(receipt, "principal_snapshot_hash", "") or ""
        )
        receipt_decision_hash = str(
            getattr(receipt, "authorization_decision_hash", "") or ""
        )
        if receipt_principal_hash and receipt_decision_hash:
            principal_hash, decision_hash = (
                receipt_principal_hash,
                receipt_decision_hash,
            )
        else:
            principal_hash, decision_hash = verification_context_hashes(
                canonical_project_id,
                request,
                principal,
                action=MonitoringAction.ADMINISTER_RUNTIME,
            )
        snapshot = ProjectVerifier(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
        )
        try:
            after_digest = snapshot.snapshot_fingerprint()
        finally:
            snapshot.close()
        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=principal_hash,
            authorization_decision_hash=decision_hash,
        )
        verified_event: Any = None
        try:
            if commit:
                coordinator.mark_committed(
                    receipt,
                    observed_durable_phase=observed_durable_phase,
                    after_digest=after_digest,
                    operation_update=operation_update,
                )
            if verification_result is not None:
                verified_event = coordinator.mark_verified(
                    receipt,
                    verifier_outcome=verification_result,
                    after_digest=after_digest,
                )
        finally:
            coordinator.close()
        return verified_event

    def boundary_verification_result(
        canonical_project_id: str,
        receipt: Any,
    ) -> str:
        verifier = ProjectVerifier(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=str(
                getattr(receipt, "principal_snapshot_hash", "") or ""
            ),
            authorization_decision_hash=str(
                getattr(receipt, "authorization_decision_hash", "") or ""
            ),
        )
        try:
            return verifier.verify().result
        finally:
            verifier.close()

    def rollback_evidence_digest(path: Path) -> str:
        digest = hashlib.sha256()
        if path.is_symlink() or not path.is_dir():
            raise OSError("rollback_evidence_unreadable")
        for entry in sorted(
            path.rglob("*"),
            key=lambda candidate: candidate.relative_to(path).as_posix(),
        ):
            relative = entry.relative_to(path).as_posix().encode("utf-8")
            if entry.is_symlink():
                digest.update(b"symlink\0" + relative)
            elif entry.is_dir():
                digest.update(b"directory\0" + relative)
            elif entry.is_file():
                digest.update(b"file\0" + relative + b"\0")
                with entry.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
            else:
                raise OSError("rollback_evidence_unreadable")
        return digest.hexdigest()

    def release_product_rollback(
        canonical_project_id: str,
        receipt: Any,
        final_record: Any,
        *,
        verified_event: Any,
        verification_result: str,
    ) -> bool:
        if verification_result != RESULT_RECORD_COMPLETE:
            return False
        rollback_raw = getattr(final_record, "rollback_path", None)
        if not rollback_raw:
            return False
        rollback_path = Path(str(rollback_raw))
        if not rollback_path.is_absolute():
            rollback_path = backup_runtime_root / rollback_path
        runtime_root_resolved = backup_runtime_root.resolve()
        try:
            rollback_path.resolve().relative_to(runtime_root_resolved)
            rollback_in_scope = True
        except (OSError, ValueError):
            rollback_in_scope = False
        if rollback_in_scope:
            try:
                rollback_digest = rollback_evidence_digest(rollback_path)
            except OSError:
                rollback_digest = hashlib.sha256(
                    ("unreadable:" + str(rollback_raw)).encode("utf-8")
                ).hexdigest()
        else:
            rollback_digest = hashlib.sha256(
                ("out-of-scope:" + str(rollback_raw)).encode("utf-8")
            ).hexdigest()
        event_id = (
            verified_event.get("event_id")
            if isinstance(verified_event, Mapping)
            else getattr(verified_event, "event_id", None)
        )
        if not event_id:
            raise ProjectVerificationError("boundary_verified_event_missing")

        def remove_rollback() -> None:
            resolved = rollback_path.resolve()
            resolved.relative_to(runtime_root_resolved)
            if rollback_path.is_symlink() or not rollback_path.is_dir():
                raise OSError("rollback_evidence_unreadable")
            shutil.rmtree(rollback_path)

        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=str(
                getattr(receipt, "principal_snapshot_hash", "") or ""
            ),
            authorization_decision_hash=str(
                getattr(receipt, "authorization_decision_hash", "") or ""
            ),
        )
        try:
            return coordinator.release_rollback_evidence(
                receipt.operation_id,
                verified_event_id=str(event_id),
                rollback_digest=rollback_digest,
                release=remove_rollback,
                operation_kind=str(getattr(receipt, "operation_kind", "") or ""),
                operation_update={"rollback_path": ""},
            )
        finally:
            coordinator.close()

    def classify_product_recovery(
        canonical_project_id: str,
        operation_ref: str,
        *,
        operation_kind: str,
        observed_durable_phase: str,
        classification: str,
        request: Optional[Request] = None,
        principal: Any = None,
    ) -> None:
        principal_hash = ""
        decision_hash = ""
        if request is not None:
            principal_hash, decision_hash = verification_context_hashes(
                canonical_project_id,
                request,
                principal,
                action=MonitoringAction.ADMINISTER_RUNTIME,
            )
        coordinator = RecoveryCoordinator(
            backup_runtime_root,
            canonical_project_id,
            project_dir=_workspace_dir(root, canonical_project_id),
            wait_seconds=maintenance_wait_seconds,
            audit_ledger_factory=audit_ledger_factory,
            principal_snapshot_hash=principal_hash,
            authorization_decision_hash=decision_hash,
        )
        try:
            coordinator.classify_recovery(
                operation_ref,
                operation_kind=operation_kind,
                observed_durable_phase=observed_durable_phase,
                classification=classification,
            )
        finally:
            coordinator.close()

    def migration_records(
        canonical_project_id: str,
    ) -> tuple[Any, ...]:
        ledger_path = backup_runtime_root / pb.OPERATIONS_DB_NAME
        if not ledger_path.is_file():
            raise MigrationError("migration_operation_not_found")
        ledger: Optional[MigrationOperationLedger] = None
        try:
            ledger = MigrationOperationLedger(ledger_path, initialize=False)
            return tuple(ledger.list_for_project(canonical_project_id))
        finally:
            if ledger is not None:
                ledger.close()

    def migration_record(
        canonical_project_id: str,
        operation_id: str,
    ) -> Any:
        if (
            not isinstance(operation_id, str)
            or re.fullmatch(r"[A-Za-z0-9_-]+", operation_id) is None
        ):
            raise MigrationError("migration_operation_not_found")
        for record in migration_records(canonical_project_id):
            if record.operation_id == operation_id:
                return record
        raise MigrationError("migration_operation_not_found")

    def migration_projection(record: Any) -> dict[str, Any]:
        if record.status in TERMINAL_STATES:
            return upgrade_result_from_state(record.status).as_dict()
        return upgrade_progress_from_operation(record).as_dict()

    def blocked_project_open_projection() -> dict[str, Any]:
        return ProjectOpenDTO(
            state="blocked",
            open_mode=OPEN_MODE_BLOCKED,
            data_coverage=DATA_COVERAGE_INCOMPLETE,
            can_view=False,
            can_edit=False,
            message="暂时无法安全打开此项目，请保留原项目并联系支持。",
            next_action="关闭项目或联系支持",
        ).as_dict()

    def open_legacy_view(
        canonical_project_id: str,
    ) -> Optional[Union[ReadOnlyProjectView, _BlockedLegacyView]]:
        """Return the only readable handle permitted for a legacy project."""
        workspace = _workspace_dir(root, canonical_project_id)
        inspection = inspect_project_schema(workspace)
        if inspection.classification is not SchemaClassification.LEGACY:
            return None
        runner = MigrationRunner(
            backup_runtime_root,
            canonical_project_id,
            project_dir=workspace,
            wait_seconds=maintenance_wait_seconds,
        )
        try:
            # Read routes must apply the same cross-member completeness oracle
            # as project-open; structural legacy status alone is insufficient.
            runner._ensure_complete_legacy(inspection)
        except MigrationError:
            return _BlockedLegacyView()
        finally:
            runner.close()
        try:
            return open_read_only_project_view(workspace, inspection=inspection)
        except ProjectCompatibilityError:
            return _BlockedLegacyView()

    def legacy_setup_projection(
        canonical_project_id: str,
    ) -> Optional[dict[str, Any]]:
        """Build setup options without creating a legacy risk database."""
        view = open_legacy_view(canonical_project_id)
        if view is None:
            return None
        try:
            rules = [
                _legacy_risk_projection(row)
                for row in view.list_risk_rules()
            ]
        finally:
            view.close()
        snapshots, baselines = _synthetic_setup_inputs(canonical_project_id)
        memory_registry = rs.RiskRuleRegistry()
        catalog = rs.RunSetupCatalog(
            project_id=canonical_project_id,
            snapshots=snapshots,
            published_baselines=baselines,
            risk_rule_registry=memory_registry,
        )
        try:
            options = catalog.get_options(canonical_project_id)
            body = options.public_projection()
        finally:
            catalog.close()
        body["rule_revisions"] = rules
        return _setup_projection(body)


    def authorize(
        request: Request,
        *,
        project_id: str,
        action: MonitoringAction,
    ) -> Union[MonitoringAuthenticatedPrincipal, None, JSONResponse]:
        if not require_server_principal:
            # Explicit offline TestClient harness only; production host keeps True.
            return None
        if principal_resolver is None:
            return _error_response(
                503,
                "principal_unavailable",
                _AUTH_MESSAGES["principal_unavailable"],
            )
        try:
            principal = principal_resolver(request)
        except Exception:
            return _error_response(
                503,
                "principal_unavailable",
                _AUTH_MESSAGES["principal_unavailable"],
            )
        if not isinstance(principal, MonitoringAuthenticatedPrincipal):
            return _error_response(
                503,
                "principal_required",
                _AUTH_MESSAGES["principal_required"],
            )
        try:
            route_context = build_monitoring_runtime_route_context(
                principal,
                request_id=_request_id(request),
                route_project_id=project_id,
                tenant_id=principal.tenant_id,
                target_scope="trial",
                action=action,
            )
            decision = authorize_monitoring_action(
                route_context.principal.to_monitoring_principal(
                    now=route_context.validated_at,
                ),
                route_context.request,
            )
        except MonitoringRuntimePrincipalDenied:
            return _error_response(
                403, "principal_denied", _AUTH_MESSAGES["principal_denied"]
            )
        except (MonitoringRuntimeRouteContextError, ValueError):
            return _error_response(
                403,
                "authorization_invalid",
                _AUTH_MESSAGES["authorization_invalid"],
            )
        if not decision.allowed:
            return _error_response(
                403, "not_permitted", _AUTH_MESSAGES["not_permitted"]
            )
        return principal

    async def _read_json_object(request: Request) -> Union[dict[str, Any], JSONResponse]:
        raw = await request.body()
        if not raw:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        if payload is None:
            return {}
        if not isinstance(payload, dict):
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        return payload

    def _validated_layer_scope(
        *,
        layer_kind: str,
        scope_key: str,
        canonical_project_id: str,
    ) -> Union[str, JSONResponse]:
        if layer_kind not in _LAYER_KINDS:
            return _error_response(
                422,
                "request_validation_failed",
                chinese_message_for("request_validation_failed"),
            )
        if (
            not isinstance(scope_key, str)
            or not scope_key.strip()
            or scope_key != scope_key.strip()
        ):
            return _error_response(
                422,
                "empty_or_illegal_scope_key",
                chinese_message_for("empty_or_illegal_scope_key"),
            )
        if layer_kind == ps.LAYER_GLOBAL_DEFAULT and scope_key != ps.GLOBAL_SCOPE_KEY:
            return _error_response(
                422,
                "empty_or_illegal_scope_key",
                chinese_message_for("empty_or_illegal_scope_key"),
            )
        if layer_kind == ps.LAYER_PROJECT:
            resolved_scope = resolve_project(scope_key)
            if (
                isinstance(resolved_scope, JSONResponse)
                or resolved_scope != canonical_project_id
            ):
                return _error_response(
                    422,
                    "empty_or_illegal_scope_key",
                    chinese_message_for("empty_or_illegal_scope_key"),
                )
            return canonical_project_id
        return scope_key

    def _auto_scopes(
        entry: MonitoringRunEntry,
        *,
        canonical_project_id: str,
        run_id: str,
        capability_scope_key: str,
    ) -> dict[str, str]:
        project_scope = ""
        if (
            entry.profile_store.latest_revision(ps.LAYER_PROJECT, canonical_project_id)
            is not None
        ):
            project_scope = canonical_project_id
        run_scope = ""
        if entry.profile_store.latest_revision(ps.LAYER_RUN_OVERRIDE, run_id) is not None:
            run_scope = run_id
        return {
            "capability_scope_key": capability_scope_key or "",
            "project_scope_key": project_scope,
            "run_override_scope_key": run_scope,
        }

    def _open_entry(
        workspace: Path,
        *,
        allow_create: bool,
    ) -> Union[MonitoringRunEntry, JSONResponse]:
        if not allow_create and not _workspace_is_ready(workspace):
            return _error_response(
                422,
                "global_default_missing",
                _AUTH_MESSAGES["workspace_not_ready"],
            )
        try:
            write_permit = acquire_product_write_gate(workspace.name)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            return MonitoringRunEntry(workspace)
        except RunEntryError as exc:
            return _run_entry_error_response(exc)
        except Exception as exc:
            return _run_entry_error_response(exc)
        finally:
            write_permit.release()

    def _publication_overlay(
        canonical_project_id: str,
        run_id: str,
        base: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Overlay registry publication state without changing R1 progress."""

        public_token = lr.derive_public_run_token(
            canonical_project_id, run_id
        )
        state = "not_started"
        has_launch = False
        launch_path = (
            _workspace_dir(root, canonical_project_id)
            / lr.LAUNCH_REGISTRY_DB_NAME
        )
        registry: Optional[lr.LaunchRegistry] = None
        try:
            if launch_path.is_file():
                registry = lr.LaunchRegistry(
                    launch_path, project_id=canonical_project_id
                )
                launch = registry.get(run_id, project_id=canonical_project_id)
                has_launch = True
                try:
                    publication = registry.get_publication(
                        project_id=canonical_project_id,
                        run_id=run_id,
                    )
                    state = publication.publication_state
                except lr.LaunchRegistryError as exc:
                    if exc.code != "publication_not_found":
                        raise
                    state = "not_started"
                public_token = launch.public_run_token
            return {
                **dict(base),
                "publication_state": state,
                "result_available": state == lr.PUBLICATION_STATE_AVAILABLE,
                "publication_status_text": _publication_status_text(
                    state, run_state=str(base.get("run_state", ""))
                ),
                "_publication_has_launch": has_launch,
                "_publication_public_token": public_token,
            }
        except lr.LaunchRegistryError as exc:
            if exc.code in {"run_not_found", "public_run_not_found"}:
                return {
                    **dict(base),
                    "publication_state": "not_started",
                    "result_available": False,
                    "publication_status_text": _publication_status_text(
                        "not_started",
                        run_state=str(base.get("run_state", "")),
                    ),
                    "_publication_has_launch": False,
                    "_publication_public_token": public_token,
                }
            raise
        except Exception:
            # A corrupt/temporarily unreadable publication row must not hide
            # the authoritative R1 progress or expose a false result link.
            return {
                **dict(base),
                "publication_state": lr.PUBLICATION_STATE_RECOVERABLE_FAILED,
                "result_available": False,
                "publication_status_text": _PUBLICATION_MESSAGES[
                    "publication_recoverable_failed"
                ],
                "_publication_has_launch": has_launch,
                "_publication_public_token": public_token,
            }
        finally:
            if registry is not None:
                registry.close()

    def _publication_setup_inputs(
        canonical_project_id: str,
        launch: lr.LaunchRecord,
    ) -> tuple[rs.DataSnapshot, rs.WorkUnitManifest, tuple[str, ...], dict[str, Any], str]:
        parsed = ProductPrepareAndStartRequest(
            current_snapshot_token=launch.current_snapshot_token,
            mode=launch.mode,
            execution_basis=launch.execution_basis,
            baseline_token=launch.baseline_token,
            risk_rule_tokens=list(launch.rule_tokens),
            idempotency_key=launch.idempotency_key,
        )
        resolved = resolve_launch_inputs(canonical_project_id, parsed)
        if isinstance(resolved, JSONResponse):
            raise ProductPublicationError("manifest_identity_mismatch")
        current, _, _, manifest = resolved
        setup_identity = _publication_manifest_identity(manifest)
        setup_digest = manifest.manifest_digest
        if (
            launch.manifest_digest is not None
            and launch.manifest_digest != setup_digest
        ):
            raise ProductPublicationError("manifest_identity_mismatch")
        coverage = tuple(
            sorted(
                {
                    str(row["site_ref"])
                    for row in current.rows
                    if isinstance(row, Mapping)
                    and isinstance(row.get("site_ref"), str)
                    and row.get("site_ref")
                }
            )
        )
        if not coverage:
            raise ProductPublicationError("authority_identity_mismatch")
        return current, manifest, coverage, setup_identity, setup_digest


    def _record_publication_failure(
        registry: lr.LaunchRegistry,
        publication: lr.ResultPublication,
        *,
        code: str,
        recoverable: bool,
    ) -> lr.ResultPublication:
        target = (
            lr.PUBLICATION_STATE_RECOVERABLE_FAILED
            if recoverable
            else lr.PUBLICATION_STATE_BLOCKED
        )
        message = _PUBLICATION_MESSAGES.get(
            code,
            _PUBLICATION_MESSAGES[
                "runtime_read_failed" if recoverable else "publication_blocked"
            ],
        )
        try:
            return registry.record_publication_failure(
                project_id=publication.project_id,
                run_id=publication.run_id,
                revision=publication.publication_revision,
                target_state=target,
                expected_state=publication.publication_state,
                error_code=code,
                error_message=message,
            )
        except lr.LaunchRegistryError:
            # A concurrent retry may have advanced the row.  Re-read it rather
            # than exposing a false local state to the caller.
            return registry.get_publication(
                project_id=publication.project_id,
                run_id=publication.run_id,
                revision=publication.publication_revision,
            )


    def _publication_failure_response(
        publication: lr.ResultPublication,
    ) -> JSONResponse:
        if publication.publication_state == lr.PUBLICATION_STATE_AVAILABLE:
            return _publication_projection(
                publication.public_run_token,
                publication.publication_state,
                replayed=True,
            )
        if publication.publication_state == lr.PUBLICATION_STATE_RECOVERABLE_FAILED:
            return _error_response(
                500,
                "publication_recoverable_failed",
                _PUBLICATION_MESSAGES["publication_recoverable_failed"],
            )
        if publication.publication_state == lr.PUBLICATION_STATE_BLOCKED:
            return _error_response(
                409,
                "publication_blocked",
                _PUBLICATION_MESSAGES["publication_blocked"],
            )
        return _error_response(
            422,
            "publication_not_available",
            _PUBLICATION_MESSAGES["publication_not_available"],
        )

    def _load_public_result_context(
        canonical_project_id: str,
        result_context_token: str,
        *,
        site_ref: Optional[str] = None,
        require_product_adapter: bool = True,
        continuity_context: bool = False,
    ) -> tuple[
        lr.LaunchRegistry,
        MonitoringRunEntry,
        lr.LaunchRecord,
        lr.ResultPublication,
        Optional[R5ProductAdapter],
    ]:
        """Resolve one persisted context and rebuild the accepted R5 view."""
        legacy_view = open_legacy_view(canonical_project_id)
        if legacy_view is not None:
            # Legacy result data is readable only through the bounded facade;
            # this R5 adapter requires mutable current-schema stores.
            legacy_view.close()
            raise ProductPublicationError("result_context_unavailable")
        registry = open_launch_registry(canonical_project_id)
        if isinstance(registry, JSONResponse):
            raise ProductPublicationError("result_context_unavailable")
        entry: Optional[MonitoringRunEntry] = None
        try:
            try:
                publication = registry.get_publication_by_result_context_token(
                    result_context_token,
                    project_id=canonical_project_id,
                )
            except lr.LaunchRegistryError as exc:
                raise ProductPublicationError(
                    "result_context_unavailable"
                ) from exc
            if (
                publication.publication_state
                != lr.PUBLICATION_STATE_AVAILABLE
                or publication.result_context_token != result_context_token
            ):
                raise ProductPublicationError("result_context_unavailable")
            try:
                launch = registry.get_by_public_token(
                    publication.public_run_token,
                    project_id=canonical_project_id,
                )
            except lr.LaunchRegistryError as exc:
                raise ProductPublicationError(
                    "result_context_unavailable"
                ) from exc
            if (
                launch.run_id != publication.run_id
                or launch.public_run_token != publication.public_run_token
                or launch.run_state != lr.STATE_COMPLETED
                or not launch.result_available
            ):
                raise ProductPublicationError("result_context_unavailable")

            (
                current,
                _setup_manifest,
                coverage,
                setup_identity,
                setup_digest,
            ) = _publication_setup_inputs(canonical_project_id, launch)
            current_source_revision = (
                current.source_revision_id or current.snapshot_ref
            )
            if (
                site_ref is not None
                and site_ref not in publication.site_coverage
            ):
                raise ProductPublicationError("result_center_out_of_scope")
            if (
                launch.current_snapshot_token != publication.snapshot_token
                or current.snapshot_token != publication.snapshot_token
                or current.snapshot_ref != publication.snapshot_ref
                or current.data_cutoff != publication.data_cutoff
                or current_source_revision != publication.source_revision_id
                or tuple(coverage) != tuple(publication.site_coverage)
                or setup_digest != publication.setup_manifest_digest
                or setup_identity != dict(publication.setup_manifest_identity)
            ):
                raise ProductPublicationError("result_context_unavailable")

            entry_candidate = _open_entry(
                _workspace_dir(root, canonical_project_id),
                allow_create=False,
            )
            if isinstance(entry_candidate, JSONResponse):
                raise ProductPublicationError("result_context_unavailable")
            entry = entry_candidate
            gate = _read_publication_gate(
                _workspace_dir(root, canonical_project_id),
                launch.run_id,
                entry=entry,
                harness_r1_profile=harness_r1_profile,
            )
            if (
                gate["revision"] != publication.manifest_revision
                or gate["digest"] != publication.manifest_digest
                or gate["identity"]
                != dict(publication.runtime_manifest_identity)
                or tuple(gate["receipt_ids"])
                != tuple(publication.receipt_identities)
                or gate["receipt_set_digest"]
                != publication.receipt_set_digest
            ):
                raise ProductPublicationError("result_context_unavailable")

            (
                _packet_type,
                _bridge_type,
                _bridge_error_type,
                _input_type,
                identity_type,
            ) = _r5_publication_types()
            authority_identity = identity_type(
                project_ref=canonical_project_id,
                run_ref=launch.run_id,
                public_run_token=launch.public_run_token,
                snapshot_ref=publication.snapshot_ref or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
                site_refs=publication.site_coverage,
                snapshot_token=publication.snapshot_token,
            )
            packet = _build_r5_publication_packet(
                publication_provider,
                authority_identity,
                attempts=gate["receipt_attempts"],
                bridge=publication_bridge,
                product_packet_factory=r5_product_packet_factory,
            )
            if (
                packet.packet_identity != publication.r5_authority_packet_id
                or packet.packet_digest != publication.r5_authority_packet_digest
                or tuple(packet.site_refs) != tuple(publication.site_coverage)
            ):
                raise ProductPublicationError("result_context_unavailable")
            if (
                not publication.r6_output_set_digest
                or len(publication.artifact_member_ids) != 4
                or publication.artifact_member_set_digest
                != lr.content_digest(list(publication.artifact_member_ids))
            ):
                raise ProductPublicationError(
                    "continuity_unavailable"
                    if continuity_context
                    else "result_context_unavailable"
                )
            runtime_dir = _workspace_dir(root, canonical_project_id) / RUNTIME_DIR_NAME
            r1_store = Store(
                runtime_dir / RUNTIME_DB_NAME,
                runtime_dir / ARTIFACT_DIR_NAME,
            )
            try:
                if any(
                    not r1_store.verify_artifact(member_id)
                    for member_id in publication.artifact_member_ids
                ):
                    raise ProductPublicationError("result_context_unavailable")
            finally:
                r1_store.close()
            product_packet = getattr(packet, "product_packet", None)
            if product_packet is None:
                raise ProductPublicationError("authority_provider_invalid")
            if (
                getattr(product_packet, "project_ref", canonical_project_id)
                != canonical_project_id
                or getattr(product_packet, "run_ref", launch.run_id)
                != launch.run_id
                or getattr(
                    product_packet,
                    "snapshot_ref",
                    publication.snapshot_ref or publication.snapshot_token,
                )
                != (publication.snapshot_ref or publication.snapshot_token)
                or getattr(product_packet, "cutoff_ref", publication.data_cutoff)
                != publication.data_cutoff
            ):
                raise ProductPublicationError("result_context_unavailable")
            for collection_name, reference_name in (
                    ("sites", "site_ref"),
                    ("subjects", "subject_ref"),
                    ("events", "event_ref"),
                    ("visits", "visit_ref"),
                    ("risks", "risk_ref"),
                    ("sources", "locator_ref"),
            ):
                if not hasattr(packet, collection_name):
                    continue
                bridge_refs = {
                    getattr(item, reference_name, None)
                    for item in getattr(packet, collection_name, ())
                }
                product_refs = {
                    getattr(item, reference_name, None)
                    for item in getattr(product_packet, collection_name, ())
                }
                if bridge_refs != product_refs:
                    raise ProductPublicationError("result_context_unavailable")

            def product_packet_provider(
                project_ref: str,
                run_ref: Optional[str] = None,
                snapshot_ref: Optional[str] = None,
                cutoff_ref: Optional[str] = None,
            ) -> Any:
                if (
                    project_ref != canonical_project_id
                    or run_ref is not None
                    and run_ref != launch.run_id
                    or snapshot_ref is not None
                    and snapshot_ref != (
                        publication.snapshot_ref or publication.snapshot_token
                    )
                    or cutoff_ref is not None
                    and cutoff_ref != publication.data_cutoff
                ):
                    raise R5ProductAdapterError(
                        "AUTHORITY_IDENTITY_MISMATCH"
                    )
                return product_packet

            adapter = R5ProductAdapter(product_packet_provider)
            return (
                registry,
                entry,
                launch,
                publication,
                adapter if require_product_adapter else None,
            )
        except Exception:
            if entry is not None:
                entry.close()
            registry.close()
            raise

    def _public_result_envelope(
        result: Mapping[str, Any],
        *,
        launch: lr.LaunchRecord,
        publication: lr.ResultPublication,
        result_context_token: str,
    ) -> dict[str, Any]:
        raw_identity = result.get("identity")
        if not isinstance(raw_identity, Mapping):
            raise ProductPublicationError("result_context_unavailable")
        projection = _public_result_projection(result.get("projection"))
        if not isinstance(projection, Mapping):
            raise ProductPublicationError("result_context_unavailable")
        identity: dict[str, Any] = {
            "project_ref": launch.project_id,
            "public_run_token": launch.public_run_token,
            "snapshot_token": publication.snapshot_token,
            "data_cutoff_text": publication.data_cutoff,
            "view": str(raw_identity.get("view") or ""),
            "mode_text": launch.mode_text,
            "site_scope_text": "、".join(
                f"中心 {site_ref}" for site_ref in publication.site_coverage
            ),
        }
        for key in _PUBLIC_RESULT_LOCATOR_KEYS:
            value = raw_identity.get(key)
            if value is not None:
                identity[key] = value
        if identity["view"] not in {"overview", "journey", "evidence"}:
            raise ProductPublicationError("result_context_unavailable")
        public_blob = json.dumps(
            {"identity": identity, "projection": projection},
            ensure_ascii=False,
        ).casefold()
        if _SECRET_VALUE.search(public_blob) or any(
            marker in public_blob
            for marker in (
                '"run_id"',
                '"run_ref"',
                '"snapshot_ref"',
                '"cutoff_ref"',
                '"authority_hash"',
                '"authority_receipt',
                '"packet_digest"',
                '"packet_identity"',
                '"s4_',
                '"r5_',
            )
        ):
            raise ProductPublicationError("result_context_unavailable")
        response_digest = lr.content_digest(
            {"identity": identity, "projection": projection}
        )
        return {
            "identity": identity,
            "projection": dict(projection),
            "result_context_token": result_context_token,
            "response_digest": response_digest,
        }

    def _public_result_error(exc: Exception) -> JSONResponse:
        if isinstance(exc, ProductPublicationError) and exc.code == (
            "result_center_out_of_scope"
        ):
            return _error_response(
                409,
                "result_center_out_of_scope",
                _PUBLICATION_MESSAGES["result_center_out_of_scope"],
            )
        if isinstance(exc, ProductPublicationError) and exc.code == (
            "continuity_unavailable"
        ):
            return _error_response(
                409,
                "continuity_unavailable",
                _PUBLICATION_MESSAGES["continuity_unavailable"],
            )
        return _error_response(
            409,
            "result_context_unavailable",
            _PUBLICATION_MESSAGES["result_context_unavailable"],
        )

    def _build_public_continuity_envelope(
        *,
        registry: lr.LaunchRegistry,
        launch: lr.LaunchRecord,
        publication: lr.ResultPublication,
        adapter: R5ProductAdapter,
        result_context_token: str,
        site_ref: Optional[str] = None,
    ) -> dict[str, Any]:
        try:
            plan = registry.get_continuity_plan(
                project_id=launch.project_id, target_run_id=launch.run_id
            )
        except Exception as exc:
            raise ProductPublicationError("continuity_unavailable") from exc

        if (
            plan.status != lr.CONTINUITY_PLAN_STATE_PUBLISHED
            or plan.project_id != launch.project_id
            or plan.target_run_id != launch.run_id
            or plan.mode != launch.mode
            or plan.target_snapshot_id != publication.snapshot_token
            or plan.target_data_cutoff != publication.data_cutoff
            or plan.r5_authority_digest != publication.r5_authority_packet_digest
            or plan.r6_publication_digest != publication.publication_fingerprint
            or plan.r6_receipt_digest != publication.receipt_set_digest
        ):
            raise ProductPublicationError("continuity_unavailable")
        if plan.r6_output_set_digest != publication.r6_output_set_digest:
            raise ProductPublicationError("continuity_unavailable")

        try:
            packet = adapter.get_authority_packet(
                project_ref=launch.project_id,
                run_ref=launch.run_id,
                snapshot_ref=publication.snapshot_ref or publication.snapshot_token,
                cutoff_ref=publication.data_cutoff,
            )
        except Exception as exc:
            raise ProductPublicationError("continuity_unavailable") from exc
        def unique_map(values: Sequence[Any], key_name: str) -> dict[str, Any]:
            mapped: dict[str, Any] = {}
            for value in values:
                key = str(getattr(value, key_name, "") or "").strip()
                if not key or key in mapped:
                    raise ProductPublicationError("continuity_unavailable")
                mapped[key] = value
            return mapped

        site_map = unique_map(packet.sites, "site_ref")
        site_audience_map = unique_map(packet.site_audience, "site_ref")
        if set(site_audience_map) != set(site_map):
            raise ProductPublicationError("continuity_unavailable")
        subject_map = unique_map(packet.subjects, "subject_ref")
        event_map = unique_map(packet.events, "event_ref")
        source_map = unique_map(packet.sources, "locator_ref")
        risk_by_ref = unique_map(packet.risks, "risk_ref")
        risk_by_instance = unique_map(packet.risks, "risk_instance_ref")

        runtime_dir = _workspace_dir(root, launch.project_id) / RUNTIME_DIR_NAME
        artifact_envelopes: dict[str, Any] = {}
        artifact_atoms: dict[tuple[str, str, str], Any] = {}
        r1_store = Store(
            runtime_dir / RUNTIME_DB_NAME,
            runtime_dir / ARTIFACT_DIR_NAME,
        )
        try:
            for member_id in publication.artifact_member_ids:
                envelope = r1_store.get_artifact(member_id)
                if not r1_store.verify_artifact(member_id):
                    raise ProductPublicationError("continuity_unavailable")
                artifact_envelopes[member_id] = envelope
                from packages.medical_monitoring.runtime.continuity_bridge import (
                    extract_atomic_items,
                )

                for atom in extract_atomic_items(
                    [envelope.payload],
                    mode=launch.mode,
                    output_artifact_map={envelope.node_id: envelope.artifact_id},
                ):
                    atom_key = (member_id, atom.object_type, atom.object_id)
                    if atom_key in artifact_atoms:
                        raise ProductPublicationError("continuity_unavailable")
                    artifact_atoms[atom_key] = atom
        except Exception as exc:
            raise ProductPublicationError("continuity_unavailable") from exc
        finally:
            r1_store.close()

        basis_raw = (
            str(plan.execution_basis or launch.execution_basis or "")
            .strip()
            .lower()
        )
        if basis_raw in {"incremental", "增量分析"}:
            basis_text = "增量分析"
        elif basis_raw in {"full", "全量分析", ""}:
            basis_text = "全量分析"
        else:
            raise ProductPublicationError("continuity_unavailable")

        if plan.baseline is None:
            source_run_text = ""
            comparison_text = "本轮为首次全面分析，无比较基线"
        else:
            baseline_cutoff = str(
                plan.baseline.source_data_cutoff or ""
            ).strip()
            if not baseline_cutoff:
                source_run_text = ""
                comparison_text = "本轮为首次全面分析，无比较基线"
            else:
                try:
                    date.fromisoformat(baseline_cutoff)
                except ValueError as exc:
                    raise ProductPublicationError("continuity_unavailable") from exc
                source_run_text = f"{baseline_cutoff} 监查批次"
                comparison_text = "已与上次监查结果比较"

        rows: list[dict[str, Any]] = []
        all_risk_rows: list[dict[str, Any]] = []
        seen_risk_instances: set[str] = set()

        for item in plan.items:
            if item.object_type == "evidence_binding":
                continue
            if item.object_type not in {
                "risk_instance",
                "query_draft",
                "mode_output_item",
            }:
                raise ProductPublicationError("continuity_unavailable")

            if (
                item.artifact_verified is False
                or item.artifact_member_verified is False
                or not item.source_artifact_id
                or item.source_artifact_id not in publication.artifact_member_ids
            ):
                raise ProductPublicationError("continuity_unavailable")
            source_artifact = artifact_envelopes[item.source_artifact_id]
            if (
                not item.source_artifact_sha256
                or item.source_artifact_sha256 != source_artifact.content_hash
                or item.source_run_id
                and item.source_run_id != source_artifact.run_id
                or not item.source_object_id
                or not item.source_identity
                or not item.target_object_id
                or item.target_object_id != item.object_ref
            ):
                raise ProductPublicationError("continuity_unavailable")
            source_atom = artifact_atoms.get(
                (
                    item.source_artifact_id,
                    item.object_type,
                    item.source_object_id,
                )
            )
            if source_atom is None or source_atom.item_digest != item.source_identity:
                raise ProductPublicationError("continuity_unavailable")
            if item.object_type == "risk_instance":
                obj_type = "risk"
                obj_type_text = "风险"
            elif item.object_type == "query_draft":
                obj_type = "query_draft"
                obj_type_text = "Query 草稿"
            else:
                obj_type = "monitoring_output"
                obj_type_text = "监查结果项"

            change_kind = str(getattr(item, "risk_change_kind", None) or getattr(item, "change_kind", None) or "").strip().lower()
            if change_kind not in _CONTINUITY_RISK_CHANGE_KINDS_ZH:
                raise ProductPublicationError("continuity_unavailable")
            if obj_type == "risk":
                _validate_continuity_risk_semantics(item, change_kind)
            change_text = _CONTINUITY_RISK_CHANGE_KINDS_ZH[change_kind]

            disposition = str(item.disposition or "").strip().lower()
            if disposition not in _CONTINUITY_DISPOSITIONS_ZH:
                raise ProductPublicationError("continuity_unavailable")
            disposition_text = _CONTINUITY_DISPOSITIONS_ZH[disposition]

            data_change_kind = str(item.data_change_kind or "").strip().lower()
            if data_change_kind not in _CONTINUITY_DATA_CHANGE_KINDS_ZH:
                raise ProductPublicationError("continuity_unavailable")
            data_change_text = _CONTINUITY_DATA_CHANGE_KINDS_ZH[data_change_kind]

            sev_before_raw = getattr(item, "prior_severity", None)
            sev_after_raw = getattr(item, "current_severity", None)
            sev_before_zh = _normalize_severity_zh(sev_before_raw)
            sev_after_zh = _normalize_severity_zh(sev_after_raw)

            need_severity_attention = False
            if obj_type == "risk" and change_kind == "new":
                if sev_before_zh != "" or sev_after_zh not in {"高", "中", "低"}:
                    need_severity_attention = True
                sev_before_zh = ""
            elif change_kind == "closed":
                if sev_before_zh not in {"高", "中", "低"} or sev_after_zh != "":
                    need_severity_attention = True
                sev_after_zh = ""
            elif change_kind in {"upgraded", "downgraded", "continued"}:
                if (
                    sev_before_zh not in {"高", "中", "低"}
                    or sev_after_zh not in {"高", "中", "低"}
                ):
                    raise ProductPublicationError("continuity_unavailable")
                rank_before = _SEVERITY_RANK[sev_before_zh]
                rank_after = _SEVERITY_RANK[sev_after_zh]
                if change_kind == "upgraded" and not (rank_after > rank_before):
                    raise ProductPublicationError("continuity_unavailable")
                if change_kind == "downgraded" and not (rank_after < rank_before):
                    raise ProductPublicationError("continuity_unavailable")
                if change_kind == "continued" and not (rank_after == rank_before):
                    raise ProductPublicationError("continuity_unavailable")
            elif obj_type == "risk" and change_kind == "reopened":
                if sev_after_zh not in {"高", "中", "低"}:
                    need_severity_attention = True
            elif obj_type == "risk" and change_kind == "needs_rejudgment":
                if sev_after_zh not in {"高", "中", "低"}:
                    need_severity_attention = True

            ev_summary = (
                item.evidence_summary
                if isinstance(item.evidence_summary, Mapping)
                else {}
            )
            risk_ref_hint = str(ev_summary.get("risk_ref") or "").strip()
            risk_instance_hint = str(
                ev_summary.get("risk_instance_ref") or ""
            ).strip()
            matching_risk = (
                risk_by_instance.get(risk_instance_hint)
                or risk_by_ref.get(risk_ref_hint)
                or risk_by_instance.get(item.object_ref)
                or risk_by_ref.get(item.object_ref)
            )
            if obj_type == "risk":
                if matching_risk is None:
                    raise ProductPublicationError("continuity_unavailable")
                if (
                    risk_ref_hint and risk_ref_hint != matching_risk.risk_ref
                    or risk_instance_hint
                    and risk_instance_hint != matching_risk.risk_instance_ref
                ):
                    raise ProductPublicationError("continuity_unavailable")
                event_ref = matching_risk.event_ref or ""
                event = event_map.get(event_ref) if event_ref else None
                if event_ref and event is None:
                    raise ProductPublicationError("continuity_unavailable")
                row_site_ref = matching_risk.site_ref
                row_subject_ref = matching_risk.subject_ref
                row_risk_ref = matching_risk.risk_ref
                row_risk_instance_ref = matching_risk.risk_instance_ref
                row_risk_anchor_ref = matching_risk.risk_anchor_ref
                authoritative_locators = tuple(matching_risk.source_locator_refs)
                if event is not None and (
                    matching_risk.risk_anchor_ref not in event.risk_anchor_refs
                ):
                    raise ProductPublicationError("continuity_unavailable")
                authority_severity_zh = _normalize_severity_zh(matching_risk.severity)
                if not need_severity_attention and (
                    (change_kind == "closed" and sev_before_zh != authority_severity_zh)
                    or (change_kind != "closed" and sev_after_zh != authority_severity_zh)
                ):
                    raise ProductPublicationError("continuity_unavailable")
            else:
                risk_ref_match = risk_by_ref.get(risk_ref_hint) if risk_ref_hint else None
                risk_instance_match = (
                    risk_by_instance.get(risk_instance_hint)
                    if risk_instance_hint
                    else None
                )
                if (
                    risk_ref_hint
                    and risk_ref_match is None
                    or risk_instance_hint
                    and risk_instance_match is None
                    or risk_ref_match is not None
                    and risk_instance_match is not None
                    and risk_ref_match is not risk_instance_match
                ):
                    raise ProductPublicationError("continuity_unavailable")
                event_ref = str(ev_summary.get("event_ref") or "").strip()
                event = event_map.get(event_ref)
                if event is None:
                    raise ProductPublicationError("continuity_unavailable")
                row_site_ref = event.site_ref
                row_subject_ref = event.subject_ref
                row_risk_ref = matching_risk.risk_ref if matching_risk is not None else ""
                row_risk_instance_ref = (
                    matching_risk.risk_instance_ref if matching_risk is not None else ""
                )
                row_risk_anchor_ref = (
                    matching_risk.risk_anchor_ref if matching_risk is not None else ""
                )
                authoritative_locators = tuple(event.source_locator_refs)
                if (
                    matching_risk is not None
                    and (matching_risk.event_ref or "") != event_ref
                ):
                    raise ProductPublicationError("continuity_unavailable")

            subject = subject_map.get(row_subject_ref)
            if (
                subject is None
                or row_site_ref not in site_map
                or subject.site_ref != row_site_ref
                or event is not None
                and (event.subject_ref != row_subject_ref or event.site_ref != row_site_ref)
            ):
                raise ProductPublicationError("continuity_unavailable")
            for hint, expected in (
                (ev_summary.get("site_ref"), row_site_ref),
                (ev_summary.get("subject_ref"), row_subject_ref),
                (ev_summary.get("risk_anchor_ref"), row_risk_anchor_ref),
                (ev_summary.get("event_ref"), event_ref),
            ):
                if hint not in (None, "") and str(hint).strip() != expected:
                    raise ProductPublicationError("continuity_unavailable")

            row_site_label = _public_continuity_text(
                site_audience_map[row_site_ref].site_label
            )
            row_subject_label = _public_continuity_text(subject.subject_label)
            row_title = _public_continuity_text(
                event.label_zh
                if event is not None
                else matching_risk.risk_type_zh
            )
            row_reason_text = _public_continuity_text(item.reason)
            row_date_label = (
                event.start_date.isoformat()
                if event is not None and event.start_date is not None
                else ""
            )
            row_window_start = str(ev_summary.get("window_start") or "").strip()
            row_window_end = str(ev_summary.get("window_end") or "").strip()
            try:
                parsed_window_start = date.fromisoformat(row_window_start)
                parsed_window_end = date.fromisoformat(row_window_end)
            except ValueError as exc:
                raise ProductPublicationError("continuity_unavailable") from exc
            if parsed_window_start > parsed_window_end:
                raise ProductPublicationError("continuity_unavailable")

            row_event_ref = event_ref

            if any(locator not in source_map for locator in authoritative_locators):
                raise ProductPublicationError("continuity_unavailable")
            requested_locator = str(
                ev_summary.get("source_locator_ref") or ""
            ).strip()
            if requested_locator and requested_locator not in authoritative_locators:
                raise ProductPublicationError("continuity_unavailable")
            loc_ref = requested_locator or (
                authoritative_locators[0] if len(authoritative_locators) == 1 else ""
            )
            src_count = len(authoritative_locators) if loc_ref else 0
            raw_source_count = ev_summary.get("source_count")
            if raw_source_count is not None and (
                type(raw_source_count) is not int
                or raw_source_count < 0
                or raw_source_count != src_count
            ):
                raise ProductPublicationError("continuity_unavailable")

            if data_change_kind == "missing":
                attention_text = "未见记录不代表风险已解除"
            elif (
                change_kind == "needs_rejudgment"
                or disposition == "blocked_incompatible"
                or data_change_kind == "cannot_compare"
                or not getattr(item, "identity_compatible", True)
                or not getattr(item, "source_compatible", True)
                or not getattr(item, "output_contract_compatible", True)
                or getattr(item, "identity_ambiguous", False)
                or getattr(item, "lineage_changed", False)
                or getattr(item, "data_missing", False)
            ):
                attention_text = "身份或数据不完整，需重新判断"
            elif need_severity_attention:
                attention_text = "等级变化待确认"
            elif not loc_ref or src_count == 0:
                attention_text = "原始记录位置待确认"
            else:
                attention_text = ""

            if attention_text not in _CONTINUITY_ATTENTION_TEXTS:
                raise ProductPublicationError("continuity_unavailable")

            ordinal = int(item.ordinal)
            if ordinal < 0:
                raise ProductPublicationError("continuity_unavailable")
            row_ref = f"continuity-row-{ordinal}"

            row_dict = {
                "row_ref": row_ref,
                "object_type": obj_type,
                "object_type_text": obj_type_text,
                "ordinal": ordinal,
                "change_kind": change_kind,
                "change_text": change_text,
                "disposition": disposition,
                "disposition_text": disposition_text,
                "data_change_kind": data_change_kind,
                "data_change_text": data_change_text,
                "severity_before_text": sev_before_zh,
                "severity_after_text": sev_after_zh,
                "title": row_title,
                "reason_text": row_reason_text,
                "attention_text": attention_text,
                "site_ref": row_site_ref,
                "site_label": row_site_label,
                "subject_ref": row_subject_ref,
                "subject_label": row_subject_label,
                "date_label": row_date_label,
                "window_start": row_window_start,
                "window_end": row_window_end,
                "risk_ref": row_risk_ref,
                "risk_instance_ref": row_risk_instance_ref,
                "risk_anchor_ref": row_risk_anchor_ref,
                "event_ref": row_event_ref,
                "source_locator_ref": loc_ref,
                "source_count": src_count,
            }
            validated_row = ProductContinuityRow(**row_dict).model_dump()

            if site_ref is not None and row_site_ref != site_ref:
                continue

            if obj_type == "risk":
                if (
                    not row_risk_instance_ref
                    or row_risk_instance_ref in seen_risk_instances
                ):
                    raise ProductPublicationError("continuity_unavailable")
                seen_risk_instances.add(row_risk_instance_ref)
                all_risk_rows.append(validated_row)

            rows.append(validated_row)

        counts = {
            "new": 0,
            "upgraded": 0,
            "continued": 0,
            "downgraded": 0,
            "closed": 0,
            "reopened": 0,
            "needs_rejudgment": 0,
            "mid_high_total": 0,
            "changed_subject_count": 0,
        }
        changed_subjects: set[str] = set()
        for r in all_risk_rows:
            k = r["change_kind"]
            if k in counts:
                counts[k] += 1
            else:
                raise ProductPublicationError("continuity_unavailable")
            if r["severity_after_text"] in {"高", "中"}:
                counts["mid_high_total"] += 1
            if k in {
                "new",
                "upgraded",
                "downgraded",
                "closed",
                "reopened",
                "needs_rejudgment",
            }:
                s = r["subject_ref"]
                if s:
                    changed_subjects.add(s)

        counts["changed_subject_count"] = len(changed_subjects)

        if (
            counts["new"]
            + counts["upgraded"]
            + counts["continued"]
            + counts["downgraded"]
            + counts["closed"]
            + counts["reopened"]
            + counts["needs_rejudgment"]
            != len(all_risk_rows)
        ):
            raise ProductPublicationError("continuity_unavailable")

        validated_counts = ProductContinuityChangeCounts(**counts).model_dump()
        sorted_rows = sorted(rows, key=_continuity_row_sort_key)
        total_count = len(sorted_rows)
        truncated = total_count > 200
        shown_rows = sorted_rows[:200]
        shown_count = len(shown_rows)

        comparison_dict = {
            "available": True,
            "basis_text": basis_text,
            "comparison_text": comparison_text,
            "source_run_text": source_run_text,
            "change_counts": validated_counts,
            "rows": shown_rows,
            "shown_count": shown_count,
            "total_count": total_count,
            "truncated": truncated,
        }
        validated_comparison = ProductContinuityComparison(
            **comparison_dict
        ).model_dump()

        identity_dict: dict[str, Any] = {
            "project_ref": launch.project_id,
            "public_run_token": launch.public_run_token,
            "snapshot_token": publication.snapshot_token,
            "data_cutoff_text": publication.data_cutoff,
            "mode_text": launch.mode_text,
            "site_scope_text": "、".join(
                _public_continuity_text(site_audience_map[s].site_label)
                for s in publication.site_coverage
            ),
        }
        if site_ref is not None:
            identity_dict["site_ref"] = site_ref

        validated_identity = ProductContinuityIdentity(**identity_dict).model_dump(
            exclude_none=True
        )

        public_blob = json.dumps(
            {"identity": validated_identity, "comparison": validated_comparison},
            ensure_ascii=False,
        ).casefold()
        if _SECRET_VALUE.search(public_blob) or any(
            marker in public_blob
            for marker in (
                '"run_id"',
                '"run_ref"',
                '"snapshot_ref"',
                '"cutoff_ref"',
                '"authority_hash"',
                '"authority_receipt',
                '"packet_digest"',
                '"packet_identity"',
                '"s4_',
                '"r5_',
            )
        ):
            raise ProductPublicationError("continuity_unavailable")

        response_digest = lr.content_digest(
            {"identity": validated_identity, "comparison": validated_comparison}
        )

        response_dict = {
            "result_context_token": result_context_token,
            "identity": validated_identity,
            "comparison": validated_comparison,
            "response_digest": response_digest,
        }
        return ProductContinuityResponse(**response_dict).model_dump(
            exclude_none=True
        )

    register_project_routes(
        router,
        ProjectRouteContext(
            root=root,
            backup_runtime_root=backup_runtime_root,
            maintenance_wait_seconds=maintenance_wait_seconds,
            resolve_project=resolve_project,
            authorize=authorize,
            blocked_project_open_projection=blocked_project_open_projection,
            open_project_inspection=open_project_inspection,
            verification_projection=verification_projection,
            read_json_object=_read_json_object,
            begin_product_boundary=begin_product_boundary,
            boundary_verification_result=boundary_verification_result,
            classify_product_recovery=classify_product_recovery,
            finish_product_boundary=finish_product_boundary,
            operation_key=operation_key,
            operation_projection_for=operation_projection_for,
            migration_projection=migration_projection,
            migration_records=migration_records,
            migration_record=migration_record,
            reserve_operation=reserve_operation,
            start_backup_worker=start_backup_worker,
            operation_record=operation_record,
            backup_source=backup_source,
            requested_operation_id=requested_operation_id,
            restore_should_start=restore_should_start,
            start_restore_worker=start_restore_worker,
            acquire_product_write_gate=acquire_product_write_gate,
            mutable_project_error=mutable_project_error,
            open_entry=_open_entry,
            workspace_dir=_workspace_dir,
            backup_terminal=_PRODUCT_BACKUP_TERMINAL,
            monitoring_action=MonitoringAction,
        ),
    )

    register_setup_routes(
        router,
        SetupRouteContext(
            root=root,
            resolve_project=resolve_project,
            authorize=authorize,
            mutable_project_error=mutable_project_error,
            read_json_object=_read_json_object,
            acquire_product_write_gate=acquire_product_write_gate,
            open_entry=_open_entry,
            legacy_setup_projection=legacy_setup_projection,
            setup_catalog=setup_catalog,
            setup_registry=setup_registry,
            open_legacy_view=open_legacy_view,
            validated_layer_scope=_validated_layer_scope,
            workspace_dir=_workspace_dir,
            risk_registry_lock=risk_registry_lock,
            monitoring_action=MonitoringAction,
        ),
    )

    run_route_context = RunRouteContext(
        root=root,
        resolve_project=resolve_project,
        authorize=authorize,
        mutable_project_error=mutable_project_error,
        read_json_object=_read_json_object,
        acquire_product_write_gate=acquire_product_write_gate,
        open_entry=_open_entry,
        auto_scopes=_auto_scopes,
        open_launch_registry=open_launch_registry,
        progress_adapter=progress_adapter,
        resolve_launch_inputs=resolve_launch_inputs,
        open_legacy_view=open_legacy_view,
        publication_overlay=_publication_overlay,
        workspace_dir=_workspace_dir,
        workspace_is_ready=_workspace_is_ready,
        monitoring_action=MonitoringAction,
    )
    register_run_launch_routes(router, run_route_context)

    publication_route_context = PublicationRouteContext(
        root=root,
        resolve_project=resolve_project,
        authorize=authorize,
        mutable_project_error=mutable_project_error,
        read_json_object=_read_json_object,
        acquire_product_write_gate=acquire_product_write_gate,
        open_entry=_open_entry,
        publication_failure_response=_publication_failure_response,
        publication_setup_inputs=_publication_setup_inputs,
        record_publication_failure=_record_publication_failure,
        open_launch_registry=open_launch_registry,
        progress_adapter=progress_adapter,
        publication_bridge=publication_bridge,
        publication_provider=publication_provider,
        r5_product_packet_factory=r5_product_packet_factory,
        r6_provider=r6_provider,
        harness_r1_profile=harness_r1_profile,
        open_legacy_view=open_legacy_view,
        load_public_result_context=_load_public_result_context,
        public_result_envelope=_public_result_envelope,
        public_result_error=_public_result_error,
        build_public_continuity_envelope=_build_public_continuity_envelope,
        workspace_dir=_workspace_dir,
        build_r5_publication_packet=(
            lambda *args, **kwargs: _build_r5_publication_packet(
                *args, **kwargs
            )
        ),
        read_publication_gate=(
            lambda *args, **kwargs: _read_publication_gate(*args, **kwargs)
        ),
        monitoring_action=MonitoringAction,
    )
    register_publication_routes(router, publication_route_context)
    register_execution_routes(router, run_route_context)

    register_public_result_routes(router, publication_route_context)
    register_run_detail_route(router, run_route_context)

    @router.api_route(
        "/{r7_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        include_in_schema=False,
    )
    async def unmatched_r7_route(r7_path: str) -> JSONResponse:
        del r7_path
        return _error_response(404, "route_not_found", _AUTH_MESSAGES["route_not_found"])

    return router


__all__ = [
    "ProductBackupRequest",
    "ProductContinuityChangeCounts",
    "ProductContinuityComparison",
    "ProductContinuityIdentity",
    "ProductContinuityResponse",
    "ProductContinuityRow",
    "ProductProjectUpgradeRequest",
    "ProjectOpenResult",
    "ProjectUpgradeProgress",
    "ProjectUpgradeResult",
    "ProductCreateRunRequest",
    "ProductExecutionActionRequest",
    "ProductRestorePreflightRequest",
    "ProductRestoreRequest",
    "ProductPublicationError",
    "ProductPublicationRequest",
    "ProductRiskRulePreviewRequest",
    "ProductRiskRuleRequest",
    "R7_PRODUCT_PREFIX",
    "R7_PRODUCT_SCHEMA",
    "R7_RISK_RULE_DB_NAME",
    "R7_WORKSPACE_ROOT_NAME",
    "create_medical_monitoring_r7_product_router",
]
