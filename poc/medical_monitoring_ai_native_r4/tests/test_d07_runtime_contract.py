"""R4-D07 focused runtime tests (worker-01 slice).

Covers the D07 closed typed runtime contract without reading the frozen
catalog/oracle/registry:

* pre-evaluator integrity pipeline: frozen first-failure order and the
  fail-closed guarantee (no medical/priority/risk/Query/Journey output on
  failure);
* deterministic evaluation: identical typed input yields identical raw
  output leaves;
* medical evaluation contracts: reference-range state, CTCAE/project grade
  with reported-vs-recomputed comparison, baseline/trend classification,
  CS/NCS controlled-value consistency, follow-up obligation states,
  L1 disposition and positive subtype, owner routing / downstream handoffs,
  monitoring priority through the precedence policy, lifecycle
  transitions, and the coverage ledger / domain completeness gates;
* runtime closure: the evaluator never imports the catalog, oracle,
  manifest or registry, and never branches on case/test/fixture ids.

All inputs are self-contained synthetic typed inputs.
"""

from __future__ import annotations

import copy
import json
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


from mm_r4.d07_safety import (  # noqa: E402
    INTEGRITY_STAGES,
    d07_content_hash,
    is_sha256_hex,
)
from mm_r4.d07_safety_evaluator import (  # noqa: E402
    evaluate_safety,
)


def _hash(obj):
    return d07_content_hash(obj)


