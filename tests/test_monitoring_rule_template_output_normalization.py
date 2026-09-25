"""W04-S2：rule_template_recommendation 生成输出归一的回归。

三类护栏形态 + 审计留痕（20260925 授权，沿用 0923 文档权威裸载荷先例）：
  1. 裸载荷（只有单个候选 payload，无任务信封）→ 服务端补齐信封后通过
     信封校验（生产中 5/5 失败的正是这一层），模型内容原样保留；
  2. 键位漂移（信封顶层非契约键 claims/system_generated_evidence、
     候选级 evidence_ids 放错层、缺 title）→ 归一后通过，动作可查；
  3. 未知漂移形态照旧 fail-closed；
  4. 归一不就地改写调用方持有的原始输出（R24-04 审计合同）。
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from services.api.app.monitoring_ai_contracts import (
    MONITORING_AI_SCHEMA_VERSION,
    MonitoringAiTaskType,
)
from services.api.app.monitoring_ai_service import (
    MonitoringAiService,
    _ProviderOutput,
)

PROJECT_INPUT_REVISION_SHA = "c" * 64


def _job() -> SimpleNamespace:
    return SimpleNamespace(
        job_id="monai_test_normalization",
        task_type=MonitoringAiTaskType.RULE_TEMPLATE_RECOMMENDATION,
        input_revision_sha256=PROJECT_INPUT_REVISION_SHA,
    )


def _bare_payload() -> dict:
    return {
        "fact_type": "visit_window",
        "rule_family": "field_predicate",
        "rationale": "模板忠实实现已确认事实。",
        "tradeoffs": ["以缺失访视名为触发条件。"],
        "deterministic_template": {
            "template_version": "monitoring_rule_template_v2",
            "rule_family": "field_predicate",
            "rule_key": "visit-name-missing",
            "executor": "field_predicate",
            "required_domains": ["SV"],
            "listing_mapping": {
                "fields": {
                    "metadata_visit_name": {"domain": "SV", "field": "VISIT"}
                }
            },
            "preconditions": "TRUE",
            "trigger_expression": "SV.VISIT is empty",
            "exclusions": "NONE",
            "title": "访视名称缺失核查",
            "severity": "high",
            "evidence_template": "SV 记录缺少访视名称。",
        },
        "evidence_ids": ["fact_1", "mapping_2"],
    }


def _template() -> dict:
    return {
        "template_version": "monitoring_rule_template_v2",
        "rule_family": "field_predicate",
        "rule_key": "visit-name-missing",
        "executor": "field_predicate",
        "required_domains": ["SV"],
        "listing_mapping": {
            "fields": {
                "metadata_visit_name": {"domain": "SV", "field": "VISIT"}
            }
        },
        "preconditions": "TRUE",
        "trigger_expression": "SV.VISIT is empty",
        "exclusions": "NONE",
        "title": "访视名称缺失核查",
        "severity": "high",
        "evidence_template": "SV 记录缺少访视名称。",
    }


def _drifted_envelope() -> dict:
    candidate = {
        "candidate_type": "deterministic_rule_template",
        "evidence_ids": ["fact_1", "mapping_2"],
        "structured_payload": {
            "fact_type": "visit_window",
            "rule_family": "field_predicate",
            "rationale": "模板忠实实现已确认事实。",
            "tradeoffs": ["以缺失访视名为触发条件。"],
            "deterministic_template": _template(),
        },
    }
    return {
        "schema_version": MONITORING_AI_SCHEMA_VERSION,
        "task_id": "monai_test_normalization",
        "task_type": "rule_template_recommendation",
        "input_revision_sha256": PROJECT_INPUT_REVISION_SHA,
        "candidates": [candidate],
        "claims": [],
        "system_generated_evidence": [],
    }


def _normalize(output: object, notes: list | None = None) -> object:
    return MonitoringAiService._normalize_rule_template_provider_output(
        _job(),
        output,
        notes,
    )


def test_bare_payload_envelope_completed_and_parses() -> None:
    output = _bare_payload()
    notes: list = []
    normalized = _normalize(output, notes)
    assert normalized["schema_version"] == MONITORING_AI_SCHEMA_VERSION
    assert normalized["task_id"] == "monai_test_normalization"
    assert normalized["task_type"] == "rule_template_recommendation"
    assert normalized["input_revision_sha256"] == PROJECT_INPUT_REVISION_SHA
    candidate = normalized["candidates"][0]
    assert candidate["structured_payload"]["fact_type"] == "visit_window"
    migrated = dict(output["deterministic_template"])
    # R24V2-B04第三类形态迁移（20260926）：触发表达式中缀字符串按受限
    # 文法迁为符号映射（SV.VISIT is empty → missing(反查角色)）。
    migrated["trigger_expression"] = {
        "missing": {"field_role": "metadata_visit_name"}
    }
    assert candidate["structured_payload"]["deterministic_template"] == migrated
    # 信封补齐动作可查。
    migrated_note = {
        "normalization": "expression_string_migrated_to_symbolic_dsl",
        "candidate_index": 0,
        "field": "trigger_expression",
        "form": "domain_field_is_empty",
        "source": "SV.VISIT is empty",
        "role": "metadata_visit_name",
    }
    assert migrated_note in notes
    assert any(
        n.get("normalization") == "bare_payload_envelope_completed" for n in notes
    )
    # 生产中失败的就是这一层校验：归一后必须通过。
    parsed = _ProviderOutput.model_validate(normalized)
    assert parsed.candidates[0].structured_payload["fact_type"] == "visit_window"


def test_key_drift_normalized_with_notes_and_parses() -> None:
    output = _drifted_envelope()
    notes: list = []
    normalized = _normalize(output, notes)
    assert "claims" not in normalized
    assert "system_generated_evidence" not in normalized
    candidate = normalized["candidates"][0]
    assert "evidence_ids" not in candidate
    assert candidate["structured_payload"]["evidence_ids"] == [
        "fact_1",
        "mapping_2",
    ]
    assert candidate["title"] == "访视名称缺失核查"
    kinds = {note["normalization"] for note in notes}
    assert "non_contract_key_stripped" in kinds
    assert "evidence_ids_relocated_into_structured_payload" in kinds
    # 生产中失败的就是这一层校验：归一后必须通过。
    parsed = _ProviderOutput.model_validate(normalized)
    assert (
        parsed.candidates[0].structured_payload["evidence_ids"]
        == ["fact_1", "mapping_2"]
    )


def test_unknown_drift_shape_still_fails_closed() -> None:
    output = {"foo": 1}
    normalized = _normalize(output)
    assert normalized == {"foo": 1}
    with pytest.raises(Exception):
        _ProviderOutput.model_validate(normalized)


def test_normalization_does_not_mutate_caller_output() -> None:
    output = _drifted_envelope()
    before = json_copy(output)
    _normalize(output, None)
    assert json_copy(output) == before
    assert "claims" in output
    assert "evidence_ids" in output["candidates"][0]
    assert "evidence_ids" not in output["candidates"][0]["structured_payload"]


def json_copy(value: object) -> object:
    import json

    return json.loads(json.dumps(value, ensure_ascii=False))


# --- 20260926 第三类漂移：表达式字符串 → 符号算子映射 ---


def _expression_template(preconditions, trigger, exclusions) -> dict:
    template = _template()
    template["preconditions"] = preconditions
    template["trigger_expression"] = trigger
    template["exclusions"] = exclusions
    template["listing_mapping"]["fields"]["subject_id"] = {
        "domain": "SV",
        "field": "SUBJID",
    }
    template["listing_mapping"]["fields"]["cm_start_date"] = {
        "domain": "CM",
        "field": "CMSTDAT",
    }
    template["listing_mapping"]["fields"]["cm_end_date"] = {
        "domain": "CM",
        "field": "CMENDAT",
    }
    return template


def _drifted_with(preconditions, trigger, exclusions) -> dict:
    payload = _bare_payload()
    payload["deterministic_template"] = _expression_template(
        preconditions, trigger, exclusions
    )
    return payload


def _normalize_with(expressions) -> tuple:
    notes: list = []
    output = MonitoringAiService._normalize_rule_template_provider_output(
        _job(), _drifted_with(*expressions), notes
    )
    template = output["candidates"][0]["structured_payload"][
        "deterministic_template"
    ]
    return template, notes


def test_infix_conjunction_migrates_to_all_of_exists():
    template, notes = _normalize_with(
        (
            "cm_start_date IS NOT NULL AND cm_end_date IS NOT NULL",
            "SV.VISIT is empty",
            "NONE",
        )
    )
    assert template["preconditions"] == {
        "all": [
            {"exists": {"field_role": "cm_start_date"}},
            {"exists": {"field_role": "cm_end_date"}},
        ]
    }
    forms = {n.get("form") for n in notes}
    assert {
        "is_not_null_conjunction",
        "domain_field_is_empty",
        "none",
    } <= forms


def test_single_conjunct_migrates_to_exists_without_all():
    template, _ = _normalize_with(
        ("cm_start_date IS NOT NULL", "SV.VISIT is empty", "NONE")
    )
    assert template["preconditions"] == {
        "exists": {"field_role": "cm_start_date"}
    }


def test_true_with_comment_migrates_to_subject_exists():
    template, notes = _normalize_with(
        ("TRUE（对SV域每条记录逐条评估）", "SV.VISIT is empty", "NONE")
    )
    assert template["preconditions"] == {"exists": {"field_role": "subject_id"}}
    assert any(n.get("form") == "true" for n in notes)


def test_none_exclusions_migrates_to_never_true_conjunction():
    template, _ = _normalize_with(
        ("TRUE", "SV.VISIT is empty", "NONE")
    )
    exclusions = template["exclusions"]
    assert exclusions["all"][0] == {"exists": {"field_role": "subject_id"}}
    assert exclusions["all"][1] == {
        "not": {"exists": {"field_role": "subject_id"}}
    }


def test_domain_field_is_empty_migrates_via_reverse_lookup():
    template, _ = _normalize_with(
        ("TRUE", "SV.VISIT is empty", "NONE")
    )
    assert template["trigger_expression"] == {
        "missing": {"field_role": "metadata_visit_name"}
    }


def test_unknown_string_form_stays_fail_closed():
    original = "cm_start_date > 3"
    template, notes = _normalize_with(
        (original, "SV.VISIT is empty", "NONE")
    )
    assert template["preconditions"] == original
    assert not any(
        n.get("field") == "preconditions"
        and n.get("normalization") == "expression_string_migrated_to_symbolic_dsl"
        for n in notes
    )


def test_unknown_role_stays_fail_closed():
    original = "unknown_role_x IS NOT NULL"
    template, _ = _normalize_with(
        (original, "SV.VISIT is empty", "NONE")
    )
    assert template["preconditions"] == original
