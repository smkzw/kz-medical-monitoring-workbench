#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R8 G6 synthetic audience seams.

This module is the deterministic, in-memory boundary for the G6 audience packet.
It provides one cross-domain fixture, a synthetic profile binding, a mock/recorded
adapter, the complete notification matrix, and the required task specification
plus explicit post-action recorder.  It never starts a service, opens a browser, calls a model, uses
network I/O, or reads a project directory.

The returned dictionaries are deliberately JSON-shaped so an actual local app can
project them into its own API envelope without copying a real-project fixture.
Technical digests remain in the evidence payload; audience copy is kept in the
Chinese fields explicitly marked as user-visible.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import synthetic_notification as _notification
except ImportError:  # pragma: no cover - package-style import for embedding
    from . import synthetic_notification as _notification  # type: ignore

try:
    from canonical_evidence import canonical_json, digest_ref
except ImportError:  # pragma: no cover - package-style import for embedding
    from .canonical_evidence import canonical_json, digest_ref  # type: ignore


FIXTURE_SCHEMA = "mm-monitoring-r8-g6-cross-domain-synthetic-fixture-v1"
FIXTURE_VERSION = "1"
BINDING_SCHEMA = "mm-monitoring-r8-g6-synthetic-profile-binding-v1"
BINDING_VERSION = "1"
ADAPTER_SCHEMA = "mm-monitoring-r8-g6-mock-recorded-adapter-v1"
ADAPTER_VERSION = "1"
NOTIFICATION_MATRIX_SCHEMA = "mm-monitoring-r8-g6-notification-matrix-v1"
NOTIFICATION_MATRIX_VERSION = "1"
USER_TASK_EVIDENCE_SCHEMA = "mm-monitoring-r8-g6-application-task-evidence-v1"
USER_TASK_EVIDENCE_VERSION = "1"
TASK_SPEC_SCHEMA = "mm-monitoring-r8-g6-required-task-specification-v1"
TASK_SPEC_VERSION = "1"
BUNDLE_SCHEMA = "mm-monitoring-r8-g6-synthetic-audience-bundle-v1"
BUNDLE_VERSION = "1"

CONTRACT_VERSION = "0.2"
CONTRACT_REF = (
    "medical_monitoring_r8_gate6_synthetic_ego_audience_acceptance_contract_v0_1_20260831"
)
APP_VERSION = "medical-monitoring-local-g6-synthetic-1"
SYNTHETIC_PROFILE_ID = "synthetic-profile-cross-domain-g6-v1"
SYNTHETIC_PROVIDER = "synthetic-recorded-provider"
SYNTHETIC_MODEL = "synthetic-recorded-model"
RECORDED_ADAPTER_ID = "g6-mock-recorded-adapter"
RECORDED_ADAPTER_KIND = "mock_recorded"

ANALYSIS_MODES: Tuple[str, ...] = (
    "full",
    "periodic_increment",
    "lock_revision_increment",
)
TERMINAL_STATUSES: Tuple[str, ...] = (
    "complete",
    "failed",
    "partial",
    "final_partial",
    "truncated",
    "timed_out",
    "cancelled",
    "interrupted",
    "blocked",
)
CAPABILITY_STATES: Tuple[str, ...] = (
    "authorized",
    "denied",
    "unavailable",
    "unknown",
)
DOMAINS: Tuple[str, ...] = (
    "AE",
    "MH",
    "CM",
    "IP",
    "LAB",
    "PD",
    "EFFICACY",
    "VISIT",
)
RISK_STATES: Tuple[str, ...] = (
    "high",
    "medium",
    "low",
    "none",
    "missing_data",
    "conflict",
    "partial_failure",
    "complete_failure",
)
FORBIDDEN_EVIDENCE_VALUES: Tuple[str, ...] = (
    "N/A",
    "not_applicable",
    "out_of_scope",
    "irrelevant",
    "partial",
    "not_evaluable",
    "conflict",
    "parse_failed",
    "blocked",
)

_MATRIX_STATUSES = frozenset(TERMINAL_STATUSES)
_MATRIX_CAPABILITIES = frozenset(CAPABILITY_STATES)
_SHA256_REF_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SYNTHETIC_RE = re.compile(r"^synthetic(?:[-_.]|$)")


class SyntheticEgoError(ValueError):
    """Synthetic G6 input, binding, matrix, or task evidence is invalid."""


FixtureError = SyntheticEgoError
BindingError = SyntheticEgoError
AdapterError = SyntheticEgoError
NotificationMatrixError = SyntheticEgoError
UserTaskEvidenceError = SyntheticEgoError


@dataclass(frozen=True)
class ReplayResult:
    """Independent replay outcome shared by all G6 evidence seams."""

    valid: bool
    status: str
    errors: Tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.valid

    def as_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "status": self.status,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class SyntheticBinding:
    """Immutable view of one synthetic profile binding."""

    payload: Mapping[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return _copy_json(self.payload)

    @property
    def binding_digest(self) -> str:
        return str(self.payload["binding_digest"])

    @property
    def project_ref(self) -> str:
        return str(self.payload["project_ref"])

    @property
    def run_ref(self) -> str:
        return str(self.payload["run_ref"])


@dataclass(frozen=True)
class SyntheticRecordedCall:
    """One call ledger entry retained by the mock adapter."""

    kind: str
    identity: Mapping[str, Any]
    binding_digest: str
    outcome: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "identity": _copy_json(self.identity),
            "binding_digest": self.binding_digest,
            "outcome": self.outcome,
        }


# Existing G4 code uses dictionaries as its public contract.  Keep the G6 task
# keys identical so the in-app evidence seam and the offline §15.4 replay remain
# joinable without a translation table.
def _copy_json(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise SyntheticEgoError("value_not_json_serializable") from exc


TASK_SPECS: Tuple[Dict[str, Any], ...]
TASK_KEYS: Tuple[str, ...]


_TASK_SPECS: Tuple[Dict[str, Any], ...] = (
    {
        "index": 1,
        "key": "export_import",
        "title": "导出后导入",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "present",
            },
            "files": {
                "source": "present",
                "export_copy": "absent",
                "import_copy": "absent",
                "identity_record": "present",
                "lineage_record": "present",
            },
        },
        "actions": (
            {
                "action": "选择导出摘要",
                "visible_result": "已显示可导出的合成对象和版本。",
                "restart_required": False,
            },
            {
                "action": "确认导入预览",
                "visible_result": "导入预览已显示，所属对象和版本保持一致。",
                "restart_required": False,
            },
        ),
        "expected_user_result": "导入预览已显示，所属对象和版本保持一致。",
        "restart_points": (),
        "negative_assertions": (
            "no_new_project_identity",
            "no_version_substitution",
        ),
        "cleanup": "remove_synthetic_import_copy",
    },
    {
        "index": 2,
        "key": "manifest_identity_lineage",
        "title": "查看备份归属",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "backup": "present",
                "manifest": "present",
                "identity_record": "present",
                "lineage_record": "present",
            },
        },
        "actions": (
            {
                "action": "打开备份摘要",
                "visible_result": "备份完整性、所属对象、版本来源已核对。",
                "restart_required": False,
            },
        ),
        "expected_user_result": "备份完整性、所属对象、版本来源已核对。",
        "restart_points": (),
        "negative_assertions": (
            "no_raw_path_in_user_copy",
            "no_identity_guess",
        ),
        "cleanup": "retain_fixture_only",
    },
    {
        "index": 3,
        "key": "backup_corruption",
        "title": "导入损坏备份",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "project": "present",
                "valid_backup": "present",
                "corrupt_backup": "present",
                "identity_record": "present",
            },
        },
        "actions": (
            {
                "action": "选择损坏备份",
                "visible_result": "备份校验未通过，导入操作已停止。",
                "restart_required": False,
            },
        ),
        "expected_user_result": "备份校验未通过，导入操作已停止。",
        "restart_points": (),
        "negative_assertions": (
            "no_half_import",
            "no_current_project_mutation",
        ),
        "cleanup": "discard_corrupt_fixture_copy",
    },
    {
        "index": 4,
        "key": "clean_restore",
        "title": "干净恢复",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "backup": "present",
                "restore_target": "absent",
                "project": "present",
                "identity_record": "present",
            },
        },
        "actions": (
            {
                "action": "查看恢复预览",
                "visible_result": "恢复前可预览，恢复对象和版本已明确。",
                "restart_required": False,
            },
            {
                "action": "确认恢复并重新打开",
                "visible_result": "恢复后项目可打开，摘要保持一致。",
                "restart_required": True,
            },
        ),
        "expected_user_result": "恢复后项目可打开，摘要保持一致。",
        "restart_points": ("after_restore",),
        "negative_assertions": (
            "no_cross_project_restore",
            "no_unverified_summary",
        ),
        "cleanup": "remove_restored_fixture_copy",
    },
    {
        "index": 5,
        "key": "pre_upgrade_protection",
        "title": "升级前保护",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "project": "present",
                "protection_point": "absent",
                "identity_record": "present",
                "lineage_record": "present",
            },
        },
        "actions": (
            {
                "action": "开始升级前检查",
                "visible_result": "升级前保护点已生成，原项目保持不变。",
                "restart_required": False,
            },
        ),
        "expected_user_result": "升级前保护点已生成，原项目保持不变。",
        "restart_points": (),
        "negative_assertions": (
            "no_precheck_data_mutation",
            "no_unbound_protection_point",
        ),
        "cleanup": "remove_protection_point",
    },
    {
        "index": 6,
        "key": "migration_success",
        "title": "迁移成功",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "old_version": "present",
                "new_version": "absent",
                "migration_marker": "absent",
                "identity_record": "present",
            },
        },
        "actions": (
            {
                "action": "确认迁移结果",
                "visible_result": "迁移完成，重启后仍可打开。",
                "restart_required": True,
            },
        ),
        "expected_user_result": "迁移完成，重启后仍可打开。",
        "restart_points": ("after_migration",),
        "negative_assertions": (
            "no_mixed_live_version",
            "no_identity_replacement",
        ),
        "cleanup": "restore_synthetic_version_state",
    },
    {
        "index": 7,
        "key": "critical_boundary_failure",
        "title": "关键边界失败",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "old_version": "present",
                "staging_version": "present",
                "switch_marker": "absent",
                "identity_record": "present",
            },
        },
        "actions": (
            {
                "action": "查看边界结果",
                "visible_result": "关键边界未通过，未切换半成品。",
                "restart_required": False,
            },
        ),
        "expected_user_result": "关键边界未通过，未切换半成品。",
        "restart_points": (),
        "negative_assertions": (
            "no_half_migration",
            "no_partial_switch",
        ),
        "cleanup": "clear_failure_fixture_state",
    },
    {
        "index": 8,
        "key": "original_version_usable",
        "title": "验证原版本",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "old_version": "present",
                "failed_new_version": "present",
                "project": "present",
                "identity_record": "present",
            },
        },
        "actions": (
            {
                "action": "重新打开原版本",
                "visible_result": "失败后原版本仍可打开和使用。",
                "restart_required": True,
            },
        ),
        "expected_user_result": "失败后原版本仍可打开和使用。",
        "restart_points": ("after_failure",),
        "negative_assertions": (
            "no_unreadable_original",
            "no_new_project_identity",
        ),
        "cleanup": "restore_synthetic_baseline",
    },
    {
        "index": 9,
        "key": "actual_rollback",
        "title": "实际回滚",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "new_version": "present",
                "old_version": "present",
                "rollback_marker": "absent",
                "identity_record": "present",
            },
        },
        "actions": (
            {
                "action": "确认回滚并重新打开",
                "visible_result": "回滚完成，重启后旧版本可用。",
                "restart_required": True,
            },
        ),
        "expected_user_result": "回滚完成，重启后旧版本可用。",
        "restart_points": ("after_rollback",),
        "negative_assertions": (
            "no_cross_version_result",
            "no_late_new_version_write",
        ),
        "cleanup": "restore_synthetic_baseline",
    },
    {
        "index": 10,
        "key": "credentials_not_exported_plaintext",
        "title": "普通导出",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "project": "present",
                "ordinary_export": "absent",
                "credential_values": 0,
                "credential_field_names": 0,
                "environment_members": 0,
            },
        },
        "actions": (
            {
                "action": "查看导出摘要",
                "visible_result": "导出摘要不显示凭据内容，包内容可核对。",
                "restart_required": False,
            },
            {
                "action": "完成包体检查",
                "visible_result": "包内可解码内容未发现敏感字段或凭据值。",
                "restart_required": False,
            },
        ),
        "expected_user_result": "包内可解码内容未发现敏感字段或凭据值。",
        "restart_points": (),
        "negative_assertions": (
            "no_credential_value_in_summary",
            "no_credential_field_name_in_package",
            "no_environment_member_in_package",
        ),
        "cleanup": "remove_ordinary_export",
    },
    {
        "index": 11,
        "key": "default_uninstall_retains_data",
        "title": "默认卸载",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
            },
            "files": {
                "application": "present",
                "project_data": "present",
                "retention_plan": "implicit",
                "identity_record": "present",
            },
        },
        "actions": (
            {
                "action": "查看卸载预览",
                "visible_result": "默认卸载将保留数据，重新打开后仍可识别。",
                "restart_required": True,
            },
        ),
        "expected_user_result": "默认卸载将保留数据，重新打开后仍可识别。",
        "restart_points": ("after_reinstall",),
        "negative_assertions": (
            "no_implicit_data_clear",
            "no_identity_guess_after_reopen",
        ),
        "cleanup": "remove_retained_fixture_data",
    },
    {
        "index": 12,
        "key": "explicit_clear_preview_confirm_cancel",
        "title": "同时清除数据",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "absent",
                "clear_confirmation": "not_confirmed",
            },
            "files": {
                "project_data": "present",
                "clear_preview": "absent",
                "clear_record": "absent",
                "identity_record": "present",
            },
        },
        "actions": (
            {
                "action": "查看清除预览并取消",
                "visible_result": "取消后数据保持不变。",
                "restart_required": False,
            },
            {
                "action": "再次预览并明确确认",
                "visible_result": "确认后按预览清除，结果可核对。",
                "restart_required": False,
            },
        ),
        "expected_user_result": "确认后按预览清除，结果可核对。",
        "restart_points": (),
        "negative_assertions": (
            "cancel_preserves_data",
            "no_clear_without_confirmation",
        ),
        "cleanup": "remove_clear_fixture_root",
    },
    {
        "index": 13,
        "key": "mixed_version_late_callback_fence",
        "title": "混合版本与迟到回调",
        "initial_state": {
            "application": {
                "entry": "ready",
                "selected_project": "synthetic-project-alpha",
                "active_run": "present",
                "current_revision": "present",
                "late_callback": "pending",
            },
            "files": {
                "current_version": "present",
                "late_callback_record": "present",
                "output_record": "present",
                "identity_record": "present",
            },
        },
        "actions": (
            {
                "action": "查看迟到回调结果",
                "visible_result": "旧回调已阻止，当前版本结果未被覆盖。",
                "restart_required": False,
            },
        ),
        "expected_user_result": "旧回调已阻止，当前版本结果未被覆盖。",
        "restart_points": (),
        "negative_assertions": (
            "no_stale_revision_overwrite",
            "no_mixed_version_publish",
        ),
        "cleanup": "clear_late_callback_fixture",
    },
)

TASK_SPECS = tuple(_copy_json(item) for item in _TASK_SPECS)
TASK_KEYS = tuple(str(item["key"]) for item in _TASK_SPECS)
TASK_SPEC_DIGEST = digest_ref(
    {
        "schema": TASK_SPEC_SCHEMA,
        "version": TASK_SPEC_VERSION,
        "tasks": list(TASK_SPECS),
    }
)





# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------



def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SyntheticEgoError("%s_must_be_object" % field)
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SyntheticEgoError("%s_must_be_non_empty_string" % field)
    return value.strip()


def _require_id(value: Any, field: str) -> str:
    result = _require_text(value, field)
    if not _SAFE_ID_RE.fullmatch(result):
        raise SyntheticEgoError("%s_must_be_safe_synthetic_id" % field)
    return result


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise SyntheticEgoError("%s_must_be_boolean" % field)
    return value


