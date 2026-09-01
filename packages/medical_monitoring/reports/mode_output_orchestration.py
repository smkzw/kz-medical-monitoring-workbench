"""Mode-output envelope orchestration and cross-mode validation."""

from __future__ import annotations

import copy
from typing import Any, Mapping, Optional, Sequence, Tuple

from . import mode_output_core as _core
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
from .mode_output_post_lock import *
from .mode_output_post_lock import (
    _require_post_lock_run,
    _normalize_population_totals,
    _shared_post_lock_identity,
    _reject_overwrite_metadata,
    _append_post_lock_surface_claim_codes,
    _assert_post_lock_surface_claims,
    _normalize_evidence_refs,
    _normalize_checkable_locator,
    _normalize_id_list,
    _normalize_project_summary,
    _validate_post_lock_payload_binding,
    _normalize_risk_summary,
    _site_material_id,
    _subject_material_id,
    _post_lock_check_id,
    _checklist_id_from_items,
    _report_id_from_body,
    _normalize_site_material,
    _normalize_subject_material,
    _normalize_post_lock_check_item,
    _validate_site_materials_payload,
    _validate_subject_materials_payload,
    _validate_checklist_payload,
    _validate_full_project_report_payload,
    _default_post_lock_payload_for_kind,
)

# The common default-payload dispatcher intentionally resolves the two
# mode-specific builders at call time. Bind them after the cohesive payload
# modules load, preserving that behavior without an import cycle.
_core._default_pre_lock_payload_for_kind = _default_pre_lock_payload_for_kind
_core._default_post_lock_payload_for_kind = _default_post_lock_payload_for_kind

