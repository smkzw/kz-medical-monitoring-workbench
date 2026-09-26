"""W04-VAL（20260926）：诊断豁免收紧——算子能力注册表与walker同源。

验收锚点 R26-A05–A09（review_pack_0926V1/kz_review_0926V1/
04_ACCEPTANCE_0926V1.json）：
- A05 missing/exists可判定例外：不编造不可达indeterminate样本；
- A06 行级比较诊断：gt/eq/regex/date_compare（及其余can_indeterminate算子）
  以缺失/非法/非有限数/部分日期/非法expected输入产生indeterminate，且发布
  分类对同一规则树要求diagnostic_indeterminate覆盖；
- A07 嵌套all/any/not与未知算子保守分类；
- A08 preconditions/trigger/exclusions三棵树共同检查；
- A09 既有包策略变更：影响清单JSON工件、两条现有missing规则单独复核，
  不写旧摘要、不伪造旧gold case。

全部fixture为冻结合成数据；不依赖第二真实项目、付费模型或生产数据库。
发布分类与求值器的同源证据：同一表达式树分别输入
expression_requires_diagnostic_coverage（发布分类）与
_evaluate_predicate_with_trace（真实求值器），断言两边一致。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import pytest

from services.api.app.monitoring_protocol_rule_repository import (
    RulePackLifecycleError,
)
from services.api.app.monitoring_protocol_rule_service import (
    MonitoringProtocolRuleService,
    _evaluate_predicate_with_trace,
)
from services.api.app.monitoring_protocol_rules import (
    _ALLOWED_PREDICATE_OPERATORS,
    OPERATOR_CAPABILITIES,
    expression_requires_diagnostic_coverage,
)
from tests.test_monitoring_gold_shadow_p7c import (
    _ready_shadow,
    _store_boolean_coverage,
)
from tests.test_monitoring_protocol_rules import _store_p7c_release_evidence

_POLICY_IMPACT_ARTIFACT = (
    Path(__file__).resolve().parents[1]
    / "metrics"
    / "monitoring_diagnostic_coverage_policy_impact_20260926.json"
)


def _context(**overrides):
    context = {
        "record": {},
        "previous_record": {},
        "related_records": {},
        "related_domain_keys": set(),
        "observed_domains": set(),
    }
    context.update(overrides)
    return context


def _legacy_requires_diagnostic(
    preconditions,
    trigger_expression,
    exclusions,
) -> bool:
    """R24V2-W04（20260926被本切片修订的窄豁免）逐字复算，仅用于A09影响
    清单的新旧策略对比；不代表当前分类器行为。"""

    def _walk(node) -> bool:
        if isinstance(node, Mapping):
            for key, operand in node.items():
                if str(key) in {"changed", "no_corresponding_record"}:
                    return True
                if _walk(operand):
                    return True
        elif isinstance(node, (list, tuple)):
            return any(_walk(item) for item in node)
        return False

    return any(
        _walk(tree)
        for tree in (preconditions, trigger_expression, exclusions)
    )


# ---------------------------------------------------------------------------
# 注册表与词表同源（防漂移）
# ---------------------------------------------------------------------------


def test_operator_capabilities_are_coextensive_with_predicate_vocabulary() -> None:
    assert set(OPERATOR_CAPABILITIES) == {"total_boolean", "can_indeterminate"}
    total = set(OPERATOR_CAPABILITIES["total_boolean"])
    can_indeterminate = set(OPERATOR_CAPABILITIES["can_indeterminate"])
    assert not total & can_indeterminate
    assert total | can_indeterminate == set(_ALLOWED_PREDICATE_OPERATORS)
    # walker以默认参数自足携带total集合（AST级探针可独立提取执行），
    # 其字面集必须与注册表total_boolean逐项一致（防双源漂移）。
    walker_defaults = (
        expression_requires_diagnostic_coverage.__kwdefaults__ or {}
    )
    assert walker_defaults.get("_total_boolean") == OPERATOR_CAPABILITIES[
        "total_boolean"
    ]


# ---------------------------------------------------------------------------
# A05：missing/exists可判定例外
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("operator", "populated", "populated_result"),
    (
        ("exists", "", False),
        ("exists", "V1", True),
        ("missing", "", True),
        ("missing", "V1", False),
    ),
)
def test_exists_and_missing_are_decidable_for_all_inputs_and_exempt(
    operator: str,
    populated: str,
    populated_result: bool,
) -> None:
    # 缺失（空串/None）与在值两种输入下都返回确定布尔——构造上可判定，
    # 无需也不得编造不可达的indeterminate样本（A05）。
    expression = {operator: {"field": "V"}}
    for record, expected in (
        ({"V": populated}, populated_result),
        ({}, operator == "missing"),
        ({"V": None}, operator == "missing"),
    ):
        result, trace = _evaluate_predicate_with_trace(
            expression,
            _context(record=record),
        )
        assert trace["state"] in {"true", "false"}, (operator, record, trace)
        assert result is expected, (operator, record)
    # 同一算子在发布分类中获得豁免。
    assert (
        expression_requires_diagnostic_coverage(
            {"exists": {"field": "K"}}, expression, {"missing": {"field": "J"}}
        )
        is False
    )


def test_total_boolean_combinators_over_exists_missing_stay_exempt() -> None:
    trees = (
        {"all": [{"exists": {"field": "A"}}, {"missing": {"field": "B"}}]},
        {
            "any": [
                {"missing": {"field": "A"}},
                {"not": {"exists": {"field": "B"}}},
            ]
        },
        {"not": {"exists": {"field": "A"}}},
    )
    for tree in trees:
        result, trace = _evaluate_predicate_with_trace(tree, _context())
        assert trace["state"] in {"true", "false"}
        assert result is (trace["state"] == "true")
        assert (
            expression_requires_diagnostic_coverage(tree, tree, tree) is False
        )


# ---------------------------------------------------------------------------
# A06：can_indeterminate算子在缺失/非法/非有限数/部分日期输入下产生
# indeterminate，且发布分类对同一规则树要求覆盖
# ---------------------------------------------------------------------------


_INDETERMINATE_TRIGGER_CASES = (
    # (operator, trigger_expression, record, 输入缺陷)
    ("eq", {"eq": {"field": "V", "value": "yes"}}, {"V": ""}, "missing_field_value"),
    ("ne", {"ne": {"field": "V", "value": "yes"}}, {"V": None}, "missing_field_value"),
    ("in", {"in": {"field": "V", "value": ["a", "b"]}}, {"V": ""}, "missing_field_value"),
    ("not_in", {"not_in": {"field": "V", "value": ["a"]}}, {"V": ""}, "missing_field_value"),
    ("gt", {"gt": {"field": "V", "value": 3}}, {"V": "BQL"}, "non_numeric_operand"),
    ("gte", {"gte": {"field": "V", "value": 3}}, {"V": float("inf")}, "non_finite_operand"),
    ("lt", {"lt": {"field": "V", "value": 3}}, {}, "missing_field_value"),
    ("lte", {"lte": {"field": "V", "value": 3}}, {"V": "N/A"}, "non_numeric_operand"),
    ("regex", {"regex": {"field": "V", "value": "p"}}, {"V": ""}, "missing_field_value"),
    (
        "changed",
        {"changed": {"field": "V"}},
        {"V": "after"},
        "missing_previous_value",
    ),
    (
        "date_compare",
        {
            "date_compare": {
                "field": "A",
                "other_field": "B",
                "relation": "after",
            }
        },
        {"A": "2026-01-02", "B": "2026-01"},
        "partial_date_operand",
    ),
    (
        "date_delta_days",
        {"date_delta_days": {"field": "A", "other_field": "B", "value": 7}},
        {"A": "2026-13-01", "B": "2026-01-02"},
        "invalid_date_operand",
    ),
    (
        "date_delta_range",
        {"date_delta_range": {"field": "A", "other_field": "B", "min_days": 1}},
        {"A": "", "B": "2026-01-02"},
        "missing_date_operand",
    ),
    (
        "ratio_range",
        {
            "ratio_range": {
                "numerator_field": "N",
                "denominator_field": "D",
                "multiplier": 1,
                "min_value": 0,
                "max_value": 5,
            }
        },
        {"N": "1", "D": "0"},
        "zero_denominator",
    ),
    (
        "no_corresponding_record",
        {"no_corresponding_record": {"domain": "AE"}},
        {},
        "search_domain_not_supplied",
    ),
)


@pytest.mark.parametrize(
    ("operator", "expression", "record", "defect"),
    _INDETERMINATE_TRIGGER_CASES,
)
def test_can_indeterminate_operators_yield_indeterminate_and_are_classified(
    operator: str,
    expression: dict,
    record: dict,
    defect: str,
) -> None:
    # 真实求值器：该输入产生不可判定求值（分支为
    # monitoring_protocol_rule_service._evaluate_predicate_with_trace）。
    _result, trace = _evaluate_predicate_with_trace(
        expression,
        _context(record=record),
    )
    assert trace["state"] == "indeterminate", (operator, defect, trace)
    # 同一规则树（exists前置 + 该触发 + missing排除）被发布分类要求
    # diagnostic_indeterminate覆盖——分类与求值同源。
    assert operator in OPERATOR_CAPABILITIES["can_indeterminate"]
    assert (
        expression_requires_diagnostic_coverage(
            {"exists": {"field": "KEY"}}, expression, {"missing": {"field": "KEY"}}
        )
        is True
    )


def test_evaluator_layer_fails_closed_on_invalid_expected_values() -> None:
    # 非法expected（eq/ne缺失expected、in/not_in非列表）在authoring期被
    # _validate_predicate_node拦截；此处证明求值器层第二道防线对同形状
    # 输入同样返回indeterminate（双防线），且发布分类要求覆盖。
    for expression in (
        {"eq": {"field": "V", "value": ""}},
        {"ne": {"field": "V", "value": ""}},
        {"in": {"field": "V", "value": "not-a-list"}},
        {"not_in": {"field": "V", "value": "not-a-list"}},
    ):
        _result, trace = _evaluate_predicate_with_trace(
            expression,
            _context(record={"V": "x"}),
        )
        assert trace["state"] == "indeterminate", (expression, trace)
        assert (
            expression_requires_diagnostic_coverage({}, expression, {})
            is True
        )


# ---------------------------------------------------------------------------
# A07：嵌套组合器与未知算子保守分类
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tree", "record"),
    (
        # all：可判定子为true，整体状态由可indeterminate子决定。
        ({"all": [{"exists": {"field": "K"}}, {"gt": {"field": "V", "value": 3}}]},
         {"K": "x", "V": "BQL"}),
        # any：无可判定true子，indeterminate子把整体拖入不可判定。
        ({"any": [{"exists": {"field": "K"}}, {"gt": {"field": "V", "value": 3}}]},
         {}),
        ({"not": {"eq": {"field": "V", "value": "yes"}}}, {"V": ""}),
    ),
)
def test_nested_combinators_conservatively_require_coverage(
    tree: dict,
    record: dict,
) -> None:
    # 求值器：嵌套树继承不可判定状态。
    _result, trace = _evaluate_predicate_with_trace(tree, _context(record=record))
    assert trace["state"] == "indeterminate", (tree, trace)
    # 分类器：任一可indeterminate子算子→保守True。
    assert expression_requires_diagnostic_coverage({}, tree, {}) is True


def test_combinators_over_decidable_children_remain_decidable_and_exempt() -> None:
    trees = (
        {"all": [{"exists": {"field": "A"}}, {"exists": {"field": "B"}}]},
        {"any": [{"missing": {"field": "A"}}, {"exists": {"field": "B"}}]},
        {"not": {"missing": {"field": "A"}}},
    )
    for tree in trees:
        _result, trace = _evaluate_predicate_with_trace(tree, _context())
        assert trace["state"] in {"true", "false"}
        assert expression_requires_diagnostic_coverage({}, tree, {}) is False


def test_unknown_operator_is_conservatively_classified(monkeypatch) -> None:
    # 词表外算子：分类器保守要求覆盖（编译期_validate_predicate_node是
    # 第一道防线，分类器保守是第二道）。
    assert (
        expression_requires_diagnostic_coverage(
            {}, {"fuzzy_match": {"field": "K"}}, {}
        )
        is True
    )
    # 词表内但注册表缺失能力的键（注册表漂移防御）：monkeypatch一个
    # 残缺注册表，未注册算子同样保守要求覆盖。
    import services.api.app.monitoring_protocol_rules as rules_module

    monkeypatch.setattr(
        rules_module,
        "OPERATOR_CAPABILITIES",
        {"total_boolean": frozenset({"exists", "missing"})},
    )
    assert (
        expression_requires_diagnostic_coverage(
            {}, {"regex": {"field": "V", "value": "p"}}, {}
        )
        is True
    )


# ---------------------------------------------------------------------------
# A08：三棵树共同检查
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("preconditions", "trigger_expression", "exclusions", "expected"),
    (
        ({}, {"changed": {"field": "V"}}, {}, True),
        ({"changed": {"field": "V"}}, {"exists": {"field": "K"}}, {}, True),
        ({}, {"exists": {"field": "K"}}, {"changed": {"field": "V"}}, True),
        ({}, {"no_corresponding_record": {"domain": "AE"}}, {}, True),
        ({"exists": {"field": "K"}}, {"missing": {"field": "J"}}, {}, False),
        ({}, {}, {}, False),
    ),
)
def test_all_three_trees_are_jointly_examined(
    preconditions: dict,
    trigger_expression: dict,
    exclusions: dict,
    expected: bool,
) -> None:
    assert (
        expression_requires_diagnostic_coverage(
            preconditions, trigger_expression, exclusions
        )
        is expected
    )


# ---------------------------------------------------------------------------
# A09：既有missing规则单独复核 + 策略变更影响清单工件
# ---------------------------------------------------------------------------

# 冻结自真实运行库（只读核验，未写入）：
# implementation/workbench/runs/phase_c_mgk10_authority_v2_20260905/runtime/
#   monitoring_protocol_rules.sqlite3 :: monitoring_rule_definitions
# 其中 monpack_15685e0579ffcfe014f9e63d（published）为已发布包，其唯一
# 规则为 cm_non_ip_medication_date_completeness。
_REAL_MISSING_RULES = (
    {
        "rule_key": "cm_non_ip_medication_date_completeness",
        "rule_family": "data_quality",
        "published_pack_rule": True,
        "preconditions": {"exists": {"field": "CMINDC"}},
        "trigger_expression": {
            "any": [
                {"missing": {"field": "CMSTDAT"}},
                {"missing": {"field": "CMENDAT"}},
            ]
        },
        "exclusions": {"missing": {"field": "SUBJID"}},
    },
    {
        "rule_key": "mh_verbatim_term_completeness",
        "rule_family": "data_quality",
        "published_pack_rule": False,
        "preconditions": {"exists": {"field": "SUBJID"}},
        "trigger_expression": {"missing": {"field": "MHTERM"}},
        "exclusions": {"missing": {"field": "SUBJID"}},
    },
)


@pytest.mark.parametrize(
    "rule",
    _REAL_MISSING_RULES,
    ids=[rule["rule_key"] for rule in _REAL_MISSING_RULES],
)
def test_existing_missing_rules_stay_exempt_and_decidable(rule: dict) -> None:
    trees = (
        rule["preconditions"],
        rule["trigger_expression"],
        rule["exclusions"],
    )
    # 新策略下依旧豁免：纯exists/missing规则构造上可判定。
    assert expression_requires_diagnostic_coverage(*trees) is False
    # 单独复核：三棵树在缺失与完整两种合成输入下全部可判定，
    # 不出现indeterminate——豁免有独立理由而非策略方便。
    for record in (
        {},
        {
            "CMINDC": "X",
            "CMSTDAT": "2026-01-01",
            "CMENDAT": "2026-02-01",
            "SUBJID": "S1",
            "MHTERM": "头痛",
        },
    ):
        for tree in trees:
            _result, trace = _evaluate_predicate_with_trace(
                tree, _context(record=record)
            )
            assert trace["state"] in {"true", "false"}, (rule, tree, trace)


def test_policy_change_impact_manifest_is_written() -> None:
    inventory = [
        {
            "rule_key": rule["rule_key"],
            "source": (
                "runs/phase_c_mgk10_authority_v2_20260905/runtime/"
                "monitoring_protocol_rules.sqlite3:monitoring_rule_definitions"
            ),
            "published_pack_rule": rule["published_pack_rule"],
            "trees": (
                rule["preconditions"],
                rule["trigger_expression"],
                rule["exclusions"],
            ),
        }
        for rule in _REAL_MISSING_RULES
    ]
    inventory.append(
        {
            # 既有跨行changed规则（旧策略已要求覆盖，预期不翻转）。
            "rule_key": "sv_visit_name_post_entry_change",
            "source": (
                "runs/phase_c_mgk10_authority_v2_20260905/runtime/"
                "monitoring_protocol_rules.sqlite3:monitoring_rule_definitions"
            ),
            "published_pack_rule": False,
            "trees": (
                {
                    "all": [
                        {"exists": {"field": "SUBJID"}},
                        {"exists": {"field": "VISIT"}},
                    ]
                },
                {"changed": {"field": "VISIT"}},
                {"missing": {"field": "SUBJID"}},
            ),
        }
    )
    inventory.append(
        {
            # 发布链模板规则形状（tests.test_monitoring_protocol_rules._rule，
            # regex触发）——旧策略放行、新策略要求覆盖，预期翻转。
            "rule_key": (
                "study_treatment.adherence.missed_dose"
                " (release-chain template shape)"
            ),
            "source": "tests.test_monitoring_protocol_rules._rule",
            "published_pack_rule": False,
            "trees": (
                {"exists": {"field": "SUBJID"}},
                {"regex": {"field": "EXDESC", "value": "漏服"}},
                {"missing": {"field": "EXDESC"}},
            ),
        }
    )

    entries = []
    for item in inventory:
        old = _legacy_requires_diagnostic(*item["trees"])
        new = expression_requires_diagnostic_coverage(*item["trees"])
        entries.append(
            {
                "rule_key": item["rule_key"],
                "source": item["source"],
                "published_pack_rule": item["published_pack_rule"],
                "old_requires_diagnostic": old,
                "new_requires_diagnostic": new,
                "flipped": old != new,
            }
        )

    manifest = {
        "policy_version": "W04-VAL-20260926-operator-capability-registry",
        "supersedes": (
            "R24V2-W04（20260926）窄豁免：仅changed/no_corresponding_record"
        ),
        "artifact_of": (
            "tests/test_monitoring_rule_diagnostic_coverage_0926.py::"
            "test_policy_change_impact_manifest_is_written"
        ),
        "repository_history_note": (
            "不篡改旧发布记录、不批量补绿历史资格；历史资格如需重评"
            "必须走新的shadow run与人工授权。"
        ),
        "rules": entries,
        "flipped_rule_keys": [
            entry["rule_key"] for entry in entries if entry["flipped"]
        ],
    }
    _POLICY_IMPACT_ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    _POLICY_IMPACT_ARTIFACT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    flipped = {entry["rule_key"] for entry in entries if entry["flipped"]}
    # 两条现有missing规则与既有changed规则均不翻转；唯一翻转的是
    # 旧策略放行的regex发布链模板规则形状。
    assert flipped == {
        "study_treatment.adherence.missed_dose (release-chain template shape)"
    }
    published_rule = next(
        entry for entry in entries if entry["published_pack_rule"]
    )
    assert published_rule["rule_key"] == "cm_non_ip_medication_date_completeness"
    assert published_rule["flipped"] is False
    # 已发布包（唯一规则）不受策略变更影响，无需补绿历史资格。
    saved = json.loads(_POLICY_IMPACT_ARTIFACT.read_text(encoding="utf-8"))
    assert saved == manifest


# ---------------------------------------------------------------------------
# repository消费点继承（经真实发布门路径）
# ---------------------------------------------------------------------------


def test_release_gate_requires_diagnostic_for_regex_rule(tmp_path: Path) -> None:
    # 集成：规则入库→_validate_release_shadow_evidence读回三棵树→
    # walker分类（继承注册表）→_assert_release_coverage按分类要求
    # diagnostic_indeterminate。旧行为（HEAD 872a451）对regex触发规则
    # 放行，发布错误只报family项目数，本用例在旧行为下失败。
    repository, lifecycle, shadow, rule, _authority = _ready_shadow(
        tmp_path / "diag-regex.sqlite3"
    )
    assert (
        expression_requires_diagnostic_coverage(
            rule.preconditions, rule.trigger_expression, rule.exclusions
        )
        is True
    )
    _store_boolean_coverage(repository, rule, diagnostic=False)
    run = MonitoringProtocolRuleService(repository).run_shadow_validation(
        rule_pack_id=shadow.rule_pack_id,
        batch_id="diag-regex",
    )
    confirmed = lifecycle.confirm_shadow(
        shadow.rule_pack_id,
        shadow_run_id=run.shadow_run_id,
        confirmed_by="medical_manager",
    )
    with pytest.raises(RulePackLifecycleError, match="diagnostic_indeterminate"):
        lifecycle.publish(
            confirmed.rule_pack_id,
            published_by="medical_manager",
        )


def test_release_gate_publishes_regex_rule_with_diagnostic_evidence(
    tmp_path: Path,
) -> None:
    # 正向对照：同一regex规则具备diagnostic_indeterminate证据后，
    # 新策略不再阻塞发布（发布门继承的是分类，而非无条件要求）。
    repository, lifecycle, shadow, rule, _authority = _ready_shadow(
        tmp_path / "diag-regex-ok.sqlite3"
    )
    _store_p7c_release_evidence(repository, [rule])
    run = MonitoringProtocolRuleService(repository).run_shadow_validation(
        rule_pack_id=shadow.rule_pack_id,
        batch_id="diag-regex-ok",
    )
    confirmed = lifecycle.confirm_shadow(
        shadow.rule_pack_id,
        shadow_run_id=run.shadow_run_id,
        confirmed_by="medical_manager",
    )
    published = lifecycle.publish(
        confirmed.rule_pack_id,
        published_by="medical_manager",
    )
    assert published.status == "published"