def _require_sha256_ref(value: Any, field: str) -> str:
    result = _require_text(value, field)
    if not _SHA256_REF_RE.fullmatch(result):
        raise SyntheticEgoError("%s_must_be_sha256_ref" % field)
    return result


def _require_enum(value: Any, field: str, allowed: Iterable[str]) -> str:
    result = _require_text(value, field)
    if result not in set(allowed):
        raise SyntheticEgoError("%s_invalid" % field)
    return result


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield from _walk_strings(key)
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


def _assert_no_path_or_external_literal(value: Any, field: str) -> None:
    for text in _walk_strings(value):
        lowered = text.lower()
        if "/" in text or "\\" in text:
            raise SyntheticEgoError("%s_contains_path_literal" % field)
        if ".env" in lowered or "sqlite" in lowered:
            raise SyntheticEgoError("%s_contains_environment_or_database_literal" % field)
        if any(token in lowered for token in ("8911", "5174", "8984", "pid=")):
            raise SyntheticEgoError("%s_contains_runtime_literal" % field)


def _assert_no_forbidden_task_value(value: Any, field: str) -> None:
    for text in _walk_strings(value):
        if text in FORBIDDEN_EVIDENCE_VALUES:
            raise SyntheticEgoError("%s_contains_forbidden_result_value" % field)


def _digest_without(value: Mapping[str, Any], *fields: str) -> str:
    excluded = set(fields)
    return digest_ref({key: _copy_json(item) for key, item in value.items() if key not in excluded})


def _expected_keys(raw: Mapping[str, Any], required: Iterable[str], field: str) -> None:
    required_set = set(required)
    actual = set(raw)
    missing = sorted(required_set - actual)
    unknown = sorted(actual - required_set)
    if missing:
        raise SyntheticEgoError("%s_missing:%s" % (field, ",".join(missing)))
    if unknown:
        raise SyntheticEgoError("%s_unknown:%s" % (field, ",".join(unknown)))


def _find_project(fixture: Mapping[str, Any], project_ref: str) -> Mapping[str, Any]:
    for project in fixture["projects"]:
        if project["project_ref"] == project_ref:
            return project
    raise SyntheticEgoError("unknown_project_ref:%s" % project_ref)


def _find_run(
    fixture: Mapping[str, Any], project_ref: str, analysis_mode: str
) -> Mapping[str, Any]:
    for run in fixture["analysis_inputs"]:
        if run["project_ref"] == project_ref and run["analysis_mode"] == analysis_mode:
            return run
    raise SyntheticEgoError("unknown_analysis_mode:%s" % analysis_mode)


# ---------------------------------------------------------------------------
# Cross-domain synthetic fixture
# ---------------------------------------------------------------------------


