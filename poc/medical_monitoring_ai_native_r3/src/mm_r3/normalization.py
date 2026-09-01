"""R3-B normalization semantics.

Deterministic normalization of listing cell values: dates, partial dates,
units, coded values, duplicates and missing values.  Every normalization
preserves the *original* raw value and emits explicit uncertainty, so a
downstream consumer can never mistake a normalized surrogate for ground truth.

Design grounding: system design §§5,9,16 (deterministic_service: 解析/hash/
identity/diff/单位/日期校验; partial/missing/conflict dates preserve
uncertainty; LLM/Agent only submit candidates, never auto-promote canonical
facts); plan R3 step 6 (日期、单位、编码、部分日期、重复记录和缺失语义).

Contracts
---------
* :class:`NormalizedValue` -- one cell's normalization outcome: original raw
  value, normalized value, kind, quality flags and explicit uncertainty.
* :func:`normalize_value` -- dispatch a raw value to the right normalizer.
* Date / partial-date / unit / coding / duplicate helpers.
* :class:`ValueNormalizer` -- pure stateless normalizer over a field profile
  hint (column name + expected kind).

All functions are pure (no I/O, no randomness).  Determinism is a hard
contract: the same raw value + hint always yields the same result.
"""

from __future__ import annotations

import datetime
import re as _re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .primitives import content_hash, deep_freeze_json, validate_nonempty_str
from .schema_registry import default_registry

__all__ = [
    "NormalizedValue",
    "NormalizationKind",
    "ValueQuality",
    "normalize_value",
    "normalize_date",
    "normalize_partial_date",
    "normalize_unit",
    "normalize_coded_value",
    "detect_duplicate",
    "ValueNormalizer",
    "UNKNOWN_VALUES",
    "PARTIAL_DATE_PATTERNS",
]


# ---------------------------------------------------------------------------
# Schema validation helper
# ---------------------------------------------------------------------------

def _validate_schema(obj: Any) -> None:
    default_registry().assert_writable(obj.schema_name, obj.schema_version)


# ---------------------------------------------------------------------------
# Enumerations (string constants; frozen dataclasses validate membership)
# ---------------------------------------------------------------------------

class NormalizationKind:
    """What a value was normalized *into*."""
    DATE = "date"
    PARTIAL_DATE = "partial_date"
    UNIT = "unit"
    CODED = "coded"
    TEXT = "text"
    NUMBER = "number"
    MISSING = "missing"
    UNSUPPORTED = "unsupported"


NORMALIZATION_KINDS: Tuple[str, ...] = (
    NormalizationKind.DATE,
    NormalizationKind.PARTIAL_DATE,
    NormalizationKind.UNIT,
    NormalizationKind.CODED,
    NormalizationKind.TEXT,
    NormalizationKind.NUMBER,
    NormalizationKind.MISSING,
    NormalizationKind.UNSUPPORTED,
)


class ValueQuality:
    """Quality of a normalized value (Design: explicit uncertainty)."""
    EXACT = "exact"                 # full-resolution, no uncertainty
    NORMALIZED = "normalized"       # canonicalized but unambiguous
    PARTIAL = "partial"             # some components missing/unknown
    IMPUTED = "imputed"             # a default was applied (recorded)
    AMBIGUOUS = "ambiguous"         # multiple interpretations possible
    MISSING = "missing"             # no usable value
    UNSUPPORTED = "unsupported"     # cannot normalize this kind


VALUE_QUALITIES: Tuple[str, ...] = (
    ValueQuality.EXACT,
    ValueQuality.NORMALIZED,
    ValueQuality.PARTIAL,
    ValueQuality.IMPUTED,
    ValueQuality.AMBIGUOUS,
    ValueQuality.MISSING,
    ValueQuality.UNSUPPORTED,
)


def _validate_enum(value: str, allowed: Tuple[str, ...], field_name: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field_name}={value!r} not in {allowed}")
    return value


# ---------------------------------------------------------------------------
# Missing-value detection (case-insensitive, NB-camp compatible)
# ---------------------------------------------------------------------------

