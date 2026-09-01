"""Worker_01 contract tests: JSON Schema, field catalog, strict parser,
and Chinese prompt contract for the R3 rule-AI adapter.

These tests prove:
* The schema is JSON Schema 2020-12 compatible, additionalProperties:false at
  every level, and its operator enum matches frozen R3 CONDITION_OPERATORS.
* The field catalog is immutable, dedupes names, and drives operator/value-type
  compatibility.  There is no built-in default catalog; an explicit catalog is
  required everywhere.
* The parser rejects markdown fences, prose, multiple JSON values, non-JSON,
  undeclared keys, unknown fields, invalid operators, type mismatches, bool-as-int,
  non-finite numbers, and missing/empty extracted_from.
* The parser accepts a clean positive candidate and produces a stable hash.
* Open questions block but are not structural failures.
* The prompt contract is vendor-neutral, deterministic, binds schema+catalog,
  and never includes simulation records.
"""

from __future__ import annotations

import json

import pytest

from mm_r3_rule_ai import (
    CATALOG_OPERATORS,
    FieldCatalog,
    FieldSpec,
    ParseStatus,
    RULE_CANDIDATE_SCHEMA,
    SCHEMA_DIALECT,
    ValueType,
    build_prompt,
    parse_rule_candidate,
    prompt_payload_hash,
    schema_content_hash,
)
from fixtures_catalogs import synthetic_catalog


CAT = synthetic_catalog()


def _good_candidate(**overrides) -> str:
    obj = {
        "rule_name": "重度AE标记",
        "conditions": [
            {
                "field": "SYN_AE_SEV",
                "operator": "eq",
                "threshold": "重度",
                "extracted_from": "严重程度为重度",
            }
        ],
        "logical_combination": "all",
        "severity_hint": "serious",
        "domain_hint": "AE",
        "assumptions": [],
        "open_questions": [],
    }
    obj.update(overrides)
    return json.dumps(obj, ensure_ascii=False)


# ===========================================================================
# Schema contract
# ===========================================================================

class TestSchema:
    def test_dialect_is_2020_12(self):
        assert RULE_CANDIDATE_SCHEMA["$schema"] == SCHEMA_DIALECT
        assert SCHEMA_DIALECT == "https://json-schema.org/draft/2020-12/schema"

    def test_top_level_additional_properties_false(self):
        assert RULE_CANDIDATE_SCHEMA["additionalProperties"] is False

    def test_condition_additional_properties_false(self):
        items = RULE_CANDIDATE_SCHEMA["properties"]["conditions"]["items"]
        assert items["additionalProperties"] is False

    def test_operator_enum_matches_catalog(self):
        schema_ops = set(
            RULE_CANDIDATE_SCHEMA["properties"]["conditions"]["items"]
            ["properties"]["operator"]["enum"]
        )
        assert schema_ops == set(CATALOG_OPERATORS)
        assert len(schema_ops) == 11

    def test_required_keys(self):
        required = set(RULE_CANDIDATE_SCHEMA["required"])
        assert required == {
            "rule_name", "conditions", "logical_combination",
            "severity_hint", "domain_hint", "assumptions", "open_questions",
        }

    def test_condition_required_keys(self):
        items = RULE_CANDIDATE_SCHEMA["properties"]["conditions"]["items"]
        assert set(items["required"]) == {"field", "operator", "threshold", "extracted_from"}

    def test_rule_name_max_length_declared(self):
        rn = RULE_CANDIDATE_SCHEMA["properties"]["rule_name"]
        assert rn.get("maxLength") == 200

    def test_schema_hash_stable(self):
        assert schema_content_hash() == schema_content_hash()
        assert len(schema_content_hash()) == 64


# ===========================================================================
# Field catalog
# ===========================================================================

