"""R3-B normalization tests: date/unit/coding/partial-date/missing/duplicate.

Deterministic, stdlib-only.  Every test asserts that the original raw value is
retained, the normalized value is canonical, and explicit uncertainty is
surfaced (never silently dropped).
"""

from __future__ import annotations

import pytest

from mm_r3.normalization import (
    NORMALIZATION_KINDS,
    VALUE_QUALITIES,
    NormalizationKind,
    NormalizedValue,
    ValueNormalizer,
    ValueQuality,
    detect_duplicate,
    is_missing,
    normalize_coded_value,
    normalize_date,
    normalize_partial_date,
    normalize_unit,
    normalize_value,
)


# ===========================================================================
# Missing / unknown detection
# ===========================================================================

class TestMissingDetection:
    @pytest.mark.parametrize("v", [None, "", "   ", "UN", "unk", "UNK", "UNKNOWN",
                                   "N/A", "na", "NOT DONE", "ND", "NOT APPLICABLE"])
    def test_recognized_missing(self, v):
        assert is_missing(v) is True

    @pytest.mark.parametrize("v", ["0", 0, 0.0, "S001", "2026-02-01", False, True])
    def test_not_missing(self, v):
        # bool False / numeric 0 are real values, not missing
        assert is_missing(v) is False

    def test_whitespace_only_is_missing(self):
        assert is_missing(" \t\n ") is True


# ===========================================================================
# Date normalization
# ===========================================================================

class TestDateNormalization:
    def test_full_iso_date_exact(self):
        nv = normalize_date("2026-02-01")
        assert nv.kind == NormalizationKind.DATE
        assert nv.normalized == "2026-02-01"
        assert nv.quality == ValueQuality.EXACT
        assert nv.uncertainty == ""
        assert nv.raw_value == "2026-02-01"

    def test_separated_ymd_normalized(self):
        nv = normalize_date("2026/2/1")
        assert nv.kind == NormalizationKind.DATE
        assert nv.normalized == "2026-02-01"
        assert nv.quality == ValueQuality.NORMALIZED
        assert nv.raw_value == "2026/2/1"

    def test_chinese_ymd_normalized(self):
        nv = normalize_date("2026年2月1日")
        assert nv.kind == NormalizationKind.DATE
        assert nv.normalized == "2026-02-01"
        assert nv.quality == ValueQuality.NORMALIZED
        assert nv.raw_value == "2026年2月1日"

    def test_invalid_chinese_ymd_rejected(self):
        nv = normalize_date("2026年2月30日")
        assert nv.kind == NormalizationKind.PARTIAL_DATE
        assert nv.quality == ValueQuality.AMBIGUOUS
        assert nv.normalized == ""

    def test_dmy_is_ambiguous(self):
        # 01/02/2026 is day-first ambiguous without a locale
        nv = normalize_date("01/02/2026")
        assert nv.kind == NormalizationKind.DATE
        assert nv.normalized == "2026-02-01"
        assert nv.quality == ValueQuality.AMBIGUOUS
        assert "ambiguous" in nv.uncertainty

    def test_invalid_calendar_date_rejected(self):
        nv = normalize_date("2026-02-30")
        assert nv.kind == NormalizationKind.PARTIAL_DATE
        assert nv.quality == ValueQuality.AMBIGUOUS
        assert nv.normalized == ""

    def test_feb_29_leap_vs_nonleap(self):
        assert normalize_date("2024-02-29").quality == ValueQuality.EXACT
        assert normalize_date("2023-02-29").quality == ValueQuality.AMBIGUOUS

    def test_partial_yyyy_mm(self):
        nv = normalize_date("2026-02")
        assert nv.kind == NormalizationKind.PARTIAL_DATE
        assert nv.normalized == "2026-02"
        assert nv.quality == ValueQuality.PARTIAL
        assert "day" in nv.uncertainty

    def test_partial_yyyy(self):
        nv = normalize_date("2026")
        assert nv.kind == NormalizationKind.PARTIAL_DATE
        assert nv.normalized == "2026"
        assert nv.quality == ValueQuality.PARTIAL
        assert "month and day" in nv.uncertainty

    def test_partial_unk_day(self):
        nv = normalize_date("2026-02-UNK")
        assert nv.kind == NormalizationKind.PARTIAL_DATE
        assert nv.normalized == "2026-02"
        assert nv.quality == ValueQuality.PARTIAL
        assert "day" in nv.uncertainty

    def test_partial_unk_month(self):
        nv = normalize_date("2026-UNK-05")
        assert nv.kind == NormalizationKind.PARTIAL_DATE
        assert nv.normalized == "2026"
        assert "month" in nv.uncertainty

    def test_partial_all_unknown_components(self):
        nv = normalize_date("UNK-UNK-UNK")
        # year is UNK so no prefix is built
        assert nv.kind == NormalizationKind.PARTIAL_DATE
        assert nv.quality == ValueQuality.PARTIAL

    def test_missing_date(self):
        nv = normalize_date("")
        assert nv.kind == NormalizationKind.MISSING
        assert nv.quality == ValueQuality.MISSING

    def test_missing_via_unk(self):
        nv = normalize_date("UNK")
        # "UNK" alone is a recognized missing sentinel
        assert nv.kind == NormalizationKind.MISSING

    def test_unrecognized_format_unsupported(self):
        nv = normalize_date("Feb 1 2026")
        assert nv.kind == NormalizationKind.UNSUPPORTED
        assert nv.quality == ValueQuality.UNSUPPORTED

    def test_non_string_unsupported(self):
        nv = normalize_date(12345)
        assert nv.kind == NormalizationKind.UNSUPPORTED


