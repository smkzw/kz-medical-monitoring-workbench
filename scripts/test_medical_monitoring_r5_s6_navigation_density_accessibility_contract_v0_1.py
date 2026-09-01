#!/usr/bin/env python3
"""Deterministic stdlib tests for the renderer-neutral R5-S6 verifier."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


sys.dont_write_bytecode = True
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import verify_medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1 as verifier


ARTIFACT_DIR = SCRIPT_DIR.parent / "artifacts/medical_monitoring_r5_s6_navigation_density_accessibility_contract_v0_1"


def load(name: str) -> dict:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


class TestS6Contract(unittest.TestCase):
    def test_verifier_passes_and_reports_frozen_counts(self) -> None:
        summary = verifier.verify()
        self.assertEqual(summary["challenge_rows"], 104)
        self.assertEqual(summary["deep_link_identity_fields"], 21)
        self.assertEqual(summary["canonical_return_fields"], 9)
        self.assertEqual(summary["ephemeral_return_fields"], 5)
        self.assertEqual(summary["keyboard_bindings"], 16)
        self.assertEqual(summary["domain_encoding_items"], 8)
        self.assertEqual(summary["performance_dataset"], {"events": 1000, "indicators": 40, "risk_anchors": 300})
        self.assertEqual(summary["performance_result_state"], "unmeasured_contract_only")
        self.assertEqual(summary["port_8911"], "stopped")
        self.assertEqual(summary["medical_writing_file_count"], 542)
        self.assertEqual(summary["medical_writing_inventory_sha256"], "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca")
        self.assertEqual(summary["accepted_input_pin_count"], 10)
        self.assertFalse(summary["runtime_started"])
        self.assertFalse(summary["browser_exercised"])
        self.assertFalse(summary["real_project_or_model"])

    def test_listener_observation_cannot_disable_port_enforcement(self) -> None:
        observations = []
        actual_probe = verifier.port_is_listening

        def actual_tcp_probe() -> bool:
            observations.append("tcp")
            return False

        def simulated_listener() -> bool:
            observations.append("injected")
            return True

        verifier.port_is_listening = actual_tcp_probe
        try:
            with self.assertRaises(verifier.VerificationFailure) as context:
                verifier.verify(port_probe=simulated_listener)
        finally:
            verifier.port_is_listening = actual_probe
        self.assertEqual(observations, ["tcp", "injected"])
        self.assertIn("PORT_8911_LISTENING", context.exception.issues)

    def test_medical_writing_boundary_is_recomputed(self) -> None:
        boundary = verifier.recompute_medical_writing_boundary()
        self.assertEqual(boundary["errors"], [])
        self.assertEqual(boundary["file_count"], 542)
        self.assertEqual(boundary["aggregate_sha256"], "feef0f171e6c102e56c930de57afb2cfaf78e7bfacc33f17d1fa8cfb7cb3d1ca")

    def test_manifest_input_pins_are_recomputed(self) -> None:
        manifest = load("manifest.json")
        pins = verifier.recompute_manifest_input_pins(manifest)
        self.assertEqual(pins["errors"], [])
        self.assertEqual(pins["declared"], dict(sorted(verifier.EXPECTED_INPUT_RAW_SHA.items())))
        self.assertEqual(pins["observed"], pins["declared"])

    def test_manifest_uses_current_runtime_split(self) -> None:
        manifest = load("manifest.json")
        self.assertNotIn("future_validation_allowlist", manifest)
        issues = []
        verifier.verify_future_runtime_allowlist(manifest, issues)
        self.assertEqual(issues, [])

    def test_challenge_registry(self) -> None:
        registry = load("challenge_registry.json")
        rows = registry["rows"]
        self.assertEqual(len(rows), registry["row_count"])
        self.assertEqual(len({row["challenge_id"] for row in rows}), len(rows))
        self.assertEqual(
            [row["challenge_id"] for row in rows],
            [f"S6C-{index:03d}" for index in range(1, 105)],
        )
        self.assertEqual(verifier.content_digest(registry, "registry_content_hash"), registry["registry_content_hash"])
        for row in rows:
            mutation = row["single_mutation"]
            self.assertEqual(set(mutation), {"op", "path", "value"})
            self.assertEqual(mutation["op"], "replace")
            self.assertNotEqual(row["baseline_value"], mutation["value"])
            self.assertEqual(row["expected_projection"], verifier.EXPECTED_PROJECTION_BY_CATEGORY[row["category"]])
            self.assertTrue(row["test_metadata_only"])

    def test_quota_ledger_is_independent_and_complete(self) -> None:
        registry = load("challenge_registry.json")
        quota = load("quota_ledger.json")
        counts = {category: sum(row["category"] == category for row in registry["rows"]) for category in quota["category_quotas"]}
        self.assertEqual({category: value["required"] for category, value in quota["category_quotas"].items()}, counts)
        self.assertEqual(sum(counts.values()), quota["expected_total"])
        self.assertEqual(quota["registry_content_hash"], registry["registry_content_hash"])
        self.assertEqual(verifier.content_digest(quota, "ledger_content_hash"), quota["ledger_content_hash"])

    def test_required_path_coverage(self) -> None:
        registry = load("challenge_registry.json")
        observed = {category: set() for category in verifier.CATEGORY_COUNTS}
        for row in registry["rows"]:
            observed[row["category"]].add(row["single_mutation"]["path"])
        self.assertEqual(observed, verifier.expected_challenge_paths())

    def test_path_specific_oracles(self) -> None:
        registry = load("challenge_registry.json")
        oracles = verifier.expected_challenge_oracles()
        for row in registry["rows"]:
            key = (row["category"], row["single_mutation"]["path"])
            self.assertEqual((row["expected_error"], row["rule_id"]), oracles[key])

    def test_canonical_recipe_excludes_ephemeral_state(self) -> None:
        canonical = {
            "deep_link_identity": {"subject_ref": "subject-001"},
            "filter_state": {"include_low": False},
            "sort_state": {"key": "priority", "direction": "desc"},
            "page_state": {"page_index": 0, "page_size": 25},
            "selection_anchor": {"selected_event_ref": "event-001"},
            "semantic_zoom_state": {"semantic_zoom_level": "detail"},
            "axis_mode": "calendar",
            "window_start": "2026-01-01",
            "window_end": "2026-03-31",
        }
        canonical_hash = verifier.content_digest(canonical, "canonical_state_hash")
        with_ephemeral = dict(canonical)
        with_ephemeral["ephemeral"] = {"focus_ref": "focus-001"}
        self.assertEqual(canonical_hash, verifier.content_digest({key: value for key, value in with_ephemeral.items() if key != "ephemeral"}, "canonical_state_hash"))

    def test_closed_keyboard_and_encoding_contracts(self) -> None:
        exact = load("exact_contract.json")
        self.assertEqual(exact["keyboard_contract"]["bindings"], verifier.expected_keyboard_bindings())
        self.assertTrue(all(binding["medical_state_mutation"] is False for binding in exact["keyboard_contract"]["bindings"]))
        encoding = load("audience_encoding_registry.json")
        self.assertEqual(encoding["domain_items"], verifier.DOMAIN_ITEMS)
        self.assertEqual(encoding["risk_overlay"]["shape"], "double_chevron_badge")
        self.assertFalse(encoding["risk_overlay"]["colour_only"])
        self.assertIn("double_chevron_badge", encoding["event_forbidden_shapes"])


if __name__ == "__main__":
    unittest.main()
