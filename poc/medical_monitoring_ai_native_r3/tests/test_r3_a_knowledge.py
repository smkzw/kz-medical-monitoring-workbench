"""R3-A tests: source classification, version/valid-time/scope, Knowledge
Pack, claim authority, and source conflict/resolution contracts.

Proves (deterministically, synthetic-only):
* source revisions are immutable + content-addressed; digest-only construction
  is blocked for public callers;
* valid-time windows and scope facets behave correctly and an unspecified
  scope never silently matches another;
* Knowledge Pack is versioned, four-layered, content-addressed and binds real
  source revisions;
* claim authority derives status from contributions and never silently
  overwrites a conflict;
* source conflicts are surfaced and resolved only via an explicit, auditable
  resolution with no silent "last writer wins";
* no project name / absolute path hardcoding (three heterogeneous listing
  shapes + generic synthetic project ids).
"""

from __future__ import annotations

import hashlib
from typing import Dict

import pytest

from mm_r3.fixtures import (
    SYNTHETIC_PROJECT_IDS,
    make_amendment_revision,
    make_authority,
    make_classification,
    make_claim,
    make_conflict,
    make_conflicting_claims,
    make_ib_revision,
    make_knowledge_pack,
    make_listing_revision,
    make_protocol_revision,
    make_report_revision,
    make_resolution,
    make_resolution_log,
    make_three_heterogeneous_listing_sources,
)
from mm_r3.knowledge import (
    Claim,
    ClaimAuthority,
    ClaimStatus,
    ConflictError,
    ConflictResolution,
    ConflictResolutionLog,
    ConflictType,
    DomainValidationError,
    KnowledgeLayer,
    ResolutionOutcome,
    SourceClassification,
    SourceConflict,
    SourceRevision,
    StudyKnowledgePack,
    SUPPORTED_SOURCE_TYPES,
)
from mm_r3.primitives import content_hash, sha256_hex


# ===========================================================================
# Source revision: immutability, content-addressing, version/valid-time/scope
# ===========================================================================

