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
# W01-R26（20260926）：v5在v4之上仅新增两个可空冻结read model引用列，
# open()对存量v4文件按守卫式ALTER原地升级，不重建表。
SCHEMA_VERSION_V5 = "mm-r7-w01r26-launch-registry-v5"
SCHEMA_VERSION = SCHEMA_VERSION_V5
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


def _coalesce_publication_alias(primary: Any, alias: Any, code: str) -> Any:
    if primary is not None and alias is not None and primary != alias:
        raise LaunchRegistryError(code)
    return primary if primary is not None else alias


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
    snapshot_value = _coalesce_publication_alias(
        snapshot_token, snapshot_option_token, "invalid_snapshot_token"
    )
    snapshot = _required_text(snapshot_value, "invalid_snapshot_token")
    source_value = _coalesce_publication_alias(
        source_revision_id, source_revision, "invalid_publication_metadata"
    )
    source = _required_text(source_value, "invalid_publication_metadata")
    cutoff = _required_text(data_cutoff, "invalid_data_cutoff")
    coverage = _normalize_publication_tokens(
        site_coverage, allow_single_text=False
    )
    identity_value = _coalesce_publication_alias(
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
    # W01-R26（20260926）：冻结read model引用列。可空：存量发布行无引用，
    # 读取侧对其保持既有重建比对路径。
    frozen_read_model_artifact_id: Optional[str] = None
    frozen_read_model_sha256: Optional[str] = None

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
    """Reject an existing legacy/unknown file before writable SQLite calls.

    W01-R26（20260926）例外：v4→v5仅新增两个可空引用列，v4文件由
    ``LaunchRegistry.open`` 以守卫式ALTER原地升级，因此放行标记为
    SCHEMA_VERSION_V4的legacy形状；更早版本仍须走staging迁移。
    """
    if not path.exists():
        return
    from .schema_manifest import SchemaClassification, inspect_member

    report = inspect_member(path, "launch_registry")
    if report.classification is SchemaClassification.CURRENT:
        return
    if (
        report.classification is SchemaClassification.LEGACY
        and report.schema_version == SCHEMA_VERSION_V4
    ):
        return
    raise LaunchRegistryError("unsupported_schema_version")
