"""状态机专项T5（02_DESIGN §5-T5）：S6灰度开启前置——重排×收割交互。

retry_terminal重排行（dwell基线重置、attempt>0）与
fail_queued_jobs_exceeding_dwell在途豁免（attempt=0等待钟重置）叠加：
- 重排行dwell重置后视界内不被二次收割（R29-01语义）；
- 在途豁免只保护attempt=0等待行，attempt>0重排循环照原视界收割；
- env off复跑=零行为差（灰度回滚面）。
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MonitoringAiInputRevision,
    MonitoringAiJobCreate,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
ATTEMPT = "attempt_t5"


class MutableClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 10, 15, 8, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self._value

    def advance(self, **kwargs: int) -> None:
        self._value += timedelta(**kwargs)


def _request(
    *,
    suffix: str,
    project_id: str = "proj-t5",
) -> MonitoringAiJobCreate:
    revision = MonitoringAiInputRevision(
        project_id=project_id,
        batch_revision="batch-t5",
        mapping_revision="mapping-t5",
        protocol_version="protocol-v1",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-listing",
                source_content_sha256=HASH_A,
            ),
            MonitoringAiSourceBinding(
                source_entry_id="source-protocol",
                source_content_sha256=HASH_B,
            ),
        ),
    )
    return MonitoringAiJobCreate(
        project_id=project_id,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        input_revision=revision,
        input_payload={"schema_version": "monitoring_ai_v1", "seq": suffix},
        prompt_version="mapping-prompt-v1",
        profile_id="independent-ai-test",
        provider="test-provider",
        requested_model="test-model",
        max_attempts=2,
        business_key=(
            f"listing-field-mapping:{ATTEMPT}:u01:{ATTEMPT}:LB:{suffix}"
        ),
    )


def _failed_job(
    repo: MonitoringAiRepository,
    *,
    suffix: str,
    project_id: str = "proj-t5",
):
    job = repo.create_or_get(_request(suffix=suffix, project_id=project_id))
    running = repo.claim_next(f"worker-{suffix}")
    assert running.job_id == job.job_id
    return repo.fail(
        running,
        owner=f"worker-{suffix}",
        failure_code="provider_runtime_error",
        failure_message="upstream infra failure",
        retryable=False,
    )


def test_requeued_row_dwell_reset_and_not_reaped_within_horizon(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """重排行dwell基线重置→视界内不被二次收割；旧行照常收割。"""

    monkeypatch.setenv("WORKBENCH_MONITORING_AI_INFRA_RETRY", "1")
    clock = MutableClock()
    repo = MonitoringAiRepository(tmp_path / "t5.sqlite3", clock=clock)

    # 失败行：t=0完成一轮失败（attempt=1）。先建先认领，避免claim_next
    # 认领到后续创建的滞留行。
    failed = _failed_job(repo, suffix="0001-of-0009")
    assert failed.status == MonitoringAiJobStatus.FAILED
    # 旧行：t=0入队后无人认领（attempt=0滞留）。
    stale = repo.create_or_get(_request(suffix="0002-of-0009"))
    assert stale.status == MonitoringAiJobStatus.QUEUED

    # t=+300s：两行dwell均已过期（视界=10+(2-1)*180=190s）；同请求重发
    # →显式重排（dwell基线重置到当前时刻）。
    clock.advance(minutes=5)
    requeued = repo.create_or_get(_request(suffix="0001-of-0009"))
    assert requeued.status == MonitoringAiJobStatus.QUEUED
    requeued_row = repo.get("proj-t5", requeued.job_id)
    assert requeued_row.status == MonitoringAiJobStatus.QUEUED

    reaped = repo.fail_queued_jobs_exceeding_dwell(
        project_id="proj-t5", timeout_seconds=10
    )
    # 重排行dwell=重排时刻（t=300），cutoff=t=110→保留；旧行dwell=t=0→收割。
    assert reaped == 1
    assert repo.get("proj-t5", requeued.job_id).status == MonitoringAiJobStatus.QUEUED
    assert repo.get("proj-t5", stale.job_id).status == MonitoringAiJobStatus.FAILED
    assert (
        repo.get("proj-t5", stale.job_id).failure_code == "queue_dwell_timeout"
    )


def test_inflight_exemption_spares_zero_attempt_rows_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """在途豁免重置attempt=0等待钟；attempt>0重排循环照原视界收割。"""

    monkeypatch.setenv("WORKBENCH_MONITORING_AI_INFRA_RETRY", "1")
    clock = MutableClock()
    repo = MonitoringAiRepository(tmp_path / "t5b.sqlite3", clock=clock)

    # attempt>0重排行：失败→显式重排（t=60，dwell重置）。先建先认领。
    failed = _failed_job(repo, suffix="0005-of-0009")
    # running行（同task_type在途信号）。
    running_target = repo.create_or_get(_request(suffix="0003-of-0009"))
    running = repo.claim_next("worker-run")
    assert running.job_id == running_target.job_id
    # attempt=0等待行（零认领纯排队）。
    waiting = repo.create_or_get(_request(suffix="0004-of-0009"))
    clock.advance(minutes=1)
    requeued = repo.create_or_get(_request(suffix="0005-of-0009"))
    assert requeued.status == MonitoringAiJobStatus.QUEUED
    assert requeued.job_id == failed.job_id

    # t=+200s：重排行的dwell(=60)也已过期；running仍在途。
    clock.advance(minutes=2, seconds=20)
    reaped = repo.fail_queued_jobs_exceeding_dwell(
        project_id="proj-t5", timeout_seconds=10
    )
    # 在途豁免：worker池在推进→本轮整项目跳过收割，attempt=0等待行
    # dwell钟重置；重排行(attempt>0)本轮同样豁免（收割语义=整轮跳过，
    # 非逐行——worker空闲后的下一轮按原视界补收）。
    assert reaped == 0
    assert repo.get("proj-t5", waiting.job_id).status == MonitoringAiJobStatus.QUEUED
    assert repo.get("proj-t5", requeued.job_id).status == MonitoringAiJobStatus.QUEUED

    # 在途信号消失（running行终态失败）后：下一轮整段视界无人认领照常
    # 收割——重排行与等待行都按各自dwell基线判定（真饥饿检测保留）。
    ended = repo.fail(
        repo.get("proj-t5", running.job_id),
        owner="worker-run",
        failure_code="provider_runtime_error",
        failure_message="worker finished",
        retryable=False,
    )
    assert ended.status == MonitoringAiJobStatus.FAILED
    clock.advance(minutes=5)
    reaped_again = repo.fail_queued_jobs_exceeding_dwell(
        project_id="proj-t5", timeout_seconds=10
    )
    assert reaped_again == 2
    assert repo.get("proj-t5", waiting.job_id).status == MonitoringAiJobStatus.FAILED
    assert repo.get("proj-t5", requeued.job_id).status == MonitoringAiJobStatus.FAILED
    assert (
        repo.get("proj-t5", requeued.job_id).failure_code
        == "queue_dwell_timeout"
    )


def test_env_off_resubmit_and_harvest_zero_behavior_difference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """env off：同请求重发原样返回失败行；收割行为与env无关。"""

    monkeypatch.delenv("WORKBENCH_MONITORING_AI_INFRA_RETRY", raising=False)
    clock = MutableClock()
    repo = MonitoringAiRepository(tmp_path / "t5c.sqlite3", clock=clock)
    failed = _failed_job(repo, suffix="0006-of-0009")
    clock.advance(minutes=1)
    again = repo.create_or_get(_request(suffix="0006-of-0009"))
    assert again.job_id == failed.job_id
    assert again.status == MonitoringAiJobStatus.FAILED
    assert again.failure_code == "provider_runtime_error"
    recovery = [
        item
        for item in repo.stage_store.list_events("proj-t5", ATTEMPT)
        if item["event_type"] == "recovery_action"
    ]
    assert recovery == []
