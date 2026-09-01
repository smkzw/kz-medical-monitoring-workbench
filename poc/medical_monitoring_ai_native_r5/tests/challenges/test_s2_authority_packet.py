"""R5 S2 W2 -- high-risk challenge tests for the synthetic authority packet.

Every challenge proves a frozen fail-closed gate with the REAL R4 pipeline:
the builder never emits a packet for a defective envelope/derivation, and a
tampered packet is rejected by :func:`mm_r5.s2_contracts.
validate_s2_authority_packet` with the matching frozen error code (or by the
typed R4/R5 constructors themselves when the defect is structurally
unconstructable).  Covered high-risk items:

* identity mismatch (receipt vs bindings/deep link);
* hidden member/site (envelope hides the pattern site -> no packet);
* source mismatch (one-hop locator/revision binding breaks);
* baseline attempt substitution (Inspector refs must be item-id derived,
  never attempt ids);
* worker non-isolation (real ensemble rejects shared session/binding);
* hidden conflict (high-risk disagreement can never be hidden);
* adjudicator collision (a worker may not adjudicate itself);
* date fabrication (nominal date never replaces the actual date; event
  geometry must hold);
* unknown domain/severity (closed S2 vocabulary fails closed);
* packet tampering (any post-build mutation is detected).

``_tampered`` builds a packet instance bypassing the fail-closed
constructor so :func:`validate_s2_authority_packet` can report the frozen
error codes; the same defect raised by the constructor is asserted where the
typed object itself forbids it.
"""

from __future__ import annotations

import copy
import dataclasses
import sys
from datetime import date
from pathlib import Path

import pytest

_POC_ROOT = Path(__file__).resolve().parents[3]
_R5_SRC = Path(__file__).resolve().parents[2] / "src"
_R4_SRC = _POC_ROOT / "medical_monitoring_ai_native_r4" / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC, _R5_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4.ensemble import (  # noqa: E402
    Adjudicator,
    EvidenceDigestContext,
    run_ensemble,
)
from mm_r4.ensemble_contracts import (  # noqa: E402
    ConflictVisibility,
    EnsembleContractError,
)
from mm_r4.ensemble import EnsembleError  # noqa: E402
from mm_r4 import d10_adapter as r4_adapter  # noqa: E402
from mm_r4.d10_contracts import (  # noqa: E402
    d10_canonical_json,
    d10_sha256_text,
)
from mm_r5 import s2_authority_builder as b  # noqa: E402
from mm_r5 import s2_contracts as s2  # noqa: E402
from mm_r5.s2_contracts import (  # noqa: E402
    R5S2AuthorityPacket,
    S2ContractError,
    S2InvariantError,
)


@pytest.fixture(scope="module")
def packet() -> R5S2AuthorityPacket:
    return b.build_s2_authority_packet()


def _bypass(obj, **changes):
    """Copy an object without running its fail-closed constructor."""
    values = {field.name: getattr(obj, field.name)
              for field in dataclasses.fields(obj)}
    values.update(changes)
    out = object.__new__(type(obj))
    for key, value in values.items():
        object.__setattr__(out, key, value)
    return out


def _tampered(packet: R5S2AuthorityPacket, **changes):
    """Packet variant bypassing the constructor (identity keys reset) so the
    fail-closed validator can report every frozen error code."""
    return _bypass(packet, packet_content_hash="", packet_id="", **changes)


def _reasons(tampered: R5S2AuthorityPacket):
    return s2.validate_s2_authority_packet(tampered)["reasons"]


# ---------------------------------------------------------------------------
# Identity mismatch
# ---------------------------------------------------------------------------


def test_identity_mismatch_receipt_project_ref_rejects(packet) -> None:
    bad_receipt = dataclasses.replace(
        packet.authority_receipt, project_ref="S2-PROJECT-OTHER")
    tampered = _tampered(packet, authority_receipt=bad_receipt)
    assert "receipt_identity_mismatch" in _reasons(tampered)
    # Fail-closed construction: the frozen constructor also rejects.
    with pytest.raises(S2InvariantError) as exc:
        dataclasses.replace(packet, authority_receipt=bad_receipt,
                            packet_content_hash="", packet_id="")
    assert exc.value.error_code == "receipt_identity_mismatch"


def test_identity_mismatch_receipt_cutoff_null_rejects(packet) -> None:
    # The S2 chain requires a non-null receipt cutoff.
    bad_receipt = dataclasses.replace(packet.authority_receipt, cutoff_ref=None)
    tampered = _tampered(packet, authority_receipt=bad_receipt)
    assert "receipt_identity_mismatch" in _reasons(tampered)


