"""R5 S1 W2 -- real typed-object tests for the read-only D10 authority adapter.

Builds real R4 typed objects through the R4 test-only frozen-artifact adapter
(read-only; the same flow as the R4 oracle-parity suite), evaluates them with
the deterministic R4 evaluator, projects them with the R4 projection layer,
and exercises the R5 authority adapter against those real objects:

* exact receipt bindings on real positive/negative/boundary/hidden-member/
  hidden-site/cutoff cases;
* canonical visibility-decision hash recipe (independently recomputed);
* all 16 frozen S1 authority challenge slots fail closed
  (8 ``authority_identity`` receipt slots + 8 ``authority_visibility``
  slots, using the frozen ``mutated::`` values of ``exact_contract.json``);
* cross-object substitution (version/projection from another evaluation)
  rejects before emission;
* real R4 integrity-gated fixtures reject where the R4 identity/content
  binding itself is broken (no receipt for a broken authority);
* hidden member/site identities never leak into the receipt or the public
  partition API;
* deterministic replay: source pair order never changes the receipt;
* no mutation of inputs; static closure of the adapter (no file IO, no
  forbidden imports, no case/fixture/test-name/sentinel branches).

Offline only: no network, no browser, no services, no writes outside the
frozen R4 artifact reads the R4 test adapter performs.
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, Tuple

_POC_ROOT = Path(__file__).resolve().parents[2]
_R5_SRC = Path(__file__).resolve().parents[1] / "src"
_R4_SRC = _POC_ROOT / "medical_monitoring_ai_native_r4" / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC, _R5_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4 import d10_adapter as r4_adapter  # noqa: E402
from mm_r4 import d10_evaluator as r4_evaluator  # noqa: E402
from mm_r4 import d10_projection as r4_projection  # noqa: E402
from mm_r4.d10_contracts import (  # noqa: E402
    d10_canonical_json,
    d10_sha256_text,
)
from mm_r5.authority_adapter import (  # noqa: E402
    DEFAULT_D10_AUTHORITY_ADAPTER_VARIANT,
    R5_PROJECTION_KINDS,
    AuthorityReceiptError,
    R5AuthorityReceipt,
    authority_receipt_dict,
    build_authority_receipt,
    compute_visibility_decision_hash,
    d10_visibility_decision_canonical_dict,
    projectable_partition,
    verify_authority_receipt,
)

# Frozen exact_contract.json v0.3.1 object keys (receipt and pair).
R5_AUTHORITY_RECEIPT_KEYS = frozenset((
    "project_ref", "run_ref", "snapshot_ref", "cutoff_ref",
    "public_projection_id", "public_projection_content_hash",
    "public_projection_kind", "evaluation_content_identities",
    "audience_contract_id", "visibility_decision_id",
    "visibility_decision_hash", "source_revision_content_pairs",
))
SOURCE_PAIR_KEYS = frozenset(("revision_id", "content_hash"))

# Frozen challenge slot values (exact_contract.json challenge_rules).
_AUTH_IDENTITY_MUTATIONS: Tuple[Tuple[str, str, Any], ...] = (
    ("project_ref", "authority_identity.project_ref",
     "mutated::authority_identity::project_ref"),
    ("run_ref", "authority_identity.run_ref",
     "mutated::authority_identity::run_ref"),
    ("snapshot_ref", "authority_identity.snapshot_ref",
     "mutated::authority_identity::snapshot_ref"),
    ("cutoff_ref", "authority_identity.cutoff_ref",
     "mutated::authority_identity::cutoff_ref"),
    ("public_projection_id", "authority_identity.projection_id",
     "mutated::authority_identity::projection_id"),
    ("public_projection_content_hash", "authority_identity.projection_content_hash",
     "mutated::authority_identity::projection_content_hash"),
    ("evaluation_content_identities", "authority_identity.evaluation_content_identity",
     ("mutated::authority_identity::evaluation_content_identity",)),
    ("audience_contract_id", "authority_identity.audience_contract_id",
     "mutated::authority_identity::audience_contract_id"),
)
MUTATED_HASH = "f" * 64
_AUTH_VISIBILITY_TYPED_MUTATIONS: Tuple[Tuple[str, str, str], ...] = (
    ("projectable_member_refs", "authority_visibility.projectable_member",
     "mutated::authority_visibility::projectable_member"),
    ("hidden_member_refs", "authority_visibility.hidden_member",
     "mutated::authority_visibility::hidden_member"),
    ("projectable_site_refs", "authority_visibility.projectable_site",
     "mutated::authority_visibility::projectable_site"),
    ("hidden_site_refs", "authority_visibility.hidden_site",
     "mutated::authority_visibility::hidden_site"),
)

_CATALOG_CACHE: Dict[str, Any] = {}


def _catalog() -> Any:
    if "catalog" not in _CATALOG_CACHE:
        _CATALOG_CACHE["catalog"], _CATALOG_CACHE["authority"] = (
            r4_adapter.load_artifacts()[0], r4_adapter.load_authority())
    return _CATALOG_CACHE


def _case_bundle(case_id: str) -> Tuple[Any, Any, Any]:
    """Real R4 bundle: (typed, projection_version, project_projection)."""
    catalog, authority = _catalog()["catalog"], _catalog()["authority"]
    case = next(c for c in catalog["cases"] if c["case_id"] == case_id)
    entry = next(e for e in authority["entries"] if e["case_id"] == case_id)
    typed = r4_adapter.build_typed_input(case["typed_input"])
    result = r4_evaluator.evaluate(typed, r4_adapter.build_authority(entry))
    version = r4_projection.build_d10_projection_version(typed, result)
    projection = r4_projection.build_d10_project_projection(typed, result)
    return typed, version, projection


# ---------------------------------------------------------------------------
# Real-fixture receipt bindings
# ---------------------------------------------------------------------------


class TestD10AuthorityAdapterRealFixtures(unittest.TestCase):
    def test_receipt_on_real_positive_with_hidden_members(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-009")
        receipt = build_authority_receipt(typed, version, projection)
        self.assertTrue(verify_authority_receipt(
            receipt, typed, version, projection)["valid"])
        self.assertEqual(receipt.project_ref, typed.project_ref)
        self.assertEqual(receipt.project_ref, version.project_ref)
        self.assertEqual(receipt.run_ref, typed.run_ref)
        self.assertEqual(receipt.snapshot_ref, typed.snapshot_ref)
        self.assertEqual(receipt.cutoff_ref, version.cutoff_ref)
        self.assertEqual(receipt.public_projection_id, projection.projection_id)
        self.assertEqual(receipt.public_projection_content_hash,
                         projection.projection_content_hash)
        self.assertEqual(receipt.evaluation_content_identities,
                         tuple(sorted(set(version.source_evaluation_content_identities))))
        self.assertEqual(receipt.audience_contract_id, version.audience_contract_ref)
        self.assertEqual(receipt.visibility_decision_id,
                         typed.visibility_decision.decision_id)
        self.assertEqual([p.revision_id for p in receipt.source_revision_content_pairs],
                         [p.revision_id for p in typed.source_revision_content_pairs])
        # Real hidden-member case: the partition survives on the typed side.
        self.assertGreater(len(typed.visibility_decision.hidden_member_refs), 0)

    def test_receipt_on_real_cutoff_and_no_cutoff(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-010")
        receipt = build_authority_receipt(typed, version, projection)
        self.assertEqual(receipt.cutoff_ref, "SYN-D10-CUT-010")
        typed2, version2, projection2 = _case_bundle("D10-CASE-001")
        receipt2 = build_authority_receipt(typed2, version2, projection2)
        self.assertEqual(version2.cutoff_ref, None)
        self.assertIsNone(receipt2.cutoff_ref)

    def test_receipt_on_real_negative_and_boundary(self) -> None:
        for case_id in ("D10-CASE-002", "D10-CASE-003"):
            typed, version, projection = _case_bundle(case_id)
            receipt = build_authority_receipt(typed, version, projection)
            self.assertTrue(verify_authority_receipt(
                receipt, typed, version, projection)["valid"], case_id)

    def test_receipt_on_real_hidden_site(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-262")
        receipt = build_authority_receipt(typed, version, projection)
        self.assertTrue(verify_authority_receipt(
            receipt, typed, version, projection)["valid"])
        self.assertEqual(len(typed.visibility_decision.hidden_site_refs), 1)

    def test_receipt_fields_pin_frozen_contract_keys(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-001")
        receipt = build_authority_receipt(typed, version, projection)
        self.assertEqual(
            frozenset(field.name for field in dataclasses.fields(receipt)),
            R5_AUTHORITY_RECEIPT_KEYS)
        self.assertEqual(
            frozenset(field.name for field in dataclasses.fields(
                R5AuthorityReceipt)),
            R5_AUTHORITY_RECEIPT_KEYS)
        pair = receipt.source_revision_content_pairs[0]
        self.assertEqual(
            frozenset(field.name for field in dataclasses.fields(pair)),
            SOURCE_PAIR_KEYS)
        self.assertIn(receipt.public_projection_kind, R5_PROJECTION_KINDS)

    def test_visibility_decision_hash_recipe_independent_recompute(self) -> None:
        typed, version, _projection = _case_bundle("D10-CASE-009")
        receipt = build_authority_receipt(typed, version, _projection)
        pairs = sorted(
            ({"revision_id": pair.revision_id, "content_hash": pair.content_hash}
             for pair in typed.source_revision_content_pairs),
            key=lambda p: (p["revision_id"], p["content_hash"]))
        expected = d10_sha256_text(d10_canonical_json({
            "projection_version_id": version.projection_version_id,
            "source_evaluation_content_identities": sorted(
                set(version.source_evaluation_content_identities)),
            "visibility_decision": d10_visibility_decision_canonical_dict(
                typed.visibility_decision),
            "source_revision_content_pairs": pairs,
        }))
        self.assertEqual(receipt.visibility_decision_hash, expected)
        self.assertEqual(
            receipt.visibility_decision_hash,
            compute_visibility_decision_hash(typed, version))

    def test_projection_kind_comes_from_concrete_variant(self) -> None:
        variant = DEFAULT_D10_AUTHORITY_ADAPTER_VARIANT
        self.assertEqual(variant.projection_kind, "d10_project")
        self.assertIn(variant.projection_kind, R5_PROJECTION_KINDS)
        typed, version, projection = _case_bundle("D10-CASE-001")
        receipt = build_authority_receipt(
            typed, version, projection, variant=variant)
        self.assertEqual(receipt.public_projection_kind,
                         variant.projection_kind)

    def test_receipt_canonical_json_round_trip(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-001")
        receipt = build_authority_receipt(typed, version, projection)
        payload = d10_canonical_json(authority_receipt_dict(receipt))
        parsed = json.loads(payload)
        self.assertEqual(parsed["project_ref"], receipt.project_ref)
        self.assertEqual(parsed["visibility_decision_hash"],
                         receipt.visibility_decision_hash)
        self.assertEqual(
            d10_canonical_json(parsed),
            d10_canonical_json(authority_receipt_dict(receipt)))


# ---------------------------------------------------------------------------
# Frozen challenge slots: authority_identity (receipt-level tampers)
# ---------------------------------------------------------------------------


class TestD10AuthorityAdapterIdentityRejects(unittest.TestCase):
    def setUp(self) -> None:
        self.typed, self.version, self.projection = _case_bundle("D10-CASE-001")
        self.receipt = build_authority_receipt(
            self.typed, self.version, self.projection)

    def test_valid_receipt_passes(self) -> None:
        self.assertTrue(verify_authority_receipt(
            self.receipt, self.typed, self.version, self.projection)["valid"])

    def test_every_authority_identity_slot_rejects(self) -> None:
        for field_name, rule_id, mutated in _AUTH_IDENTITY_MUTATIONS:
            with self.subTest(rule_id=rule_id):
                replacement = mutated
                if field_name.endswith("hash"):
                    replacement = MUTATED_HASH
                elif field_name == "evaluation_content_identities":
                    replacement = (MUTATED_HASH,)
                tampered = dataclasses.replace(
                    self.receipt, **{field_name: replacement})
                result = verify_authority_receipt(
                    tampered, self.typed, self.version, self.projection)
                self.assertFalse(result["valid"], rule_id)
                self.assertIn(rule_id, result["reasons"], rule_id)


# ---------------------------------------------------------------------------
# Frozen challenge slots: authority_visibility
# ---------------------------------------------------------------------------


class TestD10AuthorityAdapterVisibilityRejects(unittest.TestCase):
    def setUp(self) -> None:
        self.typed, self.version, self.projection = _case_bundle("D10-CASE-009")
        self.receipt = build_authority_receipt(
            self.typed, self.version, self.projection)

    def test_visibility_decision_id_receipt_tamper_rejects(self) -> None:
        tampered = dataclasses.replace(
            self.receipt,
            visibility_decision_id=(
                "mutated::authority_visibility::visibility_decision_id"))
        result = verify_authority_receipt(
            tampered, self.typed, self.version, self.projection)
        self.assertFalse(result["valid"])
        self.assertIn("authority_visibility.visibility_decision_id",
                      result["reasons"])

    def test_visibility_decision_hash_receipt_tamper_rejects(self) -> None:
        tampered = dataclasses.replace(
            self.receipt,
            visibility_decision_hash=MUTATED_HASH)
        result = verify_authority_receipt(
            tampered, self.typed, self.version, self.projection)
        self.assertFalse(result["valid"])
        self.assertIn("authority_visibility.visibility_decision_hash",
                      result["reasons"])

    def test_typed_visibility_partition_slots_reject_before_emission(self) -> None:
        for field_name, rule_id, mutated in _AUTH_VISIBILITY_TYPED_MUTATIONS:
            with self.subTest(rule_id=rule_id):
                tampered_decision = dataclasses.replace(
                    self.typed.visibility_decision, **{field_name: (mutated,)})
                tampered_typed = dataclasses.replace(
                    self.typed, visibility_decision=tampered_decision)
                with self.assertRaises(AuthorityReceiptError, msg=rule_id):
                    build_authority_receipt(
                        tampered_typed, self.version, self.projection)
                result = verify_authority_receipt(
                    self.receipt, tampered_typed,
                    self.version, self.projection)
                self.assertFalse(result["valid"], rule_id)

    def test_typed_source_revision_slot_rejects_before_emission(self) -> None:
        pair = self.typed.source_revision_content_pairs[0]
        tampered_pair = dataclasses.replace(
            pair, revision_id="mutated::authority_visibility::source_revision")
        tampered_typed = dataclasses.replace(
            self.typed, source_revision_content_pairs=(tampered_pair,))
        with self.assertRaises(AuthorityReceiptError):
            build_authority_receipt(tampered_typed, self.version, self.projection)
        result = verify_authority_receipt(
            self.receipt, tampered_typed, self.version, self.projection)
        self.assertFalse(result["valid"])
        self.assertIn("authority_visibility.source_revision", result["reasons"])

    def test_typed_source_content_hash_slot_rejects_before_emission(self) -> None:
        pair = self.typed.source_revision_content_pairs[0]
        tampered_pair = dataclasses.replace(
            pair, content_hash="mutated::authority_visibility::source_content_hash")
        tampered_typed = dataclasses.replace(
            self.typed, source_revision_content_pairs=(tampered_pair,))
        with self.assertRaises(AuthorityReceiptError):
            build_authority_receipt(tampered_typed, self.version, self.projection)
        result = verify_authority_receipt(
            self.receipt, tampered_typed, self.version, self.projection)
        self.assertFalse(result["valid"])
        self.assertIn("authority_visibility.source_content_hash",
                      result["reasons"])

    def test_receipt_source_pair_slots_reject(self) -> None:
        pair = self.receipt.source_revision_content_pairs[0]
        tampered_revision = dataclasses.replace(
            self.receipt,
            source_revision_content_pairs=(dataclasses.replace(
                pair, revision_id="mutated::authority_visibility::source_revision"),))
        result = verify_authority_receipt(
            tampered_revision, self.typed, self.version, self.projection)
        self.assertFalse(result["valid"])
        self.assertIn("authority_visibility.source_revision", result["reasons"])
        tampered_hash = dataclasses.replace(
            self.receipt,
            source_revision_content_pairs=(dataclasses.replace(
                pair, content_hash=MUTATED_HASH),))
        result = verify_authority_receipt(
            tampered_hash, self.typed, self.version, self.projection)
        self.assertFalse(result["valid"])
        self.assertIn("authority_visibility.source_content_hash",
                      result["reasons"])


# ---------------------------------------------------------------------------
# Cross-object substitution and structural breakage
# ---------------------------------------------------------------------------


class TestD10AuthorityAdapterCrossObjectRejects(unittest.TestCase):
    def test_version_from_another_evaluation_rejects(self) -> None:
        typed, _v1, projection = _case_bundle("D10-CASE-001")
        _t2, version2, _p2 = _case_bundle("D10-CASE-002")
        with self.assertRaises(AuthorityReceiptError):
            build_authority_receipt(typed, version2, projection)

    def test_projection_from_another_evaluation_rejects(self) -> None:
        typed, version, _p1 = _case_bundle("D10-CASE-001")
        _t2, _v2, projection2 = _case_bundle("D10-CASE-002")
        with self.assertRaises(AuthorityReceiptError):
            build_authority_receipt(typed, version, projection2)

    def test_mutated_typed_envelope_identity_rejects(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-001")
        tampered = dataclasses.replace(
            typed, project_ref="mutated::authority_identity::project_ref")
        with self.assertRaises(AuthorityReceiptError):
            build_authority_receipt(tampered, version, projection)

    def test_version_without_decision_ref_rejects(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-001")
        broken = dataclasses.replace(version, visibility_decision_refs=())
        with self.assertRaises(AuthorityReceiptError):
            build_authority_receipt(typed, broken, projection)

    def test_version_without_evaluation_identities_rejects(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-001")
        broken = dataclasses.replace(
            version, source_evaluation_content_identities=())
        with self.assertRaises(AuthorityReceiptError):
            build_authority_receipt(typed, broken, projection)

    def test_projection_content_hash_mismatch_rejects(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-001")
        tampered = dataclasses.replace(
            projection,
            projection_content_hash=MUTATED_HASH)
        with self.assertRaises(AuthorityReceiptError):
            build_authority_receipt(typed, version, tampered)


# ---------------------------------------------------------------------------
# Real R4 integrity-gated fixtures fail closed
# ---------------------------------------------------------------------------


class TestD10AuthorityAdapterRealGatedFixtures(unittest.TestCase):
    def test_hidden_member_dropped_fixture_rejects(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-276")
        with self.assertRaises(AuthorityReceiptError) as ctx:
            build_authority_receipt(typed, version, projection)
        self.assertIn("authority_visibility.member_partition", str(ctx.exception))

    def test_duplicate_source_pair_fixture_rejects(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-288")
        with self.assertRaises(AuthorityReceiptError) as ctx:
            build_authority_receipt(typed, version, projection)
        self.assertIn("source_pairs_duplicate", str(ctx.exception))

    def test_noncanonical_visibility_fixture_rejects(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-089")
        with self.assertRaises(AuthorityReceiptError) as ctx:
            build_authority_receipt(typed, version, projection)
        self.assertIn("visibility_decision_noncanonical", str(ctx.exception))


# ---------------------------------------------------------------------------
# Hidden identities never leak
# ---------------------------------------------------------------------------


class TestD10AuthorityAdapterHiddenLeak(unittest.TestCase):
    def test_hidden_member_refs_absent_from_receipt_json(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-263")
        receipt = build_authority_receipt(typed, version, projection)
        hidden = set(typed.visibility_decision.hidden_member_refs)
        self.assertGreater(len(hidden), 0)
        serialized = d10_canonical_json(authority_receipt_dict(receipt))
        for ref in hidden:
            self.assertNotIn(ref, serialized)

    def test_hidden_site_ref_absent_from_receipt_json(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-262")
        receipt = build_authority_receipt(typed, version, projection)
        hidden = set(typed.visibility_decision.hidden_site_refs)
        self.assertGreater(len(hidden), 0)
        serialized = d10_canonical_json(authority_receipt_dict(receipt))
        for ref in hidden:
            self.assertNotIn(ref, serialized)

    def test_projectable_partition_never_returns_hidden_refs(self) -> None:
        for case_id in ("D10-CASE-263", "D10-CASE-262", "D10-CASE-009"):
            with self.subTest(case_id=case_id):
                typed, _v, _p = _case_bundle(case_id)
                partition = projectable_partition(typed)
                hidden_members = set(typed.visibility_decision.hidden_member_refs)
                hidden_sites = set(typed.visibility_decision.hidden_site_refs)
                self.assertTrue(
                    hidden_members.isdisjoint(partition["projectable_member_refs"]))
                self.assertTrue(
                    hidden_sites.isdisjoint(partition["projectable_site_refs"]))
                self.assertEqual(
                    partition["hidden_member_count"],
                    typed.visibility_decision.hidden_member_count)
                self.assertEqual(
                    partition["hidden_site_count"],
                    typed.visibility_decision.hidden_site_count)
                self.assertEqual(
                    partition["projectable_member_refs"],
                    tuple(sorted(set(
                        typed.visibility_decision.projectable_member_refs))))
                self.assertEqual(
                    partition["projectable_site_refs"],
                    tuple(sorted(set(
                        typed.visibility_decision.projectable_site_refs))))

    def test_projectable_partition_rejects_hidden_member_overlap(self) -> None:
        typed, _version, _projection = _case_bundle("D10-CASE-263")
        hidden_ref = typed.visibility_decision.hidden_member_refs[0]
        tampered = dataclasses.replace(
            typed,
            visibility_decision=dataclasses.replace(
                typed.visibility_decision,
                projectable_member_refs=tuple(sorted(set(
                    typed.visibility_decision.projectable_member_refs
                    + (hidden_ref,))))))
        with self.assertRaises(AuthorityReceiptError) as ctx:
            projectable_partition(tampered)
        self.assertIn("authority_visibility.member_partition", str(ctx.exception))

    def test_projectable_partition_rejects_hidden_site_overlap(self) -> None:
        typed, _version, _projection = _case_bundle("D10-CASE-262")
        hidden_ref = typed.visibility_decision.hidden_site_refs[0]
        tampered = dataclasses.replace(
            typed,
            visibility_decision=dataclasses.replace(
                typed.visibility_decision,
                projectable_site_refs=tuple(sorted(set(
                    typed.visibility_decision.projectable_site_refs
                    + (hidden_ref,))))))
        with self.assertRaises(AuthorityReceiptError) as ctx:
            projectable_partition(tampered)
        self.assertIn("authority_visibility.site_partition", str(ctx.exception))


# ---------------------------------------------------------------------------
# Deterministic replay and immutability
# ---------------------------------------------------------------------------


class TestD10AuthorityAdapterDeterministicReplay(unittest.TestCase):
    def test_source_pair_order_never_changes_receipt(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-009")
        # Sign a legitimate second source revision pair for the same locator
        # set, then compare receipts under both orders.
        locator_ids = tuple(sorted(set(
            locator for member in typed.members
            for locator in member.source_locator_refs) | {
                ref.locator_id for ref in typed.evidence_refs}))
        extra = dataclasses.replace(
            typed.source_revision_content_pairs[0],
            revision_id="SRC-REV-009-EXTRA")
        extra_hash = d10_sha256_text(d10_canonical_json({
            "revision_id": extra.revision_id,
            "source_locators": list(locator_ids),
        }))
        extra_pair = dataclasses.replace(extra, content_hash=extra_hash)
        pairs_a = typed.source_revision_content_pairs + (extra_pair,)
        pairs_b = (extra_pair,) + typed.source_revision_content_pairs
        typed_a = dataclasses.replace(typed, source_revision_content_pairs=pairs_a)
        typed_b = dataclasses.replace(typed, source_revision_content_pairs=pairs_b)
        receipt_a = build_authority_receipt(typed_a, version, projection)
        receipt_b = build_authority_receipt(typed_b, version, projection)
        self.assertEqual(receipt_a, receipt_b)


class TestD10AuthorityAdapterNoMutation(unittest.TestCase):
    def test_build_does_not_mutate_inputs(self) -> None:
        typed, version, projection = _case_bundle("D10-CASE-009")
        typed_before = dataclasses.asdict(typed)
        version_before = dataclasses.asdict(version)
        projection_before = dataclasses.asdict(projection)
        build_authority_receipt(typed, version, projection)
        verify_authority_receipt(
            build_authority_receipt(typed, version, projection),
            typed, version, projection)
        self.assertEqual(dataclasses.asdict(typed), typed_before)
        self.assertEqual(dataclasses.asdict(version), version_before)
        self.assertEqual(dataclasses.asdict(projection), projection_before)


# ---------------------------------------------------------------------------
# Static closure of the adapter source
# ---------------------------------------------------------------------------


class TestD10AuthorityAdapterStaticClosure(unittest.TestCase):
    def _source(self) -> str:
        path = Path(__file__).resolve().parents[1] / "src" / "mm_r5" / "authority_adapter.py"
        return path.read_text(encoding="utf-8")

    def test_no_forbidden_tokens_or_io(self) -> None:
        source = self._source()
        for token in ("case_id", "fixture_id", "test_name", "mutation_class",
                      "SYN-", "open(", "json.load", "Path(", "read_text",
                      "read_bytes", "import json"):
            self.assertNotIn(token, source, token)
        self.assertIsNone(re.search(
            r"D10-(CASE|FIXTURE|ORACLE|MANIFEST|TEST)-\d+", source))

    def test_no_r4_runtime_or_artifact_imports(self) -> None:
        source = self._source()
        for token in ("import d10_evaluator", "from .d10_evaluator",
                      "from mm_r4.d10_evaluator", "import d10_adapter",
                      "from mm_r4.d10_adapter", "import ensemble",
                      "from mm_r4.ensemble", "import requests",
                      "import urllib", "import json"):
            self.assertNotIn(token, source, token)


# ---------------------------------------------------------------------------
# Full real-fixture sweep: every valid case emits, every broken one fails
# ---------------------------------------------------------------------------


class TestD10AuthorityAdapterFullValidSweep(unittest.TestCase):
    def test_all_real_valid_fixtures_emit_and_broken_ones_fail_closed(self) -> None:
        catalog, authority = _catalog()["catalog"], _catalog()["authority"]
        valid = [c for c in catalog["cases"] if c.get("mutation_class") == "none"]
        self.assertEqual(len(valid), 221)
        emitted: Dict[str, int] = {}
        rejected: Dict[str, str] = {}
        for case in valid:
            entry = next(e for e in authority["entries"]
                         if e["case_id"] == case["case_id"])
            typed = r4_adapter.build_typed_input(case["typed_input"])
            result = r4_evaluator.evaluate(
                typed, r4_adapter.build_authority(entry))
            version = r4_projection.build_d10_projection_version(typed, result)
            projection = r4_projection.build_d10_project_projection(
                typed, result)
            try:
                receipt = build_authority_receipt(typed, version, projection)
                self.assertTrue(verify_authority_receipt(
                    receipt, typed, version, projection)["valid"],
                    case["case_id"])
                emitted[result.disposition_or_gate] = (
                    emitted.get(result.disposition_or_gate, 0) + 1)
            except AuthorityReceiptError as error:
                rejected[case["case_id"]] = str(error)
                # A rejected authority always corresponds to an R4
                # integrity-gated evaluation (fail closed, never a false
                # reject on an authoritative R4 result).
                self.assertEqual(result.disposition_or_gate, "integrity_gate",
                                 case["case_id"])
        # 221 - 8 broken = 213 emitted.
        self.assertEqual(sum(emitted.values()), 213)
        self.assertEqual(len(rejected), 8)
        for case_id in ("D10-CASE-089", "D10-CASE-108", "D10-CASE-188",
                        "D10-CASE-271", "D10-CASE-272", "D10-CASE-276",
                        "D10-CASE-285", "D10-CASE-288"):
            self.assertIn(case_id, rejected)


if __name__ == "__main__":
    unittest.main()