#: Sentinels that mean "no value".  Matches R2's set plus a few listing-typical
#: blanks.  None is handled separately.  Case-insensitive on strings.
UNKNOWN_VALUES: frozenset = frozenset({
    "", "UN", "UNK", "UNKNOWN", "N/A", "NA", "NOT DONE", "ND",
    "NOT APPLICABLE", "NOT EVALUABLE", "MISSING",
})


def is_missing(value: Any) -> bool:
    """True when *value* is a recognized missing/unknown sentinel or None.

    Whitespace-only strings are missing.  Numeric zero is *not* missing.
    """
    if value is None:
        return True
    if isinstance(value, str):
        if value.strip() == "":
            return True
        if value.strip().upper() in UNKNOWN_VALUES:
            return True
        return False
    return False


# ---------------------------------------------------------------------------
# Date / partial-date normalization
# ---------------------------------------------------------------------------

_DATE_FULL = _re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DATE_YMD_SEP = _re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})$")
_DATE_DMY_SEP = _re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")
_DATE_YMD_ZH = _re.compile(r"^(\d{4})年(\d{1,2})月(\d{1,2})日$")
_DATE_YM = _re.compile(r"^(\d{4})-(\d{2})$")
_DATE_Y = _re.compile(r"^(\d{4})$")
# ISO 8601 partial with UNK components, e.g. "2026-02-UNK" or "2026-UNK-05"
_DATE_PARTIAL_UNK = _re.compile(r"^(\d{4}|UNK)-(\d{2}|UNK)-(\d{2}|UNK)$")

#: Documented partial-date shapes, ordered most-specific first.
PARTIAL_DATE_PATTERNS: Tuple[str, ...] = (
    "yyyy-mm-dd",
    "yyyy-mm",
    "yyyy",
    "yyyy-mm-unk-day",
    "yyyy-unk-mm-dd",
    "yyyy-unk-mm-unk-day",
)

_MAX_DAY_BY_MONTH = {
    1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31,
}


def _valid_ymd(year: int, month: int, day: int) -> bool:
    if not (1 <= month <= 12):
        return False
    max_day = _MAX_DAY_BY_MONTH[month]
    if not (1 <= day <= max_day):
        return False
    # reject Feb 30 on non-leap years
    if month == 2 and day == 29:
        try:
            datetime.date(year, month, day)
        except ValueError:
            return False
    return True


