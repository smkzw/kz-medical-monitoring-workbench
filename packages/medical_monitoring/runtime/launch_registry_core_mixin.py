"""Launch registry lifecycle and run reservation."""

from __future__ import annotations

import datetime as _datetime
import hashlib
import json
import math
import sqlite3
import threading
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Tuple, Union
from uuid import uuid4

from .continuity import (
    CarryForwardItem,
    CarryForwardPlan,
    PlanValidationError,
    validate_carry_forward_plan,
)

from .launch_schema import (
    BASE_DDL as _BASE_DDL,
    CONTINUITY_DDL as _CONTINUITY_DDL,
    CONTINUITY_INDEX_DDL as _CONTINUITY_INDEX_DDL,
    CONTINUITY_ITEMS_DDL as _CONTINUITY_ITEMS_DDL,
    CONTINUITY_PLANS_DDL as _CONTINUITY_PLANS_DDL,
    LAUNCH_DDL as _DDL,
    PUBLICATION_DDL as _PUBLICATION_DDL,
    RESULT_CONTEXT_INDEX_DDL as _RESULT_CONTEXT_INDEX_DDL,
)

from .launch_registry_contracts import *
from .launch_registry_contracts import (
    _DEFAULT_MAIN_ACTION, _RESULT_MAIN_ACTION, _assert_current_schema,
    _decode_publication_object, _decode_token_list, _normalize_comparison_range,
    _normalize_result_context_token, _optional_text, _required_text,
)

