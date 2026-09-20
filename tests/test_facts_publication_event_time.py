"""WP2回归切片1：事件结束日期与起始日期列选择（审阅WP2）。

- 事件应保留真实结束日期（*ENDAT），不再恒为None；持续状态（未填结束
  日期）如实为missing而非补造。
- 起始日期列选择必须显式优先*STDAT语义列，任意首个*DAT列（如页面上的
  VISDAT）不得冒充事件起始日期。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.medical_monitoring.projections.facts_publication import (  # noqa: E402
    FactsPublicationAuthorityProvider,
)


def _workspace(tmp_path: Path, tables: dict[str, list[dict]]) -> Path:
    import hashlib

    workspace = tmp_path / "proj"
    artifacts = workspace / "runtime" / "artifacts"
    artifacts.mkdir(parents=True)
    for table, rows in tables.items():
        payload = {table: rows}
        digest = hashlib.sha256(
            json_dumps(payload).encode("utf-8")
        ).hexdigest()
        (artifacts / f"{digest}.json").write_text(
            json_dumps(payload), encoding="utf-8"
        )
    return workspace


def json_dumps(payload) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _events_by_label(provider_events, needle: str):
    return [e for e in provider_events if needle in (e.label_zh or "")]


def test_ae_event_keeps_real_end_date(tmp_path: Path) -> None:
    workspace = _workspace(
        tmp_path,
        {
            "AE": [
                {
                    "SUBJID": "01001",
                    "AETERM": "头痛",
                    "AESEV": "1",
                    "AESTDAT": "2026-01-05",
                    "AEENDAT": "2026-01-12",
                },
                {
                    "SUBJID": "01001",
                    "AETERM": "腹泻",
                    "AESEV": "2",
                    "AESTDAT": "2026-02-03",
                    # 未恢复：结束日期留空 = 持续中，如实missing
                    "AEENDAT": "",
                },
            ],
        },
    )
    provider = FactsPublicationAuthorityProvider(workspace)
    packet = provider.get_packet("proj-test", snapshot_ref="facts-s2")
    ae_events = [e for e in packet.events if e.domain == "ae"]
    by_label = {e.label_zh: e for e in ae_events}
    headache = next(e for label, e in by_label.items() if "头痛" in label)
    diarrhea = next(e for label, e in by_label.items() if "腹泻" in label)
    assert headache.end_date is not None
    assert str(headache.end_date) == "2026-01-12"
    # 持续中的事件不得补造结束日期
    assert diarrhea.end_date is None


def test_start_column_prefers_stdat_over_page_dates(tmp_path: Path) -> None:
    workspace = _workspace(
        tmp_path,
        {
            "CM": [
                {
                    "SUBJID": "01001",
                    "CMTRT": "阿司匹林",
                    "CMSTDAT": "2026-03-01",
                    "CMENDAT": "2026-03-20",
                    "VISDAT": "2026-04-10",  # 页面/访视日期不得冒充开始
                }
            ],
        },
    )
    provider = FactsPublicationAuthorityProvider(workspace)
    packet = provider.get_packet("proj-test", snapshot_ref="facts-s3")
    cm_events = [e for e in packet.events if e.domain == "cm"]
    assert cm_events, "CM event missing"
    event = cm_events[0]
    assert str(event.start_date) == "2026-03-01"


def test_severity_source_honesty(tmp_path: Path) -> None:
    # WP2：源记录载明的严重度=recorded；缺失=unknown（不伪装中度）；
    # 非AE表的系统推定=inferred。
    workspace = _workspace(
        tmp_path,
        {
            "AE": [
                {
                    "SUBJID": "01001",
                    "AETERM": "头痛",
                    "AESEV": "重度",
                    "AESTDAT": "2026-01-05",
                },
                {
                    "SUBJID": "01001",
                    "AETERM": "乏力",
                    # 无AESEV：严重度未知
                    "AESTDAT": "2026-02-01",
                },
            ],
            "CM": [
                {
                    "SUBJID": "01001",
                    "CMTRT": "阿司匹林",
                    "CMSTDAT": "2026-03-01",
                }
            ],
        },
    )
    provider = FactsPublicationAuthorityProvider(workspace)
    packet = provider.get_packet("proj-test", snapshot_ref="facts-s4")
    risks = packet.risks
    # 风险经event_ref回链到事件标签定位（风险类型是通用核查标签，不含术语）
    def _risk_for(term: str):
        event = next(e for e in packet.events if term in (e.label_zh or ""))
        return next(r for r in risks if r.event_ref == event.event_ref)

    headache = _risk_for("头痛")
    fatigue = _risk_for("乏力")
    aspirin = _risk_for("阿司匹林")
    assert headache.severity == "critical" and headache.severity_source == "recorded"
    assert fatigue.severity_source == "unknown"
    assert aspirin.severity_source == "inferred"


def test_event_carries_original_record_id(tmp_path: Path) -> None:
    # WP2：原始记录号与源位置分离——重排/增量下跨表引用不漂移。
    workspace = _workspace(
        tmp_path,
        {
            "AE": [
                {
                    "SUBJID": "01001",
                    "AETERM": "头痛",
                    "AESEV": "1",
                    "AESTDAT": "2026-01-05",
                    "Block顺序号": "A-0042",
                },
                {
                    "SUBJID": "01001",
                    "AETERM": "腹泻",
                    "AESEV": "2",
                    "AESTDAT": "2026-02-03",
                    # 源无记录号：空串，不编造
                },
            ],
        },
    )
    provider = FactsPublicationAuthorityProvider(workspace)
    packet = provider.get_packet("proj-test", snapshot_ref="facts-s5")
    headache = next(e for e in packet.events if "头痛" in (e.label_zh or ""))
    diarrhea = next(e for e in packet.events if "腹泻" in (e.label_zh or ""))
    assert headache.source_record_id == "A-0042"
    assert diarrhea.source_record_id == ""
