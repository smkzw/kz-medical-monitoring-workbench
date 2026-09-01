"""Focused W1 tests: frozen S2 authority-packet typed contracts, exact keys,
closed enums, immutability, nonrecursive canonical identity and the
fail-closed validator over the 21 frozen cross-object invariants.

The frozen machine authority ``authority_packet_schema.json`` /
``exact_overlay.json`` / ``manifest.json`` are read-only inputs to these tests
(never loaded by the runtime package).  Their pinned SHAs are verified first
so a drifted authority cannot silently change the coverage assertions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import date
from pathlib import Path

import pytest

from mm_r4.d10_contracts import (
    EvidenceRef,
    Member,
    ModelEvidence,
    SourceRevisionPair,
)
from mm_r4.d10_projection import D10DeepLinkTarget
from mm_r4.ensemble import WorkerAnalysisOutput, worker_output_content_hash
from mm_r4.ensemble_contracts import (
    AdjudicationBinding,
    AnalysisAttempt,
    BaselineAssessment,
    ConflictVisibility,
    EvidenceVerification,
    GapCandidate,
    ReferenceBaselineItem,
)
from mm_r5 import s2_contracts as s2
from mm_r5.contracts import R5AuthorityReceipt, SourceRevisionContentPair

ARTIFACT_DIR = (
    Path(__file__).resolve().parents[3]
    / "artifacts" / "medical_monitoring_r5_s2_authority_packet_contract_v0_1")

SCHEMA_PATH = ARTIFACT_DIR / "authority_packet_schema.json"
OVERLAY_PATH = ARTIFACT_DIR / "exact_overlay.json"
MANIFEST_PATH = ARTIFACT_DIR / "manifest.json"

H64 = "a" * 64  # valid 64-hex sha256 shape


def _h(n: int) -> str:
    return f"{n:064x}"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Frozen authority SHA gates (read-only input, never imported at runtime)
# ---------------------------------------------------------------------------


def test_frozen_schema_sha256() -> None:
    assert _sha256_file(SCHEMA_PATH) == s2.S2_PACKET_SCHEMA_SHA256


def test_frozen_overlay_sha256() -> None:
    assert _sha256_file(OVERLAY_PATH) == s2.S2_EXACT_OVERLAY_SHA256


def test_frozen_manifest_sha256() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["manifest_content_sha256"] == s2.S2_MANIFEST_CONTENT_SHA256


# ---------------------------------------------------------------------------
# Schema cross-checks (static module code vs frozen JSON)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_enum_vocabulary_matches_schema(schema) -> None:
    for name, values in schema["enums"].items():
        assert s2.s2_enum_values(name) == tuple(values), (
            f"enum {name!r} must match the frozen packet schema exactly")


def test_imported_exact_keys_match_schema(schema) -> None:
    for name, spec in schema["imported_objects"].items():
        assert name in s2.IMPORTED_EXACT_KEYS
        assert tuple(spec["exact_keys"]) == s2.IMPORTED_EXACT_KEYS[name], (
            f"imported object {name} exact keys drifted from the schema")


def test_packet_binding_field_sets_match_schema(schema) -> None:
    classes = {
        "R5S2AuthorityPacket": s2.R5S2AuthorityPacket,
        "R5S2CenterBinding": s2.R5S2CenterBinding,
        "R5S2ProjectRiskBinding": s2.R5S2ProjectRiskBinding,
        "R5S2SourceBinding": s2.R5S2SourceBinding,
        "R5S2TemporalBinding": s2.R5S2TemporalBinding,
        "R5S2InspectorBinding": s2.R5S2InspectorBinding,
    }
    for object_name, cls in classes.items():
        spec = schema["objects"][object_name]
        assert is_dataclass(cls), f"{object_name} must be a dataclass"
        assert tuple(field.name for field in fields(cls)) == tuple(
            spec), (
            f"{object_name} field set must equal the frozen schema exactly")


def test_invariant_error_codes_match_schema(schema) -> None:
    schema_codes = sorted(
        invariant["error_code"]
        for invariant in schema["cross_object_invariants"])
    assert len(schema_codes) == 21
    assert sorted(s2.FROZEN_INVARIANT_ERROR_CODES) == schema_codes


# ---------------------------------------------------------------------------
# Coherent packet fixture (all 21 invariants hold at construction)
# ---------------------------------------------------------------------------


def _build_packet() -> s2.R5S2AuthorityPacket:
    """A fully coherent S2 authority packet: one receipt, one project-risk
    binding, one center binding, one temporal binding, one source binding,
    one reference item, two assessments, two isolated worker attempts/
    outputs, two passed verifications, one visible conflict, one independent
    adjudicator and one packet-only ModelEvidence."""
    project, run, snap, cut = (
        "proj-s2-001", "run-s2-001", "snap-s2-001", "cutoff-s2-001")
    site, subj, risk, spine = (
        "site-001", "subj-001", "risk-s2-001", "spine-s2-001")
    pattern_ref, ir1, ir2, loc, rev = (
        "member-pattern-001", "member-ir-101", "member-ir-102",
        "loc-001", "rev-001")

    pattern = Member(
        member_ref=pattern_ref, member_kind="center_pattern",
        aggregation_plane="center", producer_domain="ae",
        site_stable_id=site, monitoring_priority="high",
        source_locator_refs=(loc,),
        descendant_member_refs=(ir1, ir2), descendant_set_hash=_h(11))
    individual_one = Member(
        member_ref=ir1, member_kind="individual_risk",
        aggregation_plane="individual", producer_domain="ae",
        site_stable_id=site, subject_stable_id=subj,
        monitoring_priority="high", source_locator_refs=(loc,))
    individual_two = Member(
        member_ref=ir2, member_kind="individual_risk",
        aggregation_plane="individual", producer_domain="ae",
        site_stable_id=site, subject_stable_id=subj,
        monitoring_priority="medium", source_locator_refs=(loc,))

    evidence = EvidenceRef(
        locator_id=loc, locator_kind="synthetic_file",
        source_file="synthetic/s2/source.csv", row_or_cell_ref="row-17",
        lineage_ref="lin-001")
    source_binding = s2.R5S2SourceBinding(
        content_hash="", fallback_policy="none", lineage_ref="lin-001",
        locator_id=loc, locator_kind="synthetic_file",
        resolution_state="locatable", revision_content_hash=_h(20),
        revision_id=rev, row_or_cell_ref="row-17",
        source_file="synthetic/s2/source.csv")
    deep_link = D10DeepLinkTarget(
        link_id="link-001", project_ref=project, run_ref=run,
        snapshot_ref=snap, signal_definition_ref="sig-001",
        evaluation_window_instance_ref="win-001", target_kind="member",
        site_ref=site, subject_ref=subj, member_object_ref=pattern_ref,
        source_locator=loc, locator_resolution_state="locatable",
        target_state="locatable", unavailable_message=None,
        visibility_decision_ref="vis-001", visibility_decision_hash=_h(21),
        return_state_key="return-s2-001")
    receipt = R5AuthorityReceipt(
        audience_contract_id="r5-audience-s2", cutoff_ref=cut,
        evaluation_content_identities=(_h(30),), project_ref=project,
        public_projection_content_hash=_h(31), public_projection_id=_h(32),
        public_projection_kind="d10_project", run_ref=run, snapshot_ref=snap,
        source_revision_content_pairs=(
            SourceRevisionContentPair(rev, _h(20)),),
        visibility_decision_hash=_h(21), visibility_decision_id="vis-001")
    receipt_hash = s2.s2_object_content_hash(receipt)
    project_risk = s2.R5S2ProjectRiskBinding(
        authority_receipt_ref=receipt_hash, content_hash="", cutoff_ref=cut,
        member_refs=(pattern_ref, ir1, ir2), project_ref=project,
        projection_version_ref="pv-001",
        public_projection_content_hash=_h(31), public_projection_id=_h(32),
        risk_marker_content_hash=_h(40), risk_ref=risk, run_ref=run,
        snapshot_ref=snap, source_locator_refs=(loc,),
        stable_core_ref="core-001")
    center = s2.R5S2CenterBinding(
        content_hash="", individual_risk_refs=(ir1, ir2), measure_refs=(),
        member_priorities=("high", "medium"), member_producer_domains=("ae",),
        pattern_descendant_member_refs=(ir1, ir2), pattern_ref=pattern_ref,
        r4_risk_or_outcome_domain="ae", r5_domain="ae", r5_severity="high",
        site_ref=site)
    temporal = s2.R5S2TemporalBinding(
        actual_date=date(2026, 5, 12), content_hash="", cutoff_ref=cut,
        date_state="exact", domain="ae", event_end=date(2026, 5, 12),
        event_ref="evt-001", event_start=date(2026, 5, 12),
        event_subtype="ae", nominal_date=None, pending_date_refs=(),
        phase_band_refs=(), phase_ref="phase-001", risk_anchor_ref="ra-001",
        risk_ref=risk, risk_type_zh="AE漏报", severity="high",
        source_locator_ref=loc, spine_ref=spine, subject_ref=subj,
        visit_kind="actual", visit_ref="visit-001")
    item = ReferenceBaselineItem(
        item_id="item-001", source_kind="current_pack",
        source_locator_ids=(loc,), source_revision_id=rev, snapshot_id=snap,
        claimed_identity="identity-001",
        temporal_window="2026-05-12/2026-05-12", claimed_content_hash="",
        origin_artifact_hash=_h(50))
    assessment_one = BaselineAssessment(
        item_id="item-001", state="confirmed",
        source_recheck_locator_ids=(loc,), evidence_hashes=(_h(61),),
        attempt_id="attempt-001", reason_codes=("source_rechecked",))
    assessment_two = BaselineAssessment(
        item_id="item-001", state="unsupported",
        source_recheck_locator_ids=(loc,), evidence_hashes=(_h(62),),
        attempt_id="attempt-002",
        reason_codes=("content_absent_from_source",))
    output_one = WorkerAnalysisOutput(
        attempt_id="attempt-001", assessments=(assessment_one,))
    output_two = WorkerAnalysisOutput(
        attempt_id="attempt-002", assessments=(assessment_two,))

    def _attempt(attempt_id, binding_id, session_id, context, output, artifact):
        return AnalysisAttempt(
            attempt_id=attempt_id, ensemble_id="ens-001",
            binding_id=binding_id, session_id=session_id,
            model_id="model-s2-001", model_version="v1", role="worker",
            independent_context_hash=context, input_content_hash=_h(60),
            output_artifact_ref=artifact, output_hash=worker_output_content_hash(output),
            claimed_date_window="2026-05-12/2026-05-12",
            claimed_unit_contract="subject",
            claimed_source_revision=rev, claimed_rule_id="rule-001",
            claimed_rule_version="v1")

    attempt_one = _attempt("attempt-001", "bind-worker-001",
                           "sess-worker-001", _h(63), output_one, "art-001")
    attempt_two = _attempt("attempt-002", "bind-worker-002",
                           "sess-worker-002", _h(64), output_two, "art-002")
    dimensions = ("identity", "version", "date", "unit", "source", "rule",
                  "artifact_integrity")
    verification_one = EvidenceVerification(
        verification_id="verification-001", attempt_id="attempt-001",
        checked_dimensions=dimensions, result="passed", failure_reason_codes=())
    verification_two = EvidenceVerification(
        verification_id="verification-002", attempt_id="attempt-002",
        checked_dimensions=dimensions, result="passed", failure_reason_codes=())
    conflict = ConflictVisibility(
        conflict_id="conflict-001",
        member_attempt_ids=("attempt-001", "attempt-002"),
        monitoring_priority="high", relation="mutual_negation",
        display_state="visible_conflict", hidden=False)
    adjudication = AdjudicationBinding(
        binding_id="bind-adjudicator-001", session_id="sess-adjudicator-001",
        model_id="model-s2-001", model_version="v1",
        outcome="needs_user_attention",
        reviewed_artifact_refs=("art-001", "art-002"))
    model_output_identity = s2.expected_model_output_identity(
        (attempt_one, attempt_two))
    model_output_hash = s2.expected_model_output_hash(
        model_output_identity, conflict.conflict_id, adjudication.binding_id)
    model_binding_hash = s2.expected_model_binding_hash(
        model_evidence_id="me-001", role="candidate_explanation",
        model_id="model-s2-001", model_version="v1",
        ensemble_id="ens-001", input_content_hash=_h(60),
        member_analysis_refs=("attempt-001", "attempt-002"))
    model_evidence = ModelEvidence(
        model_evidence_id="me-001", role="candidate_explanation",
        permitted_leaf="model_candidate_only", model_id="model-s2-001",
        model_version="v1", evaluation_content_identity=_h(30),
        input_content_hash=_h(60),
        source_revision_content_pairs=(SourceRevisionPair(rev, _h(20)),),
        source_refs=(loc,), independent_context_hash=_h(71),
        ensemble_id="ens-001", ensemble_size=2,
        member_analysis_refs=("attempt-001", "attempt-002"),
        member_analysis_ref_set_hash=s2.s2_object_content_hash(
            ["attempt-001", "attempt-002"]),
        output_identity=model_output_identity, output_hash=model_output_hash,
        adjudication_state="adjudicated",
        model_binding_hash=model_binding_hash)
    inspector = s2.R5S2InspectorBinding(
        adjudication_ref="bind-adjudicator-001",
        analysis_attempt_refs=("attempt-001", "attempt-002"),
        authority_receipt_ref=receipt_hash,
        baseline_assessment_refs=("item-001",),
        baseline_item_refs=("item-001",), conflict_refs=("conflict-001",),
        content_hash="", counterevidence_refs=(), domain="ae",
        model_evidence_visibility="packet_only", query_draft_ref=None,
        risk_ref=risk, severity="high", source_locator_refs=(loc,),
        support_evidence_refs=(),
        verification_refs=("verification-001", "verification-002"),
        worker_output_refs=())
    return s2.R5S2AuthorityPacket(
        adjudication=adjudication, analysis_attempts=(attempt_one, attempt_two),
        authority_mode="synthetic_offline_test_only",
        authority_receipt=receipt, baseline_assessments=(
            assessment_one, assessment_two),
        center_binding=center, center_pattern_member=pattern, conflict=conflict,
        deep_link_target=deep_link, individual_members=(
            individual_one, individual_two),
        inspector_binding=inspector, model_evidence=model_evidence,
        packet_content_hash="", packet_id="", project_risk_binding=project_risk,
        reference_baseline_items=(item,), source_binding=source_binding,
        source_evidence=evidence, stage_status="R5_S2_PRECONDITION_CONTRACT_READY",
        temporal_binding=temporal, verifications=(
            verification_one, verification_two),
        worker_outputs=(output_one, output_two))


def _tamper(packet: s2.R5S2AuthorityPacket, attr: str, value: object) -> None:
    """Mutate a frozen packet field (tamper probe) bypassing construction."""
    object.__setattr__(packet, attr, value)


# ---------------------------------------------------------------------------
# Construction and identity
# ---------------------------------------------------------------------------


def test_valid_packet_constructs_and_validates() -> None:
    packet = _build_packet()
    assert s2.is_s2_authority_packet(packet)
    result = s2.validate_s2_authority_packet(packet)
    assert result["valid"] is True
    assert result["reasons"] == ()


def test_packet_identity_is_nonrecursive() -> None:
    packet = _build_packet()
    assert packet.packet_id == "r5-s2-auth:" + packet.packet_content_hash
    # The content hash excludes exactly packet_id and packet_content_hash.
    core = s2.packet_core_dict(packet)
    assert "packet_id" not in core and "packet_content_hash" not in core
    expected = s2.s2_sha256(s2.s2_canonical_bytes(core))
    assert packet.packet_content_hash == expected
    # The content hash covers nested binding hashes (included as values).
    tampered = _build_packet()
    _tamper(tampered, "center_binding",
            replace(tampered.center_binding, site_ref="site-999",
                    content_hash=""))
    assert s2.compute_packet_content_hash(tampered) != packet.packet_content_hash


def test_supplied_wrong_packet_hash_rejected() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2HashMismatchError):
        replace(packet, packet_content_hash=_h(90))


def test_supplied_wrong_packet_id_rejected() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2HashMismatchError):
        replace(packet, packet_id="r5-s2-auth:" + _h(91))


def test_immutable_after_construction() -> None:
    packet = _build_packet()
    with pytest.raises(FrozenInstanceError):
        packet.authority_mode = "not-the-frozen-mode"


def test_unordered_refs_do_not_change_hash() -> None:
    packet = _build_packet()
    other = replace(
        packet,
        analysis_attempts=tuple(reversed(packet.analysis_attempts)),
        worker_outputs=tuple(reversed(packet.worker_outputs)),
        individual_members=tuple(reversed(packet.individual_members)))
    assert other.packet_content_hash == packet.packet_content_hash


def test_nfc_normalization_does_not_change_hash() -> None:
    packet = _build_packet()
    composed = replace(
        packet, packet_content_hash="", packet_id="",
        temporal_binding=replace(
            packet.temporal_binding, risk_type_zh="é漏报", content_hash=""))
    decomposed = replace(
        packet, packet_content_hash="", packet_id="",
        temporal_binding=replace(
            packet.temporal_binding, risk_type_zh="e\u0301漏报",
            content_hash=""))
    # Both forms canonicalize to the same NFC string, so the packet hash is
    # identical (input NFC-variant never changes the content address).
    assert composed.packet_content_hash == decomposed.packet_content_hash
    assert composed.temporal_binding.risk_type_zh == "é漏报"


def test_hash_changes_when_content_field_changes() -> None:
    packet = _build_packet()
    other = replace(packet, packet_content_hash="", packet_id="",
                    temporal_binding=replace(
                        packet.temporal_binding, visit_ref="visit-999",
                        content_hash=""))
    assert other.packet_content_hash != packet.packet_content_hash


# ---------------------------------------------------------------------------
# Construction fail-closed (shape, cardinality, enums)
# ---------------------------------------------------------------------------


def test_unknown_authority_mode_rejected() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2ContractError):
        replace(packet, authority_mode="real_project_mode")


def test_unknown_domain_rejected() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2ContractError):
        replace(packet, center_binding=replace(
            packet.center_binding, r5_domain="made_up_domain"))


def test_unknown_severity_rejected() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2ContractError):
        replace(packet, center_binding=replace(
            packet.center_binding, r5_severity="critical"))


def test_wrong_attempt_cardinality_rejected() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2ContractError):
        replace(packet, analysis_attempts=packet.analysis_attempts[:1])


def test_duplicate_reference_rejected() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2ContractError):
        replace(packet, inspector_binding=replace(
            packet.inspector_binding,
            analysis_attempt_refs=("attempt-001", "attempt-001")))


def test_non_relative_source_file_rejected() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2ContractError):
        replace(packet, source_binding=replace(
            packet.source_binding,
            source_file="/abs/synthetic/source.csv"))


def test_measure_refs_must_be_empty() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2ContractError):
        replace(packet, center_binding=replace(
            packet.center_binding, measure_refs=("measure-001",)))


def test_s4_query_draft_must_be_null() -> None:
    packet = _build_packet()
    with pytest.raises(s2.S2ContractError):
        replace(packet, inspector_binding=replace(
            packet.inspector_binding, query_draft_ref="draft-001"))


# ---------------------------------------------------------------------------
# Fail-closed validator tamper probes (frozen error codes)
# ---------------------------------------------------------------------------


def test_validate_reports_authority_scope_violation() -> None:
    packet = _build_packet()
    _tamper(packet, "authority_mode", "production_mode")
    result = s2.validate_s2_authority_packet(packet)
    assert "authority_scope_violation" in result["reasons"]


def test_validate_reports_packet_identity_mismatch() -> None:
    packet = _build_packet()
    _tamper(packet, "packet_content_hash", _h(92))
    result = s2.validate_s2_authority_packet(packet)
    assert "packet_identity_hash_cycle_or_mismatch" in result["reasons"]


def test_validate_reports_hidden_site_relation() -> None:
    packet = _build_packet()
    # A hidden member on another site fails the center relation closed.
    member = packet.individual_members[1]
    object.__setattr__(member, "site_stable_id", "site-999")
    result = s2.validate_s2_authority_packet(packet)
    assert "center_member_relation_mismatch" in result["reasons"]


def test_validate_reports_pattern_kind_mismatch() -> None:
    packet = _build_packet()
    _tamper(packet, "center_pattern_member",
            replace(packet.center_pattern_member, member_kind="individual_risk"))
    result = s2.validate_s2_authority_packet(packet)
    assert "center_member_relation_mismatch" in result["reasons"]


def test_validate_reports_unknown_member_severity() -> None:
    packet = _build_packet()
    _tamper(packet, "individual_members",
            (replace(packet.individual_members[0], monitoring_priority="unknown"),)
            + packet.individual_members[1:])
    result = s2.validate_s2_authority_packet(packet)
    assert "center_severity_authority_mismatch" in result["reasons"]


def test_validate_reports_source_mismatch() -> None:
    packet = _build_packet()
    _tamper(packet, "source_evidence",
            replace(packet.source_evidence, locator_id="loc-999"))
    result = s2.validate_s2_authority_packet(packet)
    assert "source_binding_mismatch" in result["reasons"]


def test_validate_reports_baseline_attempt_substitution() -> None:
    packet = _build_packet()
    # Substitute an assessment attempt_id that is not a real worker attempt.
    bogus = replace(packet.baseline_assessments[0], attempt_id="not-a-worker")
    _tamper(packet, "baseline_assessments", (bogus, packet.baseline_assessments[1]))
    result = s2.validate_s2_authority_packet(packet)
    assert "baseline_recheck_binding_mismatch" in result["reasons"]


def test_validate_reports_worker_non_isolation() -> None:
    packet = _build_packet()
    second = replace(packet.analysis_attempts[1], binding_id="bind-worker-001")
    _tamper(packet, "analysis_attempts",
            (packet.analysis_attempts[0], second))
    result = s2.validate_s2_authority_packet(packet)
    assert "worker_isolation_mismatch" in result["reasons"]


def test_validate_reports_conflict_mismatch() -> None:
    packet = _build_packet()
    # The frozen conflict is visible, mutual_negation and high; any deviation
    # (here: a non-mutual relation) fails closed.  (R4 already forbids
    # constructing hidden=True for this relation, so the packet validator's
    # hidden check is defense-in-depth on top of it.)
    conflict = packet.conflict
    object.__setattr__(conflict, "relation", "shared_finding")
    result = s2.validate_s2_authority_packet(packet)
    assert "conflict_hidden_or_mismatched" in result["reasons"]


def test_validate_reports_adjudicator_collision() -> None:
    packet = _build_packet()
    _tamper(packet, "adjudication",
            replace(packet.adjudication, binding_id="bind-worker-001"))
    result = s2.validate_s2_authority_packet(packet)
    assert "adjudicator_not_independent" in result["reasons"]


def test_validate_reports_date_fabrication() -> None:
    packet = _build_packet()
    # Mutate the frozen temporal binding directly (construction rejects a
    # backward event window, so this probe bypasses construction).
    temporal = packet.temporal_binding
    object.__setattr__(temporal, "event_end", date(2026, 5, 10))
    result = s2.validate_s2_authority_packet(packet)
    assert "date_geometry_mismatch" in result["reasons"]


def test_validate_reports_s4_deferred_leak() -> None:
    packet = _build_packet()
    # Mutate the frozen inspector binding directly (construction rejects a
    # non-empty S4-deferred leaf, so this probe bypasses construction).
    inspector = packet.inspector_binding
    object.__setattr__(inspector, "worker_output_refs", ("attempt-001",))
    result = s2.validate_s2_authority_packet(packet)
    assert "s4_deferred_leaf_leak" in result["reasons"]


def test_validate_reports_verification_incomplete() -> None:
    packet = _build_packet()
    incomplete = replace(
        packet.verifications[0], checked_dimensions=("identity", "date"))
    _tamper(packet, "verifications", (incomplete, packet.verifications[1]))
    result = s2.validate_s2_authority_packet(packet)
    assert "verification_incomplete_or_failed" in result["reasons"]


def test_validate_reports_worker_output_attribution() -> None:
    packet = _build_packet()
    # Tamper the actual output content (a foreign gap proposal for this
    # worker) so its canonical hash no longer equals the attempt output_hash.
    gap = GapCandidate(
        gap_id="gap-tampered", gap_kind="baseline_missed_current",
        proposed_identity="identity-999", source_locator_ids=("loc-001",),
        originating_attempt_id="attempt-001")
    output = WorkerAnalysisOutput(
        attempt_id="attempt-001",
        assessments=packet.worker_outputs[0].assessments,
        gap_candidates=(gap,))
    _tamper(packet, "worker_outputs", (output, packet.worker_outputs[1]))
    result = s2.validate_s2_authority_packet(packet)
    assert "worker_output_binding_mismatch" in result["reasons"]


def test_validate_reports_model_evidence_boundary() -> None:
    packet = _build_packet()
    _tamper(packet, "model_evidence",
            replace(packet.model_evidence, ensemble_size=1))
    result = s2.validate_s2_authority_packet(packet)
    assert "model_evidence_boundary_violation" in result["reasons"]


def test_validate_reports_temporal_authority_mismatch() -> None:
    packet = _build_packet()
    temporal = packet.temporal_binding
    object.__setattr__(temporal, "subject_ref", "subj-999")
    result = s2.validate_s2_authority_packet(packet)
    assert "temporal_authority_mismatch" in result["reasons"]


def test_validate_reports_inspector_ref_derivation() -> None:
    packet = _build_packet()
    inspector = packet.inspector_binding
    object.__setattr__(inspector, "baseline_assessment_refs",
                       ("attempt-001",))
    result = s2.validate_s2_authority_packet(packet)
    assert "inspector_ref_derivation_mismatch" in result["reasons"]


def test_validate_reports_receipt_identity_mismatch() -> None:
    packet = _build_packet()
    binding = packet.project_risk_binding
    object.__setattr__(binding, "project_ref", "proj-other")
    result = s2.validate_s2_authority_packet(packet)
    assert "receipt_identity_mismatch" in result["reasons"]


def test_validate_reports_project_risk_binding_mismatch() -> None:
    packet = _build_packet()
    inspector = packet.inspector_binding
    object.__setattr__(inspector, "risk_ref", "risk-other")
    result = s2.validate_s2_authority_packet(packet)
    assert "project_risk_binding_mismatch" in result["reasons"]


def test_validate_reports_temporal_cardinality_mismatch() -> None:
    packet = _build_packet()
    temporal = packet.temporal_binding
    object.__setattr__(temporal, "domain", "mh")
    result = s2.validate_s2_authority_packet(packet)
    assert "temporal_cardinality_mismatch" in result["reasons"]


def test_validate_reports_packet_exactness_hash() -> None:
    packet = _build_packet()
    # Mutate the binding hash directly (construction rejects a mismatched
    # supplied hash, so this probe bypasses construction).
    binding = packet.center_binding
    object.__setattr__(binding, "content_hash", _h(93))
    result = s2.validate_s2_authority_packet(packet)
    assert "packet_exactness_violation" in result["reasons"]
