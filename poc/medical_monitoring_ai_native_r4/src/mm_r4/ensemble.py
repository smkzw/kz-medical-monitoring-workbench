"""Offline deterministic ensemble closure: gates, isolation, gap search,
verification-before-adjudication, worker/adjudicator separation and conflict
visibility that majority/adjudication cannot hide.

This is the shared runtime for System Design v1.1 §9.2-9.4 / R4 plan steps
9-10.  It is offline: no real model, no harness, no service, no port.  Worker
attempts and the adjudicator are deterministic functions over injected attempt
outputs; the module never reads opaque audit identifiers and never branches on
synthetic sentinel strings.

Guarantees enforced here:

1. ``ensemble_size < 1`` fails closed BEFORE any attempt, gap search,
   verification or adjudication side effect (shared entry gate).
2. ``ensemble_size == 1`` exposes no consensus/agreement leaf; residual
   conflict or the absence of an independent adjudicator keeps the outcome at
   ``needs_user_attention`` while the main analysis still completes.
3. ``ensemble_size >= 2`` requires the SAME ``input_content_hash`` on every
   attempt and DISTINCT ``binding_id`` / ``session_id`` /
   ``independent_context_hash`` values; the same ``model_id`` on different
   bindings/sessions is valid.
4. A worker can never adjudicate itself: the adjudicator ``binding_id`` and
   ``session_id`` must differ from every worker attempt.
5. Deterministic evidence verification runs BEFORE adjudication; a failed
   verification blocks any supporting outcome.  The verifier compares every
   claimed dimension against an independent typed authority context
   (identity, version, date, unit, source, rule, artifact integrity), records
   every attempted dimension for audit, and fails closed on unresolved
   authority entries.
6. Gap search only PROPOSES candidates; it never creates, escalates or closes
   a lifecycle risk.
7. High-risk or important disagreement stays visible (``hidden=False``);
   majority voting and adjudication cannot hide it.
8. Intake attribution is sealed before any analysis: every
   ``worker_outputs`` key must equal the output's own ``attempt_id`` and
   resolve to the declared ``AnalysisAttempt``, and each worker output may
   carry at most one assessment per baseline item plus unique finding and
   gap-proposal ids.  Cross-worker duplication of item ids, finding
   identities or gap proposals stays legal (independent workers may address
   the same item).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple

from mm_r2.risk import AdjudicationOutcome

from .contracts import (
    MONITORING_PRIORITIES,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_MEDIUM,
    MONITORING_PRIORITY_UNKNOWN,
    content_hash,
)
from .ensemble_contracts import (
    AdjudicationBinding,
    AnalysisAttempt,
    BaselineAssessment,
    ConflictVisibility,
    EvidenceVerification,
    GapCandidate,
    NON_HIDEABLE_RELATIONS,
    ReferenceBaselineItem,
)

__all__ = [
    "Adjudicator",
    "EnsembleError",
    "EnsembleResult",
    "EvidenceDigestContext",
    "Finding",
    "WorkerAnalysisOutput",
    "derive_conflicts",
    "require_positive_ensemble_size",
    "run_ensemble",
    "search_gaps",
    "verify_attempt",
    "worker_output_content_hash",
]

_ATTEMPT_ROLE_WORKER = "worker"

#: Explicit identity used when NO independent adjudicator is supplied.  The
#: runtime treats this as "no adjudication performed": the outcome is
#: deterministically ``needs_user_attention`` and the identity never collides
#: with a worker binding/session.
_UNRESOLVED_BINDING_ID = "no-independent-adjudicator"
_UNRESOLVED_SESSION_ID = "no-independent-session"
_UNRESOLVED_MODEL_ID = "none"
_UNRESOLVED_MODEL_VERSION = "none"


class EnsembleError(Exception):
    """Fail-closed violation of the shared ensemble runtime contract."""


def require_positive_ensemble_size(ensemble_size: int) -> int:
    """Shared fail-closed gate: ``ensemble_size`` must be >= 1.

    Zero, negative and non-int values are rejected before any attempt, gap
    search, verification or adjudication work.
    """
    if isinstance(ensemble_size, bool) or not isinstance(ensemble_size, int) \
            or ensemble_size < 1:
        raise EnsembleError(
            f"ensemble_size must be a positive int, got {ensemble_size!r}")
    return ensemble_size


def _priority_rank(priority: str) -> int:
    return {
        MONITORING_PRIORITY_HIGH: 0,
        MONITORING_PRIORITY_MEDIUM: 1,
        MONITORING_PRIORITY_LOW: 2,
        MONITORING_PRIORITY_UNKNOWN: 3,
    }[priority]


# ---------------------------------------------------------------------------
# Worker output / finding / digest context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One worker's own claim (never cross-attempt).

    ``supported`` is True when the attempt asserts the identity/fact is
    present and valid in the current pack, False when the attempt asserts it
    is absent/invalid.  A finding never carries a lifecycle action and never
    references another attempt's output.
    """

    finding_id: str
    proposed_identity: str
    monitoring_priority: str
    supported: bool
    source_locator_ids: Tuple[str, ...]
    baseline_item_ref: str = ""

    def __post_init__(self) -> None:
        for name, value in (
                ("finding_id", self.finding_id),
                ("proposed_identity", self.proposed_identity)):
            if not isinstance(value, str) or not value.strip():
                raise EnsembleError(
                    f"Finding.{name} must be a non-empty string")
        if self.monitoring_priority not in MONITORING_PRIORITIES:
            raise EnsembleError(
                f"Finding.monitoring_priority invalid: "
                f"{self.monitoring_priority!r}")
        if not isinstance(self.supported, bool):
            raise EnsembleError("Finding.supported must be a bool")
        if not isinstance(self.source_locator_ids, (list, tuple)) \
                or not self.source_locator_ids:
            raise EnsembleError(
                "Finding.source_locator_ids must be a non-empty "
                "list/tuple of locator ids")
        object.__setattr__(
            self, "source_locator_ids",
            tuple(sorted(str(item) for item in self.source_locator_ids)))
        for locator in self.source_locator_ids:
            if not locator:
                raise EnsembleError(
                    "Finding.source_locator_ids must contain non-empty "
                    "locator ids")
        if not isinstance(self.baseline_item_ref, str):
            raise EnsembleError("Finding.baseline_item_ref must be a str")


