"""状态机专项S2（02_DESIGN §3.2/§7）：识别聚合态物化+影子比对。

覆盖：§3.2全变迁矩阵（not_started→generating→candidates_ready→
needs_attention→generating循环）；派生与物化影子一致（漂移→
stage_view_divergence事件）；并发retry竞态下状态行仍一致；CAS拒绝
回滚不落物化。
"""

from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_monitoring_mapping_draft_repository import (  # noqa: E402
    _candidate,
    _seed_chunk,
)
from packages.medical_monitoring.admission.mapping_pipeline import (  # noqa: E402
    AdmissionMappingPipeline,
)
from services.api.app.monitoring_admission_stage_store import (  # noqa: E402
    STAGE_RECOGNITION,
    EVENT_STAGE_VIEW_DIVERGENCE,
    aggregate_recognition_state,
)
from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MonitoringAiInputRevision,
    MonitoringAiJobCreate,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
    MonitoringAiStateConflictError,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def _stage_row(repo):
    return repo.stage_store.get_stage("project-alpha", "batch-001", STAGE_RECOGNITION)


def _divergence_events(repo):
    return [
        event
        for event in repo.stage_store.list_events("project-alpha", "batch-001")
        if event["event_type"] == EVENT_STAGE_VIEW_DIVERGENCE
    ]


def _seed_inflight_chunk(
    ai_repository: MonitoringAiRepository,
    *,
    domain: str,
    chunk_index: int,
    chunk_total: int,
) -> MonitoringAiJob:
    """只创建不认领的在途分片（画像身份与_seed_chunk完全一致）。"""

    from tests.test_monitoring_mapping_draft_repository import (
        INPUT_HASH,
        PROFILE_HASH,
        _revision,
    )

    payload = {
        "schema_version": "monitoring_ai_v1",
        "field_profile": {
            "schema_version": "monitoring_ai_field_profile_v1",
            "scope": "complete_profile_chunk",
            "project_id": "project-alpha",
            "batch_id": "batch-001",
            "batch_revision": 1,
            "expected_domains": ["AE", "CM"],
            "full_profile_sha256": PROFILE_HASH,
            "full_input_sha256": INPUT_HASH,
            "full_field_count": 3,
            "domain": domain,
            "domain_field_count": 1,
            "chunk_index": chunk_index,
            "chunk_total": chunk_total,
            "chunk_size_limit": 1,
            "fields": [
                {
                    "domain": domain,
                    "field": "XXTERM",
                    "total_rows": 100,
                    "non_empty_count": 90,
                    "null_rate": 0.1,
                    "inferred_type": "string",
                    "unique_value_count": 20,
                    "top_values": [],
                    "representative_values": [],
                    "anomaly_examples": [],
                },
            ],
        },
    }
    return ai_repository.create_or_get(
        MonitoringAiJobCreate(
            project_id="project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=_revision("project-alpha", suffix="001"),
            input_payload=payload,
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=2,
            business_key=(
                f"listing-field-mapping:batch-001:{domain}:"
                f"{chunk_index:04d}-of-{chunk_total:04d}"
            ),
        )
    )


def test_recognition_transition_matrix_materializes_stage_row(tmp_path: Path) -> None:
    """§3.2全变迁矩阵：每个聚合态跨越后物化行即时正确、revision单调。"""

    repo = MonitoringAiRepository(tmp_path / "stage.sqlite3")
    attempt_rows = repo.stage_store.list_events("project-alpha", "batch-001")
    assert _stage_row(repo) is None  # not_started=无行

    # ① cohort首个作业入队+完成（_seed_chunk内部complete）：
    # not_started→generating→candidates_ready。
    _seed_chunk(repo, domain="AE", chunk_index=1, chunk_total=2,
                fields=("AETERM",), domain_field_count=2)
    row = _stage_row(repo)
    assert row["state"] == "candidates_ready"
    assert row["revision"] >= 1
    revision_after_first = row["revision"]

    # ② 新提交分片入队（新组INSERT）：candidates_ready→generating。
    _seed_inflight_chunk(repo, domain="AE", chunk_index=2, chunk_total=2)
    row = _stage_row(repo)
    assert row["state"] == "generating"
    assert row["revision"] > revision_after_first

    # ③ 在途分片完成：generating→candidates_ready。
    inflight = repo.list_jobs(
        "project-alpha",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix="listing-field-mapping:batch-001:",
    )
    queued = [job for job in inflight if job.status == MonitoringAiJobStatus.QUEUED]
    assert len(queued) == 1
    running = repo.claim_next("worker-s2")
    assert running.job_id == queued[0].job_id
    candidate = _candidate(running, ("XXTERM",))
    repo.complete(
        running,
        owner="worker-s2",
        response_model="test-model",
        raw_output={"candidates": [candidate.model_dump(mode="json")]},
        candidates=[candidate],
    )
    assert _stage_row(repo)["state"] == "candidates_ready"

    # ④ 追加分片终态失败（全终态且有失败）：→needs_attention。
    _seed_chunk(repo, domain="CM", chunk_index=1, chunk_total=1,
                fields=("CMTRT",), domain_field_count=1)
    assert _stage_row(repo)["state"] == "candidates_ready"
    failed_job = repo.create_or_get(
        MonitoringAiJobCreate(
            project_id="project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=_revision_for_failure(),
            input_payload={"schema_version": "monitoring_ai_v1"},
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=1,
            business_key="listing-field-mapping:batch-001:DM:0001-of-0001",
        )
    )
    running = repo.claim_next("worker-s2")
    assert running.job_id == failed_job.job_id
    repo.fail(
        running,
        owner="worker-s2",
        failure_code="invalid_ai_output",
        failure_message="bad output",
        retryable=False,
    )
    row = _stage_row(repo)
    assert row["state"] == "needs_attention"

    # ⑤ 显式重试重排：needs_attention→generating。
    repo.retry_terminal(
        "project-alpha",
        failed_job.job_id,
        current_input_revision_sha256=failed_job.input_revision_sha256,
    )
    assert _stage_row(repo)["state"] == "generating"

    # 影子期全程：派生（同口径重算）与物化一致，零漂移事件。
    jobs = repo.list_jobs(
        "project-alpha",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix="listing-field-mapping:batch-001:",
    )
    derived = aggregate_recognition_state(
        [str(job.status.value) for job in jobs]
    )
    assert derived == _stage_row(repo)["state"]
    assert _divergence_events(repo) == []


