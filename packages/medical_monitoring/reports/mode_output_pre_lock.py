"""Pre-lock report payload construction and validation."""

from __future__ import annotations

import copy
from typing import Any, Mapping, Optional, Sequence, Tuple

from .mode_output_core import *
from .mode_output_core import (
    _copy_mapping,
    _require_non_empty_str,
    _frozen_mode_contract_rows,
    _row_by_mode,
    _reshape_mode_contract,
    _dedupe,
    _append,
    _non_empty_str,
    _truthy_flag,
    _validate_common_binding,
    _validate_silent_conversion,
    _validate_execution_basis,
    _validate_entry_conditions,
    _validate_cutoff_and_revision,
    _validate_carry_forward,
    _eligible_kinds_for_mode,
    _require_ref_mapping,
    _bind_refs_to_run,
    _check_eligibility,
    _zh_clause,
    _finding_scope,
    _finding_evidence,
    _assert_query_draft_boundary,
    _query_draft_id,
    _build_one_query_draft,
    _default_payload_for_kind,
    _numeric_near,
    _validate_numeric_payload,
    _validate_change_entries,
)

def _shared_payload_identity(
    run: Mapping[str, Any], authority_refs: Mapping[str, Any]
) -> dict:
    auth = _require_ref_mapping(authority_refs, "authority_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    digest = auth.get("digest") or auth.get("authority_digest")
    return {
        "authority_digest": digest,
        "project_id": run.get("project_id"),
        "run_id": run.get("run_id"),
        "data_cutoff": run.get("data_cutoff"),
        "source_revision_id": run.get("source_revision_id"),
    }


def _require_pre_lock_run(run_binding: Mapping[str, Any]) -> dict:
    if not isinstance(run_binding, Mapping):
        raise ModeOutputError(IDENTITY_MISMATCH, "run_binding must be a mapping")
    run = _copy_mapping(run_binding)
    for field in (
        "project_id",
        "run_id",
        "mode",
        "data_cutoff",
        "source_revision_id",
    ):
        _require_non_empty_str(run.get(field), field, IDENTITY_MISMATCH)
    if run.get("mode") != "pre_lock":
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "pre_lock payloads require run.mode=pre_lock",
        )
    if run.get("execution_basis") != "full":
        raise ModeOutputError(
            MODE_ENTRY_BLOCKED,
            "pre_lock payloads require execution_basis=full",
        )
    return run


def _normalize_population_scope(raw: Any) -> dict:
    if raw is None:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "population_scope must be explicitly supplied"
        )
    if isinstance(raw, str):
        if raw.strip() == "":
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE, "population_scope must be non-empty"
            )
        return {"scope_kind": "project", "population_id": raw.strip(), "label": raw.strip()}
    if not isinstance(raw, Mapping) or not raw:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "population_scope must be a non-empty mapping or string"
        )
    scope = _copy_mapping(raw)
    if not _non_empty_str(scope.get("scope_kind")):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "population_scope.scope_kind required")
    if not _non_empty_str(scope.get("population_id")) and not _non_empty_str(
        scope.get("label")
    ):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "population_scope needs population_id or label"
        )
    return scope


def build_full_risk_payload(
    run_binding: Mapping[str, Any],
    *,
    risks: Optional[Sequence[Any]] = None,
    numeric: Optional[Mapping[str, Any]] = None,
    population_scope: Any,
    authority_refs: Mapping[str, Any],
) -> dict:
    """Build pre_lock ``full_risk`` payload with numeric/metric reconciliation.

    Risks may be empty. Quantitative risks must reconcile ``metric_id`` → numeric
    raw via the slice-04 numeric policy. Binds population_scope, cutoff,
    source_revision_id, and authority digest. No disposition / user confirmation.
    """
    run = _require_pre_lock_run(run_binding)
    auth = _require_ref_mapping(authority_refs, "authority_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    if risks is None:
        risks = []
    if not isinstance(risks, Sequence) or isinstance(risks, (str, bytes)):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "risks must be a sequence")
    if numeric is not None and not isinstance(numeric, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "numeric must be a mapping")
    payload = {
        "output_kind": "full_risk",
        "risks": copy.deepcopy(list(risks)),
        "numeric": copy.deepcopy(dict(numeric or {})),
        "population_scope": _normalize_population_scope(population_scope),
        "is_user_confirmed": False,
        "disposition_closed": False,
        "medical_conclusion_final": False,
        **_shared_payload_identity(run, auth),
    }
    codes: list[str] = []
    _validate_full_risk_payload(payload, run, authority_refs=auth, codes=codes)
    if codes:
        raise ModeOutputError(codes[0], f"full_risk invalid: {tuple(codes)}")
    return payload


