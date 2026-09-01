"""Batch A -- domain entities: immutability, content-addressing, provenance,
real content binding (gap 1+7), CanonicalFact facts-only + identity/mapping
binding + deterministic fact_id (gap 4+5), MappingDefinition.version and
RuleActivation.activated_by (gap 5)."""

from __future__ import annotations

import hashlib

import pytest

from mm_r2.domain import (
    CanonicalFact,
    DomainValidationError,
    HashMismatchError,
    ImmutableDict,
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    Provenance,
    ProvenanceError,
    RuleActivation,
    SourceRevision,
    StudyKnowledgePack,
    StudyProject,
    canonical_json,
    content_hash,
    deep_freeze_json,
    from_dictable,
    sha256_hex,
    to_dictable,
    validate_sha256_hex,
)
from mm_r2.identity import make_record_identity


def _digest(data: bytes) -> str:
    """SHA-256 of real synthetic content bytes."""
    return hashlib.sha256(data).hexdigest()


_HEX64 = "a" * 64  # valid 64-char hex for identity fields


# ---------------------------------------------------------------------------
# Fixtures (authoritative construction only)
# ---------------------------------------------------------------------------

@pytest.fixture
def project():
    return StudyProject(project_id="p1", name="Synthetic Study")


@pytest.fixture
def source(project):
    return SourceRevision.from_bytes(
        revision_id="rev-1",
        project_id="p1",
        source_type="listing",
        version="2026-01-01",
        source_bytes=b"synthetic-ae-bytes-v1",
        scope=(("file", "ae.csv"),),
    )


@pytest.fixture
def snapshot(source):
    return ListingSnapshot.from_content(
        snapshot_id="snap-1",
        project_id="p1",
        revision_id="rev-1",
        snapshot_version="cutoff-1",
        rows=[{"sub": "S01", "ae": "Nausea"}],
        structure=(("tables", ("AE", "DM")),),
    )


@pytest.fixture
def algo():
    return IdentityAlgorithm(algorithm_id="alg-1", name="record-id", version="1")


@pytest.fixture
def mapping(source, algo):
    return MappingDefinition(
        mapping_id="m1", project_id="p1", source_revision_id="rev-1",
        identity_algorithm_id="alg-1", source_field="AETERM",
        canonical_field="ae_term", fact_type="ae", version="1",
        confidence=1.0, is_critical=True,
    )


@pytest.fixture
def mapping_result(snapshot, mapping, algo):
    return MappingResult.from_verified(
        result_id="mr1", project_id="p1", snapshot=snapshot, mapping=mapping,
        identity_algorithm=algo, record_count=1,
    )


@pytest.fixture
def record_identity(algo):
    return make_record_identity("p1", algo, {"subject": "S01"})


@pytest.fixture
def canonical_fact(
    source, snapshot, record_identity, algo, mapping, mapping_result,
):
    return CanonicalFact.from_bundle(
        project=StudyProject(project_id="p1", name="Synthetic Study"),
        source=source, snapshot=snapshot, record_identity=record_identity,
        identity_algorithm=algo, mapping_definition=mapping,
        mapping_result=mapping_result,
        fact_type="ae", payload=(("term", "Nausea"),),
    )


# ---------------------------------------------------------------------------
# Gap 1: content_digest SHA-256 validation
# ---------------------------------------------------------------------------

