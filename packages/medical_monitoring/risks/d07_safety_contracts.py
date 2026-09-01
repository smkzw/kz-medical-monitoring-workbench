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
