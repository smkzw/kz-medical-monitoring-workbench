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
        # Project existence is validated by get_project raising; the synthetic
        # flag is a fixture-lane marker, not an integrity property, and real
        # projects admitted by the data pipeline are legitimate identities.
        store.get_project(run.project_id)
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


