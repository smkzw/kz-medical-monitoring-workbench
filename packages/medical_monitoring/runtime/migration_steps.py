"""SQLite schema migration steps and marker-last step runner."""

from .migration_contracts import *
from .migration_oracles import *

# ---------------------------------------------------------------------------
# SQLite migration steps
# ---------------------------------------------------------------------------

_RUNTIME_CAPABILITY_DDL = """
CREATE TABLE IF NOT EXISTS work_unit_capability_attempts (
    run_id TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL,
    work_unit_id TEXT NOT NULL,
    attempt_ordinal INTEGER NOT NULL CHECK (attempt_ordinal >= 1),
    attempt_id TEXT NOT NULL UNIQUE REFERENCES capability_attempt_journal(attempt_id),
    detail TEXT NOT NULL,
    execution_identity_json TEXT NOT NULL,
    identity_hash TEXT NOT NULL,
    bound_at TEXT NOT NULL,
    PRIMARY KEY (run_id, manifest_revision, work_unit_id, attempt_ordinal),
    UNIQUE (run_id, manifest_revision, work_unit_id, attempt_id),
    FOREIGN KEY (run_id, manifest_revision, work_unit_id)
        REFERENCES work_unit_runs(run_id, manifest_revision, work_unit_id)
);
CREATE INDEX IF NOT EXISTS idx_work_unit_capability_attempts_unit
    ON work_unit_capability_attempts(run_id, manifest_revision, work_unit_id);
"""

# Launch table/index DDL is centralized in ``launch_schema`` and shared by
# construction, manifest inspection, and these marker-last migrations.


def _split_sql(sql: str) -> Tuple[str, ...]:
    return tuple(statement.strip() for statement in sql.split(";") if statement.strip())


def _shape_for(connection: sqlite3.Connection, member: str) -> Dict[str, Any]:
    try:
        shape = copy.deepcopy(_schema._connection_shape(connection))
    except (AttributeError, sqlite3.Error) as exc:
        raise MigrationError("migration_verification_failed") from exc
    if member == RUNTIME_MEMBER:
        shape["tables"].pop("r7_execution_control", None)
    return shape


def _target_variant(member: str, version: str) -> Mapping[str, Any]:
    manifest = get_schema_manifest()
    try:
        return manifest["members"][member]["versions"][version]
    except (KeyError, TypeError) as exc:
        raise MigrationError("migration_ledger_corrupt") from exc


def _assert_shape_on_connection(
    connection: sqlite3.Connection, member: str, version: str
) -> None:
    expected = _target_variant(member, version)["shape"]
    actual = _shape_for(connection, member)
    if actual != expected:
        raise MigrationError("migration_verification_failed")


def _read_meta_marker(connection: sqlite3.Connection, member: str) -> Optional[str]:
    if member == RUNTIME_MEMBER:
        row = connection.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        return None if row is None else str(row[0])
    if member == LAUNCH_MEMBER:
        row = connection.execute(
            "SELECT value FROM r7_launch_registry_meta WHERE key='schema_version'"
        ).fetchone()
        return None if row is None else str(row[0])
    return None


def _table_columns_ordered(connection: sqlite3.Connection, table: str) -> List[str]:
    quoted = '"' + table.replace('"', '""') + '"'
    return [str(row[1]) for row in connection.execute("PRAGMA table_info(%s)" % quoted).fetchall()]
def _frozen_create_statement(ddl: str, table: str) -> str:
    """Extract one independent CREATE TABLE statement from frozen DDL."""
    pattern = re.compile(
        r"^CREATE TABLE IF NOT EXISTS\s+" + re.escape(table) + r"\s*\(",
        re.IGNORECASE,
    )
    for statement in _split_sql(ddl):
        if pattern.search(statement):
            return statement
    raise MigrationError("migration_ledger_corrupt")


def _frozen_index_statements(ddl: str, table: str) -> Tuple[str, ...]:
    pattern = re.compile(
        r"^CREATE INDEX IF NOT EXISTS\s+\S+\s+ON\s+" + re.escape(table) + r"\s*\(",
        re.IGNORECASE,
    )
    return tuple(statement for statement in _split_sql(ddl) if pattern.search(statement))


