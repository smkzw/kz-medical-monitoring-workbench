from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Literal, Mapping, Sequence, Union

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, field_validator, model_validator

from .mapping_gate import (
    MONITORING_C3_MAPPING_MODEL,
    MONITORING_C3_MAPPING_PROVIDER,
    MONITORING_C3_VERIFIER_MODEL,
    MONITORING_C3_VERIFIER_PROVIDER,
)


DOCUMENT_AUTHORITY_SCHEMA_VERSION = "monitoring-document-authority-v2"
DOCUMENT_ROLES = ("protocol", "investigator_brochure", "ecrf", "sap")
REQUIRED_DOCUMENT_ROLES = frozenset({"protocol", "ecrf"})
AUTO_RESOLVE_CONFIDENCE = 0.9
REVIEW_CONSENSUS_CONFIDENCE = 0.75
MAX_DOCUMENT_AUTHORITY_CANDIDATES = 100
PRIMARY_PROMPT_VERSION = "monitoring-document-authority-primary-v8"
VERIFIER_PROMPT_VERSION = "monitoring-document-authority-verifier-v8"
LEGACY_ANALYSIS_PROMPT_PAIRS = frozenset({
    (
        "monitoring-document-authority-primary-v6",
        "monitoring-document-authority-verifier-v6",
    ),
    (
        "monitoring-document-authority-primary-v7",
        "monitoring-document-authority-verifier-v7",
    ),
})
PRIMARY_REVIEW_PROMPT_VERSION = "monitoring-document-authority-review-primary-v7"
VERIFIER_REVIEW_PROMPT_VERSION = "monitoring-document-authority-review-verifier-v7"
LEGACY_REVIEW_PROMPT_PAIRS = frozenset({
    (
        "monitoring-document-authority-review-primary-v6",
        "monitoring-document-authority-review-verifier-v6",
    )
})
PRIMARY_ADJUDICATION_PROMPT_VERSION = (
    "monitoring-document-authority-adjudication-primary-v7"
)
VERIFIER_ADJUDICATION_PROMPT_VERSION = (
    "monitoring-document-authority-adjudication-verifier-v7"
)
PRIMARY_CRITIQUE_PROMPT_VERSION = "monitoring-document-authority-critique-primary-v1"
VERIFIER_CRITIQUE_PROMPT_VERSION = "monitoring-document-authority-critique-verifier-v1"
FULL_ROLE_REPLAY_ADJUDICATION_PROMPT_PAIRS = frozenset(
    (
        f"monitoring-document-authority-adjudication-primary-v{version}",
        f"monitoring-document-authority-adjudication-verifier-v{version}",
    )
    for version in (2, 3, 4)
)
UNRESOLVED_ROLE_REPLAY_ADJUDICATION_PROMPT_PAIRS = frozenset({
    (
        "monitoring-document-authority-adjudication-primary-v5",
        "monitoring-document-authority-adjudication-verifier-v5",
    ),
    (
        "monitoring-document-authority-adjudication-primary-v6",
        "monitoring-document-authority-adjudication-verifier-v6",
    ),
})
REPLAY_ADJUDICATION_PROMPT_PAIRS = (
    FULL_ROLE_REPLAY_ADJUDICATION_PROMPT_PAIRS
    | UNRESOLVED_ROLE_REPLAY_ADJUDICATION_PROMPT_PAIRS
)
REPLAY_PRIMARY_ADJUDICATION_PROMPT_VERSIONS = frozenset(
    pair[0] for pair in REPLAY_ADJUDICATION_PROMPT_PAIRS
)
REPLAY_VERIFIER_ADJUDICATION_PROMPT_VERSIONS = frozenset(
    pair[1] for pair in REPLAY_ADJUDICATION_PROMPT_PAIRS
)
LEGACY_PRIMARY_ADJUDICATION_PROMPT_VERSION = (
    "monitoring-document-authority-adjudication-primary-v1"
)
LEGACY_VERIFIER_ADJUDICATION_PROMPT_VERSION = (
    "monitoring-document-authority-adjudication-verifier-v1"
)

CURRENT_PROMPT_VERSIONS_BY_TASK = {
    "document_authority_analysis": frozenset(
        {PRIMARY_PROMPT_VERSION, VERIFIER_PROMPT_VERSION}
    ),
    "document_authority_review": frozenset(
        {
            PRIMARY_REVIEW_PROMPT_VERSION,
            VERIFIER_REVIEW_PROMPT_VERSION,
            PRIMARY_ADJUDICATION_PROMPT_VERSION,
            VERIFIER_ADJUDICATION_PROMPT_VERSION,
            PRIMARY_CRITIQUE_PROMPT_VERSION,
            VERIFIER_CRITIQUE_PROMPT_VERSION,
        }
    ),
}
LEGACY_TERMINAL_PROMPT_VERSIONS_BY_TASK = {
    "document_authority_analysis": frozenset(
        version for pair in LEGACY_ANALYSIS_PROMPT_PAIRS for version in pair
    ),
    "document_authority_review": frozenset(
        {
            *(version for pair in LEGACY_REVIEW_PROMPT_PAIRS for version in pair),
            *REPLAY_PRIMARY_ADJUDICATION_PROMPT_VERSIONS,
            *REPLAY_VERIFIER_ADJUDICATION_PROMPT_VERSIONS,
            LEGACY_PRIMARY_ADJUDICATION_PROMPT_VERSION,
            LEGACY_VERIFIER_ADJUDICATION_PROMPT_VERSION,
        }
    )
}

_BATCH_KEYS = frozenset({"manifest_version", "batch_id", "candidates", "authority_status"})
_CANDIDATE_KEYS = frozenset({
    "manifest_version", "candidate_id", "file_id", "filename", "content_sha256",
    "size_bytes", "media_type", "role_hypotheses", "parser_name", "parser_version",
    "technical_status", "content_status", "use_status", "authority_status",
    "extraction_status", "page_count", "locator_count", "locator_index_sha256",
    "excerpts", "sheets", "zero_text_page_count", "zero_text_page_samples",
    "ocr_recovery_pages", "limitation_codes", "evidence_revision_sha256",
    "content_profile",
})
_EXCERPT_KEYS = frozenset({"locator", "text", "text_sha256"})
_OCR_PAGE_KEYS = frozenset({
    "page_number", "dpi", "image_sha256", "locator", "requested_model",
    "actual_model", "provider", "fell_back", "status", "failure_code",
    "text_sha256", "character_count",
})
_SHEET_KEYS = frozenset({
    "locator", "sheet_name", "row_count", "headers", "visibility", "used_range",
    "parser_warnings",
})
_CONTENT_PROFILE_KEYS = frozenset({
    "normalized_text_sha256", "normalized_character_count",
    "represented_locator_count", "represented_page_count", "total_page_count",
    "represented_coverage_per_mille", "fingerprint_sha256",
})
_LEGACY_CONFLICT_PACKET_KEYS = frozenset({
    "schema_version", "batch_id", "input_sha256", "reconciliation_sha256",
    "conflict_roles", "allowed_candidate_ids_by_role", "candidates",
    "candidate_coverage", "conflict_packet_sha256",
})
_CONFLICT_PACKET_KEYS = frozenset({
    *_LEGACY_CONFLICT_PACKET_KEYS,
    "document_relationships",
})
_ADJUDICATION_CONTEXT_V1_KEYS = frozenset({
    "schema_version",
    "conflict_packet_sha256",
    "unresolved_roles",
    "options_by_role",
    "adjudication_context_sha256",
})
_ADJUDICATION_CONTEXT_KEYS = frozenset({
    *_ADJUDICATION_CONTEXT_V1_KEYS,
    "disputed_candidate_ids_by_role",
})
_CRITIQUE_CONTEXT_KEYS = frozenset({
    *_ADJUDICATION_CONTEXT_KEYS,
    "prior_adjudication_context_sha256",
})
_DOCUMENT_VERSION_RE = re.compile(
    r"(?:[Vv](?:ersion)?\s*[0-9]+(?:[._-][0-9A-Za-z]+)*(?:版|版本|稿)?|"
    r"版本(?:号)?[:：]?\s*[0-9]+(?:[._-][0-9A-Za-z]+)*|"
    r"第\s*[0-9]+(?:[._-][0-9A-Za-z]+)*\s*(?:版|版本|稿)|"
    r"[0-9]+(?:[._-][0-9A-Za-z]+)*(?:版|版本|稿)?|"
    r"初稿|终稿|正式版|最终版|修订稿|修订版)",
    re.IGNORECASE,
)
_DOCUMENT_DATE_RE = re.compile(
    r"(?:[0-9]{4}[-/.][0-9]{1,2}[-/.][0-9]{1,2}|"
    r"[0-9]{4}年[0-9]{1,2}月(?:[0-9]{1,2}日)?)"
)
AuthorityUncertainty = Literal[
    "",
    "role_unclear",
    "version_unclear",
    "date_unclear",
    "content_unreadable",
    "evidence_insufficient",
    "multiple_current_candidates",
]


