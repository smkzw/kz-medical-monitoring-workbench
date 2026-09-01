"""Synthetic/offline R7 Slice-07C-3/4 and Slice-08A registry.

The registry is the durable, project-scoped boundary for product
``prepare-and-start`` requests and the single atomic result-publication row.
It reserves one internal run and one opaque public navigation token before
preparation or background start work runs.  Publication identity is frozen
independently from completion-dependent receipt and authority facts.

This module intentionally uses only the Python standard library.  It does not
prepare manifests, bind runs, start workers, build authority packets, or open
a service.  Those operations consume this registry through the small durable
state API below.
"""

from __future__ import annotations

import datetime as _datetime
import hashlib
import json
import math
import sqlite3
import threading
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Tuple, Union
from uuid import uuid4

from .continuity import (
    CarryForwardItem,
    CarryForwardPlan,
    PlanValidationError,
    validate_carry_forward_plan,
)

from .launch_schema import (
    BASE_DDL as _BASE_DDL,
    CONTINUITY_DDL as _CONTINUITY_DDL,
    CONTINUITY_INDEX_DDL as _CONTINUITY_INDEX_DDL,
    CONTINUITY_ITEMS_DDL as _CONTINUITY_ITEMS_DDL,
    CONTINUITY_PLANS_DDL as _CONTINUITY_PLANS_DDL,
    LAUNCH_DDL as _DDL,
    PUBLICATION_DDL as _PUBLICATION_DDL,
    RESULT_CONTEXT_INDEX_DDL as _RESULT_CONTEXT_INDEX_DDL,
)

SCHEMA_VERSION_V1 = "mm-r7-slice07c2-launch-registry-v1"
SCHEMA_VERSION_V2 = "mm-r7-slice07c3-launch-registry-v2"
SCHEMA_VERSION_V3 = "mm-r7-slice08a-launch-registry-v3"
SCHEMA_VERSION_V4 = "mm-r7-slice08b-launch-registry-v4"
SCHEMA_VERSION = SCHEMA_VERSION_V4
LAUNCH_REGISTRY_DB_NAME = "launch_registry.sqlite3"
BUSY_TIMEOUT_MS = 10_000
DEFAULT_HISTORY_LIMIT = 50
MAX_HISTORY_LIMIT = 200

PUBLICATION_REVISION = 1
PUBLICATION_STATE_PUBLISHING = "publishing"
PUBLICATION_STATE_AVAILABLE = "available"
PUBLICATION_STATE_RECOVERABLE_FAILED = "recoverable_failed"
PUBLICATION_STATE_BLOCKED = "blocked"
PUBLICATION_STATE_VALUES = (
    PUBLICATION_STATE_PUBLISHING,
    PUBLICATION_STATE_AVAILABLE,
    PUBLICATION_STATE_RECOVERABLE_FAILED,
    PUBLICATION_STATE_BLOCKED,
)

# Short aliases keep route adapters readable while the explicit names remain
# the canonical contract surface.
PUBLICATION_PUBLISHING = PUBLICATION_STATE_PUBLISHING
PUBLICATION_AVAILABLE = PUBLICATION_STATE_AVAILABLE
PUBLICATION_RECOVERABLE_FAILED = PUBLICATION_STATE_RECOVERABLE_FAILED
PUBLICATION_BLOCKED = PUBLICATION_STATE_BLOCKED
RESULT_PUBLICATION_STATE_VALUES = PUBLICATION_STATE_VALUES
PUBLICATION_SCHEMA_VERSION = SCHEMA_VERSION
RESULT_PUBLICATION_REVISION = PUBLICATION_REVISION
RESULT_PUBLICATION_PUBLISHING = PUBLICATION_STATE_PUBLISHING
RESULT_PUBLICATION_AVAILABLE = PUBLICATION_STATE_AVAILABLE
RESULT_PUBLICATION_RECOVERABLE_FAILED = PUBLICATION_STATE_RECOVERABLE_FAILED
RESULT_PUBLICATION_BLOCKED = PUBLICATION_STATE_BLOCKED

# Slice-08A continuity plans are persisted independently from the existing
# ResultPublication row.  Their status is a storage gate, not a second
# publication or risk lifecycle.
CONTINUITY_PLAN_STATE_STAGING = "staging"
CONTINUITY_PLAN_STATE_VERIFIED = "verified"
CONTINUITY_PLAN_STATE_PUBLISHED = "published"
CONTINUITY_PLAN_STATE_BLOCKED = "blocked"
CONTINUITY_PLAN_STATE_VALUES = (
    CONTINUITY_PLAN_STATE_STAGING,
    CONTINUITY_PLAN_STATE_VERIFIED,
    CONTINUITY_PLAN_STATE_PUBLISHED,
    CONTINUITY_PLAN_STATE_BLOCKED,
)
CONTINUITY_PLAN_STAGING = CONTINUITY_PLAN_STATE_STAGING
CONTINUITY_PLAN_VERIFIED = CONTINUITY_PLAN_STATE_VERIFIED
CONTINUITY_PLAN_PUBLISHED = CONTINUITY_PLAN_STATE_PUBLISHED
CONTINUITY_PLAN_BLOCKED = CONTINUITY_PLAN_STATE_BLOCKED
CONTINUITY_PLAN_STATUS_STAGING = CONTINUITY_PLAN_STATE_STAGING
CONTINUITY_PLAN_STATUS_VERIFIED = CONTINUITY_PLAN_STATE_VERIFIED
CONTINUITY_PLAN_STATUS_PUBLISHED = CONTINUITY_PLAN_STATE_PUBLISHED
CONTINUITY_PLAN_STATUS_BLOCKED = CONTINUITY_PLAN_STATE_BLOCKED
CONTINUITY_PLAN_STATUS_VALUES = CONTINUITY_PLAN_STATE_VALUES
_CONTINUITY_ALLOWED_TRANSITIONS = {
    CONTINUITY_PLAN_STATE_STAGING: frozenset(
        {
            CONTINUITY_PLAN_STATE_STAGING,
            CONTINUITY_PLAN_STATE_VERIFIED,
            CONTINUITY_PLAN_STATE_BLOCKED,
        }
    ),
    CONTINUITY_PLAN_STATE_VERIFIED: frozenset(
        {CONTINUITY_PLAN_STATE_VERIFIED, CONTINUITY_PLAN_STATE_BLOCKED}
    ),
    CONTINUITY_PLAN_STATE_PUBLISHED: frozenset(
        {CONTINUITY_PLAN_STATE_PUBLISHED}
    ),
    CONTINUITY_PLAN_STATE_BLOCKED: frozenset(
        {CONTINUITY_PLAN_STATE_BLOCKED, CONTINUITY_PLAN_STATE_STAGING}
    ),
}

MODE_DAILY = "daily"
MODE_PRE_LOCK = "pre_lock"
MODE_POST_LOCK_PRE_CFDI = "post_lock_pre_cfdi"
SUPPORTED_MODES = (MODE_DAILY, MODE_PRE_LOCK, MODE_POST_LOCK_PRE_CFDI)

BASIS_FULL = "full"
BASIS_INCREMENTAL = "incremental"
SUPPORTED_EXECUTION_BASES = (BASIS_FULL, BASIS_INCREMENTAL)

STATE_WAITING_START = "waiting_start"
STATE_RUNNING = "running"
STATE_STOPPING = "stopping"
STATE_INTERRUPTED_RESUMABLE = "interrupted_resumable"
STATE_COMPLETED = "completed"
STATE_ENDED_INCOMPLETE = "ended_incomplete"
STATE_FAILED = "failed"
RUN_STATE_VALUES = (
    STATE_WAITING_START,
    STATE_RUNNING,
    STATE_STOPPING,
    STATE_INTERRUPTED_RESUMABLE,
    STATE_COMPLETED,
    STATE_ENDED_INCOMPLETE,
    STATE_FAILED,
)

_MODE_TEXT = {
    MODE_DAILY: "日常监查",
    MODE_PRE_LOCK: "锁库前监查",
    MODE_POST_LOCK_PRE_CFDI: "核查前监查",
}

_DEFAULT_MAIN_ACTION = "查看本次进度"
_RESULT_MAIN_ACTION = "查看本次结果"
RESULT_CONTEXT_TOKEN_PREFIX = "result-context:"

_STATUS_TEXT = {
    STATE_WAITING_START: "等待开始医学监查",
    STATE_RUNNING: "医学监查进行中",
    STATE_STOPPING: "正在停止医学监查",
    STATE_INTERRUPTED_RESUMABLE: "已停止，可继续",
    STATE_ENDED_INCOMPLETE: "本次监查已结束，部分工作未完成",
    STATE_FAILED: "本次监查未完成",
}


def _run_status_text(state: str, result_available: bool) -> str:
    if state == STATE_COMPLETED:
        return "结果已整理完成" if result_available else "分析已结束，结果整理未完成"
    return _STATUS_TEXT[state]


_ERROR_MESSAGES = {
    "store_closed": "运行登记存储已关闭。",
    "unsupported_schema_version": "运行登记存储架构版本不受支持。",
    "invalid_project_id": "医学监查项目标识无效。",
    "invalid_idempotency_key": "幂等请求标识无效。",
    "invalid_mode": "不支持的监查运行模式。",
    "invalid_execution_basis": "不支持的运行基准。",
    "invalid_snapshot_token": "当前数据快照标识无效。",
    "invalid_baseline_token": "比较基线标识无效。",
    "invalid_data_cutoff": "数据截止点无效。",
    "invalid_comparison_range": "比较范围无效。",
    "invalid_manifest_digest": "运行范围摘要无效。",
    "invalid_run_state": "运行状态无效。",
    "invalid_result_state": "结果可用状态无效。",
    "illegal_state_transition": "本次监查不能从当前状态变更到目标状态。",
    "invalid_history_limit": "历史记录数量限制无效。",
    "run_not_found": "未找到指定的监查运行。",
    "public_run_not_found": "未找到指定的监查运行。",
    "idempotency_conflict": "同一幂等请求标识对应的请求内容冲突，拒绝覆盖。",
    "in_flight_conflict": "当前已有监查正在进行，请先查看本次进度",
    "publication_not_found": "未找到指定的结果发布记录。",
    "invalid_publication_state": "结果发布状态无效。",
    "invalid_publication_revision": "结果发布版本无效。",
    "invalid_publication_fingerprint": "结果发布指纹无效。",
    "invalid_publication_metadata": "结果发布绑定信息无效。",
    "publication_cas_conflict": "结果发布状态已变化，拒绝覆盖。",
    "illegal_publication_transition": "结果发布不能从当前状态变更到目标状态。",
    "run_not_completed": "监查运行尚未完成，不能发布结果。",
    "invalid_continuity_plan": "连续性计划无效，拒绝保存。",
    "continuity_plan_not_found": "未找到指定的连续性计划。",
    "continuity_item_not_found": "未找到指定的连续性条目。",
    "continuity_plan_conflict": "同一目标运行对应的连续性计划内容冲突，拒绝覆盖。",
    "continuity_plan_cas_conflict": "连续性计划状态已变化，拒绝覆盖。",
    "continuity_plan_not_verified": "连续性计划尚未完成核对，不能发布结果。",
    "illegal_continuity_transition": "连续性计划不能从当前状态变更到目标状态。",
    "continuity_publication_conflict": "连续性计划与结果发布事实不一致，拒绝发布。",
}

