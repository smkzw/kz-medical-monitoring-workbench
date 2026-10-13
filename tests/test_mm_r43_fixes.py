"""R43轮修复回归（R43-01/R43-02/R40-05）。

R43-01（critical）：研究文件核对作业队列零执行死锁——A/B两位独立复现，
核对作业入队45-55分钟零认领（attempt_count=0），最终queue_dwell_timeout
收割，显式重试依旧零执行。根因（ISO sqlite只读诊断钉死）：盲核侧是与
批量字段映射分片共享的identity-bound单worker串行池，claim_next按纯
created_at FIFO排序——另一项目8小时前的70个映射分片积压把刚入队的
核对作业顶到数小时之后（期间worker每3-6分钟完成一个更早的分片，
从未空闲）。修复：同一身份内交互式研究文件核对作业
（document_authority_analysis/review）优先认领；批量分片吞吐顺序不变。

R43-02（high）：「重新核对研究文件」按钮对零执行的queued作业是完全
无操作（_recover_failed_once只处理终态失败），两次点击前后界面逐字
不变。修复：①queued作业显式重试时重置dwell基线真实重新计时；
②advance响应携带受理回执（重排/重新计时的作业与受理时刻）；
③前端回显确认并把等待/停滞计时切到受理时刻。

R40-05（medium）：MH域完全不参与风险标记与发现生成——空术语行静默
（24008实测零提示）、MH→CM方向无人检查（23003有甲减史无左甲状腺素
未报，反向24012已报）。修复：①空术语进「待核实」发现；②替代治疗类
疾病（甲减↔左甲状腺素）按受试者去重后提示核实。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from packages.medical_monitoring.projections.facts_publication import (
    FactsPublicationAuthorityProvider,
)
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiInputRevision,
    MonitoringAiJobCreate,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app.monitoring_document_authority_workflow import (
    MonitoringDocumentAuthorityWorkflow,
)


class _FakeClock:
    def __init__(self) -> None:
        self._now = datetime(2026, 10, 13, 21, 30, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now = self._now + timedelta(seconds=seconds)


_IDENTITY = dict(
    profile_id="medical_monitoring_verifier_ai__profile-1",
    provider="cms-router",
    requested_model="glm-5.3-flash",
)


def _create_request(
    *,
    task_type: MonitoringAiTaskType = MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    project_id: str = "proj_r43",
    business_key: str = "listing-field-mapping-verifier:stg-1:DM:0001-of-0070",
    prompt_version: str = "verifier-prompt",
) -> MonitoringAiJobCreate:
    return MonitoringAiJobCreate(
        project_id=project_id,
        task_type=task_type,
        business_key=business_key,
        input_revision=MonitoringAiInputRevision(
            project_id=project_id,
            batch_revision="batch-1",
            sources=(
                MonitoringAiSourceBinding(
                    source_entry_id="file-1",
                    source_content_sha256="a" * 64,
                ),
            ),
        ),
        input_payload={"batch_id": "stg-1"},
        prompt_version=prompt_version,
        max_attempts=2,
        **_IDENTITY,
    )


# ---------------------------------------------------------------------------
# R43-01：同一身份内研究文件核对作业优先于批量积压被认领
# ---------------------------------------------------------------------------


def test_claim_next_prioritizes_document_authority_over_stale_batch_backlog(
    tmp_path: Path,
) -> None:
    """R43-01核心场景：8小时前入队的映射分片积压在前，刚入队的研究文件
    核对作业（更新created_at）必须先被认领——串行worker不再让它排队
    数小时直到dwell收割。"""

    clock = _FakeClock()
    repo = MonitoringAiRepository(tmp_path / "ai.sqlite3", clock=clock)
    backlog = []
    for i in range(3):
        backlog.append(
            repo.create_or_get(
                _create_request(
                    business_key=f"listing-field-mapping-verifier:stg-1:DM:{i:04d}-of-0070"
                )
            )
        )
        # 逐条推进时钟：同刻创建的作业以job_id做平局裁决，这里让
        # created_at严格有序以匹配真实积压形态（先入队者在前）。
        clock.advance(seconds=1)
    clock.advance(seconds=297)
    interactive = repo.create_or_get(
        _create_request(
            task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS,
            business_key="document-authority-analysis:verifier:v9:mmbatch_556f",
            prompt_version="monitoring-document-authority-verifier-v9",
        )
    )

    claimed = repo.claim_next("verifier-worker", **_IDENTITY)
    assert claimed is not None
    assert claimed.job_id == interactive.job_id, (
        "研究文件核对作业必须跳过更早的批量分片积压被优先认领"
    )

    # 交互作业离开队列后，批量分片恢复既有FIFO顺序。
    second = repo.claim_next("verifier-worker", **_IDENTITY)
    assert second is not None
    assert second.job_id == backlog[0].job_id
    third = repo.claim_next("verifier-worker", **_IDENTITY)
    assert third is not None
    assert third.job_id == backlog[1].job_id


def test_claim_next_priority_also_applies_to_unfiltered_claim(
    tmp_path: Path,
) -> None:
    """无身份参数的历史认领路径共享同一排序契约（两cohort各自的
    identity-bound认领与旧路径行为一致）。"""

    clock = _FakeClock()
    repo = MonitoringAiRepository(tmp_path / "ai.sqlite3", clock=clock)
    repo.create_or_get(_create_request(business_key="mapping-old"))
    clock.advance(seconds=120)
    review = repo.create_or_get(
        _create_request(
            task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_REVIEW,
            business_key="document-authority-review:verifier:abc",
            prompt_version="monitoring-document-authority-verifier-review-v1",
        )
    )
    claimed = repo.claim_next("worker-a")
    assert claimed is not None
    assert claimed.job_id == review.job_id


# ---------------------------------------------------------------------------
# R43-02：显式重核对的受理回执与queued作业重新计时
# ---------------------------------------------------------------------------


def test_reset_queued_jobs_dwell_resets_only_queued_rows(tmp_path: Path) -> None:
    clock = _FakeClock()
    repo = MonitoringAiRepository(tmp_path / "ai.sqlite3", clock=clock)
    queued = repo.create_or_get(_create_request(business_key="queued-1"))
    clock.advance(seconds=1)
    other_project = repo.create_or_get(
        _create_request(business_key="queued-2", project_id="proj_other")
    )
    repo.claim_next("worker-a", **_IDENTITY)  # 最早的queued-1 → running
    clock.advance(seconds=600)

    reset = repo.reset_queued_jobs_dwell(
        queued.project_id, [queued.job_id, other_project.job_id, "monai_missing"]
    )
    assert reset == (), "running/跨项目/不存在的原样跳过"

    running_row = repo.get(queued.project_id, queued.job_id)
    assert running_row.status == MonitoringAiJobStatus.RUNNING
    assert queued_dwell_oldest(repo, queued.project_id) == ""


def queued_dwell_oldest(repo: MonitoringAiRepository, project_id: str) -> str:
    return repo.queued_dwell_oldest(project_id=project_id)


def test_explicit_retry_receipt_resets_queued_dwell_and_reports(
    tmp_path: Path,
) -> None:
    """零执行滞留（queued）作业点击「重新核对研究文件」：dwell基线真实
    重置并返回受理回执——按钮不再是完全无操作。"""

    clock = _FakeClock()
    repo = MonitoringAiRepository(tmp_path / "ai.sqlite3", clock=clock)
    job = repo.create_or_get(_create_request(business_key="doc-verifier-stuck"))
    clock.advance(seconds=1800)  # 滞留基线已流逝30分钟

    wakes: list[int] = []
    workflow = MonitoringDocumentAuthorityWorkflow(
        repo,
        primary_service=SimpleNamespace(),
        verifier_service=SimpleNamespace(),
        source_registry=SimpleNamespace(),
        worker_wake=lambda: wakes.append(1),
    )
    row = repo.get(job.project_id, job.job_id)
    receipt = workflow._explicit_retry_receipt((row,), [])

    assert receipt["requeued_jobs"] == []
    assert receipt["dwell_reset_jobs"] == [job.business_key]
    assert receipt["accepted_at"]
    assert wakes, "重新计时后唤醒worker尽快认领"
    # dwell基线确实重置到当前时刻（收割按基线计时，显式重试后重新计时）。
    oldest = repo.queued_dwell_oldest(project_id=job.project_id)
    assert oldest.startswith("2026-10-13T22:00"), oldest


def test_explicit_retry_receipt_empty_when_jobs_running(
    tmp_path: Path,
) -> None:
    """作业执行中时回执如实说明「无需重排」，不虚报动作。"""

    clock = _FakeClock()
    repo = MonitoringAiRepository(tmp_path / "ai.sqlite3", clock=clock)
    job = repo.create_or_get(_create_request(business_key="doc-verifier-running"))
    repo.claim_next("worker-a", **_IDENTITY)
    row = repo.get(job.project_id, job.job_id)

    workflow = MonitoringDocumentAuthorityWorkflow(
        repo,
        primary_service=SimpleNamespace(),
        verifier_service=SimpleNamespace(),
        source_registry=SimpleNamespace(),
        worker_wake=lambda: None,
    )
    receipt = workflow._explicit_retry_receipt((row,), [])
    assert receipt["requeued_jobs"] == []
    assert receipt["dwell_reset_jobs"] == []
    assert receipt["accepted_at"]


# ---------------------------------------------------------------------------
# R40-05：MH域参与风险标记与发现生成
# ---------------------------------------------------------------------------


def _workspace(tmp_path: Path, tables: dict[str, list[dict]]) -> Path:
    from tests.test_facts_publication_event_time import _workspace as _build

    return _build(tmp_path, tables)


def _risks_by_domain(tmp_path: Path, tables: dict[str, list[dict]], domain: str):
    workspace = _workspace(tmp_path, tables)
    provider = FactsPublicationAuthorityProvider(workspace)
    packet = provider.get_packet("proj-test", snapshot_ref="facts-snapshot-001")
    return [r for r in packet.risks if r.domain == domain]


def test_mh_empty_term_record_produces_quality_finding(tmp_path: Path) -> None:
    """R40-05①：24008形态——MH行仅「既往病史」类别、无诊断名——
    此前静默展示零提示，现在进「待核实」发现（中等级）。"""

    risks = _risks_by_domain(
        tmp_path,
        {
            "MH": [
                {
                    "SUBJID": "24008",
                    "MHNUM": "M001",
                    "MHCAT": "既往病史",
                    "MHTERM": "",
                    "MHSTDAT": "2020-05-01",
                },
            ],
        },
        "mh",
    )
    assert any(
        "缺诊断名称" in (r.medical_note or "") for r in risks
    ), [r.medical_note for r in risks]
    flagged = next(r for r in risks if "缺诊断名称" in (r.medical_note or ""))
    assert flagged.severity == "medium"


def test_mh_history_without_matching_medication_flags(tmp_path: Path) -> None:
    """R40-05②：23003形态——有甲减史但CM无左甲状腺素——MH→CM方向
    检出中等级核实提示（与已实现的CM→MH方向对称）。"""

    risks = _risks_by_domain(
        tmp_path,
        {
            "MH": [
                {
                    "SUBJID": "23003",
                    "MHNUM": "M001",
                    "MHTERM": "甲状腺功能减退",
                    "MHSTDAT": "2019-01-01",
                },
            ],
            "CM": [
                {
                    "SUBJID": "23003",
                    "CMNUM": "C001",
                    "CMTRT": "氨氯地平片",
                    "CMINDC": "高血压",
                    "CMSTDAT": "2026-01-10",
                },
            ],
        },
        "mh",
    )
    assert any(
        "病史与用药一致性待核实" in (r.medical_note or "")
        and "甲状腺功能减退" in (r.medical_note or "")
        for r in risks
    ), [r.medical_note for r in risks]
    flagged = next(
        r for r in risks if "病史与用药一致性待核实" in (r.medical_note or "")
    )
    assert flagged.severity == "medium"


def test_mh_history_with_brand_medication_stays_silent(tmp_path: Path) -> None:
    """用药侧以品牌名（优甲乐）登记时视为已覆盖，不制造发现。"""

    risks = _risks_by_domain(
        tmp_path,
        {
            "MH": [
                {
                    "SUBJID": "23004",
                    "MHTERM": "甲减",
                    "MHSTDAT": "2019-01-01",
                },
            ],
            "CM": [
                {
                    "SUBJID": "23004",
                    "CMTRT": "优甲乐",
                    "CMINDC": "既往用药",
                },
            ],
        },
        "mh",
    )
    assert not any(
        "病史与用药一致性待核实" in (r.medical_note or "") for r in risks
    ), [r.medical_note for r in risks]


def test_mh_overbroad_history_terms_do_not_flag(tmp_path: Path) -> None:
    """触发词收窄：「甲状腺结节」等过宽病史不构成左甲状腺素缺失信号。"""

    risks = _risks_by_domain(
        tmp_path,
        {
            "MH": [
                {
                    "SUBJID": "23005",
                    "MHTERM": "甲状腺结节",
                    "MHSTDAT": "2019-01-01",
                },
            ],
            "CM": [
                {
                    "SUBJID": "23005",
                    "CMTRT": "氨氯地平片",
                    "CMINDC": "高血压",
                },
            ],
        },
        "mh",
    )
    assert not any(
        "病史与用药一致性待核实" in (r.medical_note or "") for r in risks
    ), [r.medical_note for r in risks]


def test_mh_cm_direction_deduplicates_per_subject_and_condition(
    tmp_path: Path,
) -> None:
    """同受试者同疾病的多条病史行只产出一条核实提示（不批量刷屏）。"""

    risks = _risks_by_domain(
        tmp_path,
        {
            "MH": [
                {
                    "SUBJID": "23006",
                    "MHNUM": "M001",
                    "MHTERM": "甲状腺功能减退",
                    "MHSTDAT": "2019-01-01",
                },
                {
                    "SUBJID": "23006",
                    "MHNUM": "M002",
                    "MHTERM": "甲减",
                    "MHSTDAT": "2019-06-01",
                },
            ],
        },
        "mh",
    )
    flagged = [
        r for r in risks
        if "病史与用药一致性待核实" in (r.medical_note or "")
    ]
    assert len(flagged) == 1, [r.medical_note for r in flagged]