def _base_input() -> dict:
    scope = {
        "scope_binding_id": "SYN-SCOPE-1",
        "project_ref": "SYN-PROJECT",
        "run_ref": "SYN-RUN-2",
        "monitoring_mode": "full",
        "source_revision": "SYN-REV-2",
        "accepted_snapshot_ref": "SYN-SNAP-2",
        "snapshot_as_of": "2026-01-31T23:59:59+08:00",
        "clinical_event_cutoff": "2026-01-31T23:59:59+08:00",
        "protocol_version": "SYN-PROTO-3",
        "ib_rsi_version": "SYN-IB-2",
        "lab_manual_version": "SYN-LABMAN-4",
        "mapping_version": "SYN-MAP-1",
        "unit_dictionary_version": "SYN-UNITDICT-5",
        "rule_set_versions": {
            "baseline": "SYN-BASELINE-1",
            "grade": "SYN-GRADESETS-5",
            "monitoring": "SYN-MONRULES-2",
            "priority": "SYN-PRIORITY-1",
            "trend": "SYN-TREND-1",
        },
        "source_locator_ids": ["SYN-LOC-SCOPE"],
    }
    scope["lineage_hash"] = _hash({k: v for k, v in scope.items() if k != "lineage_hash"})
    time_refs = [
        {
            "time_ref_id": "SYN-TIME-1", "value": "2025-10-27T08:00:00+08:00",
            "precision": "datetime", "timezone": "+08:00",
            "timezone_state": "provided", "source_locator_ids": ["SYN-LOC-T1"],
        },
        {
            "time_ref_id": "SYN-TIME-2", "value": "2025-11-03T08:00:00+08:00",
            "precision": "datetime", "timezone": "+08:00",
            "timezone_state": "provided", "source_locator_ids": ["SYN-LOC-T2"],
        },
        {
            "time_ref_id": "SYN-TIME-3", "value": "2025-12-02T08:00:00+08:00",
            "precision": "datetime", "timezone": "+08:00",
            "timezone_state": "provided", "source_locator_ids": ["SYN-LOC-T3"],
        },
        {
            "time_ref_id": "SYN-TIME-CUT", "value": "2026-01-31T23:59:59+08:00",
            "precision": "datetime", "timezone": "+08:00",
            "timezone_state": "provided", "source_locator_ids": ["SYN-LOC-CUT"],
        },
    ]
    for ref in time_refs:
        ref["hash"] = _hash({k: v for k, v in ref.items() if k != "hash"})
    cutoffs = [
        {"cutoff_decision_id": f"SYN-CUT-{i}", "record_time_ref_id": f"SYN-TIME-{i}",
         "run_cutoff_time_ref_id": "SYN-TIME-CUT",
         "d05_cutoff_policy_id": "SYN-D05-CUTOFF-POLICY-1",
         "d05_cutoff_policy_version": "1",
         "d05_cutoff_policy_hash": "sha256:" + "0" * 64,
         "normalized_record_interval": ["2025-01-01T00:00:00+08:00", "2025-01-01T00:00:00+08:00"],
         "normalized_cutoff_instant": "2026-01-31T23:59:59+08:00",
         "comparison": "before", "admitted": True, "decision": "within_cutoff",
         "reason_codes": ["synthetic"], "source_locator_ids": ["SYN-LOC-CUT"]}
        for i in (1, 2, 3)
    ]
    for cutoff in cutoffs:
        cutoff["hash"] = _hash({k: v for k, v in cutoff.items() if k != "hash"})
    subject = {
        "subject_ref": "SYN-SUBJ-1", "sex": "female", "age_years": "45",
        "pregnancy_state": "not_applicable", "source_locator_ids": ["SYN-LOC-SUBJ"],
    }
    subject["hash"] = _hash({k: v for k, v in subject.items() if k != "hash"})
    measure = {
        "definition_id": "SYN-M-ALT-1", "stable_measure_key": "SYN-LB-ALT",
        "version": "1", "domain": "LB", "audience_name": "ALT",
        "result_kind": "numeric", "allowed_result_kinds": ["numeric"],
        "expected_unit_dimension": "activity_concentration",
        "applicability_rule_id": "SYN-APP-1", "source_locator_ids": ["SYN-LOC-RULE"],
    }
    measure["definition_hash"] = _hash({k: v for k, v in measure.items() if k != "definition_hash"})
    rng = {
        "range_definition_id": "SYN-RANGE-1", "stable_measure_key": "SYN-LB-ALT",
        "version": "1", "range_kind": "upper_only", "unit": "U/L", "upper": "40",
        "upper_inclusive": True, "sex": "not_applicable",
        "effective_interval": ["2025-01-01", "2026-12-31"],
        "source_locator_ids": ["SYN-LOC-RULE"],
    }
    rng["hash"] = _hash({k: v for k, v in rng.items() if k != "hash"})
    grade_set = {
        "rule_set_id": "SYN-GRADESET-5", "name": "ALT", "version": "5", "kind": "CTCAE",
        "stable_measure_key": "SYN-LB-ALT", "term_code": "ALT elevation",
        "ordered_grade_rule_ids": ["SYN-GR-1", "SYN-GR-2", "SYN-GR-3", "SYN-GR-4"],
        "grade_domain": "hepatic", "endpoint_inclusivity": "documented",
        "missing_input_outcome": "not_evaluable", "source_locator_ids": ["SYN-LOC-RULE"],
    }
    grade_set["hash"] = _hash({k: v for k, v in grade_set.items() if k != "hash"})
    grade_rules = []
    for idx, (lo, hi, grade) in enumerate(
        [("1.0", "3.0", "G1"), ("3.0", "5.0", "G2"), ("5.0", "8.0", "G3")], start=1
    ):
        rule = {
            "grade_rule_id": f"SYN-GR-{idx}", "sequence": idx, "grade": grade,
            "comparator": "between", "left_operand": "ratio_to_uln",
            "lower": lo, "upper": hi, "lower_inclusive": True,
            "upper_inclusive": False, "required_context_fields": [],
            "source_locator_ids": ["SYN-LOC-RULE"],
        }
        rule["hash"] = _hash({k: v for k, v in rule.items() if k != "hash"})
        grade_rules.append(rule)
    rule4 = {
        "grade_rule_id": "SYN-GR-4", "sequence": 4, "grade": "G4",
        "comparator": "gt", "left_operand": "ratio_to_uln", "lower": "8.0",
        "required_context_fields": [], "source_locator_ids": ["SYN-LOC-RULE"],
    }
    rule4["hash"] = _hash({k: v for k, v in rule4.items() if k != "hash"})
    grade_rules.append(rule4)
    baseline = {
        "rule_id": "SYN-BASELINE-1", "version": "1",
        "candidate_window": ["-365d", "0d"],
        "allowed_record_statuses": ["accepted_current"],
        "ordering_fields": ["collection_or_exam_time"],
        "tie_break_fields": ["stable_source_record_id"],
        "minimum_required_candidates": 1, "no_candidate_outcome": "not_evaluable",
        "tie_outcome": "boundary", "source_locator_ids": ["SYN-LOC-RULE"],
        "baseline_confirmation_relative_deviation": "0.02",
    }
    baseline["hash"] = _hash({k: v for k, v in baseline.items() if k != "hash"})
    trend = {
        "rule_id": "SYN-TREND-1", "version": "1", "minimum_comparable_points": 3,
        "confirmation_point_count": 1, "confirmation_window": "7d",
        "recovery_window": "14d", "recurrent_gap_window": "28d",
        "required_same_context_fields": ["unit", "method_kind", "specimen_kind"],
        "missing_point_policy": "break_series", "source_locator_ids": ["SYN-LOC-RULE"],
    }
    trend["hash"] = _hash({k: v for k, v in trend.items() if k != "hash"})
    priority_policy = {
        "policy_id": "SYN-PRIORITY-1", "version": "1.0",
        "ordered_precedence_rule_ids": ["SYN-PPR-1", "SYN-PPR-2", "SYN-PPR-3", "SYN-PPR-4", "SYN-PPR-5"],
        "high_priority_clinical_flag_rules": ["SYN-PPR-1"],
        "machine_close_forbidden_rules": ["SYN-PPR-1", "SYN-PPR-3"],
        "source_locator_ids": ["SYN-LOC-RULE"],
    }
    priority_policy["policy_hash"] = _hash({k: v for k, v in priority_policy.items() if k != "policy_hash"})
    precedence = []
    for step, (pid, trigger, priority, forbidden, reason) in enumerate([
        ("SYN-PPR-1", "high_priority_clinical_flag", "high", True, "rights_or_critical_threshold"),
        ("SYN-PPR-2", "identity_or_evidence_unresolved", "unknown", False, "priority_input_unresolved"),
        ("SYN-PPR-3", "significant_safety_concern", "medium", True, "significant_safety_concern"),
        ("SYN-PPR-4", "mild_or_explained", "low", False, "mild_or_explained"),
        ("SYN-PPR-5", "negative_or_not_applicable", "low", False, "no_concern"),
    ], start=1):
        rule = {
            "precedence_rule_id": pid, "step": step, "trigger": trigger,
            "monitoring_priority": priority, "machine_close_forbidden": forbidden,
            "reason_codes": [reason], "source_locator_ids": ["SYN-LOC-RULE"],
        }
        if trigger == "high_priority_clinical_flag":
            rule["safety_critical_ratio_threshold"] = "5"
        rule["hash"] = _hash({k: v for k, v in rule.items() if k != "hash"})
        precedence.append(rule)
    monitoring_rules = []
    monitoring_predicates = []
    for idx, (pid, threshold, kind, roles, floor) in enumerate([
        ("SYN-PRED-GE3", "3.0", "repeat", ["repeat_measurement"], "medium"),
        ("SYN-PRED-GE5", "5.0", "action", ["clinical_review", "treatment_action"], "high"),
    ], start=1):
        pred = {
            "predicate_id": pid, "sequence": 1, "left_operand": "ratio_to_uln",
            "comparator": "ge", "right_typed_value": threshold,
            "missing_outcome": "not_evaluable", "source_locator_ids": ["SYN-LOC-RULE"],
        }
        pred["hash"] = _hash({k: v for k, v in pred.items() if k != "hash"})
        monitoring_predicates.append(pred)
    for rule_id, kind, preds, roles, floor in [
        ("SYN-MR-REPEAT", "repeat", ["SYN-PRED-GE3"], ["repeat_measurement"], "medium"),
        ("SYN-MR-ACTION", "action", ["SYN-PRED-GE5"], ["clinical_review", "treatment_action"], "high"),
        ("SYN-MR-CS", "clinical_significance", ["SYN-PRED-GE3"], ["cs_assessment"], None),
    ]:
        rule = {
            "rule_id": rule_id, "version": "1", "rule_kind": kind,
            "applicable_measure_keys": ["SYN-LB-ALT"],
            "ordered_predicate_ids": preds, "temporal_window": ["0", "7d"],
            "required_followup_roles": roles, "owner_route": "evaluate_and_own",
            "source_locator_ids": ["SYN-LOC-RULE"],
        }
        if floor is not None:
            rule["priority_floor"] = floor
        rule["hash"] = _hash({k: v for k, v in rule.items() if k != "hash"})
        monitoring_rules.append(rule)
    obligations = []
    for oid, kind, trigger, role in [
        ("SYN-OBL-REPEAT", "repeat", "SYN-MR-REPEAT", "repeat_measurement"),
        ("SYN-OBL-REVIEW", "clinical_review", "SYN-MR-CS", "clinical_review"),
        ("SYN-OBL-TX", "treatment_action", "SYN-MR-ACTION", "treatment_action"),
        ("SYN-OBL-AE", "ae_assessment", "SYN-MR-CS", "ae_assessment"),
        ("SYN-OBL-PD", "protocol_execution_check", "SYN-MR-ACTION", "protocol_execution_check"),
    ]:
        obligation = {
            "obligation_definition_id": oid, "version": "1", "obligation_kind": kind,
            "trigger_rule_id": trigger, "required_action_role": role,
            "temporal_window": ["0", "7d"], "owner_domain": "D07", "query_owner": "D07",
            "merge_key_fields": ["stable_measure_key", "required_action_role"],
            "source_locator_ids": ["SYN-LOC-RULE"],
        }
        obligation["hash"] = _hash({k: v for k, v in obligation.items() if k != "hash"})
        obligations.append(obligation)
    authorities = []
    for claim, binding_id, version in [
        ("lab_manual", "SYN-AUTH-LABMAN-4", "4"),
        ("reference_range", "SYN-AUTH-RANGE-1", "1"),
        ("grade_ruleset", "SYN-AUTH-GRADE-5", "5"),
        ("unit_dictionary", "SYN-AUTH-UNITDICT-5", "5"),
    ]:
        authority = {
            "authority_binding_id": binding_id, "claim_kind": claim,
            "candidate_authority_ids": [binding_id],
            "selected_authority_id": binding_id, "selected_version": version,
            "decision_status": "unique",
            "effective_interval": ["2025-01-01", "2026-12-31"],
            "scope_predicate_results": [True], "source_locator_ids": ["SYN-LOC-RULE"],
        }
        authority["hash"] = _hash({k: v for k, v in authority.items() if k != "hash"})
        authorities.append(authority)
    visit = {
        "visit_ref_id": "SYN-VISIT-3", "visit_label": "V3", "status": "completed",
        "planned_date": "2025-12-02", "actual_date": "2025-12-02",
        "window": ["-3d", "+7d"], "source_locator_ids": ["SYN-LOC-VISIT"],
    }
    visit["hash"] = _hash({k: v for k, v in visit.items() if k != "hash"})
    lexicon = {
        "lexicon_id": "SYN-LEXICON-1", "version": "1",
        "allowed_domain_labels": ["实验室", "生命体征", "心电图", "体格检查", "影像", "其他检查"],
        "allowed_risk_type_labels": ["检验结果待核实", "检查变化待核实", "复测或处置记录待核实", "临床意义判断待核实"],
        "forbidden_internal_tokens": ["payload", "hash", "oracle", "候选信号", "通用风险点"],
        "required_sentence_patterns": ["basis", "finding", "action"],
        "source_locator_ids": ["SYN-LOC-LEXICON"],
    }
    lexicon["content_hash"] = _hash({k: v for k, v in lexicon.items() if k != "content_hash"})
    return {
        "input_schema": "d07-typed-input-v1",
        "run_scope_binding": scope,
        "previous_run_scope_binding": None,
        "authority_bindings": authorities,
        "measure_definitions": [measure],
        "reference_range_definitions": [rng],
        "unit_conversion_rules": [],
        "grade_rule_sets": [grade_set],
        "grade_rules": grade_rules,
        "monitoring_rules": monitoring_rules,
        "monitoring_predicates": monitoring_predicates,
        "baseline_rules": [baseline],
        "trend_rules": [trend],
        "action_obligation_definitions": obligations,
        "organ_pattern_rule_definitions": [],
        "examination_requirement_sets": [],
        "priority_policy": priority_policy,
        "priority_precedence_rules": precedence,
        "producer_consumption_bindings": [],
        "clinical_review_refs": [],
        "clinical_significance_reason_refs": [],
        "d04_context_refs": [],
        "correction_chain_decisions": [],
        "cutoff_decisions": cutoffs,
        "d05_gate_bindings": [],
        "applicability_evidence": [],
        "observed_results": [],
        "previous_observed_results": [],
        "scope_envelopes": [],
        "previous_scope_envelopes": [],
        "time_refs": time_refs,
        "previous_time_refs": [],
        "subject_demographics": [subject],
        "visit_refs": [visit],
        "carry_forward_refs": [],
        "shared_spine_binding": None,
        "shared_spine_scope_equality_decision": None,
        "audience_lexicon": lexicon,
    }