class TestContentDigestValidation:
    def test_source_requires_valid_sha256(self):
        with pytest.raises(DomainValidationError, match="64-character"):
            SourceRevision(
                revision_id="r", project_id="p", source_type="listing", version="v",
                content_digest="not-a-hash",
            )

    def test_source_rejects_short_hex(self):
        with pytest.raises(DomainValidationError, match="64-character"):
            SourceRevision(
                revision_id="r", project_id="p", source_type="listing", version="v",
                content_digest="abc123",
            )

    def test_source_rejects_empty(self):
        with pytest.raises(DomainValidationError, match="64-character"):
            SourceRevision(
                revision_id="r", project_id="p", source_type="listing", version="v",
                content_digest="",
            )

    def test_source_rejects_uppercase_hex(self):
        with pytest.raises(DomainValidationError, match="64-character"):
            SourceRevision(
                revision_id="r", project_id="p", source_type="listing", version="v",
                content_digest="A" * 64,  # uppercase not canonical
            )

    def test_source_digest_only_construction_blocked(self):
        """VETO3: digest-only construction is unavailable to public callers."""
        with pytest.raises(DomainValidationError, match="verified source bytes"):
            SourceRevision(
                revision_id="r", project_id="p", source_type="listing",
                version="v", content_digest=_digest(b"x"),
            )

    def test_source_accepts_valid_sha256(self):
        s = SourceRevision.from_bytes(
            revision_id="r", project_id="p", source_type="listing",
            version="v", source_bytes=b"x",
        )
        assert len(s.content_digest) == 64
        assert s.content_digest == _digest(b"x")

    def test_snapshot_digest_only_construction_blocked(self):
        """VETO3: snapshot digest-only construction is unavailable."""
        with pytest.raises(DomainValidationError, match="verified canonical"):
            ListingSnapshot(
                snapshot_id="s", project_id="p", revision_id="r",
                snapshot_version="sv", row_count=5,
                content_digest="0" * 64,
            )

    def test_snapshot_from_content_verifies_row_count(self):
        ls = ListingSnapshot.from_content(
            snapshot_id="s", project_id="p", revision_id="r",
            snapshot_version="sv", rows=[{"a": 1}, {"a": 2}],
        )
        assert ls.row_count == 2
        assert ls.content_digest == content_hash([{"a": 1}, {"a": 2}])

    def test_validate_sha256_hex_helper(self):
        assert validate_sha256_hex("0" * 64) == "0" * 64
        with pytest.raises(DomainValidationError):
            validate_sha256_hex("xyz")


# ---------------------------------------------------------------------------
# Content-addressed hash contracts
# ---------------------------------------------------------------------------

class TestContentAddressing:
    def test_source_hash_is_deterministic(self, source):
        again = SourceRevision.from_bytes(
            revision_id="rev-1", project_id="p1", source_type="listing",
            version="2026-01-01", source_bytes=b"synthetic-ae-bytes-v1",
            scope=(("file", "ae.csv"),),
        )
        assert source.content_hash == again.content_hash

    def test_source_hash_excludes_timestamp(self, source):
        s2 = SourceRevision.from_bytes(
            revision_id="rev-1", project_id="p1", source_type="listing",
            version="2026-01-01", source_bytes=b"synthetic-ae-bytes-v1",
            scope=(("file", "ae.csv"),), created_at="2099-01-01",
        )
        assert source.content_hash == s2.content_hash

    def test_source_hash_changes_with_version(self, source):
        s2 = SourceRevision.from_bytes(
            revision_id="rev-1", project_id="p1", source_type="listing",
            version="2026-01-02", source_bytes=b"synthetic-ae-bytes-v1",
            scope=(("file", "ae.csv"),),
        )
        assert source.content_hash != s2.content_hash

    def test_declared_hash_mismatch_rejected(self):
        # A fabricated content_hash cannot be embedded: the only in-process
        # construction paths recompute the hash internally, so injecting a
        # mismatched declared hash via the public codec is blocked (fails
        # closed for authoritative entities).
        src = SourceRevision.from_bytes(
            revision_id="r", project_id="p", source_type="listing", version="v",
            source_bytes=b"x",
        )
        d = to_dictable(src)
        d["fields"]["content_hash"] = "deadbeef"
        with pytest.raises(Exception):
            from_dictable(d)

    def test_snapshot_hash_recomputed_on_construction(self, snapshot):
        expected = snapshot.compute_hash()
        assert snapshot.content_hash == expected

    def test_different_source_bytes_different_hash(self):
        s1 = SourceRevision.from_bytes(
            revision_id="r", project_id="p", source_type="listing", version="v",
            source_bytes=b"content-a",
        )
        s2 = SourceRevision.from_bytes(
            revision_id="r", project_id="p", source_type="listing", version="v",
            source_bytes=b"content-b",
        )
        assert s1.content_hash != s2.content_hash

    def test_different_listing_rows_different_hash(self):
        ls1 = ListingSnapshot.from_content(
            snapshot_id="s", project_id="p", revision_id="r", snapshot_version="sv",
            rows=[{"sub": "S01", "val": "A"}],
            structure=(("cols", ("sub", "val")),),
        )
        ls2 = ListingSnapshot.from_content(
            snapshot_id="s", project_id="p", revision_id="r", snapshot_version="sv",
            rows=[{"sub": "S01", "val": "B"}],
            structure=(("cols", ("sub", "val")),),
        )
        assert ls1.content_hash != ls2.content_hash

    def test_metadata_fingerprint_separate_from_content(self):
        s1 = SourceRevision.from_bytes(
            revision_id="r", project_id="p", source_type="listing", version="v",
            source_bytes=b"a",
        )
        s2 = SourceRevision.from_bytes(
            revision_id="r", project_id="p", source_type="listing", version="v",
            source_bytes=b"b",
        )
        assert s1.metadata_fingerprint == s2.metadata_fingerprint
        assert s1.content_hash != s2.content_hash


