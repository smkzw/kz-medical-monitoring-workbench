"""Atomic project restore, verification, and rollback operations."""

from .project_backup_support import *


class ProjectBackupRestoreMixin:
    def restore(
        self,
        package: Union[str, Path, PreflightResult],
        idempotency_key: Optional[str] = None,
        *,
        confirmation: bool = False,
        confirmed: Optional[bool] = None,
        preflight_result: Optional[PreflightResult] = None,
        operation_id: Optional[str] = None,
        reserved_operation_id: Optional[str] = None,
    ) -> RestoreResult:
        if confirmed is not None:
            confirmation = bool(confirmed)
        package_path = self._package_path(package)
        try:
            package_id = sha256_hex(package_path.read_bytes())
        except OSError as exc:
            raise ProjectBackupError("package_corrupt") from exc
        key = _required_key(idempotency_key) if idempotency_key is not None else "restore-" + package_id
        record = self.ledger.create_or_replay(
            OP_RESTORE,
            key,
            self.canonical_project_id,
            package_id=package_id,
            initial_status=STATUS_CONFIRMED,
        )
        reserved_owner = False
        if reserved_operation_id is not None:
            if (
                not isinstance(reserved_operation_id, str)
                or _SAFE_OPERATION_ID.fullmatch(reserved_operation_id) is None
                or not record.replayed
                or record.operation_id != reserved_operation_id
                or (
                    operation_id is not None
                    and operation_id != reserved_operation_id
                )
            ):
                raise ProjectBackupError("backup_operation_conflict")
        if (
            record.replayed
            and record.status == STATUS_FAILED
            and record.error_code == "project_busy_retry_later"
        ):
            record = self.ledger.update(
                record.operation_id,
                status=STATUS_CONFIRMED,
                current_step="恢复请求已重新开始",
                error_code="",
                error_message="",
                terminal_outcome="",
                allow_terminal_reopen=True,
            )
            if reserved_operation_id is not None:
                reserved_owner = True
        if (
            reserved_operation_id is not None
            and not reserved_owner
            and record.status
            not in {
                STATUS_COMPLETED,
                STATUS_ALREADY_CURRENT,
                STATUS_RETAINED_FOR_TRIAGE,
                STATUS_FAILED,
            }
        ):
            record = dataclass_replace(record, replayed=False)
            reserved_owner = True
        if record.replayed and record.status in {
            STATUS_COMPLETED,
            STATUS_ALREADY_CURRENT,
            STATUS_RETAINED_FOR_TRIAGE,
        }:
            return self._restore_result_from_record(record)
        if preflight_result is None:
            preflight_result = self.preflight(
                package_path,
                idempotency_key="restore-preflight-" + key,
            )
        if preflight_result.package_id != package_id:
            raise ProjectBackupError("backup_operation_conflict")
        if preflight_result.decision == "blocked":
            raise ProjectBackupError("rollback_requires_review")
        if preflight_result.decision == "already_current":
            payload = {
                "result_label": "项目已是此版本",
                "project_name": preflight_result.project_name,
                "restored_cutoff_label": preflight_result.backup_cutoff_label,
                "verification_summary": "项目状态与备份版本一致",
                "next_action_label": "继续查看当前监查结果",
            }
            final_record = self._record_update(
                record.operation_id,
                OP_RESTORE,
                status=STATUS_ALREADY_CURRENT,
                progress_percent=PROGRESS_COMPLETE,
                current_step="恢复完成",
                terminal_outcome=STATUS_ALREADY_CURRENT,
                payload=payload,
            )
            return RestoreResult(
                operation=final_record,
                result_label="项目已是此版本",
                project_name=preflight_result.project_name,
                restored_cutoff_label=preflight_result.backup_cutoff_label,
                verification_summary="项目状态与备份版本一致",
                next_action_label="继续查看当前监查结果",
            )
        if preflight_result.confirmation_required and not confirmation:
            payload = {
                "result_label": "保持原项目未变",
                "project_name": preflight_result.project_name,
                "restored_cutoff_label": preflight_result.current_cutoff_label,
                "verification_summary": "尚未确认恢复，当前项目未变",
                "next_action_label": "确认后再恢复此备份",
            }
            kept = self._record_update(
                record.operation_id,
                OP_RESTORE,
                status=STATUS_KEPT_CURRENT,
                progress_percent=PROGRESS_RECONCILIATION_COMPLETE,
                current_step="等待恢复确认",
                terminal_outcome=STATUS_KEPT_CURRENT,
                payload=payload,
            )
            raise ProjectBackupError("restore_confirmation_required")
        stage_parent = (
            preflight_result.staging_path
            if preflight_result.staging_path is not None
            else self.runtime_root / STAGING_DIR_NAME / record.operation_id
        )
        stage_workspace = stage_parent / "workspace"
        rollback_path = self.runtime_root / (
            ".rollback-" + sha256_hex(self.canonical_project_id.encode("utf-8"))[:24] + "-" + record.operation_id
        )
        old_live_moved = False
        try:
            with self._gate(record.operation_id).exclusive():
                if reserved_owner:
                    latest = self.ledger.get(record.operation_id)
                    if latest.status in {
                        STATUS_COMPLETED,
                        STATUS_ALREADY_CURRENT,
                        STATUS_RETAINED_FOR_TRIAGE,
                    }:
                        return self._restore_result_from_record(latest)
                    record = latest
                current_summary, current_fp = self._current_state(record.operation_id)
                if current_fp != preflight_result.current_workspace_fingerprint:
                    raise ProjectBackupError("restore_source_changed")
                if self._existing_rollbacks():
                    raise ProjectBackupError("rollback_requires_review")
                self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_STAGING,
                    progress_percent=PROGRESS_STAGING_COMPLETE,
                    current_step="恢复副本已准备",
                    staging_path=str(stage_parent),
                )
                if self.failure_hook is not None:
                    self._hook("preflight.staging_workspace_verification.before")
                self._verify_workspace(stage_workspace, preflight_result.manifest, verify_manifest_summary=True)
                if self.failure_hook is not None:
                    self._hook("preflight.staging_workspace_verification.after")
                self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_VERIFYING_STAGED_WORKSPACE,
                    progress_percent=PROGRESS_MEMBER_VERIFICATION_COMPLETE,
                    current_step="恢复前检查已完成",
                )
                if self.failure_hook is not None:
                    self._hook("restore.quiesce.before")
                self._quiesce()
                if self.failure_hook is not None:
                    self._hook("restore.quiesce.after")
                if rollback_path.exists():
                    raise ProjectBackupError("rollback_requires_review")
                if os.stat(self.runtime_root).st_dev != os.stat(stage_parent).st_dev:
                    raise ProjectBackupError("restore_switch_failed")
                rollback_path.parent.mkdir(parents=True, exist_ok=True)
                self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_SWITCHING,
                    progress_percent=PROGRESS_STAGING_COMPLETE,
                    current_step="正在切换项目版本",
                )
                if self.workspace_dir.exists():
                    if self.failure_hook is not None:
                        self._hook("restore.current_to_rollback.before")
                    os.replace(str(self.workspace_dir), str(rollback_path))
                    old_live_moved = True
                    self._fsync_dir(self.runtime_root)
                    if self.failure_hook is not None:
                        self._hook("restore.current_to_rollback.after")
                if self.failure_hook is not None:
                    self._hook("restore.staging_to_live.before")
                os.replace(str(stage_workspace), str(self.workspace_dir))
                self._fsync_dir(self.runtime_root)
                if self.failure_hook is not None:
                    self._hook("restore.staging_to_live.after")
                self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_VERIFYING_LIVE_WORKSPACE,
                    progress_percent=PROGRESS_RECONCILIATION_COMPLETE,
                    current_step="正在重新核对项目",
                )
                live_summary, _, live_fp = self._verify_live_workspace(preflight_result.manifest)
                if live_fp != preflight_result.source_workspace_fingerprint or live_summary != preflight_result.manifest.get("project_summary"):
                    raise ProjectBackupError("restore_verification_failed")
                payload = {
                    "result_label": "恢复完成",
                    "project_name": preflight_result.project_name,
                    "restored_cutoff_label": preflight_result.backup_cutoff_label,
                    "verification_summary": "项目、监查结果、风险规则和连续性资料已重新核对",
                    "next_action_label": "继续查看监查结果",
                    "manifest": dict(preflight_result.manifest),
                }
                final_record = self._record_update(
                    record.operation_id,
                    OP_RESTORE,
                    status=STATUS_COMPLETED,
                    progress_percent=PROGRESS_COMPLETE,
                    current_step="恢复完成",
                    rollback_path=str(rollback_path) if old_live_moved else "",
                    staging_path="",
                    payload=payload,
                )
                self._cleanup_path(stage_parent)
                return RestoreResult(
                    operation=final_record,
                    result_label="恢复完成",
                    project_name=preflight_result.project_name,
                    restored_cutoff_label=preflight_result.backup_cutoff_label,
                    verification_summary="项目、监查结果、风险规则和连续性资料已重新核对",
                    next_action_label="继续查看监查结果",
                    rollback_path=rollback_path if old_live_moved else None,
                )
        except ProjectBusyError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except MaintenanceGateError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except ProjectBackupError as exc:
            rolled_back = self._rollback_after_failure(
                record.operation_id,
                rollback_path,
                stage_parent,
                old_live_moved=old_live_moved,
            )
            if rolled_back:
                self._safe_record_update(
                    record.operation_id,
                    status=STATUS_FAILED,
                    error_code=exc.code,
                    error_message=exc.message,
                    rollback_path=None,
                    staging_path=str(stage_parent) if stage_parent.exists() else None,
                )
                if not stage_parent.exists():
                    self._cleanup_path(stage_parent)
            else:
                retained_path = rollback_path
                failed_live = stage_parent / "failed-live"
                if retained_path is None or not retained_path.exists():
                    retained_path = failed_live if failed_live.exists() else stage_parent
                self._safe_record_update(
                    record.operation_id,
                    status=STATUS_RETAINED_FOR_TRIAGE,
                    terminal_outcome=STATUS_RETAINED_FOR_TRIAGE,
                    error_code="restore_rollback_failed",
                    error_message=_ERROR_MESSAGES["restore_rollback_failed"],
                    rollback_path=str(retained_path),
                    staging_path=str(stage_parent),
                )
                raise ProjectBackupError("restore_rollback_failed") from exc
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            wrapped = ProjectBackupError("restore_switch_failed")
            rolled_back = self._rollback_after_failure(
                record.operation_id,
                rollback_path,
                stage_parent,
                old_live_moved=old_live_moved,
            )
            if not rolled_back:
                retained_path = rollback_path
                failed_live = stage_parent / "failed-live"
                if retained_path is None or not retained_path.exists():
                    retained_path = failed_live if failed_live.exists() else stage_parent
                self._safe_record_update(
                    record.operation_id,
                    status=STATUS_RETAINED_FOR_TRIAGE,
                    terminal_outcome=STATUS_RETAINED_FOR_TRIAGE,
                    error_code="restore_rollback_failed",
                    error_message=_ERROR_MESSAGES["restore_rollback_failed"],
                    rollback_path=str(retained_path),
                    staging_path=str(stage_parent),
                )
                raise ProjectBackupError("restore_rollback_failed") from exc
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code=wrapped.code,
                error_message=wrapped.message,
                staging_path=str(stage_parent) if stage_parent.exists() else None,
            )
            raise wrapped from exc

    restore_backup = restore
    import_restore = restore

    def rollback(self, operation: Union[str, OperationRecord, RestoreResult]) -> RestoreResult:
        if isinstance(operation, RestoreResult):
            operation_id = operation.operation_id
        elif isinstance(operation, OperationRecord):
            operation_id = operation.operation_id
        else:
            operation_id = str(operation)
        record = self.ledger.get(operation_id)
        if not record.rollback_path:
            raise ProjectBackupError("operation_not_found")
        rollback_path = Path(record.rollback_path)
        if not rollback_path.exists():
            raise ProjectBackupError("restore_rollback_failed")
        stage_parent = self.runtime_root / STAGING_DIR_NAME / (operation_id + "-manual-rollback")
        if stage_parent.exists():
            raise ProjectBackupError("backup_operation_conflict")
        stage_parent.mkdir(parents=True, exist_ok=False)
        try:
            with self._gate(operation_id).exclusive():
                self._hook("restore.rollback.before")
                if self.workspace_dir.exists():
                    os.replace(str(self.workspace_dir), str(stage_parent / "current-live"))
                os.replace(str(rollback_path), str(self.workspace_dir))
                self._fsync_dir(self.runtime_root)
                self._verify_workspace_independent(self.workspace_dir)
                self._hook("restore.rollback.after")
                payload = {
                    "result_label": "恢复完成",
                    "project_name": self.project_name or self.canonical_project_id,
                    "restored_cutoff_label": "",
                    "verification_summary": "原项目版本已重新打开并核对",
                    "next_action_label": "继续查看监查结果",
                }
                final = self._safe_update_result(
                    operation_id,
                    status=STATUS_COMPLETED,
                    progress_percent=PROGRESS_COMPLETE,
                    current_step="恢复完成",
                    terminal_outcome=STATUS_COMPLETED,
                    rollback_path=str(stage_parent / "current-live"),
                    staging_path="",
                    payload=payload,
                )
                return RestoreResult(
                    operation=final,
                    result_label="恢复完成",
                    project_name=self.project_name or self.canonical_project_id,
                    restored_cutoff_label="",
                    verification_summary="原项目版本已重新打开并核对",
                    next_action_label="继续查看监查结果",
                    rollback_path=stage_parent / "current-live",
                )
        except ProjectBackupError:
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise ProjectBackupError("restore_rollback_failed") from exc

    def _safe_update_result(self, operation_id: str, **kwargs: Any) -> OperationRecord:
        return self.ledger.update(operation_id, allow_terminal_reopen=True, **kwargs)

    def get_operation(self, operation_id: str) -> OperationRecord:
        return self.ledger.get(operation_id)

    status = get_operation
    operation_status = get_operation