class TestSourceRevision:
    def test_from_bytes_computes_real_digest(self):
        src = SourceRevision.from_bytes(
            revision_id="rev-1",
            project_id="proj-alpha",
            source_type="protocol",
            version="1.0",
            source_bytes=b"synthetic-bytes",
        )
        assert src.content_digest == hashlib.sha256(b"synthetic-bytes").hexdigest()
        assert src.content_hash  # auto-computed
        assert src.revision_id == "rev-1"

    def test_different_bytes_produce_different_identity(self):
        a = SourceRevision.from_bytes("r1", "p1", "protocol", "1", b"aaa")
        b = SourceRevision.from_bytes("r1", "p1", "protocol", "1", b"bbb")
        assert a.content_digest != b.content_digest
        assert a.content_hash != b.content_hash

    def test_different_version_produces_different_identity(self):
        a = SourceRevision.from_bytes("r1", "p1", "protocol", "1", b"aaa")
        b = SourceRevision.from_bytes("r1", "p1", "protocol", "2", b"aaa")
        assert a.metadata_fingerprint != b.metadata_fingerprint
        assert a.content_hash != b.content_hash

    def test_digest_only_construction_blocked(self):
        with pytest.raises(DomainValidationError, match="verified source bytes"):
            SourceRevision(
                revision_id="r1",
                project_id="p1",
                source_type="protocol",
                version="1",
                content_digest="a" * 64,
            )

    def test_empty_bytes_rejected(self):
        with pytest.raises(DomainValidationError, match="non-empty"):
            SourceRevision.from_bytes("r1", "p1", "protocol", "1", b"")

    def test_invalid_digest_rejected(self):
        with pytest.raises(ValueError, match="64-char lowercase hex"):
            SourceRevision(
                revision_id="r1",
                project_id="p1",
                source_type="protocol",
                version="1",
                content_digest="short",
                _verified=object(),
            )

    def test_unknown_source_type_rejected(self):
        with pytest.raises(DomainValidationError, match="source_type"):
            SourceRevision.from_bytes("r1", "p1", "not_a_type", "1", b"x")

    def test_valid_time_window(self):
        src = SourceRevision.from_bytes(
            "r1", "p1", "protocol", "1", b"x",
            valid_from="2026-01-01",
            valid_until="2026-06-30",
        )
        assert src.is_valid_at("2026-03-15") is True
        assert src.is_valid_at("2025-12-31") is False
        assert src.is_valid_at("2026-07-01") is False

    def test_valid_until_before_valid_from_rejected(self):
        with pytest.raises(DomainValidationError, match="valid_until"):
            SourceRevision.from_bytes(
                "r1", "p1", "protocol", "1", b"x",
                valid_from="2026-06-01",
                valid_until="2026-01-01",
            )

    def test_scope_unspecified_and_overlap(self):
        unspecified = SourceRevision.from_bytes("r1", "p1", "protocol", "1", b"x")
        assert unspecified.scope_unspecified is True

        scoped = SourceRevision.from_bytes(
            "r2", "p1", "protocol", "1", b"y",
            scope=(("domain", "ae"),),
        )
        assert scoped.scope_unspecified is False
        assert scoped.scope_contains("domain", "ae") is True
        assert scoped.scope_contains("domain", "labs") is False

        # unspecified never silently overlaps
        assert unspecified.overlaps_scope(scoped, "domain") is False

        scoped2 = SourceRevision.from_bytes(
            "r3", "p1", "ib", "1", b"z",
            scope=(("domain", "ae"),),
        )
        assert scoped.overlaps_scope(scoped2, "domain") is True

    def test_immutable_fields(self):
        src = SourceRevision.from_bytes(
            "r1", "p1", "protocol", "1", b"x",
            scope=(("domain", "ae"),),
        )
        with pytest.raises(Exception):
            src.revision_id = "mutated"  # type: ignore[misc]
        # scope is frozen deep
        with pytest.raises((TypeError, AttributeError)):
            src.scope[0] = ("domain", "labs")  # type: ignore[index]

    def test_authority_token_is_not_reachable(self):
        # The construction capability is captured by the factory and removed
        # from the module namespace.  A caller cannot bless fabricated bytes
        # by importing a private module attribute.
        from mm_r3 import knowledge as kn
        assert not hasattr(kn, "_VERIFIED")
        digest = hashlib.sha256(b"fabricated").hexdigest()
        with pytest.raises(DomainValidationError):
            SourceRevision(
                revision_id="r1",
                project_id="p1",
                source_type="protocol",
                version="1",
                content_digest=digest,
                content_hash="",
                _verified=object(),
            )

    def test_from_bytes_always_consistent_hash(self):
        # The public factory recomputes content_hash internally; a caller
        # cannot inject a mismatched hash through the public surface.
        src = SourceRevision.from_bytes("r1", "p1", "protocol", "1", b"real")
        recomputed = src.compute_hash()
        assert src.content_hash == recomputed

    def test_all_supported_source_types_accepted(self):
        for st in SUPPORTED_SOURCE_TYPES:
            src = SourceRevision.from_bytes(
                f"rev-{st}", "p1", st, "1", st.encode()
            )
            assert src.source_type == st


# ===========================================================================
# Source classification
# ===========================================================================

class TestSourceClassification:
    def test_classification_binds_revision_and_layer(self, protocol_source):
        cls = make_classification(protocol_source)
        assert cls.revision_id == protocol_source.revision_id
        assert cls.knowledge_layer == KnowledgeLayer.PROJECT_DOCUMENTS
        assert cls.is_project_authoritative is True

    def test_primary_document_must_be_project_layer(self, ib_source):
        with pytest.raises(DomainValidationError, match="primary project document"):
            SourceClassification(
                classification_id="c1",
                revision_id=ib_source.revision_id,
                knowledge_layer="general_medical",
                is_primary_project_document=True,
            )

    def test_default_authority_by_layer(self, ib_source):
        cls = SourceClassification(
            classification_id="c1",
            revision_id=ib_source.revision_id,
            knowledge_layer="drug_mechanism",
        )
        assert cls.authority_level == "reference"
        assert cls.is_project_authoritative is False

    def test_invalid_layer_rejected(self, protocol_source):
        with pytest.raises(DomainValidationError, match="knowledge_layer"):
            SourceClassification(
                classification_id="c1",
                revision_id=protocol_source.revision_id,
                knowledge_layer="not_a_layer",
            )


# ===========================================================================
# Study Knowledge Pack
# ===========================================================================