# ---------------------------------------------------------------------------
# Hidden member / hidden site
# ---------------------------------------------------------------------------


def test_hidden_site_envelope_yields_no_packet() -> None:
    """Hiding the only site makes the envelope unprojectable: the real
    pipeline yields no positive unit / no locatable target and the builder
    fails closed."""
    envelope = b.build_synthetic_d10_envelope_dict()
    visibility = envelope["visibility_decision"]
    visibility["evaluation_site_refs"] = [b.SYNTHETIC_SITE_REF]
    visibility["projectable_site_refs"] = []
    visibility["hidden_site_refs"] = [b.SYNTHETIC_SITE_REF]
    visibility["hidden_site_count"] = 1
    visibility["projectable_subject_site_pairs"] = []
    visibility["deep_link_eligible_site_refs"] = []
    visibility["deep_link_eligible_subject_site_pairs"] = []
    from mm_r4.d10_contracts import d10_content_hash
    visibility["decision_id"] = d10_content_hash(
        b._visibility_decision_core(visibility), "decision_id")
    from mm_r4 import d10_adapter as r4_adapter
    typed = r4_adapter.build_typed_input(envelope)
    with pytest.raises(b.S2AuthorityBuilderError):
        b.build_s2_authority_packet(typed=typed)


def test_hidden_member_not_locatable_deep_link_rejects(packet) -> None:
    """A deep link that cannot resolve (unavailable target) breaks the
    one-hop source binding."""
    unavailable = _bypass(packet.deep_link_target,
                          target_state="unavailable",
                          source_locator=None)
    tampered = _tampered(packet, deep_link_target=unavailable)
    assert "source_binding_mismatch" in _reasons(tampered)


# ---------------------------------------------------------------------------
# Source mismatch
# ---------------------------------------------------------------------------


def test_source_mismatch_evidence_locator_rejects(packet) -> None:
    bad_evidence = dataclasses.replace(
        packet.source_evidence, locator_id="S2-LOC-OTHER")
    tampered = _tampered(packet, source_evidence=bad_evidence)
    assert "source_binding_mismatch" in _reasons(tampered)


def test_source_mismatch_revision_pair_not_in_receipt_rejects(packet) -> None:
    bad_source = _bypass(packet.source_binding,
                         revision_id="S2-REV-OTHER",
                         revision_content_hash="f" * 64)
    tampered = _tampered(packet, source_binding=bad_source)
    assert "source_binding_mismatch" in _reasons(tampered)


def test_source_mismatch_fallback_policy_rejects(packet) -> None:
    # Nearest fallback is forbidden: fallback_policy must stay none.
    bad_source = _bypass(packet.source_binding, fallback_policy="nearest")
    tampered = _tampered(packet, source_binding=bad_source)
    assert "source_binding_mismatch" in _reasons(tampered)


# ---------------------------------------------------------------------------
# Baseline attempt substitution (replacement attack)
# ---------------------------------------------------------------------------


def test_baseline_attempt_substitution_rejects(packet) -> None:
    """The public Inspector baseline assessment refs must be the sorted-unique
    item-id singleton derived from the actual assessments; substituting an
    attempt id (replacement attack) fails closed."""
    attempt_id = packet.analysis_attempts[0].attempt_id
    bad_inspector = _bypass(
        packet.inspector_binding, baseline_assessment_refs=(attempt_id,))
    tampered = _tampered(packet, inspector_binding=bad_inspector)
    assert "inspector_ref_derivation_mismatch" in _reasons(tampered)


def test_baseline_item_ref_dangling_rejects(packet) -> None:
    bad_inspector = _bypass(
        packet.inspector_binding,
        baseline_item_refs=("S2-BASELINE-ITEM-OTHER",))
    tampered = _tampered(packet, inspector_binding=bad_inspector)
    assert "inspector_ref_derivation_mismatch" in _reasons(tampered)


# ---------------------------------------------------------------------------
# Worker non-isolation
# ---------------------------------------------------------------------------


