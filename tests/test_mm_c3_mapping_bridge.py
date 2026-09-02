"""C3 profile-to-existing-harness bridge tests with generated data only."""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_ALTERNATE_MODEL,
    MONITORING_C3_ALTERNATE_PROVIDER,
    MONITORING_C3_LOCAL_FALLBACK_MODEL,
    MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROFILE_ID,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_REMOTE_UNAVAILABLE_ENV,
    monitoring_mapping_runtime_matches,
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
    first.append([
        "受试者编号(SUBJID)",
        "访视(VISIT)",
        "测量日期(VSDAT)",
        "收缩压(SYSBP)",
    ])
    first.append(["S001", "筛选期", "2026-01-05", 120])
    first.append(["S002", "筛选期", "2026-01-06", 118])
    second = workbook.create_sheet("实验室检查")
    second.append([
        "受试者编号(SUBJID)",
        "访视(VISIT)",
        "采集日期(LBDAT)",
        "检查结果(LBORRES)",
    ])
    second.append(["S001", "第1天", "2026-01-07", "正常"])
    second.append(["S002", "第1天", "2026-01-08", "异常"])
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _empty_table_xlsx_bytes() -> bytes:
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "未采集检查"
    sheet.append(["受试者编号(SUBJID)", "检查结果(LBORRES)"])
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
    provider: str = MONITORING_C3_MAPPING_PROVIDER,
    model: str = MONITORING_C3_MAPPING_MODEL,
    *,
    env: dict[str, str] | None = None,
) -> MonitoringAiRuntimeBinding:
    return MonitoringAiRuntimeBinding(
        profile_id=MONITORING_C3_MAPPING_PROFILE_ID,
        provider=provider,
        model=model,
        env=env or {},
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
        "bounded_full_column_statistics_source_labels_and_redacted_row_context_v3"
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


def test_bridge_exposes_value_distribution_and_table_structure(
    tmp_path: Path,
) -> None:
    attempt_id, workspace = _admit(tmp_path)
    bridged = admission_record_to_harness_input(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        record=_record(workspace, attempt_id),
    )
    profile = bridged.field_profile
    vital_fields = [
        item for item in profile["fields"] if item["domain"] == "生命体征"
    ]
    assert [item["field"] for item in vital_fields] == [
        "SUBJID",
        "VISIT",
        "VSDAT",
        "SYSBP",
    ]
    by_name = {item["field"]: item for item in vital_fields}
    assert by_name["SUBJID"]["column_index"] == 0
    assert by_name["SYSBP"]["column_index"] == 3
    assert by_name["SYSBP"]["source_label"] == "收缩压(SYSBP)"
    assert by_name["SYSBP"]["inferred_type"] == "decimal"
    assert by_name["SYSBP"]["representative_values"] == ["118", "120"]
    assert by_name["SYSBP"]["representative_sample_count"] == 2
    assert by_name["SYSBP"]["unique_value_count"] == 2
    assert by_name["SYSBP"]["top_values"] == [
        {"value": "118", "count": 1},
        {"value": "120", "count": 1},
    ]
    date_field = by_name["VSDAT"]
    assert date_field["inferred_type"] == "date"
    assert date_field["date_range"] == {
        "min": "2026-01-05",
        "max": "2026-01-06",
        "parsed_count": 2,
    }
    assert profile["table_field_order"] == [
        {
            "domain": "生命体征",
            "field_order": ["SUBJID", "VISIT", "VSDAT", "SYSBP"],
        },
        {
            "domain": "实验室检查",
            "field_order": ["SUBJID", "VISIT", "LBDAT", "LBORRES"],
        },
    ]


def test_bridge_keeps_header_only_table_as_evidence_without_guessing(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "empty-table.xlsx").write_bytes(_empty_table_xlsx_bytes())
    workspace = _workspace(tmp_path)
    result = DataAdmissionPipeline(parse_listing_file).create_attempt(
        project_id=PROJECT_ID,
        source_dir=source,
        workspace_dir=workspace,
    )

    bridged = admission_record_to_harness_input(
        project_id=PROJECT_ID,
        attempt_id=str(result["attempt_id"]),
        record=_record(workspace, str(result["attempt_id"])),
    )

    assert len(bridged.field_profile["table_bindings"]) == 1
    assert all(
        field["total_rows"] == 0
        and field["non_empty_count"] == 0
        and field["null_rate"] == 1.0
        and field["representative_values"] == []
        for field in bridged.field_profile["fields"]
    )


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
    fields = payload["field_profile"]["fields"]
    assert any(field["same_row_examples"] for field in fields)
    assert any(field["top_values"] for field in fields)
    assert {"redacted": "identifier"} in [
        value["value"]
        for field in fields
        for example in field["same_row_examples"]
        for value in example["nearby_values"]
        if value["field"] == "SUBJID"
    ]
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


def test_pipeline_second_pass_submits_only_questions_with_full_table_context(
    tmp_path: Path,
) -> None:
    attempt_id, workspace = _admit(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    service = MonitoringAiService(repository, runtime_resolver=_runtime)
    pipeline = AdmissionMappingPipeline(
        ai_service=service,
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )

    result = pipeline.adjudicate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        draft_id="draft-generated-1",
        draft_fields=[{
            "domain": "生命体征",
            "source_field": "SYSBP",
            "recommended_role": "vital_sign_systolic_blood_pressure",
            "field_kind": "source_collected",
            "uncertainty": "需结合同表字段复核。",
            "user_action": "该列是否为收缩压？",
            "user_decision_required": True,
        }],
        workspace_dir=workspace,
    )

    assert result["state"] == "running"
    assert result["job_count"] == 1
    jobs = repository.list_jobs(
        PROJECT_ID,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix=(
            f"listing-field-mapping-adjudication:{attempt_id}:"
        ),
    )
    assert len(jobs) == 1
    payload = repository.input_payload(PROJECT_ID, jobs[0].job_id)
    profile = payload["field_profile"]
    assert [field["field"] for field in profile["fields"]] == ["SYSBP"]
    assert profile["fields"][0]["source_label"] == "收缩压(SYSBP)"
    assert profile["adjudication_contract"]["question_count"] == 1
    assert {
        field["field"]
        for field in profile["read_only_adjudication_context_profiles"]
    } >= {"SUBJID", "VISIT", "VSDAT"}
    assert jobs[0].prompt_version == (
        "monitoring-listing-field-mapping-adjudication-v2"
    )


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


def test_pipeline_accepts_direct_cms_router_minimax_alternate(tmp_path: Path) -> None:
    attempt_id, workspace = _admit(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: _runtime(
            MONITORING_C3_ALTERNATE_PROVIDER,
            MONITORING_C3_ALTERNATE_MODEL,
        ),
    )
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

    assert result["execution"] == {
        "providers": [MONITORING_C3_ALTERNATE_PROVIDER],
        "requested_models": [MONITORING_C3_ALTERNATE_MODEL],
    }


def test_local_mtplx_fallback_requires_both_remote_routes_unavailable() -> None:
    local = _runtime(
        MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
        MONITORING_C3_LOCAL_FALLBACK_MODEL,
    )
    assert monitoring_mapping_runtime_matches(local) is False

    admitted = _runtime(
        MONITORING_C3_LOCAL_FALLBACK_PROVIDER,
        MONITORING_C3_LOCAL_FALLBACK_MODEL,
        env={MONITORING_C3_REMOTE_UNAVAILABLE_ENV: "true"},
    )
    assert monitoring_mapping_runtime_matches(admitted) is True


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


def test_list_candidates_ignores_superseded_submission_cohorts(tmp_path: Path) -> None:
    attempt_id, workspace = _admit(tmp_path)
    now = datetime.now(timezone.utc)

    def job(
        job_id: str,
        *,
        prompt: str,
        status: str,
        created_at: datetime,
        profile_id: str = "profile-current",
        provider: str = "zhipu-coding-plan",
        requested_model: str = "glm-5.3-flash",
    ):
        return SimpleNamespace(
            project_id=PROJECT_ID,
            job_id=job_id,
            status=status,
            provider=provider,
            requested_model=requested_model,
            response_model="glm-5.3-flash" if status == "completed" else "",
            failure_code="stale_input_revision" if status == "stale_input" else "",
            prompt_version=prompt,
            input_revision_sha256="revision-current" if prompt == "v18" else "revision-old",
            profile_id=profile_id if prompt == "v18" else "profile-old",
            created_at=created_at,
        )

    old = job("job-old", prompt="v17", status="stale_input", created_at=now)
    current = job(
        "job-current",
        prompt="v18",
        status="completed",
        created_at=now + timedelta(seconds=1),
    )
    deterministic = job(
        "job-deterministic",
        prompt="v18",
        status="completed",
        created_at=now + timedelta(milliseconds=500),
        profile_id="monitoring-deterministic-metadata",
        provider="workbench-system",
        requested_model="deterministic-metadata-mapping-v1",
    )
    candidate = SimpleNamespace(
        structured_payload={"field_mappings": []},
        evidence=(),
    )
    repository = SimpleNamespace(
        list_jobs=lambda *_args, **_kwargs: (old, deterministic, current),
        candidates=lambda *_args: (candidate,),
    )
    pipeline = AdmissionMappingPipeline(
        ai_service=SimpleNamespace(),
        ai_repository=repository,
        input_revision_factory=lambda value: value,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
    )

    result = pipeline.list_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        workspace_dir=workspace,
    )

    assert result["state"] == "candidates_ready"
    assert result["summary"]["job_count"] == 2
