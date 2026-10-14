"""状态机专项S5（02_DESIGN §5.2/§7）：降级入口服务端化。

- 停滞（窗口末次完成>30min且已有候选）→投影inflight_adoption_available=true；
- 未停滞→adopt即便带前端标志仍422 mapping_run_incomplete（判定单源化，
  门禁不放松）；
- 停滞→available→adopt通过（含在途排除同R35契约）。
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_monitoring_mapping_draft_repository import (  # noqa: E402
    _candidate,
    _seed_chunk,
)
from packages.medical_monitoring.admission import (  # noqa: E402
    mapping_pipeline as mp_module,
)
from packages.medical_monitoring.admission.mapping_confirmation import (  # noqa: E402
    AdmissionMappingConfirmationService,
    AdmissionMappingPipelineError,
)
from packages.medical_monitoring.admission.mapping_pipeline import (  # noqa: E402
    RECOGNITION_INFLIGHT_STALL_SECONDS,
    AdmissionMappingPipeline,
)
from services.api.app.monitoring_ai_contracts import (  # noqa: E402
    MonitoringAiJobStatus,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import (  # noqa: E402
    MonitoringAiRepository,
)
from services.api.app.monitoring_mapping_draft_repository import (  # noqa: E402
    MonitoringMappingDraftRepository,
)


class _AgedDateTime(datetime):
    """把「现在」向未来平移，制造窗口末次完成久远的停滞形态。"""

    shift_seconds = 0

    @classmethod
    def now(cls, tz=None):
        return datetime.now(tz) + timedelta(seconds=cls.shift_seconds)


@pytest.fixture()
def repositories(tmp_path: Path):
    path = tmp_path / "monitoring-s5.sqlite3"
    return path, MonitoringAiRepository(path), MonitoringMappingDraftRepository(path)


def _shift_pace_now(monkeypatch: pytest.MonkeyPatch, seconds: int) -> None:
    _AgedDateTime.shift_seconds = seconds
    monkeypatch.setattr(mp_module, "datetime", _AgedDateTime)


def _seed_generating_cohort(repo: MonitoringAiRepository):
    """2完成+1在途：generating且已有候选；完成时刻由测试钟控制。"""

    _seed_chunk(repo, domain="AE", chunk_index=1, chunk_total=2,
                fields=("AETERM",), domain_field_count=2)
    _seed_chunk(repo, domain="CM", chunk_index=1, chunk_total=1,
                fields=("CMTRT",), domain_field_count=1)
    _seed_inflight_chunk(
        repo, domain="AE", chunk_index=2, chunk_total=2,
    )
    inflight = repo.list_jobs(
        "project-alpha",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix="listing-field-mapping:batch-001:",
    )
    queued = [job for job in inflight if job.status == MonitoringAiJobStatus.QUEUED]
    assert len(queued) == 1
    return queued[0]


def _seed_inflight_chunk(
    repo: MonitoringAiRepository, *, domain: str, chunk_index: int, chunk_total: int
):
    """只创建不认领的在途分片（画像身份与_seed_chunk一致）。"""

    from tests.test_monitoring_mapping_draft_repository import (
        INPUT_HASH,
        PROFILE_HASH,
        _revision,
    )
    from services.api.app.monitoring_ai_contracts import MonitoringAiJobCreate

    payload = {
        "schema_version": "monitoring_ai_v1",
        "field_profile": {
            "schema_version": "monitoring_ai_field_profile_v1",
            "scope": "complete_profile_chunk",
            "project_id": "project-alpha",
            "batch_id": "batch-001",
            "batch_revision": 1,
            "expected_domains": ["AE", "CM"],
            "full_profile_sha256": PROFILE_HASH,
            "full_input_sha256": INPUT_HASH,
            "full_field_count": 3,
            "domain": domain,
            "domain_field_count": 1,
            "chunk_index": chunk_index,
            "chunk_total": chunk_total,
            "chunk_size_limit": 1,
            "fields": [
                {
                    "domain": domain,
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
    return repo.create_or_get(
        MonitoringAiJobCreate(
            project_id="project-alpha",
            task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
            input_revision=_revision("project-alpha", suffix="001"),
            input_payload=payload,
            prompt_version="mapping-prompt-v1",
            profile_id="independent-ai-test",
            provider="test-provider",
            requested_model="test-model",
            max_attempts=2,
            business_key=(
                f"listing-field-mapping:batch-001:{domain}:"
                f"{chunk_index:04d}-of-{chunk_total:04d}"
            ),
        )
    )


def _project_payload(ai_repository):
    """与list_candidates同源的_project派生（免ai_service装配）。"""

    pipeline = AdmissionMappingPipeline(
        ai_repository=ai_repository,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )
    jobs = ai_repository.list_jobs(
        "project-alpha",
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix="listing-field-mapping:batch-001:",
    )
    return dict(pipeline._project(jobs, attempt_id="batch-001", cohort="primary"))


def _service(ai_repository, mapping_repository):
    pipeline = SimpleNamespace(
        list_candidates=lambda **_kwargs: _project_payload(ai_repository),
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
    service.primary_runtime_resolver = lambda: SimpleNamespace(
        available=True, provider="test-provider", model="test-model",
    )
    return service


def test_stalled_generating_reports_available_flag(
    repositories, monkeypatch: pytest.MonkeyPatch
) -> None:
    """停滞形态：窗口末次完成>阈值且已有候选→inflight_adoption_available。"""

    _, ai_repository, _ = repositories
    _seed_generating_cohort(ai_repository)
    _shift_pace_now(monkeypatch, RECOGNITION_INFLIGHT_STALL_SECONDS + 600)
    try:
        payload = _project_payload(ai_repository)
    finally:
        _shift_pace_now(monkeypatch, 0)
    assert payload["state"] == "generating"
    assert payload["summary"]["candidate_count"] > 0
    assert payload["inflight_adoption_available"] is True


def test_fresh_generating_has_no_flag_and_adopt_rejected(
    repositories,
) -> None:
    """未停滞：标志false；即便前端传知情标志，adopt仍422（单源化门禁）。"""

    _, ai_repository, mapping_repository = repositories
    _seed_generating_cohort(ai_repository)
    payload = _project_payload(ai_repository)
    assert payload["state"] == "generating"
    assert payload["inflight_adoption_available"] is False
    service = _service(ai_repository, mapping_repository)
    with pytest.raises(
        AdmissionMappingPipelineError, match="mapping_run_incomplete"
    ):
        service.adopt_draft(
            project_id="project-alpha",
            attempt_id="batch-001",
            workspace_dir=None,
            actor="medical-manager",
            reason="识别仍正常推进，不应放行降级采纳",
            allow_inflight_adoption=True,
        )


def test_stalled_inflight_adoption_succeeds(
    repositories, monkeypatch: pytest.MonkeyPatch
) -> None:
    """停滞→available→adopt通过：在途分片按缺口排除（R35契约不变）。"""

    _, ai_repository, mapping_repository = repositories
    _seed_generating_cohort(ai_repository)
    _shift_pace_now(monkeypatch, RECOGNITION_INFLIGHT_STALL_SECONDS + 600)
    try:
        service = _service(ai_repository, mapping_repository)
        payload = service.adopt_draft(
            project_id="project-alpha",
            attempt_id="batch-001",
            workspace_dir=None,
            actor="medical-manager",
            reason="识别停滞，知情采用已识别字段继续",
            allow_inflight_adoption=True,
        )
    finally:
        _shift_pace_now(monkeypatch, 0)
    assert payload["status"] in {"draft", "confirmed"}
    # 在途AE chunk2的字段（AESER）不在草稿，按缺口如实排除。
    fields = {
        (field["domain"], field["source_field"]) for field in payload["fields"]
    }
    assert ("AE", "AESER") not in fields
    assert ("AE", "AETERM") in fields
    assert ("CM", "CMTRT") in fields
