"""Programmatic density fixture for the R5 projection.

This generator stays in code on purpose (B5 contract): it produces ~1400
derived records whose legacy-shape packet keeps the ``not_provided``
projection state reachable offline; externalizing it would only bloat the
repository with low-value JSON.
"""
from __future__ import annotations

from datetime import date, timedelta

from .product_fixture_records import source_record
from .product_types import (
    DOMAINS,
    R5EventRecord,
    R5RiskRecord,
    R5SiteRecord,
    R5SubjectRecord,
    R5VisitRecord,
)

_DENSITY_LABELS = {
    "ae": "不良事件记录核查",
    "mh": "既往史记录核查",
    "cm": "合并用药核查",
    "ip": "试验药使用核查",
    "lab_exam": "检验检查异常核查",
    "hospital_procedure": "住院或操作记录核查",
    "symptom_efficacy": "症状与疗效趋势核查",
    "protocol_compliance": "方案执行核查",
}


def build_density_records(snapshot_ref: str) -> tuple:
    subject = R5SubjectRecord("s7-subject-density-001", "s7-site-010", "s7-spine-density-001", "受试者 DENSITY-001")
    source = source_record(
        "s7-source-density-001", snapshot_ref, "s7-rev-density-001", "高密度 synthetic 事件定位片段。",
        "高密度验证清单", "高密度验证清单 · 事件与风险定位",
    )
    sources = (source,)
    visits = tuple(
        R5VisitRecord(f"s7-visit-density-{index:04d}", subject.subject_ref, subject.site_ref, subject.spine_ref, "actual", "exact", date(2026, 1, 1) + timedelta(days=index - 1), None, "s7-phase-density", (source.locator_ref,))
        for index in range(1, 41)
    )
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
            label_zh=f"{_DENSITY_LABELS[DOMAINS[index % len(DOMAINS)]]} · 第 {index} 条记录",
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
            risk_type_zh=f"{_DENSITY_LABELS[DOMAINS[index % len(DOMAINS)]]} · 第 {index} 项",
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