class LaunchRegistryError(ValueError):
    """Fail-closed launch-registry error with a stable code and Chinese text."""

    def __init__(self, code: str, message: Optional[str] = None) -> None:
        self.code = str(code)
        self.message = message if message is not None else _ERROR_MESSAGES.get(
            self.code, "运行登记请求未能完成。"
        )
        super().__init__(f"{self.code}: {self.message}")

    def as_error_body(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class IdempotencyConflictError(LaunchRegistryError):
    """Raised when one project/key is reused for different normalized input."""

    def __init__(self) -> None:
        super().__init__("idempotency_conflict")


def _required_text(value: Any, code: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise LaunchRegistryError(code)
    return value


def _optional_text(value: Any, code: str) -> Optional[str]:
    if value is None:
        return None
    return _required_text(value, code)


def _normalize_result_context_token(
    value: Any, code: str = "invalid_publication_metadata"
) -> Optional[str]:
    if value is None:
        return None
    token = _required_text(value, code)
    if not token.startswith(RESULT_CONTEXT_TOKEN_PREFIX) or len(
        token
    ) <= len(RESULT_CONTEXT_TOKEN_PREFIX):
        raise LaunchRegistryError(code)
    return token

def _jsonable(value: Any) -> Any:
    """Return deterministic JSON-compatible data or fail closed."""
    if isinstance(value, Enum):
        return _jsonable(value.value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite value")
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("mapping keys must be strings")
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    raise TypeError(f"unsupported value: {type(value).__name__}")


def canonical_json(value: Any) -> str:
    return json.dumps(
        _jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def derive_continuity_plan_id(plan: CarryForwardPlan) -> str:
    """Return the deterministic foreign-key identity for one plan."""
    if not isinstance(plan, CarryForwardPlan):
        raise LaunchRegistryError("invalid_continuity_plan")
    return (
        "r7-plan-"
        + content_digest(
            {
                "project_id": plan.project_id,
                "target_run_id": plan.target_run_id,
                "plan_digest": plan.plan_digest,
            }
        )[:32]
    )

def _normalize_publication_revision(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value != PUBLICATION_REVISION:
        raise LaunchRegistryError("invalid_publication_revision")
    return value


def _normalize_nonnegative_int(value: Any, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise LaunchRegistryError(code)
    return value


def _normalize_optional_positive_int(value: Any, code: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LaunchRegistryError(code)
    return value


def _normalize_publication_tokens(
    value: Optional[Iterable[Any]],
    *,
    code: str = "invalid_publication_metadata",
    allow_single_text: bool = True,
) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        if not allow_single_text:
            raise LaunchRegistryError(code)
        values: Iterable[Any] = (value,)
    else:
        try:
            values = value
        except TypeError as exc:
            raise LaunchRegistryError(code) from exc
    try:
        tokens = tuple(_required_text(item, code) for item in values)
    except (TypeError, ValueError) as exc:
        raise LaunchRegistryError(code) from exc
    return tuple(sorted(set(tokens)))




def _json_token_list(value: Iterable[str]) -> str:
    return json.dumps(list(value), ensure_ascii=False, separators=(",", ":"))


def _decode_token_list(value: Any, code: str = "store_closed") -> Tuple[str, ...]:
    try:
        decoded = json.loads(str(value))
    except (TypeError, json.JSONDecodeError) as exc:
        raise LaunchRegistryError(code) from exc
    if not isinstance(decoded, list):
        raise LaunchRegistryError(code)
    try:
        tokens = tuple(_required_text(item, code) for item in decoded)
    except LaunchRegistryError as exc:
        raise LaunchRegistryError(code) from exc
    if tokens != tuple(sorted(set(tokens))):
        raise LaunchRegistryError(code)
    return tokens


def _normalize_publication_object(
    value: Any, *, code: str = "invalid_publication_metadata"
) -> dict[str, Any]:
    if value is None:
        return {}
    candidate: Any = value
    if isinstance(value, str):
        try:
            candidate = json.loads(value)
        except json.JSONDecodeError as exc:
            raise LaunchRegistryError(code) from exc
    if not isinstance(candidate, Mapping):
        raise LaunchRegistryError(code)
    try:
        normalized = _jsonable(candidate)
    except (TypeError, ValueError) as exc:
        raise LaunchRegistryError(code) from exc
    if not isinstance(normalized, dict):
        raise LaunchRegistryError(code)
    return normalized


def _decode_publication_object(value: Any, code: str = "store_closed") -> dict[str, Any]:
    try:
        decoded = json.loads(str(value))
    except (TypeError, json.JSONDecodeError) as exc:
        raise LaunchRegistryError(code) from exc
    if not isinstance(decoded, dict):
        raise LaunchRegistryError(code)
    try:
        normalized = _jsonable(decoded)
    except (TypeError, ValueError) as exc:
        raise LaunchRegistryError(code) from exc
    if not isinstance(normalized, dict):
        raise LaunchRegistryError(code)
    return normalized
def _manifest_work_unit_mapping(
    value: Any, *, code: str = "invalid_publication_metadata"
) -> Tuple[Tuple[str, bool], ...]:
    """Extract the frozen ``work_unit_id -> mandatory`` identity.

    Publication callers may provide either the compact mapping used by the
    offline harness (``{"unit-a": True}``) or an object with a
    ``work_units`` mapping/list.  The stored object remains the caller's
    canonical JSON; this helper is only for deterministic denominator and
    setup/runtime equality checks.
    """
    normalized = _normalize_publication_object(value, code=code)
    if not normalized:
        return ()
    candidate: Any = normalized
    if "work_units" in normalized:
        candidate = normalized["work_units"]
    elif "work_unit_identity" in normalized:
        candidate = normalized["work_unit_identity"]
    elif "units" in normalized:
        candidate = normalized["units"]

    entries: list[Tuple[str, bool]] = []
    if isinstance(candidate, Mapping):
        for work_unit_id, raw_mandatory in candidate.items():
            if not isinstance(work_unit_id, str):
                raise LaunchRegistryError(code)
            if isinstance(raw_mandatory, bool):
                mandatory = raw_mandatory
            elif isinstance(raw_mandatory, Mapping):
                mandatory = raw_mandatory.get("mandatory")
                if not isinstance(mandatory, bool):
                    raise LaunchRegistryError(code)
            else:
                raise LaunchRegistryError(code)
            entries.append((_required_text(work_unit_id, code), mandatory))
    elif isinstance(candidate, (list, tuple)):
        for item in candidate:
            if isinstance(item, Mapping):
                work_unit_id = item.get("work_unit_id", item.get("id"))
                mandatory = item.get("mandatory")
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                work_unit_id, mandatory = item
            else:
                raise LaunchRegistryError(code)
            if not isinstance(mandatory, bool):
                raise LaunchRegistryError(code)
            entries.append((_required_text(work_unit_id, code), mandatory))
    else:
        raise LaunchRegistryError(code)

    if len({work_unit_id for work_unit_id, _ in entries}) != len(entries):
        raise LaunchRegistryError(code)
    return tuple(sorted(entries))


def _canonical_setup_manifest_identity(value: Any) -> dict[str, Any]:
    """Normalize accepted setup-manifest shapes for request fingerprints."""
    normalized = _normalize_publication_object(value)
    if not normalized:
        return {}
    try:
        entries = _manifest_work_unit_mapping(normalized)
    except LaunchRegistryError as exc:
        raise LaunchRegistryError("invalid_publication_metadata") from exc
    if not entries:
        raise LaunchRegistryError("invalid_publication_metadata")
    # ``entries`` is sorted by work-unit id, making the resulting mapping
    # independent of source mapping insertion order and list order.
    return {work_unit_id: mandatory for work_unit_id, mandatory in entries}


def _normalize_rule_tokens(value: Optional[Iterable[str]]) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise LaunchRegistryError("invalid_rule_token")
    try:
        tokens = tuple(_required_text(item, "invalid_rule_token") for item in value)
    except TypeError as exc:
        raise LaunchRegistryError("invalid_rule_token") from exc
    # A rule option is a set selection.  Sorting and de-duplicating makes a
    # browser retry with a different checkbox order the same request.
    return tuple(sorted(set(tokens)))


def _normalize_comparison_range(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _required_text(value, "invalid_comparison_range")
    if isinstance(value, Mapping):
        for key in ("text", "description", "label", "scope_description"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip() == candidate and candidate:
                return candidate
    raise LaunchRegistryError("invalid_comparison_range")


def normalize_request(
    *,
    project_id: str,
    idempotency_key: str,
    mode: str,
    execution_basis: str,
    current_snapshot_token: str,
    baseline_token: Optional[str] = None,
    rule_tokens: Optional[Iterable[str]] = None,
    risk_rule_tokens: Optional[Iterable[str]] = None,
) -> "LaunchRequest":
    """Validate and normalize one product launch request.

    ``risk_rule_tokens`` is accepted as the product-facing spelling while
    ``rule_tokens`` remains the compact domain spelling.  Supplying both is
    allowed only when they normalize to the same set.
    """
    project = _required_text(project_id, "invalid_project_id")
    idem = _required_text(idempotency_key, "invalid_idempotency_key")
    normalized_mode = _required_text(mode, "invalid_mode")
    if normalized_mode not in SUPPORTED_MODES:
        raise LaunchRegistryError("invalid_mode")
    normalized_basis = _required_text(execution_basis, "invalid_execution_basis")
    if normalized_basis not in SUPPORTED_EXECUTION_BASES:
        raise LaunchRegistryError("invalid_execution_basis")
    current = _required_text(current_snapshot_token, "invalid_snapshot_token")
    baseline = _optional_text(baseline_token, "invalid_baseline_token")
    first_rules = _normalize_rule_tokens(rule_tokens)
    second_rules = _normalize_rule_tokens(risk_rule_tokens)
    if rule_tokens is not None and risk_rule_tokens is not None and first_rules != second_rules:
        raise LaunchRegistryError("invalid_rule_token")
    rules = first_rules if rule_tokens is not None else second_rules
    return LaunchRequest(
        project_id=project,
        idempotency_key=idem,
        mode=normalized_mode,
        execution_basis=normalized_basis,
        current_snapshot_token=current,
        baseline_token=baseline,
        rule_tokens=rules,
    )


@dataclass(frozen=True)
class LaunchRequest:
    """Canonical request identity; no timestamps or generated identifiers."""

    project_id: str
    idempotency_key: str
    mode: str
    execution_basis: str
    current_snapshot_token: str
    baseline_token: Optional[str]
    rule_tokens: Tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "project_id", _required_text(self.project_id, "invalid_project_id"))
        object.__setattr__(
            self, "idempotency_key", _required_text(self.idempotency_key, "invalid_idempotency_key")
        )
        mode = _required_text(self.mode, "invalid_mode")
        if mode not in SUPPORTED_MODES:
            raise LaunchRegistryError("invalid_mode")
        object.__setattr__(self, "mode", mode)
        basis = _required_text(self.execution_basis, "invalid_execution_basis")
        if basis not in SUPPORTED_EXECUTION_BASES:
            raise LaunchRegistryError("invalid_execution_basis")
        object.__setattr__(self, "execution_basis", basis)
        object.__setattr__(
            self,
            "current_snapshot_token",
            _required_text(self.current_snapshot_token, "invalid_snapshot_token"),
        )
        object.__setattr__(
            self, "baseline_token", _optional_text(self.baseline_token, "invalid_baseline_token")
        )
        object.__setattr__(self, "rule_tokens", _normalize_rule_tokens(self.rule_tokens))

    def fingerprint_payload(self) -> dict[str, Any]:
        # Keep this list aligned with Slice-07C-2 §3.  Project and key are
        # namespace/lookup values, not request-content fields.
        return {
            "mode": self.mode,
            "execution_basis": self.execution_basis,
            "current_snapshot_token": self.current_snapshot_token,
            "baseline_token": self.baseline_token,
            "rule_tokens": list(self.rule_tokens),
        }

    @property
    def request_fingerprint(self) -> str:
        return content_digest(self.fingerprint_payload())

    @property
    def idempotency_fingerprint(self) -> str:
        return self.request_fingerprint

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "idempotency_key": self.idempotency_key,
            **self.fingerprint_payload(),
        }


# Public aliases make the intent explicit at call sites and keep the function
# useful to route code that calls the field an idempotency fingerprint.
def canonical_request_fingerprint(request: Union[LaunchRequest, Mapping[str, Any]]) -> str:
    if isinstance(request, LaunchRequest):
        return request.request_fingerprint
    if isinstance(request, Mapping):
        normalized = normalize_request(
            project_id=request.get("project_id", "fingerprint"),
            idempotency_key=request.get("idempotency_key", "fingerprint"),
            mode=request.get("mode"),
            execution_basis=request.get("execution_basis"),
            current_snapshot_token=request.get("current_snapshot_token"),
            baseline_token=request.get("baseline_token"),
            rule_tokens=request.get("rule_tokens"),
            risk_rule_tokens=request.get("risk_rule_tokens"),
        )
        return normalized.request_fingerprint
    raise LaunchRegistryError("invalid_idempotency_key")


def compute_request_fingerprint(
    mode: str,
    execution_basis: str,
    current_snapshot_token: str,
    baseline_token: Optional[str] = None,
    rule_tokens: Optional[Iterable[str]] = None,
    risk_rule_tokens: Optional[Iterable[str]] = None,
) -> str:
    request = normalize_request(
        project_id="fingerprint",
        idempotency_key="fingerprint",
        mode=mode,
        execution_basis=execution_basis,
        current_snapshot_token=current_snapshot_token,
        baseline_token=baseline_token,
        rule_tokens=rule_tokens,
        risk_rule_tokens=risk_rule_tokens,
    )
    return request.request_fingerprint


# A stable opaque token is a navigation identifier, not an authorization
# credential.  It is derived only after the server generated the internal run.
def derive_public_run_token(project_id: str, run_id: str) -> str:
    project = _required_text(project_id, "invalid_project_id")
    internal_run = _required_text(run_id, "run_not_found")
    return "run:" + content_digest({"project_id": project, "run_id": internal_run})[:24]


public_run_token = derive_public_run_token


def publication_fingerprint_payload(
    project_id: str,
    run_id: str,
    public_run_token: Optional[str] = None,
    snapshot_token: Optional[str] = None,
    source_revision_id: Optional[str] = None,
    data_cutoff: Optional[str] = None,
    site_coverage: Optional[Iterable[Any]] = None,
    setup_manifest_identity: Any = None,
    *,
    snapshot_option_token: Optional[str] = None,
    source_revision: Optional[str] = None,
    setup_manifest_work_unit_identity: Any = None,
) -> dict[str, Any]:
    """Build the completion-independent frozen-content identity payload."""
    project = _required_text(project_id, "invalid_project_id")
    run = _required_text(run_id, "run_not_found")
    public = (
        _required_text(public_run_token, "public_run_not_found")
        if public_run_token is not None
        else derive_public_run_token(project, run)
    )
    if public != derive_public_run_token(project, run):
        raise LaunchRegistryError("invalid_publication_metadata")
    snapshot_value = LaunchRegistry._coalesce_publication_alias(
        snapshot_token, snapshot_option_token, "invalid_snapshot_token"
    )
    snapshot = _required_text(snapshot_value, "invalid_snapshot_token")
    source_value = LaunchRegistry._coalesce_publication_alias(
        source_revision_id, source_revision, "invalid_publication_metadata"
    )
    source = _required_text(source_value, "invalid_publication_metadata")
    cutoff = _required_text(data_cutoff, "invalid_data_cutoff")
    coverage = _normalize_publication_tokens(
        site_coverage, allow_single_text=False
    )
    identity_value = LaunchRegistry._coalesce_publication_alias(
        setup_manifest_identity,
        setup_manifest_work_unit_identity,
        "invalid_publication_metadata",
    )
    identity = _canonical_setup_manifest_identity(identity_value)
    return {
        "project_id": project,
        "run_id": run,
        "public_run_token": public,
        "snapshot_token": snapshot,
        "source_revision_id": source,
        "data_cutoff": cutoff,
        "site_coverage": list(coverage),
        "setup_manifest_identity": identity,
    }


def compute_publication_fingerprint(
    project_id: str,
    run_id: str,
    public_run_token: Optional[str] = None,
    snapshot_token: Optional[str] = None,
    source_revision_id: Optional[str] = None,
    data_cutoff: Optional[str] = None,
    site_coverage: Optional[Iterable[Any]] = None,
    setup_manifest_identity: Any = None,
    *,
    snapshot_option_token: Optional[str] = None,
    source_revision: Optional[str] = None,
    setup_manifest_work_unit_identity: Any = None,
) -> str:
    return content_digest(
        publication_fingerprint_payload(
            project_id,
            run_id,
            public_run_token,
            snapshot_token,
            source_revision_id,
            data_cutoff,
            site_coverage,
            setup_manifest_identity,
            snapshot_option_token=snapshot_option_token,
            source_revision=source_revision,
            setup_manifest_work_unit_identity=setup_manifest_work_unit_identity,
        )
    )


canonical_publication_fingerprint = compute_publication_fingerprint
compute_result_publication_fingerprint = compute_publication_fingerprint


@dataclass(frozen=True)
class LaunchRecord:
    """Durable launch facts; internal identity fields stay off public views."""

    sequence: int
    project_id: str
    idempotency_key: str
    run_id: str
    public_run_token: str
    request_fingerprint: str
    mode: str
    execution_basis: str
    current_snapshot_token: str
    baseline_token: Optional[str]
    rule_tokens: Tuple[str, ...]
    data_cutoff: str
    comparison_range_text: str
    run_state: str
    result_available: bool
    main_action: str
    manifest_digest: Optional[str]
    created_at: str
    updated_at: str

    @property
    def public_token(self) -> str:
        return self.public_run_token

    @property
    def state(self) -> str:
        return self.run_state

    @property
    def idempotency_fingerprint(self) -> str:
        return self.request_fingerprint

    @property
    def mode_text(self) -> str:
        return _MODE_TEXT[self.mode]

    @property
    def status_text(self) -> str:
        return _run_status_text(self.run_state, bool(self.result_available))

    def public_projection(self) -> dict[str, Any]:
        """Return exactly the bounded public history shape."""
        return {
            "public_run_token": self.public_run_token,
            "mode_text": self.mode_text,
            "data_cutoff_text": self.data_cutoff,
            "comparison_range_text": self.comparison_range_text,
            "run_state": self.run_state,
            "result_available": bool(self.result_available),
            "main_action": self.main_action,
            "status_text": self.status_text,
        }

    def as_public_dict(self) -> dict[str, Any]:
        return self.public_projection()

    def as_dict(self) -> dict[str, Any]:
        return self.public_projection()

    @property
    def projection(self) -> dict[str, Any]:
        return self.public_projection()


@dataclass(frozen=True)
class LaunchReservation:
    """First reservation or same-key replay result."""

    record: LaunchRecord
    replayed: bool

    @property
    def public_run_token(self) -> str:
        return self.record.public_run_token

    @property
    def public_token(self) -> str:
        return self.record.public_run_token

    @property
    def run_id(self) -> str:
        return self.record.run_id

    @property
    def run_state(self) -> str:
        return self.record.run_state

    @property
    def projection(self) -> dict[str, Any]:
        body = self.record.public_projection()
        body["replayed"] = bool(self.replayed)
        return body

    def as_dict(self) -> dict[str, Any]:
        body = self.record.public_projection()
        body["replayed"] = bool(self.replayed)
        return body

    @property
    def public_projection(self) -> dict[str, Any]:
        return self.record.public_projection()


# State transitions are intentionally permissive across recovery states: a
# worker may be interrupted between any durable operation, but terminal runs
# cannot be silently replaced by another launch.


@dataclass(frozen=True)
class ResultPublication:
    """Durable internal identity and state for one published run result.

    The publication row is intentionally richer than the public history
    projection.  Hashes, receipt identities, manifest details, and the
    internal run id remain available only to the publication/authority path.
    """

    sequence: int
    project_id: str
    run_id: str
    public_run_token: str
    idempotency_key: str
    publication_revision: int
    publication_fingerprint: str
    mode: str
    execution_basis: str
    snapshot_token: str
    snapshot_ref: Optional[str]
    source_revision_id: Optional[str]
    data_cutoff: str
    setup_manifest_digest: Optional[str]
    manifest_revision: Optional[int]
    manifest_digest: Optional[str]
    mandatory_denominator: int
    site_coverage: Tuple[str, ...]
    setup_manifest_identity: Mapping[str, Any]
    runtime_manifest_identity: Mapping[str, Any]
    receipt_identities: Tuple[str, ...]
    receipt_set_digest: Optional[str]
    r5_authority_packet_id: Optional[str]
    r5_authority_packet_digest: Optional[str]
    s4_authority_packet_identities: Tuple[str, ...]
    s4_authority_packet_digests: Tuple[str, ...]
    publication_state: str
    failure_code: Optional[str]
    failure_message: Optional[str]
    created_at: str
    updated_at: str
    replayed: bool = False
    result_context_token: Optional[str] = None
    r6_output_set_digest: Optional[str] = None
    artifact_member_ids: Tuple[str, ...] = ()
    artifact_member_set_digest: Optional[str] = None

    @property
    def artifact_member_set(self) -> Tuple[str, ...]:
        return self.artifact_member_ids

    @property
    def artifact_members(self) -> Tuple[str, ...]:
        return self.artifact_member_ids
    @property
    def state(self) -> str:
        return self.publication_state

    @property
    def result_available(self) -> bool:
        return self.publication_state == PUBLICATION_STATE_AVAILABLE

    @property
    def revision(self) -> int:
        return self.publication_revision

    @property
    def fingerprint(self) -> str:
        return self.publication_fingerprint

    @property
    def request_fingerprint(self) -> str:
        return self.publication_fingerprint

    @property
    def current_snapshot_token(self) -> str:
        return self.snapshot_token

    @property
    def current_snapshot_ref(self) -> Optional[str]:
        return self.snapshot_ref

    @property
    def snapshot_option_token(self) -> str:
        return self.snapshot_token

    @property
    def setup_manifest_work_unit_identity(self) -> Mapping[str, Any]:
        return self.setup_manifest_identity

    @property
    def runtime_manifest_work_unit_identity(self) -> Mapping[str, Any]:
        return self.runtime_manifest_identity

    @property
    def runtime_manifest_revision(self) -> Optional[int]:
        return self.manifest_revision

    @property
    def runtime_manifest_digest(self) -> Optional[str]:
        return self.manifest_digest

    @property
    def sites(self) -> Tuple[str, ...]:
        return self.site_coverage

    @property
    def site_refs(self) -> Tuple[str, ...]:
        return self.site_coverage

    @property
    def site_coverage_refs(self) -> Tuple[str, ...]:
        return self.site_coverage

    @property
    def data_cutoff_text(self) -> str:
        return self.data_cutoff

    @property
    def receipt_set(self) -> Tuple[str, ...]:
        return self.receipt_identities

    @property
    def r5_packet_identity(self) -> Optional[str]:
        return self.r5_authority_packet_id

    @property
    def r5_packet_digest(self) -> Optional[str]:
        return self.r5_authority_packet_digest

    @property
    def product_authority_packet_id(self) -> Optional[str]:
        return self.r5_authority_packet_id

    @property
    def product_authority_packet_digest(self) -> Optional[str]:
        return self.r5_authority_packet_digest

    @property
    def authority_packet_id(self) -> Optional[str]:
        return self.r5_authority_packet_id

    @property
    def authority_packet_digest(self) -> Optional[str]:
        return self.r5_authority_packet_digest

    @property
    def s4_packet_identities(self) -> Tuple[str, ...]:
        return self.s4_authority_packet_identities

    @property
    def s4_packet_digests(self) -> Tuple[str, ...]:
        return self.s4_authority_packet_digests

    @property
    def error_code(self) -> Optional[str]:
        return self.failure_code

    @property
    def error_message(self) -> Optional[str]:
        return self.failure_message

    @property
    def publication_id(self) -> Tuple[str, str, int]:
        return (self.project_id, self.run_id, self.publication_revision)

    @property
    def publication(self) -> "ResultPublication":
        """Compatibility accessor for callers treating reserve as a wrapper."""
        return self

    @property
    def record(self) -> "ResultPublication":
        return self

    def as_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "project_id": self.project_id,
            "run_id": self.run_id,
            "public_run_token": self.public_run_token,
            "result_context_token": self.result_context_token,
            "idempotency_key": self.idempotency_key,
            "publication_revision": self.publication_revision,
            "publication_fingerprint": self.publication_fingerprint,
            "mode": self.mode,
            "execution_basis": self.execution_basis,
            "snapshot_token": self.snapshot_token,
            "snapshot_ref": self.snapshot_ref,
            "source_revision_id": self.source_revision_id,
            "data_cutoff": self.data_cutoff,
            "setup_manifest_digest": self.setup_manifest_digest,
            "manifest_revision": self.manifest_revision,
            "manifest_digest": self.manifest_digest,
            "mandatory_denominator": self.mandatory_denominator,
            "site_coverage": list(self.site_coverage),
            "setup_manifest_identity": dict(self.setup_manifest_identity),
            "runtime_manifest_identity": dict(self.runtime_manifest_identity),
            "receipt_identities": list(self.receipt_identities),
            "receipt_set_digest": self.receipt_set_digest,
            "r5_authority_packet_id": self.r5_authority_packet_id,
            "r5_authority_packet_digest": self.r5_authority_packet_digest,
            "s4_authority_packet_identities": list(self.s4_authority_packet_identities),
            "s4_authority_packet_digests": list(self.s4_authority_packet_digests),
            "r6_output_set_digest": self.r6_output_set_digest,
            "artifact_member_ids": list(self.artifact_member_ids),
            "artifact_member_set_digest": self.artifact_member_set_digest,
            "publication_state": self.publication_state,
            "failure_message": self.failure_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "replayed": bool(self.replayed),
        }

    def as_internal_dict(self) -> dict[str, Any]:
        return self.as_dict()
_ALLOWED_TRANSITIONS = {
    STATE_WAITING_START: frozenset(
        {
            STATE_WAITING_START,
            STATE_RUNNING,
            STATE_STOPPING,
            STATE_INTERRUPTED_RESUMABLE,
            STATE_COMPLETED,
            STATE_ENDED_INCOMPLETE,
            STATE_FAILED,
        }
    ),
    STATE_RUNNING: frozenset(
        {
            STATE_RUNNING,
            STATE_STOPPING,
            STATE_INTERRUPTED_RESUMABLE,
            STATE_WAITING_START,
            STATE_COMPLETED,
            STATE_ENDED_INCOMPLETE,
            STATE_FAILED,
        }
    ),
    STATE_STOPPING: frozenset(
        {
            STATE_STOPPING,
            STATE_INTERRUPTED_RESUMABLE,
            STATE_WAITING_START,
            STATE_COMPLETED,
            STATE_ENDED_INCOMPLETE,
            STATE_FAILED,
        }
    ),
    STATE_INTERRUPTED_RESUMABLE: frozenset(
        {
            STATE_INTERRUPTED_RESUMABLE,
            STATE_RUNNING,
            STATE_STOPPING,
            STATE_WAITING_START,
            STATE_COMPLETED,
            STATE_ENDED_INCOMPLETE,
            STATE_FAILED,
        }
    ),
    STATE_COMPLETED: frozenset({STATE_COMPLETED}),
    STATE_ENDED_INCOMPLETE: frozenset(
        {STATE_ENDED_INCOMPLETE, STATE_INTERRUPTED_RESUMABLE, STATE_RUNNING, STATE_WAITING_START}
    ),
    STATE_FAILED: frozenset({STATE_FAILED, STATE_INTERRUPTED_RESUMABLE, STATE_RUNNING, STATE_WAITING_START}),
}


_PUBLICATION_ALLOWED_TRANSITIONS = {
    PUBLICATION_STATE_PUBLISHING: frozenset(
        {
            PUBLICATION_STATE_AVAILABLE,
            PUBLICATION_STATE_RECOVERABLE_FAILED,
            PUBLICATION_STATE_BLOCKED,
        }
    ),
    PUBLICATION_STATE_RECOVERABLE_FAILED: frozenset(
        {
            PUBLICATION_STATE_PUBLISHING,
            PUBLICATION_STATE_BLOCKED,
            PUBLICATION_STATE_AVAILABLE,
        }
    ),
    PUBLICATION_STATE_BLOCKED: frozenset(
        {PUBLICATION_STATE_PUBLISHING, PUBLICATION_STATE_AVAILABLE}
    ),
    PUBLICATION_STATE_AVAILABLE: frozenset(),
}



def _assert_current_schema(path: Path) -> None:
    """Reject an existing legacy/unknown file before writable SQLite calls."""
    if not path.exists():
        return
    from .schema_manifest import SchemaClassification, inspect_member

    report = inspect_member(path, "launch_registry")
    if report.classification is not SchemaClassification.CURRENT:
        raise LaunchRegistryError("unsupported_schema_version")


class LaunchRegistry:
    """Project-scoped SQLite launch registry with explicit lifecycle."""

    def __init__(
        self,
        db_path: Union[str, Path],
        *,
        project_id: str = "",
        busy_timeout_ms: int = BUSY_TIMEOUT_MS,
        default_history_limit: int = DEFAULT_HISTORY_LIMIT,
        max_history_limit: int = MAX_HISTORY_LIMIT,
        history_limit: Optional[int] = None,
        failure_injector: Optional[Callable[[str], None]] = None,
        failure_hook: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._path = Path(db_path)
        _assert_current_schema(self._path)
        if self._path.parent and str(self._path.parent) not in ("", "."):
            self._path.parent.mkdir(parents=True, exist_ok=True)
        self._default_project_id = (
            _required_text(project_id, "invalid_project_id") if project_id else ""
        )
        if history_limit is not None:
            default_history_limit = history_limit
        if (
            isinstance(busy_timeout_ms, bool)
            or not isinstance(busy_timeout_ms, int)
            or busy_timeout_ms <= 0
        ):
            raise LaunchRegistryError("invalid_history_limit")
        if (
            isinstance(default_history_limit, bool)
            or not isinstance(default_history_limit, int)
            or default_history_limit < 0
        ):
            raise LaunchRegistryError("invalid_history_limit")
        if (
            isinstance(max_history_limit, bool)
            or not isinstance(max_history_limit, int)
            or max_history_limit < 1
        ):
            raise LaunchRegistryError("invalid_history_limit")
        self._busy_timeout_ms = busy_timeout_ms
        self._default_history_limit = min(default_history_limit, max_history_limit)
        self._max_history_limit = max_history_limit
        self._failure_injector = (
            failure_injector if failure_injector is not None else failure_hook
        )
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        self.open()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def busy_timeout_ms(self) -> int:
        return self._busy_timeout_ms

    @property
    def schema_version(self) -> str:
        with self._lock:
            row = self._require_conn().execute(
                "SELECT value FROM r7_launch_registry_meta WHERE key = ?",
                ("schema_version",),
            ).fetchone()
        if row is None or str(row["value"]) != SCHEMA_VERSION:
            raise LaunchRegistryError("unsupported_schema_version")
        return str(row["value"])

    def set_failure_injector(
        self, injector: Optional[Callable[[str], None]]
    ) -> None:
        self._failure_injector = injector

    def _inject_failure(self, point: str) -> None:
        hook = self._failure_injector
        if hook is not None:
            hook(str(point))

    @staticmethod
    def _execute_script_in_transaction(
        connection: sqlite3.Connection, script: str
    ) -> None:
        # ``executescript`` commits an open transaction on CPython. Split this
        # fixed internal DDL into statements so initialization remains atomic.
        for statement in script.split(";"):
            sql = statement.strip()
            if sql:
                connection.execute(sql)

    def open(self) -> None:
        with self._lock:
            if self._conn is not None:
                return
            _assert_current_schema(self._path)
            connection: Optional[sqlite3.Connection] = None
            transaction_started = False
            try:
                connection = sqlite3.connect(
                    str(self._path),
                    timeout=self._busy_timeout_ms / 1000.0,
                    isolation_level=None,
                    check_same_thread=False,
                )
                connection.row_factory = sqlite3.Row
                # Set both the driver timeout and SQLite's connection pragma;
                # the latter is observable and applies to lock waits in every
                # explicit transaction on this connection.
                connection.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute("BEGIN IMMEDIATE")
                transaction_started = True
                self._execute_script_in_transaction(connection, _BASE_DDL)
                row = connection.execute(
                    "SELECT value FROM r7_launch_registry_meta WHERE key = ?",
                    ("schema_version",),
                ).fetchone()
                version = None if row is None else str(row["value"])
                if version is None:
                    # A missing file is born at the current schema in one
                    # transaction; existing legacy files were rejected above.
                    self._execute_script_in_transaction(connection, _PUBLICATION_DDL)
                    self._execute_script_in_transaction(connection, _RESULT_CONTEXT_INDEX_DDL)
                    self._execute_script_in_transaction(connection, _CONTINUITY_DDL)
                    self._execute_script_in_transaction(connection, _CONTINUITY_INDEX_DDL)
                    connection.execute(
                        "INSERT INTO r7_launch_registry_meta(key, value) VALUES (?, ?)",
                        ("schema_version", SCHEMA_VERSION),
                    )
                elif version != SCHEMA_VERSION:
                    raise LaunchRegistryError("unsupported_schema_version")
                connection.commit()
                self._conn = connection
            except LaunchRegistryError:
                if connection is not None and transaction_started:
                    try:
                        connection.rollback()
                    except sqlite3.Error:
                        pass
                if connection is not None:
                    connection.close()
                raise
            except Exception as exc:
                if connection is not None and transaction_started:
                    try:
                        connection.rollback()
                    except sqlite3.Error:
                        pass
                if connection is not None:
                    connection.close()
                raise LaunchRegistryError("store_closed") from exc

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def reopen(self) -> None:
        with self._lock:
            self.close()
            self.open()

    def __enter__(self) -> "LaunchRegistry":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise LaunchRegistryError("store_closed")
        return self._conn

    def _project(self, project_id: Optional[str]) -> str:
        value = self._default_project_id if project_id is None else project_id
        return _required_text(value, "invalid_project_id")

    @staticmethod
    def _now() -> str:
        return _datetime.datetime.now(_datetime.timezone.utc).isoformat(timespec="milliseconds")

    @staticmethod
    def _default_action(state: str, result_available: bool) -> str:
        return _RESULT_MAIN_ACTION if state == STATE_COMPLETED and result_available else _DEFAULT_MAIN_ACTION

    def _row_to_record(self, row: sqlite3.Row) -> LaunchRecord:
        try:
            raw_rules = json.loads(str(row["rule_tokens_json"]))
        except (TypeError, json.JSONDecodeError) as exc:
            raise LaunchRegistryError("store_closed") from exc
        if not isinstance(raw_rules, list) or any(not isinstance(item, str) for item in raw_rules):
            raise LaunchRegistryError("store_closed")
        record = LaunchRecord(
            sequence=int(row["sequence"]),
            project_id=str(row["project_id"]),
            idempotency_key=str(row["idempotency_key"]),
            run_id=str(row["run_id"]),
            public_run_token=str(row["public_run_token"]),
            request_fingerprint=str(row["request_fingerprint"]),
            mode=str(row["mode"]),
            execution_basis=str(row["execution_basis"]),
            current_snapshot_token=str(row["current_snapshot_token"]),
            baseline_token=(str(row["baseline_token"]) if row["baseline_token"] is not None else None),
            rule_tokens=tuple(raw_rules),
            data_cutoff=str(row["data_cutoff"]),
            comparison_range_text=str(row["comparison_range_text"]),
            run_state=str(row["run_state"]),
            result_available=bool(int(row["result_available"])),
            main_action=str(row["main_action"]),
            manifest_digest=(str(row["manifest_digest"]) if row["manifest_digest"] is not None else None),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
        if record.mode not in SUPPORTED_MODES or record.run_state not in RUN_STATE_VALUES:
            raise LaunchRegistryError("store_closed")
        if record.result_available and record.run_state != STATE_COMPLETED:
            raise LaunchRegistryError("store_closed")
        try:
            request = LaunchRequest(
                project_id=record.project_id,
                idempotency_key=record.idempotency_key,
                mode=record.mode,
                execution_basis=record.execution_basis,
                current_snapshot_token=record.current_snapshot_token,
                baseline_token=record.baseline_token,
                rule_tokens=record.rule_tokens,
            )
        except LaunchRegistryError as exc:
            raise LaunchRegistryError("store_closed") from exc
        if (
            request.rule_tokens != record.rule_tokens
            or request.request_fingerprint != record.request_fingerprint
            or derive_public_run_token(record.project_id, record.run_id) != record.public_run_token
            or record.main_action != self._default_action(record.run_state, record.result_available)
        ):
            raise LaunchRegistryError("store_closed")
        return record

    def _find_by_key(self, project: str, idempotency_key: str) -> Optional[LaunchRecord]:
        row = self._require_conn().execute(
            "SELECT * FROM r7_launch_registry WHERE project_id = ? AND idempotency_key = ?",
            (project, idempotency_key),
        ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def _find_by_selector(self, project: str, selector: str) -> Optional[LaunchRecord]:
        row = self._require_conn().execute(
            "SELECT * FROM r7_launch_registry "
            "WHERE project_id = ? AND (public_run_token = ? OR run_id = ?)",
            (project, selector, selector),
        ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def _find_in_flight_locked(
        self, connection: sqlite3.Connection, project: str
    ) -> Optional[LaunchRecord]:
        row = connection.execute(
            "SELECT launch.* FROM r7_launch_registry AS launch "
            "WHERE launch.project_id = ? AND ("
            "launch.run_state IN (?, ?, ?, ?) "
            "OR (launch.run_state = ? AND launch.result_available = 0)"
            ") ORDER BY launch.created_at DESC, launch.sequence DESC LIMIT 1",
            (
                project,
                STATE_WAITING_START,
                STATE_RUNNING,
                STATE_STOPPING,
                STATE_INTERRUPTED_RESUMABLE,
                STATE_COMPLETED,
            ),
        ).fetchone()
        return self._row_to_record(row) if row is not None else None

    def get_in_flight(
        self, project_id: Optional[str] = None
    ) -> Optional[LaunchRecord]:
        project = self._project(project_id)
        with self._lock:
            return self._find_in_flight_locked(self._require_conn(), project)

    def has_in_flight(self, project_id: Optional[str] = None) -> bool:
        return self.get_in_flight(project_id) is not None

    in_flight = get_in_flight

    def _row_to_publication(
        self, row: sqlite3.Row, *, replayed: bool = False
    ) -> ResultPublication:
        try:
            state = str(row["publication_state"])
            revision = int(row["publication_revision"])
            manifest_revision = (
                int(row["manifest_revision"])
                if row["manifest_revision"] is not None
                else None
            )
            mandatory_denominator = int(row["mandatory_denominator"])
            site_coverage = _decode_token_list(row["site_coverage_json"])
            receipt_identities = _decode_token_list(row["receipt_identities_json"])
            s4_identities = _decode_token_list(
                row["s4_authority_packet_identities_json"]
            )
            s4_digests = _decode_token_list(row["s4_authority_packet_digests_json"])
            setup_identity = _decode_publication_object(
                row["setup_manifest_identity_json"]
            )
            runtime_identity = _decode_publication_object(
                row["runtime_manifest_identity_json"]
            )
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise LaunchRegistryError("store_closed") from exc
        if (
            state not in PUBLICATION_STATE_VALUES
            or revision != PUBLICATION_REVISION
            or manifest_revision is not None and manifest_revision < 1
            or mandatory_denominator < 0
        ):
            raise LaunchRegistryError("store_closed")
        project = str(row["project_id"])
        run_id = str(row["run_id"])
        public_token = str(row["public_run_token"])
        try:
            result_context_token = _normalize_result_context_token(
                row["result_context_token"]
            )
        except LaunchRegistryError as exc:
            raise LaunchRegistryError("store_closed") from exc
        if derive_public_run_token(project, run_id) != public_token:
            raise LaunchRegistryError("store_closed")
        mode = str(row["mode"])
        basis = str(row["execution_basis"])
        if mode not in SUPPORTED_MODES or basis not in SUPPORTED_EXECUTION_BASES:
            raise LaunchRegistryError("store_closed")
        try:
            snapshot_token = _required_text(
                str(row["snapshot_token"]), "invalid_snapshot_token"
            )
            fingerprint = _required_text(
                str(row["publication_fingerprint"]), "invalid_publication_fingerprint"
            )
            data_cutoff = _required_text(str(row["data_cutoff"]), "invalid_data_cutoff")
            key = _required_text(str(row["idempotency_key"]), "invalid_idempotency_key")
        except LaunchRegistryError as exc:
            raise LaunchRegistryError("store_closed") from exc
        r6_output_set_digest = (
            str(row["r6_output_set_digest"])
            if "r6_output_set_digest" in row.keys()
            and row["r6_output_set_digest"] is not None
            else None
        )
        artifact_member_ids = (
            _decode_token_list(row["artifact_member_ids_json"])
            if "artifact_member_ids_json" in row.keys()
            and row["artifact_member_ids_json"] is not None
            else ()
        )
        artifact_member_set_digest = (
            str(row["artifact_member_set_digest"])
            if "artifact_member_set_digest" in row.keys()
            and row["artifact_member_set_digest"] is not None
            else None
        )
        has_v4_closure = bool(
            r6_output_set_digest or artifact_member_ids or artifact_member_set_digest
        )
        if state == PUBLICATION_STATE_AVAILABLE and has_v4_closure:
            if (
                len(artifact_member_ids) != 4
                or r6_output_set_digest is None
                or len(r6_output_set_digest) != 64
                or artifact_member_set_digest
                != content_digest(list(artifact_member_ids))
            ):
                raise LaunchRegistryError("store_closed")

        return ResultPublication(
            sequence=int(row["sequence"]),
            project_id=project,
            run_id=run_id,
            public_run_token=public_token,
            result_context_token=result_context_token,
            idempotency_key=key,
            publication_revision=revision,
            publication_fingerprint=fingerprint,
            mode=mode,
            execution_basis=basis,
            snapshot_token=snapshot_token,
            snapshot_ref=(
                str(row["snapshot_ref"]) if row["snapshot_ref"] is not None else None
            ),
            source_revision_id=(
                str(row["source_revision_id"])
                if row["source_revision_id"] is not None
                else None
            ),
            data_cutoff=data_cutoff,
            setup_manifest_digest=(
                str(row["setup_manifest_digest"])
                if row["setup_manifest_digest"] is not None
                else None
            ),
            manifest_revision=manifest_revision,
            manifest_digest=(
                str(row["manifest_digest"])
                if row["manifest_digest"] is not None
                else None
            ),
            mandatory_denominator=mandatory_denominator,
            site_coverage=site_coverage,
            setup_manifest_identity=setup_identity,
            runtime_manifest_identity=runtime_identity,
            receipt_identities=receipt_identities,
            receipt_set_digest=(
                str(row["receipt_set_digest"])
                if row["receipt_set_digest"] is not None
                else None
            ),
            r5_authority_packet_id=(
                str(row["r5_authority_packet_id"])
                if row["r5_authority_packet_id"] is not None
                else None
            ),
            r5_authority_packet_digest=(
                str(row["r5_authority_packet_digest"])
                if row["r5_authority_packet_digest"] is not None
                else None
            ),
            s4_authority_packet_identities=s4_identities,
            s4_authority_packet_digests=s4_digests,
            r6_output_set_digest=r6_output_set_digest,
            artifact_member_ids=artifact_member_ids,
            artifact_member_set_digest=artifact_member_set_digest,
            publication_state=state,
            failure_code=(
                str(row["failure_code"]) if row["failure_code"] is not None else None
            ),
            failure_message=(
                str(row["failure_message"])
                if row["failure_message"] is not None
                else None
            ),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            replayed=bool(replayed),
        )

    def _find_publication_by_run(
        self, project: str, run_id: str
    ) -> Optional[ResultPublication]:
        row = self._require_conn().execute(
            "SELECT * FROM r7_result_publications "
            "WHERE project_id = ? AND run_id = ?",
            (project, run_id),
        ).fetchone()
        return self._row_to_publication(row) if row is not None else None

    def _find_publication_by_key(
        self, project: str, idempotency_key: str
    ) -> Optional[ResultPublication]:
        row = self._require_conn().execute(
            "SELECT * FROM r7_result_publications "
            "WHERE project_id = ? AND idempotency_key = ?",
            (project, idempotency_key),
        ).fetchone()
        return self._row_to_publication(row) if row is not None else None

    def _resolve_publication_run(
        self, project: str, selector: str
    ) -> LaunchRecord:
        value = _required_text(selector, "run_not_found")
        record = self._find_by_selector(project, value)
        if record is None:
            raise LaunchRegistryError("run_not_found")
        return record

    def reserve(
        self,
        project_id: Optional[str] = None,
        *,
        idempotency_key: str,
        mode: str,
        execution_basis: str,
        current_snapshot_token: str,
        baseline_token: Optional[str] = None,
        rule_tokens: Optional[Iterable[str]] = None,
        risk_rule_tokens: Optional[Iterable[str]] = None,
        data_cutoff: str = "",
        comparison_range: Any = "",
        comparison_range_text: Any = None,
        manifest_digest: Optional[str] = None,
        enforce_in_flight: bool = True,
    ) -> LaunchReservation:
        cutoff = _required_text(data_cutoff, "invalid_data_cutoff")
        range_value = comparison_range_text if comparison_range_text is not None else comparison_range
        range_text = _normalize_comparison_range(range_value) if range_value else ""
        digest = _optional_text(manifest_digest, "invalid_manifest_digest")
        project = self._project(project_id)
        request = normalize_request(
            project_id=project,
            idempotency_key=idempotency_key,
            mode=mode,
            execution_basis=execution_basis,
            current_snapshot_token=current_snapshot_token,
            baseline_token=baseline_token,
            rule_tokens=rule_tokens,
            risk_rule_tokens=risk_rule_tokens,
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = self._find_by_key(project, request.idempotency_key)
                if existing is not None:
                    connection.commit()
                    if existing.request_fingerprint == request.request_fingerprint:
                        return LaunchReservation(existing, True)
                    raise IdempotencyConflictError()
                if enforce_in_flight and self._find_in_flight_locked(
                    connection, project
                ) is not None:
                    raise LaunchRegistryError("in_flight_conflict")

                run_id = "r7-run-" + uuid4().hex
                public_token = derive_public_run_token(project, run_id)
                now = self._now()
                connection.execute(
                    """INSERT INTO r7_launch_registry(
                        project_id, idempotency_key, run_id, public_run_token,
                        request_fingerprint, mode, execution_basis,
                        current_snapshot_token, baseline_token, rule_tokens_json,
                        data_cutoff, comparison_range_text, run_state,
                        result_available, main_action, manifest_digest,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        project,
                        request.idempotency_key,
                        run_id,
                        public_token,
                        request.request_fingerprint,
                        request.mode,
                        request.execution_basis,
                        request.current_snapshot_token,
                        request.baseline_token,
                        json.dumps(list(request.rule_tokens), ensure_ascii=False, separators=(",", ":")),
                        cutoff,
                        range_text,
                        STATE_WAITING_START,
                        0,
                        _DEFAULT_MAIN_ACTION,
                        digest,
                        now,
                        now,
                    ),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_launch_registry WHERE project_id = ? AND idempotency_key = ?",
                    (project, request.idempotency_key),
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("store_closed")
                return LaunchReservation(self._row_to_record(row), False)
            except IdempotencyConflictError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except sqlite3.IntegrityError:
                # Another process can win only after SQLite releases the
                # immediate lock.  Re-read its committed row and apply the
                # same fingerprint comparison instead of fabricating a run.
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                existing = self._find_by_key(project, request.idempotency_key)
                if existing is not None and existing.request_fingerprint == request.request_fingerprint:
                    return LaunchReservation(existing, True)
                if existing is not None:
                    raise IdempotencyConflictError()
                raise LaunchRegistryError("store_closed")
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    # Natural aliases used by route adapters.
    reserve_launch = reserve
    register = reserve
    create = reserve

    @staticmethod
    def _coalesce_publication_alias(
        primary: Any, alias: Any, code: str
    ) -> Any:
        if primary is not None and alias is not None and primary != alias:
            raise LaunchRegistryError(code)
        return primary if primary is not None else alias

    def _publication_project_run(
        self,
        project: Optional[str],
        run: Optional[str],
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
    ) -> Tuple[str, LaunchRecord]:
        project_value = self._coalesce_publication_alias(
            project, project_id, "invalid_project_id"
        )
        run_alias = self._coalesce_publication_alias(
            run_id, public_run_token, "run_not_found"
        )
        run_value = self._coalesce_publication_alias(
            run, run_alias, "run_not_found"
        )
        project_text = self._project(project_value)
        if run_value is None:
            raise LaunchRegistryError("run_not_found")
        return project_text, self._resolve_publication_run(project_text, run_value)

    @staticmethod
    def _publication_revision_alias(
        publication_revision: Any, revision: Optional[int]
    ) -> int:
        if revision is not None:
            if (
                publication_revision is not None
                and publication_revision != PUBLICATION_REVISION
                and publication_revision != revision
            ):
                raise LaunchRegistryError("invalid_publication_revision")
            publication_revision = revision
        if publication_revision is None:
            publication_revision = PUBLICATION_REVISION
        return _normalize_publication_revision(publication_revision)

    @staticmethod
    def _publication_text_alias(
        primary: Any, alias: Any, code: str
    ) -> Optional[str]:
        value = LaunchRegistry._coalesce_publication_alias(primary, alias, code)
        return _optional_text(value, code) if value is not None else None

    def reserve_publication(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        key: Optional[str] = None,
        fingerprint: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        request_fingerprint: Optional[str] = None,
        publication_fingerprint: Optional[str] = None,
        revision: Optional[int] = None,
        snapshot_token: Optional[str] = None,
        current_snapshot_token: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        current_snapshot_ref: Optional[str] = None,
        source_revision_id: Optional[str] = None,
        source_revision: Optional[str] = None,
        data_cutoff: Optional[str] = None,
        setup_manifest_digest: Optional[str] = None,
        manifest_revision: Optional[int] = None,
        runtime_manifest_revision: Optional[int] = None,
        manifest_digest: Optional[str] = None,
        runtime_manifest_digest: Optional[str] = None,
        mandatory_denominator: int = 0,
        site_coverage: Optional[Iterable[Any]] = None,
        sites: Optional[Iterable[Any]] = None,
        setup_manifest_identity: Any = None,
        setup_manifest_work_unit_identity: Any = None,
        runtime_manifest_identity: Any = None,
        runtime_manifest_work_unit_identity: Any = None,
        receipt_identities: Optional[Iterable[Any]] = None,
        receipt_set: Optional[Iterable[Any]] = None,
        receipt_set_digest: Optional[str] = None,
        r5_authority_packet_id: Optional[str] = None,
        r5_authority_packet_identity: Optional[str] = None,
        r5_packet_id: Optional[str] = None,
        r5_authority_packet_digest: Optional[str] = None,
        r5_packet_digest: Optional[str] = None,
        s4_authority_packet_identities: Optional[Iterable[Any]] = None,
        s4_packet_identities: Optional[Iterable[Any]] = None,
        s4_authority_packet_digests: Optional[Iterable[Any]] = None,
        s4_packet_digests: Optional[Iterable[Any]] = None,
    ) -> ResultPublication:
        """Reserve the one immutable publication identity for a run.

        The run identity is authoritative; an idempotency key is only a
        retry handle.  Therefore a second key with the same frozen fingerprint
        returns the original row instead of creating a second publication.
        """
        # Runtime manifest, receipt, and authority facts are completion-
        # dependent.  They must be read and bound after this reservation, not
        # smuggled into the initial publication identity.
        prebound_values = (
            manifest_revision,
            runtime_manifest_revision,
            manifest_digest,
            runtime_manifest_digest,
            runtime_manifest_identity,
            runtime_manifest_work_unit_identity,
            receipt_identities,
            receipt_set,
            receipt_set_digest,
            r5_authority_packet_id,
            r5_authority_packet_identity,
            r5_packet_id,
            r5_authority_packet_digest,
            r5_packet_digest,
            s4_authority_packet_identities,
            s4_packet_identities,
            s4_authority_packet_digests,
            s4_packet_digests,
        )
        if any(value is not None for value in prebound_values):
            raise LaunchRegistryError("invalid_publication_metadata")

        project_text, launch = self._publication_project_run(
            project,
            run,
            project_id=project_id,
            run_id=run_id,
            public_run_token=public_run_token,
        )
        if public_run_token is not None and _required_text(
            public_run_token, "invalid_publication_metadata"
        ) != launch.public_run_token:
            raise LaunchRegistryError("invalid_publication_metadata")
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        key_value = self._coalesce_publication_alias(
            key, idempotency_key, "invalid_idempotency_key"
        )
        if key_value is None:
            raise LaunchRegistryError("invalid_idempotency_key")
        key_text = _required_text(key_value, "invalid_idempotency_key")
        fingerprint_value = self._coalesce_publication_alias(
            fingerprint,
            self._coalesce_publication_alias(
                request_fingerprint,
                publication_fingerprint,
                "invalid_publication_fingerprint",
            ),
            "invalid_publication_fingerprint",
        )
        if fingerprint_value is None:
            raise LaunchRegistryError("invalid_publication_fingerprint")
        fingerprint_text = _required_text(
            fingerprint_value, "invalid_publication_fingerprint"
        )
        snapshot_value = self._coalesce_publication_alias(
            snapshot_token, current_snapshot_token, "invalid_snapshot_token"
        )
        snapshot_text = (
            _required_text(snapshot_value, "invalid_snapshot_token")
            if snapshot_value is not None
            else launch.current_snapshot_token
        )
        snapshot_ref_value = self._coalesce_publication_alias(
            snapshot_ref, current_snapshot_ref, "invalid_snapshot_token"
        )
        snapshot_ref_text = (
            _required_text(snapshot_ref_value, "invalid_snapshot_token")
            if snapshot_ref_value is not None
            else None
        )
        source_value = self._coalesce_publication_alias(
            source_revision_id,
            source_revision,
            "invalid_publication_metadata",
        )
        source_text = _optional_text(source_value, "invalid_publication_metadata")
        cutoff_text = (
            _required_text(data_cutoff, "invalid_data_cutoff")
            if data_cutoff is not None
            else launch.data_cutoff
        )
        setup_digest = (
            _optional_text(setup_manifest_digest, "invalid_manifest_digest")
            if setup_manifest_digest is not None
            else launch.manifest_digest
        )
        manifest_revision_value = self._coalesce_publication_alias(
            manifest_revision,
            runtime_manifest_revision,
            "invalid_publication_revision",
        )
        manifest_revision_value = _normalize_optional_positive_int(
            manifest_revision_value, "invalid_publication_revision"
        )
        manifest_digest_value = self._coalesce_publication_alias(
            manifest_digest,
            runtime_manifest_digest,
            "invalid_manifest_digest",
        )
        manifest_digest_value = (
            _required_text(manifest_digest_value, "invalid_manifest_digest")
            if manifest_digest_value is not None
            else None
        )
        denominator = _normalize_nonnegative_int(
            mandatory_denominator, "invalid_publication_metadata"
        )
        sites_value = self._coalesce_publication_alias(
            site_coverage, sites, "invalid_publication_metadata"
        )
        sites_tuple = _normalize_publication_tokens(
            sites_value, allow_single_text=False
        )
        setup_identity_value = self._coalesce_publication_alias(
            setup_manifest_identity,
            setup_manifest_work_unit_identity,
            "invalid_publication_metadata",
        )
        runtime_identity_value = self._coalesce_publication_alias(
            runtime_manifest_identity,
            runtime_manifest_work_unit_identity,
            "invalid_publication_metadata",
        )
        setup_identity = _normalize_publication_object(setup_identity_value)
        runtime_identity = _normalize_publication_object(runtime_identity_value)
        receipt_value = self._coalesce_publication_alias(
            receipt_identities, receipt_set, "invalid_publication_metadata"
        )
        receipt_tuple = _normalize_publication_tokens(receipt_value)
        s4_identity_value = self._coalesce_publication_alias(
            s4_authority_packet_identities,
            s4_packet_identities,
            "invalid_publication_metadata",
        )
        s4_digest_value = self._coalesce_publication_alias(
            s4_authority_packet_digests,
            s4_packet_digests,
            "invalid_publication_metadata",
        )
        s4_identity_tuple = _normalize_publication_tokens(s4_identity_value)
        s4_digest_tuple = _normalize_publication_tokens(s4_digest_value)
        receipt_digest = _optional_text(
            receipt_set_digest, "invalid_publication_metadata"
        )
        r5_id_value = self._coalesce_publication_alias(
            r5_authority_packet_id,
            self._coalesce_publication_alias(
                r5_authority_packet_identity,
                r5_packet_id,
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        r5_digest_value = self._coalesce_publication_alias(
            r5_authority_packet_digest,
            r5_packet_digest,
            "invalid_publication_metadata",
        )
        r5_id = _optional_text(r5_id_value, "invalid_publication_metadata")
        r5_digest = _optional_text(
            r5_digest_value, "invalid_publication_metadata"
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing_for_key = self._find_publication_by_key(
                    project_text, key_text
                )
                if (
                    existing_for_key is not None
                    and existing_for_key.run_id != launch.run_id
                ):
                    raise IdempotencyConflictError()
                existing_for_run = self._find_publication_by_run(
                    project_text, launch.run_id
                )
                existing = existing_for_run or existing_for_key
                if existing is not None:
                    if (
                        existing.publication_revision != revision_text
                        or existing.publication_fingerprint != fingerprint_text
                    ):
                        raise IdempotencyConflictError()
                    connection.commit()
                    return ResultPublication(
                        **{
                            **existing.__dict__,
                            "replayed": True,
                        }
                    )
                now = self._now()
                connection.execute(
                    """INSERT INTO r7_result_publications(
                        project_id, run_id, public_run_token, idempotency_key,
                        publication_revision, publication_fingerprint,
                        mode, execution_basis, snapshot_token, snapshot_ref,
                        source_revision_id, data_cutoff, setup_manifest_digest,
                        manifest_revision, manifest_digest, mandatory_denominator,
                        site_coverage_json, setup_manifest_identity_json,
                        runtime_manifest_identity_json, receipt_identities_json,
                        receipt_set_digest, r5_authority_packet_id,
                        r5_authority_packet_digest,
                        s4_authority_packet_identities_json,
                        s4_authority_packet_digests_json, publication_state,
                        failure_code, failure_message, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        project_text,
                        launch.run_id,
                        launch.public_run_token,
                        key_text,
                        revision_text,
                        fingerprint_text,
                        launch.mode,
                        launch.execution_basis,
                        snapshot_text,
                        snapshot_ref_text,
                        source_text,
                        cutoff_text,
                        setup_digest,
                        manifest_revision_value,
                        manifest_digest_value,
                        denominator,
                        _json_token_list(sites_tuple),
                        canonical_json(setup_identity),
                        canonical_json(runtime_identity),
                        _json_token_list(receipt_tuple),
                        receipt_digest,
                        r5_id,
                        r5_digest,
                        _json_token_list(s4_identity_tuple),
                        _json_token_list(s4_digest_tuple),
                        PUBLICATION_STATE_PUBLISHING,
                        None,
                        None,
                        now,
                        now,
                    ),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_result_publications "
                    "WHERE project_id = ? AND run_id = ?",
                    (project_text, launch.run_id),
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("publication_not_found")
                return self._row_to_publication(row)
            except IdempotencyConflictError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except sqlite3.IntegrityError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                existing = self._find_publication_by_run(
                    project_text, launch.run_id
                )
                if (
                    existing is not None
                    and existing.publication_revision == revision_text
                    and existing.publication_fingerprint == fingerprint_text
                ):
                    return ResultPublication(
                        **{
                            **existing.__dict__,
                            "replayed": True,
                        }
                    )
                raise IdempotencyConflictError()
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    reserve_result_publication = reserve_publication

    def bind_publication_runtime_manifest(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: Any = PUBLICATION_REVISION,
        runtime_manifest_revision: Optional[int] = None,
        runtime_manifest_identity: Any = None,
        runtime_manifest_digest: Optional[str] = None,
        mandatory_denominator: Optional[int] = None,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
        expected_state: Optional[str] = None,
        expected_publication_state: Optional[str] = None,
        fingerprint: Optional[str] = None,
        expected_fingerprint: Optional[str] = None,
        expected_publication_fingerprint: Optional[str] = None,
        request_fingerprint: Optional[str] = None,
        manifest_revision: Optional[int] = None,
        manifest_digest: Optional[str] = None,
        runtime_manifest_work_unit_identity: Any = None,
        runtime_manifest: Any = None,
        runtime_mandatory_denominator: Optional[int] = None,
        denominator: Optional[int] = None,
        setup_manifest_identity: Any = None,
        setup_manifest_work_unit_identity: Any = None,
    ) -> ResultPublication:
        """CAS-bind the runtime manifest after reserving a publication.

        Runtime identity is deliberately bound in its own transaction.  The
        product publication path must reserve first, read runtime progress and
        manifest facts second, and only then evaluate the receipt/R5 gates.
        This method never opens the launch result flag.
        """
        project_text, launch = self._publication_project_run(
            project,
            run,
            project_id=project_id,
            run_id=run_id,
            public_run_token=public_run_token,
        )
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )

        expected_value = self._coalesce_publication_alias(
            expected_state,
            expected_publication_state,
            "invalid_publication_state",
        )
        expected = (
            _required_text(expected_value, "invalid_publication_state")
            if expected_value is not None
            else PUBLICATION_STATE_PUBLISHING
        )
        if expected not in PUBLICATION_STATE_VALUES:
            raise LaunchRegistryError("invalid_publication_state")

        fingerprint_value = self._coalesce_publication_alias(
            fingerprint,
            self._coalesce_publication_alias(
                expected_fingerprint,
                self._coalesce_publication_alias(
                    expected_publication_fingerprint,
                    request_fingerprint,
                    "invalid_publication_fingerprint",
                ),
                "invalid_publication_fingerprint",
            ),
            "invalid_publication_fingerprint",
        )
        expected_fingerprint_text = (
            _required_text(fingerprint_value, "invalid_publication_fingerprint")
            if fingerprint_value is not None
            else None
        )

        runtime_revision_value = self._coalesce_publication_alias(
            runtime_manifest_revision,
            manifest_revision,
            "invalid_publication_revision",
        )
        if runtime_revision_value is None:
            raise LaunchRegistryError("invalid_publication_metadata")
        runtime_revision_text = _normalize_optional_positive_int(
            runtime_revision_value, "invalid_publication_revision"
        )
        if runtime_revision_text is None:
            raise LaunchRegistryError("invalid_publication_metadata")

        runtime_identity_value = self._coalesce_publication_alias(
            runtime_manifest_identity,
            self._coalesce_publication_alias(
                runtime_manifest_work_unit_identity,
                runtime_manifest,
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        if runtime_identity_value is None:
            raise LaunchRegistryError("invalid_publication_metadata")
        runtime_identity = _normalize_publication_object(runtime_identity_value)
        if not runtime_identity:
            raise LaunchRegistryError("invalid_publication_metadata")
        try:
            runtime_work_units = _manifest_work_unit_mapping(runtime_identity)
        except LaunchRegistryError as exc:
            raise LaunchRegistryError("invalid_publication_metadata") from exc
        if not runtime_work_units:
            raise LaunchRegistryError("invalid_publication_metadata")

        runtime_digest_value = self._coalesce_publication_alias(
            runtime_manifest_digest,
            manifest_digest,
            "invalid_manifest_digest",
        )
        if runtime_digest_value is None:
            raise LaunchRegistryError("invalid_publication_metadata")
        runtime_digest_text = _required_text(
            runtime_digest_value, "invalid_manifest_digest"
        )

        denominator_value = self._coalesce_publication_alias(
            mandatory_denominator,
            self._coalesce_publication_alias(
                runtime_mandatory_denominator,
                denominator,
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        derived_denominator = sum(
            1 for _, mandatory in runtime_work_units if mandatory
        )
        denominator_text = (
            _normalize_nonnegative_int(
                denominator_value, "invalid_publication_metadata"
            )
            if denominator_value is not None
            else derived_denominator
        )
        if denominator_text != derived_denominator:
            raise LaunchRegistryError("publication_cas_conflict")

        setup_identity_value = self._coalesce_publication_alias(
            setup_manifest_identity,
            setup_manifest_work_unit_identity,
            "invalid_publication_metadata",
        )
        supplied_setup_identity = (
            _normalize_publication_object(setup_identity_value)
            if setup_identity_value is not None
            else None
        )

        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
                if current.publication_state != expected:
                    raise LaunchRegistryError("publication_cas_conflict")
                if (
                    expected_fingerprint_text is not None
                    and current.publication_fingerprint != expected_fingerprint_text
                ):
                    raise IdempotencyConflictError()
                if current.publication_state != PUBLICATION_STATE_PUBLISHING:
                    raise LaunchRegistryError("illegal_publication_transition")

                try:
                    setup_work_units = _manifest_work_unit_mapping(
                        current.setup_manifest_identity
                    )
                except LaunchRegistryError as exc:
                    raise LaunchRegistryError("publication_cas_conflict") from exc
                if current.setup_manifest_identity:
                    if setup_work_units != runtime_work_units:
                        raise LaunchRegistryError("publication_cas_conflict")
                    setup_denominator = sum(
                        1 for _, mandatory in setup_work_units if mandatory
                    )
                    if setup_denominator != denominator_text:
                        raise LaunchRegistryError("publication_cas_conflict")
                if supplied_setup_identity is not None:
                    try:
                        supplied_setup_work_units = _manifest_work_unit_mapping(
                            supplied_setup_identity
                        )
                    except LaunchRegistryError as exc:
                        raise LaunchRegistryError(
                            "invalid_publication_metadata"
                        ) from exc
                    if supplied_setup_work_units != runtime_work_units:
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        current.setup_manifest_identity
                        and supplied_setup_identity
                        != current.setup_manifest_identity
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                if current.setup_manifest_identity:
                    if current.mandatory_denominator != denominator_text:
                        raise LaunchRegistryError("publication_cas_conflict")
                elif (
                    current.mandatory_denominator != 0
                    and current.mandatory_denominator != denominator_text
                ):
                    raise LaunchRegistryError("publication_cas_conflict")

                already_bound = (
                    current.manifest_revision is not None
                    or current.manifest_digest is not None
                    or bool(current.runtime_manifest_identity)
                )
                bound_values_match = (
                    current.manifest_revision == runtime_revision_text
                    and current.manifest_digest == runtime_digest_text
                    and current.runtime_manifest_identity == runtime_identity
                    and current.mandatory_denominator == denominator_text
                )
                if already_bound:
                    if not bound_values_match:
                        raise LaunchRegistryError("publication_cas_conflict")
                    connection.commit()
                    return ResultPublication(
                        **{**current.__dict__, "replayed": True}
                    )

                updated_at = self._now()
                updated = connection.execute(
                    "UPDATE r7_result_publications SET "
                    "manifest_revision = ?, manifest_digest = ?, "
                    "mandatory_denominator = ?, runtime_manifest_identity_json = ?, "
                    "updated_at = ? WHERE project_id = ? AND run_id = ? "
                    "AND publication_revision = ? AND publication_state = ? "
                    "AND publication_fingerprint = ?",
                    (
                        runtime_revision_text,
                        runtime_digest_text,
                        denominator_text,
                        canonical_json(runtime_identity),
                        updated_at,
                        project_text,
                        launch.run_id,
                        revision_text,
                        PUBLICATION_STATE_PUBLISHING,
                        current.publication_fingerprint,
                    ),
                )
                if updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                self._inject_failure(
                    "bind_publication_runtime_manifest.after_update"
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_result_publications "
                    "WHERE project_id = ? AND run_id = ? "
                    "AND publication_revision = ?",
                    (project_text, launch.run_id, revision_text),
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("publication_not_found")
                return self._row_to_publication(row)
            except IdempotencyConflictError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except Exception as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    bind_runtime_manifest = bind_publication_runtime_manifest
    bind_publication_manifest = bind_publication_runtime_manifest

    def get_publication(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
    ) -> ResultPublication:
        selector = self._coalesce_publication_alias(
            run_id,
            public_run_token,
            "run_not_found",
        )
        project_text, launch = self._publication_project_run(
            project, run, project_id=project_id, run_id=selector
        )
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        with self._lock:
            publication = self._find_publication_by_run(project_text, launch.run_id)
        if publication is None or publication.publication_revision != revision_text:
            raise LaunchRegistryError("publication_not_found")
        return publication

    get_result_publication = get_publication
    get_publication_by_run = get_publication
    get_publication_for_run = get_publication
    publication_for_run = get_publication

    def get_publication_by_public_token(
        self,
        public_run_token: str,
        *,
        project_id: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        revision: Optional[int] = None,
    ) -> ResultPublication:
        return self.get_publication(
            project_id=project_id,
            run=public_run_token,
            publication_revision=publication_revision,
            revision=revision,
        )

    publication_by_public_token = get_publication_by_public_token

    def get_publication_by_result_context_token(
        self,
        result_context_token: str,
        *,
        project_id: Optional[str] = None,
    ) -> ResultPublication:
        project = self._project(project_id)
        token = _normalize_result_context_token(
            result_context_token, "publication_not_found"
        )
        if token is None:
            raise LaunchRegistryError("publication_not_found")
        with self._lock:
            row = self._require_conn().execute(
                "SELECT * FROM r7_result_publications "
                "WHERE project_id = ? AND result_context_token = ?",
                (project, token),
            ).fetchone()
        if row is None:
            raise LaunchRegistryError("publication_not_found")
        return self._row_to_publication(row)

    get_result_publication_by_context_token = (
        get_publication_by_result_context_token
    )
    publication_by_result_context_token = (
        get_publication_by_result_context_token
    )
    get_by_result_context_token = get_publication_by_result_context_token
    resolve_result_context_token = get_publication_by_result_context_token
    get_publication_by_context_token = get_publication_by_result_context_token
    publication_for_result_context = get_publication_by_result_context_token

    def get_publication_by_idempotency(
        self,
        idempotency_key: str,
        *,
        project_id: Optional[str] = None,
    ) -> ResultPublication:
        project = self._project(project_id)
        key = _required_text(idempotency_key, "invalid_idempotency_key")
        with self._lock:
            publication = self._find_publication_by_key(project, key)
        if publication is None:
            raise LaunchRegistryError("publication_not_found")
        return publication

    def list_publications(
        self, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> Tuple[ResultPublication, ...]:
        project = self._project(project_id)
        bounded = self._history_limit(limit)
        with self._lock:
            rows = self._require_conn().execute(
                "SELECT * FROM r7_result_publications "
                "WHERE project_id = ? "
                "ORDER BY created_at DESC, sequence DESC LIMIT ?",
                (project, bounded),
            ).fetchall()
            return tuple(self._row_to_publication(row) for row in rows)

    result_publications = list_publications
    list_result_publications = list_publications
    publication_history = list_publications

    def _publication_row_for_update(
        self,
        connection: sqlite3.Connection,
        project: str,
        run_id: str,
        revision: int,
    ) -> ResultPublication:
        row = connection.execute(
            "SELECT * FROM r7_result_publications "
            "WHERE project_id = ? AND run_id = ? AND publication_revision = ?",
            (project, run_id, revision),
        ).fetchone()
        if row is None:
            raise LaunchRegistryError("publication_not_found")
        return self._row_to_publication(row)

    @staticmethod
    def _publication_failure_state(value: Any) -> str:
        target = _required_text(value, "invalid_publication_state")
        if target not in (
            PUBLICATION_STATE_RECOVERABLE_FAILED,
            PUBLICATION_STATE_BLOCKED,
        ):
            raise LaunchRegistryError("invalid_publication_state")
        return target

    def record_publication_failure(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: Any = PUBLICATION_REVISION,
        state: Optional[str] = None,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
        failure_state: Optional[str] = None,
        target_state: Optional[str] = None,
        expected_state: Optional[str] = None,
        expected_publication_state: Optional[str] = None,
        current_state: Optional[str] = None,
        error_code: Optional[str] = None,
        failure_code: Optional[str] = None,
        code: Optional[str] = None,
        error_message: Optional[str] = None,
        failure_message: Optional[str] = None,
        message: Optional[str] = None,
        reason_code: Optional[str] = None,
        reason: Optional[str] = None,
        failure_reason: Optional[str] = None,
    ) -> ResultPublication:
        # A compact positional form permits
        # ``record_publication_failure(project, run, "blocked")``.
        if isinstance(publication_revision, str) and state is None:
            state = publication_revision
            publication_revision = PUBLICATION_REVISION
        target = self._publication_failure_state(
            self._coalesce_publication_alias(
                state,
                self._coalesce_publication_alias(
                    failure_state,
                    target_state,
                    "invalid_publication_state",
                ),
                "invalid_publication_state",
            )
            or PUBLICATION_STATE_RECOVERABLE_FAILED
        )
        project_text, launch = self._publication_project_run(
            project,
            run,
            project_id=project_id,
            run_id=run_id,
            public_run_token=public_run_token,
        )
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        expected_value = self._coalesce_publication_alias(
            expected_state,
            self._coalesce_publication_alias(
                expected_publication_state,
                current_state,
                "invalid_publication_state",
            ),
            "invalid_publication_state",
        )
        expected = (
            _required_text(expected_value, "invalid_publication_state")
            if expected_value is not None
            else None
        )
        if expected is not None and expected not in PUBLICATION_STATE_VALUES:
            raise LaunchRegistryError("invalid_publication_state")
        code_value = self._coalesce_publication_alias(
            error_code,
            self._coalesce_publication_alias(
                failure_code,
                self._coalesce_publication_alias(
                    code,
                    reason_code,
                    "invalid_publication_metadata",
                ),
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        message_value = self._coalesce_publication_alias(
            error_message,
            self._coalesce_publication_alias(
                failure_message,
                self._coalesce_publication_alias(
                    message,
                    self._coalesce_publication_alias(
                        reason,
                        failure_reason,
                        "invalid_publication_metadata",
                    ),
                    "invalid_publication_metadata",
                ),
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        code_text = (
            _required_text(code_value, "invalid_publication_metadata")
            if code_value is not None
            else None
        )
        message_text = (
            _required_text(message_value, "invalid_publication_metadata")
            if message_value is not None
            else None
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
                if expected is not None and current.publication_state != expected:
                    raise LaunchRegistryError("publication_cas_conflict")
                if current.publication_state == target:
                    if code_text is None and message_text is None:
                        connection.commit()
                        return current
                elif target not in _PUBLICATION_ALLOWED_TRANSITIONS.get(
                    current.publication_state, frozenset()
                ):
                    raise LaunchRegistryError("illegal_publication_transition")
                effective_code = (
                    code_text if code_text is not None else current.failure_code
                )
                effective_message = (
                    message_text
                    if message_text is not None
                    else current.failure_message
                )
                updated_at = self._now()
                where = (
                    "project_id = ? AND run_id = ? "
                    "AND publication_revision = ? AND publication_state = ?"
                )
                updated = connection.execute(
                    "UPDATE r7_result_publications SET "
                    "publication_state = ?, failure_code = ?, "
                    "failure_message = ?, updated_at = ? WHERE " + where,
                    (
                        target,
                        effective_code,
                        effective_message,
                        updated_at,
                        project_text,
                        launch.run_id,
                        revision_text,
                        current.publication_state,
                    ),
                )
                if updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_result_publications "
                    "WHERE project_id = ? AND run_id = ? AND publication_revision = ?",
                    (project_text, launch.run_id, revision_text),
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("publication_not_found")
                return self._row_to_publication(row)
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc
    record_publication_error = record_publication_failure
    mark_publication_failure = record_publication_failure

    def retry_publication(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
        expected_state: Optional[str] = None,
    ) -> ResultPublication:
        project_text, launch = self._publication_project_run(
            project,
            run,
            project_id=project_id,
            run_id=run_id,
            public_run_token=public_run_token,
        )
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        expected = (
            _required_text(expected_state, "invalid_publication_state")
            if expected_state is not None
            else None
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
                if expected is not None and current.publication_state != expected:
                    raise LaunchRegistryError("publication_cas_conflict")
                if current.publication_state == PUBLICATION_STATE_PUBLISHING:
                    connection.commit()
                    return current
                if current.publication_state not in (
                    PUBLICATION_STATE_RECOVERABLE_FAILED,
                    PUBLICATION_STATE_BLOCKED,
                ):
                    raise LaunchRegistryError("illegal_publication_transition")
                updated = connection.execute(
                    "UPDATE r7_result_publications SET "
                    "publication_state = ?, failure_code = NULL, "
                    "failure_message = NULL, updated_at = ? "
                    "WHERE project_id = ? AND run_id = ? "
                    "AND publication_revision = ? AND publication_state = ?",
                    (
                        PUBLICATION_STATE_PUBLISHING,
                        self._now(),
                        project_text,
                        launch.run_id,
                        revision_text,
                        current.publication_state,
                    ),
                )
                if updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                connection.commit()
                return self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    resume_publication = retry_publication

    def update_publication_state(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        state: str = PUBLICATION_STATE_PUBLISHING,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        revision: Optional[int] = None,
        expected_state: Optional[str] = None,
    ) -> ResultPublication:
        target = _required_text(state, "invalid_publication_state")
        if target not in PUBLICATION_STATE_VALUES:
            raise LaunchRegistryError("invalid_publication_state")
        if target == PUBLICATION_STATE_AVAILABLE:
            raise LaunchRegistryError("illegal_publication_transition")
        if target in (
            PUBLICATION_STATE_RECOVERABLE_FAILED,
            PUBLICATION_STATE_BLOCKED,
        ):
            return self.record_publication_failure(
                project,
                run,
                publication_revision,
                target,
                project_id=project_id,
                run_id=run_id,
                revision=revision,
                expected_state=expected_state,
            )
        return self.retry_publication(
            project,
            run,
            publication_revision,
            project_id=project_id,
            run_id=run_id,
            revision=revision,
            expected_state=expected_state,
        )

    set_publication_state = update_publication_state
    cas_publication_state = update_publication_state

    def finalize_publication(
        self,
        project: Optional[str] = None,
        run: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        project_id: Optional[str] = None,
        run_id: Optional[str] = None,
        public_run_token: Optional[str] = None,
        revision: Optional[int] = None,
        expected_state: Optional[str] = None,
        expected_publication_state: Optional[str] = None,
        current_state: Optional[str] = None,
        fingerprint: Optional[str] = None,
        expected_fingerprint: Optional[str] = None,
        expected_publication_fingerprint: Optional[str] = None,
        request_fingerprint: Optional[str] = None,
        receipt_identities: Optional[Iterable[Any]] = None,
        receipt_set: Optional[Iterable[Any]] = None,
        receipt_set_digest: Optional[str] = None,
        receipt_digest: Optional[str] = None,
        r5_authority_packet_id: Optional[str] = None,
        r5_authority_packet_identity: Optional[str] = None,
        r5_packet_id: Optional[str] = None,
        r5_authority_packet_digest: Optional[str] = None,
        r5_packet_digest: Optional[str] = None,
        s4_authority_packet_identities: Optional[Iterable[Any]] = None,
        s4_packet_identities: Optional[Iterable[Any]] = None,
        s4_authority_packet_digests: Optional[Iterable[Any]] = None,
        s4_packet_digests: Optional[Iterable[Any]] = None,
        r6_output_set_digest: Optional[str] = None,
        artifact_member_ids: Optional[Iterable[Any]] = None,
        artifact_members: Optional[Iterable[Any]] = None,
        artifact_member_set: Optional[Iterable[Any]] = None,
        artifact_member_set_digest: Optional[str] = None,
        artifact_members_digest: Optional[str] = None,
        require_continuity_plan: bool = False,
        expected_plan_digest: Optional[str] = None,
    ) -> ResultPublication:
        """Atomically make a publication available and open its result flag.

        The publication CAS and launch-row update share one ``BEGIN
        IMMEDIATE`` transaction.  A failure between either update and commit
        rolls both changes back, preventing a one-sided result entry.
        """
        project_text, launch = self._publication_project_run(
            project,
            run,
            project_id=project_id,
            run_id=run_id,
            public_run_token=public_run_token,
        )
        revision_text = self._publication_revision_alias(
            publication_revision, revision
        )
        expected_value = self._coalesce_publication_alias(
            expected_state,
            self._coalesce_publication_alias(
                expected_publication_state,
                current_state,
                "invalid_publication_state",
            ),
            "invalid_publication_state",
        )
        expected = (
            _required_text(expected_value, "invalid_publication_state")
            if expected_value is not None
            else None
        )
        if expected is not None and expected not in PUBLICATION_STATE_VALUES:
            raise LaunchRegistryError("invalid_publication_state")
        fingerprint_value = self._coalesce_publication_alias(
            fingerprint,
            self._coalesce_publication_alias(
                expected_fingerprint,
                self._coalesce_publication_alias(
                    expected_publication_fingerprint,
                    request_fingerprint,
                    "invalid_publication_fingerprint",
                ),
                "invalid_publication_fingerprint",
            ),
            "invalid_publication_fingerprint",
        )
        if fingerprint_value is not None:
            fingerprint_text = _required_text(
                fingerprint_value, "invalid_publication_fingerprint"
            )
        else:
            fingerprint_text = None
        receipt_value = self._coalesce_publication_alias(
            receipt_identities, receipt_set, "invalid_publication_metadata"
        )
        receipt_tuple = (
            None
            if receipt_value is None
            else _normalize_publication_tokens(receipt_value)
        )
        digest_value = self._coalesce_publication_alias(
            receipt_set_digest,
            receipt_digest,
            "invalid_publication_metadata",
        )
        receipt_digest_text = (
            _optional_text(digest_value, "invalid_publication_metadata")
            if digest_value is not None
            else None
        )
        r5_id_value = self._coalesce_publication_alias(
            r5_authority_packet_id,
            self._coalesce_publication_alias(
                r5_authority_packet_identity,
                r5_packet_id,
                "invalid_publication_metadata",
            ),
            "invalid_publication_metadata",
        )
        r5_digest_value = self._coalesce_publication_alias(
            r5_authority_packet_digest,
            r5_packet_digest,
            "invalid_publication_metadata",
        )
        r5_id = (
            _optional_text(r5_id_value, "invalid_publication_metadata")
            if r5_id_value is not None
            else None
        )
        r5_digest = (
            _optional_text(r5_digest_value, "invalid_publication_metadata")
            if r5_digest_value is not None
            else None
        )
        s4_identity_value = self._coalesce_publication_alias(
            s4_authority_packet_identities,
            s4_packet_identities,
            "invalid_publication_metadata",
        )
        s4_digest_value = self._coalesce_publication_alias(
            s4_authority_packet_digests,
            s4_packet_digests,
            "invalid_publication_metadata",
        )
        s4_identity_tuple = (
            None
            if s4_identity_value is None
            else _normalize_publication_tokens(s4_identity_value)
        )
        s4_digest_tuple = (
            None
            if s4_digest_value is None
            else _normalize_publication_tokens(s4_digest_value)
        )
        r6_out_digest_val = self._coalesce_publication_alias(
            r6_output_set_digest, None, "invalid_publication_metadata"
        )
        r6_output_set_digest_text = (
            _optional_text(r6_out_digest_val, "invalid_publication_metadata")
            if r6_out_digest_val is not None
            else None
        )
        if r6_output_set_digest_text is not None:
            if len(r6_output_set_digest_text) != 64 or any(c not in "0123456789abcdef" for c in r6_output_set_digest_text.lower()):
                raise LaunchRegistryError("invalid_publication_metadata")
            r6_output_set_digest_text = r6_output_set_digest_text.lower()

        member_ids_val = self._coalesce_publication_alias(
            artifact_member_ids,
            self._coalesce_publication_alias(
                artifact_members, artifact_member_set, "invalid_publication_metadata"
            ),
            "invalid_publication_metadata",
        )
        if member_ids_val is not None:
            raw_members = [str(x).strip() for x in member_ids_val]
            if any(not m for m in raw_members):
                raise LaunchRegistryError("invalid_publication_metadata")
            if not raw_members:
                raise LaunchRegistryError("invalid_publication_metadata")
            if sorted(raw_members) != raw_members or len(set(raw_members)) != len(raw_members):
                raise LaunchRegistryError("invalid_publication_metadata")
            member_ids_tuple = tuple(raw_members)
        else:
            member_ids_tuple = None

        member_set_digest_val = self._coalesce_publication_alias(
            artifact_member_set_digest,
            artifact_members_digest,
            "invalid_publication_metadata",
        )
        member_set_digest_text = (
            _optional_text(member_set_digest_val, "invalid_publication_metadata")
            if member_set_digest_val is not None
            else None
        )
        if member_set_digest_text is not None:
            if len(member_set_digest_text) != 64 or any(c not in "0123456789abcdef" for c in member_set_digest_text.lower()):
                raise LaunchRegistryError("invalid_publication_metadata")
            member_set_digest_text = member_set_digest_text.lower()
            if member_ids_tuple is not None:
                expected_member_digest = content_digest(list(member_ids_tuple))
                if member_set_digest_text != expected_member_digest:
                    raise LaunchRegistryError("invalid_publication_metadata")

        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._publication_row_for_update(
                    connection, project_text, launch.run_id, revision_text
                )
                continuity_row = self._continuity_plan_row(
                    connection,
                    project_text,
                    target_run_id=launch.run_id,
                )
                if continuity_row is None:
                    if require_continuity_plan or expected_plan_digest is not None:
                        raise LaunchRegistryError("continuity_plan_not_found")
                    continuity_plan = None
                else:
                    continuity_plan = self._row_to_continuity_plan(
                        connection, continuity_row
                    )
                    if continuity_plan.status not in (
                        CONTINUITY_PLAN_STATE_VERIFIED,
                        CONTINUITY_PLAN_STATE_PUBLISHED,
                    ):
                        raise LaunchRegistryError(
                            "continuity_plan_not_verified"
                        )
                    if expected_plan_digest is not None:
                        expected_digest = _required_text(
                            expected_plan_digest,
                            "continuity_plan_cas_conflict",
                        )
                        if continuity_plan.plan_digest != expected_digest:
                            raise LaunchRegistryError(
                                "continuity_plan_cas_conflict"
                            )
                if expected is not None and current.publication_state != expected:
                    raise LaunchRegistryError("publication_cas_conflict")
                if continuity_plan is not None:
                    if (
                        continuity_plan.status
                        == CONTINUITY_PLAN_STATE_PUBLISHED
                        and current.publication_state
                        != PUBLICATION_STATE_AVAILABLE
                    ):
                        raise LaunchRegistryError(
                            "continuity_publication_conflict"
                        )
                    if (
                        continuity_plan.status
                        == CONTINUITY_PLAN_STATE_VERIFIED
                        and current.publication_state
                        not in (
                            PUBLICATION_STATE_PUBLISHING,
                            PUBLICATION_STATE_AVAILABLE,
                        )
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                if continuity_plan is not None:
                    effective_r5_digest = (
                        r5_digest
                        if r5_digest is not None
                        else current.r5_authority_packet_digest
                    )
                    effective_receipt_digest = (
                        receipt_digest_text
                        if receipt_digest_text is not None
                        else current.receipt_set_digest
                    )
                    effective_r6_output_set_digest = (
                        r6_output_set_digest_text
                        if r6_output_set_digest_text is not None
                        else current.r6_output_set_digest
                    )
                    if (
                        continuity_plan.r5_authority_digest != effective_r5_digest
                        or continuity_plan.r6_publication_digest
                        != current.publication_fingerprint
                        or continuity_plan.r6_receipt_digest
                        != effective_receipt_digest
                        or (continuity_plan.r6_output_set_digest and continuity_plan.r6_output_set_digest != effective_r6_output_set_digest)
                        or (effective_r6_output_set_digest and continuity_plan.r6_output_set_digest != effective_r6_output_set_digest)
                    ):
                        raise LaunchRegistryError(
                            "continuity_publication_conflict"
                        )
                if (
                    fingerprint_text is not None
                    and current.publication_fingerprint != fingerprint_text
                ):
                    raise IdempotencyConflictError()
                if current.publication_state == PUBLICATION_STATE_AVAILABLE:
                    if (
                        receipt_tuple is not None
                        and receipt_tuple != current.receipt_identities
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        receipt_digest_text is not None
                        and receipt_digest_text != current.receipt_set_digest
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if r5_id is not None and r5_id != current.r5_authority_packet_id:
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        r5_digest is not None
                        and r5_digest != current.r5_authority_packet_digest
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        s4_identity_tuple is not None
                        and s4_identity_tuple
                        != current.s4_authority_packet_identities
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        s4_digest_tuple is not None
                        and s4_digest_tuple
                        != current.s4_authority_packet_digests
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        r6_output_set_digest_text is not None
                        and r6_output_set_digest_text != current.r6_output_set_digest
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        member_ids_tuple is not None
                        and member_ids_tuple != current.artifact_member_ids
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        member_set_digest_text is not None
                        and member_set_digest_text != current.artifact_member_set_digest
                    ):
                        raise LaunchRegistryError("publication_cas_conflict")
                    if (
                        continuity_plan is not None
                        and continuity_plan.status
                        == CONTINUITY_PLAN_STATE_VERIFIED
                    ):
                        self._mark_continuity_plan_published_locked(
                            connection,
                            project_text,
                            continuity_plan,
                        )
                    self._inject_failure("finalize.before_commit")
                    connection.commit()
                    return ResultPublication(
                        **{**current.__dict__, "replayed": True}
                    )
                if current.publication_state not in (
                    PUBLICATION_STATE_PUBLISHING,
                    PUBLICATION_STATE_RECOVERABLE_FAILED,
                    PUBLICATION_STATE_BLOCKED,
                ):
                    raise LaunchRegistryError("illegal_publication_transition")
                if launch.run_state != STATE_COMPLETED:
                    raise LaunchRegistryError("run_not_completed")
                result_context_token = _normalize_result_context_token(
                    current.result_context_token
                )
                if result_context_token is None:
                    for _ in range(16):
                        candidate = (
                            RESULT_CONTEXT_TOKEN_PREFIX + uuid4().hex
                        )
                        occupied = connection.execute(
                            "SELECT 1 FROM r7_result_publications "
                            "WHERE project_id = ? AND result_context_token = ?",
                            (project_text, candidate),
                        ).fetchone()
                        if occupied is None:
                            result_context_token = candidate
                            break
                    if result_context_token is None:
                        raise LaunchRegistryError("store_closed")


                def _effective_tuple(
                    provided: Optional[Tuple[str, ...]],
                    existing: Tuple[str, ...],
                ) -> Tuple[str, ...]:
                    # Completion-dependent receipt/member facts are bound by
                    # finalize, not by the request fingerprint.  A retry may
                    # therefore replace a provisional pre-finalize value.
                    return existing if provided is None else provided

                effective_receipts = _effective_tuple(
                    receipt_tuple, current.receipt_identities
                )
                effective_s4_ids = _effective_tuple(
                    s4_identity_tuple, current.s4_authority_packet_identities
                )
                effective_s4_digests = _effective_tuple(
                    s4_digest_tuple, current.s4_authority_packet_digests
                )
                def _effective_text(
                    provided: Optional[str], existing: Optional[str]
                ) -> Optional[str]:
                    return existing if provided is None else provided

                effective_receipt_digest = _effective_text(
                    receipt_digest_text, current.receipt_set_digest
                )
                effective_r5_id = _effective_text(
                    r5_id, current.r5_authority_packet_id
                )
                effective_r5_digest = _effective_text(
                    r5_digest, current.r5_authority_packet_digest
                )
                effective_r6_output_set_digest = _effective_text(
                    r6_output_set_digest_text, current.r6_output_set_digest
                )
                effective_member_ids = (
                    member_ids_tuple
                    if member_ids_tuple is not None
                    else current.artifact_member_ids
                )
                effective_member_set_digest = _effective_text(
                    member_set_digest_text, current.artifact_member_set_digest
                )
                if effective_member_ids and effective_member_set_digest is None:
                    effective_member_set_digest = content_digest(list(effective_member_ids))
                if (
                    len(effective_member_ids) != 4
                    or effective_r6_output_set_digest is None
                    or len(effective_r6_output_set_digest) != 64
                    or effective_member_set_digest
                    != content_digest(list(effective_member_ids))
                ):
                    raise LaunchRegistryError("invalid_publication_metadata")

                updated_at = self._now()
                where = (
                    "project_id = ? AND run_id = ? "
                    "AND publication_revision = ? AND publication_state = ?"
                )
                updated = connection.execute(
                    "UPDATE r7_result_publications SET "
                    "publication_state = ?, result_context_token = ?, "
                    "receipt_identities_json = ?, "
                    "receipt_set_digest = ?, r5_authority_packet_id = ?, "
                    "r5_authority_packet_digest = ?, "
                    "s4_authority_packet_identities_json = ?, "
                    "s4_authority_packet_digests_json = ?, "
                    "r6_output_set_digest = ?, "
                    "artifact_member_ids_json = ?, "
                    "artifact_member_set_digest = ?, "
                    "failure_code = NULL, failure_message = NULL, "
                    "updated_at = ? WHERE " + where,
                    (
                        PUBLICATION_STATE_AVAILABLE,
                        result_context_token,
                        _json_token_list(effective_receipts),
                        effective_receipt_digest,
                        effective_r5_id,
                        effective_r5_digest,
                        _json_token_list(effective_s4_ids),
                        _json_token_list(effective_s4_digests),
                        effective_r6_output_set_digest,
                        _json_token_list(effective_member_ids),
                        effective_member_set_digest,
                        updated_at,
                        project_text,
                        launch.run_id,
                        revision_text,
                        current.publication_state,
                    ),
                )
                if updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                self._inject_failure("finalize.after_publication_update")
                launch_updated = connection.execute(
                    "UPDATE r7_launch_registry SET "
                    "result_available = 1, main_action = ?, updated_at = ? "
                    "WHERE project_id = ? AND sequence = ? "
                    "AND run_state = ?",
                    (
                        _RESULT_MAIN_ACTION,
                        updated_at,
                        project_text,
                        launch.sequence,
                        STATE_COMPLETED,
                    ),
                )
                if launch_updated.rowcount != 1:
                    raise LaunchRegistryError("publication_cas_conflict")
                self._inject_failure("finalize.after_launch_update")
                if (
                    continuity_plan is not None
                    and continuity_plan.status
                    == CONTINUITY_PLAN_STATE_VERIFIED
                ):
                    self._mark_continuity_plan_published_locked(
                        connection,
                        project_text,
                        continuity_plan,
                        updated_at=updated_at,
                    )
                self._inject_failure("finalize.before_commit")
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_result_publications "
                    "WHERE project_id = ? AND run_id = ? "
                    "AND publication_revision = ?",
                    (project_text, launch.run_id, revision_text),
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("publication_not_found")
                return self._row_to_publication(row)
            except IdempotencyConflictError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except Exception as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    publish_publication = finalize_publication
    finalize_result_publication = finalize_publication
    mark_publication_available = finalize_publication
    cas_finalize_publication = finalize_publication

    @staticmethod
    def _coerce_continuity_plan(value: Any) -> CarryForwardPlan:
        if isinstance(value, CarryForwardPlan):
            plan = value
        elif isinstance(value, Mapping):
            try:
                plan = CarryForwardPlan.from_mapping(value)
            except (PlanValidationError, TypeError, ValueError) as exc:
                raise LaunchRegistryError("invalid_continuity_plan") from exc
        else:
            raise LaunchRegistryError("invalid_continuity_plan")
        try:
            validate_carry_forward_plan(plan)
        except (PlanValidationError, TypeError, ValueError) as exc:
            raise LaunchRegistryError("invalid_continuity_plan") from exc
        return plan

    @staticmethod
    def _continuity_plan_id(plan: CarryForwardPlan) -> str:
        return derive_continuity_plan_id(plan)

    @staticmethod
    def _continuity_plan_json(plan: CarryForwardPlan) -> str:
        payload = plan.as_dict()
        payload["items"] = [item.as_dict() for item in plan.items]
        if plan.baseline is not None:
            payload["baseline"] = plan.baseline.as_dict()
        return canonical_json(payload)

    @staticmethod
    def _continuity_item_evidence_json(item: CarryForwardItem) -> str:
        return canonical_json(
            {
                "evidence_summary": item.evidence_summary,
                "evidence_refs": list(item.evidence_refs),
                "closure_evidence_refs": list(item.closure_evidence_refs),
            }
        )

    @staticmethod
    def _decode_continuity_json(value: Any) -> Any:
        try:
            return json.loads(str(value))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise LaunchRegistryError("store_closed") from exc

    @classmethod
    def _decode_continuity_mapping(cls, value: Any) -> Mapping[str, Any]:
        decoded = cls._decode_continuity_json(value)
        if not isinstance(decoded, Mapping):
            raise LaunchRegistryError("store_closed")
        return decoded

    @classmethod
    def _row_to_continuity_plan(
        cls,
        connection: sqlite3.Connection,
        row: sqlite3.Row,
    ) -> CarryForwardPlan:
        try:
            payload = cls._decode_continuity_mapping(row["plan_json"])
            plan = CarryForwardPlan.from_mapping(payload)
            expected_plan_id = cls._continuity_plan_id(plan)
            if (
                str(row["plan_id"]) != expected_plan_id
                or str(row["project_id"]) != plan.project_id
                or str(row["target_run_id"]) != plan.target_run_id
                or str(row["mode"]) != plan.mode
                or str(row["execution_basis"]) != plan.execution_basis
                or str(row["target_snapshot_id"]) != plan.target_snapshot_id
                or str(row["target_data_cutoff"]) != plan.target_data_cutoff
                or str(row["target_decision_version"]) != plan.target_decision_version
                or str(row["target_rule_revision_ids_json"])
                != canonical_json(list(plan.target_rule_revision_ids))
                or str(row["baseline_source_run_id"]) != plan.baseline_source_run_id
                or str(row["baseline_source_publication_id"])
                != plan.baseline_source_publication_id
                or str(row["baseline_source_public_run_token"])
                != plan.baseline_source_public_run_token
                or str(row["r5_authority_digest"]) != plan.r5_authority_digest
                or str(row["r6_publication_digest"]) != plan.r6_publication_digest
                or str(row["r6_receipt_digest"]) != plan.r6_receipt_digest
                or (
                    "r6_output_set_digest" in row.keys()
                    and str(row["r6_output_set_digest"]) != plan.r6_output_set_digest
                )
                or str(row["plan_digest"]) != plan.plan_digest
                or str(row["status"]) != plan.status
                or str(row["counts_json"]) != canonical_json(plan.counts)
                or str(row["created_at"]) != plan.created_at
                or str(row["updated_at"]) != plan.updated_at
                or str(row["plan_json"]) != cls._continuity_plan_json(plan)
            ):
                raise LaunchRegistryError("store_closed")
            baseline = plan.baseline
            expected_source = (
                (
                    baseline.source_run_id,
                    baseline.source_publication_id,
                    baseline.source_public_run_token,
                )
                if baseline is not None
                else (
                    plan.baseline_source_run_id,
                    plan.baseline_source_publication_id,
                    plan.baseline_source_public_run_token,
                )
            )
            if (
                str(row["source_run_id"]) != expected_source[0]
                or str(row["source_publication_id"]) != expected_source[1]
                or str(row["source_public_run_token"]) != expected_source[2]
            ):
                raise LaunchRegistryError("store_closed")
            target_launch = connection.execute(
                "SELECT public_run_token, mode, execution_basis, "
                "current_snapshot_token, data_cutoff "
                "FROM r7_launch_registry WHERE project_id = ? AND run_id = ?",
                (plan.project_id, plan.target_run_id),
            ).fetchone()
            stored_target_token = row["target_public_run_token"]
            if target_launch is None:
                if stored_target_token is not None:
                    raise LaunchRegistryError("store_closed")
            elif (
                stored_target_token != target_launch["public_run_token"]
                or str(target_launch["mode"]) != plan.mode
                or str(target_launch["execution_basis"])
                != plan.execution_basis
                or str(target_launch["current_snapshot_token"])
                != plan.target_snapshot_id
                or str(target_launch["data_cutoff"]) != plan.target_data_cutoff
            ):
                raise LaunchRegistryError("store_closed")
            item_rows = connection.execute(
                "SELECT * FROM r7_continuity_items "
                "WHERE plan_id = ? ORDER BY ordinal ASC, sequence ASC",
                (expected_plan_id,),
            ).fetchall()
            if len(item_rows) != len(plan.items):
                raise LaunchRegistryError("store_closed")
            for expected, item_row in zip(plan.items, item_rows):
                item_payload = cls._decode_continuity_mapping(item_row["item_json"])
                item = CarryForwardItem.from_mapping(item_payload)
                expected_evidence = cls._continuity_item_evidence_json(expected)
                denormalized = (
                    int(item_row["ordinal"]) == expected.ordinal
                    and str(item_row["object_type"]) == expected.object_type
                    and str(item_row["object_ref"]) == expected.object_ref
                    and str(item_row["disposition"]) == expected.disposition
                    and str(item_row["source_run_id"]) == expected.source_run_id
                    and str(item_row["source_publication_id"])
                    == expected.source_publication_id
                    and str(item_row["source_public_run_token"])
                    == expected.source_public_run_token
                    and str(item_row["source_object_id"]) == expected.source_object_id
                    and str(item_row["target_object_id"]) == expected.target_object_id
                    and str(item_row["source_artifact_id"])
                    == expected.source_artifact_id
                    and str(item_row["source_artifact_sha256"])
                    == expected.source_artifact_sha256
                    and (
                        item_row["prior_risk_state"] == expected.prior_risk_state
                    )
                    and (
                        item_row["current_risk_state"] == expected.current_risk_state
                    )
                    and item_row["prior_severity"] == expected.prior_severity
                    and item_row["current_severity"] == expected.current_severity
                    and str(item_row["governing_rule_revision_ids_json"])
                    == canonical_json(list(expected.governing_rule_revision_ids))
                    and str(item_row["changed_applicable_rule_ids_json"])
                    == canonical_json(list(expected.changed_applicable_rule_ids))
                    and str(item_row["attribution"]) == expected.attribution
                    and str(item_row["evidence_json"]) == expected_evidence
                    and str(item_row["item_digest"]) == expected.item_digest
                    and item == expected
                    and str(item_row["item_json"])
                    == canonical_json(expected.as_dict())
                )
                if (
                    str(item_row["plan_id"]) != expected_plan_id
                    or not denormalized
                ):
                    raise LaunchRegistryError("store_closed")
            return plan
        except LaunchRegistryError:
            raise
        except (PlanValidationError, TypeError, ValueError, KeyError) as exc:
            raise LaunchRegistryError("store_closed") from exc

    @staticmethod
    def _continuity_plan_row(
        connection: sqlite3.Connection,
        project: str,
        *,
        target_run_id: Optional[str] = None,
        plan_id: Optional[str] = None,
    ) -> Optional[sqlite3.Row]:
        if plan_id is not None:
            query = (
                "SELECT * FROM r7_continuity_plans "
                "WHERE project_id = ? AND plan_id = ?"
            )
            params: list[Any] = [project, plan_id]
            if target_run_id is not None:
                query += " AND target_run_id = ?"
                params.append(target_run_id)
            return connection.execute(query, tuple(params)).fetchone()
        if target_run_id is not None:
            return connection.execute(
                "SELECT * FROM r7_continuity_plans "
                "WHERE project_id = ? AND target_run_id = ?",
                (project, target_run_id),
            ).fetchone()
        raise LaunchRegistryError("continuity_plan_not_found")

    def _continuity_lookup(
        self,
        project_id: Optional[str],
        target_run_id: Optional[str],
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Tuple[str, Optional[str], Optional[str]]:
        if isinstance(project_id, CarryForwardPlan):
            plan_value = project_id
            project_id = plan_value.project_id
            if target_run_id is None:
                target_run_id = plan_value.target_run_id
            if plan_id is None:
                plan_id = self._continuity_plan_id(plan_value)
        # With a default project, a single positional value is naturally a
        # target-run selector.  With no default project callers use
        # (project_id, target_run_id), matching the publication API.
        if (
            target_run_id is None
            and plan_id is None
            and selector is None
            and run_id is None
            and project_id is not None
            and self._default_project_id
        ):
            target_run_id = project_id
            project_id = None
        if (
            plan_id is None
            and target_run_id is not None
            and isinstance(target_run_id, str)
            and target_run_id.startswith("r7-plan-")
        ):
            plan_id = target_run_id
            target_run_id = None
        if run_id is not None:
            if target_run_id is not None and target_run_id != run_id:
                raise LaunchRegistryError("continuity_plan_cas_conflict")
            target_run_id = run_id
        if selector is not None:
            selector_text = _required_text(
                selector, "continuity_plan_not_found"
            )
            if (
                target_run_id is not None
                and target_run_id != selector_text
                or plan_id is not None
                and plan_id != selector_text
            ):
                raise LaunchRegistryError("continuity_plan_cas_conflict")
            if plan_id is None and target_run_id is None:
                if selector_text.startswith("r7-plan-"):
                    plan_id = selector_text
                else:
                    target_run_id = selector_text
        project = self._project(project_id)
        normalized_plan_id = (
            _required_text(plan_id, "continuity_plan_not_found")
            if plan_id is not None
            else None
        )
        normalized_target = (
            _required_text(target_run_id, "continuity_plan_not_found")
            if target_run_id is not None
            else None
        )
        if normalized_plan_id is None and normalized_target is None:
            raise LaunchRegistryError("continuity_plan_not_found")
        return project, normalized_target, normalized_plan_id

    def save_continuity_plan(
        self,
        plan: Any,
        project_id: Optional[str] = None,
        *,
        target_run_id: Optional[str] = None,
    ) -> CarryForwardPlan:
        # Also accept save_continuity_plan(project_id, plan) for consistency
        # with the older project-first registry methods.
        if isinstance(plan, str) and isinstance(
            project_id, (CarryForwardPlan, Mapping)
        ):
            plan, project_id = project_id, plan
        prepared = self._coerce_continuity_plan(plan)
        if prepared.status != CONTINUITY_PLAN_STATE_STAGING:
            raise LaunchRegistryError("invalid_continuity_plan")
        project = self._project(
            project_id if project_id is not None else prepared.project_id
        )
        if prepared.project_id != project:
            raise LaunchRegistryError("invalid_project_id")
        if target_run_id is not None and (
            _required_text(target_run_id, "continuity_plan_not_found")
            != prepared.target_run_id
        ):
            raise LaunchRegistryError("continuity_plan_cas_conflict")
        plan_id = self._continuity_plan_id(prepared)
        plan_json = self._continuity_plan_json(prepared)
        counts_json = canonical_json(prepared.counts)
        baseline = prepared.baseline
        source_run_id = (
            baseline.source_run_id
            if baseline is not None
            else prepared.baseline_source_run_id
        )
        source_publication_id = (
            baseline.source_publication_id
            if baseline is not None
            else prepared.baseline_source_publication_id
        )
        source_public_run_token = (
            baseline.source_public_run_token
            if baseline is not None
            else prepared.baseline_source_public_run_token
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = self._continuity_plan_row(
                    connection, project, target_run_id=prepared.target_run_id
                )
                if existing is not None:
                    if str(existing["plan_digest"]) != prepared.plan_digest:
                        raise IdempotencyConflictError()
                    existing_plan = self._row_to_continuity_plan(
                        connection, existing
                    )
                    connection.commit()
                    return existing_plan
                publication_row = connection.execute(
                    "SELECT publication_state FROM r7_result_publications "
                    "WHERE project_id = ? AND run_id = ? "
                    "AND publication_revision = ?",
                    (project, prepared.target_run_id, PUBLICATION_REVISION),
                ).fetchone()
                if (
                    publication_row is not None
                    and str(publication_row["publication_state"])
                    == PUBLICATION_STATE_AVAILABLE
                ):
                    raise LaunchRegistryError(
                        "continuity_publication_conflict"
                    )
                target_row = connection.execute(
                    "SELECT public_run_token, mode, execution_basis, "
                    "current_snapshot_token, data_cutoff "
                    "FROM r7_launch_registry "
                    "WHERE project_id = ? AND run_id = ?",
                    (project, prepared.target_run_id),
                ).fetchone()
                if target_row is not None and (
                    str(target_row["mode"]) != prepared.mode
                    or str(target_row["execution_basis"])
                    != prepared.execution_basis
                    or str(target_row["current_snapshot_token"])
                    != prepared.target_snapshot_id
                    or str(target_row["data_cutoff"])
                    != prepared.target_data_cutoff
                ):
                    raise LaunchRegistryError("continuity_publication_conflict")
                target_public_run_token = (
                    str(target_row["public_run_token"])
                    if target_row is not None
                    else None
                )
                connection.execute(
                    """INSERT INTO r7_continuity_plans(
                        plan_id, project_id, target_run_id,
                        target_public_run_token, source_run_id,
                        source_publication_id, source_public_run_token, mode,
                        execution_basis, target_snapshot_id, target_data_cutoff,
                        target_rule_revision_ids_json, target_decision_version,
                        baseline_source_run_id, baseline_source_publication_id,
                        baseline_source_public_run_token, r5_authority_digest,
                        r6_publication_digest, r6_receipt_digest, r6_output_set_digest, plan_digest,
                        status, counts_json, plan_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        plan_id,
                        project,
                        prepared.target_run_id,
                        target_public_run_token,
                        source_run_id,
                        source_publication_id,
                        source_public_run_token,
                        prepared.mode,
                        prepared.execution_basis,
                        prepared.target_snapshot_id,
                        prepared.target_data_cutoff,
                        canonical_json(list(prepared.target_rule_revision_ids)),
                        prepared.target_decision_version,
                        prepared.baseline_source_run_id,
                        prepared.baseline_source_publication_id,
                        prepared.baseline_source_public_run_token,
                        prepared.r5_authority_digest,
                        prepared.r6_publication_digest,
                        prepared.r6_receipt_digest,
                        prepared.r6_output_set_digest,
                        prepared.plan_digest,
                        prepared.status,
                        counts_json,
                        plan_json,
                        prepared.created_at,
                        prepared.updated_at,
                    ),
                )
                self._inject_failure("continuity.after_plan_insert")
                self._inject_failure("continuity.save.after_plan")
                for item in prepared.items:
                    connection.execute(
                        """INSERT INTO r7_continuity_items(
                            plan_id, ordinal, object_type, object_ref,
                            disposition, source_run_id, source_publication_id,
                            source_public_run_token, source_object_id,
                            target_object_id, source_artifact_id,
                            source_artifact_sha256, prior_risk_state,
                            current_risk_state, prior_severity, current_severity,
                            governing_rule_revision_ids_json,
                            changed_applicable_rule_ids_json, attribution,
                            evidence_json, item_digest, item_json,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                  ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            plan_id,
                            item.ordinal,
                            item.object_type,
                            item.object_ref,
                            item.disposition,
                            item.source_run_id,
                            item.source_publication_id,
                            item.source_public_run_token,
                            item.source_object_id,
                            item.target_object_id,
                            item.source_artifact_id,
                            item.source_artifact_sha256,
                            item.prior_risk_state,
                            item.current_risk_state,
                            item.prior_severity,
                            item.current_severity,
                            canonical_json(
                                list(item.governing_rule_revision_ids)
                            ),
                            canonical_json(
                                list(item.changed_applicable_rule_ids)
                            ),
                            item.attribution,
                            self._continuity_item_evidence_json(item),
                            item.item_digest,
                            canonical_json(item.as_dict()),
                            prepared.created_at,
                            prepared.updated_at,
                        ),
                    )
                    self._inject_failure(
                        "continuity.after_item_insert"
                    )
                    self._inject_failure(
                        "continuity.save.after_item_%d" % item.ordinal
                    )
                self._inject_failure("continuity.save.before_commit")
                self._inject_failure("continuity.before_commit")
                connection.commit()
                row = self._continuity_plan_row(
                    connection, project, target_run_id=prepared.target_run_id
                )
                if row is None:
                    raise LaunchRegistryError("continuity_plan_not_found")
                return self._row_to_continuity_plan(connection, row)
            except IdempotencyConflictError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc
            except Exception as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    persist_continuity_plan = save_continuity_plan
    store_continuity_plan = save_continuity_plan
    create_continuity_plan = save_continuity_plan
    save_carry_forward_plan = save_continuity_plan
    persist_carry_forward_plan = save_continuity_plan

    def get_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> CarryForwardPlan:
        project, target, continuity_id = self._continuity_lookup(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        )
        with self._lock:
            row = self._continuity_plan_row(
                self._require_conn(),
                project,
                target_run_id=target,
                plan_id=continuity_id,
            )
            if row is None:
                raise LaunchRegistryError("continuity_plan_not_found")
            return self._row_to_continuity_plan(self._require_conn(), row)

    load_continuity_plan = get_continuity_plan
    get_carry_forward_plan = get_continuity_plan
    load_carry_forward_plan = get_continuity_plan
    get_plan = get_continuity_plan

    def get_continuity_plan_by_id(
        self, plan_id: str, *, project_id: Optional[str] = None
    ) -> CarryForwardPlan:
        return self.get_continuity_plan(
            project_id, plan_id=plan_id
        )

    def get_continuity_plan_by_target(
        self, target_run_id: str, *, project_id: Optional[str] = None
    ) -> CarryForwardPlan:
        return self.get_continuity_plan(
            project_id, target_run_id=target_run_id
        )

    def list_continuity_plans(
        self,
        project_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Tuple[CarryForwardPlan, ...]:
        project = self._project(project_id)
        bounded = self._history_limit(limit)
        with self._lock:
            connection = self._require_conn()
            rows = connection.execute(
                "SELECT * FROM r7_continuity_plans "
                "WHERE project_id = ? "
                "ORDER BY created_at DESC, sequence DESC LIMIT ?",
                (project, bounded),
            ).fetchall()
            return tuple(
                self._row_to_continuity_plan(connection, row) for row in rows
            )

    list_carry_forward_plans = list_continuity_plans

    def list_continuity_items(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Tuple[CarryForwardItem, ...]:
        return self.get_continuity_plan(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        ).items

    get_continuity_items = list_continuity_items
    list_carry_forward_items = list_continuity_items
    get_carry_forward_items = list_continuity_items

    def get_continuity_item(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        ordinal: int = 0,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> CarryForwardItem:
        ordinal_value = _normalize_nonnegative_int(
            ordinal, "continuity_item_not_found"
        )
        items = self.list_continuity_items(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        )
        for item in items:
            if item.ordinal == ordinal_value:
                return item
        raise LaunchRegistryError("continuity_item_not_found")

    load_continuity_item = get_continuity_item

    def _update_continuity_status_locked(
        self,
        connection: sqlite3.Connection,
        project: str,
        plan: CarryForwardPlan,
        target_status: str,
        *,
        expected_status: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
        failure_prefix: str = "continuity.status",
    ) -> CarryForwardPlan:
        if target_status not in CONTINUITY_PLAN_STATE_VALUES:
            raise LaunchRegistryError("illegal_continuity_transition")
        if (
            target_status in (CONTINUITY_PLAN_STATE_VERIFIED, CONTINUITY_PLAN_STATE_PUBLISHED)
            and not plan.r6_output_set_digest
        ):
            raise LaunchRegistryError("continuity_plan_not_verified")
        if expected_status is not None:
            expected_status = _required_text(
                expected_status, "continuity_plan_cas_conflict"
            )
            if plan.status != expected_status:
                raise LaunchRegistryError("continuity_plan_cas_conflict")
        if expected_plan_digest is not None:
            expected_plan_digest = _required_text(
                expected_plan_digest, "continuity_plan_cas_conflict"
            )
            if plan.plan_digest != expected_plan_digest:
                raise LaunchRegistryError("continuity_plan_cas_conflict")
        if target_status not in _CONTINUITY_ALLOWED_TRANSITIONS[plan.status]:
            raise LaunchRegistryError("illegal_continuity_transition")
        if target_status == plan.status:
            return plan
        if target_status == CONTINUITY_PLAN_STATE_PUBLISHED:
            raise LaunchRegistryError("continuity_plan_not_verified")
        updated_at = self._now()
        transitioned = replace(
            plan,
            status=target_status,
            updated_at=updated_at,
            plan_digest="",
        )
        updated = connection.execute(
            "UPDATE r7_continuity_plans SET status = ?, plan_json = ?, "
            "updated_at = ? WHERE project_id = ? AND plan_id = ? "
            "AND status = ? AND plan_digest = ?",
            (
                transitioned.status,
                self._continuity_plan_json(transitioned),
                transitioned.updated_at,
                project,
                self._continuity_plan_id(plan),
                plan.status,
                plan.plan_digest,
            ),
        )
        if updated.rowcount != 1:
            raise LaunchRegistryError("continuity_plan_cas_conflict")
        self._inject_failure(failure_prefix + ".after_update")
        self._inject_failure("continuity.after_status_update")
        return transitioned
    def _mark_continuity_plan_published_locked(
        self,
        connection: sqlite3.Connection,
        project: str,
        plan: CarryForwardPlan,
        *,
        updated_at: Optional[str] = None,
    ) -> CarryForwardPlan:
        if plan.status == CONTINUITY_PLAN_STATE_PUBLISHED:
            return plan
        if plan.status != CONTINUITY_PLAN_STATE_VERIFIED or not plan.r6_output_set_digest:
            raise LaunchRegistryError("continuity_plan_not_verified")
        transitioned = replace(
            plan,
            status=CONTINUITY_PLAN_STATE_PUBLISHED,
            updated_at=updated_at or self._now(),
            plan_digest="",
        )
        updated = connection.execute(
            "UPDATE r7_continuity_plans SET status = ?, plan_json = ?, "
            "updated_at = ? WHERE project_id = ? AND plan_id = ? "
            "AND status = ? AND plan_digest = ?",
            (
                transitioned.status,
                self._continuity_plan_json(transitioned),
                transitioned.updated_at,
                project,
                self._continuity_plan_id(plan),
                CONTINUITY_PLAN_STATE_VERIFIED,
                plan.plan_digest,
            ),
        )
        if updated.rowcount != 1:
            raise LaunchRegistryError("continuity_plan_cas_conflict")
        self._inject_failure("finalize.after_continuity_update")
        self._inject_failure("continuity.publish.after_update")
        return transitioned

    def update_continuity_plan_status(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        status: str = CONTINUITY_PLAN_STATE_VERIFIED,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        expected_status: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
    ) -> CarryForwardPlan:
        if (
            plan_id is None
            and self._default_project_id
            and isinstance(project_id, str)
            and project_id.startswith("r7-plan-")
            and target_run_id in CONTINUITY_PLAN_STATE_VALUES
            and status == CONTINUITY_PLAN_STATE_VERIFIED
        ):
            plan_id = project_id
            project_id = None
            status = target_run_id
            target_run_id = None
        project, target, continuity_id = self._continuity_lookup(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        )
        target_status = _required_text(
            status, "illegal_continuity_transition"
        )
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = self._continuity_plan_row(
                    connection,
                    project,
                    target_run_id=target,
                    plan_id=continuity_id,
                )
                if row is None:
                    raise LaunchRegistryError("continuity_plan_not_found")
                plan = self._row_to_continuity_plan(connection, row)
                transitioned = self._update_continuity_status_locked(
                    connection,
                    project,
                    plan,
                    target_status,
                    expected_status=expected_status,
                    expected_plan_digest=expected_plan_digest,
                )
                self._inject_failure("continuity.status.before_commit")
                self._inject_failure("continuity.before_commit")
                connection.commit()
                fresh = self._continuity_plan_row(
                    connection,
                    project,
                    target_run_id=plan.target_run_id,
                )
                if fresh is None:
                    raise LaunchRegistryError("continuity_plan_not_found")
                return self._row_to_continuity_plan(connection, fresh)
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc
            except Exception as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    set_continuity_plan_status = update_continuity_plan_status
    transition_continuity_plan = update_continuity_plan_status
    set_carry_forward_plan_status = update_continuity_plan_status

    def verify_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
    ) -> CarryForwardPlan:
        return self.update_continuity_plan_status(
            project_id,
            target_run_id,
            CONTINUITY_PLAN_STATE_VERIFIED,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
            expected_plan_digest=expected_plan_digest,
        )

    mark_continuity_plan_verified = verify_continuity_plan
    verify_carry_forward_plan = verify_continuity_plan

    def block_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
    ) -> CarryForwardPlan:
        return self.update_continuity_plan_status(
            project_id,
            target_run_id,
            CONTINUITY_PLAN_STATE_BLOCKED,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
            expected_plan_digest=expected_plan_digest,
        )

    def reopen_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        expected_plan_digest: Optional[str] = None,
    ) -> CarryForwardPlan:
        return self.update_continuity_plan_status(
            project_id,
            target_run_id,
            CONTINUITY_PLAN_STATE_STAGING,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
            expected_plan_digest=expected_plan_digest,
        )

    def publish_continuity_plan(
        self,
        project_id: Optional[str] = None,
        target_run_id: Optional[str] = None,
        publication_revision: int = PUBLICATION_REVISION,
        *,
        plan_id: Optional[str] = None,
        selector: Optional[str] = None,
        run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> ResultPublication:
        project, target, continuity_id = self._continuity_lookup(
            project_id,
            target_run_id,
            plan_id=plan_id,
            selector=selector,
            run_id=run_id,
        )
        expected_digest = kwargs.pop("expected_plan_digest", None)
        plan = self.get_continuity_plan(
            project,
            target_run_id=target,
            plan_id=continuity_id,
        )
        if target is None:
            target = plan.target_run_id
        if expected_digest is not None:
            expected_digest = _required_text(
                expected_digest, "continuity_plan_cas_conflict"
            )
            if plan.plan_digest != expected_digest:
                raise LaunchRegistryError("continuity_plan_cas_conflict")
        return self.finalize_publication(
            project,
            target,
            publication_revision,
            require_continuity_plan=True,
            expected_plan_digest=expected_digest,
            **kwargs,
        )

    publish_carry_forward_plan = publish_continuity_plan
    def get_by_idempotency(
        self, idempotency_key: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        project = self._project(project_id)
        key = _required_text(idempotency_key, "invalid_idempotency_key")
        with self._lock:
            record = self._find_by_key(project, key)
        if record is None:
            raise LaunchRegistryError("run_not_found")
        return record

    def get_by_public_token(
        self, public_run_token: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        project = self._project(project_id)
        token = _required_text(public_run_token, "public_run_not_found")
        with self._lock:
            record = self._find_by_selector(project, token)
        if record is None:
            raise LaunchRegistryError("public_run_not_found")
        return record

    def get(
        self, selector: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        project = self._project(project_id)
        value = _required_text(selector, "run_not_found")
        with self._lock:
            record = self._find_by_selector(project, value)
        if record is None:
            raise LaunchRegistryError("run_not_found")
        return record

    def get_public(
        self, public_run_token: str, *, project_id: Optional[str] = None
    ) -> dict[str, Any]:
        return self.get_by_public_token(public_run_token, project_id=project_id).public_projection()

    def list_records(
        self, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> Tuple[LaunchRecord, ...]:
        project = self._project(project_id)
        bounded = self._history_limit(limit)
        with self._lock:
            rows = self._require_conn().execute(
                "SELECT * FROM r7_launch_registry WHERE project_id = ? "
                "ORDER BY created_at DESC, sequence DESC LIMIT ?",
                (project, bounded),
            ).fetchall()
            return tuple(self._row_to_record(row) for row in rows)

    def list_history(
        self, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> list[dict[str, Any]]:
        return [record.public_projection() for record in self.list_records(project_id, limit=limit)]

    history = list_history
    list_public_history = list_history
    get_public_history = list_history
    def get_public_run(
        self, public_run_token: str, *, project_id: Optional[str] = None
    ) -> dict[str, Any]:
        return self.get_public(public_run_token, project_id=project_id)

    def resolve_public_token(
        self, project_id: str, public_run_token: str
    ) -> LaunchRecord:
        return self.get_by_public_token(public_run_token, project_id=project_id)

    def set_run_state(
        self, project_id: str, selector: str, state: str, **kwargs: Any
    ) -> LaunchRecord:
        return self.update_state(selector, state, project_id=project_id, **kwargs)
    list_runs = list_history

    def _history_limit(self, limit: Optional[int]) -> int:
        value = self._default_history_limit if limit is None else limit
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise LaunchRegistryError("invalid_history_limit")
        return min(value, self._max_history_limit)

    def update_state(
        self,
        selector: str,
        state: str,
        *,
        project_id: Optional[str] = None,
        result_available: Optional[bool] = None,
        main_action: Optional[str] = None,
        manifest_digest: Optional[str] = None,
    ) -> LaunchRecord:
        """Durably update state without changing request identity.

        A same-state update is idempotent.  ``result_available`` is only
        accepted for ``completed`` and remains false throughout Slice-07C-2.
        """
        project = self._project(project_id)
        target = _required_text(state, "invalid_run_state")
        if target not in RUN_STATE_VALUES:
            raise LaunchRegistryError("invalid_run_state")
        selector_text = _required_text(selector, "run_not_found")
        if result_available is not None and not isinstance(result_available, bool):
            raise LaunchRegistryError("invalid_result_state")
        if manifest_digest is not None:
            manifest_digest = _required_text(manifest_digest, "invalid_manifest_digest")
        if main_action is not None:
            main_action = _required_text(main_action, "invalid_result_state")
        with self._lock:
            connection = self._require_conn()
            try:
                connection.execute("BEGIN IMMEDIATE")
                current = self._find_by_selector(project, selector_text)
                if current is None:
                    connection.rollback()
                    raise LaunchRegistryError("run_not_found")
                if target not in _ALLOWED_TRANSITIONS[current.run_state]:
                    connection.rollback()
                    raise LaunchRegistryError("illegal_state_transition")
                available = (
                    current.result_available
                    if result_available is None
                    else result_available
                )
                if current.result_available and not available:
                    connection.rollback()
                    raise LaunchRegistryError("invalid_result_state")
                if available and target != STATE_COMPLETED:
                    connection.rollback()
                    raise LaunchRegistryError("invalid_result_state")
                if available and not current.result_available:
                    publication_row = connection.execute(
                        "SELECT publication_state FROM r7_result_publications "
                        "WHERE project_id = ? AND run_id = ? "
                        "AND publication_revision = ?",
                        (project, current.run_id, PUBLICATION_REVISION),
                    ).fetchone()
                    if (
                        publication_row is None
                        or publication_row["publication_state"]
                        != PUBLICATION_STATE_AVAILABLE
                    ):
                        connection.rollback()
                        raise LaunchRegistryError("invalid_result_state")
                expected_action = self._default_action(target, available)
                if main_action is not None and main_action != expected_action:
                    connection.rollback()
                    raise LaunchRegistryError("invalid_result_state")
                effective_action = expected_action
                effective_manifest = (
                    manifest_digest if manifest_digest is not None else current.manifest_digest
                )
                updated_at = self._now()
                updated = connection.execute(
                    "UPDATE r7_launch_registry SET "
                    "run_state = ?, result_available = ?, main_action = ?, "
                    "manifest_digest = ?, updated_at = ? "
                    "WHERE project_id = ? AND sequence = ?",
                    (
                        target,
                        int(available),
                        effective_action,
                        effective_manifest,
                        updated_at,
                        project,
                        current.sequence,
                    ),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM r7_launch_registry WHERE sequence = ?", (current.sequence,)
                ).fetchone()
                if row is None:
                    raise LaunchRegistryError("store_closed")
                return self._row_to_record(row)
            except LaunchRegistryError:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise
            except (sqlite3.Error, OSError) as exc:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    pass
                raise LaunchRegistryError("store_closed") from exc

    set_state = update_state

    def mark_waiting_start(
        self, selector: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        return self.update_state(selector, STATE_WAITING_START, project_id=project_id)

    def mark_running(self, selector: str, *, project_id: Optional[str] = None) -> LaunchRecord:
        return self.update_state(selector, STATE_RUNNING, project_id=project_id)

    def mark_started(self, selector: str, *, project_id: Optional[str] = None) -> LaunchRecord:
        return self.mark_running(selector, project_id=project_id)

    def mark_completed(
        self,
        selector: str,
        *,
        project_id: Optional[str] = None,
        result_available: bool = False,
    ) -> LaunchRecord:
        return self.update_state(
            selector,
            STATE_COMPLETED,
            project_id=project_id,
            result_available=result_available,
        )

    def mark_failed(self, selector: str, *, project_id: Optional[str] = None) -> LaunchRecord:
        return self.update_state(selector, STATE_FAILED, project_id=project_id)

    def record_start_failure(
        self, selector: str, *, project_id: Optional[str] = None
    ) -> LaunchRecord:
        """Keep the reserved run recoverable when background start fails."""
        return self.mark_waiting_start(selector, project_id=project_id)

    def record_manifest(
        self,
        selector: str,
        manifest_digest: str,
        *,
        project_id: Optional[str] = None,
    ) -> LaunchRecord:
        record = self.get(selector, project_id=project_id)
        return self.update_state(
            selector,
            record.run_state,
            project_id=project_id,
            manifest_digest=manifest_digest,
        )


# Store naming aliases used by adjacent R7 code and tests.
LaunchRegistryStore = LaunchRegistry
ResultPublicationStore = LaunchRegistry
PublicationStore = LaunchRegistry
RunLaunchRegistry = LaunchRegistry
LaunchResult = LaunchReservation
PublicRunRecord = LaunchRecord
PublicationResult = ResultPublication
request_fingerprint = compute_request_fingerprint
publication_fingerprint = compute_publication_fingerprint


__all__ = [
    "SCHEMA_VERSION_V1",
    "SCHEMA_VERSION_V2",
    "SCHEMA_VERSION_V3",
    "SCHEMA_VERSION_V4",
    "SCHEMA_VERSION",
    "LAUNCH_REGISTRY_DB_NAME",
    "BUSY_TIMEOUT_MS",
    "DEFAULT_HISTORY_LIMIT",
    "MAX_HISTORY_LIMIT",
    "RESULT_CONTEXT_TOKEN_PREFIX",
    "PUBLICATION_REVISION",
    "RESULT_PUBLICATION_REVISION",
    "RESULT_PUBLICATION_PUBLISHING",
    "RESULT_PUBLICATION_AVAILABLE",
    "RESULT_PUBLICATION_RECOVERABLE_FAILED",
    "RESULT_PUBLICATION_BLOCKED",
    "PUBLICATION_STATE_PUBLISHING",
    "PUBLICATION_STATE_AVAILABLE",
    "PUBLICATION_STATE_RECOVERABLE_FAILED",
    "PUBLICATION_STATE_BLOCKED",
    "PUBLICATION_STATE_VALUES",
    "PUBLICATION_PUBLISHING",
    "PUBLICATION_AVAILABLE",
    "PUBLICATION_RECOVERABLE_FAILED",
    "PUBLICATION_BLOCKED",
    "RESULT_PUBLICATION_STATE_VALUES",
    "MODE_DAILY",
    "MODE_PRE_LOCK",
    "MODE_POST_LOCK_PRE_CFDI",
    "CONTINUITY_PLAN_STATE_STAGING",
    "CONTINUITY_PLAN_STATE_VERIFIED",
    "CONTINUITY_PLAN_STATE_PUBLISHED",
    "CONTINUITY_PLAN_STATE_BLOCKED",
    "CONTINUITY_PLAN_STATE_VALUES",
    "CONTINUITY_PLAN_STATUS_STAGING",
    "CONTINUITY_PLAN_STATUS_VERIFIED",
    "CONTINUITY_PLAN_STATUS_PUBLISHED",
    "CONTINUITY_PLAN_STATUS_BLOCKED",
    "CONTINUITY_PLAN_STATUS_VALUES",
    "CONTINUITY_PLAN_STAGING",
    "CONTINUITY_PLAN_VERIFIED",
    "CONTINUITY_PLAN_PUBLISHED",
    "CONTINUITY_PLAN_BLOCKED",
    "SUPPORTED_MODES",
    "BASIS_FULL",
    "BASIS_INCREMENTAL",
    "SUPPORTED_EXECUTION_BASES",
    "STATE_WAITING_START",
    "STATE_RUNNING",
    "STATE_STOPPING",
    "STATE_INTERRUPTED_RESUMABLE",
    "STATE_COMPLETED",
    "STATE_ENDED_INCOMPLETE",
    "STATE_FAILED",
    "RUN_STATE_VALUES",
    "LaunchRegistryError",
    "IdempotencyConflictError",
    "LaunchRequest",
    "LaunchRecord",
    "CarryForwardItem",
    "CarryForwardPlan",
    "PlanValidationError",
    "LaunchReservation",
    "ResultPublication",
    "PublicationResult",
    "canonical_json",
    "content_digest",
    "normalize_request",
    "canonical_request_fingerprint",
    "compute_request_fingerprint",
    "publication_fingerprint_payload",
    "compute_publication_fingerprint",
    "canonical_publication_fingerprint",
    "compute_result_publication_fingerprint",
    "public_run_token",
    "request_fingerprint",
    "publication_fingerprint",
    "derive_public_run_token",
    "derive_continuity_plan_id",
    "LaunchRegistry",
    "LaunchRegistryStore",
    "ResultPublicationStore",
    "PublicationStore",
    "RunLaunchRegistry",
    "LaunchResult",
    "PublicRunRecord",
]
