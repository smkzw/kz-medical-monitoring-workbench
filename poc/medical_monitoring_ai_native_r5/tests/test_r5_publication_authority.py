"""Focused tests for the R5 publication authority input/bridge seam."""

from __future__ import annotations

from dataclasses import dataclass, replace
from unittest.mock import Mock

import pytest

from packages.medical_monitoring.projections.publication import s4_contracts as s4
from packages.medical_monitoring.projections.publication.r5_publication_authority import (
    R5AuthorityPacket,
    R5PublicationAuthorityBridge,
    R5PublicationAuthorityError,
    R5PublicationAuthorityInputAssembler,
    R5PublicationRunIdentity,
)
from packages.medical_monitoring.projections.publication.s4_projection import build_s4_authority_packet
from packages.medical_monitoring.projections.publication.s4_validator import validate_s4_authority_packet
from s4_runtime_fixtures import build_runtime_input


@dataclass(frozen=True)
class TypedSubject:
    subject_ref: str
    site_ref: str
    spine_ref: str


@dataclass(frozen=True)
class TypedSite:
    site_ref: str


@dataclass(frozen=True)
class TypedEvent:
    event_ref: str
    subject_ref: str
    site_ref: str
    spine_ref: str


@dataclass(frozen=True)
class TypedVisit:
    visit_ref: str
    subject_ref: str
    site_ref: str
    spine_ref: str


@dataclass(frozen=True)
class TypedSource:
    locator_ref: str
    snapshot_ref: str
    source_revision_ref: str
    source_revision_content_hash: str



def _identity() -> R5PublicationRunIdentity:
    return R5PublicationRunIdentity(
        project_ref="project.p1",
        run_ref="run.r1",
        public_run_token="public-run-1",
        snapshot_ref="snap.s1",
        cutoff_ref="cutoff.v1",
        site_refs=("site.01",),
        snapshot_token="snapshot-option-1",
    )


def _members(runtime_input: s4.R5S4RuntimeInput):
    risk = runtime_input.anchor.accepted_risk_identity
    source_pair = runtime_input.authority_receipt.source_revision_content_pairs[0]
    return {
        "accepted_subjects": (
            TypedSubject(risk.subject_ref or "", risk.site_ref or "", risk.spine_ref),
        ),
        "accepted_sites": (TypedSite(risk.site_ref or ""),),
        "accepted_events": (
            TypedEvent(
                runtime_input.deep_link_state.event_ref,
                risk.subject_ref or "",
                risk.site_ref or "",
                risk.spine_ref,
            ),
        ),
        "accepted_visits": (
            TypedVisit(
                runtime_input.deep_link_state.visit_ref,
                risk.subject_ref or "",
                risk.site_ref or "",
                risk.spine_ref,
            ),
        ),
        "accepted_sources": (
            TypedSource(
                runtime_input.deep_link_state.source_locator_ref,
                runtime_input.authority_receipt.snapshot_ref,
                source_pair.revision_id,
                source_pair.content_hash,
            ),
        ),
    }


def _assembled(runtime_input=None):
    runtime_input = runtime_input or build_runtime_input("single_analysis")
    return R5PublicationAuthorityInputAssembler().assemble(
        _identity(),
        runtime_input=runtime_input,
        **_members(runtime_input),
    )


def test_assembler_accepts_only_injected_typed_identity_and_bytes():
    runtime_input = build_runtime_input("single_analysis")
    assembled = _assembled(runtime_input)

    assert assembled.runtime_inputs == (runtime_input,)
    assert assembled.raw_bytes[0].attempt_id == "a1"
    assert assembled.raw_bytes[0].raw_bytes == runtime_input.raw_outputs[0].raw_bytes
    assert assembled.subjects[0].subject_ref == "subject.1001"

    with pytest.raises(R5PublicationAuthorityError) as excinfo:
        R5PublicationAuthorityInputAssembler().assemble(
            _identity(),
            runtime_input=runtime_input,
            accepted_subjects=({"subject_ref": "subject.1001"},),
            **{
                key: value
                for key, value in _members(runtime_input).items()
                if key != "accepted_subjects"
            },
        )
    assert excinfo.value.code == "TYPED_AUTHORITY_REQUIRED"


