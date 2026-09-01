"""Coordination for accepted backup and migration recovery boundaries."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from . import migration as _migration
from . import project_backup as _backup
from .project_verifier_core import (
    _BACKUP_RECOVERY_STATES,
    _MIGRATION_RECOVERY_STATES,
    _MIGRATION_RETAINED_STATE,
    _MIGRATION_RETRYABLE_STATE,
    BoundaryReceipt,
    ProjectAuditBridge,
    ProjectVerificationError,
    RecoveryCoordinationError,
    _event_id,
    _new_audit_ledger,
    _normalise_project_id,
    _opaque_reference,
    _safe_reason,
)
from .schema_manifest import SchemaClassification, inspect_project_schema

class RecoveryCoordinator:
    """One coordinator for startup, open, retry, boundary, and rollback paths."""

    def __init__(
        self,
        runtime_root: str | Path,
        canonical_project_id: str,
        *,
        project_dir: Optional[str | Path] = None,
        wait_seconds: float = 0.5,
        audit_ledger_factory: Optional[Callable[..., Any]] = None,
        audit_ledger: Any = None,
        principal_snapshot_hash: str = "",
        authorization_decision_hash: str = "",
    ) -> None:
        self.runtime_root = Path(runtime_root)
        self.canonical_project_id = _normalise_project_id(canonical_project_id)
        self.project_dir = Path(project_dir) if project_dir is not None else (
            self.runtime_root / self.canonical_project_id
        )
        self.wait_seconds = float(wait_seconds)
        self.audit_ledger_factory = audit_ledger_factory
        self._ledger = audit_ledger
        self._owns_ledger = audit_ledger is None
        self._principal_snapshot_hash = principal_snapshot_hash
        self._authorization_decision_hash = authorization_decision_hash

    def _get_ledger(self) -> Any:
        if self._ledger is None:
            self._ledger = _new_audit_ledger(
                self.runtime_root,
                self.canonical_project_id,
                self.audit_ledger_factory,
            )
        return self._ledger

    def _bridge(self) -> ProjectAuditBridge:
        return ProjectAuditBridge(
            self._get_ledger(),
            self.canonical_project_id,
            principal_snapshot_hash=self._principal_snapshot_hash,
            authorization_decision_hash=self._authorization_decision_hash,
        )

    def close(self) -> None:
        ledger = self._ledger
        self._ledger = None
        if ledger is not None and self._owns_ledger:
            close = getattr(ledger, "close", None)
            if callable(close):
                close()

    def __enter__(self) -> "RecoveryCoordinator":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def open_project(self) -> Any:
        """Inspect first, then use the accepted migration runner's open path."""

        try:
            initial = inspect_project_schema(self.project_dir)
        except Exception as exc:
            raise RecoveryCoordinationError("schema_inspection_failed") from exc
        runner = _migration.MigrationRunner(
            self.runtime_root,
            self.canonical_project_id,
            project_dir=self.project_dir,
            wait_seconds=self.wait_seconds,
        )
        try:
            if initial.classification is SchemaClassification.LEGACY:
                runner._ensure_complete_legacy(initial)
            return runner.open_project()
        except (_migration.MigrationError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise RecoveryCoordinationError(_safe_reason(
                getattr(exc, "code", "recovery_required"),
                "recovery_required",
            )) from exc
        finally:
            runner.close()

    def startup_recovery_scan(
        self,
        operation_id: Optional[str] = None,
    ) -> tuple[Any, ...]:
        """Scan 09A recovery evidence and resume only 09B public states.

        09A restore boundaries require the original same-key/package request,
        so startup reports their durable records without replaying filesystem
        switches.  09B owns a complete evidence-based recovery runner and may
        be resumed here.  Retained triage and retryable failures remain
        excluded from both paths.
        """

        try:
            initial = inspect_project_schema(self.project_dir)
        except Exception as exc:
            raise RecoveryCoordinationError("schema_inspection_failed") from exc
        backup_pending: tuple[Any, ...] = ()
        ledger_path = self.runtime_root / str(
            getattr(_backup, "OPERATIONS_DB_NAME", "backup_operations.sqlite3")
        )
        if ledger_path.is_file():
            backup_ledger = _backup.OperationLedger(ledger_path)
            try:
                backup_pending = tuple(
                    record
                    for record in backup_ledger.list_for_project(
                        self.canonical_project_id
                    )
                    if str(record.operation_kind)
                    == str(getattr(_backup, "OP_RESTORE", "restore"))
                    and str(record.status) in _BACKUP_RECOVERY_STATES
                )
            finally:
                backup_ledger.close()
        runner = _migration.MigrationRunner(
            self.runtime_root,
            self.canonical_project_id,
            project_dir=self.project_dir,
            wait_seconds=self.wait_seconds,
        )
        try:
            if operation_id:
                ledger = runner._ledger()
                record = ledger.get(operation_id)
                status = str(record.status)
                if status in {_MIGRATION_RETRYABLE_STATE, _MIGRATION_RETAINED_STATE}:
                    raise RecoveryCoordinationError("explicit_retry_or_triage_required")
                if status not in _MIGRATION_RECOVERY_STATES and status not in set(
                    getattr(_migration, "TERMINAL_STATES", ())
                ):
                    raise RecoveryCoordinationError("operation_not_recoverable")
            return backup_pending + tuple(runner.recover(operation_id))
        except RecoveryCoordinationError:
            raise
        except (_migration.MigrationError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise RecoveryCoordinationError(_safe_reason(
                getattr(exc, "code", "recovery_required"),
                "recovery_required",
            )) from exc
        finally:
            runner.close()

    recover = startup_recovery_scan
    recover_pending = startup_recovery_scan

    def start_upgrade(self, idempotency_key: str, *, confirmation: bool = True) -> Any:
        """Use the same coordinator object for explicit same-key migration retry."""

        runner = _migration.MigrationRunner(
            self.runtime_root,
            self.canonical_project_id,
            project_dir=self.project_dir,
            wait_seconds=self.wait_seconds,
        )
        try:
            return runner.start_upgrade(idempotency_key, confirmation=confirmation)
        except (_migration.MigrationError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise RecoveryCoordinationError(_safe_reason(
                getattr(exc, "code", "retry_failed"),
                "retry_failed",
            )) from exc
        finally:
            runner.close()

    def begin_boundary(
        self,
        operation_ref: str,
        *,
        operation_kind: str,
        expected_state: str,
        before_digest: str,
        boundary_token: str,
        package_digest: Optional[str] = None,
        source_digest: Optional[str] = None,
        plan_digest: Optional[str] = None,
        slot_presence: Optional[Mapping[str, Any]] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
    ) -> BoundaryReceipt:
        safe_operation = _opaque_reference(operation_ref, prefix="operation")
        safe_token = _opaque_reference(boundary_token, prefix="boundary")
        try:
            event = self._bridge().boundary_intent(
                safe_operation,
                operation_kind=operation_kind,
                boundary_token=safe_token,
                expected_state=expected_state,
                before_digest=before_digest,
                package_digest=package_digest,
                source_digest=source_digest,
                plan_digest=plan_digest,
                slot_presence=slot_presence,
                operation_update=operation_update,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc
        return BoundaryReceipt(
            operation_id=safe_operation,
            operation_kind=_opaque_reference(operation_kind, prefix="kind"),
            boundary_token=safe_token,
            expected_state=_safe_reason(expected_state, "unknown_state"),
            before_digest=str(before_digest or ""),
            principal_snapshot_hash=self._bridge().principal_snapshot_hash,
            authorization_decision_hash=self._bridge().authorization_decision_hash,
            intent_event_id=_event_id(event),
        )

    def mark_committed(
        self,
        receipt: BoundaryReceipt,
        *,
        observed_durable_phase: str,
        after_digest: str,
        marker_digest: Optional[str] = None,
        member_digest: Optional[str] = None,
        workspace_digest: Optional[str] = None,
        operation_update: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        try:
            return self._bridge().boundary_committed(
                receipt.operation_id,
                operation_kind=receipt.operation_kind,
                boundary_token=receipt.boundary_token,
                observed_durable_phase=observed_durable_phase,
                after_digest=after_digest,
                marker_digest=marker_digest,
                member_digest=member_digest,
                workspace_digest=workspace_digest,
                operation_update=operation_update,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc

    def mark_verified(
        self,
        receipt: BoundaryReceipt,
        *,
        verifier_outcome: str,
        after_digest: str,
        r1_anchor: Optional[str] = None,
        publication_anchor: Optional[str] = None,
        continuity_anchor: Optional[str] = None,
    ) -> Any:
        try:
            return self._bridge().boundary_verified(
                receipt.operation_id,
                operation_kind=receipt.operation_kind,
                boundary_token=receipt.boundary_token,
                verifier_outcome=verifier_outcome,
                after_digest=after_digest,
                r1_anchor=r1_anchor,
                publication_anchor=publication_anchor,
                continuity_anchor=continuity_anchor,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc

    def classify_recovery(
        self,
        operation_ref: str,
        *,
        operation_kind: str,
        observed_durable_phase: str,
        classification: str,
        slot_anchor: Optional[str] = None,
        marker_anchor: Optional[str] = None,
        root_ledger_anchor: Optional[str] = None,
    ) -> Any:
        try:
            return self._bridge().recovery_classified(
                operation_ref,
                operation_kind=operation_kind,
                observed_durable_phase=observed_durable_phase,
                classification=classification,
                slot_anchor=slot_anchor,
                marker_anchor=marker_anchor,
                root_ledger_anchor=root_ledger_anchor,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc

    def release_rollback_evidence(
        self,
        operation_ref: str,
        *,
        verified_event_id: str,
        rollback_digest: str,
        release: Callable[[], Any],
        operation_kind: str,
        operation_update: Optional[Mapping[str, Any]] = None,
    ) -> bool:
        """Release rollback evidence only after a verified completion event."""

        bridge = self._bridge()
        try:
            intent = bridge.rollback_release_intent(
                operation_ref,
                operation_kind=operation_kind,
                verified_event_id=verified_event_id,
                rollback_digest=rollback_digest,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc
        intent_id = _event_id(intent)
        if not intent_id:
            raise RecoveryCoordinationError("release_intent_event_missing")
        try:
            released = release()
            if released is False:
                raise OSError("release_rejected")
        except Exception:
            try:
                bridge.rollback_evidence_release_failed(
                    operation_ref,
                    operation_kind=operation_kind,
                    release_intent_id=intent_id,
                    outcome="release_failed",
                    diagnostic_enum="release_failed",
                )
            except ProjectVerificationError as exc:
                raise RecoveryCoordinationError(exc.code) from exc
            return False
        try:
            bridge.rollback_evidence_released(
                operation_ref,
                operation_kind=operation_kind,
                release_intent_id=intent_id,
                outcome="released",
                operation_update=operation_update,
            )
        except ProjectVerificationError as exc:
            raise RecoveryCoordinationError(exc.code) from exc
        return True


def startup_recovery_scan(
    runtime_root: str | Path,
    canonical_project_id: str,
    *,
    project_dir: Optional[str | Path] = None,
    operation_id: Optional[str] = None,
    wait_seconds: float = 0.5,
    audit_ledger_factory: Optional[Callable[..., Any]] = None,
) -> tuple[Any, ...]:
    coordinator = RecoveryCoordinator(
        runtime_root,
        canonical_project_id,
        project_dir=project_dir,
        wait_seconds=wait_seconds,
        audit_ledger_factory=audit_ledger_factory,
    )
    try:
        return coordinator.startup_recovery_scan(operation_id)
    finally:
        coordinator.close()
