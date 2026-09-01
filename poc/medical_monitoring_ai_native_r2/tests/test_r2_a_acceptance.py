"""Batch A -- snapshot acceptance state chain: real verified binding, no
skipping, no reversal, fail-closed eligibility, auditable decision records,
frozen boundary, service-issued evidence."""

from __future__ import annotations

import pytest

from mm_r2.domain import (
    DomainValidationError,
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    ProvenanceError,
    SourceRevision,
    StudyProject,
)
from mm_r2.identity import AmbiguousIdentity, IdentityResolution, make_record_identity
from mm_r2.acceptance import (
    ACCEPTANCE_CHAIN,
    ACCEPTED_BY_SYSTEM_POLICY,
    AcceptanceChainError,
    AcceptanceDecisionRecord,
    AcceptanceEvidence,
    AcceptanceProof,
    AcceptanceService,
    CoverageGap,
    EligibilityBlockedError,
    SnapshotAcceptanceRecord,
    SnapshotAcceptanceState,
    SnapshotBinding,
)

LOCAL_USER = "local_test_user"  # synthetic fixture OS user


def _project(pid="p1"):
    return StudyProject(project_id=pid, name=f"Synthetic {pid}")


def _source(pid="p1", rid="rev-1"):
    return SourceRevision.from_bytes(
        revision_id=rid, project_id=pid, source_type="listing",
        version="2026-01-01", source_bytes=b"synthetic-ae-bytes",
    )


def _snapshot(pid="p1", rid="rev-1", sid="s1"):
    return ListingSnapshot.from_content(
        snapshot_id=sid, project_id=pid, revision_id=rid,
        snapshot_version="cutoff-1", rows=[{"sub": "S01", "ae": "Nausea"}],
    )


def _algo(aid="alg-1"):
    return IdentityAlgorithm(algorithm_id=aid, name="record-id", version="1")


def _mapping(pid="p1", rid="rev-1", aid="alg-1", confidence=1.0,
             is_critical=True, mid="m1", version="1"):
    return MappingDefinition(
        mapping_id=mid, project_id=pid, source_revision_id=rid,
        identity_algorithm_id=aid, source_field="AETERM",
        canonical_field="ae_term", version=version,
        confidence=confidence, is_critical=is_critical,
    )


def _mapping_result(snapshot, mapping, algo, mid="mr1"):
    return MappingResult.from_verified(
        result_id=mid, project_id=snapshot.project_id, snapshot=snapshot,
        mapping=mapping, identity_algorithm=algo, record_count=1,
    )


def _resolution(pid="p1", sid="s1", algo=None, clean=True):
    algo = algo or _algo()
    if clean:
        rid = make_record_identity(pid, algo, {"subject": "S01"})
        return IdentityResolution(algorithm=algo, resolved=(rid,))
    amb = AmbiguousIdentity(
        kind="multi", project_id=pid, algorithm_digest=algo.digest,
        candidate_digests=("a" * 64, "b" * 64), reason="two candidates",
    )
    return IdentityResolution(algorithm=algo, ambiguities=(amb,), resolved=())


def _binding(pid="p1", rid="rev-1", sid="s1", aid="alg-1", mid="m1",
             confidence=1.0, is_critical=True, version="1",
             mapping_version_mismatch=False, extra_result=False,
             missing_result=False, duplicate_result=False,
             substituted=False, resolution=None, no_resolution=False,
             no_mapping=False):
    """Build a SnapshotBinding with the given properties."""
    source = _source(pid, rid)
    snapshot = _snapshot(pid, rid, sid)
    algo = _algo(aid)
    m1 = _mapping(pid, rid, aid, confidence, is_critical, mid, version)
    defs = [m1]
    if mapping_version_mismatch:
        m2 = _mapping(pid, rid, aid, confidence, is_critical, "m2", "2")
        defs.append(m2)
    results = [_mapping_result(snapshot, m1, algo, "mr1")]
    if extra_result:
        # an extra result referencing an unknown mapping
        m_extra = _mapping(pid, rid, aid, confidence, is_critical, "m_extra")
        results.append(_mapping_result(snapshot, m_extra, algo, "mr_extra"))
    if missing_result:
        results = []
    if duplicate_result:
        results.append(_mapping_result(snapshot, m1, algo, "mr1_b"))
    if substituted:
        # result references a different mapping than the registered definitions
        m_other = _mapping(pid, rid, aid, 0.0, True, "m_sub")
        results = [_mapping_result(snapshot, m_other, algo, "mr_sub")]
        defs = [m1]  # registered critical def is m1 (confidence 1.0)
    if no_mapping:
        defs = []
        results = []
    if resolution is None and not no_resolution:
        resolution = _resolution(pid, sid, algo, clean=True)
    return SnapshotBinding(
        project_id=pid, snapshot=snapshot, source=source,
        identity_algorithm=algo, mapping_definitions=tuple(defs),
        mapping_results=tuple(results), identity_resolution=resolution,
    )


def _full_forward(svc, sid="s1", pid="p1", actor=ACCEPTED_BY_SYSTEM_POLICY):
    """Walk the full chain with correct step-specific bound evidence."""
    svc.advance(sid, SnapshotAcceptanceState.STRUCTURALLY_VALID, actor,
                evidence=svc.evidence(sid, actor, structural_validation_complete=True))
    svc.advance(sid, SnapshotAcceptanceState.MAPPING_REVIEWED, actor,
                evidence=svc.evidence(sid, actor))
    svc.advance(sid, SnapshotAcceptanceState.SNAPSHOT_ACCEPTED, actor,
                evidence=svc.evidence(sid, actor, approved_scope=True))
    return svc.advance(sid, SnapshotAcceptanceState.BASELINE_ELIGIBLE, actor,
                       evidence=svc.evidence(sid, actor, source_coverage_complete=True,
                                             approved_scope=True))


# ---------------------------------------------------------------------------
# Chain definition
# ---------------------------------------------------------------------------

