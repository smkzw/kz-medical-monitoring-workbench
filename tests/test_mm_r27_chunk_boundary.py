"""R27-02分片边界：公开配置→真实submit的往返与统一边界。

钉住的行为与理由：
- 角色profile的 listing_mapping_chunk_size（经
  WORKBENCH_AI_LISTING_MAPPING_CHUNK_SIZE 注入运行时）是唯一的分片
  公开配置；它声明的允许范围必须与 MonitoringAiService
  .submit_listing_field_mapping_chunks 的真实提交能力（1..12）一致。
- 20260927统一前：settings API 与 pipeline 校验声明 1..50，13..50 的
  配置能通过三层校验、直到真实submit才以泛化的 mapping_bridge_failed
  失败，操作员无从得知是分片配置越界。
- 统一取向（R27-02"以实现成本定"）：取12为实际能力——放大submit到50
  等于放大每次模型调用的prompt与单包失败成本，复审01明确该代价未实测
  （"不能只改常量或放大prompt"）；长期语义分组迁移属后续切片。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from packages.medical_monitoring.admission import (
    AdmissionMappingPipeline,
    AdmissionMappingPipelineError,
    MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX,
)
from packages.medical_monitoring.admission.mapping_pipeline import (
    MAX_LISTING_MAPPING_CHUNK_SIZE,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROFILE_ID,
    MONITORING_C3_MAPPING_PROVIDER,
)
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiInputRevision,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app.monitoring_ai_service import (
    MonitoringAiRuntimeBinding,
    MonitoringAiService,
)
from tests.test_mm_c3_dual_mapping_cohort import (
    PROJECT_ID,
    _CohortProvider,
    _admit,
    _runtime_env,
)
from tests.medical_monitoring.relationship_profiler_stub import (
    build_relationship_profile as _stub_profiler,
)


def _pipeline_with_chunk_env(
    tmp_path: Path, chunk_size: str,
) -> tuple[AdmissionMappingPipeline, MonitoringAiRepository]:
    """真实组件往返：真实入库、真实服务、真实submit，仅provider为桩。"""
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    env = {
        **_runtime_env(MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL),
        "WORKBENCH_AI_LISTING_MAPPING_CHUNK_SIZE": chunk_size,
    }

    def primary_runtime() -> MonitoringAiRuntimeBinding:
        return MonitoringAiRuntimeBinding(
            profile_id=MONITORING_C3_MAPPING_PROFILE_ID,
            provider=MONITORING_C3_MAPPING_PROVIDER,
            model=MONITORING_C3_MAPPING_MODEL,
            env=env,
            available=True,
        )

    service = MonitoringAiService(
        repository,
        runtime_resolver=primary_runtime,
        provider_factory=lambda _env: _CohortProvider(
            provider_name=MONITORING_C3_MAPPING_PROVIDER,
            model_name=MONITORING_C3_MAPPING_MODEL,
        ),
    )
    pipeline = AdmissionMappingPipeline(
        ai_service=service,
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        relationship_profiler=_stub_profiler,
    )
    return pipeline, repository


def _primary_jobs(repository: MonitoringAiRepository, attempt_id: str):
    return repository.list_jobs(
        PROJECT_ID,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix=(
            f"{MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX}:{attempt_id}:"
        ),
    )


def test_declared_max_matches_real_submit_capability() -> None:
    """声明上限必须等于真实提交能力：pipeline常量与service合同一致。"""
    import inspect

    from services.api.app.monitoring_ai_service import MonitoringAiService

    source = inspect.getsource(
        MonitoringAiService.submit_listing_field_mapping_chunks
    )
    assert MAX_LISTING_MAPPING_CHUNK_SIZE == 12
    assert "must be an integer from 1 to 12" in source


@pytest.mark.parametrize("chunk_size", ["1", "12"])
def test_profile_chunk_size_round_trips_into_real_submit(
    tmp_path: Path, chunk_size: str,
) -> None:
    """公开配置1..12 → 真实submit成功，且分片上限真实到达作业载荷。"""
    attempt_id, workspace = _admit(tmp_path)
    pipeline, repository = _pipeline_with_chunk_env(tmp_path, chunk_size)
    result = pipeline.generate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
    )
    assert result["state"] == "generating"
    jobs = _primary_jobs(repository, attempt_id)
    assert jobs
    for job in jobs:
        profile = repository.input_payload(PROJECT_ID, job.job_id)[
            "field_profile"
        ]
        assert profile["chunk_size_limit"] == int(chunk_size)


@pytest.mark.parametrize("chunk_size", ["13", "50"])
def test_profile_chunk_size_above_submit_capability_fails_closed(
    tmp_path: Path, chunk_size: str,
) -> None:
    """公开配置13..50在配置解析点即拒收（mapping_chunk_size_invalid），
    不再到达真实submit后以泛化 mapping_bridge_failed 失败，且不落任何作业。"""
    attempt_id, workspace = _admit(tmp_path)
    pipeline, repository = _pipeline_with_chunk_env(tmp_path, chunk_size)
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        pipeline.generate_candidates(
            project_id=PROJECT_ID,
            attempt_id=attempt_id,
            workspace_dir=workspace,
        )
    assert "mapping_chunk_size_invalid" in str(exc.value)
    assert not _primary_jobs(repository, attempt_id)


def test_service_submit_still_rejects_out_of_band_chunk_size(tmp_path: Path) -> None:
    """真实submit自身的1..12合同保持（纵深，不只依赖pipeline前置校验）。"""
    from tests.test_monitoring_ai_service import (
        FakeProvider,
        _field_profile,
        _revision,
        _service,
    )

    service = _service(tmp_path, FakeProvider([]))
    with pytest.raises(ValueError, match="must be an integer from 1 to 12"):
        service.submit_listing_field_mapping_chunks(
            project_id="project-alpha",
            input_revision=_revision(),
            field_profile=_field_profile(field_count=2),
            chunk_size=13,
        )
