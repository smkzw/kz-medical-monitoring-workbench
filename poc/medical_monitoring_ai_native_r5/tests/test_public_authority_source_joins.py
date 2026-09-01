"""Source-join coverage for the frozen 272-leaf public-authority contract."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from mm_r5.aemh_match_history_public import build_aemh_match_history_authority
from mm_r5.public_authority_common import (
    PublicAuthorityConstructionError,
    RevisionInputV02,
    canonical_sha256,
    without_field,
)
from mm_r5.subject_temporal_public import build_subject_temporal_authority
from public_authority_runtime_fixtures import (
    build_aemh_authority_bundle,
    build_subject_authority_bundle,
)


_WORKSPACE = Path(__file__).resolve().parents[3]
_V042 = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s5_public_authority_implementation_contract_v0_4_2"
)
_TYPED_AUTHORITY = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s5_typed_authority_model_delta_v0_1"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _reseal(bundle, source):
    candidate = replace(bundle, source=source, bundle_content_identity="0" * 64)
    return replace(
        candidate,
        bundle_content_identity=canonical_sha256(
            without_field(candidate, "bundle_content_identity")
        ),
    )


def _locator_refs(value: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_locator_ref" and isinstance(item, str):
                refs.add(item)
            elif key.endswith("_locator_ref") and isinstance(item, str):
                refs.add(item)
            elif key.endswith("_locator_refs") and isinstance(item, (list, tuple)):
                refs.update(ref for ref in item if isinstance(ref, str))
            refs.update(_locator_refs(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            refs.update(_locator_refs(item))
    return refs


def _revision(revision_ref: str, locator_refs: tuple[str, ...]) -> RevisionInputV02:
    return RevisionInputV02(
        locator_refs=locator_refs,
        revision_content_identity=canonical_sha256(
            {"revision": revision_ref, "accepted": True}
        ),
        revision_ref=revision_ref,
    )


def _assert_total_disjoint_partition(locator_specs, revision_specs) -> None:
    locator_refs = tuple(row.locator_ref for row in locator_specs)
    assigned_refs = tuple(
        locator_ref for revision in revision_specs for locator_ref in revision.locator_refs
    )
    assert len(locator_refs) == len(set(locator_refs))
    assert len(assigned_refs) == len(set(assigned_refs))
    assert set(assigned_refs) == set(locator_refs)
    owners = {
        locator_ref: revision.revision_ref
        for revision in revision_specs
        for locator_ref in revision.locator_refs
    }
    assert all(owners[row.locator_ref] == row.revision_ref for row in locator_specs)


def test_v042_has_exactly_272_authority_joins() -> None:
    leaf_registry = _json(_V042 / "leaf_execution_registry.json")
    typed_contract = _json(_TYPED_AUTHORITY / "authority_contract.json")
    rows = leaf_registry["rows"]
    derivations = typed_contract["leaf_derivations"]

    assert leaf_registry["row_count"] == 272
    assert leaf_registry["accepted_recipe_to_parent_packet_compare_count"] == 268
    assert leaf_registry["subject_public_cutoff_from_binding_count"] == 4
    assert len(rows) == len(derivations) == 272
    assert len({row["qualified_leaf"] for row in rows}) == 272
    assert len({row["qualified_leaf"] for row in derivations}) == 272
    assert {row["qualified_leaf"] for row in rows} == {
        row["qualified_leaf"] for row in derivations
    }

    assert {row["serialized_input_authority"] for row in rows} == {
        "accepted_temporal_v02_authority_bundle"
    }
    assert all(row["candidate_backfill_forbidden"] is True for row in rows)
    assert all(row["second_typed_truth_plane_forbidden"] is True for row in rows)
    assert all(
        pointer.startswith("/source/")
        for row in rows
        for pointer in row["transitive_authority_pointers"]
    )
    assert sum(
        row["closure_kind"] == "accepted_recipe_to_parent_packet_compare"
        for row in rows
    ) == 268
    assert sum(
        row["closure_kind"] == "subject_public_cutoff_from_binding"
        for row in rows
    ) == 4
    assert all(
        row["execution_evidence"]["typed_decode_roundtrip"] is True
        for row in rows
    )


@pytest.mark.parametrize(
    ("builder", "bundle"),
    (
        (build_subject_temporal_authority, build_subject_authority_bundle),
        (build_aemh_match_history_authority, build_aemh_authority_bundle),
    ),
)
def test_every_emitted_locator_ref_joins_authority_source(builder, bundle) -> None:
    authority = bundle()
    packet = builder(authority)
    source = authority.source
    if hasattr(source, "locator_specs"):
        source_refs = {row.locator_ref for row in source.locator_specs}
    else:
        source_refs = {
            row.locator_ref
            for row in source.current_locator_specs + source.previous_locator_specs
        }
    emitted_refs = _locator_refs(asdict(packet))
    assert emitted_refs
    assert emitted_refs <= source_refs


def test_subject_revision_pairs_and_scope_are_source_bound() -> None:
    authority = build_subject_authority_bundle()
    packet = build_subject_temporal_authority(authority)
    source = authority.source
    pairs = {
        pair.revision_id: pair for pair in packet.receipt.source_revision_content_pairs
    }
    assert set(pairs) == {row.revision_ref for row in source.revision_specs}
    for revision in source.revision_specs:
        pair = pairs[revision.revision_ref]
        assert pair.accepted_content_hash == revision.revision_content_identity
        assert pair.locator_refs == tuple(sorted(revision.locator_refs))
    _assert_total_disjoint_partition(source.locator_specs, source.revision_specs)
    scope = packet.projection.scope_identity
    assert (scope.project_ref, scope.run_ref, scope.site_ref, scope.snapshot_ref, scope.spine_ref, scope.subject_ref) == (
        source.scope.project_ref,
        source.scope.run_ref,
        source.scope.site_ref,
        source.scope.snapshot_ref,
        source.scope.spine_ref,
        source.scope.subject_ref,
    )


def test_aemh_cross_snapshot_revision_pairs_and_history_refs_are_bound() -> None:
    authority = build_aemh_authority_bundle()
    packet = build_aemh_match_history_authority(authority)
    source = authority.source
    pairs = {
        pair.revision_id: pair for pair in packet.receipt.source_revision_content_pairs
    }
    assert set(pairs) == {
        row.revision_ref
        for row in source.current_revision_specs
    }
    for revision in source.current_revision_specs:
        assert pairs[revision.revision_ref].locator_refs == tuple(
            sorted(revision.locator_refs)
        )
    _assert_total_disjoint_partition(
        source.current_locator_specs, source.current_revision_specs
    )
    _assert_total_disjoint_partition(
        source.previous_locator_specs, source.previous_revision_specs
    )
    current_refs = {row.locator_ref for row in source.current_locator_specs}
    for thread in packet.projection.threads:
        assert set(thread.evidence_locator_refs) <= current_refs
        for entry in thread.history_entries:
            assert set(entry.retained_evidence_locator_refs) <= current_refs
            assert set(entry.identity_evidence_refs) == {
                evidence.evidence_ref for evidence in entry.identity_evidence
            }


def test_subject_source_join_mutation_fails_closed() -> None:
    authority = build_subject_authority_bundle()
    source = authority.source
    mutated = replace(
        source.events[0], locator_refs=("locator::not-authorized",)
    )
    bad_authority = _reseal(authority, replace(source, events=(mutated, source.events[1])))
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_subject_temporal_authority(bad_authority)
    assert caught.value.result.primary_code == "PUB_SOURCE_JOIN_MISMATCH"


def test_aemh_evidence_binding_mutation_fails_closed() -> None:
    authority = build_aemh_authority_bundle()
    source = authority.source
    mutated_thread = replace(
        source.thread_specs[0], candidate_ref="candidate::not-authorized"
    )
    bad_source = replace(source, thread_specs=(mutated_thread, source.thread_specs[1]))
    bad_authority = _reseal(authority, bad_source)
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_aemh_match_history_authority(bad_authority)
    assert caught.value.result.primary_code == "PUB_SOURCE_LOCATOR_UNUSED"
    assert "AEMH_EVIDENCE_AUTHORITY_BINDING" in {
        issue.code for issue in caught.value.result.issues
    }


def test_subject_revision_partition_rejects_overlap_and_unused_locator() -> None:
    authority = build_subject_authority_bundle()
    source = authority.source
    overlap = _revision(
        "source-revision::listing::N+2",
        (source.locator_specs[0].locator_ref,),
    )
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_subject_temporal_authority(
            _reseal(
                authority,
                replace(source, revision_specs=source.revision_specs + (overlap,)),
            )
        )
    assert caught.value.result.primary_code == "PUB_SOURCE_REVISION_OVERLAP"

    unused = replace(
        source.locator_specs[0],
        locator_ref="locator::subject::unused",
        record_ref="unused::subject",
    )
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_subject_temporal_authority(
            _reseal(authority, replace(source, locator_specs=source.locator_specs + (unused,)))
        )
    assert caught.value.result.primary_code == "PUB_SOURCE_LOCATOR_UNUSED"


def test_aemh_revision_partition_rejects_duplicate_and_overlap() -> None:
    authority = build_aemh_authority_bundle()
    source = authority.source
    duplicate = replace(
        source,
        current_revision_specs=source.current_revision_specs
        + (source.current_revision_specs[0],),
    )
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_aemh_match_history_authority(_reseal(authority, duplicate))
    assert caught.value.result.primary_code == "PUB_SOURCE_REVISION_DUPLICATE"

    overlap = _revision(
        "source-revision::listing::N+2",
        ("locator::fact::ae1",),
    )
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_aemh_match_history_authority(
            _reseal(
                authority,
                replace(
                    source,
                    current_revision_specs=source.current_revision_specs + (overlap,),
                ),
            )
        )
    assert caught.value.result.primary_code == "PUB_SOURCE_REVISION_OVERLAP"


def test_aemh_locator_consumption_rejects_unused_and_missing_current_locator() -> None:
    authority = build_aemh_authority_bundle()
    source = authority.source
    unused = replace(
        source.current_locator_specs[0],
        locator_ref="locator::aemh::unused",
        record_ref="unused::aemh",
        entity_kind="later_fact",
        entity_ref="fact::unused",
    )
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_aemh_match_history_authority(
            _reseal(
                authority,
                replace(source, current_locator_specs=source.current_locator_specs + (unused,)),
            )
        )
    assert caught.value.result.primary_code == "PUB_SOURCE_LOCATOR_UNUSED"

    missing = tuple(
        row
        for row in source.current_locator_specs
        if row.locator_ref != "locator::reminder::mh1"
    )
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_aemh_match_history_authority(
            _reseal(authority, replace(source, current_locator_specs=missing))
        )
    assert caught.value.result.primary_code == "PUB_SOURCE_JOIN_MISMATCH"
