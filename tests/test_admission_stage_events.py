"""状态机专项S1（02_DESIGN §2/§4）：入舱阶段事件流地基。

覆盖：变迁→事件存在；no_update/no_delete触发器；failure_class分类；
同事务性（回滚则事件不存）；阶段状态行revision单调。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from services.api.app.monitoring_admission_stage_store import (
    STAGE_RECOGNITION,
    STAGE_TABLES_DDL,
    AdmissionStageStore,
    EVENT_FAILURE_RECORDED,
    EVENT_RECOVERY_ACTION,
    EVENT_STATE_CHANGED,
    failure_class_for,
    recognition_attempt_id,
)
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiClaim,
    MonitoringAiClaimKind,
    MonitoringAiCandidate,
    MonitoringAiEvidence,
    MonitoringAiInputRevision,
    MonitoringAiJobCreate,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (
    MonitoringAiRepository,
    MonitoringAiStateConflictError,
)

HASH_A = "a" * 64
HASH_B = "b" * 64
ATTEMPT = "attempt_s1"
RECOGNITION_KEY = (
    f"listing-field-mapping:{ATTEMPT}:u01:{ATTEMPT}:LB:0001-of-0002"
)


class MutableClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 10, 14, 8, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self._value

    def advance(self, **kwargs: int) -> None:
        self._value += timedelta(**kwargs)


def _revision(*, project_id: str = "proj-stage-s1") -> MonitoringAiInputRevision:
    return MonitoringAiInputRevision(
        project_id=project_id,
        batch_revision="batch-s1",
        mapping_revision="mapping-s1",
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
    *,
    project_id: str = "proj-stage-s1",
    business_key: str = RECOGNITION_KEY,
    max_attempts: int = 1,
) -> MonitoringAiJobCreate:
    revision = _revision(project_id=project_id)
    return MonitoringAiJobCreate(
        project_id=revision.project_id,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        input_revision=revision,
        input_payload={"batch_id": ATTEMPT, "field_profiles": []},
        prompt_version="monitoring-field-mapping-v1",
        profile_id="independent-ai-test",
        provider="test-provider",
        requested_model="test-model",
        max_attempts=max_attempts,
        business_key=business_key,
    )


def _candidate(job, clock: MutableClock) -> MonitoringAiCandidate:
    evidence = MonitoringAiEvidence(
        evidence_id="evidence-s1",
        source_entry_id="source-listing",
        source_content_sha256=HASH_A,
        locator="batch://LB/LBORRES/1",
        raw_fields={"domain": "LB", "field": "LBORRES"},
        input_revision_sha256=job.input_revision_sha256,
    )
    claim = MonitoringAiClaim(
        claim_id="claim-s1",
        kind=MonitoringAiClaimKind.RECOMMENDATION,
        text="建议将该字段作为原始检验结果候选映射。",
        confidence=0.85,
        uncertainty="字段语义仍需结合同域单位和参考范围字段复核。",
        user_action="请确认字段角色。",
        evidence_ids=(evidence.evidence_id,),
    )
    return MonitoringAiCandidate(
        candidate_id=f"candidate-{job.job_id}-1",
        job_id=job.job_id,
        project_id=job.project_id,
        task_type=job.task_type,
        candidate_type="field_mapping",
        title="字段映射候选 1",
        structured_payload={"domain": "LB", "field": "LBORRES"},
        claims=(claim,),
        evidence=(evidence,),
        input_revision_sha256=job.input_revision_sha256,
        prompt_version="monitoring-field-mapping-v1",
        created_at=clock(),
    )


def _recognition_events(repo, project_id: str = "proj-stage-s1"):
    return repo.stage_store.list_events(project_id, ATTEMPT)


def test_recognition_lifecycle_writes_stage_events(tmp_path: Path) -> None:
    """02_DESIGN §3.2：入队/完成各落一条state_changed；CAS拒绝不加事件。"""

    clock = MutableClock()
    repo = MonitoringAiRepository(tmp_path / "stage.sqlite3", clock=clock)
    job = repo.create_or_get(_request())

    created = _recognition_events(repo)
    assert [item["event_type"] for item in created] == [EVENT_STATE_CHANGED]
    assert created[0]["from_state"] == ""
    assert created[0]["to_state"] == "queued"
    assert created[0]["stage"] == STAGE_RECOGNITION
    assert created[0]["attempt_id"] == ATTEMPT

    running = repo.claim_next("worker-s1")
    assert running.job_id == job.job_id
    candidate = _candidate(running, clock)
    repo.complete(
        running,
        owner="worker-s1",
        response_model="test-model",
        raw_output={"candidates": [candidate.model_dump(mode="json")]},
        candidates=[candidate],
    )
    events = _recognition_events(repo)
    assert [item["event_type"] for item in events][-1] == EVENT_STATE_CHANGED
    assert events[-1]["from_state"] == "running"
    assert events[-1]["to_state"] == "completed"

    # 已完成作业不可再失败（CAS拒绝）——无新增事件。
    with pytest.raises(MonitoringAiStateConflictError):
        repo.fail(
            repo.get(job.project_id, job.job_id),
            owner="worker-s1",
            failure_code="invalid_ai_output",
            failure_message="bad output",
            retryable=False,
        )
    assert len(_recognition_events(repo)) == 2


def test_terminal_failure_and_explicit_retry_events(tmp_path: Path) -> None:
    """终态失败→failure_recorded（content类）；显式重试→recovery_action(user)。"""

    clock = MutableClock()
    repo = MonitoringAiRepository(tmp_path / "stage.sqlite3", clock=clock)
    job = repo.create_or_get(_request())
    running = repo.claim_next("worker-s1")
    failed = repo.fail(
        running,
        owner="worker-s1",
        failure_code="invalid_ai_output",
        failure_message="模型输出违反契约",
        retryable=False,
    )
    assert failed.status == MonitoringAiJobStatus.FAILED
    events = _recognition_events(repo)
    assert events[-1]["event_type"] == EVENT_FAILURE_RECORDED
    assert events[-1]["reason_code"] == "invalid_ai_output"
    assert events[-1]["failure_class"] == "content"

    retried = repo.retry_terminal(
        job.project_id,
        job.job_id,
        current_input_revision_sha256=job.input_revision_sha256,
    )
    assert retried.status == MonitoringAiJobStatus.QUEUED
    events = _recognition_events(repo)
    assert events[-1]["event_type"] == EVENT_RECOVERY_ACTION
    assert events[-1]["from_state"] == "failed"
    assert events[-1]["to_state"] == "queued"
    assert events[-1]["actor"] == "user"


def test_failure_class_infra_codes(tmp_path: Path) -> None:
    """infra类失败码→failure_class=infra（02_DESIGN §5.1判据）。"""

    clock = MutableClock()
    repo = MonitoringAiRepository(tmp_path / "stage.sqlite3", clock=clock)
    job = repo.create_or_get(_request())
    running = repo.claim_next("worker-s1")
    repo.fail(
        running,
        owner="worker-s1",
        failure_code="provider_timeout",
        failure_message="upstream timeout",
        retryable=False,
    )
    events = _recognition_events(repo)
    assert events[-1]["event_type"] == EVENT_FAILURE_RECORDED
    assert events[-1]["failure_class"] == "infra"
    assert events[-1]["reason_code"] == "provider_timeout"


def test_mark_stale_records_failure_event(tmp_path: Path) -> None:
    clock = MutableClock()
    repo = MonitoringAiRepository(tmp_path / "stage.sqlite3", clock=clock)
    # mark_stale标记queued/completed/blocked行（running由stale_claimed处理），
    # 故不claim直接以revision变化标记在队作业。
    repo.create_or_get(_request())
    repo.mark_stale(
        "proj-stage-s1",
        business_key=RECOGNITION_KEY,
        current_input_revision_sha256="f" * 64,
    )
    events = _recognition_events(repo)
    assert events[-1]["event_type"] == EVENT_FAILURE_RECORDED
    assert events[-1]["to_state"] == "stale_input"
    assert events[-1]["reason_code"] == "stale_input_revision"
    assert events[-1]["failure_class"] == "content"


def test_queue_dwell_reap_records_events(tmp_path: Path) -> None:
    """R29-01滞留收割→逐行failure_recorded（queue_dwell_timeout）。"""

    clock = MutableClock()
    repo = MonitoringAiRepository(
        tmp_path / "stage.sqlite3",
        queue_dwell_timeout_seconds=60,
        clock=clock,
    )
    repo.create_or_get(_request(business_key=RECOGNITION_KEY))
    repo.create_or_get(
        _request(
            business_key=(
                f"listing-field-mapping:{ATTEMPT}:u02:{ATTEMPT}:DM:0001-of-0001"
            )
        )
    )
    # 收割视界=基线60s+(在队2-1)×单作业预算180s=240s。
    clock.advance(seconds=600)
    reaped = repo.fail_queued_jobs_exceeding_dwell()
    assert reaped == 2
    events = [
        item
        for item in _recognition_events(repo)
        if item["reason_code"] == "queue_dwell_timeout"
    ]
    assert len(events) == 2
    assert {item["event_type"] for item in events} == {EVENT_FAILURE_RECORDED}
    assert {item["from_state"] for item in events} == {"queued"}
    assert {item["to_state"] for item in events} == {"failed"}


def test_non_recognition_business_key_writes_no_event(tmp_path: Path) -> None:
    """文档权威等非识别链作业不落recognition事件（02_DESIGN §3.2边界）。"""

    clock = MutableClock()
    repo = MonitoringAiRepository(tmp_path / "stage.sqlite3", clock=clock)
    repo.create_or_get(
        _request(business_key="document-authority:some-batch:primary")
    )
    assert _recognition_events(repo) == []


def test_event_triggers_are_immutable(tmp_path: Path) -> None:
    """no_update/no_delete触发器生效（02_DESIGN §2.1 append-only）。"""

    clock = MutableClock()
    repo = MonitoringAiRepository(tmp_path / "stage.sqlite3", clock=clock)
    repo.create_or_get(_request())
    (event,) = _recognition_events(repo)
    with sqlite3.connect(repo.path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE monitoring_admission_stage_events SET to_state = 'x'"
                " WHERE event_id = ?",
                (event["event_id"],),
            )
        with pytest.raises(sqlite3.IntegrityError, match="forbidden"):
            connection.execute(
                "DELETE FROM monitoring_admission_stage_events WHERE event_id = ?",
                (event["event_id"],),
            )


def test_same_transaction_rollback_drops_event(tmp_path: Path) -> None:
    """同事务性：外层事务回滚则事件不存（02_DESIGN §2.3）。"""

    clock = MutableClock()

    def connect() -> sqlite3.Connection:
        connection = sqlite3.connect(tmp_path / "tx.sqlite3", timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    store = AdmissionStageStore(connect, clock=clock)
    connection = connect()
    connection.executescript(STAGE_TABLES_DDL)
    connection.execute("BEGIN IMMEDIATE")
    store.append_event(
        connection,
        project_id="proj-stage-s1",
        attempt_id=ATTEMPT,
        stage=STAGE_RECOGNITION,
        event_type=EVENT_STATE_CHANGED,
        from_state="",
        to_state="queued",
    )
    connection.rollback()
    assert store.list_events("proj-stage-s1", ATTEMPT) == []


def test_bump_stage_revision_monotonic(tmp_path: Path) -> None:
    clock = MutableClock()

    def connect() -> sqlite3.Connection:
        connection = sqlite3.connect(tmp_path / "bump.sqlite3", timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    store = AdmissionStageStore(connect, clock=clock)
    connection = connect()
    connection.executescript(STAGE_TABLES_DDL)
    connection.execute("BEGIN IMMEDIATE")
    assert (
        store.bump_stage(
            connection,
            project_id="p",
            attempt_id=ATTEMPT,
            stage=STAGE_RECOGNITION,
            state="generating",
        )
        == 1
    )
    assert (
        store.bump_stage(
            connection,
            project_id="p",
            attempt_id=ATTEMPT,
            stage=STAGE_RECOGNITION,
            state="candidates_ready",
            detail={"candidate_count": 60},
        )
        == 2
    )
    connection.commit()
    row = store.get_stage("p", ATTEMPT, STAGE_RECOGNITION)
    assert row["state"] == "candidates_ready"
    assert row["revision"] == 2
    connection.close()


def test_append_event_rejects_invalid_enums(tmp_path: Path) -> None:
    """fail-closed：非法stage/event_type/failure_class直接拒绝。"""

    connection = sqlite3.connect(tmp_path / "enum.sqlite3", timeout=30)
    connection.row_factory = sqlite3.Row
    connection.executescript(STAGE_TABLES_DDL)
    store = AdmissionStageStore(lambda: connection)
    with pytest.raises(ValueError):
        store.append_event(
            connection,
            project_id="p",
            stage="unknown_stage",
            event_type=EVENT_STATE_CHANGED,
        )
    with pytest.raises(ValueError):
        store.append_event(
            connection,
            project_id="p",
            stage=STAGE_RECOGNITION,
            event_type="made_up_event",
        )
    with pytest.raises(ValueError):
        store.append_event(
            connection,
            project_id="p",
            stage=STAGE_RECOGNITION,
            event_type=EVENT_STATE_CHANGED,
            failure_class="infra2",
        )
    connection.close()


def test_attempt_prefix_parsing() -> None:
    assert (
        recognition_attempt_id(
            "listing-field-mapping:att1:u01:att1:LB:0001-of-0002"
        )
        == "att1"
    )
    assert (
        recognition_attempt_id("listing-field-mapping-verifier:att2:u01:att2:LB:x")
        == "att2"
    )
    assert recognition_attempt_id("document-authority:att3:x") == ""
    assert recognition_attempt_id("") == ""


def test_failure_class_for_codes() -> None:
    assert failure_class_for("provider_runtime_error") == "infra"
    assert failure_class_for("queue_dwell_timeout") == "content"
    assert failure_class_for("") == ""
