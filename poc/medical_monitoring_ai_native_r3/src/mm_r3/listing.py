"""R3-B listing structure profiler.

Profiles heterogeneous listing *structures* into immutable, content-addressed
workbook / table / field profiles.  A profile captures the *shape* of a
listing source (workbook -> tables -> fields) without depending on any project
name or path.  It is the input to semantic mapping (R3-B ``mapping.py``) and
to stable record identity (R3-B ``identity.py``).

Design grounding: system design §§5,16 (deterministic_service: 解析/hash/
identity; 结构画像、Mapping、Canonical Facts; every derived result retains
source locator/raw value and explicit uncertainty); plan R3 step 4 (listing
workbook/table/field 结构画像).

Supported raw input shapes
--------------------------
The profiler accepts a plain-Python *workbook descriptor* (parsed elsewhere)
so that no external parsing library is required:

* ``{"kind": "single_table", "table": {...}}`` -- one table, no workbook.
* ``{"kind": "multi_table", "tables": [...]}`` -- a workbook with named tables.
* a bare table dict ``{"name": ..., "columns": [...]}`` is treated as a
  single-table workbook.

A *table* is ``{"name": str, "columns": [col, ...], "rows": [row, ...]}`` and
a *column* is ``{"name": str, "values": [...] | optional}``.  This keeps the
profiler pure and testable on the synthetic fixtures.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .normalization import (
    NormalizationKind,
    ValueQuality,
    is_missing,
    normalize_value,
)
from .primitives import content_hash, deep_freeze_json, new_id, validate_nonempty_str
from .schema_registry import default_registry

__all__ = [
    "WorkbookProfile",
    "TableProfile",
    "FieldProfile",
    "FieldRole",
    "TableShapeKind",
    "profile_workbook",
    "profile_table",
]


# ---------------------------------------------------------------------------
# Schema validation helper
# ---------------------------------------------------------------------------

def _validate_schema(obj: Any) -> None:
    default_registry().assert_writable(obj.schema_name, obj.schema_version)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ListingProfileError(Exception):
    """Listing structure profiling violation."""


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class FieldRole:
    """Heuristic role assigned to a field by the profiler.

    Roles are *candidates*, not authoritative declarations: the semantic
    mapping layer (``mapping.py``) may refine them.  The profiler never
    silently promotes a field to an identifier; it only proposes a role.
    """
    IDENTIFIER = "identifier"      # looks like a key (subject, site, id)
    DATE = "date"                  # date / partial date column
    DOMAIN = "domain"              # domain tag (AE/MH/CM/LB)
    MEASURE = "measure"            # numeric measurement / value
    UNIT = "unit"                  # unit column
    CLASSIFIER = "classifier"      # coded categorical (sex, severity)
    FREE_TEXT = "free_text"        # unstructured text
    UNKNOWN = "unknown"


FIELD_ROLES: Tuple[str, ...] = (
    FieldRole.IDENTIFIER,
    FieldRole.DATE,
    FieldRole.DOMAIN,
    FieldRole.MEASURE,
    FieldRole.UNIT,
    FieldRole.CLASSIFIER,
    FieldRole.FREE_TEXT,
    FieldRole.UNKNOWN,
)


class TableShapeKind:
    """High-level shape of a table (anti-hardcoding discriminator)."""
    WIDE = "wide"             # many columns, subject-keyed rows
    LONG = "long"             # key/value long form (param/result)
    MATRIX = "matrix"         # 2-D grid
    SINGLE_TABLE = "single_table"
    UNKNOWN = "unknown"


TABLE_SHAPES: Tuple[str, ...] = (
    TableShapeKind.WIDE,
    TableShapeKind.LONG,
    TableShapeKind.MATRIX,
    TableShapeKind.SINGLE_TABLE,
    TableShapeKind.UNKNOWN,
)


# ---------------------------------------------------------------------------
# Hint keywords for role inference (lowercase substrings)
# ---------------------------------------------------------------------------

_ID_KEYWORDS = (
    "subject", "subj", "pt", "patient", "participant", "usubjid",
    "site", "center", "id", "受试者", "参与者", "患者", "病例",
    "研究中心", "中心编号",
)
_DATE_KEYWORDS = (
    "date", "dt", "start", "end", "onset", "stop", "visitdt", "day",
    "日期", "开始时间", "结束时间", "起始日期", "停止日期", "发生时间", "访视日",
)
_DOMAIN_KEYWORDS = (
    "domain", "ae", "mh", "cm", "lb", "vs", "dm", "class",
    "数据域", "数据集", "模块",
)
_MEASURE_KEYWORDS = (
    "val", "value", "result", "res", "num", "count", "score",
    "结果", "数值", "测定值", "计数", "评分",
)
_UNIT_KEYWORDS = ("unit", "uom", "units", "单位")
# classifiers are detected by low-cardinality non-id string columns, not name


def _name_has_hint(name: str, hint: str) -> bool:
    """Match short Latin hints as tokens and Chinese/long hints as substrings."""
    if any("\u4e00" <= ch <= "\u9fff" for ch in hint) or len(hint) > 2:
        return hint in name
    return hint in {t for t in re.split(r"[^a-z0-9]+", name) if t}


def _infer_role(name: str, sample_values: Sequence[Any]) -> str:
    """Heuristic role inference from column name + sample values.

    Name-based hints win when unambiguous; otherwise value cardinality is
    used.  The result is always one of :data:`FIELD_ROLES`; the profiler never
    returns a fabricated role.
    """
    lname = (name or "").lower()
    for kw in _ID_KEYWORDS:
        if _name_has_hint(lname, kw):
            return FieldRole.IDENTIFIER
    for kw in _DATE_KEYWORDS:
        if _name_has_hint(lname, kw):
            return FieldRole.DATE
    for kw in _DOMAIN_KEYWORDS:
        # match "domain"/"class" as whole-ish words; "ae"/"mh" only when the
        # column name *is* the domain token to avoid false positives like
        # "category"
        if kw == lname or (
            kw not in ("ae", "mh", "cm", "lb", "vs", "dm")
            and _name_has_hint(lname, kw)
        ):
            return FieldRole.DOMAIN
    for kw in _UNIT_KEYWORDS:
        if _name_has_hint(lname, kw):
            return FieldRole.UNIT
    for kw in _MEASURE_KEYWORDS:
        if _name_has_hint(lname, kw):
            return FieldRole.MEASURE
    # value-based fallback
    non_missing = [v for v in sample_values if not is_missing(v)]
    if not non_missing:
        return FieldRole.UNKNOWN
    # all numeric -> measure
    if all(_is_number_like(v) for v in non_missing):
        return FieldRole.MEASURE
    # low-cardinality strings -> classifier
    distinct = {_canonical_str(v) for v in non_missing}
    if len(distinct) <= 10 and len(non_missing) >= 4:
        return FieldRole.CLASSIFIER
    # long free text
    max_len = max(len(_canonical_str(v)) for v in non_missing)
    if max_len >= 40:
        return FieldRole.FREE_TEXT
    return FieldRole.UNKNOWN


def _is_number_like(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, str):
        s = v.strip()
        try:
            float(s)
            return True
        except ValueError:
            return False
    return False


def _canonical_str(v: Any) -> str:
    if isinstance(v, str):
        return v.strip().casefold()
    return str(v)


def _infer_kind(role: str) -> str:
    """Map a field role to a normalization kind hint."""
    if role == FieldRole.DATE:
        return NormalizationKind.DATE
    if role == FieldRole.UNIT:
        return NormalizationKind.UNIT
    if role == FieldRole.MEASURE:
        return NormalizationKind.NUMBER
    if role == FieldRole.CLASSIFIER:
        return NormalizationKind.CODED
    return NormalizationKind.TEXT


def _infer_shape(name: str, columns: Sequence["FieldProfile"], n_rows: int) -> str:
    """Infer a table's high-level shape."""
    if not columns:
        return TableShapeKind.UNKNOWN
    col_names = [c.name.lower() for c in columns]
    n_cols = len(columns)
    # long form: a param/paramcd + a value column
    has_param = any(
        any(h in n for h in ("param", "test", "item", "检验项目", "参数", "指标"))
        for n in col_names
    )
    has_value = any(
        any(h in n for h in ("val", "result", "res", "结果", "数值", "测定值"))
        for n in col_names
    )
    if has_param and has_value:
        return TableShapeKind.LONG
    # wide: many columns with an identifier
    has_id = any(c.role == FieldRole.IDENTIFIER for c in columns)
    if has_id and n_cols >= 5:
        return TableShapeKind.WIDE
    if n_cols <= 3:
        return TableShapeKind.SINGLE_TABLE
    return TableShapeKind.UNKNOWN


