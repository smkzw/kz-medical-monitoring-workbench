"""C3 profile-to-existing-harness bridge tests with generated data only."""

from __future__ import annotations

import io
from pathlib import Path
from types import SimpleNamespace

import pytest

from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROFILE_ID,
    MONITORING_C3_MAPPING_PROVIDER,
)
from packages.medical_monitoring.admission import (
    AdmissionMappingPipeline,
    AdmissionMappingPipelineError,
    DataAdmissionPipeline,
    admission_record_to_harness_input,
    current_admission_mapping_revision,
)
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.runtime.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
)
from services.api.app.listing_file_parser import parse_listing_file
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiInputRevision,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_repository import MonitoringAiRepository
from services.api.app.monitoring_ai_service import (
    MonitoringAiRuntimeBinding,
    MonitoringAiService,
)


PROJECT_ID = "c3-mapping-bridge-demo"
ATTEMPT_PREFIX = "stg-"


def _xlsx_bytes() -> bytes:
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    first = workbook.active
    first.title = "生命体征"
    first.append(["SUBJID", "VISIT", "测量日期", "收缩压"])
    first.append(["S001", "筛选期", "2026-01-05", 120])
    first.append(["S002", "筛选期", "2026-01-06", 118])
    second = workbook.create_sheet("实验室检查")
    second.append(["SUBJID", "VISIT", "采集日期", "检查结果"])
    second.append(["S001", "第1天", "2026-01-07", "正常"])
    second.append(["S002", "第1天", "2026-01-08", "异常"])
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _workspace(tmp_path: Path) -> Path:
    return tmp_path / "runtime" / PROJECT_ID


def _admit(tmp_path: Path) -> tuple[str, Path]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "listing.xlsx").write_bytes(_xlsx_bytes())
    workspace = _workspace(tmp_path)
    result = DataAdmissionPipeline(parse_listing_file).create_attempt(
        project_id=PROJECT_ID,
        source_dir=source,
        workspace_dir=workspace,
    )
    return str(result["attempt_id"]), workspace


def _record(workspace: Path, attempt_id: str) -> dict:
    runtime = workspace / RUNTIME_DIR_NAME
    store = Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME)
    try:
        persisted = store.get_domain_object("data_admission", attempt_id)
    finally:
        store.close()
    assert persisted is not None
    return persisted[1]


def _runtime(
    provider: str = MONITORING_C3_MAPPING_PROVIDER, model: str = MONITORING_C3_MAPPING_MODEL
) -> MonitoringAiRuntimeBinding:
    return MonitoringAiRuntimeBinding(
        profile_id=MONITORING_C3_MAPPING_PROFILE_ID,
        provider=provider,
        model=model,
        env={},
        available=True,
    )


def test_bridge_redacts_subject_values_and_binds_every_table(tmp_path: Path) -> None:
    attempt_id, workspace = _admit(tmp_path)
    bridged = admission_record_to_harness_input(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        record=_record(workspace, attempt_id),
    )
    profile = bridged.field_profile
    assert profile["payload_policy"] == (
        "field_statistics_without_row_or_identifier_values_v1"
    )
    assert len(profile["table_bindings"]) == 2
    assert len({item["snapshot_id"] for item in profile["table_bindings"]}) == 2
    subject_fields = [item for item in profile["fields"] if item["field"] == "SUBJID"]
    assert len(subject_fields) == 2
    assert all(item["values_redacted"] is True for item in subject_fields)
    assert all(
        item["representative_values"] == [{"redacted": "identifier"}]
        for item in subject_fields
    )
    assert "S001" not in str(profile)


def test_pipeline_submits_existing_harness_jobs_with_glm_identity(tmp_path: Path) -> None:
    attempt_id, workspace = _admit(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    service = MonitoringAiService(repository, runtime_resolver=_runtime)
    pipeline = AdmissionMappingPipeline(
        ai_service=service,
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )
    result = pipeline.generate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
    )
    assert result["state"] == "generating"
    assert result["confirmation_status"] == "pending_confirmation"
    assert result["summary"]["job_count"] >= 2
    assert result["summary"]["candidate_count"] == 0
    assert result["execution"] == {
        "providers": [MONITORING_C3_MAPPING_PROVIDER],
        "requested_models": [MONITORING_C3_MAPPING_MODEL],
    }
    jobs = repository.list_jobs(
        PROJECT_ID,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix=f"listing-field-mapping:{attempt_id}:",
    )
    assert jobs
    payload = repository.input_payload(PROJECT_ID, jobs[0].job_id)
    assert "S001" not in str(payload)
    assert payload["field_profile"]["full_profile_sha256"]
    assert current_admission_mapping_revision(
        repository,
        jobs[0],
        workspace_dir=workspace,
    ) == jobs[0].input_revision_sha256

    assert current_admission_mapping_revision(
        repository,
        jobs[0],
        workspace_dir=workspace.parent / "missing-workspace",
    ) == ""


def test_pipeline_refuses_non_default_model_without_sending_data(tmp_path: Path) -> None:
    attempt_id, workspace = _admit(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: _runtime("deepseek", "deepseek-v4-flash"),
    )
    pipeline = AdmissionMappingPipeline(
        ai_service=service,
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc_info:
        pipeline.generate_candidates(
            project_id=PROJECT_ID,
            attempt_id=attempt_id,
            workspace_dir=workspace,
        )
    assert exc_info.value.code == "mapping_model_not_configured"
    assert repository.list_jobs(PROJECT_ID) == ()


def test_pipeline_rejects_cross_project_attempt(tmp_path: Path) -> None:
    attempt_id, workspace = _admit(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    pipeline = AdmissionMappingPipeline(
        ai_service=MonitoringAiService(repository, runtime_resolver=_runtime),
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc_info:
        pipeline.generate_candidates(
            project_id="another-project",
            attempt_id=attempt_id,
            workspace_dir=workspace,
        )
    assert exc_info.value.code == "mapping_admission_not_found"


def test_candidate_projection_keeps_bounded_source_profile_evidence() -> None:
    candidate = SimpleNamespace(
        structured_payload={
            "field_mappings": [{
                "domain": "生命体征",
                "source_field": "SUBJID",
                "recommended_role": "subject_id",
                "field_kind": "source_metadata",
                "confidence": 0.7,
                "uncertainty": "需核对受试者标识。",
                "user_action": "请确认该列是否为受试者唯一标识。",
                "evidence_ids": ["e-1"],
            }],
        },
        evidence=(SimpleNamespace(
            evidence_id="e-1",
            raw_fields={
                "inferred_type": "string",
                "total_rows": 2,
                "non_empty_count": 2,
                "representative_values": [{"redacted": "identifier"}],
            },
        ),),
    )
    repository = SimpleNamespace(
        candidates=lambda *_args: (candidate,),
    )
    pipeline = AdmissionMappingPipeline(
        ai_service=SimpleNamespace(),
        ai_repository=repository,
        input_revision_factory=lambda value: value,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )
    job = SimpleNamespace(
        project_id=PROJECT_ID,
        job_id="job-1",
        status="completed",
        provider="zhipu-coding-plan",
        requested_model="glm-5.3-flash",
        response_model="glm-5.3-flash",
        failure_code="",
    )

    projected = pipeline._project((job,), attempt_id="stg-test")

    assert projected["candidates"][0]["evidence_summary"] == [{
        "inferred_type": "string",
        "total_rows": 2,
        "non_empty_count": 2,
        "sample_count": 1,
        "samples_hidden": True,
    }]
