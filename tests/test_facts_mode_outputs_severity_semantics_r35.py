"""R35轮（R35-06）：「真实发现」模板卡的严重程度语义诚实性。

确定性兜底发现此前对一切域无差别输出「已核验事实：…严重程度中度」
——合并用药、访视记录并无严重程度属性，系统以核实口吻陈述了不存在的
属性（D位实测60卡=AE15+CM19+SV26全带该子句）。现在只有源记录载明严重
度（severity_source=recorded）才输出该子句；其余域如实陈述记录存在，
分诊档位以「系统按中度/重度关注标记」归因于系统。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.api.r7_product.facts_mode_outputs import (  # noqa: E402
    FactsModeOutputProvider,
)


class _Subject:
    def __init__(self, ref, label, site):
        self.subject_ref, self.subject_label, self.site_ref = ref, label, site


class _Risk:
    def __init__(self, ref, anchor, subject, domain, severity, source):
        self.risk_ref = ref
        self.risk_instance_ref = f"riski-{ref}"
        self.risk_anchor_ref = anchor
        self.subject_ref = subject
        self.domain = domain
        self.severity = severity
        self.severity_source = source
        self.source_locator_refs = (f"loc-{ref}",)


class _Event:
    def __init__(self, ref, subject, domain, label, start):
        self.event_ref = ref
        self.subject_ref = subject
        self.site_ref = "site-01"
        self.domain = domain
        self.label_zh = label
        self.start_date = start
        self.source_locator_refs = (f"loc-{ref}",)


class _Packet:
    def __init__(self, subjects, risks, events):
        self.subjects = subjects
        self.risks = risks
        self.events = events


def test_severity_clause_only_for_recorded_source(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"  # 不写AI工件→走确定性兜底路径
    packet = _Packet(
        subjects=[_Subject("subject-01001", "01001", "site-01")],
        risks=[
            _Risk(
                "risk-AE-000001", "event-AE-000001", "subject-01001",
                "ae", "medium", "recorded",
            ),
            _Risk(
                "risk-CM-000002", "event-CM-000002", "subject-01001",
                "cm", "medium", "inferred",
            ),
            _Risk(
                "risk-SV-000003", "event-SV-000003", "subject-01001",
                "protocol_compliance", "medium", "inferred",
            ),
        ],
        events=[
            _Event(
                "event-AE-000001", "subject-01001", "ae",
                "荨麻疹加重", "2026-06-03",
            ),
            _Event(
                "event-CM-000002", "subject-01001", "cm",
                "苯磺酸氨氯地平", "2026-04-01",
            ),
            _Event(
                "event-SV-000003", "subject-01001", "protocol_compliance",
                "访视失约·W16", "2026-05-20",
            ),
        ],
    )
    provider = FactsModeOutputProvider(artifacts)
    findings = provider._daily_findings(
        {"project_id": "proj-test"}, packet
    )

    by_risk = {item["risk_id"]: item for item in findings}
    assert set(by_risk) == {
        "risk-AE-000001", "risk-CM-000002", "risk-SV-000003",
    }

    ae = by_risk["risk-AE-000001"]
    # AE源记录载明严重度：「严重程度中度」是真实的记录属性
    assert "严重程度中度" in ae["basis"]
    assert "中度不良事件信号" in ae["finding"]

    cm = by_risk["risk-CM-000002"]
    # 合并用药没有严重程度属性——不得以核实口吻陈述；分诊档位归因系统
    assert "严重程度" not in cm["basis"]
    assert "已核验事实：受试者01001于2026-04-01记录一条合并用药" in cm["basis"]
    assert "系统按中度关注标记该合并用药记录" in cm["finding"]
    assert "中度合并用药信号" not in cm["finding"]

    sv = by_risk["risk-SV-000003"]
    assert "严重程度" not in sv["basis"]
    assert "系统按中度关注标记" in sv["finding"]
