"""Read-only project verification over the frozen authority chain."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from ..graph.store import Store
from . import project_backup as _backup
from .project_audit import ProjectAuditEventKind
from .project_verifier_core import (
    VERIFIER_VERSION,
    _BACKUP_RECOVERY_STATES,
    _BACKUP_RETAINED_STATE,
    _DEFAULT_MESSAGE,
    _DEFAULT_NEXT_ACTION,
    _EVIDENCE_DIRS,
    _MIGRATION_RECOVERY_STATES,
    _MIGRATION_RETAINED_STATE,
    _MIGRATION_RETRYABLE_STATE,
    _ROLLBACK_EVIDENCE_PREFIX,
    _VerificationIssues,
    _WorkspaceSnapshot,
    ProjectAuditBridge,
    ProjectVerificationError,
    ProjectVerificationResult,
    _digest,
    _event_id,
    _event_kind,
    _event_mapping,
    _event_operation,
    _json_value,
    _new_audit_ledger,
    _normalise_hash,
    _normalise_project_id,
    _quick_check,
    _read_rows,
    _readonly_connection,
    _result_code,
    _safe_reason,
    _walk_digest_roots,
)
from .schema_manifest import (
    LAUNCH_DB_RELATIVE_PATH,
    MEMBER_ORDER,
    RUNTIME_DB_RELATIVE_PATH,
    SchemaClassification,
    inspect_project_schema,
)

class ProjectVerifier:
    """Fixed-order, read-only project verifier with own root event pair."""

    def __init__(
        self,
        runtime_root: str | Path,
        canonical_project_id: str,
        *,
        project_dir: Optional[str | Path] = None,
        audit_ledger_factory: Optional[Callable[..., Any]] = None,
        audit_ledger: Any = None,
        principal_snapshot_hash: str = "",
        authorization_decision_hash: str = "",
        requested_domain_set: Optional[Sequence[str]] = None,
    ) -> None:
        self.runtime_root = Path(runtime_root)
        self.canonical_project_id = _normalise_project_id(canonical_project_id)
        self.project_dir = Path(project_dir) if project_dir is not None else (
            self.runtime_root / self.canonical_project_id
        )
        self.audit_ledger_factory = audit_ledger_factory
        self._ledger = audit_ledger
        self._owns_ledger = audit_ledger is None
        self._principal_snapshot_hash = _normalise_hash(
            principal_snapshot_hash, "synthetic-principal"
        )
        self._authorization_decision_hash = _normalise_hash(
            authorization_decision_hash, "synthetic-authorization"
        )
        domains = tuple(requested_domain_set or (
            "root",
            "identity",
            "operation",
            "live",
            "r1",
            "publication",
            "continuity",
            "verification",
        ))
        self.requested_domain_set = tuple(
            _safe_reason(domain, "domain") for domain in domains
        )

    def _get_ledger(self) -> Any:
        if self._ledger is None:
            self._ledger = _new_audit_ledger(
                self.runtime_root,
                self.canonical_project_id,
                self.audit_ledger_factory,
            )
        return self._ledger

    def _bridge(self) -> ProjectAuditBridge:
        return ProjectAuditBridge(
            self._get_ledger(),
            self.canonical_project_id,
            principal_snapshot_hash=self._principal_snapshot_hash,
            authorization_decision_hash=self._authorization_decision_hash,
        )

    def close(self) -> None:
        ledger = self._ledger
        self._ledger = None
        if ledger is not None and self._owns_ledger:
            close = getattr(ledger, "close", None)
            if callable(close):
                close()

    def __enter__(self) -> "ProjectVerifier":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _snapshot(self) -> _WorkspaceSnapshot:
        issues: list[str] = []
        try:
            inspection = inspect_project_schema(self.project_dir)
        except Exception:
            inspection = None
            issues.append("schema_inspection_failed")
        try:
            files, file_issues = _walk_digest_roots(self.project_dir)
            issues.extend(file_issues)
        except (OSError, ValueError):
            files = []
            issues.append("workspace_unreadable")
        members: list[dict[str, Any]] = []
        if inspection is not None:
            for name in MEMBER_ORDER:
                report = inspection.members.get(name)
                if report is None:
                    members.append({"member": name, "present": False})
                    continue
                members.append(
                    {
                        "member": name,
                        "classification": str(report.classification.value),
                        "schema_version": report.schema_version,
                        "reason_code": report.reason_code,
                        "present": bool(report.present),
                        "quick_check": report.quick_check,
                        "foreign_key_violations": int(report.foreign_key_violations),
                        "shape_digest": report.shape_digest,
                        "marker_value": report.marker_value,
                    }
                )
        fingerprint = _digest(
            {
                "verifier_version": VERIFIER_VERSION,
                "members": members,
                "files": files,
                "workspace_present": self.project_dir.exists(),
                "snapshot_issues": sorted(set(issues)),
            }
        )
        return _WorkspaceSnapshot(fingerprint, inspection, tuple(sorted(set(issues))))

    def snapshot_fingerprint(self) -> str:
        """Return a deterministic workspace fingerprint without audit writes."""

        return self._snapshot().fingerprint

    def _append_verification_started(self, fingerprint: str) -> Any:
        bridge = self._bridge()
        return bridge._append(
            ProjectAuditEventKind.VERIFICATION_STARTED.value,
            operation_kind="verification",
            before_digest=fingerprint,
            after_digest=fingerprint,
            result_code="verification_started",
            reason_code="verification_started",
            verifier_version=VERIFIER_VERSION,
            snapshot_fingerprint=fingerprint,
            requested_domain_set=list(self.requested_domain_set),
        )

    def _append_verification_completed(
        self,
        result: str,
        fingerprint: str,
        anchors: Mapping[str, str],
        reason_enum: str,
    ) -> Any:
        bridge = self._bridge()
        exact = dict(anchors)
        return bridge._append(
            ProjectAuditEventKind.VERIFICATION_COMPLETED.value,
            operation_kind="verification",
            before_digest=fingerprint,
            after_digest=fingerprint,
            domain_anchors=exact,
            result_code=_result_code(result),
            reason_code=reason_enum,
            verifier_version=VERIFIER_VERSION,
            snapshot_fingerprint=fingerprint,
            verification_result=_result_code(result),
            exact_domain_anchors=exact,
            reason_enum=reason_enum,
        )

    def verify(self) -> ProjectVerificationResult:
        # Fingerprinting is a read-only preparation step.  It deliberately
        # excludes the root audit DB so repeated verification of one snapshot
        # yields the same fingerprint despite the appended event pair.
        snapshot = self._snapshot()
        fingerprint = snapshot.fingerprint
        issues = _VerificationIssues()
        for issue in snapshot.issues:
            if issue.endswith("symlink") or issue == "evidence_not_directory":
                issues.anomaly(issue)
            else:
                issues.recovery(issue)

        # The root event chain is checked before this invocation's own events.
        # An empty project chain is a valid first-verification baseline.
        started_event: Any = None
        try:
            ledger = self._get_ledger()
            events = self._audit_events(ledger, self.canonical_project_id)
            chain = self._verify_root_chain(ledger, self.canonical_project_id)
            if not events and not chain[0]:
                # ProjectAuditLedger has no per-project head until first append.
                # Other failed empty-chain implementations still indicate a
                # malformed root and are handled below.
                head = self._audit_head(ledger, self.canonical_project_id)
                if head is None or int(head.get("head_seq", 0)) == 0:
                    chain = (True, None, 0)
            if not chain[0]:
                issues.anomaly("root_audit_chain_mismatch")
                issues.anchor("root_ledger_anchor", {
                    "chain_ok": False,
                    "event_count": int(chain[2]),
                    "first_bad_seq": chain[1],
                })
                return self._result_from_issues(
                    issues,
                    fingerprint,
                    started_event=None,
                    completed_event=None,
                )
            issues.anchor("root_ledger_anchor", {
                "chain_ok": True,
                "event_count": int(chain[2]),
                "first_bad_seq": chain[1],
            })
            started_event = self._append_verification_started(fingerprint)
        except ProjectVerificationError:
            # A tampered root may reject all further appends.  Preserve the
            # deterministic anomaly result rather than hiding it behind a
            # transport exception; healthy roots always append both events.
            if issues.anomalies:
                return self._result_from_issues(
                    issues,
                    fingerprint,
                    started_event=None,
                    completed_event=None,
                )
            raise
        except Exception as exc:
            raise ProjectVerificationError(_safe_reason(
                getattr(exc, "code", "audit_ledger_unavailable"),
                "audit_ledger_unavailable",
            )) from exc

        try:
            # 1. Root schema/scope/event sequence/hash/head.
            self._check_root_scope(issues, events)
            # 2. Project identity/package/source/plan/operation.
            self._check_project_identity(issues)
            # 3. Current operation projection versus last boundary.
            self._check_operation_projection(issues)
            # 4. Live/staging/rollback/marker and independent SQLite reopen.
            self._check_live_evidence(issues, snapshot)
            # 5. R1 source/run/artifact/audit closure, using the public method.
            self._check_r1(issues)
            # 6. Publication identity/R5/R6/receipt/exact output.
            self._check_publication(issues)
            # 7. Continuity baseline/target/items/digest.
            self._check_continuity(issues)
            # 8. Own verification event anchors are appended below.
        except Exception:
            # The public surface must remain bounded even for an unexpected
            # read-only adapter failure.  The event still records recovery need.
            issues.recovery("verification_read_failed")

        result = issues.result
        try:
            completed_event = self._append_verification_completed(
                result,
                fingerprint,
                issues.anchors,
                issues.reason_enum,
            )
        except ProjectVerificationError:
            raise
        return self._result_from_issues(
            issues,
            fingerprint,
            started_event=started_event,
            completed_event=completed_event,
        )

    def _result_from_issues(
        self,
        issues: _VerificationIssues,
        fingerprint: str,
        *,
        started_event: Any,
        completed_event: Any,
    ) -> ProjectVerificationResult:
        result = issues.result
        return ProjectVerificationResult(
            result=result,
            message=_DEFAULT_MESSAGE[result],
            next_action=_DEFAULT_NEXT_ACTION[result],
            snapshot_fingerprint=fingerprint,
            before_digest=fingerprint,
            after_digest=fingerprint,
            reason_enum=issues.reason_enum,
            domain_anchors=dict(issues.anchors),
            started_event_id=_event_id(started_event) or None,
            completed_event_id=_event_id(completed_event) or None,
        )

    @staticmethod
    def _verify_root_chain(
        ledger: Any,
        canonical_project_id: str,
    ) -> tuple[bool, Optional[int], int]:
        method = getattr(ledger, "verify_chain", None)
        if not callable(method):
            method = getattr(ledger, "verify_audit_chain", None)
        if not callable(method):
            method = getattr(ledger, "verify", None)
        if not callable(method):
            raise ProjectVerificationError("audit_verify_unavailable")
        try:
            value = method(canonical_project_id)
        except TypeError:
            value = method()
        if isinstance(value, tuple):
            if len(value) >= 3:
                return bool(value[0]), value[1], int(value[2])
            if value:
                return bool(value[0]), None, 0
        if isinstance(value, list):
            if len(value) >= 3:
                return bool(value[0]), value[1], int(value[2])
            if value:
                return bool(value[0]), None, 0
        return bool(value), None, 0

    @staticmethod
    def _audit_head(
        ledger: Any,
        canonical_project_id: str,
    ) -> Optional[Mapping[str, Any]]:
        method = getattr(ledger, "head", None)
        if not callable(method):
            return None
        try:
            value = method(canonical_project_id)
        except Exception:
            return None
        data = _event_mapping(value)
        if data:
            return data
        if isinstance(value, Mapping):
            return value
        return None

    @staticmethod
    def _audit_events(
        ledger: Any,
        canonical_project_id: str,
    ) -> tuple[Any, ...]:
        method = getattr(ledger, "events", None)
        if not callable(method):
            method = getattr(ledger, "list_events", None)
        if not callable(method):
            method = getattr(ledger, "events_for_project", None)
        if not callable(method):
            raise ProjectVerificationError("audit_events_unavailable")
        try:
            value = method(canonical_project_id)
        except TypeError:
            value = method()
        if value is None:
            return ()
        return tuple(value)

    def _check_root_scope(
        self,
        issues: _VerificationIssues,
        events: Sequence[Any],
    ) -> None:
        scoped: list[dict[str, Any]] = []
        for event in events:
            data = _event_mapping(event)
            project = str(
                data.get("canonical_project_id", data.get("project_scope", "")) or ""
            )
            if project and project != self.canonical_project_id:
                issues.anomaly("root_scope_mismatch")
            scoped.append({
                "seq": data.get("project_seq", data.get("sequence", 0)),
                "kind": _event_kind(event),
                "event_id": _event_id(event),
                "operation": _event_operation(event),
                "boundary": data.get("boundary_token", ""),
                "chain": data.get("chain_hash", ""),
            })
        issues.anchor("root_event_anchor", scoped)

    def _check_project_identity(self, issues: _VerificationIssues) -> None:
        path = self.project_dir / RUNTIME_DB_RELATIVE_PATH
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.recovery("runtime_unavailable")
            issues.anchor("identity_anchor", {"runtime": "missing"})
            return
        try:
            quick, foreign_count = _quick_check(connection)
            if quick != "ok" or foreign_count:
                issues.anomaly("runtime_integrity_failed")
            projects = _read_rows(
                connection,
                "projects",
                ("project_id", "is_synthetic", "created_at"),
            )
            source_rows = _read_rows(
                connection,
                "source_revisions",
                ("revision_id", "project_id", "source_type", "version", "content_hash", "valid_from"),
            )
            snapshot_rows = _read_rows(
                connection,
                "listing_snapshots",
                ("snapshot_id", "project_id", "revision_id", "snapshot_version", "content_hash", "row_count", "is_synthetic"),
            )
            run_rows = _read_rows(
                connection,
                "monitoring_runs",
                ("run_id", "project_id", "mode", "data_cutoff", "source_revision_id", "execution_basis", "analysis_state", "evidence_state", "review_state", "output_state", "manifest_revision"),
            )
            project_rows = projects
            for row in project_rows + source_rows + snapshot_rows + run_rows:
                row_project = row.get("project_id")
                if row_project and str(row_project) != self.canonical_project_id:
                    issues.anomaly("project_identity_mismatch")
            for row in projects:
                if "is_synthetic" in row and int(row.get("is_synthetic") or 0) != 1:
                    issues.anomaly("non_synthetic_project")
            revision_ids = {str(row.get("revision_id")) for row in source_rows}
            for row in snapshot_rows:
                if row.get("revision_id") and str(row["revision_id"]) not in revision_ids:
                    issues.anomaly("source_snapshot_mismatch")
            source_id_set = revision_ids
            for row in run_rows:
                if row.get("source_revision_id") and str(row["source_revision_id"]) not in source_id_set:
                    issues.anomaly("run_source_mismatch")
            issues.anchor("identity_anchor", {
                "projects": project_rows,
                "sources": source_rows,
                "snapshots": snapshot_rows,
                "runs": run_rows,
            })
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("identity_read_failed")
        finally:
            connection.close()

    def _check_operation_projection(self, issues: _VerificationIssues) -> None:
        path = self.runtime_root / _backup.OPERATIONS_DB_NAME
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.anchor("operation_anchor", [])
            return
        try:
            rows = _read_rows(
                connection,
                "backup_operations",
                (
                    "operation_id",
                    "operation_kind",
                    "canonical_project_id",
                    "status",
                    "progress_percent",
                    "terminal_outcome",
                    "error_code",
                    "rollback_path",
                    "staging_path",
                    "package_path",
                    "updated_at",
                ),
            )
            scoped = [
                row for row in rows
                if str(row.get("canonical_project_id") or "") == self.canonical_project_id
            ]
            if len(scoped) != len(rows):
                issues.anomaly("operation_scope_mismatch")
            boundary_events = self._audit_events(
                self._get_ledger(),
                self.canonical_project_id,
            )
            last_boundary: dict[str, dict[str, Any]] = {}
            for event in boundary_events:
                kind = _event_kind(event)
                if kind not in {
                    ProjectAuditEventKind.BOUNDARY_INTENT.value,
                    ProjectAuditEventKind.BOUNDARY_COMMITTED.value,
                    ProjectAuditEventKind.BOUNDARY_VERIFIED.value,
                }:
                    continue
                operation = _event_operation(event)
                if not operation:
                    continue
                last_boundary[operation] = {
                    "kind": kind,
                    "payload": _event_mapping(event).get("payload", {}),
                }
            projection: list[dict[str, Any]] = []
            for row in scoped:
                operation = str(row.get("operation_id") or "")
                status = str(row.get("status") or "")
                if status in _MIGRATION_RECOVERY_STATES or status in _BACKUP_RECOVERY_STATES:
                    issues.recovery("operation_recovery_pending")
                if status in {_MIGRATION_RETAINED_STATE, _BACKUP_RETAINED_STATE}:
                    issues.recovery("operation_retained_for_triage")
                if status == _MIGRATION_RETRYABLE_STATE:
                    issues.recovery("explicit_retry_required")
                if row.get("rollback_path") or row.get("staging_path"):
                    # Rollback evidence is expected to remain until this
                    # verifier completes and the coordinator emits the
                    # release event.  Its presence alone must not deadlock
                    # release; active/non-terminal projections are recovery.
                    if status not in {
                        "completed",
                        "available",
                        "already_current",
                        "kept_current",
                        "rolled_back",
                        "ready_for_confirmation",
                        "confirmed",
                    }:
                        issues.recovery("rollback_evidence_retained")
                boundary = last_boundary.get(operation)
                if boundary is not None:
                    payload = boundary.get("payload")
                    if not isinstance(payload, Mapping):
                        issues.anomaly("boundary_payload_invalid")
                    else:
                        observed = payload.get("observed_durable_phase")
                        if (
                            boundary.get("kind") in {
                                ProjectAuditEventKind.BOUNDARY_COMMITTED.value,
                                ProjectAuditEventKind.BOUNDARY_VERIFIED.value,
                            }
                            and observed
                            and str(observed) != status
                        ):
                            issues.recovery("operation_boundary_mismatch")
                        if (
                            boundary.get("kind") == ProjectAuditEventKind.BOUNDARY_INTENT.value
                            and status not in {"requested", "received", "confirmed", "staging"}
                        ):
                            issues.recovery("boundary_commit_missing")
                projection.append({
                    "operation": operation,
                    "kind": str(row.get("operation_kind") or ""),
                    "status": status,
                    "progress": row.get("progress_percent"),
                    "terminal": row.get("terminal_outcome"),
                    "error": row.get("error_code"),
                    "has_rollback": bool(row.get("rollback_path")),
                    "has_staging": bool(row.get("staging_path")),
                    "updated": row.get("updated_at"),
                })
            issues.anchor("operation_anchor", projection)
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("operation_read_failed")
        finally:
            connection.close()

    def _check_live_evidence(
        self,
        issues: _VerificationIssues,
        snapshot: _WorkspaceSnapshot,
    ) -> None:
        if snapshot.inspection is None:
            issues.recovery("schema_inspection_failed")
            return
        classification = snapshot.inspection.classification
        if classification is SchemaClassification.LEGACY:
            issues.recovery("legacy_project_requires_recovery")
        elif classification is SchemaClassification.UNKNOWN:
            issues.recovery("schema_unknown")
        elif classification is SchemaClassification.CORRUPT:
            issues.anomaly("schema_corrupt")
        elif classification is not SchemaClassification.CURRENT:
            issues.recovery("schema_not_current")
        for base in (self.runtime_root, self.project_dir):
            if base.is_symlink():
                issues.anomaly("evidence_symlink")
                continue
            for name in _EVIDENCE_DIRS:
                path = base / name
                if path.is_symlink():
                    issues.anomaly("evidence_symlink")
                elif path.exists():
                    if not path.is_dir():
                        issues.anomaly("evidence_not_directory")
                    else:
                        try:
                            if any(path.iterdir()):
                                issues.recovery("recovery_evidence_present")
                        except OSError:
                            issues.recovery("recovery_evidence_unreadable")
        try:
            rollback_entries = sorted(
                entry
                for entry in self.runtime_root.iterdir()
                if entry.name.startswith(_ROLLBACK_EVIDENCE_PREFIX)
            )
        except OSError:
            rollback_entries = []
            issues.recovery("recovery_evidence_unreadable")
        for path in rollback_entries:
            if path.is_symlink():
                issues.anomaly("evidence_symlink")
            elif not path.is_dir():
                issues.anomaly("evidence_not_directory")
            else:
                issues.recovery("recovery_evidence_present")
        paths_seen: set[str] = set()
        for report in snapshot.inspection.members.values():
            if not report.present:
                continue
            path = Path(report.path)
            key = str(path)
            if key in paths_seen:
                continue
            paths_seen.add(key)
            try:
                connection = _readonly_connection(path)
            except (OSError, sqlite3.Error):
                issues.anomaly("member_reopen_failed")
                continue
            try:
                quick, foreign_count = _quick_check(connection)
                if quick != "ok" or foreign_count:
                    issues.anomaly("member_integrity_failed")
            except (OSError, sqlite3.Error):
                issues.anomaly("member_reopen_failed")
            finally:
                connection.close()
        issues.anchor("live_anchor", {
            "classification": classification.value,
            "member_count": len(snapshot.inspection.members),
            "snapshot_issues": list(snapshot.issues),
        })

    def _check_r1(self, issues: _VerificationIssues) -> None:
        path = self.project_dir / RUNTIME_DB_RELATIVE_PATH
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.recovery("r1_runtime_unavailable")
            issues.anchor("r1_anchor", {"available": False})
            return
        try:
            quick, foreign_count = _quick_check(connection)
            if quick != "ok" or foreign_count:
                issues.anomaly("r1_runtime_integrity_failed")
            # Call the established public verifier directly.  Do not copy its
            # chain algorithm into R7.
            readonly_store = Store.__new__(Store)
            readonly_store._conn = connection
            readonly_store.artifact_dir = self.project_dir / "artifacts"
            chain = readonly_store.verify_audit_chain()
            if not isinstance(chain, tuple) or not chain or not bool(chain[0]):
                issues.anomaly("r1_audit_chain_mismatch")
            artifact_rows = _read_rows(
                connection,
                "artifacts",
                ("artifact_id", "content_hash", "run_id", "node_id", "artifact_type", "completeness"),
            )
            artifact_checks: list[dict[str, Any]] = []
            for row in artifact_rows:
                artifact_id = str(row.get("artifact_id") or "")
                if not artifact_id or not str(row.get("content_hash") or ""):
                    issues.anomaly("artifact_identity_invalid")
                    continue
                try:
                    valid = bool(readonly_store.verify_artifact(artifact_id))
                except Exception:
                    valid = False
                if not valid:
                    issues.anomaly("artifact_integrity_failed")
                artifact_checks.append({
                    "artifact": artifact_id,
                    "content_hash": row.get("content_hash"),
                    "run": row.get("run_id"),
                    "valid": valid,
                })
            try:
                orphans = tuple(readonly_store.find_orphan_artifacts())
            except Exception:
                orphans = ()
            if orphans:
                issues.recovery("orphan_artifact_evidence")
            issues.anchor("r1_anchor", {
                "quick_check": quick,
                "foreign_key_violations": foreign_count,
                "audit": chain,
                "artifacts": artifact_checks,
                "orphans": sorted(str(item) for item in orphans),
            })
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("r1_read_failed")
        finally:
            connection.close()

    def _check_publication(self, issues: _VerificationIssues) -> None:
        path = self.project_dir / LAUNCH_DB_RELATIVE_PATH
        if not path.exists():
            issues.anchor("publication_anchor", [])
            return
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.anomaly("publication_reopen_failed")
            issues.anchor("publication_anchor", {"available": False})
            return
        try:
            quick, foreign_count = _quick_check(connection)
            if quick != "ok" or foreign_count:
                issues.anomaly("publication_integrity_failed")
            registry = _read_rows(
                connection,
                "r7_launch_registry",
                ("run_id", "project_id", "public_run_token", "current_snapshot_token", "source_revision_id", "run_state", "result_available"),
            )
            publications = _read_rows(
                connection,
                "r7_result_publications",
                (
                    "run_id", "project_id", "public_run_token", "result_context_token",
                    "publication_revision", "publication_fingerprint", "snapshot_token",
                    "source_revision_id", "publication_state", "receipt_identities_json",
                    "receipt_set_digest", "r5_authority_packet_id", "r5_authority_packet_digest",
                    "s4_authority_packet_identities_json", "s4_authority_packet_digests_json",
                    "r6_output_set_digest", "artifact_member_ids_json", "artifact_member_set_digest",
                ),
            )
            registry_by_run = {
                str(row.get("run_id") or ""): row for row in registry
            }
            projected_publications: list[dict[str, Any]] = []
            for row in publications:
                if str(row.get("project_id") or "") != self.canonical_project_id:
                    issues.anomaly("publication_scope_mismatch")
                run_id = str(row.get("run_id") or "")
                launch = registry_by_run.get(run_id)
                if launch is None:
                    issues.anomaly("publication_run_missing")
                elif str(row.get("public_run_token") or "") != str(launch.get("public_run_token") or ""):
                    issues.anomaly("publication_identity_mismatch")
                state = str(row.get("publication_state") or "")
                if state in {"publishing", "recoverable_failed", "blocked"}:
                    issues.recovery("publication_recovery_pending")
                if state == "available" and not row.get("result_context_token"):
                    issues.anomaly("publication_context_missing")
                if row.get("r5_authority_packet_id") and not row.get("r5_authority_packet_digest"):
                    issues.anomaly("publication_r5_anchor_missing")
                for json_name, digest_name in (
                    ("receipt_identities_json", "receipt_set_digest"),
                    ("artifact_member_ids_json", "artifact_member_set_digest"),
                ):
                    try:
                        values = _json_value(row.get(json_name), default=[])
                    except ValueError:
                        issues.anomaly("publication_json_invalid")
                        values = []
                    if not isinstance(values, list):
                        issues.anomaly("publication_json_invalid")
                    elif values and not row.get(digest_name):
                        issues.anomaly("publication_anchor_missing")
                try:
                    s4_ids = _json_value(row.get("s4_authority_packet_identities_json"), default=[])
                    s4_digests = _json_value(row.get("s4_authority_packet_digests_json"), default=[])
                    if not isinstance(s4_ids, list) or not isinstance(s4_digests, list) or len(s4_ids) != len(s4_digests):
                        issues.anomaly("publication_s4_anchor_mismatch")
                except ValueError:
                    issues.anomaly("publication_json_invalid")
                projected_publications.append({
                    "run": run_id,
                    "project": row.get("project_id"),
                    "public_token": row.get("public_run_token"),
                    "context": row.get("result_context_token"),
                    "revision": row.get("publication_revision"),
                    "fingerprint": row.get("publication_fingerprint"),
                    "snapshot": row.get("snapshot_token"),
                    "source": row.get("source_revision_id"),
                    "state": state,
                    "r5": row.get("r5_authority_packet_digest"),
                    "r6": row.get("r6_output_set_digest"),
                    "receipt": row.get("receipt_set_digest"),
                    "artifact": row.get("artifact_member_set_digest"),
                })
            issues.anchor("publication_anchor", {
                "quick_check": quick,
                "foreign_key_violations": foreign_count,
                "registry": registry,
                "publications": projected_publications,
            })
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("publication_read_failed")
        finally:
            connection.close()

    def _check_continuity(self, issues: _VerificationIssues) -> None:
        path = self.project_dir / LAUNCH_DB_RELATIVE_PATH
        if not path.exists():
            issues.anchor("continuity_anchor", [])
            return
        try:
            connection = _readonly_connection(path)
        except (OSError, sqlite3.Error):
            issues.anomaly("continuity_reopen_failed")
            issues.anchor("continuity_anchor", {"available": False})
            return
        try:
            plans = _read_rows(
                connection,
                "r7_continuity_plans",
                (
                    "plan_id", "project_id", "target_run_id", "target_public_run_token",
                    "source_run_id", "source_publication_id", "source_public_run_token",
                    "target_snapshot_id", "baseline_source_run_id", "baseline_source_publication_id",
                    "baseline_source_public_run_token", "r5_authority_digest", "r6_publication_digest",
                    "r6_receipt_digest", "r6_output_set_digest", "plan_digest", "status",
                    "counts_json", "plan_json",
                ),
            )
            items = _read_rows(
                connection,
                "r7_continuity_items",
                (
                    "plan_id", "ordinal", "object_type", "object_ref", "disposition",
                    "source_run_id", "source_publication_id", "source_public_run_token",
                    "source_artifact_id", "source_artifact_sha256", "item_digest", "item_json",
                ),
            )
            registry_rows = _read_rows(
                connection,
                "r7_launch_registry",
                ("run_id", "project_id", "public_run_token"),
            )
            publication_rows = _read_rows(
                connection,
                "r7_result_publications",
                ("run_id", "project_id", "public_run_token", "result_context_token"),
            )
            registry_by_run = {str(row.get("run_id")): row for row in registry_rows}
            publication_by_run = {str(row.get("run_id")): row for row in publication_rows}
            items_by_plan: dict[str, list[dict[str, Any]]] = {}
            for item in items:
                items_by_plan.setdefault(str(item.get("plan_id") or ""), []).append(item)
            projected: list[dict[str, Any]] = []
            for plan in plans:
                if str(plan.get("project_id") or "") != self.canonical_project_id:
                    issues.anomaly("continuity_scope_mismatch")
                target_run = str(plan.get("target_run_id") or "")
                target = registry_by_run.get(target_run)
                if target is None:
                    issues.anomaly("continuity_target_missing")
                elif plan.get("target_public_run_token") and str(plan.get("target_public_run_token")) != str(target.get("public_run_token") or ""):
                    issues.anomaly("continuity_target_identity_mismatch")
                source_run = str(plan.get("source_run_id") or "")
                if source_run and source_run not in publication_by_run:
                    issues.anomaly("continuity_source_missing")
                status = str(plan.get("status") or "")
                if status in {"staging", "blocked"}:
                    issues.recovery("continuity_recovery_pending")
                try:
                    counts = _json_value(plan.get("counts_json"), default={})
                    plan_json = _json_value(plan.get("plan_json"), default={})
                    if not isinstance(counts, dict) or not isinstance(plan_json, dict):
                        issues.anomaly("continuity_json_invalid")
                except ValueError:
                    issues.anomaly("continuity_json_invalid")
                plan_items = sorted(
                    items_by_plan.get(str(plan.get("plan_id") or ""), []),
                    key=lambda item: int(item.get("ordinal") or 0),
                )
                ordinals = [int(item.get("ordinal") or 0) for item in plan_items]
                if ordinals != list(range(len(ordinals))):
                    issues.anomaly("continuity_ordinal_gap")
                for item in plan_items:
                    if not item.get("item_digest"):
                        issues.anomaly("continuity_item_digest_missing")
                    try:
                        item_json = _json_value(item.get("item_json"), default={})
                        if not isinstance(item_json, dict):
                            issues.anomaly("continuity_item_json_invalid")
                    except ValueError:
                        issues.anomaly("continuity_item_json_invalid")
                projected.append({
                    "plan": plan.get("plan_id"),
                    "project": plan.get("project_id"),
                    "target": target_run,
                    "source": source_run,
                    "status": status,
                    "plan_digest": plan.get("plan_digest"),
                    "r5": plan.get("r5_authority_digest"),
                    "r6": plan.get("r6_publication_digest"),
                    "receipt": plan.get("r6_receipt_digest"),
                    "output": plan.get("r6_output_set_digest"),
                    "item_count": len(plan_items),
                    "items": [
                        {
                            "ordinal": item.get("ordinal"),
                            "object_type": item.get("object_type"),
                            "object_ref": item.get("object_ref"),
                            "disposition": item.get("disposition"),
                            "item_digest": item.get("item_digest"),
                        }
                        for item in plan_items
                    ],
                })
            issues.anchor("continuity_anchor", projected)
        except (OSError, sqlite3.Error, TypeError, ValueError, json.JSONDecodeError):
            issues.anomaly("continuity_read_failed")
        finally:
            connection.close()