# ---------------------------------------------------------------------------
# FieldProfile (immutable, content-addressed)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FieldProfile:
    """Profile of one listing column/field.

    Captures name, inferred role, normalization-kind hint, data type majority,
    cardinality, missing-value ratio and a sample of raw values.  Every
    derived statistic retains that it is *derived* (``inferred`` flags) so the
    semantic mapping layer never mistakes a heuristic for a declaration.
    """
    schema_name: str = "r3_field_profile"
    schema_version: str = "1"
    name: str = ""
    role: str = FieldRole.UNKNOWN
    normalization_kind_hint: str = NormalizationKind.TEXT
    code_set_hint: str = ""
    sample_values: Tuple[Any, ...] = ()
    n_values: int = 0
    n_missing: int = 0
    n_distinct: int = 0
    distinct_values: Tuple[Any, ...] = ()
    missing_ratio: float = 0.0
    majority_type: str = "unknown"
    inferred: bool = True

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.name, "FieldProfile.name")
        if self.role not in FIELD_ROLES:
            raise ListingProfileError(
                f"FieldProfile.role={self.role!r} not in {FIELD_ROLES}"
            )
        object.__setattr__(self, "sample_values", deep_freeze_json(self.sample_values))
        object.__setattr__(self, "distinct_values", deep_freeze_json(self.distinct_values))
        if self.n_values < 0 or self.n_missing < 0 or self.n_distinct < 0:
            raise ListingProfileError("counts must be non-negative")
        if self.n_missing > self.n_values:
            raise ListingProfileError("n_missing cannot exceed n_values")
        if not (0.0 <= self.missing_ratio <= 1.0):
            raise ListingProfileError("missing_ratio must be in [0,1]")

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "normalization_kind_hint": self.normalization_kind_hint,
            "code_set_hint": self.code_set_hint,
            "n_values": self.n_values,
            "n_missing": self.n_missing,
            "n_distinct": self.n_distinct,
            "missing_ratio": self.missing_ratio,
            "majority_type": self.majority_type,
            "inferred": self.inferred,
        }

    def content_hash(self) -> str:
        return content_hash(self.canonical_payload())

    def structural_payload(self) -> Dict[str, Any]:
        """Field shape used to compare schemas across full exports.

        Volume and sampled values remain available on the profile for data
        quality review, but they are not schema identity.
        """
        return {
            "name": self.name,
            "role": self.role,
            "normalization_kind_hint": self.normalization_kind_hint,
            "code_set_hint": self.code_set_hint,
            "majority_type": self.majority_type,
            "inferred": self.inferred,
        }

    @property
    def is_identifier_candidate(self) -> bool:
        return self.role == FieldRole.IDENTIFIER

    @property
    def missing(self) -> bool:
        """All values missing."""
        return self.n_values > 0 and self.n_missing == self.n_values