def build_mode_output(
    run_binding: Mapping[str, Any],
    mode_contract: Mapping[str, Any],
    output_spec: Mapping[str, Any],
    *,
    authority_refs: Mapping[str, Any],
    coverage_refs: Mapping[str, Any],
    qc_refs: Mapping[str, Any],
    entry_context: Optional[Mapping[str, Any]] = None,
    prior_run: Optional[Mapping[str, Any]] = None,
) -> dict:
    """Build an immutable ModeOutput envelope for one eligible output_kind.

    Fail-closes when the Run gate fails, the kind is not eligible for the mode,
    eligibility predicates fail, authority/coverage/QC refs drift, or
    ``producer_kind`` / external-report fields are inconsistent. Inputs are
    never mutated. ``is_user_confirmed`` is always ``False`` on construction.
    """
    if not isinstance(run_binding, Mapping) or not isinstance(mode_contract, Mapping):
        raise ModeOutputError(IDENTITY_MISMATCH, "run_binding/mode_contract required")
    if not isinstance(output_spec, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "output_spec must be a mapping")

    run = _copy_mapping(run_binding)
    contract = _copy_mapping(mode_contract)
    spec = _copy_mapping(output_spec)

    if not isinstance(entry_context, Mapping):
        raise ModeOutputError(
            MODE_ENTRY_BLOCKED, "entry_context must be explicitly supplied"
        )
    gate_codes = validate_run_mode_gate(
        run,
        contract,
        entry_context=entry_context,
        prior_run=prior_run,
    )
    if gate_codes:
        # Prefer the first gate code; mode entry blocks output eligibility.
        raise ModeOutputError(gate_codes[0], f"run gate blocked output: {gate_codes}")

    output_kind = _require_non_empty_str(
        spec.get("output_kind"), "output_kind", OUTPUT_NOT_ELIGIBLE
    )
    eligible = _eligible_kinds_for_mode(contract)
    if output_kind not in eligible:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            f"output_kind={output_kind!r} not eligible for mode={contract.get('mode')!r}",
        )

    producer_kind = spec.get("producer_kind") or PRODUCER_SYSTEM
    if producer_kind not in PRODUCER_KINDS:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, f"unknown producer_kind={producer_kind!r}"
        )
    # Daily / pre_lock / post_lock default outputs are system monitoring — never rename as report review.
    if output_kind in SYSTEM_DEFAULT_OUTPUT_KINDS and producer_kind != PRODUCER_SYSTEM:
        raise ModeOutputError(
            AUTHORITY_MISMATCH,
            "system default outputs must use producer_kind=system_monitoring_output",
        )
    if output_kind == "external_report_review_bundle" and producer_kind != PRODUCER_EXTERNAL:
        raise ModeOutputError(
            AUTHORITY_MISMATCH,
            "external_report_review_bundle requires producer_kind=external_report_review",
        )

    eligibility = spec.get("eligibility")
    if not isinstance(eligibility, Mapping):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "eligibility must be explicitly supplied"
        )
    gate_spec = _copy_mapping(eligibility)
    _check_eligibility(gate_spec, producer_kind=str(producer_kind))

    auth = _require_ref_mapping(authority_refs, "authority_refs")
    cov = _require_ref_mapping(coverage_refs, "coverage_refs")
    qc = _require_ref_mapping(qc_refs, "qc_refs")
    _bind_refs_to_run(auth, run, "authority_refs")
    _bind_refs_to_run(cov, run, "coverage_refs")
    _bind_refs_to_run(qc, run, "qc_refs")

    # Cross-ref digests must not silently disagree when present under shared keys.
    for key in ("project_id", "run_id", "data_cutoff", "source_revision_id"):
        values = {auth.get(key), cov.get(key), qc.get(key)}
        values.discard(None)
        if len(values) > 1:
            raise ModeOutputError(
                AUTHORITY_MISMATCH, f"authority/coverage/qc disagree on {key}"
            )

    output_state = spec.get("output_state") or "draft_exportable"
    if output_state not in OUTPUT_STATES:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, f"invalid output_state={output_state!r}"
        )
    if spec.get("is_user_confirmed") is True:
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "is_user_confirmed cannot be set true without a real user action",
        )
    if output_kind in POST_LOCK_OUTPUT_KINDS:
        # Envelope/spec must not silently carry sign/send/PD/overwrite claims.
        _assert_post_lock_surface_claims(spec, surface="output_spec")

    payload = spec.get("payload")
    if payload is None:
        payload = _default_payload_for_kind(output_kind, run, auth, spec)
    elif not isinstance(payload, Mapping):
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "payload must be a mapping")
    else:
        payload = _copy_mapping(payload)
        if output_kind == "affected_query_draft":
            # Re-validate boundary even when caller supplies payload.
            for draft in payload.get("query_drafts") or []:
                if not isinstance(draft, Mapping):
                    raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "query draft invalid")
                for field in QUERY_DRAFT_REQUIRED:
                    if field not in draft:
                        raise ModeOutputError(
                            OUTPUT_NOT_ELIGIBLE, f"query draft missing {field}"
                        )
                _assert_query_draft_boundary(draft)
                clauses = (draft["basis"], draft["finding"], draft["action"])
                if not all(isinstance(clause, str) for clause in clauses):
                    raise ModeOutputError(
                        OUTPUT_NOT_ELIGIBLE, "query clauses must be strings"
                    )
                expected = "".join(clauses)
                if draft.get("display_text") != expected:
                    raise ModeOutputError(
                        OUTPUT_NOT_ELIGIBLE,
                        "display_text must equal basis+finding+action",
                    )
                if draft.get("query_draft_id") != _query_draft_id(draft):
                    raise ModeOutputError(
                        IDENTITY_MISMATCH,
                        "query_draft_id does not match canonical content",
                    )

    if output_kind == "current_full_risk":
        numeric_codes: list[str] = []
        _validate_numeric_payload(payload, run, numeric_codes)
        if numeric_codes:
            raise ModeOutputError(
                numeric_codes[0], f"numeric payload invalid: {tuple(numeric_codes)}"
            )
    if output_kind == "full_risk":
        fr_codes: list[str] = []
        _validate_full_risk_payload(payload, run, authority_refs=auth, codes=fr_codes)
        if fr_codes:
            raise ModeOutputError(
                fr_codes[0], f"full_risk payload invalid: {tuple(fr_codes)}"
            )
    if output_kind == "revision_impact":
        ri_codes: list[str] = []
        _validate_revision_impact_payload(payload, run, auth, codes=ri_codes)
        if ri_codes:
            raise ModeOutputError(
                ri_codes[0], f"revision_impact payload invalid: {tuple(ri_codes)}"
            )
    if output_kind == "check_package":
        cp_codes: list[str] = []
        _validate_check_package_payload(payload, run, auth, codes=cp_codes)
        if cp_codes:
            raise ModeOutputError(
                cp_codes[0], f"check_package payload invalid: {tuple(cp_codes)}"
            )
    if output_kind == "query_revision_package":
        qr_codes: list[str] = []
        _validate_query_revision_package_payload(payload, run, auth, codes=qr_codes)
        if qr_codes:
            raise ModeOutputError(
                qr_codes[0],
                f"query_revision_package payload invalid: {tuple(qr_codes)}",
            )
    if output_kind == "full_project_report":
        fpr_codes: list[str] = []
        _validate_full_project_report_payload(payload, run, auth, fpr_codes)
        if fpr_codes:
            raise ModeOutputError(
                fpr_codes[0], f"full_project_report invalid: {tuple(fpr_codes)}"
            )
    if output_kind == "site_materials":
        sm_codes: list[str] = []
        _validate_site_materials_payload(payload, run, auth, sm_codes)
        if sm_codes:
            raise ModeOutputError(
                sm_codes[0], f"site_materials invalid: {tuple(sm_codes)}"
            )
    if output_kind == "subject_materials":
        sub_codes: list[str] = []
        _validate_subject_materials_payload(payload, run, auth, sub_codes)
        if sub_codes:
            raise ModeOutputError(
                sub_codes[0], f"subject_materials invalid: {tuple(sub_codes)}"
            )
    if output_kind == "checklist":
        cl_codes: list[str] = []
        _validate_checklist_payload(payload, run, auth, cl_codes)
        if cl_codes:
            raise ModeOutputError(
                cl_codes[0], f"checklist invalid: {tuple(cl_codes)}"
            )
    if output_kind == "change_summary":
        change_codes: list[str] = []
        _validate_change_entries(payload, "changes", change_codes)
        if change_codes:
            raise ModeOutputError(change_codes[0], "change_summary entries invalid")
    if output_kind == "data_knowledge_rule_model_change_note":
        change_codes = []
        _validate_change_entries(payload, "change_notes", change_codes)
        if change_codes:
            raise ModeOutputError(change_codes[0], "change note entries invalid")

    # When caller supplies a pre_lock/post_lock payload, still require output_kind marker.
    if output_kind in PRE_LOCK_OUTPUT_KINDS + POST_LOCK_OUTPUT_KINDS and payload.get(
        "output_kind"
    ) not in (
        None,
        output_kind,
    ):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            f"payload.output_kind must match {output_kind!r}",
        )

    envelope: dict[str, Any] = {
        "output_kind": output_kind,
        "producer_kind": producer_kind,
        "project_id": run.get("project_id"),
        "run_id": run.get("run_id"),
        "mode": run.get("mode"),
        "execution_basis": run.get("execution_basis"),
        "data_cutoff": run.get("data_cutoff"),
        "source_revision_id": run.get("source_revision_id"),
        "knowledge_pack_version": run.get("knowledge_pack_version"),
        "rule_activation_version": run.get("rule_activation_version"),
        "mapping_version": run.get("mapping_version"),
        "identity_algorithm_digest": run.get("identity_algorithm_digest"),
        "authority_refs": auth,
        "coverage_refs": cov,
        "qc_refs": qc,
        "output_state": output_state,
        "is_user_confirmed": False,
        "eligibility": gate_spec,
        "payload": payload,
        "immutable": True,
    }

    if producer_kind == PRODUCER_EXTERNAL:
        for field in EXTERNAL_REPORT_REQUIRED:
            value = spec.get(field)
            if not _non_empty_str(value):
                raise ModeOutputError(
                    AUTHORITY_MISMATCH,
                    f"external_report_review requires {field}",
                )
            # Must not be filled from run.source_revision_id.
            if field == "report_source_revision_id" and value == run.get(
                "source_revision_id"
            ):
                raise ModeOutputError(
                    AUTHORITY_MISMATCH,
                    "report_source_revision_id must not be filled from run source_revision_id",
                )
            envelope[field] = value

    computed_output_id = "out-" + sha256_hex(canonical_bytes(envelope))
    supplied_output_id = spec.get("output_id")
    if supplied_output_id is not None and supplied_output_id != computed_output_id:
        raise ModeOutputError(
            IDENTITY_MISMATCH, "supplied output_id does not match canonical content"
        )
    envelope["output_id"] = computed_output_id

    return envelope


