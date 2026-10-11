"""R29-01：核对队列滞留作业超时收割回归。

背景：R29实测一条 document_authority_analysis 作业在「失败→重试→再排队」
循环中滞留≥5.7小时，队列横幅持续显示「队列中」而无终态——租约超时与
attempt预算只管单次执行与自动恢复次数，管不住queued侧循环占用。修复：
- 仓库新增 fail_queued_jobs_exceeding_dwell：超dwell_since基线的queued作业
  落failed（queue_dwell_timeout、retryable=1）终态；暂停项目不收割。
- 显式重试（产品动作）重置基线重新计时；自动恢复不重置。
- 存量行（无dwell_since）按created_at兜底计时。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from services.api.app.monitoring_ai_contracts import (
    MonitoringAiInputRevision,
    MonitoringAiJobCreate,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (
    MonitoringAiJobStatus,
    MonitoringAiRepository,
)


class _FakeClock:
    """可手动推进的时钟（ISO UTC），模拟滞留时长。"""

    def __init__(self) -> None:
        self._now = datetime(2026, 10, 9, 3, 44, 7, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now = self._now + timedelta(seconds=seconds)


def _create_request(
    project_id: str = "proj_dwell",
    business_key: str = "document-authority-analysis:primary:g01:b1",
) -> MonitoringAiJobCreate:
    return MonitoringAiJobCreate(
        project_id=project_id,
        task_type=MonitoringAiTaskType.DOCUMENT_AUTHORITY_ANALYSIS,
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
        input_payload={"batch_id": "batch-1"},
        prompt_version="p1",
        profile_id="profile-1",
        provider="test-provider",
        requested_model="test-model",
        max_attempts=2,
    )


def _make_repository(
    tmp_path: Path,
    clock: _FakeClock,
    dwell_timeout: int = 7200,
) -> MonitoringAiRepository:
    return MonitoringAiRepository(
        tmp_path / "monitoring_ai.sqlite3",
        lease_seconds=300,
        queue_dwell_timeout_seconds=dwell_timeout,
        clock=clock,
    )


def _raw_dwell_since(repo: MonitoringAiRepository, job_id: str) -> str:
    with sqlite3.connect(repo.path) as connection:
        row = connection.execute(
            "SELECT dwell_since FROM monitoring_ai_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    return str(row[0]) if row and row[0] else ""


def test_queued_job_beyond_dwell_threshold_is_failed_with_retryable_terminal(
    tmp_path: Path,
) -> None:
    clock = _FakeClock()
    repo = _make_repository(tmp_path, clock)
    job = repo.create_or_get(_create_request())
    assert job.status is MonitoringAiJobStatus.QUEUED
    baseline = _raw_dwell_since(repo, job.job_id)
    assert baseline != ""

    # 推进2小时+1秒：正好越过默认阈值
    clock.advance(7201)
    reaped = repo.fail_queued_jobs_exceeding_dwell()
    assert reaped == 1

    final = repo.get(job.project_id, job.job_id)
    assert final.status is MonitoringAiJobStatus.FAILED
    assert final.failure_code == "queue_dwell_timeout"
    assert "滞留" in final.failure_message
    assert int(final.retryable) == 1
    # 终态后不再被计为队列中（最早滞留基线投影清空）
    assert repo.queued_dwell_oldest(project_id=job.project_id) == ""


def test_young_queued_job_is_not_reaped(tmp_path: Path) -> None:
    clock = _FakeClock()
    repo = _make_repository(tmp_path, clock)
    job = repo.create_or_get(_create_request())
    clock.advance(3600)  # 1小时 < 2小时阈值
    assert repo.fail_queued_jobs_exceeding_dwell() == 0
    untouched = repo.get(job.project_id, job.job_id)
    assert untouched.status is MonitoringAiJobStatus.QUEUED
    assert untouched.failure_code == ""


def test_explicit_retry_resets_dwell_baseline_automatic_recovery_does_not(
    tmp_path: Path,
) -> None:
    clock = _FakeClock()
    repo = _make_repository(tmp_path, clock)
    job = repo.create_or_get(_create_request())
    input_sha = job.input_revision_sha256

    # 执行一次并不可重试失败（attempt 1/2 直接落 FAILED 终态）
    claimed = repo.claim_next("owner-1")
    assert claimed is not None and claimed.job_id == job.job_id
    failed_once = repo.fail(
        claimed,
        owner="owner-1",
        failure_code="provider_runtime_error",
        failure_message="upstream 429",
        retryable=False,
    )
    assert failed_once.status is MonitoringAiJobStatus.FAILED
    baseline_before = _raw_dwell_since(repo, job.job_id)

    # 显式重试（automatic_recovery_limit=None，产品动作）：基线重置为当下
    clock.advance(7000)
    assert repo.retry_terminal(
        job.project_id,
        job.job_id,
        current_input_revision_sha256=input_sha,
        automatic_recovery_limit=None,
    ).status is MonitoringAiJobStatus.QUEUED
    baseline_after = _raw_dwell_since(repo, job.job_id)
    assert baseline_after > baseline_before

    # 重置后再推进1小时（总时间线远超阈值，但基线是新的）：不得收割
    clock.advance(3600)
    assert repo.fail_queued_jobs_exceeding_dwell() == 0
    assert repo.get(job.project_id, job.job_id).status is MonitoringAiJobStatus.QUEUED

    # 对照组：自动恢复路径不重置基线——再落失败终态后走自动恢复（预算内），
    # 推进超过阈值后应被收割。
    claimed2 = repo.claim_next("owner-2")
    assert claimed2 is not None
    repo.fail(
        claimed2,
        owner="owner-2",
        failure_code="provider_runtime_error",
        failure_message="upstream 429 again",
        retryable=False,
    )
    baseline_before_auto = _raw_dwell_since(repo, job.job_id)
    clock.advance(600)
    assert repo.retry_terminal(
        job.project_id,
        job.job_id,
        current_input_revision_sha256=input_sha,
        automatic_recovery_limit=3,
    ).status is MonitoringAiJobStatus.QUEUED
    assert _raw_dwell_since(repo, job.job_id) == baseline_before_auto

    clock.advance(7201)
    assert repo.fail_queued_jobs_exceeding_dwell() == 1
    final = repo.get(job.project_id, job.job_id)
    assert final.status is MonitoringAiJobStatus.FAILED
    assert final.failure_code == "queue_dwell_timeout"


def test_paused_project_queue_is_not_reaped(tmp_path: Path) -> None:
    clock = _FakeClock()
    repo = _make_repository(tmp_path, clock)
    job = repo.create_or_get(_create_request())
    repo.set_queue_paused(job.project_id, paused=True)
    clock.advance(7201)
    assert repo.fail_queued_jobs_exceeding_dwell() == 0
    assert repo.get(job.project_id, job.job_id).status is MonitoringAiJobStatus.QUEUED


def test_legacy_row_without_dwell_since_falls_back_to_created_at(
    tmp_path: Path,
) -> None:
    clock = _FakeClock()
    repo = _make_repository(tmp_path, clock)
    job = repo.create_or_get(_create_request())
    # 模拟升级前的存量行：dwell_since 为空
    with sqlite3.connect(repo.path) as connection:
        connection.execute(
            "UPDATE monitoring_ai_jobs SET dwell_since = '' WHERE job_id = ?",
            (job.job_id,),
        )
    clock.advance(7201)
    assert repo.fail_queued_jobs_exceeding_dwell() == 1
    assert (
        repo.get(job.project_id, job.job_id).failure_code == "queue_dwell_timeout"
    )
    # 诊断投影对存量行回落created_at（新作业入队后投影非空）
    clock.advance(1)
    repo.create_or_get(
        _create_request(
            business_key="document-authority-analysis:primary:g01:b2",
        )
    )
    assert repo.queued_dwell_oldest(project_id=job.project_id) != ""


def test_dwell_horizon_widens_with_queue_depth_r34_07(tmp_path: Path) -> None:
    """R35轮（R34-07）：大工作簿分片风暴不得被固定视界误收割。

    R34实测：54表工作簿一次性入队129个识别分片，单worker串行消费下
    队尾排队2-4小时，52/54张表被queue_dwell_timeout打为终态失败——
    字段映射无法生成，医学监查全链阻断。视界必须随在队深度放宽：
    基线 + (在队数-1)×单作业预算。此处以10个分片+180s/分片预算复现：
    基线2小时+1秒（旧固定视界必收割）时10分片队列一个都不收割；
    视界=7200+9×180=8820s，推进8821s后全部收割（兜底仍存在）。
    """

    clock = _FakeClock()
    repo = MonitoringAiRepository(
        tmp_path / "monitoring_ai.sqlite3",
        lease_seconds=300,
        queue_dwell_timeout_seconds=7200,
        queue_dwell_seconds_per_queued_job=180,
        clock=clock,
    )
    jobs = [
        repo.create_or_get(
            _create_request(
                business_key=(
                    "listing-field-mapping:batch-1:DM:"
                    f"{index:04d}-of-0010"
                ),
            )
        )
        for index in range(1, 11)
    ]
    assert all(job.status is MonitoringAiJobStatus.QUEUED for job in jobs)

    # 推进7201s：旧固定视界下整队必被收割；新语义视界8820s——不得收割。
    clock.advance(7201)
    assert repo.fail_queued_jobs_exceeding_dwell() == 0
    assert all(
        repo.get(job.project_id, job.job_id).status
        is MonitoringAiJobStatus.QUEUED
        for job in jobs
    )

    # 推进越过动态视界（累计8821s）：兜底仍生效，整队收割为可重试终态。
    clock.advance(1620)
    reaped = repo.fail_queued_jobs_exceeding_dwell()
    assert reaped == 10
    final_jobs = [repo.get(job.project_id, job.job_id) for job in jobs]
    assert all(job.status is MonitoringAiJobStatus.FAILED for job in final_jobs)
    assert all(
        job.failure_code == "queue_dwell_timeout" for job in final_jobs
    )
    assert all(int(job.retryable) == 1 for job in final_jobs)


def test_dwell_horizon_is_per_project_and_loop_guard_keeps_base(
    tmp_path: Path,
) -> None:
    """R35轮（R34-07）补：①视界按项目分组——别的项目队列深不放宽本项目；
    ②单作业循环重排（R29-01场景）视界仍=基线，循环兜底语义不变。"""

    clock = _FakeClock()
    repo = MonitoringAiRepository(
        tmp_path / "monitoring_ai.sqlite3",
        lease_seconds=300,
        queue_dwell_timeout_seconds=7200,
        queue_dwell_seconds_per_queued_job=180,
        clock=clock,
    )
    # proj_busy：9个分片在队（不该影响proj_single的收割视界）。
    for index in range(1, 10):
        repo.create_or_get(
            _create_request(
                project_id="proj_busy",
                business_key=f"listing-field-mapping:batch-1:DM:{index:04d}",
            )
        )
    single = repo.create_or_get(
        _create_request(project_id="proj_single")
    )
    clock.advance(7201)
    # proj_single只有1个在队作业：视界=基线7200s，应被收割——若跨项目
    # 污染（按全库在队10算视界8820s）则此处收割为0。
    assert repo.fail_queued_jobs_exceeding_dwell(project_id="proj_single") == 1
    final = repo.get("proj_single", single.job_id)
    assert final.status is MonitoringAiJobStatus.FAILED
    assert final.failure_code == "queue_dwell_timeout"
    # proj_busy的9个分片不受影响（视界7200+8×180=8640s尚未到）。
    assert repo.fail_queued_jobs_exceeding_dwell(project_id="proj_busy") == 0
    busy_jobs = repo.list_jobs("proj_busy")
    assert len(busy_jobs) == 9
    assert all(job.status is MonitoringAiJobStatus.QUEUED for job in busy_jobs)
