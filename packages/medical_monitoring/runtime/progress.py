"""Chinese, read-only progress projection for medical monitors.

The authoritative Store intentionally retains execution identities and immutable
transition metadata.  This module is the audience boundary: it conserves the
validated denominator and outcomes while emitting only clinical work language.
It never returns raw runtime details, identifiers or audit fields.
"""

from __future__ import annotations

import datetime
import re
from collections import Counter, OrderedDict
from collections.abc import Mapping, Sequence
from typing import Any
from zoneinfo import ZoneInfo

from ..domain.execution import (
    TERMINAL_NODE_STATUSES,
    ExecutionManifest,
    ManifestWorkUnit,
    MmR1Error,
    NodeStatus,
    WorkUnitRun,
)


class AudienceProgressError(MmR1Error):
    """Raised when an authoritative progress view is unsafe to show."""


_STATUS_LABELS = {
    NodeStatus.PENDING: "等待开始",
    NodeStatus.RUNNING: "进行中",
    NodeStatus.PASSED: "已完成",
    NodeStatus.REUSED: "已沿用已有结果",
    NodeStatus.SKIPPED: "本次无需处理",
    NodeStatus.NOT_APPLICABLE: "本研究不适用",
    NodeStatus.BLOCKED: "暂时受阻",
    NodeStatus.FAILED: "未完成",
}

_SCOPE_LABELS = {
    "subject": "受试者",
    "site": "研究中心",
    "project": "研究项目",
    "risk_domain": "风险维度",
    "visit": "访视",
    "source": "源资料",
    "document": "研究资料",
    "report_section": "报告章节",
    "qc": "质量检查",
}

_FORBIDDEN_TEXT = (
    "正式事实",
    "候选信号",
    "只读",
    "后端",
    "执行身份",
    "尝试编号",
    "节点编号",
    "工作单元",
    "哈希",
    "审计序号",
    "运行编号",
    "模型选择",
    "日志",
    "execution_identity",
    "work_unit",
    "work unit",
    "manifest_revision",
    "denominator_hash",
    "event_type",
    "raw_log",
)
_FORBIDDEN_WORDS = re.compile(
    r"(?i)(?<![a-z0-9])"
    r"(?:provider|model|selector|attempt|backend|node|run|binding|audit|log|hash|"
    r"runtime|transport|endpoint|manifest|revision|api|url|raw|sql|cache|token|"
    r"session|pid)"
    r"(?:[_-]?[a-z0-9]+)*(?![a-z0-9])"
)
_INTERNAL_ID = re.compile(
    r"(?i)(?:^|[^a-z0-9])"
    r"(?:run|node|attempt|binding|work[-_]?unit|wu)-[a-z0-9_-]+"
)
_UUID = re.compile(
    r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
)
_LONG_HEX = re.compile(r"(?i)\b[0-9a-f]{32,}\b")
_TECHNICAL_URI = re.compile(
    r"(?i)(?:[a-z][a-z0-9+.-]{0,31}://|"
    r"(?<![a-z0-9])[a-z][a-z0-9+.-]{0,31}:)"
)
_CLINICAL_COLON_PREFIX = re.compile(
    r"(?<![A-Za-z0-9])(?:AE|SAE|MH|CM|IP|PD|ALT|AST|ALP|GGT|TBIL|DBIL|"
    r"ECG|QTCF|QTCB|PK):(?=\s*[\u3400-\u9fffA-Z0-9])"
)
_ABSOLUTE_PATH = re.compile(
    r"(?i)(?<![a-z0-9])(?:/|~/|\.\.?/|[a-z]:[\\/])"
)
_LOWERCASE_RELATIVE_PATH = re.compile(
    r"(?<![A-Za-z0-9])(?:[a-z][a-z0-9._-]*/)+[a-z][a-z0-9._-]*"
    r"(?![A-Za-z0-9])"
)
_FILE_SUFFIX = re.compile(
    r"(?i)(?:^|[/\\\s])[^/\\\s]+\."
    r"(?:csv|tsv|json|jsonl|sqlite|sqlite3|db|log|txt|ya?ml|py|js|mjs|md|"
    r"xlsx?|docx?|pdf|exe|tmp|sh|zsh|bash|bin|dylib|so|zip|tar|gz|parquet|"
    r"feather)(?:$|[?#\s),;])"
)
_NETWORK_ADDRESS = re.compile(
    r"(?i)(?:(?<![a-z0-9])localhost(?![a-z0-9])|"
    r"(?<![0-9.])(?:\d{1,3}\.){3}\d{1,3}(?![0-9.])(?::\d{2,5})?|"
    r"\[[0-9a-f:]+\](?::\d{2,5})?|"
    r"(?<![a-z0-9])(?:[0-9a-f]{0,4}:){2,}[0-9a-f:]+|"
    r"(?<![a-z0-9])(?:[a-z0-9-]+\.)+[a-z]{2,}(?![a-z0-9])"
    r"(?::\d{2,5})?)"
)
_CHINESE = re.compile(r"[\u3400-\u9fff]")
_CLINICAL_TARGET_ID = re.compile(
    r"[A-Z0-9][A-Z0-9._/-]*(?: [A-Z0-9][A-Z0-9._/-]*)*"
)
_TECHNICAL_TARGET_SEGMENTS = frozenset(
    {
        "ASSETS",
        "BIN",
        "BUILD",
        "CACHE",
        "CONFIG",
        "DATA",
        "DIST",
        "DOCS",
        "ETC",
        "HOME",
        "LIB",
        "MM",
        "OPT",
        "POC",
        "PRIVATE",
        "README",
        "SETUP",
        "SRC",
        "TEST",
        "TESTS",
        "TMP",
        "USERS",
        "VAR",
    }
)


