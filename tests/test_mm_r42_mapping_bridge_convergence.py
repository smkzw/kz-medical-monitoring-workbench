"""R42轮（R42-01）：映射确认链「桥接确定性失败」根因回归。

R42B实测（ISO sqlite只读诊断）：10个verifier盲核分片8个
``queue_dwell_timeout`` 终态失败且 ``attempt_count=0``（从未被执行）——
R34-07动态视界=基线+(在队数-1)×180s随完成逐轮收缩，而dwell基线固定在
入队时刻；盲核侧是identity-bound单worker串行池、重思考分片单耗时
5-30+分钟，排空速度追不上视界收缩，健康队列的队尾被确定性误收割。
字段映射确认（reconcile_with_verifier）因此8连败
（mapping_bridge_failed / mapping_verifier_job_failed交替），用户唯一
出路是「不等待复核，知情降级确认」。

钉住的契约：
1. 队列在本视界内有过「完成」（真实排空中）不收割——视界内零完成的
   滞留场景（R29-01循环、R31饥饿、R34-07风暴兜底）语义不变。
2. 降级确认把被绕过的盲核缺口转为事后补偿：终态失败的verifier分片
   就地重新排队（best-effort，失败不阻塞已留痕的确认），公开投影
   透出补偿回执（聚合计数、无作业身份）。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

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
    def __init__(self) -> None:
        self._now = datetime(2026, 10, 13, 17, 21, 27, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now = self._now + timedelta(seconds=seconds)


def _create_request(
    project_id: str = "proj_r42",
    business_key: str = "listing-field-mapping-verifier:stg-1:DM:0001-of-0010",
) -> MonitoringAiJobCreate:
    return MonitoringAiJobCreate(
        project_id=project_id,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
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
        prompt_version="verifier-prompt",
        profile_id="profile-1",
        provider="cms-router",
        requested_model="glm-5.3-flash",
        max_attempts=2,
    )


def _make_repository(tmp_path: Path, clock: _FakeClock) -> MonitoringAiRepository:
    return MonitoringAiRepository(
        tmp_path / "monitoring_ai.sqlite3",
        lease_seconds=300,
        # R42实测生产口径：基线45分钟、180s/在队作业。
        queue_dwell_timeout_seconds=2700,
        queue_dwell_seconds_per_queued_job=180,
        clock=clock,
    )


def _complete_row(repo: MonitoringAiRepository, job_id: str) -> None:
    """测试辅助：把作业行置为completed（updated_at=当前时钟）。

    只驱动收割语义关注的（status, updated_at），不构造完整AI执行回执。
    """

    import sqlite3

    completed_at = repo.clock().isoformat()
    with sqlite3.connect(repo.path) as connection:
        connection.execute(
            """
            UPDATE monitoring_ai_jobs
            SET status = 'completed',
                updated_at = ?,
                lease_owner = '', lease_expires_at = ''
            WHERE job_id = ?
            """,
            (completed_at, job_id),
        )


def test_draining_queue_with_recent_completions_is_not_reaped(
    tmp_path: Path,
) -> None:
    """慢而真实排空的盲核队列不得被收割（R42B确定性误收割回归）。

    10个分片、单worker串行、每片耗时30分钟（>180s/分片预算）：老语义下
    视界=2700+9×180=4320s，第一片完成前无人被收割，但完成使在队数下降
    →视界收缩→68分钟后（R42B实测时刻）队尾被收割。新语义：每次完成都
    落在当前视界内=队列在排空，整队活到全部完成。
    """

    clock = _FakeClock()
    repo = _make_repository(tmp_path, clock)
    jobs = [
        repo.create_or_get(
            _create_request(
                business_key=(
                    "listing-field-mapping-verifier:stg-1:DM:"
                    f"{index:04d}-of-0010"
                ),
            )
        )
        for index in range(1, 11)
    ]

    # 串行排空：每30分钟完成一片（慢于180s/片预算、快于基线+深度视界）。
    for index, job in enumerate(jobs):
        if index > 0:
            clock.advance(1800)  # 30分钟一片
        _complete_row(repo, job.job_id)
        # 每次完成后再跑一次收割（生产中15s轮询一次）：
        assert repo.fail_queued_jobs_exceeding_dwell() == 0

    remaining = repo.list_jobs("proj_r42")
    assert all(
        job.status is MonitoringAiJobStatus.COMPLETED for job in remaining
    )


def test_stalled_queue_with_stale_completion_is_still_reaped(
    tmp_path: Path,
) -> None:
    """视界内零完成的滞留照旧收割（R29-01/R31兜底语义不变）。

    一次早期完成后队列彻底停摆（失败→重试→再排队循环的可见形态）：
    越过当前视界（基线+在队深度预算）即收割，完成救不了停滞。
    """

    clock = _FakeClock()
    repo = _make_repository(tmp_path, clock)
    jobs = [
        repo.create_or_get(
            _create_request(
                business_key=(
                    "listing-field-mapping-verifier:stg-2:EX:"
                    f"{index:04d}-of-0008"
                ),
            )
        )
        for index in range(1, 9)
    ]
    # 一片完成（t0），此后队列停滞。
    _complete_row(repo, jobs[0].job_id)
    assert repo.fail_queued_jobs_exceeding_dwell() == 0

    # 推进越过当前视界（2700+7×180=3960s）：停滞队列必须被收割。
    clock.advance(3961)
    reaped = repo.fail_queued_jobs_exceeding_dwell()
    assert reaped == 7
    statuses = {
        str(getattr(getattr(job, "status", ""), "value", job.status))
        for job in repo.list_jobs("proj_r42")
    }
    assert statuses == {
        MonitoringAiJobStatus.COMPLETED.value,
        MonitoringAiJobStatus.FAILED.value,
    }
    failed = [
        job for job in repo.list_jobs("proj_r42")
        if job.status is MonitoringAiJobStatus.FAILED
    ]
    assert all(job.failure_code == "queue_dwell_timeout" for job in failed)
    assert all(int(job.retryable) == 1 for job in failed)


def test_degraded_confirm_requeues_failed_verifier_shards() -> None:
    """降级确认把被绕过的盲核缺口转为事后补偿（就地重排队终态失败分片）。

    R42-01修复提示：降级旁路绕过的复核缺口应转为事后补偿作业而非静默
    受限。补偿回执（聚合计数）随确认载荷透出；补偿失败不阻塞已留痕的
    确认。
    """

    from packages.medical_monitoring.admission.mapping_confirmation import (
        AdmissionMappingConfirmationService,
    )

    calls: list[dict] = []

    def _retry_failed_candidates(**kwargs):
        calls.append(kwargs)
        return {
            "requeued_count": 7,
            "skipped_count": 1,
            "requeued": [],
            "skipped": [],
        }

    draft = SimpleNamespace(
        batch_id="attempt-1",
        draft_id="draft-1",
        version=1,
        model_dump=lambda mode="json": {
            "project_id": "p1",
            "draft_id": "draft-1",
            "batch_id": "attempt-1",
            "version": 1,
            "fields": [
                {
                    "domain": "AE",
                    "source_field": "AETERM",
                    "recommended_role": "ae_term",
                    "field_kind": "source_collected",
                    "confidence": 0.9,
                    "user_action": "系统已按建议采用，无需额外操作。",
                    "user_decision_required": False,
                },
            ],
        },
    )
    repo = SimpleNamespace(
        get_draft=lambda *_args, **_kwargs: draft,
        semantic_quality=lambda *_args: SimpleNamespace(
            as_payload=lambda: {"confirmable": True}
        ),
        confirm=lambda _project_id, _draft_id, **_kwargs: SimpleNamespace(
            model_dump=lambda mode="json": {
                "mapping_revision": "rev-1",
                "draft_id": "draft-1",
                "status": "confirmed",
            }
        ),
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(
            retry_failed_candidates=_retry_failed_candidates,
        ),
        mapping_repository=repo,
        ai_repository=SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
        require_dual_reconciliation=True,
    )

    def _raise_job_failed(**_kwargs):
        from packages.medical_monitoring.admission.mapping_confirmation import (
            AdmissionMappingPipelineError,
        )

        raise AdmissionMappingPipelineError("mapping_verifier_job_failed")

    service.reconcile_with_verifier = _raise_job_failed  # type: ignore[method-assign]

    payload = service.confirm_draft(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        expected_version=1,
        confirmed_by="medical_manager",
        confirmation_reason="医学问题已逐条回答完成。",
        idempotency_key="idem-r42-compensate",
        allow_unverified_dual_review=True,
        workspace_dir="/generated/non-real",
    )

    assert payload["confirmation_status"] == "confirmed"
    assert payload["dual_review_degraded"]
    # 补偿确实瞄准verifier cohort、按显式重试语义重排7片。
    assert len(calls) == 1
    assert calls[0]["cohort"] == "verifier"
    assert calls[0]["attempt_id"] == "attempt-1"
    assert payload["dual_review_compensation"] == {
        "requeued_count": 7,
        "skipped_count": 1,
    }

    # 补偿失败（pipeline不可用/重排队抛错）不回滚已留痕的确认。
    def _boom(**_kwargs):
        raise RuntimeError("verifier pipeline unavailable")

    service.mapping_pipeline = SimpleNamespace(  # type: ignore[assignment]
        retry_failed_candidates=_boom,
    )
    payload = service.confirm_draft(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        expected_version=1,
        confirmed_by="medical_manager",
        confirmation_reason="医学问题已逐条回答完成。",
        idempotency_key="idem-r42-compensate-2",
        allow_unverified_dual_review=True,
        workspace_dir="/generated/non-real",
    )
    assert payload["confirmation_status"] == "confirmed"
    assert payload["dual_review_degraded"]
    assert "dual_review_compensation" not in payload

    # 非降级确认不触发补偿。
    service.mapping_pipeline = SimpleNamespace(  # type: ignore[assignment]
        retry_failed_candidates=_retry_failed_candidates,
    )
    strict_calls_before = len(calls)
    service.reconcile_with_verifier = SimpleNamespace()  # type: ignore[method-assign]
    service.require_dual_reconciliation = False  # type: ignore[misc]
    service.confirm_draft(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        expected_version=1,
        confirmed_by="medical_manager",
        confirmation_reason="医学问题已逐条回答完成。",
        idempotency_key="idem-r42-normal",
    )
    assert len(calls) == strict_calls_before
