"""Deterministic, de-identified relationship profiler for admitted rows.

Produces the frozen-rows relationship evidence consumed by
:mod:`admission.relationship_profile_gate`: the mapping bridge invokes
:func:`build_relationship_profile` with the exact rows it froze, validates
the payload against the gate contract, and binds it into the mapping input
digests.  Evidence covers same-table field pairs (co-occurrence, per-side
missing counts, unique-pair cardinality, bidirectional multi-value
violations, hashed value-domain overlap) and cross-table same-named fields
(coverage both directions, pooled row-level match rate, shared value
count).

Design constraints (Phase C C3 relationship profiler):

* Purely deterministic: no randomness, no wall clock, no I/O, no model or
  service calls.  Identical inputs recompute to an identical payload.
* Bounded: statistics come from an evenly spaced deterministic row sample
  per domain (endpoints kept); pair, shared-field and entry budgets are
  constants, so payload size and compute stay bounded regardless of input
  width.  ``total_rows`` always echoes the full frozen row count per domain
  as the gate requires; the sampled statistics basis is declared in
  ``profiler_contract``.
* De-identified: values are only ever compared as short SHA-256 prefixes of
  trimmed cell text; no raw value and no hash enters the payload — only
  counts, rates in [0, 1] and field/table names already present in the
  admitted profile.
* Generic: no project, drug, disease, table-name, or field-name constants.
  Known naming morphology only labels a structural candidate; every other
  bounded field pair is still emitted as ``statistical_pair`` so Chinese,
  unfamiliar and vendor-specific labels are not silently excluded.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .relationship_profile_gate import RELATIONSHIP_PROFILE_SCHEMA_VERSION

__all__ = [
    "MAX_CROSS_TABLE_ITEMS",
    "MAX_PAIRS_PER_TABLE",
    "MAX_SAME_TABLE_ITEMS",
    "MAX_SAMPLE_ROWS",
    "MAX_SHARED_FIELDS_PER_TABLE_PAIR",
    "RELATIONSHIP_PROFILER_CONTRACT",
    "build_relationship_profile",
]

#: Deterministic row sample size per domain (evenly spaced, endpoints kept).
MAX_SAMPLE_ROWS = 512
#: Same-table field pairs evaluated per domain, in column order.
MAX_PAIRS_PER_TABLE = 96
#: Global same-table item budget (gate hard cap: 400).
MAX_SAME_TABLE_ITEMS = 360
#: Same-named fields evaluated per table pair, in left-table column order.
MAX_SHARED_FIELDS_PER_TABLE_PAIR = 32
#: Global cross-table item budget (gate hard cap: 400).
MAX_CROSS_TABLE_ITEMS = 256

#: Declared statistics basis; must satisfy the gate's contract pattern.
RELATIONSHIP_PROFILER_CONTRACT = (
    "admission-relationship-profiler-strided-max512-v2"
)

#: Field/domain name width the gate accepts; longer names are skipped.
_MAX_NAME_LENGTH = 160

#: Internal value-identity width; hash prefixes never enter the payload.
_VALUE_HASH_HEX = 16

_CANONICAL_SEPARATOR_RE = re.compile(r"[\s_\-./]+")
_NUMERIC_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
_CODE_SUFFIXES: Tuple[Tuple[str, int], ...] = (("CODE", 4), ("CD", 2))
_CODE_TEXT_SIBLINGS: Tuple[Tuple[str, str], ...] = (
    ("CODE", "TEXT"),
    ("CODE", "TERM"),
    ("CD", "NM"),
)
_UNIT_SUFFIX = "UNIT"
_PERFORMED_SUFFIX = "PERF"
_REASON_SUFFIX = "REASND"


def _cell(row: Mapping[str, Any], field: str) -> Optional[str]:
    value = row.get(field)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _value_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:_VALUE_HASH_HEX]


def _canonical_name(field: str) -> str:
    return _CANONICAL_SEPARATOR_RE.sub("", field).upper()


def _sample_positions(row_count: int, max_rows: int) -> List[int]:
    if row_count <= max_rows:
        return list(range(row_count))
    step = (row_count - 1) / (max_rows - 1)
    return sorted({
        min(row_count - 1, int(round(index * step)))
        for index in range(max_rows)
    })


def _mostly_numeric(column: Sequence[Optional[str]]) -> bool:
    values = [text for text in column if text is not None]
    if not values:
        return False
    numeric = sum(1 for text in values if _NUMERIC_RE.fullmatch(text))
    return numeric * 2 >= len(values)


def _same_table_item(
    *,
    domain: str,
    total_rows: int,
    left_field: str,
    left_column: Sequence[Optional[str]],
    right_field: str,
    right_column: Sequence[Optional[str]],
    relationship_type: str,
    sampled_row_count: int,
) -> Dict[str, Any]:
    """Pair evidence over the sampled rows for one morphology-selected pair.

    Counts use every sampled row; value overlap compares each field's
    distinct populated values across the whole sample, so conditional
    branches that never share a row still expose shared or disjoint
    vocabularies.  Cardinality violations count distinct values that map to
    more than one partner among co-populated rows, in both directions.
    """
    jointly = left_only = right_only = 0
    left_hashes: set = set()
    right_hashes: set = set()
    right_by_left: Dict[str, set] = {}
    left_by_right: Dict[str, set] = {}
    for text_left, text_right in zip(left_column, right_column):
        if text_left is not None:
            left_hashes.add(_value_hash(text_left))
        if text_right is not None:
            right_hashes.add(_value_hash(text_right))
        if text_left is None and text_right is None:
            continue
        if text_right is None:
            left_only += 1
            continue
        if text_left is None:
            right_only += 1
            continue
        jointly += 1
        hash_left = _value_hash(text_left)
        hash_right = _value_hash(text_right)
        right_by_left.setdefault(hash_left, set()).add(hash_right)
        left_by_right.setdefault(hash_right, set()).add(hash_left)
    item: Dict[str, Any] = {
        "domain": domain,
        "left_field": left_field,
        "right_field": right_field,
        "relationship_type": relationship_type,
        "total_rows": total_rows,
        "jointly_non_empty_count": jointly,
        "left_only_count": left_only,
        "right_only_count": right_only,
        "unique_pair_count": sum(
            len(values) for values in right_by_left.values()
        ),
        "left_values_with_multiple_right": sum(
            1 for values in right_by_left.values() if len(values) > 1
        ),
        "right_values_with_multiple_left": sum(
            1 for values in left_by_right.values() if len(values) > 1
        ),
    }
    if sampled_row_count < total_rows:
        item["sampled_row_count"] = sampled_row_count
    if left_hashes and right_hashes:
        shared = left_hashes & right_hashes
        item["value_overlap"] = {
            "shared_distinct_count": len(shared),
            "overlap_rate": round(
                len(shared) / len(left_hashes | right_hashes), 6
            ),
        }
    return item


def _pair_candidates(
    fields: Sequence[str],
    canonical_by_field: Mapping[str, str],
    numeric_by_field: Mapping[str, bool],
) -> List[Tuple[str, str, str]]:
    """Morphology-selected pairs, deterministic in column order.

    Only suffix-convention rules are applied; the first matching rule wins
    for a pair, so each pair carries exactly one relationship type.
    """
    field_by_canonical: Dict[str, str] = {}
    for field in fields:
        field_by_canonical.setdefault(canonical_by_field[field], field)
    found: Dict[Tuple[str, str], str] = {}

    def add(left: str, right: str, relationship_type: str) -> None:
        if left and right and left != right:
            found.setdefault((left, right), relationship_type)

    for right_field in fields:
        canonical = canonical_by_field[right_field]
        for suffix, length in _CODE_SUFFIXES:
            if canonical.endswith(suffix) and len(canonical) > length:
                left = field_by_canonical.get(canonical[:-length])
                if left:
                    add(left, right_field, "term_code_pair")
        for code_suffix, text_suffix in _CODE_TEXT_SIBLINGS:
            if (
                canonical.endswith(code_suffix)
                and len(canonical) > len(code_suffix)
            ):
                left = field_by_canonical.get(
                    canonical[:-len(code_suffix)] + text_suffix
                )
                if left:
                    add(left, right_field, "term_code_pair")
        if (
            canonical.endswith(_UNIT_SUFFIX)
            and len(canonical) > len(_UNIT_SUFFIX)
        ):
            left = field_by_canonical.get(canonical[:-len(_UNIT_SUFFIX)])
            if left and numeric_by_field.get(left):
                add(left, right_field, "value_unit_pair")
        if (
            canonical.endswith(_REASON_SUFFIX)
            and len(canonical) > len(_REASON_SUFFIX)
        ):
            left = field_by_canonical.get(
                canonical[:-len(_REASON_SUFFIX)] + _PERFORMED_SUFFIX
            )
            if left:
                add(left, right_field, "performed_reason_pair")
    # The deterministic model context must not disappear merely because a
    # vendor used unfamiliar or Chinese labels.  Semantic morphology wins;
    # all remaining pairs are neutral statistical evidence only.
    ordered_fields = sorted(fields, key=lambda value: (value.casefold(), value))
    for index, left in enumerate(ordered_fields):
        for right in ordered_fields[index + 1:]:
            found.setdefault((left, right), "statistical_pair")
    return [
        (left, right, kind)
        for (left, right), kind in sorted(
            found.items(),
            key=lambda item: (
                item[1] == "statistical_pair",
                item[0][0].casefold(),
                item[0][0],
                item[0][1].casefold(),
                item[0][1],
            ),
        )
    ]


def _shared_field_item(
    *,
    left_domain: str,
    left_field: str,
    left_column: Sequence[Optional[str]],
    right_domain: str,
    right_field: str,
    right_column: Sequence[Optional[str]],
    left_total_rows: int,
    right_total_rows: int,
) -> Optional[Dict[str, Any]]:
    """Coverage and row-level consistency for one same-named cross-table field.

    Coverage compares the distinct hashed value domains of both domains;
    ``match_rate`` pools both directions and reports the share of populated
    rows whose value also exists in the other domain's sampled value set.
    """
    left_values = [
        _value_hash(text) for text in left_column if text is not None
    ]
    right_values = [
        _value_hash(text) for text in right_column if text is not None
    ]
    if not left_values or not right_values:
        return None
    left_set = set(left_values)
    right_set = set(right_values)
    shared = left_set & right_set
    item: Dict[str, Any] = {
        "left_domain": left_domain,
        "left_field": left_field,
        "right_domain": right_domain,
        "right_field": right_field,
        "match_rate": round(
            (
                sum(1 for value in left_values if value in right_set)
                + sum(1 for value in right_values if value in left_set)
            )
            / (len(left_values) + len(right_values)),
            6,
        ),
        "coverage_left": round(len(shared) / len(left_set), 6),
        "coverage_right": round(len(shared) / len(right_set), 6),
        "shared_value_count": len(shared),
    }
    if len(left_column) < left_total_rows:
        item["left_sampled_row_count"] = len(left_column)
    if len(right_column) < right_total_rows:
        item["right_sampled_row_count"] = len(right_column)
    return item


def build_relationship_profile(
    *,
    rows_by_domain: Mapping[str, Sequence[Mapping[str, Any]]],
    table_field_order: Mapping[str, Sequence[str]],
    input_binding_sha256: str,
) -> Dict[str, Any]:
    """Build the gate-contract relationship payload for the mapping bridge.

    ``rows_by_domain`` holds the full frozen rows per domain;
    ``table_field_order`` maps each domain to its ordered field names;
    ``input_binding_sha256`` is the frozen-row binding digest the payload
    must echo (the gate refuses evidence that does not match it).
    """
    sampled_columns: Dict[str, Dict[str, List[Optional[str]]]] = {}
    total_rows_by_domain: Dict[str, int] = {}
    fields_by_domain: Dict[str, List[str]] = {}
    for domain, fields in table_field_order.items():
        usable = [
            field for field in fields
            if field and len(field.strip()) <= _MAX_NAME_LENGTH
        ]
        fields_by_domain[domain] = usable
        rows = rows_by_domain.get(domain) or []
        total_rows_by_domain[domain] = len(rows)
        sampled = [
            rows[position]
            for position in _sample_positions(len(rows), MAX_SAMPLE_ROWS)
            if isinstance(rows[position], Mapping)
        ]
        sampled_columns[domain] = {
            field: [_cell(row, field) for row in sampled]
            for field in usable
        }
    same_table: List[Dict[str, Any]] = []
    for domain in fields_by_domain:
        if len(same_table) >= MAX_SAME_TABLE_ITEMS:
            break
        columns = sampled_columns[domain]
        numeric_by_field = {
            field: _mostly_numeric(column)
            for field, column in columns.items()
        }
        canonical_by_field = {
            field: _canonical_name(field) for field in columns
        }
        candidates = _pair_candidates(
            list(columns), canonical_by_field, numeric_by_field
        )
        for left_field, right_field, relationship_type in candidates[
            :MAX_PAIRS_PER_TABLE
        ]:
            if len(same_table) >= MAX_SAME_TABLE_ITEMS:
                break
            item = _same_table_item(
                domain=domain,
                total_rows=total_rows_by_domain[domain],
                left_field=left_field,
                left_column=columns[left_field],
                right_field=right_field,
                right_column=columns[right_field],
                relationship_type=relationship_type,
                sampled_row_count=len(columns[left_field]),
            )
            if item["jointly_non_empty_count"] <= 0 and (
                item["left_only_count"] <= 0
                or item["right_only_count"] <= 0
            ):
                continue
            same_table.append(item)
    cross_table: List[Dict[str, Any]] = []
    domains = list(fields_by_domain)
    for index, left_domain in enumerate(domains):
        if len(cross_table) >= MAX_CROSS_TABLE_ITEMS:
            break
        left_fields = fields_by_domain[left_domain]
        for right_domain in domains[index + 1:]:
            if len(cross_table) >= MAX_CROSS_TABLE_ITEMS:
                break
            right_fields = set(fields_by_domain[right_domain])
            shared_count = 0
            for field in left_fields:
                if field not in right_fields:
                    continue
                if shared_count >= MAX_SHARED_FIELDS_PER_TABLE_PAIR:
                    break
                if len(cross_table) >= MAX_CROSS_TABLE_ITEMS:
                    break
                item = _shared_field_item(
                    left_domain=left_domain,
                    left_field=field,
                    left_column=sampled_columns[left_domain][field],
                    right_domain=right_domain,
                    right_field=field,
                    right_column=sampled_columns[right_domain][field],
                    left_total_rows=total_rows_by_domain[left_domain],
                    right_total_rows=total_rows_by_domain[right_domain],
                )
                if item is None:
                    continue
                cross_table.append(item)
                shared_count += 1
    return {
        "schema_version": RELATIONSHIP_PROFILE_SCHEMA_VERSION,
        "profiler_contract": RELATIONSHIP_PROFILER_CONTRACT,
        "input_binding_sha256": input_binding_sha256,
        "same_table": same_table,
        "cross_table": cross_table,
    }
