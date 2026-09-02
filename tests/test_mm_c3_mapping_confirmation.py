"""Focused tests for C3 admission mapping medical-question triage."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from packages.medical_monitoring.admission.mapping_confirmation import (
    AdmissionMappingConfirmationService,
    USER_QUESTION_LOW_CONFIDENCE,
    USER_QUESTION_MODEL_FLAGGED,
    USER_QUESTION_UNMAPPED,
    attention_reason,
    classify_user_question,
    enrich_candidates,
)
from packages.medical_monitoring.admission.mapping_pipeline import (
    AdmissionMappingPipelineError,
)
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (
    _mapping_error,
)


def test_attention_reason_adopts_sound_candidates_and_questions_substantive_ones() -> None:
    # Low confidence remains system-owned re-analysis work.
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "visit_date",
        "field_kind": "source_collected",
        "user_action": "请核对访视日期对应关系。",
    }) == ""
    # Coding, derived and investigational-product roles no longer force a
    # user question when the system itself is confident.
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "ae_term_term",
        "field_kind": "standardized_coded",
        "user_action": "请核对编码依据。",
    }) == ""
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "record_line_number",
        "field_kind": "deterministic_derived",
        "user_action": "请核对派生依据。",
    }) == ""
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "ip.dose",
        "field_kind": "source_collected",
        "user_action": "请核对研究用药剂量。",
    }) == ""
    assert attention_reason({
        "confidence": 0.4,
        "recommended_role": "visit_date",
        "field_kind": "source_collected",
        "user_action": "请核对访视日期对应关系。",
    }) == ""
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "unmapped",
        "field_kind": "unmapped",
        "user_action": "请确认字段用途。",
    }) == ""
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "ip.dose",
        "field_kind": "source_collected",
        "user_action": "该字段是研究用药剂量还是非研究用药剂量？",
        "user_decision_required": True,
    }) == "需医学确认"
    assert attention_reason({
        "confidence": 0.99,
        "recommended_role": "visit_date",
        "field_kind": "source_collected",
        "user_action": " ",
    }) == ""


def test_unreadable_confidence_is_not_transferred_to_the_user() -> None:
    question = classify_user_question({
        "confidence": None,
        "recommended_role": "visit_date",
        "field_kind": "source_collected",
        "user_action": "请核对访视日期对应关系。",
    })
    assert question is None


def test_decision_marker_resolves_a_question() -> None:
    assert classify_user_question({
        "confidence": 0.4,
        "recommended_role": "visit_date",
        "field_kind": "source_collected",
        "user_action": "用户已核对：确认为访视日期。",
        "user_decision_required": True,
    }) is None
    assert classify_user_question({
        "confidence": 0.99,
        "recommended_role": "unmapped",
        "field_kind": "unmapped",
        "user_action": "用户已确认：导出系统编号，不纳入监查分析。",
        "user_decision_required": True,
    }) is None
    assert classify_user_question({
        "confidence": 0.7,
        "recommended_role": "unmapped",
        "field_kind": "unmapped",
        "user_action": "该字段是否不纳入监查分析？",
        "user_decision_required": True,
    }) is not None


def test_enrich_candidates_projects_medical_questions_and_blocks_facts() -> None:
    payload = {
        "attempt_id": "attempt-1",
        "state": "candidates_ready",
        "confirmation_status": "pending_confirmation",
        "summary": {"candidate_count": 3},
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
            {
                "domain": "EX",
                "source_field": "EXDOSE",
                "recommended_role": "ip.dose",
                "confidence": 0.99,
                "field_kind": "source_collected",
                "user_action": "该字段是研究用药剂量还是非研究用药剂量？",
                "user_decision_required": True,
            },
        ],
    }
    critical = enrich_candidates(payload, focus="critical")
    assert critical["facts_generated"] is False
    assert critical["candidate_fact_boundary"] == "candidates_only"
    summary = critical["summary"]
    assert summary["field_count"] == 3
    assert summary["user_question_count"] == 1
    assert summary["system_adopted_count"] == 2
    assert summary["critical_count"] == 1
    assert summary["displayed_count"] == 1
    assert [row["source_field"] for row in critical["candidates"]] == [
        "EXDOSE",
    ]
    assert critical["candidates"][0]["triage"] == "user_question"
    assert critical["candidates"][0]["question_reason"] == USER_QUESTION_MODEL_FLAGGED
    assert critical["candidates"][0]["system_adopted"] is False
    assert "研究用药剂量还是非研究用药剂量" in (
        critical["candidates"][0]["question_text"]
    )
    assert [card["source_field"] for card in critical["user_questions"]] == [
        "EXDOSE",
    ]
    assert all(card["question_text"] for card in critical["user_questions"])

    all_rows = enrich_candidates(payload, focus="all")
    assert all_rows["summary"]["displayed_count"] == 3
    adopted = next(
        row
        for row in all_rows["candidates"]
        if row["source_field"] == "AESER"
    )
    assert adopted["triage"] == "system_adopted"
    assert adopted["system_adopted"] is True
    assert adopted["attention_reason"] == ""
    assert adopted["question_text"] == ""


def test_enrich_candidates_rejects_invalid_focus() -> None:
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        enrich_candidates({"candidates": []}, focus="mystery")
    assert exc.value.code == "mapping_focus_invalid"


def _confirmation_service(repo):
    return AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
    )


def test_confirm_draft_blocked_while_medical_questions_unresolved() -> None:
    draft = SimpleNamespace(
        batch_id="attempt-1",
        model_dump=lambda mode="json": {
            "fields": [
                {
                    "domain": "SV",
                    "source_field": "VISIT",
                    "recommended_role": "visit_name",
                    "field_kind": "source_collected",
                    "confidence": 0.4,
                    "user_action": "请核对访视名称对应关系。",
                    "user_decision_required": True,
                },
            ],
        },
    )

    def _must_not_confirm(*_args, **_kwargs):
        raise AssertionError("confirmation must not persist unresolved questions")

    repo = SimpleNamespace(
        get_draft=lambda *_args, **_kwargs: draft,
        confirm=_must_not_confirm,
    )
    service = _confirmation_service(repo)

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
    assert exc.value.code == "mapping_questions_unresolved"


def test_confirm_draft_adopts_sound_fields_and_records_decisions() -> None:
    def _confirm(*_args, **_kwargs):
        return SimpleNamespace(
            model_dump=lambda mode="json": {
                "mapping_revision": "rev-1",
                "draft_id": "draft-1",
                "status": "confirmed",
            }
        )

    # A low-confidence field with a recorded human decision no longer blocks;
    # an unmapped field the manager marked 不纳入 is equally resolved.
    draft = SimpleNamespace(
        batch_id="attempt-1",
        model_dump=lambda mode="json": {
            "fields": [
                {
                    "domain": "SV",
                    "source_field": "VISIT",
                    "recommended_role": "visit_name",
                    "field_kind": "source_collected",
                    "confidence": 0.4,
                    "user_action": "用户已核对：确认为访视名称。",
                    "user_decision_required": True,
                },
                {
                    "domain": "DM",
                    "source_field": "EXPORTNO",
                    "recommended_role": "unmapped",
                    "field_kind": "unmapped",
                    "confidence": 0.99,
                    "user_action": "用户已确认：导出系统编号，不纳入监查分析。",
                    "user_decision_required": True,
                },
                {
                    "domain": "AE",
                    "source_field": "AETERM",
                    "recommended_role": "ae_term",
                    "field_kind": "source_collected",
                    "confidence": 0.99,
                    "user_action": "系统已按建议采用，无需额外操作。",
                },
            ],
        },
    )
    repo = SimpleNamespace(
        get_draft=lambda *_args, **_kwargs: draft,
        confirm=_confirm,
    )
    payload = _confirmation_service(repo).confirm_draft(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        expected_version=1,
        confirmed_by="tester",
        confirmation_reason="医学问题已逐条回答完成。",
        idempotency_key="idem-1",
    )
    assert payload["facts_generated"] is False
    assert payload["next_action"] == "generate_facts_later"
    assert payload["confirmation_status"] == "confirmed"


def test_confirm_draft_rejects_another_attempt() -> None:
    repo = SimpleNamespace(
        get_draft=lambda *_args, **_kwargs: SimpleNamespace(batch_id="attempt-2")
    )
    service = _confirmation_service(repo)
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


def test_unresolved_question_error_is_actionable_for_users() -> None:
    response = _mapping_error("mapping_questions_unresolved")

    assert response.status_code == 422
    body = response.body.decode("utf-8")
    assert "医学问题" in body
    assert "整体确认" in body


def test_quality_blocked_error_is_distinguishable_from_conflict() -> None:
    response = _mapping_error("mapping_quality_blocked")

    assert response.status_code == 409
    assert "修订对应字段" in response.body.decode("utf-8")


def test_draft_payload_keeps_medical_question_projection_after_adoption() -> None:
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
                        "user_decision_required": True,
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
    payload = _confirmation_service(repo)._draft_payload(FakeDraft())

    assert payload["review_summary"] == {
        "field_count": 2,
        "user_question_count": 1,
        "system_adopted_count": 1,
        "system_adjudicated_count": 0,
        "critical_count": 1,
    }
    assert payload["user_questions"][0]["source_field"] == "AETERM"
    question_field = payload["fields"][0]
    assert question_field["triage"] == "user_question"
    assert question_field["attention_reason"] == "需医学确认"
    adopted_field = payload["fields"][1]
    assert adopted_field["triage"] == "system_adopted"
    assert adopted_field["needs_attention"] is False
    assert payload["facts_generated"] is False
    assert payload["candidate_fact_boundary"] == "draft_only"


def test_second_pass_only_clears_an_unchanged_evidence_supported_mapping() -> None:
    field = {
        "domain": "AE",
        "source_field": "AETERM",
        "recommended_role": "ae_term",
        "field_kind": "source_collected",
        "confidence": 0.6,
        "uncertainty": "第一轮仍有疑点。",
        "user_action": "该列是否为不良事件术语？",
        "user_decision_required": True,
    }
    state = {"version": 1, "field": dict(field)}

    class Draft:
        batch_id = "attempt-1"
        draft_id = "draft-1"

        @property
        def version(self):
            return state["version"]

        def model_dump(self, mode="json"):
            return {
                "project_id": "p1",
                "draft_id": self.draft_id,
                "batch_id": self.batch_id,
                "version": state["version"],
                "fields": [dict(state["field"])],
            }

    draft = Draft()
    quality = SimpleNamespace(as_payload=lambda: {"confirmable": True})

    def edit_field(*_args, patch, **_kwargs):
        state["field"].update(patch)
        state["version"] += 1
        return draft

    mapping_repo = SimpleNamespace(
        get_draft=lambda *_args: draft,
        edit_field=edit_field,
        semantic_quality=lambda *_args: quality,
    )
    candidate = SimpleNamespace(candidate_id="candidate-1", status="proposed")
    job = SimpleNamespace(
        job_id="job-1",
        project_id="p1",
        input_revision_sha256="r" * 64,
    )
    decisions = []
    ai_repo = SimpleNamespace(
        get=lambda *_args: job,
        candidates=lambda *_args: (candidate,),
        decide_candidate=lambda *_args, **kwargs: decisions.append(kwargs),
    )
    pipeline = SimpleNamespace(
        adjudicate_candidates=lambda **_kwargs: {
            "state": "ready",
            "mappings": [{
                **field,
                "user_decision_required": False,
                "uncertainty": "同表语境支持原对应。",
                "user_action": "同表术语字段与结果分布一致。",
                "candidate_id": "candidate-1",
                "job_id": "job-1",
            }],
        },
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=pipeline,
        mapping_repository=mapping_repo,
        ai_repository=ai_repo,
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
        current_revision_resolver=lambda *_args, **_kwargs: "r" * 64,
    )

    payload = service.adjudicate_draft(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        workspace_dir="/generated/non-real",
    )

    assert payload["adjudication"] == {
        "state": "complete",
        "resolved_count": 1,
        "remaining_question_count": 0,
    }
    assert payload["review_summary"]["system_adjudicated_count"] == 1
    assert state["field"]["user_decision_required"] is False
    assert state["field"]["user_action"].startswith("系统复核：")
    assert decisions
