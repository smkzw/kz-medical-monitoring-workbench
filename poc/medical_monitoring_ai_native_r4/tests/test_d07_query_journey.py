"""R4-D07 focused Query / Journey suite (worker-03 slice).

Verifies the frozen contract v0.4 sections 10/11 on the accepted typed
inputs without touching the frozen artifacts:

* the raw root's ``journey.*`` summary leaves exactly match the frozen
  oracle vocabulary for the seven shared-spine cases (129-134/136) and are
  absent everywhere else (including every integrity-failure run);
* the full ``D07SubjectJourneyProjection`` object is content-addressed,
  time-ordered, carries lexicon domain/risk-type labels, reversible source
  jumps with one reverse binding each, a recomputed twelve-field shared
  spine scope/hash equality decision, and passing per-payload audience /
  per-jump validation;
* the audience validator rejects forbidden internal tokens and non-lexicon
  labels (exact-key schema, domain/risk specificity, visible path, scope);
* the three-part Chinese Query draft has exactly basis/finding/action
  sentences, no system judgment, no PD wording without the accepted D04
  permission decision, and passes the closed query-payload validation;
* journey/query output is deterministic and invariant under the declared
  inert positive mutations, and pre-evaluator integrity failures emit no
  Query/Journey leaves.

All data is synthetic and offline.
"""

from __future__ import annotations

import sys
from pathlib import Path

_POC_ROOT = Path(__file__).resolve().parents[2]
_R4_SRC = Path(__file__).resolve().parents[1] / "src"
_R1_SRC = _POC_ROOT / "medical_monitoring_ai_native_r1" / "src"
_R2_SRC = _POC_ROOT / "medical_monitoring_ai_native_r2" / "src"
_R3_SRC = _POC_ROOT / "medical_monitoring_ai_native_r3" / "src"
for _src in (_R1_SRC, _R2_SRC, _R3_SRC, _R4_SRC):
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

import pytest  # noqa: E402

from mm_r4.d07_fixtures import (  # noqa: E402
    build_indexes,
    content_hash,
    flatten_root,
)
from mm_r4.d07_journey import (  # noqa: E402
    EVENT_MARKER_KEYS,
    PROJECTION_KEYS,
    QUERY_DRAFT_KEYS,
    RISK_MARKER_KEYS,
    SOURCE_JUMP_KEYS,
    SPINE_EQUALITY_FIELDS,
    build_d07_subject_journey,
    validate_audience_payload,
)
from mm_r4.d07_query import (  # noqa: E402
    build_d07_query_draft,
    build_pd_wording_permission_decision,
    validate_query_draft,
)
from mm_r4.d07_safety_evaluator import (  # noqa: E402
    D07SafetyEvaluator,
    evaluate_safety,
)

IDX = build_indexes()
CASES = IDX["overlay_cases_by_id"]
EXPECTATIONS = IDX["expectations_by_id"]

# The seven frozen shared-spine journey cases (contract v0.4 section 14 table
# rows 129-136 minus the Query-only row 135).
JOURNEY_CASES = ("129", "130", "131", "132", "133", "134", "136")
INTEGRITY_CASES = frozenset(
    {"028", "119", "120", "121", "122", "123", "124", "125", "126", "127", "128"}
)
# All eight journey summary leaves present in the frozen oracle.
SHARED_JOURNEY_LEAVES = (
    "journey.audience_validation_passed",
    "journey.event_marker_count",
    "journey.internal_token_rejected",
    "journey.pending_marker_count",
    "journey.projection_present",
    "journey.risk_marker_count",
    "journey.source_jump_count",
    "journey.trend_breakpoint_count",
)


def _run(case_id: str):
    return evaluate_safety(CASES[case_id]["typed_input"])


def _journey_leaves(flat):
    return {k: v for k, v in flat.items() if k.startswith("journey.")}


