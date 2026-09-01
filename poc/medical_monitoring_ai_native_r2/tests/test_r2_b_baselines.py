"""Batch B baselines tests: live AcceptanceService binding, content comparison,
blocked rejection, orthogonality, history, and VETO 1+2 negative regressions."""

from __future__ import annotations
import pytest
import mm_r2.baselines as baselines_module

from mm_r2.domain import DomainValidationError, ListingSnapshot
from mm_r2.baselines import BaselineError, BaselineService, DataBaseline, MedicalDecisionVersion
from helpers_b import make_accepted_snapshot
from mm_r2.acceptance import (
    ACCEPTED_BY_SYSTEM_POLICY, AcceptanceChainError, AcceptanceService,
    SnapshotAcceptanceState,
)


class TestDataBaselineAuthority:
    def test_eligible_snapshot_becomes_baseline(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap = make_accepted_snapshot(svc)
        bl = bsvc.set_data_baseline(svc, snap)
        assert bl.snapshot_id == "s1"
        assert len(bl.acceptance_evidence_hash) == 64
        assert len(bl.identity_algorithm_digest) == 64

    def test_non_eligible_rejected(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap = make_accepted_snapshot(svc, eligible=False)
        with pytest.raises(BaselineError, match="not baseline_eligible"):
            bsvc.set_data_baseline(svc, snap)

    def test_unregistered_snapshot_rejected(self):
        bsvc = BaselineService()
        snap = ListingSnapshot.from_content("fake", "p1", "rev-1", "c1", [{"subject": "S01"}])
        svc = AcceptanceService(local_user="test")
        with pytest.raises(BaselineError, match="not registered"):
            bsvc.set_data_baseline(svc, snap)

    def test_no_acceptance_service_rejected(self):
        bsvc = BaselineService()
        snap = ListingSnapshot.from_content("s1", "p1", "rev-1", "c1", [{"subject": "S01"}])
        with pytest.raises(BaselineError, match="AcceptanceService"):
            bsvc.set_data_baseline(None, snap)

    def test_duck_typed_service_rejected(self):
        """VETO 2-5: duck-typed fake AcceptanceService is rejected."""
        bsvc = BaselineService()
        snap = ListingSnapshot.from_content("s1", "p1", "rev-1", "c1", [{"subject": "S01"}])
        class FakeSvc:
            def get(self, sid): pass
            def binding(self, sid): pass
        with pytest.raises(BaselineError, match="real AcceptanceService"):
            bsvc.set_data_baseline(FakeSvc(), snap)

    def test_hostile_acceptance_subclass_rejected(self):
        class HostileAcceptance(AcceptanceService):
            def get(self, snapshot_id):
                raise AssertionError("hostile override must not run")

        bsvc = BaselineService()
        snap = ListingSnapshot.from_content(
            "s1", "p1", "rev-1", "c1", [{"subject": "S01"}]
        )
        with pytest.raises(BaselineError, match="real AcceptanceService"):
            bsvc.set_data_baseline(HostileAcceptance(local_user="test"), snap)

    def test_project_mismatch_rejected(self):
        svc = AcceptanceService(local_user="test")
        make_accepted_snapshot(svc, pid="p1", sid="s1")
        bsvc = BaselineService()
        snap_fake = ListingSnapshot.from_content("s1", "p2", "rev-1", "c1", [{"subject": "S01"}])
        with pytest.raises(BaselineError, match="project_id"):
            bsvc.set_data_baseline(svc, snap_fake)

    def test_same_id_different_content_rejected(self):
        """VETO 2-4: same snapshot ID with different content fails."""
        svc = AcceptanceService(local_user="test")
        snap = make_accepted_snapshot(svc, sid="s1", rows=[{"subject": "S01", "ae": "N"}])
        bsvc = BaselineService()
        # Create a different-content snapshot with same ID.
        snap_fake = ListingSnapshot.from_content("s1", "p1", "rev-1", "c1",
                                                  [{"subject": "S01", "ae": "DIFFERENT"}])
        with pytest.raises(BaselineError, match="content_hash"):
            bsvc.set_data_baseline(svc, snap_fake)

    def test_blocked_record_rejected(self):
        """A blocked audit record cannot reuse retained eligible state."""
        svc = AcceptanceService(local_user="test")
        snap = make_accepted_snapshot(svc)
        bsvc = BaselineService()
        with pytest.raises(AcceptanceChainError):
            svc.advance(
                "s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                ACCEPTED_BY_SYSTEM_POLICY,
            )
        assert svc.get("s1").blocked
        with pytest.raises(BaselineError, match="blocked"):
            bsvc.set_data_baseline(svc, snap)

    def test_module_does_not_expose_issuers(self):
        assert not hasattr(baselines_module, "_issue_baseline")
        assert not hasattr(baselines_module, "_issue_mdv")

    def test_direct_construction_blocked(self):
        with pytest.raises(DomainValidationError, match="service-issued"):
            DataBaseline(
                baseline_id="x", project_id="p1", snapshot_id="s1",
                snapshot_content_hash="a" * 64, snapshot_content_digest="b" * 64,
                source_revision_id="r", identity_algorithm_digest="c" * 64,
                acceptance_evidence_hash="d" * 64)

    def test_no_reachable_verified_baseline(self):
        """VETO 2-1: _verified_baseline not reachable."""
        bsvc = BaselineService()
        assert not hasattr(bsvc, "_verified_baseline")

    def test_no_reachable_verified_mdv(self):
        bsvc = BaselineService()
        assert not hasattr(bsvc, "_verified_mdv")

    def test_empty_evidence_hash_rejected(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap = make_accepted_snapshot(svc)
        bl = bsvc.set_data_baseline(svc, snap)
        assert bl.acceptance_evidence_hash != ""


class TestOrthogonality:
    def test_medical_version_does_not_block_baseline(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        bsvc.record_medical_decision_version("p1", version_kind="provisional", actor="sys")
        snap = make_accepted_snapshot(svc)
        bl = bsvc.set_data_baseline(svc, snap)
        assert bl is not None

    def test_baseline_does_not_require_medical_version(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap = make_accepted_snapshot(svc)
        bsvc.set_data_baseline(svc, snap)
        assert bsvc.current_medical_decision_version("p1") is None

    def test_unknown_data_baseline_reference_rejected(self):
        bsvc = BaselineService()
        with pytest.raises(BaselineError, match="unknown data baseline"):
            bsvc.record_medical_decision_version(
                "p1", data_baseline_id="dbl-missing", actor="test"
            )

    def test_cross_project_data_baseline_reference_rejected(self):
        svc = AcceptanceService(local_user="test")
        snap = make_accepted_snapshot(svc, pid="p1")
        bsvc = BaselineService()
        baseline = bsvc.set_data_baseline(svc, snap)
        with pytest.raises(BaselineError, match="belongs to project"):
            bsvc.record_medical_decision_version(
                "p2", data_baseline_id=baseline.baseline_id, actor="test"
            )

    def test_data_baseline_does_not_rewrite_medical_version(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        mdv = bsvc.record_medical_decision_version("p1", version_kind="signed",
                                                    actor="user1", rationale="reviewed")
        snap = make_accepted_snapshot(svc)
        bsvc.set_data_baseline(svc, snap)
        assert bsvc.current_medical_decision_version("p1").version_id == mdv.version_id

    def test_signed_requires_rationale(self):
        bsvc = BaselineService()
        with pytest.raises(DomainValidationError, match="rationale"):
            bsvc.record_medical_decision_version("p1", version_kind="signed", actor="sys")

    def test_exported_requires_rationale(self):
        bsvc = BaselineService()
        with pytest.raises(DomainValidationError, match="rationale"):
            bsvc.record_medical_decision_version("p1", version_kind="exported", actor="sys")

    def test_invalid_kind_rejected(self):
        bsvc = BaselineService()
        with pytest.raises(DomainValidationError, match="invalid"):
            bsvc.record_medical_decision_version("p1", version_kind="bad", actor="sys")

    def test_direct_mdv_construction_blocked(self):
        with pytest.raises(DomainValidationError, match="service-issued"):
            MedicalDecisionVersion(version_id="x", project_id="p1", actor="sys")

    def test_orthogonal_types(self):
        assert DataBaseline is not MedicalDecisionVersion


class TestBaselineHistory:
    def test_current_baseline_advances(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap1 = make_accepted_snapshot(svc, sid="s1", rows=[{"subject": "S01", "ae": "N"}])
        snap2 = make_accepted_snapshot(svc, rid="rev-2", sid="s2",
                                       rows=[{"subject": "S01", "ae": "V"}])
        bsvc.set_data_baseline(svc, snap1)
        bsvc.set_data_baseline(svc, snap2)
        assert bsvc.current_data_baseline("p1").snapshot_id == "s2"

    def test_baseline_history_retained(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap1 = make_accepted_snapshot(svc, sid="s1", rows=[{"subject": "S01", "ae": "N"}])
        snap2 = make_accepted_snapshot(svc, rid="rev-2", sid="s2",
                                       rows=[{"subject": "S01", "ae": "V"}])
        bsvc.set_data_baseline(svc, snap1)
        bsvc.set_data_baseline(svc, snap2)
        assert len(bsvc.data_baseline_history("p1")) == 2

    def test_data_baseline_by_snapshot(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap = make_accepted_snapshot(svc, sid="s1")
        bsvc.set_data_baseline(svc, snap)
        assert bsvc.data_baseline_by_snapshot("s1") is not None
        assert bsvc.data_baseline_by_snapshot("s2") is None

    def test_medical_versions_append_only(self):
        bsvc = BaselineService()
        v1 = bsvc.record_medical_decision_version("p1", version_kind="provisional", actor="sys")
        v2 = bsvc.record_medical_decision_version("p1", version_kind="signed",
                                                   actor="u", rationale="r")
        versions = bsvc.medical_decision_versions("p1")
        assert len(versions) == 2
        assert versions[0].version_id == v1.version_id
        assert versions[1].version_id == v2.version_id


class TestDeterminism:
    def test_baseline_hash_valid(self):
        svc = AcceptanceService(local_user="test")
        bsvc = BaselineService()
        snap = make_accepted_snapshot(svc)
        bl = bsvc.set_data_baseline(svc, snap)
        assert bl.baseline_hash == bl.compute_hash()
        assert len(bl.baseline_hash) == 64

    def test_version_hash_valid(self):
        bsvc = BaselineService()
        mdv = bsvc.record_medical_decision_version("p1", version_kind="signed",
                                                    actor="u", rationale="r")
        assert mdv.version_hash == mdv.compute_hash()
        assert len(mdv.version_hash) == 64