class DocumentAuthorityError(RuntimeError):
    pass


def document_authority_batch_sha256(batch: Mapping[str, Any]) -> str:
    _validate_batch(batch)
    return _digest(batch)


def validate_document_authority_analysis(
    batch: Mapping[str, Any], analysis: "DocumentAuthorityAnalysis"
) -> None:
    candidate_ids, locators, eligible_candidate_ids = _validate_batch(batch)
    _validate_analysis(
        analysis,
        batch_id=str(batch["batch_id"]),
        input_sha256=_digest(batch),
        candidate_ids=candidate_ids,
        locators=locators,
        eligible_candidate_ids=eligible_candidate_ids,
    )


def validate_document_authority_conflict_packet(
    packet: Mapping[str, Any],
) -> str:
    if set(packet) not in {_LEGACY_CONFLICT_PACKET_KEYS, _CONFLICT_PACKET_KEYS}:
        raise DocumentAuthorityError("document_authority_conflict_packet_invalid")
    claimed = str(packet.get("conflict_packet_sha256") or "")
    body = {key: value for key, value in packet.items() if key != "conflict_packet_sha256"}
    if claimed != _digest(body):
        raise DocumentAuthorityError("document_authority_conflict_packet_invalid")
    roles = tuple(str(value) for value in packet.get("conflict_roles", ()))
    candidates = tuple(packet.get("candidates", ()))
    try:
        locator_count_invalid = any(
            int(item.get("locator_count") or 0) < 0
            or (
                int(item.get("locator_count") or 0) == 0
                and bool(_candidate_locators(item))
            )
            for item in candidates
            if isinstance(item, Mapping)
        )
    except (TypeError, ValueError):
        locator_count_invalid = True
    candidate_ids = tuple(
        str(item.get("candidate_id") or "")
        for item in candidates
        if isinstance(item, Mapping)
    )
    expected_allowed = {role: sorted(candidate_ids) for role in roles}
    if (
        not roles
        or not 1 <= len(candidates) <= MAX_DOCUMENT_AUTHORITY_CANDIDATES
        or locator_count_invalid
        or len(roles) != len(set(roles))
        or len(candidate_ids) != len(candidates)
        or any(not value for value in candidate_ids)
        or len(candidate_ids) != len(set(candidate_ids))
        or sorted(candidate_ids) != sorted(packet.get("candidate_coverage", ()))
        or packet.get("allowed_candidate_ids_by_role") != expected_allowed
    ):
        raise DocumentAuthorityError("document_authority_conflict_packet_invalid")
    if "document_relationships" in packet and packet["document_relationships"] != (
        _build_document_relationships(candidates)
    ):
        raise DocumentAuthorityError("document_authority_conflict_packet_invalid")
    return claimed


def validate_document_authority_conflict_review(
    packet: Mapping[str, Any], review: "DocumentAuthorityConflictReview"
) -> None:
    packet_sha256 = validate_document_authority_conflict_packet(packet)
    if review.conflict_packet_sha256 != packet_sha256:
        raise DocumentAuthorityError("document_authority_review_input_mismatch")
    roles = tuple(str(value) for value in packet["conflict_roles"])
    decisions = _review_index(review, roles)
    candidates = {
        str(item["candidate_id"]): item for item in packet["candidates"]
    }
    for role in roles:
        _validate_conflict_decision(
            decisions[role],
            set(packet["allowed_candidate_ids_by_role"][role]),
            candidates,
        )


def validate_document_authority_adjudication_context(
    packet: Mapping[str, Any], context: Mapping[str, Any]
) -> str:
    packet_sha256 = validate_document_authority_conflict_packet(packet)
    schema_version = context.get("schema_version")
    expected_keys = (
        _ADJUDICATION_CONTEXT_V1_KEYS
        if schema_version == "monitoring-document-authority-adjudication-v1"
        else _CRITIQUE_CONTEXT_KEYS
        if schema_version == "monitoring-document-authority-critique-v1"
        else _ADJUDICATION_CONTEXT_KEYS
    )
    if set(context) != expected_keys:
        raise DocumentAuthorityError("document_authority_adjudication_context_invalid")
    claimed = str(context.get("adjudication_context_sha256") or "")
    body = {
        key: value
        for key, value in context.items()
        if key != "adjudication_context_sha256"
    }
    roles = tuple(str(value) for value in context.get("unresolved_roles", ()))
    options = context.get("options_by_role")
    disputed = context.get("disputed_candidate_ids_by_role")
    if (
        schema_version not in {
            "monitoring-document-authority-adjudication-v1",
            "monitoring-document-authority-adjudication-v2",
            "monitoring-document-authority-critique-v1",
        }
        or context.get("conflict_packet_sha256") != packet_sha256
        or (
            schema_version == "monitoring-document-authority-critique-v1"
            and re.fullmatch(
                r"[0-9a-f]{64}",
                str(context.get("prior_adjudication_context_sha256") or ""),
            )
            is None
        )
        or not roles
        or len(roles) != len(set(roles))
        or not set(roles).issubset(packet["conflict_roles"])
        or not isinstance(options, Mapping)
        or set(options) != set(roles)
        or (
            schema_version
            in {
                "monitoring-document-authority-adjudication-v2",
                "monitoring-document-authority-critique-v1",
            }
            and (not isinstance(disputed, Mapping) or set(disputed) != set(roles))
        )
        or claimed != _digest(body)
    ):
        raise DocumentAuthorityError("document_authority_adjudication_context_invalid")
    candidates = {
        str(item["candidate_id"]): item for item in packet["candidates"]
    }
    for role in roles:
        raw_options = options[role]
        if not isinstance(raw_options, Sequence) or isinstance(raw_options, (str, bytes)):
            raise DocumentAuthorityError(
                "document_authority_adjudication_context_invalid"
            )
        try:
            decision_model = (
                AdjudicationDecision
                if schema_version == "monitoring-document-authority-critique-v1"
                else ConflictDecision
            )
            decisions = tuple(decision_model.model_validate(item) for item in raw_options)
        except ValueError as exc:
            raise DocumentAuthorityError(
                "document_authority_adjudication_context_invalid"
            ) from exc
        if len(decisions) != 2 or any(item.role != role for item in decisions):
            raise DocumentAuthorityError(
                "document_authority_adjudication_context_invalid"
            )
        for item in decisions:
            _validate_conflict_decision(
                item,
                set(packet["allowed_candidate_ids_by_role"][role]),
                candidates,
                require_complete_disposition=(
                    schema_version == "monitoring-document-authority-critique-v1"
                ),
                required_evidence_candidate_ids=(
                    set()
                    if schema_version == "monitoring-document-authority-critique-v1"
                    else None
                ),
            )
        left_bound = _decision_bound_candidate_ids(decisions[0])
        right_bound = _decision_bound_candidate_ids(decisions[1])
        expected_disputed = sorted(left_bound ^ right_bound)
        if (
            schema_version
            in {
                "monitoring-document-authority-adjudication-v2",
                "monitoring-document-authority-critique-v1",
            }
            and disputed[role] != expected_disputed
        ):
            raise DocumentAuthorityError(
                "document_authority_adjudication_context_invalid"
            )
        if list(raw_options) != sorted(raw_options, key=_digest):
            raise DocumentAuthorityError(
                "document_authority_adjudication_context_invalid"
            )
    return claimed


