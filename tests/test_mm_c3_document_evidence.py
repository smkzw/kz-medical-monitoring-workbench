from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import docx

from packages.medical_monitoring.admission.document_evidence import (
    DOCUMENT_ROLES,
    CurrentDocumentBinding,
    DocumentEvidenceError,
    DocumentRoleEvidence,
    MonitoringDocumentEvidencePacket,
    validate_document_evidence_packet,
)
from packages.medical_monitoring.admission import (
    AdmissionMappingPipeline,
    DataAdmissionPipeline,
    MappingBridgeError,
    admission_record_to_harness_input,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROFILE_ID,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROVIDER,
)
from packages.medical_monitoring.admission.mapping_pipeline import (
    AdmissionMappingPipelineError,
)
from packages.medical_monitoring.graph.store import Store
from packages.medical_monitoring.runtime.runtime_progress import (
    ARTIFACT_DIR_NAME,
    RUNTIME_DB_NAME,
    RUNTIME_DIR_NAME,
)
from services.api.app.listing_file_parser import parse_listing_file
from services.api.app.monitoring_document_evidence import (
    MonitoringDocumentEvidenceResolver,
)
from services.api.app.source_intake import (
    SourceRegistryService,
    SourceRegistryStore,
)
from services.api.app.source_content_validation import (
    SourceContentValidationService,
    SourceContentValidationStore,
    SourceExpectedContext,
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
from tests.medical_monitoring.relationship_profiler_stub import (
    build_relationship_profile,
)


PROJECT_ID = "document-evidence-demo"


def _binding(role: str, token: str) -> CurrentDocumentBinding:
    return CurrentDocumentBinding(
        role=role,
        source_entry_id=f"source-{token}",
        source_revision=f"revision-{token}",
        content_sha256=token * 64,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            if role == "ecrf"
            else "application/pdf"
        ),
        parser_name="document-parser",
        parser_version="v1",
        validation_id=f"validation-{token}",
        validation_revision=1,
        validator_version="source-content-consistency-v2",
        validation_context_sha256="8" * 64,
        locator_index_sha256=("f" if token != "f" else "e") * 64,
        locator_count=2,
        locator_samples=(f"{role}:page:1", f"{role}:page:2"),
        selection_basis="registry_current",
    )


def _packet(
    *,
    ecrf_status: str = "current",
) -> MonitoringDocumentEvidencePacket:
    records = []
    for role, token in zip(DOCUMENT_ROLES, "abcd"):
        if role in {"investigator_brochure", "sap"}:
            records.append(
                DocumentRoleEvidence(
                    role=role,
                    status="missing",
                    limitation_codes=(f"{role}_not_registered",),
                )
            )
        elif role == "ecrf" and ecrf_status != "current":
            records.append(
                DocumentRoleEvidence(
                    role=role,
                    status=ecrf_status,
                    limitation_codes=("ecrf_not_current",),
                )
            )
        else:
            records.append(
                DocumentRoleEvidence(
                    role=role,
                    status="current",
                    binding=_binding(role, token),
                )
            )
    return MonitoringDocumentEvidencePacket(
        project_id=PROJECT_ID,
        listing_admission_date="2026-09-03",
        registry_revision_sha256="9" * 64,
        roles=tuple(records),
    )


def test_packet_accounts_for_all_roles_without_forcing_optional_user_work() -> None:
    packet = _packet()
    payload = packet.to_dict()

    assert packet.mapping_context_ready is True
    assert [item["role"] for item in payload["roles"]] == list(DOCUMENT_ROLES)
    assert payload["roles"][1]["status"] == "missing"
    assert payload["roles"][3]["status"] == "missing"
    assert "no_ctcae_grade_risk_query_or_clinical_join" in (
        payload["clinical_boundary"]
    )
    assert MonitoringDocumentEvidencePacket.from_dict(payload).to_dict() == payload


