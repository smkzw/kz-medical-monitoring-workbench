"""SQLite persistence for the R2 kernel (Batch C; Design v1.1 section 12).

The :class:`R2Store` is the durable authority for user-visible monitoring
results: it persists the Run / source / snapshot / fact / risk / baseline /
publication references a dashboard needs, and guarantees that reopening
after a process restart returns the same committed snapshot and history.

Commit protocol (Design v1.1 section 12):
  1. Write the immutable, content-addressed artifact bytes FIRST (via
     :class:`~mm_r2.artifacts.ArtifactStore`), outside any transaction.
     The store verifies SHA-256 on write.  A crash here leaves an orphan
     file that is auditable/cleanable but never authoritative.
  2. In ONE explicit SQLite transaction (``BEGIN IMMEDIATE ... COMMIT``):
     insert the artifact reference, insert/advance the business state row,
     append audit event(s) with the hash chain, and advance the
     publication pointer.  Any exception rolls back the whole transaction,
     so the publication pointer never advances past un-committed state.
  3. The publication pointer advances only to a COMPLETE, readable
     artifact.  Incomplete / partial / not_evaluable / failed results can
     never become the current published result -- users must never open a
     half-finished dashboard.

Idempotency:
  A stable ``idempotency_key`` makes a duplicate save / retry return the
  same committed result without appending duplicate history.  The ledger
  records the request hash + result; a repeat with the same key returns
  the stored result.  A repeat with the same key but a different request
  hash is rejected (the key is stable per logical operation).

Recovery:
  ``open()`` re-opens an existing store and reconstructs the live view
  from the committed rows.  ``R2Store`` is safe to re-open after a clean
  shutdown or a crash (the SQLite WAL + the atomic commit protocol ensure
  the durable state is always internally consistent).

Hashes here are functional data-integrity / recovery mechanisms, not
security controls.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .artifacts import (
    ArtifactCompleteness,
    ArtifactEnvelope,
    ArtifactStore,
    StoredArtifact,
    make_envelope,
)
from .audit import AuditChain, AuditEvent
from .domain import (
    DomainValidationError,
    HashMismatchError,
    MmR2Error,
    canonical_json,
    content_hash,
    deep_freeze_json,
    from_dictable,
    new_id,
    now_iso,
    sha256_hex,
    to_dictable,
    validate_sha256_hex,
)

__all__ = [
    "StoreError",
    "IdempotencyConflictError",
    "SaveRequest",
    "SaveResult",
    "DashboardInputs",
    "R2Store",
]

# Publication-pointer advance is allowed only for COMPLETE artifacts whose
# completeness maps to a user-visible "finished" state.  Any other
# completeness (INCOMPLETE / PARTIAL / NOT_EVALUABLE / FAILED) blocks the
# publication advance: users must never open a half-finished dashboard.
_PUBLISHABLE_COMPLETENESS = frozenset({ArtifactCompleteness.COMPLETE})


class StoreError(MmR2Error):
    """Generic R2Store violation."""


class IdempotencyConflictError(StoreError):
    """A duplicate idempotency key with a different request hash."""


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SaveRequest:
    """A request to save a monitoring result.

    Carries the user-visible references (run / source / snapshot / facts /
    risks / baseline / publication), the business payload to persist as a
    content-addressed artifact, and the stable ``idempotency_key``.

    ``completeness`` governs whether the save may advance the publication
    pointer: only ``COMPLETE`` advances it.
    """

    run_id: str
    project_id: str
    snapshot_id: str
    source_revision_id: str
    payload: Dict[str, Any]
    idempotency_key: str
    completeness: str = ArtifactCompleteness.COMPLETE
    facts: Tuple[Tuple[str, str], ...] = ()        # (fact_id, fact_hash) refs
    risks: Tuple[Tuple[str, str], ...] = ()        # (risk_identity_id, state) refs
    baseline_id: str = ""
    request_note: str = ""
    actor: str = ""


@dataclass(frozen=True)
class SaveResult:
    """The committed result of a :meth:`R2Store.save`."""

    revision: int
    artifact_id: str
    content_hash: str
    published: bool
    idempotent_replay: bool
    saved_at: str


@dataclass(frozen=True)
class DashboardInputs:
    """The user-visible references a dashboard needs to open.

    Returned by :meth:`R2Store.dashboard_inputs`.  This is the read
    projection of the current published revision; it never exposes
    un-committed or incomplete state.
    """

    run_id: str
    project_id: str
    snapshot_id: str
    source_revision_id: str
    revision: int
    artifact_id: str
    content_hash: str
    baseline_id: str
    facts: Tuple[Tuple[str, str], ...]
    risks: Tuple[Tuple[str, str], ...]
    completeness: str
    actor: str
    saved_at: str


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_STORE_SCHEMA = """
CREATE TABLE IF NOT EXISTS r2_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS r2_publication_revisions (
    revision INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    source_revision_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_hash TEXT NOT NULL,
    completeness TEXT NOT NULL,
    baseline_id TEXT NOT NULL DEFAULT '',
    facts_json TEXT NOT NULL DEFAULT '[]',
    risks_json TEXT NOT NULL DEFAULT '[]',
    actor TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    saved_at TEXT NOT NULL,
    published INTEGER NOT NULL DEFAULT 0,
    published_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_r2_rev_run ON r2_publication_revisions(run_id);
CREATE INDEX IF NOT EXISTS idx_r2_rev_project ON r2_publication_revisions(project_id);
CREATE INDEX IF NOT EXISTS idx_r2_rev_published ON r2_publication_revisions(project_id, published);
CREATE TABLE IF NOT EXISTS r2_publication_pointer (
    project_id TEXT PRIMARY KEY,
    current_revision INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS r2_idempotency_ledger (
    idempotency_key TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS r2_artifact_refs (
    artifact_id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    run_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    completeness TEXT NOT NULL,
    envelope_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class R2Store:
    """SQLite authoritative store for user-visible monitoring results.

    All mutating operations execute exactly one explicit transaction
    (``BEGIN IMMEDIATE ... COMMIT/ROLLBACK``).  The audit chain and the
    publication pointer advance inside that same transaction.
    """

    ARTIFACT_TYPE = "monitoring_result_snapshot"

    def __init__(
        self,
        db_path: Path,
        artifact_dir: Path,
        *,
        local_user: Optional[str] = None,
    ) -> None:
        import getpass
        self.db_path = Path(db_path)
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self._local_user = local_user if local_user is not None else getpass.getuser()
        self._artifact_store = ArtifactStore(self.artifact_dir)
        self._conn = sqlite3.connect(str(self.db_path), isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA busy_timeout=10000")
        self._conn.executescript(_STORE_SCHEMA)
        self._audit = AuditChain(self._conn)
        self._audit.ensure_schema()
        self._conn.execute(
            "INSERT INTO r2_meta(key, value) VALUES('schema_version','1')"
            " ON CONFLICT(key) DO UPDATE SET value=excluded.value"
        )
        self._conn.execute(
            "INSERT OR IGNORE INTO r2_meta(key, value) VALUES('store_id', ?)",
            (new_id(),),
        )

    # -- lifecycle ---------------------------------------------------------

    @property
    def local_user(self) -> str:
        return self._local_user

    @property
    def artifact_store(self) -> ArtifactStore:
        return self._artifact_store

    @property
    def audit(self) -> AuditChain:
        return self._audit

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "R2Store":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- transaction helper ------------------------------------------------

    def _txn(self, fn: Any) -> Any:
        """Run fn() in one explicit transaction."""
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

    # -- save --------------------------------------------------------------

    def _request_hash(self, req: SaveRequest) -> str:
        """Canonical hash of the logical request (excludes volatile fields)."""
        return content_hash({
            "run_id": req.run_id,
            "project_id": req.project_id,
            "snapshot_id": req.snapshot_id,
            "source_revision_id": req.source_revision_id,
            "payload": to_dictable(deep_freeze_json(req.payload)),
            "completeness": req.completeness,
            "facts": list(req.facts),
            "risks": list(req.risks),
            "baseline_id": req.baseline_id,
            "request_note": req.request_note,
            "actor": req.actor,
        })

    def save(self, req: SaveRequest) -> SaveResult:
        """Persist a monitoring result atomically.

        Steps:
          1. Check the idempotency ledger.  If the key exists with the same
             request hash, return the stored result (idempotent replay).
             If the key exists with a different request hash, raise
             :class:`IdempotencyConflictError`.
          2. Write the content-addressed artifact bytes FIRST (outside any
             transaction).  SHA-256 is verified on write.
          3. In ONE transaction: insert the artifact ref, insert the
             publication revision, append audit event(s), advance the
             publication pointer if COMPLETE, and record the idempotency
             ledger entry.
        """
        self._validate_request(req)
        rh = self._request_hash(req)

        # 1) idempotency check (read outside the txn for the fast path)
        replay = self._idempotent_result(req.idempotency_key, rh)
        if replay is not None:
            return replay

        # 2) write the artifact bytes first (content-addressed, hash-verified)
        envelope = make_envelope(
            artifact_type=self.ARTIFACT_TYPE,
            artifact_version="1",
            input_hash=rh,
            payload_role="inference",
            completeness=req.completeness,
        )
        stored = self._artifact_store.put(envelope, deep_freeze_json(req.payload))

        # 3) one explicit transaction
        def _commit() -> SaveResult:
            return self._commit_save(req, stored, rh)

        return self._txn(_commit)

    def _idempotent_result(
        self, idempotency_key: str, request_hash: str,
    ) -> Optional[SaveResult]:
        """Return a prior result or reject reuse with a different request."""
        existing = self._conn.execute(
            "SELECT request_hash, result_json FROM r2_idempotency_ledger"
            " WHERE idempotency_key=?",
            (idempotency_key,),
        ).fetchone()
        if existing is None:
            return None
        if existing["request_hash"] != request_hash:
            raise IdempotencyConflictError(
                f"idempotency key {idempotency_key!r} already used "
                f"with a different request"
            )
        data = json.loads(existing["result_json"])
        data["idempotent_replay"] = True
        return SaveResult(**data)

    def _validate_request(self, req: SaveRequest) -> None:
        if not req.run_id:
            raise StoreError("SaveRequest.run_id is required")
        if not req.project_id:
            raise StoreError("SaveRequest.project_id is required")
        if not req.snapshot_id:
            raise StoreError("SaveRequest.snapshot_id is required")
        if not req.source_revision_id:
            raise StoreError("SaveRequest.source_revision_id is required")
        if not req.idempotency_key:
            raise StoreError("SaveRequest.idempotency_key is required")
        if req.completeness not in ArtifactCompleteness.values():
            raise StoreError(
                f"SaveRequest.completeness {req.completeness!r} invalid"
            )
        if not req.actor:
            raise StoreError("SaveRequest.actor is required")

    def _commit_save(
        self, req: SaveRequest, stored: StoredArtifact, rh: str,
    ) -> SaveResult:
        conn = self._conn
        # Recheck after BEGIN IMMEDIATE acquired the write lock.  Two callers
        # can both miss the fast-path lookup; the second must replay the first
        # committed result rather than leaking a raw UNIQUE constraint error.
        replay = self._idempotent_result(req.idempotency_key, rh)
        if replay is not None:
            return replay
        saved_at = now_iso()
        # Artifact ref (idempotent on content_hash).
        conn.execute(
            "INSERT OR IGNORE INTO r2_artifact_refs"
            "(artifact_id, content_hash, run_id, artifact_type, completeness,"
            " envelope_json, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                stored.envelope.artifact_id,
                stored.envelope.content_hash,
                req.run_id,
                stored.envelope.artifact_type,
                req.completeness,
                canonical_json(to_dictable(stored.envelope)),
                saved_at,
            ),
        )
        # The content address, not the fresh operational artifact_id, is the
        # durable identity of the stored bytes.  A second logical save can
        # legitimately produce the same content hash with a new envelope ID;
        # in that case reuse the already-registered artifact_id so every
        # revision keeps a valid reference.
        artifact_ref = conn.execute(
            "SELECT artifact_id FROM r2_artifact_refs WHERE content_hash=?",
            (stored.envelope.content_hash,),
        ).fetchone()
        if artifact_ref is None:
            raise StoreError(
                "content-addressed artifact was not registered before commit"
            )
        committed_artifact_id = artifact_ref["artifact_id"]
        # Publication revision row.
        cur = conn.execute(
            "INSERT INTO r2_publication_revisions"
            "(run_id, project_id, snapshot_id, source_revision_id, artifact_id,"
            " content_hash, idempotency_key, request_hash, completeness,"
            " baseline_id, facts_json, risks_json, actor, note, saved_at,"
            " published) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
            (
                req.run_id, req.project_id, req.snapshot_id,
                req.source_revision_id, committed_artifact_id,
                stored.envelope.content_hash, req.idempotency_key, rh,
                req.completeness,
                req.baseline_id,
                canonical_json(list(req.facts)),
                canonical_json(list(req.risks)),
                req.actor, req.request_note, saved_at,
            ),
        )
        revision = int(cur.lastrowid)

        # Audit: one business-history event referencing the committed revision.
        self._audit.append(
            "result_saved",
            {
                "revision": revision,
                "run_id": req.run_id,
                "project_id": req.project_id,
                "snapshot_id": req.snapshot_id,
                "artifact_id": committed_artifact_id,
                "content_hash": stored.envelope.content_hash,
                "completeness": req.completeness,
                "baseline_id": req.baseline_id,
                "actor": req.actor,
                "note": req.request_note,
            },
            run_id=req.run_id,
            conn=conn,
        )

        # Publication pointer: advance only if COMPLETE.
        published = req.completeness in _PUBLISHABLE_COMPLETENESS
        if published:
            conn.execute(
                "INSERT INTO r2_publication_pointer(project_id, current_revision, updated_at)"
                " VALUES (?,?,?)"
                " ON CONFLICT(project_id) DO UPDATE SET"
                " current_revision=excluded.current_revision,"
                " updated_at=excluded.updated_at",
                (req.project_id, revision, saved_at),
            )
            conn.execute(
                "UPDATE r2_publication_revisions SET published=1, published_at=?"
                " WHERE revision=?",
                (saved_at, revision),
            )
            self._audit.append(
                "publication_advanced",
                {
                    "project_id": req.project_id,
                    "revision": revision,
                    "content_hash": stored.envelope.content_hash,
                    "actor": req.actor,
                },
                run_id=req.run_id,
                conn=conn,
            )

        result = SaveResult(
            revision=revision,
            artifact_id=committed_artifact_id,
            content_hash=stored.envelope.content_hash,
            published=published,
            idempotent_replay=False,
            saved_at=saved_at,
        )
        # Idempotency ledger entry: store as plain JSON (not to_dictable,
        # which would wrap it in __r2_dataclass__ and break reconstruction).
        result_json = json.dumps({
            "revision": result.revision,
            "artifact_id": result.artifact_id,
            "content_hash": result.content_hash,
            "published": result.published,
            "idempotent_replay": result.idempotent_replay,
            "saved_at": result.saved_at,
        }, sort_keys=True, ensure_ascii=False)
        conn.execute(
            "INSERT INTO r2_idempotency_ledger"
            "(idempotency_key, scope, request_hash, result_json, created_at)"
            " VALUES (?,?,?,?,?)",
            (
                req.idempotency_key,
                f"save:{req.project_id}:{req.run_id}",
                rh,
                result_json,
                saved_at,
            ),
        )
        return result

    # -- read: dashboard inputs -------------------------------------------

    def current_revision(self, project_id: str) -> Optional[int]:
        """Return the current published revision, or None if none published."""
        row = self._conn.execute(
            "SELECT current_revision FROM r2_publication_pointer WHERE project_id=?",
            (project_id,),
        ).fetchone()
        if row is None:
            return None
        return int(row[0])

    def revision_row(self, revision: int) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT * FROM r2_publication_revisions WHERE revision=?",
            (revision,),
        ).fetchone()
        if row is None:
            raise StoreError(f"unknown revision {revision}")
        return row

    def dashboard_inputs(self, project_id: str) -> DashboardInputs:
        """Return the current published dashboard inputs.

        Raises :class:`StoreError` if nothing is published for this project.
        Users must never see un-committed or incomplete state, so this reads
        only the publication pointer (which advances only for COMPLETE
        results).
        """
        rev = self.current_revision(project_id)
        if rev is None:
            raise StoreError(
                f"no published result for project {project_id!r}"
            )
        row = self.revision_row(rev)
        self._ensure_readable_revision(row)
        return DashboardInputs(
            run_id=row["run_id"],
            project_id=row["project_id"],
            snapshot_id=row["snapshot_id"],
            source_revision_id=row["source_revision_id"],
            revision=int(row["revision"]),
            artifact_id=row["artifact_id"],
            content_hash=row["content_hash"],
            baseline_id=row["baseline_id"] or "",
            facts=tuple(tuple(x) for x in json.loads(row["facts_json"])),
            risks=tuple(tuple(x) for x in json.loads(row["risks_json"])),
            completeness=row["completeness"],
            actor=row["actor"] or "",
            saved_at=row["saved_at"],
        )

    def _ensure_readable_revision(self, row: sqlite3.Row) -> None:
        """Require a complete revision with a registered, readable artifact."""
        if row["completeness"] not in _PUBLISHABLE_COMPLETENESS:
            raise StoreError(
                f"revision {int(row['revision'])} is not complete and publishable"
            )
        ref = self._conn.execute(
            "SELECT * FROM r2_artifact_refs"
            " WHERE artifact_id=? AND content_hash=?",
            (row["artifact_id"], row["content_hash"]),
        ).fetchone()
        if ref is None:
            raise StoreError(
                f"revision {int(row['revision'])} has no matching artifact reference"
            )
        if (
            ref["completeness"] != row["completeness"]
            or ref["artifact_type"] != self.ARTIFACT_TYPE
        ):
            raise StoreError(
                f"revision {int(row['revision'])} artifact reference is inconsistent"
            )
        try:
            data = self.read_artifact(row["content_hash"])
            artifact = json.loads(data.decode("utf-8"))
            if (
                not isinstance(artifact, dict)
                or artifact.get("artifact_type") != self.ARTIFACT_TYPE
                or artifact.get("completeness") != row["completeness"]
                or artifact.get("input_hash") != row["request_hash"]
            ):
                raise StoreError(
                    f"revision {int(row['revision'])} artifact contract is inconsistent"
                )
        except (MmR2Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StoreError(
                f"revision {int(row['revision'])} artifact is not readable"
            ) from exc

    def read_artifact(self, content_hash: str) -> bytes:
        """Read + verify one artifact's bytes by content hash."""
        validate_sha256_hex(content_hash, "content_hash")
        return self._artifact_store.get(content_hash)

    def revision_history(self, project_id: str) -> List[sqlite3.Row]:
        """Return all committed revisions for a project, oldest first."""
        return list(self._conn.execute(
            "SELECT * FROM r2_publication_revisions WHERE project_id=?"
            " ORDER BY revision",
            (project_id,),
        ).fetchall())

    def published_history(self, project_id: str) -> List[int]:
        """Return the revisions that were ever published, in order."""
        return [
            int(r["revision"]) for r in self._conn.execute(
                "SELECT revision FROM r2_publication_revisions"
                " WHERE project_id=? AND published=1 ORDER BY revision",
                (project_id,),
            ).fetchall()
        ]

    # -- rollback ----------------------------------------------------------

    def rollback_to_published_revision(
        self, project_id: str, target_revision: int, *, actor: str,
    ) -> int:
        """Roll the publication pointer back to a prior published revision.

        The target must be an existing published revision for the project.
        This does NOT delete any history: revisions remain queryable.  It
        only moves the current publication pointer and appends an audit
        event.  Returns the new current revision.
        """
        if not actor:
            raise StoreError("rollback requires an actor")
        row = self._conn.execute(
            "SELECT * FROM r2_publication_revisions"
            " WHERE project_id=? AND revision=?",
            (project_id, target_revision),
        ).fetchone()
        if row is None:
            raise StoreError(
                f"revision {target_revision} not found for project "
                f"{project_id!r}"
            )
        if not int(row["published"]):
            raise StoreError(
                f"revision {target_revision} was never published; cannot roll "
                f"back to an unpublished revision"
            )
        self._ensure_readable_revision(row)

        def _do() -> int:
            conn = self._conn
            saved_at = now_iso()
            conn.execute(
                "UPDATE r2_publication_pointer SET current_revision=?, updated_at=?"
                " WHERE project_id=?",
                (target_revision, saved_at, project_id),
            )
            self._audit.append(
                "publication_rolled_back",
                {
                    "project_id": project_id,
                    "target_revision": target_revision,
                    "actor": actor,
                },
                conn=conn,
            )
            return target_revision

        return self._txn(_do)

    # -- pre-commit interruption simulation (for tests) -------------------

    def simulate_pre_commit_interruption(self) -> None:
        """Begin a transaction then roll it back, simulating a crash before
        COMMIT.  Used by the idempotency / interruption test to prove that a
        pre-commit interruption leaves no authoritative state and the same
        idempotency key can still complete on retry."""
        def _interrupt():
            # Insert a row inside the txn, then raise to force rollback.
            self._conn.execute(
                "INSERT INTO r2_publication_revisions"
                "(run_id, project_id, snapshot_id, source_revision_id,"
                " artifact_id, content_hash, idempotency_key, request_hash,"
                " completeness, saved_at)"
                " VALUES ('interrupted','p','s','r','a','x','k','h',"
                " 'incomplete','t')"
            )
            raise StoreError("simulated pre-commit interruption")

        try:
            self._txn(_interrupt)
        except StoreError:
            pass  # expected
