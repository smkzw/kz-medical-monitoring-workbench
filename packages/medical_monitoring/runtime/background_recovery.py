"""R7 Slice-05 synthetic background execution and recovery.

This module owns only run-level control.  The R1 manifest and work-unit ledger
remain the source of progress counts and status.  The worker is deliberately
synthetic/offline: it never calls a provider, model, harness, or real project.

The control row is kept in the same runtime SQLite file as the R1 ledger.  It
contains no denominator or progress fields, and the process-local registry
contains thread handles only.  A lease and generation guard the boundary
between a worker that is still alive and a worker reconstructed after a
process interruption.  The boundary is intentionally at-least-once around
the synthetic action; R1 absorbs exact same-key callbacks and rejects
conflicting callbacks.
"""

from __future__ import annotations

from contextlib import contextmanager

import datetime as _datetime
import json
import math
import sqlite3
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union
from uuid import uuid4

from .maintenance_gate import (
    DEFAULT_WAIT_SECONDS,
    MaintenanceGateError,
    ProjectMaintenanceGate,
)
from .run_entry import RunEntryError
from . import progress as _audience
from ..domain.execution import (
    DEPENDENCY_SATISFYING_STATUSES,
    EVENT_CAPABILITY_ATTEMPT_CLAIMED,
    EVENT_CAPABILITY_ATTEMPT_DECLARED,
    EVENT_CAPABILITY_ATTEMPT_INTERRUPTED,
    EVENT_CAPABILITY_ATTEMPT_TERMINAL,
    EVENT_WORK_UNIT_BEGIN,
    EVENT_WORK_UNIT_ATTEMPT_BOUND,
    TERMINAL_NODE_STATUSES,
    CoverageUnit,
    ExecutionManifest,
    IdempotencyConflictError,
    ManifestWorkUnit,
    NodeType,
    NodeStatus,
    StaleCallbackError,
    StoreError,
    from_jsonable,
)
from .capability import InvocationVersions
from .controller import CapabilityWorkUnitController
from ..graph.store import Store


RUNTIME_DB_NAME = "monitoring_runtime.sqlite3"
ARTIFACT_DIR_NAME = "artifacts"
CONTROL_TABLE_NAME = "r7_execution_control"
CONTROL_TABLE = CONTROL_TABLE_NAME
LEASE_SECONDS = 15.0
HEARTBEAT_SECONDS = 5.0
MAX_CAPABILITY_ATTEMPTS = 2
RETRYABLE_CAPABILITY_ATTEMPT_STATUSES = frozenset(
    ("timeout", "partial", "truncated", "interrupted")
)

# Slice-07A: stable machine-readable run state for the product progress view.
# The frontend polls and branches on these values only; the Chinese overlay
# text stays purely presentational and is never parsed for state.
RUN_STATE_VALUES = (
    "waiting_start",
    "running",
    "stopping",
    "interrupted_resumable",
    "completed",
    "ended_incomplete",
    "failed",
)


class ExecutionControlState(str, Enum):
    PREPARED = "prepared"
    RUNNING = "running"
    CANCELLING = "cancelling"
    INTERRUPTED = "interrupted"
    FINISHED = "finished"


ControlState = ExecutionControlState
ExecutionState = ExecutionControlState
CONTROL_STATES = tuple(ExecutionControlState)


@dataclass(frozen=True)
class ExecutionControl:
    """Internal durable control row; never use this as a product response."""

    run_id: str
    manifest_revision: int
    generation: int
    state: ExecutionControlState
    owner_token: str
    lease_expires_at: Optional[float]
    cancel_requested: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ExecutionClaim:
    """Internal lease capability held by one worker thread."""

    run_id: str
    manifest_revision: int
    generation: int
    owner_token: str
    lease_expires_at: float


@dataclass(frozen=True)
class BackgroundOutcome:
    """One deterministic terminal result for a synthetic work unit."""

    status: NodeStatus
    detail: str


class ExecutionControlError(RunEntryError):
    """Stable Chinese error boundary for R7 control operations."""


BackgroundRecoveryError = ExecutionControlError

_ERROR_MESSAGES = {
    "run_binding_not_found": "未找到指定的监查运行绑定。",
    "execution_not_prepared": "请先准备本次监查工作范围。",
    "already_finished": "本次监查已结束，无需再次开始。",
    "already_running": "本次监查正在执行。",
    "not_interrupted": "本次监查当前不可继续。",
    "nothing_to_resume": "本次监查没有可继续的工作。",
    "not_running": "本次监查当前未在执行。",
    "prepare_while_running": "本次监查正在执行，不能变更工作范围。",
    "runtime_integrity_failed": "本次监查进度无法核对，已阻断。",
    "invalid_work_units": "本次监查工作范围无效，请检查工作项定义。",
    "worker_start_failed": "本次监查后台执行未能启动。",
    "project_busy_retry_later": "项目正在处理数据，请稍后重试",
}

_CONTROL_COLUMNS = (
    "run_id",
    "manifest_revision",
    "generation",
    "state",
    "owner_token",
    "lease_expires_at",
    "cancel_requested",
    "created_at",
    "updated_at",
)
_CONTROL_COLUMN_SET = frozenset(_CONTROL_COLUMNS)
_ACTIVE_STATES = frozenset(
    (ExecutionControlState.RUNNING, ExecutionControlState.CANCELLING)
)
_SATISFYING_VALUES = frozenset(status.value for status in DEPENDENCY_SATISFYING_STATUSES)
_TERMINAL_VALUES = frozenset(status.value for status in TERMINAL_NODE_STATUSES)
_AI_RETRYABLE_UNIT_VALUES = frozenset(
    (NodeStatus.FAILED.value, NodeStatus.BLOCKED.value, NodeStatus.RUNNING.value)
)