# ---------------------------------------------------------------------------
# TableProfile (immutable, content-addressed)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TableProfile:
    """Profile of one table within a workbook."""
    schema_name: str = "r3_table_profile"
    schema_version: str = "1"
    name: str = ""
    shape: str = TableShapeKind.UNKNOWN
    n_rows: int = 0
    n_columns: int = 0
    fields: Tuple[FieldProfile, ...] = ()
    identifier_candidates: Tuple[str, ...] = ()
    date_candidates: Tuple[str, ...] = ()
    measure_candidates: Tuple[str, ...] = ()
    domain_hint: str = ""
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.name, "TableProfile.name")
        if self.shape not in TABLE_SHAPES:
            raise ListingProfileError(
                f"TableProfile.shape={self.shape!r} not in {TABLE_SHAPES}"
            )
        object.__setattr__(self, "fields", tuple(self.fields))
        object.__setattr__(self, "identifier_candidates", deep_freeze_json(self.identifier_candidates))
        object.__setattr__(self, "date_candidates", deep_freeze_json(self.date_candidates))
        object.__setattr__(self, "measure_candidates", deep_freeze_json(self.measure_candidates))
        if self.n_rows < 0 or self.n_columns < 0:
            raise ListingProfileError("counts must be non-negative")
        if self.n_columns != len(self.fields):
            object.__setattr__(self, "n_columns", len(self.fields))
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise ListingProfileError(
                f"TableProfile.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def field(self, name: str) -> Optional[FieldProfile]:
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "shape": self.shape,
            "n_rows": self.n_rows,
            "n_columns": self.n_columns,
            "fields": [f.canonical_payload() for f in self.fields],
            "identifier_candidates": list(self.identifier_candidates),
            "date_candidates": list(self.date_candidates),
            "measure_candidates": list(self.measure_candidates),
            "domain_hint": self.domain_hint,
        }

    def compute_hash(self) -> str:
        return content_hash(self.structural_payload())

    def structural_payload(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "shape": self.shape,
            "fields": [f.structural_payload() for f in self.fields],
            "identifier_candidates": list(self.identifier_candidates),
            "date_candidates": list(self.date_candidates),
            "measure_candidates": list(self.measure_candidates),
            "domain_hint": self.domain_hint,
        }