def normalize_date(value: Any) -> "NormalizedValue":
    """Normalize a full or partial date string.

    Accepted shapes (case-sensitive on UNK): ``YYYY-MM-DD``,
    ``YYYY/MM/DD``, ``DD/MM/YYYY``, ``YYYY-MM``, ``YYYY``,
    and ISO partials with ``UNK`` components.

    * Full date -> :attr:`NormalizationKind.DATE`, quality ``exact``.
    * Partial date (missing month/day or UNK component) ->
      :attr:`NormalizationKind.PARTIAL_DATE`, quality ``partial``; the
      ``normalized`` value is the most specific sortable prefix and
      ``uncertainty`` records which components are unknown.
    * Separated forms are normalized to ISO ``-`` separators (quality
      ``normalized``), never silently re-interpreted.
    """
    raw = value
    if is_missing(value):
        return NormalizedValue._missing(raw)
    if isinstance(value, str):
        s = value.strip()
    else:
        return NormalizedValue._unsupported(raw, "date", "non-string date")

    # full ISO date
    m = _DATE_FULL.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_ymd(y, mo, d):
            iso = f"{y:04d}-{mo:02d}-{d:02d}"
            quality = ValueQuality.EXACT if iso == s else ValueQuality.NORMALIZED
            return NormalizedValue(
                raw_value=raw,
                kind=NormalizationKind.DATE,
                normalized=iso,
                quality=quality,
                uncertainty="",
                detail="iso_date" if quality == ValueQuality.EXACT else "iso_date_from_separated",
            )
        return NormalizedValue(
            raw_value=raw,
            kind=NormalizationKind.PARTIAL_DATE,
            normalized="",
            quality=ValueQuality.AMBIGUOUS,
            uncertainty="invalid calendar date",
            detail="invalid_full_date",
        )

    # Chinese YMD, then slash-separated YMD or DMY
    m = _DATE_YMD_ZH.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_ymd(y, mo, d):
            return NormalizedValue(
                raw_value=raw,
                kind=NormalizationKind.DATE,
                normalized=f"{y:04d}-{mo:02d}-{d:02d}",
                quality=ValueQuality.NORMALIZED,
                uncertainty="",
                detail="ymd_chinese",
            )
        return NormalizedValue(
            raw_value=raw, kind=NormalizationKind.PARTIAL_DATE, normalized="",
            quality=ValueQuality.AMBIGUOUS, uncertainty="invalid calendar date",
            detail="invalid_ymd_chinese",
        )

    m = _DATE_YMD_SEP.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_ymd(y, mo, d):
            iso = f"{y:04d}-{mo:02d}-{d:02d}"
            return NormalizedValue(
                raw_value=raw,
                kind=NormalizationKind.DATE,
                normalized=iso,
                quality=ValueQuality.NORMALIZED,
                uncertainty="",
                detail="ymd_slash",
            )
        return NormalizedValue(
            raw_value=raw, kind=NormalizationKind.PARTIAL_DATE, normalized="",
            quality=ValueQuality.AMBIGUOUS, uncertainty="invalid calendar date",
            detail="invalid_ymd_slash",
        )
    m = _DATE_DMY_SEP.match(s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if _valid_ymd(y, mo, d):
            iso = f"{y:04d}-{mo:02d}-{d:02d}"
            return NormalizedValue(
                raw_value=raw,
                kind=NormalizationKind.DATE,
                normalized=iso,
                quality=ValueQuality.AMBIGUOUS,
                uncertainty="dd/mm/yyyy interpreted as day-first; ambiguous without locale",
                detail="dmy_slash",
            )
        return NormalizedValue(
            raw_value=raw, kind=NormalizationKind.PARTIAL_DATE, normalized="",
            quality=ValueQuality.AMBIGUOUS, uncertainty="invalid calendar date",
            detail="invalid_dmy_slash",
        )

    # YYYY-MM
    m = _DATE_YM.match(s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return NormalizedValue(
                raw_value=raw,
                kind=NormalizationKind.PARTIAL_DATE,
                normalized=f"{y:04d}-{mo:02d}",
                quality=ValueQuality.PARTIAL,
                uncertainty="day unknown",
                detail="yyyy_mm",
            )
        return NormalizedValue(
            raw_value=raw, kind=NormalizationKind.PARTIAL_DATE, normalized="",
            quality=ValueQuality.AMBIGUOUS, uncertainty="invalid month",
            detail="invalid_yyyy_mm",
        )

    # YYYY
    m = _DATE_Y.match(s)
    if m:
        y = int(m.group(1))
        if 1900 <= y <= 2100:
            return NormalizedValue(
                raw_value=raw,
                kind=NormalizationKind.PARTIAL_DATE,
                normalized=f"{y:04d}",
                quality=ValueQuality.PARTIAL,
                uncertainty="month and day unknown",
                detail="yyyy",
            )
        return NormalizedValue(
            raw_value=raw, kind=NormalizationKind.PARTIAL_DATE, normalized="",
            quality=ValueQuality.AMBIGUOUS, uncertainty="year out of plausible range",
            detail="invalid_yyyy",
        )

    # ISO partial with UNK components
    m = _DATE_PARTIAL_UNK.match(s.upper())
    if m:
        yg, mg, dg = m.group(1), m.group(2), m.group(3)
        unknown: List[str] = []
        if yg == "UNK":
            unknown.append("year")
        if mg == "UNK":
            unknown.append("month")
        if dg == "UNK":
            unknown.append("day")
        prefix_parts = []
        if yg != "UNK":
            prefix_parts.append(f"{int(yg):04d}")
        if mg != "UNK":
            mo_i = int(mg)
            if not (1 <= mo_i <= 12):
                return NormalizedValue(
                    raw_value=raw, kind=NormalizationKind.PARTIAL_DATE,
                    normalized="", quality=ValueQuality.AMBIGUOUS,
                    uncertainty="invalid month", detail="invalid_partial_unk",
                )
            if prefix_parts:
                prefix_parts.append(f"{mo_i:02d}")
        if dg != "UNK":
            d_i = int(dg)
            max_d = _MAX_DAY_BY_MONTH.get(int(mg) if mg != "UNK" else 1, 31)
            if not (1 <= d_i <= max_d):
                return NormalizedValue(
                    raw_value=raw, kind=NormalizationKind.PARTIAL_DATE,
                    normalized="", quality=ValueQuality.AMBIGUOUS,
                    uncertainty="invalid day", detail="invalid_partial_unk",
                )
            if prefix_parts and len(prefix_parts) >= 2:
                prefix_parts.append(f"{d_i:02d}")
        prefix = "-".join(prefix_parts)
        return NormalizedValue(
            raw_value=raw,
            kind=NormalizationKind.PARTIAL_DATE,
            normalized=prefix,
            quality=ValueQuality.PARTIAL,
            uncertainty=", ".join(unknown) + " unknown" if unknown else "",
            detail="partial_unk",
        )

    return NormalizedValue(
        raw_value=raw, kind=NormalizationKind.UNSUPPORTED, normalized="",
        quality=ValueQuality.UNSUPPORTED,
        uncertainty="unrecognized date format",
        detail="unrecognized_date",
    )


def normalize_partial_date(value: Any) -> "NormalizedValue":
    """Alias that documents partial-date intent explicitly."""
    nv = normalize_date(value)
    # If full date came back, still report it as a partial_date-kind result
    # so callers requesting partial semantics see a consistent kind.
    if nv.kind == NormalizationKind.DATE:
        return NormalizedValue(
            raw_value=nv.raw_value,
            kind=NormalizationKind.PARTIAL_DATE,
            normalized=nv.normalized,
            quality=ValueQuality.NORMALIZED,
            uncertainty="complete date (no missing components)",
            detail="complete_date_as_partial",
        )
    return nv


# ---------------------------------------------------------------------------
# Unit normalization (case/symbol/synonym canonicalization, no conversion)
# ---------------------------------------------------------------------------

#: Canonical unit map.  Keys are lower-cased, whitespace-collapsed raw unit
#: strings.  Values are the canonical unit.  This canonicalizes *spelling and
#: symbol variants only*; it deliberately does NOT perform arithmetic unit
#: conversion (that would require a factor + uncertainty record).
_UNIT_CANONICAL: Dict[str, str] = {
    # mass / volume concentration (labs)
    "u/l": "U/L",
    "iu/l": "U/L",
    "units/l": "U/L",
    "unit/l": "U/L",
    "umol/l": "umol/L",
    "mmol/l": "mmol/L",
    "mg/dl": "mg/dL",
    "mg/dl": "mg/dL",
    "ug/dl": "ug/dL",
    "ng/ml": "ng/mL",
    "pg/ml": "pg/mL",
    "g/l": "g/L",
    "g/dl": "g/dL",
    # counts
    "10^3/ul": "10^9/L",
    "10^3/mm3": "10^9/L",
    "k/ul": "10^9/L",
    "10^6/ul": "10^12/L",
    "m/ul": "10^12/L",
    # length
    "cm": "cm",
    "mm": "mm",
    "in": "in",
    "inch": "in",
    # mass
    "kg": "kg",
    "g": "g",
    "mg": "mg",
    "ug": "ug",
    "μg": "ug",
    "µg": "ug",
    "mcg": "ug",
    # volume
    "ml": "mL",
    "l": "L",
    "dl": "dL",
    # time / rate
    "sec": "s",
    "secs": "s",
    "seconds": "s",
    "min": "min",
    "mins": "min",
    "minutes": "min",
    "hr": "h",
    "hrs": "h",
    "hours": "h",
    # frequency
    "/day": "/day",
    "qd": "once daily",
    "bid": "twice daily",
    "tid": "three times daily",
    "qid": "four times daily",
    "q.d.": "once daily",
    "b.i.d.": "twice daily",
    # percent
    "%": "%",
    "percent": "%",
    # temperature
    "c": "C",
    "degc": "C",
    "°c": "C",
    "f": "F",
    "degf": "F",
    "°f": "F",
    # pressure
    "mmhg": "mmHg",
    "kg/m2": "kg/m^2",
    "bmi": "kg/m^2",
}


def _collapse_ws(s: str) -> str:
    return _re.sub(r"\s+", " ", s).strip()


def normalize_unit(value: Any) -> "NormalizedValue":
    """Canonicalize a unit string's spelling/symbol/synonym form.

    * Case-insensitive lookup with whitespace collapse.
    * A recognized variant -> canonical unit, quality ``normalized``.
    * An unrecognized non-empty unit -> itself, quality ``exact`` with
      ``uncertainty`` noting it is not in the canonical table (so consumers
      know it was *not* converted, merely passed through).
    * Missing -> ``missing``.
    * Never performs arithmetic conversion; different magnitudes stay distinct.
    """
    raw = value
    if is_missing(value):
        return NormalizedValue._missing(raw)
    if not isinstance(value, str):
        return NormalizedValue._unsupported(raw, "unit", "non-string unit")
    # collapse whitespace AND remove spaces around separators so that
    # "mg / dL" matches the canonical "mg/dl" key.
    key = _re.sub(r"\s*([/^])\s*", r"\1", _collapse_ws(value)).lower()
    if not key:
        return NormalizedValue._missing(raw)
    canon = _UNIT_CANONICAL.get(key)
    if canon is not None:
        quality = ValueQuality.EXACT if canon == value else ValueQuality.NORMALIZED
        return NormalizedValue(
            raw_value=raw,
            kind=NormalizationKind.UNIT,
            normalized=canon,
            quality=quality,
            uncertainty="",
            detail="canonical_unit" if quality == ValueQuality.NORMALIZED else "exact_unit",
        )
    # unrecognized but non-empty: pass through, flag uncertainty.
    # Quality is AMBIGUOUS because the canonical meaning is unknown.
    return NormalizedValue(
        raw_value=raw,
        kind=NormalizationKind.UNIT,
        normalized=_collapse_ws(value),
        quality=ValueQuality.AMBIGUOUS,
        uncertainty="unit not in canonical table; no conversion performed",
        detail="unrecognized_unit",
    )


# ---------------------------------------------------------------------------
# Coded value normalization (case/synonym/boolean canonicalization)
# ---------------------------------------------------------------------------

#: Boolean / yes-no synonyms -> canonical token.
_BOOL_TRUE = frozenset({"yes", "y", "true", "t", "1", "是"})
_BOOL_FALSE = frozenset({"no", "n", "false", "f", "0", "否"})

#: Severity / sex / common coded-value synonyms.
_CODE_SYNONYMS: Dict[str, Dict[str, str]] = {
    "sex": {
        "m": "Male", "male": "Male", "男": "Male",
        "f": "Female", "female": "Female", "女": "Female",
    },
    "severity": {
        "mild": "Mild", "1": "Mild", "轻度": "Mild",
        "moderate": "Moderate", "2": "Moderate", "中度": "Moderate",
        "severe": "Severe", "3": "Severe", "重度": "Severe", "严重": "Severe", "grade3": "Severe",
        "grade 3": "Severe",
    },
    "serious": {"yes": "Yes", "no": "No"},
    "outcome": {
        "recovered": "Recovered/Resolved",
        "resolved": "Recovered/Resolved",
        "recovering": "Recovering/Resolving",
        "resolving": "Recovering/Resolving",
        "not recovered": "Not Recovered/Not Resolved",
        "ongoing": "Ongoing",
    },
}


def normalize_coded_value(
    value: Any,
    *,
    code_set: str = "",
) -> "NormalizedValue":
    """Normalize a coded/boolean value into a canonical token.

    * ``code_set`` optionally names a synonym group (``sex``/``severity``/
      ``serious``/``outcome``).
    * Boolean synonyms (yes/no/true/false/1/0) canonicalize to ``Yes``/``No``
      when no code_set is given.
    * Unrecognized non-empty codes pass through with quality ``exact`` and an
      uncertainty note; they are never silently coerced.
    """
    raw = value
    if is_missing(value):
        return NormalizedValue._missing(raw)
    if isinstance(value, bool):
        return NormalizedValue(
            raw_value=raw,
            kind=NormalizationKind.CODED,
            normalized="Yes" if value else "No",
            quality=ValueQuality.EXACT,
            uncertainty="",
            detail="python_bool",
        )
    if not isinstance(value, str):
        # numbers as codes pass through
        return NormalizedValue(
            raw_value=raw,
            kind=NormalizationKind.CODED,
            normalized=value,
            quality=ValueQuality.EXACT,
            uncertainty="numeric code not decoded",
            detail="numeric_code",
        )
    s = value.strip()
    key = s.lower()
    if not key:
        return NormalizedValue._missing(raw)
    # code-set specific synonyms first
    if code_set and code_set in _CODE_SYNONYMS:
        canon = _CODE_SYNONYMS[code_set].get(key)
        if canon is not None:
            quality = ValueQuality.EXACT if canon == s else ValueQuality.NORMALIZED
            return NormalizedValue(
                raw_value=raw,
                kind=NormalizationKind.CODED,
                normalized=canon,
                quality=quality,
                uncertainty="",
                detail=f"code_set:{code_set}",
            )
    # boolean synonyms
    if key in _BOOL_TRUE:
        return NormalizedValue(
            raw_value=raw, kind=NormalizationKind.CODED, normalized="Yes",
            quality=ValueQuality.NORMALIZED, uncertainty="",
            detail="bool_true",
        )
    if key in _BOOL_FALSE:
        return NormalizedValue(
            raw_value=raw, kind=NormalizationKind.CODED, normalized="No",
            quality=ValueQuality.NORMALIZED, uncertainty="",
            detail="bool_false",
        )
    # pass-through: canonical meaning unknown, so quality is AMBIGUOUS.
    note = ("code not in synonym table; passed through unchanged"
            if not code_set
            else f"code not in code_set {code_set!r}; passed through")
    return NormalizedValue(
        raw_value=raw,
        kind=NormalizationKind.CODED,
        normalized=s,
        quality=ValueQuality.AMBIGUOUS,
        uncertainty=note,
        detail="unrecognized_code",
    )


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def detect_duplicate(
    value: Any,
    *,
    seen: Optional[set] = None,
    key: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """Detect a duplicate scalar value within a de-duplication set.

    Returns ``(is_duplicate, canonical_key)``.  ``canonical_key`` is the
    canonical JSON key used for membership (so callers can debug); ``None``
    when the value is missing (missing values are never "duplicates" -- they
    are unknowns).

    * ``seen`` is mutated in place when provided (caller-managed set).  When
      ``seen`` is ``None`` the function is a pure classifier: it only returns
      the canonical key, ``is_duplicate`` is always ``False``.
    * ``key`` optionally overrides the canonical key (e.g. a pre-normalized
      form).  When omitted, the raw value is canonicalized via
      :func:`canonical_json`.
    """
    if is_missing(value):
        return False, None
    ckey = key if key is not None else _canonical_key(value)
    if seen is None:
        return False, ckey
    if ckey in seen:
        return True, ckey
    seen.add(ckey)
    return False, ckey


def _canonical_key(value: Any) -> str:
    """Stable string key for membership comparison.

    Strings are trimmed + lower-cased so that ``"S001"`` and ``" s001 "``
    collapse (display-only differences should not invent duplicates), but
    genuinely distinct scalars stay distinct.
    """
    if isinstance(value, str):
        return "s:" + value.strip().lower()
    if isinstance(value, bool):
        return "b:" + str(value)
    if isinstance(value, (int, float)):
        return "n:" + repr(value)
    # fallback: canonical JSON of the structure
    import json
    return "j:" + json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False)


# ---------------------------------------------------------------------------
# NormalizedValue (immutable, schema-validated, retains raw + uncertainty)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NormalizedValue:
    """The outcome of normalizing one raw cell value.

    Invariants (Design: explicit uncertainty, 来源优先):
    * ``raw_value`` is always the original input (deep-frozen).
    * ``normalized`` is the canonical form (may equal raw when already
      canonical, or be empty when the value could not be normalized).
    * ``quality`` expresses the certainty/uncertainty of the normalization.
    * ``uncertainty`` is a human-readable note; empty only when quality is
      ``exact``.
    * ``detail`` is a machine-readable discriminator for auditing.
    """
    schema_name: str = "r3_normalized_value"
    schema_version: str = "1"
    raw_value: Any = None
    kind: str = NormalizationKind.TEXT
    normalized: Any = None
    quality: str = ValueQuality.EXACT
    uncertainty: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        _validate_schema(self)
        _validate_enum(self.kind, NORMALIZATION_KINDS, "NormalizedValue.kind")
        _validate_enum(self.quality, VALUE_QUALITIES, "NormalizedValue.quality")
        if self.quality == ValueQuality.EXACT and self.uncertainty:
            raise ValueError(
                "NormalizedValue quality 'exact' must carry no uncertainty"
            )
        if self.quality != ValueQuality.EXACT and not self.uncertainty:
            # normalized = deterministic canonicalization, no residual ambiguity:
            # uncertainty is legitimately empty.  missing/unsupported/partial/
            # imputed/ambiguous all require an explicit note.
            if self.quality not in (ValueQuality.MISSING, ValueQuality.NORMALIZED):
                raise ValueError(
                    f"NormalizedValue quality {self.quality!r} requires a "
                    f"non-empty uncertainty note"
                )
        object.__setattr__(self, "raw_value", deep_freeze_json(self.raw_value))
        object.__setattr__(self, "normalized", deep_freeze_json(self.normalized))

    # -- factories ---------------------------------------------------------

    @classmethod
    def _missing(cls, raw: Any) -> "NormalizedValue":
        return cls(
            raw_value=raw,
            kind=NormalizationKind.MISSING,
            normalized=None,
            quality=ValueQuality.MISSING,
            uncertainty="missing or unknown sentinel",
            detail="missing",
        )

    @classmethod
    def _unsupported(cls, raw: Any, kind: str, note: str) -> "NormalizedValue":
        return cls(
            raw_value=raw,
            kind=NormalizationKind.UNSUPPORTED,
            normalized=None,
            quality=ValueQuality.UNSUPPORTED,
            uncertainty=note,
            detail="unsupported",
        )

    # -- derived -----------------------------------------------------------

    @property
    def is_missing(self) -> bool:
        return self.kind == NormalizationKind.MISSING

    @property
    def is_partial(self) -> bool:
        return self.quality in (ValueQuality.PARTIAL, ValueQuality.AMBIGUOUS,
                                ValueQuality.IMPUTED)

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "raw_value": self.raw_value,
            "kind": self.kind,
            "normalized": self.normalized,
            "quality": self.quality,
            "uncertainty": self.uncertainty,
            "detail": self.detail,
        }

    def content_hash(self) -> str:
        return content_hash(self.canonical_payload())


# ---------------------------------------------------------------------------
# Text / number passthrough (so normalize_value always returns NormalizedValue)
# ---------------------------------------------------------------------------

def _normalize_text(value: Any) -> NormalizedValue:
    if is_missing(value):
        return NormalizedValue._missing(value)
    if isinstance(value, str):
        s = value.strip()
        return NormalizedValue(
            raw_value=value, kind=NormalizationKind.TEXT,
            normalized=s, quality=ValueQuality.NORMALIZED,
            uncertainty="trimmed whitespace" if s != value else "",
            detail="text_trim",
        )
    return NormalizedValue(
        raw_value=value, kind=NormalizationKind.TEXT, normalized=value,
        quality=ValueQuality.EXACT, uncertainty="", detail="text_passthrough",
    )


def _normalize_number(value: Any) -> NormalizedValue:
    if is_missing(value):
        return NormalizedValue._missing(value)
    if isinstance(value, bool):
        return NormalizedValue(
            raw_value=value, kind=NormalizationKind.NUMBER,
            normalized=int(value), quality=ValueQuality.NORMALIZED,
            uncertainty="boolean coerced to int", detail="bool_to_int",
        )
    if isinstance(value, (int, float)):
        return NormalizedValue(
            raw_value=value, kind=NormalizationKind.NUMBER, normalized=value,
            quality=ValueQuality.EXACT, uncertainty="", detail="number",
        )
    if isinstance(value, str):
        s = value.strip()
        # try int then float
        try:
            return NormalizedValue(
                raw_value=value, kind=NormalizationKind.NUMBER,
                normalized=int(s), quality=ValueQuality.NORMALIZED,
                uncertainty="parsed from string", detail="str_to_int",
            )
        except ValueError:
            pass
        try:
            f = float(s)
            return NormalizedValue(
                raw_value=value, kind=NormalizationKind.NUMBER,
                normalized=f, quality=ValueQuality.NORMALIZED,
                uncertainty="parsed from string", detail="str_to_float",
            )
        except ValueError:
            return NormalizedValue(
                raw_value=value, kind=NormalizationKind.UNSUPPORTED,
                normalized=None, quality=ValueQuality.UNSUPPORTED,
                uncertainty="not a number", detail="not_a_number",
            )
    return NormalizedValue._unsupported(value, "number", "non-numeric value")


# ---------------------------------------------------------------------------
# Dispatcher + stateless ValueNormalizer
# ---------------------------------------------------------------------------

#: Hint keywords -> normalizer kind.  A field *hint* is a lowercase column
#: name substring; the first match wins (ordered most-specific first).
_HINT_DATE = ("date", "dt", "start", "end", "onset", "onsetdate", "stopdate")
_HINT_UNIT = ("unit", "units", "uom")
_HINT_CODE_SEX = ("sex", "gender")
_HINT_CODE_SEV = ("severity", "sev", "grade", "ctcae")
_HINT_CODE_SER = ("serious", "seriousness")
_HINT_CODE_OUT = ("outcome", "aeout", "resolution")
_HINT_NUMBER = ("val", "value", "result", "num", "count", "age", "dose", "qty")


def _infer_kind_from_hint(hint: str) -> Tuple[str, str]:
    """Return (kind, code_set) from a column-name hint.

    kind is a :class:`NormalizationKind` constant; code_set is the synonym
    group for coded values (empty for non-coded kinds).
    """
    h = hint.lower()
    for kw in _HINT_DATE:
        if kw in h:
            return NormalizationKind.DATE, ""
    for kw in _HINT_UNIT:
        if kw in h:
            return NormalizationKind.UNIT, ""
    for kw in _HINT_CODE_SEX:
        if kw in h:
            return NormalizationKind.CODED, "sex"
    for kw in _HINT_CODE_SEV:
        if kw in h:
            return NormalizationKind.CODED, "severity"
    for kw in _HINT_CODE_SER:
        if kw in h:
            return NormalizationKind.CODED, "serious"
    for kw in _HINT_CODE_OUT:
        if kw in h:
            return NormalizationKind.CODED, "outcome"
    for kw in _HINT_NUMBER:
        if kw in h:
            return NormalizationKind.NUMBER, ""
    return NormalizationKind.TEXT, ""


def normalize_value(
    value: Any,
    *,
    hint: str = "",
    expected_kind: str = "",
) -> NormalizedValue:
    """Dispatch a raw value to the right normalizer.

    * ``expected_kind`` (explicit) takes precedence over ``hint`` inference.
    * When neither is given, the value is treated as text.
    * Always returns a :class:`NormalizedValue`; never raises on bad input
      (it returns an ``unsupported`` result instead).
    """
    kind = expected_kind or ""
    code_set = ""
    if not kind and hint:
        kind, code_set = _infer_kind_from_hint(hint)
    if not kind:
        kind = NormalizationKind.TEXT

    if kind == NormalizationKind.DATE:
        return normalize_date(value)
    if kind == NormalizationKind.PARTIAL_DATE:
        return normalize_partial_date(value)
    if kind == NormalizationKind.UNIT:
        return normalize_unit(value)
    if kind == NormalizationKind.CODED:
        return normalize_coded_value(value, code_set=code_set)
    if kind == NormalizationKind.NUMBER:
        return _normalize_number(value)
    return _normalize_text(value)


@dataclass(frozen=True)
class ValueNormalizer:
    """Stateless normalizer bound to a field hint + expected kind.

    Equivalent to calling :func:`normalize_value` with the same hints, but
    encapsulated so a field profile can carry its normalizer deterministically.
    """
    hint: str = ""
    expected_kind: str = ""
    code_set: str = ""

    def normalize(self, value: Any) -> NormalizedValue:
        if self.expected_kind == NormalizationKind.CODED:
            return normalize_coded_value(value, code_set=self.code_set)
        return normalize_value(
            value, hint=self.hint, expected_kind=self.expected_kind
        )