def test_protocol_and_ecrf_are_required_for_mapping_context() -> None:
    packet = _packet(ecrf_status="incomplete")

    assert packet.mapping_context_ready is False
    with pytest.raises(
        DocumentEvidenceError,
        match="mapping_document_evidence_incomplete",
    ):
        validate_document_evidence_packet(
            packet.to_dict(),
            project_id=PROJECT_ID,
            require_mapping_context=True,
        )


def test_project_and_packet_digest_are_fail_closed() -> None:
    payload = _packet().to_dict()
    with pytest.raises(
        DocumentEvidenceError,
        match="document_packet_project_mismatch",
    ):
        validate_document_evidence_packet(
            payload,
            project_id="another-project",
            require_mapping_context=True,
        )

    tampered = deepcopy(payload)
    tampered["roles"][0]["binding"]["locator_samples"].append(
        "protocol:page:3"
    )
    tampered["roles"][0]["binding"]["locator_count"] = 3
    with pytest.raises(
        DocumentEvidenceError,
        match="document_packet_sha256_mismatch",
    ):
        MonitoringDocumentEvidencePacket.from_dict(tampered)


def test_registry_current_protocol_cannot_claim_event_applicability() -> None:
    with pytest.raises(
        DocumentEvidenceError,
        match="clinical_applicability_unproven",
    ):
        CurrentDocumentBinding(
            **{
                **_binding("protocol", "a").__dict__,
                "clinical_applicability_resolved": True,
            }
        )


def test_current_binding_requires_complete_unique_locators() -> None:
    with pytest.raises(
        DocumentEvidenceError,
        match="document_locators_duplicated",
    ):
        CurrentDocumentBinding(
            **{
                **_binding("ecrf", "c").__dict__,
                "locator_samples": (
                    "ecrf:sheet:1",
                    "ecrf:sheet:1",
                ),
            }
        )


def test_non_current_role_cannot_smuggle_source_identity() -> None:
    with pytest.raises(
        DocumentEvidenceError,
        match="limited_document_role_invalid",
    ):
        DocumentRoleEvidence(
            role="sap",
            status="missing",
            binding=_binding("sap", "d"),
            limitation_codes=("sap_not_registered",),
        )


def _admission_record(tmp_path: Path) -> tuple[dict, Path]:
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "不良事件"
    sheet.append(["受试者编号(SUBJID)", "事件名称(AETERM)"])
    sheet.append(["S001", "头痛"])
    stream = io.BytesIO()
    workbook.save(stream)
    source = tmp_path / "source"
    source.mkdir()
    (source / "listing.xlsx").write_bytes(stream.getvalue())
    workspace = tmp_path / "workspace"
    result = DataAdmissionPipeline(parse_listing_file).create_attempt(
        project_id=PROJECT_ID,
        source_dir=source,
        workspace_dir=workspace,
    )
    runtime = workspace / RUNTIME_DIR_NAME
    store = Store(runtime / RUNTIME_DB_NAME, runtime / ARTIFACT_DIR_NAME)
    try:
        persisted = store.get_domain_object(
            "data_admission", result["attempt_id"]
        )
    finally:
        store.close()
    assert persisted is not None
    return persisted[1], workspace


def test_mapping_bridge_requires_bound_current_documents_when_enabled(
    tmp_path: Path,
) -> None:
    record, _ = _admission_record(tmp_path)
    with pytest.raises(
        MappingBridgeError,
        match="mapping_document_evidence_missing",
    ):
        admission_record_to_harness_input(
            project_id=PROJECT_ID,
            attempt_id=record["attempt_id"],
            record=record,
            require_document_evidence=True,
        )

    bound = deepcopy(record)
    bound["technical_details"]["monitoring_document_evidence"] = (
        _packet().to_dict()
    )
    bridged = admission_record_to_harness_input(
        project_id=PROJECT_ID,
        attempt_id=record["attempt_id"],
        record=bound,
        require_document_evidence=True,
    )
    assert bridged.field_profile["document_evidence"]["packet_sha256"] == (
        _packet().packet_sha256
    )
    assert bridged.field_profile["bridge_schema_version"].endswith("-v8")


