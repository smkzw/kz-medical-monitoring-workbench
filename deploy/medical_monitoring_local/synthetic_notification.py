#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R8 G4 合成离线通知 seam。

消费既有运行终态，形成唯一通知事实、幂等 outbox、应用内持久记录、合成系统通道证据
和只导航意图。不创建、完成、取消、重试或修改运行；不启动服务、不调用模型、不读取
真实项目目录。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Tuple

from canonical_evidence import digest_ref

NOTIFICATION_SCHEMA = "mm-monitoring-r8-g4-synthetic-notification-v1"
NOTIFICATION_VERSION = "1"
CONTRACT_VERSION = "0.3"
ADAPTER_ID = "synthetic-notification-adapter"
ADAPTER_VERSION = "1"

CAPABILITY_STATES: Tuple[str, ...] = ("authorized", "denied", "unavailable", "unknown")
CHANNEL_EVIDENCE_STATES: Tuple[str, ...] = (
    "queued",
    "accepted_by_platform",
    "presented",
    "unknown",
)

NON_TERMINAL_STATUSES: FrozenSet[str] = frozenset(
    {"streaming", "checkpoint", "queued", "running"}
)
UPSTREAM_TERMINAL_STATUSES: FrozenSet[str] = frozenset(
    {
        "complete",
        "failed",
        "partial",
        "final_partial",
        "truncated",
        "timed_out",
        "cancelled",
        "interrupted",
        "blocked",
    }
)
NOTIFICATION_STATUSES: FrozenSet[str] = frozenset(
    {
        "analysis_complete",
        "failed",
        "partial",
        "final_partial",
        "truncated",
        "timed_out",
        "cancelled",
        "interrupted",
        "blocked",
    }
)
BLOCKING_ADMISSION_STATUSES: FrozenSet[str] = frozenset(
    {"revoked", "re_admission_required"}
)

NAVIGATION_BLOCKED_MESSAGE = "本次运行暂无法打开，请返回工作台查看项目运行记录。"
DISPLAY_NAME_UNAVAILABLE = "项目名称暂不可显示"

_SYSTEM_FORBIDDEN_PATTERNS: Tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        r"opaque-project:",
        r"opaque-admission:",
        r"opaque-run:",
        r"sha256:",
        r"[/\\]",
        r"\bPID\b",
        r"\b8911\b",
        r"\b5174\b",
        r"\b8984\b",
    )
)

USER_COPY: Dict[str, Dict[str, str]] = {
    "analysis_complete": {
        "title": "分析已完成",
        "body": "结果已生成，可前往工作台查看。",
        "action": "查看结果",
    },
    "failed": {
        "title": "分析未完成",
        "body": "本次运行未完成，可前往工作台查看原因。",
        "action": "查看原因",
    },
    "partial": {
        "title": "分析结果不完整",
        "body": "本次仅形成部分结果，可前往工作台查看。",
        "action": "查看已有结果",
    },
    "final_partial": {
        "title": "分析结果不完整",
        "body": "本次已停止形成新结果，现有内容不可作为完整依据。",
        "action": "查看原因",
    },
    "truncated": {
        "title": "分析结果不完整",
        "body": "本次结果未完整保留，可前往工作台查看。",
        "action": "查看详情",
    },
    "timed_out": {
        "title": "运行超时未完成",
        "body": "本次运行已停止等待，可前往工作台查看。",
        "action": "查看详情",
    },
    "cancelled": {
        "title": "分析已取消",
        "body": "本次运行已取消，可前往工作台查看记录。",
        "action": "查看运行记录",
    },
    "interrupted": {
        "title": "分析已中断",
        "body": "本次运行已中断，可前往工作台查看原因。",
        "action": "查看原因",
    },
    "blocked": {
        "title": "分析暂未继续",
        "body": "本次运行已停在当前步骤，可前往工作台查看原因。",
        "action": "查看原因",
    },
}

TARGET_KIND_BY_STATUS: Dict[str, str] = {
    "analysis_complete": "result",
    "failed": "explanation",
    "partial": "partial_result",
    "final_partial": "explanation",
    "truncated": "explanation",
    "timed_out": "explanation",
    "cancelled": "run_record",
    "interrupted": "explanation",
    "blocked": "explanation",
}


