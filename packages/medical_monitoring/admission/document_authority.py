from __future__ import annotations

import hashlib
import json
from typing import Any, Literal, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, field_validator, model_validator

from .mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROVIDER,
)


DOCUMENT_AUTHORITY_SCHEMA_VERSION = "monitoring-document-authority-v1"
DOCUMENT_ROLES = ("protocol", "investigator_brochure", "ecrf", "sap")
REQUIRED_DOCUMENT_ROLES = frozenset({"protocol", "ecrf"})
AUTO_RESOLVE_CONFIDENCE = 0.9
PRIMARY_PROMPT_VERSION = "monitoring-document-authority-primary-v1"
VERIFIER_PROMPT_VERSION = "monitoring-document-authority-verifier-v1"
PRIMARY_REVIEW_PROMPT_VERSION = "monitoring-document-authority-review-primary-v1"
VERIFIER_REVIEW_PROMPT_VERSION = "monitoring-document-authority-review-verifier-v1"

_BATCH_KEYS = frozenset({"manifest_version", "batch_id", "candidates", "authority_status"})
_CANDIDATE_KEYS = frozenset({
    "manifest_version", "candidate_id", "file_id", "filename", "content_sha256",
    "size_bytes", "media_type", "role_hypotheses", "parser_name", "parser_version",
    "technical_status", "content_status", "use_status", "authority_status",
    "extraction_status", "page_count", "locator_count", "locator_index_sha256",
    "excerpts", "sheets", "zero_text_page_count", "zero_text_page_samples",
    "limitation_codes",
})
_EXCERPT_KEYS = frozenset({"locator", "text", "text_sha256"})
_SHEET_KEYS = frozenset({
    "locator", "sheet_name", "row_count", "headers", "visibility", "used_range",
    "parser_warnings",
})
class DocumentAuthorityError(RuntimeError):
    pass


def document_authority_batch_sha256(batch: Mapping[str, Any]) -> str:
    _validate_batch(batch)
    return _digest(batch)


def validate_document_authority_analysis(
    batch: Mapping[str, Any], analysis: "DocumentAuthorityAnalysis"
) -> None:
    candidate_ids, locators = _validate_batch(batch)
    _validate_analysis(
        analysis,
        batch_id=str(batch["batch_id"]),
        input_sha256=_digest(batch),
        candidate_ids=candidate_ids,
        locators=locators,
    )


def _validate_nonempty_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    cleaned = tuple(value.strip() for value in values)
    if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
        raise ValueError("values must be non-empty and unique")
    return cleaned


class CandidateAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=2, max_length=160)
    inferred_role: Literal[
        "protocol", "investigator_brochure", "ecrf", "sap", "unrelated", "uncertain"
    ]
    usable: StrictBool
    confidence: StrictFloat = Field(ge=0, le=1)
    document_version: str = Field(default="", max_length=120)
    document_date: str = Field(default="", max_length=40)
    evidence_locators: tuple[str, ...] = Field(default=(), max_length=20)
    uncertainty: str = Field(default="", max_length=2_000)

    _locators = field_validator("evidence_locators")(_validate_nonempty_unique)


class RoleSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["protocol", "investigator_brochure", "ecrf", "sap"]
    decision: Literal["selected", "missing", "unresolved"]
    selected_candidate_id: str = Field(default="", max_length=160)
    confidence: StrictFloat = Field(ge=0, le=1)
    evidence_locators: tuple[str, ...] = Field(default=(), max_length=20)
    uncertainty: str = Field(default="", max_length=2_000)

    _locators = field_validator("evidence_locators")(_validate_nonempty_unique)

    @model_validator(mode="after")
    def validate_selection(self) -> "RoleSelection":
        if (self.decision == "selected") != bool(self.selected_candidate_id.strip()):
            raise ValueError("selected decision and candidate ID must agree")
        if self.decision == "selected" and not self.evidence_locators:
            raise ValueError("selected document requires locator evidence")
        if self.decision != "selected" and self.evidence_locators:
            raise ValueError("non-selected role cannot carry unbound evidence")
        return self


class DocumentAuthorityAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[DOCUMENT_AUTHORITY_SCHEMA_VERSION]
    batch_id: str = Field(min_length=2, max_length=160)
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_assessments: tuple[CandidateAssessment, ...]
    role_selections: tuple[RoleSelection, ...]