def test_worker_non_isolation_shared_session_rejects(packet) -> None:
    first, second = packet.analysis_attempts
    colliding = dataclasses.replace(second, session_id=first.session_id)
    outputs = {o.attempt_id: o for o in packet.worker_outputs}
    with pytest.raises(EnsembleError):
        run_ensemble(
            ensemble_id=first.ensemble_id,
            input_content_hash=first.input_content_hash,
            attempts=[first, colliding],
            worker_outputs=outputs,
            baseline_items=packet.reference_baseline_items,
            digest_context=EvidenceDigestContext(
                input_content_hash=first.input_content_hash,
                output_digests={}, evidence_digests=frozenset()))


def test_worker_non_isolation_shared_context_rejects(packet) -> None:
    first, second = packet.analysis_attempts
    colliding = dataclasses.replace(
        second, independent_context_hash=first.independent_context_hash)
    outputs = {o.attempt_id: o for o in packet.worker_outputs}
    with pytest.raises(EnsembleError):
        run_ensemble(
            ensemble_id=first.ensemble_id,
            input_content_hash=first.input_content_hash,
            attempts=[first, colliding],
            worker_outputs=outputs,
            baseline_items=packet.reference_baseline_items,
            digest_context=EvidenceDigestContext(
                input_content_hash=first.input_content_hash,
                output_digests={}, evidence_digests=frozenset()))


def test_worker_outputs_share_input_content_hash(packet) -> None:
    hashes = {attempt.input_content_hash
              for attempt in packet.analysis_attempts}
    assert len(hashes) == 1  # same question/input version, isolated workers


# ---------------------------------------------------------------------------
# Hidden conflict
# ---------------------------------------------------------------------------


def test_high_risk_conflict_cannot_be_constructed_hidden() -> None:
    """The R4 typed conflict forbids hiding high-risk mutual negation before
    any packet exists."""
    with pytest.raises(EnsembleContractError):
        ConflictVisibility(
            conflict_id="S2-CONFLICT-HIDDEN",
            member_attempt_ids=("S2-ATTEMPT-WORKER-001",
                                "S2-ATTEMPT-WORKER-002"),
            monitoring_priority="high",
            relation="mutual_negation",
            display_state="visible_conflict",
            hidden=True)


def test_hidden_conflict_packet_rejects(packet) -> None:
    hidden_conflict = _bypass(packet.conflict, hidden=True)
    tampered = _tampered(packet, conflict=hidden_conflict)
    assert "conflict_hidden_or_mismatched" in _reasons(tampered)


# ---------------------------------------------------------------------------
# Adjudicator collision
# ---------------------------------------------------------------------------


def test_adjudicator_binding_collision_rejects(packet) -> None:
    worker = packet.analysis_attempts[0]
    outputs = {o.attempt_id: o for o in packet.worker_outputs}
    with pytest.raises(EnsembleError):
        run_ensemble(
            ensemble_id=packet.analysis_attempts[0].ensemble_id,
            input_content_hash=packet.analysis_attempts[0].input_content_hash,
            attempts=packet.analysis_attempts,
            worker_outputs=outputs,
            baseline_items=packet.reference_baseline_items,
            digest_context=EvidenceDigestContext(
                input_content_hash=packet.analysis_attempts[0].input_content_hash,
                output_digests={}, evidence_digests=frozenset()),
            adjudicator=Adjudicator(
                binding_id=worker.binding_id,
                session_id="S2-ADJ-SESSION-001",
                model_id="synthetic-baseline-review-v1",
                model_version="1.0"))


def test_adjudicator_session_collision_rejects(packet) -> None:
    worker = packet.analysis_attempts[0]
    outputs = {o.attempt_id: o for o in packet.worker_outputs}
    with pytest.raises(EnsembleError):
        run_ensemble(
            ensemble_id=packet.analysis_attempts[0].ensemble_id,
            input_content_hash=packet.analysis_attempts[0].input_content_hash,
            attempts=packet.analysis_attempts,
            worker_outputs=outputs,
            baseline_items=packet.reference_baseline_items,
            digest_context=EvidenceDigestContext(
                input_content_hash=packet.analysis_attempts[0].input_content_hash,
                output_digests={}, evidence_digests=frozenset()),
            adjudicator=Adjudicator(
                binding_id="S2-ADJ-BIND-001",
                session_id=worker.session_id,
                model_id="synthetic-baseline-review-v1",
                model_version="1.0"))


# ---------------------------------------------------------------------------
# Date fabrication
# ---------------------------------------------------------------------------


def test_date_fabrication_nominal_replacing_actual_rejects(packet) -> None:
    """nominal_date must never replace the actual date (date_state=exact)."""
    fabricated = _bypass(packet.temporal_binding,
                         actual_date=None,
                         nominal_date=date(2026, 3, 15))
    tampered = _tampered(packet, temporal_binding=fabricated)
    assert "date_geometry_mismatch" in _reasons(tampered)


