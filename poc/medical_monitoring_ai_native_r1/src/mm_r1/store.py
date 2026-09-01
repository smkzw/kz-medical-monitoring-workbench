"""SQLite authoritative store: atomic commit, audit chain, artifact coverage,
idempotency and recovery protocol (worker_01 public contract).

Commit protocol (Design v1.1 section 12):
  1. Write the immutable, content-addressed artifact file FIRST (canonical JSON
     + sha256), outside any transaction -- a crash here leaves an orphan file
     that is auditable/cleanable but never authoritative.
  2. In ONE SQLite transaction: insert artifact reference, transition state,
     append audit event(s) with the hash chain.
  3. Only then advance the publication pointer (output_state) -- published
     state never appears before the database commit.

Guarantees:
  * No published state before commit (publication pointer moves in-txn).
  * Retries with the same idempotency key return the original result and never
    repeat state transitions or side effects.
  * Late attempt callbacks (different key after terminal) are rejected and
    audited; verified history is never overwritten.
  * Audit chain is append-only and tamper-evident (hash chain verification).
"""

from __future__ import annotations

import datetime
import getpass
import json
import os
import sqlite3
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import quote

from . import domain
from .domain import (
    ACCEPTANCE_CHAIN,
    ACCEPTED_BY_SYSTEM_POLICY,
    TERMINAL_NODE_STATUSES,
    AnalysisState,
    ArtifactEnvelope,
    AuditEvent,
    CanonicalFact,
    Checkpoint,
    CompletionGateError,
    ExecutionBasis,
    ExecutionManifest,
    IdempotencyConflictError,
    ListingSnapshot,
    ManifestWorkUnit,
    MonitoringRun,
    NodeAttempt,
    NodeRun,
    NodeStatus,
    NodeTerminalError,
    NodeType,
    OutputState,
    PromotionForbiddenError,
    ReviewState,
    RunMode,
    SnapshotAcceptance,
    SnapshotAcceptanceState,
    StaleCallbackError,
    StoreError,
    StudyProject,
    SourceRevision,
    UserDisposition,
    WorkUnitRun,
    AcceptanceChainError,
    AmbiguityBlocksAcceptanceError,
    ArtifactCollisionError,
    canonical_json,
    content_hash,
    from_jsonable,
    new_id,
    now_iso,
    sha256_hex,
    to_jsonable,
)

from .schema_shape import connection_shape, shape_from_ddl


_runtime_schema_shape = connection_shape
_shape_from_ddl = shape_from_ddl


AUDIT_GENESIS = sha256_hex(b"mm_r1:audit:genesis:v1")

# Valid state transitions (fail closed: anything not listed is rejected).
_ANALYSIS_TRANSITIONS: Dict[AnalysisState, Tuple[AnalysisState, ...]] = {
    AnalysisState.NOT_STARTED: (AnalysisState.RUNNING,),
    AnalysisState.RUNNING: (AnalysisState.COMPLETE, AnalysisState.BLOCKED, AnalysisState.FAILED),
    AnalysisState.BLOCKED: (AnalysisState.RUNNING,),  # resume after unblocking
    AnalysisState.COMPLETE: (),
    AnalysisState.FAILED: (),
}

_REVIEW_TRANSITIONS: Dict[ReviewState, Tuple[ReviewState, ...]] = {
    ReviewState.NOT_REQUIRED: (
        ReviewState.DETERMINISTIC_VERIFIED,
        ReviewState.INDEPENDENT_AI_REVIEWED,
        ReviewState.NEEDS_USER_ATTENTION,
    ),
    ReviewState.DETERMINISTIC_VERIFIED: (
        ReviewState.INDEPENDENT_AI_REVIEWED,
        ReviewState.NEEDS_USER_ATTENTION,
    ),
    ReviewState.INDEPENDENT_AI_REVIEWED: (
        ReviewState.NEEDS_USER_ATTENTION,
        ReviewState.USER_CONFIRMED,
    ),
    ReviewState.NEEDS_USER_ATTENTION: (
        ReviewState.DETERMINISTIC_VERIFIED,
        ReviewState.INDEPENDENT_AI_REVIEWED,
        ReviewState.USER_CONFIRMED,
    ),
    ReviewState.USER_CONFIRMED: (),
}

_OUTPUT_ORDER: List[OutputState] = [
    OutputState.NOT_PUBLISHED,
    OutputState.DASHBOARD_VISIBLE,
    OutputState.DRAFT_EXPORTABLE,
    OutputState.EXPORTED,
]

_WORK_UNIT_IDENTITY_KEYS = frozenset({
    "provider", "model", "selector", "adapter", "harness", "transport",
    "profile_fingerprint", "attempt_id", "endpoint_alias",
})
_IMMUTABLE_DOMAIN_OBJECT_KINDS = frozenset({
    "adapter_raw_output",
    "capability_work_assignment",
})
_CAPABILITY_ASSIGNMENT_KIND = "capability_work_assignment"
_CAPABILITY_ASSIGNMENT_SCHEMA = "mm-capability-work-assignment-r1"
_RESERVED_INTERNAL_AUDIT_EVENTS = frozenset({
    domain.EVENT_WORK_UNIT_BEGIN,
    domain.EVENT_WORK_UNIT_ATTEMPT_BOUND,
    domain.EVENT_WORK_UNIT_COMPLETE,
    domain.EVENT_CAPABILITY_ATTEMPT_DECLARED,
    domain.EVENT_CAPABILITY_ATTEMPT_CLAIMED,
    domain.EVENT_CAPABILITY_ATTEMPT_INTERRUPTED,
    domain.EVENT_CAPABILITY_ATTEMPT_TERMINAL,
})


class _IdempotencyLedgerConflict(Exception):
    """Private signal used to persist a conflict audit after txn rollback."""

    def __init__(self, payload: Mapping[str, Any]) -> None:
        self.payload = dict(payload)
        super().__init__("idempotency ledger conflict")


