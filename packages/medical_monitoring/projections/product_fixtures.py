"""Explicit synthetic fixtures for the R5 product projection."""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
from typing import Optional

from .product_types import (
    DOMAINS,
    R5AuthorityPacket,
    R5EventRecord,
    R5FlowStageRecord,
    R5HistoryRecord,
    R5ProductAdapterError,
    R5RiskRecord,
    R5SiteRecord,
    R5SourceRecord,
    R5SourceRevisionPair,
    R5SubjectFlowPathRecord,
    R5SubjectFlowStep,
    R5SubjectRecord,
    R5VisitRecord,
    R5_FLOW_AUTHORITY_CONTRACT_VERSION,
    SYNTHETIC_CUTOFF_REF,
    SYNTHETIC_FIXTURE_MODE,
    SYNTHETIC_PROJECT_REF,
    SYNTHETIC_RUN_REF,
    canonical_sha256,
)

class R5AuthorityProvider:
    """Provider contract used by the router; it must return a typed packet."""

    def get_packet(
        self,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> R5AuthorityPacket:
        raise NotImplementedError


class SyntheticR5AuthorityProvider(R5AuthorityProvider):
    """Explicitly isolated, deterministic S7 fixture provider."""

    fixture_mode = True

    @lru_cache(maxsize=16)
    def get_packet(
        self,
        project_ref: str,
        run_ref: Optional[str] = None,
        snapshot_ref: Optional[str] = None,
        cutoff_ref: Optional[str] = None,
    ) -> R5AuthorityPacket:
        return build_synthetic_r5_authority_packet(
            project_ref=project_ref,
            run_ref=run_ref,
            snapshot_ref=snapshot_ref,
            cutoff_ref=cutoff_ref,
        )


def _source(
    locator_ref: str,
    snapshot_ref: str,
    revision: str,
    excerpt: str,
    *,
    record_ref: Optional[str] = None,
) -> R5SourceRecord:
    content_hash = canonical_sha256({"revision": revision, "locator_ref": locator_ref, "excerpt": excerpt})
    location_labels = {
        "s7-source-pd-10008": ("方案执行 Data Listing 第 10008 行", "方案执行 Data Listing · 第 10008 行 · 访视日期单元格"),
        "s7-source-ae-06021": ("AE Data Listing 第 06021 行", "AE Data Listing · 第 06021 行 · 事件日期单元格"),
        "s7-source-ae-mh-06021": ("AE/MH 核查表第 06021 行", "AE/MH 核查表 · 第 06021 行 · 匹配关系"),
        "s7-source-date-001": ("日期核查表第 001 行", "日期核查表 · 第 001 行 · 日期状态单元格"),
        "s7-source-density-001": ("高密度验证清单", "高密度验证清单 · 事件与风险定位"),
    }
    human_record_ref, human_location = location_labels.get(locator_ref, ("合成验证记录", "合成验证来源"))
    return R5SourceRecord(
        locator_ref=locator_ref,
        snapshot_ref=snapshot_ref,
        source_file_ref=f"s7-synthetic-source-file:{revision}",
        source_revision_ref=revision,
        source_revision_content_hash=content_hash,
        record_ref=record_ref or human_record_ref,
        canonical_location=human_location,
        excerpt=excerpt,
        lineage=("本次数据版本", "来源文件", human_record_ref),
    )


def _risk(
    risk_instance_ref: str,
    *,
    risk_key: str,
    site_ref: str,
    subject_ref: str,
    spine_ref: str,
    domain: str,
    severity: str,
    risk_type_zh: str,
    event_ref: str,
    visit_ref: str,
    source_locator_ref: str,
    snapshot_ref: str,
    change_kind: str = "continued",
    change_cause: Optional[str] = None,
) -> R5RiskRecord:
    return R5RiskRecord(
        risk_ref=risk_key,
        risk_instance_ref=risk_instance_ref,
        risk_key=risk_key,
        site_ref=site_ref,
        subject_ref=subject_ref,
        spine_ref=spine_ref,
        domain=domain,
        severity=severity,
        risk_type_zh=risk_type_zh,
        date_state="exact",
        event_ref=event_ref,
        visit_ref=visit_ref,
        risk_anchor_ref=f"s7-anchor-{risk_instance_ref.removeprefix('s7-risk-')}",
        source_locator_refs=(source_locator_ref,),
        change_kind=change_kind,
        change_cause=change_cause,
        prior_snapshot_ref=("s7-snapshot-prior-001" if snapshot_ref != "s7-snapshot-current-001" else None),
    )


def _build_base_records(snapshot_ref: str, cutoff_ref: str) -> tuple[
    tuple[R5SourceRecord, ...],
    tuple[R5SiteRecord, ...],
    tuple[R5SubjectRecord, ...],
    tuple[R5EventRecord, ...],
    tuple[R5VisitRecord, ...],
    tuple[R5RiskRecord, ...],
    tuple[R5HistoryRecord, ...],
]:
    subject_a = R5SubjectRecord("s7-subject-10008", "s7-site-010", "s7-spine-10008", "受试者 10008")
    subject_b = R5SubjectRecord("s7-subject-06021", "s7-site-006", "s7-spine-06021", "受试者 06021")
    subject_date = R5SubjectRecord("s7-subject-date-001", "s7-site-010", "s7-spine-date-001", "受试者 DATE-001")
    subjects = (subject_a, subject_b, subject_date)
    visits = (
        R5VisitRecord("s7-visit-06021-w2", subject_b.subject_ref, subject_b.site_ref, subject_b.spine_ref, "actual", "exact", date(2026, 1, 31), None, "s7-phase-screening", ("s7-source-ae-mh-06021",)),
        R5VisitRecord("s7-visit-w3", subject_b.subject_ref, subject_b.site_ref, subject_b.spine_ref, "actual", "exact", date(2026, 2, 28), None, "s7-phase-treatment", ("s7-source-ae-06021",)),
        R5VisitRecord("s7-visit-w2", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "actual", "exact", date(2026, 2, 15), None, "s7-phase-treatment", ("s7-source-pd-10008",)),
        R5VisitRecord("s7-visit-w4", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "actual", "exact", date(2026, 3, 15), None, "s7-phase-treatment", ("s7-source-pd-10008",)),
        R5VisitRecord("s7-visit-date-exact", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "actual", "exact", date(2026, 1, 10), None, "s7-phase-screening", ("s7-source-date-001",)),
        R5VisitRecord("s7-visit-date-pending", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "unscheduled", "missing", None, None, None, ("s7-source-date-001",)),
    )
    events = (
        R5EventRecord("s7-event-pd-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "protocol_compliance", "protocol_deviation", "exact", date(2026, 3, 15), date(2026, 3, 15), "s7-visit-w4", ("s7-anchor-pd-10008",), ("s7-source-pd-10008",), "方案执行偏离"),
        R5EventRecord("s7-event-ae-06021", subject_b.subject_ref, subject_b.site_ref, subject_b.spine_ref, "ae", "ae", "exact", date(2026, 2, 28), date(2026, 3, 2), "s7-visit-w3", ("s7-anchor-ae-06021",), ("s7-source-ae-06021",), "不良事件记录"),
        R5EventRecord("s7-event-mh-06021", subject_b.subject_ref, subject_b.site_ref, subject_b.spine_ref, "mh", "mh", "exact", date(2026, 1, 31), date(2026, 1, 31), "s7-visit-06021-w2", ("s7-anchor-ae-mh-06021",), ("s7-source-ae-mh-06021",), "既往病史记录"),
        R5EventRecord("s7-event-cm-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "cm", "concomitant_medication", "exact", date(2026, 2, 10), date(2026, 2, 12), "s7-visit-w4", (), ("s7-source-pd-10008",), "合并用药"),
        R5EventRecord("s7-event-ip-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "ip", "ip_dose", "exact", date(2026, 1, 15), date(2026, 3, 15), "s7-visit-w4", (), ("s7-source-pd-10008",), "试验药给药"),
        R5EventRecord("s7-event-lab-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "lab_exam", "lab", "partial", date(2026, 2, 20), None, "s7-visit-w4", (), ("s7-source-pd-10008",), "实验室检查"),
        R5EventRecord("s7-event-procedure-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "hospital_procedure", "procedure", "exact", date(2026, 2, 22), date(2026, 2, 22), "s7-visit-w4", (), ("s7-source-pd-10008",), "操作记录"),
        R5EventRecord("s7-event-symptom-10008", subject_a.subject_ref, subject_a.site_ref, subject_a.spine_ref, "symptom_efficacy", "symptom", "conflicted", date(2026, 2, 1), date(2026, 2, 10), "s7-visit-w4", (), ("s7-source-pd-10008",), "症状/疗效指标"),
        R5EventRecord("s7-event-date-exact", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "ae", "ae", "exact", date(2026, 1, 10), date(2026, 1, 10), "s7-visit-date-exact", (), ("s7-source-date-001",), "日期明确记录"),
        R5EventRecord("s7-event-date-partial", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "lab_exam", "lab", "partial", date(2026, 2, 1), None, "s7-visit-date-pending", (), ("s7-source-date-001",), "日期部分明确记录"),
        R5EventRecord("s7-event-date-conflicted", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "symptom_efficacy", "symptom", "conflicted", date(2026, 2, 15), date(2026, 2, 20), "s7-visit-date-pending", (), ("s7-source-date-001",), "日期冲突记录"),
        R5EventRecord("s7-event-date-missing", subject_date.subject_ref, subject_date.site_ref, subject_date.spine_ref, "protocol_compliance", "protocol_deviation", "missing", None, None, "s7-visit-date-pending", (), ("s7-source-date-001",), "日期待核实记录"),
    )
    risks = (
        _risk("s7-risk-pd-10008", risk_key="s7-risk-key-pd-10008", site_ref=subject_a.site_ref, subject_ref=subject_a.subject_ref, spine_ref=subject_a.spine_ref, domain="protocol_compliance", severity="high", risk_type_zh="方案执行偏离", event_ref="s7-event-pd-10008", visit_ref="s7-visit-w4", source_locator_ref="s7-source-pd-10008", snapshot_ref=snapshot_ref, change_kind="new", change_cause="data"),
        _risk("s7-risk-ae-06021", risk_key="s7-risk-key-ae-06021", site_ref=subject_b.site_ref, subject_ref=subject_b.subject_ref, spine_ref=subject_b.spine_ref, domain="ae", severity="medium", risk_type_zh="不良事件与记录一致性", event_ref="s7-event-ae-06021", visit_ref="s7-visit-w3", source_locator_ref="s7-source-ae-06021", snapshot_ref=snapshot_ref, change_kind="continued", change_cause="coverage"),
        _risk("s7-risk-ae-mh-06021", risk_key="s7-risk-key-ae-mh-06021", site_ref=subject_b.site_ref, subject_ref=subject_b.subject_ref, spine_ref=subject_b.spine_ref, domain="ae", severity="high", risk_type_zh="AE/MH匹配历史", event_ref="s7-event-mh-06021", visit_ref="s7-visit-06021-w2", source_locator_ref="s7-source-ae-mh-06021", snapshot_ref=snapshot_ref, change_kind="upgraded", change_cause="data"),
    )
    events = tuple(
        event
        for event in events
        if event.subject_ref in {item.subject_ref for item in subjects}
    )
    histories = (
        R5HistoryRecord(subject_b.subject_ref, "s7-candidate-ae-mh-06021", "s7-later-fact-ae-mh-06021", "reappeared", "exact", "s7-snapshot-prior-001", snapshot_ref, ("s7-source-ae-mh-06021",)),
    )
    sources = (
        _source("s7-source-pd-10008", snapshot_ref, "s7-rev-pd-001", "参与者 10008；第 4 周访视；实际访视日期 2026-03-15；方案规定访视窗口 2026-03-08 至 2026-03-12。"),
        _source("s7-source-ae-06021", snapshot_ref, "s7-rev-ae-001", "AE记录与对应访视的原始定位片段。"),
        _source("s7-source-ae-mh-06021", snapshot_ref, "s7-rev-aemh-001", "AE/MH匹配历史的原始定位片段。"),
        _source("s7-source-date-001", snapshot_ref, "s7-rev-date-001", "日期状态记录：保留缺失日期，不推断主轴日期。"),
    )
    sites = (
        R5SiteRecord("s7-site-006", (subject_b.subject_ref,), ("s7-pattern-site-006",), ("s7-risk-key-ae-06021", "s7-risk-key-ae-mh-06021"), ("s7-measure-site-006",), "ae", "high", 2, 12, "complete"),
        R5SiteRecord("s7-site-010", (subject_a.subject_ref, subject_date.subject_ref), ("s7-pattern-site-010",), ("s7-risk-key-pd-10008",), ("s7-measure-site-010",), "protocol_compliance", "high", 1, 8, "complete"),
        R5SiteRecord("s7-site-small-001", (), ("s7-pattern-site-small-001",), (), ("s7-measure-site-small-001",), "protocol_compliance", "low", 0, 0, "small_sample"),
    )
    return sources, sites, subjects, events, visits, risks, histories


def _build_density_records(snapshot_ref: str) -> tuple[tuple[R5SourceRecord, ...], tuple[R5SiteRecord, ...], tuple[R5SubjectRecord, ...], tuple[R5EventRecord, ...], tuple[R5VisitRecord, ...], tuple[R5RiskRecord, ...], tuple[R5HistoryRecord, ...]]:
    subject = R5SubjectRecord("s7-subject-density-001", "s7-site-010", "s7-spine-density-001", "受试者 DENSITY-001")
    source = _source("s7-source-density-001", snapshot_ref, "s7-rev-density-001", "高密度 synthetic 事件定位片段。")
    sources = (source,)
    visits = tuple(
        R5VisitRecord(f"s7-visit-density-{index:04d}", subject.subject_ref, subject.site_ref, subject.spine_ref, "actual", "exact", date(2026, 1, 1) + timedelta(days=index - 1), None, "s7-phase-density", (source.locator_ref,))
        for index in range(1, 41)
    )
    density_labels = {
        "ae": "不良事件记录核查",
        "mh": "既往史记录核查",
        "cm": "合并用药核查",
        "ip": "试验药使用核查",
        "lab_exam": "检验检查异常核查",
        "hospital_procedure": "住院或操作记录核查",
        "symptom_efficacy": "症状与疗效趋势核查",
        "protocol_compliance": "方案执行核查",
    }
    events = tuple(
        R5EventRecord(
            event_ref=f"s7-event-density-{index:04d}",
            subject_ref=subject.subject_ref,
            site_ref=subject.site_ref,
            spine_ref=subject.spine_ref,
            domain=DOMAINS[index % len(DOMAINS)],
            subtype=("ae", "mh", "concomitant_medication", "ip_dose", "lab", "hospitalization", "symptom", "protocol_deviation")[index % 8],
            date_state="exact",
            start_date=date(2026, 1, 1) + timedelta(days=(index - 1) % len(visits)),
            end_date=None,
            visit_ref=visits[(index - 1) % len(visits)].visit_ref,
            risk_anchor_refs=(f"s7-anchor-density-{index:03d}",) if index <= 300 else (),
            source_locator_refs=(source.locator_ref,),
            label_zh=f"{density_labels[DOMAINS[index % len(DOMAINS)]]} · 第 {index} 条记录",
        )
        for index in range(1, 1001)
    )
    risks = tuple(
        R5RiskRecord(
            risk_ref=f"s7-risk-key-density-{index:03d}",
            risk_instance_ref=f"s7-risk-density-{index:03d}",
            risk_key=f"s7-risk-key-density-{index:03d}",
            site_ref=subject.site_ref,
            subject_ref=subject.subject_ref,
            spine_ref=subject.spine_ref,
            domain=DOMAINS[index % len(DOMAINS)],
            severity=("high", "medium", "low")[index % 3],
            risk_type_zh=f"{density_labels[DOMAINS[index % len(DOMAINS)]]} · 第 {index} 项",
            date_state="exact",
            event_ref=events[index - 1].event_ref,
            visit_ref=events[index - 1].visit_ref,
            risk_anchor_ref=f"s7-anchor-density-{index:03d}",
            source_locator_refs=(source.locator_ref,),
            change_kind="continued",
            change_cause="coverage",
        )
        for index in range(1, 301)
    )
    site = R5SiteRecord(subject.site_ref, (subject.subject_ref,), ("s7-pattern-density-001",), tuple(risk.risk_ref for risk in risks), ("s7-measure-density-001",), "ae", "high", 300, 1000, "complete")
    return sources, (site,), (subject,), events, visits, risks, ()


def _build_flow_records() -> tuple[tuple[R5FlowStageRecord, ...], tuple[R5SubjectFlowPathRecord, ...]]:
    """Deterministic Slice-07B synthetic flow catalog and canonical paths.

    The reserved missing entry exercises the partial-path bucket; the same
    column branch (治疗中 → 完成研究) and the next column branch (治疗中 →
    永久停药) are both legal per the frozen v0.3 §4 edge set.
    """

    flow_source_refs = ("s7-source-pd-10008",)
    stages = (
        R5FlowStageRecord("s7-flow-stage-consent", "已签署知情同意", 0, 0, "main", True, False, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-missing", "既往阶段数据未提供", 0, 1, "missing", True, False, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-screening", "筛选", 1, 0, "main", False, False, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-screen-fail", "筛选失败", 1, 1, "branch_terminal", False, True, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-treatment", "治疗中", 2, 0, "main", False, False, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-completed", "完成研究", 2, 1, "branch_terminal", False, True, flow_source_refs),
        R5FlowStageRecord("s7-flow-stage-stopped", "永久停药", 3, 0, "branch_terminal", False, True, flow_source_refs),
    )
    paths = (
        R5SubjectFlowPathRecord(
            subject_ref="s7-subject-10008",
            site_ref="s7-site-010",
            steps=(
                R5SubjectFlowStep("s7-flow-stage-consent", date(2026, 1, 10), date(2026, 1, 10), "exact", "签署知情同意，进入筛选", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-screening", date(2026, 1, 20), date(2026, 1, 20), "exact", "筛选通过，进入治疗", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-treatment", date(2026, 2, 1), date(2026, 2, 1), "exact", "入组治疗", flow_source_refs),
            ),
            path_state="complete",
            stage_change_kind="unchanged",
            prior_run_current_stage_ref="s7-flow-stage-treatment",
        ),
        R5SubjectFlowPathRecord(
            subject_ref="s7-subject-06021",
            site_ref="s7-site-006",
            steps=(
                R5SubjectFlowStep("s7-flow-stage-consent", date(2026, 1, 5), date(2026, 1, 5), "exact", "签署知情同意，进入筛选", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-screening", date(2026, 1, 12), date(2026, 1, 12), "exact", "筛选未通过", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-screen-fail", date(2026, 1, 20), date(2026, 1, 20), "exact", "筛选失败，终止研究", flow_source_refs),
            ),
            path_state="complete",
            stage_change_kind="advanced",
            prior_run_current_stage_ref="s7-flow-stage-screening",
        ),
        R5SubjectFlowPathRecord(
            subject_ref="s7-subject-date-001",
            site_ref="s7-site-010",
            steps=(
                R5SubjectFlowStep("s7-flow-stage-missing", None, None, "missing", "既往阶段数据未提供", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-screening", date(2026, 2, 1), None, "partial", "补录筛选记录", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-treatment", date(2026, 2, 10), None, "partial", "进入治疗", flow_source_refs),
                R5SubjectFlowStep("s7-flow-stage-completed", date(2026, 2, 20), None, "partial", "完成研究", flow_source_refs),
            ),
            path_state="partial",
            stage_change_kind="new",
        ),
    )
    return stages, paths


def build_synthetic_r5_authority_packet(
    *,
    project_ref: str = SYNTHETIC_PROJECT_REF,
    run_ref: Optional[str] = SYNTHETIC_RUN_REF,
    snapshot_ref: Optional[str] = "s7-snapshot-current-001",
    cutoff_ref: Optional[str] = SYNTHETIC_CUTOFF_REF,
) -> R5AuthorityPacket:
    """Build an isolated S7 fixture; callers must explicitly opt into it."""

    if project_ref != SYNTHETIC_PROJECT_REF:
        raise R5ProductAdapterError("PROJECT_NOT_IN_SYNTHETIC_PACKET")
    if run_ref not in {None, SYNTHETIC_RUN_REF}:
        raise R5ProductAdapterError("RUN_NOT_IN_SYNTHETIC_PACKET")
    snapshot = snapshot_ref or "s7-snapshot-current-001"
    if snapshot == "s7-snapshot-density-001":
        cutoff = cutoff_ref or "2026-12-31"
        records = _build_density_records(snapshot)
    elif snapshot in {
        "s7-snapshot-current-001",
        "s7-snapshot-comparable-001",
        "s7-snapshot-not-comparable-001",
        "s7-snapshot-date-edge-001",
        "s7-snapshot-aemh-001",
    }:
        cutoff = cutoff_ref or SYNTHETIC_CUTOFF_REF
        records = _build_base_records(snapshot, cutoff)
    else:
        raise R5ProductAdapterError("SNAPSHOT_NOT_IN_SYNTHETIC_PACKET")
    flow_stages: tuple[R5FlowStageRecord, ...] = ()
    flow_paths: tuple[R5SubjectFlowPathRecord, ...] = ()
    if snapshot != "s7-snapshot-density-001":
        # The density fixture stays a legacy-shape packet on purpose so the
        # not_provided projection state stays reachable offline.
        flow_stages, flow_paths = _build_flow_records()
    if cutoff != cutoff_ref and cutoff_ref is not None:
        raise R5ProductAdapterError("CUTOFF_IDENTITY_MISMATCH")
    sources, sites, subjects, events, visits, risks, histories = records
    if snapshot == "s7-snapshot-aemh-001":
        subjects = tuple(item for item in subjects if item.subject_ref == "s7-subject-06021")
        events = tuple(item for item in events if item.subject_ref == "s7-subject-06021")
        visits = tuple(item for item in visits if item.subject_ref == "s7-subject-06021")
        risks = tuple(item for item in risks if item.subject_ref == "s7-subject-06021")
        sites = tuple(item for item in sites if item.site_ref == "s7-site-006")
    change_kind = "not_comparable" if snapshot == "s7-snapshot-not-comparable-001" else "continued"
    change_cause = "coverage" if change_kind == "not_comparable" else None
    if change_kind != "continued":
        risks = tuple(
            R5RiskRecord(
                risk_ref=item.risk_ref,
                risk_instance_ref=item.risk_instance_ref,
                risk_key=item.risk_key,
                site_ref=item.site_ref,
                subject_ref=item.subject_ref,
                spine_ref=item.spine_ref,
                domain=item.domain,
                severity=item.severity,
                risk_type_zh=item.risk_type_zh,
                date_state=item.date_state,
                event_ref=item.event_ref,
                visit_ref=item.visit_ref,
                risk_anchor_ref=item.risk_anchor_ref,
                source_locator_refs=item.source_locator_refs,
                change_kind=change_kind,
                change_cause=change_cause,
                prior_snapshot_ref="s7-snapshot-prior-001",
            )
            for item in risks
        )
    revision_pairs = tuple(
        R5SourceRevisionPair(
            revision_id=item.source_revision_ref,
            content_hash=item.source_revision_content_hash,
            locator_refs=(item.locator_ref,),
        )
        for item in sources
    )
    return R5AuthorityPacket(
        project_ref=project_ref,
        run_ref=run_ref or SYNTHETIC_RUN_REF,
        snapshot_ref=snapshot,
        cutoff_state="present",
        cutoff_ref=cutoff,
        project_label="S7 医学监查合成项目",
        authority_contract_id="r5-authority-receipt-kind-v1",
        authority_contract_version=(
            R5_FLOW_AUTHORITY_CONTRACT_VERSION if flow_stages else "2026-08-26.1"
        ),
        audience_contract_id="medical-monitoring-r5-exact-contract-v0.3.1",
        visibility_decision_id=f"s7-visibility:{snapshot}",
        visibility_decision_hash=canonical_sha256({"snapshot_ref": snapshot, "projectable": True, "source_count": len(sources)}),
        evaluation_content_identities=(canonical_sha256({"snapshot_ref": snapshot, "kind": "evaluation"}),),
        source_revision_content_pairs=revision_pairs,
        sources=sources,
        sites=sites,
        subjects=subjects,
        events=events,
        visits=visits,
        risks=risks,
        histories=histories if snapshot == "s7-snapshot-aemh-001" else (),
        flow_stages=flow_stages,
        subject_flow_paths=flow_paths,
        synthetic=True,
        data_mode=SYNTHETIC_FIXTURE_MODE,
    )


def build_synthetic_r5_authority_provider() -> SyntheticR5AuthorityProvider:
    return SyntheticR5AuthorityProvider()
