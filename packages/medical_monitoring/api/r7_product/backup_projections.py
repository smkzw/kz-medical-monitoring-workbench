"""Audience-safe backup and restore projections for the R7 product API."""

from __future__ import annotations

from typing import Any, Mapping

from ...runtime import project_backup as pb

_BACKUP_STATUS_LABEL = {
    pb.STATUS_REQUESTED: "准备中",
    pb.STATUS_RECEIVED: "准备中",
    pb.STATUS_WAITING_FOR_PROJECT: "准备中",
    pb.STATUS_COLLECTING: "正在整理项目",
    pb.STATUS_SNAPSHOTTING: "正在整理项目",
    pb.STATUS_VERIFYING: "正在核对",
    pb.STATUS_PACKAGING: "正在整理项目",
    pb.STATUS_AVAILABLE: "已可下载",
    pb.STATUS_INSPECTING: "正在核对",
    pb.STATUS_VERIFYING_MEMBERS: "正在核对",
    pb.STATUS_RECONCILING_IDENTITY: "正在核对",
    pb.STATUS_READY_FOR_CONFIRMATION: "正在核对",
    pb.STATUS_CONFIRMED: "正在恢复项目",
    pb.STATUS_STAGING: "正在恢复项目",
    pb.STATUS_VERIFYING_STAGED_WORKSPACE: "正在核对",
    pb.STATUS_QUIESCING_PROJECT: "正在恢复项目",
    pb.STATUS_SWITCHING: "正在恢复项目",
    pb.STATUS_VERIFYING_LIVE_WORKSPACE: "正在核对",
    pb.STATUS_COMPLETED: "恢复完成",
    pb.STATUS_ALREADY_CURRENT: "项目已是此版本",
    pb.STATUS_KEPT_CURRENT: "保持原项目未变",
    pb.STATUS_ROLLBACK_IN_PROGRESS: "需要人工处理",
    pb.STATUS_RETAINED_FOR_TRIAGE: "需要人工处理",
    pb.STATUS_FAILED: "未能完成",
}
_BACKUP_STEP_LABEL = {
    pb.STATUS_REQUESTED: "正在准备项目",
    pb.STATUS_RECEIVED: "正在准备项目",
    pb.STATUS_WAITING_FOR_PROJECT: "正在等待项目空闲",
    pb.STATUS_COLLECTING: "正在整理项目",
    pb.STATUS_SNAPSHOTTING: "正在整理项目",
    pb.STATUS_VERIFYING: "正在核对",
    pb.STATUS_PACKAGING: "正在整理项目",
    pb.STATUS_AVAILABLE: "已可下载",
    pb.STATUS_INSPECTING: "正在核对",
    pb.STATUS_VERIFYING_MEMBERS: "正在核对",
    pb.STATUS_RECONCILING_IDENTITY: "正在核对",
    pb.STATUS_READY_FOR_CONFIRMATION: "恢复前检查已完成",
    pb.STATUS_CONFIRMED: "正在恢复项目",
    pb.STATUS_STAGING: "正在恢复项目",
    pb.STATUS_VERIFYING_STAGED_WORKSPACE: "正在核对",
    pb.STATUS_QUIESCING_PROJECT: "正在恢复项目",
    pb.STATUS_SWITCHING: "正在恢复项目",
    pb.STATUS_VERIFYING_LIVE_WORKSPACE: "正在核对",
    pb.STATUS_COMPLETED: "恢复完成",
    pb.STATUS_ALREADY_CURRENT: "恢复完成",
    pb.STATUS_KEPT_CURRENT: "等待恢复确认",
    pb.STATUS_ROLLBACK_IN_PROGRESS: "需要人工处理",
    pb.STATUS_RETAINED_FOR_TRIAGE: "需要人工处理",
    pb.STATUS_FAILED: "未能完成",
}
_BACKUP_IMPACT_LABEL = {
    "runs": "监查运行",
    "publications": "结果发布",
    "risk_rules": "风险规则",
    "continuity_plans": "连续性计划",
}


