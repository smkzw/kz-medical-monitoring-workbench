from __future__ import annotations

from datetime import date, timedelta

import pytest

from services.api.app.medical_monitoring_r5_product_adapter import (
    DOMAINS,
    PRODUCT_READ_SCHEMA,
    R5ProductAdapter,
    R5ProductAdapterError,
    build_synthetic_r5_authority_packet,
    build_synthetic_r5_authority_provider,
    response_snapshot_sha256,
)


PROJECT = "s7-synthetic-project-001"
RUN = "s7-run-current-001"
SNAPSHOT = "s7-snapshot-current-001"
CUTOFF = "2026-03-31"


@pytest.fixture()
def adapter() -> R5ProductAdapter:
    return R5ProductAdapter(
        build_synthetic_r5_authority_provider(), synthetic_fixture_mode=True
    )


def test_synthetic_packet_is_explicit_typed_and_identity_bound() -> None:
    packet = build_synthetic_r5_authority_packet()

    assert type(packet).__name__ == "R5AuthorityPacket"
    assert packet.synthetic is True
    assert packet.data_mode == "synthetic_offline"
    assert packet.project_ref == PROJECT
    assert packet.run_ref == RUN
    assert packet.snapshot_ref == SNAPSHOT
    assert len(packet.authority_hash) == 64
    assert len(packet.source_snapshot_sha256) == 64
    assert packet.authority_receipt()["projectable"] is True


def test_overview_projects_all_r5_identity_and_count_planes(adapter: R5ProductAdapter) -> None:
    result = adapter.overview(project_ref=PROJECT)
    projection = result["projection"]

    assert projection["kind"] == "project_cockpit"
    assert projection["content_hash"]
    assert set(result["counts"]) >= {
        "query",
        "clue",
        "center_pattern",
        "individual_risk",
        "affected_subject",
        "event",
        "affected_site",
        "project_signal",
    }
    assert len(projection["current_risk_set"]["high_risk_refs"]) >= 1
    assert len(projection["current_risk_set"]["medium_risk_refs"]) >= 1
    assert len(projection["center_map"]["cells"]) >= 2
    assert {item["domain"] for item in projection["domain_encoding"]} == set(DOMAINS)


def test_overview_shape_is_typed_and_authoritative_for_product_consumers(
    adapter: R5ProductAdapter,
) -> None:
    result = adapter.overview(project_ref=PROJECT)
    projection = result["projection"]
    counts = result["counts"]

    assert isinstance(projection["center_map"], dict)
    assert set(projection["center_map"]) == {
        "stable_site_order",
        "cells",
        "projection_instance",
        "content_hash",
    }
    assert isinstance(projection["center_map"]["cells"], list)
    assert projection["center_map"]["cells"]
    assert all(
        set(cell) == {
            "site_ref",
            "domain",
            "severity",
            "pattern_refs",
            "individual_risk_refs",
            "measure_refs",
        }
        for cell in projection["center_map"]["cells"]
    )
    assert projection["current_risks"]
    assert all(
        {
            "risk_ref",
            "risk_instance_ref",
            "risk_key",
            "risk_anchor_ref",
            "site_ref",
            "subject_ref",
            "spine_ref",
            "domain",
            "severity",
            "risk_type_zh",
            "source_locator_ref",
            "source_locator_refs",
            "change_kind",
        }.issubset(row)
        for row in projection["current_risks"]
    )
    assert counts["current_risk"] == {
        "critical": 0,
        "high": 2,
        "medium": 1,
        "low": 0,
        "total": 3,
    }
    assert counts["change_band_count"] == len(projection["change_bands"]) == 3
    assert projection["coverage"] == {
        "numerator": 3,
        "denominator": 20,
        "coverage_state": "partial",
        "label": "当前范围覆盖",
        "authority_receipt_ref": result["authority_receipt"]["receipt_id"],
    }
    assert len(projection["subjects"]) == 3


def test_source_evidence_is_a_narrow_surface_specific_projection(
    adapter: R5ProductAdapter,
) -> None:
    result = adapter.source_evidence(
        project_ref=PROJECT,
        run_ref=RUN,
        snapshot_ref=SNAPSHOT,
        cutoff_ref=CUTOFF,
        risk_instance_ref="s7-risk-pd-10008",
        source_locator_ref="s7-source-pd-10008",
    )
    projection = result["projection"]

    assert set(projection) == {
        "kind",
        "risk_ref",
        "risk_instance_ref",
        "source_locator_ref",
        "evidence",
        "authority_receipt_ref",
        "content_hash",
    }
    assert projection["kind"] == "source_evidence"
    assert "domain_encoding" not in projection
    assert "domain_tracks" not in projection
    assert "change_bands" not in projection
    assert "change_band_count" not in result["counts"]


