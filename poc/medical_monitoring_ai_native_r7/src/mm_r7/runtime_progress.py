"""R7 Slice-04 synthetic runtime manifest and audience progress adapter.

This module is deliberately a thin seam over the accepted R1 ``Store`` and
``project_audience_progress`` implementations.  It owns the R7-to-R1 identity
check and the product-safe metadata wrapper; it does not keep a second
progress table, start work, call a model, or expose execution identities.

The adapter constructor is side-effect free.  A runtime store is opened only
after an existing R7 run binding and a complete, audience-safe work-unit
definition have passed validation.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import re
import sqlite3
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Callable, Optional, Union

from . import run_binding as rb
from .maintenance_gate import (
    DEFAULT_WAIT_SECONDS,
    MaintenanceGateError,
    ProjectMaintenanceGate,
)
from .run_entry import (
    RUN_BINDING_DB_NAME,
    RunEntryError,
)


# R1 is a read-only dependency of this adapter.  Match the established R7
# adapter import convention so the module works both from the POC test runner
# and from the workbench product package.
_R1_SRC = Path(__file__).resolve().parents[3] / "medical_monitoring_ai_native_r1" / "src"
if _R1_SRC.is_dir() and str(_R1_SRC) not in sys.path:
    sys.path.insert(0, str(_R1_SRC))

from mm_r1 import audience_progress as _audience  # noqa: E402
from mm_r1.domain import (  # noqa: E402
    ExecutionBasis,
    ExecutionManifest,
    ManifestNode,
    ManifestWorkUnit,
    MonitoringRun,
    NodeStatus,
    NodeType,
    RunMode,
    SourceRevision,
    WorkUnitRun,
    canonical_json,
    content_hash,
    to_jsonable,
)
from mm_r1.store import Store  # noqa: E402


RUNTIME_DIR_NAME = "runtime"
RUNTIME_DB_NAME = "monitoring_runtime.sqlite3"
ARTIFACT_DIR_NAME = "artifacts"
NODE_ID = "r7-offline-monitor"
GRAPH_VERSION = "mm-r7-slice04-offline-v1"
SCHEMA_VERSION = "mm-r7-slice04-schema-v1"
SOURCE_VERSION = "mm-r7-slice04-synthetic-binding-v1"
HARNESS_GRAPH_VERSION = "mm-r7-slice06-harness-v1"
HARNESS_SCHEMA_VERSION = "mm-r7-slice06-schema-v1"
HARNESS_SOURCE_VERSION = "mm-r7-slice06-harness-binding-v1"
EXECUTION_KIND_DETERMINISTIC = "deterministic"
EXECUTION_KIND_HARNESS = "harness"

_WORK_UNIT_FIELDS = frozenset(
    {
        "work_unit_id",
        "stage",
        "label",
        "scope",
        "target_ref",
        "ordinal",
        "mandatory",
        "depends_on",
        # Optional request marker.  The manifest keeps node type at the node
        # level; this field only lets product callers opt into the AI seam.
        "node_type",
        "execution_mode",
    }
)
_REQUIRED_WORK_UNIT_FIELDS = (
    "work_unit_id",
    "stage",
    "label",
    "scope",
    "target_ref",
    "ordinal",
)

_MODE_TEXT = {
    RunMode.DAILY.value: "日常监查",
    RunMode.PRE_LOCK.value: "锁库前监查",
    RunMode.POST_LOCK_PRE_CFDI.value: "核查前监查",
}
_BASIS_TEXT = {
    ExecutionBasis.FULL.value: "全量",
    ExecutionBasis.INCREMENTAL.value: "增量",
}

_ERROR_MESSAGES = {
    "run_binding_not_found": "未找到指定的监查运行绑定。",
    "execution_not_prepared": "请先准备本次监查工作范围。",
    "invalid_work_units": "本次监查工作范围无效，请检查工作项定义。",
    "invalid_project_id": "医学监查项目标识无效。",
    "runtime_identity_mismatch": (
        "已准备的监查运行身份与当前绑定不一致，已阻断。"
    ),
    "runtime_integrity_failed": "本次监查进度无法核对，已阻断。",
    "superseded_scope_replay_forbidden": (
        "已存在当前监查范围，不允许重新采用历史范围。"
    ),
    "frozen_scope_revision_forbidden": "核查前监查范围已冻结，不允许变更。",
    "unsupported_mode": "不支持的监查运行模式。",
    "unsupported_execution_basis": "不支持的运行基准。",
    "unsupported_execution_kind": "不支持的监查执行方式。",
    "unsafe_data_cutoff": "数据截止点不符合展示约定。",
    "project_busy_retry_later": "项目正在处理数据，请稍后重试",
}

# Product responses are checked again after the R1 projection.  Keeping this
# scan local prevents future R1 additions or adapter metadata from widening the
# public surface accidentally.
_FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "run_id",
        "project_id",
        "node_id",
        "work_unit_id",
        "attempt_id",
        "attempt_ordinal",
        "manifest_revision",
        "binding_digest",
        "execution_profile_digest",
        "provider",
        "model",
        "selector",
        "adapter",
        "harness",
        "backend",
        "hash",
        "path",
        "database",
        "db",
        "execution_identity",
        "event_type",
        "status_code",
        "owner",
        "lease",
        "generation",
        "thread",
        "pid",
        "token",
    }
)
_FORBIDDEN_PUBLIC_TEXT = (
    "正式事实",
    "候选信号",
    "只读",
    "provider",
    "model",
    "selector",
    "adapter",
    "harness",
    "backend",
    "execution_identity",
    "work_unit",
    "manifest_revision",
    "attempt",
    "binding",
    "audit",
    "log",
    "hash",
    "sqlite",
    "database",
    "owner",
    "lease",
    "generation",
    "thread",
    "pid",
    "token",
)
_UUID = re.compile(
    r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
)
_LONG_HEX = re.compile(r"(?i)\b[0-9a-f]{32,}\b")
_TECHNICAL_ADDRESS = re.compile(
    r"(?i)(?:[a-z][a-z0-9+.-]{0,31}://|"
    r"(?<![a-z0-9])[a-z][a-z0-9+.-]{0,31}:|"
    r"(?<![a-z0-9])(?:/|~/|\.\.?/|[a-z]:[\\/])|"
    r"(?<![a-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?::\d{2,5})?)"
)
_CLINICAL_COLON_PREFIX = re.compile(
    r"(?<![A-Za-z0-9])(?:AE|SAE|MH|CM|IP|PD|ALT|AST|ALP|GGT|TBIL|DBIL|"
    r"ECG|QTCF|QTCB|PK):(?=\s*[\u3400-\u9fffA-Z0-9])"
)


class RuntimeProgressError(RunEntryError):
    """Stable R7 product error; details are never copied from lower layers."""

    def __init__(self, code: str, message: Optional[str] = None) -> None:
        super().__init__(
            code, message or _ERROR_MESSAGES.get(code, "本次监查操作未能完成。")
        )


def _error(code: str) -> RuntimeProgressError:
    return RuntimeProgressError(code)


def _non_empty_text(value: Any, code: str = "invalid_work_units") -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise _error(code)
    return value


def validate_public_data_cutoff(value: Any) -> str:
    """Return a display-safe data cutoff or fail closed with a stable code."""
    text = _non_empty_text(value, "unsafe_data_cutoff")
    if len(text) > 160 or any(ord(char) < 32 for char in text):
        raise _error("unsafe_data_cutoff")
    lowered = text.casefold()
    if any(
        token in lowered
        for token in ("sha", "hash", "sqlite", "database", "provider", "model")
    ):
        raise _error("unsafe_data_cutoff")
    if _UUID.search(text) or _LONG_HEX.search(text) or _TECHNICAL_ADDRESS.search(text):
        raise _error("unsafe_data_cutoff")
    return text


def _manifest_definition(manifest: ExecutionManifest) -> dict[str, Any]:
    """Match R1's content definition while clearing store-assigned metadata."""
    definition = to_jsonable(manifest)
    definition["revision"] = 0
    definition["created_at"] = ""
    return definition


