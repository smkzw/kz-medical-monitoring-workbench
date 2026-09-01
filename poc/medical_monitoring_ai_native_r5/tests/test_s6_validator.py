"""Focused fail-closed tests for the S6 validators and offline corpus."""

from __future__ import annotations

import copy
import dataclasses

import pytest

from mm_r5.s6_accessibility import build_keyboard_contract
from mm_r5.s6_contracts import (
    build_audience_encoding_registry,
    build_audience_encoding_registry_mapping,
    build_density_semantic_zoom_contract,
    build_performance_corpus_identity,
    build_performance_profile,
    build_performance_registry,
    build_protected_boundary,
)
from mm_r5.s6_navigation import build_semantic_zoom_state
from mm_r5.s6_validator import (
    validate_audience_encoding_registry,
    validate_canonical_return_state,
    validate_density_semantic_zoom_contract,
    validate_density_zoom_projection,
    validate_deep_link_identity,
    validate_keyboard_contract,
    validate_performance_corpus_identity,
    validate_performance_corpus_records,
    validate_performance_profile,
    validate_protected_boundary,
    validate_return_context,
    validate_s6,
    validate_semantic_zoom_state,
)
from s6_runtime_fixtures import (
    as_mapping,
    build_canonical,
    build_deep_link,
    build_performance_corpus,
    build_return_context_fixture,
    build_subject_packet,
    build_zoom_projection,
)


def test_valid_typed_and_mapping_candidates_emit_expected_states() -> None:
    subject = build_subject_packet()
    link = build_deep_link()
    canonical = build_canonical()
    context = build_return_context_fixture()

    assert validate_deep_link_identity(link, subject, expected=link).ok
    assert validate_deep_link_identity(as_mapping(link), subject, expected=link).ok
    assert validate_canonical_return_state(canonical, subject, expected=canonical).ok
    assert validate_canonical_return_state(as_mapping(canonical), subject, expected=canonical).ok
    assert validate_return_context(context, subject, expected=context).ok
    assert validate_return_context(as_mapping(context), subject, expected=context).ok
    assert validate_s6(link, subject).ok
    assert validate_s6(context, subject).ok


def test_valid_zoom_keyboard_encoding_and_density_projection_emit() -> None:
    subject = build_subject_packet()
    for level in ("overview", "detail", "evidence"):
        for density in ("standard", "high"):
            zoom = build_semantic_zoom_state(level, density)
            assert validate_semantic_zoom_state(zoom).ok
            assert validate_density_zoom_projection(
                build_zoom_projection(level, density), subject
            ).ok

    assert validate_density_semantic_zoom_contract(
        build_density_semantic_zoom_contract()
    ).ok
    keyboard = build_keyboard_contract()
    assert validate_keyboard_contract(keyboard).ok
    assert validate_keyboard_contract(as_mapping(keyboard)).ok
    assert validate_s6(keyboard).ok
    assert validate_audience_encoding_registry(
        build_audience_encoding_registry()
    ).ok
    assert validate_audience_encoding_registry(
        build_audience_encoding_registry_mapping()
    ).ok


def test_valid_performance_identity_records_profile_and_boundary_emit() -> None:
    identity = build_performance_corpus_identity()
    records = build_performance_corpus()
    profile = build_performance_profile()
    registry = build_performance_registry()

    assert validate_performance_corpus_identity(identity).ok
    assert validate_performance_corpus_identity(as_mapping(identity)).ok
    assert validate_performance_corpus_records(records).ok
    assert validate_performance_profile(profile).ok
    assert validate_performance_profile(registry).ok
    assert validate_protected_boundary(build_protected_boundary()).ok
    assert identity.event_count == 1000
    assert identity.indicator_count == 40
    assert identity.risk_anchor_count == 300
    assert len(records) == 1340