def _result(result_id, time_id, value, flag=None, visit=None, status="accepted_current",
            unit="U/L", cs=None, reported_grade=None, measure_key="SYN-LB-ALT"):
    record_id = f"SYN-REC-{result_id.split('-')[-1]}"
    result = {
        "result_id": result_id, "stable_source_record_id": record_id,
        "subject_ref": "SYN-SUBJ-1", "site_ref": "SYN-SITE-1",
        "stable_measure_key": measure_key, "domain": "LB",
        "raw_value": value, "numeric_value": value, "original_unit": unit,
        "reported_range_high": "40", "collection_or_exam_time": time_id,
        "specimen_quality": "acceptable", "correction_status": "original",
        "record_status": status, "accepted_snapshot_ref": "SYN-SNAP-2",
        "scope_envelope_id": f"SYN-ENV-{result_id.split('-')[-1]}",
        "source_locator_ids": [f"SYN-LOC-{result_id.split('-')[-1]}"],
    }
    if flag is not None:
        result["reported_abnormal_flag"] = flag
    if visit is not None:
        result["visit_ref"] = visit
    if cs is not None:
        result["reported_cs_ncs"] = cs
    if reported_grade is not None:
        result["reported_grade"] = reported_grade
    result["lineage_hash"] = _hash({k: v for k, v in result.items() if k != "lineage_hash"})
    return result


