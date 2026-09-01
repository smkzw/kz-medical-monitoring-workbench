"""Focused AE/MH match-history reconstruction and append-only tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mm_r5.aemh_match_history_public import (
    AEMHMatchHistoryAuthorityPacket,
    build_aemh_match_history_authority,
    validate_aemh_match_history_authority,
)
from mm_r5.public_authority_common import (
    PublicAuthorityConstructionError,
    canonical_sha256,
    without_field,
)
from public_authority_runtime_fixtures import build_aemh_authority_bundle


def _reseal(bundle, *, source=None):
    candidate = replace(
        bundle,
        source=bundle.source if source is None else source,
        bundle_content_identity="0" * 64,
    )
    return replace(
        candidate,
        bundle_content_identity=canonical_sha256(
            without_field(candidate, "bundle_content_identity")
        ),
    )


def test_aemh_packet_replays_previous_prefix_and_current_history() -> None:
    authority = build_aemh_authority_bundle()
    packet = build_aemh_match_history_authority(authority)
    result = validate_aemh_match_history_authority(packet, authority)
    assert isinstance(packet, AEMHMatchHistoryAuthorityPacket)
    assert result.ok is True
    assert result.packet_emitted is True

    projection = packet.projection
    assert projection.contract_id == "aemh-match-history-public-v1"
    assert projection.schema_version == "2026-08-19.1"
    assert projection.fallback_policy == "fail_closed_no_nearest"
    assert projection.previous_projection_ref is not None
    assert projection.previous_projection_content_hash is not None
    assert projection.scope_identity.snapshot_ref == "snapshot::N+1"
    assert projection.cutoff_endpoint.exact_date == "2026-08-19"
    assert projection.cutoff_endpoint.source_locator_refs == (
        "locator::reminder::ae1",
    )
    assert tuple(thread.domain for thread in projection.threads) == ("ae", "mh")
    assert len(projection.source_locators) == 4
    assert len(projection.accepted_thread_prefixes) == 2
    assert projection.membership_index.thread_refs == (
        "aemh-thread::ae::1",
        "aemh-thread::mh::1",
    )
    assert projection.membership_index.candidate_refs == (
        "candidate::suspected-ae::1",
        "candidate::suspected-mh::1",
    )
    assert projection.membership_index.later_fact_refs == (
        "fact::reported-ae::later-1",
    )

    by_domain = {thread.domain: thread for thread in projection.threads}
    ae = by_domain["ae"]
    mh = by_domain["mh"]
    assert [entry.event_kind for entry in ae.history_entries] == [
        "reminder_created",
        "match_decided",
        "withdrawn",
        "reappeared",
    ]
    assert [entry.match_state for entry in ae.history_entries] == [
        None,
        "exact",
        None,
        None,
    ]
    assert [entry.event_kind for entry in mh.history_entries] == [
        "reminder_created",
        "match_decided",
    ]
    assert mh.history_entries[-1].match_state == "rejected"

    for thread in projection.threads:
        assert [entry.seq for entry in thread.history_entries] == list(
            range(1, len(thread.history_entries) + 1)
        )
        for previous, current in zip(
            thread.history_entries, thread.history_entries[1:]
        ):
            assert current.prior_entry_hash == previous.entry_hash

    # The previous prefix is retained in-place in the current history.  The
    # accepted prefix anchors expose the corresponding head and prior thread
    # content hash.
    for prefix in projection.accepted_thread_prefixes:
        current = next(
            thread for thread in projection.threads
            if thread.thread_ref == prefix.thread_ref
        )
        assert prefix.accepted_prefix_seq == 1
        assert prefix.accepted_prefix_head_hash == current.history_entries[0].entry_hash
        assert prefix.previous_thread_content_hash is not None
        assert len(prefix.previous_thread_content_hash) == 64
        assert current.history_entries[0].prior_entry_hash is None

    assert packet.receipt.receipt_variant == "aemh_match_history"
    assert packet.receipt.scope_identity == projection.scope_identity
    assert packet.receipt.public_projection_id == projection.projection_id


def test_aemh_candidate_history_mutation_is_rejected_as_non_append_only() -> None:
    authority = build_aemh_authority_bundle()
    packet = build_aemh_match_history_authority(authority)
    thread = packet.projection.threads[0]
    entry = replace(thread.history_entries[0], reason_code="rewritten")
    mutated_thread = replace(thread, history_entries=(entry,) + thread.history_entries[1:])
    projection = replace(
        packet.projection,
        threads=(mutated_thread,) + packet.projection.threads[1:],
    )
    candidate = replace(packet, projection=projection)
    result = validate_aemh_match_history_authority(candidate, authority)
    assert result.ok is False
    assert result.primary_code == "AEMH_HISTORY_NOT_APPEND_ONLY"
    assert result.packet_emitted is False


def test_aemh_builder_rejects_wrong_authority_target() -> None:
    authority = build_aemh_authority_bundle()
    bad = replace(
        authority,
        target_contract="subject-temporal-public-v1",
        bundle_content_identity="0" * 64,
    )
    bad = replace(
        bad,
        bundle_content_identity=canonical_sha256(
            without_field(bad, "bundle_content_identity")
        ),
    )
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_aemh_match_history_authority(bad)
    assert caught.value.result.primary_code == "PUB_TARGET_CONTRACT_MISMATCH"


def _aemh_withdrawn_before_match(source):
    return replace(
        source,
        decision_records=(
            replace(source.decision_records[0], event_kind="withdrawn"),
        ) + source.decision_records[1:],
    )


def _aemh_ambiguous_with_one_fact(source):
    return replace(
        source,
        decision_records=(
            replace(source.decision_records[0], match_state="ambiguous"),
        ) + source.decision_records[1:],
    )


def _aemh_duplicate_match_decision(source):
    return replace(
        source,
        decision_records=source.decision_records + (source.decision_records[0],),
    )


def _aemh_remove_match_decision(source):
    return replace(
        source,
        decision_records=source.decision_records[1:],
    )


def _aemh_invalid_event_enum(source):
    return replace(
        source,
        decision_records=(
            replace(source.decision_records[0], event_kind="invalid"),
        ) + source.decision_records[1:],
    )


def _aemh_invalid_match_enum(source):
    return replace(
        source,
        decision_records=(
            replace(source.decision_records[0], match_state="invalid"),
        ) + source.decision_records[1:],
    )


@pytest.mark.parametrize(
    ("mutate", "expected"),
    (
        (_aemh_withdrawn_before_match, "AEMH_LIFECYCLE_TRANSITION_INVALID"),
        (_aemh_ambiguous_with_one_fact, "AEMH_MATCH_EVIDENCE_MISSING"),
        (_aemh_duplicate_match_decision, "AEMH_MATCH_DECISION_DUPLICATE"),
        (_aemh_remove_match_decision, "AEMH_LIFECYCLE_TRANSITION_INVALID"),
        (_aemh_invalid_event_enum, "PUB_TYPE_MISMATCH"),
        (_aemh_invalid_match_enum, "PUB_TYPE_MISMATCH"),
    ),
)
def test_aemh_lifecycle_enums_cardinality_fail_closed(mutate, expected) -> None:
    authority = build_aemh_authority_bundle()
    bad_authority = _reseal(authority, source=mutate(authority.source))
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_aemh_match_history_authority(bad_authority)
    assert caught.value.result.primary_code == expected
    assert caught.value.result.packet_emitted is False


def test_aemh_candidate_identity_continuity_rejects_current_record_drift() -> None:
    authority = build_aemh_authority_bundle()
    source = authority.source
    current_snapshot = source.current_scope.snapshot_ref
    locators = tuple(
        replace(locator, record_ref="clue-row::drift")
        if locator.locator_ref == "locator::reminder::ae1"
        and locator.snapshot_ref == current_snapshot
        else locator
        for locator in source.current_locator_specs
    )
    bad_authority = _reseal(authority, source=replace(source, current_locator_specs=locators))
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_aemh_match_history_authority(bad_authority)
    assert caught.value.result.primary_code == "AEMH_THREAD_STABLE_IDENTITY_MISMATCH"
    assert caught.value.result.packet_emitted is False


def test_aemh_untouched_thread_with_zero_current_decisions_remains_valid() -> None:
    authority = build_aemh_authority_bundle()
    source = authority.source
    decisions = tuple(
        decision
        for decision in source.decision_records
        if decision.thread_ref != "aemh-thread::mh::1"
    )
    current_locators = tuple(
        locator
        for locator in source.current_locator_specs
        if locator.locator_ref != "locator::considered-fact::mh1"
    )
    current_revisions = tuple(
        replace(
            revision,
            locator_refs=tuple(
                locator_ref
                for locator_ref in revision.locator_refs
                if locator_ref != "locator::considered-fact::mh1"
            ),
        )
        for revision in source.current_revision_specs
    )
    candidate = _reseal(
        authority,
        source=replace(
            source,
            current_locator_specs=current_locators,
            current_revision_specs=current_revisions,
            decision_records=decisions,
        ),
    )

    packet = build_aemh_match_history_authority(candidate)
    result = validate_aemh_match_history_authority(packet, candidate)
    assert result.ok is True
    assert result.packet_emitted is True
    mh_thread = next(
        thread
        for thread in packet.projection.threads
        if thread.thread_ref == "aemh-thread::mh::1"
    )
    assert [entry.event_kind for entry in mh_thread.history_entries] == [
        "reminder_created"
    ]
    assert mh_thread.original_candidate_ref == "candidate::suspected-mh::1"