def _impact_id(item: Mapping[str, Any]) -> str:
    fields = (
        "impact_kind",
        "from_source_revision_id",
        "to_source_revision_id",
        "affected_scope",
        "evidence_refs",
        "source_change_kind",
        "summary",
    )
    return "imp-" + sha256_hex(
        canonical_bytes({field: copy.deepcopy(item.get(field)) for field in fields})
    )[:32]


def _normalize_impact_item(
    raw: Mapping[str, Any],
    *,
    from_rev: str,
    to_rev: str,
    project_id: str,
) -> dict:
    if not isinstance(raw, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "impact item must be a mapping")
    impact_kind = raw.get("impact_kind")
    if impact_kind not in IMPACT_KINDS:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "impact_kind must be clinical_data|knowledge_rule_mapping_model|user_decision",
        )
    source_change = _require_non_empty_str(
        raw.get("source_change_kind"), "source_change_kind", OUTPUT_NOT_ELIGIBLE
    )
    source_matches = {
        "clinical_data": source_change == "clinical_data",
        "knowledge_rule_mapping_model": source_change in KNOWLEDGE_CHANGE_SURFACES,
        "user_decision": source_change == "user_decision",
    }[impact_kind]
    if not source_matches:
        raise ModeOutputError(
            AUTHORITY_MISMATCH,
            "source_change_kind does not match impact_kind",
        )
    affected = raw.get("affected_scope")
    if not isinstance(affected, Mapping) or not affected:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "affected_scope must be a non-empty mapping"
        )
    scope = _copy_mapping(affected)
    scope_kind = scope.get("scope_kind")
    if scope_kind == "project":
        if scope.get("project_id") != project_id:
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "project impact requires project_id")
    elif scope_kind == "site":
        if not _non_empty_str(scope.get("site_id")) or scope.get("subject_id") not in (None, ""):
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "site impact requires site_id only")
    elif scope_kind == "subject":
        if not _non_empty_str(scope.get("site_id")) or not _non_empty_str(
            scope.get("subject_id")
        ):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE, "subject impact requires site_id and subject_id"
            )
    elif scope_kind == "population":
        if not _non_empty_str(scope.get("population_id")):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE, "population impact requires population_id"
            )
    else:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "affected_scope.scope_kind must be project|site|subject|population",
        )
    if "project_id" in scope and scope.get("project_id") != project_id:
        raise ModeOutputError(IDENTITY_MISMATCH, "impact project_id drifts from run")
    evidence = raw.get("evidence_refs")
    if not isinstance(evidence, list) or not evidence:
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "impact evidence_refs must be non-empty")
    normalized_evidence: list = []
    for item in evidence:
        if isinstance(item, Mapping):
            if not _non_empty_str(item.get("evidence_id")) and not _non_empty_str(
                item.get("ref")
            ):
                raise ModeOutputError(
                    OUTPUT_NOT_ELIGIBLE, "impact evidence mapping lacks evidence_id/ref"
                )
            normalized_evidence.append(_copy_mapping(item))
        elif _non_empty_str(item):
            normalized_evidence.append(str(item))
        else:
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "impact evidence_refs invalid")

    item = {
        "impact_kind": impact_kind,
        "from_source_revision_id": from_rev,
        "to_source_revision_id": to_rev,
        "affected_scope": scope,
        "evidence_refs": normalized_evidence,
    }
    item["source_change_kind"] = source_change
    summary = raw.get("summary")
    if _non_empty_str(summary):
        item["summary"] = str(summary).strip()
    supplied_id = raw.get("impact_id")
    computed = _impact_id(item)
    if supplied_id is not None and supplied_id != computed:
        raise ModeOutputError(
            IDENTITY_MISMATCH, "impact_id does not match canonical content"
        )
    item["impact_id"] = computed
    return item


