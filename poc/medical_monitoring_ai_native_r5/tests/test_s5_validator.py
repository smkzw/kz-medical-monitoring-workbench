"""Focused fail-closed tests for S5 packet, audience, and workspace validators."""

from __future__ import annotations

import copy

import pytest

from mm_r5.s5_contracts import s5_as_mapping
from mm_r5.s5_validator import (
    S5RuntimeImplementationError,
    validate_audience_encoding_registry,
    validate_audience_lexicon,
    validate_audience_term,
    validate_domain_subtype_pair,
    validate_legacy_severity,
    validate_legacy_treatment_mapping,
    validate_s5_packet,
    validate_s5_subject_workspace,
    validate_subject_temporal_packet,
)
from s5_runtime_fixtures import (
    build_aemh_packet,
    build_aemh_match_history_authority_bundle,
    build_subject_packet,
    build_subject_temporal_authority_bundle,
    build_subject_workspace,
)
from mm_r5.s5_contracts import (
    S5AEMHPacket,
    S5SubjectTemporalPacket,
    build_audience_encoding_registry,
    build_audience_lexicon,
)


def _replace(mapping: dict, path: str, value) -> None:
    target = mapping
    parts = [item for item in path.strip("/").split("/") if item]
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    leaf = parts[-1]
    if isinstance(target, list):
        target[int(leaf)] = value
    else:
        target[leaf] = value


def test_valid_subject_and_aemh_packets_emit_and_rebuild_expected_packets() -> None:
    subject_source = build_subject_temporal_authority_bundle()
    aemh_source = build_aemh_match_history_authority_bundle()
    subject = build_subject_packet()
    aemh = build_aemh_packet()

    subject_result = validate_subject_temporal_packet(subject, subject_source)
    aemh_result = validate_s5_packet(aemh, aemh_source)
    assert subject_result.ok and subject_result.projection == "emitted"
    assert aemh_result.ok and aemh_result.projection == "emitted"
    assert subject_result.expected_packet == subject
    assert aemh_result.expected_packet == aemh
    assert isinstance(subject_result.expected_packet, S5SubjectTemporalPacket)
    assert isinstance(aemh_result.expected_packet, S5AEMHPacket)


def test_mapping_candidate_is_equivalent_to_typed_candidate() -> None:
    source = build_subject_temporal_authority_bundle()
    packet = build_subject_packet()
    typed = validate_subject_temporal_packet(packet, source)
    mapped = validate_subject_temporal_packet(s5_as_mapping(packet), source)
    assert typed.ok and mapped.ok
    assert mapped.expected_packet == typed.expected_packet


def test_candidate_changes_are_rejected_and_expected_packet_is_source_rebuilt() -> None:
    source = build_subject_temporal_authority_bundle()
    packet = build_subject_packet()
    candidate = s5_as_mapping(packet)
    _replace(candidate, "/receipt/scope_identity/subject_ref", "subject-cross-scope")
    result = validate_subject_temporal_packet(candidate, source)
    assert not result.ok
    assert result.primary_code == "SCOPE_IDENTITY_MISMATCH"
    assert result.projection == "not_emitted"
    assert result.expected_packet == validate_subject_temporal_packet(packet, source).expected_packet


def test_cross_domain_pair_is_rejected_before_projection() -> None:
    result = validate_domain_subtype_pair("ae", "ip_dose")
    assert not result.ok
    assert result.primary_code == "DOMAIN_SUBTYPE_MISMATCH"
    assert result.projection == "not_emitted"
    assert result.issues[0].path == "/projection/events/0/subtype"


@pytest.mark.parametrize(
    ("domain", "subtype"),
    (
        ("ae", "ae"), ("mh", "mh"), ("cm", "concomitant_medication"),
        ("ip", "ip_dose"), ("ip", "ip_pause"), ("ip", "ip_resume"),
        ("lab_exam", "lab"), ("lab_exam", "exam"),
        ("hospital_procedure", "hospitalization"),
        ("hospital_procedure", "procedure"),
        ("symptom_efficacy", "symptom"), ("symptom_efficacy", "efficacy"),
        ("symptom_efficacy", "scale"), ("symptom_efficacy", "outcome"),
        ("symptom_efficacy", "trend"),
        ("protocol_compliance", "protocol_deviation"),
    ),
)
def test_every_allowed_domain_subtype_pair_emits(domain: str, subtype: str) -> None:
    result = validate_domain_subtype_pair(domain, subtype)
    assert result.ok and result.projection == "emitted"


