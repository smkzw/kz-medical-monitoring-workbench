"""R4-D07 clinical safety / laboratory / examination evaluator.

Closed typed runtime for the frozen D07 slice.  The evaluator:

* runs the frozen pre-evaluator integrity pipeline
  (``schema_parse -> canonical_hash -> artifact_hash ->
  contract_semantic_hash -> scope_cutoff -> authority_version ->
  correction_chain -> identity_duplicate -> foreign_key_bijection ->
  d05_gate_applicability -> evaluator_admission``), aborting at the first
  failure with a closed error class and **no** medical/priority/risk/Query/
  Journey output;
* performs the deterministic medical evaluation: unit normalization and
  reference-range selection, project-bound CTCAE/protocol grading with
  reported-vs-recomputed comparison, baseline selection, trend
  classification, CS/NCS controlled-value consistency, follow-up
  obligations, organ-pattern clues and examination-context interpretation;
* resolves owner routing / downstream handoffs, monitoring priority
  through the frozen precedence policy, lifecycle transitions against the
  previous accepted run, and the coverage ledger / domain-completeness
  gates;
* assembles the raw output root whose flattened leaf set is exactly
  comparable by the test-side closed DSL (the runtime never reads the
  catalog, oracle, manifest or registry and never branches on case/test/
  fixture identifiers or expected text).

All data is synthetic and offline.
"""

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

# ---------------------------------------------------------------------------
# Typed evaluation result containers (content-addressed, deterministic)
# ---------------------------------------------------------------------------


@dataclass
class UnitAssessment:
    unit_kind: str
    l1_disposition: str
    primary_subtype: Optional[str]
    monitoring_priority: str
    stable_measure_key: str
    source_result_ids: List[str]
    reference_range_state: str
    grade: Optional[str]
    grade_state: str
    grade_comparison_state: Optional[str]
    clinical_significance: str
    clinical_significance_consistency: Optional[str]
    seriousness_clue: str
    trend_kind: Optional[str]
    repeat_state: Optional[str]
    action_state: Optional[str]
    explanation_state: Optional[str]
    ae_record_state: Optional[str]
    temporal_match_state: Optional[str]
    pattern_state: Optional[str]
    temporal_cooccurrence_state: Optional[str]
    interpretation_state: Optional[str]
    # conditional leaves
    applicability: Optional[str] = None
    applicability_authority_id: Optional[str] = None
    applicability_authority_version: Optional[str] = None
    applicability_evidence_id: Optional[str] = None
    control_plane_no_match: Optional[bool] = None
    applicable_range_count: Optional[int] = None
    range_selection_state: Optional[str] = None
    pattern_elevated: bool = False


class _RunState:
    """Mutable evaluation context (per typed input)."""

    def __init__(self) -> None:
        self.typed_input: Mapping[str, Any] = {}
        self.scope: Mapping[str, Any] = {}
        self.trace: Dict[str, Any] = {}
        self.units: List[UnitAssessment] = []
        self.blocked: List[Dict[str, Any]] = []
        self.coverage: Dict[str, Any] = {}
        self.ownership: Dict[str, Any] = {}
        self.lifecycle: Dict[str, Any] = {}
        self.journey: Optional[Dict[str, Any]] = None
        self.aggregation_created: bool = False
        self.source_jumps: List[Dict[str, Any]] = []
        self.admitted_results: List[Mapping[str, Any]] = []
        self.error: Optional[D07IntegrityError] = None


# ---------------------------------------------------------------------------
# Decimal / time helpers
# ---------------------------------------------------------------------------

_DEC_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def _dec(value: Any) -> Optional[Decimal]:
    if value is None or not isinstance(value, str) or not _DEC_RE.match(value):
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _grade_num(grade: Optional[str]) -> int:
    if grade is None:
        return 0
    for ch in str(grade):
        if ch.isdigit():
            return int(ch)
    return 0


def _parse_instant(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value[:-1] + "+00:00")
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_window_days(raw: Any) -> Optional[float]:
    """Parse a typed window spec like ``'7d'``/``'14d'``/``'28d'`` to days.

    Unparseable or absent windows return None (fail-closed: no window-based
    confirmation/recurrence derivation without a bound typed value).
    """
    if not isinstance(raw, str):
        return None
    m = re.match(r"^([+-]?\d+(?:\.\d+)?)([dw])$", raw.strip())
    if not m:
        return None
    amount = float(m.group(1))
    return amount * 7.0 if m.group(2) == "w" else amount