@dataclass(frozen=True)
class WorkerAnalysisOutput:
    """One worker's full offline output; referenced only by its own attempt.

    Worker isolation is enforced structurally: an output may only carry
    assessments/candidates attributed to its own ``attempt_id``, and a worker
    never receives another worker's output.
    """

    attempt_id: str
    assessments: Tuple[BaselineAssessment, ...]
    findings: Tuple[Finding, ...] = ()
    gap_candidates: Tuple[GapCandidate, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.attempt_id, str) or not self.attempt_id.strip():
            raise EnsembleError(
                "WorkerAnalysisOutput.attempt_id must be a non-empty string")
        if not isinstance(self.assessments, tuple):
            object.__setattr__(self, "assessments", tuple(self.assessments))
        if not isinstance(self.findings, tuple):
            object.__setattr__(self, "findings", tuple(self.findings))
        if not isinstance(self.gap_candidates, tuple):
            object.__setattr__(self, "gap_candidates",
                               tuple(self.gap_candidates))
        for assessment in self.assessments:
            if assessment.attempt_id != self.attempt_id:
                raise EnsembleError(
                    "WorkerAnalysisOutput contains an assessment from "
                    f"another attempt {assessment.attempt_id!r}")
        for candidate in self.gap_candidates:
            if candidate.originating_attempt_id != self.attempt_id:
                raise EnsembleError(
                    "WorkerAnalysisOutput contains a gap candidate from "
                    f"another attempt {candidate.originating_attempt_id!r}")
        # Intake-uniqueness invariants (per worker): at most one assessment
        # per baseline item, one finding per finding id, one gap proposal
        # per gap id.  Duplicates -- even same-state duplicates -- fail
        # closed at construction so they can never reach the verifier, gap
        # search, conflict merge or adjudication.  Cross-worker duplication
        # of item ids / finding identities / gap proposals stays legal:
        # independent workers may legitimately address the same item.
        assessment_item_ids = [
            assessment.item_id for assessment in self.assessments]
        if len(set(assessment_item_ids)) != len(assessment_item_ids):
            raise EnsembleError(
                "WorkerAnalysisOutput must carry at most one assessment per "
                "baseline item; duplicate item "
                f"{assessment_item_ids!r}")
        finding_ids = [finding.finding_id for finding in self.findings]
        if len(set(finding_ids)) != len(finding_ids):
            raise EnsembleError(
                "WorkerAnalysisOutput must carry unique finding ids; "
                f"duplicate {finding_ids!r}")
        gap_ids = [gap.gap_id for gap in self.gap_candidates]
        if len(set(gap_ids)) != len(gap_ids):
            raise EnsembleError(
                "WorkerAnalysisOutput must carry unique gap proposal ids; "
                f"duplicate {gap_ids!r}")