def _audience_text(value: Any, field: str, *, require_chinese: bool) -> str:
    if not isinstance(value, str):
        raise AudienceProgressError(f"{field} 不是可展示文字")
    text = " ".join(value.split())
    if not text:
        raise AudienceProgressError(f"{field} 不能为空")
    max_length = 40 if field == "阶段" else 160
    if len(text) > max_length:
        raise AudienceProgressError(f"{field} 超出展示长度")
    lowered = text.casefold()
    if any(token.casefold() in lowered for token in _FORBIDDEN_TEXT):
        raise AudienceProgressError(f"{field} 含内部工作标识")
    if _FORBIDDEN_WORDS.search(text) or _INTERNAL_ID.search(text):
        raise AudienceProgressError(f"{field} 含内部执行标识")
    if _UUID.search(text) or _LONG_HEX.search(text):
        raise AudienceProgressError(f"{field} 含不可展示的内部编号")
    address_text = _CLINICAL_COLON_PREFIX.sub("", text)
    if (
        "/Users/" in text
        or _TECHNICAL_URI.search(address_text)
        or _ABSOLUTE_PATH.search(text)
        or _LOWERCASE_RELATIVE_PATH.search(text)
        or _FILE_SUFFIX.search(text)
        or _NETWORK_ADDRESS.search(text)
        or "\\" in text
    ):
        raise AudienceProgressError(f"{field} 含不可展示的技术地址")
    text_segments = {
        segment for segment in re.split(r"[ ./\\_-]+", text.upper()) if segment
    }
    if text_segments & _TECHNICAL_TARGET_SEGMENTS:
        raise AudienceProgressError(f"{field} 含不可展示的技术目录")
    if require_chinese and not _CHINESE.search(text):
        raise AudienceProgressError(f"{field} 必须使用中文医学监查表达")
    return text


def _target_view(unit: ManifestWorkUnit) -> dict[str, str]:
    if unit.scope not in _SCOPE_LABELS:
        raise AudienceProgressError("工作范围类型不可展示")
    target = _audience_text(unit.target_ref, "对象", require_chinese=False)
    if not _CHINESE.search(target) and (
        _CLINICAL_TARGET_ID.fullmatch(target) is None
        or not any(character.isdigit() for character in target)
    ):
        raise AudienceProgressError("对象必须使用中文名称或带编号的临床标识")
    return {"scope_label": _SCOPE_LABELS[unit.scope], "target": target}


def _elapsed_text(seconds: Any) -> str:
    if isinstance(seconds, bool) or not isinstance(seconds, int) or seconds < 0:
        raise AudienceProgressError("当前工作时长无效")
    if seconds < 60:
        return "刚刚开始"
    minutes = seconds // 60
    if minutes < 60:
        return f"已进行 {minutes} 分钟"
    hours, remainder = divmod(minutes, 60)
    if remainder:
        return f"已进行 {hours} 小时 {remainder} 分钟"
    return f"已进行 {hours} 小时"


