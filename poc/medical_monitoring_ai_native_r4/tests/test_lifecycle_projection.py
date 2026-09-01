"""R4 D01 AE/MH lifecycle projection tests (worker_03, round 2).

These tests exercise the R4 :class:`R4LifecycleAdapter` against the frozen
R2 :class:`RiskLifecycle` and a real :class:`AcceptanceService`.  They prove
the N→N+1 reconciliation rules from the frozen matrix §3.6 and context §11
with the round-2 public-contract and identity corrections:

* only verified positive unit outputs establish risks (never auto-promote);
* monitoring priority projects to R2 ``severity``; clinical flags stay
  separate (derived by R2 from the candidate signal);
* the established risk identity exactly equals the candidate-ref identity
  (public :func:`make_risk_identity`, no parallel hash, no same-subject
  fallback);
* low/medium machine close requires a subsequent accepted full snapshot
  *plus* a closed R4 coverage ledger proving complete N+1 coverage, with
  ``rejected_by_evidence`` and ``close_reason=resolved_by_data``;
* high / SAE / AESI / user-confirmed risks carry forward (no machine close);
* L1 ``not_evaluable`` carries an active risk forward and surfaces the gap
  (L1 never changes L3 by itself);
* lineage/version change for the same stable event → ``superseded``, never
  ``resolved_by_data``; competing identities → ``identity_ambiguous``;
* closed risks reopen only through a legal adjudicated transition;
* terminal L3 ``not_evaluable`` cannot reopen;
* a previously user-confirmed risk remains ``ever_user_confirmed`` after a
  legal reopen and cannot be machine-closed during reconciliation;
* Query drafts project as basis+finding+action and never carry a 'sent'
  flag (Query export != send).

All data is synthetic and offline.  No real project, provider, or port.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r2.risk import (  # noqa: E402
    AdjudicationError,
    AdjudicationOutcome,
    IllegalTransitionError,
    RiskCandidate,
    RiskLifecycleState,
    RiskTransitionType,
)
from mm_r4.contracts import (  # noqa: E402
    CoverageValidationError,
    L1Disposition,
)
from mm_r4.lifecycle import (  # noqa: E402
    CLOSE_REASON_RESOLVED_BY_DATA,
    LifecycleAdapterError,
    R4LifecycleAdapter,
    map_priority_to_r2_severity,
)
from mm_r4.aemh import (  # noqa: E402
    MONITORING_PRIORITY_HIGH,
    MONITORING_PRIORITY_LOW,
    MONITORING_PRIORITY_MEDIUM,
)
from mm_r4.fixtures import (  # noqa: E402
    PROJECT_ID,
    RULE_LINEAGE,
    attach_risk_ref,
    evaluate,
    make_acceptance_service,
    make_baseline_snapshot,
    make_closed_ledger,
    make_lifecycle,
    make_record,
    make_record_set,
    make_subsequent_snapshot,
    make_unit,
)

_ALT = "MedDRA:10035581"


# ---------------------------------------------------------------------------
# Helpers shared by lifecycle tests
# ---------------------------------------------------------------------------

def _adapter():
    svc = make_acceptance_service()
    make_baseline_snapshot(svc, snapshot_id="snap-N", revision_id="rev-N")
    lc = make_lifecycle()
    return R4LifecycleAdapter(
        lifecycle=lc, acceptance_service=svc,
        project_id=PROJECT_ID, actor="system_policy"), svc, lc


def _positive_unit_result(priority_rec_id="sym-1", intensity="moderate"):
    """A verified positive unit result carrying one under-reporting clue."""
    records = [
        make_record("reported_ae", "MedDRA:10019242", "ae-1",
                    event_date_raw="2026-03-01"),
        make_record("symptom_event", _ALT, priority_rec_id,
                    event_date_raw="2026-03-15", intensity=intensity),
    ]
    return evaluate(records, snapshot_id="snap-N")


def _negative_unit_result(subject_ref="S001"):
    """A negative unit result for the same subject (all evidence matched)."""
    records = [
        make_record("reported_ae", "MedDRA:10019242", "ae-neg-1",
                    event_date_raw="2026-03-15", subject_ref=subject_ref),
        make_record("symptom_event", "MedDRA:10019242", "sym-neg-1",
                    event_date_raw="2026-03-15", intensity="mild",
                    subject_ref=subject_ref),
    ]
    return evaluate(records, snapshot_id="snap-N1")


def _machine_close_proof(instance, snapshot_id="snap-N1"):
    """Build the complete synthetic close proof for one historical risk."""
    negative = attach_risk_ref(
        _negative_unit_result(subject_ref=instance.identity.subject_ref),
        risk_instance_id=instance.risk_instance_id,
        risk_identity_id=instance.risk_identity_id,
    )
    ledger = make_closed_ledger(
        [negative], snapshot_id=snapshot_id, rule_lineage=RULE_LINEAGE)
    return (negative,), ledger


def _flagged_candidate(unit_result, **flag_overrides):
    """Clone the first candidate of a real positive unit result and add
    frozen D04 criticality flags (``rights_or_safety_critical`` /
    ``machine_close_forbidden``) to its detail.  All identity-bearing
    fields are preserved so the clone still passes the adapter's exact
    identity verification."""
    original = unit_result.r2_candidates[0]
    detail = dict(original.detail)
    detail.update(flag_overrides)
    return RiskCandidate.from_signal(
        project_id=original.project_id,
        subject_ref=original.subject_ref,
        domain=original.domain,
        signal_type=original.signal_type,
        source_snapshot_id=original.source_snapshot_id,
        rule_activation_id=original.rule_activation_id,
        mapping_result_id=original.mapping_result_id,
        knowledge_pack_id=original.knowledge_pack_id,
        severity_hint=original.severity_hint,
        confidence_hint=original.confidence_hint,
        detail=detail,
    )


# ===========================================================================
# 0. Private-import rejection (Codex finding 1)
# ===========================================================================

class TestNoPrivateR2Imports:

    def _r4_runtime_sources(self):
        pkg = Path(__file__).resolve().parents[1] / "src" / "mm_r4"
        return [
            pkg / "lifecycle.py",
            pkg / "aemh.py",
            pkg / "fixtures.py",
            pkg / "contracts.py",
            pkg / "coverage.py",
            pkg / "projection.py",
        ]

    def test_no_underscore_r2_import_in_runtime_modules(self):
        """No R4 runtime module imports a private (underscore) R2 symbol."""
        forbidden_substrings = (
            "from mm_r2.risk import _",
            "from mm_r2.risk._",
            "from mm_r2.identity import _",
            "from mm_r2.acceptance import _",
            "import mm_r2.risk._",
            "mm_r2.risk._severity_rank",
            "mm_r2.risk._LEGAL_TRANSITIONS",
            "mm_r2.risk._ACTION",
            # Round-3 finding 2: no runtime sys.path mutation or
            # tests-helper imports.
            "sys.path",
            "import sys",
            "helpers_b",
        )
        offenders = []
        for src in self._r4_runtime_sources():
            if not src.exists():
                continue
            text = src.read_text(encoding="utf-8")
            # Parse the AST and inspect Import/ImportFrom nodes for private
            # mm_r2 names.
            tree = ast.parse(text, filename=str(src))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("mm_r2"):
                        for alias in node.names:
                            if alias.name.startswith("_"):
                                offenders.append(
                                    f"{src.name}: private import "
                                    f"{alias.name} from {node.module}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("mm_r2.") and (
                                "_" in alias.name.split(".")[-1]):
                            offenders.append(
                                f"{src.name}: private module import "
                                f"{alias.name}")
            # AST-based check for sys.path access, import sys, and
            # helpers_b imports (round-3 finding 2).  Docstrings that
            # say "does NOT mutate sys.path" are not code and must not
            # trip the check.
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    if (isinstance(node.value, ast.Name)
                            and node.value.id == "sys"
                            and node.attr == "path"):
                        offenders.append(
                            f"{src.name}: sys.path access in runtime code")
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "sys":
                            offenders.append(
                                f"{src.name}: 'import sys' in runtime code")
                if isinstance(node, ast.ImportFrom):
                    if node.module and "helpers_b" in node.module:
                        offenders.append(
                            f"{src.name}: helpers_b import in runtime code")
            for sub in forbidden_substrings:
                if sub in text and "sys.path" not in sub and "import sys" not in sub:
                    offenders.append(f"{src.name}: forbidden '{sub}'")
        assert offenders == [], (
            "private R2 imports/access found: " + "; ".join(offenders))

    def test_must_carry_forward_uses_no_private_rank(self):
        """``must_carry_forward`` source has no ``_severity_rank`` reference."""
        src = (Path(__file__).resolve().parents[1] / "src" / "mm_r4"
               / "lifecycle.py")
        text = src.read_text(encoding="utf-8")
        assert "_severity_rank" not in text


# ===========================================================================
# 1. Severity projection (matrix §3.5)
# ===========================================================================

class TestSeverityProjection:

    @pytest.mark.parametrize(
        ("priority", "severity"),
        [
            (MONITORING_PRIORITY_HIGH, "high"),
            (MONITORING_PRIORITY_MEDIUM, "medium"),
            (MONITORING_PRIORITY_LOW, "low"),
            ("unknown", "unknown"),
        ],
    )
    def test_priority_maps_to_r2_severity(self, priority, severity):
        assert map_priority_to_r2_severity(priority) == severity

    def test_unknown_never_defaults_to_low(self):
        assert map_priority_to_r2_severity("unknown") == "unknown"

    def test_positive_unit_projects_priority_to_severity(self):
        adapter, _, lc = _adapter()
        ur = _positive_unit_result(intensity="severe")
        assert ur.l1_disposition == L1Disposition.POSITIVE
        outcome = adapter.promote_unit_result(ur)
        assert outcome.established_any
        inst = lc.get(outcome.established_risk_ids[0][0])
        # severe intensity -> medium monitoring priority -> medium severity
        assert inst.severity == "medium"

    def test_high_seriousness_projects_high_severity(self):
        adapter, _, lc = _adapter()
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-h-1",
                        event_date_raw="2026-03-01"),
            make_record("healthcare_encounter", _ALT, "hosp-h-1",
                        event_date_raw="2026-03-15",
                        seriousness_criteria=("sae",)),
        ]
        ur = evaluate(records, snapshot_id="snap-N")
        assert ur.medical_grading.monitoring_priority == MONITORING_PRIORITY_HIGH
        outcome = adapter.promote_unit_result(ur)
        inst = lc.get(outcome.established_risk_ids[0][0])
        assert inst.severity == "high"
        assert inst.clinical_risk_flags == ("sae",)

    @pytest.mark.parametrize(
        ("criteria", "expected_flags"),
        [
            (("sae",), ("sae",)),
            (("aesi",), ("aesi",)),
            (("sae", "aesi"), ("aesi", "sae")),
            (("hospitalization",), ("sae",)),
        ],
    )
    def test_seriousness_projects_independent_r2_flags(
        self, criteria, expected_flags,
    ):
        adapter, _, lc = _adapter()
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-flags",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", _ALT, "sym-flags",
                        event_date_raw="2026-03-15",
                        seriousness_criteria=criteria),
        ]
        outcome = adapter.promote_unit_result(
            evaluate(records, snapshot_id="snap-N"))
        inst = lc.get(outcome.established_risk_ids[0][0])
        assert inst.severity == "high"
        assert inst.clinical_risk_flags == expected_flags


# ===========================================================================
# 2. Exact identity (Codex findings 2, 3)
# ===========================================================================

class TestExactIdentity:

    def test_candidate_ref_identity_equals_established_identity(self):
        """Every candidate-ref identity equals the eventual R2 identity."""
        adapter, _, lc = _adapter()
        ur = _positive_unit_result(intensity="moderate")
        outcome = adapter.promote_unit_result(ur)
        inst = lc.get(outcome.established_risk_ids[0][0])
        cand_ref = ur.risk_candidate_refs[0]
        assert cand_ref.risk_identity_id == inst.risk_identity_id

    def test_same_source_event_persists_across_snapshots(self):
        """Same concept + same source event identity → same risk identity."""
        adapter, _, lc = _adapter()
        ur = _positive_unit_result(priority_rec_id="sym-stable")
        outcome = adapter.promote_unit_result(ur)
        inst = lc.get(outcome.established_risk_ids[0][0])
        old_identity = inst.risk_identity_id
        # N+1: the exact same evidence record (same record_id) → same identity.
        next_ur = _positive_unit_result(priority_rec_id="sym-stable")
        assert (next_ur.risk_candidate_refs[0].risk_identity_id
                == old_identity)

    def test_different_concept_same_subject_does_not_persist(self):
        """A different concept/event for the same participant must NOT
        keep the old risk identity alive (no same-subject fallback)."""
        adapter, _, _ = _adapter()
        ur = _positive_unit_result(priority_rec_id="sym-A")
        outcome = adapter.promote_unit_result(ur)
        inst = adapter.lifecycle.get(outcome.established_risk_ids[0][0])
        old_identity = inst.risk_identity_id
        # N+1: a *different* source event (different record_id) for the
        # same subject → different identity.
        next_records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-diff",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", _ALT, "sym-different-event",
                        event_date_raw="2026-03-20", intensity="moderate"),
        ]
        next_ur = evaluate(next_records, snapshot_id="snap-N1")
        assert next_ur.subject_ref == inst.identity.subject_ref
        assert (next_ur.risk_candidate_refs[0].risk_identity_id
                != old_identity)
        # The adapter's identity match must be False.
        assert not R4LifecycleAdapter._identity_matches(next_ur, inst)

    def test_no_same_subject_fallback_in_identity_match(self):
        """The static identity matcher returns False for a same-subject
        positive whose candidate identity differs."""
        adapter, _, _ = _adapter()
        ur = _positive_unit_result(priority_rec_id="sym-1")
        outcome = adapter.promote_unit_result(ur)
        inst = adapter.lifecycle.get(outcome.established_risk_ids[0][0])
        # Same subject but a different event identity.
        other = _positive_unit_result(priority_rec_id="sym-other")
        assert not R4LifecycleAdapter._identity_matches(other, inst)


# ===========================================================================
# 3. Never auto-promote (matrix §3.6)
# ===========================================================================

class TestNoAutoPromotion:

    def test_candidate_not_auto_established_without_adjudication(self):
        """A registered candidate alone never becomes a risk."""
        adapter, _, lc = _adapter()
        ur = _positive_unit_result()
        registered = adapter.register_candidates(ur)
        assert len(registered) == 1
        assert lc.instances_for_project(PROJECT_ID) == []

    def test_negative_unit_registers_no_candidate(self):
        adapter, _, _ = _adapter()
        ur = _negative_unit_result()
        assert ur.l1_disposition == L1Disposition.NEGATIVE
        outcome = adapter.promote_unit_result(ur)
        assert not outcome.registered_any
        assert not outcome.established_any

    def test_boundary_unit_never_establishes_risk(self):
        """Boundary clues may register candidates but never establish a
        risk through machine adjudication."""
        adapter, _, lc = _adapter()
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-b-1",
                        event_date_raw="2026-03-10"),
            make_record("symptom_event", "MedDRA:10019242", "sym-b-1",
                        event_date_raw="2026-03", intensity="moderate"),
        ]
        ur = evaluate(records, snapshot_id="snap-N")
        assert ur.l1_disposition == L1Disposition.BOUNDARY
        outcome = adapter.promote_unit_result(ur)
        assert not outcome.established_any
        assert lc.instances_for_project(PROJECT_ID) == []


# ===========================================================================
# 4. Low/medium close by data with closed-ledger gate (Codex finding 4)
# ===========================================================================

class TestCloseByData:

    def _establish_low(self, adapter):
        ur = _positive_unit_result(intensity="mild")
        outcome = adapter.promote_unit_result(ur)
        return adapter.lifecycle.get(outcome.established_risk_ids[0][0])

    def test_machine_close_adjudication_is_rejected_by_evidence(self):
        """Machine close must use rejected_by_evidence outcome."""
        adapter, svc, _ = _adapter()
        inst = self._establish_low(adapter)
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        next_results, ledger = _machine_close_proof(inst)
        closed = adapter.machine_close_by_data(
            inst, coverage_snapshot_id="snap-N1",
            next_unit_results=next_results, coverage_ledger=ledger)
        assert closed.current_state == RiskLifecycleState.CLOSED
        close_tr = closed.transitions[-1]
        assert close_tr.transition_type == RiskTransitionType.CLOSED
        assert close_tr.reason == CLOSE_REASON_RESOLVED_BY_DATA
        adj = adapter.lifecycle.adjudication(close_tr.adjudication_id)
        assert adj.outcome == AdjudicationOutcome.REJECTED_BY_EVIDENCE
        assert adj.evidence.snapshot_id == "snap-N1"
        assert not adj.user_confirmed

    def test_close_requires_subsequent_snapshot_not_source(self):
        """Source snapshot cannot be reused as close coverage."""
        adapter, _, _ = _adapter()
        inst = self._establish_low(adapter)
        next_results, ledger = _machine_close_proof(
            inst, snapshot_id="snap-N")
        with pytest.raises(AdjudicationError, match="subsequent"):
            adapter.machine_close_by_data(
                inst, coverage_snapshot_id="snap-N",
                next_unit_results=next_results, coverage_ledger=ledger)

    def test_direct_machine_close_requires_complete_linked_proof(self):
        adapter, svc, _ = _adapter()
        inst = self._establish_low(adapter)
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        with pytest.raises(LifecycleAdapterError, match="coverage proof"):
            adapter.machine_close_by_data(
                inst, coverage_snapshot_id="snap-N1")

    def test_reconcile_close_requires_closed_ledger(self):
        """No closed ledger → risk stays active with a coverage-gap reason."""
        adapter, svc, _ = _adapter()
        inst = self._establish_low(adapter)
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        neg_ur = _negative_unit_result()
        result = adapter.reconcile_n_to_n1(
            [inst], [neg_ur], coverage_snapshot_id="snap-N1",
            coverage_ledger=None)
        assert result.closed == ()
        assert result.carry_forward == (inst,)
        assert len(result.coverage_gaps) == 1
        assert "no closed R4 CoverageLedger" in result.coverage_gaps[0]

    def test_reconcile_close_succeeds_with_closed_ledger(self):
        """Closed ledger + linked negative → close (Codex round-3 finding 4)."""
        adapter, svc, _ = _adapter()
        inst = self._establish_low(adapter)
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        neg_ur = _negative_unit_result()
        # Attach the exact historical risk link required for close.
        neg_ur = attach_risk_ref(
            neg_ur,
            risk_instance_id=inst.risk_instance_id,
            risk_identity_id=inst.risk_identity_id)
        ledger = make_closed_ledger(
            [neg_ur], snapshot_id="snap-N1", rule_lineage=RULE_LINEAGE)
        result = adapter.reconcile_n_to_n1(
            [inst], [neg_ur], coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert len(result.closed) == 1
        assert result.closed[0].current_state == RiskLifecycleState.CLOSED
        assert result.coverage_gaps == ()

    def test_reconcile_close_blocked_by_l1_not_evaluable(self):
        """L1 not_evaluable in the ledger → is_domain_complete false →
        risk stays active with a coverage-gap reason."""
        adapter, svc, _ = _adapter()
        inst = self._establish_low(adapter)
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        # Build a not_evaluable N+1 unit by omitting temporal_anchor from
        # available roles (missing required role → not_evaluable).
        from mm_r4.aemh import SemanticRecordSet
        ne_records = [
            make_record("subject_identity", "subject", "s-ne",
                        subject_ref="S001"),
            make_record("site_identity", "site", "st-ne",
                        subject_ref="S001"),
            make_record("reported_ae", "MedDRA:10019242", "ae-ne",
                        event_date_raw="2026-03-01",
                        subject_ref="S001"),
        ]
        ne_rs = SemanticRecordSet(
            records=tuple(ne_records),
            subject_ref="S001", site_ref="SITE01", scope_key="S001",
            available_roles=("subject_identity", "site_identity",
                             "reported_ae"),
            empty_covered_roles=("reported_mh",),
        )
        ne_ur = evaluate(
            [], record_set=ne_rs, snapshot_id="snap-N1",
            unit=make_unit(scope_key="S001"))
        assert ne_ur.l1_disposition == L1Disposition.NOT_EVALUABLE
        # The not_evaluable carry-forward path fires before the ledger
        # gate, so the risk carries forward with a gap reason.
        result = adapter.reconcile_n_to_n1(
            [inst], [ne_ur], coverage_snapshot_id="snap-N1",
            coverage_ledger=None)
        assert result.closed == ()
        assert len(result.carry_forward) == 1
        assert len(result.coverage_gaps) >= 1

    def test_reconcile_close_blocked_by_wrong_snapshot_provenance(self):
        """Closed ledger whose provenance snapshot differs from the
        coverage snapshot → risk stays active."""
        adapter, svc, _ = _adapter()
        inst = self._establish_low(adapter)
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        neg_ur = _negative_unit_result()
        # Ledger provenance points at the wrong snapshot.
        ledger = make_closed_ledger(
            [neg_ur], snapshot_id="snap-WRONG", rule_lineage=RULE_LINEAGE)
        result = adapter.reconcile_n_to_n1(
            [inst], [neg_ur], coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert result.closed == ()
        assert len(result.carry_forward) == 1
        assert len(result.coverage_gaps) == 1
        assert "provenance_snapshot_id" in result.coverage_gaps[0]


# ===========================================================================
# 5. High / SAE / AESI / user-confirmed carry forward (matrix §3.6)
# ===========================================================================

class TestCarryForward:

    def _high_records(self, rec_suffix="hi"):
        return [
            make_record("reported_ae", "MedDRA:10019242", f"ae-{rec_suffix}-1",
                        event_date_raw="2026-03-01"),
            make_record("healthcare_encounter", _ALT, f"hosp-{rec_suffix}-1",
                        event_date_raw="2026-03-15",
                        seriousness_criteria=("sae",)),
        ]

    def test_high_risk_blocks_machine_close(self):
        adapter, svc, _ = _adapter()
        ur = evaluate(self._high_records(), snapshot_id="snap-N")
        outcome = adapter.promote_unit_result(ur)
        inst = adapter.lifecycle.get(outcome.established_risk_ids[0][0])
        assert inst.severity == "high"
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        next_results, ledger = _machine_close_proof(inst)
        with pytest.raises(LifecycleAdapterError, match="low/medium"):
            adapter.machine_close_by_data(
                inst, coverage_snapshot_id="snap-N1",
                next_unit_results=next_results, coverage_ledger=ledger)

    def test_high_risk_user_confirmed_close_ok(self):
        adapter, svc, _ = _adapter()
        ur = evaluate(self._high_records("hu"), snapshot_id="snap-N")
        outcome = adapter.promote_unit_result(ur)
        inst = adapter.lifecycle.get(outcome.established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        closed = adapter.user_close_by_data(
            inst, coverage_snapshot_id="snap-N1")
        assert closed.current_state == RiskLifecycleState.CLOSED
        assert closed.ever_user_confirmed

    def test_must_carry_forward_predicate_high(self):
        adapter, _, _ = _adapter()
        ur = evaluate(self._high_records("cf"), snapshot_id="snap-N")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        assert R4LifecycleAdapter.must_carry_forward(inst)

    def test_high_risk_carries_forward_in_reconcile(self):
        """A high risk carries forward even with a complete coverage
        ledger and no matching positive."""
        adapter, svc, _ = _adapter()
        ur = evaluate(self._high_records("hn"), snapshot_id="snap-N")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        neg_ur = _negative_unit_result()
        ledger = make_closed_ledger(
            [neg_ur], snapshot_id="snap-N1", rule_lineage=RULE_LINEAGE)
        result = adapter.reconcile_n_to_n1(
            [inst], [neg_ur], coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert len(result.carry_forward) == 1
        assert result.closed == ()
        assert result.coverage_gaps

    def test_unknown_priority_carries_forward_with_complete_close_proof(self):
        """Unknown is not silently treated as low/medium for machine close."""
        adapter, svc, _ = _adapter()
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-unknown",
                        event_date_raw="2026-03-01"),
            make_record("cm_indication", _ALT, "cm-unknown",
                        event_date_raw="2026-03-15"),
        ]
        unit_result = evaluate(records, snapshot_id="snap-N")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(
                unit_result).established_risk_ids[0][0])
        assert inst.severity == "unknown"
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        next_results, ledger = _machine_close_proof(inst)
        result = adapter.reconcile_n_to_n1(
            [inst], next_results, coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert result.closed == ()
        assert result.carry_forward == (inst,)
        assert "unknown" in result.coverage_gaps[0]


# ===========================================================================
# 5b. Candidate criticality flags force high (frozen D04 §8.1, §10.4,
# §12 items 66/70)
# ===========================================================================

class TestCriticalityFlagNormalization:
    """The frozen D04 criticality flags on the candidate detail force
    effective priority high / R2 severity high before establishment even
    when the caller passes medium, then the *persisted* high severity is
    the durable machine-close ban.  A present non-bool flag fails closed
    (CoverageValidationError) before any side effect, and the adapter
    asserts the persisted severity is high after establishment or fails
    closed.  Candidates carrying neither key (D01-D03) are unchanged."""

    def _establish_flagged(self, adapter, *, flags, priority="medium"):
        candidate = _flagged_candidate(
            _positive_unit_result(intensity="moderate"), **flags)
        adapter.lifecycle.register_candidate(candidate)
        return adapter.establish_positive_candidate(
            candidate, monitoring_priority=priority)

    def test_rights_or_safety_critical_forces_high_despite_medium(self):
        adapter, _, lc = _adapter()
        inst = self._establish_flagged(
            adapter, flags={"rights_or_safety_critical": True})
        assert inst.severity == "high"
        assert lc.get(inst.risk_instance_id).severity == "high"

    def test_machine_close_forbidden_forces_high_despite_medium(self):
        adapter, _, lc = _adapter()
        inst = self._establish_flagged(
            adapter, flags={"machine_close_forbidden": True})
        assert inst.severity == "high"
        assert lc.get(inst.risk_instance_id).severity == "high"

    def test_both_flags_true_forces_high(self):
        adapter, _, lc = _adapter()
        inst = self._establish_flagged(
            adapter, flags={"rights_or_safety_critical": True,
                            "machine_close_forbidden": True})
        assert inst.severity == "high"
        assert lc.get(inst.risk_instance_id).severity == "high"

    def test_flagged_high_input_stays_high(self):
        adapter, _, _ = _adapter()
        inst = self._establish_flagged(
            adapter, flags={"rights_or_safety_critical": True},
            priority="high")
        assert inst.severity == "high"

    def test_present_false_flags_keep_caller_priority_unchanged(self):
        """Present-but-false flags must not force high: D01-D03 behavior
        is preserved for candidates carrying the keys as False."""
        adapter, _, lc = _adapter()
        inst = self._establish_flagged(
            adapter, flags={"rights_or_safety_critical": False,
                            "machine_close_forbidden": False})
        assert inst.severity == "medium"
        assert lc.get(inst.risk_instance_id).severity == "medium"

    def test_present_false_flag_with_low_priority_stays_low(self):
        adapter, _, _ = _adapter()
        inst = self._establish_flagged(
            adapter, flags={"machine_close_forbidden": False},
            priority="low")
        assert inst.severity == "low"

    def test_non_bool_rights_flag_fails_closed_before_side_effect(self):
        adapter, _, lc = _adapter()
        candidate = _flagged_candidate(
            _positive_unit_result(intensity="moderate"),
            rights_or_safety_critical="yes")
        adapter.lifecycle.register_candidate(candidate)
        with pytest.raises(CoverageValidationError):
            adapter.establish_positive_candidate(
                candidate, monitoring_priority="medium")
        assert lc.instances_for_project(PROJECT_ID) == []

    def test_non_bool_machine_close_flag_fails_closed(self):
        adapter, _, lc = _adapter()
        candidate = _flagged_candidate(
            _positive_unit_result(intensity="moderate"),
            machine_close_forbidden=1)
        adapter.lifecycle.register_candidate(candidate)
        with pytest.raises(CoverageValidationError):
            adapter.establish_positive_candidate(
                candidate, monitoring_priority="medium")
        assert lc.instances_for_project(PROJECT_ID) == []

    def test_post_establish_severity_assertion_fails_closed(self):
        """If the persisted R2 severity diverges from the forced high
        (simulated by stubbing the severity projection), the adapter fails
        closed after establishment instead of returning the instance."""
        from unittest import mock
        adapter, _, _ = _adapter()
        candidate = _flagged_candidate(
            _positive_unit_result(intensity="moderate"),
            rights_or_safety_critical=True)
        adapter.lifecycle.register_candidate(candidate)
        with mock.patch(
                "mm_r4.lifecycle.map_priority_to_r2_severity",
                return_value="medium"):
            with pytest.raises(LifecycleAdapterError, match="severity"):
                adapter.establish_positive_candidate(
                    candidate, monitoring_priority="medium")

    def test_promote_unit_result_forces_high_via_unit_candidates(self):
        """End-to-end through the public promote path: a unit result
        carrying a flagged candidate with medium grading establishes a
        high-severity R2 risk (frozen D04 §12.66)."""
        from dataclasses import replace
        from mm_r4.contracts import RiskCandidateRef
        adapter, _, lc = _adapter()
        ur = _positive_unit_result(intensity="moderate")
        assert ur.monitoring_priority == MONITORING_PRIORITY_MEDIUM
        flagged = _flagged_candidate(
            ur, rights_or_safety_critical=True,
            machine_close_forbidden=True)
        ref = ur.risk_candidate_refs[0]
        new_ref = RiskCandidateRef(
            candidate_id=flagged.candidate_id,
            risk_identity_id=ref.risk_identity_id,
            locator=ref.locator,
        )
        flagged_ur = replace(
            ur, r2_candidates=(flagged,), risk_candidate_refs=(new_ref,))
        outcome = adapter.promote_unit_result(flagged_ur)
        assert outcome.established_any
        inst = lc.get(outcome.established_risk_ids[0][0])
        assert inst.severity == "high"

    def test_flagged_high_instance_refuses_machine_close(self):
        """The persisted high severity from a flagged candidate is the
        durable close ban: direct machine close is rejected and
        reconciliation carries the risk forward (frozen D04 §10.4)."""
        adapter, svc, _ = _adapter()
        inst = self._establish_flagged(
            adapter, flags={"rights_or_safety_critical": True,
                            "machine_close_forbidden": True})
        assert inst.severity == "high"
        assert R4LifecycleAdapter.must_carry_forward(inst)
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        next_results, ledger = _machine_close_proof(inst)
        with pytest.raises(LifecycleAdapterError, match="low/medium"):
            adapter.machine_close_by_data(
                inst, coverage_snapshot_id="snap-N1",
                next_unit_results=next_results, coverage_ledger=ledger)
        result = adapter.reconcile_n_to_n1(
            [inst], next_results, coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert result.closed == ()
        assert len(result.carry_forward) == 1
        assert result.carry_forward[0].severity == "high"


# ===========================================================================
# 6. Identity ambiguity (matrix §3.6, Codex finding 6)
# ===========================================================================

class TestIdentityAmbiguity:

    def test_mark_identity_ambiguous_blocks_auto_close(self):
        adapter, _, lc = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        ambiguous = adapter.mark_identity_ambiguous(inst)
        assert ambiguous.current_state == RiskLifecycleState.IDENTITY_AMBIGUOUS
        assert ambiguous.is_active
        with pytest.raises(AdjudicationError, match="requires a bound"):
            lc.transition(
                inst.risk_instance_id, RiskTransitionType.CLOSED,
                actor="system_policy", reason="x")

    def test_direct_machine_close_rejects_identity_ambiguous(self):
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        ambiguous = adapter.mark_identity_ambiguous(inst)
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        next_results, ledger = _machine_close_proof(ambiguous)
        with pytest.raises(
                LifecycleAdapterError, match="identity_ambiguous"):
            adapter.machine_close_by_data(
                ambiguous, coverage_snapshot_id="snap-N1",
                next_unit_results=next_results, coverage_ledger=ledger)

    def test_competing_identities_block_close(self):
        """Two N+1 candidates claiming the same stable event with
        different identities → identity_ambiguous, not close."""
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(priority_rec_id="sym-comp")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        # Two N+1 candidates for the same stable event (same record_id
        # "sym-comp", same concept _ALT) but under two *different* rule
        # lineages (v2 and v3), neither matching the instance's v1.
        # Both share the instance's classifier (stable core) but have
        # mutually incompatible identities.
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-comp",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", _ALT, "sym-comp",
                        event_date_raw="2026-03-15", intensity="moderate"),
        ]
        # Use different units (different rule_or_knowledge_lineage) so the
        # unit_ids differ and the duplicate check does not fire.
        unit_v2 = make_unit(scope_key="S001")
        unit_v2 = type(unit_v2)(
            project_id=unit_v2.project_id, domain_id=unit_v2.domain_id,
            scope_type=unit_v2.scope_type, scope_key=unit_v2.scope_key,
            normalized_concept_or_rule_item=unit_v2.normalized_concept_or_rule_item,
            temporal_window=unit_v2.temporal_window,
            rule_or_knowledge_lineage="d01-aemh-rule-v2",
            unit_algorithm_version=unit_v2.unit_algorithm_version)
        unit_v3 = make_unit(scope_key="S001")
        unit_v3 = type(unit_v3)(
            project_id=unit_v3.project_id, domain_id=unit_v3.domain_id,
            scope_type=unit_v3.scope_type, scope_key=unit_v3.scope_key,
            normalized_concept_or_rule_item=unit_v3.normalized_concept_or_rule_item,
            temporal_window=unit_v3.temporal_window,
            rule_or_knowledge_lineage="d01-aemh-rule-v3",
            unit_algorithm_version=unit_v3.unit_algorithm_version)
        next_v2 = evaluate(records, snapshot_id="snap-N1",
                           rule_lineage="d01-aemh-rule-v2", unit=unit_v2)
        next_v3 = evaluate(records, snapshot_id="snap-N1",
                           rule_lineage="d01-aemh-rule-v3", unit=unit_v3)
        assert next_v2.unit_id != next_v3.unit_id
        # Neither matches the instance identity (different scope).
        inst_core = inst.identity.classifier
        assert next_v2.risk_candidate_refs[0].risk_identity_id != (
            inst.risk_identity_id)
        assert next_v3.risk_candidate_refs[0].risk_identity_id != (
            inst.risk_identity_id)
        # Both share the same stable core but have different identities.
        from mm_r4.aemh import candidate_stable_core
        assert candidate_stable_core(next_v2.r2_candidates[0]) == inst_core
        assert candidate_stable_core(next_v3.r2_candidates[0]) == inst_core
        assert (next_v2.risk_candidate_refs[0].risk_identity_id
                != next_v3.risk_candidate_refs[0].risk_identity_id)
        result = adapter.reconcile_n_to_n1(
            [inst], [next_v2, next_v3], coverage_snapshot_id="snap-N1")
        assert result.closed == ()
        assert len(result.identity_ambiguous) == 1


# ===========================================================================
# 7. Supersede / terminate on lineage change (Codex finding 6)
# ===========================================================================

class TestSupersedeAndTerminate:

    def test_supersede_on_lineage_change(self):
        """Same stable event re-evaluated under a changed rule lineage →
        superseded, never closed by data."""
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(priority_rec_id="sym-sup")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        # N+1: same stable event (same record_id) but changed rule lineage.
        next_records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-sup",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", _ALT, "sym-sup",
                        event_date_raw="2026-03-15", intensity="mild"),
        ]
        next_ur = evaluate(next_records, snapshot_id="snap-N1",
                           rule_lineage="d01-aemh-rule-v2")
        result = adapter.reconcile_n_to_n1(
            [inst], [next_ur], coverage_snapshot_id="snap-N1")
        assert len(result.superseded) == 1
        assert result.superseded[0].current_state == RiskLifecycleState.SUPERSEDED
        assert result.closed == ()
        assert result.carry_forward == ()

    def test_supersede_transition_type_and_adjudication(self):
        adapter, _, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        sup = adapter.supersede(inst)
        tr = sup.transitions[-1]
        assert tr.transition_type == RiskTransitionType.SUPERSEDED
        adj = adapter.lifecycle.adjudication(tr.adjudication_id)
        assert adj.outcome == AdjudicationOutcome.VERSION_MISMATCH
        assert adj.action == "supersede"

    def test_terminate_not_evaluable_is_terminal(self):
        adapter, _, lc = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        terminated = adapter.terminate_not_evaluable(inst)
        assert terminated.current_state == RiskLifecycleState.NOT_EVALUABLE
        with pytest.raises(IllegalTransitionError):
            lc.transition(
                inst.risk_instance_id, RiskTransitionType.ESCALATED,
                actor="system_policy", reason="x")

    def test_terminal_not_evaluable_cannot_reopen(self):
        """Terminal L3 not_evaluable cannot transition to reopened."""
        adapter, _, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        terminated = adapter.terminate_not_evaluable(inst)
        assert terminated.current_state == RiskLifecycleState.NOT_EVALUABLE
        from mm_r4.lifecycle import LifecycleAdapterError
        with pytest.raises((IllegalTransitionError, LifecycleAdapterError)):
            adapter.reopen(terminated)


# ===========================================================================
# 8. Reopen only through legal adjudication (Codex finding 7)
# ===========================================================================

class TestReopen:

    def test_closed_reopens_through_adjudicated_transition(self):
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        next_results, ledger = _machine_close_proof(inst)
        closed = adapter.machine_close_by_data(
            inst, coverage_snapshot_id="snap-N1",
            next_unit_results=next_results, coverage_ledger=ledger)
        assert closed.current_state == RiskLifecycleState.CLOSED
        reopened = adapter.reopen(closed)
        assert reopened.current_state == RiskLifecycleState.REOPENED
        tr = reopened.transitions[-1]
        assert tr.transition_type == RiskTransitionType.REOPENED
        adj = adapter.lifecycle.adjudication(tr.adjudication_id)
        assert adj.outcome == AdjudicationOutcome.DISTINCT_SUPPORTED
        assert adj.action == "reopen"

    def test_reopen_non_closed_is_rejected(self):
        """Reopening an established (non-closed) risk is rejected."""
        adapter, _, _ = _adapter()
        ur = _positive_unit_result(intensity="moderate")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        assert inst.current_state == RiskLifecycleState.ESTABLISHED
        with pytest.raises(
                Exception,
                match="reopen requires a closed risk"):
            adapter.reopen(inst)

    def test_user_confirmed_persists_after_reopen(self):
        """A previously user-confirmed risk remains ever_user_confirmed
        after a legal reopen and cannot be machine-closed."""
        adapter, svc, _ = _adapter()
        records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-uc-1",
                        event_date_raw="2026-03-01"),
            make_record("healthcare_encounter", _ALT, "hosp-uc-1",
                        event_date_raw="2026-03-15",
                        seriousness_criteria=("sae",)),
        ]
        ur = evaluate(records, snapshot_id="snap-N")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        # User-confirmed close.
        closed = adapter.user_close_by_data(
            inst, coverage_snapshot_id="snap-N1")
        assert closed.ever_user_confirmed
        # Legal reopen.
        reopened = adapter.reopen(closed)
        assert reopened.ever_user_confirmed
        assert reopened.current_state == RiskLifecycleState.REOPENED
        # Machine close during reconciliation is blocked for ever_user_confirmed.
        neg_ur = _negative_unit_result()
        ledger = make_closed_ledger(
            [neg_ur], snapshot_id="snap-N1", rule_lineage=RULE_LINEAGE)
        result = adapter.reconcile_n_to_n1(
            [reopened], [neg_ur], coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert result.closed == ()
        assert len(result.carry_forward) == 1


# ===========================================================================
# 9. N→N+1 reconciliation: persistence and carry-forward
# ===========================================================================

class TestReconcileNToN1:

    def test_persistence_when_next_snapshot_has_matching_positive(self):
        adapter, _, _ = _adapter()
        ur = _positive_unit_result(intensity="moderate")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        # N+1: same subject, same source event → exact identity persists.
        next_ur = _positive_unit_result(priority_rec_id="sym-1")
        result = adapter.reconcile_n_to_n1([inst], [next_ur])
        assert len(result.persisted) == 1
        assert result.closed == ()
        assert result.carry_forward == ()

    def test_subject_absent_in_next_blocks_close(self):
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        other_records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-oth-1",
                        event_date_raw="2026-03-15", subject_ref="S999",
                        site_ref="SITE99"),
            make_record("symptom_event", _ALT, "sym-oth-1",
                        event_date_raw="2026-03-15", subject_ref="S999",
                        site_ref="SITE99", intensity="moderate"),
        ]
        other_rs = make_record_set(
            other_records, subject_ref="S999", site_ref="SITE99")
        other_ur = evaluate(
            [], record_set=other_rs, snapshot_id="snap-N1",
            unit=make_unit(scope_key="S999"))
        result = adapter.reconcile_n_to_n1(
            [inst], [other_ur], coverage_snapshot_id="snap-N1")
        assert len(result.identity_ambiguous) == 1
        assert result.closed == ()

    def test_l1_not_evaluable_carries_forward_active_risk(self):
        """N+1 L1 not_evaluable preserves the existing active risk and
        exposes a coverage gap; L1 never changes L3 (Codex finding 5)."""
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        from mm_r4.aemh import SemanticRecordSet
        ne_records = [
            make_record("subject_identity", "subject", "s-ne2",
                        subject_ref="S001"),
            make_record("site_identity", "site", "st-ne2",
                        subject_ref="S001"),
            make_record("reported_ae", "MedDRA:10019242", "ae-ne2",
                        event_date_raw="2026-03-01",
                        subject_ref="S001"),
        ]
        ne_rs = SemanticRecordSet(
            records=tuple(ne_records),
            subject_ref="S001", site_ref="SITE01", scope_key="S001",
            available_roles=("subject_identity", "site_identity",
                             "reported_ae"),
            empty_covered_roles=("reported_mh",),
        )
        ne_ur = evaluate(
            [], record_set=ne_rs, snapshot_id="snap-N1",
            unit=make_unit(scope_key="S001"))
        assert ne_ur.l1_disposition == L1Disposition.NOT_EVALUABLE
        result = adapter.reconcile_n_to_n1(
            [inst], [ne_ur], coverage_snapshot_id="snap-N1",
            coverage_ledger=None)
        assert result.closed == ()
        assert len(result.carry_forward) == 1
        carried = result.carry_forward[0]
        assert carried.current_state == RiskLifecycleState.ESTABLISHED
        assert len(result.coverage_gaps) >= 1
        assert "not_evaluable" in result.coverage_gaps[0]


# ===========================================================================
# 10. Query export != send (matrix §5.1)
# ===========================================================================

class TestQueryNotSend:

    def test_query_draft_has_no_sent_flag(self):
        """A QueryDraftRef carries basis/finding/action/source links only;
        it never has a 'sent'/'status' field (export != send)."""
        from mm_r4.contracts import QueryDraftRef, SourceLocator
        loc = SourceLocator(
            snapshot_id="snap-N", source_revision_id="rev-N",
            table_semantic="reported_ae", record_id="r1", column_or_anchor="row")
        q = QueryDraftRef(
            query_id="q1", unit_id="u1",
            basis="依据", finding="发现", action="行动项",
            source_locator_ids=(loc.locator_id(),),
            linked_candidate_id="c1")
        assert not hasattr(q, "sent")
        assert not hasattr(q, "status")
        assert not hasattr(q, "is_sent")

    def test_positive_unit_query_has_three_parts(self):
        ur = _positive_unit_result()
        assert ur.query_refs
        q = ur.query_refs[0]
        assert q.basis and q.finding and q.action
        assert q.unit_id == ur.unit_id


# ===========================================================================
# 11. Round-3 corrections
# ===========================================================================

class TestStableAcrossRevision:
    """Codex round-3 finding 1: stable event identity survives snapshot/
    revision changes."""

    def test_same_stable_event_same_identity_across_revisions(self):
        """N and N+1 use different snapshot/revision locators but the same
        semantic role + stable record/event id, concept, time window and
        lineage → the public R2 ``risk_identity_id`` must be exactly equal."""
        records_n = [
            make_record("reported_ae", "MedDRA:10019242", "ae-stable",
                        event_date_raw="2026-03-01",
                        snapshot_id="snap-N",
                        source_revision_id="rev-N"),
            make_record("symptom_event", _ALT, "sym-stable",
                        event_date_raw="2026-03-15", intensity="moderate",
                        snapshot_id="snap-N",
                        source_revision_id="rev-N"),
        ]
        records_n1 = [
            make_record("reported_ae", "MedDRA:10019242", "ae-stable",
                        event_date_raw="2026-03-01",
                        snapshot_id="snap-N1",
                        source_revision_id="rev-N1"),
            make_record("symptom_event", _ALT, "sym-stable",
                        event_date_raw="2026-03-15", intensity="moderate",
                        snapshot_id="snap-N1",
                        source_revision_id="rev-N1"),
        ]
        ur_n = evaluate(records_n, snapshot_id="snap-N")
        ur_n1 = evaluate(records_n1, snapshot_id="snap-N1")
        assert (ur_n.risk_candidate_refs[0].risk_identity_id
                == ur_n1.risk_candidate_refs[0].risk_identity_id)

    def test_changed_record_id_is_different_identity(self):
        """A changed record/event id produces a different identity."""
        records_a = [
            make_record("reported_ae", "MedDRA:10019242", "ae-a",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", _ALT, "sym-a",
                        event_date_raw="2026-03-15", intensity="moderate"),
        ]
        records_b = [
            make_record("reported_ae", "MedDRA:10019242", "ae-b",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", _ALT, "sym-b",
                        event_date_raw="2026-03-15", intensity="moderate"),
        ]
        ur_a = evaluate(records_a, snapshot_id="snap-N")
        ur_b = evaluate(records_b, snapshot_id="snap-N")
        assert (ur_a.risk_candidate_refs[0].risk_identity_id
                != ur_b.risk_candidate_refs[0].risk_identity_id)


class TestFailClosedIdentity:
    """Codex round-3 finding 3: stripped/tampered identity metadata is
    rejected before any side effect."""

    def test_stripped_classifier_rejected_before_establish(self):
        """A candidate with stripped classifier detail fails before any
        adjudication and leaves the lifecycle empty."""
        from mm_r4.lifecycle import LifecycleAdapterError
        adapter, _, lc = _adapter()
        from mm_r2.risk import RiskCandidate
        stripped = RiskCandidate.from_signal(
            project_id=PROJECT_ID,
            subject_ref="S001",
            domain="D01_aemh",
            signal_type="potential_unreported_ae_symptom",
            source_snapshot_id="snap-N",
            rule_activation_id=RULE_LINEAGE,
            detail={"concept": "x"},  # no identity metadata
        )
        adapter.lifecycle.register_candidate(stripped)
        with pytest.raises(LifecycleAdapterError, match="scope"):
            adapter.establish_positive_candidate(
                stripped, monitoring_priority="low")
        assert lc.instances_for_project(PROJECT_ID) == []

    def test_stripped_scope_rejected_before_establish(self):
        from mm_r4.lifecycle import LifecycleAdapterError
        adapter, _, lc = _adapter()
        from mm_r2.risk import RiskCandidate
        stripped = RiskCandidate.from_signal(
            project_id=PROJECT_ID,
            subject_ref="S001",
            domain="D01_aemh",
            signal_type="potential_unreported_ae_symptom",
            source_snapshot_id="snap-N",
            rule_activation_id=RULE_LINEAGE,
            detail={"classifier": "x", "stable_core": "x",
                    "lineage_fingerprint": "x", "risk_identity_id": "x"},
            # no "scope"
        )
        adapter.lifecycle.register_candidate(stripped)
        with pytest.raises(LifecycleAdapterError, match="scope"):
            adapter.establish_positive_candidate(
                stripped, monitoring_priority="low")
        assert lc.instances_for_project(PROJECT_ID) == []

    def test_tampered_nonempty_identity_rejected_before_side_effect(self):
        """A non-empty but forged identity is recomputed and rejected before
        adjudication/establishment, leaving no risk instance behind."""
        from mm_r2.risk import RiskCandidate
        from mm_r4.lifecycle import LifecycleAdapterError

        adapter, _, lc = _adapter()
        original = _positive_unit_result().r2_candidates[0]
        detail = dict(original.detail)
        detail["risk_identity_id"] = "risk-id-" + ("0" * 64)
        tampered = RiskCandidate.from_signal(
            project_id=original.project_id,
            subject_ref=original.subject_ref,
            domain=original.domain,
            signal_type=original.signal_type,
            source_snapshot_id=original.source_snapshot_id,
            rule_activation_id=original.rule_activation_id,
            mapping_result_id=original.mapping_result_id,
            knowledge_pack_id=original.knowledge_pack_id,
            severity_hint=original.severity_hint,
            confidence_hint=original.confidence_hint,
            detail=detail,
        )
        adapter.lifecycle.register_candidate(tampered)
        with pytest.raises(LifecycleAdapterError, match="public R2 identity"):
            adapter.establish_positive_candidate(
                tampered, monitoring_priority="low")
        assert lc.instances_for_project(PROJECT_ID) == []

    def test_mismatched_candidate_ref_rejected_before_registration(self):
        """The unit candidate/ref join is validated before registering any
        candidate, including a non-empty forged ref identity."""
        from dataclasses import replace

        from mm_r2.risk import RiskError
        from mm_r4.contracts import RiskCandidateRef
        from mm_r4.lifecycle import LifecycleAdapterError

        adapter, _, lc = _adapter()
        unit_result = _positive_unit_result()
        candidate = unit_result.r2_candidates[0]
        original_ref = unit_result.risk_candidate_refs[0]
        forged_ref = RiskCandidateRef(
            candidate_id=original_ref.candidate_id,
            risk_identity_id="risk-id-" + ("0" * 64),
            locator=original_ref.locator,
        )
        malformed = replace(
            unit_result, risk_candidate_refs=(forged_ref,))
        with pytest.raises(LifecycleAdapterError, match="candidate ref"):
            adapter.register_candidates(malformed)
        with pytest.raises(RiskError, match="unknown candidate"):
            lc.candidate(candidate.candidate_id)
        assert lc.instances_for_project(PROJECT_ID) == []


class TestUncertaintyCarryForward:
    """Codex round-3 finding 5: boundary/not-applicable/different-event
    never closes; risk carries forward."""

    def test_boundary_n1_carries_forward(self):
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        # N+1: boundary result for same subject.
        bnd_records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-bnd-cf",
                        event_date_raw="2026-03-10", subject_ref="S001"),
            make_record("symptom_event", "MedDRA:10019242", "sym-bnd-cf",
                        event_date_raw="2026-03", intensity="moderate",
                        subject_ref="S001"),
        ]
        bnd_ur = evaluate(bnd_records, snapshot_id="snap-N1")
        assert bnd_ur.l1_disposition == L1Disposition.BOUNDARY
        result = adapter.reconcile_n_to_n1(
            [inst], [bnd_ur], coverage_snapshot_id="snap-N1")
        assert result.closed == ()
        assert len(result.carry_forward) == 1

    def test_not_applicable_n1_carries_forward(self):
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        from mm_r4.fixtures import make_boundary
        na_records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-na-cf",
                        event_date_raw="2026-03-01", subject_ref="S001"),
        ]
        na_ur = evaluate(
            na_records, snapshot_id="snap-N1",
            protocol_boundary=make_boundary(
                applicable=False,
                non_applicable_reason="不收集 AE/MH"))
        assert na_ur.l1_disposition == L1Disposition.NOT_APPLICABLE
        result = adapter.reconcile_n_to_n1(
            [inst], [na_ur], coverage_snapshot_id="snap-N1")
        assert result.closed == ()
        assert len(result.carry_forward) == 1

    def test_different_event_positive_keeps_old_risk_active(self):
        """A different-event positive for the same subject must neither
        persist the old identity nor close it."""
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(priority_rec_id="sym-old")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        # N+1: a *different* event for the same subject.
        diff_records = [
            make_record("reported_ae", "MedDRA:10019242", "ae-diff-ev",
                        event_date_raw="2026-03-01"),
            make_record("symptom_event", _ALT, "sym-different",
                        event_date_raw="2026-03-20", intensity="moderate"),
        ]
        diff_ur = evaluate(diff_records, snapshot_id="snap-N1")
        result = adapter.reconcile_n_to_n1(
            [inst], [diff_ur], coverage_snapshot_id="snap-N1")
        assert result.closed == ()
        assert result.persisted == ()
        assert len(result.carry_forward) == 1


class TestLinkedNegativeRequired:
    """Codex round-3 finding 4: close requires exact linked negative."""

    def test_close_blocked_without_linked_negative(self):
        """A closed ledger with no linked negative unit → risk stays active."""
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        neg_ur = _negative_unit_result()
        # No attach_risk_ref → no linked negative.
        ledger = make_closed_ledger(
            [neg_ur], snapshot_id="snap-N1", rule_lineage=RULE_LINEAGE)
        result = adapter.reconcile_n_to_n1(
            [inst], [neg_ur], coverage_snapshot_id="snap-N1",
            coverage_ledger=ledger)
        assert result.closed == ()
        assert len(result.carry_forward) == 1
        assert "NEGATIVE" in result.coverage_gaps[0]


class TestDuplicateUnitRejection:
    """Codex round-3 finding 6: duplicate unit_id values are rejected."""

    def test_duplicate_unit_ids_produce_gap(self):
        adapter, svc, _ = _adapter()
        ur = _positive_unit_result(intensity="mild")
        inst = adapter.lifecycle.get(
            adapter.promote_unit_result(ur).established_risk_ids[0][0])
        make_subsequent_snapshot(
            svc, snapshot_id="snap-N1", revision_id="rev-N1")
        neg1 = _negative_unit_result()
        neg2 = _negative_unit_result()
        # Same default unit → same unit_id → duplicate.
        assert neg1.unit_id == neg2.unit_id
        result = adapter.reconcile_n_to_n1(
            [inst], [neg1, neg2], coverage_snapshot_id="snap-N1")
        assert result.closed == ()
        assert len(result.coverage_gaps) >= 1
        assert "duplicate" in result.coverage_gaps[0]


class TestNoSysPathMutation:
    """Codex round-3 finding 2: no runtime sys.path mutation or tests-helper
    import."""

    def test_no_sys_path_or_helpers_import_in_runtime_modules(self):
        """No runtime module has ``import sys``, ``sys.path`` attribute
        access, or ``helpers_b`` import (Codex round-3 finding 2).  Pure
        AST check -- docstrings do not count."""
        import ast
        pkg = Path(__file__).resolve().parents[1] / "src" / "mm_r4"
        offenders = []
        for src in sorted(pkg.glob("*.py")):
            text = src.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(src))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "sys":
                            offenders.append(f"{src.name}: imports sys")
                if isinstance(node, ast.ImportFrom):
                    if node.module and "helpers_b" in node.module:
                        offenders.append(
                            f"{src.name}: helpers_b import")
                if isinstance(node, ast.Attribute):
                    if (isinstance(node.value, ast.Name)
                            and node.value.id == "sys"
                            and node.attr == "path"):
                        offenders.append(
                            f"{src.name}: sys.path access")
        assert offenders == [], (
            "sys.path/helpers_b violations: " + "; ".join(offenders))