class TestFieldCatalog:
    def test_synthetic_catalog_nonempty(self):
        cat = synthetic_catalog()
        assert len(cat) >= 10
        assert "SYN_AE_SEV" in cat

    def test_catalog_fingerprint_stable(self):
        cat = synthetic_catalog()
        assert cat.fingerprint == synthetic_catalog().fingerprint
        assert len(cat.fingerprint) == 64

    def test_catalog_immutable_lookup(self):
        cat = synthetic_catalog()
        spec = cat.get("SYN_LB_STRESN")
        assert spec is not None
        assert spec.value_type == ValueType.NUMBER

    def test_catalog_rejects_duplicate_names(self):
        with pytest.raises(ValueError, match="duplicate"):
            FieldCatalog((
                FieldSpec("DUP", "AE", "a", "a", ValueType.STRING, ("eq",)),
                FieldSpec("DUP", "AE", "b", "b", ValueType.STRING, ("eq",)),
            ))

    def test_catalog_rejects_unknown_operator(self):
        with pytest.raises(ValueError, match="unknown"):
            FieldSpec("X", "AE", "x", "x", ValueType.STRING, ("bogus_op",))

    def test_catalog_covers_required_domains(self):
        cat = synthetic_catalog()
        domains = cat.domains()
        for required in ("AE", "MH", "CM", "IP", "PD", "IE", "LB"):
            assert required in domains, f"domain {required} missing"

    def test_catalog_has_no_project_names(self):
        """Public business logic must not carry project names or listing table names."""
        cat = synthetic_catalog()
        for spec in cat:
            assert not spec.name.lower().startswith("proj")
            assert "/" not in spec.name
            assert " " not in spec.name

    def test_catalog_names_are_generic_synthetic(self):
        """Field names use generic SYN_ prefixes, not real listing column names."""
        cat = synthetic_catalog()
        for spec in cat:
            assert spec.name.startswith("SYN_"), f"{spec.name} is not a generic synthetic id"


# ===========================================================================
# Parser: positive cases
# ===========================================================================

class TestParserPositive:
    def test_clean_positive(self):
        r = parse_rule_candidate(_good_candidate(), CAT)
        assert r.ok
        assert r.status == ParseStatus.OK
        c = r.candidate
        assert c.rule_name == "重度AE标记"
        assert len(c.conditions) == 1
        assert c.conditions[0].field == "SYN_AE_SEV"

    def test_content_hash_deterministic(self):
        r1 = parse_rule_candidate(_good_candidate(), CAT)
        r2 = parse_rule_candidate(_good_candidate(), CAT)
        assert r1.content_hash == r2.content_hash

    def test_different_rule_different_hash(self):
        r1 = parse_rule_candidate(_good_candidate(), CAT)
        r2 = parse_rule_candidate(_good_candidate(rule_name="别的规则"), CAT)
        assert r1.content_hash != r2.content_hash

    def test_multi_condition_all(self):
        raw = _good_candidate(conditions=[
            {"field": "SYN_AE_SEV", "operator": "eq", "threshold": "重度", "extracted_from": "重度"},
            {"field": "SYN_AE_SER", "operator": "eq", "threshold": "是", "extracted_from": "严重"},
        ])
        r = parse_rule_candidate(raw, CAT)
        assert r.ok
        assert len(r.candidate.conditions) == 2

    def test_multi_condition_any(self):
        raw = _good_candidate(
            logical_combination="any",
            conditions=[
                {"field": "SYN_AE_SEV", "operator": "eq", "threshold": "重度", "extracted_from": "重度"},
                {"field": "SYN_AE_OUT", "operator": "eq", "threshold": "致死", "extracted_from": "致死"},
            ],
        )
        r = parse_rule_candidate(raw, CAT)
        assert r.ok

    def test_in_operator_string_list(self):
        raw = _good_candidate(conditions=[
            {"field": "SYN_AE_SEV", "operator": "in", "threshold": ["重度", "中度"],
             "extracted_from": "严重程度"},
        ])
        r = parse_rule_candidate(raw, CAT)
        assert r.ok

    def test_is_missing_operator(self):
        raw = _good_candidate(conditions=[
            {"field": "SYN_AE_SEV", "operator": "is_missing", "threshold": None,
             "extracted_from": "缺失"},
        ])
        r = parse_rule_candidate(raw, CAT)
        assert r.ok

    def test_optional_hints_empty_string(self):
        raw = _good_candidate(severity_hint="", domain_hint="")
        r = parse_rule_candidate(raw, CAT)
        assert r.ok
        assert r.candidate.severity_hint == ""


# ===========================================================================
# Parser: blocking structural failures
# ===========================================================================

