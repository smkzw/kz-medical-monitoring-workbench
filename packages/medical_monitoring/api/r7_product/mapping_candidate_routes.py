"""Project-scoped C3 mapping-candidate and confirmation routes."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Protocol

from fastapi import APIRouter, File, Query, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError
from starlette.concurrency import run_in_threadpool

from ...admission.mapping_confirmation import enrich_candidates
from ...admission.admission_stage_view import AdmissionStageViewError
from ...admission.mapping_pipeline import (
    AdmissionMappingPipelineError,
    RECOGNITION_INFLIGHT_STALL_SECONDS,
)
from ...admission.document_authority import DocumentAuthorityError
from ...admission.pipeline import AdmissionPipelineError
from ...runtime import project_backup as pb
from .errors import _error_response, _run_entry_error_response
from .admission_routes import _validated_attempt_id

MAPPING_CANDIDATE_SCHEMA_VERSION = "mm-c3-mapping-candidate-v1"

# E2E拦截修复：500兜底（mapping_bridge_failed）此前静默吞栈，服务端
# 零痕迹；所有未预期异常必须留真栈。
_logger = logging.getLogger("mm.mapping_candidate_routes")
MAPPING_CONFIRMATION_SCHEMA_VERSION = "mm-c3-mapping-confirmation-v1"

# R28轮（R28-03）：研究文件核对的上游/基础设施类失败码——与
# services侧MonitoringDocumentAuthorityWorkflow._INFRA_FAILURE_CODES
# 同源（提供方限流/SSE中断/超时等瞬时故障，非文件内容判定）。
# 该类失败在失败分支不得引导「裁决」或「重新上传」充当唯一出路。
_DOCUMENT_AUTHORITY_INFRA_FAILURE_CODES = frozenset({
    "provider_runtime_error",
    "provider_sse_error_event",
    "provider_unavailable",
    "provider_timeout",
    "provider_rate_limited",
    "provider_auth_error",
    "provider_overloaded",
    "ai_not_configured",
    "network_error",
    "proxy_error",
})

# R7-01：resolve是同步长请求（推进双盲核对链可达20-30秒）。前端1.5秒
# 轮询曾无并发去重，堆积的resolve占满FastAPI同步线程池，期间
# /api/projects等全部请求排队超时——整站假死。按项目做在途防重入：
# 同一项目的并发resolve立即返回409引导稍候，不再排队占线程。
_RESOLVE_INFLIGHT: Dict[str, float] = {}
_RESOLVE_INFLIGHT_LOCK = threading.Lock()
_RESOLVE_INFLIGHT_TTL_SECONDS = 120.0

# 状态机专项T1（02_DESIGN §5-T1）：facts失败时效窗——failure_recorded
# 事件晚于最近一次ready且在24h内→retry_generate_facts动作键真实可达。
_FACTS_FAILURE_WINDOW = timedelta(hours=24)


def _parse_iso_event_time(value: Any) -> Optional[datetime]:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return None


def facts_recent_failure_from_events(
    events: Iterable[Mapping[str, Any]],
    *,
    now: Optional[datetime] = None,
) -> bool:
    """facts失败时效窗唯一推导（02_DESIGN §5-T1；纯函数便于测试）。

    - 无failure_recorded事件→False（现行为回归）；
    - 最近failure_recorded不晚于最近ready（state_changed→ready）→False
      （失败已被后续成功覆盖，retry键退回generate_facts）；
    - 最近failure_recorded超出24h时效窗→False（陈旧失败不再引导重试）。
    """

    moment = now or datetime.now(timezone.utc)
    last_ready_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    for event in events:
        created = _parse_iso_event_time(event.get("created_at"))
        if created is None:
            continue
        event_type = str(event.get("event_type") or "")
        if event_type == "failure_recorded":
            if last_failure_at is None or created > last_failure_at:
                last_failure_at = created
        elif (
            event_type == "state_changed"
            and str(event.get("to_state") or "") == "ready"
        ):
            if last_ready_at is None or created > last_ready_at:
                last_ready_at = created
    if last_failure_at is None:
        return False
    if last_ready_at is not None and last_failure_at <= last_ready_at:
        return False
    return (moment - last_failure_at) <= _FACTS_FAILURE_WINDOW


def _try_begin_resolve(project_id: str) -> bool:
    now = time.monotonic()
    with _RESOLVE_INFLIGHT_LOCK:
        started = _RESOLVE_INFLIGHT.get(project_id)
        if started is not None and now - started < _RESOLVE_INFLIGHT_TTL_SECONDS:
            return False
        _RESOLVE_INFLIGHT[project_id] = now
        return True


def _end_resolve(project_id: str) -> None:
    with _RESOLVE_INFLIGHT_LOCK:
        _RESOLVE_INFLIGHT.pop(project_id, None)

# R36轮（R36-01）：adjudicate同族在途防重入。一次复核推进内部要跑完整
# 双盲对账（输入修订重算可达分钟级）且持有项目写许可；前端1.5秒轮询+
# 页面刷新（F5后旧请求仍在服务端线程里跑）会让同草稿的复核推进彼此
# 叠加——C位实测期间 /api/projects 达11.5s、study-documents与
# mapping-candidates超15s超时的雪崩即由此放大。同项目同草稿已有复核
# 推进在途时，新请求立即返回诚实running快照（含draft_id维持前端轮询
# 状态机），不再叠加昂贵重算。TTL兜底进程异常退出后的残留登记。
_ADJUDICATE_INFLIGHT: Dict[str, float] = {}
_ADJUDICATE_INFLIGHT_LOCK = threading.Lock()
_ADJUDICATE_INFLIGHT_TTL_SECONDS = 240.0


def _try_begin_adjudicate(project_id: str, draft_id: str) -> bool:
    now = time.monotonic()
    key = f"{project_id}:{draft_id}"
    with _ADJUDICATE_INFLIGHT_LOCK:
        started = _ADJUDICATE_INFLIGHT.get(key)
        if started is not None and now - started < _ADJUDICATE_INFLIGHT_TTL_SECONDS:
            return False
        _ADJUDICATE_INFLIGHT[key] = now
        return True


def _end_adjudicate(project_id: str, draft_id: str) -> None:
    with _ADJUDICATE_INFLIGHT_LOCK:
        _ADJUDICATE_INFLIGHT.pop(f"{project_id}:{draft_id}", None)


_MAPPING_STATUS_CODES = {
    "mapping_admission_not_found": 404,
    "mapping_candidates_not_found": 404,
    "mapping_profile_not_ready": 409,
    "mapping_bridge_unconfigured": 503,
    "mapping_model_not_configured": 503,
    "mapping_verifier_unconfigured": 503,
    "mapping_cohort_invalid": 422,
    "mapping_cohort_legacy_route": 409,
    # R34轮（R33-B-F1）：双盲复核两群组数据版本不一致是可恢复的系统性
    # 状态（重新识别即收敛），不是服务器错误——不得落入兜底500。
    "mapping_cohort_input_mismatch": 409,
    "mapping_verifier_incomplete": 409,
    "mapping_verifier_job_failed": 409,
    "mapping_verifier_revision_drift": 409,
    "mapping_reconciliation_required": 409,
    "mapping_adjudication_failed_payload_unreadable": 409,
    "mapping_draft_unconfigured": 503,
    "mapping_bridge_failed": 500,
    "mapping_retry_unavailable": 503,
    "mapping_retry_table_invalid": 422,
    "mapping_document_evidence_resolver_unavailable": 503,
    "mapping_document_evidence_missing": 409,
    "mapping_document_evidence_incomplete": 422,
    "mapping_document_evidence_roles_unmet": 422,
    "document_packet_project_mismatch": 409,
    "mapping_document_selection_invalid": 422,
    "mapping_document_selection_not_found_or_role_mismatch": 404,
    "mapping_document_selection_unusable": 409,
    "mapping_document_registration_unavailable": 503,
    "mapping_document_registration_invalid": 422,
    "mapping_document_authority_unavailable": 503,
    # R40轮（R40-01）：核对作业创建失败（AI角色不可用等）——上游/配置类
    # 故障，不是文件内容问题，不得落入422「无法识别所选研究文件」误导重传。
    "mapping_document_authority_submit_unavailable": 503,
    "mapping_document_authority_incomplete": 409,
    "mapping_document_batch_required": 409,
    "mapping_document_selection_pending": 409,
    "mapping_document_refresh_pending": 409,
    "mapping_attempt_id_invalid": 422,
    "mapping_resolve_batch_id_required": 422,
    # R35轮（R33-07）：GET resolve曾把格式不合法的batch_id直接传给
    # pydantic模型构造，ValidationError在路由体内抛出→裸500（C位实测
    # 「补参后500」）。现在格式校验前置，参数非法与缺失一样给结构化
    # 422，不再出现不可诊断的服务器错误。
    "mapping_resolve_batch_id_invalid": 422,
    "mapping_focus_invalid": 422,
    "mapping_run_incomplete": 409,
    "mapping_candidate_not_adoptable": 409,
    "mapping_draft_conflict": 409,
    "mapping_quality_blocked": 409,
    # R31轮（R31-02）：识别源状态问题（分片缺失/载荷不一致）与用户输入
    # 非法分开归因——不再把系统性状态问题伪装成「字段修订内容无效」。
    "mapping_draft_source_unavailable": 409,
    "mapping_draft_invalid": 422,
    "mapping_questions_unresolved": 422,
}

_MAPPING_MESSAGES = {    "mapping_admission_not_found": "未找到对应的数据导入记录。请先完成数据导入后再生成字段对应建议。",
    "mapping_candidates_not_found": "尚未生成字段对应建议。请先发起生成。",
    "mapping_profile_not_ready": "数据结构识别尚未完成，暂时无法生成字段对应建议。请等待导入完成后再试。",
    "mapping_bridge_unconfigured": "系统识别服务暂不可用，请稍后重试。",
    "mapping_model_not_configured": "系统识别服务暂不可用，本次未发送数据。请稍后重试。",
    "mapping_verifier_unconfigured": "系统暂未完成复核准备，请稍后重试。",
    "mapping_cohort_invalid": "系统识别状态异常，请重新进入本页。",
    "mapping_cohort_legacy_route": (
        "此前的字段识别结果已过期，系统需要重新识别后才能继续。"
        "请点击重试。"
    ),
    # R34轮（R33-B-F1）：原文案「系统仍在复核，当前不需要您确认。」不说明
    # 是哪个环节在复核、也不说明确认会自动继续——5+次确认失败循环中该句
    # 与「请点击重试」同屏构成互斥指引（report_B.md F2）。如实点名双盲
    # 复核环节与自动推进路径。
    "mapping_verifier_incomplete": (
        "字段识别的双盲独立复核尚未完成（复核分片仍在生成或排队），"
        "暂时不能进入字段确认。无需重复点击；系统会自动推进复核，"
        "复核完成后确认环节将自动继续。"
    ),
    # R34轮（R33-B-F1）：该码此前未登记——落入兜底500「字段对应建议暂时
    # 不可用。」，确认失败循环全程零错误码零原因。补登记+如实事由。
    "mapping_cohort_input_mismatch": (
        "双盲复核两次识别所依据的数据版本不一致（数据或研究文件在识别后"
        "被重新提交），复核无法继续。请重新发起字段识别后再确认。"
    ),
    "mapping_verifier_job_failed": (
        "字段复核的分片任务失败，系统已将其重新排队重跑；请稍候再次查询。"
        "若持续失败，请重新发起字段识别。"
    ),
    "mapping_verifier_revision_drift": (
        "字段复核的输入证据已与当前数据版本不一致（研究文件或数据在"
        "识别后被重新提交），复核无法自动收敛；请重新发起字段识别。"
    ),
    "mapping_reconciliation_required": (
        "资料或核对结果已变化，系统会重新核实，不需要您逐项确认；"
        "您此前的回答已保留。"
    ),
    "mapping_adjudication_failed_payload_unreadable": (
        "部分失败分片的输入清单暂不可读，相关字段已保留为待核验状态；"
        "请重试或联系管理员。"
    ),
    "mapping_draft_unconfigured": "系统暂时无法保存识别结果，请稍后重试。",
    "mapping_bridge_failed": "生成字段对应建议时出现问题，本次结果未保存。请重试；如再次失败请联系管理员。",
    "mapping_retry_unavailable": (
        "当前识别会话不支持重跑失败分片，请重新发起字段识别。"
    ),
    "mapping_retry_table_invalid": (
        "表名参数无效；请刷新后重试，或不带表名重跑全部失败分片。"
    ),
    "mapping_document_evidence_resolver_unavailable": (
        "研究文档识别服务尚未就绪，本次未发送数据。请稍后重试。"
    ),
    "mapping_document_evidence_missing": (
        "系统还没有完成研究方案和电子病例报告表的识别。"
        "请先补充这两类文件，系统会自行核对，无需逐字段确认。"
    ),
    # R32-05：旧文案把「配对文档未就绪」误指为「全部为扫描版或文件损坏」，
    # 对已被系统成功识别的研究方案构成不实指控（report_C.md发现2）。
    # 该代码在证据门改造后不再由配对缺失路径触发；文案同步改为中性，
    # 防止未来复用时重新引入不实归因。
    "mapping_document_evidence_incomplete": (
        "研究文件证据链未通过完整性核对，本次未保存。"
        "请重新核对研究文件后重试；已成功识别的文件不会被判定为损坏。"
    ),
    "mapping_document_evidence_roles_unmet": (
        "研究文件配对不完整：生成字段映射需要研究方案与电子病例报告表"
        "均完成识别（声明「本次未提供」的文件同样计入缺失）。"
        "请补充上传缺失的研究文件并重新核对；"
        "已上传且识别成功的文件完好可用，与文件是否损坏无关。"
    ),
    "document_packet_project_mismatch": (
        "研究文档与当前项目不一致，本次未发送数据。请返回项目首页重新选择文件。"
    ),
    "mapping_document_selection_invalid": (
        "所选研究文档无效或已更新。请重新选择对应文件。"
    ),
    "mapping_document_selection_not_found_or_role_mismatch": (
        "未找到该文件，或文件类型与所选位置不符。请重新选择。"
    ),
    "mapping_document_selection_unusable": (
        "该文件已过期、不完整或未通过内容核对，暂时不能使用。"
    ),
    "mapping_document_registration_unavailable": (
        "研究文档导入服务尚未就绪，请稍后重试。"
    ),
    "mapping_document_registration_invalid": (
        "系统无法识别所选研究文件，请确认文件类型后重新添加。"
    ),
    "mapping_document_authority_unavailable": (
        "研究文件自动核对服务暂不可用，请稍后重试。"
    ),
    # R40轮（R40-01）：核对作业创建失败的如实归因——不是文件问题。
    "mapping_document_authority_submit_unavailable": (
        "研究文件核对任务未能创建：AI核对角色当前不可用或未配置。"
        "这不是文件内容问题，重新上传文件也无法解决；已上传的文件已保留。"
        "请联系管理员检查AI服务绑定后，再点「重新核对研究文件」。"
    ),
    "mapping_document_authority_incomplete": (
        "研究文件核对未能完成，请重新选择完整研究文件；无需逐项确认。"
    ),
    "mapping_document_batch_required": (
        "请一次选择需要使用的研究文件，系统会自动识别文件类型并交叉核对。"
    ),
    "mapping_document_selection_pending": (
        "文件已保存，但系统暂未完成关联。请稍后重新添加该文件。"
    ),
    "mapping_document_refresh_pending": (
        "文件已保存，系统暂未完成状态更新。请点击“重新核对研究文件”，无需再次上传。"
    ),
    "mapping_attempt_id_invalid": "数据导入记录标识无效。请返回上一步重新进入。",
    "mapping_resolve_batch_id_required": (
        "研究文件核对查询缺少批次参数（batch_id）。请返回向导重新进入第3步；"
        "若持续出现请刷新页面。"
    ),
    "mapping_resolve_batch_id_invalid": (
        "研究文件核对查询的批次参数（batch_id）格式无效。请返回向导重新进入"
        "第3步；若持续出现请刷新页面。"
    ),
    "mapping_focus_invalid": "筛选条件无效。请使用“重点优先”或“全部建议”。",
    "mapping_run_incomplete": "字段对应建议尚未完整完成，暂时不能进入确认。请等待生成完成或只重试失败部分。",
    "mapping_candidate_not_adoptable": "部分字段建议已不可采用。请重新生成建议后再确认。",
    "mapping_draft_conflict": "字段对应草稿发生冲突，本次未保存。请刷新后重试。",
    "mapping_quality_blocked": (
        "系统核对发现部分字段对应关系仍存在问题，暂时不能整体确认。"
        "请按系统提示修订对应字段后再确认。"
    ),
    "mapping_draft_source_unavailable": (
        "部分字段识别分片缺失或校验不一致，本次结果未保存。"
        "这不是填写内容的问题；请稍后重试，或重新发起字段识别。"
    ),
    "mapping_draft_invalid": "字段修订内容无效。请检查填写内容后重试。",
    "mapping_questions_unresolved": (
        "还有需要您确认的医学问题。请先逐条回答问题卡片"
        "（或在修订中给出对应关系和核对结论），再进行整体确认。"
    ),
}

_LAST_CHECK_NOTE_FILENAME = "last_document_check_note.json"


def _read_last_document_check_note(workspace_dir: Any) -> str:
    """R5冲刺（R1-11）：读最近一次文档核对结论（workflow层写入）。"""

    import json as _json
    from pathlib import Path as _Path

    try:
        value = _json.loads(
            (
                _Path(workspace_dir)
                / "document_authority_candidates"
                / _LAST_CHECK_NOTE_FILENAME
            ).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return ""
    if not isinstance(value, dict):
        return ""
    note = str(value.get("note") or "").strip()
    when = str(value.get("recorded_at") or "").strip()
    return f"{note}（记录于 {when[:19]}）" if note and when else note


def _latest_unpromoted_batch_brief(workspace_dir: Any) -> dict[str, Any] | None:
    """R25轮（R25-02）：最近一个尚无登记结果的研究文件核对批次简报。

    文件上传即服务端持久化（document_authority_candidates/batches），但
    readiness快照只反映已登记（select_document）的角色——核对完成前
    刷新/收起重开向导，必需角色回退「尚未添加」，用户被迫重传两份docx
    并重等18-35分钟核对（R25A/R25B实测；xlsx数据与人工裁决本身未丢）。
    本简报让readiness携带在途批次（batch_id+文件名），前端据此恢复
    「核对中」状态并继续推进既有核对，而非从零重来。
    """

    import json as _json
    from pathlib import Path as _Path

    batches_dir = (
        _Path(workspace_dir) / "document_authority_candidates" / "batches"
    )
    try:
        batch_files = sorted(
            (item for item in batches_dir.glob("*.json") if item.is_file()),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return None
    if not batch_files:
        return None
    # 只看最新一批：更旧且未完成的批次已被最新上传取代，报告它会把
    # 陈旧核对复活为「进行中」。
    try:
        batch = _json.loads(batch_files[0].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(batch, dict) or not str(batch.get("batch_id") or ""):
        return None
    if str(batch.get("authority_status") or "") == "promoted":
        return None
    files = [
        str(item.get("filename") or "").strip()
        for item in batch.get("candidates", ())
        if isinstance(item, dict) and str(item.get("filename") or "").strip()
    ]
    if not files:
        return None
    return {
        "analysis_token": str(batch["batch_id"]),
        "state": "analyzing",
        "headline": "已上传研究文件的核对尚未得出结论",
        "guidance": (
            "已上传的研究文件仍在核对或尚未得出结论（此前上传与您作出"
            "的确认均已保存）。系统会继续推进该批文件的核对并自动返回"
            "结论；刷新或重开后同样继续，无需重新上传。"
        ),
        "files": files,
    }


class AdmissionMappingPipeline(Protocol):
    def generate_dual_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
    ) -> Mapping[str, Any]: ...

    def generate_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
        cohort: str = "primary",
    ) -> Mapping[str, Any]: ...

    def list_candidates(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
        cohort: str = "primary",
    ) -> Mapping[str, Any]: ...

    def select_document(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
        role: str,
        source_entry_id: str,
    ) -> Mapping[str, Any]: ...

    def document_readiness(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
    ) -> Mapping[str, Any]: ...


class MappingDraftAdoptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=2_000)
    actor: str = Field(default="medical_manager", min_length=2, max_length=160)
    # R35轮（R35-01）：界面「采用已识别字段继续」降级入口的显式标志——
    # 识别长时间停滞（前端阈值30分钟）且已有已识别字段时，允许对已
    # 完成分片的结果子集知情采纳，未完成分片按部分采纳同规约排除出
    # 草稿并物化为缺口。默认False：普通generating态照旧拒绝（R19-01
    # 契约不变），仅降级按钮路径传True。
    include_incomplete: bool = False


class MappingDraftFieldEditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str = Field(min_length=2, max_length=200)
    domain: str = Field(min_length=1, max_length=80)
    source_field: str = Field(min_length=1, max_length=240)
    patch: dict[str, Any]
    expected_version: StrictInt = Field(ge=1)
    actor: str = Field(default="medical_manager", min_length=2, max_length=160)
    idempotency_key: str = Field(min_length=2, max_length=240)


class MappingDraftAdjudicateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str = Field(min_length=2, max_length=200)


class MappingDraftConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str = Field(min_length=2, max_length=200)
    expected_version: StrictInt = Field(ge=1)
    confirmed_by: str = Field(
        default="medical_manager",
        min_length=2,
        max_length=160,
    )
    confirmation_reason: str = Field(min_length=10, max_length=2_000)
    idempotency_key: str = Field(min_length=2, max_length=240)
    automatic: bool = False
    # R36轮（R36-01）：界面「不等待复核，知情降级确认」的显式标志——
    # 双盲复核长时间未收敛（验证队列排队/分片预算耗尽）且用户已作答
    # 完毕时的唯一非重入出路。默认False：常规确认的门与契约不变，仅
    # 降级按钮路径传True；降级事实由确认层写入留痕，不静默。
    allow_unverified_dual_review: bool = False


class DocumentAuthorityIdentityConfirmation(BaseModel):
    """R1循环：身份门的人工裁决出口（R5复用为核对结论留痕载体）。"""

    model_config = ConfigDict(extra="forbid")

    confirmed: bool
    reason: str = Field(min_length=2, max_length=2_000)


class DocumentAuthorityPromotionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(pattern=r"^mmbatch_[a-f0-9]{24}$")
    # 用户裁决：对双模型链无法收敛的角色，由医学经理绑定文件角色
    # （candidate_id为空=该角色缺失）。校验在workflow层fail-closed。
    user_role_selections: List[Dict[str, str]] = Field(default_factory=list)
    expected_decision_version: Optional[StrictInt] = Field(default=None, ge=0)
    # 身份门人工裁决：confirmed=true时落盘审计并放行该批次的角色核对。
    identity_confirmation: Optional[DocumentAuthorityIdentityConfirmation] = None
    # R28轮（R28-03/R28-04）：「重新核对研究文件」是用户显式重试——
    # 轮询路径也调用同一resolve端点，必须区分：显式重试对上游限流类
    # （infra）终态失败作业不受自动恢复预算约束，真实重排作业；轮询
    # 路径保持R27-01预算，避免无界attempt增长。
    explicit_retry: bool = False


@dataclass(frozen=True)
class MappingCandidateRouteContext:
    root: Any
    resolve_project: Any
    authorize: Any
    acquire_product_write_gate: Any
    workspace_dir: Any
    monitoring_action: Any
    admission_mapping_pipeline: Any
    admission_mapping_confirmation: Any = None
    monitoring_document_registrar: Any = None
    monitoring_document_authority_starter: Any = None
    monitoring_document_authority_promoter: Any = None


def _mapping_error(code: str) -> JSONResponse:
    return _error_response(
        _MAPPING_STATUS_CODES.get(code, 500),
        code,
        _MAPPING_MESSAGES.get(code, "字段对应建议暂时不可用。"),
    )


_PUBLIC_SUMMARY_FIELDS = frozenset({
    "job_count",
    "completed_job_count",
    "candidate_count",
    "pending_confirmation_count",
    "field_count",
    "user_question_count",
    "critical_count",
    "displayed_count",
    "system_adopted_count",
    "system_adjudicated_count",
})
_PUBLIC_MAPPING_FIELD_FIELDS = frozenset({
    "domain",
    "source_field",
    "recommended_role",
    "field_kind",
    "confidence",
    "uncertainty",
    "user_action",
    "prior_user_action",
    "user_decision_required",
    "related_fields",
    "standards_reference",
    "derivation_lineage",
    "value_constraints",
    "object_identity",
    "dose_semantics",
    "quality_gate_actions",
    "attention_reason",
    "needs_attention",
    "question_text",
    "system_adopted",
    "confirmation_status",
    "evidence_summary",
})


def _public_summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {
        key: value[key]
        for key in _PUBLIC_SUMMARY_FIELDS
        if key in value
    }


def _public_mapping_field(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {
        key: value[key]
        for key in _PUBLIC_MAPPING_FIELD_FIELDS
        if key in value
    }


def _closed_role_catalog_payload() -> list[dict[str, str]]:
    """R41轮（R41-01）：闭合目录角色候选（G-ROLE-002 阻断组随组下发）。

    延迟导入 services 侧语义质量模块（本仓库既有方向约定，见
    mapping_pipeline.py:1523 等处），避免包层顶层反向依赖。"""

    from services.api.app.monitoring_mapping_semantic_quality import (  # noqa: PLC0415
        closed_role_catalog_payload,
    )

    return [dict(item) for item in closed_role_catalog_payload()]


def _public_affected_field(value: Any) -> dict[str, Any]:
    """R41轮（R41-01）：阻断组涉及字段的公开投影（定位三键）。

    域/源字段/当前角色概念都是用户自己数据集的字段映射信息，非提供方
    或作业身份；前端据此渲染逐字段角色修订入口。"""
    if not isinstance(value, Mapping):
        return {}
    return {
        key: value[key]
        for key in ("domain", "source_field", "role_concept_id")
        if key in value
    }


def _public_draft(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    public = {
        key: value[key]
        for key in ("draft_id", "version", "status", "facts_generated")
        if key in value
    }
    public["fields"] = [
        _public_mapping_field(item) for item in value.get("fields") or ()
    ]
    public["user_questions"] = [
        _public_mapping_field(item)
        for item in value.get("user_questions") or ()
    ]
    if isinstance(value.get("semantic_quality"), Mapping):
        quality = value["semantic_quality"]
        public["semantic_quality"] = {
            key: quality[key]
            for key in (
                "status",
                "activation_disposition",
                "global_blocker_count",
                "capability_blocker_count",
                "warning_count",
            )
            if key in quality
        }
        # R41轮（R41-01）：阻断组必须携带可处置载荷——此前公开投影把
        # rule_id/affected_fields 全部剥掉，「应选择目录角色或保持未映射」
        # 成了无处置入口的死锁文案（R41B实测：blocked-group恒在、全页
        # 零角色编辑控件、确认按钮恒disabled约60分钟，刷新+3次重走向导
        # 均复现）。现随投影下发规则id与涉及字段定位，并给角色未闭合组
        # 附目录角色候选（供前端datalist），处置入口才真实存在。
        projected_groups = []
        has_unresolved_role_group = False
        for item in quality.get("finding_groups") or ():
            if not isinstance(item, Mapping):
                continue
            group = {
                key: item[key]
                for key in (
                    "finding_group_id",
                    "rule_id",
                    "severity",
                    "title_zh",
                    "summary_zh",
                    "affected_capability_ids",
                )
                if key in item
            }
            affected = item.get("affected_fields")
            if isinstance(affected, list):
                group["affected_fields"] = [
                    _public_affected_field(ref) for ref in affected
                ]
            if group.get("rule_id") == "G-ROLE-002":
                has_unresolved_role_group = True
            projected_groups.append(group)
        public["semantic_quality"]["finding_groups"] = projected_groups
        if has_unresolved_role_group:
            public["semantic_quality"]["role_catalog"] = (
                _closed_role_catalog_payload()
            )
        public["semantic_quality"]["capability_states"] = [
            {
                key: item[key]
                for key in ("capability_id", "state")
                if key in item
            }
            for item in quality.get("capability_states") or ()
            if isinstance(item, Mapping)
        ]
    public["review_summary"] = _public_summary(value.get("review_summary"))
    return public


def _public_table_failures(jobs: Any) -> list[dict[str, Any]]:
    """R32-04：按表聚合的识别失败清单（无作业身份，公开投影安全）。

    R32实测（ISO sqlite只读诊断）：265个识别分片queue_dwell_timeout终态
    失败且attempt_count=0，LB域全部沦陷；而界面此前只笼统显示「部分识
    别任务已终态失败」，用户须自行心算失败表名单。此处按表聚合分片
    级失败（表名/分片/原因/尝试次数），供第3步渲染失败清单与重跑入口。
    """

    grouped: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for job in jobs or ():
        if not isinstance(job, Mapping):
            continue
        status = str(job.get("status") or "")
        if status not in {"failed", "blocked", "stale_input", "cancelled"}:
            continue
        table = str(job.get("table_name") or "").strip() or "（未知表）"
        entry = grouped.get(table)
        if entry is None:
            entry = {
                "table_name": table,
                "failed_chunks": 0,
                "chunks": [],
                "failure_codes": [],
            }
            grouped[table] = entry
            order.append(table)
        entry["failed_chunks"] += 1
        chunk_index = str(job.get("chunk_index") or "").strip()
        entry["chunks"].append({
            "chunk_index": chunk_index,
            "status": status,
            "failure_code": str(job.get("failure_code") or ""),
            "failure_message": str(job.get("failure_message") or "")[:200],
            "attempt_count": int(job.get("attempt_count") or 0),
            "max_attempts": int(job.get("max_attempts") or 0),
        })
        code = str(job.get("failure_code") or "")
        if code and code not in entry["failure_codes"]:
            entry["failure_codes"].append(code)
    for entry in grouped.values():
        entry["chunks"].sort(key=lambda item: item["chunk_index"])
    return [grouped[table] for table in order]


def _public_mapping_projection(
    payload: Mapping[str, Any],
) -> dict[str, Any] | JSONResponse:
    public = {
        key: payload[key]
        for key in (
            "state",
            "confirmation_status",
            # 状态机专项S4（02_DESIGN §6.2）：查找键二义性显式披露
            # （attempt键×project-latest键，superseded_by_newer_attempt等）。
            "confirmation_scope",
            "facts_generated",
            # 状态机专项S5（02_DESIGN §5.2）：降级入口服务端化——前端
            # 按钮渲染读本标志（停滞判定单源）。
            "inflight_adoption_available",
            "next_action",
            "draft_id",
            "version",
            "status",
            # R36轮（R36-01）/R42轮（R42-01）：降级确认的知情留痕与
            # 事后补偿回执（盲核分片重新排队补跑的聚合计数，无作业
            # 身份）——公开投影如实透出，用户可见复核缺口已有自动出口。
            "dual_review_degraded",
            "dual_review_compensation",
        )
        if key in payload
    }
    public["summary"] = _public_summary(payload.get("summary"))
    public["candidates"] = [
        _public_mapping_field(item) for item in payload.get("candidates") or ()
    ]
    table_failures = _public_table_failures(payload.get("jobs"))
    if table_failures:
        public["table_failures"] = table_failures
    if isinstance(payload.get("verification"), Mapping):
        public["verification"] = {
            "state": payload["verification"].get("state"),
            "summary": _public_summary(payload["verification"].get("summary")),
        }
    if isinstance(payload.get("draft"), Mapping):
        public["draft"] = _public_draft(payload["draft"])
    elif "fields" in payload or "user_questions" in payload:
        public.update(_public_draft(payload))
    if isinstance(payload.get("adjudication"), Mapping):
        public["adjudication"] = {
            key: payload["adjudication"][key]
            for key in (
                "state",
                "resolved_count",
                "remaining_question_count",
                # R36轮（R36-01）：复核等待的聚合进度——分片已完成/总数、
                # 执行中/排队中、最早入队时间。仅聚合计数，无作业身份，
                # 公开投影安全；前端据此渲染复核进度并以真实进展复位
                # 停滞计时（R34-03「复核少量疑点」零进度指示同修）。
                "total_job_count",
                "completed_job_count",
                "pending_job_count",
                "pending_running_count",
                "pending_queued_count",
                "pending_since",
            )
            if key in payload["adjudication"]
        }
    forbidden = {
        "provider",
        "model",
        "source_entry_id",
        "sha256",
        "job_id",
        "candidate_id",
    }

    def contains_forbidden_key(value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(
                any(token in str(key).lower() for token in forbidden)
                or contains_forbidden_key(item)
                for key, item in value.items()
            )
        if isinstance(value, (list, tuple)):
            return any(contains_forbidden_key(item) for item in value)
        return False

    if contains_forbidden_key(public):
        # E2E拦截修复：白名单违规静默返回500同样零痕迹，留日志。
        _logger.error(
            "public mapping projection contained forbidden key: keys=%s",
            sorted(list(public.keys())),
        )
        return _mapping_error("mapping_bridge_failed")
    return public


def _assemble_stage_state(
    *,
    project_id: str,
    attempt_id: str,
    workspace_dir: Any,
    pipeline: Any,
    confirmation: Any,
    build_stage_view: Any,
    unresolved_question_counter: Any,
    pace_estimator: Any,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """stage-state四阶段权威装配（02_DESIGN §5.4/§3.5）。

    每阶段读各自权威：documents←document_readiness（A1/A3/A5投影）；
    recognition←物化行（缺失回填，S2写点同源）；mapping_confirmation←
    drafts权威行；facts←A4直查。轻量聚合，不取候选载荷。

    状态机专项M1（02_DESIGN §四-M1）：可选`now`时钟注入口，仅测试
    消费——缺省None=真钟=现状，生产调用零变化。
    """

    documents_state = "not_started"
    try:
        document_payload = dict(
            pipeline.document_readiness(
                project_id=project_id,
                attempt_id=attempt_id,
                workspace_dir=workspace_dir,
            )
            or {}
        )
    except Exception:
        document_payload = {}
    if document_payload.get("ready"):
        documents_state = "ready"
    elif str(document_payload.get("state") or "") == "failed":
        documents_state = "failed"
    elif document_payload:
        documents_state = "in_progress"

    recognition_state = "not_started"
    revision = 0
    inflight = False
    failed_shards = False
    ai_repository = getattr(confirmation, "ai_repository", None)
    if ai_repository is not None:
        task_type = getattr(confirmation, "task_type", "") or getattr(
            pipeline, "_task_type", ""
        )
        task_type = str(getattr(task_type, "value", task_type) or "")
        jobs = list(
            ai_repository.list_jobs(
                project_id,
                task_type=task_type,
                business_key_prefix=f"listing-field-mapping:{attempt_id}:",
            )
        )
        statuses = [
            str(getattr(getattr(job, "status", ""), "value", getattr(job, "status", "")))
            for job in jobs
        ]
        row_reader = getattr(confirmation, "_recognition_state_row", None)
        row = None
        if callable(row_reader):
            row = row_reader(project_id=project_id, attempt_id=attempt_id)
        if row is not None:
            recognition_state = str(row["state"])
            revision = int(row["revision"])
        elif statuses:
            from services.api.app.monitoring_admission_stage_store import (
                aggregate_recognition_state,
            )

            recognition_state = aggregate_recognition_state(statuses)
        failed_shards = any(
            status in {"failed", "blocked", "stale_input", "cancelled"}
            for status in statuses
        )
        completed = sum(status == "completed" for status in statuses)
        pace = pace_estimator(jobs, total=len(statuses), completed=completed)
        inflight = bool(
            recognition_state == "generating"
            and completed > 0
            and pace is not None
            and int(pace.get("last_completion_age_seconds") or 0)
            > RECOGNITION_INFLIGHT_STALL_SECONDS
        )

    mapping_state = "no_draft"
    blocked_group_count = 0
    unresolved = 0
    draft = None
    mapping_repository = getattr(confirmation, "mapping_repository", None)
    if mapping_repository is not None:
        try:
            draft = mapping_repository.find_draft_for_batch(project_id, attempt_id)
        except Exception:
            draft = None
        if draft is not None:
            status = getattr(getattr(draft, "status", ""), "value", getattr(draft, "status", ""))
            mapping_state = "confirmed" if str(status) == "confirmed" else "draft_active"
            if mapping_state == "draft_active":
                try:
                    fields = [
                        field.model_dump(mode="json")
                        if hasattr(field, "model_dump")
                        else dict(field)
                        for field in (draft.fields or ())
                    ]
                    unresolved = int(unresolved_question_counter(fields))
                except Exception:
                    unresolved = 0
                try:
                    quality = mapping_repository.semantic_quality(
                        project_id, str(draft.draft_id)
                    )
                    payload = quality.as_payload()
                    blocked_group_count = int(payload.get("global_blocker_count") or 0)
                except Exception:
                    blocked_group_count = 0

    facts_state = "not_generated"
    if confirmation is not None:
        facts_reader = getattr(confirmation, "_facts_status", None)
        if callable(facts_reader):
            try:
                facts_status = facts_reader(
                    project_id=project_id,
                    attempt_id=attempt_id,
                    workspace_dir=workspace_dir,
                )
                facts_state = (
                    "ready" if facts_status.get("facts_generated") else "not_generated"
                )
            except Exception:
                facts_state = "not_generated"

    # 状态机专项T1（02_DESIGN §5-T1）：读stage_events中facts最近的
    # failure_recorded（时效窗=晚于最近ready事件且24h内），retry键真实
    # 可达。best-effort：事件读取故障回退False=现状（参数缺省行为）。
    facts_recent_failure = False
    if ai_repository is not None:
        stage_store = getattr(ai_repository, "stage_store", None)
        events_reader = getattr(stage_store, "list_events", None) if stage_store is not None else None
        if callable(events_reader):
            try:
                facts_recent_failure = facts_recent_failure_from_events(
                    events_reader(
                        project_id, attempt_id, stage="facts", limit=500,
                    ),
                    now=now,
                )
            except Exception:
                facts_recent_failure = False

    return build_stage_view(
        project_id=project_id,
        attempt_id=attempt_id,
        documents_state=documents_state,
        recognition_state=recognition_state,
        mapping_state=mapping_state,
        facts_state=facts_state,
        recognition_revision=revision,
        inflight_adoption_available=inflight,
        recognition_failed_shards=failed_shards,
        blocked_group_count=blocked_group_count,
        unresolved_question_count=unresolved,
        facts_recent_failure=facts_recent_failure,
    )


def _repo_error_code(exc: Exception) -> Optional[str]:
    name = type(exc).__name__
    if "NotFound" in name:
        return "mapping_candidates_not_found"
    message = str(exc)
    if "mapping semantic quality gate is blocked" in message:
        return "mapping_quality_blocked"
    if "Conflict" in name or "StateConflict" in name:
        return "mapping_draft_conflict"
    # R31轮（R31-02）：源状态校验失败（分片缺失/载荷不一致等系统性
    # 状态问题）不得落入「用户修订内容无效」的422归因——此前一切
    # ValueError/DraftError都被归为mapping_draft_invalid，用户无任何
    # 修改点击采纳也被告知「请检查填写内容」，形成报错→重载→再报
    # 死循环。源状态问题对用户如实给409+系统侧指引。
    if "SourceStateError" in name:
        return "mapping_draft_source_unavailable"
    if "DraftError" in name or isinstance(exc, ValueError):
        return "mapping_draft_invalid"
    return None


def register_mapping_candidate_routes(
    router: APIRouter,
    context: MappingCandidateRouteContext,
) -> None:
    def _pipeline_or_error() -> Any:
        pipeline = context.admission_mapping_pipeline
        if pipeline is None:
            return _mapping_error("mapping_bridge_unconfigured")
        return pipeline

    def _confirmation_or_error() -> Any:
        service = context.admission_mapping_confirmation
        if service is None:
            return _mapping_error("mapping_draft_unconfigured")
        return service

    @router.post(
        "/data-admissions/{attempt_id}/study-documents",
        status_code=201,
    )
    async def register_mapping_document(
        project_id: str,
        attempt_id: str,
        request: Request,
        role: str = Query(...),
        file: UploadFile = File(...),
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.INTAKE_BATCH,
        )
        if isinstance(auth, JSONResponse):
            return auth
        if context.monitoring_document_authority_starter is not None:
            await file.close()
            return _mapping_error("mapping_document_batch_required")
        if context.monitoring_document_registrar is None:
            return _mapping_error("mapping_document_registration_unavailable")
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            await file.close()
            return _run_entry_error_response(exc)
        try:
            content = await file.read(50 * 1024 * 1024 + 1)
            if not content or len(content) > 50 * 1024 * 1024:
                return _mapping_error("mapping_document_registration_invalid")
            # R32-01：登记/关联/就绪检查都落workspace存储（哈希、DDL、
            # fsync），曾直接跑在事件循环里拖死全站并发请求；统一下放
            # 线程池。
            result = await run_in_threadpool(
                lambda: context.monitoring_document_registrar(
                    project_id=canonical,
                    role=role,
                    filename=file.filename or "",
                    content=content,
                )
            )
            source_entry_id = str(result.get("source_entry_id") or "").strip()
            if not source_entry_id:
                return _mapping_error("mapping_document_registration_invalid")
            workspace = context.workspace_dir(context.root, canonical)
            try:
                await run_in_threadpool(
                    lambda: pipeline.select_document(
                        project_id=canonical,
                        attempt_id=validated_attempt,
                        workspace_dir=workspace,
                        role=role,
                        source_entry_id=source_entry_id,
                    )
                )
            except AdmissionMappingPipelineError:
                raise
            except Exception:
                return _mapping_error("mapping_document_selection_pending")
            try:
                readiness = await run_in_threadpool(
                    lambda: pipeline.document_readiness(
                        project_id=canonical,
                        attempt_id=validated_attempt,
                        workspace_dir=workspace,
                    )
                )
            except Exception:
                return _mapping_error("mapping_document_refresh_pending")
            return {"project_id": canonical, **dict(readiness)}
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception:
            return _mapping_error("mapping_document_registration_invalid")
        finally:
            await file.close()
            write_permit.release()

    @router.get("/data-admissions/{attempt_id}/study-documents")
    async def mapping_document_readiness(
        project_id: str,
        attempt_id: str,
        request: Request,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.READ_SOURCE_EVIDENCE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        try:
            # R32-01：readiness是第3步的高频轮询路径，readiness本身与
            # 最近核对结论读取都落workspace；阻塞调用下放线程池，避免
            # 占住事件循环拖死全站并发请求（含 /api/projects）。
            result = await run_in_threadpool(
                lambda: pipeline.document_readiness(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    workspace_dir=context.workspace_dir(context.root, canonical),
                )
            )
            # R5冲刺（R1-11）：最近一次核对结论随readiness带回——刷新后
            # 「尚未添加」不再吞掉此前数分钟核对得出的拒收/待确认原因。
            note = _read_last_document_check_note(
                context.workspace_dir(context.root, canonical)
            )
            payload = {"project_id": canonical, **dict(result)}
            if note and not payload.get("ready"):
                payload["last_check_note"] = note
            # R25轮（R25-02）：尚无登记结果时携带最近在途核对批次——
            # 刷新/重开向导后前端恢复「核对中」并继续推进既有核对，
            # 不再回退「尚未添加」迫使重传重核。任一角色已登记（current）
            # 时不覆盖，避免把已就绪的部分误标为核对中。
            if not payload.get("ready") and not any(
                str(role.get("status") or "") == "current"
                for role in payload.get("roles", ())
                if isinstance(role, dict)
            ):
                analysis = _latest_unpromoted_batch_brief(
                    context.workspace_dir(context.root, canonical)
                )
                if analysis:
                    payload["analysis_token"] = analysis["analysis_token"]
                    payload["state"] = analysis["state"]
                    payload["headline"] = analysis["headline"]
                    payload["guidance"] = analysis["guidance"]
                    payload["files"] = analysis["files"]
                    for role in payload.get("roles", ()):
                        if (
                            isinstance(role, dict)
                            and role.get("status") == "missing"
                            and role.get("required_now")
                            and not role.get("user_declared_missing")
                        ):
                            role["status_text"] = "已上传，核对中"
            return payload
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception:
            return _mapping_error("mapping_document_evidence_incomplete")

    @router.post(
        "/data-admissions/{attempt_id}/study-documents/analyze",
        status_code=202,
    )
    async def analyze_mapping_documents(
        project_id: str,
        attempt_id: str,
        request: Request,
        files: list[UploadFile] = File(...),
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.INTAKE_BATCH,
        )
        if isinstance(auth, JSONResponse):
            return auth
        if _validated_attempt_id(attempt_id) is None:
            return _mapping_error("mapping_attempt_id_invalid")
        if context.monitoring_document_authority_starter is None:
            return _mapping_error("mapping_document_authority_unavailable")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            captured = []
            for upload in files:
                content = await upload.read(50 * 1024 * 1024 + 1)
                if not content or len(content) > 50 * 1024 * 1024:
                    return _mapping_error("mapping_document_registration_invalid")
                captured.append((upload.filename or "", content))
            # R32-01：starter包含docx/pdf抽取与OCR提交，曾直接跑在事件
            # 循环里（单次可达分钟级），全站请求在其间一律停摆；下放
            # 线程池。
            result = await run_in_threadpool(
                lambda: context.monitoring_document_authority_starter(
                    project_id=canonical,
                    workspace_dir=context.workspace_dir(context.root, canonical),
                    files=captured,
                )
            )
            response = {
                "project_id": canonical,
                "state": str(result["state"]),
                "analysis_token": str(result["batch_id"]),
                # R42-09：标题不预设「独立」——独立性状态由运维绑定披露
                # （shared_runtime_identity附注）如实表达，标题只描述阶段。
                "headline": "系统正在识别并交叉核对研究文件",
                "guidance": "当前无需逐项确认，完成后会自动更新研究文件状态。",
            }
            if result.get("shared_runtime_identity"):
                # R40轮（R40-01）：运维同绑定（盲核与主分析同通道同模型）
                # 的知情降级——在用户可见指引中如实披露独立性受限。
                response["shared_runtime_identity"] = True
                response["guidance"] = (
                    str(response["guidance"])
                    + "注：当前盲核与主分析由运维绑定为同一通道同一模型"
                    "（如额度所限的临时安排），本次核对以「双通道复诵＋您的"
                    "人工归属确认」推进，模型间独立性弱于常态；恢复独立盲核"
                    "通道后可重新核对。"
                )
            if result.get("previously_analyzed"):
                response["previously_analyzed"] = True
                response["guidance"] = (
                    "这组文件与此前上传的内容完全一致，系统会直接复用已有的"
                    "核对结论（因此可能很快返回相同结果）；如需重新核对，"
                    "请更换文件版本后上传。"
                )
            return response
        except DocumentAuthorityError as exc:
            if str(exc) == "document_authority_evidence_incomplete":
                return _mapping_error("mapping_document_evidence_incomplete")
            if str(exc) == "document_authority_submit_unavailable":
                # R40轮（R40-01）：核对作业创建失败（AI角色不可用等）不是
                # 文件问题——不得再伪装成「无法识别所选研究文件」误导重传。
                return _mapping_error(
                    "mapping_document_authority_submit_unavailable"
                )
            return _mapping_error("mapping_document_registration_invalid")
        except ValueError:
            return _mapping_error("mapping_document_registration_invalid")
        finally:
            for upload in files:
                await upload.close()
            write_permit.release()

    @router.post(
        "/data-admissions/{attempt_id}/study-documents/resolve",
        status_code=200,
    )
    def resolve_mapping_documents(
        project_id: str,
        attempt_id: str,
        payload: DocumentAuthorityPromotionRequest,
        request: Request,
    ) -> Any:
        return _resolve_mapping_documents_impl(
            project_id, attempt_id, payload, request
        )

    @router.get(
        "/data-admissions/{attempt_id}/study-documents/resolve",
        status_code=200,
    )
    async def resolve_mapping_documents_get(
        project_id: str,
        attempt_id: str,
        request: Request,
        batch_id: str = Query(default=""),
    ) -> Any:
        # R16轮（R16-01）：实测有前端/工具以GET轮询resolve（POST-only
        # 路由返回404 route_not_found且未被捕获→界面无限挂起）。补GET
        # 语义：batch_id经查询参数传入（无请求体），行为与POST一致
        # （只读推进核对状态机）。缺batch_id时给出明确可读错误而非404。
        if not batch_id.strip():
            # R19轮（R19-02）：缺batch_id曾被误报为mapping_attempt_id_
            # invalid（与「attempt失效」混淆，误导排障）——如实报告
            # 缺少查询参数。
            return _mapping_error("mapping_resolve_batch_id_required")
        try:
            payload = DocumentAuthorityPromotionRequest(batch_id=batch_id.strip())
        except ValidationError:
            # R35轮（R33-07）：batch_id格式不合法（如把来源修订号srcc1_*
            # 当批次号传入）曾在路由体内抛pydantic ValidationError→裸500
            #（C位实测「补参后500」）。现在与缺失同样给结构化422。
            return _mapping_error("mapping_resolve_batch_id_invalid")
        # R32-01：advance（核对推进）单次最长约30秒（本路由409文案即
        # 自证），async轮询路径不得在事件循环内同步执行；与POST同义但
        # 下放线程池。
        return await run_in_threadpool(
            _resolve_mapping_documents_impl,
            project_id,
            attempt_id,
            payload,
            request,
        )

    def _resolve_mapping_documents_impl(
        project_id: str,
        attempt_id: str,
        payload: DocumentAuthorityPromotionRequest,
        request: Request,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.INTAKE_BATCH,
        )
        if isinstance(auth, JSONResponse):
            return auth
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        if context.monitoring_document_authority_promoter is None:
            return _mapping_error("mapping_document_authority_unavailable")
        # R7-01在途防重入：同项目已有resolve在跑时立即返回，不排队
        # 占用同步线程池（原堆积曾致整站假死）。
        if not _try_begin_resolve(canonical):
            return JSONResponse(
                status_code=409,
                content={
                    "code": "document_resolve_in_progress",
                    "message": (
                        "研究文件核对正在推进中（单次最长约30秒）；"
                        "请稍候再查询，无需密集重试。"
                    ),
                    "project_id": canonical,
                    "state": "analyzing",
                },
            )
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            _end_resolve(canonical)
            return _run_entry_error_response(exc)
        try:
            actor = getattr(auth, "principal_id", None) or "medical_manager"
            request_fields = payload.model_dump()
            confirmation_payload = request_fields.pop("identity_confirmation", None)
            explicit_retry = bool(request_fields.pop("explicit_retry", False))
            result = context.monitoring_document_authority_promoter(
                project_id=canonical,
                workspace_dir=context.workspace_dir(context.root, canonical),
                actor=str(actor),
                identity_confirmation=confirmation_payload,
                explicit_retry=explicit_retry,
                **request_fields,
            )
            if result.get("state") == "failed":
                # V5会商L2-1：失败必须可诊断。作业级failure_code/message
                # 透传给前端与台账，不再用同一句通用文案掩盖差异。
                # R28轮（R28-03）：失败文案按失败类别如实区分——上游
                # 限流/中断（infra类）不是文件内容问题，也无处可「裁决」，
                # 旧文案「可对文件角色作出裁决后重试」在该分支承诺了
                # 不存在的控件（三名测试者分别滞留40/93/32分钟无出路）。
                # infra类如实告知上游状态与等待重试路径；内容类才引导
                # 重新上传。
                failure_code = str(result.get("failure_code") or "")
                if failure_code in _DOCUMENT_AUTHORITY_INFRA_FAILURE_CODES:
                    failure_headline = (
                        "上游AI服务暂时不可用（限流或中断），研究文件核对未完成——"
                        "这不是文件内容问题。"
                    )
                    failure_guidance = (
                        "已上传的文件与您的确认均已保留；请稍候几分钟后再点"
                        "「重新核对研究文件」（该按钮会真实重排核对作业），"
                        "上游服务恢复后即可通过；也可稍后返回本页查看自动恢复结果。"
                    )
                elif failure_code == "invalid_ai_output":
                    # R39轮（R39-01/R37-03）：AI输出未通过系统契约校验——
                    # 不是文件内容问题，重新上传解决不了；指引指向真实
                    # 强制重跑入口（「重新核对研究文件」按钮，explicit_
                    # retry重排作业），并如实说明相同文件重传会复用失败
                    # 结论（与分析接口的复用提示同一口径）。
                    failure_headline = (
                        "研究文件核对的AI输出未通过系统契约校验，核对未完成。"
                    )
                    failure_guidance = (
                        "这是系统对AI输出的fail-closed防护，不是文件内容问题，"
                        "重新上传文件也无法解决；已上传的文件与您的确认均已保留。"
                        "请点击「重新核对研究文件」（该按钮会真实重排核对作业）；"
                        "注意：重新上传完全相同的文件不会重新核对——系统会直接"
                        "复用本次失败的核对结论。"
                    )
                else:
                    # R37轮（R37-03）：旧文案「相同或新版本均可」与复用语义
                    # 自相矛盾——相同文件重传只会复用已缓存的失败结论，按
                    # 失败区指导操作的用户永远拿不到新结果。改为如实告知
                    # 复用事实与两条真实出路（换版本重传 / 按钮强制重跑）。
                    failure_headline = "研究文件自动核对未完成（见失败原因）。"
                    failure_guidance = (
                        "请注意：重新上传完全相同的文件不会重新核对，系统会"
                        "直接复用本次失败的核对结论。要获得新的核对结果，"
                        "请更换新版本文件后上传，或直接点击"
                        "「重新核对研究文件」（该按钮会真实重排核对作业）；"
                        "已上传的文件与您的确认不会丢失。"
                    )
                return JSONResponse(
                    status_code=409,
                    content={
                        "code": "mapping_document_authority_failed",
                        "message": f"{failure_headline}{failure_guidance}",
                        "detail": {
                            "failure_code": failure_code,
                            "failure_class": (
                                "upstream_unavailable"
                                if failure_code
                                in _DOCUMENT_AUTHORITY_INFRA_FAILURE_CODES
                                else "content_check_failed"
                            ),
                            "failure_message": str(
                                result.get("failure_message") or ""
                            )[:400],
                            "failed_jobs": list(result.get("failed_jobs", ()) or []),
                        },
                        "project_id": canonical,
                        "state": "failed",
                    },
                )
            if result.get("authority_status") != "promoted":
                state = str(result.get("state") or "analyzing")
                user_choices = result.get("user_choices") or []
                if state == "project_mismatch":
                    headline = "研究资料与当前项目不一致"
                    guidance = (
                        "系统未能在文件与当前项目信息之间自动建立对应关系"
                        "（常见原因：项目代号与方案研究编号不同、或药物"
                        "命名不一致）。未经您确认前，本次不会用于"
                        "当前项目；若您确认这些文件属于本研究，请点击"
                        "“确认属于当前项目并继续”，或重新选择文件。"
                    )
                elif state == "project_identity_incomplete":
                    headline = "系统还无法确认资料归属"
                    guidance = (
                        "文件中的研究编号、药物或适应症信息与当前项目"
                        "信息无法自动对应（当前项目可能尚未登记方案编号，"
                        "因此系统缺少可比对的基准，并不代表文件缺少内容）。"
                        "请核对文件确属本研究后点击“确认属于当前项目并"
                        "继续”，或在项目中补充登记方案编号后重新上传。"
                    )
                elif state == "needs_user_input":
                    headline = "还差一项关键信息"
                    guidance = str(result.get("user_question") or "").strip() or (
                        "仅有少量文件关系仍无法唯一确定，请确认系统标出的"
                        "分歧文件。"
                    )
                    if user_choices:
                        guidance = (
                            "请对下列每个文件角色作出裁决：选择它对应的"
                            "文件，或标记该角色缺失。"
                        )
                elif state == "evidence_incomplete":
                    if user_choices:
                        # 未决角色两侧都没有绑定候选：不是"补齐内容"，
                        # 是需要用户指认文件角色或补充上传。
                        headline = "需要您确认文件角色"
                        guidance = (
                            "系统两轮核对后仍有文件角色无法自动判定。"
                            "请对下列每个角色选择对应文件，或标记缺失。"
                        )
                        state = "needs_user_input"
                    else:
                        headline = "系统正在补齐少量文件内容"
                        guidance = (
                            "暂时无需重新选择全部文件，系统会先恢复所需证据。"
                        )
                elif state == "cross_checking":
                    headline = "系统正在复核最后几个分歧"
                    guidance = "无需操作，系统会自行核对并处理差异。"
                elif state == "adjudicating":
                    headline = "系统正在完成最后一次核对"
                    guidance = "无需操作，系统会自行处理两次判断中的差异。"
                else:
                    # R42-09：原「系统仍在独立核对研究文件」与同屏降级
                    # 说明（同通道同模型绑定）自相矛盾——稽查/培训只引用
                    # 标题会夸大模型独立性。标题只陈述阶段；独立性状态以
                    # 降级附注如实表达。
                    headline = "研究文件核对中"
                    guidance = "当前无需逐项确认，请稍后查看结果。"
                response_payload = {
                    "project_id": canonical,
                    "state": state,
                    "analysis_token": payload.batch_id,
                    "headline": headline,
                    "guidance": guidance,
                    "files": [
                        str(value)
                        for value in result.get("attention_files", ())
                        if str(value).strip()
                    ],
                }
                # R25轮（R25-03）：透传pending作业数与最早入队时间，前端
                # 显示阶段耗时并在长时间无进展时给出重试指引。
                # R31轮（R31-06）：排队/执行中分开透传，用户可区分
                # 「等待队列」与「正在核对」。
                if result.get("pending_job_count") is not None:
                    response_payload["pending_job_count"] = int(
                        result["pending_job_count"]
                    )
                if result.get("pending_running_count") is not None:
                    response_payload["pending_running_count"] = int(
                        result["pending_running_count"]
                    )
                if result.get("pending_queued_count") is not None:
                    response_payload["pending_queued_count"] = int(
                        result["pending_queued_count"]
                    )
                if result.get("pending_since"):
                    response_payload["pending_since"] = str(result["pending_since"])
                if result.get("explicit_retry_receipt"):
                    # R43轮（R43-02）：显式重核对受理回执透传（重排/重新计时
                    # 的作业与受理时刻）——前端据此回显确认并重置等待计数，
                    # 杜绝「点击后零变化无法区分受理与无效」。
                    response_payload["explicit_retry_receipt"] = dict(
                        result["explicit_retry_receipt"]
                    )
                if result.get("shared_runtime_identity"):
                    # R40轮（R40-01）：运维同绑定的知情降级在轮询响应中
                    # 持续如实披露。
                    response_payload["shared_runtime_identity"] = True
                    response_payload["guidance"] = (
                        str(response_payload.get("guidance") or "")
                        + "（当前盲核与主分析为同通道同模型的运维绑定："
                        "以双通道复诵＋人工归属确认推进，模型间独立性"
                        "弱于常态。）"
                    )
                if result.get("decision_version") is not None:
                    response_payload["decision_version"] = int(
                        result["decision_version"]
                    )
                if user_choices:
                    response_payload["user_choices"] = user_choices
                content_confirmations = result.get("content_confirmations") or []
                if content_confirmations:
                    response_payload["content_confirmations"] = content_confirmations
                    response_payload["headline"] = "需要您核对文件内容"
                    response_payload["guidance"] = (
                        "部分文件内容与预期上下文不一致。请逐项核对后"
                        "确认沿用，或更换文件后重新上传。"
                    )
                return response_payload
            registered_roles: set[str] = set()
            for registration in result.get("registrations", ()):
                pipeline.select_document(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    workspace_dir=context.workspace_dir(context.root, canonical),
                    role=str(registration["role"]),
                    source_entry_id=str(registration["source_entry_id"]),
                )
                registered_roles.add(str(registration["role"]))
            # R7轮（R1-02收口）：用户裁决「该角色缺失」（空candidate_id）
            # 落显式缺失声明——readiness据此不再把该角色算作required，
            # 「选未提供」后ready可转true，出口不再死锁。
            # R26轮（R26-01）：以「生效裁决」为准而非只看本次请求体——
            # 裁决已跨请求持久化（workflow层_save_user_selections），用户
            # 先保存「本次未提供eCRF」、再确认内容差异时，确认后的
            # resolve请求体不含user_role_selections，旧实现据此漏写
            # 声明，readiness恒missing、主按钮「请先添加所需文件」永久
            # 置灰（第3步无出口死锁）。晋升结果回带的
            # user_declared_missing_roles即持久化裁决的生效形态。
            effective_selections = [
                {"role": str(role), "candidate_id": ""}
                for role in result.get("user_declared_missing_roles") or ()
                if str(role).strip()
            ]
            seen_declared: set[str] = set()
            for selection in [
                *effective_selections,
                *(request_fields.get("user_role_selections") or ()),
            ]:
                if not isinstance(selection, Mapping):
                    continue
                role = str(selection.get("role") or "").strip()
                if (
                    role in registered_roles
                    or not role
                    or role in seen_declared
                    or str(selection.get("candidate_id") or "").strip()
                ):
                    continue
                seen_declared.add(role)
                if hasattr(pipeline, "declare_document_missing"):
                    pipeline.declare_document_missing(
                        project_id=canonical,
                        attempt_id=validated_attempt,
                        workspace_dir=context.workspace_dir(context.root, canonical),
                        role=role,
                        actor=str(actor),
                    )
            readiness = pipeline.document_readiness(
                project_id=canonical,
                attempt_id=validated_attempt,
                workspace_dir=context.workspace_dir(context.root, canonical),
            )
            return {"project_id": canonical, **dict(readiness)}
        except DocumentAuthorityError as exc:
            # V5会商L2-1：DocumentAuthorityError携带精确错误码（如
            # document_authority_job_attempt_invalid）——透传而非吞噬。
            diagnostic = str(exc).strip() or "document_authority_error"
            # R2测试循环：不再对任何诊断码统一承诺「可对文件角色作出
            # 裁决后重试」——逐码给出与界面能力一致的真实指引。
            if diagnostic == "document_authority_candidate_not_promotable":
                guidance_text = (
                    "所选文件内容无法完整读取（如扫描版PDF），不能作为"
                    "权威研究文件。请将该文件角色标记为缺失，或更换为"
                    "可读取版本后重新上传。"
                )
            elif diagnostic == "document_authority_selection_not_parsable":
                guidance_text = (
                    "该文件内容无法完整读取（如扫描版PDF），不能作为"
                    "权威研究文件。请改为选择「该角色缺失」，或上传可"
                    "读取的文件版本。"
                )
            elif diagnostic == "document_authority_submit_unavailable":
                # R40轮（R40-01）：核对任务创建失败是上游/配置类故障，
                # 不是文件问题——如实指认，不给「重新上传」的假出路。
                guidance_text = (
                    "核对任务创建失败：AI核对角色当前不可用或未配置。"
                    "这不是文件内容问题，重新上传文件也无法解决；已上传的"
                    "文件与您的确认均已保留。请联系管理员检查AI服务绑定后，"
                    "再点「重新核对研究文件」。"
                )
            elif diagnostic == "document_authority_job_missing":
                # R40轮（R40-01）：批次在库而作业缺失（历史故障残留）——
                # 真实出路是重传同一组文件触发重建（analyze会按批次清单
                # 幂等重建缺失作业），而不是笼统的「稍后重试」。
                guidance_text = (
                    "该批次的核对任务记录缺失（多为先前一次系统故障所致）。"
                    "请重新上传同一组研究文件——相同文件即可：系统会重建"
                    "核对任务并自动继续，无需更换文件版本。"
                )
            elif diagnostic == "document_authority_runs_not_independent":
                # R44轮（R44-01）：独立性问题不是文件内容问题——重传与
                # 空等都无法自行恢复。如实指认「双通道同身份」成因并点名
                # 运维出路，不再笼统建议「稍后重试，或重新上传研究文件」。
                guidance_text = (
                    "两次独立核对的AI通道身份未通过独立性校验（盲核与主"
                    "分析当前被绑定到同一通道同一模型，且未经知情降级"
                    "确认）。这不是文件内容问题，重新上传或继续等待都无法"
                    "解决；已上传的文件与您的确认均已保留。请联系管理员"
                    "把盲核与主分析恢复为相互独立的AI通道（或确认运维同"
                    "绑定降级已生效）后，再点「重新核对研究文件」。"
                )
            else:
                guidance_text = "请稍后重试，或重新上传研究文件。"
            return JSONResponse(
                status_code=409,
                content={
                    "code": "mapping_document_authority_failed",
                    "message": (
                        "研究文件自动核对未完成（诊断：" + diagnostic
                        + "）。" + guidance_text
                    ),
                    "detail": {"error_code": diagnostic},
                    "project_id": canonical,
                    "state": "failed",
                },
            )
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={
                    "code": "mapping_document_authority_error",
                    "message": "研究文件核对发生未预期错误，请重试或反馈。",
                    "detail": {
                        "error_type": type(exc).__name__,
                        "error_message": str(exc)[:300],
                    },
                    "project_id": canonical,
                },
            )
        finally:
            _end_resolve(canonical)
            write_permit.release()

    @router.post("/data-admissions/{attempt_id}/mapping-candidates", status_code=201)
    async def generate_mapping_candidates(
        project_id: str,
        attempt_id: str,
        request: Request,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.INTAKE_BATCH,
        )
        if isinstance(auth, JSONResponse):
            return auth
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            workspace = context.workspace_dir(context.root, canonical)
            # R32-01：双候选生成本地装配逐表AI包（大清单可达数百分片），
            # 阻塞调用下放线程池。
            result = await run_in_threadpool(
                lambda: pipeline.generate_dual_candidates(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    workspace_dir=workspace,
                )
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                **public,
                "schema_version": MAPPING_CANDIDATE_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except AdmissionPipelineError:
            return _mapping_error("mapping_admission_not_found")
        except Exception:
            # E2E拦截修复：mapping_bridge_failed此前静默吞栈（50分钟
            # 盲试无任何服务端痕迹），500兜底必须留真栈供取证。
            _logger.exception(
                "mapping-candidates projection failed (project=%s)", canonical,
            )
            return _mapping_error("mapping_bridge_failed")
        finally:
            write_permit.release()

    @router.get("/data-admissions/{attempt_id}/mapping-candidates")
    async def list_mapping_candidates(
        project_id: str,
        attempt_id: str,
        request: Request,
        focus: str = Query(default="critical"),
        cohort: str = Query(default="dual"),
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.READ_SOURCE_EVIDENCE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            confirmation = context.admission_mapping_confirmation
            workspace = context.workspace_dir(context.root, canonical)
            effective_cohort = "primary" if cohort == "dual" else cohort
            # R32-01：候选列表/复核视图装配（264字段量级）是第3步高频
            # 轮询路径，阻塞调用下放线程池。
            if confirmation is not None and effective_cohort == "primary":
                result = await run_in_threadpool(
                    lambda: confirmation.list_for_review(
                        project_id=canonical,
                        attempt_id=validated_attempt,
                        workspace_dir=workspace,
                        focus=focus,
                    )
                )
            else:
                result = enrich_candidates(
                    await run_in_threadpool(
                        lambda: pipeline.list_candidates(
                            project_id=canonical,
                            attempt_id=validated_attempt,
                            workspace_dir=workspace,
                            cohort=effective_cohort,
                        )
                    ),
                    focus=focus,
                )
            if cohort == "dual":
                try:
                    verifier = await run_in_threadpool(
                        lambda: pipeline.list_candidates(
                            project_id=canonical,
                            attempt_id=validated_attempt,
                            workspace_dir=workspace,
                            cohort="verifier",
                            # R41轮（R34-08）：GET对verifier只消费state与
                            # summary聚合计数——轻量状态包跳过全量候选装配
                            # （54表量级下单次GET=主+verifier两次全量装配，
                            # 实测14.4s+、写入期>15s触发客户端AbortError）。
                            include_candidates=False,
                        )
                    )
                    result = {
                        **dict(result),
                        "verification": {
                            "state": verifier.get("state"),
                            "summary": verifier.get("summary"),
                        },
                    }
                except AdmissionMappingPipelineError as exc:
                    if exc.code != "mapping_candidates_not_found":
                        raise
                    result = {
                        **dict(result),
                        "verification": {
                            "state": "waiting",
                            "summary": {"job_count": 0, "completed_job_count": 0},
                        },
                    }
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                **public,
                "schema_version": MAPPING_CANDIDATE_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception:
            # E2E拦截修复：GET兜底留真栈（此前零痕迹）。
            _logger.exception(
                "mapping-candidates GET failed (project=%s attempt=%s)",
                canonical, validated_attempt,
            )
            return _mapping_error("mapping_bridge_failed")

    @router.get(
        "/data-admissions/{attempt_id}/stage-state",
    )
    async def get_admission_stage_state(
        project_id: str,
        attempt_id: str,
        request: Request,
        response: Response,
    ) -> Any:
        """F5恢复=一次权威查询（02_DESIGN §5.4：stage-state投影端点）。

        projection权限（READ_SOURCE_EVIDENCE，无写门）；返回四阶段
        聚合视图供向导挂载恢复与轮询（If-None-Match: revision→304）。
        """

        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.READ_SOURCE_EVIDENCE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        confirmation = context.admission_mapping_confirmation
        workspace = context.workspace_dir(context.root, canonical)

        def _assemble() -> dict[str, Any]:
            from packages.medical_monitoring.admission.admission_stage_view import (
                build_stage_view,
            )
            from packages.medical_monitoring.admission.mapping_confirmation import (
                _unresolved_question_count,
            )
            from packages.medical_monitoring.admission.mapping_pipeline import (
                _generation_pace,
            )

            return _assemble_stage_state(
                project_id=canonical,
                attempt_id=validated_attempt,
                workspace_dir=workspace,
                pipeline=pipeline,
                confirmation=confirmation,
                build_stage_view=build_stage_view,
                unresolved_question_counter=_unresolved_question_count,
                pace_estimator=_generation_pace,
            )

        try:
            view = await run_in_threadpool(_assemble)
        except AdmissionStageViewError:
            return _mapping_error("mapping_bridge_failed")
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception:
            return _mapping_error("mapping_bridge_failed")
        if response is not None:
            etag = f'W/"{view.get("revision", 0)}"'
            if request.headers.get("if-none-match") == etag:
                from fastapi.responses import Response as FastResponse

                return FastResponse(status_code=304, headers={"ETag": etag})
            response.headers["ETag"] = etag
        return {"project_id": canonical, **view}

    @router.post(
        "/data-admissions/{attempt_id}/mapping-candidates/retry-failed",
        status_code=202,
    )
    async def retry_failed_mapping_candidates(
        project_id: str,
        attempt_id: str,
        request: Request,
    ) -> Any:
        # R32-04：识别分片终态失败（R32实测265片queue滞留收割）后，用户
        # 此前只剩「全部采纳/全部重来」两个极端选项——本路由提供显式
        # 重跑入口（可按表过滤），复用库层 retry_terminal（重置滞留
        # 基线），唤醒worker后由既有轮询自然收敛。
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.INTAKE_BATCH,
        )
        if isinstance(auth, JSONResponse):
            return auth
        pipeline = _pipeline_or_error()
        if isinstance(pipeline, JSONResponse):
            return pipeline
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        raw_body: Any = None
        if request.headers.get("content-length") not in ("", "0", None):
            try:
                raw_body = await request.json()
            except Exception:
                raw_body = None
        table_name = ""
        if isinstance(raw_body, dict):
            candidate_table = raw_body.get("table_name")
            if candidate_table is not None:
                if not isinstance(candidate_table, str):
                    return _mapping_error("mapping_retry_table_invalid")
                table_name = candidate_table.strip()
                if len(table_name) > 200:
                    return _mapping_error("mapping_retry_table_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = await run_in_threadpool(
                lambda: pipeline.retry_failed_candidates(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    workspace_dir=context.workspace_dir(context.root, canonical),
                    cohort="primary",
                    table_name=table_name,
                )
            )
            result = dict(result)
            # 公开投影不带作业身份（与mapping-candidates同规约）。
            result["requeued"] = [
                {k: v for k, v in item.items() if k != "job_id"}
                for item in result.get("requeued") or ()
            ]
            result["skipped"] = [
                {k: v for k, v in item.items() if k != "job_id"}
                for item in result.get("skipped") or ()
            ]
            return {
                "project_id": canonical,
                "attempt_id": validated_attempt,
                **result,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception:
            return _mapping_error("mapping_bridge_failed")
        finally:
            write_permit.release()

    @router.post(
        "/data-admissions/{attempt_id}/mapping-draft",
        status_code=201,
    )
    async def adopt_mapping_draft(
        project_id: str,
        attempt_id: str,
        request: Request,
        body: MappingDraftAdoptRequest,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.REVIEW_AI_CANDIDATE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        actor = getattr(auth, "principal_id", None) or body.actor
        confirmation = _confirmation_or_error()
        if isinstance(confirmation, JSONResponse):
            return confirmation
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            # R32-01：草稿采纳/修订/裁决/确认都落workspace存储与库层
            # 完整性门（R31-02槽位级校验），阻塞调用下放线程池。
            result = await run_in_threadpool(
                lambda: confirmation.adopt_draft(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    workspace_dir=context.workspace_dir(context.root, canonical),
                    actor=str(actor),
                    reason=body.reason,
                    allow_inflight_adoption=bool(body.include_incomplete),
                )
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                "attempt_id": validated_attempt,
                **public,
                "schema_version": MAPPING_CONFIRMATION_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception as exc:
            mapped = _repo_error_code(exc)
            if mapped:
                return _mapping_error(mapped)
            return _mapping_error("mapping_bridge_failed")
        finally:
            write_permit.release()

    @router.patch("/data-admissions/{attempt_id}/mapping-draft/field")
    async def edit_mapping_draft_field(
        project_id: str,
        attempt_id: str,
        request: Request,
        body: MappingDraftFieldEditRequest,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.REVIEW_AI_CANDIDATE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        actor = getattr(auth, "principal_id", None) or body.actor
        confirmation = _confirmation_or_error()
        if isinstance(confirmation, JSONResponse):
            return confirmation
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = await run_in_threadpool(
                lambda: confirmation.edit_field(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    draft_id=body.draft_id,
                    domain=body.domain,
                    source_field=body.source_field,
                    patch=body.patch,
                    expected_version=body.expected_version,
                    actor=str(actor),
                    idempotency_key=body.idempotency_key,
                )
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                **public,
                "schema_version": MAPPING_CONFIRMATION_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception as exc:
            mapped = _repo_error_code(exc)
            if mapped:
                return _mapping_error(mapped)
            return _mapping_error("mapping_bridge_failed")
        finally:
            write_permit.release()

    @router.post("/data-admissions/{attempt_id}/mapping-draft/adjudicate")
    async def adjudicate_mapping_draft(
        project_id: str,
        attempt_id: str,
        request: Request,
        body: MappingDraftAdjudicateRequest,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.REVIEW_AI_CANDIDATE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        confirmation = _confirmation_or_error()
        if isinstance(confirmation, JSONResponse):
            return confirmation
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        # R36轮（R36-01）：同草稿复核推进在途防重入——立即返回诚实running
        # 快照，不叠加昂贵对账（响应含draft_id，前端轮询状态机不断链）。
        if not _try_begin_adjudicate(canonical, body.draft_id):
            return {
                "project_id": canonical,
                "state": "adjudicating",
                "draft_id": body.draft_id,
                "adjudication": {"state": "running"},
                "schema_version": MAPPING_CONFIRMATION_SCHEMA_VERSION,
            }
        try:
            result = await run_in_threadpool(
                lambda: confirmation.adjudicate_draft(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    draft_id=body.draft_id,
                    workspace_dir=context.workspace_dir(context.root, canonical),
                )
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                **public,
                "schema_version": MAPPING_CONFIRMATION_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception as exc:
            mapped = _repo_error_code(exc)
            if mapped:
                return _mapping_error(mapped)
            return _mapping_error("mapping_bridge_failed")
        finally:
            _end_adjudicate(canonical, body.draft_id)
            write_permit.release()

    @router.post("/data-admissions/{attempt_id}/mapping-draft/confirm")
    async def confirm_mapping_draft(
        project_id: str,
        attempt_id: str,
        request: Request,
        body: MappingDraftConfirmRequest,
    ) -> Any:
        canonical = context.resolve_project(project_id)
        if isinstance(canonical, JSONResponse):
            return canonical
        auth = context.authorize(
            request,
            project_id=canonical,
            action=context.monitoring_action.REVIEW_AI_CANDIDATE,
        )
        if isinstance(auth, JSONResponse):
            return auth
        actor = (
            "system_harness"
            if body.automatic
            else getattr(auth, "principal_id", None) or body.confirmed_by
        )
        confirmation = _confirmation_or_error()
        if isinstance(confirmation, JSONResponse):
            return confirmation
        validated_attempt = _validated_attempt_id(attempt_id)
        if validated_attempt is None:
            return _mapping_error("mapping_attempt_id_invalid")
        try:
            write_permit = context.acquire_product_write_gate(canonical)
        except pb.ProjectBackupError as exc:
            return _run_entry_error_response(exc)
        try:
            result = await run_in_threadpool(
                lambda: confirmation.confirm_draft(
                    project_id=canonical,
                    attempt_id=validated_attempt,
                    draft_id=body.draft_id,
                    expected_version=body.expected_version,
                    confirmed_by=str(actor),
                    confirmation_reason=body.confirmation_reason,
                    idempotency_key=body.idempotency_key,
                    workspace_dir=context.workspace_dir(context.root, canonical),
                    allow_unverified_dual_review=bool(
                        body.allow_unverified_dual_review
                    ),
                )
            )
            public = _public_mapping_projection(result)
            if isinstance(public, JSONResponse):
                return public
            return {
                "project_id": canonical,
                **public,
                "schema_version": MAPPING_CONFIRMATION_SCHEMA_VERSION,
            }
        except AdmissionMappingPipelineError as exc:
            return _mapping_error(exc.code)
        except Exception as exc:
            mapped = _repo_error_code(exc)
            if mapped:
                return _mapping_error(mapped)
            _logger.exception(
                "mapping draft write failed (project=%s)", canonical,
            )
            return _mapping_error("mapping_bridge_failed")
        finally:
            write_permit.release()


__all__ = [
    "AdmissionMappingPipeline",
    "MAPPING_CANDIDATE_SCHEMA_VERSION",
    "MAPPING_CONFIRMATION_SCHEMA_VERSION",
    "MappingCandidateRouteContext",
    "DocumentAuthorityPromotionRequest",
    "MappingDraftAdjudicateRequest",
    "MappingDraftAdoptRequest",
    "MappingDraftConfirmRequest",
    "MappingDraftFieldEditRequest",
    "register_mapping_candidate_routes",
]