class TestStudyKnowledgePack:
    def test_pack_is_versioned_and_content_addressed(self, knowledge_pack):
        assert knowledge_pack.version == "1"
        assert knowledge_pack.content_hash
        assert len(knowledge_pack.source_revision_ids) == 2

    def test_pack_layers_accessible(self, knowledge_pack):
        assert knowledge_pack.layer("general_medical") == {"population": "adult patients"}
        assert knowledge_pack.layer("drug_mechanism") == {"mechanism": "JAK inhibitor (synthetic)"}
        assert knowledge_pack.layer("activated_rules") == {"activated_rule_count": 0}
        assert knowledge_pack.layer("nonexistent") is None

    def test_pack_requires_source_binding(self):
        with pytest.raises(Exception, match="source_revision_id"):
            StudyKnowledgePack(
                pack_id="kp1",
                project_id="p1",
                version="1",
            )

    def test_pack_rejects_invalid_layer_key(self):
        src = make_protocol_revision()
        with pytest.raises(DomainValidationError, match="layer key"):
            StudyKnowledgePack(
                pack_id="kp1",
                project_id="proj-alpha",
                version="1",
                source_revision_ids=(src.revision_id,),
                layers=(("bad_layer", {"x": 1}),),
            )

    def test_pack_hash_deterministic(self, protocol_source, ib_source):
        kp1 = make_knowledge_pack(source_revisions=[protocol_source, ib_source])
        kp2 = make_knowledge_pack(source_revisions=[protocol_source, ib_source])
        assert kp1.content_hash == kp2.content_hash

    def test_pack_hash_changes_with_content(self, protocol_source, ib_source):
        kp1 = make_knowledge_pack(
            source_revisions=[protocol_source, ib_source],
            project_layer={"endpoint": "a"},
        )
        kp2 = make_knowledge_pack(
            source_revisions=[protocol_source, ib_source],
            project_layer={"endpoint": "b"},
        )
        assert kp1.content_hash != kp2.content_hash


# ===========================================================================
# Claim authority matrix
# ===========================================================================

class TestClaimAuthority:
    def test_single_supporting_claim_is_supported(self, protocol_source):
        claim = make_claim(
            protocol_source,
            claim_scope="dosing",
            statement="dose is 10mg",
            raw_value="10mg",
        )
        auth = make_authority([claim])
        assert auth.derived_status == ClaimStatus.SUPPORTED

    def test_two_agreeing_claims_are_supported(self, protocol_source, ib_source):
        c1 = make_claim(protocol_source, claim_scope="dosing", statement="a", raw_value="10mg")
        c2 = make_claim(ib_source, claim_scope="dosing", statement="b", raw_value="10mg")
        auth = make_authority([c1, c2])
        assert auth.derived_status == ClaimStatus.SUPPORTED

    def test_conflicting_values_derive_conflicted(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source,
            claim_scope="dosing",
            value_a="10mg",
            value_b="5mg",
        )
        auth = make_authority([c1, c2])
        assert auth.derived_status == ClaimStatus.CONFLICTED

    def test_authority_records_all_contributions(self, protocol_source, ib_source):
        c1 = make_claim(protocol_source, claim_scope="x", statement="a", raw_value=1)
        c2 = make_claim(ib_source, claim_scope="x", statement="b", raw_value=2)
        auth = make_authority([c1, c2])
        assert len(auth.contributions) == 2
        contribs = dict(auth.contributions)
        assert contribs[c1.claim_id]["raw_value"] == 1
        assert contribs[c2.claim_id]["raw_value"] == 2

    def test_classification_enriches_contribution(self, protocol_source, ib_source):
        c1 = make_claim(protocol_source, claim_scope="x", statement="a", raw_value=1)
        c2 = make_claim(ib_source, claim_scope="x", statement="b", raw_value=1)
        cls_map: Dict[str, SourceClassification] = {
            protocol_source.revision_id: make_classification(protocol_source),
            ib_source.revision_id: make_classification(
                ib_source, knowledge_layer="drug_mechanism", is_primary_project_document=False,
            ),
        }
        auth = make_authority([c1, c2], classifications=cls_map)
        contribs = dict(auth.contributions)
        assert contribs[c1.claim_id]["is_primary_project_document"] is True
        assert contribs[c2.claim_id]["authority_level"] == "reference"

    def test_partial_support(self, protocol_source):
        c1 = make_claim(protocol_source, claim_scope="x", statement="a", raw_value=1, status=ClaimStatus.SUPPORTED)
        c2 = make_claim(protocol_source, claim_scope="x", statement="b", raw_value=1, status=ClaimStatus.UNSUPPORTED)
        auth = make_authority([c1, c2])
        assert auth.derived_status == ClaimStatus.PARTIALLY_SUPPORTED

    def test_claims_must_share_scope(self, protocol_source, ib_source):
        c1 = make_claim(protocol_source, claim_scope="x", statement="a", raw_value=1)
        c2 = make_claim(ib_source, claim_scope="y", statement="b", raw_value=1)
        with pytest.raises(DomainValidationError, match="share"):
            make_authority([c1, c2])


