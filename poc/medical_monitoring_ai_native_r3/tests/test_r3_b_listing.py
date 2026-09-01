"""R3-B listing structure profiler tests.

Profiles three heterogeneous listing shapes (single-table wide AE, long
key-value labs, multi-table workbook) and verifies field roles, shapes,
content-addressing and anti-hardcoding.
"""

from __future__ import annotations

import pytest

from mm_r3.listing import (
    FIELD_ROLES,
    FieldProfile,
    FieldRole,
    ListingProfileError,
    TableProfile,
    TableShapeKind,
    WorkbookProfile,
    profile_table,
    profile_workbook,
)


# ===========================================================================
# Single-table wide AE listing
# ===========================================================================

class TestSingleTableWideAE:
    def setup_method(self):
        self.descriptor = {
            "kind": "single_table",
            "table": {
                "name": "AE",
                "columns": ["SUBJECT", "AE_TERM", "AE_START", "AE_END", "SEVERITY", "SERIOUS"],
                "rows": [
                    {"SUBJECT": "S001", "AE_TERM": "Nausea", "AE_START": "2026-02-01",
                     "AE_END": "2026-02-03", "SEVERITY": "Mild", "SERIOUS": "No"},
                    {"SUBJECT": "S002", "AE_TERM": "Headache", "AE_START": "2026-02-02",
                     "AE_END": "", "SEVERITY": "Moderate", "SERIOUS": "No"},
                ],
            },
        }
        self.wb = profile_workbook("proj-alpha", "rev-listing-wide-ae", self.descriptor)

    def test_binds_source_revision(self):
        assert self.wb.source_revision_id == "rev-listing-wide-ae"
        assert self.wb.project_id == "proj-alpha"

    def test_is_single_table(self):
        assert self.wb.is_single_table is True
        assert self.wb.n_tables == 1

    def test_field_count(self):
        t = self.wb.tables[0]
        assert t.n_columns == 6
        assert len(t.fields) == 6

    def test_identifier_detected(self):
        t = self.wb.tables[0]
        assert "SUBJECT" in t.identifier_candidates
        subj = t.field("SUBJECT")
        assert subj.role == FieldRole.IDENTIFIER

    def test_date_fields_detected(self):
        t = self.wb.tables[0]
        assert "AE_START" in t.date_candidates
        assert "AE_END" in t.date_candidates

    def test_shape_wide(self):
        t = self.wb.tables[0]
        assert t.shape == TableShapeKind.WIDE

    def test_content_hash_deterministic(self):
        wb2 = profile_workbook("proj-alpha", "rev-listing-wide-ae", self.descriptor)
        assert self.wb.content_hash == wb2.content_hash

    def test_missing_ratio_computed(self):
        ae_end = self.wb.tables[0].field("AE_END")
        assert ae_end.n_values == 2
        assert ae_end.n_missing == 1
        assert ae_end.missing_ratio == 0.5


# ===========================================================================
# Long key-value labs listing
# ===========================================================================

class TestLongKeyValueLabs:
    def setup_method(self):
        self.descriptor = {
            "kind": "single_table",
            "table": {
                "name": "LB",
                "columns": ["SUBJECT", "PARAM", "PARAMCD", "VAL", "UNIT", "DAY"],
                "rows": [
                    {"SUBJECT": "S001", "PARAM": "ALT", "PARAMCD": "ALT", "VAL": "45", "UNIT": "U/L", "DAY": "1"},
                    {"SUBJECT": "S001", "PARAM": "AST", "PARAMCD": "AST", "VAL": "30", "UNIT": "U/L", "DAY": "1"},
                ],
            },
        }
        self.wb = profile_workbook("proj-beta", "rev-listing-long-labs", self.descriptor)

    def test_shape_long(self):
        t = self.wb.tables[0]
        assert t.shape == TableShapeKind.LONG

    def test_measure_detected(self):
        t = self.wb.tables[0]
        # VAL column should be a measure candidate
        assert "VAL" in t.measure_candidates

    def test_unit_field_role(self):
        unit = self.wb.tables[0].field("UNIT")
        assert unit.role == FieldRole.UNIT

    def test_param_not_identifier(self):
        param = self.wb.tables[0].field("PARAM")
        assert param.role != FieldRole.IDENTIFIER


# ===========================================================================
# Multi-table workbook
# ===========================================================================

class TestMultiTableWorkbook:
    def setup_method(self):
        self.descriptor = {
            "kind": "multi_table",
            "tables": [
                {"name": "DM", "columns": ["SUBJECT", "SEX", "AGE"],
                 "rows": [{"SUBJECT": "S001", "SEX": "F", "AGE": "42"}]},
                {"name": "AE", "columns": ["SUBJECT", "AE_TERM"],
                 "rows": [{"SUBJECT": "S001", "AE_TERM": "Fatigue"}]},
            ],
        }
        self.wb = profile_workbook("proj-gamma", "rev-listing-workbook-multi", self.descriptor)

    def test_two_tables(self):
        assert self.wb.n_tables == 2
        assert {t.name for t in self.wb.tables} == {"DM", "AE"}

    def test_table_lookup(self):
        assert self.wb.table("DM") is not None
        assert self.wb.table("MISSING") is None

    def test_total_counts(self):
        assert self.wb.n_total_rows == 2
        assert self.wb.n_total_columns == 5  # 3 + 2

    def test_each_table_profiles_independently(self):
        dm = self.wb.table("DM")
        ae = self.wb.table("AE")
        assert "AGE" in dm.measure_candidates
        assert "AE_TERM" in [f.name for f in ae.fields]


# ===========================================================================
# Bare table dict
# ===========================================================================

