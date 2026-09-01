"""Workspace, database, artifact, and filesystem migration oracles."""

from .migration_contracts import *

# Workspace and schema oracles
# ---------------------------------------------------------------------------


def _canonical_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return {"__repr__": repr(value)}


def _table_rows(connection: sqlite3.Connection, table: str) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    quoted = '"' + table.replace('"', '""') + '"'
    info = connection.execute("PRAGMA table_info(%s)" % quoted).fetchall()
    columns = [str(row[1]) for row in info]
    rows = connection.execute("SELECT * FROM %s" % quoted).fetchall()
    values = [tuple(_canonical_value(value) for value in row) for row in rows]
    values.sort(key=lambda row: canonical_json_bytes(list(row)))
    return columns, values


def _database_oracle(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"present": False, "tables": {}}
    connection: Optional[sqlite3.Connection] = None
    try:
        connection = _open_ro(path)
        tables: Dict[str, Any] = {}
        for table in sorted(_table_names(connection), key=lambda value: value.encode("utf-8")):
            columns, rows = _table_rows(connection, table)
            if table in {"meta", "r7_launch_registry_meta", "profile_store_meta"}:
                filtered: List[Tuple[Any, ...]] = []
                key_index = columns.index("key") if "key" in columns else -1
                for row in rows:
                    if key_index >= 0 and row[key_index] == "schema_version":
                        continue
                    filtered.append(row)
                rows = filtered
            tables[table] = {"columns": columns, "rows": rows}
        return {"present": True, "tables": tables}
    except (ProjectBackupError, sqlite3.Error, OSError) as exc:
        raise MigrationError("sqlite_integrity_failed") from exc
    finally:
        if connection is not None:
            connection.close()


def _workspace_oracle(workspace: Path) -> Dict[str, Any]:
    if not workspace.is_dir():
        raise MigrationError("workspace_not_found")
    db_paths = {
        RUNTIME_MEMBER: workspace / RUNTIME_DIR_NAME / RUNTIME_DB_NAME,
        PROFILE_MEMBER: workspace / PROFILE_DB_NAME,
        BINDING_MEMBER: workspace / RUN_BINDING_DB_NAME,
        LAUNCH_MEMBER: workspace / LAUNCH_REGISTRY_DB_NAME,
        RISK_MEMBER: workspace / RISK_RULE_DB_NAME,
    }
    databases = {member: _database_oracle(path) for member, path in db_paths.items()}
    project_ids: set[str] = set()
    run_ids: set[str] = set()
    profile_ids: set[str] = set()
    for database in databases.values():
        for table in database.get("tables", {}).values():
            columns = table["columns"]
            rows = table["rows"]
            for row in rows:
                if "project_id" in columns:
                    project_ids.add(str(row[columns.index("project_id")]))
                if "run_id" in columns:
                    run_ids.add(str(row[columns.index("run_id")]))
                for column in ("execution_profile_id", "profile_id"):
                    if column in columns:
                        profile_ids.add(str(row[columns.index(column)]))
    return {
        "databases": databases,
        "project_ids": sorted(project_ids),
        "run_ids": sorted(run_ids),
        "profile_ids": sorted(profile_ids),
    }


def _compare_database_oracles(before: Mapping[str, Any], after: Mapping[str, Any]) -> None:
    before_databases = before.get("databases", {})
    after_databases = after.get("databases", {})
    if before.get("project_ids") != after.get("project_ids"):
        raise MigrationError("migration_verification_failed")
    if before.get("run_ids") != after.get("run_ids"):
        raise MigrationError("migration_verification_failed")
    if before.get("profile_ids") != after.get("profile_ids"):
        raise MigrationError("migration_verification_failed")
    for member, old_database in before_databases.items():
        if not old_database.get("present"):
            continue
        new_database = after_databases.get(member, {})
        if not new_database.get("present"):
            raise MigrationError("migration_verification_failed")
        old_tables = old_database.get("tables", {})
        new_tables = new_database.get("tables", {})
        for table_name, old_table in old_tables.items():
            new_table = new_tables.get(table_name)
            if new_table is None:
                raise MigrationError("migration_verification_failed")
            old_columns = list(old_table.get("columns", []))
            new_columns = list(new_table.get("columns", []))
            common_columns = [column for column in old_columns if column in new_columns]
            old_index = [old_columns.index(column) for column in common_columns]
            new_index = [new_columns.index(column) for column in common_columns]
            old_rows = [tuple(row[index] for index in old_index) for row in old_table.get("rows", [])]
            new_rows = [tuple(row[index] for index in new_index) for row in new_table.get("rows", [])]
            old_rows.sort(key=lambda row: canonical_json_bytes(list(row)))
            new_rows.sort(key=lambda row: canonical_json_bytes(list(row)))
            if old_rows != new_rows:
                raise MigrationError("migration_verification_failed")


def _artifact_hashes_and_bytes(manager: ProjectBackupManager, workspace: Path) -> Dict[str, bytes]:
    """Use the public 09A closure primitive for migration verification."""

    try:
        return manager.artifact_closure(workspace)
    except (ProjectBackupError, OSError, sqlite3.Error, ValueError, TypeError) as exc:
        raise MigrationError("migration_verification_failed") from exc


def _compare_artifacts(before: Mapping[str, bytes], after: Mapping[str, bytes]) -> None:
    if tuple(before) != tuple(after):
        raise MigrationError("migration_verification_failed")
    for key in before:
        if before[key] != after[key]:
            raise MigrationError("migration_verification_failed")


def _remove_sqlite_sidecars(workspace: Path) -> None:
    """Remove SQLite sidecars from an isolated, closed staging copy."""
    for root, dirs, files in os.walk(str(workspace)):
        for name in files:
            if name.endswith("-wal") or name.endswith("-shm") or name.endswith("-journal"):
                try:
                    (Path(root) / name).unlink()
                except OSError as exc:
                    raise MigrationError("migration_verification_failed") from exc


def _assert_no_sqlite_sidecars(workspace: Path) -> None:
    for root, dirs, files in os.walk(str(workspace)):
        dirs[:] = [
            name for name in dirs
            if name not in {".migration-staging", MIGRATION_ROLLBACK_DIR_NAME}
        ]
        for name in files:
            if name.endswith("-wal") or name.endswith("-shm") or name.endswith("-journal"):
                raise MigrationError("migration_verification_failed")


def _assert_same_device(*paths: Path) -> None:
    devices: set[int] = set()
    for path in paths:
        candidate = path
        while not candidate.exists() and candidate != candidate.parent:
            candidate = candidate.parent
        try:
            devices.add(int(os.stat(str(candidate)).st_dev))
        except OSError as exc:
            raise MigrationError("cross_filesystem_staging_not_supported") from exc
    if len(devices) != 1:
        raise MigrationError("cross_filesystem_staging_not_supported")

def _replace_or_raise(source: Path, destination: Path) -> None:
    try:
        os.replace(str(source), str(destination))
    except OSError as exc:
        if exc.errno == errno.EXDEV:
            raise MigrationError("cross_filesystem_staging_not_supported") from exc
        raise


def _replaceable(path: Path) -> bool:
    try:
        return path.is_dir() and not path.is_symlink()
    except OSError:
        return False


__all__ = [name for name in globals() if not name.startswith("__")]
