"""Read-only legacy and execution projections for the R7 product API."""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional

from ...runtime import launch_registry as lr
from ...runtime import profile_store as ps
from ...runtime import run_setup as rs
from ...runtime.project_lifecycle import ReadOnlyProjectView
from ...runtime.run_entry import RunEntryError
from ...runtime.runtime_progress import RuntimeProgressError, validate_public_data_cutoff
from .public_text import _RUNTIME_INTERNAL_TOKENS, _SECRET_VALUE, _projection
from .result_projections import _publication_status_text


def _legacy_profile_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Rebuild the existing public profile shape without opening a store."""
    payload = row.get("payload_json")
    if not isinstance(payload, Mapping):
        raise RunEntryError("internal_error")
    try:
        validated_row = dict(row)
        validated_row["payload_json"] = ps.canonical_json_bytes(
            payload
        ).decode("utf-8")
        record = ps._row_to_record(validated_row)
        return _projection(ps.public_projection(record))
    except Exception as exc:
        raise RunEntryError("internal_error") from exc


def _legacy_binding_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return the binding's bounded public fields from a read-only row."""
    body = {
        "run_id": row.get("run_id"),
        "project_id": row.get("project_id"),
        "mode": row.get("mode"),
        "execution_basis": row.get("execution_basis"),
        "data_cutoff": row.get("data_cutoff"),
        "source_revision_id": row.get("source_revision_id"),
        "prior_accepted_snapshot_ref": row.get("prior_accepted_snapshot_ref"),
        "user_config_name": row.get("user_config_name"),
        "adapter_id": row.get("adapter_id"),
        "adapter_version": row.get("adapter_version"),
        "schema_version": row.get("schema_version"),
    }
    if any(value is None for value in body.values()):
        raise RunEntryError("internal_error")
    return _projection(body)


def _legacy_launch_record(row: Mapping[str, Any]) -> lr.LaunchRecord:
    """Materialize an immutable public-history record from a read-only row."""
    raw_rule_tokens = row.get("rule_tokens_json", ())
    if raw_rule_tokens is None:
        raw_rule_tokens = ()
    if not isinstance(raw_rule_tokens, (list, tuple)):
        raise lr.LaunchRegistryError("store_closed")
    try:
        return lr.LaunchRecord(
            sequence=int(row.get("sequence", 0)),
            project_id=str(row.get("project_id", "")),
            idempotency_key=str(row.get("idempotency_key", "")),
            run_id=str(row.get("run_id", "")),
            public_run_token=str(row.get("public_run_token", "")),
            request_fingerprint=str(row.get("request_fingerprint", "")),
            mode=str(row.get("mode", "")),
            execution_basis=str(row.get("execution_basis", "")),
            current_snapshot_token=str(row.get("current_snapshot_token", "")),
            baseline_token=(
                None
                if row.get("baseline_token") is None
                else str(row.get("baseline_token"))
            ),
            rule_tokens=tuple(str(value) for value in raw_rule_tokens),
            data_cutoff=str(row.get("data_cutoff", "")),
            comparison_range_text=str(row.get("comparison_range_text", "")),
            run_state=str(row.get("run_state", "")),
            result_available=bool(row.get("result_available", False)),
            main_action=str(row.get("main_action", "")),
            manifest_digest=(
                None
                if row.get("manifest_digest") is None
                else str(row.get("manifest_digest"))
            ),
            created_at=str(row.get("created_at", "")),
            updated_at=str(row.get("updated_at", "")),
        )
    except (TypeError, ValueError, KeyError) as exc:
        raise lr.LaunchRegistryError("store_closed") from exc