class NotificationError(ValueError):
    """合成通知输入、身份或回放无效。"""


def _copy_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NotificationError("%s_must_be_non_empty_string" % field)
    return value.strip()


def _identity_key(
    project_ref: str,
    admission_id: str,
    run_id: str,
    terminal_revision: str,
) -> Tuple[str, str, str, str]:
    return (project_ref, admission_id, run_id, terminal_revision)


@dataclass(frozen=True)
class TerminalEvent:
    """上游运行终态事件；完整绑定身份与 revision。"""

    project_ref: str
    admission_id: str
    run_id: str
    terminal_status: str
    terminal_revision: str
    authoritative: bool = True
    frozen: bool = True

    def __post_init__(self) -> None:
        _require_string(self.project_ref, "project_ref")
        _require_string(self.admission_id, "admission_id")
        _require_string(self.run_id, "run_id")
        _require_string(self.terminal_status, "terminal_status")
        _require_string(self.terminal_revision, "terminal_revision")
        if not isinstance(self.authoritative, bool) or not isinstance(self.frozen, bool):
            raise NotificationError("terminal_authority_invalid")

    @property
    def identity_key(self) -> Tuple[str, str, str, str]:
        return _identity_key(
            self.project_ref,
            self.admission_id,
            self.run_id,
            self.terminal_revision,
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "project_ref": self.project_ref,
            "admission_id": self.admission_id,
            "run_id": self.run_id,
            "terminal_status": self.terminal_status,
            "terminal_revision": self.terminal_revision,
            "authoritative": self.authoritative,
            "frozen": self.frozen,
        }


@dataclass(frozen=True)
class AdmissionBinding:
    """当前 admission 与合同绑定；用于可访问门与导航校验。"""

    project_ref: str
    admission_id: str
    admission_status: str
    binding_digest: str
    contract_version: str
    app_version: str
    registered_project_display_name: Optional[str] = None
    binding_valid: bool = True

    def __post_init__(self) -> None:
        _require_string(self.project_ref, "binding.project_ref")
        _require_string(self.admission_id, "binding.admission_id")
        _require_string(self.admission_status, "binding.admission_status")
        _require_string(self.binding_digest, "binding.binding_digest")
        _require_string(self.contract_version, "binding.contract_version")
        _require_string(self.app_version, "binding.app_version")


@dataclass(frozen=True)
class TargetAccessibility:
    """当前目标可访问门：同时绑定 revision、binding 与 source/output manifest。"""

    current_terminal_revision: str
    binding_digest: str
    source_manifest_digest: str
    output_manifest_digest: str
    target_exists: bool = False
    result_accessible: bool = False
    explanation_accessible: bool = False

    def __post_init__(self) -> None:
        _require_string(self.current_terminal_revision, "target.current_terminal_revision")
        _require_string(self.binding_digest, "target.binding_digest")
        _require_string(self.source_manifest_digest, "target.source_manifest_digest")
        _require_string(self.output_manifest_digest, "target.output_manifest_digest")
        if not all(
            isinstance(value, bool)
            for value in (
                self.target_exists,
                self.result_accessible,
                self.explanation_accessible,
            )
        ):
            raise NotificationError("target_accessibility_invalid")


@dataclass
class ProcessResult:
    """终态投影与持久化结果。"""

    status: str
    fact: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    created: bool = False


@dataclass
class NavigationIntentResult:
    """只导航意图结果；不产生新运行副作用。"""

    status: str
    intent: Optional[Dict[str, Any]] = None
    user_message: Optional[str] = None
    click_count: int = 0


def is_non_terminal_status(status: str) -> bool:
    return status in NON_TERMINAL_STATUSES


def is_upstream_terminal_status(status: str) -> bool:
    return status in UPSTREAM_TERMINAL_STATUSES


def project_notification_status(
    upstream_status: str,
    accessibility: TargetAccessibility,
) -> Optional[str]:
    """将上游终态投影为通知呈现状态；不可投影时返回 None。"""

    if is_non_terminal_status(upstream_status):
        return None
    if upstream_status == "complete":
        if not accessibility.result_accessible:
            return None
        return "analysis_complete"
    if upstream_status in UPSTREAM_TERMINAL_STATUSES:
        if upstream_status == "partial":
            if not accessibility.result_accessible:
                return None
        else:
            if not accessibility.explanation_accessible:
                return None
        return upstream_status
    return None