def build_revision_impact_payload(
    run_binding: Mapping[str, Any],
    *,
    from_source_revision_id: str,
    revision_reason: str,
    impacts: Optional[Sequence[Mapping[str, Any]]] = None,
    authority_refs: Mapping[str, Any],
) -> dict:
    """Build pre_lock ``revision_impact`` bound to current Run source revision."""
    run = _require_pre_lock_run(run_binding)
    auth = _require_ref_mapping(authority_refs, "authority_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    from_rev = _require_non_empty_str(
        from_source_revision_id, "from_source_revision_id", REVISION_MISMATCH
    )
    to_rev = str(run["source_revision_id"])
    reason = _require_non_empty_str(
        revision_reason, "revision_reason", OUTPUT_NOT_ELIGIBLE
    )
    if from_rev == to_rev:
        raise ModeOutputError(
            REVISION_MISMATCH, "from_source_revision_id must differ from current Run"
        )
    if impacts is None:
        impacts = []
    if not isinstance(impacts, Sequence) or isinstance(impacts, (str, bytes)):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "impacts must be a sequence")
    items = [
        _normalize_impact_item(
            item,
            from_rev=from_rev,
            to_rev=to_rev,
            project_id=str(run["project_id"]),
        )
        for item in impacts
    ]
    if len({item["impact_id"] for item in items}) != len(items):
        raise ModeOutputError(IDENTITY_MISMATCH, "duplicate impact_id in revision_impact")
    items.sort(key=lambda row: row["impact_id"])
    payload = {
        "output_kind": "revision_impact",
        "from_source_revision_id": from_rev,
        "to_source_revision_id": to_rev,
        "revision_reason": reason,
        "impacts": items,
        "impact_count": len(items),
        **_shared_payload_identity(run, auth),
    }
    codes: list[str] = []
    _validate_revision_impact_payload(payload, run, auth, codes)
    if codes:
        raise ModeOutputError(codes[0], f"revision_impact invalid: {tuple(codes)}")
    return payload


def _check_id(item: Mapping[str, Any]) -> str:
    fields = (
        "level",
        "check_kind",
        "status",
        "project_id",
        "site_id",
        "subject_id",
        "evidence_refs",
        "locator",
    )
    return "chk-" + sha256_hex(
        canonical_bytes({field: copy.deepcopy(item.get(field)) for field in fields})
    )[:32]


def recompute_check_coverage_summary(check_items: Sequence[Mapping[str, Any]]) -> dict:
    """Deterministic coverage_summary from check_items (ready/blocked/not_applicable)."""
    summary: dict[str, Any] = {
        "total": 0,
        "ready": 0,
        "blocked": 0,
        "not_applicable": 0,
        "by_level": {
            level: {"total": 0, "ready": 0, "blocked": 0, "not_applicable": 0}
            for level in ("project", "site", "subject")
        },
    }
    for item in check_items:
        if not isinstance(item, Mapping):
            continue
        status = item.get("status")
        level = item.get("level")
        if status not in CHECK_STATUSES or level not in CHECK_LEVELS:
            continue
        summary["total"] += 1
        summary[status] += 1
        bucket = summary["by_level"][level]
        bucket["total"] += 1
        bucket[status] += 1
    return summary