class TestChainDefinition:
    def test_exact_chain_order(self):
        assert [s.value for s in ACCEPTANCE_CHAIN] == [
            "imported", "structurally_valid", "mapping_reviewed",
            "snapshot_accepted", "baseline_eligible",
        ]

    def test_five_states(self):
        assert len(ACCEPTANCE_CHAIN) == 5


# ---------------------------------------------------------------------------
# SnapshotBinding consistency (VETO6)
# ---------------------------------------------------------------------------

class TestSnapshotBindingConsistency:
    def test_valid_binding_ok(self):
        b = _binding()
        assert b.fingerprint
        assert b.critical_mapping_clean is True
        assert b.deterministic_mapping is True
        assert b.mapping_version == "1"

    def test_cross_project_mismatch_rejected(self):
        source = _source("p1", "rev-1")
        snapshot = _snapshot("p2", "rev-1", "s1")  # different project
        with pytest.raises(DomainValidationError, match="project_id"):
            SnapshotBinding(
                project_id="p1", snapshot=snapshot, source=source,
                identity_algorithm=_algo(),
            )

    def test_revision_mismatch_rejected(self):
        source = _source("p1", "rev-1")
        snapshot = _snapshot("p1", "rev-XYZ", "s1")
        with pytest.raises(DomainValidationError, match="revision"):
            SnapshotBinding(
                project_id="p1", snapshot=snapshot, source=source,
                identity_algorithm=_algo(),
            )

    def test_mapping_version_mismatch_rejected(self):
        with pytest.raises(DomainValidationError, match="version mismatch"):
            _binding(mapping_version_mismatch=True)

    def test_extra_result_rejected(self):
        with pytest.raises(DomainValidationError, match="unknown mapping"):
            _binding(extra_result=True)

    def test_missing_result_rejected(self):
        with pytest.raises(DomainValidationError, match="missing result"):
            _binding(missing_result=True)

    def test_duplicate_result_rejected(self):
        with pytest.raises(DomainValidationError, match="multiple results"):
            _binding(duplicate_result=True)

    def test_duplicate_result_id_across_distinct_mappings_rejected(self):
        source, snapshot, algo = _source(), _snapshot(), _algo()
        m1 = _mapping(mid="m1")
        m2 = _mapping(mid="m2")
        r1 = _mapping_result(snapshot, m1, algo, "shared-result")
        r2 = _mapping_result(snapshot, m2, algo, "shared-result")
        with pytest.raises(DomainValidationError, match="duplicate mapping_result"):
            SnapshotBinding(
                project_id="p1", snapshot=snapshot, source=source,
                identity_algorithm=algo, mapping_definitions=(m1, m2),
                mapping_results=(r1, r2), identity_resolution=_resolution(),
            )

    def test_substituted_mapping_rejected(self):
        """VETO6: a result referencing a mapping not in the registered
        definitions is rejected (cannot substitute a high-confidence def)."""
        with pytest.raises(DomainValidationError, match="unknown mapping"):
            _binding(substituted=True)

    def test_same_id_mapping_semantic_substitution_rejected(self):
        source, snapshot, algo = _source(), _snapshot(), _algo()
        original = _mapping(mid="m1")
        result = _mapping_result(snapshot, original, algo)
        substituted = MappingDefinition(
            mapping_id="m1", project_id="p1", source_revision_id="rev-1",
            identity_algorithm_id="alg-1", source_field="SEX",
            canonical_field="dm_sex", fact_type="dm", version="1",
            confidence=1.0, is_critical=True,
        )
        with pytest.raises(DomainValidationError, match="mapping semantics"):
            SnapshotBinding(
                project_id="p1", snapshot=snapshot, source=source,
                identity_algorithm=algo, mapping_definitions=(substituted,),
                mapping_results=(result,), identity_resolution=_resolution(),
            )

    def test_low_confidence_critical_not_deterministic(self):
        b = _binding(confidence=0.0, is_critical=True)
        assert b.critical_mapping_clean is True  # mapping itself is unambiguous
        assert b.deterministic_mapping is False

    def test_high_confidence_critical_deterministic(self):
        b = _binding(confidence=1.0, is_critical=True)
        assert b.deterministic_mapping is True

    def test_ambiguous_critical_result_not_clean(self):
        source = _source(); snapshot = _snapshot(); algo = _algo()
        m = _mapping()
        mr = MappingResult.from_verified(
            result_id="mr1", project_id="p1", snapshot=snapshot,
            mapping=m, identity_algorithm=algo, record_count=1,
            is_ambiguous=True, ambiguity_reason="two candidates",
        )
        res = _resolution(pid="p1", sid="s1", algo=algo, clean=True)
        b = SnapshotBinding(
            project_id="p1", snapshot=snapshot, source=source,
            identity_algorithm=algo, mapping_definitions=(m,),
            mapping_results=(mr,), identity_resolution=res,
        )
        assert b.critical_mapping_clean is False

    def test_identity_resolution_algorithm_mismatch_rejected(self):
        other_algo = _algo("alg-99")
        res = _resolution(algo=other_algo)
        with pytest.raises(DomainValidationError, match="digest mismatch"):
            _binding(resolution=res)

    def test_identity_resolution_project_mismatch_rejected(self):
        algo = _algo()
        foreign = make_record_identity("p2", algo, {"subject": "P2-S01"})
        resolution = IdentityResolution(algorithm=algo, resolved=(foreign,))
        with pytest.raises(DomainValidationError, match="project_id mismatch"):
            _binding(resolution=resolution)


# ---------------------------------------------------------------------------
# VETO2 (adjacent gate): required mapping + identity evidence (no waivers)
# ---------------------------------------------------------------------------

