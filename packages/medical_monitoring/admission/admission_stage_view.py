"""入舱阶段投影单一视图（02_DESIGN §6.1：冲突1四字段的唯一推导点）。

「每个wire字段唯一推导式」的本体：
- 顶层 ``state``：STAGE_VIEW_MODE=materialized（S3默认）读物化
  recognition行（行缺失且有cohort作业→按权威行现场回填一行再读；
  仍缺失→fail-closed 500 mapping_bridge_failed）；=derive（S2影子契约）
  保留pipeline派生值。
- 顶层 ``confirmation_status``：drafts权威行status（confirmed↔否则
  pending_confirmation）。
- 顶层 ``facts_generated``：A4直查结果（facts_status.facts_generated）。
- ``summary.pending_confirmation_count``：无draft→candidate_count；
  draft_active→draft内未答疑问字段数；confirmed→0。
- 字段级 ``confirmation_status``：候选命中draft.fields且该字段无疑问
  未答→confirmed；否则pending_confirmation。

本模块是纯函数（不做I/O）；运行门（B5/B6）永不经过这里——门仍直读
权威（02_DESIGN §6.2）。
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class AdmissionStageViewError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = str(code)
        super().__init__(self.code)


def stage_view_mode() -> str:
    """STAGE_VIEW_MODE：materialized（默认，S3起）| derive（S2影子回退）。"""

    import os

    mode = str(os.environ.get("STAGE_VIEW_MODE", "materialized")).strip().lower()
    return mode if mode in {"materialized", "derive"} else "materialized"


def _field_question_unresolved(field: Mapping[str, Any]) -> bool:
    """与confirm门同一疑问口径：字段仍有未答的用户疑问。"""

    from .mapping_confirmation import classify_user_question

    try:
        return classify_user_question(field) is not None
    except Exception:
        return False


def _draft_status(draft: Any) -> str:
    status = getattr(draft, "status", "")
    return str(getattr(status, "value", status) or "")


def _draft_fields(draft: Any) -> list[Mapping[str, Any]]:
    fields = getattr(draft, "fields", None)
    if fields is None and isinstance(draft, Mapping):
        fields = draft.get("fields")
    result: list[Mapping[str, Any]] = []
    for field in fields or ():
        if isinstance(field, Mapping):
            result.append(field)
        elif hasattr(field, "model_dump"):
            result.append(field.model_dump(mode="json"))
    return result


def confirmed_field_keys(draft: Any | None) -> set[tuple[str, str]]:
    """draft内「已确认」字段键（(domain,source_field)）：无疑问未答者。"""

    if draft is None:
        return set()
    return {
        (str(field.get("domain", "")), str(field.get("source_field", "")))
        for field in _draft_fields(draft)
        if not _field_question_unresolved(field)
    }


def pending_confirmation_count(
    *,
    draft: Any | None,
    candidate_count: int,
) -> int:
    """summary.pending_confirmation_count唯一推导式（02_DESIGN §6.1）。"""

    if draft is None:
        return int(candidate_count)
    if _draft_status(draft) == "confirmed":
        return 0
    return sum(
        1 for field in _draft_fields(draft) if _field_question_unresolved(field)
    )


def apply_single_source(
    payload: Mapping[str, Any],
    *,
    draft: Any | None,
    facts_status: Mapping[str, Any] | None,
    recognition_state_row: Mapping[str, Any] | None = None,
    recognition_jobs_exist: bool = False,
    backfill: "None | Any" = None,
) -> dict[str, Any]:
    """冲突1四字段的唯一写点（02_DESIGN §6.1推导式表逐行实现）。

    ``recognition_state_row``=物化识别行（materialized模式读它）；
    ``backfill``=物化行缺失时的回填可调用（无参，由调用方绑定权威读+
    状态行写），回填后仍无行且cohort确有作业→fail-closed。
    """

    projected = dict(payload)
    summary = dict(projected.get("summary") or {})
    candidate_count = int(summary.get("candidate_count") or 0)

    # 顶层 state：物化行优先（materialized），derive保留派生值。
    if stage_view_mode() == "materialized":
        row = recognition_state_row
        if row is None and recognition_jobs_exist and callable(backfill):
            backfill()
            row = recognition_state_row
        if row is not None:
            projected["state"] = str(row["state"])
        elif recognition_jobs_exist:
            # 写点遗漏/历史数据：fail-closed暴露缺陷而非渲染死锁文案
            # （02_DESIGN §5.3不变量同款纪律）。
            raise AdmissionStageViewError("mapping_bridge_failed")

    # 顶层 confirmation_status：drafts权威行status。
    draft_status = _draft_status(draft) if draft is not None else ""
    projected["confirmation_status"] = (
        "confirmed" if draft_status == "confirmed" else "pending_confirmation"
    )

    # 顶层 facts_generated：A4直查。
    projected["facts_generated"] = bool(
        (facts_status or {}).get("facts_generated")
    )

    # summary.pending_confirmation_count。
    summary["pending_confirmation_count"] = pending_confirmation_count(
        draft=draft, candidate_count=candidate_count,
    )
    projected["summary"] = summary

    # 字段级 confirmation_status：draft命中且无疑问未答→confirmed。
    confirmed = confirmed_field_keys(draft)
    candidates: list[Any] = []
    for item in projected.get("candidates") or ():
        if isinstance(item, Mapping):
            row = dict(item)
            key = (
                str(row.get("domain", "")),
                str(row.get("source_field", "")),
            )
            row["confirmation_status"] = (
                "confirmed" if key in confirmed else "pending_confirmation"
            )
            candidates.append(row)
        else:
            candidates.append(item)
    projected["candidates"] = candidates
    return projected
