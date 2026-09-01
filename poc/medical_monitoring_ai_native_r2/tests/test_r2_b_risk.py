"""Batch B risk lifecycle tests: service-issued adjudication, deterministic
candidate ID, identity match, transition adjudication, merge/split, close
requirements, confirmed_by_user persistence, and negative regressions for all
VETO 1+2 attacks."""

from __future__ import annotations
import pytest
import mm_r2.risk as risk_module

from mm_r2.domain import DomainValidationError
from mm_r2.risk import (
    AdjudicationError, AdjudicationEvidenceBinding, AdjudicationOutcome,
    AdjudicationRecord, CANDIDATE_AUTO_PROMOTE_FORBIDDEN,
    IllegalTransitionError, RiskCandidate, RiskError, RiskInstance,
    RiskLifecycle, RiskLifecycleState, RiskTransitionType,
)
from helpers_b import make_accepted_snapshot
from mm_r2.acceptance import AcceptanceService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _candidate(pid="p1", subject="S01", domain="ae", signal="potential_unreported_ae"):
    return RiskCandidate.from_signal(
        project_id=pid, subject_ref=subject, domain=domain, signal_type=signal,
        severity_hint="medium", confidence_hint=0.8, detail={"term": "Nausea"},
        source_snapshot_id="s1", rule_activation_id="r1", mapping_result_id="mr1",
    )


def _evidence(candidate):
    return AdjudicationEvidenceBinding(
        candidate_id=candidate.candidate_id, source_revision_id="rev-1",
        snapshot_id="s1", rule_activation_id="r1", mapping_result_id="mr1",
    )


def _source_acceptance(candidate, service=None):
    service = service or AcceptanceService(local_user="test")
    try:
        service.get(candidate.source_snapshot_id)
    except Exception:
        make_accepted_snapshot(
            service, pid=candidate.project_id, rid="rev-1",
            sid=candidate.source_snapshot_id,
        )
    return service


def _establish(lc, candidate=None, severity="medium", acceptance_service=None):
    candidate = candidate or _candidate()
    acceptance_service = _source_acceptance(candidate, acceptance_service)
    lc.register_candidate(candidate)
    adj = lc.issue_adjudication(
        project_id=candidate.project_id, outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
        action="establish", evidence=_evidence(candidate), candidate=candidate,
        rationale="supports",
    )
    return lc.establish(
        candidate, adj, severity=severity, actor="system_policy",
        acceptance_service=acceptance_service,
    )


def _add_coverage(lc, instance, sid="cov-1"):
    service = lc._source_acceptance_services[instance.risk_instance_id]
    make_accepted_snapshot(service, rid=f"rev-{sid}", sid=sid)
    return service


def _merge_payload(lc, instances, severity="", classifier=""):
    return lc.merge_action_payload(
        list(instances), severity=severity, classifier=classifier,
    )


# ---------------------------------------------------------------------------
# VETO 1-6: RiskCandidate deterministic ID
# ---------------------------------------------------------------------------

class TestRiskCandidateDeterministicId:
    def test_candidate_id_is_deterministic(self):
        c = _candidate()
        assert c.candidate_id == f"cand-{c.content_hash}"

    def test_supplied_id_must_match(self):
        with pytest.raises(DomainValidationError, match="does not match"):
            RiskCandidate.from_signal(project_id="p1", subject_ref="S01",
                                      domain="ae", signal_type="x", candidate_id="wrong")

    def test_same_content_same_id(self):
        c1 = RiskCandidate.from_signal(project_id="p1", subject_ref="S01", domain="ae", signal_type="x")
        c2 = RiskCandidate.from_signal(project_id="p1", subject_ref="S01", domain="ae", signal_type="x")
        assert c1.candidate_id == c2.candidate_id

    def test_same_id_different_content_rejected(self):
        lc = RiskLifecycle(local_user="test")
        c1 = RiskCandidate.from_signal(project_id="p1", subject_ref="S01", domain="ae", signal_type="x")
        c2 = RiskCandidate.from_signal(project_id="p1", subject_ref="S01", domain="ae", signal_type="y")
        assert c1.candidate_id != c2.candidate_id
        lc.register_candidate(c1)
        lc.register_candidate(c2)
        assert lc.candidate(c1.candidate_id).signal_type == "x"

    def test_auto_promote_forbidden_message(self):
        assert "cannot auto-promote" in CANDIDATE_AUTO_PROMOTE_FORBIDDEN


# ---------------------------------------------------------------------------
# VETO 1-7 + VETO 2-3,11: Adjudication service-issued
# ---------------------------------------------------------------------------

