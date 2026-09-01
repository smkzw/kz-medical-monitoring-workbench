"""Representative synthetic field catalogs for tests only.

These catalogs use **generic synthetic canonical ids** (e.g. ``SYN_AE_SEV``)
that carry no project names, absolute paths, or actual listing table/column
names.  They exist solely so tests can exercise the parser, prompt and
workflow against a realistic domain vocabulary without introducing a
production-level default catalog.

No production module imports this file.
"""

from __future__ import annotations

from mm_r3_rule_ai.catalog import (
    ConditionOperator,
    FieldCatalog,
    FieldSpec,
    ValueType,
)

_CMP_NUM = (
    ConditionOperator.GT,
    ConditionOperator.GE,
    ConditionOperator.LT,
    ConditionOperator.LE,
    ConditionOperator.EQ,
    ConditionOperator.NE,
    ConditionOperator.IN,
    ConditionOperator.NOT_IN,
    ConditionOperator.IS_MISSING,
    ConditionOperator.IS_PRESENT,
)
_CODED = (
    ConditionOperator.EQ,
    ConditionOperator.NE,
    ConditionOperator.CONTAINS,
    ConditionOperator.IN,
    ConditionOperator.NOT_IN,
    ConditionOperator.IS_MISSING,
    ConditionOperator.IS_PRESENT,
)


def synthetic_catalog() -> FieldCatalog:
    """A representative AE/MH/CM/IP/PD/IE/LB catalog with generic ids."""
    specs = (
        # AE
        FieldSpec("SYN_AE_SEV", "AE", "严重程度", "不良事件严重程度（轻度/中度/重度）", ValueType.STRING, _CODED),
        FieldSpec("SYN_AE_SER", "AE", "严重性", "是否严重不良事件（是/否）", ValueType.STRING, _CODED),
        FieldSpec("SYN_AE_OUT", "AE", "结局", "不良事件结局", ValueType.STRING, _CODED),
        # MH
        FieldSpec("SYN_MH_TERM", "MH", "病史术语", "既往病史术语文本", ValueType.STRING, _CODED),
        # CM
        FieldSpec("SYN_CM_TRT", "CM", "合并用药名称", "合并用药名称", ValueType.STRING, _CODED),
        FieldSpec("SYN_CM_DOSE", "CM", "合并用药剂量", "合并用药剂量数值", ValueType.NUMBER, _CMP_NUM),
        # IP
        FieldSpec("SYN_IP_DOSE", "IP", "给药剂量", "试验药物给药剂量数值", ValueType.NUMBER, _CMP_NUM),
        # PD
        FieldSpec("SYN_PD_CAT", "PD", "方案偏离类别", "方案偏离类别", ValueType.STRING, _CODED),
        # IE
        FieldSpec("SYN_IE_TESTCD", "IE", "入排标准编号", "入排标准编号", ValueType.STRING, _CODED),
        # LB
        FieldSpec("SYN_LB_TESTCD", "LB", "实验室检查项目编码", "实验室检查项目编码", ValueType.STRING, _CODED),
        FieldSpec("SYN_LB_STRESN", "LB", "实验室检查标准化数值", "实验室检查标准化数值结果", ValueType.NUMBER, _CMP_NUM),
        FieldSpec("SYN_LB_NRIND", "LB", "参考范围标志", "实验室检查参考范围标志（低/正常/高）", ValueType.STRING, _CODED),
    )
    return FieldCatalog(specs)


def single_field_catalog() -> FieldCatalog:
    """A minimal catalog with one coded string field for focused tests."""
    return FieldCatalog((
        FieldSpec("SYN_SINGLE", "AE", "单一字段", "单一测试字段", ValueType.STRING, _CODED),
    ))
