"""Batch A -- artifacts: content-addressed store, envelope, determinism,
idempotency, collision rejection, concurrent same-content writes."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from mm_r2.artifacts import (
    ArtifactCollisionError,
    ArtifactCompleteness,
    ArtifactEnvelope,
    ArtifactStore,
    DomainValidationError,
    EvidenceState,
    HashMismatchError,
    StoredArtifact,
    make_envelope,
)
from mm_r2.domain import (
    CanonicalFact,
    IdentityAlgorithm,
    ListingSnapshot,
    MappingDefinition,
    MappingResult,
    SourceRevision,
    StudyProject,
)
from mm_r2.identity import make_record_identity


def _canonical_fact():
    project = StudyProject(project_id="p1", name="Synthetic Study")
    source = SourceRevision.from_bytes(
        revision_id="rev-1", project_id="p1", source_type="listing",
        version="1", source_bytes=b"synthetic-listing",
    )
    snapshot = ListingSnapshot.from_content(
        snapshot_id="snap-1", project_id="p1", revision_id="rev-1",
        snapshot_version="1", rows=[{"sub": "S01", "ae": "Nausea"}],
    )
    algorithm = IdentityAlgorithm(
        algorithm_id="alg-1", name="record-id", version="1",
    )
    mapping = MappingDefinition(
        mapping_id="m1", project_id="p1", source_revision_id="rev-1",
        identity_algorithm_id="alg-1", source_field="AETERM",
        canonical_field="ae_term", fact_type="ae", version="1",
    )
    result = MappingResult.from_verified(
        result_id="mr1", project_id="p1", snapshot=snapshot,
        mapping=mapping, identity_algorithm=algorithm, record_count=1,
    )
    identity = make_record_identity("p1", algorithm, {"subject": "S01"})
    return CanonicalFact.from_bundle(
        project=project, source=source, snapshot=snapshot,
        record_identity=identity, identity_algorithm=algorithm,
        mapping_definition=mapping, mapping_result=result, fact_type="ae",
        payload=(("term", "Nausea"),),
    )


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------

class TestEnvelope:
    def test_minimal_envelope(self):
        env = make_envelope("listing_profile", "1", input_hash="abc")
        assert env.artifact_type == "listing_profile"
        assert env.payload_role == "candidate"
        assert env.completeness == ArtifactCompleteness.COMPLETE

    def test_invalid_role_rejected(self):
        with pytest.raises(DomainValidationError, match="payload_role"):
            ArtifactEnvelope(
                artifact_id="a", artifact_type="t", artifact_version="1",
                input_hash="h", payload_role="bogus",
            )

    def test_invalid_completeness_rejected(self):
        env = make_envelope(
            "t", "1", input_hash="h", completeness="bogus",
        ) if False else None  # completeness is validated in __post_init__
        with pytest.raises(DomainValidationError, match="completeness"):
            ArtifactEnvelope(
                artifact_id="a", artifact_type="t", artifact_version="1",
                input_hash="h", payload_role="candidate", completeness="bogus",
            )

    def test_candidate_role_allowed_not_fact(self):
        env = make_envelope("t", "1", input_hash="h", payload_role="candidate")
        assert env.payload_role == "candidate"

    def test_envelope_coverage_nested_mutation_impossible(self):
        """VETO2: coverage/QC/lineage nested values are deep-frozen."""
        coverage = {"tables": ["AE", "DM"]}
        env = ArtifactEnvelope(
            artifact_id="a", artifact_type="t", artifact_version="1",
            input_hash="h", payload_role="candidate",
            coverage=(("meta", coverage),),
            qc_notes=("ok",),
        )
        coverage["tables"].append("MUT")  # mutate original caller input
        h1 = env.compute_hash({"x": 1})
        assert env.compute_hash({"x": 1}) == h1
        # reachable nested dict is immutable
        reachable = env.coverage[0][1]
        assert isinstance(reachable.get("tables"), tuple)
        with pytest.raises(TypeError):
            reachable["tables"] = ("X",)


# ---------------------------------------------------------------------------
# Store: content addressing + determinism
# ---------------------------------------------------------------------------

class TestStoreContentAddressing:
    def test_put_and_get_roundtrip(self, r2_artifact_store):
        env = make_envelope("profile", "1", input_hash="in1", payload_role="candidate")
        sa = r2_artifact_store.put(env, {"rows": 10, "cols": ["a", "b"]})
        assert sa.envelope.content_hash
        assert r2_artifact_store.exists(sa.envelope.content_hash)
        data = r2_artifact_store.get(sa.envelope.content_hash)
        assert data == sa.payload_bytes

    def test_same_payload_same_hash(self, r2_artifact_store):
        # Same envelope instance + same payload must content-address to the
        # same hash.
        env = make_envelope("profile", "1", input_hash="in1", payload_role="candidate")
        sa1 = r2_artifact_store.put(env, {"rows": 5})
        sa2 = r2_artifact_store.put(env, {"rows": 5})
        assert sa1.envelope.content_hash == sa2.envelope.content_hash

    # -- Blocker 1 regression: fresh envelopes with identical logical
    #    metadata/payload must hash equally (artifact_id excluded). --------

    def test_fresh_identical_envelopes_same_hash(self):
        """Two fresh make_envelope() calls with identical logical metadata
        must produce the same content address (artifact_id is excluded)."""
        e1 = make_envelope("profile", "1", input_hash="h", payload_role="candidate")
        e2 = make_envelope("profile", "1", input_hash="h", payload_role="candidate")
        assert e1.compute_hash({"x": 1}) == e2.compute_hash({"x": 1})

    def test_fresh_envelopes_different_payload_different_hash(self):
        e1 = make_envelope("profile", "1", input_hash="h", payload_role="candidate")
        e2 = make_envelope("profile", "1", input_hash="h", payload_role="candidate")
        assert e1.compute_hash({"x": 1}) != e2.compute_hash({"x": 2})

    def test_different_payload_different_hash(self, r2_artifact_store):
        env1 = make_envelope("profile", "1", input_hash="in1", payload_role="candidate")
        env2 = make_envelope("profile", "1", input_hash="in1", payload_role="candidate")
        sa1 = r2_artifact_store.put(env1, {"rows": 5})
        sa2 = r2_artifact_store.put(env2, {"rows": 6})
        assert sa1.envelope.content_hash != sa2.envelope.content_hash

    def test_declared_hash_mismatch_rejected(self, r2_artifact_store):
        env = ArtifactEnvelope(
            artifact_id="a", artifact_type="t", artifact_version="1",
            input_hash="h", payload_role="candidate", content_hash="bogus",
        )
        with pytest.raises(HashMismatchError, match="mismatch"):
            r2_artifact_store.put(env, {"x": 1})

    def test_get_nonexistent_raises(self, r2_artifact_store):
        with pytest.raises(Exception):
            r2_artifact_store.get("0" * 64)


# ---------------------------------------------------------------------------
# Idempotency: repeated same-content writes
# ---------------------------------------------------------------------------

class TestIdempotency:
    def test_repeated_same_content_is_idempotent(self, r2_artifact_store):
        env = make_envelope("profile", "1", input_hash="in1", payload_role="candidate")
        payload = {"rows": 10}
        sa1 = r2_artifact_store.put(env, payload)
        sa2 = r2_artifact_store.put(env, payload)
        sa3 = r2_artifact_store.put(env, payload)
        assert sa1.envelope.content_hash == sa2.envelope.content_hash == sa3.envelope.content_hash
        assert len(r2_artifact_store.list_hashes()) == 1

    def test_collision_rejected(self, tmp_path):
        store = ArtifactStore(tmp_path / "art")
        env = make_envelope("profile", "1", input_hash="in1", payload_role="candidate")
        store.put(env, {"rows": 10})
        # Corrupt: write different bytes at the same content-addressed path.
        chash = env.compute_hash({"rows": 10})
        path = store._path_for(chash)
        path.write_bytes(b"different bytes")
        with pytest.raises(ArtifactCollisionError, match="collision"):
            store.put(env, {"rows": 10})


# ---------------------------------------------------------------------------
# Concurrent same-content writes
# ---------------------------------------------------------------------------

class TestConcurrentWrites:
    def test_concurrent_same_content_safe(self, tmp_path):
        store = ArtifactStore(tmp_path / "art")
        env = make_envelope("profile", "1", input_hash="in1", payload_role="candidate")
        payload = {"rows": 42}
        results: list = []
        errors: list = []
        barrier = threading.Barrier(8)

        def writer():
            try:
                barrier.wait()
                sa = store.put(env, payload)
                results.append(sa.envelope.content_hash)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert len(results) == 8
        # all writers got the same content hash
        assert len(set(results)) == 1
        # exactly one artifact on disk
        assert len(store.list_hashes()) == 1

    def test_concurrent_different_content_distinct_hashes(self, tmp_path):
        store = ArtifactStore(tmp_path / "art")
        errors: list = []
        barrier = threading.Barrier(4)

        def writer(n):
            try:
                barrier.wait()
                env = make_envelope("profile", "1", input_hash=f"in{n}", payload_role="candidate")
                store.put(env, {"rows": n})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert len(store.list_hashes()) == 4

    def test_concurrent_fresh_envelope_same_content_safe(self, tmp_path):
        """Each thread creates a fresh envelope with identical logical metadata;
        all must content-address to the same hash and store exactly one artifact."""
        store = ArtifactStore(tmp_path / "art")
        payload = {"rows": 42}
        results: list = []
        errors: list = []
        barrier = threading.Barrier(8)

        def writer():
            try:
                barrier.wait()
                env = make_envelope("profile", "1", input_hash="in1", payload_role="candidate")
                sa = store.put(env, payload)
                results.append(sa.envelope.content_hash)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert len(results) == 8
        assert len(set(results)) == 1
        assert len(store.list_hashes()) == 1


# ---------------------------------------------------------------------------
# Payload-role separation (candidates never become facts via the store)
# ---------------------------------------------------------------------------

class TestPayloadRoleSeparation:
    def test_role_recorded_in_envelope(self, r2_artifact_store):
        env = make_envelope("profile", "1", input_hash="h", payload_role="suggestion")
        sa = r2_artifact_store.put(env, {"x": 1})
        assert sa.envelope.payload_role == "suggestion"

    def test_arbitrary_dictionary_cannot_be_promoted_to_facts(
        self, r2_artifact_store,
    ):
        env = make_envelope("canonical_facts", "1", "h", payload_role="facts")
        with pytest.raises(DomainValidationError, match="CanonicalFact"):
            env.compute_hash({"candidate": "not-authoritative"})
        with pytest.raises(DomainValidationError, match="CanonicalFact"):
            r2_artifact_store.put(env, {"candidate": "not-authoritative"})

    def test_verified_canonical_fact_can_be_stored_as_facts(
        self, r2_artifact_store,
    ):
        fact = _canonical_fact()
        env = make_envelope("canonical_facts", "1", "h", payload_role="facts")
        stored = r2_artifact_store.put(env, [fact])
        assert stored.envelope.payload_role == "facts"
        assert stored.envelope.content_hash == env.compute_hash(fact)

    def test_empty_facts_payload_is_not_an_authoritative_artifact(self):
        env = make_envelope("canonical_facts", "1", "h", payload_role="facts")
        with pytest.raises(DomainValidationError, match="at least one"):
            env.compute_hash([])
