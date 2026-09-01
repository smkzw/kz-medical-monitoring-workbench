"""Batch C: verified rehydration adapter tests.

The rehydrator must rebuild authoritative entities ONLY after verifying the
actual stored artifact bytes/hash.  Forged/missing/mismatched bytes fail
closed.  Non-authoritative entities round-trip normally.
"""

import json

import pytest

from helpers_c import (
    make_algo, make_fact, make_mapping, make_mapping_result, make_project,
    make_record_id, make_snapshot, make_source,
)

from mm_r2.artifacts import ArtifactStore
from mm_r2.domain import (
    HashMismatchError, SourceRevision, ListingSnapshot, to_dictable,
    deep_freeze_json, content_hash,
)
from mm_r2.identity import make_record_identity, make_risk_identity
from mm_r2.verification import (
    RehydrationError, Rehydrator, verify_artifact_bytes,
)


# ---------------------------------------------------------------------------
# verify_artifact_bytes
# ---------------------------------------------------------------------------

class TestVerifyArtifactBytes:
    def test_verifies_matching_bytes(self):
        data = b"hello"
        h = __import__("hashlib").sha256(data).hexdigest()
        assert verify_artifact_bytes(data, h) == data

    def test_rejects_none(self):
        h = __import__("hashlib").sha256(b"x").hexdigest()
        with pytest.raises(RehydrationError):
            verify_artifact_bytes(None, h)

    def test_rejects_mismatched_hash(self):
        data = b"hello"
        wrong = __import__("hashlib").sha256(b"other").hexdigest()
        with pytest.raises(HashMismatchError):
            verify_artifact_bytes(data, wrong)

    def test_rejects_non_bytes(self):
        h = __import__("hashlib").sha256(b"x").hexdigest()
        with pytest.raises(RehydrationError):
            verify_artifact_bytes("not-bytes", h)


# ---------------------------------------------------------------------------
# SourceRevision rehydration
# ---------------------------------------------------------------------------

class TestRehydrateSourceRevision:
    def test_round_trips_via_verified_bytes(self, tmp_path):
        store = ArtifactStore(tmp_path / "art")
        rh = Rehydrator(store)
        source = make_source(content=b"my-source")
        data = to_dictable(source)
        # round-trip: pass the raw source bytes
        rh.rehydrate_source_revision(data, source_bytes=b"my-source")

    def test_rebuilds_identical_object(self, tmp_path):
        store = ArtifactStore(tmp_path / "art")
        rh = Rehydrator(store)
        source = make_source(content=b"my-source")
        rebuilt = rh.rehydrate_source_revision(
            to_dictable(source), source_bytes=b"my-source",
        )
        assert rebuilt.content_hash == source.content_hash
        assert rebuilt.content_digest == source.content_digest
        assert rebuilt.revision_id == source.revision_id

    def test_rejects_missing_bytes_without_store(self):
        rh = Rehydrator()
        source = make_source(content=b"my-source")
        with pytest.raises(RehydrationError):
            rh.rehydrate_source_revision(to_dictable(source))

    def test_rejects_mismatched_bytes(self):
        rh = Rehydrator()
        source = make_source(content=b"my-source")
        with pytest.raises(HashMismatchError):
            rh.rehydrate_source_revision(
                to_dictable(source), source_bytes=b"WRONG",
            )


# ---------------------------------------------------------------------------
# ListingSnapshot rehydration
# ---------------------------------------------------------------------------

class TestRehydrateListingSnapshot:
    def test_round_trips_via_rows(self):
        rh = Rehydrator()
        snap = make_snapshot(rows=[{"subject": "S01", "ae": "Nausea"}])
        rebuilt = rh.rehydrate_listing_snapshot(
            to_dictable(snap),
            snapshot_rows=[{"subject": "S01", "ae": "Nausea"}],
        )
        assert rebuilt.content_hash == snap.content_hash
        assert rebuilt.snapshot_id == snap.snapshot_id

    def test_round_trips_via_bytes(self):
        from mm_r2.domain import canonical_json
        rh = Rehydrator()
        snap = make_snapshot(rows=[{"subject": "S01", "ae": "Nausea"}])
        # The snapshot's content_digest is sha256(canonical_json(frozen_rows)).
        from mm_r2.domain import deep_freeze_json
        frozen = deep_freeze_json([{"subject": "S01", "ae": "Nausea"}])
        # to_dictable converts the frozen structure to plain JSON-able.
        plain = [{"subject": "S01", "ae": "Nausea"}]
        snap_bytes = canonical_json(plain).encode("utf-8")
        rebuilt = rh.rehydrate_listing_snapshot(
            to_dictable(snap), snapshot_bytes=snap_bytes,
        )
        assert rebuilt.content_hash == snap.content_hash
    def test_rejects_mismatched_rows(self):
        rh = Rehydrator()
        snap = make_snapshot(rows=[{"subject": "S01", "ae": "Nausea"}])
        with pytest.raises(HashMismatchError):
            rh.rehydrate_listing_snapshot(
                to_dictable(snap),
                snapshot_rows=[{"subject": "S01", "ae": "Vomiting"}],
            )



# ---------------------------------------------------------------------------
# MappingResult / RecordIdentity / RiskIdentity rehydration
# ---------------------------------------------------------------------------