def _same_manifest(left: ExecutionManifest, right: ExecutionManifest) -> bool:
    return canonical_json(_manifest_definition(left)) == canonical_json(
        _manifest_definition(right)
    )


class _PendingProjectionStore:
    """Small no-I/O facade used to invoke R1's audience validation pre-Store."""

    def __init__(self, manifest: ExecutionManifest) -> None:
        self._manifest = manifest
        self._rows = [
            WorkUnitRun(
                run_id=manifest.run_id,
                manifest_revision=1,
                work_unit_id=unit.work_unit_id,
                node_id=unit.node_id,
                status=NodeStatus.PENDING,
            )
            for unit in manifest.work_units
        ]

    def structured_progress(self, run_id: str, *, feed_limit: int = 20) -> dict[str, Any]:
        if run_id != self._manifest.run_id or feed_limit != 20:
            raise _error("runtime_integrity_failed")
        return {
            "manifest_revision": 1,
            "is_current_revision": True,
            "completed": 0,
            "total": len(self._rows),
            "percent": 0.0,
            "by_status": {NodeStatus.PENDING.value: len(self._rows)},
            "running": [],
            "feed": [],
        }

    def get_manifest(self, run_id: str, revision: int) -> Optional[ExecutionManifest]:
        if run_id == self._manifest.run_id and revision == 1:
            return self._manifest
        return None

    def list_work_unit_runs(self, run_id: str, revision: int) -> list[WorkUnitRun]:
        if run_id != self._manifest.run_id or revision != 1:
            raise _error("runtime_integrity_failed")
        return list(self._rows)