def build_daily_mode_outputs(
    run_binding: Mapping[str, Any],
    mode_contract: Mapping[str, Any],
    *,
    authority_refs: Mapping[str, Any],
    coverage_refs: Mapping[str, Any],
    qc_refs: Mapping[str, Any],
    findings: Optional[Sequence[Mapping[str, Any]]] = None,
    changes: Optional[Sequence[Any]] = None,
    risks: Optional[Sequence[Any]] = None,
    numeric: Optional[Mapping[str, Any]] = None,
    change_notes: Optional[Sequence[Any]] = None,
    entry_context: Optional[Mapping[str, Any]] = None,
    prior_run: Optional[Mapping[str, Any]] = None,
) -> Tuple[dict, dict, dict, dict]:
    """Build the four daily default ModeOutputs under one authority/coverage/QC binding."""
    if mode_contract.get("mode") != "daily" or run_binding.get("mode") != "daily":
        raise ModeOutputError(OUTPUT_NOT_ELIGIBLE, "build_daily_mode_outputs requires daily")
    eligibility = default_output_eligibility()
    specs = [
        {
            "output_kind": "change_summary",
            "changes": list(changes or []),
            "eligibility": eligibility,
        },
        {
            "output_kind": "current_full_risk",
            "risks": list(risks or []),
            "numeric": dict(numeric or {}),
            "eligibility": eligibility,
        },
        {
            "output_kind": "affected_query_draft",
            "findings": list(findings or []),
            "eligibility": eligibility,
        },
        {
            "output_kind": "data_knowledge_rule_model_change_note",
            "change_notes": list(change_notes or []),
            "eligibility": eligibility,
        },
    ]
    outputs = []
    for spec in specs:
        outputs.append(
            build_mode_output(
                run_binding,
                mode_contract,
                spec,
                authority_refs=authority_refs,
                coverage_refs=coverage_refs,
                qc_refs=qc_refs,
                entry_context=entry_context,
                prior_run=prior_run,
            )
        )
    return tuple(outputs)  # type: ignore[return-value]

def build_pre_lock_mode_outputs(
    run_binding: Mapping[str, Any],
    mode_contract: Mapping[str, Any],
    *,
    authority_refs: Mapping[str, Any],
    coverage_refs: Mapping[str, Any],
    qc_refs: Mapping[str, Any],
    risks: Optional[Sequence[Any]] = None,
    numeric: Optional[Mapping[str, Any]] = None,
    population_scope: Any = None,
    from_source_revision_id: Optional[str] = None,
    revision_reason: Optional[str] = None,
    impacts: Optional[Sequence[Mapping[str, Any]]] = None,
    check_items: Optional[Sequence[Mapping[str, Any]]] = None,
    revision_entries: Optional[Sequence[Mapping[str, Any]]] = None,
    entry_context: Optional[Mapping[str, Any]] = None,
    prior_run: Optional[Mapping[str, Any]] = None,
) -> Tuple[dict, dict, dict, dict]:
    """Build the four pre_lock default ModeOutputs under one authority binding.

    Reuses ``build_mode_output`` / Run gate / eligibility. Does not mutate inputs.
    """
    if mode_contract.get("mode") != "pre_lock" or run_binding.get("mode") != "pre_lock":
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "build_pre_lock_mode_outputs requires pre_lock"
        )
    if not _non_empty_str(from_source_revision_id) or not _non_empty_str(revision_reason):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE,
            "build_pre_lock_mode_outputs requires from_source_revision_id and revision_reason",
        )
    eligibility = default_output_eligibility()
    specs = [
        {
            "output_kind": "full_risk",
            "risks": list(risks or []),
            "numeric": dict(numeric or {}),
            "population_scope": population_scope,
            "eligibility": eligibility,
        },
        {
            "output_kind": "revision_impact",
            "from_source_revision_id": from_source_revision_id,
            "revision_reason": revision_reason,
            "impacts": list(impacts or []),
            "eligibility": eligibility,
        },
        {
            "output_kind": "check_package",
            "check_items": list(check_items or []),
            "eligibility": eligibility,
        },
        {
            "output_kind": "query_revision_package",
            "revision_entries": list(revision_entries or []),
            "eligibility": eligibility,
        },
    ]
    outputs = []
    for spec in specs:
        outputs.append(
            build_mode_output(
                run_binding,
                mode_contract,
                spec,
                authority_refs=authority_refs,
                coverage_refs=coverage_refs,
                qc_refs=qc_refs,
                entry_context=entry_context,
                prior_run=prior_run,
            )
        )
    return tuple(outputs)  # type: ignore[return-value]

