"""R4-D09 negative mutation suite: outcome-changing facts fail closed,
surface-only metadata stays inert.

Mutates locally constructed typed inputs and the frozen catalog's typed
inputs (the catalog itself is never written) and verifies the runtime
reacts deterministically:

* semantic mutations (subject/cutoff/origin/locator-resolution/coverage/
  source-verification/visibility partitions) must change the assembled
  leaves or raise the typed-validation error -- never silently produce the
  original outcome;
* typed-schema violations (invalid closed enums, non-hash hashes, stale
  authority content hash, Query proof/member-partition tamper) must raise
  :class:`~mm_r4.d09_contracts.D09ContractError` from the adapter parse;
* projection-level visibility partition conflicts must raise
  :class:`~mm_r4.d09_projection.D09ProjectionError`;
* Query evidence tampering (independent and combined, including a
  recomputed content hash) must fail closed in
  :func:`~mm_r4.d09_projection.validate_query_draft`;
* R2 handoff identity tampering must fail closed in
  :func:`~mm_r4.d09_projection.validate_d09_r2_handoff` (handoff hash
  recomputation) while every accepted action regression stays valid;
* inert surface metadata (mutation description prose, anti-overfit variant
  records, envelope id) must keep the exact original leaves.

The runtime is never branched on case identifiers; case ids are used only
as test-side catalog fixture selection (the frozen adapter is the only
artifact reader).
"""

from __future__ import annotations

import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_ROOT = Path(__file__).resolve().parents[1]
_R4_SRC = _R4_ROOT / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from mm_r4.d09_contracts import (  # noqa: E402
    AntiOverfitVariant,
    D09ContractError,
    d09_content_hash,
)
from mm_r4.d09_evaluator import evaluate  # noqa: E402
from mm_r4.d09_projection import (  # noqa: E402
    D09ProjectionError,
    build_d09_audience_projection,
    build_d09_query_draft,
    build_d09_r2_handoff,
    validate_d09_r2_handoff,
    validate_query_draft,
)

from test_d09_adapter import (  # noqa: E402
    CATALOG_FILE_SHA256,
    CATALOG_PATH,
    ORACLE_FILE_SHA256,
    ORACLE_PATH,
    REGISTRY_FILE_SHA256,
    REGISTRY_PATH,
    assemble_leaf_sets,
    case_index,
    load_artifacts,
    parse_typed_input,
    run_case,
    sha256_bytes,
)


def _clone(catalog: dict, case_id: str) -> dict:
    return json.loads(json.dumps(catalog["cases"][int(case_id.split("-")[-1]) - 1]))


def _leaves(case: dict) -> dict:
    typed, result = run_case(case)
    leaf, trace, source = assemble_leaf_sets(typed, result, case_index(case))
    return {"expected_leaf_set": leaf, "expected_trace_leaf_set": trace,
            "expected_source_leaf_set": source}


def _run(case: dict):
    """Parse + validate + evaluate a mutated catalog envelope."""
    return run_case(case)


def _reseal_query_decision(case: dict) -> None:
    """Re-seal the Query redundancy decision's typed hashes for the current
    member set (test-side replica of the contract validator's recipes)."""
    members = case["typed_input"]["subject_risk_members"]
    decision = case["typed_input"]["query_redundancy_decision"]
    member_ids = sorted(member["member_id"] for member in members)
    member_queries = sorted({
        ref for member in members
        for ref in member.get("query_draft_refs", [])})
    decision["unit_member_set_hash"] = d09_content_hash(member_ids)
    decision["covered_member_refs"] = []
    decision["uncovered_member_refs"] = member_ids
    decision["member_query_refs"] = member_queries
    decision["coverage_proof_hash"] = d09_content_hash({
        "decision": decision["decision"],
        "covered": [],
        "uncovered": member_ids,
        "member_queries": list(member_queries),
        "fanout": decision["max_query_member_fanout"],
    })


class TestMutationSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog, cls.oracle, cls.registry, _quota = load_artifacts()
        cls.by_id = {c["case_id"]: c for c in cls.catalog["cases"]}
        cls.expectations = {e["case_id"]: e
                            for e in cls.oracle["ordered_expectations"]}

    def tearDown(self) -> None:
        # frozen files must never change
        self.assertEqual(sha256_bytes(CATALOG_PATH.read_bytes()),
                         CATALOG_FILE_SHA256)
        self.assertEqual(sha256_bytes(ORACLE_PATH.read_bytes()),
                         ORACLE_FILE_SHA256)
        self.assertEqual(sha256_bytes(REGISTRY_PATH.read_bytes()),
                         REGISTRY_FILE_SHA256)

    # ------------------------------------------------------------------
    # Semantic member mutations (outcome-changing)
    # ------------------------------------------------------------------

    def test_wrong_subject_mutation_changes_outcome(self) -> None:
        case = _clone(self.catalog, "D09-CASE-047")  # positive same-origin pair
        original = _leaves(case)
        case["typed_input"]["subject_risk_members"][0][
            "subject_stable_id"] = "SYN-D09-SUBJ-999"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "cross-subject member must change the outcome")
        self.assertEqual(mutated["expected_leaf_set"]["l2.affected_subject_count"],
                         3)

    def test_cutoff_all_out_mutation_fails_closed(self) -> None:
        case = _clone(self.catalog, "D09-CASE-047")
        original = _leaves(case)
        for member in case["typed_input"]["subject_risk_members"]:
            member["cutoff_relation"] = "out_of_cutoff"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "all-out-of-cutoff must change the outcome")
        self.assertEqual(mutated["expected_leaf_set"]["units.0.l1_disposition"],
                         "not_evaluable")
        self.assertEqual(mutated["expected_leaf_set"]["l2.affected_subject_count"],
                         0)
        self.assertEqual(mutated["expected_leaf_set"]["l2.event_count"], 0)

    def test_origin_dedup_flip_changes_outcome(self) -> None:
        case = _clone(self.catalog, "D09-CASE-047")
        original = _leaves(case)
        for member in case["typed_input"]["subject_risk_members"]:
            member["origin_decision"] = "distinct"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "verified-same-origin dedup flip must change counts")
        self.assertEqual(mutated["expected_leaf_set"]["l2.individual_risk_count"],
                         4)
        self.assertEqual(mutated["expected_leaf_set"]["l2.affected_subject_count"],
                         2)
        self.assertEqual(mutated["expected_leaf_set"]["l2.source_record_count"],
                         4)

    def test_n1_member_added_crosses_authority_threshold(self) -> None:
        case = _clone(self.catalog, "D09-CASE-007")  # n=1 boundary
        original = _leaves(case)
        template = case["typed_input"]["subject_risk_members"][0]
        extra = json.loads(json.dumps(template))
        extra["member_id"] = "SYN-D09-RISK-007-02"
        extra["subject_stable_id"] = "SYN-D09-SUBJ-007-02"
        extra["public_r4_risk_identity"] = "SYN-D09-RISKID-007-02"
        extra["source_event_identity"] = "SYN-D09-EVT-007-02"
        extra["source_locator_refs"] = ["SYN-D09-LOC-007-02"]
        case["typed_input"]["subject_risk_members"].append(extra)
        # the Query redundancy decision is bound to the member set: re-seal
        # its typed hashes for the enlarged set (test-side recipe replica of
        # the contract validator), then the runtime decides on the facts
        _reseal_query_decision(case)
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "second member must clear the n1 boundary")
        self.assertEqual(mutated["expected_leaf_set"]["units.0.l1_disposition"],
                         "positive")

    # ------------------------------------------------------------------
    # Locator / evidence resolution (contract section 11 fail-closed)
    # ------------------------------------------------------------------

    def test_locator_resolution_missing_changes_outcome(self) -> None:
        case = _clone(self.catalog, "D09-CASE-047")
        original = _leaves(case)
        case["typed_input"]["subject_risk_members"][0][
            "source_locator_resolution_state"] = "missing"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "unresolvable locator must fail closed")
        self.assertEqual(mutated["expected_leaf_set"]["units.0.l1_disposition"],
                         "boundary")
        self.assertEqual(mutated["expected_leaf_set"]["l2.risk_count"], 0)
        self.assertEqual(mutated["expected_leaf_set"]["l2.query_count"], 0)

    # ------------------------------------------------------------------
    # Coverage / source verification
    # ------------------------------------------------------------------

    def test_coverage_missing_changes_disposition(self) -> None:
        case = _clone(self.catalog, "D09-CASE-001")
        original = _leaves(case)
        case["typed_input"]["coverage"][0]["l0_status"] = "missing"
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original)
        self.assertEqual(mutated["expected_leaf_set"]["units.0.l1_disposition"],
                         "not_evaluable")
        self.assertEqual(mutated["expected_leaf_set"]["units.0.primary_reason"],
                         "coverage_hole")

    def test_source_verification_mismatch_fails_closed(self) -> None:
        case = _clone(self.catalog, "D09-CASE-001")
        original = _leaves(case)
        record = case["typed_input"]["source_verification_records"][0]
        record["verification_state"] = "mismatch"
        record["verified_content_hash"] = "5" * 64
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original)
        self.assertEqual(mutated["expected_leaf_set"]["units.0.l1_disposition"],
                         "not_evaluable")
        self.assertEqual(mutated["expected_leaf_set"]["units.0.primary_reason"],
                         "source_hash_mismatch")

    # ------------------------------------------------------------------
    # Typed-schema violations (closed vocabularies / hashes / proofs)
    # ------------------------------------------------------------------

    def test_invalid_closed_enum_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-001")
        case["typed_input"]["coverage"][0]["l0_status"] = "bogus"
        with self.assertRaises(D09ContractError):
            parse_typed_input(case)

    def test_invalid_hash_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-001")
        case["typed_input"]["source_content_hashes"][0] = "not-a-hash"
        with self.assertRaises(D09ContractError):
            parse_typed_input(case)

    def test_authority_threshold_tamper_rejected(self) -> None:
        """Mutating the resolved authority without a matching content hash is
        a stale-authority tamper and fails closed before evaluation."""
        case = _clone(self.catalog, "D09-CASE-047")
        case["typed_input"]["resolved_authority_decision"][
            "minimum_member_subject_count"] = 5
        with self.assertRaises(D09ContractError):
            parse_typed_input(case)

    def test_query_decision_tamper_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-081")
        case["typed_input"]["query_redundancy_decision"][
            "decision"] = "members_unlistable"
        with self.assertRaises(D09ContractError):
            parse_typed_input(case)

    def test_query_member_partition_tamper_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-081")
        case["typed_input"]["query_redundancy_decision"][
            "uncovered_member_refs"][0] = "SYN-D09-BOGUS-REF"
        with self.assertRaises(D09ContractError):
            parse_typed_input(case)

    def test_query_proof_hash_tamper_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-081")
        case["typed_input"]["query_redundancy_decision"][
            "coverage_proof_hash"] = "a" * 64
        with self.assertRaises(D09ContractError):
            parse_typed_input(case)

    def test_query_unit_member_set_hash_tamper_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-081")
        case["typed_input"]["query_redundancy_decision"][
            "unit_member_set_hash"] = "b" * 64
        with self.assertRaises(D09ContractError):
            parse_typed_input(case)

    # ------------------------------------------------------------------
    # Visibility partitions (projection fail-closed)
    # ------------------------------------------------------------------

    def test_visibility_unhide_changes_audience_leaves(self) -> None:
        case = _clone(self.catalog, "D09-CASE-147")
        original = _leaves(case)
        case["typed_input"]["visibility_decision"]["hidden_member_refs"] = []
        mutated = _leaves(case)
        self.assertNotEqual(mutated, original,
                            "unhiding members must change the audience plane")
        self.assertEqual(mutated["expected_source_leaf_set"]
                         ["source.hidden_node_count"], 0)
        self.assertEqual(mutated["expected_leaf_set"]["l2.query_count"], 1)

    def test_visibility_projectable_hidden_overlap_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-147")
        case["typed_input"]["visibility_decision"]["projectable_member_refs"] = (
            case["typed_input"]["visibility_decision"]["hidden_member_refs"])
        typed, result = _run(case)
        with self.assertRaises(D09ProjectionError):
            build_d09_audience_projection(typed, result)

    def test_visibility_unknown_hidden_ref_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-147")
        case["typed_input"]["visibility_decision"][
            "hidden_member_refs"] = ["SYN-D09-NO-SUCH"]
        typed, result = _run(case)
        with self.assertRaises(D09ProjectionError):
            build_d09_audience_projection(typed, result)

    # ------------------------------------------------------------------
    # Query evidence tampering (draft validation fail-closed)
    # ------------------------------------------------------------------

    def test_query_evidence_tamper_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-047")
        typed, result = _run(case)
        self.assertEqual(result.query_count, 1)
        draft = build_d09_query_draft(typed, result)
        self.assertIsNotNone(draft)
        assert draft is not None
        forged_locator = "SYN-D09-FORGED-LOCATOR"

        # independent tamper: evidence_refs only
        tampered = replace(draft, evidence_refs=(forged_locator,))
        validation = validate_query_draft(tampered, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("evidence_not_locatable_projectable",
                      validation["reasons"])
        self.assertIn("source_locator_ids_mismatch", validation["reasons"])

        # combined tamper with a recomputed content hash: the draft stays
        # rejected because the evidence set must equal the deterministic
        # locator set of the complete member list
        def _recompute_hash(d: object) -> str:
            return d09_content_hash({
                "query_draft_id": d.query_draft_id,
                "unit_stable_core": d.unit_stable_core,
                "query_owner": d.query_owner,
                "basis_sentence": d.basis_sentence,
                "finding_sentence": d.finding_sentence,
                "action_sentence": d.action_sentence,
                "member_refs": list(d.member_refs),
                "evidence_refs": list(d.evidence_refs),
                "source_locator_ids": list(d.source_locator_ids),
                "scope_binding_id": d.scope_binding_id,
                "redundancy_decision": d.redundancy_decision,
                "max_query_member_fanout": d.max_query_member_fanout,
                "basis_refs": list(d.basis_refs),
                "source_revision_refs": list(d.source_revision_refs),
            })

        forged = replace(
            draft,
            evidence_refs=(forged_locator,),
            source_locator_ids=(forged_locator,),
            content_hash=_recompute_hash(replace(
                draft, evidence_refs=(forged_locator,),
                source_locator_ids=(forged_locator,))))
        validation = validate_query_draft(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("evidence_not_locatable_projectable",
                      validation["reasons"])
        self.assertNotIn("content_hash_stale", validation["reasons"],
                         "a consistent forgery must still be rejected")

    # ------------------------------------------------------------------
    # R2 handoff identity tampering (handoff hash recomputation)
    # ------------------------------------------------------------------

    def test_r2_handoff_joint_forgery_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-047")
        typed, result = _run(case)
        handoff = build_d09_r2_handoff(typed, result)
        self.assertIsNotNone(handoff)
        assert handoff is not None
        # jointly-consistent forgery: the expected handoff hash is
        # recomputed from typed facts, so a stale id is always rejected
        forged = replace(handoff, handoff_id="f" * 64,
                         idempotency_key="f" * 64)
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("handoff_id_stale", validation["reasons"])
        # inconsistent pair: idempotency must equal the handoff id
        forged = replace(handoff, handoff_id="f" * 64,
                         idempotency_key="e" * 64)
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("idempotency_key_mismatch", validation["reasons"])

    def test_r2_handoff_prior_public_forgery_rejected(self) -> None:
        case = _clone(self.catalog, "D09-CASE-047")
        typed, result = _run(case)
        handoff = build_d09_r2_handoff(typed, result)
        assert handoff is not None
        forged = replace(handoff,
                         prior_public_risk_identity_ref="SYN-FORGED-PRIOR")
        validation = validate_d09_r2_handoff(forged, typed, result)
        self.assertFalse(validation["valid"])
        self.assertIn("create_with_prior_public_ref", validation["reasons"])
        self.assertIn("prior_public_ref_mismatch", validation["reasons"])

    def test_r2_handoff_continue_regression_preserved(self) -> None:
        """The accepted carry-forward/continue gate stays valid: a positive
        run with typed prior refs and continued lineage builds a `continue`
        handoff that passes closed validation."""
        case = _clone(self.catalog, "D09-CASE-047")
        typed, result = _run(case)
        lineage = replace(
            typed.lineage_context,
            prior_risk_instance_ref="SYN-PRIOR-1",
            prior_public_risk_identity_ref="SYN-PRIOR-ID-1",
            lineage_relation="continued_from_data_revision")
        continued = replace(typed, lineage_context=lineage)
        continued_result = evaluate(continued)
        handoff = build_d09_r2_handoff(continued, continued_result)
        self.assertIsNotNone(handoff)
        assert handoff is not None
        self.assertEqual(handoff.action, "continue")
        validation = validate_d09_r2_handoff(
            handoff, continued, continued_result)
        self.assertTrue(validation["valid"], validation["reasons"])

    # ------------------------------------------------------------------
    # Surface-only metadata is inert
    # ------------------------------------------------------------------

    def test_mutation_description_invariance_all_cases(self) -> None:
        """Arbitrary edits/removal/translation of the free-text mutation
        description never change any leaf."""
        substitutions = (
            "",
            "completely unrelated English prose describing an AE review step",
            "完全无关的中文描述，与中心模式评价没有任何关联",
        )
        for case in self.catalog["cases"]:
            typed, result = run_case(case)
            base = assemble_leaf_sets(typed, result, case_index(case))
            context = typed.mutation_context
            for prose in substitutions:
                varied = replace(context, desc=prose)
                re_run = evaluate(replace(typed, mutation_context=varied))
                leaves = assemble_leaf_sets(replace(typed, mutation_context=varied),
                                            re_run, case_index(case))
                self.assertEqual(leaves, base, case["case_id"])

    def test_anti_overfit_variant_metadata_inert(self) -> None:
        """The opaque anti-overfit variant record is never read: replacing
        every field keeps the exact leaves."""
        for case in self.catalog["cases"]:
            typed, result = run_case(case)
            variant = typed.anti_overfit_variant
            if variant is None:
                continue
            base = assemble_leaf_sets(typed, result, case_index(case))
            blank = AntiOverfitVariant(
                variant_id="other-variant", base_fixture_id="other-base",
                semantic_equivalence_ref="other-ref", surface_changes=())
            varied = replace(typed, anti_overfit_variant=blank)
            re_run = evaluate(varied)
            leaves = assemble_leaf_sets(varied, re_run, case_index(case))
            self.assertEqual(leaves, base, case["case_id"])

    def test_envelope_id_rename_inert(self) -> None:
        case = _clone(self.catalog, "D09-CASE-047")
        original = _leaves(case)
        case["typed_input"]["envelope_id"] = "SYN-D09-ENV-RENAMED"
        self.assertEqual(_leaves(case), original,
                         "envelope id is surface-only and must stay inert")

    # ------------------------------------------------------------------
    # Mutation class materialization
    # ------------------------------------------------------------------

    def test_all_mutation_classes_materialized(self) -> None:
        classes = {c["typed_input"]["mutation_context"]["mutation_class"]
                   for c in self.catalog["cases"]}
        required = {
            "none", "coverage_missing", "coverage_partial", "coverage_truncated",
            "coverage_failed", "n1_minimum", "authority_fail", "revision_repeat",
            "export_repeat", "order_shuffle", "display_rename",
            "same_origin_verified", "origin_ambiguous", "origin_wrong_scope",
            "origin_distinct", "evidence_ref_shared", "l1_hole_zero_risk",
            "cutoff_all_out", "cutoff_spans", "cutoff_mixed", "cutoff_conflict",
            "time_missing", "single_window", "signal_unexpandable",
            "validity_insufficient", "statistics_only", "query_non_redundant",
            "query_fully_covered", "query_members_unlistable",
            "query_fanout_exceeded", "query_no_process_delta", "carry_forward",
            "rule_supersession", "site_merge_split", "visibility_hidden",
            "anti_overfit_rename", "anti_overfit_shuffle", "consume_only",
            "routing_gate", "gap_only", "raw_only_provenance",
            "cartesian_rejected", "stratum_change", "window_shift",
            "window_definition_change", "lifecycle_coverage_broken",
            "lifecycle_high_priority", "lifecycle_member_closed",
            "opportunity_conflict", "blinded_stratum_rejected",
            "authorized_unblinded", "stratum_fanout_rejected",
            "stratum_required_empty", "revision_vs_event_time", "r5_side_by_side",
        }
        self.assertTrue(required <= classes, classes - required)


if __name__ == "__main__":
    unittest.main()
