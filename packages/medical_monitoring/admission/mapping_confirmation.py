"""Medical-question triage over C3 admission mapping candidates.

Candidate generation stays in ``AdmissionMappingPipeline``. This module only
projects completed candidates for review and gates durable confirmation. The
system adopts every basically-sound candidate on its own; only medically
substantive ambiguities — the ones that would change monitoring analysis
results — become visible Chinese questions for the user. Nothing here ever
materializes canonical facts.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Callable, Mapping, Optional

from .mapping_pipeline import (
    AdmissionMappingPipelineError,
    _latest_job_cohort,
    current_admission_mapping_revision,
)


LOW_CONFIDENCE_THRESHOLD = 0.85
_FOCUS_CRITICAL = "critical"
_FOCUS_ALL = "all"
_ALLOWED_FOCUS = frozenset({_FOCUS_CRITICAL, _FOCUS_ALL})

USER_QUESTION_UNMAPPED = "unmapped_field"
USER_QUESTION_MODEL_FLAGGED = "model_flagged"
USER_QUESTION_LOW_CONFIDENCE = "low_confidence"
USER_QUESTION_MISSING_ADVICE = "missing_advice"

_QUESTION_LABELS = {
    USER_QUESTION_UNMAPPED: "暂未映射",
    USER_QUESTION_MODEL_FLAGGED: "需医学确认",
    USER_QUESTION_LOW_CONFIDENCE: "低置信度",
    USER_QUESTION_MISSING_ADVICE: "建议缺失",
}

# A human decision marker inside ``user_action`` records the medical manager's
# answer to a question card. The marker survives into the confirmed revision,
# so an answered question is auditable without a separate answer store.
_DECISION_PREFIXES = (
    "用户已确认：",
    "用户已核对：",
)
_SYSTEM_ADJUDICATION_PREFIX = "系统复核："

_TRIAGE_QUESTION = "user_question"
_TRIAGE_ADOPTED = "system_adopted"


def _confidence(item: Mapping[str, Any]) -> float:
    try:
        return float(item.get("confidence"))
    except (TypeError, ValueError):
        # An unreadable confidence must never count as "basically sound".
        return 0.0


def _model_flag(item: Mapping[str, Any]) -> bool:
    flag = item.get("user_decision_required")
    if isinstance(flag, str):
        return flag.strip().casefold() in {"true", "1", "yes", "是"}
    return bool(flag)


def _decision_recorded(item: Mapping[str, Any]) -> bool:
    action = str(item.get("user_action") or "").strip()
    return action.startswith(_DECISION_PREFIXES)


def _question_label(domain: Any, source_field: Any) -> str:
    cleaned_domain = str(domain or "").strip()
    cleaned_field = str(source_field or "").strip()
    if cleaned_domain and cleaned_field:
        return f"「{cleaned_domain}·{cleaned_field}」"
    return f"「{cleaned_field or cleaned_domain}」"


def _question_text(code: str, item: Mapping[str, Any]) -> str:
    label = _question_label(item.get("domain"), item.get("source_field"))
    role = str(item.get("recommended_role") or "").strip()
    if code == USER_QUESTION_UNMAPPED:
        return (
            f"{label}还没有识别出对应的医学含义，它是否需要参与监查分析？"
            "如需要，请修订该字段的对应角色；如不需要，"
            "请在核对结论中注明「不纳入」。"
        )
    if code == USER_QUESTION_MODEL_FLAGGED:
        # The mapping contract requires a flagged candidate to phrase its
        # user_action as a concrete question, so it leads the card directly.
        flagged = str(item.get("user_action") or "").strip()
        uncertainty = str(item.get("uncertainty") or "").strip()
        detail = flagged or uncertainty[:200]
        if detail:
            return detail
        return f"请确认{label}记录的实际含义。"
    if code == USER_QUESTION_LOW_CONFIDENCE:
        return (
            f"{label}的识别把握不足，系统倾向于把它对应到「{role}」。"
            "请核对原始数据：如正确，请在核对结论中注明「已核对」；"
            "如不正确，请修订对应关系。"
        )
    return f"{label}缺少核对结论，请补充后再整体确认。"


def classify_user_question(
    item: Mapping[str, Any],
) -> Optional[dict[str, Any]]:
    """Return the one medical question a field still owes the user.

    ``None`` means the system adopts the candidate by itself: the mapping is
    basically sound and answering it would not change monitoring analysis.
    """

    # Confidence, an unmapped field, or incomplete advice is a system-quality
    # concern, not work to hand to a non-technical medical user. The provider
    # owns the sole escalation decision after considering full same-table
    # context; server validation requires a concrete Chinese question whenever
    # that flag is true.
    if not _model_flag(item) or _decision_recorded(item):
        return None
    code = USER_QUESTION_MODEL_FLAGGED
    return {
        "reason_code": code,
        "attention_reason": _QUESTION_LABELS[code],
        "question_text": _question_text(code, item),
    }


def attention_reason(item: Mapping[str, Any]) -> str:
    """Backward-compatible short label; empty when the system adopts."""

    question = classify_user_question(item)
    if question is None:
        return ""
    return str(question["attention_reason"])


def _question_card(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "domain": row.get("domain"),
        "source_field": row.get("source_field"),
        "recommended_role": row.get("recommended_role"),
        "field_kind": row.get("field_kind"),
        "confidence": row.get("confidence"),
        "reason_code": row.get("question_reason"),
        "attention_reason": row.get("attention_reason"),
        "question_text": row.get("question_text"),
        "evidence_summary": row.get("evidence_summary") or [],
    }


def _annotate(row: Mapping[str, Any]) -> tuple[dict[str, Any], Optional[dict[str, Any]]]:
    annotated = dict(row)
    question = classify_user_question(row)
    if question is None:
        annotated.update({
            "triage": _TRIAGE_ADOPTED,
            "system_adopted": True,
            "needs_attention": False,
            "attention_reason": "",
            "question_reason": "",
            "question_text": "",
        })
        return annotated, None
    annotated.update({
        "triage": _TRIAGE_QUESTION,
        "system_adopted": False,
        "needs_attention": True,
        "attention_reason": question["attention_reason"],
        "question_reason": question["reason_code"],
        "question_text": question["question_text"],
    })
    return annotated, _question_card(annotated)


def enrich_candidates(
    payload: Mapping[str, Any],
    *,
    focus: str = _FOCUS_CRITICAL,
) -> dict[str, Any]:
    focus_key = str(focus or _FOCUS_CRITICAL).strip().lower() or _FOCUS_CRITICAL
    if focus_key not in _ALLOWED_FOCUS:
        raise AdmissionMappingPipelineError("mapping_focus_invalid")
    candidates = []
    questions = []
    question_count = 0
    total_count = 0
    for raw in list(payload.get("candidates") or []):
        if not isinstance(raw, Mapping):
            continue
        total_count += 1
        row, question = _annotate(raw)
        if question is not None:
            question_count += 1
            questions.append(question)
        if focus_key == _FOCUS_ALL or question is not None:
            candidates.append(row)
    summary = dict(payload.get("summary") or {})
    summary["field_count"] = total_count
    summary["user_question_count"] = question_count
    summary["system_adopted_count"] = total_count - question_count
    # Backward-compatible aliases for surfaces not yet migrated to the
    # medical-question vocabulary.
    summary["critical_count"] = question_count
    summary["displayed_count"] = len(candidates)
    summary["focus"] = focus_key
    return {
        **dict(payload),
        "summary": summary,
        "user_questions": questions,
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
        projected = enrich_candidates(payload, focus=focus)
        if self.mapping_repository is None:
            return projected
        draft = self.mapping_repository.find_draft_for_batch(
            project_id,
            attempt_id,
        )
        if draft is None:
            return projected
        if str(_value(draft.status)) == "confirmed":
            projected["confirmation_status"] = "confirmed"
            projected["draft"] = {
                "draft_id": draft.draft_id,
                "version": draft.version,
                "status": "confirmed",
            }
            return projected
        projected["draft"] = self._draft_payload(draft)
        return projected

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
        jobs = _latest_job_cohort(jobs)
        profile_sha = ""
        profile_shas: dict[str, str] = {}
        current_revisions: dict[str, str] = {}
        for job in jobs:
            revision_key = str(job.input_revision_sha256)
            digest = profile_shas.get(revision_key, "")
            if not digest:
                input_payload = self.ai_repository.input_payload(
                    project_id,
                    job.job_id,
                )
                profile = input_payload.get("field_profile") or {}
                digest = str(profile.get("full_profile_sha256") or "").strip()
                if digest:
                    profile_shas[revision_key] = digest
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
                revision = current_revisions.get(revision_key)
                if revision is None:
                    revision = self._revision_for_job(
                        job,
                        workspace_dir=workspace_dir,
                    )
                    current_revisions[revision_key] = revision
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

    def adjudicate_draft(
        self,
        *,
        project_id: str,
        attempt_id: str,
        draft_id: str,
        workspace_dir: Any,
    ) -> Mapping[str, Any]:
        """Advance the focused second pass without creating facts."""

        draft = self._require_attempt_draft(project_id, attempt_id, draft_id)
        payload = (
            draft.model_dump(mode="json")
            if hasattr(draft, "model_dump")
            else dict(draft)
        )
        unresolved = [
            field
            for field in payload.get("fields") or []
            if classify_user_question(field) is not None
        ]
        result = self.mapping_pipeline.adjudicate_candidates(
            project_id=project_id,
            attempt_id=attempt_id,
            draft_id=draft_id,
            draft_fields=unresolved,
            workspace_dir=workspace_dir,
        )
        state = str(result.get("state") or "failed")
        if state != "ready":
            projected = self._draft_payload(draft)
            projected["adjudication"] = {
                "state": "complete" if state in {"failed", "not_needed"} else state,
                "resolved_count": 0,
                "remaining_question_count": len(unresolved),
            }
            return projected

        for job_id in {
            str(item.get("job_id") or "")
            for item in result.get("mappings") or []
            if str(item.get("job_id") or "")
        }:
            job = self.ai_repository.get(project_id, job_id)
            if self._revision_for_job(job, workspace_dir=workspace_dir) != str(
                job.input_revision_sha256
            ):
                raise AdmissionMappingPipelineError("mapping_run_incomplete")
            candidates = self.ai_repository.candidates(project_id, job_id)
            for candidate in candidates:
                status = _value(candidate.status)
                if status == _value(self.proposed_status):
                    self.ai_repository.decide_candidate(
                        project_id,
                        candidate.candidate_id,
                        decision=self.accepted_status,
                        actor="system_harness",
                        reason="已作为字段语义第二轮复核依据。",
                        current_input_revision_sha256=str(
                            job.input_revision_sha256
                        ),
                    )
                elif status != _value(self.accepted_status):
                    raise AdmissionMappingPipelineError(
                        "mapping_candidate_not_adoptable"
                    )

        first_pass = {
            (str(field.get("domain")), str(field.get("source_field"))): field
            for field in unresolved
        }
        resolved = 0
        for item in result.get("mappings") or []:
            pair = (
                str(item.get("domain") or ""),
                str(item.get("source_field") or ""),
            )
            original = first_pass.get(pair)
            rationale = str(item.get("user_action") or "").strip()
            if (
                original is None
                or _model_flag(item)
                or not rationale
                or "?" in rationale
                or "？" in rationale
                or str(item.get("recommended_role") or "").strip()
                != str(original.get("recommended_role") or "").strip()
                or str(_value(item.get("field_kind") or "")).strip()
                != str(_value(original.get("field_kind") or "")).strip()
            ):
                continue
            current = self.mapping_repository.get_draft(project_id, draft_id)
            current_payload = current.model_dump(mode="json")
            current_field = next(
                (
                    field
                    for field in current_payload.get("fields") or []
                    if (
                        str(field.get("domain")),
                        str(field.get("source_field")),
                    )
                    == pair
                ),
                None,
            )
            # A saved user answer always wins over a later system result.
            if current_field is None or classify_user_question(current_field) is None:
                continue
            uncertainty = str(item.get("uncertainty") or "").strip()
            operation_id = "adjudicate-" + hashlib.sha256(
                (
                    f"{draft_id}|{item.get('candidate_id')}|"
                    f"{pair[0]}|{pair[1]}"
                ).encode("utf-8")
            ).hexdigest()
            self.mapping_repository.edit_field(
                project_id,
                draft_id,
                domain=pair[0],
                source_field=pair[1],
                patch={
                    "user_decision_required": False,
                    "uncertainty": (
                        f"第二轮独立复核：{uncertainty or '当前证据支持原字段对应。'}"
                    ),
                    "user_action": f"{_SYSTEM_ADJUDICATION_PREFIX}{rationale}",
                },
                expected_version=int(current.version),
                actor="system_harness",
                idempotency_key=operation_id,
            )
            resolved += 1
        refreshed = self.mapping_repository.get_draft(project_id, draft_id)
        projected = self._draft_payload(refreshed)
        projected["adjudication"] = {
            "state": "complete",
            "resolved_count": resolved,
            "remaining_question_count": projected["review_summary"][
                "user_question_count"
            ],
        }
        return projected

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
        if _unresolved_question_count(payload.get("fields") or []):
            # Only medically substantive ambiguities block durable
            # confirmation; system-adopted candidates never do.
            raise AdmissionMappingPipelineError("mapping_questions_unresolved")
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
        fields = payload.get("fields") or []
        question_count = 0
        questions = []
        for index, field in enumerate(fields):
            annotated, question = _annotate(field)
            fields[index] = annotated
            if question is not None:
                question_count += 1
                questions.append(question)
        payload["semantic_quality"] = quality.as_payload()
        payload["user_questions"] = questions
        payload["review_summary"] = {
            "field_count": len(fields),
            "user_question_count": question_count,
            "system_adopted_count": len(fields) - question_count,
            "system_adjudicated_count": sum(
                str(field.get("user_action") or "").startswith(
                    _SYSTEM_ADJUDICATION_PREFIX
                )
                for field in fields
            ),
            # Backward-compatible alias for pre-triage surfaces.
            "critical_count": question_count,
        }
        payload["facts_generated"] = False
        payload["candidate_fact_boundary"] = "draft_only"
        return payload


def _unresolved_question_count(fields: Any) -> int:
    count = 0
    for field in fields:
        if classify_user_question(field) is not None:
            count += 1
    return count


def _value(value: Any) -> Any:
    return getattr(value, "value", value)


__all__ = [
    "AdmissionMappingConfirmationService",
    "LOW_CONFIDENCE_THRESHOLD",
    "USER_QUESTION_LOW_CONFIDENCE",
    "USER_QUESTION_MISSING_ADVICE",
    "USER_QUESTION_MODEL_FLAGGED",
    "USER_QUESTION_UNMAPPED",
    "attention_reason",
    "classify_user_question",
    "enrich_candidates",
]