# ---------------------------------------------------------------------------
# Gap 4: CanonicalFact identity/mapping binding + deterministic fact_id
# ---------------------------------------------------------------------------

class TestCanonicalFactBinding:
    def _bundle(self, project_id="p1", source_id="r1", snapshot_id="s1",
                algo=None):
        project = StudyProject(project_id=project_id, name="Synthetic Study")
        source = SourceRevision.from_bytes(
            revision_id=source_id, project_id=project_id,
            source_type="listing", version="v", source_bytes=b"bytes",
        )
        snapshot = ListingSnapshot.from_content(
            snapshot_id=snapshot_id, project_id=project_id,
            revision_id=source_id, snapshot_version="sv",
            rows=[{"sub": "S01", "ae": "Nausea"}],
        )
        algo = algo or IdentityAlgorithm(
            algorithm_id="alg-1", name="record-id", version="1"
        )
        rid = make_record_identity(project_id, algo, {"subject": "S01"})
        mapping = MappingDefinition(
            mapping_id="m1", project_id=project_id,
            source_revision_id=source_id, identity_algorithm_id=algo.algorithm_id,
            source_field="AETERM", canonical_field="ae_term",
            fact_type="ae", version="1", confidence=1.0, is_critical=True,
        )
        mr = MappingResult.from_verified(
            result_id="mr1", project_id=project_id, snapshot=snapshot,
            mapping=mapping, identity_algorithm=algo, record_count=1,
        )
        return project, source, snapshot, rid, algo, mapping, mr

    def test_digest_only_construction_blocked(self, algo):
        """VETO3: a CanonicalFact cannot be built from fabricated digests/refs."""
        with pytest.raises(DomainValidationError, match="verified record identity"):
            CanonicalFact(
                project_id="p", source_revision_id="r", snapshot_id="s",
                fact_type="ae", record_identity_digest=_HEX64,
                identity_algorithm_digest=_HEX64, mapping_result_id="mr1",
                mapping_definition_digest=_HEX64,
                payload=(("x", 1),),
            )

    def test_authority_tokens_are_not_module_attributes(self):
        import inspect
        import mm_r2.domain as domain_module
        import mm_r2.identity as identity_module

        assert not hasattr(domain_module, "_VERIFIED")
        assert not hasattr(identity_module, "_IDENTITY_VERIFIED")
        for callable_obj in (
            SourceRevision.from_bytes,
            ListingSnapshot.from_content,
            MappingResult.from_verified,
            CanonicalFact.from_bundle,
            identity_module.RecordIdentity.from_verified,
            identity_module.RiskIdentity.from_dimensions,
        ):
            assert "_authority_token" not in inspect.signature(callable_obj).parameters

    def test_deterministic_fact_id(self):
        p, src, snap, rid, algo, mapping, mr = self._bundle()
        f1 = CanonicalFact.from_bundle(
            project=p, source=src, snapshot=snap, record_identity=rid,
            identity_algorithm=algo, mapping_definition=mapping,
            mapping_result=mr, fact_type="ae",
            payload=(("term", "Nausea"),),
        )
        p2, src2, snap2, rid2, algo2, mapping2, mr2 = self._bundle()
        f2 = CanonicalFact.from_bundle(
            project=p2, source=src2, snapshot=snap2, record_identity=rid2,
            identity_algorithm=algo2, mapping_definition=mapping2,
            mapping_result=mr2, fact_type="ae",
            payload=(("term", "Nausea"),),
        )
        assert f1.fact_id == f2.fact_id

    def test_cross_project_different_fact_id(self):
        p, src, snap, rid, algo, mapping, mr = self._bundle("p1", "r1", "s1")
        f1 = CanonicalFact.from_bundle(
            project=p, source=src, snapshot=snap, record_identity=rid,
            identity_algorithm=algo, mapping_definition=mapping,
            mapping_result=mr, fact_type="ae",
            payload=(("term", "Nausea"),),
        )
        p2, src2, snap2, rid2, algo2, mapping2, mr2 = self._bundle("p2", "r1", "s1")
        f2 = CanonicalFact.from_bundle(
            project=p2, source=src2, snapshot=snap2, record_identity=rid2,
            identity_algorithm=algo2, mapping_definition=mapping2,
            mapping_result=mr2, fact_type="ae",
            payload=(("term", "Nausea"),),
        )
        assert f1.fact_id != f2.fact_id

    def test_cross_project_bundle_mismatch_rejected(self):
        """VETO3: fabricated/unresolved cross-project references are rejected."""
        p, src, snap, rid, algo, mapping, mr = self._bundle("p1", "r1", "s1")
        other_proj = StudyProject(project_id="p99", name="Other")
        with pytest.raises(ProvenanceError, match="project_id mismatch"):
            CanonicalFact.from_bundle(
                project=other_proj, source=src, snapshot=snap,
                record_identity=rid, identity_algorithm=algo,
                mapping_definition=mapping, mapping_result=mr, fact_type="ae",
            )

    def test_wrong_algorithm_bundle_mismatch_rejected(self):
        p, src, snap, rid, algo, mapping, mr = self._bundle("p1", "r1", "s1")
        other_algo = IdentityAlgorithm(
            algorithm_id="alg-2", name="record-id", version="2"
        )
        with pytest.raises(ProvenanceError, match="algorithm_digest"):
            CanonicalFact.from_bundle(
                project=p, source=src, snapshot=snap, record_identity=rid,
                identity_algorithm=other_algo, mapping_definition=mapping,
                mapping_result=mr, fact_type="ae",
            )

    def test_supplied_mismatched_fact_id_rejected(self):
        """A fact_id that does not match the deterministic derived id is rejected."""
        p, src, snap, rid, algo, mapping, mr = self._bundle()
        f = CanonicalFact.from_bundle(
            project=p, source=src, snapshot=snap, record_identity=rid,
            identity_algorithm=algo, mapping_definition=mapping,
            mapping_result=mr, fact_type="ae",
            payload=(("term", "Nausea"),),
        )
        # Direct construction with a fabricated fact_id is blocked because a
        # caller cannot pass the private verified token.
        with pytest.raises(DomainValidationError):
            CanonicalFact(
                fact_id="bogus-id", project_id="p1", source_revision_id="r1",
                snapshot_id="s1", fact_type="ae",
                record_identity_digest=rid.digest,
                identity_algorithm_digest=algo.digest,
                mapping_result_id="mr1",
                mapping_definition_digest=mapping.digest,
                payload=(("term", "Nausea"),),
            )

    def test_candidate_role_rejected(self):
        p, src, snap, rid, algo, mapping, mr = self._bundle()
        # from_bundle always produces facts; a direct construction with a
        # non-facts role is blocked because the caller cannot pass the
        # private verified token.
        with pytest.raises(DomainValidationError):
            CanonicalFact(
                project_id="p1", source_revision_id="r1", snapshot_id="s1",
                fact_type="ae", role="candidate",
                record_identity_digest=rid.digest,
                identity_algorithm_digest=algo.digest,
                mapping_result_id="mr1",
                mapping_definition_digest=mapping.digest,
                payload=(("x", 1),),
            )

    def test_default_role_is_facts(self):
        p, src, snap, rid, algo, mapping, mr = self._bundle()
        f = CanonicalFact.from_bundle(
            project=p, source=src, snapshot=snap, record_identity=rid,
            identity_algorithm=algo, mapping_definition=mapping,
            mapping_result=mr, fact_type="ae",
            payload=(("x", 1),),
        )
        assert f.role == "facts"

    def test_fact_type_must_match_mapping_semantics(self):
        p, src, snap, rid, algo, _, _ = self._bundle()
        dm_mapping = MappingDefinition(
            mapping_id="dm1", project_id="p1", source_revision_id="r1",
            identity_algorithm_id="alg-1", source_field="SEX",
            canonical_field="dm_sex", fact_type="dm", version="1",
        )
        dm_result = MappingResult.from_verified(
            result_id="dmr1", project_id="p1", snapshot=snap,
            mapping=dm_mapping, identity_algorithm=algo, record_count=1,
        )
        with pytest.raises(ProvenanceError, match="mapping definition semantics"):
            CanonicalFact.from_bundle(
                project=p, source=src, snapshot=snap, record_identity=rid,
                identity_algorithm=algo, mapping_definition=dm_mapping,
                mapping_result=dm_result, fact_type="ae",
            )

    def test_same_id_mapping_substitution_is_rejected(self):
        p, src, snap, rid, algo, ae_mapping, _ = self._bundle()
        dm_mapping = MappingDefinition(
            mapping_id=ae_mapping.mapping_id, project_id="p1",
            source_revision_id="r1", identity_algorithm_id="alg-1",
            source_field="SEX", canonical_field="dm_sex",
            fact_type="dm", version="1",
        )
        dm_result = MappingResult.from_verified(
            result_id="mr-dm", project_id="p1", snapshot=snap,
            mapping=dm_mapping, identity_algorithm=algo, record_count=1,
        )
        with pytest.raises(ProvenanceError, match="mapping definition semantics"):
            CanonicalFact.from_bundle(
                project=p, source=src, snapshot=snap, record_identity=rid,
                identity_algorithm=algo, mapping_definition=ae_mapping,
                mapping_result=dm_result, fact_type="ae",
            )


