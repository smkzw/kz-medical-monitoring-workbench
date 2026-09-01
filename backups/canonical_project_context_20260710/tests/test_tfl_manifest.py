from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.api.app.main import app  # noqa: E402
from services.api.app.tfl_manifest import MY008_ROOT, RUX_DATASET_ROOT, RUX_TFL_SINGLE_ROOT, TflManifestService  # noqa: E402


@unittest.skipUnless(RUX_DATASET_ROOT.exists() and RUX_TFL_SINGLE_ROOT.exists(), "RUX TFL fixture paths are unavailable")
class TflManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = TflManifestService().build_manifest("proj_mgk10_sar_demo")

    def package(self, package_id: str):
        return next(package for package in self.manifest.packages if package.package_id == package_id)

    def test_rux_manifest_reads_xpt_define_and_final_single_tfl_inventory(self):
        package = self.package("rux_03_002")

        self.assertEqual({"ADaM": 12, "SDTM": 48}, package.dataset_count_by_standard)
        self.assertEqual({"adam_xpt": 12, "sdtm_xpt": 48}, package.dataset_count_by_role)
        self.assertEqual(2, package.define_xml_count)
        self.assertEqual(59, package.define_itemgroup_count)
        self.assertEqual({"figure": 3, "listing": 31, "table": 57}, package.tfl_count_by_type)

        adsl = next(dataset for dataset in package.datasets if dataset.dataset_name == "ADSL")
        ae = next(dataset for dataset in package.datasets if dataset.dataset_name == "AE")
        self.assertEqual((241, 91), (adsl.row_count, adsl.column_count))
        self.assertEqual((356, 35), (ae.row_count, ae.column_count))
        self.assertTrue(adsl.define_linked)
        self.assertTrue(ae.define_linked)

    @unittest.skipUnless(MY008_ROOT.exists(), "MY008 TFL fixture path is unavailable")
    def test_my008_manifest_separates_dataset_roles_and_tfl_data_pairing(self):
        package = self.package("my008_pnh_3_01")

        self.assertEqual(0, package.define_xml_count)
        self.assertEqual(0, package.define_itemgroup_count)
        self.assertEqual(
            {
                "adam_sas7bdat": 18,
                "adam_xpt": 18,
                "raw_sas7bdat": 55,
                "sdtm_sas7bdat": 45,
                "sdtm_xpt": 45,
                "tfl_data_sas7bdat": 161,
            },
            package.dataset_count_by_role,
        )
        self.assertEqual({"figure": 23, "listing": 56, "table": 85}, package.tfl_count_by_type)
        self.assertTrue(any("未发现define.xml" in warning for warning in package.parser_warnings))

        teae = next(output for output in package.outputs if output.display_id == "t-14-03-02-01-ae-teae")
        self.assertEqual("table", teae.output_type)
        self.assertEqual("AE", teae.domain_hint)
        self.assertTrue(teae.paired_file_id)
        self.assertNotIn("/Users/", teae.relative_path)

    def test_tfl_manifest_endpoint_does_not_expose_local_absolute_paths_or_lifecycle_names(self):
        response = TestClient(app).get("/api/projects/proj_mgk10_sar_demo/tfl/manifest")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        serialized = json.dumps(payload, ensure_ascii=False)

        self.assertEqual("数据分析与TFL", payload["module_label"])
        self.assertNotIn("/Users/", serialized)
        self.assertNotIn("第7环节", serialized)
        self.assertNotIn("阶段7", serialized)
        self.assertEqual(2, payload["package_count"])
        self.assertGreaterEqual(payload["total_datasets"], 60)
        self.assertGreaterEqual(payload["total_outputs"], 90)
