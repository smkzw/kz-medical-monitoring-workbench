"""Artifact, fact, domain-object, checkpoint and recovery operations."""

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

class StoreArtifactMixin:
    """Persist content-addressed outputs and perform recovery checks."""
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
        immutable_label = {
            "adapter_raw_output": "adapter raw output",
            "admission_project_identity_binding": "admission project identity binding",
            "capability_work_assignment": "capability work assignment",
        }.get(kind, kind)
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