def _revision_for_failure() -> MonitoringAiInputRevision:
    return MonitoringAiInputRevision(
        project_id="project-alpha",
        batch_revision="batch-fail",
        mapping_revision="mapping-fail",
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


def test_shadow_compare_records_divergence_event(tmp_path: Path) -> None:
    """派生≠物化→stage_view_divergence事件；verifier cohort与缺行不比对。"""

    repo = MonitoringAiRepository(tmp_path / "shadow.sqlite3")
    _seed_chunk(repo, domain="AE", chunk_index=1, chunk_total=1,
                fields=("AETERM",), domain_field_count=1)
    assert _stage_row(repo)["state"] == "candidates_ready"

    pipeline = AdmissionMappingPipeline(ai_repository=repo)
    job = repo.list_jobs(
        "project-alpha",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
    )[0]

    # 派生（错误地）报generating而物化为candidates_ready→漂移留痕。
    pipeline._shadow_compare_recognition_state(
        jobs=[job],
        attempt_id="batch-001",
        cohort="primary",
        derived_state="generating",
    )
    events = _divergence_events(repo)
    assert len(events) == 1
    assert events[0]["from_state"] == "candidates_ready"
    assert events[0]["to_state"] == "generating"

    # 一致→不加事件。
    pipeline._shadow_compare_recognition_state(
        jobs=[job],
        attempt_id="batch-001",
        cohort="primary",
        derived_state="candidates_ready",
    )
    assert len(_divergence_events(repo)) == 1

    # verifier cohort不比对（物化行口径=primary）。
    pipeline._shadow_compare_recognition_state(
        jobs=[job],
        attempt_id="batch-001",
        cohort="verifier",
        derived_state="generating",
    )
    assert len(_divergence_events(repo)) == 1

    # 物化行缺失（另一attempt）→不比对。
    pipeline._shadow_compare_recognition_state(
        jobs=[job],
        attempt_id="batch-other",
        cohort="primary",
        derived_state="generating",
    )
    assert len(_divergence_events(repo)) == 1

    # STAGE_VIEW_MODE=materialized→影子比对关闭（S3预备）。
    monkey = pytest.MonkeyPatch()
    monkey.setenv("STAGE_VIEW_MODE", "materialized")
    try:
        pipeline._shadow_compare_recognition_state(
            jobs=[job],
            attempt_id="batch-001",
            cohort="primary",
            derived_state="generating",
        )
    finally:
        monkey.undo()
    assert len(_divergence_events(repo)) == 1


def test_concurrent_retry_keeps_stage_row_consistent(tmp_path: Path) -> None:
    """并发retry竞态：恰好一次重排成功，物化行与权威一致。"""

    repo = MonitoringAiRepository(tmp_path / "race.sqlite3")
    job = repo.create_or_get(
        MonitoringAiJobCreate(
            project_id="project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=_revision_for_failure(),
            input_payload={"schema_version": "monitoring_ai_v1"},
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=1,
            business_key="listing-field-mapping:batch-001:DM:0001-of-0001",
        )
    )
    running = repo.claim_next("worker-race")
    repo.fail(
        running,
        owner="worker-race",
        failure_code="provider_timeout",
        failure_message="upstream timeout",
        retryable=False,
    )
    assert _stage_row(repo)["state"] == "needs_attention"

    def retry() -> str:
        try:
            retried = repo.retry_terminal(
                "project-alpha",
                job.job_id,
                current_input_revision_sha256=job.input_revision_sha256,
            )
        except MonitoringAiStateConflictError:
            return "conflict"
        return str(retried.status.value)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = [
            future.result()
            for future in [
                pool.submit(retry),
                pool.submit(retry),
            ]
        ]
    # BEGIN IMMEDIATE串行化：恰好一次queued成功，另一次StateConflict。
    assert sorted(outcomes) == ["conflict", "queued"]
    assert _stage_row(repo)["state"] == "generating"
    recovery_events = [
        event
        for event in repo.stage_store.list_events("project-alpha", "batch-001")
        if event["event_type"] == "recovery_action"
    ]
    assert len(recovery_events) == 1


def test_cas_rejected_fail_rolls_back_materialization(tmp_path: Path) -> None:
    """同事务性：CAS拒绝的fail回滚，物化行不留亡态。"""

    repo = MonitoringAiRepository(tmp_path / "rollback.sqlite3")
    _seed_chunk(repo, domain="AE", chunk_index=1, chunk_total=1,
                fields=("AETERM",), domain_field_count=1)
    before = _stage_row(repo)
    assert before["state"] == "candidates_ready"
    job = repo.get(
        "project-alpha",
        repo.list_jobs(
            "project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        )[0].job_id,
    )
    with pytest.raises(MonitoringAiStateConflictError):
        repo.fail(
            job,
            owner="ghost-worker",  # 租约不匹配→CAS拒绝
            failure_code="invalid_ai_output",
            failure_message="bad output",
            retryable=False,
        )
    after = _stage_row(repo)
    assert after["state"] == "candidates_ready"
    assert after["revision"] == before["revision"]
