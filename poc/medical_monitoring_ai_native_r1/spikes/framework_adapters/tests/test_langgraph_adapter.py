"""Focused tests for the LangGraph adapter (worker_02-owned spike).

Proves (execution context: Shared Contract And Required Evidence / Acceptance):
  * the adapter is a REAL accepted ``GraphPort`` implementation (isinstance +
    exact public method behavior) and a physically separate checkpoint DB;
  * REAL LangGraph/checkpointer types are exercised;
  * exact structured work events (13 required fields, manifest-derived progress);
  * a first subprocess stops at the shared injected boundary after node 1;
  * a FRESH subprocess resumes from the persisted framework checkpoint plus the
    authoritative Store and completes;
  * no duplicate node side effect / artifact / event after restart or replay;
  * replay normalizes to the same committed result;
  * corrupt or mismatched run/thread metadata OR checkpoint state/blob fails
    closed WITHOUT changing the domain Store or work-event stream;
  * serialization evidence: checkpoint + writes tables carry msgpack-typed
    blobs, strict msgpack is active, no pickle serializer/type is used;
  * security probes are non-exploitative configuration/validation checks only.

Runs only in the authorized disposable LangGraph venv; no network/service.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import json
import subprocess
from pathlib import Path

import pytest

# conftest resolves slice1 + spike src onto sys.path
from mm_r1.store import Store
from mm_r1.domain import TERMINAL_NODE_STATUSES, NodeStatus
from mm_r1.graph import GraphPort, GraphRun, Graph

from mm_r1_spike.contract import ConformanceContract, REQUIRED_WORK_EVENT_FIELDS
from mm_r1_spike.work_events import WorkEventStore
from mm_r1_spike.restart_harness import (
    NODE_A, NODE_B, NODE_C,
    bootstrap_run,
    synthetic_three_node_graph,
)
from mm_r1_spike.langgraph_adapter import (
    ALLOWED_METADATA_KEYS,
    CHECKPOINTER_DB_NAME,
    LANGGRAPH_VERSION_TARGET,
    CHECKPOINT_SQLITE_VERSION_TARGET,
    LangGraphAdapter,
    LangGraphCheckpointIdentityError,
    thread_key,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _new_adapter(tmp_path):
    work = tmp_path / "lg_work"
    work.mkdir(parents=True, exist_ok=True)
    store = Store(work / "authoritative.sqlite3", work / "artifacts")
    events = WorkEventStore(work / "work_events.sqlite3")
    ad = LangGraphAdapter(store, events, work)
    return store, events, ad, work


def _parse_result(stdout: str) -> dict:
    for line in stdout.splitlines():
        if line.startswith("LG_ADAPTER_RESULT="):
            return json.loads(line[len("LG_ADAPTER_RESULT="):])
    raise AssertionError(f"no LG_ADAPTER_RESULT in stdout:\n{stdout}")


def _run_adapter_subprocess(work_dir, run_id, *, stop=None, bootstrap=False,
                            marker="m", src_paths=None, py=None):
    py = py or sys.executable
    env = dict(os.environ)
    env["LANGGRAPH_STRICT_MSGPACK"] = "true"
    env["PYTHONPATH"] = os.pathsep.join(str(p) for p in (src_paths or []))
    argv = [py, "-m", "mm_r1_spike.langgraph_adapter",
            "--work-dir", str(work_dir), "--run-id", run_id,
            "--invocation-marker", marker, "--manifest-revision", "1"]
    if stop:
        argv += ["--stop-after-node", stop]
    if bootstrap:
        argv += ["--bootstrap"]
    return subprocess.run(argv, capture_output=True, text=True, env=env)


def _frozen_graph(run_id):
    """Build the accepted Graph IR from the frozen manifest for ``run_id``."""
    return synthetic_three_node_graph()


# ---------------------------------------------------------------------------
# framework primitive evidence
# ---------------------------------------------------------------------------

class TestRealFrameworkPrimitives:
    def test_strict_msgpack_enabled(self):
        from mm_r1_spike.langgraph_adapter import _lg_msgpack
        assert _lg_msgpack.STRICT_MSGPACK_ENABLED is True

    def test_pinned_versions_installed(self):
        import importlib.metadata as md
        assert md.version("langgraph") == LANGGRAPH_VERSION_TARGET
        assert md.version("langgraph-checkpoint-sqlite") == CHECKPOINT_SQLITE_VERSION_TARGET

    def test_adapter_uses_real_stategraph_and_sqlitesaver(self, tmp_path):
        from langgraph.graph import StateGraph
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            assert isinstance(ad.saver, __import__(
                "langgraph.checkpoint.sqlite", fromlist=["SqliteSaver"]).SqliteSaver)
            # build a real compiled graph and confirm the StateGraph type
            manifest = bootstrap_run(store, "run-types")
            contract = ConformanceContract.from_manifest(manifest)
            sg = ad._build_state_graph(manifest, contract, manifest.revision)
            assert isinstance(sg, StateGraph)
            app = sg.compile(checkpointer=ad.saver)
            assert hasattr(app, "invoke") and hasattr(app, "get_state")
        finally:
            ad.close(); events.close(); store.close()

    def test_checkpoint_db_is_physically_separate(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-sep")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract, stop_after_node=NODE_A)
            # three distinct physical files
            assert (work / "authoritative.sqlite3").exists()
            assert (work / "work_events.sqlite3").exists()
            assert (work / CHECKPOINTER_DB_NAME).exists()
            # checkpoint DB is a different file from the Store DB
            assert (work / CHECKPOINTER_DB_NAME) != (work / "authoritative.sqlite3")
            # checkpoint DB has the langgraph schema, not the domain schema
            c = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
            tables = {r[0] for r in c.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            assert {"checkpoints", "writes"} <= tables
            # domain tables must NOT be in the checkpoint DB
            assert "node_runs" not in tables
            assert "artifacts" not in tables
            # at least one checkpoint row was persisted
            assert c.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0] >= 1
            c.close()
            # domain Store DB must NOT contain langgraph checkpoint tables
            c2 = sqlite3.connect(str(work / "authoritative.sqlite3"))
            dom_tables = {r[0] for r in c2.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            assert "writes" not in dom_tables
            c2.close()
        finally:
            ad.close(); events.close(); store.close()


# ---------------------------------------------------------------------------
# accepted public GraphPort API
# ---------------------------------------------------------------------------

class TestAcceptedGraphPortAPI:
    def test_adapter_is_graphport_instance(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            assert isinstance(ad, GraphPort)
        finally:
            ad.close(); events.close(); store.close()

    def test_public_methods_have_accepted_signatures(self):
        import inspect
        run_sig = inspect.signature(LangGraphAdapter.run)
        assert list(run_sig.parameters)[1:] == ["graph", "run_id", "context", "auto_finalize"]
        resume_sig = inspect.signature(LangGraphAdapter.resume)
        assert list(resume_sig.parameters)[1:] == ["run_id"]
        replay_sig = inspect.signature(LangGraphAdapter.replay)
        assert list(replay_sig.parameters)[1:] == ["run_id"]

    def test_run_returns_graphrun_and_completes(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-pub")
            graph = _frozen_graph("run-pub")
            r = ad.run(graph, "run-pub")
            assert isinstance(r, GraphRun)
            assert r.run_id == "run-pub"
            assert r.status == "complete"
            assert all(nr.status == NodeStatus.PASSED for nr in r.node_results)
            assert [nr.node_id for nr in r.node_results] == [NODE_A, NODE_B, NODE_C]
            assert store.manifest_progress("run-pub")["completed"] == 3
        finally:
            ad.close(); events.close(); store.close()

    def test_run_fail_closed_on_wrong_graph(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-wg")
            # supply a graph with a different graph_id
            wrong = Graph(graph_id="DIFFERENT-GRAPH")
            with pytest.raises(LangGraphCheckpointIdentityError):
                ad.run(wrong, "run-wg")
            # Store unchanged: no nodes committed
            assert store.manifest_progress("run-wg")["completed"] == 0
        finally:
            ad.close(); events.close(); store.close()

    def test_run_fail_closed_on_unknown_run(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            graph = _frozen_graph("nope")
            with pytest.raises(RuntimeError):
                ad.run(graph, "run-not-frozen")
        finally:
            ad.close(); events.close(); store.close()

    def test_resume_returns_graphrun_after_boundary(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-pubres")
            contract = ConformanceContract.from_manifest(manifest)
            graph = _frozen_graph("run-pubres")
            # inject a boundary via the private spike method, then resume publicly
            ad._run_contract(contract, stop_after_node=NODE_A)
            assert store.manifest_progress("run-pubres")["completed"] == 1
            r = ad.resume("run-pubres")
            assert isinstance(r, GraphRun)
            assert r.status == "complete"
            assert store.manifest_progress("run-pubres")["completed"] == 3
        finally:
            ad.close(); events.close(); store.close()

    def test_replay_returns_graphrun_all_reused(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-pubrep")
            graph = _frozen_graph("run-pubrep")
            ad.run(graph, "run-pubrep")
            ev_before = events.count("run-pubrep")
            r = ad.replay("run-pubrep")
            assert isinstance(r, GraphRun)
            assert r.status == "complete"
            assert all(nr.reused for nr in r.node_results)
            # no duplicate events after replay
            assert events.count("run-pubrep") == ev_before
        finally:
            ad.close(); events.close(); store.close()


# ---------------------------------------------------------------------------
# exact structured work events
# ---------------------------------------------------------------------------

class TestExactWorkEvents:
    def test_events_carry_all_required_fields_and_manifest_progress(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-events")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract)  # complete run
            evs = events.list_events("run-events")
            assert len(evs) == 6  # begin+complete per node x 3
            for ev in evs:
                d = ev.to_json()
                for f in REQUIRED_WORK_EVENT_FIELDS:
                    assert f in d, f"event missing {f}"
                assert d["total"] == contract.total_units == 3
                assert 0 <= d["completed"] <= 3
            # begin events precede complete events per node; sequences monotonic
            seqs = [e.sequence for e in evs]
            assert seqs == sorted(seqs)
            assert len(set(e.idempotency_key for e in evs)) == 6
        finally:
            ad.close(); events.close(); store.close()

    def test_no_duplicate_event_on_resume(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-dedup")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract, stop_after_node=NODE_A)
            assert events.count("run-dedup") == 2
            ad._run_contract(contract)  # resume
            assert events.count("run-dedup") == 6  # no duplicate for node A
        finally:
            ad.close(); events.close(); store.close()


# ---------------------------------------------------------------------------
# in-process stop/resume/replay (no subprocess)
# ---------------------------------------------------------------------------

class TestInProcessStopResumeReplay:
    def test_stop_after_node_a_then_resume_completes(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-inproc")
            contract = ConformanceContract.from_manifest(manifest)
            r1 = ad._run_contract(contract, stop_after_node=NODE_A)
            assert r1.progress["completed"] == 1
            assert [n.status for n in r1.node_results] == ["passed", "pending", "pending"]
            assert r1.node_results[0].reused is False
            r2 = ad._run_contract(contract)
            assert r2.resumed is True
            assert r2.progress["completed"] == 3
            # node A reused in resume; B and C freshly executed
            reused = {n.node_id: n.reused for n in r2.node_results}
            assert reused == {NODE_A: True, NODE_B: False, NODE_C: False}
        finally:
            ad.close(); events.close(); store.close()

    def test_no_duplicate_domain_side_effect_on_resume(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-nodupe")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract, stop_after_node=NODE_A)
            ad._run_contract(contract)
            # exactly one node_run row per node, all passed, attempts=1
            conn = sqlite3.connect(str(work / "authoritative.sqlite3"))
            rows = conn.execute(
                "SELECT node_id, status, attempts FROM node_runs WHERE run_id=? ORDER BY node_id",
                ("run-nodupe",),
            ).fetchall()
            conn.close()
            assert len(rows) == 3
            assert all(r[1] == "passed" for r in rows)
            assert [r[2] for r in rows] == [1, 1, 1]
        finally:
            ad.close(); events.close(); store.close()

    def test_replay_all_reused_same_result(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-replay")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract)
            before = store.manifest_progress("run-replay")
            ev_before = [(e.node_id, e.phase, e.sequence, e.status) for e in events.list_events("run-replay")]
            r = ad._run_contract(contract)
            assert all(n.reused for n in r.node_results)
            after = store.manifest_progress("run-replay")
            assert before == after
            # no new events after replay
            ev_after = [(e.node_id, e.phase, e.sequence, e.status) for e in events.list_events("run-replay")]
            assert ev_before == ev_after
            assert events.count("run-replay") == 6
        finally:
            ad.close(); events.close(); store.close()

    def test_replay_public_rejects_re_executed_node(self, tmp_path):
        """Public replay must raise if any node was not reused (contract:
        replay must only reuse committed results)."""
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-replay-raise")
            contract = ConformanceContract.from_manifest(manifest)
            # run only node A, leave B/C uncommitted
            ad._run_contract(contract, stop_after_node=NODE_A)
            # public replay against an incomplete run must raise (B/C not reused)
            with pytest.raises(RuntimeError):
                ad.replay("run-replay-raise")
        finally:
            ad.close(); events.close(); store.close()

    def test_framework_state_never_enters_domain_authority(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-noauth")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract)
            conn = sqlite3.connect(str(work / "authoritative.sqlite3"))
            art_count = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
            fact_count = conn.execute("SELECT COUNT(*) FROM canonical_facts").fetchone()[0]
            conn.close()
            assert art_count == 0  # synthetic nodes are artifact_required=False
            assert fact_count == 0
        finally:
            ad.close(); events.close(); store.close()


# ---------------------------------------------------------------------------
# REAL two-process subprocess boundary
# ---------------------------------------------------------------------------

class TestSubprocessBoundary:
    def test_two_fresh_processes_complete_run_with_distinct_pids(
        self, tmp_path, src_paths
    ):
        work = tmp_path / "sub_work"
        work.mkdir(parents=True, exist_ok=True)
        run_id = "run-sub-lg"
        py = "/tmp/mm_r1_slice2_langgraph.7esOy8/venv/bin/python"
        a = _run_adapter_subprocess(
            work, run_id, stop=NODE_A, bootstrap=True, marker="proc-A",
            src_paths=src_paths, py=py,
        )
        assert a.returncode == 0, f"proc A failed:\n{a.stderr}"
        a_res = _parse_result(a.stdout)
        assert a_res["pid"] > 0
        assert a_res["resumed"] is False
        assert a_res["progress"]["completed"] == 1
        assert a_res["progress"]["total"] == 3
        assert [n["node_id"] for n in a_res["nodes"]] == [NODE_A, NODE_B, NODE_C]
        assert a_res["nodes"][0]["reused"] is False
        assert a_res["work_event_count"] == 2

        b = _run_adapter_subprocess(
            work, run_id, stop=None, bootstrap=False, marker="proc-B",
            src_paths=src_paths, py=py,
        )
        assert b.returncode == 0, f"proc B failed:\n{b.stderr}"
        b_res = _parse_result(b.stdout)
        assert b_res["pid"] > 0
        assert b_res["resumed"] is True
        assert a_res["pid"] != b_res["pid"], "subprocess boundary not observed"
        reused = {n["node_id"]: n["reused"] for n in b_res["nodes"]}
        assert reused == {NODE_A: True, NODE_B: False, NODE_C: False}
        assert b_res["progress"]["completed"] == 3
        assert b_res["work_event_count"] == 6
        # deterministic thread id identical across processes
        assert a_res["thread_id"] == b_res["thread_id"]
        # manifest fingerprint identical across processes
        assert a_res["manifest_fingerprint"] == b_res["manifest_fingerprint"]

        # persisted Store: one row per node, all passed, attempts=1, no dupes
        conn = sqlite3.connect(str(work / "authoritative.sqlite3"))
        rows = conn.execute(
            "SELECT node_id, status, attempts FROM node_runs WHERE run_id=? ORDER BY node_id",
            (run_id,),
        ).fetchall()
        art = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
        facts = conn.execute("SELECT COUNT(*) FROM canonical_facts").fetchone()[0]
        conn.close()
        assert len(rows) == 3
        assert all(r[1] == "passed" for r in rows)
        assert [r[2] for r in rows] == [1, 1, 1]
        assert art == 0 and facts == 0

    def test_subprocess_persistence_files_separate(self, tmp_path, src_paths):
        work = tmp_path / "sub_files"
        work.mkdir(parents=True, exist_ok=True)
        run_id = "run-sub-files-lg"
        py = "/tmp/mm_r1_slice2_langgraph.7esOy8/venv/bin/python"
        _run_adapter_subprocess(work, run_id, stop=NODE_A, bootstrap=True,
                                marker="A", src_paths=src_paths, py=py)
        _run_adapter_subprocess(work, run_id, stop=None, bootstrap=False,
                                marker="B", src_paths=src_paths, py=py)
        # four separate physical persistence artifacts
        assert (work / "authoritative.sqlite3").exists()
        assert (work / "work_events.sqlite3").exists()
        assert (work / CHECKPOINTER_DB_NAME).exists()
        # checkpoint DB has real langgraph rows
        c = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
        assert c.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0] >= 1
        c.close()
        # work events: 6 deduped
        c = sqlite3.connect(str(work / "work_events.sqlite3"))
        n = c.execute("SELECT COUNT(*) FROM work_events WHERE run_id=?", (run_id,)).fetchone()[0]
        c.close()
        assert n == 6

    def test_idempotent_replay_subprocess_no_duplicate(self, tmp_path, src_paths):
        work = tmp_path / "sub_replay"
        work.mkdir(parents=True, exist_ok=True)
        run_id = "run-sub-replay-lg"
        py = "/tmp/mm_r1_slice2_langgraph.7esOy8/venv/bin/python"
        _run_adapter_subprocess(work, run_id, stop=NODE_A, bootstrap=True,
                                marker="p1", src_paths=src_paths, py=py)
        _run_adapter_subprocess(work, run_id, stop=None, bootstrap=False,
                                marker="p2", src_paths=src_paths, py=py)
        # third invocation: all reused
        p3 = _run_adapter_subprocess(work, run_id, stop=None, bootstrap=False,
                                     marker="p3", src_paths=src_paths, py=py)
        assert p3.returncode == 0, p3.stderr
        p3_res = _parse_result(p3.stdout)
        assert all(n["reused"] for n in p3_res["nodes"])
        c = sqlite3.connect(str(work / "work_events.sqlite3"))
        n = c.execute("SELECT COUNT(*) FROM work_events WHERE run_id=?", (run_id,)).fetchone()[0]
        c.close()
        assert n == 6  # no duplicate events


# ---------------------------------------------------------------------------
# checkpoint identity fail-closed (corrupt / mismatched metadata / state)
# ---------------------------------------------------------------------------

class TestCheckpointIdentityFailClosed:
    def _setup_run(self, tmp_path, run_id="run-fc"):
        store, events, ad, work = _new_adapter(tmp_path)
        manifest = bootstrap_run(store, run_id)
        contract = ConformanceContract.from_manifest(manifest)
        ad._run_contract(contract, stop_after_node=NODE_A)
        tid = thread_key(run_id, contract.manifest_fingerprint)
        ad.close(); events.close(); store.close()
        return work, contract, tid

    def test_non_allowlisted_metadata_key_fails_closed(self, tmp_path):
        work, contract, tid = self._setup_run(tmp_path)
        conn = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
        conn.execute(
            "UPDATE checkpoints SET metadata=? WHERE thread_id=?",
            (b'{"source":"loop","step":1,"evil":"x"}', tid),
        )
        conn.commit(); conn.close()
        store = Store(work / "authoritative.sqlite3", work / "artifacts")
        events = WorkEventStore(work / "work_events.sqlite3")
        ad = LangGraphAdapter(store, events, work)
        with pytest.raises(LangGraphCheckpointIdentityError):
            ad.verify_checkpoint_identity(contract, tid)
        # Store unchanged
        assert store.manifest_progress(contract.run_id)["completed"] == 1
        ad.close(); events.close(); store.close()

    def test_mismatched_run_id_fails_closed(self, tmp_path):
        work, contract, tid = self._setup_run(tmp_path)
        conn = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
        conn.execute(
            "UPDATE checkpoints SET metadata=? WHERE thread_id=?",
            (b'{"source":"loop","step":1,"run_id":"run-DIFFERENT"}', tid),
        )
        conn.commit(); conn.close()
        store = Store(work / "authoritative.sqlite3", work / "artifacts")
        events = WorkEventStore(work / "work_events.sqlite3")
        ad = LangGraphAdapter(store, events, work)
        with pytest.raises(LangGraphCheckpointIdentityError):
            ad.verify_checkpoint_identity(contract, tid)
        assert store.manifest_progress(contract.run_id)["completed"] == 1
        ad.close(); events.close(); store.close()

    def test_missing_metadata_run_id_fails_closed(self, tmp_path):
        """Missing 'run_id' in persisted metadata is failure, not accepted."""
        work, contract, tid = self._setup_run(tmp_path)
        conn = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
        conn.execute(
            "UPDATE checkpoints SET metadata=? WHERE thread_id=?",
            (b'{"source":"loop","step":1}', tid),
        )
        conn.commit(); conn.close()
        store = Store(work / "authoritative.sqlite3", work / "artifacts")
        events = WorkEventStore(work / "work_events.sqlite3")
        ad = LangGraphAdapter(store, events, work)
        with pytest.raises(LangGraphCheckpointIdentityError):
            ad.verify_checkpoint_identity(contract, tid)
        assert store.manifest_progress(contract.run_id)["completed"] == 1
        ad.close(); events.close(); store.close()

    def test_corrupt_metadata_fails_closed(self, tmp_path):
        work, contract, tid = self._setup_run(tmp_path)
        conn = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
        conn.execute(
            "UPDATE checkpoints SET metadata=? WHERE thread_id=?",
            (b'\x00\x01 not json', tid),
        )
        conn.commit(); conn.close()
        store = Store(work / "authoritative.sqlite3", work / "artifacts")
        events = WorkEventStore(work / "work_events.sqlite3")
        ad = LangGraphAdapter(store, events, work)
        with pytest.raises(LangGraphCheckpointIdentityError):
            ad.verify_checkpoint_identity(contract, tid)
        assert store.manifest_progress(contract.run_id)["completed"] == 1
        ad.close(); events.close(); store.close()

    def test_corrupt_checkpoint_state_blob_fails_closed(self, tmp_path):
        """A corrupt (empty) checkpoint state blob must fail closed, not just
        corrupt metadata."""
        work, contract, tid = self._setup_run(tmp_path)
        conn = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
        conn.execute(
            "UPDATE checkpoints SET checkpoint=? WHERE thread_id=? "
            "AND checkpoint_id=(SELECT MAX(checkpoint_id) FROM checkpoints WHERE thread_id=?)",
            (b"", tid, tid),
        )
        conn.commit(); conn.close()
        store = Store(work / "authoritative.sqlite3", work / "artifacts")
        events = WorkEventStore(work / "work_events.sqlite3")
        ad = LangGraphAdapter(store, events, work)
        with pytest.raises(LangGraphCheckpointIdentityError):
            ad.verify_checkpoint_identity(contract, tid)
        assert store.manifest_progress(contract.run_id)["completed"] == 1
        ad.close(); events.close(); store.close()

    def test_null_checkpoint_state_blob_fails_closed(self, tmp_path):
        """A NULL checkpoint state blob must fail closed."""
        work, contract, tid = self._setup_run(tmp_path)
        conn = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
        conn.execute(
            "UPDATE checkpoints SET checkpoint=NULL WHERE thread_id=? "
            "AND checkpoint_id=(SELECT MAX(checkpoint_id) FROM checkpoints WHERE thread_id=?)",
            (tid, tid),
        )
        conn.commit(); conn.close()
        store = Store(work / "authoritative.sqlite3", work / "artifacts")
        events = WorkEventStore(work / "work_events.sqlite3")
        ad = LangGraphAdapter(store, events, work)
        with pytest.raises(LangGraphCheckpointIdentityError):
            ad.verify_checkpoint_identity(contract, tid)
        assert store.manifest_progress(contract.run_id)["completed"] == 1
        ad.close(); events.close(); store.close()

    def test_run_with_corrupt_checkpoint_does_not_mutate_store(self, tmp_path):
        work, contract, tid = self._setup_run(tmp_path)
        conn = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
        conn.execute(
            "UPDATE checkpoints SET metadata=? WHERE thread_id=?",
            (b'{"source":"loop","step":1,"run_id":"run-OTHER"}', tid),
        )
        conn.commit(); conn.close()
        store = Store(work / "authoritative.sqlite3", work / "artifacts")
        events = WorkEventStore(work / "work_events.sqlite3")
        ad = LangGraphAdapter(store, events, work)
        before = store.manifest_progress(contract.run_id)
        ev_before = events.count(contract.run_id)
        with pytest.raises(LangGraphCheckpointIdentityError):
            ad._run_contract(contract)
        after = store.manifest_progress(contract.run_id)
        assert before == after  # domain Store not mutated by the failed run
        assert events.count(contract.run_id) == ev_before  # no new work events
        ad.close(); events.close(); store.close()

    def test_stale_contract_fails_closed_on_run(self, tmp_path):
        """A contract that does not match the frozen manifest for the run
        (e.g. a stale externally-constructed contract) must fail closed before
        touching domain/event state."""
        work, contract, tid = self._setup_run(tmp_path)
        store = Store(work / "authoritative.sqlite3", work / "artifacts")
        events = WorkEventStore(work / "work_events.sqlite3")
        ad = LangGraphAdapter(store, events, work)
        # fabricate a stale contract: same run but wrong manifest_fingerprint
        from dataclasses import replace
        stale = replace(contract, manifest_fingerprint="stale-fp-not-the-real-one")
        before = store.manifest_progress(contract.run_id)
        ev_before = events.count(contract.run_id)
        with pytest.raises(LangGraphCheckpointIdentityError):
            ad._run_contract(stale)
        assert store.manifest_progress(contract.run_id) == before
        assert events.count(contract.run_id) == ev_before
        ad.close(); events.close(); store.close()

    def test_different_manifest_fingerprint_different_thread(self, tmp_path):
        """Two runs sharing run_id/graph/revision wording but having different
        frozen manifests must produce DIFFERENT thread ids (fingerprint-bound)."""
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            m1 = bootstrap_run(store, "run-fp1")
            c1 = ConformanceContract.from_manifest(m1)
            t1 = thread_key("run-fp1", c1.manifest_fingerprint)
            # a different fingerprint yields a different thread id
            t2 = thread_key("run-fp1", "some-other-fingerprint")
            assert t1 != t2
            assert t1.startswith("run:run-fp1:fp:")
        finally:
            ad.close(); events.close(); store.close()

    def test_wrong_public_graph_does_not_mutate_store(self, tmp_path):
        """Public run with a graph that does not match the frozen manifest must
        fail closed and leave Store/work-event state unchanged."""
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-wpg")
            before = store.manifest_progress("run-wpg")
            ev_before = events.count("run-wpg")
            wrong = Graph(graph_id="WRONG")
            with pytest.raises(LangGraphCheckpointIdentityError):
                ad.run(wrong, "run-wpg")
            assert store.manifest_progress("run-wpg") == before
            assert events.count("run-wpg") == ev_before
        finally:
            ad.close(); events.close(); store.close()


# ---------------------------------------------------------------------------
# serialization evidence (checkpoint + writes tables; strict msgpack; no pickle)
# ---------------------------------------------------------------------------

class TestSerializationEvidence:
    def test_checkpoint_and_writes_tables_have_typed_blobs(self, tmp_path):
        """After a run, both the checkpoints and writes tables must carry rows
        with non-null type/blob columns (msgpack-typed serialized framework state)."""
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-ser")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract)
            c = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
            ckpt_rows = c.execute(
                "SELECT type, checkpoint, metadata FROM checkpoints"
            ).fetchall()
            write_rows = c.execute(
                "SELECT type, value FROM writes"
            ).fetchall()
            c.close()
            # checkpoint rows: at least one, each with a non-empty blob
            assert len(ckpt_rows) >= 1
            for typ, blob, meta in ckpt_rows:
                assert typ is not None  # type discriminator present
                assert blob is not None and len(blob) > 0  # state blob present
                assert meta is not None and len(meta) > 0  # metadata present
            # writes rows: node channel writes are persisted with type+value
            assert len(write_rows) >= 1
            for typ, val in write_rows:
                assert typ is not None
        finally:
            ad.close(); events.close(); store.close()

    def test_checkpoint_metadata_is_json_with_allowlisted_keys_only(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-mk")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract)
            c = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
            metas = [row[0] for row in c.execute("SELECT metadata FROM checkpoints")]
            c.close()
            assert len(metas) >= 1
            for meta in metas:
                d = json.loads(meta)
                assert set(d.keys()) <= ALLOWED_METADATA_KEYS
                # run_id binding present (static allowlisted key we trust)
                assert "run_id" in d
                assert d["run_id"] == "run-mk"
        finally:
            ad.close(); events.close(); store.close()

    def test_no_pickle_serializer_type_in_framework_state(self, tmp_path):
        """Framework checkpoint/writes blobs must use the msgpack/json serializer
        (strict mode), never the pickle serializer.  The ``type`` discriminator
        column in each table identifies the serializer; a pickle row would carry
        ``type='pickle'``.  We assert no pickle-typed row exists.

        (Note: a lone ``0x80`` byte is msgpack's empty-map marker, not a pickle
        protocol marker -- pickle streams are ``0x80 <version-byte>``.  We rely
        on the explicit type column rather than byte-prefix sniffing.)"""
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-pickle")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract)
            c = sqlite3.connect(str(work / CHECKPOINTER_DB_NAME))
            ckpt_types = [r[0] for r in c.execute("SELECT type FROM checkpoints")]
            write_types = [r[0] for r in c.execute("SELECT type FROM writes")]
            c.close()
            # No row may declare the pickle serializer
            assert "pickle" not in ckpt_types
            assert "pickle" not in write_types
            # The synthetic state is serialized as msgpack/json (strict mode)
            assert any(t in ("msgpack", "json") for t in ckpt_types)
        finally:
            ad.close(); events.close(); store.close()

    def test_checkpoint_db_is_untrusted_separate_persistence(self, tmp_path):
        """Deleting the checkpoint DB must not corrupt the authoritative Store."""
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-untrusted")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract, stop_after_node=NODE_A)
            progress_with_ckpt = store.manifest_progress("run-untrusted")
            ad.close(); events.close(); store.close()
            # remove the framework checkpoint DB entirely
            (work / CHECKPOINTER_DB_NAME).unlink()
            # reopen Store: domain authority intact
            store2 = Store(work / "authoritative.sqlite3", work / "artifacts")
            assert store2.manifest_progress("run-untrusted") == progress_with_ckpt
            store2.close()
        finally:
            pass


# ---------------------------------------------------------------------------
# security probes (non-exploitative configuration / validation checks only)
# ---------------------------------------------------------------------------

class TestSecurityProbes:
    def test_strict_msgpack_flag_reflected_in_framework(self):
        from mm_r1_spike.langgraph_adapter import _lg_msgpack
        assert _lg_msgpack.STRICT_MSGPACK_ENABLED is True
        # the framework module exposes the safe-type allowlist
        assert hasattr(_lg_msgpack, "SAFE_MSGPACK_TYPES")

    def test_allowlist_covers_only_expected_metadata_keys(self):
        expected = {"source", "step", "parents", "run_id",
                    "counters_since_delta_snapshot"}
        assert ALLOWED_METADATA_KEYS == expected


# ---------------------------------------------------------------------------
# Manager repair regressions (2026-08-09)
# ---------------------------------------------------------------------------

class TestManagerRepairRegressions:
    """Regressions for manager-mandated public-contract repairs."""

    def test_public_run_marks_fresh_nodes_not_reused(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            bootstrap_run(store, "run-mgr-reuse")
            graph = _frozen_graph("run-mgr-reuse")
            r = ad.run(graph, "run-mgr-reuse")
            assert all(nr.reused is False for nr in r.node_results)
        finally:
            ad.close(); events.close(); store.close()

    def test_public_resume_marks_only_precommitted_reused(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-mgr-res")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract, stop_after_node=NODE_A)
            r = ad.resume("run-mgr-res")
            reused = {nr.node_id: nr.reused for nr in r.node_results}
            assert reused == {NODE_A: True, NODE_B: False, NODE_C: False}
        finally:
            ad.close(); events.close(); store.close()

    def test_public_resume_missing_checkpoint_fails_closed_no_mutation(self, tmp_path):
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-mgr-miss")
            contract = ConformanceContract.from_manifest(manifest)
            ad._run_contract(contract, stop_after_node=NODE_A)
            before = store.manifest_progress("run-mgr-miss")
            ev_before = events.count("run-mgr-miss")
            ad.close()
            (work / CHECKPOINTER_DB_NAME).unlink()
            # reopen against empty/missing framework checkpoint
            ad2 = LangGraphAdapter(store, events, work)
            with pytest.raises(LangGraphCheckpointIdentityError):
                ad2.resume("run-mgr-miss")
            assert store.manifest_progress("run-mgr-miss") == before
            assert events.count("run-mgr-miss") == ev_before
            ad2.close()
        finally:
            events.close(); store.close()

    def test_altered_edge_graph_rejected_before_mutation(self, tmp_path):
        from mm_r1.graph import Graph, GraphNode, GraphEdge
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            manifest = bootstrap_run(store, "run-mgr-bind")
            nodes = {
                n.node_id: GraphNode(
                    node_id=n.node_id, node_type=n.node_type,
                    handler=n.handler, description=n.description,
                    mandatory=n.mandatory, max_attempts=n.max_attempts,
                    artifact_required=n.artifact_required,
                )
                for n in synthetic_three_node_graph().nodes.values()
            }
            altered = Graph(
                graph_id=manifest.graph_id,
                nodes=nodes,
                edges=[
                    GraphEdge(src=NODE_B, dst=NODE_A),
                    GraphEdge(src=NODE_A, dst=NODE_C),
                ],
            )
            with pytest.raises(LangGraphCheckpointIdentityError):
                ad.run(altered, "run-mgr-bind")
            assert store.manifest_progress("run-mgr-bind")["completed"] == 0
            assert events.count("run-mgr-bind") == 0
        finally:
            ad.close(); events.close(); store.close()

    def test_unexpected_finalization_error_propagates(self, tmp_path, monkeypatch):
        """C-LG-FINALIZE: non-CompletionGateError during finalize must propagate."""
        store, events, ad, work = _new_adapter(tmp_path)
        try:
            bootstrap_run(store, "run-mgr-fin")
            graph = _frozen_graph("run-mgr-fin")

            def boom(*_a, **_k):
                raise RuntimeError("unexpected finalization boom")

            monkeypatch.setattr(store, "complete_analysis", boom)
            with pytest.raises(RuntimeError, match="unexpected finalization boom"):
                ad.run(graph, "run-mgr-fin", auto_finalize=True)
        finally:
            ad.close(); events.close(); store.close()