class TestAdjudicationServiceIssued:
    def test_direct_construction_blocked(self):
        c = _candidate()
        with pytest.raises(DomainValidationError, match="cannot be constructed directly"):
            AdjudicationRecord(
                adjudication_id="x", project_id="p1",
                outcome=AdjudicationOutcome.DISTINCT_SUPPORTED, action="establish",
                evidence=_evidence(c), actor="sys", rationale="r",
            )

    def test_machine_issuance_never_user_confirmed(self):
        c = _candidate()
        lc = RiskLifecycle(local_user="test")
        lc.register_candidate(c)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(c), candidate=c, rationale="r",
        )
        assert adj.is_machine_adjudicated
        assert not adj.user_confirmed

    def test_user_adjudication_binds_local_user(self):
        c = _candidate()
        lc = RiskLifecycle(local_user="analyst1")
        lc.register_candidate(c)
        adj = lc.issue_user_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(c), candidate=c, rationale="r",
        )
        assert adj.user_confirmed
        assert adj.actor == "analyst1"

    def test_machine_cannot_masquerade(self):
        c = _candidate()
        lc = RiskLifecycle(local_user="test")
        lc.register_candidate(c)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(c), candidate=c, rationale="r",
        )
        assert not adj.masquerades_as_user_confirmation

    # VETO 2-3: no reachable _verified_instance
    def test_no_reachable_verified_instance(self):
        lc = RiskLifecycle(local_user="test")
        assert not hasattr(lc, "_verified_instance")

    # VETO 2-3: no reachable _verified_adjudication
    def test_no_reachable_verified_adjudication(self):
        lc = RiskLifecycle(local_user="test")
        assert not hasattr(lc, "_verified_adjudication")

    def test_module_does_not_expose_issuers(self):
        assert not hasattr(risk_module, "_issue_instance")
        assert not hasattr(risk_module, "_issue_adjudication")

    def test_hostile_candidate_subclass_rejected(self):
        class HostileCandidate(RiskCandidate):
            pass

        candidate = HostileCandidate.from_signal(
            project_id="p1", subject_ref="S01", domain="ae", signal_type="x"
        )
        with pytest.raises(RiskError, match="RiskCandidate"):
            RiskLifecycle(local_user="test").register_candidate(candidate)

    def test_hostile_evidence_subclass_rejected(self):
        class HostileEvidence(AdjudicationEvidenceBinding):
            pass

        candidate = _candidate()
        lc = RiskLifecycle(local_user="test")
        lc.register_candidate(candidate)
        evidence = HostileEvidence(
            candidate_id=candidate.candidate_id, snapshot_id="s1",
            rule_activation_id="r1", mapping_result_id="mr1",
        )
        with pytest.raises(AdjudicationError, match="exact"):
            lc.issue_adjudication(
                project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
                action="establish", evidence=evidence, candidate=candidate,
            )

    # VETO 2-11: user argument must equal local_user
    def test_user_adjudication_rejects_wrong_user(self):
        c = _candidate()
        lc = RiskLifecycle(local_user="analyst1")
        lc.register_candidate(c)
        with pytest.raises(AdjudicationError, match="does not match"):
            lc.issue_user_adjudication(
                project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
                action="establish", evidence=_evidence(c), candidate=c,
                rationale="r", user="attacker",
            )

    def test_all_outcomes_present(self):
        outcomes = set(AdjudicationOutcome.all_outcomes())
        required = {"merged_supported", "distinct_supported",
                    "rejected_by_evidence", "version_mismatch", "needs_user_attention"}
        assert required <= outcomes

    def test_model_analysis_hashes_validated(self):
        with pytest.raises(DomainValidationError):
            AdjudicationEvidenceBinding(candidate_id="c1", model_analysis_hashes=("bad",))


# ---------------------------------------------------------------------------
# VETO 1-8 + VETO 2-12: Establish requirements
# ---------------------------------------------------------------------------

class TestEstablishRequirements:
    def test_requires_registered_candidate(self):
        c = _candidate()
        lc = RiskLifecycle(local_user="test")
        with pytest.raises(AdjudicationError, match="not registered"):
            lc.issue_adjudication(
                project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
                action="establish", evidence=_evidence(c), candidate=c, rationale="r",
            )

    def test_requires_explicit_severity(self):
        c = _candidate()
        lc = RiskLifecycle(local_user="test")
        lc.register_candidate(c)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(c), candidate=c, rationale="r",
        )
        with pytest.raises(DomainValidationError, match="explicit confirmed severity"):
            lc.establish(c, adj, severity="", actor="system_policy")

    def test_identity_matches_candidate(self):
        c = _candidate(subject="S01", domain="ae")
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, c)
        assert inst.identity.subject_ref == "S01"
        assert inst.domain == "ae"

    def test_same_candidate_cannot_be_established_twice(self):
        candidate = _candidate()
        lc = RiskLifecycle(local_user="test")
        lc.register_candidate(candidate)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(candidate),
            candidate=candidate, rationale="r",
        )
        source_service = _source_acceptance(candidate)
        lc.establish(
            candidate, adj, severity="medium", actor="system_policy",
            acceptance_service=source_service,
        )
        with pytest.raises(RiskError, match="already established"):
            lc.establish(
                candidate, adj, severity="medium", actor="system_policy",
                acceptance_service=source_service,
            )

    @pytest.mark.parametrize(
        "field_name",
        ("snapshot_id", "rule_activation_id", "mapping_result_id", "knowledge_pack_id"),
    )
    def test_candidate_evidence_reference_mismatch_rejected(self, field_name):
        candidate = RiskCandidate.from_signal(
            project_id="p1", subject_ref="S01", domain="ae", signal_type="x",
            source_snapshot_id="s1", rule_activation_id="r1",
            mapping_result_id="mr1", knowledge_pack_id="kp1",
        )
        values = {
            "candidate_id": candidate.candidate_id,
            "snapshot_id": "s1",
            "rule_activation_id": "r1",
            "mapping_result_id": "mr1",
            "knowledge_pack_id": "kp1",
        }
        values[field_name] = "wrong"
        lc = RiskLifecycle(local_user="test")
        lc.register_candidate(candidate)
        with pytest.raises(AdjudicationError, match=field_name):
            lc.issue_adjudication(
                project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
                action="establish", evidence=AdjudicationEvidenceBinding(**values),
                candidate=candidate,
            )

    def test_rejected_outcome_blocks(self):
        c = _candidate()
        lc = RiskLifecycle(local_user="test")
        lc.register_candidate(c)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="establish", evidence=_evidence(c), candidate=c, rationale="r",
        )
        with pytest.raises(RiskError, match="does not support"):
            lc.establish(c, adj, severity="medium", actor="system_policy")

    def test_unregistered_adjudication_blocked(self):
        c = _candidate()
        lc1 = RiskLifecycle(local_user="test")
        lc2 = RiskLifecycle(local_user="test")
        lc1.register_candidate(c)
        adj = lc1.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(c), candidate=c, rationale="r",
        )
        lc2.register_candidate(c)
        with pytest.raises(AdjudicationError, match="not registered in"):
            lc2.establish(c, adj, severity="medium", actor="system_policy")

    # VETO 2-12: foreign-only evidence cannot authorize
    def test_foreign_only_evidence_blocked(self):
        c = RiskCandidate.from_signal(
            project_id="p1", subject_ref="S01", domain="ae", signal_type="x")
        lc = RiskLifecycle(local_user="test")
        lc.register_candidate(c)
        foreign_ev = AdjudicationEvidenceBinding(source_revision_id="foreign-only")
        with pytest.raises(AdjudicationError, match="foreign-only"):
            lc.issue_adjudication(
                project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
                action="establish", evidence=foreign_ev, candidate=c, rationale="r",
            )

    def test_identity_domain_validated(self):
        """RiskInstance validates identity domain matches domain field."""
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, _candidate(domain="ae"))
        assert inst.identity.domain == inst.domain


# ---------------------------------------------------------------------------
# Transition append-only and legality
# ---------------------------------------------------------------------------

