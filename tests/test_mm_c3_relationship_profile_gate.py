"""Fail-closed contract tests for the C3 relationship profile gate.

The gate is the only path relationship evidence may take into the mapping
bridge. These tests use synthetic rows only — no real project, service or
model — and pin the structural rules: binding to the exact frozen rows,
whitelisted keys, harness-legal same-table types, consistent counts and the
mapping-stage conclusion ban.
"""

from __future__ import annotations

import copy

import pytest

from packages.medical_monitoring.admission.relationship_profile_gate import (
    RELATIONSHIP_PROFILE_SCHEMA_VERSION,
    RelationshipProfileGateError,
    relationship_input_binding_sha256,
    relationship_rows_by_domain,
    same_table_relationship_entries,
    validate_relationship_profile,
)
from tests.medical_monitoring.relationship_profiler_stub import (
    build_relationship_profile as _stub_profiler,
)


FIELDS_BY_DOMAIN = {
    "表A": {"受试者标识", "结果", "单位"},
    "表B": {"受试者标识", "访视"},
}
ROWS_BY_DOMAIN = {
    "表A": [
        {"受试者标识": "S1", "结果": "10", "单位": "mg"},
        {"受试者标识": "S2", "结果": "12", "单位": "mg"},
    ],
    "表B": [
        {"受试者标识": "S1", "访视": "V1"},
        {"受试者标识": "S2", "访视": "V2"},
    ],
}


def _binding() -> str:
    return relationship_input_binding_sha256({
        "snap-1": ROWS_BY_DOMAIN,
    })


def _payload(**kwargs) -> dict:
    rows = kwargs.pop("rows_by_domain", ROWS_BY_DOMAIN)
    order = kwargs.pop(
        "table_field_order",
        {domain: sorted(fields) for domain, fields in FIELDS_BY_DOMAIN.items()},
    )
    kwargs.setdefault("input_binding_sha256", _binding())
    return _stub_profiler(
        rows_by_domain=rows,
        table_field_order=order,
        **kwargs,
    )


def _validate(payload):
    return validate_relationship_profile(
        payload,
        fields_by_domain=FIELDS_BY_DOMAIN,
        rows_by_domain=ROWS_BY_DOMAIN,
        input_binding_sha256=_binding(),
    )


def test_valid_payload_passes_and_normalizes() -> None:
    normalized = _validate(_payload())
    assert normalized["schema_version"] == RELATIONSHIP_PROFILE_SCHEMA_VERSION
    assert normalized["profiler_contract"] == "tests.stub-relationship-profiler-v1"
    assert normalized["input_binding_sha256"] == _binding()
    entries = same_table_relationship_entries(normalized)
    assert entries
    assert all(entry["jointly_non_empty_count"] >= 1 for entry in entries)
    # Mutating the normalized copy must not corrupt the source payload.
    entries[0]["jointly_non_empty_count"] = -5
    assert _payload()["same_table"][0]["jointly_non_empty_count"] >= 0


def test_binding_digest_is_deterministic_and_row_sensitive() -> None:
    first = relationship_input_binding_sha256({"snap-1": ROWS_BY_DOMAIN})
    second = relationship_input_binding_sha256({"snap-1": ROWS_BY_DOMAIN})
    assert first == second
    mutated = copy.deepcopy(ROWS_BY_DOMAIN)
    mutated["表A"][0]["结果"] = "99"
    assert relationship_input_binding_sha256(
        {"snap-1": mutated}
    ) != first


def test_rows_by_domain_follows_table_bindings() -> None:
    rows = relationship_rows_by_domain(
        [
            {"domain": "表B", "snapshot_id": "snap-2"},
            {"domain": "表A", "snapshot_id": "snap-1"},
        ],
        {
            "snap-1": ROWS_BY_DOMAIN,
            "snap-2": ROWS_BY_DOMAIN,
        },
    )
    assert list(rows) == ["表B", "表A"]
    assert rows["表A"] == ROWS_BY_DOMAIN["表A"]


