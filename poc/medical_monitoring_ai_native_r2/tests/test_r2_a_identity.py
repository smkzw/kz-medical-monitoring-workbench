"""Batch A -- identity: record/risk identity, ambiguity, determinism,
project-scoping, deterministic IDs, lineage-bound merge/split."""

from __future__ import annotations

import pytest

from mm_r2.domain import IdentityAlgorithm
from mm_r2.identity import (
    AmbiguousIdentity,
    DomainValidationError,
    IdentityResolution,
    RecordIdentity,
    ResolvedRiskIdentity,
    RiskIdentity,
    make_record_identity,
    make_risk_identity,
)


@pytest.fixture
def algo():
    return IdentityAlgorithm(algorithm_id="alg-1", name="record-id", version="1")


# ---------------------------------------------------------------------------
# Record identity
# ---------------------------------------------------------------------------

class TestRecordIdentity:
    def test_same_keys_same_project_same_algorithm_same_digest(self, algo):
        r1 = make_record_identity("p1", algo, {"subject": "S01", "seq": 1})
        r2 = make_record_identity("p1", algo, {"seq": 1, "subject": "S01"})
        assert r1.digest == r2.digest

    def test_different_keys_different_digest(self, algo):
        r1 = make_record_identity("p1", algo, {"subject": "S01", "seq": 1})
        r2 = make_record_identity("p1", algo, {"subject": "S01", "seq": 2})
        assert r1.digest != r2.digest

    def test_different_algorithm_different_digest(self, algo):
        algo2 = IdentityAlgorithm(
            algorithm_id="alg-2", name="record-id", version="2",
        )
        r1 = make_record_identity("p1", algo, {"subject": "S01"})
        r2 = make_record_identity("p1", algo2, {"subject": "S01"})
        assert r1.digest != r2.digest
        assert r1.algorithm_digest != r2.algorithm_digest

    # -- Blocker 2 regressions --------------------------------------------

    def test_cross_project_different_digest(self, algo):
        """Same key fields under same algorithm but different project must differ."""
        r1 = make_record_identity("p1", algo, {"subject": "S01"})
        r2 = make_record_identity("p2", algo, {"subject": "S01"})
        assert r1.digest != r2.digest

    def test_deterministic_record_id(self, algo):
        """Repeated factory calls produce the same stable record_id."""
        r1 = make_record_identity("p1", algo, {"subject": "S01", "seq": 1})
        r2 = make_record_identity("p1", algo, {"subject": "S01", "seq": 1})
        assert r1.record_id == r2.record_id

    def test_record_id_derived_from_digest(self, algo):
        r1 = make_record_identity("p1", algo, {"subject": "S01"})
        assert r1.record_id == f"rec-{r1.digest}"

    def test_declared_digest_mismatch_rejected(self, algo):
        # Direct construction is blocked (verified token not reachable by a
        # caller), so a fabricated digest cannot be blessed.
        with pytest.raises(DomainValidationError, match="verified algorithm"):
            RecordIdentity(
                record_id="r", project_id="p",
                algorithm_digest=algo.digest,
                key_fields=(("subject", "S01"),),
                digest="bogus",
            )

    def test_empty_algorithm_digest_rejected(self):
        with pytest.raises(DomainValidationError, match="algorithm_digest"):
            RecordIdentity(
                record_id="r", project_id="p",
                algorithm_digest="",
                key_fields=(("x", 1),),
            )


# ---------------------------------------------------------------------------
# Ambiguity
# ---------------------------------------------------------------------------

class TestAmbiguity:
    _H1 = "a" * 64
    _H2 = "b" * 64

    def test_multi_requires_two_candidates(self, algo):
        with pytest.raises(DomainValidationError, match="multi"):
            AmbiguousIdentity(
                kind="multi", project_id="p",
                algorithm_digest=algo.digest,
                candidate_digests=(self._H1,),
                reason="x",
            )

    def test_multi_with_two_candidates_ok(self, algo):
        amb = AmbiguousIdentity(
            kind="multi", project_id="p",
            algorithm_digest=algo.digest,
            candidate_digests=(self._H1, self._H2),
            reason="two candidates",
        )
        assert amb.kind == "multi"
        assert amb.candidate_digests == (self._H1, self._H2)

    def test_candidate_digest_must_be_hex(self, algo):
        with pytest.raises(DomainValidationError, match="candidate_digests"):
            AmbiguousIdentity(
                kind="multi", project_id="p",
                algorithm_digest=algo.digest,
                candidate_digests=("d1", "d2"),
                reason="x",
            )

    def test_candidate_digests_canonicalized(self, algo):
        """VETO: candidate digests are deduplicated and sorted."""
        amb = AmbiguousIdentity(
            kind="multi", project_id="p",
            algorithm_digest=algo.digest,
            candidate_digests=(self._H2, self._H1, self._H2),
            reason="x",
        )
        assert amb.candidate_digests == (self._H1, self._H2)

    def test_none_kind_ok(self, algo):
        amb = AmbiguousIdentity(
            kind="none", project_id="p",
            algorithm_digest=algo.digest,
            reason="unresolvable",
        )
        assert amb.kind == "none"

    def test_reason_required(self, algo):
        with pytest.raises(DomainValidationError, match="reason"):
            AmbiguousIdentity(
                kind="none", project_id="p",
                algorithm_digest=algo.digest,
            )


