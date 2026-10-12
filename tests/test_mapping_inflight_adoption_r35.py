"""R35轮（R35-01）：识别长时间停滞时的知情降级采纳（「采用已识别字段继续」）。

B位实测（54表大工作簿）：字段识别停滞82分钟不推进也不落终态——
R34-07动态收割视界使大队列的终态失败最早也在数小时后，而「采用已识别
字段继续」入口只在全部作业落终态失败（needs_attention）后出现，用户被
夹在「不失败、不推进、无出路」死态。

修复合同：
- adopt_draft在generating态默认照旧拒绝（R19-01契约不变）；
- 仅显式include_incomplete（界面降级按钮）放行在途知情采纳；
- 在途分片按部分采纳同规约排除出草稿，其(域,槽位)豁免完整性门并
  物化为「尚未完成」缺口记录（与终态失败缺口如实区分）。
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_monitoring_mapping_draft_repository import (  # noqa: E402
    _seed_chunk,
)
from packages.medical_monitoring.admission.mapping_confirmation import (  # noqa: E402
    AdmissionMappingConfirmationService,
    AdmissionMappingPipelineError,
)
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (  # noqa: E402
    MappingDraftAdoptRequest,
)
from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)
from services.api.app.monitoring_mapping_draft_repository import (  # noqa: E402
    MonitoringMappingDraftRepository,
)


@pytest.fixture()
def repositories(tmp_path: Path):
    path = tmp_path / "monitoring-r35.sqlite3"
    return path, MonitoringAiRepository(path), MonitoringMappingDraftRepository(path)


def _seed_cohort_with_inflight_chunk(ai_repository: MonitoringAiRepository) -> None:
    """AE域2分片：chunk1完成、chunk2保持queued（在途）；CM域完整。

    注意顺序：在途chunk最后创建——claim_next按(项目运行数,created_at)
    认领，先建queued会抢走后续_completed分片的worker认领。
    """
    _seed_chunk(
        ai_repository,
        domain="AE",
        chunk_index=1,
        chunk_total=2,
        fields=("AETERM",),
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
    # chunk2只创建不认领——create_or_get后即为queued在途态。输入画像
    # 身份（full_profile_sha256等）必须与已完成分片一致，草稿装配按
    # 画像指纹聚合。
    completed_job_id = [
        job
        for job in ai_repository.list_jobs(
            "project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        )
        if job.business_key.endswith("AE:0001-of-0002")
    ][0].job_id
    reference_profile = ai_repository.input_payload(
        "project-alpha", completed_job_id,
    )["field_profile"]
    from tests.test_monitoring_mapping_draft_repository import _revision

    revision = _revision("project-alpha")
    payload = {
        "schema_version": "monitoring_ai_v1",
        "field_profile": {
            **{
                key: value
                for key, value in reference_profile.items()
                if key not in {"domain", "domain_field_count", "chunk_index",
                               "chunk_total", "fields"}
            },
            "domain": "AE",
            "domain_field_count": 2,
            "chunk_index": 2,
            "chunk_total": 2,
            "chunk_size_limit": 1,
            "fields": [
                {
                    "domain": "AE",
                    "field": "AESER",
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
    from services.api.app.monitoring_ai_contracts import MonitoringAiJobCreate

    ai_repository.create_or_get(
        MonitoringAiJobCreate(
            project_id="project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=revision,
            input_payload=payload,
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=2,
            business_key="listing-field-mapping:batch-001:AE:0002-of-0002",
        )
    )


def _service(ai_repository, mapping_repository, state: str):
    pipeline = SimpleNamespace(
        list_candidates=lambda **_kwargs: {
            "state": state,
            "confirmation_status": "pending_confirmation",
            "summary": {"candidate_count": 2},
            "candidates": [],
        },
        _task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=pipeline,
        mapping_repository=mapping_repository,
        ai_repository=ai_repository,
        prompt_version="mapping-prompt-v1",
        accepted_status="accepted",
        proposed_status="proposed",
    )
    # 测试身份内必需：种子分片的provider/model按主运行身份归类，
    # 不触发legacy路线门（生产由runtime配置提供）。
    service.primary_runtime_resolver = lambda: SimpleNamespace(
        available=True, provider="test-provider", model="test-model",
    )
    return service


def test_generating_adopt_still_rejected_without_flag(repositories) -> None:
    """默认路径：generating态照旧拒绝（R19-01契约不变）。"""
    _, ai_repository, mapping_repository = repositories
    _seed_cohort_with_inflight_chunk(ai_repository)
    service = _service(ai_repository, mapping_repository, "generating")
    with pytest.raises(AdmissionMappingPipelineError, match="mapping_run_incomplete"):
        service.adopt_draft(
            project_id="project-alpha",
            attempt_id="batch-001",
            workspace_dir=None,
            actor="medical-manager",
            reason="普通采纳",
        )


def test_inflight_adoption_uses_inflight_slots_as_gaps(repositories) -> None:
    """知情降级采纳：在途分片的(域,槽位)豁免完整性门并如实物化缺口。"""
    _, ai_repository, mapping_repository = repositories
    _seed_cohort_with_inflight_chunk(ai_repository)

    # 缺口计算：在途AE chunk2在include_inflight下计入缺席槽位/缺席域，
    # 默认路径不计（保持既有终态失败口径）。
    jobs = ai_repository.list_jobs(
        "project-alpha",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix="listing-field-mapping:batch-001:",
    )
    completed_ids = {
        job.job_id for job in jobs if job.status.value == "completed"
    }
    probe = _service(ai_repository, mapping_repository, "generating")
    gaps_default, _reasons_default, slots_default = (
        probe._terminal_failure_domain_gaps(
            project_id="project-alpha",
            jobs=jobs,
            accepted_job_ids=completed_ids,
        )
    )
    assert gaps_default == () and slots_default == frozenset()
    gaps_inflight, reasons_inflight, slots_inflight = (
        probe._terminal_failure_domain_gaps(
            project_id="project-alpha",
            jobs=jobs,
            accepted_job_ids=completed_ids,
            include_inflight=True,
        )
    )
    # AE已有completed分片覆盖（chunk1）→在途chunk2按「部分覆盖域的
    # 缺席槽位」豁免，不构成整域缺席；缺口原因如实区分「尚未完成」。
    assert gaps_inflight == ()
    assert slots_inflight == frozenset({("AE", 2)})
    assert any(
        item["domain"] == "AE" and "尚未完成" in item["reason"]
        for item in reasons_inflight
    )

    # 整域在途：EX域只有queued分片、无任何completed覆盖→整域缺席。
    from tests.test_monitoring_mapping_draft_repository import _revision
    from services.api.app.monitoring_ai_contracts import MonitoringAiJobCreate

    reference = ai_repository.input_payload(
        "project-alpha",
        [job for job in jobs if job.business_key.endswith("AE:0001-of-0002")][0].job_id,
    )["field_profile"]
    ex_payload = {
        "schema_version": "monitoring_ai_v1",
        "field_profile": {
            **{
                key: value
                for key, value in reference.items()
                if key not in {"domain", "domain_field_count", "chunk_index",
                               "chunk_total", "fields"}
            },
            "domain": "EX",
            "domain_field_count": 1,
            "chunk_index": 1,
            "chunk_total": 1,
            "chunk_size_limit": 1,
            "fields": [
                {
                    "domain": "EX",
                    "field": "EXDOSE",
                    "total_rows": 100,
                    "non_empty_count": 90,
                    "null_rate": 0.1,
                    "inferred_type": "number",
                    "unique_value_count": 20,
                    "top_values": [],
                    "representative_values": [],
                    "anomaly_examples": [],
                },
            ],
        },
    }
    ai_repository.create_or_get(
        MonitoringAiJobCreate(
            project_id="project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=_revision("project-alpha", suffix="002"),
            input_payload=ex_payload,
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=2,
            business_key="listing-field-mapping:batch-001:EX:0001-of-0001",
        )
    )
    jobs_all = ai_repository.list_jobs(
        "project-alpha",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix="listing-field-mapping:batch-001:",
    )
    gaps_whole, reasons_whole, _slots_whole = (
        probe._terminal_failure_domain_gaps(
            project_id="project-alpha",
            jobs=jobs_all,
            accepted_job_ids=completed_ids,
            include_inflight=True,
        )
    )
    assert gaps_whole == ("EX",)
    assert any(
        item["domain"] == "EX" and "尚未完成" in item["reason"]
        for item in reasons_whole
    )


def test_inflight_adoption_assembles_partial_draft_with_gaps(
    repositories,
) -> None:
    """端到端：知情降级采纳装配部分草稿——在途分片字段缺席、缺口如实。"""
    _, ai_repository, mapping_repository = repositories
    _seed_cohort_with_inflight_chunk(ai_repository)
    service = _service(ai_repository, mapping_repository, "generating")
    result = service.adopt_draft(
        project_id="project-alpha",
        attempt_id="batch-001",
        workspace_dir=None,
        actor="medical-manager",
        reason="字段识别长时间无新进展，知情采用已识别字段继续。",
        allow_inflight_adoption=True,
    )
    fields = sorted(
        (item.get("domain"), item.get("source_field"))
        for item in result.get("fields", [])
    )
    # 在途AE chunk2覆盖的AESER不在草稿中；已完成分片字段齐备。
    assert fields == [("AE", "AETERM"), ("CM", "CMTRT")]
    gaps = result.get("domain_gaps") or []
    assert any(
        item.get("domain") == "AE" and "尚未完成" in str(item.get("reason"))
        for item in gaps
    )


def test_adopt_request_model_defaults_include_incomplete_false() -> None:
    body = MappingDraftAdoptRequest(reason="普通采纳")
    assert body.include_incomplete is False
    assert MappingDraftAdoptRequest(
        reason="停滞知情采纳", include_incomplete=True
    ).include_incomplete is True
