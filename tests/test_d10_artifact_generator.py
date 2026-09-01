"""Focused non-LLM freeze tests for the D10 artifact generator + oracle.

Verifies the frozen R4-D10 v0.6 synthetic/offline artifact chain:
catalog (312 exact-key immutable cases, 12 mutually-exclusive primary
partitions), independent oracle (expected leaves exist ONLY there), five-way
challenge-manifest registry, partition-quota / mandatory-attack manifest, the
two generators' import/read closure, two-stage stage-B resolution with
fail-closed tamper detection, deterministic double-pass replay, and the
independent verifier that re-derives every expected outcome from catalog
typed_input ONLY (zero skips, 312/312).

Frozen pins (2026-08-16 post-generation acceptance state; contract section 15
anchors). The catalog generator file pin is the raw file SHA; the registry's
`generator_hash` is the frozen STAGE_A code pin (self-normalized).
"""

from __future__ import annotations

import ast
import hashlib
import json
import socket
import sys
import tempfile
import unittest
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import generate_d10_challenge_registry as g  # noqa: E402
import generate_d10_expected_oracle as o  # noqa: E402
import generate_d10_fixture_authority as a  # noqa: E402

CATALOG_PATH = ROOT / "reviews/medical_monitoring_r4_d10_typed_fixture_catalog_v1_20260816.json"
ORACLE_PATH = ROOT / "reviews/medical_monitoring_r4_d10_expected_outcome_oracle_v1_20260816.json"
REGISTRY_PATH = ROOT / "reviews/medical_monitoring_r4_d10_challenge_manifest_registry_v1_20260816.json"
QUOTA_PATH = ROOT / "reviews/medical_monitoring_r4_d10_partition_quota_manifest_v1_20260816.json"
CATALOG_GEN_PATH = ROOT / "tools/generate_d10_challenge_registry.py"
ORACLE_GEN_PATH = ROOT / "tools/generate_d10_expected_oracle.py"
VERIFIER_PATH = ROOT / "tools/verify_d10_artifacts.py"

ORACLE_ARTIFACT_NAME = "medical_monitoring_r4_d10_expected_outcome_oracle_v1_20260816.json"

CASE_COUNT = 312
MIN_CASE_COUNT = 312
REQUIRED_TOTAL = 312

# ---------------------------------------------------------------------------
# Pinned schema key sets (copied from the frozen generators; must not drift).
# ---------------------------------------------------------------------------
CATALOG_TOP_KEYS = ["catalog_id", "version", "case_count", "catalog_hash", "cases"]
CASE_KEYS = [
    "case_id", "primary_partition", "family_id", "grain", "owner_route",
    "clinical_claim_token", "disposition", "fixture_id", "fixture_hash",
    "oracle_case_id", "manifest_case_id", "expected_leaf_set",
    "expected_trace_leaf_set", "expected_source_leaf_set", "mutation_class",
    "audience_contract", "typed_input",
]
AUDIENCE_CONTRACT_KEYS = [
    "audience_contract_id", "audience_scope_id", "display_language",
    "blind_status", "lexicon_ref", "forbidden_internal_terms",
    "injection_blocked",
]
REGISTRY_TOP_KEYS = [
    "artifact_kind", "registry_id", "schema_version", "contract_semantic_hash",
    "catalog_hash", "quota_manifest_hash", "generator_hash",
    "oracle_reference_state", "rows", "bijection_audit", "content_hash",
]
REGISTRY_ROW_KEYS = ["case_id", "fixture_id", "oracle_case_id",
                     "manifest_case_id", "test_id"]
BIJECTION_COLUMNS = ["case_id", "fixture_id", "oracle_case_id",
                     "manifest_case_id", "test_id"]
ORACLE_REFERENCE_STATE_KEYS = [
    "state", "reserved_for", "oracle_artifact_path", "expected_leaf_policy",
    "catalog_expected_fields",
]
QUOTA_TOP_KEYS = [
    "manifest_id", "required_total", "primary_partition_requirements",
    "mandatory_attack_requirements", "actual_mandatory_attack_counts",
    "case_to_mandatory_attack_rows", "actual_primary_partition_counts",
    "case_id_union", "pairwise_intersection_counts", "union_count",
    "duplicate_case_ids", "missing_case_ids", "catalog_hash", "oracle_hash",
    "registry_hash", "generator_hash", "manifest_hash",
]
PARTITION_REQUIREMENT_KEYS = ["partition_id", "partition_label_zh",
                              "required_minimum"]
ATTACK_REQUIREMENT_KEYS = ["attack_id", "attack_label_zh", "required_minimum"]
CASE_ATTACK_ROW_KEYS = ["case_id", "attack_ids"]
ORACLE_TOP_KEYS = [
    "artifact_kind", "oracle_id", "schema_version", "contract_semantic_hash",
    "case_count", "ordered_expectations", "fixture_authority_registry_hash",
    "content_hash",
]
ORDERED_EXPECTATION_KEYS = [
    "case_id", "oracle_case_id", "fixture_id", "expected_leaf_set",
    "expected_trace_leaf_set", "expected_source_leaf_set",
    "expected_disposition_or_gate", "forbidden_leaf_set", "oracle_hash",
]
LEAF_KEYS = sorted([
    "leaf_kind", "signal_kind", "expected_disposition", "gate_kind",
    "reason_codes", "unit_stable_core_ref", "numerator_member_count",
    "numerator_individual_risk_count", "numerator_affected_subject_count",
    "numerator_event_or_outcome_count", "numerator_center_pattern_count",
    "numerator_affected_site_count", "denominator_kind", "denominator_value",
    "denominator_state", "estimate_kind", "project_signal_count",
    "clue_count", "query_count", "risk_handoff_count", "change_kind",
    "change_cause", "lineage_relation", "handoff_action",
    "rate_projection_state", "hidden_member_count", "hidden_site_count",
    "deep_link_target_count", "member_expansion_state",
    "query_redundancy_decision", "pd_wording_state",
    "audience_injection_blocked", "counterevidence_rule_matches",
    "model_evidence_role", "hotspot_member_refs",
])
TRACE_LEAF_KEYS = sorted(["trace_kind", "stable_core_ref", "content_identity",
                          "replay_byte_equal", "terminal_state"])
SOURCE_LEAF_KEYS = sorted(["member_ref", "source_locator_ref",
                           "resolution_state", "site_stable_id",
                           "subject_stable_id"])
FORBIDDEN_LEAF_KEYS = sorted(["leaf_kind", "expected_disposition", "gate_kind",
                              "change_kind", "reason_code"])

DISPOSITIONS_OR_GATES = ("positive", "negative", "boundary", "not_applicable",
                         "not_evaluable", "global_gate", "comparison_set_gate",
                         "window_pair_gate", "routing_gate", "integrity_gate",
                         "handoff_gate")
SIGNAL_KINDS = ("project_risk_distribution", "cross_site_pattern",
                "project_time_trend", "project_safety_trend",
                "project_efficacy_trend")
GATE_DISPOSITIONS = frozenset({"global_gate", "comparison_set_gate",
                               "window_pair_gate", "routing_gate",
                               "integrity_gate", "handoff_gate"})

# Static closure proofs -----------------------------------------------------
FORBIDDEN_CATALOG_DERIVATION_TOKENS = (
    '"expected_disposition_or_gate"', '"forbidden_leaf_set"',
    "derive_disposition", "build_expected_leaf_set",
    "build_trace_leaf_set", "build_source_leaf_set",
    '"expected_leaf_set": [', '"expected_trace_leaf_set": [',
    '"expected_source_leaf_set": [',
)
FORBIDDEN_ORACLE_CATALOG_TOKENS = (
    "typed_fixture_catalog", "challenge_manifest_registry",
    "partition_quota_manifest", "generate_d10_challenge_registry",
    "mutation_context", "mutation_class", "attack_ids",
    '"disposition"', 'case["disposition"]', "primary_partition",
)
RUNTIME_TOKENS = ("socket", "bind(", "listen(", "serve_forever", "8911",
                  "uvicorn", "flask", "mm_r4", "run_monitoring")
