"""Framework-neutral conformance contract (worker_01-owned spike substrate).

Defines:
  * :class:`ConformanceContract` -- the immutable contract every candidate
    adapter (LangGraph / Microsoft Agent Framework) must satisfy.
  * :class:`ConformanceResult` -- the normalized, framework-neutral result
    produced by running a candidate against the contract.  It compares node
    status, reuse, manifest progress, artifact counts/hashes, work-event
    projection, and audit integrity, but never carries framework session /
    message types and is never domain authority.

This module imports only the accepted ``mm_r1`` public/domain ports by
read-only reference; it does not copy or edit slice1 and imports no candidate
framework.  All synthetic state is JSON-compatible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from mm_r1.domain import (
    ExecutionManifest,
    NodeStatus,
    TERMINAL_NODE_STATUSES,
    content_hash,
    now_iso,
    to_jsonable,
)
from mm_r1.graph import Graph


# ---------------------------------------------------------------------------
# Required work-event fields (execution context: Shared Contract And Required
# Evidence).  Every work event MUST carry exactly these fields; the
# WorkEventStore validates them on append.
# ---------------------------------------------------------------------------

REQUIRED_WORK_EVENT_FIELDS: Sequence[str] = (
    "event_id",
    "run_id",
    "manifest_revision",
    "sequence",
    "node_id",
    "work_unit_id",
    "phase",
    "status",
    "completed",
    "total",
    "current_detail",
    "created_at",
    "idempotency_key",
)

# Work-event phases (framework-neutral lifecycle).  ``node_begin`` / ``node_complete``
# are the two phases that drive progress.
PHASE_NODE_BEGIN = "node_begin"
PHASE_NODE_COMPLETE = "node_complete"

# Work-event statuses align with the domain NodeStatus vocabulary but are plain
# strings so the operational stream stays JSON-only and framework-neutral.
WORK_EVENT_STATUSES: Sequence[str] = tuple(s.value for s in NodeStatus)


@dataclass(frozen=True)
class ConformanceContract:
    """The immutable contract a candidate adapter must satisfy.

    A contract binds a deterministic frozen :class:`~mm_r1.domain.ExecutionManifest`
    (the exact-progress source of truth) to the work-event stream and the
    authoritative slice1 Store.  Candidates do not own or mutate the contract;
    they produce a :class:`ConformanceResult` by running the manifest through
    their engine behind the accepted ``GraphPort`` boundary.
    """
    run_id: str
    manifest_revision: int
    total_units: int
    graph_id: str
    node_ids: Tuple[str, ...]
    manifest_fingerprint: str

    @classmethod
    def from_manifest(cls, manifest: ExecutionManifest) -> "ConformanceContract":
        """Derive the exact-progress contract from a frozen manifest.

        ``total_units`` is derived exclusively from the frozen manifest nodes
        (``manifest.total_units()``), never from adapter-reported counts.
        ``manifest_fingerprint`` is the canonical content hash of the manifest
        so a different run/manifest with the same revision and node count but
        different graph_id, node ordering or content fails closed.
        """
        return cls(
            run_id=manifest.run_id,
            manifest_revision=int(manifest.revision),
            total_units=int(manifest.total_units()),
            graph_id=str(manifest.graph_id),
            node_ids=tuple(manifest.node_ids()),
            manifest_fingerprint=content_hash(to_jsonable(manifest)),
        )

    def expected_progress(self, completed: int) -> Dict[str, Any]:
        """Normalized progress projection for ``completed`` terminal nodes.

        ``completed``/``total`` are always derived from the frozen manifest;
        the contract rejects ``completed > total_units`` as well as negatives.
        """
        if completed < 0:
            raise ValueError("completed must be non-negative")
        if completed > self.total_units:
            raise ValueError(
                f"completed {completed} exceeds manifest total {self.total_units}"
            )
        return {
            "completed": int(completed),
            "total": self.total_units,
        }


# ---------------------------------------------------------------------------
# Normalized per-node result (framework-neutral)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NodeConformance:
    node_id: str
    status: str          # NodeStatus value
    reused: bool
    artifact_id: Optional[str]
    artifact_content_hash: Optional[str]
    message: str


@dataclass(frozen=True)
class WorkEventProjection:
    """Framework-neutral projection of the work-event stream for comparison.

    Carries only ordering, dedup, exact progress and the idempotency-key set --
    never the raw event payload, so no framework/content authority leaks in.
    """

    count: int
    distinct_idempotency_keys: int
    sequences: List[int]
    completed: int
    total: int
    statuses: List[str]


@dataclass
class ConformanceResult:
    """Normalized, framework-neutral result of one candidate run.

    Built from the authoritative slice1 Store + the separate work-event store;
    candidates never construct it directly with framework types.  Two
    candidates that produce the same :class:`ConformanceResult` are
    conformance-equivalent for the medical monitoring R1 spike.
    """

    run_id: str
    manifest_revision: int
    graph_id: str
    status: str                                 # complete | blocked | failed
    nodes: List[NodeConformance] = field(default_factory=list)
    progress: Dict[str, int] = field(default_factory=dict)
    artifact_count: int = 0
    artifact_hashes: List[str] = field(default_factory=list)
    work_event_projection: Optional[WorkEventProjection] = None
    audit_ok: bool = True
    audit_count: int = 0
    produced_at: str = field(default_factory=now_iso)

    def conformance_key(self) -> str:
        """Stable content hash of the conformance-significant fields.

        Two candidates with the same :meth:`conformance_key` produce the same
        authoritative state shape and the same normalized work-event stream.
        Framework-internal identity (PID, timestamps, checkpoint file paths)
        is deliberately excluded.
        """
        payload = {
            "run_id": self.run_id,
            "manifest_revision": self.manifest_revision,
            "status": self.status,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "status": n.status,
                    "reused": n.reused,
                    "artifact_content_hash": n.artifact_content_hash,
                }
                for n in sorted(self.nodes, key=lambda x: x.node_id)
            ],
            "progress": {
                "completed": self.progress.get("completed", 0),
                "total": self.progress.get("total", 0),
            },
            "artifact_count": self.artifact_count,
            "artifact_hashes": sorted(self.artifact_hashes),
            "work_events": (
                None
                if self.work_event_projection is None
                else {
                    "count": self.work_event_projection.count,
                    "distinct_idempotency_keys":
                        self.work_event_projection.distinct_idempotency_keys,
                    "completed": self.work_event_projection.completed,
                    "total": self.work_event_projection.total,
                    "statuses": self.work_event_projection.statuses,
                }
            ),
            "audit_ok": self.audit_ok,
        }
        return content_hash(payload)


def is_completed_terminal(status: Any) -> bool:
    """True for a terminal NodeStatus that counts as completed progress.

    Mirrors :func:`mm_r1.store.Store.manifest_progress` (terminal statuses).
    """
    return _coerce_status(status) in TERMINAL_NODE_STATUSES


def _coerce_status(status: Any) -> NodeStatus:
    if isinstance(status, NodeStatus):
        return status
    return NodeStatus(str(status))


# ---------------------------------------------------------------------------
# Exact Graph-IR comparator (shared by both adapters' public run methods)
# ---------------------------------------------------------------------------

# Execution-relevant GraphNode fields that must match exactly (ordered nodes).
GRAPH_IR_NODE_FIELDS: Sequence[str] = (
    "node_type",
    "handler",
    "description",
    "mandatory",
    "max_attempts",
    "artifact_required",
)


class GraphIRMismatchError(ValueError):
    """Supplied Graph IR does not exactly match the frozen expected Graph.

    Raised before any checkpoint / work-event / Store mutation so an altered
    edge order, node field, or graph_id cannot drive a commit.
    """


def assert_exact_graph_ir(supplied: Graph, expected: Graph) -> None:
    """Fail closed unless ``supplied`` is an exact Graph-IR match of ``expected``.

    Compares:
      * ``graph_id``
      * ordered node ids (insertion / freeze order)
      * every execution-relevant node field in :data:`GRAPH_IR_NODE_FIELDS`
      * ordered edges including conditional ``condition`` values

    Both public adapter ``run`` methods MUST call this against
    ``Graph.from_manifest(frozen_manifest)`` before any checkpoint, event, or
    Store mutation.
    """
    if supplied.graph_id != expected.graph_id:
        raise GraphIRMismatchError(
            f"graph_id mismatch: supplied {supplied.graph_id!r} != "
            f"expected {expected.graph_id!r}"
        )

    supplied_ids = list(supplied.nodes.keys())
    expected_ids = list(expected.nodes.keys())
    if supplied_ids != expected_ids:
        raise GraphIRMismatchError(
            f"ordered node ids mismatch: supplied {supplied_ids} != "
            f"expected {expected_ids}"
        )

    for nid in expected_ids:
        s_node = supplied.nodes[nid]
        e_node = expected.nodes[nid]
        for field_name in GRAPH_IR_NODE_FIELDS:
            s_val = getattr(s_node, field_name)
            e_val = getattr(e_node, field_name)
            if s_val != e_val:
                raise GraphIRMismatchError(
                    f"node {nid!r} field {field_name} mismatch: "
                    f"supplied {s_val!r} != expected {e_val!r}"
                )

    supplied_edges = [
        (e.src, e.dst, e.condition) for e in supplied.edges
    ]
    expected_edges = [
        (e.src, e.dst, e.condition) for e in expected.edges
    ]
    if supplied_edges != expected_edges:
        raise GraphIRMismatchError(
            f"ordered/conditional edges mismatch: supplied {supplied_edges} != "
            f"expected {expected_edges}"
        )
