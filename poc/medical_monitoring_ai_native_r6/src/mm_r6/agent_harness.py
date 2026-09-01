"""R6 slice-07 ExecutionProfile registry and OMP print Agent Harness adapter.

Stdlib only. Deterministic under any ``PYTHONHASHSEED`` and ``-O``/``-OO``.

Provider/model/effort and invocation receipts stay inside this adapter boundary.
They must not be written into ModeOutput, risk, Profile, Timeline, Query, or
report medical objects.

Adapter contract id: ``omp_print_v1``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ADAPTER_ID = "omp_print_v1"
ADAPTER_VERSION = "1.0.0"

PROFILE_DEFAULT_ID = "monitoring_harness_default_mtplx_qwen38_medium"
PROFILE_DEEPSEEK_ID = "monitoring_harness_deepseek_v4_flash_max"

USER_NAME_MTPLX = "mtplx/Youssofal--Qwen3.8-27B-MTPLX-Optimized-Quality"
USER_NAME_DEEPSEEK = "deepseek/DeepSeek V4 flash"

EFFECTIVE_SELECTOR_MTPLX = "mtplx/Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality"
EFFECTIVE_SELECTOR_DEEPSEEK = "deepseek/deepseek-v4-flash"

EFFORT_MEDIUM = "medium"
EFFORT_MAX = "max"

ALLOWED_THINKING_LEVELS = frozenset(
    {"off", "minimal", "low", "medium", "high", "xhigh", "max", "auto"}
)

DEFAULT_ALLOWED_TOOLS: Tuple[str, ...] = ("read",)
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_CONTEXT_ISOLATION = "omp_print_no_session_no_skills_no_rules"

# Public catalog fields only — never env values or secrets.
_CATALOG_PUBLIC_FIELDS = (
    "provider",
    "id",
    "selector",
    "name",
    "contextWindow",
    "maxTokens",
    "reasoning",
    "thinking",
    "input",
    "cost",
)

_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)sk-[A-Za-z0-9]{8,}"),
)

_RECEIPT_STATES = frozenset(
    {"complete", "partial", "truncated", "failed", "timed_out", "not_evaluable"}
)
_PARSE_STATES = frozenset({"parsed", "unparsed", "invalid"})


class AgentHarnessError(RuntimeError):
    """Fail-closed error for profile or adapter contract violations."""


# ---------------------------------------------------------------------------
# Deterministic identity helpers
# ---------------------------------------------------------------------------


def canonical_json_bytes(obj: Any) -> bytes:
    """Stable UTF-8 JSON bytes (sorted keys, compact separators)."""
    return json.dumps(
        obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_hex(data: Union[bytes, str]) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def content_digest(obj: Any) -> str:
    return sha256_hex(canonical_json_bytes(obj))


def _tuple_str(values: Optional[Iterable[str]]) -> Tuple[str, ...]:
    return tuple(str(v) for v in (values or ()))


def sanitize_text(text: str, *, limit: int = 4000) -> str:
    """Return a scrubbed stderr/summary fragment (no secret values)."""
    out = text or ""
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    if len(out) > limit:
        out = out[:limit] + "...[truncated]"
    return out


# ---------------------------------------------------------------------------
# Alias registry (adapter-owned; not a medical object)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelAlias:
    """Maps a user-facing configuration name to an OMP effective selector."""

    user_config_name: str
    effective_selector: str
    provider: str
    model_id: str
    default_effort: str
    profile_id: str


ALIAS_REGISTRY: Dict[str, ModelAlias] = {
    USER_NAME_MTPLX: ModelAlias(
        user_config_name=USER_NAME_MTPLX,
        effective_selector=EFFECTIVE_SELECTOR_MTPLX,
        provider="mtplx",
        model_id="Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality",
        default_effort=EFFORT_MEDIUM,
        profile_id=PROFILE_DEFAULT_ID,
    ),
    USER_NAME_DEEPSEEK: ModelAlias(
        user_config_name=USER_NAME_DEEPSEEK,
        effective_selector=EFFECTIVE_SELECTOR_DEEPSEEK,
        provider="deepseek",
        model_id="deepseek-v4-flash",
        default_effort=EFFORT_MAX,
        profile_id=PROFILE_DEEPSEEK_ID,
    ),
}


def resolve_alias(user_config_name: str) -> ModelAlias:
    key = str(user_config_name or "").strip()
    if key not in ALIAS_REGISTRY:
        raise AgentHarnessError("unknown_alias:%s" % key)
    return ALIAS_REGISTRY[key]


# ---------------------------------------------------------------------------
# ExecutionProfile layers and freeze
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionProfileLayer:
    """One override layer. ``None`` fields inherit; empty string is not delete."""

    profile_id: Optional[str] = None
    profile_revision: Optional[str] = None
    capability_id: Optional[str] = None
    requested_provider: Optional[str] = None
    requested_model: Optional[str] = None
    user_config_name: Optional[str] = None
    effective_selector: Optional[str] = None
    reasoning_effort: Optional[str] = None
    timeout_seconds: Optional[int] = None
    allowed_tools: Optional[Tuple[str, ...]] = None
    context_isolation: Optional[str] = None
    credential_ref: Optional[str] = None
    adapter_id: Optional[str] = None
    adapter_version: Optional[str] = None
    fallback_profile_ids: Optional[Tuple[str, ...]] = None

    def as_override_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for name in (
            "profile_id",
            "profile_revision",
            "capability_id",
            "requested_provider",
            "requested_model",
            "user_config_name",
            "effective_selector",
            "reasoning_effort",
            "timeout_seconds",
            "allowed_tools",
            "context_isolation",
            "credential_ref",
            "adapter_id",
            "adapter_version",
            "fallback_profile_ids",
        ):
            value = getattr(self, name)
            if value is not None:
                out[name] = value
        return out


@dataclass(frozen=True)
class FrozenExecutionProfile:
    """Run-frozen effective profile. Immutable for the life of a Run."""

    profile_id: str
    profile_revision: str
    capability_id: str
    requested_provider: str
    requested_model: str
    user_config_name: str
    effective_selector: str
    reasoning_effort: str
    timeout_seconds: int
    allowed_tools: Tuple[str, ...]
    context_isolation: str
    credential_ref: str
    adapter_id: str
    adapter_version: str
    fallback_profile_ids: Tuple[str, ...]
    execution_profile_id: str
    execution_profile_digest: str

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_revision": self.profile_revision,
            "capability_id": self.capability_id,
            "requested_provider": self.requested_provider,
            "requested_model": self.requested_model,
            "user_config_name": self.user_config_name,
            "effective_selector": self.effective_selector,
            "reasoning_effort": self.reasoning_effort,
            "timeout_seconds": self.timeout_seconds,
            "allowed_tools": list(self.allowed_tools),
            "context_isolation": self.context_isolation,
            "credential_ref": self.credential_ref,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "fallback_profile_ids": list(self.fallback_profile_ids),
            "execution_profile_id": self.execution_profile_id,
            "execution_profile_digest": self.execution_profile_digest,
        }


def _builtin_global_default() -> ExecutionProfileLayer:
    alias = ALIAS_REGISTRY[USER_NAME_MTPLX]
    return ExecutionProfileLayer(
        profile_id=PROFILE_DEFAULT_ID,
        profile_revision="r6-slice07-v1",
        capability_id="medical_monitoring_harness",
        requested_provider=alias.provider,
        requested_model=alias.model_id,
        user_config_name=alias.user_config_name,
        effective_selector=alias.effective_selector,
        reasoning_effort=EFFORT_MEDIUM,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        allowed_tools=DEFAULT_ALLOWED_TOOLS,
        context_isolation=DEFAULT_CONTEXT_ISOLATION,
        credential_ref="env:OMP_CREDENTIAL_REF",
        adapter_id=ADAPTER_ID,
        adapter_version=ADAPTER_VERSION,
        fallback_profile_ids=(),
    )


def deepseek_profile_layer() -> ExecutionProfileLayer:
    """Explicit DeepSeek V4 Flash max alternative (never an auto-fallback)."""
    alias = ALIAS_REGISTRY[USER_NAME_DEEPSEEK]
    return ExecutionProfileLayer(
        profile_id=PROFILE_DEEPSEEK_ID,
        profile_revision="r6-slice07-v1",
        capability_id="medical_monitoring_harness",
        requested_provider=alias.provider,
        requested_model=alias.model_id,
        user_config_name=alias.user_config_name,
        effective_selector=alias.effective_selector,
        reasoning_effort=EFFORT_MAX,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        allowed_tools=DEFAULT_ALLOWED_TOOLS,
        context_isolation=DEFAULT_CONTEXT_ISOLATION,
        credential_ref="env:OMP_CREDENTIAL_REF",
        adapter_id=ADAPTER_ID,
        adapter_version=ADAPTER_VERSION,
        fallback_profile_ids=(),
    )


def registered_profile_layer(profile_id: str) -> ExecutionProfileLayer:
    if profile_id == PROFILE_DEFAULT_ID:
        return _builtin_global_default()
    if profile_id == PROFILE_DEEPSEEK_ID:
        return deepseek_profile_layer()
    raise AgentHarnessError("unknown_profile_id:%s" % profile_id)


_REGISTERED_LAYER_FIELDS = frozenset(
    {
        "profile_id",
        "profile_revision",
        "capability_id",
        "requested_provider",
        "requested_model",
        "user_config_name",
        "effective_selector",
        "reasoning_effort",
        "timeout_seconds",
        "allowed_tools",
        "context_isolation",
        "credential_ref",
        "adapter_id",
        "adapter_version",
        "fallback_profile_ids",
    }
)

_TOOL_WHITELIST = frozenset(DEFAULT_ALLOWED_TOOLS)


def list_registered_profile_ids() -> Tuple[str, ...]:
    """Stable ordered registered profile ids (default first)."""
    return (PROFILE_DEFAULT_ID, PROFILE_DEEPSEEK_ID)


def alias_map() -> Dict[str, str]:
    """User configuration name -> OMP effective selector (adapter registry only)."""
    return {
        name: alias.effective_selector for name, alias in ALIAS_REGISTRY.items()
    }


def merge_profile_layers(
    *layers: Optional[ExecutionProfileLayer],
) -> Dict[str, Any]:
    """Merge layers: global default -> capability -> project -> run freeze source.

    ``None`` layer arguments are skipped. Within a layer, field value ``None``
    means inherit (omitted by ``as_override_dict``). Empty string is kept as a
    concrete value, not a delete. Only registered fields may appear.
    """
    merged: Dict[str, Any] = {}
    for layer in layers:
        if layer is None:
            continue
        if not isinstance(layer, ExecutionProfileLayer):
            raise AgentHarnessError("invalid_layer_type")
        for key, value in layer.as_override_dict().items():
            if key not in _REGISTERED_LAYER_FIELDS:
                raise AgentHarnessError("unknown_override_field:%s" % key)
            merged[key] = value
    return merged


def refuse_auto_fallback(reason: str = "slice-07 forbids automatic fallback") -> None:
    """Explicit gate: DeepSeek is never an automatic fallback from MTPLX."""
    raise AgentHarnessError("auto_fallback_forbidden:%s" % reason)


def freeze_execution_profile(
    *layers: Optional[ExecutionProfileLayer],
    run_id: str = "",
    catalog_efforts: Optional[Iterable[str]] = None,
    tool_whitelist: Optional[Iterable[str]] = None,
) -> FrozenExecutionProfile:
    """Produce a Run-frozen profile copy with canonical id and digest.

    Any Run-scoped change must mint a new frozen copy; prior copies are never
    mutated. ``run_id`` is accepted for call-site bookkeeping but is not part of
    the canonical digest body (contract freeze fields only).
    """
    # run_id retained as a no-op keyword for adapter call sites; identity uses
    # contract freeze fields only.
    _ = run_id
    selected_profile_id = PROFILE_DEFAULT_ID
    for layer in layers:
        if layer is not None and layer.profile_id is not None:
            selected_profile_id = str(layer.profile_id)
    base = registered_profile_layer(selected_profile_id)
    merged = merge_profile_layers(base, *layers)

    profile_id = merged.get("profile_id")
    if profile_id is None or profile_id == "":
        raise AgentHarnessError("empty_profile_id")
    profile_id = str(profile_id)
    if profile_id not in (PROFILE_DEFAULT_ID, PROFILE_DEEPSEEK_ID):
        raise AgentHarnessError("unknown_profile_id:%s" % profile_id)

    capability_id = merged.get("capability_id")
    # Empty string is not a delete and is invalid for capability_id.
    if capability_id is None or capability_id == "":
        raise AgentHarnessError("empty_capability_id")
    capability_id = str(capability_id)

    user_config_name = merged.get("user_config_name")
    if user_config_name is None or user_config_name == "":
        raise AgentHarnessError("empty_user_config_name")
    user_config_name = str(user_config_name)
    alias = resolve_alias(user_config_name)

    if profile_id != alias.profile_id:
        raise AgentHarnessError(
            "profile_alias_mismatch:%s!=%s" % (profile_id, alias.profile_id)
        )

    requested_provider = merged.get("requested_provider")
    requested_model = merged.get("requested_model")
    effective_selector = merged.get("effective_selector")
    effort = merged.get("reasoning_effort")

    # None inherits alias; empty string is concrete and fails closed if wrong.
    if requested_provider is None:
        requested_provider = alias.provider
    else:
        requested_provider = str(requested_provider)
    if requested_model is None:
        requested_model = alias.model_id
    else:
        requested_model = str(requested_model)
    if effective_selector is None:
        effective_selector = alias.effective_selector
    else:
        effective_selector = str(effective_selector)
    if effort is None:
        effort = alias.default_effort
    else:
        effort = str(effort)

    if requested_provider != alias.provider:
        raise AgentHarnessError("provider_mismatch")
    if requested_model != alias.model_id:
        raise AgentHarnessError("model_mismatch")
    if effective_selector != alias.effective_selector:
        raise AgentHarnessError("selector_mismatch")
    if effort not in ALLOWED_THINKING_LEVELS:
        raise AgentHarnessError("illegal_effort:%s" % effort)
    # Registered profiles freeze their contract effort exactly.
    if (profile_id == PROFILE_DEFAULT_ID and effort != EFFORT_MEDIUM) or (
        profile_id == PROFILE_DEEPSEEK_ID and effort != EFFORT_MAX
    ):
        raise AgentHarnessError("effort_profile_inconsistent")

    if catalog_efforts is not None and effort not in frozenset(catalog_efforts):
        raise AgentHarnessError("effort_unsupported_by_catalog:%s" % effort)

    timeout_raw = merged.get("timeout_seconds")
    if timeout_raw is None:
        raise AgentHarnessError("illegal_timeout")
    if isinstance(timeout_raw, bool) or not isinstance(timeout_raw, int):
        raise AgentHarnessError("illegal_timeout")
    timeout = timeout_raw
    if timeout <= 0:
        raise AgentHarnessError("illegal_timeout")

    tools = _tuple_str(merged.get("allowed_tools"))
    if not tools:
        raise AgentHarnessError("empty_allowed_tools")
    if any(not t or t != t.strip() or " " in t or "," in t for t in tools):
        raise AgentHarnessError("illegal_tool_token")
    whitelist = (
        _TOOL_WHITELIST if tool_whitelist is None else frozenset(tool_whitelist)
    )
    overreach = [t for t in tools if t not in whitelist]
    if overreach:
        raise AgentHarnessError("tool_overreach:%s" % ",".join(overreach))

    adapter_id = merged.get("adapter_id")
    adapter_version = merged.get("adapter_version")
    if adapter_id is None:
        adapter_id = ADAPTER_ID
    else:
        adapter_id = str(adapter_id)
    if adapter_version is None:
        adapter_version = ADAPTER_VERSION
    else:
        adapter_version = str(adapter_version)
    if adapter_id != ADAPTER_ID:
        raise AgentHarnessError("unsupported_adapter_id:%s" % adapter_id)
    if adapter_version != ADAPTER_VERSION:
        raise AgentHarnessError("unsupported_adapter_version:%s" % adapter_version)

    credential_ref = merged.get("credential_ref")
    if credential_ref is None or credential_ref == "":
        raise AgentHarnessError("empty_credential_ref")
    credential_ref = str(credential_ref)
    lowered = credential_ref.lower()
    if any(
        token in lowered
        for token in ("sk-", "api_key=", "bearer ", "password=", "token=")
    ):
        raise AgentHarnessError("credential_ref_must_not_be_secret_value")

    fallback = _tuple_str(merged.get("fallback_profile_ids"))
    for fb in fallback:
        if fb not in (PROFILE_DEFAULT_ID, PROFILE_DEEPSEEK_ID):
            raise AgentHarnessError("unknown_fallback_profile_id:%s" % fb)
    # This slice records fallback ids but forbids adapter auto-execution.

    context_isolation = merged.get("context_isolation")
    if context_isolation is None or context_isolation == "":
        raise AgentHarnessError("empty_context_isolation")
    context_isolation = str(context_isolation)

    profile_revision = merged.get("profile_revision")
    if profile_revision is None or profile_revision == "":
        raise AgentHarnessError("empty_profile_revision")
    profile_revision = str(profile_revision)

    # Canonical digest body: contract freeze fields only, key-sorted via
    # content_digest/canonical_json_bytes.
    body = {
        "adapter_id": adapter_id,
        "adapter_version": adapter_version,
        "allowed_tools": list(tools),
        "capability_id": capability_id,
        "context_isolation": context_isolation,
        "credential_ref": credential_ref,
        "effective_selector": effective_selector,
        "fallback_profile_ids": list(fallback),
        "profile_id": profile_id,
        "profile_revision": profile_revision,
        "reasoning_effort": effort,
        "requested_model": requested_model,
        "requested_provider": requested_provider,
        "timeout_seconds": timeout,
        "user_config_name": user_config_name,
    }
    digest = content_digest(body)
    exec_id = "ep_%s" % digest[:32]
    return FrozenExecutionProfile(
        profile_id=body["profile_id"],
        profile_revision=body["profile_revision"],
        capability_id=body["capability_id"],
        requested_provider=body["requested_provider"],
        requested_model=body["requested_model"],
        user_config_name=body["user_config_name"],
        effective_selector=body["effective_selector"],
        reasoning_effort=body["reasoning_effort"],
        timeout_seconds=body["timeout_seconds"],
        allowed_tools=tuple(body["allowed_tools"]),
        context_isolation=body["context_isolation"],
        credential_ref=body["credential_ref"],
        adapter_id=body["adapter_id"],
        adapter_version=body["adapter_version"],
        fallback_profile_ids=tuple(body["fallback_profile_ids"]),
        execution_profile_id=exec_id,
        execution_profile_digest=digest,
    )


def freeze_default_mtplx_profile(run_id: str = "") -> FrozenExecutionProfile:
    return freeze_execution_profile(run_id=run_id)


def freeze_deepseek_flash_max_profile(run_id: str = "") -> FrozenExecutionProfile:
    return freeze_execution_profile(deepseek_profile_layer(), run_id=run_id)


def validate_frozen_profile(frozen: FrozenExecutionProfile) -> None:
    """Recompute identity from frozen fields and fail closed on drift."""
    if not isinstance(frozen, FrozenExecutionProfile):
        raise AgentHarnessError("invalid_frozen_type")
    layer = ExecutionProfileLayer(
        profile_id=frozen.profile_id,
        profile_revision=frozen.profile_revision,
        capability_id=frozen.capability_id,
        requested_provider=frozen.requested_provider,
        requested_model=frozen.requested_model,
        user_config_name=frozen.user_config_name,
        effective_selector=frozen.effective_selector,
        reasoning_effort=frozen.reasoning_effort,
        timeout_seconds=frozen.timeout_seconds,
        allowed_tools=frozen.allowed_tools,
        context_isolation=frozen.context_isolation,
        credential_ref=frozen.credential_ref,
        adapter_id=frozen.adapter_id,
        adapter_version=frozen.adapter_version,
        fallback_profile_ids=frozen.fallback_profile_ids,
    )
    rebuilt = freeze_execution_profile(layer)
    if (
        rebuilt.execution_profile_digest != frozen.execution_profile_digest
        or rebuilt.execution_profile_id != frozen.execution_profile_id
    ):
        raise AgentHarnessError("identity_mismatch")


# ---------------------------------------------------------------------------
# User progress projection (pure; no internal terms)
# ---------------------------------------------------------------------------

_PROGRESS_FORBIDDEN = frozenset(
    {
        "provider",
        "model",
        "selector",
        "effort",
        "adapter",
        "attempt",
        "stdout",
        "stderr",
        "hash",
        "path",
        "mtplx",
        "deepseek",
        "omp",
        "qwen",
        "thinking",
    }
)


def project_user_progress(
    *,
    completed_nodes: int,
    total_nodes: int,
    current_work: str,
    result_available: bool,
) -> Dict[str, Any]:
    """Chinese business-facing progress only. Fail if internal terms leak in."""
    current = str(current_work or "")
    lowered = current.lower()
    for term in _PROGRESS_FORBIDDEN:
        if term in lowered:
            raise AgentHarnessError("progress_leaks_internal_term:%s" % term)
    if total_nodes < 0 or completed_nodes < 0 or completed_nodes > total_nodes:
        raise AgentHarnessError("illegal_progress_counts")
    return {
        "已完成节点": int(completed_nodes),
        "总节点": int(total_nodes),
        "当前工作": current,
        "结果可用": bool(result_available),
    }


# ---------------------------------------------------------------------------
# Catalog / preflight / argv / invoke / receipt
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CatalogModel:
    provider: str
    id: str
    selector: str
    name: str
    context_window: int
    max_tokens: int
    reasoning: bool
    thinking: Tuple[str, ...]
    input: Tuple[str, ...]
    cost: Mapping[str, Any]

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "id": self.id,
            "selector": self.selector,
            "name": self.name,
            "contextWindow": self.context_window,
            "maxTokens": self.max_tokens,
            "reasoning": self.reasoning,
            "thinking": list(self.thinking),
            "input": list(self.input),
            "cost": dict(self.cost),
        }


@dataclass(frozen=True)
class CatalogSnapshot:
    provider: str
    models: Tuple[CatalogModel, ...]
    source: str
    digest: str

    def find_selector(self, selector: str) -> Optional[CatalogModel]:
        for model in self.models:
            if model.selector == selector:
                return model
        return None

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "models": [m.to_public_dict() for m in self.models],
            "source": self.source,
            "digest": self.digest,
        }


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    executable: str
    selector: str
    effort: str
    allowed_tools: Tuple[str, ...]
    timeout_seconds: int
    reasons: Tuple[str, ...] = ()

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "executable": self.executable,
            "selector": self.selector,
            "effort": self.effort,
            "allowed_tools": list(self.allowed_tools),
            "timeout_seconds": self.timeout_seconds,
            "reasons": list(self.reasons),
        }


@dataclass
class InvocationReceipt:
    invocation_id: str
    profile_digest: str
    adapter_id: str
    adapter_version: str
    input_digest: str
    requested_selector: str
    effective_selector: str
    reasoning_effort: str
    allowed_tools: Tuple[str, ...]
    started_at: float
    ended_at: float
    duration_seconds: float
    state: str
    parse_state: str
    expected_units: Tuple[str, ...]
    produced_units: Tuple[str, ...]
    missing_units: Tuple[str, ...]
    stdout_path: str
    stdout_sha256: str
    stderr_summary: str
    exit_code: Optional[int]
    failure_reason: str
    fallback_used: bool
    analysis_complete: bool
    unsupported_operation: str = ""

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "invocation_id": self.invocation_id,
            "profile_digest": self.profile_digest,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "input_digest": self.input_digest,
            "requested_selector": self.requested_selector,
            "effective_selector": self.effective_selector,
            "reasoning_effort": self.reasoning_effort,
            "allowed_tools": list(self.allowed_tools),
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_seconds": self.duration_seconds,
            "state": self.state,
            "parse_state": self.parse_state,
            "expected_units": list(self.expected_units),
            "produced_units": list(self.produced_units),
            "missing_units": list(self.missing_units),
            "stdout_path": self.stdout_path,
            "stdout_sha256": self.stdout_sha256,
            "stderr_summary": self.stderr_summary,
            "exit_code": self.exit_code,
            "failure_reason": self.failure_reason,
            "fallback_used": self.fallback_used,
            "analysis_complete": self.analysis_complete,
            "unsupported_operation": self.unsupported_operation,
        }


def evaluate_analysis_complete(
    *,
    state: str,
    parse_state: str,
    missing_units: Sequence[str],
    profile_digest: str,
    expected_profile_digest: str,
    adapter_id: str,
    expected_adapter_id: str,
    input_digest: str,
    expected_input_digest: str,
) -> bool:
    """Fail-closed completeness gate from the slice-07 contract."""
    if state != "complete":
        return False
    if parse_state != "parsed":
        return False
    if tuple(missing_units):
        return False
    if profile_digest != expected_profile_digest:
        return False
    if adapter_id != expected_adapter_id:
        return False
    if input_digest != expected_input_digest:
        return False
    return True


def _terminate_process_group(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, 15)  # SIGTERM
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.terminate()
        except Exception:
            return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, 9)  # SIGKILL
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.kill()
        except Exception:
            pass


class OmpPrintAdapter:
    """``omp_print_v1``: catalog, preflight, argv, invoke, receipt, coverage."""

    adapter_id = ADAPTER_ID
    adapter_version = ADAPTER_VERSION

    def __init__(
        self,
        *,
        executable: Optional[str] = None,
        catalog_loader: Optional[Any] = None,
        popen_factory: Optional[Any] = None,
    ) -> None:
        self._executable_override = executable
        self._catalog_loader = catalog_loader
        self._popen_factory = popen_factory or subprocess.Popen

    # -- catalog -------------------------------------------------------------

    def resolve_executable(self) -> str:
        if self._executable_override:
            path = Path(self._executable_override)
            if not path.is_file():
                raise AgentHarnessError("executable_missing:%s" % path)
            return str(path)
        found = shutil.which("omp")
        if not found:
            raise AgentHarnessError("executable_not_found:omp")
        return found

    def catalog_snapshot(self, provider: str) -> CatalogSnapshot:
        """Return public model catalog fields only (no env/secrets)."""
        provider = str(provider or "").strip()
        if not provider:
            raise AgentHarnessError("empty_provider")

        if self._catalog_loader is not None:
            raw_obj = self._catalog_loader(provider)
        else:
            executable = self.resolve_executable()
            proc = subprocess.run(
                [executable, "models", provider, "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                shell=False,
                timeout=60,
                check=False,
            )
            if proc.returncode != 0:
                raise AgentHarnessError(
                    "catalog_failed:%s:%s"
                    % (provider, sanitize_text(proc.stderr or proc.stdout or ""))
                )
            try:
                raw_obj = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                raise AgentHarnessError("catalog_invalid_json:%s" % exc) from exc

        models_in = list(raw_obj.get("models") or [])
        models: List[CatalogModel] = []
        for item in models_in:
            if not isinstance(item, Mapping):
                continue
            public = {k: item.get(k) for k in _CATALOG_PUBLIC_FIELDS if k in item}
            thinking = tuple(str(x) for x in (public.get("thinking") or []))
            inputs = tuple(str(x) for x in (public.get("input") or []))
            cost = public.get("cost") or {}
            if not isinstance(cost, Mapping):
                cost = {}
            # Drop any unexpected keys that might carry secrets.
            safe_cost = {
                str(k): cost[k]
                for k in ("input", "output", "cacheRead", "cacheWrite")
                if k in cost
            }
            models.append(
                CatalogModel(
                    provider=str(public.get("provider") or provider),
                    id=str(public.get("id") or ""),
                    selector=str(public.get("selector") or ""),
                    name=str(public.get("name") or ""),
                    context_window=int(public.get("contextWindow") or 0),
                    max_tokens=int(public.get("maxTokens") or 0),
                    reasoning=bool(public.get("reasoning")),
                    thinking=thinking,
                    input=inputs,
                    cost=safe_cost,
                )
            )
        payload = {
            "provider": provider,
            "models": [m.to_public_dict() for m in models],
            "source": "omp models %s --json" % provider,
        }
        digest = content_digest(payload)
        return CatalogSnapshot(
            provider=provider,
            models=tuple(models),
            source=payload["source"],
            digest=digest,
        )

    # -- preflight -----------------------------------------------------------

    def preflight(
        self,
        profile: FrozenExecutionProfile,
        *,
        catalog: Optional[CatalogSnapshot] = None,
        extra_allowed_tools: Optional[Sequence[str]] = None,
    ) -> PreflightResult:
        reasons: List[str] = []
        executable = ""
        try:
            validate_frozen_profile(profile)
        except AgentHarnessError as exc:
            reasons.append(str(exc))
        try:
            executable = self.resolve_executable()
        except AgentHarnessError as exc:
            reasons.append(str(exc))

        if profile.adapter_id != ADAPTER_ID:
            reasons.append("adapter_id_mismatch")
        if profile.timeout_seconds <= 0:
            reasons.append("illegal_timeout")
        if profile.reasoning_effort not in ALLOWED_THINKING_LEVELS:
            reasons.append("illegal_effort")
        if not profile.capability_id:
            reasons.append("empty_capability")
        if not profile.allowed_tools:
            reasons.append("empty_allowed_tools")

        tool_ceiling = set(DEFAULT_ALLOWED_TOOLS)
        if extra_allowed_tools:
            tool_ceiling |= set(extra_allowed_tools)
        for tool in profile.allowed_tools:
            if tool not in tool_ceiling:
                reasons.append("tool_out_of_whitelist:%s" % tool)

        snap = catalog
        if snap is None and not reasons:
            try:
                snap = self.catalog_snapshot(profile.requested_provider)
            except AgentHarnessError as exc:
                reasons.append(str(exc))

        if snap is not None:
            if snap.provider != profile.requested_provider:
                reasons.append("catalog_provider_mismatch")
            model = snap.find_selector(profile.effective_selector)
            if model is None:
                reasons.append("selector_not_in_catalog")
            else:
                if model.provider != profile.requested_provider:
                    reasons.append("catalog_model_provider_mismatch")
                if model.id != profile.requested_model:
                    reasons.append("catalog_model_id_mismatch")
                if profile.reasoning_effort not in model.thinking:
                    reasons.append(
                        "effort_unsupported_by_catalog:%s" % profile.reasoning_effort
                    )

        ok = not reasons
        return PreflightResult(
            ok=ok,
            executable=executable,
            selector=profile.effective_selector,
            effort=profile.reasoning_effort,
            allowed_tools=profile.allowed_tools,
            timeout_seconds=profile.timeout_seconds,
            reasons=tuple(reasons),
        )

    # -- argv ----------------------------------------------------------------

    def build_start_command(
        self,
        profile: FrozenExecutionProfile,
        *,
        executable: Optional[str] = None,
    ) -> List[str]:
        """Return argv array (no shell). Prompt is never placed on argv."""
        exe = executable or self.resolve_executable()
        tools_csv = ",".join(profile.allowed_tools)
        argv = [
            exe,
            "--model",
            profile.effective_selector,
            "--thinking",
            profile.reasoning_effort,
            "--mode",
            "json",
            "--print",
            "--no-session",
            "--no-skills",
            "--no-rules",
            "--tools",
            tools_csv,
            "--max-time",
            str(int(profile.timeout_seconds)),
        ]
        # Fail closed if any argv token looks like a prompt dump or shell glue.
        joined = " ".join(argv)
        if "&&" in joined or "|" in joined or ";" in joined:
            raise AgentHarnessError("argv_contains_shell_metachar")
        return argv

    # -- lifecycle ops this print adapter does not support -------------------

    def continue_session(self, *_args: Any, **_kwargs: Any) -> Dict[str, str]:
        return {"status": "unsupported", "operation": "continue"}

    def resume_session(self, *_args: Any, **_kwargs: Any) -> Dict[str, str]:
        return {"status": "unsupported", "operation": "resume"}

    def cancel(self, *_args: Any, **_kwargs: Any) -> Dict[str, str]:
        # Print invocation is one-shot; without an active handle, cancel is
        # unsupported (do not fabricate success).
        return {"status": "unsupported", "operation": "cancel"}

    # -- invoke + receipt ----------------------------------------------------

    def invoke(
        self,
        profile: FrozenExecutionProfile,
        prompt: str,
        *,
        output_dir: Union[str, Path],
        expected_units: Sequence[str],
        catalog: Optional[CatalogSnapshot] = None,
        invocation_id: Optional[str] = None,
        preflight_result: Optional[PreflightResult] = None,
    ) -> InvocationReceipt:
        """Run one print invocation; stdin=prompt; stdout/stderr separated."""
        input_digest = sha256_hex(prompt)
        inv_id = invocation_id or ("inv_%s" % content_digest(
            {
                "profile": profile.execution_profile_digest,
                "input": input_digest,
                "adapter": ADAPTER_ID,
            }
        )[:24])
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", inv_id):
            raise AgentHarnessError("invalid_invocation_id")
        normalized_expected = tuple(str(unit) for unit in expected_units)
        if (
            not normalized_expected
            or any(not unit or unit != unit.strip() for unit in normalized_expected)
            or len(set(normalized_expected)) != len(normalized_expected)
        ):
            raise AgentHarnessError("invalid_expected_units")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        pf = preflight_result or self.preflight(profile, catalog=catalog)
        binding_reasons: List[str] = []
        try:
            validate_frozen_profile(profile)
        except AgentHarnessError as exc:
            binding_reasons.append(str(exc))
        if pf.selector != profile.effective_selector:
            binding_reasons.append("preflight_selector_mismatch")
        if pf.effort != profile.reasoning_effort:
            binding_reasons.append("preflight_effort_mismatch")
        if tuple(pf.allowed_tools) != profile.allowed_tools:
            binding_reasons.append("preflight_tools_mismatch")
        if pf.timeout_seconds != profile.timeout_seconds:
            binding_reasons.append("preflight_timeout_mismatch")
        if pf.ok and (not pf.executable or not Path(pf.executable).is_file()):
            binding_reasons.append("preflight_executable_invalid")
        started = time.time()
        if not pf.ok or binding_reasons:
            ended = time.time()
            return self._receipt(
                invocation_id=inv_id,
                profile=profile,
                input_digest=input_digest,
                started=started,
                ended=ended,
                state="failed",
                parse_state="unparsed",
                expected_units=normalized_expected,
                produced_units=(),
                stdout_path="",
                stdout_sha256=sha256_hex(b""),
                stderr_summary=sanitize_text(
                    ";".join(tuple(pf.reasons) + tuple(binding_reasons))
                ),
                exit_code=None,
                failure_reason="preflight_failed",
            )

        argv = self.build_start_command(profile, executable=pf.executable)
        stdout_path = output_dir / ("%s.stdout.json" % inv_id)
        timed_out = False
        exit_code: Optional[int] = None
        stdout_bytes = b""
        stderr_text = ""

        try:
            process = self._popen_factory(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                close_fds=True,
                start_new_session=True,
            )
        except OSError as exc:
            ended = time.time()
            return self._receipt(
                invocation_id=inv_id,
                profile=profile,
                input_digest=input_digest,
                started=started,
                ended=ended,
                state="failed",
                parse_state="unparsed",
                expected_units=normalized_expected,
                produced_units=(),
                stdout_path="",
                stdout_sha256=sha256_hex(b""),
                stderr_summary=sanitize_text(str(exc)),
                exit_code=None,
                failure_reason="spawn_failed",
            )

        try:
            out_b, err_b = process.communicate(
                input=prompt.encode("utf-8"),
                timeout=profile.timeout_seconds,
            )
            stdout_bytes = out_b or b""
            stderr_text = (err_b or b"").decode("utf-8", errors="replace")
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process_group(process)
            try:
                out_b, err_b = process.communicate(timeout=5)
            except Exception:
                out_b, err_b = b"", b""
            stdout_bytes = out_b or b""
            stderr_text = (err_b or b"").decode("utf-8", errors="replace")
            exit_code = process.returncode

        ended = time.time()
        stdout_path.write_bytes(stdout_bytes)
        stdout_sha = sha256_hex(stdout_bytes)
        stderr_summary = sanitize_text(stderr_text)

        state, parse_state, produced, failure_reason = self._classify_output(
            stdout_bytes=stdout_bytes,
            exit_code=exit_code,
            timed_out=timed_out,
            expected_units=normalized_expected,
        )

        return self._receipt(
            invocation_id=inv_id,
            profile=profile,
            input_digest=input_digest,
            started=started,
            ended=ended,
            state=state,
            parse_state=parse_state,
            expected_units=normalized_expected,
            produced_units=produced,
            stdout_path=str(stdout_path),
            stdout_sha256=stdout_sha,
            stderr_summary=stderr_summary,
            exit_code=exit_code,
            failure_reason=failure_reason,
        )

    def _classify_output(
        self,
        *,
        stdout_bytes: bytes,
        exit_code: Optional[int],
        timed_out: bool,
        expected_units: Sequence[str],
    ) -> Tuple[str, str, Tuple[str, ...], str]:
        if timed_out:
            return "timed_out", "unparsed", (), "timed_out"

        if exit_code != 0 and not stdout_bytes:
            return "failed", "unparsed", (), "nonzero_exit"

        if not stdout_bytes:
            return "failed", "unparsed", (), "empty_stdout"

        text = stdout_bytes.decode("utf-8", errors="replace")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            # OMP ``--mode json`` emits NDJSON event lines, not one object.
            payload = self._extract_payload_from_omp_jsonl(text)
            if payload is None:
                if exit_code != 0:
                    return "failed", "invalid", (), "invalid_json_nonzero_exit"
                return "failed", "invalid", (), "invalid_json"

        if self._looks_like_omp_event(payload):
            payload = self._extract_payload_from_omp_jsonl(text)
            if payload is None:
                return "failed", "invalid", (), "omp_event_without_payload"

        if not isinstance(payload, Mapping):
            return "failed", "invalid", (), "json_not_object"

        # Coverage units may be declared by the caller; produced units come from
        # an explicit list on the payload when present, else from top-level keys.
        if "produced_units" in payload and isinstance(payload["produced_units"], list):
            produced = tuple(str(x) for x in payload["produced_units"])
        else:
            produced = tuple(sorted(str(k) for k in payload.keys()))

        status_hint = str(payload.get("status") or payload.get("state") or "").lower()
        if status_hint in {"partial", "truncated", "failed", "not_evaluable"}:
            return status_hint, "parsed", produced, status_hint or "status_hint"

        missing = tuple(u for u in expected_units if u not in produced)
        if missing:
            # Coverage gap is fail-closed: never analysis_complete.
            return "partial", "parsed", produced, "coverage_gap"

        if exit_code != 0:
            return "failed", "parsed", produced, "nonzero_exit"

        return "complete", "parsed", produced, ""

    @staticmethod
    def _extract_payload_from_omp_jsonl(text: str) -> Optional[Dict[str, Any]]:
        """Parse OMP print NDJSON and recover the assistant JSON object payload."""
        assistant_chunks: List[str] = []
        parsed_any = False
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            parsed_any = True
            if not isinstance(event, Mapping):
                continue
            message = event.get("message")
            if not isinstance(message, Mapping):
                continue
            if message.get("role") != "assistant":
                continue
            content = message.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, Mapping) and part.get("type") == "text":
                        assistant_chunks.append(str(part.get("text") or ""))
            elif isinstance(content, str):
                assistant_chunks.append(content)
        if not parsed_any:
            return None
        if not any(chunk.strip() for chunk in assistant_chunks):
            # Stream parsed but no assistant text yet — treat as empty coverage.
            return {"produced_units": []}
        # Streaming may repeat or revise an assistant message. Only a whole
        # assistant chunk (or a whole fenced JSON chunk) is authoritative, and
        # the last valid object wins. Incidental braces in prose are ignored.
        parsed_objects: List[Dict[str, Any]] = []
        for raw_chunk in assistant_chunks:
            chunk = (raw_chunk or "").strip()
            if not chunk:
                continue
            candidates = [chunk]
            fence = re.fullmatch(
                r"```(?:json)?\s*(\{.*\})\s*```", chunk, re.DOTALL
            )
            if fence:
                candidates.insert(0, fence.group(1))
            parsed: Optional[Dict[str, Any]] = None
            for candidate in candidates:
                try:
                    obj = json.loads(candidate)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, Mapping):
                    parsed = dict(obj)
                    break
            if parsed is not None:
                parsed_objects.append(parsed)
        if parsed_objects:
            return parsed_objects[-1]
        return {"produced_units": [], "assistant_text_present": True}

    @staticmethod
    def _looks_like_omp_event(payload: Any) -> bool:
        if not isinstance(payload, Mapping):
            return False
        event_type = str(payload.get("type") or "")
        if event_type in {
            "session",
            "agent_start",
            "agent_end",
            "turn_start",
            "turn_end",
            "message_start",
            "message_update",
            "message_end",
            "notice",
        }:
            return True
        message = payload.get("message")
        return isinstance(message, Mapping) and "role" in message

    def _receipt(
        self,
        *,
        invocation_id: str,
        profile: FrozenExecutionProfile,
        input_digest: str,
        started: float,
        ended: float,
        state: str,
        parse_state: str,
        expected_units: Sequence[str],
        produced_units: Sequence[str],
        stdout_path: str,
        stdout_sha256: str,
        stderr_summary: str,
        exit_code: Optional[int],
        failure_reason: str,
        unsupported_operation: str = "",
    ) -> InvocationReceipt:
        if state not in _RECEIPT_STATES:
            state = "not_evaluable"
        if parse_state not in _PARSE_STATES:
            parse_state = "invalid"
        missing = tuple(u for u in expected_units if u not in set(produced_units))
        complete = evaluate_analysis_complete(
            state=state,
            parse_state=parse_state,
            missing_units=missing,
            profile_digest=profile.execution_profile_digest,
            expected_profile_digest=profile.execution_profile_digest,
            adapter_id=ADAPTER_ID,
            expected_adapter_id=ADAPTER_ID,
            input_digest=input_digest,
            expected_input_digest=input_digest,
        )
        # Hard fail-closed: non-complete states never flip analysis_complete.
        if state in {"partial", "truncated", "failed", "timed_out", "not_evaluable"}:
            complete = False
        return InvocationReceipt(
            invocation_id=invocation_id,
            profile_digest=profile.execution_profile_digest,
            adapter_id=ADAPTER_ID,
            adapter_version=ADAPTER_VERSION,
            input_digest=input_digest,
            requested_selector=profile.effective_selector,
            effective_selector=profile.effective_selector,
            reasoning_effort=profile.reasoning_effort,
            allowed_tools=profile.allowed_tools,
            started_at=started,
            ended_at=ended,
            duration_seconds=max(0.0, ended - started),
            state=state,
            parse_state=parse_state,
            expected_units=tuple(expected_units),
            produced_units=tuple(produced_units),
            missing_units=missing,
            stdout_path=stdout_path,
            stdout_sha256=stdout_sha256,
            stderr_summary=stderr_summary,
            exit_code=exit_code,
            failure_reason=failure_reason,
            fallback_used=False,
            analysis_complete=complete,
            unsupported_operation=unsupported_operation,
        )


# ---------------------------------------------------------------------------
# Synthetic helpers for offline tests (no real model call)
# ---------------------------------------------------------------------------


def synthetic_catalog_for_provider(provider: str) -> Dict[str, Any]:
    """Minimal public catalog fixtures matching OMP 18.0.7 observed shapes."""
    if provider == "mtplx":
        return {
            "models": [
                {
                    "provider": "mtplx",
                    "id": "Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality",
                    "selector": EFFECTIVE_SELECTOR_MTPLX,
                    "name": "Qwen 3.8 27B MTPLX Full ID",
                    "contextWindow": 262144,
                    "maxTokens": 32768,
                    "reasoning": True,
                    "thinking": ["low", "medium", "xhigh"],
                    "input": ["text"],
                    "cost": {
                        "input": 0,
                        "output": 0,
                        "cacheRead": 0,
                        "cacheWrite": 0,
                    },
                }
            ]
        }
    if provider == "deepseek":
        return {
            "models": [
                {
                    "provider": "deepseek",
                    "id": "deepseek-v4-flash",
                    "selector": EFFECTIVE_SELECTOR_DEEPSEEK,
                    "name": "DeepSeek V4 Flash",
                    "contextWindow": 1000000,
                    "maxTokens": 384000,
                    "reasoning": True,
                    "thinking": ["low", "high", "max"],
                    "input": ["text"],
                    "cost": {
                        "input": 0.14,
                        "output": 0.28,
                        "cacheRead": 0.0028,
                        "cacheWrite": 0,
                    },
                }
            ]
        }
    return {"models": []}


__all__ = [
    "ADAPTER_ID",
    "ADAPTER_VERSION",
    "ALIAS_REGISTRY",
    "AgentHarnessError",
    "CatalogModel",
    "CatalogSnapshot",
    "ExecutionProfileLayer",
    "FrozenExecutionProfile",
    "InvocationReceipt",
    "OmpPrintAdapter",
    "PreflightResult",
    "PROFILE_DEFAULT_ID",
    "PROFILE_DEEPSEEK_ID",
    "USER_NAME_MTPLX",
    "USER_NAME_DEEPSEEK",
    "EFFECTIVE_SELECTOR_MTPLX",
    "EFFECTIVE_SELECTOR_DEEPSEEK",
    "alias_map",
    "canonical_json_bytes",
    "content_digest",
    "deepseek_profile_layer",
    "evaluate_analysis_complete",
    "freeze_deepseek_flash_max_profile",
    "freeze_default_mtplx_profile",
    "freeze_execution_profile",
    "list_registered_profile_ids",
    "merge_profile_layers",
    "project_user_progress",
    "refuse_auto_fallback",
    "registered_profile_layer",
    "resolve_alias",
    "sanitize_text",
    "sha256_hex",
    "synthetic_catalog_for_provider",
    "validate_frozen_profile",
]
