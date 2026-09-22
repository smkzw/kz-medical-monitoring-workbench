from __future__ import annotations

from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from packages.medical_monitoring.admission import (
    MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS,
    MAPPING_ADJUDICATION_LEGACY_TERMINAL_PROMPT_VERSIONS,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_VERIFIER_PROMPT_VERSION,
)
from packages.medical_monitoring.admission.document_authority import (
    CURRENT_PROMPT_VERSIONS_BY_TASK
    as DOCUMENT_AUTHORITY_CURRENT_PROMPT_VERSIONS_BY_TASK,
    LEGACY_TERMINAL_PROMPT_VERSIONS_BY_TASK
    as DOCUMENT_AUTHORITY_LEGACY_TERMINAL_PROMPT_VERSIONS_BY_TASK,
)
from services.api.app import main as app_main
from services.api.app.monitoring_ai_contracts import (
    MonitoringAiInputRevision,
    MonitoringAiSourceBinding,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_source_packet import MonitoringAiSourcePacket
from services.api.app.monitoring_ai_service import (
    CROSS_TABLE_VERIFIER_PROMPT_VERSION,
    PROMPT_VERSION_BY_TASK,
)
from services.api.app.chapter_translation_pipeline import (
    CompositePipelineUnavailableError,
)
from services.api.app.monitoring_document_candidates import (
    CandidateOcrUnavailableError,
)
from services.api.app.monitoring_protocol_preparation_service import (
    PROTOCOL_RETIREMENT_AUDIT_PROMPT_VERSIONS,
)


def test_startup_retires_old_prompt_contracts_before_waking_worker(
    monkeypatch,
) -> None:
    events: list[tuple[str, str, str, frozenset, frozenset]] = []

    def supersede(
        *,
        task_type,
        current_prompt_version,
        additional_current_prompt_versions=(),
        legacy_terminal_prompt_versions=(),
    ):
        events.append(
            (
                "supersede",
                task_type.value,
                current_prompt_version,
                frozenset(additional_current_prompt_versions),
                frozenset(legacy_terminal_prompt_versions),
            )
        )
        return 0

    monkeypatch.setattr(
        app_main.monitoring_ai_repository,
        "supersede_prompt_versions_except",
        supersede,
    )
    monkeypatch.setattr(
        app_main.monitoring_ai_repository,
        "expire_exhausted_leases",
        lambda: events.append(("expire", "", "", frozenset(), frozenset())),
    )
    monkeypatch.setattr(
        app_main,
        "_wake_monitoring_mapping_workers",
        lambda: events.append(("wake_both", "", "", frozenset(), frozenset())),
    )

    app_main._recover_monitoring_ai_jobs()

    expected = [
        (
            "supersede",
            task_type.value,
            PROMPT_VERSION_BY_TASK[task_type],
            (
                DOCUMENT_AUTHORITY_CURRENT_PROMPT_VERSIONS_BY_TASK.get(
                    task_type.value,
                    frozenset({PROMPT_VERSION_BY_TASK[task_type]}),
                )
                    | (
                        MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS
                        | {MONITORING_C3_VERIFIER_PROMPT_VERSION}
                        if task_type == MonitoringAiTaskType.LISTING_FIELD_MAPPING
                        else {CROSS_TABLE_VERIFIER_PROMPT_VERSION}
                        if task_type
                        == MonitoringAiTaskType.CROSS_TABLE_CLUE_SYNTHESIS
                        else frozenset()
                    )
            )
            - {PROMPT_VERSION_BY_TASK[task_type]},
            PROTOCOL_RETIREMENT_AUDIT_PROMPT_VERSIONS
            if task_type == MonitoringAiTaskType.PROTOCOL_CLAUSE_STRUCTURING
            else MAPPING_ADJUDICATION_LEGACY_TERMINAL_PROMPT_VERSIONS
            if task_type == MonitoringAiTaskType.LISTING_FIELD_MAPPING
            else DOCUMENT_AUTHORITY_LEGACY_TERMINAL_PROMPT_VERSIONS_BY_TASK.get(
                task_type.value,
                frozenset(),
            ),
        )
        for task_type in MonitoringAiTaskType
    ]
    assert events == expected + [
        ("expire", "", "", frozenset(), frozenset()),
        ("wake_both", "", "", frozenset(), frozenset()),
    ]


def test_document_authority_startup_prompt_sets_are_explicit() -> None:
    assert app_main.monitoring_doc_auth_worker is app_main.monitoring_ai_worker
    assert (
        app_main.monitoring_doc_auth_verifier_worker
        is app_main.monitoring_ai_verifier_worker
    )
    assert DOCUMENT_AUTHORITY_CURRENT_PROMPT_VERSIONS_BY_TASK == {
        "document_authority_analysis": frozenset(
            {
                "monitoring-document-authority-primary-v9",
                "monitoring-document-authority-verifier-v9",
            }
        ),
        "document_authority_review": frozenset(
            {
                "monitoring-document-authority-review-primary-v7",
                "monitoring-document-authority-review-verifier-v7",
                "monitoring-document-authority-adjudication-primary-v8",
                "monitoring-document-authority-adjudication-verifier-v8",
                "monitoring-document-authority-critique-primary-v2",
                "monitoring-document-authority-critique-verifier-v2",
            }
        ),
    }
    assert DOCUMENT_AUTHORITY_LEGACY_TERMINAL_PROMPT_VERSIONS_BY_TASK == {
        "document_authority_analysis": frozenset(
            {
                "monitoring-document-authority-primary-v6",
                "monitoring-document-authority-verifier-v6",
                "monitoring-document-authority-primary-v7",
                "monitoring-document-authority-verifier-v7",
                "monitoring-document-authority-primary-v8",
                "monitoring-document-authority-verifier-v8",
            }
        ),
        "document_authority_review": frozenset(
            {
                "monitoring-document-authority-review-primary-v6",
                "monitoring-document-authority-review-verifier-v6",
                "monitoring-document-authority-adjudication-primary-v1",
                "monitoring-document-authority-adjudication-verifier-v1",
                "monitoring-document-authority-adjudication-primary-v2",
                "monitoring-document-authority-adjudication-verifier-v2",
                "monitoring-document-authority-adjudication-primary-v3",
                "monitoring-document-authority-adjudication-verifier-v3",
                "monitoring-document-authority-adjudication-primary-v4",
                "monitoring-document-authority-adjudication-verifier-v4",
                "monitoring-document-authority-adjudication-primary-v5",
                "monitoring-document-authority-adjudication-verifier-v5",
                "monitoring-document-authority-adjudication-primary-v6",
                "monitoring-document-authority-adjudication-verifier-v6",
                "monitoring-document-authority-adjudication-primary-v7",
                "monitoring-document-authority-adjudication-verifier-v7",
                "monitoring-document-authority-critique-primary-v1",
                "monitoring-document-authority-critique-verifier-v1",
            }
        )
    }


def test_monitoring_authority_defers_ocr_role_resolution_into_runner(
    monkeypatch, tmp_path,
) -> None:
    captured = {}

    def start(**kwargs):
        captured.update(kwargs)
        return {"state": "analyzing", "batch_id": "mmbatch_deferred"}

    monkeypatch.setattr(app_main.monitoring_document_authority_workflow, "start", start)
    monkeypatch.setattr(
        app_main.project_source_manifest_service,
        "build_manifest",
        lambda _project_id: SimpleNamespace(
            header_project=SimpleNamespace(
                public_dict=lambda: {
                    "project_id": "project-test",
                    "project_code": "TEST-001",
                    "project_name": "测试研究",
                    "indication": "测试适应症",
                    "product_name": "测试药物",
                    "study_phase": "II期",
                    "protocol_id": "TEST-001",
                    "protocol_version": "V1.0",
                    "protocol_date": "2026-01-01",
                    "status": "active",
                }
            )
        ),
    )
    monkeypatch.setattr(
        app_main,
        "_runtime_role_context",
        lambda _role: (_ for _ in ()).throw(
            CompositePipelineUnavailableError("OCR role unavailable")
        ),
    )

    result = app_main._start_r7_monitoring_document_authority(
        project_id="project-test",
        workspace_dir=tmp_path,
        files=[("scan.pdf", b"pdf")],
    )

    assert result["state"] == "analyzing"
    assert captured["ocr_model"] == "GLM-OCR-bf16"
    assert captured["project_context"]["project_id"] == "project-test"
    with pytest.raises(CandidateOcrUnavailableError):
        captured["ocr_runner"](1, 200, "ignored", b"png")


def test_monitoring_ocr_failure_preserves_requested_runtime_identity(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        app_main,
        "_runtime_role_context",
        lambda _role: (
            SimpleNamespace(model="PaddleOCR-VL-1.6"),
            SimpleNamespace(provider="paddle_official"),
            {},
        ),
    )
    monkeypatch.setattr(
        app_main,
        "_writing_reference_ocr_runner",
        lambda *_args: (_ for _ in ()).throw(
            CompositePipelineUnavailableError("gateway unavailable")
        ),
    )

    with pytest.raises(CandidateOcrUnavailableError) as captured:
        app_main._monitoring_candidate_ocr_runner(1, 200, "fallback", b"png")

    assert captured.value.requested_model == "PaddleOCR-VL-1.6"
    assert captured.value.provider == "paddle_official"


def test_source_job_recovery_preserves_pre_fact_revision_hash(
    monkeypatch,
) -> None:
    current_revision = MonitoringAiInputRevision(
        project_id="project-recovery",
        batch_revision="source-registry:revision-a",
        protocol_version="protocol-revision-a",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-protocol",
                source_content_sha256="a" * 64,
            ),
        ),
    )
    legacy_payload = current_revision.model_dump(
        mode="json",
        exclude={"fact_revision", "source_binding_revision"},
    )
    legacy_hash = sha256(
        json.dumps(
            legacy_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    assert legacy_hash == current_revision.revision_sha256

    job = SimpleNamespace(
        task_type=MonitoringAiTaskType.PROTOCOL_CLAUSE_STRUCTURING,
        project_id="project-recovery",
        job_id="job-recovery",
        input_revision=current_revision,
        input_revision_sha256=legacy_hash,
    )
    monkeypatch.setattr(
        app_main.monitoring_ai_repository,
        "input_payload",
        lambda _project_id, _job_id: {"source_ids": ["span-1"]},
    )
    monkeypatch.setattr(
        app_main.monitoring_ai_source_packet_resolver,
        "resolve",
        lambda _project_id, _source_ids: MonitoringAiSourcePacket(
            input_revision=current_revision,
            source_ids=("span-1",),
            evidence_packet=(),
        ),
    )

    assert app_main._current_monitoring_ai_revision(job) == legacy_hash


def test_nonempty_fact_revision_remains_part_of_revision_hash() -> None:
    base = MonitoringAiInputRevision(
        project_id="project-recovery",
        protocol_version="protocol-revision-a",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-protocol",
                source_content_sha256="a" * 64,
            ),
        ),
    )
    fact_bound = base.model_copy(update={"fact_revision": "fact-1:v2"})

    assert fact_bound.revision_sha256 != base.revision_sha256


