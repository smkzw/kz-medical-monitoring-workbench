"""Post-lock/pre-CFDI fixed-total report payload authority."""

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
from .mode_output_pre_lock import *
from .mode_output_pre_lock import (
    _shared_payload_identity,
    _require_pre_lock_run,
    _normalize_population_scope,
    _impact_id,
    _normalize_impact_item,
    _check_id,
    _normalize_check_item,
    _normalize_revision_entry,
    _normalize_supplied_query_draft,
    _default_pre_lock_payload_for_kind,
    _validate_full_risk_payload,
    _validate_pre_lock_payload_binding,
    _validate_revision_impact_payload,
    _validate_check_package_payload,
    _validate_query_revision_package_payload,
)

def _require_post_lock_run(run_binding: Mapping[str, Any]) -> dict:
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
    if run.get("mode") != "post_lock_pre_cfdi":
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "post_lock payloads require run.mode=post_lock_pre_cfdi",
        )
    if run.get("execution_basis") != "full":
        raise ModeOutputError(
            MODE_ENTRY_BLOCKED,
            "post_lock payloads require execution_basis=full",
        )
    if run.get("fixed_total") is not True:
        raise ModeOutputError(
            MODE_ENTRY_BLOCKED, "post_lock payloads require fixed_total=true"
        )
    for field in (
        "locked_snapshot_hash",
        "acceptance_evidence_hash",
        "local_os_user",
    ):
        _require_non_empty_str(run.get(field), field, MODE_ENTRY_BLOCKED)
    if run.get("output_cutoff_ref") != run.get("data_cutoff"):
        raise ModeOutputError(
            CUTOFF_MISMATCH, "output_cutoff_ref must equal data_cutoff"
        )
    if run.get("output_revision_ref") != run.get("source_revision_id"):
        raise ModeOutputError(
            REVISION_MISMATCH, "output_revision_ref must equal source_revision_id"
        )
    return run


def _normalize_population_totals(raw: Any) -> dict:
    if not isinstance(raw, Mapping):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "population_totals must be a mapping"
        )
    totals: dict[str, int] = {}
    for key in POPULATION_TOTAL_KEYS:
        value = raw.get(key)
        # bool is a subclass of int — reject explicitly.
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                f"population_totals.{key} must be a non-negative int (not bool)",
            )
        totals[key] = value
    return totals


def _shared_post_lock_identity(
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    population_totals: Mapping[str, Any],
) -> dict:
    shared = _shared_payload_identity(run, authority_refs)
    totals = _normalize_population_totals(population_totals)
    return {
        **shared,
        "locked_snapshot_hash": run.get("locked_snapshot_hash"),
        "acceptance_evidence_hash": run.get("acceptance_evidence_hash"),
        "fixed_total": True,
        "population_totals": totals,
    }


def _reject_overwrite_metadata(raw: Mapping[str, Any]) -> None:
    for key in POST_LOCK_OVERWRITE_META_KEYS:
        if key in raw and raw.get(key) not in (None, "", False):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                f"overwrite metadata {key!r} is forbidden in post_lock slice",
            )


def _append_post_lock_surface_claim_codes(
    obj: Mapping[str, Any], codes: list[str]
) -> None:
    """Reject draft/PD/overwrite/external claims on post-lock payload or envelope."""
    if not isinstance(obj, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    for flag in POST_LOCK_FORBIDDEN_TRUE_FLAGS:
        if flag in obj and obj.get(flag) is not False:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    for key in POST_LOCK_FORBIDDEN_WORKFLOW_KEYS:
        if key in obj and obj.get(key) not in (None, "", False):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    for key in POST_LOCK_OVERWRITE_META_KEYS:
        if key in obj and obj.get(key) not in (None, "", False):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    if obj.get("producer_kind") == PRODUCER_EXTERNAL:
        _append(codes, AUTHORITY_MISMATCH)
    for key in EXTERNAL_REPORT_REQUIRED:
        if key in obj and obj.get(key) not in (None, "", False):
            _append(codes, AUTHORITY_MISMATCH)


def _assert_post_lock_surface_claims(obj: Mapping[str, Any], *, surface: str) -> None:
    codes: list[str] = []
    _append_post_lock_surface_claim_codes(obj, codes)
    if codes:
        raise ModeOutputError(
            codes[0],
            f"post_lock {surface} carries forbidden draft/PD/overwrite/external claims",
        )


def _normalize_evidence_refs(raw: Any, *, field: str = "evidence_refs") -> list:
    if not isinstance(raw, list) or not raw:
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, f"{field} must be a non-empty list")
    normalized: list = []
    for item in raw:
        if isinstance(item, Mapping):
            if not _non_empty_str(item.get("evidence_id")) and not _non_empty_str(
                item.get("ref")
            ):
                raise ModeOutputError(
                    OUTPUT_NOT_ELIGIBLE, f"{field} mapping lacks evidence_id/ref"
                )
            normalized.append(_copy_mapping(item))
        elif _non_empty_str(item):
            normalized.append(str(item))
        else:
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, f"{field} entry invalid")
    # Deterministic order so semantically identical inputs yield identical nested IDs.
    normalized.sort(key=lambda item: canonical_bytes(item))
    return normalized