class TestIdentityResolution:
    def test_clean_resolution(self, algo):
        r1 = make_record_identity("p1", algo, {"subject": "S01"})
        res = IdentityResolution(algorithm=algo, resolved=(r1,))
        assert res.is_clean is True
        assert res.algorithm_digest == algo.digest

    def test_ambiguous_resolution_not_clean(self, algo):
        amb = AmbiguousIdentity(
            kind="multi", project_id="p1",
            algorithm_digest=algo.digest,
            candidate_digests=("a" * 64, "b" * 64),
            reason="two candidates",
        )
        res = IdentityResolution(algorithm=algo, ambiguities=(amb,))
        assert res.is_clean is False

    def test_resolution_input_list_mutation_inert(self, algo):
        """VETO: passing a list for resolved/ambiguities must not allow
        post-construction mutation to flip is_clean."""
        r1 = make_record_identity("p1", algo, {"subject": "S01"})
        resolved_list = [r1]
        res = IdentityResolution(algorithm=algo, resolved=resolved_list)
        assert res.is_clean is True
        resolved_list.append(make_record_identity("p1", algo, {"subject": "S02"}))
        assert res.is_clean is True
        assert len(res.resolved) == 1

    def test_resolution_algorithm_mismatch_rejected(self, algo):
        other = IdentityAlgorithm(algorithm_id="alg-2", name="record-id", version="2")
        r_other = make_record_identity("p1", other, {"subject": "S01"})
        with pytest.raises(DomainValidationError, match="algorithm"):
            IdentityResolution(algorithm=algo, resolved=(r_other,))

    def test_resolution_project_mix_rejected(self, algo):
        r1 = make_record_identity("p1", algo, {"subject": "S01"})
        r2 = make_record_identity("p2", algo, {"subject": "S01"})
        with pytest.raises(DomainValidationError, match="projects"):
            IdentityResolution(algorithm=algo, resolved=(r1, r2))


# ---------------------------------------------------------------------------
# Risk identity
# ---------------------------------------------------------------------------

