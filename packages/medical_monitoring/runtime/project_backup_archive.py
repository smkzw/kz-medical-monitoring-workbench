"""Deterministic project backup packaging and restore preflight."""

from .project_backup_support import *


class ProjectBackupArchiveMixin:
    def backup(
        self,
        idempotency_key: Optional[str] = None,
        *,
        operation_id: Optional[str] = None,
        reserved_operation_id: Optional[str] = None,
    ) -> BackupResult:
        key = _required_key(idempotency_key) if idempotency_key is not None else "backup-" + uuid.uuid4().hex
        try:
            record = self.ledger.create_or_replay(OP_BACKUP, key, self.canonical_project_id)
        except MaintenanceGateError as exc:
            raise ProjectBackupError(exc.code, exc.message) from exc
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
            if record.status not in {STATUS_AVAILABLE, STATUS_FAILED}:
                record = dataclass_replace(record, replayed=False)
                reserved_owner = True
        op_id = operation_id or record.operation_id
        stage_parent = self.runtime_root / STAGING_DIR_NAME / op_id
        stage_workspace = stage_parent / "workspace"
        temp_package = self.runtime_root / ("." + op_id + ".mmbackup.tmp")
        if record.replayed and record.status not in {STATUS_AVAILABLE, STATUS_FAILED}:
            joined = self._wait_for_replayed_operation(
                record,
                (STATUS_AVAILABLE, STATUS_FAILED),
            )
            if joined.status in {STATUS_AVAILABLE, STATUS_FAILED}:
                return self._backup_result(joined)
            if stage_parent.exists():
                raise ProjectBackupError("backup_operation_conflict")
            record = joined
        if record.replayed and record.status == STATUS_AVAILABLE:
            gate = self._gate(record.operation_id)
            try:
                with gate.exclusive():
                    current = self._current_snapshot(record.operation_id)
                    if current is None or current.fingerprint != record.source_workspace_fingerprint:
                        raise ProjectBackupError("backup_operation_conflict")
                    if record.package_path is None or not Path(record.package_path).is_file():
                        raise ProjectBackupError("backup_package_publish_failed")
                    return self._backup_result(record)
            except ProjectBusyError as exc:
                self._safe_record_update(
                    record.operation_id,
                    status=STATUS_FAILED,
                    error_code=exc.code,
                    error_message=exc.message,
                )
                raise ProjectBackupError(exc.code, exc.message) from exc
        if record.replayed and record.status == STATUS_FAILED and not record.source_workspace_fingerprint:
            return self._backup_result(record)
        try:
            with self._gate(record.operation_id).exclusive():
                if reserved_owner:
                    latest = self.ledger.get(record.operation_id)
                    if latest.status in {STATUS_AVAILABLE, STATUS_FAILED}:
                        return self._backup_result(latest)
                    record = latest
                    self._cleanup_path(stage_parent)
                    if temp_package.exists():
                        self._cleanup_path(temp_package)
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_COLLECTING,
                    progress_percent=PROGRESS_IDENTITY_CONFIRMED,
                    current_step="项目身份与状态已确认",
                )
                snapshot = self._snapshot_workspace(
                    record.operation_id,
                    destination=stage_workspace,
                    emit_hooks=True,
                )
                if (
                    record.source_workspace_fingerprint is not None
                    and record.source_workspace_fingerprint != snapshot.fingerprint
                ):
                    raise ProjectBackupError("backup_operation_conflict")
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_SNAPSHOTTING,
                    progress_percent=PROGRESS_SNAPSHOT_COMPLETE,
                    current_step="项目副本已准备",
                    source_workspace_fingerprint=snapshot.fingerprint,
                )
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_VERIFYING,
                    progress_percent=PROGRESS_ARTIFACT_CLOSURE_COMPLETE,
                    current_step="监查结果已核对",
                )
                manifest = self._build_manifest(snapshot)
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_VERIFYING,
                    progress_percent=PROGRESS_MEMBER_VERIFICATION_COMPLETE,
                    current_step="成员核验完成",
                )
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_PACKAGING,
                    progress_percent=PROGRESS_STAGING_COMPLETE,
                    current_step="备份文件正在生成",
                )
                package_id, published = self._write_package(
                    record.operation_id, manifest, snapshot.members
                )
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_PACKAGING,
                    progress_percent=PROGRESS_RECONCILIATION_COMPLETE,
                    current_step="最终对账完成",
                )
                final_record = self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_AVAILABLE,
                    progress_percent=PROGRESS_COMPLETE,
                    current_step="已可下载",
                    package_id=package_id,
                    source_workspace_fingerprint=snapshot.fingerprint,
                    terminal_outcome=STATUS_AVAILABLE,
                    package_path=str(published),
                    staging_path="",
                    payload={"manifest": manifest},
                )
                self._cleanup_path(stage_parent)
                return BackupResult(
                    operation=final_record,
                    package_id=package_id,
                    package_path=published,
                    source_workspace_fingerprint=snapshot.fingerprint,
                    manifest=manifest,
                )
        except ProjectBusyError as exc:
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code=exc.code,
                error_message=exc.message,
                staging_path=str(stage_parent),
            )
            self._cleanup_path(stage_parent)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except MaintenanceGateError as exc:
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code=exc.code,
                error_message=exc.message,
                staging_path=str(stage_parent),
            )
            self._cleanup_path(stage_parent)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except ProjectBackupError as exc:
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code=exc.code,
                error_message=exc.message,
                staging_path=str(stage_parent),
            )
            self._cleanup_path(stage_parent)
            if temp_package.exists():
                self._cleanup_path(temp_package)
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            self._safe_record_update(
                record.operation_id,
                status=STATUS_FAILED,
                error_code="sqlite_integrity_failed",
                error_message=_ERROR_MESSAGES["sqlite_integrity_failed"],
                staging_path=str(stage_parent),
            )
            self._cleanup_path(stage_parent)
            raise ProjectBackupError("sqlite_integrity_failed") from exc

    create_backup = backup
    export_backup = backup
    export = backup

    def _validate_archive_names(self, infos: Sequence[zipfile.ZipInfo]) -> None:
        if len(infos) > self.max_archive_members:
            raise ProjectBackupError("package_corrupt")
        names: set[str] = set()
        total = 0
        for info in infos:
            name = str(info.filename)
            if not name or "\x00" in name or "\\" in name:
                raise ProjectBackupError("package_corrupt")
            # R24V2-B16：真实上传件含中文名（如"【Data Listing】….xlsx"），
            # 不再要求ASCII；仍禁止控制字符与其余路径卫生约束。
            if any(ord(ch) < 32 or ch == "\x7f" for ch in name):
                raise ProjectBackupError("package_corrupt")
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
                raise ProjectBackupError("package_corrupt")
            if name in names:
                raise ProjectBackupError("package_corrupt")
            names.add(name)
            if info.is_dir() or name.endswith("/"):
                raise ProjectBackupError("package_corrupt")
            mode = (int(info.external_attr) >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ProjectBackupError("package_corrupt")
            if info.compress_type != zipfile.ZIP_STORED:
                raise ProjectBackupError("package_corrupt")
            if info.date_time != (1980, 1, 1, 0, 0, 0):
                raise ProjectBackupError("package_corrupt")
            if info.create_system != 3 or info.create_version != 20 or info.extract_version != 20:
                raise ProjectBackupError("package_corrupt")
            if info.extra or info.comment:
                raise ProjectBackupError("package_corrupt")
            if info.file_size < 0 or info.file_size > self.max_member_bytes:
                raise ProjectBackupError("package_corrupt")
            total += int(info.file_size)
            if total > self.max_archive_bytes:
                raise ProjectBackupError("package_corrupt")
        if "manifest.json" not in names:
            raise ProjectBackupError("package_corrupt")

    def _inspect_archive(
        self,
        operation_id: str,
        package_path: Path,
    ) -> Tuple[Dict[str, Any], Path, Dict[str, bytes], str]:
        try:
            archive_bytes = package_path.read_bytes()
            package_id = sha256_hex(archive_bytes)
            archive = zipfile.ZipFile(str(package_path), "r")
        except (OSError, zipfile.BadZipFile) as exc:
            raise ProjectBackupError("package_corrupt") from exc
        try:
            infos = archive.infolist()
            self._validate_archive_names(infos)
            manifest_raw = archive.read("manifest.json")
            try:
                manifest = json.loads(manifest_raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ProjectBackupError("package_corrupt") from exc
            if not isinstance(manifest, dict):
                raise ProjectBackupError("package_corrupt")
            if set(manifest) != set(_SUPPORTED_MANIFEST_KEYS):
                raise ProjectBackupError("package_corrupt")
            if manifest_raw != canonical_json_bytes(manifest) + b"\n":
                raise ProjectBackupError("package_corrupt")
            if manifest.get("contract_version") != CONTRACT_VERSION:
                raise ProjectBackupError("unsupported_contract")
            if manifest.get("schema_version") != SCHEMA_VERSION:
                raise ProjectBackupError("unsupported_contract")
            package_project = manifest.get("canonical_project_id")
            if not isinstance(package_project, str) or package_project != self.canonical_project_id:
                raise ProjectBackupError("package_identity_mismatch")
            descriptors = manifest.get("members")
            if not isinstance(descriptors, list) or not descriptors:
                raise ProjectBackupError("package_corrupt")
            descriptor_paths: List[str] = []
            for item in descriptors:
                if not isinstance(item, dict) or set(item) != {"path", "size", "sha256"}:
                    raise ProjectBackupError("package_corrupt")
                path = item.get("path")
                size = item.get("size")
                digest = item.get("sha256")
                if (
                    not isinstance(path, str)
                    or not path.startswith("members/")
                    or path == "members/"
                    or not isinstance(size, int)
                    or isinstance(size, bool)
                    or size < 0
                    or size > self.max_member_bytes
                    or not isinstance(digest, str)
                    or not _HEX64.match(digest)
                ):
                    raise ProjectBackupError("package_corrupt")
                relative = path[len("members/") :]
                if "\\" in relative or PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
                    raise ProjectBackupError("package_corrupt")
                descriptor_paths.append(path)
            if descriptor_paths != sorted(set(descriptor_paths), key=lambda value: value.encode("utf-8")):
                raise ProjectBackupError("package_corrupt")
            names = [info.filename for info in infos if info.filename != "manifest.json"]
            if names != descriptor_paths or set(names) != set(descriptor_paths):
                raise ProjectBackupError("package_corrupt")
            stage_parent = self.runtime_root / STAGING_DIR_NAME / operation_id
            if stage_parent.exists():
                raise ProjectBackupError("backup_operation_conflict")
            stage_workspace = stage_parent / "workspace"
            stage_workspace.mkdir(parents=True, exist_ok=False)
            if self.failure_hook is not None:
                self._hook("preflight.unpack.before")
            members: Dict[str, bytes] = {}
            for path in descriptor_paths:
                info = archive.getinfo(path)
                raw = archive.read(path)
                relative = path[len("members/") :]
                expected = next(item for item in descriptors if item["path"] == path)
                if len(raw) != expected["size"] or sha256_hex(raw) != expected["sha256"]:
                    raise ProjectBackupError("package_corrupt")
                target = stage_workspace / Path(relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
                members[relative] = raw
            if self.failure_hook is not None:
                self._hook("preflight.unpack.after")
            if self._manifest_content_digest(manifest, members) != manifest.get("content_digest"):
                raise ProjectBackupError("manifest_semantic_mismatch")
            if self.failure_hook is not None:
                self._hook("preflight.member_verification.before")
            actual_fp = self._fingerprint(members)
            if actual_fp != manifest.get("source_workspace_fingerprint"):
                raise ProjectBackupError("manifest_semantic_mismatch")
            if self.failure_hook is not None:
                self._hook("preflight.member_verification.after")
            return manifest, stage_parent, members, package_id
        finally:
            archive.close()

    def verify_artifact_closure(
        self,
        workspace: Path,
        summary: Mapping[str, Any],
    ) -> None:
        """Verify the exact registered-to-file artifact closure."""

        self._verify_artifact_closure(workspace, summary)

    def artifact_closure(self, workspace: Optional[Path] = None) -> Dict[str, bytes]:
        """Return verified content-addressed artifact bytes keyed by hash."""

        target = self.workspace_dir if workspace is None else Path(workspace)
        summary = self._summarize_workspace(target)
        self._verify_artifact_closure(target, summary)
        members = self._member_bytes(target)
        result: Dict[str, bytes] = {}
        prefix = RUNTIME_DIR_NAME + "/" + ARTIFACT_DIR_NAME + "/"
        for relative, data in members.items():
            if relative.startswith(prefix):
                result[Path(relative).stem] = data
        return {key: result[key] for key in sorted(result)}
    def _verify_artifact_closure(self, workspace: Path, summary: Mapping[str, Any]) -> None:
        runtime_db = workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        expected_hashes = tuple(summary.get("artifact_hashes", ()))
        if not runtime_db.exists():
            if expected_hashes:
                raise ProjectBackupError("artifact_closure_invalid")
            return
        artifact_dir = workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME
        if expected_hashes:
            _assert_directory(artifact_dir)
        actual_files: set[str] = set()
        if artifact_dir.exists():
            _assert_directory(artifact_dir)
            for child in artifact_dir.iterdir():
                if _is_ignorable(child):
                    continue
                # R24V2-B16：辅助成员（命名manifest/子目录集）不属于DB
                # 内容哈希闭包，其完整性由manifest逐成员哈希承担。
                if not (child.is_file() and _is_hex64_artifact_name(child.name)):
                    continue
                _assert_regular(child)
                actual_files.add(child.stem)
                if sha256_hex(child.read_bytes()) != child.stem:
                    raise ProjectBackupError("artifact_closure_invalid")
        if actual_files != set(expected_hashes):
            raise ProjectBackupError("artifact_closure_invalid")

    def _verify_workspace(
        self,
        workspace: Path,
        manifest: Mapping[str, Any],
        *,
        verify_manifest_summary: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, bytes], str]:
        self._validate_workspace_layout(workspace)
        members = self._member_bytes(workspace)
        fingerprint = self._fingerprint(members)
        if manifest.get("source_workspace_fingerprint") != fingerprint:
            raise ProjectBackupError("manifest_semantic_mismatch")
        summary = self._summarize_workspace(
            workspace,
            project_name_override=str(manifest.get("project_name", self.canonical_project_id)),
        )
        self._verify_artifact_closure(workspace, summary)
        closure = manifest.get("artifact_closure")
        expected_hashes = tuple(summary.get("artifact_hashes", ()))
        if not isinstance(closure, dict) or set(closure) != {"content_hashes", "count", "set_digest"}:
            raise ProjectBackupError("manifest_semantic_mismatch")
        if (
            tuple(closure.get("content_hashes", ())) != expected_hashes
            or closure.get("count") != len(expected_hashes)
            or closure.get("set_digest") != self._set_digest(expected_hashes)
        ):
            raise ProjectBackupError("manifest_semantic_mismatch")
        if verify_manifest_summary and summary != manifest.get("project_summary"):
            raise ProjectBackupError("manifest_semantic_mismatch")
        if summary.get("project_name") != manifest.get("project_name"):
            raise ProjectBackupError("manifest_semantic_mismatch")
        if summary.get("backup_cutoff") != manifest.get("backup_cutoff"):
            raise ProjectBackupError("manifest_semantic_mismatch")
        return summary, members, fingerprint

    def _current_state(self, operation_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        snapshot = self._current_snapshot(operation_id)
        if snapshot is None:
            return None, None
        return snapshot.summary, snapshot.fingerprint

    @staticmethod
    def _impact(current: Optional[Mapping[str, Any]], target: Mapping[str, Any]) -> Dict[str, int]:
        current_counts = dict((current or {}).get("counts", {}))
        target_counts = dict(target.get("counts", {}))
        result: Dict[str, int] = {}
        for key in ("runs", "publications", "risk_rules", "continuity_plans"):
            difference = int(current_counts.get(key, 0)) - int(target_counts.get(key, 0))
            if difference > 0:
                result[key] = difference
        return result

    def _preflight_result_from_record(self, record: OperationRecord, package_path: Path) -> PreflightResult:
        payload = dict(record.payload)
        try:
            return PreflightResult(
                operation=record,
                package_id=str(payload["package_id"]),
                package_path=package_path,
                canonical_project_id=self.canonical_project_id,
                project_name=str(payload["project_name"]),
                backup_cutoff_label=str(payload["backup_cutoff_label"]),
                current_cutoff_label=str(payload["current_cutoff_label"]),
                decision=str(payload["decision"]),
                decision_label=str(payload["decision_label"]),
                impact_summary=str(payload["impact_summary"]),
                items_preserved=tuple(str(value) for value in payload.get("items_preserved", [])),
                items_rolled_back=dict(payload.get("items_rolled_back", {})),
                recommended_action=str(payload["recommended_action"]),
                confirmation_required=bool(payload["confirmation_required"]),
                unfinished_work_notice=payload.get("unfinished_work_notice"),
                source_workspace_fingerprint=str(payload["source_workspace_fingerprint"]),
                current_workspace_fingerprint=payload.get("current_workspace_fingerprint"),
                staging_path=Path(payload["staging_path"]) if payload.get("staging_path") else None,
                manifest=dict(payload.get("manifest", {})),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProjectBackupError("sqlite_integrity_failed") from exc

    def preflight(
        self,
        package: Union[str, Path, PreflightResult],
        idempotency_key: Optional[str] = None,
        *,
        operation_id: Optional[str] = None,
    ) -> PreflightResult:
        package_path = self._package_path(package)
        try:
            package_id = sha256_hex(package_path.read_bytes())
        except OSError as exc:
            raise ProjectBackupError("package_corrupt") from exc
        key = _required_key(idempotency_key) if idempotency_key is not None else "preflight-" + package_id
        record = self.ledger.create_or_replay(
            OP_PREFLIGHT,
            key,
            self.canonical_project_id,
            package_id=package_id,
        )
        if record.replayed and record.status == STATUS_READY_FOR_CONFIRMATION and record.payload:
            return self._preflight_result_from_record(record, package_path)
        op_id = operation_id or record.operation_id
        stage_parent = self.runtime_root / STAGING_DIR_NAME / op_id
        try:
            with self._gate(record.operation_id).shared():
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_INSPECTING,
                    progress_percent=PROGRESS_REQUEST_ACCEPTED,
                    current_step="正在检查备份内容",
                )
                manifest, stage_parent, members, actual_package_id = self._inspect_archive(
                    record.operation_id, package_path
                )
                if actual_package_id != package_id:
                    raise ProjectBackupError("package_corrupt")
                summary, _, source_fp = self._verify_workspace(
                    stage_parent / "workspace", manifest, verify_manifest_summary=True
                )
                if self.failure_hook is not None:
                    self._hook("preflight.staging_workspace_verification.before")
                # A second pass catches a staging directory that gained an
                # unlisted file between extraction and verification.
                self._verify_workspace(stage_parent / "workspace", manifest, verify_manifest_summary=True)
                if self.failure_hook is not None:
                    self._hook("preflight.staging_workspace_verification.after")
                self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=STATUS_VERIFYING_MEMBERS,
                    progress_percent=PROGRESS_MEMBER_VERIFICATION_COMPLETE,
                    current_step="恢复前检查已完成",
                )
                current_summary, current_fp = self._current_state(record.operation_id)
                if current_summary is not None and current_summary.get("project_name") == self.canonical_project_id and self.project_name:
                    current_summary = dict(current_summary)
                    current_summary["project_name"] = self.project_name
                if self._existing_rollbacks():
                    decision = "blocked"
                    decision_label = "无法恢复"
                    confirmation_required = False
                    recommended = "请先核对已有回退版本"
                elif current_fp is not None and current_fp == source_fp and current_summary == summary:
                    decision = "already_current"
                    decision_label = "已是当前版本"
                    confirmation_required = False
                    recommended = "继续查看当前监查结果"
                else:
                    older = bool(
                        current_summary is not None
                        and str(summary.get("backup_cutoff", "")) < str(current_summary.get("backup_cutoff", ""))
                    )
                    decision = "rollback_required" if older else "ready"
                    decision_label = "需确认回退" if older else "可恢复"
                    confirmation_required = True
                    recommended = "保留当前状态，并先导出一份当前备份" if older else "确认后恢复此备份"
                impact = self._impact(current_summary, summary)
                impact_text = "无预计回退事项" if not impact else "、".join(
                    "%s %d 项" % (key, value) for key, value in sorted(impact.items())
                )
                unfinished_notice = (
                    "此备份包含未完成的监查任务，恢复后仍需继续处理"
                    if summary.get("unfinished_work")
                    else None
                )
                payload: Dict[str, Any] = {
                    "package_id": package_id,
                    "project_name": str(manifest["project_name"]),
                    "backup_cutoff_label": str(manifest["backup_cutoff"]),
                    "current_cutoff_label": str(
                        (current_summary or {}).get("backup_cutoff", "当前项目尚未建立")
                    ),
                    "decision": decision,
                    "decision_label": decision_label,
                    "impact_summary": impact_text,
                    "items_preserved": ["监查结果", "风险规则", "受试者历程", "中心汇总"],
                    "items_rolled_back": impact,
                    "recommended_action": recommended,
                    "confirmation_required": confirmation_required,
                    "unfinished_work_notice": unfinished_notice,
                    "source_workspace_fingerprint": source_fp,
                    "current_workspace_fingerprint": current_fp,
                    "staging_path": str(stage_parent),
                    "manifest": dict(manifest),
                }
                final_status = STATUS_READY_FOR_CONFIRMATION
                final_record = self._record_update(
                    record.operation_id,
                    OP_BACKUP,
                    status=final_status,
                    progress_percent=PROGRESS_RECONCILIATION_COMPLETE,
                    current_step="已完成恢复预检",
                    package_id=package_id,
                    source_workspace_fingerprint=source_fp,
                    staging_path=str(stage_parent),
                    payload=payload,
                )
                return PreflightResult(
                    operation=final_record,
                    package_id=package_id,
                    package_path=package_path,
                    canonical_project_id=self.canonical_project_id,
                    project_name=str(manifest["project_name"]),
                    backup_cutoff_label=str(manifest["backup_cutoff"]),
                    current_cutoff_label=str(
                        (current_summary or {}).get("backup_cutoff", "当前项目尚未建立")
                    ),
                    decision=decision,
                    decision_label=decision_label,
                    impact_summary=impact_text,
                    items_preserved=("监查结果", "风险规则", "受试者历程", "中心汇总"),
                    items_rolled_back=impact,
                    recommended_action=recommended,
                    confirmation_required=confirmation_required,
                    unfinished_work_notice=unfinished_notice,
                    source_workspace_fingerprint=source_fp,
                    current_workspace_fingerprint=current_fp,
                    staging_path=stage_parent,
                    manifest=manifest,
                )
        except ProjectBusyError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            self._cleanup_path(stage_parent)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except MaintenanceGateError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            self._cleanup_path(stage_parent)
            raise ProjectBackupError(exc.code, exc.message) from exc
        except ProjectBackupError as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code=exc.code, error_message=exc.message)
            self._cleanup_path(stage_parent)
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
            self._safe_record_update(record.operation_id, status=STATUS_FAILED, error_code="package_corrupt", error_message=_ERROR_MESSAGES["package_corrupt"])
            self._cleanup_path(stage_parent)
            raise ProjectBackupError("package_corrupt") from exc

    restore_preflight = preflight
    inspect = preflight

    def _existing_rollbacks(self) -> List[Path]:
        if not self.runtime_root.exists():
            return []
        prefix = ".rollback-" + sha256_hex(self.canonical_project_id.encode("utf-8"))[:24] + "-"
        result: List[Path] = []
        for child in self.runtime_root.iterdir():
            if child.name.startswith(prefix) and child.name != prefix:
                result.append(child)
        return sorted(result, key=lambda path: path.name)

    def _active_project_work(self, workspace: Path) -> bool:
        launch = workspace / LAUNCH_REGISTRY_DB_NAME
        if launch.exists():
            conn = _open_ro(launch)
            try:
                if "r7_launch_registry" in _table_names(conn):
                    columns = _table_columns(conn, "r7_launch_registry")
                    if "run_state" in columns:
                        row = conn.execute(
                            "SELECT 1 FROM r7_launch_registry WHERE run_state IN"
                            " ('waiting_start','running','stopping') LIMIT 1"
                        ).fetchone()
                        if row is not None:
                            return True
            finally:
                conn.close()
        runtime = workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        if runtime.exists():
            conn = _open_ro(runtime)
            try:
                tables = _table_names(conn)
                if "node_attempts" in tables:
                    row = conn.execute(
                        "SELECT 1 FROM node_attempts WHERE status='running' LIMIT 1"
                    ).fetchone()
                    if row is not None:
                        return True
                if "monitoring_runs" in tables:
                    row = conn.execute(
                        "SELECT 1 FROM monitoring_runs WHERE analysis_state IN"
                        " ('running','preparing') LIMIT 1"
                    ).fetchone()
                    if row is not None:
                        return True
            finally:
                conn.close()
        return False

    def _probe_transactions(self, workspace: Path) -> None:
        for relative in _member_rel_paths(workspace):
            if relative.endswith("/" + ARTIFACT_DIR_NAME) or "/" in relative and relative.split("/")[-1].endswith(".json"):
                continue
            path = workspace / Path(relative)
            conn: Optional[sqlite3.Connection] = None
            try:
                conn = sqlite3.connect(str(path), timeout=0.0, isolation_level=None)
                conn.execute("PRAGMA busy_timeout=0")
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError as exc:
                if conn is not None:
                    try:
                        conn.execute("ROLLBACK")
                    except sqlite3.Error:
                        pass
                raise ProjectBackupError("project_busy_retry_later") from exc
            except sqlite3.Error as exc:
                raise ProjectBackupError("sqlite_integrity_failed") from exc
            finally:
                if conn is not None:
                    conn.close()

    def _quiesce(self) -> None:
        if self._active_project_work(self.workspace_dir):
            raise ProjectBackupError("project_busy_retry_later")
        self._probe_transactions(self.workspace_dir)

    def _verify_live_workspace(
        self, manifest: Mapping[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, bytes], str]:
        if self.failure_hook is not None:
            self._hook("restore.live_reopen.before")
        summary, members, fingerprint = self._verify_workspace(
            self.workspace_dir, manifest, verify_manifest_summary=True
        )
        # Opening each database again after the verification pass makes the
        # close/reopen invariant explicit rather than relying on one connection.
        # R24V2-B16：只reopen五个SQLite成员；辅助成员（json/gz/上传件）
        # 不是数据库，由manifest哈希校验承担。
        db_members = set(_ALLOWED_ROOT_FILES) | {RUNTIME_DIR_NAME + "/" + RUNTIME_DB_NAME}
        for relative in _member_rel_paths(self.workspace_dir):
            if relative not in db_members:
                continue
            conn = _open_ro(self.workspace_dir / Path(relative))
            conn.close()
        if self.failure_hook is not None:
            self._hook("restore.live_reopen.after")
        if self.failure_hook is not None:
            self._hook("restore.identity_verification.before")
        if manifest.get("canonical_project_id") != self.canonical_project_id:
            raise ProjectBackupError("package_identity_mismatch")
        if self.failure_hook is not None:
            self._hook("restore.identity_verification.after")
        if self.failure_hook is not None:
            self._hook("restore.artifact_verification.before")
        self._verify_artifact_closure(self.workspace_dir, summary)
        if self.failure_hook is not None:
            self._hook("restore.artifact_verification.after")
        if self.failure_hook is not None:
            self._hook("restore.publication_verification.before")
        if summary.get("counts", {}).get("publications") != manifest.get("project_summary", {}).get("counts", {}).get("publications"):
            raise ProjectBackupError("restore_verification_failed")
        if self.failure_hook is not None:
            self._hook("restore.publication_verification.after")
        if self.failure_hook is not None:
            self._hook("restore.continuity_verification.before")
        if summary.get("counts", {}).get("continuity_plans") != manifest.get("project_summary", {}).get("counts", {}).get("continuity_plans"):
            raise ProjectBackupError("restore_verification_failed")
        if self.failure_hook is not None:
            self._hook("restore.continuity_verification.after")
        return summary, members, fingerprint

    def _verify_workspace_independent(
        self, workspace: Path
    ) -> Tuple[Dict[str, Any], Dict[str, bytes], str]:
        """Reopen and verify a live workspace without manifest self-reporting.

        Manual rollback targets the older live version, so it cannot be checked
        against the newer restore manifest.  It still must pass the same
        schema, identity, artifact-closure, and SQLite reopen checks.
        """

        self._validate_workspace_layout(workspace)
        members = self._member_bytes(workspace)
        fingerprint = self._fingerprint(members)
        summary = self._summarize_workspace(workspace, project_name_override=self.project_name)
        self._verify_artifact_closure(workspace, summary)
        # R24V2-B16：reopen只针对SQLite成员（同_verify_live_workspace）。
        db_members = set(_ALLOWED_ROOT_FILES) | {RUNTIME_DIR_NAME + "/" + RUNTIME_DB_NAME}
        for relative in _member_rel_paths(workspace):
            if relative not in db_members:
                continue
            conn = _open_ro(workspace / Path(relative))
            conn.close()
        return summary, members, fingerprint

    def _rollback_after_failure(
        self,
        operation_id: str,
        rollback_path: Optional[Path],
        staging_parent: Path,
        *,
        old_live_moved: bool,
    ) -> bool:
        if not old_live_moved or rollback_path is None or not rollback_path.exists():
            return True
        try:
            self._safe_record_update(
                operation_id,
                status=STATUS_ROLLBACK_IN_PROGRESS,
                current_step="正在恢复原项目版本",
            )
            self._hook("restore.rollback.before")
            failed_live = staging_parent / "failed-live"
            if self.workspace_dir.exists():
                if failed_live.exists():
                    self._cleanup_path(failed_live)
                os.replace(str(self.workspace_dir), str(failed_live))
            os.replace(str(rollback_path), str(self.workspace_dir))
            self._fsync_dir(self.runtime_root)
            self._hook("restore.rollback.after")
            return True
        except BaseException:
            return False