def test_date_fabrication_event_end_precedes_start_rejects(packet) -> None:
    with pytest.raises(S2ContractError):
        dataclasses.replace(
            packet.temporal_binding,
            event_end=date(2026, 3, 10),
            event_start=date(2026, 3, 15))


def test_date_fabrication_tampered_packet_rejects(packet) -> None:
    fabricated = _bypass(packet.temporal_binding,
                         event_end=date(2026, 3, 10),
                         event_start=date(2026, 3, 15))
    tampered = _tampered(packet, temporal_binding=fabricated)
    assert "date_geometry_mismatch" in _reasons(tampered)


# ---------------------------------------------------------------------------
# Unknown domain / unknown severity
# ---------------------------------------------------------------------------


def test_unknown_domain_envelope_yields_no_packet() -> None:
    envelope = b.build_synthetic_d10_envelope_dict()
    envelope["signal_definition"]["risk_or_outcome_domain"] = \
        "risk_distribution"  # not a closed S2 domain
    from mm_r4 import d10_adapter as r4_adapter
    typed = r4_adapter.build_typed_input(envelope)
    with pytest.raises(b.S2AuthorityBuilderError):
        b.build_s2_authority_packet(typed=typed)


def test_unknown_severity_registry_yields_no_packet() -> None:
    registry = {
        "S2-RISK-CENTER-001": {
            "producer_domain": "D01",
            "subject_stable_id": "S2-SUBJ-001",
            "monitoring_priority": "unknown",  # closed S2 severity fails
        },
        "S2-RISK-CENTER-002": {
            "producer_domain": "D02",
            "subject_stable_id": "S2-SUBJ-002",
            "monitoring_priority": "medium",
        },
    }
    with pytest.raises(b.S2AuthorityBuilderError):
        b.build_s2_authority_packet(individual_registry=registry)


def test_alternate_valid_individual_registry_cannot_replace_authority() -> None:
    """Even a structurally valid caller registry cannot replace the frozen
    typed Member authority or produce a second valid packet for one input."""
    registry = {
        member.member_ref: {
            "producer_domain": member.producer_domain,
            "subject_stable_id": member.subject_stable_id,
            "monitoring_priority": member.monitoring_priority,
        }
        for member in b.FROZEN_INDIVIDUAL_MEMBERS
    }
    with pytest.raises(b.S2AuthorityBuilderError, match="forbidden"):
        b.build_s2_authority_packet(individual_registry=registry)


def test_shifted_r4_analysis_window_cannot_leave_stale_s2_dates() -> None:
    """A caller window that excludes the exact visit/event must fail closed
    rather than emitting the old fixed S2 dates."""
    envelope = b.build_synthetic_d10_envelope_dict()
    envelope["analysis_windows"][0]["window_start"] = "2030-01-01"
    envelope["analysis_windows"][0]["window_end"] = "2030-12-31"
    typed = r4_adapter.build_typed_input(envelope)
    with pytest.raises(b.S2AuthorityBuilderError, match="inside"):
        b.build_s2_authority_packet(typed=typed)


@pytest.mark.parametrize(
    ("start", "end", "message"),
    (("not-a-date", "2026-06-30", "ISO-8601"),
     ("2026-06-30", "2026-01-01", "precedes")),
)
def test_malformed_or_reversed_r4_analysis_window_fails_closed(
    start: str, end: str, message: str,
) -> None:
    envelope = b.build_synthetic_d10_envelope_dict()
    envelope["analysis_windows"][0]["window_start"] = start
    envelope["analysis_windows"][0]["window_end"] = end
    typed = r4_adapter.build_typed_input(envelope)
    with pytest.raises(b.S2AuthorityBuilderError, match=message):
        b.build_s2_authority_packet(typed=typed)


def test_changed_valid_r4_window_propagates_to_all_attempts() -> None:
    """A different valid window is allowed only when every temporal consumer
    uses that exact authority; no worker may retain the builder default."""
    envelope = b.build_synthetic_d10_envelope_dict()
    envelope["analysis_windows"][0]["window_start"] = "2026-03-01"
    envelope["analysis_windows"][0]["window_end"] = "2026-04-01"
    typed = r4_adapter.build_typed_input(envelope)
    built = b.build_s2_authority_packet(typed=typed)
    item, = built.reference_baseline_items
    assert item.temporal_window == "2026-03-01..2026-04-01"
    assert {attempt.claimed_date_window
            for attempt in built.analysis_attempts} == {
                item.temporal_window}


