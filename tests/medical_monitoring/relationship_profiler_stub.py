"""Deterministic contract-conformant relationship profiler stub for tests.

This double satisfies the bridge contract documented in
``packages/medical_monitoring.admission.relationship_profile_gate``: pure,
stdlib-only, no field-name hardcoding beyond generic structural pairing, and
honest counts over the exact frozen rows it receives. It exists so bridge,
pipeline and dual-cohort tests can exercise the evidence path before the
production profiler lands; it is not the production implementation.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from packages.medical_monitoring.admission.relationship_profile_gate import (
    RELATIONSHIP_PROFILE_SCHEMA_VERSION,
)

PROFILER_CONTRACT = "tests.stub-relationship-profiler-v1"

# Bounded complexity mirrors the production contract bounds.
_MAX_PAIRS_PER_DOMAIN = 40


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _pair_counts(
    rows: Sequence[Mapping[str, Any]],
    left_field: str,
    right_field: str,
) -> dict[str, int] | None:
    jointly = 0
    left_only = 0
    right_only = 0
    pairs: set[tuple[str, str]] = set()
    right_by_left: dict[str, set[str]] = {}
    left_by_right: dict[str, set[str]] = {}
    for row in rows:
        left = _clean(row.get(left_field))
        right = _clean(row.get(right_field))
        if left and right:
            jointly += 1
            pairs.add((left, right))
            right_by_left.setdefault(left, set()).add(right)
            left_by_right.setdefault(right, set()).add(left)
        elif left:
            left_only += 1
        elif right:
            right_only += 1
    if not jointly:
        return None
    return {
        "jointly_non_empty_count": jointly,
        "left_only_count": left_only,
        "right_only_count": right_only,
        "unique_pair_count": len(pairs),
        "left_values_with_multiple_right": sum(
            1 for values in right_by_left.values() if len(values) > 1
        ),
        "right_values_with_multiple_left": sum(
            1 for values in left_by_right.values() if len(values) > 1
        ),
    }


def _value_set(
    rows: Sequence[Mapping[str, Any]],
    field: str,
) -> set[str]:
    return {
        _clean(row.get(field))
        for row in rows
        if _clean(row.get(field))
    }


def build_relationship_profile(
    *,
    rows_by_domain: Mapping[str, Sequence[Mapping[str, Any]]],
    table_field_order: Mapping[str, Sequence[str]],
    input_binding_sha256: str,
) -> dict[str, Any]:
    """Build the same payload shape the production profiler must return."""

    same_table: list[dict[str, Any]] = []
    for domain in sorted(rows_by_domain):
        rows = rows_by_domain[domain]
        fields = [
            field
            for field in table_field_order.get(domain, [])
            if field
        ]
        pair_budget = 0
        for left_index in range(len(fields)):
            for right_index in range(left_index + 1, len(fields)):
                pair_budget += 1
                if pair_budget > _MAX_PAIRS_PER_DOMAIN:
                    break
                left_field = fields[left_index]
                right_field = fields[right_index]
                counts = _pair_counts(rows, left_field, right_field)
                if counts is None:
                    continue
                entry: dict[str, Any] = {
                    "domain": domain,
                    "left_field": left_field,
                    "right_field": right_field,
                    # Structural placeholder typing: the stub carries no
                    # clinical interpretation, the type only satisfies the
                    # harness relationship vocabulary.
                    "relationship_type": "visit_identity_pair",
                    "total_rows": len(rows),
                    **counts,
                }
                left_values = _value_set(rows, left_field)
                right_values = _value_set(rows, right_field)
                shared = left_values & right_values
                union = left_values | right_values
                entry["value_overlap"] = {
                    "shared_distinct_count": len(shared),
                    "overlap_rate": (
                        round(len(shared) / len(union), 6) if union else 0.0
                    ),
                }
                same_table.append(entry)
    cross_table: list[dict[str, Any]] = []
    domains = sorted(rows_by_domain)
    for left_index in range(len(domains)):
        for right_index in range(left_index + 1, len(domains)):
            left_domain = domains[left_index]
            right_domain = domains[right_index]
            left_fields = set(table_field_order.get(left_domain, []))
            right_fields = set(table_field_order.get(right_domain, []))
            for field in sorted(left_fields & right_fields):
                left_values = _value_set(rows_by_domain[left_domain], field)
                right_values = _value_set(rows_by_domain[right_domain], field)
                shared = left_values & right_values
                if not shared:
                    continue
                cross_table.append({
                    "left_domain": left_domain,
                    "left_field": field,
                    "right_domain": right_domain,
                    "right_field": field,
                    "match_rate": round(
                        len(shared) / len(left_values | right_values), 6
                    ),
                    "coverage_left": round(
                        len(shared) / len(left_values), 6
                    ) if left_values else 0.0,
                    "coverage_right": round(
                        len(shared) / len(right_values), 6
                    ) if right_values else 0.0,
                    "shared_value_count": len(shared),
                })
    return {
        "schema_version": RELATIONSHIP_PROFILE_SCHEMA_VERSION,
        "profiler_contract": PROFILER_CONTRACT,
        "input_binding_sha256": input_binding_sha256,
        "same_table": same_table,
        "cross_table": cross_table,
    }


__all__ = ["PROFILER_CONTRACT", "build_relationship_profile"]
