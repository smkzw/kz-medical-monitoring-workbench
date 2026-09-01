"""R5-S3 worker_01 -- focused tests for the typed authority contracts and the
synthetic/offline authority builder.

The builder consumes leaf-by-leaf read-only references to the R4/S1/S2 public
authority objects (the D09/D10 public projections and the R5 authority
receipts) plus the exact typed synthetic supplemental authorities, and
produces a frozen ``R5S3AuthorityPacket``.  It never imports a D09/D10
typed-input object and never recomputes medical risk, chooses a majority,
infers members from counts or trusts a caller-supplied hash.

Focused coverage (per the R5-S3 implementation contract v0.2):

* positive: one valid packet, deterministic replay, exact current-risk
  plane / center-cell / cluster / change-band projections, severity and
  member expansion equal to the public leaves, aggregate receipt-set
  identity, byte-exact receipt bindings, private/public plane separation;
* negative: typed-input leaf promotion, receipt/content-hash drift,
  packet-id / replay / integrity-hash drift, project/run/snapshot/cutoff
  identity drift, unknown enums, resolved-without-closure, propose-close
  resolution, D09/D10 hotspot field shapes, hidden-member leakage and
  duplicate / dangling identities.

All tests are fail-closed construction gates of the typed contracts, not
oracle echoes:  the full packet-oracle battery (re-sign attacks, challenge
registry) is the worker_03 verifier's domain in ``test_s3_contract_artifacts``.
"""

from __future__ import annotations

import sys
from dataclasses import replace as dc_replace
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

from mm_r4.d10_contracts import EvidenceRef  # noqa: E402
from mm_r5 import s3_authority_builder as b  # noqa: E402
from mm_r5 import s3_contracts as c  # noqa: E402


# ---------------------------------------------------------------------------
# Positive: one valid packet + deterministic replay
# ---------------------------------------------------------------------------


def test_build_emits_one_valid_packet() -> None:
    packet = b.build_s3_authority_packet()
    assert isinstance(packet, c.R5S3AuthorityPacket)
    assert packet.authority_mode == c.AUTHORITY_MODE_S3
    assert packet.status == c.STAGE_STATUS_S3
    assert len(packet.authority_units) >= 1
    assert c.validate_s3_authority_packet(packet)["valid"]


def test_build_is_deterministic_on_replay() -> None:
    first = b.build_s3_authority_packet()
    second = b.build_s3_authority_packet()
    assert first == second
    expected_replay = c.audience_replay_content_hash(
        first.audience_payload)
    assert first.audience_replay_content_hash == expected_replay
    assert first.packet_id == c.PACKET_ID_PREFIX + ":" + expected_replay
    assert first.packet_id.count(":") == 1


def test_build_does_not_mutate_inputs() -> None:
    units_in = b.build_synthetic_units()
    before = tuple(unit.bundle for unit in units_in)
    b.build_s3_authority_packet()
    after = tuple(unit.bundle for unit in units_in)
    assert after == before


# ---------------------------------------------------------------------------
# Positive: leaves derive from the public R4/S1 objects (never recomputed)
# ---------------------------------------------------------------------------


def test_lifecycle_severity_and_expansion_from_public_leaves() -> None:
    packet = b.build_s3_authority_packet()
    for lifecycle in packet.risk_lifecycle_authorities:
        unit = next(u for u in packet.authority_units
                    if c.unit_variant_payload(u).risk_marker is not None
                    and c.unit_variant_payload(u).risk_marker.marker_id
                    == lifecycle.marker_id)
        variant = c.unit_variant_payload(unit)
        marker = variant.risk_marker
        handoff = variant.r2_handoff
        # severity is EXACTLY the public monitoring_priority (never a majority
        # vote or a recomputed risk rank).
        assert lifecycle.severity == handoff.monitoring_priority
        assert lifecycle.severity in ("high", "medium", "low")
        # member expansion is EXACTLY the public marker member set.
        assert lifecycle.member_expansion_refs == tuple(sorted(
            marker.member_refs))
        # marker identity is the kind-prefixed public marker id.
        prefix = (c.D09_MARKER_PREFIX if lifecycle.marker_kind == "d09"
                  else c.D10_MARKER_PREFIX)
        assert lifecycle.marker_identity_ref == prefix + marker.marker_id
        assert lifecycle.r2_handoff_id == handoff.handoff_id
        assert lifecycle.lifecycle_action == handoff.action


def test_lifecycle_state_from_action_table() -> None:
    packet = b.build_s3_authority_packet()
    for lifecycle in packet.risk_lifecycle_authorities:
        if lifecycle.lifecycle_action == "create":
            assert lifecycle.lifecycle_state == "current"
        if lifecycle.lifecycle_action == "continue":
            assert lifecycle.lifecycle_state in ("current", "resolved")
        assert lifecycle.lifecycle_state in c.S3_LIFECYCLE_STATES


