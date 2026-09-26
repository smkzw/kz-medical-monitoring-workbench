"""R27-B4回归：硬错误不重试模型、成功输出只重放确定性步骤、状态GET轻量化。

钉住的行为与理由：
- 证据工具协议坏输出/预算耗尽/回执身份错配是硬错误：循环内已有一次
  受控协议修复，残余直接终态；修改前协议失败retryable=True会重排队，
  把同一失败原样再发给模型（程序造成的无效推理）。
- 模型输出成功后的持久化失败只重放确定性步骤（重parse+重complete），
  绝不重调模型；进程内重放仍失败则终态留痕，已留痕的成功输出在下次
  认领时由 _replay_recorded_completion 完成入库——同样不调模型。
- field-mapping-status GET对同参数作业的重验按 (project, 冻结修订)
  请求内缓存：N个同源分片只重验一次；跨请求不缓存，输入新鲜度检查
  保持逐请求真实。
- 状态GET投影 _latest_job_cohort 的身份解析每作业只读一次payload
  （修改前同一过滤器对每作业重复读最多3次）。
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.app.ai_gateway import AiPromptEnvelope
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiJobStatus,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (
    MonitoringAiRepositoryError,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app.monitoring_ai_router import create_monitoring_ai_router
from services.api.app.monitoring_ai_service import (
    MonitoringAiRuntimeBinding,
    MonitoringAiService,
)
from tests.test_monitoring_ai_service import (
    FakeProvider,
    _field_profile,
    _revision,
    _service,
    _valid_output,
)


# ---------------------------------------------------------------------------
# B4-2：成功输出的持久化失败只重放确定性步骤
# ---------------------------------------------------------------------------


class _FlakyCompleteRepository(MonitoringAiRepository):
    """complete()前N次调用抛合成持久化故障，其余行为不变。"""

    def __init__(self, *args: Any, failures: int = 1, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._failures_left = failures
        self.complete_calls = 0

    def complete(self, job, **kwargs):
        self.complete_calls += 1
        if self._failures_left > 0:
            self._failures_left -= 1
            raise MonitoringAiRepositoryError("synthetic persistence outage")
        return super().complete(job, **kwargs)


def _full_runtime() -> MonitoringAiRuntimeBinding:
    return MonitoringAiRuntimeBinding(
        profile_id="independent-ai-test",
        provider="test-provider",
        model="test-model",
        env={
            "WORKBENCH_AI_PROVIDER": "test-provider",
            "WORKBENCH_AI_TRANSPORT": "openai_compatible",
            "WORKBENCH_AI_BASE_URL": "https://example.invalid/v1",
            "WORKBENCH_AI_API_KEY": "test-key",
            "WORKBENCH_AI_MODEL": "test-model",
            "WORKBENCH_AI_EXPECTED_RESPONSE_MODEL": "test-model",
            "WORKBENCH_AI_DEPLOYMENT_PROFILE": "local_private_clinical",
        },
        available=True,
    )


def _clue_style_mapping_service(tmp_path: Path, *, repository) -> MonitoringAiService:
    service = MonitoringAiService(
        repository,
        runtime_resolver=_full_runtime,
        provider_factory=lambda _env: FakeProvider(
            [lambda envelope: _valid_output(envelope)]
        ),
        current_revision_resolver=lambda job: job.input_revision_sha256,
    )
    return service


def test_completion_persistence_failure_replays_deterministically_in_process(
    tmp_path: Path,
) -> None:
    """complete首次失败→同进程内重放确定性步骤→完成；模型只调一次。"""
    repository = _FlakyCompleteRepository(tmp_path / "replay.sqlite3", failures=1)
    provider = FakeProvider([lambda envelope: _valid_output(envelope)])
    service = MonitoringAiService(
        repository,
        runtime_resolver=_full_runtime,
        provider_factory=lambda _env: provider,
        current_revision_resolver=lambda job: job.input_revision_sha256,
    )
    job = service.submit_listing_field_mapping(
        project_id="project-alpha",
        input_revision=_revision(),
        field_profile=_field_profile(field_count=1),
    )

    result = service.run_next("worker-replay")

    assert result.job is not None
    assert result.job.status == MonitoringAiJobStatus.COMPLETED, (
        result.job.failure_message
    )
    assert repository.complete_calls == 2  # 首次失败 + 确定性重放
    assert len(provider.envelopes) == 1  # 模型未被再次调用
    stored = service.repository.candidates("project-alpha", result.job.job_id)
    assert len(stored) == 1


def test_recorded_success_replays_on_next_claim_without_model_call(
    tmp_path: Path,
) -> None:
    """进程内重放仍失败→终态留痕；修复后重排队，再次认领仅凭留痕的
    成功输出完成入库，全程不再调用模型。"""
    # 两次故障：首次complete失败后，进程内确定性重放也失败→终态留痕
    repository = _FlakyCompleteRepository(tmp_path / "replay-later.sqlite3", failures=2)
    provider = FakeProvider([lambda envelope: _valid_output(envelope)])
    service = MonitoringAiService(
        repository,
        runtime_resolver=_full_runtime,
        provider_factory=lambda _env: provider,
        current_revision_resolver=lambda job: job.input_revision_sha256,
    )
    job = service.submit_listing_field_mapping(
        project_id="project-alpha",
        input_revision=_revision(),
        field_profile=_field_profile(field_count=1),
    )

    failed_run = service.run_next("worker-replay-later")

    assert failed_run.job is not None
    assert failed_run.job.status == MonitoringAiJobStatus.FAILED
    assert failed_run.job.failure_code == "completion_replay_failed"
    assert failed_run.job.retryable is False
    # 成功输出已随attempt留痕
    attempts = repository.attempts(job.project_id, job.job_id)
    recorded = [
        attempt
        for attempt in attempts
        if str(attempt.get("outcome")) in {"success", "success_repaired"}
    ]
    assert recorded and recorded[-1]["response"]["provider_outputs"]

    # 故障恢复后由确定性重放完成，不允许任何新的模型调用
    repository._failures_left = 0

    def forbidden_provider(_env):
        provider_run = FakeProvider([])
        provider_run.run = lambda envelope: (_ for _ in ()).throw(
            AssertionError("replay must not call the provider")
        )
        return provider_run

    service.provider_factory = forbidden_provider
    repository.retry_terminal(
        job.project_id,
        job.job_id,
        current_input_revision_sha256=job.input_revision_sha256,
    )
    replayed = service.run_next("worker-replay-later-2")

    assert replayed.job is not None
    assert replayed.job.status == MonitoringAiJobStatus.COMPLETED, (
        replayed.job.failure_message
    )
    assert len(provider.envelopes) == 1  # 模型调用量停留在首次成功
    stored = service.repository.candidates("project-alpha", job.job_id)
    assert len(stored) == 1


# ---------------------------------------------------------------------------
# B4-3：状态GET轻量化
def test_latest_job_cohort_reads_payload_once_per_job() -> None:
    """投影身份解析每作业只读一次payload（修改前每作业最多3次），
    且选择语义不变：同prompt+同profile+同路由的作业全部保留。"""

    class _CountingRepository:
        def __init__(self) -> None:
            self.payload_reads = 0

        def input_payload(self, project_id: str, job_id: str) -> dict:
            self.payload_reads += 1
            return {
                "field_profile": {
                    # 真实同批分片共享同一full_profile_sha256
                    "full_profile_sha256": "shared-profile-sha",
                }
            }

    from packages.medical_monitoring.admission.mapping_pipeline import (
        _latest_job_cohort,
    )

    repository = _CountingRepository()
    jobs = [
        SimpleNamespace(
            job_id=f"job-{index}",
            project_id="project-alpha",
            prompt_version="monitoring-listing-field-mapping-v19",
            provider="test-provider",
            requested_model="test-model",
            created_at=f"2026-09-27T00:0{index}:00+00:00",
        )
        for index in range(3)
    ]
    selected = _latest_job_cohort(jobs, repository=repository)
    assert {job.job_id for job in selected} == {"job-0", "job-1", "job-2"}
    assert repository.payload_reads == len(jobs)


def test_status_get_revalidates_shared_revision_once(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """同参数作业共享冻结修订：一次GET只做一次重验（修改前逐作业重验，
    每次重验都会重建完整画像/关系证据）。输入新鲜度检查保持逐请求真实。"""
    from dataclasses import replace
    from contextlib import contextmanager

    from tests.test_mm_c3_document_evidence import _packet
    from tests.test_monitoring_ai_api import FakeBatchRepository
    from services.api.app.monitoring_ai_field_profiler import (
        MonitoringFieldProfileSnapshot,
    )
    from services.api.app.monitoring_ai_router import (
        current_monitoring_ai_revision,
    )
    from services.api.app.monitoring_ai_service import PROMPT_VERSION_BY_TASK
    from services.api.app.monitoring_mapping_activation import (
        MonitoringMappingActivationService,
    )
    from services.api.app.monitoring_mapping_draft_repository import (
        MonitoringMappingDraftRepository,
    )

    batch_repository = FakeBatchRepository()
    repository = MonitoringAiRepository(tmp_path / "status.sqlite3")
    provider = FakeProvider([lambda envelope: _valid_output(envelope)])
    packet = replace(_packet(), project_id="project-api")
    service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: MonitoringAiRuntimeBinding(
            profile_id="independent-ai-test",
            provider="test-provider",
            model="test-model",
            env={
                "WORKBENCH_AI_PROVIDER": "test-provider",
                "WORKBENCH_AI_TRANSPORT": "openai_compatible",
                "WORKBENCH_AI_BASE_URL": "https://example.invalid/v1",
                "WORKBENCH_AI_API_KEY": "test-key",
                "WORKBENCH_AI_MODEL": "test-model",
                "WORKBENCH_AI_EXPECTED_RESPONSE_MODEL": "test-model",
                "WORKBENCH_AI_DEPLOYMENT_PROFILE": "local_private_clinical",
            },
            available=True,
        ),
        provider_factory=lambda _env: provider,
    )

    def resolve(job):
        return current_monitoring_ai_revision(
            repository, batch_repository, job,
            document_evidence_resolver=lambda **kwargs: packet,
        )

    monkeypatch.setitem(
        PROMPT_VERSION_BY_TASK,
        MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        "monitoring-listing-field-mapping-v20-tools-v1",
    )
    original_payload = MonitoringFieldProfileSnapshot.to_ai_payload

    def with_documents(snapshot):
        result = original_payload(snapshot)
        result["document_evidence"] = packet.to_dict()
        return result

    monkeypatch.setattr(
        MonitoringFieldProfileSnapshot, "to_ai_payload", with_documents
    )

    @contextmanager
    def toolkit(job, payload):
        yield SimpleNamespace(schemas={}, execute=lambda *_: None)

    service.evidence_tool_factory = toolkit
    service.current_revision_resolver = resolve
    resolver_calls: list[str] = []

    def counting_resolver(job):
        resolver_calls.append(job.job_id)
        return resolve(job)

    app = FastAPI()
    app.include_router(
        create_monitoring_ai_router(
            repository=repository,
            service=service,
            batch_repository=batch_repository,
            current_revision_resolver=counting_resolver,
            require_server_principal=False,
            mapping_repository=MonitoringMappingDraftRepository(repository.path),
            mapping_activation_service=MonitoringMappingActivationService(
                MonitoringMappingDraftRepository(repository.path)
            ),
            worker_wake=lambda: None,
        )
    )
    client = TestClient(app)
    started = client.post(
        "/api/projects/project-api/modules/medical-monitoring/ai/"
        "field-mapping-jobs",
        json={"batch_id": "batch-api", "chunk_size": 1},
    )
    assert started.status_code == 202, started.text
    job_count = started.json()["job_count"]
    assert job_count >= 2  # 同批多分片，共享同一冻结修订

    for _ in range(job_count + 1):
        run = service.run_next("status-worker")
        if run.job is None:
            break
    statuses = {
        str(job.status.value)
        for job in repository.list_jobs("project-api")
    }
    assert statuses == {"completed"}

    status = client.get(
        "/api/projects/project-api/modules/medical-monitoring/ai/"
        "field-mapping-status?batch_id=batch-api"
    )
    assert status.status_code == 200, status.text
    body = status.json()
    assert body["job_count"] == job_count
    # 同一冻结修订只重验一次（修改前每作业各重验一次，每次重建完整画像）
    assert len(resolver_calls) == 1
