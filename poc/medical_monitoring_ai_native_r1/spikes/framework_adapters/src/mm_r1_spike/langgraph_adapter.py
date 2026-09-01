"""LangGraph 1.2.10 + local SQLite checkpointer adapter (worker_02-owned spike).

A REAL accepted-``GraphPort`` implementation: ``LangGraphAdapter`` inherits
:class:`mm_r1.graph.GraphPort` and exposes the exact accepted public API
(``run`` / ``resume`` / ``replay`` returning :class:`mm_r1.graph.GraphRun`).
LangGraph ``StateGraph`` is the execution engine and the pinned ``SqliteSaver``
(``langgraph-checkpoint-sqlite`` 3.1.1) drives the cross-process
interrupt/resume boundary.  Domain authority stays EXCLUSIVELY in the accepted
slice1 ``Store``; framework checkpoint/session/message objects NEVER enter domain
artifacts, Store facts, or audit authority.

Two execution surfaces:
  * the accepted public ``GraphPort`` API (``run`` / ``resume`` / ``replay``) --
    fail closed if the supplied ``graph``/``run_id`` does not exactly match the
    current frozen manifest/contract; and
  * the candidate-specific private spike boundary ``_run_contract(contract,
    stop_after_node=None) -> AdapterRunResult`` used by the focused
    subprocess/restart evidence.

Contract guarantees (execution context: Shared Contract And Required Evidence):
  * consumes the shared frozen manifest/Graph IR (``synthetic_three_node_graph``
    + ``synthetic_manifest``) and the worker_01 conformance/work-event substrate;
  * framework state is JSON-compatible and persisted in a SEPARATE checkpoint DB
    (``langgraph_checkpoints.sqlite3``), distinct from the authoritative slice1
    Store DB and the work-event DB;
  * a deterministic thread/run key binds one run+manifest-fingerprint to one
    LangGraph thread (stable across processes);
  * domain commits happen ONLY through accepted Store/handler contracts
    (``begin_node_run`` / ``synth_handler`` / ``complete_node_run``);
  * ``LANGGRAPH_STRICT_MSGPACK=true`` is enforced and asserted at import time;
    only the static allowlisted checkpoint metadata keys are trusted on resume;
  * at EVERY public run/resume/replay the contract is recomputed from the frozen
    manifest and a wrong/stale/mismatched contract fails closed before any
    authoritative Store mutation; corrupt or mismatched run/thread metadata or
    checkpoint state/blob fails closed BEFORE any Store mutation.

No package install, no network, no service.  Disposable Python 3.12 venv only.
"""

from __future__ import annotations

# STRICT_MSGPACK_ENABLED is read at first import of
# langgraph.checkpoint.serde._msgpack (module level).  Set the env var here so
# the flag is True before the langgraph package is imported below.
import os as _os

_os.environ["LANGGRAPH_STRICT_MSGPACK"] = _os.environ.get(
    "LANGGRAPH_STRICT_MSGPACK", "true"
)

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Dict, List, Mapping, Optional, TypedDict
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

# Assert strict msgpack actually took effect (env was set before first import).
from langgraph.checkpoint.serde import _msgpack as _lg_msgpack

if not getattr(_lg_msgpack, "STRICT_MSGPACK_ENABLED", False):
    raise RuntimeError(
        "LANGGRAPH_STRICT_MSGPACK must be 'true' before langgraph is imported; "
        "strict checkpoint deserialization is mandatory for this spike"
    )

from mm_r1.domain import (
    CompletionGateError,
    TERMINAL_NODE_STATUSES,
    NodeStatus,
    new_id,
    now_iso,
)
from mm_r1.graph import (
    Graph,
    GraphNodeResult,
    GraphPort,
    GraphRun,
    NodeContext,
)
from mm_r1.store import Store

