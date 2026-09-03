"""Deterministic relationship-profiler tests with synthetic rows only.

The profiler is verified against the bridge gate contract
(``relationship_profile_gate``) so evidence that reaches the mapping input
is exactly what the fail-closed gate accepts.
"""

from __future__ import annotations

import json

import pytest

from packages.medical_monitoring.admission.relationship_profile_gate import (
    validate_relationship_profile,
)
from packages.medical_monitoring.admission.relationship_profiler import (
    MAX_CROSS_TABLE_ITEMS,
    MAX_PAIRS_PER_TABLE,
    MAX_SAMPLE_ROWS,
    RELATIONSHIP_PROFILER_CONTRACT,
    build_relationship_profile,
)

_BINDING = "a" * 64


def _build(
    rows_by_domain: dict,
    table_field_order: dict,
    binding: str = _BINDING,
) -> dict:
    return build_relationship_profile(
        rows_by_domain=rows_by_domain,
        table_field_order=table_field_order,
        input_binding_sha256=binding,
    )


def _pair(payload: dict, left_field: str, right_field: str) -> dict:
    return next(
        item
        for item in payload["same_table"]
        if item["left_field"] == left_field
        and item["right_field"] == right_field
    )


def test_term_code_pair_evidence_counts_cardinality_and_overlap() -> None:
    rows = [
        {"AETERM": "headache", "AETERMCD": "1", "NOTE": "x"},
        {"AETERM": "headache", "AETERMCD": "1", "NOTE": "y"},
        {"AETERM": "fever", "AETERMCD": "1", "NOTE": "x"},
        {"AETERM": "fever", "AETERMCD": "", "NOTE": "z"},
        {"AETERM": "", "AETERMCD": "3", "NOTE": "x"},
    ]
    payload = _build(
        {"ae": rows},
        {"ae": ["AETERM", "AETERMCD", "NOTE"]},
    )
    assert payload["schema_version"] == (
        "mm-c3-admission-relationship-profile-v1"
    )
    assert payload["profiler_contract"] == RELATIONSHIP_PROFILER_CONTRACT
    assert payload["input_binding_sha256"] == _BINDING
    pair = _pair(payload, "AETERM", "AETERMCD")
    assert pair["relationship_type"] == "term_code_pair"
    assert pair["total_rows"] == 5
    assert pair["jointly_non_empty_count"] == 3
    assert pair["left_only_count"] == 1
    assert pair["right_only_count"] == 1
    assert pair["unique_pair_count"] == 2
    assert pair["left_values_with_multiple_right"] == 0
    assert pair["right_values_with_multiple_left"] == 1
    assert pair["value_overlap"] == {
        "shared_distinct_count": 0,
        "overlap_rate": 0.0,
    }
    assert any(item["relationship_type"] == "statistical_pair" for item in payload["same_table"])


def test_value_unit_pair_requires_numeric_base_field() -> None:
    rows = [
        {"DOSE": "5", "DOSEUNIT": "mg", "NOTE": "x"},
        {"DOSE": "10", "DOSEUNIT": "mg", "NOTE": "y"},
        {"DOSE": "", "DOSEUNIT": "ml", "NOTE": "z"},
    ]
    payload = _build(
        {"dosing": rows},
        {"dosing": ["DOSE", "DOSEUNIT", "NOTE"]},
    )
    unit_pair = _pair(payload, "DOSE", "DOSEUNIT")
    assert unit_pair["relationship_type"] == "value_unit_pair"
    assert unit_pair["jointly_non_empty_count"] == 2
    assert unit_pair["right_only_count"] == 1
    negative = _build(
        {"notes": [{"NOTE": "x", "NOTEUNIT": "u"}]},
        {"notes": ["NOTE", "NOTEUNIT"]},
    )
    assert _pair(negative, "NOTE", "NOTEUNIT")["relationship_type"] == "statistical_pair"