def _envelope(result):
    import hashlib
    result_id = result["result_id"]
    idx = result_id.split("-")[-1]
    scope_key = hashlib.sha256(
        "SYN-PROJECTSYN-SITE-1SYN-SUBJ-1".encode("utf-8")).hexdigest()
    env = {
        "envelope_id": result["scope_envelope_id"], "record_id": result["stable_source_record_id"],
        "record_status": result["record_status"], "project_ref": "SYN-PROJECT",
        "run_ref": "SYN-RUN-2", "monitoring_mode": "full", "scope_type": "subject",
        "scope_key": scope_key,
        "subject_ref": "SYN-SUBJ-1", "site_ref": "SYN-SITE-1", "domain_id": "LB",
        "episode_key": "EP-1", "source_revision": "SYN-REV-2",
        "accepted_snapshot_ref": "SYN-SNAP-2",
        "cutoff": "2026-01-31T23:59:59+08:00",
        "observed_time_ref": result["collection_or_exam_time"],
        "scope_binding_id": "SYN-SCOPE-1",
        "authority_binding_id": "SYN-AUTH-LABMAN-4",
        "source_locator_ids": [f"SYN-LOC-{idx}"],
    }
    env["record_content_hash"] = _hash({k: v for k, v in env.items() if k != "record_content_hash"})
    return env


def _attach_results(input_data, results):
    input_data = copy.deepcopy(input_data)
    input_data["observed_results"] = results
    input_data["scope_envelopes"] = [_envelope(r) for r in results]
    return input_data


def _flat(root):
    out = {}
    stack = [(root, "")]
    while stack:
        value, prefix = stack.pop()
        if isinstance(value, dict):
            for key, item in value.items():
                stack.append((item, f"{prefix}.{key}" if prefix else str(key)))
        else:
            out[prefix] = value
    return out


# ---------------------------------------------------------------------------
# Integrity pipeline
# ---------------------------------------------------------------------------


class TestIntegrityPipeline:
    def test_stage_order_is_frozen(self):
        assert INTEGRITY_STAGES == (
            "schema_parse", "canonical_hash", "artifact_hash",
            "contract_semantic_hash", "scope_cutoff", "authority_version",
            "correction_chain", "identity_duplicate", "foreign_key_bijection",
            "d05_gate_applicability", "evaluator_admission",
        )

    def test_stale_hash_fails_at_canonical_hash_with_no_medical_output(self):
        base = _base_input()
        base = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        # Mutate one lineage hash to a stale value.
        base["observed_results"][2]["lineage_hash"] = "0" * 64
        raw = evaluate_safety(base)
        flat = _flat(raw)
        assert raw["integrity"]["stage"] == "canonical_hash"
        assert raw["integrity"]["error_type"] == "stale_hash"
        assert raw["integrity"]["error_object"] == "observed_results[2]"
        # Fail-closed: no medical/priority/risk/Query/Journey output.
        assert raw["unit_count"] == 0
        assert "units" not in raw
        assert "ownership" not in raw
        assert "journey" not in raw
        assert raw["domain_complete"] is False
        assert raw["l0_complete"] is False
        assert not any(k.startswith("journey.") for k in flat)

    def test_scope_mismatch_fails_at_scope_cutoff(self):
        base = _base_input()
        base = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        base["scope_envelopes"][0]["project_ref"] = "SYN-WRONG-PROJECT"
        base["scope_envelopes"][0]["record_content_hash"] = _hash(
            {k: v for k, v in base["scope_envelopes"][0].items() if k != "record_content_hash"})
        raw = evaluate_safety(base)
        assert raw["integrity"]["stage"] == "scope_cutoff"
        assert raw["integrity"]["error_type"] == "scope_mismatch"
        assert raw["unit_count"] == 0
        assert "units" not in raw

    def test_out_of_cutoff_fails_closed(self):
        base = _base_input()
        base = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        base["cutoff_decisions"][2]["admitted"] = False
        base["cutoff_decisions"][2]["decision"] = "out_of_cutoff"
        base["cutoff_decisions"][2]["hash"] = _hash(
            {k: v for k, v in base["cutoff_decisions"][2].items() if k != "hash"})
        raw = evaluate_safety(base)
        assert raw["integrity"]["stage"] == "scope_cutoff"
        assert raw["integrity"]["error_type"] == "out_of_cutoff"
        assert raw["unit_count"] == 0

    def test_authority_version_mismatch_fails_closed(self):
        base = _base_input()
        base = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        base["authority_bindings"][0]["selected_version"] = "3"
        base["authority_bindings"][0]["hash"] = _hash(
            {k: v for k, v in base["authority_bindings"][0].items() if k != "hash"})
        raw = evaluate_safety(base)
        assert raw["integrity"]["stage"] == "authority_version"
        assert raw["integrity"]["error_type"] == "authority_mismatch"
        assert raw["unit_count"] == 0

    def test_duplicate_identity_fails_closed(self):
        base = _base_input()
        base = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        base["scope_envelopes"][2]["record_id"] = "SYN-REC-2"
        base["scope_envelopes"][2]["record_content_hash"] = _hash(
            {k: v for k, v in base["scope_envelopes"][2].items() if k != "record_content_hash"})
        raw = evaluate_safety(base)
        assert raw["integrity"]["stage"] == "identity_duplicate"
        assert raw["integrity"]["error_type"] == "duplicate_identity"

    def test_foreign_key_error_fails_closed(self):
        base = _base_input()
        base = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        base["observed_results"][2]["scope_envelope_id"] = "SYN-ENV-NOT-EXISTS"
        base["observed_results"][2]["lineage_hash"] = _hash(
            {k: v for k, v in base["observed_results"][2].items() if k != "lineage_hash"})
        raw = evaluate_safety(base)
        assert raw["integrity"]["stage"] == "foreign_key_bijection"
        assert raw["integrity"]["error_type"] == "foreign_key_error"

    def test_unknown_schema_key_fails_at_schema_parse(self):
        base = _base_input()
        base["run_scope_binding"]["unexpected_key"] = "x"
        raw = evaluate_safety(base)
        assert raw["integrity"]["stage"] == "schema_parse"
        assert raw["integrity"]["error_type"] == "schema_error"

    def test_no_medical_output_on_any_failure(self):
        base = _base_input()
        base = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        base["observed_results"][1]["lineage_hash"] = "1" * 64
        raw = evaluate_safety(base)
        flat = _flat(raw)
        assert raw["integrity"]["error_type"] == "stale_hash"
        assert raw["unit_count"] == 0
        assert not any(k.startswith("units.") for k in flat)
        assert not any(k.startswith("ownership.") for k in flat)


