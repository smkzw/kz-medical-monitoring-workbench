"""Background execution adapter built on the durable recovery support layer."""
from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Callable, Mapping
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional, Union
from uuid import uuid4

from .background_recovery_support import (
    ARTIFACT_DIR_NAME,
    BackgroundOutcome,
    CONTROL_STATES,
    CONTROL_TABLE,
    CONTROL_TABLE_NAME,
    ControlState,
    ExecutionClaim,
    ExecutionControl,
    ExecutionControlError,
    ExecutionControlState,
    ExecutionState,
    HEARTBEAT_SECONDS,
    LEASE_SECONDS,
    MAX_CAPABILITY_ATTEMPTS,
    RETRYABLE_CAPABILITY_ATTEMPT_STATUSES,
    RUN_STATE_VALUES,
    RUNTIME_DB_NAME,
    _ACTIVE_STATES,
    _TERMINAL_VALUES,
    _ai_unit_ids,
    _bound_capability_attempts,
    _checked_control,
    _connect,
    _continuable_ai_units,
    _control_from_row,
    _error,
    _has_runnable,
    _now_text,
    _open_store,
    _public_overlay,
    _raw_control,
    _read_snapshot_from_store,
    _recover_expired_control,
    _require_control_schema,
    _runnable_units,
    _validate_options,
    _validate_r1_store,
    assert_prepare_scope_change_allowed,
    continuable_ai_unit,
    ensure_execution_control,
    list_bound_capability_attempts,
)
from .capability import InvocationVersions
from .controller import CapabilityWorkUnitController
from .maintenance_gate import (
    DEFAULT_WAIT_SECONDS,
    MaintenanceGateError,
    ProjectMaintenanceGate,
)
from ..domain.execution import (
    TERMINAL_NODE_STATUSES,
    CoverageUnit,
    ExecutionManifest,
    IdempotencyConflictError,
    ManifestWorkUnit,
    NodeStatus,
    StaleCallbackError,
    StoreError,
)
from ..graph.store import Store

