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

from .d07_safety_contracts import *
from .d07_safety_contracts import _RunState
from .d07_safety_integrity_mixin import D07SafetyIntegrityMixin
from .d07_safety_observation_mixin import D07SafetyObservationMixin
from .d07_safety_followup_mixin import D07SafetyFollowupMixin
from .d07_safety_priority_mixin import D07SafetyPriorityMixin
from .d07_safety_output_mixin import D07SafetyOutputMixin
from .d07_safety_jumps_mixin import D07SafetyJumpsMixin


class D07SafetyEvaluator(
    D07SafetyIntegrityMixin,
    D07SafetyObservationMixin,
    D07SafetyFollowupMixin,
    D07SafetyPriorityMixin,
    D07SafetyOutputMixin,
    D07SafetyJumpsMixin,
):
    """Deterministic closed runtime for the D07 slice."""

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

def evaluate_safety(typed_input: Mapping[str, Any]) -> Dict[str, Any]:
    """Run the D07 closed runtime on one typed input and return the raw root."""
    return D07SafetyEvaluator().evaluate(typed_input)