def test_missing_required_document_creates_no_mapping_job(
    tmp_path: Path,
) -> None:
    record, workspace = _admission_record(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "missing-doc-ai.sqlite3")

    def runtime(provider: str, model: str, profile_id: str):
        return MonitoringAiRuntimeBinding(
            profile_id=profile_id,
            provider=provider,
            model=model,
            env={},
            available=True,
        )

    pipeline = AdmissionMappingPipeline(
        ai_service=MonitoringAiService(
            repository,
            runtime_resolver=lambda: runtime(
                MONITORING_C3_MAPPING_PROVIDER,
                MONITORING_C3_MAPPING_MODEL,
                MONITORING_C3_MAPPING_PROFILE_ID,
            ),
        ),
        verifier_ai_service=MonitoringAiService(
            repository,
            runtime_resolver=lambda: runtime(
                MONITORING_C3_VERIFIER_PROVIDER,
                MONITORING_C3_VERIFIER_MODEL,
                "independent_ai__zhipu_coding_plan_glm_flash",
            ),
        ),
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        relationship_profiler=build_relationship_profile,
        require_document_evidence=True,
        document_evidence_resolver=lambda **_kwargs: _packet(
            ecrf_status="missing"
        ),
    )

    with pytest.raises(
        AdmissionMappingPipelineError,
        match="mapping_document_evidence_incomplete",
    ):
        pipeline.generate_dual_candidates(
            project_id=PROJECT_ID,
            attempt_id=record["attempt_id"],
            workspace_dir=workspace,
        )
    assert repository.list_jobs(PROJECT_ID) == ()


def test_mapping_pipeline_freezes_resolved_documents_at_attempt_date(
    tmp_path: Path,
) -> None:
    record, workspace = _admission_record(tmp_path)
    calls = []

    def resolve_documents(
        *,
        project_id: str,
        listing_admission_date: str,
        selected_entry_ids: dict[str, str],
    ):
        assert selected_entry_ids == {}
        calls.append((project_id, listing_admission_date))
        return _packet()

    bridged = AdmissionMappingPipeline(
        require_document_evidence=True,
        document_evidence_resolver=resolve_documents,
    )._frozen_harness_input(
        project_id=PROJECT_ID,
        attempt_id=record["attempt_id"],
        record=record,
        workspace_dir=workspace,
    )

    assert calls == [(PROJECT_ID, calls[0][1])]
    assert len(calls[0][1]) == 10
    assert bridged.field_profile["document_evidence"]["packet_sha256"] == (
        _packet().packet_sha256
    )


def test_dual_submission_resolves_one_shared_document_snapshot(
    tmp_path: Path,
) -> None:
    record, workspace = _admission_record(tmp_path)
    repository = MonitoringAiRepository(tmp_path / "monitoring-ai.sqlite3")
    calls = []
    wakes = []

    def resolve_documents(**kwargs):
        calls.append(kwargs)
        return _packet()

    def runtime(provider: str, model: str, profile_id: str):
        return MonitoringAiRuntimeBinding(
            profile_id=profile_id,
            provider=provider,
            model=model,
            env={},
            available=True,
        )

    pipeline = AdmissionMappingPipeline(
        ai_service=MonitoringAiService(
            repository,
            runtime_resolver=lambda: runtime(
                MONITORING_C3_MAPPING_PROVIDER,
                MONITORING_C3_MAPPING_MODEL,
                MONITORING_C3_MAPPING_PROFILE_ID,
            ),
        ),
        verifier_ai_service=MonitoringAiService(
            repository,
            runtime_resolver=lambda: runtime(
                MONITORING_C3_VERIFIER_PROVIDER,
                MONITORING_C3_VERIFIER_MODEL,
                "independent_ai__zhipu_coding_plan_glm_flash",
            ),
        ),
        ai_repository=repository,
        input_revision_factory=MonitoringAiInputRevision.model_validate,
        task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
        relationship_profiler=build_relationship_profile,
        require_document_evidence=True,
        document_evidence_resolver=resolve_documents,
        worker_wake=lambda: wakes.append(True),
    )

    result = pipeline.generate_dual_candidates(
        project_id=PROJECT_ID,
        attempt_id=record["attempt_id"],
        workspace_dir=workspace,
    )
    jobs = repository.list_jobs(PROJECT_ID)
    profiles = [
        repository.input_payload(PROJECT_ID, job.job_id)["field_profile"]
        for job in jobs
    ]

    assert result["verification"]["state"] == "generating"
    assert len(calls) == 1
    assert wakes == [True]
    assert len({
        profile["document_evidence"]["packet_sha256"]
        for profile in profiles
    }) == 1
    assert len({profile["full_input_sha256"] for profile in profiles}) == 1
    assert pipeline._document_selection_ids(
        workspace,
        record["attempt_id"],
    ) == {
        "protocol": "source-a",
        "ecrf": "source-c",
    }


