"""Migration coordinator state, inspection, and result preparation."""

from .migration_contracts import *
from .migration_oracles import *
from .migration_steps import *


class MigrationRunnerBase:
    """Shared coordinator state and inspection operations."""

    """Run one synthetic/offline legacy-to-current project migration."""

    def __init__(
        self,
        runtime_root: Union[str, Path],
        canonical_project_id: str,
        *,
        project_dir: Optional[Union[str, Path]] = None,
        workspace_dir: Optional[Union[str, Path]] = None,
        wait_seconds: float = DEFAULT_WAIT_SECONDS,
        failure_hook: Optional[Callable[[str], Any]] = None,
        failure_injector: Optional[Callable[[str], Any]] = None,
        ledger: Optional[MigrationOperationLedger] = None,
    ) -> None:
        self.runtime_root = Path(runtime_root)
        self.canonical_project_id = _safe_project_id(
            canonical_project_id,
            "migration_project_blocked",
        )
        chosen = project_dir if project_dir is not None else workspace_dir
        self.workspace_dir = (
            Path(chosen)
            if chosen is not None
            else self.runtime_root / self.canonical_project_id
        )
        try:
            self.wait_seconds = float(wait_seconds)
        except (TypeError, ValueError) as exc:
            raise MigrationError("migration_project_blocked") from exc
        if self.wait_seconds < 0 or self.wait_seconds > 120:
            raise MigrationError("migration_project_blocked")
        self.failure_hook = failure_hook if failure_hook is not None else failure_injector
        self.ledger = ledger
        self._manager: Optional[ProjectBackupManager] = None
        self._manager_ledger: Optional[OperationLedger] = None

    @property
    def staging_root(self) -> Path:
        return self.runtime_root / MIGRATION_STAGING_DIR_NAME

    @property
    def rollback_root(self) -> Path:
        return self.runtime_root / MIGRATION_ROLLBACK_DIR_NAME

    def close(self) -> None:
        if self._manager is not None and self._manager_ledger is not None:
            self._manager_ledger.close()
            self._manager = None
            self._manager_ledger = None
        if self.ledger is not None:
            self.ledger.close()
            self.ledger = None

    def __enter__(self) -> "MigrationRunner":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _ledger(self) -> MigrationOperationLedger:
        if self.ledger is None:
            self.ledger = MigrationOperationLedger(self.runtime_root)
        return self.ledger

    def _backup_manager(self) -> ProjectBackupManager:
        if self._manager is None:
            self._manager_ledger = OperationLedger(self.runtime_root)
            self._manager = ProjectBackupManager(
                self.runtime_root,
                self.canonical_project_id,
                project_dir=self.workspace_dir,
                ledger=self._manager_ledger,
                wait_seconds=self.wait_seconds,
                failure_hook=self._backup_hook,
            )
        return self._manager

    def _backup_hook(self, point: str) -> Any:
        # Pass through real 09A hook names.  A migration callback can therefore
        # inject faults at both shared backup primitives and 09B boundaries.
        return self._invoke_failure_hook(str(point))

    def _invoke_failure_hook(self, point: str) -> Any:
        callback = self.failure_hook
        if callback is None:
            return None
        try:
            result = callback(str(point))
        except InjectedMigrationFailure:
            raise
        except BaseException as exc:
            raise InjectedMigrationFailure(point) from exc
        if isinstance(result, BaseException):
            raise InjectedMigrationFailure(point) from result
        if result is True:
            raise InjectedMigrationFailure(point)
        return result

    def _hook(self, point: str) -> None:
        self._invoke_failure_hook(point)

    def _is_staging_path(self, path: Path) -> bool:
        try:
            resolved = path.resolve()
            root = self.staging_root.resolve()
            return resolved == root or root in resolved.parents
        except OSError:
            return False

    def inspect(self) -> ProjectSchemaInspection:
        # This is intentionally the first persistence operation in opening and
        # start-upgrade paths.  ProjectSchemaInspector uses mode=ro/query_only.
        return ProjectSchemaInspector(self.workspace_dir).inspect()

    def _ensure_complete_legacy(self, inspection: ProjectSchemaInspection) -> None:
        if inspection.classification is not SchemaClassification.LEGACY:
            raise MigrationError("migration_not_supported")
        if not inspection.can_view or not inspection.can_upgrade:
            raise MigrationError("migration_project_blocked")
        try:
            oracle = _workspace_oracle(self.workspace_dir)
            project_ids = set(oracle["project_ids"])
            if project_ids and project_ids != {self.canonical_project_id}:
                raise MigrationError("migration_project_blocked")
            runtime = self.workspace_dir / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
            if runtime.is_file():
                connection = _open_ro(runtime)
                try:
                    tables = _table_names(connection)
                    if "projects" in tables:
                        invalid = connection.execute(
                            "SELECT 1 FROM projects WHERE is_synthetic != 1 OR project_id != ? LIMIT 1",
                            (self.canonical_project_id,),
                        ).fetchone()
                        if invalid is not None:
                            raise MigrationError("migration_project_blocked")
                finally:
                    connection.close()
            manager = self._backup_manager()
            _artifact_hashes_and_bytes(manager, self.workspace_dir)
        except MigrationError:
            raise
        except (ProjectBackupError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise MigrationError("migration_project_blocked") from exc

    def _result(
        self,
        operation: Optional[MigrationOperation],
        state: str,
        *,
        plan: Optional[MigrationPlan] = None,
        requires_reopen: bool = False,
        message: str = "",
        next_action: str = "",
    ) -> MigrationResult:
        return MigrationResult(
            operation=operation,
            state=state,
            requires_reopen=requires_reopen,
            source_schema_set_digest=None if plan is None else plan.source_schema_set_digest,
            target_schema_set_digest=None if plan is None else plan.target_schema_set_digest,
            plan_digest=None if plan is None else plan.plan_digest,
            message=message,
            next_action=next_action,
        )

    def _cleanup_terminal_evidence(
        self,
        record: MigrationOperation,
        inspection: ProjectSchemaInspection,
    ) -> None:
        if record.status not in {STATUS_COMPLETED, STATUS_ROLLED_BACK}:
            return
        if record.status == STATUS_COMPLETED and inspection.classification is not SchemaClassification.CURRENT:
            return
        if (
            record.status == STATUS_ROLLED_BACK
            and inspection.classification
            not in {SchemaClassification.LEGACY, SchemaClassification.CURRENT}
        ):
            return
        stage_parent, _ = self._staging_paths(record.operation_id)
        rollback_path = self._rollback_path(record.operation_id)
        if record.staging_path and Path(record.staging_path) != stage_parent:
            raise MigrationError("migration_operation_conflict")
        if record.rollback_path and Path(record.rollback_path) != rollback_path:
            raise MigrationError("migration_operation_conflict")
        manager = self._backup_manager()
        if rollback_path.exists():
            manager._cleanup_path(rollback_path)
        if stage_parent.exists():
            manager._cleanup_path(stage_parent)


__all__ = [name for name in globals() if not name.startswith("__")]