def test_nonempty_source_binding_revision_remains_part_of_hash() -> None:
    base = MonitoringAiInputRevision(
        project_id="project-recovery",
        batch_revision="batch-revision-a",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-listing",
                source_content_sha256="b" * 64,
            ),
        ),
    )
    binding_bound = base.model_copy(
        update={"source_binding_revision": "source-binding:revision-a"}
    )

    assert binding_bound.revision_sha256 != base.revision_sha256


def test_main_listing_revision_path_delegates_to_lightweight_helper(
    monkeypatch,
) -> None:
    revision = MonitoringAiInputRevision(
        project_id="project-recovery",
        batch_revision="batch-revision-a",
    )
    job = SimpleNamespace(
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        project_id="project-recovery",
        job_id="job-listing-recovery",
        input_revision=revision,
        input_revision_sha256=revision.revision_sha256,
    )
    calls = []
    monkeypatch.setattr(
        app_main,
        "current_monitoring_ai_revision",
        lambda repository, batch_repository, current_job, **_kwargs: (
            calls.append((repository, batch_repository, current_job))
            or "c" * 64
        ),
    )

    assert app_main._current_monitoring_ai_revision(job) == "c" * 64
    assert calls == [
        (
            app_main.monitoring_ai_repository,
            app_main.monitoring_batch_repository,
            job,
        )
    ]


