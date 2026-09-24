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
import json
import re
from typing import Any, Callable, Iterable, Mapping, Optional

from .mapping_gate import (
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_SYSTEM_ONLY,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_UNRECOGNIZED,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER,
    MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX,
    MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX,
    MONITORING_C3_VERIFIER_PROMPT_VERSION,
    monitoring_mapping_cohort_dual_model_eligible,
    monitoring_mapping_execution_route,
    normalize_monitoring_mapping_model,
)
from .mapping_pipeline import (
    AdmissionMappingPipelineError,
    MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS,
    _latest_job_cohort,
    current_admission_mapping_revision,
)
from .mapping_reconciliation import (
    RECONCILIATION_SCHEMA_VERSION,
    cohort_payload_from_candidates,
    reconcile_mapping_cohorts,
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

# Executed routes that may never assemble or back a draft: a verifier
# identity inside the primary namespace is the pre-dual-cohort (legacy
# GLM-primary) execution shape, and anything unrecognized is unverifiable.
_OFFENDING_EXECUTION_ROUTES = frozenset({
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER,
    MONITORING_C3_MAPPING_EXECUTION_ROUTE_UNRECOGNIZED,
})


def _adjudication_reconciliation_sha256(
    reconciliation: Mapping[str, Any],
    *, prompt_versions=None,
) -> str:
    """Bind a durable resolution to the evidence/prompt generation that made it."""

    return hashlib.sha256(
        json.dumps(
            {
                "reconciliation": reconciliation,
                "adjudication_prompt_versions": sorted(
                    MAPPING_ADJUDICATION_CURRENT_PROMPT_VERSIONS if prompt_versions is None else prompt_versions
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _effective_adjudication_receipts(
    receipts: Iterable[Any],
    reconciliation_sha256: str,
) -> dict[tuple[str, str], Any]:
    """Accept only current-evidence receipts with a supported resolution.

    Legacy primary-retained receipts remain history, not proof of agreement.
    Changed evidence requires a fresh review rather than inheriting a verdict.
    """

    selected: dict[tuple[str, str], Any] = {}
    for receipt in receipts:
        pair = (receipt.domain, receipt.source_field)
        if (
            receipt.reconciliation_sha256 == reconciliation_sha256
            and receipt.resolution in {
                "escalated", "adjudicated_mapping", "unverifiable_gap",
            }
        ):
            selected[pair] = receipt
    return selected


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


def _plain_medical_question(value: Any) -> str:
    """Hide source-system notation and evidence-retrieval chores from users."""

    question = str(value or "").strip()
    if not question:
        return ""
    question = re.sub(r"(?i)\b[A-Z][A-Z0-9_]{1,20}表", "", question)
    question = re.sub(r"(?i)[（(][A-Z][A-Z0-9_]{1,30}[）)]", "", question)
    question = re.sub(
        r"(?:请)?(?:依据|查看|查阅|核对)(?:CRF|电子病例报告表|"
        r"方案|研究者手册|IB|SAP)[^。！？!?]*[。！？!?]?",
        "",
        question,
        flags=re.IGNORECASE,
    )
    alternatives = re.search(
        r"([^，,。？?]{1,30}?)(?:列|记录)?(?:无法[^，,]{0,30})?"
        r"记录的是([^，,。？?]{1,30}?)还是([^，,。？?]{1,30}?)(?:，|,|。|？|\?)",
        question,
    )
    if alternatives:
        label, first, second = (
            re.sub(r"^(?:请确认)?", "", item).strip()
            for item in alternatives.groups()
        )
        return f"请确认：{label}记录的是{first}，还是{second}？"
    question = re.sub(r"(?:请)?(?:依据|查看|查阅|核对)[^。！？!?]*$", "", question)
    return question.strip(" ，,。")


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
        flagged = _plain_medical_question(item.get("user_action"))
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
        "prior_user_action": row.get("prior_user_action") or "",
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
    # (provider, model) identities of deterministic system-owned executions
    # (for example metadata-only mapping) allowed inside the primary job
    # namespace. They are route-neutral: they neither block nor satisfy the
    # dual-model contract. Empty keeps the gate fail-closed.
    system_routes: tuple[tuple[str, str], ...] = ()
    primary_runtime_resolver: Optional[Callable[[], Any]] = None
    require_dual_reconciliation: bool = False

    def __post_init__(self) -> None:
        self._system_route_set = {
            (
                str(provider or "").strip(),
                normalize_monitoring_mapping_model(str(model or "")).strip(),
            )
            for provider, model in (self.system_routes or ())
        }

    def _first_pass_execution(
        self,
        identities: Iterable[Any],
        *,
        block: bool,
    ) -> dict[str, Any]:
        """Classify the executed routes of one primary-namespace job cohort.

        With ``block`` the migration gate raises on verifier/unrecognized
        executions (a legacy single-verifier cohort shape) so they can never
        assemble a draft. Read-only projections use ``block=False`` and
        surface the offending route instead.
        """

        routes: list[str] = []
        providers: set[str] = set()
        offending: list[str] = []
        configured_primary = None
        if self.primary_runtime_resolver is not None:
            runtime = self.primary_runtime_resolver()
            if bool(getattr(runtime, "available", False)):
                configured_primary = (
                    str(getattr(runtime, "provider", "") or "").strip(),
                    normalize_monitoring_mapping_model(
                        str(getattr(runtime, "model", "") or "")
                    ).strip(),
                )
        for provider, model in identities:
            cleaned = (
                str(provider or "").strip(),
                normalize_monitoring_mapping_model(str(model or "")).strip(),
            )
            if cleaned in self._system_route_set:
                continue
            executed = (
                MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
                if configured_primary is not None and cleaned == configured_primary
                else monitoring_mapping_execution_route(*cleaned)
            )
            providers.add(cleaned[0])
            if executed in _OFFENDING_EXECUTION_ROUTES:
                offending.append(executed)
                continue
            routes.append(executed)
        if offending and block:
            raise AdmissionMappingPipelineError("mapping_cohort_legacy_route")
        if offending:
            route = (
                MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER
                if MONITORING_C3_MAPPING_EXECUTION_ROUTE_VERIFIER in offending
                else MONITORING_C3_MAPPING_EXECUTION_ROUTE_UNRECOGNIZED
            )
        elif not routes:
            route = MONITORING_C3_MAPPING_EXECUTION_ROUTE_SYSTEM_ONLY
        elif (
            MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK in routes
        ):
            route = MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY_FALLBACK
        else:
            route = MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
        return {
            "route": route,
            "adoptable": not offending,
            "dual_model_eligible": monitoring_mapping_cohort_dual_model_eligible(
                routes
            ),
            "providers": sorted(providers),
        }

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
        # Read-only execution-route projection: a legacy or fallback cohort
        # stays visible but is marked not adoptable / not dual-model eligible.
        projected["first_pass_execution"] = self._first_pass_execution(
            (
                (row.get("provider"), row.get("requested_model"))
                for row in payload.get("jobs") or ()
            ),
            block=False,
        )
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
            business_key_prefix=(
                f"{MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX}:{attempt_id}:"
            ),
        )
        if not jobs:
            raise AdmissionMappingPipelineError("mapping_candidates_not_found")
        jobs = _latest_job_cohort(jobs, repository=self.ai_repository)
        # Migration gate: the durable draft may only be assembled from the
        # new dual-cohort execution shapes. A verifier identity inside the
        # primary namespace is a legacy single-verifier cohort and must never
        # enter a new draft.
        first_pass_execution = self._first_pass_execution(
            ((job.provider, job.requested_model) for job in jobs),
            block=True,
        )
        profile_sha = ""
        profile_shas: dict[str, str] = {}
        current_revisions: dict[str, str] = {}
        candidate_acceptances: list[dict[str, str]] = []
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
                candidate_acceptances.append(
                    {
                        "candidate_id": str(candidate.candidate_id),
                        "job_id": str(job.job_id),
                        "input_revision_sha256": revision,
                    }
                )
            elif status != _value(self.accepted_status):
                raise AdmissionMappingPipelineError("mapping_candidate_not_adoptable")
            else:
                candidate_acceptances.append(
                    {
                        "candidate_id": str(candidate.candidate_id),
                        "job_id": str(job.job_id),
                        "input_revision_sha256": revision_key,
                    }
                )
        draft = self.mapping_repository.assemble(
            project_id,
            attempt_id,
            profile_sha,
            prompt_version=self.prompt_version,
            expected_job_ids=tuple(str(job.job_id) for job in jobs),
            candidate_acceptances=tuple(candidate_acceptances),
            decision_actor=actor,
            decision_reason=reason,
        )
        payload = self._draft_payload(draft)
        # Durable record of how the first pass actually ran: downstream
        # reconciliation reads this instead of re-deriving it, so a local
        # fallback run can never be presented as dual-model agreement.
        payload["first_pass_execution"] = first_pass_execution
        return payload

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
        reconciliation = None
        reconciliation_sha256 = ""
        divergence_pairs: set[tuple[str, str]] = set()
        existing_receipts: dict[tuple[str, str], Any] = {}
        previously_resolved = 0
        if self.require_dual_reconciliation:
            try:
                reconciliation = self.reconcile_with_verifier(
                    project_id=project_id,
                    attempt_id=attempt_id,
                    draft_id=draft_id,
                    workspace_dir=workspace_dir,
                )["reconciliation"]
            except AdmissionMappingPipelineError as exc:
                if exc.code != "mapping_verifier_incomplete":
                    raise
                projected = self._draft_payload(draft)
                projected["adjudication"] = {
                    "state": "running",
                    "resolved_count": 0,
                    "remaining_question_count": len(unresolved),
                }
                return projected
            if reconciliation["state"] == "blocked":
                projected = self._draft_payload(draft)
                projected["adjudication"] = {
                    "state": "blocked",
                    "resolved_count": 0,
                    "remaining_question_count": len(unresolved),
                }
                return projected
            reconciliation_sha256 = _adjudication_reconciliation_sha256(
                reconciliation, prompt_versions=getattr(self.mapping_pipeline, "adjudication_prompt_versions", None)
            )
            divergence_pairs = {
                (
                    str(item.get("domain") or ""),
                    str(item.get("source_field") or ""),
                )
                for item in reconciliation.get("divergences") or []
                if item.get("result") == "diverged"
            }
            unresolved_by_pair = {
                (str(field.get("domain")), str(field.get("source_field"))): field
                for field in unresolved
            }
            for field in payload.get("fields") or []:
                pair = (
                    str(field.get("domain") or ""),
                    str(field.get("source_field") or ""),
                )
                if pair in divergence_pairs and pair not in unresolved_by_pair:
                    unresolved.append(field)
            if hasattr(self.mapping_repository, "adjudication_receipts"):
                existing_receipts = _effective_adjudication_receipts(
                    self.mapping_repository.adjudication_receipts(
                        project_id,
                        draft_id,
                    ),
                    reconciliation_sha256,
                )
            pending = []
            for field in unresolved:
                pair = (
                    str(field.get("domain") or ""),
                    str(field.get("source_field") or ""),
                )
                receipt = existing_receipts.get(pair)
                if receipt is None:
                    pending.append(field)
                    continue
                if receipt.resolution == "escalated":
                    if field.get("question_reconciliation_sha256") != reconciliation_sha256:
                        pending.append(field)
                        continue
                    if (_decision_recorded(field)
                            and field.get("decision_reconciliation_sha256") != reconciliation_sha256):
                        pending.append(field)
                        continue
                    if (
                        classify_user_question(field) is None
                        and not _decision_recorded(field)
                    ):
                        raise AdmissionMappingPipelineError(
                            "mapping_bridge_failed"
                        )
                    continue
                if receipt.resolution == "unverifiable_gap":
                    previously_resolved += 1
                    continue
                if (
                    receipt.resolution
                    == "adjudicated_mapping"
                    and not _model_flag(field)
                    and str(field.get("user_action") or "").startswith(
                        _SYSTEM_ADJUDICATION_PREFIX
                    )
                ):
                    previously_resolved += 1
                    continue
                raise AdmissionMappingPipelineError("mapping_bridge_failed")
            unresolved = pending
        if not unresolved:
            projected = self._draft_payload(draft)
            projected["adjudication"] = {
                "state": "complete",
                "resolved_count": previously_resolved,
                "remaining_question_count": projected["review_summary"][
                    "user_question_count"
                ],
            }
            return projected
        pending_pairs = {
            (
                str(field.get("domain") or ""),
                str(field.get("source_field") or ""),
            )
            for field in unresolved
        }
        review_context = (
            {
                "divergences": [
                    item
                    for item in (reconciliation.get("divergences") or [])
                    if (
                        str(item.get("domain") or ""),
                        str(item.get("source_field") or ""),
                    ) in pending_pairs
                ]
            }
            if reconciliation is not None and divergence_pairs
            else None
        )
        # A replay can start after some draft fields were already patched by
        # this same adjudication.  Build the model-review identity from the
        # immutable first-pass verdicts, not from those mutable draft values,
        # so restart never creates a duplicate cohort for the same conflict.
        first_pass_verdicts = {
            (
                str(row.get("domain") or ""),
                str(row.get("source_field") or ""),
            ): dict((row.get("primary") or {}).get("semantic_verdict") or {})
            for row in (reconciliation or {}).get("divergences", ())
            if isinstance(row.get("primary"), Mapping)
        }
        review_fields = []
        for field in unresolved:
            review_field = dict(field)
            first_pass_verdict = first_pass_verdicts.get(
                (
                    str(field.get("domain") or ""),
                    str(field.get("source_field") or ""),
                ),
                {},
            )
            review_field.update(first_pass_verdict)
            review_fields.append(review_field)
        cohort_results = {
            cohort: self.mapping_pipeline.adjudicate_candidates(
                project_id=project_id,
                attempt_id=attempt_id,
                draft_id=draft_id,
                draft_fields=review_fields,
                workspace_dir=workspace_dir,
                review_context=review_context,
                cohort=cohort,
            )
            for cohort in ("primary", "verifier")
        }
        states = {
            str(result.get("state") or "failed")
            for result in cohort_results.values()
        }
        if states != {"ready"}:
            all_terminal = not states.intersection({"queued", "running"})
            gap_fields: list[dict[str, str]] = []
            if (
                all_terminal
                and states.intersection({"failed", "blocked"})
                and self._cohort_recoveries_exhausted(cohort_results)
            ):
                # Bounded residue (design v2 §6): after the retry budget is
                # exhausted, the failing chunks' fields become visible
                # unverifiable gaps instead of blocking the whole batch.
                gap_fields = self._gap_fields_for_failed_chunks(
                    project_id=project_id,
                    cohort_results=cohort_results,
                    known_pairs={
                        (
                            str(field.get("domain") or ""),
                            str(field.get("source_field") or ""),
                        )
                        for field in payload.get("fields") or []
                    },
                )
            if gap_fields:
                # Bounded-gap apply: restrict the review to non-gap fields and
                # continue into the normal adoption path below.
                gap_pairs = {
                    (str(item.get("domain") or ""), str(item.get("source_field") or ""))
                    for item in gap_fields
                }
                self._mark_gap_fields(
                    project_id=project_id,
                    draft_id=draft_id,
                    draft=draft,
                    gap_pairs=gap_pairs,
                    reconciliation_sha256=reconciliation_sha256,
                    divergence_pairs=divergence_pairs,
                )
                review_context = (
                    {
                        "divergences": [
                            item
                            for item in (reconciliation.get("divergences") or [])
                            if (
                                str(item.get("domain") or ""),
                                str(item.get("source_field") or ""),
                            )
                            not in gap_pairs
                        ]
                    }
                    if reconciliation is not None
                    else None
                )
                unresolved = [
                    field
                    for field in unresolved
                    if (
                        str(field.get("domain") or ""),
                        str(field.get("source_field") or ""),
                    )
                    not in gap_pairs
                ]
                divergence_pairs -= gap_pairs
            else:
                projected = self._draft_payload(draft)
                projected["adjudication"] = {
                    "state": (
                        "blocked"
                        if states.intersection({"failed", "blocked"})
                        else "running"
                    ),
                    "resolved_count": 0,
                    "remaining_question_count": len(unresolved),
                }
                return projected

        current_revisions: dict[str, str] = {}
        for result in cohort_results.values():
            for job_id in {
                str(item.get("job_id") or "")
                for item in result.get("mappings") or []
                if str(item.get("job_id") or "")
            }:
                job = self.ai_repository.get(project_id, job_id)
                revision_key = str(job.input_revision_sha256)
                current_revision = current_revisions.get(revision_key)
                if current_revision is None:
                    current_revision = self._revision_for_job(
                        job,
                        workspace_dir=workspace_dir,
                    )
                    current_revisions[revision_key] = current_revision
                if current_revision != revision_key:
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
                            reason="已作为字段语义第二轮独立复核依据。",
                            current_input_revision_sha256=str(
                                job.input_revision_sha256
                            ),
                        )
                    elif status != _value(self.accepted_status):
                        raise AdmissionMappingPipelineError(
                            "mapping_candidate_not_adoptable"
                        )

        second_review = reconcile_mapping_cohorts(
            comparison_policy_version=getattr(self.mapping_pipeline, "adjudication_comparison_policy", RECONCILIATION_SCHEMA_VERSION),
            profile_fields=[
                {
                    "domain": field.get("domain"),
                    "source_field": field.get("source_field"),
                }
                for field in unresolved
            ],
            primary_mappings=cohort_results["primary"].get("mappings") or [],
            verifier_mappings=cohort_results["verifier"].get("mappings") or [],
            primary_evidence_ids=cohort_results["primary"].get("evidence_ids") or [],
            verifier_evidence_ids=cohort_results["verifier"].get("evidence_ids") or [],
        )
        if second_review["state"] == "blocked":
            projected = self._draft_payload(draft)
            projected["adjudication"] = {
                "state": "blocked",
                "resolved_count": 0,
                "remaining_question_count": len(unresolved),
            }
            return projected

        first_pass = {
            (str(field.get("domain")), str(field.get("source_field"))): field
            for field in unresolved
        }
        resolved = previously_resolved
        remaining_system_review_count = 0
        cohort_maps = {
            cohort: {
                (str(item.get("domain") or ""), str(item.get("source_field") or "")): item
                for item in result.get("mappings") or []
            }
            for cohort, result in cohort_results.items()
        }
        for review_row in second_review.get("fields") or []:
            pair = (
                str(review_row.get("domain") or ""),
                str(review_row.get("source_field") or ""),
            )
            original = first_pass.get(pair)
            primary_item = cohort_maps["primary"].get(pair)
            verifier_item = cohort_maps["verifier"].get(pair)
            if original is None or primary_item is None or verifier_item is None:
                continue
            agreed = review_row.get("result") == "agreed"
            item = primary_item
            rationale = str(item.get("user_action") or "").strip()
            # Dissent is neither agreement nor automatically user work.
            # Preserve the field until evidence review resolves the conflict.
            requires_user = (
                _model_flag(item)
                or _model_flag(verifier_item)
                or not rationale
                or "?" in rationale
                or "？" in rationale
            )
            if not agreed and not requires_user:
                remaining_system_review_count += 1
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
            if current_field is None:
                continue
            prior_answer = (
                str(current_field.get("user_action") or "")
                if _decision_recorded(current_field)
                else str(current_field.get("prior_user_action") or "")
            )
            if (
                pair not in divergence_pairs
                and classify_user_question(current_field) is None
            ):
                continue
            uncertainty = str(item.get("uncertainty") or "").strip()
            operation_id = "adjudicate-bound-v2-" + hashlib.sha256(
                (
                    f"{RECONCILIATION_SCHEMA_VERSION}|{reconciliation_sha256}|{draft_id}|{current.version}|"
                    f"{item.get('candidate_id')}|"
                    f"{pair[0]}|{pair[1]}"
                ).encode("utf-8")
            ).hexdigest()
            if requires_user:
                questions = [
                    str(candidate.get("user_action") or "").strip()
                    for candidate in (primary_item, verifier_item)
                    if "?" in str(candidate.get("user_action") or "")
                    or "？" in str(candidate.get("user_action") or "")
                ]
                question = questions[0] if questions else (
                    f"请确认「{pair[0]}·{pair[1]}」记录的实际医学含义。"
                )
                patch = {
                    "question_reconciliation_sha256": reconciliation_sha256,
                    "decision_reconciliation_sha256": "",
                    "prior_user_action": prior_answer,
                    "user_decision_required": True,
                    "uncertainty": (
                        f"系统复核后仍需医学确认：{uncertainty or '现有证据支持不止一种解释。'}"
                    ),
                    "user_action": question,
                }
            else:
                patch = {
                    key: item[key]
                    for key in (
                        "recommended_role", "field_kind", "confidence",
                        "related_fields", "dependency_fields", "evidence_ids", "standards_reference",
                        "derivation_lineage", "value_constraints", "object_identity",
                        "object_identity_evidence_fields", "object_identity_binding_id",
                        "validated_treatment_identity_binding", "dose_semantics",
                        "quality_gate_actions",
                    )
                    if key in item
                }
                if "dependency_comparison" in review_row:
                    patch["comparison_annotations"] = {
                        **review_row["dependency_comparison"],
                        "left_evidence_ids": list(primary_item.get("evidence_ids") or ()),
                        "right_evidence_ids": list(verifier_item.get("evidence_ids") or ()),
                    }
                    canonical = review_row["dependency_comparison"].get("canonical_role")
                    if canonical and review_row["dependency_comparison"].get("dependencies_agreed") is True:
                        patch["recommended_role"] = canonical
                # Candidates accepted before the upstream list validator was
                # added can contain exact duplicate relationship labels.  The
                # draft contract is stricter; collapse only exact duplicates
                # while preserving model order and meaning.
                if "related_fields" in patch:
                    patch["related_fields"] = list(
                        dict.fromkeys(patch["related_fields"])
                    )
                patch.update({
                    "question_reconciliation_sha256": "",
                    "decision_reconciliation_sha256": "",
                    "prior_user_action": prior_answer,
                    "user_decision_required": False,
                    "uncertainty": (
                        f"第二轮独立复核：{uncertainty or '当前证据支持原字段对应。'}"
                    ),
                    "user_action": f"{_SYSTEM_ADJUDICATION_PREFIX}{rationale}",
                })
            answered_current_question = (
                requires_user and _decision_recorded(current_field)
                and current_field.get("question_reconciliation_sha256") == reconciliation_sha256
                and current_field.get("decision_reconciliation_sha256") == reconciliation_sha256
            )
            if not answered_current_question and any(current_field.get(key) != value for key, value in patch.items()):
                self.mapping_repository.edit_field(
                    project_id,
                    draft_id,
                    domain=pair[0],
                    source_field=pair[1],
                    patch=patch,
                    expected_version=int(current.version),
                    actor="system_harness",
                    idempotency_key=operation_id,
                )
            if pair in divergence_pairs:
                review_sources = tuple(
                    {
                        "cohort": cohort,
                        "job_id": str(candidate.get("job_id") or ""),
                        "candidate_id": str(candidate.get("candidate_id") or ""),
                        "evidence_ids": tuple(
                            str(value) for value in (candidate.get("evidence_ids") or ())
                        ),
                    }
                    for cohort, candidate in (
                        ("primary", primary_item),
                        ("verifier", verifier_item),
                    )
                )
                self.mapping_repository.record_adjudication(
                    project_id,
                    draft_id,
                    domain=pair[0],
                    source_field=pair[1],
                    reconciliation_sha256=reconciliation_sha256,
                    resolution=(
                        "escalated"
                        if requires_user
                        else "adjudicated_mapping"
                    ),
                    job_id=str(item.get("job_id") or ""),
                    candidate_id=str(item.get("candidate_id") or ""),
                    evidence_ids=tuple(
                        str(value) for value in (item.get("evidence_ids") or ())
                    ),
                    review_sources=review_sources,
                )
            if not requires_user:
                resolved += 1
        refreshed = self.mapping_repository.get_draft(project_id, draft_id)
        projected = self._draft_payload(refreshed)
        # A13：人工问题与机器待核验、技术缺口分开计数——
        # remaining_question=0不代表机器核验完成，gap不计入resolved。
        gap_count = 0
        if hasattr(self.mapping_repository, "adjudication_receipts"):
            gap_count = sum(
                1
                for receipt in _effective_adjudication_receipts(
                    self.mapping_repository.adjudication_receipts(
                        project_id, draft_id
                    ),
                    reconciliation_sha256,
                ).values()
                if str(getattr(receipt, "resolution", "")) == "unverifiable_gap"
            )
        projected["adjudication"] = {
            "state": "blocked" if remaining_system_review_count else "complete",
            "resolved_count": resolved,
            "unverifiable_gap_count": gap_count,
            "remaining_system_review_count": remaining_system_review_count,
            "remaining_question_count": projected["review_summary"][
                "user_question_count"
            ],
        }
        return projected

    def _cohort_recoveries_exhausted(self, cohort_results) -> bool:
        """True when every failed adjudication job burned its retries.

        The bounded budget is the automatic-recovery count, not the raw
        attempt counter: operator requeues legitimately inflate attempts
        without opening new automatic budget, and a job whose automatic
        recovery is spent can never be resumed by the in-place loop again.
        """
        from packages.medical_monitoring.admission.mapping_pipeline import (
            _ADJUDICATION_AUTO_RECOVERY_LIMIT,
        )
        # mappings only carries completed work; query the repository directly
        # via the jobs the pipeline reported (job_ids live in mappings rows).
        for result in cohort_results.values():
            for job_ref in result.get("failed_jobs") or []:
                job = self.ai_repository.get(job_ref[0], job_ref[1])
                arc = self._automatic_recovery_count(job_ref[0], job_ref[1])
                if arc >= int(_ADJUDICATION_AUTO_RECOVERY_LIMIT):
                    continue
                if int(getattr(job, "attempt_count", 0) or 0) < int(
                    getattr(job, "max_attempts", 0) or 0
                ):
                    return False
        return True

    def _automatic_recovery_count(self, project_id: str, job_id: str) -> int:
        """Read the bounded-recovery counter from the durable job row.

        The job model intentionally omits bookkeeping columns; the raw row
        is the authority for how much automatic recovery budget is spent.
        """
        connect = getattr(self.ai_repository, "_connect", None)
        if not callable(connect):
            return 0
        try:
            with connect() as connection:
                row = connection.execute(
                    """
                    SELECT automatic_recovery_count
                    FROM monitoring_ai_jobs
                    WHERE project_id = ? AND job_id = ?
                    """,
                    (project_id, job_id),
                ).fetchone()
            return int(row[0]) if row is not None else 0
        except Exception:
            return 0

    def _gap_fields_for_failed_chunks(
        self,
        *,
        project_id: str,
        cohort_results,
        known_pairs: set,
    ) -> list:
        """Fields covered by failed chunks become visible unverifiable gaps.

        R24-03B：failed分片的payload读取失败是显式错误——静默continue会把
        “存储/覆盖未知”伪装成“没有缺口”。这里直接抛出，由调用方以
        blocked状态呈现，操作员可诊断；绝不返回空gap冒充完整。
        """
        gaps: list[dict[str, str]] = []
        seen: set = set()
        for result in cohort_results.values():
            for job_ref in result.get("failed_jobs") or []:
                try:
                    payload = self.ai_repository.input_payload(
                        job_ref[0], job_ref[1]
                    )
                except Exception as exc:
                    raise AdmissionMappingPipelineError(
                        "mapping_adjudication_failed_payload_unreadable"
                    ) from exc
                profile = payload.get("field_profile") or {}
                for field in profile.get("fields") or []:
                    pair = (
                        str(field.get("domain") or ""),
                        str(field.get("field") or field.get("source_field") or ""),
                    )
                    if pair in known_pairs and pair not in seen:
                        seen.add(pair)
                        gaps.append(
                            {"domain": pair[0], "source_field": pair[1]}
                        )
        return gaps

    def _mark_gap_fields(
        self,
        *,
        project_id: str,
        draft_id: str,
        draft: Any,
        gap_pairs: set,
        reconciliation_sha256: str,
        divergence_pairs: set,
    ) -> None:
        """Persist bounded residues as visible unverifiable gaps.

        Gap fields get a system note (not a user question), their model
        question flag is cleared so confirm is not blocked, and a receipt
        with resolution ``unverifiable_gap`` records the durable outcome.
        """
        payload = draft.model_dump(mode="json") if hasattr(draft, "model_dump") else dict(draft)
        current = self.mapping_repository.get_draft(project_id, draft_id)
        # A11：已存在本轮reconciliation有效gap回执的对直接跳过——幂等重入
        # 不重复编辑、不重复记账。
        already_gap = set()
        if hasattr(self.mapping_repository, "adjudication_receipts"):
            for receipt in self.mapping_repository.adjudication_receipts(
                project_id, draft_id
            ):
                if (
                    str(getattr(receipt, "resolution", "")) == "unverifiable_gap"
                    and str(getattr(receipt, "reconciliation_sha256", "")) == reconciliation_sha256
                ):
                    already_gap.add(
                        (str(getattr(receipt, "domain", "")), str(getattr(receipt, "source_field", "")))
                    )
        for field in payload.get("fields") or []:
            pair = (
                str(field.get("domain") or ""),
                str(field.get("source_field") or ""),
            )
            if pair not in gap_pairs:
                continue
            if pair in already_gap:
                current_field = next(
                    (f for f in (current.model_dump(mode="json").get("fields") or [])
                     if (str(f.get("domain") or ""), str(f.get("source_field") or "")) == pair),
                    {},
                )
                if current_field.get("semantic_availability") == "unverifiable_gap":
                    continue
                # 旧策略gap回执缺机器标记：补写patch（键幂等）后照常记账
                # 会被already-Gap receipt重复——记账按本轮sha幂等由存储层
                # 唯一约束处理；这里继续执行edit以补齐机器标记。
            patch = {
                "user_decision_required": False,
                "user_action": (
                    "系统复核：本字段多轮双模型裁决未能闭合，已列为不可评估能力；"
                    "相关分析将显示覆盖不足，不阻塞其余字段确认。"
                ),
                "question_reconciliation_sha256": "",
                "decision_reconciliation_sha256": "",
                # R24-02：机器可执行边界——物化/下游据此跳过该字段的
                # canonical语义消费，不依赖user_action文案。
                "semantic_availability": "unverifiable_gap",
            }
            if any(current_field.get(key) != value for key, value in patch.items() for current_field in [
                next(
                    (f for f in (current.model_dump(mode="json").get("fields") or [])
                     if (str(f.get("domain") or ""), str(f.get("source_field") or "")) == pair),
                    {},
                )
            ]):
                self.mapping_repository.edit_field(
                    project_id,
                    draft_id,
                    domain=pair[0],
                    source_field=pair[1],
                    patch=patch,
                    expected_version=int(current.version),
                    actor="system_harness",
                    # A11：幂等键绑定本轮reconciliation——跨修订不复用旧键，
                    # 修订重开时生成新的编辑身份。
                    idempotency_key=(
                        f"gap:{draft_id}:{reconciliation_sha256[:12]}:"
                        f"{pair[0]}:{pair[1]}"
                    ),
                )
                current = self.mapping_repository.get_draft(project_id, draft_id)
            if pair in divergence_pairs:
                # A10：receipt写入失败必须显式失败——edit已按幂等键落库，
                # 重放本轮即可恢复；吞错会造成“页面已改、durable回执缺失”
                # 的不一致，禁止。
                self.mapping_repository.record_adjudication(
                    project_id,
                    draft_id,
                    domain=pair[0],
                    source_field=pair[1],
                    reconciliation_sha256=reconciliation_sha256,
                    resolution="unverifiable_gap",
                    job_id="",
                    candidate_id="",
                    evidence_ids=(),
                    review_sources=(),
                )

    def reconcile_with_verifier(
        self,
        *,
        project_id: str,
        attempt_id: str,
        draft_id: str,
        verifier_candidates: Any = None,
        primary_execution_route: str = "",
        workspace_dir: Any = None,
    ) -> Mapping[str, Any]:
        """Run the deterministic dual-cohort reconciliation gate (read-only).

        The current draft carries the primary cohort's adopted verdicts; the
        verifier cohort arrives as its own completed candidates from the
        independent blind re-check. Coverage, evidence closure, agreement and
        the mapping-stage conclusion boundary are evaluated deterministically;
        divergences are preserved verbatim for focused system review. Nothing
        here edits the draft, adopts a winner, or materializes facts.

        Callers that know how the primary cohort actually executed must pass
        ``primary_execution_route`` (from ``first_pass_execution``); an empty
        value keeps the idealized remote-primary assumption of the contract
        default and is only acceptable where no fallback route exists.
        """

        draft = self._require_attempt_draft(project_id, attempt_id, draft_id)
        payload = (
            draft.model_dump(mode="json")
            if hasattr(draft, "model_dump")
            else dict(draft)
        )
        draft_fields = list(payload.get("fields") or [])
        profile_fields = [
            {
                "domain": str(field.get("domain") or ""),
                "field": str(field.get("source_field") or ""),
            }
            for field in draft_fields
        ]
        primary_mappings = [
            {
                "domain": field.get("domain"),
                "source_field": field.get("source_field"),
                "recommended_role": field.get("recommended_role"),
                "field_kind": field.get("field_kind"),
                "confidence": field.get("confidence"),
                "evidence_ids": list(field.get("evidence_ids") or []),
            }
            for field in draft_fields
        ]
        can_load_cohorts = all(
            hasattr(self.ai_repository, name)
            for name in ("list_jobs", "candidates")
        )
        if can_load_cohorts:
            primary_jobs = self._mapping_jobs(
                project_id,
                attempt_id,
                MONITORING_C3_PRIMARY_BUSINESS_KEY_PREFIX,
            )
            primary_candidates = self._completed_candidates(
                project_id,
                primary_jobs,
                workspace_dir=workspace_dir,
                allow_profile_evidence_upgrade=True,
            )
            primary = cohort_payload_from_candidates(primary_candidates)
            primary_mappings = primary["mappings"]
            primary_evidence_ids = primary["evidence_ids"]
            if not primary_execution_route:
                primary_execution_route = self._first_pass_execution(
                    ((job.provider, job.requested_model) for job in primary_jobs),
                    block=True,
                )["route"]
        elif verifier_candidates is not None:
            # Small injected unit doubles can exercise the pure comparator;
            # the product service always uses repository-backed evidence.
            primary_evidence_ids = {
                evidence_id
                for field in primary_mappings
                for evidence_id in field["evidence_ids"]
            }
        else:
            raise AdmissionMappingPipelineError("mapping_verifier_incomplete")
        if verifier_candidates is None:
            verifier_jobs = self._mapping_jobs(
                project_id,
                attempt_id,
                MONITORING_C3_VERIFIER_BUSINESS_KEY_PREFIX,
            )
            if any(
                str(job.prompt_version) != MONITORING_C3_VERIFIER_PROMPT_VERSION
                for job in verifier_jobs
            ):
                raise AdmissionMappingPipelineError("mapping_verifier_incomplete")
            # Dual-cohort input validation: agreement only counts when both
            # cohorts contain the same set of per-job frozen revisions. The
            # cohort identity is shared, but deterministic metadata jobs may
            # carry a different revision from model-analyzed chunks.
            primary_revisions = {
                str(job.input_revision_sha256) for job in primary_jobs
            }
            verifier_revisions = {
                str(job.input_revision_sha256) for job in verifier_jobs
            }
            if primary_revisions != verifier_revisions:
                raise AdmissionMappingPipelineError(
                    "mapping_cohort_input_mismatch"
                )
            verifier_candidates = self._completed_candidates(
                project_id,
                verifier_jobs,
                workspace_dir=workspace_dir,
                allow_profile_evidence_upgrade=True,
            )
        verifier = cohort_payload_from_candidates(verifier_candidates or ())
        report = reconcile_mapping_cohorts(
            profile_fields=profile_fields,
            primary_mappings=primary_mappings,
            verifier_mappings=verifier["mappings"],
            primary_evidence_ids=primary_evidence_ids,
            verifier_evidence_ids=verifier["evidence_ids"],
            primary_execution_route=(
                str(primary_execution_route).strip()
                or MONITORING_C3_MAPPING_EXECUTION_ROUTE_PRIMARY
            ),
        )
        projected = self._draft_payload(draft)
        projected["reconciliation"] = dict(report)
        return projected

    def _mapping_jobs(
        self,
        project_id: str,
        attempt_id: str,
        prefix: str,
    ) -> tuple[Any, ...]:
        if self.ai_repository is None:
            raise AdmissionMappingPipelineError("mapping_draft_unconfigured")
        task_type = self.task_type or getattr(self.mapping_pipeline, "_task_type", "")
        jobs = self.ai_repository.list_jobs(
            project_id,
            task_type=str(_value(task_type)),
            business_key_prefix=f"{prefix}:{attempt_id}:",
        )
        if not jobs:
            raise AdmissionMappingPipelineError("mapping_verifier_incomplete")
        return _latest_job_cohort(jobs, repository=self.ai_repository)

    def _completed_candidates(
        self,
        project_id: str,
        jobs: Iterable[Any],
        *,
        workspace_dir: Any = None,
        allow_profile_evidence_upgrade: bool = False,
    ) -> tuple[Any, ...]:
        candidates: list[Any] = []
        current_revisions: dict[str, str] = {}
        for job in jobs:
            if str(_value(job.status)) != "completed":
                raise AdmissionMappingPipelineError("mapping_verifier_incomplete")
            if workspace_dir is not None:
                revision_key = str(job.input_revision_sha256)
                current_revision = current_revisions.get(revision_key)
                if current_revision is None:
                    current_revision = self._revision_for_job(
                        job,
                        workspace_dir=workspace_dir,
                        allow_profile_evidence_upgrade=(
                            allow_profile_evidence_upgrade
                        ),
                    )
                    current_revisions[revision_key] = current_revision
                if current_revision != revision_key:
                    raise AdmissionMappingPipelineError(
                        "mapping_verifier_incomplete"
                    )
            rows = self.ai_repository.candidates(project_id, job.job_id)
            if len(rows) != 1:
                raise AdmissionMappingPipelineError("mapping_verifier_incomplete")
            candidates.extend(rows)
        return tuple(candidates)

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
        workspace_dir: Any = None,
    ) -> Mapping[str, Any]:
        if self.mapping_repository is None:
            raise AdmissionMappingPipelineError("mapping_draft_unconfigured")
        draft = self._require_attempt_draft(project_id, attempt_id, draft_id)
        payload = draft.model_dump(mode="json") if hasattr(draft, "model_dump") else dict(draft)
        if _unresolved_question_count(payload.get("fields") or []):
            # Only medically substantive ambiguities block durable
            # confirmation; system-adopted candidates never do.
            raise AdmissionMappingPipelineError("mapping_questions_unresolved")
        if self.require_dual_reconciliation:
            reconciliation = self.reconcile_with_verifier(
                project_id=project_id,
                attempt_id=attempt_id,
                draft_id=draft_id,
                workspace_dir=workspace_dir,
            )["reconciliation"]
            if not reconciliation["auto_pass"] and not self._resolved_dual_review(
                project_id=project_id,
                draft_id=draft_id,
                draft_fields=payload.get("fields") or [],
                reconciliation=reconciliation,
            ):
                raise AdmissionMappingPipelineError(
                    "mapping_reconciliation_required"
                )
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

    def _resolved_dual_review(
        self,
        *,
        project_id: str,
        draft_id: str,
        draft_fields: Any,
        reconciliation: Mapping[str, Any],
    ) -> bool:
        """Verify that every blind-review divergence has a durable resolution."""

        if reconciliation.get("state") != "diverged":
            return False
        divergences = [
            dict(item)
            for item in reconciliation.get("divergences") or []
            if item.get("result") == "diverged"
        ]
        fields = {
            (str(item.get("domain") or ""), str(item.get("source_field") or "")): item
            for item in draft_fields
        }
        reconciliation_sha256 = _adjudication_reconciliation_sha256(
            reconciliation, prompt_versions=getattr(self.mapping_pipeline, "adjudication_prompt_versions", None)
        )
        if not hasattr(self.mapping_repository, "adjudication_receipts"):
            return False
        receipts = _effective_adjudication_receipts(
            self.mapping_repository.adjudication_receipts(
                project_id,
                draft_id,
            ),
            reconciliation_sha256,
        )
        for divergence in divergences:
            pair = (
                str(divergence.get("domain") or ""),
                str(divergence.get("source_field") or ""),
            )
            field = fields.get(pair)
            receipt = receipts.get(pair)
            if field is None or receipt is None:
                return False
            if _decision_recorded(field):
                # A later user answer on a field whose chunk failed the dual
                # review still closes the loop: the gap receipt records the
                # residue, the recorded decision (bound to the same
                # reconciliation) resolves it for the user.
                if receipt.resolution == "unverifiable_gap" and (
                    field.get("question_reconciliation_sha256") == reconciliation_sha256
                    or field.get("decision_reconciliation_sha256") == reconciliation_sha256
                ):
                    continue
                if (receipt.resolution != "escalated"
                        or field.get("question_reconciliation_sha256") != reconciliation_sha256
                        or field.get("decision_reconciliation_sha256") != reconciliation_sha256):
                    return False
                continue
            if receipt.resolution == "unverifiable_gap":
                # Visible bounded residue: no durable verdict exists after the
                # retry budget; coverage insufficiency is the outcome itself.
                continue
            if (
                _model_flag(field)
                or receipt.resolution != "adjudicated_mapping"
                or not str(field.get("user_action") or "").startswith(
                    _SYSTEM_ADJUDICATION_PREFIX
                )
            ):
                return False
        return bool(divergences)

    def _revision_for_job(
        self,
        job: Any,
        *,
        workspace_dir: Any,
        allow_profile_evidence_upgrade: bool = False,
    ) -> str:
        if allow_profile_evidence_upgrade:
            resolved = current_admission_mapping_revision(
                self.ai_repository,
                job,
                workspace_dir=workspace_dir,
                relationship_profiler=(
                    self.mapping_pipeline._resolve_relationship_profiler()
                    if self.mapping_pipeline is not None
                    else None
                ),
                document_evidence_resolver=(
                    self.mapping_pipeline._document_evidence_resolver
                    if self.mapping_pipeline is not None
                    else None
                ),
                allow_profile_evidence_upgrade=True,
            )
            return str(resolved or "")
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
            relationship_profiler=(
                self.mapping_pipeline._resolve_relationship_profiler()
                if self.mapping_pipeline is not None
                else None
            ),
            document_evidence_resolver=(
                self.mapping_pipeline._document_evidence_resolver
                if self.mapping_pipeline is not None
                else None
            ),
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