def _validate_audience_fields(manifest: ExecutionManifest) -> None:
    """Run the accepted R1 audience projection before any runtime mkdir."""
    try:
        _audience.project_audience_progress(_PendingProjectionStore(manifest), manifest.run_id)
    except RuntimeProgressError:
        raise
    except Exception as exc:
        raise _error("invalid_work_units") from exc


def _normalize_work_units(raw: Any) -> list[ManifestWorkUnit]:
    if isinstance(raw, (str, bytes, bytearray, Mapping)) or not isinstance(
        raw, Sequence
    ):
        raise _error("invalid_work_units")
    if not raw:
        raise _error("invalid_work_units")

    units: list[ManifestWorkUnit] = []
    seen_ids: set[str] = set()
    seen_ordinals: set[int] = set()
    for item in raw:
        if not isinstance(item, Mapping) or set(item) - _WORK_UNIT_FIELDS:
            raise _error("invalid_work_units")
        if any(field not in item for field in _REQUIRED_WORK_UNIT_FIELDS):
            raise _error("invalid_work_units")
        work_unit_id = _non_empty_text(item["work_unit_id"])
        stage = _non_empty_text(item["stage"])
        label = _non_empty_text(item["label"])
        scope = _non_empty_text(item["scope"])
        target_ref = _non_empty_text(item["target_ref"])
        ordinal = item["ordinal"]
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal <= 0:
            raise _error("invalid_work_units")
        mandatory = item.get("mandatory", True)
        if not isinstance(mandatory, bool):
            raise _error("invalid_work_units")
        depends_on = item.get("depends_on", [])
        if isinstance(depends_on, (str, bytes, bytearray)) or not isinstance(
            depends_on, Sequence
        ):
            raise _error("invalid_work_units")
        normalized_dependencies = []
        for dependency in depends_on:
            normalized_dependencies.append(_non_empty_text(dependency))
        if len(normalized_dependencies) != len(set(normalized_dependencies)):
            raise _error("invalid_work_units")
        if work_unit_id in seen_ids or ordinal in seen_ordinals:
            raise _error("invalid_work_units")
        seen_ids.add(work_unit_id)
        seen_ordinals.add(ordinal)
        units.append(
            ManifestWorkUnit(
                work_unit_id=work_unit_id,
                node_id=NODE_ID,
                label=label,
                stage=stage,
                scope=scope,
                target_ref=target_ref,
                ordinal=ordinal,
                mandatory=mandatory,
                depends_on=sorted(normalized_dependencies),
            )
        )

    if sorted(seen_ordinals) != list(range(1, len(units) + 1)):
        raise _error("invalid_work_units")
    unit_ids = {unit.work_unit_id for unit in units}
    for unit in units:
        if unit.work_unit_id in unit.depends_on or any(
            dependency not in unit_ids for dependency in unit.depends_on
        ):
            raise _error("invalid_work_units")

    by_id = {unit.work_unit_id: unit for unit in units}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(unit_id: str) -> None:
        if unit_id in visited:
            return
        if unit_id in visiting:
            raise _error("invalid_work_units")
        visiting.add(unit_id)
        for dependency in by_id[unit_id].depends_on:
            visit(dependency)
        visiting.remove(unit_id)
        visited.add(unit_id)

    for unit in units:
        visit(unit.work_unit_id)
    return sorted(units, key=lambda unit: unit.ordinal)


def _normalize_execution_kind(value: Any) -> str:
    if value is None:
        return EXECUTION_KIND_DETERMINISTIC
    text = str(value).strip().casefold()
    if text in {"deterministic", "synthetic"}:
        return EXECUTION_KIND_DETERMINISTIC
    if text in {"harness", "ai", "ai_candidate", "ai-candidate"}:
        return EXECUTION_KIND_HARNESS
    raise _error("unsupported_execution_kind")


