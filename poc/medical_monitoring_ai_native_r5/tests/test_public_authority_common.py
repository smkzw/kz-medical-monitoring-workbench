"""Focused common-contract tests for the R5-S5 public producers."""

from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from typing import get_type_hints

import pytest

from mm_r5 import public_authority_common as common
from mm_r5.aemh_match_history_public import (
    AEMHMatchHistoryAuthorityPacket,
    build_aemh_match_history_authority,
)
from mm_r5.subject_temporal_public import (
    SubjectTemporalAuthorityPacket,
    build_subject_temporal_authority,
)
from public_authority_runtime_fixtures import (
    build_aemh_authority_bundle,
    build_subject_authority_bundle,
)


def test_common_records_are_frozen_dataclasses() -> None:
    """Authority and shared packet records cannot become mutable state."""
    record_types = (
        common.AEMHDecisionInputV02,
        common.AEMHThreadInputV02,
        common.AxisInputV02,
        common.CutoffEndpointBindingV02,
        common.DomainInputV02,
        common.EndpointInputV02,
        common.IdentityScopeInputV02,
        common.LocatorInputV02,
        common.PhaseInputV02,
        common.RevisionInputV02,
        common.RiskInputV02,
        common.ScopeInputV02,
        common.SubjectEventInputV02,
        common.VisitInputV02,
        common.SubjectFullGraphInputV02,
        common.AEMHFullGraphInputV02,
        common.AuthorityBundleV02,
        common.PublicScopeIdentity,
        common.PublicCutoffEndpoint,
        common.PublicSourceLocator,
        common.SourceRevisionContentPair,
        common.VisibilityClosure,
        common.PublicAuthorityReceipt,
        common.PublicAuthorityValidationIssue,
        common.PublicAuthorityValidationResult,
    )
    for record_type in record_types:
        assert is_dataclass(record_type)
        assert record_type.__dataclass_params__.frozen is True
        assert fields(record_type)


def test_canonical_hash_is_order_stable_and_tuple_preserving() -> None:
    left = {"b": ("二", "一"), "a": {"z": 1, "x": 2}}
    right = {"a": {"x": 2, "z": 1}, "b": ("二", "一")}
    assert common.canonical_json_bytes(left) == common.canonical_json_bytes(right)
    assert common.canonical_sha256(left) == common.canonical_sha256(right)
    assert common.canonical_json_bytes({"items": (1, 2)}) != common.canonical_json_bytes({"items": (2, 1)})


@pytest.mark.parametrize(
    ("builder", "packet_type", "bundle"),
    (
        (
            build_subject_temporal_authority,
            SubjectTemporalAuthorityPacket,
            build_subject_authority_bundle,
        ),
        (
            build_aemh_match_history_authority,
            AEMHMatchHistoryAuthorityPacket,
            build_aemh_authority_bundle,
        ),
    ),
)
def test_public_builders_have_packet_only_authority_boundary(
    builder, packet_type, bundle
) -> None:
    """A builder has one AuthorityBundleV02 input and returns one packet."""
    signature = inspect.signature(builder)
    assert tuple(signature.parameters) == ("source",)
    assert get_type_hints(builder)["source"] is common.AuthorityBundleV02
    assert get_type_hints(builder)["return"] is packet_type

    packet = builder(bundle())
    assert isinstance(packet, packet_type)
    with pytest.raises(common.PublicAuthorityConstructionError) as caught:
        builder(packet)
    assert caught.value.result.primary_code == "PUB_TYPE_MISMATCH"


@pytest.mark.parametrize(
    ("builder", "bundle"),
    (
        (build_subject_temporal_authority, build_subject_authority_bundle),
        (build_aemh_match_history_authority, build_aemh_authority_bundle),
    ),
)
def test_public_authority_rejects_mutable_nested_input(builder, bundle) -> None:
    """A list injected into a frozen graph is rejected before construction."""
    source_bundle = bundle()
    source = source_bundle.source
    if isinstance(source, common.SubjectFullGraphInputV02):
        mutated_source = source.__class__(
            axis=source.axis,
            cutoff_binding=source.cutoff_binding,
            domain_applicability=source.domain_applicability,
            events=list(source.events),
            locator_specs=source.locator_specs,
            phase=source.phase,
            revision_specs=source.revision_specs,
            risk=source.risk,
            scope=source.scope,
            visit=source.visit,
        )
    else:
        mutated_source = source.__class__(
            current_locator_specs=list(source.current_locator_specs),
            current_revision_specs=source.current_revision_specs,
            current_scope=source.current_scope,
            decision_records=source.decision_records,
            previous_locator_specs=source.previous_locator_specs,
            previous_revision_specs=source.previous_revision_specs,
            previous_scope=source.previous_scope,
            thread_specs=source.thread_specs,
        )
    mutated_bundle = source_bundle.__class__(
        authority_scope=source_bundle.authority_scope,
        bundle_content_identity=source_bundle.bundle_content_identity,
        contract_id=source_bundle.contract_id,
        execution_profile=source_bundle.execution_profile,
        schema_version=source_bundle.schema_version,
        source=mutated_source,
        target_contract=source_bundle.target_contract,
        temporal_v01_manifest_sha256=source_bundle.temporal_v01_manifest_sha256,
    )
    with pytest.raises(common.PublicAuthorityConstructionError) as caught:
        builder(mutated_bundle)
    assert caught.value.result.primary_code == "PUB_TYPE_MISMATCH"


@pytest.mark.parametrize(
    ("builder", "bundle"),
    (
        (build_subject_temporal_authority, build_subject_authority_bundle),
        (build_aemh_match_history_authority, build_aemh_authority_bundle),
    ),
)
def test_deep_nested_wrong_type_is_rejected_before_packet_construction(
    builder, bundle
) -> None:
    """Frozen containers do not make their nested fields dynamically typed."""
    authority = bundle()
    if isinstance(authority.source, common.SubjectFullGraphInputV02):
        source = replace(
            authority.source,
            axis=replace(authority.source.axis, mode=["calendar"]),
        )
    else:
        source = replace(
            authority.source,
            thread_specs=(
                replace(
                    authority.source.thread_specs[0],
                    candidate_ref=["candidate::suspected-ae::1"],
                ),
                authority.source.thread_specs[1],
            ),
        )
    candidate = replace(authority, source=source, bundle_content_identity="0" * 64)
    candidate = replace(
        candidate,
        bundle_content_identity=common.canonical_sha256(
            common.without_field(candidate, "bundle_content_identity")
        ),
    )
    with pytest.raises(common.PublicAuthorityConstructionError) as caught:
        builder(candidate)
    assert caught.value.result.primary_code == "PUB_TYPE_MISMATCH"
    assert caught.value.result.packet_emitted is False


def test_validation_result_is_frozen_and_does_not_emit_on_error() -> None:
    result = common.validation_result(
        (common.issue("TEST_FAILURE", "/test", origin="consumer", priority=1),)
    )
    assert result.ok is False
    assert result.packet_emitted is False
    assert result.primary_code == "TEST_FAILURE"
    with pytest.raises(FrozenInstanceError):
        result.ok = True
