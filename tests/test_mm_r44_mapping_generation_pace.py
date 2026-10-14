"""R44轮（R44-02）回归：字段识别的服务端滚动速度与剩余预估。

R44B实测（59表DataListing→177分片）：识别真实吞吐约2.6-3.2分钟/片，
全量需8小时以上，而界面此前只有「本页会话耗时/已完成片数」的线性外推
——页面刷新/会话挂起重连后起点归零，同一识别过程的ETA在439↔144分钟
间反复跳变，失去参考意义。修复：生成态载荷由服务端按最近完成分片的
真实时间戳计算滚动速率与剩余预估（窗口=最近12片），跨刷新稳定；前端
优先消费服务端预估，仅旧载荷（无pace键）才回退会话外推；预估≥90分钟
以小时呈现；服务端不可估/已失真时如实缺省。吞吐本身（分片并发度）是
运维配置面（WORKBENCH_MONITORING_AI_PARALLELISM），不属本次代码修复。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from packages.medical_monitoring.admission.mapping_pipeline import (
    AdmissionMappingPipeline,
    _generation_pace,
)


def _job(status: str, updated_at: datetime | None) -> SimpleNamespace:
    return SimpleNamespace(
        status=SimpleNamespace(value=status) if status else status,
        updated_at=updated_at,
    )


def test_pace_estimates_from_recent_completion_window() -> None:
    base = datetime(2026, 10, 14, 8, 0, 0, tzinfo=timezone.utc)
    # 最近12片：每2分钟一片（含窗口首片间的2分钟间隔，共11个间隔）。
    completed_times = [base + timedelta(minutes=2 * index) for index in range(12)]
    jobs = [
        *(_job("completed", moment) for moment in completed_times),
        _job("running", None),
        _job("queued", None),
    ]
    pace = _generation_pace(jobs, total=177, completed=74)
    assert pace is not None
    assert pace["window_shards"] == 12
    assert pace["window_seconds"] == 22 * 60
    assert pace["remaining_shards"] == 103
    # 速率=11片/1320s → 剩余103片 ≈ 12360s。
    assert pace["eta_seconds"] == 12360
    assert pace["last_completion_age_seconds"] >= 0


def test_pace_is_none_without_two_completions() -> None:
    base = datetime(2026, 10, 14, 8, 0, 0, tzinfo=timezone.utc)
    assert _generation_pace(
        [_job("completed", base), _job("queued", None)],
        total=10,
        completed=1,
    ) is None


def test_pace_is_none_when_generation_finished() -> None:
    base = datetime(2026, 10, 14, 8, 0, 0, tzinfo=timezone.utc)
    assert _generation_pace(
        [_job("completed", base), _job("completed", base)],
        total=2,
        completed=2,
    ) is None
    assert _generation_pace(
        [_job("completed", base), _job("completed", base)],
        total=0,
        completed=0,
    ) is None


def test_pace_is_none_for_naive_timestamps() -> None:
    base = datetime(2026, 10, 14, 8, 0, 0)
    assert _generation_pace(
        [_job("completed", base), _job("completed", base), _job("queued", None)],
        total=3,
        completed=2,
    ) is None


def test_project_payload_carries_pace_key() -> None:
    """生成态公开载荷必须携带pace键（不可估时为null）——前端据此区分
    「服务端已评估但缺省」与「旧载荷无此键」。"""

    base = datetime(2026, 10, 14, 8, 0, 0, tzinfo=timezone.utc)
    jobs = [
        SimpleNamespace(
            job_id="j1",
            business_key="listing-field-mapping:stg-1:AE:0001-of-0001",
            status=SimpleNamespace(value="completed"),
            provider="cms-router",
            requested_model="glm-5.3-flash",
            response_model="glm-5.3-flash",
            attempt_count=1,
            max_attempts=2,
            failure_message="",
            failure_code="",
            updated_at=base,
        ),
        SimpleNamespace(
            job_id="j2",
            business_key="listing-field-mapping:stg-1:LB:0001-of-0001",
            status=SimpleNamespace(value="queued"),
            provider="cms-router",
            requested_model="glm-5.3-flash",
            response_model="",
            attempt_count=0,
            max_attempts=2,
            failure_message="",
            failure_code="",
            updated_at=base,
        ),
    ]
    pipeline = AdmissionMappingPipeline(
        ai_repository=SimpleNamespace(candidates=lambda *_args, **_kwargs: []),
    )
    payload = pipeline._project(
        jobs,
        attempt_id="stg-1",
        include_candidates=False,
    )
    assert payload["state"] == "generating"
    assert "pace" in payload
    assert payload["pace"] is None  # 单片完成：样本不足，如实缺省