def _legacy_risk_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return the same bounded rule-revision projection as the live registry."""
    try:
        body = {
            "project_id": str(row["project_id"]),
            "revision": int(row["revision"]),
            "revision_token": str(row["revision_token"]),
            "summary": str(row["summary"]),
            "applicable_scope": str(row["applicable_scope"]),
            "starting_run": str(row["starting_run"]),
            "selectable": bool(row["selectable"]),
            "created_at": str(row["created_at"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise rs.RunSetupError("risk_rule_not_found") from exc
    return _setup_projection(body)


def _legacy_progress_projection(
    view: ReadOnlyProjectView,
    run_id: str,
    launch: Optional[lr.LaunchRecord],
) -> dict[str, Any]:
    """Project legacy execution rows without opening the mutable runtime."""
    bindings = [
        row for row in view.list_run_bindings()
        if row.get("run_id") == run_id
    ]
    if not bindings:
        raise RuntimeProgressError("run_binding_not_found")
    binding = bindings[0]
    runtime_rows = [
        row for row in view.list_monitoring_runs()
        if row.get("run_id") == run_id
    ]
    if not runtime_rows:
        raise RuntimeProgressError("execution_not_prepared")
    work_rows = list(view.list_work_unit_runs(run_id))
    status_order = (
        "pending",
        "running",
        "passed",
        "reused",
        "skipped",
        "not_applicable",
        "blocked",
        "failed",
    )
    if any(str(row.get("status")) not in status_order for row in work_rows):
        raise RuntimeProgressError("runtime_integrity_failed")
    counts = {
        status: sum(1 for row in work_rows if str(row.get("status")) == status)
        for status in status_order
    }
    total = len(work_rows)
    completed = sum(
        counts[status]
        for status in status_order
        if status not in {"pending", "running"}
    )
    percent = round((completed * 100.0 / total), 2) if total else 0.0
    state = launch.run_state if launch is not None else ""
    if state not in lr.RUN_STATE_VALUES:
        if counts["running"]:
            state = lr.STATE_RUNNING
        elif total and completed == total:
            state = lr.STATE_COMPLETED
        else:
            state = lr.STATE_WAITING_START
    mode_text = {
        lr.MODE_DAILY: "日常监查",
        lr.MODE_PRE_LOCK: "锁库前监查",
        lr.MODE_POST_LOCK_PRE_CFDI: "核查前监查",
    }.get(str(binding.get("mode")), "本次监查")
    basis_text = {
        lr.BASIS_FULL: "全面分析",
        lr.BASIS_INCREMENTAL: "增量比较",
    }.get(str(binding.get("execution_basis")), "本次分析")
    status_text = {
        lr.STATE_WAITING_START: "等待开始医学监查",
        lr.STATE_RUNNING: "医学监查进行中",
        lr.STATE_STOPPING: "正在停止医学监查",
        lr.STATE_INTERRUPTED_RESUMABLE: "已停止，可继续",
        lr.STATE_COMPLETED: "本次医学监查已完成",
        lr.STATE_ENDED_INCOMPLETE: "本次监查已结束，部分工作未完成",
        lr.STATE_FAILED: "本次监查未完成",
    }[state]
    publication_rows = list(view.list_publications(run_id=run_id))
    publication_state = (
        str(publication_rows[0].get("publication_state", ""))
        if publication_rows
        else "not_started"
    )
    if publication_state not in lr.PUBLICATION_STATE_VALUES and publication_state != "not_started":
        publication_state = lr.PUBLICATION_STATE_RECOVERABLE_FAILED
    if state == lr.STATE_COMPLETED and publication_state != lr.PUBLICATION_STATE_AVAILABLE:
        headline = "分析已结束，结果整理未完成"
    elif state == lr.STATE_COMPLETED:
        headline = "本次医学监查已完成"
    elif state == lr.STATE_RUNNING:
        headline = "医学监查进行中"
    elif state == lr.STATE_WAITING_START:
        headline = "等待开始医学监查"
    else:
        headline = status_text
    actions = {
        lr.STATE_WAITING_START: ["开始"],
        lr.STATE_RUNNING: ["停止"],
        lr.STATE_INTERRUPTED_RESUMABLE: ["继续"],
    }.get(state, [])
    if state == lr.STATE_COMPLETED:
        if publication_state == "not_started":
            actions = ["整理结果"]
        elif publication_state in {
            lr.PUBLICATION_STATE_RECOVERABLE_FAILED,
            lr.PUBLICATION_STATE_BLOCKED,
        }:
            actions = ["重新整理"]
    status_labels = {
        "pending": "等待开始",
        "running": "进行中",
        "passed": "已完成",
        "reused": "已沿用已有结果",
        "skipped": "本次无需处理",
        "not_applicable": "本研究不适用",
        "blocked": "暂时受阻",
        "failed": "未完成",
    }
    status_overview = [
        {"state_label": status_labels[status], "count": counts[status]}
        for status in status_order
        if counts[status]
    ]
    manifest_revision = max(
        [int(row.get("manifest_revision", 0)) for row in work_rows]
        + [int(runtime_rows[0].get("manifest_revision", 0))],
    )
    cutoff = validate_public_data_cutoff(binding.get("data_cutoff"))
    return {
        "scope_version_text": f"第 {manifest_revision} 版监查范围",
        "mode_text": mode_text,
        "basis_text": basis_text,
        "data_cutoff_text": cutoff,
        "headline": headline,
        "completed": completed,
        "total": total,
        "percent": float(percent),
        "progress_text": f"已处理 {completed}/{total} 项（{float(percent):g}%）",
        "status_overview": status_overview,
        "stage_progress": [],
        "current_work": [],
        "latest_updates": [],
        "run_status_text": status_text,
        "available_actions": actions,
        "run_state": state,
        "publication_state": publication_state,
        "result_available": publication_state == lr.PUBLICATION_STATE_AVAILABLE,
        "publication_status_text": _publication_status_text(
            publication_state,
            run_state=state,
        ),
    }


def _execution_action_projection(result: Any) -> dict[str, Any]:
    """Keep start/resume/stop responses to the product-safe overlay only."""
    expected = {"replayed", "run_status_text", "available_actions"}
    if not isinstance(result, Mapping) or set(result) != expected:
        raise RunEntryError("internal_error")
    if not isinstance(result["replayed"], bool):
        raise RunEntryError("internal_error")
    status_text = result["run_status_text"]
    actions = result["available_actions"]
    if (
        not isinstance(status_text, str)
        or not status_text.strip()
        or not any("\u4e00" <= char <= "\u9fff" for char in status_text)
        or not isinstance(actions, list)
        or any(
            not isinstance(action, str)
            or not action.strip()
            or not any("\u4e00" <= char <= "\u9fff" for char in action)
            for action in actions
        )
    ):
        raise RunEntryError("internal_error")
    blob = json.dumps(result, ensure_ascii=False).casefold()
    if _SECRET_VALUE.search(blob) or any(token in blob for token in _RUNTIME_INTERNAL_TOKENS):
        raise RunEntryError("internal_error")
    return dict(result)


def _safe_setup_projection(value: Any, *, key: str = "") -> Any:
    """Project opaque setup tokens without exposing internal rule identity."""
    if isinstance(value, Mapping):
        return {
            item_key: _safe_setup_projection(item, key=str(item_key))
            for item_key, item in value.items()
        }
    if isinstance(value, list):
        return [_safe_setup_projection(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_setup_projection(item) for item in value]
    if key == "revision_token" and isinstance(value, str):
        return rs.public_revision_token(value)
    return value


def _setup_projection(result: Any) -> dict[str, Any]:
    return _projection(_safe_setup_projection(result))


def _runtime_work_units(manifest: rs.WorkUnitManifest) -> list[dict[str, Any]]:
    """Adapt setup labels to the established R1 audience work-unit shape."""
    stage_text = {
        "common": "通用检查",
        rs.MODE_DAILY: "日常监查",
        rs.MODE_PRE_LOCK: "锁库前监查",
        rs.MODE_POST_LOCK_PRE_CFDI: "核查前监查",
        "daily_diff": "数据变化",
        "special_risk_rule": "特殊关注",
    }
    units: list[dict[str, Any]] = []
    for unit in manifest:
        label = (
            unit.label.replace("/", "、").replace("\\", "、")
            if any("\u4e00" <= char <= "\u9fff" for char in unit.label)
            else f"监查：{unit.label}"
        )
        if unit.stage == "special_risk_rule":
            revision_text = unit.target_ref.rsplit(":", 1)[-1]
            if revision_text.isdigit():
                label = f"{label}（已确认规则第 {revision_text} 版）"
        units.append(
            {
                **unit.as_dict(),
                "stage": stage_text.get(unit.stage, "监查检查"),
                "scope": "project",
                "target_ref": label,
                "label": label,
            }
        )
    return units


__all__ = [
    "_legacy_profile_projection",
    "_legacy_binding_projection",
    "_legacy_launch_record",
    "_legacy_risk_projection",
    "_legacy_progress_projection",
    "_execution_action_projection",
    "_safe_setup_projection",
    "_setup_projection",
    "_runtime_work_units",
]
