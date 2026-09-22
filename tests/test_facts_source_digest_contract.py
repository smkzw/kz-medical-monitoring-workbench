"""V5-01/N0-R回归：facts源摘要合同跨层一致性。

build_subject_evidence盖章的source_content_sha256必须与
facts_table_source_digest（fresh校验唯一算法）一致——旧实现的
行数式/受试者切片式摘要在本测试下失败。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.medical_monitoring.analysis.ae_mh_cross_analysis import (  # noqa: E402
    FACTS_SOURCE_DIGEST_VERSION,
    build_subject_evidence,
    facts_table_source_digest,
)


def _domains():
    return {
        "DM": [
            {"SUBJID": "01001", "AGE": 54, "SEX": "男", "ARM": "试验组"},
            {"SUBJID": "01002", "AGE": 61, "SEX": "女", "ARM": "安慰剂组"},
        ],
        "AE": [
            {"SUBJID": "01001", "AETERM": "头痛", "AESEV": "1级", "AEOUT": "痊愈"},
            {"SUBJID": "01001", "AETERM": "ALT升高", "AESEV": "2级", "AEOUT": "未恢复"},
            {"SUBJID": "01002", "AETERM": "恶心", "AESEV": "1级", "AEOUT": "痊愈"},
        ],
        "CM": [
            {"SUBJID": "01001", "CMTRT": "对乙酰氨基酚", "CMDOSE": 500},
        ],
    }


def test_builder_stamp_matches_shared_digest() -> None:
    domains = _domains()
    _, source_hashes = build_subject_evidence(domains, "01001")
    assert set(source_hashes) == {"AE", "CM"}
    for table, stamped in source_hashes.items():
        assert stamped == facts_table_source_digest(table, domains[table]), (
            f"facts:{table} 盖章摘要与fresh校验算法不一致（V5-01跨层合同）"
        )


def test_digest_is_content_sensitive_and_typed() -> None:
    rows = [{"SUBJID": "01001", "AESEV": "1级"}]
    base = facts_table_source_digest("AE", rows)
    assert base == facts_table_source_digest("AE", list(rows))
    # 同行数不同内容 → 不同摘要（旧行数式算法无法区分）
    changed = facts_table_source_digest("AE", [{"SUBJID": "01001", "AESEV": "3级"}])
    assert changed != base
    # 类型保留：数值0与字符串"0"、False与0可区分（V5-08 R5-02/03）
    assert facts_table_source_digest("LB", [{"X": 0}]) != facts_table_source_digest(
        "LB", [{"X": "0"}]
    )
    assert facts_table_source_digest("LB", [{"X": False}]) != facts_table_source_digest(
        "LB", [{"X": 0}]
    )
    # 版本标识参与摘要：算法升级不与旧摘要碰撞
    assert FACTS_SOURCE_DIGEST_VERSION in {"facts-source-digest-v2"}
