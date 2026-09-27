"""Monitoring AI DTO合同测试（tests/test_monitoring_ai_contracts.py）。

服务/包/前端三层共用的数据契约边界在此钉住（补齐编排门引用的本文件；
只新增覆盖，不削弱任何既有测试）。钉住的契约与理由：

- MonitoringAiInputRevision的修订摘要内容绑定：同输入同摘要、任一绑定字段
  变化即漂移、来源次序不影响摘要（入库前排序归一）——D对照的sha钉子与
  A/B可比性全部建立在该性质上。
- 来源绑定唯一性：同一entry_id不得绑多个hash，重复绑定对拒收。
- MonitoringAiJobCreate工程身份：project必须与修订一致、business_key/
  prompt_version/max_attempts边界、stable_job_id内容绑定——幂等重入
  （重复提交返回既有作业）的基础。
- 候选状态只有proposed/accepted/rejected/superseded：confirmed是draft层
  状态，候选层不存在——防AI候选静默转正（proposed扩展只存proposed）。
- validate_candidates_for_job：候选必须归属作业、初始即proposed、证据
  source/hash对必须落在输入修订来源集合内——G1『结论可回链来源』的
  数据层保障。
- candidate_confidence_summary：自动化永不放行（automation_permitted恒
  False），未评分不是高分。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from services.api.app.monitoring_ai_contracts import (
    MONITORING_AI_LOW_CONFIDENCE_THRESHOLD,
    MONITORING_AI_SCHEMA_VERSION,
    MonitoringAiCandidate,
    MonitoringAiCandidateStatus,
    MonitoringAiEvidence,
    MonitoringAiInputRevision,
    MonitoringAiJob,
    MonitoringAiJobCreate,
    MonitoringAiJobStatus,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
    candidate_confidence_summary,
    stable_job_id,
    validate_candidates_for_job,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)


def _revision(**overrides) -> MonitoringAiInputRevision:
    fields = {
        "project_id": "project-alpha",
        "batch_revision": "batch-001",
        "mapping_revision": "mapping-001",
        "sources": (
            MonitoringAiSourceBinding(
                source_entry_id="source-listing",
                source_content_sha256=SHA_A,
            ),
        ),
    }
    fields.update(overrides)
    return MonitoringAiInputRevision.model_validate(fields)


def _job(revision: MonitoringAiInputRevision, **overrides) -> MonitoringAiJob:
    fields = {
        "job_id": "monai_test000000000000000000000001",
        "project_id": revision.project_id,
        "task_type": MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        "status": MonitoringAiJobStatus.COMPLETED,
        "business_key": "listing-field-mapping:batch-001:CM:0001-of-0001",
        "input_revision": revision,
        "input_revision_sha256": revision.revision_sha256,
        "input_payload_sha256": SHA_B,
        "prompt_version": "monitoring-listing-field-mapping-v19",
        "profile_id": "profile-test",
        "provider": "test-provider",
        "requested_model": "test-model",
        "created_at": NOW,
        "updated_at": NOW,
    }
    fields.update(overrides)
    return MonitoringAiJob.model_validate(fields)


def _candidate(
    revision: MonitoringAiInputRevision,
    job: MonitoringAiJob,
    *,
    candidate_id: str = "moncand_test000000000000000000001",
    status: MonitoringAiCandidateStatus = MonitoringAiCandidateStatus.PROPOSED,
    evidence: tuple = (),
) -> MonitoringAiCandidate:
    return MonitoringAiCandidate.model_validate({
        "candidate_id": candidate_id,
        "job_id": job.job_id,
        "project_id": job.project_id,
        "task_type": job.task_type.value,
        "candidate_type": "listing_field_mapping_set",
        "title": "对照候选",
        "structured_payload": {"field_mappings": []},
        "status": status.value,
        "input_revision_sha256": revision.revision_sha256,
        "prompt_version": job.prompt_version,
        "created_at": NOW.isoformat(),
        "evidence": [
            {
                "evidence_id": e.evidence_id,
                "source_entry_id": e.source_entry_id,
                "source_content_sha256": e.source_content_sha256,
                "locator": e.locator,
                "quote": e.quote,
                "input_revision_sha256": e.input_revision_sha256,
            }
            for e in evidence
        ],
    })


def test_schema_version_present() -> None:
    assert MONITORING_AI_SCHEMA_VERSION


def test_revision_digest_is_content_bound() -> None:
    revision = _revision()
    same = _revision()
    assert revision.revision_sha256 == same.revision_sha256
    drifted = _revision(batch_revision="batch-002")
    assert revision.revision_sha256 != drifted.revision_sha256
    remapped = _revision(
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-listing",
                source_content_sha256=SHA_B,
            ),
        ),
    )
    assert revision.revision_sha256 != remapped.revision_sha256


def test_revision_sources_order_insensitive_and_sorted() -> None:
    first = _revision(
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-b", source_content_sha256=SHA_B,
            ),
            MonitoringAiSourceBinding(
                source_entry_id="source-a", source_content_sha256=SHA_A,
            ),
        ),
    )
    second = _revision(
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-a", source_content_sha256=SHA_A,
            ),
            MonitoringAiSourceBinding(
                source_entry_id="source-b", source_content_sha256=SHA_B,
            ),
        ),
    )
    assert first.revision_sha256 == second.revision_sha256
    assert [s.source_entry_id for s in first.sources] == [
        "source-a", "source-b",
    ]


def test_revision_rejects_duplicate_bindings() -> None:
    with pytest.raises(ValidationError):
        _revision(
            sources=(
                MonitoringAiSourceBinding(
                    source_entry_id="source-a", source_content_sha256=SHA_A,
                ),
                MonitoringAiSourceBinding(
                    source_entry_id="source-a", source_content_sha256=SHA_A,
                ),
            ),
        )
    with pytest.raises(ValidationError):
        _revision(
            sources=(
                MonitoringAiSourceBinding(
                    source_entry_id="source-a", source_content_sha256=SHA_A,
                ),
                MonitoringAiSourceBinding(
                    source_entry_id="source-a", source_content_sha256=SHA_B,
                ),
            ),
        )


def test_source_binding_requires_lowercase_sha256() -> None:
    with pytest.raises(ValidationError):
        MonitoringAiSourceBinding(
            source_entry_id="source-a", source_content_sha256="A" * 64,
        )
    with pytest.raises(ValidationError):
        MonitoringAiSourceBinding(
            source_entry_id="source-a", source_content_sha256="short",
        )


def test_job_create_binds_project_and_bounds() -> None:
    revision = _revision()
    payload = {"input_payload": True}
    common = dict(
        project_id=revision.project_id,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        input_revision=revision,
        input_payload=payload,
        prompt_version="monitoring-listing-field-mapping-v19",
        profile_id="profile-test",
        provider="test-provider",
        requested_model="test-model",
        business_key="listing-field-mapping:batch-001",
    )
    created = MonitoringAiJobCreate(**common)
    assert created.max_attempts == 2
    with pytest.raises(ValidationError):
        MonitoringAiJobCreate(**{**common, "project_id": "project-other"})
    with pytest.raises(ValidationError):
        MonitoringAiJobCreate(**{**common, "business_key": "x"})
    with pytest.raises(ValidationError):
        MonitoringAiJobCreate(**{**common, "max_attempts": 0})
    with pytest.raises(ValidationError):
        MonitoringAiJobCreate(**{**common, "max_attempts": 4})
    assert MonitoringAiJobCreate(**{**common, "max_attempts": 3}).max_attempts == 3


def test_stable_job_id_is_content_bound() -> None:
    revision = _revision()
    common = dict(
        project_id=revision.project_id,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        input_revision=revision,
        input_payload={"field_profile": {"fields": []}},
        prompt_version="monitoring-listing-field-mapping-v19",
        profile_id="profile-test",
        provider="test-provider",
        requested_model="test-model",
        business_key="listing-field-mapping:batch-001",
    )
    first = stable_job_id(MonitoringAiJobCreate(**common))
    second = stable_job_id(MonitoringAiJobCreate(**common))
    assert first == second and first.startswith("monai_")
    changed = stable_job_id(
        MonitoringAiJobCreate(**{**common, "prompt_version": "monitoring-listing-field-mapping-v20-tools-v1"})
    )
    assert changed != first


def test_candidate_status_contract_has_no_confirmed() -> None:
    # 候选层不存在confirmed：AI候选只能proposed/accepted/rejected/superseded；
    # confirmed是draft层状态（mapping_confirmation门后产生）。
    assert {status.value for status in MonitoringAiCandidateStatus} == {
        "proposed", "accepted", "rejected", "superseded",
    }
    assert not hasattr(MonitoringAiCandidateStatus, "CONFIRMED")


def test_validate_candidates_for_job_contract() -> None:
    revision = _revision()
    job = _job(revision)
    evidence = (
        MonitoringAiEvidence(
            evidence_id="evidence-1",
            source_entry_id="source-listing",
            source_content_sha256=SHA_A,
            locator="profile://CM/CMTRT",
            quote="CMTRT 原始列值样例",
            input_revision_sha256=revision.revision_sha256,
        ),
    )
    valid = _candidate(revision, job, evidence=evidence)
    validate_candidates_for_job(job, (valid,))

    with pytest.raises(ValueError):
        validate_candidates_for_job(job, ())
    with pytest.raises(ValueError):
        validate_candidates_for_job(
            job,
            (
                valid,
                _candidate(
                    revision,
                    job,
                    candidate_id=valid.candidate_id,
                ),
            ),
        )
    with pytest.raises(ValueError):
        validate_candidates_for_job(
            job,
            (_candidate(revision, job, status=MonitoringAiCandidateStatus.ACCEPTED),),
        )
    foreign = _candidate(revision, job).model_copy(
        update={"project_id": "project-other"},
    )
    with pytest.raises(ValueError):
        validate_candidates_for_job(job, (foreign,))
    stray_evidence = _candidate(
        revision,
        job,
        evidence=(
            MonitoringAiEvidence(
                evidence_id="evidence-x",
                source_entry_id="source-stranger",
                source_content_sha256=SHA_B,
                locator="profile://CM/CMCO",
                quote="不属于本作业来源的样例",
                input_revision_sha256=revision.revision_sha256,
            ),
        ),
    )
    with pytest.raises(ValueError):
        validate_candidates_for_job(job, (stray_evidence,))


def test_candidate_confidence_summary_never_automates() -> None:
    revision = _revision()
    job = _job(revision)
    base = {
        "candidate_id": "moncand_test000000000000000000009",
        "job_id": job.job_id,
        "project_id": job.project_id,
        "task_type": job.task_type.value,
        "candidate_type": "listing_field_mapping_set",
        "title": "对照候选",
        "input_revision_sha256": revision.revision_sha256,
        "prompt_version": job.prompt_version,
        "created_at": NOW.isoformat(),
        "evidence": [
            {
                "evidence_id": "evidence-1",
                "source_entry_id": "source-listing",
                "source_content_sha256": SHA_A,
                "locator": "profile://CM/CMTRT",
                "quote": "CMTRT 原始列值样例",
                "input_revision_sha256": revision.revision_sha256,
            }
        ],
    }

    unscored = MonitoringAiCandidate.model_validate(base)
    summary = candidate_confidence_summary(unscored)
    assert summary["status"] == "not_scored"
    assert summary["requires_user_review"] is True
    assert summary["automation_permitted"] is False

    def claim_with(confidence: float) -> dict:
        return {
            "claim_id": "claim-1",
            "kind": "recommendation",
            "text": "字段角色建议",
            "confidence": confidence,
            "uncertainty": "仍需核对",
            "user_action": "请确认",
            "evidence_ids": ["evidence-1"],
        }

    def candidate_with_claims(claims: dict) -> MonitoringAiCandidate:
        return MonitoringAiCandidate.model_validate(
            {**base, "claims": [claims]}
        )

    low = candidate_confidence_summary(
        candidate_with_claims(claim_with(0.1)),
    )
    assert low["status"] == "low"
    assert low["requires_additional_evidence"] is True
    assert low["automation_permitted"] is False

    high = candidate_confidence_summary(
        candidate_with_claims(claim_with(0.93)),
    )
    assert high["status"] == "review_required"
    assert high["confidence_floor"] == 0.93
    assert high["automation_permitted"] is False
    assert high["threshold"] == MONITORING_AI_LOW_CONFIDENCE_THRESHOLD
