"""R5 S2 W3 -- focused / adjacent / SHA tests for the renderer-neutral
offline thin-slice projection chain.

Coverage:
* focused: the projection chain (project risk -> center cell -> Inspector
  -> Workspace/deep link -> visit/event/risk anchor -> exact source) emits
  one valid, deterministic, renderer-neutral chain from the frozen packet;
* adjacent: the projected R5 public objects stay typed/valid, the source
  revision joins the receipt pair, the deep-link locator round-trips, the
  packet and its bindings are never mutated, and the canonical return
  context is deterministic;
* SHA: the ``evidence/r4_s2_readonly_sha256.json`` record pins the R4 public
  + R5 S0/S1 + frozen W1/W2 sources the projection imports read-only, and a
  session-scoped autouse fixture rejects any byte drift before/after the
  suite; the projection source itself stays free of file IO, network and
  forbidden semantic branches.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import fields
from pathlib import Path

import pytest

_POC_ROOT = Path(__file__).resolve().parents[2]
_R5_SRC = Path(__file__).resolve().parents[1] / "src"
_R4_SRC = _POC_ROOT / "medical_monitoring_ai_native_r4" / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC, _R5_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import mm_r5  # noqa: E402
from mm_r5 import s2_authority_builder as b  # noqa: E402
from mm_r5 import s2_contracts as s2  # noqa: E402
from mm_r5 import s2_thin_slice as ts  # noqa: E402
from mm_r5.contracts import validate_object  # noqa: E402

_MMR5_DIR = Path(__file__).resolve().parents[1] / "src" / "mm_r5"
_MMR4_DIR = _R4_SRC / "mm_r4"

# ---------------------------------------------------------------------------
# SHA gate (R4 public + R5 S0/S1 + frozen W1/W2 read-only sources)
# ---------------------------------------------------------------------------

EVIDENCE_PATH = (
    Path(__file__).resolve().parents[1] / "evidence"
    / "r4_s2_readonly_sha256.json")
_EVIDENCE = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
S2_READONLY_SHA256 = dict(_EVIDENCE["files"])


def _evidence_path(key: str) -> Path:
    prefix, name = key.split("/", 1)
    return (_MMR4_DIR if prefix == "r4" else _MMR5_DIR) / name


def _readonly_hashes() -> dict:
    return {key: hashlib.sha256(
        _evidence_path(key).read_bytes()).hexdigest()
        for key in S2_READONLY_SHA256}


@pytest.fixture(scope="session", autouse=True)
def _s2_readonly_sha_before_and_after() -> None:
    """Fail the session if any S2 read-only source drifts from the freeze,
    checked before the suite and again after the suite."""
    before = _readonly_hashes()
    assert before == S2_READONLY_SHA256, (
        "S2 read-only source drifted from the freeze BEFORE the R5 suite: "
        f"{before}")
    yield
    after = _readonly_hashes()
    assert after == S2_READONLY_SHA256, (
        "S2 read-only source drifted from the freeze AFTER the R5 suite: "
        f"{after}")
    assert after == before, "S2 read-only sources changed during the suite"


@pytest.mark.parametrize("key", sorted(S2_READONLY_SHA256))
def test_s2_readonly_source_matches_frozen_sha256(key: str) -> None:
    path = _evidence_path(key)
    assert path.is_file(), f"missing S2 read-only source: {path}"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == S2_READONLY_SHA256[key], (
        f"S2 read-only source {key} drifted from the freeze: {actual}")


def test_s2_readonly_evidence_record_is_well_formed() -> None:
    assert _EVIDENCE["schema"] == (
        "medical-monitoring-r5-s2-readonly-sha256-evidence-v1")
    assert set(_EVIDENCE["files"]) == set(S2_READONLY_SHA256)
    for key, digest in _EVIDENCE["files"].items():
        assert re.fullmatch(r"[0-9a-f]{64}", digest), key
        assert key.startswith(("r4/", "r5/")), key


# ---------------------------------------------------------------------------
# Valid packet + deterministic replay
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def packet():
    return b.build_s2_authority_packet()


def _bypass(obj, **changes):
    """Copy a frozen dataclass without running construction invariants, so
    W3 can prove its own fail-closed projection checks."""
    values = {field.name: getattr(obj, field.name) for field in fields(obj)}
    values.update(changes)
    out = object.__new__(type(obj))
    for key, value in values.items():
        object.__setattr__(out, key, value)
    return out


def test_project_emits_one_valid_renderer_neutral_chain(packet) -> None:
    projection = ts.project_thin_slice(packet)
    assert ts.is_thin_slice_projection(projection)
    assert ts.validate_thin_slice(projection) == {
        "valid": True, "reasons": ()}
    # Every hop is present as a typed R5 object.
    for obj in (projection.center_cell, projection.inspector,
                projection.workspace, projection.temporal_spine,
                projection.visit_node, projection.journey_event,
                projection.risk_anchor, projection.deep_link_state,
                projection.return_context):
        assert validate_object(obj), type(obj).__name__


def test_s2_public_entrypoints_are_exported_by_root_package(packet) -> None:
    """The accepted slice is usable without private module paths."""
    assert mm_r5.R5S2AuthorityPacket is s2.R5S2AuthorityPacket
    assert mm_r5.R5S2ThinSliceProjection is ts.R5S2ThinSliceProjection
    assert mm_r5.build_s2_authority_packet is b.build_s2_authority_packet
    assert mm_r5.project_thin_slice is ts.project_thin_slice
    assert mm_r5.validate_s2_authority_packet is \
        s2.validate_s2_authority_packet
    assert mm_r5.validate_thin_slice is ts.validate_thin_slice
    assert mm_r5.is_s2_authority_packet(packet)
    projection = mm_r5.project_thin_slice(packet)
    assert mm_r5.is_thin_slice_projection(projection)


def test_project_is_deterministic_on_replay(packet) -> None:
    first = ts.project_thin_slice(packet)
    second = ts.project_thin_slice(packet)
    assert first.content_hash == second.content_hash
    assert first.deep_link_state == second.deep_link_state
    assert first.return_context == second.return_context
    assert ts.validate_thin_slice(second)["valid"]


# ---------------------------------------------------------------------------
# Focused: project risk -> center cell
# ---------------------------------------------------------------------------


def test_project_risk_to_center_identity_closes(packet) -> None:
    projection = ts.project_thin_slice(packet)
    risk = projection.project_risk
    cell = projection.center_cell
    # Project risk binds the D10 marker + public projection identity.
    assert risk.risk_ref == packet.project_risk_binding.risk_ref
    assert risk.public_projection_id == \
        packet.project_risk_binding.public_projection_id
    assert risk.public_projection_content_hash == \
        packet.project_risk_binding.public_projection_content_hash
    assert risk.projection_version_ref == \
        packet.project_risk_binding.projection_version_ref
    assert risk.member_refs == packet.project_risk_binding.member_refs
    assert risk.stable_core_ref == packet.project_risk_binding.stable_core_ref
    # Center cell derives from the same typed member relation.
    assert cell.domain == packet.center_binding.r5_domain
    assert cell.domain == packet.center_binding.r4_risk_or_outcome_domain
    assert cell.severity == packet.center_binding.r5_severity
    assert cell.site_ref == packet.center_binding.site_ref
    assert cell.individual_risk_refs == packet.center_binding.individual_risk_refs
    assert cell.pattern_refs == (packet.center_binding.pattern_ref,)
    # The project risk ref is the same risk the center anchors.
    assert risk.risk_ref == packet.project_risk_binding.risk_ref
    assert risk.member_refs == (packet.center_pattern_member.member_ref,)


def test_center_cell_from_real_member_relation(packet) -> None:
    cell = ts.project_center_cell(packet)
    pattern = packet.center_pattern_member
    individuals = packet.individual_members
    assert set(cell.individual_risk_refs) == set(pattern.descendant_member_refs)
    assert set(cell.individual_risk_refs) == {
        m.member_ref for m in individuals}
    assert cell.site_ref == pattern.site_stable_id
    # measure_refs stays empty (S3).
    assert cell.measure_refs == ()


# ---------------------------------------------------------------------------
# Focused: Inspector
# ---------------------------------------------------------------------------


def test_inspector_refs_derived_from_real_packet_objects(packet) -> None:
    inspector = ts.project_inspector(packet)
    assert inspector.authority_receipt_ref == \
        s2.s2_object_content_hash(packet.authority_receipt)
    assert inspector.risk_ref == packet.project_risk_binding.risk_ref
    assert inspector.domain == packet.center_binding.r5_domain
    assert inspector.severity == packet.center_binding.r5_severity
    assert inspector.analysis_attempt_refs == tuple(sorted(
        a.attempt_id for a in packet.analysis_attempts))
    item_id = packet.reference_baseline_items[0].item_id
    assert inspector.baseline_item_refs == (item_id,)
    assert inspector.baseline_assessment_refs == (item_id,)
    assert inspector.conflict_refs == (packet.conflict.conflict_id,)
    assert inspector.verification_refs == tuple(sorted(
        v.verification_id for v in packet.verifications))
    assert inspector.adjudication_ref == packet.adjudication.binding_id
    assert packet.source_binding.locator_id in inspector.source_locator_refs


def test_inspector_s4_deferred_refs_stay_empty(packet) -> None:
    inspector = ts.project_inspector(packet)
    assert inspector.worker_output_refs == ()
    assert inspector.support_evidence_refs == ()
    assert inspector.counterevidence_refs == ()
    assert inspector.query_draft_ref is None


# ---------------------------------------------------------------------------
# Focused: Workspace / deep link / temporal anchors / source
# ---------------------------------------------------------------------------


def test_workspace_and_temporal_spine_close(packet) -> None:
    projection = ts.project_thin_slice(packet)
    temporal = packet.temporal_binding
    workspace = projection.workspace
    spine = projection.temporal_spine
    assert workspace.subject_ref == temporal.subject_ref
    assert workspace.spine_ref == temporal.spine_ref
    assert workspace.selected_visit_ref == temporal.visit_ref
    assert workspace.selected_event_ref == temporal.event_ref
    assert workspace.selected_risk_ref == temporal.risk_ref
    assert spine.subject_ref == temporal.subject_ref
    assert spine.spine_ref == temporal.spine_ref
    assert spine.cutoff_ref == packet.authority_receipt.cutoff_ref
    assert spine.event_refs == (temporal.event_ref,)
    assert spine.visit_refs == (temporal.visit_ref,)
    # S5 deferred leaves stay empty.
    assert spine.pending_date_refs == ()
    assert spine.phase_band_refs == ()


def test_exact_anchor_chain_visit_event_risk(packet) -> None:
    projection = ts.project_thin_slice(packet)
    temporal = packet.temporal_binding
    visit = projection.visit_node
    event = projection.journey_event
    anchor = projection.risk_anchor
    assert visit.visit_ref == temporal.visit_ref
    assert visit.visit_kind == "actual"
    assert visit.date_state == "exact"
    assert visit.actual_date == temporal.actual_date
    assert visit.nominal_date is None
    assert event.event_ref == temporal.event_ref
    assert event.domain == temporal.domain
    assert event.subtype == temporal.event_subtype
    assert event.start == temporal.event_start
    assert event.end == temporal.event_end
    assert anchor.risk_ref == temporal.risk_ref
    assert anchor.event_ref == temporal.event_ref
    assert anchor.visit_ref == temporal.visit_ref
    assert anchor.domain == temporal.domain
    assert anchor.severity == temporal.severity
    assert anchor.risk_type_zh == temporal.risk_type_zh


def _anchor_date(packet):
    return packet.temporal_binding.actual_date


def test_deep_link_state_canonical_round_trip(packet) -> None:
    projection = ts.project_thin_slice(packet)
    deep = projection.deep_link_state
    assert deep.project_ref == packet.project_risk_binding.project_ref
    assert deep.run_ref == packet.project_risk_binding.run_ref
    assert deep.snapshot_ref == packet.project_risk_binding.snapshot_ref
    assert deep.cutoff_ref == packet.authority_receipt.cutoff_ref
    assert deep.risk_ref == packet.project_risk_binding.risk_ref
    assert deep.subject_ref == packet.temporal_binding.subject_ref
    assert deep.spine_ref == packet.temporal_binding.spine_ref
    assert deep.visit_ref == packet.temporal_binding.visit_ref
    assert deep.event_ref == packet.temporal_binding.event_ref
    assert deep.risk_anchor_ref == packet.temporal_binding.risk_anchor_ref
    assert deep.return_context_key == packet.deep_link_target.return_state_key
    assert deep.source_locator_ref == packet.source_binding.locator_id
    # The exact anchor dates lie inside the evaluation window.
    assert deep.window_start <= _anchor_date(packet) <= deep.window_end


def test_exact_source_round_trip(packet) -> None:
    projection = ts.project_thin_slice(packet)
    source = projection.source
    assert source.locator_id == packet.source_binding.locator_id
    assert source.locator_id == packet.source_evidence.locator_id
    assert source.locator_kind == packet.source_binding.locator_kind
    assert source.source_file == packet.source_binding.source_file
    assert source.row_or_cell_ref == packet.source_binding.row_or_cell_ref
    assert source.lineage_ref == packet.source_binding.lineage_ref
    assert source.revision_id == packet.source_binding.revision_id
    assert source.revision_content_hash == \
        packet.source_binding.revision_content_hash
    assert source.fallback_policy == "none"
    assert source.resolution_state == "locatable"
    assert source.locator_id == projection.deep_link_state.source_locator_ref
    assert source.locator_id in projection.inspector.source_locator_refs


def test_exact_source_locator_kind_mismatch_fails_closed(packet) -> None:
    bad_source = _bypass(packet.source_binding,
                         locator_kind="listing_row")
    bad_packet = _bypass(packet, source_binding=bad_source)
    with pytest.raises(ts.ThinSliceProjectionError, match="lineage/row/cell"):
        ts.resolve_exact_source(bad_packet)


@pytest.mark.parametrize(
    "window",
    ("2030-01-01..2030-12-31", "not-a-range",
     "2026-06-30..2026-01-01"),
)
def test_packet_baseline_window_drift_fails_closed(
    packet, window: str,
) -> None:
    item, = packet.reference_baseline_items
    bad_item = _bypass(item, temporal_window=window)
    bad_packet = _bypass(packet, reference_baseline_items=(bad_item,))
    with pytest.raises((ts.ThinSliceProjectionError, s2.S2ContractError)):
        ts.project_thin_slice(bad_packet)


def test_no_nearest_fallback_enforced(packet) -> None:
    projection = ts.project_thin_slice(packet)
    assert projection.source.fallback_policy == "none"
    assert projection.visit_node.actual_date is not None
    assert projection.journey_event.start is not None
    assert projection.visit_node.date_state == "exact"
    # The anchor date must fall within the evaluation window (no snapping).
    assert projection.deep_link_state.window_start <= \
        projection.visit_node.actual_date <= \
        projection.deep_link_state.window_end


def test_return_context_canonical_and_deterministic(packet) -> None:
    projection = ts.project_thin_slice(packet)
    context = projection.return_context
    # Round trip: the return context restores exactly the deep-link state.
    assert context.deep_link_state is projection.deep_link_state
    assert context.canonical_state_hash
    assert len(context.canonical_state_hash) == 64
    # Neutral ephemeral defaults, deterministic across replay.
    second = ts.project_thin_slice(packet)
    assert second.return_context == context
    assert context.temporary_expansion_refs == ()


# ---------------------------------------------------------------------------
# Adjacent: packet/source/R5-surface integrity
# ---------------------------------------------------------------------------


def test_adjacent_packet_remains_valid_after_projection(packet) -> None:
    assert s2.validate_s2_authority_packet(packet)["valid"]
    ts.project_thin_slice(packet)
    assert s2.validate_s2_authority_packet(packet)["valid"]
    assert packet.packet_id.startswith("r5-s2-auth:")
    assert s2.compute_packet_content_hash(packet) == packet.packet_content_hash


def test_adjacent_projection_never_mutates_packet(packet) -> None:
    before = s2.s2_canonical_json(packet)
    ts.project_thin_slice(packet)
    after = s2.s2_canonical_json(packet)
    assert after == before


def test_adjacent_source_revision_joins_receipt_pair(packet) -> None:
    source = ts.resolve_exact_source(packet)
    pair = packet.authority_receipt.source_revision_content_pairs[0]
    assert source.revision_id == pair.revision_id
    assert source.revision_content_hash == pair.content_hash
    assert len(packet.authority_receipt.source_revision_content_pairs) == 1


def test_adjacent_deep_link_locator_round_trip(packet) -> None:
    source = ts.resolve_exact_source(packet)
    assert packet.deep_link_target.source_locator == source.locator_id
    assert packet.deep_link_target.target_state == "locatable"
    assert packet.deep_link_target.member_object_ref == \
        packet.center_pattern_member.member_ref


def test_adjacent_public_r5_objects_are_typed(packet) -> None:
    projection = ts.project_thin_slice(packet)
    for obj in (projection.center_cell, projection.inspector,
                projection.workspace, projection.temporal_spine,
                projection.visit_node, projection.journey_event,
                projection.risk_anchor, projection.deep_link_state,
                projection.return_context):
        assert validate_object(obj)
        # Every hop must be canonical-serializable (renderer-neutral record).
        assert s2.s2_canonical_json(obj)


# ---------------------------------------------------------------------------
# Static closure of the projection source
# ---------------------------------------------------------------------------


def _thin_slice_source() -> str:
    path = Path(__file__).resolve().parents[1] / "src" / "mm_r5" / \
        "s2_thin_slice.py"
    return path.read_text(encoding="utf-8")


def test_thin_slice_no_file_io_or_network() -> None:
    source = _thin_slice_source()
    for token in ("open(", "read_text", "read_bytes", "json.load",
                  "Path(", "requests", "urllib", "socket", "http://",
                  "https://"):
        assert token not in source, token


def test_thin_slice_no_case_fixture_test_or_sentinel_branches() -> None:
    source = _thin_slice_source()
    assert re.search(r"D10-(CASE|FIXTURE|ORACLE|TEST|MANIFEST)-\d+",
                     source) is None
    for token in ("== \"case_id\"", "== \"fixture_id\"", "== \"test_id\"",
                  "== \"oracle\"", ".case_id", ".fixture_id", ".test_id",
                  "startswith(\"SYN", "endswith(\"SYN", "\"SYN-",
                  "nearest("):
        assert token not in source, token


def test_thin_slice_imports_are_workspace_internal() -> None:
    source = _thin_slice_source()
    for token in ("import numpy", "import pandas", "import requests",
                  "import socket"):
        assert token not in source, token