@dataclass(frozen=True)
class EvidenceDigestContext:
    """Independent typed authority context used by :func:`verify_attempt`.

    Carries the authoritative expected values the verifier compares every
    attempt claim against -- it does not merely label dimensions:

    * ``expected_ensemble_identity`` -- the one ensemble/analysis identity
      the attempt may claim (identity dimension);
    * ``input_content_hash`` -- the expected input content hash (version);
    * ``artifact_source_versions`` / ``artifact_model_versions`` -- expected
      source revision and model version per output artifact (version);
    * ``artifact_rule_ids`` / ``artifact_rule_versions`` -- expected rule
      identity and rule version per output artifact (rule);
    * ``artifact_authorized_source_locators`` -- the only source locator ids
      a worker may cite (source);
    * ``evidence_digests`` -- the registered evidence digests (source);
    * ``artifact_date_windows`` / ``artifact_unit_contracts`` -- expected
      date window and unit contract per output artifact (date/unit);
    * ``output_digests`` -- the expected canonical digest of the actual
      worker output per output artifact (artifact integrity).

    A missing (unresolved) or divergent authority entry fails the
    corresponding dimension closed.
    """

    input_content_hash: str
    output_digests: Mapping[str, str]
    evidence_digests: frozenset
    expected_ensemble_identity: str = ""
    artifact_date_windows: Mapping[str, str] = field(default_factory=dict)
    artifact_unit_contracts: Mapping[str, str] = field(default_factory=dict)
    artifact_source_versions: Mapping[str, str] = field(default_factory=dict)
    artifact_model_versions: Mapping[str, str] = field(default_factory=dict)
    artifact_rule_ids: Mapping[str, str] = field(default_factory=dict)
    artifact_rule_versions: Mapping[str, str] = field(default_factory=dict)
    artifact_finding_identities: Mapping[str, frozenset] = field(
        default_factory=dict)
    artifact_authorized_source_locators: Mapping[str, frozenset] = field(
        default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.input_content_hash, str) \
                or len(self.input_content_hash) != 64:
            raise EnsembleError(
                "EvidenceDigestContext.input_content_hash must be a "
                "64-hex sha256")
        if not isinstance(self.output_digests, Mapping):
            raise EnsembleError(
                "EvidenceDigestContext.output_digests must be a Mapping")
        if not isinstance(self.evidence_digests, frozenset):
            object.__setattr__(self, "evidence_digests",
                               frozenset(self.evidence_digests))
        if not isinstance(self.expected_ensemble_identity, str):
            raise EnsembleError(
                "EvidenceDigestContext.expected_ensemble_identity must be "
                "a str")
        str_mappings = (
            (self.artifact_date_windows,
             "EvidenceDigestContext.artifact_date_windows"),
            (self.artifact_unit_contracts,
             "EvidenceDigestContext.artifact_unit_contracts"),
            (self.artifact_source_versions,
             "EvidenceDigestContext.artifact_source_versions"),
            (self.artifact_model_versions,
             "EvidenceDigestContext.artifact_model_versions"),
            (self.artifact_rule_ids,
             "EvidenceDigestContext.artifact_rule_ids"),
            (self.artifact_rule_versions,
             "EvidenceDigestContext.artifact_rule_versions"),
        )
        for mapping, name in str_mappings:
            if not isinstance(mapping, Mapping):
                raise EnsembleError(
                    f"{name} must be a Mapping")
            for key, value in mapping.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise EnsembleError(
                        f"{name} must map artifact refs to str values, got "
                        f"{key!r}: {value!r}")
        set_mappings = (
            (self.artifact_finding_identities,
             "EvidenceDigestContext.artifact_finding_identities"),
            (self.artifact_authorized_source_locators,
             "EvidenceDigestContext.artifact_authorized_source_locators"),
        )
        for mapping, name in set_mappings:
            if not isinstance(mapping, Mapping):
                raise EnsembleError(
                    f"{name} must be a Mapping")
            frozen: dict = {}
            for key, value in mapping.items():
                if not isinstance(key, str):
                    raise EnsembleError(
                        f"{name} must map artifact refs to sets, got "
                        f"{key!r}: {value!r}")
                if isinstance(value, (set, frozenset)):
                    frozen[key] = frozenset(value)
                else:
                    raise EnsembleError(
                        f"{name} values must be sets, got {key!r}: "
                        f"{value!r}")
            object.__setattr__(self, name.split(".")[-1], frozen)


# ---------------------------------------------------------------------------
# Deterministic evidence verification (no model)
# ---------------------------------------------------------------------------