# ---------------------------------------------------------------------------
# WorkbookProfile (immutable, content-addressed, binds a source revision)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkbookProfile:
    """Profile of a whole listing workbook (one or more tables).

    Binds the profile to a real :class:`SourceRevision` id so its provenance
    is auditable.  Content-addressed: the same structure yields the same hash.
    """
    schema_name: str = "r3_workbook_profile"
    schema_version: str = "1"
    profile_id: str = ""
    project_id: str = ""
    source_revision_id: str = ""
    tables: Tuple[TableProfile, ...] = ()
    n_tables: int = 0
    n_total_rows: int = 0
    n_total_columns: int = 0
    content_hash: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        validate_nonempty_str(self.profile_id, "WorkbookProfile.profile_id")
        validate_nonempty_str(self.project_id, "WorkbookProfile.project_id")
        validate_nonempty_str(self.source_revision_id, "WorkbookProfile.source_revision_id")
        object.__setattr__(self, "tables", tuple(self.tables))
        object.__setattr__(self, "n_tables", len(self.tables))
        object.__setattr__(self, "n_total_rows", sum(t.n_rows for t in self.tables))
        object.__setattr__(self, "n_total_columns", sum(t.n_columns for t in self.tables))
        expected = self.compute_hash()
        if self.content_hash and self.content_hash != expected:
            raise ListingProfileError(
                f"WorkbookProfile.content_hash mismatch: declared "
                f"{self.content_hash!r} != recomputed {expected!r}"
            )
        object.__setattr__(self, "content_hash", expected)

    def table(self, name: str) -> Optional[TableProfile]:
        for t in self.tables:
            if t.name == name:
                return t
        return None

    def canonical_payload(self) -> Dict[str, Any]:
        """Full payload including the surrogate profile_id (for audit)."""
        return {
            "profile_id": self.profile_id,
            "project_id": self.project_id,
            "source_revision_id": self.source_revision_id,
            "tables": [t.canonical_payload() for t in self.tables],
        }

    def content_fingerprint(self) -> Dict[str, Any]:
        """Structure-only payload.

        Project and source revision remain explicit lineage fields on the
        object, but they do not redefine the structural fingerprint.  This
        lets the same listing shape be recognized across successive full
        exports while a true shape change still produces a new hash.
        """
        return {
            "tables": [t.structural_payload() for t in self.tables],
        }

    def compute_hash(self) -> str:
        return content_hash(self.content_fingerprint())

    @property
    def is_single_table(self) -> bool:
        return len(self.tables) == 1