def test_d09_d10_hotspot_field_shapes_are_type_specific() -> None:
    """D09 hotspot uses separate risk/gap member fields; D10 alone carries
    a unified ``member_refs`` (contract P1-2 / reviewer blocker 2)."""
    packet = b.build_s3_authority_packet()
    d09_unit = next(u for u in packet.authority_units
                    if u.variant_kind == "d09_center_pattern_unit")
    d10_unit = next(u for u in packet.authority_units
                    if u.variant_kind == "d10_project_unit")
    assert d09_unit.d09_variant_payload is not None
    assert d09_unit.d10_variant_payload is None
    assert d10_unit.d10_variant_payload is not None
    assert d10_unit.d09_variant_payload is None
    d09_hotspot = d09_unit.d09_variant_payload.hotspots[0]
    d10_hotspot = d10_unit.d10_variant_payload.hotspots[0]
    assert d09_hotspot.member_risk_refs
    assert not hasattr(d09_hotspot, "member_refs")
    assert d10_hotspot.member_refs
    assert not hasattr(d10_hotspot, "member_risk_refs")


# ---------------------------------------------------------------------------
# Positive: exact authority projections close bidirectionally
# ---------------------------------------------------------------------------


def test_current_risk_planes_exact_bidirectional_closure() -> None:
    packet = b.build_s3_authority_packet()
    planes = b.project_current_risk_planes(packet, compare_declared=True)
    assert planes["errors"] == []
    declared = packet.audience_payload.current_risk_set
    assert sorted(planes["planes"]["high"]) == sorted(declared.high_risk_refs)
    assert sorted(planes["planes"]["medium"]) == sorted(
        declared.medium_risk_refs)
    assert sorted(planes["planes"]["low"]) == sorted(
        declared.low_risk_cluster_refs)
    assert sorted(planes["planes"]["resolved"]) == sorted(
        declared.resolved_history_refs)
    # mutually exclusive planes (unique reference sets).
    all_refs = (list(declared.high_risk_refs) + list(declared.medium_risk_refs)
                + list(declared.low_risk_cluster_refs)
                + list(declared.resolved_history_refs))
    assert len(all_refs) == len(set(all_refs))
    assert all(ref.startswith((c.D09_MARKER_PREFIX, c.D10_MARKER_PREFIX,
                               c.CLUSTER_REF_PREFIX))
               for ref in all_refs)


def test_center_cells_exact_authority_closure() -> None:
    """D09 marker members land in ``pattern_refs``, D10 members in
    ``individual_risk_refs``; a single member is never promoted to a
    pattern and no current member lacks a hotspot site binding."""
    packet = b.build_s3_authority_packet()
    cells = b.project_center_cells(packet)
    assert cells["errors"] == []
    for cell in cells["cells"]:
        assert cell.individual_risk_refs or cell.pattern_refs
        assert cell.severity in ("high", "medium", "low")
        if cell.individual_risk_refs:
            assert not cell.pattern_refs  # no single-member pattern upgrade
    site_order = cells["stable_site_order"]
    assert site_order == tuple(sorted(set(site_order)))


def test_low_cluster_ref_grammar_and_replay_presence() -> None:
    packet = b.build_s3_authority_packet()
    clusters = packet.audience_payload.low_risk_clusters
    assert clusters, "the synthetic packet must carry at least one low cluster"
    for cluster in clusters:
        expected_hash = c.cluster_content_hash(
            cluster.authority_receipt_ref, cluster.domain,
            cluster.site_ref, cluster.member_refs)
        assert cluster.content_hash == expected_hash
        assert cluster.cluster_ref == c.CLUSTER_REF_PREFIX + expected_hash
    # low clusters are serialized INSIDE the audience replay payload (P1-4):
    # touching a cluster member/content hash changes the replay hash.
    assert packet.audience_replay_content_hash == \
        c.audience_replay_content_hash(packet.audience_payload)
    replay_json = c.s3_canonical_json(packet.audience_payload)
    for cluster in clusters:
        assert cluster.cluster_ref in replay_json


def test_aggregate_receipt_set_identity_canonical() -> None:
    packet = b.build_s3_authority_packet()
    agg = packet.aggregate_receipt_set
    receipt_refs = tuple(sorted({
        c.RECEIPT_REF_PREFIX + unit.receipt_content_hash
        for unit in packet.authority_units}))
    marker_hashes = tuple(sorted({
        c.unit_variant_payload(unit).risk_marker.content_hash
        for unit in packet.authority_units
        if c.unit_variant_payload(unit).risk_marker is not None}))
    expected_id = c.aggregate_identity_id(
        receipt_refs, marker_hashes, agg.project_ref, agg.run_ref,
        agg.snapshot_ref, agg.cutoff_ref, agg.audience_contract_id)
    assert agg.aggregate_id == expected_id
    assert packet.audience_payload.current_risk_set.authority_receipt_ref \
        == agg.aggregate_id