def test_performed_reason_pair_is_derived_from_suffix_morphology() -> None:
    rows = [
        {"AEPERF": "Y", "AEREASND": "", "NOTE": "x"},
        {"AEPERF": "N", "AEREASND": "not done", "NOTE": "y"},
    ]
    payload = _build(
        {"ae": rows},
        {"ae": ["AEPERF", "AEREASND", "NOTE"]},
    )
    pair = _pair(payload, "AEPERF", "AEREASND")
    assert pair["relationship_type"] == "performed_reason_pair"
    assert pair["jointly_non_empty_count"] == 1
    assert pair["left_only_count"] == 1
    assert pair["right_only_count"] == 0


def test_unfamiliar_fields_receive_neutral_evidence_and_empty_tables_do_not() -> None:
    rows = [
        {"SUBJID": "S1", "VISIT": "V1", "VSDAT": "2026-01-01"},
        {"SUBJID": "S2", "VISIT": "V2", "VSDAT": "2026-01-02"},
    ]
    payload = _build(
        {"vitals": rows, "empty": []},
        {"vitals": ["SUBJID", "VISIT", "VSDAT"], "empty": ["X", "Y"]},
    )
    assert len(payload["same_table"]) == 3
    assert {item["relationship_type"] for item in payload["same_table"]} == {
        "statistical_pair"
    }
    assert payload["cross_table"] == []
    normalized = validate_relationship_profile(
        payload,
        fields_by_domain={
            "vitals": {"SUBJID", "VISIT", "VSDAT"},
            "empty": {"X", "Y"},
        },
        rows_by_domain={"vitals": rows, "empty": []},
        input_binding_sha256=_BINDING,
    )
    assert normalized["same_table"] == payload["same_table"]
    assert normalized["cross_table"] == []


def test_chinese_fields_and_column_reordering_keep_neutral_evidence() -> None:
    rows = [
        {"受试者号": "S1", "访视": "V1", "结果": "10", "正常上限": "8"},
        {"受试者号": "S2", "访视": "V2", "结果": "7", "正常上限": "8"},
    ]
    first = _build(
        {"检查": rows},
        {"检查": ["受试者号", "访视", "结果", "正常上限"]},
    )
    second = _build(
        {"检查": rows},
        {"检查": ["正常上限", "结果", "访视", "受试者号"]},
    )
    assert first["same_table"] == second["same_table"]
    assert len(first["same_table"]) == 6
    assert {item["relationship_type"] for item in first["same_table"]} == {
        "statistical_pair"
    }


def test_wide_table_pair_budget_is_enforced() -> None:
    fields = [f"FIELD_{index:03d}" for index in range(40)]
    payload = _build(
        {"wide": [{field: index for index, field in enumerate(fields)}]},
        {"wide": fields},
    )
    assert len(payload["same_table"]) == MAX_PAIRS_PER_TABLE


def test_cross_table_shared_field_coverage_and_row_match_rate() -> None:
    exam_rows = [
        {"SUBJID": "E1", "NOTE": "a"},
        {"SUBJID": "E2", "NOTE": "b"},
        {"SUBJID": "E3", "NOTE": "c"},
        {"SUBJID": "E4", "NOTE": "d"},
    ]
    lab_rows = [
        {"SUBJID": "E1", "NOTE": "a"},
        {"SUBJID": "E2", "NOTE": "b"},
        {"SUBJID": "E3", "NOTE": "c"},
        {"SUBJID": "E5", "NOTE": "e"},
    ]
    payload = _build(
        {"exam": exam_rows, "lab": lab_rows},
        {"exam": ["SUBJID", "NOTE"], "lab": ["SUBJID", "NOTE"]},
    )
    shared = next(
        item for item in payload["cross_table"]
        if item["left_field"] == "SUBJID"
    )
    assert shared["left_domain"] == "exam"
    assert shared["right_domain"] == "lab"
    assert shared["shared_value_count"] == 3
    assert shared["coverage_left"] == 0.75
    assert shared["coverage_right"] == 0.75
    assert shared["match_rate"] == 0.75


