from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app.main import app  # noqa: E402
from services.api.app.safety_pv_manifest import MY009_LISTING, RUX_274_ROOT, RUX_PV_ROOT, SafetyPvManifestService  # noqa: E402


@unittest.skipUnless(MY009_LISTING.exists(), "MY009 safety listing path is unavailable")
class SafetyPvManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = SafetyPvManifestService().build_manifest("proj_mgk10_sar_demo")

    def package(self, package_id: str):
        return next(package for package in self.manifest.packages if package.package_id == package_id)

    def test_my009_manifest_reads_primary_comparison_listing_and_keeps_teae_boundary(self):
        package = self.package("my009_uc_s1")

        self.assertGreaterEqual(len(package.listing_domains), 50)
        self.assertGreaterEqual(len(package.documents), 7)
        ae_domain = next(domain for domain in package.listing_domains if domain.sheet_name == "AE")
        self.assertEqual(27, ae_domain.row_count)
        self.assertEqual("不良事件", ae_domain.domain_label)
        self.assertIn("AETERM", ae_domain.key_fields)
        self.assertIn("AESER", ae_domain.key_fields)

        ae_candidate = next(candidate for candidate in package.signal_candidates if candidate.signal_type == "ae_medical_review_candidate")
        self.assertIn("8 条AE", ae_candidate.title)
        self.assertIn("4 条提示可能相关", ae_candidate.title)
        self.assertEqual("待医学/PV确认", ae_candidate.confirmation_status)
        self.assertIn("不构成最终安全性结论", ae_candidate.observation)

        gate_labels = {gate.gate_label for gate in package.quality_gates}
        self.assertIn("AE与TEAE口径待核对", gate_labels)
        self.assertIn("安全性分母口径待确认", gate_labels)

    @unittest.skipUnless(RUX_PV_ROOT.exists() and RUX_274_ROOT.exists(), "RUX safety source paths are unavailable")
    def test_rux_manifest_registers_pv_plan_and_274_without_listing_merge(self):
        package = self.package("rux_03_002_pv")

        self.assertEqual(0, len(package.listing_domains))
        self.assertTrue(any(document.document_type == "pv_plan" for document in package.documents))
        self.assertTrue(any(document.document_type == "clinical_safety_summary" for document in package.documents))
        self.assertEqual(1, len(package.signal_candidates))
        self.assertIn("PV计划与安全总结一致性核对候选", package.signal_candidates[0].signal_label)
        self.assertTrue(any(gate.gate_label == "RUX安全总结人群口径待确认" for gate in package.quality_gates))

    def test_safety_pv_manifest_endpoint_is_desensitized_and_does_not_claim_formal_pv_actions(self):
        response = TestClient(app).get("/api/projects/proj_mgk10_sar_demo/safety-pv/manifest")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        serialized = json.dumps(payload, ensure_ascii=False)

        self.assertEqual("安全信号与PV协同", payload["module_label"])
        self.assertEqual(2, payload["package_count"])
        self.assertGreaterEqual(payload["total_signal_candidates"], 5)
        for forbidden in [
            "/Users/",
            "第9环节",
            "阶段9",
            "Stage 9",
            "E2B",
            "监管clock",
            "case intake",
            "PV数据库写入",
            "正式PV判定",
            "final_seriousness",
            "final_expectedness",
            "final_causality",
            "pv_database_record_id",
        ]:
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