class TestParserStructuralFailures:
    def test_empty_output(self):
        r = parse_rule_candidate("", CAT)
        assert r.status == ParseStatus.EMPTY_OUTPUT
        assert r.blocked
        assert r.candidate is None

    def test_whitespace_only(self):
        r = parse_rule_candidate("   \n  ", CAT)
        assert r.status == ParseStatus.EMPTY_OUTPUT

    def test_markdown_fence_rejected(self):
        raw = "```json\n" + _good_candidate() + "\n```"
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.MARKDOWN_FENCE
        assert r.blocked

    def test_prose_wrapped_rejected(self):
        raw = "这是结果：" + _good_candidate() + " 谢谢"
        r = parse_rule_candidate(raw, CAT)
        assert r.status in (ParseStatus.NOT_JSON, ParseStatus.MULTIPLE_JSON_VALUES)
        assert r.blocked

    def test_multiple_json_values_rejected(self):
        raw = _good_candidate() + "\n" + _good_candidate()
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.MULTIPLE_JSON_VALUES

    def test_not_json(self):
        r = parse_rule_candidate("{not valid json", CAT)
        assert r.status == ParseStatus.NOT_JSON
        assert r.blocked

    def test_not_single_object_array(self):
        r = parse_rule_candidate("[]", CAT)
        assert r.status == ParseStatus.NOT_SINGLE_OBJECT
        assert r.blocked

    def test_not_single_object_string(self):
        r = parse_rule_candidate('"hello"', CAT)
        assert r.status == ParseStatus.NOT_SINGLE_OBJECT

    def test_not_single_object_number(self):
        r = parse_rule_candidate("42", CAT)
        assert r.status == ParseStatus.NOT_SINGLE_OBJECT


# ===========================================================================
# Parser: schema-level violations
# ===========================================================================

class TestParserSchemaViolations:
    def test_unknown_top_key_rejected(self):
        raw = json.loads(_good_candidate())
        raw["extra_key"] = "bad"
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.UNKNOWN_FIELD
        assert r.blocked

    def test_missing_required_top_key(self):
        raw = json.loads(_good_candidate())
        del raw["logical_combination"]
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.SCHEMA_VIOLATION
        assert r.blocked

    def test_unknown_condition_key_rejected(self):
        raw = json.loads(_good_candidate())
        raw["conditions"][0]["extra"] = "bad"
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.UNKNOWN_FIELD

    def test_empty_conditions_rejected(self):
        raw = json.loads(_good_candidate())
        raw["conditions"] = []
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.EMPTY_CONDITIONS

    def test_invalid_logical_combination(self):
        raw = json.loads(_good_candidate())
        raw["logical_combination"] = "xor"
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.INVALID_LOGICAL_COMBINATION

    def test_invalid_severity_hint(self):
        raw = json.loads(_good_candidate())
        raw["severity_hint"] = "super_critical"
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.SCHEMA_VIOLATION

    def test_invalid_domain_hint(self):
        raw = json.loads(_good_candidate())
        raw["domain_hint"] = "XX"
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.SCHEMA_VIOLATION

    def test_missing_extracted_from(self):
        raw = json.loads(_good_candidate())
        del raw["conditions"][0]["extracted_from"]
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.SCHEMA_VIOLATION

    def test_empty_extracted_from(self):
        raw = json.loads(_good_candidate())
        raw["conditions"][0]["extracted_from"] = "  "
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.EMPTY_EXTRACTED_FROM


# ===========================================================================
# Parser: catalog binding / operator / type compatibility
# ===========================================================================

