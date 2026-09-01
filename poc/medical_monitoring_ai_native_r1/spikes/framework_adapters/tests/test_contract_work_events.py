"""Framework-neutral conformance contract, work-event store, and subprocess
restart/replay harness tests (worker_01-owned).

These tests prove the spike substrate invariants required by the execution
context:
  * work events carry every required field and idempotency rule;
  * events are append-only, ordered, and deduplicated on idempotency key;
  * divergent reuse of an idempotency key is rejected (never overwrite);
  * exact progress (completed/total) is derived from the frozen manifest;
  * a real two-process boundary: process A stops after node A and exits;
    a FRESH process B resumes against persisted Store + separate work-event
    + JSON checkpoint persistence and finishes, with distinct PIDs and no
    duplicate side effects;
  * the authoritative slice1 Store semantics are unchanged: no work event
    or checkpoint promoted to domain authority.

Run only the focused check (no installation/network/service):
    PYTHONPATH=poc/medical_monitoring_ai_native_r1/src:poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/src \
      /tmp/mm_r1_slice2_langgraph.7esOy8/venv/bin/python -m pytest -q \
      poc/medical_monitoring_ai_native_r1/spikes/framework_adapters/tests/test_contract_work_events.py
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

from mm_r1.domain import (
    ExecutionManifest,
    ManifestNode,
    NodeStatus,
    NodeType,
    content_hash,
    now_iso,
)
from mm_r1.store import Store

from mm_r1_spike.contract import (
    ConformanceContract,
    ConformanceResult,
    NodeConformance,
    REQUIRED_WORK_EVENT_FIELDS,
    WORK_EVENT_STATUSES,
    is_completed_terminal,
)
from mm_r1_spike.restart_harness import (
    NODE_A,
    NODE_B,
    NODE_C,
    SYNTH_GRAPH_ID,
    CheckpointIdentityError,
    checkpoint_path,
    load_operational_checkpoint,
    save_operational_checkpoint,
    run_nodes_up_to_boundary,
    run_subprocess_worker,
    bootstrap_run,
    synthetic_manifest,
    synthetic_three_node_graph,
)
from mm_r1_spike.work_events import (
    WorkEventConflictError,
    WorkEventError,
    WorkEventStore,
    derive_progress,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _manifest(run_id: str = "run-conformance", nodes=3, revision: int = 1) -> ExecutionManifest:
    node_ids = [NODE_A, NODE_B, NODE_C][:nodes]
    return ExecutionManifest(
        run_id=run_id,
        nodes=[
            ManifestNode(node_id=nid, node_type=NodeType.DETERMINISTIC_SERVICE)
            for nid in node_ids
        ],
        revision=revision,
        graph_id=SYNTH_GRAPH_ID,
        identity_algorithm="synth-identity-v1",
        graph_version="synth-three-node-v1",
        schema_version="synth-schema-v1",
    )


def _event(contract: ConformanceContract, node_id: str, phase: str,
           status: str, completed: int, *, run_id: str | None = None,
           idempotency_key: str | None = None,
           work_unit_id: str | None = None, current_detail: str | None = None):
    from mm_r1.domain import new_id

    rid = run_id or contract.run_id
    return {
        "event_id": new_id("we_"),
        "run_id": rid,
        "manifest_revision": contract.manifest_revision,
        "sequence": 0,
        "node_id": node_id,
        "work_unit_id": work_unit_id or node_id,
        "phase": phase,
        "status": status,
        "completed": completed,
        "total": contract.total_units,
        "current_detail": current_detail or f"{phase}:{node_id}",
        "created_at": now_iso(),
        "idempotency_key": idempotency_key or f"we:{rid}:{node_id}:{phase}",
    }


# ===========================================================================
# conformance contract
# ===========================================================================

class TestConformanceContract:
    def test_contract_fields_and_required_event_fields(self):
        manifest = _manifest()
        contract = ConformanceContract.from_manifest(manifest)
        assert contract.run_id == "run-conformance"
        assert contract.manifest_revision == 1
        assert contract.total_units == 3
        # every execution-context-required field is declared exactly once
        assert tuple(REQUIRED_WORK_EVENT_FIELDS) == (
            "event_id", "run_id", "manifest_revision", "sequence", "node_id",
            "work_unit_id", "phase", "status", "completed", "total",
            "current_detail", "created_at", "idempotency_key",
        )
        assert set(WORK_EVENT_STATUSES) == {s.value for s in NodeStatus}

    def test_expected_progress_total_derived_from_manifest(self):
        contract = ConformanceContract.from_manifest(_manifest(nodes=3))
        assert contract.expected_progress(0) == {"completed": 0, "total": 3}
        assert contract.expected_progress(2) == {"completed": 2, "total": 3}
        assert contract.expected_progress(3) == {"completed": 3, "total": 3}

    def test_expected_progress_rejects_negative(self):
        contract = ConformanceContract.from_manifest(_manifest())
        with pytest.raises(ValueError):
            contract.expected_progress(-1)

    def test_derive_progress_counts_only_terminal(self):
        manifest = _manifest()
        statuses = {NODE_A: NodeStatus.PASSED.value, NODE_B: NodeStatus.RUNNING.value,
                    NODE_C: NodeStatus.PENDING.value}
        assert derive_progress(manifest, statuses) == {"completed": 1, "total": 3}
        statuses[NODE_B] = NodeStatus.PASSED.value
        assert derive_progress(manifest, statuses) == {"completed": 2, "total": 3}

    def test_is_completed_terminal_matches_domain(self):
        assert is_completed_terminal(NodeStatus.PASSED) is True
        assert is_completed_terminal("passed") is True
        assert is_completed_terminal("failed") is True
        assert is_completed_terminal("blocked") is True
        assert is_completed_terminal("running") is False
        assert is_completed_terminal("pending") is False

    def test_conformance_result_key_is_deterministic(self):
        manifest = _manifest()
        nodes = [NodeConformance(node_id=NODE_A, status="passed", reused=False,
                                 artifact_id=None, artifact_content_hash=None, message="")]
        proj = None
        r1 = ConformanceResult(run_id="r", manifest_revision=1, graph_id="g", status="complete",
                               nodes=nodes, progress={"completed": 3, "total": 3},
                               artifact_count=0, work_event_projection=proj, audit_ok=True)
        r2 = ConformanceResult(run_id="r", manifest_revision=1, graph_id="g", status="complete",
                               nodes=nodes, progress={"completed": 3, "total": 3},
                               artifact_count=0, work_event_projection=proj, audit_ok=True)
        assert r1.conformance_key() == r2.conformance_key()
        # a different progress shape changes the key
        r3 = ConformanceResult(run_id="r", manifest_revision=1, graph_id="g", status="complete",
                               nodes=nodes, progress={"completed": 2, "total": 3},
                               artifact_count=0, work_event_projection=proj, audit_ok=True)
        assert r1.conformance_key() != r3.conformance_key()


# ===========================================================================
# work-event store: fields, ordering, dedup, exact progress
# ===========================================================================

class TestWorkEventStore:
    def test_append_assigns_monotonic_sequence_and_is_append_only(self, work_events, tmp_path):
        contract = ConformanceContract.from_manifest(_manifest())
        e1 = work_events.append(
            _event(contract, NODE_A, "node_begin", NodeStatus.RUNNING.value, 0),
            contract,
        )
        e2 = work_events.append(
            _event(contract, NODE_A, "node_complete", NodeStatus.PASSED.value, 1),
            contract,
        )
        e3 = work_events.append(
            _event(contract, NODE_B, "node_complete", NodeStatus.PASSED.value, 2),
            contract,
        )
        assert [e1.sequence, e2.sequence, e3.sequence] == [1, 2, 3]
        listed = work_events.list_events(contract.run_id)
        assert [e.sequence for e in listed] == [1, 2, 3]
        assert [e.node_id for e in listed] == [NODE_A, NODE_A, NODE_B]

    def test_missing_required_field_rejected(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest())
        ev = _event(contract, NODE_A, "node_begin", NodeStatus.RUNNING.value, 0)
        del ev["created_at"]
        with pytest.raises(WorkEventError, match="missing required fields"):
            work_events.append(ev, contract)

    def test_invalid_status_rejected(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest())
        ev = _event(contract, NODE_A, "node_begin", "bogus", 0)
        with pytest.raises(WorkEventError, match="invalid work-event status"):
            work_events.append(ev, contract)

    def test_total_diverging_from_manifest_rejected(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest())  # total=3
        ev = _event(contract, NODE_A, "node_complete", NodeStatus.PASSED.value, 1)
        ev["total"] = 99  # diverges from manifest-derived total
        with pytest.raises(WorkEventError, match="diverges from manifest-derived"):
            work_events.append(ev, contract)

    def test_manifest_revision_diverging_rejected(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest(revision=1))
        ev = _event(contract, NODE_A, "node_complete", NodeStatus.PASSED.value, 1)
        ev["manifest_revision"] = 7
        with pytest.raises(WorkEventError, match="manifest_revision diverges"):
            work_events.append(ev, contract)

    def test_completed_out_of_range_rejected(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest())  # total=3
        ev = _event(contract, NODE_A, "node_complete", NodeStatus.PASSED.value, 4)
        with pytest.raises(WorkEventError, match="out of range"):
            work_events.append(ev, contract)

    def test_same_key_same_payload_dedup_no_duplicate(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest())
        ev = _event(contract, NODE_A, "node_complete", NodeStatus.PASSED.value, 1)
        first = work_events.append(ev, contract)
        second = work_events.append(ev, contract)
        assert first.idempotency_key == second.idempotency_key
        assert first.sequence == second.sequence  # same row reused
        assert work_events.count(contract.run_id) == 1
        assert work_events.distinct_idempotency_keys(contract.run_id) == 1

    def test_divergent_reuse_of_idempotency_key_rejected(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest())
        ev = _event(contract, NODE_A, "node_complete", NodeStatus.PASSED.value, 1)
        work_events.append(ev, contract)
        # same key, divergent status/progress -> rejected, never overwrite
        divergent = dict(ev)
        divergent["status"] = NodeStatus.FAILED.value
        divergent["completed"] = 0
        with pytest.raises(WorkEventConflictError, match="divergent"):
            work_events.append(divergent, contract)
        # original event untouched
        listed = work_events.list_events(contract.run_id)
        assert len(listed) == 1
        assert listed[0].status == NodeStatus.PASSED.value

    def test_physical_persistence_inspectable(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest())
        work_events.append(
            _event(contract, NODE_A, "node_complete", NodeStatus.PASSED.value, 1),
            contract,
        )
        # direct SQLite inspection of the operational file
        conn = sqlite3.connect(str(work_events.db_path))
        rows = conn.execute(
            "SELECT event_id, sequence, idempotency_key, payload_hash FROM work_events"
        ).fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0][1] == 1
        assert rows[0][2] == f"we:{contract.run_id}:synth_node_a:node_complete"


# ===========================================================================
# in-process restart/replay via the harness (no subprocess)
# ===========================================================================

class TestInProcessRestartReplay:
    def test_stop_after_node_a_then_resume_completes_without_duplicate_side_effects(
        self, r1_store, work_events, work_dir
    ):
        run_id = "run-inproc-restart"
        manifest = bootstrap_run(r1_store, run_id)
        contract = ConformanceContract.from_manifest(manifest)

        # process A: stop after node A
        first = run_nodes_up_to_boundary(
            r1_store, work_events, contract, work_dir, run_id,
            stop_after_node=NODE_A, rev=manifest.revision,
        )
        assert [r.node_id for r in first] == [NODE_A]
        assert first[0].reused is False
        assert r1_store.manifest_progress(run_id)["completed"] == 1

        # process B (same Store handle, simulating fresh open): resume + finish
        second = run_nodes_up_to_boundary(
            r1_store, work_events, contract, work_dir, run_id,
            stop_after_node=None, rev=manifest.revision,
        )
        # node A must be REUSED, B and C executed once each
        assert {r.node_id: r.reused for r in second} == {
            NODE_A: True, NODE_B: False, NODE_C: False,
        }
        assert r1_store.manifest_progress(run_id)["completed"] == 3

        # work events: node_begin/node_complete per node, deduped on idempotency key
        listed = work_events.list_events(run_id)
        # 2 events for A (begin+complete) + 2 for B + 2 for C = 6
        assert len(listed) == 6
        assert work_events.distinct_idempotency_keys(run_id) == 6
        # sequences strictly monotonic
        seqs = [e.sequence for e in listed]
        assert seqs == sorted(seqs) == list(range(1, 7))

    def test_operational_checkpoint_is_json_and_separate_from_domain(
        self, r1_store, work_events, work_dir
    ):
        run_id = "run-ckpt"
        manifest = bootstrap_run(r1_store, run_id)
        contract = ConformanceContract.from_manifest(manifest)
        run_nodes_up_to_boundary(
            r1_store, work_events, contract, work_dir, run_id,
            stop_after_node=NODE_B, rev=manifest.revision,
        )
        ckpt_path = checkpoint_path(work_dir)
        assert ckpt_path.exists()
        # JSON-only, no pickle/executable
        raw = ckpt_path.read_text(encoding="utf-8")
        assert raw.lstrip().startswith("{")
        data = json.loads(raw)
        assert data["run_id"] == run_id
        assert data["last_completed_node"] == NODE_B
        assert set(data["node_outputs"].keys()) == {NODE_A, NODE_B}
        # checkpoint table in authoritative store is separate from work events
        # and the checkpoint JSON file is NOT inside the artifact dir
        assert ckpt_path.parent == work_dir
        assert not str(ckpt_path).startswith(str(r1_store.artifact_dir))

    def test_work_events_never_become_domain_authority(self, r1_store, work_events, work_dir):
        """No work event creates a domain artifact, fact, or run-state transition."""
        run_id = "run-no-authority"
        manifest = bootstrap_run(r1_store, run_id)
        contract = ConformanceContract.from_manifest(manifest)
        run_nodes_up_to_boundary(
            r1_store, work_events, contract, work_dir, run_id,
            stop_after_node=None, rev=manifest.revision,
        )
        # synthetic nodes are artifact_required=False -> zero authoritative artifacts
        conn = sqlite3.connect(str(r1_store.db_path))
        artifact_count = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
        fact_count = conn.execute("SELECT COUNT(*) FROM canonical_facts").fetchone()[0]
        # analysis_state stays NOT_STARTED (nodes run directly, not via LocalGraphPort.run)
        analysis_state = conn.execute(
            "SELECT analysis_state FROM monitoring_runs WHERE run_id=?", (run_id,)
        ).fetchone()[0]
        conn.close()
        assert artifact_count == 0
        assert fact_count == 0
        assert analysis_state == "not_started"


# ===========================================================================
# REAL two-process subprocess boundary
# ===========================================================================

class TestSubprocessRestartBoundary:
    def test_two_fresh_processes_complete_run_with_distinct_pids(
        self, work_dir, src_paths
    ):
        run_id = "run-subprocess-boundary"
        py = sys.executable

        # Process A: bootstrap + stop after node A
        a = run_subprocess_worker(
            work_dir, run_id, stop_after_node=NODE_A, src_paths=src_paths,
            python_executable=py, invocation_marker="proc-A", bootstrap=True,
        )
        assert a.returncode == 0, f"proc A failed:\n{a.stderr}"
        a_result = _parse_worker_result(a.stdout)
        assert a_result["pid"] > 0
        assert a_result["progress"]["completed"] == 1
        assert a_result["progress"]["total"] == 3
        assert [n["node_id"] for n in a_result["nodes"]] == [NODE_A]
        assert a_result["nodes"][0]["reused"] is False
        assert a_result["work_event_count"] == 2

        # Process B: FRESH process, resume + finish (no --bootstrap)
        b = run_subprocess_worker(
            work_dir, run_id, stop_after_node=None, src_paths=src_paths,
            python_executable=py, invocation_marker="proc-B",
        )
        assert b.returncode == 0, f"proc B failed:\n{b.stderr}"
        b_result = _parse_worker_result(b.stdout)
        assert b_result["pid"] > 0
        # boundary observable: distinct OS process ids
        assert a_result["pid"] != b_result["pid"], "subprocess boundary not observed: same PID"
        # node A reused in process B; B and C executed
        reused_map = {n["node_id"]: n["reused"] for n in b_result["nodes"]}
        assert reused_map == {NODE_A: True, NODE_B: False, NODE_C: False}
        assert b_result["progress"]["completed"] == 3
        assert b_result["progress"]["total"] == 3

        # persisted Store: exactly one row per node, all passed, no duplicates
        store_db = work_dir / "authoritative.sqlite3"
        conn = sqlite3.connect(str(store_db))
        node_rows = conn.execute(
            "SELECT node_id, status, attempts FROM node_runs WHERE run_id=? ORDER BY node_id",
            (run_id,),
        ).fetchall()
        artifact_rows = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
        fact_rows = conn.execute("SELECT COUNT(*) FROM canonical_facts").fetchone()[0]
        conn.close()
        assert len(node_rows) == 3
        assert {r[0] for r in node_rows} == {NODE_A, NODE_B, NODE_C}
        assert all(r[1] == "passed" for r in node_rows)
        # node attempts: each node opened exactly once (A reused, not re-opened)
        assert [r[2] for r in node_rows] == [1, 1, 1]
        assert artifact_rows == 0  # synthetic nodes are artifact_required=False
        assert fact_rows == 0

    def test_subprocess_persistence_files_are_separate_operational(
        self, work_dir, src_paths
    ):
        run_id = "run-subproc-files"
        py = sys.executable
        run_subprocess_worker(
            work_dir, run_id, stop_after_node=NODE_A, src_paths=src_paths,
            python_executable=py, invocation_marker="proc-A2", bootstrap=True,
        )
        run_subprocess_worker(
            work_dir, run_id, stop_after_node=None, src_paths=src_paths,
            python_executable=py, invocation_marker="proc-B2",
        )
        # three separate physical persistence files
        assert (work_dir / "authoritative.sqlite3").exists()
        assert (work_dir / "work_events.sqlite3").exists()
        assert (work_dir / "operational_checkpoint.json").exists()
        # work-event store has all 6 events (2 per node), deduped
        conn = sqlite3.connect(str(work_dir / "work_events.sqlite3"))
        rows = conn.execute(
            "SELECT sequence, idempotency_key FROM work_events WHERE run_id=? ORDER BY sequence",
            (run_id,),
        ).fetchall()
        conn.close()
        assert len(rows) == 6
        keys = [r[1] for r in rows]
        assert len(set(keys)) == 6  # no duplicate idempotency keys
        # checkpoint JSON records all three node outputs after completion
        ckpt = load_operational_checkpoint(work_dir)
        assert set(ckpt["node_outputs"].keys()) == {NODE_A, NODE_B, NODE_C}

    def test_idempotent_replay_across_subprocess_no_duplicate_events(
        self, work_dir, src_paths
    ):
        """Re-running process B against an already-complete run replays the
        committed results and does NOT duplicate work events."""
        run_id = "run-subproc-replay"
        py = sys.executable
        run_subprocess_worker(
            work_dir, run_id, stop_after_node=NODE_A, src_paths=src_paths,
            python_executable=py, invocation_marker="p1", bootstrap=True,
        )
        run_subprocess_worker(
            work_dir, run_id, stop_after_node=None, src_paths=src_paths,
            python_executable=py, invocation_marker="p2",
        )
        # third invocation: everything reused
        p3 = run_subprocess_worker(
            work_dir, run_id, stop_after_node=None, src_paths=src_paths,
            python_executable=py, invocation_marker="p3",
        )
        assert p3.returncode == 0, p3.stderr
        p3_result = _parse_worker_result(p3.stdout)
        assert all(n["reused"] for n in p3_result["nodes"])
        # work-event store still has exactly 6 rows (deduped)
        conn = sqlite3.connect(str(work_dir / "work_events.sqlite3"))
        replay_count = conn.execute(
            "SELECT COUNT(*) FROM work_events WHERE run_id=?", (run_id,)
        ).fetchone()[0]
        conn.close()
        assert replay_count == 6
# ===========================================================================
# contract identity binding (repair 1)
# ===========================================================================

class TestContractIdentityBinding:
    def test_contract_carries_graph_and_manifest_identity(self):
        manifest = _manifest()
        contract = ConformanceContract.from_manifest(manifest)
        assert contract.graph_id == SYNTH_GRAPH_ID
        assert contract.node_ids == (NODE_A, NODE_B, NODE_C)
        assert len(contract.manifest_fingerprint) == 64  # sha256 hex

    def test_different_run_same_revision_node_count_distinct_fingerprint(self):
        """Two manifests with same revision+node count but different run_id
        produce different contracts (different run_id AND fingerprint)."""
        c1 = ConformanceContract.from_manifest(_manifest(run_id="run-X"))
        c2 = ConformanceContract.from_manifest(_manifest(run_id="run-Y"))
        assert c1.run_id != c2.run_id
        assert c1.manifest_fingerprint != c2.manifest_fingerprint
        assert c1.node_ids == c2.node_ids  # same node set, different run

    def test_different_graph_same_node_count_distinct_fingerprint(self):
        """Same run_id, revision, node count but different graph_id -> different
        fingerprint (binds event/checkpoint to the exact frozen graph)."""
        m1 = _manifest(run_id="run-G")
        m2 = ExecutionManifest(
            run_id="run-G", revision=1, graph_id="different-graph-id",
            nodes=[ManifestNode(node_id=nid, node_type=NodeType.DETERMINISTIC_SERVICE)
                   for nid in [NODE_A, NODE_B, NODE_C]],
            identity_algorithm="synth-identity-v1",
            graph_version="synth-three-node-v1", schema_version="synth-schema-v1",
        )
        c1 = ConformanceContract.from_manifest(m1)
        c2 = ConformanceContract.from_manifest(m2)
        assert c1.graph_id != c2.graph_id
        assert c1.manifest_fingerprint != c2.manifest_fingerprint

    def test_append_rejects_wrong_run_id(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest(run_id="correct-run"))
        ev = _event(contract, NODE_A, "node_begin", NodeStatus.RUNNING.value, 0,
                    run_id="wrong-run")
        with pytest.raises(WorkEventError, match="run_id.*!= contract run_id"):
            work_events.append(ev, contract)

    def test_append_rejects_unknown_node_id(self, work_events):
        contract = ConformanceContract.from_manifest(_manifest())
        ev = _event(contract, "nonexistent_node", "node_begin",
                    NodeStatus.RUNNING.value, 0)
        with pytest.raises(WorkEventError, match="not in frozen node set"):
            work_events.append(ev, contract)

    def test_expected_progress_rejects_completed_above_total(self):
        contract = ConformanceContract.from_manifest(_manifest(nodes=3))
        with pytest.raises(ValueError, match="exceeds manifest total"):
            contract.expected_progress(4)

    def test_wrong_run_manifest_same_revision_rejected_at_append(self, work_events):
        """A different manifest with the same revision and node count must NOT
        be accepted: the contract binds to the exact frozen graph, so an event
        from a different run is rejected before any DB write."""
        c1 = ConformanceContract.from_manifest(_manifest(run_id="run-A"))
        c2 = ConformanceContract.from_manifest(_manifest(run_id="run-B"))
        assert c1.manifest_revision == c2.manifest_revision
        assert c1.total_units == c2.total_units
        # event built for run-A cannot append against run-B's contract
        ev = _event(c1, NODE_A, "node_complete", NodeStatus.PASSED.value, 1)
        with pytest.raises(WorkEventError, match="run_id"):
            work_events.append(ev, c2)
        assert work_events.count() == 0  # no DB write occurred


# ===========================================================================
# checkpoint identity fail-closed (repair 2)
# ===========================================================================

class TestCheckpointIdentityFailClosed:
    def test_save_then_load_roundtrips_identity(self, work_dir):
        contract = ConformanceContract.from_manifest(_manifest(run_id="ck-rt"))
        save_operational_checkpoint(work_dir, contract, NODE_A,
                                    {NODE_A: {"v": 1}})
        data = load_operational_checkpoint(work_dir, contract)
        assert data["run_id"] == "ck-rt"
        assert data["graph_id"] == SYNTH_GRAPH_ID
        assert data["manifest_fingerprint"] == contract.manifest_fingerprint
        assert data["node_outputs"] == {NODE_A: {"v": 1}}

    def test_wrong_run_checkpoint_rejected(self, work_dir):
        c1 = ConformanceContract.from_manifest(_manifest(run_id="run-1"))
        c2 = ConformanceContract.from_manifest(_manifest(run_id="run-2"))
        save_operational_checkpoint(work_dir, c1, NODE_A, {NODE_A: {"v": 1}})
        with pytest.raises(CheckpointIdentityError, match="run_id mismatch"):
            load_operational_checkpoint(work_dir, c2)

    def test_wrong_revision_checkpoint_rejected(self, work_dir):
        manifest_r1 = ExecutionManifest(
            run_id="run-rev", revision=1, graph_id=SYNTH_GRAPH_ID,
            nodes=[ManifestNode(node_id=nid, node_type=NodeType.DETERMINISTIC_SERVICE)
                   for nid in [NODE_A, NODE_B, NODE_C]],
            identity_algorithm="synth-identity-v1",
            graph_version="synth-three-node-v1", schema_version="synth-schema-v1",
        )
        manifest_r2 = ExecutionManifest(
            run_id="run-rev", revision=2, graph_id=SYNTH_GRAPH_ID,
            nodes=[ManifestNode(node_id=nid, node_type=NodeType.DETERMINISTIC_SERVICE)
                   for nid in [NODE_A, NODE_B, NODE_C]],
            identity_algorithm="synth-identity-v1",
            graph_version="synth-three-node-v1", schema_version="synth-schema-v1",
        )
        c1 = ConformanceContract.from_manifest(manifest_r1)
        c2 = ConformanceContract.from_manifest(manifest_r2)
        save_operational_checkpoint(work_dir, c1, NODE_A, {NODE_A: {"v": 1}})
        with pytest.raises(CheckpointIdentityError, match="manifest_revision mismatch"):
            load_operational_checkpoint(work_dir, c2)

    def test_wrong_graph_checkpoint_rejected(self, work_dir):
        m1 = _manifest(run_id="run-graph")
        m2 = ExecutionManifest(
            run_id="run-graph", revision=1, graph_id="different-graph",
            nodes=[ManifestNode(node_id=nid, node_type=NodeType.DETERMINISTIC_SERVICE)
                   for nid in [NODE_A, NODE_B, NODE_C]],
            identity_algorithm="synth-identity-v1",
            graph_version="synth-three-node-v1", schema_version="synth-schema-v1",
        )
        c1 = ConformanceContract.from_manifest(m1)
        c2 = ConformanceContract.from_manifest(m2)
        save_operational_checkpoint(work_dir, c1, NODE_A, {NODE_A: {"v": 1}})
        with pytest.raises(CheckpointIdentityError, match="graph_id mismatch"):
            load_operational_checkpoint(work_dir, c2)

    def test_malformed_json_checkpoint_rejected(self, work_dir):
        contract = ConformanceContract.from_manifest(_manifest(run_id="run-mal"))
        checkpoint_path(work_dir).write_text("{not valid json", encoding="utf-8")
        with pytest.raises(CheckpointIdentityError, match="malformed checkpoint JSON"):
            load_operational_checkpoint(work_dir, contract)

    def test_checkpoint_missing_identity_fields_rejected(self, work_dir):
        contract = ConformanceContract.from_manifest(_manifest(run_id="run-miss"))
        # old-format checkpoint without identity fields
        checkpoint_path(work_dir).write_text(
            json.dumps({"last_completed_node": NODE_A, "node_outputs": {}}),
            encoding="utf-8",
        )
        with pytest.raises(CheckpointIdentityError, match="missing identity fields"):
            load_operational_checkpoint(work_dir, contract)

    def test_wrong_run_checkpoint_does_not_mutate_store_or_events(
        self, r1_store, work_events, work_dir
    ):
        """A wrong-run checkpoint must fail closed BEFORE the runner uses its
        outputs, leaving the authoritative Store and work-event DB untouched."""
        run_id = "run-real"
        manifest = bootstrap_run(r1_store, run_id)
        contract = ConformanceContract.from_manifest(manifest)
        # write a checkpoint for a DIFFERENT run/graph
        other = ConformanceContract.from_manifest(_manifest(run_id="run-other"))
        save_operational_checkpoint(work_dir, other, NODE_A, {NODE_A: {"poison": True}})
        # resuming the real run must fail closed on the wrong checkpoint
        with pytest.raises(CheckpointIdentityError):
            run_nodes_up_to_boundary(
                r1_store, work_events, contract, work_dir, run_id,
                stop_after_node=None, rev=manifest.revision,
            )
        # no node was executed, no work event written
        assert r1_store.manifest_progress(run_id)["completed"] == 0
        assert work_events.count(run_id) == 0

    def test_checkpoint_with_unknown_node_output_rejected(
        self, r1_store, work_events, work_dir
    ):
        run_id = "run-unknown-node"
        manifest = bootstrap_run(r1_store, run_id)
        contract = ConformanceContract.from_manifest(manifest)
        # checkpoint with an unknown node id in outputs
        checkpoint_path(work_dir).write_text(json.dumps({
            "run_id": run_id,
            "manifest_revision": contract.manifest_revision,
            "graph_id": contract.graph_id,
            "node_ids": list(contract.node_ids),
            "manifest_fingerprint": contract.manifest_fingerprint,
            "last_completed_node": NODE_A,
            "node_outputs": {"BOGUS_NODE": {"v": 1}},
        }), encoding="utf-8")
        with pytest.raises(CheckpointIdentityError, match="unknown node outputs"):
            run_nodes_up_to_boundary(
                r1_store, work_events, contract, work_dir, run_id,
                stop_after_node=None, rev=manifest.revision,
            )
        assert r1_store.manifest_progress(run_id)["completed"] == 0
        assert work_events.count(run_id) == 0


# ===========================================================================
# concurrent append safety (repair 3)
# ===========================================================================

class TestConcurrentAppendSafety:
    def test_concurrent_same_key_dedups_no_duplicate(self, tmp_path):
        """Two connections appending the SAME idempotency key + payload
        concurrently: exactly one row survives, no duplicate sequence."""
        from concurrent.futures import ThreadPoolExecutor

        contract = ConformanceContract.from_manifest(_manifest(run_id="run-conc"))
        db = tmp_path / "conc_events.sqlite3"
        barrier = {"n": 0}
        lock = __import__("threading").Lock()

        def _append_one():
            store = WorkEventStore(db)
            try:
                ev = _event(contract, NODE_A, "node_complete",
                            NodeStatus.PASSED.value, 1)
                return store.append(ev, contract)
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_append_one) for _ in range(2)]
            results = [f.result() for f in futures]

        # both calls returned a WorkEvent with the same sequence (deduped)
        assert all(r.sequence == results[0].sequence for r in results)
        # exactly one physical row
        check = WorkEventStore(db)
        assert check.count("run-conc") == 1
        assert check.distinct_idempotency_keys("run-conc") == 1
        check.close()

    def test_concurrent_distinct_keys_distinct_sequences(self, tmp_path):
        """Two connections appending DIFFERENT idempotency keys concurrently:
        both succeed with distinct sequences (1 and 2), no collision."""
        from concurrent.futures import ThreadPoolExecutor

        contract = ConformanceContract.from_manifest(_manifest(run_id="run-conc2"))
        db = tmp_path / "conc_events2.sqlite3"

        def _append(key_suffix, node_id):
            store = WorkEventStore(db)
            try:
                ev = _event(contract, node_id, "node_complete",
                            NodeStatus.PASSED.value, 1,
                            idempotency_key=f"we:run-conc2:{node_id}:{key_suffix}")
                return store.append(ev, contract)
            finally:
                store.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            fa = pool.submit(_append, "a", NODE_A)
            fb = pool.submit(_append, "b", NODE_B)
            ra, rb = fa.result(), fb.result()

        seqs = sorted([ra.sequence, rb.sequence])
        assert seqs == [1, 2]  # distinct sequences, no collision
        check = WorkEventStore(db)
        assert check.count("run-conc2") == 2
        check.close()

    def test_event_id_unique_collision_rejected(self, tmp_path):
        """Two events with the same event_id but different keys: the second is
        rejected (event_id is identity-safe unique)."""
        from mm_r1.domain import new_id

        contract = ConformanceContract.from_manifest(_manifest(run_id="run-eid"))
        store = WorkEventStore(tmp_path / "eid_events.sqlite3")
        shared_eid = new_id("we_")
        ev1 = _event(contract, NODE_A, "node_complete", NodeStatus.PASSED.value, 1,
                     idempotency_key="key-1")
        ev1["event_id"] = shared_eid
        store.append(ev1, contract)
        ev2 = _event(contract, NODE_B, "node_complete", NodeStatus.PASSED.value, 2,
                     idempotency_key="key-2")
        ev2["event_id"] = shared_eid  # same event_id, different key
        with pytest.raises(WorkEventConflictError, match="event_id.*already exists"):
            store.append(ev2, contract)
        # only the first event persisted
        assert store.count("run-eid") == 1
        store.close()


class TestExactGraphIRComparator:
    """Shared assert_exact_graph_ir covers ordered nodes + edges (manager repair)."""

    def test_exact_match_passes(self):
        from mm_r1_spike.contract import assert_exact_graph_ir
        from mm_r1_spike.restart_harness import synthetic_three_node_graph
        g = synthetic_three_node_graph()
        assert_exact_graph_ir(g, synthetic_three_node_graph())

    def test_altered_edges_rejected(self):
        from mm_r1.graph import Graph, GraphEdge, GraphNode
        from mm_r1_spike.contract import GraphIRMismatchError, assert_exact_graph_ir
        from mm_r1_spike.restart_harness import NODE_A, NODE_B, NODE_C, synthetic_three_node_graph
        expected = synthetic_three_node_graph()
        nodes = {
            nid: GraphNode(
                node_id=n.node_id, node_type=n.node_type, handler=n.handler,
                description=n.description, mandatory=n.mandatory,
                max_attempts=n.max_attempts, artifact_required=n.artifact_required,
            )
            for nid, n in expected.nodes.items()
        }
        altered = Graph(
            graph_id=expected.graph_id,
            nodes=nodes,
            edges=[GraphEdge(src=NODE_B, dst=NODE_A), GraphEdge(src=NODE_A, dst=NODE_C)],
        )
        with pytest.raises(GraphIRMismatchError, match="edges mismatch"):
            assert_exact_graph_ir(altered, expected)

    def test_node_field_mismatch_rejected(self):
        from mm_r1.graph import Graph, GraphNode
        from mm_r1_spike.contract import GraphIRMismatchError, assert_exact_graph_ir
        from mm_r1_spike.restart_harness import synthetic_three_node_graph
        expected = synthetic_three_node_graph()
        nodes = dict(expected.nodes)
        n0 = list(nodes.values())[0]
        nodes[n0.node_id] = GraphNode(
            node_id=n0.node_id, node_type=n0.node_type, handler="DIFFERENT",
            description=n0.description, mandatory=n0.mandatory,
            max_attempts=n0.max_attempts, artifact_required=n0.artifact_required,
        )
        altered = Graph(graph_id=expected.graph_id, nodes=nodes, edges=list(expected.edges))
        with pytest.raises(GraphIRMismatchError, match="handler"):
            assert_exact_graph_ir(altered, expected)


def _parse_worker_result(stdout: str) -> dict:
    for line in stdout.splitlines():
        if line.startswith("RESTART_WORKER_RESULT="):
            return json.loads(line[len("RESTART_WORKER_RESULT="):])
    raise AssertionError(f"no RESTART_WORKER_RESULT in stdout:\n{stdout}")
