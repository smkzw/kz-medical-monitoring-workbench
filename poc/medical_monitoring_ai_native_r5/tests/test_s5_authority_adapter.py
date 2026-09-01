"""Focused tests for the typed public-authority to S5 adapter boundary."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mm_r5 import aemh_match_history_public as aemh_public
from mm_r5 import public_authority_common as common
from mm_r5 import subject_temporal_public as subject_public
from mm_r5.s5_authority_adapter import (
    S5AuthorityAdapterError,
    adapt_aemh_match_history_authority,
    adapt_subject_temporal_authority,
    build_s5_authority_packet,
)
from mm_r5.s5_contracts import S5AEMHPacket, S5SubjectTemporalPacket, s5_as_mapping
from public_authority_runtime_fixtures import (
    build_aemh_authority_bundle,
    build_subject_authority_bundle,
)
from s5_runtime_fixtures import build_aemh_packet, build_subject_packet


def test_subject_adapter_uses_accepted_public_builder_and_preserves_bindings() -> None:
    source = build_subject_authority_bundle()
    public_packet = subject_public.build_subject_temporal_authority(source)
    public_check = subject_public.validate_subject_temporal_authority(public_packet, source)
    packet = adapt_subject_temporal_authority(source)

    assert public_check.ok
    assert isinstance(packet, S5SubjectTemporalPacket)
    assert packet.packet_content_hash == public_packet.packet_content_hash
    assert packet.projection.projection_content_hash == public_packet.projection.projection_content_hash
    assert packet.projection.projection_id == public_packet.projection.projection_id
    assert packet.receipt.receipt_id == public_packet.receipt.receipt_id
    assert packet.receipt.scope_identity.subject_ref == public_packet.receipt.scope_identity.subject_ref
    assert packet.receipt.scope_identity.spine_ref == public_packet.receipt.scope_identity.spine_ref


def test_aemh_adapter_preserves_append_only_history_and_receipt() -> None:
    source = build_aemh_authority_bundle()
    public_packet = aemh_public.build_aemh_match_history_authority(source)
    public_check = aemh_public.validate_aemh_match_history_authority(public_packet, source)
    packet = adapt_aemh_match_history_authority(source)

    assert public_check.ok
    assert isinstance(packet, S5AEMHPacket)
    assert packet.packet_content_hash == public_packet.packet_content_hash
    assert packet.projection.projection_content_hash == public_packet.projection.projection_content_hash
    assert packet.projection.accepted_thread_prefixes
    assert packet.projection.threads
    assert all(thread.history_entries for thread in packet.projection.threads)
    assert packet.receipt.receipt_id == public_packet.receipt.receipt_id


@pytest.mark.parametrize(
    ("source_factory", "packet_type"),
    ((build_subject_authority_bundle, S5SubjectTemporalPacket),
     (build_aemh_authority_bundle, S5AEMHPacket)),
)
def test_generic_builder_dispatches_only_by_typed_target(
    source_factory, packet_type,
) -> None:
    packet = build_s5_authority_packet(source_factory())
    assert isinstance(packet, packet_type)


def test_candidate_packet_cannot_be_reused_as_authority() -> None:
    candidate = build_subject_packet()
    with pytest.raises(S5AuthorityAdapterError) as error:
        build_s5_authority_packet(candidate)  # type: ignore[arg-type]
    assert error.value.code == "CANDIDATE_OUTPUT_AS_AUTHORITY"


def test_wrong_authority_target_fails_closed_before_adaptation() -> None:
    source = build_subject_authority_bundle()
    wrong_target = replace(source, target_contract="unknown-contract")
    with pytest.raises(S5AuthorityAdapterError) as error:
        adapt_subject_temporal_authority(wrong_target)
    assert error.value.code == "AUTHORITY_TARGET_MISMATCH"
    with pytest.raises(S5AuthorityAdapterError) as generic_error:
        build_s5_authority_packet(wrong_target)
    assert generic_error.value.code == "AUTHORITY_TARGET_MISMATCH"


def test_subject_and_aemh_adapters_are_deterministic_for_same_typed_input() -> None:
    subject_source = build_subject_authority_bundle()
    aemh_source = build_aemh_authority_bundle()
    assert adapt_subject_temporal_authority(subject_source) == adapt_subject_temporal_authority(
        subject_source
    )
    assert adapt_aemh_match_history_authority(aemh_source) == adapt_aemh_match_history_authority(
        aemh_source
    )


def test_adapter_mapping_is_lossless_for_dates_and_identity_fields() -> None:
    subject = build_subject_packet()
    mapped = s5_as_mapping(subject)
    first_event = mapped["projection"]["events"][0]
    assert first_event["start_endpoint"]["exact_date"] == "2026-08-01"
    assert first_event["end_endpoint"]["exact_date"] == "2026-08-02"
    assert mapped["projection"]["scope_identity"]["subject_ref"] == "subject::001-0001"
    assert mapped["projection"]["scope_identity"]["spine_ref"] == "spine::001-0001::N+1"
    assert mapped["projection"]["fallback_policy"] == "fail_closed_no_nearest"


def test_fixture_packet_helpers_are_the_same_public_adapter_path() -> None:
    assert build_subject_packet() == adapt_subject_temporal_authority(
        build_subject_authority_bundle()
    )
    assert build_aemh_packet() == adapt_aemh_match_history_authority(
        build_aemh_authority_bundle()
    )
