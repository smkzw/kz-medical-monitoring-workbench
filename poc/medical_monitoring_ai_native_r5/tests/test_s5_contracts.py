"""Focused tests for the accepted R5-S5 typed contract surface."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path

import pytest

from mm_r5 import s5_contracts as s5
from s5_runtime_fixtures import (
    build_aemh_packet,
    build_subject_packet,
    build_subject_workspace,
)


_WORKSPACE = Path(__file__).resolve().parents[3]
_CONTRACT = _WORKSPACE / "artifacts" / (
    "medical_monitoring_r5_s5_subject_workspace_contract_v0_1/exact_contract.json"
)
_EVIDENCE = _WORKSPACE / "poc" / "medical_monitoring_ai_native_r5" / "evidence" / (
    "r4_r5_s5_subject_workspace_readonly_sha256.json"
)


def _contract() -> dict:
    return json.loads(_CONTRACT.read_text(encoding="utf-8"))


def test_contract_identity_and_object_fields_are_exact() -> None:
    contract = _contract()
    assert contract["schema"] == s5.S5_SCHEMA
    assert contract["schema_version"] == s5.S5_SCHEMA_VERSION
    assert contract["contract_id"] == s5.S5_CONTRACT_ID
    assert contract["contract_content_hash"] == s5.S5_CONTRACT_CONTENT_HASH
    assert s5.S5_ACCEPTANCE_TOKEN == "ACCEPT_R5_S5_CONTRACT"
    assert s5.S5_AUTHORITY_MODE == "synthetic_offline_test_only"
    assert s5.S5_FALLBACK_POLICY == "fail_closed_no_nearest"

    for name, field_specs in contract["objects"].items():
        cls = getattr(s5, name)
        assert dataclasses.is_dataclass(cls), name
        assert tuple(field.name for field in dataclasses.fields(cls)) == tuple(field_specs)


def test_closed_vocabularies_and_domain_subtype_matrix_are_exact() -> None:
    assert s5.AEMH_DOMAINS == ("ae", "mh")
    assert s5.APPLICABILITY_STATES == ("applicable", "not_applicable", "not_provided")
    assert s5.AXIS_MODES == ("calendar", "study_day")
    assert s5.CUTOFF_ENDPOINT_STATES == ("present", "absent")
    assert s5.CUTOFF_STATES == ("present", "absent")
    assert s5.DATE_GEOMETRIES == ("point", "closed_interval", "open_start", "open_end")
    assert s5.DATE_STATES == ("exact", "partial", "conflicted", "missing")
    assert s5.DOMAINS == (
        "ae", "mh", "cm", "ip", "lab_exam", "hospital_procedure",
        "symptom_efficacy", "protocol_compliance",
    )
    assert s5.EVENT_SHAPES == (
        "rounded_rect", "bookmark", "capsule", "hexagon", "square",
        "doorframe", "circle", "triangle", "single_flag",
    )
    assert s5.JOURNEY_SUBTYPES == (
        "ae", "mh", "concomitant_medication", "ip_dose", "ip_pause",
        "ip_resume", "lab", "exam", "hospitalization", "procedure",
        "symptom", "efficacy", "scale", "outcome", "trend",
        "protocol_deviation",
    )
    assert s5.DOMAIN_SUBTYPE_MATRIX == {
        "ae": ("ae",),
        "mh": ("mh",),
        "cm": ("concomitant_medication",),
        "ip": ("ip_dose", "ip_pause", "ip_resume"),
        "lab_exam": ("lab", "exam"),
        "hospital_procedure": ("hospitalization", "procedure"),
        "symptom_efficacy": ("symptom", "efficacy", "scale", "outcome", "trend"),
        "protocol_compliance": ("protocol_deviation",),
    }
    assert s5.RISK_OVERLAY_SHAPE == "double_chevron_badge"
    assert s5.LEGACY_SEVERITY_MAPPING == {
        "severe": "high", "moderate": "medium", "mild": "low",
    }


def test_canonical_hashing_is_stable_and_unicode_normalized() -> None:
    left = {"b": "e\u0301", "a": (date(2026, 8, 26),)}
    right = {"a": [date(2026, 8, 26)], "b": "é"}
    assert s5.s5_canonical_json(left) == s5.s5_canonical_json(right)
    assert s5.s5_sha256(left) == s5.s5_sha256(right)
    assert s5.is_sha256_hex(s5.s5_sha256(left))
    assert not s5.is_sha256_hex("A" * 64)
    assert not s5.is_sha256_hex("not-a-hash")


def test_typed_packets_and_workspace_are_frozen_and_hash_bound() -> None:
    subject = build_subject_packet()
    aemh = build_aemh_packet()
    workspace = build_subject_workspace()
    assert isinstance(subject, s5.S5SubjectTemporalPacket)
    assert isinstance(aemh, s5.S5AEMHPacket)
    assert isinstance(workspace, s5.S5SubjectWorkspaceContract)
    # Packet hashes are producer-authority hashes.  The adapter preserves
    # them; it does not re-sign the converted date-bearing S5 dataclasses.
    assert s5.is_sha256_hex(subject.packet_content_hash)
    assert s5.is_sha256_hex(aemh.packet_content_hash)
    assert workspace.content_hash == s5.s5_workspace_hash(workspace)

    with pytest.raises(FrozenInstanceError):
        subject.packet_content_hash = "0" * 64  # type: ignore[misc]


def test_audience_factories_have_closed_non_color_encoding() -> None:
    registry = s5.build_audience_encoding_registry()
    lexicon = s5.build_audience_lexicon()
    assert tuple(item.domain for item in registry.domain_items) == s5.DOMAINS
    assert tuple(item.event_shape for item in registry.domain_items) == tuple(
        s5.DOMAIN_ENCODING[domain][0] for domain in s5.DOMAINS
    )
    assert tuple(item.line_style for item in registry.domain_items) == tuple(
        s5.DOMAIN_ENCODING[domain][1] for domain in s5.DOMAINS
    )
    assert registry.risk_overlay_shape not in {
        item.event_shape for item in registry.domain_items
    }
    assert tuple(item.severity for item in registry.severity_items) == s5.SEVERITIES
    assert lexicon.forbidden_terms == s5.FORBIDDEN_AUDIENCE_TERMS
    assert lexicon.content_hash == s5.s5_sha256({
        "domain_items": registry.domain_items,
        "forbidden_terms": lexicon.forbidden_terms,
        "severity_items": registry.severity_items,
        "symptom_efficacy_subtypes": registry.symptom_efficacy_subtypes,
    })


def test_runtime_evidence_binds_frozen_and_created_paths() -> None:
    evidence = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["schema"] == (
        "medical-monitoring-r5-s5-subject-workspace-runtime-readonly-sha256-evidence-v1"
    )
    coverage = evidence["challenge_coverage"]
    assert coverage["structured_mutation_row_count"] == 250
    assert coverage["structured_oracle_row_count"] == 250
    assert coverage["unique_single_mutation_tuple_count"] == 250
    assert coverage["inherited_parent_metadata_rows"] == 204
    assert coverage["s5_specific_runtime_rows"] == 36
    assert coverage["accepted_public_graph_replay_rows"] == 10
    assert coverage["runtime_execution"]
    assert evidence["protected_boundaries"]["port_8911"] == "stopped_required"
    assert evidence["protected_boundaries"]["medical_writing_file_count"] == 542
    for rel, expected in {**evidence["files"], **evidence["created_allowlist_sha256"]}.items():
        path = _WORKSPACE / rel
        assert path.exists(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, rel