def test_unknown_domain_and_subtype_fail_closed() -> None:
    unknown_domain = validate_domain_subtype_pair("OTHER", "ae")
    unknown_subtype = validate_domain_subtype_pair("ae", "OTHER")
    assert unknown_domain.primary_code == "UNKNOWN_DOMAIN_FAIL_CLOSED"
    assert unknown_subtype.primary_code == "UNKNOWN_SUBTYPE_FAIL_CLOSED"
    assert unknown_domain.projection == unknown_subtype.projection == "not_emitted"


def test_audience_registry_rejects_domain_shape_severity_and_treatment_drift() -> None:
    registry = s5_as_mapping(build_audience_encoding_registry())
    cases = (
        ("/domain_items/7/domain", "ae", "DOMAIN_REGISTRY_NOT_BIJECTIVE"),
        ("/domain_items/6/event_shape", "triangle", "SYMPTOM_EFFICACY_SHAPE_COLLISION"),
        ("/domain_items/0/event_shape", "double_chevron_badge", "RISK_EVENT_SHAPE_COLLISION"),
        ("/severity_items/1/severity", "critical", "SEVERITY_PROMOTION"),
        ("/legacy_treatment_mapping/0/mapping_state", "mapped", "LEGACY_TREATMENT_FAIL_CLOSED"),
    )
    for path, value, code in cases:
        candidate = copy.deepcopy(registry)
        _replace(candidate, path, value)
        result = validate_audience_encoding_registry(candidate)
        assert result.primary_code == code, (path, result.issues)
        assert result.projection == "not_emitted"


def test_audience_lexicon_rejects_forbidden_term_and_preserves_hash_gate() -> None:
    lexicon = s5_as_mapping(build_audience_lexicon())
    assert validate_audience_term("已记录事项").primary_code == "FORBIDDEN_AUDIENCE_TERM"
    assert validate_audience_lexicon(lexicon).ok


def test_legacy_mappings_fail_closed() -> None:
    assert validate_legacy_severity("severe").ok
    assert validate_legacy_severity("moderate").ok
    assert validate_legacy_severity("mild").ok
    assert validate_legacy_severity("unknown").primary_code == "LEGACY_SEVERITY_FAIL_CLOSED"
    assert validate_legacy_treatment_mapping("background_treatment", "unmapped_fail_closed").ok
    assert validate_legacy_treatment_mapping("non_drug_treatment", "unmapped_fail_closed").ok
    assert validate_legacy_treatment_mapping("background_treatment", "mapped").primary_code == "LEGACY_TREATMENT_FAIL_CLOSED"


def test_workspace_validator_rejects_shared_spine_and_ui_authority_drift() -> None:
    subject = build_subject_packet()
    aemh = build_aemh_packet()
    workspace = build_subject_workspace()
    candidate = {"workspace": s5_as_mapping(workspace)}
    _replace(candidate, "/workspace/view_bindings/1/spine_ref", "spine-other")
    spine_result = validate_s5_subject_workspace(candidate, subject, aemh)
    assert spine_result.primary_code == "SHARED_SPINE_MISMATCH"
    assert spine_result.projection == "not_emitted"

    candidate = {"workspace": s5_as_mapping(workspace)}
    _replace(candidate, "/workspace/view_bindings/0/authority_projection_id", "projection-ui")
    ui_result = validate_s5_subject_workspace(candidate, subject, aemh)
    assert ui_result.primary_code == "UI_STATE_AS_AUTHORITY"


def test_validator_requires_typed_authority_bundle_and_never_accepts_candidate_source() -> None:
    packet = build_subject_packet()
    with pytest.raises(S5RuntimeImplementationError):
        validate_subject_temporal_packet(packet, s5_as_mapping(build_subject_temporal_authority_bundle()))
    with pytest.raises(S5RuntimeImplementationError):
        validate_s5_packet(packet, build_aemh_match_history_authority_bundle())
