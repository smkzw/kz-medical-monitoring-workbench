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
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROVIDER,
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
from tests.medical_monitoring.relationship_profiler_stub import (
    build_relationship_profile as _stub_profiler,
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
        "bounded_full_column_statistics_source_labels_"
        "redacted_row_context_and_relationship_profile_v4"
    )
    assert len(profile["table_bindings"]) == 2
    assert len({item["snapshot_id"] for item in profile["table_bindings"]}) == 2
    assert [item["sheet_index"] for item in profile["table_bindings"]] == [1, 2]
    assert all(
        item["table_binding_id"].startswith("mmtable_")
        for item in profile["table_bindings"]
    )
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
    assert by_name["SYSBP"]["sheet_index"] == 1
    assert by_name["SYSBP"]["field_binding_id"].startswith("mmfield_")
    assert by_name["SYSBP"]["table_binding_id"] == profile[
        "table_bindings"
    ][0]["table_binding_id"]
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
    verifier_service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: _runtime(
            MONITORING_C3_VERIFIER_PROVIDER,
            MONITORING_C3_VERIFIER_MODEL,
        ),
    )
    pipeline = AdmissionMappingPipeline(
        ai_service=service,
        verifier_ai_service=verifier_service,
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        relationship_profiler=_stub_profiler,
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
    assert (
        payload["field_profile"]["mapping_cohort_schema_version"]
        == "mm-c3-dual-mapping-cohort-v1"
    )
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
        relationship_profiler=_stub_profiler,
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
    verifier_service = MonitoringAiService(
        repository,
        runtime_resolver=lambda: _runtime(
            MONITORING_C3_VERIFIER_PROVIDER,
            MONITORING_C3_VERIFIER_MODEL,
        ),
    )
    pipeline = AdmissionMappingPipeline(
        ai_service=service,
        verifier_ai_service=verifier_service,
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        relationship_profiler=_stub_profiler,
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
        review_context={
            "divergences": [{
                "domain": "生命体征",
                "source_field": "SYSBP",
                "result": "diverged",
                "primary": {
                    "recommended_role": "vital_sign_systolic_blood_pressure",
                    "field_kind": "source_collected",
                },
                "verifier": {
                    "recommended_role": "lab_result",
                    "field_kind": "source_collected",
                },
                "violations": [],
            }],
        },
    )

    assert result["state"] == "running"
    assert result["job_count"] == 1
    verifier_result = pipeline.adjudicate_candidates(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        draft_id="draft-generated-1",
        draft_fields=[{
            "domain": "生命体征",
            "source_field": "SYSBP",
            "recommended_role": "vital_sign_systolic_blood_pressure",
            "field_kind": "source_collected",
        }],
        workspace_dir=workspace,
        review_context={
            "divergences": [{
                "domain": "生命体征",
                "source_field": "SYSBP",
                "primary": {
                    "recommended_role": "vital_sign_systolic_blood_pressure",
                    "field_kind": "source_collected",
                },
                "verifier": {
                    "recommended_role": "lab_result",
                    "field_kind": "source_collected",
                },
            }],
        },
        cohort="verifier",
    )
    assert verifier_result["state"] == "running"
    jobs = repository.list_jobs(
        PROJECT_ID,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix=(
            f"listing-field-mapping-adjudication:primary:{attempt_id}:"
        ),
    )
    assert len(jobs) == 1
    payload = repository.input_payload(PROJECT_ID, jobs[0].job_id)
    profile = payload["field_profile"]
    assert [field["field"] for field in profile["fields"]] == ["SYSBP"]
    assert profile["fields"][0]["source_label"] == "收缩压(SYSBP)"
    assert profile["adjudication_contract"]["question_count"] == 1
    assert profile["adjudication_contract"]["schema_version"] == (
        "monitoring_mapping_dual_adjudication_v1"
    )
    options = profile["adjudication_contract"]["candidate_options_review"][0]
    assert len(options["candidate_options"]) == 2
    assert "primary" not in options and "verifier" not in options
    assert profile["adjudication_contract"]["first_pass_mappings"] == []
    assert {
        field["field"]
        for field in profile["read_only_adjudication_context_profiles"]
    } >= {"SUBJID", "VISIT", "VSDAT"}
    assert jobs[0].prompt_version == (
        "monitoring-listing-field-mapping-adjudication-v3"
    )
    verifier_jobs = repository.list_jobs(
        PROJECT_ID,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix=(
            f"listing-field-mapping-adjudication:verifier:{attempt_id}:"
        ),
    )
    assert len(verifier_jobs) == 1
    assert verifier_jobs[0].prompt_version == (
        "monitoring-listing-field-mapping-adjudication-verifier-v1"
    )
    verifier_profile = repository.input_payload(
        PROJECT_ID, verifier_jobs[0].job_id
    )["field_profile"]
    assert (
        verifier_profile["adjudication_contract"]["candidate_options_review"]
        == profile["adjudication_contract"]["candidate_options_review"]
    )
    anonymous_payload = str(verifier_profile["adjudication_contract"])
    assert MONITORING_C3_VERIFIER_PROVIDER not in anonymous_payload
    assert MONITORING_C3_MAPPING_PROVIDER not in anonymous_payload


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
        relationship_profiler=_stub_profiler,
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
        relationship_profiler=_stub_profiler,
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


def _load_rows_by_snapshot(
    workspace: Path,
    record: dict,
) -> dict[str, dict[str, list[dict]]]:
    runtime = workspace / RUNTIME_DIR_NAME
    store = Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME)
    try:
        return {
            str(snapshot_id): store.load_listing_content(str(snapshot_id))
            for snapshot_id in record["technical_details"]["snapshot_ids"]
        }
    finally:
        store.close()


