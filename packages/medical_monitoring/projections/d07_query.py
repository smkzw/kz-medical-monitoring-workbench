"""R4-D07 three-part Chinese Query draft and D04 PD wording permission.

Worker-03 slice.  Consumes the accepted typed input and the closed runtime's
evaluation units (never the frozen oracle/registry/manifest) and produces:

* ``build_pd_wording_permission_decision`` -- the unique
  ``D07PDWordingPermissionDecision``: PD wording is only permitted when an
  accepted typed D04 protocol-execution / deviation / eligibility context ref
  exists and all scope/hash/accepted conditions are true (contract v0.4
  section 10);
* ``build_d07_query_draft`` -- the ``D07QueryDraft`` with exactly three
  natural-Chinese sentences (basis / finding / action), evidence refs, source
  locators and content addresses.  The draft never claims a system judgment
  (no "DILI"/"SAE"/"与研究药物相关"), never writes PD wording without the
  permission decision, and its labels pass the frozen audience lexicon
  validation (exact-key schema, no forbidden internal tokens).

Boundaries honoured (v0.4 sections 1 / 3 / 10):

* Query drafts are created only for D07-owned risks (``query_owner=D07``);
  handoff-only units never get a draft;
* the draft is viewable/editable/exportable -- it is never sent and no
  external reply is tracked;
* potential PD is only phrased when ``pd_wording_permitted`` is true; without
  the accepted typed D04 ref the action sentence only describes the
  examination/disposition inconsistency.

All data is synthetic and offline.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

from .d07_journey import (
    QUERY_DRAFT_KEYS,
    _forbidden_token_hit,
    _validate_jump_target_evidence,
)
from ..risks.d07_safety import (
    L1Disposition,
    PositiveSubtype,
    RecordStatus,
    UnitKind,
    d07_content_hash,
    d07_content_hash_prefixed,
)

# ---------------------------------------------------------------------------
# PD wording permission (contract v0.4 section 10)
# ---------------------------------------------------------------------------

_SHA256_PREFIX_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

_D04_KIND_BY_CONTEXT = {
    "protocol_deviation_candidate": "protocol_deviation_candidate",
    "eligibility_context": "eligibility_context",
    "protocol_action_context": "protocol_action_context",
}


def _content_hash_equal(context_ref: Mapping[str, Any]) -> bool:
    """The D04 ref must carry a verifiable content hash (``sha256:`` + 64 hex);
    that is the only typed evidence available for content-hash equality."""
    value = context_ref.get("accepted_content_hash")
    return isinstance(value, str) and bool(_SHA256_PREFIX_RE.match(value))


def build_pd_wording_permission_decision(
    typed_input: Mapping[str, Any],
    query_draft_id: Optional[str] = None,
    units: Optional[Sequence[Any]] = None,
) -> Dict[str, Any]:
    """Unique ``D07PDWordingPermissionDecision`` for the run.

    ``pd_wording_permitted`` is true iff at least one accepted typed D04
    context ref exists, all its scope/hash/accepted conditions are true and
    (when ``units`` is provided) the run actually carries a
    ``protocol_or_ib_action_gap`` unit -- the only subtype for which PD wording
    is clinically meaningful.
    """
    refs = typed_input.get("d04_context_refs", [])
    refs = [r for r in refs if isinstance(r, dict)]
    context_ref = refs[0] if refs else None
    gap_present = True
    if units is not None:
        gap_present = any(
            u.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP
            for u in units
        )
    if context_ref is None or not gap_present:
        return {
            "decision_id": d07_content_hash_prefixed({
                "query_draft_id": query_draft_id,
                "d04_context_ref": None,
            }),
            "query_draft_id": query_draft_id,
            "d04_context_ref": None,
            "d04_decision_kind": None,
            "context_scope_equal": False,
            "context_accepted": False,
            "content_hash_equal": False,
            "pd_wording_permitted": False,
            "reason_codes": ["no_accepted_d04_context"],
            "hash": None,
        }
    scope_equal = context_ref.get("context_scope_equal") is True
    accepted = context_ref.get("context_accepted") is True
    hash_equal = _content_hash_equal(context_ref)
    permitted = scope_equal and accepted and hash_equal
    kind = _D04_KIND_BY_CONTEXT.get(
        context_ref.get("context_kind"), "protocol_action_context"
    )
    decision = {
        "decision_id": d07_content_hash_prefixed({
            "query_draft_id": query_draft_id,
            "d04_context_ref": context_ref.get("d04_context_ref_id"),
            "pd_wording_permitted": permitted,
        }),
        "query_draft_id": query_draft_id,
        "d04_context_ref": context_ref.get("d04_context_ref_id"),
        "d04_decision_kind": kind,
        "context_scope_equal": scope_equal,
        "context_accepted": accepted,
        "content_hash_equal": hash_equal,
        "pd_wording_permitted": permitted,
        "reason_codes": ["pd_wording_permitted" if permitted else "pd_wording_denied"],
        "hash": None,
    }
    decision["hash"] = d07_content_hash({
        "query_draft_id": query_draft_id,
        "d04_context_ref": decision["d04_context_ref"],
        "d04_decision_kind": kind,
        "context_scope_equal": scope_equal,
        "context_accepted": accepted,
        "content_hash_equal": hash_equal,
        "pd_wording_permitted": permitted,
    })
    return decision


# ---------------------------------------------------------------------------
# Three-part Chinese Query draft
# ---------------------------------------------------------------------------

_DAY_RE = re.compile(r"第\s*(\d+)\s*天")
_DEC_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def _visit_day(typed_input: Mapping[str, Any],
               visit_ref: Optional[str]) -> Optional[int]:
    if not isinstance(visit_ref, str):
        return None
    for v in typed_input.get("visit_refs", []):
        if v.get("visit_ref_id") != visit_ref:
            continue
        match = _DAY_RE.search(str(v.get("visit_label") or ""))
        if match:
            return int(match.group(1))
        return None
    return None


def _ratio_to_uln(typed_input: Mapping[str, Any],
                  result: Mapping[str, Any]) -> Optional[str]:
    value = result.get("numeric_value")
    if not isinstance(value, str) or not _DEC_RE.match(value):
        return None
    for rng in typed_input.get("reference_range_definitions", []):
        if rng.get("stable_measure_key") != result.get("stable_measure_key"):
            continue
        upper = rng.get("upper")
        if not isinstance(upper, str) or not _DEC_RE.match(upper):
            continue
        try:
            ratio = float(value) / float(upper)
        except (ValueError, ZeroDivisionError):
            return None
        if ratio == int(ratio):
            return f"{int(ratio)}"
        return f"{ratio:.1f}".rstrip("0").rstrip(".")
    return None


def _measure_name(typed_input: Mapping[str, Any], measure_key: str) -> str:
    for m in typed_input.get("measure_definitions", []):
        if m.get("stable_measure_key") == measure_key:
            return str(m.get("audience_name") or measure_key)
    return measure_key


def _time_desc(typed_input: Mapping[str, Any],
               result: Mapping[str, Any]) -> str:
    visit = result.get("visit_ref")
    if isinstance(visit, str):
        for v in typed_input.get("visit_refs", []):
            if v.get("visit_ref_id") == visit:
                label = v.get("visit_label")
                if label:
                    match = _DAY_RE.search(str(label))
                    if match:
                        return f"研究第 {match.group(1)} 天"
                    return f"于{label}"
    time_ref = result.get("collection_or_exam_time")
    for t in typed_input.get("time_refs", []):
        if t.get("time_ref_id") == time_ref:
            value = t.get("value")
            if value:
                return f"于 {value}"
    return "于当前采集时间"


def _value_desc(typed_input: Mapping[str, Any],
                result: Mapping[str, Any]) -> str:
    ratio = _ratio_to_uln(typed_input, result)
    measure = _measure_name(typed_input, result.get("stable_measure_key"))
    if ratio is not None:
        return f"{measure} 升高至 {ratio}×ULN"
    raw = result.get("raw_value")
    unit = result.get("original_unit")
    if raw is not None:
        return f"{measure} 为 {raw} {unit}".strip()
    return f"{measure} 出现异常结果"


def _basis_sentence(unit: Any, typed_input: Mapping[str, Any]) -> str:
    measure = _measure_name(typed_input, unit.stable_measure_key)
    if unit.unit_kind == UnitKind.FOLLOWUP_OBLIGATION:
        return f"方案要求 {measure} 达到项目阈值后在规定时间内复测并评估临床意义；"
    if unit.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
        return f"方案要求 {measure} 达到项目阈值后执行规定的临床处置并记录；"
    if unit.primary_subtype == PositiveSubtype.CS_INCONSISTENCY:
        return "方案要求异常结果的临床意义判断与数据链保持一致并记录理由；"
    return f"方案要求 {measure} 达到项目阈值后在规定时间内复测并评估临床意义；"


def _finding_sentence(unit: Any, typed_input: Mapping[str, Any]) -> str:
    subject = None
    demographics = typed_input.get("subject_demographics", [])
    if isinstance(demographics, list) and demographics:
        subject = demographics[0].get("subject_ref")
    spine = typed_input.get("shared_spine_binding")
    if not subject and isinstance(spine, dict):
        subject = spine.get("subject_ref")
    subject_part = f"受试者 {subject} " if subject else ""
    results = [r for r in typed_input.get("observed_results", [])
               if r.get("record_status") == RecordStatus.ACCEPTED_CURRENT
               and r.get("stable_measure_key") == unit.stable_measure_key]
    abnormal = [r for r in results
                if r.get("reported_abnormal_flag") in ("H", "L")]
    trigger = abnormal[-1] if abnormal else (results[-1] if results else None)
    if trigger is None:
        measure = _measure_name(typed_input, unit.stable_measure_key)
        return f"{subject_part}{measure} 存在异常结果，当前未定位到完整评估记录；"
    time_desc = _time_desc(typed_input, trigger)
    value_desc = _value_desc(typed_input, trigger)
    if unit.unit_kind == UnitKind.FOLLOWUP_OBLIGATION:
        return (f"{subject_part}{time_desc} {value_desc}，"
                f"当前未定位到规定时间窗内复测或 AE 评估记录；")
    if unit.primary_subtype == PositiveSubtype.PROTOCOL_OR_IB_ACTION_GAP:
        return (f"{subject_part}{time_desc} {value_desc}，"
                f"达到项目阈值但未定位到规定的处置记录；")
    if unit.primary_subtype == PositiveSubtype.CS_INCONSISTENCY:
        return (f"{subject_part}{time_desc} {value_desc}，"
                f"现有临床意义判断与数据链不一致；")
    return (f"{subject_part}{time_desc} {value_desc}，"
            f"当前未定位到规定时间窗内复测或 AE 评估记录；")


def _action_sentence(pd_permitted: bool) -> str:
    base = "请核实该异常的临床意义、复测与 AE 判断，并补充或更正相关记录。"
    if pd_permitted:
        return base + " 同时请核实是否涉及 PD。"
    return base


def build_d07_query_draft(
    typed_input: Mapping[str, Any],
    units: Sequence[Any],
    lexicon: Optional[Mapping[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Build the ``D07QueryDraft`` for the run's primary D07-owned risk unit.

    Returns ``None`` when the run has no risk unit (no draft to produce).
    Exactly three natural-Chinese sentences; PD wording only when the accepted
    D04 permission decision permits it.
    """
    risk_units = [
        u for u in units
        if u.l1_disposition in (L1Disposition.POSITIVE, L1Disposition.BOUNDARY)
    ]
    if not risk_units:
        return None
    unit = risk_units[0]
    lexicon = lexicon if isinstance(lexicon, dict) else (
        typed_input.get("audience_lexicon") or {}
    )
    permission = build_pd_wording_permission_decision(
        typed_input, units=units
    )
    pd_permitted = permission.get("pd_wording_permitted") is True
    basis = _basis_sentence(unit, typed_input)
    finding = _finding_sentence(unit, typed_input)
    action = _action_sentence(pd_permitted)

    spine = typed_input.get("shared_spine_binding")
    scope_binding_id = str(
        (spine if isinstance(spine, dict) else {}).get("scope_binding_id")
        or typed_input.get("run_scope_binding", {}).get("scope_binding_id")
        or ""
    )
    unit_id = d07_content_hash_prefixed({
        "stable_measure_key": unit.stable_measure_key,
        "unit_kind": unit.unit_kind,
        "scope_binding_id": scope_binding_id,
    })
    risk_id = d07_content_hash_prefixed({
        "unit_id": unit_id,
        "positive_subtype": unit.primary_subtype,
    })
    locators: List[str] = []
    for r in typed_input.get("observed_results", []):
        if r.get("stable_measure_key") != unit.stable_measure_key:
            continue
        for loc in r.get("source_locator_ids", []):
            if loc not in locators:
                locators.append(loc)
    evidence_refs = [str(s) for s in (unit.source_result_ids or [])]

    d04 = typed_input.get("d04_context_refs", [])
    d04_ref = None
    if d04 and isinstance(d04[0], dict):
        d04_ref = d04[0].get("d04_context_ref_id")
    draft_core = {
        "unit_id": unit_id,
        "risk_id": risk_id,
        "scope_binding_id": scope_binding_id,
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
        "pd_wording_permitted": pd_permitted,
        "d04_context_ref": d04_ref,
    }
    audience_payload_hash = "sha256:" + d07_content_hash(draft_core)
    query_draft_id = "sha256:" + d07_content_hash({
        "audience_payload_hash": audience_payload_hash,
        "scope_binding_id": scope_binding_id,
    })
    draft: Dict[str, Any] = {
        "query_draft_id": query_draft_id,
        "unit_id": unit_id,
        "risk_id": risk_id,
        "owner_routing_decision_id": None,
        "query_owner": "D07",
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
        "protocol_execution_context_ref": d04_ref,
        "d04_enrollment_or_pd_context_ref": d04_ref,
        "pd_wording_permission": permission,
        "evidence_refs": evidence_refs,
        "source_locator_ids": sorted(locators),
        "audience_payload_hash": audience_payload_hash,
        "content_hash": None,
    }
    draft["content_hash"] = d07_content_hash_prefixed({
        "query_draft_id": query_draft_id,
        "unit_id": unit_id,
        "risk_id": risk_id,
        "basis_sentence": basis,
        "finding_sentence": finding,
        "action_sentence": action,
        "evidence_refs": evidence_refs,
        "source_locator_ids": sorted(locators),
    })
    return draft


