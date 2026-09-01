"""R5 S2 W2 -- real R4 typed-pipeline synthetic authority-packet builder.

Derives one frozen :class:`mm_r5.s2_contracts.R5S2AuthorityPacket` from a
synthetic D10 envelope through the REAL R4 typed pipeline (read-only):

* :mod:`medical_monitoring.risks.d10_typed_input` ``build_typed_input`` turns
  the synthetic envelope dict into the immutable
  :class:`mm_r4.d10_contracts.D10TypedInput` (package-native contracts);
* :mod:`mm_r4.d10_evaluator` ``evaluate`` runs the deterministic evaluator
  against a :class:`mm_r4.d10_contracts.D10EvaluationAuthority` derived from
  the same envelope (this module reads no frozen artifact files -- the
  envelope and its authority are both built inline, offline);
* :mod:`mm_r4.d10_projection` ``project_d10_run`` emits the projection
  version, project projection, risk marker and one-hop deep-link target;
* the R5 S1 read-only :func:`mm_r5.authority_adapter.build_authority_receipt`
  binds the accepted :class:`mm_r5.contracts.R5AuthorityReceipt`;
* :mod:`mm_r4.ensemble` ``run_ensemble`` (real deterministic closure)
  produces the two worker verifications, the visible conflict and the
  independent adjudication from the two isolated worker attempts/outputs;
* the packet-only D10 :class:`mm_r4.d10_contracts.ModelEvidence` and every
  S2 binding are then derived from those real pipeline objects.

Every packet leaf derives from an actual typed pipeline object or from a
closed typed relation; nothing branches on project/case/fixture/test ids,
filenames, synthetic sentinels, oracles, indexes, mutation classes or hash
naming conventions, and nothing copies an expected output or a verifier
decision (forbidden semantic branches of the frozen packet schema).  No
``assert`` is used in a decision path: every fail-closed gate raises
:class:`S2AuthorityBuilderError` or a typed contract error explicitly.

Synthetic/offline boundary
--------------------------
* The packet is a *supplemental* synthetic/offline test authority only
  (``authority_mode = synthetic_offline_test_only``); it never claims
  clinical truth, real-project, model, product, production or security
  eligibility.
* The temporal visit/event/risk-anchor chain is synthetic supplemental test
  authority, not an R4 public temporal authority; it never fabricates dates
  and never uses a nearest-match fallback.
* ``measure_refs`` (S3), ``pending_date_refs`` / ``phase_band_refs`` (S5)
  and the public Inspector ``worker_output_refs`` / ``support_evidence_refs``
  / ``counterevidence_refs`` / ``query_draft_ref`` (S4) stay exactly
  empty/null and are never smuggled into the public R4 authority.

One derived transform (documented): the R4 deep-link builder records
``D10DeepLinkTarget.visibility_decision_hash`` as the envelope's
``decision_id`` because it does not know the R5 S1 visibility-decision hash
recipe.  The packet contract requires that hash to equal the S1 receipt's
canonical ``visibility_decision_hash``, so the builder rebinds that one field
to the receipt value.  ``link_id`` is unaffected (the R4 link-id recipe does
not include ``visibility_decision_hash``), so the target is identical.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Mapping, NamedTuple, Optional, Tuple

from ...risks.d10_contracts import (
    D10EvaluationAuthority,
    D10TypedInput,
    EvidenceRef,
    Member,
    ModelEvidence,
    SourceRevisionPair,
    d10_canonical_json,
    d10_content_hash,
    d10_sha256_text,
)
from ...risks.d10_evaluator import D10RunResult, evaluate
from ...risks.d10_typed_input import build_typed_input
from ..d10 import (
    D10DeepLinkTarget,
    D10ProjectProjection,
    D10RiskMarker,
    D10ProjectionVersion,
    build_d10_deep_links,
    build_d10_project_projection,
    build_d10_projection_version,
    build_d10_risk_marker,
)
from ...risks.ensemble import (
    Adjudicator,
    AnalysisAttempt,
    BaselineAssessment,
    EvidenceDigestContext,
    Finding,
    ReferenceBaselineItem,
    WorkerAnalysisOutput,
    run_ensemble,
    worker_output_content_hash,
)
from .authority_adapter import (
    DEFAULT_D10_AUTHORITY_ADAPTER_VARIANT,
    build_authority_receipt,
)
from .contracts import R5AuthorityReceipt
from .s2_contracts import (
    AUTHORITY_MODE_S2,
    STAGE_STATUS_S2,
    R5S2AuthorityPacket,
    R5S2CenterBinding,
    R5S2InspectorBinding,
    R5S2ProjectRiskBinding,
    R5S2SourceBinding,
    R5S2TemporalBinding,
    S2_DOMAINS,
    S2_SEVERITIES,
    expected_model_binding_hash,
    expected_model_output_hash,
    expected_model_output_identity,
    s2_canonical_json,
    s2_object_content_hash,
    s2_sha256,
    validate_s2_authority_packet,
)

# ---------------------------------------------------------------------------
# Fail-closed builder gate
# ---------------------------------------------------------------------------


class S2AuthorityBuilderError(Exception):
    """A fail-closed builder gate failed: the real pipeline did not yield the
    authority objects a frozen S2 packet requires (non-positive evaluation,
    missing risk marker, non-locatable deep link).  No packet is emitted."""


# ---------------------------------------------------------------------------
# Synthetic envelope identity (neutral, meaningful; never test/case ids)
# ---------------------------------------------------------------------------

SYNTHETIC_PROJECT_REF = "S2-PROJECT-001"
SYNTHETIC_RUN_REF = "S2-RUN-001"
SYNTHETIC_SNAPSHOT_REF = "S2-SNAPSHOT-001"
SYNTHETIC_SITE_REF = "S2-SITE-CENTER-001"
SYNTHETIC_SUBJECT_REP = "S2-SUBJ-REP-001"
SYNTHETIC_PATTERN_REF = "S2-PAT-CENTER-001"
SYNTHETIC_INDIVIDUAL_REFS: Tuple[str, ...] = (
    "S2-RISK-CENTER-001", "S2-RISK-CENTER-002")
SYNTHETIC_SOURCE_LOCATOR = "S2-LOC-SOURCE-001"
SYNTHETIC_COVERAGE_LOCATOR = "S2-LOC-COVERAGE-001"
SYNTHETIC_SOURCE_REVISION = "S2-REV-SOURCE-001"
SYNTHETIC_SOURCE_FILE = "synthetic_source/s2_packet_source.json"
SYNTHETIC_SOURCE_ROW_CELL = "sheet:1;row:1"
SYNTHETIC_SOURCE_LINEAGE = "S2-LINE-SOURCE-001"
#: Closed S2 risk/outcome domain carried by the synthetic signal definition
#: (``SignalDefinition.risk_or_outcome_domain``).  The R4 evaluator carries it
#: as a typed fact (not a gated enum), so the packet domain derives exactly
#: from the real signal definition.
SYNTHETIC_DOMAIN = "symptom_efficacy"
SYNTHETIC_CUTOFF_REF = "S2-CUTOFF-001"
SYNTHETIC_WINDOW_START = "2026-01-01"
SYNTHETIC_WINDOW_END = "2026-06-30"
SYNTHETIC_WINDOW_REF = "2026-01-01..2026-06-30"
#: Exact synthetic event dates (never nearest-matched, never fabricated as
#: a replacement for an absent actual date).
SYNTHETIC_EVENT_START = date(2026, 3, 15)
SYNTHETIC_EVENT_END = date(2026, 3, 17)
SYNTHETIC_ACTUAL_DATE = date(2026, 3, 15)
SYNTHETIC_RISK_TYPE_ZH = "症状风险信号"
SYNTHETIC_EVENT_SUBTYPE = "symptom"
SYNTHETIC_VISIT_REF = "S2-VISIT-001"
SYNTHETIC_EVENT_REF = "S2-EVENT-001"
SYNTHETIC_RISK_ANCHOR_REF = "S2-ANCHOR-001"
SYNTHETIC_SPINE_REF = "S2-SPINE-001"

#: Synthetic ensemble identity (shared question/input version).
SYNTHETIC_ENSEMBLE_ID = "S2-ENSEMBLE-001"
SYNTHETIC_MODEL_ID = "synthetic-baseline-review-v1"
SYNTHETIC_MODEL_VERSION = "1.0"


class _WorkerSpec(NamedTuple):
    """Explicit, named worker specification: the attempt/binding/session/
    artifact identities AND the finding support direction are semantic facts
    of the spec itself -- never derived from index, order or id naming."""

    attempt_id: str
    binding_id: str
    session_id: str
    artifact_ref: str
    supports_finding: bool


#: The two isolated workers: worker-001 asserts the center risk signal is
#: SUPPORTED in the rechecked source, worker-002 asserts it is NOT supported
#: (absent) -- the explicit mutual negation that keeps the S2 conflict
#: visible.  Swapping the tuple order must not change semantics (each spec
#: carries its own support direction).
WORKER_SPECS: Tuple[_WorkerSpec, ...] = (
    _WorkerSpec(
        attempt_id="S2-ATTEMPT-WORKER-001",
        binding_id="S2-BIND-WORKER-001",
        session_id="S2-SESSION-WORKER-001",
        artifact_ref="S2-ARTIFACT-WORKER-001",
        supports_finding=True,
    ),
    _WorkerSpec(
        attempt_id="S2-ATTEMPT-WORKER-002",
        binding_id="S2-BIND-WORKER-002",
        session_id="S2-SESSION-WORKER-002",
        artifact_ref="S2-ARTIFACT-WORKER-002",
        supports_finding=False,
    ),
)
#: Derived attempt-id set (kept for the frozen constant surface).
SYNTHETIC_ATTEMPT_IDS: Tuple[str, ...] = tuple(
    spec.attempt_id for spec in WORKER_SPECS)

SYNTHETIC_ADJUDICATOR_BINDING = "S2-ADJ-BIND-001"
SYNTHETIC_ADJUDICATOR_SESSION = "S2-ADJ-SESSION-001"
SYNTHETIC_BASELINE_ITEM = "S2-BASELINE-ITEM-001"
SYNTHETIC_CLAIMED_IDENTITY = "S2-CLAIM-CENTER-SIGNAL-001"
SYNTHETIC_FINDING_IDENTITY = "S2-RISK-SIGNAL-001"
SYNTHETIC_RULE_ID = "S2-RULE-POS-001"
SYNTHETIC_RULE_VERSION = "1.0"
SYNTHETIC_MODEL_EVIDENCE_ID = "S2-ME-001"
SYNTHETIC_RETURN_STATE_KEY = "inspector_center"

#: Immutable supplemental authority for the pattern descendants.  D10 cannot
#: carry both a center-pattern parent and its individual descendants in one
#: numerator without correctly failing ``d09_parent_descendant_duplication``;
#: S2 therefore freezes the descendants as actual R4 ``Member`` objects.
#: Callers cannot replace this authority with a second registry.
FROZEN_INDIVIDUAL_MEMBERS: Tuple[Member, ...] = (
    Member(
        member_ref="S2-RISK-CENTER-001",
        member_kind="individual_risk",
        aggregation_plane="individual",
        producer_domain="D01",
        member_scope_state="in_scope",
        site_stable_id=SYNTHETIC_SITE_REF,
        subject_stable_id="S2-SUBJ-001",
        monitoring_priority="high",
        accepted_current_state="accepted_current",
        locator_resolution_state="locatable",
        source_locator_refs=(SYNTHETIC_SOURCE_LOCATOR,),
        descendant_member_refs=(),
        descendant_set_hash=None,
        treatment_role_ref=None,
    ),
    Member(
        member_ref="S2-RISK-CENTER-002",
        member_kind="individual_risk",
        aggregation_plane="individual",
        producer_domain="D02",
        member_scope_state="in_scope",
        site_stable_id=SYNTHETIC_SITE_REF,
        subject_stable_id="S2-SUBJ-002",
        monitoring_priority="medium",
        accepted_current_state="accepted_current",
        locator_resolution_state="locatable",
        source_locator_refs=(SYNTHETIC_SOURCE_LOCATOR,),
        descendant_member_refs=(),
        descendant_set_hash=None,
        treatment_role_ref=None,
    ),
)

#: Closed producer domains required by the synthetic signal definition
#: (all covered/complete by the envelope coverage set).
_REQUIRED_PRODUCER_DOMAINS: Tuple[str, ...] = ("D01", "D02", "D03", "D04")

_SEVERITY_RANK: Mapping[str, int] = {"high": 2, "medium": 1, "low": 0}


def _h(value: Any) -> str:
    """S2 canonical content hash of any value (the packet recipe)."""
    return s2_sha256(s2_canonical_json(value).encode("utf-8"))


# ---------------------------------------------------------------------------
# Synthetic D10 envelope (the "synthetic D10 envelope" the packet derives)
# ---------------------------------------------------------------------------


def build_synthetic_d10_envelope_dict() -> Dict[str, Any]:
    """Deterministic synthetic D10 envelope as a catalog-style typed-input
    dict (same shape the R4 test-only adapter accepts)."""
    members = [
        {
            "member_ref": SYNTHETIC_PATTERN_REF,
            "member_kind": "center_pattern",
            "aggregation_plane": "site_pattern",
            "producer_domain": "D09",
            "member_scope_state": "in_scope",
            "site_stable_id": SYNTHETIC_SITE_REF,
            "subject_stable_id": SYNTHETIC_SUBJECT_REP,
            "monitoring_priority": "high",
            "accepted_current_state": "accepted_current",
            "locator_resolution_state": "locatable",
            "source_locator_refs": [SYNTHETIC_SOURCE_LOCATOR],
            "descendant_member_refs": list(SYNTHETIC_INDIVIDUAL_REFS),
            "descendant_set_hash": None,
            "treatment_role_ref": None,
        },
    ]
    pattern_member, = members
    pattern_member["descendant_set_hash"] = d10_sha256_text(d10_canonical_json(
        sorted(SYNTHETIC_INDIVIDUAL_REFS)))
    evidence_refs = [{
        "locator_id": SYNTHETIC_SOURCE_LOCATOR,
        "locator_kind": "synthetic_file",
        "source_file": SYNTHETIC_SOURCE_FILE,
        "row_or_cell_ref": SYNTHETIC_SOURCE_ROW_CELL,
        "lineage_ref": SYNTHETIC_SOURCE_LINEAGE,
    }]
    member_refs = sorted(m["member_ref"] for m in members)
    locator_ids = sorted(set([SYNTHETIC_SOURCE_LOCATOR]))
    src_content = d10_sha256_text(d10_canonical_json({
        "revision_id": SYNTHETIC_SOURCE_REVISION,
        "source_locators": locator_ids,
    }))
    source_pairs = [{
        "revision_id": SYNTHETIC_SOURCE_REVISION,
        "content_hash": src_content,
    }]

    visibility = {
        "decision_id": "",
        "blind_status": "blinded",
        "audience_scope_id": "S2-AUD-001",
        "evaluation_member_refs": member_refs,
        "projectable_member_refs": member_refs,
        "hidden_member_refs": [],
        "hidden_reason_codes": [],
        "evaluation_site_refs": [SYNTHETIC_SITE_REF],
        "projectable_site_refs": [SYNTHETIC_SITE_REF],
        "hidden_site_refs": [],
        "visible_n": 1,
        "eligible_n": 1,
        "hidden_member_count": 0,
        "hidden_site_count": 0,
        "rate_projection_state": "permitted",
        "deep_link_eligible_member_refs": member_refs,
        "deep_link_eligible_site_refs": [SYNTHETIC_SITE_REF],
        "hidden_set_omitted": False,
        "deep_link_eligible_violation": False,
        "treatment_inference_attempt": False,
        "projectable_subject_site_pairs": [
            [SYNTHETIC_SUBJECT_REP, SYNTHETIC_SITE_REF]],
        "deep_link_eligible_subject_site_pairs": [
            [SYNTHETIC_SUBJECT_REP, SYNTHETIC_SITE_REF]],
    }
    visibility["decision_id"] = d10_content_hash(
        _visibility_decision_core(visibility), "decision_id")

    unit_member_set_hash = d10_sha256_text(d10_canonical_json(
        sorted(set(member_refs))))
    proof = {
        "unit_member_refs": sorted(set(member_refs)),
        "covered_member_refs": [],
        "uncovered_member_refs": list(member_refs),
        "member_query_content_identities": [],
    }
    query = {
        "decision": "project_delta_present",
        "covered_member_refs": [],
        "uncovered_member_refs": list(member_refs),
        "member_query_content_identities": [],
        "unit_member_set_hash": unit_member_set_hash,
        "coverage_proof_hash": d10_sha256_text(d10_canonical_json(proof)),
        "max_query_member_fanout": 100,
        "member_unlistable": False,
        "pd_wording_state": "not_pd",
        "duplicate_query_attempt": False,
        "query_content_hash": "",
    }
    query["query_content_hash"] = d10_content_hash(
        _query_decision_core(query), "query_content_hash")

    deep_links = [{
        "target_kind": "member",
        "site_ref": SYNTHETIC_SITE_REF,
        "subject_ref": SYNTHETIC_SUBJECT_REP,
        "member_object_ref": SYNTHETIC_PATTERN_REF,
        "visibility_decision_ref": visibility["decision_id"],
        "return_state_key": SYNTHETIC_RETURN_STATE_KEY,
    }]

    legal_row = {
        "row_id": "S2-LEGAL-001",
        "signal_kind": "project_risk_distribution",
        "clinical_claim_token": "d10_project_risk_distribution",
        "d10_action": "evaluate_and_own",
    }
    legal_row["row_hash"] = d10_content_hash(legal_row, "row_hash")
    scope = {
        "scope_binding_id": "S2-SCOPE-001",
        "scope_type": "project",
        "scope_equality_decision": "exact_match",
    }
    scope["scope_binding_hash"] = d10_content_hash(scope, "scope_binding_hash")
    mode = {
        "mode_contract_version": "S2-MODE-001",
        "design_applicable_state": "applicable",
        "design_clause_ref": None,
    }
    mode["mode_contract_content_hash"] = d10_content_hash(
        mode, "mode_contract_content_hash")

    coverage = [
        {
            "accepted_current": True,
            "coverage_locator_ids": [SYNTHETIC_COVERAGE_LOCATOR],
            "l0_status": "covered",
            "l1_medical_completeness_state": "complete",
            "producer_domain": producer,
        }
        for producer in ("D01", "D02", "D03", "D04", "D05", "D06", "D07",
                         "D08", "D09")
    ]
    denominator_member_refs = list(member_refs)
    denominator_value = len(denominator_member_refs)

    return {
        "input_schema": "d10-typed-input-v1",
        "envelope_id": "S2-ENV-001",
        "project_ref": SYNTHETIC_PROJECT_REF,
        "run_ref": SYNTHETIC_RUN_REF,
        "snapshot_ref": SYNTHETIC_SNAPSHOT_REF,
        "source_revision_content_pairs": source_pairs,
        "project_scope_binding": scope,
        "mode_contract": mode,
        "signal_definition": {
            "signal_definition_id": "S2-DEF-001",
            "signal_kind": "project_risk_distribution",
            "clinical_claim_token": "d10_project_risk_distribution",
            "d10_action": "evaluate_and_own",
            "risk_or_outcome_domain": SYNTHETIC_DOMAIN,
            "required_producer_domains": list(_REQUIRED_PRODUCER_DOMAINS),
            "positive_rule_ref": SYNTHETIC_RULE_ID,
            "counterevidence_rule_refs": ["S2-RULE-CE-001"],
            "legal_matrix_row_ref": "S2-LEGAL-001",
            "authority_locator": "S2-AUTH-001",
        },
        "legal_matrix_row": legal_row,
        "expected_set": {"expected_set_state": "admitted", "admission_gate": None},
        "analysis_windows": [{
            "analysis_window_stable_id": "S2-WIN-001",
            "cutoff_ref": SYNTHETIC_CUTOFF_REF,
            "window_definition_hash": d10_sha256_text("s2 window def 001"),
            "window_definition_id": "S2-WD-001",
            "window_end": SYNTHETIC_WINDOW_END,
            "window_instance_id": "S2-WIN-001-INST",
            "window_kind": "calendar_interval",
            "window_start": SYNTHETIC_WINDOW_START,
            "window_state": "closed",
        }],
        "stratum": {
            "stratum_contract_id": "S2-SC-001",
            "stratum_key": "overall",
            "stratum_state": "closed",
            "stratum_admission": "admitted",
        },
        "comparison_gate": {
            "comparison_state": "ready",
            "comparison_reference_stable_id": "S2-REF-OVERALL",
            "required_site_count_ref": "S2-REQ-SITE-001",
            "observed_eligible_site_count": 1,
            "eligible_site_refs": [SYNTHETIC_SITE_REF],
            "excluded_site_refs": [],
            "reason_codes": [],
            "permitted_output": "admit_cross_site_unit",
        },
        "window_pair_gate": {
            "pair_state": "ready",
            "required_window_count_ref": "S2-REQ-WIN-001",
            "observed_unique_window_count": 1,
            "reason_codes": [],
            "permitted_output": "admit_trend_unit",
        },
        "site_ledger": {
            "ledger_id": "S2-LEDGER-001",
            "site_ref": SYNTHETIC_SITE_REF,
            "site_activation_state": "active",
            "identity_state": "stable",
            "eligible_subject_refs": [SYNTHETIC_SUBJECT_REP],
            "treated_subject_refs": [SYNTHETIC_SUBJECT_REP],
            "evaluable_subject_refs": [SYNTHETIC_SUBJECT_REP],
            "d09_pattern_refs": [SYNTHETIC_PATTERN_REF],
            "coverage_refs": [SYNTHETIC_COVERAGE_LOCATOR],
            "site_activation_ref": "",
        },
        "members": members,
        "numerator_ledger": {
            "individual_risk_count": 0,
            "center_pattern_count": 1,
            "affected_subject_count": 0,
            "event_or_outcome_count": 0,
            "affected_site_count": 1,
            "numerator_member_count": 1,
        },
        "measure_origin_binding": None,
        "denominator": {
            "denominator_kind": "treated_subjects",
            "denominator_value": denominator_value,
            "recomputed_value": denominator_value,
            "denominator_unit": "subject",
            "denominator_state": "closed_positive",
            "denominator_member_refs": denominator_member_refs,
            "excluded_member_refs": [],
            "exclusion_reason_codes": [],
        },
        "time_segments": [],
        "opportunity": None,
        "analysis_population": {
            "analysis_population_contract_id": "S2-POPC-001",
            "analysis_population_ref": "S2-POP-001",
            "present": True,
        },
        "coverage": coverage,
        "change_decision": None,
        "visibility_decision": visibility,
        "query_decision": query,
        "audience_text": {
            "audience_contract_id": "S2-AC-001",
            "display_language": "zh-CN",
            "sentence_part_kind": "observed_finding",
            "basis_zh": "依据已接受的成员对象与可复算分母",
            "finding_zh": "发现 {n} 名受影响受试者（绝对量，分母口径见 "
                         "denominator_context）",
            "action_zh": "建议结合中心/受试者记录核查（非正式结论）",
            "engineering_reference_attempt": False,
            "injection_blocked": False,
        },
        "deep_links": deep_links,
        "model_evidence": None,
        "safety_context": None,
        "efficacy_context": None,
        "rule_hit": {
            "positive_rule_ref": SYNTHETIC_RULE_ID,
            "hit_state": "hit",
            "evidence_sources": ["typed_member"],
            "counterevidence_matched_refs": [],
            "counterevidence_declared_refs": ["S2-CER-001"],
        },
        "hotspot": None,
        "count_layers": {"layers_in_common_numerator": ["individual_risk"],
                         "mixed": False},
        "evaluation_limits": {
            "small_sample": False, "limited_evidence": False,
            "limited_reason": None,
        },
        "numeric_policy": {
            "policy_id": "S2-NUM-001",
            "allowed_estimate_kinds": ["count", "proportion"],
            "decimal_context": "decimal(10,4)",
            "rounding_mode": "half_up",
            "display_precision": 1,
            "subject_time_unit": "day",
            "exposure_time_unit": "subject_day",
            "overlap_policy": "resolve_by_authority",
        },
        "mutation_context": {
            "mutation_class": None, "desc": None, "variant_id": None,
            "base_fixture_id": None,
        },
        "anti_overfit_variant": None,
        "evidence_refs": evidence_refs,
    }


def _visibility_decision_core(visibility: Mapping[str, Any]) -> Dict[str, Any]:
    """Exact visibility-decision canonical dict (mirrors the R4 verifier
    recipe; list order preserved)."""
    return {
        "blind_status": visibility["blind_status"],
        "audience_scope_id": visibility["audience_scope_id"],
        "evaluation_member_refs": list(visibility["evaluation_member_refs"]),
        "projectable_member_refs": list(
            visibility["projectable_member_refs"]),
        "hidden_member_refs": list(visibility["hidden_member_refs"]),
        "hidden_reason_codes": list(visibility["hidden_reason_codes"]),
        "evaluation_site_refs": list(visibility["evaluation_site_refs"]),
        "projectable_site_refs": list(
            visibility["projectable_site_refs"]),
        "hidden_site_refs": list(visibility["hidden_site_refs"]),
        "visible_n": visibility["visible_n"],
        "eligible_n": visibility["eligible_n"],
        "hidden_member_count": visibility["hidden_member_count"],
        "hidden_site_count": visibility["hidden_site_count"],
        "rate_projection_state": visibility["rate_projection_state"],
        "deep_link_eligible_member_refs": list(
            visibility["deep_link_eligible_member_refs"]),
        "deep_link_eligible_site_refs": list(
            visibility["deep_link_eligible_site_refs"]),
        "hidden_set_omitted": visibility["hidden_set_omitted"],
        "deep_link_eligible_violation": visibility[
            "deep_link_eligible_violation"],
        "treatment_inference_attempt": visibility[
            "treatment_inference_attempt"],
        "projectable_subject_site_pairs": [
            list(pair) for pair in visibility["projectable_subject_site_pairs"]],
        "deep_link_eligible_subject_site_pairs": [
            list(pair)
            for pair in visibility["deep_link_eligible_subject_site_pairs"]],
    }


def _query_decision_core(query: Mapping[str, Any]) -> Dict[str, Any]:
    """Exact query-decision canonical dict (mirrors the R4 verifier
    recipe)."""
    return {
        "decision": query["decision"],
        "covered_member_refs": list(query["covered_member_refs"]),
        "uncovered_member_refs": list(query["uncovered_member_refs"]),
        "member_query_content_identities": list(
            query["member_query_content_identities"]),
        "unit_member_set_hash": query["unit_member_set_hash"],
        "coverage_proof_hash": query["coverage_proof_hash"],
        "max_query_member_fanout": query["max_query_member_fanout"],
        "member_unlistable": query["member_unlistable"],
        "pd_wording_state": query["pd_wording_state"],
        "duplicate_query_attempt": query["duplicate_query_attempt"],
    }


def build_synthetic_d10_envelope() -> D10TypedInput:
    """Build the synthetic D10 envelope through the pure structural mapping
    converter (``build_typed_input``), the same path the frozen catalog uses."""
    return build_typed_input(build_synthetic_d10_envelope_dict())


def derive_d10_authority(typed: D10TypedInput) -> D10EvaluationAuthority:
    """Independent runtime authority for one synthetic envelope: the accepted
    envelope identity, the exact submitted source revision-content pairs and
    the accepted source locator set hash (no model pins because the envelope
    carries no model evidence)."""
    locator_ids = tuple(sorted({
        locator for member in typed.members
        for locator in member.source_locator_refs} |
        {ref.locator_id for ref in typed.evidence_refs}))
    return D10EvaluationAuthority(
        project_ref=typed.project_ref,
        run_ref=typed.run_ref,
        snapshot_ref=typed.snapshot_ref,
        accepted_source_revision_content_pairs=typed.source_revision_content_pairs,
        accepted_source_locator_set_hash=d10_sha256_text(
            d10_canonical_json(list(locator_ids))),
        model_binding_hash=None,
        model_output_hash=None,
    )


# ---------------------------------------------------------------------------
# Real pipeline gates
# ---------------------------------------------------------------------------


def evaluate_envelope(
    typed: D10TypedInput,
    authority: Optional[D10EvaluationAuthority] = None,
) -> D10RunResult:
    """Run the REAL R4 deterministic evaluator and fail closed unless the
    envelope is authoritative and yields a positive medical unit (a risk
    marker and a locatable deep link require it)."""
    authority = authority or derive_d10_authority(typed)
    result = evaluate(typed, authority)
    if result.unit is None or result.unit.l1_disposition != "positive":
        raise S2AuthorityBuilderError(
            "synthetic envelope did not evaluate to a positive medical unit: "
            f"{result.disposition_or_gate!r}/{result.primary_reason!r}")
    return result


def require_single_analysis_window(
    typed: D10TypedInput,
) -> Tuple[Any, date, date]:
    """Return the sole closed R4 analysis window and parsed date bounds.

    S2 is deliberately a one-window slice.  The temporal facts are accepted
    only when the real typed window is unique, closed and contains the exact
    supplemental event/visit dates; changing the caller's R4 window can
    therefore never leave a stale fixed S2 window behind.
    """
    if len(typed.analysis_windows) != 1:
        raise S2AuthorityBuilderError(
            "the S2 temporal chain requires exactly one R4 analysis window")
    window, = typed.analysis_windows
    if window.window_state != "closed":
        raise S2AuthorityBuilderError(
            "the S2 temporal chain requires a closed R4 analysis window")
    try:
        start = date.fromisoformat(window.window_start)
        end = date.fromisoformat(window.window_end)
    except (TypeError, ValueError):
        raise S2AuthorityBuilderError(
            "the R4 analysis window must have exact ISO-8601 date bounds") \
            from None
    if end < start:
        raise S2AuthorityBuilderError(
            "the R4 analysis window end precedes its start")
    if not (start <= SYNTHETIC_ACTUAL_DATE <= end
            and start <= SYNTHETIC_EVENT_START <= end
            and start <= SYNTHETIC_EVENT_END <= end):
        raise S2AuthorityBuilderError(
            "the exact S2 visit/event dates must lie inside the real R4 "
            "analysis window")
    return window, start, end


# ---------------------------------------------------------------------------
# Pattern descendants -> individual Member objects (synthetic registry)
# ---------------------------------------------------------------------------


def resolve_center_pattern_member(typed: D10TypedInput) -> Member:
    """The S2 single-center packet requires EXACTLY ONE ``center_pattern``
    member matching the typed relation.  0 or >1 fail closed
    (``S2AuthorityBuilderError``); never rely on input order."""
    patterns = tuple(
        member for member in typed.members
        if member.member_kind == "center_pattern")
    if len(patterns) != 1:
        raise S2AuthorityBuilderError(
            "the S2 single-center packet requires exactly one "
            f"center_pattern member, got {len(patterns)}")
    pattern, = patterns
    return pattern


def derive_individual_members(
    pattern: Member,
    registry: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> Tuple[Member, ...]:
    """Resolve the real pattern member's ``descendant_member_refs`` to
    ``individual_risk`` Member objects on the same site using the explicit
    synthetic member registry (never a nearest-match, never an id-convention
    branch).  A missing registry entry fails closed."""
    if registry is not None:
        raise S2AuthorityBuilderError(
            "external individual registries are forbidden; S2 descendant "
            "authority is the frozen tuple of typed R4 Member objects")
    descendants = tuple(sorted(set(pattern.descendant_member_refs)))
    by_ref = {member.member_ref: member
              for member in FROZEN_INDIVIDUAL_MEMBERS}
    if descendants != tuple(sorted(by_ref)):
        raise S2AuthorityBuilderError(
            "pattern descendant refs must equal the frozen supplemental "
            "individual Member authority")
    individuals = tuple(by_ref[ref] for ref in descendants)
    for member in individuals:
        if member.site_stable_id != pattern.site_stable_id or \
                member.source_locator_refs != pattern.source_locator_refs:
            raise S2AuthorityBuilderError(
                "frozen individual Member site/source authority must equal "
                "the real center-pattern relation")
    return individuals


# ---------------------------------------------------------------------------
# Binding builders (pure functions of the real pipeline objects)
# ---------------------------------------------------------------------------


def resolve_source_authority(
    typed: D10TypedInput,
    receipt: R5AuthorityReceipt,
    deep_link: D10DeepLinkTarget,
) -> Tuple[EvidenceRef, SourceRevisionPair]:
    """Resolve the ONE-HOP source authority of the single-source packet.

    The real D10 deep-link ``source_locator`` is the ONLY locator authority:
    it must resolve (``locatable``), exactly ONE ``EvidenceRef`` must match
    it, and the typed envelope and the receipt must each carry exactly one
    consistent source revision-content pair so the locator -> revision join
    is unique.  Absence, ambiguity or divergence fails closed
    (``S2AuthorityBuilderError``); there is never a first-item fallback."""
    if deep_link.target_state != "locatable" or not deep_link.source_locator:
        raise S2AuthorityBuilderError(
            "the S2 one-hop source requires a locatable deep-link target "
            "with a resolved source locator")
    matches = [ref for ref in typed.evidence_refs
               if ref.locator_id == deep_link.source_locator]
    if len(matches) != 1:
        raise S2AuthorityBuilderError(
            f"exactly one EvidenceRef must match the deep-link source "
            f"locator {deep_link.source_locator!r}, got {len(matches)}")
    pair = _require_single_source_pair(typed, receipt)
    evidence, = matches
    return evidence, pair


def _require_single_source_pair(
    typed: D10TypedInput,
    receipt: R5AuthorityReceipt,
) -> SourceRevisionPair:
    """Exactly one source revision-content pair in BOTH the typed envelope
    and the receipt, and the two must agree: the unique locator -> revision
    join of this single-source packet."""
    typed_pairs = typed.source_revision_content_pairs
    receipt_pairs = receipt.source_revision_content_pairs
    if len(typed_pairs) != 1 or len(receipt_pairs) != 1:
        raise S2AuthorityBuilderError(
            "the S2 single-source packet requires exactly one source "
            f"revision-content pair, got typed={len(typed_pairs)} "
            f"receipt={len(receipt_pairs)}; the locator -> revision join "
            "must be unique")
    typed_pair, = typed_pairs
    receipt_pair, = receipt_pairs
    if (typed_pair.revision_id, typed_pair.content_hash) != (
            receipt_pair.revision_id, receipt_pair.content_hash):
        raise S2AuthorityBuilderError(
            "typed and receipt source revision-content pairs diverge")
    return typed_pair


def build_source_binding(
    evidence: EvidenceRef,
    source_pair: SourceRevisionPair,
) -> R5S2SourceBinding:
    """One-hop source binding: the unique source revision-content pair bound
    to the locatable deep-link locator, with ``fallback_policy=none``."""
    return R5S2SourceBinding(
        content_hash="",
        fallback_policy="none",
        lineage_ref=evidence.lineage_ref,
        locator_id=evidence.locator_id,
        locator_kind=evidence.locator_kind,
        resolution_state="locatable",
        revision_content_hash=source_pair.content_hash,
        revision_id=source_pair.revision_id,
        row_or_cell_ref=evidence.row_or_cell_ref,
        source_file=evidence.source_file,
    )


def derive_center_domain(pattern: Member, individuals: Tuple[Member, ...],
                         typed: D10TypedInput) -> str:
    """The packet domain: the closed risk/outcome domain from the actual
    ``SignalDefinition.risk_or_outcome_domain`` (no count/UI/filename/test-id
    inference)."""
    domain = typed.signal_definition.risk_or_outcome_domain
    if domain not in S2_DOMAINS:
        raise S2AuthorityBuilderError(
            f"signal risk_or_outcome_domain {domain!r} is not a closed S2 "
            f"domain ({S2_DOMAINS!r})")
    return domain


def derive_center_severity(pattern: Member,
                           individuals: Tuple[Member, ...]) -> str:
    """Closed high>medium>low precedence over the actual pattern and
    individual monitoring priorities; unknown/critical fail closed."""
    priorities = [pattern.monitoring_priority] + [
        member.monitoring_priority for member in individuals]
    for priority in priorities:
        if priority not in S2_SEVERITIES:
            raise S2AuthorityBuilderError(
                f"member monitoring_priority {priority!r} is not a closed "
                f"S2 severity ({S2_SEVERITIES!r})")
    return max(priorities, key=lambda value: _SEVERITY_RANK[value])


def build_center_binding(
    pattern: Member,
    individuals: Tuple[Member, ...],
    typed: D10TypedInput,
) -> R5S2CenterBinding:
    """Center-cell binding from the actual pattern/individual typed member
    relation and the signal definition domain."""
    domain = derive_center_domain(pattern, individuals, typed)
    severity = derive_center_severity(pattern, individuals)
    priorities = tuple(sorted({pattern.monitoring_priority} | {
        member.monitoring_priority for member in individuals}))
    producer_domains = tuple(sorted({pattern.producer_domain} | {
        member.producer_domain for member in individuals}))
    return R5S2CenterBinding(
        content_hash="",
        individual_risk_refs=tuple(
            sorted(member.member_ref for member in individuals)),
        measure_refs=(),
        member_priorities=priorities,
        member_producer_domains=producer_domains,
        pattern_descendant_member_refs=tuple(
            sorted(set(pattern.descendant_member_refs))),
        pattern_ref=pattern.member_ref,
        r4_risk_or_outcome_domain=domain,
        r5_domain=domain,
        r5_severity=severity,
        site_ref=pattern.site_stable_id,
    )


def build_project_risk_binding(
    receipt: R5AuthorityReceipt,
    projection: D10ProjectProjection,
    risk_marker: D10RiskMarker,
) -> R5S2ProjectRiskBinding:
    """Project-risk binding from the accepted D10 risk marker and the bound
    project projection / S1 receipt identities."""
    return R5S2ProjectRiskBinding(
        authority_receipt_ref=s2_object_content_hash(receipt),
        content_hash="",
        cutoff_ref=receipt.cutoff_ref,
        member_refs=risk_marker.member_refs,
        project_ref=receipt.project_ref,
        projection_version_ref=projection.projection_version_ref,
        public_projection_content_hash=projection.projection_content_hash,
        public_projection_id=projection.projection_id,
        risk_marker_content_hash=risk_marker.content_hash,
        risk_ref=risk_marker.marker_id,
        run_ref=receipt.run_ref,
        snapshot_ref=receipt.snapshot_ref,
        source_locator_refs=risk_marker.source_locator_ids,
        stable_core_ref=risk_marker.stable_core,
    )


def bind_deep_link_to_receipt(
    deep_link: D10DeepLinkTarget,
    receipt: R5AuthorityReceipt,
) -> D10DeepLinkTarget:
    """Rebind the deep-link target's ``visibility_decision_hash`` to the S1
    receipt's canonical visibility-decision hash (the R4 builder records the
    envelope decision id there; the packet contract requires the receipt
    hash).  ``link_id`` and every other field are unchanged."""
    if deep_link.visibility_decision_hash == receipt.visibility_decision_hash:
        return deep_link
    from dataclasses import replace
    return replace(deep_link,
                   visibility_decision_hash=receipt.visibility_decision_hash)


def build_temporal_binding(
    typed: D10TypedInput,
    receipt: R5AuthorityReceipt,
    deep_link: D10DeepLinkTarget,
    risk_marker: D10RiskMarker,
    center_binding: R5S2CenterBinding,
    source_evidence: EvidenceRef,
) -> R5S2TemporalBinding:
    """Single synthetic/offline temporal chain: one exact-date visit/event/
    risk anchor on the deep-link subject, sharing the center domain/severity
    and the one-hop source locator."""
    window, _, _ = require_single_analysis_window(typed)
    if receipt.cutoff_ref != window.cutoff_ref:
        raise S2AuthorityBuilderError(
            "receipt cutoff_ref must equal the real R4 analysis-window "
            "cutoff_ref")
    return R5S2TemporalBinding(
        actual_date=SYNTHETIC_ACTUAL_DATE,
        content_hash="",
        cutoff_ref=receipt.cutoff_ref,
        date_state="exact",
        domain=center_binding.r5_domain,
        event_end=SYNTHETIC_EVENT_END,
        event_ref=SYNTHETIC_EVENT_REF,
        event_start=SYNTHETIC_EVENT_START,
        event_subtype=SYNTHETIC_EVENT_SUBTYPE,
        nominal_date=None,
        pending_date_refs=(),
        phase_band_refs=(),
        phase_ref=None,
        risk_anchor_ref=SYNTHETIC_RISK_ANCHOR_REF,
        risk_ref=risk_marker.marker_id,
        risk_type_zh=SYNTHETIC_RISK_TYPE_ZH,
        severity=center_binding.r5_severity,
        source_locator_ref=source_evidence.locator_id,
        spine_ref=SYNTHETIC_SPINE_REF,
        subject_ref=deep_link.subject_ref,
        visit_kind="actual",
        visit_ref=SYNTHETIC_VISIT_REF,
    )


# ---------------------------------------------------------------------------
# Ensemble side (real R4 run_ensemble)
# ---------------------------------------------------------------------------


def build_input_content_hash(
    typed: D10TypedInput,
    source_evidence: EvidenceRef,
    source_pair: SourceRevisionPair,
) -> str:
    """Deterministic shared input-version hash for the two worker attempts
    (binds the ACTUAL envelope identity, evidence locator and source
    revision -- never a hardcoded synthetic locator/revision)."""
    return _h({
        "project_ref": typed.project_ref,
        "run_ref": typed.run_ref,
        "snapshot_ref": typed.snapshot_ref,
        "source_revision_id": source_pair.revision_id,
        "source_locator_id": source_evidence.locator_id,
    })


def _build_reference_baseline_item(
    receipt: R5AuthorityReceipt,
    source_evidence: EvidenceRef,
    source_pair: SourceRevisionPair,
    temporal_window: str,
) -> ReferenceBaselineItem:
    return ReferenceBaselineItem(
        item_id=SYNTHETIC_BASELINE_ITEM,
        source_kind="legacy_profile",
        source_locator_ids=(source_evidence.locator_id,),
        source_revision_id=source_pair.revision_id,
        snapshot_id=receipt.snapshot_ref,
        claimed_identity=SYNTHETIC_CLAIMED_IDENTITY,
        temporal_window=temporal_window,
        claimed_content_hash="",
        origin_artifact_hash=source_pair.content_hash,
    )


def build_ensemble_objects(
    typed: D10TypedInput,
    receipt: R5AuthorityReceipt,
    source_evidence: EvidenceRef,
    source_pair: SourceRevisionPair,
    worker_specs: Optional[Tuple[_WorkerSpec, ...]] = None,
):
    """Build the two isolated worker attempts/outputs and run the REAL R4
    ``run_ensemble`` closure (verifications, visible conflict, independent
    adjudication).  The finding support direction comes from each explicit
    ``_WorkerSpec`` (never from index, order or id naming).  Returns a small
    bundle (item, attempts, outputs, ensemble_result)."""
    specs = worker_specs if worker_specs is not None else WORKER_SPECS
    if len(specs) != 2:
        raise S2AuthorityBuilderError(
            f"the S2 ensemble requires exactly two worker specifications, "
            f"got {len(specs)}")
    input_hash = build_input_content_hash(
        typed, source_evidence, source_pair)
    window, window_start, window_end = require_single_analysis_window(typed)
    item = _build_reference_baseline_item(
        receipt, source_evidence, source_pair,
        f"{window_start.isoformat()}..{window_end.isoformat()}")
    if window.cutoff_ref != receipt.cutoff_ref:
        raise S2AuthorityBuilderError(
            "baseline temporal window cutoff must equal the receipt cutoff")

    def make_assessment(spec: _WorkerSpec) -> BaselineAssessment:
        return BaselineAssessment(
            item_id=item.item_id,
            state="confirmed",
            source_recheck_locator_ids=(source_evidence.locator_id,),
            evidence_hashes=(source_pair.content_hash,),
            attempt_id=spec.attempt_id,
            reason_codes=("source_rechecked",),
        )

    def make_finding(spec: _WorkerSpec) -> Finding:
        return Finding(
            finding_id=f"S2-FINDING-{spec.attempt_id}",
            proposed_identity=SYNTHETIC_FINDING_IDENTITY,
            monitoring_priority="high",
            supported=spec.supports_finding,
            source_locator_ids=(source_evidence.locator_id,),
            baseline_item_ref=item.item_id,
        )

    attempts: list = []
    worker_outputs: Dict[str, WorkerAnalysisOutput] = {}
    for spec in specs:
        output = WorkerAnalysisOutput(
            attempt_id=spec.attempt_id,
            assessments=(make_assessment(spec),),
            findings=(make_finding(spec),),
            gap_candidates=(),
        )
        output_hash = worker_output_content_hash(output)
        attempt = AnalysisAttempt(
            attempt_id=spec.attempt_id,
            ensemble_id=SYNTHETIC_ENSEMBLE_ID,
            binding_id=spec.binding_id,
            session_id=spec.session_id,
            model_id=SYNTHETIC_MODEL_ID,
            model_version=SYNTHETIC_MODEL_VERSION,
            role="worker",
            independent_context_hash=s2_sha256(
                f"S2-CONTEXT:{spec.attempt_id}".encode("utf-8")),
            input_content_hash=input_hash,
            output_artifact_ref=spec.artifact_ref,
            output_hash=output_hash,
            claimed_date_window=item.temporal_window,
            claimed_unit_contract=SYNTHETIC_DOMAIN,
            claimed_source_revision=source_pair.revision_id,
            claimed_rule_id=SYNTHETIC_RULE_ID,
            claimed_rule_version=SYNTHETIC_RULE_VERSION,
        )
        attempts.append(attempt)
        worker_outputs[spec.attempt_id] = output

    digest_context = EvidenceDigestContext(
        input_content_hash=input_hash,
        output_digests={attempt.output_artifact_ref:
                        worker_output_content_hash(worker_outputs[
                            attempt.attempt_id]) for attempt in attempts},
        evidence_digests=frozenset([source_pair.content_hash]),
        expected_ensemble_identity=SYNTHETIC_ENSEMBLE_ID,
        artifact_date_windows={attempt.output_artifact_ref:
                               attempt.claimed_date_window
                               for attempt in attempts},
        artifact_unit_contracts={attempt.output_artifact_ref:
                                 attempt.claimed_unit_contract
                                 for attempt in attempts},
        artifact_source_versions={attempt.output_artifact_ref:
                                  attempt.claimed_source_revision
                                  for attempt in attempts},
        artifact_model_versions={attempt.output_artifact_ref:
                                 attempt.model_version
                                 for attempt in attempts},
        artifact_rule_ids={attempt.output_artifact_ref:
                           attempt.claimed_rule_id
                           for attempt in attempts},
        artifact_rule_versions={attempt.output_artifact_ref:
                                attempt.claimed_rule_version
                                for attempt in attempts},
        artifact_finding_identities={attempt.output_artifact_ref:
                                     frozenset([SYNTHETIC_FINDING_IDENTITY])
                                     for attempt in attempts},
        artifact_authorized_source_locators={attempt.output_artifact_ref:
                                             frozenset(
                                                 [source_evidence.locator_id])
                                             for attempt in attempts},
    )
    result = run_ensemble(
        ensemble_id=SYNTHETIC_ENSEMBLE_ID,
        input_content_hash=input_hash,
        attempts=attempts,
        worker_outputs=worker_outputs,
        baseline_items=[item],
        digest_context=digest_context,
        adjudicator=Adjudicator(
            binding_id=SYNTHETIC_ADJUDICATOR_BINDING,
            session_id=SYNTHETIC_ADJUDICATOR_SESSION,
            model_id=SYNTHETIC_MODEL_ID,
            model_version=SYNTHETIC_MODEL_VERSION,
        ),
        current_source_locator_ids=[source_evidence.locator_id],
    )
    for verification in result.verifications:
        if verification.result != "passed" \
                or set(verification.checked_dimensions) != set(
                    ("identity", "version", "date", "unit", "source",
                     "rule", "artifact_integrity")):
            raise S2AuthorityBuilderError(
                "real ensemble verification did not pass across all seven "
                f"dimensions: {verification.result!r}")
    if len(result.conflicts) != 1:
        raise S2AuthorityBuilderError(
            "real ensemble did not derive the single visible "
            "mutual_negation conflict")
    conflict, = result.conflicts
    if conflict.relation != "mutual_negation":
        raise S2AuthorityBuilderError(
            "real ensemble did not derive the single visible "
            "mutual_negation conflict")
    return _EnsembleDerived(
        item=item,
        attempts=tuple(sorted(attempts, key=lambda a: a.attempt_id)),
        worker_outputs=tuple(
            worker_outputs[spec.attempt_id] for spec in specs),
        ensemble_result=result,
    )


class _EnsembleDerived:
    """Bundle returned by :func:`build_ensemble_objects`."""

    __slots__ = ("item", "attempts", "worker_outputs", "ensemble_result")

    def __init__(self, item, attempts, worker_outputs, ensemble_result) -> None:
        self.item = item
        self.attempts = attempts
        self.worker_outputs = worker_outputs
        self.ensemble_result = ensemble_result


def build_model_evidence(
    receipt: R5AuthorityReceipt,
    version: D10ProjectionVersion,
    ensemble: _EnsembleDerived,
    source_evidence: EvidenceRef,
    source_pair: SourceRevisionPair,
) -> ModelEvidence:
    """Packet-only D10 ModelEvidence bound to the two worker attempts, the
    receipt source pairs and the shared ensemble identity."""
    evaluation_identities = version.source_evaluation_content_identities
    if len(evaluation_identities) != 1 or \
            evaluation_identities != receipt.evaluation_content_identities:
        raise S2AuthorityBuilderError(
            "ModelEvidence requires one evaluation identity shared exactly "
            "by the projection version and authority receipt")
    evaluation_identity, = evaluation_identities
    if len(ensemble.attempts) != 2:
        raise S2AuthorityBuilderError(
            "ModelEvidence requires exactly two analysis attempts")
    input_hashes = {attempt.input_content_hash
                    for attempt in ensemble.attempts}
    if len(input_hashes) != 1:
        raise S2AuthorityBuilderError(
            "ModelEvidence attempts must share one input content hash")
    input_content_hash, = input_hashes
    attempt_ids = tuple(sorted(
        attempt.attempt_id for attempt in ensemble.attempts))
    conflicts = ensemble.ensemble_result.conflicts
    if len(conflicts) != 1:
        raise S2AuthorityBuilderError(
            "ModelEvidence requires exactly one visible conflict")
    conflict, = conflicts
    output_identity = expected_model_output_identity(ensemble.attempts)
    output_hash = expected_model_output_hash(
        output_identity, conflict.conflict_id,
        ensemble.ensemble_result.adjudication.binding_id)
    binding_hash = expected_model_binding_hash(
        model_evidence_id=SYNTHETIC_MODEL_EVIDENCE_ID,
        role="candidate_explanation",
        model_id=SYNTHETIC_MODEL_ID,
        model_version=SYNTHETIC_MODEL_VERSION,
        ensemble_id=SYNTHETIC_ENSEMBLE_ID,
        input_content_hash=input_content_hash,
        member_analysis_refs=attempt_ids,
    )
    return ModelEvidence(
        model_evidence_id=SYNTHETIC_MODEL_EVIDENCE_ID,
        role="candidate_explanation",
        permitted_leaf="model_candidate_only",
        model_id=SYNTHETIC_MODEL_ID,
        model_version=SYNTHETIC_MODEL_VERSION,
        evaluation_content_identity=evaluation_identity,
        input_content_hash=input_content_hash,
        source_revision_content_pairs=(source_pair,),
        source_refs=(source_evidence.locator_id,),
        independent_context_hash=s2_sha256(
            b"S2-CONTEXT-PACKET-AGGREGATE"),
        ensemble_id=SYNTHETIC_ENSEMBLE_ID,
        ensemble_size=2,
        member_analysis_refs=attempt_ids,
        member_analysis_ref_set_hash=s2_object_content_hash(attempt_ids),
        output_identity=output_identity,
        output_hash=output_hash,
        adjudication_state="adjudicated",
        model_binding_hash=binding_hash,
    )


def build_inspector_binding(
    receipt: R5AuthorityReceipt,
    ensemble: _EnsembleDerived,
    source_evidence: EvidenceRef,
    project_risk: R5S2ProjectRiskBinding,
    center_binding: R5S2CenterBinding,
) -> R5S2InspectorBinding:
    """Risk Inspector binding: every public ref mechanically derived from the
    actual packet objects; S4-deferred leaves stay exactly empty/null."""
    result = ensemble.ensemble_result
    baseline_assessment_item_ids = tuple(sorted(set(
        assessment.item_id
        for output in ensemble.worker_outputs
        for assessment in output.assessments)))
    if len(result.conflicts) != 1:
        raise S2AuthorityBuilderError(
            "Inspector binding requires exactly one visible conflict")
    conflict, = result.conflicts
    return R5S2InspectorBinding(
        adjudication_ref=result.adjudication.binding_id,
        analysis_attempt_refs=tuple(sorted(
            attempt.attempt_id for attempt in ensemble.attempts)),
        authority_receipt_ref=s2_object_content_hash(receipt),
        baseline_assessment_refs=baseline_assessment_item_ids,
        baseline_item_refs=(ensemble.item.item_id,),
        conflict_refs=(conflict.conflict_id,),
        content_hash="",
        counterevidence_refs=(),
        domain=center_binding.r5_domain,
        model_evidence_visibility="packet_only",
        query_draft_ref=None,
        risk_ref=project_risk.risk_ref,
        severity=center_binding.r5_severity,
        source_locator_refs=(source_evidence.locator_id,),
        support_evidence_refs=(),
        verification_refs=tuple(sorted(
            verification.verification_id
            for verification in result.verifications)),
        worker_output_refs=(),
    )


def assemble_packet(
    typed: D10TypedInput,
    result: D10RunResult,
    receipt: R5AuthorityReceipt,
    projection: D10ProjectProjection,
    risk_marker: D10RiskMarker,
    deep_link: D10DeepLinkTarget,
    pattern: Member,
    individuals: Tuple[Member, ...],
    center_binding: R5S2CenterBinding,
    project_risk: R5S2ProjectRiskBinding,
    source_binding: R5S2SourceBinding,
    source_evidence: EvidenceRef,
    temporal_binding: R5S2TemporalBinding,
    ensemble: _EnsembleDerived,
    model_evidence: ModelEvidence,
    inspector_binding: R5S2InspectorBinding,
) -> R5S2AuthorityPacket:
    """Assemble the frozen typed packet from the derived objects.  The packet
    constructor itself runs every frozen cross-object invariant fail-closed
    (no packet is emitted for a tampered or inconsistent assembly)."""
    result_ = ensemble.ensemble_result
    if len(result_.conflicts) != 1:
        raise S2AuthorityBuilderError(
            "packet assembly requires exactly one visible conflict")
    conflict, = result_.conflicts
    return R5S2AuthorityPacket(
        adjudication=result_.adjudication,
        analysis_attempts=ensemble.attempts,
        authority_mode=AUTHORITY_MODE_S2,
        authority_receipt=receipt,
        baseline_assessments=tuple(sorted(
            {assessment for output in ensemble.worker_outputs
             for assessment in output.assessments},
            key=lambda assessment: assessment.attempt_id)),
        center_binding=center_binding,
        center_pattern_member=pattern,
        conflict=conflict,
        deep_link_target=deep_link,
        individual_members=individuals,
        inspector_binding=inspector_binding,
        model_evidence=model_evidence,
        packet_content_hash="",
        packet_id="",
        project_risk_binding=project_risk,
        reference_baseline_items=(ensemble.item,),
        source_binding=source_binding,
        source_evidence=source_evidence,
        stage_status=STAGE_STATUS_S2,
        temporal_binding=temporal_binding,
        verifications=result_.verifications,
        worker_outputs=ensemble.worker_outputs,
    )


def build_s2_authority_packet(
    typed: Optional[D10TypedInput] = None,
    authority: Optional[D10EvaluationAuthority] = None,
    individual_registry: Optional[Mapping[str, Mapping[str, Any]]] = None,
    variant: Optional[Any] = None,
    worker_specs: Optional[Tuple[_WorkerSpec, ...]] = None,
) -> R5S2AuthorityPacket:
    """Build one frozen S2 authority packet through the real R4 typed
    pipeline from a synthetic D10 envelope.

    ``typed`` may be a caller-supplied synthetic envelope (used by challenge
    tests to inject defects); otherwise the built-in synthetic envelope is
    used.  ``authority`` is derived from the envelope when omitted.  Every
    step is fail-closed: a defective envelope or an inconsistent derivation
    raises instead of emitting a packet.
    """
    variant = variant or DEFAULT_D10_AUTHORITY_ADAPTER_VARIANT
    typed = typed if typed is not None else build_synthetic_d10_envelope()
    result = evaluate_envelope(typed, authority)
    projection = build_d10_project_projection(typed, result)
    version = build_d10_projection_version(typed, result)
    risk_marker = build_d10_risk_marker(typed, result)
    deep_links = build_d10_deep_links(typed, result)
    if risk_marker is None:
        raise S2AuthorityBuilderError(
            "no project risk marker was derived for the envelope")
    if len(deep_links) != 1:
        raise S2AuthorityBuilderError(
            "the synthetic envelope must yield exactly one locatable "
            "deep-link target")
    deep_link, = deep_links
    if deep_link.target_state != "locatable":
        raise S2AuthorityBuilderError(
            "the synthetic envelope must yield exactly one locatable "
            "deep-link target")

    receipt = build_authority_receipt(
        typed, version, projection, variant=variant)
    deep_link = bind_deep_link_to_receipt(deep_link, receipt)

    pattern = resolve_center_pattern_member(typed)
    individuals = derive_individual_members(pattern, individual_registry)

    source_evidence, source_pair = resolve_source_authority(
        typed, receipt, deep_link)
    source_binding = build_source_binding(source_evidence, source_pair)
    center_binding = build_center_binding(pattern, individuals, typed)
    project_risk = build_project_risk_binding(
        receipt, projection, risk_marker)
    temporal_binding = build_temporal_binding(
        typed, receipt, deep_link, risk_marker, center_binding,
        source_evidence)
    ensemble = build_ensemble_objects(
        typed, receipt, source_evidence, source_pair,
        worker_specs=worker_specs)
    model_evidence = build_model_evidence(
        receipt, version, ensemble, source_evidence, source_pair)
    inspector_binding = build_inspector_binding(
        receipt, ensemble, source_evidence, project_risk, center_binding)

    packet = assemble_packet(
        typed, result, receipt, projection, risk_marker, deep_link, pattern,
        individuals, center_binding, project_risk, source_binding,
        source_evidence, temporal_binding, ensemble, model_evidence,
        inspector_binding)
    verification = validate_s2_authority_packet(packet)
    if not verification["valid"]:
        raise S2AuthorityBuilderError(
            "assembled packet failed the frozen cross-object invariants: "
            f"{verification['reasons']!r}")
    return packet


# ---------------------------------------------------------------------------
# Static closure of the runtime builder (no forbidden branches, no file IO)
# ---------------------------------------------------------------------------

#: Forbidden semantic-branch tokens (frozen packet schema) -- the builder's
#: decision paths must never consult them.
FORBIDDEN_SEMANTIC_TOKENS: Tuple[str, ...] = (
    "fixture_id", "test_id", "case_id", "oracle", "mutation_class",
    "synthetic_sentinel", "nearest_",
)


__all__ = [
    "FROZEN_INDIVIDUAL_MEMBERS",
    "FORBIDDEN_SEMANTIC_TOKENS",
    "S2AuthorityBuilderError",
    "SYNTHETIC_ACTUAL_DATE",
    "SYNTHETIC_ATTEMPT_IDS",
    "SYNTHETIC_BASELINE_ITEM",
    "SYNTHETIC_CUTOFF_REF",
    "SYNTHETIC_DOMAIN",
    "SYNTHETIC_ENSEMBLE_ID",
    "SYNTHETIC_EVENT_END",
    "SYNTHETIC_EVENT_REF",
    "SYNTHETIC_EVENT_START",
    "SYNTHETIC_EVENT_SUBTYPE",
    "SYNTHETIC_FINDING_IDENTITY",
    "SYNTHETIC_INDIVIDUAL_REFS",
    "SYNTHETIC_MODEL_EVIDENCE_ID",
    "SYNTHETIC_MODEL_ID",
    "SYNTHETIC_MODEL_VERSION",
    "SYNTHETIC_PATTERN_REF",
    "SYNTHETIC_PROJECT_REF",
    "SYNTHETIC_RISK_ANCHOR_REF",
    "SYNTHETIC_RISK_TYPE_ZH",
    "SYNTHETIC_RULE_ID",
    "SYNTHETIC_RULE_VERSION",
    "SYNTHETIC_RUN_REF",
    "SYNTHETIC_SITE_REF",
    "SYNTHETIC_SNAPSHOT_REF",
    "SYNTHETIC_SOURCE_FILE",
    "SYNTHETIC_SOURCE_LINEAGE",
    "SYNTHETIC_SOURCE_LOCATOR",
    "SYNTHETIC_SOURCE_REVISION",
    "SYNTHETIC_SOURCE_ROW_CELL",
    "SYNTHETIC_SPINE_REF",
    "SYNTHETIC_SUBJECT_REP",
    "SYNTHETIC_VISIT_REF",
    "SYNTHETIC_WINDOW_END",
    "SYNTHETIC_WINDOW_REF",
    "SYNTHETIC_WINDOW_START",
    "WORKER_SPECS",
    "assemble_packet",
    "bind_deep_link_to_receipt",
    "build_center_binding",
    "build_ensemble_objects",
    "build_input_content_hash",
    "build_inspector_binding",
    "build_model_evidence",
    "build_project_risk_binding",
    "build_s2_authority_packet",
    "build_source_binding",
    "build_synthetic_d10_envelope",
    "build_synthetic_d10_envelope_dict",
    "build_temporal_binding",
    "derive_center_domain",
    "derive_center_severity",
    "derive_d10_authority",
    "derive_individual_members",
    "evaluate_envelope",
    "resolve_center_pattern_member",
    "resolve_source_authority",
]
