"""R5 S2 W3 -- high-risk challenge tests for the offline thin-slice
projection chain.

Every challenge tampers a frozen packet (bypassing the fail-closed packet
constructors, exactly like the W2 challenge suite) and asserts the
projection layer refuses to emit a chain: identity mismatch, hidden
member/site, source mismatch, baseline attempt substitution, worker
non-isolation, hidden conflict, adjudicator collision, date fabrication,
unknown domain/severity and packet tampering all fail closed with the
hop-specific reason -- never a nearest fallback and never a partial chain.
"""

from __future__ import annotations

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

from mm_r5 import s2_authority_builder as b  # noqa: E402
from mm_r5 import s2_thin_slice as ts  # noqa: E402
from mm_r5.contracts import R5ContractError  # noqa: E402


@pytest.fixture(scope="module")
def packet():
    return b.build_s2_authority_packet()


def _bypass(obj, **changes):
    """Copy a dataclass without running its fail-closed constructor so a
    tamper variant can be fed to the projection layer."""
    fields = {f.name: getattr(obj, f.name)
              for f in dataclasses.fields(obj)}
    fields.update(changes)
    out = object.__new__(type(obj))
    for name, value in fields.items():
        object.__setattr__(out, name, value)
    return out


def _tampered(packet, **changes):
    """Packet variant bypassing the constructor (identity keys reset) with
    the named root fields replaced."""
    return _bypass(packet, packet_content_hash="", packet_id="", **changes)


def _rejects(packet, expected_reason):
    with pytest.raises(ts.ThinSliceProjectionError) as exc:
        ts.project_thin_slice(packet)
    assert expected_reason in str(exc.value)


# ---------------------------------------------------------------------------
# Identity mismatch
# ---------------------------------------------------------------------------


def test_identity_mismatch_center_domain_divergence_rejects(packet) -> None:
    bad_center = _bypass(packet.center_binding, r5_domain="ae")
    _rejects(_tampered(packet, center_binding=bad_center),
             "center r5_domain must equal r4_risk_or_outcome_domain")


def test_identity_mismatch_inspector_domain_divergence_rejects(packet) -> None:
    bad_inspector = _bypass(packet.inspector_binding, domain="ae")
    _rejects(_tampered(packet, inspector_binding=bad_inspector),
             "inspector domain must equal the center domain")


def test_identity_mismatch_inspector_receipt_ref_rejects(packet) -> None:
    bad_inspector = _bypass(
        packet.inspector_binding, authority_receipt_ref="0" * 64)
    _rejects(_tampered(packet, inspector_binding=bad_inspector),
             "inspector authority_receipt_ref must equal the canonical "
             "receipt hash")


def test_identity_mismatch_risk_ref_divergence_rejects(packet) -> None:
    bad_risk = _bypass(packet.project_risk_binding, risk_ref="0" * 64)
    _rejects(_tampered(packet, project_risk_binding=bad_risk),
             "inspector risk_ref must equal the project/temporal risk ref")


# ---------------------------------------------------------------------------
# Hidden member / hidden site
# ---------------------------------------------------------------------------


def test_hidden_member_ref_not_descendant_rejects(packet) -> None:
    bad_center = _bypass(
        packet.center_binding,
        individual_risk_refs=("S2-RISK-CENTER-001", "S2-RISK-FOREIGN-001"))
    _rejects(_tampered(packet, center_binding=bad_center),
             "center individual_risk_refs must equal the pattern descendant "
             "member refs")


def test_hidden_site_ref_divergence_rejects(packet) -> None:
    bad_center = _bypass(packet.center_binding, site_ref="S2-SITE-OTHER-001")
    _rejects(_tampered(packet, center_binding=bad_center),
             "center site_ref must equal the pattern member site_stable_id")


def test_temporal_subject_not_deep_link_subject_rejects(packet) -> None:
    bad_temporal = _bypass(
        packet.temporal_binding, subject_ref="S2-SUBJ-OTHER-001")
    _rejects(_tampered(packet, temporal_binding=bad_temporal),
             "temporal subject_ref must equal the deep-link target "
             "subject_ref")


# ---------------------------------------------------------------------------
# Source mismatch
# ---------------------------------------------------------------------------


def test_source_mismatch_locator_vs_evidence_rejects(packet) -> None:
    bad_source = _bypass(packet.source_binding, locator_id="S2-LOC-OTHER-001")
    tampered = _tampered(packet, source_binding=bad_source)
    # The Inspector hop refuses first in the composite chain...
    _rejects(tampered,
             "inspector source_locator_refs must include the exact one-hop "
             "source locator")
    # ...and the source hop refuses directly with the locator identity reason.
    with pytest.raises(ts.ThinSliceProjectionError) as exc:
        ts.resolve_exact_source(tampered)
    assert "source binding locator_id must equal the EvidenceRef locator_id" \
        in str(exc.value)