def _normalize_checkable_locator(raw: Any) -> dict:
    if not isinstance(raw, Mapping) or not raw:
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "locator must be a non-empty mapping")
    loc = _copy_mapping(raw)
    if not any(
        _non_empty_str(loc.get(key)) for key in ("path", "record_id", "field", "uri")
    ):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "locator must be independently checkable"
        )
    return loc


def _normalize_id_list(raw: Any, *, field: str) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, f"{field} must be a sequence")
    ids: list[str] = []
    for item in raw:
        value = _require_non_empty_str(item, field, OUTPUT_NOT_ELIGIBLE)
        ids.append(value)
    if len(set(ids)) != len(ids):
        raise ModeOutputError(IDENTITY_MISMATCH, f"duplicate entries in {field}")
    return ids


def _normalize_project_summary(
    raw: Any, population_totals: Mapping[str, int]
) -> dict:
    if not isinstance(raw, Mapping) or not raw:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "project_summary must be a non-empty mapping"
        )
    summary = _copy_mapping(raw)
    for key in POPULATION_TOTAL_KEYS:
        if key not in summary:
            continue
        value = summary.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                f"project_summary.{key} must be a non-negative int (not bool)",
            )
        if value != population_totals.get(key):
            raise ModeOutputError(
                AUTHORITY_MISMATCH,
                f"project_summary.{key} must equal population_totals.{key}",
            )
    return summary


def _validate_post_lock_payload_binding(
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
    if payload.get("locked_snapshot_hash") != run.get("locked_snapshot_hash"):
        _append(codes, IDENTITY_MISMATCH)
    if payload.get("acceptance_evidence_hash") != run.get("acceptance_evidence_hash"):
        _append(codes, IDENTITY_MISMATCH)
    if payload.get("fixed_total") is not True:
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    try:
        expected_totals = _normalize_population_totals(payload.get("population_totals"))
    except ModeOutputError as exc:
        _append(codes, exc.failure_code)
        return
    if canonical_bytes(payload.get("population_totals")) != canonical_bytes(
        expected_totals
    ):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    for key in POST_LOCK_OVERWRITE_META_KEYS:
        if key in payload and payload.get(key) not in (None, "", False):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    # Draft-only / no-send / no-sign / no-PD aliases: present non-false fails closed.
    for flag in POST_LOCK_FORBIDDEN_TRUE_FLAGS:
        if flag in payload and payload.get(flag) is not False:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    for key in POST_LOCK_FORBIDDEN_WORKFLOW_KEYS:
        if key in payload and payload.get(key) not in (None, "", False):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    # System post-lock payloads must not carry external-report identity fields.
    if payload.get("producer_kind") == PRODUCER_EXTERNAL:
        _append(codes, AUTHORITY_MISMATCH)
    for key in EXTERNAL_REPORT_REQUIRED:
        if key in payload and payload.get(key) not in (None, "", False):
            _append(codes, AUTHORITY_MISMATCH)


def _normalize_risk_summary(
    raw: Any, *, risk_count: int
) -> dict:
    if not isinstance(raw, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "risk_summary must be a mapping")
    summary: dict[str, Any] = {}
    total = 0
    for key in RISK_SUMMARY_COUNT_KEYS:
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                f"risk_summary.{key} must be a non-negative int (not bool)",
            )
        summary[key] = value
        total += value
    if total != risk_count:
        raise ModeOutputError(
            AUTHORITY_MISMATCH,
            "risk_summary counts must equal population_totals.risk_count",
        )
    risk_ids = _normalize_id_list(raw.get("risk_ids"), field="risk_summary.risk_ids")
    if len(risk_ids) != risk_count:
        raise ModeOutputError(
            AUTHORITY_MISMATCH,
            "unique risk_ids length must equal population_totals.risk_count",
        )
    summary["risk_ids"] = sorted(risk_ids)
    return summary