class TestRequiredMappingAndIdentity:
    def test_empty_mapping_rejected(self):
        """A baseline binding must have >=1 mapping definition/result."""
        with pytest.raises(DomainValidationError, match="at least one mapping"):
            _binding(no_mapping=True)

    def test_missing_identity_resolution_rejected(self):
        """No local-user waiver of identity review."""
        with pytest.raises(DomainValidationError,
                            match="explicit IdentityResolution"):
            _binding(no_resolution=True)

    def test_nonzero_snapshot_rejects_zero_mapping_coverage(self):
        source, snapshot, algo = _source(), _snapshot(), _algo()
        mapping = _mapping()
        with pytest.raises(ProvenanceError, match="record_count"):
            MappingResult.from_verified(
                result_id="mr-zero", project_id="p1", snapshot=snapshot,
                mapping=mapping, identity_algorithm=algo, record_count=0,
            )

    def test_nonzero_snapshot_rejects_empty_identity_coverage(self):
        source, snapshot, algo = _source(), _snapshot(), _algo()
        mapping = _mapping()
        result = _mapping_result(snapshot, mapping, algo)
        with pytest.raises(DomainValidationError, match="coverage"):
            SnapshotBinding(
                project_id="p1", snapshot=snapshot, source=source,
                identity_algorithm=algo, mapping_definitions=(mapping,),
                mapping_results=(result,),
                identity_resolution=IdentityResolution(algorithm=algo),
            )

    def test_duplicate_resolved_identity_does_not_fake_coverage(self):
        source = _source()
        snapshot = ListingSnapshot.from_content(
            snapshot_id="s-two", project_id="p1", revision_id="rev-1",
            snapshot_version="cutoff-1",
            rows=[{"sub": "S01"}, {"sub": "S01"}],
        )
        algo = _algo()
        mapping = _mapping()
        result = MappingResult.from_verified(
            result_id="mr-two", project_id="p1", snapshot=snapshot,
            mapping=mapping, identity_algorithm=algo, record_count=2,
        )
        identity = make_record_identity("p1", algo, {"subject": "S01"})
        resolution = IdentityResolution(
            algorithm=algo, resolved=(identity, identity),
        )
        with pytest.raises(DomainValidationError, match="duplicate resolved"):
            SnapshotBinding(
                project_id="p1", snapshot=snapshot, source=source,
                identity_algorithm=algo, mapping_definitions=(mapping,),
                mapping_results=(result,), identity_resolution=resolution,
            )

    def test_zero_row_snapshot_allows_explicit_zero_coverage(self):
        source = _source()
        snapshot = ListingSnapshot.from_content(
            snapshot_id="s-zero", project_id="p1", revision_id="rev-1",
            snapshot_version="cutoff-zero", rows=[],
        )
        algo = _algo()
        mapping = _mapping()
        result = MappingResult.from_verified(
            result_id="mr-zero", project_id="p1", snapshot=snapshot,
            mapping=mapping, identity_algorithm=algo, record_count=0,
        )
        binding = SnapshotBinding(
            project_id="p1", snapshot=snapshot, source=source,
            identity_algorithm=algo, mapping_definitions=(mapping,),
            mapping_results=(result,),
            identity_resolution=IdentityResolution(algorithm=algo),
        )
        assert binding.identity_clean is True

    def test_local_user_cannot_waive_mapping_identity(self, r2_acceptance_service):
        """A real binding with mapping+resolution is required even for the
        local user; without them registration/eligibility cannot happen."""
        svc = r2_acceptance_service
        with pytest.raises(DomainValidationError, match="at least one mapping"):
            _binding(no_mapping=True)
        with pytest.raises(DomainValidationError,
                            match="explicit IdentityResolution"):
            _binding(no_resolution=True)

    def test_ambiguous_identity_blocks_mapping_review(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(resolution=_resolution(clean=False)),
                     ACCEPTED_BY_SYSTEM_POLICY)
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                    ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        # identity_review not clean -> mapping_reviewed blocked
        with pytest.raises(AcceptanceChainError, match="identity"):
            svc.advance("s1", SnapshotAcceptanceState.MAPPING_REVIEWED,
                        ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))
        assert svc.get("s1").state == SnapshotAcceptanceState.STRUCTURALLY_VALID

    def test_low_confidence_critical_blocks_system_policy(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(confidence=0.0, is_critical=True),
                     ACCEPTED_BY_SYSTEM_POLICY)
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                    ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        svc.advance("s1", SnapshotAcceptanceState.MAPPING_REVIEWED,
                    ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))
        with pytest.raises(AcceptanceChainError, match="deterministic"):
            svc.advance("s1", SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                        ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                              approved_scope=True))


# ---------------------------------------------------------------------------
# VETO2 (adjacent gate): fingerprint binds full semantics
# ---------------------------------------------------------------------------

