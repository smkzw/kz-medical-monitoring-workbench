"""Shared offline ensemble / reference-baseline closure contracts.

Typed contracts for the shared cross-domain analysis closure (System Design
v1.1 §9.2-9.4; R4 implementation plan steps 9-10): reference-baseline items,
exactly six baseline assessment states, deterministic gap candidates, isolated
analysis attempts with session identity, deterministic evidence verification,
independent adjudication binding, and conflict visibility that can never hide
high-risk or important disagreement.

Scope boundary
--------------
* This is a SHARED stage contract, not D10 medical evaluation and not R2 risk
  lifecycle.  It is deliberately kept out of ``d10_evaluator.py``,
  ``efficacy_evaluator.py`` and ``lifecycle.py`` so the closure stays
  domain-independent.
* Reused read-only: R4 :mod:`mm_r4.contracts` monitoring priorities and
  canonical hashing; R2 :mod:`mm_r2.risk` ``AdjudicationOutcome`` vocabulary.
  R2 ``DataBaseline`` (snapshot diff baseline) and D10 ``ModelEvidence``
  (aggregate pin) are NOT this closure; they are different objects.
* The reference baseline is challengeable and never a gold standard: no field
  here can express gold/authoritative/accepted-as-truth semantics, and legacy
  baseline output is never copied forward as new authority.
* The six assessment states are NOT L1 dispositions and NOT L3 lifecycle
  states: ``confirmed`` never maps to a negative disposition and
  ``unsupported`` never maps to a positive one.
* No decision path in this module branches on test identifiers, case indexes,
  opaque audit identifiers, synthetic sentinel strings, or external
  evaluation-service outputs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Tuple

from mm_r2.risk import AdjudicationOutcome

from .contracts import (
    MONITORING_PRIORITY_HIGH,
    VALID_MONITORING_PRIORITIES,
    content_hash,
)

__all__ = [
    "AdjudicationBinding",
    "AnalysisAttempt",
    "ASSESSMENT_REASON_CODES",
    "ATTEMPT_ROLES",
    "BASELINE_STATES",
    "BaselineAssessment",
    "CONFLICT_DISPLAY_STATES",
    "CONFLICT_RELATIONS",
    "ConflictVisibility",
    "EnsembleContractError",
    "EvidenceVerification",
    "GAP_KINDS",
    "GapCandidate",
    "NON_HIDEABLE_RELATIONS",
    "RECHECK_REQUIRED_STATES",
    "ReferenceBaselineItem",
    "SOURCE_KINDS",
    "VERIFICATION_DIMENSIONS",
    "VERIFICATION_FAILURE_CODES",
    "VERIFICATION_RESULTS",
]


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class EnsembleContractError(Exception):
    """Closed-vocabulary or required-field violation of an ensemble contract
    object."""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _check_nonempty(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EnsembleContractError(
            f"{name} must be a non-empty string, got {value!r}")
    return value


def _check_sha256(value: Any, name: str) -> str:
    value = _check_nonempty(value, name)
    if not _SHA256_RE.match(value):
        raise EnsembleContractError(
            f"{name} must be a 64-hex sha256, got {value!r}")
    return value


def _check_closed(value: Any, name: str, allowed: Tuple[str, ...]) -> str:
    if value not in allowed:
        raise EnsembleContractError(
            f"{name} must be one of {allowed!r}, got {value!r}")
    return value


def _freeze_str_tuple(value: Any, name: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise EnsembleContractError(
            f"{name} must be a list/tuple, got {value!r}")
    result = tuple(str(item) for item in value)
    for item in result:
        _check_nonempty(item, name)
    return tuple(sorted(result))


def _require_nonempty_tuple(value: Tuple[str, ...], name: str) -> None:
    if not value:
        raise EnsembleContractError(f"{name} must be non-empty, got ()")


# ---------------------------------------------------------------------------
# Closed vocabularies
# ---------------------------------------------------------------------------

#: Reference-baseline source kinds (legacy outputs are the challengeable
#: baseline, never copied forward as new authority).
SOURCE_KINDS: Tuple[str, ...] = (
    "legacy_profile",
    "legacy_timeline",
    "legacy_omission",
    "current_pack",
)

#: The exactly-six baseline assessment states.  This is a closed vocabulary;
#: it is not an L1 disposition set and not an L3 lifecycle state set.
BASELINE_STATES: Tuple[str, ...] = (
    "confirmed",
    "partially_supported",
    "unsupported",
    "outdated",
    "insufficient_evidence",
    "not_applicable",
)

#: States that prove the ORIGINAL source was actually rechecked (never just
#: the baseline text re-read).  These are the only states that require
#: ``source_recheck_locator_ids``.
RECHECK_REQUIRED_STATES: Tuple[str, ...] = ("confirmed", "unsupported")

#: Gap-search candidate kinds.
GAP_KINDS: Tuple[str, ...] = (
    "baseline_missed_current",
    "current_missed_baseline",
    "source_unrepresented",
)

#: Analysis-attempt roles.  Runtime analysis attempts are workers; the
#: adjudicator is a separate binding with its own session identity.
ATTEMPT_ROLES: Tuple[str, ...] = ("worker", "adjudicator")

#: Deterministic evidence-verification results.
VERIFICATION_RESULTS: Tuple[str, ...] = ("passed", "failed", "not_evaluable")

#: Dimensions a deterministic verifier may check (identity, version, date,
#: unit, source, rule, artifact integrity).
VERIFICATION_DIMENSIONS: Tuple[str, ...] = (
    "identity",
    "version",
    "date",
    "unit",
    "source",
    "rule",
    "artifact_integrity",
)

#: Closed failure-reason codes carried by a failed verification record.
VERIFICATION_FAILURE_CODES: Tuple[str, ...] = (
    "identity_mismatch",
    "version_mismatch",
    "date_out_of_window",
    "unit_mismatch",
    "source_unresolvable",
    "rule_version_mismatch",
    "artifact_hash_mismatch",
    "input_content_mismatch",
)

#: Closed assessment reason codes; free prose is never a state or a reason.
ASSESSMENT_REASON_CODES: Tuple[str, ...] = (
    "source_rechecked",
    "content_match",
    "partial_content_match",
    "content_absent_from_source",
    "source_revision_superseded",
    "evidence_insufficient",
    "locator_unresolvable",
    "outside_assessment_scope",
)

#: Conflict relations derived by the ensemble merge.
CONFLICT_RELATIONS: Tuple[str, ...] = (
    "shared_finding",
    "single_model_new",
    "graded_conflict",
    "mutual_negation",
    "baseline_miss",
)

#: Conflict display states.
CONFLICT_DISPLAY_STATES: Tuple[str, ...] = (
    "needs_attention",
    "visible_conflict",
    "visible_baseline_miss",
)

#: Relations that always describe important disagreement.  A conflict of this
#: relation can never be constructed with ``hidden=True``.
NON_HIDEABLE_RELATIONS: Tuple[str, ...] = ("mutual_negation", "baseline_miss")


# ---------------------------------------------------------------------------
# ReferenceBaselineItem
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReferenceBaselineItem:
    """One challengeable reference-baseline entry (never a gold standard).

    Legacy profile/timeline/omission output is treated as a baseline for
    rechecking, never copied forward as new authority: the item carries no
    gold/authoritative/accepted-as-truth field and exposes the original
    source locators so a later assessment must recheck the original source.
    ``claimed_content_hash`` is a deterministic content address of the item's
    own core fields (like ``EvaluationUnit.unit_id``).
    """

    item_id: str
    source_kind: str
    source_locator_ids: Tuple[str, ...]
    source_revision_id: str
    snapshot_id: str
    claimed_identity: str
    temporal_window: str
    claimed_content_hash: str
    origin_artifact_hash: str

    #: Fields structurally forbidden on a reference-baseline item: the
    #: baseline is challengeable and never accepted as truth.
    FORBIDDEN_AUTHORITY_FIELDS: Tuple[str, ...] = (
        "is_gold", "authoritative", "accepted_as_truth")

    def __post_init__(self) -> None:
        _check_nonempty(self.item_id, "ReferenceBaselineItem.item_id")
        _check_closed(self.source_kind, "ReferenceBaselineItem.source_kind",
                      SOURCE_KINDS)
        object.__setattr__(
            self, "source_locator_ids",
            _freeze_str_tuple(self.source_locator_ids,
                              "ReferenceBaselineItem.source_locator_ids"))
        _require_nonempty_tuple(
            self.source_locator_ids,
            "ReferenceBaselineItem.source_locator_ids")
        _check_nonempty(self.source_revision_id,
                        "ReferenceBaselineItem.source_revision_id")
        _check_nonempty(self.snapshot_id, "ReferenceBaselineItem.snapshot_id")
        _check_nonempty(self.claimed_identity,
                        "ReferenceBaselineItem.claimed_identity")
        _check_nonempty(self.temporal_window,
                        "ReferenceBaselineItem.temporal_window")
        _check_sha256(self.origin_artifact_hash,
                      "ReferenceBaselineItem.origin_artifact_hash")
        expected = self.compute_content_hash()
        if self.claimed_content_hash and self.claimed_content_hash != expected:
            raise EnsembleContractError(
                "ReferenceBaselineItem.claimed_content_hash "
                f"{self.claimed_content_hash!r} does not match the "
                f"deterministic hash {expected!r}")
        object.__setattr__(self, "claimed_content_hash", expected)

    def compute_content_hash(self) -> str:
        """Deterministic content address of the item's core fields."""
        return content_hash({
            "item_id": self.item_id,
            "source_kind": self.source_kind,
            "source_locator_ids": sorted(self.source_locator_ids),
            "source_revision_id": self.source_revision_id,
            "snapshot_id": self.snapshot_id,
            "claimed_identity": self.claimed_identity,
            "temporal_window": self.temporal_window,
        })


