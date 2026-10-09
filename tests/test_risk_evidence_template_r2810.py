"""R28-10：请核实事项卡差异化信息注入回归。

背景：R29实测55张「请核实事项」卡三段文本仅差受试者号——依据/发现/
行动项只绑定 subject+risk_type_zh，卡面无事件名称、无日期、无规则名、
无差异化核查指向，监查员无法据卡决策。修复：_risk_payload 注入
- 依据段引用规则名（「依据当前项目监查规则「{risk_type_zh}」…」）；
- 发现段注入事件术语与日期（绑定不到事件时回落「域记录+日期状态」，
  不伪造具体事件）；
- 行动项按医学域给出具体核对入口（_DOMAIN_VERIFY_HINTS）。
"""

from __future__ import annotations

from datetime import date

from packages.medical_monitoring.projections.product_projection_helpers import (
    _DOMAIN_VERIFY_HINTS,
    _risk_payload,
)
from packages.medical_monitoring.projections.product_types import (
    R5EventRecord,
    R5RiskRecord,
)


def _risk(domain: str = "ae", *, event_ref: str | None = "event-1", date_state: str = "exact") -> R5RiskRecord:
    return R5RiskRecord(
        risk_ref="risk-1",
        risk_instance_ref="inst-1",
        risk_key="s7-risk-key-ae-06021",
        site_ref="site-01",
        subject_ref="subj-22006",
        spine_ref="spine-1",
        domain=domain,
        severity="high",
        risk_type_zh="AE漏报待核实",
        date_state=date_state,
        event_ref=event_ref,
        visit_ref=None,
        risk_anchor_ref="event-1",
        source_locator_refs=("loc-1",),
    )


def _event(domain: str = "ae") -> R5EventRecord:
    subtype_by_domain = {
        "ae": "ae",
        "cm": "concomitant_medication",
        "lab_exam": "lab",
    }
    return R5EventRecord(
        event_ref="event-1",
        subject_ref="subj-22006",
        site_ref="site-01",
        spine_ref="spine-1",
        domain=domain,
        subtype=subtype_by_domain[domain],
        date_state="exact",
        start_date=date(2026, 6, 10),
        end_date=date(2026, 6, 14),
        visit_ref=None,
        risk_anchor_refs=("event-1",),
        source_locator_refs=("loc-1",),
        label_zh="头痛（3级）",
    )


def test_card_carries_rule_name_event_term_and_date() -> None:
    payload = _risk_payload(_risk(), "receipt-1", subject_label="22006", event_by_ref={"event-1": _event()})
    summary = payload["evidence_summary"]
    # 依据段引用规则名
    assert "「AE漏报待核实」" in summary["basis"]
    # 发现段注入事件术语与真实起止日期
    assert "头痛（3级）" in summary["finding"]
    assert "2026-06-10至2026-06-14" in summary["finding"]
    assert "22006" in summary["finding"]
    # 行动项为AE域差异化指向
    assert _DOMAIN_VERIFY_HINTS["ae"][:6] in summary["action_item"]
    # query_draft三段同步携带规则名/事件/日期/域指向
    assert "「AE漏报待核实」" in summary["query_draft"]
    assert "头痛（3级）" in summary["query_draft"]
    assert "2026-06-10" in summary["query_draft"]


def test_cards_for_different_domains_differ_in_action_item() -> None:
    ae = _risk_payload(_risk(domain="ae"), "receipt-1", event_by_ref={"event-1": _event("ae")})
    cm = _risk_payload(_risk(domain="cm"), "receipt-1", event_by_ref={"event-1": _event("cm")})
    lab = _risk_payload(_risk(domain="lab_exam"), "receipt-1", event_by_ref={"event-1": _event("lab_exam")})
    actions = {
        item["evidence_summary"]["action_item"]
        for item in (ae, cm, lab)
    }
    assert len(actions) == 3, "不同医学域的行动项必须差异化"


def test_unbound_event_falls_back_to_honest_domain_record_clause() -> None:
    # event_ref 指向不存在的事件：不得伪造事件术语，回落域记录+日期状态
    payload = _risk_payload(
        _risk(event_ref="event-missing"),
        "receipt-1",
        subject_label="22006",
        event_by_ref={"event-1": _event()},
    )
    finding = payload["evidence_summary"]["finding"]
    assert "头痛" not in finding
    assert "域记录" in finding
    assert "2026-06-10" not in finding  # exact日期只来自真实绑定事件


def test_non_exact_date_state_does_not_show_specific_date() -> None:
    payload = _risk_payload(
        _risk(date_state="missing"),
        "receipt-1",
        subject_label="22006",
        event_by_ref={"event-1": _event()},
    )
    finding = payload["evidence_summary"]["finding"]
    assert "2026-06-10" not in finding
    assert "缺失" in finding


def test_no_event_lookup_still_renders_complete_card() -> None:
    # 兼容路径：未传event_by_ref（旧调用方）不崩且保持差异化
    payload = _risk_payload(_risk(event_ref=None), "receipt-1", subject_label="22006")
    summary = payload["evidence_summary"]
    assert "「AE漏报待核实」" in summary["basis"]
    assert "域记录" in summary["finding"]
    assert _DOMAIN_VERIFY_HINTS["ae"][:6] in summary["action_item"]