def _site_material_id(item: Mapping[str, Any]) -> str:
    fields = (
        "site_id",
        "subject_ids",
        "risk_ids",
        "evidence_refs",
        "locator",
    )
    return "smat-" + sha256_hex(
        canonical_bytes({field: copy.deepcopy(item.get(field)) for field in fields})
    )[:32]


def _subject_material_id(item: Mapping[str, Any]) -> str:
    fields = (
        "subject_id",
        "site_id",
        "profile_ref",
        "timeline_ref",
        "risk_ids",
        "evidence_refs",
        "locator",
    )
    return "submat-" + sha256_hex(
        canonical_bytes({field: copy.deepcopy(item.get(field)) for field in fields})
    )[:32]


def _post_lock_check_id(item: Mapping[str, Any]) -> str:
    fields = (
        "level",
        "check_kind",
        "scope_id",
        "status",
        "risk_ids",
        "evidence_refs",
        "locator",
        "coverage_missing",
        "evidence_conflict",
    )
    return "plchk-" + sha256_hex(
        canonical_bytes({field: copy.deepcopy(item.get(field)) for field in fields})
    )[:32]


def _checklist_id_from_items(
    items: Sequence[Mapping[str, Any]], locked: Mapping[str, Any]
) -> str:
    body = {
        "check_items": copy.deepcopy(list(items)),
        "project_id": locked.get("project_id"),
        "run_id": locked.get("run_id"),
        "data_cutoff": locked.get("data_cutoff"),
        "source_revision_id": locked.get("source_revision_id"),
        "locked_snapshot_hash": locked.get("locked_snapshot_hash"),
        "authority_digest": locked.get("authority_digest"),
        "population_totals": locked.get("population_totals"),
    }
    return "cl-" + sha256_hex(canonical_bytes(body))[:32]


def _report_id_from_body(body: Mapping[str, Any]) -> str:
    return "fpr-" + sha256_hex(canonical_bytes(body))[:32]


def _normalize_site_material(raw: Mapping[str, Any]) -> dict:
    if not isinstance(raw, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "site material must be a mapping")
    _reject_overwrite_metadata(raw)
    site_id = _require_non_empty_str(raw.get("site_id"), "site_id", OUTPUT_NOT_ELIGIBLE)
    subject_ids = _normalize_id_list(raw.get("subject_ids"), field="subject_ids")
    risk_ids = _normalize_id_list(raw.get("risk_ids"), field="risk_ids")
    evidence = _normalize_evidence_refs(raw.get("evidence_refs"))
    locator = _normalize_checkable_locator(raw.get("locator"))
    item = {
        "site_id": site_id,
        "subject_ids": sorted(subject_ids),
        "risk_ids": sorted(risk_ids),
        "evidence_refs": evidence,
        "locator": locator,
    }
    computed = _site_material_id(item)
    supplied = raw.get("site_material_id")
    if supplied is not None and supplied != computed:
        raise ModeOutputError(
            IDENTITY_MISMATCH, "site_material_id does not match canonical content"
        )
    item["site_material_id"] = computed
    return item