def test_document_selection_is_validated_before_it_is_versioned(
    tmp_path: Path,
) -> None:
    record, workspace = _admission_record(tmp_path)

    def resolve_documents(**kwargs):
        selected = kwargs["selected_entry_ids"].get("ecrf", "")
        if selected == "source-c":
            return _packet()
        roles = list(_packet().roles)
        roles[2] = DocumentRoleEvidence(
            role="ecrf",
            status="incomplete",
            limitation_codes=("ecrf_selection_stale",),
        )
        return MonitoringDocumentEvidencePacket(
            project_id=PROJECT_ID,
            listing_admission_date="2026-09-03",
            registry_revision_sha256="9" * 64,
            roles=tuple(roles),
        )

    pipeline = AdmissionMappingPipeline(
        require_document_evidence=True,
        document_evidence_resolver=resolve_documents,
    )
    with pytest.raises(
        AdmissionMappingPipelineError,
        match="mapping_document_selection_not_found_or_role_mismatch",
    ):
        pipeline.select_document(
            project_id=PROJECT_ID,
            attempt_id=record["attempt_id"],
            workspace_dir=workspace,
            role="ecrf",
            source_entry_id="source-wrong-role",
        )
    assert pipeline._document_selection_ids(workspace, record["attempt_id"]) == {}

    saved = pipeline.select_document(
        project_id=PROJECT_ID,
        attempt_id=record["attempt_id"],
        workspace_dir=workspace,
        role="ecrf",
        source_entry_id="source-c",
    )
    assert saved["version"] == 1
    assert pipeline._document_selection_ids(
        workspace,
        record["attempt_id"],
    ) == {
        "ecrf": "source-c"
    }


def test_document_selection_is_isolated_between_admission_attempts(
    tmp_path: Path,
) -> None:
    first, workspace = _admission_record(tmp_path)
    second = DataAdmissionPipeline(parse_listing_file).create_attempt(
        project_id=PROJECT_ID,
        source_dir=tmp_path / "source",
        workspace_dir=workspace,
    )

    def resolve_documents(**kwargs):
        selected = kwargs["selected_entry_ids"].get("ecrf", "")
        token = {"source-c": "c", "source-d": "d"}.get(selected, "c")
        roles = list(_packet().roles)
        roles[2] = DocumentRoleEvidence(
            role="ecrf",
            status="current",
            binding=_binding("ecrf", token),
        )
        return MonitoringDocumentEvidencePacket(
            project_id=PROJECT_ID,
            listing_admission_date="2026-09-03",
            registry_revision_sha256="9" * 64,
            roles=tuple(roles),
        )

    pipeline = AdmissionMappingPipeline(
        require_document_evidence=True,
        document_evidence_resolver=resolve_documents,
    )
    pipeline.select_document(
        project_id=PROJECT_ID,
        attempt_id=first["attempt_id"],
        workspace_dir=workspace,
        role="ecrf",
        source_entry_id="source-c",
    )
    pipeline.select_document(
        project_id=PROJECT_ID,
        attempt_id=second["attempt_id"],
        workspace_dir=workspace,
        role="ecrf",
        source_entry_id="source-d",
    )

    assert pipeline._document_selection_ids(
        workspace,
        first["attempt_id"],
    ) == {"ecrf": "source-c"}
    assert pipeline._document_selection_ids(
        workspace,
        second["attempt_id"],
    ) == {"ecrf": "source-d"}