def test_receipt_bindings_byte_exact_across_all_supplementals() -> None:
    """Every named supplemental binds the exact receipt: ref = 'receipt:' +
    canonical content hash, visibility decision id/hash and source
    revision-content pairs byte-equal to the receipt."""
    packet = _packet_with_all_supplementals()
    receipt_by_hash = {
        c.receipt_content_hash(unit.authority_receipt): unit.authority_receipt
        for unit in packet.authority_units}

    supplementals = list(packet.risk_lifecycle_authorities) \
        + list(packet.closure_authorities) \
        + list(packet.clinical_domain_authorities) \
        + list(packet.denominator_authorities) \
        + list(packet.layer_membership_authorities) \
        + list(packet.cutoff_authorities) \
        + list(packet.evaluation_limit_authorities) \
        + list(packet.coverage_authorities) \
        + list(packet.change_cause_mixture_authorities)
    assert supplementals, "expected at least one named supplemental"
    for authority in supplementals:
        assert authority.receipt_ref == \
            c.RECEIPT_REF_PREFIX + authority.receipt_hash
        receipt = receipt_by_hash[authority.receipt_hash]
        assert authority.visibility_decision_id == \
            receipt.visibility_decision_id
        assert authority.visibility_decision_hash == \
            receipt.visibility_decision_hash
        assert c.s3_canonical_bytes(
            authority.source_revision_content_pairs) == \
            c.s3_canonical_bytes(receipt.source_revision_content_pairs)
        assert authority.content_hash == c.s3_content_hash_excluding(
            authority, ("content_hash",))


def test_units_validate_receipt_content_hash_recipe() -> None:
    packet = b.build_s3_authority_packet()
    for unit in packet.authority_units:
        expected = c.receipt_content_hash(unit.authority_receipt)
        assert unit.receipt_content_hash == expected
        assert c.authority_receipt_ref(unit.authority_receipt) == \
            c.RECEIPT_REF_PREFIX + expected


# ---------------------------------------------------------------------------
# Positive: private/public plane separation
# ---------------------------------------------------------------------------


def test_true_hidden_only_mutation_keeps_audience() -> None:
    """A hidden-only private change must leave the audience replay
    identical while changing the packet integrity hash (P1-4 positive
    control)."""
    base = _packet_from_units(b.build_synthetic_units())
    before_replay = base.audience_replay_content_hash
    before_integrity = base.packet_integrity_hash

    units_in = b.build_synthetic_units()
    d10_in = units_in[0]
    audience = dc_replace(
        d10_in.bundle.audience,
        hidden_member_refs=("S3-HIDDEN-ONLY-001",), hidden_member_count=1)
    bundle = dc_replace(d10_in.bundle, audience=audience)
    hidden_units = (dc_replace(d10_in, bundle=bundle),) + units_in[1:]
    hidden = _packet_from_units(hidden_units)

    assert hidden.audience_replay_content_hash == before_replay
    assert hidden.packet_integrity_hash != before_integrity


def test_unit_rejects_hidden_member_in_projectable_plane() -> None:
    """A hidden member can never leak into the projectable plane (construct
    gate ``hidden_leaf_in_audience_hash``)."""
    units_in = b.build_synthetic_units()
    d10_in = units_in[0]
    unit = b.build_authority_unit(d10_in, "cda.test")
    assert unit.hidden_member_refs == ()
    with pytest.raises(c.S3ContractError):
        c.R5S3AuthorityUnitTagged(
            unit_ref=unit.unit_ref,
            variant_kind=unit.variant_kind,
            authority_receipt=unit.authority_receipt,
            receipt_content_hash=unit.receipt_content_hash,
            projectable_member_refs=unit.projectable_member_refs
            + ("S3-LEAK-001",),
            hidden_member_refs=unit.hidden_member_refs + ("S3-LEAK-001",),
            hidden_site_refs=unit.hidden_site_refs,
            source_unit_refs=unit.source_unit_refs,
            d09_variant_payload=unit.d09_variant_payload,
            d10_variant_payload=unit.d10_variant_payload,
            content_hash=unit.content_hash,
        )


# ---------------------------------------------------------------------------
# Negative: typed-input leaf promotion (contract P1-1)
# ---------------------------------------------------------------------------