def _infer_execution_kind(raw: Any, explicit: Any) -> str:
    kind = _normalize_execution_kind(explicit)
    if kind == EXECUTION_KIND_HARNESS or not isinstance(raw, Sequence):
        return kind
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        marker = item.get("node_type", item.get("execution_mode", ""))
        if str(marker).strip().casefold() in {
            "harness", "ai", "ai_candidate", "ai-candidate",
            "nodetype.ai_candidate",
        }:
            return EXECUTION_KIND_HARNESS
    return kind


def _binding_from_store(
    run_id: str,
    workspace_dir: Path,
    binding_store: Any,
) -> rb.MonitoringRunBinding:
    owned = False
    store = binding_store
    if store is None:
        binding_path = workspace_dir / RUN_BINDING_DB_NAME
        if not binding_path.is_file():
            raise _error("run_binding_not_found")
        try:
            store = rb.RunBindingStore(binding_path)
            owned = True
        except Exception as exc:
            raise _error("runtime_integrity_failed") from exc
    try:
        try:
            binding = store.get(run_id)
            if not isinstance(binding, rb.MonitoringRunBinding):
                raise _error("runtime_integrity_failed")
            return binding
        except rb.RunBindingError as exc:
            code = str(exc).split(":", 1)[0]
            if code == "run_binding_not_found":
                raise _error("run_binding_not_found") from exc
            raise _error("runtime_integrity_failed") from exc
        except Exception as exc:
            raise _error("runtime_integrity_failed") from exc
    finally:
        if owned:
            store.close()


def _assert_binding_identity(
    binding: rb.MonitoringRunBinding,
    run_id: str,
    canonical_project_id: str,
) -> tuple[RunMode, ExecutionBasis, str]:
    if not isinstance(binding, rb.MonitoringRunBinding):
        raise _error("runtime_integrity_failed")
    if binding.run_id != run_id or (
        canonical_project_id and binding.project_id != canonical_project_id
    ):
        raise _error("run_binding_not_found")
    try:
        mode = RunMode(binding.mode)
    except ValueError as exc:
        raise _error("unsupported_mode") from exc
    try:
        basis = ExecutionBasis(binding.execution_basis)
    except ValueError as exc:
        raise _error("unsupported_execution_basis") from exc
    cutoff = validate_public_data_cutoff(binding.data_cutoff)
    return mode, basis, cutoff


def _binding_source_hash(binding: rb.MonitoringRunBinding) -> str:
    return content_hash(
        {
            "synthetic": True,
            "schema_version": SCHEMA_VERSION,
            "project_id": binding.project_id,
            "source_revision_id": binding.source_revision_id,
        }
    )


def _ensure_runtime_identity(
    store: Store,
    binding: rb.MonitoringRunBinding,
    mode: RunMode,
    basis: ExecutionBasis,
    *,
    allow_create: bool,
) -> None:
    """Create or validate the synthetic R1 identity in contract order.

    ``allow_create`` is true only for explicit prepare.  A progress read must
    never repair missing business rows, even when its SQLite file exists.
    """
    try:
        try:
            project = store.get_project(binding.project_id)
        except Exception as exc:
            if "project not found" not in str(exc).casefold():
                raise
            if not allow_create:
                raise _error("runtime_identity_mismatch") from exc
            store.create_project(binding.project_id, "合成医学监查项目", config={})
            project = store.get_project(binding.project_id)
        if project.project_id != binding.project_id or not project.is_synthetic:
            raise _error("runtime_identity_mismatch")

        expected_source = SourceRevision(
            revision_id=binding.source_revision_id,
            project_id=binding.project_id,
            source_type="listing",
            version=SOURCE_VERSION,
            content_hash=_binding_source_hash(binding),
            scope={},
        )
        try:
            source = store.get_source_revision(binding.source_revision_id)
        except Exception as exc:
            if "source revision not found" not in str(exc).casefold():
                raise
            if not allow_create:
                raise _error("runtime_identity_mismatch") from exc
            store.add_source_revision(expected_source)
            source = store.get_source_revision(binding.source_revision_id)
        if (
            source.revision_id != expected_source.revision_id
            or source.project_id != expected_source.project_id
            or source.source_type != expected_source.source_type
            or source.version != expected_source.version
            or source.content_hash != expected_source.content_hash
            or source.valid_from != expected_source.valid_from
            or source.scope != expected_source.scope
        ):
            raise _error("runtime_identity_mismatch")

        expected_run = MonitoringRun(
            run_id=binding.run_id,
            project_id=binding.project_id,
            mode=mode,
            data_cutoff=binding.data_cutoff,
            source_revision_id=binding.source_revision_id,
            execution_basis=basis,
        )
        try:
            run = store.get_run(binding.run_id)
        except Exception as exc:
            if "run not found" not in str(exc).casefold():
                raise
            if not allow_create:
                raise _error("runtime_identity_mismatch") from exc
            store.create_run(expected_run)
            run = store.get_run(binding.run_id)
        if (
            run.run_id != expected_run.run_id
            or run.project_id != expected_run.project_id
            or run.mode != expected_run.mode
            or run.data_cutoff != expected_run.data_cutoff
            or run.source_revision_id != expected_run.source_revision_id
            or run.execution_basis != expected_run.execution_basis
        ):
            raise _error("runtime_identity_mismatch")
    except RuntimeProgressError:
        raise
    except Exception as exc:
        raise _error("runtime_integrity_failed") from exc


