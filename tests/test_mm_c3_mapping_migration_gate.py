"""Synthetic migration-gate tests for the C3 dual-cohort mapping pipeline.

These tests pin the P0 migration contract without any real project:

1. The paused legacy single-GLM cohort (verifier identity executing inside
   the primary job namespace, for example the RUX run) can never assemble a
   new mapping draft.
2. A local-fallback first pass is truthfully labeled and can never back a
   dual-model pass, even when the verifier cohort agrees with it.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from packages.medical_monitoring.admission.mapping_confirmation import (
    AdmissionMappingConfirmationService,
)
from packages.medical_monitoring.admission.mapping_gate import (
    MONITORING_C3_ALTERNATE_MODEL,
    MONITORING_C3_ALTERNATE_PROVIDER,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_SYSTEM_ONLY,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_UNRECOGNIZED,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER,
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROMPT_VERSION,
    MONITORING_C3_VERIFIER_PROVIDER,
    monitoring_mapping_cohort_dual_model_eligible,
    monitoring_mapping_execution_route,
)
from packages.medical_monitoring.admission.mapping_pipeline import (
    AdmissionMappingPipelineError,
)
from packages.medical_monitoring.admission.mapping_reconciliation import (
    reconcile_mapping_cohorts,
)
from packages.medical_monitoring.api.r7_product.mapping_candidate_routes import (
    _mapping_error,
)


DETERMINISTIC_IDENTITY = ("workbench-system", "deterministic-metadata-mapping-v1")


def test_execution_route_classification_covers_all_gate_routes() -> None:
    assert (
        monitoring_mapping_execution_route(
            MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL
        )
        == MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
    )
    # The alternate transport identity is still a remote primary route.
    assert (
        monitoring_mapping_execution_route(
            MONITORING_C3_ALTERNATE_PROVIDER, MONITORING_C3_ALTERNATE_MODEL
        )
        == MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
    )
    assert (
        monitoring_mapping_execution_route(
            MONITORING_C3_MAPPING_PROVIDER, "minimax-m3"
        )
        == MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
    )
    assert (
        monitoring_mapping_execution_route(
            "mtplx", "mtplx-flash-next-optimized-speed"
        )
        == MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK
    )
    # The verifier identity is recognized regardless of historical case.
    assert (
        monitoring_mapping_execution_route(
            MONITORING_C3_VERIFIER_PROVIDER, "GLM-5.3-FLASH"
        )
        == MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER
    )
    assert (
        monitoring_mapping_execution_route("deepseek", "deepseek-v4-flash")
        == MONITORING_C3_MAPPING_EXECUTION_ROUTE_UNRECOGNIZED
    )
    assert (
        monitoring_mapping_execution_route("", "")
        == MONITORING_C3_MAPPING_EXECUTION_ROUTE_UNRECOGNIZED
    )


def test_only_remote_primary_routes_back_a_dual_model_pass() -> None:
    assert (
        monitoring_mapping_cohort_dual_model_eligible(
            [MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY]
        )
        is True
    )
    # A local-fallback first pass can never masquerade as dual-model pass.
    assert (
        monitoring_mapping_cohort_dual_model_eligible(
            [MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK]
        )
        is False
    )
    assert (
        monitoring_mapping_cohort_dual_model_eligible(
            [
                MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY,
                MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK,
            ]
        )
        is False
    )
    # No executed LLM route at all: nothing to confirm dual-model-wise.
    assert (
        monitoring_mapping_cohort_dual_model_eligible(
            [MONITORING_C3_MAPPING_EXECUTION_ROUTE_SYSTEM_ONLY]
        )
        is False
    )
    assert monitoring_mapping_cohort_dual_model_eligible([]) is False


def _job(provider: str, model: str, *, job_id: str, created_at: int = 0):
    return SimpleNamespace(
        job_id=job_id,
        project_id="p1",
        prompt_version="prompt",
        input_revision_sha256="r" * 64,
        status="completed",
        provider=provider,
        requested_model=model,
        created_at=created_at,
    )


def _assembling_repository(deterministic_allowed: bool):
    """AI repository + mapping repository fakes for ``adopt_draft``."""

    jobs = [
        _job(
            MONITORING_C3_MAPPING_PROVIDER,
            MONITORING_C3_MAPPING_MODEL,
            job_id="job-minimax-1",
        ),
        _job(*DETERMINISTIC_IDENTITY, job_id="job-det-1"),
    ]
    decided = []

    def _must_not_assemble(*_args, **_kwargs):
        raise AssertionError("a blocked cohort must never assemble a draft")

    ai_repository = SimpleNamespace(
        list_jobs=lambda *_args, **_kwargs: tuple(jobs),
        input_payload=lambda *_args: {
            "field_profile": {"full_profile_sha256": "a" * 64}
        },
        candidates=lambda *_args: (
            SimpleNamespace(candidate_id="cand-1", status="proposed"),
        ),
        decide_candidate=lambda *_args, **kwargs: decided.append(kwargs),
    )
    draft = SimpleNamespace(
        model_dump=lambda mode="json": {
            "project_id": "p1",
            "draft_id": "draft-1",
            "batch_id": "attempt-1",
            "version": 1,
            "fields": [],
        }
    )
    mapping_repository = SimpleNamespace(
        assemble=lambda *_args, **_kwargs: draft,
        semantic_quality=lambda *_args: SimpleNamespace(
            as_payload=lambda: {"confirmable": True}
        ),
    )
    system_routes = (DETERMINISTIC_IDENTITY,) if deterministic_allowed else ()
    return ai_repository, mapping_repository, system_routes, decided


def _confirmation_service(
    ai_repository,
    mapping_repository,
    system_routes=(),
    *,
    pipeline=None,
):
    return AdmissionMappingConfirmationService(
        mapping_pipeline=(
            pipeline
            or SimpleNamespace(
                list_candidates=lambda **_kwargs: {
                    "state": "candidates_ready",
                    "candidates": [],
                    "jobs": [],
                }
            )
        ),
        mapping_repository=mapping_repository,
        ai_repository=ai_repository,
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
        task_type="listing_semantic_mapping",
        current_revision_resolver=lambda _repo, job, **_kwargs: str(
            job.input_revision_sha256
        ),
        system_routes=system_routes,
    )


def test_adopt_draft_assembles_remote_primary_cohort_and_labels_it() -> None:
    ai_repository, mapping_repository, system_routes, decided = (
        _assembling_repository(deterministic_allowed=True)
    )
    payload = _confirmation_service(
        ai_repository, mapping_repository, system_routes
    ).adopt_draft(
        project_id="p1",
        attempt_id="attempt-1",
        workspace_dir="/generated/non-real",
        actor="tester",
        reason="重新生成后整体采纳。",
    )

    execution = payload["first_pass_execution"]
    assert execution == {
        "route": MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY,
        "adoptable": True,
        "dual_model_eligible": True,
        "providers": [MONITORING_C3_MAPPING_PROVIDER],
    }
    assert decided


def test_legacy_glm_cohort_can_never_enter_a_new_draft() -> None:
    # The paused RUX cohort shape: every primary-namespace job executed on
    # the verifier identity under the old single-model route.
    def _blocked_case(jobs, system_routes=()):
        ai_repository = SimpleNamespace(
            list_jobs=lambda *_args, **_kwargs: tuple(jobs),
            input_payload=lambda *_args: {
                "field_profile": {"full_profile_sha256": "a" * 64}
            },
            candidates=lambda *_args: (
                SimpleNamespace(candidate_id="cand-1", status="proposed"),
            ),
            decide_candidate=lambda *_args, **_kwargs: None,
        )
        mapping_repository = SimpleNamespace(
            assemble=lambda *_args, **_kwargs: (
                AssertionError("assemble must not run")
            ),
        )
        return ai_repository, mapping_repository, system_routes

    legacy_jobs = [
        _job(
            MONITORING_C3_VERIFIER_PROVIDER,
            MONITORING_C3_VERIFIER_MODEL,
            job_id="job-glm-1",
        ),
        _job(*DETERMINISTIC_IDENTITY, job_id="job-det-1"),
    ]
    ai_repository, mapping_repository, system_routes = _blocked_case(
        legacy_jobs, (DETERMINISTIC_IDENTITY,)
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        _confirmation_service(
            ai_repository, mapping_repository, system_routes
        ).adopt_draft(
            project_id="p1",
            attempt_id="attempt-1",
            workspace_dir="/generated/non-real",
            actor="tester",
            reason="恢复 RUX 尝试。",
        )
    assert exc.value.code == "mapping_cohort_legacy_route"

    # A mixed cohort (new primary + leftover legacy GLM jobs sharing the
    # same prompt version and input revision) is equally fail-closed.
    mixed_jobs = [
        _job(
            MONITORING_C3_MAPPING_PROVIDER,
            MONITORING_C3_MAPPING_MODEL,
            job_id="job-minimax-1",
        ),
        _job(
            MONITORING_C3_VERIFIER_PROVIDER,
            MONITORING_C3_VERIFIER_MODEL,
            job_id="job-glm-1",
        ),
    ]
    ai_repository, mapping_repository, system_routes = _blocked_case(
        mixed_jobs, (DETERMINISTIC_IDENTITY,)
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        _confirmation_service(
            ai_repository, mapping_repository, system_routes
        ).adopt_draft(
            project_id="p1",
            attempt_id="attempt-1",
            workspace_dir="/generated/non-real",
            actor="tester",
            reason="混合 cohort 拒绝。",
        )
    assert exc.value.code == "mapping_cohort_legacy_route"

    # Unrecognized executions are unverifiable and equally blocked.
    unknown_jobs = [
        _job("deepseek", "deepseek-v4-flash", job_id="job-unknown-1"),
    ]
    ai_repository, mapping_repository, system_routes = _blocked_case(
        unknown_jobs
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        _confirmation_service(
            ai_repository, mapping_repository
        ).adopt_draft(
            project_id="p1",
            attempt_id="attempt-1",
            workspace_dir="/generated/non-real",
            actor="tester",
            reason="未知路由拒绝。",
        )
    assert exc.value.code == "mapping_cohort_legacy_route"


def test_deterministic_jobs_require_configured_system_routes() -> None:
    # Fail-closed default: a deployment that does not declare the
    # deterministic system identity cannot adopt a cohort containing it.
    ai_repository, mapping_repository, _, _ = _assembling_repository(
        deterministic_allowed=True
    )
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        _confirmation_service(ai_repository, mapping_repository).adopt_draft(
            project_id="p1",
            attempt_id="attempt-1",
            workspace_dir="/generated/non-real",
            actor="tester",
            reason="未注入系统路由。",
        )
    assert exc.value.code == "mapping_cohort_legacy_route"


def test_fallback_cohort_is_adoptable_but_labeled_and_ineligible() -> None:
    jobs = [
        _job("mtplx", "mtplx-flash-next-optimized-speed", job_id="job-fb-1"),
        _job(*DETERMINISTIC_IDENTITY, job_id="job-det-1"),
    ]
    decided = []
    ai_repository = SimpleNamespace(
        list_jobs=lambda *_args, **_kwargs: tuple(jobs),
        input_payload=lambda *_args: {
            "field_profile": {"full_profile_sha256": "a" * 64}
        },
        candidates=lambda *_args: (
            SimpleNamespace(candidate_id="cand-1", status="proposed"),
        ),
        decide_candidate=lambda *_args, **kwargs: decided.append(kwargs),
    )
    draft = SimpleNamespace(
        model_dump=lambda mode="json": {
            "project_id": "p1",
            "draft_id": "draft-1",
            "batch_id": "attempt-1",
            "version": 1,
            "fields": [],
        }
    )
    mapping_repository = SimpleNamespace(
        assemble=lambda *_args, **_kwargs: draft,
        semantic_quality=lambda *_args: SimpleNamespace(
            as_payload=lambda: {"confirmable": True}
        ),
    )
    payload = _confirmation_service(
        ai_repository,
        mapping_repository,
        (DETERMINISTIC_IDENTITY,),
    ).adopt_draft(
        project_id="p1",
        attempt_id="attempt-1",
        workspace_dir="/generated/non-real",
        actor="tester",
        reason="远端路由不可用期间的降级执行。",
    )

    assert payload["first_pass_execution"] == {
        "route": MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK,
        "adoptable": True,
        "dual_model_eligible": False,
        "providers": ["mtplx"],
    }
    assert decided


def test_list_for_review_marks_legacy_cohort_without_raising() -> None:
    payload = {
        "state": "candidates_ready",
        "candidates": [],
        "jobs": [
            {
                "status": "completed",
                "provider": MONITORING_C3_VERIFIER_PROVIDER,
                "requested_model": MONITORING_C3_VERIFIER_MODEL,
            },
        ],
    }
    pipeline = SimpleNamespace(
        list_candidates=lambda **_kwargs: payload,
    )
    service = _confirmation_service(
        SimpleNamespace(), None, pipeline=pipeline
    )
    projected = service.list_for_review(
        project_id="p1",
        attempt_id="attempt-1",
        workspace_dir=None,
    )
    execution = projected["first_pass_execution"]
    assert execution["route"] == MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER
    assert execution["adoptable"] is False
    assert execution["dual_model_eligible"] is False


def test_list_for_review_labels_fallback_cohort() -> None:
    payload = {
        "state": "candidates_ready",
        "candidates": [],
        "jobs": [
            {
                "status": "completed",
                "provider": "mtplx",
                "requested_model": "mtplx-flash-next-optimized-speed",
            },
        ],
    }
    pipeline = SimpleNamespace(list_candidates=lambda **_kwargs: payload)
    service = _confirmation_service(SimpleNamespace(), None, pipeline=pipeline)
    projected = service.list_for_review(
        project_id="p1",
        attempt_id="attempt-1",
        workspace_dir=None,
    )
    execution = projected["first_pass_execution"]
    assert (
        execution["route"]
        == MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK
    )
    assert execution["adoptable"] is True
    assert execution["dual_model_eligible"] is False


def _profile_field(domain="AE", field="AETERM"):
    return [{"domain": domain, "field": field}]


def _mapping(domain="AE", field="AETERM", role="ae_term", kind="source_collected"):
    return {
        "domain": domain,
        "source_field": field,
        "recommended_role": role,
        "field_kind": kind,
        "confidence": 0.99,
        "evidence_ids": ["ev-1"],
    }


def test_full_agreement_with_fallback_primary_is_never_a_dual_model_pass() -> None:
    report = reconcile_mapping_cohorts(
        profile_fields=_profile_field(),
        primary_mappings=[_mapping()],
        verifier_mappings=[_mapping()],
        primary_evidence_ids={"ev-1"},
        verifier_evidence_ids={"ev-1"},
        primary_execution_route=(
            MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK
        ),
    )
    # Both cohorts agree, but the first pass ran on the local fallback:
    # the agreement must stay visible while never claiming a dual-model pass.
    assert report["state"] == "agreed"
    assert report["primary_execution_route"] == (
        MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK
    )
    assert report["dual_model_pass"] is False
    assert report["auto_pass"] is False


def test_default_route_keeps_the_documented_auto_pass_contract() -> None:
    report = reconcile_mapping_cohorts(
        profile_fields=_profile_field(),
        primary_mappings=[_mapping()],
        verifier_mappings=[_mapping()],
        primary_evidence_ids={"ev-1"},
        verifier_evidence_ids={"ev-1"},
    )
    assert report["state"] == "agreed"
    assert report["dual_model_pass"] is True
    assert report["auto_pass"] is True


def test_service_reconciliation_honors_the_fallback_route() -> None:
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
                "fields": [
                    {
                        "domain": "AE",
                        "source_field": "AETERM",
                        "recommended_role": "ae_term",
                        "field_kind": "source_collected",
                        "confidence": 0.99,
                        "evidence_ids": ["ev-1"],
                    },
                ],
            }

    repo = SimpleNamespace(
        get_draft=lambda *_args: Draft(),
        semantic_quality=lambda *_args: SimpleNamespace(
            as_payload=lambda: {"confirmable": True}
        ),
    )
    verifier_candidate = SimpleNamespace(
        candidate_id="verifier-cand-1",
        evidence=[SimpleNamespace(evidence_id="ev-glm-1")],
        structured_payload={
            "field_mappings": [
                {
                    "domain": "AE",
                    "source_field": "AETERM",
                    "recommended_role": "ae_term",
                    "field_kind": "source_collected",
                    "confidence": 0.98,
                    "evidence_ids": ["ev-glm-1"],
                },
            ],
        },
    )
    service = AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(),
        mapping_repository=repo,
        ai_repository=SimpleNamespace(),
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
    )
    payload = service.reconcile_with_verifier(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        verifier_candidates=[verifier_candidate],
        primary_execution_route=(
            MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK
        ),
    )
    reconciliation = payload["reconciliation"]
    assert reconciliation["state"] == "agreed"
    assert reconciliation["dual_model_pass"] is False
    assert reconciliation["auto_pass"] is False


def test_legacy_route_error_is_actionable_for_users() -> None:
    response = _mapping_error("mapping_cohort_legacy_route")

    assert response.status_code == 409
    body = response.body.decode("utf-8")
    assert "字段识别结果已过期" in body
    assert "重新识别" in body
    assert "点击重试" in body


def test_reconciliation_errors_do_not_ask_user_for_bulk_review() -> None:
    pending = _mapping_error("mapping_verifier_incomplete")
    diverged = _mapping_error("mapping_reconciliation_required")

    assert pending.status_code == diverged.status_code == 409
    assert "不需要您确认" in pending.body.decode("utf-8")
    assert "不需要您逐项确认" in diverged.body.decode("utf-8")


def _dual_confirmation_service(verifier_role: str):
    primary_job = _job(
        MONITORING_C3_MAPPING_PROVIDER,
        MONITORING_C3_MAPPING_MODEL,
        job_id="job-primary",
    )
    verifier_job = _job(
        MONITORING_C3_VERIFIER_PROVIDER,
        MONITORING_C3_VERIFIER_MODEL,
        job_id="job-verifier",
    )
    verifier_job.prompt_version = MONITORING_C3_VERIFIER_PROMPT_VERSION

    def candidate(job_id: str):
        role = "ae_term" if job_id == "job-primary" else verifier_role
        evidence_id = "ev-primary" if job_id == "job-primary" else "ev-verifier"
        return SimpleNamespace(
            candidate_id=f"candidate-{job_id}",
            evidence=[SimpleNamespace(evidence_id=evidence_id)],
            structured_payload={
                "field_mappings": [
                    {
                        **_mapping(role=role),
                        "evidence_ids": [evidence_id],
                    }
                ]
            },
        )

    ai_repository = SimpleNamespace(
        list_jobs=lambda *_args, **kwargs: (
            (verifier_job,)
            if "verifier" in kwargs.get("business_key_prefix", "")
            else (primary_job,)
        ),
        candidates=lambda _project_id, job_id: (candidate(job_id),),
    )

    class Draft:
        batch_id = "attempt-1"
        draft_id = "draft-1"
        version = 1

        def model_dump(self, mode="json"):
            return {
                "project_id": "p1",
                "batch_id": self.batch_id,
                "draft_id": self.draft_id,
                "version": self.version,
                "fields": [
                    {
                        **_mapping(),
                        "evidence_ids": ["ev-primary"],
                    }
                ],
            }

    draft = Draft()
    mapping_repository = SimpleNamespace(
        get_draft=lambda *_args: draft,
        semantic_quality=lambda *_args: SimpleNamespace(
            as_payload=lambda: {"confirmable": True}
        ),
        confirm=lambda *_args, **_kwargs: SimpleNamespace(
            model_dump=lambda mode="json": {
                "mapping_revision_id": "revision-1"
            }
        ),
    )
    return AdmissionMappingConfirmationService(
        mapping_pipeline=SimpleNamespace(_task_type="listing_semantic_mapping"),
        mapping_repository=mapping_repository,
        ai_repository=ai_repository,
        prompt_version="prompt",
        accepted_status="accepted",
        proposed_status="proposed",
        task_type="listing_semantic_mapping",
        require_dual_reconciliation=True,
    )


def test_confirmation_requires_and_accepts_repository_backed_dual_agreement() -> None:
    result = _dual_confirmation_service("ae_term").confirm_draft(
        project_id="p1",
        attempt_id="attempt-1",
        draft_id="draft-1",
        expected_version=1,
        confirmed_by="system_harness",
        confirmation_reason="两次独立分析一致。",
        idempotency_key="confirm-dual-1",
    )

    assert result["mapping_revision_id"] == "revision-1"


def test_confirmation_blocks_dual_disagreement_before_revision() -> None:
    with pytest.raises(AdmissionMappingPipelineError) as exc:
        _dual_confirmation_service("ae_term_text").confirm_draft(
            project_id="p1",
            attempt_id="attempt-1",
            draft_id="draft-1",
            expected_version=1,
            confirmed_by="system_harness",
            confirmation_reason="两次独立分析存在差异。",
            idempotency_key="confirm-dual-2",
        )

    assert exc.value.code == "mapping_reconciliation_required"