# ---------------------------------------------------------------------------
# BaselineAssessment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaselineAssessment:
    """One worker's six-state assessment of a reference-baseline item.

    ``confirmed`` and ``unsupported`` require ``source_recheck_locator_ids``:
    a claim that the ORIGINAL source was actually rechecked, never just the
    baseline text re-read.  When the original source cannot be rechecked the
    assessment must stop at ``insufficient_evidence`` / ``not_applicable``.
    """

    item_id: str
    state: str
    source_recheck_locator_ids: Tuple[str, ...]
    evidence_hashes: Tuple[str, ...]
    attempt_id: str
    reason_codes: Tuple[str, ...]

    def __post_init__(self) -> None:
        _check_nonempty(self.item_id, "BaselineAssessment.item_id")
        _check_closed(self.state, "BaselineAssessment.state", BASELINE_STATES)
        object.__setattr__(
            self, "source_recheck_locator_ids",
            _freeze_str_tuple(
                self.source_recheck_locator_ids,
                "BaselineAssessment.source_recheck_locator_ids"))
        object.__setattr__(
            self, "evidence_hashes",
            _freeze_str_tuple(self.evidence_hashes,
                              "BaselineAssessment.evidence_hashes"))
        _require_nonempty_tuple(self.evidence_hashes,
                                "BaselineAssessment.evidence_hashes")
        for evidence_hash in self.evidence_hashes:
            _check_sha256(evidence_hash,
                          "BaselineAssessment.evidence_hashes")
        _check_nonempty(self.attempt_id, "BaselineAssessment.attempt_id")
        object.__setattr__(
            self, "reason_codes",
            _freeze_str_tuple(self.reason_codes,
                              "BaselineAssessment.reason_codes"))
        _require_nonempty_tuple(self.reason_codes,
                                "BaselineAssessment.reason_codes")
        for code in self.reason_codes:
            _check_closed(code, "BaselineAssessment.reason_codes",
                          ASSESSMENT_REASON_CODES)
        if (self.state in RECHECK_REQUIRED_STATES
                and not self.source_recheck_locator_ids):
            raise EnsembleContractError(
                f"BaselineAssessment.state {self.state!r} requires "
                "source_recheck_locator_ids (original source recheck, not "
                "baseline text re-read)")


