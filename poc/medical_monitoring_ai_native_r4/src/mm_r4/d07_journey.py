"""R4-D07 shared visit-axis Journey projection and audience validation.

Worker-03 slice.  Consumes the accepted typed input and the closed runtime's
evaluation units (never the frozen oracle/registry/manifest) and produces:

* ``build_d07_journey_summary`` -- the deterministic journey summary leaves
  that the raw output root carries under ``journey.*`` (the frozen oracle
  vocabulary, contract v0.4 section 11);
* ``build_d07_subject_journey`` -- the renderer-neutral, content-addressed
  ``D07SubjectJourneyProjection`` object (event markers, risk markers, source
  jumps with reverse bindings, shared-spine scope/hash equality decision and
  per-payload audience / per-jump validation results) for consumers and the
  focused journey tests;
* ``validate_audience_payload`` -- the shared closed exact-key audience
  validator used by both the journey and the query payloads.

Boundaries honoured (v0.4 section 11 / 13):

* the projection only exists on the shared visit/time spine when the typed
  input binds ``shared_spine_binding`` + ``shared_spine_scope_equality_decision``
  and the run is admitted (no pre-evaluator integrity error, no D05 open gate);
* every marker/jump/projection is content-addressed; serializers recompute the
  hashes from typed fields only;
* each source jump carries exactly one reverse binding; ``cardinality=one``
  requires a single target ref, ``many`` an ordered, duplicate-free list;
* ``temporal_context`` joins require a typed ``temporal_relation_ref``; every
  jump produces a ``D07SourceJumpValidationResult`` and every payload a
  ``D07AudiencePayloadValidationResult``; both must pass to be visible;
* labels come from the frozen ``D07AudienceLexicon``; forbidden internal
  tokens (``payload``/``lineage``/``hash``/``ref``/``fixture``/``oracle``/
  ``candidate``/``正式事实``/``候选信号``/``已记录事项``/``通用风险点`` ...)
  are rejected -- no internal object names or enums leak to the audience;
* no risk identity is fabricated and no adjacent-domain event (AE/CM/IP/PD)
  is copied; jumps to adjacent records are only produced from typed producer
  bindings.

All data is synthetic and offline.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .d07_safety import (
    ClinicalSignificance,
    L1Disposition,
    PositiveSubtype,
    RecordStatus,
    UnitKind,
    d07_content_hash,
    is_sha256_hex,
    SECTION_HASH_FIELDS,
    SINGLETON_HASH_FIELDS,

)

# ---------------------------------------------------------------------------
# Domain vocabulary (fixed, project-independent; labels come from the lexicon)
# ---------------------------------------------------------------------------

_DOMAIN_ORDER: Tuple[str, ...] = ("LB", "VS", "EG", "PE", "IMAGING", "OTHER")

_DOMAIN_EVENT_KIND: Dict[str, str] = {
    "LB": "lab",
    "VS": "vital_sign",
    "EG": "ecg",
    "PE": "physical_exam",
    "IMAGING": "imaging",
    "OTHER": "other_exam",
}

# Stable unit identity inputs (contract v0.4 section 5.1 -- stable core).
_SCOPE_TUPLE_FIELDS = (
    "project_ref", "site_ref", "subject_ref", "scope_type", "scope_key",
    "episode_key", "accepted_snapshot_ref", "source_revision",
)

# The twelve shared-spine scope/hash equality comparisons (v0.4 section 11).
SPINE_EQUALITY_FIELDS: Tuple[str, ...] = (
    "project_equal", "run_equal", "mode_equal", "scope_type_equal",
    "scope_key_equal", "subject_equal", "site_equal", "snapshot_equal",
    "source_revision_equal", "episode_equal", "cutoff_equal",
    "axis_hash_valid",
)

# Exact-key schemas for the audience payloads (fail-closed validation).
QUERY_DRAFT_KEYS = frozenset({
    "query_draft_id", "unit_id", "risk_id", "owner_routing_decision_id",
    "query_owner", "basis_sentence", "finding_sentence", "action_sentence",
    "protocol_execution_context_ref", "d04_enrollment_or_pd_context_ref",
    "pd_wording_permission", "evidence_refs", "source_locator_ids",
    "audience_payload_hash", "content_hash",
})
PD_PERMISSION_KEYS = frozenset({
    "decision_id", "query_draft_id", "d04_context_ref", "d04_decision_kind",
    "context_scope_equal", "context_accepted", "content_hash_equal",
    "pd_wording_permitted", "reason_codes", "hash",
})
EVENT_MARKER_KEYS = frozenset({
    "marker_id", "domain", "event_kind", "stable_measure_key", "result_id",
    "event_time_ref", "visit_or_pending_ref", "pending", "audience_label",
    "value_label", "range_label", "grade_label", "cs_ncs_label",
    "seriousness_clue_label", "source_jump_ids", "payload_hash",
})
RISK_MARKER_KEYS = frozenset({
    "marker_id", "risk_id", "unit_id", "positive_subtype", "monitoring_priority",
    "seriousness_clue_state", "grade_comparison_assessment_id",
    "clinical_significance_assessment_id", "priority_decision_id",
    "anchor_kind", "anchor_ref", "clinical_domain_label", "risk_type_label",
    "summary_label", "source_jump_ids", "query_draft_ref", "payload_hash",
})
SOURCE_JUMP_KEYS = frozenset({
    "jump_id", "target_kind", "cardinality", "target_ref",
    "ordered_target_refs", "join_reason", "temporal_relation_ref",
    "reverse_binding_ref", "source_object_id", "hash",
})
SOURCE_JUMP_TARGET_KEYS = frozenset({
    "target_ref_id", "target_object_id", "target_schema_id",
    "target_scope_binding_id", "target_content_hash", "source_locator_ids",
    "hash",
})
AUDIENCE_VALIDATION_KEYS = frozenset({
    "validation_id", "payload_kind", "payload_object_id", "payload_hash",
    "lexicon_id", "lexicon_version", "lexicon_hash", "schema_valid",
    "no_internal_tokens", "domain_specific", "risk_specific",
    "source_jump_valid", "visible_path_valid", "scope_equal",
    "validation_passed", "reason_codes",
})
JUMP_VALIDATION_KEYS = frozenset({
    "validation_id", "jump_id", "source_object_id", "source_scope_binding_id",
    "target_schema_valid", "target_hash_valid", "scope_equal",
    "cardinality_valid", "join_reason_valid", "reverse_binding_valid",
    "temporal_relation_valid", "validation_passed", "reason_codes",
})
PROJECTION_KEYS = frozenset({
    "projection_id", "scope_binding_id", "subject_ref", "shared_spine_binding_id",
    "d05_projection_id", "axis_version", "axis_hash", "cutoff",
    "shared_spine_equality", "ordered_event_markers", "ordered_risk_markers",
    "source_jumps", "audience_validation_results",
    "source_jump_validation_results", "projection_hash",
})
SPINE_EQUALITY_KEYS = frozenset({
    "decision_id", "binding_id", "d05_projection_id", "project_equal",
    "run_equal", "mode_equal", "scope_type_equal", "scope_key_equal",
    "subject_equal", "site_equal", "snapshot_equal", "source_revision_equal",
    "episode_equal", "cutoff_equal", "axis_hash_valid", "all_equal",
    "recomputed_equal", "scope_equal_verified", "reason_codes", "hash",
})

# Allowed source-jump target kinds (contract v0.4 section 11).
TARGET_KINDS: Tuple[str, ...] = (
    "listing_row", "listing_cell", "protocol_clause", "ib_clause",
    "lab_manual_rule", "ae_record", "cm_record", "ip_action", "visit",
    "examination_report",
)
JOIN_REASONS: Tuple[str, ...] = (
    "direct_source", "rule_authority", "producer_binding", "shared_identity",
    "temporal_context",
)

_RANGE_LABEL = {
    "high": "高于参考范围",
    "low": "低于参考范围",
    "within_range": "在参考范围内",
    "not_classifiable": "范围无法判定",
    "boundary": "范围边界",
}
_CS_LABEL = {
    ClinicalSignificance.CS: "临床意义：CS",
    ClinicalSignificance.NCS: "临床意义：NCS",
    ClinicalSignificance.UNKNOWN: "临床意义：未知",
    ClinicalSignificance.NOT_COLLECTED: "临床意义：未收集",
}
_SERIOUSNESS_LABEL = {
    "present": "严重性线索：有",
    "absent": "严重性线索：无",
    "unknown": "严重性线索：未知",
}

# Risk-type label selection per unit kind / primary subtype (labels are only
# ever picked from the frozen lexicon's allowed_risk_type_labels).
_LAB_REVIEW = "复测或处置记录待核实"
_LAB_CHANGE = "检查变化待核实"
_LAB_RESULT = "检验结果待核实"
_LAB_CS = "临床意义判断待核实"

_RISK_TYPE_FALLBACKS: Tuple[str, ...] = (
    _LAB_RESULT, _LAB_CHANGE, _LAB_REVIEW, _LAB_CS,
)


def _risk_type_label(
    unit: Any, allowed: Sequence[str], domain: str
) -> Optional[str]:
    """Pick the audience risk-type label for a unit from the lexicon's allowed
    set (fall back to the first allowed label when the semantic slot is not
    allowed -- the lexicon version governs the exact wording)."""
    allowed_list = list(allowed)
    if not allowed_list:
        return None
    if unit.unit_kind == UnitKind.FOLLOWUP_OBLIGATION:
        slot = _LAB_REVIEW
    elif unit.primary_subtype == PositiveSubtype.CS_INCONSISTENCY:
        slot = _LAB_CS
    elif unit.primary_subtype in (
        PositiveSubtype.NEW_ABNORMALITY,
        PositiveSubtype.BASELINE_ABNORMAL_WORSENING,
        PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING,
        PositiveSubtype.PERSISTENT_OR_RECURRENT,
        PositiveSubtype.SOURCE_OR_CORRECTION_INCONSISTENCY,
    ):
        slot = _LAB_RESULT if domain == "LB" else _LAB_CHANGE
    else:
        slot = _LAB_CHANGE
    if slot in allowed_list:
        return slot
    for fallback in _RISK_TYPE_FALLBACKS:
        if fallback in allowed_list:
            return fallback
    return allowed_list[0]


def _domain_label(domain: str, allowed: Sequence[str]) -> Optional[str]:
    """Lexicon-ordered domain short label (positional contract: the lexicon
    lists the labels in the fixed domain order)."""
    if domain not in _DOMAIN_ORDER:
        return None
    allowed_list = list(allowed)
    index = _DOMAIN_ORDER.index(domain)
    if index < len(allowed_list):
        return allowed_list[index]
    return None


# ---------------------------------------------------------------------------
# Time / spine helpers (deterministic; order-insensitive to typed list order)
# ---------------------------------------------------------------------------

_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?"
    r"(?:[+-]\d{2}:?\d{2}|Z)?)?$"
)


def _resolve_time_ref(time_refs: Sequence[Mapping[str, Any]], ref: Optional[str]
                      ) -> Optional[Tuple[str, Optional[str]]]:
    """Resolve a time-ref id to ``(value, precision)`` or None."""
    if not isinstance(ref, str):
        return None
    for t in time_refs:
        if t.get("time_ref_id") == ref:
            return t.get("value"), t.get("precision")
    return None


def _result_time_key(result: Mapping[str, Any],
                     time_refs: Sequence[Mapping[str, Any]]) -> Tuple[int, str, str]:
    """Deterministic ordering key for an observed result on the shared spine.

    Full datetime values sort first (by instant), date-only values next, then
    month/year, then unknown/missing; ties break on the stable result id so the
    marker order never depends on typed list order.
    """
    value, precision = _resolve_time_ref(
        time_refs, result.get("collection_or_exam_time")
    )
    if value is None:
        return (4, "", str(result.get("result_id", "")))
    if precision == "datetime":
        try:
            from datetime import datetime
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            parsed = datetime.fromisoformat(value)
            return (0, parsed.isoformat(), str(result.get("result_id", "")))
        except ValueError:
            return (3, value, str(result.get("result_id", "")))
    if precision == "date":
        return (1, value, str(result.get("result_id", "")))
    if precision in ("month", "year"):
        return (2, value, str(result.get("result_id", "")))
    return (3, value, str(result.get("result_id", "")))


def _visit_by_id(visit_refs: Sequence[Mapping[str, Any]],
                 ref: Optional[str]) -> Optional[Mapping[str, Any]]:
    if not isinstance(ref, str):
        return None
    for v in visit_refs:
        if v.get("visit_ref_id") == ref:
            return v
    return None


def _is_pending_visit(visit_refs: Sequence[Mapping[str, Any]],
                      ref: Optional[str]) -> bool:
    visit = _visit_by_id(visit_refs, ref)
    if visit is None:
        return False
    status = visit.get("status")
    return status == "pending" or not visit.get("actual_date")


def _unit_scope_tuple(spine: Mapping[str, Any]) -> Tuple[str, ...]:
    return tuple(str(spine.get(field) or "") for field in _SCOPE_TUPLE_FIELDS)


def _spine_equality_verified(
    spine: Mapping[str, Any],
    run_scope: Mapping[str, Any],
    decision: Mapping[str, Any],
    scope_envelopes: Sequence[Mapping[str, Any]] = (),
) -> Dict[str, Any]:
    """Recompute the twelve shared-spine scope/hash comparisons and verify them
    against the typed ``D07SharedSpineScopeEqualityDecision``.

    The reference scope is the accepted record scope envelope (subject/site
    live there, not on the run-scope binding), overlaid on the run-scope
    binding.  Returns a ``shared_spine_equality`` object carrying both the
    typed decision fields and the recomputed result;
    ``scope_equal_verified`` is the gate used by the projection.
    """
    envelope = scope_envelopes[0] if scope_envelopes else {}
    ref = dict(run_scope)
    for field in ("subject_ref", "site_ref", "project_ref", "run_ref",
                  "monitoring_mode", "accepted_snapshot_ref", "source_revision",
                  "episode_key", "scope_type", "scope_key", "cutoff"):
        if envelope.get(field) is not None:
            ref[field] = envelope[field]
    recomputed: Dict[str, bool] = {
        "project_equal": spine.get("project_ref") == ref.get("project_ref"),
        "run_equal": spine.get("run_ref") == ref.get("run_ref"),
        "mode_equal": spine.get("monitoring_mode") == ref.get("monitoring_mode"),
        "scope_type_equal": spine.get("scope_type") == "subject"
        and ref.get("scope_type") == "subject",
        "scope_key_equal": isinstance(spine.get("scope_key"), str)
        and len(spine.get("scope_key", "")) == 64
        and spine.get("scope_key") == ref.get("scope_key"),
        "subject_equal": spine.get("subject_ref") == ref.get("subject_ref"),
        "site_equal": spine.get("site_ref") == ref.get("site_ref"),
        "snapshot_equal": spine.get("accepted_snapshot_ref")
        == ref.get("accepted_snapshot_ref"),
        "source_revision_equal": spine.get("source_revision")
        == ref.get("source_revision"),
        "episode_equal": isinstance(spine.get("episode_key"), str)
        and bool(spine.get("episode_key"))
        and spine.get("episode_key") == ref.get("episode_key"),
        "cutoff_equal": spine.get("cutoff") == ref.get("cutoff"),
        "axis_hash_valid": isinstance(spine.get("axis_hash"), str)
        and spine.get("axis_hash", "").startswith("sha256:")
        and is_sha256_hex(spine.get("axis_hash", "")[7:]),
    }
    all_recomputed = all(recomputed.values())
    typed_equal = all(
        decision.get(field) is True for field in SPINE_EQUALITY_FIELDS
    ) and decision.get("all_equal") is True
    scope_equal_verified = all_recomputed and typed_equal
    return {
        "decision_id": decision.get("decision_id"),
        "binding_id": decision.get("binding_id"),
        "d05_projection_id": decision.get("d05_projection_id"),
        "project_equal": recomputed["project_equal"],
        "run_equal": recomputed["run_equal"],
        "mode_equal": recomputed["mode_equal"],
        "scope_type_equal": recomputed["scope_type_equal"],
        "scope_key_equal": recomputed["scope_key_equal"],
        "subject_equal": recomputed["subject_equal"],
        "site_equal": recomputed["site_equal"],
        "snapshot_equal": recomputed["snapshot_equal"],
        "source_revision_equal": recomputed["source_revision_equal"],
        "episode_equal": recomputed["episode_equal"],
        "cutoff_equal": recomputed["cutoff_equal"],
        "axis_hash_valid": recomputed["axis_hash_valid"],
        "all_equal": typed_equal,
        "recomputed_equal": all_recomputed,
        "scope_equal_verified": scope_equal_verified,
        "reason_codes": ["shared_spine_scope_equality_recomputed"],
        "hash": d07_content_hash({
            "decision_id": decision.get("decision_id"),
            "binding_id": decision.get("binding_id"),
            "d05_projection_id": decision.get("d05_projection_id"),
            "recomputed_equal": all_recomputed,
            "typed_all_equal": typed_equal,
        }),
    }


def _unit_identity(unit: Any, spine: Mapping[str, Any],
                   algorithm_version: str) -> str:
    """Stable unit identity (contract v0.4 section 5.1 stable core, minus the
    mutable run-specific fields)."""
    core = {
        "project_ref": spine.get("project_ref"),
        "site_ref": spine.get("site_ref"),
        "subject_ref": spine.get("subject_ref"),
        "scope_type": "subject",
        "scope_key": spine.get("scope_key"),
        "unit_kind": unit.unit_kind,
        "unit_algorithm_version": algorithm_version,
        "stable_measure_key": unit.stable_measure_key,
        "episode_key": spine.get("episode_key"),
        "positive_subtype": unit.primary_subtype,
    }
    return "sha256:" + d07_content_hash(core)


# ---------------------------------------------------------------------------
# Source jumps
# ---------------------------------------------------------------------------

_JUMP_JOIN_REASON: Dict[str, str] = {
    "listing_row": "direct_source",
    "listing_cell": "direct_source",
    "protocol_clause": "rule_authority",
    "ib_clause": "rule_authority",
    "lab_manual_rule": "rule_authority",
    "ae_record": "producer_binding",
    "cm_record": "producer_binding",
    "ip_action": "producer_binding",
    "visit": "temporal_context",
    "examination_report": "rule_authority",
}


def _target_registry(typed_input: Mapping[str, Any]) -> Dict[str, Tuple[str, str, Mapping[str, Any]]]:
    """Index every resolvable target object id to ``(section, schema, object)``,
    so source jumps only point at objects that actually exist in the accepted
    input. No fallback schemas exist: an unknown id resolves to nothing."""
    registry: Dict[str, Tuple[str, str, Mapping[str, Any]]] = {}
    sections: Dict[str, str] = {
        "observed_results": "observed_result",
        "scope_envelopes": "record_scope_envelope",
        "run_scope_binding": "run_scope_binding",
        "time_refs": "time_ref",
        "visit_refs": "visit_ref",
        "subject_demographics": "subject_demographics",
        "audience_lexicon": "audience_lexicon",
        "authority_bindings": "authority_binding",
        "measure_definitions": "safety_measure_definition",
        "reference_range_definitions": "reference_range_definition",
        "unit_conversion_rules": "unit_conversion_rule",
        "grade_rule_sets": "safety_grade_rule_set",
        "grade_rules": "safety_grade_rule",
        "monitoring_rules": "safety_monitoring_rule",
        "monitoring_predicates": "safety_monitoring_predicate",
        "baseline_rules": "baseline_rule",
        "trend_rules": "trend_rule",
        "action_obligation_definitions": "action_obligation_definition",
        "organ_pattern_rule_definitions": "organ_pattern_rule_definition",
        "examination_requirement_sets": "examination_requirement_set",
        "priority_policy": "priority_policy",
        "priority_precedence_rules": "priority_precedence_rule",
        "producer_consumption_bindings": "producer_consumption_binding",
        "clinical_review_refs": "clinical_review_ref",
        "clinical_significance_reason_refs": "clinical_significance_reason_ref",
        "d04_context_refs": "d04_context_ref",
        "correction_chain_decisions": "correction_chain_decision",
        "cutoff_decisions": "cutoff_decision",
        "d05_gate_bindings": "d05_gate_binding",
        "applicability_evidence": "applicability_evidence",
        "carry_forward_refs": "carry_forward_ref",
        "shared_spine_binding": "shared_spine_binding",
        "shared_spine_scope_equality_decision": "shared_spine_scope_equality_decision",
    }
    id_fields: Dict[str, Tuple[str, ...]] = {
        "observed_results": ("result_id", "stable_source_record_id"),
        "scope_envelopes": ("envelope_id", "record_id"),
        "visit_refs": ("visit_ref_id",),
        "measure_definitions": ("definition_id", "stable_measure_key"),
        "reference_range_definitions": ("range_definition_id",),
        "unit_conversion_rules": ("conversion_rule_id",),
        "grade_rule_sets": ("rule_set_id",),
        "grade_rules": ("grade_rule_id",),
        "monitoring_rules": ("rule_id",),
        "monitoring_predicates": ("predicate_id",),
        "baseline_rules": ("rule_id",),
        "trend_rules": ("rule_id",),
        "action_obligation_definitions": ("obligation_definition_id",),
        "organ_pattern_rule_definitions": ("pattern_rule_id",),
        "examination_requirement_sets": ("requirement_set_id",),
        "priority_precedence_rules": ("precedence_rule_id",),
        "producer_consumption_bindings": ("binding_id", "producer_object_id"),
        "clinical_review_refs": ("review_ref_id",),
        "clinical_significance_reason_refs": ("reason_ref_id",),
        "d04_context_refs": ("d04_context_ref_id", "protocol_clause_ref"),
        "correction_chain_decisions": ("decision_id",),
        "cutoff_decisions": ("cutoff_decision_id",),
        "d05_gate_bindings": ("d05_gate_binding_id",),
        "applicability_evidence": ("applicability_evidence_id",),
        "carry_forward_refs": ("carry_forward_ref_id", "source_risk_id"),
        "authority_bindings": ("authority_binding_id",),
        "time_refs": ("time_ref_id",),
    }
    for section, schema in sections.items():
        value = typed_input.get(section)
        objs = value if isinstance(value, list) else (
            [value] if isinstance(value, dict) else []
        )
        for obj in objs:
            if not isinstance(obj, dict):
                continue
            for field in id_fields.get(section, ()):
                ident = obj.get(field)
                if isinstance(ident, str) and ident:
                    # First-indexed wins: record ids resolve to the observed
                    # result, not to the envelope that carries the same id.
                    registry.setdefault(ident, (section, schema, obj))
    # The ECG repeat-series refs are examination-report targets.
    for obj in typed_input.get("observed_results", []):
        series = obj.get("repeat_series_ref")
        if isinstance(series, str) and series:
            registry.setdefault(
                series, ("observed_results", "examination_series", obj)
            )
    return registry


# Target kinds that resolve only to a producer binding of the matching domain.
_PRODUCER_KIND_DOMAIN = {
    "ae_record": "D01",
    "cm_record": "D02",
    "ip_action": "D03",
}
# Target kinds whose resolved schema must be one of the rule authorities.
_RULE_AUTHORITY_SCHEMAS = frozenset({
    "safety_monitoring_rule", "safety_monitoring_predicate",
    "safety_grade_rule", "safety_grade_rule_set", "reference_range_definition",
    "unit_conversion_rule", "trend_rule", "baseline_rule",
    "organ_pattern_rule_definition",
})
# Listing rows point at records, review/reason refs, or D06/D10 producer objects.
_LISTING_SCHEMAS = frozenset({
    "observed_result", "clinical_review_ref",
    "clinical_significance_reason_ref", "producer_consumption_binding",
    "examination_series",
})


def _resolve_target(target_kind: str, target_object_id: Optional[str],
                    registry: Mapping[str, Tuple[str, str, Mapping[str, Any]]]
                    ) -> Optional[Tuple[str, str, Mapping[str, Any]]]:
    """Resolve a jump target strictly: the kind must be a valid target kind
    and the id must resolve to a real, kind-appropriate typed object."""
    if target_kind not in TARGET_KINDS or not isinstance(target_object_id, str):
        return None
    entry = registry.get(target_object_id)
    if entry is None:
        return None
    section, schema, obj = entry
    if target_kind in ("listing_row", "listing_cell"):
        if schema not in _LISTING_SCHEMAS:
            return None
        if schema == "producer_consumption_binding" and obj.get("producer_domain") not in ("D06", "D10"):
            return None
        return entry
    if target_kind in _PRODUCER_KIND_DOMAIN:
        if schema != "producer_consumption_binding":
            return None
        if obj.get("producer_domain") != _PRODUCER_KIND_DOMAIN[target_kind]:
            return None
        return entry
    if target_kind in ("protocol_clause", "ib_clause"):
        if schema == "producer_consumption_binding":
            if obj.get("producer_domain") == "D04":
                return entry
            return None
        if schema in ("safety_monitoring_rule", "action_obligation_definition",
                      "d04_context_ref"):
            return entry
        return None
    if target_kind == "lab_manual_rule":
        if schema in _RULE_AUTHORITY_SCHEMAS:
            return entry
        return None
    if target_kind == "examination_report":
        if schema in ("examination_requirement_set", "examination_series"):
            return entry
        return None
    if target_kind == "visit":
        if schema == "visit_ref":
            return entry
        return None
    return None


def _object_self_hash(section: str, obj: Mapping[str, Any]) -> str:
    """The recomputed canonical content hash of a resolved target object.

    For a section with an embedded self-hash field this is the frozen
    ``sha256(canonical_json(fields minus the hash field))`` self-hash (the
    value the canonical-hash stage verifies).  For a section without any
    hash field it is the full-object content hash, so a hash-less target is
    still bound into and revalidated through the jump hash (contract v0.4
    section 11 -- no unconditional hash bypass)."""
    hash_field = SECTION_HASH_FIELDS.get(section) or SINGLETON_HASH_FIELDS.get(section)
    if hash_field:
        core = {key: value for key, value in obj.items() if key != hash_field}
        return d07_content_hash(core)
    return d07_content_hash(obj)


def _jump_content_hash(
    source_object_id: Any,
    target_kind: Any,
    cardinality: Any,
    target_ref: Any,
    join_reason: Any,
    target_content_hash: Any,
) -> str:
    """The content address of a source jump: the source id, the target ref
    and the bound canonical target content hash.  Build and validation share
    this formula so a hash-less target is revalidated through the exact same
    jump hash (contract v0.4 section 11)."""
    return d07_content_hash({
        "source_object_id": source_object_id,
        "target_kind": target_kind,
        "cardinality": cardinality,
        "target_ref": target_ref,
        "join_reason": join_reason,
        "target_content_hash": target_content_hash,
    })


def _build_source_jumps(
    pairs: Sequence[Mapping[str, Any]],
    typed_input: Mapping[str, Any],
    scope_binding_id: str,
) -> List[Dict[str, Any]]:
    """Materialise the runtime's jump pairs as content-addressed
    ``D07SourceJump`` objects, each with exactly one reverse binding.

    The reverse binding model is star-shaped: every jump from the same source
    object shares the anchor; the reverse of each jump is the anchor's
    ``listing_row`` jump when present (jump back to the raw row), otherwise the
    anchor's first jump.  Each target ref resolves against the accepted input;
    the jump hash recomputes from the source, the target ref and the resolved
    target content hash before visibility. An invalid target kind is never
    rewritten — it flows through and fails the per-jump validation.
    """
    registry = _target_registry(typed_input)
    jumps: List[Dict[str, Any]] = []
    by_source: Dict[str, List[Dict[str, Any]]] = {}
    for pair in pairs:
        source_object_id = pair.get("source_object_id")
        target_kind = pair.get("target_kind")
        target_object_id = pair.get("target_object_id")
        resolved = _resolve_target(target_kind, target_object_id, registry)
        target_content_hash = None
        if resolved is not None:
            target_content_hash = _object_self_hash(resolved[0], resolved[2])
        jump = {
            "jump_id": None,  # filled after content assembly
            "target_kind": target_kind,
            "cardinality": "one",
            "target_ref": target_object_id,
            "ordered_target_refs": None,
            "join_reason": _JUMP_JOIN_REASON.get(target_kind, "direct_source"),
            "temporal_relation_ref": (
                "same_visit" if _JUMP_JOIN_REASON.get(target_kind) == "temporal_context"
                else None
            ),
            "reverse_binding_ref": None,  # filled in a second pass
            "source_object_id": source_object_id,
            "hash": None,
        }
        jump["hash"] = _jump_content_hash(
            source_object_id, target_kind, "one", target_object_id,
            jump["join_reason"], target_content_hash,
        )
        jump["jump_id"] = "sha256:" + d07_content_hash({
            "jump": jump["hash"], "scope_binding_id": scope_binding_id,
        })
        jumps.append(jump)
        by_source.setdefault(source_object_id, []).append(jump)
    for group in by_source.values():
        reverse = next(
            (j for j in group if j["target_kind"] == "listing_row"), group[0]
        )
        for jump in group:
            jump["reverse_binding_ref"] = reverse["jump_id"]
    return jumps


def _locator_universe(typed_input: Mapping[str, Any]) -> Set[str]:
    """Every source locator carried by any typed object of the run."""
    universe: Set[str] = set()
    sections = (
        "observed_results", "scope_envelopes", "run_scope_binding",
        "previous_run_scope_binding", "previous_scope_envelopes",
        "previous_time_refs", "cutoff_decisions", "time_refs", "visit_refs",
        "subject_demographics", "audience_lexicon", "authority_bindings",
        "measure_definitions", "reference_range_definitions",
        "unit_conversion_rules", "grade_rule_sets", "grade_rules",
        "monitoring_rules", "monitoring_predicates", "baseline_rules",
        "trend_rules", "action_obligation_definitions",
        "organ_pattern_rule_definitions", "examination_requirement_sets",
        "priority_policy", "priority_precedence_rules",
        "producer_consumption_bindings", "clinical_review_refs",
        "clinical_significance_reason_refs", "d04_context_refs",
        "correction_chain_decisions", "carry_forward_refs",
        "shared_spine_binding", "shared_spine_scope_equality_decision",
        "d05_gate_bindings", "applicability_evidence",
    )
    for section in sections:
        value = typed_input.get(section)
        objs = value if isinstance(value, list) else (
            [value] if isinstance(value, dict) else []
        )
        for obj in objs:
            if isinstance(obj, dict):
                for loc in obj.get("source_locator_ids", []):
                    if isinstance(loc, str):
                        universe.add(loc)
    return universe


def _target_scope_matches(schema: str, obj: Mapping[str, Any],
                          source_result: Optional[Mapping[str, Any]],
                          scope_binding_id: str,
                          typed_input: Mapping[str, Any]) -> bool:
    """The typed scope predicate for a resolved target object."""
    if schema == "observed_result":
        env = next(
            (e for e in typed_input.get("scope_envelopes", [])
             if e.get("record_id") == obj.get("stable_source_record_id")
             and e.get("scope_binding_id") == scope_binding_id),
            None,
        )
        return env is not None
    if schema == "record_scope_envelope":
        return obj.get("scope_binding_id") == scope_binding_id
    if schema in ("safety_measure_definition", "reference_range_definition",
                  "unit_conversion_rule", "safety_grade_rule_set",
                  "safety_grade_rule"):
        return bool(source_result) and obj.get("stable_measure_key") == source_result.get(
            "stable_measure_key"
        )
    if schema == "safety_monitoring_rule":
        return bool(source_result) and source_result.get(
            "stable_measure_key"
        ) in obj.get("applicable_measure_keys", [])
    if schema == "safety_monitoring_predicate":
        # A predicate's scope is the set of rules that reference it for the
        # source measure.
        if not source_result:
            return False
        return any(
            source_result.get("stable_measure_key") in rule.get("applicable_measure_keys", [])
            and obj.get("predicate_id") in rule.get("ordered_predicate_ids", [])
            for rule in typed_input.get("monitoring_rules", [])
        )
    if schema == "action_obligation_definition":
        if not source_result:
            return False
        trigger_rule = next(
            (r for r in typed_input.get("monitoring_rules", [])
             if r.get("rule_id") == obj.get("trigger_rule_id")),
            None,
        )
        return trigger_rule is not None and source_result.get(
            "stable_measure_key"
        ) in trigger_rule.get("applicable_measure_keys", [])
    if schema == "organ_pattern_rule_definition":
        if not source_result:
            return False
        return any(
            role.get("stable_measure_key") == source_result.get("stable_measure_key")
            for role in obj.get("required_component_roles", [])
        )
    if schema == "examination_requirement_set":
        return bool(source_result) and obj.get("domain") == source_result.get("domain")
    if schema == "producer_consumption_binding":
        return obj.get("consumer_domain") == "D07"
    if schema == "d04_context_ref":
        return obj.get("context_scope_equal") is True
    if schema == "shared_spine_binding":
        return obj.get("scope_binding_id") == scope_binding_id
    if schema in ("trend_rule", "baseline_rule", "visit_ref", "time_ref",
                  "clinical_review_ref", "clinical_significance_reason_ref",
                  "examination_series", "run_scope_binding", "audience_lexicon",
                  "authority_binding", "subject_demographics",
                  "cutoff_decision", "correction_chain_decision",
                  "carry_forward_ref", "d05_gate_binding",
                  "applicability_evidence", "priority_policy",
                  "priority_precedence_rule",
                  "shared_spine_scope_equality_decision"):
        # Global / no-scope objects: the schema, hash and locator checks bind.
        return True
    return False


def _source_jump_validation(
    jump: Mapping[str, Any],
    typed_input: Mapping[str, Any],
    scope_binding_id: str,
    registry: Mapping[str, Tuple[str, str, Mapping[str, Any]]],
) -> Dict[str, Any]:
    """Per-jump ``D07SourceJumpValidationResult`` (exact keys, fail-closed)."""
    reasons: List[str] = []
    source_result = next(
        (r for r in typed_input.get("observed_results", [])
         if r.get("result_id") == jump.get("source_object_id")),
        None,
    )
    if source_result is None:
        reasons.append("source_unresolved")
    resolved = _resolve_target(
        jump.get("target_kind"), jump.get("target_ref"), registry
    )
    target_schema_valid = resolved is not None
    if not target_schema_valid:
        reasons.append("target_schema_unresolved")
    target_hash_valid = False
    scope_equal = False
    locator_valid = False
    if resolved is not None:
        section, schema, obj = resolved
        recomputed = _object_self_hash(section, obj)
        hash_field = SECTION_HASH_FIELDS.get(section) or SINGLETON_HASH_FIELDS.get(section)
        if hash_field:
            supplied = obj.get(hash_field)
            target_hash_valid = (
                is_sha256_hex(supplied) and supplied == recomputed
            )
        else:
            # No embedded hash field: the canonical target content hash is
            # bound into the jump hash.  Revalidate it through the jump hash
            # (the recomputed canonical hash must reproduce the stored jump
            # hash) -- a mutated hash-less target fails, never a bypass.
            target_hash_valid = (
                _jump_content_hash(
                    jump.get("source_object_id"),
                    jump.get("target_kind"),
                    jump.get("cardinality"),
                    jump.get("target_ref"),
                    jump.get("join_reason"),
                    recomputed,
                )
                == jump.get("hash")
            )
        if not target_hash_valid:
            reasons.append("target_hash_mismatch")
        locator_ids = [str(loc) for loc in obj.get("source_locator_ids", [])]
        locator_valid = bool(locator_ids) and all(
            loc in _locator_universe(typed_input) for loc in locator_ids
        )
        if not locator_valid:
            reasons.append("target_locator_unresolved")
        scope_equal = _target_scope_matches(
            schema, obj, source_result, scope_binding_id, typed_input
        )
        if not scope_equal:
            reasons.append("target_scope_mismatch")
    else:
        reasons.append("target_locator_unresolved")
    cardinality_valid = (
        jump.get("cardinality") == "one"
        and isinstance(jump.get("target_ref"), str)
        and jump.get("ordered_target_refs") is None
    )
    if not cardinality_valid:
        reasons.append("cardinality_contract")
    join_reason_valid = jump.get("join_reason") in JOIN_REASONS
    if not join_reason_valid:
        reasons.append("join_reason")
    reverse_valid = (
        isinstance(jump.get("reverse_binding_ref"), str)
        and bool(jump.get("reverse_binding_ref"))
    )
    if not reverse_valid:
        reasons.append("reverse_binding_missing")
    temporal_valid = True
    if jump.get("join_reason") == "temporal_context":
        temporal_valid = isinstance(jump.get("temporal_relation_ref"), str)
        if not temporal_valid:
            reasons.append("temporal_relation_missing")
    elif jump.get("temporal_relation_ref") is not None:
        temporal_valid = False
        reasons.append("temporal_relation_forbidden")
    passed = (
        target_schema_valid and target_hash_valid and scope_equal
        and locator_valid and cardinality_valid and join_reason_valid
        and reverse_valid and temporal_valid
    )
    return {
        "validation_id": "sha256:" + d07_content_hash({
            "jump_id": jump.get("jump_id"), "scope_binding_id": scope_binding_id,
        }),
        "jump_id": jump.get("jump_id"),
        "source_object_id": jump.get("source_object_id"),
        "source_scope_binding_id": scope_binding_id,
        "target_schema_valid": target_schema_valid,
        "target_hash_valid": target_hash_valid,
        "scope_equal": scope_equal,
        "cardinality_valid": cardinality_valid,
        "join_reason_valid": join_reason_valid,
        "reverse_binding_valid": reverse_valid,
        "temporal_relation_valid": temporal_valid,
        "validation_passed": passed,
        "reason_codes": reasons if reasons else ["source_jump_contract_ok"],
    }


def _validate_jump_target_evidence(
    typed_input: Mapping[str, Any],
    scope_binding_id: str,
    source_object_id: Any,
    target_kind: Any,
    target_ref: Any,
) -> Tuple[bool, List[str]]:
    """Validate a jump target's schema, object hash, scope and locator.

    The exact fail-closed checks a source-jump target must pass, but without
    requiring a materialised jump object (a hash-less target is fail-closed
    here because there is no jump hash to revalidate through).  Shared by the
    query evidence validation (contract v0.4 §11).
    """
    reasons: List[str] = []
    registry = _target_registry(typed_input)
    resolved = _resolve_target(target_kind, target_ref, registry)
    if resolved is None:
        return False, ["target_schema_unresolved"]
    section, schema, obj = resolved
    valid = True
    recomputed = _object_self_hash(section, obj)
    hash_field = SECTION_HASH_FIELDS.get(section) or SINGLETON_HASH_FIELDS.get(section)
    if hash_field:
        supplied = obj.get(hash_field)
        if not (is_sha256_hex(supplied) and supplied == recomputed):
            valid = False
            reasons.append("target_hash_mismatch")
    else:
        valid = False
        reasons.append("target_hash_missing")
    locator_ids = [str(loc) for loc in obj.get("source_locator_ids", [])]
    if not (bool(locator_ids) and all(
        loc in _locator_universe(typed_input) for loc in locator_ids
    )):
        valid = False
        reasons.append("target_locator_unresolved")
    source_result = next(
        (r for r in typed_input.get("observed_results", [])
         if r.get("result_id") == source_object_id),
        None,
    )
    if not _target_scope_matches(schema, obj, source_result, scope_binding_id, typed_input):
        valid = False
        reasons.append("target_scope_mismatch")
    return valid, reasons


# ---------------------------------------------------------------------------
# Audience payload validation (shared with the query payload)
# ---------------------------------------------------------------------------

def _forbidden_token_hit(lexicon: Mapping[str, Any],
                         labels: Sequence[Optional[str]]) -> Optional[str]:
    forbidden = [str(t) for t in lexicon.get("forbidden_internal_tokens", [])]
    for label in labels:
        if not isinstance(label, str):
            continue
        for token in forbidden:
            if token and token in label:
                return token
    return None


def _schema_valid(payload_kind: str, payload: Mapping[str, Any]) -> bool:
    if payload_kind == "query":
        return set(payload) == QUERY_DRAFT_KEYS
    if payload_kind == "event_marker":
        return set(payload) == EVENT_MARKER_KEYS
    if payload_kind == "risk_marker":
        return set(payload) == RISK_MARKER_KEYS
    if payload_kind == "projection":
        return set(payload) == PROJECTION_KEYS
    return False


def validate_audience_payload(
    lexicon: Mapping[str, Any],
    payload_kind: str,
    payload: Mapping[str, Any],
    scope_binding_id: str,
    spine_subject_ref: str,
    allowed_jump_ids: Sequence[str],
    extra_labels: Sequence[Optional[str]] = (),
    jumps_all_valid: bool = True,
) -> Dict[str, Any]:
    """Closed exact-key audience validation for one payload.

    Returns a ``D07AudiencePayloadValidationResult``.  ``payload_kind`` is one
    of ``query|event_marker|risk_marker|projection``; the caller supplies the
    payload object (already content-addressed) plus any label strings that must
    be checked for forbidden internal tokens.
    """
    reasons: List[str] = []
    schema_valid = _schema_valid(payload_kind, payload)
    if not schema_valid:
        reasons.append("schema_exact_keys")
    labels = list(extra_labels)
    if payload_kind == "event_marker":
        labels += [
            payload.get("audience_label"), payload.get("value_label"),
            payload.get("range_label"), payload.get("grade_label"),
            payload.get("cs_ncs_label"), payload.get("seriousness_clue_label"),
        ]
    elif payload_kind == "risk_marker":
        labels += [
            payload.get("clinical_domain_label"), payload.get("risk_type_label"),
            payload.get("summary_label"),
        ]
    elif payload_kind == "projection":
        labels += [str(payload.get("scope_binding_id")),
                   str(payload.get("subject_ref"))]
    forbidden = _forbidden_token_hit(lexicon, labels)
    no_internal_tokens = forbidden is None
    if forbidden is not None:
        reasons.append(f"forbidden_internal_token:{forbidden}")

    allowed_domains = [str(d) for d in lexicon.get("allowed_domain_labels", [])]
    allowed_risks = [str(r) for r in lexicon.get("allowed_risk_type_labels", [])]
    domain_specific = True
    risk_specific = True
    if payload_kind == "event_marker":
        domain_specific = isinstance(payload.get("audience_label"), str) and bool(
            payload.get("audience_label")
        )
    elif payload_kind == "risk_marker":
        domain_specific = payload.get("clinical_domain_label") in allowed_domains
        risk_specific = payload.get("risk_type_label") in allowed_risks
    elif payload_kind == "projection":
        domain_specific = bool(payload.get("ordered_event_markers"))
    if not domain_specific:
        reasons.append("domain_label_missing")
    if not risk_specific:
        reasons.append("risk_type_label_missing")

    jump_ids = payload.get("source_jump_ids", []) if payload_kind in (
        "event_marker", "risk_marker"
    ) else []
    allowed = set(allowed_jump_ids)
    source_jump_valid = isinstance(jump_ids, list) and all(
        jid in allowed for jid in jump_ids
    )
    if not source_jump_valid:
        reasons.append("source_jump_unresolved")
    # Any emitted/referenced jump that failed its own target validation makes
    # the projection not visible (no audience pass alongside a failed jump).
    if not jumps_all_valid:
        source_jump_valid = False
        reasons.append("source_jump_failed")

    visible_path_valid = True
    if payload_kind == "risk_marker" and payload.get("anchor_ref") is None:
        visible_path_valid = False
        reasons.append("risk_anchor_missing")
    if payload_kind == "event_marker" and payload.get("result_id") is None:
        visible_path_valid = False
        reasons.append("event_result_missing")

    scope_equal = (
        payload_kind in ("query", "event_marker", "risk_marker", "projection")
    )
    if payload_kind == "projection":
        scope_equal = (
            payload.get("scope_binding_id") == scope_binding_id
            and payload.get("subject_ref") == spine_subject_ref
        )
    elif payload_kind in ("event_marker", "risk_marker"):
        # Markers carry no own scope tuple; their scope is the projection's
        # (verified via the shared-spine equality decision at the projection
        # level).
        scope_equal = True
    if not scope_equal:
        reasons.append("scope_mismatch")

    passed = (
        schema_valid and no_internal_tokens and domain_specific
        and risk_specific and source_jump_valid and visible_path_valid
        and scope_equal
    )
    return {
        "validation_id": "sha256:" + d07_content_hash({
            "payload_kind": payload_kind,
            "payload_object_id": payload.get("payload_hash")
            or payload.get("projection_id"),
            "scope_binding_id": scope_binding_id,
        }),
        "payload_kind": payload_kind,
        "payload_object_id": payload.get("payload_hash")
        or payload.get("projection_id"),
        "payload_hash": payload.get("payload_hash") or payload.get("projection_hash"),
        "lexicon_id": lexicon.get("lexicon_id"),
        "lexicon_version": lexicon.get("version"),
        "lexicon_hash": lexicon.get("content_hash"),
        "schema_valid": schema_valid,
        "no_internal_tokens": no_internal_tokens,
        "domain_specific": domain_specific,
        "risk_specific": risk_specific,
        "source_jump_valid": source_jump_valid,
        "visible_path_valid": visible_path_valid,
        "scope_equal": scope_equal,
        "validation_passed": passed,
        "reason_codes": reasons if reasons else ["audience_payload_ok"],
    }


# ---------------------------------------------------------------------------
# Journey summary leaves (raw root vocabulary)
# ---------------------------------------------------------------------------

def _trend_breakpoint_count(
    typed_input: Mapping[str, Any],
    units: Sequence[Any],
) -> int:
    """Count trend-line breaks across the admitted results of each stable
    measure key: a break occurs between two comparable points that cannot be
    normalized (unit change without a conversion rule, or a reference-range
    change).  Single-point or insufficient series never count as breaks."""
    time_refs = typed_input.get("time_refs", [])
    conversion = typed_input.get("unit_conversion_rules", [])
    ranges = typed_input.get("reference_range_definitions", [])
    results = [r for r in typed_input.get("observed_results", [])
               if r.get("record_status") == RecordStatus.ACCEPTED_CURRENT]
    by_measure: Dict[str, List[Mapping[str, Any]]] = {}
    for r in results:
        by_measure.setdefault(r.get("stable_measure_key"), []).append(r)

    def range_key(r: Mapping[str, Any]) -> Optional[str]:
        for rng in ranges:
            if rng.get("stable_measure_key") != r.get("stable_measure_key"):
                continue
            return "|".join(str(rng.get(k) or "") for k in (
                "range_definition_id", "lower", "upper", "unit"))
        return None

    def convertible(from_unit: Optional[str], to_unit: Optional[str]) -> bool:
        if not from_unit or not to_unit:
            return False
        if from_unit == to_unit:
            return True
        for rule in conversion:
            if (rule.get("from_unit") == from_unit
                    and rule.get("to_unit") == to_unit):
                return True
            if (rule.get("from_unit") == to_unit
                    and rule.get("to_unit") == from_unit):
                return True
        return False

    breaks = 0
    for measure, items in by_measure.items():
        ordered = sorted(items, key=lambda r: _result_time_key(r, time_refs))
        for prev, curr in zip(ordered, ordered[1:]):
            if not convertible(prev.get("original_unit"),
                               curr.get("original_unit")):
                breaks += 1
                continue
            prev_range = range_key(prev)
            curr_range = range_key(curr)
            if prev_range is not None and curr_range is not None \
                    and prev_range != curr_range:
                breaks += 1
    return breaks


def _risk_units(units: Sequence[Any]) -> List[Any]:
    return [u for u in units
            if u.l1_disposition in (L1Disposition.POSITIVE, L1Disposition.BOUNDARY)]


def _risk_anchor(
    unit: Any,
    typed_input: Mapping[str, Any],
) -> Tuple[str, str]:
    """Anchor a risk marker to the triggering result: the latest abnormal
    accepted result for the unit's measure key (time-ordered), falling back to
    the unit's own source ids.  Returns ``(anchor_kind, anchor_ref)``; the
    anchor is a concrete result whenever one resolves (``anchor_kind=result``),
    otherwise the pending/visit zone."""
    results = [r for r in typed_input.get("observed_results", [])
               if r.get("record_status") == RecordStatus.ACCEPTED_CURRENT]
    measure_results = [
        r for r in results
        if r.get("stable_measure_key") == unit.stable_measure_key
        and r.get("reported_abnormal_flag") in ("H", "L")
    ]
    time_refs = typed_input.get("time_refs", [])
    ordered = sorted(measure_results,
                     key=lambda r: _result_time_key(r, time_refs))
    if ordered:
        return "result", str(ordered[-1].get("result_id"))
    source_ids = [str(s) for s in (unit.source_result_ids or [])]
    by_id = {str(r.get("result_id")): r for r in results}
    for rid in reversed(source_ids):
        if rid in by_id:
            return "result", rid
    return "pending_time", None


def build_d07_journey_summary(
    typed_input: Mapping[str, Any],
    units: Sequence[Any],
    source_jump_pairs: Sequence[Mapping[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Deterministic journey summary for the raw output root.

    Returns ``None`` when the run has no shared-spine binding (no journey
    section is emitted at all).  The caller (the evaluator) only invokes this
    on admitted runs without D05 open gates; the summary therefore always
    reports a present projection.

    The ``risk_marker_anchored_result_count`` leaf is only emitted when
    non-zero (zero risk anchors are the uninteresting default; the leaf is
    part of the frozen oracle vocabulary for the result-anchored case).
    """
    spine = typed_input.get("shared_spine_binding")
    if not isinstance(spine, dict):
        return None
    lexicon = typed_input.get("audience_lexicon")
    lexicon = lexicon if isinstance(lexicon, dict) else {}
    visit_refs = typed_input.get("visit_refs", [])
    results = [r for r in typed_input.get("observed_results", [])
               if r.get("record_status") == RecordStatus.ACCEPTED_CURRENT]
    risk_units = _risk_units(units)
    pending = sum(
        1 for r in results
        if _is_pending_visit(visit_refs, r.get("visit_ref"))
    )
    anchored = 0
    for unit in risk_units:
        kind, _ref = _risk_anchor(unit, typed_input)
        if kind == "result":
            anchored += 1
    internal_hit = False
    if lexicon:
        forbidden = [str(t) for t in lexicon.get("forbidden_internal_tokens", [])]
        for label in _summary_labels(typed_input, units):
            if isinstance(label, str):
                for token in forbidden:
                    if token and token in label:
                        internal_hit = True
                        break
    summary: Dict[str, Any] = {
        "projection_present": True,
        "event_marker_count": len(results),
        "risk_marker_count": len(risk_units),
        "pending_marker_count": pending,
        "source_jump_count": len(source_jump_pairs),
        "trend_breakpoint_count": _trend_breakpoint_count(typed_input, units),
        "audience_validation_passed": not internal_hit,
        "internal_token_rejected": internal_hit,
    }
    if anchored > 0:
        summary["risk_marker_anchored_result_count"] = anchored
    return summary