class TestRiskTransitionAppendOnly:
    def test_all_required_states_covered(self):
        states = set(RiskLifecycleState.all_states())
        required = {"established", "escalated", "deescalated", "closed",
                    "reopened", "identity_ambiguous", "superseded", "not_evaluable"}
        assert required <= states

    def test_transition_is_append_only(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="escalate",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst], rationale="r",
        )
        inst2 = lc.transition(inst.risk_instance_id, RiskTransitionType.ESCALATED,
                              actor="system_policy", reason="worse", adjudication=adj)
        assert len(inst2.transitions) == len(inst.transitions) + 1
        assert inst2.transitions[0] == inst.transitions[0]


class TestRiskTransitionLegality:
    def _adj_for(self, lc, inst, action="escalate"):
        outcome = (
            AdjudicationOutcome.REJECTED_BY_EVIDENCE
            if action == "close" else AdjudicationOutcome.DISTINCT_SUPPORTED
        )
        return lc.issue_adjudication(
            project_id=inst.project_id,
            outcome=outcome, action=action,
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id,
                source_revision_id="rev-1",
                snapshot_id="cov-1" if action == "close" else "",
            ),
            risk_instances=[inst], rationale="r",
        )

    def test_escalated(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj = self._adj_for(lc, inst)
        inst2 = lc.transition(inst.risk_instance_id, RiskTransitionType.ESCALATED,
                              actor="system_policy", reason="worse", adjudication=adj)
        assert inst2.current_state == RiskLifecycleState.ESCALATED

    def test_rejected_outcome_cannot_authorize_escalation(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="escalate",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[inst], rationale="negative finding",
        )
        with pytest.raises(AdjudicationError, match="does not support"):
            lc.transition(
                inst.risk_instance_id, RiskTransitionType.ESCALATED,
                actor="system_policy", adjudication=adj,
            )

    def test_stale_risk_object_cannot_receive_adjudication(self):
        lc = RiskLifecycle(local_user="test")
        stale = _establish(lc)
        lc.transition(
            stale.risk_instance_id, RiskTransitionType.IDENTITY_AMBIGUOUS,
            actor="system_policy", reason="identity changed",
        )
        with pytest.raises(AdjudicationError, match="current registered"):
            lc.issue_adjudication(
                project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
                action="escalate",
                evidence=AdjudicationEvidenceBinding(
                    risk_identity_id=stale.risk_identity_id,
                    source_revision_id="rev-1",
                ),
                risk_instances=[stale],
            )

    def test_adjudication_cannot_replay_after_state_changes(self):
        lc = RiskLifecycle(local_user="test")
        established = _establish(lc)
        escalate = self._adj_for(lc, established, "escalate")
        escalated = lc.transition(
            established.risk_instance_id, RiskTransitionType.ESCALATED,
            actor="system_policy", adjudication=escalate,
        )
        deescalate = self._adj_for(lc, escalated, "deescalate")
        lc.transition(
            established.risk_instance_id, RiskTransitionType.DEESCALATED,
            actor="system_policy", adjudication=deescalate,
        )
        with pytest.raises(AdjudicationError, match="stale"):
            lc.transition(
                established.risk_instance_id, RiskTransitionType.ESCALATED,
                actor="system_policy", adjudication=escalate,
            )

    def test_deescalated(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj = self._adj_for(lc, inst, "deescalate")
        inst2 = lc.transition(inst.risk_instance_id, RiskTransitionType.DEESCALATED,
                              actor="system_policy", reason="better", adjudication=adj)
        assert inst2.current_state == RiskLifecycleState.DEESCALATED

    def test_identity_ambiguous_no_adj_needed(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        inst2 = lc.transition(inst.risk_instance_id, RiskTransitionType.IDENTITY_AMBIGUOUS,
                              actor="system_policy", reason="ambiguous")
        assert inst2.current_state == RiskLifecycleState.IDENTITY_AMBIGUOUS

    def test_not_evaluable_no_adj_needed(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        inst2 = lc.transition(inst.risk_instance_id, RiskTransitionType.NOT_EVALUABLE,
                              actor="system_policy", reason="coverage lost")
        assert inst2.current_state == RiskLifecycleState.NOT_EVALUABLE

    def test_superseded_is_terminal(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj = self._adj_for(lc, inst, "supersede")
        lc.transition(inst.risk_instance_id, RiskTransitionType.SUPERSEDED,
                      actor="system_policy", reason="rule changed", adjudication=adj)
        with pytest.raises(IllegalTransitionError):
            lc.transition(inst.risk_instance_id, RiskTransitionType.ESCALATED,
                          actor="system_policy", reason="x", adjudication=adj)

    def test_closed_to_escalated_illegal(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="low")
        adj_close = self._adj_for(lc, inst, "close")
        svc_acc = _add_coverage(lc, inst)
        lc.transition(inst.risk_instance_id, RiskTransitionType.CLOSED,
                      actor="system_policy", reason="resolved",
                      adjudication=adj_close, acceptance_service=svc_acc,
                      coverage_snapshot_id="cov-1")
        closed = lc.get(inst.risk_instance_id)
        adj_esc = self._adj_for(lc, closed)
        with pytest.raises(IllegalTransitionError):
            lc.transition(inst.risk_instance_id, RiskTransitionType.ESCALATED,
                          actor="system_policy", reason="x", adjudication=adj_esc)

    def test_closed_reopened(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="low")
        adj_close = self._adj_for(lc, inst, "close")
        svc_acc = _add_coverage(lc, inst)
        lc.transition(inst.risk_instance_id, RiskTransitionType.CLOSED,
                      actor="system_policy", reason="resolved",
                      adjudication=adj_close, acceptance_service=svc_acc,
                      coverage_snapshot_id="cov-1")
        closed = lc.get(inst.risk_instance_id)
        adj_reopen = self._adj_for(lc, closed, "reopen")
        inst3 = lc.transition(inst.risk_instance_id, RiskTransitionType.REOPENED,
                              actor="system_policy", reason="recurred",
                              adjudication=adj_reopen)
        assert inst3.current_state == RiskLifecycleState.REOPENED
        assert inst3.is_active

    def test_identity_ambiguous_can_resolve(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        lc.transition(inst.risk_instance_id, RiskTransitionType.IDENTITY_AMBIGUOUS,
                      actor="system_policy", reason="ambiguous")
        ambiguous = lc.get(inst.risk_instance_id)
        adj = self._adj_for(lc, ambiguous, "establish")
        inst3 = lc.transition(inst.risk_instance_id, RiskTransitionType.ESTABLISHED,
                              actor="system_policy", reason="resolved", adjudication=adj)
        assert inst3.current_state == RiskLifecycleState.ESTABLISHED


# ---------------------------------------------------------------------------
# VETO 1-9 + VETO 2-13: Close requirements
# ---------------------------------------------------------------------------

class TestCloseRequirements:
    def _adj_for(self, lc, inst, action="close", user=False):
        evidence = AdjudicationEvidenceBinding(
            risk_identity_id=inst.risk_identity_id,
            source_revision_id="rev-1",
            snapshot_id="cov-1" if action == "close" else "",
        )
        if user:
            return lc.issue_user_adjudication(
                project_id=inst.project_id,
                outcome=AdjudicationOutcome.DISTINCT_SUPPORTED, action=action,
                evidence=evidence,
                risk_instances=[inst], rationale="r",
            )
        outcome = (
            AdjudicationOutcome.REJECTED_BY_EVIDENCE
            if action == "close" else AdjudicationOutcome.DISTINCT_SUPPORTED
        )
        return lc.issue_adjudication(
            project_id=inst.project_id,
            outcome=outcome, action=action, evidence=evidence,
            risk_instances=[inst], rationale="r",
        )

    def test_close_requires_adjudication(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        with pytest.raises(AdjudicationError, match="requires a bound"):
            lc.transition(inst.risk_instance_id, RiskTransitionType.CLOSED,
                          actor="system_policy", reason="resolved")

    def test_close_requires_real_acceptance_service(self):
        """VETO 2-13: close requires real AcceptanceService, not booleans."""
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj = self._adj_for(lc, inst)
        with pytest.raises(AdjudicationError, match="real AcceptanceService"):
            lc.transition(inst.risk_instance_id, RiskTransitionType.CLOSED,
                          actor="system_policy", reason="resolved", adjudication=adj,
                          coverage_snapshot_id="cov-1")

    def test_close_rejects_hostile_acceptance_subclass(self):
        class HostileAcceptance(AcceptanceService):
            def get(self, snapshot_id):
                raise AssertionError("hostile override must not run")

        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="low")
        adj = self._adj_for(lc, inst)
        with pytest.raises(AdjudicationError, match="real AcceptanceService"):
            lc.transition(
                inst.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=adj,
                acceptance_service=HostileAcceptance(local_user="test"),
                coverage_snapshot_id="cov-1",
            )

    def test_close_requires_coverage_snapshot(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj = self._adj_for(lc, inst)
        svc_acc = lc._source_acceptance_services[inst.risk_instance_id]
        with pytest.raises(AdjudicationError, match="coverage_snapshot_id"):
            lc.transition(inst.risk_instance_id, RiskTransitionType.CLOSED,
                          actor="system_policy", reason="resolved", adjudication=adj,
                          acceptance_service=svc_acc)

    def test_close_low_risk_with_coverage_ok(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="low")
        adj = self._adj_for(lc, inst)
        svc_acc = _add_coverage(lc, inst)
        inst2 = lc.transition(inst.risk_instance_id, RiskTransitionType.CLOSED,
                              actor="system_policy", reason="resolved", adjudication=adj,
                              acceptance_service=svc_acc, coverage_snapshot_id="cov-1")
        assert inst2.current_state == RiskLifecycleState.CLOSED

    def test_source_snapshot_cannot_be_reused_as_close_coverage(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="low")
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="close",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id,
                source_revision_id="rev-1", snapshot_id="s1",
            ),
            risk_instances=[inst], rationale="no longer supported",
        )
        service = lc._source_acceptance_services[inst.risk_instance_id]
        with pytest.raises(AdjudicationError, match="subsequent"):
            lc.transition(
                inst.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=adj,
                acceptance_service=service, coverage_snapshot_id="s1",
            )

    def test_cross_service_coverage_cannot_close(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="low")
        unrelated = AcceptanceService(local_user="test")
        make_accepted_snapshot(unrelated, rid="rev-cov", sid="cov-1")
        adj = self._adj_for(lc, inst)
        with pytest.raises(AdjudicationError, match="same AcceptanceService"):
            lc.transition(
                inst.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=adj,
                acceptance_service=unrelated, coverage_snapshot_id="cov-1",
            )

    def test_aesi_cannot_be_machine_closed(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="aesi")
        adj = self._adj_for(lc, inst)
        service = _add_coverage(lc, inst)
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(
                inst.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=adj,
                acceptance_service=service, coverage_snapshot_id="cov-1",
            )

    def test_aesi_signal_flag_survives_medium_severity(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(
            lc, _candidate(signal="protocol_aesi_signal"), severity="medium"
        )
        assert inst.clinical_risk_flags == ("aesi",)
        adj = self._adj_for(lc, inst)
        service = _add_coverage(lc, inst)
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(
                inst.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=adj,
                acceptance_service=service, coverage_snapshot_id="cov-1",
            )

    @pytest.mark.parametrize(
        ("signal", "expected_flag"),
        [
            ("potentialAESI", "aesi"),
            ("potentialSAE", "sae"),
            ("AeSi", "aesi"),
            ("sAe", "sae"),
            ("Protocol_AeSi_Signal", "aesi"),
            ("PROTOCOL_sAe_SIGNAL", "sae"),
            ("POTENTIALAESI", "aesi"),
            ("potentialaesi", "aesi"),
            ("serious_adverse_event", "sae"),
            ("adverse_event_of_special_interest", "aesi"),
            ("严重不良事件", "sae"),
            ("特别关注不良事件", "aesi"),
            ("特别关注的不良事件", "aesi"),
            ("重点关注的不良事件", "aesi"),
            ("未报告严重不良事件", "sae"),
            ("没有排除严重不良事件", "sae"),
            ("未排除特别关注不良事件", "aesi"),
            ("疑似特别关注的不良事件", "aesi"),
            ("不能确认没有严重不良事件", "sae"),
            ("无法确认没有特别关注不良事件", "aesi"),
            ("尚不能确认没有严重不良事件", "sae"),
            ("没有证据表明没有严重不良事件", "sae"),
            ("疑似没有严重不良事件", "sae"),
            ("可能没有严重不良事件", "sae"),
            ("不能确定没有特别关注的不良事件", "aesi"),
            ("并非没有严重不良事件", "sae"),
            ("不一定没有特别关注不良事件", "aesi"),
            ("不能确认严重不良事件不存在", "sae"),
            ("没有严重不良事件，但疑似特别关注的不良事件", "aesi"),
        ],
    )
    def test_clinical_term_variants_block_machine_close(
        self, signal, expected_flag,
    ):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, _candidate(signal=signal), severity="medium")
        assert expected_flag in inst.clinical_risk_flags
        adj = self._adj_for(lc, inst)
        service = _add_coverage(lc, inst)
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(
                inst.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=adj,
                acceptance_service=service, coverage_snapshot_id="cov-1",
            )

    @pytest.mark.parametrize(
        "signal",
        [
            "disease_management", "unsafe_data", "aesis", "saes",
            "massaeffect", "aesiology", "saeology",
            "non_serious_adverse_event",
            "not_adverse_event_of_special_interest",
            "not_protocol_aesi_signal", "without_protocol_sae_signal",
            "非严重不良事件", "非特别关注不良事件", "未发生严重不良事件",
            "没有严重不良事件", "没有严重的不良事件",
            "没有发生严重不良事件", "未有严重不良事件",
            "没有出现任何严重不良事件", "未发现严重不良事件",
            "目前没有发生严重不良事件", "截至目前尚未发生任何严重不良事件",
            "该受试者无任何严重不良事件",
            "不含严重不良事件", "无任何严重不良事件",
            "严重不良事件不存在",
            "没有特别关注不良事件", "没有特别关注的不良事件",
            "没有发生特别关注不良事件", "未有特别关注不良事件",
            "没有发现任何特别关注不良事件", "未见任何特别关注不良事件",
            "经核查特别关注不良事件不存在",
            "不包含特别关注的不良事件", "无任何特别关注不良事件",
            "特别关注不良事件不存在",
        ],
    )
    def test_unrelated_or_negated_terms_do_not_create_sae_aesi_flags(
        self, signal,
    ):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, _candidate(signal=signal), severity="low")
        assert inst.clinical_risk_flags == ()
        adj = self._adj_for(lc, inst)
        service = _add_coverage(lc, inst)
        closed = lc.transition(
            inst.risk_instance_id, RiskTransitionType.CLOSED,
            actor="system_policy", adjudication=adj,
            acceptance_service=service, coverage_snapshot_id="cov-1",
        )
        assert closed.current_state == RiskLifecycleState.CLOSED

    def test_high_risk_no_auto_close(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="high")
        adj = self._adj_for(lc, inst)
        svc_acc = _add_coverage(lc, inst)
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(inst.risk_instance_id, RiskTransitionType.CLOSED,
                          actor="system_policy", reason="resolved", adjudication=adj,
                          acceptance_service=svc_acc, coverage_snapshot_id="cov-1")

    def test_high_risk_user_confirmed_close_ok(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="high")
        adj = self._adj_for(lc, inst, user=True)
        svc_acc = _add_coverage(lc, inst)
        inst2 = lc.transition(inst.risk_instance_id, RiskTransitionType.CLOSED,
                              actor="system_policy", reason="resolved", adjudication=adj,
                              acceptance_service=svc_acc, coverage_snapshot_id="cov-1")
        assert inst2.current_state == RiskLifecycleState.CLOSED


# ---------------------------------------------------------------------------
# VETO 2-14: confirmed_by_user persistence
# ---------------------------------------------------------------------------

class TestConfirmedByUserPersistence:
    def test_user_escalation_persists_through_close(self):
        """Once any transition is user-confirmed, confirmed_by_user persists."""
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc, severity="low")
        # Escalate with user-confirmed adjudication.
        adj_esc = lc.issue_user_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="escalate",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst], rationale="user escalated",
        )
        inst2 = lc.transition(inst.risk_instance_id, RiskTransitionType.ESCALATED,
                              actor="system_policy", reason="worse", adjudication=adj_esc)
        assert inst2.confirmed_by_user
        assert inst2.ever_user_confirmed
        # Machine close should now require user-confirmed (ever_user_confirmed).
        adj_close = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="close",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id,
                source_revision_id="rev-1", snapshot_id="cov-1"),
            risk_instances=[inst2], rationale="close",
        )
        svc_acc = _add_coverage(lc, inst2)
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(inst.risk_instance_id, RiskTransitionType.CLOSED,
                          actor="system_policy", reason="resolved", adjudication=adj_close,
                          acceptance_service=svc_acc, coverage_snapshot_id="cov-1")


