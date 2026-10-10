"""R31轮（R31-04）：量表周分值（UASW2/4/8/12）日期锚定。

此前周分值事件start恒None——全部UAS7量表记录落「日期待确认」：无法
推算周归属、指标趋势退化为单柱、预设监查重点「UAS7完整性」不可操作
（R31D位实测三受试者4条UAS7全部待确认；21009第12周15分与2026-06-03
起「荨麻疹加重」AE临床高度相关但系统无法建立时间关联）。

锚定规则（列名周数+源记录日期，不凭空造数）：
- 优先SV同周访视（VISIT=W{N}）的实际日期（记录值）；
- 缺席时按EX首次给药日期+周数×7天推定（第N周评估=首剂后第7N+1天，
  与W2=Day15/W4=Day29访视窗一致）；锚定依据写入事件标签；
- 两者皆缺时保持missing（日期待确认），不补造。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.test_facts_publication_event_time import (  # noqa: E402
    _workspace,
)
from packages.medical_monitoring.projections.facts_publication import (  # noqa: E402
    FactsPublicationAuthorityProvider,
)


def _scale_events(packet):
    return sorted(
        (e for e in packet.events if e.subtype == "scale"),
        key=lambda e: e.event_ref,
    )


def test_sv_recorded_visit_date_anchors_scale_week(tmp_path: Path) -> None:
    workspace = _workspace(
        tmp_path,
        {
            "UAS": [
                {
                    "SUBJID": "21009",
                    "UASW2": "6",
                    "UASW12": "15",
                },
            ],
            "SV": [
                {"SUBJID": "21009", "VISIT": "W2", "VISDAT": "2026-03-29"},
                {"SUBJID": "21009", "VISIT": "W12", "VISDAT": "2026-06-07"},
            ],
        },
    )
    packet = FactsPublicationAuthorityProvider(workspace).get_packet(
        "proj-test", snapshot_ref="facts-snapshot-001"
    )
    events = _scale_events(packet)
    assert len(events) == 2
    by_label = {e.measure_label: e for e in events}
    week2 = by_label["UAS7量表（第2周）"]
    week12 = by_label["UAS7量表（第12周）"]
    # 记录日期锚定：进共享时间轴（exact + 可解析日期）
    assert week2.date_state == "exact"
    assert str(week2.start_date) == "2026-03-29"
    assert week12.date_state == "exact"
    assert str(week12.start_date) == "2026-06-07"
    # 锚定出处写入标签（推定要有出处）
    assert "W2访视记录日期" in week2.label_zh
    assert "W12访视记录日期" in week12.label_zh


def test_ex_first_dose_derives_week_anchor_when_sv_missing(
    tmp_path: Path,
) -> None:
    workspace = _workspace(
        tmp_path,
        {
            "UAS": [
                {
                    "SUBJID": "21009",
                    "UASW2": "6",
                    "UASW4": "9",
                },
            ],
            "EX": [
                {"SUBJID": "21009", "EXDAT": "2026-03-15"},
                {"SUBJID": "21009", "EXDAT": "2026-03-29"},
            ],
        },
    )
    packet = FactsPublicationAuthorityProvider(workspace).get_packet(
        "proj-test", snapshot_ref="facts-snapshot-001"
    )
    events = _scale_events(packet)
    by_label = {e.measure_label: e for e in events}
    week2 = by_label["UAS7量表（第2周）"]
    week4 = by_label["UAS7量表（第4周）"]
    # 第N周=首剂后第7N+1天：首剂2026-03-15 → W2=+14天=03-29，W4=+28天=04-12
    assert str(week2.start_date) == "2026-03-29"
    assert str(week4.start_date) == "2026-04-12"
    assert week2.date_state == "exact"
    assert "按首次给药日期2026-03-15+第2周推定" in week2.label_zh


def test_no_anchor_source_keeps_missing_state(tmp_path: Path) -> None:
    """SV与EX都缺时不凭空补造——保持日期待确认（诚实缺省）。"""
    workspace = _workspace(
        tmp_path,
        {
            "UAS": [{"SUBJID": "21009", "UASW2": "6", "UASW4": "9"}],
            "AE": [
                {
                    "SUBJID": "21009",
                    "AETERM": "瘙痒",
                    "AESEV": "1级",
                    "AESTDAT": "2026-03-20",
                },
            ],
        },
    )
    packet = FactsPublicationAuthorityProvider(workspace).get_packet(
        "proj-test", snapshot_ref="facts-snapshot-001"
    )
    events = _scale_events(packet)
    assert len(events) == 2
    assert all(e.date_state == "missing" for e in events)
    assert all(e.start_date is None for e in events)


def test_partial_week_visit_date_falls_back_to_ex_derivation(
    tmp_path: Path,
) -> None:
    """SV同周访视日期非精确（如空值）时不用它，落EX推定。"""
    workspace = _workspace(
        tmp_path,
        {
            "UAS": [{"SUBJID": "23003", "UASW8": "12", "UASW12": "8"}],
            "SV": [
                {"SUBJID": "23003", "VISIT": "W8", "VISDAT": ""},
            ],
            "EX": [{"SUBJID": "23003", "EXDAT": "2026-01-10"}],
            "AE": [
                {
                    "SUBJID": "23003",
                    "AETERM": "瘙痒",
                    "AESEV": "1级",
                    "AESTDAT": "2026-01-20",
                },
            ],
        },
    )
    packet = FactsPublicationAuthorityProvider(workspace).get_packet(
        "proj-test", snapshot_ref="facts-snapshot-001"
    )
    events = _scale_events(packet)
    assert len(events) == 2
    by_label = {e.measure_label: e for e in events}
    event = by_label["UAS7量表（第8周）"]
    assert str(event.start_date) == "2026-03-07"  # 2026-01-10 + 56 天
    assert "推定" in event.label_zh
