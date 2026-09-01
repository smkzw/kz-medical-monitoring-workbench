"""Store lifecycle, audit, source, snapshot and run-state operations."""

from __future__ import annotations

from .store_common import *
from .store_common import (
    _runtime_schema_shape,
    _shape_from_ddl,
    _ANALYSIS_TRANSITIONS,
    _REVIEW_TRANSITIONS,
    _OUTPUT_ORDER,
    _WORK_UNIT_IDENTITY_KEYS,
    _IMMUTABLE_DOMAIN_OBJECT_KINDS,
    _CAPABILITY_ASSIGNMENT_KIND,
    _CAPABILITY_ASSIGNMENT_SCHEMA,
    _RESERVED_INTERNAL_AUDIT_EVENTS,
    _IdempotencyLedgerConflict,
    _RuntimeAttemptJournal,
    _SCHEMA,
    _build_current_runtime_schema_shape,
    _CURRENT_RUNTIME_SCHEMA_SHAPE,
    _assert_current_schema,
)

class StoreBaseMixin:
    """Own the connection and the base transaction/state operations."""
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