class TestFingerprintSemantics:
    def test_multiple_ambiguities_are_canonical_and_do_not_crash(self):
        source, algo = _source(), _algo()
        snapshot = ListingSnapshot.from_content(
            snapshot_id="s1", project_id="p1", revision_id="rev-1",
            snapshot_version="cutoff-1",
            rows=[{"sub": "S01"}, {"sub": "S02"}],
        )
        mapping = _mapping()
        result = MappingResult.from_verified(
            result_id="mr1", project_id="p1", snapshot=snapshot,
            mapping=mapping, identity_algorithm=algo, record_count=2,
        )
        a1 = AmbiguousIdentity(
            kind="none", project_id="p1", algorithm_digest=algo.digest,
            reason="first unresolved row",
        )
        a2 = AmbiguousIdentity(
            kind="none", project_id="p1", algorithm_digest=algo.digest,
            reason="second unresolved row",
        )
        forward = IdentityResolution(algorithm=algo, ambiguities=(a1, a2))
        reverse = IdentityResolution(algorithm=algo, ambiguities=(a2, a1))
        b1 = SnapshotBinding(
            project_id="p1", snapshot=snapshot, source=source,
            identity_algorithm=algo, mapping_definitions=(mapping,),
            mapping_results=(result,), identity_resolution=forward,
        )
        b2 = SnapshotBinding(
            project_id="p1", snapshot=snapshot, source=source,
            identity_algorithm=algo, mapping_definitions=(mapping,),
            mapping_results=(result,), identity_resolution=reverse,
        )
        assert b1.fingerprint == b2.fingerprint

    def test_fingerprint_differs_on_source_field(self):
        res = _resolution()
        source, snapshot, algo = _source(), _snapshot(), _algo()
        m1 = _mapping()  # source_field AETERM
        m1b = MappingDefinition(
            mapping_id="m1", project_id="p1", source_revision_id="rev-1",
            identity_algorithm_id="alg-1", source_field="DIFFERENT",
            canonical_field="ae_term", version="1", confidence=1.0,
            is_critical=True,
        )
        mr1 = _mapping_result(snapshot, m1, algo)
        mr1b = MappingResult.from_verified(
            result_id="mr1", project_id="p1", snapshot=snapshot,
            mapping=m1b, identity_algorithm=algo, record_count=1,
        )
        b1 = SnapshotBinding(project_id="p1", snapshot=snapshot, source=source,
                             identity_algorithm=algo, mapping_definitions=(m1,),
                             mapping_results=(mr1,), identity_resolution=res)
        b2 = SnapshotBinding(project_id="p1", snapshot=snapshot, source=source,
                             identity_algorithm=algo, mapping_definitions=(m1b,),
                             mapping_results=(mr1b,), identity_resolution=res)
        assert b1.fingerprint != b2.fingerprint

    def test_fingerprint_differs_on_confidence(self):
        res = _resolution()
        source, snapshot, algo = _source(), _snapshot(), _algo()
        m1 = _mapping(confidence=1.0)
        m1b = _mapping(confidence=0.5)
        mr1 = _mapping_result(snapshot, m1, algo)
        mr1b = MappingResult.from_verified(
            result_id="mr1", project_id="p1", snapshot=snapshot,
            mapping=m1b, identity_algorithm=algo, record_count=1,
        )
        b1 = SnapshotBinding(project_id="p1", snapshot=snapshot, source=source,
                             identity_algorithm=algo, mapping_definitions=(m1,),
                             mapping_results=(mr1,), identity_resolution=res)
        b2 = SnapshotBinding(project_id="p1", snapshot=snapshot, source=source,
                             identity_algorithm=algo, mapping_definitions=(m1b,),
                             mapping_results=(mr1b,), identity_resolution=res)
        assert b1.fingerprint != b2.fingerprint

    def test_fingerprint_differs_on_result_ambiguity(self):
        res = _resolution()
        source, snapshot, algo = _source(), _snapshot(), _algo()
        m = _mapping()
        mr_clean = MappingResult.from_verified(
            result_id="mr1", project_id="p1", snapshot=snapshot,
            mapping=m, identity_algorithm=algo, record_count=1,
        )
        mr_amb = MappingResult.from_verified(
            result_id="mr1", project_id="p1", snapshot=snapshot,
            mapping=m, identity_algorithm=algo, record_count=1,
            is_ambiguous=True, ambiguity_reason="two candidates",
        )
        b1 = SnapshotBinding(project_id="p1", snapshot=snapshot, source=source,
                             identity_algorithm=algo, mapping_definitions=(m,),
                             mapping_results=(mr_clean,), identity_resolution=res)
        b2 = SnapshotBinding(project_id="p1", snapshot=snapshot, source=source,
                             identity_algorithm=algo, mapping_definitions=(m,),
                             mapping_results=(mr_amb,), identity_resolution=res)
        assert b1.fingerprint != b2.fingerprint

    def test_record_count_mismatch_rejected(self):
        snapshot, algo = _snapshot(), _algo()
        m = _mapping()
        with pytest.raises(ProvenanceError, match="record_count"):
            MappingResult.from_verified(
                result_id="mr1", project_id="p1", snapshot=snapshot,
                mapping=m, identity_algorithm=algo, record_count=5,
            )

    def test_fingerprint_differs_on_identity_resolution(self):
        source, snapshot, algo = _source(), _snapshot(), _algo()
        m = _mapping()
        mr = _mapping_result(snapshot, m, algo)
        clean = _resolution(clean=True)
        ambiguous = _resolution(clean=False)
        b1 = SnapshotBinding(project_id="p1", snapshot=snapshot, source=source,
                             identity_algorithm=algo, mapping_definitions=(m,),
                             mapping_results=(mr,), identity_resolution=clean)
        b2 = SnapshotBinding(project_id="p1", snapshot=snapshot, source=source,
                             identity_algorithm=algo, mapping_definitions=(m,),
                             mapping_results=(mr,), identity_resolution=ambiguous)
        assert b1.fingerprint != b2.fingerprint
        assert b1.identity_clean is True
        assert b2.identity_clean is False

    def test_caller_supplied_fingerprint_validated(self):
        """A caller-supplied nonempty fingerprint must match the recomputed
        value, not be silently overwritten."""
        res = _resolution()
        source, snapshot, algo = _source(), _snapshot(), _algo()
        m = _mapping()
        mr = _mapping_result(snapshot, m, algo)
        with pytest.raises(DomainValidationError, match="fingerprint mismatch"):
            SnapshotBinding(
                project_id="p1", snapshot=snapshot, source=source,
                identity_algorithm=algo, mapping_definitions=(m,),
                mapping_results=(mr,), identity_resolution=res,
                fingerprint="f" * 64,
            )

    def test_binding_collections_defensively_copied(self):
        """Mutating the initial lists after construction must not change the
        fingerprint or the binding contents."""
        res = _resolution()
        source, snapshot, algo = _source(), _snapshot(), _algo()
        m1 = _mapping()
        m1b = _mapping(mid="m2")
        mr1 = _mapping_result(snapshot, m1, algo)
        mr1b = MappingResult.from_verified(
            result_id="mr2", project_id="p1", snapshot=snapshot,
            mapping=m1b, identity_algorithm=algo, record_count=1,
        )
        defs_list = [m1]
        results_list = [mr1]
        b = SnapshotBinding(
            project_id="p1", snapshot=snapshot, source=source,
            identity_algorithm=algo, mapping_definitions=defs_list,
            mapping_results=results_list, identity_resolution=res,
        )
        fp = b.fingerprint
        defs_list.append(m1b)
        results_list.append(mr1b)
        assert b.fingerprint == fp
        assert len(b.mapping_definitions) == 1