class TestJourneySummaryMatchesOracle:
    """The raw-root ``journey.*`` leaves are exactly the frozen oracle
    vocabulary on the seven shared-spine cases (values included)."""

    @pytest.mark.parametrize("case_id", JOURNEY_CASES)
    def test_shared_journey_leaves_match_oracle(self, case_id):
        root = _run(case_id)
        flat = flatten_root(root)
        assert root["journey"] is not None
        expected = EXPECTATIONS[case_id]["expected_leaf_set"]
        actual = _journey_leaves(flat)
        for path in SHARED_JOURNEY_LEAVES:
            assert actual.get(path) == expected.get(path), (
                f"case {case_id} {path}: expected {expected.get(path)!r} "
                f"got {actual.get(path)!r}"
            )

    def test_case_134_emits_anchored_result_count(self):
        # Case 134 is the frozen "risk marker anchored to result" row: the
        # runtime's anchored count (2, both risk markers result-anchored)
        # matches the oracle leaf exactly.
        root = _run("134")
        flat = flatten_root(root)
        expected = EXPECTATIONS["134"]["expected_leaf_set"]
        assert flat["journey.risk_marker_anchored_result_count"] == (
            expected["journey.risk_marker_anchored_result_count"]
        )
        assert expected["journey.risk_marker_anchored_result_count"] == 2

    @pytest.mark.parametrize("case_id", JOURNEY_CASES)
    def test_anchored_count_is_semantic_risk_marker_count(self, case_id):
        # Documented semantics: every risk marker in the frozen band anchors to
        # a concrete result, so the anchored count equals the risk marker count
        # and the leaf is emitted whenever it is non-zero.
        root = _run(case_id)
        flat = flatten_root(root)
        risk_count = flat.get("journey.risk_marker_count", 0)
        anchored = flat.get("journey.risk_marker_anchored_result_count")
        if risk_count > 0:
            assert anchored == risk_count, case_id
        else:
            assert anchored is None, case_id

    @pytest.mark.parametrize("case_id", JOURNEY_CASES)
    def test_no_extra_journey_leaves_beyond_contract_vocabulary(self, case_id):
        root = _run(case_id)
        flat = flatten_root(root)
        allowed = set(SHARED_JOURNEY_LEAVES) | {
            "journey.risk_marker_anchored_result_count"
        }
        assert set(_journey_leaves(flat)) <= allowed, case_id

    def test_no_journey_without_shared_spine(self):
        # Case 135 carries the lexicon and a Query but no shared spine -> no
        # journey section at all.
        root = _run("135")
        assert "journey" not in root
        flat = flatten_root(root)
        assert not _journey_leaves(flat)

    @pytest.mark.parametrize("case_id", ("001", "050", "100"))
    def test_no_journey_outside_spine_band(self, case_id):
        root = _run(case_id)
        assert "journey" not in root, case_id

    @pytest.mark.parametrize("case_id", sorted(INTEGRITY_CASES))
    def test_integrity_failure_emits_no_journey(self, case_id):
        root = _run(case_id)
        assert root.get("integrity_error") is not None
        assert "journey" not in root
        assert "query" not in root
        flat = flatten_root(root)
        assert not _journey_leaves(flat)