def _system_payload_allowed(title: str, body: str) -> bool:
    combined = title + body
    return not any(pattern.search(combined) for pattern in _SYSTEM_FORBIDDEN_PATTERNS)


def _resolve_in_app_display_name(binding: AdmissionBinding) -> str:
    if not binding.binding_valid:
        return DISPLAY_NAME_UNAVAILABLE
    name = binding.registered_project_display_name
    if not isinstance(name, str) or not name.strip():
        return DISPLAY_NAME_UNAVAILABLE
    return name.strip()


def _build_fact_body(
    event: TerminalEvent,
    binding: AdmissionBinding,
    accessibility: TargetAccessibility,
    notification_status: str,
    capability_state: str,
    channel_evidence: str,
) -> Dict[str, Any]:
    user_copy = dict(USER_COPY[notification_status])
    target_kind = TARGET_KIND_BY_STATUS[notification_status]
    body: Dict[str, Any] = {
        "schema": NOTIFICATION_SCHEMA,
        "version": NOTIFICATION_VERSION,
        "contract_version": CONTRACT_VERSION,
        "identity": {
            "project_ref": event.project_ref,
            "admission_id": event.admission_id,
            "run_id": event.run_id,
        },
        "terminal_status": event.terminal_status,
        "notification_status": notification_status,
        "terminal_revision": event.terminal_revision,
        "terminal_authoritative": event.authoritative,
        "terminal_frozen": event.frozen,
        "user_copy": user_copy,
        "system_copy": {
            "title": user_copy["title"],
            "body": user_copy["body"],
        },
        "in_app_copy": {
            "title": user_copy["title"],
            "body": user_copy["body"],
            "action": user_copy["action"],
            "project_display_name": _resolve_in_app_display_name(binding),
        },
        "binding_digest": binding.binding_digest,
        "source_manifest_digest": accessibility.source_manifest_digest,
        "output_manifest_digest": accessibility.output_manifest_digest,
        "contract_ref_version": binding.contract_version,
        "app_version": binding.app_version,
        "capability_state": capability_state,
        "channel_evidence": channel_evidence,
        "navigation_target": {
            "project_ref": event.project_ref,
            "admission_id": event.admission_id,
            "run_id": event.run_id,
            "terminal_revision": event.terminal_revision,
            "binding_digest": accessibility.binding_digest,
            "source_manifest_digest": accessibility.source_manifest_digest,
            "output_manifest_digest": accessibility.output_manifest_digest,
            "target_kind": target_kind,
            "action": "navigate_only",
        },
        "fact_digest": "",
    }
    body["fact_digest"] = digest_ref({k: v for k, v in body.items() if k != "fact_digest"})
    return body


