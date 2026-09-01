from __future__ import annotations

import json
import unittest

from services.api.app.project_source_manifest import (
    MEDICAL_MODULE_LABELS,
    ProjectSourceManifestService,
)

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - minimal runtimes can skip route checks.
    TestClient = None


FORBIDDEN_PUBLIC_TOKENS = (
    "/Users/",
    "source_path",
    "server_path",
    "content_hash",
    "preview_hash",
    "storage_key",
    "internal_path",
)


class ProjectSourceManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ProjectSourceManifestService()

    def assert_public_payload_is_sanitized(self, payload: dict) -> None:
        serialized = json.dumps(payload, ensure_ascii=False)
        for token in FORBIDDEN_PUBLIC_TOKENS:
            self.assertNotIn(token, serialized)

    def test_manifest_covers_demo_and_three_real_project_families(self) -> None:
        manifests = {
            project_id: self.service.public_manifest(project_id)
            for project_id in (
                "proj_mgk10_sar_demo",
                "proj_rux_03_002",
                "d001_raw_intake",
                "my009_uc_monitoring_raw",
            )
        }

        self.assertEqual("MG-K10-SAR-DEMO", manifests["proj_mgk10_sar_demo"]["header_project"]["project_code"])
        self.assertEqual("RUX-03-002", manifests["proj_rux_03_002"]["header_project"]["project_code"])
        self.assertEqual("CMS-D001", manifests["d001_raw_intake"]["header_project"]["project_code"])
        self.assertEqual("MY009-UC", manifests["my009_uc_monitoring_raw"]["header_project"]["project_code"])

        for manifest in manifests.values():
            self.assert_public_payload_is_sanitized(manifest)
            labels = [module["label"] for module in manifest["modules"]]
            self.assertTrue(labels)
            for label in labels:
                self.assertNotIn("环节", label)
                self.assertNotIn("阶段", label)
                self.assertNotRegex(label, r"第[一二三四五六七八九十0-9]+")
            self.assertTrue(set(module["module"] for module in manifest["modules"]).issubset(MEDICAL_MODULE_LABELS))

    def test_rux_manifest_separates_cm_from_investigational_product_changes(self) -> None:
        manifest = self.service.public_manifest("proj_rux_03_002")

        roles = {source["source_role"]: source for source in manifest["sources"]}
        self.assertIn("monitoring_listing", roles)
        self.assertIn("monitoring_subject_report", roles)
        self.assertIn("protocol_docx", roles)
        self.assertIn("concomitant_medication_domain", roles)
        self.assertIn("study_drug_change_domain", roles)
        self.assertEqual("非试验用合并用药", roles["concomitant_medication_domain"]["boundary_label"])
        self.assertEqual("试验药物变更/剂量调整", roles["study_drug_change_domain"]["boundary_label"])
        self.assertNotEqual(
            roles["concomitant_medication_domain"]["source_id"],
            roles["study_drug_change_domain"]["source_id"],
        )

        monitoring = self.service.module_binding("proj_rux_03_002", "medical_monitoring")
        self.assertEqual("proj_rux_03_002", monitoring.route_project_id)
        self.assertIn("rux_listing_20250612", monitoring.primary_source_ids)
        self.assertEqual("RUX listing 2025-06-12", monitoring.public_dict()["display_batch"]["batch_label"])
        self.assertEqual("2025-06-12", monitoring.public_dict()["display_batch"]["extract_date"])

    def test_d001_manifest_uses_raw_intake_as_input_and_legacy_only_as_comparison(self) -> None:
        manifest = self.service.public_manifest("d001_raw_intake")
        roles = {source["source_role"]: source for source in manifest["sources"]}

        self.assertIn("eligibility_protocol_docx", roles)
        self.assertIn("eligibility_raw_subject_bundle", roles)
        self.assertIn("legacy_eligibility_adapter", roles)
        self.assertEqual("legacy_comparison", roles["legacy_eligibility_adapter"]["source_scope"])
        self.assertNotIn("legacy_eligibility_adapter", manifest["route_bindings"]["eligibility_review"]["primary_source_ids"])
        self.assertEqual("d001_raw_intake", manifest["route_bindings"]["eligibility_review"]["route_project_id"])
        self.assertEqual(
            "D001 全量入组资料",
            manifest["route_bindings"]["eligibility_review"]["display_batch"]["batch_label"],
        )

    def test_my009_aliases_route_to_same_canonical_project_without_d001_or_rux_leakage(self) -> None:
        by_monitoring_id = self.service.public_manifest("my009_uc_monitoring_raw")
        by_eligibility_id = self.service.public_manifest("my009_uc_raw_intake")

        self.assertEqual(by_monitoring_id["project_id"], by_eligibility_id["project_id"])
        self.assertEqual("my009_uc", by_monitoring_id["project_id"])
        self.assertEqual("my009_uc_raw_intake", by_monitoring_id["route_bindings"]["eligibility_review"]["route_project_id"])
        self.assertEqual("my009_uc_monitoring_raw", by_monitoring_id["route_bindings"]["medical_monitoring"]["route_project_id"])
        self.assertEqual(
            "MY009 MM Listing 2026-04-08",
            by_monitoring_id["route_bindings"]["medical_monitoring"]["display_batch"]["batch_label"],
        )

        serialized = json.dumps(by_monitoring_id, ensure_ascii=False)
        self.assertNotIn("D001", serialized)
        self.assertNotIn("RUX-03-002 原始数据 listing 2025-06-12", serialized)
        self.assert_public_payload_is_sanitized(by_monitoring_id)

    @unittest.skipUnless(TestClient is not None, "FastAPI test client is unavailable")
    def test_source_manifest_api_exposes_sanitized_payload_for_raw_project_aliases(self) -> None:
        from services.api.app.main import app

        client = TestClient(app)
        response = client.get("/api/projects/d001_raw_intake/source-manifest")

        self.assertEqual(200, response.status_code, response.text)
        payload = response.json()
        self.assertEqual("CMS-D001", payload["header_project"]["project_code"])
        self.assertEqual("d001_raw_intake", payload["route_bindings"]["eligibility_review"]["route_project_id"])
        self.assert_public_payload_is_sanitized(payload)


if __name__ == "__main__":
    unittest.main()
