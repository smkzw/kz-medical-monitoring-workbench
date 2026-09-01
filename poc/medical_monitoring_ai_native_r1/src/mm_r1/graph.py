"""Framework-neutral Graph IR with GraphPort / CheckpointPort boundaries.

Node types are fixed to the four Design v1.1 kinds
(``deterministic_service|ai_candidate|human_decision|projection``); node
statuses distinguish ``passed/reused/skipped/not_applicable/blocked/failed``.
No framework session/message types appear anywhere: a graph is a plain
dataclass structure that any candidate engine (LangGraph, Agent Framework,
Temporal) could implement behind :class:`GraphPort` / :class:`CheckpointPort`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional

from .domain import (
    DEPENDENCY_SATISFYING_STATUSES,
    TERMINAL_NODE_STATUSES,
    AnalysisState,
    ArtifactEnvelope,
    Checkpoint,
    CompletionGateError,
    ExecutionManifest,
    GraphValidationError,
    ManifestNode,
    NodeRun,
    NodeStatus,
    NodeTerminalError,
    NodeType,
    to_jsonable,
)

Handler = Callable[["NodeContext"], "NodeOutcome"]


# ---------------------------------------------------------------------------
# Graph IR
# ---------------------------------------------------------------------------

@dataclass
class GraphNode:
    node_id: str
    node_type: NodeType
    handler: str = ""
    description: str = ""
    mandatory: bool = True
    max_attempts: int = 1           # retry policy, frozen into the manifest
    artifact_required: bool = True  # state-only/QC nodes opt out explicitly


@dataclass
class GraphEdge:
    src: str
    dst: str
    condition: Optional[str] = None
    # condition = name of a context key that must be truthy for the edge to
    # carry a dependency.  Framework-neutral, serializable.


@dataclass
class Graph:
    graph_id: str
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> "Graph":
        if node.node_id in self.nodes:
            raise GraphValidationError(f"duplicate node id: {node.node_id}")
        if node.node_type not in NodeType:
            raise GraphValidationError(f"invalid node type: {node.node_type!r}")
        self.nodes[node.node_id] = node
        return self

    def add_edge(self, src: str, dst: str, condition: Optional[str] = None) -> "Graph":
        self.edges.append(GraphEdge(src=src, dst=dst, condition=condition))
        return self

    def validate(self) -> None:
        for e in self.edges:
            if e.src not in self.nodes:
                raise GraphValidationError(f"edge source not found: {e.src}")
            if e.dst not in self.nodes:
                raise GraphValidationError(f"edge destination not found: {e.dst}")
        # acyclicity (Kahn)
        indegree: Dict[str, int] = {n: 0 for n in self.nodes}
        for e in self.edges:
            indegree[e.dst] += 1
        queue = [n for n, d in indegree.items() if d == 0]
        visited = 0
        while queue:
            n = queue.pop()
            visited += 1
            for e in self.edges:
                if e.src == n:
                    indegree[e.dst] -= 1
                    if indegree[e.dst] == 0:
                        queue.append(e.dst)
        if visited != len(self.nodes):
            raise GraphValidationError("graph contains a cycle")

    def topological_order(self) -> List[str]:
        self.validate()
        indegree: Dict[str, int] = {n: 0 for n in self.nodes}
        out_edges: Dict[str, List[GraphEdge]] = {n: [] for n in self.nodes}
        for e in self.edges:
            indegree[e.dst] += 1
            out_edges[e.src].append(e)
        queue = sorted(n for n, d in indegree.items() if d == 0)
        order: List[str] = []
        while queue:
            n = queue.pop(0)
            order.append(n)
            for e in out_edges[n]:
                indegree[e.dst] -= 1
                if indegree[e.dst] == 0:
                    queue.append(e.dst)
                    queue.sort()
        return order

    def to_manifest(self, run_id: str, **freeze: Any) -> ExecutionManifest:
        """Derive an ExecutionManifest from the graph (the freeze record).

        All execution-relevant IR is frozen: graph_id (idempotency key
        prefix), edges with conditional semantics, per-node max_attempts and
        artifact_required.  ``depends_on`` is kept for compatibility.
        """
        freeze.pop("graph_id", None)
        return ExecutionManifest(
            run_id=run_id,
            graph_id=self.graph_id,
            nodes=[ManifestNode(node_id=n.node_id, node_type=n.node_type,
                                handler=n.handler, description=n.description,
                                mandatory=n.mandatory, max_attempts=n.max_attempts,
                                artifact_required=n.artifact_required,
                                depends_on=[e.src for e in self.edges if e.dst == n.node_id])
                   for n in self.nodes.values()],
            edges=[{"src": e.src, "dst": e.dst, "condition": e.condition}
                   for e in self.edges],
            **freeze,
        )

    @classmethod
    def from_manifest(cls, manifest: ExecutionManifest) -> "Graph":
        """Restore the graph EXACTLY as frozen: same graph_id, same conditional
        edges, same retry/artifact policy.  (Only manifests without a frozen
        graph_id -- legacy -- fall back to a derived id.)"""
        graph = Graph(graph_id=manifest.graph_id or f"manifest:{manifest.run_id}")
        deps: Dict[str, List[str]] = {}
        for n in manifest.nodes:
            graph.add_node(GraphNode(node_id=n.node_id, node_type=n.node_type,
                                     handler=n.handler, description=n.description,
                                     mandatory=n.mandatory, max_attempts=n.max_attempts,
                                     artifact_required=n.artifact_required))
            deps[n.node_id] = list(n.depends_on)
        if manifest.edges:
            for e in manifest.edges:
                graph.add_edge(e["src"], e["dst"], e.get("condition"))
        else:
            for dst, srcs in deps.items():
                for src in srcs:
                    graph.add_edge(src, dst)
        return graph


# ---------------------------------------------------------------------------
# Ports (framework-neutral boundaries)
# ---------------------------------------------------------------------------

class CheckpointPort(ABC):
    @abstractmethod
    def save_checkpoint(self, run_id: str, node_id: str,
                        state: Mapping[str, Any]) -> Checkpoint:
        ...

    @abstractmethod
    def load_checkpoint(self, run_id: str, node_id: str) -> Optional[Checkpoint]:
        ...

    @abstractmethod
    def list_checkpoints(self, run_id: str) -> List[Checkpoint]:
        ...


@dataclass
class NodeContext:
    """What a handler sees: provenance, the store, the checkpoint port and the
    shared run context.  No framework types."""
    run_id: str
    node_id: str
    node_type: NodeType
    store: Any                                   # mm_r1.store.Store
    checkpoint: CheckpointPort
    shared: Dict[str, Any]                       # merged outputs of dependencies

    def save_checkpoint(self, state: Mapping[str, Any]) -> Checkpoint:
        return self.checkpoint.save_checkpoint(self.run_id, self.node_id, state)

    def load_checkpoint(self) -> Optional[Checkpoint]:
        return self.checkpoint.load_checkpoint(self.run_id, self.node_id)


@dataclass
class NodeOutcome:
    status: NodeStatus                          # PASSED|SKIPPED|NOT_APPLICABLE|FAILED|BLOCKED
    artifact: Optional[ArtifactEnvelope] = None
    output: Optional[Mapping[str, Any]] = None  # merged into the run context
    reason: Optional[str] = None


@dataclass
class GraphNodeResult:
    run_id: str
    node_id: str
    status: NodeStatus
    reused: bool = False
    artifact_id: Optional[str] = None
    message: str = ""


@dataclass
class GraphRun:
    run_id: str
    graph_id: str
    status: str                                 # complete | blocked | failed
    node_results: List[GraphNodeResult] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


class GraphPort(ABC):
    """Framework-neutral execution boundary.

    A candidate engine (LangGraph / Agent Framework / Temporal adapter) would
    implement this interface while keeping the domain schema untouched.
    """

    @abstractmethod
    def run(self, graph: Graph, run_id: str,
            context: Optional[Mapping[str, Any]] = None,
            auto_finalize: bool = True) -> GraphRun:
        ...

    @abstractmethod
    def resume(self, run_id: str) -> GraphRun:
        """Continue an interrupted run from its frozen manifest + checkpoints."""
        ...

    @abstractmethod
    def replay(self, run_id: str) -> GraphRun:
        """Re-execute a completed run; every node must come back REUSED with
        identical artifacts (no duplicate side effects)."""
        ...


# ---------------------------------------------------------------------------
# Default local runner
# ---------------------------------------------------------------------------

class LocalGraphPort(GraphPort):
    """Reference GraphPort implementation over the SQLite Store.

    Idempotency key per node: ``g:<graph_id>:<node_id>:r<manifest_revision>``.
    A later manifest revision therefore re-executes nodes (new key), while a
    crash-and-resume with the same revision reuses committed results.
    """

    def __init__(self, store: Any, handlers: Mapping[str, Handler]) -> None:
        self._store = store
        self._handlers = dict(handlers)

    def register(self, name: str, handler: Handler) -> None:
        self._handlers[name] = handler

    def _check_registered(self, graph: Graph) -> None:
        missing = [n.node_id for n in graph.nodes.values()
                   if n.handler and n.handler not in self._handlers]
        if missing:
            raise GraphValidationError(f"no handler registered for nodes: {missing}")

    def _execute_node(self, graph: Graph, node_id: str, run_id: str,
                      rev: int, shared: Dict[str, Any]) -> GraphNodeResult:
        store = self._store
        node = graph.nodes[node_id]
        key = f"g:{graph.graph_id}:{node_id}:r{rev}"
        try:
            begun = store.begin_node_run(run_id, node_id, node.node_type, key)
        except NodeTerminalError as exc:
            # Terminal with a different key (e.g. manifest revision changed):
            # the committed result stands; re-execution would need a new run.
            existing = store.get_node_run(run_id, node_id)
            status = existing.status if existing is not None else NodeStatus.PENDING
            return GraphNodeResult(run_id=run_id, node_id=node_id, status=status,
                                   reused=True, artifact_id=existing.artifact_id
                                   if existing is not None else None, message=str(exc))
        if begun.status in TERMINAL_NODE_STATUSES:
            return GraphNodeResult(run_id=run_id, node_id=node_id, status=begun.status,
                                   reused=True, artifact_id=begun.artifact_id,
                                   message="reused from committed state")
        attempts = 0
        while True:
            attempts += 1
            outcome: Optional[NodeOutcome] = None
            error: Optional[str] = None
            try:
                ctx = NodeContext(run_id=run_id, node_id=node_id, node_type=node.node_type,
                                  store=store, checkpoint=store, shared=shared)
                outcome = self._handlers[node.handler](ctx)
                if outcome.status not in (NodeStatus.PASSED, NodeStatus.SKIPPED,
                                          NodeStatus.NOT_APPLICABLE, NodeStatus.FAILED,
                                          NodeStatus.BLOCKED):
                    raise GraphValidationError(f"handler returned illegal status {outcome.status}")
            except Exception as exc:  # handler crash -> failed attempt
                error = f"{type(exc).__name__}: {exc}"
                if attempts >= node.max_attempts:
                    store.complete_node_run(run_id, node_id, key, NodeStatus.FAILED,
                                            error=error[:2000], reason="handler_exception")
                    return GraphNodeResult(run_id=run_id, node_id=node_id,
                                           status=NodeStatus.FAILED, message=error[:300])
                # record the failed attempt, then reopen for retry (attempts
                # counter grows; the failure stays in the audit trail)
                store.complete_node_run(run_id, node_id, key, NodeStatus.FAILED,
                                        error=error[:2000], reason="handler_retry")
                store.begin_node_run(run_id, node_id, node.node_type, key)
                continue
            if outcome.status in (NodeStatus.FAILED, NodeStatus.BLOCKED):
                store.complete_node_run(run_id, node_id, key, outcome.status,
                                        error=error, reason=outcome.reason)
                return GraphNodeResult(run_id=run_id, node_id=node_id, status=outcome.status,
                                       message=outcome.reason or "")
            completed = store.complete_node_run(
                run_id, node_id, key, outcome.status,
                envelope=outcome.artifact, output=outcome.output, reason=outcome.reason,
            )
            if outcome.output:
                shared.update(outcome.output)
            return GraphNodeResult(run_id=run_id, node_id=node_id, status=completed.status,
                                   artifact_id=completed.artifact_id, message=outcome.reason or "")

    def run(self, graph: Graph, run_id: str,
            context: Optional[Mapping[str, Any]] = None,
            auto_finalize: bool = True) -> GraphRun:
        graph.validate()
        self._check_registered(graph)
        store = self._store
        run = store.get_run(run_id)
        rev = run.manifest_revision
        shared: Dict[str, Any] = dict(context or {})
        if run.analysis_state == AnalysisState.NOT_STARTED:
            store.update_run_state(run_id, analysis=AnalysisState.RUNNING, reason="graph run started")

        results: List[GraphNodeResult] = []
        any_failed = any_blocked = False
        for node_id in graph.topological_order():
            node = graph.nodes[node_id]
            existing = store.get_node_run(run_id, node_id)
            if existing is not None and existing.status in TERMINAL_NODE_STATUSES:
                results.append(GraphNodeResult(run_id=run_id, node_id=node_id,
                                               status=existing.status, reused=True,
                                               artifact_id=existing.artifact_id,
                                               message="reused from committed state"))
                if existing.output:
                    shared.update(existing.output)  # rebuild context for resume
                continue
            blocked_reason = self._dependencies_satisfied(graph, node_id, run_id, shared)
            if blocked_reason is not None:
                any_blocked = True
                key = f"g:{graph.graph_id}:{node_id}:r{rev}"
                try:
                    store.begin_node_run(run_id, node_id, node.node_type, key)
                except Exception:
                    pass
                store.complete_node_run(run_id, node_id, key, NodeStatus.BLOCKED,
                                        reason=blocked_reason)
                results.append(GraphNodeResult(run_id=run_id, node_id=node_id,
                                               status=NodeStatus.BLOCKED, message=blocked_reason))
                continue
            result = self._execute_node(graph, node_id, run_id, rev, shared)
            results.append(result)
            if result.status == NodeStatus.FAILED:
                any_failed = True
            elif result.status == NodeStatus.BLOCKED:
                any_blocked = True

        if any_blocked:
            store.update_run_state(run_id, analysis=AnalysisState.BLOCKED,
                                   reason="graph run blocked")
            return GraphRun(run_id=run_id, graph_id=graph.graph_id, status="blocked",
                            node_results=results, context=shared)
        if any_failed:
            store.update_run_state(run_id, analysis=AnalysisState.FAILED,
                                   reason="graph run failed")
            return GraphRun(run_id=run_id, graph_id=graph.graph_id, status="failed",
                            node_results=results, context=shared)
        if auto_finalize:
            store.complete_analysis(run_id, reason="graph run finalized")
        return GraphRun(run_id=run_id, graph_id=graph.graph_id, status="complete",
                        node_results=results, context=shared)

    def _dependencies_satisfied(self, graph: Graph, node_id: str, run_id: str,
                                shared: Mapping[str, Any]) -> Optional[str]:
        """None when the node may run; otherwise a blocking reason."""
        store = self._store
        for e in graph.edges:
            if e.dst != node_id:
                continue
            if e.condition is not None:
                if e.condition not in shared:
                    raise GraphValidationError(
                        f"edge condition key '{e.condition}' missing from run context"
                    )
                if not shared[e.condition]:
                    continue  # conditional edge skipped -> no dependency
            src_run = store.get_node_run(run_id, e.src)
            if src_run is None or src_run.status not in DEPENDENCY_SATISFYING_STATUSES:
                st = src_run.status.value if src_run else "no_run"
                return f"dependency '{e.src}' not satisfied for '{node_id}' ({st})"
        return None

    def _graph_from_store(self, run_id: str) -> Graph:
        manifest = self._store.get_manifest(run_id)
        if manifest is None:
            raise GraphValidationError(f"no manifest frozen for run {run_id}")
        return Graph.from_manifest(manifest)

    def resume(self, run_id: str) -> GraphRun:
        """Continue from the frozen manifest; committed nodes are reused."""
        graph = self._graph_from_store(run_id)
        return self.run(graph, run_id, auto_finalize=True)

    def replay(self, run_id: str) -> GraphRun:
        """Re-execute a completed run.  Every node must come back REUSED and
        committed artifacts must be byte-identical (idempotency guarantees no
        duplicate side effects)."""
        graph = self._graph_from_store(run_id)
        result = self.run(graph, run_id, auto_finalize=True)
        for nr in result.node_results:
            if not nr.reused:
                raise GraphValidationError(
                    f"replay re-executed node {nr.node_id} (status {nr.status.value}); "
                    "replay must only reuse committed results"
                )
        return result