class NotificationStore:
    """内存合成 store：按完整身份 + revision 幂等保存唯一事实、outbox 与应用内记录。"""

    def __init__(self) -> None:
        self._facts: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
        self._outbox: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
        self._in_app: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
        self._conflicts: List[Dict[str, Any]] = []
        self._frozen_terminal_by_run: Dict[Tuple[str, str, str], Dict[str, str]] = {}
        self._save_count: int = 0

    @property
    def save_count(self) -> int:
        return self._save_count

    @property
    def conflicts(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(_copy_json(item) for item in self._conflicts)

    def get_fact(self, key: Tuple[str, str, str, str]) -> Optional[Dict[str, Any]]:
        stored = self._facts.get(key)
        return _copy_json(stored) if stored is not None else None

    def get_outbox(self, key: Tuple[str, str, str, str]) -> Optional[Dict[str, Any]]:
        stored = self._outbox.get(key)
        return _copy_json(stored) if stored is not None else None

    def get_in_app(self, key: Tuple[str, str, str, str]) -> Optional[Dict[str, Any]]:
        stored = self._in_app.get(key)
        return _copy_json(stored) if stored is not None else None

    def record_conflict(
        self,
        key: Tuple[str, str, str, str],
        existing_status: str,
        incoming_status: str,
    ) -> None:
        self._conflicts.append(
            {
                "identity_key": list(key),
                "existing_terminal_status": existing_status,
                "incoming_terminal_status": incoming_status,
            }
        )

    def save_fact(
        self,
        fact: Mapping[str, Any],
        *,
        capability_state: str,
        channel_evidence: str,
    ) -> Tuple[Dict[str, Any], bool]:
        identity = dict(_require_mapping(fact.get("identity"), "fact.identity"))
        project_ref = _require_string(identity.get("project_ref"), "identity.project_ref")
        admission_id = _require_string(identity.get("admission_id"), "identity.admission_id")
        run_id = _require_string(identity.get("run_id"), "identity.run_id")
        terminal_revision = _require_string(fact.get("terminal_revision"), "terminal_revision")
        key = _identity_key(project_ref, admission_id, run_id, terminal_revision)
        run_key = (project_ref, admission_id, run_id)

        frozen = self._frozen_terminal_by_run.get(run_key)
        if frozen is not None and frozen["terminal_revision"] != terminal_revision:
            self._conflicts.append(
                {
                    "identity_key": list(run_key),
                    "reason": "terminal_revision_conflict",
                    "existing_terminal_revision": frozen["terminal_revision"],
                    "incoming_terminal_revision": terminal_revision,
                    "existing_terminal_status": frozen["terminal_status"],
                    "incoming_terminal_status": str(fact.get("terminal_status")),
                }
            )
            raise NotificationError("terminal_revision_conflict")

        existing = self._facts.get(key)
        if existing is not None:
            if existing.get("terminal_status") != fact.get("terminal_status"):
                self.record_conflict(
                    key,
                    str(existing.get("terminal_status")),
                    str(fact.get("terminal_status")),
                )
                raise NotificationError("terminal_status_conflict")
            self._save_count += 1
            return _copy_json(existing), False

        stored = _copy_json(dict(fact))
        self._facts[key] = stored
        self._frozen_terminal_by_run[run_key] = {
            "terminal_revision": terminal_revision,
            "terminal_status": str(stored.get("terminal_status")),
        }
        self._in_app[key] = {
            "identity": dict(identity),
            "terminal_revision": terminal_revision,
            "notification_status": stored.get("notification_status"),
            "user_copy": dict(stored.get("in_app_copy", {})),
            "read_state": "unread",
            "persistent": True,
        }
        self._outbox[key] = {
            "identity": dict(identity),
            "terminal_revision": terminal_revision,
            "capability_state": capability_state,
            "channel_evidence": channel_evidence,
            "queued": False,
            "attempts": 0,
        }
        self._save_count += 1
        return _copy_json(stored), True


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise NotificationError("%s_must_be_object" % field)
    return value


class SyntheticNotificationAdapter:
    """合成系统通知能力 adapter；通道证据不反向改写运行终态。"""

    def __init__(
        self,
        capability_by_admission: Optional[Mapping[str, str]] = None,
        default_capability: str = "unknown",
        channel_evidence_by_capability: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._capabilities = dict(capability_by_admission or {})
        if default_capability not in CAPABILITY_STATES:
            raise NotificationError("default_capability_invalid")
        self._default_capability = default_capability
        self._channel_map = dict(channel_evidence_by_capability or {})
        self._system_attempts: List[Dict[str, Any]] = []
        self._navigation_side_effects: List[Dict[str, Any]] = []

    @property
    def system_attempts(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(_copy_json(item) for item in self._system_attempts)

    @property
    def navigation_side_effects(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(_copy_json(item) for item in self._navigation_side_effects)

    def query_capability(self, admission_id: str) -> str:
        state = self._capabilities.get(admission_id, self._default_capability)
        if state not in CAPABILITY_STATES:
            raise NotificationError("capability_state_invalid")
        return state

    def attempt_system_notification(
        self,
        fact: Mapping[str, Any],
        capability_state: str,
    ) -> str:
        if capability_state not in CAPABILITY_STATES:
            raise NotificationError("capability_state_invalid")
        identity = dict(_require_mapping(fact.get("identity"), "fact.identity"))
        attempt = {
            "admission_id": identity.get("admission_id"),
            "run_id": identity.get("run_id"),
            "capability_state": capability_state,
        }
        self._system_attempts.append(attempt)
        if capability_state != "authorized":
            return "unknown"
        mapped = self._channel_map.get(capability_state, "queued")
        if mapped not in CHANNEL_EVIDENCE_STATES:
            return "queued"
        return mapped

    def record_navigation_click(self, intent: Mapping[str, Any]) -> None:
        self._navigation_side_effects.append(
            {
                "kind": "navigation_click",
                "intent": dict(intent),
            }
        )




def _apply_channel_evidence(
    fact: Dict[str, Any],
    store: NotificationStore,
    key: Tuple[str, str, str, str],
    capability_state: str,
    channel_evidence: str,
    attempted: bool,
) -> Dict[str, Any]:
    fact["channel_evidence"] = channel_evidence
    fact["capability_state"] = capability_state
    fact["fact_digest"] = digest_ref({k: v for k, v in fact.items() if k != "fact_digest"})
    stored = store._facts.get(key)
    if stored is not None:
        stored["channel_evidence"] = channel_evidence
        stored["capability_state"] = capability_state
        stored["fact_digest"] = fact["fact_digest"]
    outbox = store._outbox.get(key)
    if outbox is not None:
        outbox["channel_evidence"] = channel_evidence
        outbox["capability_state"] = capability_state
        outbox["queued"] = channel_evidence == "queued"
        if attempted:
            outbox["attempts"] = int(outbox.get("attempts", 0)) + 1
    return _copy_json(fact)

def process_terminal_event(
    event: TerminalEvent,
    binding: AdmissionBinding,
    accessibility: TargetAccessibility,
    store: NotificationStore,
    adapter: SyntheticNotificationAdapter,
) -> ProcessResult:
    """消费终态事件；失败关闭时不生成可能误导的通知事实。"""

    if binding.admission_status in BLOCKING_ADMISSION_STATUSES:
        return ProcessResult(status="fail_closed", reason="admission_blocked")
    if not binding.binding_valid:
        return ProcessResult(status="fail_closed", reason="binding_invalid")
    if binding.project_ref != event.project_ref or binding.admission_id != event.admission_id:
        return ProcessResult(status="fail_closed", reason="identity_mismatch")
    if binding.contract_version != CONTRACT_VERSION:
        return ProcessResult(status="fail_closed", reason="contract_version_incompatible")
    if not event.authoritative or not event.frozen:
        return ProcessResult(status="fail_closed", reason="terminal_not_authoritative_frozen")
    if accessibility.current_terminal_revision != event.terminal_revision:
        return ProcessResult(status="fail_closed", reason="terminal_revision_stale")
    if accessibility.binding_digest != binding.binding_digest:
        return ProcessResult(status="fail_closed", reason="target_binding_mismatch")
    if not accessibility.target_exists:
        return ProcessResult(status="fail_closed", reason="target_not_accessible")
    if is_non_terminal_status(event.terminal_status):
        return ProcessResult(status="fail_closed", reason="non_terminal_status")
    notification_status = project_notification_status(event.terminal_status, accessibility)
    if notification_status is None:
        return ProcessResult(status="fail_closed", reason="target_not_accessible")
    try:
        capability_state = adapter.query_capability(event.admission_id)
    except NotificationError:
        return ProcessResult(status="fail_closed", reason="capability_invalid")
    if capability_state not in CAPABILITY_STATES:
        return ProcessResult(status="fail_closed", reason="capability_invalid")

    fact_body = _build_fact_body(
        event,
        binding,
        accessibility,
        notification_status,
        capability_state,
        "unknown",
    )
    if not _system_payload_allowed(
        fact_body["system_copy"]["title"],
        fact_body["system_copy"]["body"],
    ):
        return ProcessResult(status="fail_closed", reason="system_copy_forbidden")

    try:
        fact, created = store.save_fact(
            fact_body,
            capability_state=capability_state,
            channel_evidence="unknown",
        )
    except NotificationError as exc:
        if str(exc) in {"terminal_status_conflict", "terminal_revision_conflict"}:
            return ProcessResult(status="fail_closed", reason=str(exc))
        raise

    attempted = False
    outbox = store.get_outbox(event.identity_key) or {}
    if capability_state == "authorized" and int(outbox.get("attempts", 0)) == 0:
        try:
            channel_evidence = adapter.attempt_system_notification(fact, capability_state)
        except Exception:  # synthetic channel failure stays outside run semantics
            channel_evidence = "unknown"
        attempted = True
    elif capability_state == "authorized":
        channel_evidence = str(outbox.get("channel_evidence", "unknown"))
    else:
        channel_evidence = "unknown"
    if channel_evidence not in CHANNEL_EVIDENCE_STATES:
        channel_evidence = "unknown"

    key = event.identity_key
    finalized = _apply_channel_evidence(
        fact,
        store,
        key,
        capability_state,
        channel_evidence,
        attempted,
    )

    return ProcessResult(status="ok", fact=finalized, created=created)


def build_navigation_intent(
    fact: Mapping[str, Any],
    binding: AdmissionBinding,
    accessibility: TargetAccessibility,
    store: NotificationStore,
    adapter: SyntheticNotificationAdapter,
    *,
    click_count: int = 1,
) -> NavigationIntentResult:
    """只返回已有运行目标的导航意图；重复点击无副作用。"""

    if click_count < 1:
        raise NotificationError("click_count_invalid")

    identity = dict(_require_mapping(fact.get("identity"), "fact.identity"))
    project_ref = _require_string(identity.get("project_ref"), "identity.project_ref")
    admission_id = _require_string(identity.get("admission_id"), "identity.admission_id")
    run_id = _require_string(identity.get("run_id"), "identity.run_id")
    terminal_revision = _require_string(fact.get("terminal_revision"), "terminal_revision")

    def blocked() -> NavigationIntentResult:
        return NavigationIntentResult(
            status="blocked",
            intent=None,
            user_message=NAVIGATION_BLOCKED_MESSAGE,
            click_count=click_count,
        )

    if binding.admission_status in BLOCKING_ADMISSION_STATUSES or not binding.binding_valid:
        return blocked()
    if binding.project_ref != project_ref or binding.admission_id != admission_id:
        return blocked()
    if binding.contract_version != CONTRACT_VERSION:
        return blocked()
    if fact.get("binding_digest") != binding.binding_digest:
        return blocked()
    if fact.get("contract_ref_version") != binding.contract_version:
        return blocked()
    if fact.get("app_version") != binding.app_version:
        return blocked()
    if accessibility.current_terminal_revision != terminal_revision:
        return blocked()
    if accessibility.binding_digest != binding.binding_digest:
        return blocked()
    if not accessibility.target_exists:
        return blocked()
    if fact.get("source_manifest_digest") != accessibility.source_manifest_digest:
        return blocked()
    if fact.get("output_manifest_digest") != accessibility.output_manifest_digest:
        return blocked()
    if project_notification_status(str(fact.get("terminal_status")), accessibility) != fact.get(
        "notification_status"
    ):
        return blocked()

    key = _identity_key(project_ref, admission_id, run_id, terminal_revision)
    stored = store.get_fact(key)
    if stored is None:
        return blocked()
    if stored.get("terminal_revision") != terminal_revision:
        return blocked()
    if stored.get("fact_digest") != fact.get("fact_digest"):
        return blocked()

    target = dict(_require_mapping(fact.get("navigation_target"), "navigation_target"))
    if target.get("project_ref") != project_ref:
        return blocked()
    if target.get("admission_id") != admission_id:
        return blocked()
    if target.get("run_id") != run_id:
        return blocked()
    if target.get("terminal_revision") != terminal_revision:
        return blocked()
    if target.get("binding_digest") != accessibility.binding_digest:
        return blocked()
    if target.get("source_manifest_digest") != accessibility.source_manifest_digest:
        return blocked()
    if target.get("output_manifest_digest") != accessibility.output_manifest_digest:
        return blocked()
    if target.get("action") != "navigate_only":
        return blocked()

    intent = {
        "project_ref": project_ref,
        "admission_id": admission_id,
        "run_id": run_id,
        "terminal_revision": terminal_revision,
        "target_kind": target.get("target_kind"),
        "action": "navigate_only",
    }

    for _ in range(click_count):
        adapter.record_navigation_click(intent)

    return NavigationIntentResult(
        status="ok",
        intent=intent,
        user_message=None,
        click_count=click_count,
    )


def validate_notification_fact(value: Mapping[str, Any]) -> Dict[str, Any]:
    """严格校验通知事实结构与摘要。"""

    raw = dict(_require_mapping(value, "fact"))
    required = {
        "schema",
        "version",
        "contract_version",
        "identity",
        "terminal_status",
        "notification_status",
        "terminal_revision",
        "terminal_authoritative",
        "terminal_frozen",
        "user_copy",
        "system_copy",
        "in_app_copy",
        "binding_digest",
        "source_manifest_digest",
        "output_manifest_digest",
        "contract_ref_version",
        "app_version",
        "capability_state",
        "channel_evidence",
        "navigation_target",
        "fact_digest",
    }
    if set(raw) != required:
        raise NotificationError("fact_fields_mismatch")
    if raw["schema"] != NOTIFICATION_SCHEMA:
        raise NotificationError("schema_mismatch")
    if raw["version"] != NOTIFICATION_VERSION:
        raise NotificationError("version_mismatch")
    if raw["contract_version"] != CONTRACT_VERSION:
        raise NotificationError("contract_version_mismatch")
    if raw["notification_status"] not in NOTIFICATION_STATUSES:
        raise NotificationError("notification_status_invalid")
    if raw["terminal_authoritative"] is not True or raw["terminal_frozen"] is not True:
        raise NotificationError("terminal_not_authoritative_frozen")
    projected = "analysis_complete" if raw["terminal_status"] == "complete" else raw["terminal_status"]
    if projected != raw["notification_status"]:
        raise NotificationError("terminal_projection_mismatch")
    if raw["capability_state"] not in CAPABILITY_STATES:
        raise NotificationError("capability_state_invalid")
    if raw["channel_evidence"] not in CHANNEL_EVIDENCE_STATES:
        raise NotificationError("channel_evidence_invalid")
    for field in (
        "terminal_status",
        "terminal_revision",
        "binding_digest",
        "source_manifest_digest",
        "output_manifest_digest",
        "contract_ref_version",
        "app_version",
    ):
        _require_string(raw.get(field), field)

    fact_digest = raw["fact_digest"]
    if not isinstance(fact_digest, str) or not fact_digest.startswith("sha256:"):
        raise NotificationError("fact_digest_invalid")
    body = {k: v for k, v in raw.items() if k != "fact_digest"}
    if digest_ref(body) != fact_digest:
        raise NotificationError("fact_digest_mismatch")

    system_copy = dict(_require_mapping(raw["system_copy"], "system_copy"))
    if not _system_payload_allowed(
        _require_string(system_copy.get("title"), "system_copy.title"),
        _require_string(system_copy.get("body"), "system_copy.body"),
    ):
        raise NotificationError("system_copy_forbidden")

    identity = dict(_require_mapping(raw["identity"], "identity"))
    target = dict(_require_mapping(raw["navigation_target"], "navigation_target"))
    for field in ("project_ref", "admission_id", "run_id"):
        if _require_string(identity.get(field), "identity.%s" % field) != target.get(field):
            raise NotificationError("navigation_identity_mismatch")
    if target.get("terminal_revision") != raw["terminal_revision"]:
        raise NotificationError("navigation_revision_mismatch")
    if target.get("binding_digest") != raw["binding_digest"]:
        raise NotificationError("navigation_binding_mismatch")
    if target.get("source_manifest_digest") != raw["source_manifest_digest"]:
        raise NotificationError("navigation_source_manifest_mismatch")
    if target.get("output_manifest_digest") != raw["output_manifest_digest"]:
        raise NotificationError("navigation_output_manifest_mismatch")
    if target.get("target_kind") != TARGET_KIND_BY_STATUS[raw["notification_status"]]:
        raise NotificationError("navigation_target_kind_mismatch")
    if target.get("action") != "navigate_only":
        raise NotificationError("navigation_action_invalid")
    if raw["user_copy"] != USER_COPY[raw["notification_status"]]:
        raise NotificationError("user_copy_mismatch")

    return _copy_json(raw)