class LaunchRegistryCoreMixin:
    """Cohesive methods extracted from the launch registry."""

    def __init__(
        self,
        db_path: Union[str, Path],
        *,
        project_id: str = "",
        busy_timeout_ms: int = BUSY_TIMEOUT_MS,
        default_history_limit: int = DEFAULT_HISTORY_LIMIT,
        max_history_limit: int = MAX_HISTORY_LIMIT,
        history_limit: Optional[int] = None,
        failure_injector: Optional[Callable[[str], None]] = None,
        failure_hook: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._path = Path(db_path)
        _assert_current_schema(self._path)
        if self._path.parent and str(self._path.parent) not in ("", "."):
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self._default_project_id = (
            _required_text(project_id, "invalid_project_id") if project_id else ""
        )
        if history_limit is not None:
            default_history_limit = history_limit
        if (
            isinstance(busy_timeout_ms, bool)
            or not isinstance(busy_timeout_ms, int)
            or busy_timeout_ms <= 0
        ):
            raise LaunchRegistryError("invalid_history_limit")
        if (
            isinstance(default_history_limit, bool)
            or not isinstance(default_history_limit, int)
            or default_history_limit < 0
        ):
            raise LaunchRegistryError("invalid_history_limit")
        if (
            isinstance(max_history_limit, bool)
            or not isinstance(max_history_limit, int)
            or max_history_limit < 1
        ):
            raise LaunchRegistryError("invalid_history_limit")
        self._busy_timeout_ms = busy_timeout_ms
        self._default_history_limit = min(default_history_limit, max_history_limit)
        self._max_history_limit = max_history_limit
        self._failure_injector = (
            failure_injector if failure_injector is not None else failure_hook
        )
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        self.open()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def busy_timeout_ms(self) -> int:
        return self._busy_timeout_ms

    @property
    def schema_version(self) -> str:
        with self._lock:
            row = self._require_conn().execute(
                "SELECT value FROM r7_launch_registry_meta WHERE key = ?",
                ("schema_version",),
            ).fetchone()
        if row is None or str(row["value"]) != SCHEMA_VERSION:
            raise LaunchRegistryError("unsupported_schema_version")
        return str(row["value"])

    def set_failure_injector(
        self, injector: Optional[Callable[[str], None]]
    ) -> None:
        self._failure_injector = injector

    def _inject_failure(self, point: str) -> None:
        hook = self._failure_injector
        if hook is not None:
            hook(str(point))

    @staticmethod
    def _execute_script_in_transaction(
        connection: sqlite3.Connection, script: str
    ) -> None:
        # ``executescript`` commits an open transaction on CPython. Split this
        # fixed internal DDL into statements so initialization remains atomic.
        for statement in script.split(";"):
            sql = statement.strip()
            if sql:
                connection.execute(sql)

    def open(self) -> None:
        with self._lock:
            if self._conn is not None:
                return
            _assert_current_schema(self._path)
            connection: Optional[sqlite3.Connection] = None
            transaction_started = False
            try:
                connection = sqlite3.connect(
                    str(self._path),
                    timeout=self._busy_timeout_ms / 1000.0,
                    isolation_level=None,
                    check_same_thread=False,
                )
                connection.row_factory = sqlite3.Row
                # Set both the driver timeout and SQLite's connection pragma;
                # the latter is observable and applies to lock waits in every
                # explicit transaction on this connection.
                connection.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute("BEGIN IMMEDIATE")
                transaction_started = True
                self._execute_script_in_transaction(connection, _BASE_DDL)
                row = connection.execute(
                    "SELECT value FROM r7_launch_registry_meta WHERE key = ?",
                    ("schema_version",),
                ).fetchone()
                version = None if row is None else str(row["value"])
                if version is None:
                    # A missing file is born at the current schema in one
                    # transaction; existing legacy files were rejected above.
                    self._execute_script_in_transaction(connection, _PUBLICATION_DDL)
                    self._execute_script_in_transaction(connection, _RESULT_CONTEXT_INDEX_DDL)
                    self._execute_script_in_transaction(connection, _CONTINUITY_DDL)
                    self._execute_script_in_transaction(connection, _CONTINUITY_INDEX_DDL)
                    connection.execute(
                        "INSERT INTO r7_launch_registry_meta(key, value) VALUES (?, ?)",
                        ("schema_version", SCHEMA_VERSION),
                    )
                elif version == SCHEMA_VERSION_V4:
                    # W01-R26（20260926）：v4→v5仅新增两个可空冻结read
                    # model引用列。守卫式ALTER原地升级：先查PRAGMA再ADD
                    # COLUMN，不重建表、不改写任何既有行数据；同一事务内
                    # 推进marker，保证打开即达当前schema。
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
                    connection.execute(
                        "UPDATE r7_launch_registry_meta SET value = ? "
                        "WHERE key = 'schema_version'",
                        (SCHEMA_VERSION,),
                    )
                elif version != SCHEMA_VERSION:
                    raise LaunchRegistryError("unsupported_schema_version")
                connection.commit()
                self._conn = connection
            except LaunchRegistryError:
                if connection is not None and transaction_started:
                    try:
                        connection.rollback()
                    except sqlite3.Error:
                        pass
                if connection is not None:
                    connection.close()
                raise
            except Exception as exc:
                if connection is not None and transaction_started:
                    try:
                        connection.rollback()
                    except sqlite3.Error:
                        pass
                if connection is not None:
                    connection.close()
                raise LaunchRegistryError("store_closed") from exc

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def reopen(self) -> None:
        with self._lock:
            self.close()
            self.open()

    def __enter__(self) -> "LaunchRegistry":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise LaunchRegistryError("store_closed")
        return self._conn

    def _project(self, project_id: Optional[str]) -> str:
        value = self._default_project_id if project_id is None else project_id
        return _required_text(value, "invalid_project_id")

    @staticmethod
    def _now() -> str:
        return _datetime.datetime.now(_datetime.timezone.utc).isoformat(timespec="milliseconds")

    @staticmethod
    def _default_action(state: str, result_available: bool) -> str:
        return _RESULT_MAIN_ACTION if state == STATE_COMPLETED and result_available else _DEFAULT_MAIN_ACTION

    def _row_to_record(self, row: sqlite3.Row) -> LaunchRecord:
        try:
            raw_rules = json.loads(str(row["rule_tokens_json"]))
        except (TypeError, json.JSONDecodeError) as exc:
            raise LaunchRegistryError("store_closed") from exc
        if not isinstance(raw_rules, list) or any(not isinstance(item, str) for item in raw_rules):
            raise LaunchRegistryError("store_closed")
        record = LaunchRecord(
            sequence=int(row["sequence"]),
            project_id=str(row["project_id"]),
            idempotency_key=str(row["idempotency_key"]),
            run_id=str(row["run_id"]),
            public_run_token=str(row["public_run_token"]),
            request_fingerprint=str(row["request_fingerprint"]),
            mode=str(row["mode"]),
            execution_basis=str(row["execution_basis"]),
            current_snapshot_token=str(row["current_snapshot_token"]),
            baseline_token=(str(row["baseline_token"]) if row["baseline_token"] is not None else None),
            rule_tokens=tuple(raw_rules),
            data_cutoff=str(row["data_cutoff"]),
            comparison_range_text=str(row["comparison_range_text"]),
            run_state=str(row["run_state"]),
            result_available=bool(int(row["result_available"])),
            main_action=str(row["main_action"]),
            manifest_digest=(str(row["manifest_digest"]) if row["manifest_digest"] is not None else None),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
        if record.mode not in SUPPORTED_MODES or record.run_state not in RUN_STATE_VALUES:
            raise LaunchRegistryError("store_closed")
        if record.result_available and record.run_state != STATE_COMPLETED:
            raise LaunchRegistryError("store_closed")
        try:
            request = LaunchRequest(
                project_id=record.project_id,
                idempotency_key=record.idempotency_key,
                mode=record.mode,
                execution_basis=record.execution_basis,
                current_snapshot_token=record.current_snapshot_token,
                baseline_token=record.baseline_token,
                rule_tokens=record.rule_tokens,
            )
        except LaunchRegistryError as exc:
            raise LaunchRegistryError("store_closed") from exc
        if (
            request.rule_tokens != record.rule_tokens
            or request.request_fingerprint != record.request_fingerprint
            or derive_public_run_token(record.project_id, record.run_id) != record.public_run_token
            or record.main_action != self._default_action(record.run_state, record.result_available)
        ):
            raise LaunchRegistryError("store_closed")
        return record

    def _find_by_key(self, project: str, idempotency_key: str) -> Optional[LaunchRecord]:
        row = self._require_conn().execute(
            "SELECT * FROM r7_launch_registry WHERE project_id = ? AND idempotency_key = ?",
            (project, idempotency_key),
        ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def _find_by_selector(self, project: str, selector: str) -> Optional[LaunchRecord]:
        row = self._require_conn().execute(
            "SELECT * FROM r7_launch_registry "
            "WHERE project_id = ? AND (public_run_token = ? OR run_id = ?)",
            (project, selector, selector),
        ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def _find_in_flight_locked(
        self, connection: sqlite3.Connection, project: str
    ) -> Optional[LaunchRecord]:
        row = connection.execute(
            "SELECT launch.* FROM r7_launch_registry AS launch "
            "WHERE launch.project_id = ? AND ("
            "launch.run_state IN (?, ?, ?, ?) "
            "OR (launch.run_state = ? AND launch.result_available = 0)"
            ") ORDER BY launch.created_at DESC, launch.sequence DESC LIMIT 1",
            (
                project,
                STATE_WAITING_START,
                STATE_RUNNING,
                STATE_STOPPING,
                STATE_INTERRUPTED_RESUMABLE,
                STATE_COMPLETED,
            ),
        ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def get_in_flight(
        self, project_id: Optional[str] = None
    ) -> Optional[LaunchRecord]:
        project = self._project(project_id)
        with self._lock:
            return self._find_in_flight_locked(self._require_conn(), project)

    def has_in_flight(self, project_id: Optional[str] = None) -> bool:
        return self.get_in_flight(project_id) is not None

    in_flight = get_in_flight

    def _row_to_publication(
        self, row: sqlite3.Row, *, replayed: bool = False
    ) -> ResultPublication:
        try:
            state = str(row["publication_state"])
            revision = int(row["publication_revision"])
            manifest_revision = (
                int(row["manifest_revision"])
                if row["manifest_revision"] is not None
                else None
            )
            mandatory_denominator = int(row["mandatory_denominator"])
            site_coverage = _decode_token_list(row["site_coverage_json"])
            receipt_identities = _decode_token_list(row["receipt_identities_json"])
            s4_identities = _decode_token_list(
                row["s4_authority_packet_identities_json"]
            )
            s4_digests = _decode_token_list(row["s4_authority_packet_digests_json"])
            setup_identity = _decode_publication_object(
                row["setup_manifest_identity_json"]
            )
            runtime_identity = _decode_publication_object(
                row["runtime_manifest_identity_json"]
            )
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise LaunchRegistryError("store_closed") from exc
        if (
            state not in PUBLICATION_STATE_VALUES
            or revision != PUBLICATION_REVISION
            or manifest_revision is not None and manifest_revision < 1
            or mandatory_denominator < 0
        ):
            raise LaunchRegistryError("store_closed")
        project = str(row["project_id"])
        run_id = str(row["run_id"])
        public_token = str(row["public_run_token"])
        try:
            result_context_token = _normalize_result_context_token(
                row["result_context_token"]
            )
        except LaunchRegistryError as exc:
            raise LaunchRegistryError("store_closed") from exc
        if derive_public_run_token(project, run_id) != public_token:
            raise LaunchRegistryError("store_closed")
        mode = str(row["mode"])
        basis = str(row["execution_basis"])
        if mode not in SUPPORTED_MODES or basis not in SUPPORTED_EXECUTION_BASES:
            raise LaunchRegistryError("store_closed")
        try:
            snapshot_token = _required_text(
                str(row["snapshot_token"]), "invalid_snapshot_token"
            )
            fingerprint = _required_text(
                str(row["publication_fingerprint"]), "invalid_publication_fingerprint"
            )
            data_cutoff = _required_text(str(row["data_cutoff"]), "invalid_data_cutoff")
            key = _required_text(str(row["idempotency_key"]), "invalid_idempotency_key")
        except LaunchRegistryError as exc:
            raise LaunchRegistryError("store_closed") from exc
        r6_output_set_digest = (
            str(row["r6_output_set_digest"])
            if "r6_output_set_digest" in row.keys()
            and row["r6_output_set_digest"] is not None
            else None
        )
        artifact_member_ids = (
            _decode_token_list(row["artifact_member_ids_json"])
            if "artifact_member_ids_json" in row.keys()
            and row["artifact_member_ids_json"] is not None
            else ()
        )
        artifact_member_set_digest = (
            str(row["artifact_member_set_digest"])
            if "artifact_member_set_digest" in row.keys()
            and row["artifact_member_set_digest"] is not None
            else None
        )
        frozen_read_model_artifact_id = (
            str(row["frozen_read_model_artifact_id"])
            if "frozen_read_model_artifact_id" in row.keys()
            and row["frozen_read_model_artifact_id"] is not None
            else None
        )
        frozen_read_model_sha256 = (
            str(row["frozen_read_model_sha256"])
            if "frozen_read_model_sha256" in row.keys()
            and row["frozen_read_model_sha256"] is not None
            else None
        )
        has_v4_closure = bool(
            r6_output_set_digest or artifact_member_ids or artifact_member_set_digest
        )
        if state == PUBLICATION_STATE_AVAILABLE and has_v4_closure:
            if (
                len(artifact_member_ids) != 4
                or r6_output_set_digest is None
                or len(r6_output_set_digest) != 64
                or artifact_member_set_digest
                != content_digest(list(artifact_member_ids))
            ):
                raise LaunchRegistryError("store_closed")

        return ResultPublication(
            sequence=int(row["sequence"]),
            project_id=project,
            run_id=run_id,
            public_run_token=public_token,
            result_context_token=result_context_token,
            idempotency_key=key,
            publication_revision=revision,
            publication_fingerprint=fingerprint,
            mode=mode,
            execution_basis=basis,
            snapshot_token=snapshot_token,
            snapshot_ref=(
                str(row["snapshot_ref"]) if row["snapshot_ref"] is not None else None
            ),
            source_revision_id=(
                str(row["source_revision_id"])
                if row["source_revision_id"] is not None
                else None
            ),
            data_cutoff=data_cutoff,
            setup_manifest_digest=(
                str(row["setup_manifest_digest"])
                if row["setup_manifest_digest"] is not None
                else None
            ),
            manifest_revision=manifest_revision,
            manifest_digest=(
                str(row["manifest_digest"])
                if row["manifest_digest"] is not None
                else None
            ),
            mandatory_denominator=mandatory_denominator,
            site_coverage=site_coverage,
            setup_manifest_identity=setup_identity,
            runtime_manifest_identity=runtime_identity,
            receipt_identities=receipt_identities,
            receipt_set_digest=(
                str(row["receipt_set_digest"])
                if row["receipt_set_digest"] is not None
                else None
            ),
            r5_authority_packet_id=(
                str(row["r5_authority_packet_id"])
                if row["r5_authority_packet_id"] is not None
                else None
            ),
            r5_authority_packet_digest=(
                str(row["r5_authority_packet_digest"])
                if row["r5_authority_packet_digest"] is not None
                else None
            ),
            s4_authority_packet_identities=s4_identities,
            s4_authority_packet_digests=s4_digests,
            r6_output_set_digest=r6_output_set_digest,
            artifact_member_ids=artifact_member_ids,
            artifact_member_set_digest=artifact_member_set_digest,
            frozen_read_model_artifact_id=frozen_read_model_artifact_id,
            frozen_read_model_sha256=frozen_read_model_sha256,
            publication_state=state,
            failure_code=(
                str(row["failure_code"]) if row["failure_code"] is not None else None
            ),
            failure_message=(
                str(row["failure_message"])
                if row["failure_message"] is not None
                else None
            ),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            replayed=bool(replayed),
        )

    def _find_publication_by_run(
        self, project: str, run_id: str
    ) -> Optional[ResultPublication]:
        row = self._require_conn().execute(
            "SELECT * FROM r7_result_publications "
            "WHERE project_id = ? AND run_id = ?",
            (project, run_id),
        ).fetchone()
        return self._row_to_publication(row) if row is not None else None

    def _find_publication_by_key(
        self, project: str, idempotency_key: str
    ) -> Optional[ResultPublication]:
        row = self._require_conn().execute(
            "SELECT * FROM r7_result_publications "
            "WHERE project_id = ? AND idempotency_key = ?",
            (project, idempotency_key),
        ).fetchone()
        return self._row_to_publication(row) if row is not None else None

    def _resolve_publication_run(
        self, project: str, selector: str
    ) -> LaunchRecord:
        value = _required_text(selector, "run_not_found")
        record = self._find_by_selector(project, value)
        if record is None:
            raise LaunchRegistryError("run_not_found")
        return record

    def reserve(
        self,
        project_id: Optional[str] = None,
        *,
        idempotency_key: str,
        mode: str,
        execution_basis: str,
        current_snapshot_token: str,
        baseline_token: Optional[str] = None,
        rule_tokens: Optional[Iterable[str]] = None,
        risk_rule_tokens: Optional[Iterable[str]] = None,
        data_cutoff: str = "",
        comparison_range: Any = "",
        comparison_range_text: Any = None,
        manifest_digest: Optional[str] = None,
        enforce_in_flight: bool = True,
    ) -> LaunchReservation:
        cutoff = _required_text(data_cutoff, "invalid_data_cutoff")
        range_value = comparison_range_text if comparison_range_text is not None else comparison_range
        range_text = _normalize_comparison_range(range_value) if range_value else ""
        digest = _optional_text(manifest_digest, "invalid_manifest_digest")
        project = self._project(project_id)
        request = normalize_request(
            project_id=project,
            idempotency_key=idempotency_key,
            mode=mode,
            execution_basis=execution_basis,
            current_snapshot_token=current_snapshot_token,
            baseline_token=baseline_token,
            rule_tokens=rule_tokens,
            risk_rule_tokens=risk_rule_tokens,
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = self._find_by_key(project, request.idempotency_key)
                if existing is not None:
                    connection.commit()
                    if existing.request_fingerprint == request.request_fingerprint:
                        return LaunchReservation(existing, True)
                    raise IdempotencyConflictError()
                if enforce_in_flight and self._find_in_flight_locked(
                    connection, project
                ) is not None:
                    raise LaunchRegistryError("in_flight_conflict")

                run_id = "r7-run-" + uuid4().hex
                public_token = derive_public_run_token(project, run_id)
                now = self._now()
                connection.execute(
                    """INSERT INTO r7_launch_registry(
                        project_id, idempotency_key, run_id, public_run_token,
                        request_fingerprint, mode, execution_basis,
                        current_snapshot_token, baseline_token, rule_tokens_json,
                        data_cutoff, comparison_range_text, run_state,
                        result_available, main_action, manifest_digest,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        project,
                        request.idempotency_key,
                        run_id,
                        public_token,
                        request.request_fingerprint,
                        request.mode,
                        request.execution_basis,
                        request.current_snapshot_token,
                        request.baseline_token,
                        json.dumps(list(request.rule_tokens), ensure_ascii=False, separators=(",", ":")),
                        cutoff,
                        range_text,
                        STATE_WAITING_START,
                        0,
                        _DEFAULT_MAIN_ACTION,
                        digest,
                        now,
                        now,
                    ),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_launch_registry WHERE project_id = ? AND idempotency_key = ?",
                    (project, request.idempotency_key),
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("store_closed")
                return LaunchReservation(self._row_to_record(row), False)
            except IdempotencyConflictError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except sqlite3.IntegrityError:
                # Another process can win only after SQLite releases the
                # immediate lock.  Re-read its committed row and apply the
                # same fingerprint comparison instead of fabricating a run.
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                existing = self._find_by_key(project, request.idempotency_key)
                if existing is not None and existing.request_fingerprint == request.request_fingerprint:
                    return LaunchReservation(existing, True)
                if existing is not None:
                    raise IdempotencyConflictError()
                raise LaunchRegistryError("store_closed")
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc
