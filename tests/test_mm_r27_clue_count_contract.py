"""R27-03普通跨表线索候选数合同：提示与校验同源、单一合格候选允许1个。

钉住的行为与理由：
- 修改前：提示写"输出1至3个……只能构造出合格的单一候选时只输出这一个"，
  但两层校验都要求2..3——服务层 _validate_task_specific_output 与
  持久化门 monitoring_ai_contracts.validate_candidates_for_job。模型
  服从提示输出单一合格候选会被拒收，触发修复轮/重试，属于程序造成的
  无效推理。
- 修改后：候选数边界由唯一常量
  monitoring_ai_contracts.CROSS_TABLE_CLUE_CANDIDATE_RANGE=(1,3)
  同源派生（提示文案常量、服务层校验、持久化门校验三层共用）；每候选
  仍必须引用≥2个真实原始数据域；上限3保留（防无边界输出耗尽上下文）。
- 定向核实lane恰好1候选的子合同独立保留（服务层按
  subject_context.focused_contract版本识别；持久化门按business_key的
  :focus:/:focus-p:标记识别）。旧结构下focused作业携带2-3候选会经
  范围检查外层条件意外放行，本文件一并钉住该缺口已闭合。
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from services.api.app.monitoring_ai_contracts import (
    CROSS_TABLE_CLUE_CANDIDATE_CONTRACT,
    CROSS_TABLE_CLUE_CANDIDATE_RANGE,
    MonitoringAiCandidate,
    MonitoringAiClaim,
    MonitoringAiClaimKind,
    MonitoringAiEvidence,
    MonitoringAiJobCreate,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
    validate_candidates_for_job,
)
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiInputRevision,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app import monitoring_ai_service as service_module
from services.api.app.monitoring_ai_service import (
    MonitoringAiService,
)
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiJobStatus,
)
from tests.test_monitoring_ai_service import (
    FakeProvider,
    _nonmapping_input_payload,
    _revision,
    _service,
    _valid_output,
)

HASH_A = "a" * 64


def test_candidate_contract_is_derived_from_single_range() -> None:
    """同源性：range常量唯一，service与contracts引用同一对象，提示文案
    由range派生；服务层校验源码不再手写clue候选数边界。"""
    assert CROSS_TABLE_CLUE_CANDIDATE_RANGE == (1, 3)
    assert (
        service_module.CROSS_TABLE_CLUE_CANDIDATE_RANGE
        is CROSS_TABLE_CLUE_CANDIDATE_RANGE
    )
    assert (
        service_module.CROSS_TABLE_CLUE_CANDIDATE_CONTRACT
        is CROSS_TABLE_CLUE_CANDIDATE_CONTRACT
    )
    assert CROSS_TABLE_CLUE_CANDIDATE_CONTRACT.startswith("输出1至3个")
    assert "只输出这一个" in CROSS_TABLE_CLUE_CANDIDATE_CONTRACT
    validator_source = inspect.getsource(
        MonitoringAiService._validate_task_specific_output
    )
    assert "CROSS_TABLE_CLUE_CANDIDATE_RANGE" in validator_source
    assert "cross-table clue task requires 2 to 3" not in validator_source
    # 第三张面：TASK_CONTRACTS任务合同文案同样由range派生，不再手写
    # "2至3"（该文案经payload.task_contract送达模型）。
    from services.api.app.monitoring_ai_service import TASK_CONTRACTS

    clue_contract = TASK_CONTRACTS[MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS]
    assert "1至3" in clue_contract
    assert "2至3" not in clue_contract
    assert "只输出这一个" in clue_contract


def test_clue_envelope_carries_the_same_source_contract(tmp_path: Path) -> None:
    """信封的candidate_count_contract载荷逐字使用同源常量。"""
    provider = FakeProvider([])
    service = _service(tmp_path, provider)
    service.submit_task(
        project_id="project-alpha",
        task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
        input_revision=_revision(),
        input_payload=_nonmapping_input_payload(
            source_context={"case_id": "case-001"},
        ),
        business_key="clue-count-envelope",
    )
    job = service.repository.list_jobs("project-alpha")[0]
    envelope = service._build_prompt_envelope(
        job, service.repository.input_payload(job.project_id, job.job_id)
    )
    assert (
        envelope.payload["candidate_count_contract"]
        == CROSS_TABLE_CLUE_CANDIDATE_CONTRACT
    )


@pytest.mark.parametrize("candidate_count", [1, 2, 3])
def test_ordinary_clue_lane_accepts_one_to_three_qualified_candidates(
    tmp_path: Path, candidate_count: int,
) -> None:
    """普通lane按医学意图接受1..3个候选——含此前被拒收的单一合格候选。"""
    provider = FakeProvider(
        [lambda envelope: _valid_output(envelope, candidate_count=candidate_count)]
    )
    service = _service(tmp_path, provider)
    service.submit_task(
        project_id="project-alpha",
        task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
        input_revision=_revision(),
        input_payload=_nonmapping_input_payload(
            source_context={"case_id": "case-001"},
        ),
        business_key=f"clue-count-{candidate_count}",
    )
    result = service.run_next("worker-clue")
    assert result.job is not None
    assert result.job.status == MonitoringAiJobStatus.COMPLETED, (
        result.job.failure_message
    )
    stored = service.repository.candidates("project-alpha", result.job.job_id)
    assert len(stored) == candidate_count


def test_ordinary_clue_lane_still_rejects_out_of_band_counts(
    tmp_path: Path,
) -> None:
    """上限3保留：4个候选拒收，且错误信息与同源range一致（1 to 3）。"""

    def four_candidates(envelope) -> dict:
        output = _valid_output(envelope, candidate_count=3)
        fourth = dict(output["candidates"][0])
        fourth["title"] = "监查候选 4"
        output["candidates"].append(fourth)
        return output

    provider = FakeProvider([four_candidates])
    service = _service(tmp_path, provider)
    service.submit_task(
        project_id="project-alpha",
        task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
        input_revision=_revision(),
        input_payload=_nonmapping_input_payload(
            source_context={"case_id": "case-001"},
        ),
        business_key="clue-count-overflow",
    )
    result = service.run_next("worker-clue")
    assert result.job is not None
    assert result.job.status == MonitoringAiJobStatus.FAILED
    assert "requires 1 to 3 candidates" in (result.job.failure_message or "")


def test_focused_lane_still_requires_exactly_one_candidate(
    tmp_path: Path,
) -> None:
    """定向核实子合同不受普通合同放宽影响：恰好1个；2个拒收。"""
    provider = FakeProvider(
        [lambda envelope: _valid_output(envelope, candidate_count=2)]
    )
    service = _service(tmp_path, provider)
    input_payload = _nonmapping_input_payload(
        source_context={"case_id": "case-001"},
    )
    input_payload["subject_context"] = {
        "focused_contract": {
            "version": "aemh-focused-v1",
            "expected_candidates": 1,
        }
    }
    service.submit_task(
        project_id="project-alpha",
        task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
        input_revision=_revision(),
        input_payload=input_payload,
        business_key="clue-count-focused",
    )
    result = service.run_next("worker-focused")
    assert result.job is not None
    assert result.job.status == MonitoringAiJobStatus.FAILED
    assert "focused verification requires exactly one candidate" in (
        result.job.failure_message or ""
    )

    single = FakeProvider(
        [lambda envelope: _valid_output(envelope, candidate_count=1)]
    )
    service_single = _service(tmp_path, single)
    input_payload = _nonmapping_input_payload(
        source_context={"case_id": "case-001"},
    )
    input_payload["subject_context"] = {
        "focused_contract": {
            "version": "aemh-focused-v1",
            "expected_candidates": 1,
        }
    }
    service_single.submit_task(
        project_id="project-alpha",
        task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
        input_revision=_revision(),
        input_payload=input_payload,
        business_key="clue-count-focused-single",
    )
    result_single = service_single.run_next("worker-focused-single")
    assert result_single.job is not None
    assert result_single.job.status == MonitoringAiJobStatus.COMPLETED, (
        result_single.job.failure_message
    )


# ---------------------------------------------------------------------------
# 持久化门（monitoring_ai_contracts.validate_candidates_for_job）同合同
# ---------------------------------------------------------------------------


def _clue_job(tmp_path: Path, *, business_key: str):
    clock_clock = {"value": None}

    class _Clock:
        def __call__(self):
            from datetime import datetime, timezone

            return datetime(2026, 9, 27, tzinfo=timezone.utc)

    revision = MonitoringAiInputRevision(
        project_id="project-alpha",
        batch_revision="batch-clue",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-listing",
                source_content_sha256=HASH_A,
            ),
        ),
    )
    request = MonitoringAiJobCreate(
        project_id=revision.project_id,
        task_type=MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS,
        input_revision=revision,
        input_payload={"evidence_packet": []},
        prompt_version="monitoring-cross-table-clue-synthesis-v3",
        profile_id="independent-ai-test",
        provider="test-provider",
        requested_model="test-model",
        business_key=business_key,
    )
    repository = MonitoringAiRepository(tmp_path / "clue-contracts.sqlite3")
    repository.create_or_get(request)
    return repository.claim_next("worker-contracts")


def _clue_candidate(job, index: int) -> MonitoringAiCandidate:
    evidence = MonitoringAiEvidence(
        evidence_id=f"evidence-{index}",
        source_entry_id="source-listing",
        source_content_sha256=HASH_A,
        locator=f"listing:test:row:{index}",
        raw_fields={"domain": "AE", "field": "AETERM"},
        input_revision_sha256=job.input_revision_sha256,
    )
    claim = MonitoringAiClaim(
        claim_id=f"claim-{index}",
        kind=MonitoringAiClaimKind.RECOMMENDATION,
        text="跨表线索候选，需要医学经理复核。",
        confidence=0.82,
        uncertainty="尚未获得医学经理最终判断。",
        user_action="请确认或修订候选。",
        evidence_ids=(evidence.evidence_id,),
    )
    return MonitoringAiCandidate(
        candidate_id=f"candidate-{job.job_id}-{index}",
        job_id=job.job_id,
        project_id=job.project_id,
        task_type=job.task_type,
        candidate_type="cross_table_clue",
        title=f"跨表线索候选 {index}",
        structured_payload={"subject_id": "S001"},
        claims=(claim,),
        evidence=(evidence,),
        input_revision_sha256=job.input_revision_sha256,
        prompt_version=job.prompt_version,
        created_at=job.created_at,
    )


def test_persistence_gate_accepts_single_ordinary_clue_candidate(
    tmp_path: Path,
) -> None:
    """持久化门同合同：普通lane单一候选入库合法（修改前在此被拒）。"""
    job = _clue_job(tmp_path, business_key="clue-count-gate")
    validate_candidates_for_job(job, (_clue_candidate(job, 1),))


def test_persistence_gate_rejects_four_ordinary_clue_candidates(
    tmp_path: Path,
) -> None:
    job = _clue_job(tmp_path, business_key="clue-count-gate-overflow")
    with pytest.raises(ValueError, match="requires 1 to 3 candidates"):
        validate_candidates_for_job(
            job,
            tuple(_clue_candidate(job, index) for index in range(1, 5)),
        )


def test_persistence_gate_focused_lane_requires_exactly_one(
    tmp_path: Path,
) -> None:
    """business_key :focus: 标记的定向核实：恰好1个；2个拒收。"""
    job = _clue_job(tmp_path, business_key="aemh:focus:fid-1")
    validate_candidates_for_job(job, (_clue_candidate(job, 1),))
    with pytest.raises(
        ValueError, match="focused verification requires exactly one candidate"
    ):
        validate_candidates_for_job(
            job,
            tuple(_clue_candidate(job, index) for index in range(1, 3)),
        )