class BackgroundRecoveryAdapter:
    """Run-level controller and synthetic worker for one canonical workspace."""

    _registry_lock = threading.Lock()
    _registry: dict[tuple[str, str, int], threading.Thread] = {}

    def __init__(
        self,
        workspace_dir: Optional[Union[str, Path]] = None,
        *,
        runtime_dir: Optional[Union[str, Path]] = None,
        db_path: Optional[Union[str, Path]] = None,
        artifact_dir: Optional[Union[str, Path]] = None,
        canonical_project_id: str = "",
        maintenance_root: Optional[Union[str, Path]] = None,
        unit_step: Optional[Callable[[ManifestWorkUnit, str], BackgroundOutcome]] = None,
        clock: Callable[[], float] = time.time,
        lease_seconds: float = LEASE_SECONDS,
        heartbeat_seconds: float = HEARTBEAT_SECONDS,
        step_seconds: float = 0.01,
        sweep_seconds: float = 0.01,
        harness_runtime_factory: Optional[Callable[..., Any]] = None,
        harness_adapter: Any = None,
        harness_catalog: Any = None,
        harness_r1_profile: Any = None,
        harness_profile_factory: Optional[Callable[[str], Any]] = None,
        run_binding_store: Any = None,
    ) -> None:
        _validate_options(lease_seconds, heartbeat_seconds, step_seconds, sweep_seconds)
        if db_path is not None:
            self.db_path = Path(db_path)
            self.artifact_dir = Path(
                artifact_dir if artifact_dir is not None else self.db_path.parent / ARTIFACT_DIR_NAME
            )
        else:
            root = Path(runtime_dir if runtime_dir is not None else workspace_dir or "")
            if not str(root):
                raise _error("runtime_integrity_failed")
            if root.name != "runtime":
                root = root / "runtime"
            self.db_path = root / RUNTIME_DB_NAME
            self.artifact_dir = Path(artifact_dir) if artifact_dir is not None else root / ARTIFACT_DIR_NAME
        self.canonical_project_id = canonical_project_id
        self.unit_step = unit_step or synthetic_outcome
        self.clock = clock
        self.lease_seconds = float(lease_seconds)
        self.heartbeat_seconds = float(heartbeat_seconds)
        self.step_seconds = float(step_seconds)
        self.sweep_seconds = float(sweep_seconds)
        self.harness_runtime_factory = harness_runtime_factory
        self.harness_adapter = harness_adapter
        self.harness_catalog = harness_catalog
        self.harness_r1_profile = harness_r1_profile
        self.harness_profile_factory = harness_profile_factory
        self.run_binding_store = run_binding_store
        self.maintenance_root = (
            Path(maintenance_root)
            if maintenance_root is not None
            else self.db_path.parent.parent.parent
        )

    @contextmanager
    def _shared_project_maintenance(self):
        """Hold the product write gate for the complete worker lifetime."""
        if not self.canonical_project_id:
            yield
            return
        gate = ProjectMaintenanceGate(
            self.maintenance_root,
            self.canonical_project_id,
            wait_seconds=DEFAULT_WAIT_SECONDS,
        )
        try:
            with gate.shared():
                yield
        except MaintenanceGateError as exc:
            raise _error("project_busy_retry_later") from exc

    def _key(self, run_id: str, revision: int) -> tuple[str, str, int]:
        return (str(self.db_path), run_id, revision)

    def _validate(self, run_id: str) -> None:
        store = _open_store(self.db_path, self.artifact_dir)
        try:
            _validate_r1_store(store, run_id, self.canonical_project_id)
        finally:
            store.close()

    def _control(self, run_id: str) -> ExecutionControl:
        connection = _connect(self.db_path)
        try:
            _require_control_schema(connection)
            return _checked_control(connection, run_id)
        finally:
            connection.close()

    def get_control(self, run_id: str) -> ExecutionControl:
        """Read the durable control row for offline tests and diagnostics."""
        return self._control(run_id)

    control = get_control
    read_control = get_control
    get_execution_control = get_control

    def _recover_expired_lease_unlocked(self, run_id: str) -> ExecutionControl:
        """Mark an expired owner interrupted; never start a worker."""
        self._recover_expired_attempts(run_id)
        recovered = _recover_expired_control(self.db_path, run_id, float(self.clock()))
        if recovered is None:
            raise _error("runtime_integrity_failed")
        return self._control(run_id)
    def recover_expired_lease(self, run_id: str) -> ExecutionControl:
        with self._shared_project_maintenance():
            return self._recover_expired_lease_unlocked(run_id)

    recover = recover_expired_lease

    def _recover_expired_attempts(self, run_id: str) -> list[str]:
        """Recover R1 attempt leases without dispatching or reconciling transport."""
        store = _open_store(self.db_path, self.artifact_dir)
        try:
            return list(
                store.recover_expired_capability_attempts(
                    now_epoch=float(self.clock()), run_id=run_id
                )
            )
        finally:
            store.close()

    def _renew_inflight_lease_unlocked(
        self,
        run_id: str,
        manifest_revision: int,
        generation: int,
        owner_token: str,
        *,
        lease_seconds: Optional[float] = None,
        now_epoch: Optional[float] = None,
    ) -> bool:
        """Renew only the current harness unit's run lease.

        This path intentionally does not call :meth:`heartbeat`; a cancelling
        owner may keep its current transport lease alive but cannot claim more
        work.
        """
        from .harness_runtime import renew_inflight_lease

        return bool(
            renew_inflight_lease(
                self.db_path,
                run_id,
                manifest_revision,
                generation,
                owner_token,
                lease_seconds=(
                    self.lease_seconds if lease_seconds is None else lease_seconds
                ),
                now_epoch=now_epoch,
            )
        )

    def renew_inflight_lease(
        self,
        run_id: str,
        manifest_revision: int,
        generation: int,
        owner_token: str,
        *,
        lease_seconds: Optional[float] = None,
        now_epoch: Optional[float] = None,
    ) -> bool:
        with self._shared_project_maintenance():
            return self._renew_inflight_lease_unlocked(
                run_id,
                manifest_revision,
                generation,
                owner_token,
                lease_seconds=lease_seconds,
                now_epoch=now_epoch,
            )
    def _heartbeat_unlocked(
        self, run_id: str, manifest_revision: int, generation: int,
        owner_token: str, *, now: Optional[float] = None,
    ) -> bool:
        """CAS renew one active owner lease; false means the owner is stale."""
        current_time = float(self.clock() if now is None else now)
        connection = _connect(self.db_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _require_control_schema(connection)
                row = _raw_control(connection, run_id)
                if row is None:
                    connection.execute("ROLLBACK")
                    return False
                control = _control_from_row(row)
                valid = (
                    control.manifest_revision == manifest_revision
                    and control.generation == generation
                    and control.owner_token == owner_token
                    and control.state is ExecutionControlState.RUNNING
                    and not control.cancel_requested
                    and control.lease_expires_at is not None
                    and control.lease_expires_at > current_time
                )
                if not valid:
                    connection.execute("ROLLBACK")
                    return False
                new_expiry = current_time + self.lease_seconds
                stamp = _now_text(current_time)
                cursor = connection.execute(
                    f"UPDATE {CONTROL_TABLE_NAME} SET lease_expires_at=?, updated_at=?"
                    " WHERE run_id=? AND manifest_revision=? AND generation=?"
                    " AND owner_token=? AND state=? AND cancel_requested=0"
                    " AND lease_expires_at>?",
                    (
                        new_expiry, stamp, run_id, manifest_revision, generation,
                        owner_token, ExecutionControlState.RUNNING.value, current_time,
                    ),
                )
                ok = cursor.rowcount == 1
                connection.execute("COMMIT" if ok else "ROLLBACK")
                return ok
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
    def heartbeat(
        self, run_id: str, manifest_revision: int, generation: int,
        owner_token: str, *, now: Optional[float] = None,
    ) -> bool:
        with self._shared_project_maintenance():
            return self._heartbeat_unlocked(
                run_id,
                manifest_revision,
                generation,
                owner_token,
                now=now,
            )

    cas_heartbeat = heartbeat

    def _claim(self, run_id: str, action: str) -> tuple[Optional[ExecutionClaim], bool]:
        current_time = float(self.clock())
        connection = _connect(self.db_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _require_control_schema(connection)
                control = _checked_control(connection, run_id)
                if (
                    control.state in _ACTIVE_STATES
                    and control.lease_expires_at is not None
                    and control.lease_expires_at <= current_time
                ):
                    stamp = _now_text(current_time)
                    cursor = connection.execute(
                        f"UPDATE {CONTROL_TABLE_NAME} SET generation=?, state=?,"
                        " owner_token='', lease_expires_at=NULL, cancel_requested=0,"
                        " updated_at=? WHERE run_id=? AND manifest_revision=?"
                        " AND generation=? AND owner_token=?",
                        (
                            control.generation + 1,
                            ExecutionControlState.INTERRUPTED.value,
                            stamp,
                            run_id,
                            control.manifest_revision,
                            control.generation,
                            control.owner_token,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise _error("runtime_integrity_failed")
                    control = _checked_control(connection, run_id)
                if control.state in _ACTIVE_STATES:
                    connection.execute("COMMIT")
                    return None, True
                if action == "start":
                    if control.state is ExecutionControlState.FINISHED:
                        raise _error("already_finished")
                    if control.state is not ExecutionControlState.PREPARED:
                        raise _error("execution_not_prepared")
                elif action == "resume":
                    if control.state is ExecutionControlState.FINISHED \
                            and not _has_runnable(
                                connection, run_id, control.manifest_revision
                            ):
                        raise _error("nothing_to_resume")
                    if control.state is not ExecutionControlState.INTERRUPTED:
                        raise _error("not_interrupted")
                    if not _has_runnable(connection, run_id, control.manifest_revision):
                        raise _error("nothing_to_resume")
                else:  # pragma: no cover - private caller guard
                    raise _error("runtime_integrity_failed")
                owner = uuid4().hex
                generation = control.generation + 1
                expiry = current_time + self.lease_seconds
                stamp = _now_text(current_time)
                cursor = connection.execute(
                    f"UPDATE {CONTROL_TABLE_NAME} SET generation=?, state=?,"
                    " owner_token=?, lease_expires_at=?, cancel_requested=0, updated_at=?"
                    " WHERE run_id=? AND manifest_revision=? AND generation=?"
                    " AND state=? AND owner_token='' AND lease_expires_at IS NULL",
                    (
                        generation, ExecutionControlState.RUNNING.value, owner, expiry,
                        stamp, run_id, control.manifest_revision, control.generation,
                        control.state.value,
                    ),
                )
                if cursor.rowcount != 1:
                    raise _error("already_running")
                connection.execute("COMMIT")
                return ExecutionClaim(
                    run_id=run_id,
                    manifest_revision=control.manifest_revision,
                    generation=generation,
                    owner_token=owner,
                    lease_expires_at=expiry,
                ), False
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

    def _spawn(self, claim: ExecutionClaim) -> None:
        key = self._key(claim.run_id, claim.manifest_revision)
        with self._registry_lock:
            # A non-replayed claim always has a new generation.  An old
            # thread may still be unwinding after lease recovery; replacing
            # its handle is required so the new generation is not left
            # running with no worker.  The old thread will fail its CAS check
            # and exit without overwriting the new owner.
            stop_event = threading.Event()
            worker = threading.Thread(
                target=self._worker_main,
                args=(claim, stop_event),
                name="mm-r7-background-worker",
                daemon=True,
            )
            self._registry[key] = worker
        try:
            worker.start()
        except Exception as exc:
            with self._registry_lock:
                if self._registry.get(key) is worker:
                    self._registry.pop(key, None)
            self._release_claim(claim, interrupted=True)
            raise _error("worker_start_failed") from exc

    def _harness_profile(self, run_id: str) -> Any:
        if self.harness_profile_factory is not None:
            profile = self.harness_profile_factory(run_id)
            if profile is not None:
                return profile
        getter = getattr(self.run_binding_store, "get_with_frozen", None)
        if callable(getter):
            _, profile = getter(run_id)
            return profile
        return None

    def _make_harness_runtime(
        self, store: Store, claim: ExecutionClaim, unit: ManifestWorkUnit,
    ) -> Any:
        factory = self.harness_runtime_factory
        if factory is not None:
            # The callback is deliberately a complete-runtime seam.  It may
            # construct a test HarnessCapabilityRuntime with a fake R6 adapter;
            # R7 never discovers or starts a provider itself.
            runtime = factory(store, claim, unit)
            if runtime is None:
                raise StoreError("harness runtime factory returned no runtime")
            return runtime
        if self.harness_adapter is None:
            raise StoreError("offline harness adapter is not configured")
        profile = self._harness_profile(claim.run_id)
        if profile is None:
            raise StoreError("frozen harness profile is unavailable")
        from .harness_runtime import (
            HarnessCapabilityRuntime,
            build_profile_receipt_bridge,
        )

        bridge = build_profile_receipt_bridge(
            profile, self.harness_r1_profile,
        )
        return HarnessCapabilityRuntime(
            bridge,
            adapter=self.harness_adapter,
            attempt_journal=store,
            journal_owner_token=claim.owner_token,
            run_claim=claim,
            run_control=self,
            control_db_path=self.db_path,
            run_lease_seconds=self.lease_seconds,
            renew_interval_seconds=self.heartbeat_seconds,
            catalog=self.harness_catalog,
            require_run_cas=True,
        )

    @staticmethod
    def _preflight_ok(result: Any) -> bool:
        if isinstance(result, Mapping):
            return result.get("ok") is True
        return getattr(result, "ok", False) is True

    def _persist_harness_preflight_failure(
        self,
        store: Store,
        claim: ExecutionClaim,
        runtime: Any,
        unit: ManifestWorkUnit,
        result: Any = None,
    ) -> None:
        """Record only a de-sensitive diagnosis; never declare an attempt."""
        try:
            from .harness_runtime import (
                build_preflight_diagnosis,
                persist_preflight_diagnosis,
            )
            from mm_r6.agent_harness import PreflightResult

            bridge = getattr(runtime, "bridge", None)
            if bridge is None:
                return
            if not isinstance(result, PreflightResult):
                profile = bridge.r6_profile
                reasons = tuple(
                    str(value) for value in (
                        result.get("reasons", ())
                        if isinstance(result, Mapping) else getattr(result, "reasons", ())
                    )
                )
                result = PreflightResult(
                    ok=False,
                    executable="",
                    selector=profile.effective_selector,
                    effort=profile.reasoning_effort,
                    allowed_tools=tuple(profile.allowed_tools),
                    timeout_seconds=int(profile.timeout_seconds),
                    reasons=reasons or ("preflight_failed",),
                )
            diagnosis = build_preflight_diagnosis(
                bridge,
                result,
                run_id=claim.run_id,
                node_id=unit.node_id,
                manifest_revision=claim.manifest_revision,
            )
            persist_preflight_diagnosis(store, diagnosis)
        except Exception:
            # A missing optional diagnosis projection must not turn a failed
            # preflight into an attempt or a transport dispatch.
            return

    def _preflight_harness(
        self,
        store: Store,
        claim: ExecutionClaim,
        runtime: Any,
        unit: ManifestWorkUnit,
    ) -> bool:
        try:
            from .harness_runtime import persist_profile_receipt_bridge

            bridge = getattr(runtime, "bridge", None)
            if bridge is not None:
                persist_profile_receipt_bridge(store, bridge, run_id=claim.run_id)
            preflight = getattr(runtime, "preflight", None)
            if not callable(preflight):
                raise StoreError("harness runtime preflight is unavailable")
            result = preflight()
        except Exception as exc:
            self._persist_harness_preflight_failure(store, claim, runtime, unit)
            return False
        if not self._preflight_ok(result):
            self._persist_harness_preflight_failure(
                store, claim, runtime, unit, result
            )
            return False
        return self._claim_permitted(claim)

    @staticmethod
    def _capability_attempt_id(
        run_id: str, revision: int, work_unit_id: str, ordinal: int,
    ) -> str:
        return (
            f"r7-capability:{run_id}:{revision}:{work_unit_id}:attempt-{ordinal}"
        )

    def _ai_payload_and_coverage(
        self, unit: ManifestWorkUnit,
    ) -> tuple[dict[str, str], tuple[CoverageUnit, ...]]:
        payload = {
            "work_unit_id": unit.work_unit_id,
            "scope": unit.scope,
            "target_ref": unit.target_ref,
        }
        expected = (CoverageUnit(scope=unit.scope, key=unit.target_ref),)
        return payload, expected

    def _invoke_ai_attempt(
        self,
        store: Store,
        claim: ExecutionClaim,
        unit: ManifestWorkUnit,
        runtime: Any,
        controller: CapabilityWorkUnitController,
        *,
        attempt_id: str,
        continued_from: str = "",
    ) -> Any:
        run = store.get_run(claim.run_id)
        payload, expected = self._ai_payload_and_coverage(unit)
        versions = InvocationVersions(
            source_revision_id=run.source_revision_id,
            rule_version="mm-r7-slice06-rule-v1",
            knowledge_version="mm-r7-slice06-knowledge-v1",
            graph_version="mm-r7-slice06-harness-v1",
            schema_version="mm-r7-slice06-schema-v1",
        )
        if continued_from:
            return controller.resume(
                runtime,
                continued_from,
                attempt_id=attempt_id,
                manifest_revision=claim.manifest_revision,
            )
        return controller.execute(
            runtime,
            work_unit_id=unit.work_unit_id,
            attempt_id=attempt_id,
            monitoring_run_id=claim.run_id,
            node_id=unit.node_id,
            manifest_revision=claim.manifest_revision,
            versions=versions,
            payload=payload,
            expected_units=expected,
        )

    def _retry_ai_if_allowed(
        self,
        store: Store,
        claim: ExecutionClaim,
        unit: ManifestWorkUnit,
        runtime: Any,
        controller: CapabilityWorkUnitController,
        previous_attempt_id: str,
    ) -> Any:
        control = self._control(claim.run_id)
        if control.state is not ExecutionControlState.RUNNING:
            return None
        if not self._claim_permitted(claim):
            return None
        history = _bound_capability_attempts(
            store, claim.run_id, claim.manifest_revision, unit.work_unit_id
        )
        if not history:
            return None
        latest = history[-1]
        if (
            latest["attempt_id"] != previous_attempt_id
            or latest["attempt_ordinal"] >= MAX_CAPABILITY_ATTEMPTS
            or latest.get("status") not in RETRYABLE_CAPABILITY_ATTEMPT_STATUSES
        ):
            return None
        next_id = self._capability_attempt_id(
            claim.run_id,
            claim.manifest_revision,
            unit.work_unit_id,
            latest["attempt_ordinal"] + 1,
        )
        return self._invoke_ai_attempt(
            store,
            claim,
            unit,
            runtime,
            controller,
            attempt_id=next_id,
            continued_from=previous_attempt_id,
        )

    def _start_execution_unlocked(self, run_id: str) -> dict[str, Any]:
        self._validate(run_id)
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, float(self.clock()))
        claim, replayed = self._claim(run_id, "start")
        if claim is not None:
            self._spawn(claim)
        return self._action_response(run_id, replayed=replayed)
    def start_execution(self, run_id: str) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._start_execution_unlocked(run_id)

    start = start_execution
    start_run = start_execution

    def _resume_execution_unlocked(self, run_id: str) -> dict[str, Any]:
        self._validate(run_id)
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, float(self.clock()))
        claim, replayed = self._claim(run_id, "resume")
        if claim is not None:
            self._spawn(claim)
        return self._action_response(run_id, replayed=replayed)
    def resume_execution(self, run_id: str) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._resume_execution_unlocked(run_id)

    resume = resume_execution
    resume_run = resume_execution

    def _cancel_execution_unlocked(self, run_id: str) -> dict[str, Any]:
        self._validate(run_id)
        current_time = float(self.clock())
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, current_time)
        connection = _connect(self.db_path)
        replayed = False
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _require_control_schema(connection)
                control = _checked_control(connection, run_id)
                if (
                    control.state in _ACTIVE_STATES
                    and control.lease_expires_at is not None
                    and control.lease_expires_at <= current_time
                ):
                    stamp = _now_text(current_time)
                    cursor = connection.execute(
                        f"UPDATE {CONTROL_TABLE_NAME} SET generation=?, state=?,"
                        " owner_token='', lease_expires_at=NULL, cancel_requested=0,"
                        " updated_at=? WHERE run_id=? AND manifest_revision=?"
                        " AND generation=? AND owner_token=?",
                        (
                            control.generation + 1,
                            ExecutionControlState.INTERRUPTED.value,
                            stamp, run_id, control.manifest_revision, control.generation,
                            control.owner_token,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise _error("runtime_integrity_failed")
                    control = _checked_control(connection, run_id)
                if control.state is ExecutionControlState.RUNNING:
                    stamp = _now_text(current_time)
                    cursor = connection.execute(
                        f"UPDATE {CONTROL_TABLE_NAME} SET state=?, cancel_requested=1,"
                        " updated_at=? WHERE run_id=? AND manifest_revision=?"
                        " AND generation=? AND owner_token=? AND state=?"
                        " AND lease_expires_at>?",
                        (
                            ExecutionControlState.CANCELLING.value, stamp, run_id,
                            control.manifest_revision, control.generation,
                            control.owner_token, ExecutionControlState.RUNNING.value,
                            current_time,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise _error("not_running")
                elif control.state in {
                    ExecutionControlState.CANCELLING,
                    ExecutionControlState.INTERRUPTED,
                    ExecutionControlState.FINISHED,
                }:
                    replayed = True
                else:
                    raise _error("not_running")
                connection.execute("COMMIT")
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
        return self._action_response(run_id, replayed=replayed)
    def cancel_execution(self, run_id: str) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._cancel_execution_unlocked(run_id)

    cancel = cancel_execution
    stop = cancel_execution
    cancel_run = cancel_execution
    start_background = start_execution
    resume_background = resume_execution
    cancel_background = cancel_execution

    def wait(self, run_id: str, timeout: Optional[float] = None) -> bool:
        control = self._control(run_id)
        key = self._key(run_id, control.manifest_revision)
        with self._registry_lock:
            worker = self._registry.get(key)
        if worker is None:
            return not self.running(run_id)
        worker.join(timeout)
        return not worker.is_alive()

    def running(self, run_id: str) -> bool:
        try:
            control = self._control(run_id)
        except ExecutionControlError:
            return False
        key = self._key(run_id, control.manifest_revision)
        with self._registry_lock:
            worker = self._registry.get(key)
        return worker is not None and worker.is_alive()

    is_running = running

    def _snapshot_unlocked(self, run_id: str, *, feed_limit: int = 20) -> dict[str, Any]:
        """Read R1 audience data and control overlay from one SQLite snapshot."""
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, float(self.clock()))
        store = _open_store(self.db_path, self.artifact_dir)
        try:
            return _read_snapshot_from_store(store, run_id, feed_limit=feed_limit)
        finally:
            store.close()
    def snapshot(self, run_id: str, *, feed_limit: int = 20) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._snapshot_unlocked(run_id, feed_limit=feed_limit)

    read_progress = snapshot
    get_progress = snapshot

    def _snapshot_from_store_unlocked(
        self, store: Store, run_id: str, *, feed_limit: int = 20,
    ) -> dict[str, Any]:
        """Use a caller-owned Store while keeping base view and overlay atomic."""
        self._recover_expired_attempts(run_id)
        _recover_expired_control(self.db_path, run_id, float(self.clock()))
        return _read_snapshot_from_store(store, run_id, feed_limit=feed_limit)
    def snapshot_from_store(
        self, store: Store, run_id: str, *, feed_limit: int = 20,
    ) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._snapshot_from_store_unlocked(
                store, run_id, feed_limit=feed_limit
            )

    def _action_response(self, run_id: str, *, replayed: bool) -> dict[str, Any]:
        control = self._control(run_id)
        if control.state in {
            ExecutionControlState.INTERRUPTED,
            ExecutionControlState.FINISHED,
            ExecutionControlState.CANCELLING,
        }:
            view = self.snapshot(run_id)
            overlay = {
                "run_status_text": view["run_status_text"],
                "available_actions": view["available_actions"],
            }
        else:
            overlay = _public_overlay(control, {"completed": 0, "total": 1})
        return {
            "replayed": bool(replayed),
            "run_status_text": overlay["run_status_text"],
            "available_actions": overlay["available_actions"],
        }

    def _release_claim(self, claim: ExecutionClaim, *, interrupted: bool) -> None:
        current_time = float(self.clock())
        connection = _connect(self.db_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _require_control_schema(connection)
                state = (
                    ExecutionControlState.INTERRUPTED
                    if interrupted else ExecutionControlState.FINISHED
                )
                cursor = connection.execute(
                    f"UPDATE {CONTROL_TABLE_NAME} SET state=?, owner_token='',"
                    " lease_expires_at=NULL, cancel_requested=0, updated_at=?"
                    " WHERE run_id=? AND manifest_revision=? AND generation=?"
                    " AND owner_token=? AND state IN (?,?)",
                    (
                        state.value, _now_text(current_time), claim.run_id,
                        claim.manifest_revision, claim.generation, claim.owner_token,
                        ExecutionControlState.RUNNING.value,
                        ExecutionControlState.CANCELLING.value,
                    ),
                )
                if cursor.rowcount:
                    connection.execute("COMMIT")
                else:
                    connection.execute("ROLLBACK")
            except BaseException:
                try:
                    connection.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
        except (ExecutionControlError, sqlite3.Error, OSError, ValueError):
            # A stale worker must not replace a newer owner.  The next
            # explicit resume/recovery operation will reconcile the row.
            return
        finally:
            connection.close()

    def _worker_main_locked(self, claim: ExecutionClaim, stop_event: threading.Event) -> None:
        key = self._key(claim.run_id, claim.manifest_revision)
        store: Optional[Store] = None
        try:
            store = _open_store(self.db_path, self.artifact_dir)
            stalled_rounds = 0
            while True:
                if stop_event.is_set():
                    self._release_claim(claim, interrupted=True)
                    return
                if not self.heartbeat(
                    claim.run_id, claim.manifest_revision, claim.generation,
                    claim.owner_token,
                ):
                    if self._finish_cancelled_if_quiescent(store, claim):
                        return
                    self._release_claim(claim, interrupted=True)
                    return
                manifest = store.get_manifest(claim.run_id, claim.manifest_revision)
                if manifest is None or not manifest.work_units:
                    self._release_claim(claim, interrupted=True)
                    return
                rows = {
                    row.work_unit_id: row
                    for row in store.list_work_unit_runs(
                        claim.run_id, claim.manifest_revision,
                    )
                }
                statuses = {unit_id: row.status.value for unit_id, row in rows.items()}
                runnable = _runnable_units(
                    manifest,
                    statuses,
                    continuable_ids=_continuable_ai_units(
                        store, claim.run_id, claim.manifest_revision, manifest
                    ),
                )
                if not runnable:
                    if self._finish_if_quiescent(store, claim, statuses, manifest):
                        return
                    stalled_rounds += 1
                    if stalled_rounds >= 3:
                        self._release_claim(claim, interrupted=True)
                        return
                    stop_event.wait(self.sweep_seconds)
                    continue
                progressed = False
                for unit in runnable:
                    if stop_event.is_set() or not self.heartbeat(
                        claim.run_id, claim.manifest_revision, claim.generation,
                        claim.owner_token,
                    ):
                        self._release_claim(claim, interrupted=True)
                        return
                    result = self._process_unit(store, claim, unit, stop_event)
                    progressed = progressed or result
                if not progressed:
                    stalled_rounds += 1
                    if stalled_rounds >= 3:
                        self._release_claim(claim, interrupted=True)
                        return
                    stop_event.wait(self.sweep_seconds)
                else:
                    stalled_rounds = 0
                    if self.sweep_seconds:
                        stop_event.wait(self.sweep_seconds)
        except Exception:
            self._release_claim(claim, interrupted=True)
        finally:
            if store is not None:
                store.close()
            with self._registry_lock:
                if self._registry.get(key) is threading.current_thread():
                    self._registry.pop(key, None)

    def _worker_main(self, claim: ExecutionClaim, stop_event: threading.Event) -> None:
        try:
            with self._shared_project_maintenance():
                self._worker_main_locked(claim, stop_event)
        except ExecutionControlError:
            # The claim remains lease-bound when the worker cannot enter the
            # shared gate; a later explicit recovery can reconcile it.
            pass

    def _process_unit(
        self, store: Store, claim: ExecutionClaim, unit: ManifestWorkUnit,
        stop_event: threading.Event,
    ) -> bool:
        manifest = store.get_manifest(claim.run_id, claim.manifest_revision)
        if manifest is None:
            self._release_claim(claim, interrupted=True)
            return False
        if unit.work_unit_id in _ai_unit_ids(manifest):
            return self._process_ai_unit(store, claim, unit, stop_event)
        stable_key = f"r7-background:{claim.run_id}:{claim.manifest_revision}:{unit.work_unit_id}"
        detail = f"正在{unit.label}"
        # Re-check immediately before the R1 begin callback.  A lease may
        # expire between the sweep-level heartbeat and this point; a resumed
        # generation must be the only one allowed to claim new work.
        if not self._claim_permitted(claim):
            self._release_claim(claim, interrupted=True)
            return False
        try:
            store.begin_work_unit(
                claim.run_id, unit.work_unit_id, stable_key, detail,
                manifest_revision=claim.manifest_revision,
            )
        except (IdempotencyConflictError, StaleCallbackError, StoreError):
            return False
        if not self._sleep_synthetic(claim, stop_event):
            self._release_claim(claim, interrupted=True)
            return False
        try:
            outcome = self.unit_step(unit, stable_key)
        except Exception:
            outcome = BackgroundOutcome(
                NodeStatus.FAILED, f"未完成：{unit.label}"
            )
        if not isinstance(outcome, BackgroundOutcome):
            outcome = BackgroundOutcome(
                NodeStatus.FAILED, f"未完成：{unit.label}"
            )
        if outcome.status not in TERMINAL_NODE_STATUSES or not isinstance(outcome.detail, str):
            outcome = BackgroundOutcome(
                NodeStatus.FAILED, f"未完成：{unit.label}"
            )
        if not self._commit_permitted(claim):
            self._release_claim(claim, interrupted=True)
            return False
        try:
            store.complete_work_unit(
                claim.run_id, unit.work_unit_id, stable_key, outcome.status,
                outcome.detail, evidence_count=0,
                manifest_revision=claim.manifest_revision,
            )
            return True
        except (IdempotencyConflictError, StaleCallbackError, StoreError):
            # A lost lease, injected store failure, or another same-key writer
            # leaves the ledger authoritative.  The next sweep may replay the
            # same stable key; it never fabricates a second progress record.
            return False

    def _process_ai_unit(
        self,
        store: Store,
        claim: ExecutionClaim,
        unit: ManifestWorkUnit,
        stop_event: threading.Event,
    ) -> bool:
        """Run one AI candidate through R1's controller and bounded retry."""
        del stop_event  # The injected harness owns the blocking transport wait.
        if not self._claim_permitted(claim):
            self._release_claim(claim, interrupted=True)
            return False
        try:
            runtime = self._make_harness_runtime(store, claim, unit)
        except Exception:
            # No attempt is declared when the offline runtime cannot even be
            # constructed.  Keep the work unit pending and let the run recover.
            self._release_claim(claim, interrupted=True)
            return False
        if not self._preflight_harness(store, claim, runtime, unit):
            self._release_claim(claim, interrupted=True)
            return False
        if not self._claim_permitted(claim):
            self._release_claim(claim, interrupted=True)
            return False

        controller = CapabilityWorkUnitController(store)
        history = _bound_capability_attempts(
            store, claim.run_id, claim.manifest_revision, unit.work_unit_id
        )
        previous_attempt_id = ""
        if history:
            latest = history[-1]
            latest_status = latest.get("status")
            if latest_status in RETRYABLE_CAPABILITY_ATTEMPT_STATUSES:
                if latest["attempt_ordinal"] >= MAX_CAPABILITY_ATTEMPTS:
                    return False
                attempt_id = self._capability_attempt_id(
                    claim.run_id,
                    claim.manifest_revision,
                    unit.work_unit_id,
                    latest["attempt_ordinal"] + 1,
                )
                previous_attempt_id = latest["attempt_id"]
            elif latest_status in {"declared", "running"}:
                # A process restart may leave a declared assignment without a
                # binding.  Replay that exact assignment; R1 controls whether
                # the attempt can claim its lease.
                attempt_id = latest["attempt_id"]
            else:
                return False
        else:
            attempt_id = self._capability_attempt_id(
                claim.run_id,
                claim.manifest_revision,
                unit.work_unit_id,
                1,
            )

        try:
            result = self._invoke_ai_attempt(
                store,
                claim,
                unit,
                runtime,
                controller,
                attempt_id=attempt_id,
                continued_from=previous_attempt_id,
            )
        except Exception:
            # Runtime exceptions are converted to an interrupted R1 attempt by
            # CapabilityRuntime.  A running owner gets exactly one linked retry;
            # cancelling or a lost lease never creates it.
            try:
                current = store.get_capability_attempt(attempt_id)
                status = current.get("status") if current else ""
                if status == "interrupted":
                    retry = self._retry_ai_if_allowed(
                        store,
                        claim,
                        unit,
                        runtime,
                        controller,
                        attempt_id,
                    )
                    return retry is not None
            except Exception:
                pass
            return False

        result_status = getattr(getattr(result, "status", None), "value", "")
        if result_status in RETRYABLE_CAPABILITY_ATTEMPT_STATUSES:
            try:
                retry = self._retry_ai_if_allowed(
                    store,
                    claim,
                    unit,
                    runtime,
                    controller,
                    attempt_id,
                )
                if retry is not None:
                    return True
            except Exception:
                # The first terminal result remains authoritative.  A failed
                # retry will be surfaced as a resumable/limited unit state.
                return True
        return True

    def _sleep_synthetic(
        self, claim: ExecutionClaim, stop_event: threading.Event,
    ) -> bool:
        """Wait for the configured synthetic action while renewing its lease."""
        remaining = self.step_seconds
        while remaining > 0:
            if stop_event.is_set():
                return False
            interval = min(remaining, self.heartbeat_seconds)
            started = time.monotonic()
            if stop_event.wait(interval):
                return False
            remaining -= max(0.0, time.monotonic() - started)
            if remaining > 0 and not self.heartbeat(
                claim.run_id, claim.manifest_revision, claim.generation,
                claim.owner_token,
            ):
                # A user stop changes the control row to ``cancelling`` and
                # intentionally makes heartbeat renewal return false.  The
                # current synthetic action may still finish; only a lost
                # generation/owner or an expired lease aborts it.
                try:
                    control = self._control(claim.run_id)
                except ExecutionControlError:
                    return False
                if not (
                    control.manifest_revision == claim.manifest_revision
                    and control.generation == claim.generation
                    and control.owner_token == claim.owner_token
                    and control.state is ExecutionControlState.CANCELLING
                    and control.lease_expires_at is not None
                    and control.lease_expires_at > float(self.clock())
                ):
                    return False
        return not stop_event.is_set()

    def _claim_permitted(self, claim: ExecutionClaim) -> bool:
        """CAS guard used before a new R1 work-unit begin callback."""
        now = float(self.clock())
        connection = _connect(self.db_path)
        try:
            _require_control_schema(connection)
            row = _raw_control(connection, claim.run_id)
            if row is None:
                return False
            control = _control_from_row(row)
            return bool(
                control.manifest_revision == claim.manifest_revision
                and control.generation == claim.generation
                and control.owner_token == claim.owner_token
                and control.state is ExecutionControlState.RUNNING
                and not control.cancel_requested
                and control.lease_expires_at is not None
                and control.lease_expires_at > now
            )
        except ExecutionControlError:
            return False
        finally:
            connection.close()

    def _commit_permitted(self, claim: ExecutionClaim) -> bool:
        """Check the owner CAS immediately before the R1 terminal callback.

        ``cancelling`` is allowed here: the contract lets the current
        synthetic unit finish, then prevents the next claim.  A public
        heartbeat remains stricter and only renews ``running`` leases.
        """
        now = float(self.clock())
        connection = _connect(self.db_path)
        try:
            _require_control_schema(connection)
            row = _raw_control(connection, claim.run_id)
            if row is None:
                return False
            control = _control_from_row(row)
            return bool(
                control.manifest_revision == claim.manifest_revision
                and control.generation == claim.generation
                and control.owner_token == claim.owner_token
                and control.state in _ACTIVE_STATES
                and control.lease_expires_at is not None
                and control.lease_expires_at > now
            )
        except ExecutionControlError:
            return False
        finally:
            connection.close()

    def _finish_cancelled_if_quiescent(
        self, store: Store, claim: ExecutionClaim,
    ) -> bool:
        """Finish a stopped run only when its ledger has no resumable work."""
        try:
            control = self._control(claim.run_id)
        except ExecutionControlError:
            return False
        if not (
            control.manifest_revision == claim.manifest_revision
            and control.generation == claim.generation
            and control.owner_token == claim.owner_token
            and control.state is ExecutionControlState.CANCELLING
        ):
            return False
        manifest = store.get_manifest(claim.run_id, claim.manifest_revision)
        if manifest is None:
            return False
        statuses = {
            row.work_unit_id: row.status.value
            for row in store.list_work_unit_runs(
                claim.run_id, claim.manifest_revision,
            )
        }
        return self._finish_if_quiescent(store, claim, statuses, manifest)

    def _finish_if_quiescent(
        self, store: Store, claim: ExecutionClaim, statuses: Mapping[str, str],
        manifest: ExecutionManifest,
    ) -> bool:
        continuable_ids = _continuable_ai_units(
            store,
            claim.run_id,
            claim.manifest_revision,
            manifest,
        )
        if continuable_ids:
            return False
        has_nonterminal = any(status not in _TERMINAL_VALUES for status in statuses.values())
        if has_nonterminal:
            runnable = _runnable_units(
                manifest, statuses, continuable_ids=continuable_ids
            )
            # A failed/blocked dependency makes remaining pending work
            # permanently non-runnable in this slice.  Leave those rows
            # pending and close the run honestly.  A live dependency or a
            # malformed state is not silently marked finished.
            failed_dependency = any(
                statuses.get(dep) in {
                    NodeStatus.FAILED.value, NodeStatus.BLOCKED.value,
                }
                for unit in manifest.work_units
                if statuses.get(unit.work_unit_id) in {
                    NodeStatus.PENDING.value, NodeStatus.RUNNING.value,
                }
                for dep in unit.depends_on
            )
            if runnable or not failed_dependency:
                return False
        self._release_claim(claim, interrupted=False)
        return True

    def progress(self, run_id: str, *, feed_limit: int = 20) -> dict[str, Any]:
        return self.snapshot(run_id, feed_limit=feed_limit)


def synthetic_outcome(unit: ManifestWorkUnit, idempotency_key: str = "") -> BackgroundOutcome:
    """Default offline action: one deterministic, audience-readable pass."""
    del idempotency_key
    return BackgroundOutcome(NodeStatus.PASSED, f"已完成：{unit.label}")


def audience_snapshot(
    db_path: Union[str, Path], artifact_dir: Union[str, Path], run_id: str,
    *, feed_limit: int = 20,
) -> dict[str, Any]:
    """Reconstruct R1 audience progress plus the R7 Chinese overlay."""
    return BackgroundRecoveryAdapter(
        db_path=db_path, artifact_dir=artifact_dir,
    ).snapshot(run_id, feed_limit=feed_limit)


BackgroundRecovery = BackgroundRecoveryAdapter
RunControlAdapter = BackgroundRecoveryAdapter


__all__ = [
    "ARTIFACT_DIR_NAME",
    "audience_snapshot",
    "BackgroundOutcome",
    "BackgroundRecovery",
    "BackgroundRecoveryError",
    "CONTROL_STATES",
    "CONTROL_TABLE",
    "CONTROL_TABLE_NAME",
    "ControlState",
    "ExecutionClaim",
    "ExecutionControl",
    "ExecutionControlError",
    "ExecutionControlState",
    "ExecutionState",
    "BackgroundRecoveryAdapter",
    "HEARTBEAT_SECONDS",
    "LEASE_SECONDS",
    "MAX_CAPABILITY_ATTEMPTS",
    "list_bound_capability_attempts",
    "RETRYABLE_CAPABILITY_ATTEMPT_STATUSES",
    "RUN_STATE_VALUES",
    "RunControlAdapter",
    "RUNTIME_DB_NAME",
    "assert_prepare_scope_change_allowed",
    "ensure_execution_control",
    "continuable_ai_unit",
    "synthetic_outcome",
]