class _RuntimeAttemptJournal:
    """Private runtime-only mutation facade for capability attempts.

    ``Store`` keeps read-only attempt inspection public, but transport lifecycle
    mutation is deliberately absent from its public surface.  The capability
    runtime obtains this narrow facade through the private adapter hook below;
    ordinary Store callers therefore cannot manufacture a successful attempt
    and bind it to authoritative work-unit progress.
    """

    def __init__(self, store: "Store") -> None:
        self._store = store

    def declare_capability_attempt(self, **kwargs: Any) -> Mapping[str, Any]:
        return self._store._declare_capability_attempt(**kwargs)

    def claim_capability_attempt(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        return self._store._claim_capability_attempt(*args, **kwargs)

    def interrupt_capability_attempt(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        return self._store._interrupt_capability_attempt(*args, **kwargs)

    def complete_capability_attempt(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        return self._store._complete_capability_attempt(*args, **kwargs)

    def get_capability_attempt(self, attempt_id: str) -> Optional[Mapping[str, Any]]:
        return self._store.get_capability_attempt(attempt_id)


@dataclass
class RunRecoveryState:
    run_id: str
    analysis_state: str
    open_attempts: int
    node_states: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class RecoveryReport:
    audit_ok: bool
    audit_first_bad_seq: Optional[int]
    audit_count: int
    orphan_artifacts: List[str]
    integrity_violations: List[str]
    incomplete_runs: List[RunRecoveryState]

    def is_clean(self) -> bool:
        return (
            self.audit_ok
            and not self.orphan_artifacts
            and not self.integrity_violations
            and not self.incomplete_runs
        )


_SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL,
    config_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_revisions (
    revision_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    source_type TEXT NOT NULL,
    version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    valid_from TEXT,
    scope_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS listing_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    revision_id TEXT NOT NULL REFERENCES source_revisions(revision_id),
    snapshot_version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    structure_json TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snapshot_hash ON listing_snapshots(content_hash);
CREATE TABLE IF NOT EXISTS snapshot_acceptance (
    snapshot_id TEXT PRIMARY KEY REFERENCES listing_snapshots(snapshot_id),
    state TEXT NOT NULL,
    accepted_by TEXT,
    ambiguity_json TEXT,
    blocked INTEGER NOT NULL DEFAULT 0,
    reason TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS monitoring_runs (
    run_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    mode TEXT NOT NULL,
    data_cutoff TEXT NOT NULL,
    source_revision_id TEXT NOT NULL REFERENCES source_revisions(revision_id),
    execution_basis TEXT NOT NULL,
    analysis_state TEXT NOT NULL,
    evidence_state TEXT NOT NULL,
    review_state TEXT NOT NULL,
    output_state TEXT NOT NULL,
    user_disposition TEXT,
    manifest_revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS run_manifests (
    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),
    revision INTEGER NOT NULL,
    manifest_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, revision)
);
CREATE TABLE IF NOT EXISTS work_unit_runs (
    run_id TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL,
    work_unit_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT NOT NULL DEFAULT '',
    begin_hash TEXT NOT NULL DEFAULT '',
    detail TEXT NOT NULL DEFAULT '',
    execution_identity_json TEXT NOT NULL DEFAULT '{}',
    evidence_count INTEGER NOT NULL DEFAULT 0,
    completion_hash TEXT NOT NULL DEFAULT '',
    started_at TEXT,
    finished_at TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (run_id, manifest_revision, work_unit_id),
    FOREIGN KEY (run_id, manifest_revision)
        REFERENCES run_manifests(run_id, revision)
);
CREATE INDEX IF NOT EXISTS idx_work_unit_runs_revision
    ON work_unit_runs(run_id, manifest_revision, status);
CREATE TABLE IF NOT EXISTS manifest_node_progress (
    run_id TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL,
    node_id TEXT NOT NULL,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (run_id, manifest_revision, node_id),
    FOREIGN KEY (run_id, manifest_revision)
        REFERENCES run_manifests(run_id, revision)
);
CREATE INDEX IF NOT EXISTS idx_manifest_node_progress_revision
    ON manifest_node_progress(run_id, manifest_revision, status);
CREATE TABLE IF NOT EXISTS node_runs (
    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),
    node_id TEXT NOT NULL,
    node_type TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    artifact_id TEXT,
    output_json TEXT NOT NULL DEFAULT '{}',
    error TEXT,
    reason TEXT,
    started_at TEXT,
    finished_at TEXT,
    PRIMARY KEY (run_id, node_id)
);
CREATE TABLE IF NOT EXISTS node_attempts (
    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),
    node_id TEXT NOT NULL,
    attempt_seq INTEGER NOT NULL,
    idempotency_key TEXT NOT NULL,
    logical_key TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    payload_hash TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, node_id, attempt_seq),
    UNIQUE (idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_attempts_logical ON node_attempts(logical_key);
CREATE TABLE IF NOT EXISTS capability_attempt_journal (
    attempt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),
    node_id TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    request_json TEXT NOT NULL,
    profile_fingerprint TEXT NOT NULL,
    manifest_revision INTEGER NOT NULL,
    input_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    terminal INTEGER NOT NULL DEFAULT 0,
    owner_token TEXT,
    lease_expires_at REAL,
    result_json TEXT,
    result_hash TEXT,
    continued_from TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    terminal_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_capability_attempt_run
    ON capability_attempt_journal(run_id, node_id, created_at);
CREATE INDEX IF NOT EXISTS idx_capability_attempt_lease
    ON capability_attempt_journal(status, lease_expires_at);
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
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),
    node_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    completeness TEXT NOT NULL,
    envelope_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES monitoring_runs(run_id),
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    chain_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_chain_head (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    last_seq INTEGER NOT NULL,
    last_chain_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),
    node_id TEXT NOT NULL,
    state_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS domain_objects (
    kind TEXT NOT NULL,
    object_id TEXT NOT NULL,
    run_id TEXT REFERENCES monitoring_runs(run_id),
    version INTEGER NOT NULL,
    object_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (kind, object_id, version)
);
CREATE TABLE IF NOT EXISTS canonical_facts (
    run_id TEXT NOT NULL REFERENCES monitoring_runs(run_id),
    fact_hash TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    fact_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, fact_hash)
);
CREATE TABLE IF NOT EXISTS idempotency_ledger (
    idempotency_key TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_run ON audit_events(run_id);
CREATE INDEX IF NOT EXISTS idx_node_runs_run ON node_runs(run_id);
CREATE INDEX IF NOT EXISTS idx_attempts_run ON node_attempts(run_id);
CREATE INDEX IF NOT EXISTS idx_domain_run ON domain_objects(run_id);
"""


def _build_current_runtime_schema_shape() -> Dict[str, Any]:
    return _shape_from_ddl(_SCHEMA)


_CURRENT_RUNTIME_SCHEMA_SHAPE = _build_current_runtime_schema_shape()


def _assert_current_schema(db_path: Path) -> None:
    """Fail closed before opening an existing non-current runtime database."""
    if not db_path.exists():
        return
    connection: Optional[sqlite3.Connection] = None
    try:
        uri = "file:" + quote(str(db_path.resolve()), safe="/") + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, isolation_level=None)
        connection.execute("PRAGMA query_only=ON")
        if int(connection.execute("PRAGMA query_only").fetchone()[0]) != 1:
            raise sqlite3.DatabaseError("query_only was not enabled")
        quick_rows = connection.execute("PRAGMA quick_check").fetchall()
        if not quick_rows or any(
            str(row[0]).lower() != "ok" for row in quick_rows
        ):
            raise sqlite3.DatabaseError("quick_check failed")
        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise sqlite3.DatabaseError("foreign_key_check failed")
        marker = connection.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()
        if marker is None or str(marker[0]) != "6":
            raise sqlite3.DatabaseError("schema_version is not current")
        actual_shape = _runtime_schema_shape(connection)
        # R7 may add its optional execution-control table to this shared
        # runtime database; the local Store gate owns only the R1 shape.
        actual_shape["tables"].pop("r7_execution_control", None)
        if actual_shape != _CURRENT_RUNTIME_SCHEMA_SHAPE:
            raise sqlite3.DatabaseError("runtime schema shape is not current")
    except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
        raise StoreError("unsupported schema") from exc
    finally:
        if connection is not None:
            connection.close()


class Store:
    """SQLite authoritative store for the R1 POC.

    All mutating public methods execute exactly one explicit transaction
    (BEGIN IMMEDIATE ... COMMIT/ROLLBACK) and append audit events inside it.
    """

    def __init__(self, db_path: Path, artifact_dir: Path) -> None:
        self.db_path = Path(db_path)
        _assert_current_schema(self.db_path)
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), isolation_level=None)
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA busy_timeout=10000")
        self._conn.executescript(_SCHEMA)
        work_unit_columns = {
            row[1] for row in self._conn.execute("PRAGMA table_info(work_unit_runs)")
        }
        if "begin_hash" not in work_unit_columns:
            self._conn.execute(
                "ALTER TABLE work_unit_runs ADD COLUMN begin_hash TEXT NOT NULL DEFAULT ''"
            )
        capability_binding_columns = {
            row[1] for row in self._conn.execute(
                "PRAGMA table_info(work_unit_capability_attempts)"
            )
        }
        if "detail" not in capability_binding_columns:
            self._conn.execute(
                "ALTER TABLE work_unit_capability_attempts"
                " ADD COLUMN detail TEXT NOT NULL DEFAULT ''"
            )
        node_attempt_columns = {
            row[1] for row in self._conn.execute("PRAGMA table_info(node_attempts)")
        }
        if "manifest_revision" not in node_attempt_columns:
            self._conn.execute(
                "ALTER TABLE node_attempts ADD COLUMN manifest_revision INTEGER NOT NULL DEFAULT 0"
            )
            for run_id, node_id, attempt_seq, created_at in self._conn.execute(
                "SELECT run_id, node_id, attempt_seq, created_at FROM node_attempts"
            ).fetchall():
                revision = self._manifest_revision_at(run_id, created_at)
                self._conn.execute(
                    "UPDATE node_attempts SET manifest_revision=?"
                    " WHERE run_id=? AND node_id=? AND attempt_seq=?",
                    (revision, run_id, node_id, int(attempt_seq)),
                )
        node_run_columns = {
            row[1] for row in self._conn.execute("PRAGMA table_info(node_runs)")
        }
        if "manifest_revision" not in node_run_columns:
            self._conn.execute(
                "ALTER TABLE node_runs ADD COLUMN manifest_revision INTEGER NOT NULL DEFAULT 0"
            )
            for run_id, node_id, started_at in self._conn.execute(
                "SELECT run_id, node_id, started_at FROM node_runs"
            ).fetchall():
                latest = self._conn.execute(
                    "SELECT manifest_revision FROM node_attempts WHERE run_id=?"
                    " AND node_id=? ORDER BY attempt_seq DESC LIMIT 1",
                    (run_id, node_id),
                ).fetchone()
                revision = (
                    int(latest[0]) if latest is not None
                    else self._manifest_revision_at(run_id, started_at or "")
                )
                self._conn.execute(
                    "UPDATE node_runs SET manifest_revision=?"
                    " WHERE run_id=? AND node_id=?",
                    (revision, run_id, node_id),
                )
        self._conn.execute(
            "INSERT OR IGNORE INTO audit_chain_head(singleton, last_seq, last_chain_hash)"
            " VALUES (1, 0, ?)",
            (AUDIT_GENESIS,),
        )
        self._migrate_authoritative_progress_v4()
        self._conn.execute(
            "INSERT INTO meta(key, value) VALUES('schema_version', '6')"
            " ON CONFLICT(key) DO UPDATE SET value=excluded.value"
        )
        self._conn.execute(
            "INSERT OR IGNORE INTO meta(key, value) VALUES('store_id', ?)",
            (new_id(),),
        )

    # ------------------------------------------------------------------ utils

    def _manifest_revision_at(self, run_id: str, observed_at: str) -> int:
        """Resolve a pre-v5 node timestamp to the manifest then in force."""

        if not observed_at:
            return 0
        row = self._conn.execute(
            "SELECT revision FROM run_manifests WHERE run_id=? AND created_at<=?"
            " ORDER BY revision DESC LIMIT 1",
            (run_id, observed_at),
        ).fetchone()
        return int(row[0]) if row is not None else 0

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _txn(self, fn: Any) -> Any:
        """Run fn() in one explicit transaction (closures use self._conn)."""
        conn = self._conn
        conn.execute("BEGIN IMMEDIATE")
        try:
            result = fn()
            conn.execute("COMMIT")
            return result
        except BaseException:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise

    # ------------------------------------------------------------ audit chain

    def _migrate_authoritative_progress_v4(self) -> None:
        """Backfill v4 anchors/legacy denominators for pre-v4 POC stores.

        A pre-v4 store had no durable audit tail anchor and no revisioned
        node-level denominator.  Migration trusts the already-present tail
        once, then every subsequent append and verification is anchored.
        Legacy node progress is reconstructed from manifest/node audit events;
        the live node row is only a fallback when no transition event exists.
        """

        head = self._conn.execute(
            "SELECT last_seq, last_chain_hash FROM audit_chain_head WHERE singleton=1"
        ).fetchone()
        last = self._conn.execute(
            "SELECT seq, chain_hash FROM audit_events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        if head == (0, AUDIT_GENESIS) and last is not None:
            self._conn.execute(
                "UPDATE audit_chain_head SET last_seq=?, last_chain_hash=? WHERE singleton=1",
                (int(last[0]), last[1]),
            )

        had_node_progress = bool(self._conn.execute(
            "SELECT 1 FROM manifest_node_progress LIMIT 1"
        ).fetchone())
        current_revisions = {
            row[0]: int(row[1])
            for row in self._conn.execute(
                "SELECT run_id, manifest_revision FROM monitoring_runs"
            ).fetchall()
        }
        for run_id, revision, manifest_json, created_at in self._conn.execute(
            "SELECT run_id, revision, manifest_json, created_at FROM run_manifests"
        ).fetchall():
            manifest = from_jsonable(ExecutionManifest, json.loads(manifest_json))
            if manifest.work_units:
                continue
            live_status = {}
            if int(revision) == current_revisions.get(run_id):
                live_status = {
                    row[0]: row[1]
                    for row in self._conn.execute(
                        "SELECT node_id, status FROM node_runs WHERE run_id=?"
                        " AND manifest_revision=?",
                        (run_id, int(revision)),
                    ).fetchall()
                }
            for node in manifest.nodes:
                self._conn.execute(
                    "INSERT OR IGNORE INTO manifest_node_progress("
                    "run_id, manifest_revision, node_id, status, updated_at)"
                    " VALUES (?,?,?,?,?)",
                    (run_id, int(revision), node.node_id,
                     live_status.get(node.node_id, NodeStatus.PENDING.value), created_at),
                )
        if had_node_progress:
            return

        active_revision: Dict[str, int] = {}
        reconstructed: Dict[Tuple[str, int, str], str] = {}
        for run_id, event_type, payload_json in self._conn.execute(
            "SELECT run_id, event_type, payload_json FROM audit_events"
            " WHERE run_id IS NOT NULL AND event_type IN (?,?,?) ORDER BY seq",
            (domain.EVENT_MANIFEST_SET, domain.EVENT_NODE_BEGIN,
             domain.EVENT_NODE_COMPLETE),
        ).fetchall():
            payload = json.loads(payload_json)
            if event_type == domain.EVENT_MANIFEST_SET:
                try:
                    active_revision[run_id] = int(payload["revision"])
                except (KeyError, TypeError, ValueError):
                    continue
                continue
            try:
                revision = int(
                    payload.get("manifest_revision", active_revision.get(run_id, 0))
                )
            except (TypeError, ValueError):
                continue
            node_id = payload.get("node_id")
            if revision < 1 or not isinstance(node_id, str):
                continue
            if event_type == domain.EVENT_NODE_BEGIN:
                status = NodeStatus.RUNNING.value
            else:
                status = payload.get("status")
                try:
                    NodeStatus(str(status))
                except ValueError:
                    continue
            reconstructed[(run_id, revision, node_id)] = str(status)
        for (run_id, revision, node_id), status in reconstructed.items():
            self._conn.execute(
                "UPDATE manifest_node_progress SET status=?, updated_at=?"
                " WHERE run_id=? AND manifest_revision=? AND node_id=?",
                (status, now_iso(), run_id, revision, node_id),
            )

    def _append_audit_row(self, conn: sqlite3.Connection, event_type: str,
                          payload: Mapping[str, Any], run_id: Optional[str] = None) -> AuditEvent:
        if not event_type or not isinstance(event_type, str):
            raise StoreError("audit event_type must be a non-empty string")
        created = now_iso()
        payload_json = canonical_json(to_jsonable(dict(payload)))
        payload_hash = sha256_hex(payload_json.encode("utf-8"))
        head = conn.execute(
            "SELECT last_seq, last_chain_hash FROM audit_chain_head WHERE singleton=1"
        ).fetchone()
        if head is None:
            raise StoreError("audit chain head is missing")
        last = conn.execute(
            "SELECT seq, chain_hash FROM audit_events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        actual = (0, AUDIT_GENESIS) if last is None else (int(last[0]), last[1])
        anchored = (int(head[0]), head[1])
        if actual != anchored:
            raise StoreError("audit chain tail does not match its durable head")
        seq, prev = anchored[0] + 1, anchored[1]
        chain_hash = sha256_hex(canonical_json({
            "seq": seq, "event_type": event_type, "payload_hash": payload_hash,
            "prev_hash": prev, "created_at": created,
        }).encode("utf-8"))
        conn.execute(
            "INSERT INTO audit_events(seq, run_id, event_type, payload_json, payload_hash,"
            " prev_hash, chain_hash, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (seq, run_id, event_type, payload_json, payload_hash, prev, chain_hash, created),
        )
        conn.execute(
            "UPDATE audit_chain_head SET last_seq=?, last_chain_hash=? WHERE singleton=1",
            (seq, chain_hash),
        )
        return AuditEvent(seq=seq, event_type=event_type, payload=dict(payload),
                          payload_hash=payload_hash, prev_hash=prev, chain_hash=chain_hash,
                          run_id=run_id, created_at=created)

    def append_audit(self, event_type: str, payload: Mapping[str, Any],
                     run_id: Optional[str] = None) -> AuditEvent:
        """Public audit append (own transaction)."""
        if event_type in _RESERVED_INTERNAL_AUDIT_EVENTS:
            raise StoreError(
                f"audit event {event_type!r} is reserved for authoritative work-unit transitions"
            )
        return self._txn(lambda: self._append_audit_row(self._conn, event_type, payload, run_id))

    def verify_audit_chain(self) -> Tuple[bool, Optional[int], int]:
        """Recompute the hash chain AND payload hashes.

        Returns (ok, first_bad_seq|None, count).  Detects modification,
        insertion, deletion (gap) and reordering of audit rows.
        """
        rows = self._conn.execute(
            "SELECT seq, event_type, payload_json, payload_hash, prev_hash, chain_hash,"
            " created_at FROM audit_events ORDER BY seq"
        ).fetchall()
        expected_prev = AUDIT_GENESIS
        for i, r in enumerate(rows, start=1):
            seq, etype, payload_json, ph, prev, chain, created = r
            if seq != i:
                return False, seq, len(rows)
            if prev != expected_prev:
                return False, seq, len(rows)
            if sha256_hex(payload_json.encode("utf-8")) != ph:
                return False, seq, len(rows)
            expected = sha256_hex(canonical_json({
                "seq": seq, "event_type": etype, "payload_hash": ph,
                "prev_hash": prev, "created_at": created,
            }).encode("utf-8"))
            if chain != expected:
                return False, seq, len(rows)
            expected_prev = chain
        head = self._conn.execute(
            "SELECT last_seq, last_chain_hash FROM audit_chain_head WHERE singleton=1"
        ).fetchone()
        if head is None:
            return False, len(rows) + 1, len(rows)
        if int(head[0]) != len(rows) or head[1] != expected_prev:
            return False, min(len(rows) + 1, max(1, int(head[0]))), len(rows)
        return True, None, len(rows)

    def audit_trail(self, limit: Optional[int] = None) -> List[AuditEvent]:
        sql = "SELECT * FROM audit_events ORDER BY seq"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        out = []
        for r in self._conn.execute(sql):
            out.append(AuditEvent(seq=r[0], run_id=r[1], event_type=r[2],
                                  payload=json.loads(r[3]), payload_hash=r[4],
                                  prev_hash=r[5], chain_hash=r[6], created_at=r[7]))
        return out

    # --------------------------------------------------------- idempotency

    def _run_idempotent(self, key: str, scope: str, request_hash: str, fn: Any) -> Any:
        """Idempotent execution guarded by (key, scope, request_hash).

        Same key + same scope + same request hash -> replay of the stored
        result (no side effects).  Same key with a different scope OR a
        different request -> IdempotencyConflictError (never silently return
        an unrelated prior result).  ``request_hash`` is the canonical content
        hash of the operation's request payload.
        """
        if not key:
            raise StoreError("idempotency key is required")

        def _work() -> Any:
            row = self._conn.execute(
                "SELECT scope, request_hash, result_json FROM idempotency_ledger"
                " WHERE idempotency_key=?", (key,)
            ).fetchone()
            if row is not None:
                stored_scope, stored_hash, result_json = row
                if stored_scope != scope or stored_hash != request_hash:
                    raise _IdempotencyLedgerConflict({
                        "idempotency_key": key,
                        "scope": scope,
                        "request_hash": request_hash,
                        "stored_scope": stored_scope,
                        "stored_request_hash": stored_hash,
                    })
                self._append_audit_row(
                    self._conn, domain.EVENT_IDEMPOTENT_REPLAY,
                    {"idempotency_key": key, "scope": scope}, None,
                )
                return json.loads(result_json)
            result = fn()
            self._conn.execute(
                "INSERT INTO idempotency_ledger(idempotency_key, scope, request_hash,"
                " result_json, created_at) VALUES (?,?,?,?,?)",
                (key, scope, request_hash, canonical_json(to_jsonable(result)), now_iso()),
            )
            return result

        try:
            return self._txn(_work)
        except _IdempotencyLedgerConflict as conflict:
            self.append_audit(domain.EVENT_IDEMPOTENCY_CONFLICT, conflict.payload, None)
            raise IdempotencyConflictError(
                f"idempotency key {key!r} reused with a different scope/request "
                f"(scope {scope!r}, request {request_hash[:12]}...)"
            ) from None

    # ------------------------------------------------------------- projects

    def create_project(self, project_id: str, name: str,
                       config: Optional[Mapping[str, Any]] = None,
                       is_synthetic: bool = True) -> StudyProject:
        """Create a project. POC guard: only SYNTHETIC fixtures are allowed."""
        if not is_synthetic:
            raise StoreError("POC guard: only synthetic projects are allowed")
        existing = self._conn.execute(
            "SELECT project_id FROM projects WHERE project_id=?", (project_id,)
        ).fetchone()
        if existing is not None:
            return self.get_project(project_id)
        created = now_iso()
        proj = StudyProject(project_id=project_id, name=name, is_synthetic=True,
                            created_at=created, config=dict(config or {}))

        def _work() -> StudyProject:
            self._conn.execute(
                "INSERT INTO projects(project_id, name, is_synthetic, config_json, created_at)"
                " VALUES (?,?,?,?,?)",
                (project_id, name, 1, canonical_json(to_jsonable(proj.config)), created),
            )
            self._append_audit_row(self._conn, domain.EVENT_PROJECT_CREATED,
                                   {"project_id": project_id, "name": name}, None)
            return proj

        return self._txn(_work)

    def get_project(self, project_id: str) -> StudyProject:
        r = self._conn.execute(
            "SELECT project_id, name, is_synthetic, config_json, created_at"
            " FROM projects WHERE project_id=?", (project_id,)
        ).fetchone()
        if r is None:
            raise StoreError(f"project not found: {project_id}")
        return StudyProject(project_id=r[0], name=r[1], is_synthetic=bool(r[2]),
                            config=json.loads(r[3]), created_at=r[4])

    # ------------------------------------------------------ source revisions

    def add_source_revision(self, revision: SourceRevision) -> SourceRevision:
        """Idempotent by revision_id; the revision must belong to an existing
        project and must never be reused across projects (fail closed)."""
        self.get_project(revision.project_id)
        existing = self._conn.execute(
            "SELECT revision_id, project_id FROM source_revisions WHERE revision_id=?",
            (revision.revision_id,),
        ).fetchone()
        if existing is not None:
            if existing[1] != revision.project_id:
                raise IdempotencyConflictError(
                    f"revision id {revision.revision_id!r} reused across projects "
                    f"({existing[1]} -> {revision.project_id})"
                )
            return self.get_source_revision(revision.revision_id)
        created = revision.created_at or now_iso()
        rev = SourceRevision(**{**to_jsonable(revision), "created_at": created})

        def _work() -> SourceRevision:
            self._conn.execute(
                "INSERT INTO source_revisions(revision_id, project_id, source_type, version,"
                " content_hash, valid_from, scope_json, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (rev.revision_id, rev.project_id, rev.source_type, rev.version,
                 rev.content_hash, rev.valid_from,
                 canonical_json(to_jsonable(rev.scope)), created),
            )
            self._append_audit_row(self._conn, domain.EVENT_SOURCE_ADDED,
                                   {"revision_id": rev.revision_id, "project_id": rev.project_id,
                                    "source_type": rev.source_type, "version": rev.version,
                                    "content_hash": rev.content_hash}, None)
            return rev

        return self._txn(_work)

    def get_source_revision(self, revision_id: str) -> SourceRevision:
        r = self._conn.execute(
            "SELECT * FROM source_revisions WHERE revision_id=?", (revision_id,)
        ).fetchone()
        if r is None:
            raise StoreError(f"source revision not found: {revision_id}")
        return SourceRevision(revision_id=r[0], project_id=r[1], source_type=r[2],
                              version=r[3], content_hash=r[4], valid_from=r[5],
                              scope=json.loads(r[6]), created_at=r[7])

    # ------------------------------------------------------ listing snapshots

    def add_listing_snapshot(self, snapshot: ListingSnapshot,
                             listing_data: Mapping[str, Sequence[Mapping[str, Any]]]) -> ListingSnapshot:
        """Persist a full-listing snapshot.

        Identity semantics (snapshot_id is the idempotency key; bytes may dedupe):
        * same snapshot_id + same content/metadata -> replay (returns existing);
        * same snapshot_id + different content/metadata -> IdempotencyConflictError;
        * different snapshot_id + identical bytes -> separate snapshot row, same
          content-addressed blob (never collapsed into one snapshot).

        ``listing_data`` must map table name -> list of row dicts.  Content hash
        is computed over the canonical JSON of the whole listing.
        """
        if not snapshot.is_synthetic:
            raise StoreError("POC guard: only synthetic snapshots are allowed")
        self.get_project(snapshot.project_id)
        rev = self.get_source_revision(snapshot.revision_id)
        if rev.project_id != snapshot.project_id:
            raise StoreError(
                f"snapshot {snapshot.snapshot_id} references revision {snapshot.revision_id} "
                f"of project {rev.project_id}, not {snapshot.project_id}"
            )
        for table, rows in listing_data.items():
            if not isinstance(rows, (list, tuple)):
                raise StoreError(f"listing table '{table}' must be a list of rows")
        listing_hash = content_hash(to_jsonable(listing_data))
        existing = self._conn.execute(
            "SELECT content_hash, project_id, revision_id, snapshot_version, structure_json"
            " FROM listing_snapshots WHERE snapshot_id=?", (snapshot.snapshot_id,),
        ).fetchone()
        if existing is not None:
            if (existing[0] == listing_hash
                    and existing[1] == snapshot.project_id
                    and existing[2] == snapshot.revision_id
                    and existing[3] == snapshot.snapshot_version
                    and json.loads(existing[4]) == dict(snapshot.structure)):
                return self.get_listing_snapshot(snapshot.snapshot_id)
            raise IdempotencyConflictError(
                f"snapshot id {snapshot.snapshot_id!r} replayed with different "
                "content/metadata"
            )
        self._write_content_file(listing_hash, to_jsonable(listing_data))
        created = snapshot.created_at or now_iso()
        row_count = sum(len(rows) for rows in listing_data.values())
        snap = ListingSnapshot(
            snapshot_id=snapshot.snapshot_id, project_id=snapshot.project_id,
            revision_id=snapshot.revision_id, snapshot_version=snapshot.snapshot_version,
            content_hash=listing_hash, row_count=row_count,
            structure=dict(snapshot.structure), is_synthetic=True, created_at=created,
        )

        def _work() -> ListingSnapshot:
            self._conn.execute(
                "INSERT INTO listing_snapshots(snapshot_id, project_id, revision_id,"
                " snapshot_version, content_hash, row_count, structure_json, is_synthetic,"
                " created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (snap.snapshot_id, snap.project_id, snap.revision_id, snap.snapshot_version,
                 snap.content_hash, snap.row_count,
                 canonical_json(to_jsonable(snap.structure)), 1, created),
            )
            self._conn.execute(
                "INSERT INTO snapshot_acceptance(snapshot_id, state, accepted_by, ambiguity_json,"
                " blocked, reason, updated_at) VALUES (?,?,NULL,NULL,0,'',?)",
                (snap.snapshot_id, SnapshotAcceptanceState.IMPORTED.value, created),
            )
            self._append_audit_row(self._conn, domain.EVENT_SNAPSHOT_ADDED,
                                   {"snapshot_id": snap.snapshot_id, "project_id": snap.project_id,
                                    "content_hash": snap.content_hash, "row_count": snap.row_count},
                                   None)
            return snap

        return self._txn(_work)

    def get_listing_snapshot(self, snapshot_id: str) -> ListingSnapshot:
        r = self._conn.execute(
            "SELECT * FROM listing_snapshots WHERE snapshot_id=?", (snapshot_id,)
        ).fetchone()
        if r is None:
            raise StoreError(f"listing snapshot not found: {snapshot_id}")
        return ListingSnapshot(snapshot_id=r[0], project_id=r[1], revision_id=r[2],
                               snapshot_version=r[3], content_hash=r[4], row_count=r[5],
                               structure=json.loads(r[6]), is_synthetic=bool(r[7]),
                               created_at=r[8])

    def load_listing_content(self, snapshot_id: str) -> Dict[str, List[Dict[str, Any]]]:
        snap = self.get_listing_snapshot(snapshot_id)
        path = self._content_path(snap.content_hash)
        if not path.exists():
            raise StoreError(f"listing content missing for snapshot {snapshot_id} ({snap.content_hash})")
        return json.loads(path.read_text("utf-8"))

    # --------------------------------------------------- snapshot acceptance

    def baseline_eligibility_proof(self, snapshot_id: str) -> domain.SnapshotBaselineProof:
        """Project the current Store acceptance row (not an authority token)."""
        return domain.SnapshotBaselineProof.from_acceptance(self.get_acceptance(snapshot_id))

    def get_acceptance(self, snapshot_id: str) -> SnapshotAcceptance:
        r = self._conn.execute(
            "SELECT snapshot_id, state, accepted_by, ambiguity_json, blocked, reason, updated_at"
            " FROM snapshot_acceptance WHERE snapshot_id=?", (snapshot_id,)
        ).fetchone()
        if r is None:
            raise StoreError(f"no acceptance record for snapshot: {snapshot_id}")
        return SnapshotAcceptance(snapshot_id=r[0],
                                  state=SnapshotAcceptanceState(r[1]), accepted_by=r[2],
                                  ambiguity=json.loads(r[3]) if r[3] else None,
                                  blocked=bool(r[4]), reason=r[5], updated_at=r[6])

    def transition_snapshot_acceptance(self, snapshot_id: str, to_state: SnapshotAcceptanceState,
                                       accepted_by: Optional[str] = None, reason: str = "",
                                       idempotency_key: Optional[str] = None) -> SnapshotAcceptance:
        """Strict one-step-forward chain.  Fail closed:
        * jumps/rewinds -> AcceptanceChainError;
        * any recorded ambiguity blocks SNAPSHOT_ACCEPTED / BASELINE_ELIGIBLE;
        * acceptance requires accepted_by == 'system_policy' or the OS user.
        """
        current = self.get_acceptance(snapshot_id)
        if current.state == to_state:
            return current
        chain = ACCEPTANCE_CHAIN
        try:
            cur_idx, new_idx = chain.index(current.state), chain.index(to_state)
        except ValueError:
            raise StoreError(f"unknown acceptance state: {to_state}")
        if new_idx != cur_idx + 1:
            raise AcceptanceChainError(
                f"illegal acceptance transition {current.state.value} -> {to_state.value}"
            )
        if to_state in (SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                        SnapshotAcceptanceState.BASELINE_ELIGIBLE):
            if current.ambiguity:
                raise AmbiguityBlocksAcceptanceError(
                    f"ambiguity blocks acceptance of snapshot {snapshot_id}: "
                    f"{canonical_json(current.ambiguity)}"
                )
            if not accepted_by:
                raise StoreError("accepted_by is required for acceptance transitions")
            if accepted_by != ACCEPTED_BY_SYSTEM_POLICY and accepted_by != getpass.getuser():
                raise StoreError(f"invalid acceptance subject: {accepted_by!r}")

        def _work() -> SnapshotAcceptance:
            updated = now_iso()
            self._conn.execute(
                "UPDATE snapshot_acceptance SET state=?, accepted_by=?, blocked=0, reason=?,"
                " updated_at=? WHERE snapshot_id=?",
                (to_state.value, accepted_by, reason, updated, snapshot_id),
            )
            self._append_audit_row(self._conn, domain.EVENT_ACCEPTANCE_TRANSITION,
                                   {"snapshot_id": snapshot_id, "from": current.state.value,
                                    "to": to_state.value, "accepted_by": accepted_by,
                                    "reason": reason}, None)
            return SnapshotAcceptance(snapshot_id=snapshot_id, state=to_state,
                                      accepted_by=accepted_by, ambiguity=None,
                                      blocked=False, reason=reason, updated_at=updated)

        return self._txn(_work)

    def set_acceptance_ambiguity(self, snapshot_id: str, ambiguity: Mapping[str, Any],
                                 reason: str = "") -> SnapshotAcceptance:
        """Record identity/mapping/source-scope ambiguity; blocks acceptance."""
        current = self.get_acceptance(snapshot_id)
        if current.state in (SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                            SnapshotAcceptanceState.BASELINE_ELIGIBLE):
            raise StoreError("cannot flag ambiguity on an already accepted snapshot")
        amb = dict(ambiguity)

        def _work() -> SnapshotAcceptance:
            updated = now_iso()
            self._conn.execute(
                "UPDATE snapshot_acceptance SET ambiguity_json=?, blocked=1, reason=?,"
                " updated_at=? WHERE snapshot_id=?",
                (canonical_json(to_jsonable(amb)), reason or "ambiguity recorded", updated, snapshot_id),
            )
            self._append_audit_row(self._conn, domain.EVENT_ACCEPTANCE_AMBIGUITY_SET,
                                   {"snapshot_id": snapshot_id, "ambiguity": amb, "reason": reason},
                                   None)
            return SnapshotAcceptance(snapshot_id=snapshot_id, state=current.state,
                                      accepted_by=current.accepted_by, ambiguity=amb,
                                      blocked=True, reason=reason, updated_at=updated)

        return self._txn(_work)

    def clear_acceptance_ambiguity(self, snapshot_id: str, accepted_by: str,
                                   reason: str = "") -> SnapshotAcceptance:
        """Clear a recorded ambiguity so acceptance can proceed."""
        if accepted_by != ACCEPTED_BY_SYSTEM_POLICY and accepted_by != getpass.getuser():
            raise StoreError(f"invalid acceptance subject: {accepted_by!r}")
        current = self.get_acceptance(snapshot_id)

        def _work() -> SnapshotAcceptance:
            updated = now_iso()
            self._conn.execute(
                "UPDATE snapshot_acceptance SET ambiguity_json=NULL, blocked=0, reason=?,"
                " updated_at=? WHERE snapshot_id=?",
                (reason or "ambiguity cleared", updated, snapshot_id),
            )
            self._append_audit_row(self._conn, domain.EVENT_ACCEPTANCE_AMBIGUITY_CLEARED,
                                   {"snapshot_id": snapshot_id, "accepted_by": accepted_by,
                                    "reason": reason}, None)
            return SnapshotAcceptance(snapshot_id=snapshot_id, state=current.state,
                                      accepted_by=accepted_by, ambiguity=None,
                                      blocked=False, reason=reason, updated_at=updated)

        return self._txn(_work)

    # ----------------------------------------------------------- runs & state

    def create_run(self, run: MonitoringRun) -> MonitoringRun:
        """Create a monitoring run; idempotent by run_id.  States start fail-closed
        (not_started / not_evaluable / not_required / not_published).  The source
        revision must exist and belong to the same project."""
        self.get_project(run.project_id)
        if run.source_revision_id:
            rev = self.get_source_revision(run.source_revision_id)
            if rev.project_id != run.project_id:
                raise StoreError(
                    f"run {run.run_id} references revision {run.source_revision_id} "
                    f"of project {rev.project_id}, not {run.project_id}"
                )
        existing = self._conn.execute(
            "SELECT run_id FROM monitoring_runs WHERE run_id=?", (run.run_id,)
        ).fetchone()
        if existing is not None:
            return self.get_run(run.run_id)
        created = run.created_at or now_iso()
        r = MonitoringRun(run_id=run.run_id, project_id=run.project_id, mode=run.mode,
                          data_cutoff=run.data_cutoff, source_revision_id=run.source_revision_id,
                          execution_basis=run.execution_basis,
                          analysis_state=AnalysisState.NOT_STARTED,
                          evidence_state=domain.EvidenceState.NOT_EVALUABLE,
                          review_state=ReviewState.NOT_REQUIRED,
                          output_state=OutputState.NOT_PUBLISHED,
                          user_disposition=None, manifest_revision=0,
                          created_at=created, updated_at=created)

        def _work() -> MonitoringRun:
            self._conn.execute(
                "INSERT INTO monitoring_runs(run_id, project_id, mode, data_cutoff,"
                " source_revision_id, execution_basis, analysis_state, evidence_state,"
                " review_state, output_state, user_disposition, manifest_revision, created_at,"
                " updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r.run_id, r.project_id, r.mode.value, r.data_cutoff, r.source_revision_id,
                 r.execution_basis.value, r.analysis_state.value, r.evidence_state.value,
                 r.review_state.value, r.output_state.value, None, 0, created, created),
            )
            self._append_audit_row(self._conn, domain.EVENT_RUN_CREATED,
                                   {"run_id": r.run_id, "project_id": r.project_id,
                                    "mode": r.mode.value, "data_cutoff": r.data_cutoff,
                                    "source_revision_id": r.source_revision_id,
                                    "execution_basis": r.execution_basis.value}, r.run_id)
            return r

        return self._txn(_work)

    def get_run(self, run_id: str) -> MonitoringRun:
        r = self._conn.execute("SELECT * FROM monitoring_runs WHERE run_id=?", (run_id,)).fetchone()
        if r is None:
            raise StoreError(f"run not found: {run_id}")
        return MonitoringRun(
            run_id=r[0], project_id=r[1], mode=RunMode(r[2]), data_cutoff=r[3],
            source_revision_id=r[4], execution_basis=ExecutionBasis(r[5]),
            analysis_state=AnalysisState(r[6]), evidence_state=domain.EvidenceState(r[7]),
            review_state=ReviewState(r[8]), output_state=OutputState(r[9]),
            user_disposition=UserDisposition(r[10]) if r[10] else None,
            manifest_revision=r[11], created_at=r[12], updated_at=r[13],
        )

    def list_runs(self, project_id: Optional[str] = None) -> List[MonitoringRun]:
        if project_id:
            rows = self._conn.execute(
                "SELECT run_id FROM monitoring_runs WHERE project_id=? ORDER BY created_at",
                (project_id,),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT run_id FROM monitoring_runs ORDER BY created_at").fetchall()
        return [self.get_run(r[0]) for r in rows]

    def _apply_state_changes(self, conn: sqlite3.Connection, run_id: str,
                             changes: Mapping[str, Any]) -> None:
        """Validate and apply orthogonal state transitions (fail closed)."""
        row = conn.execute("SELECT * FROM monitoring_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise StoreError(f"run not found: {run_id}")
        cur = {
            "analysis_state": AnalysisState(row[6]),
            "evidence_state": domain.EvidenceState(row[7]),
            "review_state": ReviewState(row[8]),
            "output_state": OutputState(row[9]),
            "user_disposition": UserDisposition(row[10]) if row[10] else None,
        }
        if "analysis" in changes:
            new = AnalysisState(changes["analysis"])
            if new != cur["analysis_state"] and new not in _ANALYSIS_TRANSITIONS[cur["analysis_state"]]:
                raise StoreError(
                    f"illegal analysis transition {cur['analysis_state'].value} -> {new.value}"
                )
            cur["analysis_state"] = new
        if "evidence" in changes:
            cur["evidence_state"] = domain.EvidenceState(changes["evidence"])
        if "review" in changes:
            new = ReviewState(changes["review"])
            if new != cur["review_state"] and new not in _REVIEW_TRANSITIONS[cur["review_state"]]:
                raise StoreError(
                    f"illegal review transition {cur['review_state'].value} -> {new.value}"
                )
            cur["review_state"] = new
        if "output" in changes:
            new = OutputState(changes["output"])
            if _OUTPUT_ORDER.index(new) < _OUTPUT_ORDER.index(cur["output_state"]):
                raise StoreError(
                    f"illegal output regression {cur['output_state'].value} -> {new.value}"
                )
            cur["output_state"] = new
        if "user_disposition" in changes:
            cur["user_disposition"] = changes["user_disposition"]
        updated = now_iso()
        conn.execute(
            "UPDATE monitoring_runs SET analysis_state=?, evidence_state=?, review_state=?,"
            " output_state=?, user_disposition=?, updated_at=? WHERE run_id=?",
            (cur["analysis_state"].value, cur["evidence_state"].value, cur["review_state"].value,
             cur["output_state"].value,
             cur["user_disposition"].value if cur["user_disposition"] else None,
             updated, run_id),
        )

    def update_run_state(self, run_id: str, *, analysis: Optional[AnalysisState] = None,
                         evidence: Optional[domain.EvidenceState] = None,
                         review: Optional[ReviewState] = None,
                         output: Optional[OutputState] = None,
                         user_disposition: Optional[UserDisposition] = None,
                         reason: str = "", actor: Optional[str] = None) -> MonitoringRun:
        """Transition orthogonal run states; every change is audited.

        ``output_state=exported`` is rejected here; callers must use
        :meth:`publish` so actor checks and ``user_disposition=EXPORTED`` stay
        on one atomic path.
        """
        changes: Dict[str, Any] = {}
        if analysis is not None:
            changes["analysis"] = analysis
        if evidence is not None:
            changes["evidence"] = evidence
        if review is not None:
            changes["review"] = review
        if output is not None:
            changes["output"] = output
        if user_disposition is not None:
            if not actor:
                raise StoreError("user_disposition requires an actor (actual user action)")
            if actor != getpass.getuser():
                raise StoreError(f"invalid actor: {actor!r}")
            changes["user_disposition"] = user_disposition
        if not changes:
            return self.get_run(run_id)
        # Export is exclusively owned by Store.publish so actor validation and
        # user_disposition=EXPORTED stay atomic on one path.
        if output is not None and output == OutputState.EXPORTED:
            raise StoreError(
                "output_state=exported is only allowed via Store.publish(); "
                "update_run_state cannot export"
            )
        cur_run = self.get_run(run_id)
        # analysis_complete gate: analysis may only transition to COMPLETE
        # through the same artifact/coverage gate as Store.complete_analysis
        # (a manual state change must never bypass coverage).
        if (analysis is not None and analysis == AnalysisState.COMPLETE
                and cur_run.analysis_state != AnalysisState.COMPLETE):
            reasons = self._gate_reasons(cur_run)
            if reasons:
                raise CompletionGateError(reasons)
        # publication gate: advancing output beyond not_published requires
        # analysis+evidence complete AND a fresh mandatory-artifact integrity /
        # provenance / coverage / publishability check (same as Store.publish).
        # analysis_complete must not freeze a one-time pass that later tampering
        # can ride through.
        if output is not None and _OUTPUT_ORDER.index(output) > _OUTPUT_ORDER.index(OutputState.NOT_PUBLISHED):
            reasons = []
            if cur_run.analysis_state != AnalysisState.COMPLETE:
                reasons.append("analysis not complete")
            if cur_run.evidence_state != domain.EvidenceState.COMPLETE:
                reasons.append("evidence not complete")
            reasons.extend(self._gate_reasons(cur_run))
            # Deduplicate while preserving order (analysis/evidence may appear twice).
            reasons = list(dict.fromkeys(reasons))
            if reasons:
                raise CompletionGateError(reasons)

        def _work() -> MonitoringRun:
            self._apply_state_changes(self._conn, run_id, changes)
            self._append_audit_row(self._conn, domain.EVENT_RUN_STATE_CHANGED,
                                   {"run_id": run_id, "changes": {k: v.value for k, v in changes.items()},
                                    "reason": reason, "actor": actor}, run_id)
            return self.get_run(run_id)

        return self._txn(_work)

    def _gate_reasons(self, run: MonitoringRun) -> List[str]:
        reasons: List[str] = []
        if run.manifest_revision < 1:
            reasons.append("no execution manifest frozen for the run")
        if run.evidence_state != domain.EvidenceState.COMPLETE:
            reasons.append(f"evidence_state is '{run.evidence_state.value}', not 'complete'")
        nodes = self._conn.execute(
            "SELECT node_id, node_type, status, artifact_id FROM node_runs"
            " WHERE run_id=? AND manifest_revision=?",
            (run.run_id, run.manifest_revision),
        ).fetchall()
        manifest = self.get_manifest(run.run_id)
        mandatory = {n.node_id for n in manifest.nodes if n.mandatory} if manifest else set()
        mnode_by_id = {n.node_id: n for n in manifest.nodes} if manifest else {}
        by_id = {r[0]: r for r in nodes}
        for node_id in sorted(mandatory):
            nr = by_id.get(node_id)
            if nr is None:
                reasons.append(f"mandatory node '{node_id}' has no node run")
                continue
            status = NodeStatus(nr[2])
            if status in (NodeStatus.FAILED, NodeStatus.BLOCKED):
                reasons.append(f"mandatory node '{node_id}' is {nr[2]}")
            elif status not in TERMINAL_NODE_STATUSES:
                reasons.append(f"mandatory node '{node_id}' is not terminal ({nr[2]})")
            else:
                # Artifact gate (fail closed): every mandatory node that produces
                # an artifact must reference an existing, integrity-valid,
                # publishable envelope.  A state-only/QC node may have no
                # artifact only when the frozen manifest declares so.
                mnode = mnode_by_id.get(node_id)
                artifact_id = nr[3]
                if artifact_id is None and mnode is not None and mnode.artifact_required:
                    reasons.append(
                        f"mandatory node '{node_id}' produced no artifact "
                        "(manifest requires one)"
                    )
                if artifact_id is not None:
                    try:
                        env = self.get_artifact(artifact_id)
                    except StoreError:
                        reasons.append(
                            f"mandatory node '{node_id}' artifact {artifact_id} "
                            "is not committed"
                        )
                        continue
                    if env.run_id != run.run_id or env.node_id != node_id:
                        reasons.append(
                            f"mandatory node '{node_id}' artifact {artifact_id} "
                            "provenance mismatch"
                        )
                    if not self.verify_artifact(artifact_id):
                        reasons.append(
                            f"mandatory node '{node_id}' artifact {artifact_id} "
                            "failed integrity check"
                        )
                    ok, why = env.is_publishable()
                    if not ok:
                        reasons.append(
                            f"mandatory node '{node_id}' artifact not publishable: "
                            + "; ".join(why)
                        )
        return reasons

    def complete_analysis(self, run_id: str, reason: str = "") -> MonitoringRun:
        """analysis_complete gate: manifest frozen, evidence complete, no failed/
        blocked mandatory nodes.  On success advances analysis to COMPLETE and
        the publication pointer to DASHBOARD_VISIBLE in the same transaction."""
        run = self.get_run(run_id)
        if run.analysis_state == AnalysisState.COMPLETE:
            return run
        if run.analysis_state != AnalysisState.RUNNING:
            raise CompletionGateError(
                [f"analysis_state is '{run.analysis_state.value}', expected 'running'"]
            )
        reasons = self._gate_reasons(run)
        if reasons:
            raise CompletionGateError(reasons)

        def _work() -> MonitoringRun:
            self._apply_state_changes(self._conn, run_id, {
                "analysis": AnalysisState.COMPLETE,
                "output": OutputState.DASHBOARD_VISIBLE,
            })
            self._append_audit_row(self._conn, domain.EVENT_RUN_STATE_CHANGED,
                                   {"run_id": run_id, "changes": {"analysis_state": "complete",
                                                                  "output_state": "dashboard_visible"},
                                    "reason": reason}, run_id)
            self._append_audit_row(self._conn, domain.EVENT_PUBLISH_ADVANCED,
                                   {"run_id": run_id, "output_state": "dashboard_visible",
                                    "reason": reason}, run_id)
            return self.get_run(run_id)

        return self._txn(_work)

    def publish(self, run_id: str, target: OutputState, reason: str = "",
                actor: Optional[str] = None) -> MonitoringRun:
        """Advance the publication pointer with gates.

        ``DASHBOARD_VISIBLE`` and ``DRAFT_EXPORTABLE`` require analysis+evidence
        complete plus a fresh mandatory-artifact gate.  ``EXPORTED`` is only
        reachable through this method: it requires a prior exportable state, an
        OS-user actor, and atomically sets ``user_disposition=EXPORTED``.
        """
        run = self.get_run(run_id)
        cur_idx = _OUTPUT_ORDER.index(run.output_state)
        new_idx = _OUTPUT_ORDER.index(target)
        if new_idx < cur_idx:
            raise StoreError(f"output regression {run.output_state.value} -> {target.value}")
        if new_idx == cur_idx:
            return run
        reasons: List[str] = []
        if run.analysis_state != AnalysisState.COMPLETE:
            reasons.append("analysis not complete")
        if run.evidence_state != domain.EvidenceState.COMPLETE:
            reasons.append("evidence not complete")
        if target == OutputState.EXPORTED:
            if cur_idx < _OUTPUT_ORDER.index(OutputState.DRAFT_EXPORTABLE):
                reasons.append("export requires an exportable output state first")
            if not actor:
                reasons.append("export requires an actor (user action)")
            elif actor != getpass.getuser():
                reasons.append(f"invalid actor: {actor!r}")
        # Re-evaluate mandatory artifact integrity/provenance/coverage/publishability
        # on every output advance; analysis_complete is not a permanent waiver.
        reasons.extend(self._gate_reasons(run))
        reasons = list(dict.fromkeys(reasons))
        if reasons:
            raise CompletionGateError(reasons)

        def _work() -> MonitoringRun:
            self._apply_state_changes(self._conn, run_id, {"output": target})
            if target == OutputState.EXPORTED and actor:
                self._apply_state_changes(self._conn, run_id, {"user_disposition": UserDisposition.EXPORTED})
            self._append_audit_row(self._conn, domain.EVENT_PUBLISH_ADVANCED,
                                   {"run_id": run_id, "output_state": target.value,
                                    "reason": reason, "actor": actor}, run_id)
            return self.get_run(run_id)

        return self._txn(_work)

    # ------------------------------------------------------------- manifests

    @staticmethod
    def _validate_manifest_work_units(manifest: ExecutionManifest) -> None:
        """Validate the frozen denominator before it can become authoritative."""
        if not manifest.work_units:
            return
        node_ids = set(manifest.node_ids())
        unit_ids = [u.work_unit_id for u in manifest.work_units]
        if len(unit_ids) != len(set(unit_ids)):
            raise StoreError("manifest work unit ids must be unique")
        ordinals = [u.ordinal for u in manifest.work_units]
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in ordinals
        ):
            raise StoreError("manifest work unit ordinals must be positive integers")
        if len(ordinals) != len(set(ordinals)):
            raise StoreError("manifest work unit ordinals must be unique")
        covered_nodes = set()
        by_id = {u.work_unit_id: u for u in manifest.work_units}
        for unit in manifest.work_units:
            if unit.node_id not in node_ids:
                raise StoreError(
                    f"work unit {unit.work_unit_id!r} references unknown node {unit.node_id!r}"
                )
            covered_nodes.add(unit.node_id)
            for field_name in ("work_unit_id", "label", "stage", "scope", "target_ref"):
                value = getattr(unit, field_name)
                if not isinstance(value, str) or not value.strip():
                    raise StoreError(
                        f"work unit {unit.work_unit_id!r} requires non-empty {field_name}"
                    )
            if unit.work_unit_id in unit.depends_on:
                raise StoreError(f"work unit {unit.work_unit_id!r} cannot depend on itself")
            unknown = [dependency for dependency in unit.depends_on if dependency not in by_id]
            if unknown:
                raise StoreError(
                    f"work unit {unit.work_unit_id!r} has unknown dependencies: {unknown}"
                )
        uncovered = node_ids - covered_nodes
        if uncovered:
            raise StoreError(
                "explicit work-unit manifests must cover every node: "
                + ", ".join(sorted(uncovered))
            )

        visiting: set[str] = set()
        visited: set[str] = set()

        def _visit(unit_id: str) -> None:
            if unit_id in visited:
                return
            if unit_id in visiting:
                raise StoreError("manifest work unit dependencies contain a cycle")
            visiting.add(unit_id)
            for dependency in by_id[unit_id].depends_on:
                _visit(dependency)
            visiting.remove(unit_id)
            visited.add(unit_id)

        for unit_id in unit_ids:
            _visit(unit_id)

    @staticmethod
    def _denominator_hash(manifest: ExecutionManifest, revision: int) -> str:
        if manifest.work_units:
            units: Any = [
                to_jsonable(unit)
                for unit in sorted(manifest.work_units, key=lambda item: item.ordinal)
            ]
            kind = "work_unit"
        else:
            units = manifest.node_ids()
            kind = "legacy_node"
        return content_hash({
            "run_id": manifest.run_id,
            "manifest_revision": revision,
            "denominator_kind": kind,
            "units": units,
        })

    @staticmethod
    def _manifest_definition(manifest: ExecutionManifest) -> Dict[str, Any]:
        """Canonical manifest content excluding store-assigned revision metadata."""
        definition = to_jsonable(manifest)
        definition["revision"] = 0
        definition["created_at"] = ""
        return definition

    def set_manifest(self, manifest: ExecutionManifest, idempotency_key: Optional[str] = None) -> int:
        """Freeze a manifest revision.  Same content -> same revision (idempotent);
        changed content -> next revision (append-only).  Requires an existing run."""
        self.get_run(manifest.run_id)
        node_ids = [n.node_id for n in manifest.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise StoreError("manifest node ids must be unique")
        for n in manifest.nodes:
            if n.node_type not in NodeType:
                raise StoreError(f"invalid node_type: {n.node_type!r}")
        self._validate_manifest_work_units(manifest)
        manifest_definition = self._manifest_definition(manifest)
        request_hash = content_hash(manifest_definition)
        key = idempotency_key or f"manifest:{manifest.run_id}:{request_hash}"
        scope = f"manifest:{manifest.run_id}"

        def _work() -> int:
            row = self._conn.execute(
                "SELECT COALESCE(MAX(revision),0) FROM run_manifests WHERE run_id=?",
                (manifest.run_id,),
            ).fetchone()
            revision = int(row[0]) + 1
            created = now_iso()
            self._conn.execute(
                "INSERT INTO run_manifests(run_id, revision, manifest_json, created_at)"
                " VALUES (?,?,?,?)",
                (manifest.run_id, revision, canonical_json(manifest_definition), created),
            )
            for unit in sorted(manifest.work_units, key=lambda item: item.ordinal):
                self._conn.execute(
                    "INSERT INTO work_unit_runs(run_id, manifest_revision, work_unit_id,"
                    " node_id, status, updated_at) VALUES (?,?,?,?,?,?)",
                    (manifest.run_id, revision, unit.work_unit_id, unit.node_id,
                     NodeStatus.PENDING.value, created),
                )
            if not manifest.work_units:
                for node in manifest.nodes:
                    self._conn.execute(
                        "INSERT INTO manifest_node_progress("
                        "run_id, manifest_revision, node_id, status, updated_at)"
                        " VALUES (?,?,?,?,?)",
                        (manifest.run_id, revision, node.node_id,
                         NodeStatus.PENDING.value, created),
                    )
            self._conn.execute(
                "UPDATE monitoring_runs SET manifest_revision=?, updated_at=? WHERE run_id=?",
                (revision, created, manifest.run_id),
            )
            self._append_audit_row(self._conn, domain.EVENT_MANIFEST_SET,
                                   {"run_id": manifest.run_id, "revision": revision,
                                    "nodes": node_ids,
                                    "work_unit_count": len(manifest.work_units),
                                    "denominator_hash": self._denominator_hash(
                                        manifest, revision
                                    )}, manifest.run_id)
            return revision

        return self._run_idempotent(key, scope, request_hash, _work)

    def get_manifest(self, run_id: str, revision: Optional[int] = None) -> Optional[ExecutionManifest]:
        if revision is None:
            r = self._conn.execute(
                "SELECT revision, manifest_json FROM run_manifests WHERE run_id=?"
                " ORDER BY revision DESC LIMIT 1",
                (run_id,),
            ).fetchone()
        else:
            r = self._conn.execute(
                "SELECT revision, manifest_json FROM run_manifests WHERE run_id=? AND revision=?",
                (run_id, revision),
            ).fetchone()
        if r is None:
            return None
        manifest = from_jsonable(ExecutionManifest, json.loads(r[1]))
        manifest.revision = int(r[0])
        return manifest

    def list_manifest_revisions(self, run_id: str) -> List[int]:
        rows = self._conn.execute(
            "SELECT revision FROM run_manifests WHERE run_id=? ORDER BY revision", (run_id,)
        ).fetchall()
        return [r[0] for r in rows]

    def manifest_progress(
        self, run_id: str, manifest_revision: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Real progress denominator: completed/total against the frozen manifest."""
        manifest = self.get_manifest(run_id, manifest_revision)
        if manifest is None:
            if manifest_revision is not None:
                raise StoreError(
                    f"manifest revision not found: {run_id}/{manifest_revision}"
                )
            return {"completed": 0, "total": 0, "by_status": {}}
        if manifest.work_units:
            rows, _ = self._validated_work_unit_projection(manifest)
            by_status: Dict[str, int] = {}
            for row in rows:
                by_status[row.status.value] = by_status.get(row.status.value, 0) + 1
            completed = sum(
                count for status, count in by_status.items()
                if NodeStatus(status) in TERMINAL_NODE_STATUSES
            )
            return {
                "completed": completed,
                "total": manifest.total_units(),
                "by_status": by_status,
            }
        rows = self._conn.execute(
            "SELECT node_id, status FROM manifest_node_progress WHERE run_id=?"
            " AND manifest_revision=? ORDER BY node_id",
            (run_id, manifest.revision),
        ).fetchall()
        expected_ids = set(manifest.node_ids())
        actual_ids = {row[0] for row in rows}
        if len(rows) != manifest.total_units() or actual_ids != expected_ids:
            raise StoreError(
                "authoritative node ledger does not match the manifest denominator"
            )
        by_status: Dict[str, int] = {}
        for _, status in rows:
            try:
                NodeStatus(status)
            except ValueError as exc:
                raise StoreError(
                    "authoritative node ledger contains an invalid status"
                ) from exc
            by_status[status] = by_status.get(status, 0) + 1
        completed = sum(v for k, v in by_status.items() if NodeStatus(k) in TERMINAL_NODE_STATUSES)
        return {"completed": completed, "total": manifest.total_units(), "by_status": by_status}

    def _set_current_manifest_node_progress(
        self, run_id: str, node_id: str, status: NodeStatus,
    ) -> None:
        """Update the revision-bound node denominator when it is in use."""

        run = self.get_run(run_id)
        if run.manifest_revision < 1:
            return
        manifest = self.get_manifest(run_id, run.manifest_revision)
        if manifest is None or manifest.work_units or node_id not in manifest.node_ids():
            return
        changed = self._conn.execute(
            "UPDATE manifest_node_progress SET status=?, updated_at=?"
            " WHERE run_id=? AND manifest_revision=? AND node_id=?",
            (status.value, now_iso(), run_id, run.manifest_revision, node_id),
        ).rowcount
        if changed != 1:
            raise StoreError("authoritative node progress row is missing")

    @staticmethod
    def _normalize_work_unit_detail(detail: str) -> str:
        if not isinstance(detail, str) or not detail.strip():
            raise StoreError("work unit detail must be a non-empty audience-readable sentence")
        normalized = " ".join(detail.split())
        if len(normalized) > 300:
            raise StoreError("work unit detail exceeds 300 characters")
        return normalized

    @staticmethod
    def _normalize_work_unit_identity(
        identity: Optional[Mapping[str, Any]],
    ) -> Dict[str, str]:
        normalized: Dict[str, str] = {}
        for key, value in dict(identity or {}).items():
            if key not in _WORK_UNIT_IDENTITY_KEYS:
                raise StoreError(f"work unit execution identity key is not allowed: {key!r}")
            if not isinstance(value, str) or not value.strip() or len(value) > 200:
                raise StoreError(
                    f"work unit execution identity value is invalid for {key!r}"
                )
            normalized[key] = value.strip()
        return normalized

    def get_work_unit_run(
        self, run_id: str, manifest_revision: int, work_unit_id: str,
    ) -> Optional[WorkUnitRun]:
        row = self._conn.execute(
            "SELECT run_id, manifest_revision, work_unit_id, node_id, status,"
            " idempotency_key, begin_hash, detail, execution_identity_json, evidence_count,"
            " completion_hash, started_at, finished_at, updated_at"
            " FROM work_unit_runs WHERE run_id=? AND manifest_revision=?"
            " AND work_unit_id=?",
            (run_id, manifest_revision, work_unit_id),
        ).fetchone()
        if row is None:
            return None
        return WorkUnitRun(
            run_id=row[0], manifest_revision=int(row[1]), work_unit_id=row[2],
            node_id=row[3], status=NodeStatus(row[4]), idempotency_key=row[5],
            begin_hash=row[6], detail=row[7], execution_identity=json.loads(row[8]),
            evidence_count=int(row[9]), completion_hash=row[10],
            started_at=row[11] or "", finished_at=row[12] or "", updated_at=row[13],
        )

    def list_work_unit_runs(
        self, run_id: str, manifest_revision: Optional[int] = None,
    ) -> List[WorkUnitRun]:
        if manifest_revision is None:
            manifest_revision = self.get_run(run_id).manifest_revision
        rows = self._conn.execute(
            "SELECT work_unit_id FROM work_unit_runs WHERE run_id=?"
            " AND manifest_revision=? ORDER BY rowid",
            (run_id, manifest_revision),
        ).fetchall()
        return [
            self.get_work_unit_run(run_id, manifest_revision, row[0])
            for row in rows
        ]

    def _current_work_unit_manifest(
        self, run_id: str, work_unit_id: str, manifest_revision: Optional[int],
    ) -> Tuple[ExecutionManifest, ManifestWorkUnit]:
        run = self.get_run(run_id)
        revision = run.manifest_revision if manifest_revision is None else manifest_revision
        if revision != run.manifest_revision:
            raise StaleCallbackError(
                f"work unit callback revision {revision} is stale; current revision is "
                f"{run.manifest_revision}"
            )
        manifest = self.get_manifest(run_id, revision)
        if manifest is None or not manifest.work_units:
            raise StoreError("current manifest has no explicit work units")
        units = {unit.work_unit_id: unit for unit in manifest.work_units}
        if work_unit_id not in units:
            raise StoreError(f"work unit not found in current manifest: {work_unit_id}")
        return manifest, units[work_unit_id]

    @staticmethod
    def _manifest_node_type(manifest: ExecutionManifest, node_id: str) -> NodeType:
        for node in manifest.nodes:
            if node.node_id == node_id:
                return node.node_type
        raise StoreError(f"work unit node is missing from manifest: {node_id}")

    def _capability_work_unit_identity(
        self,
        manifest: ExecutionManifest,
        unit: ManifestWorkUnit,
        attempt_id: str,
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Resolve a work-unit identity only from the durable attempt journal."""

        if self._manifest_node_type(manifest, unit.node_id) != NodeType.AI_CANDIDATE:
            raise StoreError("capability attempts may bind only to AI candidate work units")
        attempt = self.get_capability_attempt(attempt_id)
        if attempt is None:
            raise StoreError("capability attempt does not exist")
        audit_ok, first_bad_seq, _ = self.verify_audit_chain()
        if not audit_ok:
            raise StoreError(
                f"capability attempt audit chain is invalid at sequence {first_bad_seq}"
            )
        self._validate_capability_result_envelope(attempt)
        if attempt["run_id"] != manifest.run_id \
                or attempt["node_id"] != unit.node_id \
                or int(attempt["manifest_revision"]) != manifest.revision:
            raise StaleCallbackError(
                "capability attempt run/node/manifest identity does not match the work unit"
            )
        params = attempt["request"].get("params")
        if not isinstance(params, Mapping):  # defensive; journal validation also checks this
            raise StoreError("capability attempt request params are invalid")
        binding = params.get("binding")
        declared = params.get("execution_identity")
        if not isinstance(binding, Mapping) or not isinstance(declared, Mapping):
            raise StoreError("capability attempt execution identity is invalid")
        expected_declared = {
            "profile_fingerprint": attempt["profile_fingerprint"],
            "binding_id": binding.get("binding_id"),
            "provider": binding.get("provider"),
            "model": binding.get("model"),
            "selector": binding.get("selector"),
            "adapter_version": binding.get("adapter_version"),
        }
        if dict(declared) != expected_declared:
            raise StoreError(
                "capability attempt execution identity does not match its frozen binding"
            )
        self._validate_capability_work_assignment(manifest, unit, attempt)
        identity: Dict[str, str] = {
            "provider": str(expected_declared["provider"] or ""),
            "model": str(expected_declared["model"] or ""),
            "adapter": str(expected_declared["adapter_version"] or ""),
            "profile_fingerprint": str(attempt["profile_fingerprint"]),
            "attempt_id": str(attempt["attempt_id"]),
        }
        if expected_declared["selector"]:
            identity["selector"] = str(expected_declared["selector"])
        return attempt, self._normalize_work_unit_identity(identity)

    def _validate_capability_work_assignment(
        self,
        manifest: ExecutionManifest,
        unit: ManifestWorkUnit,
        attempt: Mapping[str, Any],
    ) -> None:
        """Require the controller's immutable pre-dispatch assignment.

        The Store deliberately revalidates the assignment instead of trusting
        a caller-provided work-unit id.  This closes the process-local path in
        which a claimed journal entry could otherwise create audience-visible
        running progress without passing through controller registration.
        """

        attempt_id = str(attempt["attempt_id"])
        object_id = "capability-work-assignment:%s" % attempt_id
        row = self.get_domain_object(_CAPABILITY_ASSIGNMENT_KIND, object_id)
        if row is None:
            raise StoreError(
                "capability attempt has no pre-registered work assignment"
            )
        version, payload = row
        if version != 1 or not isinstance(payload, Mapping):
            raise StoreError("capability work assignment must remain immutable")
        expected_keys = {
            "schema_version", "attempt_id", "run_id", "manifest_revision",
            "work_unit_id", "node_id", "profile_fingerprint", "request_hash",
            "request", "running_detail", "passed_detail", "failed_detail",
            "blocked_detail",
        }
        if set(payload) != expected_keys \
                or payload.get("schema_version") != _CAPABILITY_ASSIGNMENT_SCHEMA:
            raise StoreError("capability work assignment shape is invalid")
        expected_identity = {
            "attempt_id": attempt_id,
            "run_id": manifest.run_id,
            "manifest_revision": manifest.revision,
            "work_unit_id": unit.work_unit_id,
            "node_id": unit.node_id,
            "profile_fingerprint": attempt["profile_fingerprint"],
            "request_hash": attempt["request_hash"],
        }
        actual_identity = {key: payload.get(key) for key in expected_identity}
        if actual_identity != expected_identity:
            if payload.get("attempt_id") == attempt_id:
                raise IdempotencyConflictError(
                    "capability attempt is assigned to another work unit or frozen request"
                )
            raise StoreError("capability work assignment identity is invalid")
        if payload.get("request") != attempt["request"] \
                or content_hash(payload["request"]) != attempt["request_hash"]:
            raise StoreError("capability work assignment request is invalid")
        text_keys = (
            "running_detail", "passed_detail", "failed_detail", "blocked_detail",
        )
        if any(
            not isinstance(payload.get(key), str) or not payload[key].strip()
            for key in text_keys
        ):
            raise StoreError("capability work assignment audience text is invalid")
        matching = [
            event for event in self.audit_trail()
            if event.event_type == domain.EVENT_DOMAIN_OBJECT_PUT
            and event.payload.get("kind") == _CAPABILITY_ASSIGNMENT_KIND
            and event.payload.get("object_id") == object_id
            and int(event.payload.get("version", 0)) == version
        ]
        if len(matching) != 1 \
                or matching[0].payload.get("run_id") != manifest.run_id \
                or matching[0].payload.get("content_hash") != content_hash(payload):
            raise StoreError("capability work assignment audit evidence is invalid")

    def _list_work_unit_capability_attempts(
        self, run_id: str, manifest_revision: int, work_unit_id: str,
    ) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT attempt_ordinal, attempt_id, detail, execution_identity_json, identity_hash,"
            " bound_at FROM work_unit_capability_attempts WHERE run_id=?"
            " AND manifest_revision=? AND work_unit_id=? ORDER BY attempt_ordinal",
            (run_id, manifest_revision, work_unit_id),
        ).fetchall()
        bindings: List[Dict[str, Any]] = []
        for ordinal, attempt_id, detail, identity_json, identity_hash, bound_at in rows:
            try:
                identity = json.loads(identity_json)
            except (TypeError, json.JSONDecodeError) as exc:
                raise StoreError("work-unit capability identity JSON is invalid") from exc
            if not isinstance(identity, Mapping) \
                    or self._normalize_work_unit_identity(identity) != identity \
                    or content_hash(identity) != identity_hash:
                raise StoreError("work-unit capability identity binding is invalid")
            bindings.append({
                "attempt_ordinal": int(ordinal),
                "attempt_id": attempt_id,
                "detail": detail,
                "execution_identity": dict(identity),
                "identity_hash": identity_hash,
                "bound_at": bound_at,
            })
        return bindings

    def begin_work_unit(
        self, run_id: str, work_unit_id: str, idempotency_key: str, detail: str,
        execution_identity: Optional[Mapping[str, Any]] = None,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Begin a non-AI work unit; AI identity must come from its attempt journal."""

        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        if self._manifest_node_type(manifest, unit.node_id) == NodeType.AI_CANDIDATE:
            raise StoreError(
                "AI work units must begin through bind_capability_attempt_to_work_unit"
            )
        return self._begin_work_unit_direct(
            run_id, work_unit_id, idempotency_key, detail,
            execution_identity, manifest_revision,
        )

    def _begin_work_unit_direct(
        self, run_id: str, work_unit_id: str, idempotency_key: str, detail: str,
        execution_identity: Optional[Mapping[str, Any]] = None,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Atomically move a current-revision work unit from pending to running."""
        if not idempotency_key:
            raise StoreError("work unit idempotency key is required")
        detail = self._normalize_work_unit_detail(detail)
        identity = self._normalize_work_unit_identity(execution_identity)
        begin_hash = content_hash({"detail": detail, "execution_identity": identity})
        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        revision = manifest.revision

        def _work() -> WorkUnitRun:
            current_revision = self._conn.execute(
                "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            if int(current_revision) != revision:
                raise StaleCallbackError(
                    f"work unit callback revision {revision} became stale"
                )
            current = self.get_work_unit_run(run_id, revision, work_unit_id)
            if current is None:
                raise StoreError("authoritative work unit row is missing")
            if current.status == NodeStatus.RUNNING:
                if (current.idempotency_key == idempotency_key
                        and current.begin_hash == begin_hash):
                    return current
                raise IdempotencyConflictError(
                    f"work unit {work_unit_id!r} is already running with another request"
                )
            if current.status in TERMINAL_NODE_STATUSES:
                if (current.idempotency_key == idempotency_key
                        and current.begin_hash == begin_hash):
                    return current
                raise IdempotencyConflictError(
                    f"terminal work unit {work_unit_id!r} received a conflicting begin replay"
                )
            dependency_states: Dict[str, str] = {}
            for dependency in unit.depends_on:
                row = self._conn.execute(
                    "SELECT status FROM work_unit_runs WHERE run_id=?"
                    " AND manifest_revision=? AND work_unit_id=?",
                    (run_id, revision, dependency),
                ).fetchone()
                if row is None:
                    raise StoreError(f"dependency work unit row is missing: {dependency}")
                dependency_states[dependency] = row[0]
            unsatisfied = {
                key: value for key, value in dependency_states.items()
                if NodeStatus(value) not in domain.DEPENDENCY_SATISFYING_STATUSES
            }
            if unsatisfied:
                raise StoreError(
                    f"work unit dependencies are not satisfied: {unsatisfied}"
                )
            started = now_iso()
            self._conn.execute(
                "UPDATE work_unit_runs SET status=?, idempotency_key=?, begin_hash=?, detail=?,"
                " execution_identity_json=?, started_at=?, finished_at=NULL, updated_at=?"
                " WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
                (NodeStatus.RUNNING.value, idempotency_key, begin_hash, detail,
                 canonical_json(identity), started, started, run_id, revision, work_unit_id),
            )
            self._append_audit_row(
                self._conn, domain.EVENT_WORK_UNIT_BEGIN,
                {"run_id": run_id, "manifest_revision": revision,
                 "work_unit_id": work_unit_id, "node_id": unit.node_id,
                 "label": unit.label, "stage": unit.stage, "scope": unit.scope,
                 "target_ref": unit.target_ref, "status": NodeStatus.RUNNING.value,
                 "detail": detail, "execution_identity": identity,
                 "evidence_count": 0}, run_id,
            )
            return self.get_work_unit_run(run_id, revision, work_unit_id)

        return self._txn(_work)

    def bind_capability_attempt_to_work_unit(
        self,
        run_id: str,
        work_unit_id: str,
        attempt_id: str,
        detail: str,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Start or continue an AI work unit from one journaled attempt.

        The caller supplies only the durable attempt id and an audience-readable
        progress sentence. Provider/model/profile identity is re-derived from
        the immutable request journal. A later attempt may replace the current
        identity only through an exact ``continued_from`` chain.
        """

        if not attempt_id:
            raise StoreError("capability attempt_id is required")
        detail = self._normalize_work_unit_detail(detail)
        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        revision = manifest.revision
        stable_key = f"capability-work-unit:{run_id}:{revision}:{work_unit_id}"

        def _work() -> WorkUnitRun:
            current_revision = self._conn.execute(
                "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            if int(current_revision) != revision:
                raise StaleCallbackError(
                    f"work unit callback revision {revision} became stale"
                )
            # Re-resolve inside BEGIN IMMEDIATE so a manifest change or direct
            # journal corruption cannot slip between validation and binding.
            current_manifest, current_unit = self._current_work_unit_manifest(
                run_id, work_unit_id, revision
            )
            attempt, identity = self._capability_work_unit_identity(
                current_manifest, current_unit, attempt_id
            )
            if attempt["status"] == "declared":
                raise StoreError(
                    "capability attempt must be claimed before work-unit binding"
                )
            current = self.get_work_unit_run(run_id, revision, work_unit_id)
            if current is None:
                raise StoreError("authoritative work unit row is missing")
            bindings = self._list_work_unit_capability_attempts(
                run_id, revision, work_unit_id
            )
            existing_binding = next(
                (item for item in bindings if item["attempt_id"] == attempt_id), None
            )
            if existing_binding is not None:
                if existing_binding["detail"] != detail:
                    raise IdempotencyConflictError(
                        "capability attempt binding replay changed its progress detail"
                    )
                if bindings[-1]["attempt_id"] != attempt_id:
                    raise StaleCallbackError(
                        "an older capability attempt cannot replace the latest binding"
                    )
                return current
            used_elsewhere = self._conn.execute(
                "SELECT run_id, manifest_revision, work_unit_id"
                " FROM work_unit_capability_attempts WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
            if used_elsewhere is not None:
                raise IdempotencyConflictError(
                    "capability attempt is already bound to another work unit"
                )
            if not bindings:
                if current.status in TERMINAL_NODE_STATUSES:
                    raise StaleCallbackError(
                        "terminal work unit cannot accept a first capability binding"
                    )
                if attempt["continued_from"]:
                    raise StaleCallbackError(
                        "a continuation attempt cannot be the first work-unit binding"
                    )
                dependency_states: Dict[str, str] = {}
                for dependency in current_unit.depends_on:
                    row = self._conn.execute(
                        "SELECT status FROM work_unit_runs WHERE run_id=?"
                        " AND manifest_revision=? AND work_unit_id=?",
                        (run_id, revision, dependency),
                    ).fetchone()
                    if row is None:
                        raise StoreError(
                            f"dependency work unit row is missing: {dependency}"
                        )
                    dependency_states[dependency] = row[0]
                unsatisfied = {
                    key: value for key, value in dependency_states.items()
                    if NodeStatus(value) not in domain.DEPENDENCY_SATISFYING_STATUSES
                }
                if unsatisfied:
                    raise StoreError(
                        f"work unit dependencies are not satisfied: {unsatisfied}"
                    )
                if current.status != NodeStatus.PENDING:
                    raise StoreError(
                        "AI work unit has running state without a capability binding"
                    )
                ordinal = 1
                started = now_iso()
                begin_hash = content_hash({
                    "detail": detail, "execution_identity": identity,
                })
                self._conn.execute(
                    "INSERT INTO work_unit_capability_attempts("
                    " run_id, manifest_revision, work_unit_id, attempt_ordinal, attempt_id,"
                    " detail, execution_identity_json, identity_hash, bound_at)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        run_id, revision, work_unit_id, ordinal, attempt_id, detail,
                        canonical_json(identity), content_hash(identity), started,
                    ),
                )
                self._conn.execute(
                    "UPDATE work_unit_runs SET status=?, idempotency_key=?, begin_hash=?,"
                    " detail=?, execution_identity_json=?, started_at=?, finished_at=NULL,"
                    " updated_at=? WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
                    (
                        NodeStatus.RUNNING.value, stable_key, begin_hash, detail,
                        canonical_json(identity), started, started,
                        run_id, revision, work_unit_id,
                    ),
                )
                self._append_audit_row(
                    self._conn, domain.EVENT_WORK_UNIT_BEGIN,
                    {
                        "run_id": run_id, "manifest_revision": revision,
                        "work_unit_id": work_unit_id, "node_id": current_unit.node_id,
                        "label": current_unit.label, "stage": current_unit.stage,
                        "scope": current_unit.scope, "target_ref": current_unit.target_ref,
                        "status": NodeStatus.RUNNING.value, "detail": detail,
                        "execution_identity": identity, "evidence_count": 0,
                    },
                    run_id,
                )
                return self.get_work_unit_run(run_id, revision, work_unit_id)

            if current.status not in {
                NodeStatus.RUNNING, NodeStatus.FAILED, NodeStatus.BLOCKED,
            }:
                raise StoreError(
                    "capability retry requires a running, failed or blocked work unit"
                )
            previous_binding = bindings[-1]
            previous = self.get_capability_attempt(previous_binding["attempt_id"])
            if previous is None:  # pragma: no cover - FK plus prior validation
                raise StoreError("previous capability attempt is missing")
            self._validate_capability_result_envelope(previous)
            retryable_statuses = frozenset({
                "interrupted", "failed", "timeout", "cancelled", "partial", "truncated",
            })
            if previous["status"] not in retryable_statuses:
                raise StoreError(
                    "latest capability attempt is not in a retryable terminal/interrupted state"
                )
            if attempt["continued_from"] != previous["attempt_id"]:
                raise StaleCallbackError(
                    "capability continuation does not reference the latest bound attempt"
                )
            ordinal = len(bindings) + 1
            bound_at = now_iso()
            self._conn.execute(
                "INSERT INTO work_unit_capability_attempts("
                " run_id, manifest_revision, work_unit_id, attempt_ordinal, attempt_id,"
                " detail, execution_identity_json, identity_hash, bound_at)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    run_id, revision, work_unit_id, ordinal, attempt_id, detail,
                    canonical_json(identity), content_hash(identity), bound_at,
                ),
            )
            self._conn.execute(
                "UPDATE work_unit_runs SET status=?, detail=?, execution_identity_json=?,"
                " evidence_count=0, completion_hash='', finished_at=NULL, updated_at=?"
                " WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
                (
                    NodeStatus.RUNNING.value, detail, canonical_json(identity), bound_at,
                    run_id, revision, work_unit_id,
                ),
            )
            self._append_audit_row(
                self._conn, domain.EVENT_WORK_UNIT_ATTEMPT_BOUND,
                {
                    "run_id": run_id, "manifest_revision": revision,
                    "work_unit_id": work_unit_id, "node_id": current_unit.node_id,
                    "label": current_unit.label, "stage": current_unit.stage,
                    "scope": current_unit.scope, "target_ref": current_unit.target_ref,
                    "status": NodeStatus.RUNNING.value, "detail": detail,
                    "execution_identity": identity, "evidence_count": 0,
                    "attempt_ordinal": ordinal,
                    "continued_from": previous["attempt_id"],
                },
                run_id,
            )
            return self.get_work_unit_run(run_id, revision, work_unit_id)

        return self._txn(_work)

    def complete_work_unit(
        self, run_id: str, work_unit_id: str, idempotency_key: str,
        status: NodeStatus, detail: str, evidence_count: int = 0,
        execution_identity: Optional[Mapping[str, Any]] = None,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Complete a non-AI work unit through the direct deterministic path."""

        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        if self._manifest_node_type(manifest, unit.node_id) == NodeType.AI_CANDIDATE:
            raise StoreError(
                "AI work units must complete through complete_capability_work_unit"
            )
        return self._complete_work_unit_direct(
            run_id, work_unit_id, idempotency_key, status, detail,
            evidence_count, execution_identity, manifest_revision,
        )

    def _complete_work_unit_direct(
        self, run_id: str, work_unit_id: str, idempotency_key: str,
        status: NodeStatus, detail: str, evidence_count: int = 0,
        execution_identity: Optional[Mapping[str, Any]] = None,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Commit one immutable terminal work-unit outcome in the current revision."""
        if status not in TERMINAL_NODE_STATUSES:
            raise StoreError(f"work unit completion requires terminal status: {status.value}")
        if not idempotency_key:
            raise StoreError("work unit idempotency key is required")
        if isinstance(evidence_count, bool) or not isinstance(evidence_count, int) \
                or evidence_count < 0:
            raise StoreError("work unit evidence_count must be a non-negative integer")
        detail = self._normalize_work_unit_detail(detail)
        supplied_identity = (
            self._normalize_work_unit_identity(execution_identity)
            if execution_identity is not None else None
        )
        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        revision = manifest.revision

        def _work() -> WorkUnitRun:
            current_revision = self._conn.execute(
                "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            if int(current_revision) != revision:
                raise StaleCallbackError(
                    f"work unit callback revision {revision} became stale"
                )
            current = self.get_work_unit_run(run_id, revision, work_unit_id)
            if current is None:
                raise StoreError("authoritative work unit row is missing")
            identity = (
                current.execution_identity if supplied_identity is None else supplied_identity
            )
            if (supplied_identity is not None and current.execution_identity
                    and supplied_identity != current.execution_identity):
                raise IdempotencyConflictError(
                    f"work unit {work_unit_id!r} execution identity cannot change at completion"
                )
            fingerprint = content_hash({
                "status": status.value, "detail": detail,
                "execution_identity": identity, "evidence_count": evidence_count,
            })
            if current.status in TERMINAL_NODE_STATUSES:
                if (current.idempotency_key == idempotency_key
                        and current.completion_hash == fingerprint):
                    return current
                raise IdempotencyConflictError(
                    f"terminal work unit {work_unit_id!r} received a conflicting replay"
                )
            if current.status != NodeStatus.RUNNING:
                raise StaleCallbackError(
                    f"work unit {work_unit_id!r} was not started before completion"
                )
            if current.idempotency_key != idempotency_key:
                raise StaleCallbackError(
                    f"work unit {work_unit_id!r} completion key is stale"
                )
            finished = now_iso()
            self._conn.execute(
                "UPDATE work_unit_runs SET status=?, detail=?, execution_identity_json=?,"
                " evidence_count=?, completion_hash=?, finished_at=?, updated_at=?"
                " WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
                (status.value, detail, canonical_json(identity), evidence_count,
                 fingerprint, finished, finished, run_id, revision, work_unit_id),
            )
            self._append_audit_row(
                self._conn, domain.EVENT_WORK_UNIT_COMPLETE,
                {"run_id": run_id, "manifest_revision": revision,
                 "work_unit_id": work_unit_id, "node_id": unit.node_id,
                 "label": unit.label, "stage": unit.stage, "scope": unit.scope,
                 "target_ref": unit.target_ref, "status": status.value,
                 "detail": detail, "execution_identity": identity,
                 "evidence_count": evidence_count}, run_id,
            )
            return self.get_work_unit_run(run_id, revision, work_unit_id)

        return self._txn(_work)

    def _capability_persistence_evidence_count(
        self,
        attempt: Mapping[str, Any],
    ) -> int:
        """Verify the complete Store footprint produced by capability persistence.

        A terminal journal row proves execution, not persistence.  Audience
        progress may therefore close only after every object written by
        ``persist_capability_attempt`` is present, hash-verified and bound to
        the same frozen attempt.  No caller-supplied receipt or count is
        trusted.
        """

        if not attempt.get("terminal") or not isinstance(attempt.get("result"), Mapping):
            raise StoreError("terminal capability attempt has no persisted result envelope")
        result = attempt["result"]
        adapter_run = result.get("adapter_run")
        events = result.get("work_events")
        if not isinstance(adapter_run, Mapping) or not isinstance(events, list):
            raise StoreError("capability persistence result envelope is invalid")
        binding = adapter_run.get("binding")
        analysis = adapter_run.get("analysis")
        raw = adapter_run.get("raw_output")
        if not isinstance(binding, Mapping) \
                or not isinstance(analysis, Mapping) \
                or not isinstance(raw, Mapping):
            raise StoreError(
                "terminal capability attempt has no complete persisted evidence envelope"
            )

        def require_domain(kind: str, object_id: str, expected: Any) -> None:
            row = self.get_domain_object(kind, object_id, version=1)
            if row is None or row[1] != to_jsonable(expected):
                raise StoreError(
                    "capability attempt evidence is not fully persisted: %s" % kind
                )

        raw_ref = raw.get("raw_output_ref")
        if not isinstance(raw_ref, str) or not raw_ref:
            raise StoreError("terminal capability attempt raw evidence reference is invalid")
        require_domain("adapter_raw_output", "adapter-raw:%s" % raw_ref, raw)
        if not self.verify_adapter_raw_output(raw_ref):
            raise StoreError("terminal capability attempt raw evidence failed verification")

        params = attempt["request"].get("params")
        if not isinstance(params, Mapping):
            raise StoreError("capability attempt request params are invalid")
        binding_id = binding.get("binding_id")
        input_hash = binding.get("input_hash")
        if binding_id != params.get("binding", {}).get("binding_id") \
                or input_hash != attempt["input_hash"]:
            raise StoreError("persisted capability binding identity is invalid")
        require_domain(
            "adapter_binding",
            "adapter-binding:%s:%s" % (binding_id, input_hash or "unbound"),
            binding,
        )

        analysis_id = analysis.get("analysis_id")
        if not isinstance(analysis_id, str) or not analysis_id:
            raise StoreError("persisted capability analysis identity is invalid")
        require_domain(
            "adapter_analysis", "adapter-analysis:%s" % analysis_id, analysis
        )

        candidate = adapter_run.get("candidate_artifact")
        artifact_id = None
        artifact_count = 0
        if candidate is not None:
            if not isinstance(candidate, Mapping):
                raise StoreError("capability candidate artifact envelope is invalid")
            try:
                envelope = from_jsonable(ArtifactEnvelope, candidate)
                artifact_id = envelope.canonical_hash()
                committed = self.get_artifact(artifact_id)
            except (StoreError, TypeError, ValueError) as exc:
                raise StoreError(
                    "capability candidate artifact is not fully persisted"
                ) from exc
            if committed.content_dict() != envelope.content_dict() \
                    or committed.run_id != attempt["run_id"] \
                    or committed.node_id != attempt["node_id"] \
                    or committed.node_type != NodeType.AI_CANDIDATE \
                    or committed.payload_role != domain.PAYLOAD_ROLE_CANDIDATE \
                    or raw_ref not in committed.evidence_refs \
                    or not self.verify_artifact(artifact_id):
                raise StoreError("persisted capability candidate artifact is invalid")
            artifact_count = 1

        expected_run_snapshot = {
            "adapter_run_id": attempt["attempt_id"],
            "monitoring_run_id": adapter_run.get("monitoring_run_id", ""),
            "node_id": adapter_run.get("node_id", ""),
            "status": adapter_run.get("status"),
            "binding_id": binding_id,
            "input_hash": input_hash,
            "analysis_id": analysis_id,
            "raw_output_ref": raw_ref,
            "candidate_artifact_id": artifact_id,
            "failure_reason": adapter_run.get("failure_reason"),
            "independent": adapter_run.get("independent", True),
            "continued_from": adapter_run.get("continued_from"),
            "created_at": adapter_run.get("created_at", ""),
            "finished_at": adapter_run.get("finished_at", ""),
        }
        if expected_run_snapshot["monitoring_run_id"] != attempt["run_id"] \
                or expected_run_snapshot["node_id"] != attempt["node_id"] \
                or expected_run_snapshot["status"] != attempt["status"]:
            raise StoreError("persisted capability run snapshot identity is invalid")
        require_domain(
            "adapter_run", "adapter-run:%s" % attempt["attempt_id"],
            expected_run_snapshot,
        )

        profile_row = self.get_domain_object(
            "execution_profile",
            "execution-profile:%s" % attempt["profile_fingerprint"],
            version=1,
        )
        if profile_row is None \
                or content_hash(profile_row[1]) != attempt["profile_fingerprint"]:
            raise StoreError("capability execution profile is not fully persisted")
        expected_request = {
            "attempt_id": attempt["attempt_id"],
            "monitoring_run_id": attempt["run_id"],
            "node_id": attempt["node_id"],
            "manifest_revision": attempt["manifest_revision"],
            "profile_fingerprint": attempt["profile_fingerprint"],
            "binding_id": binding_id,
            "input_hash": attempt["input_hash"],
            "versions": params.get("versions", {}),
            "expected_units": params.get("expected_coverage", []),
            "continued_from": attempt.get("continued_from", ""),
            "request_hash": attempt["request_hash"],
        }
        require_domain(
            "adapter_attempt_request",
            "adapter-attempt-request:%s" % attempt["attempt_id"],
            expected_request,
        )
        for index, event in enumerate(events, start=1):
            if not isinstance(event, Mapping) \
                    or event.get("attempt_id") != attempt["attempt_id"] \
                    or event.get("sequence") != index:
                raise StoreError("capability work-event evidence is invalid")
            require_domain(
                "adapter_work_event",
                "adapter-work-event:%s:%03d" % (attempt["attempt_id"], index),
                event,
            )
        # profile + request, four adapter domain objects, work events, optional artifact
        return 2 + 4 + len(events) + artifact_count

    def complete_capability_work_unit(
        self,
        run_id: str,
        work_unit_id: str,
        attempt_id: str,
        detail: str,
        evidence_count: Optional[int] = None,
        manifest_revision: Optional[int] = None,
    ) -> WorkUnitRun:
        """Finish an AI work unit from the latest bound durable attempt.

        Capability ``complete`` is the only success path. Interrupted attempts
        become blocked; failed/timeout/cancelled/partial/truncated attempts
        become failed. Callers cannot supply or upgrade the status.
        """

        if not attempt_id:
            raise StoreError("capability attempt_id is required")
        if evidence_count is not None and (
            isinstance(evidence_count, bool)
            or not isinstance(evidence_count, int)
            or evidence_count < 0
        ):
            raise StoreError("work unit evidence_count must be a non-negative integer")
        detail = self._normalize_work_unit_detail(detail)
        manifest, unit = self._current_work_unit_manifest(
            run_id, work_unit_id, manifest_revision
        )
        revision = manifest.revision
        stable_key = f"capability-work-unit:{run_id}:{revision}:{work_unit_id}"

        def _work() -> WorkUnitRun:
            current_revision = self._conn.execute(
                "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            if int(current_revision) != revision:
                raise StaleCallbackError(
                    f"work unit callback revision {revision} became stale"
                )
            current_manifest, current_unit = self._current_work_unit_manifest(
                run_id, work_unit_id, revision
            )
            attempt, identity = self._capability_work_unit_identity(
                current_manifest, current_unit, attempt_id
            )
            bindings = self._list_work_unit_capability_attempts(
                run_id, revision, work_unit_id
            )
            if not bindings or bindings[-1]["attempt_id"] != attempt_id:
                raise StaleCallbackError(
                    "only the latest bound capability attempt may finish the work unit"
                )
            if attempt["status"] == "complete" and attempt["terminal"]:
                status = NodeStatus.PASSED
            elif attempt["status"] == "interrupted" and not attempt["terminal"]:
                status = NodeStatus.BLOCKED
            elif attempt["terminal"] and attempt["status"] in {
                "failed", "timeout", "cancelled", "partial", "truncated",
            }:
                status = NodeStatus.FAILED
            else:
                raise StoreError(
                    "capability attempt must be terminal or interrupted before work-unit completion"
                )
            if attempt["terminal"]:
                persisted_evidence_count = self._capability_persistence_evidence_count(
                    attempt
                )
                if evidence_count is not None \
                        and evidence_count != persisted_evidence_count:
                    raise StoreError(
                        "work unit evidence_count does not match persisted capability evidence"
                    )
                resolved_evidence_count = persisted_evidence_count
            else:
                if evidence_count not in (None, 0):
                    raise StoreError(
                        "interrupted capability attempt cannot claim persisted terminal evidence"
                    )
                resolved_evidence_count = 0
            current = self.get_work_unit_run(run_id, revision, work_unit_id)
            if current is None:
                raise StoreError("authoritative work unit row is missing")
            fingerprint = content_hash({
                "status": status.value,
                "detail": detail,
                "execution_identity": identity,
                "evidence_count": resolved_evidence_count,
            })
            if current.status in TERMINAL_NODE_STATUSES:
                if current.idempotency_key == stable_key \
                        and current.completion_hash == fingerprint:
                    return current
                raise IdempotencyConflictError(
                    f"terminal work unit {work_unit_id!r} received a conflicting replay"
                )
            if current.status != NodeStatus.RUNNING:
                raise StaleCallbackError(
                    f"work unit {work_unit_id!r} was not started before completion"
                )
            if current.idempotency_key != stable_key \
                    or current.execution_identity != identity:
                raise StaleCallbackError(
                    "work unit current identity does not match the latest capability binding"
                )
            finished = now_iso()
            self._conn.execute(
                "UPDATE work_unit_runs SET status=?, detail=?, execution_identity_json=?,"
                " evidence_count=?, completion_hash=?, finished_at=?, updated_at=?"
                " WHERE run_id=? AND manifest_revision=? AND work_unit_id=?",
                (
                    status.value, detail, canonical_json(identity),
                    resolved_evidence_count,
                    fingerprint, finished, finished, run_id, revision, work_unit_id,
                ),
            )
            self._append_audit_row(
                self._conn, domain.EVENT_WORK_UNIT_COMPLETE,
                {
                    "run_id": run_id, "manifest_revision": revision,
                    "work_unit_id": work_unit_id, "node_id": current_unit.node_id,
                    "label": current_unit.label, "stage": current_unit.stage,
                    "scope": current_unit.scope, "target_ref": current_unit.target_ref,
                    "status": status.value, "detail": detail,
                    "execution_identity": identity,
                    "evidence_count": resolved_evidence_count,
                },
                run_id,
            )
            return self.get_work_unit_run(run_id, revision, work_unit_id)

        return self._txn(_work)

    def _validated_work_unit_feed_payload(
        self, event_type: str, payload: Mapping[str, Any], manifest: ExecutionManifest,
        unit_by_id: Mapping[str, ManifestWorkUnit],
    ) -> Dict[str, Any]:
        expected_keys = {
            "run_id", "manifest_revision", "work_unit_id", "node_id", "label",
            "stage", "scope", "target_ref", "status", "detail",
            "execution_identity", "evidence_count",
        }
        if event_type == domain.EVENT_WORK_UNIT_ATTEMPT_BOUND:
            expected_keys = expected_keys | {"attempt_ordinal", "continued_from"}
        if set(payload) != expected_keys:
            raise StoreError("work-unit audit payload shape is invalid")
        if payload.get("run_id") != manifest.run_id \
                or payload.get("manifest_revision") != manifest.revision:
            raise StoreError("work-unit audit payload manifest identity is invalid")
        work_unit_id = payload.get("work_unit_id")
        unit = unit_by_id.get(str(work_unit_id))
        if unit is None:
            raise StoreError("work-unit audit payload references an unknown unit")
        expected_identity = {
            "node_id": unit.node_id,
            "label": unit.label,
            "stage": unit.stage,
            "scope": unit.scope,
            "target_ref": unit.target_ref,
        }
        if any(payload.get(key) != value for key, value in expected_identity.items()):
            raise StoreError("work-unit audit payload definition does not match manifest")
        detail = self._normalize_work_unit_detail(str(payload.get("detail", "")))
        if detail != payload.get("detail"):
            raise StoreError("work-unit audit detail is not normalized")
        execution_identity = payload.get("execution_identity")
        if not isinstance(execution_identity, Mapping) \
                or self._normalize_work_unit_identity(execution_identity) != execution_identity:
            raise StoreError("work-unit audit execution identity is invalid")
        evidence_count = payload.get("evidence_count")
        if isinstance(evidence_count, bool) or not isinstance(evidence_count, int) \
                or evidence_count < 0:
            raise StoreError("work-unit audit evidence count is invalid")
        try:
            status = NodeStatus(str(payload.get("status")))
        except ValueError as exc:
            raise StoreError("work-unit audit status is invalid") from exc
        if event_type == domain.EVENT_WORK_UNIT_BEGIN:
            if status != NodeStatus.RUNNING or evidence_count != 0:
                raise StoreError("work-unit begin audit state is invalid")
        elif event_type == domain.EVENT_WORK_UNIT_ATTEMPT_BOUND:
            attempt_ordinal = payload.get("attempt_ordinal")
            if status != NodeStatus.RUNNING or evidence_count != 0 \
                    or isinstance(attempt_ordinal, bool) \
                    or not isinstance(attempt_ordinal, int) \
                    or attempt_ordinal < 2 \
                    or not isinstance(payload.get("continued_from"), str) \
                    or not payload.get("continued_from"):
                raise StoreError("work-unit attempt binding audit state is invalid")
        elif event_type == domain.EVENT_WORK_UNIT_COMPLETE:
            if status not in TERMINAL_NODE_STATUSES:
                raise StoreError("work-unit completion audit state is invalid")
        else:  # pragma: no cover - caller query fixes the event types
            raise StoreError("unexpected work-unit audit event type")
        return dict(payload)

    def _validated_work_unit_projection(
        self, manifest: ExecutionManifest,
    ) -> Tuple[List[WorkUnitRun], List[Dict[str, Any]]]:
        """Cross-check manifest, ledger and immutable transition events.

        SQLite rows carry the efficient current state, while the hash-chained
        begin/complete events prove how that state was reached.  A projection
        is authoritative only when all three representations agree exactly.
        """

        try:
            rows = self.list_work_unit_runs(manifest.run_id, manifest.revision)
        except ValueError as exc:
            raise StoreError(
                "authoritative work unit ledger contains an invalid status"
            ) from exc
        unit_by_id = {unit.work_unit_id: unit for unit in manifest.work_units}
        row_by_id = {row.work_unit_id: row for row in rows}
        if len(rows) != manifest.total_units() or set(row_by_id) != set(unit_by_id):
            raise StoreError(
                "authoritative work unit ledger does not match the manifest denominator"
            )
        for work_unit_id, row in row_by_id.items():
            if row.node_id != unit_by_id[work_unit_id].node_id:
                raise StoreError(
                    "authoritative work unit ledger definition does not match the manifest"
                )

        audit_ok, first_bad_seq, _ = self.verify_audit_chain()
        if not audit_ok:
            raise StoreError(f"audit chain is invalid at sequence {first_bad_seq}")
        event_rows = self._conn.execute(
            "SELECT seq, event_type, payload_json, created_at FROM audit_events"
            " WHERE run_id=? AND event_type IN (?,?,?) ORDER BY seq",
            (manifest.run_id, domain.EVENT_WORK_UNIT_BEGIN,
             domain.EVENT_WORK_UNIT_ATTEMPT_BOUND,
             domain.EVENT_WORK_UNIT_COMPLETE),
        ).fetchall()
        derived_status = {
            work_unit_id: NodeStatus.PENDING for work_unit_id in unit_by_id
        }
        begin_payloads: Dict[str, Dict[str, Any]] = {}
        latest_running_payloads: Dict[str, Dict[str, Any]] = {}
        attempt_binding_payloads: Dict[str, List[Dict[str, Any]]] = {
            work_unit_id: [] for work_unit_id in unit_by_id
        }
        completion_payloads: Dict[str, Dict[str, Any]] = {}
        validated_events: List[Dict[str, Any]] = []
        for seq, event_type, payload_json, created_at in event_rows:
            payload = json.loads(payload_json)
            if int(payload.get("manifest_revision", -1)) != manifest.revision:
                continue
            validated = self._validated_work_unit_feed_payload(
                event_type, payload, manifest, unit_by_id
            )
            work_unit_id = str(validated["work_unit_id"])
            if event_type == domain.EVENT_WORK_UNIT_BEGIN:
                if derived_status[work_unit_id] != NodeStatus.PENDING:
                    raise StoreError("work-unit audit transition sequence is invalid")
                derived_status[work_unit_id] = NodeStatus.RUNNING
                begin_payloads[work_unit_id] = validated
                latest_running_payloads[work_unit_id] = validated
                if validated["execution_identity"].get("attempt_id"):
                    attempt_binding_payloads[work_unit_id].append(validated)
            elif event_type == domain.EVENT_WORK_UNIT_ATTEMPT_BOUND:
                if derived_status[work_unit_id] not in {
                    NodeStatus.RUNNING, NodeStatus.FAILED, NodeStatus.BLOCKED,
                }:
                    raise StoreError("work-unit retry binding sequence is invalid")
                derived_status[work_unit_id] = NodeStatus.RUNNING
                latest_running_payloads[work_unit_id] = validated
                attempt_binding_payloads[work_unit_id].append(validated)
                completion_payloads.pop(work_unit_id, None)
            else:
                if derived_status[work_unit_id] != NodeStatus.RUNNING:
                    raise StoreError("work-unit audit transition sequence is invalid")
                derived_status[work_unit_id] = NodeStatus(str(validated["status"]))
                completion_payloads[work_unit_id] = validated
            validated_events.append({
                **validated,
                "sequence": int(seq),
                "event_type": event_type,
                "created_at": created_at,
            })

        for work_unit_id, row in row_by_id.items():
            if row.status != derived_status[work_unit_id]:
                raise StoreError(
                    "authoritative work unit ledger status does not match its audit history"
                )
            unit = unit_by_id[work_unit_id]
            is_ai = self._manifest_node_type(manifest, unit.node_id) == NodeType.AI_CANDIDATE
            bindings = self._list_work_unit_capability_attempts(
                manifest.run_id, manifest.revision, work_unit_id
            )
            if not is_ai and bindings:
                raise StoreError(
                    "non-AI work unit cannot retain capability attempt bindings"
                )
            if is_ai and row.status != NodeStatus.PENDING and not bindings:
                raise StoreError(
                    "started AI work unit has no authoritative capability binding"
                )
            if is_ai and bindings:
                if [item["attempt_ordinal"] for item in bindings] \
                        != list(range(1, len(bindings) + 1)):
                    raise StoreError("work-unit capability attempt ordinals are invalid")
                transition_bindings = attempt_binding_payloads[work_unit_id]
                if len(transition_bindings) != len(bindings):
                    raise StoreError(
                        "work-unit capability binding ledger does not match its audit history"
                    )
                previous_attempt: Optional[Dict[str, Any]] = None
                retryable_statuses = frozenset({
                    "interrupted", "failed", "timeout", "cancelled",
                    "partial", "truncated",
                })
                for index, (binding_row, binding_event) in enumerate(
                    zip(bindings, transition_bindings), start=1
                ):
                    attempt, expected_identity = self._capability_work_unit_identity(
                        manifest, unit, binding_row["attempt_id"]
                    )
                    if binding_row["execution_identity"] != expected_identity \
                            or binding_row["detail"] != self._normalize_work_unit_detail(
                                binding_row["detail"]
                            ):
                        raise StoreError(
                            "work-unit capability binding does not match the attempt journal"
                        )
                    if binding_event["execution_identity"] != expected_identity \
                            or binding_event["detail"] != binding_row["detail"]:
                        raise StoreError(
                            "work-unit capability binding event does not match its ledger"
                        )
                    if index == 1:
                        if attempt["continued_from"]:
                            raise StoreError(
                                "first work-unit capability binding is a continuation"
                            )
                    else:
                        if previous_attempt is None \
                                or previous_attempt["status"] not in retryable_statuses \
                                or attempt["continued_from"] != previous_attempt["attempt_id"] \
                                or binding_event.get("attempt_ordinal") != index \
                                or binding_event.get("continued_from") \
                                != previous_attempt["attempt_id"]:
                            raise StoreError(
                                "work-unit capability continuation chain is invalid"
                            )
                    previous_attempt = attempt
            if row.status == NodeStatus.PENDING:
                if (row.idempotency_key or row.begin_hash or row.detail
                        or row.execution_identity or row.evidence_count
                        or row.completion_hash or row.started_at or row.finished_at):
                    raise StoreError("pending work-unit ledger state is not pristine")
                continue
            begin = begin_payloads.get(work_unit_id)
            if begin is None or not row.idempotency_key or not row.started_at:
                raise StoreError("started work-unit ledger evidence is incomplete")
            expected_begin_hash = content_hash({
                "detail": begin["detail"],
                "execution_identity": begin["execution_identity"],
            })
            if row.begin_hash != expected_begin_hash:
                raise StoreError("work-unit begin fingerprint does not match its audit event")
            if row.status == NodeStatus.RUNNING:
                latest_running = latest_running_payloads.get(work_unit_id)
                if (latest_running is None
                        or row.detail != latest_running["detail"]
                        or row.execution_identity != latest_running["execution_identity"]
                        or row.evidence_count != 0 or row.completion_hash
                        or row.finished_at):
                    raise StoreError("running work-unit ledger state is inconsistent")
                continue
            complete = completion_payloads.get(work_unit_id)
            if complete is None or not row.finished_at:
                raise StoreError("terminal work-unit ledger evidence is incomplete")
            if is_ai:
                latest_attempt = self.get_capability_attempt(bindings[-1]["attempt_id"])
                if latest_attempt is None:  # pragma: no cover - FK plus binding validation
                    raise StoreError("latest capability attempt is missing")
                if latest_attempt["status"] == "complete" and latest_attempt["terminal"]:
                    expected_status = NodeStatus.PASSED
                elif latest_attempt["status"] == "interrupted" \
                        and not latest_attempt["terminal"]:
                    expected_status = NodeStatus.BLOCKED
                elif latest_attempt["terminal"] and latest_attempt["status"] in {
                    "failed", "timeout", "cancelled", "partial", "truncated",
                }:
                    expected_status = NodeStatus.FAILED
                else:
                    raise StoreError(
                        "terminal AI work unit references a non-terminal capability attempt"
                    )
                if NodeStatus(str(complete["status"])) != expected_status:
                    raise StoreError(
                        "AI work-unit status does not match its capability attempt outcome"
                    )
            expected_completion_hash = content_hash({
                "status": complete["status"],
                "detail": complete["detail"],
                "execution_identity": complete["execution_identity"],
                "evidence_count": complete["evidence_count"],
            })
            if (row.detail != complete["detail"]
                    or row.execution_identity != complete["execution_identity"]
                    or row.evidence_count != complete["evidence_count"]
                    or row.completion_hash != expected_completion_hash):
                raise StoreError("terminal work-unit ledger state is inconsistent")
        return rows, validated_events

    def structured_progress(
        self, run_id: str, manifest_revision: Optional[int] = None,
        feed_limit: int = 20,
    ) -> Dict[str, Any]:
        """Project the authoritative ledger into a bounded UI-safe progress view."""
        if isinstance(feed_limit, bool) or not isinstance(feed_limit, int) \
                or not 1 <= feed_limit <= 100:
            raise StoreError("feed_limit must be an integer between 1 and 100")
        run = self.get_run(run_id)
        revision = run.manifest_revision if manifest_revision is None else manifest_revision
        manifest = self.get_manifest(run_id, revision)
        if manifest is None:
            raise StoreError(f"manifest revision not found: {run_id}/{revision}")
        if manifest.work_units:
            rows, validated_events = self._validated_work_unit_projection(manifest)
            by_status: Dict[str, int] = {}
            for row in rows:
                by_status[row.status.value] = by_status.get(row.status.value, 0) + 1
            completed = sum(
                count for status, count in by_status.items()
                if NodeStatus(status) in TERMINAL_NODE_STATUSES
            )
            unit_by_id = {unit.work_unit_id: unit for unit in manifest.work_units}
            running = []
            for row in rows:
                if row.status != NodeStatus.RUNNING:
                    continue
                unit = unit_by_id[row.work_unit_id]
                elapsed = 0
                if row.started_at:
                    started = datetime.datetime.fromisoformat(row.started_at)
                    elapsed = max(0, int((datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()))
                running.append({
                    "work_unit_id": row.work_unit_id, "node_id": row.node_id,
                    "label": unit.label, "stage": unit.stage, "scope": unit.scope,
                    "target_ref": unit.target_ref, "detail": row.detail,
                    "execution_identity": row.execution_identity,
                    "started_at": row.started_at, "elapsed_seconds": elapsed,
                })
            feed = validated_events[-feed_limit:]
            total = manifest.total_units()
        else:
            legacy = self.manifest_progress(run_id, revision)
            completed, total, by_status = (
                legacy["completed"], legacy["total"], legacy["by_status"]
            )
            running, feed = [], []
        return {
            "run_id": run_id,
            "manifest_revision": revision,
            "is_current_revision": revision == run.manifest_revision,
            "denominator_hash": self._denominator_hash(manifest, revision),
            "completed": completed,
            "total": total,
            "percent": round((completed * 100.0 / total), 2) if total else 0.0,
            "by_status": by_status,
            "running": running,
            "feed": feed,
        }

    def _work_unit_completion_gate_reasons(
        self, run_id: str, node_id: str, status: NodeStatus,
    ) -> List[str]:
        run = self.get_run(run_id)
        manifest = self.get_manifest(run_id, run.manifest_revision)
        if manifest is None or not manifest.work_units:
            return []
        units = [unit for unit in manifest.work_units if unit.node_id == node_id]
        if not units:
            return []
        rows = {
            row.work_unit_id: row
            for row in self.list_work_unit_runs(run_id, run.manifest_revision)
        }
        reasons = []
        for unit in units:
            row = rows.get(unit.work_unit_id)
            if row is None:
                reasons.append(f"work unit {unit.work_unit_id} is missing")
            elif row.status not in TERMINAL_NODE_STATUSES:
                reasons.append(
                    f"work unit {unit.work_unit_id} is not terminal ({row.status.value})"
                )
            elif (status in domain.DEPENDENCY_SATISFYING_STATUSES
                  and row.status in (NodeStatus.BLOCKED, NodeStatus.FAILED)):
                reasons.append(
                    f"successful node outcome conflicts with work unit "
                    f"{unit.work_unit_id}={row.status.value}"
                )
        return reasons

    # --------------------------------------------------------- nodes/attempts

    def get_node_run(self, run_id: str, node_id: str) -> Optional[NodeRun]:
        r = self._conn.execute(
            "SELECT run_id, node_id, node_type, manifest_revision, status,"
            " idempotency_key, attempts, artifact_id, output_json, error, reason,"
            " started_at, finished_at FROM node_runs WHERE run_id=? AND node_id=?",
            (run_id, node_id),
        ).fetchone()
        if r is None:
            return None
        return NodeRun(run_id=r[0], node_id=r[1], node_type=NodeType(r[2]),
                       manifest_revision=int(r[3]), status=NodeStatus(r[4]),
                       idempotency_key=r[5], attempts=r[6], artifact_id=r[7],
                       output=json.loads(r[8]), error=r[9], reason=r[10],
                       started_at=r[11], finished_at=r[12])

    def list_node_runs(self, run_id: str) -> List[NodeRun]:
        rows = self._conn.execute(
            "SELECT node_id FROM node_runs WHERE run_id=? ORDER BY started_at", (run_id,)
        ).fetchall()
        return [self.get_node_run(run_id, r[0]) for r in rows]

    def begin_node_run(self, run_id: str, node_id: str, node_type: NodeType,
                       idempotency_key: str) -> NodeRun:
        """Open (or reopen) a node attempt.  Idempotent semantics:
        * same logical key + successful terminal node -> return existing result;
        * same logical key + open/RUNNING -> resume in-flight state;
        * same logical key + FAILED/BLOCKED -> NEW immutable attempt record
          (prior terminal attempt is preserved, never mutated);
        * different logical key + successful terminal node -> NodeTerminalError.

        ``idempotency_key`` is the stable logical node-operation key.  Each
        attempt gets its own immutable row with a distinct attempt-scoped key
        (``<logical>#a<seq>``); replay identity stays on the logical key.
        """
        if node_type not in NodeType:
            raise StoreError(f"invalid node_type: {node_type!r}")
        if not idempotency_key:
            raise StoreError("idempotency key is required")
        manifest_revision = self.get_run(run_id).manifest_revision
        for r in self._conn.execute(
            "SELECT run_id, node_id FROM node_attempts WHERE logical_key=?",
            (idempotency_key,),
        ).fetchall():
            if (r[0], r[1]) != (run_id, node_id):
                raise IdempotencyConflictError(
                    f"idempotency key {idempotency_key!r} already used for run={r[0]} node={r[1]}"
                )
        node = self.get_node_run(run_id, node_id)
        if (node is not None and node.manifest_revision == manifest_revision
                and node.status in (
                NodeStatus.PASSED, NodeStatus.REUSED, NodeStatus.SKIPPED,
                NodeStatus.NOT_APPLICABLE)):
            mine = self._conn.execute(
                "SELECT 1 FROM node_attempts WHERE run_id=? AND node_id=?"
                " AND manifest_revision=? AND logical_key=? LIMIT 1",
                (run_id, node_id, manifest_revision, idempotency_key),
            ).fetchone()
            if mine is not None:
                return node  # idempotent replay of the committed result
            raise NodeTerminalError(
                f"node {run_id}/{node_id} already terminal ({node.status.value}); "
                "re-execution requires an explicit manifest revision"
            )

        def _work() -> NodeRun:
            if self.get_run(run_id).manifest_revision != manifest_revision:
                raise StaleCallbackError(
                    f"node begin revision {manifest_revision} became stale"
                )
            latest = self._conn.execute(
                "SELECT attempt_seq, status, logical_key, manifest_revision"
                " FROM node_attempts"
                " WHERE run_id=? AND node_id=? ORDER BY attempt_seq DESC LIMIT 1",
                (run_id, node_id),
            ).fetchone()
            now = now_iso()
            if latest is not None:
                seq, st, lkey, attempt_revision = latest
                if (st == NodeStatus.RUNNING.value and lkey == idempotency_key
                        and int(attempt_revision) == manifest_revision):
                    # Resume the same in-flight attempt: no new attempt row,
                    # no attempt counter growth.
                    self._conn.execute(
                        "UPDATE node_runs SET manifest_revision=?, status=?,"
                        " idempotency_key=?, error=NULL,"
                        " finished_at=NULL WHERE run_id=? AND node_id=?",
                        (manifest_revision, NodeStatus.RUNNING.value,
                         idempotency_key, run_id, node_id),
                    )
                else:
                    # Retry after FAILED/BLOCKED (same key) or a new lifecycle
                    # key: append a NEW immutable attempt record; the previous
                    # terminal attempt row stays untouched.
                    new_seq = int(seq) + 1
                    self._conn.execute(
                        "INSERT INTO node_attempts(run_id, node_id, attempt_seq, idempotency_key,"
                        " logical_key, manifest_revision, status, created_at)"
                        " VALUES (?,?,?,?,?,?,?,?)",
                        (run_id, node_id, new_seq, f"{idempotency_key}#a{new_seq}",
                         idempotency_key, manifest_revision,
                         NodeStatus.RUNNING.value, now),
                    )
                    self._conn.execute(
                        "UPDATE node_runs SET manifest_revision=?, status=?, idempotency_key=?,"
                        " attempts=attempts+1, artifact_id=NULL, output_json='{}', error=NULL,"
                        " reason=NULL, started_at=?, finished_at=NULL"
                        " WHERE run_id=? AND node_id=?",
                        (manifest_revision, NodeStatus.RUNNING.value,
                         idempotency_key, now, run_id, node_id),
                    )
            elif node is None:
                self._conn.execute(
                    "INSERT INTO node_runs(run_id, node_id, node_type, manifest_revision,"
                    " status, idempotency_key, attempts, output_json, started_at)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (run_id, node_id, node_type.value, manifest_revision,
                     NodeStatus.RUNNING.value, idempotency_key, 1, "{}", now),
                )
                self._conn.execute(
                    "INSERT INTO node_attempts(run_id, node_id, attempt_seq, idempotency_key,"
                    " logical_key, manifest_revision, status, created_at)"
                    " VALUES (?,?,?,?,?,?,?,?)",
                    (run_id, node_id, 1, f"{idempotency_key}#a1", idempotency_key,
                     manifest_revision, NodeStatus.RUNNING.value, now),
                )
            else:  # defensive: node exists without any attempt row
                self._conn.execute(
                    "INSERT INTO node_attempts(run_id, node_id, attempt_seq, idempotency_key,"
                    " logical_key, manifest_revision, status, created_at)"
                    " VALUES (?,?,?,?,?,?,?,?)",
                    (run_id, node_id, 1, f"{idempotency_key}#a1", idempotency_key,
                     manifest_revision, NodeStatus.RUNNING.value, now),
                )
                self._conn.execute(
                    "UPDATE node_runs SET manifest_revision=?, status=?, idempotency_key=?,"
                    " attempts=attempts+1, artifact_id=NULL, output_json='{}', error=NULL,"
                    " reason=NULL, started_at=?, finished_at=NULL"
                    " WHERE run_id=? AND node_id=?",
                    (manifest_revision, NodeStatus.RUNNING.value,
                     idempotency_key, now, run_id, node_id),
                )
            self._set_current_manifest_node_progress(
                run_id, node_id, NodeStatus.RUNNING
            )
            self._append_audit_row(self._conn, domain.EVENT_NODE_BEGIN,
                                   {"run_id": run_id, "node_id": node_id,
                                    "node_type": node_type.value,
                                    "idempotency_key": idempotency_key,
                                    "manifest_revision": manifest_revision}, run_id)
            return self.get_node_run(run_id, node_id)

        return self._txn(_work)

    @staticmethod
    def _outcome_fingerprint(status: NodeStatus, envelope: Optional[ArtifactEnvelope],
                             output: Optional[Mapping[str, Any]],
                             error: Optional[str], reason: Optional[str]) -> str:
        """Canonical fingerprint of a complete callback outcome: status +
        envelope content + output + error/reason.  Derived inside the Store so
        callers cannot silently accept conflicting same-key output by omitting
        a payload hash."""
        return content_hash({
            "status": status.value,
            "envelope": to_jsonable(envelope.content_dict()) if envelope is not None else None,
            "output": to_jsonable(dict(output or {})),
            "error": error,
            "reason": reason,
        })

    def _audit_callback_conflict(self, run_id: str, node_id: str, idempotency_key: str,
                                 attempted_status: NodeStatus, fingerprint: str) -> None:
        try:
            self.append_audit(domain.EVENT_IDEMPOTENCY_CONFLICT,
                              {"run_id": run_id, "node_id": node_id,
                               "idempotency_key": idempotency_key,
                               "attempted_status": attempted_status.value,
                               "outcome_fingerprint": fingerprint,
                               "reason": "outcome_conflict"}, run_id)
        except Exception:  # pragma: no cover - audit failure must not mask rejection
            pass

    def complete_node_run(self, run_id: str, node_id: str, idempotency_key: str,
                          status: NodeStatus, envelope: Optional[ArtifactEnvelope] = None,
                          output: Optional[Mapping[str, Any]] = None, error: Optional[str] = None,
                          reason: Optional[str] = None,
                          payload_hash: Optional[str] = None) -> NodeRun:
        """Commit a node outcome + optional artifact atomically.

        Protocol: validate the callback (key currency, outcome fingerprint)
        FIRST -- no artifact file, no DB row, no audit except the deliberate
        rejection/conflict audit is produced by a stale or conflicting
        callback.  Only a current, non-conflicting callback stages the
        artifact file (outside txn), then ONE transaction inserts the artifact
        row, closes the attempt and appends audits.

        Duplicate identical callbacks replay the stored result; stale or
        conflicting callbacks raise without creating any artifact/orphan state.
        """
        if status not in TERMINAL_NODE_STATUSES:
            raise StoreError(f"non-terminal status cannot be committed: {status.value}")
        if envelope is not None:
            if envelope.run_id != run_id or envelope.node_id != node_id:
                raise StoreError("envelope provenance must match run/node")
            if status in (NodeStatus.FAILED, NodeStatus.BLOCKED):
                raise StoreError("failed/blocked nodes must not produce artifacts")
        node = self.get_node_run(run_id, node_id)
        if node is None:
            raise StaleCallbackError(
                f"callback for unknown/unopened node {run_id}/{node_id}"
            )
        manifest_revision = self.get_run(run_id).manifest_revision
        if node.manifest_revision != manifest_revision:
            self._reject_late(run_id, node_id, idempotency_key, status)
            raise StaleCallbackError(
                f"node callback revision {node.manifest_revision} is stale;"
                f" current revision is {manifest_revision}"
            )
        fingerprint = self._outcome_fingerprint(status, envelope, output, error, reason)
        latest = self._conn.execute(
            "SELECT attempt_seq, idempotency_key, logical_key, manifest_revision,"
            " status, payload_hash"
            " FROM node_attempts WHERE run_id=? AND node_id=? ORDER BY attempt_seq DESC LIMIT 1",
            (run_id, node_id),
        ).fetchone()
        if latest is None or int(latest[3]) != manifest_revision:
            self._reject_late(run_id, node_id, idempotency_key, status)
            raise StaleCallbackError(
                f"node attempt callback revision is stale for {run_id}/{node_id}"
            )
        if node.status in TERMINAL_NODE_STATUSES:
            if latest is not None and latest[2] == idempotency_key:
                stored_fp = latest[5]
                if stored_fp is not None and stored_fp != fingerprint:
                    self._audit_callback_conflict(run_id, node_id, idempotency_key,
                                                  status, fingerprint)
                    raise IdempotencyConflictError(
                        f"same idempotency key {idempotency_key!r} replayed with "
                        "a different outcome"
                    )
                self.append_audit(domain.EVENT_IDEMPOTENT_REPLAY,
                                  {"scope": "node_complete", "run_id": run_id,
                                   "node_id": node_id, "idempotency_key": idempotency_key},
                                  run_id)
                return node  # idempotent replay, history untouched
            self._reject_late(run_id, node_id, idempotency_key, status)
            raise StaleCallbackError(
                f"late attempt callback for terminal node {run_id}/{node_id}: "
                f"key {idempotency_key!r} != current {node.idempotency_key!r}"
            )
        if latest[2] != idempotency_key or latest[4] != NodeStatus.RUNNING.value:
            self._reject_late(run_id, node_id, idempotency_key, status)
            raise StaleCallbackError(
                f"attempt {idempotency_key!r} is not the open attempt of {run_id}/{node_id}"
            )
        work_unit_gate_reasons = self._work_unit_completion_gate_reasons(
            run_id, node_id, status
        )
        if work_unit_gate_reasons:
            raise CompletionGateError(work_unit_gate_reasons)
        # Validation passed: only now stage the artifact file (crash here
        # leaves an auditable orphan, never authoritative state).
        staged_hash = self.stage_artifact(envelope) if envelope is not None else None

        def _work() -> NodeRun:
            if self.get_run(run_id).manifest_revision != manifest_revision:
                raise StaleCallbackError(
                    f"node completion revision {manifest_revision} became stale"
                )
            if staged_hash is not None:
                self._insert_artifact_row(self._conn, staged_hash, envelope)
                artifact_id = staged_hash
            else:
                artifact_id = node.artifact_id
            finished = now_iso()
            self._conn.execute(
                "UPDATE node_runs SET status=?, artifact_id=?, output_json=?, error=?, reason=?,"
                " finished_at=? WHERE run_id=? AND node_id=? AND manifest_revision=?",
                (status.value, artifact_id,
                 canonical_json(to_jsonable(dict(output or {}))), error, reason, finished,
                 run_id, node_id, manifest_revision),
            )
            self._conn.execute(
                "UPDATE node_attempts SET status=?, payload_hash=? WHERE run_id=? AND node_id=?"
                " AND attempt_seq=? AND manifest_revision=?",
                (status.value, fingerprint, run_id, node_id, latest[0],
                 manifest_revision),
            )
            self._set_current_manifest_node_progress(run_id, node_id, status)
            self._append_audit_row(self._conn, domain.EVENT_NODE_COMPLETE,
                                   {"run_id": run_id, "node_id": node_id, "status": status.value,
                                    "artifact_id": artifact_id, "idempotency_key": idempotency_key,
                                    "error": error, "reason": reason,
                                    "manifest_revision": manifest_revision}, run_id)
            return self.get_node_run(run_id, node_id)

        return self._txn(_work)

    def _reject_late(self, run_id: str, node_id: str, idempotency_key: str,
                     attempted_status: NodeStatus) -> None:
        """Audit a rejected late/stale callback (best effort; no state change)."""
        try:
            self.append_audit(domain.EVENT_NODE_REJECTED,
                              {"run_id": run_id, "node_id": node_id,
                               "idempotency_key": idempotency_key,
                               "attempted_status": attempted_status.value,
                               "reason": "stale_callback"}, run_id)
        except Exception:  # pragma: no cover - audit failure must not mask rejection
            pass

    def list_node_attempts(self, run_id: str, node_id: str) -> List[NodeAttempt]:
        """Immutable per-attempt history, oldest first (public inspection)."""
        rows = self._conn.execute(
            "SELECT run_id, node_id, attempt_seq, idempotency_key, status, payload_hash,"
            " created_at, logical_key, manifest_revision FROM node_attempts"
            " WHERE run_id=? AND node_id=?"
            " ORDER BY attempt_seq", (run_id, node_id),
        ).fetchall()
        return [NodeAttempt(run_id=r[0], node_id=r[1], attempt_seq=r[2],
                            idempotency_key=r[3], status=NodeStatus(r[4]),
                            payload_hash=r[5], created_at=r[6], logical_key=r[7],
                            manifest_revision=int(r[8]))
                for r in rows]

    # ------------------------------------------------ capability attempts

    @staticmethod
    def _capability_attempt_dict(row: Sequence[Any]) -> Dict[str, Any]:
        request = json.loads(row[4])
        result = json.loads(row[12]) if row[12] is not None else None
        terminal = bool(row[9])
        if content_hash(request) != row[3]:
            raise StoreError("capability attempt request hash mismatch")
        params = request.get("params")
        if not isinstance(params, Mapping):
            raise StoreError("capability attempt request params are invalid")
        binding = params.get("binding")
        execution_identity = params.get("execution_identity")
        if not isinstance(binding, Mapping) or not isinstance(execution_identity, Mapping):
            raise StoreError("capability attempt execution identity is invalid")
        expected_execution_identity = {
            "profile_fingerprint": row[5],
            "binding_id": binding.get("binding_id"),
            "provider": binding.get("provider"),
            "model": binding.get("model"),
            "selector": binding.get("selector"),
            "adapter_version": binding.get("adapter_version"),
        }
        if request.get("jsonrpc") != "2.0" \
                or request.get("method") != "medical_monitoring.analyze" \
                or request.get("id") != row[0] \
                or params.get("monitoring_run_id") != row[1] \
                or params.get("node_id") != row[2] \
                or params.get("manifest_revision") != int(row[6]) \
                or (params.get("continued_from") or "") != (row[14] or "") \
                or params.get("profile_fingerprint") != row[5] \
                or execution_identity.get("profile_fingerprint") != row[5] \
                or params.get("input_hash") != row[7] \
                or binding.get("input_hash") != row[7]:
            raise StoreError("capability attempt request identity mismatch")
        if dict(execution_identity) != expected_execution_identity:
            raise StoreError(
                "capability attempt execution identity does not match its frozen binding"
            )
        if terminal != (result is not None):
            raise StoreError("capability attempt terminal/result state mismatch")
        terminal_statuses = frozenset(
            ("complete", "failed", "timeout", "cancelled", "partial", "truncated")
        )
        nonterminal_statuses = frozenset(("declared", "running", "interrupted"))
        if terminal and row[8] not in terminal_statuses:
            raise StoreError("capability attempt terminal status is invalid")
        if not terminal and row[8] not in nonterminal_statuses:
            raise StoreError("capability attempt non-terminal status is invalid")
        if row[8] == "running" and (not row[10] or row[11] is None):
            raise StoreError("running capability attempt requires owner and lease")
        if row[8] != "running" and (row[10] is not None or row[11] is not None):
            raise StoreError("non-running capability attempt cannot retain owner or lease")
        if terminal != bool(row[17]):
            raise StoreError("capability attempt terminal timestamp state mismatch")
        if result is not None and content_hash({"status": row[8], "result": result}) != row[13]:
            raise StoreError("capability attempt result hash mismatch")
        return {
            "attempt_id": row[0],
            "run_id": row[1],
            "node_id": row[2],
            "request_hash": row[3],
            "request": request,
            "profile_fingerprint": row[5],
            "manifest_revision": int(row[6]),
            "input_hash": row[7],
            "status": row[8],
            "terminal": terminal,
            "owner_token": row[10] or "",
            "lease_expires_at": row[11],
            "result": result,
            "result_hash": row[13] or "",
            "continued_from": row[14] or "",
            "created_at": row[15],
            "updated_at": row[16],
            "terminal_at": row[17] or "",
        }

    def get_capability_attempt(self, attempt_id: str) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT attempt_id, run_id, node_id, request_hash, request_json,"
            " profile_fingerprint, manifest_revision, input_hash, status, terminal,"
            " owner_token, lease_expires_at, result_json, result_hash, continued_from,"
            " created_at, updated_at, terminal_at FROM capability_attempt_journal"
            " WHERE attempt_id=?",
            (attempt_id,),
        ).fetchone()
        if row is None:
            return None
        attempt = self._capability_attempt_dict(row)
        self._validate_capability_attempt_lifecycle(attempt)
        return attempt

    def _runtime_attempt_journal(self) -> _RuntimeAttemptJournal:
        """Private hook consumed by :class:`CapabilityRuntime` only."""

        return _RuntimeAttemptJournal(self)

    def _validate_capability_attempt_lifecycle(
        self, attempt: Mapping[str, Any],
    ) -> None:
        """Reconcile the current journal row with its reserved audit events."""

        rows = self._conn.execute(
            "SELECT event_type, payload_json FROM audit_events WHERE run_id=?"
            " AND event_type IN (?,?,?,?) ORDER BY seq",
            (
                attempt["run_id"],
                domain.EVENT_CAPABILITY_ATTEMPT_DECLARED,
                domain.EVENT_CAPABILITY_ATTEMPT_CLAIMED,
                domain.EVENT_CAPABILITY_ATTEMPT_INTERRUPTED,
                domain.EVENT_CAPABILITY_ATTEMPT_TERMINAL,
            ),
        ).fetchall()
        lifecycle: List[Tuple[str, Dict[str, Any]]] = []
        for event_type, payload_json in rows:
            try:
                payload = json.loads(payload_json)
            except (TypeError, json.JSONDecodeError) as exc:
                raise StoreError("capability attempt lifecycle audit JSON is invalid") from exc
            if isinstance(payload, Mapping) and payload.get("attempt_id") == attempt["attempt_id"]:
                lifecycle.append((event_type, dict(payload)))
        if not lifecycle or lifecycle[0][0] != domain.EVENT_CAPABILITY_ATTEMPT_DECLARED:
            raise StoreError("capability attempt has no authoritative declaration audit event")
        declared = lifecycle[0][1]
        if (
            declared.get("run_id") != attempt["run_id"]
            or declared.get("node_id") != attempt["node_id"]
            or declared.get("request_hash") != attempt["request_hash"]
            or int(declared.get("manifest_revision", -1)) != attempt["manifest_revision"]
            or (declared.get("continued_from") or "") != attempt["continued_from"]
        ):
            raise StoreError("capability declaration audit does not match its journal row")

        state = "declared"
        for event_type, payload in lifecycle[1:]:
            if event_type == domain.EVENT_CAPABILITY_ATTEMPT_CLAIMED:
                if state != "declared":
                    raise StoreError("capability attempt claim audit sequence is invalid")
                state = "running"
            elif event_type == domain.EVENT_CAPABILITY_ATTEMPT_INTERRUPTED:
                if state != "running":
                    raise StoreError("capability attempt interruption audit sequence is invalid")
                state = "interrupted"
            elif event_type == domain.EVENT_CAPABILITY_ATTEMPT_TERMINAL:
                if state != "running":
                    raise StoreError("capability attempt terminal audit sequence is invalid")
                if payload.get("status") != attempt["status"] \
                        or payload.get("result_hash") != attempt["result_hash"]:
                    raise StoreError(
                        "capability terminal audit does not match its journal result"
                    )
                state = str(payload.get("status"))
            else:  # pragma: no cover - SQL filter is closed above
                raise StoreError("unexpected capability lifecycle audit event")

        if state != attempt["status"]:
            raise StoreError("capability attempt journal state does not match its audit lifecycle")

    @staticmethod
    def _validate_capability_result_envelope(attempt: Mapping[str, Any]) -> None:
        """Require an immutable runtime result envelope before authority binding."""

        if not attempt["terminal"]:
            return
        result = attempt.get("result")
        if not isinstance(result, Mapping):
            raise StoreError("terminal capability attempt has no runtime result envelope")
        adapter_run = result.get("adapter_run")
        work_events = result.get("work_events")
        transport = result.get("transport_execution")
        if not isinstance(adapter_run, Mapping) \
                or not isinstance(work_events, list) \
                or not isinstance(transport, Mapping):
            raise StoreError("terminal capability result is not a runtime evidence envelope")
        params = attempt["request"]["params"]
        binding = adapter_run.get("binding")
        if (
            adapter_run.get("run_id") != attempt["attempt_id"]
            or adapter_run.get("monitoring_run_id") != attempt["run_id"]
            or adapter_run.get("node_id") != attempt["node_id"]
            or adapter_run.get("status") != attempt["status"]
            or (adapter_run.get("continued_from") or "") != attempt["continued_from"]
            or not isinstance(binding, Mapping)
            or dict(binding) != dict(params["binding"])
        ):
            raise StoreError("terminal capability runtime identity does not match its request")
        raw_output = adapter_run.get("raw_output")
        if not isinstance(raw_output, Mapping):
            raise StoreError("terminal capability runtime evidence has no sealed raw output")
        raw_json = raw_output.get("raw_output_json")
        try:
            parsed_raw = json.loads(raw_json) if isinstance(raw_json, str) else None
        except json.JSONDecodeError as exc:
            raise StoreError("terminal capability raw output JSON is invalid") from exc
        raw_hash = content_hash({"raw_output": parsed_raw}) if parsed_raw is not None else ""
        expected_ref = f"raw-output:{attempt['attempt_id']}:{raw_hash}"
        if (
            not raw_hash
            or raw_output.get("content_hash") != raw_hash
            or raw_output.get("raw_output_ref") != expected_ref
            or raw_output.get("run_id") != attempt["attempt_id"]
            or raw_output.get("binding_id") != binding.get("binding_id")
            or raw_output.get("input_hash") != attempt["input_hash"]
            or raw_output.get("immutable") is not True
            or transport.get("raw_output") != parsed_raw
        ):
            raise StoreError("terminal capability raw-output evidence is inconsistent")
        if [item.get("sequence") for item in work_events if isinstance(item, Mapping)] \
                != list(range(1, len(work_events) + 1)) \
                or not work_events \
                or any(
                    not isinstance(item, Mapping)
                    or item.get("attempt_id") != attempt["attempt_id"]
                    for item in work_events
                ) \
                or work_events[-1].get("stage") != "attempt_terminal" \
                or work_events[-1].get("status") != attempt["status"]:
            raise StoreError("terminal capability work-event evidence is inconsistent")
        if attempt["status"] in {"complete", "partial", "truncated"}:
            candidate = adapter_run.get("candidate_artifact")
            if (
                not isinstance(candidate, Mapping)
                or candidate.get("run_id") != attempt["run_id"]
                or candidate.get("node_id") != attempt["node_id"]
                or candidate.get("node_type") != "ai_candidate"
                or candidate.get("payload_role") != "candidate"
                or attempt["input_hash"] not in candidate.get("input_hashes", [])
                or expected_ref not in candidate.get("evidence_refs", [])
            ):
                raise StoreError("terminal capability candidate evidence is inconsistent")

    def _declare_capability_attempt(
        self,
        *,
        attempt_id: str,
        run_id: str,
        node_id: str,
        request_hash: str,
        request: Mapping[str, Any],
        profile_fingerprint: str,
        manifest_revision: int,
        input_hash: str,
        continued_from: str = "",
    ) -> Dict[str, Any]:
        """Atomically freeze one transport attempt before any dispatch.

        The full request is retained only inside this synthetic-only POC Store.
        Reusing an attempt id with a different identity is always rejected.
        """

        if not all((attempt_id, run_id, node_id, request_hash, profile_fingerprint, input_hash)):
            raise StoreError("capability attempt identity fields are required")
        detached = to_jsonable(dict(request))
        if content_hash(detached) != request_hash:
            raise StoreError("capability request hash does not match request JSON")
        conflict: Optional[Tuple[str, str]] = None

        def _work() -> Dict[str, Any]:
            nonlocal conflict
            existing = self.get_capability_attempt(attempt_id)
            if existing is not None:
                if existing["request_hash"] != request_hash:
                    conflict = (existing["request_hash"], request_hash)
                return existing
            run_row = self._conn.execute(
                "SELECT manifest_revision FROM monitoring_runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if run_row is None:
                raise StoreError("capability attempt run does not exist")
            if int(run_row[0]) != int(manifest_revision):
                raise StaleCallbackError("capability attempt manifest revision is not current")
            created = now_iso()
            self._conn.execute(
                "INSERT INTO capability_attempt_journal("
                " attempt_id, run_id, node_id, request_hash, request_json, profile_fingerprint,"
                " manifest_revision, input_hash, status, terminal, continued_from, created_at,"
                " updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    attempt_id, run_id, node_id, request_hash, canonical_json(detached),
                    profile_fingerprint, int(manifest_revision), input_hash, "declared", 0,
                    continued_from, created, created,
                ),
            )
            self._append_audit_row(
                self._conn,
                domain.EVENT_CAPABILITY_ATTEMPT_DECLARED,
                {
                    "attempt_id": attempt_id,
                    "run_id": run_id,
                    "node_id": node_id,
                    "request_hash": request_hash,
                    "manifest_revision": int(manifest_revision),
                    "continued_from": continued_from,
                },
                run_id,
            )
            return self.get_capability_attempt(attempt_id)

        entry = self._txn(_work)
        if conflict is not None:
            self.append_audit(
                domain.EVENT_CAPABILITY_ATTEMPT_REJECTED,
                {
                    "attempt_id": attempt_id,
                    "reason": "request_identity_conflict",
                    "stored_request_hash": conflict[0],
                    "attempted_request_hash": conflict[1],
                },
                run_id,
            )
            raise IdempotencyConflictError(
                "capability attempt_id already belongs to a different frozen request"
            )
        return entry

    def _claim_capability_attempt(
        self,
        attempt_id: str,
        request_hash: str,
        owner_token: str,
        *,
        lease_seconds: float,
        now_epoch: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Claim a declared attempt; never re-run an expired attempt id."""

        if not owner_token or lease_seconds <= 0:
            raise StoreError("capability claim requires owner_token and a positive lease")
        current_epoch = float(time.time() if now_epoch is None else now_epoch)

        def _work() -> Dict[str, Any]:
            entry = self.get_capability_attempt(attempt_id)
            if entry is None or entry["request_hash"] != request_hash:
                raise StaleCallbackError("unknown or mismatched capability attempt claim")
            if entry["terminal"] or entry["status"] == "interrupted":
                return entry
            if entry["status"] == "running":
                expires = entry["lease_expires_at"]
                if expires is not None and float(expires) <= current_epoch:
                    updated = now_iso()
                    self._conn.execute(
                        "UPDATE capability_attempt_journal SET status='interrupted',"
                        " owner_token=NULL, lease_expires_at=NULL, updated_at=?"
                        " WHERE attempt_id=? AND terminal=0",
                        (updated, attempt_id),
                    )
                    self._append_audit_row(
                        self._conn,
                        domain.EVENT_CAPABILITY_ATTEMPT_INTERRUPTED,
                        {"attempt_id": attempt_id, "reason": "lease_expired"},
                        entry["run_id"],
                    )
                    return self.get_capability_attempt(attempt_id)
                raise StoreError("capability attempt is leased by another process")
            if entry["status"] != "declared":
                raise StoreError("capability attempt cannot be claimed from its current state")
            expires_at = current_epoch + float(lease_seconds)
            updated = now_iso()
            self._conn.execute(
                "UPDATE capability_attempt_journal SET status='running', owner_token=?,"
                " lease_expires_at=?, updated_at=? WHERE attempt_id=? AND terminal=0",
                (owner_token, expires_at, updated, attempt_id),
            )
            self._append_audit_row(
                self._conn,
                domain.EVENT_CAPABILITY_ATTEMPT_CLAIMED,
                {"attempt_id": attempt_id, "lease_expires_at": expires_at},
                entry["run_id"],
            )
            return self.get_capability_attempt(attempt_id)

        return self._txn(_work)

    def _interrupt_capability_attempt(
        self,
        attempt_id: str,
        request_hash: str,
        owner_token: str,
        *,
        reason: str,
    ) -> Dict[str, Any]:
        def _work() -> Dict[str, Any]:
            entry = self.get_capability_attempt(attempt_id)
            if entry is None or entry["request_hash"] != request_hash:
                raise StaleCallbackError("unknown or mismatched capability attempt")
            if entry["terminal"] or entry["status"] == "interrupted":
                return entry
            if entry["status"] != "running" or entry["owner_token"] != owner_token:
                raise StaleCallbackError("only the current capability owner may interrupt")
            self._conn.execute(
                "UPDATE capability_attempt_journal SET status='interrupted', owner_token=NULL,"
                " lease_expires_at=NULL, updated_at=? WHERE attempt_id=? AND terminal=0",
                (now_iso(), attempt_id),
            )
            self._append_audit_row(
                self._conn,
                domain.EVENT_CAPABILITY_ATTEMPT_INTERRUPTED,
                {"attempt_id": attempt_id, "reason": reason},
                entry["run_id"],
            )
            return self.get_capability_attempt(attempt_id)

        return self._txn(_work)

    def recover_expired_capability_attempts(
        self,
        *,
        now_epoch: Optional[float] = None,
        run_id: Optional[str] = None,
    ) -> List[str]:
        """Mark expired running leases interrupted; never redispatch them."""

        current_epoch = float(time.time() if now_epoch is None else now_epoch)

        def _work() -> List[str]:
            sql = (
                "SELECT attempt_id, run_id FROM capability_attempt_journal"
                " WHERE status='running' AND terminal=0 AND lease_expires_at IS NOT NULL"
                " AND lease_expires_at<=?"
            )
            params: List[Any] = [current_epoch]
            if run_id is not None:
                sql += " AND run_id=?"
                params.append(run_id)
            rows = self._conn.execute(sql, tuple(params)).fetchall()
            recovered: List[str] = []
            for attempt, attempt_run_id in rows:
                self._conn.execute(
                    "UPDATE capability_attempt_journal SET status='interrupted',"
                    " owner_token=NULL, lease_expires_at=NULL, updated_at=?"
                    " WHERE attempt_id=? AND status='running' AND terminal=0",
                    (now_iso(), attempt),
                )
                self._append_audit_row(
                    self._conn,
                    domain.EVENT_CAPABILITY_ATTEMPT_INTERRUPTED,
                    {"attempt_id": attempt, "reason": "lease_expired_recovery"},
                    attempt_run_id,
                )
                recovered.append(attempt)
            return recovered

        return self._txn(_work)

    def _complete_capability_attempt(
        self,
        attempt_id: str,
        request_hash: str,
        owner_token: str,
        *,
        status: str,
        result: Mapping[str, Any],
        now_epoch: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Commit one immutable terminal result or reject a stale callback."""

        terminal_statuses = frozenset(
            ("complete", "failed", "timeout", "cancelled", "partial", "truncated")
        )
        if status not in terminal_statuses:
            raise StoreError("non-terminal capability status cannot be committed: %s" % status)
        detached = to_jsonable(dict(result))
        # Bind the row-level terminal status to the immutable result payload.
        # Hashing the payload alone would allow direct journal corruption to
        # change ``status`` while replaying the original result.
        result_hash = content_hash({"status": status, "result": detached})
        current_epoch = float(time.time() if now_epoch is None else now_epoch)
        rejection: Optional[Tuple[str, Optional[str]]] = None

        def _work() -> Dict[str, Any]:
            nonlocal rejection
            entry = self.get_capability_attempt(attempt_id)
            if entry is None or entry["request_hash"] != request_hash:
                rejection = ("unknown_or_mismatched_attempt", None)
                return entry or {}
            if entry["terminal"]:
                if entry["status"] != status or entry["result_hash"] != result_hash:
                    rejection = ("terminal_result_conflict", entry["run_id"])
                return entry
            if entry["status"] != "running" or entry["owner_token"] != owner_token:
                rejection = ("stale_or_interrupted_callback", entry["run_id"])
                return entry
            expires = entry["lease_expires_at"]
            if expires is None or float(expires) <= current_epoch:
                updated = now_iso()
                self._conn.execute(
                    "UPDATE capability_attempt_journal SET status='interrupted',"
                    " owner_token=NULL, lease_expires_at=NULL, updated_at=?"
                    " WHERE attempt_id=? AND terminal=0",
                    (updated, attempt_id),
                )
                self._append_audit_row(
                    self._conn,
                    domain.EVENT_CAPABILITY_ATTEMPT_INTERRUPTED,
                    {"attempt_id": attempt_id, "reason": "lease_expired_before_completion"},
                    entry["run_id"],
                )
                rejection = ("expired_lease_callback", entry["run_id"])
                return self.get_capability_attempt(attempt_id)
            terminal_at = now_iso()
            self._conn.execute(
                "UPDATE capability_attempt_journal SET status=?, terminal=1, owner_token=NULL,"
                " lease_expires_at=NULL, result_json=?, result_hash=?, updated_at=?, terminal_at=?"
                " WHERE attempt_id=? AND terminal=0",
                (
                    status, canonical_json(detached), result_hash, terminal_at, terminal_at,
                    attempt_id,
                ),
            )
            self._append_audit_row(
                self._conn,
                domain.EVENT_CAPABILITY_ATTEMPT_TERMINAL,
                {"attempt_id": attempt_id, "status": status, "result_hash": result_hash},
                entry["run_id"],
            )
            return self.get_capability_attempt(attempt_id)

        completed = self._txn(_work)
        if rejection is not None:
            reject_run_id = rejection[1]
            if reject_run_id is not None:
                self.append_audit(
                    domain.EVENT_CAPABILITY_ATTEMPT_REJECTED,
                    {"attempt_id": attempt_id, "reason": rejection[0], "result_hash": result_hash},
                    reject_run_id,
                )
            if rejection[0] == "terminal_result_conflict":
                raise IdempotencyConflictError("terminal capability result is immutable")
            raise StaleCallbackError("stale/interrupted capability completion was rejected")
        return completed

    # -------------------------------------------------------------- artifacts

    def _content_path(self, content_hash: str) -> Path:
        return self.artifact_dir / f"{content_hash}.json"

    def _write_content_file(self, content_hash: str, obj: Any) -> Path:
        """Immutable content-addressed write.

        Durability protocol: write to a UNIQUE temp file in the artifact dir,
        flush + fsync, atomic rename into place, then best-effort directory
        fsync -- only then may the DB reference the content address.  A crash
        at any point leaves at most an unreferenced ``*.tmp``/orphan file that
        recovery audits, never authoritative state.
        """
        path = self._content_path(content_hash)
        payload = canonical_json(obj)
        if path.exists():
            existing = path.read_text("utf-8")
            if existing != payload:
                raise ArtifactCollisionError(
                    f"content address {content_hash} already exists with different bytes"
                )
            return path
        fd, tmp_name = tempfile.mkstemp(prefix=path.stem + ".", suffix=".tmp",
                                        dir=str(self.artifact_dir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, path)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        self._fsync_dir(self.artifact_dir)
        return path

    @staticmethod
    def _fsync_dir(directory: Path) -> None:
        """Best-effort directory fsync so the rename is durable."""
        try:
            dfd = os.open(str(directory), os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(dfd)
        except OSError:
            pass
        finally:
            os.close(dfd)

    def stage_artifact(self, envelope: ArtifactEnvelope) -> str:
        """Step 1 of the commit protocol: write the immutable artifact file only.

        No DB rows are created; a crash after this point leaves an orphan file
        that recovery can audit and quarantine but that is never authoritative.
        Returns the content hash (== artifact id).
        """
        content_hash_val = envelope.canonical_hash()
        self._write_content_file(content_hash_val, envelope.content_dict())
        return content_hash_val

    def _insert_artifact_row(self, conn: sqlite3.Connection, content_hash_val: str,
                             envelope: ArtifactEnvelope) -> None:
        row = conn.execute(
            "SELECT envelope_json, created_at FROM artifacts WHERE content_hash=?",
            (content_hash_val,),
        ).fetchone()
        if row is not None:
            return  # already committed (idempotent)
        created = now_iso()
        full = dict(envelope.content_dict())
        full["artifact_id"] = content_hash_val
        full["content_hash"] = content_hash_val
        full["created_at"] = created
        conn.execute(
            "INSERT INTO artifacts(artifact_id, content_hash, run_id, node_id, artifact_type,"
            " completeness, envelope_json, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (content_hash_val, content_hash_val, envelope.run_id, envelope.node_id,
             envelope.artifact_type, envelope.completeness.value,
             canonical_json(full), created),
        )
        self._append_audit_row(conn, domain.EVENT_ARTIFACT_COMMITTED,
                               {"artifact_id": content_hash_val, "run_id": envelope.run_id,
                                "node_id": envelope.node_id, "artifact_type": envelope.artifact_type,
                                "completeness": envelope.completeness.value}, envelope.run_id)

    def commit_artifact(self, staged_hash: str, envelope: ArtifactEnvelope) -> ArtifactEnvelope:
        """Step 2: commit a staged artifact (artifact row + audit in one txn)."""
        if not self._content_path(staged_hash).exists():
            raise StoreError(f"staged artifact file missing for {staged_hash}")
        if staged_hash != envelope.canonical_hash():
            raise StoreError("staged hash does not match envelope content")

        def _work() -> ArtifactEnvelope:
            self._insert_artifact_row(self._conn, staged_hash, envelope)
            return self.get_artifact(staged_hash)

        return self._txn(_work)

    def get_artifact(self, artifact_id: str) -> ArtifactEnvelope:
        r = self._conn.execute(
            "SELECT * FROM artifacts WHERE artifact_id=?", (artifact_id,)
        ).fetchone()
        if r is None:
            raise StoreError(f"artifact not found (not committed): {artifact_id}")
        data = json.loads(r[6])
        data["artifact_id"] = r[0]
        data["content_hash"] = r[1]
        data["created_at"] = r[7]
        return from_jsonable(ArtifactEnvelope, data)

    def get_artifact_by_hash(self, content_hash_val: str) -> Optional[ArtifactEnvelope]:
        r = self._conn.execute(
            "SELECT artifact_id FROM artifacts WHERE content_hash=?", (content_hash_val,)
        ).fetchone()
        return self.get_artifact(r[0]) if r is not None else None

    def list_artifacts(self, run_id: Optional[str] = None) -> List[ArtifactEnvelope]:
        if run_id is None:
            rows = self._conn.execute("SELECT artifact_id FROM artifacts ORDER BY created_at").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT artifact_id FROM artifacts WHERE run_id=? ORDER BY created_at", (run_id,)
            ).fetchall()
        return [self.get_artifact(r[0]) for r in rows]

    def verify_artifact(self, artifact_id: str) -> bool:
        """Verify the committed envelope, content file and raw evidence refs."""
        try:
            env = self.get_artifact(artifact_id)
            path = self._content_path(env.content_hash)
            if not path.exists():
                return False
            if sha256_hex(path.read_bytes()) != env.content_hash:
                return False
            if env.canonical_hash() != env.content_hash:
                return False
            for evidence_ref in env.evidence_refs:
                if evidence_ref.startswith("raw-output:") \
                        and not self.verify_adapter_raw_output(evidence_ref):
                    return False
            return True
        except (StoreError, OSError, TypeError, ValueError, json.JSONDecodeError):
            return False

    # ----------------------------------------------------- canonical facts

    def commit_facts(self, run_id: str, node_id: str, idempotency_key: str,
                     facts: List[CanonicalFact]) -> int:
        """Persist canonical facts.  Promotion gate: only deterministic-service
        and human-decision nodes may commit facts; AI candidates are rejected
        (fail closed, audited).  Deduplicated by (run_id, fact_hash)."""
        node = self.get_node_run(run_id, node_id)
        if node is None:
            raise StoreError(f"node not found: {run_id}/{node_id}")
        if node.node_type not in (NodeType.DETERMINISTIC_SERVICE, NodeType.HUMAN_DECISION):
            self.append_audit(domain.EVENT_PROMOTION_REJECTED,
                              {"run_id": run_id, "node_id": node_id,
                               "node_type": node.node_type.value, "fact_count": len(facts),
                               "reason": "ai_candidate cannot promote facts"}, run_id)
            raise PromotionForbiddenError(
                f"node {node_id} of type {node.node_type.value} cannot promote canonical facts"
            )
        prepared = []
        for f in facts:
            fh = f.canonical_hash()
            prepared.append(CanonicalFact(fact_type=f.fact_type, body=f.body,
                                          subject_id=f.subject_id, site_id=f.site_id,
                                          source_refs=list(f.source_refs),
                                          fact_id=f.fact_id or new_id("fact_"), fact_hash=fh))
        # Request hash over the facts CONTENT (fact_id is generated, so it must
        # not be part of the idempotency request identity).
        request_hash = content_hash(to_jsonable([
            {"fact_type": f.fact_type, "body": to_jsonable(f.body),
             "subject_id": f.subject_id, "site_id": f.site_id,
             "source_refs": list(f.source_refs)} for f in facts
        ]))

        def _work() -> int:
            inserted = 0
            for f in prepared:
                cur = self._conn.execute(
                    "SELECT 1 FROM canonical_facts WHERE run_id=? AND fact_hash=?",
                    (run_id, f.fact_hash),
                ).fetchone()
                if cur is not None:
                    continue
                self._conn.execute(
                    "INSERT INTO canonical_facts(run_id, fact_hash, fact_id, node_id, fact_json,"
                    " created_at) VALUES (?,?,?,?,?,?)",
                    (run_id, f.fact_hash, f.fact_id, node_id,
                     canonical_json(to_jsonable(f)), now_iso()),
                )
                inserted += 1
            self._append_audit_row(self._conn, domain.EVENT_FACT_COMMITTED,
                                   {"run_id": run_id, "node_id": node_id,
                                    "inserted": inserted, "total": len(prepared)}, run_id)
            return inserted

        return self._run_idempotent(idempotency_key, f"facts:{run_id}:{node_id}",
                                    request_hash, _work)

    def list_facts(self, run_id: str) -> List[CanonicalFact]:
        rows = self._conn.execute(
            "SELECT fact_json FROM canonical_facts WHERE run_id=? ORDER BY created_at", (run_id,)
        ).fetchall()
        return [from_jsonable(CanonicalFact, json.loads(r[0])) for r in rows]

    # ------------------------------------------------------- domain objects

    def put_domain_object(self, kind: str, object_id: str, obj: Any,
                          run_id: Optional[str] = None,
                          idempotency_key: Optional[str] = None) -> int:
        """Append-only versioned domain state (risks, queries, projections,
        ledgers, mode contracts...).  Same content at the latest version ->
        dedupe; new content -> next version; history never overwritten."""
        if not kind or not object_id:
            raise StoreError("kind and object_id are required")
        obj_hash = content_hash(to_jsonable(obj))
        immutable_label = (
            "adapter raw output"
            if kind == "adapter_raw_output"
            else "capability work assignment"
        )
        latest = self._conn.execute(
            "SELECT version, content_hash FROM domain_objects WHERE kind=? AND object_id=?"
            " ORDER BY version DESC LIMIT 1", (kind, object_id),
        ).fetchone()
        if latest is not None and latest[1] == obj_hash:
            # Dedupe is valid only when the stored bytes still match their
            # recorded hash and any kind-specific identity constraints.
            self.get_domain_object(kind, object_id, version=int(latest[0]))
            return int(latest[0])
        if latest is not None and kind in _IMMUTABLE_DOMAIN_OBJECT_KINDS:
            raise IdempotencyConflictError(
                "%s is immutable for one object identity" % immutable_label
            )

        def _work() -> int:
            # Re-read under BEGIN IMMEDIATE.  The optimistic read above is
            # only a fast path; it must never let concurrent writers create a
            # second version of an immutable object.
            current = self._conn.execute(
                "SELECT version, content_hash FROM domain_objects"
                " WHERE kind=? AND object_id=? ORDER BY version DESC LIMIT 1",
                (kind, object_id),
            ).fetchone()
            if current is not None and current[1] == obj_hash:
                persisted = self.get_domain_object(
                    kind, object_id, version=int(current[0])
                )
                if persisted is None:  # pragma: no cover - row just selected
                    raise StoreError("domain object replay references a missing record")
                return int(current[0])
            if current is not None and kind in _IMMUTABLE_DOMAIN_OBJECT_KINDS:
                raise IdempotencyConflictError(
                    "%s is immutable for one object identity" % immutable_label
                )
            version = int(current[0]) + 1 if current is not None else 1
            self._conn.execute(
                "INSERT INTO domain_objects(kind, object_id, run_id, version, object_json,"
                " content_hash, created_at) VALUES (?,?,?,?,?,?,?)",
                (kind, object_id, run_id, version, canonical_json(to_jsonable(obj)),
                 obj_hash, now_iso()),
            )
            self._append_audit_row(self._conn, domain.EVENT_DOMAIN_OBJECT_PUT,
                                   {"kind": kind, "object_id": object_id, "run_id": run_id,
                                    "version": version, "content_hash": obj_hash}, run_id)
            return version

        if idempotency_key:
            version = self._run_idempotent(
                idempotency_key, f"domain:{kind}:{object_id}", obj_hash, _work
            )
            if kind in _IMMUTABLE_DOMAIN_OBJECT_KINDS:
                # A ledger replay is not proof that the authoritative raw row
                # or frozen controller assignment still exists.  Validate the
                # exact stored version before reporting success.
                persisted = self.get_domain_object(
                    kind, object_id, version=int(version)
                )
                if persisted is None:
                    raise StoreError(
                        "%s idempotency replay references a missing record" % kind
                    )
            return int(version)
        return self._txn(_work)

    def get_domain_object(self, kind: str, object_id: str,
                          version: Optional[int] = None) -> Optional[Tuple[int, Any]]:
        """Return a verified versioned object or fail closed on corruption."""
        if version is None:
            r = self._conn.execute(
                "SELECT version, object_json, content_hash FROM domain_objects"
                " WHERE kind=? AND object_id=?"
                " ORDER BY version DESC LIMIT 1", (kind, object_id),
            ).fetchone()
        else:
            r = self._conn.execute(
                "SELECT version, object_json, content_hash FROM domain_objects"
                " WHERE kind=? AND object_id=?"
                " AND version=?", (kind, object_id, version),
            ).fetchone()
        if r is None:
            return None
        try:
            obj = json.loads(r[1])
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise StoreError(
                "domain object JSON is invalid: %s/%s@%s" % (kind, object_id, r[0])
            ) from exc
        try:
            verified_hash = content_hash(obj)
        except (TypeError, ValueError) as exc:
            raise StoreError(
                "domain object canonical hash is invalid: %s/%s@%s"
                % (kind, object_id, r[0])
            ) from exc
        if verified_hash != r[2]:
            raise StoreError(
                "domain object content hash mismatch: %s/%s@%s" % (kind, object_id, r[0])
            )
        if kind == "adapter_raw_output":
            self._validate_adapter_raw_output_object(object_id, obj)
        return (int(r[0]), obj)

    @staticmethod
    def _validate_adapter_raw_output_object(object_id: str, obj: Any) -> None:
        if not isinstance(obj, Mapping):
            raise StoreError("adapter raw output must be an object")
        raw_ref = obj.get("raw_output_ref")
        raw_hash = obj.get("content_hash")
        adapter_run_id = obj.get("run_id")
        raw_json = obj.get("raw_output_json")
        if not all(isinstance(value, str) and value for value in (
            raw_ref, raw_hash, adapter_run_id, raw_json,
        )):
            raise StoreError("adapter raw output identity fields are invalid")
        expected_ref = "raw-output:%s:%s" % (adapter_run_id, raw_hash)
        if raw_ref != expected_ref or object_id != "adapter-raw:%s" % raw_ref:
            raise StoreError("adapter raw output reference identity mismatch")
        if obj.get("immutable") is not True:
            raise StoreError("adapter raw output must remain immutable")
        try:
            raw_value = json.loads(raw_json)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise StoreError("adapter raw output JSON is invalid") from exc
        try:
            nested_hash = content_hash({"raw_output": raw_value})
        except (TypeError, ValueError) as exc:
            raise StoreError("adapter raw output nested content hash is invalid") from exc
        if nested_hash != raw_hash:
            raise StoreError("adapter raw output nested content hash mismatch")

    def verify_adapter_raw_output(self, raw_output_ref: str) -> bool:
        """Return True only for one present, immutable, fully verified raw record."""
        if not raw_output_ref:
            return False
        object_id = "adapter-raw:%s" % raw_output_ref
        try:
            row = self.get_domain_object("adapter_raw_output", object_id)
        except (StoreError, TypeError, ValueError, json.JSONDecodeError):
            return False
        return row is not None

    def list_domain_objects(self, kind: str) -> List[Tuple[str, int]]:
        rows = self._conn.execute(
            "SELECT object_id, MAX(version) FROM domain_objects WHERE kind=? GROUP BY object_id"
            " ORDER BY object_id", (kind,),
        ).fetchall()
        return [(r[0], int(r[1])) for r in rows]

    # ------------------------------------------------------------ checkpoints

    def save_checkpoint(self, run_id: str, node_id: str, state: Mapping[str, Any],
                        idempotency_key: Optional[str] = None) -> Checkpoint:
        state_hash = content_hash(to_jsonable(dict(state)))
        cid = content_hash({"run_id": run_id, "node_id": node_id, "state": to_jsonable(dict(state))})
        existing = self._conn.execute(
            "SELECT checkpoint_id FROM checkpoints WHERE checkpoint_id=?", (cid,)
        ).fetchone()
        if existing is not None:
            r = self._conn.execute(
                "SELECT checkpoint_id, state_json, content_hash, created_at FROM checkpoints"
                " WHERE checkpoint_id=?", (cid,),
            ).fetchone()
            return Checkpoint(checkpoint_id=r[0], run_id=run_id, node_id=node_id,
                              state=json.loads(r[1]), content_hash=r[2], created_at=r[3])

        def _work() -> Checkpoint:
            created = now_iso()
            self._conn.execute(
                "INSERT INTO checkpoints(checkpoint_id, run_id, node_id, state_json,"
                " content_hash, created_at) VALUES (?,?,?,?,?,?)",
                (cid, run_id, node_id, canonical_json(to_jsonable(dict(state))), state_hash, created),
            )
            self._append_audit_row(self._conn, domain.EVENT_CHECKPOINT_SAVED,
                                   {"checkpoint_id": cid, "run_id": run_id, "node_id": node_id,
                                    "content_hash": state_hash}, run_id)
            return Checkpoint(checkpoint_id=cid, run_id=run_id, node_id=node_id,
                              state=dict(state), content_hash=state_hash, created_at=created)

        return self._txn(_work)

    def load_checkpoint(self, run_id: str, node_id: str) -> Optional[Checkpoint]:
        r = self._conn.execute(
            "SELECT checkpoint_id, state_json, content_hash, created_at FROM checkpoints"
            " WHERE run_id=? AND node_id=? ORDER BY created_at DESC, checkpoint_id DESC LIMIT 1",
            (run_id, node_id),
        ).fetchone()
        if r is None:
            return None
        return Checkpoint(checkpoint_id=r[0], run_id=run_id, node_id=node_id,
                          state=json.loads(r[1]), content_hash=r[2], created_at=r[3])

    def list_checkpoints(self, run_id: str) -> List[Checkpoint]:
        rows = self._conn.execute(
            "SELECT checkpoint_id, node_id, state_json, content_hash, created_at FROM checkpoints"
            " WHERE run_id=? ORDER BY created_at, checkpoint_id", (run_id,),
        ).fetchall()
        return [Checkpoint(checkpoint_id=r[0], run_id=run_id, node_id=r[1],
                           state=json.loads(r[2]), content_hash=r[3], created_at=r[4])
                for r in rows]

    # ------------------------------------------------------------ recovery

    def find_orphan_artifacts(self) -> List[str]:
        """Files in the artifact dir with no committed reference (crash between
        stage and commit, or a leftover temp file).  Orphans are NEVER
        authoritative and are auditable/cleanable."""
        art = {r[0] for r in self._conn.execute("SELECT content_hash FROM artifacts").fetchall()}
        lst = {r[0] for r in self._conn.execute("SELECT content_hash FROM listing_snapshots").fetchall()}
        orphans = []
        for path in sorted(list(self.artifact_dir.glob("*.json"))
                           + list(self.artifact_dir.glob("*.tmp"))):
            stem = path.stem
            if path.suffix == ".tmp" or (stem not in art and stem not in lst):
                orphans.append(path.name)
        return orphans

    def recover(self) -> RecoveryReport:
        """Recovery protocol: verify audit chain + artifact integrity, list
        orphans and incomplete runs.  Never auto-completes anything.

        Fail closed: when the audit chain is broken, no recovery event is
        appended onto the broken chain (the report still carries the violation
        and the store is not mutated)."""
        audit_ok, first_bad, count = self.verify_audit_chain()
        integrity: List[str] = []
        for r in self._conn.execute("SELECT artifact_id FROM artifacts ORDER BY created_at").fetchall():
            if not self.verify_artifact(r[0]):
                integrity.append(f"artifact {r[0]}")
        for r in self._conn.execute("SELECT snapshot_id, content_hash FROM listing_snapshots").fetchall():
            path = self._content_path(r[1])
            if not path.exists() or sha256_hex(path.read_bytes()) != r[1]:
                integrity.append(f"listing {r[0]} ({r[1]})")
        for kind, object_id, version in self._conn.execute(
            "SELECT kind, object_id, version FROM domain_objects"
            " ORDER BY kind, object_id, version"
        ).fetchall():
            try:
                self.get_domain_object(kind, object_id, version=int(version))
            except StoreError:
                integrity.append("domain object %s/%s@%s" % (kind, object_id, version))
        incomplete: List[RunRecoveryState] = []
        for run in self.list_runs():
            if run.analysis_state == AnalysisState.COMPLETE:
                continue
            open_attempts = self._conn.execute(
                "SELECT COUNT(*) FROM node_attempts WHERE run_id=? AND status=?",
                (run.run_id, NodeStatus.RUNNING.value),
            ).fetchone()[0]
            node_states = [(r[0], r[1]) for r in self._conn.execute(
                "SELECT node_id, status FROM node_runs WHERE run_id=? ORDER BY node_id", (run.run_id,)
            ).fetchall()]
            if open_attempts or node_states or run.analysis_state == AnalysisState.RUNNING:
                incomplete.append(RunRecoveryState(run_id=run.run_id,
                                                   analysis_state=run.analysis_state.value,
                                                   open_attempts=int(open_attempts),
                                                   node_states=node_states))
        report = RecoveryReport(audit_ok=audit_ok, audit_first_bad_seq=first_bad,
                                audit_count=count, orphan_artifacts=self.find_orphan_artifacts(),
                                integrity_violations=integrity, incomplete_runs=incomplete)
        if audit_ok:
            self.append_audit(domain.EVENT_RECOVERY,
                              {"audit_ok": audit_ok, "orphans": len(report.orphan_artifacts),
                               "integrity_violations": len(integrity),
                               "incomplete_runs": len(incomplete)}, None)
        return report

    def cleanup_orphan_artifacts(self, quarantine_dir: Optional[Path] = None) -> List[str]:
        """Quarantine orphan artifact files (audited).  Quarantined orphans stay
        non-authoritative; nothing is deleted by default."""
        quarantine = Path(quarantine_dir) if quarantine_dir else (self.artifact_dir.parent / "orphan_quarantine")
        quarantine.mkdir(parents=True, exist_ok=True)
        moved: List[str] = []
        for name in self.find_orphan_artifacts():
            src = self.artifact_dir / name
            dst = quarantine / name
            if dst.exists():
                dst = quarantine / f"{name}.{new_id(prefix='dup_')}"
            os.replace(src, dst)
            moved.append(dst.name)
            self.append_audit(domain.EVENT_ORPHAN_CLEANUP,
                              {"file": name, "quarantine": str(dst), "reason": "unreferenced_artifact"},
                              None)
        return moved