def _normalize_subject_material(raw: Mapping[str, Any]) -> dict:
    if not isinstance(raw, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "subject material must be a mapping")
    _reject_overwrite_metadata(raw)
    subject_id = _require_non_empty_str(
        raw.get("subject_id"), "subject_id", OUTPUT_NOT_ELIGIBLE
    )
    site_id = _require_non_empty_str(raw.get("site_id"), "site_id", OUTPUT_NOT_ELIGIBLE)
    profile_ref = raw.get("profile_ref")
    timeline_ref = raw.get("timeline_ref")
    if not isinstance(profile_ref, Mapping) or not _non_empty_str(
        profile_ref.get("profile_id") or profile_ref.get("ref")
    ):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "profile_ref must be an entry mapping with profile_id/ref"
        )
    if not isinstance(timeline_ref, Mapping) or not _non_empty_str(
        timeline_ref.get("timeline_id") or timeline_ref.get("ref")
    ):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "timeline_ref must be an entry mapping with timeline_id/ref",
        )
    profile = _copy_mapping(profile_ref)
    timeline = _copy_mapping(timeline_ref)
    # Dual primary/ref keys: if both keys are present, both values must be
    # non-empty strings and exactly equal. Single-key entries remain valid.
    for name, entry, primary_key in (
        ("profile_ref", profile, "profile_id"),
        ("timeline_ref", timeline, "timeline_id"),
    ):
        if primary_key in entry and "ref" in entry:
            primary = entry.get(primary_key)
            ref = entry.get("ref")
            if not _non_empty_str(primary) or not _non_empty_str(ref):
                raise ModeOutputError(
                    IDENTITY_MISMATCH,
                    f"{name}.{primary_key} and ref must both be non-empty when both keys are present",
                )
            if str(primary) != str(ref):
                raise ModeOutputError(
                    IDENTITY_MISMATCH,
                    f"{name}.{primary_key} and ref must be the same non-empty identity",
                )
    # Bind Profile/Timeline entries to this material subject; reject cross-subject jumps.
    for name, entry in (("profile_ref", profile), ("timeline_ref", timeline)):
        bound = entry.get("subject_id")
        if bound in (None, ""):
            entry["subject_id"] = subject_id
        elif not _non_empty_str(bound):
            raise ModeOutputError(
                IDENTITY_MISMATCH, f"{name}.subject_id must be a non-empty string"
            )
        elif bound != subject_id:
            raise ModeOutputError(
                IDENTITY_MISMATCH,
                f"{name}.subject_id must equal material subject_id",
            )
    risk_ids = _normalize_id_list(raw.get("risk_ids"), field="risk_ids")
    evidence = _normalize_evidence_refs(raw.get("evidence_refs"))
    locator = _normalize_checkable_locator(raw.get("locator"))
    item = {
        "subject_id": subject_id,
        "site_id": site_id,
        "profile_ref": profile,
        "timeline_ref": timeline,
        "risk_ids": sorted(risk_ids),
        "evidence_refs": evidence,
        "locator": locator,
    }
    computed = _subject_material_id(item)
    supplied = raw.get("subject_material_id")
    if supplied is not None and supplied != computed:
        raise ModeOutputError(
            IDENTITY_MISMATCH, "subject_material_id does not match canonical content"
        )
    item["subject_material_id"] = computed
    return item


def _normalize_post_lock_check_item(
    raw: Mapping[str, Any], run: Mapping[str, Any]
) -> dict:
    if not isinstance(raw, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "check_item must be a mapping")
    _reject_overwrite_metadata(raw)
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
    scope_id = _require_non_empty_str(raw.get("scope_id"), "scope_id", OUTPUT_NOT_ELIGIBLE)
    if level == "project" and scope_id != run.get("project_id"):
        raise ModeOutputError(
            IDENTITY_MISMATCH, "project-level scope_id must equal run.project_id"
        )
    risk_ids = _normalize_id_list(raw.get("risk_ids") or [], field="risk_ids")
    evidence = _normalize_evidence_refs(raw.get("evidence_refs"))
    locator = _normalize_checkable_locator(raw.get("locator"))
    item = {
        "level": level,
        "check_kind": check_kind,
        "scope_id": scope_id,
        "status": status,
        "risk_ids": sorted(risk_ids),
        "evidence_refs": evidence,
        "locator": locator,
        "evidence_conflict": bool(evidence_conflict),
        "coverage_missing": bool(coverage_missing),
    }
    computed = _post_lock_check_id(item)
    supplied = raw.get("check_id")
    if supplied is not None and supplied != computed:
        raise ModeOutputError(
            IDENTITY_MISMATCH, "check_id does not match canonical content"
        )
    item["check_id"] = computed
    return item