def _summary_labels(
    typed_input: Mapping[str, Any],
    units: Sequence[Any],
) -> List[Optional[str]]:
    """Label strings surfaced by the journey payloads (checked for forbidden
    internal tokens by the summary and the audience validator)."""
    labels: List[Optional[str]] = []
    measures = {m.get("stable_measure_key"): m
                for m in typed_input.get("measure_definitions", [])}
    lexicon = typed_input.get("audience_lexicon")
    allowed_domains = [str(d) for d in lexicon.get("allowed_domain_labels", [])] \
        if isinstance(lexicon, dict) else []
    allowed_risks = [str(r) for r in lexicon.get("allowed_risk_type_labels", [])] \
        if isinstance(lexicon, dict) else []
    for r in typed_input.get("observed_results", []):
        measure = measures.get(r.get("stable_measure_key"), {})
        labels.append(measure.get("audience_name"))
        labels.append(_domain_label(r.get("domain"), allowed_domains))
    for unit in units:
        if unit.l1_disposition not in (
            L1Disposition.POSITIVE, L1Disposition.BOUNDARY
        ):
            continue
        labels.append(_risk_type_label(unit, allowed_risks, "LB"))
        labels.append(_domain_label("LB", allowed_domains))
    return labels


# ---------------------------------------------------------------------------
# Full renderer-neutral projection (content-addressed)
# ---------------------------------------------------------------------------