def _runtime_manifest_revision(
    connection: sqlite3.Connection, run_id: Any, observed_at: Any
) -> int:
    row = connection.execute(
        "SELECT revision FROM run_manifests WHERE run_id=? AND created_at<=? "
        "ORDER BY revision DESC LIMIT 1",
        (run_id, observed_at or ""),
    ).fetchone()
    return 0 if row is None else int(row[0])


def _rebuild_runtime_table(
    connection: sqlite3.Connection,
    table: str,
    old_columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    revisions: Sequence[int],
) -> None:
    """Rebuild a v4 table so the added column has frozen-order placement."""
    old_name = "__migration_old_" + table
    create = _frozen_create_statement(_schema._R1_DDL, table)
    if table == "node_attempts":
        expected_old = [
            "run_id",
            "node_id",
            "attempt_seq",
            "idempotency_key",
            "logical_key",
            "status",
            "payload_hash",
            "created_at",
        ]
    else:
        expected_old = [
            "run_id",
            "node_id",
            "node_type",
            "status",
            "idempotency_key",
            "attempts",
            "artifact_id",
            "output_json",
            "error",
            "reason",
            "started_at",
            "finished_at",
        ]
    if list(old_columns) != expected_old:
        raise MigrationError("migration_verification_failed")
    # Drop the old named indexes before renaming the table.  SQLite keeps
    # index names across ALTER TABLE ... RENAME, so leaving them in place
    # would prevent recreating the frozen current indexes.
    for statement in _frozen_index_statements(_schema._R1_DDL, table):
        match = re.search(
            r"^CREATE INDEX IF NOT EXISTS\s+(\S+)", statement, re.IGNORECASE
        )
        if match:
            connection.execute("DROP INDEX IF EXISTS " + match.group(1))
    connection.execute("ALTER TABLE %s RENAME TO %s" % (table, old_name))
    connection.execute(create)
    target_columns = _table_columns_ordered(connection, table)
    placeholders = ",".join("?" for _ in target_columns)
    connection.executemany(
        "INSERT INTO %s (%s) VALUES (%s)" % (
            table,
            ",".join(target_columns),
            placeholders,
        ),
        [
            tuple(
                (revision if column == "manifest_revision" else row[old_columns.index(column)])
                for column in target_columns
            )
            for row, revision in zip(rows, revisions)
        ],
    )
    connection.execute("DROP TABLE %s" % old_name)
    for statement in _frozen_index_statements(_schema._R1_DDL, table):
        connection.execute(statement)
def _drop_named_indexes(
    connection: sqlite3.Connection, statements: Sequence[str]
) -> None:
    for statement in statements:
        match = re.search(
            r"^CREATE(?: UNIQUE)? INDEX IF NOT EXISTS\s+(\S+)",
            statement,
            re.IGNORECASE,
        )
        if match:
            connection.execute("DROP INDEX IF EXISTS " + match.group(1))


def _rebuild_table_from_ddl(
    connection: sqlite3.Connection,
    table: str,
    ddl: str,
    old_columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    defaults: Optional[Mapping[str, Any]] = None,
) -> None:
    old_name = "__migration_old_" + table
    if old_name in _table_names(connection):
        raise MigrationError("migration_operation_conflict")
    create = _frozen_create_statement(ddl, table)
    connection.execute("ALTER TABLE %s RENAME TO %s" % (table, old_name))
    connection.execute(create)
    target_columns = _table_columns_ordered(connection, table)
    values = []
    defaults = dict(defaults or {})
    for row in rows:
        values.append(
            tuple(
                row[old_columns.index(column)]
                if column in old_columns
                else defaults.get(column)
                for column in target_columns
            )
        )
    placeholders = ",".join("?" for _ in target_columns)
    if values:
        connection.executemany(
            "INSERT INTO %s (%s) VALUES (%s)" % (
                table,
                ",".join(target_columns),
                placeholders,
            ),
            values,
        )
    connection.execute("DROP TABLE %s" % old_name)


