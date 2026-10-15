"""状态机专项T3（02_DESIGN §5-T3/§2.2 mapping_confirmation表）：draft事件留痕。

覆盖：adopt/edit/confirm→事件链完整；confirm幂等重放不重复落事件；
CAS冲突回滚→事件不存在（同事务性）；draft回执与事件detail一致；
降级采纳/降级确认另记degradation；不建状态行（§2.5裁决）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)
from services.api.app.monitoring_mapping_draft_repository import (  # noqa: E402
    MonitoringMappingDraftRepository,
    MonitoringMappingStateConflictError,
)
from tests.test_monitoring_mapping_draft_repository import (  # noqa: E402
    PROFILE_HASH,
    _seed_chunk,
    _seed_complete_source,
)

PROJECT = "project-alpha"
BATCH = "batch-001"


@pytest.fixture
def repositories(tmp_path: Path):
    path = tmp_path / "monitoring.sqlite3"
    ai_repository = MonitoringAiRepository(path)
    mapping_repository = MonitoringMappingDraftRepository(path)
    return ai_repository, mapping_repository


def _draft_events(
    mapping_repository: MonitoringMappingDraftRepository,
) -> list[dict]:
    return mapping_repository.stage_store.list_events(
        PROJECT, BATCH, stage="mapping_confirmation", limit=1000
    )


def test_adopt_edit_confirm_event_chain_complete(repositories) -> None:
    """adopt→draft_active(v1)、edit→v2、confirm→confirmed全链留痕。"""

    ai_repository, mapping_repository = repositories
    _seed_complete_source(ai_repository)

    draft = mapping_repository.assemble(PROJECT, BATCH, PROFILE_HASH)
    events = _draft_events(mapping_repository)
    assert [(event["event_type"], event["from_state"], event["to_state"]) for event in events] == [
        ("state_changed", "no_draft", "draft_active"),
    ]
    assert events[0]["attempt_id"] == BATCH
    assert events[0]["stage"] == "mapping_confirmation"
    assert events[0]["detail_json"]
    import json as _json

    detail = _json.loads(events[0]["detail_json"])
    assert detail["draft_id"] == draft.draft_id
    assert detail["version"] == 1

    edited = mapping_repository.edit_field(
        PROJECT,
        draft.draft_id,
        domain="AE",
        source_field="AETERM",
        patch={"confidence": 0.95},
        expected_version=1,
        actor="medical-manager",
        idempotency_key="t3-edit-001",
    )
    assert edited.version == 2
    events = _draft_events(mapping_repository)
    assert len(events) == 2
    assert (events[1]["event_type"], events[1]["to_state"]) == (
        "state_changed",
        "draft_active",
    )
    detail = _json.loads(events[1]["detail_json"])
    assert detail["version"] == 2
    assert detail["previous_version"] == 1
    assert detail["operation"] == "edit_field"

    revision = mapping_repository.confirm(
        PROJECT,
        edited.draft_id,
        expected_version=2,
        confirmed_by="medical-manager",
        confirmation_reason="无疑问且复核收敛，确认字段映射。",
        idempotency_key="t3-confirm-001",
    )
    events = _draft_events(mapping_repository)
    assert len(events) == 3
    assert (events[2]["event_type"], events[2]["from_state"], events[2]["to_state"]) == (
        "state_changed",
        "draft_active",
        "confirmed",
    )
    # draft回执与事件detail一致：mapping_revision可对账。
    detail = _json.loads(events[2]["detail_json"])
    assert detail["mapping_revision"] == revision.mapping_revision
    assert detail["draft_id"] == edited.draft_id
    # 不建状态行（§2.5裁决：drafts权威行本身即状态行）。
    assert (
        mapping_repository.stage_store.get_stage(PROJECT, BATCH, "mapping_confirmation")
        is None
    )


def test_confirm_idempotent_replay_does_not_duplicate_events(repositories) -> None:
    """幂等重放（同idempotency_key）返回原revision且不重复落事件。"""

    ai_repository, mapping_repository = repositories
    _seed_complete_source(ai_repository)
    draft = mapping_repository.assemble(PROJECT, BATCH, PROFILE_HASH)
    revision = mapping_repository.confirm(
        PROJECT,
        draft.draft_id,
        expected_version=1,
        confirmed_by="medical-manager",
        confirmation_reason="确认。",
        idempotency_key="t3-confirm-replay",
    )
    before = _draft_events(mapping_repository)
    assert len(before) == 2  # adopt + confirm

    repeated = mapping_repository.confirm(
        PROJECT,
        draft.draft_id,
        expected_version=1,
        confirmed_by="medical-manager",
        confirmation_reason="确认。",
        idempotency_key="t3-confirm-replay",
    )
    assert repeated.mapping_revision == revision.mapping_revision
    after = _draft_events(mapping_repository)
    assert len(after) == len(before)


def test_cas_conflict_rollback_leaves_no_event(repositories) -> None:
    """CAS冲突回滚→事件不存在（事件与draft写同一事务）。"""

    ai_repository, mapping_repository = repositories
    _seed_complete_source(ai_repository)
    draft = mapping_repository.assemble(PROJECT, BATCH, PROFILE_HASH)

    with pytest.raises(MonitoringMappingStateConflictError):
        mapping_repository.edit_field(
            PROJECT,
            draft.draft_id,
            domain="AE",
            source_field="AETERM",
            patch={"confidence": 0.95},
            expected_version=99,  # CAS失配
            actor="medical-manager",
            idempotency_key="t3-edit-stale",
        )
    with pytest.raises(MonitoringMappingStateConflictError):
        mapping_repository.confirm(
            PROJECT,
            draft.draft_id,
            expected_version=99,  # CAS失配
            confirmed_by="medical-manager",
            confirmation_reason="过期版本确认。",
            idempotency_key="t3-confirm-stale",
        )
    events = _draft_events(mapping_repository)
    assert len(events) == 1  # 仅adopt事件，冲突事务的埋点全部回滚


def test_partial_adoption_records_degradation_event(repositories) -> None:
    """部分采纳（域豁免）=降级采纳→另记degradation事件。"""

    ai_repository, mapping_repository = repositories
    _seed_chunk(
        ai_repository,
        project_id=PROJECT,
        batch_id=BATCH,
        domain="AE",
        chunk_index=1,
        chunk_total=1,
        fields=("AETERM",),
        domain_field_count=1,
        full_field_count=1,
        expected_domains=("AE", "CM"),
    )
    draft = mapping_repository.assemble(
        PROJECT,
        BATCH,
        PROFILE_HASH,
        decision_actor="medical-manager",
        decision_reason="部分采纳",
        allowed_missing_domains=("CM",),
    )
    events = _draft_events(mapping_repository)
    kinds = [(event["event_type"], event["to_state"]) for event in events]
    assert ("state_changed", "draft_active") in kinds
    assert ("degradation", "draft_active") in kinds
    degradation = next(
        event for event in events if event["event_type"] == "degradation"
    )
    assert degradation["reason_code"] == "partial_adoption"
    assert degradation["actor"] == "medical-manager"
    assert draft.draft_id


def test_degraded_confirm_records_degradation_event(repositories) -> None:
    """降级确认（知情跳过双盲复核）→confirmed之外另记degradation。"""

    ai_repository, mapping_repository = repositories
    _seed_complete_source(ai_repository)
    draft = mapping_repository.assemble(PROJECT, BATCH, PROFILE_HASH)
    mapping_repository.confirm(
        PROJECT,
        draft.draft_id,
        expected_version=1,
        confirmed_by="medical-manager",
        confirmation_reason="双盲复核未完成，知情降级确认。",
        idempotency_key="t3-confirm-degraded",
        degraded=True,
    )
    events = _draft_events(mapping_repository)
    degradations = [
        event for event in events if event["event_type"] == "degradation"
    ]
    assert len(degradations) == 1
    assert degradations[0]["reason_code"] == "dual_review_degraded"
    assert degradations[0]["to_state"] == "confirmed"


def test_no_state_row_for_mapping_stage(repositories) -> None:
    """映射阶段任何写点都不建stage_state行（drafts权威行即状态行）。"""

    ai_repository, mapping_repository = repositories
    _seed_complete_source(ai_repository)
    draft = mapping_repository.assemble(PROJECT, BATCH, PROFILE_HASH)
    mapping_repository.edit_field(
        PROJECT,
        draft.draft_id,
        domain="AE",
        source_field="AETERM",
        patch={"confidence": 0.9},
        expected_version=1,
        actor="medical-manager",
        idempotency_key="t3-edit-norow",
    )
    mapping_repository.confirm(
        PROJECT,
        draft.draft_id,
        expected_version=2,
        confirmed_by="medical-manager",
        confirmation_reason="确认。",
        idempotency_key="t3-confirm-norow",
    )
    assert (
        mapping_repository.stage_store.get_stage(PROJECT, BATCH, "mapping_confirmation")
        is None
    )