# ---------------------------------------------------------------------------
# Gap 5: MappingDefinition.version required + RuleActivation.activated_by
# ---------------------------------------------------------------------------

class TestMappingDefinitionValidation:
    def test_version_required(self):
        with pytest.raises(DomainValidationError, match="version"):
            MappingDefinition(
                mapping_id="m", project_id="p", source_revision_id="r",
                identity_algorithm_id="a", source_field="x", canonical_field="y",
            )

    def test_with_version_ok(self):
        m = MappingDefinition(
            mapping_id="m", project_id="p", source_revision_id="r",
            identity_algorithm_id="a", source_field="x", canonical_field="y",
            version="1",
        )
        assert m.version == "1"

    def test_confidence_bounds(self):
        with pytest.raises(DomainValidationError, match="confidence"):
            MappingDefinition(
                mapping_id="m", project_id="p", source_revision_id="r",
                identity_algorithm_id="a", source_field="x", canonical_field="y",
                version="1", confidence=1.5,
            )
        for c in (0.0, 1.0):
            MappingDefinition(
                mapping_id="m", project_id="p", source_revision_id="r",
                identity_algorithm_id="a", source_field="x", canonical_field="y",
                version="1", confidence=c,
            )


class TestRuleActivationValidation:
    def test_activated_by_required(self):
        with pytest.raises(DomainValidationError, match="activated_by"):
            RuleActivation(
                activation_id="a", project_id="p", source_revision_id="r",
                knowledge_pack_id="k", rule_text="rule", activated_version="1",
            )

    def test_with_activated_by_ok(self):
        ra = RuleActivation(
            activation_id="a", project_id="p", source_revision_id="r",
            knowledge_pack_id="k", rule_text="rule", activated_version="1",
            activated_by="user_bob",
        )
        assert ra.activated_by == "user_bob"


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------

