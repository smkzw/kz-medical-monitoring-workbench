"""R31轮（R31-05）：SAE漏报审查模式不得在「肯定无关」事件上误触发。

- 源数据AEREL取值为 肯定有关/可能有关/可能无关/肯定无关（见
  scripts/generate_test_listing.py:153）。此前判定条件用子串匹配
  `"肯定" in rel_raw`，「肯定无关」照样命中——在明确无关、已好转的
  3级事件上误报SAE漏报（对研究中心的严肃错误指控）。
- 修复后：仅「肯定有关」命中；「肯定无关」不得触发；「肯定有关」
  的修饰变体仍触发（防漏报），显式含「肯定无关」一律不触发。
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

_NOTE_NEEDLE = "漏报审查模式"


def _ae_risk_notes(tmp_path: Path, rel_raw: str):
    workspace = _workspace(
        tmp_path,
        {
            "AE": [
                {
                    "SUBJID": "01001",
                    "AETERM": "咳嗽",
                    "AESEV": "3",
                    "AESTDAT": "2026-06-03",
                    "AEENDAT": "2026-06-10",
                    "AEOUT": "未恢复/持续",
                    "AEREL": rel_raw,
                    "AESER": "否",
                }
            ],
        },
    )
    provider = FactsPublicationAuthorityProvider(workspace)
    packet = provider.get_packet("proj-test", snapshot_ref="facts-snapshot-001")
    ae_risks = [r for r in packet.risks if r.domain == "ae"]
    assert ae_risks, "AE风险锚点行缺失"
    return [r.medical_note for r in ae_risks]


def test_definitely_not_related_never_triggers_underreport(tmp_path: Path) -> None:
    notes = _ae_risk_notes(tmp_path, "肯定无关")
    for note in notes:
        assert _NOTE_NEEDLE not in note, (
            "肯定无关的3级事件不得触发SAE漏报审查（误报=对研究中心的错误指控）"
        )
        # 源记录依据段仍须完整呈现（不被误报修复波及）
        assert "与试验药关系：肯定无关" in note


def test_definitely_related_still_triggers_underreport(tmp_path: Path) -> None:
    notes = _ae_risk_notes(tmp_path, "肯定有关")
    assert any(_NOTE_NEEDLE in note for note in notes), (
        "肯定有关+3级+持续+未报SAE仍须触发SAE漏报审查模式"
    )


def test_possibly_related_does_not_trigger_underreport(tmp_path: Path) -> None:
    notes = _ae_risk_notes(tmp_path, "可能有关")
    for note in notes:
        assert _NOTE_NEEDLE not in note


def test_decorated_definitely_related_still_triggers(tmp_path: Path) -> None:
    """「肯定有关」的修饰变体（如带括注）仍视为肯定有关，防漏报。"""
    notes = _ae_risk_notes(tmp_path, "肯定有关（与试验药物明确相关）")
    assert any(_NOTE_NEEDLE in note for note in notes)


def test_mixed_text_containing_not_related_never_triggers(tmp_path: Path) -> None:
    """文本同时含两词时（异常脏数据）按保守方向不触发——误报代价高。"""
    notes = _ae_risk_notes(tmp_path, "肯定无关（非肯定有关）")
    for note in notes:
        assert _NOTE_NEEDLE not in note