def worker_output_content_hash(output: WorkerAnalysisOutput) -> str:
    """Deterministic canonical content address of the ACTUAL worker output.

    Hashes every semantically material field -- attribution
    (``attempt_id``), assessments (item/state/recheck locators/evidence
    hashes/reason codes), findings (identity/priority/support/locators) and
    gap proposals -- with canonical ordering (sorted tuples, sorted keys).
    The result is independent of input ordering and is the value a worker's
    ``output_hash`` declaration AND the authority's registered digest must
    equal; any post-digest change to the output changes this hash.
    """
    return content_hash({
        "attempt_id": output.attempt_id,
        "assessments": [
            {
                "item_id": assessment.item_id,
                "state": assessment.state,
                "source_recheck_locator_ids": sorted(
                    assessment.source_recheck_locator_ids),
                "evidence_hashes": sorted(assessment.evidence_hashes),
                "attempt_id": assessment.attempt_id,
                "reason_codes": sorted(assessment.reason_codes),
            }
            for assessment in sorted(output.assessments,
                                     key=lambda a: a.item_id)
        ],
        "findings": [
            {
                "finding_id": finding.finding_id,
                "proposed_identity": finding.proposed_identity,
                "monitoring_priority": finding.monitoring_priority,
                "supported": finding.supported,
                "source_locator_ids": sorted(finding.source_locator_ids),
                "baseline_item_ref": finding.baseline_item_ref,
            }
            for finding in sorted(output.findings, key=lambda f: f.finding_id)
        ],
        "gap_candidates": [
            {
                "gap_id": gap.gap_id,
                "gap_kind": gap.gap_kind,
                "proposed_identity": gap.proposed_identity,
                "source_locator_ids": sorted(gap.source_locator_ids),
                "originating_attempt_id": gap.originating_attempt_id,
            }
            for gap in sorted(output.gap_candidates, key=lambda g: g.gap_id)
        ],
    })


def verify_attempt(
    attempt: AnalysisAttempt,
    output: WorkerAnalysisOutput,
    context: EvidenceDigestContext,
) -> EvidenceVerification:
    """Deterministic, model-free evidence verification for one attempt.

    Compares EVERY claimed dimension against the independent typed authority
    context (``EvidenceDigestContext``); nothing here calls a model:

    * identity: the attempt's ``ensemble_id`` must equal the authority's
      expected ensemble identity, and every finding identity must be
      authorized for the attempt's artifact -> ``identity_mismatch``;
    * version: input content hash, claimed source revision and model version
      must equal the authority entries -> ``version_mismatch``;
    * date: claimed date window vs authority per-artifact window ->
      ``date_out_of_window``;
    * unit: claimed unit contract vs authority per-artifact contract ->
      ``unit_mismatch``;
    * source: every assessment recheck locator and finding source locator
      must be authorized, and every assessment evidence hash must be
      registered -> ``source_unresolvable``;
    * rule: claimed rule id/version vs authority entries ->
      ``rule_version_mismatch``;
    * artifact integrity: the RECOMPUTED canonical digest of the actual
      ``WorkerAnalysisOutput`` must equal both the attempt's declared
      ``output_hash`` and the authority digest for the artifact; any
      post-digest change to the actual output fails here ->
      ``artifact_hash_mismatch``.

    Every attempted dimension is recorded in ``checked_dimensions`` even when
    it fails, so the record stays auditable when every dimension fails (never
    an empty dimension tuple).  Any failure yields ``failed`` with explicit
    reason codes; a failed record blocks the full analysis.
    """
    verification_id = "verify-" + content_hash({
        "attempt_id": attempt.attempt_id,
        "input_content_hash": attempt.input_content_hash,
        "output_hash": attempt.output_hash,
    })
    checked: list = []
    failure_codes: list = []
    artifact_ref = attempt.output_artifact_ref
    # identity: ensemble identity + every finding identity authorized.
    checked.append("identity")
    if attempt.ensemble_id != context.expected_ensemble_identity:
        failure_codes.append("identity_mismatch")
    finding_identities = set(
        finding.proposed_identity for finding in output.findings)
    authorized_identities = context.artifact_finding_identities.get(
        artifact_ref)
    if finding_identities and (
            authorized_identities is None
            or not finding_identities.issubset(authorized_identities)):
        failure_codes.append("identity_mismatch")
    # version: input hash, source revision, model version.
    checked.append("version")
    if attempt.input_content_hash != context.input_content_hash:
        failure_codes.append("version_mismatch")
    expected_source_version = context.artifact_source_versions.get(
        artifact_ref)
    if expected_source_version is None \
            or attempt.claimed_source_revision != expected_source_version:
        failure_codes.append("version_mismatch")
    expected_model_version = context.artifact_model_versions.get(artifact_ref)
    if expected_model_version is None \
            or attempt.model_version != expected_model_version:
        failure_codes.append("version_mismatch")
    # date: authoritative window must exist and match the claim.
    checked.append("date")
    expected_date = context.artifact_date_windows.get(artifact_ref)
    if expected_date is None or attempt.claimed_date_window != expected_date:
        failure_codes.append("date_out_of_window")
    # unit: authoritative contract must exist and match the claim.
    checked.append("unit")
    expected_unit = context.artifact_unit_contracts.get(artifact_ref)
    if expected_unit is None or attempt.claimed_unit_contract != expected_unit:
        failure_codes.append("unit_mismatch")
    # source: locators authorized + evidence hashes registered.
    checked.append("source")
    authorized_locators = context.artifact_authorized_source_locators.get(
        artifact_ref)
    claimed_locators = set(
        locator
        for assessment in output.assessments
        for locator in assessment.source_recheck_locator_ids) | set(
        locator
        for finding in output.findings
        for locator in finding.source_locator_ids)
    if claimed_locators and (
            authorized_locators is None
            or not claimed_locators.issubset(authorized_locators)):
        failure_codes.append("source_unresolvable")
    evidence_hashes = [
        evidence_hash
        for assessment in output.assessments
        for evidence_hash in assessment.evidence_hashes
    ]
    if evidence_hashes and not all(
            hash_value in context.evidence_digests
            for hash_value in evidence_hashes):
        failure_codes.append("source_unresolvable")
    # rule: authoritative rule id/version must match the claims.
    checked.append("rule")
    expected_rule_id = context.artifact_rule_ids.get(artifact_ref)
    if expected_rule_id is None \
            or attempt.claimed_rule_id != expected_rule_id:
        failure_codes.append("rule_version_mismatch")
    expected_rule_version = context.artifact_rule_versions.get(artifact_ref)
    if expected_rule_version is None \
            or attempt.claimed_rule_version != expected_rule_version:
        failure_codes.append("rule_version_mismatch")
    # artifact integrity: recompute the ACTUAL output digest and compare it
    # to both the attempt declaration and the authority digest.
    checked.append("artifact_integrity")
    actual_output_hash = worker_output_content_hash(output)
    if actual_output_hash != attempt.output_hash:
        failure_codes.append("artifact_hash_mismatch")
    expected_output = context.output_digests.get(artifact_ref)
    if expected_output is None or actual_output_hash != expected_output:
        failure_codes.append("artifact_hash_mismatch")
    result = "failed" if failure_codes else "passed"
    return EvidenceVerification(
        verification_id=verification_id,
        attempt_id=attempt.attempt_id,
        checked_dimensions=tuple(sorted(set(checked))),
        result=result,
        failure_reason_codes=tuple(sorted(set(failure_codes))),
    )


