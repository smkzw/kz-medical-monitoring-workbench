"""Migration backup, staging, and member-step execution."""

from .migration_contracts import *
from .migration_oracles import *
from .migration_steps import *


class MigrationExecutionMixin:
    def start_upgrade(
        self,
        idempotency_key: str,
        *,
        confirmation: bool = True,
        confirmed: Optional[bool] = None,
    ) -> MigrationResult:
        if confirmed is not None:
            confirmation = bool(confirmed)
        inspection = self.inspect()
        key = _safe_key(idempotency_key)
        ledger = self._ledger()
        records = ledger.list_for_project(self.canonical_project_id)
        existing: Optional[MigrationOperation] = None
        for candidate in records:
            if candidate.idempotency_key == key:
                existing = candidate
                break
        if any(candidate.status == STATUS_RETAINED_FOR_TRIAGE for candidate in records):
            raise MigrationError("migration_rollback_failed")

        if existing is not None:
            if existing.status == STATUS_MIGRATION_OPERATION_CONFLICT:
                raise MigrationError("migration_operation_conflict")
            plan = self._operation_plan(existing)
            if existing.status == STATUS_COMPLETED:
                self._cleanup_terminal_evidence(existing, inspection)
                return self._result(
                    existing,
                    STATUS_COMPLETED,
                    plan=plan,
                    requires_reopen=True,
                    message="项目格式已升级。请重新打开项目后继续使用。",
                    next_action="重新打开项目",
                )
            if existing.status == STATUS_ROLLED_BACK:
                self._cleanup_terminal_evidence(existing, inspection)
                return self._result(
                    existing,
                    STATUS_ROLLED_BACK,
                    plan=plan,
                    message="升级未完成，原项目仍可只读查看。可稍后重试。",
                    next_action="稍后重试升级",
                )
            if not confirmation:
                return self._result(
                    existing,
                    STATUS_LEGACY_READONLY,
                    plan=plan,
                    message="项目格式较旧，当前可以只读查看。",
                    next_action="开始升级或稍后处理",
                )
            directory_recovery = existing.status in {
                STATUS_SWITCHING,
                STATUS_LIVE_VERIFYING,
                STATUS_ROLLBACK_IN_PROGRESS,
            }
            if (
                not directory_recovery
                and inspection.classification
                not in {SchemaClassification.LEGACY, SchemaClassification.CURRENT}
            ):
                raise MigrationError("migration_not_supported")
            if inspection.classification is SchemaClassification.LEGACY:
                self._ensure_complete_legacy(inspection)
            try:
                if existing.status in {
                    STATUS_SWITCHING,
                    STATUS_LIVE_VERIFYING,
                    STATUS_ROLLBACK_IN_PROGRESS,
                }:
                    current = ledger.get(existing.operation_id)
                else:
                    self._ledger_update(
                        existing.operation_id,
                        status=STATUS_INSPECTING,
                        progress_percent=PROGRESS_INSPECTION_COMPLETE,
                        current_step="项目检查完成",
                        payload=plan.as_dict(),
                    )
                    current = ledger.get(existing.operation_id)
                return self._resume_or_execute(current, plan)
            except MigrationError:
                raise
            except (
                ProjectBackupError,
                MaintenanceGateError,
                sqlite3.Error,
                OSError,
                ValueError,
                TypeError,
            ) as exc:
                self._safe_failure(existing.operation_id, "sqlite_integrity_failed", str(exc))
                raise MigrationError("sqlite_integrity_failed") from exc

        if inspection.classification is SchemaClassification.CURRENT:
            return self._result(
                None,
                STATUS_ALREADY_CURRENT,
                message="项目格式已是当前版本。",
                next_action="继续使用项目",
            )
        if inspection.classification is not SchemaClassification.LEGACY:
            raise MigrationError("migration_not_supported")
        self._ensure_complete_legacy(inspection)
        plan = MigrationPlan.from_inspection(inspection)
        if not confirmation:
            return self._result(
                None,
                STATUS_LEGACY_READONLY,
                plan=plan,
                message="项目格式较旧，当前可以只读查看。",
                next_action="开始升级或稍后处理",
            )
        record = ledger.create_or_replay(
            key,
            self.canonical_project_id,
            source_schema_set_digest=plan.source_schema_set_digest,
            target_schema_set_digest=plan.target_schema_set_digest,
            plan_digest=plan.plan_digest,
            plan=plan.as_dict(),
        )
        try:
            self._ledger_update(
                record.operation_id,
                status=STATUS_INSPECTING,
                progress_percent=PROGRESS_INSPECTION_COMPLETE,
                current_step="项目检查完成",
                payload=plan.as_dict(),
            )
            current = ledger.get(record.operation_id)
            return self._resume_or_execute(current, plan)
        except MigrationError:
            raise
        except (
            ProjectBackupError,
            MaintenanceGateError,
            sqlite3.Error,
            OSError,
            ValueError,
            TypeError,
        ) as exc:
            self._safe_failure(record.operation_id, "sqlite_integrity_failed", str(exc))
            raise MigrationError("sqlite_integrity_failed") from exc

    upgrade = start_upgrade
    migrate = start_upgrade

    def _ledger_update(self, operation_id: str, **updates: Any) -> MigrationOperation:
        self._hook("migration.ledger_commit.before")
        record = self._ledger().update(operation_id, **updates)
        try:
            self._hook("migration.ledger_commit.after")
        except BaseException as exc:
            # The row is durable; retry/recovery must inspect actual stage state.
            raise _CommittedStepFailure("migration.ledger_commit.after", exc) from exc
        return record

    def _safe_failure(self, operation_id: str, code: str, detail: str = "") -> None:
        try:
            self._ledger().update(
                operation_id,
                status=STATUS_RETRYABLE_FAILED,
                error_code=code,
                error_message=_ERROR_MESSAGES.get(code, detail or "项目升级未完成。"),
                terminal_outcome=None,
            )
        except BaseException:
            pass

    def _operation_plan(self, record: MigrationOperation) -> MigrationPlan:
        payload = record.payload
        if "steps" not in payload:
            raise MigrationError("migration_ledger_corrupt")
        return MigrationPlan.from_mapping(payload)

    def _live_fingerprint(self, manager: ProjectBackupManager) -> str:
        try:
            # 09A fingerprints a consistent SQLite snapshot, not the main
            # database header while a WAL sidecar is active.  Reuse that
            # helper so the comparison is byte-identical to the backup
            # manifest and remains read-only for live project files.
            snapshot = manager.snapshot_workspace(
                "migration-fingerprint-" + self.canonical_project_id
            )
            return snapshot.fingerprint
        except MigrationError:
            raise
        except (ProjectBackupError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise MigrationError("migration_project_blocked") from exc

    def _prepare_backup(self, record: MigrationOperation, plan: MigrationPlan) -> MigrationOperation:
        manager = self._backup_manager()
        self._ledger_update(
            record.operation_id,
            status=STATUS_BACKUP_REQUIRED,
            progress_percent=PROGRESS_INSPECTION_COMPLETE,
            current_step="等待准备恢复点",
        )
        try:
            self._ledger_update(
                record.operation_id,
                status=STATUS_BACKUP_IN_PROGRESS,
                progress_percent=PROGRESS_INSPECTION_COMPLETE,
                current_step="正在准备恢复点",
            )
            backup = manager.backup("migration-backup-" + record.idempotency_key)
            if backup.package_path is None or backup.package_id is None:
                raise MigrationError("migration_project_blocked")
            manifest = dict(backup.manifest)
            source_fp = str(backup.source_workspace_fingerprint or manifest.get("source_workspace_fingerprint", ""))
            if not source_fp or source_fp != manifest.get("source_workspace_fingerprint"):
                raise MigrationError("migration_project_blocked")
            # 09A backup() already performs closure and reopen verification.  A
            # second preflight validates the published package independently.
            preflight = manager.preflight(
                backup.package_path,
                "migration-preflight-" + record.idempotency_key,
            )
            if preflight.staging_path is not None:
                manager._cleanup_path(preflight.staging_path.parent)
            payload = dict(plan.as_dict())
            payload.update(
                {
                    "package_id": backup.package_id,
                    "package_path": str(backup.package_path),
                    "source_workspace_fingerprint": source_fp,
                    "source_manifest": manifest,
                    "member_step_digests": dict(plan.member_step_digests),
                }
            )
            return self._ledger_update(
                record.operation_id,
                status=STATUS_BACKUP_VERIFIED,
                progress_percent=PROGRESS_BACKUP_VERIFIED,
                current_step="恢复点已完成",
                package_id=backup.package_id,
                package_path=str(backup.package_path),
                source_workspace_fingerprint=source_fp,
                payload=payload,
            )
        except MigrationError:
            raise
        except (ProjectBackupError, MaintenanceGateError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            self._safe_failure(record.operation_id, "migration_project_blocked", str(exc))
            raise MigrationError("migration_project_blocked") from exc

    def _gate_event(self, operation_id: str, event: str) -> None:
        try:
            if event == "waiting_for_project":
                self._ledger().update(
                    operation_id,
                    status=STATUS_WAITING_FOR_PROJECT,
                    current_step="正在等待项目空闲",
                    maintenance_state=event,
                )
            elif event == "maintenance_acquired":
                self._ledger().update(
                    operation_id,
                    status=STATUS_MAINTENANCE_ACQUIRED,
                    progress_percent=PROGRESS_PROJECT_IDLE,
                    current_step="项目已空闲",
                    maintenance_state=event,
                )
            else:
                self._ledger().update(operation_id, maintenance_state=event)
        except BaseException:
            # A progress observation must not leak the maintenance lock.
            pass

    def _staging_paths(self, operation_id: str) -> Tuple[Path, Path]:
        operation_id = _safe_operation_id(operation_id)
        parent = self.staging_root / operation_id
        return parent, parent / "workspace"

    def _rollback_path(self, operation_id: str) -> Path:
        operation_id = _safe_operation_id(operation_id)
        return self.rollback_root / (self.canonical_project_id + "-" + operation_id)

    def _ensure_staging(
        self,
        record: MigrationOperation,
        manager: ProjectBackupManager,
        source_oracle: Mapping[str, Any],
    ) -> Tuple[Path, WorkspaceSnapshot, Mapping[str, bytes]]:
        parent, workspace = self._staging_paths(record.operation_id)
        if record.staging_path:
            recorded = Path(record.staging_path)
            if recorded != parent:
                raise MigrationError("migration_operation_conflict")
        if parent.exists() and not _replaceable(parent):
            raise MigrationError("migration_operation_conflict")
        if parent.exists() and workspace.exists():
            _assert_directory(workspace)
            _remove_sqlite_sidecars(workspace)
            _assert_no_sqlite_sidecars(workspace)
            members = manager.member_bytes(workspace)
            return parent, WorkspaceSnapshot(
                workspace,
                members,
                {},
                workspace_fingerprint(members),
            ), members
        if parent.exists() and not workspace.exists():
            manager._cleanup_path(parent)
        self._hook("migration.staging_create.before")
        _assert_directory(self.runtime_root)
        self.staging_root.mkdir(parents=True, exist_ok=True)
        parent.mkdir(parents=True, exist_ok=False)
        _assert_same_device(self.runtime_root, self.staging_root, parent)
        try:
            snapshot = manager.snapshot_workspace(
                record.operation_id,
                destination=workspace,
                emit_hooks=False,
            )
            _remove_sqlite_sidecars(workspace)
            _assert_no_sqlite_sidecars(workspace)
            stage_oracle = _workspace_oracle(workspace)
            _compare_database_oracles(source_oracle, stage_oracle)
            source_artifacts = _artifact_hashes_and_bytes(manager, self.workspace_dir)
            stage_artifacts = _artifact_hashes_and_bytes(manager, workspace)
            _compare_artifacts(source_artifacts, stage_artifacts)
            self._hook("migration.staging_create.after")
            return parent, snapshot, snapshot.members
        except BaseException:
            manager._cleanup_path(parent)
            raise

    def _verify_stage_current(
        self,
        manager: ProjectBackupManager,
        stage_workspace: Path,
        source_oracle: Mapping[str, Any],
        source_artifacts: Mapping[str, bytes],
    ) -> None:
        inspection = ProjectSchemaInspector(stage_workspace).inspect()
        if inspection.classification is not SchemaClassification.CURRENT:
            raise MigrationError("migration_verification_failed")
        stage_oracle = _workspace_oracle(stage_workspace)
        _compare_database_oracles(source_oracle, stage_oracle)
        stage_artifacts = _artifact_hashes_and_bytes(manager, stage_workspace)
        _compare_artifacts(source_artifacts, stage_artifacts)
        _assert_no_sqlite_sidecars(stage_workspace)
        runtime = stage_workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        if runtime.is_file():
            connection = _open_ro(runtime)
            try:
                manager._verify_audit_chain(connection)
            except ProjectBackupError as exc:
                raise MigrationError("migration_verification_failed") from exc
            finally:
                connection.close()

    def _step_target_applied(self, step: MigrationStep, stage_workspace: Path) -> bool:
        path = self._member_path(stage_workspace, step.member)
        if path is None or not path.is_file():
            return False
        report = inspect_member(path, step.member)
        if step.member == RUNTIME_MEMBER:
            return report.classification is SchemaClassification.CURRENT and report.schema_version == RUNTIME_V6
        return report.classification is SchemaClassification.CURRENT and report.schema_version == LAUNCH_V4

    @staticmethod
    def _member_path(workspace: Path, member: str) -> Optional[Path]:
        relative = {
            RUNTIME_MEMBER: Path(RUNTIME_DIR_NAME) / RUNTIME_DB_NAME,
            PROFILE_MEMBER: Path(PROFILE_DB_NAME),
            BINDING_MEMBER: Path(RUN_BINDING_DB_NAME),
            LAUNCH_MEMBER: Path(LAUNCH_REGISTRY_DB_NAME),
            RISK_MEMBER: Path(RISK_RULE_DB_NAME),
        }.get(member)
        return None if relative is None else workspace / relative

    def _run_steps(
        self,
        record: MigrationOperation,
        plan: MigrationPlan,
        stage_workspace: Path,
    ) -> MigrationOperation:
        source_oracle = _workspace_oracle(self.workspace_dir)
        manager = self._backup_manager()
        source_artifacts = _artifact_hashes_and_bytes(manager, self.workspace_dir)
        current = record
        for step in plan.steps:
            if self._step_target_applied(step, stage_workspace):
                current = self._ledger_update(
                    current.operation_id,
                    status=STATUS_MIGRATING,
                    progress_percent=PROGRESS_CONTENT_UPDATED,
                    current_step="%s内容已更新" % step.member,
                    current_member=step.member,
                    member_step_digest=step.step_digest,
                )
                continue
            current = self._ledger_update(
                current.operation_id,
                status=STATUS_MIGRATING,
                progress_percent=PROGRESS_CONTENT_UPDATED,
                current_step="正在更新%s" % step.member,
                current_member=step.member,
                member_step_digest=step.step_digest,
            )
            runner = _StepRunner(self, step)
            try:
                runner.run(self._member_path(stage_workspace, step.member) or Path(""))
            except _CommittedStepFailure:
                raise
            except BaseException:
                if runner.committed:
                    raise _CommittedStepFailure("migration.%s.commit.after" % step.member, RuntimeError("committed"))
                raise
            if not self._step_target_applied(step, stage_workspace):
                raise MigrationError("migration_verification_failed")
            current = self._ledger_update(
                current.operation_id,
                status=STATUS_MIGRATING,
                progress_percent=PROGRESS_CONTENT_UPDATED,
                current_step="%s内容已更新" % step.member,
                current_member=step.member,
                member_step_digest=step.step_digest,
            )
        self._hook("migration.project_oracle.before")
        self._verify_stage_current(manager, stage_workspace, source_oracle, source_artifacts)
        self._hook("migration.project_oracle.after")
        return self._ledger_update(
            current.operation_id,
            status=STATUS_STAGED_VERIFIED,
            progress_percent=PROGRESS_STAGED_VERIFIED,
            current_step="升级副本核验完成",
            current_member=None,
            member_step_digest=None,
        )

    def _checkpoint_workspace(self, workspace: Path) -> None:
        for relative in _member_rel_paths(workspace):
            if relative.endswith(".json") or relative.endswith("/artifacts"):
                continue
            path = workspace / Path(relative)
            if not path.is_file():
                continue
            connection: Optional[sqlite3.Connection] = None
            try:
                connection = sqlite3.connect(str(path), timeout=0.0, isolation_level=None)
                connection.execute("PRAGMA busy_timeout=0")
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                connection.execute("PRAGMA journal_mode=DELETE")
            except sqlite3.OperationalError as exc:
                raise MigrationError("project_busy_retry_later") from exc
            except sqlite3.Error as exc:
                raise MigrationError("migration_verification_failed") from exc
            finally:
                if connection is not None:
                    connection.close()

    def _quiesce_live(self, manager: ProjectBackupManager) -> None:
        self._hook("migration.live_quiesce.before")
        try:
            manager._quiesce()
        except ProjectBackupError as exc:
            raise MigrationError(exc.code) from exc
        self._hook("migration.live_quiesce.after")

    def _verify_live_target(
        self,
        manager: ProjectBackupManager,
        expected_oracle: Mapping[str, Any],
        expected_artifacts: Mapping[str, bytes],
    ) -> None:
        self._hook("migration.live_reopen.before")
        inspection = ProjectSchemaInspector(self.workspace_dir).inspect()
        if inspection.classification is not SchemaClassification.CURRENT:
            raise MigrationError("migration_verification_failed")
        actual_oracle = _workspace_oracle(self.workspace_dir)
        _compare_database_oracles(expected_oracle, actual_oracle)
        actual_artifacts = _artifact_hashes_and_bytes(manager, self.workspace_dir)
        _compare_artifacts(expected_artifacts, actual_artifacts)
        _assert_no_sqlite_sidecars(self.workspace_dir)
        for relative in _member_rel_paths(self.workspace_dir):
            if relative.endswith(".json"):
                continue
            connection = _open_ro(self.workspace_dir / Path(relative))
            connection.close()
        self._hook("migration.live_reopen.after")
        self._hook("migration.identity_verification.before")
        if actual_oracle.get("project_ids") and actual_oracle.get("project_ids") != [self.canonical_project_id]:
            raise MigrationError("migration_verification_failed")
        self._hook("migration.identity_verification.after")

    def _mark_rollback_in_progress(self, operation_id: str) -> None:
        try:
            self._ledger().update(
                operation_id,
                status=STATUS_ROLLBACK_IN_PROGRESS,
                current_step="正在恢复原项目",
                directory_switch_stage="rollback_in_progress",
            )
        except BaseException:
            # Safety action continues even if the observability write is down.
            pass

    def _rollback_after_failure(
        self,
        record: MigrationOperation,
        rollback_path: Path,
        stage_parent: Path,
    ) -> bool:
        try:
            self._hook("migration.rollback.before")
            failed_live = stage_parent / "failed-live"
            if self.workspace_dir.exists():
                if failed_live.exists():
                    self._backup_manager()._cleanup_path(failed_live)
                _replace_or_raise(self.workspace_dir, failed_live)
            if rollback_path.exists():
                _replace_or_raise(rollback_path, self.workspace_dir)
            ProjectBackupManager._fsync_dir(self.runtime_root)
            self._hook("migration.rollback.after")
            return self.workspace_dir.is_dir()
        except BaseException:
            return False

    def _verify_source_workspace(
        self,
        manager: ProjectBackupManager,
        record: MigrationOperation,
        workspace: Path,
    ) -> None:
        if not workspace.is_dir():
            raise MigrationError("workspace_not_found")
        package_path = Path(record.package_path or "")
        if not package_path.is_file():
            raise MigrationError("migration_project_blocked")
        source_operation = "migration-source-" + record.operation_id
        fallback_parent = self.runtime_root / ".mmbackup-staging" / source_operation
        fallback_preexisting = fallback_parent.exists()
        source_manager = ProjectBackupManager(
            self.runtime_root,
            self.canonical_project_id,
            workspace_dir=workspace,
            ledger=manager.ledger,
            wait_seconds=self.wait_seconds,
            max_archive_members=manager.max_archive_members,
            max_member_bytes=manager.max_member_bytes,
            max_archive_bytes=manager.max_archive_bytes,
        )
        try:
            manifest, extracted_parent, _, package_id = source_manager._inspect_archive(
                source_operation,
                package_path,
            )
            if record.package_id is None or package_id != record.package_id:
                raise MigrationError("migration_operation_conflict")
            source_workspace = extracted_parent / "workspace"
            source_manager._verify_workspace(
                source_workspace,
                manifest,
                verify_manifest_summary=True,
            )
            expected_oracle = _workspace_oracle(source_workspace)
            expected_artifacts = _artifact_hashes_and_bytes(source_manager, source_workspace)
            inspection = ProjectSchemaInspector(workspace).inspect()
            if inspection.classification is not SchemaClassification.LEGACY:
                raise MigrationError("migration_verification_failed")
            actual_oracle = _workspace_oracle(workspace)
            _compare_database_oracles(expected_oracle, actual_oracle)
            actual_artifacts = _artifact_hashes_and_bytes(manager, workspace)
            _compare_artifacts(expected_artifacts, actual_artifacts)
        except MigrationError:
            raise
        except (ProjectBackupError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
            raise MigrationError("migration_project_blocked") from exc
        finally:
            if extracted_parent is not None or not fallback_preexisting:
                source_manager._cleanup_path(extracted_parent or fallback_parent)


__all__ = [name for name in globals() if not name.startswith("__")]