def build_site_materials_payload(
    run_binding: Mapping[str, Any],
    *,
    materials: Optional[Sequence[Mapping[str, Any]]] = None,
    population_totals: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
) -> dict:
    """Build post_lock ``site_materials`` with fixed totals and stable IDs."""
    run = _require_post_lock_run(run_binding)
    auth = _require_ref_mapping(authority_refs, "authority_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    if materials is None:
        materials = []
    if not isinstance(materials, Sequence) or isinstance(materials, (str, bytes)):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "materials must be a sequence")
    items = [_normalize_site_material(item) for item in materials]
    material_ids = [item["site_material_id"] for item in items]
    site_ids = [item["site_id"] for item in items]
    if len(set(material_ids)) != len(material_ids):
        raise ModeOutputError(IDENTITY_MISMATCH, "duplicate site_material_id")
    if len(set(site_ids)) != len(site_ids):
        raise ModeOutputError(IDENTITY_MISMATCH, "duplicate site_id in site_materials")
    all_subjects: list[str] = []
    all_risks: list[str] = []
    for item in items:
        all_subjects.extend(item["subject_ids"])
        all_risks.extend(item["risk_ids"])
    if len(set(all_subjects)) != len(all_subjects):
        raise ModeOutputError(
            IDENTITY_MISMATCH, "duplicate subject_id across site_materials"
        )
    if len(set(all_risks)) != len(all_risks):
        raise ModeOutputError(
            IDENTITY_MISMATCH, "duplicate risk_id across site_materials"
        )
    items.sort(key=lambda row: row["site_material_id"])
    locked = _shared_post_lock_identity(run, auth, population_totals)
    if locked["population_totals"]["site_count"] != len(items):
        raise ModeOutputError(
            AUTHORITY_MISMATCH,
            "material_count/unique sites must equal population_totals.site_count",
        )
    payload = {
        "output_kind": "site_materials",
        "materials": items,
        "material_count": len(items),
        **locked,
    }
    codes: list[str] = []
    _validate_site_materials_payload(payload, run, auth, codes)
    if codes:
        raise ModeOutputError(codes[0], f"site_materials invalid: {tuple(codes)}")
    return payload


def build_subject_materials_payload(
    run_binding: Mapping[str, Any],
    *,
    materials: Optional[Sequence[Mapping[str, Any]]] = None,
    population_totals: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
) -> dict:
    """Build post_lock ``subject_materials``; Profile/Timeline refs are entries only."""
    run = _require_post_lock_run(run_binding)
    auth = _require_ref_mapping(authority_refs, "authority_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    if materials is None:
        materials = []
    if not isinstance(materials, Sequence) or isinstance(materials, (str, bytes)):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "materials must be a sequence")
    items = [_normalize_subject_material(item) for item in materials]
    material_ids = [item["subject_material_id"] for item in items]
    subject_ids = [item["subject_id"] for item in items]
    if len(set(material_ids)) != len(material_ids):
        raise ModeOutputError(IDENTITY_MISMATCH, "duplicate subject_material_id")
    if len(set(subject_ids)) != len(subject_ids):
        raise ModeOutputError(
            IDENTITY_MISMATCH, "duplicate subject_id in subject_materials"
        )
    items.sort(key=lambda row: row["subject_material_id"])
    locked = _shared_post_lock_identity(run, auth, population_totals)
    if locked["population_totals"]["subject_count"] != len(items):
        raise ModeOutputError(
            AUTHORITY_MISMATCH,
            "material_count must equal population_totals.subject_count",
        )
    payload = {
        "output_kind": "subject_materials",
        "materials": items,
        "material_count": len(items),
        **locked,
    }
    codes: list[str] = []
    _validate_subject_materials_payload(payload, run, auth, codes)
    if codes:
        raise ModeOutputError(codes[0], f"subject_materials invalid: {tuple(codes)}")
    return payload


def build_checklist_payload(
    run_binding: Mapping[str, Any],
    *,
    check_items: Optional[Sequence[Mapping[str, Any]]] = None,
    population_totals: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
) -> dict:
    """Build post_lock ``checklist`` with recomputable coverage_summary."""
    run = _require_post_lock_run(run_binding)
    auth = _require_ref_mapping(authority_refs, "authority_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    if check_items is None:
        check_items = []
    if not isinstance(check_items, Sequence) or isinstance(check_items, (str, bytes)):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "check_items must be a sequence")
    items = [_normalize_post_lock_check_item(item, run) for item in check_items]
    if len({item["check_id"] for item in items}) != len(items):
        raise ModeOutputError(IDENTITY_MISMATCH, "duplicate check_id in checklist")
    levels_present = {item["level"] for item in items}
    missing = CHECK_LEVELS - levels_present
    if missing:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            f"checklist must include project/site/subject levels; missing={sorted(missing)}",
        )
    items.sort(key=lambda row: (row["level"], row["check_id"]))
    summary = recompute_check_coverage_summary(items)
    locked = _shared_post_lock_identity(run, auth, population_totals)
    checklist_id = _checklist_id_from_items(items, locked)
    payload = {
        "output_kind": "checklist",
        "checklist_id": checklist_id,
        "check_items": items,
        "item_count": len(items),
        "coverage_summary": summary,
        **locked,
    }
    codes: list[str] = []
    _validate_checklist_payload(payload, run, auth, codes)
    if codes:
        raise ModeOutputError(codes[0], f"checklist invalid: {tuple(codes)}")
    return payload