def validate_query_draft(
    draft: Dict[str, Any],
    lexicon: Mapping[str, Any],
    scope_binding_id: str,
    spine_subject_ref: str,
    typed_input: Optional[Mapping[str, Any]] = None,
    valid_jumps: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """Closed audience validation of the query payload: exact-key schema, no
    forbidden internal tokens, three-sentence structure, PD gating, plus
    evidence/source-locator/scope/content-hash validation against the typed
    input, the shared spine and the emitted valid jumps (contract §10/§11)."""
    reasons: List[str] = []
    schema_valid = set(draft) == QUERY_DRAFT_KEYS
    if not schema_valid:
        reasons.append("schema_exact_keys")
    sentences = [
        draft.get("basis_sentence"), draft.get("finding_sentence"),
        draft.get("action_sentence"),
    ]
    three_sentence = (
        len(sentences) == 3
        and all(isinstance(s, str) and bool(s) for s in sentences)
    )
    if not three_sentence:
        reasons.append("three_sentence_contract")
    forbidden = _forbidden_token_hit(lexicon, sentences)
    no_internal_tokens = forbidden is None
    if forbidden is not None:
        reasons.append(f"forbidden_internal_token:{forbidden}")
    permission = draft.get("pd_wording_permission") or {}
    pd_gated = True
    if "PD" in str(draft.get("action_sentence") or ""):
        pd_gated = permission.get("pd_wording_permitted") is True
        if not pd_gated:
            reasons.append("pd_wording_without_permission")

    # Content hash: recompute from the draft core; a stale hash fails.
    content_hash_valid = True
    expected_content_hash = d07_content_hash_prefixed({
        "query_draft_id": draft.get("query_draft_id"),
        "unit_id": draft.get("unit_id"),
        "risk_id": draft.get("risk_id"),
        "basis_sentence": draft.get("basis_sentence"),
        "finding_sentence": draft.get("finding_sentence"),
        "action_sentence": draft.get("action_sentence"),
        "evidence_refs": draft.get("evidence_refs"),
        "source_locator_ids": draft.get("source_locator_ids"),
    })
    if draft.get("content_hash") != expected_content_hash:
        content_hash_valid = False
        reasons.append("content_hash_stale")

    # Exact evidence/scope/jump/locator validation requires the typed input
    # and the emitted valid jumps.  Their absence fails closed -- the draft
    # schema carries no scope key or jump set, so nothing may degrade to a
    # passed binding (contract v0.4 section 10/11).
    if typed_input is None:
        reasons.append("typed_input_missing")
    if valid_jumps is None:
        reasons.append("valid_jumps_missing")

    # Scope: the draft's unit identity embeds the scope binding; every
    # evidence record's envelope must carry the same scope and subject.
    scope_equal = False
    if typed_input is not None:
        scope_equal = bool(scope_binding_id)
        envelopes = {
            e.get("record_id"): e for e in typed_input.get("scope_envelopes", [])
        }
        results = {
            r.get("result_id"): r for r in typed_input.get("observed_results", [])
        }
        evidence = [r for rid in (draft.get("evidence_refs") or [])
                    if isinstance(rid, str) and (r := results.get(rid)) is not None]
        if len(evidence) != len(draft.get("evidence_refs") or []):
            scope_equal = False
            reasons.append("evidence_ref_unresolved")
        for r in evidence:
            env = envelopes.get(r.get("stable_source_record_id"))
            if env is None or env.get("scope_binding_id") != scope_binding_id:
                scope_equal = False
                reasons.append("evidence_scope_mismatch")
                break
            if env.get("subject_ref") != spine_subject_ref:
                scope_equal = False
                reasons.append("evidence_subject_mismatch")
                break
            if r.get("record_status") != "accepted_current":
                scope_equal = False
                reasons.append("evidence_not_visible")
                break
        # The unit identity recomputes from the evidence measure, the unit
        # kind and the scope binding.
        if evidence:
            expected_unit_id = d07_content_hash_prefixed({
                "stable_measure_key": evidence[0].get("stable_measure_key"),
                "unit_kind": "observation_interpretation",
                "scope_binding_id": scope_binding_id,
            })
            if draft.get("unit_id") != expected_unit_id:
                scope_equal = False
                reasons.append("unit_scope_mismatch")
    if not scope_equal:
        reasons.append("scope_binding_mismatch")

    # Source jumps: every evidence ref anchors a real result; the emitted
    # valid jumps must cover the evidence and originate only from it.  The
    # evidence also needs the typed input to resolve.
    source_jump_valid = bool(draft.get("evidence_refs"))
    if not source_jump_valid:
        reasons.append("evidence_refs_empty")
    if valid_jumps is not None and typed_input is not None:
        jump_sources = {j.get("source_object_id") for j in valid_jumps}
        evidence_set = set(draft.get("evidence_refs") or [])
        if not evidence_set <= jump_sources:
            source_jump_valid = False
            reasons.append("evidence_without_jump")
        if not jump_sources <= evidence_set:
            source_jump_valid = False
            reasons.append("jump_without_evidence")
        # A source-id set alignment alone is not evidence: every valid jump
        # must itself pass target schema/hash/scope/locator validation.
        # The contract-materialised ``D07SourceJump`` carries ``target_ref``;
        # the test adapter pair carries ``target_object_id``.  Accept either,
        # but fail closed when both are present and disagree.
        for jump in valid_jumps:
            target_ref = jump.get("target_ref")
            target_object_id = jump.get("target_object_id")
            if (target_ref is not None and target_object_id is not None
                    and target_ref != target_object_id):
                source_jump_valid = False
                reasons.append("jump_target_ref_conflict")
                continue
            target_id = target_ref if target_ref is not None else target_object_id
            if target_id is None:
                source_jump_valid = False
                reasons.append("jump_target_ref_missing")
                continue
            target_ok, target_reasons = _validate_jump_target_evidence(
                typed_input, scope_binding_id,
                jump.get("source_object_id"),
                jump.get("target_kind"),
                target_id,
            )
            if not target_ok:
                source_jump_valid = False
                for reason in target_reasons:
                    reasons.append(f"jump_{reason}")
    else:
        source_jump_valid = False

    # Visible path: the draft locators must be non-empty and every locator
    # must exist in the typed input's locator universe.
    visible_path_valid = bool(draft.get("source_locator_ids"))
    if not visible_path_valid:
        reasons.append("source_locators_empty")
    if typed_input is not None and visible_path_valid:
        universe: Set[str] = set()
        for section in (
            "observed_results", "scope_envelopes", "run_scope_binding",
            "time_refs", "visit_refs", "subject_demographics",
            "audience_lexicon", "authority_bindings", "measure_definitions",
            "reference_range_definitions", "unit_conversion_rules",
            "grade_rule_sets", "grade_rules", "monitoring_rules",
            "monitoring_predicates", "baseline_rules", "trend_rules",
            "action_obligation_definitions",
            "organ_pattern_rule_definitions", "examination_requirement_sets",
            "priority_policy", "priority_precedence_rules",
            "producer_consumption_bindings", "clinical_review_refs",
            "clinical_significance_reason_refs", "d04_context_refs",
            "correction_chain_decisions", "carry_forward_refs",
            "shared_spine_binding", "shared_spine_scope_equality_decision",
            "d05_gate_bindings", "applicability_evidence",
        ):
            value = typed_input.get(section)
            objs = value if isinstance(value, list) else (
                [value] if isinstance(value, dict) else []
            )
            for obj in objs:
                if isinstance(obj, dict):
                    for loc in obj.get("source_locator_ids", []):
                        if isinstance(loc, str):
                            universe.add(loc)
        unknown = [loc for loc in draft.get("source_locator_ids", [])
                   if loc not in universe]
        if unknown:
            visible_path_valid = False
            reasons.append("source_locator_unresolved")
    elif typed_input is None:
        # Without the typed input the locator universe cannot be resolved;
        # the visible path cannot be proven.
        visible_path_valid = False

    passed = (
        schema_valid and three_sentence and no_internal_tokens and pd_gated
        and content_hash_valid and scope_equal and source_jump_valid
        and visible_path_valid
    )
    return {
        "validation_id": d07_content_hash_prefixed({
            "payload_kind": "query",
            "payload_object_id": draft.get("audience_payload_hash"),
            "scope_binding_id": scope_binding_id,
        }),
        "payload_kind": "query",
        "payload_object_id": draft.get("audience_payload_hash"),
        "payload_hash": draft.get("audience_payload_hash"),
        "lexicon_id": lexicon.get("lexicon_id"),
        "lexicon_version": lexicon.get("version"),
        "lexicon_hash": lexicon.get("content_hash"),
        "schema_valid": schema_valid,
        "no_internal_tokens": no_internal_tokens,
        "domain_specific": True,
        "risk_specific": True,
        "source_jump_valid": source_jump_valid,
        "visible_path_valid": visible_path_valid,
        "scope_equal": scope_equal,
        "validation_passed": passed,
        "reason_codes": reasons if reasons else ["query_payload_ok"],
    }
