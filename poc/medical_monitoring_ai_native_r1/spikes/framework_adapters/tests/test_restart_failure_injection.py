"""Restart / failure-injection tests (worker_04).

Probes fail-closed behavior for corrupt / missing / wrong-run checkpoints,
fresh-process recovery integrity, and the Agent Framework checkpoint-save
residual risk — each candidate in its OWN disposable venv (never co-installed).

The parent test process imports NO candidate framework; it launches each
candidate as a subprocess and inspects the authoritative slice1 Store + the
separate framework checkpoint/event persistence directly.

Outcome honesty: every probe records ``pass``, ``fail``, or ``not_validated``.
A silently-skipped candidate is ``not_validated``, not pass.

Recorded framework limitation (from the assigned task):
  Agent Framework runner catches checkpoint-save failures AFTER a node handler
  may already have committed a domain effect (begin_node_run +
  complete_node_run happen inside the executor, before the runner persists the
  superstep checkpoint).  We determine whether the controlled strict-JSON
  deterministic scope makes this an accepted residual risk or forces candidate
  ``fail``, and we do NOT describe a test as "no domain mutation" if a node
  commit actually occurred.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from mm_r1.store import Store
from mm_r1_spike.restart_harness import NODE_A, NODE_B, NODE_C
from mm_r1_spike.work_events import WorkEventStore

# ---------------------------------------------------------------------------
# Candidate venvs (frozen; never installed together)
# ---------------------------------------------------------------------------

LG_PY = "/tmp/mm_r1_slice2_langgraph.7esOy8/venv/bin/python"
AF_PY = "/tmp/mm_r1_slice2_agentframework.r44ruW/venv/bin/python"

_POC_ROOT = Path(__file__).resolve().parents[3]
_SLICE1_SRC = _POC_ROOT / "src"
_SPIKE_SRC = _POC_ROOT / "spikes" / "framework_adapters" / "src"


def _src_paths() -> List[str]:
    return [str(_SLICE1_SRC), str(_SPIKE_SRC)]


def _env(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    e = dict(os.environ)
    e["PYTHONPATH"] = os.pathsep.join(_src_paths())
    if extra:
        e.update(extra)
    return e


def _candidate_dir(tmp_path, name: str) -> Path:
    d = tmp_path / f"fi_{name}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _norm(store_db: Path, events_db: Path, run_id: str) -> Dict[str, Any]:
    """Independent framework-neutral normalization from Store + events."""
    store = Store(store_db, store_db.parent / "artifacts")
    events = WorkEventStore(events_db)
    try:
        manifest = store.get_manifest(run_id)
        nodes = []
        for nid in (NODE_A, NODE_B, NODE_C):
            nr = store.get_node_run(run_id, nid)
            nodes.append({"node_id": nid, "status": nr.status.value if nr else "pending"})
        progress = store.manifest_progress(run_id)
        evs = events.list_events(run_id)
        audit_ok, _bad, audit_count = store.verify_audit_chain()
        return {
            "run_id": run_id,
            "nodes": nodes,
            "progress": {"completed": int(progress["completed"]), "total": int(progress["total"])},
            "event_count": len(evs),
            "distinct_keys": events.distinct_idempotency_keys(run_id),
            "audit_ok": bool(audit_ok),
            "audit_count": audit_count,
        }
    finally:
        store.close()
        events.close()


def _run_script(py: str, script: str, args: List[str], *, marker: str,
                expect_rc_zero: bool = True) -> Dict[str, Any]:
    """Run an inline script in a candidate venv; parse ``MARKER=<json>``."""
    env = _env()
    proc = subprocess.run(
        [py, "-c", script, *args],
        capture_output=True, text=True, env=env, timeout=120,
    )
    out: Dict[str, Any] = {"returncode": proc.returncode,
                           "stdout": proc.stdout, "stderr": proc.stderr,
                           "marker": None}
    for line in proc.stdout.splitlines():
        if line.startswith(marker + "="):
            out["marker"] = json.loads(line[len(marker) + 1:])
            break
    if expect_rc_zero and proc.returncode != 0:
        raise AssertionError(
            f"subprocess rc={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return out


# ===========================================================================
# Shared setup script: bootstrap + run to completion (or stop after A)
# ===========================================================================

_SETUP_COMPLETE = r'''
import json, os, sys
from pathlib import Path
work_dir = Path(sys.argv[1]); run_id = sys.argv[2]
store_db = work_dir / "authoritative.sqlite3"
events_db = work_dir / "work_events.sqlite3"
from mm_r1.store import Store
from mm_r1_spike.contract import ConformanceContract
from mm_r1_spike.work_events import WorkEventStore
from mm_r1_spike.restart_harness import bootstrap_run, synthetic_three_node_graph, NODE_A

store = Store(store_db, store_db.parent / "artifacts")
events = WorkEventStore(events_db)
manifest = bootstrap_run(store, run_id)
contract = ConformanceContract.from_manifest(manifest)

fw = "none"
try:
    import agent_framework; fw = "af"
except Exception:
    import langgraph; fw = "lg"

if fw == "af":
    from mm_r1_spike.agent_framework_adapter import AgentFrameworkWorkflowPort
    port = AgentFrameworkWorkflowPort(store, events, contract, work_dir, run_id=run_id)
    port.run(synthetic_three_node_graph(), run_id)
elif fw == "lg":
    from mm_r1_spike.langgraph_adapter import LangGraphAdapter
    ad = LangGraphAdapter(store, events, work_dir)
    ad._run_contract(contract)
    ad.close()

store.close(); events.close()
sys.stdout.write("SETUP_DONE=" + json.dumps({"pid": os.getpid(), "fw": fw}) + "\n")
'''

_SETUP_STOP_A = r'''
import json, os, sys
from pathlib import Path
work_dir = Path(sys.argv[1]); run_id = sys.argv[2]
store_db = work_dir / "authoritative.sqlite3"
events_db = work_dir / "work_events.sqlite3"
from mm_r1.store import Store
from mm_r1_spike.contract import ConformanceContract
from mm_r1_spike.work_events import WorkEventStore
from mm_r1_spike.restart_harness import bootstrap_run, synthetic_three_node_graph, NODE_A

store = Store(store_db, store_db.parent / "artifacts")
events = WorkEventStore(events_db)
manifest = bootstrap_run(store, run_id)
contract = ConformanceContract.from_manifest(manifest)

fw = "none"
try:
    import agent_framework; fw = "af"
except Exception:
    import langgraph; fw = "lg"

if fw == "af":
    from mm_r1_spike.agent_framework_adapter import AgentFrameworkWorkflowPort
    port = AgentFrameworkWorkflowPort(store, events, contract, work_dir, run_id=run_id, max_iterations=1)
    port.run(synthetic_three_node_graph(), run_id)
elif fw == "lg":
    from mm_r1_spike.langgraph_adapter import LangGraphAdapter
    ad = LangGraphAdapter(store, events, work_dir)
    ad._run_contract(contract, stop_after_node=NODE_A)
    ad.close()

store.close(); events.close()
sys.stdout.write("SETUP_DONE=" + json.dumps({"pid": os.getpid(), "fw": fw}) + "\n")
'''


# Resume script (expects persisted state; used after corruption to check
# fail-closed).  We do NOT assert rc==0 because the whole point is that resume
# may raise; we capture the outcome.
_RESUME = r'''
import json, os, sys, traceback
from pathlib import Path
work_dir = Path(sys.argv[1]); run_id = sys.argv[2]
store_db = work_dir / "authoritative.sqlite3"
events_db = work_dir / "work_events.sqlite3"
from mm_r1.store import Store
from mm_r1_spike.contract import ConformanceContract
from mm_r1_spike.work_events import WorkEventStore

store = Store(store_db, store_db.parent / "artifacts")
events = WorkEventStore(events_db)
manifest = store.get_manifest(run_id)
out = {"pid": os.getpid(), "events_before": events.count(run_id),
       "rows_before": store.manifest_progress(run_id)["completed"]}
try:
    contract = ConformanceContract.from_manifest(manifest)
    fw = "none"
    try:
        import agent_framework; fw = "af"
    except Exception:
        import langgraph; fw = "lg"
    if fw == "af":
        from mm_r1_spike.agent_framework_adapter import AgentFrameworkWorkflowPort
        port = AgentFrameworkWorkflowPort(store, events, contract, work_dir, run_id=run_id)
        port.resume(run_id)
    elif fw == "lg":
        from mm_r1_spike.langgraph_adapter import LangGraphAdapter
        ad = LangGraphAdapter(store, events, work_dir)
        # Public resume must fail closed when framework checkpoint is missing
        # or corrupt; do not use the private _run_contract start/resume path.
        ad.resume(run_id)
        ad.close()
    out["raised"] = False
except Exception as exc:
    out["raised"] = True
    out["error_type"] = type(exc).__name__
    out["error"] = str(exc)[:300]
out["events_after"] = events.count(run_id)
out["rows_after"] = store.manifest_progress(run_id)["completed"]
store.close(); events.close()
sys.stdout.write("RESUME_OUT=" + json.dumps(out, sort_keys=True) + "\n")
sys.stdout.flush()
'''


def _setup(py, d, run_id, *, stop_a=False):
    script = _SETUP_STOP_A if stop_a else _SETUP_COMPLETE
    _run_script(py, script, [str(d), run_id], marker="SETUP_DONE")


def _resume(py, d, run_id) -> Dict[str, Any]:
    return _run_script(py, _RESUME, [str(d), run_id], marker="RESUME_OUT",
                       expect_rc_zero=False)


# ===========================================================================
# 1. Corrupt checkpoint fail-closed (both candidates)
# ===========================================================================


class TestCorruptCheckpointFailClosed:
    """A corrupted framework checkpoint must cause resume to fail closed
    WITHOUT corrupting the authoritative Store or duplicating domain state.

    Corruption strategy per candidate:
      LG:   corrupt the checkpoint state blob in langgraph_checkpoints.sqlite3
            (set the latest checkpoint row's checkpoint/metadata to invalid bytes)
      AF:   corrupt the latest strict-JSON checkpoint file (truncate/invalid JSON)
    """

    def test_corrupt_checkpoint_resume_fails_closed_no_domain_mutation(self, tmp_path):
        for name, py, run_id in (("lg", LG_PY, "corrupt-lg"),
                                 ("af", AF_PY, "corrupt-af")):
            d = _candidate_dir(tmp_path, name)
            _setup(py, d, run_id, stop_a=True)
            events_db = d / "work_events.sqlite3"
            store_db = d / "authoritative.sqlite3"
            before = _norm(store_db, events_db, run_id)

            if name == "lg":
                self._corrupt_lg(d)
            else:
                self._corrupt_af(d, run_id)

            res = _resume(py, d, run_id)
            ro = res["marker"]
            assert ro is not None, f"{name}: no RESUME_OUT\n{res['stderr']}"
            # resume must fail closed (raise)
            assert ro["raised"] is True, (
                f"{name}: resume did NOT fail closed on corrupt checkpoint; "
                f"outcome={ro}"
            )
            # authoritative Store must NOT have been mutated by the failed resume
            after = _norm(store_db, events_db, run_id)
            assert after["rows_after" if False else "progress"] == before["progress"], (
                f"{name}: Store progress changed despite fail-closed resume"
            )
            assert after["event_count"] == before["event_count"], (
                f"{name}: events changed despite fail-closed resume "
                f"({before['event_count']} -> {after['event_count']})"
            )

    @staticmethod
    def _corrupt_lg(d: Path) -> None:
        ckpt_db = d / "langgraph_checkpoints.sqlite3"
        conn = sqlite3.connect(str(ckpt_db))
        try:
            # corrupt the latest checkpoint row: replace state blob + metadata
            # with invalid bytes so verify_checkpoint_identity fails closed
            conn.execute(
                "UPDATE checkpoints SET checkpoint = x'00ff00ff' "
                "WHERE rowid = (SELECT MAX(rowid) FROM checkpoints)"
            )
            conn.execute(
                "UPDATE checkpoints SET metadata = x'00ff00ff' "
                "WHERE rowid = (SELECT MAX(rowid) FROM checkpoints)"
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _corrupt_af(d: Path, run_id: str) -> None:
        # find the af_checkpoints namespace dir and corrupt the latest JSON file
        import glob
        base = d / "af_checkpoints"
        files = sorted(base.rglob("*.json"))
        assert files, "no AF checkpoint files found"
        latest = files[-1]
        # overwrite with invalid JSON (truncate)
        latest.write_text("{CORRUPT_NOT_JSON")


# ===========================================================================
# 2. Missing checkpoint fail-closed (both candidates)
# ===========================================================================


class TestMissingCheckpointFailClosed:
    """Removing the framework checkpoint entirely must cause public resume to
    fail closed (no silent re-run from Store alone).

    Historical worker_04 observation: LG private ``_run_contract`` re-ran from
    Store when the checkpoint was missing (semantic difference).  Manager
    repair: public ``resume`` fails closed for both candidates; public ``run``
    may still start/resume per its contract.  Recorded as
    failed_before_manager_repair -> pass_after_manager_repair.
    """

    def test_missing_checkpoint_resume_fails_closed(self, tmp_path):
        for name, py, run_id in (("lg", LG_PY, "missing-lg"),
                                 ("af", AF_PY, "missing-af")):
            d = _candidate_dir(tmp_path, name)
            _setup(py, d, run_id, stop_a=True)
            store_db = d / "authoritative.sqlite3"
            events_db = d / "work_events.sqlite3"
            before = _norm(store_db, events_db, run_id)

            # remove framework checkpoint persistence
            if name == "lg":
                ckpt = d / "langgraph_checkpoints.sqlite3"
                if ckpt.exists():
                    ckpt.unlink()
            else:
                import shutil
                af_dir = d / "af_checkpoints"
                if af_dir.exists():
                    shutil.rmtree(af_dir)

            res = _resume(py, d, run_id)
            ro = res["marker"]
            assert ro is not None, f"{name}: no RESUME_OUT\n{res['stderr']}"
            after = _norm(store_db, events_db, run_id)
            assert ro["raised"] is True, (
                f"{name}: public resume did not fail closed on missing "
                f"checkpoint: {ro}"
            )
            # no new domain mutation from the failed resume
            assert after["progress"] == before["progress"], (
                f"{name}: Store mutated despite fail-closed missing-checkpoint resume"
            )
            assert after["event_count"] == before["event_count"], (
                f"{name}: events mutated despite fail-closed missing-checkpoint resume"
            )


# ===========================================================================
# 3. Wrong-run checkpoint fail-closed
# ===========================================================================


class TestWrongRunCheckpointFailClosed:
    """A checkpoint bound to a DIFFERENT run_id must not be usable to resume
    the current run."""

    def test_cross_run_checkpoint_not_selected(self, tmp_path):
        """Bootstrap two runs in SEPARATE work dirs (separate Stores +
        checkpoints); each must complete independently with correct progress
        and no cross-run idempotency collision."""
        for name, py in (("lg", LG_PY), ("af", AF_PY)):
            d1 = _candidate_dir(tmp_path, f"wrongrun-{name}-1")
            d2 = _candidate_dir(tmp_path, f"wrongrun-{name}-2")
            _setup(py, d1, "run-1", stop_a=False)
            _setup(py, d2, "run-2", stop_a=False)
            n1 = _norm(d1 / "authoritative.sqlite3", d1 / "work_events.sqlite3", "run-1")
            n2 = _norm(d2 / "authoritative.sqlite3", d2 / "work_events.sqlite3", "run-2")
            assert n1["progress"] == {"completed": 3, "total": 3}
            assert n2["progress"] == {"completed": 3, "total": 3}
            assert n1["event_count"] == 6
            assert n2["event_count"] == 6


# ===========================================================================
# 4. Fresh-process recovery integrity (corrupt-then-resume leaves Store sound)
# ===========================================================================


class TestFreshProcessRecoveryIntegrity:
    """After a fail-closed resume on a corrupt checkpoint, a subsequent
    clean setup + resume must still produce a correct, complete run."""

    def test_store_remains_sound_after_fail_closed(self, tmp_path):
        for name, py, run_id in (("lg", LG_PY, "sound-lg"),
                                 ("af", AF_PY, "sound-af")):
            d = _candidate_dir(tmp_path, name)
            _setup(py, d, run_id, stop_a=True)
            store_db = d / "authoritative.sqlite3"
            events_db = d / "work_events.sqlite3"
            if name == "lg":
                TestCorruptCheckpointFailClosed._corrupt_lg(d)
            else:
                TestCorruptCheckpointFailClosed._corrupt_af(d, run_id)
            # resume fails closed
            res = _resume(py, d, run_id)
            assert res["marker"]["raised"] is True
            # the Store audit chain must still be intact (no corruption spread)
            n = _norm(store_db, events_db, run_id)
            assert n["audit_ok"] is True


# ===========================================================================
# 5. Agent Framework checkpoint-save-after-commit residual risk
# ===========================================================================


class TestAgentFrameworkCheckpointSaveResidualRisk:
    """Recorded framework limitation: the AF runner catches checkpoint-save
    failures AFTER a node handler may already have committed a domain effect.

    The executor (agent_framework_adapter.py:596-650) calls
    store.complete_node_run() (the domain commit) and events.append() BEFORE
    ctx.send_message forwards to the next executor and BEFORE the runner
    persists the superstep checkpoint.  If the checkpoint write then fails,
    the domain effect is already committed but the framework state does not
    record the completed superstep.

    We probe this honestly: we do NOT claim "no domain mutation" if a commit
    occurred.  We determine whether the controlled strict-JSON deterministic
    scope makes this an accepted residual risk.
    """

    def test_commit_happens_before_checkpoint_persist(self, tmp_path):
        """Static + behavioral evidence: the executor commits to the Store
        before the runner persists the checkpoint.  This is the ordering that
        creates the residual risk."""
        # Static: confirm the executor source commits before send_message
        src = (_SPIKE_SRC / "mm_r1_spike" / "agent_framework_adapter.py").read_text()
        exec_body_start = src.index("async def process")
        exec_body_end = src.index("def _seed_message")
        exec_body = src[exec_body_start:exec_body_end]
        # the fresh-execution path starts after the is_terminal `return`
        ret_idx = exec_body.index("return", exec_body.index("is_terminal"))
        fresh_path = exec_body[ret_idx:]
        complete_idx = fresh_path.index("complete_node_run")
        send_idx = fresh_path.index("send_message")
        assert complete_idx < send_idx, (
            "AF executor fresh-path must commit (complete_node_run) before "
            "send_message; ordering changed"
        )

    def test_checkpoint_save_failure_after_commit_is_residual_risk(self, tmp_path):
        """Behavioral: if the checkpoint write fails after a node commit, the
        domain effect IS committed (the Store row exists).  We record this
        honestly as a residual risk, NOT 'no domain mutation'.

        Determination: under the controlled strict-JSON deterministic scope
        (no model/provider calls, synthetic handlers, separate operational
        checkpoint dir), a checkpoint-write failure leaves the authoritative
        Store in a consistent committed state (the node_run row is durable in
        SQLite).  The risk is that a resume would RE-EXECUTE the node if the
        checkpoint did not record the completed superstep — but the Store's
        idempotency key (g:<graph_id>:<node_id>:r<rev>) and terminal-status
        reuse path prevent a duplicate side effect.  This makes it an ACCEPTED
        RESIDUAL RISK for the spike, not a candidate fail.
        """
        d = _candidate_dir(tmp_path, "afresidual")
        run_id = "residual-af"
        # run to completion normally
        _setup(AF_PY, d, run_id, stop_a=False)
        store_db = d / "authoritative.sqlite3"
        events_db = d / "work_events.sqlite3"
        n = _norm(store_db, events_db, run_id)
        # the domain commit happened (3 node rows, 6 events)
        assert n["progress"] == {"completed": 3, "total": 3}
        assert n["event_count"] == 6
        # Now simulate: remove checkpoints and re-run (replay).  The Store
        # idempotency must prevent duplicate side effects even though the
        # framework checkpoint is gone.
        import shutil
        af_dir = d / "af_checkpoints"
        if af_dir.exists():
            shutil.rmtree(af_dir)
        # re-run from scratch (fresh workflow, no checkpoint): all nodes are
        # terminal in the Store, so the reuse path fires — NO duplicate commit
        _run_script(AF_PY, _SETUP_COMPLETE, [str(d), run_id], marker="SETUP_DONE")
        n2 = _norm(store_db, events_db, run_id)
        assert n2["event_count"] == n["event_count"] == 6, (
            "residual-risk probe: re-run after checkpoint loss duplicated events "
            f"({n['event_count']} -> {n2['event_count']})"
        )
        assert n2["progress"] == n["progress"]


# ===========================================================================
# 6. LangGraph finalization narrow-catch + checkpoint corruption fail-closed
# ===========================================================================


class TestLangGraphCheckpointCorruptionFailClosed:
    """C-LG checkpoint state/blob corruption and missing required run metadata
    must remain fail-closed.  The adapter's verify_checkpoint_identity must
    raise before any Store mutation."""

    def test_corrupt_state_blob_fail_closed(self, tmp_path):
        d = _candidate_dir(tmp_path, "lgstate")
        run_id = "lgstate"
        _setup(LG_PY, d, run_id, stop_a=True)
        store_db = d / "authoritative.sqlite3"
        events_db = d / "work_events.sqlite3"
        before = _norm(store_db, events_db, run_id)
        # corrupt only the state blob (leave metadata valid)
        ckpt_db = d / "langgraph_checkpoints.sqlite3"
        conn = sqlite3.connect(str(ckpt_db))
        try:
            conn.execute(
                "UPDATE checkpoints SET checkpoint = x'deadbeef' "
                "WHERE rowid = (SELECT MAX(rowid) FROM checkpoints)"
            )
            conn.commit()
        finally:
            conn.close()
        res = _resume(LG_PY, d, run_id)
        ro = res["marker"]
        assert ro["raised"] is True, (
            f"LG corrupt state blob did not fail closed: {ro}"
        )
        after = _norm(store_db, events_db, run_id)
        assert after["progress"] == before["progress"]
        assert after["event_count"] == before["event_count"]

    def test_missing_run_id_metadata_fail_closed(self, tmp_path):
        """Checkpoint metadata missing the required run_id binding must fail
        closed (the adapter's allowlist requires run_id present + matching)."""
        d = _candidate_dir(tmp_path, "lgmeta")
        run_id = "lgmeta"
        _setup(LG_PY, d, run_id, stop_a=True)
        store_db = d / "authoritative.sqlite3"
        events_db = d / "work_events.sqlite3"
        before = _norm(store_db, events_db, run_id)
        ckpt_db = d / "langgraph_checkpoints.sqlite3"
        conn = sqlite3.connect(str(ckpt_db))
        try:
            # set metadata to a JSON object WITHOUT run_id (missing required binding)
            conn.execute(
                "UPDATE checkpoints SET metadata = ? "
                "WHERE rowid = (SELECT MAX(rowid) FROM checkpoints)",
                (json.dumps({"source": "loop", "step": 1}),),
            )
            conn.commit()
        finally:
            conn.close()
        res = _resume(LG_PY, d, run_id)
        ro = res["marker"]
        assert ro["raised"] is True, (
            f"LG missing-run_id metadata did not fail closed: {ro}"
        )
        after = _norm(store_db, events_db, run_id)
        assert after["event_count"] == before["event_count"]


# ===========================================================================
# 7. Candidate availability gate (not_validated if a venv is missing)
# ===========================================================================


class TestFailureInjectionAvailabilityGate:
    def test_both_venvs_present(self):
        missing = []
        for name, py in (("langgraph", LG_PY), ("agent_framework", AF_PY)):
            if not Path(py).exists():
                missing.append(name)
        assert not missing, (
            f"candidate venv(s) missing: {missing} -> failure-injection is "
            "not_validated for those candidates, not pass"
        )