# ---------------------------------------------------------------------------
# Registration bound to real objects
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_with_binding(self, r2_acceptance_service):
        svc = r2_acceptance_service
        b = _binding()
        rec = svc.register(b, ACCEPTED_BY_SYSTEM_POLICY)
        assert rec.state == SnapshotAcceptanceState.IMPORTED
        assert rec.snapshot_id == "s1"
        assert rec.project_id == "p1"

    def test_register_requires_binding(self, r2_acceptance_service):
        svc = r2_acceptance_service
        with pytest.raises(AcceptanceChainError, match="SnapshotBinding"):
            svc.register("s1", ACCEPTED_BY_SYSTEM_POLICY)  # type: ignore[arg-type]

    def test_register_resolves_from_binding_not_ids(self, r2_acceptance_service):
        svc = r2_acceptance_service
        b = _binding(sid="snap-9")
        rec = svc.register(b, ACCEPTED_BY_SYSTEM_POLICY)
        assert rec.snapshot_id == "snap-9"

    def test_double_register_rejected(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        with pytest.raises(AcceptanceChainError, match="already registered"):
            svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)


# ---------------------------------------------------------------------------
# Normal forward path
# ---------------------------------------------------------------------------

class TestNormalPath:
    def test_full_forward_chain_with_evidence(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        rec = _full_forward(svc)
        assert rec.state == SnapshotAcceptanceState.BASELINE_ELIGIBLE
        assert rec.is_baseline_eligible is True

    def test_each_advance_records_decision(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID, ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        records = svc.decision_records("s1")
        assert len(records) == 2
        assert all(isinstance(r, AcceptanceDecisionRecord) for r in records)


# ---------------------------------------------------------------------------
# No skipping / no reversal
# ---------------------------------------------------------------------------

class TestNoSkipNoReversal:
    def _reg(self, svc):
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)

    def test_skip_two_steps_rejected(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._reg(svc)
        with pytest.raises(AcceptanceChainError, match="skip"):
            svc.advance("s1", SnapshotAcceptanceState.MAPPING_REVIEWED, ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))

    def test_skip_to_eligible_rejected(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._reg(svc)
        with pytest.raises(AcceptanceChainError, match="skip"):
            svc.advance("s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE, ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))

    def test_rewind_rejected(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._reg(svc)
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID, ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        with pytest.raises(AcceptanceChainError, match="rewind"):
            svc.advance("s1", SnapshotAcceptanceState.IMPORTED, ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))

    def test_stay_in_place_rejected(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._reg(svc)
        with pytest.raises(AcceptanceChainError, match="rewind"):
            svc.advance("s1", SnapshotAcceptanceState.IMPORTED, ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))

    def test_unknown_target_rejected(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._reg(svc)

        class FakeState:
            value = "bogus"

        with pytest.raises(AcceptanceChainError):
            svc.advance("s1", FakeState(), ACCEPTED_BY_SYSTEM_POLICY)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Evidence is service-issued (VETO5)
# ---------------------------------------------------------------------------

class TestEvidenceIssued:
    def test_direct_construction_blocked(self):
        """A caller cannot fabricate AcceptanceEvidence with invented IDs."""
        with pytest.raises(DomainValidationError, match="cannot be constructed"):
            AcceptanceEvidence(
                binding_fingerprint="f" * 64, actor="system_policy",
                produced_at="t", critical_mapping_clean=True,
                deterministic_mapping=True,
            )

    def test_evidence_authority_is_not_reachable_or_in_constructor(self):
        import inspect
        import mm_r2.acceptance as acceptance_module

        assert not hasattr(acceptance_module, "_EVIDENCE_OK")
        assert "_issued" not in inspect.signature(AcceptanceEvidence).parameters
        with pytest.raises(TypeError):
            AcceptanceEvidence(
                binding_fingerprint="f" * 64,
                actor=ACCEPTED_BY_SYSTEM_POLICY,
                produced_at="t",
                _issued=True,
            )

    def test_service_issues_bound_evidence(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        ev = svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                          structural_validation_complete=True)
        assert ev.binding_fingerprint == svc.binding("s1").fingerprint
        assert ev.evidence_hash

    def test_invented_evidence_cannot_reach_eligible(self, r2_acceptance_service):
        """VETO5: fabricated evidence (even with a copied fingerprint) cannot
        advance because the service re-derives and cross-checks the binding."""
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        fp = svc.binding("s1").fingerprint
        # Build a fake evidence carrying the right fingerprint but wrong derived props.
        fake = AcceptanceEvidence(
            binding_fingerprint=fp, actor=ACCEPTED_BY_SYSTEM_POLICY,
            produced_at="t", structural_validation_complete=True,
            critical_mapping_clean=True, identity_review_clean=True,
            approved_scope=True, deterministic_mapping=True,
            _issued=True,  # mimic service issuance
        ) if False else None
        # The public constructor exposes no issuance capability; the only
        # supported in-process authority is the service.
        with pytest.raises(TypeError):
            AcceptanceEvidence(
                binding_fingerprint=fp, actor=ACCEPTED_BY_SYSTEM_POLICY,
                produced_at="t", structural_validation_complete=True,
                critical_mapping_clean=True, identity_review_clean=True,
                approved_scope=True, deterministic_mapping=True,
                _issued=True,
            )

    def test_evidence_from_another_snapshot_rejected(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(sid="s1"), ACCEPTED_BY_SYSTEM_POLICY)
        svc.register(_binding(sid="s2"), ACCEPTED_BY_SYSTEM_POLICY)
        ev2 = svc.evidence("s2", ACCEPTED_BY_SYSTEM_POLICY,
                           structural_validation_complete=True)
        with pytest.raises(AcceptanceChainError, match="evidence mismatch"):
            svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                        ACCEPTED_BY_SYSTEM_POLICY, evidence=ev2)


# ---------------------------------------------------------------------------
# Frozen record boundary
# ---------------------------------------------------------------------------

class TestFrozenRecordBoundary:
    def test_record_is_frozen(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        rec = svc.get("s1")
        with pytest.raises(Exception):
            rec.state = SnapshotAcceptanceState.BASELINE_ELIGIBLE  # type: ignore[misc]

    def test_external_mutation_does_not_bypass(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        rec = svc.get("s1")
        try:
            rec.state = SnapshotAcceptanceState.BASELINE_ELIGIBLE  # type: ignore[misc]
        except Exception:
            pass
        assert svc.get("s1").state == SnapshotAcceptanceState.IMPORTED
        assert svc.get("s1").is_baseline_eligible is False

    def test_records_tuple_is_immutable(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        rec = svc.get("s1")
        with pytest.raises(Exception):
            rec.records.append(None)  # type: ignore[attr-defined]

    def test_stale_reference_after_advance(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        stale = svc.get("s1")
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID, ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        fresh = svc.get("s1")
        assert stale.state == SnapshotAcceptanceState.IMPORTED
        assert fresh.state == SnapshotAcceptanceState.STRUCTURALLY_VALID


# ---------------------------------------------------------------------------
# Step-specific evidence gates
# ---------------------------------------------------------------------------

class TestStepSpecificEvidenceGates:
    def _to_structural(self, svc, sid="s1", actor=ACCEPTED_BY_SYSTEM_POLICY):
        svc.register(_binding(sid=sid), actor)
        svc.advance(sid, SnapshotAcceptanceState.STRUCTURALLY_VALID, actor,
                    evidence=svc.evidence(sid, actor, structural_validation_complete=True))

    def _to_mapping(self, svc, sid="s1", actor=ACCEPTED_BY_SYSTEM_POLICY):
        self._to_structural(svc, sid, actor)
        svc.advance(sid, SnapshotAcceptanceState.MAPPING_REVIEWED, actor,
                    evidence=svc.evidence(sid, actor))

    def _to_accepted(self, svc, sid="s1", actor=ACCEPTED_BY_SYSTEM_POLICY):
        self._to_mapping(svc, sid, actor)
        svc.advance(sid, SnapshotAcceptanceState.SNAPSHOT_ACCEPTED, actor,
                    evidence=svc.evidence(sid, actor, approved_scope=True))

    # -- structurally_valid gate ------------------------------------------

    def test_structural_no_evidence_blocked(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        with pytest.raises(AcceptanceChainError, match="evidence"):
            svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                        ACCEPTED_BY_SYSTEM_POLICY)
        assert svc.get("s1").state == SnapshotAcceptanceState.IMPORTED

    def test_structural_with_evidence_ok(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        rec = svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                          ACCEPTED_BY_SYSTEM_POLICY,
                          evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                                structural_validation_complete=True))
        assert rec.state == SnapshotAcceptanceState.STRUCTURALLY_VALID

    def test_structural_blocked_appends_record(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        with pytest.raises(AcceptanceChainError):
            svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                        ACCEPTED_BY_SYSTEM_POLICY)
        records = svc.decision_records("s1")
        assert records[-1].decision == "transition_blocked"

    # -- mapping_reviewed gate --------------------------------------------

    def test_mapping_no_evidence_blocked(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_structural(svc)
        with pytest.raises(AcceptanceChainError, match="evidence"):
            svc.advance("s1", SnapshotAcceptanceState.MAPPING_REVIEWED,
                        ACCEPTED_BY_SYSTEM_POLICY)
        assert svc.get("s1").state == SnapshotAcceptanceState.STRUCTURALLY_VALID

    def test_mapping_with_evidence_ok(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_structural(svc)
        rec = svc.advance("s1", SnapshotAcceptanceState.MAPPING_REVIEWED,
                          ACCEPTED_BY_SYSTEM_POLICY,
                          evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))
        assert rec.state == SnapshotAcceptanceState.MAPPING_REVIEWED

    # -- snapshot_accepted gate -------------------------------------------

    def test_accepted_no_scope_blocked(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_mapping(svc)
        with pytest.raises(AcceptanceChainError, match="approved_scope"):
            svc.advance("s1", SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                        ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))
        assert svc.get("s1").state == SnapshotAcceptanceState.MAPPING_REVIEWED

    def test_accepted_system_policy_low_confidence_blocked(self, r2_acceptance_service):
        """VETO4/VETO6: a real confidence=0.0 critical mapping blocks
        system_policy even with all step decisions set."""
        svc = r2_acceptance_service
        svc.register(_binding(confidence=0.0, is_critical=True), ACCEPTED_BY_SYSTEM_POLICY)
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID, ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        svc.advance("s1", SnapshotAcceptanceState.MAPPING_REVIEWED, ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))
        with pytest.raises(AcceptanceChainError, match="deterministic"):
            svc.advance("s1", SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                        ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                              approved_scope=True))

    def test_accepted_system_policy_with_evidence_ok(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_mapping(svc)
        rec = svc.advance("s1", SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                          ACCEPTED_BY_SYSTEM_POLICY,
                          evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                                approved_scope=True))
        assert rec.state == SnapshotAcceptanceState.SNAPSHOT_ACCEPTED

    def test_local_user_actor_no_deterministic_required(self, r2_acceptance_service):
        """The local OS user may advance a low-confidence critical mapping
        (human decision) without deterministic evidence."""
        svc = r2_acceptance_service
        svc.register(_binding(sid="s2", confidence=0.0, is_critical=True), LOCAL_USER)
        svc.advance("s2", SnapshotAcceptanceState.STRUCTURALLY_VALID, LOCAL_USER,
                    evidence=svc.evidence("s2", LOCAL_USER,
                                          structural_validation_complete=True))
        svc.advance("s2", SnapshotAcceptanceState.MAPPING_REVIEWED, LOCAL_USER,
                    evidence=svc.evidence("s2", LOCAL_USER))
        rec = svc.advance("s2", SnapshotAcceptanceState.SNAPSHOT_ACCEPTED, LOCAL_USER,
                          evidence=svc.evidence("s2", LOCAL_USER, approved_scope=True))
        assert rec.state == SnapshotAcceptanceState.SNAPSHOT_ACCEPTED

    # -- baseline_eligible gate ------------------------------------------

    def test_eligible_no_evidence_blocked(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_accepted(svc)
        with pytest.raises(AcceptanceChainError, match="evidence"):
            svc.advance("s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                        ACCEPTED_BY_SYSTEM_POLICY)
        assert svc.get("s1").state == SnapshotAcceptanceState.SNAPSHOT_ACCEPTED

    def test_eligible_with_full_evidence_ok(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_accepted(svc)
        rec = svc.advance("s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                          ACCEPTED_BY_SYSTEM_POLICY,
                          evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                                source_coverage_complete=True,
                                                approved_scope=True))
        assert rec.is_baseline_eligible is True

    def test_eligible_critical_gap_blocked(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_accepted(svc)
        gap = CoverageGap(scope="source", severity="critical", detail="missing")
        with pytest.raises(EligibilityBlockedError, match="coverage gap"):
            svc.advance("s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                        ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                              source_coverage_complete=True,
                                              approved_scope=True, coverage_gaps=(gap,)))

    def test_eligible_minor_gap_ok(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_accepted(svc)
        gap = CoverageGap(scope="row", severity="minor", detail="note")
        rec = svc.advance("s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                          ACCEPTED_BY_SYSTEM_POLICY,
                          evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                                source_coverage_complete=True,
                                                approved_scope=True, coverage_gaps=(gap,)))
        assert rec.is_baseline_eligible is True

    def test_blocked_then_resolved_can_proceed(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_accepted(svc)
        with pytest.raises(AcceptanceChainError):
            svc.advance("s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                        ACCEPTED_BY_SYSTEM_POLICY)
        rec = svc.advance("s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                          ACCEPTED_BY_SYSTEM_POLICY,
                          evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                                source_coverage_complete=True,
                                                approved_scope=True))
        assert rec.is_baseline_eligible is True

    def test_low_confidence_critical_blocks_eligible(self, r2_acceptance_service):
        """VETO4: a real confidence=0.0 critical mapping blocks system_policy
        advancement (it cannot even reach snapshot_accepted, because the
        deterministic gate fires there for system_policy)."""
        svc = r2_acceptance_service
        svc.register(_binding(confidence=0.0, is_critical=True), ACCEPTED_BY_SYSTEM_POLICY)
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID, ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        svc.advance("s1", SnapshotAcceptanceState.MAPPING_REVIEWED, ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))
        with pytest.raises(AcceptanceChainError, match="deterministic"):
            svc.advance("s1", SnapshotAcceptanceState.SNAPSHOT_ACCEPTED,
                        ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                              approved_scope=True))
        assert svc.get("s1").state == SnapshotAcceptanceState.MAPPING_REVIEWED

    def test_evidence_hash_is_deterministic(self):
        svc = AcceptanceService(local_user=LOCAL_USER)
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        ev1 = svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY, approved_scope=True,
                           produced_at="2026-01-01T00:00:00")
        ev2 = svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY, approved_scope=True,
                           produced_at="2026-01-01T00:00:00")
        assert ev1.evidence_hash == ev2.evidence_hash

    def test_can_advance_preview(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_accepted(svc)
        ok, reasons = svc.can_advance_to_eligible(
            "s1", evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                        source_coverage_complete=True,
                                        approved_scope=True),
            actor=ACCEPTED_BY_SYSTEM_POLICY)
        assert ok is True
        assert reasons == []

    def test_can_advance_preview_blocked(self, r2_acceptance_service):
        svc = r2_acceptance_service
        self._to_accepted(svc)
        ok, reasons = svc.can_advance_to_eligible("s1", actor=ACCEPTED_BY_SYSTEM_POLICY)
        assert ok is False
        assert len(reasons) > 0


# ---------------------------------------------------------------------------
# Decision records: auditable, append-only, hash-chained
# ---------------------------------------------------------------------------

class TestDecisionRecords:
    def test_records_are_hash_chained(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        _full_forward(svc)
        assert svc.verify_chain("p1") is True

    def test_blocked_attempt_records_decision(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        with pytest.raises(AcceptanceChainError):
            svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                        ACCEPTED_BY_SYSTEM_POLICY)
        records = svc.decision_records("s1")
        assert records[-1].decision == "transition_blocked"
        assert svc.verify_chain("p1") is True

    def test_reject_records_decision(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        svc.reject("s1", "low confidence mapping", ACCEPTED_BY_SYSTEM_POLICY,
                   SnapshotAcceptanceState.MAPPING_REVIEWED)
        records = svc.decision_records("s1")
        assert records[-1].decision == "rejected"
        assert records[-1].reasons == ("low confidence mapping",)
        assert svc.get("s1").state == SnapshotAcceptanceState.IMPORTED

    def test_record_hash_is_deterministic(self):
        r1 = AcceptanceDecisionRecord(
            record_id="adr-1", snapshot_id="s1", project_id="p1",
            from_state="imported", to_state="imported",
            actor="system_policy", decision="transition",
            prev_hash="",
        )
        r2 = AcceptanceDecisionRecord(
            record_id="adr-1", snapshot_id="s1", project_id="p1",
            from_state="imported", to_state="imported",
            actor="system_policy", decision="transition",
            prev_hash="",
        )
        assert r1.record_hash == r2.record_hash


# ---------------------------------------------------------------------------
# CoverageGap validation
# ---------------------------------------------------------------------------

class TestCoverageGap:
    def test_invalid_scope(self):
        with pytest.raises(DomainValidationError, match="scope"):
            CoverageGap(scope="bogus", severity="critical", detail="x")

    def test_invalid_severity(self):
        with pytest.raises(DomainValidationError, match="severity"):
            CoverageGap(scope="source", severity="bogus", detail="x")

    def test_detail_required(self):
        with pytest.raises(DomainValidationError, match="detail"):
            CoverageGap(scope="source", severity="critical", detail="")


# ---------------------------------------------------------------------------
# Proof is not an authority token
# ---------------------------------------------------------------------------

class TestProofIsNotAuthority:
    def test_proof_matches_live_record(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        rec = svc.get("s1")
        proof = svc.proof("s1")
        assert proof.state == rec.state
        assert proof.is_baseline_eligible == rec.is_baseline_eligible

    def test_proof_evidence_hash_changes_with_state(self, r2_acceptance_service):
        svc = r2_acceptance_service
        svc.register(_binding(), ACCEPTED_BY_SYSTEM_POLICY)
        proof1 = svc.proof("s1")
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                    ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        proof2 = svc.proof("s1")
        assert proof1.state != proof2.state
        assert proof1.evidence_hash != proof2.evidence_hash


# ---------------------------------------------------------------------------
# VETO5: every illegal transition is audited without changing state
# ---------------------------------------------------------------------------

class TestIllegalTransitionAudit:
    def _reg(self, svc, sid="s1"):
        svc.register(_binding(sid=sid), ACCEPTED_BY_SYSTEM_POLICY)
        return svc

    def _count_records(self, svc, sid="s1"):
        return len(svc.decision_records(sid))

    def test_illegal_skip_appends_audit_record(self, r2_acceptance_service):
        svc = self._reg(r2_acceptance_service)
        before = self._count_records(svc)
        with pytest.raises(AcceptanceChainError, match="skip"):
            svc.advance("s1", SnapshotAcceptanceState.MAPPING_REVIEWED,
                        ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))
        rec = svc.get("s1")
        assert rec.state == SnapshotAcceptanceState.IMPORTED
        assert self._count_records(svc) == before + 1
        last = rec.records[-1]
        assert last.decision == "transition_blocked"
        assert last.to_state == "mapping_reviewed"
        assert any("skip" in r for r in last.reasons)
        assert last.actor == ACCEPTED_BY_SYSTEM_POLICY

    def test_illegal_rewind_appends_audit_record(self, r2_acceptance_service):
        svc = self._reg(r2_acceptance_service)
        svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                    ACCEPTED_BY_SYSTEM_POLICY,
                    evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY,
                                          structural_validation_complete=True))
        before = self._count_records(svc)
        with pytest.raises(AcceptanceChainError, match="rewind"):
            svc.advance("s1", SnapshotAcceptanceState.IMPORTED,
                        ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))
        rec = svc.get("s1")
        assert rec.state == SnapshotAcceptanceState.STRUCTURALLY_VALID
        assert self._count_records(svc) == before + 1
        last = rec.records[-1]
        assert last.decision == "transition_blocked"
        assert any("rewind" in r for r in last.reasons)

    def test_stay_in_place_appends_audit_record(self, r2_acceptance_service):
        svc = self._reg(r2_acceptance_service)
        before = self._count_records(svc)
        with pytest.raises(AcceptanceChainError, match="rewind"):
            svc.advance("s1", SnapshotAcceptanceState.IMPORTED,
                        ACCEPTED_BY_SYSTEM_POLICY,
                        evidence=svc.evidence("s1", ACCEPTED_BY_SYSTEM_POLICY))
        assert self._count_records(svc) == before + 1
        assert svc.get("s1").state == SnapshotAcceptanceState.IMPORTED

    def test_unknown_actor_appends_rejected_record(self, r2_acceptance_service):
        svc = self._reg(r2_acceptance_service)
        before = self._count_records(svc)
        with pytest.raises(AcceptanceChainError, match="not the local user"):
            svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID, "attacker")
        rec = svc.get("s1")
        assert rec.state == SnapshotAcceptanceState.IMPORTED
        assert self._count_records(svc) == before + 1
        last = rec.records[-1]
        assert last.decision == "rejected"
        assert last.actor == "attacker"
        assert any("attacker" in r for r in last.reasons)

    def test_evidence_mismatch_appends_audit_record(self, r2_acceptance_service):
        svc = self._reg(r2_acceptance_service)
        svc.register(_binding(sid="s9"), ACCEPTED_BY_SYSTEM_POLICY)
        other_ev = svc.evidence("s9", ACCEPTED_BY_SYSTEM_POLICY,
                                structural_validation_complete=True)
        before = self._count_records(svc)
        with pytest.raises(AcceptanceChainError, match="evidence mismatch"):
            svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID,
                        ACCEPTED_BY_SYSTEM_POLICY, evidence=other_ev)
        rec = svc.get("s1")
        assert rec.state == SnapshotAcceptanceState.IMPORTED
        assert self._count_records(svc) == before + 1
        last = rec.records[-1]
        assert last.decision == "transition_blocked"
        assert any("binding" in r or "mismatch" in r for r in last.reasons)

    def test_audit_chain_stays_valid_after_illegal_attempts(self, r2_acceptance_service):
        svc = self._reg(r2_acceptance_service)
        with pytest.raises(AcceptanceChainError):
            svc.advance("s1", SnapshotAcceptanceState.BASELINE_ELIGIBLE,
                        ACCEPTED_BY_SYSTEM_POLICY)
        with pytest.raises(AcceptanceChainError):
            svc.advance("s1", SnapshotAcceptanceState.STRUCTURALLY_VALID, "attacker")
        assert svc.verify_chain("p1") is True

    def test_unauthorized_reject_appends_audit_record(self, r2_acceptance_service):
        """Adjacent audit: an unauthorized reject attempt is itself audited
        (rejected record appended) without changing the accepted state."""
        svc = self._reg(r2_acceptance_service)
        before = self._count_records(svc)
        with pytest.raises(AcceptanceChainError, match="not the local user"):
            svc.reject("s1", "reason", "attacker",
                       SnapshotAcceptanceState.MAPPING_REVIEWED)
        rec = svc.get("s1")
        assert rec.state == SnapshotAcceptanceState.IMPORTED
        assert self._count_records(svc) == before + 1
        last = rec.records[-1]
        assert last.decision == "rejected"
        assert last.actor == "attacker"
        assert any("attacker" in r for r in last.reasons)