# ---------------------------------------------------------------------------
# Profiling entry points
# ---------------------------------------------------------------------------

def _majority_type(values: Sequence[Any]) -> str:
    """Return the majority python type name over non-missing values."""
    counts: Dict[str, int] = {}
    for v in values:
        if is_missing(v):
            continue
        if isinstance(v, bool):
            tname = "bool"
        elif isinstance(v, int):
            tname = "int"
        elif isinstance(v, float):
            tname = "float"
        elif isinstance(v, str):
            tname = "str"
        else:
            tname = type(v).__name__
        counts[tname] = counts.get(tname, 0) + 1
    if not counts:
        return "unknown"
    return max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]


def _profile_field(name: str, values: Sequence[Any]) -> FieldProfile:
    non_missing = [v for v in values if not is_missing(v)]
    n_values = len(values)
    n_missing = n_values - len(non_missing)
    canon_distinct = []
    seen = set()
    for v in non_missing:
        ck = _canonical_str(v)
        if ck not in seen:
            seen.add(ck)
            canon_distinct.append(v)
    sample = tuple(non_missing[:10])
    role = _infer_role(name, non_missing)
    kind_hint = _infer_kind(role)
    code_set_hint = ""
    if role == FieldRole.CLASSIFIER:
        lname = name.lower()
        if "sex" in lname or "gender" in lname:
            code_set_hint = "sex"
        elif "severity" in lname or "grade" in lname:
            code_set_hint = "severity"
        elif "serious" in lname:
            code_set_hint = "serious"
        elif "outcome" in lname or "resolution" in lname:
            code_set_hint = "outcome"
    return FieldProfile(
        name=name,
        role=role,
        normalization_kind_hint=kind_hint,
        code_set_hint=code_set_hint,
        sample_values=sample,
        n_values=n_values,
        n_missing=n_missing,
        n_distinct=len(canon_distinct),
        distinct_values=tuple(canon_distinct[:20]),
        missing_ratio=(n_missing / n_values) if n_values else 0.0,
        majority_type=_majority_type(values),
        inferred=True,
    )


def _column_values(table: Mapping[str, Any], col_name: str, rows: Sequence[Mapping[str, Any]]) -> List[Any]:
    """Collect values for one column, preferring an explicit ``values`` list
    on the column descriptor, else reading from rows."""
    cols = table.get("columns") or []
    for c in cols:
        if isinstance(c, Mapping) and c.get("name") == col_name and "values" in c:
            return list(c["values"])
    return [r.get(col_name) for r in rows]


