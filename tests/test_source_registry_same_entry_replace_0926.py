"""20260926回归：source registry同entry_id二次注册必须原位替换（护栏3）。

背景：文档权威promotion对同content→同entry_id的文件重复注册时，
_commit按provenance差异把它当新行追加，list_spans对同一entry累计多份
spans，破坏locator index sha不变量，文档权威readiness永久false
（SAR重跑阶段2实测）。修复后：同entry_id提交=原位替换spans+entry；
不同entry_id照旧追加；历史遗留重复行收敛到最早一行。
"""

from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app.source_intake import (  # noqa: E402
    SourceRegistryEntry,
    SourceRegistrySpan,
    SourceRegistryStore,
    SourceRegistrationResult,
)


def _result(entry_id: str, parser_version: str, span_count: int = 3) -> SourceRegistrationResult:
    now = datetime(2026, 9, 26, tzinfo=timezone.utc)
    entry = SourceRegistryEntry(
        entry_id=entry_id,
        project_id="proj_test_replace",
        module="medical_monitoring",
        source_kind="ecrf_document",
        public_title="doc.pdf",
        content_hash="a" * 64,
        size_bytes=123,
        parser_status="parsed",
        parser_version=parser_version,
        span_count=span_count,
        metadata={
            "filename": "doc.pdf",
            "parser_version": parser_version,
            "expected_locator_count": span_count,
            "expected_locator_index_sha256": "pending",
            "locator_manifest_complete": True,
            "monitoring_authority_status": "promoted",
        },
        created_at=now,
    )
    spans = [
        SourceRegistrySpan(
            source_id=f"{entry_id}_{index:04d}",
            entry_id=entry_id,
            project_id="proj_test_replace",
            module="medical_monitoring",
            source_type="ecrf_span",
            title="doc.pdf",
            locator=f"upload:candidate:x:p1:b{index}",
            text_preview=f"text {index}",
            created_at=now,
        )
        for index in range(1, span_count + 1)
    ]
    return SourceRegistrationResult(entry=entry, spans=spans)


class SameEntryReplaceTest(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.jsonl = Path(self._tmp.name) / "source_registry.jsonl"
        self.store = SourceRegistryStore(self.jsonl)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_same_entry_id_recommit_replaces_in_place(self) -> None:
        first = _result("src_x_ecrf_1", "pymupdf-september")
        self.store.append(first)
        self.assertEqual(len(self.store.list_results("proj_test_replace")), 1)

        # provenance漂移的同content重注册（同entry_id、不同parser版本）
        second = _result("src_x_ecrf_1", "monitoring-candidate-ocr-v1")
        self.store.append(second)

        results = self.store.list_results("proj_test_replace")
        self.assertEqual(
            len(results), 1, "同entry_id二次提交必须原位替换而非追加新行"
        )
        self.assertEqual(
            results[0].entry.parser_version,
            "monitoring-candidate-ocr-v1",
            "应替换为新provenance",
        )
        spans = self.store.list_spans("proj_test_replace")
        self.assertEqual(
            len(spans), 3, "spans不得跨提交累计（locator index不变量）"
        )
        self.assertEqual(len({s.source_id for s in spans}), 3)

    def test_different_entry_id_still_appends(self) -> None:
        self.store.append(_result("src_x_ecrf_1", "pv1"))
        self.store.append(_result("src_x_ecrf_2", "pv1"))
        self.assertEqual(len(self.store.list_results("proj_test_replace")), 2)

    def test_historical_duplicate_lines_converge(self) -> None:
        # 直接构造历史遗留的重复行（同entry_id两行），再提交任一新结果
        first = _result("src_x_ecrf_1", "pymupdf-september")
        self.store.append(first)
        self.store.append(_result("src_other_1", "pv1"))
        raw = self.jsonl.read_text(encoding="utf-8")
        lines = raw.splitlines()
        duplicate_first = next(l for l in lines if "src_x_ecrf_1" in l)
        self.jsonl.write_text(
            raw + duplicate_first + "\n", encoding="utf-8"
        )
        self.store.append(_result("src_y_ecrf_1", "pv1"))
        remaining = [
            json.loads(l)["entry"]["entry_id"]
            for l in self.jsonl.read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]
        self.assertEqual(remaining.count("src_x_ecrf_1"), 1, "历史重复行应收敛到一行")
        self.assertIn("src_other_1", remaining)
        self.assertIn("src_y_ecrf_1", remaining)


if __name__ == "__main__":
    unittest.main()
