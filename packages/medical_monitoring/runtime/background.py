"""Application-owned background progress facade for the isolated R1 shell.

The facade advances synthetic manifest work units in one daemon worker that
owns a worker-thread Store connection on the same SQLite file.  Work therefore
continues without an open progress page, an HTTP server, or any client
polling.  The facade never keeps a second completed/total/percent state:
every audience response is reconstructed from the authoritative Store through
``project_audience_progress``.

Normal dispatch stays single-execution across page refresh, facade
reconstruction and concurrent facades.  One stable begin/complete key per
manifest revision and work unit also lets the Store absorb exact ledger
replays.  If the worker loses the Store after the actual unit action but
before its terminal callback is durably recorded, recovery is deliberately
at-least-once: the supplied unit action must therefore honor that same stable
identity and be idempotent.  This POC does not claim transactional exactly-once
semantics across an external action and SQLite.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

from .progress import project_audience_progress
from ..domain.execution import (
    ExecutionBasis,
    ExecutionManifest,
    IdempotencyConflictError,
    ManifestNode,
    ManifestWorkUnit,
    MonitoringRun,
    NodeStatus,
    NodeType,
    RunMode,
    SourceRevision,
    StaleCallbackError,
    StoreError,
    content_hash,
)


class BackgroundProgressError(StoreError):
    """Raised when the background facade cannot run safely."""


@dataclass(frozen=True)
class BackgroundOutcome:
    """One deterministic synthetic outcome for a manifest work unit."""

    status: NodeStatus
    detail: str


# ---------------------------------------------------------------------------
# Fictional synthetic shell fixture (no real project/patient material)
# ---------------------------------------------------------------------------

SHELL_PROJECT_ID = "project-bg-shell"
SHELL_SOURCE_ID = "source-bg-shell"
SHELL_RUN_ID = "run-bg-shell"
SHELL_NODE_ID = "background-shell-monitor"
SHELL_GRAPH_VERSION = "synthetic-bg-shell-v1"
SHELL_SCHEMA_VERSION = "synthetic-schema-v1"

# (work_unit_id, stage, label, scope, target_ref, outcome)
SHELL_UNITS: Tuple[Tuple[str, str, str, str, str, str], ...] = (
    ("shell-1", "资料准备", "核对合成研究资料清单", "source", "SYN-DOC-1", "passed"),
    ("shell-2", "数据解构", "整理受试者 SYN-001 的访视与事件数据", "subject", "SYN-001", "passed"),
    ("shell-3", "数据解构", "整理受试者 SYN-002 的访视与事件数据", "subject", "SYN-002", "passed"),
    ("shell-4", "风险分析", "分析受试者 SYN-001 的 AE 与 MH 记录", "risk_domain", "SYN-001/AE-MH", "passed"),
    ("shell-5", "风险分析", "分析受试者 SYN-002 的合并用药记录", "risk_domain", "SYN-002/CM", "passed"),
    ("shell-6", "质量检查", "核查合成数据完整性", "qc", "SYN-QC-1", "failed"),
    ("shell-7", "方案符合性", "核查受试者 SYN-001 的访视计划符合性", "subject", "SYN-001", "passed"),
    ("shell-8", "结果汇总", "汇总本次合成监查结果", "project", "SYN-900", "blocked"),
)

_SHELL_OUTCOME_BY_UNIT: Dict[str, str] = {
    unit_id: outcome for unit_id, _, _, _, _, outcome in SHELL_UNITS
}

# One application process may reconstruct more than one facade for the same
# SQLite run (for example after a page refresh).  Store idempotency prevents
# duplicate ledger events, but it cannot by itself prevent two live threads
# from both executing the work between the same begin/complete callbacks.
# Serialize the actual unit action as well, then re-read the ledger while the
# lock is held.  Cross-process ownership remains a later application-hosting
# concern and is deliberately not claimed by this R1 process-local shell.
_UNIT_LOCKS_GUARD = threading.Lock()
_UNIT_LOCKS: Dict[Tuple[str, str, int, str], threading.Lock] = {}


def _unit_execution_lock(
    db_path: Any,
    run_id: str,
    revision: int,
    work_unit_id: str,
) -> threading.Lock:
    key = (str(db_path), run_id, revision, work_unit_id)
    with _UNIT_LOCKS_GUARD:
        lock = _UNIT_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _UNIT_LOCKS[key] = lock
        return lock


def synthetic_shell_outcome(
    unit: ManifestWorkUnit,
    idempotency_key: str = "",
) -> BackgroundOutcome:
    """Deterministic fictional outcome for one shell work unit."""

    del idempotency_key  # accepted so the default obeys the callback contract

    label = " ".join(str(unit.label).split())
    outcome = _SHELL_OUTCOME_BY_UNIT.get(unit.work_unit_id, "passed")
    if outcome == "failed":
        return BackgroundOutcome(
            NodeStatus.FAILED, "未完成：%s：合成数据完整性校验未通过" % label
        )
    if outcome == "blocked":
        return BackgroundOutcome(
            NodeStatus.BLOCKED, "已暂停：%s：等待完整性核查结果" % label
        )
    return BackgroundOutcome(NodeStatus.PASSED, "已完成：%s" % label)


def prepare_synthetic_shell(
    store: Any,
    *,
    project_id: str = SHELL_PROJECT_ID,
    run_id: str = SHELL_RUN_ID,
    data_cutoff: str = "2026-08-09",
) -> int:
    """Build the fictional shell project/run/manifest; idempotent by content."""

    store.create_project(project_id, "合成医学监查后台演示项目")
    store.add_source_revision(
        SourceRevision(
            revision_id=SHELL_SOURCE_ID,
            project_id=project_id,
            source_type="listing",
            version="synthetic-shell-v1",
            content_hash=content_hash({"synthetic_shell": True}),
        )
    )
    store.create_run(
        MonitoringRun(
            run_id=run_id,
            project_id=project_id,
            mode=RunMode.DAILY,
            data_cutoff=data_cutoff,
            source_revision_id=SHELL_SOURCE_ID,
            execution_basis=ExecutionBasis.FULL,
        )
    )
    manifest = ExecutionManifest(
        run_id=run_id,
        nodes=[ManifestNode(SHELL_NODE_ID, NodeType.DETERMINISTIC_SERVICE)],
        work_units=[
            ManifestWorkUnit(
                work_unit_id=unit_id,
                node_id=SHELL_NODE_ID,
                label=label,
                stage=stage,
                scope=scope,
                target_ref=target_ref,
                ordinal=ordinal,
            )
            for ordinal, (unit_id, stage, label, scope, target_ref, _) in enumerate(
                SHELL_UNITS, start=1
            )
        ],
        graph_version=SHELL_GRAPH_VERSION,
        schema_version=SHELL_SCHEMA_VERSION,
    )
    return int(store.set_manifest(manifest))


# ---------------------------------------------------------------------------
# Facade
# ---------------------------------------------------------------------------


def audience_snapshot(
    db_path: Any,
    artifact_dir: Any,
    run_id: str,
    *,
    feed_limit: int = 20,
) -> Dict[str, Any]:
    """Reconstruct the audience view from SQLite on the calling thread.

    A fresh Store is opened and closed per call so any thread (for example one
    HTTP handler thread) may read without sharing SQLite connections, and so a
    browser refresh or facade reconstruction always re-derives the view from
    the authoritative file.  The projection reads are pinned inside one
    deferred read transaction: with WAL mode that holds one consistent
    snapshot, so a concurrent background commit can never be observed
    half-applied between the projection's reads.
    """

    from ..graph.store import Store

    store = Store(db_path, artifact_dir)
    try:
        store._conn.execute("BEGIN")
        try:
            return project_audience_progress(store, run_id, feed_limit=feed_limit)
        finally:
            store._conn.execute("ROLLBACK")
    finally:
        store.close()


class BackgroundProgressFacade:
    """Advance one run's manifest work units without any client attached.

    * One daemon worker owns a Store connection created in that worker thread;
      the constructor's reference Store is used only for paths and validation.
    * ``snapshot()`` is the only progress read and always delegates to
      ``project_audience_progress``; no facade state mirrors counts.
    * Begin/complete use one deterministic key per revision and work unit so
      reconstruction and concurrent facades replay instead of re-dispatching.
    """

    def __init__(
        self,
        store: Any,
        run_id: str,
        *,
        unit_step: Optional[
            Callable[[ManifestWorkUnit, str], BackgroundOutcome]
        ] = None,
        step_seconds: float = 0.02,
        sweep_seconds: float = 0.05,
    ) -> None:
        for attribute in ("db_path", "artifact_dir", "get_run"):
            if not hasattr(store, attribute):
                raise TypeError("store does not expose the R1 store contract")
        run = store.get_run(run_id)
        if int(run.manifest_revision) < 1:
            raise BackgroundProgressError(
                "background progress requires a frozen manifest revision"
            )
        if isinstance(step_seconds, bool) or step_seconds < 0:
            raise BackgroundProgressError("step_seconds must be non-negative")
        if isinstance(sweep_seconds, bool) or sweep_seconds < 0:
            raise BackgroundProgressError("sweep_seconds must be non-negative")
        self.store = store
        self.run_id = run_id
        self.db_path = store.db_path
        self.artifact_dir = store.artifact_dir
        self.unit_step = unit_step or synthetic_shell_outcome
        self.step_seconds = float(step_seconds)
        self.sweep_seconds = float(sweep_seconds)
        self._stop = threading.Event()
        self._done = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.errors: list = []

    # ------------------------------------------------------------- lifecycle

    def start(self) -> bool:
        """Start the worker once; further calls while alive are no-ops."""

        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                return False
            self._stop.clear()
            self._done.clear()
            self._worker = threading.Thread(
                target=self._work,
                name="mm-r1-background-progress:%s" % self.run_id,
                daemon=True,
            )
            self._worker.start()
            return True

    def stop(self, timeout: Optional[float] = None) -> None:
        """Cooperatively stop after the current unit and join the worker."""

        self._stop.set()
        with self._lock:
            worker = self._worker
        if worker is not None and worker.is_alive():
            worker.join(timeout)

    def running(self) -> bool:
        with self._lock:
            worker = self._worker
        return worker is not None and worker.is_alive()

    def wait(self, timeout: Optional[float] = None) -> bool:
        """Wait until every unit reached a terminal status in the ledger."""

        return self._done.wait(timeout)

    # -------------------------------------------------------------- progress

    def snapshot(self, *, feed_limit: int = 20) -> Dict[str, Any]:
        """Return the audience projection reconstructed from SQLite."""

        return audience_snapshot(
            self.db_path, self.artifact_dir, self.run_id, feed_limit=feed_limit
        )

    # ---------------------------------------------------------------- worker

    def _work(self) -> None:
        from ..graph.store import Store

        worker_store = Store(self.db_path, self.artifact_dir)
        try:
            while not self._stop.is_set():
                try:
                    remaining = self._sweep(worker_store)
                except Exception as exc:  # noqa: BLE001 - retry durable state
                    self.errors.append(("background-worker", repr(exc)))
                    self._stop.wait(self.sweep_seconds)
                    continue
                if remaining == 0:
                    self._done.set()
                    return
                self._stop.wait(self.sweep_seconds)
        finally:
            worker_store.close()

    def _sweep(self, worker_store: Any) -> int:
        """One pass over the current revision; return non-terminal count."""

        revision = int(worker_store.get_run(self.run_id).manifest_revision)
        manifest = worker_store.get_manifest(self.run_id, revision)
        if manifest is None or not manifest.work_units:
            raise BackgroundProgressError("background run has no work units")
        rows = {
            row.work_unit_id: row
            for row in worker_store.list_work_unit_runs(self.run_id, revision)
        }
        units = sorted(manifest.work_units, key=lambda item: item.ordinal)
        remaining = 0
        for unit in units:
            row = rows.get(unit.work_unit_id)
            if row is None or row.status not in (
                NodeStatus.PENDING, NodeStatus.RUNNING,
            ):
                continue
            remaining += 1
            if self._stop.is_set():
                continue
            self._process(worker_store, revision, unit)
        return remaining

    def _process(self, worker_store: Any, revision: int, unit: ManifestWorkUnit) -> None:
        lock = _unit_execution_lock(
            self.db_path, self.run_id, revision, unit.work_unit_id
        )
        with lock:
            row = worker_store.get_work_unit_run(
                self.run_id, revision, unit.work_unit_id
            )
            if row is None or row.status not in (
                NodeStatus.PENDING,
                NodeStatus.RUNNING,
            ):
                return
            self._process_locked(worker_store, revision, unit)

    def _process_locked(
        self,
        worker_store: Any,
        revision: int,
        unit: ManifestWorkUnit,
    ) -> None:
        key = "background-progress:%d:%s" % (revision, unit.work_unit_id)
        begin_detail = "正在%s" % unit.label
        try:
            worker_store.begin_work_unit(
                self.run_id, unit.work_unit_id, key, begin_detail,
                manifest_revision=revision,
            )
        except IdempotencyConflictError:
            return  # another writer owns this unit with a different request
        except StaleCallbackError:
            return  # the revision moved on; the next sweep re-reads state

        self._stop.wait(self.step_seconds)  # simulated synthetic work

        try:
            outcome = self.unit_step(unit, key)
        except Exception as exc:  # noqa: BLE001 - a failed unit stays failed
            self.errors.append((unit.work_unit_id, repr(exc)))
            outcome = BackgroundOutcome(
                NodeStatus.FAILED, "未完成：%s" % unit.label
            )
        if not isinstance(outcome, BackgroundOutcome) \
                or outcome.status not in (
                NodeStatus.PASSED, NodeStatus.FAILED, NodeStatus.BLOCKED,
        ):
            self.errors.append((unit.work_unit_id, "invalid synthetic outcome"))
            outcome = BackgroundOutcome(
                NodeStatus.FAILED, "未完成：%s" % unit.label
            )
        try:
            worker_store.complete_work_unit(
                self.run_id, unit.work_unit_id, key, outcome.status,
                outcome.detail, evidence_count=0, manifest_revision=revision,
            )
        except (IdempotencyConflictError, StaleCallbackError):
            return  # another writer closed this unit first; history is kept


__all__ = [
    "BackgroundOutcome",
    "BackgroundProgressError",
    "BackgroundProgressFacade",
    "SHELL_PROJECT_ID",
    "SHELL_RUN_ID",
    "SHELL_SOURCE_ID",
    "SHELL_UNITS",
    "audience_snapshot",
    "prepare_synthetic_shell",
    "synthetic_shell_outcome",
]