# ---------------------------------------------------------------------------
# Gap search (proposals only, never lifecycle actions)
# ---------------------------------------------------------------------------


def search_gaps(
    *,
    baseline_items: Sequence[ReferenceBaselineItem],
    worker_outputs: Mapping[str, WorkerAnalysisOutput],
    current_source_locator_ids: Sequence[str],
    originating_attempt_id: str,
) -> Tuple[GapCandidate, ...]:
    """Deterministic gap search between the reference baseline and the
    current pack.

    Produces three candidate kinds:

    * ``baseline_missed_current`` -- a baseline item with no assessment in
      any worker output;
    * ``current_missed_baseline`` -- a current finding identity with no
      matching baseline claimed identity;
    * ``source_unrepresented`` -- an assessed baseline item whose source
      locators are absent from the current pack's source locator set.

    Returns PROPOSALS only: nothing here establishes or closes a risk (risk
    lifecycle stays in :mod:`mm_r4.lifecycle`).
    """
    candidates: list = []
    assessed_item_ids = {
        assessment.item_id
        for output in worker_outputs.values()
        for assessment in output.assessments
    }
    current_source_set = set(current_source_locator_ids)
    baseline_identities = {
        item.claimed_identity for item in baseline_items
    }
    current_identities = {
        finding.proposed_identity
        for output in worker_outputs.values()
        for finding in output.findings
    }
    for item in sorted(baseline_items, key=lambda b: b.item_id):
        if item.item_id not in assessed_item_ids:
            candidates.append(GapCandidate(
                gap_id="gap-" + content_hash({
                    "kind": "baseline_missed_current",
                    "item_id": item.item_id,
                }),
                gap_kind="baseline_missed_current",
                proposed_identity=item.claimed_identity,
                source_locator_ids=item.source_locator_ids,
                originating_attempt_id=originating_attempt_id,
            ))
        elif not current_source_set.intersection(item.source_locator_ids):
            candidates.append(GapCandidate(
                gap_id="gap-" + content_hash({
                    "kind": "source_unrepresented",
                    "item_id": item.item_id,
                }),
                gap_kind="source_unrepresented",
                proposed_identity=item.claimed_identity,
                source_locator_ids=item.source_locator_ids,
                originating_attempt_id=originating_attempt_id,
            ))
    for identity in sorted(current_identities - baseline_identities):
        first_locator = sorted(
            locator
            for output in worker_outputs.values()
            for finding in output.findings
            if finding.proposed_identity == identity
            for locator in finding.source_locator_ids
        )
        candidates.append(GapCandidate(
            gap_id="gap-" + content_hash({
                "kind": "current_missed_baseline",
                "identity": identity,
            }),
            gap_kind="current_missed_baseline",
            proposed_identity=identity,
            source_locator_ids=tuple(first_locator),
            originating_attempt_id=originating_attempt_id,
        ))
    return tuple(sorted(candidates, key=lambda c: c.gap_id))