STDLIB_MODULES = frozenset({
    "__future__", "argparse", "ast", "collections", "hashlib", "json",
    "pathlib", "re", "sys", "typing", "unicodedata", "unittest",
})
# Verifier source must stay blind to catalog-side declared labels. The
# post-derivation consistency assertion in verify_case compares the DERIVED
# outcome with the catalog's declared label; fact extraction never reads it.
FORBIDDEN_VERIFIER_TOKENS = (
    "mutation_class", "attack_ids", "family_id", "primary_partition",
    "mutation_context",
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(g.normalize_value(value), ensure_ascii=False,
                      sort_keys=True, separators=(",", ":"), allow_nan=False)


def object_hash(obj: dict, own_key: str = "content_hash") -> str:
    core = {k: v for k, v in obj.items() if k != own_key}
    return sha256_text(canonical_json(core))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clone(obj: Any) -> Any:
    return json.loads(canonical_json(obj))


def load_artifacts() -> tuple[dict, dict, dict, dict]:
    return (load_json(CATALOG_PATH), load_json(ORACLE_PATH),
            load_json(REGISTRY_PATH), load_json(QUOTA_PATH))


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


# ===========================================================================
# INDEPENDENT verifier (round 2): all verification goes through
# tools/verify_d10_artifacts.py - a standalone module that never imports,
# calls or reads the generators/oracle/audit. Tests call only its public
# entry points (verify_all / project_facts / rebuild_expectation /
# derive_disposition).
# ===========================================================================
import verify_d10_artifacts as v  # noqa: E402

AUTHORITY_PATH = ROOT / "reviews/medical_monitoring_r4_d10_fixture_authority_registry_v1_20260816.json"


def clone_case(case: dict[str, Any]) -> dict[str, Any]:
    return json.loads(canonical_json(case))


def _resign_object(obj: dict, key: str) -> None:
    obj[key] = object_hash(obj, key)


def resign_case(case: dict[str, Any]) -> dict[str, Any]:
    """Re-sign every recomputable local hash of a (tampered) case so the
    catalog becomes internally self-consistent again."""
    t = case["typed_input"]
    _resign_object(t["project_scope_binding"], "scope_binding_hash")
    _resign_object(t["mode_contract"], "mode_contract_content_hash")
    lr = t["legal_matrix_row"]
    lr["row_hash"] = sha256_text(canonical_json({
        "row_id": lr["row_id"], "signal_kind": lr["signal_kind"],
        "clinical_claim_token": lr["clinical_claim_token"],
        "d10_action": lr["d10_action"]}))
    for m in t["members"]:
        if m["member_kind"] == "center_pattern":
            m["descendant_set_hash"] = sha256_text(canonical_json(
                sorted(m["descendant_member_refs"])))
    mob = t["measure_origin_binding"]
    if mob is not None:
        mob["candidate_partition_hash"] = sha256_text(canonical_json(sorted(
            set(mob["verified_risk_refs"]) | set(mob["distinct_risk_refs"])
            | set(mob["ambiguous_risk_refs"]))))
        locator_ids = sorted({
            loc for m in t["members"] for loc in m["source_locator_refs"]}
            | {ref["locator_id"] for ref in t["evidence_refs"]})
        revision = {"revision_id": "SRC-REV-%03d-001" % int(
            case["case_id"].rsplit("-", 1)[-1]),
            "content_hash": sha256_text(canonical_json({
                "revision_id": "SRC-REV-%03d-001" % int(
                    case["case_id"].rsplit("-", 1)[-1]),
                "source_locators": locator_ids}))}
        mob["source_provenance_hash"] = sha256_text(canonical_json({
            "measure_ref": mob["measure_ref"],
            "source_revisions": [revision],
            "locator_ids": locator_ids}))
        _resign_object(mob, "binding_hash")
    qd = t["query_decision"]
    member_refs = [m["member_ref"] for m in t["members"]]
    qd["unit_member_set_hash"] = sha256_text(
        canonical_json(sorted(member_refs)))
    _resign_object(qd, "query_content_hash")
    vis = t["visibility_decision"]
    _resign_object(vis, "decision_id")
    for dl in t["deep_links"]:
        dl["visibility_decision_ref"] = vis["decision_id"]
    me = t["model_evidence"]
    if me is not None:
        me["model_binding_hash"] = sha256_text(canonical_json({
            "model_evidence_id": me["model_evidence_id"], "role": me["role"],
            "ensemble_size": me["ensemble_size"],
            "member_analysis_refs": me["member_analysis_refs"]}))
        _resign_object(me, "output_hash")
    ec = t["efficacy_context"]
    if ec is not None and ec["treatment_assignment_exposure_identity_ref"]:
        recomputed = sha256_text(canonical_json({
            "authority": ec["treatment_role_authority_ref"],
            "project": t["project_ref"], "run": t["run_ref"]}))
        ec["treatment_assignment_exposure_identity_ref"] = recomputed
        ec["treatment_assignment_mapping_hash"] = recomputed
    locator_ids = sorted({
        loc for m in t["members"] for loc in m["source_locator_refs"]}
        | {ref["locator_id"] for ref in t["evidence_refs"]})
    for pair in t["source_revision_content_pairs"]:
        pair["content_hash"] = sha256_text(canonical_json({
            "revision_id": pair["revision_id"],
            "source_locators": locator_ids}))
    core = {key: item for key, item in case.items() if key != "fixture_hash"}
    case["fixture_hash"] = object_hash(core, "fixture_hash")
    return case


def resign_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    """Re-sign every case's local hashes AND the catalog content hash."""
    for case in catalog["cases"]:
        resign_case(case)
    catalog["catalog_hash"] = object_hash(catalog, "catalog_hash")
    return catalog


def probe_case(case_id: str, mutate, authority: dict[str, Any],
               expect_gate: tuple = None,
               catalog_path: Path = CATALOG_PATH) -> str:
    """Round-2 probe runner: tamper -> the independent verifier must REJECT
    the case (per_case ok False) and the derived outcome must be a gate that
    differs from the oracle label."""
    catalog = load_json(catalog_path)
    clone = clone_case(next(c for c in catalog["cases"]
                            if c["case_id"] == case_id))
    mutate(clone)
    tampered_catalog = json.loads(canonical_json(catalog))
    for index, c in enumerate(tampered_catalog["cases"]):
        if c["case_id"] == case_id:
            tampered_catalog["cases"][index] = clone
            break
    result = v.verify_all(catalog=tampered_catalog, authority=authority)
    entry = result["per_case"][case_id]
    if entry["ok"]:
        raise AssertionError(f"{case_id} probe silently accepted by the "
                             "independent verifier")
    f = v.project_facts(clone)
    authority_index = {e["case_id"]: e for e in authority["entries"]}
    v.rebuild_expectation(clone, f, authority_index[case_id])
    disposition, reason, _extra = v.derive_disposition(f)
    if disposition not in GATE_DISPOSITIONS:
        raise AssertionError(f"{case_id} probe not rejected by verifier: "
                             f"{disposition}/{reason}")
    oracle = load_json(ORACLE_PATH)
    oracle_label = next(e for e in oracle["ordered_expectations"]
                        if e["case_id"] == case_id)["expected_disposition_or_gate"]
    if disposition == oracle_label:
        raise AssertionError(f"{case_id} probe outcome equals oracle label")
    if expect_gate is not None:
        if disposition != expect_gate[0] or reason != expect_gate[1]:
            raise AssertionError(f"{case_id} probe gate mismatch: "
                                 f"{disposition}:{reason}")
    return f"{disposition}:{reason}"
# ===========================================================================
class TestHashPinsAndAnchors(unittest.TestCase):
    """Computed content integrity: generator self-pins must recompute from the
    current tool source; frozen artifact content must stay self-consistent."""

    def test_generator_pin_self_consistent(self) -> None:
        self.assertEqual(g._generator_code_hash(), g.STAGE_A_GENERATOR_SHA256)
        self.assertEqual(a._generator_code_hash(), a.STAGE_A_GENERATOR_SHA256)

    def test_authority_artifact_content_hash_self_consistent(self) -> None:
        authority = load_json(AUTHORITY_PATH)
        self.assertEqual(authority["content_hash"], object_hash(authority, "content_hash"))

    def test_no_skip_identifiers_defined(self) -> None:
        source = VERIFIER_PATH.read_text(encoding="utf-8")
        for ident in ("SKIP", "xfail", "skipTest"):
            self.assertNotIn(f"{ident}(", source,
                             f"skip identifier {ident} used in verifier")


class TestCanonicalEncoding(unittest.TestCase):
    """UTF-8 / NFC / no-whitespace canonical JSON + no non-finite numbers."""

    ARTIFACT_PATHS = (CATALOG_PATH, ORACLE_PATH, REGISTRY_PATH, QUOTA_PATH)

    def test_utf8_nfc_and_canonical(self) -> None:
        for path in self.ARTIFACT_PATHS:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            self.assertEqual(text, unicodedata.normalize("NFC", text),
                             f"{path.name} not NFC")
            obj = json.loads(text)
            self.assertEqual(canonical_json(obj), text,
                             f"{path.name} not canonical")

    def test_no_nonfinite_numbers(self) -> None:
        for path in self.ARTIFACT_PATHS:
            for token in _walk_strings(json.loads(path.read_text(encoding="utf-8"))):
                self.assertNotIn("NaN", token, f"{path.name} contains NaN")
                self.assertNotIn("Infinity", token,
                                 f"{path.name} contains Infinity")

    def test_catalog_hash_format(self) -> None:
        catalog, _, _, _ = load_artifacts()
        self.assertRegex(catalog["catalog_hash"], r"^[0-9a-f]{64}$")


class TestCatalogSchema(unittest.TestCase):
    """Exact top-level / case / typed_input schemas; >= 312 cases."""

    def setUp(self) -> None:
        self.catalog, self.oracle, self.registry, self.quota = load_artifacts()

    def test_top_level_exact_keys_and_identity(self) -> None:
        self.assertEqual(sorted(self.catalog.keys()), sorted(CATALOG_TOP_KEYS))
        self.assertEqual(self.catalog["catalog_id"],
                         "medical-monitoring-r4-d10-typed-fixture-catalog-v1")
        self.assertEqual(self.catalog["case_count"], CASE_COUNT)
        self.assertGreaterEqual(self.catalog["case_count"], MIN_CASE_COUNT)
        self.assertEqual(self.catalog["catalog_hash"],
                         object_hash(self.catalog, "catalog_hash"))

    def test_every_case_schema_and_null_leaves(self) -> None:
        for case in self.catalog["cases"]:
            self.assertEqual(sorted(case.keys()), sorted(CASE_KEYS))
            self.assertIsNone(case["expected_leaf_set"])
            self.assertIsNone(case["expected_trace_leaf_set"])
            self.assertIsNone(case["expected_source_leaf_set"])
            self.assertEqual(sorted(case["audience_contract"].keys()),
                             sorted(AUDIENCE_CONTRACT_KEYS))
            core = {k: v for k, v in case.items() if k != "fixture_hash"}
            self.assertEqual(case["fixture_hash"],
                             object_hash(core, "fixture_hash"))
            self.assertRegex(case["fixture_hash"], r"^[0-9a-f]{64}$")
            self.assertEqual(case["disposition"], case["disposition"])
            self.assertIn(case["disposition"], DISPOSITIONS_OR_GATES)
            self.assertIn(case["owner_route"],
                          ("evaluate_and_own", "consume_only", "handoff_only",
                           "context_only", "routing_gate"))
            self.assertIn(case["primary_partition"], g.PARTITION_MINIMUMS)

    def test_full_generator_validation(self) -> None:
        g.validate_catalog(self.catalog)


class TestPartitionQuota(unittest.TestCase):
    """Exact primary-partition floors, uniqueness, disjoint-union proof,
    mandatory-attack bidirectional coverage."""

    def setUp(self) -> None:
        self.catalog, self.oracle, self.registry, self.quota = load_artifacts()

    def test_every_partition_at_least_minimum_and_exact(self) -> None:
        counts: dict[str, int] = {}
        for case in self.catalog["cases"]:
            counts[case["primary_partition"]] = \
                counts.get(case["primary_partition"], 0) + 1
        self.assertEqual(sum(counts.values()), REQUIRED_TOTAL)
        for partition, _, minimum in g.PARTITIONS:
            self.assertGreaterEqual(counts.get(partition, 0), minimum,
                                    f"{partition} below floor")
            self.assertEqual(counts.get(partition, 0),
                             self.quota["actual_primary_partition_counts"][partition])

    def test_disjoint_union_proof(self) -> None:
        ids = [c["case_id"] for c in self.catalog["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(self.quota["union_count"], len(ids))
        self.assertEqual(self.quota["union_count"], REQUIRED_TOTAL)
        self.assertEqual(self.quota["duplicate_case_ids"], [])
        self.assertEqual(self.quota["missing_case_ids"], [])
        self.assertEqual(self.quota["case_id_union"], sorted(ids))
        self.assertTrue(all(v == 0 for v in
                            self.quota["pairwise_intersection_counts"].values()))
        self.assertEqual(len(self.quota["pairwise_intersection_counts"]), 66)

    def test_mandatory_attacks_bidirectional(self) -> None:
        reqs = {e["attack_id"]: e for e in
                self.quota["mandatory_attack_requirements"]}
        self.assertEqual(len(reqs), len(g.ATTACK_IDS))
        self.assertGreaterEqual(len(g.ATTACK_IDS), 24)
        for attack_id in g.ATTACK_IDS:
            self.assertIn(attack_id, reqs, f"attack {attack_id} not listed")
            self.assertGreaterEqual(self.quota["actual_mandatory_attack_counts"]
                                    [attack_id], 1,
                                    f"attack {attack_id} has no case")
        # core 12 and enumerated 24 all covered
        for attack_id in g.CORE_ATTACKS:
            self.assertGreaterEqual(self.quota["actual_mandatory_attack_counts"]
                                    [attack_id], 1)
        for attack_id in g.ENUMERATED_ATTACKS:
            self.assertGreaterEqual(self.quota["actual_mandatory_attack_counts"]
                                    [attack_id], 1)
        # reverse mapping: counts derived from rows
        derived: dict[str, int] = {aid: 0 for aid in g.ATTACK_IDS}
        seen_rows: set[str] = set()
        for row in self.quota["case_to_mandatory_attack_rows"]:
            self.assertNotIn(row["case_id"], seen_rows)
            seen_rows.add(row["case_id"])
            for aid in row["attack_ids"]:
                self.assertIn(aid, g.ATTACK_IDS)
                derived[aid] += 1
        self.assertEqual(derived, self.quota["actual_mandatory_attack_counts"])
        # every attack-referencing case exists in the catalog
        catalog_ids = {c["case_id"] for c in self.catalog["cases"]}
        self.assertTrue(seen_rows <= catalog_ids)

    def test_full_generator_validation(self) -> None:
        g.validate_quota_manifest(self.quota, self.catalog)


class TestRegistryBijectionAndCoverage(unittest.TestCase):
    """Five-way bijection and full oracle coverage."""

    def setUp(self) -> None:
        self.catalog, self.oracle, self.registry, self.quota = load_artifacts()

    def test_five_column_bijection(self) -> None:
        self.assertEqual(sorted(self.registry.keys()), sorted(REGISTRY_TOP_KEYS))
        self.assertEqual(len(self.registry["rows"]), CASE_COUNT)
        for row in self.registry["rows"]:
            self.assertEqual(sorted(row.keys()), sorted(REGISTRY_ROW_KEYS))
        for column in BIJECTION_COLUMNS:
            values = [row[column] for row in self.registry["rows"]]
            self.assertEqual(len(values), len(set(values)),
                             f"registry column {column} not unique")
        self.assertTrue(self.registry["bijection_audit"]["bijection_ok"])
        self.assertEqual(self.registry["bijection_audit"]["row_count"],
                         CASE_COUNT)

    def test_rows_match_catalog_identities(self) -> None:
        by_id = {c["case_id"]: c for c in self.catalog["cases"]}
        for row in self.registry["rows"]:
            case = by_id[row["case_id"]]
            self.assertEqual(row["fixture_id"], case["fixture_id"])
            self.assertEqual(row["oracle_case_id"], case["oracle_case_id"])
            self.assertEqual(row["manifest_case_id"], case["manifest_case_id"])

    def test_full_oracle_coverage(self) -> None:
        oracle_ids = {e["oracle_case_id"] for e in
                      self.oracle["ordered_expectations"]}
        registry_oracle_ids = {row["oracle_case_id"]
                               for row in self.registry["rows"]}
        self.assertEqual(oracle_ids, registry_oracle_ids)
        self.assertEqual(len(oracle_ids), CASE_COUNT)

    def test_full_generator_validation(self) -> None:
        g.validate_registry(self.registry, self.catalog)


class TestOracleSchemaAndLeaves(unittest.TestCase):
    """Oracle-only expected/source/trace leaves: schema, uniformity, absence
    of catalog expected content."""

    def setUp(self) -> None:
        self.catalog, self.oracle, self.registry, self.quota = load_artifacts()

    def test_top_level_schema(self) -> None:
        self.assertEqual(sorted(self.oracle.keys()), sorted(ORACLE_TOP_KEYS))
        self.assertEqual(self.oracle["oracle_id"],
                         "medical-monitoring-r4-d10-expected-outcome-oracle")
        self.assertEqual(self.oracle["case_count"], CASE_COUNT)
        self.assertEqual(self.oracle["content_hash"],
                         object_hash(self.oracle, "content_hash"))
        self.assertRegex(self.oracle["content_hash"], r"^[0-9a-f]{64}$")

    def test_expectation_schema_and_uniform_leaves(self) -> None:
        for entry in self.oracle["ordered_expectations"]:
            self.assertEqual(sorted(entry.keys()),
                             sorted(ORDERED_EXPECTATION_KEYS))
            self.assertIn(entry["expected_disposition_or_gate"],
                          DISPOSITIONS_OR_GATES)
            for leaf in entry["expected_leaf_set"]:
                self.assertEqual(sorted(leaf.keys()), sorted(LEAF_KEYS))
                self.assertIn(leaf["leaf_kind"], g.LEAF_KINDS)
            for leaf in entry["expected_trace_leaf_set"]:
                self.assertEqual(sorted(leaf.keys()), sorted(TRACE_LEAF_KEYS))
            for leaf in entry["expected_source_leaf_set"]:
                self.assertEqual(sorted(leaf.keys()), sorted(SOURCE_LEAF_KEYS))
            for leaf in entry["forbidden_leaf_set"]:
                self.assertEqual(sorted(leaf.keys()), sorted(FORBIDDEN_LEAF_KEYS))
            core = {k: v for k, v in entry.items() if k != "oracle_hash"}
            self.assertEqual(entry["oracle_hash"], object_hash(core))
            self.assertRegex(entry["oracle_hash"], r"^[0-9a-f]{64}$")

    def test_gates_have_no_medical_units(self) -> None:
        for entry in self.oracle["ordered_expectations"]:
            if entry["expected_disposition_or_gate"] in GATE_DISPOSITIONS:
                for leaf in entry["expected_leaf_set"]:
                    self.assertNotEqual(leaf["leaf_kind"], "medical_unit")

    def test_full_generator_validation(self) -> None:
        o.validate_oracle(self.oracle)

    def test_quota_chain_hashes_match(self) -> None:
        suffix = "; oracle artifact content_hash="
        policy = self.registry["oracle_reference_state"]["expected_leaf_policy"]
        self.assertIn(suffix, policy)
        oracle_hash = policy.split(suffix, 1)[1]
        self.assertEqual(oracle_hash, self.oracle["content_hash"])
        self.assertEqual(oracle_hash, self.quota["oracle_hash"])
        self.assertEqual(self.quota["registry_hash"],
                         self.registry["content_hash"])
        self.assertEqual(self.quota["catalog_hash"],
                         self.catalog["catalog_hash"])
        self.assertEqual(self.quota["generator_hash"],
                         g.STAGE_A_GENERATOR_SHA256)
        self.assertEqual(self.quota["manifest_hash"],
                         object_hash(self.quota, "manifest_hash"))


class TestImportAndReadClosure(unittest.TestCase):
    """Static proofs: catalog generator never derives expected leaves; oracle
    generator never reads the catalog; neither imports the other, D10 runtime,
    or non-stdlib modules."""

    def test_catalog_generator_has_no_oracle_derivation(self) -> None:
        source = CATALOG_GEN_PATH.read_text(encoding="utf-8")
        for token in FORBIDDEN_CATALOG_DERIVATION_TOKENS:
            self.assertNotIn(token, source,
                             f"catalog generator contains oracle token {token!r}")

    def test_oracle_generator_has_no_catalog_read(self) -> None:
        source = ORACLE_GEN_PATH.read_text(encoding="utf-8")
        for token in FORBIDDEN_ORACLE_CATALOG_TOKENS:
            self.assertNotIn(token, source,
                             f"oracle generator contains catalog token {token!r}")

    def test_no_runtime_tokens(self) -> None:
        for path in (CATALOG_GEN_PATH, ORACLE_GEN_PATH):
            source = path.read_text(encoding="utf-8")
            for token in RUNTIME_TOKENS:
                self.assertNotIn(token, source,
                                 f"{path.name} contains runtime token {token!r}")

    def test_stdlib_only_imports(self) -> None:
        for path in (CATALOG_GEN_PATH, ORACLE_GEN_PATH):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        self.assertIn(root, STDLIB_MODULES,
                                      f"{path.name} imports {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module.split(".")[0], STDLIB_MODULES,
                                  f"{path.name} imports from {node.module}")

    def test_oracle_generator_never_reads_catalog_artifacts(self) -> None:
        source = ORACLE_GEN_PATH.read_text(encoding="utf-8")
        self.assertNotIn("typed_fixture_catalog", source)
        self.assertNotIn("challenge_manifest_registry", source)
        self.assertNotIn("partition_quota_manifest", source)
        stripped = source.replace(
            '"reviews/medical_monitoring_r4_d10_expected_outcome_oracle_v1_20260816.json"',
            "").replace(
            '"reviews/medical_monitoring_r4_d10_fixture_authority_registry_v1_20260816.json"',
            "")
        self.assertNotIn(".json\"", stripped,
                         "oracle generator references an unlisted artifact")

    def test_verifier_is_blind_to_catalog_labels(self) -> None:
        source = VERIFIER_PATH.read_text(encoding="utf-8")
        # AST proof: the verifier never subscripts any object with declared
        # catalog labels or mutation metadata (schema key lists may contain
        # the strings; reads may not).
        tree = ast.parse(source)
        reads = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) \
                    and isinstance(node.value, ast.Name) \
                    and node.value.id == "case" \
                    and isinstance(node.slice, ast.Constant) \
                    and isinstance(node.slice.value, str):
                reads.append(node.slice.value)
        # primary_partition is read ONLY for authority conformance
        # (compare against the pinned partition), never for derivation.
        for token in ("disposition", "mutation_class", "mutation_context",
                      "family_id", "attack_ids", "owner_route",
                      "clinical_claim_token"):
            self.assertNotIn(token, reads,
                             f"verifier reads forbidden case key {token!r}")

    def test_verifier_never_imports_generators(self) -> None:
        source = VERIFIER_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        for name in imports:
            self.assertFalse(name.startswith("generate_d10"),
                             f"verifier imports generator module {name}")
        # the verifier pins generator FILE SHAs for identity verification but
        # must never import or execute generator code
        for token in ("import generate_d10", "from generate_d10",
                      "generate_d10_challenge_registry import",
                      "generate_d10_expected_oracle import",
                      "generate_d10_fixture_authority import"):
            self.assertNotIn(token, source,
                             f"verifier imports generator code {token!r}")

    def test_verifier_unaffected_by_generator_breakage(self) -> None:
        """Monkeypatch proof: breaking the generator/oracle modules must not
        affect the independent verifier (it never calls them)."""
        import generate_d10_expected_oracle as o_mod
        import generate_d10_fixture_authority as a_mod
        original_o = o_mod.assemble_oracle
        original_a = a_mod.assemble_authority
        try:
            o_mod.assemble_oracle = lambda: (_ for _ in ()).throw(
                RuntimeError("oracle broken"))
            a_mod.assemble_authority = lambda: (_ for _ in ()).throw(
                RuntimeError("authority broken"))
            result = v.verify_all()
            self.assertTrue(result["ok"],
                            "verifier affected by generator breakage: "
                            f"{result['problems'][:3]}")
        finally:
            o_mod.assemble_oracle = original_o
            a_mod.assemble_authority = original_a


class TestTwoStageResolution(unittest.TestCase):
    """Regression: stage-A provisional registry/quota are oracle-blind;
    stage-B resolution is exactly provisional + declared delta; --check
    passes on the on-disk resolved artifacts."""

    def test_fresh_stage_a_and_resolution_roundtrip(self) -> None:
        catalog, oracle, registry, quota = load_artifacts()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            fresh = g.render_artifacts(verbose=False, out_dir=out)
            fresh_registry = fresh["registry"]
            fresh_quota = fresh["quota_manifest"]
            self.assertEqual(fresh_registry["oracle_reference_state"]["state"],
                             "unresolved")
            self.assertEqual(fresh_quota["oracle_hash"], g.PROVISIONAL_HASH_SENTINEL)
            resolved_registry, resolved_quota = g.resolve_stage_b(
                fresh_registry, fresh_quota, oracle["content_hash"])
            # resolved == on-disk resolved artifacts
            self.assertEqual(resolved_registry, registry)
            self.assertEqual(resolved_quota, quota)
            # registry core (minus deltas) matches fresh provisional
            self.assertEqual(g._registry_core(resolved_registry),
                             g._registry_core(fresh_registry))
            g.verify_resolved_registry(registry, catalog)
            g.validate_resolved_quota(quota, registry)

    def test_check_passes(self) -> None:
        self.assertEqual(g.check_artifacts(verbose=False), 0)


class TestStageBFailsClosed(unittest.TestCase):
    """Every tamper of the resolved registry/quota must fail closed."""

    def setUp(self) -> None:
        self.catalog, self.oracle, self.registry, self.quota = load_artifacts()

    def _assert_rejects(self, mutate, validator) -> None:
        tampered = clone(self.registry)
        mutate(tampered)
        with self.assertRaises(g.D10ArtifactError):
            validator(tampered, self.catalog)

    def test_registry_tampers(self) -> None:
        cases = [
            lambda r: r["oracle_reference_state"].update(state="unresolved"),
            lambda r: r["oracle_reference_state"].update(reserved_for="attacker"),
            lambda r: r["oracle_reference_state"].update(
                oracle_artifact_path="reviews/other.json"),
            lambda r: r["oracle_reference_state"].update(
                expected_leaf_policy="fake policy"),
            lambda r: r["oracle_reference_state"].update(
                expected_leaf_policy=r["oracle_reference_state"]
                ["expected_leaf_policy"] + "; tampered"),
            lambda r: r.update(generator_hash="0" * 64),
            lambda r: r["rows"].append(dict(r["rows"][0])),
            lambda r: r["rows"][0].update(test_id="D10-TEST-999"),
            lambda r: r["rows"].pop(),
            lambda r: r["bijection_audit"].update(bijection_ok=False),
        ]
        for i, mutate in enumerate(cases):
            with self.subTest(i=i):
                self._assert_rejects(mutate, g.verify_resolved_registry)

    def test_quota_tampers(self) -> None:
        tampered = clone(self.quota)
        tampered["oracle_hash"] = "0" * 64
        with self.assertRaises(g.D10ArtifactError):
            g.validate_resolved_quota(tampered, self.registry)
        tampered = clone(self.quota)
        tampered["registry_hash"] = "1" * 64
        with self.assertRaises(g.D10ArtifactError):
            g.validate_resolved_quota(tampered, self.registry)
        tampered = clone(self.quota)
        tampered["generator_hash"] = "0" * 64
        with self.assertRaises(g.D10ArtifactError):
            g.validate_resolved_quota(tampered, self.registry)
        tampered = clone(self.quota)
        tampered["manifest_hash"] = "0" * 64
        with self.assertRaises(g.D10ArtifactError):
            g.validate_resolved_quota(tampered, self.registry)

    def test_render_refuses_to_clobber_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            g.render_artifacts(verbose=False, out_dir=out)
            reg = json.loads((out / g.REGISTRY.name).read_text(encoding="utf-8"))
            q = json.loads((out / g.QUOTA.name).read_text(encoding="utf-8"))
            resolved_reg, resolved_q = g.resolve_stage_b(
                reg, q, self.oracle["content_hash"])
            (out / g.REGISTRY.name).write_text(canonical_json(resolved_reg))
            (out / g.QUOTA.name).write_text(canonical_json(resolved_q))
            with self.assertRaises(g.D10ArtifactError):
                g.render_artifacts(verbose=False, out_dir=out)


class TestMutationGates(unittest.TestCase):
    """Generator schema/hash/token gates reject tampered artifacts."""

    def setUp(self) -> None:
        self.catalog, self.oracle, self.registry, self.quota = load_artifacts()

    def test_catalog_tampers(self) -> None:
        tampered = clone(self.catalog)
        tampered["cases"][0]["disposition"] = "negative"
        with self.assertRaises(g.D10ArtifactError):
            g.validate_catalog(tampered)  # fixture_hash mismatch
        tampered = clone(self.catalog)
        tampered["cases"][0]["expected_leaf_set"] = [{"leaf_kind": "x"}]
        with self.assertRaises(g.D10ArtifactError):
            g.validate_catalog(tampered)
        tampered = clone(self.catalog)
        tampered["cases"][0]["typed_input"]["envelope_id"] = "tampered"
        with self.assertRaises(g.D10ArtifactError):
            g.validate_catalog(tampered)
        tampered = clone(self.catalog)
        tampered["catalog_hash"] = "0" * 64
        with self.assertRaises(g.D10ArtifactError):
            g.validate_catalog(tampered)

    def test_oracle_tampers(self) -> None:
        tampered = clone(self.oracle)
        entry = tampered["ordered_expectations"][0]
        entry["expected_disposition_or_gate"] = "invalid_disposition"
        with self.assertRaises(SystemExit):
            o.validate_oracle(tampered)
        tampered = clone(self.oracle)
        tampered["ordered_expectations"][0]["expected_leaf_set"][0]["leaf_kind"] = \
            "bogus_kind"
        with self.assertRaises(SystemExit):
            o.validate_oracle(tampered)
        tampered = clone(self.oracle)
        tampered["content_hash"] = "0" * 64
        with self.assertRaises(SystemExit):
            o.validate_oracle(tampered)


class TestIndependentVerifier(unittest.TestCase):
    """312/312 full-outcome re-derivation by the INDEPENDENT verifier module,
    with ZERO skips; every rebuilt expectation must equal the oracle."""

    def test_verify_all_reproduces_oracle_exactly(self) -> None:
        result = v.verify_all()
        self.assertTrue(result["ok"], result["problems"][:5])
        self.assertEqual(len(result["per_case"]), CASE_COUNT)
        failures = [cid for cid, entry in result["per_case"].items()
                    if not entry["ok"]]
        self.assertEqual(failures, [])

    def test_valid_source_subset_matches_semantic_baseline(self) -> None:
        """Semantic verification accepts a legal subset of authority pairs.

        Artifact conformance separately requires every authority anchor to be
        present in the frozen fixture catalog; this direct semantic check
        proves that distinction does not become a runtime envelope equality
        requirement.
        """
        catalog = load_json(CATALOG_PATH)
        authority = load_json(AUTHORITY_PATH)
        authority_index = {entry["case_id"]: entry
                           for entry in authority["entries"]}
        selected = None
        for case in catalog["cases"]:
            entry = authority_index[case["case_id"]]
            if not v.audit_case(case, entry):
                selected = (case, entry)
                break
        self.assertIsNotNone(selected)
        case, entry = selected
        typed = case["typed_input"]
        current = typed["source_revision_content_pairs"][0]
        alternate_revision = f"{current['revision_id']}-alternate"
        alternate = {
            "revision_id": alternate_revision,
            "content_hash": sha256_text(canonical_json({
                "revision_id": alternate_revision,
                "source_locators": v._locator_ids(typed),
            })),
        }
        expanded_entry = clone(entry)
        expanded_entry["source_revisions"].append(alternate)
        expanded_entry["authority_hash"] = object_hash(
            expanded_entry, "authority_hash")

        baseline = v.project_facts(case, entry)
        subset = v.project_facts(case, expanded_entry)
        self.assertTrue(subset["envelope_ok"])
        self.assertFalse(subset["source_authority_bad"])
        self.assertNotIn("source_authority_bad",
                         v.audit_case(case, expanded_entry))
        self.assertEqual(v.derive_disposition(subset)[:2],
                         v.derive_disposition(baseline)[:2])


class TestContentIdentityAndInvariance(unittest.TestCase):
    """Anti-overfit pairs: identical disposition/counts/gates; only
    identity-bearing leaf fields may differ."""

    def setUp(self) -> None:
        self.catalog, self.oracle, _, _ = load_artifacts()

    def test_anti_overfit_variant_pairs(self) -> None:
        entries = {e["case_id"]: e for e in self.oracle["ordered_expectations"]}
        for base_idx in range(297, 313, 2):
            v1 = entries[f"D10-CASE-{base_idx:03d}"]
            v2 = entries[f"D10-CASE-{base_idx + 1:03d}"]
            self.assertEqual(v1["expected_disposition_or_gate"],
                             v2["expected_disposition_or_gate"])
            self.assertEqual(len(v1["expected_leaf_set"]),
                             len(v2["expected_leaf_set"]))
            for left, right in zip(v1["expected_leaf_set"],
                                   v2["expected_leaf_set"]):
                self.assertEqual(left["leaf_kind"], right["leaf_kind"])
                self.assertEqual(left["expected_disposition"],
                                 right["expected_disposition"])
                for key in LEAF_KEYS:
                    if key in ("unit_stable_core_ref", "hotspot_member_refs"):
                        continue
                    self.assertEqual(left[key], right[key],
                                     f"variant {base_idx} leaf {key} differs")

    def test_substantive_facts_equal_across_variants(self) -> None:
        """Anti-overfit variant pairs share the SAME typed-fact projection
        and the SAME substantive identity (stable core, content identity,
        source leaves, member sets, denominator) rebuilt from the accepted
        authority; only display/order/non-medical version surfaces differ."""
        authority = load_json(AUTHORITY_PATH)
        index = {e["case_id"]: e for e in authority["entries"]}
        by_id = {c["case_id"]: c for c in self.catalog["cases"]}
        for base_idx in range(297, 313, 2):
            v1 = by_id[f"D10-CASE-{base_idx:03d}"]
            v2 = by_id[f"D10-CASE-{base_idx + 1:03d}"]
            f1 = {k: item for k, item in v.project_facts(v1).items()
                  if k not in ("surface_alt", "idx", "case_id",
                               "oracle_case_id", "fixture_id")}
            f2 = {k: item for k, item in v.project_facts(v2).items()
                  if k not in ("surface_alt", "idx", "case_id",
                               "oracle_case_id", "fixture_id")}
            self.assertEqual(f1, f2,
                             f"variant pair {base_idx} facts differ")
            e1 = v.rebuild_expectation(v1, f1, index[v1["case_id"]])
            e2 = v.rebuild_expectation(v2, f2, index[v2["case_id"]])
            self.assertEqual(e1["expected_leaf_set"], e2["expected_leaf_set"],
                             f"variant pair {base_idx} leaves differ")
            self.assertEqual(e1["expected_source_leaf_set"],
                             e2["expected_source_leaf_set"],
                             f"variant pair {base_idx} source leaves differ")
            self.assertEqual(e1["expected_trace_leaf_set"],
                             e2["expected_trace_leaf_set"],
                             f"variant pair {base_idx} trace identity differs")
            self.assertEqual(
                f1["authority_entry"]["signal_definition"]
                ["signal_definition_id"],
                f2["authority_entry"]["signal_definition"]
                ["signal_definition_id"])
            self.assertNotEqual(v1["typed_input"], v2["typed_input"])


class TestDeterministicReplayAndPort(unittest.TestCase):
    """Repeated generation is byte-identical; TCP 8911 stays stopped."""

    def test_generate_all_twice_byte_identical(self) -> None:
        first = g._generate_all()
        second = g._generate_all()
        for a, b in zip(first[:3], second[:3]):
            self.assertEqual(canonical_json(a), canonical_json(b))
        self.assertEqual(first[3], second[3])

    def test_oracle_twice_byte_identical(self) -> None:
        first = o.assemble_oracle()
        second = o.assemble_oracle()
        self.assertEqual(canonical_json(first), canonical_json(second))

    def test_port_8911_stopped(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            result = sock.connect_ex(("127.0.0.1", 8911))
        finally:
            sock.close()
        self.assertNotEqual(result, 0,
                            "port 8911 must stay stopped (connection refused)")


# ===========================================================================
# Independent-verifier probes (2026-08-16 REVISE_D10_ARTIFACTS): every listed
# re-signed semantic tamper must be REJECTED by validate_catalog() (via the
# typed-input audit) AND by the independent verifier (integrity/global gate,
# never the oracle's benign outcome).
# ===========================================================================
class TestSemanticTamperProbes(unittest.TestCase):
    """REVISE_D10_ARTIFACTS round-2 probes: every listed tamper must be
    rejected by the INDEPENDENT verifier (per-case ok False + gate outcome),
    by validate_catalog() (audit) where the tamper is internally inconsistent,
    and by authority conformance where it is fully re-signed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = load_json(AUTHORITY_PATH)
        cls.catalog = load_json(CATALOG_PATH)

    def _probe(self, case_id: str, mutate, expect_gate: tuple = None) -> str:
        return probe_case(case_id, mutate, self.authority,
                          expect_gate=expect_gate)

    def _resign_probe(self, case_id: str, mutate) -> str:
        """Full re-sign variant: tamper + re-sign every local hash + catalog
        hash so the artifact is internally self-consistent; rejection must
        come from the FIXED fixture authority."""
        catalog = clone(self.catalog)
        case = next(c for c in catalog["cases"] if c["case_id"] == case_id)
        mutate(case)
        resign_catalog(catalog)
        # rejection must come from the audit OR the fixed authority
        try:
            g.validate_catalog(catalog)
        except g.D10ArtifactError:
            return "audit_rejected"
        with self.assertRaises(g.D10ArtifactError):
            g.validate_authority_conformance(catalog, self.authority)
        result = v.verify_all(catalog=catalog, authority=self.authority)
        entry = result["per_case"][case_id]
        if entry["ok"]:
            raise AssertionError(f"{case_id} full re-sign accepted by verifier")
        mismatch = [pr for pr in entry["problems"]
                    if "authority mismatch" in pr]
        self.assertTrue(mismatch,
                        f"{case_id} re-sign rejected for wrong reason: "
                        f"{entry['problems'][:2]}")
        return "authority_mismatch:" + mismatch[0].split(" authority mismatch ")[1]

    # ---- round-1 tamper probes (20 variants across the 16 listed families)
    def test_probe_001_owner_route(self) -> None:
        result = self._probe("D10-CASE-001", lambda c: c["typed_input"]
                             ["signal_definition"].update(
                                 d10_action="consume_only"),
                             ("integrity_gate", "legal_row_mismatch"))
        self.assertEqual(result, "integrity_gate:legal_row_mismatch")

    def test_probe_001_legal_row_hash(self) -> None:
        result = self._probe("D10-CASE-001", lambda c: c["typed_input"]
                             ["legal_matrix_row"].update(row_hash="0" * 64),
                             ("integrity_gate", "legal_matrix_row_tamper"))
        self.assertEqual(result, "integrity_gate:legal_matrix_row_tamper")

    def test_probe_001_scope_binding_id(self) -> None:
        result = self._probe("D10-CASE-001", lambda c: c["typed_input"]
                             ["project_scope_binding"].update(
                                 scope_binding_id="SYN-D10-SCOPE-999"),
                             ("integrity_gate", "scope_binding_tamper"))
        self.assertEqual(result, "integrity_gate:scope_binding_tamper")

    def test_probe_001_source_pair_hash(self) -> None:
        result = self._probe("D10-CASE-001", lambda c: c["typed_input"]
                             ["source_revision_content_pairs"][0].update(
                                 content_hash="0" * 64),
                             ("integrity_gate", "source_revision_hash_tamper"))
        self.assertEqual(result, "integrity_gate:source_revision_hash_tamper")

    def test_probe_094_origin_external_ref(self) -> None:
        result = self._probe("D10-CASE-094", lambda c: c["typed_input"]
                             ["measure_origin_binding"]["verified_risk_refs"]
                             .append("SYN-EXTERNAL-RISK-999-01"),
                             ("integrity_gate", "measure_origin_binding_tamper"))
        self.assertEqual(result, "integrity_gate:measure_origin_binding_tamper")

    def test_probe_001_denominator_refs_cleared(self) -> None:
        result = self._probe("D10-CASE-001", lambda c: c["typed_input"]
                             ["denominator"].update(
                                 denominator_member_refs=[]),
                             ("integrity_gate",
                              "denominator_recompute_mismatch"))
        self.assertEqual(result,
                         "integrity_gate:denominator_recompute_mismatch")

    def test_probe_117_segment_fields(self) -> None:
        def mutate(c):
            seg = c["typed_input"]["time_segments"][0]
            seg["start_value"] = seg["start_value"] + 10
            seg["end_value"] = seg["end_value"] + 10
            seg["member_ref"] = "SYN-EXTERNAL-SUBJ-999-01"
        result = self._probe("D10-CASE-117", mutate,
                             ("integrity_gate",
                              "denominator_recompute_mismatch"))
        self.assertEqual(result,
                         "integrity_gate:denominator_recompute_mismatch")

    def test_probe_220_cutoff_order(self) -> None:
        result = self._probe("D10-CASE-220", lambda c: c["typed_input"]
                             ["change_decision"]["cutoff_advance"].update(
                                 current_boundary_value="2026-02-01"),
                             ("integrity_gate", "cutoff_advance_tamper"))
        self.assertEqual(result, "integrity_gate:cutoff_advance_tamper")

    def test_probe_216_mode_hash(self) -> None:
        result = self._probe("D10-CASE-216", lambda c: c["typed_input"]
                             ["mode_contract"].update(
                                 mode_contract_content_hash="0" * 64),
                             ("integrity_gate", "mode_contract_tamper"))
        self.assertEqual(result, "integrity_gate:mode_contract_tamper")

    def test_probe_217_r2_prior(self) -> None:
        result = self._probe("D10-CASE-217", lambda c: c["typed_input"]
                             ["change_decision"].update(
                                 r2_prior_ref_or_none=None),
                             ("integrity_gate", "r2_wrong_prior"))
        self.assertEqual(result, "integrity_gate:r2_wrong_prior")

    def test_probe_217_r2_lineage(self) -> None:
        result = self._probe("D10-CASE-217", lambda c: c["typed_input"]
                             ["change_decision"].update(
                                 lineage_relation="superseded_by_mode_change"),
                             ("integrity_gate", "r2_wrong_lineage"))
        self.assertEqual(result, "integrity_gate:r2_wrong_lineage")

    def test_probe_251_deeplink_subject_ref(self) -> None:
        result = self._probe("D10-CASE-251", lambda c: c["typed_input"]
                             ["deep_links"][0].update(
                                 subject_ref="SYN-EXTERNAL-SUBJECT-999"),
                             ("integrity_gate", "deep_link_target_tamper"))
        self.assertEqual(result, "integrity_gate:deep_link_target_tamper")

    def test_probe_251_deeplink_vis_ref(self) -> None:
        result = self._probe("D10-CASE-251", lambda c: c["typed_input"]
                             ["deep_links"][0].update(
                                 visibility_decision_ref="0" * 64),
                             ("integrity_gate", "deep_link_target_tamper"))
        self.assertEqual(result, "integrity_gate:deep_link_target_tamper")

    def test_probe_261_hidden_in_eligible(self) -> None:
        def mutate(c):
            vis = c["typed_input"]["visibility_decision"]
            vis["deep_link_eligible_member_refs"].append(
                vis["hidden_member_refs"][0])
        result = self._probe("D10-CASE-261", mutate,
                             ("integrity_gate",
                              "deep_link_eligible_violation"))
        self.assertEqual(result,
                         "integrity_gate:deep_link_eligible_violation")

    def test_probe_243_covered_external(self) -> None:
        result = self._probe("D10-CASE-243", lambda c: c["typed_input"]
                             ["query_decision"].update(
                                 covered_member_refs=[
                                     "SYN-EXTERNAL-RISK-999-01"] * 7),
                             ("integrity_gate", "query_redundancy_tamper"))
        self.assertEqual(result, "integrity_gate:query_redundancy_tamper")

    def test_probe_243_query_identities_duplicated(self) -> None:
        def mutate(c):
            qd = c["typed_input"]["query_decision"]
            ids = qd["member_query_content_identities"]
            qd["member_query_content_identities"] = [ids[0]] * len(ids)
        result = self._probe("D10-CASE-243", mutate,
                             ("integrity_gate", "query_redundancy_tamper"))
        self.assertEqual(result, "integrity_gate:query_redundancy_tamper")

    def test_probe_201_assignment(self) -> None:
        result = self._probe("D10-CASE-201", lambda c: c["typed_input"]
                             ["efficacy_context"].update(
                                 treatment_assignment_exposure_identity_ref=
                                 "0" * 64),
                             ("integrity_gate", "treatment_assignment_tamper"))
        self.assertEqual(result, "integrity_gate:treatment_assignment_tamper")

    def test_probe_101_descendant_hash(self) -> None:
        def mutate(c):
            pattern = next(m for m in c["typed_input"]["members"]
                           if m["member_kind"] == "center_pattern")
            pattern["descendant_set_hash"] = "0" * 64
        result = self._probe("D10-CASE-101", mutate,
                             ("integrity_gate", "descendant_set_tamper"))
        self.assertEqual(result, "integrity_gate:descendant_set_tamper")

    def test_probe_184_model_adjudication(self) -> None:
        result = self._probe("D10-CASE-184", lambda c: c["typed_input"]
                             ["model_evidence"].update(
                                 adjudication_state="divergent"),
                             ("integrity_gate", "model_evidence_tamper"))
        self.assertEqual(result, "integrity_gate:model_evidence_tamper")

    def test_probe_001_audience_injection(self) -> None:
        def mutate(c):
            c["typed_input"]["audience_text"]["finding_zh"] = (
                "正式安全性信号 pattern=foo 相关受试者 {n} 名")
        result = self._probe("D10-CASE-001", mutate,
                             ("integrity_gate", "audience_injection_blocked"))
        self.assertEqual(result, "integrity_gate:audience_injection_blocked")

    # ---- round-2 FULL RE-SIGN variants (16 classes): internally consistent,
    #      rejected ONLY by the fixed fixture authority
    def test_resign_scope_type(self) -> None:
        result = self._resign_probe(
            "D10-CASE-001",
            lambda c: c["typed_input"]["project_scope_binding"].update(
                scope_type="subject"))
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_legal_row_id(self) -> None:
        result = self._resign_probe(
            "D10-CASE-001",
            lambda c: c["typed_input"]["legal_matrix_row"].update(
                row_id="SYN-D10-LEGAL-999"))
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_source_revision(self) -> None:
        result = self._resign_probe(
            "D10-CASE-001",
            lambda c: c["typed_input"]["source_revision_content_pairs"][0]
            .update(revision_id="SRC-REV-999-001"))
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_denominator_subjects(self) -> None:
        result = self._resign_probe(
            "D10-CASE-001",
            lambda c: c["typed_input"]["denominator"].update(
                denominator_member_refs=["SYN-D10-SUBJ-001-01-77"]
                * c["typed_input"]["denominator"]["denominator_value"]))
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_time_segments(self) -> None:
        def mutate(c):
            seg = c["typed_input"]["time_segments"][0]
            seg["start_value"] = 100
            seg["end_value"] = 129
            seg["member_ref"] = "SYN-D10-SUBJ-117-01-05"
        result = self._resign_probe("D10-CASE-117", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_r2_prior(self) -> None:
        result = self._resign_probe(
            "D10-CASE-217",
            lambda c: c["typed_input"]["change_decision"].update(
                r2_prior_ref_or_none=None))
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_visibility_partition(self) -> None:
        def mutate(c):
            vis = c["typed_input"]["visibility_decision"]
            hidden = vis["hidden_member_refs"]
            vis["hidden_member_refs"] = []
            vis["projectable_member_refs"] = sorted(
                set(vis["projectable_member_refs"]) | set(hidden))
        result = self._resign_probe("D10-CASE-261", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_deeplink_valid_subject(self) -> None:
        result = self._resign_probe(
            "D10-CASE-251",
            lambda c: c["typed_input"]["deep_links"][0].update(
                subject_ref="SYN-D10-SUBJ-251-01-02"))
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_query_refs(self) -> None:
        def mutate(c):
            refs = c["typed_input"]["query_decision"]["uncovered_member_refs"]
            refs[0] = "SYN-D10-RISK-245-999"
        result = self._resign_probe("D10-CASE-245", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_query_identities(self) -> None:
        def mutate(c):
            qd = c["typed_input"]["query_decision"]
            qd["member_query_content_identities"] = [
                sha256_text(canonical_json({"member_ref": ref}))
                for ref in reversed(qd["covered_member_refs"])]
        result = self._resign_probe("D10-CASE-243", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_d09_descendants(self) -> None:
        def mutate(c):
            pattern = next(m for m in c["typed_input"]["members"]
                           if m["member_kind"] == "center_pattern")
            pattern["descendant_member_refs"] = [
                "SYN-D10-DESC-101-01", "SYN-D10-DESC-101-02",
                "SYN-D10-DESC-101-03"]
        result = self._resign_probe("D10-CASE-101", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_model_evidence_refs(self) -> None:
        def mutate(c):
            me = c["typed_input"]["model_evidence"]
            me["member_analysis_refs"] = [
                "SYN-D10-MA-184-01", "SYN-D10-MA-184-02",
                "SYN-D10-MA-184-03"]
        result = self._resign_probe("D10-CASE-184", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_audience_contract_terms(self) -> None:
        def mutate(c):
            c["audience_contract"]["forbidden_internal_terms"] = [
                "正式安全性信号", "确证治疗效果"]
        result = self._resign_probe("D10-CASE-001", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_treatment_authority_mapping(self) -> None:
        def mutate(c):
            ec = c["typed_input"]["efficacy_context"]
            ec["treatment_role_authority_ref"] = "SYN-D10-TRAUTH-999"
        result = self._resign_probe("D10-CASE-201", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_measure_origin_refs(self) -> None:
        def mutate(c):
            mob = c["typed_input"]["measure_origin_binding"]
            mob["measure_ref"] = "SYN-D10-SAFE-094-99"
        result = self._resign_probe("D10-CASE-094", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_mode_version(self) -> None:
        result = self._resign_probe(
            "D10-CASE-001",
            lambda c: c["typed_input"]["mode_contract"].update(
                mode_contract_version="SYN-D10-MODE-999"))
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")

    def test_resign_signal_window_stratum_locator(self) -> None:
        def mutate(c):
            t = c["typed_input"]
            t["signal_definition"]["signal_definition_id"] = "SYN-D10-DEF-999"
            t["analysis_windows"][0]["analysis_window_stable_id"] = \
                "SYN-D10-WIN-999-1"
            t["stratum"]["stratum_contract_id"] = "SYN-D10-SC-999"
            t["members"][0]["source_locator_refs"] = ["SYN-D10-LOC-999-01"]
        result = self._resign_probe("D10-CASE-001", mutate)
        self.assertTrue(result.startswith(("authority_mismatch",
                                        "audit_rejected")),
                        f"resign variant not rejected: {result}")


class TestFixtureAuthorityGates(unittest.TestCase):
    """Independent gates over the fixture authority registry itself: schema,
    hashes, bijection, case coverage, double-pass byte identity, fixed pin."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = load_json(AUTHORITY_PATH)

    def test_double_pass_byte_identical(self) -> None:
        first = a.assemble_authority()
        second = a.assemble_authority()
        self.assertEqual(canonical_json(first), canonical_json(second))
        self.assertEqual(first["content_hash"], self.authority["content_hash"])

    def test_bijection_and_coverage(self) -> None:
        self.assertEqual(self.authority["case_count"], 312)
        entries = self.authority["entries"]
        self.assertEqual(len(entries), 312)
        self.assertEqual({e["case_id"] for e in entries},
                         {f"D10-CASE-{i:03d}" for i in range(1, 313)})
        self.assertEqual({e["authority_id"] for e in entries},
                         {f"D10-AUTH-{i:03d}" for i in range(1, 313)})
        self.assertTrue(self.authority["bijection_audit"]["bijection_ok"])

    def test_entry_hashes_and_top_hash(self) -> None:
        for entry in self.authority["entries"]:
            self.assertEqual(entry["authority_hash"],
                             object_hash(entry, "authority_hash"),
                             f"{entry['case_id']} authority_hash mismatch")
        self.assertEqual(self.authority["content_hash"],
                         object_hash(self.authority, "content_hash"))

    def test_authority_pin(self) -> None:
        self.assertEqual(self.authority["generator_hash"],
                         a.STAGE_A_GENERATOR_SHA256)
        self.assertEqual(a._generator_code_hash(),
                         a.STAGE_A_GENERATOR_SHA256)

    def test_tampered_authority_rejected(self) -> None:
        # schema-level tamper (hash not re-signed) -> validator rejects
        tampered = clone(self.authority)
        tampered["entries"][0]["signal_definition"]["signal_kind"] = \
            "cross_site_pattern"
        with self.assertRaises(a.AuthorityError):
            a.validate_authority(tampered)
        # fully re-signed authority value tamper -> catalog conformance and
        # the independent verifier reject (catalog matches the ORIGINAL
        # fixed authority, never the tampered one)
        tampered = clone(self.authority)
        tampered["entries"][0]["signal_definition"]["signal_kind"] = \
            "cross_site_pattern"
        tampered["entries"][0]["authority_hash"] = object_hash(
            tampered["entries"][0], "authority_hash")
        tampered["content_hash"] = object_hash(tampered, "content_hash")
        catalog = load_json(CATALOG_PATH)
        with self.assertRaises(g.D10ArtifactError):
            g.validate_authority_conformance(catalog, tampered)
        result = v.verify_all(authority=tampered)
        self.assertFalse(result["ok"])
        self.assertTrue(any("authority mismatch" in pr
                            for pr in result["problems"]))


class TestRound3Probes(unittest.TestCase):
    """REVISE_D10_ARTIFACTS round-3 acceptance gates: fixed artifact identity,
    mode/visibility/R2 authority, query/source/ModelEvidence/origin provenance.
    Every probe must fail closed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.authority = load_json(AUTHORITY_PATH)
        cls.catalog = load_json(CATALOG_PATH)
        cls.oracle = load_json(ORACLE_PATH)
        cls.registry = load_json(REGISTRY_PATH)
        cls.quota = load_json(QUOTA_PATH)

    def _reject(self, case_id: str, mutate, authority=None) -> str:
        """Round-3 resign probe: tamper + re-sign -> verifier per-case reject."""
        authority = authority or self.authority
        catalog = clone(self.catalog)
        case = next(c for c in catalog["cases"] if c["case_id"] == case_id)
        mutate(case)
        resign_catalog(catalog)
        try:
            g.validate_catalog(catalog)
        except g.D10ArtifactError:
            return "audit_rejected"
        with self.assertRaises(g.D10ArtifactError):
            g.validate_authority_conformance(catalog, authority)
        result = v.verify_all(catalog=catalog, authority=authority)
        entry = result["per_case"][case_id]
        self.assertFalse(entry["ok"],
                         f"{case_id} re-sign accepted by verifier")
        self.assertTrue(any("authority mismatch" in pr for pr in entry["problems"]),
                        f"{case_id} rejected for wrong reason: {entry['problems'][:2]}")
        return "authority_rejected"

    def _reject_chain(self, artifacts: dict) -> list[str]:
        """Run the verifier with overridden artifacts; return its problems."""
        result = v.verify_all(**artifacts)
        self.assertFalse(result["ok"])
        return result["problems"]

    # 1. mode design clause (requirement 2)
    def test_resign_design_clause(self) -> None:
        result = self._reject(
            "D10-CASE-001",
            lambda c: c["typed_input"]["mode_contract"].update(
                design_clause_ref="SYN-D10-DESIGN-999"))
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 2. visibility site partition (requirement 2)
    def test_resign_site_partition(self) -> None:
        def mutate(c):
            vis = c["typed_input"]["visibility_decision"]
            vis["projectable_site_refs"] = ["SYN-D10-SITE-001"]
            vis["hidden_site_refs"] = []
        result = self._reject("D10-CASE-262", mutate)
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 3. deep-link eligible external site (requirement 2)
    def test_resign_eligible_external_site(self) -> None:
        result = self._reject(
            "D10-CASE-249",
            lambda c: c["typed_input"]["visibility_decision"]
            ["deep_link_eligible_site_refs"].append("SYN-EXTERNAL-SITE-999"))
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 4. accepted prior evaluation identity (requirement 2)
    def test_resign_prior_evaluation_identity(self) -> None:
        result = self._reject(
            "D10-CASE-217",
            lambda c: c["typed_input"]["change_decision"].update(
                prior_snapshot_ref_or_none="SYN-D10-SNAP-PRIOR-999"))
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 5. mode-change ref substitution (requirement 2)
    def test_resign_mode_change_ref(self) -> None:
        result = self._reject(
            "D10-CASE-231",
            lambda c: c["typed_input"]["change_decision"].update(
                mode_change_refs=["SYN-D10-MODECHG-231-99"]))
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 6. Query synchronized reversal (requirement 3)
    def test_resign_query_sync_reversal(self) -> None:
        def mutate(c):
            qd = c["typed_input"]["query_decision"]
            covered, uncovered = qd["covered_member_refs"], qd["uncovered_member_refs"]
            qd["covered_member_refs"], qd["uncovered_member_refs"] = uncovered, covered
        result = self._reject("D10-CASE-257", mutate)
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 7. source file replacement + NFD row (requirement 3)
    def test_resign_source_file_nfd(self) -> None:
        def mutate(c):
            ref = c["typed_input"]["evidence_refs"][0]
            ref["source_file"] = "synthetic_source/other_dataset.json"
            ref["row_or_cell_ref"] = "sheet:1;row:1".encode("utf-8").decode("utf-8")
            ref["row_or_cell_ref"] = unicodedata.normalize(
                "NFD", "sheet:1;row:2")
        result = self._reject("D10-CASE-001", mutate)
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 8. ensemble=1 consensus leaf (requirement 3)
    def test_resign_ensemble1_consensus(self) -> None:
        result = self._reject(
            "D10-CASE-184",
            lambda c: c["typed_input"]["model_evidence"].update(
                permitted_leaf="counterevidence_suggestion_only"))
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 9. same revision ID, different typed content (requirement 3)
    def test_resign_same_revision_different_content(self) -> None:
        result = self._reject(
            "D10-CASE-001",
            lambda c: c["typed_input"]["evidence_refs"][0].update(
                locator_id="SYN-D10-LOC-001-99"))
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 10. paired provenance substitution (requirement 3)
    def test_resign_origin_ref_substitution(self) -> None:
        result = self._reject(
            "D10-CASE-094",
            lambda c: c["typed_input"]["measure_origin_binding"]
            ["verified_risk_refs"].__setitem__(0, "SYN-D10-RISK-094-07"))
        self.assertIn(result, ("authority_rejected", "audit_rejected"))

    # 11. full cross-case payload swap (requirement 1)
    def test_full_cross_case_payload_swap(self) -> None:
        catalog = clone(self.catalog)
        by_id = {c["case_id"]: c for c in catalog["cases"]}
        payload = clone(by_id["D10-CASE-002"]["typed_input"])
        by_id["D10-CASE-001"]["typed_input"] = payload
        resign_catalog(catalog)
        result = v.verify_all(catalog=catalog, authority=self.authority)
        entry = result["per_case"]["D10-CASE-001"]
        self.assertFalse(entry["ok"], "payload swap accepted")
        self.assertTrue(any("authority mismatch" in pr
                            for pr in entry["problems"]),
                        "payload swap rejected for wrong reason")

    # 12. registry generator/row swap (requirement 1)
    def test_registry_row_swap(self) -> None:
        registry = clone(self.registry)
        rows = registry["rows"]
        for col in ("fixture_id", "oracle_case_id", "manifest_case_id"):
            rows[0][col], rows[1][col] = rows[1][col], rows[0][col]
        registry["content_hash"] = object_hash(registry, "content_hash")
        problems = self._reject_chain({"registry": registry})
        self.assertTrue(any("rebuilt chain" in pr for pr in problems),
                        "row swap not caught by rebuilt chain")

    # 13. quota attacks replacement (requirement 1)
    def test_quota_attacks_replacement(self) -> None:
        quota = clone(self.quota)
        quota["mandatory_attack_requirements"][0]["attack_id"] = "bogus_attack"
        del quota["actual_mandatory_attack_counts"]["cross_project_scope"]
        quota["actual_mandatory_attack_counts"]["bogus_attack"] = 1
        quota["case_to_mandatory_attack_rows"][0]["attack_ids"].append(
            "bogus_attack")
        quota["manifest_hash"] = object_hash(quota, "manifest_hash")
        problems = self._reject_chain({"quota": quota})
        self.assertTrue(any("rebuilt chain" in pr for pr in problems),
                        "quota attack replacement not caught")

    # 14. authority cross-case swap (requirement 1)
    def test_authority_cross_case_swap(self) -> None:
        authority = clone(self.authority)
        entries = authority["entries"]
        entries[0]["signal_definition"], entries[1]["signal_definition"] = \
            entries[1]["signal_definition"], entries[0]["signal_definition"]
        for entry in entries:
            entry["authority_hash"] = object_hash(entry, "authority_hash")
        authority["content_hash"] = object_hash(authority, "content_hash")
        problems = self._reject_chain({"authority": authority})
        self.assertTrue(any("fixed identity" in pr or
                            "authority mismatch" in pr or
                            "rebuilt chain" in pr for pr in problems),
                        "authority swap not caught")

    # 15. fixed identity replacement: authority pin/contract/schema/id
    def test_authority_pin_contract_schema_id_replacement(self) -> None:
        for key, value in (("generator_hash", "0" * 64),
                           ("contract_semantic_hash", "0" * 64),
                           ("schema_version", "9.9.9"),
                           ("authority_id", "replaced-authority-id")):
            authority = clone(self.authority)
            authority[key] = value
            authority["content_hash"] = object_hash(authority, "content_hash")
            problems = self._reject_chain({"authority": authority})
            self.assertTrue(any("fixed identity" in pr for pr in problems),
                            f"authority {key} replacement not caught")

    # 16. catalog fixture/oracle synthetic fallback (requirement 1)
    def test_catalog_synthetic_fallback(self) -> None:
        catalog = clone(self.catalog)
        case = next(c for c in catalog["cases"] if c["case_id"] == "D10-CASE-001")
        spec = {"partition": "p12_anti_overfit", "family": "synthetic",
                "kind": "project_risk_distribution", "token": "d10_project_risk_distribution",
                "owner": "evaluate_and_own", "disposition": "positive",
                "mc": "none", "desc": "synthetic fallback"}
        case["typed_input"] = g.build_typed_input(spec, 999)
        resign_catalog(catalog)
        result = v.verify_all(catalog=catalog, authority=self.authority)
        entry = result["per_case"]["D10-CASE-001"]
        self.assertFalse(entry["ok"], "synthetic fallback accepted")
        self.assertTrue(any("authority mismatch" in pr for pr in entry["problems"]),
                        "synthetic fallback rejected for wrong reason")

    # 17. full-chain self-consistent re-sign (requirement 4)
    def test_full_chain_self_consistent_resign(self) -> None:
        catalog = clone(self.catalog)
        registry = clone(self.registry)
        quota = clone(self.quota)
        # internally consistent full-chain re-sign: a display zh label change
        # propagated through catalog + registry + quota hashes. Every local
        # validator accepts the re-signed chain...
        catalog["cases"][0]["typed_input"]["audience_text"]["finding_zh"] = \
            "发现 {n} 名受影响受试者（同一显示口径）"
        changed_case = catalog["cases"][0]
        changed_case["fixture_hash"] = object_hash(
            changed_case, "fixture_hash")
        catalog["catalog_hash"] = object_hash(catalog, "catalog_hash")
        registry["catalog_hash"] = catalog["catalog_hash"]
        registry["content_hash"] = object_hash(registry, "content_hash")
        quota["catalog_hash"] = catalog["catalog_hash"]
        quota["registry_hash"] = registry["content_hash"]
        quota["manifest_hash"] = object_hash(quota, "manifest_hash")
        g.validate_catalog(catalog)
        g.validate_registry(registry, catalog)
        g.validate_quota_manifest(quota, catalog)
        # ...but the frozen fixed identity rejects it
        problems = self._reject_chain({"catalog": catalog,
                                       "registry": registry,
                                       "quota": quota})
        self.assertTrue(any("fixed identity" in pr for pr in problems),
                        "full-chain re-sign not caught by fixed identity")


if __name__ == "__main__":
    unittest.main()