# ---------------------------------------------------------------------------
# VETO 2-15: Merge/split complete target validation
# ---------------------------------------------------------------------------

class TestMergeSplitValidation:
    def _two_instances(
        self, lc, subject="S01", severities=("medium", "medium"),
        scopes=((), ()),
    ):
        results = []
        source_service = AcceptanceService(local_user="test")
        for i, severity in enumerate(severities):
            c = _candidate(subject=subject, signal=f"merge-signal-{i}")
            source_service = _source_acceptance(c, source_service)
            lc.register_candidate(c)
            adj = lc.issue_adjudication(
                project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
                action="establish", evidence=_evidence(c), candidate=c, rationale="r",
            )
            results.append(lc.establish(
                c, adj, severity=severity, actor="system_policy",
                scope=list(scopes[i]),
                acceptance_service=source_service,
            ))
        return results

    def test_merge_cross_subject_rejected(self):
        lc = RiskLifecycle(local_user="test")
        c1 = _candidate(subject="S01")
        c2 = _candidate(subject="S02")
        lc.register_candidate(c1)
        lc.register_candidate(c2)
        adj1 = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(c1), candidate=c1, rationale="r",
        )
        adj2 = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(c2), candidate=c2, rationale="r",
        )
        source_service = _source_acceptance(c1)
        inst1 = lc.establish(
            c1, adj1, severity="medium", actor="system_policy",
            acceptance_service=source_service,
        )
        inst2 = lc.establish(
            c2, adj2, severity="medium", actor="system_policy",
            acceptance_service=source_service,
        )
        adj_m = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.MERGED_SUPPORTED,
            action="merge",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst1.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst1, inst2], rationale="merge",
            action_payload=_merge_payload(lc, [inst1, inst2]),
        )
        with pytest.raises(RiskError, match="cross subjects"):
            lc.merge([inst1.risk_instance_id, inst2.risk_instance_id],
                     adjudication=adj_m, actor="system_policy")

    def test_merge_partial_target_binding_rejected(self):
        """VETO 2-15: merge adjudication binding only first risk cannot
        authorize merging the second."""
        lc = RiskLifecycle(local_user="test")
        inst1, inst2 = self._two_instances(lc)
        # Adjudication binds only inst1, not inst2.
        adj_partial = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.MERGED_SUPPORTED,
            action="merge",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst1.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst1], rationale="partial",
            action_payload=_merge_payload(lc, [inst1]),
        )
        with pytest.raises(AdjudicationError, match="target_risk_identity_ids"):
            lc.merge([inst1.risk_instance_id, inst2.risk_instance_id],
                     adjudication=adj_partial, actor="system_policy")

    def test_merge_duplicate_targets_rejected(self):
        lc = RiskLifecycle(local_user="test")
        inst, _ = self._two_instances(lc)
        with pytest.raises(RiskError, match="duplicate"):
            lc.merge(
                [inst.risk_instance_id, inst.risk_instance_id],
                adjudication=None, actor="system_policy",
            )

    def test_merge_adjudication_requires_result_payload(self):
        lc = RiskLifecycle(local_user="test")
        inst1, inst2 = self._two_instances(lc)
        with pytest.raises(AdjudicationError, match="bound action payload"):
            lc.issue_adjudication(
                project_id="p1",
                outcome=AdjudicationOutcome.MERGED_SUPPORTED,
                action="merge",
                evidence=AdjudicationEvidenceBinding(
                    risk_identity_id=inst1.risk_identity_id,
                    source_revision_id="rev-1",
                ),
                risk_instances=[inst1, inst2], rationale="merge",
            )

    def test_merge_result_payload_mismatch_is_atomic(self):
        lc = RiskLifecycle(local_user="test")
        inst1, inst2 = self._two_instances(lc)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.MERGED_SUPPORTED,
            action="merge",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst1.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[inst1, inst2], rationale="merge",
            action_payload=_merge_payload(
                lc, [inst1, inst2], classifier="approved-classifier",
            ),
        )
        before_instances = tuple(lc.instances_for_project("p1"))
        before_head = dict(lc._chain_head)
        with pytest.raises(AdjudicationError, match="exact severity"):
            lc.merge(
                [inst1.risk_instance_id, inst2.risk_instance_id],
                adjudication=adj, classifier="different-classifier",
                actor="system_policy",
            )
        assert tuple(lc.instances_for_project("p1")) == before_instances
        assert lc._chain_head == before_head

    def test_merge_high_lineage_cannot_be_downgraded(self):
        lc = RiskLifecycle(local_user="test")
        high, medium = self._two_instances(
            lc, severities=("high", "medium"),
        )
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.MERGED_SUPPORTED,
            action="merge",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=high.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[high, medium], rationale="merge low",
            action_payload={"severity": "low", "classifier": ""},
        )
        before_instances = tuple(lc.instances_for_project("p1"))
        before_head = dict(lc._chain_head)
        with pytest.raises(AdjudicationError, match="cannot downgrade"):
            lc.merge(
                [high.risk_instance_id, medium.risk_instance_id],
                adjudication=adj, severity="low", actor="system_policy",
            )
        assert tuple(lc.instances_for_project("p1")) == before_instances
        assert lc._chain_head == before_head

    def test_merge_inherits_highest_severity_and_blocks_machine_close(self):
        lc = RiskLifecycle(local_user="test")
        high, medium = self._two_instances(
            lc, severities=("high", "medium"),
        )
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.MERGED_SUPPORTED,
            action="merge",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=high.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[high, medium], rationale="merge",
            action_payload=_merge_payload(lc, [high, medium]),
        )
        merged = lc.merge(
            [high.risk_instance_id, medium.risk_instance_id],
            adjudication=adj, actor="system_policy",
        )
        assert merged.severity == "high"
        service = _add_coverage(lc, merged)
        close_adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="close",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=merged.risk_identity_id,
                source_revision_id="rev-cov-1", snapshot_id="cov-1",
            ),
            risk_instances=[merged], rationale="close",
        )
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(
                merged.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=close_adj,
                acceptance_service=service, coverage_snapshot_id="cov-1",
            )

    def test_merge_scope_and_identity_are_input_order_independent(self):
        def build(reverse=False):
            lc = RiskLifecycle(local_user="test")
            left, right = self._two_instances(
                lc, severities=("high", "medium"),
                scopes=(("left",), ("right",)),
            )
            ordered = [right, left] if reverse else [left, right]
            adj = lc.issue_adjudication(
                project_id="p1",
                outcome=AdjudicationOutcome.MERGED_SUPPORTED,
                action="merge",
                evidence=AdjudicationEvidenceBinding(
                    risk_identity_id=ordered[0].risk_identity_id,
                    source_revision_id="rev-1",
                ),
                risk_instances=ordered, rationale="merge",
                action_payload=_merge_payload(lc, ordered),
            )
            return lc.merge(
                [item.risk_instance_id for item in ordered],
                adjudication=adj, actor="system_policy",
            )

        forward = build()
        reverse = build(reverse=True)
        assert forward.identity.scope == ("left", "right")
        assert reverse.identity.scope == ("left", "right")
        assert forward.risk_identity_id == reverse.risk_identity_id

    def test_merge_preserves_old_identities(self):
        lc = RiskLifecycle(local_user="test")
        inst1, inst2 = self._two_instances(lc)
        adj_m = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.MERGED_SUPPORTED,
            action="merge",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst1.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst1, inst2], rationale="merge",
            action_payload=_merge_payload(lc, [inst1, inst2]),
        )
        merged = lc.merge([inst1.risk_instance_id, inst2.risk_instance_id],
                          adjudication=adj_m, actor="system_policy")
        assert inst1.identity.risk_identity_id in merged.identity.derived_from
        assert inst2.identity.risk_identity_id in merged.identity.derived_from
        assert lc.get(inst1.risk_instance_id).current_state == RiskLifecycleState.SUPERSEDED
        assert lc.verify_chain("p1")

    def test_merge_factory_failure_is_atomic(self):
        from mm_r2.identity import make_risk_identity

        def factory(**kwargs):
            if kwargs.get("derived_from"):
                raise RuntimeError("injected merge identity failure")
            return make_risk_identity(**kwargs)

        lc = RiskLifecycle(local_user="test", identity_factory=factory)
        inst1, inst2 = self._two_instances(lc)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.MERGED_SUPPORTED,
            action="merge",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst1.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[inst1, inst2], rationale="merge",
            action_payload=_merge_payload(lc, [inst1, inst2]),
        )
        before_instances = tuple(lc.instances_for_project("p1"))
        before_head = dict(lc._chain_head)
        with pytest.raises(RuntimeError, match="injected"):
            lc.merge(
                [inst1.risk_instance_id, inst2.risk_instance_id],
                adjudication=adj, actor="system_policy",
            )
        assert tuple(lc.instances_for_project("p1")) == before_instances
        assert lc._chain_head == before_head

    def test_merge_inherits_user_confirmation(self):
        lc = RiskLifecycle(local_user="test")
        first, second = self._two_instances(lc)
        user_escalation = lc.issue_user_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="escalate",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=first.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[first], rationale="user escalation",
        )
        first = lc.transition(
            first.risk_instance_id, RiskTransitionType.ESCALATED,
            actor="system_policy", adjudication=user_escalation,
        )
        merge_adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.MERGED_SUPPORTED,
            action="merge",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=first.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[first, second], rationale="merge",
            action_payload=_merge_payload(lc, [first, second]),
        )
        merged = lc.merge(
            [first.risk_instance_id, second.risk_instance_id],
            adjudication=merge_adj, actor="system_policy",
        )
        assert merged.ever_user_confirmed
        service = _add_coverage(lc, merged)
        close_adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="close",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=merged.risk_identity_id,
                source_revision_id="rev-cov-1", snapshot_id="cov-1",
            ),
            risk_instances=[merged], rationale="close",
        )
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(
                merged.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=close_adj,
                acceptance_service=service, coverage_snapshot_id="cov-1",
            )

    def test_merge_wrong_outcome_rejected(self):
        lc = RiskLifecycle(local_user="test")
        inst1, inst2 = self._two_instances(lc)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="merge",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst1.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst1, inst2], rationale="r",
            action_payload=_merge_payload(lc, [inst1, inst2]),
        )
        with pytest.raises(AdjudicationError, match="merged_supported"):
            lc.merge([inst1.risk_instance_id, inst2.risk_instance_id],
                     adjudication=adj, actor="system_policy")

    def test_split_cross_subject_rejected(self):
        """VETO 2-15: split cannot put one subject's risk into S02/S03."""
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj_s = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst], rationale="split",
            action_payload=[{"subject_ref": "S02"}, {"subject_ref": "S03"}],
        )
        with pytest.raises(AdjudicationError, match="cross subjects"):
            lc.split(inst.risk_instance_id,
                     [{"subject_ref": "S02"}, {"subject_ref": "S03"}],
                     adjudication=adj_s, actor="system_policy")

    def test_split_cross_domain_rejected(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj_s = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst], rationale="split",
            action_payload=[{"domain": "cm"}, {"domain": "lab"}],
        )
        with pytest.raises(AdjudicationError, match="cross domains"):
            lc.split(inst.risk_instance_id,
                     [{"domain": "cm"}, {"domain": "lab"}],
                     adjudication=adj_s, actor="system_policy")

    def test_split_preserves_original(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj_s = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst], rationale="split",
            action_payload=[
                {"domain": "ae", "scope": ["liver"]},
                {"domain": "ae", "scope": ["gi"]},
            ],
        )
        children = lc.split(inst.risk_instance_id,
                            [{"domain": "ae", "scope": ["liver"]},
                             {"domain": "ae", "scope": ["gi"]}],
                            adjudication=adj_s, actor="system_policy")
        assert len(children) == 2
        assert lc.get(inst.risk_instance_id).current_state == RiskLifecycleState.SUPERSEDED
        assert lc.verify_chain("p1")

    def test_split_payload_mismatch_is_atomic(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        approved = [
            {"domain": "ae", "scope": ["liver"]},
            {"domain": "ae", "scope": ["gi"]},
        ]
        attempted = [
            {"domain": "ae", "scope": ["liver"]},
            {"domain": "ae", "scope": ["renal"]},
        ]
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[inst], action_payload=approved, rationale="split",
        )
        before_instances = tuple(lc.instances_for_project("p1"))
        before_head = dict(lc._chain_head)
        with pytest.raises(AdjudicationError, match="exact child specs"):
            lc.split(
                inst.risk_instance_id, attempted,
                adjudication=adj, actor="system_policy",
            )
        assert tuple(lc.instances_for_project("p1")) == before_instances
        assert lc._chain_head == before_head

    def test_split_high_lineage_cannot_be_downgraded(self):
        lc = RiskLifecycle(local_user="test")
        parent = _establish(lc, severity="high")
        specs = [
            {"scope": ["liver"], "severity": "low"},
            {"scope": ["renal"], "severity": "low"},
        ]
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=parent.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[parent], action_payload=specs, rationale="split",
        )
        before_instances = tuple(lc.instances_for_project("p1"))
        before_head = dict(lc._chain_head)
        with pytest.raises(AdjudicationError, match="cannot downgrade"):
            lc.split(
                parent.risk_instance_id, specs,
                adjudication=adj, actor="system_policy",
            )
        assert tuple(lc.instances_for_project("p1")) == before_instances
        assert lc._chain_head == before_head

    def test_split_children_keep_high_severity_and_block_machine_close(self):
        lc = RiskLifecycle(local_user="test")
        parent = _establish(lc, severity="high")
        specs = [{"scope": ["liver"]}, {"scope": ["renal"]}]
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=parent.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[parent], action_payload=specs, rationale="split",
        )
        children = lc.split(
            parent.risk_instance_id, specs,
            adjudication=adj, actor="system_policy",
        )
        assert all(child.severity == "high" for child in children)
        service = _add_coverage(lc, children[0])
        close_adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="close",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=children[0].risk_identity_id,
                source_revision_id="rev-cov-1", snapshot_id="cov-1",
            ),
            risk_instances=[children[0]], rationale="close",
        )
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(
                children[0].risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=close_adj,
                acceptance_service=service, coverage_snapshot_id="cov-1",
            )

    def test_split_mixed_case_aesi_classifier_blocks_machine_close(self):
        lc = RiskLifecycle(local_user="test")
        parent = _establish(lc, severity="medium")
        specs = [
            {"scope": ["special"], "classifier": "AeSi"},
            {"scope": ["other"], "classifier": "ordinary"},
        ]
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=parent.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[parent], action_payload=specs, rationale="split",
        )
        children = lc.split(
            parent.risk_instance_id, specs,
            adjudication=adj, actor="system_policy",
        )
        aesi_child = children[0]
        assert aesi_child.clinical_risk_flags == ("aesi",)
        service = _add_coverage(lc, aesi_child)
        close_adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="close",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=aesi_child.risk_identity_id,
                source_revision_id="rev-cov-1", snapshot_id="cov-1",
            ),
            risk_instances=[aesi_child], rationale="close",
        )
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(
                aesi_child.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=close_adj,
                acceptance_service=service, coverage_snapshot_id="cov-1",
            )

    def test_split_duplicate_child_identities_rejected(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        specs = [
            {"domain": "ae", "scope": ["same"], "classifier": "same"},
            {"domain": "ae", "scope": ["same"], "classifier": "same"},
        ]
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[inst], action_payload=specs, rationale="split",
        )
        with pytest.raises(AdjudicationError, match="duplicate risk identities"):
            lc.split(
                inst.risk_instance_id, specs,
                adjudication=adj, actor="system_policy",
            )

    def test_split_factory_failure_is_atomic(self):
        from mm_r2.identity import make_risk_identity

        def factory(**kwargs):
            if kwargs.get("classifier") == "boom":
                raise RuntimeError("injected split identity failure")
            return make_risk_identity(**kwargs)

        lc = RiskLifecycle(local_user="test", identity_factory=factory)
        inst = _establish(lc)
        specs = [
            {"domain": "ae", "scope": ["a"], "classifier": "ok"},
            {"domain": "ae", "scope": ["b"], "classifier": "boom"},
        ]
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[inst], action_payload=specs, rationale="split",
        )
        before_instances = tuple(lc.instances_for_project("p1"))
        before_head = dict(lc._chain_head)
        with pytest.raises(RuntimeError, match="injected"):
            lc.split(
                inst.risk_instance_id, specs,
                adjudication=adj, actor="system_policy",
            )
        assert tuple(lc.instances_for_project("p1")) == before_instances
        assert lc._chain_head == before_head

    def test_split_children_inherit_user_confirmation(self):
        lc = RiskLifecycle(local_user="test")
        parent = _establish(lc)
        user_escalation = lc.issue_user_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="escalate",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=parent.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[parent], rationale="user escalation",
        )
        parent = lc.transition(
            parent.risk_instance_id, RiskTransitionType.ESCALATED,
            actor="system_policy", adjudication=user_escalation,
        )
        specs = [
            {"domain": "ae", "scope": ["liver"]},
            {"domain": "ae", "scope": ["gi"]},
        ]
        split_adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="split",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=parent.risk_identity_id,
                source_revision_id="rev-1",
            ),
            risk_instances=[parent], rationale="split", action_payload=specs,
        )
        children = lc.split(
            parent.risk_instance_id, specs,
            adjudication=split_adj, actor="system_policy",
        )
        assert all(child.ever_user_confirmed for child in children)
        service = _add_coverage(lc, children[0])
        close_adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.REJECTED_BY_EVIDENCE,
            action="close",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=children[0].risk_identity_id,
                source_revision_id="rev-cov-1", snapshot_id="cov-1",
            ),
            risk_instances=[children[0]], rationale="close",
        )
        with pytest.raises(AdjudicationError, match="auto-close"):
            lc.transition(
                children[0].risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", adjudication=close_adj,
                acceptance_service=service, coverage_snapshot_id="cov-1",
            )


