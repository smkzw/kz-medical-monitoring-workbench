"""E2E拦截修复（2/3，20261016）：整域缺口部分采纳的确认链死锁。

E2E实测（MX循SM1-CSU，EX--试验用药分片invalid_ai_output预算耗尽）：
- 部分采纳成功（EX整域豁免、domain_gaps物化）后，确认×5恒409
  mapping_verifier_job_failed——reconcile_with_verifier装载主cohort时
  _completed_candidates对「存在终态失败分片」无条件硬失败，缺口豁免
  （R10/R31）与对账exempt_domains（R11）都没有机会生效；
- 知情降级确认×2恒409 mapping_draft_source_unavailable——库层域完整性
  门在再校验路径把装配时已豁免的整域缺口重判为missing（槽位级门有
  revalidating_persisted_draft放行、域级门没有）。

修复合同：
- reconcile先算缺口再装载候选：缺口域终态失败分片按缺口语义跳过
  （对齐verifier侧缺席域「单侧结果不构成双模型比对」），非缺口域
  失败分片照旧硬失败；
- 库层域完整性门在revalidating_persisted_draft=True时按装配时豁免
  口径放行整域缺口（持久化草稿接受分片集由source_set_sha256钉死）；
- 装配路径仍必须显式携带豁免集（缺豁免照旧硬拒，绝不凭空放宽）。
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.admission.mapping_confirmation import (  # noqa: E402
    AdmissionMappingConfirmationService,
    AdmissionMappingPipelineError,
)
from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MonitoringAiCandidateStatus,
    MonitoringAiInputRevision,
    MonitoringAiJobCreate,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)
from services.api.app.monitoring_mapping_draft_repository import (  # noqa: E402
    MonitoringMappingDraftRepository,
)
from tests.test_monitoring_mapping_draft_repository import (  # noqa: E402
    PROFILE_HASH,
    SOURCE_HASH,
)

PROJECT = "project-alpha"
BATCH = "batch-001"


def _seed_completed_chunk(
    ai_repository: MonitoringAiRepository,
    *,
    domain: str,
    fields: tuple[str, ...],
    expected_domains: tuple[str, ...],
) -> None:
    """种一个完成的分片（候选带field_mappings，供对账/cohort装载）。"""

    from tests.test_monitoring_mapping_draft_repository import (
        _candidate,
        _mapping,
    )

    revision = MonitoringAiInputRevision(
        project_id=PROJECT,
        batch_revision="batch-gap",
        mapping_revision="pre-mapping-gap",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-listing",
                source_content_sha256=SOURCE_HASH,
            ),
        ),
    )
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
            "project_id": PROJECT,
            "batch_id": BATCH,
            "batch_revision": 1,
            "expected_domains": list(expected_domains),
            "full_profile_sha256": PROFILE_HASH,
            "full_input_sha256": "c" * 64,
            "full_field_count": 2,
            "domain": domain,
            "domain_field_count": 1,
            "chunk_index": 1,
            "chunk_total": 1,
            "chunk_size_limit": 1,
            "fields": profile_fields,
        },
    }
    created = ai_repository.create_or_get(
        MonitoringAiJobCreate(
            project_id=PROJECT,
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=revision,
            input_payload=payload,
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=2,
            business_key=(
                f"listing-field-mapping:{BATCH}:{domain}:0001-of-0001"
            ),
        )
    )
    running = ai_repository.claim_next(f"worker-{domain}")
    assert running.job_id == created.job_id
    candidates = (
        _candidate(
            running,
            fields,
            candidate_suffix="1",
        ),
    )
    ai_repository.complete(
        running,
        owner=f"worker-{domain}",
        response_model="test-model",
        raw_output={"candidates": 1},
        candidates=candidates,
    )
    for candidate in candidates:
        ai_repository.decide_candidate(
            PROJECT,
            candidate.candidate_id,
            decision=MonitoringAiCandidateStatus.ACCEPTED,
            actor="medical-manager",
            reason="同意纳入字段映射草稿",
            current_input_revision_sha256=running.input_revision_sha256,
        )


def _seed_failed_whole_domain(
    ai_repository: MonitoringAiRepository,
    *,
    domain: str = "EX",
    expected_domains: tuple[str, ...] = ("AE", "CM", "EX"),
    failure_code: str = "invalid_ai_output",
) -> None:
    """种一个整域失败的域（全部主分片终态失败，内容级确定性失败）。"""

    revision = MonitoringAiInputRevision(
        project_id=PROJECT,
        batch_revision="batch-gap",
        mapping_revision="pre-mapping-gap",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-listing",
                source_content_sha256=SOURCE_HASH,
            ),
        ),
    )
    payload = {
        "schema_version": "monitoring_ai_v1",
        "field_profile": {
            "schema_version": "monitoring_ai_field_profile_v1",
            "scope": "complete_profile_chunk",
            "project_id": PROJECT,
            "batch_id": BATCH,
            "batch_revision": 1,
            "expected_domains": list(expected_domains),
            "full_profile_sha256": PROFILE_HASH,
            "full_input_sha256": "c" * 64,
            "full_field_count": 2,
            "domain": domain,
            "domain_field_count": 5,
            "chunk_index": 1,
            "chunk_total": 1,
            "chunk_size_limit": 1,
            "fields": [
                {
                    "domain": domain,
                    "field": "EXDOSE",
                    "total_rows": 100,
                    "non_empty_count": 90,
                    "null_rate": 0.1,
                    "inferred_type": "string",
                    "unique_value_count": 20,
                    "top_values": [],
                    "representative_values": [],
                    "anomaly_examples": [],
                }
            ],
        },
    }
    created = ai_repository.create_or_get(
        MonitoringAiJobCreate(
            project_id=PROJECT,
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=revision,
            input_payload=payload,
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=2,
            business_key=(
                f"listing-field-mapping:{BATCH}:{domain}:0001-of-0001"
            ),
        )
    )
    claimed = ai_repository.claim_next(f"worker-failed-{domain}")
    assert claimed.job_id == created.job_id
    failed = ai_repository.fail(
        claimed,
        owner=f"worker-failed-{domain}",
        failure_code=failure_code,
        failure_message="模型输出违约（内容级确定性失败）",
        retryable=False,
    )
    assert failed.status.value == "failed"


@pytest.fixture()
def repositories(tmp_path: Path):
    path = tmp_path / "monitoring-gap.sqlite3"
    ai_repository = MonitoringAiRepository(path)
    mapping_repository = MonitoringMappingDraftRepository(path)
    return ai_repository, mapping_repository


def _seed_cohort_with_whole_domain_gap(ai_repository) -> None:
    _seed_completed_chunk(
        ai_repository,
        domain="AE",
        fields=("AETERM",),
        expected_domains=("AE", "CM", "EX"),
    )
    _seed_completed_chunk(
        ai_repository,
        domain="CM",
        fields=("CMTRT",),
        expected_domains=("AE", "CM", "EX"),
    )
    _seed_failed_whole_domain(ai_repository, domain="EX")


def test_whole_domain_gap_draft_confirms_without_source_error(
    repositories,
) -> None:
    """整域缺口部分采纳：edit/confirm再校验不再重判已豁免缺口。

    修复前：confirm的_validated_source（revalidating路径）把装配时已
    豁免的EX重判missing→SourceStateError「expected field mapping
    domains are missing: EX」→降级确认409 mapping_draft_source_
    unavailable「本次结果未保存」（E2E实测降级×2同错）。
    """

    ai_repository, mapping_repository = repositories
    _seed_cohort_with_whole_domain_gap(ai_repository)
    completed_ids = tuple(
        job.job_id
        for job in ai_repository.list_jobs(
            PROJECT,
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        )
        if job.status.value == "completed"
    )
    assert len(completed_ids) == 2

    draft = mapping_repository.assemble(
        PROJECT,
        BATCH,
        PROFILE_HASH,
        expected_job_ids=completed_ids,
        allowed_missing_domains=frozenset({"EX"}),
    )
    assert draft.fields

    edited = mapping_repository.edit_field(
        PROJECT,
        draft.draft_id,
        domain="AE",
        source_field="AETERM",
        patch={"confidence": 0.91},
        expected_version=draft.version,
        actor="medical-manager",
        idempotency_key="edit-gap-aeterm",
    )
    assert edited.version == draft.version + 1

    revision = mapping_repository.confirm(
        PROJECT,
        edited.draft_id,
        expected_version=edited.version,
        confirmed_by="medical-manager",
        confirmation_reason="整域缺口部分采纳的知情确认。",
        idempotency_key="confirm-gap-partial",
    )
    assert revision.confirmed_by == "medical-manager"


def test_assemble_without_exemption_still_fails_closed(repositories) -> None:
    """装配路径不传豁免集：整域缺口照旧硬拒（绝不凭空放宽）。"""

    ai_repository, mapping_repository = repositories
    _seed_cohort_with_whole_domain_gap(ai_repository)
    from services.api.app.monitoring_mapping_draft_repository import (
        MonitoringMappingSourceStateError,
    )

    completed_ids = tuple(
        job.job_id
        for job in ai_repository.list_jobs(
            PROJECT,
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        )
        if job.status.value == "completed"
    )
    with pytest.raises(
        MonitoringMappingSourceStateError,
        match="expected field mapping domains are missing: EX",
    ):
        mapping_repository.assemble(
            PROJECT,
            BATCH,
            PROFILE_HASH,
            expected_job_ids=completed_ids,
        )


def test_reconcile_skips_gap_domain_failed_shards(repositories) -> None:
    """对账装载跳过缺口域终态失败分片（不再mapping_verifier_job_failed）。

    修复前：reconcile_with_verifier对主cohort全量装载，EX失败分片触发
    _completed_candidates硬失败→确认×5恒409（E2E实测）。修复后缺口
    豁免先生效，对账以exempt_domains继续，domain_gaps如实透出。
    """

    ai_repository, mapping_repository = repositories
    _seed_cohort_with_whole_domain_gap(ai_repository)
    completed_ids = tuple(
        job.job_id
        for job in ai_repository.list_jobs(
            PROJECT,
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        )
        if job.status.value == "completed"
    )
    draft = mapping_repository.assemble(
        PROJECT,
        BATCH,
        PROFILE_HASH,
        expected_job_ids=completed_ids,
        allowed_missing_domains=frozenset({"EX"}),
    )

    pipeline = SimpleNamespace(
        _task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=pipeline,
        mapping_repository=mapping_repository,
        ai_repository=ai_repository,
        prompt_version="mapping-prompt-v1",
        accepted_status=MonitoringAiCandidateStatus.ACCEPTED,
        proposed_status=MonitoringAiCandidateStatus.PROPOSED,
    )
    service.primary_runtime_resolver = lambda: SimpleNamespace(
        available=True, provider="test-provider", model="test-model",
    )

    # 盲核侧注入主侧同款候选（单侧一致→agreement路径）——本测试聚焦
    # 主cohort装载不再被缺口域失败分片卡死，不构造真实双盲分歧。
    from packages.medical_monitoring.admission.mapping_confirmation import (
        MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX,
        _value,
    )

    primary_jobs = service._mapping_jobs(
        PROJECT, BATCH, MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX,
    )
    verifier_candidates = tuple(
        candidate
        for job in primary_jobs
        if str(_value(job.status)) == "completed"
        for candidate in ai_repository.candidates(PROJECT, job.job_id)
    )
    projected = service.reconcile_with_verifier(
        project_id=PROJECT,
        attempt_id=BATCH,
        draft_id=draft.draft_id,
        verifier_candidates=verifier_candidates,
        workspace_dir=None,
    )
    gap_list = projected.get("domain_gaps") or []
    assert [item["domain"] for item in gap_list] == ["EX"]
    assert "reconciliation" in projected
