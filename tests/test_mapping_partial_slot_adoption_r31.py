"""R31轮（R31-02）：混合域部分分片失败时的知情采纳不再被422硬拒。

R31C-MY008实测：36表556字段全量识别后，收割（queue_dwell_timeout）
使部分域呈「部分分片completed+部分分片failed」混合态；用户无任何修改
点击「采用已识别的556个字段并继续」100%被422「字段修订内容无效」
拒绝——库层槽位完整性门`domain {d} has missing or extra chunk slots`
对混合域硬拒，且_repo_error_code把SourceStateError归因为用户输入非法。

修复合同：
- 装配路径：只有确认层显式计算出的终态失败槽位（allowed_missing_slots）
  才豁免；未传豁免时混合域仍然fail-closed（原有强校验不放松）。
- 豁免域的缺失字段如实物化到domain_gaps；部分覆盖域按在场分片核对。
- 已持久化的部分草稿在edit/confirm再校验时不再因装配后作业状态变化
  被推翻（source_set_sha256内容钉死身份）。
- 源状态错误与用户输入错误分开归因（409 mapping_draft_source_unavailable）。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_monitoring_mapping_draft_repository import (  # noqa: E402
    PROFILE_HASH,
    _seed_chunk,
)
from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MonitoringAiCandidateStatus,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)
from services.api.app.monitoring_mapping_draft_repository import (  # noqa: E402
    MonitoringMappingDraftRepository,
    MonitoringMappingSourceStateError,
)
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (  # noqa: E402
    _MAPPING_MESSAGES,
    _MAPPING_STATUS_CODES,
    _repo_error_code,
)


@pytest.fixture()
def repositories(tmp_path: Path):
    path = tmp_path / "monitoring-r31.sqlite3"
    ai_repository = MonitoringAiRepository(path)
    mapping_repository = MonitoringMappingDraftRepository(path)
    return path, ai_repository, mapping_repository


def _seed_failed_chunk(
    ai_repository: MonitoringAiRepository,
    *,
    project_id: str = "project-alpha",
    batch_id: str = "batch-001",
    domain: str,
    chunk_index: int,
    chunk_total: int,
    fields: tuple[str, ...],
    domain_field_count: int,
    full_field_count: int = 3,
    failure_code: str = "queue_dwell_timeout",
) -> None:
    """Seed one chunk whose job reached a terminal failure state.

    Mirrors the R31 production shape: the chunk was created with the rest
    of the cohort but was reaped by the queue dwell watchdog without ever
    completing.
    """

    from tests.test_monitoring_mapping_draft_repository import _revision

    revision = _revision(project_id)
    profile_fields = [
        {
            "domain": domain,
            "field": field,
            "total_rows": 100,
            "non_empty_count": 90,
            "null_rate": 0.1,
            "inferred_type": "string",
            "unique_value_count": 20,
            "top_values": [],
            "representative_values": [],
            "anomaly_examples": [],
        }
        for field in fields
    ]
    payload = {
        "schema_version": "monitoring_ai_v1",
        "field_profile": {
            "schema_version": "monitoring_ai_field_profile_v1",
            "scope": "complete_profile_chunk",
            "project_id": project_id,
            "batch_id": batch_id,
            "batch_revision": 1,
            "expected_domains": ["AE", "CM"],
            "full_profile_sha256": PROFILE_HASH,
            "full_input_sha256": "c" * 64,
            "full_field_count": full_field_count,
            "domain": domain,
            "domain_field_count": domain_field_count,
            "chunk_index": chunk_index,
            "chunk_total": chunk_total,
            "chunk_size_limit": 1,
            "fields": profile_fields,
        },
    }
    from services.api.app.monitoring_ai_contracts import MonitoringAiJobCreate

    created = ai_repository.create_or_get(
        MonitoringAiJobCreate(
            project_id=project_id,
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=revision,
            input_payload=payload,
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=2,
            business_key=(
                f"listing-field-mapping:{batch_id}:{domain}:"
                f"{chunk_index:04d}-of-{chunk_total:04d}"
            ),
        )
    )
    claimed = ai_repository.claim_next(f"worker-failed-{created.job_id}")
    assert claimed is not None
    failed = ai_repository.fail(
        claimed,
        owner=f"worker-failed-{created.job_id}",
        failure_code=failure_code,
        failure_message="作业在队列中滞留超过收割视界仍未获得执行终态。",
        retryable=False,
    )
    assert failed.status.value == "failed"


def _seed_mixed_cohort(ai_repository: MonitoringAiRepository) -> None:
    """AE域2分片：chunk1完成、chunk2终态失败（混合域）；CM域完整。"""
    _seed_chunk(
        ai_repository,
        domain="AE",
        chunk_index=1,
        chunk_total=2,
        fields=("AETERM",),
        domain_field_count=2,
    )
    _seed_failed_chunk(
        ai_repository,
        domain="AE",
        chunk_index=2,
        chunk_total=2,
        fields=("AESER",),
        domain_field_count=2,
    )
    _seed_chunk(
        ai_repository,
        domain="CM",
        chunk_index=1,
        chunk_total=1,
        fields=("CMTRT",),
        domain_field_count=1,
    )


def test_mixed_domain_still_fails_closed_without_slot_exemption(
    repositories,
) -> None:
    """未显式豁免时混合域缺槽位照旧硬拒——修复绝不放宽默认防线。"""
    _, ai_repository, mapping_repository = repositories
    _seed_mixed_cohort(ai_repository)
    completed_ids = tuple(
        job.job_id
        for job in ai_repository.list_jobs(
            "project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        )
        if job.status.value == "completed"
    )
    with pytest.raises(MonitoringMappingSourceStateError, match="chunk slots"):
        mapping_repository.assemble(
            "project-alpha",
            "batch-001",
            PROFILE_HASH,
            expected_job_ids=completed_ids,
        )


def test_assemble_with_slot_exemption_adopts_partial_domain(
    repositories,
) -> None:
    """确认层显式豁免终态失败槽位后，混合域部分采纳成功且缺口如实。"""
    _, ai_repository, mapping_repository = repositories
    _seed_mixed_cohort(ai_repository)
    completed_ids = tuple(
        job.job_id
        for job in ai_repository.list_jobs(
            "project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        )
        if job.status.value == "completed"
    )
    draft = mapping_repository.assemble(
        "project-alpha",
        "batch-001",
        PROFILE_HASH,
        expected_job_ids=completed_ids,
        allowed_missing_slots=frozenset({("AE", 2)}),
    )
    field_pairs = {(f.domain, f.source_field) for f in draft.fields}
    assert field_pairs == {("AE", "AETERM"), ("CM", "CMTRT")}
    assert ("AE", "AESER") not in field_pairs


def test_persisted_partial_draft_survives_edit_and_confirm(
    repositories,
) -> None:
    """部分草稿的edit/confirm再校验不被装配后的作业状态变化推翻。"""
    _, ai_repository, mapping_repository = repositories
    _seed_mixed_cohort(ai_repository)
    completed_ids = tuple(
        job.job_id
        for job in ai_repository.list_jobs(
            "project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        )
        if job.status.value == "completed"
    )
    draft = mapping_repository.assemble(
        "project-alpha",
        "batch-001",
        PROFILE_HASH,
        expected_job_ids=completed_ids,
        allowed_missing_slots=frozenset({("AE", 2)}),
    )
    edited = mapping_repository.edit_field(
        "project-alpha",
        draft.draft_id,
        domain="AE",
        source_field="AETERM",
        patch={"confidence": 0.91},
        expected_version=draft.version,
        actor="medical-manager",
        idempotency_key="edit-aeterm-r31",
    )
    assert edited.version == draft.version + 1
    revision = mapping_repository.confirm(
        "project-alpha",
        edited.draft_id,
        expected_version=edited.version,
        confirmed_by="medical-manager",
        confirmation_reason="R31轮部分采纳后确认：缺失分片已如实列示。",
        idempotency_key="confirm-r31-partial",
    )
    assert revision.confirmed_by == "medical-manager"


def test_wrong_exemption_never_sneaks_missing_slot_through(
    repositories,
) -> None:
    """豁免集必须精确匹配终态失败槽位——豁免在场槽位不能放走缺席。"""
    _, ai_repository, mapping_repository = repositories
    _seed_mixed_cohort(ai_repository)
    completed_ids = tuple(
        job.job_id
        for job in ai_repository.list_jobs(
            "project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        )
        if job.status.value == "completed"
    )
    # 豁免了错误的方向（在场槽位AE:1/CM:1而非失败槽位AE:2）——缺席
    # 槽位不在豁免集内，照旧硬拒。
    with pytest.raises(MonitoringMappingSourceStateError, match="chunk slots"):
        mapping_repository.assemble(
            "project-alpha",
            "batch-001",
            PROFILE_HASH,
            expected_job_ids=completed_ids,
            allowed_missing_slots=frozenset({("AE", 1), ("CM", 1)}),
        )


def test_terminal_failure_gaps_returns_partial_slots_and_reasons(
    repositories,
) -> None:
    from packages.medical_monitoring.admission.mapping_confirmation import (
        AdmissionMappingConfirmationService,
    )

    _, ai_repository, _ = repositories
    _seed_mixed_cohort(ai_repository)
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=None,
        mapping_repository=None,
        ai_repository=ai_repository,
        prompt_version="mapping-prompt-v1",
        accepted_status=MonitoringAiCandidateStatus.ACCEPTED,
        proposed_status=MonitoringAiCandidateStatus.PROPOSED,
    )
    jobs = ai_repository.list_jobs(
        "project-alpha",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
    )
    gaps, reasons, slots = service._terminal_failure_domain_gaps(
        project_id="project-alpha",
        jobs=jobs,
        accepted_job_ids={
            job.job_id for job in jobs if job.status.value == "completed"
        },
    )
    # AE是混合域（部分分片失败）→槽位豁免；CM全completed→无缺口。
    assert gaps == ()
    assert slots == frozenset({("AE", 2)})
    partial_reasons = [r for r in reasons if r["domain"] == "AE"]
    assert partial_reasons and "1 个识别分片终态失败" in partial_reasons[0]["reason"]


def test_source_state_error_attribution_is_not_user_input() -> None:
    """源状态错误归因409+系统侧文案，不再伪装成「字段修订内容无效」。"""

    class MonitoringMappingSourceStateErrorStub(ValueError):
        pass

    code = _repo_error_code(MonitoringMappingSourceStateErrorStub("boom"))
    assert code == "mapping_draft_source_unavailable"
    assert _MAPPING_STATUS_CODES[code] == 409
    # 不再把用户往「检查填写内容」上指（R31C实测死循环文案）
    assert "请检查填写内容" not in _MAPPING_MESSAGES[code]
    # 用户输入非法的422归因保持不变
    assert _repo_error_code(ValueError("bad user payload")) == (
        "mapping_draft_invalid"
    )
    assert "请检查填写内容" in _MAPPING_MESSAGES["mapping_draft_invalid"]