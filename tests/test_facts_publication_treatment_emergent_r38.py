"""R38轮（R36-05）：AE treatment-emergent 时间矛盾核对。

缺陷回顾：22006头痛AE 3级「肯定有关」开始于2026-03-13，早于该受试者
首次给药2026-03-16——给药前发生的事件判定「肯定有关」在时间逻辑上
不成立，但医学依据仅转录源记录字段（严重度/关系/转归），矛盾无人点出。

修复后：AE开始日期（精确）早于该受试者首次EX给药日期（精确）且关系
记录为「肯定有关」时，AE风险行追加治疗emergent矛盾提示（确定性核对，
不代替医学判定、不自动改写关系字段）。
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

_TE_NEEDLE = "治疗emergent核对发现矛盾"


def _packet_with(
    tmp_path: Path,
    ae_rows: list[dict],
    ex_rows: list[dict],
):
    workspace = _workspace(tmp_path, {"AE": ae_rows, "EX": ex_rows})
    provider = FactsPublicationAuthorityProvider(workspace)
    return provider.get_packet("proj-test", snapshot_ref="facts-snapshot-001")


def _ae_notes(packet) -> list[str]:
    notes = [r.medical_note for r in packet.risks if r.domain == "ae"]
    assert notes, "AE风险锚点行缺失"
    return notes


_AE_BASE = {
    "AETERM": "头痛",
    "AESEV": "3",
    "AEOUT": "好转",
    "AEREL": "肯定有关",
    "AESER": "否",
}
_EX_BASE = {
    "EXDAT": "2026-03-16",
    "EXTRT": "试验药",
    "EXSTATE": "完成",
}


def test_pre_dose_definitely_related_flags_contradiction(tmp_path: Path) -> None:
    """给药前发生的「肯定有关」事件必须点出时间矛盾（缺陷场景）。"""

    packet = _packet_with(
        tmp_path,
        [{**_AE_BASE, "SUBJID": "01001", "AESTDAT": "2026-03-13"}],
        [{**_EX_BASE, "SUBJID": "01001"}],
    )
    notes = _ae_notes(packet)
    assert any(_TE_NEEDLE in note for note in notes)
    joined = "\n".join(notes)
    assert "2026-03-13" in joined and "2026-03-16" in joined
    assert "时间逻辑不成立" in joined
    # 源记录依据段仍完整（矛盾提示是追加，不是替换转录）
    assert "与试验药关系：肯定有关" in joined


def test_post_dose_definitely_related_no_contradiction(tmp_path: Path) -> None:
    """给药后发生的「肯定有关」事件不触发治疗emergent矛盾。"""

    packet = _packet_with(
        tmp_path,
        [{**_AE_BASE, "SUBJID": "01001", "AESTDAT": "2026-03-20"}],
        [{**_EX_BASE, "SUBJID": "01001"}],
    )
    for note in _ae_notes(packet):
        assert _TE_NEEDLE not in note


def test_same_day_is_treatment_emergent_not_contradiction(tmp_path: Path) -> None:
    """开始日期=首次给药当日不构成「早于给药」矛盾。"""

    packet = _packet_with(
        tmp_path,
        [{**_AE_BASE, "SUBJID": "01001", "AESTDAT": "2026-03-16"}],
        [{**_EX_BASE, "SUBJID": "01001"}],
    )
    for note in _ae_notes(packet):
        assert _TE_NEEDLE not in note


def test_missing_first_dose_skips_check(tmp_path: Path) -> None:
    """无EX给药记录（或日期非精确）时不做核对、不造结论。"""

    packet = _packet_with(
        tmp_path,
        [{**_AE_BASE, "SUBJID": "01001", "AESTDAT": "2026-03-13"}],
        [{**_EX_BASE, "SUBJID": "01001", "EXDAT": ""}],
    )
    for note in _ae_notes(packet):
        assert _TE_NEEDLE not in note


def test_not_definitely_related_skips_check(tmp_path: Path) -> None:
    """关系非「肯定有关」时不做治疗emergent矛盾提示。"""

    packet = _packet_with(
        tmp_path,
        [{**_AE_BASE, "SUBJID": "01001", "AESTDAT": "2026-03-13", "AEREL": "可能有关"}],
        [{**_EX_BASE, "SUBJID": "01001"}],
    )
    for note in _ae_notes(packet):
        assert _TE_NEEDLE not in note


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
