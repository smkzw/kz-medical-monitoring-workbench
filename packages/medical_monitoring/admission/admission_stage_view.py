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


def confirmation_scope(
    *,
    draft: Any | None,
    latest_draft: Any | None,
) -> dict[str, Any]:
    """§6.2查找键显式披露：attempt键×project-latest键不再暗中打架。

    - latest为本attempt draft（或两侧皆无）→scope按draft状态正常
      （confirmed|pending）；
    - latest属于别的attempt（confirmed/未确认皆然）→scope=
      superseded_by_newer_attempt：本attempt的confirmation_status仍按
      其权威draft行如实展示，但显式披露「项目存在更新导入、项目级
      映射确认尚未完成」——B5门按latest判定409的语义不变。
    """

    status = _draft_status(draft) if draft is not None else ""
    latest_id = str(getattr(latest_draft, "batch_id", "") or "")
    draft_id = str(getattr(draft, "draft_id", "") or "") if draft is not None else ""
    latest_draft_id = (
        str(getattr(latest_draft, "draft_id", "") or "")
        if latest_draft is not None
        else ""
    )
    scope = "confirmed" if status == "confirmed" else "pending"
    payload: dict[str, Any] = {
        "scope": scope,
        "latest_draft_id": latest_draft_id,
        "latest_draft_attempt_id": latest_id,
    }
    if (
        scope == "confirmed"
        and latest_draft is not None
        and latest_draft_id != draft_id
    ):
        payload["scope"] = "superseded_by_newer_attempt"
        payload["note"] = (
            "本批次字段映射已确认，但项目存在更新导入，"
            "最新批次的字段映射确认尚未完成。"
        )
    return payload


