"""Fail-closed gate for relationship evidence entering the mapping bridge.

The C3 mapping bridge only embeds a relationship profile that a pure
deterministic profiler produced over the exact frozen admission rows. This
module owns that contract: it binds the evidence to the rows it was computed
from, validates every entry structurally, and refuses missing or malformed
evidence instead of degrading the mapping input.

Contract for the profiler (dependency-injected or resolved by the pipeline):

1. The profiler is a pure callable. It receives the frozen rows per domain,
   the original table field order, and the input binding digest; it performs
   no I/O, calls no model, and never returns raw cell values — only counts,
   rates and field/table names that already exist in the admitted profile.
2. Its payload must match :data:`RELATIONSHIP_PROFILE_SCHEMA_VERSION` exactly
   (unknown keys are malformed), must echo ``input_binding_sha256``, and must
   keep every entry inside the whitelisted key sets below.
3. Same-table entries reuse the harness relationship vocabulary so the dual
   models read them through the existing ``relationships`` channel. The type
   set mirrors the service-layer ``FIELD_RELATIONSHIP_TYPES``; packages stay
   independent of the FastAPI layer, so the service constant remains the
   source of truth and drift fails closed at submission.

Empty ``same_table`` / ``cross_table`` sections are valid evidence (tables
too small to pair, no same-named cross-table fields, or the profiler's
bounded candidate selection). "Missing evidence" means a payload that is
absent, does not match the binding digest, or violates this contract.

The mapping-stage conclusion boundary also applies to the evidence itself:
structured CTCAE / risk / Query conclusion keys are malformed here, exactly
as they are in mapping verdicts.
"""

from __future__ import annotations

import math
import re
from copy import deepcopy
from typing import Any, Mapping, Sequence

from ..intelligence.primitives import (
    content_hash,
    validate_sha256_hex,
)
from .mapping_reconciliation import FORBIDDEN_CONCLUSION_ITEM_KEYS


RELATIONSHIP_PROFILE_SCHEMA_VERSION = "mm-c3-admission-relationship-profile-v1"
RELATIONSHIP_INPUT_BINDING_SCHEMA_VERSION = (
    "mm-c3-relationship-input-binding-v1"
)

# Mirror of the harness relationship vocabulary accepted by the mapping
# service for same-table pairs (see monitoring_ai_field_profiler). Kept
# local so ``packages`` never imports the FastAPI service layer.
SAME_TABLE_RELATIONSHIP_TYPES = frozenset({
    "statistical_pair",
    "term_code_pair",
    "site_identity_pair",
    "visit_identity_pair",
    "value_unit_pair",
    "performed_reason_pair",
})

# Bounded complexity: a relationship profile may never grow with the raw
# worksheet beyond these evidence limits.
MAX_SAME_TABLE_RELATIONSHIP_ITEMS = 400
MAX_CROSS_TABLE_RELATIONSHIP_ITEMS = 400
MAX_RELATIONSHIP_NAME_LENGTH = 160

_PROFILER_CONTRACT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

_SAME_TABLE_ITEM_KEYS = frozenset({
    "domain",
    "left_field",
    "right_field",
    "relationship_type",
    "total_rows",
    "jointly_non_empty_count",
    "left_only_count",
    "right_only_count",
    "unique_pair_count",
    "left_values_with_multiple_right",
    "right_values_with_multiple_left",
})
_SAME_TABLE_OPTIONAL_KEYS = frozenset({
    "sampled_row_count",
    "value_overlap",
})
_VALUE_OVERLAP_KEYS = frozenset({
    "shared_distinct_count",
    "overlap_rate",
})
_CROSS_TABLE_ITEM_KEYS = frozenset({
    "left_domain",
    "left_field",
    "right_domain",
    "right_field",
    "match_rate",
    "coverage_left",
    "coverage_right",
    "shared_value_count",
})
_CROSS_TABLE_OPTIONAL_KEYS = frozenset({
    "left_sampled_row_count",
    "right_sampled_row_count",
})

_SAME_TABLE_COUNT_KEYS = (
    "total_rows",
    "jointly_non_empty_count",
    "left_only_count",
    "right_only_count",
    "unique_pair_count",
    "left_values_with_multiple_right",
    "right_values_with_multiple_left",
)