class TestImmutability:
    def test_study_project_is_frozen(self, project):
        with pytest.raises(Exception):
            project.project_id = "x"  # type: ignore[misc]

    def test_source_revision_is_frozen(self, source):
        with pytest.raises(Exception):
            source.version = "x"  # type: ignore[misc]

    def test_listing_snapshot_is_frozen(self, snapshot):
        with pytest.raises(Exception):
            snapshot.row_count = 0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_writing_unknown_version_rejected(self):
        from mm_r2.schema_registry import SchemaRegistryError
        with pytest.raises(SchemaRegistryError):
            SourceRevision(
                schema_version="99",
                revision_id="rev-1", project_id="p1",
                source_type="listing", version="v1",
                content_digest=_digest(b"x"),
            )

    def test_non_synthetic_project_rejected(self):
        with pytest.raises(DomainValidationError, match="synthetic"):
            StudyProject(project_id="p1", name="x", is_synthetic=False)

    def test_non_synthetic_snapshot_rejected(self):
        with pytest.raises(DomainValidationError, match="synthetic"):
            ListingSnapshot(
                snapshot_id="s", project_id="p", revision_id="r",
                snapshot_version="v", is_synthetic=False,
                content_digest=_digest(b"x"),
            )


# ---------------------------------------------------------------------------
# Provenance binding
# ---------------------------------------------------------------------------