# ---------------------------------------------------------------------------
# GapCandidate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GapCandidate:
    """Deterministic proposal of a coverage gap between baseline and current.

    A gap candidate is a PROPOSAL only: it never creates, escalates or closes
    a lifecycle risk, never becomes an authority, and carries no
    promotion/decision field.  Risk lifecycle stays exclusively in
    :mod:`mm_r4.lifecycle`.
    """

    gap_id: str
    gap_kind: str
    proposed_identity: str
    source_locator_ids: Tuple[str, ...]
    originating_attempt_id: str

    #: Fields structurally forbidden on a gap candidate: no automatic
    #: escalation to a risk and no formal conclusion.
    FORBIDDEN_PROMOTION_FIELDS: Tuple[str, ...] = (
        "promoted_to_risk", "risk_instance_ref", "formal_conclusion")

    def __post_init__(self) -> None:
        _check_nonempty(self.gap_id, "GapCandidate.gap_id")
        _check_closed(self.gap_kind, "GapCandidate.gap_kind", GAP_KINDS)
        _check_nonempty(self.proposed_identity,
                        "GapCandidate.proposed_identity")
        object.__setattr__(
            self, "source_locator_ids",
            _freeze_str_tuple(self.source_locator_ids,
                              "GapCandidate.source_locator_ids"))
        _require_nonempty_tuple(self.source_locator_ids,
                                "GapCandidate.source_locator_ids")
        _check_nonempty(self.originating_attempt_id,
                        "GapCandidate.originating_attempt_id")