def test_source_job_recovery_detects_real_revision_change(
    monkeypatch,
) -> None:
    frozen_revision = MonitoringAiInputRevision(
        project_id="project-recovery",
        protocol_version="protocol-revision-a",
        sources=(
            MonitoringAiSourceBinding(
                source_entry_id="source-protocol",
                source_content_sha256="a" * 64,
            ),
        ),
    )
    current_revision = frozen_revision.model_copy(
        update={
            "sources": (
                MonitoringAiSourceBinding(
                    source_entry_id="source-protocol",
                    source_content_sha256="b" * 64,
                ),
            )
        }
    )
    job = SimpleNamespace(
        task_type=MonitoringAiTaskType.PROTOCOL_CLAUSE_STRUCTURING,
        project_id="project-recovery",
        job_id="job-recovery",
        input_revision=frozen_revision,
        input_revision_sha256=frozen_revision.revision_sha256,
    )
    monkeypatch.setattr(
        app_main.monitoring_ai_repository,
        "input_payload",
        lambda _project_id, _job_id: {"source_ids": ["span-1"]},
    )
    monkeypatch.setattr(
        app_main.monitoring_ai_source_packet_resolver,
        "resolve",
        lambda _project_id, _source_ids: MonitoringAiSourcePacket(
            input_revision=current_revision,
            source_ids=("span-1",),
            evidence_packet=(),
        ),
    )

    assert (
        app_main._current_monitoring_ai_revision(job)
        == current_revision.revision_sha256
    )