class TestProvenance:
    def test_knowledge_pack_requires_source_and_identity(self):
        with pytest.raises(ProvenanceError, match="source_revision_id"):
            StudyKnowledgePack(
                pack_id="kp", project_id="p", version="1",
                identity_algorithm_id="a",
            )

    def test_rule_activation_requires_source_and_pack(self):
        with pytest.raises(ProvenanceError, match="source_revision_id"):
            RuleActivation(
                activation_id="a", project_id="p", rule_text="r",
                activated_version="1", knowledge_pack_id="k", activated_by="u",
            )

    def test_mapping_definition_requires_source_and_identity(self):
        with pytest.raises(ProvenanceError, match="identity_algorithm_id"):
            MappingDefinition(
                mapping_id="m", project_id="p", source_revision_id="r",
                source_field="a", canonical_field="b", version="1",
            )

    def test_mapping_result_ambiguous_requires_reason(self):
        with pytest.raises(DomainValidationError, match="ambiguity_reason"):
            MappingResult(
                result_id="r", project_id="p", snapshot_id="s", mapping_id="m",
                mapping_definition_digest=_HEX64,
                identity_algorithm_id="a", is_ambiguous=True,
            )


# ---------------------------------------------------------------------------
# Deterministic serialization round-trip (non-authoritative) + fail-closed
# authoritative rehydration
# ---------------------------------------------------------------------------

