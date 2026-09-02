"""Durable draft adopt/edit/confirm over C3 admission mapping candidates.

Candidate generation stays in ``AdmissionMappingPipeline``. This module only
bridges completed candidates into the existing mapping-draft authority and
never materializes canonical facts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional

from .mapping_pipeline import AdmissionMappingPipelineError, current_admission_mapping_revision


LOW_CONFIDENCE_THRESHOLD = 0.85
_FOCUS_CRITICAL = "critical"
_FOCUS_ALL = "all"
_ALLOWED_FOCUS = frozenset({_FOCUS_CRITICAL, _FOCUS_ALL})
_MEDICATION_ROLE = re.compile(
    r"(^|[._-])(ip|cm|dose|dosing|adherence|compliance)([._-]|$)"
)


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


def attention_reason(item: Mapping[str, Any]) -> str:
    role = str(item.get("recommended_role") or "").lower()
    kind = str(item.get("field_kind") or "").strip()
    if not str(item.get("user_action") or "").strip():
        return "建议不完整"
    try:
        confidence = float(item.get("confidence"))
    except (TypeError, ValueError):
        confidence = 1.0
    if kind == "unmapped":
        return "暂未映射"
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return "低置信度"
    if _MEDICATION_ROLE.search(role):
        return "用药边界"
    if kind == "standardized_coded":
        return "编码依据"
    if kind == "deterministic_derived":
        return "派生依据"
    return ""


def enrich_candidates(
    payload: Mapping[str, Any],
    *,
    focus: str = _FOCUS_CRITICAL,
) -> dict[str, Any]:
    focus_key = str(focus or _FOCUS_CRITICAL).strip().lower() or _FOCUS_CRITICAL
    if focus_key not in _ALLOWED_FOCUS:
        raise AdmissionMappingPipelineError("mapping_focus_invalid")
    candidates = []
    critical_count = 0
    for raw in list(payload.get("candidates") or []):
        if not isinstance(raw, Mapping):
            continue
        reason = attention_reason(raw)
        row = dict(raw)
        row["attention_reason"] = reason
        row["needs_attention"] = bool(reason)
        if reason:
            critical_count += 1
        if focus_key == _FOCUS_ALL or reason:
            candidates.append(row)
    summary = dict(payload.get("summary") or {})
    summary["critical_count"] = critical_count
    summary["displayed_count"] = len(candidates)
    summary["focus"] = focus_key
    return {
        **dict(payload),
        "summary": summary,
        "candidates": candidates,
        "facts_generated": False,
        "candidate_fact_boundary": "candidates_only",
    }


@dataclass
class AdmissionMappingConfirmationService:
    """Adopt/edit/confirm using the durable mapping-draft repository."""

    mapping_pipeline: Any
    mapping_repository: Any
    ai_repository: Any
    prompt_version: str
    accepted_status: Any
    proposed_status: Any
    task_type: Any = None
    current_revision_resolver: Optional[Callable[..., str]] = None

    def list_for_review(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
        focus: str = _FOCUS_CRITICAL,
    ) -> Mapping[str, Any]:
        payload = self.mapping_pipeline.list_candidates(
            project_id=project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        return enrich_candidates(payload, focus=focus)

    def adopt_draft(
        self,
        *,
        project_id: str,
        attempt_id: str,
        workspace_dir: Any,
        actor: str,
        reason: str,
    ) -> Mapping[str, Any]:
        if self.mapping_repository is None or self.ai_repository is None:
            raise AdmissionMappingPipelineError("mapping_draft_unconfigured")
        payload = self.mapping_pipeline.list_candidates(
            project_id=project_id,
            attempt_id=attempt_id,
            workspace_dir=workspace_dir,
        )
        if payload.get("state") != "candidates_ready":
            raise AdmissionMappingPipelineError("mapping_run_incomplete")
        task_type = self.task_type
        if task_type is None:
            task_type = getattr(self.mapping_pipeline, "_task_type", "")
        jobs = self.ai_repository.list_jobs(
            project_id,
            task_type=str(_value(task_type)),
            business_key_prefix=f"listing-field-mapping:{attempt_id}:",
        )
        if not jobs:
            raise AdmissionMappingPipelineError("mapping_candidates_not_found")
        profile_sha = ""
        for job in jobs:
            input_payload = self.ai_repository.input_payload(project_id, job.job_id)
            profile = input_payload.get("field_profile") or {}
            digest = str(profile.get("full_profile_sha256") or "").strip()
            if not digest:
                raise AdmissionMappingPipelineError("mapping_bridge_failed")
            if profile_sha and profile_sha != digest:
                raise AdmissionMappingPipelineError("mapping_bridge_failed")
            profile_sha = digest
            if str(job.prompt_version) != str(self.prompt_version):
                raise AdmissionMappingPipelineError("mapping_run_incomplete")
            if str(_value(job.status)) != "completed":
                raise AdmissionMappingPipelineError("mapping_run_incomplete")
            candidates = self.ai_repository.candidates(project_id, job.job_id)
            if len(candidates) != 1:
                raise AdmissionMappingPipelineError("mapping_bridge_failed")
            candidate = candidates[0]
            status = _value(candidate.status)
            if status == _value(self.proposed_status):
                revision = self._revision_for_job(job, workspace_dir=workspace_dir)
                self.ai_repository.decide_candidate(
                    project_id,
                    candidate.candidate_id,
                    decision=self.accepted_status,
                    actor=actor,
                    reason=reason,
                    current_input_revision_sha256=revision,
                )
            elif status != _value(self.accepted_status):
                raise AdmissionMappingPipelineError("mapping_candidate_not_adoptable")
        draft = self.mapping_repository.assemble(
            project_id,
            attempt_id,
            profile_sha,
            prompt_version=self.prompt_version,
        )
        return self._draft_payload(draft)

    def edit_field(
        self,
        *,
        project_id: str,
        attempt_id: str,
        draft_id: str,
        domain: str,
        source_field: str,
        patch: Mapping[str, Any],
        expected_version: int,
        actor: str,
        idempotency_key: str,
    ) -> Mapping[str, Any]:
        if self.mapping_repository is None:
            raise AdmissionMappingPipelineError("mapping_draft_unconfigured")
        self._require_attempt_draft(project_id, attempt_id, draft_id)
        draft = self.mapping_repository.edit_field(
            project_id,
            draft_id,
            domain=domain,
            source_field=source_field,
            patch=dict(patch),
            expected_version=expected_version,
            actor=actor,
            idempotency_key=idempotency_key,
        )
        return self._draft_payload(draft)

    def confirm_draft(
        self,
        *,
        project_id: str,
        attempt_id: str,
        draft_id: str,
        expected_version: int,
        confirmed_by: str,
        confirmation_reason: str,
        idempotency_key: str,
    ) -> Mapping[str, Any]:
        if self.mapping_repository is None:
            raise AdmissionMappingPipelineError("mapping_draft_unconfigured")
        draft = self._require_attempt_draft(project_id, attempt_id, draft_id)
        payload = draft.model_dump(mode="json") if hasattr(draft, "model_dump") else dict(draft)
        if any(
            not str(field.get("user_action") or "").strip()
            for field in payload.get("fields") or []
        ):
            raise AdmissionMappingPipelineError("mapping_advice_incomplete")
        revision = self.mapping_repository.confirm(
            project_id,
            draft_id,
            expected_version=expected_version,
            confirmed_by=confirmed_by,
            confirmation_reason=confirmation_reason,
            idempotency_key=idempotency_key,
        )
        payload = revision.model_dump(mode="json")
        # Confirmation creates a durable mapping revision only. Canonical facts
        # remain a later deterministic step outside this product entry.
        payload["facts_generated"] = False
        payload["next_action"] = "generate_facts_later"
        payload["confirmation_status"] = "confirmed"
        return payload

    def _revision_for_job(self, job: Any, *, workspace_dir: Any) -> str:
        if self.current_revision_resolver is not None:
            return str(
                self.current_revision_resolver(
                    self.ai_repository,
                    job,
                    workspace_dir=workspace_dir,
                )
                or ""
            )
        resolved = current_admission_mapping_revision(
            self.ai_repository,
            job,
            workspace_dir=workspace_dir,
        )
        if resolved is None:
            return str(job.input_revision_sha256)
        return str(resolved)

    def _require_attempt_draft(
        self, project_id: str, attempt_id: str, draft_id: str
    ) -> Any:
        draft = self.mapping_repository.get_draft(project_id, draft_id)
        if str(draft.batch_id) != str(attempt_id):
            raise AdmissionMappingPipelineError("mapping_draft_conflict")
        return draft

    def _draft_payload(self, draft: Any) -> dict[str, Any]:
        if hasattr(draft, "model_dump"):
            payload = draft.model_dump(mode="json")
        else:
            payload = dict(draft)
        quality = self.mapping_repository.semantic_quality(
            payload["project_id"],
            payload["draft_id"],
        )
        critical_count = 0
        for field in payload.get("fields") or []:
            reason = attention_reason(field)
            field["attention_reason"] = reason
            field["needs_attention"] = bool(reason)
            critical_count += bool(reason)
        payload["semantic_quality"] = quality.as_payload()
        payload["review_summary"] = {
            "field_count": len(payload.get("fields") or []),
            "critical_count": critical_count,
        }
        payload["facts_generated"] = False
        payload["candidate_fact_boundary"] = "draft_only"
        return payload


__all__ = [
    "AdmissionMappingConfirmationService",
    "LOW_CONFIDENCE_THRESHOLD",
    "attention_reason",
    "enrich_candidates",
]
