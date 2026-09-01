"""Typed construction of R5 base/flow records from the external fixture.

The fixture JSON (``tests/fixtures/medical_monitoring/
r5_authority_fixture.json``) stores source data only: per-request identity
fields (snapshot refs) and derived values (hashes, anchors, lineage) are
recomputed here exactly as before the B5 externalization.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Mapping, Optional

from .fixture_data import load_r5_fixture
from .product_types import (
    R5EventRecord,
    R5FlowStageRecord,
    R5HistoryRecord,
    R5RiskRecord,
    R5SiteRecord,
    R5SourceRecord,
    R5SubjectFlowPathRecord,
    R5SubjectFlowStep,
    R5SubjectRecord,
    R5VisitRecord,
    canonical_sha256,
)


def as_optional_date(value: Optional[str]) -> Optional[date]:
    return date.fromisoformat(value) if value is not None else None


def source_record(
    locator_ref: str,
    snapshot_ref: str,
    revision: str,
    excerpt: str,
    record_ref: str,
    canonical_location: str,
) -> R5SourceRecord:
    content_hash = canonical_sha256({"revision": revision, "locator_ref": locator_ref, "excerpt": excerpt})
    return R5SourceRecord(
        locator_ref=locator_ref,
        snapshot_ref=snapshot_ref,
        source_file_ref=f"s7-synthetic-source-file:{revision}",
        source_revision_ref=revision,
        source_revision_content_hash=content_hash,
        record_ref=record_ref,
        canonical_location=canonical_location,
        excerpt=excerpt,
        lineage=("本次数据版本", "来源文件", record_ref),
    )


def _source(entry: Mapping[str, Any], snapshot_ref: str) -> R5SourceRecord:
    return source_record(
        entry["locator_ref"],
        snapshot_ref,
        entry["revision"],
        entry["excerpt"],
        entry["record_ref"],
        entry["canonical_location"],
    )


def _risk(entry: Mapping[str, Any], snapshot_ref: str) -> R5RiskRecord:
    instance_ref = entry["risk_instance_ref"]
    return R5RiskRecord(
        risk_ref=entry["risk_key"],
        risk_instance_ref=instance_ref,
        risk_key=entry["risk_key"],
        site_ref=entry["site_ref"],
        subject_ref=entry["subject_ref"],
        spine_ref=entry["spine_ref"],
        domain=entry["domain"],
        severity=entry["severity"],
        risk_type_zh=entry["risk_type_zh"],
        date_state="exact",
        event_ref=entry["event_ref"],
        visit_ref=entry["visit_ref"],
        risk_anchor_ref=f"s7-anchor-{instance_ref.removeprefix('s7-risk-')}",
        source_locator_refs=(entry["source_locator_ref"],),
        change_kind=entry["change_kind"],
        change_cause=entry["change_cause"],
        prior_snapshot_ref=("s7-snapshot-prior-001" if snapshot_ref != "s7-snapshot-current-001" else None),
    )


def base_records_from_fixture(snapshot_ref: str) -> tuple:
    data = load_r5_fixture()
    subjects = tuple(R5SubjectRecord(**item) for item in data["subjects"])
    subject_refs = {item.subject_ref for item in subjects}
    sources = tuple(_source(item, snapshot_ref) for item in data["sources"])
    sites = tuple(
        R5SiteRecord(
            item["site_ref"], tuple(item["subject_refs"]), tuple(item["pattern_refs"]),
            tuple(item["individual_risk_refs"]), tuple(item["measure_refs"]),
            item["domain"], item["severity"], item["numerator"], item["denominator"],
            item["coverage_state"],
        )
        for item in data["sites"]
    )
    events = tuple(
        R5EventRecord(
            event_ref=item["event_ref"], subject_ref=item["subject_ref"],
            site_ref=item["site_ref"], spine_ref=item["spine_ref"], domain=item["domain"],
            subtype=item["subtype"], date_state=item["date_state"],
            start_date=as_optional_date(item["start_date"]),
            end_date=as_optional_date(item["end_date"]),
            visit_ref=item["visit_ref"], risk_anchor_refs=tuple(item["risk_anchor_refs"]),
            source_locator_refs=tuple(item["source_locator_refs"]), label_zh=item["label_zh"],
        )
        for item in data["events"]
        if item["subject_ref"] in subject_refs
    )
    visits = tuple(
        R5VisitRecord(
            item["visit_ref"], item["subject_ref"], item["site_ref"], item["spine_ref"],
            item["visit_kind"], item["date_state"], as_optional_date(item["actual_date"]),
            as_optional_date(item["nominal_date"]), item["phase_ref"],
            tuple(item["source_locator_refs"]),
        )
        for item in data["visits"]
    )
    risks = tuple(_risk(item, snapshot_ref) for item in data["risks"])
    histories = tuple(
        R5HistoryRecord(
            item["subject_ref"], item["candidate_ref"], item["later_fact_ref"],
            item["event_kind"], item["match_state"], item["from_snapshot_ref"],
            item["to_snapshot_ref"].format(snapshot_ref=snapshot_ref),
            tuple(item["identity_evidence_refs"]),
        )
        for item in data["histories"]
    )
    return sources, sites, subjects, events, visits, risks, histories


def flow_records_from_fixture() -> tuple[tuple[R5FlowStageRecord, ...], tuple[R5SubjectFlowPathRecord, ...]]:
    """Deterministic Slice-07B synthetic flow catalog and canonical paths."""

    data = load_r5_fixture()
    stages = tuple(
        R5FlowStageRecord(
            item["stage_ref"], item["stage_label_zh"], item["column_order"], item["row_order"],
            item["stage_kind"], item["is_entry"], item["is_terminal"], tuple(item["source_locator_refs"]),
        )
        for item in data["flow_stages"]
    )
    paths = tuple(
        R5SubjectFlowPathRecord(
            subject_ref=item["subject_ref"],
            site_ref=item["site_ref"],
            steps=tuple(
                R5SubjectFlowStep(
                    step["stage_ref"], as_optional_date(step["entered_date"]),
                    as_optional_date(step["basis_date"]), step["date_state"],
                    step["transition_reason_zh"], tuple(step["source_locator_refs"]),
                )
                for step in item["steps"]
            ),
            path_state=item["path_state"],
            stage_change_kind=item["stage_change_kind"],
            prior_run_current_stage_ref=item["prior_run_current_stage_ref"],
        )
        for item in data["flow_paths"]
    )
    return stages, paths