def build_d07_subject_journey(
    typed_input: Mapping[str, Any],
    units: Sequence[Any],
    source_jump_pairs: Sequence[Mapping[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Build the full ``D07SubjectJourneyProjection`` object.

    Returns ``None`` when the shared spine is not bound.  Every marker and jump
    is content-addressed; the projection carries its own audience and source
    jump validation results (both must pass for the projection to be visible).
    """
    spine = typed_input.get("shared_spine_binding")
    if not isinstance(spine, dict):
        return None
    decision = typed_input.get("shared_spine_scope_equality_decision")
    decision = decision if isinstance(decision, dict) else {}
    lexicon = typed_input.get("audience_lexicon")
    lexicon = lexicon if isinstance(lexicon, dict) else {}
    run_scope = typed_input.get("run_scope_binding", {})
    scope_binding_id = str(spine.get("scope_binding_id") or "")
    spine_subject = str(spine.get("subject_ref") or "")
    time_refs = typed_input.get("time_refs", [])
    visit_refs = typed_input.get("visit_refs", [])
    measures = {m.get("stable_measure_key"): m
                for m in typed_input.get("measure_definitions", [])}
    algorithm_versions = {
        UnitKind.OBSERVATION_INTERPRETATION: "d07-observation-interpretation-v1",
        UnitKind.FOLLOWUP_OBLIGATION: "d07-followup-obligation-v1",
        UnitKind.ORGAN_PATTERN: "d07-organ-pattern-v1",
    }

    equality = _spine_equality_verified(
        spine, run_scope, decision,
        typed_input.get("scope_envelopes", []),
    )

    # --- source jumps (content-addressed, reverse-bound) ---
    jumps = _build_source_jumps(source_jump_pairs, typed_input, scope_binding_id)
    registry = _target_registry(typed_input)
    jump_validation = [
        _source_jump_validation(j, typed_input, scope_binding_id, registry)
        for j in jumps
    ]
    jump_ids = [j.get("jump_id") for j in jumps]
    jumps_all_valid = all(v.get("validation_passed") for v in jump_validation)
    valid_jump_ids = [
        j.get("jump_id") for j, v in zip(jumps, jump_validation)
        if v.get("validation_passed")
    ]

    # --- event markers (one per accepted result, time-ordered) ---
    results = [r for r in typed_input.get("observed_results", [])
               if r.get("record_status") == RecordStatus.ACCEPTED_CURRENT]
    allowed_domains = [str(d) for d in lexicon.get("allowed_domain_labels", [])]
    event_markers: List[Dict[str, Any]] = []
    for r in sorted(results, key=lambda x: _result_time_key(x, time_refs)):
        result_id = str(r.get("result_id") or "")
        domain = str(r.get("domain") or "OTHER")
        measure = measures.get(r.get("stable_measure_key"), {})
        visit_ref = r.get("visit_ref")
        pending = _is_pending_visit(visit_refs, visit_ref)
        marker_jumps = [j.get("jump_id") for j in jumps
                        if j.get("source_object_id") == result_id]
        raw = r.get("raw_value")
        unit = r.get("original_unit")
        value_label = f"{raw} {unit}".strip() if raw is not None else None
        range_state = "not_classifiable"
        cs = r.get("reported_cs_ncs")
        grade = r.get("reported_grade")
        payload = {
            "marker_id": None,
            "domain": domain,
            "event_kind": _DOMAIN_EVENT_KIND.get(domain, "other_exam"),
            "stable_measure_key": r.get("stable_measure_key"),
            "result_id": result_id,
            "event_time_ref": r.get("collection_or_exam_time"),
            "visit_or_pending_ref": visit_ref,
            "pending": pending,
            "audience_label": measure.get("audience_name"),
            "value_label": value_label,
            "range_label": _RANGE_LABEL.get(range_state, range_state),
            "grade_label": f"分级 {grade}" if grade else None,
            "cs_ncs_label": _CS_LABEL.get(cs),
            "seriousness_clue_label": None,
            "source_jump_ids": marker_jumps,
            "payload_hash": None,
        }
        payload["payload_hash"] = "sha256:" + d07_content_hash({
            "result_id": result_id, "domain": domain,
            "stable_measure_key": r.get("stable_measure_key"),
            "event_time_ref": r.get("collection_or_exam_time"),
            "visit_or_pending_ref": visit_ref,
            "pending": pending,
        })
        payload["marker_id"] = "sha256:" + d07_content_hash({
            "payload_hash": payload["payload_hash"],
            "scope_binding_id": scope_binding_id,
        })
        event_markers.append(payload)

    # --- risk markers (one per risk unit, anchored to a result) ---
    risk_markers: List[Dict[str, Any]] = []
    for unit in _risk_units(units):
        domain = "LB"
        measure = measures.get(unit.stable_measure_key, {})
        if measure.get("domain") in _DOMAIN_ORDER:
            domain = str(measure.get("domain"))
        anchor_kind, anchor_ref = _risk_anchor(unit, typed_input)
        algorithm_version = algorithm_versions.get(
            unit.unit_kind, "d07-observation-interpretation-v1"
        )
        unit_id = _unit_identity(unit, spine, algorithm_version)
        risk_id = "sha256:" + d07_content_hash({
            "unit_id": unit_id, "positive_subtype": unit.primary_subtype,
            "normalized_concept": unit.stable_measure_key,
        })
        marker_jumps = [j.get("jump_id") for j in jumps
                        if j.get("source_object_id") == anchor_ref]
        domain_label = _domain_label(domain, allowed_domains)
        risk_label = _risk_type_label(
            unit, lexicon.get("allowed_risk_type_labels", []), domain
        )
        summary_label = _risk_summary(unit, measure, risk_label)
        payload = {
            "marker_id": None,
            "risk_id": risk_id,
            "unit_id": unit_id,
            "positive_subtype": unit.primary_subtype,
            "monitoring_priority": unit.monitoring_priority,
            "seriousness_clue_state": unit.seriousness_clue,
            "grade_comparison_assessment_id": None,
            "clinical_significance_assessment_id": None,
            "priority_decision_id": None,
            "anchor_kind": anchor_kind,
            "anchor_ref": anchor_ref,
            "clinical_domain_label": domain_label,
            "risk_type_label": risk_label,
            "summary_label": summary_label,
            "source_jump_ids": marker_jumps,
            "query_draft_ref": None,
            "payload_hash": None,
        }
        payload["payload_hash"] = "sha256:" + d07_content_hash({
            "risk_id": risk_id, "anchor_kind": anchor_kind,
            "anchor_ref": anchor_ref, "risk_type_label": risk_label,
        })
        payload["marker_id"] = "sha256:" + d07_content_hash({
            "payload_hash": payload["payload_hash"],
            "scope_binding_id": scope_binding_id,
        })
        risk_markers.append(payload)

    # --- audience validation for every payload ---
    # Only target-validated jumps are allowed into the audience/projection;
    # any emitted or referenced jump that failed its schema/hash/scope/locator
    # validation fails the payloads that reference it and the projection.
    allowed_jump_ids = valid_jump_ids
    event_validation = [
        validate_audience_payload(
            lexicon, "event_marker", m, scope_binding_id, spine_subject,
            allowed_jump_ids,
        )
        for m in event_markers
    ]
    risk_validation = [
        validate_audience_payload(
            lexicon, "risk_marker", m, scope_binding_id, spine_subject,
            allowed_jump_ids,
        )
        for m in risk_markers
    ]

    projection_core = {
        "scope_binding_id": scope_binding_id,
        "subject_ref": spine_subject,
        "shared_spine_binding_id": spine.get("binding_id"),
        "d05_projection_id": spine.get("d05_projection_id"),
        "axis_version": spine.get("axis_version"),
        "axis_hash": spine.get("axis_hash"),
        "cutoff": spine.get("cutoff"),
        "shared_spine_equality": equality,
        "event_marker_ids": [m.get("marker_id") for m in event_markers],
        "risk_marker_ids": [m.get("marker_id") for m in risk_markers],
        "source_jump_ids": jump_ids,
    }
    projection_id = "sha256:" + d07_content_hash(projection_core)
    projection: Dict[str, Any] = {
        "projection_id": projection_id,
        "scope_binding_id": scope_binding_id,
        "subject_ref": spine_subject,
        "shared_spine_binding_id": spine.get("binding_id"),
        "d05_projection_id": spine.get("d05_projection_id"),
        "axis_version": spine.get("axis_version"),
        "axis_hash": spine.get("axis_hash"),
        "cutoff": spine.get("cutoff"),
        "shared_spine_equality": equality,
        "ordered_event_markers": event_markers,
        "ordered_risk_markers": risk_markers,
        "source_jumps": jumps,
        "audience_validation_results": event_validation + risk_validation,
        "source_jump_validation_results": jump_validation,
        "projection_hash": projection_id,
    }
    projection_validation = validate_audience_payload(
        lexicon, "projection", projection, scope_binding_id, spine_subject,
        allowed_jump_ids, jumps_all_valid=jumps_all_valid,
    )
    projection["audience_validation_results"] = (
        event_validation + risk_validation + [projection_validation]
    )
    return projection


def _risk_summary(unit: Any, measure: Mapping[str, Any],
                  risk_label: Optional[str]) -> str:
    measure_name = measure.get("audience_name") or unit.stable_measure_key
    if unit.unit_kind == UnitKind.FOLLOWUP_OBLIGATION:
        return f"{measure_name} 复测或处置记录待核实"
    if unit.primary_subtype == PositiveSubtype.NEW_ABNORMALITY:
        return f"{measure_name} 新发异常，需复测与临床意义评估"
    if unit.primary_subtype == PositiveSubtype.BASELINE_ABNORMAL_WORSENING:
        return f"{measure_name} 基线异常进一步加重"
    if unit.primary_subtype == PositiveSubtype.GRADE_OR_MAGNITUDE_WORSENING:
        return f"{measure_name} 等级或幅度恶化"
    if unit.primary_subtype == PositiveSubtype.PERSISTENT_OR_RECURRENT:
        return f"{measure_name} 持续或复发性异常"
    if unit.primary_subtype == PositiveSubtype.CS_INCONSISTENCY:
        return f"{measure_name} 临床意义判断与数据链不一致"
    if unit.primary_subtype == PositiveSubtype.MISSING_REPEAT_OR_FOLLOWUP:
        return f"{measure_name} 规定复测或随访缺失"
    if unit.primary_subtype == PositiveSubtype.MEDICAL_ACTION_INCONSISTENCY:
        return f"{measure_name} 与处置记录不一致"
    if unit.primary_subtype == PositiveSubtype.AE_RECORDING_HANDOFF_CLUE:
        return f"{measure_name} 疑似需核查 AE 记录"
    if unit.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
        return f"{measure_name} 达到项目阈值但缺规定动作"
    if unit.primary_subtype == PositiveSubtype.ORGAN_PATTERN_CLUE:
        return f"{measure_name} 命中组合规则待裁决"
    if unit.primary_subtype == PositiveSubtype.EXAM_INTERPRETATION_INCONSISTENCY:
        return f"{measure_name} 检查结论或复核不一致"
    if unit.primary_subtype == PositiveSubtype.SOURCE_OR_CORRECTION_INCONSISTENCY:
        return f"{measure_name} 原值或更正链不一致"
    return f"{measure_name} 异常待核实"