# ---------------------------------------------------------------------------
# Packet tampering
# ---------------------------------------------------------------------------


def test_packet_tamper_baseline_recheck_locators_rejects(packet) -> None:
    """Post-build tampering of the assessment recheck locators is detected
    by the baseline recheck binding invariant."""
    bad_assessments = tuple(
        _bypass(assessment, source_recheck_locator_ids=("S2-LOC-OTHER",))
        for assessment in packet.baseline_assessments)
    tampered = _tampered(packet, baseline_assessments=bad_assessments)
    reasons = _reasons(tampered)
    assert "baseline_recheck_binding_mismatch" in reasons


def test_packet_tamper_worker_output_assessment_swap_rejects(packet) -> None:
    """Swapping the worker outputs' assessments off the actual assessments is
    detected (worker output attribution + baseline recheck)."""
    first = packet.analysis_attempts[0].attempt_id
    swapped = tuple(
        _bypass(output, assessments=()) if output.attempt_id == first
        else _bypass(output, assessments=packet.baseline_assessments)
        for output in packet.worker_outputs)
    tampered = _tampered(packet, worker_outputs=swapped)
    reasons = _reasons(tampered)
    assert "worker_output_binding_mismatch" in reasons or \
        "baseline_recheck_binding_mismatch" in reasons


def test_packet_tamper_identity_hash_cycle_detected(packet) -> None:
    """A post-build mutation changes the canonical packet hash: the stored
    packet_content_hash no longer matches (nonrecursive identity gate)."""
    bad_evidence = dataclasses.replace(
        packet.source_evidence, lineage_ref="S2-LINE-OTHER")
    tampered = _tampered(packet, source_evidence=bad_evidence)
    reasons = _reasons(tampered)
    assert "packet_identity_hash_cycle_or_mismatch" in reasons


def test_packet_tamper_binding_content_hash_stale_rejects(packet) -> None:
    """A binding mutation without rehashing is rejected by canonical
    exactness (the binding's own content hash is re-verified)."""
    bad_source = _bypass(packet.source_binding,
                         row_or_cell_ref="sheet:9;row:9")
    tampered = _tampered(packet, source_binding=bad_source)
    assert "packet_exactness_violation" in _reasons(tampered)


def test_packet_tamper_s4_deferred_leak_rejects(packet) -> None:
    """Smuggling worker-output refs into the public Inspector refs leaks the
    packet-only authority into the public R4 surface and fails closed."""
    bad_inspector = _bypass(
        packet.inspector_binding,
        worker_output_refs=tuple(
            output.attempt_id for output in packet.worker_outputs))
    tampered = _tampered(packet, inspector_binding=bad_inspector)
    assert "s4_deferred_leaf_leak" in _reasons(tampered)


def test_packet_tamper_model_evidence_ensemble_size_rejects(packet) -> None:
    bad_model = _bypass(packet.model_evidence, ensemble_size=3)
    tampered = _tampered(packet, model_evidence=bad_model)
    assert "model_evidence_boundary_violation" in _reasons(tampered)


@pytest.mark.parametrize(
    ("field", "value"),
    (("evaluation_content_identity", "f" * 64),
     ("output_identity", "e" * 64),
     ("output_hash", "d" * 64),
     ("source_refs", ("S2-LOC-OTHER",)),
     ("adjudication_state", "accepted"),
     ("model_binding_hash", "c" * 64)),
)
def test_packet_tamper_model_evidence_exact_identity_rejects(
    packet, field: str, value: object,
) -> None:
    bad_model = _bypass(packet.model_evidence, **{field: value})
    tampered = _tampered(packet, model_evidence=bad_model)
    assert "model_evidence_boundary_violation" in _reasons(tampered)


def test_packet_tamper_source_locator_kind_rejects(packet) -> None:
    bad_source = _bypass(packet.source_binding,
                         locator_kind="listing_row")
    tampered = _tampered(packet, source_binding=bad_source)
    assert "source_binding_mismatch" in _reasons(tampered)


def test_packet_tamper_worker_claimed_window_rejects(packet) -> None:
    first, second = packet.analysis_attempts
    bad_first = _bypass(first, claimed_date_window="2025-01-01..2025-12-31")
    tampered = _tampered(
        packet, analysis_attempts=(bad_first, second))
    assert "baseline_recheck_binding_mismatch" in _reasons(tampered) or \
        "model_evidence_boundary_violation" in _reasons(tampered)