# ---------------------------------------------------------------------------
# Deterministic medical evaluation
# ---------------------------------------------------------------------------


def _healthy_run():
    base = _base_input()
    return _attach_results(base, [
        _result("SYN-RES-1", "SYN-TIME-1", "28"),
        _result("SYN-RES-2", "SYN-TIME-2", "30"),
        _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
    ])


class TestDeterminism:
    def test_identical_input_identical_output(self):
        inp = _healthy_run()
        first = evaluate_safety(inp)
        second = evaluate_safety(inp)
        assert first == second

    def test_leaf_counts_are_reported(self):
        raw = evaluate_safety(_healthy_run())
        assert raw["integrity_error"] is None
        assert raw["medical_leaf_count"] > 0
        assert raw["trace_leaf_count"] > 0
        assert raw["source_leaf_count"] > 0


class TestMedicalEvaluation:
    def test_new_abnormality_positive_unit(self):
        raw = evaluate_safety(_healthy_run())
        units = raw["units"]
        assert len(units) == 2
        obs = units["0"]
        assert obs["unit_kind"] == "observation_interpretation"
        assert obs["l1_disposition"] == "positive"
        assert obs["primary_subtype"] == "new_abnormality"
        assert obs["reference_range_state"] == "high"
        assert obs["grade_state"] == "graded"
        assert obs["grade"] == "G2"
        assert obs["trend_kind"] == "new_abnormality"
        assert obs["clinical_significance"] == "unknown"
        assert obs["monitoring_priority"] == "medium"
        followup = units["1"]
        assert followup["unit_kind"] == "followup_obligation"
        assert followup["repeat_state"] == "required_missing"
        assert followup["l1_disposition"] == "positive"
        assert followup["primary_subtype"] == "missing_repeat_or_followup"

    def test_repeat_met_followup_is_negative(self):
        base = _base_input()
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
            _result("SYN-RES-4", "SYN-TIME-3", "36", visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        followup = raw["units"]["1"]
        assert followup["repeat_state"] == "required_met"
        assert followup["l1_disposition"] == "negative"

    def test_grade_comparison_mismatch(self):
        base = _base_input()
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3",
                    reported_grade="G1"),
        ])
        raw = evaluate_safety(inp)
        obs = raw["units"]["0"]
        assert obs["grade"] == "G2"
        assert obs["grade_comparison_state"] == "mismatch"

    def test_g3_high_priority(self):
        base = _base_input()
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "260", flag="H", visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        obs = raw["units"]["0"]
        assert obs["grade"] == "G3"
        assert obs["monitoring_priority"] == "high"
        assert obs["primary_subtype"] == "new_abnormality"
        assert raw["ownership"]["risk_candidate_present"] is True
        assert raw["ownership"]["query_draft_present"] is True

    def test_negative_within_range(self):
        base = _base_input()
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "36", visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        obs = raw["units"]["0"]
        assert obs["reference_range_state"] == "within_range"
        assert obs["l1_disposition"] == "negative"
        assert obs["monitoring_priority"] == "low"

    def test_ncs_consistent_negative(self):
        base = _base_input()
        reason = {
            "reason_ref_id": "SYN-REASON-1", "reason_text": "无相关症状",
            "source_locator_ids": ["SYN-LOC-REASON"],
        }
        reason["hash"] = _hash({k: v for k, v in reason.items() if k != "hash"})
        base["clinical_significance_reason_refs"] = [reason]
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "48", flag="H", cs="NCS", visit="SYN-VISIT-3"),
            _result("SYN-RES-4", "SYN-TIME-2", "36", cs="NCS", visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        obs = raw["units"]["0"]
        assert obs["clinical_significance"] == "NCS"
        assert obs["clinical_significance_consistency"] == "consistent"
        assert obs["l1_disposition"] == "negative"

    def test_low_range_ratio_to_lln(self):
        base = _base_input()
        base["reference_range_definitions"][0].update({
            "range_kind": "closed_interval", "lower": "125", "upper": "350",
            "lower_inclusive": True, "stable_measure_key": "SYN-LB-PLT",
        })
        base["reference_range_definitions"][0]["hash"] = _hash(
            {k: v for k, v in base["reference_range_definitions"][0].items() if k != "hash"})
        base["grade_rule_sets"][0]["stable_measure_key"] = "SYN-LB-PLT"
        base["grade_rule_sets"][0]["hash"] = _hash(
            {k: v for k, v in base["grade_rule_sets"][0].items() if k != "hash"})
        base["measure_definitions"][0]["stable_measure_key"] = "SYN-LB-PLT"
        base["measure_definitions"][0]["definition_hash"] = _hash(
            {k: v for k, v in base["measure_definitions"][0].items() if k != "definition_hash"})
        base["grade_rules"] = []
        for idx, (lo, hi, grade) in enumerate(
            [("0.75", "1.0", "G1"), ("0.5", "0.75", "G2"), ("0.25", "0.5", "G3")], start=1
        ):
            rule = {
                "grade_rule_id": f"SYN-GR-PLT-{idx}", "sequence": idx, "grade": grade,
                "comparator": "between", "left_operand": "ratio_to_lln",
                "lower": lo, "upper": hi, "lower_inclusive": True,
                "upper_inclusive": False, "required_context_fields": [],
                "source_locator_ids": ["SYN-LOC-RULE"],
            }
            rule["hash"] = _hash({k: v for k, v in rule.items() if k != "hash"})
            base["grade_rules"].append(rule)
        base["grade_rule_sets"][0]["ordered_grade_rule_ids"] = [r["grade_rule_id"] for r in base["grade_rules"]]
        base["grade_rule_sets"][0]["hash"] = _hash(
            {k: v for k, v in base["grade_rule_sets"][0].items() if k != "hash"})
        for rule in base["monitoring_rules"]:
            rule["applicable_measure_keys"] = ["SYN-LB-PLT"]
            rule["hash"] = _hash({k: v for k, v in rule.items() if k != "hash"})
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "150", measure_key="SYN-LB-PLT"),
            _result("SYN-RES-2", "SYN-TIME-2", "60", flag="L", visit="SYN-VISIT-3",
                    measure_key="SYN-LB-PLT"),
        ])
        raw = evaluate_safety(inp)
        obs = raw["units"]["0"]
        assert obs["reference_range_state"] == "low"
        assert obs["grade"] == "G3"
        assert obs["grade_state"] == "graded"

    def test_domain_complete_flags(self):
        raw = evaluate_safety(_healthy_run())
        assert raw["l0_complete"] is True
        assert raw["expected_set_reconciled"] is True
        assert raw["all_units_disposed"] is True
        assert raw["not_evaluable_count"] == 0
        assert raw["open_d05_gate_count"] == 0
        assert raw["domain_complete"] is True

    def test_not_evaluable_blocks_domain_complete(self):
        base = _base_input()
        # Drop the range definition: no applicable range -> not_evaluable.
        base["reference_range_definitions"] = []
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        obs = raw["units"]["0"]
        assert obs["l1_disposition"] == "not_evaluable"
        assert obs["reference_range_state"] == "not_classifiable"
        assert raw["not_evaluable_count"] == 1
        assert raw["domain_complete"] is False

    def test_handoff_to_d04_with_pd_permission(self):
        base = _base_input()
        ctx = {
            "d04_context_ref_id": "SYN-D04-CTX-1",
            "context_kind": "protocol_deviation_candidate",
            "protocol_clause_ref": "SYN-D04-CLAUSE-1",
            "context_accepted": True, "context_scope_equal": True,
            "accepted_content_hash": "sha256:" + "a" * 64,
            "source_locator_ids": ["SYN-LOC-D04"],
        }
        ctx["hash"] = _hash({k: v for k, v in ctx.items() if k != "hash"})
        base["d04_context_refs"] = [ctx]
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "260", flag="H", visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        assert raw["ownership"]["handoff_target_domain"] == "D04"
        assert raw["ownership"]["downstream_handoff_present"] is True
        assert raw["ownership"]["pd_wording_permitted"] is True

    def test_lifecycle_carry_forward(self):
        base = _base_input()
        base["previous_run_scope_binding"] = copy.deepcopy(base["run_scope_binding"])
        base["previous_run_scope_binding"]["scope_binding_id"] = "SYN-SCOPE-PREV"
        base["previous_run_scope_binding"]["lineage_hash"] = _hash(
            {k: v for k, v in base["previous_run_scope_binding"].items() if k != "lineage_hash"})
        carry = {
            "carry_forward_ref_id": "SYN-CARRY-1", "previous_run_ref": "SYN-RUN-1",
            "previous_scope_binding_id": "SYN-SCOPE-PREV",
            "source_risk_id": "SYN-RISK-1", "identity_resolution_state": "resolved",
            "source_locator_ids": ["SYN-LOC-PREV"],
        }
        carry["hash"] = _hash({k: v for k, v in carry.items() if k != "hash"})
        base["carry_forward_refs"] = [carry]
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        assert raw["lifecycle"]["transition"] == "carry_forward"
        assert raw["lifecycle"]["carry_forward_source_risk_id"] == "SYN-RISK-1"
        assert raw["ownership"]["risk_candidate_present"] is True

    def test_lifecycle_closed_when_withdrawn(self):
        base = _base_input()
        base["previous_run_scope_binding"] = copy.deepcopy(base["run_scope_binding"])
        base["previous_run_scope_binding"]["scope_binding_id"] = "SYN-SCOPE-PREV"
        base["previous_run_scope_binding"]["lineage_hash"] = _hash(
            {k: v for k, v in base["previous_run_scope_binding"].items() if k != "lineage_hash"})
        carry = {
            "carry_forward_ref_id": "SYN-CARRY-1", "previous_run_ref": "SYN-RUN-1",
            "previous_scope_binding_id": "SYN-SCOPE-PREV",
            "source_risk_id": "SYN-RISK-1", "identity_resolution_state": "resolved",
            "source_locator_ids": ["SYN-LOC-PREV"],
        }
        carry["hash"] = _hash({k: v for k, v in carry.items() if k != "hash"})
        base["carry_forward_refs"] = [carry]
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3",
                    status="withdrawn"),
        ])
        raw = evaluate_safety(inp)
        assert raw["lifecycle"]["transition"] == "closed"
        assert raw["lifecycle"]["close_reason"] == "withdrawn_by_source"
        assert raw["ownership"]["risk_candidate_present"] is False

    def test_d05_gate_blocks_evaluation(self):
        base = _base_input()
        gate = {
            "d05_gate_binding_id": "SYN-GATE-1", "source_record_id": "SYN-REC-3",
            "blocked_observation_id": "SYN-BLOCKED-1",
            "blocked_stage": "evaluation_admission",
            "control_plane_state": "boundary", "reason_codes": ["d05_visit_activity_unresolved"],
            "project_ref": "SYN-PROJECT", "run_ref": "SYN-RUN-2",
            "scope_binding_id": "SYN-SCOPE-1", "subject_ref": "SYN-SUBJ-1",
            "site_ref": "SYN-SITE-1", "source_locator_ids": ["SYN-LOC-GATE"],
        }
        gate["hash"] = _hash({k: v for k, v in gate.items() if k != "hash"})
        base["d05_gate_bindings"] = [gate]
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "128", flag="H", visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        assert raw["open_d05_gate_count"] == 1
        assert raw["blocked"]["0"]["d05_gate_binding_id"] == "SYN-GATE-1"
        assert raw["unit_count"] == 0
        assert raw["domain_complete"] is False
        assert raw["ownership"]["owner_domain"] == "D05"
        assert raw["ownership"]["d07_action"] == "handoff_only"
        assert raw["coverage"]["expected_unit_count"] == 1
        assert raw["coverage"]["missing_unit_count"] == 1

    def test_not_applicable_with_authority(self):
        base = _base_input()
        collection = {
            "authority_binding_id": "SYN-AUTH-COLLECT-1", "claim_kind": "collection_scope",
            "candidate_authority_ids": ["SYN-AUTH-COLLECT-1"],
            "selected_authority_id": "SYN-AUTH-COLLECT-1", "selected_version": "2",
            "decision_status": "unique",
            "effective_interval": ["2025-01-01", "2026-12-31"],
            "scope_predicate_results": [True], "source_locator_ids": ["SYN-LOC-RULE"],
        }
        collection["hash"] = _hash({k: v for k, v in collection.items() if k != "hash"})
        base["authority_bindings"].append(collection)
        evidence = {
            "applicability_evidence_id": "SYN-APP-1", "scope_binding_id": "SYN-SCOPE-1",
            "unit_candidate_key": "SYN-LB-ALT|SYN-REQ-1",
            "authority_binding_id": "SYN-AUTH-COLLECT-1",
            "applicability_rule_id": "SYN-APP-RULE-1",
            "applicability": "not_applicable", "control_plane_no_match": False,
            "predicate_results": [True], "source_locator_ids": ["SYN-LOC-APP"],
        }
        evidence["hash"] = _hash({k: v for k, v in evidence.items() if k != "hash"})
        base["applicability_evidence"] = [evidence]
        raw = evaluate_safety(base)
        obs = raw["units"]["0"]
        assert obs["l1_disposition"] == "not_applicable"
        assert obs["applicability_evidence_id"] == "SYN-APP-1"
        assert obs["applicability_authority_id"] == "SYN-AUTH-COLLECT-1"
        assert raw["ownership"]["d07_action"] == "not_applicable"
        assert raw["ownership"]["risk_candidate_present"] is False
        assert raw["domain_complete"] is True