def test_subject_projection_preserves_shared_spine_window_and_eight_domains(
    adapter: R5ProductAdapter,
) -> None:
    result = adapter.subject_workspace(
        project_ref=PROJECT,
        subject_ref="s7-subject-10008",
        run_ref=RUN,
        snapshot_ref=SNAPSHOT,
        cutoff_ref=CUTOFF,
        site_ref="s7-site-010",
        spine_ref="s7-spine-10008",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 3, 31),
        risk_instance_ref="s7-risk-pd-10008",
    )
    projection = result["projection"]

    assert projection["subject"]["spine_ref"] == "s7-spine-10008"
    assert projection["temporal_spine"]["spine_ref"] == "s7-spine-10008"
    assert projection["workspace_state"]["window_start"] == "2026-01-01"
    assert projection["workspace_state"]["window_end"] == "2026-03-31"
    assert {item["domain"] for item in projection["domain_tracks"]} == set(DOMAINS)
    assert any(item["date_state"] in {"partial", "conflicted"} for item in projection["events"])


def test_subject_projection_has_current_risks_spine_records_and_indicator_points(
    adapter: R5ProductAdapter,
) -> None:
    result = adapter.subject_workspace(
        project_ref=PROJECT,
        subject_ref="s7-subject-10008",
        run_ref=RUN,
        snapshot_ref=SNAPSHOT,
        cutoff_ref=CUTOFF,
        site_ref="s7-site-010",
        spine_ref="s7-spine-10008",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 3, 31),
    )
    projection = result["projection"]
    spine = projection["temporal_spine"]

    assert projection["current_risks"]
    assert [item["risk_instance_ref"] for item in projection["current_risks"]] == [
        item["risk_instance_ref"] for item in projection["risk_anchors"]
    ]
    assert spine["axis_mode"] == "calendar"
    assert spine["window_start"] == "2026-01-01"
    assert spine["window_end"] == "2026-03-31"
    assert spine["visits"] == projection["visits"]
    assert spine["events"] == projection["events"]
    assert spine["risk_anchors"] == projection["risk_anchors"]
    assert all({"item_ref", "event_ref", "domain", "date_state"}.issubset(item) for item in spine["pending_dates"])
    assert len(projection["indicators"]) == 2
    assert {item["value_kind"] for item in projection["indicators"]} == {"authority_record_count"}
    assert all(indicator["points"] for indicator in projection["indicators"])
    assert all(
        {"point_ref", "date", "date_state", "value", "record_refs", "source_locator_refs"}.issubset(point)
        for indicator in projection["indicators"]
        for point in indicator["points"]
    )
    assert result["counts"]["indicator"] == len(projection["indicators"])
    assert result["counts"]["current_risk"]["high"] == 1


def test_density_events_and_risks_share_exact_anchor_identity() -> None:
    packet = build_synthetic_r5_authority_packet(snapshot_ref="s7-snapshot-density-001")
    event_anchors = {
        anchor
        for event in packet.events
        for anchor in event.risk_anchor_refs
    }
    risk_anchors = {risk.risk_anchor_ref for risk in packet.risks}

    assert event_anchors == risk_anchors
    assert next(risk for risk in packet.risks if risk.risk_instance_ref == "s7-risk-density-001").risk_ref == "s7-risk-key-density-001"


def test_density_fixture_has_forty_continuous_actual_visit_dates(adapter: R5ProductAdapter) -> None:
    packet = build_synthetic_r5_authority_packet(snapshot_ref="s7-snapshot-density-001")
    visits = packet.visits

    assert len(visits) == 40
    assert all(item.visit_kind == "actual" and item.date_state == "exact" for item in visits)
    assert [item.actual_date for item in visits] == [
        date(2026, 1, 1) + timedelta(days=index) for index in range(40)
    ]
    visits_by_ref = {item.visit_ref: item for item in visits}
    assert all(item.start_date == visits_by_ref[item.visit_ref].actual_date for item in packet.events)

    projection = adapter.subject_workspace(
        project_ref=PROJECT,
        subject_ref="s7-subject-density-001",
        run_ref=RUN,
        snapshot_ref="s7-snapshot-density-001",
        cutoff_ref="2026-12-31",
        site_ref="s7-site-010",
        spine_ref="s7-spine-density-001",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 2, 9),
    )["projection"]
    assert [item["actual_date"] for item in projection["visits"]] == [
        (date(2026, 1, 1) + timedelta(days=index)).isoformat() for index in range(40)
    ]


