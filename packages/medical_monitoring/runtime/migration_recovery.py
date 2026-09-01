"""Atomic migration switch, recovery, and rollback operations."""

from .migration_contracts import *
from .migration_oracles import *
from .migration_steps import *


class MigrationRecoveryMixin:
    def _recover_directory_state(
        self,
        record: MigrationOperation,
        plan: MigrationPlan,
    ) -> Optional[MigrationResult]:
        if record.status not in {
            STATUS_SWITCHING,
            STATUS_LIVE_VERIFYING,
            STATUS_ROLLBACK_IN_PROGRESS,
        }:
            return None
        stage_parent, stage_workspace = self._staging_paths(record.operation_id)
        rollback_path = self._rollback_path(record.operation_id)
        if record.staging_path and Path(record.staging_path) != stage_parent:
            raise MigrationError("migration_operation_conflict")
        if record.rollback_path and Path(record.rollback_path) != rollback_path:
            raise MigrationError("migration_operation_conflict")

        def retain(detail: str) -> MigrationResult:
            try:
                self._ledger().update(
                    record.operation_id,
                    status=STATUS_RETAINED_FOR_TRIAGE,
                    terminal_outcome=STATUS_RETAINED_FOR_TRIAGE,
                    current_step="升级现场已保留待处置",
                    error_code="migration_rollback_failed",
                    error_message=_ERROR_MESSAGES["migration_rollback_failed"],
                    rollback_path=str(rollback_path) if rollback_path.exists() else None,
                    staging_path=str(stage_parent) if stage_parent.exists() else None,
                    directory_switch_stage="retained_for_triage",
                )
            except BaseException:
                pass
            raise MigrationError(
                "migration_rollback_failed",
                details={"operation_id": record.operation_id, "detail": detail},
            )

        def rolled_back() -> MigrationResult:
            current = self._ledger().update(
                record.operation_id,
                status=STATUS_ROLLED_BACK,
                progress_percent=max(record.progress_percent, PROGRESS_SWITCHED),
                current_step="原项目已恢复",
                terminal_outcome=STATUS_ROLLED_BACK,
                rollback_path=str(rollback_path) if rollback_path.exists() else None,
                staging_path=str(stage_parent) if stage_parent.exists() else None,
                directory_switch_stage="rolled_back",
                error_code=None,
                error_message=None,
            )
            manager = self._backup_manager()
            if rollback_path.exists():
                manager._cleanup_path(rollback_path)
            if stage_parent.exists():
                manager._cleanup_path(stage_parent)
            return self._result(
                current,
                STATUS_ROLLED_BACK,
                plan=plan,
                message="升级未完成，原项目仍可只读查看。可稍后重试。",
                next_action="稍后重试升级",
            )

        def restore_and_finish(manager: ProjectBackupManager) -> MigrationResult:
            self._mark_rollback_in_progress(record.operation_id)
            if not self._rollback_after_failure(record, rollback_path, stage_parent):
                return retain("恢复点切换失败")
            try:
                self._verify_source_workspace(manager, record, self.workspace_dir)
            except BaseException as exc:
                return retain(str(exc))
            return rolled_back()

        if not rollback_path.exists():
            if self.workspace_dir.is_dir() and record.status == STATUS_SWITCHING:
                inspection = ProjectSchemaInspector(self.workspace_dir).inspect()
                if inspection.classification is SchemaClassification.LEGACY:
                    # The ledger checkpoint can precede the first rename.
                    return None
            if self.workspace_dir.is_dir():
                return retain("切换记录存在但原项目恢复点缺失")
            return retain("切换记录存在但项目目录缺失")

        manager = self._backup_manager()
        gate = ProjectMaintenanceGate(
            self.runtime_root,
            self.canonical_project_id,
            wait_seconds=self.wait_seconds,
            event_callback=lambda event: self._gate_event(record.operation_id, event),
        )
        with gate.exclusive():
            try:
                _assert_directory(rollback_path)
                self._checkpoint_workspace(rollback_path)
                _remove_sqlite_sidecars(rollback_path)
                _assert_no_sqlite_sidecars(rollback_path)
            except BaseException as exc:
                return retain(str(exc))

            if self.workspace_dir.is_dir():
                inspection = ProjectSchemaInspector(self.workspace_dir).inspect()
                if inspection.classification is SchemaClassification.CURRENT:
                    try:
                        self._verify_source_workspace(manager, record, rollback_path)
                        expected_workspace = self.workspace_dir
                        if stage_workspace.is_dir():
                            stage_inspection = ProjectSchemaInspector(stage_workspace).inspect()
                            if stage_inspection.classification is not SchemaClassification.CURRENT:
                                return retain("切换副本格式无法核对")
                            expected_workspace = stage_workspace
                        expected_oracle = _workspace_oracle(expected_workspace)
                        expected_artifacts = _artifact_hashes_and_bytes(manager, expected_workspace)
                        self._verify_live_target(manager, expected_oracle, expected_artifacts)
                    except BaseException:
                        return restore_and_finish(manager)
                    current = self._ledger().update(
                        record.operation_id,
                        status=STATUS_COMPLETED,
                        progress_percent=PROGRESS_COMPLETE,
                        current_step="升级完成",
                        terminal_outcome=STATUS_COMPLETED,
                        rollback_path=str(rollback_path),
                        staging_path=str(stage_parent),
                        directory_switch_stage="verified",
                        error_code=None,
                        error_message=None,
                    )
                    manager._cleanup_path(rollback_path)
                    if stage_parent.exists():
                        manager._cleanup_path(stage_parent)
                    return self._result(
                        current,
                        STATUS_COMPLETED,
                        plan=plan,
                        requires_reopen=True,
                        message="项目格式已升级。请重新打开项目后继续使用。",
                        next_action="重新打开项目",
                    )

                if inspection.classification is SchemaClassification.LEGACY:
                    try:
                        self._verify_source_workspace(manager, record, self.workspace_dir)
                        self._verify_source_workspace(manager, record, rollback_path)
                    except BaseException:
                        return restore_and_finish(manager)
                    return rolled_back()

            return restore_and_finish(manager)

    def _switch_and_verify(
        self,
        record: MigrationOperation,
        plan: MigrationPlan,
        stage_parent: Path,
        stage_workspace: Path,
    ) -> MigrationOperation:
        manager = self._backup_manager()
        rollback_path = self._rollback_path(record.operation_id)
        expected_oracle = _workspace_oracle(stage_workspace)
        expected_artifacts = _artifact_hashes_and_bytes(manager, stage_workspace)
        _assert_same_device(self.runtime_root, stage_parent, self.rollback_root)
        self.rollback_root.mkdir(parents=True, exist_ok=True)
        _assert_same_device(self.runtime_root, self.rollback_root)
        if rollback_path.exists():
            raise MigrationError("migration_operation_conflict")
        current = self._ledger_update(
            record.operation_id,
            status=STATUS_SWITCHING,
            progress_percent=PROGRESS_SWITCHED,
            current_step="正在切换项目",
            rollback_path=str(rollback_path),
            staging_path=str(stage_parent),
            directory_switch_stage="ready",
        )
        old_live_moved = False
        try:
            self._hook("migration.switch.live_to_rollback.before")
            if not self.workspace_dir.exists():
                raise MigrationError("migration_source_changed")
            _replace_or_raise(self.workspace_dir, rollback_path)
            old_live_moved = True
            self._checkpoint_workspace(rollback_path)
            _remove_sqlite_sidecars(rollback_path)
            _assert_no_sqlite_sidecars(rollback_path)
            ProjectBackupManager._fsync_dir(self.runtime_root)
            current = self._ledger_update(
                current.operation_id,
                directory_switch_stage="live_to_rollback",
                current_step="原项目已保留",
            )
            self._hook("migration.switch.live_to_rollback.after")
            self._hook("migration.switch.staging_to_live.before")
            _replace_or_raise(stage_workspace, self.workspace_dir)
            ProjectBackupManager._fsync_dir(self.runtime_root)
            current = self._ledger_update(
                current.operation_id,
                status=STATUS_LIVE_VERIFYING,
                progress_percent=PROGRESS_SWITCHED,
                current_step="项目已切换，正在重新核对",
                directory_switch_stage="staging_to_live",
            )
            self._hook("migration.switch.staging_to_live.after")
            self._verify_live_target(manager, expected_oracle, expected_artifacts)
            current = self._ledger_update(
                current.operation_id,
                status=STATUS_COMPLETED,
                progress_percent=PROGRESS_COMPLETE,
                current_step="升级完成",
                terminal_outcome=STATUS_COMPLETED,
                rollback_path=str(rollback_path),
                staging_path=str(stage_parent),
                directory_switch_stage="verified",
                payload=dict(current.payload),
            )
            # The rollback copy is no longer needed after independent reopen
            # verification, but the ledger keeps its path as evidence.
            manager._cleanup_path(rollback_path)
            manager._cleanup_path(stage_parent)
            return current
        except _CommittedStepFailure:
            raise
        except BaseException as exc:
            if old_live_moved:
                self._mark_rollback_in_progress(current.operation_id)
                rolled_back = self._rollback_after_failure(current, rollback_path, stage_parent)
                if rolled_back:
                    self._ledger().update(
                        current.operation_id,
                        status=STATUS_ROLLED_BACK,
                        progress_percent=current.progress_percent,
                        current_step="原项目已恢复",
                        terminal_outcome=STATUS_ROLLED_BACK,
                        rollback_path=str(rollback_path),
                        staging_path=str(stage_parent) if stage_parent.exists() else None,
                        directory_switch_stage="rolled_back",
                        error_code=(exc.code if isinstance(exc, MigrationError) else "migration_switch_failed"),
                        error_message=(
                            exc.message if isinstance(exc, MigrationError) else _ERROR_MESSAGES["migration_switch_failed"]
                        ),
                    )
                    # Preserve evidence only when a failed-live remains; the
                    # restored source itself is the live truth.
                    if stage_parent.exists():
                        manager._cleanup_path(stage_parent)
                    return self._ledger().get(current.operation_id)
                self._ledger().update(
                    current.operation_id,
                    status=STATUS_RETAINED_FOR_TRIAGE,
                    terminal_outcome=STATUS_RETAINED_FOR_TRIAGE,
                    current_step="升级现场已保留待处置",
                    error_code="migration_rollback_failed",
                    error_message=_ERROR_MESSAGES["migration_rollback_failed"],
                    rollback_path=str(rollback_path) if rollback_path.exists() else str(stage_parent),
                    staging_path=str(stage_parent),
                    directory_switch_stage="retained_for_triage",
                )
                raise MigrationError("migration_rollback_failed") from exc
            # No directory was switched; old live is intact.  A committed DB
            # step or an injected ledger boundary leaves staging for retry.
            if isinstance(exc, _CommittedStepFailure):
                raise
            manager._cleanup_path(stage_parent)
            self._safe_failure(current.operation_id, getattr(exc, "code", "migration_verification_failed"), str(exc))
            raise

    def _resume_or_execute(
        self,
        record: MigrationOperation,
        plan: MigrationPlan,
    ) -> MigrationResult:
        manager = self._backup_manager()
        recovered = self._recover_directory_state(record, plan)
        if recovered is not None:
            return recovered
        if record.package_path is None or record.source_workspace_fingerprint is None:
            record = self._prepare_backup(record, plan)
        package_path = Path(record.package_path or "")
        if not package_path.is_file():
            raise MigrationError("migration_project_blocked")
        stage_parent, stage_workspace = self._staging_paths(record.operation_id)
        gate = ProjectMaintenanceGate(
            self.runtime_root,
            self.canonical_project_id,
            wait_seconds=self.wait_seconds,
            event_callback=lambda event: self._gate_event(record.operation_id, event),
        )
        try:
            with gate.exclusive():
                self._hook("migration.source_recheck.before")
                live_fp = self._live_fingerprint(manager)
                if live_fp != record.source_workspace_fingerprint:
                    conflict = self._ledger().update(
                        record.operation_id,
                        status=STATUS_MIGRATION_OPERATION_CONFLICT,
                        terminal_outcome=STATUS_MIGRATION_OPERATION_CONFLICT,
                        current_step="项目内容已变化",
                        error_code=STATUS_MIGRATION_OPERATION_CONFLICT,
                        error_message=_ERROR_MESSAGES[STATUS_MIGRATION_OPERATION_CONFLICT],
                        directory_switch_stage="source_drift",
                    )
                    manager._cleanup_path(stage_parent)
                    raise MigrationError(
                        "migration_operation_conflict",
                        details={"operation_id": conflict.operation_id},
                    )
                self._hook("migration.source_recheck.after")
                self._quiesce_live(manager)
                source_oracle = _workspace_oracle(self.workspace_dir)
                source_artifacts = _artifact_hashes_and_bytes(manager, self.workspace_dir)
                current = self._ledger().get(record.operation_id)
                if current.status in {
                    STATUS_BACKUP_VERIFIED,
                    STATUS_BACKUP_REQUIRED,
                    STATUS_BACKUP_IN_PROGRESS,
                    STATUS_INSPECTING,
                    STATUS_REQUESTED,
                    STATUS_RETRYABLE_FAILED,
                }:
                    current = self._ledger_update(
                        current.operation_id,
                        status=STATUS_STAGING,
                        progress_percent=PROGRESS_STAGING_COMPLETE,
                        current_step="正在建立升级副本",
                        staging_path=str(stage_parent),
                    )
                self._ensure_staging(current, manager, source_oracle)
                current = self._ledger().get(current.operation_id)
                if not plan.steps:
                    raise MigrationError("migration_operation_conflict")
                current = self._run_steps(current, plan, stage_workspace)
                current = self._switch_and_verify(
                    current,
                    plan,
                    stage_parent,
                    stage_workspace,
                )
                if current.status == STATUS_COMPLETED:
                    return self._result(
                        current,
                        STATUS_COMPLETED,
                        plan=plan,
                        requires_reopen=True,
                        message="项目格式已升级。请重新打开项目后继续使用。",
                        next_action="重新打开项目",
                    )
                if current.status == STATUS_ROLLED_BACK:
                    return self._result(
                        current,
                        STATUS_ROLLED_BACK,
                        plan=plan,
                        message="升级未完成，原项目仍可只读查看。可稍后重试。",
                        next_action="稍后重试升级",
                    )
                return self._result(current, current.status, plan=plan)
        except _CommittedStepFailure:
            # Preserve sibling staging and ledger checkpoint for same-key replay.
            raise
        except ProjectBusyError as exc:
            self._safe_failure(record.operation_id, exc.code, exc.message)
            manager._cleanup_path(stage_parent)
            raise MigrationError(exc.code, exc.message) from exc
        except MigrationError as exc:
            current = self._ledger().get(record.operation_id)
            if current.status not in TERMINAL_STATES:
                self._safe_failure(record.operation_id, exc.code, exc.message)
            raise
        except (
            ProjectBackupError,
            MaintenanceGateError,
            OSError,
            sqlite3.Error,
            ValueError,
            TypeError,
        ) as exc:
            manager._cleanup_path(stage_parent)
            self._safe_failure(
                record.operation_id,
                "migration_verification_failed",
                str(exc),
            )
            raise MigrationError("migration_verification_failed") from exc

    def recover(self, operation_id: Optional[str] = None) -> Tuple[MigrationResult, ...]:
        # Recovery is explicitly separate from ordinary open; it still takes a
        # fresh read-only schema snapshot before replaying a selected operation.
        initial = self.inspect()
        ledger = self._ledger()
        records = (
            [ledger.get(operation_id)]
            if operation_id
            else ledger.list_recovery(self.canonical_project_id)
        )
        results: List[MigrationResult] = []
        for record in records:
            plan = self._operation_plan(record)
            if record.status in TERMINAL_STATES:
                if record.status == STATUS_COMPLETED:
                    self._cleanup_terminal_evidence(record, initial)
                    results.append(
                        self._result(
                            record,
                            STATUS_COMPLETED,
                            plan=plan,
                            requires_reopen=True,
                            message="项目格式已升级。请重新打开项目后继续使用。",
                            next_action="重新打开项目",
                        )
                    )
                elif record.status == STATUS_ROLLED_BACK:
                    self._cleanup_terminal_evidence(record, initial)
                continue
            try:
                self._hook("migration.recovery.before")
                result = self._resume_or_execute(record, plan)
                self._hook("migration.recovery.after")
                results.append(result)
            except MigrationError as exc:
                current = ledger.get(record.operation_id)
                if current.status in TERMINAL_STATES:
                    results.append(self._result(current, current.status, plan=plan))
                else:
                    raise exc
        return tuple(results)

    recover_pending = recover
    startup_recovery_scan = recover

    def open_project(self) -> ProjectSchemaInspection:
        initial = self.inspect()
        # The read-only inspector remains first.  The subsequent root-ledger
        # scan is the only durable lookup needed to detect crash leftovers.
        records = self._ledger().list_for_project(self.canonical_project_id)
        if any(record.status == STATUS_RETAINED_FOR_TRIAGE for record in records):
            raise MigrationError("migration_rollback_failed")
        for record in records:
            self._cleanup_terminal_evidence(record, initial)
        pending = [record for record in records if record.status in PUBLIC_RECOVERY_STATES]
        if pending:
            self.recover()
            return self.inspect()
        return initial


    def apply_callback(
        self,
        operation_id: str,
        *,
        plan_digest: str,
        expected_state: str,
        **updates: Any,
    ) -> MigrationOperation:
        return self._ledger().apply_callback(
            operation_id,
            plan_digest=plan_digest,
            expected_state=expected_state,
            **updates,
        )


__all__ = [name for name in globals() if not name.startswith("__")]
