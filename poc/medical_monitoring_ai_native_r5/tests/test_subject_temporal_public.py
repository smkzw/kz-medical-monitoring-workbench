"""Focused subject-temporal public projection tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from mm_r5.public_authority_common import (
    PublicAuthorityConstructionError,
    canonical_sha256,
    without_field,
)
from mm_r5.subject_temporal_public import (
    SubjectTemporalAuthorityPacket,
    build_subject_temporal_authority,
    validate_subject_temporal_authority,
)
from public_authority_runtime_fixtures import build_subject_authority_bundle


def _reseal(bundle, *, source=None, **changes):
    candidate = replace(
        bundle,
        source=bundle.source if source is None else source,
        bundle_content_identity="0" * 64,
        **changes,
    )
    return replace(
        candidate,
        bundle_content_identity=canonical_sha256(
            without_field(candidate, "bundle_content_identity")
        ),
    )


def test_subject_packet_reconstructs_full_temporal_projection() -> None:
    authority = build_subject_authority_bundle()
    packet = build_subject_temporal_authority(authority)
    result = validate_subject_temporal_authority(packet, authority)
    assert isinstance(packet, SubjectTemporalAuthorityPacket)
    assert result.ok is True
    assert result.packet_emitted is True

    projection = packet.projection
    assert projection.contract_id == "subject-temporal-public-v1"
    assert projection.schema_version == "2026-08-19.1"
    assert projection.fallback_policy == "fail_closed_no_nearest"
    assert projection.scope_identity.subject_ref == "subject::001-0001"
    assert projection.scope_identity.cutoff_ref == "2026-08-19"
    assert projection.axis_basis.default_axis_mode == "calendar"
    assert projection.axis_basis.study_day_anchor_event_ref == "event::ae::1"
    assert projection.axis_basis.study_day_zero_exists is False
    assert projection.axis_basis.cutoff_endpoint.exact_date == "2026-08-19"
    assert projection.axis_basis.cutoff_endpoint.source_locator_refs == (
        "locator::cutoff::v1",
    )

    assert tuple(event.domain for event in projection.events) == ("ae", "mh")
    assert len(projection.visits) == 1
    assert len(projection.events) == 2
    assert len(projection.risk_anchors) == 1
    assert len(projection.phase_bands) == 1
    assert len(projection.pending_date_items) == 2
    assert len(projection.domain_tracks) == 8
    assert len(projection.source_locators) == 4
    assert projection.membership_index.event_refs == (
        "event::ae::1",
        "event::mh::1",
    )

    ae, mh = projection.events
    assert ae.start_endpoint.exact_date == "2026-08-01"
    assert ae.start_endpoint.study_day == 1
    assert ae.end_endpoint.exact_date == "2026-08-02"
    assert ae.end_endpoint.study_day == 2
    assert mh.start_endpoint.state == "partial"
    assert mh.start_endpoint.range_start == "2026-08-01"
    assert mh.start_endpoint.range_end == "2026-08-31"
    assert mh.end_endpoint.state == "missing"
    assert mh.end_endpoint.main_axis_projectable is False

    assert packet.receipt.receipt_variant == "subject_temporal"
    assert packet.receipt.scope_identity == projection.scope_identity
    assert packet.receipt.public_projection_id == projection.projection_id
    assert packet.receipt.public_projection_content_hash == (
        projection.projection_content_hash
    )
    assert packet.packet_content_hash == canonical_sha256(
        {
            "receipt_content_hash": packet.receipt.receipt_content_hash,
            "projection_content_hash": projection.projection_content_hash,
        }
    )


def test_subject_build_is_deterministic_and_candidate_is_not_authority() -> None:
    authority = build_subject_authority_bundle()
    first = build_subject_temporal_authority(authority)
    second = build_subject_temporal_authority(authority)
    assert first == second

    tampered = replace(first, packet_content_hash="0" * 64)
    result = validate_subject_temporal_authority(tampered, authority)
    assert result.ok is False
    assert result.primary_code == "PUB_HASH_MISMATCH"
    assert result.packet_emitted is False


def test_subject_authority_pin_failure_is_fail_closed() -> None:
    authority = build_subject_authority_bundle()
    bad = replace(authority, bundle_content_identity="0" * 64)
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_subject_temporal_authority(bad)
    assert caught.value.result.primary_code == "PUB_AUTHORITY_IDENTITY_MISMATCH"
    assert caught.value.result.packet_emitted is False


def test_subject_source_join_failure_does_not_fallback_to_nearest() -> None:
    authority = build_subject_authority_bundle()
    source = authority.source
    bad_event = replace(source.events[0], locator_refs=("locator::not-authorized",))
    bad_source = replace(source, events=(bad_event, source.events[1]))
    bad_authority = _reseal(authority, source=bad_source)

    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_subject_temporal_authority(bad_authority)
    assert caught.value.result.primary_code == "PUB_SOURCE_JOIN_MISMATCH"
    assert all(
        issue.code != "PUB_NEAREST_FALLBACK" for issue in caught.value.result.issues
    )


def _subject_axis_timezone_empty(source):
    return replace(source, axis=replace(source.axis, timezone=""))


def _subject_domain_state_invalid(source):
    return replace(
        source,
        domain_applicability=tuple(
            replace(row, state="invalid") if row.domain == "mh" else row
            for row in source.domain_applicability
        ),
    )


def _subject_geometry_invalid(source):
    return replace(source, events=(replace(source.events[0], geometry="point"), source.events[1]))


def _subject_date_state_invalid(source):
    event = replace(
        source.events[0],
        start=replace(source.events[0].start, state="partial"),
    )
    return replace(source, events=(event, source.events[1]))


def _subject_exact_endpoint_not_projectable(source):
    event = replace(
        source.events[0],
        end=replace(
            source.events[0].end,
            projectable=False,
            range_authorized=False,
        ),
    )
    return replace(source, events=(event, source.events[1]))


@pytest.mark.parametrize(
    ("mutate", "expected"),
    (
        (_subject_axis_timezone_empty, "PUB_AXIS_INVALID"),
        (_subject_domain_state_invalid, "PUB_DOMAIN_APPLICABILITY_INVALID"),
        (_subject_geometry_invalid, "PUB_DATE_GEOMETRY_INVALID"),
        (_subject_date_state_invalid, "PUB_DATE_STATE_INVALID"),
        (_subject_exact_endpoint_not_projectable, "PUB_DATE_PROJECTABILITY_MISMATCH"),
    ),
)
def test_subject_axis_geometry_date_projectability_and_domain_gates_fail_closed(
    mutate, expected
) -> None:
    authority = build_subject_authority_bundle()
    bad_authority = _reseal(authority, source=mutate(authority.source))
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_subject_temporal_authority(bad_authority)
    assert caught.value.result.primary_code == expected
    assert caught.value.result.packet_emitted is False


def _subject_visit_actual_missing(source):
    actual = replace(
        source.visit.actual,
        candidates=(),
        exact_date=None,
        projectable=False,
        range_authorized=False,
        range_end=None,
        range_start=None,
        state="missing",
        study_day=None,
    )
    return replace(source, visit=replace(source.visit, actual=actual))


def test_subject_pending_items_cover_a_missing_actual_visit() -> None:
    authority = build_subject_authority_bundle()
    packet = build_subject_temporal_authority(
        _reseal(authority, source=_subject_visit_actual_missing(authority.source))
    )
    pending = packet.projection.pending_date_items
    assert {(item.item_kind, item.item_ref) for item in pending} == {
        ("visit", "visit::actual::v1"),
        ("event", "event::mh::1"),
        ("phase", "phase::treatment"),
    }
    assert packet.projection.membership_index.pending_date_refs == tuple(
        item.pending_ref for item in pending
    )
    visit_pending = next(item for item in pending if item.item_kind == "visit")
    assert visit_pending.end_endpoint.state == "missing"
    assert visit_pending.target_content_hash == packet.projection.visits[0].visit_content_hash


def _subject_visit_phase_mismatch(source):
    return replace(source, visit=replace(source.visit, phase_ref="phase::other"))


def _subject_risk_event_domain_mismatch(source):
    return replace(source, risk=replace(source.risk, event_ref="event::mh::1"))


def _subject_event_risk_domain_mismatch(source):
    event = replace(source.events[1], risk_refs=(source.risk.risk_anchor_ref,))
    return replace(source, events=(source.events[0], event))


@pytest.mark.parametrize(
    ("mutate", "path"),
    (
        (_subject_visit_phase_mismatch, "/source/visit/phase_ref"),
        (_subject_risk_event_domain_mismatch, "/source/risk/event_ref"),
        (_subject_event_risk_domain_mismatch, "/source/events/risk_refs"),
    ),
)
def test_subject_phase_and_cross_domain_bindings_fail_closed(mutate, path) -> None:
    authority = build_subject_authority_bundle()
    bad_authority = _reseal(authority, source=mutate(authority.source))
    with pytest.raises(PublicAuthorityConstructionError) as caught:
        build_subject_temporal_authority(bad_authority)
    assert caught.value.result.primary_code == "PUB_SOURCE_JOIN_MISMATCH"
    assert path in {issue.path for issue in caught.value.result.issues}
    assert caught.value.result.packet_emitted is False