class TestProjectionObject:
    """The full renderer-neutral projection object (module API)."""

    def test_projection_exact_keys_and_content_addressing(self, case_id="129"):
        ti = CASES[case_id]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        projection = build_d07_subject_journey(
            ti, evaluator.state.units, root["source"]["source_jump_target_pairs"]
        )
        assert projection is not None
        assert set(projection) == PROJECTION_KEYS
        assert projection["projection_id"] == projection["projection_hash"]
        assert projection["projection_hash"].startswith("sha256:")
        assert projection["shared_spine_binding_id"] == (
            ti["shared_spine_binding"]["binding_id"]
        )
        assert projection["subject_ref"] == ti["shared_spine_binding"]["subject_ref"]

    @pytest.mark.parametrize(
        "case_id,expected_events,expected_risks,expected_pending",
        [
            ("129", 3, 2, 0),
            ("131", 4, 3, 0),
            ("132", 3, 1, 0),
            ("134", 3, 2, 0),
            ("136", 2, 1, 1),
        ],
    )
    def test_marker_counts(
        self, case_id, expected_events, expected_risks, expected_pending
    ):
        ti = CASES[case_id]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        projection = build_d07_subject_journey(
            ti, evaluator.state.units, root["source"]["source_jump_target_pairs"]
        )
        assert len(projection["ordered_event_markers"]) == expected_events
        assert len(projection["ordered_risk_markers"]) == expected_risks
        pending = sum(1 for m in projection["ordered_event_markers"] if m["pending"])
        assert pending == expected_pending

    def test_event_markers_exact_schema_time_ordered(self):
        ti = CASES["129"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        projection = build_d07_subject_journey(
            ti, evaluator.state.units, root["source"]["source_jump_target_pairs"]
        )
        markers = projection["ordered_event_markers"]
        for marker in markers:
            assert set(marker) == EVENT_MARKER_KEYS
            assert marker["marker_id"].startswith("sha256:")
            assert marker["payload_hash"].startswith("sha256:")
            assert marker["audience_label"]  # measure audience name
        # Time ordering: baseline (no visit) results precede the V3 result.
        assert markers[0]["result_id"] == "SYN-RES-129-1"
        assert markers[1]["result_id"] == "SYN-RES-129-2"
        assert markers[2]["result_id"] == "SYN-RES-129-3"

    def test_risk_markers_anchored_and_labeled(self):
        ti = CASES["129"]["typed_input"]
        lexicon = ti["audience_lexicon"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        projection = build_d07_subject_journey(
            ti, evaluator.state.units, root["source"]["source_jump_target_pairs"]
        )
        for marker in projection["ordered_risk_markers"]:
            assert set(marker) == RISK_MARKER_KEYS
            assert marker["anchor_kind"] == "result"
            assert marker["anchor_ref"] == "SYN-RES-129-3"
            assert marker["clinical_domain_label"] in lexicon["allowed_domain_labels"]
            assert marker["risk_type_label"] in lexicon["allowed_risk_type_labels"]
            assert marker["risk_id"].startswith("sha256:")
            assert marker["unit_id"].startswith("sha256:")
            assert marker["monitoring_priority"] in (
                "low", "medium", "high", "unknown"
            )

    def test_source_jumps_reversible_and_validated(self):
        ti = CASES["129"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        projection = build_d07_subject_journey(
            ti, evaluator.state.units, root["source"]["source_jump_target_pairs"]
        )
        jumps = projection["source_jumps"]
        assert len(jumps) == 3
        jump_ids = {j["jump_id"] for j in jumps}
        for jump in jumps:
            assert set(jump) == SOURCE_JUMP_KEYS
            assert jump["cardinality"] == "one"
            assert isinstance(jump["target_ref"], str)
            assert jump["ordered_target_refs"] is None
            assert jump["join_reason"] in (
                "direct_source", "rule_authority", "producer_binding",
                "shared_identity", "temporal_context",
            )
            # Exactly one reverse binding, resolving inside the projection.
            assert jump["reverse_binding_ref"] in jump_ids
            if jump["join_reason"] == "temporal_context":
                assert jump["temporal_relation_ref"] is not None
            else:
                assert jump["temporal_relation_ref"] is None
        # Jump kinds cover the raw row, the rule authority and the protocol
        # clause (contract: 一跳回原始记录/规则/方案).
        kinds = {j["target_kind"] for j in jumps}
        assert {"listing_row", "lab_manual_rule", "protocol_clause"} <= kinds

    def test_spine_scope_equality_recomputed_true(self):
        ti = CASES["129"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        projection = build_d07_subject_journey(
            ti, evaluator.state.units, root["source"]["source_jump_target_pairs"]
        )
        equality = projection["shared_spine_equality"]
        for field in SPINE_EQUALITY_FIELDS:
            assert equality[field] is True, field
        assert equality["all_equal"] is True
        assert equality["scope_equal_verified"] is True

    def test_all_payload_and_jump_validations_pass(self):
        ti = CASES["129"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        projection = build_d07_subject_journey(
            ti, evaluator.state.units, root["source"]["source_jump_target_pairs"]
        )
        for result in projection["audience_validation_results"]:
            assert result["validation_passed"] is True, result["reason_codes"]
        for result in projection["source_jump_validation_results"]:
            assert result["validation_passed"] is True, result["reason_codes"]

    def test_pending_visit_zone_marker(self):
        ti = CASES["136"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        projection = build_d07_subject_journey(
            ti, evaluator.state.units, root["source"]["source_jump_target_pairs"]
        )
        pending = [m for m in projection["ordered_event_markers"] if m["pending"]]
        assert len(pending) == 1
        assert pending[0]["visit_or_pending_ref"] == "SYN-D05-VISIT-PEND"
        assert pending[0]["result_id"] == "SYN-RES-136-2"

    def test_trend_breakpoint_marker(self):
        # Case 132 switches ALT unit (U/L -> µkat/L) without a conversion rule:
        # the trend line shows exactly one breakpoint.
        ti = CASES["132"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        flat = flatten_root(root)
        assert flat.get("journey.trend_breakpoint_count") == 1


class TestAudienceValidation:
    def test_forbidden_internal_token_rejected(self):
        lexicon = dict(CASES["129"]["typed_input"]["audience_lexicon"])
        marker = {
            "marker_id": "sha256:x",
            "domain": "LB",
            "event_kind": "lab",
            "stable_measure_key": "SYN-LB-ALT",
            "result_id": "SYN-RES-129-3",
            "event_time_ref": "SYN-TIME-129-3",
            "visit_or_pending_ref": "SYN-D05-VISIT-V3",
            "pending": False,
            "audience_label": "丙氨酸氨基转移酶 payload 泄漏",
            "value_label": "128 U/L",
            "range_label": "高于参考范围",
            "grade_label": "分级 G2",
            "cs_ncs_label": None,
            "seriousness_clue_label": None,
            "source_jump_ids": [],
            "payload_hash": "sha256:y",
        }
        result = validate_audience_payload(
            lexicon, "event_marker", marker, "SYN-D07-SCOPE-129",
            "SYN-D07-SUBJECT-001", [],
        )
        assert result["validation_passed"] is False
        assert result["no_internal_tokens"] is False
        assert any("forbidden_internal_token" in r for r in result["reason_codes"])

    def test_non_lexicon_risk_label_rejected(self):
        lexicon = dict(CASES["129"]["typed_input"]["audience_lexicon"])
        marker = {
            "marker_id": "sha256:x",
            "risk_id": "sha256:r",
            "unit_id": "sha256:u",
            "positive_subtype": "new_abnormality",
            "monitoring_priority": "medium",
            "seriousness_clue_state": "absent",
            "grade_comparison_assessment_id": None,
            "clinical_significance_assessment_id": None,
            "priority_decision_id": None,
            "anchor_kind": "result",
            "anchor_ref": "SYN-RES-129-3",
            "clinical_domain_label": "实验室",
            "risk_type_label": "SYN-WRONG-RISK-LABEL",
            "summary_label": "ALT 新发异常",
            "source_jump_ids": [],
            "query_draft_ref": None,
            "payload_hash": "sha256:y",
        }
        result = validate_audience_payload(
            lexicon, "risk_marker", marker, "SYN-D07-SCOPE-129",
            "SYN-D07-SUBJECT-001", [],
        )
        assert result["validation_passed"] is False
        assert result["risk_specific"] is False


class TestQueryDraft:
    def test_three_sentence_natural_chinese(self, case_id="129"):
        ti = CASES[case_id]["typed_input"]
        evaluator = D07SafetyEvaluator()
        evaluator.evaluate(ti)
        draft = build_d07_query_draft(ti, evaluator.state.units)
        assert draft is not None
        assert set(draft) == QUERY_DRAFT_KEYS
        assert draft["query_owner"] == "D07"
        assert draft["basis_sentence"].endswith("；")
        assert draft["finding_sentence"].endswith("；")
        assert draft["action_sentence"].endswith("。")
        assert len(draft["basis_sentence"]) > 5
        assert len(draft["finding_sentence"]) > 5
        assert len(draft["action_sentence"]) > 5
        # No system judgment wording and no internal tokens in the sentences.
        joined = (draft["basis_sentence"] + draft["finding_sentence"]
                  + draft["action_sentence"])
        for token in ("DILI", "SAE", "与研究药物相关", "系统判定", "候选信号",
                      "payload", "hash", "oracle", "fixture"):
            assert token not in joined
        assert draft["content_hash"].startswith("sha256:")
        assert draft["query_draft_id"].startswith("sha256:")

    def test_finding_matches_contract_example_shape(self):
        ti = CASES["129"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        evaluator.evaluate(ti)
        draft = build_d07_query_draft(ti, evaluator.state.units)
        # 受试者 <subject> 于研究第 29 天 <measure> 升高至 3.2×ULN ...
        assert "受试者 SYN-D07-SUBJECT-001" in draft["finding_sentence"]
        assert "研究第 29 天" in draft["finding_sentence"]
        assert "丙氨酸氨基转移酶" in draft["finding_sentence"]
        assert "3.2×ULN" in draft["finding_sentence"]

    def test_pd_wording_permitted_only_with_accepted_d04(self):
        ti = CASES["135"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        evaluator.evaluate(ti)
        draft = build_d07_query_draft(ti, evaluator.state.units)
        assert draft is not None
        permission = draft["pd_wording_permission"]
        assert permission["pd_wording_permitted"] is True
        assert permission["context_scope_equal"] is True
        assert permission["context_accepted"] is True
        assert permission["content_hash_equal"] is True
        assert permission["d04_context_ref"] == "SYN-D04-CTX-135"
        assert "是否涉及 PD" in draft["action_sentence"]

    def test_no_pd_wording_without_permission(self):
        ti = CASES["129"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        evaluator.evaluate(ti)
        draft = build_d07_query_draft(ti, evaluator.state.units)
        assert draft["pd_wording_permission"]["pd_wording_permitted"] is False
        assert "PD" not in draft["action_sentence"]

    def test_pd_denied_when_context_not_accepted(self):
        import copy

        ti = copy.deepcopy(CASES["135"]["typed_input"])
        ti["d04_context_refs"][0]["context_accepted"] = False
        decision = build_pd_wording_permission_decision(ti)
        assert decision["pd_wording_permitted"] is False
        assert decision["context_accepted"] is False

    def test_pd_denied_when_hash_malformed(self):
        import copy

        ti = copy.deepcopy(CASES["135"]["typed_input"])
        ti["d04_context_refs"][0]["accepted_content_hash"] = "not-a-hash"
        decision = build_pd_wording_permission_decision(ti)
        assert decision["pd_wording_permitted"] is False
        assert decision["content_hash_equal"] is False

    def test_query_payload_validation_passes(self):
        ti = CASES["135"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        draft = build_d07_query_draft(ti, evaluator.state.units)
        lexicon = ti["audience_lexicon"]
        result = validate_query_draft(
            draft, lexicon,
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti,
            valid_jumps=root["source"]["source_jump_target_pairs"],
        )
        assert result["validation_passed"] is True, result["reason_codes"]

    def test_query_payload_validation_rejects_missing_sentence(self):
        import copy

        ti = CASES["129"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        evaluator.evaluate(ti)
        draft = build_d07_query_draft(ti, evaluator.state.units)
        broken = copy.deepcopy(draft)
        broken["action_sentence"] = ""
        result = validate_query_draft(
            broken, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
        )
        assert result["validation_passed"] is False
        assert "three_sentence_contract" in result["reason_codes"]

    def test_no_query_draft_without_risk_unit(self):
        # Case 007 is the frozen L0-gap row (no accepted results, no risk
        # units): the run is admitted but produces no Query draft.
        ti = CASES["007"]["typed_input"]
        evaluator = D07SafetyEvaluator()
        evaluator.evaluate(ti)
        draft = build_d07_query_draft(ti, evaluator.state.units)
        assert draft is None


class TestDeterminismAndInertMutations:
    @pytest.mark.parametrize("case_id", JOURNEY_CASES)
    def test_journey_summary_deterministic(self, case_id):
        ti = CASES[case_id]["typed_input"]
        first = evaluate_safety(ti)
        second = evaluate_safety(ti)
        assert content_hash(first.get("journey")) == content_hash(
            second.get("journey")
        )

    @pytest.mark.parametrize(
        "case_id,mutation_id",
        [
            ("129", "P-ARRAY-REORDER"),
            ("129", "P-ADD-UNRELATED-RECORD"),
            ("134", "P-COUNTEREVIDENCE-ADDED"),
            ("136", "P-ARRAY-REORDER"),
        ],
    )
    def test_journey_invariant_under_inert_positive_mutations(
        self, case_id, mutation_id
    ):
        from mm_r4.d07_fixtures import apply_mutation

        ti = CASES[case_id]["typed_input"]
        baseline = evaluate_safety(ti).get("journey")
        mutated = evaluate_safety(apply_mutation(ti, mutation_id)).get("journey")
        assert content_hash(mutated) == content_hash(baseline), (
            case_id, mutation_id
        )

    @pytest.mark.parametrize(
        "case_id,mutation_id",
        [
            ("129", "N-JOURNEY-MARKER-DRIFT"),
            ("129", "N-PAYLOAD-DRIFT"),
            ("129", "N-REVERSE-BINDING-MISSING"),
            ("134", "N-JUMP-DRIFT"),
        ],
    )
    def test_journey_mutations_fail_closed(self, case_id, mutation_id):
        from mm_r4.d07_fixtures import apply_mutation

        ti = CASES[case_id]["typed_input"]
        root = evaluate_safety(apply_mutation(ti, mutation_id))
        assert root.get("integrity_error") is not None
        assert "journey" not in root
        assert "query" not in root


class TestExactTargetValidation:
    """Fail-closed source-jump target validation (verifier counterexamples)."""

    @staticmethod
    def _projection(case_id="129"):
        ti = CASES[case_id]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        return ti, root, build_d07_subject_journey(
            ti, evaluator.state.units, root["source"]["source_jump_target_pairs"]
        )

    def test_unknown_target_id_fails_closed(self):
        import copy

        ti, root, _ = self._projection()
        pairs = copy.deepcopy(root["source"]["source_jump_target_pairs"])
        pairs[1]["target_object_id"] = "SYN-UNKNOWN-TARGET"
        projection = build_d07_subject_journey(
            ti, [], pairs
        )
        results = projection["source_jump_validation_results"]
        assert results[1]["validation_passed"] is False
        assert "target_schema_unresolved" in results[1]["reason_codes"]

    def test_invalid_target_kind_fails_closed_without_rewriting(self):
        import copy

        ti, root, _ = self._projection()
        pairs = copy.deepcopy(root["source"]["source_jump_target_pairs"])
        pairs[1]["target_kind"] = "invalid_kind"
        projection = build_d07_subject_journey(ti, [], pairs)
        results = projection["source_jump_validation_results"]
        assert results[1]["validation_passed"] is False
        assert projection["source_jumps"][1]["target_kind"] == "invalid_kind"
        assert "target_schema_unresolved" in results[1]["reason_codes"]

    def test_mutated_target_content_fails_closed(self):
        import copy

        ti, root, _ = self._projection()
        mutated = copy.deepcopy(ti)
        for r in mutated["observed_results"]:
            if r["result_id"] == "SYN-RES-129-3":
                r["raw_value"] = "999 U/L"
        projection = build_d07_subject_journey(
            mutated, [], root["source"]["source_jump_target_pairs"]
        )
        results = projection["source_jump_validation_results"]
        listing = next(
            (v for j, v in zip(projection["source_jumps"], results)
             if j["target_kind"] == "listing_row"),
            None,
        )
        assert listing is not None
        assert listing["validation_passed"] is False
        assert "target_hash_mismatch" in listing["reason_codes"]

    def test_missing_target_locator_fails_closed(self):
        import copy

        ti, root, _ = self._projection()
        mutated = copy.deepcopy(ti)
        for obj in mutated["grade_rule_sets"]:
            obj["source_locator_ids"] = []
        projection = build_d07_subject_journey(
            mutated, [], root["source"]["source_jump_target_pairs"]
        )
        results = projection["source_jump_validation_results"]
        lab = next(
            (v for j, v in zip(projection["source_jumps"], results)
             if j["target_kind"] == "lab_manual_rule"),
            None,
        )
        assert lab is not None
        assert lab["validation_passed"] is False
        assert "target_locator_unresolved" in lab["reason_codes"]

    def test_scope_mismatch_fails_closed(self):
        ti, root, _ = self._projection()
        projection = build_d07_subject_journey(
            ti, [], root["source"]["source_jump_target_pairs"]
        )
        # Rebuild with a foreign scope binding: the listing target's envelope
        # no longer matches the jump scope.
        foreign = dict(ti["shared_spine_binding"])
        foreign["scope_binding_id"] = "SYN-FOREIGN-SCOPE"
        mutated = dict(ti)
        mutated["shared_spine_binding"] = foreign
        projection = build_d07_subject_journey(
            mutated, [], root["source"]["source_jump_target_pairs"]
        )
        results = projection["source_jump_validation_results"]
        listing = next(
            (v for j, v in zip(projection["source_jumps"], results)
             if j["target_kind"] == "listing_row"),
            None,
        )
        assert listing is not None
        assert listing["validation_passed"] is False
        assert "target_scope_mismatch" in listing["reason_codes"]

    def test_valid_targets_pass(self):
        _, _, projection = self._projection()
        for result in projection["source_jump_validation_results"]:
            assert result["validation_passed"] is True, result["reason_codes"]

    def test_failed_jump_blocks_audience_and_projection(self):
        import copy

        ti, root, _ = self._projection()
        for label, mutate in [
            ("unknown_id", lambda p: p.__setitem__(
                1, {**p[1], "target_object_id": "SYN-UNKNOWN-TARGET"})),
            ("wrong_kind", lambda p: p.__setitem__(
                1, {**p[1], "target_kind": "invalid_kind"})),
        ]:
            pairs = copy.deepcopy(root["source"]["source_jump_target_pairs"])
            mutate(pairs)
            projection = build_d07_subject_journey(ti, [], pairs)
            jump_ok = all(
                v["validation_passed"]
                for v in projection["source_jump_validation_results"]
            )
            audience_ok = all(
                v["validation_passed"]
                for v in projection["audience_validation_results"]
            )
            assert jump_ok is False, label
            assert audience_ok is False, label


class TestQueryExactAudienceValidation:
    """Query evidence/locator/scope/hash validation (verifier counterexamples)."""

    @staticmethod
    def _draft(case_id="129"):
        ti = CASES[case_id]["typed_input"]
        evaluator = D07SafetyEvaluator()
        root = evaluator.evaluate(ti)
        return ti, root, build_d07_query_draft(ti, evaluator.state.units)

    def test_empty_evidence_and_locators_fail(self):
        import copy

        ti, _root, draft = self._draft()
        broken = copy.deepcopy(draft)
        broken["evidence_refs"] = []
        broken["source_locator_ids"] = []
        result = validate_query_draft(
            broken, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti,
        )
        assert result["validation_passed"] is False
        assert "evidence_refs_empty" in result["reason_codes"]
        assert "source_locators_empty" in result["reason_codes"]

    def test_unknown_evidence_ref_fails(self):
        import copy

        ti, _root, draft = self._draft()
        broken = copy.deepcopy(draft)
        broken["evidence_refs"] = ["SYN-RES-UNKNOWN"]
        result = validate_query_draft(
            broken, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti,
        )
        assert result["validation_passed"] is False
        assert "evidence_ref_unresolved" in result["reason_codes"]

    def test_wrong_scope_and_subject_fail(self):
        ti, _root, draft = self._draft()
        result = validate_query_draft(
            draft, ti["audience_lexicon"],
            "SYN-FOREIGN-SCOPE", "SYN-FOREIGN-SUBJECT",
            typed_input=ti,
        )
        assert result["validation_passed"] is False
        assert "evidence_scope_mismatch" in result["reason_codes"]

    def test_stale_content_hash_fails(self):
        import copy

        ti, _root, draft = self._draft()
        broken = copy.deepcopy(draft)
        broken["content_hash"] = "sha256:" + "0" * 64
        result = validate_query_draft(
            broken, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti,
        )
        assert result["validation_passed"] is False
        assert "content_hash_stale" in result["reason_codes"]

    def test_valid_query_passes_with_evidence(self):
        ti, root, draft = self._draft()
        result = validate_query_draft(
            draft, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti,
            valid_jumps=root["source"]["source_jump_target_pairs"],
        )
        assert result["validation_passed"] is True, result["reason_codes"]
        assert result["source_jump_valid"] is True
        assert result["visible_path_valid"] is True
        assert result["scope_equal"] is True

    def test_absent_typed_input_fails_closed(self):
        ti, _root, draft = self._draft()
        result = validate_query_draft(
            draft, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
        )
        assert result["validation_passed"] is False
        assert "typed_input_missing" in result["reason_codes"]
        assert "valid_jumps_missing" in result["reason_codes"]

    def test_absent_valid_jumps_fails_closed(self):
        ti, _root, draft = self._draft()
        result = validate_query_draft(
            draft, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti,
        )
        assert result["validation_passed"] is False
        assert "valid_jumps_missing" in result["reason_codes"]

    def test_malformed_jump_target_fails_closed(self):
        import copy

        ti, root, draft = self._draft()
        pairs = copy.deepcopy(root["source"]["source_jump_target_pairs"])
        pairs[0]["target_object_id"] = "SYN-UNKNOWN-TARGET"
        result = validate_query_draft(
            draft, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti, valid_jumps=pairs,
        )
        assert result["validation_passed"] is False
        assert result["source_jump_valid"] is False
        assert "jump_target_schema_unresolved" in result["reason_codes"]

    def test_wrong_kind_jump_fails_closed(self):
        import copy

        ti, root, draft = self._draft()
        pairs = copy.deepcopy(root["source"]["source_jump_target_pairs"])
        pairs[0]["target_kind"] = "invalid_kind"
        result = validate_query_draft(
            draft, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti, valid_jumps=pairs,
        )
        assert result["validation_passed"] is False
        assert result["source_jump_valid"] is False
        assert "jump_target_schema_unresolved" in result["reason_codes"]

    def test_tampered_jump_target_hash_fails_closed(self):
        import copy

        ti, root, draft = self._draft()
        pairs = copy.deepcopy(root["source"]["source_jump_target_pairs"])
        mutated = copy.deepcopy(ti)
        for r in mutated["observed_results"]:
            if r["result_id"] == "SYN-RES-129-3":
                r["raw_value"] = "999 U/L"
        result = validate_query_draft(
            draft, mutated["audience_lexicon"],
            mutated["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=mutated, valid_jumps=pairs,
        )
        assert result["validation_passed"] is False
        assert result["source_jump_valid"] is False
        assert any("jump_target_hash_mismatch" in r for r in result["reason_codes"])

    def test_jump_scope_mismatch_fails_closed(self):
        import copy

        ti, root, draft = self._draft()
        pairs = copy.deepcopy(root["source"]["source_jump_target_pairs"])
        foreign = dict(ti["shared_spine_binding"])
        foreign["scope_binding_id"] = "SYN-FOREIGN-SCOPE"
        mutated = dict(ti)
        mutated["shared_spine_binding"] = foreign
        result = validate_query_draft(
            draft, mutated["audience_lexicon"],
            "SYN-FOREIGN-SCOPE", "SYN-D07-SUBJECT-001",
            typed_input=mutated, valid_jumps=pairs,
        )
        assert result["validation_passed"] is False
        assert result["source_jump_valid"] is False

    def test_materialized_target_ref_jumps_pass(self):
        ti, root, draft = self._draft()
        projection = build_d07_subject_journey(
            ti, [], root["source"]["source_jump_target_pairs"]
        )
        result = validate_query_draft(
            draft, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti, valid_jumps=projection["source_jumps"],
        )
        assert result["validation_passed"] is True, result["reason_codes"]
        assert result["source_jump_valid"] is True

    def test_conflicting_target_ref_and_object_id_fails_closed(self):
        import copy

        ti, root, draft = self._draft()
        projection = build_d07_subject_journey(
            ti, [], root["source"]["source_jump_target_pairs"]
        )
        both = copy.deepcopy(projection["source_jumps"])
        for jump in both:
            jump["target_object_id"] = "SYN-DIFFERENT-TARGET"
        result = validate_query_draft(
            draft, ti["audience_lexicon"],
            ti["run_scope_binding"]["scope_binding_id"], "SYN-D07-SUBJECT-001",
            typed_input=ti, valid_jumps=both,
        )
        assert result["validation_passed"] is False
        assert result["source_jump_valid"] is False
        assert "jump_target_ref_conflict" in result["reason_codes"]