from .contract import (
    ConformanceContract,
    PHASE_NODE_BEGIN,
    PHASE_NODE_COMPLETE,
    GraphIRMismatchError,
    assert_exact_graph_ir,
)
from .restart_harness import (
    SYNTH_OUTPUT_KEY,
    bootstrap_run,
    save_operational_checkpoint,
    synth_handler,
)
from .work_events import WorkEventStore


def _merge_dict(left: Optional[Mapping[str, Any]], right: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """LangGraph channel reducer: merge successive node returns into one dict.

    With the default ``StateGraph(dict)`` schema each node return OVERWRITES the
    prior value, so accumulator channels (node_outputs / reuse_flags /
    node_sequences) would lose earlier nodes' entries.  This reducer accumulates
    them so the final state reflects every executed node.
    """
    merged: Dict[str, Any] = {}
    if left:
        merged.update(left)
    if right:
        merged.update(right)
    return merged


class _AdapterState(TypedDict, total=False):
    """LangGraph state schema: dict channels merge across nodes via _merge_dict."""

    node_outputs: Annotated[Dict[str, Any], _merge_dict]
    reuse_flags: Annotated[Dict[str, Any], _merge_dict]
    node_sequences: Annotated[Dict[str, Any], _merge_dict]
    last_node: str


LANGGRAPH_VERSION_TARGET = "1.2.10"
CHECKPOINT_SQLITE_VERSION_TARGET = "3.1.1"
CHECKPOINTER_DB_NAME = "langgraph_checkpoints.sqlite3"


# Static allowlist of LangGraph CheckpointMetadata keys we trust on resume.
# Exactly the keys produced by langgraph.checkpoint.base.CheckpointMetadata
# (source / step / parents / run_id / counters_since_delta_snapshot).  Any other
# key in a persisted checkpoint is untrusted and fails closed.
ALLOWED_METADATA_KEYS = frozenset(
    {"source", "step", "parents", "run_id", "counters_since_delta_snapshot"}
)


class LangGraphCheckpointIdentityError(RuntimeError):
    """Framework checkpoint identity mismatch / corruption -- fail closed.

    Raised before any authoritative Store mutation so a wrong-run, wrong-thread,
    non-allowlisted-metadata, missing-run-id, fingerprint-divergent, or corrupt
    checkpoint (metadata OR state/blob) can never drive a commit.
    """


def thread_key(run_id: str, manifest_fingerprint: str) -> str:
    """Deterministic LangGraph thread id binding one run + frozen manifest
    fingerprint to one thread.

    The manifest fingerprint binds run_id + graph_id + revision + node set +
    node content (canonical hash).  Two runs that share run_id/graph/revision but
    have a different frozen manifest therefore get different threads -- a stale
    or swapped manifest cannot resume another run's checkpoint.

    Stable across processes: a fresh process reopening the same work dir derives
    the identical thread id and therefore resumes the identical checkpoint.
    """
    return f"run:{run_id}:fp:{manifest_fingerprint}"


@dataclass
class AdapterNodeResult:
    node_id: str
    status: str
    reused: bool
    work_event_sequence: int


@dataclass
class AdapterRunResult:
    run_id: str
    thread_id: str
    graph_id: str
    manifest_revision: int
    manifest_fingerprint: str
    stop_node: Optional[str]
    resumed: bool
    node_results: List[AdapterNodeResult] = field(default_factory=list)
    progress: Dict[str, Any] = field(default_factory=dict)
    final_state: Dict[str, Any] = field(default_factory=dict)


def _completed_so_far(store: Store, run_id: str) -> int:
    return int(store.manifest_progress(run_id)["completed"])


def _work_event(
    run_id: str,
    contract: ConformanceContract,
    node_id: str,
    phase: str,
    status: str,
    completed: int,
) -> Dict[str, Any]:
    return {
        "event_id": new_id("we_"),
        "run_id": run_id,
        "manifest_revision": contract.manifest_revision,
        "sequence": 0,
        "node_id": node_id,
        "work_unit_id": node_id,
        "phase": phase,
        "status": status,
        "completed": completed,
        "total": contract.total_units,
        "current_detail": f"{phase}:{node_id}",
        "created_at": now_iso(),
        "idempotency_key": f"we:{run_id}:{node_id}:{phase}",
    }


class LangGraphAdapter(GraphPort):
    """Real ``GraphPort`` implementation over LangGraph + SQLite checkpointer.

    LangGraph ``StateGraph`` is the execution engine (not a decorative wrapper):
    each synthetic manifest node becomes a LangGraph node function that commits
    to the authoritative Store through the accepted handler contract, and the
    pinned ``SqliteSaver`` persists framework state in a separate DB so a fresh
    process can resume across the injected interrupt boundary.

    Accepted public API (exact ``GraphPort`` contract):
      * ``run(graph, run_id, context=None, auto_finalize=True) -> GraphRun``
      * ``resume(run_id) -> GraphRun``
      * ``replay(run_id) -> GraphRun``

    Each public method recomputes the conformance contract from the frozen
    manifest and fails closed if the supplied graph/run does not exactly match.
    """

    def __init__(
        self,
        store: Store,
        events: WorkEventStore,
        work_dir: Path,
        *,
        checkpoint_db: Optional[Path] = None,
    ) -> None:
        self._store = store
        self._events = events
        self._work_dir = Path(work_dir)
        self._work_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoint_db = (
            Path(checkpoint_db)
            if checkpoint_db is not None
            else self._work_dir / CHECKPOINTER_DB_NAME
        )
        self._conn = sqlite3.connect(str(self._checkpoint_db), check_same_thread=False)
        self._saver = SqliteSaver(self._conn)
        self._saver.setup()

    @property
    def saver(self) -> SqliteSaver:
        return self._saver

    @property
    def checkpoint_db(self) -> Path:
        return self._checkpoint_db

    def close(self) -> None:
        try:
            self._conn.close()
        except sqlite3.Error:
            pass

    def __enter__(self) -> "LangGraphAdapter":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # contract resolution (recomputed from the frozen manifest every call)
    # ------------------------------------------------------------------

    def _resolve_contract(self, run_id: str) -> ConformanceContract:
        """Recompute the conformance contract from the authoritative frozen
        manifest.  Raises if no manifest is frozen for the run."""
        manifest = self._store.get_manifest(run_id)
        if manifest is None:
            raise RuntimeError(f"no manifest frozen for run {run_id}")
        return ConformanceContract.from_manifest(manifest)

    def _pre_terminal_nodes(self, run_id: str) -> set:
        """Snapshot node ids that are already terminal BEFORE this invocation.

        Public GraphRun.reused and private AdapterNodeResult.reused both derive
        from this set so fresh executions report reused=False, resume reports
        only earlier committed nodes as reused, and replay reports all True.
        """
        manifest = self._store.get_manifest(run_id)
        if manifest is None:
            return set()
        out: set = set()
        for nid in manifest.node_ids():
            nr = self._store.get_node_run(run_id, nid)
            if nr is not None and nr.status in TERMINAL_NODE_STATUSES:
                out.add(nid)
        return out

    def _assert_graph_matches_contract(
        self, graph: Graph, contract: ConformanceContract
    ) -> None:
        """Fail closed if the supplied graph IR does not exactly match the
        frozen manifest Graph (ordered nodes + execution-relevant fields +
        ordered/conditional edges) and the recomputed contract fingerprint.

        Called by public ``run`` BEFORE any checkpoint / work-event / Store
        mutation.  A same-id/same-node-set graph with altered edges is rejected.
        """
        manifest = self._store.get_manifest(contract.run_id)
        if manifest is None:
            raise LangGraphCheckpointIdentityError(
                f"no manifest frozen for run {contract.run_id}"
            )
        fresh = ConformanceContract.from_manifest(manifest)
        if (
            fresh.manifest_fingerprint != contract.manifest_fingerprint
            or fresh.manifest_revision != contract.manifest_revision
            or fresh.graph_id != contract.graph_id
            or fresh.node_ids != contract.node_ids
        ):
            raise LangGraphCheckpointIdentityError(
                "manifest fingerprint/revision/graph/node-order drift: supplied "
                f"contract does not match frozen manifest for run {contract.run_id!r}"
            )
        expected = Graph.from_manifest(manifest)
        try:
            assert_exact_graph_ir(graph, expected)
        except GraphIRMismatchError as exc:
            raise LangGraphCheckpointIdentityError(str(exc)) from exc

    # -- state graph construction from frozen manifest/Graph IR -------------

    def _build_state_graph(self, manifest, contract: ConformanceContract, rev: int):
        node_ids = list(manifest.node_ids())
        node_types = {n.node_id: n.node_type for n in manifest.nodes}

        def make_node_fn(node_id: str):
            def fn(state: Mapping[str, Any]) -> Dict[str, Any]:
                return self._execute_node(
                    state, node_id, manifest, contract, rev, node_types[node_id]
                )

            fn.__name__ = f"lg_{node_id}"
            return fn

        sg = StateGraph(_AdapterState, context=Any)
        for nid in node_ids:
            sg.add_node(nid, make_node_fn(nid))
        sg.add_edge(START, node_ids[0])
        graph = Graph.from_manifest(manifest)
        for e in graph.edges:
            sg.add_edge(e.src, e.dst)
        sg.add_edge(node_ids[-1], END)
        return sg

    # -- per-node execution (domain commit via accepted contracts) ----------

    def _execute_node(
        self,
        state: Mapping[str, Any],
        node_id: str,
        manifest,
        contract: ConformanceContract,
        rev: int,
        node_type: Any,
    ) -> Dict[str, Any]:
        store = self._store
        events = self._events
        run_id = manifest.run_id
        key = f"g:{manifest.graph_id}:{node_id}:r{rev}"

        outputs: Dict[str, Any] = dict(state.get("node_outputs", {}))
        reuse_flags: Dict[str, bool] = dict(state.get("reuse_flags", {}))
        node_sequences: Dict[str, int] = dict(state.get("node_sequences", {}))

        existing = store.get_node_run(run_id, node_id)
        is_terminal = existing is not None and existing.status in TERMINAL_NODE_STATUSES

        if is_terminal:
            if existing.output:
                outputs[node_id] = existing.output.get(SYNTH_OUTPUT_KEY, {})
            reuse_flags[node_id] = True
            node_sequences[node_id] = events.sequence_for(
                run_id, node_id, PHASE_NODE_COMPLETE
            )
            save_operational_checkpoint(self._work_dir, contract, node_id, outputs)
            return {
                "node_outputs": outputs,
                "reuse_flags": reuse_flags,
                "node_sequences": node_sequences,
                "last_node": node_id,
            }

        # fresh execution: node_begin event
        events.append(
            _work_event(
                run_id, contract, node_id, PHASE_NODE_BEGIN,
                status="running", completed=_completed_so_far(store, run_id),
            ),
            contract,
        )
        store.begin_node_run(run_id, node_id, node_type, key)
        ctx = NodeContext(
            run_id=run_id, node_id=node_id, node_type=node_type,
            store=store, checkpoint=store, shared={SYNTH_OUTPUT_KEY: outputs},
        )
        outcome = synth_handler(node_id, ctx)
        completed = store.complete_node_run(
            run_id, node_id, key, outcome.status, output=outcome.output
        )
        outputs[node_id] = outcome.output.get(SYNTH_OUTPUT_KEY, {}) if outcome.output else {}
        ev = events.append(
            _work_event(
                run_id, contract, node_id, PHASE_NODE_COMPLETE,
                status=completed.status.value, completed=_completed_so_far(store, run_id),
            ),
            contract,
        )
        reuse_flags[node_id] = False
        node_sequences[node_id] = ev.sequence
        save_operational_checkpoint(self._work_dir, contract, node_id, outputs)
        return {
            "node_outputs": outputs,
            "reuse_flags": reuse_flags,
            "node_sequences": node_sequences,
            "last_node": node_id,
        }

    # -- checkpoint identity fail-closed (before any domain commit) ---------

    def verify_checkpoint_identity(self, contract: ConformanceContract, tid: str) -> None:
        """Fail closed if the persisted framework checkpoint does not bind to
        the exact frozen run + manifest fingerprint, carries non-allowlisted
        metadata, has a missing/unequal run_id, or is corrupt (metadata OR
        state/blob).

        Reads only the separate checkpoint DB; never touches the authoritative
        Store.  Raises :class:`LangGraphCheckpointIdentityError` on any mismatch
        or corruption so a wrong-run/corrupt checkpoint cannot drive a commit.

        The thread id already encodes the manifest fingerprint; this additionally
        verifies the persisted metadata binds to the exact run_id and that the
        checkpoint state blob is present and well-formed for the latest row.
        """
        row = self._conn.execute(
            "SELECT thread_id, checkpoint, metadata FROM checkpoints "
            "WHERE thread_id=? ORDER BY checkpoint_id DESC LIMIT 1",
            (tid,),
        ).fetchone()
        if row is None:
            return  # nothing persisted yet for this thread -> nothing to verify
        db_thread, state_blob, meta_blob = row
        if db_thread != tid:
            raise LangGraphCheckpointIdentityError(
                f"checkpoint thread_id mismatch: {db_thread!r} != {tid!r}"
            )
        # checkpoint state blob must be present and non-empty
        if state_blob is None:
            raise LangGraphCheckpointIdentityError(
                "checkpoint state blob is NULL"
            )
        if isinstance(state_blob, (bytes, bytearray)) and len(state_blob) == 0:
            raise LangGraphCheckpointIdentityError(
                "checkpoint state blob is empty"
            )
        # metadata must be valid JSON
        try:
            meta = (
                json.loads(meta_blob)
                if isinstance(meta_blob, (bytes, bytearray))
                else dict(meta_blob or {})
            )
        except (ValueError, TypeError) as exc:
            raise LangGraphCheckpointIdentityError(
                f"checkpoint metadata is corrupt/not JSON: {exc}"
            ) from exc
        if not isinstance(meta, dict):
            raise LangGraphCheckpointIdentityError("checkpoint metadata is not a JSON object")
        extra = set(meta.keys()) - ALLOWED_METADATA_KEYS
        if extra:
            raise LangGraphCheckpointIdentityError(
                f"checkpoint metadata has non-allowlisted keys: {sorted(extra)}"
            )
        # run_id binding is REQUIRED (missing is failure, not accepted)
        ck_run = meta.get("run_id")
        if ck_run is None:
            raise LangGraphCheckpointIdentityError(
                "checkpoint metadata is missing required 'run_id' binding"
            )
        if str(ck_run) != contract.run_id:
            raise LangGraphCheckpointIdentityError(
                f"checkpoint run_id {ck_run!r} != contract run_id {contract.run_id!r}"
            )

    # ------------------------------------------------------------------
    # candidate-specific private spike boundary (subprocess/focused evidence)
    # ------------------------------------------------------------------

    def _run_contract(
        self,
        contract: ConformanceContract,
        *,
        stop_after_node: Optional[str] = None,
    ) -> AdapterRunResult:
        """Run the frozen manifest through LangGraph behind the spike boundary.

        First call executes from the start; when ``stop_after_node`` is set the
        graph is compiled with ``interrupt_before`` so LangGraph halts at the
        injected boundary after that node (framework primitive, not a manual
        break).  The pinned ``SqliteSaver`` persists framework state in the
        separate checkpoint DB.

        A subsequent call (same work dir, fresh process) resumes: the identical
        deterministic thread id reopens the persisted checkpoint, already-
        terminal Store nodes are reused, and only outstanding nodes execute.

        The contract is recomputed from the frozen manifest at entry and the
        persisted checkpoint identity is verified fail-closed BEFORE any domain
        commit, so an externally stale/mismatched contract cannot drive a commit.
        """
        store = self._store
        run_id = contract.run_id
        # recompute the authoritative contract from the frozen manifest and
        # reject any externally stale/mismatched contract before touching state
        fresh = self._resolve_contract(run_id)
        if (
            fresh.manifest_fingerprint != contract.manifest_fingerprint
            or fresh.manifest_revision != contract.manifest_revision
            or fresh.graph_id != contract.graph_id
        ):
            raise LangGraphCheckpointIdentityError(
                "supplied contract does not match the frozen manifest for run "
                f"{run_id!r}"
            )
        contract = fresh

        manifest = store.get_manifest(run_id)
        rev = manifest.revision
        tid = thread_key(run_id, contract.manifest_fingerprint)

        # fail-closed identity verification BEFORE any domain commit
        self.verify_checkpoint_identity(contract, tid)

        node_ids = list(manifest.node_ids())
        interrupt = None
        if stop_after_node is not None:
            idx = node_ids.index(stop_after_node)
            interrupt = node_ids[idx + 1:] if idx + 1 < len(node_ids) else None

        sg = self._build_state_graph(manifest, contract, rev)
        app = sg.compile(checkpointer=self._saver, interrupt_before=interrupt)

        # snapshot which nodes were ALREADY terminal before this invocation --
        # the authoritative "reused" signal comes from the Store, not framework
        # state, so resume/replay reuse is determined independently of how the
        # engine replays its checkpoint.
        pre_terminal = {
            nid for nid in node_ids
            if (store.get_node_run(run_id, nid) is not None
                and store.get_node_run(run_id, nid).status in TERMINAL_NODE_STATUSES)
        }

        # run_id is placed in `configurable` so LangGraph propagates it into the
        # persisted checkpoint metadata (the static allowlisted identity binding
        # verified on resume); the top-level run_id is kept for framework routing.
        cfg = {
            "configurable": {"thread_id": tid, "run_id": run_id},
            "run_id": run_id,
        }

        # resume if a checkpoint already exists for this thread
        tup = self._saver.get_tuple({"configurable": {"thread_id": tid}})
        resumed = tup is not None
        if resumed:
            state_out = app.invoke(None, config=cfg)
        else:
            state_out = app.invoke(
                {"node_outputs": {}, "reuse_flags": {}, "node_sequences": {}},
                config=cfg,
            )

        # collect node results in manifest order; reused = was terminal pre-run
        node_sequences = dict(state_out.get("node_sequences", {}))
        node_results: List[AdapterNodeResult] = []
        for nid in node_ids:
            nr = store.get_node_run(run_id, nid)
            status = nr.status.value if nr else "pending"
            was_reused = nid in pre_terminal
            # work-event sequence: freshly-run nodes have it in framework state;
            # reused nodes look it up from the committed event stream
            seq = int(node_sequences.get(nid, 0))
            if was_reused and seq == 0:
                seq = self._events.sequence_for(run_id, nid, PHASE_NODE_COMPLETE)
            node_results.append(
                AdapterNodeResult(
                    node_id=nid,
                    status=status,
                    reused=was_reused,
                    work_event_sequence=seq,
                )
            )

        progress = store.manifest_progress(run_id)
        return AdapterRunResult(
            run_id=run_id,
            thread_id=tid,
            graph_id=manifest.graph_id,
            manifest_revision=rev,
            manifest_fingerprint=contract.manifest_fingerprint,
            stop_node=stop_after_node,
            resumed=resumed,
            node_results=node_results,
            progress=progress,
            final_state=dict(state_out),
        )

    # ------------------------------------------------------------------
    # accepted public GraphPort API
    # ------------------------------------------------------------------

    def run(
        self,
        graph: Graph,
        run_id: str,
        context: Optional[Mapping[str, Any]] = None,
        auto_finalize: bool = True,
    ) -> GraphRun:
        """Accepted ``GraphPort.run``: execute the graph for ``run_id``.

        The contract is recomputed from the frozen manifest; the supplied graph
        must exactly match the frozen Graph IR, else fail closed before any
        domain / event / checkpoint mutation.  Public ``run`` may start a new
        thread or resume an existing framework checkpoint for the same run.
        """
        contract = self._resolve_contract(run_id)
        self._assert_graph_matches_contract(graph, contract)
        pre_terminal = self._pre_terminal_nodes(run_id)
        self._run_contract(contract, stop_after_node=None)
        return self._materialize_graph_run(
            run_id, contract, auto_finalize=auto_finalize, pre_terminal=pre_terminal,
        )

    def resume(self, run_id: str) -> GraphRun:
        """Accepted ``GraphPort.resume``: continue an interrupted run from its
        frozen manifest + framework checkpoint + committed Store state.

        Requires a persisted framework checkpoint for this run's thread and
        fails closed if missing (does NOT silently restart from the Store alone).
        """
        contract = self._resolve_contract(run_id)
        tid = thread_key(run_id, contract.manifest_fingerprint)
        # fail-closed: public resume must not restart from Store when the
        # framework checkpoint is absent
        tup = self._saver.get_tuple({"configurable": {"thread_id": tid}})
        if tup is None:
            raise LangGraphCheckpointIdentityError(
                f"no LangGraph framework checkpoint to resume for run {run_id!r} "
                f"(thread {tid!r}); public resume fails closed"
            )
        self.verify_checkpoint_identity(contract, tid)
        pre_terminal = self._pre_terminal_nodes(run_id)
        self._run_contract(contract, stop_after_node=None)
        return self._materialize_graph_run(
            run_id, contract, auto_finalize=True, pre_terminal=pre_terminal,
        )

    def replay(self, run_id: str) -> GraphRun:
        """Accepted ``GraphPort.replay``: re-execute a completed run; every node
        must come back REUSED with no duplicate side effect/artifact/event."""
        contract = self._resolve_contract(run_id)
        pre_terminal = self._pre_terminal_nodes(run_id)
        result = self._run_contract(contract, stop_after_node=None)
        for nr in result.node_results:
            if not nr.reused:
                raise RuntimeError(
                    f"replay re-executed node {nr.node_id} (status {nr.status}); "
                    "replay must only reuse committed results"
                )
        return self._materialize_graph_run(
            run_id, contract, auto_finalize=True, pre_terminal=pre_terminal,
        )

    def _materialize_graph_run(
        self,
        run_id: str,
        contract: ConformanceContract,
        *,
        auto_finalize: bool,
        pre_terminal: Optional[set] = None,
    ) -> GraphRun:
        """Build the accepted ``GraphRun`` from the authoritative Store state,
        optionally finalizing analysis (mirrors LocalGraphPort semantics).

        ``reused`` is derived exclusively from ``pre_terminal`` (captured before
        invocation): fresh nodes False, resume only earlier committed True,
        replay all True.  Never computed from post-execution Store state.
        """
        store = self._store
        manifest = store.get_manifest(run_id)
        node_ids = list(manifest.node_ids())
        pre = set(pre_terminal) if pre_terminal is not None else set()
        any_failed = any_blocked = False
        node_results: List[GraphNodeResult] = []
        for nid in node_ids:
            nr = store.get_node_run(run_id, nid)
            if nr is None:
                node_results.append(GraphNodeResult(
                    run_id=run_id, node_id=nid, status=NodeStatus.PENDING,
                    message="no node run",
                ))
                any_blocked = True
                continue
            reused = nid in pre
            node_results.append(GraphNodeResult(
                run_id=run_id, node_id=nid, status=nr.status, reused=reused,
                artifact_id=nr.artifact_id,
                message="reused from committed state" if reused else "",
            ))
            if nr.status == NodeStatus.FAILED:
                any_failed = True
            elif nr.status == NodeStatus.BLOCKED:
                any_blocked = True

        status = "complete"
        if any_blocked:
            status = "blocked"
        elif any_failed:
            status = "failed"
        else:
            status = "complete"

        if auto_finalize and status == "complete":
            try:
                from mm_r1.domain import AnalysisState
                run = store.get_run(run_id)
                if run.analysis_state == AnalysisState.NOT_STARTED:
                    store.update_run_state(
                        run_id, analysis=AnalysisState.RUNNING,
                        reason="langgraph adapter run started",
                    )
                store.complete_analysis(run_id, reason="langgraph adapter run finalized")
            except CompletionGateError:
                # Catch ONLY the expected analysis completion-gate exception
                # from the synthetic evidence gate.  Do not broadly swallow
                # arbitrary exceptions — unexpected finalization errors propagate.
                pass

        progress = store.manifest_progress(run_id)
        return GraphRun(
            run_id=run_id,
            graph_id=contract.graph_id,
            status=status,
            node_results=node_results,
            context={"progress": progress, "manifest_fingerprint": contract.manifest_fingerprint},
        )


# ---------------------------------------------------------------------------
# Subprocess entrypoint support
# ---------------------------------------------------------------------------

def _store_paths(work_dir: Path):
    work_dir = Path(work_dir)
    store_db = work_dir / "authoritative.sqlite3"
    artifact_dir = work_dir / "artifacts"
    events_db = work_dir / "work_events.sqlite3"
    return store_db, artifact_dir, events_db


def adapter_main(argv: Optional[List[str]] = None) -> int:
    """Subprocess entrypoint for the LangGraph adapter two-process boundary.

    Process A bootstraps + runs to the injected boundary; process B is a FRESH
    process that reopens the persisted authoritative Store + separate checkpoint
    DB and resumes.  Framework state is read from the separate checkpoint DB,
    domain authority from the slice1 Store.
    """
    import json as _json

    parser = argparse.ArgumentParser(description="LangGraph adapter restart worker")
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--stop-after-node", default=None)
    parser.add_argument("--invocation-marker", default=None)
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--manifest-revision", type=int, default=1)
    args = parser.parse_args(argv)

    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    store_db, artifact_dir, events_db = _store_paths(work_dir)

    store = Store(store_db, artifact_dir)
    events = WorkEventStore(events_db)
    adapter = LangGraphAdapter(store, events, work_dir)
    try:
        if args.bootstrap:
            manifest = bootstrap_run(store, args.run_id, manifest_revision=args.manifest_revision)
        else:
            manifest = store.get_manifest(args.run_id)
            if manifest is None:
                raise RuntimeError(f"no manifest frozen for run {args.run_id}")

        contract = ConformanceContract.from_manifest(manifest)
        result = adapter._run_contract(contract, stop_after_node=args.stop_after_node)

        progress = store.manifest_progress(args.run_id)
        out = {
            "pid": _os.getpid(),
            "ppid": _os.getppid(),
            "run_id": args.run_id,
            "invocation_marker": args.invocation_marker,
            "thread_id": result.thread_id,
            "resumed": result.resumed,
            "graph_id": result.graph_id,
            "manifest_revision": contract.manifest_revision,
            "manifest_fingerprint": result.manifest_fingerprint,
            "nodes": [
                {"node_id": nr.node_id, "status": nr.status, "reused": nr.reused,
                 "work_event_sequence": nr.work_event_sequence}
                for nr in result.node_results
            ],
            "progress": progress,
            "stop_after_node": args.stop_after_node,
            "work_event_count": events.count(args.run_id),
            "distinct_idempotency_keys": events.distinct_idempotency_keys(args.run_id),
            "checkpoint_db": str(adapter.checkpoint_db),
        }
        sys.stdout.write("LG_ADAPTER_RESULT=" + _json.dumps(out, sort_keys=True) + "\n")
        sys.stdout.flush()
        return 0
    finally:
        adapter.close()
        events.close()
        store.close()


if __name__ == "__main__":
    raise SystemExit(adapter_main())
