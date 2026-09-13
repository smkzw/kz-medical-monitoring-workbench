"""v7.1 patch-repair contract: version sets, prompt discipline, envelope
localization, splice behavior, and frozen v7 full-rebuild compatibility."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

from services.api.app.monitoring_ai_contracts import MonitoringAiJobStatus
from services.api.app.monitoring_ai_service import MonitoringAiService
from tests.test_monitoring_ai_service import (
    FakeProvider,
    _field_profile,
    _revision,
    _service,
    _valid_output,
)

V71_PRIMARY = "monitoring-listing-field-mapping-adjudication-v16-tools-v7.1"
V71_VERIFIER = (
    "monitoring-listing-field-mapping-adjudication-verifier-v14-tools-v7.1"
)
V7_PRIMARY = "monitoring-listing-field-mapping-adjudication-v12-tools-v7"


def _patch_factory():
    @contextmanager
    def factory(*_args: Any):
        yield SimpleNamespace(schemas={}, execute=lambda *_: None)

    return factory


def _submit_v71(service: MonitoringAiService) -> Any:
    profile = _field_profile(1)
    profile["adjudication_contract"] = {"first_pass_mappings": []}
    return service.submit_listing_field_mapping(
        project_id="project-alpha",
        input_revision=_revision(),
        field_profile=profile,
        prompt_version=V71_PRIMARY,
    )


def test_v71_versions_and_pipeline_selection() -> None:
    from packages.medical_monitoring.admission.evidence_tool_contract import (
        PATCH_REPAIR_MAPPING_PROMPT_VERSIONS,
        ROLE_EQUIVALENCE_PROMPT_VERSIONS,
        STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS,
    )
    from packages.medical_monitoring.admission.mapping_pipeline import (
        MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS,
        MAPPING_ADJUDICATION_LEGACY_TERMINAL_PROMPT_VERSIONS,
        AdmissionMappingPipeline,
    )

    assert {V71_PRIMARY, V71_VERIFIER} <= PATCH_REPAIR_MAPPING_PROMPT_VERSIONS
    assert V71_PRIMARY in STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS
    assert V71_VERIFIER in STRICT_MAPPING_RESPONSE_PROMPT_VERSIONS
    assert V71_PRIMARY in ROLE_EQUIVALENCE_PROMPT_VERSIONS
    assert MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS == frozenset(
        {V71_PRIMARY, V71_VERIFIER}
    )
    assert V7_PRIMARY in MAPPING_ADJUDICATION_LEGACY_TERMINAL_PROMPT_VERSIONS
    assert "monitoring-listing-field-mapping-adjudication-v15-tools-v7.1" in (
        MAPPING_ADJUDICATION_LEGACY_TERMINAL_PROMPT_VERSIONS
    )
    pipeline = AdmissionMappingPipeline(
        adjudication_tool_reads=True,
        explicit_mapping_dependencies=True,
        visual_tool_reads=True,
        role_equivalence=True,
    )
    assert pipeline.adjudication_prompt_versions == frozenset(
        {V71_PRIMARY, V71_VERIFIER}
    )
    assert pipeline.adjudication_comparison_policy == (
        "mm-mapping-role-equivalence-v2"
    )


def test_v71_prompt_carries_key_discipline(tmp_path: Path) -> None:
    service = _service(tmp_path, FakeProvider([]))
    job = _submit_v71(service)
    payload = service.repository.input_payload(job.project_id, job.job_id)
    envelope = service._build_prompt_envelope(job, payload)
    for forbidden in (
        "role_equivalence_evidence",
        "counterevidence_summary",
        "user_action",
    ):
        assert forbidden in envelope.system_prompt
    assert "输出键名纪律" in envelope.system_prompt
    assert "不是输出键" in envelope.system_prompt


def _dependency_compliant(result: Dict[str, Any]) -> Dict[str, Any]:
    for mapping in result["candidates"][0]["structured_payload"][
        "field_mappings"
    ]:
        mapping["dependency_fields"] = []
        mapping["standards_reference"] = None
    return result


def _initial_with_empty_user_action(envelope: Any) -> Dict[str, Any]:
    result = _dependency_compliant(_valid_output(envelope))
    mappings = result["candidates"][0]["structured_payload"]["field_mappings"]
    mappings[0]["user_action"] = ""
    return result


def _patch_fixing_field_zero(envelope: Any) -> Dict[str, Any]:
    base = _dependency_compliant(_valid_output(envelope))
    mappings = base["candidates"][0]["structured_payload"]["field_mappings"]
    return {
        "schema_version": base["schema_version"],
        "task_id": base["task_id"],
        "task_type": base["task_type"],
        "input_revision_sha256": base["input_revision_sha256"],
        "candidates": [
            {
                "candidate_type": base["candidates"][0]["candidate_type"],
                "title": "字段修复补丁",
                "text": "",
                "structured_payload": {"field_mappings": [mappings[0]]},
                "evidence": base["candidates"][0]["evidence"],
            }
        ],
    }


def test_patch_repair_localizes_splices_and_completes(
    tmp_path: Path,
) -> None:
    provider = FakeProvider(
        [_initial_with_empty_user_action, _patch_fixing_field_zero]
    )
    service = _service(tmp_path, provider)
    service.evidence_tool_factory = _patch_factory()
    job = _submit_v71(service)

    result = service.run_next("worker-patch")

    assert result.job is not None
    assert result.job.status == MonitoringAiJobStatus.COMPLETED, (
        result.job.failure_message
    )
    assert len(provider.envelopes) == 2
    repair_payload = provider.envelopes[1].payload
    assert "patch_contract" in repair_payload
    targets = repair_payload["patch_contract"]["violating_fields"]
    assert len(targets) == 1
    fields = _field_profile(1)["fields"]
    assert targets[0]["domain"] == fields[0]["domain"]
    assert targets[0]["source_field"] == fields[0]["field"]
    assert any("user_action" in str(error) for error in targets[0]["errors"])
    # The patch output schema describes a patch, not the full document.
    patch_mappings = repair_payload["output_schema"]["candidates"][0][
        "structured_payload"
    ]["field_mappings"]
    assert isinstance(patch_mappings, list)
    candidates = service.repository.candidates(job.project_id, job.job_id)
    assert len(candidates) == 1
    stored = candidates[0].structured_payload["field_mappings"]
    assert stored[0]["user_action"]


def test_patch_repair_rejects_unknown_target(tmp_path: Path) -> None:
    def patch_with_unknown_field(envelope: Any) -> Dict[str, Any]:
        patch = _patch_fixing_field_zero(envelope)
        patch["candidates"][0]["structured_payload"]["field_mappings"][0][
            "source_field"
        ] = "不存在的字段"
        return patch

    provider = FakeProvider(
        [_initial_with_empty_user_action, patch_with_unknown_field]
    )
    service = _service(tmp_path, provider)
    service.evidence_tool_factory = _patch_factory()
    job = _submit_v71(service)

    result = service.run_next("worker-patch")

    assert result.job is not None
    assert result.job.status == MonitoringAiJobStatus.FAILED
    assert result.job.failure_code == "invalid_ai_output"
    assert "field patch target not present" in result.job.failure_message


def test_unlocalizable_error_keeps_full_rebuild_contract(
    tmp_path: Path,
) -> None:
    def envelope_level_invalid(envelope: Any) -> Dict[str, Any]:
        result = _valid_output(envelope)
        result["candidates"][0]["text_for_uncertain"] = "invented key"
        return result

    def full_rebuild(envelope: Any) -> Dict[str, Any]:
        return _dependency_compliant(_valid_output(envelope))

    provider = FakeProvider([envelope_level_invalid, full_rebuild])
    service = _service(tmp_path, provider)
    service.evidence_tool_factory = _patch_factory()
    _submit_v71(service)

    result = service.run_next("worker-patch")

    assert result.job is not None
    assert len(provider.envelopes) == 2
    assert "patch_contract" not in provider.envelopes[1].payload
    assert result.job.status == MonitoringAiJobStatus.COMPLETED, (
        result.job.failure_message
    )


def test_v7_prompt_keeps_frozen_full_repair(tmp_path: Path) -> None:
    provider = FakeProvider(
        [_initial_with_empty_user_action, _patch_fixing_field_zero]
    )
    service = _service(tmp_path, provider)
    service.evidence_tool_factory = _patch_factory()
    profile = _field_profile(2)
    profile["adjudication_contract"] = {"first_pass_mappings": []}
    service.submit_listing_field_mapping(
        project_id="project-alpha",
        input_revision=_revision(),
        field_profile=profile,
        prompt_version=V7_PRIMARY,
    )

    result = service.run_next("worker-v7")

    assert result.job is not None
    assert len(provider.envelopes) == 2
    assert "patch_contract" not in provider.envelopes[1].payload
    # v7 keeps its frozen full-rebuild instruction.
    assert "重建完整" in provider.envelopes[1].payload["repair_contract"][
        "instruction"
    ]
    # A patch-shaped response is not a valid full rebuild under v7.
    assert result.job.status == MonitoringAiJobStatus.FAILED


def test_custom_domain_field_error_localizes_for_patch() -> None:
    from services.api.app.monitoring_ai_contracts import MonitoringAiTaskType

    output = {"candidates": [{"structured_payload": {"field_mappings": [
        {"domain": "AE", "source_field": "AECO"}
    ]}}]}
    # Both the bare custom error and the controlled-formatter prefixed form
    # (observed in the real v7.1 isolated trial) must localize.
    for text in (
        "AE/AECO: role_equivalence_axis_invalid:object",
        "MonitoringAiOutputValidationError: AE/AECO: role_equivalence_axis_invalid:object",
    ):
        targets = MonitoringAiService._patch_repair_targets(
            SimpleNamespace(
                task_type=MonitoringAiTaskType.LISTING_FIELD_MAPPING,
                prompt_version=V71_PRIMARY,
            ),
            output,
            text,
        )
        assert targets == [
            {
                "domain": "AE",
                "source_field": "AECO",
                "errors": ["role_equivalence_axis_invalid:object"],
            }
        ]
