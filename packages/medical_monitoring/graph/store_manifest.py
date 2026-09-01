"""Execution-manifest and capability work-unit store operations."""

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

class StoreManifestMixin:
    """Persist manifest revisions and begin capability work units."""
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