def _normalize_check_item(raw: Mapping[str, Any], run: Mapping[str, Any]) -> dict:
    if not isinstance(raw, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "check_item must be a mapping")
    level = raw.get("level")
    if level not in CHECK_LEVELS:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "check level must be project|site|subject"
        )
    status = raw.get("status")
    if status in CHECK_FORBIDDEN_STATUSES:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "check status cannot be completed/passed/user_confirmed in this slice",
        )
    if status not in CHECK_STATUSES:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "check status must be ready|blocked|not_applicable"
        )
    check_kind = _require_non_empty_str(
        raw.get("check_kind"), "check_kind", OUTPUT_NOT_ELIGIBLE
    )
    evidence = raw.get("evidence_refs")
    locator = raw.get("locator")
    # No coverage / evidence conflict must be blocked — cannot forge ready.
    for flag in ("evidence_conflict", "coverage_missing"):
        if flag in raw and not isinstance(raw.get(flag), bool):
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, f"{flag} must be boolean")
    evidence_conflict = raw.get("evidence_conflict", False)
    coverage_missing = raw.get("coverage_missing", False)
    if (evidence_conflict or coverage_missing) and status != "blocked":
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "coverage/evidence conflict requires status=blocked",
        )
    if not isinstance(evidence, list) or not evidence:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "check_items require evidence_refs"
        )
    if not isinstance(locator, Mapping) or not locator:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "check_items require locator"
        )
    if not any(
        _non_empty_str(locator.get(key))
        for key in ("path", "record_id", "field", "uri")
    ):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "check locator must be independently checkable"
        )
    normalized_evidence: list = []
    if evidence is None:
        evidence = []
    if not isinstance(evidence, list):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "evidence_refs must be a list")
    for item in evidence:
        if isinstance(item, Mapping):
            if not _non_empty_str(item.get("evidence_id")) and not _non_empty_str(
                item.get("ref")
            ):
                raise ModeOutputError(
                    OUTPUT_NOT_ELIGIBLE, "check evidence mapping lacks evidence_id/ref"
                )
            normalized_evidence.append(_copy_mapping(item))
        elif _non_empty_str(item):
            normalized_evidence.append(str(item))
        else:
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "check evidence_refs invalid")
    loc = {}
    if locator is not None:
        if not isinstance(locator, Mapping):
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "locator must be a mapping")
        loc = _copy_mapping(locator)

    project_id = raw.get("project_id", run.get("project_id"))
    if project_id != run.get("project_id"):
        raise ModeOutputError(IDENTITY_MISMATCH, "check project_id drifts from run")
    site_id = raw.get("site_id")
    subject_id = raw.get("subject_id")
    if level == "project":
        if site_id not in (None, "") or subject_id not in (None, ""):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE, "project-level check must not claim site/subject"
            )
        site_id = ""
        subject_id = ""
    elif level == "site":
        if not _non_empty_str(site_id):
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "site-level check requires site_id")
        if subject_id not in (None, ""):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE, "site-level check must not claim subject_id"
            )
        subject_id = ""
    else:  # subject
        if not _non_empty_str(site_id) or not _non_empty_str(subject_id):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE, "subject-level check requires site_id and subject_id"
            )

    item = {
        "level": level,
        "check_kind": check_kind,
        "status": status,
        "project_id": project_id,
        "site_id": site_id or "",
        "subject_id": subject_id or "",
        "evidence_refs": normalized_evidence,
        "locator": loc,
        "evidence_conflict": bool(evidence_conflict),
        "coverage_missing": bool(coverage_missing),
    }
    supplied = raw.get("check_id")
    computed = _check_id(item)
    if supplied is not None and supplied != computed:
        raise ModeOutputError(
            IDENTITY_MISMATCH, "check_id does not match canonical content"
        )
    item["check_id"] = computed
    return item


def build_check_package_payload(
    run_binding: Mapping[str, Any],
    *,
    check_items: Optional[Sequence[Mapping[str, Any]]] = None,
    authority_refs: Mapping[str, Any],
) -> dict:
    """Build pre_lock ``check_package`` with recomputable coverage_summary."""
    run = _require_pre_lock_run(run_binding)
    auth = _require_ref_mapping(authority_refs, "authority_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    if check_items is None:
        check_items = []
    if not isinstance(check_items, Sequence) or isinstance(check_items, (str, bytes)):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "check_items must be a sequence")
    items = [_normalize_check_item(item, run) for item in check_items]
    if len({item["check_id"] for item in items}) != len(items):
        raise ModeOutputError(IDENTITY_MISMATCH, "duplicate check_id in check_package")
    levels_present = {item["level"] for item in items}
    missing = CHECK_LEVELS - levels_present
    if missing:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            f"check_package must include project/site/subject levels; missing={sorted(missing)}",
        )
    items.sort(key=lambda row: (row["level"], row["check_id"]))
    summary = recompute_check_coverage_summary(items)
    payload = {
        "output_kind": "check_package",
        "check_items": items,
        "coverage_summary": summary,
        **_shared_payload_identity(run, auth),
    }
    codes: list[str] = []
    _validate_check_package_payload(payload, run, auth, codes)
    if codes:
        raise ModeOutputError(codes[0], f"check_package invalid: {tuple(codes)}")
    return payload


