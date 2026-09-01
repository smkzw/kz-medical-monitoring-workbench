"""Focused runtime tests for strict S6 navigation, return and density paths."""

from __future__ import annotations

from datetime import date

import pytest

from mm_r5.s6_contracts import (
    S6FilterState,
    S6PageState,
    S6SelectionAnchor,
    S6SortState,
)
from mm_r5.s6_navigation import (
    S6NavigationError,
    build_canonical_return_state,
    build_deep_link_identity,
    build_ephemeral_return_state,
    build_return_context,
    build_semantic_zoom_state,
    canonical_state_error,
    deep_link_identity_error,
    project_density_and_zoom,
    projectable_member_refs,
    restore_return_context,
)
from mm_r5.s6_validator import (
    validate_canonical_return_state,
    validate_density_zoom_projection,
    validate_deep_link_identity,
    validate_return_context,
)
from s6_runtime_fixtures import (
    as_mapping,
    build_canonical,
    build_deep_link,
    build_ephemeral,
    build_return_context_fixture,
    build_subject_packet,
    build_subject_workspace_packet,
)


def test_deep_link_is_built_from_one_verified_projectable_target() -> None:
    subject = build_subject_packet()
    workspace = build_subject_workspace_packet()
    link = build_deep_link()
    refs = projectable_member_refs(subject)

    assert link.project_ref == subject.projection.scope_identity.project_ref
    assert link.run_ref == subject.projection.scope_identity.run_ref
    assert link.snapshot_ref == subject.projection.scope_identity.snapshot_ref
    assert link.subject_ref == subject.projection.scope_identity.subject_ref
    assert link.risk_ref in refs["risk"]
    assert link.event_ref in refs["event"]
    assert link.visit_ref in refs["visit"]
    assert link.risk_anchor_ref in refs["risk_anchor"]
    assert link.source_locator_ref in refs["source_locator"]
    result = validate_deep_link_identity(link, subject)
    assert result.ok and result.projection == "emitted"

    rebuilt = build_deep_link_identity(
        subject,
        workspace,
        target_kind="risk_inspector",
        view="timeline",
        axis_mode="calendar",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 3, 31),
        risk_ref=link.risk_ref,
        event_ref=link.event_ref,
        risk_anchor_ref=link.risk_anchor_ref,
        visit_ref=link.visit_ref,
        source_locator_ref=link.source_locator_ref,
        return_context_key="return::s6::alternate",
    )
    assert rebuilt.target_kind == "risk_inspector"
    assert rebuilt.view == "timeline"
    assert rebuilt.return_context_key == "return::s6::alternate"
    assert rebuilt.spine_ref == link.spine_ref


def test_deep_link_rejects_identity_drift_and_nearest_fallback() -> None:
    subject = build_subject_packet()
    link = build_deep_link()
    candidate = as_mapping(link)
    candidate["project_ref"] = "project-unprojectable"
    assert deep_link_identity_error(candidate, subject) == "DEEP_LINK_TARGET_NOT_PROJECTABLE"
    assert validate_deep_link_identity(candidate, subject).projection == "not_emitted"

    adjacent = as_mapping(link)
    adjacent["subject_ref"] = "subject-adjacent"
    assert deep_link_identity_error(adjacent, subject) == "NEAREST_FALLBACK_FORBIDDEN"

    with pytest.raises(S6NavigationError) as error:
        build_deep_link_identity(subject, build_subject_workspace_packet(), fallback_policy="nearest")
    assert error.value.code == "NEAREST_FALLBACK_FORBIDDEN"

    with pytest.raises(S6NavigationError) as error:
        build_deep_link_identity(
            subject,
            build_subject_workspace_packet(),
            risk_anchor_ref="risk-anchor::missing",
        )
    assert error.value.code == "DEEP_LINK_ANCHOR_NOT_MEMBER"

    with pytest.raises(S6NavigationError) as error:
        build_deep_link_identity(
            subject,
            build_subject_workspace_packet(),
            axis_mode="study_day",
        )
    assert error.value.code == "DEEP_LINK_TARGET_NOT_PROJECTABLE"