# ---------------------------------------------------------------------------
# Conflict derivation
# ---------------------------------------------------------------------------


def derive_conflicts(
    *,
    attempts: Sequence[AnalysisAttempt],
    worker_outputs: Mapping[str, WorkerAnalysisOutput],
    baseline_items: Sequence[ReferenceBaselineItem],
) -> Tuple[ConflictVisibility, ...]:
    """Derive visible cross-attempt conflicts from worker findings.

    The merge ONLY forms conflict relations (never a verdict that hides
    disagreement): every derived conflict has ``hidden=False``, and a
    high-risk or important conflict (high priority, ``mutual_negation`` or
    ``baseline_miss``) is additionally protected at the contract level from
    ever being constructed hidden.  Majority voting and adjudication can
    therefore never hide them.
    """
    conflicts: list = []
    by_identity: Dict[str, list] = {}
    for output in worker_outputs.values():
        for finding in output.findings:
            by_identity.setdefault(finding.proposed_identity, []).append(
                (output.attempt_id, finding.monitoring_priority,
                 finding.supported))
    for identity in sorted(by_identity):
        rows = by_identity[identity]
        supporters = sorted({attempt_id for attempt_id, _priority, supported
                             in rows if supported})
        negators = sorted({attempt_id for attempt_id, _priority, supported
                           in rows if not supported})
        priorities = sorted({priority for _attempt_id, priority, _supported
                             in rows}, key=_priority_rank)
        members = sorted(set(supporters) | set(negators))
        if supporters and negators:
            relation = "mutual_negation"
            display_state = "visible_conflict"
        elif len(supporters) >= 2:
            if len(set(priorities)) > 1:
                relation = "graded_conflict"
            else:
                relation = "shared_finding"
            display_state = "visible_conflict"
        elif supporters or negators:
            relation = "single_model_new"
            display_state = "needs_attention"
        else:  # pragma: no cover - unreachable by construction
            continue
        conflicts.append(ConflictVisibility(
            conflict_id="conflict-" + content_hash({
                "identity": identity,
                "members": members,
                "relation": relation,
            }),
            member_attempt_ids=tuple(members),
            monitoring_priority=priorities[0],
            relation=relation,
            display_state=display_state,
            hidden=False,
        ))
    assessed_item_ids = {
        assessment.item_id
        for output in worker_outputs.values()
        for assessment in output.assessments
    }
    for item in sorted(baseline_items, key=lambda b: b.item_id):
        if item.item_id in assessed_item_ids:
            continue
        # An unassessed baseline item is important disagreement: it stays
        # visible at high priority until resolved (fail-safe by default).
        conflicts.append(ConflictVisibility(
            conflict_id="conflict-" + content_hash({
                "baseline_item": item.item_id,
                "kind": "baseline_miss",
            }),
            member_attempt_ids=tuple(
                sorted(attempt.attempt_id for attempt in attempts)),
            monitoring_priority=MONITORING_PRIORITY_HIGH,
            relation="baseline_miss",
            display_state="visible_baseline_miss",
            hidden=False,
        ))
    return tuple(sorted(conflicts, key=lambda c: c.conflict_id))


# ---------------------------------------------------------------------------
# Adjudicator + adjudication rule
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Adjudicator:
    """Independent adjudicator identity; must not collide with any worker."""

    binding_id: str
    session_id: str
    model_id: str
    model_version: str

    def __post_init__(self) -> None:
        for name, value in (
                ("binding_id", self.binding_id),
                ("session_id", self.session_id),
                ("model_id", self.model_id),
                ("model_version", self.model_version)):
            if not isinstance(value, str) or not value.strip():
                raise EnsembleError(f"Adjudicator.{name} must be non-empty")