def test_source_mismatch_revision_not_in_receipt_rejects(packet) -> None:
    bad_source = _bypass(packet.source_binding, revision_id="S2-REV-OTHER-001")
    _rejects(_tampered(packet, source_binding=bad_source),
             "source revision-content pair must equal the receipt's single "
             "pair")


def test_source_mismatch_nearest_fallback_rejects(packet) -> None:
    bad_source = _bypass(packet.source_binding, fallback_policy="nearest")
    _rejects(_tampered(packet, source_binding=bad_source),
             "fallback_policy must be none (no nearest fallback)")


def test_source_mismatch_unlocatable_deep_link_rejects(packet) -> None:
    bad_link = _bypass(packet.deep_link_target, target_state="unavailable")
    _rejects(_tampered(packet, deep_link_target=bad_link),
             "deep-link target must be locatable (no nearest fallback)")


# ---------------------------------------------------------------------------
# Baseline attempt substitution (replacement attack)
# ---------------------------------------------------------------------------


def test_baseline_attempt_substitution_rejects(packet) -> None:
    """The public Inspector baseline refs must be the sorted-unique
    reference item ids, never attempt ids."""
    bad_inspector = _bypass(
        packet.inspector_binding,
        baseline_assessment_refs=("S2-ATTEMPT-WORKER-001",
                                  "S2-ATTEMPT-WORKER-002"))
    _rejects(_tampered(packet, inspector_binding=bad_inspector),
             "inspector baseline refs must equal the sorted-unique "
             "reference item ids")


def test_baseline_item_ref_dangling_rejects(packet) -> None:
    bad_inspector = _bypass(
        packet.inspector_binding, baseline_item_refs=("S2-BASELINE-OTHER-001",))
    _rejects(_tampered(packet, inspector_binding=bad_inspector),
             "inspector baseline refs must equal the sorted-unique "
             "reference item ids")


# ---------------------------------------------------------------------------
# Worker non-isolation
# ---------------------------------------------------------------------------


def test_worker_non_isolation_attempt_refs_rejects(packet) -> None:
    bad_inspector = _bypass(
        packet.inspector_binding,
        analysis_attempt_refs=("S2-ATTEMPT-WORKER-001",
                               "S2-ATTEMPT-WORKER-001"))
    _rejects(_tampered(packet, inspector_binding=bad_inspector),
             "inspector analysis_attempt_refs must equal the real attempt "
             "ids")


# ---------------------------------------------------------------------------
# Hidden conflict
# ---------------------------------------------------------------------------


def test_hidden_conflict_rejects(packet) -> None:
    hidden = _bypass(packet.conflict, hidden=True)
    _rejects(_tampered(packet, conflict=hidden),
             "the S2 conflict must be visible (never hidden)")


def test_conflict_ref_dangling_rejects(packet) -> None:
    bad_inspector = _bypass(
        packet.inspector_binding, conflict_refs=("conflict-other",))
    _rejects(_tampered(packet, inspector_binding=bad_inspector),
             "inspector conflict_refs must equal the real conflict id")


# ---------------------------------------------------------------------------
# Adjudicator collision
# ---------------------------------------------------------------------------


def test_adjudicator_binding_collision_rejects(packet) -> None:
    worker = packet.analysis_attempts[0]
    bad_adjudication = _bypass(
        packet.adjudication, binding_id=worker.binding_id)
    # Keep the Inspector adjudication ref consistent with the (tampered)
    # binding so the independence check itself is exercised.
    bad_inspector = _bypass(
        packet.inspector_binding, adjudication_ref=worker.binding_id)
    _rejects(_tampered(packet, adjudication=bad_adjudication,
                       inspector_binding=bad_inspector),
             "the adjudicator binding/session must differ from both workers")


def test_adjudicator_session_collision_rejects(packet) -> None:
    worker = packet.analysis_attempts[0]
    bad_adjudication = _bypass(
        packet.adjudication, session_id=worker.session_id)
    bad_inspector = _bypass(
        packet.inspector_binding,
        adjudication_ref=packet.adjudication.binding_id)
    _rejects(_tampered(packet, adjudication=bad_adjudication,
                       inspector_binding=bad_inspector),
             "the adjudicator binding/session must differ from both workers")


# ---------------------------------------------------------------------------
# Date fabrication / no nearest fallback
# ---------------------------------------------------------------------------


def test_date_fabrication_actual_removed_rejects(packet) -> None:
    bad_temporal = _bypass(packet.temporal_binding, actual_date=None)
    _rejects(_tampered(packet, temporal_binding=bad_temporal),
             "visit date_state=exact requires actual_date (no nearest "
             "fallback)")


