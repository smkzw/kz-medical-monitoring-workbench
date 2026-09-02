"""Focused tests for C3 admission mapping confirmation helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from packages.medical_monitoring.admission.mapping_confirmation import (
    AdmissionMappingConfirmationService,
    attention_reason,
    enrich_candidates,
)
from packages.medical_monitoring.admission.mapping_pipeline import (
    AdmissionMappingPipelineError,
)
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (
    _mapping_error,
)


def test_attention_reason_marks_low_confidence_and_medication_roles() -> None:
    assert attention_reason({
        "confidence": 0.4,
        "recommended_role": "visit_date",
        "user_action": "请核对访视日期对应关系。",
    }) == "低置信度"
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "ip.dose",
        "field_kind": "source_collected",
        "user_action": "请核对研究用药剂量。",
    }) == "用药边界"
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "subject_id",
        "field_kind": "source_collected",
        "user_action": "请核对受试者编号。",
    }) == ""
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "visit_date",
        "field_kind": "source_collected",
        "user_action": " ",
    }) == "建议不完整"


def test_enrich_candidates_defaults_to_critical_focus_and_blocks_facts() -> None:
    payload = {
        "attempt_id": "attempt-1",
        "state": "candidates_ready",
        "confirmation_status": "pending_confirmation",
        "summary": {"candidate_count": 2},
        "candidates": [
            {
                "domain": "AE",
                "source_field": "AETERM",
                "recommended_role": "ae_term",
                "confidence": 0.4,
                "field_kind": "source_collected",
                "user_action": "请核对不良事件术语。",
            },
            {
                "domain": "AE",
                "source_field": "AESER",
                "recommended_role": "ae_serious_flag",
                "confidence": 0.99,
                "field_kind": "source_collected",
                "user_action": "请核对严重性标志。",
            },
        ],
    }
    critical = enrich_candidates(payload, focus="critical")
    assert critical["facts_generated"] is False
    assert critical["candidate_fact_boundary"] == "candidates_only"
    assert critical["summary"]["critical_count"] == 1
    assert critical["summary"]["displayed_count"] == 1
    assert critical["candidates"][0]["source_field"] == "AETERM"
    assert critical["candidates"][0]["attention_reason"] == "低置信度"

    all_rows = enrich_candidates(payload, focus="all")
    assert all_rows["summary"]["displayed_count"] == 2


def test_confirm_draft_never_claims_facts_generated() -> None:
    class FakeRepo:
        def get_draft(self, *args, **kwargs):
            return SimpleNamespace(
                batch_id="attempt-1",
                model_dump=lambda mode="json": {
                    "fields": [{"user_action": "已核对字段对应关系。"}],
                },
            )

        def confirm(self, *args, **kwargs):
            return SimpleNamespace(
                model_dump=lambda mode="json": {
                    "mapping_revision": "rev-1",
                    "draft_id": "draft-1",
                    "status": "confirmed",
                }
            )

    service = AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=FakeRepo(),
        ai_repository=SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
    )
    payload = service.confirm_draft(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        expected_version=1,
        confirmed_by="tester",
        confirmation_reason="核对完成",
        idempotency_key="idem-1",
    )
    assert payload["facts_generated"] is False
    assert payload["next_action"] == "generate_facts_later"
    assert payload["confirmation_status"] == "confirmed"


def test_confirm_draft_rejects_another_attempt() -> None:
    repo = SimpleNamespace(
        get_draft=lambda *_args, **_kwargs: SimpleNamespace(batch_id="attempt-2")
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        service.confirm_draft(
            project_id="p1",
            attempt_id="attempt-1",
            draft_id="draft-1",
            expected_version=1,
            confirmed_by="tester",
            confirmation_reason="核对完成",
            idempotency_key="idem-1",
        )
    assert exc.value.code == "mapping_draft_conflict"


def test_confirm_draft_rejects_incomplete_chinese_advice() -> None:
    draft = SimpleNamespace(
        batch_id="attempt-1",
        model_dump=lambda mode="json": {
            "fields": [{"domain": "SV", "source_field": "VISIT", "user_action": ""}],
        },
    )
    repo = SimpleNamespace(get_draft=lambda *_args, **_kwargs: draft)
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
    )

    with pytest.raises(AdmissionMappingPipelineError) as exc:
        service.confirm_draft(
            project_id="p1",
            attempt_id="attempt-1",
            draft_id="draft-1",
            expected_version=1,
            confirmed_by="tester",
            confirmation_reason="已完成全部重点字段核对。",
            idempotency_key="idem-1",
        )

    assert exc.value.code == "mapping_advice_incomplete"


def test_incomplete_advice_has_actionable_product_error() -> None:
    response = _mapping_error("mapping_advice_incomplete")

    assert response.status_code == 422
    assert "缺少具体的中文核对建议" in response.body.decode("utf-8")


def test_draft_payload_keeps_critical_focus_metadata_after_adoption() -> None:
    class FakeDraft:
        def model_dump(self, mode="json"):
            return {
                "project_id": "p1",
                "draft_id": "draft-1",
                "fields": [
                    {
                        "domain": "AE",
                        "source_field": "AETERM",
                        "recommended_role": "ae_term",
                        "field_kind": "source_collected",
                        "confidence": 0.4,
                        "user_action": "请核对不良事件术语。",
                    },
                    {
                        "domain": "AE",
                        "source_field": "AESER",
                        "recommended_role": "ae_serious_flag",
                        "field_kind": "source_collected",
                        "confidence": 0.99,
                        "user_action": "请核对严重性标志。",
                    },
                ],
            }

    quality = SimpleNamespace(as_payload=lambda: {"confirmable": True})
    repo = SimpleNamespace(semantic_quality=lambda *_args: quality)
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
    )

    payload = service._draft_payload(FakeDraft())

    assert payload["review_summary"] == {"field_count": 2, "critical_count": 1}
    assert payload["fields"][0]["attention_reason"] == "低置信度"
    assert payload["fields"][1]["needs_attention"] is False


def test_enrich_candidates_rejects_invalid_focus() -> None:
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        enrich_candidates({"candidates": []}, focus="mystery")
    assert exc.value.code == "mapping_focus_invalid"