def _adjudicate(
    *,
    ensemble_size: int,
    attempts: Sequence[AnalysisAttempt],
    conflicts: Tuple[ConflictVisibility, ...],
    verifications: Tuple[EvidenceVerification, ...],
    adjudicator: Optional[Adjudicator],
    consensus_leaf: Optional[str],
) -> Tuple[AdjudicationBinding, bool]:
    """Deterministic adjudication rule (no model).

    Order of precedence:

    1. A failed/not-evaluable verification blocks any supporting outcome
       (``needs_user_attention``).
    2. No independent adjudicator -> ``needs_user_attention``.
    3. High-risk or important disagreement (high priority, mutual negation,
       baseline miss) or any residual conflict in a single-model run ->
       ``needs_user_attention`` (majority cannot close it).
    4. Otherwise: full agreement -> ``merged_supported``; distinct coherent
       results -> ``distinct_supported``.
    """
    verification_blocked = any(
        verification.result != "passed" for verification in verifications)
    reviewed_artifact_refs = tuple(
        sorted(attempt.output_artifact_ref for attempt in attempts))
    if adjudicator is None:
        return AdjudicationBinding(
            binding_id=_UNRESOLVED_BINDING_ID,
            session_id=_UNRESOLVED_SESSION_ID,
            model_id=_UNRESOLVED_MODEL_ID,
            model_version=_UNRESOLVED_MODEL_VERSION,
            outcome=AdjudicationOutcome.NEEDS_USER_ATTENTION,
            reviewed_artifact_refs=reviewed_artifact_refs,
        ), verification_blocked
    if verification_blocked:
        return AdjudicationBinding(
            binding_id=adjudicator.binding_id,
            session_id=adjudicator.session_id,
            model_id=adjudicator.model_id,
            model_version=adjudicator.model_version,
            outcome=AdjudicationOutcome.NEEDS_USER_ATTENTION,
            reviewed_artifact_refs=reviewed_artifact_refs,
        ), True
    important = any(
        conflict.monitoring_priority == MONITORING_PRIORITY_HIGH
        or conflict.relation in NON_HIDEABLE_RELATIONS
        for conflict in conflicts)
    if ensemble_size == 1 and conflicts:
        # A single model cannot adjudicate its own residual conflict.
        important = True
    if important:
        return AdjudicationBinding(
            binding_id=adjudicator.binding_id,
            session_id=adjudicator.session_id,
            model_id=adjudicator.model_id,
            model_version=adjudicator.model_version,
            outcome=AdjudicationOutcome.NEEDS_USER_ATTENTION,
            reviewed_artifact_refs=reviewed_artifact_refs,
        ), False
    if consensus_leaf is not None:
        outcome = AdjudicationOutcome.MERGED_SUPPORTED
    else:
        outcome = AdjudicationOutcome.DISTINCT_SUPPORTED
    return AdjudicationBinding(
        binding_id=adjudicator.binding_id,
        session_id=adjudicator.session_id,
        model_id=adjudicator.model_id,
        model_version=adjudicator.model_version,
        outcome=outcome,
        reviewed_artifact_refs=reviewed_artifact_refs,
    ), False


# ---------------------------------------------------------------------------
# Shared ensemble entry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EnsembleResult:
    """Deterministic result of one offline ensemble run.

    ``consensus_leaf`` is only ever populated for ``ensemble_size >= 2`` and
    is only a signal: a single-model run exposes NO consensus/agreement leaf.
    ``verification_blocked`` is True when evidence verification failed before
    adjudication (the outcome is then ``needs_user_attention``).
    """

    ensemble_id: str
    ensemble_size: int
    input_content_hash: str
    attempts: Tuple[AnalysisAttempt, ...]
    verifications: Tuple[EvidenceVerification, ...]
    gap_candidates: Tuple[GapCandidate, ...]
    conflicts: Tuple[ConflictVisibility, ...]
    adjudication: AdjudicationBinding
    consensus_leaf: Optional[str] = None
    verification_blocked: bool = False