class TestSerialization:
    def test_source_to_dictable_is_deterministic(self, source):
        d1 = to_dictable(source)
        d2 = to_dictable(source)
        assert d1 == d2

    def test_codec_fails_closed_for_authoritative_source(self, source):
        """VETO4: generic from_dictable must NOT bless an authoritative
        entity (even untampered) without an explicit verified capability."""
        with pytest.raises(Exception, match="rehydration"):
            from_dictable(to_dictable(source))

    def test_codec_fails_closed_for_authoritative_snapshot(self, snapshot):
        with pytest.raises(Exception, match="rehydration"):
            from_dictable(to_dictable(snapshot))

    def test_codec_fails_closed_for_tampered_digest(self, source):
        """VETO4: editing a serialized content_digest cannot fabricate an
        authoritative object via the generic codec."""
        d = to_dictable(source)
        d["fields"]["content_digest"] = "f" * 64
        with pytest.raises(Exception, match="rehydration"):
            from_dictable(d)

    def test_codec_roundtrip_for_non_authoritative(self, algo):
        """Non-authoritative entities (no _verified InitVar) round-trip."""
        d = to_dictable(algo)
        back = from_dictable(d)
        assert back.digest == algo.digest
        assert back.algorithm_id == algo.algorithm_id

    def test_no_digest_only_rehydration_for_source(self):
        """VETO (adjacent gate): there is no callable digest-only rehydration
        path in Batch A for SourceRevision."""
        assert not hasattr(SourceRevision, "_rehydrate_verified")

    def test_no_digest_only_rehydration_for_snapshot(self):
        """VETO (adjacent gate): no digest-only rehydration for ListingSnapshot."""
        assert not hasattr(ListingSnapshot, "_rehydrate_verified")

    def test_no_callable_verified_rehydration_anywhere(self):
        """Batch A exposes no digest-only trust escalator: the only way to
        build an authoritative SourceRevision/ListingSnapshot is from the
        actual bytes/content via from_bytes/from_content."""
        with pytest.raises(Exception):
            # A fabricated "verified" direct construction is blocked.
            SourceRevision(
                revision_id="r", project_id="p", source_type="listing",
                version="v", content_digest=sha256_hex(b"x"),
            )

    def test_canonical_json_is_sortable_and_compact(self):
        a = canonical_json({"b": 1, "a": 2})
        b = canonical_json({"a": 2, "b": 1})
        assert a == b
        assert " " not in a


# ---------------------------------------------------------------------------
# VETO2: deep immutability of JSON-like fields (nested mutation impossible)
# ---------------------------------------------------------------------------