def test_bridge_embeds_relationship_evidence_bound_to_frozen_rows(
    tmp_path: Path,
) -> None:
    attempt_id, workspace = _admit(tmp_path)
    record = _record(workspace, attempt_id)
    rows_by_snapshot = _load_rows_by_snapshot(workspace, record)

    bridged = admission_record_to_harness_input(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        record=record,
        table_rows_by_snapshot=rows_by_snapshot,
        relationship_profiler=_stub_profiler,
    ).field_profile

    fields = {
        (item["domain"], item["field"]) for item in bridged["fields"]
    }
    relationships = bridged["relationships"]
    assert relationships
    for relationship in relationships:
        assert (relationship["domain"], relationship["left_field"]) in fields
        assert (relationship["domain"], relationship["right_field"]) in fields
        assert relationship["total_rows"] == 2
        assert relationship["jointly_non_empty_count"] >= 1
    cross_table = bridged["cross_table_relationships"]
    assert {
        frozenset({
            (entry["left_domain"], entry["left_field"]),
            (entry["right_domain"], entry["right_field"]),
        })
        for entry in cross_table
    } == {frozenset({("生命体征", "SUBJID"), ("实验室检查", "SUBJID")})}
    assert all(entry["match_rate"] == 1.0 for entry in cross_table)
    summary = bridged["relationship_profile"]
    assert summary["same_table_pair_count"] == len(relationships)
    assert summary["cross_table_entry_count"] == len(cross_table)
    assert len(summary["input_binding_sha256"]) == 64
    assert len(summary["evidence_sha256"]) == 64
    # The evidence stays desensitized: only counts, rates and field names.
    assert "S001" not in str(bridged)

    # Deterministic recompute over the same frozen input.
    rebuilt = admission_record_to_harness_input(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        record=record,
        table_rows_by_snapshot=rows_by_snapshot,
        relationship_profiler=_stub_profiler,
    ).field_profile
    assert rebuilt["input_sha256"] == bridged["input_sha256"]
    assert rebuilt["profile_sha256"] == bridged["profile_sha256"]


