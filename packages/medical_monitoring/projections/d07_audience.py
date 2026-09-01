"""Closed audience schemas and validation for D07 journey/query projections."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from ..risks.d07_safety import d07_content_hash


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


def _forbidden_token_hit(
    lexicon: Mapping[str, Any], labels: Sequence[Optional[str]]
) -> Optional[str]:
    forbidden = [str(token) for token in lexicon.get("forbidden_internal_tokens", [])]
    for label in labels:
        if not isinstance(label, str):
            continue
        for token in forbidden:
            if token and token in label:
                return token
    return None


def _schema_valid(payload_kind: str, payload: Mapping[str, Any]) -> bool:
    schemas = {
        "query": QUERY_DRAFT_KEYS,
        "event_marker": EVENT_MARKER_KEYS,
        "risk_marker": RISK_MARKER_KEYS,
        "projection": PROJECTION_KEYS,
    }
    schema = schemas.get(payload_kind)
    return schema is not None and set(payload) == schema


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
    """Validate one audience payload against its closed schema and lexicon."""

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
        labels += [str(payload.get("scope_binding_id")), str(payload.get("subject_ref"))]
    forbidden = _forbidden_token_hit(lexicon, labels)
    no_internal_tokens = forbidden is None
    if forbidden is not None:
        reasons.append("forbidden_internal_token:%s" % forbidden)

    allowed_domains = [str(value) for value in lexicon.get("allowed_domain_labels", [])]
    allowed_risks = [str(value) for value in lexicon.get("allowed_risk_type_labels", [])]
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
    source_jump_valid = isinstance(jump_ids, list) and all(
        jump_id in set(allowed_jump_ids) for jump_id in jump_ids
    )
    if not source_jump_valid:
        reasons.append("source_jump_unresolved")
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

    scope_equal = payload_kind in ("query", "event_marker", "risk_marker", "projection")
    if payload_kind == "projection":
        scope_equal = (
            payload.get("scope_binding_id") == scope_binding_id
            and payload.get("subject_ref") == spine_subject_ref
        )
    if not scope_equal:
        reasons.append("scope_mismatch")

    passed = (
        schema_valid and no_internal_tokens and domain_specific
        and risk_specific and source_jump_valid and visible_path_valid and scope_equal
    )
    return {
        "validation_id": "sha256:" + d07_content_hash({
            "payload_kind": payload_kind,
            "payload_object_id": payload.get("payload_hash") or payload.get("projection_id"),
            "scope_binding_id": scope_binding_id,
        }),
        "payload_kind": payload_kind,
        "payload_object_id": payload.get("payload_hash") or payload.get("projection_id"),
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
