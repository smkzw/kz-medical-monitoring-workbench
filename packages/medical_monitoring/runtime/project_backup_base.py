"""Project backup manager configuration and workspace snapshot primitives."""

from .project_backup_support import *


class ProjectBackupBase:
    """Shared state and snapshot operations for backup and restore."""

    """Backup, preflight, restore, and atomic rollback for one project."""

    def __init__(
        self,
        root: Union[str, Path],
        canonical_project_id: Optional[str] = None,
        *,
        project_dir: Optional[Union[str, Path]] = None,
        workspace_dir: Optional[Union[str, Path]] = None,
        publication_dir: Optional[Union[str, Path]] = None,
        backup_dir: Optional[Union[str, Path]] = None,
        ledger: Optional[OperationLedger] = None,
        wait_seconds: float = DEFAULT_WAIT_SECONDS,
        max_archive_members: int = MAX_ARCHIVE_MEMBERS,
        max_member_bytes: int = MAX_MEMBER_BYTES,
        max_archive_bytes: int = MAX_ARCHIVE_BYTES,
        project_name: Optional[str] = None,
        failure_hook: Optional[Callable[[str], None]] = None,
        failure_injector: Optional[Callable[[str], None]] = None,
    ) -> None:
        root_path = Path(root)
        chosen_workspace = project_dir if project_dir is not None else workspace_dir
        if chosen_workspace is not None:
            self.runtime_root = root_path
            self.workspace_dir = Path(chosen_workspace)
            if canonical_project_id is None:
                canonical_project_id = self.workspace_dir.name
        elif canonical_project_id is None:
            self.workspace_dir = root_path
            self.runtime_root = root_path.parent
            canonical_project_id = root_path.name
        else:
            self.runtime_root = root_path
            self.workspace_dir = root_path / canonical_project_id
        self.canonical_project_id = _required_project_id(canonical_project_id)
        self.project_name = project_name if isinstance(project_name, str) and project_name else None
        self.publication_dir = Path(
            publication_dir
            if publication_dir is not None
            else (backup_dir if backup_dir is not None else self.runtime_root / BACKUP_PUBLICATION_DIR_NAME)
        )
        self.ledger = ledger if ledger is not None else OperationLedger(self.runtime_root)
        try:
            wait = float(wait_seconds)
        except (TypeError, ValueError) as exc:
            raise ProjectBackupError("invalid_idempotency_key") from exc
        if wait < 0 or wait > 120:
            raise ProjectBackupError("invalid_idempotency_key")
        self.wait_seconds = wait
        self.max_archive_members = int(max_archive_members)
        self.max_member_bytes = int(max_member_bytes)
        self.max_archive_bytes = int(max_archive_bytes)
        if self.max_archive_members < 1 or self.max_member_bytes < 1 or self.max_archive_bytes < 1:
            raise ProjectBackupError("package_corrupt")
        self.failure_hook = failure_hook if failure_hook is not None else failure_injector

    @property
    def project_dir(self) -> Path:
        return self.workspace_dir

    @property
    def operations_db_path(self) -> Path:
        return self.ledger.path

    def set_failure_hook(self, hook: Optional[Callable[[str], None]]) -> None:
        self.failure_hook = hook

    def _hook(self, point: str) -> None:
        callback = self.failure_hook
        if callback is None:
            return
        try:
            result = callback(str(point))
            if isinstance(result, BaseException):
                raise result
            if result is True:
                raise InjectedFailure(point)
        except ProjectBackupError:
            raise
        except BaseException as exc:
            raise InjectedFailure(point) from exc

    def _record_update(self, operation_id: str, operation_kind: str, **kwargs: Any) -> OperationRecord:
        prefix = "restore" if operation_kind == OP_RESTORE else "backup"
        self._hook(prefix + ".operation_record_submit.before")
        record = self.ledger.update(operation_id, **kwargs)
        self._hook(prefix + ".operation_record_submit.after")
        return record

    def _safe_record_update(self, operation_id: str, **kwargs: Any) -> None:
        try:
            self.ledger.update(operation_id, allow_terminal_reopen=True, **kwargs)
        except (ProjectBackupError, sqlite3.Error):
            pass

    def _gate_event(self, operation_id: str, event: str) -> None:
        try:
            if event == "waiting_for_project":
                self.ledger.update(
                    operation_id,
                    status=STATUS_WAITING_FOR_PROJECT,
                    current_step="正在等待项目空闲",
                    maintenance_state=event,
                )
            else:
                self.ledger.record_maintenance(operation_id, event)
        except (ProjectBackupError, sqlite3.Error):
            # A ledger observation must never retain a project lock.  The
            # operation path still records a terminal error when possible.
            pass

    def _gate(self, operation_id: str) -> ProjectMaintenanceGate:
        return ProjectMaintenanceGate(
            self.runtime_root,
            self.canonical_project_id,
            wait_seconds=self.wait_seconds,
            event_callback=lambda event: self._gate_event(operation_id, event),
        )

    def _validate_workspace_layout(self, workspace: Optional[Path] = None) -> None:
        root = workspace if workspace is not None else self.workspace_dir
        if not root.exists():
            raise ProjectBackupError("workspace_not_found")
        _assert_directory(root)
        for child in sorted(root.iterdir(), key=lambda p: p.name.encode("utf-8")):
            if _is_ignorable(child):
                continue
            if _is_sqlite_sidecar(child.name):
                continue
            if child.name in _ALLOWED_ROOT_FILES:
                _assert_regular(child)
                continue
            if child.name != RUNTIME_DIR_NAME:
                raise ProjectBackupError("workspace_unknown_member")
            _assert_directory(child)
            for nested in sorted(child.iterdir(), key=lambda p: p.name.encode("utf-8")):
                if _is_ignorable(nested):
                    continue
                if _is_sqlite_sidecar(nested.name):
                    continue
                if nested.name == RUNTIME_DB_NAME:
                    _assert_regular(nested)
                elif nested.name == ARTIFACT_DIR_NAME:
                    _assert_directory(nested)
                    for artifact in sorted(nested.iterdir(), key=lambda p: p.name.encode("utf-8")):
                        if _is_ignorable(artifact):
                            continue
                        _assert_regular(artifact)
                        if artifact.suffix == ".tmp":
                            raise ProjectBackupError("artifact_closure_invalid")
                        if artifact.suffix != ".json" or not _HEX64.match(artifact.stem):
                            raise ProjectBackupError("artifact_closure_invalid")
                else:
                    raise ProjectBackupError("workspace_unknown_member")
        if not (root / PROFILE_DB_NAME).exists():
            raise ProjectBackupError("workspace_member_missing")
        if not (root / RUN_BINDING_DB_NAME).exists():
            raise ProjectBackupError("workspace_member_missing")

    @staticmethod
    def _schema_version(conn: sqlite3.Connection, relative_path: str) -> str:
        tables = _table_names(conn)
        name = Path(relative_path).name
        if name == PROFILE_DB_NAME:
            if "profile_store_meta" not in tables:
                raise ProjectBackupError("unsupported_schema")
            row = conn.execute(
                "SELECT value FROM profile_store_meta WHERE key='schema_version'"
            ).fetchone()
            value = "" if row is None else str(row[0])
            if value != _SUPPORTED_PROFILE_SCHEMA:
                raise ProjectBackupError("unsupported_schema")
            return value
        if name == RUN_BINDING_DB_NAME:
            if "monitoring_run_bindings" not in tables:
                raise ProjectBackupError("unsupported_schema")
            columns = _table_columns(conn, "monitoring_run_bindings")
            if "schema_version" not in columns:
                raise ProjectBackupError("unsupported_schema")
            rows = conn.execute(
                "SELECT DISTINCT schema_version FROM monitoring_run_bindings"
            ).fetchall()
            values = {str(row[0]) for row in rows}
            if values and values != {_SUPPORTED_BINDING_SCHEMA}:
                raise ProjectBackupError("unsupported_schema")
            return _SUPPORTED_BINDING_SCHEMA
        if name == LAUNCH_REGISTRY_DB_NAME:
            if "r7_launch_registry_meta" not in tables:
                raise ProjectBackupError("unsupported_schema")
            row = conn.execute(
                "SELECT value FROM r7_launch_registry_meta WHERE key='schema_version'"
            ).fetchone()
            value = "" if row is None else str(row[0])
            if value not in _SUPPORTED_LAUNCH_SCHEMAS:
                raise ProjectBackupError("unsupported_schema")
            return value
        if name == RISK_RULE_DB_NAME:
            if "r7_risk_rule_revisions" not in tables:
                raise ProjectBackupError("unsupported_schema")
            return "mm-r7-risk-rule-v1"
        if name == RUNTIME_DB_NAME:
            if "meta" not in tables:
                raise ProjectBackupError("unsupported_schema")
            row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            value = "" if row is None else str(row[0])
            if value not in _SUPPORTED_RUNTIME_SCHEMAS:
                raise ProjectBackupError("unsupported_schema")
            required = {"projects", "monitoring_runs", "artifacts", "listing_snapshots"}
            if not required.issubset(tables):
                raise ProjectBackupError("unsupported_schema")
            return value
        raise ProjectBackupError("unsupported_schema")

    def _sqlite_snapshot(self, source: Path, target: Path) -> str:
        _assert_regular(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        source_conn: Optional[sqlite3.Connection] = None
        target_conn: Optional[sqlite3.Connection] = None
        try:
            source_conn = sqlite3.connect(_sqlite_uri(source), uri=True, timeout=10.0)
            source_conn.row_factory = sqlite3.Row
            _quick_check(source_conn)
            target_conn = sqlite3.connect(str(target), timeout=10.0)
            target_conn.row_factory = sqlite3.Row
            source_conn.backup(target_conn)
            # A WAL source can carry the WAL mode bit into the destination
            # header.  Package members intentionally exclude -wal/-shm, so
            # normalize the isolated snapshot to rollback-journal mode before
            # closing it; otherwise a reopened member would need sidecars.
            target_conn.execute("PRAGMA journal_mode=DELETE")
            target_conn.commit()
            _quick_check(target_conn)
        except ProjectBackupError:
            raise
        except (sqlite3.Error, OSError, ValueError) as exc:
            raise ProjectBackupError("sqlite_integrity_failed") from exc
        finally:
            if target_conn is not None:
                target_conn.close()
            if source_conn is not None:
                source_conn.close()
        try:
            verify_conn = _open_ro(target)
            version = self._schema_version(verify_conn, target.name)
            verify_conn.close()
            return version
        except ProjectBackupError:
            raise
        except (sqlite3.Error, OSError) as exc:
            raise ProjectBackupError("sqlite_integrity_failed") from exc

    def _member_bytes(self, workspace: Path) -> Dict[str, bytes]:
        result: Dict[str, bytes] = {}
        for relative in _member_rel_paths(workspace):
            path = workspace / Path(relative)
            _assert_regular(path)
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise ProjectBackupError("workspace_member_missing") from exc
            if len(data) > self.max_member_bytes:
                raise ProjectBackupError("package_corrupt")
            result[relative] = data
        return {key: result[key] for key in sorted(result, key=lambda value: value.encode("utf-8"))}

    def member_bytes(self, workspace: Optional[Path] = None) -> Dict[str, bytes]:
        """Return verified bytes for the selected workspace members."""

        target = self.workspace_dir if workspace is None else Path(workspace)
        return self._member_bytes(target)

    @staticmethod
    def _fingerprint(member_bytes: Mapping[str, bytes]) -> str:
        return workspace_fingerprint(member_bytes)

    @staticmethod
    def _verify_audit_chain(conn: sqlite3.Connection) -> None:
        """Use R1's public verifier as the single chain algorithm."""

        try:
            readonly_store = R1Store.__new__(R1Store)
            readonly_store._conn = conn
            result = readonly_store.verify_audit_chain()
            if not isinstance(result, tuple) or not result or not bool(result[0]):
                raise ProjectBackupError("sqlite_integrity_failed")
        except ProjectBackupError:
            raise
        except (sqlite3.Error, TypeError, ValueError, UnicodeError, AttributeError) as exc:
            raise ProjectBackupError("sqlite_integrity_failed") from exc

    @staticmethod
    def _artifact_hashes(conn: sqlite3.Connection) -> Tuple[str, ...]:
        hashes: set[str] = set()
        tables = _table_names(conn)
        for table in ("artifacts", "listing_snapshots"):
            if table not in tables:
                continue
            columns = _table_columns(conn, table)
            if "content_hash" not in columns:
                raise ProjectBackupError("unsupported_schema")
            rows = conn.execute("SELECT content_hash FROM %s" % table).fetchall()
            for row in rows:
                value = str(row[0])
                if not _HEX64.match(value):
                    raise ProjectBackupError("artifact_closure_invalid")
                hashes.add(value)
        return tuple(sorted(hashes))

    @staticmethod
    def _set_digest(values: Iterable[str]) -> str:
        return sha256_hex(canonical_json_bytes(list(sorted(values))))

    def _summarize_workspace(
        self, workspace: Path, *, project_name_override: Optional[str] = None
    ) -> Dict[str, Any]:
        self._validate_workspace_layout(workspace)
        schema_versions: Dict[str, str] = {}
        project_ids: set[str] = set()
        project_name = project_name_override or self.project_name or self.canonical_project_id
        runs: List[Dict[str, Any]] = []
        run_states: List[str] = []
        mode_counts: Dict[str, int] = {}
        basis_counts: Dict[str, int] = {}
        artifact_hashes: Tuple[str, ...] = tuple()
        publications = continuity_plans = continuity_items = risk_rules = 0
        launch_active = False
        node_attempts_running = 0
        for relative in _member_rel_paths(workspace):
            if relative.endswith(".json"):
                continue
            if relative not in _ALLOWED_ROOT_FILES and relative != RUNTIME_DIR_NAME + "/" + RUNTIME_DB_NAME:
                continue
            path = workspace / Path(relative)
            if path.name == ARTIFACT_DIR_NAME or relative.endswith("/" + ARTIFACT_DIR_NAME):
                continue
            conn = _open_ro(path)
            try:
                schema_versions[relative] = self._schema_version(conn, relative)
                tables = _table_names(conn)
                # Every authoritative table that carries project_id must
                # point at the route-selected canonical project.  This also
                # covers launch publications and continuity plans/items,
                # whose project columns are easy to miss when counting only
                # the primary launch table.
                for table in sorted(tables):
                    if "project_id" not in _table_columns(conn, table):
                        continue
                    project_ids.update(
                        str(row[0])
                        for row in conn.execute(
                            "SELECT DISTINCT project_id FROM %s" % table
                        ).fetchall()
                    )
                if path.name == RUNTIME_DB_NAME:
                    self._verify_audit_chain(conn)
                    if "projects" in tables:
                        for row in conn.execute(
                            "SELECT project_id, name, is_synthetic FROM projects ORDER BY project_id"
                        ).fetchall():
                            pid = str(row[0])
                            project_ids.add(pid)
                            if pid == self.canonical_project_id and row[1]:
                                project_name = str(row[1])
                            if not bool(row[2]):
                                raise ProjectBackupError("package_identity_mismatch")
                    if "source_revisions" in tables:
                        project_ids.update(
                            str(row[0])
                            for row in conn.execute(
                                "SELECT DISTINCT project_id FROM source_revisions"
                            ).fetchall()
                        )
                    if "listing_snapshots" in tables:
                        project_ids.update(
                            str(row[0])
                            for row in conn.execute(
                                "SELECT DISTINCT project_id FROM listing_snapshots"
                            ).fetchall()
                        )
                    if "monitoring_runs" in tables:
                        rows = conn.execute(
                            "SELECT project_id, mode, execution_basis, analysis_state, data_cutoff"
                            " FROM monitoring_runs ORDER BY run_id"
                        ).fetchall()
                        for row in rows:
                            project_ids.add(str(row[0]))
                            mode = str(row[1])
                            basis = str(row[2])
                            state = str(row[3])
                            mode_counts[mode] = mode_counts.get(mode, 0) + 1
                            basis_counts[basis] = basis_counts.get(basis, 0) + 1
                            run_states.append(state)
                            runs.append(
                                {
                                    "analysis_state": state,
                                    "data_cutoff": str(row[4]),
                                    "execution_basis": basis,
                                    "mode": mode,
                                }
                            )
                    if "node_attempts" in tables:
                        node_attempts_running = int(
                            conn.execute(
                                "SELECT COUNT(*) FROM node_attempts WHERE status='running'"
                            ).fetchone()[0]
                        )
                    artifact_hashes = self._artifact_hashes(conn)
                elif path.name == LAUNCH_REGISTRY_DB_NAME:
                    if "r7_launch_registry" in tables:
                        columns = _table_columns(conn, "r7_launch_registry")
                        if "project_id" in columns:
                            project_ids.update(
                                str(row[0])
                                for row in conn.execute(
                                    "SELECT DISTINCT project_id FROM r7_launch_registry"
                                ).fetchall()
                            )
                        if "run_state" in columns:
                            launch_states = [
                                str(row[0])
                                for row in conn.execute(
                                    "SELECT run_state FROM r7_launch_registry ORDER BY sequence"
                                ).fetchall()
                            ]
                            launch_active = any(
                                state in {"waiting_start", "running", "stopping"}
                                for state in launch_states
                            )
                    if "r7_result_publications" in tables:
                        publications = int(
                            conn.execute("SELECT COUNT(*) FROM r7_result_publications").fetchone()[0]
                        )
                    if "r7_continuity_plans" in tables:
                        continuity_plans = int(
                            conn.execute("SELECT COUNT(*) FROM r7_continuity_plans").fetchone()[0]
                        )
                    if "r7_continuity_items" in tables:
                        continuity_items = int(
                            conn.execute("SELECT COUNT(*) FROM r7_continuity_items").fetchone()[0]
                        )
                elif path.name == RISK_RULE_DB_NAME:
                    if "r7_risk_rule_revisions" in tables:
                        columns = _table_columns(conn, "r7_risk_rule_revisions")
                        if "project_id" in columns:
                            project_ids.update(
                                str(row[0])
                                for row in conn.execute(
                                    "SELECT DISTINCT project_id FROM r7_risk_rule_revisions"
                                ).fetchall()
                            )
                        risk_rules = int(
                            conn.execute("SELECT COUNT(*) FROM r7_risk_rule_revisions").fetchone()[0]
                        )
                elif path.name == RUN_BINDING_DB_NAME:
                    columns = _table_columns(conn, "monitoring_run_bindings")
                    if "project_id" in columns:
                        project_ids.update(
                            str(row[0])
                            for row in conn.execute(
                                "SELECT DISTINCT project_id FROM monitoring_run_bindings"
                            ).fetchall()
                        )
            finally:
                conn.close()
        if project_ids and project_ids != {self.canonical_project_id}:
            raise ProjectBackupError("package_identity_mismatch")
        cutoffs = sorted({item["data_cutoff"] for item in runs if item["data_cutoff"]})
        backup_cutoff = cutoffs[-1] if cutoffs else "未建立监查运行"
        unfinished_states = [
            item["analysis_state"] for item in runs if item["analysis_state"] != "complete"
        ]
        unfinished = bool(unfinished_states or launch_active or node_attempts_running)
        counts = {
            "runs": len(runs),
            "completed_runs": sum(1 for item in runs if item["analysis_state"] == "complete"),
            "unfinished_runs": len(unfinished_states),
            "publications": publications,
            "continuity_plans": continuity_plans,
            "continuity_items": continuity_items,
            "risk_rules": risk_rules,
            "listing_snapshots": 0,
            "artifacts": len(artifact_hashes),
        }
        runtime_db = workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        if runtime_db.exists():
            conn = _open_ro(runtime_db)
            try:
                if "listing_snapshots" in _table_names(conn):
                    counts["listing_snapshots"] = int(
                        conn.execute("SELECT COUNT(*) FROM listing_snapshots").fetchone()[0]
                    )
            finally:
                conn.close()
        summary: Dict[str, Any] = {
            "project_name": project_name,
            "backup_cutoff": backup_cutoff,
            "mode_summary": {key: mode_counts[key] for key in sorted(mode_counts)},
            "execution_basis_summary": {key: basis_counts[key] for key in sorted(basis_counts)},
            "run_states": sorted(run_states),
            "counts": counts,
            "unfinished_work": unfinished,
            "schema_versions": {
                key: schema_versions[key]
                for key in sorted(schema_versions, key=lambda value: value.encode("utf-8"))
            },
            "artifact_hashes": list(artifact_hashes),
        }
        summary["semantic_digest"] = sha256_hex(
            canonical_json_bytes({key: value for key, value in summary.items() if key != "semantic_digest"})
        )
        return summary

    def summarize_workspace(
        self,
        workspace: Optional[Path] = None,
        *,
        project_name_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return the validated semantic summary for one workspace."""

        target = self.workspace_dir if workspace is None else Path(workspace)
        return self._summarize_workspace(
            target,
            project_name_override=project_name_override,
        )
    def _copy_artifacts(
        self,
        source_workspace: Path,
        staged_workspace: Path,
        artifact_hashes: Sequence[str],
        *,
        emit_hooks: bool,
    ) -> None:
        source_dir = source_workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME
        target_dir = staged_workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME
        if not artifact_hashes:
            return
        _assert_directory(source_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        for content_hash in sorted(artifact_hashes):
            source = source_dir / (content_hash + ".json")
            target = target_dir / source.name
            _assert_regular(source)
            before_stat = _lstat(source)
            if emit_hooks:
                self._hook("backup.artifact_copy.before")
            try:
                payload = source.read_bytes()
                if len(payload) > self.max_member_bytes:
                    raise ProjectBackupError("artifact_closure_invalid")
                target.write_bytes(payload)
                with target.open("rb") as handle:
                    os.fsync(handle.fileno())
            except ProjectBackupError:
                raise
            except OSError as exc:
                raise ProjectBackupError("artifact_closure_invalid") from exc
            after_stat = _lstat(source)
            try:
                after_payload = source.read_bytes()
            except OSError as exc:
                raise ProjectBackupError("artifact_closure_invalid") from exc
            if (
                before_stat.st_size != after_stat.st_size
                or before_stat.st_mtime_ns != after_stat.st_mtime_ns
                or payload != after_payload
                or sha256_hex(payload) != content_hash
                or sha256_hex(target.read_bytes()) != content_hash
            ):
                raise ProjectBackupError("artifact_closure_invalid")
            if emit_hooks:
                self._hook("backup.artifact_copy.after")

    def _snapshot_workspace(
        self,
        operation_id: str,
        *,
        destination: Optional[Path] = None,
        emit_hooks: bool = True,
    ) -> _WorkspaceSnapshot:
        source_workspace = self.workspace_dir
        self._validate_workspace_layout(source_workspace)
        if destination is None:
            destination = self.runtime_root / STAGING_DIR_NAME / operation_id / "workspace"
        if destination.exists():
            raise ProjectBackupError("backup_operation_conflict")
        destination.mkdir(parents=True, exist_ok=True)
        db_map = {
            PROFILE_DB_NAME: source_workspace / PROFILE_DB_NAME,
            RUN_BINDING_DB_NAME: source_workspace / RUN_BINDING_DB_NAME,
            LAUNCH_REGISTRY_DB_NAME: source_workspace / LAUNCH_REGISTRY_DB_NAME,
            RISK_RULE_DB_NAME: source_workspace / RISK_RULE_DB_NAME,
            RUNTIME_DIR_NAME + "/" + RUNTIME_DB_NAME: source_workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
        }
        for relative in sorted(db_map, key=lambda value: value.encode("utf-8")):
            source = db_map[relative]
            if not source.exists():
                if relative in {PROFILE_DB_NAME, RUN_BINDING_DB_NAME}:
                    raise ProjectBackupError("workspace_member_missing")
                continue
            target = destination / Path(relative)
            if emit_hooks:
                self._hook("backup.sqlite_snapshot.before")
            self._sqlite_snapshot(source, target)
            if emit_hooks:
                self._hook("backup.sqlite_snapshot.after")
        runtime_source_db = source_workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        runtime_stage_db = destination / RUNTIME_DIR_NAME / RUNTIME_DB_NAME
        artifact_hashes: Tuple[str, ...] = tuple()
        if runtime_source_db.exists():
            conn = _open_ro(runtime_stage_db)
            try:
                if emit_hooks:
                    self._hook("backup.artifact_set_freeze.before")
                artifact_hashes = self._artifact_hashes(conn)
                if emit_hooks:
                    self._hook("backup.artifact_set_freeze.after")
            finally:
                conn.close()
            source_artifact_dir = source_workspace / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME
            actual_artifact_files: set[str] = set()
            if source_artifact_dir.exists():
                _assert_directory(source_artifact_dir)
                for child in source_artifact_dir.iterdir():
                    if _is_ignorable(child):
                        continue
                    _assert_regular(child)
                    if child.suffix != ".json" or not _HEX64.match(child.stem):
                        raise ProjectBackupError("artifact_closure_invalid")
                    actual_artifact_files.add(child.stem)
            if actual_artifact_files != set(artifact_hashes):
                raise ProjectBackupError("artifact_closure_invalid")
            self._copy_artifacts(
                source_workspace,
                destination,
                artifact_hashes,
                emit_hooks=emit_hooks,
            )
            if emit_hooks:
                self._hook("backup.artifact_closure_verification.before")
            staged_conn = _open_ro(runtime_stage_db)
            try:
                staged_hashes = self._artifact_hashes(staged_conn)
            finally:
                staged_conn.close()
            for content_hash in staged_hashes:
                file_path = destination / RUNTIME_DIR_NAME / ARTIFACT_DIR_NAME / (content_hash + ".json")
                _assert_regular(file_path)
                if sha256_hex(file_path.read_bytes()) != content_hash:
                    raise ProjectBackupError("artifact_closure_invalid")
            if staged_hashes != tuple(sorted(artifact_hashes)):
                raise ProjectBackupError("artifact_closure_invalid")
            if emit_hooks:
                self._hook("backup.artifact_closure_verification.after")
        members = self._member_bytes(destination)
        fingerprint = self._fingerprint(members)
        summary = self._summarize_workspace(
            destination,
            project_name_override=self.project_name,
        )
        return _WorkspaceSnapshot(destination, members, summary, fingerprint)

    def _manifest_content_digest(
        self, manifest: Mapping[str, Any], member_bytes: Mapping[str, bytes]
    ) -> str:
        body = {key: manifest[key] for key in sorted(manifest) if key != "content_digest"}
        payload = canonical_json_bytes(body)
        for relative in sorted(member_bytes, key=lambda value: value.encode("utf-8")):
            payload += member_bytes[relative]
        return sha256_hex(payload)

    def _build_manifest(self, snapshot: _WorkspaceSnapshot) -> Dict[str, Any]:
        if self.failure_hook is not None:
            self._hook("backup.manifest_generation.before")
        descriptors = [
            {
                "path": "members/" + relative,
                "size": len(snapshot.members[relative]),
                "sha256": sha256_hex(snapshot.members[relative]),
            }
            for relative in sorted(snapshot.members, key=lambda value: value.encode("utf-8"))
        ]
        artifact_hashes = list(snapshot.summary.get("artifact_hashes", []))
        manifest: Dict[str, Any] = {
            "contract_version": CONTRACT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "canonical_project_id": self.canonical_project_id,
            "project_name": str(snapshot.summary.get("project_name", self.canonical_project_id)),
            "backup_cutoff": str(snapshot.summary.get("backup_cutoff", "未建立监查运行")),
            "members": descriptors,
            "artifact_closure": {
                "content_hashes": artifact_hashes,
                "count": len(artifact_hashes),
                "set_digest": self._set_digest(artifact_hashes),
            },
            "project_summary": dict(snapshot.summary),
            "source_workspace_fingerprint": snapshot.fingerprint,
        }
        manifest["content_digest"] = self._manifest_content_digest(manifest, snapshot.members)
        if self.failure_hook is not None:
            self._hook("backup.manifest_generation.after")
        return manifest

    @staticmethod
    def _zip_info(name: str) -> zipfile.ZipInfo:
        info = zipfile.ZipInfo(filename=name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED
        info.create_system = 3
        info.create_version = 20
        info.extract_version = 20
        info.extra = b""
        info.comment = b""
        info.external_attr = 0o100644 << 16
        info.internal_attr = 0
        info.flag_bits = 0x800
        return info

    def _write_package(
        self,
        operation_id: str,
        manifest: Mapping[str, Any],
        member_bytes: Mapping[str, bytes],
    ) -> Tuple[str, Path]:
        self.publication_dir.mkdir(parents=True, exist_ok=True)
        temp_path = self.runtime_root / ("." + operation_id + ".mmbackup.tmp")
        package_bytes: bytes
        try:
            if self.failure_hook is not None:
                self._hook("backup.package_generation.before")
            manifest_bytes = canonical_json_bytes(dict(manifest)) + b"\n"
            with zipfile.ZipFile(
                str(temp_path), mode="w", compression=zipfile.ZIP_STORED, allowZip64=False
            ) as archive:
                archive.writestr(self._zip_info("manifest.json"), manifest_bytes)
                for relative in sorted(member_bytes, key=lambda value: value.encode("utf-8")):
                    archive.writestr(
                        self._zip_info("members/" + relative), member_bytes[relative]
                    )
            with temp_path.open("rb") as handle:
                os.fsync(handle.fileno())
                package_bytes = handle.read()
            package_id = sha256_hex(package_bytes)
            with temp_path.open("rb") as handle:
                if handle.read() != package_bytes:
                    raise ProjectBackupError("backup_package_publish_failed")
            if self.failure_hook is not None:
                self._hook("backup.package_generation.after")
        except ProjectBackupError:
            raise
        except (OSError, zipfile.BadZipFile, ValueError) as exc:
            raise ProjectBackupError("backup_package_publish_failed") from exc
        published = self.publication_dir / (package_id + BACKUP_SUFFIX)
        if published.exists():
            _assert_regular(published)
            try:
                existing = published.read_bytes()
            except OSError as exc:
                raise ProjectBackupError("backup_package_publish_failed") from exc
            if existing != package_bytes:
                raise ProjectBackupError("backup_package_publish_failed")
            try:
                temp_path.unlink()
            except OSError:
                pass
            return package_id, published
        try:
            if self.failure_hook is not None:
                self._hook("backup.package_publish.before")
            os.replace(str(temp_path), str(published))
            self._fsync_dir(self.publication_dir)
            if self.failure_hook is not None:
                self._hook("backup.package_publish.after")
        except ProjectBackupError:
            raise
        except OSError as exc:
            raise ProjectBackupError("backup_package_publish_failed") from exc
        return package_id, published

    @staticmethod
    def _fsync_dir(directory: Path) -> None:
        try:
            fd = os.open(str(directory), os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(fd)
        except OSError:
            pass
        finally:
            os.close(fd)

    @staticmethod
    def _cleanup_path(path: Optional[Path]) -> None:
        if path is None or not path.exists():
            return
        try:
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(str(path))
            else:
                path.unlink()
        except OSError:
            pass

    def _manifest_from_package(self, package_path: Path) -> Dict[str, Any]:
        try:
            with zipfile.ZipFile(str(package_path), "r") as archive:
                raw = archive.read("manifest.json")
            manifest = json.loads(raw.decode("utf-8"))
        except (OSError, KeyError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            raise ProjectBackupError("package_corrupt") from exc
        if not isinstance(manifest, dict):
            raise ProjectBackupError("package_corrupt")
        return manifest

    def _package_path(self, package: Union[str, Path, PreflightResult]) -> Path:
        if isinstance(package, PreflightResult):
            return package.package_path
        path = Path(package)
        if not path.exists() and path.name and not path.suffix:
            path = self.publication_dir / (path.name + BACKUP_SUFFIX)
        if not path.exists():
            raise ProjectBackupError("package_corrupt")
        _assert_regular(path)
        try:
            if path.stat().st_size > self.max_archive_bytes:
                raise ProjectBackupError("package_corrupt")
        except OSError as exc:
            raise ProjectBackupError("package_corrupt") from exc
        return path

    def _backup_result(self, record: OperationRecord) -> BackupResult:
        path = Path(record.package_path) if record.package_path else None
        manifest: Dict[str, Any] = {}
        if path is not None and path.exists():
            try:
                manifest = self._manifest_from_package(path)
            except ProjectBackupError:
                manifest = {}
        return BackupResult(
            operation=record,
            package_id=record.package_id,
            package_path=path,
            source_workspace_fingerprint=record.source_workspace_fingerprint,
            manifest=manifest,
        )

    def _restore_result_from_record(self, record: OperationRecord) -> RestoreResult:
        payload = dict(record.payload)
        return RestoreResult(
            operation=record,
            result_label=str(payload.get("result_label", "恢复完成")),
            project_name=str(
                payload.get("project_name", self.project_name or self.canonical_project_id)
            ),
            restored_cutoff_label=str(payload.get("restored_cutoff_label", "")),
            verification_summary=str(payload.get("verification_summary", "")),
            next_action_label=str(
                payload.get("next_action_label", "继续查看监查结果")
            ),
            rollback_path=Path(record.rollback_path) if record.rollback_path else None,
        )
    def _wait_for_replayed_operation(
        self,
        record: OperationRecord,
        terminal_statuses: Sequence[str],
        *,
        timeout_seconds: float = 120.0,
    ) -> OperationRecord:
        """Join an operation already owned by another process/thread."""

        deadline = time.monotonic() + min(max(float(timeout_seconds), 0.0), 120.0)
        terminal = set(terminal_statuses)
        current = record
        while current.status not in terminal:
            if time.monotonic() >= deadline:
                return current
            time.sleep(0.01)
            current = self.ledger.get(record.operation_id)
        return current


    def snapshot_workspace(
        self,
        operation_id: str,
        *,
        destination: Optional[Path] = None,
        emit_hooks: bool = False,
    ) -> WorkspaceSnapshot:
        """Create a closure-verified workspace snapshot through the stable seam."""

        if destination is None:
            snapshot = self._current_snapshot(operation_id)
            if snapshot is None:
                raise ProjectBackupError("workspace_not_found")
            return snapshot
        return self._snapshot_workspace(
            operation_id,
            destination=destination,
            emit_hooks=emit_hooks,
        )

    current_workspace_snapshot = snapshot_workspace

    def _current_snapshot(self, operation_id: str) -> Optional[_WorkspaceSnapshot]:
        if not self.workspace_dir.exists():
            return None
        parent = Path(tempfile.mkdtemp(prefix=".mmbackup-check-", dir=str(self.runtime_root)))
        destination = parent / "workspace"
        try:
            snapshot = self._snapshot_workspace(
                operation_id,
                destination=destination,
                emit_hooks=False,
            )
        finally:
            self._cleanup_path(parent)
        return snapshot