def test_total_rows_echo_frozen_count_while_statistics_use_the_sample() -> None:
    rows = [
        {"AETERM": f"term-{index}", "AETERMCD": str(index % 7)}
        for index in range(1500)
    ]
    payload = _build(
        {"ae": rows},
        {"ae": ["AETERM", "AETERMCD"]},
    )
    pair = _pair(payload, "AETERM", "AETERMCD")
    assert pair["total_rows"] == 1500
    evidence_rows = (
        pair["jointly_non_empty_count"]
        + pair["left_only_count"]
        + pair["right_only_count"]
    )
    assert evidence_rows <= MAX_SAMPLE_ROWS
    assert pair["jointly_non_empty_count"] == MAX_SAMPLE_ROWS
    assert pair["sampled_row_count"] == MAX_SAMPLE_ROWS
    assert pair["unique_pair_count"] <= pair["jointly_non_empty_count"]


def test_payload_is_deterministic_gate_clean_and_value_free() -> None:
    rows = {
        "ae": [
            {"AETERM": "headache", "AETERMCD": "1"},
            {"AETERM": "fever", "AETERMCD": "2"},
        ],
        "lab": [{"SUBJID": "E1", "LBORRESU": "mmol/L"}],
    }
    order = {"ae": ["AETERM", "AETERMCD"], "lab": ["SUBJID", "LBORRESU"]}
    first = _build(rows, order)
    second = _build(rows, order)
    assert first == second
    normalized = validate_relationship_profile(
        first,
        fields_by_domain={
            "ae": {"AETERM", "AETERMCD"},
            "lab": {"SUBJID", "LBORRESU"},
        },
        rows_by_domain=rows,
        input_binding_sha256=_BINDING,
    )
    assert normalized["profiler_contract"] == RELATIONSHIP_PROFILER_CONTRACT
    dumped = json.dumps(first, ensure_ascii=False, default=str)
    for raw_value in ("headache", "fever", "mmol/L", "E1"):
        assert raw_value not in dumped


def test_tampered_binding_digest_is_refused_by_the_gate() -> None:
    payload = _build(
        {"ae": [{"AETERM": "x", "AETERMCD": "1"}]},
        {"ae": ["AETERM", "AETERMCD"]},
    )
    with pytest.raises(Exception, match="binding_mismatch"):
        validate_relationship_profile(
            payload,
            fields_by_domain={"ae": {"AETERM", "AETERMCD"}},
            rows_by_domain={"ae": [{"AETERM": "x", "AETERMCD": "1"}]},
            input_binding_sha256="b" * 64,
        )


def test_over_long_field_names_are_skipped_without_failure() -> None:
    long_name = "L" * 200 + "CD"
    rows = [{"AETERM": "x", long_name: "1"}]
    payload = _build(
        {"ae": rows},
        {"ae": ["AETERM", long_name]},
    )
    assert payload["same_table"] == []
    normalized = validate_relationship_profile(
        payload,
        fields_by_domain={"ae": {"AETERM", long_name}},
        rows_by_domain=rows,
        input_binding_sha256=_BINDING,
    )
    assert normalized["same_table"] == []


def test_cross_table_entry_budget_stops_deterministically() -> None:
    table_count = 24
    rows_by_domain = {}
    table_field_order = {}
    for index in range(table_count):
        domain = f"t{index:02d}"
        rows_by_domain[domain] = [{"SHARED": f"{domain}-value"}]
        table_field_order[domain] = ["SHARED"]
    payload = _build(rows_by_domain, table_field_order)
    assert len(payload["cross_table"]) == MAX_CROSS_TABLE_ITEMS
    keys = {
        (
            item["left_domain"],
            item["right_domain"],
        )
        for item in payload["cross_table"]
    }
    assert len(keys) == MAX_CROSS_TABLE_ITEMS


def test_gate_rejects_counts_inconsistent_with_frozen_rows() -> None:
    payload = _build(
        {"ae": [{"AETERM": "x", "AETERMCD": "1"}]},
        {"ae": ["AETERM", "AETERMCD"]},
    )
    tampered = dict(payload)
    tampered["same_table"] = [
        dict(payload["same_table"][0], total_rows=99)
    ]
    with pytest.raises(Exception, match="row_binding_mismatch"):
        validate_relationship_profile(
            tampered,
            fields_by_domain={"ae": {"AETERM", "AETERMCD"}},
            rows_by_domain={"ae": [{"AETERM": "x", "AETERMCD": "1"}]},
            input_binding_sha256=_BINDING,
        )