def run_ensemble(
    *,
    ensemble_id: str,
    input_content_hash: str,
    attempts: Sequence[AnalysisAttempt],
    worker_outputs: Mapping[str, WorkerAnalysisOutput],
    baseline_items: Sequence[ReferenceBaselineItem],
    digest_context: EvidenceDigestContext,
    adjudicator: Optional[Adjudicator] = None,
    verifier: Optional[
        Callable[[AnalysisAttempt, WorkerAnalysisOutput,
                  EvidenceDigestContext], EvidenceVerification]
    ] = None,
    current_source_locator_ids: Sequence[str] = (),
) -> EnsembleResult:
    """Run one offline ensemble closure.

    The ``ensemble_size`` gate is the FIRST action: size < 1 raises
    :class:`EnsembleError` before any attempt, gap search, verification or
    adjudication side effect.
    """
    verify = verifier if verifier is not None else verify_attempt
    ensemble_size = require_positive_ensemble_size(len(attempts))
    if not isinstance(ensemble_id, str) or not ensemble_id.strip():
        raise EnsembleError("ensemble_id must be a non-empty string")
    if not isinstance(input_content_hash, str) \
            or len(input_content_hash) != 64:
        raise EnsembleError(
            "input_content_hash must be a 64-hex sha256")
    attempt_list = tuple(sorted(attempts, key=lambda a: a.attempt_id))
    if len(attempt_list) != ensemble_size:
        raise EnsembleError(
            "attempts length must equal the ensemble size")
    attempt_ids = tuple(sorted(attempt.attempt_id for attempt in attempt_list))
    if len(set(attempt_ids)) != len(attempt_ids):
        raise EnsembleError("attempt_ids must be unique within an ensemble")
    if set(worker_outputs) != set(attempt_ids):
        raise EnsembleError(
            "worker_outputs keys must match the attempt ids exactly")
    for key, output in worker_outputs.items():
        if output.attempt_id != key:
            raise EnsembleError(
                "worker_outputs mapping key must equal the output's "
                f"attempt_id; key {key!r} carries output for attempt "
                f"{output.attempt_id!r}")
    attempt_by_id = {attempt.attempt_id: attempt for attempt in attempt_list}
    for key, output in worker_outputs.items():
        if key not in attempt_by_id:
            raise EnsembleError(
                "worker_outputs key must resolve to a declared "
                f"AnalysisAttempt; no attempt {key!r}")
    baseline_list = tuple(baseline_items)
    baseline_ids = [item.item_id for item in baseline_list]
    if len(set(baseline_ids)) != len(baseline_ids):
        raise EnsembleError("baseline item ids must be unique")
    baseline_identity = {item.item_id: item for item in baseline_list}
    for output in worker_outputs.values():
        for assessment in output.assessments:
            if assessment.item_id not in baseline_identity:
                raise EnsembleError(
                    "assessment references unknown baseline item "
                    f"{assessment.item_id!r}")
    # Isolation identity rules (same input version; unique sessions/contexts).
    for attempt in attempt_list:
        if attempt.role != _ATTEMPT_ROLE_WORKER:
            raise EnsembleError(
                "analysis attempts must have role 'worker'; adjudication is "
                "carried by the separate Adjudicator binding")
        if attempt.input_content_hash != input_content_hash:
            raise EnsembleError(
                "all attempts must share the same input_content_hash "
                f"(same question, same input version); attempt "
                f"{attempt.attempt_id!r} diverges")
    if ensemble_size >= 2:
        binding_ids = [attempt.binding_id for attempt in attempt_list]
        session_ids = [attempt.session_id for attempt in attempt_list]
        context_hashes = [
            attempt.independent_context_hash for attempt in attempt_list]
        if len(set(binding_ids)) != ensemble_size:
            raise EnsembleError(
                "N-way ensembles require distinct binding_ids per attempt")
        if len(set(session_ids)) != ensemble_size:
            raise EnsembleError(
                "N-way ensembles require distinct session_ids per attempt")
        if len(set(context_hashes)) != ensemble_size:
            raise EnsembleError(
                "N-way ensembles require distinct independent_context_hash "
                "per attempt")
    if adjudicator is not None:
        worker_binding_ids = {
            attempt.binding_id for attempt in attempt_list}
        worker_session_ids = {
            attempt.session_id for attempt in attempt_list}
        if adjudicator.binding_id in worker_binding_ids:
            raise EnsembleError(
                "a worker may not adjudicate itself: adjudicator binding_id "
                "collides with a worker attempt")
        if adjudicator.session_id in worker_session_ids:
            raise EnsembleError(
                "a worker may not adjudicate itself: adjudicator session_id "
                "collides with a worker attempt")
    # Deterministic evidence verification precedes adjudication.
    verifications = tuple(
        verify(attempt, worker_outputs[attempt.attempt_id], digest_context)
        for attempt in attempt_list)
    # Gap search proposes candidates only (never lifecycle actions).
    gap_candidates = search_gaps(
        baseline_items=baseline_list,
        worker_outputs=worker_outputs,
        current_source_locator_ids=tuple(current_source_locator_ids),
        originating_attempt_id=attempt_ids[0],
    )
    conflicts = derive_conflicts(
        attempts=attempt_list,
        worker_outputs=worker_outputs,
        baseline_items=baseline_list,
    )
    consensus_leaf = _consensus_leaf(ensemble_size, worker_outputs)
    adjudication, verification_blocked = _adjudicate(
        ensemble_size=ensemble_size,
        attempts=attempt_list,
        conflicts=conflicts,
        verifications=verifications,
        adjudicator=adjudicator,
        consensus_leaf=consensus_leaf,
    )
    return EnsembleResult(
        ensemble_id=ensemble_id,
        ensemble_size=ensemble_size,
        input_content_hash=input_content_hash,
        attempts=attempt_list,
        verifications=verifications,
        gap_candidates=gap_candidates,
        conflicts=conflicts,
        adjudication=adjudication,
        consensus_leaf=consensus_leaf,
        verification_blocked=verification_blocked,
    )


def _consensus_leaf(
    ensemble_size: int,
    worker_outputs: Mapping[str, WorkerAnalysisOutput],
) -> Optional[str]:
    """Agreement signal shared by ALL workers; None for a single model.

    A single-model run exposes NO consensus/agreement leaf.  For N-way runs
    the leaf is only a signal; conflicts remain visible regardless.
    """
    if ensemble_size < 2:
        return None
    supported_by_attempt: Dict[str, set] = {}
    for attempt_id, output in worker_outputs.items():
        supported_by_attempt[attempt_id] = {
            finding.proposed_identity
            for finding in output.findings
            if finding.supported
        }
    if not supported_by_attempt:
        return None
    common = set.intersection(*supported_by_attempt.values())
    if not common:
        return None
    return "|".join(sorted(common))