def test_document_readiness_is_plain_chinese_and_hides_registry_identity(
    tmp_path: Path,
) -> None:
    record, workspace = _admission_record(tmp_path)
    pipeline = AdmissionMappingPipeline(
        require_document_evidence=True,
        document_evidence_resolver=lambda **_kwargs: _packet(),
    )

    readiness = pipeline.document_readiness(
        project_id=PROJECT_ID,
        attempt_id=record["attempt_id"],
        workspace_dir=workspace,
    )
    blob = json.dumps(readiness, ensure_ascii=False)

    assert readiness["ready"] is True
    assert "无需逐项确认" in readiness["guidance"]
    assert [item["label"] for item in readiness["roles"]] == [
        "研究方案",
        "研究者手册",
        "电子病例报告表",
        "统计分析计划",
    ]
    assert "source_entry_id" not in blob
    assert "packet_sha256" not in blob


class _Registry:
    def __init__(self, entries: list, spans: list) -> None:
        self._entries = entries
        self._spans = spans

    def list_entries(self, project_id: str) -> list:
        return [
            item for item in self._entries if item.project_id == project_id
        ]

    def list_spans(self, project_id: str) -> list:
        return [
            item for item in self._spans if item.project_id == project_id
        ]

    def current_content_validation(
        self, project_id: str, source_entry_id: str
    ):
        return SimpleNamespace(
            validation_id=f"validation-{source_entry_id}",
            revision=1,
            expected_context_hash="8" * 64,
            use_status="allowed",
            technical_status="ready",
            validator_version="source_content_consistency_v2",
            source_entry_id=source_entry_id,
            project_id=project_id,
            module="medical_monitoring",
            file_sha256=next(
                item.content_hash
                for item in self._entries
                if item.entry_id == source_entry_id
            ),
        )

    def assert_operational_sources_usable(
        self, project_id: str, source_ids: list[str]
    ) -> None:
        assert project_id == PROJECT_ID
        assert source_ids
        target = next(
            item
            for item in self._entries
            if source_ids[0].startswith(item.entry_id + "-span-")
        )
        latest = max(
            (
                item
                for item in self._entries
                if item.project_id == project_id
                and item.module == "medical_monitoring"
                and item.source_kind == target.source_kind
            ),
            key=lambda item: item.created_at,
        )
        if latest.entry_id != target.entry_id:
            raise ValueError("superseded")