def _build_fixture_body() -> Dict[str, Any]:
    center_specs = (
        ("synthetic-center-01", "合成中心一"),
        ("synthetic-center-02", "合成中心二"),
        ("synthetic-center-03", "合成中心三"),
    )
    project_specs = (
        ("synthetic-project-alpha", "合成项目甲"),
        ("synthetic-project-beta", "合成项目乙"),
    )
    domain_specs = (
        ("AE", "adverse_event", "不良事件"),
        ("MH", "medical_history", "既往情况"),
        ("CM", "concomitant_record", "合并用药记录"),
        ("IP", "administration_record", "给药记录"),
        ("LAB", "laboratory_observation", "检验检查"),
        ("PD", "pharmacodynamic_observation", "PD观察"),
        ("EFFICACY", "efficacy_observation", "疗效观察"),
        ("VISIT", "visit_event", "访视事件"),
    )
    risk_specs = (
        ("high", "高风险"),
        ("medium", "中风险"),
        ("low", "低风险"),
        ("none", "无风险"),
        ("missing_data", "缺资料"),
        ("conflict", "冲突"),
        ("partial_failure", "部分失败"),
        ("complete_failure", "完全失败"),
    )
    dates = ("2026-01-08", "2026-02-12", "2026-03-19", "2026-04-23")
    center_assignments = (
        (
            "synthetic-center-01",
            "synthetic-center-01",
            "synthetic-center-02",
            "synthetic-center-02",
            "synthetic-center-03",
            "synthetic-center-03",
        ),
        (
            "synthetic-center-01",
            "synthetic-center-02",
            "synthetic-center-02",
            "synthetic-center-03",
            "synthetic-center-03",
            "synthetic-center-03",
        ),
    )

    centers = [
        {
            "center_ref": center_ref,
            "display_name": display_name,
            "synthetic_only": True,
        }
        for center_ref, display_name in center_specs
    ]
    projects = [
        {
            "project_ref": project_ref,
            "admission_id": "synthetic-admission-%s" % project_ref.rsplit("-", 1)[-1],
            "display_name": display_name,
            "center_refs": [center[0] for center in center_specs],
            "synthetic_only": True,
        }
        for project_ref, display_name in project_specs
    ]

    subjects: List[Dict[str, Any]] = []
    visits: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    subjects_by_project: Dict[str, List[Dict[str, Any]]] = {
        project["project_ref"]: [] for project in projects
    }
    subject_counter = 0
    for project_index, project in enumerate(projects):
        for local_index in range(6):
            subject_counter += 1
            subject_ref = "synthetic-subject-%03d" % subject_counter
            center_ref = center_assignments[project_index][local_index]
            risk_state, risk_label = risk_specs[(subject_counter - 1) % len(risk_specs)]
            visit_refs: List[str] = []
            event_refs: List[str] = []
            for visit_index, occurred_on in enumerate(dates, start=1):
                visit_ref = "%s-visit-%02d" % (subject_ref, visit_index)
                visit_refs.append(visit_ref)
                visits.append(
                    {
                        "visit_ref": visit_ref,
                        "project_ref": project["project_ref"],
                        "center_ref": center_ref,
                        "subject_ref": subject_ref,
                        "visit_order": visit_index,
                        "visit_label": "访视%d" % visit_index,
                        "occurred_on": occurred_on,
                        "axis_position": visit_index,
                    }
                )
            subject = {
                "subject_ref": subject_ref,
                "project_ref": project["project_ref"],
                "center_ref": center_ref,
                "risk_state": risk_state,
                "risk_label_zh": risk_label,
                "visit_refs": visit_refs,
                "event_refs": event_refs,
                "synthetic_only": True,
            }
            subjects.append(subject)
            subjects_by_project[project["project_ref"]].append(subject)

            event_plan = [
                (
                    2 if subject_counter == 1 else (domain_index % len(dates)) + 1,
                    domain_index,
                    domain,
                    event_kind,
                    domain_label,
                )
                for domain_index, (domain, event_kind, domain_label) in enumerate(domain_specs)
            ]
            event_plan.sort(key=lambda item: (item[0], item[1]))
            for visit_index, domain_index, domain, event_kind, domain_label in event_plan:
                visit_ref = visit_refs[visit_index - 1]
                event_ref = "%s-event-%s" % (subject_ref, domain.lower())
                event_refs.append(event_ref)
                record_state = "available"
                if risk_state == "missing_data" and domain in {"LAB", "EFFICACY"}:
                    record_state = "missing"
                elif risk_state == "conflict" and domain in {"AE", "CM"}:
                    record_state = "conflict"
                elif risk_state == "partial_failure" and domain in {"PD", "EFFICACY"}:
                    record_state = "partial_failure"
                elif risk_state == "complete_failure":
                    record_state = "complete_failure"
                events.append(
                    {
                        "event_ref": event_ref,
                        "project_ref": project["project_ref"],
                        "center_ref": center_ref,
                        "subject_ref": subject_ref,
                        "domain": domain,
                        "event_kind": event_kind,
                        "domain_label_zh": domain_label,
                        "event_label_zh": (
                            "第%d名受试者的%s事件标记，用于核对访视时间、状态与关联来源"
                            % (subject_counter, domain_label)
                        ),
                        "detail_label_zh": (
                            "第%d名受试者在第%d次访视的%s合成观察记录，需核对时间、状态与关联来源"
                            % (subject_counter, visit_index, domain_label)
                        ),
                        "source_label_zh": (
                            "合成来源说明：第%d名受试者的%s记录，作为当前访视的可追溯阅读线索"
                            % (subject_counter, domain_label)
                        ),
                        "visit_ref": visit_ref,
                        "occurred_on": dates[visit_index - 1],
                        "record_state": record_state,
                        "risk_state": risk_state,
                        "source_ref": "synthetic-source-%03d-%s" % (subject_counter, domain.lower()),
                    }
                )

    mode_status = {
        "full": "complete",
        "periodic_increment": "partial",
        "lock_revision_increment": "final_partial",
    }
    mode_condition = {
        "full": "none",
        "periodic_increment": "partial_failure",
        "lock_revision_increment": "complete_failure",
    }
    analysis_inputs: List[Dict[str, Any]] = []
    for project in projects:
        project_events = [
            event for event in events if event["project_ref"] == project["project_ref"]
        ]
        for mode in ANALYSIS_MODES:
            if mode == "full":
                selected_events = project_events
            elif mode == "periodic_increment":
                selected_events = project_events[::2]
            else:
                selected_events = project_events[: len(project_events) // 2]
            analysis_inputs.append(
                {
                    "run_ref": "synthetic-run-%s-%s"
                    % (project["project_ref"].rsplit("-", 1)[-1], mode),
                    "project_ref": project["project_ref"],
                    "admission_id": project["admission_id"],
                    "analysis_mode": mode,
                    "input_ref": "synthetic-input-%s-%s"
                    % (project["project_ref"].rsplit("-", 1)[-1], mode),
                    "event_refs": [event["event_ref"] for event in selected_events],
                    "terminal_status": mode_status[mode],
                    "condition": mode_condition[mode],
                    "source_revision": "synthetic-source-revision-%s-%s"
                    % (project["project_ref"].rsplit("-", 1)[-1], mode),
                    "synthetic_only": True,
                }
            )

    flow_nodes = [
        {"node_ref": "consent", "label_zh": "知情同意", "order": 1},
        {"node_ref": "screening", "label_zh": "筛选", "order": 2},
        {"node_ref": "treatment", "label_zh": "治疗", "order": 3},
        {"node_ref": "study_status", "label_zh": "研究状态", "order": 4},
        {"node_ref": "recheck", "label_zh": "待重新核对", "order": 5},
    ]
    flow_rows: List[Dict[str, Any]] = []
    for project in projects:
        for center in centers:
            center_subjects = [
                subject
                for subject in subjects_by_project[project["project_ref"]]
                if subject["center_ref"] == center["center_ref"]
            ]
            subject_refs = [subject["subject_ref"] for subject in center_subjects]
            count = len(subject_refs)
            transitions = (
                ("consent", "screening", count, subject_refs),
                (
                    "screening",
                    "treatment",
                    max(count - 1, 0),
                    subject_refs[: max(count - 1, 0)],
                ),
                (
                    "screening",
                    "study_status",
                    1 if count else 0,
                    subject_refs[-1:] if count else [],
                ),
                (
                    "treatment",
                    "study_status",
                    max(count - 1, 0),
                    subject_refs[: max(count - 1, 0)],
                ),
                ("treatment", "recheck", 0, []),
            )
            for stage_from, stage_to, row_count, row_subjects in transitions:
                flow_rows.append(
                    {
                        "flow_ref": "synthetic-flow-%s-%s-%s-%s"
                        % (
                            project["project_ref"].rsplit("-", 1)[-1],
                            center["center_ref"].rsplit("-", 1)[-1],
                            stage_from,
                            stage_to,
                        ),
                        "project_ref": project["project_ref"],
                        "center_ref": center["center_ref"],
                        "stage_from": stage_from,
                        "stage_to": stage_to,
                        "count": row_count,
                        "subject_refs": row_subjects,
                        "metric": "reached",
                    }
                )
    flow_totals: List[Dict[str, Any]] = []
    for project in projects:
        for center in centers:
            scoped_subjects = [
                subject
                for subject in subjects_by_project[project["project_ref"]]
                if subject["center_ref"] == center["center_ref"]
            ]
            scoped_rows = [
                row
                for row in flow_rows
                if row["project_ref"] == project["project_ref"]
                and row["center_ref"] == center["center_ref"]
            ]
            transition_counts = {
                (row["stage_from"], row["stage_to"]): row["count"] for row in scoped_rows
            }
            subject_count = len(scoped_subjects)
            flow_totals.append(
                {
                    "project_ref": project["project_ref"],
                    "center_ref": center["center_ref"],
                    "subject_count": subject_count,
                    "consent_to_screening": transition_counts[("consent", "screening")],
                    "screening_to_treatment": transition_counts[("screening", "treatment")],
                    "screening_to_study_status": transition_counts[("screening", "study_status")],
                    "treatment_to_study_status": transition_counts[("treatment", "study_status")],
                    "treatment_to_recheck": transition_counts[("treatment", "recheck")],
                    "terminal_total": (
                        transition_counts[("screening", "study_status")]
                        + transition_counts[("treatment", "study_status")]
                    ),
                }
            )

    dense_subject = subjects[0]
    dense_visit = next(
        visit
        for visit in visits
        if visit["visit_ref"] == dense_subject["visit_refs"][1]
    )
    dense_events = [
        event
        for event in events
        if event["subject_ref"] == dense_subject["subject_ref"]
        and event["visit_ref"] == dense_visit["visit_ref"]
    ]
    domain_counts = {
        domain: sum(1 for event in events if event["domain"] == domain)
        for domain in DOMAINS
    }
    risk_state_counts = {
        risk_state: sum(1 for subject in subjects if subject["risk_state"] == risk_state)
        for risk_state in RISK_STATES
    }
    center_subject_counts = {
        project["project_ref"]: {
            center["center_ref"]: sum(
                1
                for subject in subjects_by_project[project["project_ref"]]
                if subject["center_ref"] == center["center_ref"]
            )
            for center in centers
        }
        for project in projects
    }
    challenge = {
        "dense_same_day": {
            "subject_ref": dense_subject["subject_ref"],
            "visit_ref": dense_visit["visit_ref"],
            "occurred_on": dense_visit["occurred_on"],
            "event_refs": [event["event_ref"] for event in dense_events],
            "domains": [event["domain"] for event in dense_events],
            "event_count": len(dense_events),
        },
        "long_label_fields": ["event_label_zh", "detail_label_zh", "source_label_zh"],
        "long_label_min_chars": min(
            len(event[field])
            for event in events
            for field in ("event_label_zh", "detail_label_zh", "source_label_zh")
        ),
        "flow_shape": {
            "has_split": any(
                row["stage_from"] == "screening"
                and row["stage_to"] in {"treatment", "study_status"}
                and row["count"] > 0
                for row in flow_rows
            ),
            "has_merge": any(
                row["stage_to"] == "study_status" and row["count"] > 0 for row in flow_rows
            ),
            "has_zero": any(row["count"] == 0 for row in flow_rows),
            "has_center_differences": (
                center_subject_counts["synthetic-project-alpha"]
                != center_subject_counts["synthetic-project-beta"]
            ),
        },
    }
    table_totals = {
        "projects": len(projects),
        "centers": len(centers),
        "subjects": len(subjects),
        "visits": len(visits),
        "events": len(events),
        "analysis_inputs": len(analysis_inputs),
        "risk_scenarios": len(risk_specs),
        "flow_rows": len(flow_rows),
        "flow_count_total": sum(row["count"] for row in flow_rows),
        "domain_counts": domain_counts,
        "risk_state_counts": risk_state_counts,
        "center_subject_counts": center_subject_counts,
    }

    risk_scenarios = [
        {
            "scenario_ref": "synthetic-risk-scenario-%02d" % (index + 1),
            "risk_state": risk_state,
            "label_zh": label,
            "subject_refs": [
                subject["subject_ref"]
                for subject in subjects
                if subject["risk_state"] == risk_state
            ],
        }
        for index, (risk_state, label) in enumerate(risk_specs)
    ]
    analysis_cases = [
        {
            "case_ref": "synthetic-analysis-case-partial-failure",
            "condition": "partial_failure",
            "terminal_status": "partial",
            "run_ref": analysis_inputs[1]["run_ref"],
        },
        {
            "case_ref": "synthetic-analysis-case-complete-failure",
            "condition": "complete_failure",
            "terminal_status": "failed",
            "run_ref": analysis_inputs[2]["run_ref"],
        },
    ]
    task_keys = list(TASK_KEYS)
    body: Dict[str, Any] = {
        "schema": FIXTURE_SCHEMA,
        "version": FIXTURE_VERSION,
        "contract_ref": CONTRACT_REF,
        "contract_version": CONTRACT_VERSION,
        "app_version": APP_VERSION,
        "synthetic_profile_id": SYNTHETIC_PROFILE_ID,
        "fixture_id": "synthetic-cross-domain-g6-v1",
        "synthetic_only": True,
        "offline": True,
        "projects": projects,
        "centers": centers,
        "subjects": subjects,
        "visits": visits,
        "events": events,
        "analysis_modes": list(ANALYSIS_MODES),
        "analysis_inputs": analysis_inputs,
        "risk_scenarios": risk_scenarios,
        "analysis_cases": analysis_cases,
        "journey": {
            "axis": "visit",
            "orientation": "horizontal",
            "visit_order": [1, 2, 3, 4],
            "marker_domains": list(DOMAINS),
            "event_count": len(events),
            "marker_counts": domain_counts,
        },
        "flow_nodes": flow_nodes,
        "flow_rows": flow_rows,
        "flow_totals": flow_totals,
        "challenge": challenge,
        "table_totals": table_totals,
        "section_15_4": {
            "synthetic_object_ref": "synthetic-section-15-4-object",
            "task_keys": task_keys,
            "task_count": len(task_keys),
            "evidence_mode": "required_task_specification",
            "task_spec_schema": TASK_SPEC_SCHEMA,
            "task_spec_version": TASK_SPEC_VERSION,
            "task_spec_digest": TASK_SPEC_DIGEST,
            "execution_required": True,
            "initial_state_included": True,
        },
    }
    body["counts"] = {
        "projects": len(projects),
        "centers": len(centers),
        "subjects": len(subjects),
        "visits": len(visits),
        "events": len(events),
        "analysis_inputs": len(analysis_inputs),
        "flow_rows": len(flow_rows),
        "risk_scenarios": len(risk_scenarios),
        "domain_counts": {
            domain: sum(1 for event in events if event["domain"] == domain)
            for domain in DOMAINS
        },
    }
    fixture_digest = _digest_without(body, "fixture_digest", "binding_digest", "profile_binding_digest")
    profile_binding_digest = digest_ref(
        {
            "contract_version": CONTRACT_VERSION,
            "app_version": APP_VERSION,
            "fixture_digest": fixture_digest,
            "synthetic_profile_id": SYNTHETIC_PROFILE_ID,
        }
    )
    body["fixture_digest"] = fixture_digest
    body["binding_digest"] = profile_binding_digest
    body["profile_binding_digest"] = profile_binding_digest
    return body


def build_synthetic_fixture() -> Dict[str, Any]:
    """Build the deterministic two-project, cross-domain fixture."""

    return validate_synthetic_fixture(_build_fixture_body())


def validate_synthetic_fixture(value: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate counts, references, domains, modes, and the fixture digest."""

    raw = dict(_require_mapping(value, "fixture"))
    _expected_keys(
        raw,
        (
            "schema",
            "version",
            "contract_ref",
            "contract_version",
            "app_version",
            "synthetic_profile_id",
            "fixture_id",
            "synthetic_only",
            "offline",
            "projects",
            "centers",
            "subjects",
            "visits",
            "events",
            "analysis_modes",
            "analysis_inputs",
            "risk_scenarios",
            "analysis_cases",
            "journey",
            "flow_nodes",
            "flow_rows",
            "flow_totals",
            "challenge",
            "table_totals",
            "section_15_4",
            "counts",
            "fixture_digest",
            "binding_digest",
            "profile_binding_digest",
        ),
        "fixture",
    )
    if raw["schema"] != FIXTURE_SCHEMA or raw["version"] != FIXTURE_VERSION:
        raise SyntheticEgoError("fixture_schema_mismatch")
    if raw["contract_ref"] != CONTRACT_REF or raw["contract_version"] != CONTRACT_VERSION:
        raise SyntheticEgoError("fixture_contract_mismatch")
    if raw["app_version"] != APP_VERSION:
        raise SyntheticEgoError("fixture_app_version_mismatch")
    if raw["synthetic_profile_id"] != SYNTHETIC_PROFILE_ID:
        raise SyntheticEgoError("fixture_profile_mismatch")
    _require_id(raw["fixture_id"], "fixture.fixture_id")
    _require_bool(raw["synthetic_only"], "fixture.synthetic_only")
    _require_bool(raw["offline"], "fixture.offline")
    if raw["synthetic_only"] is not True or raw["offline"] is not True:
        raise SyntheticEgoError("fixture_must_be_synthetic_offline")
    _require_sha256_ref(raw["fixture_digest"], "fixture.fixture_digest")
    _require_sha256_ref(raw["binding_digest"], "fixture.binding_digest")
    _require_sha256_ref(raw["profile_binding_digest"], "fixture.profile_binding_digest")
    if raw["binding_digest"] != raw["profile_binding_digest"]:
        raise SyntheticEgoError("fixture_binding_digest_mismatch")
    if not isinstance(raw["projects"], list) or len(raw["projects"]) != 2:
        raise SyntheticEgoError("fixture_project_count_mismatch")
    if not isinstance(raw["centers"], list) or len(raw["centers"]) != 3:
        raise SyntheticEgoError("fixture_center_count_mismatch")
    if not isinstance(raw["subjects"], list) or len(raw["subjects"]) != 12:
        raise SyntheticEgoError("fixture_subject_count_mismatch")
    for field in (
        "visits",
        "events",
        "analysis_modes",
        "analysis_inputs",
        "risk_scenarios",
        "analysis_cases",
        "flow_nodes",
        "flow_rows",
        "flow_totals",
    ):
        if not isinstance(raw[field], list):
            raise SyntheticEgoError("fixture_%s_must_be_list" % field)

    project_refs = [_require_id(row.get("project_ref"), "project.project_ref") for row in raw["projects"]]
    if len(set(project_refs)) != len(project_refs):
        raise SyntheticEgoError("fixture_duplicate_project_ref")
    if set(project_refs) != {"synthetic-project-alpha", "synthetic-project-beta"}:
        raise SyntheticEgoError("fixture_project_refs_mismatch")
    admission_ids = set()
    center_refs = set()
    for row in raw["projects"]:
        _expected_keys(row, ("project_ref", "admission_id", "display_name", "center_refs", "synthetic_only"), "project")
        _require_id(row["admission_id"], "project.admission_id")
        admission_ids.add(row["admission_id"])
        if not isinstance(row["center_refs"], list) or set(row["center_refs"]) != {
            "synthetic-center-01",
            "synthetic-center-02",
            "synthetic-center-03",
        }:
            raise SyntheticEgoError("project_center_refs_mismatch")
        if row["synthetic_only"] is not True:
            raise SyntheticEgoError("project_not_synthetic")
    for row in raw["centers"]:
        _expected_keys(row, ("center_ref", "display_name", "synthetic_only"), "center")
        center_refs.add(_require_id(row["center_ref"], "center.center_ref"))
        if row["synthetic_only"] is not True:
            raise SyntheticEgoError("center_not_synthetic")
    if center_refs != {"synthetic-center-01", "synthetic-center-02", "synthetic-center-03"}:
        raise SyntheticEgoError("fixture_center_refs_mismatch")
    project_by_ref = {row["project_ref"]: row for row in raw["projects"]}
    center_by_ref = {row["center_ref"]: row for row in raw["centers"]}
    if len(project_by_ref) != 2 or len(center_by_ref) != 3:
        raise SyntheticEgoError("fixture_identity_index_mismatch")

    subject_refs = set()
    subject_events: Dict[str, set[str]] = {}
    subject_event_order: Dict[str, List[str]] = {}
    subject_visits: Dict[str, set[str]] = {}
    subject_visit_order: Dict[str, List[str]] = {}
    subject_scope: Dict[str, Tuple[str, str]] = {}
    for row in raw["subjects"]:
        _expected_keys(
            row,
            (
                "subject_ref",
                "project_ref",
                "center_ref",
                "risk_state",
                "risk_label_zh",
                "visit_refs",
                "event_refs",
                "synthetic_only",
            ),
            "subject",
        )
        subject_ref = _require_id(row["subject_ref"], "subject.subject_ref")
        if subject_ref in subject_refs:
            raise SyntheticEgoError("fixture_duplicate_subject_ref")
        subject_refs.add(subject_ref)
        if row["project_ref"] not in project_refs or row["center_ref"] not in center_refs:
            raise SyntheticEgoError("subject_scope_reference_mismatch")
        _require_enum(row["risk_state"], "subject.risk_state", RISK_STATES)
        if row["synthetic_only"] is not True:
            raise SyntheticEgoError("subject_not_synthetic")
        if not isinstance(row["visit_refs"], list) or len(row["visit_refs"]) != 4:
            raise SyntheticEgoError("subject_visit_count_mismatch")
        if not isinstance(row["event_refs"], list) or len(row["event_refs"]) != len(DOMAINS):
            raise SyntheticEgoError("subject_event_count_mismatch")
        visit_ref_list = [_require_id(item, "subject.visit_ref") for item in row["visit_refs"]]
        event_ref_list = [_require_id(item, "subject.event_ref") for item in row["event_refs"]]
        if len(set(visit_ref_list)) != len(visit_ref_list):
            raise SyntheticEgoError("subject_duplicate_visit_ref")
        if len(set(event_ref_list)) != len(event_ref_list):
            raise SyntheticEgoError("subject_duplicate_event_ref")
        subject_events[subject_ref] = set(event_ref_list)
        subject_event_order[subject_ref] = event_ref_list
        subject_scope[subject_ref] = (row["project_ref"], row["center_ref"])
        subject_visits[subject_ref] = set(visit_ref_list)
        subject_visit_order[subject_ref] = visit_ref_list
    if len(subject_refs) != 12:
        raise SyntheticEgoError("fixture_subject_refs_mismatch")
    visit_by_ref: Dict[str, Mapping[str, Any]] = {}

    visit_refs = set()
    for row in raw["visits"]:
        _expected_keys(
            row,
            (
                "visit_ref",
                "project_ref",
                "center_ref",
                "subject_ref",
                "visit_order",
                "visit_label",
                "occurred_on",
                "axis_position",
            ),
            "visit",
        )
        visit_ref = _require_id(row["visit_ref"], "visit.visit_ref")
        if visit_ref in visit_refs:
            raise SyntheticEgoError("fixture_duplicate_visit_ref")
        visit_refs.add(visit_ref)
        if not isinstance(row["visit_order"], int) or isinstance(row["visit_order"], bool):
            raise SyntheticEgoError("visit_order_invalid")
        if row["visit_order"] not in {1, 2, 3, 4} or row["axis_position"] != row["visit_order"]:
            raise SyntheticEgoError("visit_axis_position_mismatch")
        _require_text(row["occurred_on"], "visit.occurred_on")
        visit_by_ref[visit_ref] = row
        if row["subject_ref"] not in subject_refs or row["project_ref"] not in project_by_ref:
            raise SyntheticEgoError("visit_scope_reference_mismatch")
        subject_project, subject_center = subject_scope[row["subject_ref"]]
        if row["project_ref"] != subject_project or row["center_ref"] != subject_center:
            raise SyntheticEgoError("visit_subject_scope_mismatch")
        if row["visit_ref"] not in subject_visits[row["subject_ref"]]:
            raise SyntheticEgoError("visit_not_bound_to_subject")
        if row["center_ref"] not in center_by_ref:
            raise SyntheticEgoError("visit_center_reference_mismatch")
    if len(visit_refs) != 48:
        raise SyntheticEgoError("fixture_visit_refs_mismatch")
    for subject_ref, expected_refs in subject_visit_order.items():
        ordered_visits = sorted(
            (visit_by_ref[visit_ref] for visit_ref in expected_refs),
            key=lambda visit: visit["visit_order"],
        )
        if [visit["visit_ref"] for visit in ordered_visits] != expected_refs:
            raise SyntheticEgoError("fixture_visit_order_mismatch")
        dates_for_subject = [visit["occurred_on"] for visit in ordered_visits]
        if dates_for_subject != sorted(dates_for_subject):
            raise SyntheticEgoError("fixture_visit_chronology_mismatch")

    event_refs = set()
    domain_counts = {domain: 0 for domain in DOMAINS}
    events_by_subject: Dict[str, List[Mapping[str, Any]]] = {
        subject_ref: [] for subject_ref in subject_refs
    }
    domain_rank = {domain: index for index, domain in enumerate(DOMAINS)}
    for row in raw["events"]:
        _expected_keys(
            row,
            (
                "event_ref",
                "project_ref",
                "center_ref",
                "subject_ref",
                "domain",
                "event_kind",
                "domain_label_zh",
                "event_label_zh",
                "detail_label_zh",
                "source_label_zh",
                "visit_ref",
                "occurred_on",
                "record_state",
                "risk_state",
                "source_ref",
            ),
            "event",
        )
        event_ref = _require_id(row["event_ref"], "event.event_ref")
        if event_ref in event_refs:
            raise SyntheticEgoError("fixture_duplicate_event_ref")
        event_refs.add(event_ref)
        domain = _require_enum(row["domain"], "event.domain", DOMAINS)
        domain_counts[domain] += 1
        if row["subject_ref"] not in subject_refs or row["project_ref"] not in project_by_ref:
            raise SyntheticEgoError("event_scope_reference_mismatch")
        subject_project, subject_center = subject_scope[row["subject_ref"]]
        if row["project_ref"] != subject_project or row["center_ref"] != subject_center:
            raise SyntheticEgoError("event_subject_scope_mismatch")
        if row["center_ref"] not in center_by_ref or row["visit_ref"] not in visit_refs:
            raise SyntheticEgoError("event_reference_mismatch")
        if row["visit_ref"] not in subject_visits[row["subject_ref"]]:
            raise SyntheticEgoError("event_visit_scope_mismatch")
        visit = visit_by_ref[row["visit_ref"]]
        if (
            visit["subject_ref"] != row["subject_ref"]
            or visit["project_ref"] != row["project_ref"]
            or visit["center_ref"] != row["center_ref"]
            or visit["occurred_on"] != row["occurred_on"]
        ):
            raise SyntheticEgoError("event_visit_identity_mismatch")
        if event_ref not in subject_events[row["subject_ref"]]:
            raise SyntheticEgoError("event_not_bound_to_subject")
        expected_risk_state = next(
            subject["risk_state"]
            for subject in raw["subjects"]
            if subject["subject_ref"] == row["subject_ref"]
        )
        if row["risk_state"] != expected_risk_state:
            raise SyntheticEgoError("event_risk_state_mismatch")
        _require_enum(
            row["record_state"],
            "event.record_state",
            ("available", "missing", "conflict", "partial_failure", "complete_failure"),
        )
        expected_record_state = "available"
        if expected_risk_state == "missing_data" and domain in {"LAB", "EFFICACY"}:
            expected_record_state = "missing"
        elif expected_risk_state == "conflict" and domain in {"AE", "CM"}:
            expected_record_state = "conflict"
        elif expected_risk_state == "partial_failure" and domain in {"PD", "EFFICACY"}:
            expected_record_state = "partial_failure"
        elif expected_risk_state == "complete_failure":
            expected_record_state = "complete_failure"
        if row["record_state"] != expected_record_state:
            raise SyntheticEgoError("event_record_state_mismatch")
        _require_id(row["source_ref"], "event.source_ref")
        _require_text(row["domain_label_zh"], "event.domain_label_zh")
        for label_field in ("event_label_zh", "detail_label_zh", "source_label_zh"):
            if len(_require_text(row[label_field], "event.%s" % label_field)) < 20:
                raise SyntheticEgoError("event_label_too_short")
        events_by_subject[row["subject_ref"]].append(row)
    if len(event_refs) != 96 or set(domain_counts) != set(DOMAINS):
        raise SyntheticEgoError("fixture_event_refs_mismatch")
    if any(count != 12 for count in domain_counts.values()):
        raise SyntheticEgoError("fixture_domain_count_mismatch")
    for subject_ref, subject_event_rows in events_by_subject.items():
        if len(subject_event_rows) != len(DOMAINS):
            raise SyntheticEgoError("subject_event_count_mismatch")
        if {row["domain"] for row in subject_event_rows} != set(DOMAINS):
            raise SyntheticEgoError("subject_marker_domain_mismatch")
        chronological_rows = sorted(
            subject_event_rows,
            key=lambda row: (
                visit_by_ref[row["visit_ref"]]["visit_order"],
                domain_rank[row["domain"]],
                row["event_ref"],
            ),
        )
        if [row["event_ref"] for row in chronological_rows] != subject_event_order[subject_ref]:
            raise SyntheticEgoError("fixture_event_chronology_mismatch")

    if raw["analysis_modes"] != list(ANALYSIS_MODES):
        raise SyntheticEgoError("fixture_analysis_modes_mismatch")
    if len(raw["analysis_inputs"]) != 6:
        raise SyntheticEgoError("fixture_analysis_input_count_mismatch")
    project_event_refs = {
        project_ref: [
            event["event_ref"]
            for event in raw["events"]
            if event["project_ref"] == project_ref
        ]
        for project_ref in project_refs
    }
    seen_modes: set[Tuple[str, str]] = set()
    for row in raw["analysis_inputs"]:
        _expected_keys(
            row,
            (
                "run_ref",
                "project_ref",
                "admission_id",
                "analysis_mode",
                "input_ref",
                "event_refs",
                "terminal_status",
                "condition",
                "source_revision",
                "synthetic_only",
            ),
            "analysis_input",
        )
        key = (row["project_ref"], row["analysis_mode"])
        if key in seen_modes:
            raise SyntheticEgoError("duplicate_analysis_input")
        seen_modes.add(key)
        if row["admission_id"] != project_by_ref[row["project_ref"]]["admission_id"]:
            raise SyntheticEgoError("analysis_input_admission_mismatch")
        _require_id(row["run_ref"], "analysis_input.run_ref")
        _require_id(row["input_ref"], "analysis_input.input_ref")
        _require_id(row["source_revision"], "analysis_input.source_revision")
        if row["project_ref"] not in project_refs or row["admission_id"] not in admission_ids:
            raise SyntheticEgoError("analysis_input_identity_mismatch")
        _require_enum(row["analysis_mode"], "analysis_input.analysis_mode", ANALYSIS_MODES)
        _require_enum(row["terminal_status"], "analysis_input.terminal_status", TERMINAL_STATUSES)
        if row["synthetic_only"] is not True or not isinstance(row["event_refs"], list):
            raise SyntheticEgoError("analysis_input_invalid")
        if not row["event_refs"]:
            raise SyntheticEgoError("analysis_input_empty")
        if any(event_ref not in event_refs for event_ref in row["event_refs"]):
            raise SyntheticEgoError("analysis_input_event_reference_mismatch")
        base_refs = project_event_refs[row["project_ref"]]
        if row["analysis_mode"] == "full":
            expected_refs = base_refs
            expected_terminal_status = "complete"
            expected_condition = "none"
        elif row["analysis_mode"] == "periodic_increment":
            expected_refs = base_refs[::2]
            expected_terminal_status = "partial"
            expected_condition = "partial_failure"
        else:
            expected_refs = base_refs[: len(base_refs) // 2]
            expected_terminal_status = "final_partial"
            expected_condition = "complete_failure"
        if row["event_refs"] != expected_refs:
            raise SyntheticEgoError("analysis_input_event_order_mismatch")
        if (
            row["terminal_status"] != expected_terminal_status
            or row["condition"] != expected_condition
        ):
            raise SyntheticEgoError("analysis_input_projection_mismatch")
        if row["condition"] not in {"none", "partial_failure", "complete_failure"}:
            raise SyntheticEgoError("analysis_input_condition_invalid")
    if seen_modes != {(project_ref, mode) for project_ref in project_refs for mode in ANALYSIS_MODES}:
        raise SyntheticEgoError("analysis_input_mode_coverage_mismatch")

    risk_states = set()
    for row in raw["risk_scenarios"]:
        _expected_keys(row, ("scenario_ref", "risk_state", "label_zh", "subject_refs"), "risk_scenario")
        _require_id(row["scenario_ref"], "risk_scenario.scenario_ref")
        risk_state = _require_enum(row["risk_state"], "risk_scenario.risk_state", RISK_STATES)
        risk_states.add(risk_state)
        if not isinstance(row["subject_refs"], list) or not row["subject_refs"]:
            raise SyntheticEgoError("risk_scenario_subjects_missing")
        expected_subjects = {
            subject["subject_ref"]
            for subject in raw["subjects"]
            if subject["risk_state"] == risk_state
        }
        if set(row["subject_refs"]) != expected_subjects:
            raise SyntheticEgoError("risk_scenario_subject_reference_mismatch")
    if risk_states != set(RISK_STATES) or len(raw["risk_scenarios"]) != len(RISK_STATES):
        raise SyntheticEgoError("fixture_risk_scenario_coverage_mismatch")
    if len(raw["analysis_cases"]) < 2:
        raise SyntheticEgoError("fixture_failure_case_coverage_mismatch")
    case_conditions = set()
    for row in raw["analysis_cases"]:
        _expected_keys(row, ("case_ref", "condition", "terminal_status", "run_ref"), "analysis_case")
        _require_id(row["case_ref"], "analysis_case.case_ref")
        _require_enum(row["condition"], "analysis_case.condition", ("partial_failure", "complete_failure"))
        _require_enum(row["terminal_status"], "analysis_case.terminal_status", TERMINAL_STATUSES)
        _require_id(row["run_ref"], "analysis_case.run_ref")
        case_conditions.add(row["condition"])
    if {"partial_failure", "complete_failure"} - case_conditions:
        raise SyntheticEgoError("fixture_failure_case_coverage_mismatch")

    journey = _require_mapping(raw["journey"], "fixture.journey")
    _expected_keys(
        journey,
        ("axis", "orientation", "visit_order", "marker_domains", "marker_counts", "event_count"),
        "journey",
    )
    if journey["axis"] != "visit" or journey["orientation"] != "horizontal":
        raise SyntheticEgoError("journey_axis_mismatch")
    if journey["visit_order"] != [1, 2, 3, 4] or journey["marker_domains"] != list(DOMAINS):
        raise SyntheticEgoError("journey_marker_domain_mismatch")
    if journey["marker_counts"] != domain_counts:
        raise SyntheticEgoError("journey_marker_count_mismatch")
    if journey["event_count"] != len(raw["events"]):
        raise SyntheticEgoError("journey_event_count_mismatch")
    if len(raw["flow_rows"]) < 1 or not any(row.get("count") == 0 for row in raw["flow_rows"]):
        raise SyntheticEgoError("flow_zero_row_missing")
    flow_node_refs = set()
    for node in raw["flow_nodes"]:
        _expected_keys(node, ("node_ref", "label_zh", "order"), "flow_node")
        node_ref = _require_id(node["node_ref"], "flow_node.node_ref")
        if node_ref in flow_node_refs:
            raise SyntheticEgoError("duplicate_flow_node")
        flow_node_refs.add(node_ref)
        if not isinstance(node["order"], int) or isinstance(node["order"], bool) or node["order"] < 1:
            raise SyntheticEgoError("flow_node_order_invalid")
    seen_flow_refs = set()
    for row in raw["flow_rows"]:
        _expected_keys(
            row,
            (
                "flow_ref",
                "project_ref",
                "center_ref",
                "stage_from",
                "stage_to",
                "count",
                "subject_refs",
                "metric",
            ),
            "flow_row",
        )
        flow_ref = _require_id(row["flow_ref"], "flow_row.flow_ref")
        if flow_ref in seen_flow_refs:
            raise SyntheticEgoError("duplicate_flow_ref")
        seen_flow_refs.add(flow_ref)
        if row["project_ref"] not in project_refs or row["center_ref"] not in center_refs:
            raise SyntheticEgoError("flow_scope_reference_mismatch")
        if row["stage_from"] not in flow_node_refs or row["stage_to"] not in flow_node_refs:
            raise SyntheticEgoError("flow_node_reference_mismatch")
        if row["metric"] != "reached":
            raise SyntheticEgoError("flow_metric_invalid")
        if not isinstance(row["count"], int) or isinstance(row["count"], bool) or row["count"] < 0:
            raise SyntheticEgoError("flow_count_invalid")
        if not isinstance(row["subject_refs"], list) or len(row["subject_refs"]) != row["count"]:
            raise SyntheticEgoError("flow_subject_count_mismatch")
        if len(set(row["subject_refs"])) != len(row["subject_refs"]):
            raise SyntheticEgoError("flow_duplicate_subject_ref")
        if not set(row["subject_refs"]).issubset(subject_refs):
            raise SyntheticEgoError("flow_subject_reference_mismatch")
        for flow_subject_ref in row["subject_refs"]:
            if subject_scope[flow_subject_ref] != (row["project_ref"], row["center_ref"]):
                raise SyntheticEgoError("flow_subject_scope_mismatch")
    expected_flow_rows: Dict[Tuple[str, str, str, str], Tuple[int, List[str]]] = {}
    expected_flow_totals: List[Dict[str, Any]] = []
    actual_flow_rows: Dict[Tuple[str, str, str, str], Tuple[int, List[str]]] = {}
    for row in raw["flow_rows"]:
        actual_flow_rows[
            (row["project_ref"], row["center_ref"], row["stage_from"], row["stage_to"])
        ] = (row["count"], list(row["subject_refs"]))
    for project_ref in project_refs:
        for center_ref in sorted(center_refs):
            scoped_subject_refs = [
                subject["subject_ref"]
                for subject in raw["subjects"]
                if subject["project_ref"] == project_ref and subject["center_ref"] == center_ref
            ]
            count = len(scoped_subject_refs)
            transitions = (
                ("consent", "screening", count, scoped_subject_refs),
                (
                    "screening",
                    "treatment",
                    max(count - 1, 0),
                    scoped_subject_refs[: max(count - 1, 0)],
                ),
                (
                    "screening",
                    "study_status",
                    1 if count else 0,
                    scoped_subject_refs[-1:] if count else [],
                ),
                (
                    "treatment",
                    "study_status",
                    max(count - 1, 0),
                    scoped_subject_refs[: max(count - 1, 0)],
                ),
                ("treatment", "recheck", 0, []),
            )
            for stage_from, stage_to, row_count, row_subjects in transitions:
                expected_flow_rows[(project_ref, center_ref, stage_from, stage_to)] = (
                    row_count,
                    row_subjects,
                )
            expected_flow_totals.append(
                {
                    "project_ref": project_ref,
                    "center_ref": center_ref,
                    "subject_count": count,
                    "consent_to_screening": count,
                    "screening_to_treatment": max(count - 1, 0),
                    "screening_to_study_status": 1 if count else 0,
                    "treatment_to_study_status": max(count - 1, 0),
                    "treatment_to_recheck": 0,
                    "terminal_total": count,
                }
            )
    if len(actual_flow_rows) != len(raw["flow_rows"]):
        raise SyntheticEgoError("flow_duplicate_transition")
    if set(actual_flow_rows) != set(expected_flow_rows):
        raise SyntheticEgoError("flow_transition_coverage_mismatch")
    for key, expected in expected_flow_rows.items():
        if actual_flow_rows[key] != expected:
            raise SyntheticEgoError("flow_conservation_mismatch")
    if not isinstance(raw["flow_totals"], list) or len(raw["flow_totals"]) != 6:
        raise SyntheticEgoError("flow_total_count_mismatch")
    for row in raw["flow_totals"]:
        _expected_keys(
            row,
            (
                "project_ref",
                "center_ref",
                "subject_count",
                "consent_to_screening",
                "screening_to_treatment",
                "screening_to_study_status",
                "treatment_to_study_status",
                "treatment_to_recheck",
                "terminal_total",
            ),
            "flow_total",
        )
    if raw["flow_totals"] != expected_flow_totals:
        raise SyntheticEgoError("flow_total_conservation_mismatch")
    dense_candidates: List[Tuple[str, str, List[Mapping[str, Any]]]] = []
    for subject_ref in sorted(subject_refs):
        for visit_ref in subject_visit_order[subject_ref]:
            visit_events = [
                row
                for row in events_by_subject[subject_ref]
                if row["visit_ref"] == visit_ref
            ]
            if (
                len(visit_events) == len(DOMAINS)
                and {row["domain"] for row in visit_events} == set(DOMAINS)
                and len({row["occurred_on"] for row in visit_events}) == 1
            ):
                dense_candidates.append((subject_ref, visit_ref, visit_events))
    if not dense_candidates:
        raise SyntheticEgoError("dense_same_day_domain_markers_missing")
    dense_subject_ref, dense_visit_ref, dense_event_rows = dense_candidates[0]
    dense_event_rows = sorted(
        dense_event_rows,
        key=lambda row: (domain_rank[row["domain"]], row["event_ref"]),
    )
    dense_visit = visit_by_ref[dense_visit_ref]
    expected_challenge = {
        "dense_same_day": {
            "subject_ref": dense_subject_ref,
            "visit_ref": dense_visit_ref,
            "occurred_on": dense_visit["occurred_on"],
            "event_refs": [row["event_ref"] for row in dense_event_rows],
            "domains": [row["domain"] for row in dense_event_rows],
            "event_count": len(dense_event_rows),
        },
        "long_label_fields": ["event_label_zh", "detail_label_zh", "source_label_zh"],
        "long_label_min_chars": min(
            len(row[field])
            for row in raw["events"]
            for field in ("event_label_zh", "detail_label_zh", "source_label_zh")
        ),
        "flow_shape": {
            "has_split": any(
                row["stage_from"] == "screening"
                and row["stage_to"] in {"treatment", "study_status"}
                and row["count"] > 0
                for row in raw["flow_rows"]
            ),
            "has_merge": any(
                row["stage_to"] == "study_status" and row["count"] > 0
                for row in raw["flow_rows"]
            ),
            "has_zero": any(row["count"] == 0 for row in raw["flow_rows"]),
            "has_center_differences": (
                {
                    center_ref: sum(
                        1
                        for subject in raw["subjects"]
                        if subject["project_ref"] == "synthetic-project-alpha"
                        and subject["center_ref"] == center_ref
                    )
                    for center_ref in sorted(center_refs)
                }
                != {
                    center_ref: sum(
                        1
                        for subject in raw["subjects"]
                        if subject["project_ref"] == "synthetic-project-beta"
                        and subject["center_ref"] == center_ref
                    )
                    for center_ref in sorted(center_refs)
                }
            ),
        },
    }
    challenge = _require_mapping(raw["challenge"], "fixture.challenge")
    _expected_keys(
        challenge,
        ("dense_same_day", "long_label_fields", "long_label_min_chars", "flow_shape"),
        "fixture.challenge",
    )
    dense_challenge = _require_mapping(
        challenge["dense_same_day"], "fixture.challenge.dense_same_day"
    )
    flow_shape = _require_mapping(challenge["flow_shape"], "fixture.challenge.flow_shape")
    _expected_keys(
        dense_challenge,
        ("subject_ref", "visit_ref", "occurred_on", "event_refs", "domains", "event_count"),
        "fixture.challenge.dense_same_day",
    )
    _expected_keys(
        flow_shape,
        ("has_split", "has_merge", "has_zero", "has_center_differences"),
        "fixture.challenge.flow_shape",
    )
    if challenge != expected_challenge:
        raise SyntheticEgoError("fixture_challenge_oracle_mismatch")

    expected_risk_state_counts = {
        risk_state: sum(1 for subject in raw["subjects"] if subject["risk_state"] == risk_state)
        for risk_state in RISK_STATES
    }
    expected_center_subject_counts = {
        project_ref: {
            center_ref: sum(
                1
                for subject in raw["subjects"]
                if subject["project_ref"] == project_ref and subject["center_ref"] == center_ref
            )
            for center_ref in sorted(center_refs)
        }
        for project_ref in project_refs
    }
    expected_table_totals = {
        "projects": len(raw["projects"]),
        "centers": len(raw["centers"]),
        "subjects": len(raw["subjects"]),
        "visits": len(raw["visits"]),
        "events": len(raw["events"]),
        "analysis_inputs": len(raw["analysis_inputs"]),
        "risk_scenarios": len(raw["risk_scenarios"]),
        "flow_rows": len(raw["flow_rows"]),
        "flow_count_total": sum(row["count"] for row in raw["flow_rows"]),
        "domain_counts": domain_counts,
        "risk_state_counts": expected_risk_state_counts,
        "center_subject_counts": expected_center_subject_counts,
    }
    table_totals = _require_mapping(raw["table_totals"], "fixture.table_totals")
    _expected_keys(
        table_totals,
        tuple(expected_table_totals.keys()),
        "fixture.table_totals",
    )
    if table_totals != expected_table_totals:
        raise SyntheticEgoError("fixture_table_total_mismatch")
    section = _require_mapping(raw["section_15_4"], "fixture.section_15_4")
    _expected_keys(
        section,
        (
            "synthetic_object_ref",
            "task_keys",
            "task_count",
            "evidence_mode",
            "task_spec_schema",
            "task_spec_version",
            "task_spec_digest",
            "execution_required",
            "initial_state_included",
        ),
        "section_15_4",
    )
    _require_id(section["synthetic_object_ref"], "section_15_4.synthetic_object_ref")
    if section["task_keys"] != list(TASK_KEYS) or section["task_count"] != len(TASK_KEYS):
        raise SyntheticEgoError("section_15_4_task_coverage_mismatch")
    if (
        section["evidence_mode"] != "required_task_specification"
        or section["task_spec_schema"] != TASK_SPEC_SCHEMA
        or section["task_spec_version"] != TASK_SPEC_VERSION
        or section["task_spec_digest"] != TASK_SPEC_DIGEST
        or section["execution_required"] is not True
        or section["initial_state_included"] is not True
    ):
        raise SyntheticEgoError("section_15_4_evidence_mode_mismatch")

    counts = _require_mapping(raw["counts"], "fixture.counts")
    _expected_keys(
        counts,
        (
            "projects",
            "centers",
            "subjects",
            "visits",
            "events",
            "analysis_inputs",
            "flow_rows",
            "risk_scenarios",
            "domain_counts",
        ),
        "fixture.counts",
    )
    expected_counts = {
        "projects": 2,
        "centers": 3,
        "subjects": 12,
        "visits": 48,
        "events": 96,
        "analysis_inputs": 6,
        "flow_rows": len(raw["flow_rows"]),
        "risk_scenarios": 8,
        "domain_counts": domain_counts,
    }
    for key, expected in expected_counts.items():
        if counts[key] != expected:
            raise SyntheticEgoError("fixture_count_mismatch:%s" % key)

    _assert_no_path_or_external_literal(raw, "fixture")
    recomputed_fixture_digest = _digest_without(
        raw, "fixture_digest", "binding_digest", "profile_binding_digest"
    )
    if recomputed_fixture_digest != raw["fixture_digest"]:
        raise SyntheticEgoError("fixture_digest_mismatch")
    expected_profile_digest = digest_ref(
        {
            "contract_version": raw["contract_version"],
            "app_version": raw["app_version"],
            "fixture_digest": raw["fixture_digest"],
            "synthetic_profile_id": raw["synthetic_profile_id"],
        }
    )
    if raw["binding_digest"] != expected_profile_digest:
        raise SyntheticEgoError("fixture_profile_binding_digest_mismatch")
    return _copy_json(raw)


# Descriptive aliases for callers that use the contract language directly.
create_synthetic_fixture = build_synthetic_fixture
build_cross_domain_synthetic_fixture = build_synthetic_fixture
validate_cross_domain_synthetic_fixture = validate_synthetic_fixture


# ---------------------------------------------------------------------------
# Synthetic profile binding and mock/recorded adapter
# ---------------------------------------------------------------------------


def _binding_digest_projection(value: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: _copy_json(item)
        for key, item in value.items()
        if key != "binding_digest"
    }


def build_synthetic_binding(
    fixture: Mapping[str, Any],
    project_ref: str,
    analysis_mode: str = "full",
    *,
    run_ref: Optional[str] = None,
    provider: str = SYNTHETIC_PROVIDER,
    model: str = SYNTHETIC_MODEL,
    adapter_id: str = RECORDED_ADAPTER_ID,
) -> Dict[str, Any]:
    """Freeze one synthetic profile binding for one project/run."""

    checked_fixture = validate_synthetic_fixture(fixture)
    project_ref = _require_id(project_ref, "binding.project_ref")
    analysis_mode = _require_enum(analysis_mode, "binding.analysis_mode", ANALYSIS_MODES)
    project = _find_project(checked_fixture, project_ref)
    run = _find_run(checked_fixture, project_ref, analysis_mode)
    selected_run_ref = run["run_ref"] if run_ref is None else _require_id(run_ref, "binding.run_ref")
    if not selected_run_ref.startswith("synthetic-run-"):
        raise SyntheticEgoError("binding_run_must_be_synthetic")
    provider = _require_text(provider, "binding.provider")
    model = _require_text(model, "binding.model")
    adapter_id = _require_text(adapter_id, "binding.adapter_id")
    if not _SYNTHETIC_RE.match(provider) or not _SYNTHETIC_RE.match(model):
        raise SyntheticEgoError("non_synthetic_provider_or_model")
    if adapter_id != RECORDED_ADAPTER_ID:
        raise SyntheticEgoError("adapter_not_mock_recorded")
    event_refs = list(run["event_refs"])
    source_manifest_digest = digest_ref(
        {
            "fixture_digest": checked_fixture["fixture_digest"],
            "project_ref": project_ref,
            "analysis_mode": analysis_mode,
            "event_refs": event_refs,
            "manifest_kind": "source",
        }
    )
    output_manifest_digest = digest_ref(
        {
            "fixture_digest": checked_fixture["fixture_digest"],
            "project_ref": project_ref,
            "analysis_mode": analysis_mode,
            "run_ref": selected_run_ref,
            "manifest_kind": "output",
        }
    )
    binding_id = "synthetic-binding-%s-%s-%s" % (
        project_ref,
        analysis_mode,
        checked_fixture["fixture_digest"][7:15],
    )
    body: Dict[str, Any] = {
        "schema": BINDING_SCHEMA,
        "version": BINDING_VERSION,
        "contract_ref": CONTRACT_REF,
        "contract_version": CONTRACT_VERSION,
        "app_version": checked_fixture["app_version"],
        "synthetic_profile_id": checked_fixture["synthetic_profile_id"],
        "fixture_id": checked_fixture["fixture_id"],
        "fixture_digest": checked_fixture["fixture_digest"],
        "fixture_binding_digest": checked_fixture["binding_digest"],
        "profile_binding_digest": checked_fixture["profile_binding_digest"],
        "binding_id": binding_id,
        "project_ref": project_ref,
        "admission_id": project["admission_id"],
        "run_ref": selected_run_ref,
        "analysis_mode": analysis_mode,
        "provider": provider,
        "model": model,
        "adapter_id": adapter_id,
        "adapter_version": ADAPTER_VERSION,
        "adapter_kind": RECORDED_ADAPTER_KIND,
        "source_manifest_digest": source_manifest_digest,
        "output_manifest_digest": output_manifest_digest,
        "synthetic_only": True,
        "offline": True,
    }
    body["binding_digest"] = digest_ref(_binding_digest_projection(body))
    return validate_synthetic_binding(body, fixture=checked_fixture)


def validate_synthetic_binding(
    value: Mapping[str, Any], *, fixture: Optional[Mapping[str, Any]] = None
) -> Dict[str, Any]:
    """Fail closed on unknown provider/model, drift, or digest mismatch."""

    raw = dict(_require_mapping(value, "binding"))
    _expected_keys(
        raw,
        (
            "schema",
            "version",
            "contract_ref",
            "contract_version",
            "app_version",
            "synthetic_profile_id",
            "fixture_id",
            "fixture_digest",
            "fixture_binding_digest",
            "profile_binding_digest",
            "binding_id",
            "project_ref",
            "admission_id",
            "run_ref",
            "analysis_mode",
            "provider",
            "model",
            "adapter_id",
            "adapter_version",
            "adapter_kind",
            "source_manifest_digest",
            "output_manifest_digest",
            "synthetic_only",
            "offline",
            "binding_digest",
        ),
        "binding",
    )
    if raw["schema"] != BINDING_SCHEMA or raw["version"] != BINDING_VERSION:
        raise SyntheticEgoError("binding_schema_mismatch")
    if raw["contract_ref"] != CONTRACT_REF or raw["contract_version"] != CONTRACT_VERSION:
        raise SyntheticEgoError("binding_contract_mismatch")
    if raw["app_version"] != APP_VERSION:
        raise SyntheticEgoError("binding_app_version_mismatch")
    if raw["synthetic_profile_id"] != SYNTHETIC_PROFILE_ID:
        raise SyntheticEgoError("binding_profile_mismatch")
    if raw["fixture_id"] != "synthetic-cross-domain-g6-v1":
        raise SyntheticEgoError("binding_fixture_id_invalid")
    for field in (
        "fixture_id",
        "binding_id",
        "project_ref",
        "admission_id",
        "run_ref",
    ):
        _require_id(raw[field], "binding.%s" % field)
    if not raw["project_ref"].startswith("synthetic-project-"):
        raise SyntheticEgoError("binding_project_not_synthetic")
    if not raw["admission_id"].startswith("synthetic-admission-"):
        raise SyntheticEgoError("binding_admission_not_synthetic")
    if not raw["run_ref"].startswith("synthetic-run-"):
        raise SyntheticEgoError("binding_run_not_synthetic")
    _require_sha256_ref(raw["fixture_digest"], "binding.fixture_digest")
    _require_sha256_ref(raw["fixture_binding_digest"], "binding.fixture_binding_digest")
    _require_sha256_ref(raw["profile_binding_digest"], "binding.profile_binding_digest")
    _require_sha256_ref(raw["source_manifest_digest"], "binding.source_manifest_digest")
    _require_sha256_ref(raw["binding_digest"], "binding.binding_digest")
    _require_enum(raw["analysis_mode"], "binding.analysis_mode", ANALYSIS_MODES)
    provider = _require_text(raw["provider"], "binding.provider")
    model = _require_text(raw["model"], "binding.model")
    if provider != SYNTHETIC_PROVIDER or model != SYNTHETIC_MODEL:
        raise SyntheticEgoError("non_synthetic_provider_or_model")
    if raw["adapter_id"] != RECORDED_ADAPTER_ID or raw["adapter_kind"] != RECORDED_ADAPTER_KIND:
        raise SyntheticEgoError("adapter_not_mock_recorded")
    if raw["adapter_version"] != ADAPTER_VERSION:
        raise SyntheticEgoError("adapter_version_mismatch")
    if raw["synthetic_only"] is not True or raw["offline"] is not True:
        raise SyntheticEgoError("binding_must_be_synthetic_offline")
    _assert_no_path_or_external_literal(raw, "binding")
    if digest_ref(_binding_digest_projection(raw)) != raw["binding_digest"]:
        raise SyntheticEgoError("binding_digest_mismatch")
    if fixture is not None:
        checked_fixture = validate_synthetic_fixture(fixture)
        if raw["fixture_id"] != checked_fixture["fixture_id"]:
            raise SyntheticEgoError("binding_fixture_id_mismatch")
        if raw["fixture_digest"] != checked_fixture["fixture_digest"]:
            raise SyntheticEgoError("binding_fixture_digest_mismatch")
        if raw["fixture_binding_digest"] != checked_fixture["binding_digest"]:
            raise SyntheticEgoError("binding_fixture_profile_digest_mismatch")
        if raw["profile_binding_digest"] != checked_fixture["profile_binding_digest"]:
            raise SyntheticEgoError("binding_profile_binding_digest_mismatch")
        project = _find_project(checked_fixture, raw["project_ref"])
        if raw["admission_id"] != project["admission_id"]:
            raise SyntheticEgoError("binding_admission_mismatch")
        run = _find_run(checked_fixture, raw["project_ref"], raw["analysis_mode"])
        expected_source = digest_ref(
            {
                "fixture_digest": checked_fixture["fixture_digest"],
                "project_ref": raw["project_ref"],
                "analysis_mode": raw["analysis_mode"],
                "event_refs": run["event_refs"],
                "manifest_kind": "source",
            }
        )
        expected_output = digest_ref(
            {
                "fixture_digest": checked_fixture["fixture_digest"],
                "project_ref": raw["project_ref"],
                "analysis_mode": raw["analysis_mode"],
                "run_ref": raw["run_ref"],
                "manifest_kind": "output",
            }
        )
        if raw["source_manifest_digest"] != expected_source:
            raise SyntheticEgoError("binding_source_manifest_mismatch")
        if raw["output_manifest_digest"] != expected_output:
            raise SyntheticEgoError("binding_output_manifest_mismatch")
    return _copy_json(raw)


class SyntheticRecordedAdapter(_notification.SyntheticNotificationAdapter):
    """Mock/recorded adapter with no network, model, or fallback path."""

    def __init__(
        self,
        fixture: Mapping[str, Any],
        binding: Optional[Mapping[str, Any]] = None,
        *,
        capability_by_admission: Optional[Mapping[str, str]] = None,
        default_capability: str = "unknown",
        channel_evidence_by_capability: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.fixture = validate_synthetic_fixture(fixture)
        super().__init__(
            capability_by_admission=capability_by_admission,
            default_capability=default_capability,
            channel_evidence_by_capability=channel_evidence_by_capability
            or {"authorized": "presented"},
        )
        self._bindings: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        self._analysis_calls: List[Dict[str, Any]] = []
        self._recorded_calls: List[Dict[str, Any]] = []
        self._fallback_attempts: List[Dict[str, Any]] = []
        self._external_calls: List[Dict[str, Any]] = []
        if binding is not None:
            self.bind(binding)

    @property
    def adapter_descriptor(self) -> Dict[str, Any]:
        return {
            "schema": ADAPTER_SCHEMA,
            "version": ADAPTER_VERSION,
            "id": RECORDED_ADAPTER_ID,
            "kind": RECORDED_ADAPTER_KIND,
            "provider": SYNTHETIC_PROVIDER,
            "model": SYNTHETIC_MODEL,
            "synthetic_only": True,
            "offline": True,
            "network_allowed": False,
            "fallback_allowed": False,
        }

    @property
    def recorded_calls(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(_copy_json(item) for item in self._recorded_calls)

    @property
    def analysis_calls(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(_copy_json(item) for item in self._analysis_calls)

    @property
    def fallback_attempts(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(_copy_json(item) for item in self._fallback_attempts)

    @property
    def external_calls(self) -> Tuple[Dict[str, Any], ...]:
        return tuple(_copy_json(item) for item in self._external_calls)

    @property
    def real_model_calls(self) -> Tuple[Dict[str, Any], ...]:
        return ()

    @property
    def run_side_effect_count(self) -> int:
        return len(self._analysis_calls) + len(self._fallback_attempts)

    def bind(self, binding: Mapping[str, Any]) -> Dict[str, Any]:
        checked = validate_synthetic_binding(binding, fixture=self.fixture)
        key = (checked["project_ref"], checked["admission_id"], checked["run_ref"])
        existing = self._bindings.get(key)
        if existing is not None and existing["binding_digest"] != checked["binding_digest"]:
            raise SyntheticEgoError("binding_replacement_conflict")
        self._bindings[key] = checked
        return _copy_json(checked)

    def _bound_for_identity(self, identity: Mapping[str, Any]) -> Dict[str, Any]:
        project_ref = _require_id(identity.get("project_ref"), "identity.project_ref")
        admission_id = _require_id(identity.get("admission_id"), "identity.admission_id")
        run_id = _require_id(identity.get("run_id"), "identity.run_id")
        binding = self._bindings.get((project_ref, admission_id, run_id))
        if binding is None:
            raise SyntheticEgoError("unbound_synthetic_run")
        return binding

    def execute_analysis(
        self,
        binding: Mapping[str, Any],
        *,
        terminal_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        checked = self.bind(binding)
        run = _find_run(self.fixture, checked["project_ref"], checked["analysis_mode"])
        status = run["terminal_status"] if terminal_status is None else _require_enum(
            terminal_status, "terminal_status", TERMINAL_STATUSES
        )
        if status != run["terminal_status"]:
            raise SyntheticEgoError("recorded_terminal_status_mismatch")
        identity = {
            "project_ref": checked["project_ref"],
            "admission_id": checked["admission_id"],
            "run_id": checked["run_ref"],
        }
        existing = next(
            (
                call["response"]
                for call in self._analysis_calls
                if call["identity"] == identity
            ),
            None,
        )
        if existing is not None:
            return _copy_json(existing)
        response = {
            "identity": identity,
            "terminal_status": status,
            "terminal_revision": "synthetic-revision-%s" % checked["analysis_mode"],
            "fixture_digest": checked["fixture_digest"],
            "binding_digest": checked["binding_digest"],
            "source_manifest_digest": checked["source_manifest_digest"],
            "output_manifest_digest": checked["output_manifest_digest"],
            "event_refs": list(run["event_refs"]),
            "recorded": True,
            "synthetic_only": True,
        }
        entry = {
            "kind": "analysis",
            "identity": identity,
            "binding_digest": checked["binding_digest"],
            "response": response,
        }
        self._analysis_calls.append(entry)
        self._recorded_calls.append(
            SyntheticRecordedCall(
                kind="analysis",
                identity=identity,
                binding_digest=checked["binding_digest"],
                outcome="recorded",
            ).as_dict()
        )
        return _copy_json(response)

    # Familiar aliases for app adapters and focused tests.
    run_analysis = execute_analysis
    execute_run = execute_analysis

    def attempt_system_notification(
        self,
        fact: Mapping[str, Any],
        capability_state: str,
    ) -> str:
        identity = dict(_require_mapping(fact.get("identity"), "fact.identity"))
        binding = self._bound_for_identity(identity)
        if fact.get("binding_digest") != binding["binding_digest"]:
            raise SyntheticEgoError("notification_binding_mismatch")
        evidence = super().attempt_system_notification(fact, capability_state)
        self._recorded_calls.append(
            SyntheticRecordedCall(
                kind="system_notification",
                identity=identity,
                binding_digest=binding["binding_digest"],
                outcome=evidence,
            ).as_dict()
        )
        return evidence

    def record_navigation_click(self, intent: Mapping[str, Any]) -> None:
        # ``build_navigation_intent`` has already performed the complete target
        # check.  Keep this ledger side-effect free and only record the intent.
        identity = {
            "project_ref": intent.get("project_ref"),
            "admission_id": intent.get("admission_id"),
            "run_id": intent.get("run_id"),
        }
        binding = self._bound_for_identity(identity)
        super().record_navigation_click(intent)
        self._recorded_calls.append(
            SyntheticRecordedCall(
                kind="navigation",
                identity=identity,
                binding_digest=binding["binding_digest"],
                outcome="navigate_only",
            ).as_dict()
        )

    def attempt_fallback(self, reason: str = "") -> None:
        self._fallback_attempts.append({"reason": str(reason)})
        raise SyntheticEgoError("fallback_forbidden")

    def call_external(self, target: str) -> None:
        self._external_calls.append({"target": str(target)})
        raise SyntheticEgoError("external_call_forbidden")


MockRecordedAdapter = SyntheticRecordedAdapter
SyntheticBindingAdapter = SyntheticRecordedAdapter


def build_synthetic_binding_object(
    fixture: Mapping[str, Any], project_ref: str, analysis_mode: str = "full", **kwargs: Any
) -> SyntheticBinding:
    return SyntheticBinding(build_synthetic_binding(fixture, project_ref, analysis_mode, **kwargs))


# ---------------------------------------------------------------------------
# Nine terminal states × four capability states notification matrix
# ---------------------------------------------------------------------------


def _notification_accessibility(
    binding: Mapping[str, Any], terminal_status: str, terminal_revision: str
) -> _notification.TargetAccessibility:
    result_accessible = terminal_status in {"complete", "partial"}
    explanation_accessible = not result_accessible
    return _notification.TargetAccessibility(
        current_terminal_revision=terminal_revision,
        binding_digest=binding["binding_digest"],
        source_manifest_digest=binding["source_manifest_digest"],
        output_manifest_digest=binding["output_manifest_digest"],
        target_exists=True,
        result_accessible=result_accessible,
        explanation_accessible=explanation_accessible,
    )


def _notification_binding(binding: Mapping[str, Any]) -> _notification.AdmissionBinding:
    return _notification.AdmissionBinding(
        project_ref=binding["project_ref"],
        admission_id=binding["admission_id"],
        admission_status="accepted",
        binding_digest=binding["binding_digest"],
        contract_version=_notification.CONTRACT_VERSION,
        app_version=binding["app_version"],
        registered_project_display_name="合成项目",
        binding_valid=True,
    )


def _simulate_notification_row(
    fixture: Mapping[str, Any], terminal_status: str, capability_state: str, index: int
) -> Dict[str, Any]:
    project_ref = fixture["projects"][index % len(fixture["projects"])]
    project_id = project_ref["project_ref"]
    mode = ANALYSIS_MODES[index % len(ANALYSIS_MODES)]
    run_ref = "synthetic-run-notification-%03d" % (index + 1)
    binding = build_synthetic_binding(
        fixture,
        project_id,
        mode,
        run_ref=run_ref,
    )
    terminal_revision = "synthetic-terminal-revision-%03d" % (index + 1)
    event = _notification.TerminalEvent(
        project_ref=project_id,
        admission_id=binding["admission_id"],
        run_id=run_ref,
        terminal_status=terminal_status,
        terminal_revision=terminal_revision,
        authoritative=True,
        frozen=True,
    )
    access = _notification_accessibility(binding, terminal_status, terminal_revision)
    store = _notification.NotificationStore()
    adapter = SyntheticRecordedAdapter(
        fixture,
        binding,
        capability_by_admission={binding["admission_id"]: capability_state},
        default_capability=capability_state,
        channel_evidence_by_capability={"authorized": "presented"},
    )
    processed = _notification.process_terminal_event(
        event,
        _notification_binding(binding),
        access,
        store,
        adapter,
    )
    if processed.status != "ok" or processed.fact is None:
        raise NotificationMatrixError(
            "notification_matrix_process_failed:%s:%s:%s"
            % (terminal_status, capability_state, processed.reason or "unknown")
        )
    in_app = store.get_in_app(event.identity_key)
    if in_app is None or in_app.get("persistent") is not True:
        raise NotificationMatrixError("notification_in_app_record_missing")
    system_navigation = _notification.build_navigation_intent(
        processed.fact,
        _notification_binding(binding),
        access,
        store,
        adapter,
        click_count=1,
    )
    in_app_navigation = _notification.build_navigation_intent(
        processed.fact,
        _notification_binding(binding),
        access,
        store,
        adapter,
        click_count=1,
    )
    if system_navigation.status != "ok" or in_app_navigation.status != "ok":
        raise NotificationMatrixError("notification_navigation_process_failed")
    navigation_paths = (
        {
            "source": "system_notification",
            "status": system_navigation.status,
            "intent": system_navigation.intent,
        },
        {
            "source": "in_app_record",
            "status": in_app_navigation.status,
            "intent": in_app_navigation.intent,
        },
    )
    row: Dict[str, Any] = {
        "matrix_key": "%s:%s" % (terminal_status, capability_state),
        "terminal_status": terminal_status,
        "notification_status": processed.fact["notification_status"],
        "capability_state": capability_state,
        "identity": processed.fact["identity"],
        "terminal_revision": terminal_revision,
        "fixture_digest": fixture["fixture_digest"],
        "binding_digest": binding["binding_digest"],
        "source_manifest_digest": binding["source_manifest_digest"],
        "output_manifest_digest": binding["output_manifest_digest"],
        "in_app_persistent": in_app["persistent"],
        "in_app_fact_digest": processed.fact["fact_digest"],
        "system_copy": processed.fact["system_copy"],
        "channel_evidence": processed.fact["channel_evidence"],
        "system_attempt_count": len(adapter.system_attempts),
        "navigation_paths": list(navigation_paths),
        "navigation_side_effect_count": len(adapter.navigation_side_effects),
        "run_side_effect_count": adapter.run_side_effect_count,
        "real_model_call_count": len(adapter.real_model_calls),
        "fallback_attempt_count": len(adapter.fallback_attempts),
        "recorded_adapter_only": True,
    }
    return row


def _build_negative_navigation_cases(fixture: Mapping[str, Any]) -> List[Dict[str, Any]]:
    binding = build_synthetic_binding(
        fixture,
        fixture["projects"][0]["project_ref"],
        "full",
        run_ref="synthetic-run-notification-negative",
    )
    terminal_revision = "synthetic-terminal-revision-negative"
    event = _notification.TerminalEvent(
        project_ref=binding["project_ref"],
        admission_id=binding["admission_id"],
        run_id=binding["run_ref"],
        terminal_status="complete",
        terminal_revision=terminal_revision,
        authoritative=True,
        frozen=True,
    )
    access = _notification_accessibility(binding, "complete", terminal_revision)
    notify_binding = _notification_binding(binding)
    store = _notification.NotificationStore()
    adapter = SyntheticRecordedAdapter(
        fixture,
        binding,
        capability_by_admission={binding["admission_id"]: "authorized"},
        default_capability="authorized",
        channel_evidence_by_capability={"authorized": "presented"},
    )
    processed = _notification.process_terminal_event(
        event, notify_binding, access, store, adapter
    )
    if processed.status != "ok" or processed.fact is None:
        raise NotificationMatrixError("negative_navigation_fixture_failed")
    mutations: Dict[str, Dict[str, Any]] = {
        "old_revision": {"current_terminal_revision": "synthetic-terminal-revision-old"},
        "binding_drift": {"binding_digest": "sha256:" + "f" * 64},
        "source_manifest_drift": {"source_manifest_digest": "sha256:" + "e" * 64},
        "output_manifest_drift": {"output_manifest_digest": "sha256:" + "d" * 64},
        "target_deleted": {"target_exists": False},
        "target_inaccessible": {"result_accessible": False},
    }
    rows: List[Dict[str, Any]] = []
    for case, changes in mutations.items():
        access_payload = {
            "current_terminal_revision": access.current_terminal_revision,
            "binding_digest": access.binding_digest,
            "source_manifest_digest": access.source_manifest_digest,
            "output_manifest_digest": access.output_manifest_digest,
            "target_exists": access.target_exists,
            "result_accessible": access.result_accessible,
            "explanation_accessible": access.explanation_accessible,
        }
        access_payload.update(changes)
        mutated_access = _notification.TargetAccessibility(**access_payload)
        before = len(adapter.navigation_side_effects)
        nav = _notification.build_navigation_intent(
            processed.fact,
            notify_binding,
            mutated_access,
            store,
            adapter,
            click_count=1,
        )
        after = len(adapter.navigation_side_effects)
        rows.append(
            {
                "case": case,
                "status": nav.status,
                "user_message": nav.user_message,
                "side_effect_count_before": before,
                "side_effect_count_after": after,
                "run_side_effect_count": adapter.run_side_effect_count,
                "identity": processed.fact["identity"],
                "binding_digest": binding["binding_digest"],
            }
        )
    return rows


def build_notification_matrix(fixture: Mapping[str, Any]) -> Dict[str, Any]:
    """Build all 36 terminal/capability combinations and six blocked paths."""

    checked_fixture = validate_synthetic_fixture(fixture)
    matrix_pairs = (
        (terminal_status, capability_state)
        for terminal_status in TERMINAL_STATUSES
        for capability_state in CAPABILITY_STATES
    )
    rows = [
        _simulate_notification_row(
            checked_fixture,
            terminal_status,
            capability_state,
            index,
        )
        for index, (terminal_status, capability_state) in enumerate(matrix_pairs)
    ]
    body: Dict[str, Any] = {
        "schema": NOTIFICATION_MATRIX_SCHEMA,
        "version": NOTIFICATION_MATRIX_VERSION,
        "contract_ref": CONTRACT_REF,
        "contract_version": CONTRACT_VERSION,
        "app_version": checked_fixture["app_version"],
        "synthetic_profile_id": checked_fixture["synthetic_profile_id"],
        "fixture_digest": checked_fixture["fixture_digest"],
        "adapter": {
            "schema": ADAPTER_SCHEMA,
            "version": ADAPTER_VERSION,
            "id": RECORDED_ADAPTER_ID,
            "kind": RECORDED_ADAPTER_KIND,
            "provider": SYNTHETIC_PROVIDER,
            "model": SYNTHETIC_MODEL,
            "network_allowed": False,
            "fallback_allowed": False,
        },
        "terminal_statuses": list(TERMINAL_STATUSES),
        "capability_states": list(CAPABILITY_STATES),
        "row_count": len(rows),
        "rows": rows,
        "negative_navigation_cases": _build_negative_navigation_cases(checked_fixture),
        "no_real_model_calls": True,
        "no_fallback": True,
        "recorded_only": True,
    }
    body["matrix_digest"] = _digest_without(body, "matrix_digest")
    return validate_notification_matrix(body, fixture=checked_fixture)


def validate_notification_matrix(
    value: Mapping[str, Any], *, fixture: Optional[Mapping[str, Any]] = None
) -> Dict[str, Any]:
    """Validate full 36-row coverage, persistence, navigation, and no fallback."""

    raw = dict(_require_mapping(value, "notification_matrix"))
    _expected_keys(
        raw,
        (
            "schema",
            "version",
            "contract_ref",
            "contract_version",
            "app_version",
            "synthetic_profile_id",
            "fixture_digest",
            "adapter",
            "terminal_statuses",
            "capability_states",
            "row_count",
            "rows",
            "negative_navigation_cases",
            "no_real_model_calls",
            "no_fallback",
            "recorded_only",
            "matrix_digest",
        ),
        "notification_matrix",
    )
    if raw["schema"] != NOTIFICATION_MATRIX_SCHEMA or raw["version"] != NOTIFICATION_MATRIX_VERSION:
        raise SyntheticEgoError("notification_matrix_schema_mismatch")
    if raw["contract_ref"] != CONTRACT_REF or raw["contract_version"] != CONTRACT_VERSION:
        raise SyntheticEgoError("notification_matrix_contract_mismatch")
    if raw["app_version"] != APP_VERSION or raw["synthetic_profile_id"] != SYNTHETIC_PROFILE_ID:
        raise SyntheticEgoError("notification_matrix_binding_metadata_mismatch")
    _require_sha256_ref(raw["fixture_digest"], "notification_matrix.fixture_digest")
    _require_sha256_ref(raw["matrix_digest"], "notification_matrix.matrix_digest")
    if _digest_without(raw, "matrix_digest") != raw["matrix_digest"]:
        raise SyntheticEgoError("notification_matrix_digest_mismatch")
    adapter = _require_mapping(raw["adapter"], "notification_matrix.adapter")
    _expected_keys(
        adapter,
        (
            "schema",
            "version",
            "id",
            "kind",
            "provider",
            "model",
            "network_allowed",
            "fallback_allowed",
        ),
        "notification_matrix.adapter",
    )
    if (
        adapter["schema"] != ADAPTER_SCHEMA
        or adapter["version"] != ADAPTER_VERSION
        or adapter["id"] != RECORDED_ADAPTER_ID
        or adapter["kind"] != RECORDED_ADAPTER_KIND
        or adapter["provider"] != SYNTHETIC_PROVIDER
        or adapter["model"] != SYNTHETIC_MODEL
        or adapter["network_allowed"] is not False
        or adapter["fallback_allowed"] is not False
    ):
        raise SyntheticEgoError("notification_matrix_adapter_mismatch")
    if raw["terminal_statuses"] != list(TERMINAL_STATUSES):
        raise SyntheticEgoError("notification_matrix_terminal_coverage_mismatch")
    if raw["capability_states"] != list(CAPABILITY_STATES):
        raise SyntheticEgoError("notification_matrix_capability_coverage_mismatch")
    if raw["row_count"] != 36 or not isinstance(raw["rows"], list) or len(raw["rows"]) != 36:
        raise SyntheticEgoError("notification_matrix_row_count_mismatch")
    if raw["no_real_model_calls"] is not True or raw["no_fallback"] is not True or raw["recorded_only"] is not True:
        raise SyntheticEgoError("notification_matrix_offline_guard_mismatch")
    combos: set[Tuple[str, str]] = set()
    for row in raw["rows"]:
        _expected_keys(
            row,
            (
                "matrix_key",
                "terminal_status",
                "notification_status",
                "capability_state",
                "identity",
                "terminal_revision",
                "fixture_digest",
                "binding_digest",
                "source_manifest_digest",
                "output_manifest_digest",
                "in_app_persistent",
                "in_app_fact_digest",
                "system_copy",
                "channel_evidence",
                "system_attempt_count",
                "navigation_paths",
                "navigation_side_effect_count",
                "run_side_effect_count",
                "real_model_call_count",
                "fallback_attempt_count",
                "recorded_adapter_only",
            ),
            "notification_matrix.row",
        )
        terminal_status = _require_enum(row["terminal_status"], "row.terminal_status", TERMINAL_STATUSES)
        capability_state = _require_enum(row["capability_state"], "row.capability_state", CAPABILITY_STATES)
        expected_notification_status = (
            "analysis_complete" if terminal_status == "complete" else terminal_status
        )
        if row["notification_status"] != expected_notification_status:
            raise SyntheticEgoError("notification_matrix_status_projection_mismatch")
        if row["matrix_key"] != "%s:%s" % (terminal_status, capability_state):
            raise SyntheticEgoError("notification_matrix_key_mismatch")
        combo = (terminal_status, capability_state)
        if combo in combos:
            raise SyntheticEgoError("notification_matrix_duplicate_combo")
        combos.add(combo)
        if row["fixture_digest"] != raw["fixture_digest"]:
            raise SyntheticEgoError("notification_matrix_row_fixture_mismatch")
        _require_sha256_ref(row["binding_digest"], "row.binding_digest")
        _require_sha256_ref(row["source_manifest_digest"], "row.source_manifest_digest")
        _require_sha256_ref(row["output_manifest_digest"], "row.output_manifest_digest")
        _require_sha256_ref(row["in_app_fact_digest"], "row.in_app_fact_digest")
        identity = _require_mapping(row["identity"], "row.identity")
        _expected_keys(identity, ("project_ref", "admission_id", "run_id"), "row.identity")
        for identity_field in ("project_ref", "admission_id", "run_id"):
            _require_id(identity[identity_field], "row.identity.%s" % identity_field)
        _require_id(row["terminal_revision"], "row.terminal_revision")
        if row["in_app_persistent"] is not True or row["recorded_adapter_only"] is not True:
            raise SyntheticEgoError("notification_matrix_persistence_mismatch")
        expected_evidence = "presented" if capability_state == "authorized" else "unknown"
        if row["channel_evidence"] != expected_evidence:
            raise SyntheticEgoError("notification_matrix_channel_evidence_mismatch")
        if row["system_attempt_count"] != (1 if capability_state == "authorized" else 0):
            raise SyntheticEgoError("notification_matrix_attempt_count_mismatch")
        if row["navigation_side_effect_count"] != 2 or row["run_side_effect_count"] != 0:
            raise SyntheticEgoError("notification_matrix_navigation_side_effect_mismatch")
        if row["real_model_call_count"] != 0 or row["fallback_attempt_count"] != 0:
            raise SyntheticEgoError("notification_matrix_real_call_mismatch")
        paths = row["navigation_paths"]
        if not isinstance(paths, list) or len(paths) != 2:
            raise SyntheticEgoError("notification_matrix_navigation_path_count_mismatch")
        intents = []
        for path in paths:
            _expected_keys(path, ("source", "status", "intent"), "row.navigation_path")
            expected_source = (
                "system_notification" if len(intents) == 0 else "in_app_record"
            )
            if path["source"] != expected_source:
                raise SyntheticEgoError("notification_matrix_navigation_source_mismatch")
            if path["status"] != "ok":
                raise SyntheticEgoError("notification_matrix_navigation_blocked")
            intent = _require_mapping(path["intent"], "row.navigation_path.intent")
            _expected_keys(
                intent,
                (
                    "project_ref",
                    "admission_id",
                    "run_id",
                    "terminal_revision",
                    "target_kind",
                    "action",
                ),
                "row.navigation_path.intent",
            )
            expected_intent = {
                "project_ref": identity["project_ref"],
                "admission_id": identity["admission_id"],
                "run_id": identity["run_id"],
                "terminal_revision": row["terminal_revision"],
                "target_kind": _notification.TARGET_KIND_BY_STATUS[expected_notification_status],
                "action": "navigate_only",
            }
            if dict(intent) != expected_intent:
                raise SyntheticEgoError("notification_matrix_navigation_identity_mismatch")
            intents.append(dict(intent))
        if intents[0] != intents[1]:
            raise SyntheticEgoError("notification_matrix_navigation_identity_mismatch")
        system_copy = _require_mapping(row["system_copy"], "row.system_copy")
        if not system_copy.get("title") or not system_copy.get("body"):
            raise SyntheticEgoError("notification_matrix_system_copy_missing")
        _assert_no_path_or_external_literal(system_copy, "notification_matrix.system_copy")
    if combos != {(status, capability) for status in TERMINAL_STATUSES for capability in CAPABILITY_STATES}:
        raise SyntheticEgoError("notification_matrix_combo_coverage_mismatch")

    negative = raw["negative_navigation_cases"]
    if not isinstance(negative, list) or len(negative) != 6:
        raise SyntheticEgoError("notification_matrix_negative_case_count_mismatch")
    expected_negative = {
        "old_revision",
        "binding_drift",
        "source_manifest_drift",
        "output_manifest_drift",
        "target_deleted",
        "target_inaccessible",
    }
    actual_negative = set()
    for row in negative:
        _expected_keys(
            row,
            (
                "case",
                "status",
                "user_message",
                "side_effect_count_before",
                "side_effect_count_after",
                "run_side_effect_count",
                "identity",
                "binding_digest",
            ),
            "negative_navigation_case",
        )
        actual_negative.add(row["case"])
        if row["status"] != "blocked" or row["user_message"] != _notification.NAVIGATION_BLOCKED_MESSAGE:
            raise SyntheticEgoError("notification_matrix_negative_case_not_blocked")
        if row["side_effect_count_before"] != row["side_effect_count_after"]:
            raise SyntheticEgoError("notification_matrix_negative_navigation_side_effect")
        if row["run_side_effect_count"] != 0:
            raise SyntheticEgoError("notification_matrix_negative_run_side_effect")
        _require_sha256_ref(row["binding_digest"], "negative_navigation_case.binding_digest")
    if actual_negative != expected_negative:
        raise SyntheticEgoError("notification_matrix_negative_case_coverage_mismatch")

    _assert_no_path_or_external_literal(raw, "notification_matrix")
    if fixture is not None:
        checked_fixture = validate_synthetic_fixture(fixture)
        if raw["fixture_digest"] != checked_fixture["fixture_digest"]:
            raise SyntheticEgoError("notification_matrix_fixture_digest_mismatch")
    return _copy_json(raw)


def replay_notification_matrix(
    value: Any, *, fixture: Optional[Mapping[str, Any]] = None, strict: bool = False
) -> ReplayResult:
    errors: List[str] = []
    try:
        validate_notification_matrix(value, fixture=fixture)
    except Exception as exc:  # independent replay returns evidence, not a traceback
        errors.append(str(exc))
    result = ReplayResult(valid=not errors, status="passed" if not errors else "failed", errors=tuple(errors))
    if strict and not result.valid:
        raise NotificationMatrixError(errors[0])
    return result


independent_notification_replay = replay_notification_matrix
replay_g6_notification_matrix = replay_notification_matrix


# ---------------------------------------------------------------------------
# Thirteen application-task specifications and post-action evidence recorder
# ---------------------------------------------------------------------------


class SyntheticUserTaskEvidenceRecorder:
    """Record application-visible task steps after explicit user actions."""

    def __init__(self, fixture: Mapping[str, Any], binding: Mapping[str, Any]) -> None:
        self.fixture = validate_synthetic_fixture(fixture)
        self.binding = validate_synthetic_binding(binding, fixture=self.fixture)
        self._active_key: Optional[str] = None
        self._rows: Dict[str, Dict[str, Any]] = {}

    def start_task(self, task_key: str) -> None:
        task_key = _require_text(task_key, "task_key")
        if task_key not in TASK_KEYS:
            raise UserTaskEvidenceError("unknown_task_key:%s" % task_key)
        if self._active_key is not None:
            raise UserTaskEvidenceError("task_already_active")
        if task_key in self._rows:
            raise UserTaskEvidenceError("task_already_recorded:%s" % task_key)
        self._active_key = task_key
        self._rows[task_key] = {"steps": []}

    def record_step(
        self,
        *,
        action: str,
        visible_result: str,
        file_state: Mapping[str, Any],
        restart_required: bool = False,
        negative_assertions: Sequence[str] = (),
    ) -> None:
        if self._active_key is None:
            raise UserTaskEvidenceError("no_active_task")
        action = _require_text(action, "step.action")
        visible_result = _require_text(visible_result, "step.visible_result")
        _require_bool(restart_required, "step.restart_required")
        if not isinstance(file_state, Mapping):
            raise UserTaskEvidenceError("step.file_state_must_be_object")
        if not isinstance(negative_assertions, (list, tuple)):
            raise UserTaskEvidenceError("step.negative_assertions_must_be_list")
        self._rows[self._active_key]["steps"].append(
            {
                "action": action,
                "visible_result": visible_result,
                "file_state": _copy_json(dict(file_state)),
                "restart_required": restart_required,
                "negative_assertions": [str(item) for item in negative_assertions],
            }
        )

    def finish_task(
        self,
        *,
        summary: str,
        restart_points: Sequence[str] = (),
        negative_assertions: Sequence[str] = (),
        cleanup: str,
        file_state_summary: Mapping[str, Any],
        result: str = "passed",
    ) -> None:
        if self._active_key is None:
            raise UserTaskEvidenceError("no_active_task")
        if result != "passed":
            raise UserTaskEvidenceError("required_task_must_pass")
        if not self._rows[self._active_key]["steps"]:
            raise UserTaskEvidenceError("task_has_no_steps")
        if not isinstance(file_state_summary, Mapping):
            raise UserTaskEvidenceError("task_file_state_summary_must_be_object")
        spec = next(item for item in TASK_SPECS if item["key"] == self._active_key)
        task = {
            "index": spec["index"],
            "key": self._active_key,
            "title": spec["title"],
            "initial_state": _copy_json(spec["initial_state"]),
            "steps": self._rows[self._active_key]["steps"],
            "summary": _require_text(summary, "task.summary"),
            "restart_points": [str(item) for item in restart_points],
            "negative_assertions": [str(item) for item in negative_assertions],
            "cleanup": _require_text(cleanup, "task.cleanup"),
            "file_state_summary": _copy_json(dict(file_state_summary)),
            "result": result,
            "identity_preserved": True,
            "fixture_digest": self.fixture["fixture_digest"],
            "binding_digest": self.binding["binding_digest"],
            "task_spec_digest": TASK_SPEC_DIGEST,
            "run_ref": self.binding["run_ref"],
        }
        task["task_digest"] = _digest_without(task, "task_digest")
        self._rows[self._active_key] = task
        self._active_key = None

    def build_manifest(self) -> Dict[str, Any]:
        if self._active_key is not None:
            raise UserTaskEvidenceError("task_still_active")
        if set(self._rows) != set(TASK_KEYS):
            missing = sorted(set(TASK_KEYS) - set(self._rows))
            raise UserTaskEvidenceError("required_tasks_missing:%s" % ",".join(missing))
        tasks = [self._rows[key] for key in TASK_KEYS]
        body: Dict[str, Any] = {
            "schema": USER_TASK_EVIDENCE_SCHEMA,
            "version": USER_TASK_EVIDENCE_VERSION,
            "contract_ref": CONTRACT_REF,
            "contract_version": CONTRACT_VERSION,
            "app_version": self.fixture["app_version"],
            "synthetic_profile_id": self.fixture["synthetic_profile_id"],
            "fixture_digest": self.fixture["fixture_digest"],
            "binding_digest": self.binding["binding_digest"],
            "entry_surface": "actual-app-synthetic",
            "evidence_kind": "application_internal_recorded",
            "synthetic_only": True,
            "offline": True,
            "task_spec_schema": TASK_SPEC_SCHEMA,
            "task_spec_version": TASK_SPEC_VERSION,
            "task_spec_digest": TASK_SPEC_DIGEST,
            "run_ref": self.binding["run_ref"],
            "task_count": len(tasks),
            "tasks": tasks,
            "status": "passed",
            "no_real_model_calls": True,
            "no_fallback": True,
            "execution_required": True,
        }
        body["manifest_digest"] = _digest_without(body, "manifest_digest")
        return validate_user_task_evidence(body, fixture=self.fixture, binding=self.binding)


def build_user_task_specification(
    fixture: Mapping[str, Any], binding: Mapping[str, Any]
) -> Dict[str, Any]:
    """Build required task specifications without claiming user completion."""

    checked_fixture = validate_synthetic_fixture(fixture)
    checked_binding = validate_synthetic_binding(binding, fixture=checked_fixture)
    body: Dict[str, Any] = {
        "schema": USER_TASK_EVIDENCE_SCHEMA,
        "version": USER_TASK_EVIDENCE_VERSION,
        "contract_ref": CONTRACT_REF,
        "contract_version": CONTRACT_VERSION,
        "app_version": checked_fixture["app_version"],
        "synthetic_profile_id": checked_fixture["synthetic_profile_id"],
        "fixture_digest": checked_fixture["fixture_digest"],
        "binding_digest": checked_binding["binding_digest"],
        "entry_surface": "actual-app-synthetic",
        "evidence_kind": "required_task_specification",
        "synthetic_only": True,
        "offline": True,
        "task_spec_schema": TASK_SPEC_SCHEMA,
        "task_spec_version": TASK_SPEC_VERSION,
        "task_spec_digest": TASK_SPEC_DIGEST,
        "run_ref": checked_binding["run_ref"],
        "task_count": len(TASK_SPECS),
        "tasks": [_copy_json(spec) for spec in TASK_SPECS],
        "status": "awaiting_user_actions",
        "no_real_model_calls": True,
        "no_fallback": True,
        "execution_required": True,
    }
    body["manifest_digest"] = _digest_without(body, "manifest_digest")
    return validate_user_task_evidence(body, fixture=checked_fixture, binding=checked_binding)


def build_user_task_evidence(
    fixture: Mapping[str, Any], binding: Mapping[str, Any]
) -> Dict[str, Any]:
    """Compatibility name for the canonical required-task specification."""

    return build_user_task_specification(fixture, binding)


def validate_user_task_evidence(
    value: Mapping[str, Any],
    *,
    fixture: Optional[Mapping[str, Any]] = None,
    binding: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate either a required specification or post-action app evidence."""

    raw = dict(_require_mapping(value, "user_task_evidence"))
    evidence_kind = raw.get("evidence_kind")
    if evidence_kind not in {"required_task_specification", "application_internal_recorded"}:
        raise SyntheticEgoError("user_task_evidence_kind_invalid")
    _expected_keys(
        raw,
        (
            "schema",
            "version",
            "contract_ref",
            "contract_version",
            "app_version",
            "synthetic_profile_id",
            "fixture_digest",
            "binding_digest",
            "entry_surface",
            "evidence_kind",
            "synthetic_only",
            "offline",
            "task_spec_schema",
            "task_spec_version",
            "task_spec_digest",
            "run_ref",
            "task_count",
            "tasks",
            "status",
            "no_real_model_calls",
            "no_fallback",
            "execution_required",
            "manifest_digest",
        ),
        "user_task_evidence",
    )
    if raw["schema"] != USER_TASK_EVIDENCE_SCHEMA or raw["version"] != USER_TASK_EVIDENCE_VERSION:
        raise SyntheticEgoError("user_task_evidence_schema_mismatch")
    if raw["contract_ref"] != CONTRACT_REF or raw["contract_version"] != CONTRACT_VERSION:
        raise SyntheticEgoError("user_task_evidence_contract_mismatch")
    if raw["app_version"] != APP_VERSION or raw["synthetic_profile_id"] != SYNTHETIC_PROFILE_ID:
        raise SyntheticEgoError("user_task_evidence_metadata_mismatch")
    for field in ("fixture_digest", "binding_digest", "task_spec_digest", "manifest_digest"):
        _require_sha256_ref(raw[field], "user_task_evidence.%s" % field)
    if raw["task_spec_schema"] != TASK_SPEC_SCHEMA or raw["task_spec_version"] != TASK_SPEC_VERSION:
        raise SyntheticEgoError("user_task_evidence_task_spec_metadata_mismatch")
    if raw["task_spec_digest"] != TASK_SPEC_DIGEST:
        raise SyntheticEgoError("user_task_evidence_task_spec_digest_mismatch")
    _require_id(raw["run_ref"], "user_task_evidence.run_ref")
    if _digest_without(raw, "manifest_digest") != raw["manifest_digest"]:
        raise SyntheticEgoError("user_task_evidence_manifest_digest_mismatch")
    if raw["entry_surface"] != "actual-app-synthetic":
        raise SyntheticEgoError("user_task_evidence_surface_mismatch")
    if raw["synthetic_only"] is not True or raw["offline"] is not True:
        raise SyntheticEgoError("user_task_evidence_offline_guard_mismatch")
    if (
        raw["no_real_model_calls"] is not True
        or raw["no_fallback"] is not True
        or raw["execution_required"] is not True
    ):
        raise SyntheticEgoError("user_task_evidence_offline_guard_mismatch")
    expected_status = (
        "awaiting_user_actions"
        if evidence_kind == "required_task_specification"
        else "passed"
    )
    if raw["status"] != expected_status:
        raise SyntheticEgoError("user_task_evidence_status_mismatch")
    if (
        not isinstance(raw["task_count"], int)
        or isinstance(raw["task_count"], bool)
        or raw["task_count"] != len(TASK_KEYS)
        or not isinstance(raw["tasks"], list)
        or len(raw["tasks"]) != len(TASK_KEYS)
    ):
        raise SyntheticEgoError("user_task_evidence_task_count_mismatch")

    for index, task_value in enumerate(raw["tasks"], start=1):
        task = _require_mapping(task_value, "user_task_evidence.task")
        spec = TASK_SPECS[index - 1]
        if evidence_kind == "required_task_specification":
            _expected_keys(
                task,
                (
                    "index",
                    "key",
                    "title",
                    "initial_state",
                    "actions",
                    "expected_user_result",
                    "restart_points",
                    "negative_assertions",
                    "cleanup",
                ),
                "user_task_evidence.task_spec",
            )
            if dict(task) != _copy_json(spec):
                raise SyntheticEgoError("user_task_evidence_task_spec_mismatch")
            initial_state = _require_mapping(task["initial_state"], "task.initial_state")
            _expected_keys(initial_state, ("application", "files"), "task.initial_state")
            if not isinstance(initial_state["application"], Mapping) or not isinstance(
                initial_state["files"], Mapping
            ):
                raise SyntheticEgoError("task_initial_state_shape_invalid")
            if not isinstance(task["actions"], list) or not task["actions"]:
                raise SyntheticEgoError("task_action_spec_missing")
            for action in task["actions"]:
                action_map = _require_mapping(action, "task.action")
                _expected_keys(
                    action_map,
                    ("action", "visible_result", "restart_required"),
                    "task.action",
                )
                _require_text(action_map["action"], "task.action.action")
                _require_text(action_map["visible_result"], "task.action.visible_result")
                _require_bool(action_map["restart_required"], "task.action.restart_required")
        else:
            _expected_keys(
                task,
                (
                    "index",
                    "key",
                    "title",
                    "initial_state",
                    "steps",
                    "summary",
                    "restart_points",
                    "negative_assertions",
                    "cleanup",
                    "file_state_summary",
                    "result",
                    "identity_preserved",
                    "fixture_digest",
                    "binding_digest",
                    "task_spec_digest",
                    "run_ref",
                    "task_digest",
                ),
                "user_task_evidence.task",
            )
            if task["index"] != index or task["key"] != TASK_KEYS[index - 1]:
                raise SyntheticEgoError("user_task_evidence_task_order_mismatch")
            if task["title"] != spec["title"] or task["initial_state"] != spec["initial_state"]:
                raise SyntheticEgoError("user_task_evidence_task_initial_state_mismatch")
            if task["summary"] != spec["actions"][-1]["visible_result"]:
                raise SyntheticEgoError("user_task_evidence_summary_mismatch")
            if task["restart_points"] != list(spec["restart_points"]):
                raise SyntheticEgoError("user_task_evidence_restart_points_mismatch")
            if task["negative_assertions"] != list(spec["negative_assertions"]):
                raise SyntheticEgoError("user_task_evidence_negative_assertions_mismatch")
            if task["cleanup"] != spec["cleanup"]:
                raise SyntheticEgoError("user_task_evidence_cleanup_mismatch")
            if task["result"] != "passed" or task["identity_preserved"] is not True:
                raise SyntheticEgoError("user_task_evidence_task_not_passed")
            if (
                task["fixture_digest"] != raw["fixture_digest"]
                or task["binding_digest"] != raw["binding_digest"]
                or task["task_spec_digest"] != raw["task_spec_digest"]
                or task["run_ref"] != raw["run_ref"]
            ):
                raise SyntheticEgoError("user_task_evidence_task_binding_mismatch")
            if not isinstance(task["file_state_summary"], Mapping):
                raise SyntheticEgoError("user_task_evidence_file_state_missing")
            _require_text(task["summary"], "task.summary")
            _require_text(task["cleanup"], "task.cleanup")
            if not isinstance(task["restart_points"], list) or not isinstance(
                task["negative_assertions"], list
            ):
                raise SyntheticEgoError("user_task_evidence_assertion_shape_invalid")
            steps = task["steps"]
            if not isinstance(steps, list) or len(steps) != len(spec["actions"]):
                raise SyntheticEgoError("user_task_evidence_step_count_mismatch")
            for step_index, step_value in enumerate(steps):
                step = _require_mapping(step_value, "user_task_evidence.step")
                _expected_keys(
                    step,
                    (
                        "action",
                        "visible_result",
                        "file_state",
                        "restart_required",
                        "negative_assertions",
                    ),
                    "user_task_evidence.step",
                )
                expected_action = spec["actions"][step_index]
                if (
                    step["action"] != expected_action["action"]
                    or step["visible_result"] != expected_action["visible_result"]
                    or step["restart_required"] is not expected_action["restart_required"]
                    or step["negative_assertions"] != list(spec["negative_assertions"])
                ):
                    raise SyntheticEgoError("user_task_evidence_step_contract_mismatch")
                if not isinstance(step["file_state"], Mapping):
                    raise SyntheticEgoError("user_task_evidence_step_file_state_invalid")
                _require_text(step["action"], "step.action")
                _require_text(step["visible_result"], "step.visible_result")
                _require_bool(step["restart_required"], "step.restart_required")
            _require_sha256_ref(task["fixture_digest"], "task.fixture_digest")
            _require_sha256_ref(task["binding_digest"], "task.binding_digest")
            _require_sha256_ref(task["task_spec_digest"], "task.task_spec_digest")
            _require_id(task["run_ref"], "task.run_ref")
            _require_sha256_ref(task["task_digest"], "task.task_digest")
            if _digest_without(task, "task_digest") != task["task_digest"]:
                raise SyntheticEgoError("user_task_evidence_task_digest_mismatch")

    _assert_no_path_or_external_literal(raw, "user_task_evidence")
    _assert_no_forbidden_task_value(raw, "user_task_evidence")
    if fixture is not None:
        checked_fixture = validate_synthetic_fixture(fixture)
        if raw["fixture_digest"] != checked_fixture["fixture_digest"]:
            raise SyntheticEgoError("user_task_evidence_fixture_digest_mismatch")
    if binding is not None:
        checked_binding = validate_synthetic_binding(binding, fixture=fixture)
        if raw["binding_digest"] != checked_binding["binding_digest"]:
            raise SyntheticEgoError("user_task_evidence_binding_digest_mismatch")
        if raw["run_ref"] != checked_binding["run_ref"]:
            raise SyntheticEgoError("user_task_evidence_run_ref_mismatch")
    return _copy_json(raw)


def replay_user_task_evidence(
    value: Any,
    *,
    fixture: Optional[Mapping[str, Any]] = None,
    binding: Optional[Mapping[str, Any]] = None,
    strict: bool = False,
) -> ReplayResult:
    errors: List[str] = []
    try:
        validate_user_task_evidence(value, fixture=fixture, binding=binding)
    except Exception as exc:  # independent replay returns evidence, not a traceback
        errors.append(str(exc))
    evidence_kind = value.get("evidence_kind") if isinstance(value, Mapping) else None
    result = ReplayResult(
        valid=not errors,
        status=(
            "specification_valid"
            if not errors and evidence_kind == "required_task_specification"
            else "passed"
            if not errors
            else "failed"
        ),
        errors=tuple(errors),
    )
    if strict and not result.valid:
        raise UserTaskEvidenceError(errors[0])
    return result


build_application_task_evidence = build_user_task_evidence
build_synthetic_user_task_evidence = build_user_task_evidence
replay_application_task_evidence = replay_user_task_evidence
independent_user_task_replay = replay_user_task_evidence


# ---------------------------------------------------------------------------
# Bundle and offline CLI
# ---------------------------------------------------------------------------


def _build_run_bindings(fixture: Mapping[str, Any]) -> List[Dict[str, Any]]:
    checked_fixture = validate_synthetic_fixture(fixture)
    return [
        build_synthetic_binding(checked_fixture, project["project_ref"], analysis_mode)
        for project in checked_fixture["projects"]
        for analysis_mode in ANALYSIS_MODES
    ]


def build_synthetic_audience_bundle(
    project_ref: str = "synthetic-project-alpha", analysis_mode: str = "full"
) -> Dict[str, Any]:
    fixture = build_synthetic_fixture()
    run_bindings = _build_run_bindings(fixture)
    binding = build_synthetic_binding(fixture, project_ref, analysis_mode)
    binding_role = (
        "backward_compatible_default_alpha_full"
        if (project_ref, analysis_mode) == ("synthetic-project-alpha", "full")
        else "legacy_selected_run_binding"
    )
    matrix = build_notification_matrix(fixture)
    tasks = build_user_task_evidence(fixture, binding)
    body: Dict[str, Any] = {
        "schema": BUNDLE_SCHEMA,
        "version": BUNDLE_VERSION,
        "contract_ref": CONTRACT_REF,
        "contract_version": CONTRACT_VERSION,
        "app_version": APP_VERSION,
        "synthetic_only": True,
        "offline": True,
        "binding_role": binding_role,
        "run_binding_count": len(run_bindings),
        "fixture": fixture,
        "binding": binding,
        "run_bindings": run_bindings,
        "notification_matrix": matrix,
        "user_task_evidence": tasks,
    }
    body["bundle_digest"] = _digest_without(body, "bundle_digest")
    return body


build_g6_synthetic_bundle = build_synthetic_audience_bundle


def validate_synthetic_audience_bundle(value: Mapping[str, Any]) -> Dict[str, Any]:
    raw = dict(_require_mapping(value, "bundle"))
    _expected_keys(
        raw,
        (
            "schema",
            "version",
            "contract_ref",
            "contract_version",
            "app_version",
            "synthetic_only",
            "offline",
            "binding_role",
            "run_binding_count",
            "fixture",
            "binding",
            "run_bindings",
            "notification_matrix",
            "user_task_evidence",
            "bundle_digest",
        ),
        "bundle",
    )
    if raw["schema"] != BUNDLE_SCHEMA or raw["version"] != BUNDLE_VERSION:
        raise SyntheticEgoError("bundle_schema_mismatch")
    if raw["contract_ref"] != CONTRACT_REF or raw["contract_version"] != CONTRACT_VERSION:
        raise SyntheticEgoError("bundle_contract_mismatch")
    if raw["app_version"] != APP_VERSION or raw["synthetic_only"] is not True or raw["offline"] is not True:
        raise SyntheticEgoError("bundle_boundary_mismatch")
    if raw["binding_role"] not in {
        "backward_compatible_default_alpha_full",
        "legacy_selected_run_binding",
    }:
        raise SyntheticEgoError("bundle_binding_role_mismatch")
    fixture = validate_synthetic_fixture(raw["fixture"])
    expected_pairs = {
        (project["project_ref"], analysis_mode)
        for project in fixture["projects"]
        for analysis_mode in ANALYSIS_MODES
    }
    if raw["run_binding_count"] != len(expected_pairs):
        raise SyntheticEgoError("bundle_run_binding_count_mismatch")
    binding = validate_synthetic_binding(raw["binding"], fixture=fixture)
    selected_pair = (binding["project_ref"], binding["analysis_mode"])
    if (
        raw["binding_role"] == "backward_compatible_default_alpha_full"
        and selected_pair != ("synthetic-project-alpha", "full")
    ):
        raise SyntheticEgoError("bundle_default_binding_mismatch")
    expected_selected_binding = build_synthetic_binding(
        fixture, selected_pair[0], selected_pair[1]
    )
    if binding != expected_selected_binding:
        raise SyntheticEgoError("bundle_selected_binding_direct_mismatch")
    run_bindings_value = raw["run_bindings"]
    if not isinstance(run_bindings_value, list) or len(run_bindings_value) != raw["run_binding_count"]:
        raise SyntheticEgoError("bundle_run_binding_matrix_mismatch")
    actual_pairs = set()
    binding_digests = set()
    for run_binding_value in run_bindings_value:
        run_binding = validate_synthetic_binding(run_binding_value, fixture=fixture)
        pair = (run_binding["project_ref"], run_binding["analysis_mode"])
        if pair in actual_pairs:
            raise SyntheticEgoError("bundle_duplicate_run_binding_pair")
        actual_pairs.add(pair)
        binding_digests.add(run_binding["binding_digest"])
        expected_run_binding = build_synthetic_binding(
            fixture, run_binding["project_ref"], run_binding["analysis_mode"]
        )
        if run_binding != expected_run_binding:
            raise SyntheticEgoError("bundle_run_binding_direct_mismatch")
        if run_binding["profile_binding_digest"] != fixture["profile_binding_digest"]:
            raise SyntheticEgoError("bundle_run_profile_binding_mismatch")
        if run_binding["binding_digest"] == fixture["profile_binding_digest"]:
            raise SyntheticEgoError("bundle_run_binding_not_distinct")
    if actual_pairs != expected_pairs or len(binding_digests) != raw["run_binding_count"]:
        raise SyntheticEgoError("bundle_run_binding_pair_coverage_mismatch")
    selected_matrix_bindings = [
        row
        for row in run_bindings_value
        if (row["project_ref"], row["analysis_mode"]) == selected_pair
    ]
    if len(selected_matrix_bindings) != 1 or selected_matrix_bindings[0] != binding:
        raise SyntheticEgoError("bundle_selected_binding_matrix_mismatch")
    validate_notification_matrix(raw["notification_matrix"], fixture=fixture)
    validate_user_task_evidence(raw["user_task_evidence"], fixture=fixture, binding=binding)
    if _digest_without(raw, "bundle_digest") != raw["bundle_digest"]:
        raise SyntheticEgoError("bundle_digest_mismatch")
    return _copy_json(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline G6 synthetic evidence seams")
    parser.add_argument(
        "artifact",
        choices=("fixture", "binding", "notification-matrix", "user-tasks", "bundle"),
        default="bundle",
        nargs="?",
    )
    parser.add_argument("--project-ref", default="synthetic-project-alpha")
    parser.add_argument("--analysis-mode", choices=ANALYSIS_MODES, default="full")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    fixture = build_synthetic_fixture()
    if args.artifact == "fixture":
        payload: Any = fixture
    elif args.artifact == "binding":
        payload = build_synthetic_binding(fixture, args.project_ref, args.analysis_mode)
    elif args.artifact == "notification-matrix":
        payload = build_notification_matrix(fixture)
    elif args.artifact == "user-tasks":
        binding = build_synthetic_binding(fixture, args.project_ref, args.analysis_mode)
        payload = build_user_task_evidence(fixture, binding)
    else:
        payload = build_synthetic_audience_bundle(args.project_ref, args.analysis_mode)
    print(canonical_json(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