def _normalize_revision_entry(
    raw: Mapping[str, Any], run: Mapping[str, Any]
) -> dict:
    if not isinstance(raw, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "revision entry must be a mapping")
    revision_kind = raw.get("revision_kind")
    if revision_kind not in REVISION_KINDS:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "revision_kind must be new|updated|unchanged|withdrawn_draft",
        )
    previous = raw.get("previous_query_draft_id")
    if previous is None or previous == "":
        previous_id = None
    elif _non_empty_str(previous):
        previous_id = str(previous)
    else:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "previous_query_draft_id must be string or empty"
        )
    if revision_kind == "new" and previous_id is not None:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "revision_kind=new requires empty previous_query_draft_id"
        )
    if revision_kind in {"updated", "unchanged", "withdrawn_draft"} and previous_id is None:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            f"revision_kind={revision_kind} requires previous_query_draft_id",
        )

    finding = raw.get("finding")
    draft_raw = raw.get("query_draft")
    if isinstance(draft_raw, Mapping):
        draft = _normalize_supplied_query_draft(draft_raw, run)
    elif isinstance(finding, Mapping):
        draft = _build_one_query_draft(run, finding)
    elif revision_kind == "withdrawn_draft":
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "withdrawn_draft requires a complete query_draft or finding",
        )
    else:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "revision entry requires finding or query_draft",
        )

    if revision_kind in {"updated", "unchanged"} and previous_id == draft.get(
        "query_draft_id"
    ):
        raise ModeOutputError(
            IDENTITY_MISMATCH,
            f"revision_kind={revision_kind} requires changed query_draft identity",
        )

    return {
        "query_draft_id": draft["query_draft_id"],
        "previous_query_draft_id": previous_id,
        "revision_kind": revision_kind,
        "query_draft": draft,
    }


def _normalize_supplied_query_draft(
    raw: Mapping[str, Any], run: Mapping[str, Any]
) -> dict:
    draft = _copy_mapping(raw)
    for field in QUERY_DRAFT_REQUIRED:
        if field not in draft:
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, f"query draft missing {field}")
    _assert_query_draft_boundary(draft)
    if not all(isinstance(draft.get(key), str) for key in ("basis", "finding", "action")):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "query clauses must be strings")
    if draft.get("display_text") != "".join(
        (draft["basis"], draft["finding"], draft["action"])
    ):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "display_text must equal basis+finding+action"
        )
    subject_id, site_id, scope_kind = _finding_scope(draft)
    evidence_refs, locator = _finding_evidence(draft)
    if draft.get("project_id") != run.get("project_id") or draft.get(
        "run_id"
    ) != run.get("run_id"):
        raise ModeOutputError(IDENTITY_MISMATCH, "query draft identity drifts")
    if draft.get("data_cutoff") != run.get("data_cutoff"):
        raise ModeOutputError(CUTOFF_MISMATCH, "query draft cutoff drifts")
    if draft.get("source_revision_id") != run.get("source_revision_id"):
        raise ModeOutputError(REVISION_MISMATCH, "query draft revision drifts")
    if draft.get("producer_kind") != PRODUCER_SYSTEM:
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "query draft producer must be system")

    normalized = {
        key: copy.deepcopy(draft[key])
        for key in QUERY_DRAFT_REQUIRED
    }
    normalized.update(
        {
            "subject_id": subject_id,
            "site_id": site_id,
            "scope_kind": scope_kind,
            "evidence_refs": evidence_refs,
            "locator": locator,
            "is_pd_recorded": False,
            "is_pd_closed": False,
            "producer_kind": PRODUCER_SYSTEM,
        }
    )
    for key in ("finding_kind", "pd_wording_state"):
        if _non_empty_str(draft.get(key)):
            normalized[key] = str(draft[key])
    if draft.get("query_draft_id") != _query_draft_id(normalized):
        raise ModeOutputError(
            IDENTITY_MISMATCH, "query_draft_id does not match canonical content"
        )
    return normalized


def build_query_revision_package_payload(
    run_binding: Mapping[str, Any],
    *,
    revision_entries: Optional[Sequence[Mapping[str, Any]]] = None,
    authority_refs: Mapping[str, Any],
) -> dict:
    """Build pre_lock ``query_revision_package`` (draft-only; never sent/closed)."""
    run = _require_pre_lock_run(run_binding)
    auth = _require_ref_mapping(authority_refs, "authority_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    if revision_entries is None:
        revision_entries = []
    if not isinstance(revision_entries, Sequence) or isinstance(
        revision_entries, (str, bytes)
    ):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "revision_entries must be a sequence")
    entries = [_normalize_revision_entry(item, run) for item in revision_entries]
    if len({entry["query_draft_id"] for entry in entries}) != len(entries):
        raise ModeOutputError(
            IDENTITY_MISMATCH, "duplicate query_draft_id in query_revision_package"
        )
    entries.sort(key=lambda row: (row["revision_kind"], row["query_draft_id"]))
    payload = {
        "output_kind": "query_revision_package",
        "revision_entries": entries,
        "entry_count": len(entries),
        "is_sent": False,
        "is_closed": False,
        "is_user_confirmed": False,
        "pd_registration_allowed": False,
        "external_dispatch_allowed": False,
        **_shared_payload_identity(run, auth),
    }
    codes: list[str] = []
    _validate_query_revision_package_payload(payload, run, auth, codes)
    if codes:
        raise ModeOutputError(
            codes[0], f"query_revision_package invalid: {tuple(codes)}"
        )
    return payload