_CONTROL_DDL = f"""
CREATE TABLE IF NOT EXISTS {CONTROL_TABLE_NAME} (
    run_id TEXT PRIMARY KEY NOT NULL REFERENCES monitoring_runs(run_id),
    manifest_revision INTEGER NOT NULL,
    generation INTEGER NOT NULL,
    state TEXT NOT NULL,
    owner_token TEXT NOT NULL DEFAULT '',
    lease_expires_at REAL,
    cancel_requested INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _error(code: str) -> ExecutionControlError:
    return ExecutionControlError(code, _ERROR_MESSAGES.get(code, "本次监查操作未能完成。"))


def _now_text(value: float) -> str:
    return _datetime.datetime.fromtimestamp(
        float(value), _datetime.timezone.utc
    ).isoformat()


def _validate_options(lease_seconds: float, heartbeat_seconds: float, step_seconds: float,
                      sweep_seconds: float) -> None:
    for value in (lease_seconds, heartbeat_seconds, step_seconds, sweep_seconds):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise _error("runtime_integrity_failed")
        if not math.isfinite(float(value)) or float(value) < 0:
            raise _error("runtime_integrity_failed")
    if float(lease_seconds) <= 0 or float(heartbeat_seconds) <= 0:
        raise _error("runtime_integrity_failed")


def _connect(db_path: Union[str, Path]) -> sqlite3.Connection:
    if not Path(db_path).is_file():
        raise _error("execution_not_prepared")
    try:
        connection = sqlite3.connect(
            str(db_path), timeout=10.0, isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection
    except (OSError, sqlite3.Error) as exc:
        raise _error("runtime_integrity_failed") from exc


def _ensure_control_schema(connection: sqlite3.Connection) -> None:
    try:
        # ``executescript`` commits an open transaction on CPython.  A
        # control claim/recovery must remain one BEGIN IMMEDIATE transaction,
        # so the single CREATE statement is executed directly.
        connection.execute(_CONTROL_DDL)
        columns = tuple(
            row[1] for row in connection.execute(
                f"PRAGMA table_info({CONTROL_TABLE_NAME})"
            ).fetchall()
        )
    except sqlite3.Error as exc:
        raise _error("runtime_integrity_failed") from exc
    if frozenset(columns) != _CONTROL_COLUMN_SET or len(columns) != len(_CONTROL_COLUMNS):
        raise _error("runtime_integrity_failed")


def _require_control_schema(connection: sqlite3.Connection) -> None:
    """Validate an existing control table without creating or migrating it."""
    try:
        columns = tuple(
            row[1] for row in connection.execute(
                f"PRAGMA table_info({CONTROL_TABLE_NAME})"
            ).fetchall()
        )
    except sqlite3.Error as exc:
        raise _error("runtime_integrity_failed") from exc
    if not columns:
        raise _error("execution_not_prepared")
    if frozenset(columns) != _CONTROL_COLUMN_SET or len(columns) != len(_CONTROL_COLUMNS):
        raise _error("runtime_integrity_failed")


def _raw_control(connection: sqlite3.Connection, run_id: str) -> Optional[sqlite3.Row]:
    try:
        return connection.execute(
            f"SELECT {', '.join(_CONTROL_COLUMNS)} FROM {CONTROL_TABLE_NAME}"
            " WHERE run_id=?",
            (run_id,),
        ).fetchone()
    except sqlite3.Error as exc:
        raise _error("runtime_integrity_failed") from exc


def _control_from_row(row: sqlite3.Row) -> ExecutionControl:
    # R1 ``Store`` intentionally uses tuple rows, while this module's direct
    # connections use ``sqlite3.Row``.  Normalize both shapes without
    # changing the caller-owned Store connection configuration.
    if hasattr(row, "keys"):
        values = {key: row[key] for key in row.keys()}
    else:
        try:
            values = dict(zip(_CONTROL_COLUMNS, row))
        except TypeError as exc:
            raise _error("runtime_integrity_failed") from exc
    if frozenset(values) != _CONTROL_COLUMN_SET:
        raise _error("runtime_integrity_failed")
    try:
        run_id = values["run_id"]
        revision = values["manifest_revision"]
        generation = values["generation"]
        state = ExecutionControlState(values["state"])
        owner = values["owner_token"]
        lease = values["lease_expires_at"]
        cancel = values["cancel_requested"]
        created = values["created_at"]
        updated = values["updated_at"]
    except (KeyError, ValueError, TypeError) as exc:
        raise _error("runtime_integrity_failed") from exc
    if (
        not isinstance(run_id, str) or not run_id.strip()
        or isinstance(revision, bool) or not isinstance(revision, int) or revision <= 0
        or isinstance(generation, bool) or not isinstance(generation, int) or generation < 0
        or not isinstance(owner, str)
        or isinstance(cancel, bool) or cancel not in (0, 1)
        or not isinstance(created, str) or not created
        or not isinstance(updated, str) or not updated
    ):
        raise _error("runtime_integrity_failed")
    if lease is not None:
        try:
            lease = float(lease)
        except (TypeError, ValueError) as exc:
            raise _error("runtime_integrity_failed") from exc
        if not math.isfinite(lease) or lease <= 0:
            raise _error("runtime_integrity_failed")
    if state in _ACTIVE_STATES:
        if not owner or lease is None:
            raise _error("runtime_integrity_failed")
        if state is ExecutionControlState.RUNNING and cancel != 0:
            raise _error("runtime_integrity_failed")
        if state is ExecutionControlState.CANCELLING and cancel != 1:
            raise _error("runtime_integrity_failed")
    elif owner or lease is not None or cancel != 0:
        raise _error("runtime_integrity_failed")
    return ExecutionControl(
        run_id=run_id,
        manifest_revision=revision,
        generation=generation,
        state=state,
        owner_token=owner,
        lease_expires_at=lease,
        cancel_requested=bool(cancel),
        created_at=created,
        updated_at=updated,
    )


def _checked_control(
    connection: sqlite3.Connection, run_id: str, *, require_current: bool = True,
) -> ExecutionControl:
    row = _raw_control(connection, run_id)
    if row is None:
        raise _error("runtime_integrity_failed")
    control = _control_from_row(row)
    try:
        run = connection.execute(
            "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        manifest = connection.execute(
            "SELECT 1 FROM run_manifests WHERE run_id=? AND revision=?",
            (run_id, control.manifest_revision),
        ).fetchone()
    except sqlite3.Error as exc:
        raise _error("runtime_integrity_failed") from exc
    if run is None or manifest is None:
        raise _error("runtime_integrity_failed")
    if require_current and int(run[0]) != control.manifest_revision:
        raise _error("runtime_integrity_failed")
    return control


def _manifest_from_connection(
    connection: sqlite3.Connection, run_id: str, revision: int,
) -> ExecutionManifest:
    try:
        row = connection.execute(
            "SELECT manifest_json FROM run_manifests WHERE run_id=? AND revision=?",
            (run_id, revision),
        ).fetchone()
    except sqlite3.Error as exc:
        raise _error("runtime_integrity_failed") from exc
    if row is None:
        raise _error("runtime_integrity_failed")
    try:
        manifest = from_jsonable(ExecutionManifest, json.loads(row[0]))
    except Exception as exc:
        raise _error("runtime_integrity_failed") from exc
    manifest.revision = revision
    if manifest.run_id != run_id or not manifest.work_units:
        raise _error("runtime_integrity_failed")
    try:
        # Re-run the accepted R1 manifest validator before a control claim;
        # raw SQLite tampering must not turn a malformed dependency graph into
        # a background scheduling decision.
        Store._validate_manifest_work_units(manifest)
    except Exception as exc:
        raise _error("runtime_integrity_failed") from exc
    return manifest


def _unit_statuses(
    connection: sqlite3.Connection, run_id: str, revision: int,
) -> dict[str, str]:
    try:
        rows = connection.execute(
            "SELECT work_unit_id, status FROM work_unit_runs"
            " WHERE run_id=? AND manifest_revision=?",
            (run_id, revision),
        ).fetchall()
    except sqlite3.Error as exc:
        raise _error("runtime_integrity_failed") from exc
    statuses: dict[str, str] = {}
    for row in rows:
        if row[0] in statuses or not isinstance(row[0], str):
            raise _error("runtime_integrity_failed")
        try:
            NodeStatus(row[1])
        except (TypeError, ValueError) as exc:
            raise _error("runtime_integrity_failed") from exc
        statuses[row[0]] = row[1]
    return statuses


def _runnable_units(
    manifest: ExecutionManifest,
    statuses: Mapping[str, str],
    *,
    continuable_ids: Optional[set[str]] = None,
) -> list[ManifestWorkUnit]:
    expected_ids = {unit.work_unit_id for unit in manifest.work_units}
    if set(statuses) != expected_ids:
        raise _error("runtime_integrity_failed")
    continuable_ids = continuable_ids or set()
    node_types = {node.node_id: node.node_type for node in manifest.nodes}
    runnable = []
    for unit in sorted(manifest.work_units, key=lambda item: item.ordinal):
        status = statuses[unit.work_unit_id]
        normal = status in {NodeStatus.PENDING.value, NodeStatus.RUNNING.value}
        continuation = (
            node_types.get(unit.node_id) is NodeType.AI_CANDIDATE
            and unit.work_unit_id in continuable_ids
            and status in _AI_RETRYABLE_UNIT_VALUES
        )
        if not normal and not continuation:
            continue
        if all(statuses.get(dep) in _SATISFYING_VALUES for dep in unit.depends_on):
            runnable.append(unit)
    return runnable


def _ai_unit_ids(manifest: ExecutionManifest) -> set[str]:
    node_types = {node.node_id: node.node_type for node in manifest.nodes}
    return {
        unit.work_unit_id
        for unit in manifest.work_units
        if node_types.get(unit.node_id) is NodeType.AI_CANDIDATE
    }


def _attempt_lifecycle_from_connection(
    connection: sqlite3.Connection, run_id: str,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Read only public audit evidence, never the R1 private attempt tables."""
    try:
        rows = connection.execute(
            "SELECT event_type, payload_json FROM audit_events"
            " WHERE run_id=? ORDER BY seq",
            (run_id,),
        ).fetchall()
    except sqlite3.Error as exc:
        raise _error("runtime_integrity_failed") from exc
    statuses: dict[str, str] = {}
    bindings: list[dict[str, Any]] = []
    lifecycle_types = {
        EVENT_CAPABILITY_ATTEMPT_DECLARED,
        EVENT_CAPABILITY_ATTEMPT_CLAIMED,
        EVENT_CAPABILITY_ATTEMPT_INTERRUPTED,
        EVENT_CAPABILITY_ATTEMPT_TERMINAL,
    }
    for event_type, payload_json in rows:
        try:
            payload = json.loads(payload_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise _error("runtime_integrity_failed") from exc
        if not isinstance(payload, Mapping):
            raise _error("runtime_integrity_failed")
        if event_type in lifecycle_types:
            attempt_id = payload.get("attempt_id")
            if not isinstance(attempt_id, str) or not attempt_id:
                raise _error("runtime_integrity_failed")
            if event_type == EVENT_CAPABILITY_ATTEMPT_DECLARED:
                statuses[attempt_id] = "declared"
            elif event_type == EVENT_CAPABILITY_ATTEMPT_CLAIMED:
                statuses[attempt_id] = "running"
            elif event_type == EVENT_CAPABILITY_ATTEMPT_INTERRUPTED:
                statuses[attempt_id] = "interrupted"
            else:
                status = payload.get("status")
                if not isinstance(status, str) or not status:
                    raise _error("runtime_integrity_failed")
                statuses[attempt_id] = status
        elif event_type in {EVENT_WORK_UNIT_BEGIN, EVENT_WORK_UNIT_ATTEMPT_BOUND}:
            if payload.get("run_id") != run_id:
                continue
            identity = payload.get("execution_identity")
            attempt_id = payload.get("attempt_id")
            if isinstance(identity, Mapping):
                attempt_id = identity.get("attempt_id")
            if event_type == EVENT_WORK_UNIT_BEGIN and not attempt_id:
                # Ordinary deterministic work-unit starts carry an empty
                # execution identity; only AI starts are attempt bindings.
                continue
            work_unit_id = payload.get("work_unit_id")
            ordinal = payload.get("attempt_ordinal")
            revision = payload.get("manifest_revision")
            if event_type == EVENT_WORK_UNIT_BEGIN:
                ordinal = 1
            if (
                not isinstance(attempt_id, str) or not attempt_id
                or not isinstance(work_unit_id, str) or not work_unit_id
                or isinstance(ordinal, bool) or not isinstance(ordinal, int)
                or ordinal < 1
                or isinstance(revision, bool) or not isinstance(revision, int)
                or revision < 1
            ):
                raise _error("runtime_integrity_failed")
            bindings.append(
                {
                    "attempt_id": attempt_id,
                    "work_unit_id": work_unit_id,
                    "attempt_ordinal": ordinal,
                    "manifest_revision": revision,
                }
            )
    return statuses, bindings


def _continuable_ids_from_connection(
    connection: sqlite3.Connection, run_id: str, revision: int,
) -> set[str]:
    statuses, bindings = _attempt_lifecycle_from_connection(connection, run_id)
    latest: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        if binding["manifest_revision"] != revision:
            continue
        old = latest.get(binding["work_unit_id"])
        if old is not None and binding["attempt_ordinal"] <= old["attempt_ordinal"]:
            raise _error("runtime_integrity_failed")
        latest[binding["work_unit_id"]] = binding
    return {
        work_unit_id
        for work_unit_id, binding in latest.items()
        if binding["attempt_ordinal"] < MAX_CAPABILITY_ATTEMPTS
        and statuses.get(binding["attempt_id"]) in RETRYABLE_CAPABILITY_ATTEMPT_STATUSES
    }


def _bound_capability_attempts(
    store: Store, run_id: str, revision: int, work_unit_id: str,
) -> list[dict[str, Any]]:
    """Return R1 binding history through its public append-only audit seam."""
    statuses, bindings = _attempt_lifecycle_from_store(store, run_id)
    selected = [
        binding for binding in bindings
        if binding["manifest_revision"] == revision
        and binding["work_unit_id"] == work_unit_id
    ]
    selected.sort(key=lambda item: item["attempt_ordinal"])
    if [item["attempt_ordinal"] for item in selected] != list(
        range(1, len(selected) + 1)
    ):
        raise StoreError("capability binding ordinals are not contiguous")
    for binding in selected:
        attempt = store.get_capability_attempt(binding["attempt_id"])
        if attempt is None or attempt.get("status") != statuses.get(binding["attempt_id"]):
            # The public Store getter is authoritative; audit evidence is only
            # used to enumerate the append-only binding sequence.
            if attempt is None:
                raise StoreError("bound capability attempt is missing")
        binding["status"] = str(attempt.get("status", ""))
        binding["attempt"] = attempt
    return selected

def list_bound_capability_attempts(
    store: Store,
    run_id: str,
    manifest_revision: int,
    work_unit_id: str,
) -> list[dict[str, Any]]:
    """Read one work-unit's final-attempt history through public Store APIs.

    This is the single read seam used by publication gates.  It delegates to
    the existing audit/journal reconciliation helper and never opens the R1
    private capability mutation facade.
    """

    return _bound_capability_attempts(
        store, run_id, manifest_revision, work_unit_id
    )


def _attempt_lifecycle_from_store(
    store: Store, run_id: str,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    # ``audit_trail`` is an R1 public evidence API.  Keep the parser shared
    # with the connection-only resume gate without reading private tables.
    try:
        rows = store.audit_trail()
    except Exception as exc:
        raise _error("runtime_integrity_failed") from exc
    statuses: dict[str, str] = {}
    bindings: list[dict[str, Any]] = []
    for event in rows:
        if event.run_id != run_id:
            continue
        payload = event.payload
        if not isinstance(payload, Mapping):
            raise _error("runtime_integrity_failed")
        if event.event_type == EVENT_CAPABILITY_ATTEMPT_DECLARED:
            attempt_id = payload.get("attempt_id")
            if not isinstance(attempt_id, str) or not attempt_id:
                raise _error("runtime_integrity_failed")
            statuses[attempt_id] = "declared"
        elif event.event_type == EVENT_CAPABILITY_ATTEMPT_CLAIMED:
            attempt_id = payload.get("attempt_id")
            if not isinstance(attempt_id, str) or not attempt_id:
                raise _error("runtime_integrity_failed")
            statuses[attempt_id] = "running"
        elif event.event_type == EVENT_CAPABILITY_ATTEMPT_INTERRUPTED:
            attempt_id = payload.get("attempt_id")
            if not isinstance(attempt_id, str) or not attempt_id:
                raise _error("runtime_integrity_failed")
            statuses[attempt_id] = "interrupted"
        elif event.event_type == EVENT_CAPABILITY_ATTEMPT_TERMINAL:
            attempt_id = payload.get("attempt_id")
            status = payload.get("status")
            if not isinstance(attempt_id, str) or not attempt_id \
                    or not isinstance(status, str) or not status:
                raise _error("runtime_integrity_failed")
            statuses[attempt_id] = status
        elif event.event_type in {EVENT_WORK_UNIT_BEGIN, EVENT_WORK_UNIT_ATTEMPT_BOUND}:
            if payload.get("run_id") != run_id:
                continue
            identity = payload.get("execution_identity")
            attempt_id = payload.get("attempt_id")
            if isinstance(identity, Mapping):
                attempt_id = identity.get("attempt_id")
            if event.event_type == EVENT_WORK_UNIT_BEGIN and not attempt_id:
                # Ordinary deterministic work-unit starts carry an empty
                # execution identity; only AI starts are attempt bindings.
                continue
            work_unit_id = payload.get("work_unit_id")
            ordinal = payload.get("attempt_ordinal")
            revision = payload.get("manifest_revision")
            if event.event_type == EVENT_WORK_UNIT_BEGIN:
                ordinal = 1
            if (
                not isinstance(attempt_id, str) or not attempt_id
                or not isinstance(work_unit_id, str) or not work_unit_id
                or isinstance(ordinal, bool) or not isinstance(ordinal, int)
                or ordinal < 1
                or isinstance(revision, bool) or not isinstance(revision, int)
                or revision < 1
            ):
                raise _error("runtime_integrity_failed")
            bindings.append(
                {
                    "attempt_id": attempt_id,
                    "work_unit_id": work_unit_id,
                    "attempt_ordinal": ordinal,
                    "manifest_revision": revision,
                }
            )
    return statuses, bindings


def continuable_ai_unit(
    store: Store,
    run_id: str,
    manifest_revision: int,
    work_unit_id: Union[str, ManifestWorkUnit],
) -> bool:
    """Return whether one AI unit may receive its single linked retry."""
    manifest = store.get_manifest(run_id, manifest_revision)
    if manifest is None:
        return False
    unit_id = (
        work_unit_id.work_unit_id
        if isinstance(work_unit_id, ManifestWorkUnit) else str(work_unit_id)
    )
    unit = next(
        (item for item in manifest.work_units if item.work_unit_id == unit_id), None
    )
    if unit is None or unit_id not in _ai_unit_ids(manifest):
        return False
    history = _bound_capability_attempts(store, run_id, manifest_revision, unit_id)
    if not history:
        return False
    latest = history[-1]
    return (
        latest["attempt_ordinal"] < MAX_CAPABILITY_ATTEMPTS
        and latest.get("status") in RETRYABLE_CAPABILITY_ATTEMPT_STATUSES
    )


def _continuable_ai_units(
    store: Store, run_id: str, revision: int, manifest: ExecutionManifest,
) -> set[str]:
    return {
        unit.work_unit_id
        for unit in manifest.work_units
        if continuable_ai_unit(store, run_id, revision, unit.work_unit_id)
    }


def _has_runnable(
    connection: sqlite3.Connection, run_id: str, revision: int,
) -> bool:
    manifest = _manifest_from_connection(connection, run_id, revision)
    return bool(
        _runnable_units(
            manifest,
            _unit_statuses(connection, run_id, revision),
            continuable_ids=_continuable_ids_from_connection(connection, run_id, revision),
        )
    )


def _validate_r1_store(store: Store, run_id: str, expected_project_id: str = "") -> None:
    """Validate audit, ledger and artifact integrity without recovery writes."""
    try:
        run = store.get_run(run_id)
        if expected_project_id and run.project_id != expected_project_id:
            raise _error("run_binding_not_found")
        if not store.get_project(run.project_id).is_synthetic:
            raise _error("runtime_integrity_failed")
        if int(run.manifest_revision) <= 0:
            raise _error("execution_not_prepared")
        manifest = store.get_manifest(run_id, run.manifest_revision)
        if manifest is None or not manifest.work_units:
            raise _error("execution_not_prepared")
        audit_ok, _, _ = store.verify_audit_chain()
        if not audit_ok:
            raise _error("runtime_integrity_failed")
        # structured_progress performs the authoritative ledger/audit join.  A
        # deferred transaction keeps this validation from observing a partial
        # work-unit commit.
        store._conn.execute("BEGIN")
        try:
            store.structured_progress(run_id, feed_limit=20)
        finally:
            store._conn.execute("ROLLBACK")
        for artifact in store.list_artifacts(run_id):
            if not store.verify_artifact(artifact.artifact_id):
                raise _error("runtime_integrity_failed")
        for snapshot_id, content_hash in store._conn.execute(
            "SELECT snapshot_id, content_hash FROM listing_snapshots"
        ).fetchall():
            path = store._content_path(content_hash)
            if not path.is_file():
                raise _error("runtime_integrity_failed")
            import hashlib

            if hashlib.sha256(path.read_bytes()).hexdigest() != content_hash:
                raise _error("runtime_integrity_failed")
        for kind, object_id, version in store._conn.execute(
            "SELECT kind, object_id, version FROM domain_objects"
        ).fetchall():
            try:
                store.get_domain_object(kind, object_id, version=int(version))
            except Exception as exc:
                raise _error("runtime_integrity_failed") from exc
    except ExecutionControlError:
        raise
    except (StoreError, sqlite3.Error, OSError) as exc:
        raise _error("runtime_integrity_failed") from exc
    except Exception as exc:
        raise _error("runtime_integrity_failed") from exc


def _open_store(db_path: Path, artifact_dir: Path) -> Store:
    if not db_path.is_file() or not artifact_dir.is_dir():
        raise _error("execution_not_prepared")
    try:
        return Store(db_path, artifact_dir)
    except Exception as exc:
        raise _error("runtime_integrity_failed") from exc


def _public_overlay(
    control: ExecutionControl,
    view: Mapping[str, Any],
    *,
    harness: bool = False,
    has_continuable_ai: bool = False,
    has_runnable_work: bool = False,
    retry_exhausted: bool = False,
) -> dict[str, Any]:
    if control.state is ExecutionControlState.PREPARED:
        text, actions, run_state = "等待开始医学监查", ["开始"], "waiting_start"
    elif control.state is ExecutionControlState.RUNNING:
        if harness:
            current_work = view.get("current_work")
            label = (
                current_work[0].get("label")
                if isinstance(current_work, list) and current_work
                and isinstance(current_work[0], Mapping)
                else ""
            )
            if isinstance(label, str) and label.strip():
                detail = label.strip().rstrip("。")
                # The 正在分析： prefix already carries the ongoing aspect;
                # drop a duplicated leading 正在 from the work label so the
                # audience text never reads 正在分析：正在…。
                if detail.startswith("正在"):
                    detail = detail[2:].lstrip("：:，, ").rstrip("。")
                text = f"正在分析：{detail}。" if detail else "正在分析"
            else:
                text = "正在分析"
            actions = ["停止"]
        else:
            text, actions = "医学监查进行中", ["停止"]
        run_state = "running"
    elif control.state is ExecutionControlState.CANCELLING:
        text, actions = (
            ("正在停止，当前分析可能完成；系统不会开始下一项工作。", [])
            if harness else ("正在停止医学监查", [])
        )
        run_state = "stopping"
    elif harness and retry_exhausted:
        text = "本项分析未完成，已达到本次重试上限。"
        actions = (
            ["继续"]
            if control.state is ExecutionControlState.INTERRUPTED
            and (has_continuable_ai or has_runnable_work)
            else []
        )
        # Exhausted retries remain continuable only while the server still
        # offers the 继续 action; without it the run is a stable failure.
        run_state = "interrupted_resumable" if actions else "failed"
    elif control.state is ExecutionControlState.INTERRUPTED \
            and harness and has_continuable_ai:
        text, actions, run_state = (
            "分析已中断，可继续本次监查。",
            ["继续"],
            "interrupted_resumable",
        )
    elif harness and view.get("headline") == "本次监查已结束，部分工作未完成":
        text, actions, run_state = "分析服务连接异常，本项分析未完成。", [], "failed"
    elif view.get("total") and view.get("completed") == view.get("total"):
        text, actions, run_state = "本次监查已完成", [], "completed"
    elif control.state is ExecutionControlState.INTERRUPTED:
        text, actions, run_state = "已停止，可继续", ["继续"], "interrupted_resumable"
    else:
        text, actions, run_state = "本次监查已结束，部分工作未完成", [], "ended_incomplete"
    if run_state not in RUN_STATE_VALUES:
        raise _error("runtime_integrity_failed")
    return {
        "run_status_text": text,
        "available_actions": actions,
        "run_state": run_state,
    }


def _read_snapshot_from_store(
    store: Store, run_id: str, *, feed_limit: int = 20,
) -> dict[str, Any]:
    connection = store._conn
    try:
        connection.execute("BEGIN")
        try:
            view = _audience.project_audience_progress(
                store, run_id, feed_limit=feed_limit,
            )
            control = _checked_control(connection, run_id)
            manifest = store.get_manifest(run_id, control.manifest_revision)
            if manifest is None:
                raise _error("runtime_integrity_failed")
            ai_ids = _ai_unit_ids(manifest)
            continuable = _continuable_ai_units(
                store, run_id, control.manifest_revision, manifest
            )
            statuses = {
                row.work_unit_id: row.status.value
                for row in store.list_work_unit_runs(
                    run_id, control.manifest_revision,
                )
            }
            has_runnable_work = bool(
                _runnable_units(
                    manifest,
                    statuses,
                    continuable_ids=continuable,
                )
            )
            retry_exhausted = False
            if ai_ids:
                try:
                    history = _attempt_lifecycle_from_store(store, run_id)[1]
                    for unit_id in ai_ids:
                        unit_history = sorted(
                            (
                                item for item in history
                                if item["manifest_revision"] == control.manifest_revision
                                and item["work_unit_id"] == unit_id
                            ),
                            key=lambda item: item["attempt_ordinal"],
                        )
                        if unit_history:
                            latest = store.get_capability_attempt(
                                unit_history[-1]["attempt_id"]
                            )
                            if latest is not None and (
                                unit_history[-1]["attempt_ordinal"]
                                >= MAX_CAPABILITY_ATTEMPTS
                                and latest.get("status")
                                in RETRYABLE_CAPABILITY_ATTEMPT_STATUSES
                            ):
                                retry_exhausted = True
                                break
                except StoreError:
                    raise
            return {
                **view,
                **_public_overlay(
                    control,
                    view,
                    harness=bool(ai_ids),
                    has_continuable_ai=bool(continuable),
                    has_runnable_work=has_runnable_work,
                    retry_exhausted=retry_exhausted,
                ),
            }
        finally:
            connection.execute("ROLLBACK")
    except ExecutionControlError:
        raise
    except Exception as exc:
        raise _error("runtime_integrity_failed") from exc


def _recover_expired_control(
    db_path: Path, run_id: str, now: float,
) -> Optional[ExecutionControl]:
    connection = _connect(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        try:
            _require_control_schema(connection)
            row = _raw_control(connection, run_id)
            if row is None:
                connection.execute("ROLLBACK")
                return None
            control = _control_from_row(row)
            if (
                control.state in _ACTIVE_STATES
                and control.lease_expires_at is not None
                and control.lease_expires_at <= now
            ):
                updated = _now_text(now)
                connection.execute(
                    f"UPDATE {CONTROL_TABLE_NAME} SET generation=?, state=?,"
                    " owner_token='', lease_expires_at=NULL, cancel_requested=0,"
                    " updated_at=? WHERE run_id=? AND manifest_revision=?"
                    " AND generation=? AND owner_token=?",
                    (
                        control.generation + 1,
                        ExecutionControlState.INTERRUPTED.value,
                        updated,
                        run_id,
                        control.manifest_revision,
                        control.generation,
                        control.owner_token,
                    ),
                )
                if connection.execute("SELECT changes()").fetchone()[0] != 1:
                    raise _error("runtime_integrity_failed")
                control = _checked_control(connection, run_id, require_current=False)
            connection.execute("COMMIT")
            return control
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
    finally:
        connection.close()


def ensure_execution_control(
    db_path: Union[str, Path], run_id: str, manifest_revision: int,
    *, now: Optional[float] = None,
) -> ExecutionControl:
    """Create or reconcile the one control row for a prepared revision."""
    if isinstance(manifest_revision, bool) or not isinstance(manifest_revision, int) \
            or manifest_revision <= 0:
        raise _error("runtime_integrity_failed")
    connection = _connect(db_path)
    current_time = time.time() if now is None else float(now)
    try:
        connection.execute("BEGIN IMMEDIATE")
        try:
            _ensure_control_schema(connection)
            run = connection.execute(
                "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            manifest = connection.execute(
                "SELECT 1 FROM run_manifests WHERE run_id=? AND revision=?",
                (run_id, manifest_revision),
            ).fetchone()
            if run is None or int(run[0]) != manifest_revision or manifest is None:
                raise _error("runtime_integrity_failed")
            row = _raw_control(connection, run_id)
            if row is None:
                stamp = _now_text(current_time)
                connection.execute(
                    f"INSERT INTO {CONTROL_TABLE_NAME}({', '.join(_CONTROL_COLUMNS)})"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        run_id, manifest_revision, 0,
                        ExecutionControlState.PREPARED.value, "", None, 0,
                        stamp, stamp,
                    ),
                )
            else:
                old = _control_from_row(row)
                if old.manifest_revision != manifest_revision:
                    if old.manifest_revision > manifest_revision:
                        raise _error("runtime_integrity_failed")
                    if old.state in _ACTIVE_STATES:
                        raise _error("prepare_while_running")
                    stamp = _now_text(current_time)
                    connection.execute(
                        f"UPDATE {CONTROL_TABLE_NAME} SET manifest_revision=?,"
                        " generation=?, state=?, owner_token='', lease_expires_at=NULL,"
                        " cancel_requested=0, updated_at=? WHERE run_id=?"
                        " AND manifest_revision=? AND generation=?",
                        (
                            manifest_revision,
                            old.generation + 1,
                            ExecutionControlState.PREPARED.value,
                            stamp,
                            run_id,
                            old.manifest_revision,
                            old.generation,
                        ),
                    )
                    if connection.execute("SELECT changes()").fetchone()[0] != 1:
                        raise _error("runtime_integrity_failed")
            control = _checked_control(connection, run_id)
            connection.execute("COMMIT")
            return control
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
    except ExecutionControlError:
        raise
    except (sqlite3.Error, OSError, ValueError) as exc:
        raise _error("runtime_integrity_failed") from exc
    finally:
        connection.close()


def assert_prepare_scope_change_allowed(
    db_path: Union[str, Path], run_id: str, current_revision: int,
) -> None:
    """Reject a different manifest revision while a run still owns a lease."""
    connection = _connect(db_path)
    current_time = time.time()
    try:
        connection.execute("BEGIN IMMEDIATE")
        try:
            _ensure_control_schema(connection)
            row = _raw_control(connection, run_id)
            if row is None:
                connection.execute("ROLLBACK")
                return
            control = _control_from_row(row)
            if control.manifest_revision != current_revision:
                raise _error("runtime_integrity_failed")
            if (
                control.state in _ACTIVE_STATES
                and control.lease_expires_at is not None
                and control.lease_expires_at <= current_time
            ):
                cursor = connection.execute(
                    f"UPDATE {CONTROL_TABLE_NAME} SET generation=?, state=?,"
                    " owner_token='', lease_expires_at=NULL, cancel_requested=0,"
                    " updated_at=? WHERE run_id=? AND manifest_revision=?"
                    " AND generation=? AND owner_token=?",
                    (
                        control.generation + 1,
                        ExecutionControlState.INTERRUPTED.value,
                        _now_text(current_time), run_id, control.manifest_revision,
                        control.generation, control.owner_token,
                    ),
                )
                if cursor.rowcount != 1:
                    raise _error("runtime_integrity_failed")
                control = _checked_control(connection, run_id)
            if control.state in _ACTIVE_STATES:
                raise _error("prepare_while_running")
            connection.execute("COMMIT")
        except BaseException:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
    finally:
        connection.close()


class BackgroundRecoveryAdapter:
    """Run-level controller and synthetic worker for one canonical workspace."""

    _registry_lock = threading.Lock()
    _registry: dict[tuple[str, str, int], threading.Thread] = {}

    def __init__(
        self,
        workspace_dir: Optional[Union[str, Path]] = None,
        *,
        runtime_dir: Optional[Union[str, Path]] = None,
        db_path: Optional[Union[str, Path]] = None,
        artifact_dir: Optional[Union[str, Path]] = None,
        canonical_project_id: str = "",
        maintenance_root: Optional[Union[str, Path]] = None,
        unit_step: Optional[Callable[[ManifestWorkUnit, str], BackgroundOutcome]] = None,
        clock: Callable[[], float] = time.time,
        lease_seconds: float = LEASE_SECONDS,
        heartbeat_seconds: float = HEARTBEAT_SECONDS,
        step_seconds: float = 0.01,
        sweep_seconds: float = 0.01,
        harness_runtime_factory: Optional[Callable[..., Any]] = None,
        harness_adapter: Any = None,
        harness_catalog: Any = None,
        harness_r1_profile: Any = None,
        harness_profile_factory: Optional[Callable[[str], Any]] = None,
        run_binding_store: Any = None,
    ) -> None:
        _validate_options(lease_seconds, heartbeat_seconds, step_seconds, sweep_seconds)
        if db_path is not None:
            self.db_path = Path(db_path)
            self.artifact_dir = Path(
                artifact_dir if artifact_dir is not None else self.db_path.parent / ARTIFACT_DIR_NAME
            )
        else:
            root = Path(runtime_dir if runtime_dir is not None else workspace_dir or "")
            if not str(root):
                raise _error("runtime_integrity_failed")
            if root.name != "runtime":
                root = root / "runtime"
            self.db_path = root / RUNTIME_DB_NAME
            self.artifact_dir = Path(artifact_dir) if artifact_dir is not None else root / ARTIFACT_DIR_NAME
        self.canonical_project_id = canonical_project_id
        self.unit_step = unit_step or synthetic_outcome
        self.clock = clock
        self.lease_seconds = float(lease_seconds)
        self.heartbeat_seconds = float(heartbeat_seconds)
        self.step_seconds = float(step_seconds)
        self.sweep_seconds = float(sweep_seconds)
        self.harness_runtime_factory = harness_runtime_factory
        self.harness_adapter = harness_adapter
        self.harness_catalog = harness_catalog
        self.harness_r1_profile = harness_r1_profile
        self.harness_profile_factory = harness_profile_factory
        self.run_binding_store = run_binding_store
        self.maintenance_root = (
            Path(maintenance_root)
            if maintenance_root is not None
            else self.db_path.parent.parent.parent
        )

    @contextmanager
    def _shared_project_maintenance(self):
        """Hold the product write gate for the complete worker lifetime."""
        if not self.canonical_project_id:
            yield
            return
        gate = ProjectMaintenanceGate(
            self.maintenance_root,
            self.canonical_project_id,
            wait_seconds=DEFAULT_WAIT_SECONDS,
        )
        try:
            with gate.shared():
                yield
        except MaintenanceGateError as exc:
            raise _error("project_busy_retry_later") from exc

    def _key(self, run_id: str, revision: int) -> tuple[str, str, int]:
        return (str(self.db_path), run_id, revision)

    def _validate(self, run_id: str) -> None:
        store = _open_store(self.db_path, self.artifact_dir)
        try:
            _validate_r1_store(store, run_id, self.canonical_project_id)
        finally:
            store.close()

    def _control(self, run_id: str) -> ExecutionControl:
        connection = _connect(self.db_path)
        try:
            _require_control_schema(connection)
            return _checked_control(connection, run_id)
        finally:
            connection.close()

    def get_control(self, run_id: str) -> ExecutionControl:
        """Read the durable control row for offline tests and diagnostics."""
        return self._control(run_id)

    control = get_control
    read_control = get_control
    get_execution_control = get_control

    def _recover_expired_lease_unlocked(self, run_id: str) -> ExecutionControl:
        """Mark an expired owner interrupted; never start a worker."""
        self._recover_expired_attempts(run_id)
        recovered = _recover_expired_control(self.db_path, run_id, float(self.clock()))
        if recovered is None:
            raise _error("runtime_integrity_failed")
        return self._control(run_id)
    def recover_expired_lease(self, run_id: str) -> ExecutionControl:
        with self._shared_project_maintenance():
            return self._recover_expired_lease_unlocked(run_id)

    recover = recover_expired_lease

    def _recover_expired_attempts(self, run_id: str) -> list[str]:
        """Recover R1 attempt leases without dispatching or reconciling transport."""
        store = _open_store(self.db_path, self.artifact_dir)
        try:
            return list(
                store.recover_expired_capability_attempts(
                    now_epoch=float(self.clock()), run_id=run_id
                )
            )
        finally:
            store.close()

    def _renew_inflight_lease_unlocked(
        self,
        run_id: str,
        manifest_revision: int,
        generation: int,
        owner_token: str,
        *,
        lease_seconds: Optional[float] = None,
        now_epoch: Optional[float] = None,
    ) -> bool:
        """Renew only the current harness unit's run lease.

        This path intentionally does not call :meth:`heartbeat`; a cancelling
        owner may keep its current transport lease alive but cannot claim more
        work.
        """
        from .harness_runtime import renew_inflight_lease

        return bool(
            renew_inflight_lease(
                self.db_path,
                run_id,
                manifest_revision,
                generation,
                owner_token,
                lease_seconds=(
                    self.lease_seconds if lease_seconds is None else lease_seconds
                ),
                now_epoch=now_epoch,
            )
        )

    def renew_inflight_lease(
        self,
        run_id: str,
        manifest_revision: int,
        generation: int,
        owner_token: str,
        *,
        lease_seconds: Optional[float] = None,
        now_epoch: Optional[float] = None,
    ) -> bool:
        with self._shared_project_maintenance():
            return self._renew_inflight_lease_unlocked(
                run_id,
                manifest_revision,
                generation,
                owner_token,
                lease_seconds=lease_seconds,
                now_epoch=now_epoch,
            )
    def _heartbeat_unlocked(
        self, run_id: str, manifest_revision: int, generation: int,
        owner_token: str, *, now: Optional[float] = None,
    ) -> bool:
        """CAS renew one active owner lease; false means the owner is stale."""
        current_time = float(self.clock() if now is None else now)
        connection = _connect(self.db_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _require_control_schema(connection)
                row = _raw_control(connection, run_id)
                if row is None:
                    connection.execute("ROLLBACK")
                    return False
                control = _control_from_row(row)
                valid = (
                    control.manifest_revision == manifest_revision
                    and control.generation == generation
                    and control.owner_token == owner_token
                    and control.state is ExecutionControlState.RUNNING
                    and not control.cancel_requested
                    and control.lease_expires_at is not None
                    and control.lease_expires_at > current_time
                )
                if not valid:
                    connection.execute("ROLLBACK")
                    return False
                new_expiry = current_time + self.lease_seconds
                stamp = _now_text(current_time)
                cursor = connection.execute(
                    f"UPDATE {CONTROL_TABLE_NAME} SET lease_expires_at=?, updated_at=?"
                    " WHERE run_id=? AND manifest_revision=? AND generation=?"
                    " AND owner_token=? AND state=? AND cancel_requested=0"
                    " AND lease_expires_at>?",
                    (
                        new_expiry, stamp, run_id, manifest_revision, generation,
                        owner_token, ExecutionControlState.RUNNING.value, current_time,
                    ),
                )
                ok = cursor.rowcount == 1
                connection.execute("COMMIT" if ok else "ROLLBACK")
                return ok
            except BaseException:
                try:
                    connection.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
        except ExecutionControlError:
            raise
        except (sqlite3.Error, OSError, ValueError) as exc:
            raise _error("runtime_integrity_failed") from exc
        finally:
            connection.close()
    def heartbeat(
        self, run_id: str, manifest_revision: int, generation: int,
        owner_token: str, *, now: Optional[float] = None,
    ) -> bool:
        with self._shared_project_maintenance():
            return self._heartbeat_unlocked(
                run_id,
                manifest_revision,
                generation,
                owner_token,
                now=now,
            )

    cas_heartbeat = heartbeat

    def _claim(self, run_id: str, action: str) -> tuple[Optional[ExecutionClaim], bool]:
        current_time = float(self.clock())
        connection = _connect(self.db_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _require_control_schema(connection)
                control = _checked_control(connection, run_id)
                if (
                    control.state in _ACTIVE_STATES
                    and control.lease_expires_at is not None
                    and control.lease_expires_at <= current_time
                ):
                    stamp = _now_text(current_time)
                    cursor = connection.execute(
                        f"UPDATE {CONTROL_TABLE_NAME} SET generation=?, state=?,"
                        " owner_token='', lease_expires_at=NULL, cancel_requested=0,"
                        " updated_at=? WHERE run_id=? AND manifest_revision=?"
                        " AND generation=? AND owner_token=?",
                        (
                            control.generation + 1,
                            ExecutionControlState.INTERRUPTED.value,
                            stamp,
                            run_id,
                            control.manifest_revision,
                            control.generation,
                            control.owner_token,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise _error("runtime_integrity_failed")
                    control = _checked_control(connection, run_id)
                if control.state in _ACTIVE_STATES:
                    connection.execute("COMMIT")
                    return None, True
                if action == "start":
                    if control.state is ExecutionControlState.FINISHED:
                        raise _error("already_finished")
                    if control.state is not ExecutionControlState.PREPARED:
                        raise _error("execution_not_prepared")
                elif action == "resume":
                    if control.state is ExecutionControlState.FINISHED \
                            and not _has_runnable(
                                connection, run_id, control.manifest_revision
                            ):
                        raise _error("nothing_to_resume")
                    if control.state is not ExecutionControlState.INTERRUPTED:
                        raise _error("not_interrupted")
                    if not _has_runnable(connection, run_id, control.manifest_revision):
                        raise _error("nothing_to_resume")
                else:  # pragma: no cover - private caller guard
                    raise _error("runtime_integrity_failed")
                owner = uuid4().hex
                generation = control.generation + 1
                expiry = current_time + self.lease_seconds
                stamp = _now_text(current_time)
                cursor = connection.execute(
                    f"UPDATE {CONTROL_TABLE_NAME} SET generation=?, state=?,"
                    " owner_token=?, lease_expires_at=?, cancel_requested=0, updated_at=?"
                    " WHERE run_id=? AND manifest_revision=? AND generation=?"
                    " AND state=? AND owner_token='' AND lease_expires_at IS NULL",
                    (
                        generation, ExecutionControlState.RUNNING.value, owner, expiry,
                        stamp, run_id, control.manifest_revision, control.generation,
                        control.state.value,
                    ),
                )
                if cursor.rowcount != 1:
                    raise _error("already_running")
                connection.execute("COMMIT")
                return ExecutionClaim(
                    run_id=run_id,
                    manifest_revision=control.manifest_revision,
                    generation=generation,
                    owner_token=owner,
                    lease_expires_at=expiry,
                ), False
            except BaseException:
                try:
                    connection.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
        except ExecutionControlError:
            raise
        except (sqlite3.Error, OSError, ValueError) as exc:
            raise _error("runtime_integrity_failed") from exc
        finally:
            connection.close()

    def _spawn(self, claim: ExecutionClaim) -> None:
        key = self._key(claim.run_id, claim.manifest_revision)
        with self._registry_lock:
            # A non-replayed claim always has a new generation.  An old
            # thread may still be unwinding after lease recovery; replacing
            # its handle is required so the new generation is not left
            # running with no worker.  The old thread will fail its CAS check
            # and exit without overwriting the new owner.
            stop_event = threading.Event()
            worker = threading.Thread(
                target=self._worker_main,
                args=(claim, stop_event),
                name="mm-r7-background-worker",
                daemon=True,
            )
            self._registry[key] = worker
        try:
            worker.start()
        except Exception as exc:
            with self._registry_lock:
                if self._registry.get(key) is worker:
                    self._registry.pop(key, None)
            self._release_claim(claim, interrupted=True)
            raise _error("worker_start_failed") from exc

    def _harness_profile(self, run_id: str) -> Any:
        if self.harness_profile_factory is not None:
            profile = self.harness_profile_factory(run_id)
            if profile is not None:
                return profile
        getter = getattr(self.run_binding_store, "get_with_frozen", None)
        if callable(getter):
            _, profile = getter(run_id)
            return profile
        return None

    def _make_harness_runtime(
        self, store: Store, claim: ExecutionClaim, unit: ManifestWorkUnit,
    ) -> Any:
        factory = self.harness_runtime_factory
        if factory is not None:
            # The callback is deliberately a complete-runtime seam.  It may
            # construct a test HarnessCapabilityRuntime with a fake R6 adapter;
            # R7 never discovers or starts a provider itself.
            runtime = factory(store, claim, unit)
            if runtime is None:
                raise StoreError("harness runtime factory returned no runtime")
            return runtime
        if self.harness_adapter is None:
            raise StoreError("offline harness adapter is not configured")
        profile = self._harness_profile(claim.run_id)
        if profile is None:
            raise StoreError("frozen harness profile is unavailable")
        from .harness_runtime import (
            HarnessCapabilityRuntime,
            build_profile_receipt_bridge,
        )

        bridge = build_profile_receipt_bridge(
            profile, self.harness_r1_profile,
        )
        return HarnessCapabilityRuntime(
            bridge,
            adapter=self.harness_adapter,
            attempt_journal=store,
            journal_owner_token=claim.owner_token,
            run_claim=claim,
            run_control=self,
            control_db_path=self.db_path,
            run_lease_seconds=self.lease_seconds,
            renew_interval_seconds=self.heartbeat_seconds,
            catalog=self.harness_catalog,
            require_run_cas=True,
        )

    @staticmethod
    def _preflight_ok(result: Any) -> bool:
        if isinstance(result, Mapping):
            return result.get("ok") is True
        return getattr(result, "ok", False) is True

    def _persist_harness_preflight_failure(
        self,
        store: Store,
        claim: ExecutionClaim,
        runtime: Any,
        unit: ManifestWorkUnit,
        result: Any = None,
    ) -> None:
        """Record only a de-sensitive diagnosis; never declare an attempt."""
        try:
            from .harness_runtime import (
                build_preflight_diagnosis,
                persist_preflight_diagnosis,
            )
            from mm_r6.agent_harness import PreflightResult

            bridge = getattr(runtime, "bridge", None)
            if bridge is None:
                return
            if not isinstance(result, PreflightResult):
                profile = bridge.r6_profile
                reasons = tuple(
                    str(value) for value in (
                        result.get("reasons", ())
                        if isinstance(result, Mapping) else getattr(result, "reasons", ())
                    )
                )
                result = PreflightResult(
                    ok=False,
                    executable="",
                    selector=profile.effective_selector,
                    effort=profile.reasoning_effort,
                    allowed_tools=tuple(profile.allowed_tools),
                    timeout_seconds=int(profile.timeout_seconds),
                    reasons=reasons or ("preflight_failed",),
                )
            diagnosis = build_preflight_diagnosis(
                bridge,
                result,
                run_id=claim.run_id,
                node_id=unit.node_id,
                manifest_revision=claim.manifest_revision,
            )
            persist_preflight_diagnosis(store, diagnosis)
        except Exception:
            # A missing optional diagnosis projection must not turn a failed
            # preflight into an attempt or a transport dispatch.
            return

    def _preflight_harness(
        self,
        store: Store,
        claim: ExecutionClaim,
        runtime: Any,
        unit: ManifestWorkUnit,
    ) -> bool:
        try:
            from .harness_runtime import persist_profile_receipt_bridge

            bridge = getattr(runtime, "bridge", None)
            if bridge is not None:
                persist_profile_receipt_bridge(store, bridge, run_id=claim.run_id)
            preflight = getattr(runtime, "preflight", None)
            if not callable(preflight):
                raise StoreError("harness runtime preflight is unavailable")
            result = preflight()
        except Exception as exc:
            self._persist_harness_preflight_failure(store, claim, runtime, unit)
            return False
        if not self._preflight_ok(result):
            self._persist_harness_preflight_failure(
                store, claim, runtime, unit, result
            )
            return False
        return self._claim_permitted(claim)

    @staticmethod
    def _capability_attempt_id(
        run_id: str, revision: int, work_unit_id: str, ordinal: int,
    ) -> str:
        return (
            f"r7-capability:{run_id}:{revision}:{work_unit_id}:attempt-{ordinal}"
        )

    def _ai_payload_and_coverage(
        self, unit: ManifestWorkUnit,
    ) -> tuple[dict[str, str], tuple[CoverageUnit, ...]]:
        payload = {
            "work_unit_id": unit.work_unit_id,
            "scope": unit.scope,
            "target_ref": unit.target_ref,
        }
        expected = (CoverageUnit(scope=unit.scope, key=unit.target_ref),)
        return payload, expected

    def _invoke_ai_attempt(
        self,
        store: Store,
        claim: ExecutionClaim,
        unit: ManifestWorkUnit,
        runtime: Any,
        controller: CapabilityWorkUnitController,
        *,
        attempt_id: str,
        continued_from: str = "",
    ) -> Any:
        run = store.get_run(claim.run_id)
        payload, expected = self._ai_payload_and_coverage(unit)
        versions = InvocationVersions(
            source_revision_id=run.source_revision_id,
            rule_version="mm-r7-slice06-rule-v1",
            knowledge_version="mm-r7-slice06-knowledge-v1",
            graph_version="mm-r7-slice06-harness-v1",
            schema_version="mm-r7-slice06-schema-v1",
        )
        if continued_from:
            return controller.resume(
                runtime,
                continued_from,
                attempt_id=attempt_id,
                manifest_revision=claim.manifest_revision,
            )
        return controller.execute(
            runtime,
            work_unit_id=unit.work_unit_id,
            attempt_id=attempt_id,
            monitoring_run_id=claim.run_id,
            node_id=unit.node_id,
            manifest_revision=claim.manifest_revision,
            versions=versions,
            payload=payload,
            expected_units=expected,
        )

    def _retry_ai_if_allowed(
        self,
        store: Store,
        claim: ExecutionClaim,
        unit: ManifestWorkUnit,
        runtime: Any,
        controller: CapabilityWorkUnitController,
        previous_attempt_id: str,
    ) -> Any:
        control = self._control(claim.run_id)
        if control.state is not ExecutionControlState.RUNNING:
            return None
        if not self._claim_permitted(claim):
            return None
        history = _bound_capability_attempts(
            store, claim.run_id, claim.manifest_revision, unit.work_unit_id
        )
        if not history:
            return None
        latest = history[-1]
        if (
            latest["attempt_id"] != previous_attempt_id
            or latest["attempt_ordinal"] >= MAX_CAPABILITY_ATTEMPTS
            or latest.get("status") not in RETRYABLE_CAPABILITY_ATTEMPT_STATUSES
        ):
            return None
        next_id = self._capability_attempt_id(
            claim.run_id,
            claim.manifest_revision,
            unit.work_unit_id,
            latest["attempt_ordinal"] + 1,
        )
        return self._invoke_ai_attempt(
            store,
            claim,
            unit,
            runtime,
            controller,
            attempt_id=next_id,
            continued_from=previous_attempt_id,
        )

    def _start_execution_unlocked(self, run_id: str) -> dict[str, Any]:
        self._validate(run_id)
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, float(self.clock()))
        claim, replayed = self._claim(run_id, "start")
        if claim is not None:
            self._spawn(claim)
        return self._action_response(run_id, replayed=replayed)
    def start_execution(self, run_id: str) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._start_execution_unlocked(run_id)

    start = start_execution
    start_run = start_execution

    def _resume_execution_unlocked(self, run_id: str) -> dict[str, Any]:
        self._validate(run_id)
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, float(self.clock()))
        claim, replayed = self._claim(run_id, "resume")
        if claim is not None:
            self._spawn(claim)
        return self._action_response(run_id, replayed=replayed)
    def resume_execution(self, run_id: str) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._resume_execution_unlocked(run_id)

    resume = resume_execution
    resume_run = resume_execution

    def _cancel_execution_unlocked(self, run_id: str) -> dict[str, Any]:
        self._validate(run_id)
        current_time = float(self.clock())
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, current_time)
        connection = _connect(self.db_path)
        replayed = False
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _require_control_schema(connection)
                control = _checked_control(connection, run_id)
                if (
                    control.state in _ACTIVE_STATES
                    and control.lease_expires_at is not None
                    and control.lease_expires_at <= current_time
                ):
                    stamp = _now_text(current_time)
                    cursor = connection.execute(
                        f"UPDATE {CONTROL_TABLE_NAME} SET generation=?, state=?,"
                        " owner_token='', lease_expires_at=NULL, cancel_requested=0,"
                        " updated_at=? WHERE run_id=? AND manifest_revision=?"
                        " AND generation=? AND owner_token=?",
                        (
                            control.generation + 1,
                            ExecutionControlState.INTERRUPTED.value,
                            stamp, run_id, control.manifest_revision, control.generation,
                            control.owner_token,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise _error("runtime_integrity_failed")
                    control = _checked_control(connection, run_id)
                if control.state is ExecutionControlState.RUNNING:
                    stamp = _now_text(current_time)
                    cursor = connection.execute(
                        f"UPDATE {CONTROL_TABLE_NAME} SET state=?, cancel_requested=1,"
                        " updated_at=? WHERE run_id=? AND manifest_revision=?"
                        " AND generation=? AND owner_token=? AND state=?"
                        " AND lease_expires_at>?",
                        (
                            ExecutionControlState.CANCELLING.value, stamp, run_id,
                            control.manifest_revision, control.generation,
                            control.owner_token, ExecutionControlState.RUNNING.value,
                            current_time,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise _error("not_running")
                elif control.state in {
                    ExecutionControlState.CANCELLING,
                    ExecutionControlState.INTERRUPTED,
                    ExecutionControlState.FINISHED,
                }:
                    replayed = True
                else:
                    raise _error("not_running")
                connection.execute("COMMIT")
            except BaseException:
                try:
                    connection.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
        except ExecutionControlError:
            raise
        except (sqlite3.Error, OSError, ValueError) as exc:
            raise _error("runtime_integrity_failed") from exc
        finally:
            connection.close()
        return self._action_response(run_id, replayed=replayed)
    def cancel_execution(self, run_id: str) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._cancel_execution_unlocked(run_id)

    cancel = cancel_execution
    stop = cancel_execution
    cancel_run = cancel_execution
    start_background = start_execution
    resume_background = resume_execution
    cancel_background = cancel_execution

    def wait(self, run_id: str, timeout: Optional[float] = None) -> bool:
        control = self._control(run_id)
        key = self._key(run_id, control.manifest_revision)
        with self._registry_lock:
            worker = self._registry.get(key)
        if worker is None:
            return not self.running(run_id)
        worker.join(timeout)
        return not worker.is_alive()

    def running(self, run_id: str) -> bool:
        try:
            control = self._control(run_id)
        except ExecutionControlError:
            return False
        key = self._key(run_id, control.manifest_revision)
        with self._registry_lock:
            worker = self._registry.get(key)
        return worker is not None and worker.is_alive()

    is_running = running

    def _snapshot_unlocked(self, run_id: str, *, feed_limit: int = 20) -> dict[str, Any]:
        """Read R1 audience data and control overlay from one SQLite snapshot."""
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, float(self.clock()))
        store = _open_store(self.db_path, self.artifact_dir)
        try:
            return _read_snapshot_from_store(store, run_id, feed_limit=feed_limit)
        finally:
            store.close()
    def snapshot(self, run_id: str, *, feed_limit: int = 20) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._snapshot_unlocked(run_id, feed_limit=feed_limit)

    read_progress = snapshot
    get_progress = snapshot

    def _snapshot_from_store_unlocked(
        self, store: Store, run_id: str, *, feed_limit: int = 20,
    ) -> dict[str, Any]:
        """Use a caller-owned Store while keeping base view and overlay atomic."""
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, float(self.clock()))
        return _read_snapshot_from_store(store, run_id, feed_limit=feed_limit)
    def snapshot_from_store(
        self, store: Store, run_id: str, *, feed_limit: int = 20,
    ) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._snapshot_from_store_unlocked(
                store, run_id, feed_limit=feed_limit
            )

    def _action_response(self, run_id: str, *, replayed: bool) -> dict[str, Any]:
        control = self._control(run_id)
        if control.state in {
            ExecutionControlState.INTERRUPTED,
            ExecutionControlState.FINISHED,
            ExecutionControlState.CANCELLING,
        }:
            view = self.snapshot(run_id)
            overlay = {
                "run_status_text": view["run_status_text"],
                "available_actions": view["available_actions"],
            }
        else:
            overlay = _public_overlay(control, {"completed": 0, "total": 1})
        return {
            "replayed": bool(replayed),
            "run_status_text": overlay["run_status_text"],
            "available_actions": overlay["available_actions"],
        }

    def _release_claim(self, claim: ExecutionClaim, *, interrupted: bool) -> None:
        current_time = float(self.clock())
        connection = _connect(self.db_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _require_control_schema(connection)
                state = (
                    ExecutionControlState.INTERRUPTED
                    if interrupted else ExecutionControlState.FINISHED
                )
                cursor = connection.execute(
                    f"UPDATE {CONTROL_TABLE_NAME} SET state=?, owner_token='',"
                    " lease_expires_at=NULL, cancel_requested=0, updated_at=?"
                    " WHERE run_id=? AND manifest_revision=? AND generation=?"
                    " AND owner_token=? AND state IN (?,?)",
                    (
                        state.value, _now_text(current_time), claim.run_id,
                        claim.manifest_revision, claim.generation, claim.owner_token,
                        ExecutionControlState.RUNNING.value,
                        ExecutionControlState.CANCELLING.value,
                    ),
                )
                if cursor.rowcount:
                    connection.execute("COMMIT")
                else:
                    connection.execute("ROLLBACK")
            except BaseException:
                try:
                    connection.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
        except (ExecutionControlError, sqlite3.Error, OSError, ValueError):
            # A stale worker must not replace a newer owner.  The next
            # explicit resume/recovery operation will reconcile the row.
            return
        finally:
            connection.close()

    def _worker_main_locked(self, claim: ExecutionClaim, stop_event: threading.Event) -> None:
        key = self._key(claim.run_id, claim.manifest_revision)
        store: Optional[Store] = None
        try:
            store = _open_store(self.db_path, self.artifact_dir)
            stalled_rounds = 0
            while True:
                if stop_event.is_set():
                    self._release_claim(claim, interrupted=True)
                    return
                if not self.heartbeat(
                    claim.run_id, claim.manifest_revision, claim.generation,
                    claim.owner_token,
                ):
                    if self._finish_cancelled_if_quiescent(store, claim):
                        return
                    self._release_claim(claim, interrupted=True)
                    return
                manifest = store.get_manifest(claim.run_id, claim.manifest_revision)
                if manifest is None or not manifest.work_units:
                    self._release_claim(claim, interrupted=True)
                    return
                rows = {
                    row.work_unit_id: row
                    for row in store.list_work_unit_runs(
                        claim.run_id, claim.manifest_revision,
                    )
                }
                statuses = {unit_id: row.status.value for unit_id, row in rows.items()}
                runnable = _runnable_units(
                    manifest,
                    statuses,
                    continuable_ids=_continuable_ai_units(
                        store, claim.run_id, claim.manifest_revision, manifest
                    ),
                )
                if not runnable:
                    if self._finish_if_quiescent(store, claim, statuses, manifest):
                        return
                    stalled_rounds += 1
                    if stalled_rounds >= 3:
                        self._release_claim(claim, interrupted=True)
                        return
                    stop_event.wait(self.sweep_seconds)
                    continue
                progressed = False
                for unit in runnable:
                    if stop_event.is_set() or not self.heartbeat(
                        claim.run_id, claim.manifest_revision, claim.generation,
                        claim.owner_token,
                    ):
                        self._release_claim(claim, interrupted=True)
                        return
                    result = self._process_unit(store, claim, unit, stop_event)
                    progressed = progressed or result
                if not progressed:
                    stalled_rounds += 1
                    if stalled_rounds >= 3:
                        self._release_claim(claim, interrupted=True)
                        return
                    stop_event.wait(self.sweep_seconds)
                else:
                    stalled_rounds = 0
                    if self.sweep_seconds:
                        stop_event.wait(self.sweep_seconds)
        except Exception:
            self._release_claim(claim, interrupted=True)
        finally:
            if store is not None:
                store.close()
            with self._registry_lock:
                if self._registry.get(key) is threading.current_thread():
                    self._registry.pop(key, None)

    def _worker_main(self, claim: ExecutionClaim, stop_event: threading.Event) -> None:
        try:
            with self._shared_project_maintenance():
                self._worker_main_locked(claim, stop_event)
        except ExecutionControlError:
            # The claim remains lease-bound when the worker cannot enter the
            # shared gate; a later explicit recovery can reconcile it.
            pass

    def _process_unit(
        self, store: Store, claim: ExecutionClaim, unit: ManifestWorkUnit,
        stop_event: threading.Event,
    ) -> bool:
        manifest = store.get_manifest(claim.run_id, claim.manifest_revision)
        if manifest is None:
            self._release_claim(claim, interrupted=True)
            return False
        if unit.work_unit_id in _ai_unit_ids(manifest):
            return self._process_ai_unit(store, claim, unit, stop_event)
        stable_key = f"r7-background:{claim.run_id}:{claim.manifest_revision}:{unit.work_unit_id}"
        detail = f"正在{unit.label}"
        # Re-check immediately before the R1 begin callback.  A lease may
        # expire between the sweep-level heartbeat and this point; a resumed
        # generation must be the only one allowed to claim new work.
        if not self._claim_permitted(claim):
            self._release_claim(claim, interrupted=True)
            return False
        try:
            store.begin_work_unit(
                claim.run_id, unit.work_unit_id, stable_key, detail,
                manifest_revision=claim.manifest_revision,
            )
        except (IdempotencyConflictError, StaleCallbackError, StoreError):
            return False
        if not self._sleep_synthetic(claim, stop_event):
            self._release_claim(claim, interrupted=True)
            return False
        try:
            outcome = self.unit_step(unit, stable_key)
        except Exception:
            outcome = BackgroundOutcome(
                NodeStatus.FAILED, f"未完成：{unit.label}"
            )
        if not isinstance(outcome, BackgroundOutcome):
            outcome = BackgroundOutcome(
                NodeStatus.FAILED, f"未完成：{unit.label}"
            )
        if outcome.status not in TERMINAL_NODE_STATUSES or not isinstance(outcome.detail, str):
            outcome = BackgroundOutcome(
                NodeStatus.FAILED, f"未完成：{unit.label}"
            )
        if not self._commit_permitted(claim):
            self._release_claim(claim, interrupted=True)
            return False
        try:
            store.complete_work_unit(
                claim.run_id, unit.work_unit_id, stable_key, outcome.status,
                outcome.detail, evidence_count=0,
                manifest_revision=claim.manifest_revision,
            )
            return True
        except (IdempotencyConflictError, StaleCallbackError, StoreError):
            # A lost lease, injected store failure, or another same-key writer
            # leaves the ledger authoritative.  The next sweep may replay the
            # same stable key; it never fabricates a second progress record.
            return False

    def _process_ai_unit(
        self,
        store: Store,
        claim: ExecutionClaim,
        unit: ManifestWorkUnit,
        stop_event: threading.Event,
    ) -> bool:
        """Run one AI candidate through R1's controller and bounded retry."""
        del stop_event  # The injected harness owns the blocking transport wait.
        if not self._claim_permitted(claim):
            self._release_claim(claim, interrupted=True)
            return False
        try:
            runtime = self._make_harness_runtime(store, claim, unit)
        except Exception:
            # No attempt is declared when the offline runtime cannot even be
            # constructed.  Keep the work unit pending and let the run recover.
            self._release_claim(claim, interrupted=True)
            return False
        if not self._preflight_harness(store, claim, runtime, unit):
            self._release_claim(claim, interrupted=True)
            return False
        if not self._claim_permitted(claim):
            self._release_claim(claim, interrupted=True)
            return False

        controller = CapabilityWorkUnitController(store)
        history = _bound_capability_attempts(
            store, claim.run_id, claim.manifest_revision, unit.work_unit_id
        )
        previous_attempt_id = ""
        if history:
            latest = history[-1]
            latest_status = latest.get("status")
            if latest_status in RETRYABLE_CAPABILITY_ATTEMPT_STATUSES:
                if latest["attempt_ordinal"] >= MAX_CAPABILITY_ATTEMPTS:
                    return False
                attempt_id = self._capability_attempt_id(
                    claim.run_id,
                    claim.manifest_revision,
                    unit.work_unit_id,
                    latest["attempt_ordinal"] + 1,
                )
                previous_attempt_id = latest["attempt_id"]
            elif latest_status in {"declared", "running"}:
                # A process restart may leave a declared assignment without a
                # binding.  Replay that exact assignment; R1 controls whether
                # the attempt can claim its lease.
                attempt_id = latest["attempt_id"]
            else:
                return False
        else:
            attempt_id = self._capability_attempt_id(
                claim.run_id,
                claim.manifest_revision,
                unit.work_unit_id,
                1,
            )

        try:
            result = self._invoke_ai_attempt(
                store,
                claim,
                unit,
                runtime,
                controller,
                attempt_id=attempt_id,
                continued_from=previous_attempt_id,
            )
        except Exception:
            # Runtime exceptions are converted to an interrupted R1 attempt by
            # CapabilityRuntime.  A running owner gets exactly one linked retry;
            # cancelling or a lost lease never creates it.
            try:
                current = store.get_capability_attempt(attempt_id)
                status = current.get("status") if current else ""
                if status == "interrupted":
                    retry = self._retry_ai_if_allowed(
                        store,
                        claim,
                        unit,
                        runtime,
                        controller,
                        attempt_id,
                    )
                    return retry is not None
            except Exception:
                pass
            return False

        result_status = getattr(getattr(result, "status", None), "value", "")
        if result_status in RETRYABLE_CAPABILITY_ATTEMPT_STATUSES:
            try:
                retry = self._retry_ai_if_allowed(
                    store,
                    claim,
                    unit,
                    runtime,
                    controller,
                    attempt_id,
                )
                if retry is not None:
                    return True
            except Exception:
                # The first terminal result remains authoritative.  A failed
                # retry will be surfaced as a resumable/limited unit state.
                return True
        return True

    def _sleep_synthetic(
        self, claim: ExecutionClaim, stop_event: threading.Event,
    ) -> bool:
        """Wait for the configured synthetic action while renewing its lease."""
        remaining = self.step_seconds
        while remaining > 0:
            if stop_event.is_set():
                return False
            interval = min(remaining, self.heartbeat_seconds)
            started = time.monotonic()
            if stop_event.wait(interval):
                return False
            remaining -= max(0.0, time.monotonic() - started)
            if remaining > 0 and not self.heartbeat(
                claim.run_id, claim.manifest_revision, claim.generation,
                claim.owner_token,
            ):
                # A user stop changes the control row to ``cancelling`` and
                # intentionally makes heartbeat renewal return false.  The
                # current synthetic action may still finish; only a lost
                # generation/owner or an expired lease aborts it.
                try:
                    control = self._control(claim.run_id)
                except ExecutionControlError:
                    return False
                if not (
                    control.manifest_revision == claim.manifest_revision
                    and control.generation == claim.generation
                    and control.owner_token == claim.owner_token
                    and control.state is ExecutionControlState.CANCELLING
                    and control.lease_expires_at is not None
                    and control.lease_expires_at > float(self.clock())
                ):
                    return False
        return not stop_event.is_set()

    def _claim_permitted(self, claim: ExecutionClaim) -> bool:
        """CAS guard used before a new R1 work-unit begin callback."""
        now = float(self.clock())
        connection = _connect(self.db_path)
        try:
            _require_control_schema(connection)
            row = _raw_control(connection, claim.run_id)
            if row is None:
                return False
            control = _control_from_row(row)
            return bool(
                control.manifest_revision == claim.manifest_revision
                and control.generation == claim.generation
                and control.owner_token == claim.owner_token
                and control.state is ExecutionControlState.RUNNING
                and not control.cancel_requested
                and control.lease_expires_at is not None
                and control.lease_expires_at > now
            )
        except ExecutionControlError:
            return False
        finally:
            connection.close()

    def _commit_permitted(self, claim: ExecutionClaim) -> bool:
        """Check the owner CAS immediately before the R1 terminal callback.

        ``cancelling`` is allowed here: the contract lets the current
        synthetic unit finish, then prevents the next claim.  A public
        heartbeat remains stricter and only renews ``running`` leases.
        """
        now = float(self.clock())
        connection = _connect(self.db_path)
        try:
            _require_control_schema(connection)
            row = _raw_control(connection, claim.run_id)
            if row is None:
                return False
            control = _control_from_row(row)
            return bool(
                control.manifest_revision == claim.manifest_revision
                and control.generation == claim.generation
                and control.owner_token == claim.owner_token
                and control.state in _ACTIVE_STATES
                and control.lease_expires_at is not None
                and control.lease_expires_at > now
            )
        except ExecutionControlError:
            return False
        finally:
            connection.close()

    def _finish_cancelled_if_quiescent(
        self, store: Store, claim: ExecutionClaim,
    ) -> bool:
        """Finish a stopped run only when its ledger has no resumable work."""
        try:
            control = self._control(claim.run_id)
        except ExecutionControlError:
            return False
        if not (
            control.manifest_revision == claim.manifest_revision
            and control.generation == claim.generation
            and control.owner_token == claim.owner_token
            and control.state is ExecutionControlState.CANCELLING
        ):
            return False
        manifest = store.get_manifest(claim.run_id, claim.manifest_revision)
        if manifest is None:
            return False
        statuses = {
            row.work_unit_id: row.status.value
            for row in store.list_work_unit_runs(
                claim.run_id, claim.manifest_revision,
            )
        }
        return self._finish_if_quiescent(store, claim, statuses, manifest)

    def _finish_if_quiescent(
        self, store: Store, claim: ExecutionClaim, statuses: Mapping[str, str],
        manifest: ExecutionManifest,
    ) -> bool:
        continuable_ids = _continuable_ai_units(
            store,
            claim.run_id,
            claim.manifest_revision,
            manifest,
        )
        if continuable_ids:
            return False
        has_nonterminal = any(status not in _TERMINAL_VALUES for status in statuses.values())
        if has_nonterminal:
            runnable = _runnable_units(
                manifest, statuses, continuable_ids=continuable_ids
            )
            # A failed/blocked dependency makes remaining pending work
            # permanently non-runnable in this slice.  Leave those rows
            # pending and close the run honestly.  A live dependency or a
            # malformed state is not silently marked finished.
            failed_dependency = any(
                statuses.get(dep) in {
                    NodeStatus.FAILED.value, NodeStatus.BLOCKED.value,
                }
                for unit in manifest.work_units
                if statuses.get(unit.work_unit_id) in {
                    NodeStatus.PENDING.value, NodeStatus.RUNNING.value,
                }
                for dep in unit.depends_on
            )
            if runnable or not failed_dependency:
                return False
        self._release_claim(claim, interrupted=False)
        return True

    def progress(self, run_id: str, *, feed_limit: int = 20) -> dict[str, Any]:
        return self.snapshot(run_id, feed_limit=feed_limit)


def synthetic_outcome(unit: ManifestWorkUnit, idempotency_key: str = "") -> BackgroundOutcome:
    """Default offline action: one deterministic, audience-readable pass."""
    del idempotency_key
    return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")


def audience_snapshot(
    db_path: Union[str, Path], artifact_dir: Union[str, Path], run_id: str,
    *, feed_limit: int = 20,
) -> dict[str, Any]:
    """Reconstruct R1 audience progress plus the R7 Chinese overlay."""
    return BackgroundRecoveryAdapter(
        db_path=db_path, artifact_dir=artifact_dir,
    ).snapshot(run_id, feed_limit=feed_limit)


BackgroundRecovery = BackgroundRecoveryAdapter
RunControlAdapter = BackgroundRecoveryAdapter


__all__ = [
    "ARTIFACT_DIR_NAME",
    "audience_snapshot",
    "BackgroundOutcome",
    "BackgroundRecovery",
    "BackgroundRecoveryError",
    "CONTROL_STATES",
    "CONTROL_TABLE",
    "CONTROL_TABLE_NAME",
    "ControlState",
    "ExecutionClaim",
    "ExecutionControl",
    "ExecutionControlError",
    "ExecutionControlState",
    "ExecutionState",
    "BackgroundRecoveryAdapter",
    "HEARTBEAT_SECONDS",
    "LEASE_SECONDS",
    "MAX_CAPABILITY_ATTEMPTS",
    "list_bound_capability_attempts",
    "RETRYABLE_CAPABILITY_ATTEMPT_STATUSES",
    "RUN_STATE_VALUES",
    "RunControlAdapter",
    "RUNTIME_DB_NAME",
    "assert_prepare_scope_change_allowed",
    "ensure_execution_control",
    "continuable_ai_unit",
    "synthetic_outcome",
]
