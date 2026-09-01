"""Immutable D10 evaluation result records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class D10TraceLeaf:
    trace_kind: str
    stable_core_ref: Optional[str]
    content_identity: str
    replay_byte_equal: bool
    terminal_state: str


@dataclass(frozen=True)
class D10SourceLeaf:
    member_ref: str
    source_locator_ref: Optional[str]
    resolution_state: str
    site_stable_id: str
    subject_stable_id: Optional[str]


@dataclass(frozen=True)
class D10ForbiddenLeaf:
    leaf_kind: str
    expected_disposition: Optional[str]
    gate_kind: Optional[str]
    change_kind: Optional[str]
    reason_code: str


@dataclass(frozen=True)
class D10UnitResult:
    """One medical expected-set unit (contract section 9 five dispositions)."""

    signal_kind: str
    l1_disposition: str
    primary_reason: str
    stable_core_ref: str
    numerator_member_count: int
    individual_risk_count: int
    affected_subject_count: int
    event_or_outcome_count: int
    center_pattern_count: int
    affected_site_count: int
    denominator_kind: str
    denominator_value: int
    denominator_state: str
    estimate_kind: str
    project_signal_count: int
    clue_count: int
    query_count: int
    risk_handoff_count: int
    change_kind: str
    change_cause: Optional[str]
    lineage_relation: str
    handoff_action: Optional[str]
    rate_projection_state: str
    hidden_member_count: int
    hidden_site_count: int
    deep_link_target_count: int
    member_expansion_state: str
    query_redundancy_decision: str
    pd_wording_state: str
    audience_injection_blocked: bool
    counterevidence_rule_matches: int
    model_evidence_role: Optional[str]
    hotspot_member_refs: Tuple[str, ...] = ()


@dataclass(frozen=True)
class D10GateResult:
    gate_kind: str
    leaf_kind: str
    signal_kind: str
    reason_codes: Tuple[str, ...]
    denominator_value: int = 0
    audience_injection_blocked: bool = False


@dataclass(frozen=True)
class D10RunResult:
    """Complete deterministic outcome of one typed run."""

    disposition_or_gate: str
    primary_reason: str
    unit: Optional[D10UnitResult]
    gate: Optional[D10GateResult]
    trace: Tuple[D10TraceLeaf, ...]
    source: Tuple[D10SourceLeaf, ...]
    forbidden: Tuple[D10ForbiddenLeaf, ...]
    evaluation_content_identity: str
    stable_core_ref: Optional[str]
    replay_byte_equal: bool
    terminal_state: str