# ---------------------------------------------------------------------------
# Center/source ambiguity and worker-spec determinism
# ---------------------------------------------------------------------------


def test_two_center_patterns_fail_closed() -> None:
    """More than one center_pattern member must fail closed: 0 or >1 is
    never resolved by input order."""
    envelope = b.build_synthetic_d10_envelope_dict()
    second = copy.deepcopy(envelope["members"][0])
    second["member_ref"] = "S2-PAT-CENTER-002"
    second["subject_stable_id"] = "S2-SUBJ-REP-002"
    second["descendant_member_refs"] = [
        "S2-RISK-CENTER-003", "S2-RISK-CENTER-004"]
    second["descendant_set_hash"] = d10_sha256_text(d10_canonical_json(
        sorted(second["descendant_member_refs"])))
    envelope["members"].append(second)
    typed = r4_adapter.build_typed_input(envelope)
    # exactly-one gate (direct helper)
    with pytest.raises(b.S2AuthorityBuilderError):
        b.resolve_center_pattern_member(typed)
    # full pipeline fails closed
    with pytest.raises(b.S2AuthorityBuilderError):
        b.build_s2_authority_packet(typed=typed)


def test_zero_center_patterns_fail_closed() -> None:
    envelope = b.build_synthetic_d10_envelope_dict()
    envelope["members"] = []
    typed = r4_adapter.build_typed_input(envelope)
    with pytest.raises(b.S2AuthorityBuilderError):
        b.resolve_center_pattern_member(typed)
    with pytest.raises(b.S2AuthorityBuilderError):
        b.build_s2_authority_packet(typed=typed)


def test_duplicate_matching_evidence_ref_fails_closed(packet) -> None:
    """Exactly one EvidenceRef must match the deep-link source locator;
    ambiguity fails closed (no first-item fallback)."""
    envelope = b.build_synthetic_d10_envelope_dict()
    duplicate = copy.deepcopy(envelope["evidence_refs"][0])
    duplicate["lineage_ref"] = "S2-LINE-DUP"
    duplicate["row_or_cell_ref"] = "sheet:1;row:2"
    envelope["evidence_refs"].append(duplicate)
    typed = r4_adapter.build_typed_input(envelope)
    # exactly-one EvidenceRef gate (direct)
    with pytest.raises(b.S2AuthorityBuilderError):
        b.resolve_source_authority(typed, packet.authority_receipt,
                                   packet.deep_link_target)
    # full pipeline fails closed
    with pytest.raises(b.S2AuthorityBuilderError):
        b.build_s2_authority_packet(typed=typed)


def test_multiple_source_revision_pairs_fail_closed(packet) -> None:
    """The single-source packet requires exactly one consistent revision-
    content pair; multiple pairs break the unique locator -> revision join
    and fail closed."""
    envelope = b.build_synthetic_d10_envelope_dict()
    envelope["source_revision_content_pairs"].append({
        "revision_id": "S2-REV-SOURCE-002",
        "content_hash": "f" * 64,
    })
    typed = r4_adapter.build_typed_input(envelope)
    # single-pair join gate (direct)
    with pytest.raises(b.S2AuthorityBuilderError):
        b.resolve_source_authority(typed, packet.authority_receipt,
                                   packet.deep_link_target)
    # full pipeline fails closed
    with pytest.raises(b.S2AuthorityBuilderError):
        b.build_s2_authority_packet(typed=typed)


def test_worker_spec_order_swap_does_not_change_semantics() -> None:
    """The finding support direction is a per-spec semantic fact; swapping
    the worker-spec tuple order must not change the packet or the support
    direction (never derived from index/order/id naming)."""
    packet = b.build_s2_authority_packet()
    swapped = b.build_s2_authority_packet(
        worker_specs=tuple(reversed(b.WORKER_SPECS)))
    assert swapped == packet
    support = {spec.attempt_id: spec.supports_finding
               for spec in b.WORKER_SPECS}
    for output in packet.worker_outputs:
        assert output.findings[0].supported == support[output.attempt_id]
    # The visible conflict is the explicit mutual negation, not an
    # order/index artifact.
    assert packet.conflict.relation == "mutual_negation"
    assert len(packet.conflict.member_attempt_ids) == 2
    assert not packet.conflict.hidden