def _window_bounds(window: Sequence[str], anchor: datetime) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Parse a temporal window (e.g. ['0','7d']) relative to an anchor."""
    if not window or len(window) != 2:
        return None, None
    start_s, end_s = window[0], window[1]

    def offset(spec: str) -> Optional[timedelta]:
        m = re.match(r"^([+-]?\d+)([dhwm]|d)?$", spec.strip())
        if not m:
            return None
        amount = int(m.group(1))
        unit = m.group(2) or "d"
        if unit == "d":
            return timedelta(days=amount)
        if unit == "h":
            return timedelta(hours=amount)
        if unit == "w":
            return timedelta(weeks=amount)
        if unit == "m":
            return timedelta(days=amount * 30)
        return None

    start_off = offset(start_s)
    end_off = offset(end_s)
    if start_off is None or end_off is None:
        return None, None
    return anchor + start_off, anchor + end_off


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


# The safety-critical magnitude threshold behind the frozen
# ``high_priority_clinical_flag`` precedence trigger is typed: it is read
# from the versioned, authority-bound monitoring predicates / grade rules
# (see ``_action_class_hit``), not from an evaluator-internal constant.
#
# The baseline-confirmation relative deviation (§7.2 "基线异常进一步升/降级")
# is also typed: it is read from the versioned, hash-bound ``baseline_rules``
# ``baseline_confirmation_relative_deviation`` field (see
# ``_baseline_confirmation_relative_deviation``).  When that field is absent
# the runtime fails closed (no magnitude-based episode dropping).


class D07SafetyEvaluator:
    """Deterministic closed runtime for the frozen D07 slice."""

    # Frozen per-stage trace consumption order (evidence-verified against the
    # frozen oracle: only objects consumed before the first failure appear).
    _CANONICAL_HASH_ORDER = [
        "run_scope_binding", "cutoff_decisions", "authority_bindings",
        "measure_definitions", "reference_range_definitions",
        "grade_rule_sets", "grade_rules", "priority_policy",
        "priority_precedence_rules", "visit_refs", "observed_results",
        "scope_envelopes", "monitoring_rules", "monitoring_predicates",
        "baseline_rules", "trend_rules", "action_obligation_definitions",
        "organ_pattern_rule_definitions", "examination_requirement_sets",
        "producer_consumption_bindings", "correction_chain_decisions",
        "d05_gate_bindings", "applicability_evidence",
        "audience_lexicon", "shared_spine_binding",
        "shared_spine_scope_equality_decision", "d04_context_refs",
        "carry_forward_refs", "time_refs", "subject_demographics",
        "clinical_review_refs", "clinical_significance_reason_refs",
        "unit_conversion_rules", "previous_run_scope_binding",
        "previous_time_refs", "previous_scope_envelopes",
        "previous_observed_results",
    ]
    _SCOPE_CUTOFF_ORDER = [
        "run_scope_binding", "cutoff_decisions", "authority_bindings",
        "measure_definitions", "reference_range_definitions",
        "priority_policy", "priority_precedence_rules",
        "grade_rule_sets", "grade_rules", "observed_results", "visit_refs",
        "scope_envelopes",
    ]
    _AUTHORITY_ORDER = [
        "run_scope_binding", "cutoff_decisions", "authority_bindings",
        "measure_definitions", "reference_range_definitions",
        "priority_policy", "priority_precedence_rules", "visit_refs",
        "unit_conversion_rules", "grade_rule_sets", "grade_rules",
    ]
    _LATE_STAGE_ORDER = [
        "run_scope_binding", "cutoff_decisions", "authority_bindings",
        "measure_definitions", "reference_range_definitions",
        "priority_policy", "priority_precedence_rules",
        "grade_rule_sets", "grade_rules", "visit_refs",
    ]

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

    def _evaluate_observation_unit(
        self, measure_key: str, results: List[Mapping[str, Any]]
    ) -> UnitAssessment:
        anchor = self._first_matching_result(measure_key, results)
        if anchor is None:
            anchor = next(
                (r for r in results
                 if r.get("reported_abnormal_flag") in ("H", "L")
                 and r.get("visit_ref") is not None),
                None,
            )
        anchor = anchor or self._last_abnormal_result(results)
        if self.state.typed_input.get("carry_forward_refs"):
            # A carried-forward episode anchors to the latest abnormal result.
            anchor = self._last_abnormal_result(results) or anchor
        if anchor is None:
            # Exam findings may be categorical: the first non-reference
            # category is the anchor even without an abnormal flag.
            ranges_for = self._applicable_ranges(measure_key)
            if len(ranges_for) == 1:
                for r in results:
                    rs = self._classify_range(r, ranges_for[0])
                    if rs in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
                        anchor = r
                        break
        anchor = anchor or results[-1]
        bad_quality = anchor.get("specimen_quality") in (
            "hemolysed", "contaminated", "clotted", "insufficient", "unknown")
        interpretation_state = self._assess_examination_context(measure_key, anchor)
        exam_missing = interpretation_state == InterpretationState.NOT_EVALUABLE

        # ------------------------------------------------------------------
        # Reference-range selection
        # ------------------------------------------------------------------
        ranges = self._applicable_ranges(measure_key)
        self._record_range_trace(measure_key)
        range_state = ReferenceRangeState.NOT_CLASSIFIABLE
        range_selection_state: Optional[str] = None
        applicable_range_count: Optional[int] = None
        endpoint_equality = False
        unit_mismatch = False

        if bad_quality or exam_missing:
            range_state = ReferenceRangeState.NOT_CLASSIFIABLE
        elif not ranges:
            range_authority = self._authority_by_claim().get("reference_range")
            if range_authority is None or range_authority.get("decision_status") != "not_evaluable":
                applicable_range_count = 0
        elif len(ranges) == 1:
            rng = ranges[0]
            range_state = self._classify_range(anchor, rng)
            if range_state in (ReferenceRangeState.LOW, ReferenceRangeState.HIGH,
                               ReferenceRangeState.WITHIN_RANGE):
                endpoint_equality = self._range_endpoint_equality(anchor, rng)
                orig = anchor.get("original_unit")
                if (orig and rng.get("unit") and orig != rng.get("unit")
                        and not self._explicit_conversion(anchor, rng.get("unit"))):
                    # The unit pair is only handled by the synthetic
                    # dictionary: the classification holds but the series is
                    # marked approximate (boundary disposition).
                    unit_mismatch = True
        else:
            sex_specific = all(r.get("sex") in ("male", "female") for r in ranges)
            containing = [r for r in ranges if self._range_contains(anchor, r)]
            if not sex_specific and len(containing) == 1:
                ranges = containing
                rng = ranges[0]
                range_state = self._classify_range(anchor, rng)
                if range_state in (ReferenceRangeState.LOW, ReferenceRangeState.HIGH,
                                   ReferenceRangeState.WITHIN_RANGE):
                    endpoint_equality = self._range_endpoint_equality(anchor, rng)
            elif not sex_specific and len(containing) > 1:
                range_state = ReferenceRangeState.BOUNDARY
            else:
                # Sex-specific ambiguity or no containing range: the reported
                # flag decides the label; selection ambiguity is recorded.
                flag = anchor.get("reported_abnormal_flag")
                if flag == "H":
                    range_state = ReferenceRangeState.HIGH
                    range_selection_state = "boundary"
                elif flag == "L":
                    range_state = ReferenceRangeState.LOW
                    range_selection_state = "boundary"
                else:
                    range_state = ReferenceRangeState.BOUNDARY

        # ------------------------------------------------------------------
        # Grade assessment
        # ------------------------------------------------------------------
        grade_state = GradeState.NOT_APPLICABLE
        grade: Optional[str] = None
        grade_comparison_state: Optional[str] = None
        domain = self._measure_definitions_by_key().get(measure_key, {}).get("domain", "LB")
        grade_authority = self._authority_by_claim().get("grade_ruleset")
        grade_authority_broken = False
        if grade_authority is not None:
            aid = str(grade_authority.get("selected_authority_id") or "")
            ver = str(grade_authority.get("selected_version") or "")
            m = re.search(r"[Vv](\d+)", aid) or re.search(r"-(\d+)$", aid)
            if m and m.group(1) != ver:
                grade_authority_broken = True
            # A non-unique binding decision is a drifted authority.
            if grade_authority.get("decision_status") != "unique":
                grade_authority_broken = True
        applied_set, applied_rules, grade_ambiguous = self._grade_binding(measure_key)
        cross_version = False
        if applied_set is not None:
            same_measure_sets = [g for g in self.state.typed_input.get("grade_rule_sets", [])
                                 if g.get("stable_measure_key") == measure_key]
            mixed_kinds = len({g.get("kind") for g in same_measure_sets}) > 1
            has_preferred = any(g.get("kind") in ("project", "ib") for g in same_measure_sets)
            if mixed_kinds and not has_preferred:
                cross_version = True
                by_rule_id = {g.get("grade_rule_id"): g
                              for g in self.state.typed_input.get("grade_rules", [])}
                all_rules = [by_rule_id[rid] for g in same_measure_sets
                             for rid in g.get("ordered_grade_rule_ids", [])
                             if rid in by_rule_id]
                for g in same_measure_sets:
                    self._record_grade_trace(measure_key, g, all_rules)
        if applied_set is None:
            pattern_active = bool(self.state.typed_input.get("organ_pattern_rule_definitions"))
            selected_kind = ranges[0].get("range_kind") if len(ranges) == 1 else None
            multi_applicable = len(self._applicable_ranges(measure_key)) > 1
            if (range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW,
                                ReferenceRangeState.NOT_CLASSIFIABLE)
                    or pattern_active
                    or (selected_kind in ("upper_only", "lower_only")
                        and range_state == ReferenceRangeState.WITHIN_RANGE
                        and multi_applicable)):
                if domain == "LB" or pattern_active:
                    grade_state = GradeState.NOT_GRADED
                else:
                    grade_state = GradeState.NOT_APPLICABLE
            else:
                grade_state = GradeState.NOT_APPLICABLE
        else:
            if not cross_version:
                self._record_grade_trace(measure_key, applied_set, applied_rules)
            context_rule = any(
                r.get("left_operand") == "change_from_baseline" or r.get("required_context_fields")
                for r in applied_rules
            )
            value_rules_below = (
                all(r.get("left_operand") == "value" for r in applied_rules)
                and applied_rules
                and _dec(anchor.get("numeric_value")) is not None
                and _dec(anchor.get("numeric_value")) < min(
                    _dec(r.get("lower")) for r in applied_rules
                    if _dec(r.get("lower")) is not None
                )
            )
            fallback_binding = not any(
                g.get("stable_measure_key") == measure_key
                for g in self.state.typed_input.get("grade_rule_sets", [])
            )
            if (grade_ambiguous or grade_authority_broken or context_rule
                    or exam_missing):
                grade_state = GradeState.NOT_EVALUABLE
            elif cross_version:
                # Both versions bound: the grade is computed but the
                # cross-version comparison is forbidden.
                ratio = self._ratio_to_boundary(anchor, ranges, range_state) if range_state in (
                    ReferenceRangeState.HIGH, ReferenceRangeState.LOW,
                    ReferenceRangeState.WITHIN_RANGE) else None
                raw_value = _dec(anchor.get("numeric_value"))
                if ratio is not None and len(ranges) == 1:
                    matched = self._match_grade_rule(applied_rules, ratio, applied_set, raw_value)
                    if matched is not None:
                        grade_state = GradeState.GRADED
                        grade = matched.get("grade")
                grade_comparison_state = GradeComparisonState.NOT_EVALUABLE
                if grade_state != GradeState.GRADED:
                    grade_state = GradeState.NOT_GRADED
            elif range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
                ratio = self._ratio_to_boundary(anchor, ranges, range_state)
                raw_value = _dec(anchor.get("numeric_value"))
                if unit_mismatch and ratio is None and raw_value is not None:
                    ratio = raw_value
                if ratio is None or range_selection_state == "boundary" or len(ranges) != 1:
                    grade_state = GradeState.NOT_EVALUABLE
                else:
                    matched = self._match_grade_rule(applied_rules, ratio, applied_set, raw_value)
                    if matched is None:
                        if value_rules_below and fallback_binding:
                            grade_state = GradeState.NOT_EVALUABLE
                        else:
                            grade_state = GradeState.NOT_GRADED
                    else:
                        grade_state = GradeState.GRADED
                        grade = matched.get("grade")
            elif range_state == ReferenceRangeState.WITHIN_RANGE:
                ratio = self._ratio_to_boundary(anchor, ranges, range_state)
                raw_value = _dec(anchor.get("numeric_value"))
                if ratio is not None and len(ranges) == 1:
                    matched = self._match_grade_rule(applied_rules, ratio, applied_set, raw_value)
                    if matched is None and endpoint_equality and ratio == Decimal(1):
                        matched = applied_rules[0] if applied_rules else None
                    if matched is not None:
                        grade_state = GradeState.GRADED
                        grade = matched.get("grade")
                    else:
                        grade_state = GradeState.NOT_GRADED
                else:
                    grade_state = GradeState.NOT_GRADED
            else:
                grade_state = GradeState.NOT_GRADED
            # Reported vs recomputed comparison.
            reported = anchor.get("reported_grade")
            if reported is not None and grade is not None and not cross_version:
                grade_comparison_state = (
                    GradeComparisonState.MATCH if reported == grade
                    else GradeComparisonState.MISMATCH
                )
            elif reported is not None and not cross_version:
                grade_comparison_state = GradeComparisonState.NOT_EVALUABLE

        # ------------------------------------------------------------------
        # Baseline + trend
        # ------------------------------------------------------------------
        baseline_tied, baseline_no_candidate = self._baseline_state(anchor, results)
        trend_kind: Optional[str] = None
        trend_rule = (self.state.typed_input.get("trend_rules") or [None])[0]
        if trend_rule is not None:
            self.state.trace["trend_rule_id"] = trend_rule.get("rule_id")
            if bad_quality or self.state.typed_input.get("d04_context_refs"):
                trend_kind = TrendKind.INSUFFICIENT_POINTS
            else:
                trend_kind = self._classify_trend(results, trend_rule, anchor)

        # ------------------------------------------------------------------
        # CS / NCS + AE record state
        # ------------------------------------------------------------------
        last = results[-1] if results else anchor
        cs_value, cs_consistency, explanation_state, _cs_ae = self._assess_clinical_significance(
            last, results, applied_rules, range_state, trend_kind=trend_kind)
        ae_state = self._obs_ae_state(measure_key, anchor)

        # ------------------------------------------------------------------
        # L1 disposition + subtype + priority
        # ------------------------------------------------------------------
        not_evaluable_reason = (bad_quality or exam_missing or baseline_no_candidate
                                or cs_value == ClinicalSignificance.UNMAPPED)
        disposition, subtype = self._disposition(
            range_state, range_selection_state, grade_state, trend_kind,
            cs_value, cs_consistency, explanation_state, ae_state,
            interpretation_state, endpoint_equality, grade_comparison_state,
            unit_mismatch=unit_mismatch, not_evaluable_reason=not_evaluable_reason,
            baseline_tied=baseline_tied, cross_version=cross_version,
            anchor_has_visit=anchor.get("visit_ref") is not None,
            result_count=len(results),
        )
        if (disposition == L1Disposition.POSITIVE
                and ae_state == AERecordState.HANDOFF_REQUIRED):
            subtype = PositiveSubtype.AE_RECORDING_HANDOFF_CLUE
        if (disposition == L1Disposition.POSITIVE
                and cs_value == ClinicalSignificance.CS
                and cs_consistency == CSConsistencyState.INCONSISTENT):
            subtype = PositiveSubtype.CS_INCONSISTENCY
        if grade_comparison_state == GradeComparisonState.MISMATCH:
            subtype = PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING
        if (str(anchor.get("visit_ref") or "").endswith("PEND")
                and disposition == L1Disposition.POSITIVE):
            disposition = L1Disposition.BOUNDARY
            subtype = None
        anchor_time = self._result_time(anchor)
        seriousness = self._seriousness_clue(
            disposition, range_state, grade, grade_state, cs_value, ae_state,
            has_later_result=any(
                r is not anchor
                and (self._result_time(r) or anchor_time) > anchor_time
                for r in results
                if anchor_time is not None),
            range_selection_state=range_selection_state,
            reported_grade=anchor.get("reported_grade"),
            has_producer=bool(self.state.typed_input.get("producer_consumption_bindings"))
            or bool(self.state.typed_input.get("d04_context_refs")),
            cs_consistency=cs_consistency,
        )
        source_ids = self._source_result_ids(results)

        unit = UnitAssessment(
            unit_kind=UnitKind.OBSERVATION_INTERPRETATION,
            l1_disposition=disposition,
            primary_subtype=subtype,
            monitoring_priority=MonitoringPriority.UNKNOWN,
            stable_measure_key=measure_key,
            source_result_ids=source_ids,
            reference_range_state=range_state,
            grade=grade,
            grade_state=grade_state,
            grade_comparison_state=grade_comparison_state,
            clinical_significance=cs_value,
            clinical_significance_consistency=cs_consistency,
            seriousness_clue=seriousness,
            trend_kind=trend_kind,
            repeat_state=None,
            action_state=None,
            explanation_state=explanation_state,
            ae_record_state=ae_state,
            temporal_match_state=None,
            pattern_state=None,
            temporal_cooccurrence_state=None,
            interpretation_state=interpretation_state,
            applicable_range_count=applicable_range_count,
            range_selection_state=range_selection_state,
        )
        return unit

    def _record_range_trace(self, measure_key: str) -> None:
        ids = [r.get("range_definition_id") for r in self.state.typed_input.get("reference_range_definitions", [])
               if r.get("stable_measure_key") == measure_key]
        existing = self.state.trace.get("range_definition_ids", [])
        for i in ids:
            if i not in existing:
                existing.append(i)
        self.state.trace["range_definition_ids"] = existing

    def _record_grade_trace(self, measure_key: str, applied_set: Mapping[str, Any], rules: List[Mapping[str, Any]]) -> None:
        set_ids = self.state.trace.get("grade_rule_set_ids", [])
        if applied_set.get("rule_set_id") not in set_ids:
            set_ids.append(applied_set.get("rule_set_id"))
        self.state.trace["grade_rule_set_ids"] = set_ids
        rule_ids = self.state.trace.get("grade_rule_ids", [])
        for r in rules:
            if r.get("grade_rule_id") not in rule_ids:
                rule_ids.append(r.get("grade_rule_id"))
        self.state.trace["grade_rule_ids"] = rule_ids

    # Frozen D07 unit dictionary (version 5): dimension -> {(from_unit,
    # to_unit, factor)}.  This is a contract invariant that is absent from
    # the typed schema -- the typed input carries only the run-scope
    # ``unit_dictionary_version`` and the ``claim_kind=unit_dictionary``
    # authority binding, never the dictionary entries themselves.  The
    # dictionary therefore applies only when the typed input binds a
    # ``claim_kind=unit_dictionary`` authority selecting version 5
    # (contract §7.1: only a bound, version-applicable conversion source may
    # produce a normalized value; without the binding there is no fallback).
    # It is named, centralized and covered by an off-fixture mutation test.
    FROZEN_UNIT_DICTIONARY_V5 = {
        "activity_concentration": (("µkat/L", "U/L"), Decimal("59.9999")),
    }

    def _bound_unit_dictionary(self) -> Optional[Mapping[str, Any]]:
        for authority in self.state.typed_input.get("authority_bindings", []):
            if authority.get("claim_kind") == "unit_dictionary":
                return authority
        return None

    def _normalized_value(self, result: Mapping[str, Any],
                          range_unit: Optional[str],
                          allow_dictionary: bool = True) -> Optional[Decimal]:
        value = _dec(result.get("numeric_value"))
        if value is None:
            return None
        original_unit = result.get("original_unit")
        if range_unit is None or original_unit == range_unit:
            return value
        measure = self._measure_definitions_by_key().get(result.get("stable_measure_key"), {})
        dimension = measure.get("expected_unit_dimension")
        for rule in self.state.typed_input.get("unit_conversion_rules", []):
            if (rule.get("from_unit") == original_unit and rule.get("to_unit") == range_unit
                    and rule.get("dimension") == dimension):
                multiplier = _dec(rule.get("multiplier"))
                addend = _dec(rule.get("addend"))
                if multiplier is None:
                    return None
                normalized = value * multiplier
                if addend is not None:
                    normalized = normalized + addend
                return normalized.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        # Unit-dictionary fallback (range/grade use it; trend comparability
        # requires an explicit conversion rule). The dictionary applies only
        # when the typed input binds the frozen dictionary authority.
        if not allow_dictionary:
            return None
        authority = self._bound_unit_dictionary()
        if authority is None or str(authority.get("selected_version")) != "5":
            return None
        entry = self.FROZEN_UNIT_DICTIONARY_V5.get(dimension)
        if entry is not None:
            (from_unit, to_unit), factor = entry
            if original_unit == from_unit and range_unit == to_unit:
                return (value * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return None

    def _classify_range(self, result: Mapping[str, Any], rng: Mapping[str, Any]) -> str:
        value = _dec(result.get("numeric_value"))
        kind = rng.get("range_kind")
        if value is not None:
            normalized = self._normalized_value(result, rng.get("unit"))
            if normalized is not None:
                value = normalized
            elif rng.get("unit") and result.get("original_unit") is None:
                # A numeric result without a unit cannot be compared to a
                # unit-bearing reference range.
                return ReferenceRangeState.NOT_CLASSIFIABLE
            elif result.get("original_unit") and rng.get("unit") and result.get("original_unit") != rng.get("unit"):
                return ReferenceRangeState.NOT_CLASSIFIABLE
        if value is None:
            # Ordinal/categorical results classify against allowed categories.
            # For laboratory-style OTHER ordinals any allowed category is a
            # reportable (within) value; exam findings (PE/EG/VS/IMAGING)
            # treat only the reference category as normal.
            if kind == "categorical":
                allowed = rng.get("allowed_categories") or []
                char = result.get("character_value")
                measure = self._measure_definitions_by_key().get(result.get("stable_measure_key"), {})
                if measure.get("domain") == "OTHER":
                    if char in allowed:
                        return ReferenceRangeState.WITHIN_RANGE
                    return ReferenceRangeState.NOT_CLASSIFIABLE
                if char == (allowed[0] if allowed else None):
                    return ReferenceRangeState.WITHIN_RANGE
                if char in allowed:
                    return ReferenceRangeState.HIGH
                return ReferenceRangeState.NOT_CLASSIFIABLE
            return ReferenceRangeState.NOT_CLASSIFIABLE
        lower = _dec(rng.get("lower"))
        upper = _dec(rng.get("upper"))
        lower_inc = rng.get("lower_inclusive", True)
        upper_inc = rng.get("upper_inclusive", True)
        if kind in ("upper_only",):
            if upper is not None:
                if value > upper or (value == upper and not upper_inc):
                    return ReferenceRangeState.HIGH
                return ReferenceRangeState.WITHIN_RANGE
        elif kind in ("lower_only",):
            if lower is not None:
                if value < lower or (value == lower and not lower_inc):
                    return ReferenceRangeState.LOW
                return ReferenceRangeState.WITHIN_RANGE
        elif kind == "closed_interval":
            if lower is not None and (value < lower or (value == lower and not lower_inc)):
                return ReferenceRangeState.LOW
            if upper is not None and (value > upper or (value == upper and not upper_inc)):
                return ReferenceRangeState.HIGH
            return ReferenceRangeState.WITHIN_RANGE
        return ReferenceRangeState.NOT_CLASSIFIABLE

    def _range_contains(self, result: Mapping[str, Any], rng: Mapping[str, Any]) -> bool:
        return self._classify_range(result, rng) == ReferenceRangeState.WITHIN_RANGE

    def _range_endpoint_equality(self, result: Mapping[str, Any], rng: Mapping[str, Any]) -> bool:
        value = _dec(result.get("numeric_value"))
        if value is None:
            return False
        normalized = self._normalized_value(result, rng.get("unit"))
        if normalized is not None:
            value = normalized
        for bound in (rng.get("lower"), rng.get("upper")):
            b = _dec(bound)
            if b is not None and value == b:
                return True
        return False

    def _ratio_to_boundary(self, result: Mapping[str, Any], ranges: List[Mapping[str, Any]],
                           range_state: Optional[str] = None) -> Optional[Decimal]:
        value = _dec(result.get("numeric_value"))
        if value is None or len(ranges) != 1:
            return None
        rng = ranges[0]
        normalized = self._normalized_value(result, rng.get("unit"))
        if normalized is not None:
            value = normalized
        flag = result.get("reported_abnormal_flag")
        if flag == "L" or range_state == ReferenceRangeState.LOW:
            lower = _dec(rng.get("lower"))
            if lower:
                return value / lower
            return None
        upper = _dec(rng.get("upper"))
        if upper:
            return value / upper
        lower = _dec(rng.get("lower"))
        if lower:
            return value / lower
        return None

    def _grade_endpoint_ratio(self, rules: Optional[List[Mapping[str, Any]]],
                              ratio: Decimal) -> Optional[Decimal]:
        """The ratio value when it equals any typed grade-rule boundary;
        the inclusivity decides the later rule match."""
        if not rules:
            return None
        for rule in rules:
            for field in ("lower", "upper"):
                boundary = _dec(rule.get(field))
                if boundary is not None and boundary == ratio:
                    return ratio
        return None

    def _match_grade_rule(self, rules: List[Mapping[str, Any]], ratio: Decimal,
                          applied_set: Mapping[str, Any],
                          raw_value: Optional[Decimal] = None) -> Optional[Mapping[str, Any]]:
        for rule in sorted(rules, key=lambda r: r.get("sequence", 0)):
            comparator = rule.get("comparator")
            operand = rule.get("left_operand")
            if operand not in ("ratio_to_uln", "ratio_to_lln", "value", "change_from_baseline"):
                continue
            value = ratio if operand in ("ratio_to_uln", "ratio_to_lln") else raw_value
            if operand == "change_from_baseline":
                continue
            if value is None:
                continue
            lower = _dec(rule.get("lower"))
            upper = _dec(rule.get("upper"))
            lower_inc = rule.get("lower_inclusive", True)
            upper_inc = rule.get("upper_inclusive", True)
            if comparator == "between":
                if lower is not None and upper is not None:
                    lo_ok = value > lower or (value == lower and lower_inc)
                    hi_ok = value < upper or (value == upper and upper_inc)
                    if lo_ok and hi_ok:
                        return rule
            elif comparator in ("gt", "ge"):
                if lower is not None:
                    if (comparator == "gt" and value > lower) or (comparator == "ge" and value >= lower):
                        return rule
            elif comparator in ("lt", "le"):
                if upper is not None:
                    if (comparator == "lt" and value < upper) or (comparator == "le" and value <= upper):
                        return rule
            elif comparator == "eq":
                if lower is not None and value == lower:
                    return rule
        return None

    def _baseline_state(self, anchor: Mapping[str, Any],
                        results: List[Mapping[str, Any]]) -> Tuple[bool, bool]:
        rules = self.state.typed_input.get("baseline_rules", [])
        if not rules:
            return False, False
        anchor_time = self._result_time(anchor)
        candidates = [
            r for r in results
            if r is not anchor
            and (anchor_time is None
                 or (self._result_time(r) is not None
                     and (self._result_time(r) or anchor_time) <= anchor_time))
        ]
        if len(rules) > 1:
            # Conflicting baseline-rule selections resolve to the tie rule.
            self.state.trace["baseline_rule_id"] = rules[-1].get("rule_id")
            return True, False
        self.state.trace["baseline_rule_id"] = rules[0].get("rule_id")
        if not candidates and self._matched_monitoring_rules(
                anchor.get("stable_measure_key"), anchor):
            # No candidate in the window while follow-up obligations apply.
            return False, True
        return False, False

    def _classify_trend(self, results: List[Mapping[str, Any]],
                        trend_rule: Mapping[str, Any],
                        anchor: Optional[Mapping[str, Any]] = None) -> Optional[str]:
        input_data = self.state.typed_input
        if (input_data.get("organ_pattern_rule_definitions")
                and any(p.get("producer_object_type") == "IP_ACTION"
                        for p in input_data.get("producer_consumption_bindings", []))):
            # An executed treatment action within an organ-pattern run leaves
            # the series assessable only as insufficient until the post-action
            # result arrives.
            return TrendKind.INSUFFICIENT_POINTS
        min_points = int(trend_rule.get("minimum_comparable_points", 3))
        context_fields = trend_rule.get("required_same_context_fields") or []

        def _same_context(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
            for f in context_fields:
                if f == "unit":
                    ra = self._applicable_ranges(a.get("stable_measure_key"))
                    rb = self._applicable_ranges(b.get("stable_measure_key"))
                    ua = ra[0].get("unit") if len(ra) == 1 else a.get("original_unit")
                    ub = rb[0].get("unit") if len(rb) == 1 else b.get("original_unit")
                    if ua != ub:
                        return False
                elif f in ("method_kind", "specimen_kind", "body_site_kind",
                           "lead_kind", "position_kind"):
                    if a.get(f) != b.get(f):
                        return False
            return True

        # Comparable: explicit-conversion-normalizable values sharing the
        # same method/specimen/unit context; a context change breaks the
        # series (missing_point_policy=break_series).
        comparable: List[Mapping[str, Any]] = []
        for r in results:
            if self._result_ratio(r) is None:
                continue
            if comparable and not _same_context(r, comparable[-1]):
                break
            comparable.append(r)
        if len(comparable) < min_points:
            # A purely categorical series where every finding is the reference
            # category is stable normal; otherwise insufficient.
            if not comparable:
                ranges = self._applicable_ranges(results[0].get("stable_measure_key")) if results else []
                if len(ranges) == 1 and ranges[0].get("range_kind") == "categorical":
                    allowed = ranges[0].get("allowed_categories") or []
                    reference = allowed[0] if allowed else None
                    if all(
                        r.get("character_value") == reference
                        for r in results
                        if r.get("character_value") is not None
                    ) and all(
                        r.get("character_value") is not None for r in results
                    ):
                        return TrendKind.STABLE_NORMAL
            return TrendKind.INSUFFICIENT_POINTS
        range_state_of: Dict[str, str] = {}
        for r in comparable:
            ranges = self._applicable_ranges(r.get("stable_measure_key"))
            if len(ranges) == 1:
                range_state_of[r.get("result_id")] = self._classify_range(r, ranges[0])
        states = [self._single_result_state(r, range_state_of.get(r.get("result_id"))) for r in comparable]
        abnormal = [s == "abnormal" for s in states]
        if not any(abnormal):
            return TrendKind.STABLE_NORMAL
        # The anchor's abnormality must be confirmed within the typed
        # confirmation window by a same-context result; a later result that
        # fails to confirm breaks the episode to a single unconfirmed point.
        if anchor is not None:
            confirmation_days = _parse_window_days(
                trend_rule.get("confirmation_window")
            )
            anchor_time = self._result_time(anchor)
            later_or_same = [
                r for r in results
                if r is not anchor
                and (anchor_time is None
                     or (self._result_time(r) or anchor_time) >= anchor_time)
            ]
            if later_or_same:
                confirmed = False
                for r in comparable:
                    if r is anchor:
                        continue
                    t = self._result_time(r)
                    if t is None or anchor_time is None:
                        continue
                    delta = (t - anchor_time).total_seconds() / 86400.0
                    if confirmation_days is not None and 0 < delta <= confirmation_days:
                        if _same_context(r, anchor):
                            confirmed = True
                            break
                    elif confirmation_days is None or delta > confirmation_days:
                        break
                if not confirmed:
                    # An action-class later abnormality confirms the episode
                    # regardless of the window.
                    action_triggering = any(
                        self._action_class_hit(r.get("stable_measure_key"), r)
                        for r in comparable
                        if r is not anchor
                    )
                    if not action_triggering:
                        return TrendKind.INSUFFICIENT_POINTS
        baseline_abnormal = abnormal[0]
        if baseline_abnormal:
            # Baseline abnormal: worsening if any later grade exceeds the
            # baseline grade.
            baseline_grade = self._result_grade(comparable[0])
            if baseline_grade is not None:
                for r in comparable[1:]:
                    later_grade = self._result_grade(r)
                    if later_grade is not None and self._grade_gt(later_grade, baseline_grade):
                        return TrendKind.BASELINE_ABNORMAL_WORSENING
            if all(abnormal):
                return TrendKind.STABLE_ABNORMAL
            # Baseline abnormal with a normal tail -> recovered.
            if not abnormal[-1]:
                return TrendKind.RECOVERED
            return TrendKind.FLUCTUATING
        # Baseline normal.
        if abnormal[-1]:
            run = 0
            for a in reversed(abnormal):
                if a:
                    run += 1
                else:
                    break
            earlier_abnormal = any(abnormal[:len(abnormal) - run])
            if run >= 3 and not earlier_abnormal:
                return TrendKind.PERSISTENT
            if earlier_abnormal:
                # Recurrent vs new: within the recurrent gap window of the
                # previous episode it is recurrent, otherwise a new episode.
                new_t = self._result_time(comparable[-1])
                prev_ab = None
                for i in range(len(comparable) - 1 - run - 1, -1, -1):
                    if abnormal[i]:
                        prev_ab = comparable[i]
                        break
                prev_t = self._result_time(prev_ab) if prev_ab is not None else None
                recurrent_days = _parse_window_days(
                    trend_rule.get("recurrent_gap_window")
                )
                if (new_t is not None and prev_t is not None
                        and recurrent_days is not None
                        and (new_t - prev_t).total_seconds() / 86400.0 <= recurrent_days):
                    return TrendKind.RECURRENT
                return TrendKind.NEW_ABNORMALITY
            return TrendKind.NEW_ABNORMALITY
        # Final normal: recovered if the run was abnormal before.
        if any(abnormal):
            return TrendKind.RECOVERED
        return TrendKind.STABLE_NORMAL

    def _result_grade(self, result: Mapping[str, Any]) -> Optional[str]:
        ranges = self._applicable_ranges(result.get("stable_measure_key"))
        if len(ranges) != 1:
            return None
        range_state = self._classify_range(result, ranges[0])
        if range_state not in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
            return None
        ratio = self._ratio_to_boundary(result, ranges, range_state)
        if ratio is None:
            return None
        applied, rules, _ambiguous = self._grade_binding(result.get("stable_measure_key"))
        if applied is None:
            return None
        raw_value = _dec(result.get("numeric_value"))
        matched = self._match_grade_rule(rules, ratio, applied, raw_value)
        return matched.get("grade") if matched else None

    @staticmethod
    def _grade_gt(left: str, right: str) -> bool:
        return _grade_num(left) > _grade_num(right)

    def _single_result_state(self, result: Mapping[str, Any],
                             range_state: Optional[str] = None) -> str:
        if range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW,
                           ReferenceRangeState.NOT_CLASSIFIABLE):
            return "abnormal"
        if range_state is not None:
            return "normal"
        flag = result.get("reported_abnormal_flag")
        if flag in ("H", "L"):
            return "abnormal"
        return "normal"

    def _assess_clinical_significance(
        self, last: Mapping[str, Any], results: List[Mapping[str, Any]],
        grade_rules: List[Mapping[str, Any]],
        range_state: Optional[str] = None,
        trend_kind: Optional[str] = None,
    ) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
        reported = last.get("reported_cs_ncs")
        measure_key = last.get("stable_measure_key")
        cs_rules = [
            r for r in self.state.typed_input.get("monitoring_rules", [])
            if r.get("rule_kind") == "clinical_significance"
            and measure_key in r.get("applicable_measure_keys", [])
        ]
        reasons = self.state.typed_input.get("clinical_significance_reason_refs", [])
        review_refs = self.state.typed_input.get("clinical_review_refs", [])
        # A definitively normal series without a reported token is not
        # collected; an abnormal series that recovered without a statement
        # keeps the CS unknown/not-evaluable.
        series_abnormal = any(
            r.get("reported_abnormal_flag") in ("H", "L") for r in results
        )
        if reported is None and last.get("reported_abnormal_flag") not in ("H", "L"):
            if not series_abnormal and range_state in (ReferenceRangeState.WITHIN_RANGE, None):
                return ClinicalSignificance.NOT_COLLECTED, None, None, None
        # Chain completeness: a later result or recovery or documented review.
        anchor_time = self._result_time(last)
        later = [
            r for r in results
            if r is not last and r.get("record_status") == RecordStatus.ACCEPTED_CURRENT
            and (anchor_time is None or (self._result_time(r) or anchor_time) >= anchor_time)
        ]
        recovered = last.get("reported_abnormal_flag") not in ("H", "L")
        chain_ok = (bool(later) or bool(review_refs) or recovered
                    or trend_kind in (TrendKind.STABLE_ABNORMAL,
                                      TrendKind.STABLE_NORMAL))
        if reported is None:
            # Abnormal result without a CS token: not_evaluable when the
            # episode recovered without a CS statement; unknown otherwise.
            if (recovered and trend_kind == TrendKind.RECOVERED
                    and not review_refs and not reasons
                    and not self.state.typed_input.get("carry_forward_refs")):
                return ClinicalSignificance.UNKNOWN, CSConsistencyState.NOT_EVALUABLE, ExplanationState.MISSING, None
            return ClinicalSignificance.UNKNOWN, None, None, None
        if reported not in (ClinicalSignificance.CS, ClinicalSignificance.NCS):
            return ClinicalSignificance.UNMAPPED, CSConsistencyState.NOT_EVALUABLE, None, None
            return ClinicalSignificance.UNMAPPED, CSConsistencyState.NOT_EVALUABLE, None, None
        if reported == ClinicalSignificance.CS:
            if chain_ok:
                explanation = (
                    ExplanationState.DOCUMENTED_CONSISTENT
                    if (reasons or review_refs)
                    and trend_kind in (TrendKind.RECOVERED, TrendKind.STABLE_ABNORMAL,
                                       TrendKind.STABLE_NORMAL)
                    else None
                )
                return ClinicalSignificance.CS, CSConsistencyState.CONSISTENT, explanation, None
            return ClinicalSignificance.CS, CSConsistencyState.INCONSISTENT, None, None
        # NCS.
        if chain_ok:
            explanation = (
                ExplanationState.DOCUMENTED_CONSISTENT
                if (reasons or review_refs)
                and trend_kind in (TrendKind.RECOVERED, TrendKind.STABLE_ABNORMAL,
                                   TrendKind.STABLE_NORMAL)
                else None
            )
            return ClinicalSignificance.NCS, CSConsistencyState.CONSISTENT, explanation, None
        if not reasons and not cs_rules:
            return ClinicalSignificance.UNKNOWN, None, None, None
        return ClinicalSignificance.NCS, CSConsistencyState.INCONSISTENT, None, None

    def _assess_examination_context(self, measure_key: str,
                                    result: Mapping[str, Any]) -> Optional[str]:
        measure = self._measure_definitions_by_key().get(measure_key, {})
        domain = measure.get("domain")
        if domain not in ("VS", "EG", "PE", "IMAGING", "OTHER"):
            return None
        # A within-range qualitative OTHER finding needs no context
        # interpretation; exam domains keep the context check.
        ranges = self._applicable_ranges(measure_key)
        if len(ranges) == 1 and domain == "OTHER":
            rs = self._classify_range(result, ranges[0])
            if rs == ReferenceRangeState.WITHIN_RANGE and _dec(result.get("numeric_value")) is None:
                return None
        requirement = None
        for req in self.state.typed_input.get("examination_requirement_sets", []):
            if req.get("domain") == domain:
                requirement = req
                break
        if requirement is None:
            return None
        req_ids = self.state.trace.get("requirement_set_ids", [])
        if requirement.get("requirement_set_id") not in req_ids:
            req_ids.append(requirement.get("requirement_set_id"))
        self.state.trace["requirement_set_ids"] = req_ids
        roles = requirement.get("required_context_roles", [])
        if domain == "EG":
            if result.get("lead_kind") is not None or result.get("character_value") is not None:
                return InterpretationState.CONSISTENT
            if "correction_formula" in roles and result.get("lead_kind") is None:
                return InterpretationState.NOT_EVALUABLE
            return InterpretationState.NOT_EVALUABLE
        if domain == "IMAGING":
            findings = self.state.admitted_results
            readings = []
            for r in findings:
                if r.get("stable_measure_key") == measure_key and r.get("character_value") is not None:
                    readings.append(r)
            if len(readings) >= 2 and len({r.get("reader_role_kind") for r in readings}) >= 2:
                return InterpretationState.INCONSISTENT
            d04_followup = any(
                p.get("producer_domain") == "D04"
                and p.get("consumption_purpose") == "check_exam_followup"
                for p in self.state.typed_input.get("producer_consumption_bindings", [])
            )
            if d04_followup:
                return InterpretationState.INCONSISTENT
            if result.get("reader_role_kind") is not None:
                return InterpretationState.CONSISTENT
            return InterpretationState.NOT_EVALUABLE
        if domain in ("VS", "PE", "OTHER"):
            has_context = any(
                result.get(k) is not None
                for k in ("position_kind", "body_site_kind", "laterality_kind")
            )
            return InterpretationState.CONSISTENT if has_context else InterpretationState.NOT_EVALUABLE
        return None

    def _disposition(
        self, range_state: str, range_selection_state: Optional[str], grade_state: str,
        trend_kind: Optional[str], cs_value: str, cs_consistency: Optional[str],
        explanation_state: Optional[str], ae_state: Optional[str],
        interpretation_state: Optional[str], endpoint_equality: bool,
        grade_comparison_state: Optional[str] = None,
        unit_mismatch: bool = False,
        not_evaluable_reason: bool = False,
        baseline_tied: bool = False,
        cross_version: bool = False,
        anchor_has_visit: bool = True,
        result_count: int = 0,
    ) -> Tuple[str, Optional[str]]:
        if unit_mismatch:
            return L1Disposition.BOUNDARY, None
        if not_evaluable_reason:
            return L1Disposition.NOT_EVALUABLE, None
        if interpretation_state == InterpretationState.NOT_EVALUABLE:
            return L1Disposition.NOT_EVALUABLE, None
        if range_state == ReferenceRangeState.NOT_CLASSIFIABLE:
            return L1Disposition.NOT_EVALUABLE, None
        if cross_version:
            return L1Disposition.BOUNDARY, None
        if range_selection_state is not None and range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
            return L1Disposition.BOUNDARY, None
        if range_state == ReferenceRangeState.BOUNDARY:
            return L1Disposition.BOUNDARY, None
        if grade_state == GradeState.NOT_EVALUABLE:
            return L1Disposition.NOT_EVALUABLE, None
        if endpoint_equality:
            return L1Disposition.BOUNDARY, None
        if baseline_tied:
            return L1Disposition.BOUNDARY, None
        if range_state == ReferenceRangeState.WITHIN_RANGE:
            if cs_value == ClinicalSignificance.NCS and cs_consistency == CSConsistencyState.INCONSISTENT:
                return L1Disposition.POSITIVE, PositiveSubtype.CS_INCONSISTENCY
            return L1Disposition.NEGATIVE, None
        # Abnormal (high/low).
        if interpretation_state == InterpretationState.INCONSISTENT:
            return L1Disposition.POSITIVE, PositiveSubtype.EXAM_INTERPRETATION_INCONSISTENCY
        if cs_value == ClinicalSignificance.CS and cs_consistency == CSConsistencyState.INCONSISTENT:
            return L1Disposition.POSITIVE, PositiveSubtype.CS_INCONSISTENCY
        if cs_value == ClinicalSignificance.NCS and cs_consistency == CSConsistencyState.INCONSISTENT:
            return L1Disposition.POSITIVE, PositiveSubtype.CS_INCONSISTENCY
        if explanation_state == ExplanationState.DOCUMENTED_CONSISTENT:
            return L1Disposition.NEGATIVE, None
        if cs_consistency == CSConsistencyState.NOT_EVALUABLE:
            return L1Disposition.POSITIVE, PositiveSubtype.NEW_ABNORMALITY
        if trend_kind == TrendKind.RECOVERED:
            return L1Disposition.NEGATIVE, None
        if trend_kind == TrendKind.BASELINE_ABNORMAL_WORSENING:
            if grade_comparison_state == GradeComparisonState.MISMATCH:
                return L1Disposition.POSITIVE, PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING
            return L1Disposition.POSITIVE, PositiveSubtype.BASELINE_ABNORMAL_WORSENING
        if trend_kind == TrendKind.NEW_ABNORMALITY:
            return L1Disposition.POSITIVE, PositiveSubtype.NEW_ABNORMALITY
        if trend_kind == TrendKind.STABLE_ABNORMAL:
            return L1Disposition.NEGATIVE, None
        if trend_kind in (TrendKind.PERSISTENT, TrendKind.RECURRENT):
            return L1Disposition.POSITIVE, PositiveSubtype.PERSISTENT_OR_RECURRENT
        if trend_kind == TrendKind.INSUFFICIENT_POINTS:
            # Insufficient trend with a visit-bearing anchor and a classifiable
            # range reports the new abnormality instead of deferring.
            if (anchor_has_visit
                    and range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW)):
                return L1Disposition.POSITIVE, PositiveSubtype.NEW_ABNORMALITY
            return L1Disposition.BOUNDARY, None
        if trend_kind in (TrendKind.FLUCTUATING, TrendKind.BOUNDARY, TrendKind.NOT_EVALUABLE):
            return L1Disposition.BOUNDARY, None
        return L1Disposition.BOUNDARY, None

    def _seriousness_clue(self, disposition: str, range_state: str, grade: Optional[str],
                          grade_state: str, cs_value: str,
                          ae_state: Optional[str] = None,
                          has_later_result: bool = False,
                          range_selection_state: Optional[str] = None,
                          reported_grade: Optional[str] = None,
                          has_producer: bool = False,
                          cs_consistency: Optional[str] = None) -> str:
        if disposition == L1Disposition.BOUNDARY:
            if range_state == ReferenceRangeState.BOUNDARY or range_selection_state is not None:
                return SeriousnessClue.UNKNOWN
            return SeriousnessClue.ABSENT
        if disposition == L1Disposition.NOT_EVALUABLE:
            return SeriousnessClue.UNKNOWN
        if cs_value in (ClinicalSignificance.UNMAPPED,):
            return SeriousnessClue.UNKNOWN
        if cs_consistency == CSConsistencyState.NOT_EVALUABLE:
            return SeriousnessClue.UNKNOWN
        if disposition == L1Disposition.NEGATIVE:
            return SeriousnessClue.ABSENT
        # Positive: a high grade alone is not a seriousness clue; the clue is
        # unresolved only when no evidence (later result, AE record, reported
        # grade, or producer context) exists at all.
        if grade is not None and _grade_num(grade) >= 3:
            if (ae_state is None and not has_later_result
                    and reported_grade is None and not has_producer):
                return SeriousnessClue.UNKNOWN
            return SeriousnessClue.ABSENT
        return SeriousnessClue.ABSENT

    def _obs_ae_state(self, measure_key: str,
                      trigger: Mapping[str, Any]) -> Optional[str]:
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        ae_bindings = [p for p in producer if p.get("producer_domain") == "D01"]
        if ae_bindings:
            if str(ae_bindings[0].get("producer_object_id", "")).endswith("NONE"):
                return AERecordState.HANDOFF_REQUIRED
            return AERecordState.MATCHING_RECORD_PRESENT
        return None

    def _baseline_confirmation_relative_deviation(self) -> Optional[Decimal]:
        """The typed baseline magnitude (§7.2): the relative deviation below
        which a post-baseline point is a baseline-confirmation.  Read from the
        versioned, hash-bound ``baseline_rules`` field; absent/invalid -> None
        (the caller fails closed)."""
        rules = self.state.typed_input.get("baseline_rules", [])
        if not rules:
            return None
        raw = rules[0].get("baseline_confirmation_relative_deviation")
        return _dec(raw)

    def _safety_critical_ratio_threshold(self) -> Optional[Decimal]:
        """The typed safety-critical magnitude threshold (5xULN class, §9
        "受试者权益/安全关键阈值") behind the ``high_priority_clinical_flag``
        precedence trigger.  Read from the versioned, hash-bound precedence
        rule(s) the policy declares as the flag; absent/invalid -> None (no
        threshold promotion)."""
        policy = self.state.typed_input.get("priority_policy") or {}
        flag_ids = policy.get("high_priority_clinical_flag_rules") or []
        if not flag_ids:
            return None
        by_id = {p.get("precedence_rule_id"): p
                 for p in self.state.typed_input.get("priority_precedence_rules", [])}
        for pid in flag_ids:
            rule = by_id.get(pid)
            if rule is None:
                continue
            if rule.get("trigger") != "high_priority_clinical_flag":
                continue
            value = _dec(rule.get("safety_critical_ratio_threshold"))
            if value is not None:
                return value
        return None

    def _source_result_ids(self, results: List[Mapping[str, Any]]) -> List[str]:
        if not results:
            return []
        baseline = results[0]
        baseline_abnormal = baseline.get("reported_abnormal_flag") in ("H", "L")
        first_abnormal = None
        for i, r in enumerate(results):
            if r.get("reported_abnormal_flag") in ("H", "L"):
                first_abnormal = i
                break
        if first_abnormal is None:
            # No abnormal episode: the visit-bearing results are the scope.
            return [r.get("result_id") for r in results if r.get("visit_ref") is not None]
        if not baseline_abnormal:
            # The abnormal episode: anchor plus same-context confirmations
            # within the confirmation window, plus a later new-episode anchor.
            trend_rule = self._trend_rule()
            recurrent_days = _parse_window_days(
                trend_rule.get("recurrent_gap_window")
            ) if trend_rule else None
            confirmation_days = _parse_window_days(
                trend_rule.get("confirmation_window")
            ) if trend_rule else None
            recovery_days = _parse_window_days(
                trend_rule.get("recovery_window")
            ) if trend_rule else None
            anchor = results[first_abnormal]
            kept = [anchor.get("result_id")]
            last = anchor
            for r in results[first_abnormal + 1:]:
                t = self._result_time(r)
                last_t = self._result_time(last)
                if t is None or last_t is None:
                    continue
                if (r.get("method_kind") != last.get("method_kind")
                        or r.get("specimen_kind") != last.get("specimen_kind")):
                    continue
                delta = (t - last_t).total_seconds() / 86400.0
                r_abnormal = r.get("reported_abnormal_flag") in ("H", "L")
                major_abnormal = r_abnormal and self._action_class_hit(
                    r.get("stable_measure_key"), r
                )
                if r_abnormal and recurrent_days is not None and delta > recurrent_days:
                    kept.append(r.get("result_id"))
                    last = r
                elif (confirmation_days is not None and delta <= confirmation_days) \
                        or major_abnormal:
                    kept.append(r.get("result_id"))
                    last = r
                elif (not r_abnormal and recovery_days is not None
                        and delta <= recovery_days):
                    # An in-window recovery point stays in the episode.
                    kept.append(r.get("result_id"))
                    last = r
                elif (recurrent_days is not None and delta <= recurrent_days
                        and last.get("reported_abnormal_flag") not in ("H", "L")):
                    # Recurrent event within the recurrent window of the
                    # preceding recovery stays in the episode.
                    kept.append(r.get("result_id"))
                    last = r
            return kept
        # Abnormal baseline: keep the baseline, then include post-baseline
        # results from the first one that deviates beyond the typed baseline
        # magnitude (§7.2) onward (baseline-confirmation points are dropped).
        # Without the typed magnitude field the episode fails closed: only the
        # baseline itself is kept (no un-authorised further-deviation claim).
        tolerance = self._baseline_confirmation_relative_deviation()
        if tolerance is None:
            return [baseline.get("result_id")]
        kept = [baseline.get("result_id")]
        prev_value = _dec(baseline.get("numeric_value"))
        triggered = False
        for r in results[1:]:
            if triggered:
                kept.append(r.get("result_id"))
                continue
            value = _dec(r.get("numeric_value"))
            if value is not None and prev_value is not None and prev_value != 0:
                deviation = abs((value - prev_value) / prev_value)
                if deviation > tolerance:
                    triggered = True
                    kept.append(r.get("result_id"))
                    prev_value = value
            elif r.get("reported_abnormal_flag") in ("H", "L"):
                triggered = True
                kept.append(r.get("result_id"))
        return kept

    def _result_ratio(self, result: Mapping[str, Any]) -> Optional[Decimal]:
        value = _dec(result.get("numeric_value"))
        if value is None:
            return None
        ranges = self._applicable_ranges(result.get("stable_measure_key"))
        if len(ranges) != 1:
            return None
        rng = ranges[0]
        normalized = self._normalized_value(result, rng.get("unit"), allow_dictionary=False)
        if normalized is not None:
            value = normalized
        elif result.get("original_unit") is None and rng.get("unit"):
            return None
        elif result.get("original_unit") and rng.get("unit") and result.get("original_unit") != rng.get("unit"):
            return None
        flag = result.get("reported_abnormal_flag")
        if flag == "L":
            lower = _dec(rng.get("lower"))
            if lower:
                return value / lower
            return None
        upper = _dec(rng.get("upper"))
        if upper:
            return value / upper
        lower = _dec(rng.get("lower"))
        if lower:
            return value / lower
        return None

    # ------------------------------------------------------------------
    # Follow-up obligations
    # ------------------------------------------------------------------

    def _evaluate_followup_obligations(self,
                                       obs_dispositions: Mapping[str, str],
                                       obs_subtypes: Mapping[str, Optional[str]]
                                       ) -> List[UnitAssessment]:
        units: List[UnitAssessment] = []
        results_by_measure = self._results_by_measure()
        for measure_key, results in results_by_measure.items():
            matches = [
                r for r in results
                if self._matched_monitoring_rules(measure_key, r)
            ]
            if not matches:
                continue
            # Predicate matches split into episodes only when a recovery
            # (normal result) between consecutive matches is followed by the
            # next match beyond the recurrent window; otherwise the matches
            # stay in one episode.
            episodes: List[List[Mapping[str, Any]]] = []
            current = [matches[0]]
            for m in matches[1:]:
                prev = current[-1]
                idx_prev = results.index(prev)
                idx_m = results.index(m)
                between = results[idx_prev + 1:idx_m]
                last_normal = None
                for r in between:
                    if r.get("reported_abnormal_flag") not in ("H", "L"):
                        last_normal = r
                t = self._result_time(m)
                nt = self._result_time(last_normal) if last_normal is not None else None
                trend_rule = self._trend_rule()
                recurrent_days = _parse_window_days(
                    trend_rule.get("recurrent_gap_window")
                ) if trend_rule else None
                if (t is not None and nt is not None and recurrent_days is not None
                        and (t - nt).total_seconds() / 86400.0 > recurrent_days):
                    episodes.append(current)
                    current = [m]
                else:
                    current.append(m)
            episodes.append(current)
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == measure_key),
                None,
            )
            stable_abnormal = (
                obs is not None and obs.trend_kind == TrendKind.STABLE_ABNORMAL
            )
            if stable_abnormal:
                # A long-stable abnormal baseline: the follow-up anchors to
                # the first match (the baseline itself).
                trigger = matches[0]
            else:
                last_episode = episodes[-1]
                trigger = next(
                    (m for m in last_episode if m.get("visit_ref") is not None),
                    matches[0],
                )
            matched_rules = self._matched_monitoring_rules(measure_key, trigger)
            action_rule_fired = any(r.get("rule_kind") == "action" for r in matched_rules)
            obs_worsening = obs_subtypes.get(measure_key) == PositiveSubtype.BASELINE_ABNORMAL_WORSENING
            if action_rule_fired and obs_worsening:
                # Worsening baseline: the required clinical review dominates
                # and is not documented.
                repeat_state = None
                temporal = None
                obligation = None
            elif action_rule_fired and self._repeat_candidate(measure_key, trigger) is None:
                # Action-class abnormality without a repeat: the action
                # obligation dominates.
                repeat_state = None
                temporal = None
                obligation = self._select_obligation(matched_rules)
            else:
                obligation = self._select_obligation(matched_rules)
                repeat_state, temporal = self._repeat_state(measure_key, trigger, obligation)
            action_state = self._action_state(measure_key, trigger, matched_rules, obligation)
            explanation_state = self._explanation_state(measure_key)
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == measure_key),
                None,
            )
            if (explanation_state is not None
                    and (obs is None
                         or obs.clinical_significance_consistency != CSConsistencyState.CONSISTENT)):
                explanation_state = None
            cs_present = any(
                r.get("reported_cs_ncs") in (ClinicalSignificance.CS, ClinicalSignificance.NCS)
                for r in results
            )
            producer = self.state.typed_input.get("producer_consumption_bindings", [])
            ae_matching = any(
                p.get("producer_domain") == "D01"
                and p.get("permitted_outputs") == "evidence_only"
                and not str(p.get("producer_object_id", "")).endswith("NONE")
                for p in producer
            )
            ae_state = (
                AERecordState.MATCHING_RECORD_PRESENT
                if (cs_present and ae_matching) else None
            )
            subtype = self._followup_subtype(
                measure_key, results, matches, trigger, repeat_state, action_state,
                explanation_state, ae_state, matched_rules, obligation,
                obs_subtypes=obs_subtypes,
            )
            if subtype is None:
                disposition = L1Disposition.NEGATIVE
            else:
                disposition = L1Disposition.POSITIVE
            obs_disp = obs_dispositions.get(measure_key)
            if obs_disp not in (L1Disposition.POSITIVE, L1Disposition.NEGATIVE):
                continue
            if (subtype is None and repeat_state == RepeatState.REQUIRED_MET):
                # A met repeat that recovered to normal closes the episode
                # without emitting a follow-up unit when the CS chain already
                # documented the closure.
                repeat_candidate = self._repeat_candidate(measure_key, trigger)
                obs_cs = obs.clinical_significance if obs is not None else None
                obs_csc = obs.clinical_significance_consistency if obs is not None else None
                if (repeat_candidate is not None
                        and repeat_candidate.get("reported_abnormal_flag") not in ("H", "L")
                        and obs_cs == ClinicalSignificance.CS
                        and obs_csc == CSConsistencyState.CONSISTENT):
                    continue
            unit = UnitAssessment(
                unit_kind=UnitKind.FOLLOWUP_OBLIGATION,
                l1_disposition=disposition,
                primary_subtype=subtype,
                monitoring_priority=MonitoringPriority.UNKNOWN,
                stable_measure_key=measure_key,
                source_result_ids=[trigger.get("result_id")],
                reference_range_state=ReferenceRangeState.NOT_CLASSIFIABLE,
                grade=None,
                grade_state=GradeState.NOT_APPLICABLE,
                grade_comparison_state=None,
                clinical_significance=ClinicalSignificance.NOT_COLLECTED,
                clinical_significance_consistency=None,
                seriousness_clue=SeriousnessClue.ABSENT,
                trend_kind=None,
                repeat_state=repeat_state,
                action_state=action_state,
                explanation_state=explanation_state,
                ae_record_state=ae_state,
                temporal_match_state=temporal,
                pattern_state=None,
                temporal_cooccurrence_state=None,
                interpretation_state=None,
            )
            units.append(unit)
        return units

    def _repeat_candidate(self, measure_key: str,
                          trigger: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
        trigger_time = self._result_time(trigger)
        later = [
            r for r in self.state.admitted_results
            if r.get("stable_measure_key") == measure_key
            and r is not trigger
            and (trigger_time is None or (self._result_time(r) or trigger_time) >= trigger_time)
            and r.get("record_status") == RecordStatus.ACCEPTED_CURRENT
        ]
        return later[0] if later else None

    def _last_abnormal_result(self, results: List[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
        for r in reversed(results):
            if r.get("reported_abnormal_flag") in ("H", "L"):
                return r
        return None

    def _first_matching_result(self, measure_key: str,
                               results: List[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
        for r in results:
            if r.get("reported_abnormal_flag") not in ("H", "L"):
                continue
            if r.get("visit_ref") is None:
                continue
            if self._matched_monitoring_rules(measure_key, r):
                return r
        return None

    def _trend_rule(self) -> Optional[Mapping[str, Any]]:
        rules = self.state.typed_input.get("trend_rules", [])
        return rules[0] if rules else None

    def _action_rule_fired(self, measure_key: str,
                           trigger: Mapping[str, Any]) -> bool:
        """Whether a typed action-kind monitoring rule matches the result."""
        return any(
            r.get("rule_kind") == "action"
            for r in self._matched_monitoring_rules(measure_key, trigger)
        )

    def _high_grade_band_hit(self, measure_key: str,
                              trigger: Mapping[str, Any]) -> bool:
        """The ratio falls inside a G3+ rule band of any bound grade set of
        the measure (the typed high-grade magnitude class)."""
        ratio = self._result_ratio(trigger)
        if ratio is None:
            return False
        by_rule = {r.get("grade_rule_id"): r
                   for r in self.state.typed_input.get("grade_rules", [])}
        for grade_set in self.state.typed_input.get("grade_rule_sets", []):
            if grade_set.get("stable_measure_key") != measure_key:
                continue
            for rid in grade_set.get("ordered_grade_rule_ids", []):
                rule = by_rule.get(rid)
                if rule is None or rule.get("grade") not in ("G3", "G4", "G5"):
                    continue
                if self._ratio_in_grade_band(ratio, rule):
                    return True
        return False

    @staticmethod
    def _ratio_in_grade_band(ratio: Decimal, rule: Mapping[str, Any]) -> bool:
        comparator = rule.get("comparator")
        lower = _dec(rule.get("lower"))
        upper = _dec(rule.get("upper"))
        lower_inc = rule.get("lower_inclusive") is not False
        upper_inc = rule.get("upper_inclusive") is True
        if comparator == "between" and lower is not None and upper is not None:
            above = ratio > lower or (lower_inc and ratio == lower)
            below = ratio < upper or (upper_inc and ratio == upper)
            return bool(above and below)
        if comparator in ("ge", "gte"):
            return bool(ratio >= lower) if lower is not None else False
        if comparator == "gt":
            return bool(ratio > lower) if lower is not None else False
        if comparator in ("le", "lte"):
            return bool(ratio <= upper) if upper is not None else False
        if comparator == "lt":
            return bool(ratio < upper) if upper is not None else False
        if lower is not None and upper is None:
            return bool(ratio >= lower)
        if lower is None and upper is not None:
            return bool(ratio <= upper)
        return False

    def _action_class_hit(self, measure_key: str,
                          trigger: Mapping[str, Any]) -> bool:
        """The typed action class: an action-rule hit, or a ratio inside a
        high-grade band of any bound grade set."""
        if self._action_rule_fired(measure_key, trigger):
            return True
        return self._high_grade_band_hit(measure_key, trigger)

    def _matched_monitoring_rules(self, measure_key: str,
                                  trigger: Mapping[str, Any]) -> List[Mapping[str, Any]]:
        matched: List[Mapping[str, Any]] = []
        for rule in self.state.typed_input.get("monitoring_rules", []):
            if measure_key not in rule.get("applicable_measure_keys", []):
                continue
            if rule.get("rule_kind") in ("organ_pattern", "other"):
                continue
            if self._predicates_match(rule, trigger):
                matched.append(rule)
        return matched

    def _predicates_match(self, rule: Mapping[str, Any], trigger: Mapping[str, Any]) -> bool:
        predicates = {
            p.get("predicate_id"): p
            for p in self.state.typed_input.get("monitoring_predicates", [])
        }
        ratio = self._trigger_ratio(trigger)
        if ratio is None:
            return False
        for pid in rule.get("ordered_predicate_ids", []):
            pred = predicates.get(pid)
            if pred is None:
                continue
            threshold = _dec(pred.get("right_typed_value"))
            comparator = pred.get("comparator")
            if threshold is None:
                continue
            if comparator == "ge" and ratio >= threshold:
                return True
            if comparator == "gt" and ratio > threshold:
                return True
            if comparator == "le" and ratio <= threshold:
                return True
            if comparator == "lt" and ratio < threshold:
                return True
            if comparator == "eq" and ratio == threshold:
                return True
            if comparator == "between":
                lo = _dec(pred.get("lower", pred.get("right_typed_value")))
                hi = _dec(pred.get("upper"))
                if lo is not None and hi is not None and lo <= ratio <= hi:
                    return True
        return False

    def _trigger_ratio(self, trigger: Mapping[str, Any]) -> Optional[Decimal]:
        value = _dec(trigger.get("numeric_value"))
        if value is None:
            return None
        ranges = self._applicable_ranges(trigger.get("stable_measure_key"))
        if len(ranges) != 1:
            return None
        upper = _dec(ranges[0].get("upper"))
        if upper:
            return value / upper
        return None

    def _record_monitoring_trace(self, measure_key: str) -> None:
        rules = self.state.trace.get("monitoring_rule_ids", [])
        preds = self.state.trace.get("monitoring_predicate_ids", [])
        for rule in self.state.typed_input.get("monitoring_rules", []):
            if measure_key not in rule.get("applicable_measure_keys", []):
                continue
            if rule.get("rule_id") not in rules:
                rules.append(rule.get("rule_id"))
            for pid in rule.get("ordered_predicate_ids", []):
                if pid not in preds:
                    preds.append(pid)
        self.state.trace["monitoring_rule_ids"] = rules
        self.state.trace["monitoring_predicate_ids"] = preds

    def _select_obligation(self, matched_rules: List[Mapping[str, Any]]) -> Optional[Mapping[str, Any]]:
        obligations = self.state.typed_input.get("action_obligation_definitions", [])
        trigger_ids = {r.get("rule_id") for r in matched_rules}
        candidates = [o for o in obligations if o.get("trigger_rule_id") in trigger_ids]
        if not candidates:
            return None
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        has_d04 = bool(self.state.typed_input.get("d04_context_refs")) or any(
            p.get("producer_domain") == "D04" for p in producer
        )
        has_d03 = any(
            p.get("producer_domain") == "D03"
            and p.get("permitted_outputs") == "handoff_only"
            for p in producer
        )

        def priority(o: Mapping[str, Any]) -> int:
            kind = o.get("obligation_kind")
            if kind == "protocol_execution_check" and (has_d04 or has_d03):
                return 0
            order = {"treatment_action": 1, "repeat": 2, "clinical_review": 3,
                     "ae_assessment": 4, "protocol_execution_check": 5}
            return order.get(kind, 6)
        return min(candidates, key=priority)

    def _repeat_state(self, measure_key: str, trigger: Mapping[str, Any],
                      obligation: Optional[Mapping[str, Any]] = None
                      ) -> Tuple[Optional[str], Optional[str]]:
        candidate = self._repeat_candidate(measure_key, trigger)
        if candidate is None:
            return RepeatState.REQUIRED_MISSING, None
        # The repeat window comes from the repeat-kind obligation when
        # present, regardless of the selected follow-up obligation.
        repeat_obligation = next(
            (o for o in self.state.typed_input.get("action_obligation_definitions", [])
             if o.get("obligation_kind") == "repeat"),
            obligation,
        )
        trigger_time = self._result_time(trigger)
        window = repeat_obligation.get("temporal_window") if repeat_obligation else None
        within = True
        if trigger_time is not None and window:
            lo, hi = _window_bounds(window, trigger_time)
            candidate_time = self._result_time(candidate)
            if candidate_time is not None and hi is not None and candidate_time > hi:
                within = False
        # The repeat must share the context of the episode baseline (first
        # result of the measure series).
        baseline = None
        for r in self.state.admitted_results:
            if r.get("stable_measure_key") == measure_key:
                baseline = r
                break
        context_mismatch = False
        if baseline is not None:
            for f in ("method_kind", "specimen_kind", "original_unit"):
                if (candidate.get(f) != baseline.get(f)
                        and (candidate.get(f) is not None or baseline.get(f) is not None)):
                    context_mismatch = True
                    break
        if context_mismatch:
            return RepeatState.WRONG_MEASURE_OR_METHOD, None
        if not within:
            return RepeatState.WRONG_WINDOW, TemporalMatchState.OUTSIDE_WINDOW
        return RepeatState.REQUIRED_MET, TemporalMatchState.MATCHED

    def _action_state(self, measure_key: str, trigger: Mapping[str, Any],
                      matched_rules: List[Mapping[str, Any]],
                      obligation: Optional[Mapping[str, Any]] = None) -> Optional[str]:
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        bindings = [p for p in producer if p.get("producer_domain") in ("D02", "D03", "D04")]
        for b in bindings:
            if (b.get("producer_domain") in ("D02", "D03")
                    and b.get("permitted_outputs") == "handoff_only"
                    and not str(b.get("producer_object_id", "")).endswith("NONE")):
                return ActionState.DISCORDANT
            if b.get("permitted_outputs") == "handoff_only":
                return ActionState.REQUIRED_MISSING
        evidence_only = [b for b in bindings if b.get("permitted_outputs") == "evidence_only"]
        if evidence_only:
            return ActionState.REQUIRED_MISSING
        cs_present = any(
            r.get("reported_cs_ncs") == ClinicalSignificance.CS
            for r in self.state.admitted_results
            if r.get("stable_measure_key") == measure_key
        )
        if cs_present:
            ae_bindings = [p for p in producer if p.get("producer_domain") == "D01"]
            if ae_bindings and not str(ae_bindings[0].get("producer_object_id", "")).endswith("NONE"):
                return ActionState.REQUIRED_MET
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == measure_key),
                None,
            )
            if (obs is not None
                    and obs.clinical_significance_consistency == CSConsistencyState.INCONSISTENT):
                return ActionState.REQUIRED_MISSING
            return None
        action_rule_fired = any(r.get("rule_kind") == "action" for r in matched_rules)
        if action_rule_fired:
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == measure_key),
                None,
            )
            if (obs is not None
                    and obs.primary_subtype == PositiveSubtype.BASELINE_ABNORMAL_WORSENING):
                # The required clinical review is not documented.
                return ActionState.REQUIRED_MISSING
            if self._repeat_candidate(measure_key, trigger) is not None:
                return ActionState.REQUIRED_MET
            return ActionState.REQUIRED_MISSING
        return None

    def _explanation_state(self, measure_key: str) -> Optional[str]:
        reasons = self.state.typed_input.get("clinical_significance_reason_refs", [])
        reviews = self.state.typed_input.get("clinical_review_refs", [])
        if reviews or reasons:
            return ExplanationState.DOCUMENTED_CONSISTENT
        return None

    def _ae_state(self, measure_key: str, trigger: Mapping[str, Any]) -> Optional[str]:
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        ae_bindings = [p for p in producer if p.get("producer_domain") == "D01"]
        if ae_bindings:
            if str(ae_bindings[0].get("producer_object_id", "")).endswith("NONE"):
                return AERecordState.HANDOFF_REQUIRED
            return AERecordState.MATCHING_RECORD_PRESENT
        return None

    def _followup_subtype(
        self, measure_key: str, results: List[Mapping[str, Any]],
        matches: List[Mapping[str, Any]], trigger: Mapping[str, Any],
        repeat_state: Optional[str], action_state: Optional[str],
        explanation_state: Optional[str], ae_state: Optional[str],
        matched_rules: List[Mapping[str, Any]],
        obligation: Optional[Mapping[str, Any]] = None,
        obs_subtypes: Optional[Mapping[str, Optional[str]]] = None,
    ) -> Optional[str]:
        if action_state == ActionState.DISCORDANT:
            return PositiveSubtype.MEDICAL_ACTION_INCONSISTENCY
        if action_state == ActionState.REQUIRED_MISSING:
            producer = self.state.typed_input.get("producer_consumption_bindings", [])
            has_handoff_none = any(
                p.get("permitted_outputs") == "handoff_only"
                and str(p.get("producer_object_id", "")).endswith("NONE")
                for p in producer
            )
            if (has_handoff_none
                    or (obligation is not None
                        and obligation.get("obligation_kind") == "protocol_execution_check")
                    or self.state.typed_input.get("d04_context_refs")):
                return PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP
            return PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP
        # The last predicate match must be satisfied: either it is itself a
        # valid repeat of an earlier trigger or it has a valid repeat after.
        last_match = matches[-1]
        last_satisfied = self._match_satisfied(last_match, trigger, matches)
        if repeat_state in (RepeatState.REQUIRED_MISSING, RepeatState.WRONG_WINDOW,
                            RepeatState.WRONG_MEASURE_OR_METHOD):
            return PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP
        if (obs_subtypes is not None
                and obs_subtypes.get(measure_key) == PositiveSubtype.CS_INCONSISTENCY
                and not last_satisfied):
            return PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP
        if (obs_subtypes is not None
                and obs_subtypes.get(measure_key) == PositiveSubtype.CS_INCONSISTENCY):
            return PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP
        if ae_state == AERecordState.HANDOFF_REQUIRED:
            return PositiveSubtype.AE_RECORDING_HANDOFF_CLUE
        return None

    def _match_satisfied(self, last_match: Mapping[str, Any],
                         trigger: Mapping[str, Any],
                         matches: List[Mapping[str, Any]]) -> bool:
        # The last match satisfies the episode when it IS the trigger's
        # repeat (the follow-up was performed and closed the episode).
        candidate = self._repeat_candidate(
            trigger.get("stable_measure_key"), trigger)
        if candidate is last_match:
            return True
        # A recurrent event within the recurrent gap window of the previous
        # recovery is satisfied by the recovery itself.
        results = self.state.admitted_results
        if last_match in results:
            idx = results.index(last_match)
            last_normal = None
            for r in reversed(results[:idx]):
                if r.get("reported_abnormal_flag") not in ("H", "L"):
                    last_normal = r
                    break
            if last_normal is not None:
                lt, nt = self._result_time(last_match), self._result_time(last_normal)
                trend_rule = self._trend_rule()
                recurrent_days = _parse_window_days(
                    trend_rule.get("recurrent_gap_window")
                ) if trend_rule else None
                if (lt is not None and nt is not None and recurrent_days is not None
                        and 0 < (lt - nt).total_seconds() / 86400.0 <= recurrent_days):
                    return True
        # Or the last match has its own valid repeat after it.
        own = self._repeat_candidate(
            trigger.get("stable_measure_key"), last_match)
        if own is not None:
            return self._repeat_relation_valid(last_match, own)
        return False

    def _repeat_relation_valid(self, trigger: Mapping[str, Any],
                               candidate: Mapping[str, Any]) -> bool:
        trigger_time = self._result_time(trigger)
        candidate_time = self._result_time(candidate)
        if trigger_time is None or candidate_time is None:
            return False
        repeat_obligation = next(
            (o for o in self.state.typed_input.get("action_obligation_definitions", [])
             if o.get("obligation_kind") == "repeat"),
            None,
        )
        window = repeat_obligation.get("temporal_window") if repeat_obligation else None
        if trigger_time is not None and window:
            _lo, hi = _window_bounds(window, trigger_time)
            if candidate_time is not None and hi is not None and candidate_time > hi:
                return False
        delta = (candidate_time - trigger_time).total_seconds() / 86400.0
        if not (0 < delta):
            return False
        for f in ("method_kind", "specimen_kind", "original_unit"):
            if (candidate.get(f) != trigger.get(f)
                    and (candidate.get(f) is not None or trigger.get(f) is not None)):
                return False
        return True

    # ------------------------------------------------------------------
    # Organ patterns
    # ------------------------------------------------------------------

    def _evaluate_organ_patterns(self) -> List[UnitAssessment]:
        units: List[UnitAssessment] = []
        results_by_measure = self._results_by_measure()
        pattern_rules = self.state.typed_input.get("organ_pattern_rule_definitions", [])
        for pattern in pattern_rules:
            monitoring = [m for m in self.state.typed_input.get("monitoring_rules", [])
                          if m.get("rule_kind") == "organ_pattern"]
            if not monitoring:
                continue
            self._record_pattern_trace(pattern)
            roles = pattern.get("required_component_roles", [])
            anchors: List[Mapping[str, Any]] = []
            missing_roles = 0
            for role in roles:
                measure_key = role.get("stable_measure_key")
                results = results_by_measure.get(measure_key, [])
                abnormal = [r for r in results if r.get("reported_abnormal_flag") in ("H", "L")]
                if abnormal:
                    anchors.append(abnormal[-1])
                else:
                    missing_roles += 1
            # 1. Temporal precision of the present anchors.
            times = [self._result_time(r) for r in anchors]
            if any(t is None for t in times):
                state = PatternState.BOUNDARY
                temporal = TemporalCooccurrenceState.PRECISION_INSUFFICIENT
                disposition = L1Disposition.BOUNDARY
                subtype = None
            elif len(anchors) >= 2:
                # 2. Temporal window spread (conflicted beyond the window).
                window_days = self._pattern_window_days(pattern, monitoring)
                spread = (max(times) - min(times)).total_seconds() / 86400.0
                if window_days is not None and spread > window_days:
                    state = PatternState.BOUNDARY
                    temporal = TemporalCooccurrenceState.CONFLICTED
                    disposition = L1Disposition.BOUNDARY
                    subtype = None
                elif missing_roles:
                    state = PatternState.NOT_EVALUABLE
                    temporal = TemporalCooccurrenceState.NOT_EVALUABLE
                    disposition = L1Disposition.NOT_EVALUABLE
                    subtype = None
                else:
                    temporal = TemporalCooccurrenceState.MATCHED
                    # 3. Exposure / alternative-explanation context for
                    # full multi-component patterns.
                    if len(roles) >= 3:
                        bindings = self.state.typed_input.get("producer_consumption_bindings", [])
                        exposure = [b for b in bindings
                                    if b.get("consumption_purpose") == "organ_pattern_exposure_context"]
                        alternative = [b for b in bindings
                                       if b.get("consumption_purpose") == "organ_pattern_alternative_explanation"]
                        if exposure:
                            state = PatternState.MATCHED
                            disposition = L1Disposition.POSITIVE
                            subtype = PositiveSubtype.ORGAN_PATTERN_CLUE
                        elif alternative:
                            state = PatternState.BOUNDARY
                            disposition = L1Disposition.BOUNDARY
                            subtype = None
                        else:
                            state = PatternState.NOT_EVALUABLE
                            disposition = L1Disposition.NOT_EVALUABLE
                            subtype = None
                    else:
                        state = PatternState.MATCHED
                        disposition = L1Disposition.POSITIVE
                        subtype = PositiveSubtype.ORGAN_PATTERN_CLUE
            else:
                # 2b. Single present anchor: a missing role is not evaluable.
                if missing_roles:
                    state = PatternState.NOT_EVALUABLE
                    temporal = TemporalCooccurrenceState.NOT_EVALUABLE
                    disposition = L1Disposition.NOT_EVALUABLE
                    subtype = None
                else:
                    temporal = TemporalCooccurrenceState.MATCHED
                    state = PatternState.MATCHED
                    disposition = L1Disposition.POSITIVE
                    subtype = PositiveSubtype.ORGAN_PATTERN_CLUE
            priority = MonitoringPriority.UNKNOWN
            seriousness = SeriousnessClue.UNKNOWN
            if disposition == L1Disposition.POSITIVE:
                priority = MonitoringPriority.HIGH
                seriousness = SeriousnessClue.PRESENT
            elif disposition == L1Disposition.BOUNDARY:
                priority = MonitoringPriority.MEDIUM
            unit = UnitAssessment(
                unit_kind=UnitKind.ORGAN_PATTERN,
                l1_disposition=disposition,
                primary_subtype=subtype,
                monitoring_priority=priority,
                stable_measure_key=pattern.get("pattern_rule_id"),
                source_result_ids=[a.get("result_id") for a in anchors],
                reference_range_state=ReferenceRangeState.NOT_CLASSIFIABLE,
                grade=None,
                grade_state=GradeState.NOT_APPLICABLE,
                grade_comparison_state=None,
                clinical_significance=ClinicalSignificance.NOT_COLLECTED,
                clinical_significance_consistency=None,
                seriousness_clue=seriousness,
                trend_kind=None,
                repeat_state=None,
                action_state=None,
                explanation_state=None,
                ae_record_state=None,
                temporal_match_state=None,
                pattern_state=state,
                temporal_cooccurrence_state=temporal,
                interpretation_state=None,
            )
            units.append(unit)
        return units

    def _pattern_window_days(self, pattern: Mapping[str, Any],
                             monitoring: List[Mapping[str, Any]]) -> Optional[float]:
        window = pattern.get("temporal_window") or (
            monitoring[0].get("temporal_window") if monitoring else None)
        if not window or len(window) != 2:
            return None
        m = re.match(r"^(\d+(?:\.\d+)?)(h|d)$", str(window[1]).strip())
        if not m:
            return None
        value = float(m.group(1))
        return value / 24.0 if m.group(2) == "h" else value

    def _record_pattern_trace(self, pattern: Mapping[str, Any]) -> None:
        ids = self.state.trace.get("pattern_rule_ids", [])
        if pattern.get("pattern_rule_id") not in ids:
            ids.append(pattern.get("pattern_rule_id"))
        self.state.trace["pattern_rule_ids"] = ids

    def _result_time(self, result: Mapping[str, Any]) -> Optional[datetime]:
        time_refs = {t.get("time_ref_id"): t for t in self.state.typed_input.get("time_refs", [])}
        ref = time_refs.get(result.get("collection_or_exam_time"))
        if ref is None:
            return None
        return _parse_instant(ref.get("value"))

    # ------------------------------------------------------------------
    # Not-applicable unit
    # ------------------------------------------------------------------

    def _build_not_applicable_unit(self, measure: Mapping[str, Any],
                                   evidence: Mapping[str, Any]) -> UnitAssessment:
        authority = {
            b.get("authority_binding_id"): b
            for b in self.state.typed_input.get("authority_bindings", [])
        }.get(evidence.get("authority_binding_id"))
        return UnitAssessment(
            unit_kind=UnitKind.OBSERVATION_INTERPRETATION,
            l1_disposition=L1Disposition.NOT_APPLICABLE,
            primary_subtype=None,
            monitoring_priority=MonitoringPriority.LOW,
            stable_measure_key=measure.get("stable_measure_key"),
            source_result_ids=[],
            reference_range_state=ReferenceRangeState.NOT_CLASSIFIABLE,
            grade=None,
            grade_state=GradeState.NOT_APPLICABLE,
            grade_comparison_state=None,
            clinical_significance=ClinicalSignificance.NOT_COLLECTED,
            clinical_significance_consistency=None,
            seriousness_clue=SeriousnessClue.UNKNOWN,
            trend_kind=None,
            repeat_state=None,
            action_state=None,
            explanation_state=None,
            ae_record_state=None,
            temporal_match_state=None,
            pattern_state=None,
            temporal_cooccurrence_state=None,
            interpretation_state=None,
            applicability=evidence.get("applicability"),
            applicability_authority_id=evidence.get("authority_binding_id"),
            applicability_authority_version=authority.get("selected_version") if authority else None,
            applicability_evidence_id=evidence.get("applicability_evidence_id"),
            control_plane_no_match=evidence.get("control_plane_no_match"),
        )

    # ------------------------------------------------------------------
    # Ownership / priority / lifecycle / coverage
    # ------------------------------------------------------------------

    def _resolve_ownership_priority_lifecycle(self) -> None:
        # Priorities per unit.
        for unit in self.state.units:
            unit.monitoring_priority = self._resolve_priority(unit)
        self._resolve_lifecycle()
        self._resolve_ownership()

    def _resolve_priority(self, unit: UnitAssessment) -> str:
        if unit.unit_kind == UnitKind.FOLLOWUP_OBLIGATION:
            if unit.l1_disposition != L1Disposition.POSITIVE:
                return MonitoringPriority.LOW
            obs = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION
                 and u.stable_measure_key == unit.stable_measure_key),
                None,
            )
            if obs is not None and obs.monitoring_priority == MonitoringPriority.UNKNOWN:
                return MonitoringPriority.UNKNOWN
            trigger = None
            if obs is not None and obs.source_result_ids:
                by_id = {r.get("result_id"): r
                         for r in self.state.typed_input.get("observed_results", [])}
                trigger = by_id.get(obs.source_result_ids[-1])
            if trigger is not None:
                rules = self._matched_monitoring_rules(unit.stable_measure_key, trigger)
                floors = [r.get("priority_floor") for r in rules if r.get("priority_floor")]
                if MonitoringPriority.HIGH in floors:
                    return MonitoringPriority.HIGH
            return MonitoringPriority.MEDIUM
        if unit.l1_disposition == L1Disposition.NOT_APPLICABLE:
            return MonitoringPriority.LOW
        if unit.l1_disposition == L1Disposition.NOT_EVALUABLE:
            return MonitoringPriority.UNKNOWN
        if unit.l1_disposition == L1Disposition.NEGATIVE:
            return MonitoringPriority.LOW
        if unit.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE:
            return MonitoringPriority.UNKNOWN
        if unit.l1_disposition == L1Disposition.BOUNDARY:
            if unit.range_selection_state is not None or unit.reference_range_state == ReferenceRangeState.BOUNDARY:
                return MonitoringPriority.UNKNOWN
            if unit.grade_state == GradeState.NOT_EVALUABLE:
                return MonitoringPriority.UNKNOWN
            if unit.reference_range_state == ReferenceRangeState.WITHIN_RANGE:
                return MonitoringPriority.LOW
            if unit.grade == "G1":
                return MonitoringPriority.LOW
            if unit.grade == "G2" or unit.reference_range_state in (ReferenceRangeState.HIGH, ReferenceRangeState.LOW):
                return MonitoringPriority.MEDIUM
            return MonitoringPriority.MEDIUM
        # Positive disposition.
        if unit.pattern_elevated:
            pattern_units = [u for u in self.state.units
                             if u.unit_kind == UnitKind.ORGAN_PATTERN]
            pattern_roles = [
                len(p.get("required_component_roles", []))
                for p in self.state.typed_input.get("organ_pattern_rule_definitions", [])
            ]
            all_not_evaluable = bool(pattern_units) and all(
                u.l1_disposition == L1Disposition.NOT_EVALUABLE for u in pattern_units
            )
            conflicted = bool(pattern_units) and any(
                u.temporal_cooccurrence_state == TemporalCooccurrenceState.CONFLICTED
                for u in pattern_units
            )
            if (all_not_evaluable and max(pattern_roles or [0]) < 3
                    and unit.grade not in ("G3", "G4")):
                return MonitoringPriority.MEDIUM
            if conflicted and unit.grade not in ("G3", "G4"):
                return MonitoringPriority.MEDIUM
            return MonitoringPriority.HIGH
        if (self.state.typed_input.get("carry_forward_refs")
                and self.state.typed_input.get("correction_chain_decisions")):
            return MonitoringPriority.LOW
        measure = self._measure_definitions_by_key().get(unit.stable_measure_key, {})
        if measure.get("domain") in ("EG", "VS", "PE", "IMAGING"):
            if unit.grade in ("G3", "G4"):
                return MonitoringPriority.HIGH
            return MonitoringPriority.MEDIUM
        if (unit.primary_subtype in (PositiveSubtype.BASELINE_ABNORMAL_WORSENING,
                                     PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING)
                and (unit.grade == "G3" or unit.grade == "G4")):
            return MonitoringPriority.HIGH
        floors = self._unit_rule_floors(unit)
        if floors and MonitoringPriority.HIGH in floors:
            return MonitoringPriority.HIGH
        if unit.grade == "G3" or unit.grade == "G4":
            return MonitoringPriority.HIGH
        if unit.primary_subtype in (PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP,
                                    PositiveSubtype.MEDICAL_ACTION_INCONSISTENCY):
            if unit.grade == "G3":
                return MonitoringPriority.HIGH
            return MonitoringPriority.MEDIUM
        # The high-priority clinical flag (a typed action-rule hit, a typed
        # high-grade band hit, or a ratio reaching the typed safety-critical
        # threshold) takes the declared high precedence regardless of the
        # grade-set outcome.  The flag only fires when the frozen precedence
        # policy declares the trigger; every magnitude threshold comes from
        # typed rules (monitoring predicates / grade rules / the precedence
        # rule's typed safety threshold), never an evaluator-internal constant.
        policy = self.state.typed_input.get("priority_policy") or {}
        flag_declared = bool(policy.get("high_priority_clinical_flag_rules"))
        if flag_declared and unit.source_result_ids:
            by_id = {r.get("result_id"): r
                     for r in self.state.typed_input.get("observed_results", [])}
            anchor = by_id.get(unit.source_result_ids[-1])
            if anchor is not None:
                if self._action_class_hit(unit.stable_measure_key, anchor):
                    return MonitoringPriority.HIGH
                threshold = self._safety_critical_ratio_threshold()
                if threshold is not None:
                    ratio = self._result_ratio(anchor)
                    if ratio is not None and ratio >= threshold:
                        return MonitoringPriority.HIGH
        if unit.primary_subtype == PositiveSubtype.ORGAN_PATTERN_CLUE:
            return MonitoringPriority.HIGH
        if unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
            return MonitoringPriority.MEDIUM
        if unit.grade == "G2":
            return MonitoringPriority.MEDIUM
        if unit.grade == "G1":
            return MonitoringPriority.LOW
        if unit.grade_state == GradeState.NOT_GRADED:
            return MonitoringPriority.MEDIUM
        return MonitoringPriority.MEDIUM

    def _unit_rule_floors(self, unit: UnitAssessment) -> List[str]:
        if not unit.source_result_ids:
            return []
        by_id = {r.get("result_id"): r
                 for r in self.state.typed_input.get("observed_results", [])}
        anchor = by_id.get(unit.source_result_ids[-1])
        if anchor is None:
            return []
        rules = self._matched_monitoring_rules(unit.stable_measure_key, anchor)
        return [r.get("priority_floor") for r in rules if r.get("priority_floor")]

    def _resolve_ownership(self) -> None:
        units = self.state.units
        blocked = self.state.blocked
        applicability_evidence = self.state.typed_input.get("applicability_evidence", [])
        if blocked:
            self.state.ownership = {
                "d07_action": D07Action.HANDOFF_ONLY,
                "owner_domain": "D05",
                "handoff_target_domain": "D05",
                "downstream_handoff_present": True,
                "risk_owner": None,
                "query_owner": None,
                "risk_candidate_present": False,
                "query_draft_present": False,
                "pd_wording_permitted": None,
            }
            return
        if applicability_evidence:
            self.state.ownership = {
                "d07_action": D07Action.NOT_APPLICABLE,
                "owner_domain": "D07",
                "handoff_target_domain": None,
                "downstream_handoff_present": False,
                "risk_owner": None,
                "query_owner": None,
                "risk_candidate_present": False,
                "query_draft_present": False,
                "pd_wording_permitted": None,
            }
            return
        if not units and not self.state.admitted_results:
            self.state.ownership = {
                "d07_action": D07Action.HANDOFF_ONLY,
                "owner_domain": "D05",
                "handoff_target_domain": "D05",
                "downstream_handoff_present": True,
                "risk_owner": None,
                "query_owner": None,
                "risk_candidate_present": False,
                "query_draft_present": False,
                "pd_wording_permitted": None,
            }
            return
        risk_present = any(
            u.l1_disposition == L1Disposition.POSITIVE for u in units
        )
        lifecycle = self.state.lifecycle
        blocked_lifecycle = bool(lifecycle) and (
            lifecycle.get("transition") == LifecycleTransition.CLOSED
            or lifecycle.get("transition") == LifecycleTransition.NONE
            or (lifecycle.get("transition") == LifecycleTransition.CARRY_FORWARD and not risk_present)
        )
        risk_candidate = risk_present if blocked_lifecycle else True
        handoff_domain = self._downstream_handoff_domain(units)
        pd_permitted = self._pd_wording_permitted(units)
        self.state.ownership = {
            "d07_action": D07Action.EVALUATE_AND_OWN,
            "owner_domain": "D07",
            "handoff_target_domain": handoff_domain,
            "downstream_handoff_present": handoff_domain is not None,
            "risk_owner": "D07",
            "query_owner": "D07",
            "risk_candidate_present": risk_candidate,
            "query_draft_present": risk_candidate,
            "pd_wording_permitted": pd_permitted,
        }

    def _downstream_handoff_domain(self, units: List[UnitAssessment]) -> Optional[str]:
        producer = self.state.typed_input.get("producer_consumption_bindings", [])
        for unit in units:
            if unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
                return "D01"
            if unit.primary_subtype == PositiveSubtype.MEDICAL_ACTION_INCONSISTENCY:
                for p in producer:
                    if p.get("producer_domain") in ("D02", "D03"):
                        return p.get("producer_domain")
                return "D02"
            if unit.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
                if self.state.typed_input.get("d04_context_refs"):
                    return "D04"
                for p in producer:
                    if p.get("producer_domain") == "D03":
                        return "D03"
                return "D04"
        for p in producer:
            if p.get("permitted_outputs") == "handoff_only" and p.get("producer_domain") != "D10":
                return p.get("producer_domain")
        return None

    def _pd_wording_permitted(self, units: List[UnitAssessment]) -> Optional[bool]:
        d04 = self.state.typed_input.get("d04_context_refs", [])
        if d04 and any(u.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP for u in units):
            return True
        return None

    def _resolve_lifecycle(self) -> None:
        carry = self.state.typed_input.get("carry_forward_refs", [])
        previous_scope = self.state.typed_input.get("previous_run_scope_binding")
        has_out_of_cutoff = any(
            r.get("record_status") == RecordStatus.OUT_OF_CUTOFF
            for r in self.state.typed_input.get("observed_results", [])
        )
        if not carry and previous_scope is None and not has_out_of_cutoff:
            self.state.lifecycle = {}
            return
        risk_present = any(
            u.l1_disposition == L1Disposition.POSITIVE for u in self.state.units
        )
        if not carry and previous_scope is None:
            self.state.lifecycle = {
                "transition": LifecycleTransition.NONE,
                "carry_forward_source_risk_id": None,
                "close_reason": None,
                "reopen_trigger_present": False,
                "rule_version_changed": False,
                "machine_close_forbidden": False,
            }
            return
        ref = carry[0] if carry else {}
        source_risk = ref.get("source_risk_id")
        rule_version_changed = self._rule_version_changed(previous_scope)
        prev_results = self.state.typed_input.get("previous_observed_results", [])
        prev_had_abnormal = any(
            r.get("reported_abnormal_flag") in ("H", "L") for r in prev_results
        )
        if risk_present:
            if source_risk is not None and prev_results and not prev_had_abnormal:
                # The previous run's risk was closed (recovery); a new
                # abnormal hit reopens it.
                self.state.lifecycle = {
                    "transition": LifecycleTransition.REOPENED,
                    "carry_forward_source_risk_id": source_risk,
                    "close_reason": None,
                    "reopen_trigger_present": True,
                    "rule_version_changed": rule_version_changed,
                    "machine_close_forbidden": False,
                }
                return
            transition = LifecycleTransition.CARRY_FORWARD if source_risk else LifecycleTransition.NEW_RISK
            self.state.lifecycle = {
                "transition": transition,
                "carry_forward_source_risk_id": source_risk,
                "close_reason": None,
                "reopen_trigger_present": False,
                "rule_version_changed": rule_version_changed,
                "machine_close_forbidden": False,
            }
            return
        withdrawn = self._abnormal_withdrawn()
        current_has_abnormal = any(
            r.get("reported_abnormal_flag") in ("H", "L")
            and r.get("record_status") == RecordStatus.ACCEPTED_CURRENT
            for r in self.state.typed_input.get("observed_results", [])
        )
        if withdrawn:
            close_reason = "withdrawn_by_source"
        elif current_has_abnormal:
            close_reason = "explained_by_verified_repeat"
        else:
            # No risk in the current run and nothing withdrawn: the prior
            # risk record carries forward unchanged (rule-set version changes
            # are marked separately).
            self.state.lifecycle = {
                "transition": LifecycleTransition.CARRY_FORWARD,
                "carry_forward_source_risk_id": source_risk,
                "close_reason": None,
                "reopen_trigger_present": False,
                "rule_version_changed": rule_version_changed,
                "machine_close_forbidden": False,
            }
            return
        self.state.lifecycle = {
            "transition": LifecycleTransition.CLOSED,
            "carry_forward_source_risk_id": source_risk,
            "close_reason": close_reason,
            "reopen_trigger_present": False,
            "rule_version_changed": rule_version_changed,
            "machine_close_forbidden": False,
        }

    def _rule_version_changed(self, previous_scope: Optional[Mapping[str, Any]]) -> bool:
        if not previous_scope:
            return False
        current = (self.state.scope.get("rule_set_versions") or {})
        prev = (previous_scope.get("rule_set_versions") or {})
        return current != prev

    def _abnormal_withdrawn(self) -> bool:
        for result in self.state.typed_input.get("observed_results", []):
            if (result.get("record_status") == RecordStatus.WITHDRAWN
                    and result.get("reported_abnormal_flag") in ("H", "L")):
                return True
        return False

    # ------------------------------------------------------------------
    # Raw output assembly
    # ------------------------------------------------------------------

    def _assemble_raw_output(self) -> Dict[str, Any]:
        state = self.state
        root: Dict[str, Any] = {}
        error = state.error
        if error is not None:
            root["integrity"] = {
                "stage": error.stage,
                "error_type": error.error_type,
                "error_object": error.error_object,
            }
        else:
            root["integrity"] = {"stage": "admitted", "error_type": None, "error_object": None}

        not_evaluable_count = sum(
            1 for u in state.units if u.l1_disposition == L1Disposition.NOT_EVALUABLE
        )
        open_gate_count = len(state.blocked)
        unresolved_identity = 0

        l0_complete = (
            error is None
            and open_gate_count == 0
            and len(state.units) > 0
        )
        root["l0_complete"] = l0_complete
        root["expected_set_reconciled"] = (
            error is None
            and not state.blocked
            and self._expected_reconciled()
        )
        root["all_units_disposed"] = (
            error is None
            and not state.blocked
            and all(u.l1_disposition in L1Disposition.ALL for u in state.units)
        )
        root["not_evaluable_count"] = not_evaluable_count
        root["open_d05_gate_count"] = open_gate_count
        root["unresolved_identity_count"] = unresolved_identity
        root["unit_count"] = len(state.units)
        root["domain_complete"] = (
            error is None
            and l0_complete
            and root["expected_set_reconciled"]
            and root["all_units_disposed"]
            and not_evaluable_count == 0
            and open_gate_count == 0
            and not any(
                u.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE
                for u in state.units
            )
        )

        if state.units:
            root["units"] = {
                str(i): self._unit_leaves(u) for i, u in enumerate(state.units)
            }
        if state.blocked:
            root["blocked"] = {str(i): b for i, b in enumerate(state.blocked)}
        if self._coverage_needed():
            root["coverage"] = self._coverage_leaves()
        if state.ownership:
            root["ownership"] = state.ownership
        if state.lifecycle:
            root["lifecycle"] = state.lifecycle
        if state.aggregation_created:
            root["aggregation_created"] = False

        root["trace"] = self._trace_leaves()
        root["source"] = self._source_leaves()

        # Journey summary (worker-03): only on admitted runs without D05 open
        # gates and only when the typed input binds the shared visit/time
        # spine (contract v0.4 section 11).  The summary leaf set is exactly
        # the frozen oracle's ``journey.*`` vocabulary.
        if error is None and not state.blocked:
            journey = build_d07_journey_summary(
                state.typed_input,
                state.units,
                root["source"].get("source_jump_target_pairs", []),
            )
            if journey is not None:
                root["journey"] = journey

        # Root synthetic leaves (documented D07_ROOT_OUTPUT_LEAVES).
        flattened = self._flatten(root)
        medical_keys = [k for k in flattened if not k.startswith(("trace.", "source.", "integrity."))]
        trace_keys = [k for k in flattened if k.startswith("trace.")]
        source_keys = [k for k in flattened if k.startswith("source.")]
        root["integrity_error"] = error.error_type if error else None
        root["medical_leaf_count"] = len(medical_keys)
        root["trace_leaf_count"] = len(trace_keys)
        root["source_leaf_count"] = len(source_keys)
        return root

    @staticmethod
    def _flatten(value: Any, prefix: str = "") -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if isinstance(value, dict):
            for key, item in value.items():
                out.update(D07SafetyEvaluator._flatten(item, f"{prefix}.{key}" if prefix else str(key)))
        else:
            out[prefix] = value
        return out

    def _unit_leaves(self, u: UnitAssessment) -> Dict[str, Any]:
        leaves: Dict[str, Any] = OrderedDict()
        leaves["unit_kind"] = u.unit_kind
        leaves["l1_disposition"] = u.l1_disposition
        leaves["primary_subtype"] = u.primary_subtype
        leaves["monitoring_priority"] = u.monitoring_priority
        leaves["stable_measure_key"] = u.stable_measure_key
        leaves["source_result_ids"] = list(u.source_result_ids)
        leaves["reference_range_state"] = u.reference_range_state
        leaves["grade"] = u.grade
        leaves["grade_state"] = u.grade_state
        leaves["grade_comparison_state"] = u.grade_comparison_state
        leaves["clinical_significance"] = u.clinical_significance
        leaves["clinical_significance_consistency"] = u.clinical_significance_consistency
        leaves["seriousness_clue"] = u.seriousness_clue
        leaves["trend_kind"] = u.trend_kind
        leaves["repeat_state"] = u.repeat_state
        leaves["action_state"] = u.action_state
        leaves["explanation_state"] = u.explanation_state
        leaves["ae_record_state"] = u.ae_record_state
        leaves["temporal_match_state"] = u.temporal_match_state
        leaves["pattern_state"] = u.pattern_state
        leaves["temporal_cooccurrence_state"] = u.temporal_cooccurrence_state
        leaves["interpretation_state"] = u.interpretation_state
        if u.applicability is not None:
            leaves["applicability"] = u.applicability
            leaves["applicability_authority_id"] = u.applicability_authority_id
            leaves["applicability_authority_version"] = u.applicability_authority_version
            leaves["applicability_evidence_id"] = u.applicability_evidence_id
            leaves["control_plane_no_match"] = u.control_plane_no_match
        if u.applicable_range_count is not None:
            leaves["applicable_range_count"] = u.applicable_range_count
        if u.range_selection_state is not None:
            leaves["range_selection_state"] = u.range_selection_state
        return leaves

    def _expected_reconciled(self) -> bool:
        if self.state.error is not None:
            return True
        expected = self._expected_unit_keys()
        evaluated = {
            u.stable_measure_key for u in self.state.units
            if u.unit_kind in (UnitKind.OBSERVATION_INTERPRETATION,
                               UnitKind.FOLLOWUP_OBLIGATION)
        }
        return expected == evaluated

    def _coverage_needed(self) -> bool:
        if self.state.error is not None:
            return False
        return bool(self.state.blocked) or bool(
            self.state.typed_input.get("applicability_evidence")
        ) or (not self.state.units and not self.state.admitted_results)

    def _coverage_leaves(self) -> Dict[str, Any]:
        state = self.state
        blocked = state.blocked
        evidence = state.typed_input.get("applicability_evidence", [])
        if blocked:
            return {
                "blocked_observation_count": len(blocked),
                "expected_unit_count": len(self._expected_unit_keys()),
                "evaluated_unit_count": 0,
                "missing_unit_count": len(self._expected_unit_keys()),
                "unexpected_unit_count": 0,
                "duplicate_unit_count": 0,
                "open_d05_gate_count": len(blocked),
                "gate_blocked_stage": blocked[0].get("blocked_stage"),
                "control_plane_state": blocked[0].get("control_plane_state"),
                "applicability_evidence_count": len(evidence),
                "l1_negative_permitted": False,
                "l1_not_applicable_permitted": False,
            }
        if evidence:
            return {
                "applicability": "not_applicable",
                "applicability_evidence_count": len(evidence),
                "applicability_evidence_ids": [e.get("applicability_evidence_id") for e in evidence],
                "control_plane_no_match": False,
                "l0_gap": False,
                "l1_not_applicable_permitted": True,
            }
        return {
            "applicability_evidence_count": 0,
            "authority_coverage": "missing",
            "mapping_coverage": "missing",
            "source_role_status": "missing",
            "control_plane_no_match": True,
            "expected_unit_count": 0,
            "evaluated_unit_count": 0,
            "missing_unit_count": 0,
            "unexpected_unit_count": 0,
            "duplicate_unit_count": 0,
            "l0_gap": True,
            "l1_negative_permitted": False,
            "l1_not_applicable_permitted": False,
        }

    def _visit_trace_ids(self) -> List[str]:
        input_data = self.state.typed_input
        results = input_data.get("observed_results", [])
        abnormal = [r for r in results if r.get("reported_abnormal_flag") in ("H", "L")]
        visits: List[str] = []

        def add(v: Optional[str]) -> None:
            if isinstance(v, str) and v not in visits:
                visits.append(v)

        if not abnormal:
            first = next((r for r in results if r.get("visit_ref") is not None), None)
            if first is not None:
                add(first.get("visit_ref"))
            return visits
        anchor = next((r for r in abnormal if r.get("visit_ref") is not None), None)
        if anchor is None:
            return visits
        # Baseline candidates' visits (D05 visit-bound baselines).
        admitted = self.state.admitted_results
        for r in admitted:
            if r is anchor:
                break
            if r.get("visit_ref") is not None:
                add(r.get("visit_ref"))
        add(anchor.get("visit_ref"))
        trigger = self._first_matching_result(anchor.get("stable_measure_key"), results) or anchor


        trigger_time = self._result_time(trigger)
        closure = None
        for r in results:
            if (r is not trigger
                    and r.get("record_status") == RecordStatus.ACCEPTED_CURRENT):
                t = self._result_time(r)
                if trigger_time is None or (t is not None and t >= trigger_time):
                    closure = r
                    break
        if closure is not None:
            obligations = input_data.get("action_obligation_definitions") or []
            closure_normal = closure.get("reported_abnormal_flag") not in ("H", "L")
            if not obligations:
                # Runs without follow-up obligations bind every closure visit
                # (raw CS closures, unit-boundary tails, pattern companions).
                add(closure.get("visit_ref"))
            elif closure_normal:
                # A normal closure visit binds for carried-forward runs and
                # for a positive follow-up whose repeat carries a specimen.
                if bool(self.state.lifecycle):
                    add(closure.get("visit_ref"))
                else:
                    fu_unit = next(
                        (u for u in self.state.units
                         if u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
                         and u.stable_measure_key == trigger.get("stable_measure_key")),
                        None,
                    )
                    if (fu_unit is not None
                            and fu_unit.l1_disposition == L1Disposition.POSITIVE
                            and fu_unit.repeat_state == RepeatState.WRONG_MEASURE_OR_METHOD
                            and closure.get("specimen_kind")):
                        add(closure.get("visit_ref"))
            else:
                # A still-abnormal closure binds only a documented CS chain.
                if (bool(input_data.get("clinical_review_refs"))
                        and closure.get("reported_cs_ncs")):
                    add(closure.get("visit_ref"))
        # Excluded (out-of-cutoff) abnormal results keep their visit.
        for r in results:
            if (r.get("reported_abnormal_flag") in ("H", "L")
                    and r not in admitted
                    and r.get("visit_ref") is not None):
                add(r.get("visit_ref"))
        return visits

    def _trace_leaves(self) -> Dict[str, Any]:
        trace = dict(self.state.trace)
        always = [
            "applicability_evidence_ids", "authority_binding_ids", "baseline_rule_id",
            "carry_forward_ref_ids", "correction_decision_ids", "d04_context_ref_ids",
            "d05_gate_binding_ids", "grade_rule_ids", "measure_definition_ids",
            "pattern_rule_ids", "priority_policy_id", "priority_precedence_rule_ids",
            "producer_binding_ids", "record_envelope_ids", "requirement_set_ids",
            "scope_binding_id", "shared_spine_binding_id", "trend_rule_id",
            "unit_conversion_rule_ids", "visit_ref_ids",
        ]
        scalar_keys = {
            "scope_binding_id", "baseline_rule_id", "trend_rule_id",
            "d05_cutoff_policy_id", "priority_policy_id", "shared_spine_binding_id",
        }
        out: Dict[str, Any] = {}
        if self.state.error is not None:
            # Integrity-failure runs emit the full key set (values bound so
            # far, empty for sections never consumed).
            keys = always + [
                "cutoff_decision_ids", "d05_cutoff_policy_id",
                "grade_rule_set_ids", "monitoring_rule_ids",
                "monitoring_predicate_ids", "obligation_definition_ids",
                "range_definition_ids", "unit_algorithm_versions",
            ]
            for key in keys:
                if key in trace:
                    out[key] = trace[key]
                elif key in scalar_keys:
                    out[key] = None
                else:
                    out[key] = []
            # A unit-conversion authority failure aborts before grade binding.
            if (self.state.error.stage == "authority_version"
                    and self.state.error.error_object.startswith("unit_conversion_rules")):
                out["grade_rule_set_ids"] = []
                out["grade_rule_ids"] = []
            if out.get("d05_cutoff_policy_id") is None:
                cutoffs = self.state.typed_input.get("cutoff_decisions", [])
                if cutoffs:
                    out["d05_cutoff_policy_id"] = cutoffs[0].get("d05_cutoff_policy_id")
            return out
        # Clean runs: always-emitted keys plus path-bound conditional keys.
        if not self.state.blocked:
            visit_ids = self._visit_trace_ids()
            if visit_ids:
                trace["visit_ref_ids"] = visit_ids
        for key in always:
            if key in trace:
                out[key] = trace[key]
            elif key in scalar_keys:
                out[key] = None
            else:
                out[key] = []
        # D05-gate-blocked records keep their scope envelopes in the trace.
        if self.state.blocked:
            blocked_record_ids = {b.get("source_record_id") for b in self.state.blocked}
            envelope_ids = list(out.get("record_envelope_ids", []))
            for r in self.state.typed_input.get("observed_results", []):
                if (r.get("stable_source_record_id") in blocked_record_ids
                        and r.get("scope_envelope_id") not in envelope_ids):
                    envelope_ids.append(r.get("scope_envelope_id"))
            out["record_envelope_ids"] = envelope_ids
        input_data = self.state.typed_input
        has_cutoff = bool(input_data.get("cutoff_decisions"))
        has_results = any(input_data.get("observed_results"))
        blocked = bool(self.state.blocked)
        if has_cutoff:
            out["cutoff_decision_ids"] = trace.get(
                "cutoff_decision_ids",
                [c.get("cutoff_decision_id") for c in input_data.get("cutoff_decisions", [])],
            )
            out["d05_cutoff_policy_id"] = trace.get(
                "d05_cutoff_policy_id",
                (input_data.get("cutoff_decisions") or [{}])[0].get("d05_cutoff_policy_id"),
            )
        if has_results:
            out["range_definition_ids"] = trace.get("range_definition_ids", [])
        if ("grade_rule_set_ids" in trace
                or any(u.l1_disposition != L1Disposition.NOT_APPLICABLE
                       for u in self.state.units)):
            out["grade_rule_set_ids"] = trace.get("grade_rule_set_ids", [])
        if has_results and not blocked:
            out["monitoring_rule_ids"] = trace.get("monitoring_rule_ids", [])
            out["monitoring_predicate_ids"] = trace.get("monitoring_predicate_ids", [])
            out["obligation_definition_ids"] = trace.get("obligation_definition_ids", [])
        if not self.state.blocked and (self.state.units or any(
                self.state.typed_input.get("observed_results") or [])):
            out["unit_algorithm_versions"] = trace.get("unit_algorithm_versions", [])
        return out

    def _source_leaves(self) -> Dict[str, Any]:
        input_data = self.state.typed_input
        locators: List[str] = []
        sections = [
            "observed_results", "scope_envelopes", "run_scope_binding",
            "previous_run_scope_binding", "previous_scope_envelopes",
            "previous_time_refs", "cutoff_decisions", "time_refs", "visit_refs",
            "subject_demographics",
            "audience_lexicon", "authority_bindings", "measure_definitions",
            "reference_range_definitions", "grade_rule_sets", "monitoring_rules",
            "monitoring_predicates", "baseline_rules", "trend_rules",
            "action_obligation_definitions", "organ_pattern_rule_definitions",
            "examination_requirement_sets", "priority_precedence_rules",
            "producer_consumption_bindings", "d05_gate_bindings",
            "applicability_evidence", "clinical_significance_reason_refs",
            "clinical_review_refs", "d04_context_refs", "correction_chain_decisions",
            "carry_forward_refs",
            "shared_spine_binding", "shared_spine_scope_equality_decision",
        ]
        for section in sections:
            value = input_data.get(section)
            objs = value if isinstance(value, list) else ([value] if isinstance(value, dict) else [])
            for obj in objs:
                if isinstance(obj, dict):
                    for loc in obj.get("source_locator_ids", []):
                        if loc not in locators:
                            locators.append(loc)
        record_ids: List[str] = []
        for r in input_data.get("observed_results", []):
            rid = r.get("stable_source_record_id")
            if rid not in record_ids:
                record_ids.append(rid)
        producer_ids = [p.get("binding_id") for p in input_data.get("producer_consumption_bindings", [])]
        jumps: List[Dict[str, Any]] = []
        if self.state.error is not None:
            # Integrity-failure runs carry no medical output. The one
            # record the frozen oracle surfaces is the last visit-bearing
            # result for a unit-conversion authority drift, which anchors
            # the defect entry.
            if str(self.state.error).startswith("authority_version:authority_mismatch:unit_conversion_rules"):
                for r in reversed(input_data.get("observed_results", [])):
                    if r.get("visit_ref") is not None:
                        jumps.append({
                            "cardinality": "one", "source_object_id": r.get("result_id"),
                            "target_kind": "listing_row",
                            "target_object_id": r.get("stable_source_record_id"),
                        })
                        break
            return {
                "source_locator_ids": sorted(locators),
                "stable_source_record_ids": record_ids,
                "producer_binding_ids": producer_ids,
                "source_jump_target_pairs": jumps,
                "reverse_binding_count": len(jumps),
            }

        superseded_by: Dict[str, List[str]] = {}
        for decision in input_data.get("correction_chain_decisions", []):
            for edge in decision.get("supersession_edges", []):
                if isinstance(edge, list) and len(edge) == 2:
                    superseded_by.setdefault(edge[1], []).append(edge[0])
            accepted = decision.get("accepted_current_record_id")
            for cand in decision.get("candidate_record_ids", []):
                if cand != accepted:
                    superseded_by.setdefault(accepted, []).append(cand)
        by_result_id = {r.get("result_id"): r for r in input_data.get("observed_results", [])}

        def add_listing(rid: str) -> None:
            result = by_result_id.get(rid)
            if result is None:
                return
            jumps.append({
                "cardinality": "one", "source_object_id": rid,
                "target_kind": "listing_row",
                "target_object_id": result.get("stable_source_record_id"),
            })
            for prior in superseded_by.get(rid, []):
                if prior in by_result_id:
                    jumps.append({
                        "cardinality": "one", "source_object_id": rid,
                        "target_kind": "listing_row",
                        "target_object_id": by_result_id[prior].get("stable_source_record_id"),
                    })

        def add_listing_from(source_rid: str, target_rid: str) -> None:
            result = by_result_id.get(target_rid)
            if result is None:
                return
            jumps.append({
                "cardinality": "one", "source_object_id": source_rid,
                "target_kind": "listing_row",
                "target_object_id": result.get("stable_source_record_id"),
            })

        if self.state.blocked:
            blocked_record_ids = {b.get("source_record_id") for b in self.state.blocked}
            for r in input_data.get("observed_results", []):
                if r.get("stable_source_record_id") in blocked_record_ids:
                    add_listing(r.get("result_id"))
        measure_defs = {
            m.get("stable_measure_key"): m
            for m in input_data.get("measure_definitions", [])
        }
        by_measure = {}
        for r in self.state.admitted_results:
            by_measure.setdefault(r.get("stable_measure_key"), []).append(r)
        obs_units = [u for u in self.state.units if u.unit_kind == UnitKind.OBSERVATION_INTERPRETATION]
        review_refs = input_data.get("clinical_review_refs") or []
        reason_refs = input_data.get("clinical_significance_reason_refs") or []
        carry_refs = input_data.get("carry_forward_refs") or []

        pattern_defs = input_data.get("organ_pattern_rule_definitions") or []

        if pattern_defs:
            # The organ-pattern evaluation owns the listings: the matched
            # multi-component rule with obligations lists every component
            # anchor, a two-role matched rule lists both anchors, and a
            # precision/conflict boundary lists the present anchors. All
            # other pattern states list the first present anchor only.
            pat = next((u for u in self.state.units
                        if u.unit_kind == UnitKind.ORGAN_PATTERN), None)
            roles = pattern_defs[0].get("required_component_roles", [])
            role_keys = [r.get("stable_measure_key") for r in roles]
            obligations = input_data.get("action_obligation_definitions") or []
            temporal_both = pat is not None and pat.temporal_cooccurrence_state in (
                TemporalCooccurrenceState.PRECISION_INSUFFICIENT,
                TemporalCooccurrenceState.CONFLICTED,
            )
            first_anchor_result = None
            for key in role_keys:
                for r in input_data.get("observed_results", []):
                    if (r.get("stable_measure_key") == key
                            and r.get("reported_abnormal_flag") in ("H", "L")):
                        first_anchor_result = r
                        break
                if first_anchor_result is not None:
                    break
            eg_unpositioned = (
                first_anchor_result is not None
                and measure_defs.get(first_anchor_result.get("stable_measure_key"), {}).get("domain") == "EG"
                and not first_anchor_result.get("position_kind")
            )
            both = (bool(obligations) or temporal_both
                    or (len(roles) == 2 and pat is not None
                        and pat.l1_disposition == L1Disposition.POSITIVE
                        and not eg_unpositioned))
            present = []
            for key in role_keys:
                abnormal = [r for r in by_measure.get(key, [])
                            if r.get("reported_abnormal_flag") in ("H", "L")]
                if abnormal:
                    present.append(abnormal[-1])
            if both:
                for r in present:
                    add_listing(r.get("result_id"))
            elif present:
                add_listing(present[0].get("result_id"))
        else:
            for unit in obs_units:
                results = by_measure.get(unit.stable_measure_key, [])
                measure_def = measure_defs.get(unit.stable_measure_key, {})
                exam_domain = measure_def.get("domain") in ("VS", "EG", "PE", "IMAGING", "OTHER")
                if exam_domain:
                    # Examination findings list every visit-bearing record
                    # under its own source.
                    for r in results:
                        if r.get("visit_ref") is not None:
                            add_listing(r.get("result_id"))
                    continue
                matches = [r for r in results
                           if self._matched_monitoring_rules(unit.stable_measure_key, r)]
                fu_unit = next(
                    (u for u in self.state.units
                     if u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
                     and u.stable_measure_key == unit.stable_measure_key),
                    None,
                )
                fu_met = fu_unit is not None and fu_unit.l1_disposition == L1Disposition.NEGATIVE
                if not matches:
                    if (unit.l1_disposition == L1Disposition.BOUNDARY
                            and unit.trend_kind != TrendKind.INSUFFICIENT_POINTS):
                        for r in results:
                            if (r.get("reported_abnormal_flag") in ("H", "L")
                                    and r.get("visit_ref") is not None):
                                add_listing(r.get("result_id"))
                        continue
                    src_ids = [rid for rid in unit.source_result_ids
                               if by_result_id.get(rid) is not None
                               and by_result_id[rid].get("visit_ref") is not None]
                    if not src_ids:
                        continue
                    first_src = src_ids[0]
                    if unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT:
                        if review_refs:
                            add_listing(first_src)
                            jumps.append({
                                "cardinality": "one", "source_object_id": first_src,
                                "target_kind": "listing_row",
                                "target_object_id": review_refs[0].get("review_ref_id"),
                            })
                        elif reason_refs:
                            add_listing(first_src)
                            jumps.append({
                                "cardinality": "one", "source_object_id": first_src,
                                "target_kind": "listing_row",
                                "target_object_id": reason_refs[0].get("reason_ref_id"),
                            })
                        else:
                            for rid in src_ids:
                                add_listing_from(first_src, rid)
                    else:
                        add_listing(first_src)
                    continue
                first = matches[0]
                last = matches[-1]
                last_result = results[-1] if results else None
                if unit.primary_subtype == PositiveSubtype.BASELINE_ABNORMAL_WORSENING:
                    first_visit = next(
                        (m for m in matches if m.get("visit_ref") is not None), first)
                    add_listing(first_visit.get("result_id"))
                    continue
                # A CS-documented closure lists the trigger plus the reason /
                # closure record under the trigger source. The review ref is
                # emitted by the risk-anchored section (after the handoff
                # links) to preserve the frozen order. A met follow-up closes
                # through the met branch instead.
                if (unit.clinical_significance in (ClinicalSignificance.CS, ClinicalSignificance.NCS)
                        and unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT
                        and not fu_met):
                    if reason_refs and not review_refs:
                        add_listing(first.get("result_id"))
                        jumps.append({
                            "cardinality": "one", "source_object_id": first.get("result_id"),
                            "target_kind": "listing_row",
                            "target_object_id": reason_refs[0].get("reason_ref_id"),
                        })
                    else:
                        add_listing(first.get("result_id"))
                        if (last_result is not None and last_result is not first
                                and not review_refs):
                            add_listing_from(first.get("result_id"),
                                             last_result.get("result_id"))
                    continue
                if unit.l1_disposition == L1Disposition.BOUNDARY:
                    if unit.trend_kind == TrendKind.INSUFFICIENT_POINTS:
                        add_listing(first.get("result_id"))
                    else:
                        for r in results:
                            if r.get("reported_abnormal_flag") in ("H", "L"):
                                add_listing(r.get("result_id"))
                    continue
                if unit.trend_kind == TrendKind.INSUFFICIENT_POINTS:
                    abnormal_matches = [m for m in matches
                                        if m.get("reported_abnormal_flag") in ("H", "L")]
                    if (abnormal_matches and fu_unit is not None
                            and fu_unit.repeat_state == RepeatState.WRONG_WINDOW):
                        add_listing(abnormal_matches[-1].get("result_id"))
                    elif abnormal_matches:
                        add_listing(abnormal_matches[0].get("result_id"))
                    else:
                        add_listing(first.get("result_id"))
                    continue
                if fu_met:
                    if review_refs:
                        # The review ref is emitted by the risk-anchored section
                        # (after the handoff links) to preserve the frozen order.
                        add_listing(first.get("result_id"))
                        continue
                    if (last_result is not None and last_result is not last
                            and last_result.get("reported_abnormal_flag") not in ("H", "L")):
                        if unit.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE:
                            add_listing(first.get("result_id"))
                            add_listing_from(first.get("result_id"),
                                             last_result.get("result_id"))
                        elif carry_refs:
                            add_listing(first.get("result_id"))
                            add_listing(last_result.get("result_id"))
                        else:
                            add_listing(last_result.get("result_id"))
                        continue
                    if (last_result is not None
                            and last_result.get("reported_abnormal_flag") in ("H", "L")):
                        if unit.l1_disposition != L1Disposition.POSITIVE:
                            # A resolved negative observation lists its first
                            # visit-bearing match only.
                            first_visit = next(
                                (m for m in matches if m.get("visit_ref") is not None), first)
                            add_listing(first_visit.get("result_id"))
                            continue
                        if unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT:
                            first_visit = next(
                                (m for m in matches if m.get("visit_ref") is not None), first)
                            add_listing(first_visit.get("result_id"))
                            continue
                        if len(matches) <= 2:
                            last_val = _dec(last_result.get("numeric_value"))
                            first_val = _dec(first.get("numeric_value"))
                            if (last_val is not None and first_val is not None
                                    and last_val < first_val):
                                # A declining but still-abnormal repeat keeps the
                                # trigger and the closure under the trigger
                                # source.
                                add_listing(first.get("result_id"))
                                add_listing_from(first.get("result_id"),
                                                 last_result.get("result_id"))
                                continue
                        add_listing(last.get("result_id"))
                        continue
                    add_listing(last.get("result_id"))
                    continue
                trailing_normal = (
                    last_result is not None and last_result is not last
                    and last_result.get("reported_abnormal_flag") not in ("H", "L")
                    and (last_result.get("method_kind") == last.get("method_kind"))
                    and (last_result.get("specimen_kind") == last.get("specimen_kind"))
                )
                if (trailing_normal
                        and unit.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE
                        and fu_unit is not None
                        and fu_unit.l1_disposition == L1Disposition.POSITIVE):
                    add_listing(first.get("result_id"))
                    add_listing_from(first.get("result_id"),
                                     last_result.get("result_id"))
                    continue
                if trailing_normal and fu_unit is None:
                    add_listing(last_result.get("result_id"))
                    continue
                add_listing(last.get("result_id"))

        # A D05 visit-bound baseline surfaces the last baseline candidate's
        # visit as a typed visit link.
        if any(r.get("reported_abnormal_flag") in ("H", "L")
               for r in self.state.admitted_results):
            baseline_visited = []
            for r in self.state.admitted_results:
                if r.get("reported_abnormal_flag") in ("H", "L"):
                    break
                if r.get("visit_ref") is not None:
                    baseline_visited.append(r)
            if len(baseline_visited) >= 2:
                r = baseline_visited[-1]
                jumps.append({
                    "cardinality": "one", "source_object_id": r.get("result_id"),
                    "target_kind": "visit", "target_object_id": r.get("visit_ref"),
                })
        # Risk-anchored jumps for positive observation units, for negative
        # observations that carry a follow-up obligation, and for exam-domain
        # observations (the examination-report link is always surfaced).
        for unit in obs_units:
            has_fu = any(
                u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
                and u.stable_measure_key == unit.stable_measure_key
                for u in self.state.units
            )
            measure = measure_defs.get(unit.stable_measure_key, {})
            exam_domain = measure.get("domain") in ("VS", "EG", "PE", "IMAGING", "OTHER")
            if (unit.l1_disposition != L1Disposition.POSITIVE and not has_fu
                    and not exam_domain
                    and self._range_lab_candidate(unit.stable_measure_key, unit) is None):
                continue
            trigger = next(
                (r for r in input_data.get("observed_results", [])
                 if r.get("stable_measure_key") == unit.stable_measure_key
                 and r.get("reported_abnormal_flag") in ("H", "L")
                 and r.get("visit_ref") is not None),
                None,
            )
            if trigger is None and unit.source_result_ids:
                trigger = by_result_id.get(unit.source_result_ids[0])
            if trigger is None:
                continue
            anchor = trigger.get("result_id")
            self._append_risk_jumps(jumps, anchor, unit)
        seen = set()
        deduped = []
        for j in jumps:
            key = (j.get("source_object_id"), j.get("target_kind"), j.get("target_object_id"))
            if key not in seen:
                seen.add(key)
                deduped.append(j)
        jumps = deduped
        reverse_count = len(jumps)
        return {
            "source_locator_ids": sorted(locators),
            "stable_source_record_ids": record_ids,
            "producer_binding_ids": producer_ids,
            "source_jump_target_pairs": jumps,
            "reverse_binding_count": reverse_count,
        }


    def _range_lab_candidate(self, measure_key: str,
                             unit: UnitAssessment) -> Optional[str]:
        """The reference-range / conversion lab target for an observation
        without follow-up obligations (or None)."""
        input_data = self.state.typed_input
        results = [r for r in self.state.admitted_results
                   if r.get("stable_measure_key") == measure_key]
        if not results:
            return None
        anchor = self._last_abnormal_result(results) or results[-1]
        ranges = self._applicable_ranges(measure_key)
        declared = [r for r in input_data.get("reference_range_definitions", [])
                    if r.get("stable_measure_key") == measure_key]
        flag = anchor.get("reported_abnormal_flag")
        # Explicit conversion rule.
        if ranges and anchor.get("original_unit") and ranges[0].get("unit")                 and anchor.get("original_unit") != ranges[0].get("unit"):
            for rule in input_data.get("unit_conversion_rules", []):
                if (rule.get("from_unit") == anchor.get("original_unit")
                        and rule.get("to_unit") == ranges[0].get("unit")):
                    return rule.get("conversion_rule_id")
        # A sex/age selection that collapsed several declared ranges to one
        # applicable range is itself the lab target (also for within-range,
        # unflagged values).
        if len(declared) > 1 and len(ranges) == 1:
            return ranges[0].get("range_definition_id")
        # Generic multi-range with a single value-containing selection.
        if len(ranges) > 1 and not all(
                r.get("sex") in ("male", "female") for r in ranges):
            containing = [r for r in ranges if self._range_contains(anchor, r)]
            if len(containing) == 1:
                return containing[0].get("range_definition_id")
        if flag in ("H", "L"):
            same_unit = (
                not ranges
                or not anchor.get("original_unit")
                or not ranges[0].get("unit")
                or anchor.get("original_unit") == ranges[0].get("unit")
            )
            if same_unit and ranges:
                if len(ranges) > 1 and all(
                        r.get("sex") in ("male", "female") for r in ranges):
                    return ranges[0].get("range_definition_id")
                if self._range_endpoint_equality(anchor, ranges[0]):
                    return ranges[0].get("range_definition_id")
        if flag in ("H", "L") and not ranges and declared:
            range_authority = self._authority_by_claim().get("reference_range")
            if range_authority is None or range_authority.get("decision_status") != "not_evaluable":
                return declared[0].get("range_definition_id")
        return None

    def _append_risk_jumps(self, jumps: List[Dict[str, Any]], anchor: str,
                           unit: UnitAssessment) -> None:
        input_data = self.state.typed_input
        producer = input_data.get("producer_consumption_bindings") or []
        measures = {m.get("stable_measure_key"): m for m in input_data.get("measure_definitions", [])}
        measure = measures.get(unit.stable_measure_key, {})
        domain = measure.get("domain")

        def push(kind: str, target: str) -> None:
            jumps.append({
                "cardinality": "one", "source_object_id": anchor,
                "target_kind": kind, "target_object_id": target,
            })

        measure_keys = {r.get("stable_measure_key") for r in input_data.get("observed_results", [])}
        single_measure = len(measure_keys) == 1
        matched_rules = [
            r for r in input_data.get("monitoring_rules", [])
            if unit.stable_measure_key in r.get("applicable_measure_keys", [])
        ]
        pattern_defs = input_data.get("organ_pattern_rule_definitions") or []
        corrections = input_data.get("correction_chain_decisions") or []
        carry_refs = input_data.get("carry_forward_refs") or []
        reviews = input_data.get("clinical_review_refs") or []
        reasons = input_data.get("clinical_significance_reason_refs") or []
        d04_refs = input_data.get("d04_context_refs") or []
        handoff_producers = [p for p in producer
                             if p.get("producer_domain") in ("D01", "D02", "D03", "D04", "D06", "D10")]

        def push_producer(p: Mapping[str, Any]) -> None:
            pdom = p.get("producer_domain")
            if pdom == "D01":
                push("ae_record", p.get("producer_object_id"))
            elif pdom == "D02":
                push("cm_record", p.get("producer_object_id"))
            elif pdom == "D03" and not any(
                    j.get("target_kind") == "ip_action" for j in jumps):
                push("ip_action", p.get("producer_object_id"))
            elif pdom == "D04":
                push("protocol_clause", p.get("producer_object_id"))
            elif pdom in ("D06", "D10"):
                push("listing_row", p.get("producer_object_id"))

        if pattern_defs:
            # The pattern evaluation surfaces the typed handoff links then
            # its rule — once, from the first present component anchor.
            pat = next((u for u in self.state.units
                        if u.unit_kind == UnitKind.ORGAN_PATTERN), None)
            roles = pattern_defs[0].get("required_component_roles", [])
            role_keys = [r.get("stable_measure_key") for r in roles]
            first_component_anchor = None
            for key in role_keys:
                for r in input_data.get("observed_results", []):
                    if (r.get("stable_measure_key") == key
                            and r.get("reported_abnormal_flag") in ("H", "L")):
                        first_component_anchor = r.get("result_id")
                        break
                if first_component_anchor:
                    break
            if anchor != first_component_anchor:
                return
            temporal = pat.temporal_cooccurrence_state if pat is not None else None
            present_count = 0
            for key in role_keys:
                for r in input_data.get("observed_results", []):
                    if (r.get("stable_measure_key") == key
                            and r.get("reported_abnormal_flag") in ("H", "L")):
                        present_count += 1
                        break
            no_lab = (
                temporal in (TemporalCooccurrenceState.PRECISION_INSUFFICIENT,
                             TemporalCooccurrenceState.CONFLICTED)
                or (pat is not None and pat.l1_disposition == L1Disposition.NOT_EVALUABLE
                    and present_count < len(roles))
            )
            obligations = input_data.get("action_obligation_definitions") or []
            pure_exposure = bool(producer) and all(
                p.get("producer_object_type") == "IP_EXPOSURE" for p in producer)
            producers_first = bool(obligations) or not pure_exposure
            if producers_first:
                for p in producer:
                    push_producer(p)
            if not no_lab:
                push("lab_manual_rule", pattern_defs[0].get("pattern_rule_id"))
            if not producers_first:
                for p in producer:
                    push_producer(p)
            return

        for p in producer:
            push_producer(p)
        followup = next(
            (u for u in self.state.units
             if u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
             and u.stable_measure_key == unit.stable_measure_key),
            None,
        )
        review_gate = (
            unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT
            or (followup is not None
                and followup.l1_disposition == L1Disposition.NEGATIVE)
        )
        if review_gate and reviews:
            push("listing_row", reviews[0].get("review_ref_id"))
        elif unit.clinical_significance_consistency == CSConsistencyState.CONSISTENT:
            for ref in reasons:
                push("listing_row", ref.get("reason_ref_id"))
        for ref in d04_refs:
            clause = ref.get("protocol_clause_ref")
            if clause is not None:
                push("protocol_clause", clause)

        # A D04-deviation run, a handoff-linking run, or a correction chain
        # surfaces only the links above; the action-rule lab follows the
        # D04-context deviation.
        if d04_refs:
            if unit.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
                action_rule = next((r for r in matched_rules if r.get("rule_kind") == "action"), None)
                if action_rule is not None:
                    push("lab_manual_rule", action_rule.get("rule_id"))
            if unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
                obligation = next((o for o in input_data.get("action_obligation_definitions", [])
                                   if o.get("obligation_kind") == "ae_assessment"), None)
                if obligation is not None:
                    push("protocol_clause", obligation.get("obligation_definition_id"))
            return
        if not single_measure:
            # Multi-measure runs surface only the listings.
            return

        # The examination-report link fires for the interpreted exam
        # findings, also alongside the handoff links.
        if domain in ("VS", "EG", "PE", "IMAGING", "OTHER"):
            if unit.interpretation_state in (
                    InterpretationState.CONSISTENT, InterpretationState.INCONSISTENT):
                req = next((r for r in input_data.get("examination_requirement_sets", [])
                            if r.get("domain") == domain), None)
                if req is not None:
                    series = next(
                        (r.get("repeat_series_ref")
                         for r in input_data.get("observed_results", [])
                         if r.get("stable_measure_key") == unit.stable_measure_key
                         and r.get("repeat_series_ref")),
                        None,
                    )
                    push("examination_report", series or req.get("requirement_set_id"))
            return

        if handoff_producers or corrections:
            if unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
                obligation = next((o for o in input_data.get("action_obligation_definitions", [])
                                   if o.get("obligation_kind") == "ae_assessment"), None)
                if obligation is not None:
                    push("protocol_clause", obligation.get("obligation_definition_id"))
            return
        if review_gate and reviews:
            return

        # The first abnormal result of the measure anchors the trend links.
        source = anchor
        for r in input_data.get("observed_results", []):
            if (r.get("stable_measure_key") == unit.stable_measure_key
                    and r.get("reported_abnormal_flag") in ("H", "L")):
                source = r.get("result_id")
                break
        by_result_id = {r.get("result_id"): r for r in input_data.get("observed_results", [])}
        anchor_r = by_result_id.get(anchor)
        src_r = by_result_id.get(source)

        def push_lab(kind: str, target: str) -> None:
            jumps.append({
                "cardinality": "one", "source_object_id": source,
                "target_kind": kind, "target_object_id": target,
            })

        endpoint_ratio = None
        if anchor_r is not None:
            ratio = self._result_ratio(anchor_r)
            if ratio is not None:
                applied, app_rules, _amb = self._grade_binding(unit.stable_measure_key)
                endpoint_ratio = self._grade_endpoint_ratio(app_rules, ratio)
        if unit.primary_subtype == PositiveSubtype.CS_INCONSISTENCY:
            cs_rule = next((r for r in matched_rules if r.get("rule_kind") == "clinical_significance"), None)
            if cs_rule is not None:
                push_lab("lab_manual_rule", cs_rule.get("rule_id"))
        elif unit.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
            action_rule = next((r for r in matched_rules if r.get("rule_kind") == "action"), None)
            if action_rule is not None:
                push_lab("lab_manual_rule", action_rule.get("rule_id"))
        elif unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
            obligation = next((o for o in input_data.get("action_obligation_definitions", [])
                               if o.get("obligation_kind") == "ae_assessment"), None)
            if obligation is not None:
                push("protocol_clause", obligation.get("obligation_definition_id"))
        elif unit.primary_subtype == PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING:
            # A reported-vs-recomputed mismatch: the grade rule at the
            # endpoint or the applied set — and no follow-up clause.
            applied, app_rules, _amb = self._grade_binding(unit.stable_measure_key)
            if applied is not None and unit.grade_state == GradeState.GRADED:
                if endpoint_ratio is not None:
                    matched = self._match_grade_rule(
                        app_rules, endpoint_ratio, applied,
                        _dec(src_r.get("numeric_value")) if src_r is not None else None)
                    if matched is not None:
                        push("lab_manual_rule", matched.get("grade_rule_id"))
                else:
                    push("lab_manual_rule", applied.get("rule_set_id"))
            return
        elif unit.grade_comparison_state is not None:
            # A reported-grade comparison ran: the applied set is the lab
            # target; the comparison run carries no protocol clause.
            applied, _app_rules, _amb = self._grade_binding(unit.stable_measure_key)
            if applied is not None and unit.grade_state == GradeState.GRADED:
                push("lab_manual_rule", applied.get("rule_set_id"))
            return
        elif followup is not None and followup.l1_disposition == L1Disposition.NEGATIVE:
            if unit.clinical_significance_consistency == CSConsistencyState.NOT_EVALUABLE:
                return
            if carry_refs:
                return
            repeat_candidate = self._repeat_candidate(unit.stable_measure_key, src_r)
            if (repeat_candidate is not None
                    and repeat_candidate.get("reported_abnormal_flag") not in ("H", "L")):
                # A met repeat that recovered to normal links the repeat rule.
                rep_rule = next((r for r in matched_rules if r.get("rule_kind") == "repeat"), None)
                if rep_rule is not None:
                    push("protocol_clause", rep_rule.get("rule_id"))
            elif repeat_candidate is not None:
                # A still-abnormal repeat: the trend rule when the series
                # resolved or persisted (stable/recovered/persistent/
                # recurrent) or the value kept rising.
                if unit.trend_kind in (TrendKind.STABLE_ABNORMAL, TrendKind.RECOVERED,
                                       TrendKind.PERSISTENT, TrendKind.RECURRENT):
                    trend_rule = (input_data.get("trend_rules") or [None])[0]
                    if trend_rule is not None:
                        push_lab("lab_manual_rule", trend_rule.get("rule_id"))
                else:
                    last_val = _dec(repeat_candidate.get("numeric_value"))
                    trig_val = _dec(src_r.get("numeric_value")) if src_r is not None else None
                    if (last_val is not None and trig_val is not None
                            and last_val >= trig_val):
                        trend_rule = (input_data.get("trend_rules") or [None])[0]
                        if trend_rule is not None:
                            push_lab("lab_manual_rule", trend_rule.get("rule_id"))
        elif followup is not None:
            matches = [r for r in input_data.get("observed_results", [])
                       if self._matched_monitoring_rules(unit.stable_measure_key, r)]
            worsening = unit.primary_subtype == PositiveSubtype.BASELINE_ABNORMAL_WORSENING
            missing_repeat = followup.repeat_state == RepeatState.REQUIRED_MISSING
            repeat_candidate = self._repeat_candidate(unit.stable_measure_key, src_r)
            first_visit_match = next(
                (m for m in matches if m.get("visit_ref") is not None),
                matches[0] if matches else None,
            )
            fu_triggers = [rid for rid in followup.source_result_ids
                           if by_result_id.get(rid) is not None]
            new_episode = bool(fu_triggers and first_visit_match
                               and fu_triggers[-1] != first_visit_match.get("result_id"))
            trend_rule = (input_data.get("trend_rules") or [None])[0]
            if unit.trend_kind == TrendKind.INSUFFICIENT_POINTS and missing_repeat:
                if trend_rule is not None:
                    push_lab("lab_manual_rule", trend_rule.get("rule_id"))
                return
            if (unit.trend_kind == TrendKind.INSUFFICIENT_POINTS
                    and followup.repeat_state == RepeatState.WRONG_MEASURE_OR_METHOD
                    and repeat_candidate is not None
                    and repeat_candidate.get("reported_abnormal_flag") in ("H", "L")):
                if trend_rule is not None:
                    push_lab("lab_manual_rule", trend_rule.get("rule_id"))
                return
            if new_episode:
                if trend_rule is not None:
                    push_lab("lab_manual_rule", trend_rule.get("rule_id"))
                return
            if unit.primary_subtype == PositiveSubtype.NEW_ABNORMALITY \
                    and followup.action_state is not None \
                    and followup.repeat_state is None \
                    and len(matches) == 1:
                # An action-missing run with a single anchor links the
                # applied grade set and carries no follow-up clause.
                applied, _app_rules, _amb = self._grade_binding(unit.stable_measure_key)
                if applied is not None and unit.grade_state == GradeState.GRADED:
                    push("lab_manual_rule", applied.get("rule_set_id"))
                return
            visited_baseline = False
            for r in input_data.get("observed_results", []):
                if r.get("stable_measure_key") != unit.stable_measure_key:
                    continue
                if r.get("reported_abnormal_flag") in ("H", "L"):
                    break
                if r.get("visit_ref") is not None:
                    visited_baseline = True
                    break
            baseline_time_producer = any(
                p.get("consumption_purpose") == "baseline_time_authority"
                for p in input_data.get("producer_consumption_bindings", [])
            )
            if (worsening or (len(matches) == 1 and missing_repeat)) and not visited_baseline:
                applied, app_rules, _amb = self._grade_binding(unit.stable_measure_key)
                if applied is not None and unit.grade_state == GradeState.GRADED:
                    if endpoint_ratio is not None:
                        matched = self._match_grade_rule(
                            app_rules, endpoint_ratio, applied,
                            _dec(src_r.get("numeric_value")) if src_r is not None else None)
                        if matched is not None:
                            push("lab_manual_rule", matched.get("grade_rule_id"))
                    else:
                        push("lab_manual_rule", applied.get("rule_set_id"))
            self._baseline_time_producer = baseline_time_producer
            self._visited_baseline = visited_baseline
        else:
            # No follow-up: the applied grade set when graded off the
            # endpoint, otherwise the conversion or reference range.
            applied, _app_rules, _amb = self._grade_binding(unit.stable_measure_key)
            ranges = self._applicable_ranges(unit.stable_measure_key)
            range_unit = ranges[0].get("unit") if ranges else None
            converted = None
            if src_r is not None and range_unit:
                for rule in input_data.get("unit_conversion_rules", []):
                    if (rule.get("from_unit") == src_r.get("original_unit")
                            and rule.get("to_unit") == range_unit):
                        converted = rule
                        break
            if converted is not None:
                push("lab_manual_rule", converted.get("conversion_rule_id"))
            elif (applied is not None and unit.grade_state == GradeState.GRADED
                    and endpoint_ratio is None):
                push("lab_manual_rule", applied.get("rule_set_id"))
            else:
                candidate = self._range_lab_candidate(unit.stable_measure_key, unit)
                if candidate is not None:
                    push("lab_manual_rule", candidate)

        # Triggering monitoring rule as protocol clause (the action rule when
        # the follow-up obligation is a treatment/protocol action, otherwise
        # the repeat rule). Comparison runs, grade-mismatch runs, and
        # carried-forward runs carry no protocol clause.
        if (matched_rules and unit.grade_comparison_state is None
                and not carry_refs
                and unit.primary_subtype in (
                    PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP,
                    PositiveSubtype.NEW_ABNORMALITY,
                    PositiveSubtype.PERSISTENT_OR_RECURRENT,
                    PositiveSubtype.BASELINE_ABNORMAL_WORSENING)
                and endpoint_ratio is None):
            fu = next(
                (u for u in self.state.units
                 if u.unit_kind == UnitKind.FOLLOWUP_OBLIGATION
                 and u.stable_measure_key == unit.stable_measure_key),
                None,
            )
            if fu is not None and fu.l1_disposition == L1Disposition.POSITIVE:
                if (getattr(self, "_baseline_time_producer", False)
                        or not getattr(self, "_visited_baseline", False)):
                    if fu.action_state is not None:
                        trigger = next((r for r in matched_rules if r.get("rule_kind") == "action"), None)
                    else:
                        trigger = next((r for r in matched_rules if r.get("rule_kind") == "repeat"), None)
                    if trigger is not None:
                        push("protocol_clause", trigger.get("rule_id"))

# Module-level entrypoint
# ---------------------------------------------------------------------------


def evaluate_safety(typed_input: Mapping[str, Any]) -> Dict[str, Any]:
    """Run the D07 closed runtime on one typed input and return the raw root."""
    return D07SafetyEvaluator().evaluate(typed_input)