def _safe_public_payload(
    payload: Mapping[str, Any], expected_keys: set[str]
) -> dict[str, Any]:
    if set(payload) != expected_keys:
        raise _error("runtime_integrity_failed")
    lowered_keys = {str(key).casefold() for key in payload}
    if lowered_keys & _FORBIDDEN_PUBLIC_KEYS:
        raise _error("runtime_integrity_failed")
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    lowered = blob.casefold()
    if any(token in lowered for token in _FORBIDDEN_PUBLIC_TEXT):
        raise _error("runtime_integrity_failed")
    address_text = _CLINICAL_COLON_PREFIX.sub("", blob)
    if (
        _UUID.search(blob)
        or _LONG_HEX.search(blob)
        or _TECHNICAL_ADDRESS.search(address_text)
    ):
        raise _error("runtime_integrity_failed")
    return dict(payload)


class RuntimeProgressAdapter:
    """Prepare and read one canonical project's R1-backed runtime store."""

    def __init__(
        self,
        workspace_dir: Optional[Union[str, Path]] = None,
        binding_store: Any = None,
        *,
        runtime_dir: Optional[Union[str, Path]] = None,
        canonical_project_id: str = "",
        entry: Any = None,
        harness_runtime_factory: Optional[Callable[..., Any]] = None,
        harness_adapter: Any = None,
        harness_catalog: Any = None,
        harness_r1_profile: Any = None,
    ) -> None:
        if runtime_dir is not None:
            self.runtime_dir = Path(runtime_dir)
            self.workspace_dir = self.runtime_dir.parent
        elif workspace_dir is not None:
            root = Path(workspace_dir)
            if root.name == RUNTIME_DIR_NAME:
                self.runtime_dir = root
                self.workspace_dir = root.parent
            else:
                self.workspace_dir = root
                self.runtime_dir = root / RUNTIME_DIR_NAME
        else:
            raise _error("invalid_project_id")
        self.canonical_project_id = canonical_project_id or (
            self.workspace_dir.name if self.workspace_dir.name != RUNTIME_DIR_NAME else ""
        )
        self.binding_store = binding_store or getattr(entry, "run_binding_store", None)
        self.harness_runtime_factory = harness_runtime_factory
        self.harness_adapter = harness_adapter
        self.harness_catalog = harness_catalog
        self.harness_r1_profile = harness_r1_profile
        # Product requests may close their RunEntry immediately after spawning
        # the worker.  Cache the immutable frozen profile while that request's
        # binding store is still open; the worker never needs the R6 store.
        self._harness_profiles: dict[str, Any] = {}

    @property
    def db_path(self) -> Path:
        return self.runtime_dir / RUNTIME_DB_NAME

    @property
    def artifact_dir(self) -> Path:
        return self.runtime_dir / ARTIFACT_DIR_NAME
    @contextmanager
    def _shared_project_maintenance(self):
        """Hold the product shared gate while preparing runtime state."""
        if not self.canonical_project_id:
            yield
            return
        gate = ProjectMaintenanceGate(
            self.workspace_dir.parent,
            self.canonical_project_id,
            wait_seconds=DEFAULT_WAIT_SECONDS,
        )
        try:
            with gate.shared():
                yield
        except MaintenanceGateError as exc:
            raise _error("project_busy_retry_later") from exc

    def _binding(self, run_id: str) -> rb.MonitoringRunBinding:
        run_id = _non_empty_text(run_id, "run_binding_not_found")
        return _binding_from_store(run_id, self.workspace_dir, self.binding_store)

    def _manifest(
        self,
        run_id: str,
        binding: rb.MonitoringRunBinding,
        units: list[ManifestWorkUnit],
        execution_kind: str = EXECUTION_KIND_DETERMINISTIC,
    ) -> ExecutionManifest:
        is_harness = execution_kind == EXECUTION_KIND_HARNESS
        return ExecutionManifest(
            run_id=run_id,
            nodes=[
                ManifestNode(
                    node_id=NODE_ID,
                    node_type=(
                        NodeType.AI_CANDIDATE
                        if is_harness else NodeType.DETERMINISTIC_SERVICE
                    ),
                    mandatory=True,
                )
            ],
            work_units=units,
            graph_version=HARNESS_GRAPH_VERSION if is_harness else GRAPH_VERSION,
            schema_version=HARNESS_SCHEMA_VERSION if is_harness else SCHEMA_VERSION,
            adapter_profile={"execution_profile_digest": binding.execution_profile_digest},
        )

    def _open_prepared_store(self) -> Store:
        # Both checks precede Store construction.  Store.__init__ creates the
        # artifacts directory and executes schema/WAL setup, so it must not be
        # called for the unprepared GET path.
        if not self.db_path.is_file() or not self.artifact_dir.is_dir():
            raise _error("execution_not_prepared")
        try:
            return Store(self.db_path, self.artifact_dir)
        except RuntimeProgressError:
            raise
        except Exception as exc:
            raise _error("runtime_integrity_failed") from exc

    def _prepare_unlocked(
        self,
        run_id: str,
        work_units: Sequence[Mapping[str, Any]],
        execution_kind: str = EXECUTION_KIND_DETERMINISTIC,
    ) -> dict[str, Any]:
        """Explicitly prepare or replay the current offline scope."""
        binding = self._binding(run_id)
        mode, basis, cutoff = _assert_binding_identity(
            binding, run_id, self.canonical_project_id
        )
        execution_kind = _infer_execution_kind(work_units, execution_kind)
        units = _normalize_work_units(work_units)
        candidate = self._manifest(run_id, binding, units, execution_kind)
        _validate_audience_fields(candidate)
        if execution_kind == EXECUTION_KIND_HARNESS:
            self._cache_harness_profile(run_id)

        # This is the first operation allowed to create runtime/ and the R1
        # Store.  All request and audience checks above are deliberately before
        # this point.
        try:
            self.runtime_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise _error("runtime_integrity_failed") from exc
        store: Optional[Store] = None
        try:
            try:
                store = Store(self.db_path, self.artifact_dir)
                _ensure_runtime_identity(
                    store, binding, mode, basis, allow_create=True
                )
                run = store.get_run(run_id)
                current_revision = int(run.manifest_revision)
                revisions = store.list_manifest_revisions(run_id)
                if current_revision < 0 or (
                    current_revision == 0 and revisions
                ) or (
                    current_revision > 0 and current_revision not in revisions
                ):
                    raise _error("runtime_integrity_failed")
                current = (
                    store.get_manifest(run_id, current_revision)
                    if current_revision > 0
                    else None
                )
                if current_revision > 0 and current is None:
                    raise _error("runtime_integrity_failed")

                if current is not None and _same_manifest(current, candidate):
                    revision = current_revision
                    replayed = True
                else:
                    if mode == RunMode.POST_LOCK_PRE_CFDI and current is not None:
                        raise _error("frozen_scope_revision_forbidden")
                    # R7 control owns the run-level lease.  A different
                    # revision must not replace a live execution; the check
                    # occurs before R1's append-only manifest write.
                    from .background_recovery import (
                        assert_prepare_scope_change_allowed,
                    )

                    if current is not None:
                        assert_prepare_scope_change_allowed(
                            self.db_path, run_id, current_revision
                        )
                    for revision_number in revisions:
                        if revision_number == current_revision:
                            continue
                        historical = store.get_manifest(run_id, revision_number)
                        if historical is None:
                            raise _error("runtime_integrity_failed")
                        if _same_manifest(historical, candidate):
                            raise _error("superseded_scope_replay_forbidden")
                    expected_next = current_revision + 1
                    revision = int(store.set_manifest(candidate))
                    if revision != expected_next:
                        raise _error("runtime_integrity_failed")
                    replayed = False

                # The control row is deliberately separate from the R1
                # denominator/ledger, but lives in the same SQLite file.
                from .background_recovery import ensure_execution_control

                ensure_execution_control(self.db_path, run_id, revision)

                # A successful prepare must leave a reconciled authoritative
                # ledger.  This also checks the audit chain before responding.
                view = _audience.project_audience_progress(store, run_id)
                if view.get("total") != len(candidate.work_units):
                    raise _error("runtime_integrity_failed")
                response = {
                    "replayed": replayed,
                    "scope_version_text": f"第 {revision} 版监查范围",
                    "total": int(view["total"]),
                    "data_cutoff_text": cutoff,
                    "mode_text": _MODE_TEXT[mode.value],
                    "basis_text": _BASIS_TEXT[basis.value],
                }
                return _safe_public_payload(
                    response,
                    {
                        "replayed",
                        "scope_version_text",
                        "total",
                        "data_cutoff_text",
                        "mode_text",
                        "basis_text",
                    },
                )
            except RuntimeProgressError:
                raise
            except RunEntryError as exc:
                # Keep the Slice-04 adapter's public exception type while
                # preserving the stable R7 control code/message.
                if isinstance(exc, RuntimeProgressError):
                    raise
                raise RuntimeProgressError(exc.code, exc.message) from exc
            except (rb.RunBindingError, sqlite3.Error) as exc:
                raise _error("runtime_integrity_failed") from exc
            except Exception as exc:
                # R1's detailed exception text can contain internal IDs and is
                # intentionally not part of the product error boundary.
                raise _error("runtime_integrity_failed") from exc
        finally:
            if store is not None:
                store.close()
    def prepare(
        self,
        run_id: str,
        work_units: Sequence[Mapping[str, Any]],
        execution_kind: str = EXECUTION_KIND_DETERMINISTIC,
    ) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._prepare_unlocked(
                run_id, work_units, execution_kind=execution_kind
            )


    def _cache_harness_profile(self, run_id: str) -> None:
        """Capture the immutable R6 profile before a product request closes."""
        source = self.binding_store
        owned = False
        if source is None:
            binding_path = self.workspace_dir / RUN_BINDING_DB_NAME
            if not binding_path.is_file():
                return
            try:
                source = rb.RunBindingStore(binding_path)
                owned = True
            except Exception as exc:
                raise _error("runtime_integrity_failed") from exc
        try:
            getter = getattr(source, "get_with_frozen", None)
            if not callable(getter):
                raise _error("runtime_integrity_failed")
            _, frozen = getter(run_id)
            self._harness_profiles[run_id] = frozen
        except RuntimeProgressError:
            raise
        except Exception as exc:
            raise _error("runtime_integrity_failed") from exc
        finally:
            if owned:
                source.close()

    def _progress_unlocked(self, run_id: str) -> dict[str, Any]:
        """Return the current R1-backed Chinese audience progress."""
        binding = self._binding(run_id)
        mode, basis, cutoff = _assert_binding_identity(
            binding, run_id, self.canonical_project_id
        )
        store = self._open_prepared_store()
        try:
            try:
                # A bound run that was never prepared must read as
                # execution_not_prepared even when another run prepared the
                # shared project store first; identity validation only makes
                # sense once the run row and a manifest revision exist.
                try:
                    run = store.get_run(run_id)
                except Exception as exc:
                    if "run not found" in str(exc).casefold():
                        raise _error("execution_not_prepared") from exc
                    raise
                if run.manifest_revision <= 0:
                    raise _error("execution_not_prepared")
                _ensure_runtime_identity(
                    store, binding, mode, basis, allow_create=False
                )
                # The R7 helper joins the R1 audience projection and control
                # overlay inside this Store connection's deferred snapshot.
                from .background_recovery import BackgroundRecoveryAdapter

                view = BackgroundRecoveryAdapter(
                    runtime_dir=self.runtime_dir,
                    canonical_project_id=self.canonical_project_id,
                ).snapshot_from_store(store, run_id)
                expected = {
                    "headline",
                    "completed",
                    "total",
                    "percent",
                    "progress_text",
                    "status_overview",
                    "stage_progress",
                    "current_work",
                    "latest_updates",
                    "run_status_text",
                    "available_actions",
                    "run_state",
                }
                view = _safe_public_payload(view, expected)
                response = {
                    "scope_version_text": f"第 {run.manifest_revision} 版监查范围",
                    "mode_text": _MODE_TEXT[mode.value],
                    "basis_text": _BASIS_TEXT[basis.value],
                    "data_cutoff_text": cutoff,
                    **view,
                }
                return _safe_public_payload(
                    response,
                    expected
                    | {
                        "scope_version_text",
                        "mode_text",
                        "basis_text",
                        "data_cutoff_text",
                    },
                )
            except RuntimeProgressError:
                raise
            except RunEntryError as exc:
                if isinstance(exc, RuntimeProgressError):
                    raise
                raise RuntimeProgressError(exc.code, exc.message) from exc
            except (rb.RunBindingError, sqlite3.Error) as exc:
                raise _error("runtime_integrity_failed") from exc
            except Exception as exc:
                raise _error("runtime_integrity_failed") from exc
        finally:
            store.close()
    def progress(self, run_id: str) -> dict[str, Any]:
        with self._shared_project_maintenance():
            return self._progress_unlocked(run_id)

    def _background(self) -> Any:
        from .background_recovery import BackgroundRecoveryAdapter

        return BackgroundRecoveryAdapter(
            runtime_dir=self.runtime_dir,
            canonical_project_id=self.canonical_project_id,
            maintenance_root=self.workspace_dir.parent,
            harness_runtime_factory=self.harness_runtime_factory,
            harness_adapter=self.harness_adapter,
            harness_catalog=self.harness_catalog,
            harness_r1_profile=self.harness_r1_profile,
            harness_profile_factory=self._harness_profiles.get,
        )

    def start_execution(self, run_id: str) -> dict[str, Any]:
        binding = self._binding(run_id)
        _assert_binding_identity(binding, run_id, self.canonical_project_id)
        self._cache_harness_profile(run_id)
        try:
            return self._background().start_execution(run_id)
        except RunEntryError as exc:
            if isinstance(exc, RuntimeProgressError):
                raise
            raise RuntimeProgressError(exc.code, exc.message) from exc

    def resume_execution(self, run_id: str) -> dict[str, Any]:
        binding = self._binding(run_id)
        _assert_binding_identity(binding, run_id, self.canonical_project_id)
        self._cache_harness_profile(run_id)
        try:
            return self._background().resume_execution(run_id)
        except RunEntryError as exc:
            if isinstance(exc, RuntimeProgressError):
                raise
            raise RuntimeProgressError(exc.code, exc.message) from exc

    def cancel_execution(self, run_id: str) -> dict[str, Any]:
        binding = self._binding(run_id)
        _assert_binding_identity(binding, run_id, self.canonical_project_id)
        try:
            return self._background().cancel_execution(run_id)
        except RunEntryError as exc:
            if isinstance(exc, RuntimeProgressError):
                raise
            raise RuntimeProgressError(exc.code, exc.message) from exc

    start = start_execution
    resume = resume_execution
    cancel = cancel_execution

    # Names used by the product router and by the next execution slice.
    def prepare_execution(
        self,
        run_id: str,
        work_units: Sequence[Mapping[str, Any]],
        execution_kind: str = EXECUTION_KIND_DETERMINISTIC,
    ) -> dict[str, Any]:
        return self.prepare(run_id, work_units, execution_kind=execution_kind)

    def prepare_harness(
        self, run_id: str, work_units: Sequence[Mapping[str, Any]]
    ) -> dict[str, Any]:
        return self.prepare(
            run_id, work_units, execution_kind=EXECUTION_KIND_HARNESS
        )

    def read_progress(self, run_id: str) -> dict[str, Any]:
        return self.progress(run_id)

    def get_progress(self, run_id: str) -> dict[str, Any]:
        return self.progress(run_id)


RuntimeProgress = RuntimeProgressAdapter
RunProgressAdapter = RuntimeProgressAdapter


__all__ = [
    "ARTIFACT_DIR_NAME",
    "EXECUTION_KIND_DETERMINISTIC",
    "EXECUTION_KIND_HARNESS",
    "GRAPH_VERSION",
    "HARNESS_GRAPH_VERSION",
    "HARNESS_SCHEMA_VERSION",
    "HARNESS_SOURCE_VERSION",
    "NODE_ID",
    "RUNTIME_DB_NAME",
    "RUNTIME_DIR_NAME",
    "RuntimeProgress",
    "RuntimeProgressAdapter",
    "RuntimeProgressError",
    "RunProgressAdapter",
    "SCHEMA_VERSION",
]