def _default_pre_lock_payload_for_kind(
    output_kind: str,
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    output_spec: Mapping[str, Any],
) -> dict:
    if output_kind == "full_risk":
        return build_full_risk_payload(
            run,
            risks=output_spec.get("risks"),
            numeric=output_spec.get("numeric"),
            population_scope=output_spec.get("population_scope"),
            authority_refs=authority_refs,
        )
    if output_kind == "revision_impact":
        from_rev = output_spec.get("from_source_revision_id")
        reason = output_spec.get("revision_reason")
        if not _non_empty_str(from_rev) or not _non_empty_str(reason):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                "revision_impact requires from_source_revision_id and revision_reason",
            )
        return build_revision_impact_payload(
            run,
            from_source_revision_id=str(from_rev),
            revision_reason=str(reason),
            impacts=output_spec.get("impacts") or [],
            authority_refs=authority_refs,
        )
    if output_kind == "check_package":
        return build_check_package_payload(
            run,
            check_items=output_spec.get("check_items") or [],
            authority_refs=authority_refs,
        )
    if output_kind == "query_revision_package":
        return build_query_revision_package_payload(
            run,
            revision_entries=output_spec.get("revision_entries") or [],
            authority_refs=authority_refs,
        )
    raise ModeOutputError(
        OUTPUT_NOT_ELIGIBLE, f"unknown pre_lock output_kind={output_kind!r}"
    )