# ---------------------------------------------------------------------------
# Determinism and identity
# ---------------------------------------------------------------------------

class TestRiskDeterminism:
    def test_candidate_deterministic_hash(self):
        c1 = RiskCandidate.from_signal(
            project_id="p1", subject_ref="S01", domain="ae", signal_type="x",
            severity_hint="m", confidence_hint=0.5, detail={"k": "v"})
        c2 = RiskCandidate.from_signal(
            project_id="p1", subject_ref="S01", domain="ae", signal_type="x",
            severity_hint="m", confidence_hint=0.5, detail={"k": "v"})
        assert c1.content_hash == c2.content_hash

    def test_identity_is_stable(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        assert inst.identity.project_id == "p1"
        assert inst.identity.risk_identity_id.startswith("risk-id-")

    def test_identity_project_scoped(self):
        lc = RiskLifecycle(local_user="test")
        c1 = _candidate(pid="p1")
        c2 = _candidate(pid="p2")
        lc.register_candidate(c1)
        lc.register_candidate(c2)
        adj1 = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(c1), candidate=c1, rationale="r")
        adj2 = lc.issue_adjudication(
            project_id="p2", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="establish", evidence=_evidence(c2), candidate=c2, rationale="r")
        inst1 = lc.establish(
            c1, adj1, severity="medium", actor="system_policy",
            acceptance_service=_source_acceptance(c1),
        )
        inst2 = lc.establish(
            c2, adj2, severity="medium", actor="system_policy",
            acceptance_service=_source_acceptance(c2),
        )
        assert inst1.identity.risk_identity_id != inst2.identity.risk_identity_id

    def test_identity_not_overwritten_on_transition(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        original_identity = inst.identity
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="escalate",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst], rationale="r")
        inst2 = lc.transition(inst.risk_instance_id, RiskTransitionType.ESCALATED,
                              actor="system_policy", reason="worse", adjudication=adj)
        assert inst2.identity == original_identity

    def test_chain_verifies(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        adj = lc.issue_adjudication(
            project_id="p1", outcome=AdjudicationOutcome.DISTINCT_SUPPORTED,
            action="escalate",
            evidence=AdjudicationEvidenceBinding(
                risk_identity_id=inst.risk_identity_id, source_revision_id="rev-1"),
            risk_instances=[inst], rationale="r")
        lc.transition(inst.risk_instance_id, RiskTransitionType.ESCALATED,
                      actor="system_policy", reason="worse", adjudication=adj)
        assert lc.verify_chain("p1")

    def test_direct_instance_construction_blocked(self):
        from mm_r2.identity import make_risk_identity
        ident = make_risk_identity(project_id="p1", subject_ref="S01", domain="ae")
        with pytest.raises(DomainValidationError, match="verified construction"):
            RiskInstance(
                risk_instance_id="x", project_id="p1", identity=ident,
                domain="ae", source_snapshot_ids=("s1",),
                established_adjudication_id="a")

    def test_transition_hash_valid(self):
        lc = RiskLifecycle(local_user="test")
        inst = _establish(lc)
        for t in inst.transitions:
            assert t.transition_hash == t.compute_hash()
            assert len(t.transition_hash) == 64
