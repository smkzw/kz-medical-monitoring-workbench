"""E2E拦截修复回归：确认链verifier死锁家族（2026-10-15 SM1/SM2实测）。

- 收割器：同任务类型在途执行（live lease）时，attempt_count=0的排队行
  是「等待」不是「滞留」——重置等待钟并跳过收割；attempt>0循环与
  worker空闲真饥饿仍按原视界收割。
- confirm路径：mapping_verifier_job_failed在raise前兑现重排承诺
  （409文案与行为一致），前端下次确认进入等待而非死循环。
- apply_single_source：backfill返回值不得丢弃（回填成功不得误触
  fail-closed）。
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.admission.admission_stage_view import (  # noqa: E402
    apply_single_source,
)
from packages.medical_monitoring.admission.mapping_confirmation import (  # noqa: E402
    AdmissionMappingConfirmationService,
    AdmissionMappingPipelineError,
)
from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MonitoringAiJobCreate,
    MonitoringAiInputRevision,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
VERIFIER_KEY = (
    "listing-field-mapping-verifier:attempt_rx:u01:attempt_rx:LB:0001-of-0001"
)


def _revision(project_id: str = "proj-rx"):
    return MonitoringAiInputRevision(
        project_id=project_id,
        batch_revision="batch-rx",
        mapping_revision="mapping-rx",
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


def _request(
    repo, business_key: str, *, max_attempts: int = 2
) -> MonitoringAiJobCreate:
    return MonitoringAiJobCreate(
        project_id="proj-rx",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        input_revision=_revision(),
        input_payload={"schema_version": "monitoring_ai_v1"},
        prompt_version="mapping-prompt-v1",
        profile_id="independent-ai-test",
        provider="test-provider",
        requested_model="test-model",
        max_attempts=max_attempts,
        business_key=business_key,
    )


def test_dwell_reaper_spares_zero_claim_rows_while_cohort_executing(
    tmp_path: Path,
) -> None:
    """在途执行（running行存在）时零认领排队行被豁免且等待钟重置。"""

    from datetime import datetime, timedelta, timezone

    class _Clock:
        def __init__(self) -> None:
            self.value = datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc)

        def __call__(self) -> datetime:
            return self.value

        def advance(self, **kwargs) -> None:
            self.value += timedelta(**kwargs)

    clock = _Clock()
    repo = MonitoringAiRepository(
        tmp_path / "rx.sqlite3",
        queue_dwell_timeout_seconds=60,
        clock=clock,
    )
    # 先建会被认领的作业（模拟别的项目/分片占着verifier单worker），
    # 认领后其status=running=同任务类型在途执行。
    busy = repo.create_or_get(
        _request(repo, "listing-field-mapping-verifier:attempt_busy:u01:x")
    )
    claimed = repo.claim_next("verifier-worker")
    assert claimed.job_id == busy.job_id

    # 再建零认领排队行（后到项目的分片）。
    waiting = repo.create_or_get(
        _request(repo, VERIFIER_KEY)
    )

    # 推进远超视界（60s）；running行租约虽已过期，但claim_next会自动
    # 回收、终态僵尸由expire_exhausted_leases清理——running信号有界自愈。
    clock.advance(minutes=30)

    reaped = repo.fail_queued_jobs_exceeding_dwell()
    assert reaped == 0
    still_queued = repo.get("proj-rx", waiting.job_id)
    assert still_queued.status == MonitoringAiJobStatus.QUEUED
    # 等待钟已重置：dwell_since（DB列）≈收割时刻而非入队时刻。
    import sqlite3 as _sqlite3

    with _sqlite3.connect(repo.path) as connection:
        connection.row_factory = _sqlite3.Row
        row = connection.execute(
            "SELECT dwell_since FROM monitoring_ai_jobs WHERE job_id = ?",
            (waiting.job_id,),
        ).fetchone()
    assert row["dwell_since"] >= clock.value.isoformat()


def test_dwell_reaper_still_reaps_when_workers_idle(tmp_path: Path) -> None:
    """worker空闲（无running行）时真饥饿照常收割（R29-01语义保留）。"""

    from datetime import datetime, timedelta, timezone

    class _Clock:
        def __init__(self) -> None:
            self.value = datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc)

        def __call__(self) -> datetime:
            return self.value

        def advance(self, **kwargs) -> None:
            self.value += timedelta(**kwargs)

    clock = _Clock()
    repo = MonitoringAiRepository(
        tmp_path / "rx2.sqlite3",
        queue_dwell_timeout_seconds=60,
        clock=clock,
    )
    waiting = repo.create_or_get(_request(repo, VERIFIER_KEY))

    clock.advance(minutes=30)
    reaped = repo.fail_queued_jobs_exceeding_dwell()
    assert reaped == 1
    assert repo.get("proj-rx", waiting.job_id).status == MonitoringAiJobStatus.FAILED


def test_confirm_requeues_failed_verifier_shards_before_raising(
    tmp_path: Path,
) -> None:
    """confirm的409承诺兑现：mapping_verifier_job_failed raise前先重排。"""

    requeue_calls: list[dict[str, str]] = []
    draft = SimpleNamespace(
        batch_id="attempt-1",
        model_dump=lambda mode="json": {
            "fields": [
                {
                    "domain": "AE",
                    "source_field": "AETERM",
                    "recommended_role": "ae_term",
                    "field_kind": "source_collected",
                    "confidence": 0.99,
                    "user_action": "系统已按建议采用，无需额外操作。",
                },
            ],
        },
    )
    repo = SimpleNamespace(
        get_draft=lambda *_args, **_kwargs: draft,
        confirm=lambda *_args, **_kwargs: SimpleNamespace(
            model_dump=lambda mode="json": {"mapping_revision": "rev-1"}
        ),
    )

    class _Service(AdmissionMappingConfirmationService):
        def reconcile_with_verifier(self, **_kwargs):
            raise AdmissionMappingPipelineError("mapping_verifier_job_failed")

        def _retry_failed_mapping_jobs(self, *, project_id, attempt_id):
            requeue_calls.append(
                {"project_id": project_id, "attempt_id": attempt_id}
            )
            return 10

    service = _Service(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=SimpleNamespace(),
        prompt_version="p",
        accepted_status="accepted",
        proposed_status="proposed",
        require_dual_reconciliation=True,
    )
    with pytest.raises(
        AdmissionMappingPipelineError, match="mapping_verifier_job_failed"
    ):
        service.confirm_draft(
            project_id="p1",
            attempt_id="attempt-1",
            draft_id="draft-1",
            expected_version=1,
            confirmed_by="tester",
            confirmation_reason="医学问题已逐条回答完成。",
            idempotency_key="idem-rx-1",
        )
    assert requeue_calls == [
        {"project_id": "p1", "attempt_id": "attempt-1"}
    ]


def test_apply_single_source_uses_backfill_result() -> None:
    """backfill返回值生效：回填出物化行后不再fail-closed。"""

    payload = {
        "state": "candidates_ready",
        "summary": {"candidate_count": 1},
        "candidates": [],
    }
    projected = apply_single_source(
        payload,
        draft=None,
        facts_status=None,
        recognition_state_row=None,
        recognition_jobs_exist=True,
        backfill=lambda: {"state": "generating"},
    )
    assert projected["state"] == "generating"