def test_relationship_evidence_participates_in_frozen_input_revision(
    tmp_path: Path,
) -> None:
    attempt_id, workspace = _admit(tmp_path)
    record = _record(workspace, attempt_id)
    rows_by_snapshot = _load_rows_by_snapshot(workspace, record)

    def _shifted_profiler(**kwargs):
        payload = _stub_profiler(**kwargs)
        # Same contract, different honest evidence: the first column pair is
        # also a stable identity pairing, so the same pair carries a second
        # relationship type with internally consistent counts.
        domain = sorted(kwargs["rows_by_domain"])[0]
        fields = kwargs["table_field_order"][domain]
        payload["same_table"] = [*payload["same_table"], {
            "domain": domain,
            "left_field": fields[0],
            "right_field": fields[1],
            "relationship_type": "site_identity_pair",
            "total_rows": len(kwargs["rows_by_domain"][domain]),
            "jointly_non_empty_count": 2,
            "left_only_count": 0,
            "right_only_count": 0,
            "unique_pair_count": 2,
            "left_values_with_multiple_right": 0,
            "right_values_with_multiple_left": 0,
        }]
        return payload

    base = admission_record_to_harness_input(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        record=record,
        table_rows_by_snapshot=rows_by_snapshot,
        relationship_profiler=_stub_profiler,
    ).field_profile
    shifted = admission_record_to_harness_input(
        project_id=PROJECT_ID,
        attempt_id=attempt_id,
        record=record,
        table_rows_by_snapshot=rows_by_snapshot,
        relationship_profiler=_shifted_profiler,
    ).field_profile

    assert shifted["input_sha256"] != base["input_sha256"]
    assert shifted["profile_sha256"] != base["profile_sha256"]
    assert shifted["input_completeness"] == base["input_completeness"]


def test_pipeline_resolves_default_relationship_profiler(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No injection: the lazily resolved production profiler lights up the bridge."""

    attempt_id, workspace = _admit(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    pipeline = AdmissionMappingPipeline(
        ai_service=MonitoringAiService(repository, runtime_resolver=_runtime),
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
    jobs = repository.list_jobs(
        PROJECT_ID,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING.value,
        business_key_prefix=f"listing-field-mapping:{attempt_id}:",
    )
    assert jobs
    payload = repository.input_payload(PROJECT_ID, jobs[0].job_id)
    profile = payload["field_profile"]
    assert profile["relationship_profile"]["profiler_contract"] == (
        "admission-relationship-profiler-strided-max512-v2"
    )
    assert profile["relationship_profile"]["same_table_pair_count"] >= len(
        profile["relationships"]
    )
    # The revision resolver recomputes through the same default profiler, so
    # the submitted job stays fresh without any caller-side wiring.
    assert current_admission_mapping_revision(
        repository,
        jobs[0],
        workspace_dir=workspace,
    ) == jobs[0].input_revision_sha256

    monkeypatch.setattr(
        pipeline,
        "_resolve_relationship_profiler",
        lambda: None,
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc_info:
        pipeline.generate_candidates(
            project_id=PROJECT_ID,
            attempt_id=attempt_id,
            workspace_dir=workspace,
        )
    assert exc_info.value.code == "mapping_relationship_profiler_unavailable"


def test_pipeline_refuses_relationship_evidence_not_bound_to_frozen_rows(
    tmp_path: Path,
) -> None:
    attempt_id, workspace = _admit(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")

    def _unbound_profiler(**kwargs):
        payload = _stub_profiler(**kwargs)
        payload["input_binding_sha256"] = "0" * 64
        return payload

    pipeline = AdmissionMappingPipeline(
        ai_service=MonitoringAiService(repository, runtime_resolver=_runtime),
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        relationship_profiler=_unbound_profiler,
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc_info:
        pipeline.generate_candidates(
            project_id=PROJECT_ID,
            attempt_id=attempt_id,
            workspace_dir=workspace,
        )
    assert exc_info.value.code == "mapping_bridge_failed"
    assert repository.list_jobs(PROJECT_ID) == ()