class TestRehydrateMappingResult:
    def test_round_trips_with_verified_objects(self):
        rh = Rehydrator()
        snap = make_snapshot()
        mapping = make_mapping()
        algo = make_algo()
        result = make_mapping_result(snap=snap, mapping=mapping, algo=algo)
        rebuilt = rh.rehydrate_mapping_result(
            to_dictable(result), mapping, snap, algo,
        )
        assert rebuilt.result_id == result.result_id
        assert rebuilt.mapping_definition_digest == mapping.digest

    def test_rejects_wrong_mapping(self):
        rh = Rehydrator()
        snap = make_snapshot()
        mapping = make_mapping()
        algo = make_algo()
        result = make_mapping_result(snap=snap, mapping=mapping, algo=algo)
        # A DIFFERENT mapping (different source_field)
        from mm_r2.domain import MappingDefinition
        other_mapping = MappingDefinition(
            mapping_id="m2", project_id="p1", source_revision_id="rev-1",
            identity_algorithm_id="alg-1", source_field="OTHER",
            canonical_field="other", fact_type="ae", version="1",
            confidence=1.0, is_critical=True,
        )
        with pytest.raises(RehydrationError):
            rh.rehydrate_mapping_result(
                to_dictable(result), other_mapping, snap, algo,
            )


class TestRehydrateRecordIdentity:
    def test_round_trips(self):
        rh = Rehydrator()
        algo = make_algo()
        ri = make_record_identity("p1", algo, {"subject": "S01"})
        rebuilt = rh.rehydrate_record_identity(to_dictable(ri), algo)
        assert rebuilt.digest == ri.digest
        assert rebuilt.record_id == ri.record_id

    def test_rejects_declared_digest_mismatch(self):
        rh = Rehydrator()
        algo = make_algo()
        ri = make_record_identity("p1", algo, {"subject": "S01"})
        data = to_dictable(ri)
        data["fields"]["digest"] = "0" * 64  # fake digest
        with pytest.raises(RehydrationError):
            rh.rehydrate_record_identity(data, algo)


class TestRehydrateRiskIdentity:
    def test_round_trips(self):
        rh = Rehydrator()
        ri = make_risk_identity(
            project_id="p1", subject_ref="S01", domain="ae",
            scope=["subject"], classifier="ae",
        )
        rebuilt = rh.rehydrate_risk_identity(to_dictable(ri))
        assert rebuilt.digest == ri.digest
        assert rebuilt.risk_identity_id == ri.risk_identity_id


# ---------------------------------------------------------------------------
# CanonicalFact rehydration
# ---------------------------------------------------------------------------

class TestRehydrateCanonicalFact:
    def test_round_trips_with_verified_bundle(self):
        rh = Rehydrator()
        fact = make_fact()
        project = make_project()
        source = make_source()
        snap = make_snapshot()
        algo = make_algo()
        mapping = make_mapping()
        result = make_mapping_result(snap=snap, mapping=mapping, algo=algo)
        record = make_record_id()
        rebuilt = rh.rehydrate_canonical_fact(
            to_dictable(fact), project, source, snap, record, algo,
            mapping, result,
        )
        assert rebuilt.fact_id == fact.fact_id
        assert rebuilt.content_hash == fact.content_hash

    @pytest.mark.parametrize("field", ["fact_id", "content_hash"])
    def test_rejects_declared_fact_identity_mismatch(self, field):
        rh = Rehydrator()
        fact = make_fact()
        data = to_dictable(fact)
        data["fields"][field] = "0" * 64
        project = make_project()
        source = make_source()
        snap = make_snapshot()
        algo = make_algo()
        mapping = make_mapping()
        result = make_mapping_result(snap=snap, mapping=mapping, algo=algo)
        record = make_record_id()
        with pytest.raises(RehydrationError):
            rh.rehydrate_canonical_fact(
                data, project, source, snap, record, algo, mapping, result,
            )

    @pytest.mark.parametrize("field", [
        "fact_id", "content_hash", "project_id", "mapping_result_id",
    ])
    def test_rejects_missing_or_empty_declared_fact_identity(self, field):
        rh = Rehydrator()
        fact = make_fact()
        data = to_dictable(fact)
        data["fields"][field] = ""
        project = make_project()
        source = make_source()
        snap = make_snapshot()
        algo = make_algo()
        mapping = make_mapping()
        result = make_mapping_result(snap=snap, mapping=mapping, algo=algo)
        record = make_record_id()
        with pytest.raises(RehydrationError):
            rh.rehydrate_canonical_fact(
                data, project, source, snap, record, algo, mapping, result,
            )


# ---------------------------------------------------------------------------
# Non-authoritative passthrough
# ---------------------------------------------------------------------------

class TestRehydratePlain:
    def test_round_trips_non_authoritative(self):
        from mm_r2.domain import StudyProject
        rh = Rehydrator()
        project = StudyProject(project_id="p1", name="Test")
        rebuilt = rh.rehydrate_plain(to_dictable(project))
        assert rebuilt.project_id == "p1"
        assert rebuilt.name == "Test"

    def test_rejects_authoritative_via_plain(self):
        rh = Rehydrator()
        source = make_source()
        with pytest.raises(Exception):
            rh.rehydrate_plain(to_dictable(source))
