"""Worker-02 gates for the renderer-neutral R5-S3 public projection.

These tests deliberately exercise the projection boundary rather than the
authority builder's construction tests.  In particular, they keep the
declared audience payload as an untrusted comparison target, exercise the
full-set/cluster split, and check that quantitative layers retain independent
state instead of inventing a cross-layer total.
"""

from __future__ import annotations

import sys
from dataclasses import replace as dc_replace
from pathlib import Path

import pytest

_POC_ROOT = Path(__file__).resolve().parents[2]
for _src in (
    _POC_ROOT / "medical_monitoring_ai_native_r1" / "src",
    _POC_ROOT / "medical_monitoring_ai_native_r2" / "src",
    _POC_ROOT / "medical_monitoring_ai_native_r3" / "src",
    _POC_ROOT / "medical_monitoring_ai_native_r4" / "src",
    Path(__file__).resolve().parents[1] / "src",
):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4.d10_projection import D10ProjectProjection, D10ProjectionBundle  # noqa: E402
from mm_r5 import s3_authority_builder as b  # noqa: E402
from mm_r5 import s3_contracts as c  # noqa: E402
from mm_r5 import s3_projection as p  # noqa: E402


def _packet_from_units(units_in):
    """Assemble a packet from synthetic units through public builder APIs."""
    domain_ids = {unit.unit_ref: b._domain_authority_id(unit)
                  for unit in units_in}
    domains = tuple(
        b.build_clinical_domain_authority(
            domain_ids[unit.unit_ref], unit.clinical_domain, unit.receipt)
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
        if unit_in.kind == "d09" and unit.unit_ref == b.SYNTHETIC_UNIT_D09_RESOLVED_REF:
            closure = b.build_closure_authority(
                "S3-CLOSURE-D09-002", "S3-CLOSE-DECISION-D09-002",
                c.D09_MARKER_PREFIX + marker.marker_id,
                b.SYNTHETIC_PRIOR_INSTANCE_D09_RESOLVED,
                unit.authority_receipt)
            closures.append(closure)
            lifecycle = b.build_lifecycle_authority(
                authority_id="S3-LIFECYCLE-" + unit.unit_ref,
                marker_kind="d09", marker=marker, handoff=handoff,
                clinical_domain_ref=domain_ids[unit.unit_ref],
                receipt=unit.authority_receipt,
                closure_authority_ref=closure.closure_authority_id,
                prior_marker_identity_ref=c.D09_MARKER_PREFIX + marker.marker_id)
        else:
            prior = (c.D10_MARKER_PREFIX + marker.marker_id
                     if unit_in.kind == "d10" else None)
            lifecycle = b.build_lifecycle_authority(
                authority_id="S3-LIFECYCLE-" + unit.unit_ref,
                marker_kind=unit_in.kind, marker=marker, handoff=handoff,
                clinical_domain_ref=domain_ids[unit.unit_ref],
                receipt=unit.authority_receipt,
                prior_marker_identity_ref=prior)
        lifecycles.append(lifecycle)
    # Match the builder's deterministic fixture supplementals.  They bind to
    # the first (base) D10 receipt and therefore remain valid as more units
    # are added for full-set tests.
    first = units[0].authority_receipt
    return b.assemble_packet(
        units, aggregate,
        tuple(sorted(lifecycles, key=lambda item: item.marker_identity_ref)),
        tuple(closures),
        tuple(sorted(domains, key=lambda item: item.authority_id)),
        (), (),
        (b.build_cutoff_authority("S3-CUTOFF-AUTHORITY-001",
                                  b.SYNTHETIC_CUTOFF_REF, first),),
        (b.build_evaluation_limit_authority(
            "S3-EVALLIMIT-AUTHORITY-001",
            (b.SYNTHETIC_EVALUATION_LIMIT_D10,),
            (b.SYNTHETIC_EVALUATION_LIMIT_D10,), first),),
        (b.build_coverage_authority("S3-COVERAGE-AUTHORITY-001", "complete",
                                    first),),
        (b.build_change_cause_mixture_authority(
            "S3-CHANGE-CAUSE-MIXTURE-001", ("data", "coverage"), first),),
    )


def _extra_d10(label: str, priority: str = "high", change_kind: str = "continued",
               change_cause: str | None = "data") -> b.S3SyntheticUnit:
    """Create one deterministic extra D10 public unit for cardinality tests."""
    members = (f"S3-MEMBER-{label}-001", f"S3-MEMBER-{label}-002")
    site = f"S3-SITE-{label}"
    subject = f"S3-SUBJ-{label}"
    marker = b._build_d10_marker(label, members)
    handoff = b._build_d10_handoff(
        label, "continue", priority, members, b.SYNTHETIC_PRIOR_INSTANCE_D10)
    audience = b._build_d10_audience(f"S3-SCOPE-{label}", members, site)
    counts = b._build_d10_counts(label, members, site)
    version = b._build_d10_version(label)
    center = b._build_d10_center_row(site, members)
    hotspot = b._build_d10_hotspot(label, site, subject, members, priority)
    trend = b._build_d10_trend(label)
    section = dc_replace(
        b._build_d10_change_section(),
        change_kind=change_kind,
        change_cause=change_cause,
    )
    projection = D10ProjectProjection(
        projection_id=f"S3-PROJECTION-{label}",
        projection_version_ref=version.projection_version_id,
        change_section=section,
        center_distribution=(center,),
        trend_surface=trend,
        warning_markers=(),
        risk_marker_ref=marker.marker_id,
        hotspot_site_refs=(site,),
        hotspot_subject_refs=(subject,),
        count_surface_ref=b._fixture_hash(f"count.{label}"),
        coverage_refs=(),
        deep_link_target_refs=(),
        query_draft_ref=None,
        r2_handoff_ref=handoff.handoff_id,
        audience_text_ref=b.SYNTHETIC_AUDIENCE_CONTRACT_ID,
        projection_content_hash=b._fixture_hash(f"projection.{label}"),
    )
    bundle = D10ProjectionBundle(
        audience=audience,
        counts=counts,
        version=version,
        change_section=section,
        center_distribution=(center,),
        trend_surface=trend,
        warning_markers=(),
        risk_marker=marker,
        hotspots=(hotspot,),
        deep_links=(),
        query_draft=None,
        r2_handoff=handoff,
        project_projection=projection,
    )
    return b.S3SyntheticUnit(
        "d10", f"S3-UNIT-{label}", bundle,
        b._build_receipt("d10", f"S3-U-{label}"), "mh", "d10")


def test_surface_projects_all_public_surfaces_and_audit_traces() -> None:
    packet = b.build_s3_authority_packet()
    surface = p.project_surface(packet)

    assert p.validate_s3_projection(packet) == {"valid": True, "reasons": ()}
    assert surface.current_risk.high_risk_refs
    assert surface.current_risk.medium_risk_refs == ()
    assert surface.current_risk.low_risk_cluster_refs
    assert surface.current_risk.resolved_history_refs
    assert len(surface.quantity_layers) == len(c.S3_LAYERS) == 8
    assert surface.center_graph.stable_site_order == tuple(sorted(
        surface.center_graph.stable_site_order))
    assert surface.cockpit.authority_receipt_ref == packet.aggregate_receipt_set.aggregate_id

    for leaf in surface.current_risk.risk_leaves:
        assert leaf.trace.authority_receipt_ref.startswith("receipt:")
        assert leaf.trace.visibility_decision_id
        assert leaf.trace.source_revision_content_pairs
        assert leaf.trace.public_projection_content_hash
    for leaf in surface.current_risk.cluster_leaves:
        assert leaf.trace.source_revision_content_pairs
    for layer in surface.quantity_layers:
        assert layer.layer in c.S3_LAYERS
        for leaf in layer.counts:
            assert leaf.visibility_decision_id
            assert leaf.source_revision_content_pairs
            assert leaf.authority_content_hash
            assert leaf.public_projection_content_hash
    for leaf in surface.center_graph.cell_leaves:
        assert leaf.trace_refs
        assert leaf.traces
        assert all(trace.source_revision_content_pairs for trace in leaf.traces)


def test_high_and_medium_planes_are_full_sets_not_top_n() -> None:
    base = list(b.build_synthetic_units())
    extras = [_extra_d10(f"EXTRA-{i:02d}", "high") for i in range(1, 6)]
    packet = _packet_from_units(tuple([base[0], *extras, base[1], base[2]]))
    surface = p.project_surface(packet)
    assert len(surface.current_risk.high_risk_refs) == 6
    # Low clusters have their own expandable leaves; risk leaves therefore
    # contain six high plus the resolved history leaf.
    assert len(surface.current_risk.risk_leaves) == 7
    assert surface.current_risk.high_risk_refs == tuple(sorted(
        surface.current_risk.high_risk_refs))
    assert not any("top" in field.name.lower()
                   for field in surface.current_risk.__dataclass_fields__.values())


def test_low_cluster_expands_and_singleton_d09_stays_pattern() -> None:
    surface = p.project_surface(b.build_s3_authority_packet())
    cluster = surface.current_risk.low_risk_clusters[0]
    assert cluster.member_refs
    low_leaf = next(leaf for leaf in surface.current_risk.cluster_leaves
                    if leaf.cluster_ref == cluster.cluster_ref)
    assert low_leaf.member_refs == cluster.member_refs
    d09_cells = [cell for cell in surface.center_graph.cells if cell.pattern_refs]
    assert d09_cells
    assert all(not cell.individual_risk_refs for cell in d09_cells)
    assert all(len(cell.pattern_refs) >= 1 for cell in d09_cells)


def test_quantity_layers_are_independent_and_expose_limits_without_sum() -> None:
    surface = p.project_surface(b.build_s3_authority_packet())
    by_layer = {layer.layer: layer for layer in surface.quantity_layers}
    assert set(by_layer) == set(c.S3_LAYERS)
    assert by_layer["individual_risk"].denominator_state == "closed_positive"
    assert by_layer["individual_risk"].denominator_value == 8
    assert by_layer["project_signal"].denominator_policy == "not_applicable"
    assert by_layer["project_signal"].denominator_value is None
    assert by_layer["project_signal"].rate_state == "not_evaluable"
    assert by_layer["individual_risk"].evaluation_limit_refs == (
        b.SYNTHETIC_EVALUATION_LIMIT_D10,)
    assert all("total" not in field.name.lower()
               for layer in surface.quantity_layers
               for field in layer.__dataclass_fields__.values())


def test_replay_is_stable_and_declared_mutations_fail_closed() -> None:
    first = p.project_surface(b.build_s3_authority_packet())
    second = p.project_surface(b.build_s3_authority_packet())
    assert first == second
    assert first.content_hash == second.content_hash

    packet = b.build_s3_authority_packet()
    declared = packet.audience_payload.current_risk_set
    object.__setattr__(declared, "high_risk_refs",
                       declared.high_risk_refs + ("d10:caller-mutated",))
    result = p.validate_s3_projection(packet)
    assert result["valid"] is False
    assert result["reasons"]


def test_resolved_current_conflict_and_hidden_mutation_fail_closed() -> None:
    packet = b.build_s3_authority_packet()
    current = packet.audience_payload.current_risk_set
    object.__setattr__(current, "high_risk_refs",
                       current.high_risk_refs + current.resolved_history_refs)
    result = p.validate_s3_projection(packet)
    assert result["valid"] is False
    assert result["reasons"]

    packet = b.build_s3_authority_packet()
    unit = packet.authority_units[0]
    object.__setattr__(unit, "hidden_member_refs", ("S3-HIDDEN-MUTATION",))
    result = p.validate_s3_projection(packet)
    assert result["valid"] is False
    assert result["reasons"]


@pytest.mark.parametrize("kind", c.S3_CHANGE_KINDS)
@pytest.mark.parametrize("cause", c.S3_CHANGE_CAUSES)
def test_change_kind_and_cause_vocabularies_are_not_filtered(kind: str, cause: str) -> None:
    # The typed contract owns enum admission.  Projection must preserve every
    # accepted kind/cause (resolved is lifecycle-derived, not section-derived).
    unit = _extra_d10(f"CHANGE-{kind}-{cause}", "high", kind, cause)
    packet = _packet_from_units((*b.build_synthetic_units(), unit))
    if kind == "resolved":
        with pytest.raises(p.S3ProjectionError) as excinfo:
            p.project_change_bands(packet)
        assert excinfo.value.error_code == "change_emission_mismatch"
        return
    bands = p.project_change_bands(packet)
    assert any(band.change_kind == kind for band in bands.change_bands)
    assert any(band.change_cause == cause for band in bands.change_bands)


def test_site_domain_and_classification_drift_fail_closed() -> None:
    packet = b.build_s3_authority_packet()
    cells = packet.audience_payload.center_map.cells
    object.__setattr__(packet.audience_payload.center_map, "cells",
                       tuple(dc_replace(cell, site_ref="S3-SITE-WRONG")
                             for cell in cells))
    result = p.validate_s3_projection(packet)
    assert result["valid"] is False
    assert result["reasons"]
