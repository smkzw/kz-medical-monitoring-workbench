"""R4-D01 AE/MH lifecycle adapter (worker_03).

This module is the *only* R4 surface that touches R2 :class:`RiskLifecycle`.
It never copies lifecycle enums, never forks lifecycle authority, and never
accesses private lifecycle internals.  It uses the frozen R2 public API:

* :class:`RiskLifecycle` (establish / transition / register_candidate /
  issue_adjudication / issue_user_adjudication / merge / split)
* :class:`RiskCandidate` (the real candidate produced by
  :mod:`mm_r4.aemh`)
* :class:`AdjudicationEvidenceBinding`, :class:`AdjudicationOutcome`,
  :class:`RiskTransitionType`, :class:`RiskLifecycleState`
* :class:`AcceptanceService` and real baseline-eligible snapshots built from
  public R2 acceptance / identity / mapping APIs (no R2 test-helper imports).

Round-2 corrections (Codex findings):

* No private R2 import or access.  ``must_carry_forward`` reads the public
  ``RiskInstance.severity``, ``clinical_risk_flags`` and
  ``ever_user_confirmed`` fields only.
* The pre-establishment identity is the *exact* public R2 identity:
  scope/classifier are read from the candidate ``detail`` (stored there by
  :mod:`mm_r4.aemh` via public :func:`make_risk_identity`) and passed to
  ``RiskLifecycle.establish`` so ``RiskInstance.risk_identity_id`` equals
  the candidate-ref identity.  No custom parallel identity hash and no
  same-subject fallback.
* Automatic close requires a closed R4 :class:`CoverageLedger` whose
  expected unit ids exactly equal the supplied N+1 unit results, whose
  ``is_domain_complete(summary)`` is true, and whose
  ``UnitEvaluation.provenance_snapshot_id`` equals the accepted
  ``coverage_snapshot_id``.  Missing/open/mismatched/incomplete/partial/
  truncated/failed/missing coverage, L1 not-evaluable, or a wrong snapshot
  keeps the risk active and surfaces a coverage-gap reason.
* L1 ``not_evaluable`` carries an active risk forward and exposes the gap;
  it never by itself changes L3 (matrix §3.4/§3.6).
* Lineage/version change for the same stable clinical event calls public
  R2 ``SUPERSEDED``; competing incompatible identities that claim the same
  old event use public ``identity_ambiguous`` and block close/merge.

Contract (frozen matrix §3.5, §3.6; context §11):

1. Only **verified positive** AE/MH unit outputs become registered R2
   candidates; a candidate is never auto-promoted to an established risk
   merely because it exists.  Establishment requires a service-issued
   ``establish`` adjudication with ``distinct_supported`` outcome against
   a real baseline-eligible source snapshot.
2. Establishment projects the **monitoring priority** to
   ``RiskInstance.severity`` (high/medium/low/unknown).  SAE/AESI
   seriousness criteria ride through the candidate ``signal_type`` and
   R2's own ``clinical_risk_flags`` derivation; R4 never writes clinical
   flags directly.  Intensity/CTCAE grade never projects to severity.
3. Low/medium monitoring-priority risks machine-close only on a
   *subsequent accepted full snapshot* **plus** a closed R4 coverage
   ledger proving complete N+1 coverage, with a
   ``rejected_by_evidence`` adjudication and
   ``close_reason=resolved_by_data``.  High / SAE / AESI / user-confirmed
   risks carry forward; closed risks reopen only through a legal
   adjudicated transition; identity ambiguity blocks merge/close; lineage
   change supersedes or terminates not-evaluable.
4. ``boundary`` unit results stay candidates -- they are never
   established as risks by machine adjudication (matrix §3.6: uncertain
   identity/time keeps the clue as a candidate).
5. N→N+1 reconciliation persists the *exact* matching identity: an
   established risk with a matching positive identity in N+1 persists
   (carry-forward, no transition).  A different concept/event for the same
   participant does NOT keep the old identity alive.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ..domain.acceptance import (
    AcceptanceService,
    SnapshotAcceptanceState,
)
from ..domain.identity import make_risk_identity
from ..domain.risk import (
    AdjudicationEvidenceBinding,
    AdjudicationOutcome,
    RiskCandidate,
    RiskInstance,
    RiskLifecycle,
    RiskLifecycleState,
    RiskTransitionType,
)

from .contracts import (
    L1Disposition,
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_MEDIUM,
    RiskDomainUnitResult,
    RiskInstanceRef,
    candidate_identity_classifier,
    candidate_lineage_fingerprint,
    candidate_identity_scope,
    candidate_machine_close_forbidden,
    candidate_rights_or_safety_critical,
    candidate_stable_core,
)
from .coverage import CoverageLedger, is_domain_complete

__all__ = [
    "LifecycleAdapterError",
    "PromotionOutcome",
    "ReconcileResult",
    "R4LifecycleAdapter",
    "map_priority_to_r2_severity",
    "CLOSE_REASON_RESOLVED_BY_DATA",
    "MACHINE_ACTOR",
]


#: The matrix §3.6 ``close_reason`` value for data-driven resolution.
CLOSE_REASON_RESOLVED_BY_DATA = "resolved_by_data"

#: Default machine actor for R4 adjudication issuance.  R2 allows
#: ``system_policy`` as a trusted machine actor independent of the local OS
#: user, so R4 uses it for deterministic machine adjudication.
MACHINE_ACTOR = "system_policy"


def map_priority_to_r2_severity(monitoring_priority: str) -> str:
    """Project a D01 monitoring priority to an R2 ``RiskInstance.severity``.

    Only monitoring priority projects here (matrix §3.5).  Unknown stays
    unknown; it is never defaulted to low or zero.
    """
    if monitoring_priority == MONITORING_PRIORITY_HIGH:
        return "high"
    if monitoring_priority == MONITORING_PRIORITY_MEDIUM:
        return "medium"
    if monitoring_priority == MONITORING_PRIORITY_LOW:
        return "low"
    return "unknown"


class LifecycleAdapterError(Exception):
    """An R4 lifecycle adapter invariant was violated."""


@dataclass(frozen=True)
class PromotionOutcome:
    """Outcome of promoting one unit result through R2.

    * ``registered_candidate_ids``: R2 candidate IDs that were registered
      (positive/boundary only).
    * ``established_risk_ids``: ``(risk_instance_id, risk_identity_id)``
      pairs for risks established from positive candidates.
    * ``skipped_dispositions``: L1 dispositions that produced no promotion
      (negative / not_evaluable / not_applicable).
    """

    unit_id: str
    subject_ref: str
    l1_disposition: str
    registered_candidate_ids: Tuple[str, ...] = ()
    established_risk_ids: Tuple[Tuple[str, str], ...] = ()
    skipped_dispositions: Tuple[str, ...] = ()
    not_evaluable_reason: str = ""

    @property
    def established_any(self) -> bool:
        return bool(self.established_risk_ids)

    @property
    def registered_any(self) -> bool:
        return bool(self.registered_candidate_ids)


@dataclass(frozen=True)
class ReconcileResult:
    """Outcome of one N→N+1 reconciliation pass.

    Each list holds :class:`RiskInstance` values in their post-reconciliation
    state.  ``coverage_gaps`` carries human-readable reasons when a risk
    could not be closed because the R4 coverage proof was missing or
    incomplete.
    """

    persisted: Tuple[RiskInstance, ...] = ()
    closed: Tuple[RiskInstance, ...] = ()
    carry_forward: Tuple[RiskInstance, ...] = ()
    superseded: Tuple[RiskInstance, ...] = ()
    identity_ambiguous: Tuple[RiskInstance, ...] = ()
    coverage_gaps: Tuple[str, ...] = ()

    def total(self) -> int:
        return (
            len(self.persisted) + len(self.closed) + len(self.carry_forward)
            + len(self.superseded) + len(self.identity_ambiguous))


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

@dataclass
class R4LifecycleAdapter:
    """Adapts R4 AE/MH unit results to the frozen R2 :class:`RiskLifecycle`.

    The adapter owns *no* lifecycle state of its own: every established
    risk, transition and adjudication lives inside the wrapped R2
    :class:`RiskLifecycle`.  The adapter is a thin, deterministic mapping
    layer that enforces the frozen matrix projection rules.

    Construction requires a real :class:`AcceptanceService` whose local
    user matches the adapter's ``actor`` so the same service can both
    issue baseline-eligible snapshots and verify close coverage.
    """

    lifecycle: RiskLifecycle
    acceptance_service: AcceptanceService
    project_id: str
    actor: str = MACHINE_ACTOR

    def __post_init__(self) -> None:
        if not isinstance(self.lifecycle, RiskLifecycle):
            raise LifecycleAdapterError(
                "lifecycle must be a real mm_r2 RiskLifecycle")
        if not isinstance(self.acceptance_service, AcceptanceService):
            raise LifecycleAdapterError(
                "acceptance_service must be a real mm_r2 AcceptanceService")
        if not self.project_id:
            raise LifecycleAdapterError("project_id is required")
        if not self.actor:
            raise LifecycleAdapterError("actor is required")

    # -- candidate registration ------------------------------------------

    def _is_promotable_disposition(self, disposition: str) -> bool:
        """Only positive/boundary unit outputs carry promotable candidates.

        A negative/not_evaluable/not_applicable unit never registers a
        candidate (matrix §3.3, §3.6).
        """
        return disposition in (L1Disposition.POSITIVE, L1Disposition.BOUNDARY)

    def _verify_candidate_identity(self, candidate: RiskCandidate) -> str:
        """Fail closed *before* any side effect when a candidate lacks
        complete identity metadata (Codex round-3 finding 3).

        Requires all of: scope, classifier, stable_core,
        lineage_fingerprint, and exact public ``risk_identity_id`` on
        the candidate detail.  The candidate must be one-to-one with
        its ``RiskCandidateRef`` -- no missing or mismatched identity.
        """
        cid = candidate.candidate_id
        scope = candidate_identity_scope(candidate)
        classifier = candidate_identity_classifier(candidate)
        stable_core = candidate_stable_core(candidate)
        lineage_fp = candidate_lineage_fingerprint(candidate)
        rid = str(candidate.detail.get("risk_identity_id", ""))
        if candidate.project_id != self.project_id:
            raise LifecycleAdapterError(
                f"candidate {cid!r} project_id {candidate.project_id!r} "
                f"does not match adapter project_id {self.project_id!r}")
        if not scope or any(
                not isinstance(item, str) or not item for item in scope):
            raise LifecycleAdapterError(
                f"candidate {cid!r} detail lacks identity scope; "
                f"cannot register/establish without complete metadata")
        if not classifier:
            raise LifecycleAdapterError(
                f"candidate {cid!r} detail lacks identity classifier; "
                f"cannot register/establish without complete metadata")
        if not stable_core:
            raise LifecycleAdapterError(
                f"candidate {cid!r} detail lacks stable_core; "
                f"cannot register/establish without complete metadata")
        if not lineage_fp:
            raise LifecycleAdapterError(
                f"candidate {cid!r} detail lacks lineage_fingerprint; "
                f"cannot register/establish without complete metadata")
        if not rid:
            raise LifecycleAdapterError(
                f"candidate {cid!r} detail lacks risk_identity_id; "
                f"cannot register/establish without complete metadata")
        detail_domain = str(candidate.detail.get("domain", ""))
        if not detail_domain or detail_domain != candidate.domain:
            raise LifecycleAdapterError(
                f"candidate {cid!r} identity domain is missing or does not "
                f"match candidate.domain")
        if stable_core != classifier:
            raise LifecycleAdapterError(
                f"candidate {cid!r} stable_core does not exactly match its "
                f"identity classifier")

        # Recompute the identity with the frozen public R2 authority before
        # registration, adjudication, or establishment.  Merely checking that
        # metadata is non-empty would allow a non-empty tampered identity to
        # create lifecycle side effects before the mismatch was noticed.
        identity = make_risk_identity(
            project_id=candidate.project_id,
            subject_ref=candidate.subject_ref,
            domain=candidate.domain,
            scope=scope,
            classifier=classifier,
        )
        expected_lineage = "|".join(identity.scope)
        if lineage_fp != expected_lineage:
            raise LifecycleAdapterError(
                f"candidate {cid!r} lineage_fingerprint does not exactly "
                f"match its public R2 identity scope")
        if rid != identity.risk_identity_id:
            raise LifecycleAdapterError(
                f"candidate {cid!r} risk_identity_id {rid!r} does not match "
                f"the public R2 identity {identity.risk_identity_id!r}")
        return identity.risk_identity_id

    def _verify_unit_candidate_refs(
        self, unit_result: RiskDomainUnitResult,
    ) -> None:
        """Validate the whole D01 candidate/ref join before registration.

        Validation is all-or-nothing: a malformed second candidate cannot
        leave the first one registered.  Each candidate must have exactly one
        reference, and that reference must bind the same public R2 identity
        and source locator carried by the candidate provenance.
        """
        candidates = tuple(unit_result.r2_candidates)
        refs = tuple(unit_result.risk_candidate_refs)
        candidate_ids = [candidate.candidate_id for candidate in candidates]
        ref_ids = [ref.candidate_id for ref in refs]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise LifecycleAdapterError(
                f"unit {unit_result.unit_id!r} contains duplicate R2 "
                f"candidate ids")
        if len(ref_ids) != len(set(ref_ids)):
            raise LifecycleAdapterError(
                f"unit {unit_result.unit_id!r} contains duplicate "
                f"RiskCandidateRef candidate ids")
        if set(candidate_ids) != set(ref_ids):
            raise LifecycleAdapterError(
                f"unit {unit_result.unit_id!r} candidates and "
                f"RiskCandidateRefs are not one-to-one")

        refs_by_id = {ref.candidate_id: ref for ref in refs}
        for candidate in candidates:
            expected_identity_id = self._verify_candidate_identity(candidate)
            ref = refs_by_id[candidate.candidate_id]
            if ref.risk_identity_id != expected_identity_id:
                raise LifecycleAdapterError(
                    f"candidate ref {ref.candidate_id!r} risk_identity_id "
                    f"does not match its exact public R2 identity")
            full_locator_id = str(
                candidate.detail.get("full_locator_id", ""))
            if (not full_locator_id or ref.locator is None
                    or ref.locator.locator_id() != full_locator_id):
                raise LifecycleAdapterError(
                    f"candidate ref {ref.candidate_id!r} is not bound to "
                    f"the candidate's exact source locator")

    def register_candidates(self, unit_result: RiskDomainUnitResult) -> Tuple[str, ...]:
        """Register the R2 candidates carried by a unit result.

        Each candidate is identity-verified *before* registration (Codex
        round-3 finding 3).  Returns the candidate IDs registered.
        Non-promotable dispositions register nothing.
        """
        if not self._is_promotable_disposition(unit_result.l1_disposition):
            return ()
        self._verify_unit_candidate_refs(unit_result)
        ids: List[str] = []
        for cand in unit_result.r2_candidates:
            self.lifecycle.register_candidate(cand)
            ids.append(cand.candidate_id)
        return tuple(ids)

    # -- establishment ---------------------------------------------------

    def _ensure_source_snapshot(self, candidate: RiskCandidate) -> None:
        """Ensure the candidate's source snapshot is baseline-eligible in
        the adapter's acceptance service."""
        if not candidate.source_snapshot_id:
            raise LifecycleAdapterError(
                f"candidate {candidate.candidate_id!r} has no source_snapshot_id")
        rec = self.acceptance_service.get(candidate.source_snapshot_id)
        if rec.project_id != self.project_id:
            raise LifecycleAdapterError(
                f"candidate source snapshot project_id {rec.project_id!r} "
                f"does not match adapter project_id {self.project_id!r}")
        if rec.blocked:
            raise LifecycleAdapterError(
                f"candidate source snapshot {candidate.source_snapshot_id!r} "
                f"is blocked")
        if rec.state != SnapshotAcceptanceState.BASELINE_ELIGIBLE:
            raise LifecycleAdapterError(
                f"candidate source snapshot {candidate.source_snapshot_id!r} "
                f"is not baseline_eligible (state={rec.state.value})")

    def establish_positive_candidate(
        self,
        candidate: RiskCandidate,
        *,
        monitoring_priority: str,
    ) -> RiskInstance:
        """Establish one positive candidate as an R2 risk.

        Projects monitoring priority → R2 severity (matrix §3.5).  Clinical
        flags are derived by R2 from the candidate ``signal_type``; R4
        never writes them directly.

        Fail-closed identity (Codex round-3 finding 3): the candidate must
        carry complete scope, classifier, stable_core, lineage_fingerprint
        and exact public ``risk_identity_id``.  These are verified *before*
        any adjudication or establishment side effect.  No arbitrary
        scope/classifier overrides are accepted -- the identity comes
        exclusively from the candidate detail.

        Frozen D04 §8.1/§10 criticality normalization: the candidate-detail
        flags ``rights_or_safety_critical`` / ``machine_close_forbidden``
        are read through the public strict-boolean readers *before* any
        side effect.  If either is true, the effective priority is forced
        to high regardless of the caller-supplied ``monitoring_priority``
        (e.g. a mistaken ``medium``), the R2 instance is established with
        ``severity=high``, and the persisted severity is asserted high or
        the adapter fails closed.  The flags never add R2 fields and never
        touch ``clinical_risk_flags``; D01-D03 candidates carrying neither
        key behave exactly as before.

        Raises :class:`LifecycleAdapterError` if the identity metadata is
        incomplete, the candidate is not registered, its source snapshot
        is not baseline-eligible, or the established identity diverges.
        """
        if not monitoring_priority:
            raise LifecycleAdapterError(
                "establish requires an explicit monitoring_priority")
        # Fail closed BEFORE any side effect.
        self._verify_candidate_identity(candidate)
        # Frozen D04 §8.1/§10: strict public boolean readers on the
        # candidate detail.  Missing → False; a present non-bool fails
        # closed (CoverageValidationError) before any adjudication or
        # establishment side effect.  Either flag true forces effective
        # priority high even if the caller passes medium; the persisted
        # R2 severity must then be high or the adapter fails closed.
        # The flags never write R2 fields, never extend
        # ``clinical_risk_flags``, and change nothing for D01-D03
        # candidates that carry neither key.
        force_high = (
            candidate_rights_or_safety_critical(candidate)
            or candidate_machine_close_forbidden(candidate))
        eff_priority = (
            MONITORING_PRIORITY_HIGH if force_high else monitoring_priority)
        self._ensure_source_snapshot(candidate)
        eff_scope = candidate_identity_scope(candidate)
        eff_classifier = candidate_identity_classifier(candidate)
        expected_id = str(candidate.detail.get("risk_identity_id", ""))
        evidence = AdjudicationEvidenceBinding(
            candidate_id=candidate.candidate_id,
            snapshot_id=candidate.source_snapshot_id,
            rule_activation_id=candidate.rule_activation_id,
            mapping_result_id=candidate.mapping_result_id,
            knowledge_pack_id=candidate.knowledge_pack_id,
        )
        adj = self.lifecycle.issue_adjudication(
            project_id=self.project_id,
            outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish",
            evidence=evidence,
            candidate=candidate,
            rationale=(
                "R4 D01 machine adjudication: verified positive AE/MH "
                "under-reporting clue with full coverage"),
        )
        severity = map_priority_to_r2_severity(eff_priority)
        instance = self.lifecycle.establish(
            candidate,
            adj,
            severity=severity,
            scope=eff_scope,
            classifier=eff_classifier,
            actor=self.actor,
            acceptance_service=self.acceptance_service,
        )
        # Post-establish high-severity assertion for flagged candidates
        # (frozen D04 §10.4): the forced high priority MUST be persisted
        # as R2 ``RiskInstance.severity=high`` -- that persisted severity
        # is the durable machine-close ban -- or the adapter fails closed.
        if force_high and instance.severity != "high":
            raise LifecycleAdapterError(
                "candidate flagged rights_or_safety_critical/"
                "machine_close_forbidden but established R2 severity is "
                f"{instance.severity!r}, not 'high'; the R4 lifecycle "
                f"adapter fails closed on the persisted high-severity "
                f"assertion")
        # Exact-identity assertion.
        if instance.risk_identity_id != expected_id:
            raise LifecycleAdapterError(
                f"established risk_identity_id {instance.risk_identity_id!r} "
                f"!= candidate-ref identity {expected_id!r}; the R4 identity "
                f"surface and the R2 establish scope/classifier diverged")
        return instance

    # -- promote one unit result ----------------------------------------

    def promote_unit_result(
        self,
        unit_result: RiskDomainUnitResult,
        *,
        establish: bool = True,
    ) -> PromotionOutcome:
        """Promote one unit result through the R2 lifecycle.

        * positive → register candidates, optionally establish risks for
          each candidate (monitoring priority from the unit grading).
        * boundary → register candidates only (never established by
          machine adjudication; matrix §3.6).
        * negative / not_evaluable / not_applicable → nothing registered.

        ``establish=False`` registers candidates without establishing
        risks, which is useful for N→N+1 reconciliation where the next
        snapshot decides.
        """
        disposition = unit_result.l1_disposition
        if not self._is_promotable_disposition(disposition):
            return PromotionOutcome(
                unit_id=unit_result.unit_id,
                subject_ref=unit_result.subject_ref,
                l1_disposition=disposition,
                skipped_dispositions=(disposition,),
                not_evaluable_reason=unit_result.not_evaluable_reason,
            )

        registered = self.register_candidates(unit_result)
        established: List[Tuple[str, str]] = []

        if disposition == L1Disposition.POSITIVE and establish:
            priority = unit_result.monitoring_priority
            cand_by_id = {
                c.candidate_id: c for c in unit_result.r2_candidates}
            for cand_id in registered:
                candidate = cand_by_id[cand_id]
                instance = self.establish_positive_candidate(
                    candidate, monitoring_priority=priority)
                established.append(
                    (instance.risk_instance_id, instance.risk_identity_id))

        return PromotionOutcome(
            unit_id=unit_result.unit_id,
            subject_ref=unit_result.subject_ref,
            l1_disposition=disposition,
            registered_candidate_ids=registered,
            established_risk_ids=tuple(established),
        )

    # -- close / reopen / supersede / terminate -------------------------

    def _instance_ref(self, instance: RiskInstance) -> RiskInstanceRef:
        return RiskInstanceRef(
            risk_instance_id=instance.risk_instance_id,
            risk_identity_id=instance.risk_identity_id,
            risk_state=instance.current_state,
        )

    def _verify_coverage_snapshot(self, snapshot_id: str) -> None:
        """Assert a snapshot is a live baseline-eligible full snapshot."""
        if not snapshot_id:
            raise LifecycleAdapterError("coverage_snapshot_id is required")
        rec = self.acceptance_service.get(snapshot_id)
        if rec.project_id != self.project_id:
            raise LifecycleAdapterError(
                f"coverage snapshot {snapshot_id!r} project_id mismatch")
        if rec.blocked:
            raise LifecycleAdapterError(
                f"coverage snapshot {snapshot_id!r} is blocked")
        if rec.state != SnapshotAcceptanceState.BASELINE_ELIGIBLE:
            raise LifecycleAdapterError(
                f"coverage snapshot {snapshot_id!r} is not baseline_eligible")

    def machine_close_by_data(
        self,
        instance: RiskInstance,
        *,
        coverage_snapshot_id: str,
        next_unit_results: Optional[Sequence[RiskDomainUnitResult]] = None,
        coverage_ledger: Optional[CoverageLedger] = None,
    ) -> RiskInstance:
        """Machine-close a low/medium risk by data (matrix §3.6).

        This public entry point enforces the same proof as reconciliation:
        a subsequent accepted full snapshot, a closed complete R4 ledger,
        and one exact linked NEGATIVE for this historical risk.  Only an
        explicitly low/medium, non-ambiguous active risk may machine-close.
        R2 then independently verifies the accepted subsequent snapshot and
        the ``rejected_by_evidence`` adjudication.
        """
        if instance.current_state == RiskLifecycleState.IDENTITY_AMBIGUOUS:
            raise LifecycleAdapterError(
                "identity_ambiguous risk cannot be machine-closed")
        allowed_states = (
            RiskLifecycleState.ESTABLISHED,
            RiskLifecycleState.ESCALATED,
            RiskLifecycleState.DEESCALATED,
            RiskLifecycleState.REOPENED,
        )
        if instance.current_state not in allowed_states:
            raise LifecycleAdapterError(
                f"risk state {instance.current_state!r} cannot be "
                f"machine-closed")
        if instance.severity not in ("low", "medium"):
            raise LifecycleAdapterError(
                f"machine close requires explicit low/medium monitoring "
                f"priority, got {instance.severity!r}")
        self._verify_coverage_snapshot(coverage_snapshot_id)
        proof_results = tuple(next_unit_results or ())
        ok, reason = self._verify_close_coverage_proof(
            next_unit_results=proof_results,
            coverage_ledger=coverage_ledger,
            coverage_snapshot_id=coverage_snapshot_id,
            instance=instance,
        )
        if not ok:
            raise LifecycleAdapterError(
                f"machine close coverage proof rejected: {reason}")
        evidence = AdjudicationEvidenceBinding(
            risk_identity_id=instance.risk_identity_id,
            snapshot_id=coverage_snapshot_id,
        )
        adj = self.lifecycle.issue_adjudication(
            project_id=self.project_id,
            outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="close",
            evidence=evidence,
            risk_instances=[instance],
            rationale=(
                "R4 D01 machine close: subsequent accepted full snapshot "
                "rejects the AE/MH under-reporting clue by evidence"),
        )
        return self.lifecycle.transition(
            instance.risk_instance_id,
            RiskTransitionType.CLOSED,
            actor=self.actor,
            reason=CLOSE_REASON_RESOLVED_BY_DATA,
            adjudication=adj,
            acceptance_service=self.acceptance_service,
            coverage_snapshot_id=coverage_snapshot_id,
        )

    def user_close_by_data(
        self,
        instance: RiskInstance,
        *,
        coverage_snapshot_id: str,
        rationale: str = "",
    ) -> RiskInstance:
        """User-confirmed close for high/SAE/AESI/ever-user-confirmed risks.

        R2 requires ``user_confirmed=True`` adjudication for these.  The
        adapter issues a user adjudication (R2 enforces ``user`` matches
        the configured local user) with ``distinct_supported`` outcome,
        which R2 allows for the close action.
        """
        self._verify_coverage_snapshot(coverage_snapshot_id)
        evidence = AdjudicationEvidenceBinding(
            risk_identity_id=instance.risk_identity_id,
            snapshot_id=coverage_snapshot_id,
        )
        adj = self.lifecycle.issue_user_adjudication(
            project_id=self.project_id,
            outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="close",
            evidence=evidence,
            risk_instances=[instance],
            rationale=rationale or "R4 D01 user-confirmed close by data",
        )
        return self.lifecycle.transition(
            instance.risk_instance_id,
            RiskTransitionType.CLOSED,
            actor=self.actor,
            reason=CLOSE_REASON_RESOLVED_BY_DATA,
            adjudication=adj,
            acceptance_service=self.acceptance_service,
            coverage_snapshot_id=coverage_snapshot_id,
        )

    def reopen(
        self,
        instance: RiskInstance,
        *,
        rationale: str = "",
    ) -> RiskInstance:
        """Reopen a closed risk through a legal adjudicated transition.

        R2 only allows ``closed -> reopened`` (matrix §3.6: closed risks
        reopen only through legal adjudication).  Reopening a non-closed
        risk is rejected here and by R2's transition legality table.
        """
        if instance.current_state != RiskLifecycleState.CLOSED:
            raise LifecycleAdapterError(
                f"reopen requires a closed risk, got state="
                f"{instance.current_state!r}")
        evidence = AdjudicationEvidenceBinding(
            risk_identity_id=instance.risk_identity_id,
        )
        adj = self.lifecycle.issue_adjudication(
            project_id=self.project_id,
            outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="reopen",
            evidence=evidence,
            risk_instances=[instance],
            rationale=rationale or "R4 D01 risk recurred; legal reopen",
        )
        return self.lifecycle.transition(
            instance.risk_instance_id,
            RiskTransitionType.REOPENED,
            actor=self.actor,
            reason="risk recurred in a subsequent snapshot",
            adjudication=adj,
        )

    def mark_identity_ambiguous(
        self,
        instance: RiskInstance,
        *,
        rationale: str = "",
    ) -> RiskInstance:
        """Move an established risk to ``identity_ambiguous``.

        R2 does not require adjudication for this transition (matrix §3.6:
        identity ambiguity blocks auto merge/close).  The risk is not
        closed or superseded; it stays in an active-but-blocked state.
        """
        if instance.current_state not in (
                RiskLifecycleState.ESTABLISHED,
                RiskLifecycleState.ESCALATED,
                RiskLifecycleState.DEESCALATED,
                RiskLifecycleState.REOPENED):
            raise LifecycleAdapterError(
                f"identity_ambiguous requires an active risk, got state="
                f"{instance.current_state!r}")
        return self.lifecycle.transition(
            instance.risk_instance_id,
            RiskTransitionType.IDENTITY_AMBIGUOUS,
            actor=self.actor,
            reason=rationale or "identity cannot be matched across snapshots",
        )

    def supersede(
        self,
        instance: RiskInstance,
        *,
        rationale: str = "",
    ) -> RiskInstance:
        """Supersede a risk on a lineage/version change (matrix §3.6).

        Uses a ``supersede`` adjudication.  The original identity is
        preserved in the superseded state; a new Run must produce a new
        candidate/instance with the new lineage.
        """
        evidence = AdjudicationEvidenceBinding(
            risk_identity_id=instance.risk_identity_id,
        )
        adj = self.lifecycle.issue_adjudication(
            project_id=self.project_id,
            outcome=AdjudicationOutcome.VERSION_MISMATCH,
            action="supersede",
            evidence=evidence,
            risk_instances=[instance],
            rationale=rationale or "R4 lineage/rule change supersedes risk",
        )
        return self.lifecycle.transition(
            instance.risk_instance_id,
            RiskTransitionType.SUPERSEDED,
            actor=self.actor,
            reason="rule/mapping/identity algorithm lineage changed",
            adjudication=adj,
        )

    def terminate_not_evaluable(
        self,
        instance: RiskInstance,
        *,
        rationale: str = "",
    ) -> RiskInstance:
        """Terminate a risk whose identity itself cannot continue.

        R2 ``not_evaluable`` is a *terminal* L3 state (matrix §3.6: the
        risk identity itself cannot continue).  No adjudication is
        required by R2 for this transition.  This wrapper is only used
        when the risk identity/lineage itself cannot continue; L1
        not-evaluable alone never reaches here.
        """
        if instance.current_state in RiskLifecycleState.terminal_states():
            raise LifecycleAdapterError(
                f"risk is already terminal (state={instance.current_state!r})")
        return self.lifecycle.transition(
            instance.risk_instance_id,
            RiskTransitionType.NOT_EVALUABLE,
            actor=self.actor,
            reason=rationale or "risk identity cannot continue",
        )

    # -- carry-forward predicate ----------------------------------------

    @staticmethod
    def must_carry_forward(instance: RiskInstance) -> bool:
        """True when a risk must carry forward across an unevaluated or
        evidence-free N+1 snapshot.

        High monitoring priority, SAE/AESI clinical flags, or any prior
        user confirmation all force carry-forward (matrix §3.6).  Uses
        only the public ``RiskInstance`` fields; no private R2 access.
        """
        # The frozen matrix permits machine close only for explicit low or
        # medium priority.  Unknown remains unknown and therefore carries
        # forward rather than being treated as the lowest tier.
        if instance.severity not in ("low", "medium"):
            return True
        if instance.clinical_risk_flags:
            return True
        if instance.ever_user_confirmed:
            return True
        return False
    # -- coverage-proof gate --------------------------------------------

    def _has_linked_negative(
        self,
        next_unit_results: Sequence[RiskDomainUnitResult],
        instance: RiskInstance,
    ) -> bool:
        """True when at least one N+1 ``NEGATIVE`` unit explicitly links
        the exact prior ``risk_instance_id`` and ``risk_identity_id``
        via its ``risk_instance_refs`` (Codex round-3 finding 4).

        A generic same-subject negative result is NOT sufficient: the
        unit must carry the historical risk link to prove this specific
        risk was reviewed and resolved.
        """
        for ur in next_unit_results:
            if ur.l1_disposition != L1Disposition.NEGATIVE:
                continue
            if ur.subject_ref != instance.identity.subject_ref:
                continue
            for ref in ur.risk_instance_refs:
                if (ref.risk_instance_id == instance.risk_instance_id
                        and ref.risk_identity_id == instance.risk_identity_id):
                    return True
        return False

    def _verify_close_coverage_proof(
        self,
        *,
        next_unit_results: Sequence[RiskDomainUnitResult],
        coverage_ledger: Optional[CoverageLedger],
        coverage_snapshot_id: str,
        instance: RiskInstance,
    ) -> Tuple[bool, str]:
        """Verify the closed-ledger + linked-negative coverage proof
        required for an automatic low/medium close.

        Returns ``(ok, reason)``.  ``ok`` is True only when *all* hold:

        * a closed R4 :class:`CoverageLedger` is supplied;
        * its expected unit ids exactly equal the N+1 unit ids;
        * ``is_domain_complete(summary)`` is true;
        * every :class:`UnitEvaluation.provenance_snapshot_id` equals the
          accepted ``coverage_snapshot_id``;
        * at least one N+1 ``NEGATIVE`` unit explicitly links the exact
          prior risk_instance_id and risk_identity_id (Codex round-3
          finding 4).

        Any failure returns ``(False, reason)`` and the risk stays active.
        """
        if coverage_ledger is None:
            return False, "no closed R4 CoverageLedger supplied"
        if not coverage_ledger.is_closed:
            return False, "coverage ledger is not closed"
        expected_ids = set(coverage_ledger.expected_set.unit_ids)
        next_ids_list = [ur.unit_id for ur in next_unit_results]
        next_ids = set(next_ids_list)
        if expected_ids != next_ids:
            return False, (
                "coverage ledger expected-set does not exactly equal the "
                f"N+1 unit ids (ledger={len(expected_ids)}, "
                f"next={len(next_ids)}, "
                f"diff={sorted(expected_ids.symmetric_difference(next_ids))[:3]})")
        summary = coverage_ledger.close_and_summarize()
        complete, reasons = is_domain_complete(summary)
        if not complete:
            return False, (
                "is_domain_complete is false: " + "; ".join(reasons))
        for ue in coverage_ledger.all_evaluations():
            if ue.provenance_snapshot_id != coverage_snapshot_id:
                return False, (
                    f"unit {ue.unit_id!r} provenance_snapshot_id "
                    f"{ue.provenance_snapshot_id!r} != coverage_snapshot_id "
                    f"{coverage_snapshot_id!r}")
        if not self._has_linked_negative(next_unit_results, instance):
            return False, (
                f"no N+1 NEGATIVE unit explicitly links prior risk "
                f"{instance.risk_instance_id!r} / "
                f"{instance.risk_identity_id!r}")
        return True, ""

    # -- N→N+1 reconciliation -------------------------------------------

    @staticmethod
    def _identity_matches(
        unit_result: RiskDomainUnitResult, instance: RiskInstance,
    ) -> bool:
        """Exact identity match: same subject AND at least one candidate
        whose ``risk_identity_id`` exactly equals the instance identity.

        No same-subject fallback: a different concept/event for the same
        participant must NOT keep the old risk alive (Codex finding 3).
        """
        if unit_result.subject_ref != instance.identity.subject_ref:
            return False
        for cand_ref in unit_result.risk_candidate_refs:
            if cand_ref.risk_identity_id == instance.risk_identity_id:
                return True
        return False

    @staticmethod
    def _lineage_changed_for(
        unit_result: RiskDomainUnitResult, instance: RiskInstance,
    ) -> bool:
        """True when N+1 carries a candidate with the same stable core
        as the instance's classifier but a different lineage fingerprint.

        Used to detect a rule/mapping/knowledge/algorithm change for the
        *same stable clinical event* → supersede, not close by data.
        """
        instance_core = instance.identity.classifier
        for cand in unit_result.r2_candidates:
            new_core = candidate_stable_core(cand)
            new_fp = candidate_lineage_fingerprint(cand)
            old_fp = "|".join(instance.identity.scope)
            if (new_core == instance_core
                    and new_fp
                    and old_fp
                    and new_fp != old_fp):
                return True
        return False

    @staticmethod
    def _check_no_duplicate_unit_ids(
        next_unit_results: Sequence[RiskDomainUnitResult],
    ) -> Optional[str]:
        """Return a gap reason if ``next_unit_results`` contains duplicate
        ``unit_id`` values, else None (Codex round-3 finding 6)."""
        seen: Dict[str, int] = {}
        for ur in next_unit_results:
            seen[ur.unit_id] = seen.get(ur.unit_id, 0) + 1
        dups = sorted(uid for uid, count in seen.items() if count > 1)
        if dups:
            return (
                f"duplicate N+1 unit_id values: {dups[:5]}; "
                f"reconciliation cannot proceed safely")
        return None

    def reconcile_n_to_n1(
        self,
        previous_instances: Sequence[RiskInstance],
        next_unit_results: Sequence[RiskDomainUnitResult],
        *,
        coverage_snapshot_id: str = "",
        coverage_ledger: Optional[CoverageLedger] = None,
    ) -> ReconcileResult:
        """Reconcile established risks from snapshot N against the unit
        results of snapshot N+1.

        Rejects duplicate ``unit_id`` values up front (Codex round-3
        finding 6).  For each previous (non-terminal) risk:

        * If N+1 has a positive unit for the same subject whose identity
          **exactly** matches, the risk **persists**.  A different
          concept/event for the same participant does NOT persist the old
          identity -- the old risk stays active until resolved by an
          exact linked negative (Codex round-3 finding 5).
        * If the same stable event re-appears under a changed lineage, the
          risk is **superseded**; competing identities → ambiguous.
        * L1 ``not_evaluable``, ``boundary``, or ``not_applicable`` for
          the subject without an exact positive → **carry forward** with
          a gap reason (Codex round-3 finding 5).  Uncertainty never
          closes.
        * Subject absent → **identity_ambiguous**.
        * High / SAE / AESI / ever-user-confirmed → **carry forward**.
        * Low/medium with no matching positive: **closed by data** only
          when there is a closed, complete, snapshot-matched
          :class:`CoverageLedger` AND at least one N+1 ``NEGATIVE`` unit
          whose ``risk_instance_refs`` explicitly links the exact prior
          risk_instance_id and risk_identity_id (Codex round-3 finding 4).
          Otherwise the risk stays active with a gap reason.
        """
        dup_reason = self._check_no_duplicate_unit_ids(next_unit_results)
        if dup_reason:
            return ReconcileResult(
                persisted=tuple(
                    i for i in previous_instances
                    if i.current_state in RiskLifecycleState.terminal_states()
                ),
                carry_forward=tuple(
                    i for i in previous_instances
                    if i.current_state not in RiskLifecycleState.terminal_states()
                ),
                coverage_gaps=(dup_reason,),
            )

        next_by_subject: Dict[str, List[RiskDomainUnitResult]] = {}
        for ur in next_unit_results:
            next_by_subject.setdefault(ur.subject_ref, []).append(ur)

        persisted: List[RiskInstance] = []
        closed: List[RiskInstance] = []
        carry_forward: List[RiskInstance] = []
        superseded: List[RiskInstance] = []
        ambiguous: List[RiskInstance] = []
        gaps: List[str] = []

        for inst in previous_instances:
            if inst.current_state in RiskLifecycleState.terminal_states():
                persisted.append(inst)
                continue

            subject = inst.identity.subject_ref
            subject_units = next_by_subject.get(subject, [])

            # Exact identity persistence.
            matching = any(
                self._identity_matches(ur, inst) for ur in subject_units)
            if matching:
                persisted.append(inst)
                continue

            # L1 not-evaluable carry-forward; L1 never changes L3.
            has_ne = any(
                ur.l1_disposition == L1Disposition.NOT_EVALUABLE
                for ur in subject_units)
            if has_ne:
                carry_forward.append(inst)
                gaps.append(
                    f"subject {subject!r} has an L1 not_evaluable N+1 unit; "
                    f"risk {inst.risk_instance_id!r} carries forward")
                continue

            # Boundary / not-applicable carry-forward (Codex round-3
            # finding 5): uncertainty never closes.
            has_uncertain = any(
                ur.l1_disposition in (L1Disposition.BOUNDARY,
                                      L1Disposition.NOT_APPLICABLE)
                for ur in subject_units)
            if has_uncertain:
                carry_forward.append(inst)
                gaps.append(
                    f"subject {subject!r} has a BOUNDARY or NOT_APPLICABLE "
                    f"N+1 unit without exact positive; risk "
                    f"{inst.risk_instance_id!r} carries forward "
                    f"(uncertainty never closes)")
                continue

            # Competing identities → ambiguous (checked before supersede).
            if self._has_competing_identities(subject_units, inst):
                amb = self.mark_identity_ambiguous(
                    inst, rationale=(
                        "competing incompatible identities claim the same "
                        "old event; close/merge blocked"))
                ambiguous.append(amb)
                continue

            # Lineage change → supersede.
            if self._lineage_changed_for_subject(subject_units, inst):
                sup = self.supersede(
                    inst, rationale=(
                        "same stable clinical event re-evaluated under a "
                        "changed rule/mapping/knowledge/identity lineage"))
                superseded.append(sup)
                continue

            # Subject absent → identity_ambiguous.
            if not subject_units:
                amb = self.mark_identity_ambiguous(
                    inst, rationale=(
                        "subject absent from N+1 snapshot; identity cannot "
                        "be matched, auto-close blocked"))
                ambiguous.append(amb)
                continue

            # A different-event positive for the same subject keeps the
            # old risk active: the linked-negative gate below will fail,
            # preventing close (Codex round-3 finding 5).  No explicit
            # branch needed -- the risk falls through to the coverage
            # proof check, which requires an exact linked negative.

            # High/SAE/AESI/user-confirmed → carry forward.
            if self.must_carry_forward(inst):
                carry_forward.append(inst)
                gaps.append(
                    f"risk {inst.risk_instance_id!r} carries forward: "
                    f"machine close forbidden for monitoring priority "
                    f"{inst.severity!r}, clinical flags "
                    f"{inst.clinical_risk_flags!r}, or prior user "
                    f"confirmation")
                continue

            # Low/medium: close by data only with coverage proof AND
            # exact linked negative (Codex round-3 finding 4).
            ok, reason = self._verify_close_coverage_proof(
                next_unit_results=next_unit_results,
                coverage_ledger=coverage_ledger,
                coverage_snapshot_id=coverage_snapshot_id,
                instance=inst,
            )
            if not ok:
                carry_forward.append(inst)
                gaps.append(
                    f"risk {inst.risk_instance_id!r} cannot machine-close: "
                    f"{reason}; risk stays active")
                continue
            cl = self.machine_close_by_data(
                inst,
                coverage_snapshot_id=coverage_snapshot_id,
                next_unit_results=next_unit_results,
                coverage_ledger=coverage_ledger,
            )
            closed.append(cl)

        return ReconcileResult(
            persisted=tuple(persisted),
            closed=tuple(closed),
            carry_forward=tuple(carry_forward),
            superseded=tuple(superseded),
            identity_ambiguous=tuple(ambiguous),
            coverage_gaps=tuple(gaps),
        )

    @staticmethod
    def _lineage_changed_for_subject(
        subject_units: Sequence[RiskDomainUnitResult],
        instance: RiskInstance,
    ) -> bool:
        """Check whether any N+1 unit for the subject carries a lineage
        change for the instance's stable event."""
        for ur in subject_units:
            if R4LifecycleAdapter._lineage_changed_for(ur, instance):
                return True
        return False

    @staticmethod
    def _has_competing_identities(
        subject_units: Sequence[RiskDomainUnitResult],
        instance: RiskInstance,
    ) -> bool:
        """True when two or more N+1 candidates for the subject share the
        instance's stable core but carry mutually incompatible new
        identities (different risk_identity_id for the same stable
        event).  Such competition blocks close/merge via
        ``identity_ambiguous`` (Codex finding 6)."""
        cores_to_ids: Dict[str, set] = {}
        instance_core = instance.identity.classifier
        for ur in subject_units:
            for cand in ur.r2_candidates:
                core = candidate_stable_core(cand)
                rid = str(cand.detail.get("risk_identity_id", ""))
                if not core or not rid:
                    continue
                # Only consider candidates that claim the same stable
                # event as the instance.
                if core != instance_core:
                    continue
                cores_to_ids.setdefault(core, set()).add(rid)
        for core, ids in cores_to_ids.items():
            if len(ids) > 1:
                return True
        return False