def profile_table(
    table: Mapping[str, Any],
    *,
    table_name: str = "",
) -> TableProfile:
    """Profile a single table descriptor into a :class:`TableProfile`.

    ``table`` is a mapping with:

    * ``name`` (str) -- table name;
    * ``columns`` (list[str | {name, values?}]) -- column declarations;
    * ``rows`` (list[Mapping]) -- row records (optional when columns carry
      explicit ``values``).
    """
    if not isinstance(table, Mapping):
        raise ListingProfileError("profile_table requires a table mapping")
    name = table_name or table.get("name") or ""
    validate_nonempty_str(name, "table.name")
    raw_cols = table.get("columns") or []
    if not raw_cols:
        raise ListingProfileError(f"table {name!r} has no columns")
    rows = list(table.get("rows") or [])

    # normalize column declarations into (name, values)
    col_specs: List[Tuple[str, List[Any]]] = []
    for c in raw_cols:
        if isinstance(c, str):
            col_specs.append((c, _column_values({"columns": raw_cols}, c, rows)))
        elif isinstance(c, Mapping):
            cname = c.get("name")
            if not cname:
                raise ListingProfileError(f"table {name!r} has a column without a name")
            vals = c.get("values") if "values" in c else _column_values(table, cname, rows)
            col_specs.append((str(cname), list(vals or [])))
        else:
            raise ListingProfileError(
                f"table {name!r} column spec must be str or mapping, got {type(c).__name__}"
            )

    fields = tuple(_profile_field(cname, vals) for cname, vals in col_specs)
    n_rows = len(rows) if rows else (max((len(v) for _, v in col_specs), default=0))
    shape = _infer_shape(name, fields, n_rows)

    id_candidates = tuple(f.name for f in fields if f.role == FieldRole.IDENTIFIER)
    date_candidates = tuple(f.name for f in fields if f.role == FieldRole.DATE)
    measure_candidates = tuple(f.name for f in fields if f.role == FieldRole.MEASURE)

    return TableProfile(
        name=name,
        shape=shape,
        n_rows=n_rows,
        n_columns=len(fields),
        fields=fields,
        identifier_candidates=id_candidates,
        date_candidates=date_candidates,
        measure_candidates=measure_candidates,
        domain_hint=str(table.get("domain") or ""),
    )


def profile_workbook(
    project_id: str,
    source_revision_id: str,
    descriptor: Mapping[str, Any],
    *,
    profile_id: str = "",
) -> WorkbookProfile:
    """Profile a workbook descriptor into a :class:`WorkbookProfile`.

    Accepted ``descriptor`` shapes:

    * ``{"kind": "single_table", "table": {...}}``
    * ``{"kind": "multi_table", "tables": [...]}``
    * a bare table dict (treated as single-table).

    The profile binds ``project_id`` + ``source_revision_id`` for provenance.
    """
    validate_nonempty_str(project_id, "profile_workbook.project_id")
    validate_nonempty_str(source_revision_id, "profile_workbook.source_revision_id")
    if not isinstance(descriptor, Mapping):
        raise ListingProfileError("profile_workbook requires a descriptor mapping")

    kind = descriptor.get("kind", "")
    tables: List[TableProfile] = []

    if kind == "single_table" or (not kind and "table" in descriptor):
        t = descriptor.get("table")
        if not isinstance(t, Mapping):
            raise ListingProfileError("single_table descriptor needs a 'table' mapping")
        tables.append(profile_table(t))
    elif kind == "multi_table" or "tables" in descriptor:
        raw_tables = descriptor.get("tables") or []
        if not raw_tables:
            raise ListingProfileError("multi_table descriptor has no tables")
        for i, t in enumerate(raw_tables):
            if not isinstance(t, Mapping):
                raise ListingProfileError(f"table #{i} is not a mapping")
            tables.append(profile_table(t))
    else:
        # bare table dict
        if "columns" in descriptor:
            tables.append(profile_table(descriptor))
        else:
            raise ListingProfileError(
                "descriptor must be single_table/multi_table or a bare table"
            )

    n_total_rows = sum(t.n_rows for t in tables)
    n_total_columns = sum(t.n_columns for t in tables)

    return WorkbookProfile(
        profile_id=profile_id or new_id("wbp-"),
        project_id=project_id,
        source_revision_id=source_revision_id,
        tables=tuple(tables),
        n_total_rows=n_total_rows,
        n_total_columns=n_total_columns,
    )
