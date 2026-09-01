"""Batch B modes tests: immutable contracts, real AcceptanceService binding,
blocked rejection, derived fields, carry-forward, and VETO 1+2 regressions."""

from __future__ import annotations
import pytest
import mm_r2.modes as modes_module
from types import MappingProxyType

from mm_r2.domain import (
    DomainValidationError, IdentityAlgorithm, ListingSnapshot,
    MappingDefinition, MappingResult, SourceRevision,
)
from mm_r2.acceptance import (
    ACCEPTED_BY_SYSTEM_POLICY, AcceptanceChainError, AcceptanceService,
    SnapshotAcceptanceState, SnapshotBinding,
)
from mm_r2.identity import IdentityResolution, make_record_identity
from mm_r2.modes import (
    ExecutionBasis, LockedVersionSelection, MODE_CONTRACTS, ModeContract,
    ModeContractError,
    MonitoringMode, MonitoringRun, RunManager, get_mode_contract,
)
from helpers_b import make_accepted_snapshot


class TestModeContractsImmutable:
    def test_three_modes(self):
        assert set(MODE_CONTRACTS.keys()) == {
            MonitoringMode.DAILY, MonitoringMode.PRE_LOCK,
            MonitoringMode.POST_LOCK_PRE_CFDI}

    def test_is_mapping_proxy(self):
        assert isinstance(MODE_CONTRACTS, MappingProxyType)

    def test_cannot_replace_at_runtime(self):
        with pytest.raises(TypeError):
            MODE_CONTRACTS["daily"] = None

    def test_daily_contract(self):
        c = get_mode_contract(MonitoringMode.DAILY)
        assert c.requires_accepted_snapshot
        assert c.allows_subsequent_snapshots

    def test_pre_lock_contract(self):
        c = get_mode_contract(MonitoringMode.PRE_LOCK)
        assert c.requires_explicit_cutoff
        assert c.requires_lock_prep_window

    def test_post_lock_contract(self):
        c = get_mode_contract(MonitoringMode.POST_LOCK_PRE_CFDI)
        assert c.requires_user_selected_locked_version
        assert c.fixed_total

    def test_unknown_mode_rejected(self):
        with pytest.raises(ModeContractError):
            get_mode_contract("nonexistent")

    def test_entry_conditions_listed(self):
        c = get_mode_contract(MonitoringMode.PRE_LOCK)
        conditions = c.entry_conditions()
        assert any("cutoff" in cond for cond in conditions)


