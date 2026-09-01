"""Node-run and capability-attempt journal operations."""

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

class StoreAttemptMixin:
    """Own node and transport-attempt lifecycle mutations."""
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