class RelationshipProfileGateError(ValueError):
    """Stable fail-closed violation for relationship evidence."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = str(code)
        self.detail = str(detail)
        super().__init__(self.code)


def relationship_input_binding_sha256(
    table_rows_by_snapshot: Mapping[
        str, Mapping[str, Sequence[Mapping[str, Any]]]
    ],
) -> str:
    """Content-address the exact frozen rows relationship evidence binds to."""

    try:
        return content_hash({
            "schema_version": RELATIONSHIP_INPUT_BINDING_SCHEMA_VERSION,
            "rows": table_rows_by_snapshot,
        })
    except (TypeError, ValueError) as exc:
        raise RelationshipProfileGateError(
            "relationship_input_rows_not_canonicalizable",
            str(exc),
        ) from exc


def relationship_rows_by_domain(
    table_bindings: Sequence[Mapping[str, Any]],
    table_rows_by_snapshot: Mapping[
        str, Mapping[str, Sequence[Mapping[str, Any]]]
    ],
) -> dict[str, list[Mapping[str, Any]]]:
    """Collect the frozen rows per domain in table-binding order."""

    rows_by_domain: dict[str, list[Mapping[str, Any]]] = {}
    for binding in table_bindings:
        domain = str(binding.get("domain") or "").strip()
        snapshot_id = str(binding.get("snapshot_id") or "").strip()
        if not domain or not snapshot_id:
            raise RelationshipProfileGateError(
                "relationship_input_binding_incomplete",
                domain or snapshot_id,
            )
        snapshot_content = table_rows_by_snapshot.get(snapshot_id, {})
        if not isinstance(snapshot_content, Mapping):
            raise RelationshipProfileGateError(
                "relationship_input_rows_malformed",
                snapshot_id,
            )
        rows = snapshot_content.get(domain, [])
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise RelationshipProfileGateError(
                "relationship_input_rows_malformed",
                domain,
            )
        rows_by_domain.setdefault(domain, list(rows))
    return rows_by_domain


def _name(value: Any, code: str) -> str:
    if not isinstance(value, str):
        raise RelationshipProfileGateError(code, repr(value)[:80])
    cleaned = value.strip()
    if not cleaned or len(cleaned) > MAX_RELATIONSHIP_NAME_LENGTH:
        raise RelationshipProfileGateError(code, cleaned[:80])
    return cleaned


def _count(value: Any, code: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RelationshipProfileGateError(code, repr(value)[:80])
    return value


def _rate(value: Any, code: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
        or not 0.0 <= float(value) <= 1.0
    ):
        raise RelationshipProfileGateError(code, repr(value)[:80])
    return float(value)


def _exact_keys(
    item: Mapping[str, Any],
    allowed: frozenset[str],
    code: str,
) -> None:
    unexpected = sorted(set(item) - allowed)
    if unexpected:
        raise RelationshipProfileGateError(
            code,
            ",".join(unexpected[:8]),
        )


def _validate_same_table_item(
    item: Mapping[str, Any],
    *,
    fields_by_domain: Mapping[str, set[str]],
    rows_by_domain: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    _exact_keys(
        item,
        _SAME_TABLE_ITEM_KEYS | _SAME_TABLE_OPTIONAL_KEYS,
        "relationship_profile_same_table_key_invalid",
    )
    domain = _name(item.get("domain"), "relationship_profile_name_invalid")
    left_field = _name(
        item.get("left_field"),
        "relationship_profile_name_invalid",
    )
    right_field = _name(
        item.get("right_field"),
        "relationship_profile_name_invalid",
    )
    if left_field == right_field:
        raise RelationshipProfileGateError(
            "relationship_profile_pair_degenerate",
            f"{domain}.{left_field}",
        )
    domain_fields = fields_by_domain.get(domain)
    if domain_fields is None:
        raise RelationshipProfileGateError(
            "relationship_profile_unknown_field",
            domain,
        )
    for field in (left_field, right_field):
        if field not in domain_fields:
            raise RelationshipProfileGateError(
                "relationship_profile_unknown_field",
                f"{domain}.{field}",
            )
    relationship_type = str(item.get("relationship_type") or "").strip()
    if relationship_type not in SAME_TABLE_RELATIONSHIP_TYPES:
        raise RelationshipProfileGateError(
            "relationship_profile_type_invalid",
            relationship_type[:80],
        )
    counts = {
        key: _count(
            item.get(key),
            "relationship_profile_count_invalid",
        )
        for key in _SAME_TABLE_COUNT_KEYS
    }
    sampled_row_count = counts["total_rows"]
    if "sampled_row_count" in item:
        sampled_row_count = _count(
            item.get("sampled_row_count"),
            "relationship_profile_count_invalid",
        )
        if sampled_row_count > counts["total_rows"]:
            raise RelationshipProfileGateError(
                "relationship_profile_counts_inconsistent",
                f"{domain}.{left_field}/{right_field}",
            )
    if counts["total_rows"] != len(rows_by_domain.get(domain, ())):
        raise RelationshipProfileGateError(
            "relationship_profile_row_binding_mismatch",
            f"{domain}.{left_field}/{right_field}",
        )
    if (
        counts["jointly_non_empty_count"]
        + counts["left_only_count"]
        + counts["right_only_count"]
        > sampled_row_count
        or counts["unique_pair_count"] > counts["jointly_non_empty_count"]
    ):
        raise RelationshipProfileGateError(
            "relationship_profile_counts_inconsistent",
            f"{domain}.{left_field}/{right_field}",
        )
    normalized: dict[str, Any] = {"domain": domain, **{
        key: value
        for key, value in (
            ("left_field", left_field),
            ("right_field", right_field),
            ("relationship_type", relationship_type),
        )
    }, **counts}
    if "sampled_row_count" in item:
        normalized["sampled_row_count"] = sampled_row_count
    if "value_overlap" in item:
        overlap = item.get("value_overlap")
        if not isinstance(overlap, Mapping):
            raise RelationshipProfileGateError(
                "relationship_profile_value_overlap_malformed",
                f"{domain}.{left_field}/{right_field}",
            )
        _exact_keys(
            overlap,
            _VALUE_OVERLAP_KEYS,
            "relationship_profile_value_overlap_key_invalid",
        )
        normalized["value_overlap"] = {
            "shared_distinct_count": _count(
                overlap.get("shared_distinct_count"),
                "relationship_profile_count_invalid",
            ),
            "overlap_rate": _rate(
                overlap.get("overlap_rate"),
                "relationship_profile_rate_invalid",
            ),
        }
    return normalized


def _validate_cross_table_item(
    item: Mapping[str, Any],
    *,
    fields_by_domain: Mapping[str, set[str]],
    rows_by_domain: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    _exact_keys(
        item,
        _CROSS_TABLE_ITEM_KEYS | _CROSS_TABLE_OPTIONAL_KEYS,
        "relationship_profile_cross_table_key_invalid",
    )
    left_domain = _name(
        item.get("left_domain"),
        "relationship_profile_name_invalid",
    )
    left_field = _name(
        item.get("left_field"),
        "relationship_profile_name_invalid",
    )
    right_domain = _name(
        item.get("right_domain"),
        "relationship_profile_name_invalid",
    )
    right_field = _name(
        item.get("right_field"),
        "relationship_profile_name_invalid",
    )
    if left_domain == right_domain:
        raise RelationshipProfileGateError(
            "relationship_profile_cross_table_same_domain",
            left_domain,
        )
    for domain, field in (
        (left_domain, left_field),
        (right_domain, right_field),
    ):
        if field not in fields_by_domain.get(domain, set()):
            raise RelationshipProfileGateError(
                "relationship_profile_unknown_field",
                f"{domain}.{field}",
            )
    normalized = {
        "left_domain": left_domain,
        "left_field": left_field,
        "right_domain": right_domain,
        "right_field": right_field,
        "match_rate": _rate(
            item.get("match_rate"),
            "relationship_profile_rate_invalid",
        ),
        "coverage_left": _rate(
            item.get("coverage_left"),
            "relationship_profile_rate_invalid",
        ),
        "coverage_right": _rate(
            item.get("coverage_right"),
            "relationship_profile_rate_invalid",
        ),
        "shared_value_count": _count(
            item.get("shared_value_count"),
            "relationship_profile_count_invalid",
        ),
    }
    for key in _CROSS_TABLE_OPTIONAL_KEYS:
        if key in item:
            sampled_count = _count(
                item.get(key),
                "relationship_profile_count_invalid",
            )
            domain = left_domain if key.startswith("left_") else right_domain
            if sampled_count > len(rows_by_domain.get(domain, ())):
                raise RelationshipProfileGateError(
                    "relationship_profile_counts_inconsistent",
                    f"{left_domain}.{left_field}/{right_domain}.{right_field}",
                )
            normalized[key] = sampled_count
    return normalized


def validate_relationship_profile(
    payload: Any,
    *,
    fields_by_domain: Mapping[str, set[str]],
    rows_by_domain: Mapping[str, Sequence[Mapping[str, Any]]],
    input_binding_sha256: str,
) -> dict[str, Any]:
    """Validate one profiler payload against the bridge contract.

    Returns a normalized deep copy safe to embed in the frozen harness
    profile. Any structural violation raises; nothing is repaired or dropped.
    """

    if not isinstance(payload, Mapping):
        raise RelationshipProfileGateError(
            "relationship_profile_malformed",
            "payload is not an object",
        )
    _exact_keys(
        payload,
        frozenset({
            "schema_version",
            "profiler_contract",
            "input_binding_sha256",
            "same_table",
            "cross_table",
        }),
        "relationship_profile_key_invalid",
    )
    if (
        payload.get("schema_version")
        != RELATIONSHIP_PROFILE_SCHEMA_VERSION
    ):
        raise RelationshipProfileGateError(
            "relationship_profile_schema_version_invalid",
            str(payload.get("schema_version"))[:80],
        )
    profiler_contract = payload.get("profiler_contract")
    if (
        not isinstance(profiler_contract, str)
        or not _PROFILER_CONTRACT_RE.fullmatch(profiler_contract)
    ):
        raise RelationshipProfileGateError(
            "relationship_profile_profiler_contract_invalid",
            repr(profiler_contract)[:80],
        )
    binding = payload.get("input_binding_sha256")
    try:
        valid_binding = isinstance(binding, str) and bool(
            validate_sha256_hex(binding, "relationship input binding")
        )
    except ValueError:
        valid_binding = False
    if not valid_binding:
        raise RelationshipProfileGateError(
            "relationship_profile_binding_digest_malformed",
            repr(binding)[:80],
        )
    if binding != input_binding_sha256:
        raise RelationshipProfileGateError(
            "relationship_profile_binding_mismatch",
            "evidence was not computed from the frozen mapping rows",
        )
    same_table = payload.get("same_table")
    cross_table = payload.get("cross_table")
    if not isinstance(same_table, list) or not isinstance(cross_table, list):
        raise RelationshipProfileGateError(
            "relationship_profile_malformed",
        )
    if len(same_table) > MAX_SAME_TABLE_RELATIONSHIP_ITEMS:
        raise RelationshipProfileGateError(
            "relationship_profile_same_table_too_large",
            str(len(same_table)),
        )
    if len(cross_table) > MAX_CROSS_TABLE_RELATIONSHIP_ITEMS:
        raise RelationshipProfileGateError(
            "relationship_profile_cross_table_too_large",
            str(len(cross_table)),
        )
    normalized_same_table: list[dict[str, Any]] = []
    same_table_keys: set[tuple[str, str, str, str]] = set()
    for item in same_table:
        if not isinstance(item, Mapping):
            raise RelationshipProfileGateError(
                "relationship_profile_malformed",
            )
        if FORBIDDEN_CONCLUSION_ITEM_KEYS.intersection(item):
            raise RelationshipProfileGateError(
                "relationship_profile_conclusion_key",
                "mapping-stage conclusions are not relationship evidence",
            )
        normalized = _validate_same_table_item(
            item,
            fields_by_domain=fields_by_domain,
            rows_by_domain=rows_by_domain,
        )
        key = (
            normalized["domain"],
            normalized["left_field"],
            normalized["right_field"],
            normalized["relationship_type"],
        )
        if key in same_table_keys:
            raise RelationshipProfileGateError(
                "relationship_profile_duplicate",
                "/".join(key[:3]),
            )
        same_table_keys.add(key)
        normalized_same_table.append(normalized)
    normalized_cross_table: list[dict[str, Any]] = []
    cross_table_keys: set[tuple[str, str, str, str]] = set()
    for item in cross_table:
        if not isinstance(item, Mapping):
            raise RelationshipProfileGateError(
                "relationship_profile_malformed",
            )
        if FORBIDDEN_CONCLUSION_ITEM_KEYS.intersection(item):
            raise RelationshipProfileGateError(
                "relationship_profile_conclusion_key",
                "mapping-stage conclusions are not relationship evidence",
            )
        normalized = _validate_cross_table_item(
            item,
            fields_by_domain=fields_by_domain,
            rows_by_domain=rows_by_domain,
        )
        key = (
            normalized["left_domain"],
            normalized["left_field"],
            normalized["right_domain"],
            normalized["right_field"],
        )
        if key in cross_table_keys:
            raise RelationshipProfileGateError(
                "relationship_profile_duplicate",
                "/".join(key),
            )
        cross_table_keys.add(key)
        normalized_cross_table.append(normalized)
    return {
        "schema_version": RELATIONSHIP_PROFILE_SCHEMA_VERSION,
        "profiler_contract": profiler_contract,
        "input_binding_sha256": binding,
        "same_table": normalized_same_table,
        "cross_table": normalized_cross_table,
    }


def same_table_relationship_entries(
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return the harness-channel entries for one validated payload."""

    return deepcopy(list(payload.get("same_table") or []))


def cross_table_relationship_entries(
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return the read-only cross-table entries for one validated payload."""

    return deepcopy(list(payload.get("cross_table") or []))


__all__ = [
    "MAX_CROSS_TABLE_RELATIONSHIP_ITEMS",
    "MAX_SAME_TABLE_RELATIONSHIP_ITEMS",
    "RELATIONSHIP_INPUT_BINDING_SCHEMA_VERSION",
    "RELATIONSHIP_PROFILE_SCHEMA_VERSION",
    "SAME_TABLE_RELATIONSHIP_TYPES",
    "RelationshipProfileGateError",
    "cross_table_relationship_entries",
    "relationship_input_binding_sha256",
    "relationship_rows_by_domain",
    "same_table_relationship_entries",
    "validate_relationship_profile",
]