def validate_post_lock_output_set(
    full_project_report: Mapping[str, Any],
    site_materials: Mapping[str, Any],
    subject_materials: Mapping[str, Any],
    checklist: Mapping[str, Any],
) -> Tuple[str, ...]:
    """Cross-output reconciliation for the four post_lock fixed-total payloads.

    Accepts either ModeOutput envelopes (with ``payload``) or bare payloads.
    Invokes the four existing payload validators against a derived common
    run/authority identity before relational checks. Envelope inputs also bind
    outer identity to the locked inner payload and reuse ``validate_mode_output``
    (no second envelope framework). Does not mutate inputs.
    """
    codes: list[str] = []

    def _unwrap(
        obj: Mapping[str, Any], kind: str
    ) -> Tuple[Mapping[str, Any], Optional[Mapping[str, Any]]]:
        if not isinstance(obj, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            return {}, None
        # Bare payload: output_kind matches and no envelope wrapper.
        if "payload" not in obj:
            if obj.get("output_kind") == kind:
                return obj, None
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            return {}, None
        # ModeOutput envelope: outer and inner output_kind must both match exactly.
        if obj.get("output_kind") != kind:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            return {}, None
        # Envelope surface claims (sign/send/PD/overwrite/external) must fail closed.
        _append_post_lock_surface_claim_codes(obj, codes)
        inner = obj.get("payload")
        if not isinstance(inner, Mapping) or inner.get("output_kind") != kind:
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            return {}, None
        return inner, obj

    report, report_env = _unwrap(full_project_report, "full_project_report")
    sites, sites_env = _unwrap(site_materials, "site_materials")
    subjects, subjects_env = _unwrap(subject_materials, "subject_materials")
    checks, checks_env = _unwrap(checklist, "checklist")
    if not report or not sites or not subjects or not checks:
        return tuple(_dedupe(codes))

    # Envelope outer identity must bind the locked inner payload; wrappers that
    # drift after output_id restamp must fail closed without a second framework.
    envelope_pairs = (
        (report_env, report),
        (sites_env, sites),
        (subjects_env, subjects),
        (checks_env, checks),
    )
    envelopes: list[Mapping[str, Any]] = []
    for envelope, inner in envelope_pairs:
        if envelope is None:
            continue
        for key in ("project_id", "run_id"):
            if envelope.get(key) != inner.get(key):
                _append(codes, IDENTITY_MISMATCH)
        if envelope.get("data_cutoff") != inner.get("data_cutoff"):
            _append(codes, CUTOFF_MISMATCH)
        if envelope.get("source_revision_id") != inner.get("source_revision_id"):
            _append(codes, REVISION_MISMATCH)
        if envelope.get("mode") != "post_lock_pre_cfdi":
            _append(codes, IDENTITY_MISMATCH)
        if envelope.get("execution_basis") != "full":
            _append(codes, IDENTITY_MISMATCH)
        envelopes.append(envelope)

    if envelopes:
        # Run-identity / version / digest fields must agree across envelopes.
        envelope_identity_keys = (
            "project_id",
            "run_id",
            "mode",
            "execution_basis",
            "data_cutoff",
            "source_revision_id",
            "knowledge_pack_version",
            "rule_activation_version",
            "mapping_version",
            "identity_algorithm_digest",
        )
        for key in envelope_identity_keys:
            values = [env.get(key) for env in envelopes]
            if any(value != values[0] for value in values[1:]):
                if key == "data_cutoff":
                    _append(codes, CUTOFF_MISMATCH)
                elif key == "source_revision_id":
                    _append(codes, REVISION_MISMATCH)
                else:
                    _append(codes, IDENTITY_MISMATCH)

        # Reuse validate_mode_output for refs + canonical outer output_id.
        # Run identity is taken from locked inners so four wrappers that drift
        # together still fail against the payload-locked identity.
        seed = envelopes[0]
        envelope_run = {
            "project_id": report.get("project_id"),
            "run_id": report.get("run_id"),
            "mode": "post_lock_pre_cfdi",
            "execution_basis": "full",
            "data_cutoff": report.get("data_cutoff"),
            "source_revision_id": report.get("source_revision_id"),
            "knowledge_pack_version": seed.get("knowledge_pack_version"),
            "rule_activation_version": seed.get("rule_activation_version"),
            "mapping_version": seed.get("mapping_version"),
            "identity_algorithm_digest": seed.get("identity_algorithm_digest"),
            "fixed_total": True,
            "locked_snapshot_hash": report.get("locked_snapshot_hash"),
            "acceptance_evidence_hash": report.get("acceptance_evidence_hash"),
            "output_cutoff_ref": report.get("data_cutoff"),
            "output_revision_ref": report.get("source_revision_id"),
            "local_os_user": "derived-from-locked-identity",
        }
        contract = build_mode_contract("post_lock_pre_cfdi")
        for envelope in envelopes:
            for code in validate_mode_output(envelope, envelope_run, contract):
                _append(codes, code)

    identity_keys = (
        "project_id",
        "run_id",
        "data_cutoff",
        "source_revision_id",
        "authority_digest",
        "locked_snapshot_hash",
        "acceptance_evidence_hash",
        "fixed_total",
        "population_totals",
    )
    for key in identity_keys:
        values = [
            report.get(key),
            sites.get(key),
            subjects.get(key),
            checks.get(key),
        ]
        if any(canonical_bytes(values[0]) != canonical_bytes(value) for value in values[1:]):
            if key == "data_cutoff":
                _append(codes, CUTOFF_MISMATCH)
            elif key == "source_revision_id":
                _append(codes, REVISION_MISMATCH)
            elif key in ("authority_digest", "population_totals"):
                _append(codes, AUTHORITY_MISMATCH)
            else:
                _append(codes, IDENTITY_MISMATCH)

    # Derive common run/authority from the agreed locked identity; reuse existing
    # payload validators (no second framework).
    derived_run = {
        "project_id": report.get("project_id"),
        "run_id": report.get("run_id"),
        "mode": "post_lock_pre_cfdi",
        "execution_basis": "full",
        "data_cutoff": report.get("data_cutoff"),
        "source_revision_id": report.get("source_revision_id"),
        "fixed_total": True,
        "locked_snapshot_hash": report.get("locked_snapshot_hash"),
        "acceptance_evidence_hash": report.get("acceptance_evidence_hash"),
        "output_cutoff_ref": report.get("data_cutoff"),
        "output_revision_ref": report.get("source_revision_id"),
        "local_os_user": "derived-from-locked-identity",
    }
    derived_auth = {
        "digest": report.get("authority_digest"),
        "authority_digest": report.get("authority_digest"),
        "project_id": report.get("project_id"),
        "run_id": report.get("run_id"),
        "data_cutoff": report.get("data_cutoff"),
        "source_revision_id": report.get("source_revision_id"),
    }
    _validate_full_project_report_payload(report, derived_run, derived_auth, codes)
    _validate_site_materials_payload(sites, derived_run, derived_auth, codes)
    _validate_subject_materials_payload(subjects, derived_run, derived_auth, codes)
    _validate_checklist_payload(checks, derived_run, derived_auth, codes)

    site_mats = sites.get("materials") if isinstance(sites.get("materials"), list) else []
    subject_mats = (
        subjects.get("materials") if isinstance(subjects.get("materials"), list) else []
    )
    check_items = (
        checks.get("check_items") if isinstance(checks.get("check_items"), list) else []
    )

    # Count / identity drift the single-output validators already cover when
    # payloads are well-formed; keep explicit relational closures here too.
    totals = report.get("population_totals")
    if isinstance(totals, Mapping):
        if sites.get("material_count") != len(site_mats) or totals.get(
            "site_count"
        ) != len(site_mats):
            _append(codes, AUTHORITY_MISMATCH)
        if subjects.get("material_count") != len(subject_mats) or totals.get(
            "subject_count"
        ) != len(subject_mats):
            _append(codes, AUTHORITY_MISMATCH)
        if checks.get("item_count") != len(check_items):
            _append(codes, OUTPUT_NOT_ELIGIBLE)

    site_ids = [
        item.get("site_id") for item in site_mats if isinstance(item, Mapping)
    ]
    subject_ids = [
        item.get("subject_id") for item in subject_mats if isinstance(item, Mapping)
    ]
    if len(site_ids) != len(set(site_ids)):
        _append(codes, IDENTITY_MISMATCH)
    if len(subject_ids) != len(set(subject_ids)):
        _append(codes, IDENTITY_MISMATCH)

    site_material_ids = sorted(
        str(item.get("site_material_id"))
        for item in site_mats
        if isinstance(item, Mapping)
    )
    subject_material_ids = sorted(
        str(item.get("subject_material_id"))
        for item in subject_mats
        if isinstance(item, Mapping)
    )
    report_site_ids = report.get("site_material_ids")
    report_subject_ids = report.get("subject_material_ids")
    if not isinstance(report_site_ids, list) or sorted(
        str(v) for v in report_site_ids
    ) != site_material_ids:
        _append(codes, AUTHORITY_MISMATCH)
    if not isinstance(report_subject_ids, list) or sorted(
        str(v) for v in report_subject_ids
    ) != subject_material_ids:
        _append(codes, AUTHORITY_MISMATCH)
    if report.get("checklist_id") != checks.get("checklist_id"):
        _append(codes, IDENTITY_MISMATCH)

    site_id_set = {
        str(item.get("site_id"))
        for item in site_mats
        if isinstance(item, Mapping) and _non_empty_str(item.get("site_id"))
    }
    site_subject_map: dict[str, set[str]] = {
        str(item.get("site_id")): set(str(s) for s in (item.get("subject_ids") or []))
        for item in site_mats
        if isinstance(item, Mapping)
    }
    site_declared_subjects: set[str] = set()
    for declared in site_subject_map.values():
        site_declared_subjects.update(declared)
    subject_id_set = {
        str(item.get("subject_id"))
        for item in subject_mats
        if isinstance(item, Mapping) and _non_empty_str(item.get("subject_id"))
    }
    # Exact closure: no site-declared ghost subjects, no orphan subject materials.
    if site_declared_subjects != subject_id_set:
        _append(codes, AUTHORITY_MISMATCH)
    if isinstance(totals, Mapping):
        if totals.get("site_count") != len(site_id_set):
            _append(codes, AUTHORITY_MISMATCH)
        if totals.get("subject_count") != len(subject_id_set):
            _append(codes, AUTHORITY_MISMATCH)

    site_risks: set[str] = set()
    for item in site_mats:
        if isinstance(item, Mapping):
            site_risks.update(str(r) for r in (item.get("risk_ids") or []))
    subject_risks: set[str] = set()
    for item in subject_mats:
        if not isinstance(item, Mapping):
            continue
        site_id = item.get("site_id")
        subject_id = item.get("subject_id")
        if site_id not in site_id_set:
            _append(codes, AUTHORITY_MISMATCH)
        elif subject_id not in site_subject_map.get(str(site_id), set()):
            _append(codes, AUTHORITY_MISMATCH)
        subject_risks.update(str(r) for r in (item.get("risk_ids") or []))
    report_risks = set()
    risk_summary = report.get("risk_summary")
    if isinstance(risk_summary, Mapping):
        report_risks = set(str(r) for r in (risk_summary.get("risk_ids") or []))
    material_risks = site_risks | subject_risks
    risk_count = totals.get("risk_count") if isinstance(totals, Mapping) else None
    if risk_count == 0:
        if report_risks or material_risks:
            _append(codes, AUTHORITY_MISMATCH)
    elif isinstance(risk_count, int) and not isinstance(risk_count, bool):
        # Codex: report_risks == site_risks ∪ subject_risks (center risks need not
        # be copied onto a subject).
        if report_risks != material_risks or len(report_risks) != risk_count:
            _append(codes, AUTHORITY_MISMATCH)
    else:
        _append(codes, OUTPUT_NOT_ELIGIBLE)

    for item in check_items:
        if not isinstance(item, Mapping):
            continue
        level = item.get("level")
        scope_id = item.get("scope_id")
        if level == "project" and scope_id != report.get("project_id"):
            _append(codes, IDENTITY_MISMATCH)
        if level == "site" and scope_id not in site_id_set:
            _append(codes, AUTHORITY_MISMATCH)
        if level == "subject":
            if scope_id not in subject_id_set:
                _append(codes, AUTHORITY_MISMATCH)
        for risk_id in item.get("risk_ids") or []:
            # Empty report risk set still rejects any checklist risk reference.
            if str(risk_id) not in report_risks:
                _append(codes, AUTHORITY_MISMATCH)

    return tuple(_dedupe(codes))

def build_post_lock_mode_outputs(
    run_binding: Mapping[str, Any],
    mode_contract: Mapping[str, Any],
    *,
    authority_refs: Mapping[str, Any],
    coverage_refs: Mapping[str, Any],
    qc_refs: Mapping[str, Any],
    population_totals: Mapping[str, Any],
    report_version: str,
    project_summary: Mapping[str, Any],
    risk_summary: Mapping[str, Any],
    evidence_refs: Sequence[Any],
    site_materials: Optional[Sequence[Mapping[str, Any]]] = None,
    subject_materials: Optional[Sequence[Mapping[str, Any]]] = None,
    check_items: Optional[Sequence[Mapping[str, Any]]] = None,
    entry_context: Optional[Mapping[str, Any]] = None,
    prior_run: Optional[Mapping[str, Any]] = None,
) -> Tuple[dict, dict, dict, dict]:
    """Build the four post_lock fixed-total ModeOutputs under one locked identity.

    Builds site/subject/checklist first, then the project report with reconciled
    IDs. Fail-closes on cross-output drift. Does not mutate inputs.
    """
    if (
        mode_contract.get("mode") != "post_lock_pre_cfdi"
        or run_binding.get("mode") != "post_lock_pre_cfdi"
    ):
        raise ModeOutputError(
            OUTPUT_NOT_ELIGIBLE, "build_post_lock_mode_outputs requires post_lock_pre_cfdi"
        )
    eligibility = default_output_eligibility()
    site_out = build_mode_output(
        run_binding,
        mode_contract,
        {
            "output_kind": "site_materials",
            "materials": list(site_materials or []),
            "population_totals": population_totals,
            "eligibility": eligibility,
        },
        authority_refs=authority_refs,
        coverage_refs=coverage_refs,
        qc_refs=qc_refs,
        entry_context=entry_context,
        prior_run=prior_run,
    )
    subject_out = build_mode_output(
        run_binding,
        mode_contract,
        {
            "output_kind": "subject_materials",
            "materials": list(subject_materials or []),
            "population_totals": population_totals,
            "eligibility": eligibility,
        },
        authority_refs=authority_refs,
        coverage_refs=coverage_refs,
        qc_refs=qc_refs,
        entry_context=entry_context,
        prior_run=prior_run,
    )
    checklist_out = build_mode_output(
        run_binding,
        mode_contract,
        {
            "output_kind": "checklist",
            "check_items": list(check_items or []),
            "population_totals": population_totals,
            "eligibility": eligibility,
        },
        authority_refs=authority_refs,
        coverage_refs=coverage_refs,
        qc_refs=qc_refs,
        entry_context=entry_context,
        prior_run=prior_run,
    )
    report_out = build_mode_output(
        run_binding,
        mode_contract,
        {
            "output_kind": "full_project_report",
            "report_version": report_version,
            "project_summary": project_summary,
            "risk_summary": risk_summary,
            "site_material_ids": [
                item["site_material_id"] for item in site_out["payload"]["materials"]
            ],
            "subject_material_ids": [
                item["subject_material_id"]
                for item in subject_out["payload"]["materials"]
            ],
            "checklist_id": checklist_out["payload"]["checklist_id"],
            "evidence_refs": evidence_refs,
            "population_totals": population_totals,
            "eligibility": eligibility,
        },
        authority_refs=authority_refs,
        coverage_refs=coverage_refs,
        qc_refs=qc_refs,
        entry_context=entry_context,
        prior_run=prior_run,
    )
    reconcile_codes = validate_post_lock_output_set(
        report_out, site_out, subject_out, checklist_out
    )
    if reconcile_codes:
        raise ModeOutputError(
            reconcile_codes[0],
            f"post_lock cross-output reconciliation failed: {reconcile_codes}",
        )
    return report_out, site_out, subject_out, checklist_out


def _validate_query_payload(payload: Mapping[str, Any], run: Mapping[str, Any], codes: list[str]) -> None:
    drafts = payload.get("query_drafts")
    if not isinstance(drafts, list):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
        return
    for draft in drafts:
        if not isinstance(draft, Mapping):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
            continue
        for field in QUERY_DRAFT_REQUIRED:
            if field not in draft:
                _append(codes, OUTPUT_NOT_ELIGIBLE)
        try:
            _assert_query_draft_boundary(draft)
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)
        clauses = (draft.get("basis"), draft.get("finding"), draft.get("action"))
        if not all(isinstance(clause, str) for clause in clauses):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
        elif draft.get("display_text") != "".join(clauses):
            _append(codes, OUTPUT_NOT_ELIGIBLE)
        if draft.get("query_draft_id") != _query_draft_id(draft):
            _append(codes, IDENTITY_MISMATCH)
        if draft.get("project_id") != run.get("project_id") or draft.get("run_id") != run.get(
            "run_id"
        ):
            _append(codes, IDENTITY_MISMATCH)
        if draft.get("data_cutoff") != run.get("data_cutoff"):
            _append(codes, CUTOFF_MISMATCH)
        if draft.get("source_revision_id") != run.get("source_revision_id"):
            _append(codes, REVISION_MISMATCH)
        for key in QUERY_FORBIDDEN_KEYS:
            if key in draft and draft.get(key) not in (None, "", False):
                _append(codes, OUTPUT_NOT_ELIGIBLE)
    for flag in (
        "is_sent",
        "is_closed",
        "is_user_confirmed",
        "pd_registration_allowed",
        "external_dispatch_allowed",
    ):
        if flag not in payload or payload.get(flag) is not False:
            _append(codes, OUTPUT_NOT_ELIGIBLE)


