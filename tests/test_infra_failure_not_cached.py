"""状态机专项S6（02_DESIGN §5.1/§7）：失败态永不缓存复用（库层不变量）。

R11-01场景：infra终态失败行→同请求重发→显式重排（env灰度）；
content失败/契约退役行/env默认off→原样返回（现状fail-closed）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app.monitoring_admission_stage_store import (  # noqa: E402
    INFRA_FAILURE_CODES,
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
)

HASH_A = "a" * 64
HASH_B = "b" * 64
ATTEMPT = "attempt_s6"
KEY = f"listing-field-mapping:{ATTEMPT}:u01:{ATTEMPT}:LB:0001-of-0001"


def _request(business_key: str = KEY) -> MonitoringAiJobCreate:
    revision = MonitoringAiInputRevision(
        project_id="proj-s6",
        batch_revision="batch-s6",
        mapping_revision="mapping-s6",
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
        project_id=revision.project_id,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        input_revision=revision,
        input_payload={"schema_version": "monitoring_ai_v1"},
        prompt_version="mapping-prompt-v1",
        profile_id="independent-ai-test",
        provider="test-provider",
        requested_model="test-model",
        max_attempts=2,
        business_key=business_key,
    )


def _failed_job(
    repo: MonitoringAiRepository, *, failure_code: str
):
    job = repo.create_or_get(_request())
    running = repo.claim_next("worker-s6")
    assert running.job_id == job.job_id
    return repo.fail(
        running,
        owner="worker-s6",
        failure_code=failure_code,
        failure_message="upstream failure",
        retryable=False,
    )


def test_infra_failed_hit_requeues_on_resubmit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R11-01场景（env开）：503类失败行→同请求重发→requeued+留痕。"""

    monkeypatch.setenv("WORKBENCH_MONITORING_AI_INFRA_RETRY", "1")
    repo = MonitoringAiRepository(tmp_path / "s6.sqlite3")
    failed = _failed_job(repo, failure_code="provider_runtime_error")
    assert failed.status == MonitoringAiJobStatus.FAILED

    resubmitted = repo.create_or_get(_request())
    assert resubmitted.status == MonitoringAiJobStatus.QUEUED
    # recovery_action留痕（actor=user=显式重试语义）。
    events = repo.stage_store.list_events("proj-s6", ATTEMPT)
    recovery = [item for item in events if item["event_type"] == "recovery_action"]
    assert len(recovery) == 1
    assert recovery[0]["actor"] == "user"


def test_content_failed_hit_returned_as_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """content失败（invalid_ai_output）：env开也原样返回（边界fail-closed）。"""

    monkeypatch.setenv("WORKBENCH_MONITORING_AI_INFRA_RETRY", "1")
    repo = MonitoringAiRepository(tmp_path / "s6.sqlite3")
    failed = _failed_job(repo, failure_code="invalid_ai_output")
    again = repo.create_or_get(_request())
    assert again.job_id == failed.job_id
    assert again.status == MonitoringAiJobStatus.FAILED
    assert again.failure_code == "invalid_ai_output"
    recovery = [
        item
        for item in repo.stage_store.list_events("proj-s6", ATTEMPT)
        if item["event_type"] == "recovery_action"
    ]
    assert recovery == []


def test_contract_retired_hit_returned_as_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """契约退役行：env开也原样返回（绝不重排）。"""

    monkeypatch.setenv("WORKBENCH_MONITORING_AI_INFRA_RETRY", "1")
    repo = MonitoringAiRepository(tmp_path / "s6.sqlite3")
    job = repo.create_or_get(_request())
    retired = repo.retire_obsolete_generation(
        "proj-s6", job_ids=[job.job_id], reason="测试退役"
    )
    assert retired == 1
    again = repo.create_or_get(_request())
    assert again.status == MonitoringAiJobStatus.STALE_INPUT
    assert again.contract_retirement_code == "obsolete_generation"


def test_default_env_off_keeps_current_behavior(tmp_path: Path) -> None:
    """env默认off：infra失败行同请求重发原样返回（现状，灰度零行为）。"""

    repo = MonitoringAiRepository(tmp_path / "s6.sqlite3")
    failed = _failed_job(repo, failure_code="provider_runtime_error")
    assert failed.failure_code in INFRA_FAILURE_CODES
    again = repo.create_or_get(_request())
    assert again.status == MonitoringAiJobStatus.FAILED
    assert again.failure_code == "provider_runtime_error"
