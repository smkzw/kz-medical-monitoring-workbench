"""Listing layout classification — the anti-overfit presentation-form layer.

Classifies each table's data presentation form from its materialized rows:
wide (one row per record, fields as columns), long (one observation per row
with TEST/RESULT pairs), or matrix (entities spread across columns, e.g.
one column per subject or per visit). Recorded into a content-addressed
profile artifact and surfaced to the analysis models so a listing's shape
is explicit rather than assumed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from ..intelligence.primitives import content_hash

_TEST_COLUMN_HINTS = ("TEST", "指标名称", "项目名称", "PARAM")
_RESULT_COLUMN_HINTS = ("ORRES", "结果", "VALUE", "取值", "AVAL")
_ENTITY_KEY_HINTS = ("SUBJID", "受试者", "USUBJID", "受试者编号")

_WIDE = "wide_row_per_record"
_LONG = "long_observation_per_row"
_MATRIX = "matrix_entity_columns"

_VISIT_COLUMN_RE = re.compile(r"(?:V|访视|Visit)[0-9]{1,3}")


def classify_table_layout(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Classify one table's presentation form from its rows.

    Signals:
    - long: a test-name column + result column pair, with many rows sharing
      the same entity key (measurements stacked by row).
    - matrix: many symmetric visit/period columns per row (entities spread
      across columns) — e.g. one column per visit with no TEST column.
    - wide: the default one-row-per-record shape.
    """
    if not rows:
        return {"layout": _WIDE, "confidence": 0.0, "signals": ["empty"]}
    columns = list(rows[0].keys())
    col_upper = {str(c).upper(): c for c in columns}

    def _find(hints: Sequence[str]) -> str:
        for hint in hints:
            for upper, original in col_upper.items():
                if hint in upper:
                    return original
        return ""

    test_col = _find(_TEST_COLUMN_HINTS)
    result_col = _find(_RESULT_COLUMN_HINTS)
    entity_col = _find(_ENTITY_KEY_HINTS)

    signals: list[str] = []
    if test_col and result_col:
        signals.append(f"test/result pair: {test_col}+{result_col}")
    visit_like = [c for c in columns if _VISIT_COLUMN_RE.search(str(c))]
    if len(visit_like) >= 3:
        signals.append(f"{len(visit_like)} symmetric visit columns")

    if test_col and result_col and entity_col:
        # 行堆叠观察：同一受试者出现在大量行（每行一个测量）
        key_counts: dict[str, int] = {}
        for row in rows:
            key_counts[str(row.get(entity_col, ""))] = key_counts.get(
                str(row.get(entity_col, "")), 0
            ) + 1
        max_repeat = max(key_counts.values(), default=0)
        if max_repeat >= 5:
            signals.append(f"entity rows repeat up to {max_repeat}x")
            return {
                "layout": _LONG,
                "confidence": min(0.9, 0.5 + max_repeat / max(1, len(key_counts))),
                "signals": signals,
                "test_column": test_col,
                "result_column": result_col,
                "entity_column": entity_col,
            }
    if len(visit_like) >= 3 and not (test_col and result_col):
        return {
            "layout": _MATRIX,
            "confidence": min(0.9, 0.4 + 0.1 * len(visit_like)),
            "signals": signals,
            "visit_columns": len(visit_like),
        }
    return {"layout": _WIDE, "confidence": 0.8, "signals": signals or ["default wide"]}


def build_layout_profile(domains: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Classify every materialized table into a content-addressed profile."""

    tables: dict[str, dict[str, Any]] = {}
    layout_counts: dict[str, int] = {}
    for table, rows in sorted(domains.items()):
        info = classify_table_layout(rows)
        info["row_count"] = len(rows)
        info["column_count"] = len(rows[0]) if rows else 0
        tables[table] = info
        layout_counts[info["layout"]] = layout_counts.get(info["layout"], 0) + 1
    profile = {
        "kind": "listing_layout_profile",
        "layout_counts": layout_counts,
        "tables": tables,
    }
    profile["content_sha256"] = content_hash(profile)
    return profile


def layout_artifact_path(workspace: Path) -> Path:
    return workspace / "runtime" / "artifacts" / "listing-layout.json"


def layout_summary_for_contract(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Compact per-table layout note injected into analysis subject_context."""

    tables = profile.get("tables", {})
    layout_notes = {
        _LONG: "按行堆叠呈现（每行一条测量，测试名+结果成对列）",
        _MATRIX: "矩阵式呈现（实体/访视展开为列）",
        _WIDE: "按列排宽表（每行一条记录，字段为列）",
    }
    by_layout: dict[str, list[str]] = {}
    for table, info in tables.items():
        by_layout.setdefault(info.get("layout", _WIDE), []).append(table)
    return {
        "presentation_note_zh": {
            layout: {
                "tables": tables_list[:12],
                "note": layout_notes[layout],
            }
            for layout, tables_list in sorted(by_layout.items())
        },
        "reading_rule_zh": (
            "阅读证据时先看该表呈现形态：长表同一受试者的多次测量分散在多行，"
            "矩阵表的数值按列分属不同实体/访视——不要把行数当成受试者数。"
        ),
    }


__all__ = [
    "build_layout_profile",
    "classify_table_layout",
    "layout_artifact_path",
    "layout_summary_for_contract",
]