def _time_text(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise AudienceProgressError("工作动态时间无效")
    try:
        parsed = datetime.datetime.fromisoformat(value)
    except ValueError as exc:
        raise AudienceProgressError("工作动态时间无效") from exc
    if parsed.tzinfo is None:
        raise AudienceProgressError("工作动态时间缺少时区")
    local = parsed.astimezone(ZoneInfo("Asia/Shanghai"))
    return local.strftime("%m月%d日 %H:%M")


def _overall_state(counts: Mapping[NodeStatus, int], completed: int, total: int) -> str:
    if counts.get(NodeStatus.RUNNING, 0):
        return "医学监查进行中"
    if completed == total and total:
        if counts.get(NodeStatus.FAILED, 0) or counts.get(NodeStatus.BLOCKED, 0):
            return "本次监查已结束，部分工作未完成"
        return "本次医学监查已完成"
    if completed == 0:
        return "等待开始医学监查"
    return "医学监查准备继续"


def _event_message(event_type: str, status: NodeStatus, label: str) -> str:
    if event_type == "work_unit_begin":
        if status != NodeStatus.RUNNING:
            raise AudienceProgressError("开始动态状态不可展示")
        return f"开始处理：{label}"
    if event_type == "work_unit_attempt_bound":
        if status != NodeStatus.RUNNING:
            raise AudienceProgressError("继续处理动态状态不可展示")
        return f"正在继续处理：{label}"
    if event_type != "work_unit_complete":
        raise AudienceProgressError("工作动态类型不可展示")
    prefix = {
        NodeStatus.PASSED: "已完成",
        NodeStatus.REUSED: "已沿用已有结果",
        NodeStatus.SKIPPED: "本次无需处理",
        NodeStatus.NOT_APPLICABLE: "本研究不适用",
        NodeStatus.BLOCKED: "暂时受阻",
        NodeStatus.FAILED: "未完成",
    }.get(status)
    if prefix is None:
        raise AudienceProgressError("工作动态状态不可展示")
    return f"{prefix}：{label}"


def _validated_authoritative_state(
    manifest: ExecutionManifest,
    rows: Sequence[WorkUnitRun],
    source: Mapping[str, Any],
) -> tuple[list[ManifestWorkUnit], dict[str, WorkUnitRun], Counter[NodeStatus]]:
    if not manifest.work_units:
        raise AudienceProgressError("当前批次缺少可展示的工作明细")
    units = sorted(manifest.work_units, key=lambda item: item.ordinal)
    row_by_id = {row.work_unit_id: row for row in rows}
    if len(row_by_id) != len(rows) or set(row_by_id) != {
        unit.work_unit_id for unit in units
    }:
        raise AudienceProgressError("工作进度与本次监查范围不一致")
    counts: Counter[NodeStatus] = Counter(row.status for row in rows)
    source_counts = source.get("by_status")
    expected_counts = {status.value: count for status, count in counts.items()}
    if source_counts != expected_counts:
        raise AudienceProgressError("工作进度分类与权威记录不一致")
    completed = sum(counts.get(status, 0) for status in TERMINAL_NODE_STATUSES)
    if source.get("completed") != completed or source.get("total") != len(units):
        raise AudienceProgressError("总体进度与权威记录不一致")
    return units, row_by_id, counts


def project_audience_progress(
    store: Any,
    run_id: str,
    *,
    feed_limit: int = 20,
) -> dict[str, Any]:
    """Return the current audience view without mutating the Store.

    ``store.structured_progress`` remains the authority and performs the
    ledger/audit reconciliation.  Internal keys are used only to join that
    validated view to the frozen manifest; none are returned.
    """

    source = store.structured_progress(run_id, feed_limit=feed_limit)
    if not isinstance(source, Mapping):
        raise AudienceProgressError("权威进度格式无效")
    if source.get("is_current_revision") is not True:
        raise AudienceProgressError("当前展示不是最新监查进度")
    revision = source.get("manifest_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision <= 0:
        raise AudienceProgressError("本次监查范围版本无效")
    manifest = store.get_manifest(run_id, revision)
    if manifest is None:
        raise AudienceProgressError("本次监查范围不可用")
    rows = store.list_work_unit_runs(run_id, revision)
    units, row_by_id, counts = _validated_authoritative_state(manifest, rows, source)

    safe_units: dict[str, dict[str, Any]] = {}
    for unit in units:
        safe_units[unit.work_unit_id] = {
            "stage": _audience_text(unit.stage, "阶段", require_chinese=True),
            "label": _audience_text(unit.label, "工作说明", require_chinese=True),
            **_target_view(unit),
        }

    stages: OrderedDict[str, list[ManifestWorkUnit]] = OrderedDict()
    for unit in units:
        stages.setdefault(safe_units[unit.work_unit_id]["stage"], []).append(unit)
    stage_progress: list[dict[str, Any]] = []
    for stage, stage_units in stages.items():
        processed = sum(
            row_by_id[unit.work_unit_id].status in TERMINAL_NODE_STATUSES
            for unit in stage_units
        )
        stage_progress.append(
            {
                "stage": stage,
                "processed": processed,
                "total": len(stage_units),
                "progress_text": f"已处理 {processed}/{len(stage_units)} 项",
            }
        )

    running_source = source.get("running")
    if not isinstance(running_source, list):
        raise AudienceProgressError("当前工作记录无效")
    running_by_id: dict[str, Mapping[str, Any]] = {}
    for item in running_source:
        if not isinstance(item, Mapping) or not isinstance(
            item.get("work_unit_id"), str
        ):
            raise AudienceProgressError("当前工作记录无效")
        if item["work_unit_id"] in running_by_id:
            raise AudienceProgressError("当前工作记录重复")
        running_by_id[item["work_unit_id"]] = item
    expected_running = {
        row.work_unit_id for row in rows if row.status == NodeStatus.RUNNING
    }
    if set(running_by_id) != expected_running:
        raise AudienceProgressError("当前工作与权威记录不一致")
    current_work: list[dict[str, Any]] = []
    for unit in units:
        running = running_by_id.get(unit.work_unit_id)
        if running is None:
            continue
        safe = safe_units[unit.work_unit_id]
        current_work.append(
            {
                **safe,
                "state_label": _STATUS_LABELS[NodeStatus.RUNNING],
                "elapsed_text": _elapsed_text(running.get("elapsed_seconds")),
                "message": f"正在进行：{safe['label']}",
            }
        )

    feed_source = source.get("feed")
    if not isinstance(feed_source, list):
        raise AudienceProgressError("工作动态记录无效")
    latest_updates: list[dict[str, Any]] = []
    for event in feed_source:
        if not isinstance(event, Mapping):
            raise AudienceProgressError("工作动态记录无效")
        unit_id = event.get("work_unit_id")
        if unit_id not in safe_units:
            raise AudienceProgressError("工作动态不属于本次监查范围")
        try:
            status = NodeStatus(str(event.get("status")))
        except ValueError as exc:
            raise AudienceProgressError("工作动态状态无效") from exc
        safe = safe_units[str(unit_id)]
        latest_updates.append(
            {
                "time_text": _time_text(event.get("created_at")),
                "stage": safe["stage"],
                "label": safe["label"],
                "state_label": _STATUS_LABELS[status],
                "message": _event_message(
                    str(event.get("event_type")), status, safe["label"]
                ),
            }
        )

    completed_value = source.get("completed")
    total_value = source.get("total")
    if (
        isinstance(completed_value, bool)
        or not isinstance(completed_value, int)
        or completed_value < 0
        or isinstance(total_value, bool)
        or not isinstance(total_value, int)
        or total_value < 0
    ):
        raise AudienceProgressError("总体进度计数无效")
    completed = completed_value
    total = total_value
    percent = source.get("percent")
    if isinstance(percent, bool) or not isinstance(percent, (int, float)):
        raise AudienceProgressError("总体进度百分比无效")
    expected_percent = round((completed * 100.0 / total), 2) if total else 0.0
    if float(percent) != expected_percent:
        raise AudienceProgressError("总体进度百分比与权威记录不一致")
    status_overview = [
        {"state_label": _STATUS_LABELS[status], "count": counts[status]}
        for status in NodeStatus
        if counts.get(status, 0)
    ]
    return {
        "headline": _overall_state(counts, completed, total),
        "completed": completed,
        "total": total,
        "percent": float(percent),
        "progress_text": f"已处理 {completed}/{total} 项（{float(percent):g}%）",
        "status_overview": status_overview,
        "stage_progress": stage_progress,
        "current_work": current_work,
        "latest_updates": latest_updates,
    }