def _rebuild_launch_publication_v3(connection: sqlite3.Connection) -> None:
    table = "r7_result_publications"
    old_columns = _table_columns_ordered(connection, table)
    rows = connection.execute("SELECT * FROM %s ORDER BY rowid" % table).fetchall()
    _drop_named_indexes(
        connection,
        _split_sql(_PUBLICATION_DDL) + _split_sql(_RESULT_CONTEXT_INDEX_DDL),
    )
    _rebuild_table_from_ddl(
        connection,
        table,
        _PUBLICATION_DDL,
        old_columns,
        rows,
        {
            "r6_output_set_digest": None,
            "artifact_member_ids_json": "[]",
            "artifact_member_set_digest": None,
        },
    )
    _execute = _split_sql(_PUBLICATION_DDL)
    for statement in _execute:
        if statement.upper().startswith("CREATE INDEX"):
            connection.execute(statement)
    for statement in _split_sql(_RESULT_CONTEXT_INDEX_DDL):
        connection.execute(statement)


def _rebuild_launch_continuity_v3(connection: sqlite3.Connection) -> None:
    plan_table = "r7_continuity_plans"
    item_table = "r7_continuity_items"
    plan_columns = _table_columns_ordered(connection, plan_table)
    item_columns = _table_columns_ordered(connection, item_table)
    plan_rows = connection.execute("SELECT * FROM %s ORDER BY rowid" % plan_table).fetchall()
    item_rows = connection.execute("SELECT * FROM %s ORDER BY rowid" % item_table).fetchall()
    _drop_named_indexes(connection, _split_sql(_CONTINUITY_INDEX_DDL))
    old_plan = "__migration_old_" + plan_table
    old_item = "__migration_old_" + item_table
    connection.execute("ALTER TABLE %s RENAME TO %s" % (item_table, old_item))
    connection.execute("ALTER TABLE %s RENAME TO %s" % (plan_table, old_plan))
    connection.execute(_frozen_create_statement(_CONTINUITY_PLANS_DDL, plan_table))
    connection.execute(_frozen_create_statement(_CONTINUITY_ITEMS_DDL, item_table))
    new_plan_columns = _table_columns_ordered(connection, plan_table)
    new_item_columns = _table_columns_ordered(connection, item_table)
    plan_values = [
        tuple(
            row[plan_columns.index(column)] if column in plan_columns
            else ("" if column == "r6_output_set_digest" else None)
            for column in new_plan_columns
        )
        for row in plan_rows
    ]
    item_values = [
        tuple(
            row[item_columns.index(column)] for column in new_item_columns
        )
        for row in item_rows
    ]
    if plan_values:
        connection.executemany(
            "INSERT INTO %s (%s) VALUES (%s)" % (
                plan_table,
                ",".join(new_plan_columns),
                ",".join("?" for _ in new_plan_columns),
            ),
            plan_values,
        )
    if item_values:
        connection.executemany(
            "INSERT INTO %s (%s) VALUES (%s)" % (
                item_table,
                ",".join(new_item_columns),
                ",".join("?" for _ in new_item_columns),
            ),
            item_values,
        )
    connection.execute("DROP TABLE %s" % old_item)
    connection.execute("DROP TABLE %s" % old_plan)
    for statement in _split_sql(_CONTINUITY_INDEX_DDL):
        connection.execute(statement)