class DocumentAuthorityRunEnvelope(BaseModel):
    """Server-owned identity around model output; absent from blind input."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(min_length=2, max_length=160)
    job_id: str = Field(min_length=2, max_length=160)
    role: Literal["primary", "verifier"]
    provider: str
    model: str
    prompt_version: str
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    analysis: DocumentAuthorityAnalysis

    @model_validator(mode="after")
    def bind_output(self) -> "DocumentAuthorityRunEnvelope":
        if self.input_sha256 != self.analysis.input_sha256:
            raise ValueError("run input hash does not bind analysis")
        if self.output_sha256 != _digest(self.analysis.model_dump(mode="json")):
            raise ValueError("run output hash does not bind analysis")
        return self


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=2, max_length=160)
    locator: str = Field(min_length=1, max_length=500)


class ConflictDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["protocol", "investigator_brochure", "ecrf", "sap"]
    decision: Literal["selected", "missing", "unresolved"]
    selected_candidate_id: str = Field(default="", max_length=160)
    document_version: str = Field(default="", max_length=120)
    document_date: str = Field(default="", max_length=40)
    confidence: StrictFloat = Field(ge=0, le=1)
    considered_candidate_ids: tuple[str, ...] = Field(default=(), max_length=100)
    evidence_references: tuple[EvidenceReference, ...] = Field(default=(), max_length=100)
    uncertainty: str = Field(default="", max_length=2_000)

    _candidates = field_validator("considered_candidate_ids")(_validate_nonempty_unique)

    @model_validator(mode="after")
    def validate_decision(self) -> "ConflictDecision":
        if (self.decision == "selected") != bool(self.selected_candidate_id.strip()):
            raise ValueError("selected decision and candidate ID must agree")
        evidence_keys = {
            (item.candidate_id, item.locator) for item in self.evidence_references
        }
        if len(evidence_keys) != len(self.evidence_references):
            raise ValueError("evidence references must be unique")
        if self.decision == "selected" and not self.evidence_references:
            raise ValueError("selected document requires candidate-bound evidence")
        if self.decision == "selected" and not (
            self.document_version.strip() or self.document_date.strip()
        ):
            raise ValueError("selected current document requires version or date")
        if self.decision != "selected" and (
            self.document_version.strip() or self.document_date.strip()
        ):
            raise ValueError("non-selected decision cannot carry version or date")
        return self


class DocumentAuthorityConflictReview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[DOCUMENT_AUTHORITY_SCHEMA_VERSION]
    conflict_packet_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    decisions: tuple[ConflictDecision, ...]


class DocumentAuthorityConflictRunEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(min_length=2, max_length=160)
    job_id: str = Field(min_length=2, max_length=160)
    role: Literal["primary", "verifier"]
    provider: str
    model: str
    prompt_version: str
    conflict_packet_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review: DocumentAuthorityConflictReview

    @model_validator(mode="after")
    def bind_output(self) -> "DocumentAuthorityConflictRunEnvelope":
        if self.conflict_packet_sha256 != self.review.conflict_packet_sha256:
            raise ValueError("review input hash does not bind output")
        if self.output_sha256 != _digest(self.review.model_dump(mode="json")):
            raise ValueError("review output hash does not bind output")
        return self


class ResolvedRole(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["protocol", "investigator_brochure", "ecrf", "sap"]
    status: Literal["selected", "missing"]
    candidate_id: str = Field(default="", max_length=160)

    @model_validator(mode="after")
    def validate_candidate(self) -> "ResolvedRole":
        if (self.status == "selected") != bool(self.candidate_id.strip()):
            raise ValueError("resolved status and candidate must agree")
        return self


class AuthorityConflict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["protocol", "investigator_brochure", "ecrf", "sap"]
    status: Literal["needs_dual_review"]
    candidate_options: tuple[str, ...] = Field(default=(), max_length=100)

    _candidates = field_validator("candidate_options")(_validate_nonempty_unique)


class DocumentAuthorityReconciliation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[DOCUMENT_AUTHORITY_SCHEMA_VERSION]
    batch_id: str = Field(min_length=2, max_length=160)
    input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: Literal["resolved", "needs_dual_review"]
    resolved_roles: tuple[ResolvedRole, ...]
    conflicts: tuple[AuthorityConflict, ...]
    run_ids: tuple[str, str]
    reconciliation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_partition(self) -> "DocumentAuthorityReconciliation":
        roles = [item.role for item in (*self.resolved_roles, *self.conflicts)]
        if sorted(roles) != sorted(DOCUMENT_ROLES) or len(roles) != len(set(roles)):
            raise ValueError("reconciliation roles must form one complete partition")
        if (self.state == "needs_dual_review") != bool(self.conflicts):
            raise ValueError("reconciliation state must match conflicts")
        if len(set(self.run_ids)) != 2:
            raise ValueError("reconciliation requires two run IDs")
        return self


def reconcile_document_authority(
    batch: Mapping[str, Any],
    primary: DocumentAuthorityRunEnvelope,
    verifier: DocumentAuthorityRunEnvelope,
) -> dict[str, Any]:
    candidate_ids, locators = _validate_batch(batch)
    input_sha256 = _digest(batch)
    _validate_run_pair(primary, verifier, input_sha256, review=False)
    for run in (primary, verifier):
        _validate_analysis(
            run.analysis,
            batch_id=str(batch["batch_id"]),
            input_sha256=input_sha256,
            candidate_ids=candidate_ids,
            locators=locators,
        )

    left_roles = {item.role: item for item in primary.analysis.role_selections}
    right_roles = {item.role: item for item in verifier.analysis.role_selections}
    resolved: list[dict[str, str]] = []
    conflicts: list[dict[str, Any]] = []
    for role in DOCUMENT_ROLES:
        left, right = left_roles[role], right_roles[role]
        if _same_selection(left, right) and _same_role_assessments(
            primary.analysis, verifier.analysis, role, left.selected_candidate_id
        ):
            resolved.append(_resolved_role(role, "selected", left.selected_candidate_id))
        elif (
            role not in REQUIRED_DOCUMENT_ROLES
            and _same_missing(left, right)
            and _role_absent(primary.analysis, role)
            and _role_absent(verifier.analysis, role)
            and _same_role_assessments(
                primary.analysis, verifier.analysis, role, ""
            )
        ):
            resolved.append(_resolved_role(role, "missing", ""))
        else:
            conflicts.append({
                "role": role,
                "status": "needs_dual_review",
                "candidate_options": sorted({
                    item.selected_candidate_id for item in (left, right)
                    if item.selected_candidate_id
                }),
            })
    result = {
        "schema_version": DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        "batch_id": str(batch["batch_id"]),
        "input_sha256": input_sha256,
        "state": "needs_dual_review" if conflicts else "resolved",
        "resolved_roles": resolved,
        "conflicts": conflicts,
        "run_ids": sorted((primary.run_id, verifier.run_id)),
    }
    output = {**result, "reconciliation_sha256": _digest(result)}
    DocumentAuthorityReconciliation.model_validate(output)
    return output


def build_anonymous_conflict_packet(
    batch: Mapping[str, Any],
    primary: DocumentAuthorityRunEnvelope,
    verifier: DocumentAuthorityRunEnvelope,
) -> dict[str, Any]:
    candidate_ids, _locators = _validate_batch(batch)
    reconciliation = reconcile_document_authority(batch, primary, verifier)
    conflict_rows = list(reconciliation.get("conflicts") or ())
    conflict_roles = sorted(str(item.get("role") or "") for item in conflict_rows)
    if not conflict_roles:
        raise DocumentAuthorityError("document_authority_conflicts_invalid")

    candidates = [_anonymous_candidate(raw) for raw in batch["candidates"]]
    allowed_by_role = {
        role: sorted(str(candidate["candidate_id"]) for candidate in candidates)
        for role in conflict_roles
    }
    packet = {
        "schema_version": DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        "batch_id": str(batch["batch_id"]),
        "input_sha256": _digest(batch),
        "reconciliation_sha256": reconciliation["reconciliation_sha256"],
        "conflict_roles": conflict_roles,
        "allowed_candidate_ids_by_role": allowed_by_role,
        "candidates": sorted(candidates, key=lambda item: item["candidate_id"]),
        "candidate_coverage": sorted(candidate_ids),
    }
    return {**packet, "conflict_packet_sha256": _digest(packet)}


def resolve_document_authority_conflicts(
    batch: Mapping[str, Any],
    analysis_primary: DocumentAuthorityRunEnvelope,
    analysis_verifier: DocumentAuthorityRunEnvelope,
    conflict_packet: Mapping[str, Any],
    primary: DocumentAuthorityConflictRunEnvelope,
    verifier: DocumentAuthorityConflictRunEnvelope,
) -> dict[str, Any]:
    reconciliation = reconcile_document_authority(
        batch, analysis_primary, analysis_verifier
    )
    expected_packet = build_anonymous_conflict_packet(
        batch, analysis_primary, analysis_verifier
    )
    if conflict_packet != expected_packet:
        raise DocumentAuthorityError("document_authority_conflict_packet_tampered")
    expected_hash = str(conflict_packet["conflict_packet_sha256"])
    _validate_run_pair(primary, verifier, expected_hash, review=True)
    roles = tuple(str(value) for value in conflict_packet["conflict_roles"])
    left = _review_index(primary.review, roles)
    right = _review_index(verifier.review, roles)
    candidates = {str(item["candidate_id"]): item for item in conflict_packet["candidates"]}
    allowed_by_role = {
        role: set(conflict_packet["allowed_candidate_ids_by_role"][role])
        for role in roles
    }
    resolved = list(reconciliation["resolved_roles"])
    unresolved: list[str] = []
    for role in roles:
        left_item, right_item = left[role], right[role]
        allowed = allowed_by_role[role]
        for item in (left_item, right_item):
            _validate_conflict_decision(item, allowed, candidates)
        if _same_conflict_selection(left_item, right_item):
            resolved.append(_resolved_role(role, "selected", left_item.selected_candidate_id))
        elif role not in REQUIRED_DOCUMENT_ROLES and _same_conflict_missing(
            left_item, right_item, allowed
        ):
            resolved.append(_resolved_role(role, "missing", ""))
        else:
            unresolved.append(role)
    return {
        "schema_version": DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        "batch_id": reconciliation["batch_id"],
        "state": "needs_user_input" if unresolved else "resolved",
        "resolved_roles": sorted(resolved, key=lambda item: DOCUMENT_ROLES.index(item["role"])),
        "unresolved_roles": unresolved,
        "user_question": (
            "系统仍无法可靠判断部分研究文件的当前版本，请选择应作为本次分析依据的文件。"
            if unresolved else ""
        ),
        "review_run_ids": sorted((primary.run_id, verifier.run_id)),
    }


def _validate_batch(batch: Mapping[str, Any]) -> tuple[set[str], dict[str, set[str]]]:
    if (
        set(batch) - _BATCH_KEYS
        or batch.get("manifest_version") != "monitoring-document-candidate-v1"
        or batch.get("authority_status") != "not_adjudicated"
    ):
        raise DocumentAuthorityError("document_authority_batch_invalid")
    candidate_ids: set[str] = set()
    locators: dict[str, set[str]] = {}
    for raw in batch.get("candidates", ()):
        if set(raw) - _CANDIDATE_KEYS:
            raise DocumentAuthorityError("document_authority_candidate_shape_invalid")
        if raw.get("authority_status") not in {None, "not_promoted"}:
            raise DocumentAuthorityError("document_authority_candidate_shape_invalid")
        candidate_id = str(raw.get("candidate_id") or "")
        if not candidate_id or candidate_id in candidate_ids:
            raise DocumentAuthorityError("document_authority_candidate_coverage_invalid")
        candidate_ids.add(candidate_id)
        locators[candidate_id] = _candidate_locators(raw)
    if not candidate_ids:
        raise DocumentAuthorityError("document_authority_candidate_coverage_invalid")
    return candidate_ids, locators


def _validate_analysis(
    analysis: DocumentAuthorityAnalysis,
    *, batch_id: str, input_sha256: str,
    candidate_ids: set[str], locators: Mapping[str, set[str]],
) -> None:
    if analysis.batch_id != batch_id or analysis.input_sha256 != input_sha256:
        raise DocumentAuthorityError("document_authority_analysis_stale")
    assessments = {item.candidate_id: item for item in analysis.candidate_assessments}
    if set(assessments) != candidate_ids or len(assessments) != len(analysis.candidate_assessments):
        raise DocumentAuthorityError("document_authority_candidate_coverage_invalid")
    selections = {item.role: item for item in analysis.role_selections}
    if set(selections) != set(DOCUMENT_ROLES) or len(selections) != len(analysis.role_selections):
        raise DocumentAuthorityError("document_authority_role_coverage_invalid")
    for assessment in assessments.values():
        if not set(assessment.evidence_locators).issubset(locators[assessment.candidate_id]):
            raise DocumentAuthorityError("document_authority_evidence_not_closed")
    for selection in selections.values():
        candidate_id = selection.selected_candidate_id
        if candidate_id and candidate_id not in candidate_ids:
            raise DocumentAuthorityError("document_authority_selection_unknown")
        if candidate_id and not set(selection.evidence_locators).issubset(locators[candidate_id]):
            raise DocumentAuthorityError("document_authority_evidence_not_closed")
        assessment = assessments.get(candidate_id)
        if assessment and (not assessment.usable or assessment.inferred_role != selection.role):
            raise DocumentAuthorityError("document_authority_selection_inconsistent")
        if selection.decision == "missing" and not _role_absent(analysis, selection.role):
            raise DocumentAuthorityError("document_authority_missing_not_proven")


def _validate_run_pair(left: Any, right: Any, input_hash: str, *, review: bool) -> None:
    if left.run_id == right.run_id or left.job_id == right.job_id:
        raise DocumentAuthorityError("document_authority_runs_not_independent")
    expected = (
        (
            "primary", MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL,
            PRIMARY_REVIEW_PROMPT_VERSION if review else PRIMARY_PROMPT_VERSION,
        ),
        (
            "verifier", MONITORING_C3_VERIFIER_PROVIDER, MONITORING_C3_VERIFIER_MODEL,
            VERIFIER_REVIEW_PROMPT_VERSION if review else VERIFIER_PROMPT_VERSION,
        ),
    )
    for run, identity in zip((left, right), expected):
        actual = (run.role, run.provider, run.model, run.prompt_version)
        bound_hash = run.conflict_packet_sha256 if review else run.input_sha256
        if actual != identity or bound_hash != input_hash:
            raise DocumentAuthorityError("document_authority_run_identity_invalid")


def _anonymous_candidate(raw: Mapping[str, Any]) -> dict[str, Any]:
    if set(raw) - _CANDIDATE_KEYS:
        raise DocumentAuthorityError("document_authority_candidate_shape_invalid")
    return {
        "candidate_id": str(raw.get("candidate_id") or ""),
        "role_hypotheses": sorted(str(value) for value in raw.get("role_hypotheses", ())),
        "filename": str(raw.get("filename") or ""),
        "technical_status": str(raw.get("technical_status") or ""),
        "extraction_status": str(raw.get("extraction_status") or ""),
        "locator_count": int(raw.get("locator_count") or 0),
        "excerpts": [_project_nested(item, _EXCERPT_KEYS) for item in raw.get("excerpts", ())],
        "sheets": [_project_nested(item, _SHEET_KEYS) for item in raw.get("sheets", ())],
    }


def _project_nested(item: Mapping[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
    if set(item) - allowed:
        raise DocumentAuthorityError("document_authority_anonymous_evidence_invalid")
    return {key: item[key] for key in sorted(item)}


def _candidate_locators(raw: Mapping[str, Any]) -> set[str]:
    return {
        str(item.get("locator") or "")
        for key in ("excerpts", "sheets")
        for item in raw.get(key, ())
        if item.get("locator")
    }


def _same_selection(left: RoleSelection, right: RoleSelection) -> bool:
    return bool(
        left.decision == right.decision == "selected"
        and left.selected_candidate_id == right.selected_candidate_id
        and min(left.confidence, right.confidence) >= AUTO_RESOLVE_CONFIDENCE
        and set(left.evidence_locators) == set(right.evidence_locators)
        and _normalized(left.uncertainty) == _normalized(right.uncertainty)
    )


def _same_missing(left: RoleSelection, right: RoleSelection) -> bool:
    return bool(
        left.decision == right.decision == "missing"
        and min(left.confidence, right.confidence) >= AUTO_RESOLVE_CONFIDENCE
        and set(left.evidence_locators) == set(right.evidence_locators)
        and _normalized(left.uncertainty) == _normalized(right.uncertainty)
    )


def _same_role_assessments(
    left_analysis: DocumentAuthorityAnalysis,
    right_analysis: DocumentAuthorityAnalysis,
    role: str,
    candidate_id: str,
) -> bool:
    left_items = {item.candidate_id: item for item in left_analysis.candidate_assessments}
    right_items = {item.candidate_id: item for item in right_analysis.candidate_assessments}
    relevant_ids = {
        item.candidate_id
        for item in (*left_items.values(), *right_items.values())
        if item.candidate_id == candidate_id or item.inferred_role == role
    }
    return all(_same_candidate_assessment(left_items[value], right_items[value]) for value in relevant_ids)


def _same_candidate_assessment(left: CandidateAssessment, right: CandidateAssessment) -> bool:
    return bool(
        left.inferred_role == right.inferred_role
        and left.usable == right.usable
        and _normalized(left.document_version) == _normalized(right.document_version)
        and _normalized(left.document_date) == _normalized(right.document_date)
        and set(left.evidence_locators) == set(right.evidence_locators)
        and _normalized(left.uncertainty) == _normalized(right.uncertainty)
        and min(left.confidence, right.confidence) >= AUTO_RESOLVE_CONFIDENCE
    )


def _role_absent(analysis: DocumentAuthorityAnalysis, role: str) -> bool:
    return not any(item.usable and item.inferred_role == role for item in analysis.candidate_assessments)


def _validate_conflict_decision(
    item: ConflictDecision,
    allowed: set[str],
    candidates: Mapping[str, Mapping[str, Any]],
) -> None:
    if set(item.considered_candidate_ids) != allowed:
        raise DocumentAuthorityError("document_authority_review_coverage_invalid")
    if item.selected_candidate_id and item.selected_candidate_id not in allowed:
        raise DocumentAuthorityError("document_authority_review_candidate_unknown")
    locators_by_candidate = {
        candidate_id: {
            str(evidence["locator"])
            for key in ("excerpts", "sheets")
            for evidence in candidates[candidate_id][key]
            if evidence.get("locator")
        }
        for candidate_id in allowed
    }
    evidence = {(ref.candidate_id, ref.locator) for ref in item.evidence_references}
    if any(
        candidate_id not in allowed
        or locator not in locators_by_candidate[candidate_id]
        for candidate_id, locator in evidence
    ):
        raise DocumentAuthorityError("document_authority_review_evidence_not_closed")
    if any(
        candidate_locators
        and not any(candidate_id == ref_candidate for ref_candidate, _locator in evidence)
        for candidate_id, candidate_locators in locators_by_candidate.items()
    ):
        raise DocumentAuthorityError("document_authority_review_coverage_invalid")
    if item.selected_candidate_id and not any(
        candidate_id == item.selected_candidate_id for candidate_id, _locator in evidence
    ):
        raise DocumentAuthorityError("document_authority_review_evidence_not_closed")


def _same_conflict_selection(left: ConflictDecision, right: ConflictDecision) -> bool:
    return bool(
        left.decision == right.decision == "selected"
        and left.selected_candidate_id == right.selected_candidate_id
        and _normalized(left.document_version) == _normalized(right.document_version)
        and _normalized(left.document_date) == _normalized(right.document_date)
        and set(left.considered_candidate_ids) == set(right.considered_candidate_ids)
        and set(left.evidence_references) == set(right.evidence_references)
        and _normalized(left.uncertainty) == _normalized(right.uncertainty)
        and min(left.confidence, right.confidence) >= AUTO_RESOLVE_CONFIDENCE
    )


def _same_conflict_missing(
    left: ConflictDecision, right: ConflictDecision, allowed: set[str]
) -> bool:
    return bool(
        left.decision == right.decision == "missing"
        and set(left.considered_candidate_ids) == allowed
        and set(right.considered_candidate_ids) == allowed
        and set(left.evidence_references) == set(right.evidence_references)
        and _normalized(left.uncertainty) == _normalized(right.uncertainty)
        and min(left.confidence, right.confidence) >= AUTO_RESOLVE_CONFIDENCE
    )


def _resolved_role(role: str, status: str, candidate_id: str) -> dict[str, str]:
    return {"role": role, "status": status, "candidate_id": candidate_id}


def _review_index(
    review: DocumentAuthorityConflictReview, roles: Sequence[str]
) -> dict[str, ConflictDecision]:
    indexed = {item.role: item for item in review.decisions}
    if set(indexed) != set(roles) or len(indexed) != len(review.decisions):
        raise DocumentAuthorityError("document_authority_review_coverage_invalid")
    return indexed


def _normalized(value: str) -> str:
    return " ".join(value.split()).casefold()


def _digest(value: Any) -> str:
    if isinstance(value, Mapping) and "candidates" in value:
        value = {
            **value,
            "candidates": sorted(
                value.get("candidates", ()),
                key=lambda item: str(item.get("candidate_id") or ""),
            ),
        }
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