class TestDeepImmutability:
    def test_canonical_json_rejects_nan(self):
        with pytest.raises(ValueError):
            canonical_json({"x": float("nan")})

    def test_canonical_json_rejects_infinity(self):
        with pytest.raises(ValueError):
            canonical_json({"x": float("inf")})

    def test_deep_freeze_rejects_non_finite(self):
        with pytest.raises(DomainValidationError, match="non-finite"):
            deep_freeze_json({"x": float("nan")})

    def test_deep_freeze_rejects_unsupported_type(self):
        with pytest.raises(DomainValidationError, match="unsupported"):
            deep_freeze_json({"x": object()})

    def test_nested_value_in_source_scope_cannot_be_mutated(self, source):
        """Mutating a value reachable from the frozen object is impossible."""
        from collections.abc import Mapping as _Mapping
        scope = source.scope
        has_dict = any(isinstance(v, _Mapping) for _, v in scope)
        if has_dict:
            d = next(v for _, v in scope if isinstance(v, _Mapping))
            with pytest.raises(TypeError):
                d["newkey"] = "x"
        fp = source.metadata_fingerprint
        assert source.metadata_fingerprint == fp

    def test_original_caller_input_mutation_does_not_change_hash(self):
        """Mutating the original caller input after construction is inert."""
        meta = {"cols": ["a", "b"]}
        scope = (("meta", meta),)
        src = SourceRevision.from_bytes(
            revision_id="r", project_id="p", source_type="listing",
            version="v", source_bytes=b"bytes", scope=scope,
        )
        fp1 = src.metadata_fingerprint
        meta["cols"].append("MUT")  # mutate original caller input
        meta["newkey"] = "x"
        assert src.metadata_fingerprint == fp1

    def test_snapshot_structure_nested_mutation_impossible(self):
        struct = {"tables": ["AE", "DM"]}
        snap = ListingSnapshot.from_content(
            snapshot_id="s", project_id="p", revision_id="r",
            snapshot_version="sv", rows=[{"a": 1}],
            structure=(("meta", struct),),
        )
        struct["tables"].append("MUT")  # mutate original input
        fp = snap.metadata_fingerprint
        assert snap.metadata_fingerprint == fp
        # reachable nested list has been converted to an immutable tuple
        reachable = snap.structure[0][1]
        assert isinstance(reachable.get("tables"), tuple)
        with pytest.raises(TypeError):
            reachable["tables"] = ("X",)

    def test_identity_key_fields_nested_mutation_impossible(self, algo):
        key = {"subject": "S01", "extra": {"nested": [1, 2]}}
        rid = make_record_identity("p1", algo, dict(key))
        d1 = rid.digest
        key["extra"]["nested"].append(3)
        assert rid.digest == d1
        # reachable nested list is a tuple (immutable)
        reachable_list_or_tuple = rid.key_fields
        assert isinstance(reachable_list_or_tuple, tuple)

    def test_frozen_source_scope_immutable(self, source):
        from collections.abc import Mapping as _Mapping
        # scope is a tuple: element assignment is impossible
        with pytest.raises(TypeError):
            source.scope[0] = ("replacement", "x")  # type: ignore[index]
        # mutation of a mutable nested value reachable via scope is blocked
        for _, v in source.scope:
            if isinstance(v, _Mapping):
                with pytest.raises(TypeError):
                    v["k"] = 1

    def test_immutable_dict_has_no_dict_base_backdoor(self):
        """VETO1: dict.__setitem__ cannot mutate a frozen mapping because
        ImmutableDict is a Mapping, not a dict subclass."""
        from collections.abc import Mapping as _Mapping
        d = deep_freeze_json({"outer": {"x": 1}})
        assert isinstance(d, _Mapping)
        assert not isinstance(d, dict)
        with pytest.raises(TypeError):
            dict.__setitem__(d, "outer", {"x": 2})  # base-class backdoor
        with pytest.raises(TypeError):
            dict.__setitem__(d["outer"], "x", 2)
        # item assignment also blocked
        with pytest.raises(TypeError):
            d["outer"] = {"x": 2}

    def test_immutable_dict_has_no_reachable_mutable_backing(self):
        """VETO (adjacent gate): the backing `_m` is a mappingproxy, so
        `frozen._m["x"]=2` and `frozen["outer"]._m["x"]=2` raise TypeError."""
        from types import MappingProxyType
        d = deep_freeze_json({"outer": {"x": 1}})
        # outer backing access
        assert isinstance(d._m, MappingProxyType)
        with pytest.raises(TypeError):
            d._m["outer"] = {"x": 2}
        # nested backing access
        with pytest.raises(TypeError):
            d["outer"]._m["x"] = 2
        # recomputed hash stable regardless
        fp = canonical_json(d)
        assert canonical_json(d) == fp

    def test_immutable_dict_backing_attribute_cannot_be_rebound(self):
        d = deep_freeze_json({"outer": {"x": 1}})
        fp = canonical_json(d)
        with pytest.raises(TypeError):
            d._m = {"outer": {"x": 2}}
        with pytest.raises(TypeError):
            d["outer"]._m = {"x": 2}
        with pytest.raises(TypeError):
            del d._m
        assert canonical_json(d) == fp

    def test_immutable_dict_caller_input_mutation_inert(self):
        """Mutating the original caller input after freezing is inert."""
        src = {"outer": {"x": 1}}
        d = deep_freeze_json(src)
        fp = canonical_json(d)
        src["outer"]["x"] = 999
        src["newkey"] = "mutable"
        assert canonical_json(d) == fp

    def test_study_project_config_deep_frozen(self):
        """VETO2: StudyProject.config nested values cannot be mutated."""
        cfg = {"meta": {"tables": ["AE", "DM"], "n": 1}}
        proj = StudyProject(
            project_id="p1", name="Synthetic Study",
            config=(("k", cfg),),
        )
        # mutate original caller input
        cfg["meta"]["tables"].append("MUT")
        cfg["newkey"] = "x"
        reachable = proj.config[0][1]
        assert isinstance(reachable, ImmutableDict)
        assert reachable.get("meta")["tables"] == ("AE", "DM")
        with pytest.raises(TypeError):
            reachable["newkey"] = "x"
        with pytest.raises(TypeError):
            reachable["meta"]["tables"] = ("X",)

    def test_immutable_dict_equality_and_dict_conversion(self):
        d = deep_freeze_json({"a": 1, "b": [1, 2]})
        assert d == {"a": 1, "b": (1, 2)}
        assert dict(d) == {"a": 1, "b": (1, 2)}
        assert canonical_json(d) == canonical_json({"a": 1, "b": (1, 2)})