class TestPartialDateAlias:
    def test_complete_date_as_partial_reports_full(self):
        nv = normalize_partial_date("2026-02-01")
        assert nv.kind == NormalizationKind.PARTIAL_DATE
        assert nv.normalized == "2026-02-01"
        assert "complete" in nv.uncertainty

    def test_partial_stays_partial(self):
        nv = normalize_partial_date("2026-02")
        assert nv.kind == NormalizationKind.PARTIAL_DATE
        assert nv.quality == ValueQuality.PARTIAL


# ===========================================================================
# Unit normalization
# ===========================================================================

class TestUnitNormalization:
    @pytest.mark.parametrize("raw,expected", [
        ("U/L", "U/L"),
        ("u/l", "U/L"),
        ("iu/l", "U/L"),
        ("IU/L", "U/L"),
        ("units/l", "U/L"),
        ("mg/dL", "mg/dL"),
        ("mg/dl", "mg/dL"),
        ("10^3/ul", "10^9/L"),
        ("kg/m2", "kg/m^2"),
        ("mmHg", "mmHg"),
        ("mmhg", "mmHg"),
        ("mcg", "ug"),
        ("μg", "ug"),
        ("µg", "ug"),
    ])
    def test_canonical_units(self, raw, expected):
        nv = normalize_unit(raw)
        assert nv.kind == NormalizationKind.UNIT
        assert nv.normalized == expected

    def test_exact_unit_no_uncertainty(self):
        nv = normalize_unit("U/L")
        assert nv.quality == ValueQuality.EXACT
        assert nv.uncertainty == ""

    def test_normalized_unit_quality(self):
        nv = normalize_unit("iu/l")
        assert nv.quality == ValueQuality.NORMALIZED
        assert nv.raw_value == "iu/l"

    def test_unrecognized_unit_passthrough_with_uncertainty(self):
        nv = normalize_unit("widgets/L")
        assert nv.kind == NormalizationKind.UNIT
        assert nv.normalized == "widgets/L"
        assert nv.quality == ValueQuality.AMBIGUOUS
        assert "not in canonical table" in nv.uncertainty

    def test_microlitre_per_litre_is_not_misread_as_enzyme_units(self):
        nv = normalize_unit("uL/L")
        assert nv.normalized == "uL/L"
        assert nv.quality == ValueQuality.AMBIGUOUS
        assert nv.normalized != "U/L"

    def test_missing_unit(self):
        assert normalize_unit("").kind == NormalizationKind.MISSING
        assert normalize_unit(None).kind == NormalizationKind.MISSING

    def test_whitespace_collapsed(self):
        nv = normalize_unit("  mg /  dL  ")
        assert nv.normalized == "mg/dL"


# ===========================================================================
# Coded value normalization
# ===========================================================================

class TestCodedNormalization:
    def test_sex_synonyms(self):
        assert normalize_coded_value("m", code_set="sex").normalized == "Male"
        assert normalize_coded_value("F", code_set="sex").normalized == "Female"
        assert normalize_coded_value("male", code_set="sex").normalized == "Male"
        assert normalize_coded_value("男", code_set="sex").normalized == "Male"
        assert normalize_coded_value("女", code_set="sex").normalized == "Female"

    def test_severity_synonyms(self):
        assert normalize_coded_value("mild", code_set="severity").normalized == "Mild"
        assert normalize_coded_value("2", code_set="severity").normalized == "Moderate"
        assert normalize_coded_value("Severe", code_set="severity").normalized == "Severe"
        assert normalize_coded_value("轻度", code_set="severity").normalized == "Mild"
        assert normalize_coded_value("中度", code_set="severity").normalized == "Moderate"
        assert normalize_coded_value("重度", code_set="severity").normalized == "Severe"

    def test_boolean_synonyms(self):
        assert normalize_coded_value("yes").normalized == "Yes"
        assert normalize_coded_value("Y").normalized == "Yes"
        assert normalize_coded_value("true").normalized == "Yes"
        assert normalize_coded_value("0").normalized == "No"
        assert normalize_coded_value("FALSE").normalized == "No"

    def test_python_bool(self):
        nv = normalize_coded_value(True)
        assert nv.normalized == "Yes"
        assert nv.quality == ValueQuality.EXACT

    def test_unrecognized_code_passthrough(self):
        nv = normalize_coded_value("Purple", code_set="severity")
        assert nv.normalized == "Purple"
        assert nv.quality == ValueQuality.AMBIGUOUS
        assert "not in code_set" in nv.uncertainty

    def test_missing_code(self):
        assert normalize_coded_value("").kind == NormalizationKind.MISSING
        assert normalize_coded_value("UNK").kind == NormalizationKind.MISSING