def validate_document_authority_adjudication_review(
    packet: Mapping[str, Any],
    context: Mapping[str, Any],
    review: "DocumentAuthorityConflictReview",
    *,
    prompt_version: str | None = None,
) -> None:
    validate_document_authority_adjudication_context(packet, context)
    if context["schema_version"] not in {
        "monitoring-document-authority-adjudication-v2",
        "monitoring-document-authority-critique-v1",
    }:
        validate_document_authority_conflict_review(packet, review)
        return
    if review.conflict_packet_sha256 != packet["conflict_packet_sha256"]:
        raise DocumentAuthorityError("document_authority_review_input_mismatch")
    full_role_replay_prompt_versions = frozenset(
        version
        for pair in FULL_ROLE_REPLAY_ADJUDICATION_PROMPT_PAIRS
        for version in pair
    )
    roles = tuple(
        str(value)
        for value in (
            packet["conflict_roles"]
            if prompt_version in full_role_replay_prompt_versions
            else context["unresolved_roles"]
        )
    )
    decisions = _review_index(review, roles)
    candidates = {
        str(item["candidate_id"]): item for item in packet["candidates"]
    }
    unresolved_roles = set(context["unresolved_roles"])
    focused_evidence_candidate_ids = _focused_adjudication_candidate_ids_by_role(
        context, unresolved_roles
    )
    for role in roles:
        decision = decisions[role]
        _validate_conflict_decision(
            decision,
            set(packet["allowed_candidate_ids_by_role"][role]),
            candidates,
            require_complete_disposition=role in unresolved_roles,
            required_evidence_candidate_ids=(
                focused_evidence_candidate_ids[role]
                if role in unresolved_roles
                else None
            ),
        )
        if prompt_version in {
            PRIMARY_ADJUDICATION_PROMPT_VERSION,
            VERIFIER_ADJUDICATION_PROMPT_VERSION,
            PRIMARY_CRITIQUE_PROMPT_VERSION,
            VERIFIER_CRITIQUE_PROMPT_VERSION,
        }:
            if not isinstance(decision, AdjudicationDecision) or not (
                decision.rationale.strip()
            ):
                raise DocumentAuthorityError(
                    "document_authority_adjudication_rationale_missing"
                )
            for reference in decision.counter_evidence_references:
                if (
                    reference.candidate_id not in candidates
                    or reference.locator
                    not in _candidate_locators(candidates[reference.candidate_id])
                ):
                    raise DocumentAuthorityError(
                        "document_authority_evidence_not_closed"
                    )


def _focused_adjudication_candidate_ids_by_role(
    context: Mapping[str, Any], roles: Sequence[str]
) -> dict[str, set[str]]:
    return {
        role: {
            str(candidate_id)
            for option in context["options_by_role"][role]
            for candidate_id in (
                option.get("selected_candidate_id"),
                *(option.get("supplementary_candidate_ids") or ()),
                *(context["disputed_candidate_ids_by_role"].get(role) or ()),
            )
            if candidate_id
        }
        for role in roles
    }


def _validate_nonempty_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    cleaned = tuple(value.strip() for value in values)
    if any(not value for value in cleaned) or len(cleaned) != len(set(cleaned)):
        raise ValueError("values must be non-empty and unique")
    return cleaned


def _validate_document_version(value: str) -> str:
    if value and (value != value.strip() or not _DOCUMENT_VERSION_RE.fullmatch(value)):
        raise ValueError("document version must be a controlled version identifier")
    return value


def _validate_document_date(value: str) -> str:
    if value and (value != value.strip() or not _DOCUMENT_DATE_RE.fullmatch(value)):
        raise ValueError("document date must be a controlled date identifier")
    return value


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
    uncertainty: AuthorityUncertainty = ""

    _locators = field_validator("evidence_locators")(_validate_nonempty_unique)
    _version = field_validator("document_version")(_validate_document_version)
    _date = field_validator("document_date")(_validate_document_date)


