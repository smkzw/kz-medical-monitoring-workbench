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

from ..domain import execution as domain
from ..domain.execution import (
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

from ..domain.schema_shape import connection_shape, shape_from_ddl


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
    "admission_project_identity_binding",
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


def _runtime_schema_integrity(connection: sqlite3.Connection) -> None:
    """Run the full read-only integrity gate on an open connection."""

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


def _open_schema_probe_connection(db_path: Path) -> sqlite3.Connection:
    """Open the database read-only for the integrity gate.

    A ``mode=ro`` URI connection cannot create the ``-shm`` sidecar that a
    persistently WAL-mode database requires, so the connect itself may
    succeed while the first query fails with "unable to open database
    file" whenever no other process currently holds the sidecar open.
    That is an availability condition of the probe, not evidence of a
    schema problem: retry briefly, then fall back to the read-write
    driver pinned read-only via ``query_only`` (which the gate requires
    on every connection anyway).
    """

    uri = "file:" + quote(str(db_path.resolve()), safe="/") + "?mode=ro"
    last_error: Optional[Exception] = None
    for attempt in range(3):
        connection: Optional[sqlite3.Connection] = None
        try:
            connection = sqlite3.connect(uri, uri=True, isolation_level=None)
            _runtime_schema_integrity(connection)
            return connection
        except sqlite3.OperationalError as exc:
            last_error = exc
            if connection is not None:
                connection.close()
            if "unable to open database file" not in str(exc):
                raise
            time.sleep(0.15 * (attempt + 1))
    connection = sqlite3.connect(str(db_path), isolation_level=None)
    try:
        _runtime_schema_integrity(connection)
    except Exception:
        connection.close()
        raise
    return connection


def _assert_current_schema(db_path: Path) -> None:
    """Fail closed before opening an existing non-current runtime database."""
    if not db_path.exists():
        return
    connection: Optional[sqlite3.Connection] = None
    try:
        connection = _open_schema_probe_connection(db_path)
    except (OSError, sqlite3.Error, TypeError, ValueError) as exc:
        raise StoreError("unsupported schema") from exc
    finally:
        if connection is not None:
            connection.close()