def _backup_payload_manifest(record: pb.OperationRecord) -> Mapping[str, Any]:
    payload = record.payload
    if not isinstance(payload, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    manifest = payload.get("manifest", {})
    if manifest is None:
        return {}
    if not isinstance(manifest, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    return manifest


def _backup_progress(record: pb.OperationRecord) -> int:
    value = record.progress_percent
    if isinstance(value, bool) or not isinstance(value, int):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    return max(0, min(100, value))


def _backup_text(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if not isinstance(value, str) or not value.strip():
        return fallback
    return value


def _backup_scope_summary(manifest: Mapping[str, Any]) -> str:
    summary = manifest.get("project_summary", {})
    if not isinstance(summary, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    counts = summary.get("counts", {})
    if not isinstance(counts, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    runs = counts.get("runs", 0)
    if isinstance(runs, bool) or not isinstance(runs, int) or runs < 0:
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    return f"已整理 {runs} 次监查运行" if runs else "已整理当前项目监查资料"


def _public_backup_projection(
    record: pb.OperationRecord,
    canonical_project_id: str,
) -> dict[str, Any]:
    status = str(record.status)
    if status not in _BACKUP_STATUS_LABEL:
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    manifest = _backup_payload_manifest(record)
    summary = manifest.get("project_summary", {})
    if summary is not None and not isinstance(summary, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    project_name = _backup_text(
        manifest.get("project_name") if manifest else None,
        canonical_project_id,
    )
    cutoff = _backup_text(
        manifest.get("backup_cutoff") if manifest else None,
        "尚未建立监查运行",
    )
    body: dict[str, Any] = {
        "operation_id": record.operation_id,
        "status_label": _BACKUP_STATUS_LABEL[status],
        "project_name": project_name,
        "backup_cutoff_label": cutoff,
        "monitoring_scope_summary": _backup_scope_summary(manifest),
        "recommended_next_action": (
            "下载备份文件"
            if status == pb.STATUS_AVAILABLE
            else "请稍后重试"
            if status == pb.STATUS_FAILED
            else "请查看备份进度"
        ),
        "progress_percent": _backup_progress(record),
        "current_step_label": _BACKUP_STEP_LABEL[status],
    }
    if isinstance(summary, Mapping) and summary.get("unfinished_work"):
        body["unfinished_work_notice"] = (
            "此备份包含未完成的监查任务，恢复后仍需继续处理"
        )
    return body


def _public_impact_items(value: Any) -> dict[str, int]:
    if value is None:
        value = {}
    if not isinstance(value, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    result: dict[str, int] = {}
    for key, label in _BACKUP_IMPACT_LABEL.items():
        count = value.get(key, 0)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise pb.ProjectBackupError("sqlite_integrity_failed")
        result[label] = count
    return result


def _public_preflight_projection(
    result: pb.PreflightResult,
    backup_operation_id: str,
) -> dict[str, Any]:
    items_rolled_back = _public_impact_items(result.items_rolled_back)
    impact_summary = (
        "无预计回退事项"
        if not any(items_rolled_back.values())
        else "、".join(
            f"{label} {count} 项"
            for label, count in items_rolled_back.items()
            if count
        )
    )
    operation = result.operation
    status = str(operation.status)
    step = _BACKUP_STEP_LABEL.get(status, "正在核对")
    body: dict[str, Any] = {
        "operation_id": result.operation_id,
        "backup_operation_id": backup_operation_id,
        "decision_label": result.decision_label,
        "backup_project_name": result.project_name,
        "backup_cutoff_label": result.backup_cutoff_label,
        "current_cutoff_label": result.current_cutoff_label,
        "impact_summary": impact_summary,
        "items_preserved": list(result.items_preserved),
        "items_rolled_back": items_rolled_back,
        "recommended_action": result.recommended_action,
        "confirmation_required": bool(result.confirmation_required),
        "unfinished_work_notice": (
            result.unfinished_work_notice or ""
        ),
        "progress_percent": _backup_progress(operation),
        "current_step_label": step,
    }
    return body


def _public_restore_projection(
    record: pb.OperationRecord,
    canonical_project_id: str,
) -> dict[str, Any]:
    status = str(record.status)
    if status not in _BACKUP_STATUS_LABEL:
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    payload = record.payload
    if not isinstance(payload, Mapping):
        raise pb.ProjectBackupError("sqlite_integrity_failed")
    if status == pb.STATUS_COMPLETED:
        result_label = "恢复完成"
    elif status == pb.STATUS_ALREADY_CURRENT:
        result_label = "项目已是此版本"
    elif status == pb.STATUS_KEPT_CURRENT:
        result_label = "保持原项目未变"
    elif status in {
        pb.STATUS_RETAINED_FOR_TRIAGE,
        pb.STATUS_ROLLBACK_IN_PROGRESS,
        pb.STATUS_FAILED,
    }:
        result_label = "需要人工处理"
    else:
        result_label = "正在恢复项目"
    return {
        "operation_id": record.operation_id,
        "result_label": result_label,
        "project_name": _backup_text(
            payload.get("project_name"), canonical_project_id
        ),
        "restored_cutoff_label": _backup_text(
            payload.get("restored_cutoff_label"), "当前项目尚未建立"
        ),
        "verification_summary": _backup_text(
            payload.get("verification_summary"),
            "项目恢复尚未完成，请稍后核对",
        ),
        "next_action_label": _backup_text(
            payload.get("next_action_label"),
            "请稍后核对项目状态",
        ),
        "progress_percent": _backup_progress(record),
        "current_step_label": _BACKUP_STEP_LABEL[status],
    }

__all__ = [
    "_BACKUP_STATUS_LABEL",
    "_BACKUP_STEP_LABEL",
    "_BACKUP_IMPACT_LABEL",
    "_backup_payload_manifest",
    "_backup_progress",
    "_backup_text",
    "_backup_scope_summary",
    "_public_backup_projection",
    "_public_impact_items",
    "_public_preflight_projection",
    "_public_restore_projection",
]