class _StepRunner:
    def __init__(self, owner: "MigrationRunner", step: MigrationStep) -> None:
        self.owner = owner
        self.step = step
        self.committed = False

    def _hook(self, suffix: str) -> None:
        self.owner._hook("migration.%s.%s" % (self.step.member, suffix))

    def _execute_statements(self, connection: sqlite3.Connection, sql: str) -> None:
        for statement in _split_sql(sql):
            connection.execute(statement)
    def _runtime_backfill(self, connection: sqlite3.Connection) -> None:
        if self.step.source_version != RUNTIME_V4:
            return
        # Added columns default to 0.  Reconstruct historical revisions from
        # immutable manifest timestamps, matching R1's accepted v4 migration
        # oracle without importing the mutable Store constructor.
        node_attempt_columns = _table_columns_ordered(connection, "node_attempts")
        if "manifest_revision" in node_attempt_columns:
            rows = connection.execute(
                "SELECT run_id,node_id,attempt_seq,created_at FROM node_attempts "
                "ORDER BY run_id,node_id,attempt_seq"
            ).fetchall()
            for run_id, node_id, attempt_seq, created_at in rows:
                revision_row = connection.execute(
                    "SELECT revision FROM run_manifests WHERE run_id=? AND created_at<=? "
                    "ORDER BY revision DESC LIMIT 1",
                    (run_id, created_at or ""),
                ).fetchone()
                revision = 0 if revision_row is None else int(revision_row[0])
                connection.execute(
                    "UPDATE node_attempts SET manifest_revision=? WHERE run_id=? "
                    "AND node_id=? AND attempt_seq=?",
                    (revision, run_id, node_id, int(attempt_seq)),
                )
        node_run_columns = _table_columns_ordered(connection, "node_runs")
        if "manifest_revision" in node_run_columns:
            rows = connection.execute(
                "SELECT run_id,node_id,started_at FROM node_runs ORDER BY run_id,node_id"
            ).fetchall()
            for run_id, node_id, started_at in rows:
                latest = connection.execute(
                    "SELECT manifest_revision FROM node_attempts WHERE run_id=? AND node_id=? "
                    "ORDER BY attempt_seq DESC LIMIT 1",
                    (run_id, node_id),
                ).fetchone()
                if latest is not None:
                    revision = int(latest[0])
                else:
                    revision_row = connection.execute(
                        "SELECT revision FROM run_manifests WHERE run_id=? AND created_at<=? "
                        "ORDER BY revision DESC LIMIT 1",
                        (run_id, started_at or ""),
                    ).fetchone()
                    revision = 0 if revision_row is None else int(revision_row[0])
                connection.execute(
                    "UPDATE node_runs SET manifest_revision=? WHERE run_id=? AND node_id=?",
                    (revision, run_id, node_id),
                )

    def _rebuild_runtime_columns(self, connection: sqlite3.Connection) -> None:
        if self.step.source_version != RUNTIME_V4:
            return
        for table in ("node_attempts", "node_runs"):
            old_columns = _table_columns_ordered(connection, table)
            rows = connection.execute(
                "SELECT * FROM %s ORDER BY rowid" % table
            ).fetchall()
            if table == "node_attempts":
                revisions = [
                    _runtime_manifest_revision(connection, row[0], row[7])
                    for row in rows
                ]
            else:
                revisions = [
                    _runtime_manifest_revision(connection, row[0], row[10])
                    for row in rows
                ]
            _rebuild_runtime_table(connection, table, old_columns, rows, revisions)

    def _rebuild_launch_v4_columns(self, connection: sqlite3.Connection) -> None:
        if self.step.source_version != LAUNCH_V3:
            return
        _rebuild_launch_publication_v3(connection)
        _rebuild_launch_continuity_v3(connection)

    @staticmethod
    def _add_v5_publication_columns(connection: sqlite3.Connection) -> None:
        """W01-R26（20260926）：v4→v5仅新增两个可空冻结read model引用列。

        守卫式ALTER：先读PRAGMA table_info，缺列才ADD COLUMN。不重建表、
        不改写既有行数据，ADD-if-absent使已提交步骤可安全重放。
        """
        existing_columns = {
            str(row["name"])
            for row in connection.execute(
                "PRAGMA table_info(r7_result_publications)"
            )
        }
        for column in (
            "frozen_read_model_artifact_id",
            "frozen_read_model_sha256",
        ):
            if column not in existing_columns:
                connection.execute(
                    "ALTER TABLE r7_result_publications "
                    f"ADD COLUMN {column} TEXT"
                )

    def _launch_ddl(self, connection: sqlite3.Connection) -> None:
        version = self.step.source_version
        # v1 has no publication or continuity tables, v2 has no continuity,
        # v3 has the tables but lacks four v4 columns, and v4 only lacks the
        # two nullable frozen-read-model reference columns.  CREATE IF NOT
        # EXISTS and ADD-if-absent make a committed step replay-safe.
        if version == LAUNCH_V1:
            self._execute_statements(connection, _PUBLICATION_DDL)
            self._execute_statements(connection, _RESULT_CONTEXT_INDEX_DDL)
            self._execute_statements(connection, _CONTINUITY_PLANS_DDL)
            self._execute_statements(connection, _CONTINUITY_ITEMS_DDL)
            self._execute_statements(connection, _CONTINUITY_INDEX_DDL)
        elif version == LAUNCH_V2:
            self._execute_statements(connection, _RESULT_CONTEXT_INDEX_DDL)
            self._execute_statements(connection, _CONTINUITY_PLANS_DDL)
            self._execute_statements(connection, _CONTINUITY_ITEMS_DDL)
            self._execute_statements(connection, _CONTINUITY_INDEX_DDL)
        elif version == LAUNCH_V3:
            self._rebuild_launch_v4_columns(connection)
            self._execute_statements(connection, _RESULT_CONTEXT_INDEX_DDL)
            self._execute_statements(connection, _CONTINUITY_INDEX_DDL)
        elif version == LAUNCH_V4:
            self._add_v5_publication_columns(connection)
        else:
            raise MigrationError("migration_operation_conflict")

    def run(self, path: Path) -> None:
        if not self.owner._is_staging_path(path):
            raise MigrationError("migration_requires_staging")
        connection: Optional[sqlite3.Connection] = None
        transaction_started = False
        try:
            connection = sqlite3.connect(
                str(path), timeout=10.0, isolation_level=None, check_same_thread=False
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA busy_timeout=10000")
            connection.execute("PRAGMA foreign_keys=ON")
            marker = _read_meta_marker(connection, self.step.member)
            if marker != self.step.source_version:
                # A committed step may have advanced the target marker while
                # the ledger was not advanced.  Structural + marker oracles
                # make that state safely idempotent.
                if marker == self.step.target_version:
                    _assert_shape_on_connection(connection, self.step.member, str(self.step.target_version))
                    return
                raise MigrationError("migration_operation_conflict")
            self._hook("ddl.before")
            connection.execute("BEGIN IMMEDIATE")
            transaction_started = True
            if self.step.member == RUNTIME_MEMBER:
                self._rebuild_runtime_columns(connection)
                self._execute_statements(connection, _RUNTIME_CAPABILITY_DDL)
            elif self.step.member == LAUNCH_MEMBER:
                self._launch_ddl(connection)
            else:
                raise MigrationError("migration_operation_conflict")
            self._hook("ddl.after")
            if self.step.member == RUNTIME_MEMBER and self.step.source_version == RUNTIME_V4:
                self._hook("backfill.before")
                self._runtime_backfill(connection)
                self._hook("backfill.after")
            self._hook("oracle.before")
            _assert_shape_on_connection(connection, self.step.member, str(self.step.target_version))
            foreign_rows = connection.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_rows:
                raise MigrationError("migration_verification_failed")
            self._hook("oracle.after")
            self._hook("marker.before")
            if self.step.member == RUNTIME_MEMBER:
                connection.execute(
                    "UPDATE meta SET value=? WHERE key='schema_version'",
                    (self.step.target_version,),
                )
            else:
                connection.execute(
                    "UPDATE r7_launch_registry_meta SET value=? WHERE key='schema_version'",
                    (self.step.target_version,),
                )
            self._hook("marker.after")
            self._hook("commit.before")
            connection.commit()
            self.committed = True
            try:
                self._hook("commit.after")
            except BaseException as exc:
                raise _CommittedStepFailure(
                    "migration.%s.commit.after" % self.step.member, exc
                ) from exc
        except _CommittedStepFailure:
            raise
        except BaseException:
            if connection is not None and transaction_started and not self.committed:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
            raise
        finally:
            if connection is not None:
                connection.close()


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------


__all__ = [name for name in globals() if not name.startswith("__")]