class TestRiskIdentity:
    def test_same_dimensions_same_digest(self):
        r1 = make_risk_identity("p1", "S01", "ae", scope=("week1",), classifier="serious")
        r2 = make_risk_identity("p1", "S01", "ae", scope=("week1",), classifier="serious")
        assert r1.digest == r2.digest

    def test_different_domain_different_digest(self):
        r1 = make_risk_identity("p1", "S01", "ae")
        r2 = make_risk_identity("p1", "S01", "mh")
        assert r1.digest != r2.digest

    # -- Blocker 2 regressions --------------------------------------------

    def test_deterministic_risk_identity_id(self):
        """Repeated factory calls produce the same stable risk_identity_id."""
        r1 = make_risk_identity("p1", "S01", "ae", classifier="x")
        r2 = make_risk_identity("p1", "S01", "ae", classifier="x")
        assert r1.risk_identity_id == r2.risk_identity_id

    def test_cross_project_different_digest(self):
        r1 = make_risk_identity("p1", "S01", "ae")
        r2 = make_risk_identity("p2", "S01", "ae")
        assert r1.digest != r2.digest

    def test_merge_creates_derived_identity(self):
        parent1 = make_risk_identity("p1", "S01", "ae")
        parent2 = make_risk_identity("p1", "S01", "ae", classifier="alt")
        merged = make_risk_identity(
            "p1", "S01", "ae", derived_from=[parent1.risk_identity_id, parent2.risk_identity_id],
        )
        assert merged.is_derived is True
        assert parent1.risk_identity_id in merged.derived_from
        assert parent2.risk_identity_id in merged.derived_from
        assert parent1.derived_from == ()

    def test_merge_does_not_collapse_onto_parent(self):
        """A merged identity must not have the same digest as a non-merged one
        even with identical dimensions, because derived_from is in the digest."""
        base = make_risk_identity("p1", "S01", "ae", classifier="x")
        parent = make_risk_identity("p1", "S01", "ae", classifier="y")
        merged = make_risk_identity(
            "p1", "S01", "ae", classifier="x",
            derived_from=[parent.risk_identity_id],
        )
        assert merged.digest != base.digest
        assert merged.risk_identity_id != base.risk_identity_id

    def test_resolved_ambiguous_requires_reason(self):
        rid = make_risk_identity("p1", "S01", "ae")
        with pytest.raises(DomainValidationError, match="ambiguity_reason"):
            ResolvedRiskIdentity(identity=rid, is_ambiguous=True)

    # -- Gap 2 + VETO3: verified construction + direct-constructor gate -------

    def test_direct_constructor_arbitrary_id_rejected(self, algo):
        """A fabricated digest-only RecordIdentity is unavailable to public
        callers (VETO3)."""
        with pytest.raises(DomainValidationError, match="verified algorithm"):
            RecordIdentity(
                record_id="arbitrary-id",
                project_id="p1",
                algorithm_digest=algo.digest,
                key_fields=(("subject", "S01"),),
            )

    def test_direct_constructor_arbitrary_id_rejected_verified(self, algo):
        """A caller cannot bless an arbitrary id by passing _verified=True
        (the sentinel is a private object, not a boolean)."""
        derived = make_record_identity("p1", algo, {"subject": "S01"})
        with pytest.raises(DomainValidationError, match="verified algorithm"):
            RecordIdentity(
                record_id="arbitrary-id",
                project_id="p1",
                algorithm_digest=algo.digest,
                key_fields=(("subject", "S01"),),
                _verified=True,
            )

    def test_direct_constructor_correct_id_rejected_too(self, algo):
        """Even a correct id cannot be constructed directly: the verified
        token is not reachable through the public constructor."""
        derived = make_record_identity("p1", algo, {"subject": "S01"})
        with pytest.raises(DomainValidationError, match="verified algorithm"):
            RecordIdentity(
                record_id=derived.record_id,
                project_id="p1",
                algorithm_digest=algo.digest,
                key_fields=(("subject", "S01"),),
            )

    def test_fabricated_algorithm_digest_blocked(self, algo):
        """A fabricated algorithm digest cannot create an authoritative identity."""
        with pytest.raises(DomainValidationError, match="verified algorithm"):
            RecordIdentity(
                record_id="", project_id="p1",
                algorithm_digest="f" * 64, key_fields=(("x", 1),),
            )

    def test_risk_direct_constructor_arbitrary_id_rejected(self):
        with pytest.raises(DomainValidationError, match="verified construction"):
            RiskIdentity(
                risk_identity_id="bogus",
                project_id="p1", subject_ref="S01", domain="ae",
            )

    def test_risk_direct_constructor_arbitrary_id_rejected_verified(self):
        """A caller cannot bless an arbitrary risk id with _verified=True."""
        with pytest.raises(DomainValidationError, match="verified construction"):
            RiskIdentity(
                risk_identity_id="bogus",
                project_id="p1", subject_ref="S01", domain="ae",
                _verified=True,
            )

    def test_risk_parent_order_canonical(self):
        """Different parent ordering in derived_from must produce the same identity."""
        p1 = make_risk_identity("p1", "S01", "ae")
        p2 = make_risk_identity("p1", "S01", "mh")
        m1 = make_risk_identity("p1", "S01", "ae",
                                derived_from=[p1.risk_identity_id, p2.risk_identity_id])
        m2 = make_risk_identity("p1", "S01", "ae",
                                derived_from=[p2.risk_identity_id, p1.risk_identity_id])
        assert m1.digest == m2.digest
        assert m1.risk_identity_id == m2.risk_identity_id

    def test_risk_scope_order_canonical(self):
        """Different scope ordering must produce the same identity."""
        r1 = make_risk_identity("p1", "S01", "ae", scope=["b", "a"])
        r2 = make_risk_identity("p1", "S01", "ae", scope=["a", "b"])
        assert r1.digest == r2.digest

    def test_fabricated_64hex_algorithm_digest_blocked(self):
        """VETO3: an arbitrary 64-hex string is not enough to create an
        authoritative record identity (must bind a real IdentityAlgorithm)."""
        with pytest.raises(DomainValidationError, match="verified algorithm"):
            RecordIdentity(
                record_id="", project_id="p1",
                algorithm_digest="a" * 64, key_fields=(("subject", "S01"),),
            )

    def test_key_fields_nested_immutability(self, algo):
        """VETO2: nested values inside key_fields cannot be mutated after
        construction."""
        key = {"subject": "S01", "meta": {"lst": [1, 2]}}
        rid = make_record_identity("p1", algo, dict(key))
        digest = rid.digest
        key["meta"]["lst"].append(99)  # mutate original caller input
        assert rid.digest == digest
        # reachable nested structure is deep-frozen
        for _, v in rid.key_fields:
            if isinstance(v, dict):
                with pytest.raises(TypeError):
                    v["new"] = 1