class TestParserCatalogBinding:
    def test_unknown_field_rejected(self):
        raw = json.loads(_good_candidate())
        raw["conditions"][0]["field"] = "AEDECOD"  # not in catalog
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.FIELD_NOT_IN_CATALOG
        assert r.blocked

    def test_invented_field_rejected(self):
        raw = json.loads(_good_candidate())
        raw["conditions"][0]["field"] = "FAKE_FIELD"
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.FIELD_NOT_IN_CATALOG

    def test_invalid_operator_rejected(self):
        raw = json.loads(_good_candidate())
        raw["conditions"][0]["operator"] = "approximately"
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.INVALID_OPERATOR

    def test_operator_not_allowed_for_field(self):
        # SYN_AE_SEV is coded (eq/ne/contains/in/not_in/is_missing/is_present);
        # 'gt' is not allowed for a coded string field.
        raw = json.loads(_good_candidate())
        raw["conditions"][0]["operator"] = "gt"
        raw["conditions"][0]["threshold"] = 3
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.OPERATOR_NOT_ALLOWED_FOR_FIELD

    def test_threshold_type_mismatch_number_field_string_value(self):
        raw = json.dumps({
            "rule_name": "实验室规则",
            "conditions": [{
                "field": "SYN_LB_STRESN", "operator": "gt", "threshold": "不是数字",
                "extracted_from": "实验室值升高",
            }],
            "logical_combination": "all", "severity_hint": "warning", "domain_hint": "LB",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.THRESHOLD_TYPE_MISMATCH

    def test_threshold_bool_as_int_rejected(self):
        raw = json.dumps({
            "rule_name": "布尔规则",
            "conditions": [{
                "field": "SYN_LB_STRESN", "operator": "eq", "threshold": True,
                "extracted_from": "实验室值",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "LB",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.BOOL_AS_INT

    def test_threshold_non_finite_rejected(self):
        raw = json.dumps({
            "rule_name": "无穷规则",
            "conditions": [{
                "field": "SYN_LB_STRESN", "operator": "gt", "threshold": 1e999,
                "extracted_from": "实验室值",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "LB",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.NON_FINITE_NUMBER

    def test_is_missing_with_threshold_rejected(self):
        raw = json.dumps({
            "rule_name": "缺失规则",
            "conditions": [{
                "field": "SYN_AE_SEV", "operator": "is_missing", "threshold": "重度",
                "extracted_from": "缺失",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "AE",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.THRESHOLD_TYPE_MISMATCH

    def test_in_operator_requires_list(self):
        raw = json.dumps({
            "rule_name": "列表规则",
            "conditions": [{
                "field": "SYN_AE_SEV", "operator": "in", "threshold": "重度",
                "extracted_from": "严重程度",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "AE",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.THRESHOLD_TYPE_MISMATCH

    def test_in_operator_number_list_for_number_field(self):
        raw = json.dumps({
            "rule_name": "数值列表规则",
            "conditions": [{
                "field": "SYN_LB_STRESN", "operator": "in", "threshold": [1.5, 2.0],
                "extracted_from": "实验室值",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "LB",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.ok


# ===========================================================================
# Parser: open questions block
# ===========================================================================

class TestParserOpenQuestions:
    def test_open_questions_block(self):
        raw = json.loads(_good_candidate())
        raw["open_questions"] = ["剂量单位不明确"]
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.status == ParseStatus.BLOCKED_OPEN_QUESTIONS
        assert r.blocked
        assert r.candidate is not None  # candidate still present for audit

    def test_assumptions_alone_do_not_block_parse(self):
        raw = json.loads(_good_candidate())
        raw["assumptions"] = ["假设严重程度字段为重度"]
        r = parse_rule_candidate(json.dumps(raw, ensure_ascii=False), CAT)
        assert r.ok


# ===========================================================================
# Prompt contract (requires explicit catalog)
# ===========================================================================

class TestPromptContract:
    def test_build_prompt_basic(self):
        p = build_prompt("标记所有严重程度为重度的不良事件", CAT)
        assert p.system_prompt
        assert p.user_prompt
        assert "标记所有严重程度为重度的不良事件" in p.user_prompt
        assert p.schema_hash == schema_content_hash()
        assert p.catalog_fingerprint == CAT.fingerprint
    def test_prompt_requires_catalog(self):
        with pytest.raises(TypeError):
            build_prompt("规则")  # type: ignore[call-arg]

    def test_different_rule_different_prompt(self):
        p1 = build_prompt("规则甲", CAT)
        p2 = build_prompt("规则乙", CAT)
        assert prompt_payload_hash(p1) != prompt_payload_hash(p2)

    def test_prompt_contains_catalog_block(self):
        p = build_prompt("测试规则", CAT)
        assert "SYN_AE_SEV" in p.user_prompt
        assert "可用字段目录" in p.user_prompt

    def test_prompt_contains_schema_json(self):
        p = build_prompt("测试规则", CAT)
        assert "RuleCandidate" in p.user_prompt
        assert "additionalProperties" in p.user_prompt

    def test_prompt_is_vendor_neutral(self):
        """No provider/model/api/project identifiers in the prompt."""
        p = build_prompt("测试规则", CAT, business_context="某试验")
        full = p.system_prompt + p.user_prompt
        for forbidden in ("openai", "anthropic", "claude", "gpt", "/api/", "/Users/", ".py"):
            assert forbidden.lower() not in full.lower(), f"found {forbidden!r}"

    def test_prompt_never_includes_simulation_records(self):
        p = build_prompt("测试规则", CAT)
        assert "_record_id" not in p.user_prompt
        assert "simulate" not in p.user_prompt.lower()

    def test_prompt_rejects_empty_rule(self):
        with pytest.raises(ValueError):
            build_prompt("", CAT)

    def test_prompt_rejects_non_string_context(self):
        with pytest.raises(ValueError):
            build_prompt("规则", CAT, business_context=123)  # type: ignore[arg-type]


# ===========================================================================
# Determinism / cross-parse stability
# ===========================================================================

class TestDeterminism:
    def test_same_input_same_result(self):
        raw = _good_candidate()
        r1 = parse_rule_candidate(raw, CAT)
        r2 = parse_rule_candidate(raw, CAT)
        assert r1.status == r2.status
        assert r1.content_hash == r2.content_hash
        assert r1.catalog_fingerprint == r2.catalog_fingerprint

    def test_catalog_fingerprint_bound_to_result(self):
        r = parse_rule_candidate(_good_candidate(), CAT)
        assert r.catalog_fingerprint == CAT.fingerprint

    def test_custom_catalog_changes_fingerprint(self):
        spec = FieldSpec("CUSTOM1", "AE", "自定义", "自定义字段", ValueType.STRING, ("eq",))
        cat = FieldCatalog((spec,))
        raw = json.dumps({
            "rule_name": "自定义",
            "conditions": [{
                "field": "CUSTOM1", "operator": "eq", "threshold": "x",
                "extracted_from": "原文",
            }],
            "logical_combination": "all",
            "severity_hint": "", "domain_hint": "AE",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, cat)
        assert r.ok
        assert r.catalog_fingerprint == cat.fingerprint
        assert r.catalog_fingerprint != CAT.fingerprint


# ===========================================================================
# Remediation: duplicate keys, deep-freeze, schema-derived, maxLength
# ===========================================================================

class TestRemediation:
    def test_duplicate_top_key_rejected(self):
        raw = '{"rule_name":"A","rule_name":"B","conditions":[],"logical_combination":"all","severity_hint":"","domain_hint":"","assumptions":[],"open_questions":[]}'
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.DUPLICATE_KEY
        assert r.blocked

    def test_duplicate_condition_key_rejected(self):
        raw = '{"rule_name":"规则","conditions":[{"field":"SYN_AE_SEV","field":"SYN_AE_OUT","operator":"eq","threshold":"重度","extracted_from":"原文"}],"logical_combination":"all","severity_hint":"","domain_hint":"","assumptions":[],"open_questions":[]}'
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.DUPLICATE_KEY

    def test_threshold_list_deep_frozen(self):
        raw = json.dumps({
            "rule_name": "列表规则",
            "conditions": [{
                "field": "SYN_AE_SEV", "operator": "in",
                "threshold": ["重度", "中度"],
                "extracted_from": "原文",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "AE",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.ok
        thresh = r.candidate.conditions[0].threshold
        # deep-frozen: list becomes a tuple
        assert isinstance(thresh, tuple)
        assert thresh == ("重度", "中度")

    def test_rule_name_max_length_enforced(self):
        long_name = "规则" * 200  # 400 chars, exceeds maxLength=200
        raw = json.dumps({
            "rule_name": long_name,
            "conditions": [{
                "field": "SYN_AE_SEV", "operator": "eq", "threshold": "重度",
                "extracted_from": "原文",
            }],
            "logical_combination": "all", "severity_hint": "", "domain_hint": "AE",
            "assumptions": [], "open_questions": [],
        }, ensure_ascii=False)
        r = parse_rule_candidate(raw, CAT)
        assert r.status == ParseStatus.SCHEMA_VIOLATION
        assert "maxLength" in r.errors[0]

    def test_schema_derived_enums_match(self):
        from mm_r3_rule_ai.parser import _schema_enum
        assert _schema_enum("logical_combination") == ("all", "any")
        assert "" in _schema_enum("severity_hint")
        assert "AE" in _schema_enum("domain_hint")

    def test_no_default_catalog_in_production(self):
        """The production package must not export a built-in default catalog."""
        import mm_r3_rule_ai
        assert not hasattr(mm_r3_rule_ai, "default_catalog")
        assert not hasattr(mm_r3_rule_ai, "DEFAULT_CATALOG")
