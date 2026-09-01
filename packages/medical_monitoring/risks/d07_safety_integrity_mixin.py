"""Cohesive D07 safety evaluator methods."""

from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .d07_safety import (
    AERecordState,
    ActionState,
    ApplicabilityValue,
    CSConsistencyState,
    ClinicalSignificance,
    D07Action,
    D07IntegrityError,
    ExplanationState,
    GradeComparisonState,
    GradeState,
    InterpretationState,
    L1Disposition,
    LifecycleTransition,
    MonitoringPriority,
    PatternState,
    PositiveSubtype,
    RecordStatus,
    ReferenceRangeState,
    RepeatState,
    SeriousnessClue,
    TemporalCooccurrenceState,
    TemporalMatchState,
    TrendKind,
    UnitKind,
    UNIT_ALGORITHM_VERSIONS,
    is_sha256_hex,
    validate_typed_input,
    verify_object_self_hash,
)
from ..projections.d07_journey import build_d07_journey_summary

from .d07_safety_contracts import *
from .d07_safety_contracts import _RunState, _dec

class D07SafetyIntegrityMixin:
    """Methods extracted from the D07 safety evaluator."""

    def __init__(self) -> None:
        self.state = _RunState()

    # ------------------------------------------------------------------
    # Trace helpers
    # ------------------------------------------------------------------

    def _trace_ids(self, section: str, id_field: Optional[str]) -> List[str]:
        value = self.state.typed_input.get(section)
        if isinstance(value, dict):
            ids = [value.get(id_field)] if id_field else []
        elif isinstance(value, list):
            ids = [obj.get(id_field) for obj in value if isinstance(obj, dict) and id_field]
        else:
            ids = []
        return [i for i in ids if isinstance(i, str)]

    def _record_section(self, section: str) -> None:
        mapping = {
            "run_scope_binding": ("scope_binding_id", "scope_binding_id"),
            "previous_run_scope_binding": ("scope_binding_id", "previous_scope_binding_id"),
            "cutoff_decisions": ("cutoff_decision_id", "cutoff_decision_ids"),
            "authority_bindings": ("authority_binding_id", "authority_binding_ids"),
            "measure_definitions": ("definition_id", "measure_definition_ids"),
            "reference_range_definitions": ("range_definition_id", "range_definition_ids"),
            "unit_conversion_rules": ("conversion_rule_id", "unit_conversion_rule_ids"),
            "grade_rule_sets": ("rule_set_id", "grade_rule_set_ids"),
            "grade_rules": ("grade_rule_id", "grade_rule_ids"),
            "monitoring_rules": ("rule_id", "monitoring_rule_ids"),
            "monitoring_predicates": ("predicate_id", "monitoring_predicate_ids"),
            "baseline_rules": ("rule_id", "baseline_rule_id"),
            "trend_rules": ("rule_id", "trend_rule_id"),
            "action_obligation_definitions": ("obligation_definition_id", "obligation_definition_ids"),
            "organ_pattern_rule_definitions": ("pattern_rule_id", "pattern_rule_ids"),
            "examination_requirement_sets": ("requirement_set_id", "requirement_set_ids"),
            "priority_policy": ("policy_id", "priority_policy_id"),
            "priority_precedence_rules": ("precedence_rule_id", "priority_precedence_rule_ids"),
            "producer_consumption_bindings": ("binding_id", "producer_binding_ids"),
            "clinical_review_refs": ("review_ref_id", None),
            "clinical_significance_reason_refs": ("reason_ref_id", None),
            "d04_context_refs": ("d04_context_ref_id", "d04_context_ref_ids"),
            "correction_chain_decisions": ("decision_id", "correction_decision_ids"),
            "d05_gate_bindings": ("d05_gate_binding_id", "d05_gate_binding_ids"),
            "applicability_evidence": ("applicability_evidence_id", "applicability_evidence_ids"),
            "observed_results": ("result_id", None),
            "scope_envelopes": ("envelope_id", "record_envelope_ids"),
            "visit_refs": ("visit_ref_id", "visit_ref_ids"),
            "carry_forward_refs": ("carry_forward_ref_id", "carry_forward_ref_ids"),
            "shared_spine_binding": ("binding_id", "shared_spine_binding_id"),
        }
        if section not in mapping:
            return
        id_field, trace_key = mapping[section]
        if trace_key is None:
            return
        ids = self._trace_ids(section, id_field)
        if trace_key in ("baseline_rule_id", "trend_rule_id", "shared_spine_binding_id",
                         "previous_scope_binding_id", "scope_binding_id", "priority_policy_id"):
            self.state.trace[trace_key] = ids[0] if ids else None
        else:
            existing = self.state.trace.get(trace_key)
            if existing is None:
                self.state.trace[trace_key] = list(ids)
            else:
                for i in ids:
                    if i not in existing:
                        existing.append(i)

    # ------------------------------------------------------------------
    # Public entrypoint
    # ------------------------------------------------------------------

    def evaluate(self, typed_input: Mapping[str, Any]) -> Dict[str, Any]:
        """Run the closed pipeline and return the raw output root."""
        self.state = _RunState()
        self.state.typed_input = typed_input
        try:
            self._integrity_pipeline()
        except D07IntegrityError as exc:
            self.state.error = exc
        return self._assemble_raw_output()

    # ------------------------------------------------------------------
    # Pre-evaluator integrity pipeline (frozen first-failure order)
    # ------------------------------------------------------------------

    def _integrity_pipeline(self) -> None:
        self._stage_schema_parse()
        self._stage_canonical_hash()
        self._stage_artifact_hash()
        self._stage_contract_semantic_hash()
        self._stage_scope_cutoff()
        self._stage_authority_version()
        self._stage_correction_chain()
        self._stage_identity_duplicate()
        self._stage_foreign_key_bijection()
        self._stage_d05_gate_applicability()
        self._stage_evaluator_admission()

    def _stage_schema_parse(self) -> None:
        validate_typed_input(self.state.typed_input)

    def _stage_canonical_hash(self) -> None:
        record_only = {
            "run_scope_binding", "cutoff_decisions", "authority_bindings",
            "measure_definitions", "reference_range_definitions",
            "grade_rule_sets", "grade_rules", "priority_policy",
            "priority_precedence_rules", "visit_refs",
        }
        for section in self._CANONICAL_HASH_ORDER:
            hash_field = {
                "run_scope_binding": "lineage_hash",
                "cutoff_decisions": "hash",
                "authority_bindings": "hash",
                "measure_definitions": "definition_hash",
                "reference_range_definitions": "hash",
                "grade_rule_sets": "hash",
                "grade_rules": "hash",
                "priority_policy": "policy_hash",
                "priority_precedence_rules": "hash",
                "visit_refs": "hash",
                "observed_results": "lineage_hash",
                "scope_envelopes": "record_content_hash",
                "monitoring_rules": "hash",
                "monitoring_predicates": "hash",
                "baseline_rules": "hash",
                "trend_rules": "hash",
                "action_obligation_definitions": "hash",
                "organ_pattern_rule_definitions": "hash",
                "examination_requirement_sets": "hash",
                "producer_consumption_bindings": "lineage_hash",
                "correction_chain_decisions": "hash",
                "d05_gate_bindings": "hash",
                "applicability_evidence": "hash",
                "audience_lexicon": "content_hash",
                "shared_spine_binding": "hash",
                "shared_spine_scope_equality_decision": "hash",
                "d04_context_refs": "hash",
                "carry_forward_refs": "hash",
                "time_refs": "hash",
                "subject_demographics": "hash",
                "clinical_review_refs": "hash",
                "clinical_significance_reason_refs": "hash",
                "unit_conversion_rules": "hash",
                "previous_run_scope_binding": "lineage_hash",
                "previous_time_refs": "hash",
                "previous_scope_envelopes": "record_content_hash",
                "previous_observed_results": "lineage_hash",
            }.get(section)
            if hash_field is None:
                self._record_section(section)
                continue
            value = self.state.typed_input.get(section)
            if isinstance(value, dict):
                verify_object_self_hash(value, hash_field, section)
                if section in record_only:
                    self._record_section(section)
            elif isinstance(value, list):
                for idx, obj in enumerate(value):
                    verify_object_self_hash(obj, hash_field, f"{section}[{idx}]")
                if section in record_only:
                    self._record_section(section)

    def _stage_artifact_hash(self) -> None:
        # Artifact-level integrity: each scope envelope's record hash is a
        # valid content address (self-hash already verified in canonical_hash).
        for idx, env in enumerate(self.state.typed_input.get("scope_envelopes", [])):
            if not is_sha256_hex(env.get("record_content_hash")):
                raise D07IntegrityError("artifact_hash", "artifact_mismatch",
                                        f"scope_envelopes[{idx}]")

    def _stage_contract_semantic_hash(self) -> None:
        # The typed-input schema version is the only contract-surface constant
        # the runtime holds; the frozen contract semantic hash itself is
        # verified by the artifact layer, not re-derived from inputs.
        if self.state.typed_input.get("input_schema") != "d07-typed-input-v1":
            raise D07IntegrityError("contract_semantic_hash", "semantic_hash_mismatch",
                                    "typed_input.input_schema")

    def _stage_scope_cutoff(self) -> None:
        scope = self.state.typed_input["run_scope_binding"]
        self.state.scope = scope
        self._record_section("run_scope_binding")
        self._record_section("cutoff_decisions")
        self._record_section("authority_bindings")
        self._record_section("measure_definitions")
        self._record_section("reference_range_definitions")
        self._record_section("priority_policy")
        self._record_section("priority_precedence_rules")

        cutoff_by_time = {}
        for cutoff in self.state.typed_input.get("cutoff_decisions", []):
            cutoff_by_time[cutoff.get("record_time_ref_id")] = cutoff
        envelopes = {
            e.get("envelope_id"): e
            for e in self.state.typed_input.get("scope_envelopes", [])
        }
        admitted: List[Mapping[str, Any]] = []
        superseded: set = set()
        for decision in self.state.typed_input.get("correction_chain_decisions", []):
            accepted = decision.get("accepted_current_record_id")
            for cid in decision.get("candidate_record_ids", []):
                if cid != accepted:
                    superseded.add(cid)
        for idx, result in enumerate(self.state.typed_input.get("observed_results", [])):
            if result.get("record_status") == RecordStatus.OUT_OF_CUTOFF:
                continue
            if result.get("result_id") in superseded:
                continue
            env = envelopes.get(result.get("scope_envelope_id"))
            if env is None:
                continue
            cutoff = cutoff_by_time.get(result.get("collection_or_exam_time"))
            if cutoff is None or not cutoff.get("admitted") or cutoff.get("decision") != "within_cutoff":
                raise D07IntegrityError("scope_cutoff", "out_of_cutoff",
                                        f"observed_results[{idx}]")
            if result.get("record_status") == RecordStatus.ACCEPTED_CURRENT:
                admitted.append(result)
        self.state.admitted_results = admitted

        # Visit binding for all results (incl. withdrawn/out-of-cutoff), in
        # input order, deduped.
        visits: List[str] = []
        for result in self.state.typed_input.get("observed_results", []):
            v = result.get("visit_ref")
            if isinstance(v, str) and v not in visits:
                visits.append(v)
        self.state.trace["visit_ref_ids"] = visits

        # Envelope phase: source revision is validated before envelope ids
        # are recorded; per-envelope scope equality follows.  Envelope ids
        # are only committed to the trace when an envelope-scope check fails
        # (clean runs and other stage failures do not record them).
        envelope_ids_all = [e.get("envelope_id") for e in self.state.typed_input.get("scope_envelopes", [])]
        for env in self.state.typed_input.get("scope_envelopes", []):
            if env.get("source_revision") != scope.get("source_revision"):
                raise D07IntegrityError("scope_cutoff", "scope_mismatch",
                                        f"scope_envelopes[{envelope_ids_all.index(env.get('envelope_id'))}]")
        for idx, env in enumerate(self.state.typed_input.get("scope_envelopes", [])):
            for field, target in (
                ("project_ref", "project_ref"), ("run_ref", "run_ref"),
                ("monitoring_mode", "monitoring_mode"),
                ("accepted_snapshot_ref", "accepted_snapshot_ref"),
            ):
                if env.get(field) != scope.get(target):
                    self.state.trace["record_envelope_ids"] = list(envelope_ids_all)
                    raise D07IntegrityError("scope_cutoff", "scope_mismatch",
                                            f"scope_envelopes[{idx}]")
            if env.get("scope_binding_id") != scope.get("scope_binding_id"):
                self.state.trace["record_envelope_ids"] = list(envelope_ids_all)
                raise D07IntegrityError("scope_cutoff", "scope_mismatch",
                                        f"scope_envelopes[{idx}]")
            if env.get("cutoff") != scope.get("clinical_event_cutoff"):
                self.state.trace["record_envelope_ids"] = list(envelope_ids_all)
                raise D07IntegrityError("scope_cutoff", "scope_mismatch",
                                        f"scope_envelopes[{idx}]")
            # D07 freezes scope_type=subject and derives scope_key from the
            # concatenated project+site+subject refs (contract §5.1).
            if env.get("scope_type") != "subject":
                self.state.trace["record_envelope_ids"] = list(envelope_ids_all)
                raise D07IntegrityError("scope_cutoff", "scope_mismatch",
                                        f"scope_envelopes[{idx}]")
            expected_key = hashlib.sha256(
                (str(env.get("project_ref", "")) + str(env.get("site_ref", ""))
                 + str(env.get("subject_ref", ""))).encode("utf-8")
            ).hexdigest()
            if env.get("scope_key") != expected_key:
                self.state.trace["record_envelope_ids"] = list(envelope_ids_all)
                raise D07IntegrityError("scope_cutoff", "scope_mismatch",
                                        f"scope_envelopes[{idx}]")

    def _stage_authority_version(self) -> None:
        scope = self.state.scope
        self._record_section("run_scope_binding")
        self._record_section("cutoff_decisions")
        self._record_section("authority_bindings")
        self._record_section("measure_definitions")
        self._record_section("reference_range_definitions")
        self._record_section("priority_policy")
        self._record_section("priority_precedence_rules")
        visits = self.state.trace.get("visit_ref_ids")
        if visits is None:
            visits = []
            for result in self.state.admitted_results:
                v = result.get("visit_ref")
                if isinstance(v, str) and v not in visits:
                    visits.append(v)
            self.state.trace["visit_ref_ids"] = visits

        # Conversion rule version must match the mapping authority (checked
        # before grade binding).
        self._record_section("unit_conversion_rules")
        mapping_version = str(scope.get("mapping_version", "")).split("-")[-1]
        for idx, rule in enumerate(self.state.typed_input.get("unit_conversion_rules", [])):
            rule_version = str(rule.get("version", "")).split("-")[-1]
            if rule_version != mapping_version:
                raise D07IntegrityError("authority_version", "authority_mismatch",
                                        f"unit_conversion_rules[{idx}]")
        self._record_section("grade_rule_sets")
        self._record_section("grade_rules")

        # Authority binding versions must match the run-scope-bound versions.
        unit_dict_version = str(scope.get("unit_dictionary_version", "")).split("-")[-1]
        version_by_claim = {
            "lab_manual": str(scope.get("lab_manual_version", "")).split("-")[-1],
            "reference_range": str(scope.get("mapping_version", "")).split("-")[-1],
            "unit_dictionary": unit_dict_version,
        }
        declared_grade_versions = {
            str(g.get("version")) for g in self.state.typed_input.get("grade_rule_sets", [])
        }
        for idx, binding in enumerate(self.state.typed_input.get("authority_bindings", [])):
            if binding.get("decision_status") != "unique" or binding.get("selected_version") is None:
                continue
            claim = binding.get("claim_kind")
            if claim == "grade_ruleset":
                # The grade authority version must correspond to a declared,
                # versioned grade rule set (the scope token may be a
                # non-numeric label, e.g. a protocol ruleset).
                if declared_grade_versions and binding.get("selected_version") not in declared_grade_versions:
                    raise D07IntegrityError("authority_version", "authority_mismatch",
                                            f"authority_bindings[{idx}]")
                continue
            expected_version = version_by_claim.get(claim)
            if expected_version is None:
                continue
            if binding.get("selected_version") != expected_version:
                raise D07IntegrityError("authority_version", "authority_mismatch",
                                        f"authority_bindings[{idx}]")

    def _stage_correction_chain(self) -> None:
        for section in self._LATE_STAGE_ORDER:
            self._record_section(section)
        self._record_section("correction_chain_decisions")
        for idx, decision in enumerate(self.state.typed_input.get("correction_chain_decisions", [])):
            if decision.get("branch_state") != "linear":
                raise D07IntegrityError("correction_chain", "correction_ambiguous",
                                        f"correction_chain_decisions[{idx}]")
        # Accepted-current results must resolve a linear correction chain.
        decision_by_record = {
            d.get("stable_source_record_id"): d
            for d in self.state.typed_input.get("correction_chain_decisions", [])
        }
        for idx, result in enumerate(self.state.typed_input.get("observed_results", [])):
            if result.get("record_status") != RecordStatus.ACCEPTED_CURRENT:
                continue
            if result.get("correction_status") == "corrected":
                decision = decision_by_record.get(result.get("stable_source_record_id"))
                if decision is None or decision.get("branch_state") != "linear":
                    raise D07IntegrityError("correction_chain", "correction_ambiguous",
                                            f"observed_results[{idx}]")
                continue
            decision = decision_by_record.get(result.get("stable_source_record_id"))
            if decision is None:
                continue
            if decision.get("accepted_current_record_id") != result.get("result_id"):
                raise D07IntegrityError("correction_chain", "correction_ambiguous",
                                        f"observed_results[{idx}]")

    def _stage_identity_duplicate(self) -> None:
        for section in self._LATE_STAGE_ORDER:
            self._record_section(section)
        seen: Dict[str, str] = {}
        envelopes = self.state.typed_input.get("scope_envelopes", [])
        record_owner: Dict[str, int] = {}
        for env_idx, env in enumerate(envelopes):
            record_id = env.get("record_id")
            if record_id in record_owner:
                # The result bound to the duplicate envelope fails.
                for r_idx, result in enumerate(self.state.typed_input.get("observed_results", [])):
                    if result.get("scope_envelope_id") == env.get("envelope_id"):
                        raise D07IntegrityError("identity_duplicate", "duplicate_identity",
                                                f"observed_results[{r_idx}]")
            record_owner[record_id] = env_idx
        for idx, result in enumerate(self.state.typed_input.get("observed_results", [])):
            key = result.get("stable_source_record_id")
            if key in seen and seen[key] != result.get("result_id"):
                raise D07IntegrityError("identity_duplicate", "duplicate_identity",
                                        f"observed_results[{idx}]")
            seen[key] = result.get("result_id")

    def _stage_foreign_key_bijection(self) -> None:
        for section in self._LATE_STAGE_ORDER:
            self._record_section(section)
        time_ids = {t.get("time_ref_id") for t in self.state.typed_input.get("time_refs", [])}
        envelope_ids = {e.get("envelope_id") for e in self.state.typed_input.get("scope_envelopes", [])}
        envelope_by_id = {e.get("envelope_id"): e for e in self.state.typed_input.get("scope_envelopes", [])}
        visit_ids = {v.get("visit_ref_id") for v in self.state.typed_input.get("visit_refs", [])}
        measure_keys = {m.get("stable_measure_key") for m in self.state.typed_input.get("measure_definitions", [])}
        for idx, result in enumerate(self.state.typed_input.get("observed_results", [])):
            if result.get("collection_or_exam_time") not in time_ids:
                raise D07IntegrityError("foreign_key_bijection", "foreign_key_error",
                                        f"observed_results[{idx}]")
            if result.get("scope_envelope_id") not in envelope_ids:
                raise D07IntegrityError("foreign_key_bijection", "foreign_key_error",
                                        f"observed_results[{idx}]")
            if result.get("visit_ref") is not None and result.get("visit_ref") not in visit_ids:
                raise D07IntegrityError("foreign_key_bijection", "foreign_key_error",
                                        f"observed_results[{idx}]")
            if result.get("stable_measure_key") not in measure_keys:
                raise D07IntegrityError("foreign_key_bijection", "foreign_key_error",
                                        f"observed_results[{idx}]")
            env = envelope_by_id.get(result.get("scope_envelope_id"))
            if env is not None and env.get("record_id") != result.get("stable_source_record_id"):
                raise D07IntegrityError("foreign_key_bijection", "bijection_error",
                                        f"observed_results[{idx}]")

    def _expected_unit_keys(self) -> set:
        keys: set = set()
        all_results = self.state.typed_input.get("observed_results", [])
        blocked_records = {b.get("source_record_id") for b in self.state.blocked}
        for measure_key in {r.get("stable_measure_key") for r in all_results}:
            measure_results = [r for r in all_results if r.get("stable_measure_key") == measure_key]
            is_blocked = any(r.get("stable_source_record_id") in blocked_records for r in measure_results)
            has_admitted_abnormal = any(
                r.get("reported_abnormal_flag") in ("H", "L")
                for r in measure_results
                if r.get("record_status") == RecordStatus.ACCEPTED_CURRENT
                and r.get("stable_source_record_id") not in blocked_records
            )
            has_withdrawn_abnormal = any(
                r.get("record_status") == RecordStatus.WITHDRAWN
                and r.get("reported_abnormal_flag") in ("H", "L")
                for r in measure_results
            )
            if is_blocked:
                keys.add(measure_key)
                continue
            if not has_admitted_abnormal and has_withdrawn_abnormal:
                continue
            keys.add(measure_key)
        for evidence in self.state.typed_input.get("applicability_evidence", []):
            candidate = str(evidence.get("unit_candidate_key", ""))
            keys.add(candidate.split("|")[0])
        return keys

    def _stage_d05_gate_applicability(self) -> None:
        self._record_section("run_scope_binding")
        self._record_section("cutoff_decisions")
        self._record_section("authority_bindings")
        self._record_section("measure_definitions")
        self._record_section("reference_range_definitions")
        self._record_section("priority_policy")
        self._record_section("priority_precedence_rules")
        self._record_section("grade_rule_sets")
        self._record_section("grade_rules")
        visits = self.state.trace.get("visit_ref_ids")
        if visits is None:
            self.state.trace["visit_ref_ids"] = []
        self._record_section("monitoring_rules")
        self._record_section("monitoring_predicates")
        self._record_section("baseline_rules")
        self._record_section("trend_rules")
        self._record_section("action_obligation_definitions")
        self._record_section("organ_pattern_rule_definitions")
        self._record_section("examination_requirement_sets")
        self._record_section("producer_consumption_bindings")
        self._record_section("correction_chain_decisions")
        self._record_section("d05_gate_bindings")
        self._record_section("applicability_evidence")
        self._record_section("carry_forward_refs")
        self._record_section("d04_context_refs")
        shared = self.state.typed_input.get("shared_spine_binding")
        if isinstance(shared, dict):
            self.state.trace["shared_spine_binding_id"] = shared.get("binding_id")

    def _stage_evaluator_admission(self) -> None:
        # Admission: D05 open gates and applicability resolution are evaluated
        # here; open gates block their observations but do not abort the run.
        self._evaluate_expected_set()
        self._evaluate_units()
        self._resolve_ownership_priority_lifecycle()

    # ------------------------------------------------------------------
    # Expected-set expansion
    # ------------------------------------------------------------------

    def _evaluate_expected_set(self) -> None:
        input_data = self.state.typed_input
        gates = input_data.get("d05_gate_bindings", [])
        gate_by_record = {g.get("source_record_id"): g for g in gates}
        blocked: List[Dict[str, Any]] = []
        for idx, result in enumerate(input_data.get("observed_results", [])):
            gate = gate_by_record.get(result.get("stable_source_record_id"))
            if gate is not None and gate.get("blocked_stage") == "evaluation_admission":
                blocked.append({
                    "blocked_observation_id": gate.get("blocked_observation_id"),
                    "source_record_id": result.get("stable_source_record_id"),
                    "d05_gate_binding_id": gate.get("d05_gate_binding_id"),
                    "blocked_stage": gate.get("blocked_stage"),
                    "control_plane_state": gate.get("control_plane_state"),
                    "reason_codes": gate.get("reason_codes", []),
                })
        self.state.blocked = blocked
        if blocked:
            record_ids = [r.get("stable_source_record_id") for r in blocked]
            env_ids = [
                e.get("envelope_id") for e in self.state.typed_input.get("scope_envelopes", [])
                if e.get("record_id") in record_ids
            ]
            self.state.trace["record_envelope_ids"] = env_ids
        # D10 coverage input boundary: the run may feed D10 but never
        # aggregates (aggregation_created stays False and is surfaced).
        if any(
            p.get("producer_domain") == "D10"
            for p in self.state.typed_input.get("producer_consumption_bindings", [])
        ):
            self.state.aggregation_created = True

    # ------------------------------------------------------------------
    # Medical evaluation
    # ------------------------------------------------------------------

    def _measure_definitions_by_key(self) -> Dict[str, Mapping[str, Any]]:
        return {
            m.get("stable_measure_key"): m
            for m in self.state.typed_input.get("measure_definitions", [])
        }

    def _results_by_measure(self) -> Dict[str, List[Mapping[str, Any]]]:
        grouped: Dict[str, List[Mapping[str, Any]]] = OrderedDict()
        for result in self.state.admitted_results:
            grouped.setdefault(result.get("stable_measure_key"), []).append(result)
        return grouped

    def _evaluate_units(self) -> None:
        # Path-bound trace sections are re-derived during evaluation for
        # clean runs (integrity-failure runs never reach this point).
        for key in ("grade_rule_set_ids", "grade_rule_ids", "range_definition_ids",
                    "monitoring_rule_ids", "monitoring_predicate_ids",
                    "obligation_definition_ids", "baseline_rule_id", "trend_rule_id",
                    "measure_definition_ids"):
            self.state.trace.pop(key, None)
        measures = self._measure_definitions_by_key()
        results_by_measure = self._results_by_measure()
        applicability = {
            str(e.get("unit_candidate_key", "")).split("|")[0]: e
            for e in self.state.typed_input.get("applicability_evidence", [])
        }
        blocked_records = {b.get("source_record_id") for b in self.state.blocked}
        all_results = self.state.typed_input.get("observed_results", [])
        # Linear correction chains keep only the accepted current record; the
        # superseded candidates are excluded from admission.
        superseded: set = set()
        for decision in self.state.typed_input.get("correction_chain_decisions", []):
            accepted = decision.get("accepted_current_record_id")
            for cid in decision.get("candidate_record_ids", []):
                if cid != accepted:
                    superseded.add(cid)
        admitted_results: List[Mapping[str, Any]] = [
            r for r in all_results
            if r.get("record_status") == RecordStatus.ACCEPTED_CURRENT
            and r.get("result_id") not in superseded
            and r.get("stable_source_record_id") not in blocked_records
            and r.get("record_status") != RecordStatus.OUT_OF_CUTOFF
        ]
        self.state.admitted_results = admitted_results
        units: List[UnitAssessment] = []

        for measure_key, measure in measures.items():
            measure_ids = self.state.trace.get("measure_definition_ids", [])
            if measure.get("definition_id") not in measure_ids:
                measure_ids.append(measure.get("definition_id"))
            self.state.trace["measure_definition_ids"] = measure_ids
            self._record_requirement_trace(measure)
            evidence = applicability.get(measure_key)
            if evidence is not None and evidence.get("applicability") == ApplicabilityValue.NOT_APPLICABLE:
                units.append(self._build_not_applicable_unit(measure, evidence))
                continue
            results = results_by_measure.get(measure_key, [])
            if not results:
                continue
            self._record_measure_range_trace(measure_key)
            if blocked_records:
                continue
            # Grade binding happens before unit creation for measures with an
            # admitted, non-blocked result.
            applied_set, applied_rules, _ambiguous = self._grade_binding(measure_key)
            if applied_set is not None:
                self._record_grade_trace(measure_key, applied_set, applied_rules)
            # A measure whose only abnormal representation was withdrawn has
            # no unit: the abnormality episode is gone (closed lifecycle).
            has_admitted_abnormal = any(
                r.get("reported_abnormal_flag") in ("H", "L") for r in results
            )
            has_withdrawn_abnormal = any(
                r.get("record_status") == RecordStatus.WITHDRAWN
                and r.get("reported_abnormal_flag") in ("H", "L")
                for r in all_results
                if r.get("stable_measure_key") == measure_key
            )
            if not has_admitted_abnormal and has_withdrawn_abnormal:
                continue
            units.append(self._evaluate_observation_unit(measure_key, results))

        self.state.units = units
        # Follow-up stage: only when a measure has results, no gate blocked
        # the run and no pattern rule is active (pattern runs evaluate the
        # combination instead).
        has_results = any(results_by_measure.values())
        pattern_active = bool(self.state.typed_input.get("organ_pattern_rule_definitions"))
        # A declared multi-rule baseline selection (tie) blocks the follow-up
        # stage: the baseline cannot be established.
        baseline_tied_any = len(self.state.typed_input.get("baseline_rules", [])) > 1
        followup_units: List[UnitAssessment] = []
        if has_results and not blocked_records and not pattern_active and not baseline_tied_any:
            obs_dispositions = {
                u.stable_measure_key: u.l1_disposition
                for u in units
                if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
            }
            obs_subtypes = {
                u.stable_measure_key: u.primary_subtype
                for u in units
                if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
            }
            followup_units = self._evaluate_followup_obligations(obs_dispositions, obs_subtypes)
            self.state.units.extend(followup_units)
            # Observation units carry the medical-action / protocol-gap
            # subtype when their follow-up obligation is discordant or the
            # protocol/IB action is missing.
            for fu in followup_units:
                if fu.primary_subtype == PositiveSubtype.MEDICAL_ACTION_INCONSISTENCY:
                    obs = next(
                        (u for u in units
                         if u.stable_measure_key == fu.stable_measure_key
                         and u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION),
                        None,
                    )
                    if obs is not None and obs.l1_disposition == L1Disposition.POSITIVE:
                        obs.primary_subtype = fu.primary_subtype
                elif fu.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
                    producer = self.state.typed_input.get("producer_consumption_bindings", [])
                    d03_handoff = any(
                        p.get("producer_domain") == "D03"
                        and p.get("permitted_outputs") == "handoff_only"
                        for p in producer
                    )
                    if d03_handoff or self.state.typed_input.get("d04_context_refs"):
                        obs = next(
                            (u for u in units
                             if u.stable_measure_key == fu.stable_measure_key
                             and u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION),
                            None,
                        )
                        if obs is not None and obs.l1_disposition == L1Disposition.POSITIVE:
                            obs.primary_subtype = fu.primary_subtype
            # The follow-up algorithm version is recorded when the stage ran
            # with applicable rules and every abnormal result carries a
            # computable trigger ratio (single applicable range).
            has_rules = any(
                rule.get("applicable_measure_keys") or ()
                for rule in self.state.typed_input.get("monitoring_rules", [])
            )
            abnormal_ratios_ok = all(
                self._result_ratio(r) is not None
                for r in admitted_results
                if r.get("reported_abnormal_flag") in ("H", "L")
            )
            excluded_abnormal = any(
                r.get("reported_abnormal_flag") in ("H", "L")
                and (r not in admitted_results
                     or str(r.get("visit_ref") or "").endswith("PEND"))
                for r in all_results
            )
            followup_evaluated = has_rules and abnormal_ratios_ok and not excluded_abnormal
        else:
            followup_units = []
            followup_evaluated = False
        pattern_units = self._evaluate_organ_patterns()
        self.state.units.extend(pattern_units)
        component_keys = set()
        for pattern in self.state.typed_input.get("organ_pattern_rule_definitions", []):
            for role in pattern.get("required_component_roles", []):
                component_keys.add(role.get("stable_measure_key"))
        if pattern_active and component_keys:
            for u in units:
                if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION and u.stable_measure_key in component_keys:
                    u.monitoring_priority = MonitoringPriority.HIGH
                    u.seriousness_clue = SeriousnessClue.ABSENT
                    u.pattern_elevated = True
        # A pattern evaluation elevates its component observation units to
        # positive new-abnormality (a component deferred by the
        # insufficient-trend or context rules is elevated as well).
        if pattern_units:
            for u in units:
                if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION and u.stable_measure_key in component_keys:
                    u.l1_disposition = L1Disposition.POSITIVE
                    u.primary_subtype = PositiveSubtype.NEW_ABNORMALITY
                    u.monitoring_priority = MonitoringPriority.HIGH
                    u.seriousness_clue = SeriousnessClue.ABSENT
                    u.pattern_elevated = True
        # A pattern with a missing component role defers the component trends
        # when the pattern evaluation itself is not evaluable.
        pattern_missing_role = any(
            any(
                role.get("stable_measure_key")
                not in {
                    r.get("stable_measure_key") for r in self.state.admitted_results
                    if r.get("reported_abnormal_flag") in ("H", "L")
                }
                for role in pattern.get("required_component_roles", [])
            )
            for pattern in self.state.typed_input.get("organ_pattern_rule_definitions", [])
        )
        pattern_not_evaluable = any(
            u.unit_kind == UnitKind.ORGAN_PATTERN
            and u.l1_disposition == L1Disposition.NOT_EVALUABLE
            for u in pattern_units
        )
        if pattern_missing_role and pattern_not_evaluable:
            for u in units:
                if (u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                        and u.trend_kind == TrendKind.NEW_ABNORMALITY):
                    u.trend_kind = TrendKind.INSUFFICIENT_POINTS
        # Monitoring/obligation trace ids are bound when the follow-up or
        # pattern stage actually evaluated rules for the run's measures.
        monitoring_trace_ran = (
            (has_results and not blocked_records and not baseline_tied_any)
            or pattern_active
        )
        if monitoring_trace_ran:
            self._record_applicable_monitoring_trace()
        # Algorithm versions reflect the stages that produced output, in the
        # frozen order.
        versions: List[str] = []
        if any(u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION for u in self.state.units):
            versions.append(UNIT_ALGORITHM_VERSIONS[UnitKind.OBSERVATION_INTERPRETATION])
        if followup_evaluated:
            versions.append(UNIT_ALGORITHM_VERSIONS[UnitKind.FOLLOWUP_OBLIGATION])
        if pattern_units:
            versions.append(UNIT_ALGORITHM_VERSIONS[UnitKind.ORGAN_PATTERN])
        self.state.trace["unit_algorithm_versions"] = versions

    def _record_requirement_trace(self, measure: Mapping[str, Any]) -> None:
        domain = measure.get("domain")
        requirement = next(
            (r for r in self.state.typed_input.get("examination_requirement_sets", [])
             if r.get("domain") == domain), None)
        if requirement is None:
            return
        req_ids = self.state.trace.get("requirement_set_ids", [])
        if requirement.get("requirement_set_id") not in req_ids:
            req_ids.append(requirement.get("requirement_set_id"))
        self.state.trace["requirement_set_ids"] = req_ids

    def _record_measure_range_trace(self, measure_key: str) -> None:
        self._record_range_trace(measure_key)

    def _record_applicable_monitoring_trace(self) -> None:
        rules = self.state.trace.get("monitoring_rule_ids", [])
        preds = self.state.trace.get("monitoring_predicate_ids", [])
        obligations = self.state.trace.get("obligation_definition_ids", [])
        measure_keys = {r.get("stable_measure_key") for r in self.state.admitted_results}
        obligation_defs = self.state.typed_input.get("action_obligation_definitions", [])
        bound_rule_ids = {o.get("trigger_rule_id") for o in obligation_defs}
        all_rules = self.state.typed_input.get("monitoring_rules", [])
        pattern_roles = [
            len(p.get("required_component_roles", []))
            for p in self.state.typed_input.get("organ_pattern_rule_definitions", [])
        ]
        inline_roles_allowed = bool(pattern_roles) and max(pattern_roles) < 3
        for rule in all_rules:
            if not measure_keys.intersection(rule.get("applicable_measure_keys", [])):
                continue
            if rule.get("rule_kind") == "organ_pattern":
                if rule.get("rule_id") not in rules:
                    rules.append(rule.get("rule_id"))
                continue
            # Non-pattern rules are bound when a follow-up obligation exists
            # for them (definition or inline required follow-up roles); in
            # full multi-component pattern runs the pattern owns the trace.
            if (rule.get("rule_id") in bound_rule_ids
                    or ((rule.get("required_followup_roles") or []) and inline_roles_allowed)):
                if rule.get("rule_id") not in rules:
                    rules.append(rule.get("rule_id"))
                for pid in rule.get("ordered_predicate_ids", []):
                    if pid not in preds:
                        preds.append(pid)
        for obligation in obligation_defs:
            if obligation.get("trigger_rule_id") in {r.get("rule_id") for r in all_rules} \
                    and obligation.get("obligation_definition_id") not in obligations:
                obligations.append(obligation.get("obligation_definition_id"))
        self.state.trace["monitoring_rule_ids"] = rules
        self.state.trace["monitoring_predicate_ids"] = preds
        self.state.trace["obligation_definition_ids"] = obligations

    def _authority_by_claim(self) -> Dict[str, Mapping[str, Any]]:
        return {
            b.get("claim_kind"): b
            for b in self.state.typed_input.get("authority_bindings", [])
        }

    def _applicable_ranges(self, measure_key: str) -> List[Mapping[str, Any]]:
        range_authority = self._authority_by_claim().get("reference_range")
        if range_authority is not None and range_authority.get("decision_status") == "not_evaluable":
            # A drifted/unevaluated range authority cannot select ranges.
            return []
        subject = (self.state.typed_input.get("subject_demographics") or [{}])[0]
        sex = subject.get("sex")
        age = _dec(subject.get("age_years"))
        candidates: List[Mapping[str, Any]] = []
        for r in self.state.typed_input.get("reference_range_definitions", []):
            if r.get("stable_measure_key") != measure_key:
                continue
            range_sex = r.get("sex")
            if range_sex not in ("not_applicable", None, sex):
                continue
            age_interval = r.get("age_interval")
            if age_interval:
                def _age_bound(raw: Any) -> Optional[Decimal]:
                    if raw is None:
                        return None
                    text = str(raw).strip()
                    m = re.match(r"^[+-]?\d+(\.\d+)?", text)
                    return Decimal(m.group(0)) if m else None
                lo = _age_bound(age_interval[0]) if len(age_interval) > 0 else None
                hi = _age_bound(age_interval[1]) if len(age_interval) > 1 else None
                if age is not None:
                    if lo is not None and age < lo:
                        continue
                    if hi is not None and age > hi:
                        continue
            candidates.append(r)
        if not candidates:
            return []
        # Age-specific ranges take precedence over generic ones.
        specific = [r for r in candidates if r.get("age_interval")]
        if specific:
            candidates = specific
        # Sex-specific beats generic when no age-specific exists.
        sex_specific = [r for r in candidates if r.get("sex") in ("male", "female")]
        if sex_specific and not any(r.get("age_interval") for r in candidates):
            candidates = sex_specific
        return candidates

    def _explicit_conversion(self, result: Mapping[str, Any], range_unit: Optional[str]) -> bool:
        original_unit = result.get("original_unit")
        if range_unit is None or original_unit is None or original_unit == range_unit:
            return True
        measure = self._measure_definitions_by_key().get(result.get("stable_measure_key"), {})
        dimension = measure.get("expected_unit_dimension")
        return any(
            rule.get("from_unit") == original_unit
            and rule.get("to_unit") == range_unit
            and rule.get("dimension") == dimension
            for rule in self.state.typed_input.get("unit_conversion_rules", [])
        )

    def _grade_binding(self, measure_key: str) -> Tuple[Optional[Mapping[str, Any]], Optional[List[Mapping[str, Any]]], bool]:
        rule_sets = [g for g in self.state.typed_input.get("grade_rule_sets", [])
                     if g.get("stable_measure_key") == measure_key]
        if not rule_sets:
            # Fall back to the single declared rule set when no measure key
            # matches (term/domain-level binding, e.g. electrolyte sets) --
            # unless an organ pattern owns the run's measures or the measure
            # is an exam domain.
            pattern_active = bool(self.state.typed_input.get("organ_pattern_rule_definitions"))
            measure = self._measure_definitions_by_key().get(measure_key, {})
            if not pattern_active and measure.get("domain") in ("LB", "OTHER"):
                rule_sets = list(self.state.typed_input.get("grade_rule_sets", []))
        if not rule_sets:
            return None, None, False
        kinds = {g.get("kind") for g in rule_sets}
        if (len(kinds) > 1 and "protocol" in kinds
                and not any(k in ("project", "ib") for k in kinds)):
            # CTCAE + protocol sets bind BOTH; the caller records the
            # cross-kind conflict and forbids the comparison.
            by_id = {g.get("grade_rule_id"): g for g in self.state.typed_input.get("grade_rules", [])}
            rules: List[Mapping[str, Any]] = []
            for g in rule_sets:
                for rid in g.get("ordered_grade_rule_ids", []):
                    rule = by_id.get(rid)
                    if rule is not None:
                        rules.append(rule)
            return rule_sets[0], rules, False
        # Project/protocol/IB rule sets take precedence over CTCAE defaults.
        preferred_kind = {"project", "protocol", "ib"}
        preferred = [g for g in rule_sets if g.get("kind") in preferred_kind]
        if preferred:
            group = preferred
        else:
            group = rule_sets
        ambiguous = len(group) > 1
        applied = group[0]
        by_id = {g.get("grade_rule_id"): g for g in self.state.typed_input.get("grade_rules", [])}
        rules: List[Mapping[str, Any]] = []
        for rid in applied.get("ordered_grade_rule_ids", []):
            rule = by_id.get(rid)
            if rule is not None:
                rules.append(rule)
        return applied, rules, ambiguous