def test_deep_link_and_return_hash_or_membership_drift_fail_closed() -> None:
    subject = build_subject_packet()
    link = as_mapping(build_deep_link())
    link["target_projection_content_hash"] = "f" * 64
    result = validate_deep_link_identity(link, subject)
    assert result.primary_code == "DEEP_LINK_ARTIFACT_MISSING"
    assert result.projection == "not_emitted"

    canonical = as_mapping(build_canonical())
    canonical["canonical_state_hash"] = "0" * 64
    result = validate_canonical_return_state(canonical, subject)
    assert result.primary_code == "CANONICAL_STATE_HASH_MISMATCH"
    assert result.projection == "not_emitted"

    context = as_mapping(build_return_context_fixture())
    context["canonical"]["selection_anchor"]["selected_event_ref"] = "event::missing"
    result = validate_return_context(context, subject)
    assert result.primary_code == "RETURN_ANCHOR_NOT_MEMBER"
    assert result.projection == "not_restored"


def test_zoom_keyboard_encoding_and_boundary_drift_fail_closed() -> None:
    zoom = as_mapping(build_semantic_zoom_state("overview", "standard"))
    zoom["source_locator_policy"] = "all_projectable"
    result = validate_semantic_zoom_state(zoom)
    assert result.primary_code == "SEMANTIC_ZOOM_POLICY_MISMATCH"
    assert result.projection == "not_emitted"

    projection = build_zoom_projection("detail", "standard")
    hidden = dataclasses.replace(projection, visible_risk_anchor_refs=())
    result = validate_density_zoom_projection(hidden, build_subject_packet())
    assert result.primary_code == "DENSITY_REQUIRED_RISK_HIDDEN"
    assert result.projection == "not_emitted"

    keyboard = as_mapping(build_keyboard_contract())
    keyboard["bindings"][0]["medical_state_mutation"] = True
    result = validate_keyboard_contract(keyboard)
    assert result.primary_code == "KEYBOARD_MEDICAL_STATE_MUTATION"
    assert result.projection == "not_emitted"

    audience = copy.deepcopy(build_audience_encoding_registry_mapping())
    audience["domain_items"][0]["event_shape"] = "double_chevron_badge"
    result = validate_audience_encoding_registry(audience)
    assert result.primary_code == "NON_COLOUR_ENCODING_INCOMPLETE"
    assert result.projection == "not_emitted"

    boundary = copy.deepcopy(build_protected_boundary())
    boundary["protected_boundaries"]["production_paths_written"] = True
    result = validate_protected_boundary(boundary)
    assert result.primary_code == "PROTECTED_BOUNDARY_DRIFT"
    assert result.projection == "not_emitted"


def test_performance_identity_profile_and_records_reject_drift() -> None:
    identity = as_mapping(build_performance_corpus_identity())
    identity["event_count"] = 999
    result = validate_performance_corpus_identity(identity)
    assert result.primary_code == "PERFORMANCE_CORPUS_IDENTITY_MISMATCH"
    assert result.projection == "not_emitted"

    profile = copy.deepcopy(build_performance_registry())
    profile["result_state"] = "measured_pass"
    result = validate_performance_profile(profile)
    assert result.primary_code == "PERFORMANCE_RESULT_PREMATURE"
    assert result.projection == "not_emitted"

    records = list(build_performance_corpus())
    records[-1] = dataclasses.replace(records[-1], ordinal=298)
    result = validate_performance_corpus_records(records)
    assert result.primary_code == "PERFORMANCE_CORPUS_IDENTITY_MISMATCH"
    assert result.projection == "not_emitted"

    result = validate_performance_corpus_records(records[:-1])
    assert result.primary_code == "PERFORMANCE_CORPUS_IDENTITY_MISMATCH"
    assert result.projection == "not_emitted"


@pytest.mark.parametrize(
    ("level", "density"),
    (("overview", "standard"), ("detail", "high"), ("evidence", "standard")),
)
def test_zoom_projection_round_trips_through_validator(level: str, density: str) -> None:
    projection = build_zoom_projection(level, density)
    result = validate_density_zoom_projection(projection, build_subject_packet())
    assert result.ok
    assert result.expected is None
    assert result.projection_state == "emitted"