def test_typed_input_leaf_promotion_rejected() -> None:
    """A D10 typed-input object (``EvidenceRef``) is never a public
    authority leaf: the structural gate fails closed with
    ``typed_input_leaf_promoted``."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _LeakyPayload:
        evidence: EvidenceRef

    leaky = _LeakyPayload(EvidenceRef(locator_id="S3-TYPED-EVIDENCE-001"))
    with pytest.raises(c.S3InvariantError) as excinfo:
        c.check_imported_objects_allowed(leaky)
    assert excinfo.value.error_code == "typed_input_leaf_promoted"


# ---------------------------------------------------------------------------
# Negative: identity / receipt / hash drift
# ---------------------------------------------------------------------------


def test_receipt_content_hash_drift_rejected() -> None:
    """A caller-supplied (drifted) receipt content hash is never trusted:
    the unit construction fails closed."""
    units_in = b.build_synthetic_units()
    unit = b.build_authority_unit(units_in[0], "cda.test")
    with pytest.raises(c.S3HashMismatchError):
        c.R5S3AuthorityUnitTagged(
            unit_ref=unit.unit_ref,
            variant_kind=unit.variant_kind,
            authority_receipt=unit.authority_receipt,
            receipt_content_hash="0" * 64,
            projectable_member_refs=unit.projectable_member_refs,
            hidden_member_refs=unit.hidden_member_refs,
            hidden_site_refs=unit.hidden_site_refs,
            source_unit_refs=unit.source_unit_refs,
            d09_variant_payload=unit.d09_variant_payload,
            d10_variant_payload=unit.d10_variant_payload,
            content_hash=unit.content_hash,
        )


def test_supplemental_receipt_ref_prefix_drift_rejected() -> None:
    """A named supplemental whose ``receipt_ref`` is not exactly
    ``'receipt:' + receipt_hash`` fails closed at construction (exact
    identity/receipt binding; the visibility/source pair byte-equality to
    the receipt is asserted in the positive binding test)."""
    units_in = b.build_synthetic_units()
    receipt = units_in[0].receipt
    with pytest.raises(c.S3ContractError):
        c.R5S3CutoffAuthority(
            authority_id="S3-CUTOFF-PREFIX-BAD",
            cutoff_ref=b.SYNTHETIC_CUTOFF_REF,
            receipt_hash=c.receipt_content_hash(receipt),
            receipt_ref="cutoff:" + c.receipt_content_hash(receipt),
            visibility_decision_id=receipt.visibility_decision_id,
            visibility_decision_hash=receipt.visibility_decision_hash,
            source_revision_content_pairs=(
                receipt.source_revision_content_pairs),
            offline_test_only=True,
            content_hash="",
        )


def test_low_cluster_canonical_ref_drift_rejected() -> None:
    """A low-risk cluster whose ``cluster_ref`` drifts from
    ``'cluster:' + content_hash`` fails closed (P1-4)."""
    packet = b.build_s3_authority_packet()
    cluster = packet.audience_payload.low_risk_clusters[0]
    with pytest.raises(c.S3ContractError):
        c.R5S3LowRiskCluster(
            cluster_ref=c.CLUSTER_REF_PREFIX + "0" * 64,
            authority_receipt_ref=cluster.authority_receipt_ref,
            domain=cluster.domain,
            site_ref=cluster.site_ref,
            member_refs=cluster.member_refs,
            content_hash=cluster.content_hash,
        )


def test_packet_replay_hash_drift_rejected() -> None:
    packet = b.build_s3_authority_packet()
    with pytest.raises(c.S3HashMismatchError):
        c.R5S3AuthorityPacket(
            packet_id=packet.packet_id,
            schema=packet.schema, status=packet.status,
            authority_mode=packet.authority_mode,
            authority_units=packet.authority_units,
            aggregate_receipt_set=packet.aggregate_receipt_set,
            risk_lifecycle_authorities=packet.risk_lifecycle_authorities,
            closure_authorities=packet.closure_authorities,
            clinical_domain_authorities=packet.clinical_domain_authorities,
            denominator_authorities=packet.denominator_authorities,
            layer_membership_authorities=packet.layer_membership_authorities,
            cutoff_authorities=packet.cutoff_authorities,
            evaluation_limit_authorities=packet.evaluation_limit_authorities,
            coverage_authorities=packet.coverage_authorities,
            change_cause_mixture_authorities=(
                packet.change_cause_mixture_authorities),
            audience_payload=packet.audience_payload,
            audience_replay_content_hash="0" * 64,
            packet_integrity_hash=None,
        )


def test_packet_id_grammar_drift_rejected() -> None:
    packet = b.build_s3_authority_packet()
    with pytest.raises(c.S3ContractError):
        c.R5S3AuthorityPacket(
            packet_id="r5-s3-contract::" + packet.audience_replay_content_hash,
            schema=packet.schema, status=packet.status,
            authority_mode=packet.authority_mode,
            authority_units=packet.authority_units,
            aggregate_receipt_set=packet.aggregate_receipt_set,
            risk_lifecycle_authorities=packet.risk_lifecycle_authorities,
            closure_authorities=packet.closure_authorities,
            clinical_domain_authorities=packet.clinical_domain_authorities,
            denominator_authorities=packet.denominator_authorities,
            layer_membership_authorities=packet.layer_membership_authorities,
            cutoff_authorities=packet.cutoff_authorities,
            evaluation_limit_authorities=packet.evaluation_limit_authorities,
            coverage_authorities=packet.coverage_authorities,
            change_cause_mixture_authorities=(
                packet.change_cause_mixture_authorities),
            audience_payload=packet.audience_payload,
            audience_replay_content_hash=packet.audience_replay_content_hash,
            packet_integrity_hash=None,
        )


def test_packet_integrity_hash_drift_rejected() -> None:
    packet = b.build_s3_authority_packet()
    with pytest.raises(c.S3HashMismatchError):
        c.R5S3AuthorityPacket(
            packet_id=packet.packet_id,
            schema=packet.schema, status=packet.status,
            authority_mode=packet.authority_mode,
            authority_units=packet.authority_units,
            aggregate_receipt_set=packet.aggregate_receipt_set,
            risk_lifecycle_authorities=packet.risk_lifecycle_authorities,
            closure_authorities=packet.closure_authorities,
            clinical_domain_authorities=packet.clinical_domain_authorities,
            denominator_authorities=packet.denominator_authorities,
            layer_membership_authorities=packet.layer_membership_authorities,
            cutoff_authorities=packet.cutoff_authorities,
            evaluation_limit_authorities=packet.evaluation_limit_authorities,
            coverage_authorities=packet.coverage_authorities,
            change_cause_mixture_authorities=(
                packet.change_cause_mixture_authorities),
            audience_payload=packet.audience_payload,
            audience_replay_content_hash=packet.audience_replay_content_hash,
            packet_integrity_hash="0" * 64,
        )


def test_project_run_snapshot_cutoff_identity_drift_rejected() -> None:
    """The aggregate receipt-set identity requires ONE shared
    project/run/snapshot/cutoff/audience_contract identity; a drifted
    project_ref fails closed."""
    units_in = b.build_synthetic_units()
    u_a = b.build_authority_unit(units_in[0], "cda.a")
    drifted_receipt = dc_replace(units_in[1].receipt,
                                 project_ref="S3-PROJECT-DRIFTED")
    drifted = b.S3SyntheticUnit("d09", "S3-UNIT-D09-DRIFT", units_in[1].bundle,
                                drifted_receipt, units_in[1].clinical_domain,
                                "d09")
    u_b = b.build_authority_unit(drifted, "cda.b")
    with pytest.raises(b.S3AuthorityBuilderError):
        b.build_aggregate_receipt_set((u_a, u_b))


# ---------------------------------------------------------------------------
# Negative: unknown enums / lifecycle shape violations
# ---------------------------------------------------------------------------


def test_lifecycle_unknown_severity_fails_closed() -> None:
    """``critical``/``unknown``/``unmapped`` monitoring priorities never
    reach a lifecycle authority (severity is high/medium/low only)."""
    units_in = b.build_synthetic_units()
    unit_in = units_in[0]
    marker = unit_in.bundle.risk_marker
    handoff = dc_replace(unit_in.bundle.r2_handoff,
                         monitoring_priority="critical")
    with pytest.raises(b.S3AuthorityBuilderError):
        b.build_lifecycle_authority(
            authority_id="S3-LIFECYCLE-TEST",
            marker_kind="d10", marker=marker, handoff=handoff,
            clinical_domain_ref="cda.test", receipt=unit_in.receipt)


def test_change_cause_mixture_requires_two_causes() -> None:
    """A single D10 cause can never be promoted to a mixture
    (``mixed_d10_cause``)."""
    units_in = b.build_synthetic_units()
    with pytest.raises(c.S3ContractError):
        b.build_change_cause_mixture_authority(
            "S3-CHANGE-CAUSE-MIXTURE-BAD", ("data",), units_in[0].receipt)


def test_cutoff_authority_offsets_unknown_coverage_state_fails_closed() -> None:
    """``not_evaluable`` is never a closed coverage state (the coverage
    enum is complete/partial/truncated/unknown/not_applicable)."""
    units_in = b.build_synthetic_units()
    with pytest.raises(c.S3ContractError):
        b.build_coverage_authority("S3-COVERAGE-BAD", "not_evaluable",
                                   units_in[0].receipt)


def test_resolved_lifecycle_requires_closure_authority() -> None:
    """A resolved lifecycle without its exact closure authority fails
    closed (``resolved_without_lifecycle_authority``)."""
    units_in = b.build_synthetic_units()
    unit_in = units_in[2]
    marker = unit_in.bundle.risk_marker
    handoff = unit_in.bundle.r2_handoff
    with pytest.raises(c.S3ContractError):
        c.R5S3RiskLifecycleAuthority(
            authority_id="S3-LIFECYCLE-NOCLOSURE",
            marker_kind="d09",
            marker_identity_ref=c.D09_MARKER_PREFIX + marker.marker_id,
            marker_id=marker.marker_id,
            marker_content_hash=marker.content_hash,
            receipt_hash=c.receipt_content_hash(unit_in.receipt),
            receipt_ref=c.authority_receipt_ref(unit_in.receipt),
            visibility_decision_id=unit_in.receipt.visibility_decision_id,
            visibility_decision_hash=unit_in.receipt.visibility_decision_hash,
            source_revision_content_pairs=(
                unit_in.receipt.source_revision_content_pairs),
            clinical_domain_ref="cda.test",
            severity="medium",
            lifecycle_state="resolved",
            lifecycle_action="continue",
            r2_handoff_id=handoff.handoff_id,
            r2_handoff_ref="r2:" + handoff.handoff_id,
            member_expansion_refs=tuple(sorted(marker.member_refs)),
            closure_authority_ref=None,
            prior_marker_identity_ref=c.D09_MARKER_PREFIX + marker.marker_id,
            offline_test_only=True,
            content_hash="",
        )


def test_propose_close_never_resolves() -> None:
    """``propose_close`` keeps the current/proposed-close lifecycle and
    MUST NOT resolve (packet-attack ``propose_close_resolved``)."""
    units_in = b.build_synthetic_units()
    unit_in = units_in[1]
    marker = unit_in.bundle.risk_marker
    handoff = unit_in.bundle.r2_handoff
    with pytest.raises(c.S3ContractError):
        c.R5S3RiskLifecycleAuthority(
            authority_id="S3-LIFECYCLE-PROPOSE",
            marker_kind="d09",
            marker_identity_ref=c.D09_MARKER_PREFIX + marker.marker_id,
            marker_id=marker.marker_id,
            marker_content_hash=marker.content_hash,
            receipt_hash=c.receipt_content_hash(unit_in.receipt),
            receipt_ref=c.authority_receipt_ref(unit_in.receipt),
            visibility_decision_id=unit_in.receipt.visibility_decision_id,
            visibility_decision_hash=unit_in.receipt.visibility_decision_hash,
            source_revision_content_pairs=(
                unit_in.receipt.source_revision_content_pairs),
            clinical_domain_ref="cda.test",
            severity="low",
            lifecycle_state="resolved",
            lifecycle_action="propose_close",
            r2_handoff_id=handoff.handoff_id,
            r2_handoff_ref="r2:" + handoff.handoff_id,
            member_expansion_refs=tuple(sorted(marker.member_refs)),
            closure_authority_ref="S3-CLOSURE-TEST",
            prior_marker_identity_ref=None,
            offline_test_only=True,
            content_hash="",
        )


# ---------------------------------------------------------------------------
# Negative: duplicate / dangling identities
# ---------------------------------------------------------------------------


def test_duplicate_unit_identity_rejected() -> None:
    """Two authority units sharing one ``unit_ref`` fail closed at packet
    assembly (sorted-unique by unit_ref)."""
    units_in = b.build_synthetic_units()
    u0 = b.build_authority_unit(units_in[0], "cda.a")
    u1 = dc_replace(
        b.build_authority_unit(units_in[0], "cda.a"), unit_ref=u0.unit_ref)
    # rebuild the aggregate over the (now identical) units is irrelevant:
    # the packet must reject the duplicate.
    with pytest.raises(c.S3ContractError):
        b.assemble_packet(
            (u0, u1),
            b.build_aggregate_receipt_set((u0, u1)),
            (), (), (), (), (), (), (), (), (),
        )


def test_dangling_lifecycle_identity_rejected() -> None:
    """A marker identity ref with no matching lifecycle authority is a
    dangling identity and fails closed in the projector/index lookup."""
    packet = b.build_s3_authority_packet()
    with pytest.raises(c.S3ContractError):
        b._lifecycle_by_ref(packet, c.D09_MARKER_PREFIX + "no-such-marker")


# ---------------------------------------------------------------------------
# Positive: named supplemental exactness
# ---------------------------------------------------------------------------


def test_named_supplementals_are_exact_typed_objects() -> None:
    """Every named supplemental is a frozen dataclass with the schema-declared
    exact key set and closed enums (no generic dict authority)."""
    packet = b.build_s3_authority_packet()
    expected_names = (
        "R5S3RiskLifecycleAuthority", "R5S3ClosureAuthority",
        "R5S3ClinicalDomainAuthority", "R5S3DenominatorAuthority",
        "R5S3LayerMembershipAuthority", "R5S3CutoffAuthority",
        "R5S3EvaluationLimitAuthority", "R5S3CoverageAuthority",
        "R5S3ChangeCauseMixtureAuthority")
    for name in expected_names:
        cls = getattr(c, name)
        from dataclasses import is_dataclass, fields
        assert is_dataclass(cls)
        assert fields(cls), name
    assert packet.cutoff_authorities
    cutoff = packet.cutoff_authorities[0]
    assert cutoff.cutoff_ref == b.SYNTHETIC_CUTOFF_REF
    limit = packet.evaluation_limit_authorities[0]
    assert tuple(limit.evaluation_limit_refs) == tuple(
        limit.evaluation_limit_values) == (b.SYNTHETIC_EVALUATION_LIMIT_D10,)
    coverage = packet.coverage_authorities[0]
    assert coverage.coverage_state == "complete"


# ---------------------------------------------------------------------------
# Independent runtime review (REVISE_R5_S3): verifier-owned supplemental
# receipt bindings must survive a full coordinated packet re-sign.
# ---------------------------------------------------------------------------

_ALL_SUPPLEMENTAL_KINDS = (
    "risk_lifecycle", "closure", "clinical_domain", "denominator",
    "layer_membership", "cutoff", "evaluation_limit", "coverage",
    "change_cause_mixture",
)

_SUPPLEMENTAL_COLLECTION_FIELD = {
    "risk_lifecycle": "risk_lifecycle_authorities",
    "closure": "closure_authorities",
    "clinical_domain": "clinical_domain_authorities",
    "denominator": "denominator_authorities",
    "layer_membership": "layer_membership_authorities",
    "cutoff": "cutoff_authorities",
    "evaluation_limit": "evaluation_limit_authorities",
    "coverage": "coverage_authorities",
    "change_cause_mixture": "change_cause_mixture_authorities",
}


def _resign_packet(full, **collection_overrides) -> c.R5S3AuthorityPacket:
    """Rebuild the packet with the given authority-collection overrides and
    recompute every dependent object/root hash (coordinated re-sign)."""
    return b.assemble_packet(
        full.authority_units,
        full.aggregate_receipt_set,
        collection_overrides.get("risk_lifecycle_authorities",
                                 full.risk_lifecycle_authorities),
        collection_overrides.get("closure_authorities",
                                 full.closure_authorities),
        collection_overrides.get("clinical_domain_authorities",
                                 full.clinical_domain_authorities),
        collection_overrides.get("denominator_authorities",
                                 full.denominator_authorities),
        collection_overrides.get("layer_membership_authorities",
                                 full.layer_membership_authorities),
        collection_overrides.get("cutoff_authorities",
                                 full.cutoff_authorities),
        collection_overrides.get("evaluation_limit_authorities",
                                 full.evaluation_limit_authorities),
        collection_overrides.get("coverage_authorities",
                                 full.coverage_authorities),
        collection_overrides.get("change_cause_mixture_authorities",
                                 full.change_cause_mixture_authorities),
    )


def _supplemental_with(original, **overrides):
    """Reconstruct a supplemental with the given field overrides and RECOMPUTE
    its canonical content hash (internal consistency), mirroring a coordinated
    re-sign attacker who keeps the object self-consistent."""
    from dataclasses import fields as dc_fields
    values = {f.name: getattr(original, f.name)
              for f in dc_fields(original)}
    values.update(overrides)
    obj_dict = {k: v for k, v in values.items() if k != "content_hash"}
    values["content_hash"] = c.s3_sha256(c.s3_canonical_bytes(obj_dict))
    return type(original)(**values)


def _packet_with_all_supplementals() -> c.R5S3AuthorityPacket:
    """A pristine packet that carries a member in EVERY one of the nine
    supplemental collections (the default builder leaves denominator and
    layer-membership empty)."""
    from decimal import Decimal
    packet = b.build_s3_authority_packet()
    receipt = packet.authority_units[0].authority_receipt
    members = packet.authority_units[0].projectable_member_refs
    denominator = b.build_denominator_authority(
        authority_id="S3-DENOM-TEST-001",
        denominator_kind="treated_subjects",
        denominator_state="closed_positive",
        denominator_value=Decimal(8),
        measure_unit="subject",
        member_refs=members,
        exclusion_refs=(),
        receipt=receipt,
    )
    layer = b.build_layer_membership_authority(
        authority_id="S3-LAYER-TEST-001",
        layer="individual_risk",
        membership_state="projectable",
        member_refs=members,
        source_count_value=Decimal(len(members)),
        source_count_ref=("mm_r4.d10_projection:D10ProjectionCountSurface."
                          "individual_risk_count"),
        disabled_state="enabled",
        receipt=receipt,
    )
    return _resign_packet(
        packet,
        denominator_authorities=(denominator,),
        layer_membership_authorities=(layer,),
    )


@pytest.mark.parametrize("kind", _ALL_SUPPLEMENTAL_KINDS)
def test_reviewer_supplemental_content_hash_mutation_rejected(kind: str) -> None:
    """Scenario 1: changing the canonical ``content_hash`` on ANY of the nine
    supplemental collections, then re-signing every packet hash, must be
    rejected with ``supplemental_content_hash_mismatch``."""
    full = _packet_with_all_supplementals()
    field = _SUPPLEMENTAL_COLLECTION_FIELD[kind]
    collection = list(getattr(full, field))
    assert collection, kind
    obj = collection[0]
    object.__setattr__(obj, "content_hash", "0" * 64)
    replaced = tuple(item if item is not obj else obj for item in collection)
    with pytest.raises(c.S3InvariantError) as excinfo:
        _resign_packet(full, **{field: replaced})
    assert excinfo.value.error_code == "supplemental_content_hash_mismatch"


def test_reviewer_closure_receipt_hash_drift_rejected() -> None:
    """Scenario 2: changing closure ``receipt_hash``, then recomputing the
    closure content hash AND all packet hashes, must be rejected (the new
    receipt does not resolve to exactly one complete unit receipt)."""
    full = _packet_with_all_supplementals()
    closure = full.closure_authorities[0]
    drifted = _supplemental_with(
        closure, receipt_hash="e" * 64,
        receipt_ref=c.RECEIPT_REF_PREFIX + "e" * 64)
    with pytest.raises(c.S3InvariantError) as excinfo:
        _resign_packet(full, closure_authorities=(drifted,))
    assert excinfo.value.error_code == "supplemental_receipt_missing"


def test_reviewer_missing_receipt_rejected() -> None:
    """A quantified supplemental whose receipt resolves to no complete unit
    receipt fails closed even after a full re-sign."""
    full = _packet_with_all_supplementals()
    denominator = full.denominator_authorities[0]
    drifted = _supplemental_with(
        denominator, receipt_hash="0" * 64,
        receipt_ref=c.RECEIPT_REF_PREFIX + "0" * 64)
    with pytest.raises(c.S3InvariantError) as excinfo:
        _resign_packet(full, denominator_authorities=(drifted,))
    assert excinfo.value.error_code == "supplemental_receipt_missing"


def test_reviewer_ambiguous_unit_receipt_resolution_rejected() -> None:
    """Two authority units sharing one complete receipt contents make the
    supplemental receipt resolution ambiguous and fail closed."""
    units_in = b.build_synthetic_units()
    unit_dup = dc_replace(units_in[0], unit_ref="S3-UNIT-D10-DUP")
    u0 = b.build_authority_unit(units_in[0], "cda.a")
    u1 = b.build_authority_unit(unit_dup, "cda.a")
    assert u0.receipt_content_hash == u1.receipt_content_hash
    with pytest.raises(c.S3InvariantError) as excinfo:
        b.assemble_packet(
            (u0, u1),
            b.build_aggregate_receipt_set((u0, u1)),
            (), (), (), (), (), (), (), (), ())
    assert excinfo.value.error_code == \
        "supplemental_receipt_cardinality_mismatch"


def test_reviewer_visibility_drift_rejected() -> None:
    """A supplemental whose visibility decision id drifts from the resolved
    receipt fails closed after a full re-sign."""
    full = _packet_with_all_supplementals()
    cutoff = full.cutoff_authorities[0]
    drifted = _supplemental_with(
        cutoff, visibility_decision_id="S3-VIS-DRIFTED")
    with pytest.raises(c.S3InvariantError) as excinfo:
        _resign_packet(full, cutoff_authorities=(drifted,))
    assert excinfo.value.error_code == \
        "supplemental_visibility_binding_mismatch"


def test_reviewer_source_pairs_drift_rejected() -> None:
    """A supplemental whose source revision/content pairs drift from the
    resolved receipt fails closed after a full re-sign."""
    full = _packet_with_all_supplementals()
    cutoff = full.cutoff_authorities[0]
    drifted = _supplemental_with(
        cutoff,
        source_revision_content_pairs=(
            c.SourceRevisionContentPair(
                revision_id="S3-REV-DRIFT-001",
                content_hash=c.s3_sha256(b"drifted")),))
    with pytest.raises(c.S3InvariantError) as excinfo:
        _resign_packet(full, cutoff_authorities=(drifted,))
    assert excinfo.value.error_code == "supplemental_source_pairs_mismatch"


def test_reviewer_offline_only_state_drift_rejected() -> None:
    """A supplemental whose ``offline_test_only`` flag drifts fails closed
    (the object is kept internally consistent by recomputing the hash)."""
    full = _packet_with_all_supplementals()
    cutoff = full.cutoff_authorities[0]
    object.__setattr__(cutoff, "offline_test_only", False)
    from dataclasses import fields as dc_fields
    obj_dict = {f.name: getattr(cutoff, f.name)
                for f in dc_fields(cutoff) if f.name != "content_hash"}
    object.__setattr__(cutoff, "content_hash",
                       c.s3_sha256(c.s3_canonical_bytes(obj_dict)))
    with pytest.raises(c.S3InvariantError) as excinfo:
        _resign_packet(full, cutoff_authorities=(cutoff,))
    assert excinfo.value.error_code == "supplemental_type_mismatch"


def test_reviewer_inplace_content_hash_mutation_rejected_by_validator() -> None:
    """Scenario 1 via the validator path (not only at construction): an
    in-place supplemental content_hash mutation followed by a coordinated
    packet re-sign is rejected by ``validate_s3_authority_packet`` -- the
    same entry point the projection layer calls first."""
    full = b.build_s3_authority_packet()
    closure = full.closure_authorities[0]
    object.__setattr__(closure, "content_hash", "0" * 64)
    replay = c.audience_replay_content_hash(full.audience_payload)
    object.__setattr__(full, "audience_replay_content_hash", replay)
    object.__setattr__(full, "packet_id", c.PACKET_ID_PREFIX + ":" + replay)
    object.__setattr__(
        full, "packet_integrity_hash",
        c.compute_packet_integrity_hash(full))
    result = c.validate_s3_authority_packet(full)
    assert not result["valid"]
    assert "supplemental_content_hash_mismatch" in result["reasons"]


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _packet_from_units(units_in) -> c.R5S3AuthorityPacket:
    """Assemble a full packet from synthetic units through the public
    authority-builder APIs (mirrors ``build_s3_authority_packet``)."""
    domain_ids = {unit.unit_ref: b._domain_authority_id(unit)
                  for unit in units_in}
    domain_authorities = tuple(
        b.build_clinical_domain_authority(domain_ids[unit.unit_ref],
                                          unit.clinical_domain, unit.receipt)
        for unit in units_in)
    units = tuple(
        b.build_authority_unit(unit, domain_ids[unit.unit_ref])
        for unit in units_in)
    aggregate = b.build_aggregate_receipt_set(units)
    lifecycles = []
    closures = []
    for unit, unit_in in zip(units, units_in):
        variant = c.unit_variant_payload(unit)
        marker = variant.risk_marker
        handoff = variant.r2_handoff
        assert marker is not None and handoff is not None
        domain_ref = domain_ids[unit.unit_ref]
        if unit_in.kind == "d09" and unit.unit_ref == \
                b.SYNTHETIC_UNIT_D09_RESOLVED_REF:
            closure = b.build_closure_authority(
                "S3-CLOSURE-D09-002", "S3-CLOSE-DECISION-D09-002",
                c.D09_MARKER_PREFIX + marker.marker_id,
                b.SYNTHETIC_PRIOR_INSTANCE_D09_RESOLVED,
                unit.authority_receipt)
            closures.append(closure)
            lifecycle = b.build_lifecycle_authority(
                authority_id="S3-LIFECYCLE-" + unit.unit_ref,
                marker_kind="d09", marker=marker, handoff=handoff,
                clinical_domain_ref=domain_ref,
                receipt=unit.authority_receipt,
                closure_authority_ref=closure.closure_authority_id,
                prior_marker_identity_ref=c.D09_MARKER_PREFIX
                + marker.marker_id)
        else:
            lifecycle = b.build_lifecycle_authority(
                authority_id="S3-LIFECYCLE-" + unit.unit_ref,
                marker_kind=unit_in.kind, marker=marker, handoff=handoff,
                clinical_domain_ref=domain_ref,
                receipt=unit.authority_receipt,
                prior_marker_identity_ref=None)
        lifecycles.append(lifecycle)
    return b.assemble_packet(
        units, aggregate,
        tuple(sorted(lifecycles, key=lambda l: l.marker_identity_ref)),
        tuple(closures),
        tuple(sorted(domain_authorities, key=lambda d: d.authority_id)),
        (), (), (), (), (), (),
    )