# ===========================================================================
# Dispatcher (normalize_value / ValueNormalizer)
# ===========================================================================

class TestDispatcher:
    def test_hint_infers_date(self):
        nv = normalize_value("2026-02-01", hint="AE_START")
        assert nv.kind == NormalizationKind.DATE

    def test_hint_infers_unit(self):
        nv = normalize_value("mg/dL", hint="RESULT_UNIT")
        assert nv.kind == NormalizationKind.UNIT

    def test_hint_infers_coded_sex(self):
        nv = normalize_value("M", hint="SEX")
        assert nv.kind == NormalizationKind.CODED
        assert nv.normalized == "Male"

    def test_hint_infers_number(self):
        nv = normalize_value("45", hint="AGE")
        assert nv.kind == NormalizationKind.NUMBER
        assert nv.normalized == 45

    def test_expected_kind_overrides_hint(self):
        nv = normalize_value("2026", hint="AGE", expected_kind=NormalizationKind.DATE)
        assert nv.kind == NormalizationKind.PARTIAL_DATE

    def test_text_fallback(self):
        nv = normalize_value("some narrative", hint="NOTES")
        assert nv.kind == NormalizationKind.TEXT
        assert nv.normalized == "some narrative"

    def test_value_normalizer_bound(self):
        vn = ValueNormalizer(hint="SEX")
        nv = vn.normalize("F")
        assert nv.normalized == "Female"


# ===========================================================================
# Duplicate detection
# ===========================================================================

class TestDuplicateDetection:
    def test_first_occurrence_not_dup(self):
        seen = set()
        is_dup, key = detect_duplicate("S001", seen=seen)
        assert is_dup is False
        assert key is not None

    def test_second_occurrence_is_dup(self):
        seen = set()
        detect_duplicate("S001", seen=seen)
        is_dup, _ = detect_duplicate("S001", seen=seen)
        assert is_dup is True

    def test_display_only_collapses(self):
        seen = set()
        detect_duplicate("S001", seen=seen)
        is_dup, _ = detect_duplicate(" s001 ", seen=seen)
        assert is_dup is True

    def test_distinct_not_dup(self):
        seen = set()
        detect_duplicate("S001", seen=seen)
        is_dup, _ = detect_duplicate("S002", seen=seen)
        assert is_dup is False

    def test_missing_never_dup(self):
        seen = set()
        detect_duplicate("S001", seen=seen)
        is_dup, key = detect_duplicate("", seen=seen)
        assert is_dup is False
        assert key is None

    def test_no_seen_returns_key_only(self):
        is_dup, key = detect_duplicate("S001")
        assert is_dup is False
        assert key is not None


# ===========================================================================
# NormalizedValue invariants
# ===========================================================================

class TestNormalizedValueInvariants:
    def test_raw_value_always_retained(self):
        nv = normalize_date("2026/2/1")
        assert nv.raw_value == "2026/2/1"
        assert nv.normalized == "2026-02-01"

    def test_exact_forbids_uncertainty(self):
        with pytest.raises(ValueError):
            NormalizedValue(
                raw_value="x", kind=NormalizationKind.TEXT,
                normalized="x", quality=ValueQuality.EXACT,
                uncertainty="should not be here",
            )

    def test_partial_requires_uncertainty(self):
        with pytest.raises(ValueError):
            NormalizedValue(
                raw_value="2026", kind=NormalizationKind.PARTIAL_DATE,
                normalized="2026", quality=ValueQuality.PARTIAL,
                uncertainty="",
            )

    def test_invalid_kind_rejected(self):
        with pytest.raises(ValueError):
            NormalizedValue(
                raw_value="x", kind="bogus",
                quality=ValueQuality.EXACT,
            )

    def test_immutable(self):
        nv = normalize_date("2026-02-01")
        with pytest.raises(Exception):
            nv.normalized = "hacked"  # type: ignore[misc]

    def test_is_missing_property(self):
        assert normalize_date("").is_missing is True
        assert normalize_date("2026-02-01").is_missing is False

    def test_content_hash_deterministic(self):
        nv1 = normalize_unit("iu/l")
        nv2 = normalize_unit("iu/l")
        assert nv1.content_hash() == nv2.content_hash()

    def test_all_kinds_and_qualities_validated(self):
        # sanity: the enumeration tuples are non-empty and stable
        assert NormalizationKind.DATE in NORMALIZATION_KINDS
        assert ValueQuality.EXACT in VALUE_QUALITIES
