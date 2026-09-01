from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app.main import app  # noqa: E402
from services.api.app.medical_writing_manifest import (  # noqa: E402
    D001_PROTOCOL_DOCX,
    RUX_PROTOCOL_DOCX,
    MedicalWritingManifestService,
)


@unittest.skipUnless(
    RUX_PROTOCOL_DOCX.exists() and D001_PROTOCOL_DOCX.exists(),
    "real protocol DOCX fixtures are unavailable",
)
class MedicalWritingManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.manifest = MedicalWritingManifestService().build_manifest("proj_mgk10_sar_demo")

    def test_manifest_parses_real_protocol_docx_files(self):
        self.assertEqual("医学写作", self.manifest.module_label)
        self.assertEqual(2, self.manifest.package_count)
        self.assertGreaterEqual(self.manifest.total_source_spans, 4500)
        self.assertGreaterEqual(self.manifest.total_tables, 40)

        docs = [package.documents[0] for package in self.manifest.packages]
        by_protocol_id = {doc.protocol_identifier: doc for doc in docs}
        self.assertIn("RUX-03-002", by_protocol_id)
        self.assertIn("D001-02-002", by_protocol_id)
        self.assertGreaterEqual(by_protocol_id["RUX-03-002"].paragraph_count, 1900)
        self.assertGreaterEqual(by_protocol_id["D001-02-002"].paragraph_count, 2700)
        self.assertEqual("正文已解析", by_protocol_id["RUX-03-002"].parser_status)
        self.assertEqual("正文已解析", by_protocol_id["D001-02-002"].parser_status)

    def test_manifest_exposes_conservative_sections_tables_and_quality_gates(self):
        for package in self.manifest.packages:
            self.assertTrue(package.sections)
            self.assertTrue(package.tables)
            self.assertTrue(any(section.requires_human_mapping for section in package.sections))
            self.assertTrue(any(table.role_hint == "研究流程/SoA候选" for table in package.tables))
            self.assertTrue(any(table.quality_notes for table in package.tables))
            gate_by_label = {gate.gate_label: gate for gate in package.quality_gates}
            self.assertEqual("ok", gate_by_label["来源绑定完整性"].status)
            self.assertIn(gate_by_label["AI修订线程已关闭"].status, {"blocked", "warning"})
            self.assertEqual("blocked", gate_by_label["导出元数据齐备"].status)
            self.assertEqual("ok", gate_by_label["禁用表述扫描通过"].status)

    def test_manifest_payload_has_no_local_path_lifecycle_or_overclaim(self):
        payload = self.manifest.model_dump(mode="json")
        serialized = json.dumps(payload, ensure_ascii=False)
        forbidden = [
            "/Users/",
            "第8环节",
            "阶段8",
            "Stage 8",
            "AI 已完成正式方案",
            "自动定稿",
            "可直接提交监管",
            "正式方案已生成",
            "最终医学结论",
            "监管认可",
            "疗效最优",
            "首选方案",
            "竞品证明",
        ]
        for fragment in forbidden:
            self.assertNotIn(fragment, serialized)
        self.assertIn("待医学批准", serialized)
        self.assertIn("不可生成正式导出包", serialized)
        self.assertIn("codex_runtime_dependency=false", serialized)

    def test_manifest_endpoint_returns_same_scope(self):
        response = self.client.get("/api/projects/proj_mgk10_sar_demo/medical-writing/manifest")
        self.assertEqual(200, response.status_code, response.text)
        payload = response.json()
        self.assertEqual("医学写作", payload["module_label"])
        self.assertEqual(2, payload["package_count"])
        self.assertGreaterEqual(payload["total_source_spans"], 4500)
        self.assertFalse("/Users/" in json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