def test_canonical_and_ephemeral_return_state_restore_separately() -> None:
    subject = build_subject_packet()
    workspace = build_subject_workspace_packet()
    link = build_deep_link()
    canonical = build_canonical()
    ephemeral = build_ephemeral()
    context = build_return_context(canonical, ephemeral)

    assert canonical_state_error(canonical, subject, workspace) is None
    assert validate_canonical_return_state(canonical, subject).ok
    restored = restore_return_context(
        context,
        subject,
        expected_return_context_key=link.return_context_key,
        expected_canonical=canonical,
        workspace=workspace,
    )
    assert restored == context
    assert restored.restoration_outcome == "restored"
    assert restored.canonical == canonical
    assert restored.ephemeral == ephemeral
    assert validate_return_context(restored, subject, expected=context).ok

    changed_ephemeral = as_mapping(context)
    changed_ephemeral["ephemeral"]["focus_ref"] = "focus::different"
    restored_with_changed_ephemeral = restore_return_context(
        changed_ephemeral,
        subject,
        expected_return_context_key=link.return_context_key,
        expected_canonical=canonical,
        workspace=workspace,
    )
    # The lower-level restore helper restores canonical identity and carries
    # a valid ephemeral presentation state; expected-context equivalence is
    # enforced by the focused validator below.
    assert restored_with_changed_ephemeral.restoration_outcome == "restored"
    assert restored_with_changed_ephemeral.canonical == canonical
    assert restored_with_changed_ephemeral.ephemeral.focus_ref == "focus::different"
    validation = validate_return_context(
        changed_ephemeral, subject, expected=as_mapping(context)
    )
    assert validation.primary_code == "EPHEMERAL_STATE_IN_CANONICAL_HASH"
    assert validation.projection == "not_restored"


def test_canonical_state_requires_identity_and_membership_before_emission() -> None:
    subject = build_subject_packet()
    canonical = as_mapping(build_canonical())
    canonical["selection_anchor"]["selected_event_ref"] = "event::other"
    assert canonical_state_error(canonical, subject) == "RETURN_ANCHOR_NOT_MEMBER"
    assert validate_canonical_return_state(canonical, subject).projection == "not_emitted"

    canonical = as_mapping(build_canonical())
    canonical["deep_link_identity"]["subject_ref"] = "subject-adjacent"
    assert canonical_state_error(canonical, subject) == "NEAREST_FALLBACK_FORBIDDEN"

    canonical = as_mapping(build_canonical())
    canonical["canonical_state_hash"] = "f" * 64
    result = validate_canonical_return_state(canonical, subject)
    assert result.primary_code == "CANONICAL_STATE_HASH_MISMATCH"
    assert result.projection == "not_emitted"

    with pytest.raises(S6NavigationError) as error:
        build_canonical_return_state(build_deep_link(), axis_mode="study_day")
    assert error.value.code == "DEEP_LINK_IDENTITY_MISMATCH"


@pytest.mark.parametrize("level", ("overview", "detail", "evidence"))
@pytest.mark.parametrize("density", ("standard", "high"))
def test_density_and_semantic_zoom_preserve_identity_and_required_risks(
    level: str, density: str,
) -> None:
    subject = build_subject_packet()
    workspace = build_subject_workspace_packet()
    zoom = build_semantic_zoom_state(level, density)
    projection = project_density_and_zoom(subject, zoom, workspace)
    validation = validate_density_zoom_projection(projection, subject)

    expected_events = tuple(item.event_ref for item in subject.projection.events)
    expected_risks = tuple(item.risk_anchor_ref for item in subject.projection.risk_anchors)
    assert validation.ok and validation.projection == "emitted"
    assert projection.visible_event_refs == expected_events
    assert projection.visible_risk_anchor_refs == expected_risks
    assert projection.spacing_units == (1 if density == "high" else 2)
    assert all(item.aggregated is False for item in projection.risk_anchor_items)
    assert all(item.event_shape != "double_chevron_badge" for item in projection.event_items)

    required_events = {
        item.event_ref
        for item in subject.projection.risk_anchors
        if item.severity in {"critical", "high", "medium"}
    }
    assert required_events <= set(projection.visible_event_refs)
    if level in {"detail", "evidence"}:
        assert projection.aggregated_event_refs == ()

    if level == "overview":
        expected_locators = {
            ref for item in subject.projection.risk_anchors for ref in item.source_locator_refs
        }
    elif level == "detail":
        expected_locators = {
            ref for item in subject.projection.events for ref in item.source_locator_refs
        }
        expected_locators |= {
            ref for item in subject.projection.risk_anchors for ref in item.source_locator_refs
        }
    else:
        expected_locators = {item.locator_ref for item in subject.projection.source_locators}
    assert set(projection.source_locator_refs) == expected_locators


def test_density_only_changes_spacing_and_zoom_policy_is_closed() -> None:
    subject = build_subject_packet()
    workspace = build_subject_workspace_packet()
    standard = project_density_and_zoom(
        subject, build_semantic_zoom_state("overview", "standard"), workspace
    )
    high = project_density_and_zoom(
        subject, build_semantic_zoom_state("overview", "high"), workspace
    )
    assert standard.visible_event_refs == high.visible_event_refs
    assert standard.visible_risk_anchor_refs == high.visible_risk_anchor_refs
    assert standard.aggregated_event_refs == high.aggregated_event_refs
    assert standard.source_locator_refs == high.source_locator_refs
    assert high.spacing_units < standard.spacing_units

    with pytest.raises(S6NavigationError) as error:
        build_semantic_zoom_state("summary", "standard")
    assert error.value.code == "SEMANTIC_ZOOM_POLICY_MISMATCH"