def _entry(
    role: str,
    order: int,
    *,
    module: str = "medical_monitoring",
    authority_status: str = "current_effective",
):
    source_kind = {
        "protocol": "protocol_docx",
        "investigator_brochure": "investigator_brochure",
        "ecrf": "ecrf_xlsx",
        "sap": "statistical_analysis_plan",
    }[role]
    suffix = ".docx" if role == "protocol" else (
        ".xlsx" if role == "ecrf" else ".pdf"
    )
    entry_id = f"source-{role}-{order}"
    locator_manifest = [
        {
            "source_id": f"{entry_id}-span-{index}",
            "locator": f"document:page:{index}",
        }
        for index in (1, 2)
    ]
    return SimpleNamespace(
        entry_id=entry_id,
        project_id=PROJECT_ID,
        module=module,
        source_kind=source_kind,
        public_title=f"{role}{suffix}",
        content_hash=str(order) * 64,
        parser_status="parsed",
        parser_version="parser-v1",
        span_count=2,
        metadata={
            "filename": f"{role}{suffix}",
            "monitoring_authority_status": authority_status,
            "document_revision": f"{role}-revision-{order}",
            "expected_locator_count": 2,
            "expected_locator_index_sha256": hashlib.sha256(
                json.dumps(
                    locator_manifest,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
            "locator_manifest_complete": True,
        },
        created_at=datetime(
            2026, 9, order, tzinfo=timezone.utc
        ),
    )


def _span(entry, index: int):
    return SimpleNamespace(
        source_id=f"{entry.entry_id}-span-{index}",
        entry_id=entry.entry_id,
        project_id=entry.project_id,
        module=entry.module,
        locator=f"document:page:{index}",
        text_preview=f"bounded extract {index}",
    )


def test_registry_resolver_uses_only_monitoring_owned_current_sources() -> None:
    current = [
        _entry("protocol", 2),
        _entry("ecrf", 3),
        _entry("investigator_brochure", 4),
        _entry("sap", 5),
    ]
    old_protocol = _entry(
        "protocol",
        1,
        authority_status="superseded",
    )
    writing_ib = _entry(
        "investigator_brochure",
        6,
        module="medical_writing",
    )
    entries = [old_protocol, *current, writing_ib]
    spans = [
        _span(entry, index)
        for entry in entries
        for index in (1, 2)
    ]
    packet = MonitoringDocumentEvidenceResolver(
        _Registry(entries, spans)
    ).resolve(
        project_id=PROJECT_ID,
        listing_admission_date="2026-09-03",
    )
    by_role = {item.role: item for item in packet.roles}

    assert packet.mapping_context_ready is True
    assert by_role["protocol"].binding is not None
    assert by_role["protocol"].binding.source_entry_id == (
        "source-protocol-2"
    )
    assert by_role["investigator_brochure"].binding is not None
    assert by_role[
        "investigator_brochure"
    ].binding.source_entry_id == "source-investigator_brochure-4"
    assert all(
        item.binding is None
        or item.binding.clinical_applicability_resolved is False
        for item in packet.roles
    )


def test_registry_resolver_reuses_registry_supersession_policy() -> None:
    first = _entry("protocol", 1)
    second = _entry("protocol", 2)
    entries = [first, second]
    packet = MonitoringDocumentEvidenceResolver(
        _Registry(
            entries,
            [
                _span(first, 1),
                _span(first, 2),
                _span(second, 1),
                _span(second, 2),
            ],
        )
    ).resolve(
        project_id=PROJECT_ID,
        listing_admission_date="2026-09-03",
    )

    protocol = packet.roles[0]
    assert protocol.status == "current"
    assert protocol.binding is not None
    assert protocol.binding.source_entry_id == second.entry_id


def test_registry_resolver_rejects_partial_locator_index() -> None:
    protocol = _entry("protocol", 1)
    first = _span(protocol, 1)
    second = _span(protocol, 2)
    second.locator = ""
    packet = MonitoringDocumentEvidenceResolver(
        _Registry([protocol], [first, second])
    ).resolve(
        project_id=PROJECT_ID,
        listing_admission_date="2026-09-03",
    )

    assert packet.roles[0].status == "incomplete"


def test_registry_resolver_rejects_self_consistent_partial_span_count() -> None:
    protocol = _entry("protocol", 1)
    protocol.span_count = 1
    packet = MonitoringDocumentEvidenceResolver(
        _Registry([protocol], [_span(protocol, 1)])
    ).resolve(
        project_id=PROJECT_ID,
        listing_admission_date="2026-09-03",
    )

    assert packet.roles[0].status == "incomplete"


def test_ecrf_registration_persists_independent_locator_manifest(
    tmp_path: Path,
) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "AE表单"
    sheet.append(["字段名", "字段含义"])
    sheet.append(["AETERM", "不良事件名称"])
    stream = io.BytesIO()
    workbook.save(stream)
    registry = SourceRegistryService(
        SourceRegistryStore(tmp_path / "registry.jsonl")
    )

    result = registry.register_monitoring_mapping_document(
        PROJECT_ID,
        "forms.xlsx",
        stream.getvalue(),
        document_role="ecrf",
    )

    metadata = result.entry.metadata
    legacy_token = hashlib.sha256(
        (
            "workbench_source_registry_v0_1:"
            f"{PROJECT_ID}:medical_monitoring:ecrf:"
            f"{result.entry.content_hash}"
        ).encode("utf-8")
    ).hexdigest()[:12]
    legacy_entry_id = f"src_{PROJECT_ID.replace('-', '_')}_ecrf_{legacy_token}"
    assert result.entry.source_kind == "ecrf"
    assert result.entry.entry_id != legacy_entry_id
    assert metadata["locator_manifest_complete"] is True
    assert metadata["locator_manifest_revision"] == (
        "monitoring-locator-manifest-v1"
    )
    assert metadata["expected_locator_count"] == len(result.spans) == 1
    assert len(metadata["expected_locator_index_sha256"]) == 64


@pytest.mark.parametrize(
    ("role", "filename", "paragraphs"),
    (
        (
            "investigator_brochure",
            "investigator-brochure.docx",
            (
                "Investigator Brochure",
                "Nonclinical Studies",
                "Effects in Humans",
            ),
        ),
        (
            "sap",
            "statistical-analysis-plan.pdf",
            (
                "Statistical Analysis Plan",
                "Analysis Population",
                "Statistical Methods",
            ),
        ),
    ),
)
def test_optional_study_document_registration_is_locator_backed_and_current(
    tmp_path: Path,
    role: str,
    filename: str,
    paragraphs: tuple[str, ...],
) -> None:
    validation_store = SourceContentValidationStore(
        tmp_path / "validations.sqlite3"
    )
    registry = SourceRegistryService(
        SourceRegistryStore(tmp_path / "registry.jsonl"),
        artifact_root=tmp_path / "artifacts",
        content_validation_service=SourceContentValidationService(
            validation_store
        ),
        expected_context_resolver=lambda *_args: SourceExpectedContext(),
    )
    if filename.endswith(".docx"):
        document = docx.Document()
        for paragraph in paragraphs:
            document.add_paragraph(paragraph)
        stream = io.BytesIO()
        document.save(stream)
        payload = stream.getvalue()
    else:
        pymupdf = pytest.importorskip("pymupdf")
        document = pymupdf.open()
        page = document.new_page()
        page.insert_text((72, 72), "\n".join(paragraphs))
        payload = document.tobytes()
        document.close()

    result = registry.register_monitoring_mapping_document(
        PROJECT_ID,
        filename,
        payload,
        document_role=role,
    )
    validation = registry.current_content_validation(
        PROJECT_ID,
        result.entry.entry_id,
    )
    packet = MonitoringDocumentEvidenceResolver(registry).resolve(
        project_id=PROJECT_ID,
        listing_admission_date="2026-09-03",
    )
    evidence = next(item for item in packet.roles if item.role == role)

    assert result.entry.module == "medical_monitoring"
    assert result.entry.source_kind == {
        "investigator_brochure": "investigator_brochure",
        "sap": "statistical_analysis_plan",
    }[role]
    assert result.entry.metadata["locator_manifest_complete"] is True
    assert result.entry.metadata["expected_locator_count"] == len(
        result.spans
    )
    assert result.spans
    assert validation is not None
    assert validation.content_status == "matched"
    assert validation.use_status == "allowed"
    assert evidence.status == "current"
    assert evidence.binding is not None
    assert evidence.binding.locator_count == len(result.spans)
    assert packet.mapping_context_ready is False
    retrieval = MonitoringDocumentEvidenceResolver(
        registry
    ).retrieve_current_excerpts(
        project_id=PROJECT_ID,
        binding=evidence.binding,
        query_terms=(
            ["Nonclinical"]
            if role == "investigator_brochure"
            else ["Analysis Population"]
        ),
    )
    assert retrieval["source_entry_id"] == result.entry.entry_id
    assert retrieval["content_sha256"] == result.entry.content_hash
    assert retrieval["locator_index_sha256"] == (
        evidence.binding.locator_index_sha256
    )
    assert retrieval["excerpts"]
    assert retrieval["clinical_conclusions"] == []
    assert len(retrieval["packet_sha256"]) == 64
    with pytest.raises(
        ValueError,
        match="binding is no longer current",
    ):
        MonitoringDocumentEvidenceResolver(
            registry
        ).retrieve_current_excerpts(
            project_id=PROJECT_ID,
            binding=replace(
                evidence.binding,
                content_sha256="f" * 64,
            ),
            query_terms=["Analysis"],
        )
