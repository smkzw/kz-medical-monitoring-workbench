"""状态机专项S3（02_DESIGN §6.1/§7）：投影单源化。

冲突1场景参数化断言：confirmed draft + facts ready 时同一投影内
pending_confirmation_count=0、facts_generated=true、顶层
confirmation_status=confirmed、state读物化行；derive模式保留派生值；
materialized模式行缺失且cohort有作业→fail-closed。
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.admission.admission_stage_view import (  # noqa: E402
    AdmissionStageViewError,
    apply_single_source,
    stage_view_mode,
)
from packages.medical_monitoring.admission.mapping_confirmation import (  # noqa: E402
    AdmissionMappingConfirmationService,
)
from services.api.app.monitoring_admission_stage_store import (  # noqa: E402
    STAGE_RECOGNITION,
)
from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MonitoringAiJobCreate,
    MonitoringAiInputRevision,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def _confirmed_draft() -> SimpleNamespace:
    return SimpleNamespace(
        status="confirmed",
        draft_id="draft-1",
        version=7,
        fields=(
            {
                "domain": "AE",
                "source_field": "AETERM",
                "recommended_role": "ae_term",
                "field_kind": "source_collected",
                "confidence": 0.99,
                "user_action": "系统已按建议采用，无需额外操作。",
            },
        ),
    )


def _active_draft() -> SimpleNamespace:
    """active draft：AE已答、DM待答（未答疑问字段）。"""

    return SimpleNamespace(
        status="draft",
        draft_id="draft-2",
        version=3,
        fields=(
            {
                "domain": "AE",
                "source_field": "AETERM",
                "recommended_role": "ae_term",
                "field_kind": "source_collected",
                "confidence": 0.99,
                "user_action": "用户已核对：确认为不良事件术语。",
                "user_decision_required": True,
            },
            {
                "domain": "DM",
                "source_field": "AGE",
                "recommended_role": "demographics.age",
                "field_kind": "source_collected",
                "confidence": 0.42,
                "uncertainty": "低置信度",
                "user_action": "请确认该列的用途。",
                "user_decision_required": True,
            },
        ),
    )


def _base_payload() -> dict:
    return {
        "attempt_id": "batch-001",
        "cohort": "primary",
        # B1派生值（B1硬编码删除后由aggregate函数派生，此处模拟残留派生态）
        "state": "candidates_ready",
        "summary": {
            "job_count": 2,
            "completed_job_count": 2,
            "candidate_count": 2,
        },
        "candidates": [
            {
                "domain": "AE",
                "source_field": "AETERM",
                "recommended_role": "ae_term",
                "confidence": 0.99,
            },
            {
                "domain": "DM",
                "source_field": "AGE",
                "recommended_role": "demographics.age",
                "confidence": 0.42,
            },
        ],
        "jobs": [
            {"provider": "p1", "requested_model": "m1", "status": "queued"},
        ],
    }


def _facts(status: str, generated: bool) -> dict:
    return {"state": status, "facts_generated": generated}


def test_confirmed_draft_and_facts_ready_single_source() -> None:
    """冲突1场景：confirmed+facts ready→count=0、facts=true、顶层confirmed。"""

    projected = apply_single_source(
        _base_payload(),
        draft=_confirmed_draft(),
        facts_status=_facts("ready", True),
        recognition_state_row={"state": "candidates_ready"},
        recognition_jobs_exist=True,
    )
    assert projected["confirmation_status"] == "confirmed"
    assert projected["summary"]["pending_confirmation_count"] == 0
    assert projected["facts_generated"] is True
    assert projected["state"] == "candidates_ready"
    # 字段级：命中draft已确认字段→confirmed。
    statuses = {
        (item["domain"], item["source_field"]): item["confirmation_status"]
        for item in projected["candidates"]
    }
    assert statuses[("AE", "AETERM")] == "confirmed"


def test_active_draft_counts_only_unanswered_questions() -> None:
    """draft_active：count=draft内未答疑问字段数；已答字段→confirmed。"""

    projected = apply_single_source(
        _base_payload(),
        draft=_active_draft(),
        facts_status=_facts("not_generated", False),
        recognition_state_row={"state": "generating"},
        recognition_jobs_exist=True,
    )
    assert projected["confirmation_status"] == "pending_confirmation"
    assert projected["summary"]["pending_confirmation_count"] == 1
    assert projected["facts_generated"] is False
    statuses = {
        (item["domain"], item["source_field"]): item["confirmation_status"]
        for item in projected["candidates"]
    }
    assert statuses[("AE", "AETERM")] == "confirmed"
    assert statuses[("DM", "AGE")] == "pending_confirmation"


def test_no_draft_keeps_candidate_count_and_pending() -> None:
    projected = apply_single_source(
        _base_payload(),
        draft=None,
        facts_status=_facts("not_generated", False),
        recognition_state_row={"state": "generating"},
        recognition_jobs_exist=True,
    )
    assert projected["confirmation_status"] == "pending_confirmation"
    assert projected["summary"]["pending_confirmation_count"] == 2
    statuses = {
        (item["domain"], item["source_field"]): item["confirmation_status"]
        for item in projected["candidates"]
    }
    assert set(statuses.values()) == {"pending_confirmation"}


def test_materialized_mode_reads_stage_row_and_fails_closed() -> None:
    """materialized：顶层state读物化行；行缺失且有作业→fail-closed 500。"""

    assert stage_view_mode() == "materialized"
    projected = apply_single_source(
        _base_payload(),
        draft=None,
        facts_status=None,
        recognition_state_row={"state": "needs_attention"},
        recognition_jobs_exist=True,
    )
    assert projected["state"] == "needs_attention"

    with pytest.raises(AdmissionStageViewError, match="mapping_bridge_failed"):
        apply_single_source(
            _base_payload(),
            draft=None,
            facts_status=None,
            recognition_state_row=None,
            recognition_jobs_exist=True,
        )

    # 无cohort作业（行也无）→不fail（上游本就会404），保留派生态。
    projected = apply_single_source(
        _base_payload(),
        draft=None,
        facts_status=None,
        recognition_state_row=None,
        recognition_jobs_exist=False,
    )
    assert projected["state"] == "candidates_ready"


def test_derive_mode_keeps_derived_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """STAGE_VIEW_MODE=derive（S2影子回退）：顶层state保留派生值。"""

    monkeypatch.setenv("STAGE_VIEW_MODE", "derive")
    projected = apply_single_source(
        _base_payload(),
        draft=None,
        facts_status=None,
        recognition_state_row={"state": "needs_attention"},
        recognition_jobs_exist=True,
    )
    assert projected["state"] == "candidates_ready"
    monkeypatch.undo()


def test_list_for_review_single_source_end_to_end(tmp_path: Path) -> None:
    """集成：GET装配点经apply_single_source输出唯一口径。"""

    repo = MonitoringAiRepository(tmp_path / "s3.sqlite3")
    # 真实作业写点落物化行（S2路径）。
    revision = MonitoringAiInputRevision(
        project_id="project-alpha",
        batch_revision="batch-s3",
        mapping_revision="mapping-s3",
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
    repo.create_or_get(
        MonitoringAiJobCreate(
            project_id="project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=revision,
            input_payload={"schema_version": "monitoring_ai_v1"},
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=2,
            business_key="listing-field-mapping:batch-001:AE:0001-of-0001",
        )
    )
    row = repo.stage_store.get_stage("project-alpha", "batch-001", STAGE_RECOGNITION)
    assert row is not None and row["state"] == "generating"

    pipeline = SimpleNamespace(
        list_candidates=lambda **_kwargs: _base_payload(),
        _task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
    )
    mapping_repository = SimpleNamespace(
        find_draft_for_batch=lambda *_args: _confirmed_draft(),
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=pipeline,
        mapping_repository=mapping_repository,
        ai_repository=repo,
        prompt_version="mapping-prompt-v1",
        accepted_status="accepted",
        proposed_status="proposed",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        primary_runtime_resolver=lambda: SimpleNamespace(
            available=True, provider="test-provider", model="test-model",
        ),
        facts_status_resolver=lambda **_kwargs: _facts("ready", True),
    )
    projected = service.list_for_review(
        project_id="project-alpha",
        attempt_id="batch-001",
        workspace_dir=None,
    )
    # 冲突1四字段同一投影内一致（02_DESIGN §7 S3验收断言）。
    assert projected["confirmation_status"] == "confirmed"
    assert projected["summary"]["pending_confirmation_count"] == 0
    assert projected["facts_generated"] is True
    assert projected["state"] == "generating"  # 物化行（真实作业在队）
    assert projected["draft"]["status"] == "confirmed"