def test_bridge_calls_existing_s4_builder_then_validator_and_is_deterministic(monkeypatch):
    runtime_input = build_runtime_input("single_analysis")
    assembled = _assembled(runtime_input)
    real_builder = build_s4_authority_packet
    builder = Mock(side_effect=real_builder)
    validator = Mock(side_effect=validate_s4_authority_packet)
    monkeypatch.setattr("mm_r5.r5_publication_authority.s4_projection.build_s4_authority_packet", builder)
    monkeypatch.setattr("mm_r5.r5_publication_authority.s4_validator.validate_s4_authority_packet", validator)

    packet = R5PublicationAuthorityBridge().build(assembled)
    replay = R5PublicationAuthorityBridge().build(assembled)

    assert isinstance(packet, R5AuthorityPacket)
    assert packet.project_ref == "project.p1"
    assert packet.site_refs == ("site.01",)
    assert packet.s4_packet_ids == (packet.s4_packets[0].packet_id,)
    assert packet.packet_digest == replay.packet_digest
    assert packet.packet_identity == "r5-publication-authority:" + packet.packet_digest
    assert builder.call_count == 2
    assert validator.call_count == 2
    assert validator.call_args_list[0].args[1] is runtime_input


def test_bridge_rejects_s4_validation_without_emitting_aggregate(monkeypatch):
    runtime_input = build_runtime_input("single_analysis")
    assembled = _assembled(runtime_input)
    candidate = build_s4_authority_packet(runtime_input)
    rejected = s4.R5S4ValidationResult(ok=False, issues=(), expected_packet=candidate)
    monkeypatch.setattr(
        "mm_r5.r5_publication_authority.s4_projection.build_s4_authority_packet",
        lambda _: candidate,
    )
    monkeypatch.setattr(
        "mm_r5.r5_publication_authority.s4_validator.validate_s4_authority_packet",
        lambda *_: rejected,
    )

    with pytest.raises(R5PublicationAuthorityError) as excinfo:
        R5PublicationAuthorityBridge().build(assembled)
    assert excinfo.value.code == "S4_VALIDATION_REJECTED"


def test_assembler_rejects_raw_byte_drift_and_bridge_rejects_member_escape():
    runtime_input = build_runtime_input("single_analysis")
    members = _members(runtime_input)
    with pytest.raises(R5PublicationAuthorityError) as excinfo:
        R5PublicationAuthorityInputAssembler().assemble(
            _identity(),
            runtime_input=runtime_input,
            raw_bytes=(
                type(runtime_input.raw_outputs[0])(
                    attempt_id="a1",
                    artifact_id=runtime_input.raw_outputs[0].artifact_id,
                    raw_format=runtime_input.raw_outputs[0].raw_format,
                    raw_bytes=b"tampered",
                ),
            ),
            **members,
        )
    assert excinfo.value.code == "RAW_BYTES_MISMATCH"

    escaped = replace(members["accepted_events"][0], site_ref="site.foreign")
    with pytest.raises(R5PublicationAuthorityError) as excinfo:
        R5PublicationAuthorityInputAssembler().assemble(
            _identity(),
            runtime_input=runtime_input,
            accepted_events=(escaped,),
            **{key: value for key, value in members.items() if key != "accepted_events"},
        )
    assert excinfo.value.code == "SITE_COVERAGE_MISMATCH"


def test_explicit_product_factory_is_the_only_product_handoff():
    runtime_input = build_runtime_input("single_analysis")
    assembled = _assembled(runtime_input)
    product = TypedSubject("product", "site.01", "spine.product")
    factory = Mock(return_value=product)

    packet = R5PublicationAuthorityBridge(product_packet_factory=factory).build(assembled)

    assert packet.product_packet is product
    assert factory.call_count == 1
    factory_input = factory.call_args.args[0]
    assert factory_input.product_packet is None
    assert factory_input.packet_digest == packet.packet_digest
    with pytest.raises(R5PublicationAuthorityError) as excinfo:
        R5PublicationAuthorityBridge(product_packet_factory=lambda _: object()).build(assembled)
    # The invalid factory is reached only after S4/member checks; this call
    # proves that an implicit fixture fallback is not used.
    assert excinfo.value.code == "TYPED_AUTHORITY_REQUIRED"