def apply_single_source(
    payload: Mapping[str, Any],
    *,
    draft: Any | None,
    facts_status: Mapping[str, Any] | None,
    recognition_state_row: Mapping[str, Any] | None = None,
    recognition_jobs_exist: bool = False,
    backfill: "None | Any" = None,
    latest_draft: Any | None = None,
) -> dict[str, Any]:
    """冲突1四字段的唯一写点（02_DESIGN §6.1推导式表逐行实现）。

    ``recognition_state_row``=物化识别行（materialized模式读它）；
    ``backfill``=物化行缺失时的回填可调用（无参，由调用方绑定权威读+
    状态行写），回填后仍无行且cohort确有作业→fail-closed。
    ``latest_draft``=latest_draft_for_project权威行（S4 confirmation_scope
    查找键显式披露；缺省None时scope退化为attempt键自身）。
    """

    projected = dict(payload)
    summary = dict(projected.get("summary") or {})
    candidate_count = int(summary.get("candidate_count") or 0)

    # 顶层 state：物化行优先（materialized），derive保留派生值。
    if stage_view_mode() == "materialized":
        row = recognition_state_row
        if row is None and recognition_jobs_exist and callable(backfill):
            # E2E拦截修复：回填返回值此前被丢弃（row重读入参None），
            # 回填成功仍会误触fail-closed。取回填真值；回填后仍无行才
            # 按设计fail-closed。
            row = backfill()
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
    # S4：查找键二义性显式披露（§6.2）。
    projected["confirmation_scope"] = confirmation_scope(
        draft=draft, latest_draft=latest_draft,
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


# §3.5动作键枚举（前端文案表只认key）。标注*者为设计枚举之外的最小
# 扩展：no_draft/draft_active常态（无疑问/无阻断组）必须有可执行的
# 常规动作键（§3.3变迁条件即采纳/确认），否则§5.3不变量在健康路径
# 上必然500。
STAGE_ACTION_KEYS = frozenset(
    {
        "upload_documents",
        "retry_document_check",
        "resolve_role_adjudication",
        "confirm_identity",
        "retry_recognition_failed",
        "adopt_full",                # *常规全量采纳（no_draft常态）
        "adopt_partial",
        "adopt_inflight_degraded",
        "answer_questions",
        "resolve_blocked_groups",
        "confirm_mapping",           # *常规确认（draft_active无疑问常态）
        "confirm_mapping_degraded",
        "generate_facts",
        "retry_generate_facts",
    }
)

# F5恢复的单向映射：current_stage→向导激活面板（02_DESIGN §5.4）。
_STAGE_COMPLETION_STATES = {
    "documents": {"ready"},
    "recognition": {"candidates_ready"},
    "mapping_confirmation": {"confirmed"},
    "facts": {"ready"},
}
_STAGE_ORDER = ("documents", "recognition", "mapping_confirmation", "facts")


def build_stage_view(
    *,
    project_id: str,
    attempt_id: str,
    documents_state: str,
    recognition_state: str,
    mapping_state: str,
    facts_state: str,
    recognition_revision: int = 0,
    inflight_adoption_available: bool = False,
    recognition_failed_shards: bool = False,
    blocked_group_count: int = 0,
    unresolved_question_count: int = 0,
    facts_recent_failure: bool = False,
) -> dict[str, Any]:
    """跨阶段聚合出口（02_DESIGN §3.5）：stages/current_stage/blocking[]。

    blocking[]不变量（§5.3根治点3）：**需要用户自救的形态**（failed/
    needs_attention/未决疑问/阻断组/降级场景）必须携带≥1个
    action_available=true的动作键，违反→500 fail-closed暴露缺陷而非
    渲染死锁文案。等待态（in_progress/generating健康推进）如实给
    action_available=false的等待条目——健康排队不是缺陷，不得误伤。
    """

    stages = {
        "documents": str(documents_state or "not_started"),
        "recognition": str(recognition_state or "not_started"),
        "mapping_confirmation": str(mapping_state or "no_draft"),
        "facts": str(facts_state or "not_generated"),
    }
    for stage, state in stages.items():
        allowed = _STAGE_COMPLETION_STATES[stage] | {
            "documents": {"not_started", "in_progress", "needs_user_input", "failed"},
            "recognition": {"not_started", "generating", "needs_attention"},
            "mapping_confirmation": {"no_draft", "draft_active"},
            "facts": {"not_generated"},
        }[stage]
        if state not in allowed:
            raise AdmissionStageViewError("mapping_bridge_failed")

    blocking: list[dict[str, Any]] = []
    if stages["documents"] != "ready":
        blocking.append(_documents_blocking(stages["documents"]))
    if stages["recognition"] != "candidates_ready":
        blocking.append(
            _recognition_blocking(
                stages["recognition"],
                inflight_adoption_available=inflight_adoption_available,
                failed_shards=recognition_failed_shards,
            )
        )
    if stages["mapping_confirmation"] != "confirmed":
        blocking.append(
            _mapping_blocking(
                stages["mapping_confirmation"],
                blocked_group_count=blocked_group_count,
                unresolved_question_count=unresolved_question_count,
                recognition_ready=(
                    stages["recognition"] == "candidates_ready"
                ),
            )
        )
    if stages["facts"] != "ready":
        # generate_facts仅在轮到facts（映射已确认）时可用——此前阶段
        # 未完成时该动作不可执行，不得抢占primary_action_key。
        blocking.append(
            {
                "stage": "facts",
                "action_key": (
                    "retry_generate_facts" if facts_recent_failure
                    else "generate_facts"
                ),
                "action_available": (
                    stages["mapping_confirmation"] == "confirmed"
                ),
            }
        )

    current_stage = "complete"
    for stage in _STAGE_ORDER:
        if stages[stage] not in _STAGE_COMPLETION_STATES[stage]:
            current_stage = stage
            break

    # §5.3不变量：自救形态无可用动作键→fail-closed。自救形态=用户正
    # 处于该阶段且状态本身要求用户动作（failed/needs_attention/
    # needs_user_input/映射未确认）；健康等待态（in_progress/generating
    # /尚轮到的阶段）不是缺陷，不误伤。
    for entry in blocking:
        state = stages[entry["stage"]]
        escape_required = entry["stage"] == current_stage and (
            state in {"failed", "needs_attention", "needs_user_input"}
            or entry["stage"] == "mapping_confirmation"
        )
        if escape_required and not entry.get("action_available"):
            raise AdmissionStageViewError("mapping_bridge_failed")
    for entry in blocking:
        if entry["action_key"] not in STAGE_ACTION_KEYS:
            raise AdmissionStageViewError("mapping_bridge_failed")

    actionable = [entry for entry in blocking if entry.get("action_available")]
    primary_action_key = actionable[0]["action_key"] if actionable else ""
    return {
        "attempt_id": str(attempt_id),
        "stages": stages,
        "current_stage": current_stage,
        "blocking": blocking,
        "inflight_adoption_available": bool(inflight_adoption_available),
        "primary_action_key": primary_action_key,
        "revision": int(recognition_revision or 0),
    }


def _documents_blocking(state: str) -> dict[str, Any]:
    if state == "failed":
        return {
            "stage": "documents",
            "action_key": "retry_document_check",
            "action_available": True,
        }
    if state == "needs_user_input":
        # 角色/身份裁决挂起：两类入口都在文档面板（具体表单由
        # study-documents载荷驱动），此处给可达键。
        return {
            "stage": "documents",
            "action_key": "resolve_role_adjudication",
            "action_available": True,
        }
    return {
        "stage": "documents",
        "action_key": "upload_documents",
        "action_available": state == "not_started",
    }


def _recognition_blocking(
    state: str,
    *,
    inflight_adoption_available: bool,
    failed_shards: bool,
) -> dict[str, Any]:
    if state == "needs_attention":
        return {
            "stage": "recognition",
            "action_key": "adopt_partial",
            "action_available": True,
        }
    if state == "generating" and inflight_adoption_available:
        return {
            "stage": "recognition",
            "action_key": "adopt_inflight_degraded",
            "action_available": True,
        }
    if state == "generating" and failed_shards:
        return {
            "stage": "recognition",
            "action_key": "retry_recognition_failed",
            "action_available": True,
        }
    return {
        "stage": "recognition",
        "action_key": "retry_recognition_failed",
        "action_available": False,
    }


def _mapping_blocking(
    state: str,
    *,
    blocked_group_count: int,
    unresolved_question_count: int,
    recognition_ready: bool,
) -> dict[str, Any]:
    if blocked_group_count > 0:
        return {
            "stage": "mapping_confirmation",
            "action_key": "resolve_blocked_groups",
            "action_available": True,
        }
    if unresolved_question_count > 0:
        return {
            "stage": "mapping_confirmation",
            "action_key": "answer_questions",
            "action_available": True,
        }
    if state == "draft_active":
        return {
            "stage": "mapping_confirmation",
            "action_key": "confirm_mapping",
            "action_available": True,
        }
    # no_draft常态：识别尚未就绪时不可采纳（顺序未到），如实等待。
    return {
        "stage": "mapping_confirmation",
        "action_key": "adopt_full",
        "action_available": state == "no_draft" and recognition_ready,
    }