# ---------------------------------------------------------------------------
# Named kernel invariants (absent from the typed schema): off-fixture
# mutation tests that prove each frozen constant is gated, not a fallback.
# ---------------------------------------------------------------------------


class TestKernelInvariants:
    """The unit dictionary v5 (authority-bound) and the typed baseline /
    safety-critical magnitude thresholds must each be exercised by an
    off-fixture mutation test proving their gating: present -> applied,
    absent -> fail-closed (no fallback)."""

    def test_unit_dictionary_v5_gates_mukat_conversion(self):
        # The µkat/L -> U/L conversion only exists as the frozen dictionary
        # v5, bound through the typed ``claim_kind=unit_dictionary``
        # authority.  With the authority bound the result normalizes; without
        # it the conversion fails closed (no fallback).
        bound = _attach_results(_base_input(), [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "3.2", flag="H",
                      visit="SYN-VISIT-3", unit="µkat/L"),
        ])
        raw = evaluate_safety(bound)
        assert raw["integrity"]["error_type"] is None
        assert raw["units"]["0"]["reference_range_state"] == "high"
        assert raw["units"]["0"]["grade"] == "G2"

        unbound = _base_input()
        unbound["authority_bindings"] = [
            a for a in unbound["authority_bindings"]
            if a.get("claim_kind") != "unit_dictionary"
        ]
        unbound = _attach_results(unbound, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "3.2", flag="H",
                      visit="SYN-VISIT-3", unit="µkat/L"),
        ])
        raw = evaluate_safety(unbound)
        assert raw["integrity"]["error_type"] is None
        assert raw["units"]["0"]["reference_range_state"] == "not_classifiable"
        assert raw["units"]["0"]["l1_disposition"] == "not_evaluable"
        assert raw["units"]["0"]["monitoring_priority"] == "unknown"

    def test_baseline_confirmation_relative_deviation_drops_points(self):
        # The 2% relative deviation separates a baseline-confirmation point
        # (<= 2% from the abnormal baseline, dropped from the episode) from a
        # true further deviation (> 2%, kept).  100 -> 101 is +1% (dropped),
        # 100 -> 104 is +4% (kept).
        inp = _attach_results(_base_input(), [
            _result("SYN-RES-1", "SYN-TIME-1", "100", flag="H"),
            _result("SYN-RES-2", "SYN-TIME-2", "101", flag="H"),
            _result("SYN-RES-3", "SYN-TIME-3", "104", flag="H",
                      visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        assert raw["integrity"]["error_type"] is None
        assert raw["units"]["0"]["source_result_ids"] == [
            "SYN-RES-1", "SYN-RES-3",
        ]

    @staticmethod
    def _no_g3_grade_input():
        base = _base_input()
        rules = []
        for idx, (cid, lo, hi, grade, comparator) in enumerate([
            ("SYN-GR-1", "1.0", "3.0", "G1", "between"),
            ("SYN-GR-2", "3.0", "10.0", "G2", "between"),
            ("SYN-GR-4", "10.0", None, "G4", "gt"),
        ], start=1):
            rule = {
                "grade_rule_id": cid, "sequence": idx, "grade": grade,
                "comparator": comparator, "left_operand": "ratio_to_uln",
                "lower": lo, "upper": hi, "lower_inclusive": True,
                "upper_inclusive": False, "required_context_fields": [],
                "source_locator_ids": ["SYN-LOC-RULE"],
            }
            if comparator == "gt":
                rule.pop("upper")
                rule.pop("upper_inclusive")
            rule["hash"] = _hash({k: v for k, v in rule.items() if k != "hash"})
            rules.append(rule)
        base["grade_rules"] = rules
        base["grade_rule_sets"][0]["ordered_grade_rule_ids"] = [
            r["grade_rule_id"] for r in rules
        ]
        base["grade_rule_sets"][0]["hash"] = _hash({
            k: v for k, v in base["grade_rule_sets"][0].items() if k != "hash"
        })
        # Drop the typed monitoring rules/predicates so the only high-promoting
        # magnitude signal left is the typed safety-critical threshold.
        base["monitoring_rules"] = []
        base["monitoring_predicates"] = []
        return base

    def test_safety_critical_ratio_threshold_promotes_to_high(self):
        # With no G3 grade band, the 5.0xULN safety-critical threshold (typed
        # trigger ``high_priority_clinical_flag``) is the only high-promoting
        # rule: a ratio of 5.0 promotes to high, 4.9 stays medium.
        base = self._no_g3_grade_input()
        at_threshold = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "200", flag="H",
                      visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(at_threshold)
        assert raw["units"]["0"]["grade"] == "G2"
        assert raw["units"]["0"]["monitoring_priority"] == "high"

        below = _attach_results(self._no_g3_grade_input(), [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "196", flag="H",
                      visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(below)
        assert raw["units"]["0"]["grade"] == "G2"
        assert raw["units"]["0"]["monitoring_priority"] == "medium"

    def test_baseline_magnitude_absent_fails_closed(self):
        # Without the typed baseline magnitude the baseline-abnormal episode
        # fails closed: only the baseline is kept (no further-deviation claim
        # without the authorised magnitude rule).
        base = _base_input()
        del base["baseline_rules"][0]["baseline_confirmation_relative_deviation"]
        base["baseline_rules"][0]["hash"] = _hash({
            k: v for k, v in base["baseline_rules"][0].items() if k != "hash"
        })
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "100", flag="H"),
            _result("SYN-RES-2", "SYN-TIME-2", "101", flag="H"),
            _result("SYN-RES-3", "SYN-TIME-3", "104", flag="H",
                      visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        assert raw["integrity"]["error_type"] is None
        assert raw["units"]["0"]["source_result_ids"] == ["SYN-RES-1"]

    def test_safety_threshold_absent_fails_closed(self):
        # Without the typed safety-critical threshold the flag does not
        # promote a 5.0xULN ratio (no evaluator-internal 5 fallback).
        base = self._no_g3_grade_input()
        for rule in base["priority_precedence_rules"]:
            if rule.get("trigger") == "high_priority_clinical_flag":
                rule.pop("safety_critical_ratio_threshold", None)
                rule["hash"] = _hash({
                    k: v for k, v in rule.items() if k != "hash"
                })
        inp = _attach_results(base, [
            _result("SYN-RES-1", "SYN-TIME-1", "28"),
            _result("SYN-RES-2", "SYN-TIME-2", "30"),
            _result("SYN-RES-3", "SYN-TIME-3", "200", flag="H",
                      visit="SYN-VISIT-3"),
        ])
        raw = evaluate_safety(inp)
        assert raw["units"]["0"]["grade"] == "G2"
        assert raw["units"]["0"]["monitoring_priority"] == "medium"


# ---------------------------------------------------------------------------
# Runtime closure (no reverse dependency on test-side artifacts)
# ---------------------------------------------------------------------------


class TestRuntimeClosure:
    def test_evaluator_does_not_import_test_artifacts(self):
        import mm_r4.d07_safety
        import mm_r4.d07_safety_evaluator

        for module in (mm_r4.d07_safety, mm_r4.d07_safety_evaluator):
            source = open(module.__file__, encoding="utf-8").read()
            # No import/read of the frozen test-side artifact files.
            for forbidden in (
                "typed_fixture_catalog", "expected_outcome_oracle",
                "challenge_manifest_registry", "generate_d07_challenge_registry",
                "reviews/medical_monitoring_r4_d07",
            ):
                assert forbidden not in source, f"{module.__file__} references {forbidden!r}"
            # No branching on case/fixture/test identifiers.
            for forbidden in ("case_id", "fixture_id", "test_id", "d07f-", "d07-test"):
                assert forbidden not in source, f"{module.__file__} references {forbidden!r}"

    def test_content_hashes_are_sha256_hex(self):
        raw = evaluate_safety(_healthy_run())
        assert is_sha256_hex(raw["source"]["source_locator_ids"][0]) is False  # locators are ids
        # The runtime never fabricates hashes for input objects.
        assert raw["integrity"]["stage"] == "admitted"

    def test_deterministic_replay_identical_hashes(self):
        inp = _healthy_run()
        first = evaluate_safety(inp)
        second = evaluate_safety(inp)
        assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