def test_date_fabrication_nominal_replacing_actual_rejects(packet) -> None:
    """The nominal visit date must never replace the actual date."""
    bad_temporal = _bypass(
        packet.temporal_binding, actual_date=None,
        nominal_date=date(2026, 3, 15))
    _rejects(_tampered(packet, temporal_binding=bad_temporal),
             "visit date_state=exact requires actual_date (no nearest "
             "fallback)")


def test_date_fabrication_snapped_actual_date_rejects(packet) -> None:
    """An actual date that no longer equals the event start is a snapped
    date and must fail closed."""
    bad_temporal = _bypass(packet.temporal_binding,
                           actual_date=date(2026, 3, 14))
    _rejects(_tampered(packet, temporal_binding=bad_temporal),
             "visit actual_date must equal the event start (no snapped or "
             "fabricated date)")


def test_date_fabrication_event_end_precedes_start_rejects(packet) -> None:
    bad_temporal = _bypass(packet.temporal_binding,
                           event_end=date(2026, 3, 10))
    _rejects(_tampered(packet, temporal_binding=bad_temporal),
             "event_end must not precede event_start")


def test_anchor_outside_evaluation_window_rejects(packet) -> None:
    """An anchor moved outside the evaluation window is a nearest-match
    violation: the composite validator must reject the chain."""
    moved_start = date(2026, 12, 1)
    bad_temporal = _bypass(
        packet.temporal_binding, actual_date=moved_start,
        event_start=moved_start, event_end=date(2026, 12, 3))
    _rejects(_tampered(packet, temporal_binding=bad_temporal),
             "anchor_outside_evaluation_window")


# ---------------------------------------------------------------------------
# Unknown domain / unknown severity
# ---------------------------------------------------------------------------


def test_unknown_domain_center_rejects(packet) -> None:
    bad_center = _bypass(
        packet.center_binding, r5_domain="unknown",
        r4_risk_or_outcome_domain="unknown")
    _rejects(_tampered(packet, center_binding=bad_center),
             "is not a closed S2 domain")


def test_unknown_domain_temporal_rejects(packet) -> None:
    """An unclosed domain fails at the R5 typed surface itself."""
    bad_temporal = _bypass(packet.temporal_binding, domain="unknown")
    with pytest.raises(R5ContractError):
        ts.project_thin_slice(_tampered(packet, temporal_binding=bad_temporal))


def test_unknown_severity_center_rejects(packet) -> None:
    bad_center = _bypass(packet.center_binding, r5_severity="unknown")
    _rejects(_tampered(packet, center_binding=bad_center),
             "center severity must equal the closed priority precedence")


# ---------------------------------------------------------------------------
# Packet tampering (S4 leak / dangling refs / nearest validation)
# ---------------------------------------------------------------------------


def test_packet_tamper_s4_deferred_leak_rejects(packet) -> None:
    """Smuggling worker-output refs into the public Inspector refs must fail
    at the projection hop, not reach the R5 surface."""
    bad_inspector = _bypass(
        packet.inspector_binding, worker_output_refs=("S2-ATTEMPT-WORKER-001",))
    _rejects(_tampered(packet, inspector_binding=bad_inspector),
             "inspector worker/support/counterevidence refs must stay empty "
             "(S4)")


def test_packet_tamper_source_ref_missing_rejects(packet) -> None:
    bad_inspector = _bypass(packet.inspector_binding, source_locator_refs=())
    _rejects(_tampered(packet, inspector_binding=bad_inspector),
             "inspector source_locator_refs must include the exact one-hop "
             "source locator")


def test_packet_tamper_verification_refs_dangling_rejects(packet) -> None:
    bad_inspector = _bypass(
        packet.inspector_binding,
        verification_refs=("verify-tampered",))
    _rejects(_tampered(packet, inspector_binding=bad_inspector),
             "inspector verification_refs must equal the real verification "
             "ids")


def test_validate_rejects_nearest_fallback_chain(packet) -> None:
    """The fail-closed re-verifier must also reject a chain whose source
    carries a nearest fallback."""
    projection = ts.project_thin_slice(packet)
    bad_source = _bypass(projection.source, fallback_policy="nearest")
    bad_projection = _bypass(projection, source=bad_source)
    result = ts.validate_thin_slice(bad_projection)
    assert not result["valid"]
    assert "nearest_fallback_forbidden" in result["reasons"]


def test_projection_requires_typed_packet() -> None:
    with pytest.raises(ts.ThinSliceProjectionError):
        ts.project_thin_slice({"not": "a packet"})
