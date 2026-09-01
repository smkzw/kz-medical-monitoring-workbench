"""Focused tests for the accepted renderer-neutral R5-S6 contract surface."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path

import pytest

from mm_r5.s6_accessibility import validate_keyboard_non_mutating
from mm_r5 import s6_contracts as s6
from s6_runtime_fixtures import (
    as_mapping,
    build_canonical,
    build_deep_link,
    build_keyboard,
    build_performance_corpus,
)


_WORKSPACE = Path(__file__).resolve().parents[3]
_ARTIFACTS = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1"
)


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_contract_identity_and_object_fields_are_exact() -> None:
    contract = _json(_ARTIFACTS / "exact_contract.json")

    assert contract["schema"] == s6.S6_SCHEMA
    assert contract["schema_version"] == s6.S6_SCHEMA_VERSION
    assert contract["contract_id"] == s6.S6_CONTRACT_ID
    assert contract["contract_content_hash"] == s6.S6_CONTRACT_CONTENT_HASH
    assert s6.S6_ACCEPTANCE_TOKEN == "ACCEPT_R5_S6_CONTRACT_V0_1"
    assert s6.S6_AUTHORITY_MODE == "synthetic_offline_test_only"
    assert s6.S6_FALLBACK_POLICY == "none"
    assert contract["renderer_neutral"] is True
    assert contract["contract_only"] is True

    for name, field_specs in contract["objects"].items():
        cls = getattr(s6, name)
        assert dataclasses.is_dataclass(cls), name
        actual = {field.name for field in dataclasses.fields(cls)}
        assert actual == set(field_specs), name
        assert len(actual) == len(field_specs), name


def test_closed_vocabularies_and_contract_tables_match_artifact() -> None:
    contract = _json(_ARTIFACTS / "exact_contract.json")
    enums = contract["enums"]

    actual_enums = {
        "aggregation_policy": s6.AGGREGATION_POLICIES,
        "axis_mode": s6.AXIS_MODES,
        "benchmark_statistic": s6.BENCHMARK_STATISTICS,
        "change_kind": s6.CHANGE_KINDS,
        "cutoff_state": s6.CUTOFF_STATES,
        "date_state": s6.DATE_STATES,
        "density_mode": s6.DENSITY_MODES,
        "domain": s6.DOMAINS,
        "event_shape": s6.EVENT_SHAPES,
        "fallback_policy": s6.FALLBACK_POLICIES,
        "journey_subtype": s6.JOURNEY_SUBTYPES,
        "keyboard_action": s6.KEYBOARD_ACTIONS,
        "keyboard_key": s6.KEYBOARD_KEYS,
        "keyboard_scope": s6.KEYBOARD_SCOPES,
        "line_style": s6.LINE_STYLES,
        "performance_mode": s6.PERFORMANCE_MODES,
        "performance_result_state": s6.PERFORMANCE_RESULT_STATES,
        "restoration_outcome": s6.RESTORATION_OUTCOMES,
        "risk_visibility_policy": s6.RISK_VISIBILITY_POLICIES,
        "semantic_zoom_level": s6.SEMANTIC_ZOOM_LEVELS,
        "severity": s6.SEVERITIES,
        "sort_direction": s6.SORT_DIRECTIONS,
        "sort_key": s6.SORT_KEYS,
        "source_locator_policy": s6.SOURCE_LOCATOR_POLICIES,
        "target_kind": s6.TARGET_KINDS,
        "view": s6.VIEWS,
    }
    assert set(actual_enums) == set(enums)
    for name, values in actual_enums.items():
        # The machine artifact stores enum members in sorted JSON order;
        # tuple order in the runtime constants is the contract's display/
        # traversal order and is not itself an identity field.
        assert set(values) == set(enums[name]), name
        assert len(values) == len(enums[name]), name

    assert s6.DOMAIN_SUBTYPE_MATRIX == {
        "ae": ("ae",),
        "mh": ("mh",),
        "cm": ("concomitant_medication",),
        "ip": ("ip_dose", "ip_pause", "ip_resume"),
        "lab_exam": ("lab", "exam"),
        "hospital_procedure": ("hospitalization", "procedure"),
        "symptom_efficacy": ("symptom", "efficacy", "scale", "outcome", "trend"),
        "protocol_compliance": ("protocol_deviation",),
    }


def test_canonical_hashing_and_typed_values_are_immutable() -> None:
    left = {"b": "e\u0301", "a": (date(2026, 8, 26),)}
    right = {"a": [date(2026, 8, 26)], "b": "é"}
    assert s6.s6_canonical_json(left) == s6.s6_canonical_json(right)
    assert s6.s6_sha256(left) == s6.s6_sha256(right)
    assert s6.is_sha256_hex(s6.s6_sha256(left))
    assert not s6.is_sha256_hex("A" * 64)

    link = build_deep_link()
    canonical = build_canonical()
    assert canonical.canonical_state_hash == s6.s6_canonical_state_hash(canonical)
    assert dataclasses.is_dataclass(link) and dataclasses.is_dataclass(canonical)
    with pytest.raises(FrozenInstanceError):
        link.project_ref = "project-mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        canonical.axis_mode = "study_day"  # type: ignore[misc]


def test_factory_registry_hashes_and_performance_identity_are_frozen() -> None:
    encoding = s6.build_audience_encoding_registry()
    assert tuple(item.domain for item in encoding.domain_items) == s6.DOMAINS
    assert tuple(item.event_shape for item in encoding.domain_items) == tuple(
        s6.DOMAIN_ENCODING[domain][0] for domain in s6.DOMAINS
    )
    assert tuple(item.line_style for item in encoding.domain_items) == tuple(
        s6.DOMAIN_ENCODING[domain][1] for domain in s6.DOMAINS
    )
    assert encoding.risk_overlay.shape not in {
        item.event_shape for item in encoding.domain_items
    }
    assert encoding.content_hash == s6.S6_AUDIENCE_ENCODING_CONTENT_HASH
    assert s6.s6_audience_encoding_hash(encoding) == encoding.content_hash

    identity = s6.build_performance_corpus_identity()
    profile = s6.build_performance_profile()
    registry = s6.build_performance_registry()
    artifact = _json(_ARTIFACTS / "performance_corpus_registry.json")
    assert as_mapping(identity) == as_mapping(profile.corpus)
    assert identity.event_count == 1000
    assert identity.indicator_count == 40
    assert identity.risk_anchor_count == 300
    assert identity.content_hash == s6.S6_CORPUS_CONTENT_HASH
    assert registry == artifact
    assert profile.result_state == "unmeasured_contract_only"
    assert profile.modes == ("cold", "warm")
    assert profile.samples_per_mode == 7
    assert profile.viewport == (1440, 900)
    assert len(build_performance_corpus()) == 1340


def test_future_runtime_manifest_is_exactly_synthetic_and_unaccepted() -> None:
    manifest = _json(_ARTIFACTS / "manifest.json")
    allowlist = manifest["future_runtime_allowlist"]
    paths = tuple(item["path"] for item in allowlist)
    expected = (
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_contracts.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_navigation.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_accessibility.py",
        "poc/medical_monitoring_ai_native_r5/src/mm_r5/s6_validator.py",
        "poc/medical_monitoring_ai_native_r5/tests/s6_runtime_fixtures.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_s6_contracts.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_s6_navigation.py",
        "poc/medical_monitoring_ai_native_r5/tests/test_s6_validator.py",
        "poc/medical_monitoring_ai_native_r5/tests/challenges/test_s6_runtime_challenges.py",
        "poc/medical_monitoring_ai_native_r5/evidence/r4_r5_s6_navigation_readonly_sha256.json",
    )
    assert paths == expected
    assert manifest["counts"]["future_runtime_allowlist_paths"] == 10
    assert manifest["status"] == "candidate_unaccepted"
    assert manifest["acceptance_token_emitted"] is False
    assert manifest["self_acceptance"] is False
    assert manifest["unlock"]["future_runtime_kind"] == "synthetic_offline_renderer_neutral_only"
    assert manifest["unlock"]["does_not_unlock"] == [
        "frontend", "browser", "services", "real projects", "real models",
        "security", "medical-writing", "8911",
    ]
    for item in allowlist:
        assert item["create_only"] is True
        assert item["browser"] is False
        assert item["real_project_or_model"] is False
        assert item["starts_8911"] is False


def test_density_and_zoom_policy_preserves_required_risk() -> None:
    policy = s6.build_density_semantic_zoom_contract()
    assert tuple(policy["desktop_min_viewport"]) == s6.S6_MIN_VIEWPORT
    assert set(policy["semantic_zoom_levels"]) == set(s6.SEMANTIC_ZOOM_LEVELS)
    assert len(policy["invariants"]) == 5
    assert "all critical/high/medium risk anchors remain individually represented at every semantic zoom level" in policy["invariants"]


def test_keyboard_factory_has_all_sixteen_non_mutating_bindings() -> None:
    keyboard = build_keyboard()
    assert len(keyboard.bindings) == 16
    assert validate_keyboard_non_mutating(keyboard)
    assert all(item.medical_state_mutation is False for item in keyboard.bindings)
    assert tuple(item.key for item in keyboard.bindings) == (
        "Tab", "Shift+Tab", "Enter", "Space", "Escape", "ArrowUp", "ArrowDown",
        "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home", "End", "+", "-", "0",
    )


def test_runtime_evidence_binds_frozen_and_created_paths() -> None:
    evidence_path = _WORKSPACE / "poc" / "medical_monitoring_ai_native_r5" / "evidence" / (
        "r4_r5_s6_navigation_readonly_sha256.json"
    )
    evidence = _json(evidence_path)
    assert evidence["schema"] == (
        "medical-monitoring-r5-s6-navigation-density-accessibility-runtime-readonly-sha256-evidence-v1"
    )
    assert evidence["challenge_coverage"]["registry_row_count"] == 104
    assert evidence["challenge_coverage"]["executed_row_count"] == 104
    assert evidence["performance_corpus"] == {
        "events": 1000,
        "indicators": 40,
        "risk_anchors": 300,
        "records": 1340,
        "identity_hash": "6b94a83fa3507b3c0ec0030f6b84e3916e081c436d2af771e8e5dbf46d85463b",
        "result_state": "unmeasured_contract_only",
        "explicit_matrix": "normal/-O/-OO all accepted all 1340 records",
    }
    assert evidence["protected_boundaries"]["port_8911"] == "stopped"
    assert evidence["protected_boundaries"]["acceptance_token_emitted"] is False
    for rel, expected in {
        **evidence["files"],
        **evidence["created_allowlist_sha256"],
    }.items():
        path = _WORKSPACE / rel
        assert path.exists(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, rel