class TestRunCreationAuthority:
    def test_daily_run_with_accepted_snapshot(self):
        svc = AcceptanceService(local_user="test")
        snap = make_accepted_snapshot(svc)
        rm = RunManager()
        run = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                            "s1", svc, cutoff="c1", actor="sys")
        assert run.mode == MonitoringMode.DAILY

    def test_fake_snapshot_rejected(self):
        svc = AcceptanceService(local_user="test")
        rm = RunManager()
        with pytest.raises(ModeContractError, match="not registered"):
            rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                          "fake-snap", svc, actor="sys")

    def test_no_acceptance_service_rejected(self):
        rm = RunManager()
        with pytest.raises(ModeContractError, match="AcceptanceService"):
            rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                          "s1", None, actor="sys")

    def test_duck_typed_service_rejected(self):
        """VETO 2-6: duck-typed fake AcceptanceService rejected."""
        rm = RunManager()
        class FakeSvc:
            def get(self, sid): pass
            def binding(self, sid): pass
        with pytest.raises(ModeContractError, match="real AcceptanceService"):
            rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                          "s1", FakeSvc(), actor="sys")

    def test_hostile_acceptance_subclass_rejected(self):
        class HostileAcceptance(AcceptanceService):
            def get(self, snapshot_id):
                raise AssertionError("hostile override must not run")

        rm = RunManager()
        with pytest.raises(ModeContractError, match="real AcceptanceService"):
            rm.create_run(
                "p1", MonitoringMode.DAILY, ExecutionBasis.FULL, "s1",
                HostileAcceptance(local_user="test"), actor="sys",
            )

    def test_blocked_eligible_snapshot_rejected(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        with pytest.raises(AcceptanceChainError):
            svc.advance(
                "s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                ACCEPTED_BY_SYSTEM_POLICY,
            )
        assert svc.get("s1").blocked
        with pytest.raises(ModeContractError, match="blocked"):
            RunManager().create_run(
                "p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                "s1", svc, actor="sys",
            )

    def test_unaccepted_snapshot_rejected(self):
        svc = AcceptanceService(local_user="test")
        rows = [{"subject": "S01"}]
        source = SourceRevision.from_bytes("rev-1", "p1", "listing", "v1", b"x")
        snap = ListingSnapshot.from_content("s1", "p1", "rev-1", "c1", rows)
        algo = IdentityAlgorithm(algorithm_id="a1", name="r", version="1")
        mapping = MappingDefinition(
            mapping_id="m1", project_id="p1", source_revision_id="rev-1",
            identity_algorithm_id="a1", source_field="AETERM",
            canonical_field="ae_term", version="1", confidence=1.0, is_critical=True)
        result = MappingResult.from_verified("mr1", "p1", snap, mapping, algo, record_count=1)
        rec_id = make_record_identity("p1", algo, {"subject": "S01"})
        res = IdentityResolution(algorithm=algo, resolved=(rec_id,))
        binding = SnapshotBinding(
            project_id="p1", snapshot=snap, source=source,
            identity_algorithm=algo, mapping_definitions=(mapping,),
            mapping_results=(result,), identity_resolution=res)
        svc.register(binding, ACCEPTED_BY_SYSTEM_POLICY)
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                    ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        rm = RunManager()
        with pytest.raises(ModeContractError, match="not accepted"):
            rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                          "s1", svc, actor="sys")

    def test_pre_lock_requires_cutoff(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        with pytest.raises(ModeContractError, match="cutoff"):
            rm.create_run("p1", MonitoringMode.PRE_LOCK, ExecutionBasis.FULL,
                          "s1", svc, lock_prep_window=True, actor="sys")

    def test_pre_lock_requires_lock_prep_window(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        with pytest.raises(ModeContractError, match="lock-prep"):
            rm.create_run("p1", MonitoringMode.PRE_LOCK, ExecutionBasis.FULL,
                          "s1", svc, cutoff="c1", actor="sys")

    def test_post_lock_requires_user_selected(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        with pytest.raises(ModeContractError, match="service-issued"):
            rm.create_run("p1", MonitoringMode.POST_LOCK_PRE_CFDI, ExecutionBasis.FULL,
                          "s1", svc, actor="sys")

    def test_revision_derived_from_binding(self):
        """VETO 2-7: revision is derived from the binding, not caller-supplied."""
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc, rid="rev-actual")
        rm = RunManager()
        run = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                            "s1", svc, cutoff="c1", actor="sys")
        assert run.source_revision_id == "rev-actual"

    def test_mapping_and_identity_derived(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        run = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                            "s1", svc, cutoff="c1", actor="sys")
        # Derived from binding.
        assert run.mapping_version == "1"
        assert len(run.identity_algorithm_digest) == 64

    def test_no_reachable_verified_run(self):
        """VETO 2-2: _verified_run not reachable."""
        rm = RunManager()
        assert not hasattr(rm, "_verified_run")

    def test_module_does_not_expose_run_issuer(self):
        assert not hasattr(modes_module, "_issue_run")
        assert not hasattr(modes_module, "_issue_selection")

    def test_locked_selection_direct_construction_blocked(self):
        with pytest.raises(DomainValidationError, match="RunManager issuance"):
            LockedVersionSelection(
                selection_id="x", project_id="p1", snapshot_id="s1",
                selected_by="test", snapshot_content_hash="a" * 64,
                acceptance_evidence_hash="b" * 64,
            )

    def test_locked_selection_requires_configured_local_user(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        with pytest.raises(ModeContractError, match="configured local user"):
            rm.select_locked_version("p1", "s1", svc, user="attacker")
        with pytest.raises(ModeContractError, match="configured local user"):
            rm.select_locked_version("p1", "s1", svc, user="system_policy")

    def test_caller_asserted_locked_boolean_is_not_an_api(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        with pytest.raises(TypeError, match="user_selected_locked_version"):
            RunManager().create_run(
                "p1", MonitoringMode.POST_LOCK_PRE_CFDI,
                ExecutionBasis.FULL, "s1", svc,
                user_selected_locked_version=True, actor="system_policy",
            )


class TestPostLockFixedTotal:
    def _locked_run(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc, sid="s1")
        make_accepted_snapshot(svc, rid="rev-2", sid="s2")
        rm = RunManager()
        selection = rm.select_locked_version(
            "p1", "s1", svc, user="test"
        )
        locked = rm.create_run(
            "p1", MonitoringMode.POST_LOCK_PRE_CFDI, ExecutionBasis.FULL,
            "s1", svc, locked_version_selection=selection, actor="sys",
        )
        return svc, rm, locked

    def test_post_lock_rejects_incremental(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        selection = rm.select_locked_version("p1", "s1", svc, user="test")
        with pytest.raises(ModeContractError, match="requires a full run"):
            rm.create_run(
                "p1", MonitoringMode.POST_LOCK_PRE_CFDI,
                ExecutionBasis.INCREMENTAL, "s1", svc,
                locked_version_selection=selection, actor="sys",
            )

    def test_post_lock_reuses_exact_locked_snapshot(self):
        svc, rm, _ = self._locked_run()
        selection = rm.select_locked_version("p1", "s2", svc, user="test")
        with pytest.raises(ModeContractError, match="reuse the same locked snapshot"):
            rm.create_run(
                "p1", MonitoringMode.POST_LOCK_PRE_CFDI,
                ExecutionBasis.FULL, "s2", svc,
                locked_version_selection=selection, actor="sys",
            )

    def test_selection_from_another_manager_rejected(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        selection = RunManager().select_locked_version(
            "p1", "s1", svc, user="test"
        )
        with pytest.raises(ModeContractError, match="not registered"):
            RunManager().create_run(
                "p1", MonitoringMode.POST_LOCK_PRE_CFDI,
                ExecutionBasis.FULL, "s1", svc,
                locked_version_selection=selection, actor="sys",
            )

    def test_post_lock_is_terminal_for_locked_version(self):
        svc, rm, locked = self._locked_run()
        with pytest.raises(ModeContractError, match="terminal"):
            rm.create_run(
                "p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                "s2", svc, carry_forward_run_ids=[locked.run_id], actor="sys",
            )


class TestNoSilentModeConversion:
    def test_silent_mode_change_blocked(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                      "s1", svc, cutoff="c1", actor="sys")
        with pytest.raises(ModeContractError, match="carry_forward"):
            rm.create_run("p1", MonitoringMode.PRE_LOCK, ExecutionBasis.FULL,
                          "s1", svc, cutoff="c2", lock_prep_window=True, actor="sys")

    def test_mode_change_with_carry_forward(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        r1 = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                           "s1", svc, cutoff="c1", actor="sys")
        r2 = rm.change_mode("p1", MonitoringMode.PRE_LOCK, ExecutionBasis.FULL,
                            "s1", svc, carry_forward_run_ids=[r1.run_id],
                            cutoff="c2", lock_prep_window=True, actor="sys")
        assert r1.run_id != r2.run_id
        assert r1.run_id in r2.carry_forward_run_ids

    def test_carry_forward_must_include_prior(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        r1 = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                           "s1", svc, cutoff="c1", actor="sys")
        r2 = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                           "s1", svc, cutoff="c2", actor="sys")
        with pytest.raises(ModeContractError, match="immediate prior"):
            rm.change_mode("p1", MonitoringMode.PRE_LOCK, ExecutionBasis.FULL,
                           "s1", svc, carry_forward_run_ids=[r1.run_id],
                           cutoff="c3", lock_prep_window=True, actor="sys")

    def test_fake_carry_forward_rejected(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        with pytest.raises(ModeContractError, match="does not reference"):
            rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                          "s1", svc, carry_forward_run_ids=["fake"], actor="sys")

    def test_cross_project_carry_forward_rejected(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc, pid="p1")
        make_accepted_snapshot(svc, pid="p2", rid="rev-2", sid="s2")
        rm = RunManager()
        r1 = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                           "s1", svc, cutoff="c1", actor="sys")
        with pytest.raises(ModeContractError, match="different project"):
            rm.create_run("p2", MonitoringMode.PRE_LOCK, ExecutionBasis.FULL,
                          "s2", svc, carry_forward_run_ids=[r1.run_id],
                          cutoff="c2", lock_prep_window=True, actor="sys")

    def test_same_mode_no_carry_forward_required(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                      "s1", svc, cutoff="c1", actor="sys")
        r2 = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                           "s1", svc, cutoff="c2", actor="sys")
        assert r2.mode == MonitoringMode.DAILY


class TestRunImmutability:
    def test_direct_construction_blocked(self):
        with pytest.raises(DomainValidationError, match="service-issued"):
            MonitoringRun(run_id="x", project_id="p1", mode=MonitoringMode.DAILY,
                          execution_basis=ExecutionBasis.FULL,
                          source_revision_id="r", snapshot_id="s", actor="a")

    def test_run_mode_immutable(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        run = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                            "s1", svc, cutoff="c1", actor="sys")
        with pytest.raises(Exception):
            run.mode = MonitoringMode.PRE_LOCK  # type: ignore

    def test_run_hash_valid(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        run = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                            "s1", svc, cutoff="c1", actor="sys")
        assert run.run_hash == run.compute_hash()
        assert len(run.run_hash) == 64

    def test_invalid_mode_rejected(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        with pytest.raises(ModeContractError):
            rm.create_run("p1", "bogus", ExecutionBasis.FULL, "s1", svc, actor="sys")

    def test_invalid_basis_rejected(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        with pytest.raises(ModeContractError):
            rm.create_run("p1", MonitoringMode.DAILY, "bogus", "s1", svc, actor="sys")

    def test_runs_for_project_ordered(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc)
        rm = RunManager()
        r1 = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                           "s1", svc, cutoff="c1", actor="sys")
        r2 = rm.create_run("p1", MonitoringMode.DAILY, ExecutionBasis.FULL,
                           "s1", svc, cutoff="c2", actor="sys")
        runs = rm.runs_for_project("p1")
        assert len(runs) == 2
        assert runs[0].run_id == r1.run_id
        assert runs[1].run_id == r2.run_id