# ---------------------------------------------------------------------------
# AnalysisAttempt
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AnalysisAttempt:
    """One isolated analysis attempt with its own session identity.

    Isolation identity is ``binding_id`` + ``session_id`` +
    ``independent_context_hash``.  The same ``model_id`` may appear on many
    attempts: a different binding/session is a different analysis, not a
    duplicate.  N-way runs require every attempt to carry the SAME
    ``input_content_hash`` (same question, same input version) while their
    ``independent_context_hash`` values differ.

    ``claimed_date_window``, ``claimed_unit_contract``,
    ``claimed_source_revision``, ``claimed_rule_id`` and
    ``claimed_rule_version`` are the attempt's own evidence claims: the
    deterministic verifier compares them against the authoritative
    per-artifact entries in :class:`mm_r4.ensemble.EvidenceDigestContext`.
    A claim that is absent, unresolved in the authority index, or divergent
    fails verification closed (``date_out_of_window`` / ``unit_mismatch`` /
    ``version_mismatch`` / ``rule_version_mismatch``).
    """

    attempt_id: str
    ensemble_id: str
    binding_id: str
    session_id: str
    model_id: str
    model_version: str
    role: str
    independent_context_hash: str
    input_content_hash: str
    output_artifact_ref: str
    output_hash: str
    claimed_date_window: str
    claimed_unit_contract: str
    claimed_source_revision: str
    claimed_rule_id: str
    claimed_rule_version: str

    def __post_init__(self) -> None:
        for name, value in (
                ("attempt_id", self.attempt_id),
                ("ensemble_id", self.ensemble_id),
                ("binding_id", self.binding_id),
                ("session_id", self.session_id),
                ("model_id", self.model_id),
                ("model_version", self.model_version),
                ("output_artifact_ref", self.output_artifact_ref)):
            _check_nonempty(value, f"AnalysisAttempt.{name}")
        _check_closed(self.role, "AnalysisAttempt.role", ATTEMPT_ROLES)
        _check_sha256(self.independent_context_hash,
                      "AnalysisAttempt.independent_context_hash")
        _check_sha256(self.input_content_hash,
                      "AnalysisAttempt.input_content_hash")
        _check_sha256(self.output_hash, "AnalysisAttempt.output_hash")
        _check_nonempty(self.claimed_date_window,
                        "AnalysisAttempt.claimed_date_window")
        _check_nonempty(self.claimed_unit_contract,
                        "AnalysisAttempt.claimed_unit_contract")
        _check_nonempty(self.claimed_source_revision,
                        "AnalysisAttempt.claimed_source_revision")
        _check_nonempty(self.claimed_rule_id,
                        "AnalysisAttempt.claimed_rule_id")
        _check_nonempty(self.claimed_rule_version,
                        "AnalysisAttempt.claimed_rule_version")


# ---------------------------------------------------------------------------
# EvidenceVerification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceVerification:
    """Deterministic, model-free evidence verification record.

    The verifier checks identity/version/date/unit/source/rule/artifact
    integrity from digest and locator indexes only; it never calls a model.
    A ``failed`` verification blocks the full analysis: no supporting
    adjudication outcome may follow a failed record.
    """

    verification_id: str
    attempt_id: str
    checked_dimensions: Tuple[str, ...]
    result: str
    failure_reason_codes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _check_nonempty(self.verification_id,
                        "EvidenceVerification.verification_id")
        _check_nonempty(self.attempt_id, "EvidenceVerification.attempt_id")
        object.__setattr__(
            self, "checked_dimensions",
            _freeze_str_tuple(self.checked_dimensions,
                              "EvidenceVerification.checked_dimensions"))
        _require_nonempty_tuple(self.checked_dimensions,
                                "EvidenceVerification.checked_dimensions")
        for dimension in self.checked_dimensions:
            _check_closed(dimension,
                          "EvidenceVerification.checked_dimensions",
                          VERIFICATION_DIMENSIONS)
        _check_closed(self.result, "EvidenceVerification.result",
                      VERIFICATION_RESULTS)
        object.__setattr__(
            self, "failure_reason_codes",
            _freeze_str_tuple(self.failure_reason_codes,
                              "EvidenceVerification.failure_reason_codes"))
        for code in self.failure_reason_codes:
            _check_closed(code,
                          "EvidenceVerification.failure_reason_codes",
                          VERIFICATION_FAILURE_CODES)
        if self.result == "passed" and self.failure_reason_codes:
            raise EnsembleContractError(
                "EvidenceVerification passed must carry no failure reason "
                "codes")
        if self.result == "failed" and not self.failure_reason_codes:
            raise EnsembleContractError(
                "EvidenceVerification failed must carry at least one failure "
                "reason code")


