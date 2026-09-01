"""Focused renderer-neutral S5 projection and shared-context tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from mm_r5.s5_contracts import S5AEMHPacket, S5SubjectTemporalPacket
from mm_r5.s5_projection import (
    S5ProjectionError,
    build_selection_anchor,
    build_subject_workspace,
    project_aemh_history,
    project_subject_temporal,
    project_subject_workspace,
)
from s5_runtime_fixtures import (
    build_aemh_match_history_authority_bundle,
    build_aemh_packet,
    build_subject_packet,
    build_subject_temporal_authority_bundle,
    build_subject_workspace as fixture_workspace,
)


def test_workspace_binds_three_views_to_one_shared_context_and_spine() -> None:
    subject = build_subject_packet()
    aemh = build_aemh_packet()
    workspace = project_subject_workspace(subject, aemh)

    assert workspace.subject_ref == subject.projection.scope_identity.subject_ref
    assert workspace.spine_ref == subject.projection.scope_identity.spine_ref
    assert workspace.shared_context.authority_receipt_ref == subject.receipt.receipt_id
    assert workspace.shared_context.axis_mode == "calendar"
    assert len(workspace.view_bindings) == 3
    assert {binding.view for binding in workspace.view_bindings} == {
        "journey", "profile", "timeline",
    }
    assert {binding.shared_context_ref for binding in workspace.view_bindings} == {
        workspace.shared_context.context_ref,
    }
    assert {binding.spine_ref for binding in workspace.view_bindings} == {
        workspace.spine_ref,
    }


def test_workspace_is_deterministic_and_source_builder_matches_projection() -> None:
    subject_source = fixture_workspace()
    subject = build_subject_packet()
    aemh = build_aemh_packet()
    assert subject_source == project_subject_workspace(subject, aemh)
    assert subject_source == project_subject_workspace(subject, aemh)
    assert build_subject_workspace(
        # The source-facing helper must use typed public authority internally.
        build_subject_temporal_authority_bundle(),
        build_aemh_match_history_authority_bundle(),
    ) == subject_source


@pytest.mark.parametrize(
    ("kind", "ref_attr"),
    (("event", "event_ref"), ("risk_anchor", "risk_anchor_ref"),
     ("visit", "visit_ref"), ("source_locator", "locator_ref")),
)
def test_selection_anchor_accepts_only_verified_packet_members(kind: str, ref_attr: str) -> None:
    subject = build_subject_packet()
    members = {
        "event": subject.projection.events,
        "risk_anchor": subject.projection.risk_anchors,
        "visit": subject.projection.visits,
        "source_locator": subject.projection.source_locators,
    }[kind]
    assert members, kind
    ref = getattr(members[0], ref_attr)
    anchor = build_selection_anchor(subject, anchor_kind=kind, anchor_ref=ref)
    assert anchor.anchor_kind == kind
    assert anchor.anchor_ref == ref


def test_selection_anchor_rejects_unbound_reference_and_bad_kind() -> None:
    subject = build_subject_packet()
    with pytest.raises(S5ProjectionError) as bad_ref:
        build_selection_anchor(subject, anchor_kind="event", anchor_ref="event-unbound")
    assert bad_ref.value.code == "SELECTION_ANCHOR_NOT_MEMBER"
    with pytest.raises(S5ProjectionError) as bad_kind:
        build_selection_anchor(subject, anchor_kind="other", anchor_ref="event::ae::1")
    assert bad_kind.value.code == "SELECTION_ANCHOR_NOT_MEMBER"


def test_study_day_requires_explicit_axis_anchor_and_valid_context_members() -> None:
    subject = build_subject_packet()
    anchor = build_selection_anchor(
        subject, anchor_kind="event", anchor_ref=subject.projection.events[0].event_ref
    )
    workspace = project_subject_workspace(
        subject,
        axis_mode="study_day",
        window_start=date(2026, 8, 1),
        window_end=date(2026, 8, 31),
        selection_anchor=anchor,
        selected_event_ref=subject.projection.events[0].event_ref,
    )
    assert workspace.shared_context.axis_mode == "study_day"
    assert workspace.shared_context.window_start == date(2026, 8, 1)
    assert workspace.shared_context.window_end == date(2026, 8, 31)
    assert workspace.shared_context.selection_anchor == anchor


def test_projection_entrypoints_require_exact_typed_packets() -> None:
    subject = build_subject_packet()
    aemh = build_aemh_packet()
    with pytest.raises(S5ProjectionError) as subject_error:
        project_subject_temporal({})  # type: ignore[arg-type]
    assert subject_error.value.code == "SUBJECT_PACKET_TYPE_MISMATCH"
    with pytest.raises(S5ProjectionError) as aemh_error:
        project_aemh_history({})  # type: ignore[arg-type]
    assert aemh_error.value.code == "AEMH_PACKET_TYPE_MISMATCH"
    assert isinstance(project_subject_temporal(subject), S5SubjectTemporalPacket)
    assert isinstance(project_aemh_history(aemh), S5AEMHPacket)


def test_scope_and_window_mismatches_fail_closed() -> None:
    subject = build_subject_packet()
    aemh = build_aemh_packet()
    different_spine = replace(
        aemh.projection.scope_identity,
        spine_ref="spine-other",
    )
    different_aemh = replace(
        aemh,
        projection=replace(aemh.projection, scope_identity=different_spine),
    )
    with pytest.raises(S5ProjectionError) as spine_error:
        project_subject_workspace(subject, different_aemh)
    assert spine_error.value.code == "SHARED_SPINE_MISMATCH"

    with pytest.raises(S5ProjectionError) as window_error:
        project_subject_workspace(
            subject,
            window_start=date(2026, 8, 31),
            window_end=date(2026, 8, 1),
        )
    assert window_error.value.code == "SHARED_WINDOW_MISMATCH"


def test_projected_workspace_does_not_make_a_candidate_authority() -> None:
    subject = build_subject_packet()
    aemh = build_aemh_packet()
    workspace = project_subject_workspace(subject, aemh)
    assert workspace.authority_receipt_refs == (
        subject.receipt.receipt_id, aemh.receipt.receipt_id
    )
    assert workspace.view_bindings[0].authority_projection_id == subject.projection.projection_id