def test_aemh_history_and_date_pending_records_are_projectable(adapter: R5ProductAdapter) -> None:
    aemh = adapter.subject_workspace(
        project_ref=PROJECT,
        subject_ref="s7-subject-06021",
        run_ref=RUN,
        snapshot_ref="s7-snapshot-aemh-001",
        cutoff_ref=CUTOFF,
        site_ref="s7-site-006",
        spine_ref="s7-spine-06021",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 3, 31),
    )
    date_edge = adapter.subject_workspace(
        project_ref=PROJECT,
        subject_ref="s7-subject-date-001",
        run_ref=RUN,
        snapshot_ref="s7-snapshot-date-edge-001",
        cutoff_ref=CUTOFF,
        site_ref="s7-site-010",
        spine_ref="s7-spine-date-001",
        window_start=date(2026, 1, 1),
        window_end=date(2026, 3, 31),
    )

    assert aemh["projection"]["aemh_match_history"][0]["later_fact_ref"]
    assert date_edge["projection"]["date_pending_refs"] == [
        "s7-event-date-partial",
        "s7-event-date-conflicted",
        "s7-event-date-missing",
    ]
    assert {
        item["date_state"] for item in date_edge["projection"]["events"]
    } == {"exact", "partial", "conflicted", "missing"}
    assert next(
        item for item in date_edge["projection"]["events"]
        if item["date_state"] == "missing"
    )["start_date"] is None


def test_source_evidence_requires_exact_bound_locator(adapter: R5ProductAdapter) -> None:
    result = adapter.source_evidence(
        project_ref=PROJECT,
        run_ref=RUN,
        snapshot_ref=SNAPSHOT,
        cutoff_ref=CUTOFF,
        risk_instance_ref="s7-risk-pd-10008",
        source_locator_ref="s7-source-pd-10008",
    )

    assert result["projection"]["kind"] == "source_evidence"
    evidence = result["projection"]["evidence"]
    assert all(evidence[field] for field in ("record_ref", "canonical_location", "excerpt"))
    assert evidence["record_ref"] == "方案执行 Data Listing 第 10008 行"
    assert evidence["canonical_location"] == "方案执行 Data Listing · 第 10008 行 · 访视日期单元格"
    assert len(result["source_refs"]) == 1
    source = result["source_refs"][0]
    assert all(source[field] == evidence[field] for field in ("record_ref", "canonical_location", "excerpt"))
    with pytest.raises(R5ProductAdapterError, match="SOURCE_LOCATOR_NOT_BOUND"):
        adapter.source_evidence(
            project_ref=PROJECT,
            run_ref=RUN,
            snapshot_ref=SNAPSHOT,
            cutoff_ref=CUTOFF,
            risk_instance_ref="s7-risk-pd-10008",
            source_locator_ref="s7-source-ae-06021",
        )


def test_unknown_identity_and_mapping_provider_fail_closed(adapter: R5ProductAdapter) -> None:
    with pytest.raises(R5ProductAdapterError, match="PROJECT_NOT_IN_SYNTHETIC_PACKET"):
        adapter.overview(project_ref="s7-synthetic-project-other")
    with pytest.raises(R5ProductAdapterError, match="TYPED_AUTHORITY_REQUIRED"):
        R5ProductAdapter(lambda *_args: {"project_ref": PROJECT}) .overview(project_ref=PROJECT)


def test_response_digest_is_deterministic_and_excludes_self_reference(
    adapter: R5ProductAdapter,
) -> None:
    result = adapter.overview(project_ref=PROJECT)
    response = {
        "schema": PRODUCT_READ_SCHEMA,
        "identity": {
            "project_ref": PROJECT,
            "response_snapshot_sha256": "",
        },
        "projection": result["projection"],
        "read_handoff": {
            "response_snapshot_sha256": "",
            "contract_sha256": "a" * 64,
        },
        "response_snapshot_sha256": "",
    }
    digest = response_snapshot_sha256(response)
    response["response_snapshot_sha256"] = digest
    response["identity"]["response_snapshot_sha256"] = digest
    response["read_handoff"]["response_snapshot_sha256"] = digest
    assert response_snapshot_sha256(response) == digest
