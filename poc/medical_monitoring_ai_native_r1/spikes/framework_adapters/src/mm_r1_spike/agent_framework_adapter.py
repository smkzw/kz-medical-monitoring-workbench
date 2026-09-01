"""Microsoft Agent Framework Core 1.13.0 adapter (worker_03-owned spike).

This is a real accepted-``GraphPort``-compatible adapter that drives the
synthetic three-node manifest through Microsoft Agent Framework Core's
deterministic workflow/executor primitives (``WorkflowBuilder``, ``Executor``,
``@handler``, the Pregel-style runner/superstep loop, and the
``CheckpointStorage`` protocol).  It is NOT a wrapper around the slice1
``LocalGraphPort``.

followup_01 repairs (Codex-reproduced hard-boundary defects):
  1. The framework's ``FileCheckpointStorage`` serializes checkpoint state with
     pickle embedded as base64 (``_checkpoint_encoding.py``).  The task contract
     says: no pickle; only JSON-compatible synthetic state.  This adapter
     replaces it with a spike-owned ``StrictJsonCheckpointStorage`` that persists
     a strict, versioned JSON schema and reconstructs only the exact
     allowlisted Agent Framework checkpoint/message dataclasses needed by this
     deterministic synthetic workflow.  It NEVER imports/calls pickle or
     executes arbitrary type metadata.
  2. ``WorkflowCheckpoint`` is not tied to a workflow instance, so a constant
     ``WORKFLOW_NAME`` lets ``get_latest()`` select another run with the same
     topology.  This adapter binds the checkpoint namespace AND metadata to the
     exact ``run_id``, manifest revision, graph id, ordered node ids, and
     manifest fingerprint, and validates every binding before any domain/event
     mutation.  Cross-run/stale/corrupt-latest recovery fails closed with no
     silent fallback to an older valid file.

Conformance contract (execution context: Shared Contract And Required Evidence):
  * consumes the same frozen manifest/Graph IR as the framework-neutral
    substrate and worker_02's LangGraph adapter;
  * keeps framework checkpoint/session/message state SEPARATE from the
    authoritative slice1 Store (separate checkpoint dir per run);
  * commits domain effects ONLY through accepted Store/handler contracts
    (``begin_node_run`` / ``complete_node_run``) and emits structured work
    events ONLY through ``WorkEventStore.append``;
  * proves fresh-process resume: process A stops after node 1 via the
    framework's own ``max_iterations`` boundary; a freshly launched process B
    restores the framework checkpoint and the authoritative Store and completes
    the remaining nodes.

Framework symbols exercised (all from ``agent_framework`` 1.13.0):
  ``Workflow``, ``WorkflowBuilder``, ``Executor``, ``@handler``,
  ``WorkflowContext``, ``CheckpointStorage`` (protocol), ``WorkflowCheckpoint``,
  ``WorkflowCheckpointException``, ``WorkflowConvergenceException``,
  ``WorkflowEvent``, ``WorkflowRunResult``, ``WorkflowRunState``,
  ``WorkflowMessage``, ``MessageType``, ``RunnerImpl`` (runner/superstep loop).

No chat agents, providers, Foundry, credentials, or network clients are
instantiated.  Deterministic executors only.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from mm_r1.domain import (
    ExecutionManifest,
    NodeStatus,
    TERMINAL_NODE_STATUSES,
    content_hash,
    now_iso,
)
from mm_r1.graph import (
    Graph,
    GraphNodeResult,
    GraphPort,
    GraphRun,
    NodeContext,
)

from .contract import (
    ConformanceContract,
    ConformanceResult,
    NodeConformance,
    PHASE_NODE_BEGIN,
    PHASE_NODE_COMPLETE,
    WorkEventProjection,
    assert_exact_graph_ir,
    is_completed_terminal,
)
from .restart_harness import (
    SYNTH_OUTPUT_KEY,
    synth_handler,
)
from .work_events import WorkEventStore

# Framework import is deferred to module body so a missing package produces a
# clear ImportError at adapter construction time rather than at import time of
# this module (the substrate modules must remain importable without the
# framework venv).
try:
    import agent_framework as af  # type: ignore[import-not-found]
    from agent_framework import (  # type: ignore[import-not-found]
        Executor,
        WorkflowBuilder,
        WorkflowCheckpoint,
        WorkflowCheckpointException,
        WorkflowConvergenceException,
        WorkflowContext,
        WorkflowRunResult,
        handler,
    )
    from agent_framework._workflows._checkpoint import (  # type: ignore[import-not-found]
        CheckpointID,
    )
    from agent_framework._workflows._runner_context import (  # type: ignore[import-not-found]
        MessageType,
        WorkflowMessage,
    )
except ImportError as exc:  # pragma: no cover - exercised only without the venv
    raise ImportError(
        "agent_framework (agent-framework-core==1.13.0) is required for the "
        "Agent Framework adapter; it lives only in the disposable venv "
        "/tmp/mm_r1_slice2_agentframework.r44ruW/venv"
    ) from exc


# ---------------------------------------------------------------------------
# Package version probe (evidence for the report)
# ---------------------------------------------------------------------------

FRAMEWORK_PACKAGE = "agent-framework-core"
FRAMEWORK_VERSION: str = getattr(af, "__version__", "1.13.0")

# Strict-JSON checkpoint schema version (spike-owned, independent of the
# framework's internal checkpoint version field).
CHECKPOINT_SCHEMA_VERSION = "mm-r1-spike-json-v1"


# ===========================================================================
# StrictJsonCheckpointStorage — spike-owned, no pickle, no opaque type metadata
# ===========================================================================


class CheckpointIdentityError(RuntimeError):
    """Raised fail-closed when a checkpoint's run/graph binding is
    missing/mismatched/corrupt, before any domain/event mutation."""


class StrictJsonCheckpointStorage:
    """Spike-owned ``CheckpointStorage`` protocol implementation.

    Persists ``WorkflowCheckpoint`` objects as STRICT JSON (versioned schema)
    and reconstructs only the exact allowlisted Agent Framework dataclasses
    needed by this deterministic synthetic workflow:
      * ``WorkflowCheckpoint`` (via its dataclass fields)
      * ``WorkflowMessage`` (via its public ``from_dict``/``to_dict``)

    It NEVER imports/calls ``pickle``, NEVER executes arbitrary type metadata,
    and NEVER decodes base64-pickled payloads.  Every persisted value is plain
    JSON (str/int/float/bool/None/list/dict).

    Atomicity: writes go to a unique ``.tmp`` file, then ``flush`` + ``fsync``
    the file, ``os.replace`` into place, and best-effort ``fsync`` the parent
    directory.  A crashed write leaves at most an orphan ``.tmp`` file.

    Identity: each instance is scoped to one run via ``checkpoint_namespace``,
    which encodes the run_id, manifest revision, graph id, and manifest
    fingerprint.  ``list_checkpoints``/``get_latest`` only ever consider files
    whose persisted ``_namespace`` matches, so two runs with identical topology
    cannot cross-select.  ``load`` additionally validates the full identity
    binding.
    """

    def __init__(
        self,
        storage_path: Path,
        *,
        checkpoint_namespace: str,
        run_id: str,
        manifest_revision: int,
        graph_id: str,
        node_ids: Sequence[str],
        manifest_fingerprint: str,
    ) -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.checkpoint_namespace = checkpoint_namespace
        self._identity = {
            "run_id": run_id,
            "manifest_revision": int(manifest_revision),
            "graph_id": graph_id,
            "node_ids": list(node_ids),
            "manifest_fingerprint": manifest_fingerprint,
            "namespace": checkpoint_namespace,
        }

    # ---------------------------------------------------------- path safety

    def _validate_file_path(self, checkpoint_id: CheckpointID) -> Path:
        """Resolve a checkpoint ID to a path inside the storage dir only."""
        file_path = (self.storage_path / f"{checkpoint_id}.json").resolve()
        if not file_path.is_relative_to(self.storage_path.resolve()):
            raise WorkflowCheckpointException(f"Invalid checkpoint ID: {checkpoint_id}")
        return file_path

    # ---------------------------------------------------------- message codec

    @staticmethod
    def _encode_message(wm: WorkflowMessage, _seen: Optional[set]) -> Dict[str, Any]:
        """``WorkflowMessage`` -> plain JSON dict (NO pickle).

        Every field value is routed through the strict codec
        (:func:`_strict_json`) so unsupported objects, non-string keys,
        NaN/Infinity, and recursive structures are rejected with a checkpoint
        exception BEFORE any file is written.

        This deterministic synthetic workflow never calls ``request_info``;
        if ``original_request_info_event`` is non-None we fail closed (this
        spike does not implement the ``WorkflowEvent`` codec) rather than
        silently dropping it.
        """
        if wm.original_request_info_event is not None:
            raise WorkflowCheckpointException(
                "checkpoint message has non-None original_request_info_event; "
                "this spike does not implement the WorkflowEvent codec for "
                "request-info messages"
            )
        return {
            "data": _strict_json(wm.data, _seen),
            "source_id": _strict_json(wm.source_id, _seen),
            "target_id": _strict_json(wm.target_id, _seen),
            "type": _strict_json(wm.type.value, _seen),
            "trace_contexts": _strict_json(wm.trace_contexts, _seen),
            "source_span_ids": _strict_json(wm.source_span_ids, _seen),
            "original_request_info_event": None,
        }

    @staticmethod
    def _decode_message(d: Mapping[str, Any]) -> WorkflowMessage:
        """Plain JSON dict -> ``WorkflowMessage`` via its public ``from_dict``.

        Fails closed on missing required fields, an unknown ``MessageType``,
        or a non-None ``original_request_info_event`` (this spike does not
        implement the ``WorkflowEvent`` codec).
        """
        if not isinstance(d, Mapping):
            raise WorkflowCheckpointException(
                f"checkpoint message is not a JSON object: {type(d).__name__}"
            )
        if "data" not in d or "source_id" not in d:
            raise WorkflowCheckpointException(
                "checkpoint message missing required data/source_id fields"
            )
        if d.get("original_request_info_event") is not None:
            raise WorkflowCheckpointException(
                "checkpoint message carries original_request_info_event; "
                "this spike does not implement the WorkflowEvent codec"
            )
        type_str = str(d.get("type", "standard"))
        try:
            MessageType(type_str)  # validate before reconstruction
        except ValueError as exc:
            raise WorkflowCheckpointException(
                f"checkpoint message has unknown MessageType: {type_str!r}"
            ) from exc
        return WorkflowMessage.from_dict(dict(d))

    # ---------------------------------------------------------- checkpoint codec

    def _encode_checkpoint(self, cp: WorkflowCheckpoint) -> Dict[str, Any]:
        """``WorkflowCheckpoint`` -> strict JSON dict (NO pickle).

        Every persisted value is routed through the strict codec
        (:func:`_strict_json`) so unsupported objects, non-string keys,
        NaN/Infinity, and recursive structures are rejected with a checkpoint
        exception BEFORE any file is written.

        If ``pending_request_info_events`` is non-empty we fail closed (this
        spike does not implement the ``WorkflowEvent`` codec) rather than
        silently dropping it.
        """
        if cp.pending_request_info_events:
            raise WorkflowCheckpointException(
                f"checkpoint has {len(cp.pending_request_info_events)} pending "
                "request_info event(s); this spike does not implement the "
                "WorkflowEvent codec for request-info messages"
            )
        _seen: set = set()
        return {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "namespace": _strict_json(self.checkpoint_namespace, _seen),
            "identity": _strict_json(dict(self._identity), _seen),
            "workflow_name": _strict_json(cp.workflow_name, _seen),
            "graph_signature_hash": _strict_json(cp.graph_signature_hash, _seen),
            "checkpoint_id": _strict_json(cp.checkpoint_id, _seen),
            "previous_checkpoint_id": _strict_json(cp.previous_checkpoint_id, _seen),
            "timestamp": _strict_json(cp.timestamp, _seen),
            "messages": _strict_json(
                {src: [self._encode_message(m, _seen) for m in msgs]
                 for src, msgs in cp.messages.items()},
                _seen,
            ),
            "state": _strict_json(cp.state, _seen) if cp.state is not None else {},
            "pending_request_info_events": {},
            "iteration_count": _strict_json(int(cp.iteration_count), _seen),
            "metadata": _strict_json(dict(cp.metadata) if cp.metadata else {}, _seen),
            "version": _strict_json(cp.version, _seen),
        }

    def _decode_checkpoint(self, d: Mapping[str, Any]) -> WorkflowCheckpoint:
        """Strict JSON dict -> ``WorkflowCheckpoint`` with identity validation."""
        if not isinstance(d, Mapping):
            raise CheckpointIdentityError("checkpoint root is not a JSON object")
        # Schema gate: reject anything we did not write.
        sv = d.get("schema_version")
        if sv != CHECKPOINT_SCHEMA_VERSION:
            raise CheckpointIdentityError(
                f"checkpoint schema_version mismatch: {sv!r} != {CHECKPOINT_SCHEMA_VERSION!r}"
            )
        # Identity gate: the persisted identity must match exactly.
        stored_identity = d.get("identity")
        if not isinstance(stored_identity, Mapping):
            raise CheckpointIdentityError("checkpoint missing identity block")
        self._verify_identity(stored_identity)
        # Namespace gate (defense-in-depth).
        if d.get("namespace") != self.checkpoint_namespace:
            raise CheckpointIdentityError(
                f"checkpoint namespace mismatch: {d.get('namespace')!r} != "
                f"{self.checkpoint_namespace!r}"
            )
        # Reconstruct messages (the only non-primitive nested values).
        raw_messages = d.get("messages", {})
        if not isinstance(raw_messages, Mapping):
            raise CheckpointIdentityError("checkpoint messages is not a JSON object")
        messages: Dict[str, List[WorkflowMessage]] = {}
        for src, msgs in raw_messages.items():
            if not isinstance(msgs, list):
                raise CheckpointIdentityError(
                    f"checkpoint messages[{src!r}] is not a JSON array"
                )
            messages[str(src)] = [self._decode_message(m) for m in msgs]
        # Reconstruct the WorkflowCheckpoint from primitives.
        return WorkflowCheckpoint(
            workflow_name=str(d["workflow_name"]),
            graph_signature_hash=str(d["graph_signature_hash"]),
            checkpoint_id=str(d["checkpoint_id"]),
            previous_checkpoint_id=d.get("previous_checkpoint_id"),
            timestamp=str(d["timestamp"]),
            messages=messages,
            state=dict(d.get("state", {})),
            pending_request_info_events={},
            iteration_count=int(d.get("iteration_count", 0)),
            metadata=dict(d.get("metadata", {})),
            version=str(d.get("version", "1.0")),
        )

    def _verify_identity(self, stored: Mapping[str, Any]) -> None:
        """Fail closed if the stored identity binding does not match exactly."""
        checks = [
            ("run_id", stored.get("run_id"), self._identity["run_id"]),
            ("manifest_revision", _to_int(stored.get("manifest_revision")),
             self._identity["manifest_revision"]),
            ("graph_id", stored.get("graph_id"), self._identity["graph_id"]),
            ("node_ids", list(stored.get("node_ids", [])), self._identity["node_ids"]),
            ("manifest_fingerprint", stored.get("manifest_fingerprint"),
             self._identity["manifest_fingerprint"]),
            ("namespace", stored.get("namespace"), self.checkpoint_namespace),
        ]
        for name, got, want in checks:
            if got != want:
                raise CheckpointIdentityError(
                    f"checkpoint {name} mismatch: {got!r} != {want!r}"
                )

    # ---------------------------------------------------------- CheckpointStorage protocol

    async def save(self, checkpoint: WorkflowCheckpoint) -> CheckpointID:
        path = self._validate_file_path(checkpoint.checkpoint_id)
        # Encode + strictly validate the ENTIRE payload BEFORE touching disk,
        # so a codec rejection leaves zero final file and zero .tmp residue.
        payload = self._encode_checkpoint(checkpoint)
        # Double-check: the payload must be re-encodable as strict JSON with
        # NaN/Infinity rejected (json.dump's allow_nan=True would otherwise
        # silently emit invalid JSON tokens).
        serialized = json.dumps(payload, ensure_ascii=False)

        def _write_atomic() -> None:
            # Genuinely unique temp file (mkstemp), not a deterministic name.
            fd, tmp_str = tempfile.mkstemp(
                prefix=f".{checkpoint.checkpoint_id}.", suffix=".json.tmp",
                dir=str(self.storage_path),
            )
            tmp_path = Path(tmp_str)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(serialized)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, path)
                _fsync_dir(self.storage_path)
            except BaseException:
                # Clean up the orphaned temp file on ANY failure.
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
                raise

        await asyncio.to_thread(_write_atomic)
        return checkpoint.checkpoint_id

    async def load(self, checkpoint_id: CheckpointID) -> WorkflowCheckpoint:
        path = self._validate_file_path(checkpoint_id)
        if not path.exists():
            raise WorkflowCheckpointException(
                f"No checkpoint found with ID {checkpoint_id}"
            )

        def _read() -> Dict[str, Any]:
            with open(path, encoding="utf-8") as f:
                return json.load(f)

        raw = await asyncio.to_thread(_read)
        # Full identity + schema validation on every load; no silent fallback.
        return self._decode_checkpoint(raw)

    async def list_checkpoints(self, *, workflow_name: str) -> List[WorkflowCheckpoint]:
        """List checkpoints for a workflow name.

        NOTE: this storage is per-run (one namespace per directory), so
        ``workflow_name`` is matched but the namespace/identity binding is the
        primary selector.  A corrupt/unreadable file raises (no swallow, no
        silent fallback to older files).
        """

        def _list() -> List[WorkflowCheckpoint]:
            out: List[WorkflowCheckpoint] = []
            for file_path in sorted(self.storage_path.glob("*.json")):
                with open(file_path, encoding="utf-8") as f:
                    d = json.load(f)
                # Filter by namespace first (cheap), then workflow_name, then
                # full decode (which validates identity).  A file that fails
                # JSON parse or identity validation is a corruption -> raise.
                if d.get("namespace") != self.checkpoint_namespace:
                    continue
                if d.get("workflow_name") != workflow_name:
                    continue
                out.append(self._decode_checkpoint(d))
            return out

        return await asyncio.to_thread(_list)

    async def delete(self, checkpoint_id: CheckpointID) -> bool:
        path = self._validate_file_path(checkpoint_id)

        def _delete() -> bool:
            if path.exists():
                path.unlink()
                return True
            return False

        return await asyncio.to_thread(_delete)

    async def get_latest(self, *, workflow_name: str) -> Optional[WorkflowCheckpoint]:
        checkpoints = await self.list_checkpoints(workflow_name=workflow_name)
        if not checkpoints:
            return None
        return max(checkpoints, key=lambda cp: datetime.fromisoformat(cp.timestamp))

    async def list_checkpoint_ids(self, *, workflow_name: str) -> List[CheckpointID]:
        checkpoints = await self.list_checkpoints(workflow_name=workflow_name)
        return [cp.checkpoint_id for cp in checkpoints]


# ---------------------------------------------------------------------------
# Strict-JSON codec: rejects unsupported values, non-string keys, NaN/Infinity,
# and recursive/cyclic structures BEFORE any file is written.
# ---------------------------------------------------------------------------


_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))


def _strict_json(v: Any, seen: Optional[set] = None) -> Any:
    """Recursively coerce ``v`` to a strict JSON-native value or raise.

    Accepts ONLY:
      * ``None``, ``str``, ``bool``;
      * finite ``int`` / ``float`` (NaN, Infinity, -Infinity are rejected);
      * ``dict`` / ``Mapping`` with ALL-STRING keys;
      * ``list`` / ``tuple``.

    Rejects (raises ``WorkflowCheckpointException``):
      * any other object type (opaque classes, callables, bytes, sets, ...);
      * non-string mapping keys;
      * NaN / Infinity floats;
      * recursive/cyclic container structures.

    ``seen`` tracks the set of container ``id()``s on the current path so a
    cycle is detected before Python's recursion limit.  Callers should pass
    ``None`` (or an empty set) for top-level invocation.
    """
    if v is None:
        return None
    # bool is a subclass of int; check before int to keep True/False as-is.
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        if not math.isfinite(v):
            raise WorkflowCheckpointException(
                f"checkpoint value is non-finite float: {v!r}"
            )
        return v
    if isinstance(v, (list, tuple)):
        if seen is None:
            seen = set()
        oid = id(v)
        if oid in seen:
            raise WorkflowCheckpointException(
                "checkpoint value is a recursive/cyclic structure"
            )
        seen.add(oid)
        try:
            return [_strict_json(item, seen) for item in v]
        finally:
            seen.discard(oid)
    if isinstance(v, Mapping):
        if seen is None:
            seen = set()
        oid = id(v)
        if oid in seen:
            raise WorkflowCheckpointException(
                "checkpoint value is a recursive/cyclic structure"
            )
        seen.add(oid)
        try:
            result: Dict[str, Any] = {}
            for k, val in v.items():
                if not isinstance(k, str):
                    raise WorkflowCheckpointException(
                        f"checkpoint mapping has non-string key: {type(k).__name__} = {k!r}"
                    )
                result[k] = _strict_json(val, seen)
            return result
        finally:
            seen.discard(oid)
    raise WorkflowCheckpointException(
        f"checkpoint value is not JSON-serializable: {type(v).__name__} = {v!r}"
    )


def _to_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    return int(v)


def _fsync_dir(path: Path) -> None:
    """Best-effort fsync of a directory for atomic-replace durability."""
    try:
        dfd = os.open(str(path), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass


# ===========================================================================
# Deterministic executor: one per synthetic manifest node
# ===========================================================================


class _SyntheticNodeExecutor(Executor):
    """Agent Framework executor wrapping the slice1 synthetic node handler.

    Receives the inbound message (a plain ``str`` seed carrying the run id and
    accumulated node output), runs the accepted ``synth_handler`` against a real
    ``NodeContext`` bound to the authoritative Store, emits structured work
    events, and forwards the output to the next executor via
    ``ctx.send_message``.  No model/provider calls.
    """

    def __init__(
        self,
        node_id: str,
        *,
        port: "AgentFrameworkWorkflowPort",
    ) -> None:
        super().__init__(id=node_id)
        self._node_id = node_id
        self._port = port

    @handler
    async def process(self, message: str, ctx: WorkflowContext[str]) -> None:
        """Run one synthetic node through the authoritative Store contracts."""
        node_id = self._node_id
        port = self._port
        store = port._store
        manifest = port._manifest
        assert manifest is not None
        rev = manifest.revision
        key = f"g:{manifest.graph_id}:{node_id}:r{rev}"

        existing = store.get_node_run(manifest.run_id, node_id)
        is_terminal = (
            existing is not None and existing.status in TERMINAL_NODE_STATUSES
        )

        if is_terminal:
            # Reused terminal node: do NOT re-emit node_complete (same
            # idempotency key with advanced progress would be divergent).  The
            # authoritative Store already holds the committed result; we only
            # forward the output so downstream executors can run.
            output = (
                existing.output.get(SYNTH_OUTPUT_KEY, {}) if existing and existing.output else {}
            )
            port._record_reused(node_id, existing.status.value)
            await ctx.send_message(_seed_message(manifest.run_id, output))
            return

        # node_begin work event (only when actually starting)
        port._emit_work_event(node_id, PHASE_NODE_BEGIN, node_id,
                              status=NodeStatus.RUNNING.value)

        store.begin_node_run(manifest.run_id, node_id,
                             manifest.nodes[0].node_type, key)
        node_ctx = NodeContext(
            run_id=manifest.run_id,
            node_id=node_id,
            node_type=manifest.nodes[0].node_type,
            store=store,
            checkpoint=store,
            shared={SYNTH_OUTPUT_KEY: port._outputs},
        )
        outcome = synth_handler(node_id, node_ctx)
        completed = store.complete_node_run(
            manifest.run_id, node_id, key, outcome.status, output=outcome.output
        )
        node_output = (
            outcome.output.get(SYNTH_OUTPUT_KEY, {}) if outcome.output else {}
        )
        port._outputs[node_id] = node_output

        port._emit_work_event(node_id, PHASE_NODE_COMPLETE, node_id,
                              status=completed.status.value)

        await ctx.send_message(_seed_message(manifest.run_id, node_output))


def _seed_message(run_id: str, output: Mapping[str, Any]) -> str:
    """Encode the run id + accumulated node output into the plain-str message
    type that the linear workflow carries between executors.

    The payload is JSON-only synthetic state.  It is operational plumbing for
    the executor chain, never domain authority.
    """
    return json.dumps({"run_id": run_id, "output": dict(output)}, sort_keys=True)


# ---------------------------------------------------------------------------
# Checkpoint identity helpers (JSON files on disk, separate operational dir)
# ---------------------------------------------------------------------------


def checkpoint_dir(work_dir: Path) -> Path:
    """Directory holding the strict-JSON checkpoint files (separate operational
    persistence, never inside the authoritative Store or artifact dir)."""
    d = Path(work_dir) / "af_checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d


def checkpoint_namespace(
    run_id: str,
    manifest_revision: int,
    graph_id: str,
    node_ids: Sequence[str],
    manifest_fingerprint: str,
) -> str:
    """A stable, collision-resistant namespace binding a checkpoint to one run.

    Encodes run_id, manifest revision, graph id, ordered node ids, and manifest
    fingerprint so two runs with identical topology but different run_id (or a
    different manifest) get disjoint checkpoint namespaces and cannot
    cross-select via ``get_latest``.
    """
    return content_hash({
        "run_id": run_id,
        "manifest_revision": int(manifest_revision),
        "graph_id": graph_id,
        "node_ids": list(node_ids),
        "manifest_fingerprint": manifest_fingerprint,
    })


# ===========================================================================
# The accepted GraphPort adapter
# ===========================================================================


class AgentFrameworkWorkflowPort(GraphPort):
    """Accepted ``GraphPort`` backed by Microsoft Agent Framework workflows.

    The adapter builds a real Agent Framework ``Workflow`` (linear chain of
    ``_SyntheticNodeExecutor`` instances connected by edges) with the
    spike-owned ``StrictJsonCheckpointStorage``.  ``run`` executes to completion
    or to an injected ``max_iterations`` boundary; ``resume`` restores from the
    latest persisted framework checkpoint in a fresh process; ``replay`` proves
    idempotent reuse of committed terminal nodes.

    Framework state (workflow instance, checkpoint files, executor state) is
    kept separate from the authoritative slice1 Store.  Domain effects are
    committed only through accepted Store/handler contracts.
    """

    WORKFLOW_NAME = "mm-r1-spike-af"

    def __init__(
        self,
        store: Any,
        events: WorkEventStore,
        contract: ConformanceContract,
        work_dir: Path,
        *,
        run_id: str,
        max_iterations: int = 100,
    ) -> None:
        # C-AF-CTOR: reject mismatched constructor identity BEFORE creating
        # checkpoint directories or storage.  run_id must equal contract.run_id,
        # and the contract must match the current frozen manifest fingerprint /
        # revision / graph / ordered node ids when a manifest is already frozen.
        if run_id != contract.run_id:
            raise CheckpointIdentityError(
                f"constructor run_id {run_id!r} != contract.run_id "
                f"{contract.run_id!r}"
            )
        frozen = store.get_manifest(run_id)
        if frozen is not None:
            fresh = ConformanceContract.from_manifest(frozen)
            if (
                fresh.manifest_fingerprint != contract.manifest_fingerprint
                or fresh.manifest_revision != contract.manifest_revision
                or fresh.graph_id != contract.graph_id
                or fresh.node_ids != contract.node_ids
                or fresh.run_id != contract.run_id
            ):
                raise CheckpointIdentityError(
                    "constructor contract does not match the current frozen "
                    f"manifest for run {run_id!r} "
                    f"(fingerprint/revision/graph/node-order)"
                )
            contract = fresh

        self._store = store
        self._events = events
        self._contract = contract
        self._work_dir = Path(work_dir)
        self._run_id = run_id
        self._max_iterations = max_iterations
        self._manifest: Optional[ExecutionManifest] = None
        self._outputs: Dict[str, Mapping[str, Any]] = {}
        # per-run node result tracking (GraphRun assembly)
        self._node_results: List[GraphNodeResult] = []
        self._reused_ids: set = set()
        self._pre_terminal: set = set()
        # Per-run checkpoint dir + namespace: bind checkpoints to exact run,
        # manifest revision, graph id, node ids, and manifest fingerprint.
        # Created ONLY after constructor identity validation above.
        self._ns = checkpoint_namespace(
            run_id,
            contract.manifest_revision,
            contract.graph_id,
            contract.node_ids,
            contract.manifest_fingerprint,
        )
        self._run_ckpt_dir = checkpoint_dir(self._work_dir) / self._ns
        self._run_ckpt_dir.mkdir(parents=True, exist_ok=True)
        self._checkpoint_storage = StrictJsonCheckpointStorage(
            self._run_ckpt_dir,
            checkpoint_namespace=self._ns,
            run_id=run_id,
            manifest_revision=contract.manifest_revision,
            graph_id=contract.graph_id,
            node_ids=contract.node_ids,
            manifest_fingerprint=contract.manifest_fingerprint,
        )

    # ------------------------------------------------------------------ build

    def _build_workflow(self, node_ids: Sequence[str]) -> Any:
        """Build a fresh Agent Framework ``Workflow`` for the given node ids."""
        executors = {
            nid: _SyntheticNodeExecutor(nid, port=self) for nid in node_ids
        }
        start = executors[node_ids[0]]
        builder = WorkflowBuilder(
            start_executor=start,
            checkpoint_storage=self._checkpoint_storage,
            name=self.WORKFLOW_NAME,
            max_iterations=self._max_iterations,
        )
        for i in range(len(node_ids) - 1):
            builder.add_edge(executors[node_ids[i]], executors[node_ids[i + 1]])
        return builder.build()

    # ------------------------------------------------------------------ identity

    def _validate_live_contract(self, run_id: str) -> ConformanceContract:
        """Recompute the frozen contract at public-method entry; reject stale
        constructor state before any workflow construction or mutation."""
        if run_id != self._run_id:
            raise CheckpointIdentityError(
                f"public method run_id {run_id!r} != constructor run_id "
                f"{self._run_id!r}"
            )
        manifest = self._load_manifest(run_id)
        fresh = ConformanceContract.from_manifest(manifest)
        if (
            fresh.manifest_fingerprint != self._contract.manifest_fingerprint
            or fresh.manifest_revision != self._contract.manifest_revision
            or fresh.graph_id != self._contract.graph_id
            or fresh.node_ids != self._contract.node_ids
        ):
            raise CheckpointIdentityError(
                "stale constructor contract: frozen manifest fingerprint/"
                f"revision/graph/node-order diverged for run {run_id!r}"
            )
        self._contract = fresh
        self._manifest = manifest
        return fresh

    def _snapshot_pre_terminal(self, run_id: str) -> set:
        """Capture terminal Store nodes BEFORE this public invocation."""
        manifest = self._manifest or self._load_manifest(run_id)
        out: set = set()
        for nid in manifest.node_ids():
            existing = self._store.get_node_run(run_id, nid)
            if existing is not None and existing.status in TERMINAL_NODE_STATUSES:
                out.add(nid)
        self._pre_terminal = out
        return out

    # ------------------------------------------------------------------ ports

    def run(
        self,
        graph: Graph,
        run_id: str,
        context: Optional[Mapping[str, Any]] = None,
        auto_finalize: bool = True,
    ) -> GraphRun:
        """Execute the graph through the Agent Framework workflow engine.

        Validates the live frozen contract and exact Graph IR BEFORE any
        workflow construction, checkpoint, event, or Store mutation.
        """
        self._validate_live_contract(run_id)
        assert self._manifest is not None
        expected = Graph.from_manifest(self._manifest)
        assert_exact_graph_ir(graph, expected)
        pre_terminal = self._snapshot_pre_terminal(run_id)
        node_ids = list(self._manifest.node_ids())
        self._node_results = []
        self._reused_ids = set()
        wf = self._build_workflow(node_ids)
        try:
            asyncio.run(self._await_run(wf, run_id, seed=_initial_seed(run_id)))
            status = "complete"
        except WorkflowConvergenceException:
            # Injected boundary (max_iterations reached before convergence):
            # process A stops here.  The checkpoint from the last completed
            # superstep is already persisted (strict JSON) and resumable.
            status = "blocked"
        return self._assemble_run(
            run_id, graph.graph_id, status, pre_terminal=pre_terminal,
        )

    def resume(self, run_id: str) -> GraphRun:
        """Resume an interrupted run from the latest framework checkpoint.

        The checkpoint is validated for exact run/graph binding before any
        domain/event mutation (the storage's ``load`` enforces this).
        """
        self._validate_live_contract(run_id)
        assert self._manifest is not None
        node_ids = list(self._manifest.node_ids())
        pre_terminal = self._snapshot_pre_terminal(run_id)
        self._node_results = []
        self._reused_ids = set()

        latest = asyncio.run(
            self._checkpoint_storage.get_latest(workflow_name=self.WORKFLOW_NAME)
        )
        if latest is None:
            raise RuntimeError(
                f"no Agent Framework checkpoint to resume for run {run_id} "
                f"(namespace {self._ns})"
            )
        wf = self._build_workflow(node_ids)
        try:
            asyncio.run(self._await_run(wf, run_id, checkpoint_id=latest.checkpoint_id))
            status = "complete"
        except WorkflowConvergenceException:
            status = "blocked"
        return self._assemble_run(
            run_id, self._manifest.graph_id, status, pre_terminal=pre_terminal,
        )

    def replay(self, run_id: str) -> GraphRun:
        """Re-execute a completed run; every node must come back REUSED."""
        self._validate_live_contract(run_id)
        assert self._manifest is not None
        node_ids = list(self._manifest.node_ids())
        pre_terminal = self._snapshot_pre_terminal(run_id)
        self._node_results = []
        self._reused_ids = set()
        # Replay runs the workflow from a fresh seed; all nodes are terminal in
        # the Store so every executor takes the reused path.
        wf = self._build_workflow(node_ids)
        asyncio.run(self._await_run(wf, run_id, seed=_initial_seed(run_id)))
        # public replay asserts every node was reused (pre-invocation terminal)
        for nid in node_ids:
            if nid not in pre_terminal:
                raise RuntimeError(
                    f"replay did not reuse node {nid} "
                    "(node was not terminal pre-invocation)"
                )
        return self._assemble_run(
            run_id, self._manifest.graph_id, "complete", pre_terminal=pre_terminal,
        )

    # -------------------------------------------------------- async runners

    async def _await_run(
        self,
        wf: Any,
        run_id: str,
        *,
        seed: Optional[str] = None,
        checkpoint_id: Optional[str] = None,
    ) -> WorkflowRunResult:
        if checkpoint_id is not None:
            return await wf.run(checkpoint_id=checkpoint_id)
        return await wf.run(seed)

    # -------------------------------------------------------- result assembly

    def _assemble_run(
        self,
        run_id: str,
        graph_id: str,
        status: str,
        *,
        pre_terminal: Optional[set] = None,
    ) -> GraphRun:
        node_results: List[GraphNodeResult] = []
        manifest = self._manifest
        assert manifest is not None
        pre = set(pre_terminal) if pre_terminal is not None else set(self._pre_terminal)
        for node_id in manifest.node_ids():
            existing = self._store.get_node_run(run_id, node_id)
            node_status = (
                existing.status if existing is not None else NodeStatus.PENDING
            )
            # reused = was terminal BEFORE this invocation (not post-exec state)
            reused = node_id in pre
            node_results.append(
                GraphNodeResult(
                    run_id=run_id,
                    node_id=node_id,
                    status=node_status,
                    reused=bool(reused),
                    artifact_id=existing.artifact_id if existing else None,
                    message="reused from committed state" if reused else "af-adapter",
                )
            )
        self._node_results = node_results
        return GraphRun(
            run_id=run_id,
            graph_id=graph_id,
            status=status,
            node_results=node_results,
        )

    # -------------------------------------------------------- manifest/state

    def _load_manifest(self, run_id: str) -> ExecutionManifest:
        manifest = self._store.get_manifest(run_id)
        if manifest is None:
            raise RuntimeError(f"no manifest frozen for run {run_id}")
        return manifest

    # -------------------------------------------------------- work events

    def _completed_so_far(self) -> int:
        assert self._manifest is not None
        progress = self._store.manifest_progress(self._manifest.run_id)
        return int(progress["completed"])

    def _emit_work_event(
        self,
        node_id: str,
        phase: str,
        work_unit_id: str,
        *,
        status: str,
    ) -> None:
        from mm_r1.domain import new_id

        assert self._manifest is not None
        event = {
            "event_id": new_id("we_"),
            "run_id": self._run_id,
            "manifest_revision": self._contract.manifest_revision,
            "sequence": 0,
            "node_id": node_id,
            "work_unit_id": work_unit_id,
            "phase": phase,
            "status": status,
            "completed": self._completed_so_far(),
            "total": self._contract.total_units,
            "current_detail": f"{phase}:{node_id}",
            "created_at": now_iso(),
            "idempotency_key": f"we:{self._run_id}:{node_id}:{phase}",
        }
        self._events.append(event, self._contract)

    def _record_reused(self, node_id: str, status_value: str) -> None:
        self._reused_ids.add(node_id)

    # -------------------------------------------------------- conformance

    def conformance_result(self, run_id: str) -> ConformanceResult:
        """Build the normalized framework-neutral result from the Store + events.

        ``reused`` mirrors the last public invocation's pre-terminal snapshot
        when available; otherwise falls back to empty (fresh) semantics so a
        post-hoc call after a fresh run does not falsely mark nodes reused.
        """
        manifest = self._load_manifest(run_id)
        pre = set(self._pre_terminal)
        nodes: List[NodeConformance] = []
        for node_id in manifest.node_ids():
            existing = self._store.get_node_run(run_id, node_id)
            status = existing.status.value if existing else NodeStatus.PENDING.value
            nodes.append(
                NodeConformance(
                    node_id=node_id,
                    status=status,
                    reused=node_id in pre,
                    artifact_id=existing.artifact_id if existing else None,
                    artifact_content_hash=None,
                    message="af-adapter",
                )
            )
        progress = self._store.manifest_progress(run_id)
        events_list = self._events.list_events(run_id)
        projection = WorkEventProjection(
            count=len(events_list),
            distinct_idempotency_keys=self._events.distinct_idempotency_keys(run_id),
            sequences=[e.sequence for e in events_list],
            completed=int(progress["completed"]),
            total=int(progress["total"]),
            statuses=[e.status for e in events_list],
        )
        audit_ok = True
        try:
            self._store.verify_audit_chain(run_id)
        except Exception:
            audit_ok = False
        terminal = all(is_completed_terminal(n.status) for n in nodes)
        return ConformanceResult(
            run_id=run_id,
            manifest_revision=manifest.revision,
            graph_id=manifest.graph_id,
            status="complete" if terminal else "blocked",
            nodes=nodes,
            progress={"completed": int(progress["completed"]), "total": int(progress["total"])},
            artifact_count=0,
            artifact_hashes=[],
            work_event_projection=projection,
            audit_ok=audit_ok,
            audit_count=0,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _initial_seed(run_id: str) -> str:
    """The seed message for the first executor (no accumulated outputs)."""
    return json.dumps({"run_id": run_id, "outputs": {}}, sort_keys=True)


__all__ = [
    "FRAMEWORK_PACKAGE",
    "FRAMEWORK_VERSION",
    "CHECKPOINT_SCHEMA_VERSION",
    "AgentFrameworkWorkflowPort",
    "StrictJsonCheckpointStorage",
    "CheckpointIdentityError",
    "checkpoint_dir",
    "checkpoint_namespace",
]
