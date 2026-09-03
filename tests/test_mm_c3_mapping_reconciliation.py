"""Contract tests for deterministic C3 dual-cohort mapping reconciliation.

Covers the five contract rules: full field coverage, evidence reference
closure, agreement auto-pass, divergence preservation, and the
mapping-stage ban on CTCAE grade / risk / Query conclusions.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from packages.medical_monitoring.admission.mapping_confirmation import (
    AdmissionMappingConfirmationService,
)
from packages.medical_monitoring.admission.mapping_pipeline import (
    AdmissionMappingPipelineError,
)
from packages.medical_monitoring.admission.mapping_reconciliation import (
    COHORT_PRIMARY,
    COHORT_VERIFIER,
    RECONCILIATION_SCHEMA_VERSION,
    MappingReconciliationError,
    cohort_payload_from_candidates,
    mapping_conclusion_violations,
    reconcile_mapping_cohorts,
)


PROFILE = [
    {"domain": "AE", "field": "AETERM"},
    {"domain": "AE", "field": "AESER"},
    {"domain": "SV", "field": "VISIT"},
]


def _item(
    domain: str,
    source_field: str,
    role: str,
    kind: str = "source_collected",
    evidence=("ev-1",),
    **extra,
):
    payload = {
        "domain": domain,
        "source_field": source_field,
        "recommended_role": role,
        "field_kind": kind,
        "confidence": 0.9,
        "evidence_ids": list(evidence),
    }
    payload.update(extra)
    return payload


def _primary_verdicts():
    return [
        _item("AE", "AETERM", "ae_term"),
        _item("AE", "AESER", "ae_serious_flag"),
        _item("SV", "VISIT", "visit_name", evidence=("ev-sv",)),
    ]


def _verifier_verdicts():
    return [
        _item("AE", "AETERM", "ae_term", evidence=("ev-glm-1",)),
        _item("AE", "AESER", "ae_serious_flag", evidence=("ev-glm-2",)),
        _item("SV", "VISIT", "visit_name", evidence=("ev-glm-3",)),
    ]


PRIMARY_EVIDENCE = frozenset({"ev-1", "ev-sv"})
VERIFIER_EVIDENCE = frozenset({"ev-glm-1", "ev-glm-2", "ev-glm-3"})


def _reconcile(**overrides):
    kwargs = {
        "profile_fields": PROFILE,
        "primary_mappings": _primary_verdicts(),
        "verifier_mappings": _verifier_verdicts(),
        "primary_evidence_ids": PRIMARY_EVIDENCE,
        "verifier_evidence_ids": VERIFIER_EVIDENCE,
    }
    kwargs.update(overrides)
    return reconcile_mapping_cohorts(**kwargs)


def test_full_agreement_auto_passes_with_closed_evidence() -> None:
    report = _reconcile()

    assert report["schema_version"] == RECONCILIATION_SCHEMA_VERSION
    assert report["state"] == "agreed"
    assert report["auto_pass"] is True
    assert report["summary"]["field_count"] == 3
    assert report["summary"]["agreed_count"] == 3
    assert report["summary"]["diverged_count"] == 0
    assert report["summary"]["blocked_count"] == 0
    assert report["summary"]["human_decision_count"] == 0
    assert report["coverage_violations"] == []
    assert report["contract_violations"] == []
    assert report["divergences"] == []
    assert report["facts_generated"] is False
    assert report["candidate_fact_boundary"] == "reconciliation_only"
    assert [row["source_field"] for row in report["fields"]] == [
        "AETERM",
        "AESER",
        "VISIT",
    ]


def test_reconciliation_is_deterministic() -> None:
    assert _reconcile() == _reconcile()


def test_verdict_copies_are_preserved_not_aliased() -> None:
    primary = _primary_verdicts()
    report = _reconcile(primary_mappings=primary)
    primary[0]["evidence_ids"].append("ev-late")

    assert "ev-late" not in report["fields"][0]["primary"]["evidence_ids"]


def test_role_divergence_is_preserved_for_system_review_first() -> None:
    verifier = _verifier_verdicts()
    verifier[0]["recommended_role"] = "ae_term_text"

    report = _reconcile(verifier_mappings=verifier)

    assert report["state"] == "diverged"
    assert report["auto_pass"] is False
    assert report["summary"]["agreed_count"] == 2
    assert report["summary"]["diverged_count"] == 1
    divergence = report["divergences"][0]
    assert divergence["domain"] == "AE"
    assert divergence["source_field"] == "AETERM"
    assert divergence["primary"]["recommended_role"] == "ae_term"
    assert divergence["verifier"]["recommended_role"] == "ae_term_text"
    assert divergence["primary"]["evidence_ids"] == ["ev-1"]
    assert divergence["verifier"]["evidence_ids"] == ["ev-glm-1"]
    row = report["fields"][0]
    assert row["result"] == "diverged"
    assert row["human_decision_required"] is False
    assert row["system_review_required"] is True


def test_field_kind_divergence_never_auto_passes() -> None:
    verifier = _verifier_verdicts()
    verifier[1]["field_kind"] = "unmapped"

    report = _reconcile(verifier_mappings=verifier)

    assert report["state"] == "diverged"
    assert report["auto_pass"] is False
    assert report["divergences"][0]["source_field"] == "AESER"


def test_case_only_role_difference_still_agrees() -> None:
    verifier = _verifier_verdicts()
    verifier[0]["recommended_role"] = "AE_TERM"

    report = _reconcile(verifier_mappings=verifier)

    assert report["state"] == "agreed"
    assert report["auto_pass"] is True


def test_non_role_semantic_difference_never_auto_passes() -> None:
    primary = _primary_verdicts()
    verifier = _verifier_verdicts()
    primary[0]["standards_reference"] = {
        "system": "MedDRA",
        "version": "27.1",
    }
    verifier[0]["standards_reference"] = None

    report = _reconcile(
        primary_mappings=primary,
        verifier_mappings=verifier,
    )

    assert report["state"] == "diverged"
    assert report["auto_pass"] is False
    assert report["divergences"][0]["source_field"] == "AETERM"


def test_unmapped_verdicts_agree_without_evidence() -> None:
    primary = [
        _item("AE", "AETERM", "unmapped", kind="unmapped", evidence=()),
        _item("AE", "AESER", "unmapped", kind="unmapped", evidence=()),
        _item("SV", "VISIT", "unmapped", kind="unmapped", evidence=()),
    ]
    verifier = [
        _item("AE", "AETERM", "unmapped", kind="unmapped", evidence=()),
        _item("AE", "AESER", "unmapped", kind="unmapped", evidence=()),
        _item("SV", "VISIT", "unmapped", kind="unmapped", evidence=()),
    ]

    report = _reconcile(
        primary_mappings=primary,
        verifier_mappings=verifier,
    )

    assert report["state"] == "agreed"
    assert report["auto_pass"] is True


def test_mapped_field_without_verifier_evidence_cannot_auto_pass() -> None:
    verifier = _verifier_verdicts()
    verifier[0]["evidence_ids"] = []

    report = _reconcile(verifier_mappings=verifier)

    assert report["state"] == "blocked"
    assert report["auto_pass"] is False
    violation = report["contract_violations"][0]
    assert violation["cohort"] == COHORT_VERIFIER
    assert violation["code"] == "evidence_reference_missing"
    assert violation["source_field"] == "AETERM"


def test_unknown_evidence_reference_blocks_the_cohort() -> None:
    verifier = _verifier_verdicts()
    verifier[0]["evidence_ids"] = ["ev-glm-1", "ev-hallucinated"]

    report = _reconcile(verifier_mappings=verifier)

    assert report["state"] == "blocked"
    assert report["auto_pass"] is False
    closure = report["fields"][0]["verifier_evidence_closure"]
    assert closure["closed"] is False
    assert closure["unknown_evidence_ids"] == ["ev-hallucinated"]
    assert any(
        item["code"] == "evidence_reference_unclosed"
        and item["detail"] == "ev-hallucinated"
        for item in report["contract_violations"]
    )
    # Both verdicts stay preserved even though the field is blocked.
    assert report["fields"][0]["verifier"]["evidence_ids"] == [
        "ev-glm-1",
        "ev-hallucinated",
    ]
    assert report["fields"][0]["human_decision_required"] is False


def test_missing_verifier_field_blocks_full_auto_pass() -> None:
    verifier = _verifier_verdicts()[:2]

    report = _reconcile(verifier_mappings=verifier)

    assert report["state"] == "blocked"
    assert report["auto_pass"] is False
    assert report["summary"]["coverage_violation_count"] == 1
    assert report["coverage_violations"] == [
        {
            "cohort": COHORT_VERIFIER,
            "code": "missing_in_verifier",
            "domain": "SV",
            "source_field": "VISIT",
        }
    ]


def test_single_cohort_can_never_auto_pass() -> None:
    report = _reconcile(verifier_mappings=())

    assert report["state"] == "blocked"
    assert report["auto_pass"] is False
    assert report["summary"]["coverage_violation_count"] == 3


def test_unexpected_field_in_either_cohort_blocks() -> None:
    primary = _primary_verdicts()
    primary.append(_item("EX", "EXDOSE", "ip.dose"))

    report = _reconcile(primary_mappings=primary)

    assert report["state"] == "blocked"
    assert report["auto_pass"] is False
    assert report["summary"]["coverage_violation_count"] == 1
    assert report["coverage_violations"] == [
        {
            "cohort": COHORT_PRIMARY,
            "code": "unexpected_in_primary",
            "domain": "EX",
            "source_field": "EXDOSE",
        }
    ]
    assert report["contract_violations"] == []


def test_duplicate_field_in_a_cohort_blocks() -> None:
    primary = _primary_verdicts()
    primary.append(_item("AE", "AETERM", "ae_term_dup"))

    report = _reconcile(primary_mappings=primary)

    assert report["state"] == "blocked"
    assert report["auto_pass"] is False
    assert report["summary"]["agreed_count"] == 2
    assert report["summary"]["blocked_count"] == 1
    assert any(
        item["code"] == "duplicate_in_primary"
        and item["source_field"] == "AETERM"
        for item in report["coverage_violations"]
    )
    # The duplicated verdict stays visible on its field row.
    assert report["fields"][0]["result"] == "blocked"
    assert any(
        item["code"] == "duplicate_in_primary"
        for item in report["fields"][0]["violations"]
    )


def test_ctcae_grade_conclusion_is_a_contract_violation() -> None:
    primary = _primary_verdicts()
    primary[0]["uncertainty"] = "术语明确。该记录判定为 CTCAE 3级。"

    report = _reconcile(primary_mappings=primary)

    assert report["state"] == "blocked"
    assert report["auto_pass"] is False
    assert any(
        item["code"] == "ctcae_grade_conclusion"
        and item["cohort"] == COHORT_PRIMARY
        and item["detail"] == "uncertainty"
        for item in report["contract_violations"]
    )
    assert report["fields"][0]["result"] == "blocked"


def test_risk_and_query_conclusions_are_contract_violations() -> None:
    primary = _primary_verdicts()
    primary[1]["user_action"] = "风险等级：高。建议发起医学Query。"

    report = _reconcile(primary_mappings=primary)

    assert report["state"] == "blocked"
    codes = {
        item["code"] for item in report["contract_violations"]
    }
    assert "risk_conclusion" in codes
    assert "query_conclusion" in codes


def test_structured_conclusion_keys_are_contract_violations() -> None:
    primary = _primary_verdicts()
    primary[2]["ctcae_grade"] = "3"

    report = _reconcile(primary_mappings=primary)

    assert report["state"] == "blocked"
    assert any(
        item["code"] == "forbidden_conclusion_field"
        and item["detail"] == "ctcae_grade"
        for item in report["contract_violations"]
    )


def test_field_description_of_ctcae_column_is_not_a_conclusion() -> None:
    item = _item(
        "AE",
        "AETOXGR",
        "ae_toxicity_grade",
        uncertainty="该字段为CTCAE分级字段，编码依据不足，需要核对。",
        user_action="请核对CTCAE分级字段与术语字段的对应关系。",
    )

    assert mapping_conclusion_violations(item) == []


def test_invalid_profile_is_rejected() -> None:
    with pytest.raises(MappingReconciliationError) as exc:
        reconcile_mapping_cohorts(profile_fields=[])
    assert exc.value.code == "reconciliation_profile_invalid"

    with pytest.raises(MappingReconciliationError) as exc:
        reconcile_mapping_cohorts(
            profile_fields=[
                {"domain": "AE", "field": "AETERM"},
                {"domain": "AE", "field": "AETERM"},
            ],
        )
    assert exc.value.code == "reconciliation_profile_invalid"

    with pytest.raises(MappingReconciliationError) as exc:
        reconcile_mapping_cohorts(
            profile_fields=[{"domain": "AE", "field": "  "}],
        )
    assert exc.value.code == "reconciliation_profile_invalid"


def test_cohort_payload_from_candidates_extracts_verdicts_and_evidence() -> None:
    candidates = [
        SimpleNamespace(
            candidate_id="cand-1",
            evidence=[
                SimpleNamespace(evidence_id="ev-a"),
                SimpleNamespace(evidence_id="ev-b"),
            ],
            structured_payload={
                "field_mappings": [
                    _item("AE", "AETERM", "ae_term"),
                ],
            },
        ),
        SimpleNamespace(
            candidate_id="cand-2",
            evidence=[SimpleNamespace(evidence_id="ev-c")],
            structured_payload={"field_mappings": []},
        ),
    ]

    payload = cohort_payload_from_candidates(candidates)

    assert payload["evidence_ids"] == frozenset({"ev-a", "ev-b", "ev-c"})
    assert payload["mappings"] == [
        {
            "domain": "AE",
            "source_field": "AETERM",
            "recommended_role": "ae_term",
            "field_kind": "source_collected",
            "confidence": 0.9,
            "evidence_ids": ["ev-1"],
            "candidate_id": "cand-1",
        }
    ]


def _service_with_draft(fields):
    class Draft:
        batch_id = "attempt-1"
        draft_id = "draft-1"
        version = 1

        def model_dump(self, mode="json"):
            return {
                "project_id": "p1",
                "draft_id": self.draft_id,
                "batch_id": self.batch_id,
                "version": self.version,
                "fields": fields,
            }

    quality = SimpleNamespace(as_payload=lambda: {"confirmable": True})
    repo = SimpleNamespace(
        get_draft=lambda *_args: Draft(),
        semantic_quality=lambda *_args: quality,
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
    )
    return service


DRAFT_FIELDS = [
    {
        "domain": "AE",
        "source_field": "AETERM",
        "recommended_role": "ae_term",
        "field_kind": "source_collected",
        "confidence": 0.9,
        "evidence_ids": ["ev-1"],
    },
]


def _verifier_candidate(role="ae_term", evidence=("ev-glm-1",)):
    return SimpleNamespace(
        candidate_id="verifier-cand-1",
        evidence=[SimpleNamespace(evidence_id=item) for item in evidence],
        structured_payload={
            "field_mappings": [
                _item("AE", "AETERM", role, evidence=evidence),
            ],
        },
    )


def test_service_reconciliation_auto_passes_on_agreement() -> None:
    service = _service_with_draft(DRAFT_FIELDS)

    payload = service.reconcile_with_verifier(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        verifier_candidates=[_verifier_candidate()],
    )

    assert payload["reconciliation"]["state"] == "agreed"
    assert payload["reconciliation"]["auto_pass"] is True
    assert payload["review_summary"]["field_count"] == 1


def test_service_reconciliation_preserves_divergence_without_editing() -> None:
    service = _service_with_draft(DRAFT_FIELDS)

    payload = service.reconcile_with_verifier(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        verifier_candidates=[_verifier_candidate(role="ae_term_text")],
    )

    reconciliation = payload["reconciliation"]
    assert reconciliation["state"] == "diverged"
    assert reconciliation["auto_pass"] is False
    divergence = reconciliation["divergences"][0]
    assert divergence["primary"]["recommended_role"] == "ae_term"
    assert divergence["verifier"]["recommended_role"] == "ae_term_text"
    # The draft itself is untouched; reconciliation never picks a winner.
    assert payload["fields"][0]["recommended_role"] == "ae_term"
    assert "user_questions" in payload


def test_service_reconciliation_requires_the_attempts_own_draft() -> None:
    repo = SimpleNamespace(
        get_draft=lambda *_args: SimpleNamespace(batch_id="attempt-2")
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
    )
    from packages.medical_monitoring.admission.mapping_pipeline import (
        AdmissionMappingPipelineError,
    )

    with pytest.raises(AdmissionMappingPipelineError) as exc:
        service.reconcile_with_verifier(
            project_id="p1",
            attempt_id="attempt-1",
            draft_id="draft-1",
            verifier_candidates=[],
        )
    assert exc.value.code == "mapping_draft_conflict"


def test_confirmation_gate_waits_for_repository_backed_verifier() -> None:
    service = _service_with_draft(DRAFT_FIELDS)
    service.require_dual_reconciliation = True

    with pytest.raises(AdmissionMappingPipelineError) as exc:
        service.confirm_draft(
            project_id="p1",
            attempt_id="attempt-1",
            draft_id="draft-1",
            expected_version=1,
            confirmed_by="system_harness",
            confirmation_reason="双模型复核。",
            idempotency_key="dual-review-1",
        )

    assert getattr(exc.value, "code", "") == "mapping_verifier_incomplete"


def test_acceptance_rejects_ctcae_grade_conclusion_in_provider_output() -> None:
    import services.api.app.monitoring_ai_service as service_module

    base = {
        "domain": "AE",
        "source_field": "AETERM",
        "recommended_role": "ae_term",
        "field_kind": "source_collected",
        "confidence": 0.9,
        "uncertainty": "同表术语分布一致。",
        "user_action": "请核对不良事件术语。",
        "user_decision_required": False,
        "evidence_ids": ["ev-1"],
    }
    validated = service_module._FieldMappingItem.model_validate(base)
    assert validated.recommended_role == "ae_term"

    concluded = dict(base)
    concluded["uncertainty"] = "该记录判定为 CTCAE 4级。"
    with pytest.raises(ValidationError) as exc:
        service_module._FieldMappingItem.model_validate(concluded)
    assert "CTCAE grade, risk or Query conclusions" in str(exc.value)

    query_push = dict(base)
    query_push["user_action"] = "建议发起医学Query核对漏报。"
    with pytest.raises(ValidationError) as exc:
        service_module._FieldMappingItem.model_validate(query_push)
    assert "CTCAE grade, risk or Query conclusions" in str(exc.value)


def test_service_reconciliation_refuses_cohorts_mapped_on_different_inputs() -> None:
    """Dual-cohort input validation: agreement only counts on one frozen input.

    The primary and verifier cohorts must carry the same
    ``input_revision_sha256`` — the digest that binds the field profile,
    its sources and the frozen relationship evidence. Diverging revisions
    mean the cohorts did not see identical inputs and must never reconcile.
    """

    from datetime import datetime, timezone

    from packages.medical_monitoring.admission.mapping_confirmation import (
        MONITORING_C3_VERIFIER_PROMPT_VERSION,
    )

    now = datetime.now(timezone.utc)

    def _job(job_id: str, revision: str, prompt: str, provider: str, model: str):
        return SimpleNamespace(
            job_id=job_id,
            status="completed",
            prompt_version=prompt,
            input_revision_sha256=revision,
            created_at=now,
            provider=provider,
            requested_model=model,
        )

    primary_jobs = (
        _job(
            "primary-1",
            "rev-a",
            "monitoring-listing-field-mapping-v19",
            "cms-smk",
            "MiniMax-M3",
        ),
    )
    verifier_jobs = (
        _job(
            "verifier-1",
            "rev-b",
            MONITORING_C3_VERIFIER_PROMPT_VERSION,
            "zhipu-coding-plan",
            "glm-5.3-flash",
        ),
    )

    class Draft:
        batch_id = "attempt-1"
        draft_id = "draft-1"
        version = 1

        def model_dump(self, mode="json"):
            return {
                "project_id": "p1",
                "draft_id": self.draft_id,
                "batch_id": self.batch_id,
                "version": self.version,
                "fields": DRAFT_FIELDS,
            }

    quality = SimpleNamespace(as_payload=lambda: {"confirmable": True})

    def _list_jobs(_project, *args, task_type="", business_key_prefix=""):
        if business_key_prefix.startswith("listing-field-mapping:"):
            return primary_jobs
        return verifier_jobs

    repo = SimpleNamespace(
        get_draft=lambda *_args: Draft(),
        semantic_quality=lambda *_args: quality,
    )
    ai_repo = SimpleNamespace(
        list_jobs=_list_jobs,
        candidates=lambda *_args: (
            SimpleNamespace(
                candidate_id="cand-1",
                evidence=(),
                structured_payload={"field_mappings": []},
            ),
        ),
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=ai_repo,
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
    )

    with pytest.raises(AdmissionMappingPipelineError) as exc:
        service.reconcile_with_verifier(
            project_id="p1",
            attempt_id="attempt-1",
            draft_id="draft-1",
            workspace_dir=None,
        )
    assert exc.value.code == "mapping_cohort_input_mismatch"