class TestBareTable:
    def test_bare_table_treated_as_single(self):
        wb = profile_workbook("p", "rev", {"name": "X", "columns": ["A", "B"], "rows": []})
        assert wb.is_single_table is True
        assert wb.tables[0].name == "X"


# ===========================================================================
# Explicit column values (no rows)
# ===========================================================================

class TestExplicitColumnValues:
    def test_columns_with_values(self):
        wb = profile_workbook("p", "rev", {
            "kind": "single_table",
            "table": {
                "name": "T",
                "columns": [
                    {"name": "SUBJECT", "values": ["S001", "S002", "S003"]},
                    {"name": "AGE", "values": [42, 55, 38]},
                ],
            },
        })
        t = wb.tables[0]
        assert t.n_rows == 3
        assert "SUBJECT" in t.identifier_candidates


class TestContentAddressing:
    def test_different_structure_different_hash(self):
        # a structure profile captures shape (columns/roles), not row values.
        # Different structure -> different hash.
        d1 = {"kind": "single_table", "table": {"name": "T", "columns": ["SUBJECT", "AE_TERM"], "rows": []}}
        d2 = {"kind": "single_table", "table": {"name": "T", "columns": ["SUBJECT", "AGE"], "rows": []}}
        wb1 = profile_workbook("p", "rev", d1)
        wb2 = profile_workbook("p", "rev", d2)
        assert wb1.content_hash != wb2.content_hash

    def test_same_structure_same_hash(self):
        # same structure, different row values -> same structural hash
        d1 = {"kind": "single_table", "table": {"name": "T", "columns": ["A"], "rows": [{"A": "1"}]}}
        d2 = {"kind": "single_table", "table": {"name": "T", "columns": ["A"], "rows": [{"A": "2"}]}}
        wb1 = profile_workbook("p", "rev", d1)
        wb2 = profile_workbook("p", "rev", d2)
        assert wb1.content_hash == wb2.content_hash

    def test_same_structure_across_revisions_and_row_growth_same_hash(self):
        d1 = {
            "kind": "single_table",
            "table": {
                "name": "T", "columns": ["SUBJECT", "AGE"],
                "rows": [{"SUBJECT": "S1", "AGE": 40}],
            },
        }
        d2 = {
            "kind": "single_table",
            "table": {
                "name": "T", "columns": ["SUBJECT", "AGE"],
                "rows": [
                    {"SUBJECT": "S1", "AGE": 40},
                    {"SUBJECT": "S2", "AGE": 41},
                ],
            },
        }
        wb1 = profile_workbook("project-1", "rev-1", d1)
        wb2 = profile_workbook("project-2", "rev-2", d2)
        assert wb1.source_revision_id != wb2.source_revision_id
        assert wb1.content_hash == wb2.content_hash

    def test_derived_counts_cannot_be_fabricated(self):
        table = profile_table({
            "name": "T", "columns": ["A", "B"],
            "rows": [{"A": 1, "B": 2}],
        })
        wb = WorkbookProfile(
            profile_id="wb-1", project_id="p", source_revision_id="rev",
            tables=(table,), n_tables=99, n_total_rows=99,
            n_total_columns=99,
        )
        assert wb.n_tables == 1
        assert wb.n_total_rows == 1
        assert wb.n_total_columns == 2

    def test_declared_hash_mismatch_rejected(self):
        with pytest.raises(ListingProfileError):
            TableProfile(
                name="T", shape=TableShapeKind.UNKNOWN,
                content_hash="0" * 64,
            )

    def test_workbook_immutable(self):
        wb = profile_workbook("p", "rev", {"name": "T", "columns": ["A"], "rows": []})
        with pytest.raises(Exception):
            wb.project_id = "x"  # type: ignore[misc]


# ===========================================================================
# Validation errors
# ===========================================================================

class TestValidationErrors:
    def test_empty_columns_rejected(self):
        with pytest.raises(ListingProfileError):
            profile_table({"name": "T", "columns": []})

    def test_column_without_name_rejected(self):
        with pytest.raises(ListingProfileError):
            profile_table({"name": "T", "columns": [{"values": [1]}]})

    def test_invalid_role_rejected(self):
        with pytest.raises(ListingProfileError):
            FieldProfile(name="X", role="bogus")

    def test_invalid_shape_rejected(self):
        with pytest.raises(ListingProfileError):
            TableProfile(name="T", shape="bogus")

    def test_missing_ratio_range_validated(self):
        with pytest.raises(ListingProfileError):
            FieldProfile(name="X", missing_ratio=1.5)

    def test_n_missing_exceeds_n_values_rejected(self):
        with pytest.raises(ListingProfileError):
            FieldProfile(name="X", n_values=5, n_missing=10)


# ===========================================================================
# Anti-hardcoding: profile of fixtures-style shapes, no project names
# ===========================================================================

class TestAntiHardcoding:
    def test_no_project_name_in_profile_payload(self):
        wb = profile_workbook("proj-alpha", "rev1", {
            "kind": "single_table",
            "table": {"name": "AE", "columns": ["SUBJECT", "AE_TERM"],
                      "rows": [{"SUBJECT": "S001", "AE_TERM": "X"}]},
        })
        payload = str(wb.canonical_payload())
        # the project_id appears (it is generic), but no real-project tokens
        for token in ("RUX", "MGK10", "MY009", "MY008", "芦可替尼"):
            assert token not in payload

    def test_all_field_roles_are_known(self):
        wb = profile_workbook("p", "rev", {
            "kind": "single_table",
            "table": {"name": "T", "columns": ["SUBJECT", "X"], "rows": [{"SUBJECT": "S1", "X": "v"}]},
        })
        for t in wb.tables:
            for f in t.fields:
                assert f.role in FIELD_ROLES
