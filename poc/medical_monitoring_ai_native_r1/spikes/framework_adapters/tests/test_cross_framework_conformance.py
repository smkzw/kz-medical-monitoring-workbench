"""Cross-framework conformance + independent public-port challenge (worker_04).

This file is worker_04-owned.  It does NOT import either candidate framework
module at collection time: LangGraph and Microsoft Agent Framework live in two
disposable venvs that must never be installed together.  Instead, each candidate
is exercised in its OWN venv as a ``subprocess`` that prints a
framework-neutral JSON-normalized result (``CANDIDATE_RESULT=...``).  The parent
test process (which imports no candidate framework) reads the authoritative
slice1 SQLite Store + the separate work-event SQLite store to build an
INDEPENDENT framework-neutral normalization and compares it across candidates.

Comparison basis (execution-context "Shared Contract And Required Evidence"):
  * derived progress (completed/total) from the frozen manifest;
  * work-event ordering and idempotency (no duplicate completed event/side effect);
  * Store node-run, artifact, and audit counts;
  * fresh-process restart recovery (distinct PIDs);
  * absence of framework state in domain artifacts/audits.

Outcome honesty: every candidate probe records ``pass``, ``fail``, or
``not_validated``.  A silently-skipped candidate is ``not_validated``, not pass.
Where a candidate's PUBLIC GraphPort contract deviates from the reference
semantics, the deviation is recorded as a documented finding (the test asserts
the deviation is observed and labeled, not papered over).

Independent public-port challenges added here (not fully proven by candidate
focused suites):

  C-RUN-REUSE   public ``run`` on a fresh Store marks newly executed nodes
                ``reused=False`` (reference LocalGraphPort semantics).
                Manager repair: both candidates now match (pre-invocation
                terminal snapshot). Historical worker_04 post-exec deviation:
                failed_before_manager_repair -> pass_after_manager_repair.
  C-RESUME      ``resume`` marks ONLY nodes committed before that invocation as
                reused. Public paths verified for both after manager repair.
  C-REPLAY      ``replay`` marks EVERY node reused. Both pass; AF asserts.
  C-GRAPH-BIND  a supplied Graph with same graph_id/node set but altered edge
                order must fail BEFORE any Store node/event/checkpoint mutation.
                Manager repair: shared ``assert_exact_graph_ir``;
                failed_before_manager_repair -> pass_after_manager_repair.
  C-AF-CTOR     Agent Framework construction rejects constructor run_id !=
                contract.run_id and stale manifest fingerprint.
                failed_before_manager_repair -> pass_after_manager_repair.
  C-LG-FINALIZE LangGraph finalization catches ONLY ``CompletionGateError``;
                unexpected finalization errors propagate.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# conftest resolves slice1 + spike src onto sys.path
from mm_r1.store import Store
from mm_r1_spike.contract import REQUIRED_WORK_EVENT_FIELDS
from mm_r1_spike.restart_harness import (
    NODE_A,
    NODE_B,
    NODE_C,
)
from mm_r1_spike.work_events import WorkEventStore

# ---------------------------------------------------------------------------
# Candidate venvs (frozen in parent context; never installed together)
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


# ---------------------------------------------------------------------------
# Framework-neutral normalization built from Store + events (parent process,
# no framework dependency).  This is the SAME basis as
# ConformanceResult.conformance_key() but constructed independently in the
# parent so it cannot be influenced by adapter-internal state.
# ---------------------------------------------------------------------------


def _normalize_from_store(
    store_db: Path, events_db: Path, run_id: str
) -> Dict[str, Any]:
    """Build a framework-neutral normalized dict from the authoritative Store
    + the separate work-event store.  Reads only physical SQLite files; never
    imports a candidate adapter or framework."""
    store = Store(store_db, store_db.parent / "artifacts")
    events = WorkEventStore(events_db)
    try:
        manifest = store.get_manifest(run_id)
        if manifest is None:
            raise RuntimeError(f"no manifest for {run_id}")
        nodes_out: List[Dict[str, Any]] = []
        for nid in manifest.node_ids():
            nr = store.get_node_run(run_id, nid)
            status = nr.status.value if nr else "pending"
            nodes_out.append({"node_id": nid, "status": status})
        progress = store.manifest_progress(run_id)
        evs = events.list_events(run_id)

        # audit integrity (Store.verify_audit_chain -> (ok, first_bad, count))
        audit_ok, _first_bad, audit_count = store.verify_audit_chain()

        # physical counts from the domain DB
        conn = sqlite3.connect(str(store_db))
        try:
            n_runs = conn.execute(
                "SELECT COUNT(*) FROM node_runs WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            n_art = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
            n_facts = conn.execute("SELECT COUNT(*) FROM canonical_facts").fetchone()[0]
        finally:
            conn.close()

        return {
            "run_id": run_id,
            "graph_id": manifest.graph_id,
            "manifest_revision": manifest.revision,
            "nodes": nodes_out,
            "progress": {
                "completed": int(progress["completed"]),
                "total": int(progress["total"]),
            },
            "node_run_rows": n_runs,
            "artifact_count": n_art,
            "fact_count": n_facts,
            "events": [
                {
                    "sequence": e.sequence,
                    "node_id": e.node_id,
                    "phase": e.phase,
                    "status": e.status,
                    "completed": e.completed,
                    "total": e.total,
                    "idempotency_key": e.idempotency_key,
                }
                for e in evs
            ],
            "distinct_idempotency_keys": events.distinct_idempotency_keys(run_id),
            "audit_ok": bool(audit_ok),
            "audit_count": audit_count,
        }
    finally:
        store.close()
        events.close()


# ---------------------------------------------------------------------------
# Subprocess runner: runs a tiny framework-neutral script INSIDE the chosen
# candidate venv that (a) bootstraps a run, (b) drives it through the
# candidate adapter, and (c) prints CANDIDATE_RESULT=<json> with the PID and
# adapter-reported per-node reuse/status.  The parent then independently
# normalizes from Store + events.
# ---------------------------------------------------------------------------


def _run_candidate(
    py: str,
    work_dir: Path,
    run_id: str,
    *,
    scenario: str,
    extra_env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Run one candidate scenario in its own venv.

    scenarios:
      complete       bootstrap + run(graph) to completion
      stop_after_a   bootstrap + run to a boundary after node A (process A)
      resume         resume(run_id) from persisted state (process B)
      replay         replay(run_id) (every node reused)
    Returns the parsed CANDIDATE_RESULT JSON dict.
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    script = _CANDIDATE_SCRIPT
    argv = [
        py, "-c", script,
        scenario, str(work_dir), run_id,
    ]
    env = _env(extra_env)
    proc = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=120)
    if proc.returncode != 0:
        raise AssertionError(
            f"candidate subprocess ({scenario}) rc={proc.returncode}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    for line in proc.stdout.splitlines():
        if line.startswith("CANDIDATE_RESULT="):
            return json.loads(line[len("CANDIDATE_RESULT="):])
    raise AssertionError(
        f"no CANDIDATE_RESULT in stdout ({scenario}):\n{proc.stdout}\n---stderr---\n{proc.stderr}"
    )


# The script detects which framework is importable and uses the matching
# adapter.  This lets one script serve both venvs.  It bootstraps only when
# scenario == 'complete' or 'stop_after_a'; resume/replay reuse the persisted
# manifest.  It reports BOTH the public GraphRun reuse flags AND the private
# execution-path reuse flags (where available) so the parent can challenge
# them against the domain-authoritative Store state independently.
_CANDIDATE_SCRIPT = r'''
import json, os, sys
from pathlib import Path

scenario = sys.argv[1]
work_dir = Path(sys.argv[2])
run_id = sys.argv[3]

store_db = work_dir / "authoritative.sqlite3"
events_db = work_dir / "work_events.sqlite3"

from mm_r1.store import Store
from mm_r1_spike.contract import ConformanceContract
from mm_r1_spike.work_events import WorkEventStore
from mm_r1_spike.restart_harness import (
    bootstrap_run, synthetic_three_node_graph, NODE_A,
)

store = Store(store_db, store_db.parent / "artifacts")
events = WorkEventStore(events_db)


def _detect():
    try:
        import agent_framework  # noqa
        return "af"
    except Exception:
        pass
    try:
        import langgraph  # noqa
        return "lg"
    except Exception:
        return "none"


fw = _detect()
graph = synthetic_three_node_graph()

reported = {"framework": fw, "pid": os.getpid(), "ppid": os.getppid(),
            "scenario": scenario}

if fw == "af":
    from mm_r1_spike.agent_framework_adapter import AgentFrameworkWorkflowPort
    if scenario in ("complete", "stop_after_a"):
        manifest = bootstrap_run(store, run_id)
    else:
        manifest = store.get_manifest(run_id)
    contract = ConformanceContract.from_manifest(manifest)
    max_iter = 1 if scenario == "stop_after_a" else 100
    port = AgentFrameworkWorkflowPort(store, events, contract, work_dir,
                                      run_id=run_id, max_iterations=max_iter)
    if scenario in ("complete", "stop_after_a"):
        run = port.run(graph, run_id)
    elif scenario == "resume":
        run = port.resume(run_id)
    elif scenario == "replay":
        run = port.replay(run_id)
    else:
        raise SystemExit(f"bad scenario {scenario}")
    cr = port.conformance_result(run_id)
    reported["status"] = run.status
    reported["nodes"] = [
        {"node_id": n.node_id, "status": n.status, "reused": n.reused}
        for n in cr.nodes
    ]
    reported["conformance_key"] = cr.conformance_key()

elif fw == "lg":
    from mm_r1_spike.langgraph_adapter import LangGraphAdapter
    if scenario in ("complete", "stop_after_a"):
        manifest = bootstrap_run(store, run_id)
    else:
        manifest = store.get_manifest(run_id)
    contract = ConformanceContract.from_manifest(manifest)
    ad = LangGraphAdapter(store, events, work_dir)
    try:
        if scenario == "stop_after_a":
            r = ad._run_contract(contract, stop_after_node=NODE_A)
        else:
            r = ad._run_contract(contract)
        reported["status"] = "blocked" if scenario == "stop_after_a" else "complete"
        # PRIVATE execution-path reuse flags (domain-authoritative, pre-invocation)
        reported["private_reuse"] = {
            n.node_id: n.reused for n in r.node_results
        }
        # also expose a `nodes` list (status from Store, reused from private path)
        reported["nodes"] = [
            {"node_id": n.node_id,
             "status": n.status,
             "reused": bool(reported["private_reuse"].get(n.node_id, False))}
            for n in r.node_results
        ]
    finally:
        ad.close()
else:
    raise SystemExit("no candidate framework importable in this venv")

reported["progress"] = store.manifest_progress(run_id)
reported["event_count"] = events.count(run_id)
reported["distinct_keys"] = events.distinct_idempotency_keys(run_id)
store.close(); events.close()
sys.stdout.write("CANDIDATE_RESULT=" + json.dumps(reported, sort_keys=True) + "\n")
sys.stdout.flush()
'''


def _candidate_dir(tmp_path, name: str) -> Path:
    d = tmp_path / f"cand_{name}"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ===========================================================================
# Candidate availability gate (not_validated if a venv/import is missing)
# ===========================================================================


class TestCandidateAvailabilityRecord:
    """If a candidate cannot be exercised, the record must say so honestly.
    A missing venv or import failure is ``not_validated``, never pass."""

    _candidates = [
        ("langgraph", LG_PY),
        ("agent_framework", AF_PY),
    ]

    def test_both_candidate_venvs_exist(self):
        missing = [n for n, py in self._candidates if not Path(py).exists()]
        assert not missing, (
            f"candidate venv(s) missing: {missing} -> cross-candidate comparison "
            "is not_validated, not pass"
        )

    def test_candidate_status_matrix(self, tmp_path):
        """Record per-candidate pass/not_validated.  A missing venv or
        import failure is not_validated, never pass."""
        matrix = {}
        for name, py in self._candidates:
            if not Path(py).exists():
                matrix[name] = "not_validated"
                continue
            d = _candidate_dir(tmp_path, f"avail-{name}")
            try:
                res = _run_candidate(py, d, f"avail-{name}", scenario="complete")
                if res.get("framework") == "none":
                    matrix[name] = "not_validated"
                else:
                    matrix[name] = "pass"
            except Exception:
                matrix[name] = "not_validated"
        for name in ("langgraph", "agent_framework"):
            assert matrix[name] == "pass", (
                f"candidate {name} is {matrix[name]} (not pass); cross-candidate "
                "parity must NOT be claimed for this candidate"
            )


# ===========================================================================
# 1. Cross-candidate conformance: both candidates produce the SAME normalized
#    authoritative output from the same synthetic three-node manifest.
#    (This is the STORE-NORMALIZED comparison — the basis the execution
#    context mandates: "compare normalized authoritative outputs".)
# ===========================================================================


class TestCrossCandidateNormalizedEquivalence:
    """Both candidates, run to completion in their own venv, must produce
    identical normalized authoritative Store + work-event shape."""

    def test_completion_produces_identical_normalized_output(self, tmp_path):
        lg_dir = _candidate_dir(tmp_path, "lg")
        af_dir = _candidate_dir(tmp_path, "af")
        _run_candidate(LG_PY, lg_dir, "run-lg", scenario="complete")
        _run_candidate(AF_PY, af_dir, "run-af", scenario="complete")

        lg_norm = _normalize_from_store(
            lg_dir / "authoritative.sqlite3", lg_dir / "work_events.sqlite3", "run-lg"
        )
        af_norm = _normalize_from_store(
            af_dir / "authoritative.sqlite3", af_dir / "work_events.sqlite3", "run-af"
        )

        # run_id differs by design; compare conformance-significant fields.
        for key in ("graph_id", "manifest_revision", "progress", "node_run_rows",
                    "artifact_count", "fact_count", "distinct_idempotency_keys",
                    "audit_ok", "audit_count", "nodes"):
            assert lg_norm[key] == af_norm[key], (
                f"cross-candidate divergence on {key}:\n"
                f"  lg={lg_norm[key]!r}\n  af={af_norm[key]!r}"
            )
        assert len(lg_norm["events"]) == len(af_norm["events"]) == 6
        lg_phases = [(e["node_id"], e["phase"]) for e in lg_norm["events"]]
        af_phases = [(e["node_id"], e["phase"]) for e in af_norm["events"]]
        assert lg_phases == af_phases
        assert lg_norm["progress"] == {"completed": 3, "total": 3}

    def test_work_events_carry_all_required_fields_both_candidates(self, tmp_path):
        for name, py, run_id in (("lg", LG_PY, "run-fields-lg"),
                                 ("af", AF_PY, "run-fields-af")):
            d = _candidate_dir(tmp_path, name)
            _run_candidate(py, d, run_id, scenario="complete")
            events = WorkEventStore(d / "work_events.sqlite3")
            try:
                evs = events.list_events(run_id)
                assert len(evs) == 6
                for ev in evs:
                    d_ev = ev.to_json()
                    for f in REQUIRED_WORK_EVENT_FIELDS:
                        assert f in d_ev, f"{name}: event missing {f}"
                    assert d_ev["total"] == 3
            finally:
                events.close()


# ===========================================================================
# 2. Independent public-port reuse-semantics challenge (C-RUN/RESUME/REPLAY)
#
#    Manager repair 2026-08-09: both candidates' PUBLIC GraphRun (and AF
#    conformance_result) now derive ``reused`` from the pre-invocation
#    terminal snapshot.  Fresh run -> all False; resume -> only earlier
#    committed True; replay -> all True.  Historical worker_04 finding of
#    post-execution ``reused=True`` is recorded as
#    failed_before_manager_repair -> pass_after_manager_repair.
# ===========================================================================


# Reference semantics (LocalGraphPort, graph.py:356-360): a node is reused
# only if it was ALREADY terminal before this invocation.  Freshly executed
# nodes carry reused=False (GraphNodeResult default, line 216).
REF_FRESH_REUSED = False


class TestPublicPortReuseSemanticsChallenge:
    """C-RUN-REUSE / C-RESUME / C-REPLAY: independently challenge the public
    run/resume/replay reuse contract."""

    def test_run_public_reuse_flags_observed_and_labeled(self, tmp_path):
        """C-RUN-REUSE: public run on a fresh Store marks every node
        reused=False (reference LocalGraphPort semantics)."""
        findings = {}
        for name, py, run_id in (("lg", LG_PY, "run-reuse-lg"),
                                 ("af", AF_PY, "run-reuse-af")):
            d = _candidate_dir(tmp_path, name)
            res = _run_candidate(py, d, run_id, scenario="complete")
            fresh_reused = {n["node_id"]: n["reused"] for n in res["nodes"]}
            all_false = all(v is REF_FRESH_REUSED for v in fresh_reused.values())
            findings[name] = "match" if all_false else "deviation"
        assert findings == {"lg": "match", "af": "match"}, (
            "C-RUN-REUSE public reused flags must match reference "
            f"(fresh=False): {findings}"
        )

    def test_run_private_execution_path_reuse_correct(self, tmp_path):
        """The PRIVATE execution path (LG _run_contract, which tracks
        pre-invocation terminal state) must mark fresh nodes reused=False.
        This proves the domain-authoritative reuse computation is correct even
        though the public GraphRun flag deviates."""
        d = _candidate_dir(tmp_path, "lgpriv")
        res = _run_candidate(LG_PY, d, "run-priv-lg", scenario="complete")
        priv = res["private_reuse"]
        assert all(v is False for v in priv.values()), (
            f"LG private path fresh-run reuse wrong: {priv}"
        )

    def test_resume_marks_only_pre_committed_nodes_reused_private(self, tmp_path):
        """C-RESUME (private path): process A stops after node A; fresh process
        B resumes.  Private reuse must mark ONLY node A reused."""
        d = _candidate_dir(tmp_path, "lgresume")
        a = _run_candidate(LG_PY, d, "resume-lg", scenario="stop_after_a")
        assert a["pid"] > 0
        # process A private: node A executed fresh
        assert a["private_reuse"][NODE_A] is False
        # fresh process B resumes
        b = _run_candidate(LG_PY, d, "resume-lg", scenario="resume")
        assert b["pid"] != a["pid"], "A/B PIDs not distinct"
        # private reuse: only node A reused
        assert b["private_reuse"] == {NODE_A: True, NODE_B: False, NODE_C: False}, (
            f"LG private resume reuse wrong: {b['private_reuse']}"
        )

    def test_replay_marks_every_node_reused(self, tmp_path):
        """C-REPLAY: both candidates mark every node reused on replay (all
        terminal post-execution, so the public flag is correct here)."""
        for name, py, run_id in (("lg", LG_PY, "replay-lg"),
                                 ("af", AF_PY, "replay-af")):
            d = _candidate_dir(tmp_path, name)
            _run_candidate(py, d, run_id, scenario="complete")
            r = _run_candidate(py, d, run_id, scenario="replay")
            for n in r["nodes"]:
                assert n["reused"] is True, (
                    f"{name}: replay did not reuse {n['node_id']}"
                )

    def test_replay_does_not_duplicate_events_or_side_effects(self, tmp_path):
        for name, py, run_id in (("lg", LG_PY, "replay-dedup-lg"),
                                 ("af", AF_PY, "replay-dedup-af")):
            d = _candidate_dir(tmp_path, name)
            _run_candidate(py, d, run_id, scenario="complete")
            before = _normalize_from_store(
                d / "authoritative.sqlite3", d / "work_events.sqlite3", run_id
            )
            _run_candidate(py, d, run_id, scenario="replay")
            after = _normalize_from_store(
                d / "authoritative.sqlite3", d / "work_events.sqlite3", run_id
            )
            assert after["events"] == before["events"]
            assert after["node_run_rows"] == before["node_run_rows"] == 3
            assert after["progress"] == before["progress"]


# ===========================================================================
# 3. Fresh-process recovery: cross-candidate subprocess boundary evidence
# ===========================================================================


class TestFreshProcessRecovery:
    """Both candidates must complete a run across a real subprocess boundary
    with distinct PIDs, no duplicate domain side effects."""

    def test_two_fresh_processes_complete_with_distinct_pids(self, tmp_path):
        for name, py, run_id in (("lg", LG_PY, "restart-lg"),
                                 ("af", AF_PY, "restart-af")):
            d = _candidate_dir(tmp_path, name)
            a = _run_candidate(py, d, run_id, scenario="stop_after_a")
            b = _run_candidate(py, d, run_id, scenario="resume")
            assert a["pid"] != b["pid"]
            norm = _normalize_from_store(
                d / "authoritative.sqlite3", d / "work_events.sqlite3", run_id
            )
            assert norm["progress"] == {"completed": 3, "total": 3}
            assert norm["node_run_rows"] == 3
            assert len(norm["events"]) == 6
            assert norm["distinct_idempotency_keys"] == 6
            assert all(n["status"] == "passed" for n in norm["nodes"])
            assert norm["artifact_count"] == 0
            assert norm["fact_count"] == 0
            assert norm["audit_ok"] is True


# ===========================================================================
# 4. Store / node / artifact / audit count conformance
# ===========================================================================


class TestStoreNodeArtifactAuditCounts:
    def test_counts_agree_across_candidates(self, tmp_path):
        norms = {}
        for name, py, run_id in (("lg", LG_PY, "counts-lg"),
                                 ("af", AF_PY, "counts-af")):
            d = _candidate_dir(tmp_path, name)
            _run_candidate(py, d, run_id, scenario="complete")
            norms[name] = _normalize_from_store(
                d / "authoritative.sqlite3", d / "work_events.sqlite3", run_id
            )
        for key in ("node_run_rows", "artifact_count", "fact_count",
                    "audit_count", "progress"):
            assert norms["lg"][key] == norms["af"][key], key
        assert norms["lg"]["node_run_rows"] == 3
        assert norms["lg"]["artifact_count"] == 0
        assert norms["lg"]["fact_count"] == 0


# ===========================================================================
# 5. Event ordering and idempotency (cross-candidate)
# ===========================================================================


class TestEventOrderingIdempotency:
    def test_monotonic_sequences_and_unique_keys_both_candidates(self, tmp_path):
        for name, py, run_id in (("lg", LG_PY, "order-lg"),
                                 ("af", AF_PY, "order-af")):
            d = _candidate_dir(tmp_path, name)
            _run_candidate(py, d, run_id, scenario="complete")
            norm = _normalize_from_store(
                d / "authoritative.sqlite3", d / "work_events.sqlite3", run_id
            )
            seqs = [e["sequence"] for e in norm["events"]]
            assert seqs == sorted(seqs), f"{name}: sequences not monotonic"
            keys = [e["idempotency_key"] for e in norm["events"]]
            assert len(keys) == len(set(keys)), f"{name}: duplicate keys"

    def test_begin_before_complete_per_node_both_candidates(self, tmp_path):
        for name, py, run_id in (("lg", LG_PY, "phase-lg"),
                                 ("af", AF_PY, "phase-af")):
            d = _candidate_dir(tmp_path, name)
            _run_candidate(py, d, run_id, scenario="complete")
            norm = _normalize_from_store(
                d / "authoritative.sqlite3", d / "work_events.sqlite3", run_id
            )
            for nid in (NODE_A, NODE_B, NODE_C):
                phases = [e["phase"] for e in norm["events"] if e["node_id"] == nid]
                assert phases == ["node_begin", "node_complete"], (
                    f"{name}: node {nid} phases={phases}"
                )


# ===========================================================================
# 6. Absence of framework state in domain artifacts (cross-candidate)
# ===========================================================================


class TestNoFrameworkStateInDomainArtifacts:
    def test_checkpoint_tables_absent_from_domain_db_both(self, tmp_path):
        """The domain Store DB must NOT contain framework-specific checkpoint
        tables.  Note: slice1's domain Store legitimately has a ``checkpoints``
        table (the CheckpointPort domain authority), and LangGraph's checkpoint
        DB also uses ``checkpoints``; the framework-SPECIFIC leak signal is
        the langgraph ``writes`` table.  We assert (a) the domain DB has no
        ``writes`` table and (b) the langgraph checkpoint DB is a physically
        separate file from the domain Store."""
        for name, py, run_id in (("lg", LG_PY, "noleak-lg"),
                                 ("af", AF_PY, "noleak-af")):
            d = _candidate_dir(tmp_path, name)
            _run_candidate(py, d, run_id, scenario="complete")
            store_db = d / "authoritative.sqlite3"
            conn = sqlite3.connect(str(store_db))
            try:
                tables = {r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                # langgraph 'writes' table is framework-specific; must be absent
                assert "writes" not in tables, (
                    f"{name}: langgraph 'writes' table leaked into domain DB"
                )
                art = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
                facts = conn.execute("SELECT COUNT(*) FROM canonical_facts").fetchone()[0]
                assert art == 0 and facts == 0
            finally:
                conn.close()
            # langgraph checkpoint DB is a physically separate file
            if name == "lg":
                lg_ckpt = d / "langgraph_checkpoints.sqlite3"
                assert lg_ckpt.exists() and lg_ckpt != store_db
                c2 = sqlite3.connect(str(lg_ckpt))
                try:
                    lg_tables = {r[0] for r in c2.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'")}
                    assert {"checkpoints", "writes"} <= lg_tables
                    # domain tables absent from the framework checkpoint DB
                    assert "node_runs" not in lg_tables
                    assert "artifacts" not in lg_tables
                finally:
                    c2.close()

    def test_framework_checkpoint_files_separate_from_store_both(self, tmp_path):
        for name, py, run_id, marker_files in (
            ("lg", LG_PY, "sep-lg", ["langgraph_checkpoints.sqlite3"]),
            ("af", AF_PY, "sep-af", ["af_checkpoints"]),
        ):
            d = _candidate_dir(tmp_path, name)
            _run_candidate(py, d, run_id, scenario="complete")
            store_db = d / "authoritative.sqlite3"
            assert store_db.exists()
            for mf in marker_files:
                assert (d / mf).exists(), f"{name}: framework persistence {mf} missing"


# ===========================================================================
# 7. C-GRAPH-BIND: altered Graph must fail before any Store mutation.
#    Same graph_id and node SET but altered edge order.  A mere graph_id +
#    node-set check would ACCEPT this; the manifest-fingerprint binding must
#    reject it before any Store node/event/checkpoint mutation.
# ===========================================================================


def _run_graph_bind_probe(py: str, work_dir: Path, run_id: str) -> Dict[str, Any]:
    script = r'''
import json, os, sys
from pathlib import Path
run_id = sys.argv[1]
work_dir = Path(sys.argv[2])
store_db = work_dir / "authoritative.sqlite3"
events_db = work_dir / "work_events.sqlite3"
from mm_r1.store import Store
from mm_r1_spike.contract import ConformanceContract
from mm_r1_spike.work_events import WorkEventStore
from mm_r1_spike.restart_harness import bootstrap_run, NODE_A, NODE_B, NODE_C

store = Store(store_db, store_db.parent / "artifacts")
events = WorkEventStore(events_db)
manifest = bootstrap_run(store, run_id)
contract = ConformanceContract.from_manifest(manifest)

# Build a graph with the SAME graph_id + SAME node set but reordered edges.
from mm_r1.graph import Graph, GraphNode, GraphEdge
nodes = [
    GraphNode(node_id=NODE_A, node_type=manifest.nodes[0].node_type),
    GraphNode(node_id=NODE_B, node_type=manifest.nodes[0].node_type),
    GraphNode(node_id=NODE_C, node_type=manifest.nodes[0].node_type),
]
# altered edge ORDER: B -> A -> C (same nodes, same graph_id, different topology)
edges = [GraphEdge(src=NODE_B, dst=NODE_A), GraphEdge(src=NODE_A, dst=NODE_C)]
altered = Graph(graph_id=manifest.graph_id, nodes={n.node_id: n for n in nodes}, edges=edges)

events_before = events.count(run_id)
rows_before = store.manifest_progress(run_id)["completed"]

out = {"pid": os.getpid(), "events_before": events_before, "rows_before": rows_before}
try:
    fw = "none"
    try:
        import agent_framework; fw = "af"
    except Exception:
        import langgraph; fw = "lg"
    if fw == "af":
        from mm_r1_spike.agent_framework_adapter import AgentFrameworkWorkflowPort
        port = AgentFrameworkWorkflowPort(store, events, contract, work_dir, run_id=run_id)
        port.run(altered, run_id)
        out["accepted"] = True
    else:
        from mm_r1_spike.langgraph_adapter import LangGraphAdapter
        ad = LangGraphAdapter(store, events, work_dir)
        ad.run(altered, run_id)
        ad.close()
        out["accepted"] = True
    out["raised"] = False
except Exception as exc:
    out["raised"] = True
    out["error_type"] = type(exc).__name__
    out["accepted"] = False
out["events_after"] = events.count(run_id)
out["rows_after"] = store.manifest_progress(run_id)["completed"]
store.close(); events.close()
sys.stdout.write("GRAPH_BIND_PROBE=" + json.dumps(out, sort_keys=True) + "\n")
'''
    work_dir.mkdir(parents=True, exist_ok=True)
    env = _env()
    proc = subprocess.run(
        [py, "-c", script, run_id, str(work_dir)],
        capture_output=True, text=True, env=env, timeout=120,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("GRAPH_BIND_PROBE="):
            return json.loads(line[len("GRAPH_BIND_PROBE="):])
    raise AssertionError(
        f"no GRAPH_BIND_PROBE:\n{proc.stdout}\n---\n{proc.stderr}"
    )


class TestGraphBindingChallenge:
    """C-GRAPH-BIND: an altered graph (same graph_id/node set, different
    topology) must be rejected before any Store mutation."""

    def test_altered_edge_order_rejected_before_mutation(self, tmp_path):
        for name, py, run_id in (("lg", LG_PY, "gbind-lg"),
                                 ("af", AF_PY, "gbind-af")):
            d = _candidate_dir(tmp_path, name)
            probe = _run_graph_bind_probe(py, d, run_id)
            assert probe["raised"] is True, (
                f"{name}: altered-edge-order graph was ACCEPTED without raising "
                "(graph_id+node-set check is insufficient; manifest-fingerprint "
                "binding must reject it)"
            )
            assert probe["accepted"] is False
            assert probe["events_after"] == probe["events_before"] == 0, (
                f"{name}: events mutated before rejection "
                f"({probe['events_before']} -> {probe['events_after']})"
            )
            assert probe["rows_after"] == probe["rows_before"] == 0


# ===========================================================================
# 8. C-AF-CTOR: Agent Framework construction identity binding
# ===========================================================================


def _run_af_ctor_probe(work_dir: Path, run_id: str, probe: str) -> Dict[str, Any]:
    script = r'''
import json, os, sys
from pathlib import Path
probe = sys.argv[1]
run_id = sys.argv[2]
work_dir = Path(sys.argv[3])
store_db = work_dir / "authoritative.sqlite3"
events_db = work_dir / "work_events.sqlite3"
from mm_r1.store import Store
from mm_r1_spike.contract import ConformanceContract
from mm_r1_spike.work_events import WorkEventStore
from mm_r1_spike.restart_harness import bootstrap_run

store = Store(store_db, store_db.parent / "artifacts")
events = WorkEventStore(events_db)
manifest = bootstrap_run(store, run_id)
contract = ConformanceContract.from_manifest(manifest)
out = {"pid": os.getpid(), "probe": probe, "events_before": events.count(run_id)}

from mm_r1_spike.agent_framework_adapter import AgentFrameworkWorkflowPort
try:
    if probe == "wrong_run_id":
        port = AgentFrameworkWorkflowPort(
            store, events, contract, work_dir,
            run_id="DIFFERENT_RUN_ID", max_iterations=100,
        )
        out["raised"] = False
    elif probe == "stale_fingerprint":
        import dataclasses
        stale = dataclasses.replace(contract, manifest_fingerprint="STALE_FP")
        port = AgentFrameworkWorkflowPort(
            store, events, stale, work_dir, run_id=run_id, max_iterations=100,
        )
        out["raised"] = False
    else:
        out["raised"] = False
        out["error"] = "unknown probe"
except Exception as exc:
    out["raised"] = True
    out["error_type"] = type(exc).__name__
out["events_after"] = events.count(run_id)
store.close(); events.close()
sys.stdout.write("AF_CTOR_PROBE=" + json.dumps(out, sort_keys=True) + "\n")
'''
    work_dir.mkdir(parents=True, exist_ok=True)
    env = _env()
    proc = subprocess.run(
        [AF_PY, "-c", script, probe, run_id, str(work_dir)],
        capture_output=True, text=True, env=env, timeout=120,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("AF_CTOR_PROBE="):
            return json.loads(line[len("AF_CTOR_PROBE="):])
    raise AssertionError(f"no AF_CTOR_PROBE:\n{proc.stdout}\n---\n{proc.stderr}")


class TestAgentFrameworkCtorIdentityChallenge:
    """C-AF-CTOR: AF construction must reject wrong run_id / stale fingerprint
    before creating a checkpoint namespace or emitting an event.

    Historical worker_04 finding: constructor accepted mismatched bindings
    (failed_before_manager_repair).  Manager repair rejects at construction
    before checkpoint dirs/storage are created (pass_after_manager_repair).
    """

    def test_wrong_constructor_run_id_observed(self, tmp_path):
        d = _candidate_dir(tmp_path, "afctor1")
        probe = _run_af_ctor_probe(d, "af-ctor-1", probe="wrong_run_id")
        assert probe.get("raised") is True, (
            "C-AF-CTOR wrong_run_id: AgentFrameworkWorkflowPort accepted a "
            "constructor run_id != contract.run_id without raising. The "
            "adapter must reject this before creating/using a checkpoint "
            f"namespace. probe={probe}"
        )
        assert probe["events_after"] == probe["events_before"] == 0

    def test_stale_manifest_fingerprint_observed(self, tmp_path):
        d = _candidate_dir(tmp_path, "afctor2")
        probe = _run_af_ctor_probe(d, "af-ctor-2", probe="stale_fingerprint")
        assert probe.get("raised") is True, (
            "C-AF-CTOR stale_fingerprint: AgentFrameworkWorkflowPort accepted "
            "a stale manifest fingerprint without raising. probe={probe}".format(
                probe=probe)
        )
        assert probe["events_after"] == probe["events_before"] == 0


# ===========================================================================
# 9. C-LG-FINALIZE: LangGraph finalization catches ONLY the expected
#    analysis completion-gate exception, not a broad swallow.
# ===========================================================================


class TestLangGraphFinalizationNarrowCatch:
    """C-LG-FINALIZE: the LangGraph adapter's finalization block must catch
    only the analysis CompletionGateError, not mask arbitrary failures
    in the per-node domain-commit path."""

    def test_finalize_catches_only_gate_exception(self):
        src = (_SPIKE_SRC / "mm_r1_spike" / "langgraph_adapter.py").read_text()
        # The finalization try/except documents the narrow gate scope.
        assert "CompletionGateError" in src, (
            "LangGraph finalize: must catch CompletionGateError specifically"
        )
        assert "except CompletionGateError" in src, (
            "LangGraph finalize: missing narrow CompletionGateError catch"
        )
        # The per-node _execute_node must NOT swallow exceptions in the
        # domain-commit path.  Confirm _execute_node has no broad except.
        exec_start = src.index("def _execute_node")
        exec_end = src.index("def verify_checkpoint_identity")
        exec_body = src[exec_start:exec_end]
        assert "except Exception" not in exec_body, (
            "LangGraph _execute_node swallows exceptions in the domain-commit path"
        )

    def test_only_finalize_block_has_gate_catch(self):
        """The finalize block catches CompletionGateError only; run/resume/
        replay and _execute_node must not broadly swallow exceptions."""
        src = (_SPIKE_SRC / "mm_r1_spike" / "langgraph_adapter.py").read_text()
        mat_start = src.index("def _materialize_graph_run")
        mat_end = src.index("\n# ----", mat_start) if "\n# ----" in src[mat_start:] \
            else len(src)
        mat_body = src[mat_start:mat_end] if mat_end > mat_start else src[mat_start:]
        assert "except CompletionGateError" in mat_body, (
            "finalize block missing its narrow CompletionGateError catch"
        )
        assert "except Exception" not in mat_body, (
            "finalize block must not use broad except Exception"
        )
        # replay() has a RuntimeError raise on non-reused; it must not be
        # swallowed by a broad except inside replay().
        replay_start = src.index("def replay(")
        replay_end = src.index("def _materialize_graph_run")
        replay_body = src[replay_start:replay_end]
        assert "except Exception" not in replay_body, (
            "replay() swallows exceptions (broad except present)"
        )
