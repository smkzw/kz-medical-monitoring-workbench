"""Immutable field catalog for the R3 rule-AI adapter.

Discovery review §4.3: every condition ``field`` MUST hit the frozen field
catalog supplied at call time; a field's allowed operators and value types are
catalog-driven.  Unknown or invented fields become a blocking question, never
an implicit alias.

There is **no built-in default catalog**.  Production callers
(:func:`mm_r3_rule_ai.parser.parse_rule_candidate`,
:func:`mm_r3_rule_ai.prompt.build_prompt`,
:func:`mm_r3_rule_ai.workflow.convert_attempt_to_draft`) all require an
explicit :class:`FieldCatalog` so the public runtime carries no listing-shaped
field vocabulary.  Representative synthetic catalogs for tests live in
:mod:`tests.fixtures_catalogs`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

__all__ = [
    "ConditionOperator",
    "CATALOG_OPERATORS",
    "ValueType",
    "VALUE_TYPES",
    "FieldSpec",
    "FieldCatalog",
    "catalog_hash",
]

# Re-declared here so the catalog is self-contained and does not import frozen
# R3 internals just to describe allowed operators.  Byte identity with frozen
# R3 ``CONDITION_OPERATORS`` is enforced by the isolated cross-package tests.


class ConditionOperator:
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GE = "ge"
    LT = "lt"
    LE = "le"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"
    IS_MISSING = "is_missing"
    IS_PRESENT = "is_present"


CATALOG_OPERATORS: Tuple[str, ...] = (
    ConditionOperator.EQ,
    ConditionOperator.NE,
    ConditionOperator.GT,
    ConditionOperator.GE,
    ConditionOperator.LT,
    ConditionOperator.LE,
    ConditionOperator.CONTAINS,
    ConditionOperator.IN,
    ConditionOperator.NOT_IN,
    ConditionOperator.IS_MISSING,
    ConditionOperator.IS_PRESENT,
)


class ValueType:
    """Value-type tags a catalog field admits for a threshold."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING_LIST = "string_list"
    NUMBER_LIST = "number_list"
    NONE = "none"  # is_missing / is_present forbid a threshold


VALUE_TYPES: Tuple[str, ...] = (
    ValueType.STRING,
    ValueType.NUMBER,
    ValueType.INTEGER,
    ValueType.BOOLEAN,
    ValueType.STRING_LIST,
    ValueType.NUMBER_LIST,
    ValueType.NONE,
)


@dataclass(frozen=True)
class FieldSpec:
    """One field the model is allowed to reference.

    ``allowed_operators`` and ``value_type`` constrain operator/value
    compatibility; the parser enforces both at call time.
    """
    name: str
    domain: str
    label_zh: str
    description_zh: str
    value_type: str = ValueType.STRING
    allowed_operators: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("FieldSpec.name is required")
        if not self.domain or not self.domain.strip():
            raise ValueError("FieldSpec.domain is required")
        if not self.label_zh or not self.label_zh.strip():
            raise ValueError("FieldSpec.label_zh is required")
        if self.value_type not in VALUE_TYPES:
            raise ValueError(f"FieldSpec.value_type {self.value_type!r} unknown")
        # Normalize the operator tuple first so ordering/dup checks operate on
        # the frozen canonical form.
        normalized = tuple(self.allowed_operators)
        bad = [o for o in normalized if o not in CATALOG_OPERATORS]
        if bad:
            raise ValueError(f"FieldSpec.allowed_operators has unknown: {bad}")
        seen: List[str] = []
        dups: List[str] = []
        for op in normalized:
            if op in seen:
                dups.append(op)
            else:
                seen.append(op)
        if dups:
            raise ValueError(f"FieldSpec.allowed_operators has duplicates: {dups}")
        if not normalized:
            raise ValueError("FieldSpec.allowed_operators must contain at least one operator")
        object.__setattr__(self, "allowed_operators", normalized)

    def allows_operator(self, operator: str) -> bool:
        return operator in self.allowed_operators

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "label_zh": self.label_zh,
            "description_zh": self.description_zh,
            "value_type": self.value_type,
            "allowed_operators": list(self.allowed_operators),
        }


@dataclass(frozen=True)
class FieldCatalog:
    """An immutable catalog of allowed fields.

    A catalog is frozen at construction; later mutation is impossible.  The
    catalog is the authoritative field set the model sees and the parser binds
    against.  An empty catalog is rejected: a caller must declare the fields it
    admits.
    """
    _fields: Tuple[FieldSpec, ...]
    _fingerprint: str = ""

    def __post_init__(self) -> None:
        specs = tuple(self._fields)
        if not specs:
            raise ValueError("catalog must contain at least one field")
        seen: Dict[str, int] = {}
        for i, spec in enumerate(specs):
            if not isinstance(spec, FieldSpec):
                raise ValueError("catalog entries must be FieldSpec instances")
            key = spec.name
            if key in seen:
                raise ValueError(f"duplicate field name {key!r} in catalog")
            seen[key] = i
        object.__setattr__(self, "_fields", specs)
        object.__setattr__(self, "_fingerprint", catalog_hash(specs))

    # -- lookup -----------------------------------------------------------
    def names(self) -> Tuple[str, ...]:
        return tuple(spec.name for spec in self._fields)

    def get(self, name: str) -> Optional[FieldSpec]:
        for spec in self._fields:
            if spec.name == name:
                return spec
        return None

    def __contains__(self, name: object) -> bool:
        return self.get(str(name)) is not None

    def __len__(self) -> int:
        return len(self._fields)

    def __iter__(self):
        return iter(self._fields)

    @property
    def fingerprint(self) -> str:
        """Stable SHA-256 of the catalog's canonical payload.

        Bound to every parse so two parses against the same catalog are
        reproducible; a different catalog yields a different fingerprint.
        """
        return self._fingerprint

    def public_payload(self) -> Dict[str, Any]:
        """Deterministic, JSON-able projection for prompt binding and hashing."""
        return {
            "fields": [spec.to_public_dict() for spec in self._fields],
        }

    def domains(self) -> FrozenSet[str]:
        return frozenset(spec.domain for spec in self._fields)


def catalog_hash(specs: Sequence[FieldSpec]) -> str:
    """Stable SHA-256 of the canonical catalog payload."""
    import hashlib
    import json

    payload = {"fields": [spec.to_public_dict() for spec in specs]}
    canon = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()
