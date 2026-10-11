"""R34轮（R29-07）：「合并用药与病史一致性」专项交叉判定。

- 此前CM记录只落「低风险·系统推定·医学依据空白」模板旗标，无任何
  CM-MH交叉核对产出（report_D.md发现3）：合成数据植入的
  「22006 孟鲁司特钠片·用药目的写明哮喘病史·而MH无哮喘记录」未被
  检出；55条高/中风险定位中CM-病史一致性域为空。
- 修复后两条确定性路径：
  ①CMINDC明示疾病词（剔除通用短语后）在该受试者MH全文无对应 →
    中等级+可核实依据；
  ②CMINDC为空/通用时按内置常见用药对照推定适应症词，MH无对应 →
    中等级+「按常见适应症对照提示核实，非医学诊断」依据。
- 一致（MH有对应记录）或无法判定（通用短语/未收录药物）不制造发现。
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


def _cm_risk_records(tmp_path: Path, cm_rows, mh_rows):
    workspace = _workspace(
        tmp_path,
        {"CM": cm_rows, "MH": mh_rows},
    )
    provider = FactsPublicationAuthorityProvider(workspace)
    packet = provider.get_packet("proj-test", snapshot_ref="facts-snapshot-001")
    return [r for r in packet.risks if r.domain == "cm"]


def test_indication_named_condition_missing_from_history_flags(tmp_path: Path) -> None:
    """路径①：CMINDC明示「哮喘」而MH无哮喘——必须检出并给出依据。"""
    records = _cm_risk_records(
        tmp_path,
        [{
            "SUBJID": "22006",
            "CMNUM": "C006",
            "CMTRT": "孟鲁司特钠片",
            "CMINDC": "哮喘病史长期用药",
            "CMSTDAT": "2026-01-10",
            "CMENDAT": "",
            "CMONGO": "是",
        }],
        [
            {"SUBJID": "22006", "MHTERM": "慢性乙型肝炎携带", "MHSTDAT": "2010-01-01", "MHONGO": "是"},
            {"SUBJID": "22006", "MHTERM": "偏头痛", "MHSTDAT": "2015-06-01", "MHONGO": "否"},
        ],
    )
    assert records, "CM风险锚点行缺失"
    flagged = [r for r in records if "一致性待核实" in (r.medical_note or "")]
    assert flagged, "CMINDC明示哮喘而病史无哮喘——CM-MH一致性发现缺失"
    assert all(r.severity == "medium" for r in flagged), "一致性发现必须为中等级"
    note = flagged[0].medical_note
    assert "哮喘" in note and "孟鲁司特钠片" in note
    assert "慢性乙型肝炎携带" in note, "依据须列出病史实际记录供核实"


def test_indication_condition_present_in_history_stays_quiet(tmp_path: Path) -> None:
    """一致（MH有对应记录）不制造发现——保持低等级锚点、无一致性文案。"""
    records = _cm_risk_records(
        tmp_path,
        [{
            "SUBJID": "23001",
            "CMNUM": "C001",
            "CMTRT": "孟鲁司特钠片",
            "CMINDC": "哮喘病史长期用药",
            "CMSTDAT": "2026-01-10",
            "CMENDAT": "",
            "CMONGO": "是",
        }],
        [{"SUBJID": "23001", "MHTERM": "哮喘", "MHSTDAT": "2012-03-01", "MHONGO": "是"}],
    )
    assert records
    assert all("一致性待核实" not in (r.medical_note or "") for r in records)
    assert all(r.severity != "medium" for r in records)


def test_generic_indication_drug_lookup_still_applies(tmp_path: Path) -> None:
    """CMINDC为通用描述（「既往用药」/空）时仍走常见用药对照：孟鲁司特
    +病史无哮喘/鼻炎记录→按对照提示核实（R29-07 TesterD期望：23003既往
    奥马珠单抗仅低级别空依据属缺陷，此类用药-病史覆盖缺口须可见）。"""
    records = _cm_risk_records(
        tmp_path,
        [
            {
                "SUBJID": "23008", "CMNUM": "C002", "CMTRT": "孟鲁司特钠片",
                "CMINDC": "既往用药", "CMSTDAT": "", "CMENDAT": "2026-07-10", "CMONGO": "否",
            },
            {
                "SUBJID": "23008", "CMNUM": "C003", "CMTRT": "孟鲁司特钠片",
                "CMINDC": "", "CMSTDAT": "2026-02-01", "CMENDAT": "2026-05-01", "CMONGO": "否",
            },
        ],
        [{"SUBJID": "23008", "MHTERM": "胃炎", "MHSTDAT": "2018-01-01", "MHONGO": "否"}],
    )
    assert len(records) >= 2
    flagged = [r for r in records if "常见适应症对照" in (r.medical_note or "")]
    assert len(flagged) == 2, "通用适应症下常见用药对照仍应触发（非医学诊断口径）"
    assert all(r.severity == "medium" for r in flagged)


def test_row_without_drug_and_without_indication_never_flags(tmp_path: Path) -> None:
    """既无药物名称也无适应症文本：无任何推定依据，不制造发现。"""
    records = _cm_risk_records(
        tmp_path,
        [{
            "SUBJID": "23009", "CMNUM": "C001", "CMTRT": "", "CMINDC": "",
            "CMSTDAT": "2026-02-01", "CMENDAT": "2026-05-01", "CMONGO": "否",
        }],
        [{"SUBJID": "23009", "MHTERM": "胃炎", "MHSTDAT": "2018-01-01", "MHONGO": "否"}],
    )
    assert records
    assert all("一致性待核实" not in (r.medical_note or "") for r in records)
    assert all(r.severity != "medium" for r in records)


def test_known_drug_defaulting_indication_flags_when_history_lacks(tmp_path: Path) -> None:
    """路径②：CMINDC为「既往用药」（通用）时，常见用药对照推定适应症；
    病史无对应记录→中等级发现，文案明示「非医学诊断」。"""
    records = _cm_risk_records(
        tmp_path,
        [{
            "SUBJID": "22006",
            "CMNUM": "C007",
            "CMTRT": "左甲状腺素钠",
            "CMINDC": "既往用药",
            "CMSTDAT": "2025-11-01",
            "CMENDAT": "2026-06-01",
            "CMONGO": "否",
        }],
        [{"SUBJID": "22006", "MHTERM": "偏头痛", "MHSTDAT": "2015-06-01", "MHONGO": "否"}],
    )
    assert records
    flagged = [r for r in records if "常见适应症对照" in (r.medical_note or "")]
    assert flagged, "左甲状腺素钠+病史无甲状腺相关记录——对照提示缺失"
    assert all(r.severity == "medium" for r in flagged)
    assert "非医学诊断" in flagged[0].medical_note


def test_known_drug_with_matching_history_stays_quiet(tmp_path: Path) -> None:
    """病史已有对应记录（甲减别名命中）时不制造发现。"""
    records = _cm_risk_records(
        tmp_path,
        [{
            "SUBJID": "22007",
            "CMNUM": "C001",
            "CMTRT": "左甲状腺素钠",
            "CMINDC": "既往用药",
            "CMSTDAT": "2025-11-01",
            "CMENDAT": "2026-06-01",
            "CMONGO": "否",
        }],
        [{"SUBJID": "22007", "MHTERM": "甲状腺功能减退", "MHSTDAT": "2014-01-01", "MHONGO": "是"}],
    )
    assert records
    assert all("一致性待核实" not in (r.medical_note or "") for r in records)


def test_unknown_drug_without_indication_never_flags(tmp_path: Path) -> None:
    """未收录药物+通用适应症：不做任何推定，不制造发现。"""
    records = _cm_risk_records(
        tmp_path,
        [{
            "SUBJID": "22008",
            "CMNUM": "C001",
            "CMTRT": "某未收录新药",
            "CMINDC": "既往用药",
            "CMSTDAT": "2025-11-01",
            "CMENDAT": "2026-06-01",
            "CMONGO": "否",
        }],
        [{"SUBJID": "22008", "MHTERM": "偏头痛", "MHSTDAT": "2015-06-01", "MHONGO": "否"}],
    )
    assert records
    assert all("一致性待核实" not in (r.medical_note or "") for r in records)