# ---------------------------------------------------------------------------
# AdjudicationBinding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdjudicationBinding:
    """Independent adjudication binding over the original attempt outputs.

    The binding identity (``binding_id``/``session_id``) must differ from
    EVERY worker attempt: a worker may never adjudicate itself.  ``model_id``
    MAY equal a worker's model; a different binding/session is sufficient
    independence.  ``outcome`` reuses the R2 five-state vocabulary; a failed
    evidence verification or an unresolved high-risk disagreement must resolve
    to ``needs_user_attention``, never to a supporting outcome.  The binding
    reviews the ORIGINAL attempt artifacts; it never rewrites worker output.
    """

    binding_id: str
    session_id: str
    model_id: str
    model_version: str
    outcome: str
    reviewed_artifact_refs: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name, value in (
                ("binding_id", self.binding_id),
                ("session_id", self.session_id),
                ("model_id", self.model_id),
                ("model_version", self.model_version)):
            _check_nonempty(value, f"AdjudicationBinding.{name}")
        _check_closed(self.outcome, "AdjudicationBinding.outcome",
                      tuple(AdjudicationOutcome.all_outcomes()))
        object.__setattr__(
            self, "reviewed_artifact_refs",
            _freeze_str_tuple(self.reviewed_artifact_refs,
                              "AdjudicationBinding.reviewed_artifact_refs"))
        _require_nonempty_tuple(self.reviewed_artifact_refs,
                                "AdjudicationBinding.reviewed_artifact_refs")


# ---------------------------------------------------------------------------
# ConflictVisibility
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConflictVisibility:
    """A cross-attempt disagreement kept visible after merge.

    High-risk, low-confidence or important medical disagreement can never be
    hidden: ``hidden=True`` is rejected for high monitoring priority and for
    the ``mutual_negation`` / ``baseline_miss`` relations.  Majority voting,
    an adjudicator, or D10-style pin merging can never flip ``hidden`` to
    ``True`` for such a conflict: the merge path simply cannot construct it.
    """

    conflict_id: str
    member_attempt_ids: Tuple[str, ...]
    monitoring_priority: str
    relation: str
    display_state: str
    hidden: bool = False

    def __post_init__(self) -> None:
        _check_nonempty(self.conflict_id, "ConflictVisibility.conflict_id")
        object.__setattr__(
            self, "member_attempt_ids",
            _freeze_str_tuple(self.member_attempt_ids,
                              "ConflictVisibility.member_attempt_ids"))
        _require_nonempty_tuple(self.member_attempt_ids,
                                "ConflictVisibility.member_attempt_ids")
        _check_closed(self.monitoring_priority,
                      "ConflictVisibility.monitoring_priority",
                      VALID_MONITORING_PRIORITIES)
        _check_closed(self.relation, "ConflictVisibility.relation",
                      CONFLICT_RELATIONS)
        _check_closed(self.display_state,
                      "ConflictVisibility.display_state",
                      CONFLICT_DISPLAY_STATES)
        if not isinstance(self.hidden, bool):
            raise EnsembleContractError(
                "ConflictVisibility.hidden must be a bool")
        if self.hidden and (
                self.monitoring_priority == MONITORING_PRIORITY_HIGH
                or self.relation in NON_HIDEABLE_RELATIONS):
            raise EnsembleContractError(
                "ConflictVisibility.hidden=True is rejected for high-risk or "
                "important disagreement: priority "
                f"{self.monitoring_priority!r} relation {self.relation!r} "
                "must stay visible")
        if self.relation == "baseline_miss" and \
                self.display_state != "visible_baseline_miss":
            raise EnsembleContractError(
                "ConflictVisibility baseline_miss requires display_state "
                "visible_baseline_miss")
        if self.relation == "mutual_negation" and \
                self.display_state != "visible_conflict":
            raise EnsembleContractError(
                "ConflictVisibility mutual_negation requires display_state "
                "visible_conflict")