def build_full_project_report_payload(
    run_binding: Mapping[str, Any],
    *,
    report_version: str,
    project_summary: Any,
    risk_summary: Mapping[str, Any],
    site_material_ids: Optional[Sequence[str]] = None,
    subject_material_ids: Optional[Sequence[str]] = None,
    checklist_id: str,
    evidence_refs: Sequence[Any],
    population_totals: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    report_id: Optional[str] = None,
) -> dict:
    """Build post_lock ``full_project_report`` (system draft; not external review)."""
    run = _require_post_lock_run(run_binding)
    auth = _require_ref_mapping(authority_refs, "authority_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    version = _require_non_empty_str(report_version, "report_version", OUTPUT_NOT_ELIGIBLE)
    checklist = _require_non_empty_str(checklist_id, "checklist_id", IDENTITY_MISMATCH)
    locked = _shared_post_lock_identity(run, auth, population_totals)
    summary = _normalize_project_summary(project_summary, locked["population_totals"])
    risk = _normalize_risk_summary(
        risk_summary, risk_count=locked["population_totals"]["risk_count"]
    )
    site_ids = _normalize_id_list(
        site_material_ids or [], field="site_material_ids"
    )
    subject_ids = _normalize_id_list(
        subject_material_ids or [], field="subject_material_ids"
    )
    if len(site_ids) != locked["population_totals"]["site_count"]:
        raise ModeOutputError(
            AUTHORITY_MISMATCH,
            "site_material_ids length must equal population_totals.site_count",
        )
    if len(subject_ids) != locked["population_totals"]["subject_count"]:
        raise ModeOutputError(
            AUTHORITY_MISMATCH,
            "subject_material_ids length must equal population_totals.subject_count",
        )
    evidence = _normalize_evidence_refs(evidence_refs)
    draft_flags = {flag: False for flag in POST_LOCK_FORBIDDEN_TRUE_FLAGS}
    body = {
        "output_kind": "full_project_report",
        "report_version": version,
        "project_summary": summary,
        "risk_summary": risk,
        "site_material_ids": sorted(site_ids),
        "subject_material_ids": sorted(subject_ids),
        "checklist_id": checklist,
        "evidence_refs": evidence,
        **draft_flags,
        **locked,
    }
    computed_report_id = _report_id_from_body(body)
    if report_id is not None and report_id != computed_report_id:
        raise ModeOutputError(
            IDENTITY_MISMATCH, "report_id does not match canonical content"
        )
    payload = {"report_id": computed_report_id, **body}
    codes: list[str] = []
    _validate_full_project_report_payload(payload, run, auth, codes)
    if codes:
        raise ModeOutputError(
            codes[0], f"full_project_report invalid: {tuple(codes)}"
        )
    return payload


def _validate_site_materials_payload(
    payload: Mapping[str, Any],
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not isinstance(payload, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    _validate_post_lock_payload_binding(
        payload, run, authority_refs, expected_kind="site_materials", codes=codes
    )
    materials = payload.get("materials")
    if not isinstance(materials, list):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    if payload.get("material_count") != len(materials):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    totals = payload.get("population_totals")
    if isinstance(totals, Mapping) and totals.get("site_count") != len(materials):
        _append(codes, AUTHORITY_MISMATCH)
    material_ids = []
    site_ids = []
    subjects: list[str] = []
    risks: list[str] = []
    for item in materials:
        if not isinstance(item, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        try:
            normalized = _normalize_site_material(item)
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)
            continue
        if canonical_bytes(item) != canonical_bytes(normalized):
            _append(codes, IDENTITY_MISMATCH)
        material_ids.append(item.get("site_material_id"))
        site_ids.append(item.get("site_id"))
        subjects.extend(list(item.get("subject_ids") or []))
        risks.extend(list(item.get("risk_ids") or []))
    if len(set(material_ids)) != len(material_ids):
        _append(codes, IDENTITY_MISMATCH)
    if len(set(site_ids)) != len(site_ids):
        _append(codes, IDENTITY_MISMATCH)
    if len(set(subjects)) != len(subjects):
        _append(codes, IDENTITY_MISMATCH)
    if len(set(risks)) != len(risks):
        _append(codes, IDENTITY_MISMATCH)


def _validate_subject_materials_payload(
    payload: Mapping[str, Any],
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not isinstance(payload, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    _validate_post_lock_payload_binding(
        payload, run, authority_refs, expected_kind="subject_materials", codes=codes
    )
    materials = payload.get("materials")
    if not isinstance(materials, list):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    if payload.get("material_count") != len(materials):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    totals = payload.get("population_totals")
    if isinstance(totals, Mapping) and totals.get("subject_count") != len(materials):
        _append(codes, AUTHORITY_MISMATCH)
    material_ids = []
    subject_ids = []
    for item in materials:
        if not isinstance(item, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        try:
            normalized = _normalize_subject_material(item)
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)
            continue
        if canonical_bytes(item) != canonical_bytes(normalized):
            _append(codes, IDENTITY_MISMATCH)
        material_ids.append(item.get("subject_material_id"))
        subject_ids.append(item.get("subject_id"))
    if len(set(material_ids)) != len(material_ids):
        _append(codes, IDENTITY_MISMATCH)
    if len(set(subject_ids)) != len(subject_ids):
        _append(codes, IDENTITY_MISMATCH)


def _validate_checklist_payload(
    payload: Mapping[str, Any],
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not isinstance(payload, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    _validate_post_lock_payload_binding(
        payload, run, authority_refs, expected_kind="checklist", codes=codes
    )
    items = payload.get("check_items")
    if not isinstance(items, list):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    if not items:
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    else:
        levels = {item.get("level") for item in items if isinstance(item, Mapping)}
        if not CHECK_LEVELS.issubset(levels):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    if payload.get("item_count") != len(items):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    check_ids = []
    normalized_items = []
    for item in items:
        if not isinstance(item, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        try:
            normalized = _normalize_post_lock_check_item(item, run)
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)
            continue
        if canonical_bytes(item) != canonical_bytes(normalized):
            _append(codes, IDENTITY_MISMATCH)
        check_ids.append(item.get("check_id"))
        normalized_items.append(normalized)
    if len(set(check_ids)) != len(check_ids):
        _append(codes, IDENTITY_MISMATCH)
    summary = payload.get("coverage_summary")
    expected_summary = recompute_check_coverage_summary(normalized_items)
    if not isinstance(summary, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    elif canonical_bytes(summary) != canonical_bytes(expected_summary):
        _append(codes, AUTHORITY_MISMATCH)
    locked = {
        "project_id": payload.get("project_id"),
        "run_id": payload.get("run_id"),
        "data_cutoff": payload.get("data_cutoff"),
        "source_revision_id": payload.get("source_revision_id"),
        "locked_snapshot_hash": payload.get("locked_snapshot_hash"),
        "authority_digest": payload.get("authority_digest"),
        "population_totals": payload.get("population_totals"),
    }
    expected_id = _checklist_id_from_items(normalized_items, locked)
    if payload.get("checklist_id") != expected_id:
        _append(codes, IDENTITY_MISMATCH)


def _validate_full_project_report_payload(
    payload: Mapping[str, Any],
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    codes: list[str],
) -> None:
    if not isinstance(payload, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    _validate_post_lock_payload_binding(
        payload, run, authority_refs, expected_kind="full_project_report", codes=codes
    )
    if not _non_empty_str(payload.get("report_version")):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    totals = payload.get("population_totals")
    try:
        if not isinstance(totals, Mapping):
            raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "population_totals required")
        normalized_totals = _normalize_population_totals(totals)
        summary = _normalize_project_summary(
            payload.get("project_summary"), normalized_totals
        )
    except ModeOutputError as exc:
        _append(codes, exc.failure_code)
        summary = None
    else:
        if canonical_bytes(payload.get("project_summary")) != canonical_bytes(summary):
            _append(codes, IDENTITY_MISMATCH)
    for flag in POST_LOCK_REQUIRED_FALSE_FLAGS:
        if flag not in payload or payload.get(flag) is not False:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    for flag in POST_LOCK_FORBIDDEN_TRUE_FLAGS:
        if flag in payload and payload.get(flag) is not False:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
    risk = None
    if isinstance(totals, Mapping):
        try:
            risk_count = totals.get("risk_count")
            if isinstance(risk_count, bool) or not isinstance(risk_count, int):
                raise ModeOutputError(
                    OUTPUT_NOT_ELIGIBLE, "population_totals.risk_count invalid"
                )
            risk = _normalize_risk_summary(
                payload.get("risk_summary"), risk_count=risk_count
            )
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)
        else:
            if canonical_bytes(payload.get("risk_summary")) != canonical_bytes(risk):
                _append(codes, IDENTITY_MISMATCH)
    else:
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    for field in ("site_material_ids", "subject_material_ids"):
        values = payload.get(field)
        if not isinstance(values, list):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        try:
            normalized = _normalize_id_list(values, field=field)
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)
            continue
        if sorted(str(v) for v in values) != normalized:
            _append(codes, IDENTITY_MISMATCH)
    if isinstance(totals, Mapping):
        site_ids = payload.get("site_material_ids")
        subject_ids = payload.get("subject_material_ids")
        if isinstance(site_ids, list) and len(site_ids) != totals.get("site_count"):
            _append(codes, AUTHORITY_MISMATCH)
        if isinstance(subject_ids, list) and len(subject_ids) != totals.get(
            "subject_count"
        ):
            _append(codes, AUTHORITY_MISMATCH)
    if not _non_empty_str(payload.get("checklist_id")):
        _append(codes, IDENTITY_MISMATCH)
    try:
        evidence = _normalize_evidence_refs(payload.get("evidence_refs"))
    except ModeOutputError as exc:
        _append(codes, exc.failure_code)
        evidence = None
    else:
        if canonical_bytes(payload.get("evidence_refs")) != canonical_bytes(evidence):
            _append(codes, IDENTITY_MISMATCH)
    body = {key: copy.deepcopy(payload.get(key)) for key in payload if key != "report_id"}
    expected_report_id = _report_id_from_body(body)
    if payload.get("report_id") != expected_report_id:
        _append(codes, IDENTITY_MISMATCH)

def _default_post_lock_payload_for_kind(
    output_kind: str,
    run: Mapping[str, Any],
    authority_refs: Mapping[str, Any],
    output_spec: Mapping[str, Any],
) -> dict:
    totals = output_spec.get("population_totals")
    if not isinstance(totals, Mapping):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "post_lock outputs require population_totals in output_spec",
        )
    if output_kind == "site_materials":
        return build_site_materials_payload(
            run,
            materials=output_spec.get("materials") or [],
            population_totals=totals,
            authority_refs=authority_refs,
        )
    if output_kind == "subject_materials":
        return build_subject_materials_payload(
            run,
            materials=output_spec.get("materials") or [],
            population_totals=totals,
            authority_refs=authority_refs,
        )
    if output_kind == "checklist":
        return build_checklist_payload(
            run,
            check_items=output_spec.get("check_items") or [],
            population_totals=totals,
            authority_refs=authority_refs,
        )
    if output_kind == "full_project_report":
        report_version = output_spec.get("report_version")
        project_summary = output_spec.get("project_summary")
        risk_summary = output_spec.get("risk_summary")
        checklist_id = output_spec.get("checklist_id")
        evidence_refs = output_spec.get("evidence_refs")
        if (
            not _non_empty_str(report_version)
            or not isinstance(project_summary, Mapping)
            or not isinstance(risk_summary, Mapping)
            or not _non_empty_str(checklist_id)
            or evidence_refs is None
        ):
            raise ModeOutputError(
                OUTPUT_NOT_ELIGIBLE,
                "full_project_report requires report_version, project_summary, "
                "risk_summary, checklist_id, evidence_refs",
            )
        return build_full_project_report_payload(
            run,
            report_version=str(report_version),
            project_summary=project_summary,
            risk_summary=risk_summary,
            site_material_ids=output_spec.get("site_material_ids") or [],
            subject_material_ids=output_spec.get("subject_material_ids") or [],
            checklist_id=str(checklist_id),
            evidence_refs=evidence_refs,
            population_totals=totals,
            authority_refs=authority_refs,
            report_id=output_spec.get("report_id"),
        )
    raise ModeOutputError(
        OUTPUT_NOT_ELIGIBLE, f"unknown post_lock output_kind={output_kind!r}"
    )