class RoleSupplementaryBinding(BaseModel):
    """One valid supplementary file bound under a role's primary selection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=2, max_length=160)
    evidence_locators: tuple[str, ...] = Field(min_length=1, max_length=20)

    _locators = field_validator("evidence_locators")(_validate_nonempty_unique)


class RoleSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["protocol", "investigator_brochure", "ecrf", "sap"]
    decision: Literal["selected", "missing", "unresolved"]
    selected_candidate_id: str = Field(default="", max_length=160)
    confidence: StrictFloat = Field(ge=0, le=1)
    evidence_locators: tuple[str, ...] = Field(default=(), max_length=20)
    supplementary_bindings: tuple[RoleSupplementaryBinding, ...] = Field(
        max_length=20
    )
    uncertainty: AuthorityUncertainty = ""

    _locators = field_validator("evidence_locators")(_validate_nonempty_unique)

    @field_validator("supplementary_bindings")
    @classmethod
    def _supplementary_ids(cls, value: tuple[RoleSupplementaryBinding, ...]) -> tuple[RoleSupplementaryBinding, ...]:
        _validate_nonempty_unique(tuple(item.candidate_id for item in value))
        return value

    @model_validator(mode="after")
    def validate_selection(self) -> "RoleSelection":
        if (self.decision == "selected") != bool(self.selected_candidate_id.strip()):
            raise ValueError("selected decision and candidate ID must agree")
        if self.decision == "selected" and not self.evidence_locators:
            raise ValueError("selected document requires locator evidence")
        if self.decision != "selected" and self.evidence_locators:
            raise ValueError("non-selected role cannot carry unbound evidence")
        if self.decision != "selected" and self.supplementary_bindings:
            raise ValueError("non-selected role cannot bind supplementary files")
        if any(
            item.candidate_id == self.selected_candidate_id
            for item in self.supplementary_bindings
        ):
            raise ValueError("supplementary candidate cannot duplicate the primary file")
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
    job_input_revision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
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
    considered_candidate_ids: tuple[str, ...] = Field(
        default=(), max_length=MAX_DOCUMENT_AUTHORITY_CANDIDATES
    )
    supplementary_candidate_ids: tuple[str, ...] = Field(max_length=20)
    evidence_references: tuple[EvidenceReference, ...] = Field(
        default=(), max_length=MAX_DOCUMENT_AUTHORITY_CANDIDATES
    )
    uncertainty: AuthorityUncertainty = ""

    _candidates = field_validator("considered_candidate_ids")(_validate_nonempty_unique)
    _supplementary = field_validator("supplementary_candidate_ids")(_validate_nonempty_unique)
    _version = field_validator("document_version")(_validate_document_version)
    _date = field_validator("document_date")(_validate_document_date)

    @model_validator(mode="after")
    def validate_decision(self) -> "ConflictDecision":
        if (self.decision == "selected") != bool(self.selected_candidate_id.strip()):
            raise ValueError("selected decision and candidate ID must agree")
        if self.decision != "selected" and self.supplementary_candidate_ids:
            raise ValueError("non-selected decision cannot bind supplementary files")
        if self.selected_candidate_id in self.supplementary_candidate_ids:
            raise ValueError("supplementary candidate cannot duplicate the primary file")
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


class AdjudicationDecision(ConflictDecision):
    excluded_candidate_ids: tuple[str, ...] = Field(
        max_length=MAX_DOCUMENT_AUTHORITY_CANDIDATES
    )
    rationale: str = Field(default="", max_length=1200)
    counter_evidence_references: tuple[EvidenceReference, ...] = Field(
        default=(), max_length=20
    )

    _excluded = field_validator("excluded_candidate_ids")(_validate_nonempty_unique)

    @model_validator(mode="after")
    def validate_exclusions(self) -> "AdjudicationDecision":
        if set(self.excluded_candidate_ids) & _decision_bound_candidate_ids(self):
            raise ValueError("excluded candidates cannot also be bound")
        counter_keys = {
            (item.candidate_id, item.locator)
            for item in self.counter_evidence_references
        }
        if len(counter_keys) != len(self.counter_evidence_references):
            raise ValueError("counter evidence references must be unique")
        return self


class DocumentAuthorityAdjudicationReview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[DOCUMENT_AUTHORITY_SCHEMA_VERSION]
    conflict_packet_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    decisions: tuple[AdjudicationDecision, ...]


class DocumentAuthorityConflictRunEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(min_length=2, max_length=160)
    job_id: str = Field(min_length=2, max_length=160)
    role: Literal["primary", "verifier"]
    provider: str
    model: str
    prompt_version: str
    conflict_packet_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    job_input_revision_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    review: Union[
        DocumentAuthorityAdjudicationReview,
        DocumentAuthorityConflictReview,
    ]

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
    supplementary_candidate_ids: tuple[str, ...] = Field(default=(), max_length=20)

    _supplementary = field_validator("supplementary_candidate_ids")(_validate_nonempty_unique)

    @model_validator(mode="after")
    def validate_candidate(self) -> "ResolvedRole":
        if (self.status == "selected") != bool(self.candidate_id.strip()):
            raise ValueError("resolved status and candidate must agree")
        if self.status != "selected" and self.supplementary_candidate_ids:
            raise ValueError("non-selected role cannot carry supplementary files")
        if self.candidate_id in self.supplementary_candidate_ids:
            raise ValueError("supplementary candidate cannot duplicate the primary file")
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
    candidate_ids, locators, eligible_candidate_ids = _validate_batch(batch)
    input_sha256 = _digest(batch)
    _validate_run_pair(primary, verifier, input_sha256, stage="analysis")
    for run in (primary, verifier):
        _validate_analysis(
            run.analysis,
            batch_id=str(batch["batch_id"]),
            input_sha256=input_sha256,
            candidate_ids=candidate_ids,
            locators=locators,
            eligible_candidate_ids=eligible_candidate_ids,
        )

    left_roles = {item.role: item for item in primary.analysis.role_selections}
    right_roles = {item.role: item for item in verifier.analysis.role_selections}
    resolved: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for role in DOCUMENT_ROLES:
        left, right = left_roles[role], right_roles[role]
        if _same_selection(left, right) and _same_role_assessments(
            primary.analysis, verifier.analysis, role, left.selected_candidate_id
        ):
            resolved.append(_resolved_role(
                role,
                "selected",
                left.selected_candidate_id,
                tuple(item.candidate_id for item in left.supplementary_bindings),
            ))
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
                    candidate_id
                    for item in (left, right)
                    for candidate_id in (
                        item.selected_candidate_id,
                        *(binding.candidate_id for binding in item.supplementary_bindings),
                    )
                    if candidate_id
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
    candidate_ids, _locators, _eligible_candidate_ids = _validate_batch(batch)
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
    if any(candidate.get("content_profile") for candidate in candidates):
        packet["document_relationships"] = _build_document_relationships(candidates)
    return {**packet, "conflict_packet_sha256": _digest(packet)}


def build_anonymous_adjudication_context(
    batch: Mapping[str, Any],
    analysis_primary: DocumentAuthorityRunEnvelope,
    analysis_verifier: DocumentAuthorityRunEnvelope,
    conflict_packet: Mapping[str, Any],
    review_primary: DocumentAuthorityConflictRunEnvelope,
    review_verifier: DocumentAuthorityConflictRunEnvelope,
    *,
    legacy_v1: bool = False,
) -> dict[str, Any]:
    resolution = resolve_document_authority_conflicts(
        batch,
        analysis_primary,
        analysis_verifier,
        conflict_packet,
        review_primary,
        review_verifier,
    )
    unresolved = tuple(resolution["unresolved_roles"])
    if not unresolved:
        raise DocumentAuthorityError("document_authority_adjudication_not_required")
    roles = tuple(str(value) for value in conflict_packet["conflict_roles"])
    left = _review_index(review_primary.review, roles)
    right = _review_index(review_verifier.review, roles)
    options = {
        role: sorted(
            (
                left[role].model_dump(mode="json"),
                right[role].model_dump(mode="json"),
            ),
            key=_digest,
        )
        for role in unresolved
    }
    disputed = {
        role: sorted(
            _decision_bound_candidate_ids(left[role])
            ^ _decision_bound_candidate_ids(right[role])
        )
        for role in unresolved
    }
    context = {
        "schema_version": (
            "monitoring-document-authority-adjudication-v1"
            if legacy_v1
            else "monitoring-document-authority-adjudication-v2"
        ),
        "conflict_packet_sha256": conflict_packet["conflict_packet_sha256"],
        "unresolved_roles": list(unresolved),
        "options_by_role": options,
    }
    if not legacy_v1:
        context["disputed_candidate_ids_by_role"] = disputed
    output = {**context, "adjudication_context_sha256": _digest(context)}
    validate_document_authority_adjudication_context(conflict_packet, output)
    return output


def build_anonymous_critique_context(
    batch: Mapping[str, Any],
    analysis_primary: DocumentAuthorityRunEnvelope,
    analysis_verifier: DocumentAuthorityRunEnvelope,
    conflict_packet: Mapping[str, Any],
    review_primary: DocumentAuthorityConflictRunEnvelope,
    review_verifier: DocumentAuthorityConflictRunEnvelope,
    adjudication_context: Mapping[str, Any],
    adjudication_primary: DocumentAuthorityConflictRunEnvelope,
    adjudication_verifier: DocumentAuthorityConflictRunEnvelope,
) -> dict[str, Any]:
    resolution = resolve_document_authority_adjudication(
        batch,
        analysis_primary,
        analysis_verifier,
        conflict_packet,
        review_primary,
        review_verifier,
        adjudication_context,
        adjudication_primary,
        adjudication_verifier,
    )
    roles = tuple(str(value) for value in resolution["unresolved_roles"])
    if not roles:
        raise DocumentAuthorityError("document_authority_critique_not_required")
    left = _review_index(adjudication_primary.review, roles)
    right = _review_index(adjudication_verifier.review, roles)
    options = {
        role: sorted(
            (
                left[role].model_dump(mode="json"),
                right[role].model_dump(mode="json"),
            ),
            key=_digest,
        )
        for role in roles
    }
    context = {
        "schema_version": "monitoring-document-authority-critique-v1",
        "conflict_packet_sha256": conflict_packet["conflict_packet_sha256"],
        "prior_adjudication_context_sha256": adjudication_context[
            "adjudication_context_sha256"
        ],
        "unresolved_roles": list(roles),
        "options_by_role": options,
        "disputed_candidate_ids_by_role": {
            role: sorted(
                _decision_bound_candidate_ids(left[role])
                ^ _decision_bound_candidate_ids(right[role])
            )
            for role in roles
        },
    }
    output = {**context, "adjudication_context_sha256": _digest(context)}
    validate_document_authority_adjudication_context(conflict_packet, output)
    return output


def resolve_document_authority_conflicts(
    batch: Mapping[str, Any],
    analysis_primary: DocumentAuthorityRunEnvelope,
    analysis_verifier: DocumentAuthorityRunEnvelope,
    conflict_packet: Mapping[str, Any],
    primary: DocumentAuthorityConflictRunEnvelope,
    verifier: DocumentAuthorityConflictRunEnvelope,
) -> dict[str, Any]:
    if len({
        analysis_primary.job_input_revision_sha256,
        analysis_verifier.job_input_revision_sha256,
        primary.job_input_revision_sha256,
        verifier.job_input_revision_sha256,
    }) != 1:
        raise DocumentAuthorityError("document_authority_input_revision_mismatch")
    reconciliation = reconcile_document_authority(
        batch, analysis_primary, analysis_verifier
    )
    expected_packet = build_anonymous_conflict_packet(
        batch, analysis_primary, analysis_verifier
    )
    if conflict_packet != expected_packet:
        raise DocumentAuthorityError("document_authority_conflict_packet_tampered")
    expected_hash = str(conflict_packet["conflict_packet_sha256"])
    _validate_run_pair(primary, verifier, expected_hash, stage="review")
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
            resolved.append(_resolved_role(
                role,
                "selected",
                left_item.selected_candidate_id,
                left_item.supplementary_candidate_ids,
            ))
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
            "现有文件仍无法明确区分版本或签署状态，请一次重新选择完整研究文件。"
            if unresolved else ""
        ),
        "review_run_ids": sorted((primary.run_id, verifier.run_id)),
    }


def resolve_document_authority_adjudication(
    batch: Mapping[str, Any],
    analysis_primary: DocumentAuthorityRunEnvelope,
    analysis_verifier: DocumentAuthorityRunEnvelope,
    conflict_packet: Mapping[str, Any],
    review_primary: DocumentAuthorityConflictRunEnvelope,
    review_verifier: DocumentAuthorityConflictRunEnvelope,
    adjudication_context: Mapping[str, Any],
    adjudication_primary: DocumentAuthorityConflictRunEnvelope,
    adjudication_verifier: DocumentAuthorityConflictRunEnvelope,
) -> dict[str, Any]:
    if len({
        analysis_primary.job_input_revision_sha256,
        analysis_verifier.job_input_revision_sha256,
        review_primary.job_input_revision_sha256,
        review_verifier.job_input_revision_sha256,
        adjudication_primary.job_input_revision_sha256,
        adjudication_verifier.job_input_revision_sha256,
    }) != 1:
        raise DocumentAuthorityError("document_authority_input_revision_mismatch")
    expected_context = build_anonymous_adjudication_context(
        batch,
        analysis_primary,
        analysis_verifier,
        conflict_packet,
        review_primary,
        review_verifier,
        legacy_v1=(
            adjudication_context.get("schema_version")
            == "monitoring-document-authority-adjudication-v1"
        ),
    )
    if adjudication_context != expected_context:
        raise DocumentAuthorityError("document_authority_adjudication_context_tampered")
    expected_hash = str(conflict_packet["conflict_packet_sha256"])
    prompt_pair = (
        adjudication_primary.prompt_version,
        adjudication_verifier.prompt_version,
    )
    _validate_run_pair(
        adjudication_primary,
        adjudication_verifier,
        expected_hash,
        stage=(
            "legacy_adjudication"
            if adjudication_context.get("schema_version")
            == "monitoring-document-authority-adjudication-v1"
            else "previous_adjudication"
            if prompt_pair in REPLAY_ADJUDICATION_PROMPT_PAIRS
            else "adjudication"
        ),
    )
    for run in (adjudication_primary, adjudication_verifier):
        validate_document_authority_adjudication_review(
            conflict_packet,
            adjudication_context,
            run.review,
            prompt_version=run.prompt_version,
        )

    initial = resolve_document_authority_conflicts(
        batch,
        analysis_primary,
        analysis_verifier,
        conflict_packet,
        review_primary,
        review_verifier,
    )
    full_role_replay_pair = (
        prompt_pair in FULL_ROLE_REPLAY_ADJUDICATION_PROMPT_PAIRS
    )
    output_roles = tuple(
        str(value)
        for value in (
            conflict_packet["conflict_roles"]
            if adjudication_context["schema_version"]
            == "monitoring-document-authority-adjudication-v1"
            or full_role_replay_pair
            else adjudication_context["unresolved_roles"]
        )
    )
    left = _review_index(adjudication_primary.review, output_roles)
    right = _review_index(adjudication_verifier.review, output_roles)
    candidates = {
        str(item["candidate_id"]): item for item in conflict_packet["candidates"]
    }
    resolved = list(initial["resolved_roles"])
    unresolved: list[str] = []
    focused_evidence_candidate_ids = (
        _focused_adjudication_candidate_ids_by_role(
            adjudication_context, initial["unresolved_roles"]
        )
        if adjudication_context["schema_version"]
        == "monitoring-document-authority-adjudication-v2"
        else None
    )
    for role in initial["unresolved_roles"]:
        allowed = set(conflict_packet["allowed_candidate_ids_by_role"][role])
        for item in (left[role], right[role]):
            _validate_conflict_decision(
                item,
                allowed,
                candidates,
                required_evidence_candidate_ids=(
                    focused_evidence_candidate_ids[role]
                    if focused_evidence_candidate_ids is not None
                    else None
                ),
            )
        if _same_conflict_selection(left[role], right[role]):
            resolved.append(_resolved_role(
                role,
                "selected",
                left[role].selected_candidate_id,
                left[role].supplementary_candidate_ids,
            ))
        elif role not in REQUIRED_DOCUMENT_ROLES and _same_conflict_missing(
            left[role], right[role], allowed
        ):
            resolved.append(_resolved_role(role, "missing", ""))
        else:
            unresolved.append(role)
    return {
        "schema_version": DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        "batch_id": initial["batch_id"],
        "state": "needs_user_input" if unresolved else "resolved",
        "resolved_roles": sorted(
            resolved, key=lambda item: DOCUMENT_ROLES.index(item["role"])
        ),
        "unresolved_roles": unresolved,
        "user_question": (
            "现有文件仍无法明确区分版本或签署状态，请一次重新选择完整研究文件。"
            if unresolved else ""
        ),
        "review_run_ids": initial["review_run_ids"],
        "adjudication_run_ids": sorted(
            (adjudication_primary.run_id, adjudication_verifier.run_id)
        ),
    }


def resolve_document_authority_critique(
    batch: Mapping[str, Any],
    analysis_primary: DocumentAuthorityRunEnvelope,
    analysis_verifier: DocumentAuthorityRunEnvelope,
    conflict_packet: Mapping[str, Any],
    review_primary: DocumentAuthorityConflictRunEnvelope,
    review_verifier: DocumentAuthorityConflictRunEnvelope,
    adjudication_context: Mapping[str, Any],
    adjudication_primary: DocumentAuthorityConflictRunEnvelope,
    adjudication_verifier: DocumentAuthorityConflictRunEnvelope,
    critique_context: Mapping[str, Any],
    critique_primary: DocumentAuthorityConflictRunEnvelope,
    critique_verifier: DocumentAuthorityConflictRunEnvelope,
) -> dict[str, Any]:
    initial = resolve_document_authority_adjudication(
        batch,
        analysis_primary,
        analysis_verifier,
        conflict_packet,
        review_primary,
        review_verifier,
        adjudication_context,
        adjudication_primary,
        adjudication_verifier,
    )
    expected_context = build_anonymous_critique_context(
        batch,
        analysis_primary,
        analysis_verifier,
        conflict_packet,
        review_primary,
        review_verifier,
        adjudication_context,
        adjudication_primary,
        adjudication_verifier,
    )
    if critique_context != expected_context:
        raise DocumentAuthorityError("document_authority_critique_context_tampered")
    packet_hash = str(conflict_packet["conflict_packet_sha256"])
    _validate_run_pair(
        critique_primary, critique_verifier, packet_hash, stage="critique"
    )
    for run in (critique_primary, critique_verifier):
        validate_document_authority_adjudication_review(
            conflict_packet,
            critique_context,
            run.review,
            prompt_version=run.prompt_version,
        )
    roles = tuple(str(value) for value in initial["unresolved_roles"])
    left = _review_index(critique_primary.review, roles)
    right = _review_index(critique_verifier.review, roles)
    candidates = {
        str(item["candidate_id"]): item for item in conflict_packet["candidates"]
    }
    focused_by_role = _focused_adjudication_candidate_ids_by_role(
        critique_context, roles
    )
    resolved = list(initial["resolved_roles"])
    unresolved: list[str] = []
    for role in roles:
        allowed = set(conflict_packet["allowed_candidate_ids_by_role"][role])
        for item in (left[role], right[role]):
            _validate_conflict_decision(
                item,
                allowed,
                candidates,
                require_complete_disposition=True,
                required_evidence_candidate_ids=focused_by_role[role],
            )
        if _same_conflict_selection(left[role], right[role]):
            resolved.append(_resolved_role(
                role,
                "selected",
                left[role].selected_candidate_id,
                left[role].supplementary_candidate_ids,
            ))
        elif role not in REQUIRED_DOCUMENT_ROLES and _same_conflict_missing(
            left[role], right[role], allowed
        ):
            resolved.append(_resolved_role(role, "missing", ""))
        else:
            unresolved.append(role)
    evidence_candidate_ids = {
        candidate_id
        for role in unresolved
        for candidate_id in (
            focused_by_role[role]
            | _decision_bound_candidate_ids(left[role])
            | _decision_bound_candidate_ids(right[role])
        )
    }
    evidence_complete = bool(evidence_candidate_ids) and all(
        _candidate_profile_complete(candidates[candidate_id])
        for candidate_id in evidence_candidate_ids
    )
    attention_files = sorted({
        str(candidates[candidate_id]["filename"])
        for candidate_id in evidence_candidate_ids
    })
    state = (
        "resolved"
        if not unresolved
        else "needs_user_input"
        if evidence_complete
        else "evidence_incomplete"
    )
    return {
        "schema_version": DOCUMENT_AUTHORITY_SCHEMA_VERSION,
        "batch_id": initial["batch_id"],
        "state": state,
        "resolved_roles": sorted(
            resolved, key=lambda item: DOCUMENT_ROLES.index(item["role"])
        ),
        "unresolved_roles": unresolved,
        "attention_files": attention_files,
        "user_question": (
            f"仅需确认：{'、'.join(attention_files)} 中，哪些是当前主文件"
            "或必须与主文件一起阅读的补充文件？"
            if state == "needs_user_input"
            else ""
        ),
        "review_run_ids": initial["review_run_ids"],
        "adjudication_run_ids": initial["adjudication_run_ids"],
        "critique_run_ids": sorted((critique_primary.run_id, critique_verifier.run_id)),
    }


def _candidate_profile_complete(candidate: Mapping[str, Any]) -> bool:
    profile = candidate.get("content_profile")
    return bool(
        isinstance(profile, Mapping)
        and int(profile.get("normalized_character_count") or 0) > 0
        and int(profile.get("represented_coverage_per_mille") or 0) == 1000
    )


def _validate_batch(
    batch: Mapping[str, Any],
) -> tuple[set[str], dict[str, set[str]], set[str]]:
    if (
        set(batch) - _BATCH_KEYS
        or batch.get("manifest_version") != "monitoring-document-candidate-v1"
        or batch.get("authority_status") != "not_adjudicated"
    ):
        raise DocumentAuthorityError("document_authority_batch_invalid")
    raw_candidates = tuple(batch.get("candidates", ()))
    if not 1 <= len(raw_candidates) <= MAX_DOCUMENT_AUTHORITY_CANDIDATES:
        raise DocumentAuthorityError("document_authority_candidate_coverage_invalid")
    candidate_ids: set[str] = set()
    locators: dict[str, set[str]] = {}
    eligible_candidate_ids: set[str] = set()
    for raw in raw_candidates:
        if set(raw) - _CANDIDATE_KEYS:
            raise DocumentAuthorityError("document_authority_candidate_shape_invalid")
        if raw.get("authority_status") not in {None, "not_promoted"}:
            raise DocumentAuthorityError("document_authority_candidate_shape_invalid")
        candidate_id = str(raw.get("candidate_id") or "")
        if not candidate_id or candidate_id in candidate_ids:
            raise DocumentAuthorityError("document_authority_candidate_coverage_invalid")
        candidate_ids.add(candidate_id)
        candidate_locator_list = _candidate_locator_list(raw)
        candidate_locators = set(candidate_locator_list)
        evidence_revision = str(raw.get("evidence_revision_sha256") or "")
        if evidence_revision and len(candidate_locators) != len(candidate_locator_list):
            raise DocumentAuthorityError(
                "document_authority_candidate_locator_count_invalid"
            )
        locator_count = int(raw.get("locator_count") or 0)
        if (
            locator_count < len(candidate_locators)
            or (evidence_revision and locator_count != len(candidate_locators))
        ):
            raise DocumentAuthorityError(
                "document_authority_candidate_locator_count_invalid"
            )
        if evidence_revision:
            if str(raw.get("locator_index_sha256") or "") != _digest(
                candidate_locator_list
            ):
                raise DocumentAuthorityError(
                    "document_authority_candidate_locator_index_invalid"
                )
            for excerpt in raw.get("excerpts", ()):
                text = str(excerpt.get("text") or "")
                if str(excerpt.get("text_sha256") or "") != hashlib.sha256(
                    text.encode("utf-8")
                ).hexdigest():
                    raise DocumentAuthorityError(
                        "document_authority_candidate_excerpt_hash_invalid"
                    )
            _validate_candidate_content_profile(raw.get("content_profile"))
        _validate_candidate_ocr_evidence(raw, candidate_locators)
        if evidence_revision:
            page_count = int(raw.get("page_count") or 0)
            zero_text_page_count = int(raw.get("zero_text_page_count") or 0)
            zero_text_page_samples = tuple(raw.get("zero_text_page_samples", ()))
            if (
                zero_text_page_count < 0
                or zero_text_page_count > page_count
                or any(
                    not isinstance(page_number, int)
                    or isinstance(page_number, bool)
                    or page_number <= 0
                    or page_number > page_count
                    for page_number in zero_text_page_samples
                )
                or len(set(zero_text_page_samples)) != len(zero_text_page_samples)
                or len(zero_text_page_samples) > zero_text_page_count
            ):
                raise DocumentAuthorityError(
                    "document_authority_candidate_ocr_evidence_invalid"
                )
            ocr_pages = tuple(raw.get("ocr_recovery_pages", ()))
            recovered_pages = {
                int(item.get("page_number") or 0)
                for item in ocr_pages
                if item.get("status") == "recovered"
            }
            if not {
                int(item.get("page_number") or 0) for item in ocr_pages
            }.issubset(set(zero_text_page_samples)):
                raise DocumentAuthorityError(
                    "document_authority_candidate_ocr_evidence_invalid"
                )
            ocr_complete = (
                zero_text_page_count > 0
                and len(zero_text_page_samples) == zero_text_page_count
                and recovered_pages == set(zero_text_page_samples)
                and len(ocr_pages) == zero_text_page_count
            )
            if (zero_text_page_count or ocr_pages) and raw.get(
                "extraction_status"
            ) != ("parsed" if ocr_complete else "needs_ocr"):
                raise DocumentAuthorityError(
                    "document_authority_candidate_ocr_status_invalid"
                )
        if evidence_revision:
            revision_body = dict(raw)
            revision_body.pop("evidence_revision_sha256", None)
            if evidence_revision != _digest(revision_body):
                raise DocumentAuthorityError(
                    "document_authority_candidate_evidence_revision_invalid"
                )
        locators[candidate_id] = candidate_locators
        if (
            raw.get("technical_status") == "ready"
            and raw.get("extraction_status") == "parsed"
        ):
            eligible_candidate_ids.add(candidate_id)
    return candidate_ids, locators, eligible_candidate_ids


def _validate_candidate_content_profile(profile: Any) -> None:
    if profile is None:
        return
    fingerprints = tuple(profile.get("fingerprint_sha256", ())) if isinstance(
        profile, Mapping
    ) else ()
    if (
        not isinstance(profile, Mapping)
        or set(profile) != _CONTENT_PROFILE_KEYS
        or re.fullmatch(
            r"[0-9a-f]{64}", str(profile.get("normalized_text_sha256") or "")
        ) is None
        or any(
            re.fullmatch(r"[0-9a-f]{64}", str(value)) is None
            for value in fingerprints
        )
        or list(fingerprints) != sorted(set(fingerprints))
        or len(fingerprints) > 128
        or any(
            not isinstance(profile.get(key), int)
            or isinstance(profile.get(key), bool)
            or int(profile[key]) < 0
            for key in (
                "normalized_character_count",
                "represented_locator_count",
                "represented_page_count",
                "total_page_count",
                "represented_coverage_per_mille",
            )
        )
        or int(profile["represented_coverage_per_mille"]) > 1000
        or int(profile["represented_page_count"]) > int(profile["total_page_count"])
        and int(profile["total_page_count"]) > 0
    ):
        raise DocumentAuthorityError(
            "document_authority_candidate_content_profile_invalid"
        )


def _validate_candidate_ocr_evidence(
    raw: Mapping[str, Any], candidate_locators: set[str]
) -> None:
    excerpts = {
        str(item.get("locator") or ""): item
        for item in raw.get("excerpts", ())
        if item.get("locator")
    }
    seen_pages: set[int] = set()
    empty_hash = hashlib.sha256(b"").hexdigest()
    for item in raw.get("ocr_recovery_pages", ()):
        if set(item) != _OCR_PAGE_KEYS:
            raise DocumentAuthorityError(
                "document_authority_candidate_ocr_evidence_invalid"
            )
        page_number = int(item.get("page_number") or 0)
        status = str(item.get("status") or "")
        locator = str(item.get("locator") or "")
        text_sha256 = str(item.get("text_sha256") or "")
        character_count = int(item.get("character_count") or 0)
        requested_model = item.get("requested_model")
        actual_model = str(item.get("actual_model") or "")
        fell_back = item.get("fell_back")
        if (
            page_number <= 0
            or page_number in seen_pages
            or int(item.get("dpi") or 0) < 200
            or re.fullmatch(r"[0-9a-f]{64}", str(item.get("image_sha256") or ""))
            is None
            or re.fullmatch(r"[0-9a-f]{64}", text_sha256) is None
            or status not in {"recovered", "empty", "failed"}
            or not isinstance(requested_model, str)
            or not requested_model.strip()
            or not isinstance(fell_back, bool)
        ):
            raise DocumentAuthorityError(
                "document_authority_candidate_ocr_evidence_invalid"
            )
        seen_pages.add(page_number)
        if status == "recovered":
            excerpt = excerpts.get(locator)
            expected_locator = (
                f"candidate:{raw.get('candidate_id')}:p{page_number}:ocr"
            )
            if (
                not locator
                or locator != expected_locator
                or locator not in candidate_locators
                or excerpt is None
                or text_sha256 != str(excerpt.get("text_sha256") or "")
                or text_sha256
                != hashlib.sha256(
                    str(excerpt.get("text") or "").encode("utf-8")
                ).hexdigest()
                or character_count != len(str(excerpt.get("text") or ""))
                or item.get("failure_code")
                or not actual_model
            ):
                raise DocumentAuthorityError(
                    "document_authority_candidate_ocr_evidence_invalid"
                )
        else:
            invalid_status_provenance = (
                status == "failed" and (actual_model or fell_back is not False)
            ) or (status == "empty" and (not actual_model or item.get("failure_code")))
            if (
                locator
                or character_count != 0
                or text_sha256 != empty_hash
                or (status == "failed") != (
                    item.get("failure_code") == "ocr_runtime_unavailable"
                )
                or invalid_status_provenance
            ):
                raise DocumentAuthorityError(
                    "document_authority_candidate_ocr_evidence_invalid"
                )


def _validate_analysis(
    analysis: DocumentAuthorityAnalysis,
    *, batch_id: str, input_sha256: str,
    candidate_ids: set[str], locators: Mapping[str, set[str]],
    eligible_candidate_ids: set[str],
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
        if assessment.usable and assessment.candidate_id not in eligible_candidate_ids:
            raise DocumentAuthorityError("document_authority_candidate_not_usable")
    for selection in selections.values():
        candidate_id = selection.selected_candidate_id
        if candidate_id and candidate_id not in candidate_ids:
            raise DocumentAuthorityError("document_authority_selection_unknown")
        if candidate_id and not set(selection.evidence_locators).issubset(locators[candidate_id]):
            raise DocumentAuthorityError("document_authority_evidence_not_closed")
        assessment = assessments.get(candidate_id)
        if assessment and (not assessment.usable or assessment.inferred_role != selection.role):
            raise DocumentAuthorityError("document_authority_selection_inconsistent")
        for binding in selection.supplementary_bindings:
            if binding.candidate_id not in candidate_ids:
                raise DocumentAuthorityError("document_authority_selection_unknown")
            if not set(binding.evidence_locators).issubset(locators[binding.candidate_id]):
                raise DocumentAuthorityError("document_authority_evidence_not_closed")
            supplement = assessments.get(binding.candidate_id)
            if (
                supplement is None
                or not supplement.usable
                or supplement.inferred_role != selection.role
            ):
                raise DocumentAuthorityError("document_authority_selection_inconsistent")
        if selection.decision == "missing" and not _role_absent(analysis, selection.role):
            raise DocumentAuthorityError("document_authority_missing_not_proven")


def _validate_run_pair(
    left: Any,
    right: Any,
    input_hash: str,
    *,
    stage: Literal[
        "analysis",
        "review",
        "adjudication",
        "critique",
        "previous_adjudication",
        "legacy_adjudication",
    ],
) -> None:
    if left.run_id == right.run_id or left.job_id == right.job_id:
        raise DocumentAuthorityError("document_authority_runs_not_independent")
    if left.job_input_revision_sha256 != right.job_input_revision_sha256:
        raise DocumentAuthorityError("document_authority_input_revision_mismatch")
    previous_prompt_pair = (left.prompt_version, right.prompt_version)
    analysis_prompt_pairs = {
        (PRIMARY_PROMPT_VERSION, VERIFIER_PROMPT_VERSION),
        *LEGACY_ANALYSIS_PROMPT_PAIRS,
    }
    if stage == "analysis" and previous_prompt_pair not in analysis_prompt_pairs:
        raise DocumentAuthorityError("document_authority_run_identity_invalid")
    if stage == "review" and previous_prompt_pair not in {
        (PRIMARY_REVIEW_PROMPT_VERSION, VERIFIER_REVIEW_PROMPT_VERSION),
        *LEGACY_REVIEW_PROMPT_PAIRS,
    }:
        raise DocumentAuthorityError("document_authority_run_identity_invalid")
    if (
        stage == "previous_adjudication"
        and previous_prompt_pair not in REPLAY_ADJUDICATION_PROMPT_PAIRS
    ):
        raise DocumentAuthorityError("document_authority_run_identity_invalid")
    if stage == "critique" and previous_prompt_pair != (
        PRIMARY_CRITIQUE_PROMPT_VERSION,
        VERIFIER_CRITIQUE_PROMPT_VERSION,
    ):
        raise DocumentAuthorityError("document_authority_run_identity_invalid")
    expected = (
        (
            "primary", MONITORING_C3_MAPPING_PROVIDER, MONITORING_C3_MAPPING_MODEL,
            (
                LEGACY_PRIMARY_ADJUDICATION_PROMPT_VERSION
                if stage == "legacy_adjudication"
                else PRIMARY_CRITIQUE_PROMPT_VERSION
                if stage == "critique"
                else left.prompt_version
                if stage == "previous_adjudication"
                else PRIMARY_ADJUDICATION_PROMPT_VERSION
                if stage == "adjudication"
                else left.prompt_version
                if stage == "review"
                else left.prompt_version
                if stage == "analysis"
                else PRIMARY_PROMPT_VERSION
            ),
        ),
        (
            "verifier", MONITORING_C3_VERIFIER_PROVIDER, MONITORING_C3_VERIFIER_MODEL,
            (
                LEGACY_VERIFIER_ADJUDICATION_PROMPT_VERSION
                if stage == "legacy_adjudication"
                else VERIFIER_CRITIQUE_PROMPT_VERSION
                if stage == "critique"
                else right.prompt_version
                if stage == "previous_adjudication"
                else VERIFIER_ADJUDICATION_PROMPT_VERSION
                if stage == "adjudication"
                else right.prompt_version
                if stage == "review"
                else right.prompt_version
                if stage == "analysis"
                else VERIFIER_PROMPT_VERSION
            ),
        ),
    )
    for run, identity in zip((left, right), expected):
        actual = (run.role, run.provider, run.model, run.prompt_version)
        bound_hash = (
            run.input_sha256
            if stage == "analysis"
            else run.conflict_packet_sha256
        )
        if actual != identity or bound_hash != input_hash:
            raise DocumentAuthorityError("document_authority_run_identity_invalid")


def _anonymous_candidate(raw: Mapping[str, Any]) -> dict[str, Any]:
    if set(raw) - _CANDIDATE_KEYS:
        raise DocumentAuthorityError("document_authority_candidate_shape_invalid")
    candidate = {
        "candidate_id": str(raw.get("candidate_id") or ""),
        "role_hypotheses": sorted(str(value) for value in raw.get("role_hypotheses", ())),
        "filename": str(raw.get("filename") or ""),
        "technical_status": str(raw.get("technical_status") or ""),
        "extraction_status": str(raw.get("extraction_status") or ""),
        "locator_count": int(raw.get("locator_count") or 0),
        "excerpts": [_project_nested(item, _EXCERPT_KEYS) for item in raw.get("excerpts", ())],
        "sheets": [_project_nested(item, _SHEET_KEYS) for item in raw.get("sheets", ())],
    }
    profile = raw.get("content_profile")
    if profile is not None:
        candidate["content_profile"] = _project_nested(profile, _CONTENT_PROFILE_KEYS)
    return candidate


def _build_document_relationships(
    candidates: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    ordered = sorted(candidates, key=lambda item: str(item.get("candidate_id") or ""))
    for index, left in enumerate(ordered):
        left_profile = left.get("content_profile")
        if not isinstance(left_profile, Mapping):
            continue
        left_count = int(left_profile.get("normalized_character_count") or 0)
        left_fingerprints = set(left_profile.get("fingerprint_sha256") or ())
        if left_count <= 0:
            continue
        for right in ordered[index + 1 :]:
            right_profile = right.get("content_profile")
            if not isinstance(right_profile, Mapping):
                continue
            right_count = int(right_profile.get("normalized_character_count") or 0)
            right_fingerprints = set(right_profile.get("fingerprint_sha256") or ())
            if right_count <= 0:
                continue
            shared = len(left_fingerprints & right_fingerprints)
            left_overlap = (
                shared * 1000 // len(left_fingerprints) if left_fingerprints else 0
            )
            right_overlap = (
                shared * 1000 // len(right_fingerprints) if right_fingerprints else 0
            )
            equivalent = bool(
                left_count == right_count
                and left_profile.get("normalized_text_sha256")
                == right_profile.get("normalized_text_sha256")
            )
            if not equivalent and max(left_overlap, right_overlap) < 100:
                continue
            relationships.append({
                "candidate_ids": [left["candidate_id"], right["candidate_id"]],
                "relation": "equivalent" if equivalent else "sampled_content_overlap",
                "shared_fingerprint_count": shared,
                "left_sampled_overlap_per_mille": left_overlap,
                "right_sampled_overlap_per_mille": right_overlap,
                "left_coverage_per_mille": int(
                    left_profile.get("represented_coverage_per_mille") or 0
                ),
                "right_coverage_per_mille": int(
                    right_profile.get("represented_coverage_per_mille") or 0
                ),
            })
    return relationships


def _project_nested(item: Mapping[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
    if set(item) - allowed:
        raise DocumentAuthorityError("document_authority_anonymous_evidence_invalid")
    return {key: item[key] for key in sorted(item)}


def _candidate_locators(raw: Mapping[str, Any]) -> set[str]:
    return set(_candidate_locator_list(raw))


def _candidate_locator_list(raw: Mapping[str, Any]) -> list[str]:
    return [
        str(item.get("locator") or "")
        for key in ("excerpts", "sheets")
        for item in raw.get(key, ())
        if item.get("locator")
    ]


def _same_selection(left: RoleSelection, right: RoleSelection) -> bool:
    return bool(
        left.decision == right.decision == "selected"
        and left.selected_candidate_id == right.selected_candidate_id
        and min(left.confidence, right.confidence) >= AUTO_RESOLVE_CONFIDENCE
        and set(left.evidence_locators) == set(right.evidence_locators)
        and _same_supplementary_bindings(left.supplementary_bindings, right.supplementary_bindings)
        and _normalized(left.uncertainty) == _normalized(right.uncertainty)
    )


def _same_supplementary_bindings(
    left: tuple[RoleSupplementaryBinding, ...],
    right: tuple[RoleSupplementaryBinding, ...],
) -> bool:
    left_map = {item.candidate_id: frozenset(item.evidence_locators) for item in left}
    right_map = {item.candidate_id: frozenset(item.evidence_locators) for item in right}
    return left_map == right_map


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
    *,
    require_complete_disposition: bool = False,
    required_evidence_candidate_ids: set[str] | None = None,
) -> None:
    if set(item.considered_candidate_ids) != allowed:
        raise DocumentAuthorityError("document_authority_review_coverage_invalid")
    if item.selected_candidate_id and item.selected_candidate_id not in allowed:
        raise DocumentAuthorityError("document_authority_review_candidate_unknown")
    if any(candidate_id not in allowed for candidate_id in item.supplementary_candidate_ids):
        raise DocumentAuthorityError("document_authority_review_candidate_unknown")
    excluded_candidate_ids = tuple(
        getattr(item, "excluded_candidate_ids", ())
    )
    if any(candidate_id not in allowed for candidate_id in excluded_candidate_ids):
        raise DocumentAuthorityError("document_authority_review_candidate_unknown")
    if require_complete_disposition:
        bound = _decision_bound_candidate_ids(item)
        excluded = set(excluded_candidate_ids)
        if bound & excluded or bound | excluded != allowed:
            raise DocumentAuthorityError(
                "document_authority_review_disposition_incomplete"
            )
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
    bound_candidate_ids = {
        item.selected_candidate_id,
        *item.supplementary_candidate_ids,
    } - {""}
    evidence_required = (
        allowed
        if required_evidence_candidate_ids is None
        else required_evidence_candidate_ids | bound_candidate_ids
    )
    if any(
        candidate_locators
        and not any(candidate_id == ref_candidate for ref_candidate, _locator in evidence)
        for candidate_id, candidate_locators in locators_by_candidate.items()
        if candidate_id in evidence_required
    ):
        raise DocumentAuthorityError("document_authority_review_coverage_invalid")
    if any(
        candidate_id not in {ref_candidate for ref_candidate, _locator in evidence}
        for candidate_id in bound_candidate_ids
    ):
        raise DocumentAuthorityError("document_authority_review_evidence_not_closed")


def _same_conflict_selection(left: ConflictDecision, right: ConflictDecision) -> bool:
    return bool(
        left.decision == right.decision == "selected"
        and left.selected_candidate_id == right.selected_candidate_id
        and _normalized_document_version(left.document_version)
        == _normalized_document_version(right.document_version)
        and _normalized_document_date(left.document_date)
        == _normalized_document_date(right.document_date)
        and set(left.considered_candidate_ids) == set(right.considered_candidate_ids)
        and set(left.supplementary_candidate_ids) == set(right.supplementary_candidate_ids)
        and _normalized(left.uncertainty) == _normalized(right.uncertainty)
        and min(left.confidence, right.confidence) >= REVIEW_CONSENSUS_CONFIDENCE
    )


def _decision_bound_candidate_ids(item: ConflictDecision) -> set[str]:
    return {
        item.selected_candidate_id,
        *item.supplementary_candidate_ids,
    } - {""}


def _same_conflict_missing(
    left: ConflictDecision, right: ConflictDecision, allowed: set[str]
) -> bool:
    return bool(
        left.decision == right.decision == "missing"
        and set(left.considered_candidate_ids) == allowed
        and set(right.considered_candidate_ids) == allowed
        and _normalized(left.uncertainty) == _normalized(right.uncertainty)
        and min(left.confidence, right.confidence) >= REVIEW_CONSENSUS_CONFIDENCE
    )


def _resolved_role(
    role: str, status: str, candidate_id: str, supplementary: tuple[str, ...] = ()
) -> dict[str, Any]:
    return {
        "role": role,
        "status": status,
        "candidate_id": candidate_id,
        "supplementary_candidate_ids": sorted(supplementary),
    }


def _review_index(
    review: DocumentAuthorityConflictReview, roles: Sequence[str]
) -> dict[str, ConflictDecision]:
    indexed = {item.role: item for item in review.decisions}
    if set(indexed) != set(roles) or len(indexed) != len(review.decisions):
        raise DocumentAuthorityError("document_authority_review_coverage_invalid")
    return indexed


def _normalized(value: str) -> str:
    return " ".join(value.split()).casefold()


def _normalized_document_version(value: str) -> str:
    normalized = re.sub(r"\s+", "", value).casefold()
    numeric = re.fullmatch(
        r"(?:v(?:ersion)?|版本(?:号)?|第)?([0-9]+(?:[._-][0-9a-z]+)*)(?:版|版本|稿)?",
        normalized,
    )
    if not numeric:
        return normalized
    return numeric.group(1).replace("_", ".").replace("-", ".")


def _normalized_document_date(value: str) -> str:
    normalized = re.sub(r"\s+", "", value).casefold()
    match = re.fullmatch(
        r"([0-9]{4})(?:年|[-/.])([0-9]{1,2})(?:月|[-/.])([0-9]{1,2})日?",
        normalized,
    )
    if not match:
        return normalized
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


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