def _validate_full_risk_payload(
    payload: Mapping[str, Any],
    run: Mapping[str, Any],
    *,
    authority_refs: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not isinstance(payload, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    if payload.get("output_kind") != "full_risk":
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    _validate_pre_lock_payload_binding(
        payload, run, authority_refs, expected_kind="full_risk", codes=codes
    )
    scope = payload.get("population_scope")
    if not isinstance(scope, Mapping) or not scope:
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    elif not _non_empty_str(scope.get("scope_kind")):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    elif not (
        _non_empty_str(scope.get("population_id")) or _non_empty_str(scope.get("label"))
    ):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    for flag in FULL_RISK_FORBIDDEN_TRUE_FLAGS:
        if flag in payload and payload.get(flag) is not False:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    for flag in ("is_user_confirmed", "disposition_closed", "medical_conclusion_final"):
        if flag not in payload or payload.get(flag) is not False:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    risks = payload.get("risks")
    if isinstance(risks, list):
        for risk in risks:
            if not isinstance(risk, Mapping):
                continue
            for flag in FULL_RISK_FORBIDDEN_TRUE_FLAGS:
                if flag in risk and risk.get(flag) is not False:
                    _append(codes, OUTPUT_NOT_ELIGIBLE)
    _validate_numeric_payload(payload, run, codes)
    numeric = payload.get("numeric")
    if isinstance(numeric, Mapping):
        scope_ids = {scope.get("population_id"), scope.get("label")}
        for row in numeric.values():
            if not isinstance(row, Mapping):
                continue
            if row.get("data_cutoff") != run.get("data_cutoff"):
                _append(codes, CUTOFF_MISMATCH)
            if row.get("source_revision_id") != run.get("source_revision_id"):
                _append(codes, REVISION_MISMATCH)
            if not _non_empty_str(row.get("population")) or row.get("population") not in scope_ids:
                _append(codes, AUTHORITY_MISMATCH)


def _validate_pre_lock_payload_binding(
    payload: Mapping[str, Any],
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    *,
    expected_kind: str,
    codes: list[str],
) -> None:
    if payload.get("output_kind") != expected_kind:
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    for field in ("project_id", "run_id"):
        if payload.get(field) != run.get(field):
            _append(codes, IDENTITY_MISMATCH)
    if payload.get("data_cutoff") != run.get("data_cutoff"):
        _append(codes, CUTOFF_MISMATCH)
    if payload.get("source_revision_id") != run.get("source_revision_id"):
        _append(codes, REVISION_MISMATCH)
    expected = authority_refs.get("digest") or authority_refs.get("authority_digest")
    if not _non_empty_str(expected) or payload.get("authority_digest") != expected:
        _append(codes, AUTHORITY_MISMATCH)


def _validate_revision_impact_payload(
    payload: Mapping[str, Any],
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not isinstance(payload, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    _validate_pre_lock_payload_binding(
        payload, run, authority_refs, expected_kind="revision_impact", codes=codes
    )
    from_rev = payload.get("from_source_revision_id")
    to_rev = payload.get("to_source_revision_id")
    if not _non_empty_str(from_rev) or not _non_empty_str(to_rev):
        _append(codes, REVISION_MISMATCH)
    elif from_rev == to_rev:
        _append(codes, REVISION_MISMATCH)
    if to_rev != run.get("source_revision_id"):
        _append(codes, REVISION_MISMATCH)
    if not _non_empty_str(payload.get("revision_reason")):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    impacts = payload.get("impacts")
    if not isinstance(impacts, list):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    if payload.get("impact_count") != len(impacts):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    impact_ids = [
        item.get("impact_id") for item in impacts if isinstance(item, Mapping)
    ]
    if len(set(impact_ids)) != len(impact_ids):
        _append(codes, IDENTITY_MISMATCH)
    for item in impacts:
        if not isinstance(item, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        try:
            normalized = _normalize_impact_item(
                item,
                from_rev=str(from_rev),
                to_rev=str(to_rev),
                project_id=str(run.get("project_id") or ""),
            )
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)
        else:
            if canonical_bytes(item) != canonical_bytes(normalized):
                _append(codes, IDENTITY_MISMATCH)


def _validate_check_package_payload(
    payload: Mapping[str, Any],
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not isinstance(payload, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    _validate_pre_lock_payload_binding(
        payload, run, authority_refs, expected_kind="check_package", codes=codes
    )
    items = payload.get("check_items")
    if not isinstance(items, list):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    if items:
        levels = {item.get("level") for item in items if isinstance(item, Mapping)}
        if not CHECK_LEVELS.issubset(levels):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    else:
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    check_ids = [item.get("check_id") for item in items if isinstance(item, Mapping)]
    if len(set(check_ids)) != len(check_ids):
        _append(codes, IDENTITY_MISMATCH)
    for item in items:
        if not isinstance(item, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        try:
            normalized = _normalize_check_item(item, run)
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)
        else:
            if canonical_bytes(item) != canonical_bytes(normalized):
                _append(codes, IDENTITY_MISMATCH)
    summary = payload.get("coverage_summary")
    expected_summary = recompute_check_coverage_summary(
        [item for item in items if isinstance(item, Mapping)]
    )
    if not isinstance(summary, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    elif canonical_bytes(summary) != canonical_bytes(expected_summary):
        _append(codes, AUTHORITY_MISMATCH)


def _validate_query_revision_package_payload(
    payload: Mapping[str, Any],
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not isinstance(payload, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    _validate_pre_lock_payload_binding(
        payload,
        run,
        authority_refs,
        expected_kind="query_revision_package",
        codes=codes,
    )
    for flag in (
        "is_sent",
        "is_closed",
        "is_user_confirmed",
        "pd_registration_allowed",
        "external_dispatch_allowed",
    ):
        if flag not in payload or payload.get(flag) is not False:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    for key in QUERY_FORBIDDEN_KEYS:
        if key in payload and payload.get(key) not in (None, "", False):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    for flag in QUERY_FORBIDDEN_TRUE_FLAGS:
        if flag in payload and payload.get(flag) is not False:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    entries = payload.get("revision_entries")
    if not isinstance(entries, list):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    if payload.get("entry_count") != len(entries):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    draft_ids = [
        entry.get("query_draft_id") for entry in entries if isinstance(entry, Mapping)
    ]
    if len(set(draft_ids)) != len(draft_ids):
        _append(codes, IDENTITY_MISMATCH)
    for entry in entries:
        if not isinstance(entry, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        try:
            normalized = _normalize_revision_entry(entry, run)
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)
        else:
            if canonical_bytes(entry) != canonical_bytes(normalized):
                _append(codes, IDENTITY_MISMATCH)
