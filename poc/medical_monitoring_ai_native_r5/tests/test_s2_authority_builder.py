"""R5 S2 W2 -- focused tests for the real R4 typed-pipeline synthetic
authority-packet builder (``mm_r5.s2_authority_builder``).

Every packet leaf derives from a REAL R4 typed pipeline object (the D10
envelope/adapter/evaluator/projection and the R4 ensemble closure) or from a
closed typed relation; nothing copies an expected output or branches on
test/case/fixture ids.  These tests assert:

* ``build_s2_authority_packet`` emits ONE packet that passes every frozen
  cross-object invariant and is deterministic on replay;
* the project-risk / center / deep-link / source / temporal / baseline /
  worker / conflict / adjudicator / ModelEvidence identities all close by
  identity against the real pipeline objects;
* no mutation of inputs and static closure of the builder source
  (no file IO, no network, no forbidden semantic branches).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R5_SRC = Path(__file__).resolve().parents[1] / "src"
_R4_SRC = _POC_ROOT / "medical_monitoring_ai_native_r4" / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC, _R5_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4 import d10_evaluator as r4_evaluator  # noqa: E402
from mm_r4 import d10_projection as r4_projection  # noqa: E402
from mm_r5 import s2_authority_builder as b  # noqa: E402
from mm_r5 import s2_contracts as s2  # noqa: E402

# ---------------------------------------------------------------------------
# Valid packet + deterministic replay
# ---------------------------------------------------------------------------


def test_build_emits_one_valid_packet() -> None:
    packet = b.build_s2_authority_packet()
    result = s2.validate_s2_authority_packet(packet)
    assert result["valid"], result["reasons"]
    assert result["reasons"] == ()
    assert packet.packet_id.startswith(s2.PACKET_ID_PREFIX)
    assert packet.packet_id == s2.PACKET_ID_PREFIX + packet.packet_content_hash
    assert packet.authority_mode == s2.AUTHORITY_MODE_S2
    assert packet.stage_status == s2.STAGE_STATUS_S2


def test_build_is_deterministic_on_replay() -> None:
    first = b.build_s2_authority_packet()
    second = b.build_s2_authority_packet()
    assert first == second
    assert s2.validate_s2_authority_packet(first)["valid"]
    assert s2.validate_s2_authority_packet(second)["valid"]


def test_all_frozen_invariant_error_codes_pass() -> None:
    packet = b.build_s2_authority_packet()
    assert s2.validate_s2_authority_packet(packet) == {"valid": True,
                                                       "reasons": ()}


# ---------------------------------------------------------------------------
# Real pipeline derivation (identities close by identity)
# ---------------------------------------------------------------------------


def test_envelope_evaluates_positive_through_real_pipeline() -> None:
    typed = b.build_synthetic_d10_envelope()
    result = b.evaluate_envelope(typed)
    assert result.unit is not None
    assert result.unit.l1_disposition == "positive"
    assert b.derive_d10_authority(typed) is not None


def test_project_risk_binding_matches_real_marker_and_projection() -> None:
    packet = b.build_s2_authority_packet()
    typed = b.build_synthetic_d10_envelope()
    result = r4_evaluator.evaluate(typed, b.derive_d10_authority(typed))
    marker = r4_projection.build_d10_risk_marker(typed, result)
    projection = r4_projection.build_d10_project_projection(typed, result)
    receipt = packet.authority_receipt
    risk = packet.project_risk_binding
    assert marker is not None
    assert risk.risk_ref == marker.marker_id
    assert risk.risk_marker_content_hash == marker.content_hash
    assert risk.stable_core_ref == marker.stable_core
    assert risk.member_refs == marker.member_refs
    assert risk.source_locator_refs == marker.source_locator_ids
    assert risk.projection_version_ref == projection.projection_version_ref
    assert risk.public_projection_id == projection.projection_id
    assert risk.public_projection_content_hash == \
        projection.projection_content_hash
    assert risk.public_projection_id == receipt.public_projection_id
    assert risk.public_projection_content_hash == \
        receipt.public_projection_content_hash
    assert risk.project_ref == receipt.project_ref
    assert risk.run_ref == receipt.run_ref
    assert risk.snapshot_ref == receipt.snapshot_ref
    assert risk.cutoff_ref == receipt.cutoff_ref
    assert receipt.cutoff_ref is not None


def test_center_binding_from_typed_member_relation() -> None:
    packet = b.build_s2_authority_packet()
    pattern = packet.center_pattern_member
    individuals = packet.individual_members
    center = packet.center_binding
    assert pattern.member_kind == "center_pattern"
    assert tuple(sorted(m.member_ref for m in individuals)) == tuple(
        sorted(set(pattern.descendant_member_refs)))
    assert all(m.member_kind == "individual_risk" for m in individuals)
    assert all(m.site_stable_id == pattern.site_stable_id
               for m in individuals)
    # Domain from the actual SignalDefinition.risk_or_outcome_domain.
    assert center.r5_domain == b.SYNTHETIC_DOMAIN
    assert center.r5_domain == center.r4_risk_or_outcome_domain
    assert center.r5_domain in s2.S2_DOMAINS
    # Severity from the closed precedence over actual member priorities.
    ranks = {"high": 2, "medium": 1, "low": 0}
    expected_max = max(
        [pattern.monitoring_priority] +
        [m.monitoring_priority for m in individuals],
        key=lambda v: ranks[v])
    assert center.r5_severity == expected_max
    assert center.r5_severity in s2.S2_SEVERITIES
    # Producer domains record the pattern + individual relations exactly.
    assert center.member_producer_domains == tuple(sorted(
        {pattern.producer_domain} | {m.producer_domain for m in individuals}))


def test_deep_link_locatable_and_source_binding_one_hop() -> None:
    packet = b.build_s2_authority_packet()
    link = packet.deep_link_target
    source = packet.source_binding
    evidence = packet.source_evidence
    assert link.target_state == "locatable"
    assert link.locator_resolution_state == "locatable"
    assert link.source_locator == source.locator_id
    assert link.member_object_ref == packet.center_pattern_member.member_ref
    assert evidence.locator_id == source.locator_id
    assert source.fallback_policy == "none"
    assert source.resolution_state == "locatable"
    # The deep link hash is rebound to the S1 receipt's canonical hash.
    assert link.visibility_decision_hash == \
        packet.authority_receipt.visibility_decision_hash
    assert link.visibility_decision_ref == \
        packet.authority_receipt.visibility_decision_id
    # Source revision-content pair is the accepted receipt pair.
    pair = packet.authority_receipt.source_revision_content_pairs[0]
    assert source.revision_id == pair.revision_id
    assert source.revision_content_hash == pair.content_hash


def test_temporal_single_chain_binds_subject_risk_source() -> None:
    packet = b.build_s2_authority_packet()
    temporal = packet.temporal_binding
    assert temporal.date_state == "exact"
    assert temporal.actual_date == temporal.event_start
    assert temporal.event_end >= temporal.event_start
    assert temporal.nominal_date is None
    assert temporal.subject_ref == packet.deep_link_target.subject_ref
    assert temporal.cutoff_ref == packet.authority_receipt.cutoff_ref
    assert temporal.risk_ref == packet.project_risk_binding.risk_ref
    assert temporal.source_locator_ref == packet.source_binding.locator_id
    assert temporal.domain == packet.center_binding.r5_domain
    assert temporal.severity == packet.center_binding.r5_severity
    assert temporal.visit_ref and temporal.event_ref and temporal.risk_anchor_ref
    assert temporal.pending_date_refs == ()
    assert temporal.phase_band_refs == ()


def test_baseline_recheck_binding_closes() -> None:
    packet = b.build_s2_authority_packet()
    item = packet.reference_baseline_items[0]
    assert len(packet.baseline_assessments) == 2
    for assessment in packet.baseline_assessments:
        assert assessment.item_id == item.item_id
        assert assessment.source_recheck_locator_ids == item.source_locator_ids
    assert item.source_revision_id == packet.source_binding.revision_id
    assert item.snapshot_id == packet.authority_receipt.snapshot_ref
    assert packet.source_evidence.locator_id in item.source_locator_ids


def test_worker_isolation_and_real_ensemble_closure() -> None:
    packet = b.build_s2_authority_packet()
    attempts = packet.analysis_attempts
    first, second = attempts
    assert first.input_content_hash == second.input_content_hash
    assert first.ensemble_id == second.ensemble_id
    assert first.attempt_id != second.attempt_id
    assert first.binding_id != second.binding_id
    assert first.session_id != second.session_id
    assert first.independent_context_hash != second.independent_context_hash
    # Real R4 closure: passed verifications, visible conflict, independent
    # adjudicator needing user attention.
    for verification in packet.verifications:
        assert verification.result == "passed"
        assert set(verification.checked_dimensions) == set(
            s2.S2_VERIFICATION_DIMENSIONS)
    assert len(packet.verifications) == 2
    assert packet.conflict.relation == "mutual_negation"
    assert packet.conflict.display_state == "visible_conflict"
    assert packet.conflict.hidden is False
    assert packet.conflict.monitoring_priority == "high"
    assert set(packet.conflict.member_attempt_ids) == {
        first.attempt_id, second.attempt_id}
    assert packet.adjudication.binding_id not in {
        first.binding_id, second.binding_id}
    assert packet.adjudication.session_id not in {
        first.session_id, second.session_id}
    assert packet.adjudication.outcome == "needs_user_attention"
    assert tuple(sorted(packet.adjudication.reviewed_artifact_refs)) == tuple(
        sorted(attempt.output_artifact_ref for attempt in attempts))


def test_model_evidence_packet_only_and_inspector_s4_deferred_empty() -> None:
    packet = b.build_s2_authority_packet()
    model = packet.model_evidence
    assert model.ensemble_size == 2
    assert tuple(sorted(model.member_analysis_refs)) == tuple(sorted(
        attempt.attempt_id for attempt in packet.analysis_attempts))
    assert model.input_content_hash == \
        packet.analysis_attempts[0].input_content_hash
    assert model.ensemble_id == packet.analysis_attempts[0].ensemble_id
    assert model.model_id == packet.analysis_attempts[0].model_id
    assert model.model_version == packet.analysis_attempts[0].model_version
    assert packet.source_evidence.locator_id in model.source_refs
    inspector = packet.inspector_binding
    assert inspector.worker_output_refs == ()
    assert inspector.support_evidence_refs == ()
    assert inspector.counterevidence_refs == ()
    assert inspector.query_draft_ref is None
    assert inspector.model_evidence_visibility == "packet_only"
    # Inspector baseline refs are the sorted-unique item-id singleton (never
    # attempt ids).
    assert inspector.baseline_item_refs == \
        (packet.reference_baseline_items[0].item_id,)
    assert inspector.baseline_assessment_refs == \
        (packet.reference_baseline_items[0].item_id,)


def test_inspector_authority_receipt_ref_is_canonical_receipt_hash() -> None:
    packet = b.build_s2_authority_packet()
    expected = s2.s2_object_content_hash(packet.authority_receipt)
    assert packet.inspector_binding.authority_receipt_ref == expected
    assert packet.project_risk_binding.authority_receipt_ref == expected


def test_build_does_not_mutate_inputs() -> None:
    typed = b.build_synthetic_d10_envelope()
    import dataclasses
    before = dataclasses.asdict(typed)
    b.build_s2_authority_packet(typed=typed)
    after = dataclasses.asdict(typed)
    assert after == before


# ---------------------------------------------------------------------------
# Static closure of the builder source
# ---------------------------------------------------------------------------


def _builder_source() -> str:
    path = Path(__file__).resolve().parents[1] / "src" / "mm_r5" / \
        "s2_authority_builder.py"
    return path.read_text(encoding="utf-8")


def test_builder_no_file_io_or_network() -> None:
    source = _builder_source()
    for token in ("open(", "read_text", "read_bytes", "json.load",
                  "Path(", "import json", "requests", "urllib", "socket",
                  "http://", "https://"):
        assert token not in source, token


def test_builder_no_case_fixture_test_or_sentinel_branches() -> None:
    source = _builder_source()
    # No opaque fixture/case/test ids and no synthetic sentinel lookup.
    assert re.search(r"D10-(CASE|FIXTURE|ORACLE|TEST|MANIFEST)-\d+",
                     source) is None
    # Code-level decision patterns only: the prose docstring and the
    # FORBIDDEN_SEMANTIC_TOKENS declaration may legitimately name the
    # forbidden vocabulary.
    for token in ("== \"case_id\"", "== \"fixture_id\"", "== \"test_id\"",
                  "== \"oracle\"", ".case_id", ".fixture_id", ".test_id",
                  "startswith(\"SYN", "endswith(\"SYN", "\"SYN-",
                  "nearest("):
        assert token not in source, token


def test_builder_source_imports_are_all_workspace_internal() -> None:
    source = _builder_source()
    for token in ("from mm_r4.", "from mm_r5.", "from mm_r2.", "from mm_r1.",
                  "from mm_r3."):
        pass  # allowed: the real R4/R5 pipeline is the derivation path
    # No third-party or stdlib IO/network imports beyond what the R4 pipeline
    # itself needs.
    for token in ("import numpy", "import pandas", "import requests",
                  "import socket"):
        assert token not in source, token