def validate_mode_output(
    output: Mapping[str, Any],
    run_binding: Mapping[str, Any],
    mode_contract: Mapping[str, Any],
) -> Tuple[str, ...]:
    """Validate a ModeOutput envelope against run + ModeContract (R6-C-OUT-001).

    Returns canonical failure codes. Does not mutate inputs.
    """
    codes: list[str] = []
    if not isinstance(output, Mapping) or not isinstance(run_binding, Mapping):
        return (IDENTITY_MISMATCH,)
    if not isinstance(mode_contract, Mapping):
        return (IDENTITY_MISMATCH,)

    out = _copy_mapping(output)
    run = _copy_mapping(run_binding)
    contract = _copy_mapping(mode_contract)

    for field in MODE_OUTPUT_ENVELOPE_REQUIRED:
        if field not in out:
            _append(codes, IDENTITY_MISMATCH)

    if out.get("immutable") is False:
        _append(codes, SILENT_MODE_CONVERSION)

    for field in (
        "project_id",
        "run_id",
        "mode",
        "execution_basis",
        "data_cutoff",
        "source_revision_id",
        "knowledge_pack_version",
        "rule_activation_version",
        "mapping_version",
        "identity_algorithm_digest",
    ):
        if out.get(field) != run.get(field):
            if field in ("data_cutoff",):
                _append(codes, CUTOFF_MISMATCH)
            elif field == "source_revision_id":
                _append(codes, REVISION_MISMATCH)
            else:
                _append(codes, IDENTITY_MISMATCH)

    if run.get("mode") != contract.get("mode"):
        _append(codes, MODE_ENTRY_BLOCKED)

    output_kind = out.get("output_kind")
    eligible = _eligible_kinds_for_mode(contract)
    if output_kind not in eligible:
        _append(codes, OUTPUT_NOT_ELIGIBLE)

    producer_kind = out.get("producer_kind")
    if producer_kind not in PRODUCER_KINDS:
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    if output_kind in SYSTEM_DEFAULT_OUTPUT_KINDS and producer_kind != PRODUCER_SYSTEM:
        _append(codes, AUTHORITY_MISMATCH)
    if output_kind == "external_report_review_bundle" and producer_kind != PRODUCER_EXTERNAL:
        _append(codes, AUTHORITY_MISMATCH)

    if out.get("is_user_confirmed") is not False:
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    if out.get("output_state") not in OUTPUT_STATES:
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    if output_kind in POST_LOCK_OUTPUT_KINDS:
        # ModeOutput envelope is the persisted artifact; apply the same draft/PD/
        # overwrite/external restrictions used on payloads.
        _append_post_lock_surface_claim_codes(out, codes)

    eligibility = out.get("eligibility")
    if not isinstance(eligibility, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    else:
        try:
            _check_eligibility(eligibility, producer_kind=str(producer_kind))
        except ModeOutputError as exc:
            _append(codes, exc.failure_code)

    for ref_name in ("authority_refs", "coverage_refs", "qc_refs"):
        refs = out.get(ref_name)
        if not isinstance(refs, Mapping) or not refs:
            _append(codes, AUTHORITY_MISMATCH)
            continue
        digest = (
            refs.get("digest")
            or refs.get("authority_digest")
            or refs.get("coverage_digest")
            or refs.get("qc_digest")
        )
        if not _non_empty_str(digest):
            _append(codes, AUTHORITY_MISMATCH)
        for key in ("project_id", "run_id", "data_cutoff", "source_revision_id"):
            if key in refs and refs.get(key) != run.get(key):
                if key == "data_cutoff":
                    _append(codes, CUTOFF_MISMATCH)
                elif key == "source_revision_id":
                    _append(codes, REVISION_MISMATCH)
                else:
                    _append(codes, AUTHORITY_MISMATCH)

    if producer_kind == PRODUCER_EXTERNAL:
        for field in EXTERNAL_REPORT_REQUIRED:
            if not _non_empty_str(out.get(field)):
                _append(codes, AUTHORITY_MISMATCH)
        if out.get("report_source_revision_id") == run.get("source_revision_id"):
            _append(codes, AUTHORITY_MISMATCH)

    payload = out.get("payload")
    if not isinstance(payload, Mapping):
        _append(codes, OUTPUT_NOT_ELIGIBLE)
    elif output_kind == "affected_query_draft":
        _validate_query_payload(payload, run, codes)
    elif output_kind == "current_full_risk":
        _validate_numeric_payload(payload, run, codes)
    elif output_kind == "full_risk":
        authority_refs = out.get("authority_refs")
        _validate_full_risk_payload(
            payload,
            run,
            authority_refs=authority_refs if isinstance(authority_refs, Mapping) else {},
            codes=codes,
        )
    elif output_kind == "revision_impact":
        authority_refs = out.get("authority_refs")
        _validate_revision_impact_payload(
            payload,
            run,
            authority_refs if isinstance(authority_refs, Mapping) else {},
            codes,
        )
    elif output_kind == "check_package":
        authority_refs = out.get("authority_refs")
        _validate_check_package_payload(
            payload,
            run,
            authority_refs if isinstance(authority_refs, Mapping) else {},
            codes,
        )
    elif output_kind == "query_revision_package":
        authority_refs = out.get("authority_refs")
        _validate_query_revision_package_payload(
            payload,
            run,
            authority_refs if isinstance(authority_refs, Mapping) else {},
            codes,
        )
    elif output_kind == "full_project_report":
        authority_refs = out.get("authority_refs")
        _validate_full_project_report_payload(
            payload,
            run,
            authority_refs if isinstance(authority_refs, Mapping) else {},
            codes,
        )
    elif output_kind == "site_materials":
        authority_refs = out.get("authority_refs")
        _validate_site_materials_payload(
            payload,
            run,
            authority_refs if isinstance(authority_refs, Mapping) else {},
            codes,
        )
    elif output_kind == "subject_materials":
        authority_refs = out.get("authority_refs")
        _validate_subject_materials_payload(
            payload,
            run,
            authority_refs if isinstance(authority_refs, Mapping) else {},
            codes,
        )
    elif output_kind == "checklist":
        authority_refs = out.get("authority_refs")
        _validate_checklist_payload(
            payload,
            run,
            authority_refs if isinstance(authority_refs, Mapping) else {},
            codes,
        )
    elif output_kind == "change_summary":
        _validate_change_entries(payload, "changes", codes)
    elif output_kind == "data_knowledge_rule_model_change_note":
        _validate_change_entries(payload, "change_notes", codes)
    if isinstance(payload, Mapping) and output_kind in SYSTEM_DEFAULT_OUTPUT_KINDS:
        # Pre-lock / post-lock identity is mandatory; daily identity, when present, must not drift.
        auth = out.get("authority_refs") or {}
        expected = auth.get("digest") or auth.get("authority_digest")
        locked_kinds = frozenset(PRE_LOCK_OUTPUT_KINDS + POST_LOCK_OUTPUT_KINDS)
        if expected:
            if output_kind in locked_kinds:
                if payload.get("authority_digest") != expected:
                    _append(codes, AUTHORITY_MISMATCH)
            elif payload.get("authority_digest") not in (None, expected):
                _append(codes, AUTHORITY_MISMATCH)
        for key in ("project_id", "run_id", "data_cutoff", "source_revision_id"):
            if output_kind in locked_kinds and payload.get(key) != run.get(key):
                _append(codes, AUTHORITY_MISMATCH)
            elif key in payload and payload.get(key) != run.get(key):
                _append(codes, AUTHORITY_MISMATCH)

    stored_output_id = out.pop("output_id", None)
    expected_output_id = "out-" + sha256_hex(canonical_bytes(out))
    if stored_output_id != expected_output_id:
        _append(codes, IDENTITY_MISMATCH)

    return tuple(_dedupe(codes))
