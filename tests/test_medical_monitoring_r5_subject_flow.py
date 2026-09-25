"""Deterministic Slice-07B subject-flow contract tests (v0.2 + v0.3 §9).

Offline only: synthetic packets, stub providers, no server, no browser.
Covers the frozen blocking cases: three states, conservation, center scope,
edge legality, Journey jump windows and legacy hash compatibility.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.api.app.medical_monitoring_r5_product_adapter import (
    R5_FLOW_AUTHORITY_CONTRACT_VERSION,
    R5AuthorityPacket,
    R5FlowStageRecord,
    R5ProductAdapter,
    R5ProductAdapterError,
    R5RiskRecord,
    R5SiteRecord,
    R5SourceRecord,
    R5SourceRevisionPair,
    R5SubjectFlowPathRecord,
    R5SubjectFlowStep,
    R5SubjectRecord,
    R5VisitRecord,
    build_synthetic_r5_authority_packet,
    build_synthetic_r5_authority_provider,
    canonical_sha256,
    response_snapshot_sha256,
)
from services.api.app.medical_monitoring_r5_product_router import (
    R5_PRODUCT_PREFIX,
    create_medical_monitoring_r5_product_router,
)
from services.api.app.monitoring_runtime_principal import (
    MonitoringAuthenticatedPrincipal,
)


SYNTHETIC_PROJECT = "s7-synthetic-project-001"
SYNTHETIC_CUTOFF = "2026-03-31"
# Authority hash of the pre-Slice-07B legacy v0.3.1 base packet. Empty flow
# fields must never enter the hash payload, so a legacy-shaped packet built
# today must reproduce this exact digest.
# 0925重钉：fb8fd4a（WP2切片1）把severity_source三分写入synthetic fixture
# 载荷时未同步本钉值；二分确认7b23297过/fb8fd4a起挂，属有意的schema演进，
# 按新载荷重钉（本测试继续守护未来意外漂移）。
FLOW_LEGACY_AUTHORITY_HASH = "4a5e7d2477cb3e7fdc1c6a4558c5b30f65cad916f35484c2a4e5d9cee1717c41"

PROJECT = "flow-test-project-001"
RUN = "flow-test-run-001"
SNAPSHOT = "flow-snapshot-001"
CUTOFF = "2026-03-31"
SOURCE_REF = "flow-source-001"


def _adapter_for(packet: R5AuthorityPacket) -> R5ProductAdapter:
    return R5ProductAdapter(lambda *_args: packet)


def _stage(
    ref: str,
    label: str,
    column: int,
    row: int,
    kind: str = "main",
    *,
    entry: bool = False,
    terminal: bool = False,
) -> R5FlowStageRecord:
    return R5FlowStageRecord(ref, label, column, row, kind, entry, terminal, (SOURCE_REF,))


def _step(
    ref: str,
    entered: date | None = None,
    *,
    basis: date | None = None,
    state: str = "exact",
    reason: str = "进入下一阶段",
) -> R5SubjectFlowStep:
    return R5SubjectFlowStep(ref, entered, basis, state, reason, (SOURCE_REF,))


def _path(
    subject_ref: str,
    site_ref: str,
    steps: tuple[R5SubjectFlowStep, ...],
    *,
    state: str = "complete",
    change: str = "initial",
    prior: str | None = None,
) -> R5SubjectFlowPathRecord:
    return R5SubjectFlowPathRecord(subject_ref, site_ref, steps, state, change, prior)


def _source() -> R5SourceRecord:
    return R5SourceRecord(
        locator_ref=SOURCE_REF,
        snapshot_ref=SNAPSHOT,
        source_file_ref="flow-source-file-001",
        source_revision_ref="flow-rev-001",
        source_revision_content_hash=canonical_sha256({"revision": "flow-rev-001"}),
        record_ref="流向合成验证记录",
        canonical_location="流向合成验证来源",
        excerpt="受试者阶段流向合成定位片段。",
    )


def _packet(
    *,
    subjects: tuple[R5SubjectRecord, ...],
    sites: tuple[R5SiteRecord, ...],
    stages: tuple[R5FlowStageRecord, ...],
    paths: tuple[R5SubjectFlowPathRecord, ...],
    risks: tuple[R5RiskRecord, ...] = (),
    visits: tuple[R5VisitRecord, ...] = (),
) -> R5AuthorityPacket:
    source = _source()
    if not risks and subjects:
        first = subjects[0]
        risks = (_risk(first.subject_ref, first.site_ref, first.spine_ref, severity="low"),)
    return R5AuthorityPacket(
        project_ref=PROJECT,
        run_ref=RUN,
        snapshot_ref=SNAPSHOT,
        cutoff_state="present",
        cutoff_ref=CUTOFF,
        project_label="流向合成项目",
        authority_contract_id="r5-authority-receipt-kind-v1",
        authority_contract_version=R5_FLOW_AUTHORITY_CONTRACT_VERSION,
        audience_contract_id="medical-monitoring-r5-exact-contract-v0.3.1",
        visibility_decision_id="flow-visibility-001",
        visibility_decision_hash=canonical_sha256({"visibility": "flow-001"}),
        evaluation_content_identities=(canonical_sha256({"identity": "flow-001"}),),
        source_revision_content_pairs=(
            R5SourceRevisionPair("flow-rev-001", source.source_revision_content_hash, (SOURCE_REF,)),
        ),
        sources=(source,),
        sites=sites,
        subjects=subjects,
        events=(),
        visits=visits,
        risks=risks,
        histories=(),
        flow_stages=stages,
        subject_flow_paths=paths,
    )


def _risk(subject_ref: str, site_ref: str, spine_ref: str, *, severity: str = "high") -> R5RiskRecord:
    return R5RiskRecord(
        risk_ref=f"flow-risk-key-{subject_ref}",
        risk_instance_ref=f"flow-risk-{subject_ref}",
        risk_key=f"flow-risk-key-{subject_ref}",
        site_ref=site_ref,
        subject_ref=subject_ref,
        spine_ref=spine_ref,
        domain="ae",
        severity=severity,
        risk_type_zh="测试风险",
        date_state="exact",
        event_ref=None,
        visit_ref=None,
        risk_anchor_ref=f"flow-anchor-{subject_ref}",
        source_locator_refs=(SOURCE_REF,),
    )


def _twelve_catalog() -> tuple[R5FlowStageRecord, ...]:
    return (
        _stage("flow-stage-consent", "已签署知情同意", 0, 0, "main", entry=True),
        _stage("flow-stage-screening", "筛选", 1, 0),
        _stage("flow-stage-screen-fail", "筛选失败", 1, 1, "branch_terminal", terminal=True),
        _stage("flow-stage-treatment", "治疗中", 2, 0),
        _stage("flow-stage-completed", "完成研究", 2, 1, "branch_terminal", terminal=True),
        _stage("flow-stage-stopped", "永久停药", 3, 0, "branch_terminal", terminal=True),
    )


_TWELVE_CURRENT = {
    "flow-subject-01": "flow-stage-screen-fail",
    "flow-subject-02": "flow-stage-treatment",
    "flow-subject-03": "flow-stage-treatment",
    "flow-subject-04": "flow-stage-treatment",
    "flow-subject-05": "flow-stage-completed",
    "flow-subject-06": "flow-stage-stopped",
    "flow-subject-07": "flow-stage-screen-fail",
    "flow-subject-08": "flow-stage-treatment",
    "flow-subject-09": "flow-stage-treatment",
    "flow-subject-10": "flow-stage-completed",
    "flow-subject-11": "flow-stage-completed",
    "flow-subject-12": "flow-stage-stopped",
}


def _twelve_subjects() -> tuple[R5SubjectRecord, ...]:
    return tuple(
        R5SubjectRecord(f"flow-subject-{index:02d}", site, f"flow-spine-{index:02d}", f"受试者 {index:02d}")
        for index, site in [(item, "flow-site-a" if item <= 6 else "flow-site-b") for item in range(1, 13)]
    )


def _twelve_sites() -> tuple[R5SiteRecord, ...]:
    return (
        R5SiteRecord(
            "flow-site-a",
            tuple(f"flow-subject-{index:02d}" for index in range(1, 7)),
            ("flow-pattern-a",), (), ("flow-measure-a",), "ae", "high", 6, 6, "complete",
        ),
        R5SiteRecord(
            "flow-site-b",
            tuple(f"flow-subject-{index:02d}" for index in range(7, 13)),
            ("flow-pattern-b",), (), ("flow-measure-b",), "ae", "high", 6, 6, "complete",
        ),
    )


def _twelve_paths() -> tuple[R5SubjectFlowPathRecord, ...]:
    paths = []
    for index in range(1, 13):
        subject_ref = f"flow-subject-{index:02d}"
        site_ref = "flow-site-a" if index <= 6 else "flow-site-b"
        steps = [
            _step("flow-stage-consent", date(2026, 1, 6)),
            _step("flow-stage-screening", date(2026, 1, 15)),
        ]
        tail = _TWELVE_CURRENT[subject_ref]
        if tail == "flow-stage-screen-fail":
            steps.append(_step(tail, date(2026, 1, 22)))
        else:
            steps.append(_step("flow-stage-treatment", date(2026, 2, 1)))
            if tail == "flow-stage-completed":
                steps.append(_step(tail, date(2026, 3, 1)))
            elif tail == "flow-stage-stopped":
                steps.append(_step(tail, date(2026, 3, 5)))
        paths.append(_path(subject_ref, site_ref, tuple(steps)))
    return tuple(paths)


def _twelve_packet() -> R5AuthorityPacket:
    subjects = _twelve_subjects()
    risks = (
        _risk("flow-subject-01", "flow-site-a", "flow-spine-01"),
        _risk("flow-subject-02", "flow-site-a", "flow-spine-02"),
        _risk("flow-subject-08", "flow-site-b", "flow-spine-08"),
        _risk("flow-subject-05", "flow-site-a", "flow-spine-05", severity="low"),
    )
    return _packet(
        subjects=subjects,
        sites=_twelve_sites(),
        stages=_twelve_catalog(),
        paths=_twelve_paths(),
        risks=risks,
    )


def _stage_by_ref(flow: dict, ref: str) -> dict:
    return next(item for item in flow["stages"] if item["stage_ref"] == ref)


def _link_by_ref(flow: dict, ref: str) -> dict:
    return next(item for item in flow["links"] if item["link_ref"] == ref)


def _blocked_gaps(packet: R5AuthorityPacket) -> list[str]:
    flow = _adapter_for(packet).overview(project_ref=PROJECT)["projection"]["subject_flow"]
    assert flow["availability"] == "available"
    reconciliation = flow["reconciliation"]
    assert reconciliation["state"] == "blocked"
    assert reconciliation["gaps_zh"]
    assert "stages" not in flow and "links" not in flow and "subjects" not in flow
    return reconciliation["gaps_zh"]


# ---------------------------------------------------------------------------
# Synthetic fixture projection: matched state, conservation, risk intersection
# ---------------------------------------------------------------------------


def test_synthetic_flow_projection_is_matched_and_conserved() -> None:
    adapter = R5ProductAdapter(build_synthetic_r5_authority_provider(), synthetic_fixture_mode=True)
    flow = adapter.overview(project_ref=SYNTHETIC_PROJECT)["projection"]["subject_flow"]

    assert flow["availability"] == "available"
    assert flow["visual_kind"] == "path_throughput_sankey"
    assert flow["scope"]["project_ref"] == SYNTHETIC_PROJECT
    assert flow["scope"]["site_ref"] is None
    assert flow["scope"]["cutoff_ref"] == SYNTHETIC_CUTOFF

    counts = {
        item["stage_ref"]: (item["reached_count"], item["current_count"], item["current_mid_high_risk_count"])
        for item in flow["stages"]
    }
    assert counts["s7-flow-stage-consent"] == (2, 0, 0)
    assert counts["s7-flow-stage-missing"] == (1, 0, 0)
    assert counts["s7-flow-stage-screening"] == (3, 0, 0)
    assert counts["s7-flow-stage-screen-fail"] == (1, 1, 1)
    assert counts["s7-flow-stage-treatment"] == (2, 1, 1)
    assert counts["s7-flow-stage-completed"] == (1, 1, 0)
    assert counts["s7-flow-stage-stopped"] == (0, 0, 0)

    links = {item["link_ref"]: (item["count"], item["current_mid_high_risk_count"]) for item in flow["links"]}
    assert links["r5-flow-link:s7-flow-stage-consent:s7-flow-stage-screening"] == (2, 2)
    assert links["r5-flow-link:s7-flow-stage-missing:s7-flow-stage-screening"] == (1, 0)
    assert links["r5-flow-link:s7-flow-stage-screening:s7-flow-stage-screen-fail"] == (1, 1)
    assert links["r5-flow-link:s7-flow-stage-screening:s7-flow-stage-treatment"] == (2, 1)
    assert links["r5-flow-link:s7-flow-stage-treatment:s7-flow-stage-completed"] == (1, 0)

    assert flow["coverage"] == {
        "total_subjects": 3,
        "complete_count": 2,
        "partial_count": 1,
        "conflicted_count": 0,
        "not_provided_count": 0,
        "not_applicable_count": 0,
    }
    assert flow["reconciliation"] == {
        "state": "matched",
        "total_subject_count": 3,
        "entry_count": 3,
        "current_stay_count": 3,
        "detail_count": 3,
        "node_conservation_matched": True,
        "link_conservation_matched": True,
        "membership_ok": True,
        "continuity_ok": True,
        "gaps_zh": [],
    }
    assert len({item["column_order"] for item in flow["stages"]}) <= 6


def test_flow_node_and_link_conservation_recomputed_from_projection_rows() -> None:
    flow = _adapter_for(_twelve_packet()).overview(project_ref=PROJECT)["projection"]["subject_flow"]
    row_refs_by_stage: dict[str, set[str]] = {}
    row_refs_by_link: dict[str, set[str]] = {}
    for row in flow["subjects"]:
        for ref in row["path_stage_refs"]:
            row_refs_by_stage.setdefault(ref, set()).add(row["subject_ref"])
        for ref in row["path_link_refs"]:
            row_refs_by_link.setdefault(ref, set()).add(row["subject_ref"])

    for stage in flow["stages"]:
        assert stage["reached_count"] == len(row_refs_by_stage.get(stage["stage_ref"], set()))
        assert stage["current_count"] == sum(
            1 for row in flow["subjects"] if row["current_stage_ref"] == stage["stage_ref"]
        )
    for link in flow["links"]:
        assert link["count"] == len(row_refs_by_link.get(link["link_ref"], set()))


def test_selection_sets_reconcile_exactly_with_detail_rows() -> None:
    flow = _adapter_for(_twelve_packet()).overview(project_ref=PROJECT)["projection"]["subject_flow"]

    current_treatment = [row["subject_ref"] for row in flow["subjects"] if row["current_stage_ref"] == "flow-stage-treatment"]
    assert len(current_treatment) == _stage_by_ref(flow, "flow-stage-treatment")["current_count"] == 5

    reached_screening = [row["subject_ref"] for row in flow["subjects"] if "flow-stage-screening" in row["path_stage_refs"]]
    assert len(reached_screening) == _stage_by_ref(flow, "flow-stage-screening")["reached_count"] == 12

    link_ref = "r5-flow-link:flow-stage-screening:flow-stage-treatment"
    link_rows = [row["subject_ref"] for row in flow["subjects"] if link_ref in row["path_link_refs"]]
    assert len(link_rows) == _link_by_ref(flow, link_ref)["count"] == 10

    mid_high = [row["subject_ref"] for row in flow["subjects"] if row["current_mid_high_risk"]]
    assert sorted(mid_high) == ["flow-subject-01", "flow-subject-02", "flow-subject-08"]
    assert len([ref for ref in mid_high if ref in set(current_treatment)]) == (
        _stage_by_ref(flow, "flow-stage-treatment")["current_mid_high_risk_count"]
    ) == 2
    assert len([ref for ref in mid_high if ref in set(link_rows)]) == (
        _link_by_ref(flow, link_ref)["current_mid_high_risk_count"]
    ) == 2


def test_twelve_subject_example_conserves_entry_current_and_outflow() -> None:
    flow = _adapter_for(_twelve_packet()).overview(project_ref=PROJECT)["projection"]["subject_flow"]
    reconciliation = flow["reconciliation"]

    assert reconciliation["state"] == "matched"
    assert reconciliation["total_subject_count"] == reconciliation["entry_count"] == 12
    assert reconciliation["current_stay_count"] == sum(
        item["current_count"] for item in flow["stages"]
    ) == 12
    assert reconciliation["detail_count"] == len(flow["subjects"]) == 12
    by_stage = {item["stage_ref"]: item for item in flow["stages"]}
    assert by_stage["flow-stage-screen-fail"]["current_count"] == 2
    assert by_stage["flow-stage-treatment"]["current_count"] == 5
    assert by_stage["flow-stage-completed"]["current_count"] == 3
    assert by_stage["flow-stage-stopped"]["current_count"] == 2
    outbound = {item["stage_ref"]: 0 for item in flow["stages"]}
    inbound = {item["stage_ref"]: 0 for item in flow["stages"]}
    for link in flow["links"]:
        outbound[link["from_stage_ref"]] += link["count"]
        inbound[link["to_stage_ref"]] += link["count"]
    for stage in flow["stages"]:
        ref = stage["stage_ref"]
        assert stage["reached_count"] == stage["current_count"] + outbound[ref]
        if stage["is_entry"]:
            assert inbound[ref] == 0
        else:
            assert inbound[ref] == stage["reached_count"]

    assert flow["coverage"]["complete_count"] == 12
    assert flow["coverage"]["total_subjects"] == sum(
        value for key, value in flow["coverage"].items() if key.endswith("_count")
    )


def test_center_scopes_partition_the_project_set_without_overlap() -> None:
    adapter = _adapter_for(_twelve_packet())
    project_rows = adapter.overview(project_ref=PROJECT)["projection"]["subject_flow"]["subjects"]
    site_a = adapter.overview(project_ref=PROJECT, site_ref="flow-site-a")["projection"]["subject_flow"]
    site_b = adapter.overview(project_ref=PROJECT, site_ref="flow-site-b")["projection"]["subject_flow"]

    assert [row["subject_ref"] for row in site_a["subjects"]] == [
        f"flow-subject-{index:02d}" for index in range(1, 7)
    ]
    assert all(row["site_ref"] == "flow-site-a" for row in site_a["subjects"])
    refs_a = {row["subject_ref"] for row in site_a["subjects"]}
    refs_b = {row["subject_ref"] for row in site_b["subjects"]}
    assert refs_a.isdisjoint(refs_b)
    assert refs_a | refs_b == {row["subject_ref"] for row in project_rows}
    assert site_a["reconciliation"]["state"] == site_b["reconciliation"]["state"] == "matched"
    assert site_a["reconciliation"]["total_subject_count"] == 6


# ---------------------------------------------------------------------------
# Three states: not_provided / blocked / matched empty range
# ---------------------------------------------------------------------------


def test_legacy_packet_without_flow_fields_is_not_provided_with_pinned_hash() -> None:
    packet = replace(
        build_synthetic_r5_authority_packet(),
        flow_stages=(),
        subject_flow_paths=(),
        authority_hash="",
        source_snapshot_sha256="",
        authority_contract_version="2026-08-26.1",
    )
    assert packet.authority_hash == FLOW_LEGACY_AUTHORITY_HASH

    flow = _adapter_for(packet).overview(project_ref=SYNTHETIC_PROJECT)["projection"]["subject_flow"]
    assert flow["availability"] == "not_provided"
    assert flow["reason_zh"] == "本次数据未提供研究状态"
    assert flow["reconciliation"] == {"state": "not_applicable"}
    assert "stages" not in flow and "links" not in flow and "subjects" not in flow
    assert "coverage" not in flow


def test_density_snapshot_overview_stays_not_provided() -> None:
    adapter = R5ProductAdapter(build_synthetic_r5_authority_provider(), synthetic_fixture_mode=True)
    flow = adapter.overview(
        project_ref=SYNTHETIC_PROJECT,
        snapshot_ref="s7-snapshot-density-001",
        cutoff_ref="2026-12-31",
    )["projection"]["subject_flow"]
    assert flow["availability"] == "not_provided"
    assert "0 人" not in flow["reason_zh"]
    assert "stages" not in flow


def test_empty_center_range_is_matched_with_zero_subjects() -> None:
    adapter = R5ProductAdapter(build_synthetic_r5_authority_provider(), synthetic_fixture_mode=True)
    flow = adapter.overview(
        project_ref=SYNTHETIC_PROJECT,
        site_ref="s7-site-small-001",
    )["projection"]["subject_flow"]

    assert flow["availability"] == "available"
    assert flow["reconciliation"]["state"] == "matched"
    assert flow["reconciliation"]["total_subject_count"] == 0
    assert flow["coverage"]["total_subjects"] == 0
    assert flow["subjects"] == []
    assert flow["links"] == []
    assert all(item["reached_count"] == 0 and item["current_count"] == 0 for item in flow["stages"])


@pytest.mark.parametrize(
    "mutate, expected_gap",
    [
        pytest.param(
            lambda data: {**data, "stages": ()},
            "路径数据缺少阶段目录",
            id="paths_without_stages",
        ),
        pytest.param(
            lambda data: {**data, "paths": ()},
            "受试者缺少规范路径记录",
            id="stages_without_paths",
        ),
        pytest.param(
            lambda data: {
                **data,
                "paths": data["paths"]
                + (_path("flow-subject-ghost", "flow-site-a", (_step("flow-stage-consent", date(2026, 1, 6)), _step("flow-stage-screening", date(2026, 1, 15)))),),
            },
            "规范路径引用了范围外的受试者",
            id="orphan_path_subject",
        ),
        pytest.param(
            lambda data: {**data, "paths": data["paths"] + data["paths"][:1]},
            "同一受试者存在多条规范路径",
            id="duplicate_path_per_subject",
        ),
        pytest.param(
            lambda data: {
                **data,
                "paths": (_path(data["paths"][0].subject_ref, "flow-site-b", data["paths"][0].steps),)
                + data["paths"][1:],
            },
            "路径与受试者中心归属不一致",
            id="site_membership_mismatch",
        ),
        pytest.param(
            lambda data: {
                **data,
                "paths": tuple(
                    _path(path.subject_ref, path.site_ref, (_step("flow-stage-ghost", date(2026, 1, 6)),) + path.steps[1:])
                    if index == 0
                    else path
                    for index, path in enumerate(data["paths"])
                ),
            },
            "规范路径引用了未定义的阶段",
            id="unknown_stage_reference",
        ),
        pytest.param(
            lambda data: {**data, "paths": data["paths"][:-1]},
            "受试者缺少规范路径记录",
            id="missing_path_member",
        ),
        pytest.param(
            lambda data: {
                **data,
                "paths": (
                    _path(data["paths"][0].subject_ref, data["paths"][0].site_ref, (
                        _step("flow-stage-consent", date(2026, 1, 6)),
                        _step("flow-stage-screening", date(2026, 1, 15)),
                        _step("flow-stage-screening", date(2026, 1, 16)),
                    )),
                )
                + data["paths"][1:],
            },
            "规范路径中阶段重复",
            id="repeated_stage_in_path",
        ),
        pytest.param(
            lambda data: {
                **data,
                "paths": (_path("flow-subject-01", "flow-site-a", (
                    _step("flow-stage-screening", date(2026, 1, 15)),
                    _step("flow-stage-treatment", date(2026, 2, 1)),
                )),)
                + data["paths"][1:],
            },
            "规范路径入口不合法",
            id="path_does_not_start_at_entry",
        ),
        pytest.param(
            lambda data: {
                **data,
                "paths": (_path("flow-subject-01", "flow-site-a", (
                    _step("flow-stage-consent", date(2026, 1, 6)),
                    _step("flow-stage-treatment", date(2026, 2, 1)),
                )),)
                + data["paths"][1:],
            },
            "规范路径阶段连续性校验未通过",
            id="main_chain_column_skip",
        ),
        pytest.param(
            lambda data: {
                **data,
                "paths": (_path("flow-subject-01", "flow-site-a", (
                    _step("flow-stage-consent", date(2026, 1, 6)),
                    _step("flow-stage-treatment", date(2026, 2, 1)),
                    _step("flow-stage-screening", date(2026, 2, 2)),
                )),)
                + data["paths"][1:],
            },
            "规范路径阶段连续性校验未通过",
            id="main_chain_column_regression",
        ),
        pytest.param(
            lambda data: {
                **data,
                "stages": data["stages"]
                + (
                    _stage("flow-stage-extra-1", "扩展阶段一", 4, 0),
                    _stage("flow-stage-extra-2", "扩展阶段二", 5, 0),
                    _stage("flow-stage-extra-3", "扩展阶段三", 6, 0),
                ),
            },
            "受试者阶段列数超过当前看板容量",
            id="more_than_six_columns",
        ),
        pytest.param(
            lambda data: {
                **data,
                "stages": data["stages"]
                + (_stage("flow-stage-mid-entry", "中途入口", 4, 0, "main", entry=True),),
                "paths": (_path("flow-subject-01", "flow-site-a", (
                    _step("flow-stage-consent", date(2026, 1, 6)),
                    _step("flow-stage-mid-entry", date(2026, 2, 1)),
                )),)
                + data["paths"][1:],
            },
            "规范路径入口不合法",
            id="entry_stage_draws_inbound_edge",
        ),
    ],
)
def test_blocked_conditions_are_distinct_from_not_provided(mutate, expected_gap: str) -> None:
    packet = _twelve_packet()
    mutated = mutate({"subjects": packet.subjects, "sites": packet.sites, "stages": packet.flow_stages, "paths": packet.subject_flow_paths, "risks": packet.risks})
    rebuilt = _packet(**mutated)
    gaps = _blocked_gaps(rebuilt)
    assert expected_gap in gaps


def test_mid_chain_gap_enters_unknown_path_without_fake_cross_column_link() -> None:
    stages = _twelve_catalog() + (
        _stage("flow-stage-unknown", "状态待核实", 0, 2, "unknown", entry=True, terminal=True),
    )
    subjects = (
        R5SubjectRecord("flow-subject-ok", "flow-site-a", "flow-spine-ok", "受试者 OK"),
        R5SubjectRecord("flow-subject-conflict", "flow-site-a", "flow-spine-conflict", "受试者 CONFLICT"),
    )
    sites = (
        R5SiteRecord(
            "flow-site-a",
            ("flow-subject-ok", "flow-subject-conflict"),
            ("flow-pattern-a",), (), ("flow-measure-a",), "ae", "high", 2, 2, "complete",
        ),
    )
    paths = (
        _path("flow-subject-ok", "flow-site-a", (
            _step("flow-stage-consent", date(2026, 1, 6)),
            _step("flow-stage-screening", date(2026, 1, 15)),
            _step("flow-stage-treatment", date(2026, 2, 1)),
        )),
        _path(
            "flow-subject-conflict",
            "flow-site-a",
            (_step("flow-stage-unknown", None, state="conflicted", reason="现有数据相互冲突"),),
            state="conflicted",
            change="not_comparable",
        ),
    )
    flow = _adapter_for(_packet(subjects=subjects, sites=sites, stages=stages, paths=paths)).overview(
        project_ref=PROJECT
    )["projection"]["subject_flow"]

    assert flow["reconciliation"]["state"] == "matched"
    assert flow["coverage"] == {
        "total_subjects": 2,
        "complete_count": 1,
        "partial_count": 0,
        "conflicted_count": 1,
        "not_provided_count": 0,
        "not_applicable_count": 0,
    }
    conflict_row = next(row for row in flow["subjects"] if row["subject_ref"] == "flow-subject-conflict")
    assert conflict_row["current_stage_ref"] == "flow-stage-unknown"
    assert conflict_row["path_link_refs"] == []
    assert all("flow-subject-conflict" not in row["path_stage_refs"] for row in flow["subjects"] if row["subject_ref"] != "flow-subject-conflict")
    assert not any("consent" in link["link_ref"] and "treatment" in link["link_ref"] for link in flow["links"])


def test_single_step_missing_and_not_applicable_paths_keep_distinct_buckets() -> None:
    stages = _twelve_catalog() + (
        _stage("flow-stage-missing", "既往阶段数据未提供", 0, 1, "missing", entry=True),
        _stage("flow-stage-na", "本研究不适用", 0, 3, "not_applicable", entry=True, terminal=True),
    )
    subjects = (
        R5SubjectRecord("flow-subject-missing", "flow-site-a", "flow-spine-missing", "受试者 MISSING"),
        R5SubjectRecord("flow-subject-na", "flow-site-a", "flow-spine-na", "受试者 NA"),
    )
    sites = (
        R5SiteRecord(
            "flow-site-a",
            ("flow-subject-missing", "flow-subject-na"),
            ("flow-pattern-a",), (), ("flow-measure-a",), "ae", "high", 2, 2, "complete",
        ),
    )
    paths = (
        _path(
            "flow-subject-missing",
            "flow-site-a",
            (_step("flow-stage-missing", None, state="missing", reason="当前状态已知，既往阶段数据未提供"),),
        ),
        _path(
            "flow-subject-na",
            "flow-site-a",
            (_step("flow-stage-na", None, state="missing", reason="本研究不适用"),),
        ),
    )
    flow = _adapter_for(_packet(subjects=subjects, sites=sites, stages=stages, paths=paths)).overview(
        project_ref=PROJECT
    )["projection"]["subject_flow"]

    assert flow["reconciliation"]["state"] == "matched"
    buckets = {row["subject_ref"]: row["coverage_bucket"] for row in flow["subjects"]}
    assert buckets == {
        "flow-subject-missing": "not_provided",
        "flow-subject-na": "not_applicable",
    }
    assert flow["coverage"] == {
        "total_subjects": 2,
        "complete_count": 0,
        "partial_count": 0,
        "conflicted_count": 0,
        "not_provided_count": 1,
        "not_applicable_count": 1,
    }


# ---------------------------------------------------------------------------
# Journey jump windows (v0.3 §5 / §9.4)
# ---------------------------------------------------------------------------


def test_fixture_rows_carry_cutoff_constrained_journey_windows() -> None:
    adapter = R5ProductAdapter(build_synthetic_r5_authority_provider(), synthetic_fixture_mode=True)
    rows = {
        row["subject_ref"]: row
        for row in adapter.overview(project_ref=SYNTHETIC_PROJECT)["projection"]["subject_flow"]["subjects"]
    }
    assert rows["s7-subject-10008"]["jump_window_start"] == "2026-01-15"
    assert rows["s7-subject-10008"]["jump_window_end"] == "2026-03-15"
    assert rows["s7-subject-06021"]["jump_window_start"] == "2026-01-31"
    assert rows["s7-subject-06021"]["jump_window_end"] == "2026-03-02"
    # The window comes from visits/events (min 2026-01-10), never from path
    # step dates (min would be 2026-02-01 for this partial path).
    assert rows["s7-subject-date-001"]["jump_window_start"] == "2026-01-10"
    assert rows["s7-subject-date-001"]["jump_window_end"] == "2026-02-20"
    assert all(row["journey_jump_enabled"] and row["journey_jump_state_zh"] == "可跳转" for row in rows.values())


def test_rows_without_usable_dates_stay_visible_with_disabled_jump() -> None:
    flow = _adapter_for(_twelve_packet()).overview(project_ref=PROJECT)["projection"]["subject_flow"]
    assert flow["subjects"]
    for row in flow["subjects"]:
        assert row["journey_jump_enabled"] is False
        assert row["journey_jump_state_zh"] == "时间窗待确认"
        assert row["jump_window_start"] is None and row["jump_window_end"] is None
        # Path steps carry exact dates, but path dates never substitute for a
        # visits/events window (v0.3 §9.4).
        assert row["entered_date"] is not None


def test_jump_window_is_clipped_to_current_cutoff() -> None:
    subjects = (R5SubjectRecord("flow-subject-window", "flow-site-a", "flow-spine-window", "受试者 WINDOW"),)
    sites = (
        R5SiteRecord("flow-site-a", ("flow-subject-window",), ("flow-pattern-a",), (), ("flow-measure-a",), "ae", "high", 1, 1, "complete"),
    )
    visits = (
        R5VisitRecord("flow-visit-1", "flow-subject-window", "flow-site-a", "flow-spine-window", "actual", "exact", date(2026, 2, 10), None, None, (SOURCE_REF,)),
        R5VisitRecord("flow-visit-2", "flow-subject-window", "flow-site-a", "flow-spine-window", "actual", "exact", date(2026, 4, 15), None, None, (SOURCE_REF,)),
    )
    flow = _adapter_for(
        _packet(subjects=subjects, sites=sites, stages=_twelve_catalog(), paths=(
            _path("flow-subject-window", "flow-site-a", (
                _step("flow-stage-consent", date(2026, 1, 6)),
                _step("flow-stage-screening", date(2026, 1, 15)),
                _step("flow-stage-treatment", date(2026, 2, 1)),
            )),
        ), visits=visits)
    ).overview(project_ref=PROJECT)["projection"]["subject_flow"]
    row = flow["subjects"][0]
    assert row["jump_window_start"] == "2026-02-10"
    assert row["jump_window_end"] == "2026-02-10"
    assert row["journey_jump_enabled"] is True


# ---------------------------------------------------------------------------
# Authority hash and contract version invariants
# ---------------------------------------------------------------------------


def test_flow_records_enter_authority_hash_and_require_flow_contract_version() -> None:
    packet = build_synthetic_r5_authority_packet()
    assert packet.authority_contract_version == R5_FLOW_AUTHORITY_CONTRACT_VERSION
    assert packet.authority_hash != FLOW_LEGACY_AUTHORITY_HASH

    stages = list(packet.flow_stages)
    stages[0] = replace(stages[0], stage_label_zh=stages[0].stage_label_zh + "（修订）")
    relabeled = replace(packet, flow_stages=tuple(stages), authority_hash="", source_snapshot_sha256="")
    assert relabeled.authority_hash != packet.authority_hash

    with pytest.raises(R5ProductAdapterError) as exc_info:
        replace(packet, authority_contract_version="2026-08-26.1")
    assert exc_info.value.code == "FLOW_CONTRACT_VERSION_MISMATCH"
    with pytest.raises(R5ProductAdapterError) as exc_info:
        replace(packet, authority_hash="0" * 64)
    assert exc_info.value.code == "AUTHORITY_DIGEST_MISMATCH"
    with pytest.raises(R5ProductAdapterError) as exc_info:
        replace(packet, flow_stages=packet.flow_stages + (packet.flow_stages[0],), authority_hash="", source_snapshot_sha256="")
    assert exc_info.value.code == "FLOW_STAGE_DUPLICATE"


def test_visit_phase_ref_change_does_not_affect_subject_flow() -> None:
    packet = build_synthetic_r5_authority_packet()
    base_flow = _adapter_for(packet).overview(project_ref=SYNTHETIC_PROJECT)["projection"]["subject_flow"]
    modified_visits = tuple(
        replace(visit, phase_ref="s7-phase-rewired") if visit.subject_ref == "s7-subject-10008" else visit
        for visit in packet.visits
    )
    rewired = replace(packet, visits=modified_visits, authority_hash="", source_snapshot_sha256="")
    rewired_flow = _adapter_for(rewired).overview(project_ref=SYNTHETIC_PROJECT)["projection"]["subject_flow"]
    assert rewired_flow == base_flow


# ---------------------------------------------------------------------------
# Router envelope integration
# ---------------------------------------------------------------------------


def _principal() -> MonitoringAuthenticatedPrincipal:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return MonitoringAuthenticatedPrincipal.from_server_verified_claims(
        {
            "server_verified": True,
            "principal_id": "s7-user-001",
            "tenant_id": "s7-tenant-001",
            "roles": ["medical_manager"],
            "project_scope": [SYNTHETIC_PROJECT],
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "authenticated": True,
            "authn_method": "offline-test-session",
            "session_id": "s7-flow-test-session",
            "directory_revision": "s7-test-directory-v1",
            "verification_ref_sha256": "c" * 64,
        },
        now=now,
    )


def _client(principal: MonitoringAuthenticatedPrincipal) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_medical_monitoring_r5_product_router(
            synthetic_fixture_mode=True,
            principal_resolver=lambda _request: principal,
        )
    )
    return TestClient(app)


def test_router_overview_envelope_carries_subject_flow_and_digest_covers_it() -> None:
    client = _client(_principal())
    base = R5_PRODUCT_PREFIX.format(project_id=SYNTHETIC_PROJECT)
    response = client.get(f"{base}/overview")
    assert response.status_code == 200
    payload = response.json()
    flow = payload["projection"]["subject_flow"]
    assert flow["availability"] == "available"
    assert flow["reconciliation"]["state"] == "matched"
    assert payload["response_snapshot_sha256"] == response_snapshot_sha256(payload)

    tampered = deepcopy(payload)
    tampered["projection"]["subject_flow"]["stages"][0]["current_count"] += 1
    assert response_snapshot_sha256(tampered) != payload["response_snapshot_sha256"]

    small = client.get(
        f"{base}/overview",
        params={"run_ref": "s7-run-current-001", "snapshot_ref": "s7-snapshot-current-001", "cutoff_ref": SYNTHETIC_CUTOFF, "site_ref": "s7-site-small-001"},
    )
    assert small.status_code == 200
    small_flow = small.json()["projection"]["subject_flow"]
    assert small_flow["reconciliation"]["state"] == "matched"
    assert small_flow["coverage"]["total_subjects"] == 0
    assert small_flow["subjects"] == []
