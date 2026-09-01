"""Subprocess restart/replay harness (worker_01-owned spike substrate).

Provides a real two-process execution boundary: process A completes node 0 and
exits at an injected boundary; process B is freshly launched against the
persisted authoritative Store plus the separate work-event/checkpoint
persistence and finishes the manifest.  The harness records process identity
and invocation evidence so the boundary is observable and inspectable.

The harness is framework-neutral: it drives a plain synthetic three-node graph
through the accepted ``mm_r1`` Store + work-event store.  It does NOT import
LangGraph or Microsoft Agent Framework; later worker adapters plug a candidate
``GraphPort`` behind this boundary.

Only JSON-compatible synthetic state and SQLite/JSON from the standard library
are used.  The authoritative slice1 Store remains the sole domain authority;
the work-event store and checkpoint JSON file are separate operational
persistence.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from mm_r1.domain import (
    ExecutionManifest,
    NodeStatus,
    TERMINAL_NODE_STATUSES,
    content_hash,
    now_iso,
)
from mm_r1.graph import Graph
from mm_r1.store import Store

from .contract import ConformanceContract, PHASE_NODE_BEGIN, PHASE_NODE_COMPLETE
from .work_events import WorkEventStore


# ---------------------------------------------------------------------------
# Deterministic synthetic three-node graph/manifest fixture
# ---------------------------------------------------------------------------

NODE_A = "synth_node_a"
NODE_B = "synth_node_b"
NODE_C = "synth_node_c"
SYNTH_GRAPH_ID = "synth-three-node-v1"


def synthetic_three_node_graph() -> Graph:
    """Deterministic synthetic three-node linear graph (A -> B -> C).

    Framework-neutral: plain dataclass IR, no framework types.  All three
    nodes are deterministic-service synthetic handlers that produce a
    JSON-compatible output keyed by node id.
    """
    graph = Graph(graph_id=SYNTH_GRAPH_ID)
    graph.add_node(_synth_node(NODE_A))
    graph.add_node(_synth_node(NODE_B))
    graph.add_node(_synth_node(NODE_C))
    graph.add_edge(NODE_A, NODE_B)
    graph.add_edge(NODE_B, NODE_C)
    return graph


def _synth_node(node_id: str):
    from mm_r1.graph import GraphNode
    from mm_r1.domain import NodeType

    return GraphNode(
        node_id=node_id,
        node_type=NodeType.DETERMINISTIC_SERVICE,
        handler=f"synth:{node_id}",
        description=f"synthetic deterministic node {node_id}",
        artifact_required=False,
    )


def synthetic_manifest(run_id: str, manifest_revision: int = 1) -> ExecutionManifest:
    """The frozen deterministic three-node manifest for ``run_id``."""
    graph = synthetic_three_node_graph()
    return graph.to_manifest(
        run_id,
        revision=manifest_revision,
        identity_algorithm="synth-identity-v1",
        graph_version=SYNTH_GRAPH_ID,
        schema_version="synth-schema-v1",
    )


# ---------------------------------------------------------------------------
# Checkpoint JSON file (separate operational persistence, JSON-only)
# ---------------------------------------------------------------------------

def checkpoint_path(work_dir: Path) -> Path:
    return Path(work_dir) / "operational_checkpoint.json"


class CheckpointIdentityError(RuntimeError):
    """The operational checkpoint identity binding is missing/mismatched/corrupt.

    Raised fail-closed before any checkpoint output is used, so a wrong-run,
    wrong-revision/graph, or malformed JSON checkpoint never mutates the
    authoritative Store or the work-event DB.
    """


def save_operational_checkpoint(
    work_dir: Path,
    contract: ConformanceContract,
    last_completed_node: Optional[str],
    node_outputs: Mapping[str, Mapping[str, Any]],
) -> Path:
    """Persist a JSON-only operational checkpoint of synthetic execution state.

    This is separate operational persistence (untrusted), never domain
    authority.  It records exact run/revision/graph/node-set identity (bound
    to the frozen contract) plus which node completed last and the JSON output
    of each node so a fresh process can resume deterministically AND verify it
    is resuming the same frozen graph.
    """
    path = checkpoint_path(work_dir)
    payload = {
        "run_id": contract.run_id,
        "manifest_revision": contract.manifest_revision,
        "graph_id": contract.graph_id,
        "node_ids": list(contract.node_ids),
        "manifest_fingerprint": contract.manifest_fingerprint,
        "last_completed_node": last_completed_node,
        "node_outputs": {k: dict(v) for k, v in node_outputs.items()},
        "saved_at": now_iso(),
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def load_operational_checkpoint(
    work_dir: Path, contract: Optional[ConformanceContract] = None
) -> Optional[Mapping[str, Any]]:
    """Load and (when a contract is given) verify the operational checkpoint.

    Fail closed: malformed JSON, a missing identity field, or any mismatch
    against the contract (run_id, manifest_revision, graph_id, node_ids,
    manifest_fingerprint) raises :class:`CheckpointIdentityError` BEFORE any
    output is returned, so the caller cannot mutate authoritative state from a
    wrong/corrupt checkpoint.
    """
    path = checkpoint_path(work_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CheckpointIdentityError(f"malformed checkpoint JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise CheckpointIdentityError("checkpoint root is not a JSON object")
    if contract is not None:
        _verify_checkpoint_identity(data, contract)
    return data


def _verify_checkpoint_identity(data: Mapping[str, Any], contract: ConformanceContract) -> None:
    """Fail closed if the checkpoint does not bind to the exact frozen graph."""
    required = ("run_id", "manifest_revision", "graph_id", "node_ids",
                "manifest_fingerprint")
    missing = [f for f in required if f not in data]
    if missing:
        raise CheckpointIdentityError(
            f"checkpoint missing identity fields: {missing}"
        )
    checks = [
        ("run_id", data["run_id"], contract.run_id),
        ("manifest_revision", int(data["manifest_revision"]), contract.manifest_revision),
        ("graph_id", data["graph_id"], contract.graph_id),
        ("node_ids", list(data["node_ids"]), list(contract.node_ids)),
        ("manifest_fingerprint", data["manifest_fingerprint"], contract.manifest_fingerprint),
    ]
    for name, got, want in checks:
        if got != want:
            raise CheckpointIdentityError(
                f"checkpoint {name} mismatch: {got!r} != {want!r}"
            )

# ---------------------------------------------------------------------------
# In-process synthetic runner (used by both parent and subprocess worker)
# ---------------------------------------------------------------------------

SYNTH_OUTPUT_KEY = "synth_outputs"


def synth_handler(node_id: str, ctx) -> "NodeOutcome":  # type: ignore[name-defined]
    """Deterministic synthetic node handler producing JSON-compatible output.

    Idempotent: same node id always produces the same output content hash, so
    replay/restart never duplicates a side effect.
    """
    from mm_r1.graph import NodeOutcome

    output = {"node_id": node_id, "marker": "SYNTHETIC", "value_hash": content_hash(node_id)}
    ctx.save_checkpoint({"node_id": node_id, "output": output})
    return NodeOutcome(status=NodeStatus.PASSED, output={SYNTH_OUTPUT_KEY: output})


@dataclass
class NodeStepResult:
    node_id: str
    status: str
    reused: bool
    work_event_sequence: int


def run_nodes_up_to_boundary(
    store: Store,
    events: WorkEventStore,
    contract: ConformanceContract,
    work_dir: Path,
    run_id: str,
    stop_after_node: Optional[str],
    rev: int,
) -> List[NodeStepResult]:
    """Execute synthetic nodes in manifest order up to (and including)
    ``stop_after_node``, then return.  Emits structured work events and saves
    an operational checkpoint after each node.

    Resumes from any committed Store state + operational checkpoint, so a
    fresh process picks up exactly where the prior process stopped without
    duplicating side effects.
    """
    manifest = store.get_manifest(run_id)
    if manifest is None:
        raise RuntimeError(f"no manifest frozen for run {run_id}")
    node_ids = manifest.node_ids()
    outputs: Dict[str, Mapping[str, Any]] = {}
    ckpt = load_operational_checkpoint(work_dir, contract)
    if ckpt is not None:
        raw_outputs = ckpt.get("node_outputs", {})
        # fail closed: any unknown node id in the checkpoint is rejected
        unknown = [k for k in raw_outputs if k not in set(contract.node_ids)]
        if unknown:
            raise CheckpointIdentityError(
                f"checkpoint contains unknown node outputs: {unknown}"
            )
        outputs = {k: dict(v) for k, v in raw_outputs.items()}

    results: List[NodeStepResult] = []
    reached_stop = False
    for node_id in node_ids:
        existing = store.get_node_run(run_id, node_id)
        is_terminal = existing is not None and existing.status in TERMINAL_NODE_STATUSES
        key = f"g:{manifest.graph_id}:{node_id}:r{rev}"


        # node_begin fires only when the node is actually starting (not a
        # reused terminal node).  Re-emitting begin for a reused node would
        # replay the same idempotency key with a different completed count
        # (progress advanced) and be rejected as divergent; reuse instead.
        if not is_terminal:
            events.append(
                _work_event(run_id, contract, node_id, PHASE_NODE_BEGIN, node_id,
                            status=NodeStatus.RUNNING.value,
                            completed=_completed_so_far(store, manifest)),
                contract,
            )

        if is_terminal:
            if existing and existing.output:
                outputs[node_id] = existing.output.get(SYNTH_OUTPUT_KEY, {})
            # reused terminal node: do NOT re-emit node_complete (it was
            # recorded at original completion with the progress at that time).
            # Re-emitting would replay the same idempotency key with a now-
            # different completed count and be rejected as divergent.  Look
            # up the existing event sequence instead -> true replay no-op.
            ev_seq = events.sequence_for(run_id, node_id, PHASE_NODE_COMPLETE)
            results.append(NodeStepResult(node_id, existing.status.value, reused=True,
                                          work_event_sequence=ev_seq))
        else:
            store.begin_node_run(run_id, node_id, manifest.nodes[0].node_type, key)
            from mm_r1.graph import NodeContext

            ctx = NodeContext(run_id=run_id, node_id=node_id,
                              node_type=manifest.nodes[0].node_type,
                              store=store, checkpoint=store, shared={SYNTH_OUTPUT_KEY: outputs})
            outcome = synth_handler(node_id, ctx)
            completed = store.complete_node_run(
                run_id, node_id, key, outcome.status, output=outcome.output
            )
            outputs[node_id] = outcome.output.get(SYNTH_OUTPUT_KEY, {}) if outcome.output else {}
            ev = events.append(
                _work_event(run_id, contract, node_id, PHASE_NODE_COMPLETE, node_id,
                            status=completed.status.value,
                            completed=_completed_so_far(store, manifest)),
                contract,
            )
            results.append(NodeStepResult(node_id, completed.status.value, reused=False,
                                          work_event_sequence=ev.sequence))

        save_operational_checkpoint(work_dir, contract, node_id, outputs)
        if stop_after_node is not None and node_id == stop_after_node:
            reached_stop = True
            break

    if stop_after_node is not None and not reached_stop:
        raise RuntimeError(
            f"stop_after_node {stop_after_node!r} not found in manifest {node_ids}"
        )
    return results


def _completed_so_far(store: Store, manifest: ExecutionManifest) -> int:
    progress = store.manifest_progress(run_id := manifest.run_id)
    return int(progress["completed"])


def _work_event(
    run_id: str,
    contract: ConformanceContract,
    node_id: str,
    phase: str,
    work_unit_id: str,
    status: str,
    completed: int,
) -> Dict[str, Any]:
    from mm_r1.domain import new_id

    return {
        "event_id": new_id("we_"),
        "run_id": run_id,
        "manifest_revision": contract.manifest_revision,
        "sequence": 0,  # assigned by store
        "node_id": node_id,
        "work_unit_id": work_unit_id,
        "phase": phase,
        "status": status,
        "completed": completed,
        "total": contract.total_units,
        "current_detail": f"{phase}:{node_id}",
        "created_at": now_iso(),
        "idempotency_key": f"we:{run_id}:{node_id}:{phase}",
    }


# ---------------------------------------------------------------------------
# Subprocess restart harness
# ---------------------------------------------------------------------------

@dataclass
class SubprocessRecord:
    """Process identity + invocation evidence for one subprocess boundary."""

    pid: int
    argv: List[str]
    returncode: int
    stdout: str
    stderr: str
    invocation_marker: str
    started_at: str
    finished_at: str


@dataclass
class RestartOutcome:
    """Full two-process restart outcome (parent-assembles)."""

    first_process: SubprocessRecord
    second_process: SubprocessRecord
    node_results: List[NodeStepResult] = field(default_factory=list)
    final_status: str = ""
    pids_differ: bool = True


RESTART_WORKER_SCRIPT = "restart_worker.py"


def _worker_script_path() -> Path:
    """Resolve the restart_worker.py script path relative to this package."""
    # this file: spikes/framework_adapters/src/mm_r1_spike/restart_harness.py
    # script:   spikes/framework_adapters/scripts/restart_worker.py
    spike_root = Path(__file__).resolve().parents[2]
    return spike_root / "scripts" / RESTART_WORKER_SCRIPT


def run_subprocess_worker(
    work_dir: Path,
    run_id: str,
    *,
    stop_after_node: Optional[str] = None,
    src_paths: Optional[List[Path]] = None,
    python_executable: Optional[str] = None,
    invocation_marker: Optional[str] = None,
    bootstrap: bool = False,
    manifest_revision: int = 1,
) -> SubprocessRecord:
    """Launch ONE fresh subprocess that runs the synthetic worker.

    ``src_paths`` is the PYTHONPATH prefix (slice1 src + spike src).  The
    subprocess is always a fresh interpreter invocation, so its PID differs
    from the parent -- the boundary is observable via :attr:`SubprocessRecord.pid`.

    When ``bootstrap`` is True the subprocess creates the synthetic
    project/run/manifest before running (first process only).
    """
    script = _worker_script_path()
    if src_paths is None:
        raise ValueError("src_paths (PYTHONPATH prefixes) are required")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(str(p) for p in src_paths)
    argv = [
        python_executable or sys.executable,
        str(script),
        "--work-dir", str(work_dir),
        "--run-id", run_id,
    ]
    if stop_after_node is not None:
        argv += ["--stop-after-node", stop_after_node]
    if bootstrap:
        argv += ["--bootstrap"]
    argv += ["--manifest-revision", str(manifest_revision)]
    marker = invocation_marker or f"restart-{now_iso()}"
    argv += ["--invocation-marker", marker]
    started = now_iso()
    # Popen so the child PID is observable (subprocess.run hides it).  The
    # boundary is proven by distinct PIDs across the two-process test.
    proc = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    stdout, stderr = proc.communicate()
    return SubprocessRecord(
        pid=proc.pid,
        argv=argv,
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        invocation_marker=marker,
        started_at=started,
        finished_at=now_iso(),
    )


def bootstrap_run(
    store: Store,
    run_id: str,
    manifest_revision: int = 1,
) -> ExecutionManifest:
    """Create the synthetic project/revision/run + frozen manifest in the
    authoritative Store.  Returns the frozen manifest.
    """
    from mm_r1.domain import (
        ExecutionBasis,
        MonitoringRun,
        RunMode,
        SourceRevision,
    )

    project_id = "SYNTH-PROJECT-" + run_id
    revision_id = "SYNTH-REVISION-" + run_id
    store.create_project(project_id, "SYNTHETIC restart-harness project")
    store.add_source_revision(
        SourceRevision(
            revision_id=revision_id,
            project_id=project_id,
            source_type="listing",
            version="SYNTH-1",
            content_hash=content_hash({"synthetic": True, "revision": revision_id}),
        )
    )
    store.create_run(
        MonitoringRun(
            run_id=run_id,
            project_id=project_id,
            mode=RunMode.DAILY,
            data_cutoff="SYNTHETIC-CUTOFF-1",
            source_revision_id=revision_id,
            execution_basis=ExecutionBasis.FULL,
        )
    )
    manifest = synthetic_manifest(run_id, manifest_revision=manifest_revision)
    store.set_manifest(manifest)
    # re-read to get the committed revision assigned by the Store
    committed = store.get_manifest(run_id)
    assert committed is not None
    return committed