def test_binding_mismatch_is_refused() -> None:
    payload = _payload()
    payload["input_binding_sha256"] = "0" * 64
    with pytest.raises(RelationshipProfileGateError) as exc_info:
        _validate(payload)
    assert exc_info.value.code == "relationship_profile_binding_mismatch"


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda p: p.pop("cross_table"), "relationship_profile_malformed"),
        (
            lambda p: p.update(unexpected="x"),
            "relationship_profile_key_invalid",
        ),
        (
            lambda p: p.update(schema_version="mm-c3-admission-relationship-profile-v0"),
            "relationship_profile_schema_version_invalid",
        ),
        (
            lambda p: p.update(profiler_contract="Bad Contract"),
            "relationship_profile_profiler_contract_invalid",
        ),
        (
            lambda p: p.update(input_binding_sha256="nothex"),
            "relationship_profile_binding_digest_malformed",
        ),
        (
            lambda p: p.update(same_table="x"),
            "relationship_profile_malformed",
        ),
    ],
)
def test_payload_level_violations_are_refused(mutate, code) -> None:
    payload = _payload()
    mutate(payload)
    with pytest.raises(RelationshipProfileGateError) as exc_info:
        _validate(payload)
    assert exc_info.value.code == code


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (
            lambda item: item.update(left_field="不存在"),
            "relationship_profile_unknown_field",
        ),
        (
            lambda item: item.update(domain="表B", left_field="结果"),
            "relationship_profile_unknown_field",
        ),
        (
            lambda item: item.update(right_field=item["left_field"]),
            "relationship_profile_pair_degenerate",
        ),
        (
            lambda item: item.update(relationship_type="made_up_pair"),
            "relationship_profile_type_invalid",
        ),
        (
            lambda item: item.update(total_rows=999),
            "relationship_profile_row_binding_mismatch",
        ),
        (
            lambda item: item.update(jointly_non_empty_count=-1),
            "relationship_profile_count_invalid",
        ),
        (
            lambda item: item.update(
                jointly_non_empty_count=99,
                unique_pair_count=1,
            ),
            "relationship_profile_counts_inconsistent",
        ),
        (
            lambda item: item.update(sampled_row_count=1),
            "relationship_profile_counts_inconsistent",
        ),
        (
            lambda item: item.update(unexpected_key=1),
            "relationship_profile_same_table_key_invalid",
        ),
        (
            lambda item: item.update(
                value_overlap={"shared_distinct_count": 1, "bogus": 0.5}
            ),
            "relationship_profile_value_overlap_key_invalid",
        ),
        (
            lambda item: item.update(
                value_overlap={"shared_distinct_count": 1, "overlap_rate": 1.5}
            ),
            "relationship_profile_rate_invalid",
        ),
        (
            lambda item: item.update(ctcae_grade=3),
            "relationship_profile_conclusion_key",
        ),
    ],
)
def test_same_table_violations_are_refused(mutate, code) -> None:
    payload = _payload()
    assert payload["same_table"]
    mutate(payload["same_table"][0])
    with pytest.raises(RelationshipProfileGateError) as exc_info:
        _validate(payload)
    assert exc_info.value.code == code


def test_cross_table_violations_are_refused() -> None:
    payload = _payload()
    entry = dict(payload["cross_table"][0])
    entry["right_domain"] = entry["left_domain"]
    payload["cross_table"] = [entry]
    with pytest.raises(RelationshipProfileGateError) as exc_info:
        _validate(payload)
    assert exc_info.value.code == "relationship_profile_cross_table_same_domain"

    payload = _payload()
    payload["cross_table"][0]["match_rate"] = -0.1
    with pytest.raises(RelationshipProfileGateError) as exc_info:
        _validate(payload)
    assert exc_info.value.code == "relationship_profile_rate_invalid"

    payload = _payload()
    payload["cross_table"][0]["left_sampled_row_count"] = 999
    with pytest.raises(RelationshipProfileGateError) as exc_info:
        _validate(payload)
    assert exc_info.value.code == "relationship_profile_counts_inconsistent"

    payload = _payload()
    payload["cross_table"] = [payload["cross_table"][0], dict(payload["cross_table"][0])]
    with pytest.raises(RelationshipProfileGateError) as exc_info:
        _validate(payload)
    assert exc_info.value.code == "relationship_profile_duplicate"


def test_oversized_evidence_is_refused() -> None:
    from packages.medical_monitoring.admission.relationship_profile_gate import (
        MAX_SAME_TABLE_RELATIONSHIP_ITEMS,
    )

    payload = _payload()
    payload["same_table"] = [dict(payload["same_table"][0])] * (
        MAX_SAME_TABLE_RELATIONSHIP_ITEMS + 1
    )
    with pytest.raises(RelationshipProfileGateError) as exc_info:
        _validate(payload)
    assert exc_info.value.code == "relationship_profile_same_table_too_large"


def test_non_json_rows_cannot_bind() -> None:
    with pytest.raises(RelationshipProfileGateError) as exc_info:
        relationship_input_binding_sha256(
            {"snap-1": {"表A": [{"x": object()}]}}
        )
    assert (
        exc_info.value.code == "relationship_input_rows_not_canonicalizable"
    )