# ===========================================================================
# Source conflict + resolution
# ===========================================================================

class TestSourceConflict:
    def test_conflict_requires_two_claims(self, protocol_source):
        c1 = make_claim(protocol_source, claim_scope="x", statement="a", raw_value=1)
        with pytest.raises(DomainValidationError, match="at least two"):
            SourceConflict.between([c1], conflict_type=ConflictType.CONTRADICTION)

    def test_conflict_records_claim_ids(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source, claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        assert len(conflict.claim_ids) == 2
        assert c1.claim_id in conflict.claim_ids
        assert c2.claim_id in conflict.claim_ids

    def test_conflict_claims_must_share_scope(self, protocol_source, ib_source):
        c1 = make_claim(protocol_source, claim_scope="x", statement="a", raw_value=1)
        c2 = make_claim(ib_source, claim_scope="y", statement="b", raw_value=2)
        with pytest.raises(DomainValidationError, match="share"):
            make_conflict([c1, c2])


class TestConflictResolution:
    def test_resolution_names_winner(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source, claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        res = make_resolution(conflict, winning_claim_id=c1.claim_id)
        assert res.outcome == ResolutionOutcome.PROJECT_SOURCE_WINS
        assert res.winning_claim_id == c1.claim_id

    def test_unresolved_must_not_name_winner(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source, claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        with pytest.raises(DomainValidationError, match="must not declare a winner"):
            ConflictResolution(
                resolution_id="r1",
                conflict_id=conflict.conflict_id,
                outcome=ResolutionOutcome.UNRESOLVED,
                winning_claim_id=c1.claim_id,
                resolved_by="local_test_user",
            )

    def test_machine_resolution_cannot_user_confirm(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source, claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        with pytest.raises(DomainValidationError, match="machine resolution"):
            ConflictResolution(
                resolution_id="r1",
                conflict_id=conflict.conflict_id,
                outcome=ResolutionOutcome.PROJECT_SOURCE_WINS,
                winning_claim_id=c1.claim_id,
                winning_source_revision_id=protocol_source.revision_id,
                resolved_by="local_test_user",
                is_machine_resolution=True,
                user_confirmed=True,
            )

    def test_user_resolution_must_user_confirm(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source, claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        with pytest.raises(DomainValidationError, match="user resolution"):
            ConflictResolution(
                resolution_id="r1",
                conflict_id=conflict.conflict_id,
                outcome=ResolutionOutcome.USER_ADJUDICATED,
                winning_claim_id=c1.claim_id,
                winning_source_revision_id=protocol_source.revision_id,
                resolved_by="local_test_user",
                is_machine_resolution=False,
                user_confirmed=False,
            )


class TestConflictResolutionLog:
    def test_unresolved_conflict_exposed(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source, claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        log = make_resolution_log(conflicts=[conflict])
        assert len(log.unresolved_conflicts()) == 1

    def test_resolved_conflict_not_unresolved(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source, claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        res = make_resolution(conflict, winning_claim_id=c1.claim_id)
        log = make_resolution_log(conflicts=[conflict], resolutions=[res])
        assert len(log.unresolved_conflicts()) == 0

    def test_winner_must_be_conflict_claim(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source, claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        log = ConflictResolutionLog(project_id="proj-alpha")
        log.record_conflict(conflict)
        bogus = ConflictResolution(
            resolution_id="res-bogus",
            conflict_id=conflict.conflict_id,
            outcome=ResolutionOutcome.PROJECT_SOURCE_WINS,
            winning_claim_id="bogus",
            winning_source_revision_id=protocol_source.revision_id,
            resolved_by="local_test_user",
        )
        with pytest.raises(ConflictError, match="winning_claim_id"):
            log.resolve(bogus)

    def test_append_only_history_preserved(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source, claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        res1 = make_resolution(conflict, winning_claim_id=c1.claim_id)
        res2 = make_resolution(
            conflict, winning_claim_id=c2.claim_id,
            outcome=ResolutionOutcome.USER_ADJUDICATED,
            is_machine_resolution=False,
        )
        log = make_resolution_log(conflicts=[conflict], resolutions=[res1, res2])
        assert len(log.resolutions) == 2  # history preserved
        assert log.current_resolution(conflict.conflict_id).resolution_id == res2.resolution_id

    def test_winner_source_must_match_winning_claim(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source,
            claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2])
        log = make_resolution_log(conflicts=[conflict])
        bad = make_resolution(
            conflict,
            winning_claim_id=c1.claim_id,
            winning_source_revision_id=ib_source.revision_id,
        )
        with pytest.raises(ConflictError, match="winning_source_revision_id"):
            log.resolve(bad)

    def test_duplicate_conflict_id_rejected(self, protocol_source, ib_source):
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source,
            claim_scope="dosing", value_a=10, value_b=5,
        )
        conflict = make_conflict([c1, c2], conflict_id="conf-fixed")
        log = make_resolution_log(conflicts=[conflict])
        with pytest.raises(ConflictError, match="duplicate conflict_id"):
            log.record_conflict(conflict)

    def test_cannot_resolve_unknown_conflict(self):
        log = ConflictResolutionLog(project_id="proj-alpha")
        bogus_res = ConflictResolution(
            resolution_id="r1",
            conflict_id="nope",
            outcome=ResolutionOutcome.UNRESOLVED,
            resolved_by="local_test_user",
        )
        with pytest.raises(ConflictError, match="unknown conflict"):
            log.resolve(bogus_res)


# ===========================================================================
# Anti-hardcoding: three heterogeneous listing shapes, generic project ids
# ===========================================================================

class TestAntiHardcoding:
    def test_three_heterogeneous_shapes_distinct(self, three_heterogeneous_sources):
        s1, s2, s3 = three_heterogeneous_sources
        shapes = {s1.scope_get("shape"), s2.scope_get("shape"), s3.scope_get("shape")}
        assert shapes == {"wide_tabular", "long_keyvalue", "multi_table_workbook"}
        # distinct content
        assert len({s1.content_digest, s2.content_digest, s3.content_digest}) == 3
        # distinct revisions
        assert len({s1.revision_id, s2.revision_id, s3.revision_id}) == 3

    def test_no_real_project_name_in_fixtures(self):
        forbidden = ("RUX", "MGK10", "MG-K10", "MY009", "MY008", "芦可替尼")
        import mm_r3.fixtures as fx_mod
        import mm_r3.knowledge as kn_mod
        for mod in (fx_mod, kn_mod):
            src = open(mod.__file__).read()
            for bad in forbidden:
                assert bad not in src, f"forbidden token {bad!r} found in {mod.__file__}"

    def test_synthetic_project_ids_generic(self):
        for pid in SYNTHETIC_PROJECT_IDS:
            assert pid.startswith("proj-")
            assert pid.isascii()


# ===========================================================================
# Authority precedence within scope (project source wins, but explicitly)
# ===========================================================================

class TestAuthorityPrecedence:
    def test_project_source_wins_inside_scope_explicitly(self, protocol_source, ib_source):
        """A project document claim and a reference claim conflict on the same
        scope.  The resolution explicitly picks the project source; the
        conflict is never silently overwritten."""
        c1, c2 = make_conflicting_claims(
            protocol_source, ib_source,
            claim_scope="endpoint",
            value_a="ORR",
            value_b="PFS",
            statement_a="protocol defines ORR",
            statement_b="IB mentions PFS",
        )
        auth = make_authority([c1, c2])
        assert auth.derived_status == ClaimStatus.CONFLICTED
        conflict = make_conflict([c1, c2])
        res = make_resolution(
            conflict,
            winning_claim_id=c1.claim_id,
            outcome=ResolutionOutcome.PROJECT_SOURCE_WINS,
            basis="project source wins within its declared scope",
        )
        assert res.winning_claim_id == c1.claim_id
        # the authority matrix itself still records the conflict
        assert auth.derived_status == ClaimStatus.CONFLICTED

    def test_later_revision_resolution(self):
        v1 = make_protocol_revision(revision_id="rev-proto-v1", version="1.0", content=b"v1")
        v2 = make_amendment_revision(revision_id="rev-proto-v2", version="2.0", content=b"v2")
        c1, c2 = make_conflicting_claims(
            v1, v2, claim_scope="design", value_a="open_label", value_b="double_blind",
        )
        conflict = make_conflict([c1, c2])
        res = make_resolution(
            conflict,
            winning_claim_id=c2.claim_id,
            outcome=ResolutionOutcome.LATER_REVISION_WINS,
            basis="amendment v2 supersedes v1",
        )
        assert res.outcome == ResolutionOutcome.LATER_REVISION_WINS
