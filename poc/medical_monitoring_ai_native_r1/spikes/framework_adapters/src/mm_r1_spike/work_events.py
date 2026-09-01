"""Append-only operational work-event store (worker_01-owned spike substrate).

Work events are operational evidence broadcast while a candidate engine runs a
node: they carry structured progress (node/work-unit/status/current-detail/
timestamp) and are strictly append-only.  They are NEVER domain authority:
they cannot stage artifacts, transition run state, or store facts.  The
authoritative slice1 Store remains the sole domain authority.

Semantics implemented here (execution context: Shared Contract And Required
Evidence / Risk Boundaries):
  * every event carries exactly the required fields (see
    :data:`~mm_r1_spike.contract.REQUIRED_WORK_EVENT_FIELDS`);
  * events are append-only with a monotonic per-run ``sequence`` and a global
    autoincrement rowid -- ordering is physical and inspectable;
  * retry/replay of the SAME idempotency key with the SAME outcome is a no-op
    (deduplication: the stored event is returned, no duplicate row);
  * reuse of an idempotency key with a DIVERGENT payload is rejected
    (:class:`WorkEventConflictError`) -- never overwrite, never silently
    duplicate a side effect;
  * ``completed``/``total`` are derived from the frozen manifest via the
    :class:`~mm_r1_spike.contract.ConformanceContract`; the store rejects any
    event whose ``total`` diverges from the contract.

Persistence is SQLite (standard library only) inside a separate operational
file.  No pickle; only JSON-compatible state.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from mm_r1.domain import (
    ExecutionManifest,
    canonical_json,
    content_hash,
    now_iso,
)

from .contract import (
    ConformanceContract,
    REQUIRED_WORK_EVENT_FIELDS,
    WORK_EVENT_STATUSES,
)


class WorkEventError(Exception):
    """Base class for work-event store violations."""


class WorkEventConflictError(WorkEventError):
    """An idempotency key was replayed with a divergent payload.

    Mirrors the slice1 ``IdempotencyConflictError`` rule: never overwrite a
    committed outcome, never silently duplicate a side effect.
    """


_SCHEMA = """
CREATE TABLE IF NOT EXISTS work_events (
    rowid_ INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    node_id TEXT NOT NULL,
    work_unit_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    status TEXT NOT NULL,
    completed INTEGER NOT NULL,
    total INTEGER NOT NULL,
    current_detail TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    event_json TEXT NOT NULL,
    UNIQUE (run_id, sequence),
    UNIQUE (idempotency_key),
    UNIQUE (event_id)
);
CREATE INDEX IF NOT EXISTS idx_work_events_run ON work_events(run_id, sequence);
CREATE INDEX IF NOT EXISTS idx_work_events_node ON work_events(run_id, node_id);
"""


@dataclass(frozen=True)
class WorkEvent:
    """A single structured work event (operational, non-authoritative)."""

    event_id: str
    run_id: str
    manifest_revision: int
    sequence: int
    node_id: str
    work_unit_id: str
    phase: str
    status: str
    completed: int
    total: int
    current_detail: str
    created_at: str
    idempotency_key: str

    def to_json(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "manifest_revision": self.manifest_revision,
            "sequence": self.sequence,
            "node_id": self.node_id,
            "work_unit_id": self.work_unit_id,
            "phase": self.phase,
            "status": self.status,
            "completed": self.completed,
            "total": self.total,
            "current_detail": self.current_detail,
            "created_at": self.created_at,
            "idempotency_key": self.idempotency_key,
        }


class WorkEventStore:
    """Append-only SQLite work-event store (separate operational persistence).

    The backing file is separate from the authoritative slice1 Store.  This
    store performs no domain writes: it records operational progress only.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), isolation_level=None)
        # busy_timeout BEFORE journal_mode so concurrent connections opening
        # the same file do not fail with "database is locked" during init.
        self._conn.execute("PRAGMA busy_timeout=10000")
        self._set_wal_with_retry()
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.executescript(_SCHEMA)

    def _set_wal_with_retry(self) -> None:
        """Set WAL mode, retrying briefly if another connection holds the
        journal-mode lock.  WAL is persistent in the file header, so once one
        connection sets it, subsequent opens no-op."""
        import time
        for _ in range(50):
            try:
                self._conn.execute("PRAGMA journal_mode=WAL")
                return
            except sqlite3.OperationalError:
                time.sleep(0.01)
        # final attempt: let the error propagate if still locked
        self._conn.execute("PRAGMA journal_mode=WAL")

    # ------------------------------------------------------------------ utils

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "WorkEventStore":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _next_sequence(self, run_id: str) -> int:
        row = self._conn.execute(
            "SELECT COALESCE(MAX(sequence), 0) FROM work_events WHERE run_id=?",
            (run_id,),
        ).fetchone()
        return int(row[0]) + 1

    # ------------------------------------------------------------- append API

    def append(
        self,
        event: Mapping[str, Any],
        contract: ConformanceContract,
    ) -> WorkEvent:
        """Append one structured work event.

        Validates every required field, binds the event to the exact frozen
        graph via the contract identity (run_id + node set + manifest
        revision), derives ``completed``/``total`` against the frozen-manifest
        contract, deduplicates same-key same-outcome replays, and rejects
        divergent idempotency-key reuse.

        All dedup/conflict lookup, next-sequence allocation and the insert
        happen inside ONE ``BEGIN IMMEDIATE`` transaction so two concurrent
        connections cannot race a duplicate sequence/event/side effect.
        SQLite durability is unchanged (WAL + synchronous=FULL).

        Returns the stored (or reused) :class:`WorkEvent`.
        """
        self._validate_fields(event)
        status = str(event["status"])
        if status not in WORK_EVENT_STATUSES:
            raise WorkEventError(f"invalid work-event status: {status!r}")
        run_id = str(event["run_id"])
        node_id = str(event["node_id"])
        # Fail-closed contract binding: the event must belong to the exact
        # frozen run/graph.  A different run with the same revision and node
        # count is rejected here (before any DB write).
        if run_id != contract.run_id:
            raise WorkEventError(
                f"work-event run_id {run_id!r} != contract run_id {contract.run_id!r}"
            )
        if node_id not in contract.node_ids:
            raise WorkEventError(
                f"work-event node_id {node_id!r} not in frozen node set "
                f"{list(contract.node_ids)}"
            )
        if int(event["manifest_revision"]) != contract.manifest_revision:
            raise WorkEventError(
                "work-event manifest_revision diverges from contract: "
                f"{event['manifest_revision']} != {contract.manifest_revision}"
            )

        # Exact progress is derived from the frozen manifest; reject any total
        # that diverges from the contract's manifest-derived total.
        completed = int(event["completed"])
        total = int(event["total"])
        if total != contract.total_units:
            raise WorkEventError(
                f"work-event total {total} diverges from manifest-derived "
                f"total {contract.total_units}"
            )
        if completed < 0 or completed > total:
            raise WorkEventError(
                f"work-event completed {completed} out of range [0, {total}]"
            )

        key = str(event["idempotency_key"])
        created_at = str(event.get("created_at") or now_iso())
        normalized: Dict[str, Any] = {
            "event_id": str(event["event_id"]),
            "run_id": run_id,
            "manifest_revision": int(event["manifest_revision"]),
            "sequence": 0,  # assigned inside the transaction below
            "node_id": node_id,
            "work_unit_id": str(event["work_unit_id"]),
            "phase": str(event["phase"]),
            "status": status,
            "completed": completed,
            "total": total,
            "current_detail": str(event["current_detail"]),
            "created_at": created_at,
            "idempotency_key": key,
        }

        payload_hash = content_hash({
            "run_id": normalized["run_id"],
            "manifest_revision": normalized["manifest_revision"],
            "node_id": normalized["node_id"],
            "work_unit_id": normalized["work_unit_id"],
            "phase": normalized["phase"],
            "status": normalized["status"],
            "completed": normalized["completed"],
            "total": normalized["total"],
            "current_detail": normalized["current_detail"],
        })

        # ONE transaction: dedup/conflict lookup + sequence allocation + insert.
        # A second connection that races the same key/sequence blocks on the
        # IMMEDIATE lock; the loser then sees the committed row and either
        # dedups (same payload) or conflicts (divergent payload).  No duplicate
        # sequence or side effect can be produced.
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            existing = self._conn.execute(
                "SELECT payload_hash, sequence FROM work_events WHERE idempotency_key=?",
                (key,),
            ).fetchone()
            if existing is not None:
                stored_hash, stored_seq = existing
                if stored_hash != payload_hash:
                    self._conn.execute("ROLLBACK")
                    raise WorkEventConflictError(
                        f"work-event idempotency key {key!r} reused with a divergent "
                        "payload (status/progress/phase/current_detail differ)"
                    )
                # same key + same payload -> idempotent replay (no new row)
                self._conn.execute("COMMIT")
                return self._row_to_event(
                    self._conn.execute(
                        "SELECT * FROM work_events WHERE idempotency_key=?", (key,)
                    ).fetchone()
                )
            # event_id collision -> identity-safe rejection
            eid_existing = self._conn.execute(
                "SELECT 1 FROM work_events WHERE event_id=?", (normalized["event_id"],)
            ).fetchone()
            if eid_existing is not None:
                self._conn.execute("ROLLBACK")
                raise WorkEventConflictError(
                    f"work-event event_id {normalized['event_id']!r} already exists"
                )
            normalized["sequence"] = self._next_sequence(run_id)
            self._conn.execute(
                "INSERT INTO work_events(event_id, run_id, manifest_revision, sequence,"
                " node_id, work_unit_id, phase, status, completed, total, current_detail,"
                " created_at, idempotency_key, payload_hash, event_json)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    normalized["event_id"],
                    normalized["run_id"],
                    normalized["manifest_revision"],
                    normalized["sequence"],
                    normalized["node_id"],
                    normalized["work_unit_id"],
                    normalized["phase"],
                    normalized["status"],
                    normalized["completed"],
                    normalized["total"],
                    normalized["current_detail"],
                    normalized["created_at"],
                    key,
                    payload_hash,
                    canonical_json(normalized),
                ),
            )
            self._conn.execute("COMMIT")
        except BaseException:
            try:
                self._conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        return WorkEvent(**normalized)

    def _validate_fields(self, event: Mapping[str, Any]) -> None:
        missing = [f for f in REQUIRED_WORK_EVENT_FIELDS if f not in event]
        if missing:
            raise WorkEventError(f"work-event missing required fields: {missing}")

    # ------------------------------------------------------------- read API
    def list_events(self, run_id: str) -> List[WorkEvent]:
        rows = self._conn.execute(
            "SELECT * FROM work_events WHERE run_id=? ORDER BY sequence", (run_id,)
        ).fetchall()
        return [self._row_to_event(r) for r in rows]

    def count(self, run_id: Optional[str] = None) -> int:
        if run_id is None:
            row = self._conn.execute("SELECT COUNT(*) FROM work_events").fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM work_events WHERE run_id=?", (run_id,)
            ).fetchone()
        return int(row[0])

    def distinct_idempotency_keys(self, run_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(DISTINCT idempotency_key) FROM work_events WHERE run_id=?",
            (run_id,),
        ).fetchone()
        return int(row[0])

    def sequence_for(self, run_id: str, node_id: str, phase: str) -> int:
        """Return the stored sequence for a (run, node, phase) work event, or 0.

        Used by replay/restart paths that encounter a reused terminal node:
        the node_complete event already exists, so we return its sequence
        instead of re-emitting a divergent event.
        """
        row = self._conn.execute(
            "SELECT sequence FROM work_events WHERE run_id=? AND node_id=? AND phase=?"
            " ORDER BY sequence LIMIT 1",
            (run_id, node_id, phase),
        ).fetchone()
        return int(row[0]) if row is not None else 0

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> WorkEvent:
        # row layout matches _SCHEMA column order.
        return WorkEvent(
            event_id=row[1],
            run_id=row[2],
            manifest_revision=row[3],
            sequence=row[4],
            node_id=row[5],
            work_unit_id=row[6],
            phase=row[7],
            status=row[8],
            completed=row[9],
            total=row[10],
            current_detail=row[11],
            created_at=row[12],
            idempotency_key=row[13],
        )


def derive_progress(manifest: ExecutionManifest, completed_statuses: Mapping[str, str]) -> Dict[str, int]:
    """Derive exact ``completed``/``total`` from the frozen manifest.

    ``completed_statuses`` maps ``node_id -> status``; a node counts as
    completed when its status is a terminal NodeStatus.  ``total`` is always
    ``manifest.total_units()``.
    """
    from mm_r1.domain import NodeStatus, TERMINAL_NODE_STATUSES

    total = int(manifest.total_units())
    completed = 0
    for node in manifest.nodes:
        raw = completed_statuses.get(node.node_id)
        if raw is None:
            continue
        try:
            status = NodeStatus(str(raw))
        except ValueError:
            continue
        if status in TERMINAL_NODE_STATUSES:
            completed += 1
    return {"completed": completed, "total": total}
