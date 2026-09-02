"""State-preserving project operations used by the R7 product router."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import threading
from typing import Any, Callable, Mapping, Optional, Union

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...runtime import launch_registry as lr
from ...runtime import project_backup as pb
from ...runtime import run_setup as rs
from ...runtime.maintenance_gate import MaintenanceGateError, ProjectMaintenanceGate
from ...runtime.migration import MigrationError, MigrationOperationLedger, MigrationRunner, TERMINAL_STATES
from ...runtime.project_lifecycle import (
    DATA_COVERAGE_INCOMPLETE,
    OPEN_MODE_BLOCKED,
    ProjectCompatibilityError,
    ProjectOpenDTO,
    ReadOnlyProjectView,
    inspect_project_schema,
    open_read_only_project_view,
    require_current_project,
    upgrade_progress_from_operation,
    upgrade_result_from_state,
)
from ...runtime.project_verifier import (
    ProjectVerificationError,
    ProjectVerifier,
    RESULT_RECORD_COMPLETE,
)
from ...runtime.run_entry import PROFILE_DB_NAME, RUN_BINDING_DB_NAME, MonitoringRunEntry
from ...runtime.runtime_progress import RUNTIME_DB_NAME, RUNTIME_DIR_NAME, RuntimeProgressAdapter
from ...runtime.schema_manifest import SchemaClassification, inspect_member
from .contracts import ProductPrepareAndStartRequest
from .errors import (
    _AUTH_MESSAGES,
    _error_response,
    _launch_error_response,
    _run_entry_error_response,
    _status_for,
)
from .legacy_projections import _legacy_risk_projection, _setup_projection
from .route_utils import _request_id, _workspace_dir, _workspace_is_ready


@dataclass(frozen=True)
class ProjectOperationDependencies:
    root: Path
    backup_runtime_root: Path
    maintenance_wait_seconds: float
    audit_ledger_factory: Any
    risk_registries: dict[str, Any]
    risk_registry_lock: Any
    harness_runtime_factory: Any
    harness_adapter: Any
    harness_catalog: Any
    harness_r1_profile: Any
    project_resolver: Any
    backup_workers: dict[Any, Any]
    backup_workers_lock: Any
    backup_terminal: Any
    restore_terminal: Any
    recovery_coordinator_factory: Any
    blocked_legacy_view_type: Any
    monitoring_action: Any
    synthetic_setup_inputs: Any
    risk_rule_db_name: str


@dataclass(frozen=True)
class ProjectOperations:
    acquire_product_write_gate: Any
    close_cached_risk_registry: Any
    operation_record: Any
    backup_source: Any
    requested_operation_id: Any
    operation_key: Any
    reserve_operation: Any
    product_worker_key: Any
    start_worker_once: Any
    mark_worker_failed: Any
    start_backup_worker: Any
    start_restore_worker: Any
    restore_should_start: Any
    setup_registry: Any
    setup_catalog: Any
    open_launch_registry: Any
    resolve_launch_inputs: Any
    progress_adapter: Any
    resolve_project: Any
    mutable_project_error: Any
    open_project_inspection: Any
    verification_context_hashes: Any
    verification_projection: Any
    operation_projection_for: Any
    begin_product_boundary: Any
    finish_product_boundary: Any
    boundary_verification_result: Any
    rollback_evidence_digest: Any
    release_product_rollback: Any
    classify_product_recovery: Any
    migration_records: Any
    migration_record: Any
    migration_projection: Any
    blocked_project_open_projection: Any
    open_legacy_view: Any
    legacy_setup_projection: Any


def build_project_operations(
    router: APIRouter,
    dependencies: ProjectOperationDependencies,
) -> ProjectOperations:
    root = dependencies.root
    backup_runtime_root = dependencies.backup_runtime_root
    maintenance_wait_seconds = dependencies.maintenance_wait_seconds
    audit_ledger_factory = dependencies.audit_ledger_factory
    risk_registries = dependencies.risk_registries
    risk_registry_lock = dependencies.risk_registry_lock
    harness_runtime_factory = dependencies.harness_runtime_factory
    harness_adapter = dependencies.harness_adapter
    harness_catalog = dependencies.harness_catalog
    harness_r1_profile = dependencies.harness_r1_profile
    project_resolver = dependencies.project_resolver
    _PRODUCT_BACKUP_WORKERS = dependencies.backup_workers
    _PRODUCT_BACKUP_WORKERS_LOCK = dependencies.backup_workers_lock
    _PRODUCT_BACKUP_TERMINAL = dependencies.backup_terminal
    _PRODUCT_RESTORE_TERMINAL = dependencies.restore_terminal
    RecoveryCoordinator = dependencies.recovery_coordinator_factory
    _BlockedLegacyView = dependencies.blocked_legacy_view_type
    MonitoringAction = dependencies.monitoring_action
    _synthetic_setup_inputs = dependencies.synthetic_setup_inputs
    R7_RISK_RULE_DB_NAME = dependencies.risk_rule_db_name

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
        try:
            snapshots, baselines = _synthetic_setup_inputs(canonical_project_id)
        except Exception as exc:
            return _run_entry_error_response(exc)
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


    return ProjectOperations(
        acquire_product_write_gate=acquire_product_write_gate,
        close_cached_risk_registry=close_cached_risk_registry,
        operation_record=operation_record,
        backup_source=backup_source,
        requested_operation_id=requested_operation_id,
        operation_key=operation_key,
        reserve_operation=reserve_operation,
        product_worker_key=product_worker_key,
        start_worker_once=start_worker_once,
        mark_worker_failed=mark_worker_failed,
        start_backup_worker=start_backup_worker,
        start_restore_worker=start_restore_worker,
        restore_should_start=restore_should_start,
        setup_registry=setup_registry,
        setup_catalog=setup_catalog,
        open_launch_registry=open_launch_registry,
        resolve_launch_inputs=resolve_launch_inputs,
        progress_adapter=progress_adapter,
        resolve_project=resolve_project,
        mutable_project_error=mutable_project_error,
        open_project_inspection=open_project_inspection,
        verification_context_hashes=verification_context_hashes,
        verification_projection=verification_projection,
        operation_projection_for=operation_projection_for,
        begin_product_boundary=begin_product_boundary,
        finish_product_boundary=finish_product_boundary,
        boundary_verification_result=boundary_verification_result,
        rollback_evidence_digest=rollback_evidence_digest,
        release_product_rollback=release_product_rollback,
        classify_product_recovery=classify_product_recovery,
        migration_records=migration_records,
        migration_record=migration_record,
        migration_projection=migration_projection,
        blocked_project_open_projection=blocked_project_open_projection,
        open_legacy_view=open_legacy_view,
        legacy_setup_projection=legacy_setup_projection,
    )


__all__ = [
    "ProjectOperationDependencies",
    "ProjectOperations",
    "build_project_operations",
]
